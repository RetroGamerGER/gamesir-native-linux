#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual QML AppImage binding, fake inspection/elevation/system only."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['QT_QUICK_BACKEND']='software'
os.environ['QT_QUICK_CONTROLS_STYLE']='Basic'
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from PySide6.QtCore import QCoreApplication,QEvent,QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from app_packages import AppImageTransactions
from main import create_engine
from test_control_center_app_packages import fixture,FakeTransport,Adapter,COMPONENTS
import test_control_center_transactions_ui as ui


class BundleWindow(unittest.TestCase):
    item,click,wait_result=ui.BackendWindow.item,ui.BackendWindow.click,ui.BackendWindow.wait_result

    @classmethod
    def setUpClass(cls):
        cls.app=QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.root=Path(self.temp.name)
        self.engine=None;self.adapter=Adapter();self.reads=[];self.main_thread=threading.get_ident()
        self.profile,self.trust=fixture(self.root)
        self.release=threading.Event();self.release.set()

    def open(self,code=0,calibration_factory=None):
        def read(request):
            self.reads.append((threading.get_ident(),request))
            def collect():
                if not self.release.wait(3):raise RuntimeError('Fixture timeout')
                return self.adapter.observe()
            return Mock(collect=collect)
        self.tx=AppImageTransactions(self.root,reader=read,clock=lambda:100,
            transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.trust,code))
        self.engine=create_engine(self.root/'prefs.ini',demo=False,collector=Mock(collect=lambda:None),
                                  execution=self.tx,calibration_factory=calibration_factory)
        self.window=self.engine.rootObjects()[0];self.window.resize(940,1020)
        self.model=self.engine.center_model;self.model.setLanguage('en')
        self.wait_state(('idle','blocked'))

    def wait_state(self,states):
        for _ in range(150):
            if self.tx.state in states:return
            QTest.qWait(20)
        self.fail('Inspection did not complete')

    def tearDown(self):
        self.release.set();QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()
        if self.engine:
            self.window.close();self.engine.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()
        self.temp.cleanup()

    def review(self,action='install'):
        self.click(action+'Button');self.click('backendProceed');self.wait_state(('review',))

    def test_async_install_selection_review_password_boundary_and_postcheck(self):
        self.open();self.assertTrue(self.model.view['canInstall']);self.assertFalse(self.model.isRehearsal)
        self.review()
        self.assertFalse(self.tx.transport.sent)
        self.assertEqual(len(self.reads),2)
        self.assertTrue(all(t!=self.main_thread for t,r in self.reads))
        reads=len(self.reads)
        for _ in range(20):self.model.view;self.model.backend
        self.assertEqual(len(self.reads),reads)
        self.assertIn('SHA256',self.model.backend['review'])
        self.click('backendProceed');self.wait_result()
        self.assertEqual(self.tx.outcome.state,'verified_success')
        self.assertFalse(self.model.view['canRemove']);self.model.refresh();QTest.qWait(60)
        self.assertFalse(self.model.view['canInstall'])
        self.assertEqual(len(self.tx.transport.sent),1)
        self.model.confirmBackend();self.assertEqual(len(self.tx.transport.sent),1)

    def test_removal_includes_explicit_dependent_selection(self):
        self.adapter.host=replace(self.adapter.host,installed=tuple(
            (COMPONENTS[r.component][0],r.version) for r in self.trust.catalog.records if r.component in ('core','bridge')))
        self.open();self.click('removeButton')
        self.model.selectBackendComponent('bridge',True)
        self.click('backendProceed');self.wait_state(('review',))
        self.assertIn('gamesir-native-trigger-bridge',self.model.backend['review'])
        self.assertFalse(self.tx.transport.sent)
        self.click('backendProceed');self.wait_result()
        self.assertEqual(self.tx.outcome.state,'verified_success');self.assertEqual(self.adapter.host.installed,())
        self.assertTrue(self.model.backend['verifiedSuccess'])
        self.assertEqual(self.model.backend['successTitle'],'Successfully uninstalled')
        self.assertEqual(self.item('backendCancel').property('text'),'Done')
        self.click('backendCancel')
        self.assertFalse(self.item('backendDialog').property('visible'))
        self.assertTrue(self.window.isVisible())

    def test_cancel_during_slow_read_cannot_open_late_review_or_prompt(self):
        self.open();self.release.clear();self.click('installButton');self.click('backendProceed')
        self.assertEqual(self.tx.state,'checking');self.assertFalse(self.model.view['canRemove'])
        self.click('backendCancel');self.assertEqual(self.tx.state,'cancelled')
        self.release.set();QTest.qWait(120)
        self.assertEqual(self.tx.state,'cancelled');self.assertIsNone(self.tx.session)
        self.assertFalse(self.tx.transport.sent)

    def test_invalid_bundle_locks_buttons_and_shows_reason_without_fallback(self):
        (self.root/'profile.json').write_bytes(b'{}');self.open()
        self.assertEqual(self.tx.state,'blocked');self.assertIn('locked',self.model.view['notice'])
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.model.view['canRemove'])
        self.assertFalse(self.reads)

    def test_agent_cancellation_no_transaction_and_unknown_result_locks(self):
        self.open(code=126);self.review();self.click('backendProceed');self.wait_result()
        self.assertEqual(self.tx.outcome.state,'cancelled');self.assertNotIn('commit',self.adapter.calls)

    def test_uncertain_reply_locks_both_buttons_in_german(self):
        self.open(code=2);self.model.setLanguage('de');self.review()
        self.click('backendProceed');self.wait_result()
        self.assertEqual(self.tx.outcome.state,'uncertain');self.assertIn('Frisch prüfen',self.model.backend['message'])
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.model.view['canRemove'])


if __name__=='__main__':unittest.main()
