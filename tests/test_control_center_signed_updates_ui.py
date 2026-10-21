#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real offscreen QML, signed public fixture seed and fake HTTPS/host/helper."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['QT_QUICK_BACKEND']='software'
os.environ['QT_QUICK_CONTROLS_STYLE']='Basic'
from pathlib import Path
import sys,tempfile,threading,unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from PySide6.QtCore import QCoreApplication,QEvent,QEventLoop,QThreadPool,QTimer
from PySide6.QtGui import QGuiApplication
from app_packages import AppImageTransactions
from main import create_engine
from release_download import ReleaseDownloader
from test_control_center_app_packages import FakeTransport,Adapter
from test_control_center_release_download import Client,Reply
from test_control_center_signed_updates import signed_fixture,sign_payload,content,NOW
from package_wire import encode,decode
import test_control_center_transactions_ui as ui

class SignedUpdateWindow(unittest.TestCase):
    item,click=ui.BackendWindow.item,ui.BackendWindow.click
    @classmethod
    def setUpClass(cls):
        cls.app=QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.root=Path(self.temp.name)
        self.anchor,self.blobs=signed_fixture(self.root)
        self.envelope=sign_payload(encode(content(self.anchor)))
        self.net=Client([Reply(self.envelope)]);self.adapter=Adapter();self.threads=[]
        def collect():self.threads.append(threading.get_ident());return self.adapter.observe()
        self.tx=AppImageTransactions(self.root,clock=lambda:100,wall_clock=lambda:NOW,
            downloader=ReleaseDownloader(self.net,clock=lambda:100),reader=lambda r:Mock(collect=collect),
            transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.anchor))
        self.engine=create_engine(self.root/'prefs.ini',demo=False,collector=Mock(collect=lambda:None),execution=self.tx)
        self.window=self.engine.rootObjects()[0];self.window.resize(940,1080)
        self.model=self.engine.center_model;self.model.setLanguage('en')
        self.wait(lambda:self.tx.state=='idle')
    def wait(self,predicate):
        loop=QEventLoop();timer=QTimer();timer.setInterval(10)
        timer.timeout.connect(lambda:loop.quit() if predicate() else None)
        timer.start();QTimer.singleShot(5000,loop.quit);loop.exec();timer.stop()
        self.assertTrue(predicate())
    def tearDown(self):
        if self.tx.state=='checking_updates':self.tx.cancel()
        QThreadPool.globalInstance().waitForDone(5000);self.app.processEvents()
        self.window.close();self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents();self.temp.cleanup()
    def finish(self):self.wait(lambda:self.model.inspection_job is None and self.tx.state=='idle')
    def test_user_click_checks_signed_catalog_in_worker_without_password_or_install(self):
        self.assertFalse(self.net.calls);self.assertFalse(self.model.view['canInstall'])
        button=self.item('checkUpdatesButton');self.assertTrue(button.property('visible'))
        self.assertEqual(button.property('text'),'Check driver updates')
        self.click('checkUpdatesButton');self.finish()
        self.assertEqual(len(self.net.calls),1);self.assertTrue(self.model.view['canInstall'])
        self.assertIn('Signed catalog verified',self.model.view['notice'])
        self.assertFalse(self.tx.transport.sent);self.assertNotIn('lock',self.adapter.calls)
        self.assertTrue(all(t!=threading.get_ident() for t in self.threads))
    def test_invalid_signature_shows_failure_and_keeps_installation_disabled(self):
        self.net.replies=[Reply(encode({**decode(self.envelope),'signature':'0'*128}))]
        self.click('checkUpdatesButton');self.finish()
        self.assertIn('release_signature_invalid',self.model.view['notice'])
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.tx.transport.sent)
    def test_cancel_discards_late_result_and_localization(self):
        entered,release=threading.Event(),threading.Event()
        def block():
            entered.set()
            if not release.wait(3):raise OSError('fixture timeout')
        self.net.replies[0].on_read=block
        self.model.setLanguage('de');self.assertEqual(self.item('checkUpdatesButton').property('text'),'Treiberupdates prüfen')
        self.click('checkUpdatesButton');self.wait(entered.is_set)
        try:
            self.assertTrue(self.item('cancelUpdateCheckButton').property('visible'))
            self.click('cancelUpdateCheckButton');self.assertEqual(self.tx.state,'idle')
        finally:release.set()
        self.finish();self.assertIsNone(self.tx.bundle.signed_release)
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.tx.transport.sent)

if __name__=='__main__':unittest.main()
