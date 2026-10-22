#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real QML input/rendering with a synthetic clock/controller, no host probes."""
import os
os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                  QT_QUICK_CONTROLS_STYLE='Basic')
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QObject, QCoreApplication, QEvent, QPointF, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from main import create_engine
from stick_calibration import Sample, SECTORS
from test_control_center_calibration import Clock


class CalibrationWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.no_probe = patch('qt_bridge.Collector.collect', side_effect=AssertionError('Host probe'))
        self.no_probe.start()
        self.engine = create_engine(Path(self.temp.name)/'preferences.ini', calibration_preview=True)
        self.window = self.engine.rootObjects()[0]
        self.model = self.engine.center_model
        self.bridge = self.model.stickCalibration
        self.clock = Clock(); self.clock.now = time.monotonic()
        self.bridge.session.clock = self.clock
        self.window.resize(940, 1000)
        QTest.qWait(40)

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.no_probe.stop()
        self.temp.cleanup()

    def item(self, name):
        value = self.window.findChild(QObject,name)
        if value is None:
            # Repeater delegates belong to a QML context in the QObject tree;
            # their actual visual parent is still the page (and receives input).
            todo=[self.window.contentItem()]
            while todo:
                item=todo.pop()
                if item.objectName()==name:
                    value=item;break
                todo.extend(item.childItems())
        self.assertIsNotNone(value,name)
        return value

    def click(self, name, *, scrolling=None):
        item = self.item(name)
        self.assertTrue(item.property('visible'),name)
        self.assertTrue(item.property('enabled'),name)
        if scrolling:
            scroll = self.item(scrolling)
            flick = scroll.property('contentItem')
            top = item.mapToItem(flick,QPointF(0,0)).y()
            flick.setProperty('contentY',max(0,top-scroll.height()/2))
            QTest.qWait(20)
        p = item.mapToScene(QPointF(item.width()/2,item.height()/2))
        QTest.mouseClick(self.window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,
                         QPoint(round(p.x()),round(p.y())))
        QTest.qWait(20)

    def open(self):
        self.click('calibrationOpen',scrolling='mainScroll')
        self.bridge.timer.stop()
        self.assertTrue(self.item('calibrationDialog').property('visible'))

    def start(self):
        self.click('calibrationStart')
        for _ in range(7):
            self.clock.advance(0.5);self.bridge.advance()
        self.bridge.timer.stop()
        self.app.processEvents()
        self.assertEqual(self.bridge.session.phase,'measuring')

    def feed(self, active=3, done=0, left=(0.,0.),right=(0.,0.)):
        self.clock.advance(0.1)
        s=self.bridge.session
        s.feed(s.key,Sample(s.last_sequence+1,self.clock(),left,right,active,done))
        self.bridge.changed.emit();self.app.processEvents()

    def operations(self): return [x.operation for x in self.bridge.session.port.intents]

    def test_open_has_badge_neutral_sticks_and_no_command(self):
        self.open()
        self.assertEqual(self.bridge.view['phase'],'ready')
        self.assertEqual(self.operations(),[])
        self.assertTrue(self.item('calibrationStart').property('enabled'))
        self.assertEqual(self.item('calibrationLeft').property('stick')['coverage'],0)

    def test_preparation_is_visible_and_escape_cancels_delayed_start(self):
        self.open();self.click('calibrationStart')
        self.assertEqual(self.bridge.session.phase,'preparing')
        self.assertIn('3',self.item('calibrationStatus').property('text'))
        QTest.keyClick(self.window,Qt.Key.Key_Escape);QTest.qWait(30)
        self.clock.advance(5);self.bridge.advance()
        self.assertFalse(self.item('calibrationDialog').property('visible'))
        self.assertFalse(self.bridge.timer.isActive())
        self.assertEqual(self.operations(),[])

    def test_plot_positions_and_progress_are_independent_per_stick(self):
        import math
        self.open();self.start()
        for n in range(SECTORS//2):
            a=(n+0.5)*math.tau/SECTORS
            self.feed(left=(math.cos(a),math.sin(a)))
        left=self.item('calibrationLeft').property('stick')
        right=self.item('calibrationRight').property('stick')
        self.assertGreaterEqual(left['coverage'],50)
        self.assertLess(right['coverage'],left['coverage'])
        self.assertFalse(self.item('calibrationFinish').property('visible'))

    def test_finish_button_waits_for_both_status_bits_and_never_repeats(self):
        self.open();self.start();self.feed(done=1)
        self.assertFalse(self.item('calibrationFinish').property('visible'))
        self.feed(done=3)
        self.assertTrue(self.item('calibrationFinish').property('enabled'))
        self.assertEqual(self.operations(),['Start'])
        self.click('calibrationFinish')
        self.assertEqual(self.operations(),['Start','Finish'])
        self.assertEqual(self.bridge.view['phase'],'completed')
        self.assertEqual(self.item('calibrationLeft').property('statusText'),
                         self.model.strings['cal_stick_done'])
        self.click('calibrationCancel')
        self.assertEqual(self.operations(),['Start','Finish'])
        self.assertTrue(self.window.isVisible())

    def test_disconnect_ui_drops_readiness_and_requires_deliberate_new_start(self):
        self.open();self.start();self.feed(done=3)
        old=self.bridge.session.key
        self.click('calibrationDisconnect',scrolling='calibrationScroll')
        self.assertEqual(self.bridge.view['phase'],'lost')
        self.assertFalse(self.item('calibrationFinish').property('visible'))
        self.assertEqual(self.operations(),['Start'])
        self.click('calibrationNew',scrolling='calibrationScroll')
        self.bridge.timer.stop()
        self.assertNotEqual(self.bridge.session.key,old)
        self.assertEqual(self.bridge.view['phase'],'ready')
        self.bridge.session.tick(old);self.bridge.finish()
        self.assertEqual(self.operations(),['Start'])

    def test_escape_after_ready_emits_exit_and_no_late_finish(self):
        self.open();self.start();self.feed(done=3)
        QTest.keyClick(self.window,Qt.Key.Key_Escape);QTest.qWait(30)
        self.bridge.advance();self.bridge.finish();self.bridge.close()
        self.assertEqual(self.operations(),['Start','Exit'])
        self.assertFalse(self.bridge.timer.isActive())

    def test_main_window_close_stops_the_session_once(self):
        self.open();self.start();self.feed()
        self.window.close();self.bridge.close()
        self.assertEqual(self.operations(),['Start','Exit'])
        self.assertFalse(self.bridge.timer.isActive())

    def test_languages_small_layout_and_software_render(self):
        self.open();self.start();self.feed(left=(.9,.1))
        for lang in ('de','en'):
            self.model.setLanguage(lang)
            for width,height in ((940,1000),(560,480)):
                self.window.resize(width,height);QTest.qWait(70)
                self.assertLessEqual(self.item('calibrationDialog').property('height'),height)
                self.assertLessEqual(self.item('calibrationDialog').property('width'),width)
                self.assertFalse(self.window.grabWindow().isNull())
                self.assertTrue(self.item('calibrationStatus').property('text'))
        self.click('calibrationCancel')
        self.assertFalse(self.item('calibrationDialog').property('visible'))

    def test_normal_app_cannot_enable_calibration_or_mix_with_real_status(self):
        from qt_bridge import CenterModel
        from PySide6.QtCore import QSettings
        settings=QSettings(str(Path(self.temp.name)/'other.ini'),QSettings.Format.IniFormat)
        normal=CenterModel(settings,demo=False)
        self.assertFalse(normal.stickCalibration.available)
        self.assertFalse(normal.stickCalibration.open())
        self.assertFalse(normal.stickCalibration.timer.isActive())
        normal.age_timer.stop()
        for kwargs in [dict(demo=False),dict(collector=object()),
                       dict(rehearsal=object()),dict(execution=object())]:
            with self.assertRaises(ValueError):
                CenterModel(settings,calibration_preview=True,**kwargs)

    def test_keyboard_reveals_disconnect_control_on_small_screen(self):
        self.open();self.start()
        self.window.resize(560,480);QTest.qWait(50)
        button=self.item('calibrationDisconnect');button.forceActiveFocus()
        QTest.qWait(30)
        scroll=self.item('calibrationScroll')
        top=button.mapToItem(scroll,QPointF(0,0)).y()
        self.assertGreaterEqual(top,0)
        self.assertLessEqual(top+button.height(),scroll.height())
        QTest.keyClick(self.window,Qt.Key.Key_Return);QTest.qWait(20)
        self.assertEqual(self.bridge.view['phase'],'lost')


if __name__=='__main__':unittest.main()
