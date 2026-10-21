#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real QML -> Qt worker -> backend session, with exclusively synthetic data."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QCoreApplication, QEvent, QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from main import create_engine
from rehearsal import create_rehearsal


class BackendWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tx = create_rehearsal()
        self.engine = None

    def open(self, scenario='success', *, authorization=None, **kwargs):
        self.tx = create_rehearsal(scenario, authorization=authorization)
        self.engine = create_engine(Path(self.temp.name) / 'prefs.ini', rehearsal=self.tx, **kwargs)
        self.assertEqual(len(self.engine.rootObjects()), 1)
        self.window = self.engine.rootObjects()[0]
        self.window.resize(940, 1020)
        self.model = self.engine.center_model
        QTest.qWait(50)

    def tearDown(self):
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()
        if self.engine:
            self.window.close()
            self.engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
        self.temp.cleanup()

    def item(self, name):
        item = self.window.findChild(QObject, name)
        if item is None:
            # Repeater delegates have a visual parent without QObject ancestry
            # below the window. Exercise the visible controls, not a test proxy.
            queue = [self.window.contentItem()]
            while queue:
                candidate = queue.pop()
                if candidate.objectName() == name:
                    item = candidate
                    break
                queue.extend(candidate.childItems())
        self.assertIsNotNone(item, name)
        return item

    def click(self, name):
        item = self.item(name)
        self.assertTrue(item.property('enabled'), name)
        if name in ('installButton', 'removeButton'):
            scroll = self.item('mainScroll').property('contentItem')
            pt = item.mapToItem(scroll, QPointF(0, 0))
            scroll.setProperty('contentY', max(0, pt.y() - self.window.height() / 2))
            QTest.qWait(20)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                         QPoint(round(point.x()), round(point.y())))
        QTest.qWait(40)

    def wait_result(self):
        for _ in range(100):
            if self.tx.state == 'done':
                return
            QTest.qWait(20)
        self.fail('Backend did not complete')

    def test_default_read_only_handlers_cannot_reach_backend(self):
        with patch('qt_bridge.Collector') as collector:
            self.engine = create_engine(Path(self.temp.name) / 'prefs.ini', demo=False,
                                        collector=collector)
            self.window = self.engine.rootObjects()[0]
            model = self.engine.center_model
            self.assertFalse(model.isRehearsal)
            self.assertEqual(model.backend['state'], 'disabled')
            model.request('install'); model.prepareBackend(); model.confirmBackend(); model.cancelBackend()
            self.assertFalse(model.view['canInstall'])
            self.assertFalse(model.view['canRemove'])
            self.assertIsNone(model.backend_job)

    def test_rehearsal_refuses_real_status_combination(self):
        from PySide6.QtCore import QSettings
        from qt_bridge import CenterModel
        settings = QSettings(str(Path(self.temp.name) / 'prefs.ini'), QSettings.Format.IniFormat)
        with self.assertRaises(ValueError):
            CenterModel(settings, demo=False, rehearsal=self.tx)
        with self.assertRaises(ValueError):
            CenterModel(settings, demo=True, collector=object(), rehearsal=self.tx)

    def test_install_review_confirm_and_remove_via_real_buttons(self):
        with patch('qt_bridge.Collector.collect', side_effect=AssertionError('No host snapshot')):
            self.open()
            self.model.setLanguage('de')
            self.assertIn('OFFLINE', self.window.title())
            self.assertFalse(self.item('scenarioBox').property('visible'))
            self.click('installButton')
            self.assertTrue(self.item('backendDialog').property('visible'))
            self.assertEqual(self.tx.state, 'editing')
            self.click('backendProceed')
            self.assertEqual(self.tx.state, 'review')
            self.assertIn('gamesir-native-dkms', self.item('backendReview').property('text'))
            self.assertIn('Keine Treiberaktivierung', self.model.backend['review'])
            self.assertFalse(self.tx.port.calls)
            self.click('backendProceed'); self.wait_result()
            self.assertTrue(self.model.view['installed'])
            self.assertFalse(self.model.view['loaded'])
            self.assertIn('Offline-Probelauf bestanden', self.model.backend['message'])
            self.click('backendCancel')
            self.click('removeButton'); self.click('backendProceed')
            self.assertIn('Deinstallationsablauf', self.item('backendDialog').property('title'))
            self.assertIn('0.1.0.offline-1', self.model.backend['review'])
            self.click('backendProceed'); self.wait_result()
            self.assertFalse(self.model.view['installed'])
            self.assertIn('0.1.0.offline-1', self.model.backend['review'])

    def test_checkbox_selection_reaches_backend_and_dependencies_block(self):
        self.open(); self.click('installButton')
        self.click('component_core'); self.click('component_bridge')
        self.assertEqual(self.tx.selected, ('bridge',))
        self.click('backendProceed')
        self.assertEqual(self.tx.state, 'editing')
        self.assertIn('dependent_component_requires_explicit_selection', self.model.backend['message'])
        self.assertFalse(self.tx.port.calls)
        self.click('component_core'); self.click('backendProceed')
        self.assertEqual(self.tx.state, 'review')

    def test_escape_cancels_review_without_any_package_calls(self):
        self.open(); self.click('installButton'); self.click('backendProceed')
        QTest.keyClick(self.window, Qt.Key.Key_Escape); QTest.qWait(30)
        self.assertEqual(self.tx.state, 'cancelled')
        self.assertFalse(self.tx.port.calls)
        self.assertFalse(self.model.view['installed'])
        self.model.confirmBackend()
        self.assertFalse(self.tx.port.calls)

    def test_worker_failures_are_visible_and_never_report_success(self):
        self.open('transaction_failed')
        self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
        self.wait_result()
        self.assertIn('offline_transaction_failed', self.model.backend['message'])
        self.assertTrue(self.tx.outcome.changes_possible)
        self.assertFalse(self.model.view['installed'])
        self.assertEqual(self.model.view['driver'], self.model.strings['unknown'])
        self.assertFalse(self.model.view['canInstall'])
        self.assertFalse(self.model.view['canRemove'])
        calls = list(self.tx.port.calls)
        self.model.confirmBackend()
        self.assertEqual(self.tx.port.calls, calls)

    def test_gui_worker_uses_authorization_protocol_without_any_real_password_prompt(self):
        from privilege.client import AuthorizationAttempt
        from privilege.helper import answer
        from privilege.transport import Reply
        calls = []
        class Agent:
            def invoke(agent, data, *, cancelled):
                calls.append(data)
                return Reply('complete', 126)
        self.open(authorization=lambda plan: AuthorizationAttempt(plan, Agent(), nonce='c'*64).run())
        with patch('subprocess.Popen', side_effect=AssertionError('No real pkexec or package action')):
            self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
            self.wait_result()
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.tx.outcome.state, 'cancelled')
        self.assertNotIn('commit', self.tx.port.calls)
        self.assertFalse(self.model.view['installed'])
        self.assertIn(self.model.strings['backend_cancelled'], self.model.backend['message'])

    def test_running_worker_does_not_block_ui_and_cannot_be_cancelled_or_duplicated(self):
        self.open()
        entered, release = threading.Event(), threading.Event()
        original = self.tx.port.commit
        def slow(plan):
            entered.set()
            release.wait(3)
            original(plan)
        with patch.object(self.tx.port, 'commit', side_effect=slow):
            self.click('installButton'); self.click('backendProceed'); self.model.confirmBackend()
            self.assertTrue(entered.wait(1))
            try:
                self.model.setLanguage('en'); self.app.processEvents()
                self.assertEqual(self.model.language, 'en')
                self.assertFalse(self.item('backendCancel').property('enabled'))
                self.model.confirmBackend(); self.model.cancelBackend()
                self.assertEqual(self.tx.state, 'running')
                QTest.keyClick(self.window, Qt.Key.Key_Escape)
                self.assertTrue(self.item('backendDialog').property('visible'))
            finally:
                release.set()
            self.wait_result()
        self.assertEqual(self.tx.port.calls.count('commit'), 1)

    def test_dialog_scrolls_at_small_size_and_translates_review(self):
        self.open(); self.window.resize(560, 480)
        self.model.setLanguage('en'); self.click('installButton')
        for component in ('steam', 'gamescope', 'bridge'):
            self.model.selectBackendComponent(component, True)
        self.model.prepareBackend(); QTest.qWait(30)
        dialog = self.item('backendDialog')
        self.assertLessEqual(dialog.property('height'), 440)
        self.assertGreater(self.item('backendScroll').property('contentHeight'),
                           self.item('backendScroll').property('height'))
        self.assertIn('Exact example packages', self.model.backend['review'])
        self.model.setLanguage('de')
        self.assertIn('Genaue Beispielpakete', self.model.backend['review'])
        self.assertFalse(self.tx.port.calls)


if __name__ == '__main__':
    unittest.main()
