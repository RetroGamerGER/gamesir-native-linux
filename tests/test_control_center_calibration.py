#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline calibration lifecycle, identity and failure regressions. No hardware."""
from contextlib import ExitStack
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from stick_calibration import (Calibration, Instance, RunKey, Sample, MemoryPort,
                               SECTORS, MAX_SAMPLE_AGE)


class Clock:
    def __init__(self): self.now = 10.0
    def __call__(self): return self.now
    def advance(self, seconds=0.1): self.now += seconds


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.port = MemoryPort()
        self.session = Calibration(self.port, clock=self.clock)
        self.instance = Instance('gamepad-A', 'connection-1')
        self.key = self.session.open(self.instance)
        self.seq = 0

    def sample(self, *, left=(0.0, 0.0), right=(0.0, 0.0), active=0, done=0, key=None):
        self.clock.advance()
        self.seq += 1
        s = Sample(self.seq, self.clock(), left, right, active, done)
        return self.session.feed(key or self.key, s)

    def start(self):
        self.sample()
        self.assertTrue(self.session.prepare())
        for _ in range(31):
            self.sample()
            self.session.tick(self.key)
        self.assertEqual(self.session.phase, 'measuring')
        self.assertEqual(self.operations(), ['Start'])

    def operations(self): return [x.operation for x in self.port.intents]

    def test_open_never_starts_or_substitutes_an_active_device(self):
        self.assertIsNone(self.session.open(Instance('gamepad-B', 'connection-2')))
        self.assertEqual(self.session.key, self.key)
        self.assertEqual(self.operations(), [])
        self.assertFalse(self.session.snapshot()['canStart'])

    def test_preparation_needs_reports_and_an_explicit_start(self):
        self.sample()
        for _ in range(40):
            self.sample(); self.session.tick(self.key)
        self.assertEqual(self.operations(), [])
        self.assertEqual(self.session.phase, 'ready')
        self.assertTrue(self.session.prepare())
        self.session.tick(self.key)
        self.assertEqual(self.operations(), [])

    def test_delayed_start_is_consumed_once(self):
        self.start()
        for _ in range(5): self.session.tick(self.key)
        self.assertEqual(self.operations(), ['Start'])
        self.assertFalse(self.session.prepare())

    def test_cancel_during_preparation_prevents_delayed_start(self):
        self.sample();self.session.prepare()
        self.assertTrue(self.session.cancel())
        self.clock.advance(5);self.session.tick(self.key)
        self.assertEqual(self.operations(), [])
        self.assertEqual(self.session.phase, 'cancelled')

    def test_loss_during_preparation_sends_neither_start_nor_exit(self):
        self.sample();self.session.prepare()
        self.session.disconnect(self.key)
        self.clock.advance(5);self.session.tick(self.key)
        self.assertFalse(self.session.finish())
        self.assertFalse(self.session.cancel())
        self.assertEqual(self.operations(), [])

    def test_cancel_while_measuring_requests_exit_once_for_original_instance(self):
        self.start();self.sample(active=3)
        self.assertTrue(self.session.cancel())
        self.assertFalse(self.session.cancel())
        self.assertFalse(self.session.finish())
        self.assertEqual(self.operations(), ['Start', 'Exit'])
        self.assertEqual({i.key for i in self.port.intents}, {self.key})

    def test_foreign_device_connection_or_generation_cannot_finish_or_disconnect(self):
        self.start()
        for bad in [RunKey(Instance('gamepad-B', 'connection-1'), self.key.generation),
                    RunKey(Instance('gamepad-A', 'connection-2'), self.key.generation),
                    RunKey(self.instance, self.key.generation+1)]:
            self.assertFalse(self.sample(active=3, done=3, key=bad))
            self.assertFalse(self.session.disconnect(bad))
            self.session.tick(bad)
        self.assertEqual(self.session.phase, 'measuring')
        self.assertEqual(self.operations(), ['Start'])

    def test_one_stick_is_not_both_and_duplicate_status_never_finishes(self):
        self.start();self.sample(active=3, done=1)
        self.assertFalse(self.session.snapshot()['canFinish'])
        self.assertTrue(self.session.snapshot()['sticks'][0]['ready'])
        self.assertFalse(self.session.finish())
        for _ in range(10):self.sample(active=3, done=1)
        self.assertEqual(self.operations(), ['Start'])

    def test_coverage_and_firmware_readiness_are_independent(self):
        self.start()
        for n in range(SECTORS):
            angle=(n+0.5)*math.tau/SECTORS
            point=(math.cos(angle), math.sin(angle))
            self.sample(active=3, left=point, right=point)
        v=self.session.snapshot()
        self.assertEqual([s['coverage'] for s in v['sticks']], [100,100])
        self.assertFalse(v['canFinish'])
        self.assertFalse(self.session.finish())

    def test_center_samples_show_position_without_edge_coverage(self):
        self.start();self.sample(active=3, left=(0.2, -0.3), right=(-0.1, 0.1))
        v=self.session.snapshot()
        self.assertEqual((v['sticks'][0]['x'],v['sticks'][0]['y']), (0.2,-0.3))
        self.assertEqual([s['coverage'] for s in v['sticks']], [0,0])

    def test_done_before_start_is_not_retained(self):
        self.sample(active=3,done=3)
        self.assertEqual(self.session.done,0)
        self.assertFalse(self.session.finish())

    def test_both_report_ready_without_geometry_guess_and_finish_is_explicit_once(self):
        self.start();self.sample(active=3,done=3)
        self.assertEqual(self.session.phase,'ready_to_finish')
        self.assertEqual(self.operations(),['Start'])
        self.assertTrue(self.session.finish())
        self.assertEqual(self.session.phase,'completed')
        self.assertFalse(self.session.finish());self.session.cancel()
        self.assertEqual(self.operations(),['Start','Finish'])

    def test_readiness_regression_withdraws_finish(self):
        self.start();self.sample(active=3,done=3)
        self.sample(active=3,done=1)
        self.assertFalse(self.session.finish())
        self.assertEqual(self.session.phase,'measuring')

    def test_exit_after_ready_has_no_pending_finish_timer(self):
        self.start();self.sample(active=3,done=3)
        self.session.cancel();self.clock.advance(10);self.session.tick(self.key)
        self.assertFalse(self.sample(active=3,done=3))
        self.assertFalse(self.session.finish())
        self.assertEqual(self.operations(),['Start','Exit'])

    def test_loss_after_ready_is_terminal_without_finish_or_exit(self):
        self.start();self.sample(active=3,done=3)
        self.assertTrue(self.session.disconnect(self.key))
        self.assertFalse(self.session.finish());self.session.cancel()
        self.assertFalse(self.sample(active=3,done=3))
        self.assertEqual(self.session.phase,'lost')
        self.assertEqual(self.operations(),['Start'])

    def test_late_report_after_gap_cannot_hide_loss(self):
        self.start();self.clock.advance(MAX_SAMPLE_AGE+1)
        self.assertFalse(self.sample(active=3,done=3))
        self.assertEqual(self.session.phase,'lost')
        self.assertEqual(self.operations(),['Start'])

    def test_missing_heartbeat_blocks_start_finish_and_exit(self):
        for action in ('prepare','finish','cancel','tick'):
            with self.subTest(action=action):
                self.setUp()
                if action=='prepare':self.sample()
                else:self.start();self.sample(active=3,done=3)
                self.clock.advance(MAX_SAMPLE_AGE+1)
                if action=='tick':self.session.tick(self.key)
                else:getattr(self.session,action)()
                self.assertEqual(self.session.phase,'lost')
                self.assertNotIn('Finish',self.operations())
                self.assertNotIn('Exit',self.operations())

    def test_reconnect_requires_new_run_and_ignores_old_callbacks(self):
        self.start();old=self.key;self.session.disconnect(old)
        self.key=self.session.open(Instance('gamepad-A','connection-2'))
        self.assertNotEqual(self.key,old)
        self.assertEqual(self.session.phase,'ready')
        self.clock.advance(4);self.session.tick(old)
        self.assertFalse(self.sample(active=3,done=3,key=old))
        self.assertFalse(self.session.finish())
        self.assertEqual(self.operations(),['Start'])
        self.assertEqual(self.session.snapshot()['sticks'][0]['coverage'],0)

    def test_same_instance_new_generation_still_rejects_old_callbacks(self):
        old=self.key;self.sample();self.session.prepare();self.session.cancel()
        self.key=self.session.open(self.instance)
        self.assertGreater(self.key.generation,old.generation)
        self.sample();self.session.prepare()
        self.clock.advance(0.1);self.session.tick(old)
        self.assertFalse(self.sample(active=3,done=3,key=old))
        self.assertEqual(self.operations(),[])

    def test_out_of_order_and_duplicate_samples_do_not_refresh_liveness(self):
        self.start();self.sample(active=3)
        before=self.session.last_sample_at
        for seq,stamp in [(self.seq,self.clock()+0.1),(self.seq+1,before)]:
            self.clock.advance(0.1)
            self.assertFalse(self.session.feed(self.key,Sample(seq,stamp,(1.,0.),(0.,0.),3,3)))
        self.assertEqual(self.session.last_sample_at,before)
        self.clock.advance(MAX_SAMPLE_AGE+1);self.session.tick(self.key)
        self.assertEqual(self.session.phase,'lost')

    def test_invalid_current_samples_stop_without_sending(self):
        good=Sample(1,10.1,(0.,0.),(0.,0.),3,0)
        invalid=[replace(good,sequence=True),replace(good,sequence=-1),
                 replace(good,timestamp=float('nan')),replace(good,timestamp=99),
                 replace(good,left=(float('inf'),0.)),replace(good,right=(1.1,0.)),
                 replace(good,left=(True,0.)),replace(good,left=(0.,)),
                 replace(good,active=True),replace(good,done=4)]
        for value in invalid:
            with self.subTest(value=value):
                self.setUp();self.clock.advance(0.1)
                self.assertFalse(self.session.feed(self.key,value))
                self.assertEqual(self.session.phase,'error')
                self.assertEqual(self.operations(),[])

    def test_initial_inactive_report_waits_but_leaving_observed_mode_stops(self):
        self.start();self.sample(active=0)
        self.assertEqual(self.session.phase,'measuring')
        self.sample(active=3);self.sample(active=0)
        self.assertEqual(self.session.phase,'error')
        self.assertEqual(self.session.reason,'inactive')
        self.assertEqual(self.operations(),['Start'])

    def test_each_transfer_failure_is_terminal_without_retry(self):
        for operation in ('Start','Finish','Exit'):
            with self.subTest(operation=operation):
                self.setUp();self.port.fail_on.add(operation)
                if operation=='Start':
                    self.sample();self.session.prepare()
                    for _ in range(31):self.sample();self.session.tick(self.key)
                else:
                    self.start();self.sample(active=3,done=3)
                    if operation=='Finish':self.session.finish()
                    else:self.session.cancel()
                self.assertEqual(self.session.phase,'error')
                before=list(self.port.intents)
                for _ in range(3):
                    self.session.tick(self.key);self.session.finish();self.session.cancel()
                self.assertEqual(self.port.intents,before)
                self.assertEqual(self.operations().count(operation),1)

    def test_entire_flow_needs_no_files_processes_network_or_devices(self):
        with ExitStack() as stack:
            for name in ('subprocess.run','subprocess.Popen','socket.socket',
                         'os.open','builtins.open','pathlib.Path.open'):
                stack.enter_context(patch(name,side_effect=AssertionError('Unexpected I/O')))
            self.start();self.sample(active=3,done=3);self.session.finish()
            self.session.cancel();self.session.tick(self.key)
        self.assertEqual(self.operations(),['Start','Finish'])

    def test_instance_identity_is_required(self):
        for args in [('', 'a'),('a',''),('a',None),('a',' '*3)]:
            with self.assertRaises(ValueError):Instance(*args)


if __name__=='__main__':unittest.main()
