# SPDX-License-Identifier: GPL-2.0-only
"""QML offline preview adapter. All samples and connection events are synthetic."""
import math
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from stick_calibration import Calibration, Instance, Sample, SECTORS


class CalibrationPreview(QObject):
    changed = Signal()

    def __init__(self, *, enabled=False, parent=None):
        super().__init__(parent)
        self.enabled = enabled
        self.session = Calibration()
        self.timer = QTimer(self)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self.advance)
        self.sequence = self.frame = self.connection = 0

    @Property(bool, constant=True)
    def available(self):
        return self.enabled

    @Property('QVariantMap', notify=changed)
    def view(self):
        return self.session.snapshot()

    @Slot(result=bool)
    def open(self):
        if not self.enabled or self.session.snapshot()['running']:
            return False
        self.connection += 1
        key = self.session.open(Instance('offline-g7-pro', f'simulated-{self.connection}'))
        if key is None:
            return False
        self.sequence = self.frame = 0
        self.advance()  # Neutral synthetic report; no automatic Start.
        self.timer.start()
        return True

    @Slot()
    def start(self):
        if self.enabled:
            self.session.prepare()
            self.changed.emit()

    @Slot()
    def finish(self):
        if self.enabled:
            self.session.finish()
            if not self.session.snapshot()['running']:
                self.timer.stop()
            self.changed.emit()

    @Slot()
    def close(self):
        self.timer.stop()
        self.session.cancel()
        self.changed.emit()

    @Slot()
    def disconnect(self):
        if self.enabled:
            self.timer.stop()
            self.session.disconnect(self.session.key)
            self.changed.emit()

    @Slot()
    def advance(self):
        if not self.enabled or not self.session.snapshot()['running']:
            self.timer.stop()
            return
        key = self.session.key
        if self.session.last_sample_at is not None:
            self.session.tick(key)
        if not self.session.snapshot()['running']:
            self.timer.stop()
            self.changed.emit()
            return
        left = right = (0.0, 0.0)
        active = done = 0
        if self.session.phase in ('measuring', 'ready_to_finish'):
            # A deterministic three-circle demonstration for each stick.
            # Only this fixture ties its made-up done flags to the animation.
            self.frame += 1
            active = 3
            circle = SECTORS * 3
            angle = (self.frame % SECTORS + 0.5) * math.tau / SECTORS
            point = (0.95*math.cos(angle), 0.95*math.sin(angle))
            left = point if self.frame < circle else (0.0, 0.0)
            right = point if circle <= self.frame < circle*2 else (0.0, 0.0)
            done = (1 if self.frame >= circle else 0) | (2 if self.frame >= circle*2 else 0)
        self.sequence += 1
        self.session.feed(key, Sample(self.sequence, self.session.clock(), left, right, active, done))
        self.changed.emit()
