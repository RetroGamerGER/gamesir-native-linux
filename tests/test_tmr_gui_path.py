#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""End-to-end source policy, fake manager/ABI, pipes and permissions; no devices."""
from dataclasses import replace
import copy
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import stat
import struct
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from tmr_wire import request, encode, decode, target, TmrFailure, FILES, HELPER, POLICY, ARGV
from tmr_channel import NativeChannel, ManagerSocket
from tmr_helper import Session, serve, PipeInput
from tmr_client import HelperClient, load_pins
from calibration_controller import ControllerCalibration, CONTINUITY_CAPABILITIES
from calibration_protocol import PositionPolicy
import test_tmr_maintenance as native_tests
report = native_tests.report


def load_script(name):
    sys.path.insert(0,str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class PathTests(unittest.TestCase):
    def setUp(self):
        self.fixture=native_tests.ManagerTmr();self.fixture.setUp()
        self.host,self.manager,self.backend=self.fixture.host,self.fixture.manager,self.fixture.backend
        self.calls=[]
        def call(value):
            self.calls.append(copy.deepcopy(value))
            return self.manager.command(value)
        self.session=Session(call,clock=lambda:self.host.now)
        self.number=0
        self.packet()

    def tearDown(self):
        self.session.close()

    def packet(self,active=0,done=0,raw=(128,128,128,128),advance=0):
        self.host.now+=advance
        s=self.backend.status
        packet=bytearray.fromhex(report(active,done));packet[51:55]=bytes(raw)
        s.update(report=packet.hex(),report_number=s['report_number']+1,
                 host_monotonic_ns=int(self.host.now*1e9))

    def send(self,action,**kw):
        self.number+=1
        return self.session.handle(encode({'schema':1,'id':self.number,'action':action,**kw}))

    def select(self):
        rows=self.send('list')['targets']
        self.assertEqual(len(rows),1)
        return self.send('select',target=rows[0])['view']

    def start(self):
        self.select();self.send('prepare')
        for _ in range(13):
            self.packet(advance=.25);self.send('poll')
        self.assertIn('Start',self.backend.calls)

    def test_listing_is_readonly_and_does_not_open_native_backend(self):
        rows=self.send('list')['targets']
        self.assertEqual(rows[0]['port_token'],11)
        self.host.open_tmr.assert_not_called()
        self.assertFalse(self.host.calls)

    def test_one_manager_poll_per_display_update_with_new_report(self):
        self.select();self.calls.clear();self.packet(advance=.1)
        view=self.send('poll')['view']
        self.assertTrue(view['canStart'])
        self.assertEqual([c['tmr'] for c in self.calls],['poll'])

    def test_one_manager_poll_does_not_forge_heartbeat_on_repeated_snapshot(self):
        self.select();before=self.session.adapter.session.last_sample_at
        self.calls.clear();self.host.now+=.2
        self.send('poll')
        self.assertEqual(self.session.adapter.session.last_sample_at,before)
        self.assertEqual([c['tmr'] for c in self.calls],['poll'])

    def test_empty_or_paused_manager_never_rebinds_or_starts_anything(self):
        self.manager.paused=True
        self.assertEqual(self.send('list')['targets'],[])
        self.host.open_tmr.assert_not_called()
        self.assertFalse(self.host.calls)

    def test_full_flow_start_movement_ready_finish_local_return(self):
        self.start()
        self.packet(3,3,(0,255,255,0),advance=.1)
        view=self.send('poll')['view']
        self.assertTrue(view['canFinish'])
        self.assertEqual(view['sticks'][0]['x'],-1)
        self.assertEqual(view['sticks'][0]['y'],-1)
        result=self.send('finish')['view']
        self.assertEqual(result['phase'],'completed')
        self.assertFalse(result['leaseHeld'])
        self.assertEqual([c for c in self.backend.calls if c!='renew'],['acquire','Start','Finish','release'])
        self.assertFalse(self.host.calls)

    def test_readiness_without_a_full_ui_ring_is_sufficient(self):
        self.start();self.packet(3,3,advance=.1)
        view=self.send('poll')['view']
        self.assertTrue(view['canFinish']);self.assertEqual(view['sticks'][0]['coverage'],0)

    def test_partial_ready_never_finishes(self):
        self.start();self.packet(3,1,advance=.1);self.send('poll')
        self.assertFalse(self.send('finish')['view']['canFinish'])
        self.assertNotIn('Finish',self.backend.calls)

    def test_cancel_after_start_sends_one_exit_and_no_finish(self):
        self.start();self.send('cancel');self.session.close(explicit=True)
        self.assertEqual(self.backend.calls.count('Exit'),1)
        self.assertNotIn('Finish',self.backend.calls)
        self.assertEqual(self.backend.calls.count('release'),1)

    def test_cancel_before_or_during_preparation_has_no_usb_command(self):
        self.select();self.send('prepare');self.send('cancel')
        self.assertEqual([c for c in self.backend.calls if c!='renew'],['acquire','release'])

    def test_abrupt_pipe_loss_returns_lease_without_exit(self):
        self.start();self.session.close()
        self.assertNotIn('Exit',self.backend.calls)
        self.assertNotIn('Finish',self.backend.calls)
        self.assertFalse(self.manager.tmr.runs)

    def test_silence_stops_and_rereads_do_not_create_a_heartbeat(self):
        self.start()
        number=self.session.adapter.session.last_sequence
        self.send('poll')
        self.assertEqual(self.session.adapter.session.last_sequence,number)
        self.host.now+=1.6
        self.assertFalse(self.send('poll')['view']['running'])
        self.assertNotIn('Exit',self.backend.calls)
        self.assertNotIn('Finish',self.backend.calls)

    def test_changed_epoch_or_instance_is_terminal(self):
        for field in ('stream_epoch','instance_token','generation'):
            with self.subTest(field=field):
                self.setUp();self.start();self.backend.status[field]+=1
                self.assertFalse(self.send('poll')['view']['running'])
                self.assertNotIn('Exit',self.backend.calls)
                self.session.close()

    def test_no_rf_identity_claim_and_strict_default_stays_strict(self):
        view=self.select();a=self.session.adapter
        self.assertEqual(view['linkBasis'],'fresh_e0_continuity_only')
        self.assertFalse(a.lease.connected)
        self.assertEqual(a.lease.capabilities,CONTINUITY_CAPABILITIES)
        strict=ControllerCalibration(PositionPolicy('raw',(1,1,1,1)))
        strict.target=a.target;strict.session.key=a.session.key
        self.assertFalse(strict._valid_lease(a.lease))
        self.assertFalse(a._valid_lease(replace(a.lease,connected=True)))

    def test_wrong_selection_not_admitted_and_changed_tokens_not_reselected(self):
        row=self.send('list')['targets'][0];row['instance_token']+=1
        with self.assertRaises(TmrFailure):self.send('select',target=row)
        self.host.open_tmr.assert_not_called()

    def test_changed_selection_between_list_and_acquire_stops(self):
        row=self.send('list')['targets'][0]
        self.manager.entries[row['port']].kernel_tokens=[11,23]
        with self.assertRaises(Exception):self.send('select',target=row)
        self.assertFalse(self.backend.calls)

    def test_original_send_failure_survives_cleanup_failure_without_replay(self):
        self.select();self.send('prepare')
        original=self.backend.command
        def command(op,*args):
            if op in ('Start','release'):
                self.backend.calls.append(op);raise OSError('private diagnostic')
            return original(op,*args)
        self.backend.command=command
        for _ in range(13):
            self.packet(advance=.25)
            if self.session.adapter.session.snapshot()['running']:self.send('poll')
        view=self.session.view()
        self.assertEqual(view['adapterProblem'],'submission_failed')
        self.assertTrue(view['cleanupProblem'])
        self.assertEqual(self.backend.calls.count('Start'),1)
        self.assertNotIn('Exit',self.backend.calls)
        self.assertNotIn('private',str(view))

    def test_duplicate_request_or_second_selection_is_rejected(self):
        self.select()
        with self.assertRaises(TmrFailure):
            self.session.handle(encode({'schema':1,'id':self.number,'action':'poll'}))
        with self.assertRaises(TmrFailure):self.send('select',target=self.session.targets[0])

    def test_no_lease_token_or_run_generation_leaks_to_view(self):
        view=self.select()
        self.assertNotIn(self.session.channel.token,str(view))
        self.assertNotIn('port_token',view)

    def test_manager_rejects_nonempty_listing_parameters(self):
        with self.assertRaises(Exception):
            self.manager.command({'version':1,'tmr':'list','port':'1-1'})

    def test_unsupported_identity_and_nonstick_flags_rejected(self):
        self.select()
        for change in ({'pid':0x100a},{'flags':15},{'report':'10'*64}):
            status=copy.deepcopy(self.backend.status);status.update(change)
            with self.assertRaises(TmrFailure):self.session.channel._status({'status':status},leased=True)

    def test_timestamp_or_count_regression_and_inconsistent_pair_rejected(self):
        self.select();c=self.session.channel
        for change in ({'report_number':1},{'host_monotonic_ns':2},
                       {'report_number':c.last_number+1}):
            status=copy.deepcopy(c.status);status.update(change)
            with self.assertRaises(TmrFailure):c._status({'status':status},leased=True)


    def test_multiple_controllers_only_selected_zzz_gets_a_lease(self):
        other=native_tests.device(port='2-3.5',pid='105e',driver='gs_native')
        xbox=native_tests.device(port='2-3.6',pid='100a',driver='xpad')
        for dev,tokens in ((other,[33,44]),(xbox,[55,66])):
            self.host.devices[dev.port]=dev
            self.manager.observed[dev.port]=dev
            self.manager.entries[dev.port]=native_tests.service.Entry(dev,'active',kernel_tokens=tokens)
        zzz=native_tests.Backend(self.host)
        zzz.status.update(pid=0x105e,port_token=33,instance_token=44)
        self.host.open_tmr=Mock(side_effect=lambda dev:zzz if dev.port==other.port else self.backend)
        rows=self.send('list')['targets']
        self.assertEqual(len(rows),2)
        chosen=next(row for row in rows if row['pid']==0x105e)
        view=self.send('select',target=chosen)['view']
        self.assertTrue(view['canStart'])
        self.send('cancel')
        self.assertEqual(self.backend.calls,[])
        self.assertEqual([c for c in zzz.calls if c!='renew'],['acquire','release'])
        self.assertTrue(all(call.args[0]==other for call in self.host.open_tmr.call_args_list))
        self.assertFalse(self.host.calls)

    def test_disabled_native_api_never_enables_module_or_uses_fallback(self):
        row=self.send('list')['targets'][0]
        self.host.open_tmr.side_effect=ValueError('experimental_tmr is disabled')
        with self.assertRaises(native_tests.service.Unsafe):self.send('select',target=row)
        self.assertFalse(self.host.calls)
        self.assertFalse(self.backend.calls)

    def test_old_kernel_status_cannot_satisfy_native_contract(self):
        row=self.send('list')['targets'][0]
        self.backend.status.pop('report_number')
        with self.assertRaises(Exception):self.send('select',target=row)
        self.assertNotIn('Start',self.backend.calls)
        self.assertNotIn('Exit',self.backend.calls)


class WireAndPermission(unittest.TestCase):
    def test_unknown_or_extra_operations_are_refused_before_process(self):
        for action in ('resume','release','flash','Start','End','install'):
            with self.assertRaises(TmrFailure):request(encode({'schema':1,'id':1,'action':action}))
        for field in ('path','command','payload','token'):
            with self.assertRaises(TmrFailure):request(encode({'schema':1,'id':1,'action':'list',field:'x'}))

    def test_duplicate_fields_bool_numbers_and_oversized_input_refused(self):
        for wire in (b'{"schema":1,"schema":1,"id":1,"action":"list"}\n',
                     encode({'schema':True,'id':1,'action':'list'}),
                     encode({'schema':1,'id':True,'action':'list'}),b'x'*16385,b'{}',b'[]\n'):
            with self.assertRaises(TmrFailure):request(wire)

    def test_target_scope_rejects_paths_other_vid_pids_or_tokens(self):
        base={'port':'1-2.3','pid':0x109c,'port_token':1,'instance_token':2}
        for change in ({'port':'../../dev/input'},{'pid':0x100a},{'pid':True},
                       {'port_token':True},{'instance_token':0},{'vendor':0x054c}):
            with self.assertRaises(TmrFailure):target(dict(base,**change))

    def test_policy_is_separate_active_session_admin_without_cache(self):
        path=ROOT/'packaging/control-center/tmr'/Path(POLICY).name
        action=ET.parse(path).find('action')
        self.assertEqual(action.findtext('defaults/allow_active'),'auth_admin')
        self.assertEqual(action.findtext('defaults/allow_inactive'),'no')
        self.assertEqual(action.findtext('defaults/allow_any'),'no')
        self.assertEqual(action.find('annotate').text,HELPER)
        self.assertIn('save',action.findtext('message'))

    def test_import_and_client_construction_are_inert(self):
        spawn=Mock();auditor=Mock()
        client=HelperClient({p:'a'*64 for p in FILES},spawn=spawn,auditor=auditor)
        spawn.assert_not_called();auditor.inspect.assert_not_called()
        client.close();spawn.assert_not_called()

    def test_changed_or_missing_helper_refused_before_pkexec(self):
        auditor=Mock();auditor.inspect.side_effect=OSError('missing')
        spawn=Mock();client=HelperClient({p:'a'*64 for p in FILES},spawn=spawn,auditor=auditor)
        with self.assertRaises(OSError):client.call('list')
        spawn.assert_not_called()

    def test_fixed_spawn_has_no_shell_credentials_or_appimage_script(self):
        child=Mock();child.stdin=io.BytesIO();child.stdout=io.BytesIO()
        spawn=Mock(return_value=child)
        client=HelperClient({p:'a'*64 for p in FILES},spawn=spawn,auditor=Mock())
        client.start()
        args,kw=spawn.call_args
        self.assertEqual(args,(ARGV,));self.assertFalse(kw['shell'])
        self.assertEqual(set(kw['env']),{'PATH','LANG','LC_ALL'})
        client.close()

    def test_pipe_fragments_coalesced_requests_and_eof(self):
        read,write=os.pipe()
        try:
            os.write(write,b'{"action":"list"}\n{}\n');os.close(write);write=None
            pipe=PipeInput(read)
            self.assertEqual(pipe.read(.1),b'{"action":"list"}\n')
            self.assertEqual(pipe.read(.1),b'{}\n')
            with self.assertRaises(TmrFailure):pipe.read(.1)
        finally:
            os.close(read)
            if write is not None:os.close(write)

    def test_server_failure_always_returns_lease_without_device_exit(self):
        session=Mock();session.closed=False;session.adapter=True
        self.assertEqual(serve(Mock(side_effect=EOFError),Mock(),session),2)
        session.close.assert_called_once_with(explicit=False)

    def test_offline_staging_has_eight_hashed_files_and_no_install(self):
        builder=load_script('stage_tmr_helper')
        with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='tmr-stage-test-') as tmp:
            dest=builder.stage(Path(tmp)/'new')
            pins=load_pins(dest/'tmr-helper.json')
            self.assertEqual(set(pins),set(FILES))
            self.assertEqual(len(pins),8)
            for name,digest in pins.items():
                import hashlib
                self.assertEqual(hashlib.sha256((dest/'root'/name.lstrip('/')).read_bytes()).hexdigest(),digest)
            packager=load_script('package_control_center')
            app=Path(tmp)/'app';app.mkdir()
            packager.stage_calibration_helper(dest,app)
            self.assertTrue((app/'tmr-helper.json').is_file())
            (dest/'root'/HELPER.lstrip('/')).write_text('changed')
            with self.assertRaises(ValueError):packager.stage_calibration_helper(dest,Path(tmp)/'bad')

    def test_bad_pins_or_unexpected_files_are_refused(self):
        for pins in ({},{p:'a'*63 for p in FILES},dict({p:'a'*64 for p in FILES},extra='a'*64)):
            with self.assertRaises(TmrFailure):HelperClient(pins)


    def test_isolated_helper_entry_refuses_execution_from_uninstalled_source(self):
        result=subprocess.run([sys.executable,'-IBS',str(ROOT/'packaging/control-center/tmr/execute')],
                              capture_output=True,timeout=5)
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stdout,b'')
        self.assertEqual(result.stderr,b'')

    def test_helper_main_rejects_missing_caller_or_nonroot_before_input(self):
        import tmr_helper
        for uid,caller in ((1000,'1000'),(0,''),(0,'0'),(0,'x'),(0,'1'*100)):
            with patch.object(tmr_helper.os,'geteuid',return_value=uid), \
                 patch.dict(tmr_helper.os.environ,{'PKEXEC_UID':caller}), \
                 patch.object(tmr_helper.sys,'argv',['execute']), \
                 patch.object(tmr_helper,'PipeInput') as reader:
                self.assertEqual(tmr_helper.main(),2)
                reader.assert_not_called()


    def test_manager_socket_requires_root_private_directory_and_socket(self):
        directory=SimpleNamespace(st_mode=stat.S_IFDIR|0o700,st_uid=0)
        leaf=SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_uid=0)
        for a,b in ((SimpleNamespace(st_mode=stat.S_IFLNK|0o777,st_uid=0),leaf),
                    (SimpleNamespace(st_mode=stat.S_IFDIR|0o755,st_uid=0),leaf),
                    (directory,SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_uid=1000)),
                    (directory,SimpleNamespace(st_mode=stat.S_IFSOCK|0o666,st_uid=0))):
            with patch('tmr_channel.os.lstat',side_effect=[a,b]),patch('tmr_channel.socket.socket') as spawn:
                with self.assertRaises(TmrFailure):ManagerSocket()({'version':1,'tmr':'list'})
                spawn.assert_not_called()

    def test_manager_socket_checks_peer_before_sending_any_request(self):
        infos=[SimpleNamespace(st_mode=stat.S_IFDIR|0o700,st_uid=0),
               SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_uid=0)]
        with patch('tmr_channel.os.lstat',side_effect=infos),patch('tmr_channel.socket.socket') as factory:
            connection=factory.return_value.__enter__.return_value
            connection.getsockopt.return_value=struct.pack('3i',999,1000,1000)
            with self.assertRaises(TmrFailure):ManagerSocket()({'version':1,'tmr':'list'})
            connection.sendall.assert_not_called()

    def test_manager_socket_handles_fragmented_reply_without_an_actual_socket(self):
        infos=[SimpleNamespace(st_mode=stat.S_IFDIR|0o700,st_uid=0),
               SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_uid=0)]
        with patch('tmr_channel.os.lstat',side_effect=infos),patch('tmr_channel.socket.socket') as factory:
            connection=factory.return_value.__enter__.return_value
            connection.getsockopt.return_value=struct.pack('3i',999,0,0)
            connection.recv.side_effect=[b'{"ok":',b'true,"targets":[]}\n']
            self.assertEqual(ManagerSocket()({'version':1,'tmr':'list'}),{'targets':[]})
            connection.connect.assert_called_once_with('/run/gamesir-native/control.sock')
            connection.sendall.assert_called_once_with(encode({'version':1,'tmr':'list'}))


class PipeChild:
    """Unprivileged pipes/thread only; never a real pkexec or manager socket."""
    def __init__(self, manager=None, mode='normal'):
        read_in, write_in=os.pipe();read_out, write_out=os.pipe()
        self.stdin=os.fdopen(write_in,'wb',buffering=0)
        self.stdout=os.fdopen(read_out,'rb',buffering=0)
        self.code=None;self.rows=[]
        def run():
            try:
                pipe=PipeInput(read_in)
                if manager:
                    def writer(data):os.write(write_out,data)
                    self.code=serve(pipe.read,writer,Session(manager))
                elif mode=='denied':self.code=126
                else:
                    while True:
                        v=request(pipe.read(1))
                        self.rows.append(v)
                        if mode=='cancel_wait':
                            threading.Event().wait(.2)
                        reply=encode({'schema':1,'id':v['id']+(mode=='wrong_id'),
                                      'ok':True,'targets':[],'view':None})
                        if mode=='oversized':reply=b'x'*17000
                        # Deliberately split the pipe response.
                        os.write(write_out,reply[:7]);os.write(write_out,reply[7:])
            except (OSError,ValueError):self.code=2
            finally:
                os.close(read_in);os.close(write_out)
                self.code=self.code if self.code is not None else 0
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()

    def wait(self,timeout):
        self.thread.join(timeout)
        if self.thread.is_alive():raise subprocess.TimeoutExpired('offline pipe fixture',timeout)
        return self.code


class PipeClientTests(unittest.TestCase):
    def client(self,mode='normal'):
        self.children=[]
        def spawn(*args,**kw):
            child=PipeChild(mode=mode);self.children.append(child);return child
        self.client_under_test=HelperClient({p:'a'*64 for p in FILES},auditor=Mock(),spawn=spawn)
        return self.client_under_test

    def tearDown(self):
        if hasattr(self,'client_under_test'):self.client_under_test.close()
        for child in getattr(self,'children',[]):child.thread.join(1)

    def test_one_permission_process_with_fragmented_replies_and_incremental_ids(self):
        client=self.client()
        self.assertEqual(client.call('list')['targets'],[])
        client.call('poll');client.call('cancel')
        self.assertEqual(len(self.children),1)
        self.assertEqual([v['id'] for v in self.children[0].rows],[1,2,3])
        self.assertEqual([v['action'] for v in self.children[0].rows],['list','poll','cancel'])

    def test_denied_or_cancelled_polkit_has_no_manager_request(self):
        client=self.client('denied')
        with self.assertRaises(TmrFailure):client.call('list')
        self.assertTrue(client.closed)
        self.assertEqual(self.children[0].rows,[])

    def test_wrong_response_generation_or_limit_closes_pipe_without_retry(self):
        for mode in ('wrong_id','oversized'):
            client=self.client(mode)
            with self.assertRaises(TmrFailure):client.call('list')
            self.assertTrue(client.closed)
            with self.assertRaises(TmrFailure):client.call('list')
            self.assertEqual(len(self.children),1)
            self.tearDown()

    def test_cancel_during_pending_reply_closes_pipe(self):
        client=self.client('cancel_wait')
        cancel=threading.Event();client.cancelled=cancel.is_set
        timer=threading.Timer(.03,cancel.set);timer.start()
        try:
            with self.assertRaises(TmrFailure):client.call('list')
        finally:timer.join()
        self.assertTrue(client.closed)
        self.assertEqual(len(self.children[0].rows),1)

    def test_request_before_listing_cannot_spawn(self):
        client=self.client()
        with self.assertRaises(TmrFailure):client.call('poll')
        self.assertEqual(self.children,[])


if __name__=='__main__':unittest.main()
