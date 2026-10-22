#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Render only synthetic TMR calibration states using the software renderer."""
import os
os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                  QT_QUICK_CONTROLS_STYLE='Basic')
import math
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from PySide6.QtCore import QObject,QMetaObject,QCoreApplication,QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem,QQuickWindow
from PySide6.QtTest import QTest
from main import create_engine
from stick_calibration import Sample,SECTORS


def main():
    app=QGuiApplication([]);app.setQuitOnLastWindowClosed(False)
    dest=ROOT/'build/control-center-calibration'
    dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        engine=create_engine(Path(temp)/'prefs.ini',calibration_preview=True)
        window=engine.rootObjects()[0];model=engine.center_model
        bridge=model.stickCalibration;session=bridge.session
        now=[100.0];session.clock=lambda:now[0]
        window.resize(940,1000)
        dialog=window.findChild(QObject,'calibrationDialog')

        def feed(left=(0.,0.),right=(0.,0.),done=0):
            now[0]+=0.1
            session.feed(session.key,Sample(session.last_sequence+1,now[0],left,right,3,done))
            bridge.changed.emit()

        def save(name):
            QTest.qWait(80)
            assert window.grabWindow().save(str(dest/name))

        for language in ('de','en'):
            model.setLanguage(language)
            assert bridge.open();bridge.timer.stop()
            QMetaObject.invokeMethod(dialog,'open');QTest.qWait(30)
            bridge.start()
            for _ in range(7):now[0]+=.5;bridge.advance()
            bridge.timer.stop()
            for n in range(18):
                a=(n+.5)*math.tau/SECTORS
                b=(n/2+.5)*math.tau/SECTORS
                feed((.95*math.cos(a),.95*math.sin(a)),(.95*math.cos(b),.95*math.sin(b)))
            save('calibration-measuring-'+language+'.png')
            feed(done=3)
            save('calibration-ready-'+language+'.png')
            bridge.disconnect()
            save('calibration-lost-'+language+'.png')
            if language=='de':
                window.resize(560,480)
                save('calibration-small-de.png')
                window.resize(940,1000)
            QMetaObject.invokeMethod(dialog,'close');QTest.qWait(30)
        window.close()
        engine.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    print(dest)
    return 0


if __name__=='__main__':raise SystemExit(main())
