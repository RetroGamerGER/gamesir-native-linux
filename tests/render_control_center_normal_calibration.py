#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Render the normal combined UI with synthetic package/controller fixtures."""
from pathlib import Path
from test_control_center_normal_calibration_ui import NormalCalibration
from PySide6.QtTest import QTest
from status import Snapshot, Fact


def main():
    destination = Path(__file__).resolve().parents[1] / 'build/control-center-tmr-alpha2-20261022/previews'
    destination.mkdir(parents=True, exist_ok=True)
    NormalCalibration.setUpClass()
    case = NormalCalibration()
    case.setUp()
    try:
        case.model.receive(Snapshot('synthetic', 'synthetic', {
            'os': Fact('ok', 'Garuda Linux'), 'kernel': Fact('ok', 'example'),
            'architecture': Fact('ok', 'x86_64'), 'support': Fact('ok'),
            'headers': Fact('match'), 'module': Fact('loaded', '0.1.0.alpha3'),
            'gamesir-native-dkms': Fact('ok', '0.1.0.alpha3-20'),
            'receiver': Fact('present'), 'connection': Fact('unobserved')}))
        for language in ('de', 'en'):
            case.model.setLanguage(language); case.window.resize(940, 1000)
            QTest.qWait(100)
            assert case.window.grabWindow().save(str(destination / ('main-' + language + '.png')))
        case.model.setLanguage('de'); case.start()
        QTest.qWait(80)
        assert case.window.grabWindow().save(str(destination / 'calibration-de.png'))
        case.window.resize(560, 480); QTest.qWait(100)
        assert case.window.grabWindow().save(str(destination / 'calibration-small-de.png'))
    finally:
        case.tearDown()
    print(destination)


if __name__ == '__main__':
    main()
