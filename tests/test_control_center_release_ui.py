#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual QML, synthetic release packages, fake HTTPS/host/helper only."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QThreadPool, QTimer
from PySide6.QtGui import QGuiApplication
from app_packages import AppImageTransactions
from main import create_engine
from release_download import ReleaseAsset, ReleaseDownloader, serialize_assets
from test_control_center_release_download import Client, Reply
from test_control_center_app_packages import fixture, FakeTransport, Adapter
import test_control_center_transactions_ui as ui


class ReleaseWindow(unittest.TestCase):
    item, click = ui.BackendWindow.item, ui.BackendWindow.click

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build'); self.root = Path(self.temp.name)
        _, self.trust = fixture(self.root)
        blobs = {r.component: (self.root / (r.component + '.pkg.tar.zst')).read_bytes()
                 for r in self.trust.catalog.records}
        self.assets = tuple(ReleaseAsset(r.component, 'offline-' + r.component + '.pkg.tar.zst', r)
                            for r in self.trust.catalog.records)
        for p in self.root.glob('*.pkg.tar.zst'): p.unlink()
        (self.root / 'release-assets.json').write_bytes(serialize_assets(self.assets))
        self.adapter, self.client, self.threads = Adapter(), Client([Reply(blobs['core'])]), []
        self.tx = AppImageTransactions(self.root, clock=lambda: 100,
            downloader=ReleaseDownloader(self.client, clock=lambda: 100),
            reader=lambda r: Mock(collect=self.collect),
            transport_factory=lambda pins: FakeTransport(pins, self.adapter, self.trust))
        self.engine = create_engine(self.root / 'prefs.ini', demo=False,
                                   collector=Mock(collect=lambda: None), execution=self.tx)
        self.window = self.engine.rootObjects()[0]; self.window.resize(940, 1020)
        self.model = self.engine.center_model; self.model.setLanguage('en')
        self.wait_state('idle')

    def collect(self):
        self.threads.append(threading.get_ident())
        return self.adapter.observe()

    def wait_state(self, state):
        loop = QEventLoop(); timer = QTimer(); timer.setInterval(10)
        timer.timeout.connect(lambda: loop.quit() if self.tx.state == state else None)
        timer.start(); QTimer.singleShot(5000, loop.quit); loop.exec(); timer.stop()
        self.assertEqual(self.tx.state, state)

    def tearDown(self):
        if self.tx.state == 'checking': self.tx.cancel()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents(); self.window.close(); self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete); self.app.processEvents()
        self.temp.cleanup()

    def test_explicit_download_label_then_exact_plan_without_authentication(self):
        self.assertFalse(self.client.calls)
        self.click('installButton')
        self.assertEqual(self.item('backendProceed').property('text'), 'Download and check packages')
        self.assertIn('GitHub', self.model.strings['backend_intro'])
        for _ in range(10): self.model.view; self.model.backend; self.model.strings
        self.assertFalse(self.client.calls)
        self.click('backendProceed'); self.wait_state('review')
        self.assertEqual(len(self.client.calls), 1)
        self.assertIn(self.assets[0].url, self.model.backend['review'])
        self.assertEqual(self.item('backendProceed').property('text'), 'Confirm and authenticate')
        self.assertFalse(self.tx.transport.sent); self.assertNotIn('lock', self.adapter.calls)
        self.assertTrue(all(t != threading.get_ident() for t in self.threads))

    def test_download_failure_shows_reason_and_cannot_confirm(self):
        self.client.replies = [OSError('offline')]
        self.click('installButton'); self.click('backendProceed'); self.wait_state('editing')
        self.assertIn('release_download_unavailable', self.model.backend['message'])
        self.assertIsNone(self.tx.begin()); self.assertFalse(self.tx.transport.sent)

    def test_download_text_is_localized_and_removal_keeps_non_download_text(self):
        self.click('installButton'); self.model.setLanguage('de')
        self.assertEqual(self.item('backendProceed').property('text'), 'Pakete laden und prüfen')
        self.assertIn('Noch keine Installation', self.model.strings['backend_intro'])
        self.model.cancelBackend(); self.assertFalse(self.client.calls)
        # Removing does not change into a download operation.
        self.tx.operation = 'remove'; self.model.changed.emit()
        self.assertEqual(self.model.strings['backend_prepare'], 'Auswahl prüfen')

    def test_cancel_while_downloading_discards_late_worker_result(self):
        entered, release = threading.Event(), threading.Event()
        def wait():
            entered.set()
            if not release.wait(3): raise OSError('Offline fixture wait expired')
        self.client.replies[0].on_read = wait
        self.click('installButton'); self.click('backendProceed')
        loop = QEventLoop(); timer = QTimer(); timer.setInterval(10)
        timer.timeout.connect(lambda: loop.quit() if entered.is_set() else None)
        timer.start(); QTimer.singleShot(2000, loop.quit); loop.exec(); timer.stop()
        try:
            self.assertTrue(entered.is_set()); self.click('backendCancel')
            self.assertEqual(self.tx.state, 'cancelled')
        finally:
            release.set()
        loop = QEventLoop(); timer = QTimer(); timer.setInterval(10)
        timer.timeout.connect(lambda: loop.quit() if self.model.inspection_job is None else None)
        timer.start(); QTimer.singleShot(3000, loop.quit); loop.exec(); timer.stop()
        self.assertEqual(self.tx.state, 'cancelled'); self.assertIsNone(self.tx.session)
        self.assertFalse(self.tx.transport.sent)


if __name__ == '__main__':
    unittest.main()
