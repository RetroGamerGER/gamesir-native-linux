#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Normal package + TMR UI with fake helpers/manager only; no system access."""
import os
os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                  QT_QUICK_CONTROLS_STYLE='Basic')
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QObject
from PySide6.QtTest import QTest
import test_control_center_app_packages_ui as packages
import test_tmr_gui_ui as live
import test_control_center_calibration_ui as preview
import test_tmr_maintenance as native
from tmr_helper import Session
from tmr_wire import FILES, encode
from main import calibration_factory


class NormalCalibration(unittest.TestCase):
    setUpClass = packages.BundleWindow.__dict__['setUpClass']
    item, click = preview.CalibrationWindow.item, preview.CalibrationWindow.click
    wait_state = packages.BundleWindow.wait_state
    wait, settle = live.LiveWindow.wait, live.LiveWindow.settle
    open, select, advance, start = (live.LiveWindow.open, live.LiveWindow.select,
                                  live.LiveWindow.advance, live.LiveWindow.start)

    def setUp(self):
        packages.BundleWindow.setUp(self)
        self.f = native.ManagerTmr(); self.f.setUp()
        self.f.host.now = time.monotonic()
        self.f.backend.status.update(host_monotonic_ns=int(self.f.host.now * 1e9))
        self.session = Session(self.f.manager.command, clock=lambda: self.f.host.now)
        self.clients = []
        def factory(cancelled):
            client = live.FakeClient(self.session, cancelled)
            self.clients.append(client)
            return client
        packages.BundleWindow.open(self, calibration_factory=factory)
        self.bridge = self.model.stickCalibration
        self.bridge.changed.connect(self.bridge.timer.stop)

    def tearDown(self):
        self.bridge.shutdown()
        packages.BundleWindow.tearDown(self)

    def test_normal_window_has_packages_and_calibration_without_automatic_authorization(self):
        self.assertTrue(self.model.hasTransactions)
        self.assertTrue(self.model.canCalibrate)
        self.assertTrue(self.item('calibrationOpen').property('enabled'))
        self.assertEqual(self.clients, [])
        self.assertFalse(self.tx.transport.sent)
        self.assertFalse(self.item('calibrationDialog').property('visible'))
        self.assertFalse(self.item('plannedToggle').property('expanded'))

    def test_package_review_blocks_even_direct_calibration_open_and_cancel_restores_it(self):
        self.model.request('install')
        self.assertEqual(self.tx.state, 'editing')
        self.assertFalse(self.model.canCalibrate)
        self.assertFalse(self.bridge.open())
        self.model.prepareBackend(); self.wait_state(('review',))
        self.assertFalse(self.bridge.open())
        self.assertEqual(self.clients, [])
        self.model.cancelBackend()
        self.assertTrue(self.model.canCalibrate)
        self.assertTrue(self.bridge.open()); self.settle()

    def test_calibration_blocks_all_package_and_setup_entry_points(self):
        self.select()
        self.tx.setup_review = self.tx.setup_result = None
        with patch.object(self.tx, 'request', wraps=self.tx.request) as request, \
             patch.object(self.tx, 'begin_preparation', wraps=self.tx.begin_preparation) as prepare, \
             patch.object(self.tx, 'begin', wraps=self.tx.begin) as begin, \
             patch.object(self.tx, 'begin_update_check', wraps=self.tx.begin_update_check) as update:
            self.tx.request_setup = Mock()
            self.tx.begin_setup = Mock()
            for _ in range(2):
                self.model.request('install'); self.model.request('remove')
                self.model.prepareBackend(); self.model.confirmBackend(); self.model.checkUpdates()
                self.model.requestSetup(); self.model.confirmSetup()
            for action in (request, prepare, begin, update, self.tx.request_setup, self.tx.begin_setup):
                action.assert_not_called()
        self.assertFalse(self.model.view['canInstall'])
        self.assertFalse(self.model.view['canRemove'])
        self.assertFalse(self.tx.transport.sent)

    def test_close_waits_for_helper_return_before_unlocking_packages(self):
        self.select()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        client = self.clients[0]; original = client.close
        def delayed():
            entered.set(); release.wait(2); original()
        client.close = delayed
        self.click('calibrationCancel')
        self.wait(entered.is_set)
        self.assertTrue(self.bridge.inUse)
        self.model.request('install')
        self.assertEqual(self.tx.state, 'idle')
        self.assertFalse(self.model.view['canInstall'])
        release.set(); self.wait(lambda: not self.bridge.inUse)
        self.assertTrue(self.model.view['canInstall'])

    def test_worker_exit_stays_locked_until_queued_return_is_processed(self):
        self.select()
        self.bridge.close()
        # Waiting without pumping GUI events reproduces the interval between
        # thread exit and delivery of its queued result/finished notifications.
        self.assertTrue(self.bridge.worker.wait(2000))
        self.assertFalse(self.bridge.worker.isRunning())
        self.assertTrue(self.bridge.inUse)
        self.model.request('install')
        self.assertEqual(self.tx.state, 'idle')
        self.wait(lambda: not self.bridge.inUse)
        self.assertTrue(self.model.view['canInstall'])

    def test_old_completion_cannot_unlock_a_new_session(self):
        self.select()
        self.bridge.worker_finished(self.bridge.generation - 1)
        self.assertTrue(self.bridge.inUse)

    def test_late_cleanup_problem_after_close_keeps_packages_locked(self):
        self.select()
        self.bridge.close()
        self.bridge.receive(self.bridge.generation, {'view': {'cleanupProblem': 'unconfirmed'}})
        self.wait(lambda: not self.bridge.worker.isRunning())
        self.assertTrue(self.bridge.inUse)
        self.model.request('install')
        self.assertEqual(self.tx.state, 'idle')
        self.assertFalse(self.tx.transport.sent)

    def test_normal_flow_keeps_one_shot_finish_and_done_closes_only_dialog(self):
        self.start(); self.advance(3, 3)
        self.assertIn('3 / 3', self.item('calibrationStep').property('text'))
        self.click('calibrationFinish'); self.settle()
        self.wait(lambda: not self.bridge.inUse)
        self.assertEqual(self.bridge.view['phase'], 'completed')
        self.assertFalse(self.item('calibrationPlots').property('visible'))
        self.assertEqual(self.item('calibrationCancel').property('text'), 'Done')
        self.assertEqual(self.f.backend.calls.count('Start'), 1)
        self.assertEqual(self.f.backend.calls.count('Finish'), 1)
        self.assertNotIn('Exit', self.f.backend.calls)
        self.assertFalse(self.tx.transport.sent)
        self.click('calibrationCancel')
        self.assertFalse(self.item('calibrationDialog').property('visible'))
        self.assertTrue(self.window.isVisible())

    def test_uncertain_calibration_keeps_package_changes_locked_after_dialog_close(self):
        self.bridge.factory = Mock(side_effect=RuntimeError('denied'))
        self.open()
        self.wait(lambda: not self.bridge.worker.isRunning())
        self.click('calibrationCancel')
        self.assertTrue(self.bridge.blocked)
        self.assertFalse(self.model.view['canInstall'])
        self.assertFalse(self.model.canCalibrate)
        self.model.request('remove')
        self.assertEqual(self.tx.state, 'idle')
        self.assertFalse(self.tx.transport.sent)

    def test_pending_inspection_setup_and_uncertain_package_state_block_calibration(self):
        for state in ('loading', 'editing', 'checking', 'review', 'running', 'checking_updates',
                      'setup_review', 'setup_running', 'setup_failed'):
            with self.subTest(state=state):
                self.tx.state = state
                self.assertFalse(self.model.canCalibrate)
                self.assertFalse(self.bridge.open())
        self.tx.state = 'idle'
        from backend import Outcome
        self.tx.outcome = Outcome('uncertain', 'test', changes_possible=True)
        self.assertFalse(self.bridge.open())
        self.tx.outcome = None
        self.model.inspection_job = object()
        self.assertFalse(self.bridge.open())
        self.model.inspection_job = None
        self.assertEqual(self.clients, [])

    def test_selection_and_steps_fit_small_window_in_both_languages(self):
        self.open()
        self.assertFalse(self.item('calibrationPlots').property('visible'))
        self.assertIn('1 / 3', self.item('calibrationStep').property('text'))
        self.click('calibrationSelect', scrolling='calibrationScroll'); self.settle()
        for language in ('de', 'en'):
            self.model.setLanguage(language)
            self.window.resize(560, 480); QTest.qWait(50)
            dialog = self.item('calibrationDialog')
            self.assertLessEqual(dialog.property('height'), 448)
            self.assertIn('2 / 3', self.item('calibrationStep').property('text'))
            self.assertTrue(self.item('calibrationStart').property('enabled'))
            self.assertFalse(self.window.grabWindow().isNull())

    def test_normal_factory_loads_only_reviewed_pins_and_never_launches_helper(self):
        pins = {name: 'a' * 64 for name in FILES}
        (self.root / 'tmr-helper.json').write_bytes(encode({'schema': 1, 'files': pins}))
        with patch('tmr_client.subprocess.Popen') as spawn, \
             patch('tmr_client.InstalledAuditor.inspect') as inspect:
            factory = calibration_factory(self.root)
            client = factory(lambda: False)
            self.assertEqual(client.pins, pins)
            self.assertIsNone(client.child)
            spawn.assert_not_called(); inspect.assert_not_called()

    def test_missing_or_changed_manifest_cannot_enable_live_calibration(self):
        self.assertIsNone(calibration_factory(self.root))
        with self.assertRaises(ValueError): calibration_factory(self.root, required=True)
        (self.root / 'tmr-helper.json').write_bytes(encode({'schema': 1, 'files': {}}))
        self.assertIsNone(calibration_factory(self.root))


if __name__ == '__main__':
    unittest.main()
