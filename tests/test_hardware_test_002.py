#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Device-free coordinator tests: virtual clock, synthetic metadata/client/events."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hw002", ROOT / "tools/native/hardware_test_002.py")
hw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hw)
PLAN = json.loads((ROOT / "docs/HARDWARE_TEST_002_PHASES.json").read_text())
COMPARISON = json.loads((ROOT / "docs/native-motor-comparison-plan.json").read_text())
TARGET = {"port": "8-6", "busnum": "8", "devnum": "123", "devpath": "6"}


def metadata(driver="xpad"):
    common = {"bAlternateSetting": "0", "bInterfaceClass": "ff", "bInterfaceSubClass": "47", "bInterfaceProtocol": "d0"}
    ep = {"bmAttributes": "03", "wMaxPacketSize": "0040", "bInterval": "02"}
    return {"port": "8-6", "identity": {"idVendor": "3537", "idProduct": "109c", "busnum": "8", "devnum": "123", "devpath": "6", "bConfigurationValue": "1"},
            "industrialio_already_loaded": True, "gs_native_loaded": True,
            "interfaces": {"8-6:1.0": {**common, "bInterfaceNumber": "00", "driver": driver,
                "endpoints": {"ep_02": {**ep, "bEndpointAddress": "02"}, "ep_82": {**ep, "bEndpointAddress": "82"}}},
                "8-6:1.1": {**common, "bInterfaceNumber": "01", "driver": None, "endpoints": {}}}}


class Fake:
    """All time/USB ownership/client data are artificial; no real backend calls."""
    def __init__(self, fault=None):
        self.t = self.t0 = 1000.0
        self.state = metadata()
        self.fault = fault
        self.commands, self.records, self.changes, self.queue = [], [], [], []
        self.cues = []
        self.finished = 0
        self.launched = False

    def now(self):
        return self.t

    def wait(self, seconds):
        self.t += seconds
        if self.fault == "late" and 1029.99 < self.t < 1030.01:
            self.t += .6

    def snapshot(self):
        return copy.deepcopy(self.state)

    def assert_released(self):
        if self.fault == "held":
            raise hw.Halt("Synthetic open USB handle")

    def change(self, driver, action):
        self.changes.append((driver, action))
        self.state["interfaces"]["8-6:1.0"]["driver"] = None if action == "unbind" else driver
        if self.fault == "identity-after-unbind" and action == "unbind":
            self.state["identity"]["idProduct"] = "100a"
        if self.fault == "slow-unbind" and action == "unbind":
            self.t += 2.1

    def start_client(self):
        self.launched = True
        if self.fault == "no-start":
            return
        self.queue = [{"type": "start_call", "timestamp_ns": int(self.t * 1e9)}, {"type": "started"}]
        self.t0 = self.t

    def send(self, command):
        self.commands.append((self.t - self.t0, command))
        kind = command.split()[0]
        if (self.fault == "pulse-ack" and kind == "pulse") or (self.fault == "stop-ack" and kind == "stop"):
            return
        if kind == "info":
            count = int((self.t - self.t0) * 100) + 1
            self.queue.append({"type": "info", "pid": 0x109c, "state": 1, "error": 0,
                "output": 1, "session": 1, "pad": min(count, 8700) if self.fault == "pad-stalled" else count, "imu": count,
                "rejected": 0, "accel_num": 8192, "accel_den": 1})
        elif kind == "sample":
            timestamp = self.t
            if self.fault == "stale" and self.t - self.t0 > 20:
                timestamp -= 2
            if self.fault == "future":
                timestamp += 2
            self.queue.append({"type": "sample", "timestamp_ns": int(timestamp * 1e9),
                "number": int((self.t - self.t0) * 50) + 1,
                "gyro_raw": [1, -2, 3], "accel_raw": [5, 8, 8192]})
        else:
            self.queue.append({"type": kind})

    def receive(self):
        out, self.queue = self.queue, []
        if self.fault == "generated-during-read":
            self.t += .0001
            for item in out:
                if item["type"] in ("sample", "start_call"):
                    item["timestamp_ns"] = int(self.t * 1e9)
        if self.fault == "info-error":
            for item in out:
                if item["type"] == "info":
                    item["error"] = -5
        return out

    def record(self, kind, data):
        self.records.append((kind, data))

    def setup_input(self):
        pass

    def cue(self, kind, name):
        self.cues.append((self.t - self.t0, kind, name))

    def check(self):
        if self.fault == "interrupt" and self.t - self.t0 > 50:
            raise KeyboardInterrupt()
        if self.fault == "disconnect" and self.t - self.t0 > 50:
            raise hw.Halt("Synthetic disconnect")

    def exited(self):
        return self.fault == "early-exit" and self.t - self.t0 > 50

    def finish(self):
        self.finished += 1
        return self.fault != "final-stop"


class ComparisonFake(Fake):
    """Recorder and human movement are synthetic, including completely quiet pauses."""
    def __init__(self, fault=None, acknowledgement_delay=.02):
        super().__init__(fault)
        self.deliveries, self.capture_checks = [], []
        self.acknowledgement_delay = acknowledgement_delay
        self.sent_stops = 0

    def capture_check(self, required_remaining_seconds, stage):
        self.capture_checks.append((self.t, required_remaining_seconds, stage))
        if self.fault in ("capture-not-ready", "capture-budget"):
            raise RuntimeError("Synthetic recorder ready/budget failure")
        if self.fault == "capture-before-bind" and stage == "before-bind":
            raise RuntimeError("Synthetic recorder died before bind")
        if self.fault == "capture-before-start" and stage == "before-start":
            raise RuntimeError("Synthetic recorder died before START")
        if self.fault == "capture-exit" and self.t - self.t0 > 60:
            raise RuntimeError("Synthetic recorder exited")
        if self.fault == "slow-capture-before-bind" and stage == "before-bind":
            self.t += 2.1
        if self.fault == "slow-capture-before-pulse" and stage == "before-pulse":
            self.t += .6
        if self.t + required_remaining_seconds > self.t0 + 450:
            raise RuntimeError("Synthetic insufficient recorder duration")

    def wait(self, seconds):
        super().wait(seconds)
        if self.fault == "late-last-motor" and 1224.99 < self.t < 1225.01:
            self.t += .6

    def send(self, command):
        before = len(self.queue)
        super().send(command)
        kind = command.split()[0]
        if kind == "stop":
            self.sent_stops += 1
        new, self.queue = self.queue[before:], self.queue[:before]
        elapsed = self.t - self.t0
        for message in new:
            if kind == "info":
                # Input only after the cue and through the bounded pulse/STOP window.
                message["pad"] = sum(int(max(0, min(elapsed - (p["at_seconds"] - 5), 6.9)) * 100)
                                     for p in COMPARISON["pulses"])
                if self.fault == "no-announced-input":
                    message["pad"] = 0
                if self.fault == "no-imu-counter-progress":
                    message["imu"] = 1
            if self.fault == "last-stop-ack" and kind == "stop" and self.sent_stops == 12:
                continue
            delay = self.acknowledgement_delay if kind in ("pulse", "stop") else 0
            self.deliveries.append((self.t + delay, message))

    def receive(self):
        due = [item for at, item in self.deliveries if at <= self.t]
        self.deliveries = [(at, item) for at, item in self.deliveries if at > self.t]
        self.queue += due
        return super().receive()


class PlanTests(unittest.TestCase):
    def test_human_ready_input(self):
        for text in ("bereit", "BEREIT", "BeReIt", "  bereit \n"):
            with self.subTest(text=text):
                self.assertTrue(hw.ready_input(text))
        for text in ("", "\n", "nein", "noch nicht bereit", "bereit\npulse left 100 400"):
            with self.subTest(text=text):
                self.assertFalse(hw.ready_input(text))

    def test_expected_halt_has_clear_message_without_traceback(self):
        stderr = io.StringIO()
        with patch.object(hw.sys, "argv", ["helper", "execute-authorized", "--manifest", "unused", "--output", "unused"]), \
                patch.object(hw.signal, "signal"), patch.object(hw.sys, "stderr", stderr), \
                patch.object(hw, "execute", side_effect=hw.Halt("Synthetic readiness refusal")):
            self.assertEqual(hw.main(), 2)
        self.assertIn("ABBRUCH: Synthetic readiness refusal", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_exact_four_pulses_and_rest_buffer(self):
        hw.validate_plan(PLAN)
        events = hw.schedule(PLAN)
        self.assertEqual([v for _, kind, v in events if kind == "command" and v.startswith("pulse")],
                         ["pulse left 100 400", "pulse right 100 400", "pulse lt 100 400", "pulse rt 100 400"])
        self.assertEqual((PLAN["phases"][1]["start"], PLAN["phases"][1]["end"]), (5, 20))
        self.assertEqual((PLAN["phases"][2]["start"], PLAN["phases"][2]["end"]), (20, 30))

    def test_modified_schedule_rejected(self):
        for mutate in (lambda p: p.update(session_seconds=121), lambda p: p.update(repeat=True),
                       lambda p: p["pulses"][0].update(percent=20),
                       lambda p: p["pulses"][1].update(motor="left"),
                       lambda p: p["phases"][2].update(end=29),
                       lambda p: p.update(usbmon_capture_included=True)):
            p = copy.deepcopy(PLAN)
            mutate(p)
            with self.subTest(mutation=mutate), self.assertRaises(hw.Halt):
                hw.validate_plan(p)

    def test_client_output_parser_keeps_raw_units(self):
        value = hw.parse_line("host_monotonic_ns=1000000000000 sample=1 gyro_raw=[-32768,0,32767] accel_raw=[0,0,8192] experiment_valid=1 accel_um_s2=[0,0,9806650]")
        self.assertEqual(value["gyro_raw"], [-32768, 0, 32767])
        self.assertNotIn("gyro_rad_s", value)
        self.assertEqual(hw.parse_line("STOP accepted; zero motor transfer confirmed.")["type"], "stop")
        self.assertEqual(hw.parse_line("START_CALL monotonic_ns=123")["timestamp_ns"], 123)
        with self.assertRaises(hw.Halt):
            hw.parse_line("STOP failed but continue")


class GuardTests(unittest.TestCase):
    def test_expected_109c_has_no_usbhid_on_interface_one(self):
        hw.guard(metadata(), TARGET, "xpad")

    def test_wrong_states_rejected(self):
        mutations = [lambda s: s["identity"].update(idProduct="100a"),
                     lambda s: s["identity"].update(devnum="124"),
                     lambda s: s.update(port="8-7"),
                     lambda s: s.update(industrialio_already_loaded=False),
                     lambda s: s.update(gs_native_loaded=False),
                     lambda s: s["interfaces"]["8-6:1.1"].update(driver="usbhid"),
                     lambda s: s["interfaces"]["8-6:1.0"].update(driver="usbfs"),
                     lambda s: s["interfaces"]["8-6:1.0"]["endpoints"]["ep_82"].update(wMaxPacketSize="0020")]
        for mutate in mutations:
            state = metadata()
            mutate(state)
            with self.subTest(mutation=mutate), self.assertRaises(hw.Halt):
                hw.guard(state, TARGET, "xpad")

    def test_one_handover_only(self):
        fake = Fake()
        hw.handover(fake, TARGET)
        self.assertEqual(fake.changes, [("xpad", "unbind"), ("gs_native", "bind")])
        self.assertTrue(fake.launched)

    def test_failed_handover_does_not_retry_or_restore(self):
        for fault, count in (("held", 0), ("identity-after-unbind", 1), ("slow-unbind", 1)):
            fake = Fake(fault)
            with self.subTest(fault=fault), self.assertRaises(hw.Halt):
                hw.handover(fake, TARGET)
            self.assertEqual(len(fake.changes), count)
            self.assertFalse(fake.launched)


class SessionTests(unittest.TestCase):
    def test_full_120_seconds_on_virtual_clock(self):
        fake = Fake()
        fake.start_client()
        result = hw.run_session(fake, PLAN)
        self.assertTrue(result["passed_transport_run"])
        self.assertFalse(result["motor_perception_confirmed"])
        self.assertFalse(result["xpad_restored"])
        self.assertFalse(result["full_imu_stream"])
        pulses = [(t, c) for t, c in fake.commands if c.startswith("pulse")]
        self.assertEqual(len(pulses), 4)
        for actual, expected in zip(pulses, PLAN["pulses"]):
            self.assertAlmostEqual(actual[0], expected["at_seconds"], delta=.03)
        self.assertEqual(sum(c == "stop" for _, c in fake.commands), 4)
        self.assertGreater(sum(c == "sample" for _, c in fake.commands), 4000)
        self.assertEqual(fake.finished, 1)
        self.assertGreaterEqual(fake.now() - fake.t0, 120)

    def test_all_failure_paths_finish_without_more_pulses(self):
        faults = {"stale": "Stale/future", "future": "Stale/future", "info-error": "runtime/identity", "late": "Late phase",
                  "disconnect": "Synthetic disconnect", "early-exit": "exited early", "pulse-ack": "acknowledgement timed out",
                  "stop-ack": "Late phase|acknowledgement timed out", "no-start": "START acknowledgement", "final-stop": "Final zero",
                  "pad-stalled": "No recent gamepad changes"}
        for fault, reason in faults.items():
            fake = Fake(fault)
            fake.start_client()
            with self.subTest(fault=fault), self.assertRaisesRegex(hw.Halt, reason):
                hw.run_session(fake, PLAN)
            self.assertEqual(fake.finished, 1)
            pulses = [c for _, c in fake.commands if c.startswith("pulse")]
            self.assertLessEqual(len(pulses), 1 if fault in ("pulse-ack", "stop-ack") else 4 if fault == "final-stop" else 0)
            self.assertEqual(fake.changes, [])

    def test_keyboard_interrupt_performs_end(self):
        fake = Fake("interrupt")
        fake.start_client()
        with self.assertRaises(KeyboardInterrupt):
            hw.run_session(fake, PLAN)
        self.assertEqual(fake.finished, 1)

    def test_syn_dropped_is_terminal(self):
        live = object.__new__(hw.Live)
        live.next_guard, live.event_count = 2000, 0
        live.now = lambda: 1000
        live.record = lambda *args: None
        live.check_journal = lambda: None
        live.input = types.SimpleNamespace(fd=42, read=lambda: [types.SimpleNamespace(sec=0, usec=0, type=0, code=3, value=0)])
        with patch.object(hw.select, "select", return_value=([42], [], [])), self.assertRaises(hw.Halt):
            live.check()

    def test_simulation_cannot_use_real_open_subprocess_or_sleep(self):
        fake = Fake()
        fake.start_client()
        with patch.object(hw.os, "open", side_effect=AssertionError("real open")), \
                patch.object(hw.subprocess, "Popen", side_effect=AssertionError("real subprocess")), \
                patch.object(hw.time, "sleep", side_effect=AssertionError("real wait")), \
                patch.object(hw, "Live", side_effect=AssertionError("real backend")):
            hw.run_session(fake, PLAN)

    def test_timestamps_created_during_receive_are_not_future(self):
        fake = Fake("generated-during-read")
        fake.start_client()
        self.assertTrue(hw.run_session(fake, PLAN)["passed_transport_run"])


class ComparisonTests(unittest.TestCase):
    def test_exact_plan_and_changed_variants_rejected(self):
        hw.validate_plan(COMPARISON)
        events = hw.schedule(COMPARISON)
        expected = [45, 51, 57, 105, 111, 117, 165, 171, 177, 225, 231, 237]
        self.assertEqual([at for at, kind, value in events if kind == "command" and value.startswith("pulse")], expected)
        self.assertEqual([at for at, kind, _ in events if kind == "input_prepare"], [t - 5 for t in expected])
        self.assertEqual(len([x for x in events if x[1] == "command" and x[2] == "stop"]), 12)
        for mutate in (lambda p: p.update(session_seconds=301), lambda p: p.update(repeat=True),
                       lambda p: p.update(usbmon_capture_included=False),
                       lambda p: p.update(minimum_pause_seconds_after_stop_ack=4),
                       lambda p: p.update(explicit_stop_seconds_after_pulse_ack=.6),
                       lambda p: p["pulses"][0].update(duration_ms=1001),
                       lambda p: p["pulses"][1].update(at_seconds=50),
                       lambda p: p["pulses"][-1].update(motor="lt"),
                       lambda p: p["phases"][2].update(end=89),
                       lambda p: p.update(variant="unknown")):
            plan = copy.deepcopy(COMPARISON)
            mutate(plan)
            with self.subTest(mutation=mutate), self.assertRaises(hw.Halt):
                hw.validate_plan(plan)

    def test_full_300_seconds_with_quiet_pauses_and_twelve_confirmed_stops(self):
        fake = ComparisonFake()
        fake.start_client()
        result = hw.run_session(fake, COMPARISON)
        self.assertTrue(result["passed_transport_run"])
        self.assertEqual((result["pulses"], result["pulse_acknowledgements"], result["stop_acknowledgements"]), (12, 12, 12))
        self.assertFalse(result["motor_perception_confirmed"])
        pulse_commands = [(t, c) for t, c in fake.commands if c.startswith("pulse")]
        self.assertEqual([c for _, c in pulse_commands], [f"pulse {p['motor']} 100 1000" for p in COMPARISON["pulses"]])
        stops = [t for t, c in fake.commands if c == "stop"]
        for i, ((at, _), stop, planned) in enumerate(zip(pulse_commands, stops, COMPARISON["pulses"])):
            self.assertGreaterEqual(at, planned["at_seconds"])
            self.assertLessEqual(at - planned["at_seconds"], .5)
            self.assertGreaterEqual(stop - at, 1 + fake.acknowledgement_delay - 1e-8)
            if i:
                self.assertGreaterEqual(at - stops[i - 1], 5 + fake.acknowledgement_delay - 1e-8)
        feedback = [t for t, kind, _ in fake.cues if kind == "feedback"]
        for i in range(1, 12):
            self.assertGreaterEqual(pulse_commands[i][0] - feedback[i - 1], 5 - 1e-8)
        self.assertEqual(len(feedback), 12)
        self.assertEqual(sum(kind == "pulse_data_progress" for kind, _ in fake.records), 12)
        infos = [data for kind, data in fake.records if kind == "info"]
        self.assertTrue(any(a["pad"] == b["pad"] for a, b in zip(infos, infos[1:])))
        self.assertGreaterEqual(fake.now() - fake.t0, 300)
        self.assertEqual(fake.finished, 1)
        self.assertGreater(len(fake.capture_checks), 1000)
        self.assertTrue(all(required >= 30 for _, required, _ in fake.capture_checks))

    def test_capture_gates_prevent_unapproved_handover_progress(self):
        for fault, count in (("capture-not-ready", 0), ("capture-budget", 0),
                             ("capture-before-bind", 1), ("slow-capture-before-bind", 1),
                             ("capture-before-start", 2)):
            fake = ComparisonFake(fault)
            with self.subTest(fault=fault), self.assertRaises(hw.Halt):
                hw.handover(fake, TARGET, COMPARISON)
            self.assertEqual(len(fake.changes), count)
            self.assertFalse(fake.launched)

    def test_successful_handover_checks_recorder_before_each_action(self):
        fake = ComparisonFake()
        hw.handover(fake, TARGET, COMPARISON)
        self.assertEqual([stage for _, _, stage in fake.capture_checks], ["before-unbind", "before-bind", "before-start"])
        self.assertEqual(fake.changes, [("xpad", "unbind"), ("gs_native", "bind")])
        self.assertTrue(fake.launched)

    def test_missing_recorder_interface_fails_closed(self):
        fake = Fake()
        with self.assertRaisesRegex(hw.Halt, "Recorder guard failed"):
            hw.handover(fake, TARGET, COMPARISON)
        self.assertEqual(fake.changes, [])
        self.assertFalse(fake.launched)

    def test_comparison_failures_end_without_catchup_or_retry(self):
        faults = {"capture-exit": ("Recorder guard failed", 3),
                  "slow-capture-before-pulse": ("Late motor", 0),
                  "no-announced-input": ("No recent gamepad", 0),
                  "no-imu-counter-progress": ("did not advance during", 1),
                  "stop-ack": ("acknowledgement timed out", 1),
                  "last-stop-ack": ("acknowledgement timed out", 12),
                  "pulse-ack": ("Late phase|acknowledgement timed out", 1),
                  "late-last-motor": ("Late phase", 9),
                  "stale": ("Stale/future", 0),
                  "info-error": ("runtime/identity", 0),
                  "final-stop": ("Final zero", 12)}
        for fault, (message, maximum_pulses) in faults.items():
            fake = ComparisonFake(fault)
            fake.start_client()
            with self.subTest(fault=fault), self.assertRaisesRegex(hw.Halt, message):
                hw.run_session(fake, COMPARISON)
            self.assertEqual(fake.finished, 1)
            self.assertLessEqual(sum(c.startswith("pulse") for _, c in fake.commands), maximum_pulses)
            self.assertEqual(fake.changes, [])

    def test_large_ack_delays_never_compress_pause(self):
        fake = ComparisonFake(acknowledgement_delay=.20)
        fake.start_client()
        with self.assertRaisesRegex(hw.Halt, "Late phase"):
            hw.run_session(fake, COMPARISON)
        pulse_commands = [t for t, c in fake.commands if c.startswith("pulse")]
        feedback = [t for t, kind, _ in fake.cues if kind == "feedback"]
        self.assertLess(len(pulse_commands), 12)
        for i in range(1, len(pulse_commands)):
            self.assertGreaterEqual(pulse_commands[i] - feedback[i - 1], 5 - 1e-8)
        self.assertEqual(fake.finished, 1)

    def test_offline_variant_never_constructs_live_backend(self):
        output = io.StringIO()
        with patch.object(hw.sys, "argv", ["helper", "show-plan", "--variant", hw.COMPARISON_VARIANT]), \
                patch.object(hw.sys, "stdout", output), \
                patch.object(hw, "Live", side_effect=AssertionError("real backend")), \
                patch.object(hw.os, "open", side_effect=AssertionError("device open")), \
                patch.object(hw.subprocess, "Popen", side_effect=AssertionError("subprocess")):
            self.assertEqual(hw.main(), 0)
        self.assertFalse(json.loads(output.getvalue())["hardware_access"])
        self.assertEqual(json.loads(output.getvalue())["session_seconds"], 300)

    def test_comparison_simulation_has_no_system_access(self):
        fake = ComparisonFake()
        fake.start_client()
        with patch.object(hw.os, "open", side_effect=AssertionError("real open")), \
                patch.object(hw.subprocess, "Popen", side_effect=AssertionError("real subprocess")), \
                patch.object(hw.time, "sleep", side_effect=AssertionError("real wait")), \
                patch.object(hw, "Live", side_effect=AssertionError("real backend")):
            self.assertTrue(hw.run_session(fake, COMPARISON)["passed_transport_run"])

    def test_execute_orders_capture_before_handover_and_finish_after_end(self):
        for fault in (None, "capture-start", "capture-before-bind", "capture-finish", "refused-readiness"):
            order, saved = [], {}
            recorder = types.SimpleNamespace()
            def start():
                order.append("capture-start")
                if fault == "capture-start":
                    raise RuntimeError("Synthetic capture startup failed")
            def check(required, stage):
                order.append("capture-check:" + stage)
                if fault == "capture-before-bind" and stage == "before-bind":
                    raise RuntimeError("Synthetic capture lost")
            def finish_capture():
                order.append("capture-finish")
                return {"passed": fault != "capture-finish"}
            recorder.start, recorder.check, recorder.finish = start, check, finish_capture
            fake = ComparisonFake()
            fake.state = metadata("usbfs")
            base_wait, base_change, base_finish = fake.wait, fake.change, fake.finish
            def wait(seconds):
                base_wait(seconds)
                if not fake.launched and fake.t >= 1015:
                    fake.state = metadata("xpad")
            def change(driver, action):
                order.append(action)
                base_change(driver, action)
            def finish_client():
                order.append("client-end")
                return base_finish()
            fake.wait, fake.change, fake.finish = wait, change, finish_client
            fake.capture_check = check
            fake.start_journal = lambda: order.append("journal-start")
            fake.check_journal = lambda: None
            fake.write_object = lambda name, value: saved.update({name: copy.deepcopy(value)})
            fake.close_logs = lambda: order.append("logs-close")
            capture_module = types.SimpleNamespace(attach=lambda manifest, output: recorder)
            output = Mock()
            output.is_dir.return_value = True
            output.is_symlink.return_value = False
            output.resolve.return_value = ROOT / "build/hardware-tests/synthetic"
            output.iterdir.return_value = iter(())
            output.stat.return_value = types.SimpleNamespace(st_mode=0o700, st_uid=1000)
            names = ("build/gsnative-ctl", "build/kernel/gs_native.ko", "docs/native-motor-comparison-plan.json",
                     "tools/native/hardware_test_002.py", "tools/native/preflight.py")
            manifest = {"scope": "native-motor-comparison-300-handover-twelve-pulses-capture-end-only",
                        "variant": hw.COMPARISON_VARIANT, "plan": "docs/native-motor-comparison-plan.json",
                        "session_seconds": 300, "journal_cursor": "synthetic=1", "target": TARGET,
                        "module_srcversion": "synthetic-module",
                        "sha256": {name: hw.hashlib.sha256(b"synthetic").hexdigest() for name in names}}
            manifest_path = types.SimpleNamespace(read_text=lambda: json.dumps(manifest))
            params = {"test_interface": "8-6:1.0", "test_pid": str(0x109c), "enable_output": "Y",
                      "session_ms": "315000", "accel_counts_per_g_num": "8192", "accel_counts_per_g_den": "1",
                      "srcversion": "synthetic-module"}
            def read_text(path):
                if str(path).startswith("/sys/module/gs_native/"):
                    return params[path.name]
                raise AssertionError("Unexpected filesystem read: " + str(path))
            input_stream = types.SimpleNamespace(isatty=lambda: True,
                readline=lambda: "nein\n" if fault == "refused-readiness" else "bereit\n")
            out = Mock()
            out.isatty.return_value = True
            held = {"deadband": [42], "usb_handles": [{"pid": 42}], "unreadable": []}
            released = {"deadband": [], "usb_handles": [], "unreadable": []}
            with self.subTest(fault=fault), patch.object(hw.os, "geteuid", return_value=0), \
                    patch.dict(hw.os.environ, {"SUDO_UID": "1000"}), \
                    patch.object(hw.sys, "stdin", input_stream), patch.object(hw.sys, "stdout", out), \
                    patch.object(hw.Path, "read_bytes", return_value=b"synthetic"), \
                    patch.object(hw.Path, "read_text", read_text), patch.object(hw.Path, "is_symlink", return_value=False), \
                    patch.object(hw.select, "select", return_value=([input_stream], [], [])), \
                    patch.object(hw, "process_state", side_effect=[held, released]), \
                    patch.object(hw, "Live", return_value=fake), \
                    patch.dict(hw.sys.modules, {"native_usb_capture": capture_module}), \
                    patch.object(hw.os, "open", side_effect=AssertionError("real device open")), \
                    patch.object(hw.subprocess, "Popen", side_effect=AssertionError("real subprocess")), \
                    patch.object(hw.time, "sleep", side_effect=AssertionError("real wait")):
                if fault is None:
                    hw.execute(manifest_path, output, COMPARISON)
                else:
                    with self.assertRaises(hw.Halt):
                        hw.execute(manifest_path, output, COMPARISON)
            self.assertLess(order.index("client-end"), order.index("capture-finish"))
            self.assertLess(order.index("capture-finish"), order.index("logs-close"))
            self.assertEqual(order.count("capture-finish"), 1)
            if fault in ("capture-start", "refused-readiness"):
                self.assertEqual(fake.changes, [])
            else:
                self.assertLess(order.index("capture-start"), order.index("unbind"))
            if fault == "refused-readiness":
                self.assertNotIn("capture-start", order)
            self.assertEqual(saved["result.json"]["passed_recorded_transport_run"], fault is None)


class EvidenceTests(unittest.TestCase):
    def test_live_journal_parser_aborts_on_saved_warning(self):
        live = object.__new__(hw.Live)
        live.journal = types.SimpleNamespace(stdout=types.SimpleNamespace(fileno=lambda: 41),
            stderr=types.SimpleNamespace(fileno=lambda: 42), poll=lambda: None)
        live.journal_buffer = b""
        live.logs = {"kernel": io.StringIO()}
        warning = {"PRIORITY": "4", "MESSAGE": "Synthetic kernel warning"}
        with patch.object(hw.os, "read", side_effect=[b"", (json.dumps(warning) + "\n").encode()]), \
                self.assertRaisesRegex(hw.Halt, "New kernel warning"):
            live.check_journal()
        self.assertEqual(json.loads(live.logs["kernel"].getvalue()), warning)

    def test_kernel_warning_has_no_implicit_enoent_exception(self):
        self.assertFalse(hw.kernel_warning({"PRIORITY": "6", "MESSAGE": "input registered"}))
        for item in ({"PRIORITY": "4", "MESSAGE": "xpad: usb_submit_urb failed with -2"},
                     {"PRIORITY": "3", "MESSAGE": "USB error"}):
            self.assertTrue(hw.kernel_warning(item))
        with self.assertRaises(hw.Halt):
            hw.kernel_warning({"MESSAGE": "priority missing"})

    def test_lost_device_still_saves_final_evidence(self):
        saved, closed = {}, []
        def disappeared():
            raise SystemExit("Selected port absent; stop")
        backend = types.SimpleNamespace(snapshot=disappeared, write_object=lambda name, value: saved.update({name: value}),
                                        close_logs=lambda: closed.append(True))
        hw.save_final_evidence(backend, {"passed_transport_run": False})
        self.assertTrue(saved["after.json"]["unavailable"])
        self.assertFalse(saved["result.json"]["passed_transport_run"])
        self.assertEqual(closed, [True])

    def test_failed_summary_write_still_closes_logs(self):
        closed = []
        def full_disk(name, value):
            raise OSError("Synthetic disk full")
        backend = types.SimpleNamespace(snapshot=lambda: {}, write_object=full_disk, close_logs=lambda: closed.append(True))
        with self.assertRaisesRegex(OSError, "disk full"):
            hw.save_final_evidence(backend, {})
        self.assertEqual(closed, [True])


if __name__ == "__main__":
    unittest.main(verbosity=2)
