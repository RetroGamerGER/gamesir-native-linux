#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Optional software-rendered QML tests. No display, real links or host probes."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
from pathlib import Path
import sys
import tempfile
import unittest
import threading
import time
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtCore import QObject, QSettings, Qt, QPoint, QPointF, QCoreApplication, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from main import create_engine
from qt_bridge import CenterModel
from model import LINKS, SITUATIONS
from status import Snapshot, Fact


class CenterWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings_file = Path(self.temp.name) / 'preferences.ini'
        self.engine = create_engine(self.settings_file)
        self.assertEqual(len(self.engine.rootObjects()), 1)
        self.window = self.engine.rootObjects()[0]
        self.model = self.engine.center_model
        self.opened = []
        self.model.opener = lambda url: self.opened.append(url.toString()) or True
        self.window.resize(940, 1020)
        QTest.qWait(60)

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def item(self, name):
        found = self.window.findChild(QObject, name)
        self.assertIsNotNone(found, name)
        return found

    def click(self, name):
        item = self.item(name)
        self.assertTrue(item.property('enabled'))
        # Source-authored controls: scroll the item into view, then exercise Qt's real input path.
        scroll = self.item('mainScroll')
        flickable = scroll.property('contentItem')
        pt = item.mapToItem(flickable, QPointF(0, 0))
        height = self.window.height()
        if pt.y() > height - 80:
            flickable.setProperty('contentY', max(0, pt.y() - height / 2))
            QTest.qWait(30)
        scene = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                         QPoint(round(scene.x()), round(scene.y())))
        QTest.qWait(30)

    def test_qml_loads_and_demo_does_not_create_preferences(self):
        self.assertFalse(self.settings_file.exists())
        self.assertFalse(self.model.view['installed'])
        self.assertEqual(self.opened, [])

    def test_language_clicks_translate_and_persist(self):
        self.click('languageDe')
        self.assertEqual(self.item('installButton').property('text'), 'Treiber installieren')
        self.click('languageEn')
        self.assertEqual(self.item('installButton').property('text'), 'Install driver')
        settings = QSettings(str(self.settings_file), QSettings.Format.IniFormat)
        restored = CenterModel(settings, 'de_DE', opener=lambda _: True)
        self.assertEqual(restored.language, 'en')
        self.assertEqual(set(settings.allKeys()), {'language'})

    def test_explicit_current_language_is_saved_too(self):
        current = self.model.language
        self.assertFalse(self.settings_file.exists())
        self.model.setLanguage(current)
        self.assertTrue(self.settings_file.exists())
        restored = CenterModel(QSettings(str(self.settings_file), QSettings.Format.IniFormat),
                               'de_DE' if current == 'en' else 'en_US')
        self.assertEqual(restored.language, current)

    def test_install_dialog_confirmation_and_result_by_mouse(self):
        self.model.setLanguage('en')
        self.click('installButton')
        self.assertTrue(self.item('confirmationDialog').property('visible'))
        self.assertFalse(self.model.view['installed'])
        self.click('confirmButton')
        self.assertTrue(self.item('resultDialog').property('visible'))
        self.assertTrue(self.model.view['installed'])
        self.assertFalse(self.model.view['loaded'])
        self.assertEqual(self.model.view['manager'], 'Not started')
        self.click('resultCloseButton')
        self.assertFalse(self.item('resultDialog').property('visible'))

    def test_escape_cancels_dialog_and_does_not_install(self):
        self.click('installButton')
        QTest.keyClick(self.window, Qt.Key.Key_Escape)
        QTest.qWait(50)
        self.assertFalse(self.model.view['installed'])
        self.assertEqual(self.model.preview.result[0], 'result_cancelled')

    def test_remove_button_confirmation_cancel_and_success(self):
        self.model.selectScenario(1)
        self.click('removeButton')
        self.assertTrue(self.item('confirmationDialog').property('visible'))
        self.click('cancelButton')
        self.assertTrue(self.model.view['installed'])
        self.click('resultCloseButton')
        self.click('removeButton')
        self.click('confirmButton')
        self.assertFalse(self.model.view['installed'])
        self.assertFalse(self.model.view['loaded'])
        self.assertTrue(self.item('resultDialog').property('visible'))

    def test_keyboard_focus_and_enter(self):
        button = self.item('installButton')
        button.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key.Key_Return)
        QTest.qWait(40)
        self.assertTrue(self.item('confirmationDialog').property('visible'))
        QTest.keyClick(self.window, Qt.Key.Key_Tab)
        QTest.keyClick(self.window, Qt.Key.Key_Escape)
        QTest.qWait(30)
        self.assertFalse(self.model.view['installed'])

    def test_combo_selection_and_normal_receiver_wait(self):
        box = self.item('scenarioBox')
        box.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key.Key_Down)
        QTest.keyClick(self.window, Qt.Key.Key_Down)
        QTest.qWait(40)
        self.assertEqual(self.model.scenarioIndex, 2)
        self.assertTrue(self.model.view['receiver'])
        self.assertFalse(self.model.view['connected'])
        self.assertFalse(self.model.view['noticeWarning'])

    def test_every_error_case_is_localized_and_can_be_previewed(self):
        for language in ('de', 'en'):
            self.model.setLanguage(language)
            for index, situation in enumerate(SITUATIONS):
                self.model.selectScenario(index)
                self.app.processEvents()
                self.assertTrue(self.model.view['notice'])
                if self.model.view['canInstall']:
                    self.model.request('install'); self.model.confirm()
                    self.assertTrue(self.model.result['body'])
                    self.item('resultDialog').setProperty('visible', False)
                    self.item('confirmationDialog').setProperty('visible', False)

    def test_explicit_links_only_and_browser_failure_message(self):
        self.assertFalse(self.opened)
        self.model.openLink('unknown')
        self.assertFalse(self.opened)
        self.model.openLink('github'); self.model.openLink('deadband')
        self.assertEqual(self.opened, [LINKS['github'], LINKS['deadband']])
        self.model.opener = lambda _: False
        self.model.openLink('github')
        self.assertTrue(self.model.view['linkError'])
        self.model.setLanguage('de')
        self.assertIn('Browser', self.model.view['linkError'])

    def test_minimum_and_normal_size_render_and_scroll_to_last_action(self):
        for language in ('de', 'en'):
            self.model.setLanguage(language)
            for width, height in ((560, 480), (640, 520), (940, 1180)):
                self.window.resize(width, height)
                QTest.qWait(70)
                self.assertFalse(self.window.grabWindow().isNull())
                self.assertLessEqual(self.item('statusCard').width(), width)
                self.assertGreater(self.item('installButton').width(), 150)
                self.click('deadbandButton')
                self.assertEqual(self.opened[-1], LINKS['deadband'])

    def test_keyboard_focus_scrolls_lower_controls_into_view(self):
        self.window.resize(560, 480)
        QTest.qWait(50)
        button = self.item('deadbandButton')
        button.forceActiveFocus()
        QTest.qWait(40)
        point = button.mapToScene(QPointF(0, 0))
        self.assertGreaterEqual(point.y(), 0)
        self.assertLessEqual(point.y() + button.height(), self.window.height())

    def test_both_confirmation_dialogs_fit_minimum_window(self):
        self.window.resize(560, 480)
        for language in ('de', 'en'):
            self.model.setLanguage(language)
            for action, index in (('install', 0), ('remove', 1)):
                self.model.selectScenario(index)
                self.model.request(action)
                QTest.qWait(30)
                dialog = self.item('confirmationDialog')
                self.assertLessEqual(dialog.property('height'), self.window.height() - 20)
                self.assertLessEqual(dialog.property('width'), self.window.width() - 20)
                self.assertFalse(self.item('confirmButton').property('text') == '')
                self.model.preview.pending = ''
                dialog.setProperty('visible', False)

    def test_after_removal_receiver_presence_does_not_claim_radio_wait(self):
        self.model.setLanguage('en')
        self.model.selectScenario(1)
        self.model.preview.request('remove')
        self.model.preview.confirm()
        self.assertTrue(self.model.view['receiver'])
        self.assertFalse(self.model.view['loaded'])
        self.assertEqual(self.model.view['controller'], 'Not observed')

    def test_preference_write_failure_remains_translated_and_nonfatal(self):
        class Broken:
            Status = QSettings.Status
            def value(self, *args): return None
            def setValue(self, *args): pass
            def sync(self): pass
            def status(self): return QSettings.Status.AccessError
        model = CenterModel(Broken(), 'en')
        model.setLanguage('de')
        self.assertEqual(model.language, 'de')
        self.assertTrue(model.view['settingsError'])


class ReadOnlyWindow(unittest.TestCase):
    item = CenterWindow.item
    click = CenterWindow.click

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.calls = []
        self.gate = threading.Event()
        self.gate.set()
        self.outcome = Snapshot('2026-10-20T12:00:00Z', '2026-10-20T12:00:01Z', {
            'os': Fact('ok', 'Test Linux'), 'kernel': Fact('ok', '7.test'),
            'architecture': Fact('ok', 'x86_64'), 'support': Fact('ok'),
            'headers': Fact('match', '7.test'), 'module': Fact('loaded', '0.1.0.alpha3'),
            'gamesir-native-dkms': Fact('ok', '0.1.0.alpha3-16'),
            'receiver': Fact('absent'), 'connection': Fact('unobserved')})
        owner = self
        class FakeCollector:
            def collect(self):
                owner.calls.append(threading.get_ident())
                owner.gate.wait(2)
                if isinstance(owner.outcome, Exception):
                    raise owner.outcome
                return owner.outcome
        self.engine = create_engine(Path(self.temp.name) / 'preferences.ini',
                                    demo=False, collector=FakeCollector())
        self.window = self.engine.rootObjects()[0]
        self.model = self.engine.center_model
        self.model.opener = lambda _: self.fail('No unsolicited link')
        self.window.resize(940, 1020)
        self.wait_ready()

    def wait_ready(self):
        for _ in range(100):
            QTest.qWait(10)
            if self.calls and not self.model.reading:
                break
        self.assertFalse(self.model.reading)

    def tearDown(self):
        self.gate.set()
        from PySide6.QtCore import QThreadPool
        QThreadPool.globalInstance().waitForDone(3000)
        self.app.processEvents()
        self.window.close()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def test_real_mode_and_reading_happen_off_ui_thread(self):
        self.assertFalse(self.model.isDemo)
        self.assertEqual(len(self.calls), 1)
        self.assertNotEqual(self.calls[0], threading.get_ident())
        self.assertFalse(self.item('scenarioBox').property('visible'))
        self.assertTrue(self.item('refreshButton').property('visible'))
        self.assertIn('0.1.0.alpha3-16', self.model.view['driver'])
        self.assertEqual(self.model.view['sampleTime'], self.outcome.finished)

    def test_live_install_remove_and_forced_demo_slots_are_inert(self):
        for name in ('installButton', 'removeButton'):
            self.assertFalse(self.item(name).property('enabled'))
        self.model.selectScenario(1)
        self.model.preview.request('install')  # Even a stale synthetic request cannot execute.
        self.model.request('install'); self.model.request('remove')
        self.model.confirm(); self.model.cancel()
        self.assertEqual(self.model.scenarioIndex, 0)
        self.assertFalse(self.item('confirmationDialog').property('visible'))
        self.assertFalse(self.item('resultDialog').property('visible'))
        self.assertEqual(len(self.calls), 1)

    def test_refresh_replaces_snapshot_and_cannot_overlap(self):
        self.gate.clear()
        self.click('refreshButton')
        self.assertTrue(self.model.reading)
        self.assertFalse(self.item('refreshButton').property('enabled'))
        self.assertEqual(self.model.view['sampleTime'], '')
        for _ in range(10):
            self.model.refresh()
        self.assertEqual(len(self.calls), 2)
        self.click('languageDe')  # UI remains responsive while reading.
        self.gate.set(); self.wait_ready()
        self.assertEqual(self.model.language, 'de')
        self.assertEqual(len(self.calls), 2)

    def test_failed_refresh_clears_previous_values_without_retry(self):
        self.outcome = RuntimeError('/home/private-user/never-display')
        self.click('refreshButton'); self.wait_ready()
        self.assertTrue(self.model.failed)
        self.assertNotIn('0.1.0.alpha3-16', self.model.view['driver'])
        self.assertNotIn('private-user', str(self.model.view))
        self.assertEqual(len(self.calls), 2)

    def test_status_and_details_translate_without_rereading(self):
        self.click('languageDe')
        self.assertIn('Funkverbindung', self.model.view['controller'])
        self.click('languageEn')
        self.assertIn('Wireless', self.model.view['controller'])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.model.view['details']), 10)

    def test_details_open_separately_without_pushing_main_content(self):
        self.assertIsNone(self.window.findChild(QObject, 'detailsCard'))
        dialog = self.item('detailsDialog')
        self.assertFalse(dialog.property('visible'))
        installation_y = self.item('installationCard').y()
        status = self.item('statusCard')
        self.assertLessEqual(installation_y - status.y() - status.height(), 24)
        self.click('detailsButton')
        self.assertTrue(dialog.property('visible'))
        self.assertEqual(self.item('installationCard').y(), installation_y)
        self.assertEqual(len(self.calls), 1)  # Opening details does not query the host again.
        self.click('detailsCloseButton')
        self.assertFalse(dialog.property('visible'))
        self.assertTrue(self.item('detailsButton').hasActiveFocus())
        self.assertEqual(self.item('installationCard').y(), installation_y)

    def test_details_dialog_keyboard_translation_and_small_window(self):
        for language, size in [('de', (560, 480)), ('en', (940, 1020))]:
            self.model.setLanguage(language)
            self.window.resize(*size)
            QTest.qWait(40)
            self.item('detailsButton').forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key.Key_Return)
            QTest.qWait(40)
            dialog = self.item('detailsDialog')
            self.assertTrue(dialog.property('visible'))
            self.assertEqual(dialog.property('title'), self.model.strings['system_details'])
            self.assertLessEqual(dialog.property('height'), self.window.height())
            self.assertLessEqual(dialog.property('width'), self.window.width())
            close = self.item('detailsCloseButton')
            point = close.mapToScene(QPointF(0, 0))
            self.assertGreaterEqual(point.x(), 0)
            self.assertGreaterEqual(point.y(), 0)
            self.assertLessEqual(point.y() + close.height(), self.window.height())
            scroll = self.item('detailsScroll')
            flick = scroll.property('contentItem')
            if language == 'de':
                self.assertGreater(flick.property('contentHeight'), scroll.property('availableHeight'))
            QTest.keyClick(self.window, Qt.Key.Key_Escape)
            QTest.qWait(40)
            self.assertFalse(dialog.property('visible'))
        self.assertEqual(len(self.calls), 1)

    def test_snapshot_age_never_silently_triggers_probes(self):
        self.model.received_at = time.monotonic() - 61
        self.model.changed.emit()
        self.assertEqual(self.model.view['sampleState'], self.model.strings['sample_stale'])
        self.assertEqual(len(self.calls), 1)

    def test_read_only_small_window_keyboard_and_scroll(self):
        self.window.resize(560, 480)
        QTest.qWait(40)
        self.assertFalse(self.window.grabWindow().isNull())
        self.click('refreshButton'); self.wait_ready()
        self.assertEqual(len(self.calls), 2)
        self.item('deadbandButton').forceActiveFocus()
        QTest.qWait(40)
        button = self.item('deadbandButton')
        y = button.mapToScene(QPointF(0, 0)).y()
        self.assertGreaterEqual(y, 0)
        self.assertLess(y + button.height(), 480)

    def test_closing_window_during_probe_is_safe(self):
        self.gate.clear(); self.model.refresh()
        QTest.qWait(10)
        self.window.close()
        self.gate.set(); self.wait_ready()
        self.assertFalse(self.window.isVisible())

    def test_application_quit_finishes_reader_before_qt_teardown(self):
        script = '''
import sys, time
from pathlib import Path
sys.path.insert(0, "tools/control_center")
import main as launcher
from status import Snapshot
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
original = launcher.create_engine
class SlowReader:
    def collect(self):
        time.sleep(0.15)
        print("reader finished", flush=True)
        return Snapshot("start", "end", {})
def create(**kwargs):
    engine = original(Path(sys.argv[1]), demo=False, collector=SlowReader())
    QTimer.singleShot(30, QGuiApplication.instance().quit)
    return engine
launcher.create_engine = create
raise SystemExit(launcher.main([]))
'''
        result = subprocess.run([sys.executable, '-B', '-c', script,
                                 str(Path(self.temp.name) / 'child.ini')],
                                cwd=ROOT, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('reader finished', result.stdout)
        self.assertNotIn('Signal source has been deleted', result.stderr)


if __name__ == '__main__':
    unittest.main()
