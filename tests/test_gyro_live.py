#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Live transport tests use pipes, synthetic/saved files and fake IIO only."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import select
import threading
from unittest.mock import patch
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/imu'))
import gamesir_gyro_live as live
import gamesir_gyro_worker as worker
import gamesir_gyro_guided as guided
from gamesir_imu_diagnostic import OBSERVED_AXIS_PROFILE
from gyro_view_model import Clip, rotation_degrees
import test_gyro_worker as wf
import test_gyro_view_model as mf


SNAP = {'directory':'/synthetic/iio:device9','iio_identity':[1,2],
        'device_node':'/synthetic-node','buffer_enable':'0','buffer_stream_active':'0'}
INSTANCE='/synthetic/iio:device9:1:2'


def event(name,**fields):
    return dict(protocol_version=1,event=name,**fields)


def ready():
    return event('ready',capture_seconds=None,device_opened=False,buffer_modified=False)


def started(stamp=1_000_000_000):
    return event('capture_started',monotonic_ns=stamp,instance_id=INSTANCE)


def row(stamp=1_010_000_000,count=1):
    return dict(timestamp_ns=stamp,sample_number=count,gyro_raw=[0,100,0],
                accel_raw=[0,8192,0],coherent=True,timebase='host_monotonic_receive',
                source_kind='iio_buffer',instance_id=INSTANCE)


def finished(count=1,passed=True):
    return event('finished',passed=passed,restored=True,failure=None if passed else 'original fault',
                 observations=count,cleanup_errors=[])


class Protocol(unittest.TestCase):
    def stream(self):
        s=live.LiveEvents(SNAP,2000)
        s.accept(ready(),1_000_000_000);s.accept(started(),1_000_000_000)
        return s

    def test_ready_start_samples_finish_and_no_commands_from_events(self):
        s=self.stream();s.accept(event('sample',row=row()),1_020_000_000)
        s.accept(finished(),1_030_000_000)
        self.assertEqual(s.count,1);self.assertEqual(s.state,'finished')
        with self.assertRaises(ValueError):s.accept(event('sample',row=row()),1_040_000_000)

    def test_profile_change_keeps_raw_and_transport_guards(self):
        s=self.stream();s.accept(event('sample',row=row()),1_020_000_000)
        raw=s.last_row['gyro_raw'][:];s.pose.gain=2
        s.select_profile(125)
        self.assertIsNone(s.pose.frame);self.assertEqual(s.pose.gain,2)
        s.accept(event('sample',row=row(1_030_000_000,2)),1_040_000_000)
        self.assertEqual(s.pose.frame.gyro_raw,tuple(raw));self.assertEqual(s.count,2)
        self.assertAlmostEqual(s.pose.frame.body_dps[2],.4375)
        self.assertAlmostEqual(rotation_degrees(s.pose.orientation),0)
        s.select_profile(2000)
        with self.assertRaisesRegex(ValueError,'counter'):
            s.accept(event('sample',row=row(1_040_000_000,4)),1_050_000_000)

    def test_offline_and_live_integration_identical(self):
        rows=mf.samples(count=501)
        for r in rows:r.update(instance_id=INSTANCE,source_kind='iio_buffer')
        c=Clip.from_samples(rows,profile=2000,axis_profile=OBSERVED_AXIS_PROFILE)
        s=self.stream()
        for r in rows:s.accept(event('sample',row=r),r['timestamp_ns']+1)
        self.assertEqual(s.pose.frame,c.frames[-1]);self.assertEqual(s.count,len(rows))

    def test_no_108_second_or_100000_sample_preview_limit(self):
        s=self.stream();s.accept(event('sample',row=row()),1_020_000_000)
        s.pose.integrator.count=100_000
        s.count=100_000
        s.accept(event('sample',row=row(1_020_000_000,2)),1_030_000_000)
        self.assertEqual(s.count,100_001)
        # At a far-future live time, adjacent fresh samples still work.
        s=self.stream();s.started_ns=10**15
        s.accept(event('sample',row=row(10**15+1,1)),10**15+2)
        self.assertEqual(s.count,1)

    def test_invalid_identity_timing_counter_source_and_raw_stop(self):
        for change in ({'instance_id':'replacement'},{'source_kind':'synthetic'},
                       {'coherent':False},{'timestamp_ns':1},{'timestamp_ns':9_000_000_000},
                       {'gyro_raw':[float('nan'),0,0]},{'gyro_raw':[32767,0,0]}):
            s=self.stream();r=row();r.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                s.accept(event('sample',row=r),1_020_000_000)
        for r in (row(1_400_000_000,2),row(1_020_000_000,3),row(1_010_000_000,2)):
            s=self.stream();s.accept(event('sample',row=row()),1_020_000_000)
            with self.assertRaises(ValueError):s.accept(event('sample',row=r),1_500_000_000)

    def test_protocol_order_version_and_false_success_rejected(self):
        for bad in (event('sample',row=row()),started(),dict(ready(),protocol_version=True),
                    dict(ready(),capture_seconds=108),event('command',command='GO')):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                live.LiveEvents(SNAP,2000).accept(bad,1_020_000_000)
        s=self.stream()
        with self.assertRaises(ValueError):s.accept(ready(),1_020_000_000)
        with self.assertRaises(ValueError):s.accept(finished(99),1_020_000_000)


class ContinuousWorker(unittest.TestCase):
    def setup_run(self):
        self.evidence=wf.MemoryEvidence();self.channel=wf.FakeParent();self.tx=wf.FakeTransaction()
        self.manifest={'snapshot':SNAP,'profile':2000,'axis_profile':OBSERVED_AXIS_PROFILE}

    def run_worker(self, reader):
        return worker.execute(self.manifest,self.evidence,self.channel,stream=True,
                              transaction_factory=lambda s:self.tx,reader=reader)

    def test_continuous_explicit_stop_restores_and_stores_summary_only(self):
        self.setup_run()
        def reader(metadata,node,duration,no_data,**kwargs):
            self.assertIsNone(duration)
            yield wf.synthetic_frame(1,time.monotonic_ns()),time.monotonic_ns()
            raise worker.FrontendStop('frontend STOP; cancel and restore')
        self.assertEqual(self.run_worker(reader),0)
        self.assertEqual(self.tx.restore_calls,1)
        self.assertNotIn('scans.bin',self.evidence.handles)
        self.assertNotIn('observations.jsonl',self.evidence.handles)
        report=self.evidence.documents['report.json']
        self.assertTrue(report['stopped_by_user']);self.assertIsNone(report['capture_seconds'])
        self.assertFalse(report['raw_recording']);self.assertEqual(report['original_bytes'],0)
        self.assertEqual([e['event'] for e in self.channel.events],['ready','capture_started','sample','finished'])

    def test_eof_stall_and_broken_output_preserve_fault_and_restore(self):
        for fault in ('frontend pipe closed','IIO EOF/disconnect','frontend heartbeat lost'):
            self.setup_run()
            def reader(*args,**kwargs):
                yield wf.synthetic_frame(1,time.monotonic_ns()),time.monotonic_ns()
                raise ValueError(fault)
            self.assertEqual(self.run_worker(reader),1);self.assertEqual(self.tx.restore_calls,1)
            self.assertIn(fault,self.evidence.documents['report.json']['failure'])
        self.setup_run();self.channel.break_event='sample'
        def reader(*args,**kwargs):yield wf.synthetic_frame(1,time.monotonic_ns()),time.monotonic_ns()
        self.assertEqual(self.run_worker(reader),1);self.assertEqual(self.tx.restore_calls,1)

    def test_unexpected_reader_end_or_stop_with_failed_rollback_not_success(self):
        self.setup_run()
        def ended(*args,**kwargs):yield wf.synthetic_frame(1,time.monotonic_ns()),time.monotonic_ns()
        self.assertEqual(self.run_worker(ended),1)
        self.assertIn('without explicit STOP',self.evidence.documents['report.json']['failure'])
        self.setup_run();self.tx.restored=False
        def stopped(*args,**kwargs):
            raise worker.FrontendStop('STOP')
            yield
        self.assertEqual(self.run_worker(stopped),1)
        self.assertFalse(self.channel.events[-1]['passed'])

    def test_live_pipe_nonblocking_and_full_pipe_stop_deadline(self):
        r,w=os.pipe();parent_r,parent_w=os.pipe()
        try:
            with os.fdopen(w,'w') as output:
                channel=worker.LiveParentChannel(parent_r,output)
                channel.emit('ready',capture_seconds=None)
                self.assertEqual(json.loads(os.read(r,4096))['protocol_version'],1)
                while True:
                    try:os.write(w,b'x'*4096)
                    except BlockingIOError:break
                os.write(parent_w,b'STOP\n')
                with self.assertRaises(worker.FrontendStop):channel.emit('sample',row=row())
                with patch.object(worker.time,'monotonic',side_effect=[0,1]):
                    with self.assertRaisesRegex(ValueError,'not draining'):channel.emit('sample',row=row())
        finally:
            os.close(r);os.close(parent_r);os.close(parent_w)

    def test_continuous_reader_requires_owned_fd_and_watchdog(self):
        from gamesir_imu_stream import live_chunks
        with self.assertRaisesRegex(ValueError,'watchdog'):
            list(live_chunks({},'/never-open',None,2))

    def test_stop_during_forward_does_not_count_undelivered_sample(self):
        self.setup_run()
        original=self.channel.emit
        def emit(name,**fields):
            if name=='sample':raise worker.FrontendStop('STOP during forward')
            original(name,**fields)
        self.channel.emit=emit
        def reader(*args,**kwargs):yield wf.synthetic_frame(1,time.monotonic_ns()),time.monotonic_ns()
        self.assertEqual(self.run_worker(reader),0)
        self.assertEqual(self.evidence.documents['report.json']['observations'],0)
        self.assertEqual(self.channel.events[-1]['observations'],0)

    def test_actual_worker_pipe_roundtrip_go_samples_stop_and_restore(self):
        self.setup_run()
        input_r,input_w=os.pipe();output_r,output_w=os.pipe()
        result=[];pending=b'';events=live.LiveEvents(SNAP,2000)
        output=os.fdopen(output_w,'w')
        channel=worker.LiveParentChannel(input_r,output)
        original_setup=self.tx.setup
        def setup():
            metadata,fd=original_setup();metadata['instance_id']=INSTANCE
            return metadata,fd
        self.tx.setup=setup
        def reader(*args,check_alive,**kwargs):
            for count in range(1,4):
                check_alive()
                yield wf.synthetic_frame(count,time.monotonic_ns()),time.monotonic_ns()
            while True:
                check_alive();time.sleep(.001)
        def run():
            try:
                result.append(worker.execute(self.manifest,self.evidence,channel,stream=True,
                              transaction_factory=lambda s:self.tx,reader=reader))
            except BaseException as exc:result.append(exc)
        thread=threading.Thread(target=run,daemon=True);thread.start()
        try:
            deadline=time.monotonic()+2
            while not events.finished and time.monotonic()<deadline:
                if not select.select([output_r],[],[],.1)[0]:continue
                pending+=os.read(output_r,4096)
                while b'\n' in pending:
                    line,_,pending=pending.partition(b'\n')
                    kind=events.accept(json.loads(line),time.monotonic_ns())
                    if kind=='ready':os.write(input_w,b'GO\n')
                    if kind=='sample' and events.count==3:
                        os.write(input_w,b'STOP\n');os.close(input_w);input_w=None
            thread.join(1)
            self.assertEqual(result,[0]);self.assertFalse(thread.is_alive())
            self.assertTrue(events.finished['passed']);self.assertEqual(events.count,3)
            self.assertEqual(self.tx.restore_calls,1)
            self.assertFalse(self.evidence.handles)
        finally:
            if input_w is not None:os.close(input_w)
            thread.join(1);output.close();os.close(input_r);os.close(output_r)


class FakeProcess:
    def __init__(self):
        self.input_read,input_write=os.pipe();output_read,self.output_write=os.pipe()
        self.stdin=os.fdopen(input_write,'wb',buffering=0)
        self.stdout=os.fdopen(output_read,'rb',buffering=0)
        os.set_blocking(self.input_read,False)
        self.code=None

    def emit(self,value):os.write(self.output_write,(json.dumps(value)+'\n').encode())
    def poll(self):return self.code
    def commands(self):
        try:return os.read(self.input_read,8192)
        except BlockingIOError:return b''
    def close(self):
        self.stdin.close();self.stdout.close();os.close(self.input_read);os.close(self.output_write)


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name)
        self.home_patch=patch.object(guided,'home_directory',return_value=self.home);self.home_patch.start()
        self.process=FakeProcess();self.now=0
        self.report={'session':'live_view','completed':True,'restored':True,'failure':None,
                     'stopped_by_user':True,'observations':0}
        self.launch_count=0
        def launch(*args):self.launch_count+=1;return self.process
        self.session=live.LiveSession(self.home/'run',2000,discover=lambda:copy.deepcopy(SNAP),
            snapshot=lambda *args:copy.deepcopy(SNAP),launch=launch,
            verify=lambda *args:dict(self.report),clock=lambda:self.now)

    def tearDown(self):
        self.process.close();self.home_patch.stop();self.tmp.cleanup()

    def poll(self):
        self.session.poll()

    def arm(self):
        self.session.start();self.poll();self.process.commands()
        self.process.emit(ready());self.poll()
        self.assertEqual(self.session.state,'ready')

    def test_open_is_inert_waiting_and_one_launch_no_go_until_user(self):
        self.assertEqual(self.launch_count,0);self.assertFalse((self.home/'run').exists())
        self.session.discover=lambda:None;self.session.start();self.poll()
        self.assertEqual(self.launch_count,0)
        self.session.discover=lambda:SNAP;self.now=.6;self.poll()
        self.assertEqual(self.launch_count,1);self.assertNotIn(b'GO',self.process.commands())
        self.process.emit(ready());self.poll();self.session.go()
        self.assertIn(b'GO\n',self.process.commands())
        with self.assertRaises(ValueError):self.session.start()

    def test_normal_stop_independent_check_and_summary(self):
        self.arm();self.session.stop()
        self.assertIn(b'STOP\n',self.process.commands())
        self.process.emit(finished(0));self.process.code=0;self.poll()
        self.assertEqual(self.session.state,'done');self.assertTrue(self.session.restored)
        self.assertTrue(json.loads((self.home/'run/frontend-result.json').read_text())['passed'])

    def test_missing_finish_preserves_fault_even_if_snapshot_restored(self):
        self.arm();self.process.code=1;self.poll();self.poll()
        self.assertEqual(self.session.state,'error');self.assertTrue(self.session.restored)
        self.assertIn('without a verified',self.session.failure)

    def test_failed_postcheck_never_claims_rollback(self):
        self.arm();self.session.stop();self.process.emit(finished(0));self.process.code=0
        self.session.snapshot=lambda *args:{'replacement':True}
        self.poll();self.assertFalse(self.session.restored)
        self.assertIn('NICHT bestätigt',self.session.message)

    def test_stale_stream_stops_once_no_replacement_adoption(self):
        self.arm();self.session.go()
        stamp=time.monotonic_ns();self.process.emit(started(stamp));self.poll()
        self.assertEqual(self.session.state,'running')
        with patch.object(live.time,'monotonic_ns',return_value=stamp+2_100_000_000):self.poll()
        self.assertEqual(self.session.state,'stopping');self.assertTrue(self.session.stop_sent)
        self.process.commands();self.session.stop('secondary');self.assertEqual(self.process.commands(),b'')
        self.assertIn('keine frischen',self.session.failure);self.assertEqual(self.launch_count,1)

    def test_auth_cancel_and_cleanup_timeout_no_force_kill_or_restart(self):
        self.session.start();self.poll();self.session.stop()
        self.now=121;self.poll()
        self.assertEqual(self.session.state,'error');self.assertFalse(self.session.restored)
        self.assertEqual(self.launch_count,1);self.assertIsNone(self.process.code)

    def test_no_device_timeout_and_unexpected_backend_error_fail_closed(self):
        self.session.discover=lambda:None;self.session.start();self.now=61;self.poll()
        self.assertEqual(self.session.state,'error');self.assertEqual(self.launch_count,0)

    def test_new_manifest_fixed_sources_and_profile_changes_are_local(self):
        self.arm()
        m=json.loads((self.home/'run/manifest.json').read_text())
        self.assertEqual(m['kind'],worker.LIVE_KIND)
        self.assertEqual(set(m['source_sha256']),set(worker.LIVE_SOURCES))
        self.assertEqual(worker.read_manifest(self.home/'run/manifest.json'),m)
        self.session.select_profile(125)
        self.assertEqual(worker.read_manifest(self.home/'run/manifest.json')['profile'],2000)
        self.assertEqual(self.session.events.pose.integrator.profile,125)


class Evidence(unittest.TestCase):
    def test_summary_checksums_and_restoration_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);capture=output/'capture';capture.mkdir(mode=0o700)
            files={'report.json':{'session':'live_view','capture_seconds':None,'raw_recording':False,
                                 'restored':True,'cleanup_errors':[]},
                   'buffer-transaction.json':{'restored':True,'errors':[],'before':SNAP}}
            def save():
                hashes=[]
                for name,value in files.items():
                    raw=json.dumps(value).encode();p=capture/name;p.write_bytes(raw);p.chmod(0o600)
                    hashes.append(hashlib.sha256(raw).hexdigest()+'  '+name+'\n')
                p=capture/'SHA256SUMS';p.write_text(''.join(hashes));p.chmod(0o600)
            save();self.assertTrue(live.verify_result(output,{'snapshot':SNAP})['restored'])
            (capture/'report.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'checksum'):live.verify_result(output,{'snapshot':SNAP})
            files['buffer-transaction.json']['restored']=False;save()
            with self.assertRaisesRegex(ValueError,'restoration'):live.verify_result(output,{'snapshot':SNAP})

    def test_discovery_metadata_only_none_unique_ambiguous_and_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=Path(tmp)/'iio:device1';one.mkdir();(one/'name').write_text(live.IIO_NAME)
            two=Path(tmp)/'iio:device2';two.mkdir();(two/'name').write_text(live.IIO_NAME)
            with patch.object(live.Path,'glob',return_value=[]),patch.object(live,'snapshot_iio') as snapshot:
                self.assertIsNone(live.discover_native());snapshot.assert_not_called()
            with patch.object(live.Path,'glob',return_value=[one]), \
                    patch.object(live,'snapshot_iio',return_value=SNAP) as snapshot:
                self.assertEqual(live.discover_native(),SNAP)
                snapshot.assert_called_once_with(one,Path('/dev/iio:device1'))
            with patch.object(live.Path,'glob',return_value=[one,two]),patch.object(live,'snapshot_iio') as snapshot:
                with self.assertRaisesRegex(ValueError,'multiple'):live.discover_native()
                snapshot.assert_not_called()
            with patch.object(live.Path,'glob',return_value=[one]), \
                    patch.object(live,'snapshot_iio',return_value={**SNAP,'buffer_enable':'1'}):
                with self.assertRaisesRegex(ValueError,'already active'):live.discover_native()


if __name__=='__main__':unittest.main()
