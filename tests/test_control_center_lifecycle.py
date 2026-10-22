#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual main-loop shutdown in fresh processes; synthetic host/helper only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'tools/control_center'


def child(mode, source=APP):
    # Keep the real main()/QML lifetime; substitute only external inputs and
    # automate the ordinary window close. Never destroy the engine here.
    import gc
    import threading
    import time
    from unittest.mock import Mock, patch
    sys.path[:0] = [str(source), str(ROOT / 'tests'), str(APP)]
    import main
    from PySide6.QtCore import QTimer, QThreadPool
    from status import Snapshot, Fact
    from helper_setup import SetupInspector
    from test_control_center_first_run import setup_fixture, FakeTarget
    from test_control_center_app_packages import Adapter, FakeTransport
    import first_run
    events = []
    started = threading.Event()

    class Collector:
        def collect(self):
            events.append('status_started')
            started.set()
            if mode == 'slow_status':
                time.sleep(0.15)
            events.append('status_finished')
            return Snapshot('synthetic', 'synthetic', {
                'os': Fact('ok', 'Offline fixture'),
                'kernel': Fact('ok', 'fixture'),
                'architecture': Fact('ok', 'x86_64')})

    class Inspector(SetupInspector):
        def inspect(self, payload):
            events.append('inspection_started')
            started.set()
            if mode == 'slow_inspection':
                time.sleep(0.15)
            result = super().inspect(payload)
            events.append('inspection_finished')
            return result

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = FakeTarget()
        adapter = Adapter()
        tx = None
        packages = root / 'unused-calibration-bundle' if mode == 'calibration' else None
        if mode in ('helper_ready', 'helper_missing', 'slow_inspection', 'normal_calibration'):
            packages, _, _, payload, trust = setup_fixture(root)
            if mode != 'helper_missing':
                target.seed(payload)
            tx = first_run.FirstRunTransactions(
                packages, inspector=Inspector(target), setup_runner=target.runner,
                reader=lambda request: Mock(collect=adapter.observe), clock=lambda: 100,
                transport_factory=lambda pins: FakeTransport(pins, adapter, trust))
        create = main.create_engine

        def create_fixture(**kwargs):
            if mode not in ('demo', 'rehearsal', 'calibration'):
                kwargs['collector'] = Collector()
            engine = create(root / 'preferences.ini', **kwargs)
            engine.destroyed.connect(lambda: events.append('engine_destroyed'))
            engine.center_model.destroyed.connect(lambda: events.append('model_destroyed'))
            window = engine.rootObjects()[0]
            window.destroyed.connect(lambda: events.append('window_destroyed'))
            if mode == 'calibration':
                preview = engine.center_model.stickCalibration
                assert preview.open()
                preview.start()
                assert preview.session.phase == 'preparing'

            def close_when_ready():
                if mode == 'slow_status':
                    ready = started.is_set()
                elif mode == 'slow_inspection':
                    ready = 'inspection_started' in events
                elif tx is not None:
                    ready = tx.state == ('setup_required' if mode == 'helper_missing' else 'idle')
                else:
                    ready = mode in ('demo', 'rehearsal', 'calibration') or 'status_finished' in events
                if ready:
                    if mode == 'normal_calibration':
                        assert engine.center_model.hasTransactions
                        assert engine.center_model.canCalibrate
                        events.append('calibration_ready_without_authorization')
                    events.append('window_close')
                    window.close()
                else:
                    QTimer.singleShot(5, close_when_ready)
            QTimer.singleShot(5, close_when_ready)
            return engine

        argv = {'demo': ['--demo'], 'rehearsal': ['--rehearse-backend'],
                'calibration': ['--rehearse-calibration']}.get(mode, [])
        with patch.object(main, 'create_engine', create_fixture), \
                patch.object(main, 'calibration_factory', return_value=(
                    Mock(side_effect=AssertionError('Automatic calibration authorization'))
                    if mode == 'normal_calibration' else None)) as calibration, \
                patch.object(first_run, 'FirstRunTransactions', return_value=tx) as setup_constructor, \
                patch('subprocess.Popen', side_effect=AssertionError('Unexpected system command')):
            result = main.main(argv, packages_directory=packages)
            if mode == 'calibration': setup_constructor.assert_not_called()
            if mode in ('demo', 'rehearsal', 'calibration'): calibration.assert_not_called()
            if mode == 'normal_calibration':
                calibration.assert_called_once()
                calibration.return_value.assert_not_called()
        gc.collect()
        print(json.dumps({'result': result, 'events': events,
                          'active_workers': QThreadPool.globalInstance().activeThreadCount(),
                          'setup_commands': len(target.calls),
                          'package_submissions': len(tx.transport.sent) if tx and tx.transport else 0,
                          'state': tx.state if tx else None}))


class Lifecycle(unittest.TestCase):
    def run_case(self, mode):
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                   QT_QUICK_CONTROLS_STYLE='Basic', PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run([sys.executable, '-B', __file__, '--child', mode], env=env,
                             text=True, capture_output=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn('TypeError', run.stderr)
        self.assertNotIn('ReferenceError', run.stderr)
        self.assertNotIn('wrapped C/C++ object', run.stderr)
        report = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(report['result'], 0)
        self.assertEqual(report['active_workers'], 0)
        self.assertEqual(report['setup_commands'], 0)
        self.assertEqual(report['package_submissions'], 0)
        events = report['events']
        for event in ('window_close', 'window_destroyed', 'engine_destroyed', 'model_destroyed'):
            self.assertEqual(events.count(event), 1, events)
        self.assertLess(events.index('window_close'), events.index('window_destroyed'))
        self.assertLess(events.index('window_destroyed'), events.index('model_destroyed'))
        self.assertLess(events.index('engine_destroyed'), events.index('model_destroyed'))
        for prefix in ('status', 'inspection'):
            if prefix + '_started' in events:
                self.assertLess(events.index(prefix + '_finished'), events.index('window_destroyed'))
        return report

    def test_demo_close(self):
        self.run_case('demo')

    def test_read_only_status_close(self):
        self.run_case('status')

    def test_rehearsal_close(self):
        self.run_case('rehearsal')

    def test_calibration_preparation_close(self):
        report = self.run_case('calibration')
        self.assertNotIn('status_started',report['events'])

    def test_ready_helper_close_without_authentication(self):
        self.assertEqual(self.run_case('helper_ready')['state'], 'idle')

    def test_normal_launcher_offers_packages_and_calibration_without_authorization(self):
        report = self.run_case('normal_calibration')
        self.assertEqual(report['state'], 'idle')
        self.assertIn('calibration_ready_without_authorization', report['events'])

    def test_missing_helper_close_without_setup(self):
        self.assertEqual(self.run_case('helper_missing')['state'], 'setup_required')

    def test_close_during_status_waits_for_worker(self):
        events = self.run_case('slow_status')['events']
        self.assertLess(events.index('window_close'), events.index('status_finished'))

    def test_close_during_inspection_waits_for_worker(self):
        events = self.run_case('slow_inspection')['events']
        self.assertLess(events.index('window_close'), events.index('inspection_finished'))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        child(sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 else APP)
    else:
        unittest.main()
