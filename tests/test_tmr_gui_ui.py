#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real QML + async worker + fake root session/manager, exclusively offline."""
import os
os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                  QT_QUICK_CONTROLS_STYLE='Basic')
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from PySide6.QtCore import QObject, QCoreApplication, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from main import create_engine
from tmr_bridge import CalibrationLive
from tmr_wire import encode
import test_control_center_calibration_ui as preview
import test_tmr_maintenance as native
from tmr_helper import Session


class FakeClient:
    def __init__(self, session, cancelled):
        self.session,self.cancelled=session,cancelled
        self.number=0;self.calls=[];self.thread_ids=[];self.closed=False

    def call(self,action,**fields):
        self.thread_ids.append(threading.get_ident())
        if self.cancelled():raise RuntimeError('cancelled')
        self.calls.append(action);self.number+=1
        return self.session.handle(encode({'schema':1,'id':self.number,'action':action,**fields}))

    def close(self):
        self.closed=True;self.session.close()


class LiveWindow(unittest.TestCase):
    item=preview.CalibrationWindow.item
    click=preview.CalibrationWindow.click

    @classmethod
    def setUpClass(cls):
        cls.app=QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.f=native.ManagerTmr();self.f.setUp()
        self.f.host.now=time.monotonic()
        s=self.f.backend.status
        packet=bytearray.fromhex(native.report());packet[51:55]=bytes((128,)*4)
        s.update(host_monotonic_ns=int(self.f.host.now*1e9),report=packet.hex())
        self.session=Session(self.f.manager.command,clock=lambda:self.f.host.now)
        self.clients=[]
        def factory(cancelled):
            client=FakeClient(self.session,cancelled);self.clients.append(client);return client
        self.engine=create_engine(Path(self.tmp.name)/'prefs.ini',demo=False,
                 collector=Mock(collect=Mock(return_value=None)),calibration_factory=factory)
        self.model=self.engine.center_model;self.window=self.engine.rootObjects()[0]
        self.bridge=self.model.stickCalibration
        self.bridge.changed.connect(self.bridge.timer.stop)  # Manual deterministic polling.
        self.window.resize(940,1000)
        QTest.qWait(40)

    def tearDown(self):
        self.bridge.shutdown();self.window.close()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.app.processEvents();self.tmp.cleanup()

    def wait(self,condition):
        deadline=time.monotonic()+3
        while not condition() and time.monotonic()<deadline:QTest.qWait(5)
        self.assertTrue(condition())

    def settle(self):
        self.wait(lambda:not self.bridge.busy and not getattr(self.bridge,'inflight',None))

    def open(self):
        self.click('calibrationOpen',scrolling='mainScroll');self.settle()
        self.assertTrue(self.item('calibrationDialog').property('visible'))

    def select(self):
        self.open();self.click('calibrationSelect',scrolling='calibrationScroll');self.settle()
        self.assertTrue(self.bridge.view['canStart'])

    def advance(self,active=0,done=0):
        self.f.host.now+=.25
        s=self.f.backend.status
        s.update(report=native.report(active,done),report_number=s['report_number']+1,
                 host_monotonic_ns=int(self.f.host.now*1e9))
        self.bridge.poll();self.settle()

    def start(self):
        self.select();self.click('calibrationStart');self.settle()
        for _ in range(13):self.advance()
        self.assertEqual(self.bridge.view['phase'],'measuring')

    def test_normal_construction_never_authenticates_and_label_is_pre_alpha(self):
        self.assertEqual(self.clients,[])
        self.assertIn('PRE-ALPHA',self.window.title())
        self.assertFalse(self.model.hasTransactions)
        self.assertFalse(self.item('calibrationDialog').property('visible'))

    def test_explicit_selection_precedes_start_and_only_one_client_per_run(self):
        self.select()
        self.assertEqual(self.clients[0].calls,['list','select'])
        self.assertNotIn('Start',self.f.backend.calls)
        self.assertEqual(len(self.clients),1)
        self.assertTrue(all(i!=threading.get_ident() for i in self.clients[0].thread_ids))

    def test_live_start_finish_and_cleanup_flow(self):
        self.start();self.advance(3,3)
        self.assertTrue(self.bridge.view['canFinish'])
        self.click('calibrationFinish');self.settle()
        self.assertEqual(self.bridge.view['phase'],'completed')
        self.assertFalse(self.bridge.view['leaseHeld'])
        self.assertEqual(self.f.backend.calls.count('Start'),1)
        self.assertEqual(self.f.backend.calls.count('Finish'),1)
        self.assertNotIn('Exit',self.f.backend.calls)
        self.assertEqual(len(self.clients),1)

    def hold_poll(self):
        entered,release=threading.Event(),threading.Event()
        client=self.clients[0];original=client.call
        def delayed(action,**fields):
            if action=='poll':
                entered.set();release.wait(2)
            return original(action,**fields)
        client.call=delayed
        self.addCleanup(release.set)
        self.bridge.poll();self.wait(entered.is_set)
        return release

    def test_background_poll_keeps_start_enabled_and_does_not_flash(self):
        self.select();release=self.hold_poll()
        try:
            QTest.qWait(40)
            self.assertTrue(self.bridge.view['canStart'])
            self.assertTrue(self.item('calibrationStart').property('enabled'))
            self.assertFalse(self.bridge.view['busy'])
        finally:release.set()
        self.settle()

    def test_click_during_poll_is_serialized_once_without_poll_backlog(self):
        self.select();release=self.hold_poll()
        try:
            for _ in range(25):self.bridge.poll()
            self.bridge.start();self.bridge.start()
        finally:release.set()
        self.settle()
        self.assertEqual(self.clients[0].calls,['list','select','poll','prepare'])
        self.assertEqual(self.bridge.view['phase'],'preparing')
        self.assertNotIn('Start',self.f.backend.calls)

    def test_close_discards_start_queued_behind_background_poll(self):
        self.select();release=self.hold_poll()
        self.bridge.start();self.bridge.close();release.set()
        self.wait(lambda:not self.bridge.worker.isRunning())
        self.assertNotIn('prepare',self.clients[0].calls)
        self.assertNotIn('Start',self.f.backend.calls)
        self.assertNotIn('Exit',self.f.backend.calls)

    def test_periodic_polling_keeps_fixed_cadence_and_no_start_button_flicker(self):
        self.select();self.bridge.changed.disconnect(self.bridge.timer.stop)
        original=self.clients[0].call
        def delayed(action,**fields):
            if action=='poll':time.sleep(.045)
            return original(action,**fields)
        self.clients[0].call=delayed
        self.bridge.timer.start()
        states=[]
        self.bridge.changed.connect(lambda:states.append(self.bridge.view['canStart']))
        deadline=time.monotonic()+.55
        while time.monotonic()<deadline:QTest.qWait(2)
        self.bridge.timer.stop();self.settle()
        self.assertGreaterEqual(self.clients[0].calls.count('poll'),5)
        self.assertTrue(states and all(states))

    def test_pending_finish_uses_new_readiness_and_never_replays(self):
        self.start();self.advance(3,3);release=self.hold_poll()
        self.bridge.finish();self.bridge.finish()
        self.f.backend.status['report']=native.report(3,1)
        self.f.backend.status['report_number']+=1
        self.f.host.now+=.1
        self.f.backend.status['host_monotonic_ns']=int(self.f.host.now*1e9)
        release.set();self.settle()
        self.assertFalse(self.bridge.view['canFinish'])
        self.assertNotIn('finish',self.clients[0].calls)
        self.assertNotIn('Finish',self.f.backend.calls)

    def test_pending_finish_runs_once_after_poll_and_preserves_serial_worker(self):
        self.start();self.advance(3,3);release=self.hold_poll()
        self.bridge.finish();self.bridge.finish();release.set();self.settle()
        self.assertEqual(self.clients[0].calls.count('finish'),1)
        self.assertEqual(self.f.backend.calls.count('Finish'),1)
        self.assertEqual(self.bridge.view['phase'],'completed')

    def test_failed_poll_discards_queued_start(self):
        self.select();release=self.hold_poll()
        self.bridge.start();self.f.backend.status['instance_token']+=1
        release.set();self.settle()
        self.assertFalse(self.bridge.view['running'])
        self.assertNotIn('prepare',self.clients[0].calls)
        self.assertNotIn('Start',self.f.backend.calls)

    def test_dialog_close_after_start_cancels_and_returns_without_finish(self):
        self.start();self.click('calibrationCancel')
        self.wait(lambda:not self.bridge.worker.isRunning())
        self.assertEqual(self.f.backend.calls.count('Exit'),1)
        self.assertEqual(self.f.backend.calls.count('release'),1)
        self.assertNotIn('Finish',self.f.backend.calls)
        self.assertTrue(self.window.isVisible())

    def test_no_preview_disconnect_or_new_run_buttons_in_live_mode(self):
        self.select()
        self.assertFalse(self.item('calibrationDisconnect').property('visible'))
        self.assertFalse(self.item('calibrationNew').property('visible'))

    def test_changed_instance_stops_without_finish_or_exit(self):
        self.start();self.f.backend.status['instance_token']+=1
        self.bridge.poll();self.settle()
        self.assertFalse(self.bridge.view['running'])
        self.assertFalse(self.bridge.view['canFinish'])
        self.assertNotIn('Finish',self.f.backend.calls)
        self.assertNotIn('Exit',self.f.backend.calls)

    def test_stale_worker_result_cannot_update_closed_or_new_dialog(self):
        self.select();before=self.bridge.view
        self.bridge.receive(self.bridge.generation-1,{'view':{'phase':'completed'}})
        self.assertEqual(self.bridge.view,before)
        self.bridge.close()
        self.bridge.receive(self.bridge.generation,{'failed':True})
        self.assertTrue(self.bridge.blocked)

    def test_language_switch_preserves_run_and_empty_target_list_is_clear(self):
        self.f.manager.paused=True;self.open()
        self.assertFalse(self.item('calibrationSelect').property('enabled'))
        self.model.setLanguage('de');self.app.processEvents()
        self.assertIn('auswählen',self.item('calibrationStatus').property('text'))
        self.assertEqual(len(self.clients),1)

    def test_auth_denial_is_terminal_and_does_not_select_or_touch_manager(self):
        self.bridge.factory=Mock(side_effect=RuntimeError('denied'))
        self.open()
        self.assertEqual(self.bridge.view['phase'],'error')
        self.f.host.open_tmr.assert_not_called()
        self.assertFalse(self.bridge.open())

    def test_close_during_authorization_stays_responsive(self):
        entered=threading.Event()
        def factory(cancelled):
            entered.set()
            while not cancelled():time.sleep(.005)
            raise RuntimeError('closed')
        self.bridge.factory=factory
        self.assertTrue(self.bridge.open());self.wait(entered.is_set)
        self.bridge.close();self.bridge.shutdown()
        self.assertFalse(self.bridge.worker.isRunning())
        self.f.host.open_tmr.assert_not_called()

    def test_synthetic_modes_reject_permission_factory(self):
        from PySide6.QtCore import QSettings
        from qt_bridge import CenterModel
        settings=QSettings(str(Path(self.tmp.name)/'other.ini'),QSettings.Format.IniFormat)
        factory=Mock()
        with self.assertRaises(ValueError):CenterModel(settings,demo=True,calibration_factory=factory)
        factory.assert_not_called()

    def test_render_live_selection_and_ready_in_both_languages(self):
        self.open()
        output=ROOT/'build/tmr-gui-offline';output.mkdir(parents=True,exist_ok=True)
        for lang in ('de','en'):
            self.model.setLanguage(lang);self.app.processEvents();QTest.qWait(20)
            image=self.window.grabWindow()
            self.assertFalse(image.isNull());self.assertTrue(image.save(str(output/f'select-{lang}.png')))
        self.click('calibrationSelect',scrolling='calibrationScroll');self.settle()
        QTest.qWait(20)
        self.assertTrue(self.window.grabWindow().save(str(output/'ready.png')))


if __name__=='__main__':unittest.main()
