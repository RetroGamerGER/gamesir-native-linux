#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Optional Qt offscreen tests: no display server, devices or network needed."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import io
from contextlib import redirect_stderr
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/imu'))
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import gamesir_gyro_viewer as ui
import test_gyro_axis_profile as capture_fixture


class Window(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=ui.QApplication.instance() or ui.QApplication([])

    def setUp(self):
        self.fixture=capture_fixture.CoherentReplay();self.fixture.setUp()
        self.window=ui.Viewer();self.window.timer.stop()

    def tearDown(self):
        self.window.close();self.window.deleteLater();self.app.processEvents()
        self.fixture.tearDown()

    def load(self):
        self.window.load_capture(self.fixture.capture,2000)
        self.window.show();self.app.processEvents()

    def test_no_source_or_selected_profile_at_start(self):
        self.assertIsNone(self.window.playback)
        self.assertIsNone(self.window.profile_box.currentData())
        self.assertFalse(self.window.play_button.isEnabled())
        with patch.object(ui.QMessageBox,'information') as message, \
                patch.object(ui.QFileDialog,'getExistingDirectory') as chooser:
            self.window.choose_capture()
            message.assert_called_once();chooser.assert_not_called()

    def test_controls_seek_play_pause_center_gain_restart_and_end(self):
        self.load();w=self.window;b=w.playback
        self.assertFalse(b.playing)
        w.timeline.setValue(5000)
        self.assertAlmostEqual(b.position,b.clip.duration*.5)
        raw=b.frame.gyro_raw;q=b.frame.orientation
        w.gain_slider.setValue(200);self.assertEqual(b.gain,2)
        self.assertEqual(b.frame.gyro_raw,raw);self.assertEqual(b.frame.orientation,q)
        QTest.mouseClick(w.center_button,Qt.MouseButton.LeftButton)
        self.assertAlmostEqual(ui.rotation_degrees(b.orientation),0)
        QTest.mouseClick(w.play_button,Qt.MouseButton.LeftButton);self.assertTrue(b.playing)
        QTest.mouseClick(w.play_button,Qt.MouseButton.LeftButton);self.assertFalse(b.playing)
        w.speed_box.setCurrentIndex(3);self.assertEqual(b.speed,4)
        b.playing=True;b.advance(1);w.refresh()
        self.assertFalse(b.playing);self.assertIn('Replay beendet',w.position_label.text())
        QTest.mouseClick(w.restart_button,Qt.MouseButton.LeftButton)
        self.assertEqual(b.position,0);self.assertFalse(b.playing)

    def test_profile_rebuild_is_paused_and_does_not_relabel_old_results(self):
        self.load();w=self.window;w.playback.playing=True
        w.profile_box.setCurrentIndex(w.profile_box.findData(125))
        self.assertEqual(w.playback.clip.profile,125)
        self.assertFalse(w.playback.playing)
        self.assertIn('0.004375',w.warning.text())
        w.profile_box.setCurrentIndex(0)
        self.assertIsNone(w.playback);self.assertFalse(w.play_button.isEnabled())

    def test_rejected_replacement_clears_old_animation(self):
        self.load();w=self.window
        (self.fixture.capture/'scans.bin').write_bytes(b'broken')
        with patch.object(ui.QMessageBox,'warning') as message:
            w.try_load(self.fixture.capture,2000)
        message.assert_called_once();self.assertIsNone(w.playback)
        self.assertIsNone(w.capture_path);self.assertFalse(w.play_button.isEnabled())

    def test_software_render_at_minimum_and_normal_size(self):
        self.load()
        for width,height in ((900,880),(1080,900)):
            self.window.resize(width,height);self.app.processEvents()
            pixmap=self.window.grab()
            self.assertFalse(pixmap.isNull())
            self.assertGreater(self.window.view.height(),300)
            self.assertTrue(self.window.gain_slider.isVisible())
            self.assertLess(self.window.view.geometry().bottom(),self.window.values.geometry().top())

    def test_close_stops_playback_and_timer(self):
        self.load();self.window.playback.playing=True;self.window.timer.start()
        self.window.close()
        self.assertFalse(self.window.playback.playing)
        self.assertFalse(self.window.timer.isActive())

    def test_real_qt_timer_reaches_end_without_extrapolation(self):
        self.load();w=self.window
        w.timer.start();w.toggle_play()
        QTest.qWait(200)
        self.assertFalse(w.playback.playing)
        self.assertEqual(w.playback.position,w.playback.clip.duration)
        final=w.playback.orientation
        QTest.qWait(60)
        self.assertEqual(final,w.playback.orientation)

    def test_cli_rejects_implicit_gain_or_live_mode(self):
        for args in (['--capture-dir','unused'],['--live'],['--profile','999']):
            with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):ui.main(args)


if __name__=='__main__':
    unittest.main()
