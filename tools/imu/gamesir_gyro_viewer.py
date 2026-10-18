#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Local experimental gyro window: verified saved captures only, never live IIO."""
import argparse
import math
from pathlib import Path
import sys
import time

from gamesir_imu_diagnostic import OBSERVED_AXIS_PROFILE, PROFILES
from gyro_view_model import Clip, Playback, crosshair, rotate, rotation_degrees

try:
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
    from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                                  QLabel, QMainWindow, QMessageBox, QPushButton,
                                  QSlider, QVBoxLayout, QWidget)
except ImportError:
    raise SystemExit('Das optionale Diagnosefenster benötigt PySide6. Nichts wurde installiert.')


BG = '#101923'
PANEL = '#192635'
INK = '#e5edf5'
MUTED = '#9eb0c1'
CYAN = '#66e1cc'
AMBER = '#ffcd78'


class MotionView(QWidget):
    """Software QPainter only: no OpenGL, QtSensors, input grabbing or injection."""
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setMinimumSize(740, 340)
        self.setAccessibleName('Fadenkreuz und experimentelle relative Drehung')

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        left = QRectF(0, 0, w*.49, h)
        right = QRectF(w*.51, 0, w*.49, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(PANEL))
        for area in (left, right):
            p.drawRoundedRect(area, 14, 14)
        p.setPen(QColor(INK))
        p.setFont(QFont('Sans Serif', 12, QFont.Weight.DemiBold))
        p.drawText(QPointF(20, 31), 'Fadenkreuz')
        p.drawText(QPointF(right.x()+20, 31), 'Relative Drehung · 1× Testprofil')
        p.setFont(QFont('Sans Serif', 10))
        p.setPen(QColor(MUTED))
        p.drawText(QPointF(20, 54), 'Links / rechts drehen · Vorderkante auf / ab')
        p.drawText(QPointF(right.x()+20, 54), 'Gyro-Integration · ohne Driftkorrektur')
        center = QPointF(left.center().x(), h*.52)
        radius = min(left.width()*.36, (h-160)*.5)
        p.setPen(QPen(QColor('#34495b'), 1))
        for part in (.5, 1):
            p.drawEllipse(center, radius*part, radius*part)
        p.drawLine(QPointF(center.x()-radius, center.y()), QPointF(center.x()+radius, center.y()))
        p.drawLine(QPointF(center.x(), center.y()-radius), QPointF(center.x(), center.y()+radius))
        playback = self.owner.playback
        if playback is None:
            p.drawText(left.adjusted(20, 90, -20, -20), Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap,
                       'Aufnahme auswählen und Testprofil bestätigen.')
            p.end()
            return
        q = playback.orientation
        x, y, outside = crosshair(q, playback.gain)
        target = QPointF(center.x()+radius*x, center.y()+radius*y)
        p.setPen(QPen(QColor(AMBER if outside else CYAN), 2))
        p.drawLine(QPointF(target.x()-12, target.y()), QPointF(target.x()+12, target.y()))
        p.drawLine(QPointF(target.x(), target.y()-12), QPointF(target.x(), target.y()+12))
        p.drawEllipse(target, 5, 5)
        p.setFont(QFont('Sans Serif', 10))
        p.drawText(QPointF(20, h-39), f'Empfindlichkeit {playback.gain:.2f}× · Sichtfeld ±45° bei 1×')
        p.setPen(QColor(AMBER if outside else MUTED))
        p.drawText(QPointF(20, h-18), 'Außerhalb Sichtfeld · Marker am Rand' if outside
                   else 'Zentrieren setzt nur die Ansicht zurück.')

        origin = QPointF(right.center().x(), h*.52)
        scale = min(right.width()/5, (h-145)/2.5)

        def project(v):
            x, y, z = rotate(q, v)
            return QPointF(origin.x()+scale*(x+.30*y), origin.y()-scale*(.52*y+.85*z))

        # Original geometric outline, front edge at +Y; no manufacturer artwork.
        outline = [(-1., .65, 0), (-.75, 1., 0), (.75, 1., 0), (1., .65, 0),
                   (1.1, -.9, 0), (.65, -1.15, 0), (.35, -.45, 0),
                   (-.35, -.45, 0), (-.65, -1.15, 0), (-1.1, -.9, 0)]
        p.setPen(QPen(QColor(CYAN), 2))
        p.setBrush(QColor('#254b52'))
        p.drawPolygon(QPolygonF([project(v) for v in outline]))
        p.setPen(QPen(QColor(INK), 5))
        p.drawLine(project((-.25, .95, 0)), project((.25, .95, 0)))
        p.setPen(QColor(MUTED))
        p.drawText(project((-.2, 1.3, 0)), 'Vorne')
        for endpoint, color, label in [((.9, 0, 0), '#fa9b9b', 'X'),
                                       ((0, .9, 0), '#93d595', 'Y'),
                                       ((0, 0, .9), '#9dbaff', 'Z')]:
            p.setPen(QPen(QColor(color), 2))
            p.drawLine(origin, project(endpoint))
            p.drawText(project(tuple(v*1.15 for v in endpoint)), label)
        p.setPen(QColor(INK))
        p.drawText(QPointF(right.x()+20, h-39), f'Abstand zur Mitte: {rotation_degrees(q):.1f}° (0–180°)')
        p.setPen(QColor(MUTED))
        p.drawText(QPointF(right.x()+20, h-18), 'X rechts · Y vorne · Z aus der Tastenfläche')
        p.end()


class Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playback = None
        self.capture_path = None
        self.metadata = None
        self.last_tick = time.monotonic()
        self.setWindowTitle('GameSir G7 Pro · Gyro-Labor · Offline')
        self.resize(1080, 900)
        self.setMinimumSize(900, 880)
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(13)
        title = QLabel('GameSir G7 Pro  /  Gyro-Labor')
        title.setStyleSheet('font-size: 23px; font-weight: 600;')
        layout.addWidget(title)
        self.mode = QLabel('OFFLINE-REPLAY  ·  Keine Live-Verbindung  ·  Keine Aufnahme')
        self.mode.setStyleSheet(f'color: {CYAN}; font-weight: 600;')
        layout.addWidget(self.mode)
        self.warning = QLabel('EXPERIMENTELL · Sensorfaktor unbestätigt · Keine Kalibrierung')
        self.warning.setWordWrap(True)
        self.warning.setStyleSheet(f'background: #3c3021; color: {AMBER}; padding: 10px; border-radius: 7px;')
        layout.addWidget(self.warning)
        row = QHBoxLayout()
        self.open_button = QPushButton('Gespeicherte Aufnahme öffnen…')
        self.open_button.clicked.connect(self.choose_capture)
        row.addWidget(self.open_button)
        self.profile_box = QComboBox()
        self.profile_box.addItem('Testfaktor ausdrücklich wählen…', None)
        for profile, factor in PROFILES.items():
            self.profile_box.addItem(f'±{profile} °/s — {float(factor):g} °/s pro Rohwert (Annahme)', profile)
        self.profile_box.currentIndexChanged.connect(self.profile_changed)
        row.addWidget(self.profile_box, 1)
        layout.addLayout(row)
        self.source = QLabel('Keine Aufnahme geladen. Es werden ausschließlich gespeicherte Dateien gelesen.')
        self.source.setWordWrap(True)
        self.source.setTextFormat(Qt.TextFormat.PlainText)
        self.source.setStyleSheet(f'color: {MUTED};')
        layout.addWidget(self.source)
        self.view = MotionView(self)
        layout.addWidget(self.view, 1)
        self.values = QLabel('G0 / G1 / G2: —     A0 / A1 / A2: —')
        self.values.setMinimumHeight(64)
        self.values.setWordWrap(True)
        self.values.setStyleSheet('font-family: monospace;')
        layout.addWidget(self.values)
        self.position_label = QLabel('Pausiert')
        layout.addWidget(self.position_label)
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 10000)
        self.timeline.setAccessibleName('Wiedergabeposition')
        self.timeline.sliderPressed.connect(self.pause)
        self.timeline.valueChanged.connect(self.seek)
        layout.addWidget(self.timeline)
        controls = QHBoxLayout()
        self.play_button = QPushButton('Abspielen')
        self.play_button.clicked.connect(self.toggle_play)
        self.restart_button = QPushButton('Zum Anfang')
        self.restart_button.clicked.connect(self.restart)
        self.center_button = QPushButton('Ansicht zentrieren')
        self.center_button.clicked.connect(self.center)
        for b in (self.play_button, self.restart_button, self.center_button):
            controls.addWidget(b)
        controls.addStretch()
        controls.addWidget(QLabel('Wiedergabe'))
        self.speed_box = QComboBox()
        for speed in (.5, 1., 2., 4.):
            self.speed_box.addItem(f'{speed:g}×', speed)
        self.speed_box.setCurrentIndex(1)
        self.speed_box.currentIndexChanged.connect(self.speed_changed)
        controls.addWidget(self.speed_box)
        layout.addLayout(controls)
        sensitivity = QHBoxLayout()
        self.gain_label = QLabel('Fadenkreuz-Empfindlichkeit  1.00×')
        self.gain_label.setMinimumWidth(290)
        sensitivity.addWidget(self.gain_label)
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(25, 400)
        self.gain_slider.setValue(100)
        self.gain_slider.setAccessibleName('Fadenkreuz-Empfindlichkeit')
        self.gain_slider.valueChanged.connect(self.gain_changed)
        sensitivity.addWidget(self.gain_slider)
        layout.addLayout(sensitivity)
        footer = QLabel('Vollständige Aufnahme inklusive Rückbewegung. Host-Zeitstempel; keine Sensorzeit.\n'
                        'Relative Orientierung kann driften. Kein automatischer Bias-Abzug; Beschleunigung bleibt in Rohachsen.')
        footer.setWordWrap(True)
        footer.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
        layout.addWidget(footer)
        self.setCentralWidget(main)
        self.setStyleSheet(f'QMainWindow, QWidget {{background: {BG}; color: {INK}; font-size: 13px;}}'
                          'QPushButton, QComboBox {background: #273b4e; padding: 8px; border: 1px solid #405770; border-radius: 5px;}'
                          'QPushButton:disabled, QComboBox:disabled {color: #718295;}'
                          f'QSlider::groove:horizontal {{height: 5px; background: #34495b;}}'
                          f'QSlider::handle:horizontal {{width: 15px; margin: -5px 0; background: {CYAN}; border-radius: 6px;}}')
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.refresh()

    def load_capture(self, path, profile):
        # Drop the old clip first: a failed replacement must not leave a stale
        # animation labelled as the new capture. Loader performs no live reads.
        self.playback = self.metadata = self.capture_path = None
        self.refresh()
        clip, metadata = Clip.load(path, profile=profile, axis_profile=OBSERVED_AXIS_PROFILE)
        self.capture_path, self.metadata = Path(path), metadata
        self.playback = Playback(clip)
        self.playback.gain = self.gain_slider.value()/100
        self.playback.speed = self.speed_box.currentData()
        self.profile_box.blockSignals(True)
        self.profile_box.setCurrentIndex(self.profile_box.findData(profile))
        self.profile_box.blockSignals(False)
        self.warning.setText(f'EXPERIMENTELL · {float(PROFILES[profile]):g} °/s pro Rohwert — UNBESTÄTIGT · Keine Kalibrierung')
        self.source.setText(f'{self.capture_path.parent.name} / {self.capture_path.name}  ·  '
                            f'{len(clip.frames):,} Scans  ·  SHA256 geprüft  ·  '
                            f'Δt median/max {clip.median_dt_ms:.2f}/{clip.max_dt_ms:.2f} ms  ·  '
                            f'{clip.wide_intervals} Intervalle >2× Median (kein Beweis für Paketverlust)')
        self.refresh()

    def try_load(self, path, profile):
        try:
            self.load_capture(path, profile)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.source.setText('Aufnahme abgelehnt. Keine Wiedergabe, kein Gerätezugriff.')
            QMessageBox.warning(self, 'Aufnahme nicht freigegeben', str(error))

    def choose_capture(self):
        self.pause()
        profile = self.profile_box.currentData()
        if profile is None:
            QMessageBox.information(self, 'Testfaktor auswählen', 'Bitte zuerst einen ausdrücklich experimentellen Testfaktor wählen.')
            return
        path = QFileDialog.getExistingDirectory(self, 'Privaten capture-Ordner auswählen', '',
                                               QFileDialog.Option.DontUseNativeDialog)
        if path:
            self.try_load(path, profile)

    def profile_changed(self):
        self.pause()
        if self.capture_path and self.profile_box.currentData() is not None:
            self.try_load(self.capture_path, self.profile_box.currentData())
        elif self.profile_box.currentData() is None:
            self.playback = self.metadata = self.capture_path = None
            self.source.setText('Kein Testfaktor ausgewählt. Wiedergabe verworfen.')
            self.refresh()

    def toggle_play(self):
        if self.playback:
            if self.playback.position >= self.playback.clip.duration:
                self.playback.restart()
            self.playback.playing = not self.playback.playing
            self.last_tick = time.monotonic()
            self.refresh()

    def pause(self):
        if self.playback:
            self.playback.playing = False
            self.refresh()

    def restart(self):
        if self.playback:
            self.playback.restart()
            self.refresh()

    def center(self):
        if self.playback:
            self.playback.center()
            self.refresh()

    def seek(self, value):
        if self.playback:
            self.playback.seek(value/10000*self.playback.clip.duration)
            self.last_tick = time.monotonic()
            self.refresh()

    def speed_changed(self):
        if self.playback:
            self.playback.speed = self.speed_box.currentData()
            self.last_tick = time.monotonic()

    def gain_changed(self, value):
        self.gain_label.setText(f'Fadenkreuz-Empfindlichkeit  {value/100:.2f}×')
        if self.playback:
            self.playback.gain = value/100
            self.refresh()

    def tick(self):
        now = time.monotonic()
        if self.playback and self.playback.playing:
            self.playback.advance(max(0., now-self.last_tick))
            self.refresh()
        self.last_tick = now

    def refresh(self):
        active = self.playback is not None
        for control in (self.play_button, self.restart_button, self.center_button, self.timeline,
                        self.gain_slider, self.speed_box):
            control.setEnabled(active)
        if active:
            b = self.playback
            f = b.frame
            status = 'Wiedergabe' if b.playing else ('Replay beendet' if b.position >= b.clip.duration else 'Pausiert')
            self.position_label.setText(f'{status}  ·  {b.position:.2f} / {b.clip.duration:.2f} s  ·  Scan {f.number}')
            self.play_button.setText('Pause' if b.playing else ('Erneut abspielen' if b.position >= b.clip.duration else 'Abspielen'))
            self.timeline.blockSignals(True)
            self.timeline.setValue(round(b.position/b.clip.duration*10000))
            self.timeline.blockSignals(False)
            x, y, z = f.body_dps
            rx, ry, rz = f.body_rad_s
            self.values.setText(f'Vorne hoch: {x:+8.2f} °/s   Links drehen: {z:+8.2f} °/s   Links kippen: {-y:+8.2f} °/s\n'
                                f'Gehäuse X/Y/Z: {rx:+.4f} / {ry:+.4f} / {rz:+.4f} rad/s (Testwerte)\n'
                                f'Roh G0/G1/G2: {f.gyro_raw}   Roh A0/A1/A2: {f.accel_raw}')
        else:
            self.values.setText('Keine Sensordaten geladen.')
            self.position_label.setText('Pausiert · keine Quelle')
            self.play_button.setText('Abspielen')
        self.view.update()

    def closeEvent(self, event):
        self.timer.stop()
        self.pause()
        event.accept()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture-dir', type=Path, help='verified saved capture directory; no live path')
    p.add_argument('--experimental', action='store_true')
    p.add_argument('--profile', type=int, choices=tuple(PROFILES))
    p.add_argument('--axis-profile', choices=[OBSERVED_AXIS_PROFILE])
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.capture_dir and not (args.experimental and args.profile and args.axis_profile):
        p.error('capture replay requires --experimental, --profile and --axis-profile')
    app = QApplication([sys.argv[0]])
    window = Viewer()
    if args.capture_dir:
        try:
            window.load_capture(args.capture_dir, args.profile)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f'Offline replay rejected: {error}', file=sys.stderr)
            return 1
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
