#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""First-run QML tests with fixture agents/files/commands only."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['QT_QUICK_BACKEND']='software'
os.environ['QT_QUICK_CONTROLS_STYLE']='Basic'
from pathlib import Path
import sys,tempfile,threading,time,unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from PySide6.QtCore import QCoreApplication,QEvent,QThreadPool
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from main import create_engine
from first_run import FirstRunTransactions
from helper_setup import SetupInspector,SetupCommandError
from test_control_center_first_run import setup_fixture,FakeTarget
from test_control_center_app_packages import Adapter,FakeTransport
import test_control_center_transactions_ui as ui


class SetupWindow(unittest.TestCase):
    item,click=ui.BackendWindow.item,ui.BackendWindow.click

    @classmethod
    def setUpClass(cls):
        cls.app=QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.root=Path(self.temp.name)
        self.packages,self.sources,self.bundle,self.payload,self.trust=setup_fixture(self.root)
        self.target=FakeTarget();self.adapter=Adapter();self.engine=None
        self.read_threads=[];self.release=threading.Event();self.release.set()
        self.main_thread=threading.get_ident()

    def open(self,runner=None):
        def reader(request):
            self.read_threads.append(threading.get_ident())
            return Mock(collect=self.adapter.observe)
        self.tx=FirstRunTransactions(self.packages,inspector=SetupInspector(self.target),
            reader=reader,setup_runner=runner or self.target.runner,clock=lambda:100,
            transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.trust))
        self.engine=create_engine(self.root/'prefs.ini',demo=False,collector=Mock(collect=lambda:None),execution=self.tx)
        self.model=self.engine.center_model;self.window=self.engine.rootObjects()[0]
        self.window.resize(940,1020);self.model.setLanguage('de')
        self.wait_state(('setup_required','idle','blocked'))

    def wait_state(self,states):
        # Give Python I/O workers the GIL as the real Qt exec loop does;
        # repeated native QTest.qWait can starve the path-verification worker.
        for _ in range(500):
            if self.tx.state in states:return
            self.app.processEvents(); time.sleep(0.01)
        self.fail('Setup state timed out: '+self.tx.state)

    def tearDown(self):
        self.release.set();QThreadPool.globalInstance().waitForDone(5000);self.app.processEvents()
        if self.engine:
            self.window.close();self.engine.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()
        self.temp.cleanup()

    def test_first_start_offers_only_after_passive_check_no_automatic_auth(self):
        self.open();self.assertTrue(self.item('setupButton').property('visible'))
        self.assertTrue(self.model.setup['offer']);self.assertFalse(self.target.calls)
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.model.view['canRemove'])
        self.assertTrue(all(t!=self.main_thread for t in self.read_threads))
        self.click('setupButton')
        self.assertTrue(self.item('setupDialog').property('visible'))
        self.assertIn('13',self.model.setup['summary']);self.assertFalse(self.target.calls)
        self.click('setupCancel')
        self.assertFalse(self.item('setupDialog').property('visible'))
        self.assertEqual(self.tx.state,'setup_required');self.assertFalse(self.target.calls)

    def test_confirmed_fixture_setup_success_done_keeps_main_window_and_never_installs_package(self):
        self.open();self.click('setupButton');self.click('setupConfirm');self.wait_state(('setup_done',))
        self.assertEqual(len(self.target.calls),16)
        self.assertEqual(self.model.setup['message'],'Helfer erfolgreich eingerichtet')
        self.assertEqual(self.item('setupCancel').property('text'),'Fertig')
        self.model.confirmSetup();self.assertEqual(len(self.target.calls),16)
        self.click('setupCancel');self.wait_state(('idle',))
        self.assertFalse(self.item('setupDialog').property('visible'));self.assertTrue(self.window.isVisible())
        self.assertFalse(self.item('setupButton').property('visible'))
        self.assertTrue(self.model.view['canInstall']);self.assertFalse(self.tx.transport.sent)
        self.assertNotIn('lock',self.adapter.calls)

    def test_matching_existing_helper_no_offer_or_authentication(self):
        self.target.seed(self.payload);self.open()
        self.assertEqual(self.tx.state,'idle');self.assertFalse(self.model.setup['offer'])
        self.assertFalse(self.item('setupButton').property('visible'));self.assertFalse(self.target.calls)
        self.model.requestSetup();self.model.confirmSetup();self.assertFalse(self.target.calls)

    def test_partial_existing_state_never_offers_overwrite(self):
        self.target.dirs['/var/cache/gamesir-control-center']=0o700;self.open()
        self.assertEqual(self.tx.state,'blocked');self.assertFalse(self.model.setup['offer'])
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.target.calls)

    def test_running_setup_disables_close_and_duplicate_confirm(self):
        def slow(argv,source=None):
            if not self.release.wait(3):raise SetupCommandError('fixture_timeout')
            self.target.runner(argv,source)
        self.open(runner=slow);self.click('setupButton');self.release.clear();self.click('setupConfirm')
        self.assertEqual(self.tx.state,'setup_running')
        self.assertFalse(self.item('setupCancel').property('enabled'))
        self.assertFalse(self.item('setupConfirm').property('visible'))
        self.model.confirmSetup();self.assertFalse(self.target.calls)
        self.release.set();self.wait_state(('setup_done',));self.assertEqual(len(self.target.calls),16)

    def test_failed_setup_visible_english_and_no_retry_or_package_action(self):
        attempts=[]
        def fail(argv,source=None):attempts.append(argv);raise SetupCommandError('setup_command_failed')
        self.open(runner=fail);self.model.setLanguage('en')
        self.click('setupButton');self.click('setupConfirm');self.wait_state(('setup_failed',))
        self.assertTrue(self.item('setupDialog').property('visible'))
        self.assertFalse(self.model.setup['success']);self.assertIn('No automatic retry',self.model.setup['message'])
        self.assertFalse(self.model.view['canInstall']);self.assertFalse(self.model.view['canRemove'])
        self.model.confirmSetup();self.assertEqual(len(attempts),1)
        self.click('setupCancel');self.assertTrue(self.window.isVisible());self.assertFalse(self.model.setup['offer'])


if __name__=='__main__':unittest.main()
