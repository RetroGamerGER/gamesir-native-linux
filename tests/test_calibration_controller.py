#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure frame/provider/lease adapter tests; all channel operations are in memory."""
from contextlib import ExitStack
from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from calibration_protocol import (InvalidTelemetry, PositionPolicy, calibration_message,
                                  decode_telemetry)
from calibration_controller import (ControllerCalibration, Target, Lease, Report,
                                    ChannelUnavailable, CAPABILITIES)
from stick_calibration import Instance, Intent, CalibrationFailure, MAX_SAMPLE_AGE
from test_control_center_calibration import Clock


def telemetry(*, active=0, done=0, raw=(128,128,128,128), processed=(128,128,128,128), seq=0):
    packet=bytearray(64)
    packet[:5]=bytes((0x10,0,seq,0x3c,0xe0))
    packet[5:9]=bytes(processed);packet[51:55]=bytes(raw)
    packet[30]=active;packet[31]=done
    return bytes(packet)


class FakeChannel:
    """Test-only proposed owner API. It never simulates firmware execution."""
    def __init__(self, clock):
        self.clock=clock
        self.lease=None
        self.events=[]
        self.fail_send=False
        self.after_send=None
        self.inspect_error=False
        self.release_ok=True
        self.acquire_error=None
        self.accepted=True

    def acquire(self,target,key):
        self.events.append(('acquire',target,key))
        if self.acquire_error:raise self.acquire_error
        self.lease=Lease(key,target,'test-lease-token-0001',self.clock()+100,True,True,
                         'gs_native',CAPABILITIES)
        return self.lease

    def inspect(self,lease):
        self.events.append(('inspect',lease))
        if self.inspect_error:raise RuntimeError('untrusted diagnostic/private/path')
        return self.lease

    def send_message(self,lease,message):
        self.events.append(('send',lease,message))
        if self.after_send:self.after_send(self)
        if self.fail_send:raise RuntimeError('possibly delivered; never retry')
        return self.accepted

    def release(self,lease):
        self.events.append(('release',lease))
        return self.release_ok

    @property
    def messages(self):return [e[2] for e in self.events if e[0]=='send']
    @property
    def releases(self):return [e[1] for e in self.events if e[0]=='release']


class CodecTests(unittest.TestCase):
    def test_exact_provider_payloads_without_usb_header_sequence_or_padding(self):
        for name,expected in [('Start','fe0003'),('Finish','fe0100'),('Exit','fe0200')]:
            message=calibration_message(name)
            self.assertEqual(message.message_type,0x0f)
            self.assertEqual(message.payload.hex(),expected)
            self.assertEqual(len(message.payload),3)
        for bad in ('flash','resume','release','start',0,None,True,bytes.fromhex('fe0003')):
            with self.assertRaises(ValueError):calibration_message(bad)

    def test_expected_fields_keep_raw_and_processed_positions_separate(self):
        p=telemetry(active=3,done=1,raw=(0,255,128,64),processed=(1,2,3,4),seq=255)
        d=decode_telemetry(p)
        self.assertEqual((d.active,d.done,d.wire_sequence),(3,1,255))
        self.assertEqual(d.raw,(0,255,128,64));self.assertEqual(d.processed,(1,2,3,4))

    def test_truncated_padded_chunked_or_other_packet_rejected(self):
        packet=telemetry()
        for bad in [packet[:i] for i in range(64)]+[packet+b'\0',bytearray(packet),None]:
            with self.subTest(length=len(bad) if bad is not None else None):
                with self.assertRaises(InvalidTelemetry):decode_telemetry(bad)
        for index,byte in [(0,0x20),(1,0x20),(3,0x7c),(4,0x05)]:
            changed=bytearray(packet);changed[index]=byte
            with self.assertRaises(InvalidTelemetry):decode_telemetry(bytes(changed))

    def test_nonstick_flags_do_not_become_ready(self):
        for field in ('active','done'):
            for bit in range(2,8):
                with self.assertRaises(InvalidTelemetry):
                    decode_telemetry(telemetry(**{field:3|(1<<bit)}))

    def test_status_bytes_26_27_payload_or_sensor_bytes_are_not_used_by_mistake(self):
        p=bytearray(telemetry())
        p[26]=p[27]=p[57]=p[58]=3
        self.assertEqual((decode_telemetry(bytes(p)).active,decode_telemetry(bytes(p)).done),(0,0))

    def test_explicit_mapping_has_zero_and_exact_endpoints_without_deadzone(self):
        policy=PositionPolicy('raw',(1,-1,1,-1))
        d=decode_telemetry(telemetry(raw=(0,0,255,255)))
        self.assertEqual(policy.positions(d),((-1.,1.),(1.,-1.)))
        for value in range(256):
            d=decode_telemetry(telemetry(raw=(value,)*4))
            left,_=policy.positions(d)
            self.assertTrue(-1<=left[0]<=1)
            self.assertEqual(left[1],-left[0])
        d=decode_telemetry(telemetry(raw=(128,)*4,processed=(0,)*4))
        self.assertEqual(policy.positions(d),((0.,0.),(0.,0.)))
        self.assertEqual(PositionPolicy('processed',(1,1,1,1)).positions(d),((-1.,-1.),(-1.,-1.)))

    def test_position_assumptions_are_mandatory(self):
        for source,signs in [('guess',(1,1,1,1)),('raw',(1,1)),('raw',(1,True,1,1)),
                             ('raw',(1,0,1,1)),('raw',[1,1,1,1])]:
            with self.assertRaises(ValueError):PositionPolicy(source,signs)
        with self.assertRaises(ValueError):ControllerCalibration(None)

    def test_saved_capture_confirms_layout_without_claiming_a_calibration_capture(self):
        value=json.loads((ROOT/'fixtures/sprint002-target.json').read_text())
        found=[]
        def walk(v):
            if isinstance(v,dict):
                if 'data_hex' in v:
                    p=bytes.fromhex(v['data_hex'])
                    if len(p)==64 and p[0]==0x10 and p[4]==0xe0:found.append(p)
                for x in v.values():walk(x)
            elif isinstance(v,list):
                for x in v:walk(x)
        walk(value)
        self.assertTrue(found)
        d=decode_telemetry(found[0])
        self.assertEqual(d.processed,(128,128,128,128))
        self.assertEqual(d.raw,(128,126,127,132))
        self.assertEqual((d.active,d.done),(0,0))


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.channel=FakeChannel(self.clock)
        self.policy=PositionPolicy('raw',(1,-1,1,-1))
        self.adapter=ControllerCalibration(self.policy,channel=self.channel,clock=self.clock)
        self.target=Target(Instance('native-device-A','radio-connection-1'),0x3537,0x109c,17,42)
        self.assertTrue(self.adapter.open(self.target))

    def report(self, data=None, **changes):
        self.clock.advance(.1)
        s=self.adapter.session
        report=Report(s.key,self.target,self.adapter.lease.token,s.last_sequence+1,
                      self.clock(),data if data is not None else telemetry())
        return replace(report,**changes)

    def feed(self,**kwargs):return self.adapter.receive(self.report(telemetry(**kwargs)))

    def start(self):
        self.feed();self.assertTrue(self.adapter.prepare())
        for _ in range(31):self.feed();self.adapter.tick()
        self.assertEqual(self.adapter.session.phase,'measuring')
        self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_acquisition_alone_does_not_prove_reports_or_start(self):
        self.assertFalse(self.adapter.view()['canStart'])
        self.assertEqual(self.channel.messages,[])

    def test_waits_for_first_report_without_starting_or_premature_disconnect(self):
        self.clock.advance(.5);self.adapter.tick()
        self.assertEqual(self.adapter.session.phase,'ready')
        self.assertFalse(self.adapter.prepare())
        self.assertEqual(self.adapter.session.phase,'ready')
        self.assertTrue(self.feed())
        self.assertTrue(self.adapter.view()['canStart'])
        self.assertEqual(self.channel.messages,[])

    def test_first_report_timeout_is_bounded_even_if_late_report_arrives_before_tick(self):
        for late_report in (False,True):
            with self.subTest(late_report=late_report):
                self.setUp();self.clock.advance(MAX_SAMPLE_AGE+.1)
                if late_report:self.assertFalse(self.feed())
                else:self.adapter.tick()
                self.assertEqual(self.adapter.session.phase,'lost')
                self.assertEqual(self.adapter.problem,'first_report_timeout')
                self.assertEqual(self.channel.messages,[])
                self.assertEqual(len(self.channel.releases),1)

    def test_real_byte_layout_reaches_the_accepted_session_view(self):
        self.start();self.feed(active=3,done=1,raw=(255,0,128,255))
        v=self.adapter.view()
        self.assertEqual((v['sticks'][0]['x'],v['sticks'][0]['y']),(1.,1.))
        self.assertEqual((v['sticks'][1]['x'],v['sticks'][1]['y']),(0.,-1.))
        self.assertTrue(v['sticks'][0]['ready']);self.assertFalse(v['canFinish'])
        self.feed(active=3,done=3)
        self.assertTrue(self.adapter.finish())
        self.assertEqual(self.adapter.session.phase,'completed')
        self.adapter.finish();self.adapter.close();self.adapter.tick()
        self.assertEqual(self.channel.messages,[calibration_message('Start'),calibration_message('Finish')])
        self.assertEqual(len(self.channel.releases),1)

    def test_same_adapter_supports_both_explicit_native_ids(self):
        self.adapter.close()
        for pid in (0x109c,0x105e):
            target=replace(self.target,product=pid)
            self.assertTrue(self.adapter.open(target))
            self.assertEqual(self.adapter.target.product,pid)
            self.adapter.close()
        for pid in (0x100a,0x1022,0x0575,0x02ea):
            with self.assertRaises(ValueError):replace(self.target,product=pid)

    def test_target_requires_vid_and_positive_kernel_tokens(self):
        for changes in [dict(vendor=0x045e),dict(port_token=0),dict(instance_token=0),
                        dict(port_token=True),dict(product=True),dict(instance='A')]:
            with self.assertRaises(ValueError):replace(self.target,**changes)

    def test_default_backend_is_inert_and_missing_api_is_explicit(self):
        with ExitStack() as stack:
            for name in ('builtins.open','os.open','socket.socket','subprocess.run',
                         'subprocess.Popen','fcntl.ioctl','pathlib.Path.open'):
                stack.enter_context(patch(name,side_effect=AssertionError('Unexpected live I/O')))
            a=ControllerCalibration(self.policy,clock=self.clock)
            self.assertFalse(a.open(self.target))
            a.prepare();a.tick();a.finish();a.close()
        self.assertEqual(a.problem,'calibration_api_unavailable')
        self.assertFalse(a.view()['acquisitionUncertain'])

    def test_unattested_acquisition_never_sends_or_releases_unknown_lease(self):
        self.adapter.close()
        original=self.channel.acquire
        def wrong(target,key):return replace(original(target,key),exclusive=False)
        self.channel.acquire=wrong
        self.assertFalse(self.adapter.open(self.target))
        before=len(self.channel.releases)
        self.adapter.close();self.assertFalse(self.adapter.open(self.target))
        self.assertEqual(len(self.channel.releases),before)
        self.assertEqual(self.channel.messages,[])
        self.assertTrue(self.adapter.acquisition_uncertain)

    def test_uncertain_acquisition_does_not_automatically_retry(self):
        self.adapter.close();self.channel.acquire_error=TimeoutError()
        self.assertFalse(self.adapter.open(self.target))
        count=len(self.channel.events)
        self.assertFalse(self.adapter.open(self.target))
        self.assertEqual(len(self.channel.events),count)
        self.assertEqual(self.adapter.problem,'acquisition_unconfirmed')

    def test_lease_changes_before_start_block_any_packet(self):
        for change in [dict(connected=False),dict(exclusive=False),dict(owner='xpad'),
                       dict(capabilities=frozenset()),dict(expires_at=0),dict(token='different-token-001'),
                       dict(target=replace(self.target,instance_token=43))]:
            with self.subTest(change=change):
                self.setUp();self.feed();self.adapter.prepare()
                self.channel.lease=replace(self.channel.lease,**change)
                self.adapter.tick()
                self.assertEqual(self.adapter.session.phase,'lost')
                self.assertEqual(self.channel.messages,[])
                self.assertEqual(self.channel.releases[0].target,self.target)

    def test_loss_during_preparation_has_no_start_or_exit(self):
        self.feed();self.adapter.prepare();key=self.adapter.session.key
        self.adapter.connection_lost(key);self.clock.advance(4);self.adapter.tick()
        self.assertEqual(self.channel.messages,[])
        self.assertEqual(self.adapter.session.phase,'lost')

    def test_cancel_after_start_sends_one_exit_only(self):
        self.start();self.feed(active=3,done=3)
        self.adapter.close();self.adapter.finish();self.adapter.close()
        self.assertEqual(self.channel.messages,[calibration_message('Start'),calibration_message('Exit')])
        self.assertEqual(len(self.channel.releases),1)

    def test_foreign_reports_and_loss_events_never_refresh_or_finish(self):
        self.start();before=self.adapter.session.last_sample_at
        current=self.report(telemetry(active=3,done=3))
        other_key=replace(current.key,instance=Instance('device-B','radio-connection-1'))
        for event in [replace(current,key=other_key),
                      replace(current,target=replace(self.target,instance_token=99)),
                      replace(current,lease_token='foreign-token-00001')]:
            self.assertFalse(self.adapter.receive(event))
        self.assertFalse(self.adapter.connection_lost(other_key))
        self.assertEqual(self.adapter.session.last_sample_at,before)
        self.assertFalse(self.adapter.finish())

    def test_reconnect_has_new_generation_and_needs_explicit_start(self):
        self.start();old=self.report(telemetry(active=3,done=3))
        self.adapter.connection_lost(self.adapter.session.key)
        self.assertTrue(self.adapter.open(self.target))
        self.assertNotEqual(self.adapter.session.key,old.key)
        self.assertFalse(self.adapter.receive(old))
        self.assertFalse(self.adapter.finish())
        self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_report_number_not_wrapping_device_sequence_controls_order(self):
        self.start()
        for seq in (254,255,0,1):self.assertTrue(self.feed(active=3,seq=seq))
        before=self.adapter.session.last_sample_at
        report=self.report(telemetry(active=3,done=3),number=0)
        self.assertFalse(self.adapter.receive(report))
        self.assertEqual(self.adapter.session.last_sample_at,before)
        self.assertFalse(self.adapter.finish())

    def test_nontelemetry_traffic_does_not_keep_dead_stream_ready(self):
        self.start();self.feed(active=3,done=3)
        for data in [bytes.fromhex('0320000487000000'),bytes.fromhex('20000120')+bytes(32),
                     b'\x10\x00\x00\x3c\x05'+bytes(59)]:
            self.assertFalse(self.adapter.receive(self.report(data)))
        self.clock.advance(MAX_SAMPLE_AGE+1);self.adapter.tick()
        self.assertEqual(self.adapter.session.phase,'lost')
        self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_malformed_current_status_stops_without_exit_or_finish(self):
        for data in [telemetry(active=3,done=3)[:-1],telemetry(active=0x13,done=3),
                     b'',bytearray(telemetry())]:
            with self.subTest(data=data):
                self.setUp();self.start()
                self.assertFalse(self.adapter.receive(self.report(data)))
                self.assertEqual(self.adapter.problem,'invalid_telemetry')
                self.assertEqual(self.adapter.session.phase,'error')
                self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_start_finish_and_exit_failure_never_retry(self):
        for operation in ('Start','Finish','Exit'):
            with self.subTest(operation=operation):
                self.setUp()
                if operation=='Start':
                    self.feed();self.adapter.prepare();self.channel.fail_send=True
                    for _ in range(31):self.feed();self.adapter.tick()
                else:
                    self.start();self.feed(active=3,done=3);self.channel.fail_send=True
                    if operation=='Finish':self.adapter.finish()
                    else:self.adapter.close()
                before=list(self.channel.messages)
                self.adapter.finish();self.adapter.close();self.adapter.tick()
                self.assertEqual(self.channel.messages,before)
                self.assertEqual(self.adapter.problem,'submission_failed')
                self.assertEqual(self.adapter.session.phase,'error')

    def test_connection_change_during_submission_is_uncertain_and_terminal(self):
        self.start();self.feed(active=3,done=3)
        self.channel.after_send=lambda c:setattr(c,'lease',replace(c.lease,connected=False))
        self.assertFalse(self.adapter.finish())
        self.assertEqual(self.adapter.session.phase,'lost')
        self.adapter.finish();self.adapter.close()
        self.assertEqual(self.channel.messages.count(calibration_message('Finish')),1)

    def test_cleanup_failure_preserves_cause_and_blocks_another_run(self):
        self.start();self.feed(active=3,done=3)
        self.channel.release_ok=False;self.channel.inspect_error=True
        self.assertFalse(self.adapter.finish())
        self.assertEqual(self.adapter.problem,'observation_failed')
        self.assertEqual(self.adapter.cleanup_problem,'lease_release_unconfirmed')
        self.assertFalse(self.adapter.open(self.target))
        self.adapter.close();self.adapter.tick()
        self.assertEqual(len(self.channel.releases),1)
        self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_direct_port_cannot_skip_the_session_order(self):
        self.feed()
        for operation in ('Start','Finish','Exit','flash'):
            with self.assertRaises(CalibrationFailure):
                self.adapter.port.submit(Intent(self.adapter.session.key,operation))
        self.assertEqual(self.channel.messages,[])

    def test_opaque_errors_are_not_exposed_as_backend_text(self):
        self.channel.inspect_error=True;self.adapter.tick()
        self.assertNotIn('/path',str(self.adapter.view()))
        self.assertEqual(self.adapter.problem,'observation_failed')

    def test_same_usb_binding_with_new_radio_lifetime_stops_before_finish(self):
        self.start();self.feed(active=3,done=3)
        different=replace(self.target,instance=Instance(self.target.instance.device,'radio-connection-2'))
        self.channel.lease=replace(self.channel.lease,target=different)
        self.assertFalse(self.adapter.finish())
        self.assertEqual(self.adapter.session.phase,'lost')
        self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_invalid_host_report_metadata_stops_and_releases_own_lease(self):
        for field,value in [('number',True),('timestamp',float('nan')),('timestamp',1e9),
                            ('timestamp',2**10000)]:
            with self.subTest(field=field):
                self.setUp();self.start()
                self.assertFalse(self.adapter.receive(replace(self.report(),**{field:value})))
                self.assertEqual(self.adapter.session.phase,'error')
                self.assertEqual(len(self.channel.releases),1)
                self.assertEqual(self.channel.messages,[calibration_message('Start')])

    def test_send_result_must_be_explicit_submission_success(self):
        for accepted in (False,None,1,'success'):
            with self.subTest(accepted=accepted):
                self.setUp();self.feed();self.adapter.prepare();self.channel.accepted=accepted
                for _ in range(40):
                    if self.adapter.session.phase!='preparing':break
                    self.feed();self.adapter.tick()
                self.assertEqual(self.adapter.session.phase,'error')
                self.assertEqual(self.adapter.problem,'submission_failed')
                self.assertEqual(len(self.channel.messages),1)

    def test_malformed_acquire_proof_cannot_grant_access(self):
        for mutation in [dict(expires_at=float('nan')),dict(expires_at=True),dict(expires_at=2**10000),
                         dict(connected=1),dict(exclusive=1),dict(token='x'),
                         dict(capabilities=set(CAPABILITIES))]:
            with self.subTest(mutation=mutation):
                self.setUp();self.adapter.close();original=self.channel.acquire
                self.channel.acquire=lambda target,key:replace(original(target,key),**mutation)
                self.assertFalse(self.adapter.open(self.target))
                self.assertTrue(self.adapter.acquisition_uncertain)
                self.assertEqual(self.channel.messages,[])

    def test_complete_injected_workflow_has_no_file_socket_ioctl_or_process_access(self):
        with ExitStack() as stack:
            for name in ('builtins.open','os.open','pathlib.Path.open','socket.socket',
                         'subprocess.run','subprocess.Popen','fcntl.ioctl'):
                stack.enter_context(patch(name,side_effect=AssertionError('Unexpected live I/O')))
            self.start();self.feed(active=3,done=3);self.adapter.finish();self.adapter.close()
        self.assertEqual(self.channel.messages,[calibration_message('Start'),calibration_message('Finish')])


if __name__=='__main__':unittest.main()
