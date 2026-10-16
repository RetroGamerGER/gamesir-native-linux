# SPDX-License-Identifier: GPL-2.0-only
"""Virtual-clock checks of the real motor-free measurement loop; no live backend."""
import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/native"))
import hardware_test_003 as test


class Fake:
    def __init__(self, fault=None):
        self.clock = 0
        self.fault = fault
        self.messages = []
        self.commands = []
        self.records = []
        self.event_count = 0

    def now(self):
        return self.clock

    def wait(self, seconds):
        self.clock += seconds

    def start_client(self):
        if self.fault != "no-start":
            self.messages.append({"type": "started"})

    def receive(self):
        out, self.messages = self.messages, []
        return out

    def check(self):
        if self.fault == "guard" and self.clock > 3:
            raise test.Halt("synthetic state change")
        if 30 <= self.clock < 65:
            self.event_count += 1

    def exited(self):
        return self.fault == "exit" and self.clock > 3

    def setup_input(self):
        pass

    def input_snapshot(self, label):
        self.record("input_snapshot", {"label": label})

    def record(self, kind, data):
        self.records.append((kind, data))

    def send(self, command):
        assert command in ("info", "sample"), command
        self.commands.append(command)
        if self.fault == "ended" and self.clock > 3:
            self.messages.append({"type": "ended"})
        elif command == "info":
            self.messages.append({"type": "info", "pid": 0x109c, "state": 1,
                                  "error": -5 if self.fault == "status" else 0,
                                  "output": 1, "session": 1})
        elif self.fault != "no-sample":
            self.messages.append({"type": "sample", "gyro_raw": [1, 2, 3], "accel_raw": [4, 5, 6]})


class MeasurementTest(unittest.TestCase):
    def run_measurement(self, fake):
        with contextlib.redirect_stdout(io.StringIO()):
            return test.measure(fake)

    def test_success_and_human_buffers(self):
        fake = Fake()
        result = self.run_measurement(fake)
        self.assertGreaterEqual(result["measurement_seconds"], 120)
        self.assertLess(result["measurement_seconds"], 120.02)
        self.assertGreater(result["imu_snapshots"], 400)
        self.assertGreater(result["input_events"], 0)
        self.assertEqual(result["motor_pulses"], 0)
        phases = [data["offset"] for kind, data in fake.records if kind == "phase"]
        self.assertEqual(len(phases), 7)
        for actual, (expected, _) in zip(phases, test.PHASES):
            self.assertAlmostEqual(actual, expected, delta=.011)
        self.assertEqual(set(fake.commands), {"info", "sample"})
        self.assertEqual(test.PHASES[2][0] - test.PHASES[1][0], 15)
        self.assertEqual(test.PHASES[4][0] - test.PHASES[3][0], 15)

    def test_stop_conditions(self):
        for fault in ("no-start", "no-sample", "exit", "guard", "status", "ended"):
            with self.subTest(fault=fault):
                fake = Fake(fault)
                with self.assertRaises(test.Halt):
                    self.run_measurement(fake)
                self.assertLess(fake.clock, 4)


if __name__ == "__main__":
    unittest.main()
