#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual Qt worker -> package protocol -> executor, all system edges fake."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from main import create_engine
from package_client import ExecutionTransactions
from package_execution import PackageExecutor, ExecutionTrust
from package_wire import parse_message, receipt
from test_control_center_execution import Adapter, trust_records
import test_control_center_transactions_ui as ui
from rehearsal import fixture_catalog
import io


class PackageWindow(unittest.TestCase):
    item, click, wait_result = ui.BackendWindow.item, ui.BackendWindow.click, ui.BackendWindow.wait_result

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = None
        self.adapter = Adapter()
        self.catalog, self.blobs = fixture_catalog()
        self.trust = ExecutionTrust(self.catalog, trust_records(self.catalog))
        self.sent = []

    def open(self, code=0):
        owner = self
        class Transport:
            def invoke(self, message):
                owner.sent.append(message)
                if code:
                    return code, b''
                source = io.BytesIO(b''.join(message.chunks()))
                parsed = parse_message(source.read, owner.trust)
                owner.adapter.plan = parsed.plan
                outcome = PackageExecutor(owner.trust, owner.adapter, clock=lambda: 100).run(parsed.plan)
                return 0, receipt(parsed, outcome)
        class Collector:
            def collect(self): return None  # No actual host reader in tests.
        self.tx = ExecutionTransactions(self.adapter, self.catalog, self.blobs, lambda: 100,
                                        transport=Transport())
        self.engine = create_engine(Path(self.temp.name) / 'prefs.ini', demo=False,
                                    collector=Collector(), execution=self.tx)
        self.assertEqual(len(self.engine.rootObjects()), 1)
        self.window = self.engine.rootObjects()[0]
        self.window.resize(940, 1020)
        self.model = self.engine.center_model
        QTest.qWait(60)
        self.model.setLanguage('en')

    def tearDown(self):
        QThreadPool.globalInstance().waitForDone(5000)
        if self.engine:
            self.window.close()
            self.engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
        self.temp.cleanup()

    def test_gui_confirmation_protocol_and_independent_postcheck(self):
        self.open()
        self.assertFalse(self.model.isDemo)
        self.assertFalse(self.model.isRehearsal)
        self.assertTrue(self.model.hasTransactions)
        self.click('installButton'); self.click('backendProceed')
        self.assertFalse(self.sent)
        review = self.model.backend['review']
        self.assertIn('SHA256', review)
        self.assertIn('Target:', review)
        self.assertNotIn('example packages', review)
        self.click('backendProceed'); self.wait_result()
        self.assertEqual(self.tx.outcome.state, 'verified_success')
        self.assertIn('Package result verified', self.model.backend['message'])
        self.assertEqual(len(self.sent), 1)
        self.assertTrue(self.adapter.closed)
        self.assertFalse(self.model.view['canInstall'])
        self.assertFalse(self.model.view['canRemove'])
        self.model.confirmBackend()
        self.assertEqual(len(self.sent), 1)

    def test_gui_cancellation_before_prompt_sends_nothing(self):
        self.open()
        self.click('installButton'); self.click('backendProceed')
        self.click('backendCancel')
        self.assertFalse(self.sent)
        self.assertNotIn('lock', self.adapter.calls)
        self.assertEqual(self.tx.state, 'cancelled')

    def test_agent_cancel_stops_before_root_transaction_and_has_no_retry(self):
        self.open(126)
        self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
        self.wait_result()
        self.assertEqual(self.tx.outcome.state, 'cancelled')
        self.assertFalse(self.tx.outcome.changes_possible)
        self.assertNotIn('lock', self.adapter.calls)
        self.model.confirmBackend()
        self.assertEqual(len(self.sent), 1)

    def test_uncertain_receipt_never_becomes_success_or_keeps_buttons_enabled(self):
        self.open(2)
        self.model.setLanguage('de')
        self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
        self.wait_result()
        self.assertEqual(self.tx.outcome.state, 'uncertain')
        self.assertIn('Frisch prüfen', self.model.backend['message'])
        self.assertNotIn('Offline-Probelauf', self.model.backend['message'])
        self.assertFalse(self.model.view['canRemove'])

    def test_verified_install_success_and_done_closes_only_operation_dialog(self):
        self.open(); self.model.setLanguage('de')
        self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
        self.wait_result()
        self.assertTrue(self.model.backend['verifiedSuccess'])
        self.assertEqual(self.model.backend['successTitle'], 'Erfolgreich installiert')
        self.assertEqual(self.item('backendSuccessTitle').property('text'), 'Erfolgreich installiert')
        self.assertEqual(self.item('backendCancel').property('text'), 'Fertig')
        self.assertTrue(self.item('backendDialog').property('visible'))
        self.click('backendCancel')
        self.assertFalse(self.item('backendDialog').property('visible'))
        self.assertTrue(self.window.isVisible())
        self.assertEqual(len(self.sent), 1)

    def test_failure_cannot_show_success_or_done_label(self):
        self.open(2)
        self.click('installButton'); self.click('backendProceed'); self.click('backendProceed')
        self.wait_result()
        self.assertFalse(self.model.backend['verifiedSuccess'])
        self.assertEqual(self.model.backend['successTitle'], '')
        self.assertFalse(self.item('backendSuccessTitle').property('visible'))
        self.assertEqual(self.item('backendCancel').property('text'), 'Close')
        self.assertTrue(self.item('backendDialog').property('visible'))
        self.assertTrue(self.window.isVisible())

    def test_mode_separation_and_no_execution_default(self):
        self.open()
        with self.assertRaises(ValueError):
            create_engine(Path(self.temp.name) / 'other.ini', demo=True, execution=self.tx)


if __name__ == '__main__':
    unittest.main()
