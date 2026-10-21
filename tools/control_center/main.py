#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read-only local desktop status (default) or explicitly isolated demo."""
import argparse
import os
from pathlib import Path
import sys


def create_engine(settings_file=None, *, demo=True, collector=None, rehearsal=None, execution=None):
    from PySide6.QtCore import QLocale, QSettings, QStandardPaths, QUrl, QTimer
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow  # Register the window wrapper before QML creates it.
    from qt_bridge import CenterModel
    if settings_file is None:
        settings_file = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)) / 'preferences.ini'
    settings = QSettings(str(settings_file), QSettings.Format.IniFormat)
    model = CenterModel(settings, QLocale.system().name(), demo=demo, collector=collector,
                        rehearsal=rehearsal, execution=execution)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('appModel', model)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name('qml') / 'Main.qml')))
    # Hold adapter/preferences until after the QML engine is destroyed.
    engine.center_model = model
    engine.center_settings = settings
    if not demo:
        QTimer.singleShot(0, model.refresh)
    return engine


def main(argv=None, *, packages_directory=None):
    p = argparse.ArgumentParser(description='GameSir Control Center — read-only local status')
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--demo', action='store_true', help='use isolated demo examples, without host probes')
    modes.add_argument('--rehearse-backend', action='store_true',
                       help='exercise the real session coordinator with in-memory fixtures only')
    args = p.parse_args(argv)
    if os.geteuid() == 0:
        print('This preview runs as your desktop user. Do not start it with sudo.', file=sys.stderr)
        return 2
    os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
    os.environ.setdefault('QT_QUICK_BACKEND', 'software')
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtCore import QCoreApplication, QThreadPool, QStandardPaths
    except ImportError:
        print('The optional preview needs PySide6 / Qt 6. Nothing was installed.', file=sys.stderr)
        return 2
    QCoreApplication.setOrganizationName('GameSirNativeLinux')
    QCoreApplication.setApplicationName('ControlCenterPreview')
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationDisplayName('GameSir Native Linux · Control Center')
    rehearsal = None
    if args.rehearse_backend:
        from rehearsal import create_rehearsal
        rehearsal = create_rehearsal()
    execution = None
    if packages_directory is not None and not args.demo and not args.rehearse_backend:
        from app_packages import AppImageTransactions, UserCatalogCache
        update_cache = UserCatalogCache(Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.CacheLocation)) / 'signed-releases')
        if (Path(packages_directory).parent / 'helper-payload').exists():
            from first_run import FirstRunTransactions
            execution = FirstRunTransactions(packages_directory, update_cache=update_cache)
        else:
            execution = AppImageTransactions(packages_directory, update_cache=update_cache)
    engine = create_engine(demo=args.demo or args.rehearse_backend, rehearsal=rehearsal,
                           execution=execution)
    def finish_workers():
        # Cancel only a pre-authentication reader/download. Never interrupt a
        # helper setup, package transaction or its hooks on application exit.
        if execution is not None and execution.state in ('checking', 'checking_updates'):
            execution.cancel()
        QThreadPool.globalInstance().waitForDone()
    app.aboutToQuit.connect(finish_workers)
    if not engine.rootObjects():
        return 1
    screen = app.primaryScreen()
    if screen is not None:
        area = screen.availableGeometry()
        engine.rootObjects()[0].resize(min(940, max(560, area.width() - 64)),
                                      min(1020, max(480, area.height() - 96)))
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
