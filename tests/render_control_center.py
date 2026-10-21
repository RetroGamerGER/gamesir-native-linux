#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Render our own QML preview using temporary preferences and software only."""
import os
import argparse
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Basic'
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QObject, QCoreApplication, QEvent, QEventLoop, QTimer, QThreadPool, QMetaObject
from PySide6.QtTest import QTest
from main import create_engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', action='store_true', help='render one genuine read-only local snapshot')
    args = parser.parse_args()
    app = QGuiApplication([])
    app.setQuitOnLastWindowClosed(False)
    dest = ROOT / 'build/control-center'
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        engine = create_engine(Path(temp) / 'preferences.ini', demo=not args.status)
        if not engine.rootObjects():
            return 1
        window = engine.rootObjects()[0]
        model = engine.center_model
        if args.status:
            loop = QEventLoop()
            def done():
                if not model.reading and (model.snapshot is not None or model.failed):
                    loop.quit()
            model.changed.connect(done)
            QTimer.singleShot(10000, loop.quit)
            loop.exec()
            model.changed.disconnect(done)
            if model.reading or model.failed:
                QThreadPool.globalInstance().waitForDone()
                return 1
        for language in ('de', 'en'):
            model.setLanguage(language)
            window.resize(940, 1180)
            QTest.qWait(100)
            prefix = 'control-center-status-' if args.status else 'control-center-'
            if not window.grabWindow().save(str(dest / (prefix + language + '.png'))):
                return 1
            if args.status:
                dialog = window.findChild(QObject, 'detailsDialog')
                QMetaObject.invokeMethod(dialog, 'open')
                QTest.qWait(100)
                window.grabWindow().save(str(dest / ('control-center-details-' + language + '.png')))
                QMetaObject.invokeMethod(dialog, 'close')
                QTest.qWait(50)
        model.setLanguage('de')
        window.resize(640, 520)
        model.selectScenario(2)
        QTest.qWait(100)
        window.grabWindow().save(str(dest / ('control-center-status-small.png' if args.status else 'control-center-small.png')))
        if args.status:
            QMetaObject.invokeMethod(dialog, 'open')
            QTest.qWait(100)
            window.grabWindow().save(str(dest / 'control-center-details-small.png'))
            QMetaObject.invokeMethod(dialog, 'close')
        if not args.status:
            window.resize(940, 900)
            model.selectScenario(0)
            model.request('install')
            QTest.qWait(100)
            window.grabWindow().save(str(dest / 'control-center-confirmation.png'))
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    print(dest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
