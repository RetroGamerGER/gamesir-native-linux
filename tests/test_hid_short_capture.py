# SPDX-License-Identifier: GPL-2.0-only
"""File-only regressions for the separately authorized 90-second HID test.

All runtime paths use the existing virtual clock and synthetic recorder. These
tests neither collect host metadata nor open USB, HID, input or control nodes.
"""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import test_hid_sidechannel_capture as helpers

capture = helpers.capture
passive = helpers.passive


class ShortManifestTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name in ("Popen", "run"):
            self.stack.enter_context(patch.object(capture.subprocess, name,
                side_effect=AssertionError("No live metadata or capture process")))

    def manifest(self):
        return passive.make_manifest(helpers.target(), helpers.metadata(),
                                     scope=capture.PASSIVE_SHORT_SCOPE)

    def test_explicit_short_scope_has_its_own_exact_budget_and_source_pins(self):
        value = passive.validate_manifest(self.manifest())
        self.assertEqual(value["scope"], "passive-hid-100a-90")
        self.assertEqual(value["target"], helpers.target())
        conf = value["usb_capture"]
        self.assertEqual((conf["duration_seconds"], conf["outer_timeout_seconds"]), (90, 120))
        expected = {"tools/native/native_usb_capture.py", "tools/native/hid_sidechannel_capture.py"}
        expected.update("tools/native/usb_capture/" + name for name in capture.ASSET_NAMES)
        self.assertEqual(set(value["sha256"]), expected)
        for name, pinned in value["sha256"].items():
            self.assertEqual(pinned, capture.digest(helpers.ROOT / name))

    def test_existing_manifest_and_default_keep_the_full_300_second_plan(self):
        value = passive.make_manifest(helpers.target(), helpers.metadata())
        original = copy.deepcopy(value)
        checked = passive.validate_manifest(value)
        self.assertEqual(value, original)
        self.assertEqual(checked["scope"], capture.PASSIVE_SCOPE)
        self.assertEqual(checked["usb_capture"]["duration_seconds"], 300)
        self.assertEqual(checked["usb_capture"]["outer_timeout_seconds"], 330)
        self.assertEqual(passive.phase_plan()[-1]["end"], 300)

    def test_scope_and_duration_cannot_be_silently_exchanged(self):
        for scope, duration, outer in (
                (capture.PASSIVE_SHORT_SCOPE, 300, 330),
                (capture.PASSIVE_SHORT_SCOPE, 90, 330),
                (capture.PASSIVE_SHORT_SCOPE, 300, 120),
                (capture.PASSIVE_SCOPE, 90, 120),
                (capture.PASSIVE_SCOPE, 300, 120),
                (capture.PASSIVE_SHORT_SCOPE, True, 120),
                (capture.PASSIVE_SHORT_SCOPE, 90, 120.0)):
            with self.subTest(scope=scope, duration=duration, outer=outer):
                value = self.manifest()
                value["scope"] = scope
                value["usb_capture"].update(duration_seconds=duration,
                                             outer_timeout_seconds=outer)
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_unknown_profiles_do_not_gain_passive_capture_authority(self):
        for scope in ("passive-hid-100a-10", "passive-hid-100a-90 ", capture.SCOPE, "", None):
            with self.subTest(scope=scope):
                with self.assertRaises(capture.CaptureHalt):
                    passive.make_manifest(helpers.target(), helpers.metadata(), scope=scope)
                value = self.manifest()
                value["scope"] = scope
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_short_profile_requires_current_wrapper_and_guard_source_hashes(self):
        for path in ("tools/native/hid_sidechannel_capture.py",
                     "tools/native/native_usb_capture.py",
                     "tools/native/usb_capture/identity-check.py",
                     "tools/native/usb_capture/guest-check.py"):
            with self.subTest(path=path):
                value = self.manifest()
                value["sha256"][path] = "0" * 64
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_short_plan_is_explicit_cli_choice_without_host_metadata(self):
        for arguments, expected in (([], 300), (["show-plan"], 300),
                                    (["show-plan", "--profile", "90"], 90),
                                    (["show-plan", "--profile", "300"], 300)):
            with self.subTest(arguments=arguments):
                stream = io.StringIO()
                with patch.object(capture, "attach", side_effect=AssertionError("No recorder")), \
                     patch.object(capture, "dumpcap_metadata", side_effect=AssertionError("No host probe")), \
                     contextlib.redirect_stdout(stream):
                    self.assertEqual(passive.main(arguments), 0)
                plan = json.loads(stream.getvalue())
                self.assertFalse(plan["hardware_access"])
                self.assertEqual(plan["duration_ceiling_seconds"], expected)
                self.assertEqual(plan["phases"][-1]["end"], expected)

    def test_short_attach_is_pure_and_preserves_no_tail_contract(self):
        value = self.manifest()
        with tempfile.TemporaryDirectory(prefix="synthetic-short-attach-") as name:
            root = Path(name)
            output = root / "build/hardware-tests/synthetic-short"
            output.mkdir(parents=True, mode=0o700)
            with patch.object(capture, "ROOT", root), \
                 patch.object(capture, "verify_sources", return_value={}):
                recorder = capture.attach(value, output)
            self.assertEqual((recorder.duration, recorder.outer_timeout, recorder.tail), (90, 120, 0))
            self.assertTrue(recorder.passive)
            self.assertFalse(recorder.directory.exists())
            self.assertFalse(recorder.finish()["passed"])
            self.assertFalse(recorder.directory.exists())


class ShortTimingTests(unittest.TestCase):
    def recorder(self, fault_at=None):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock, fault_at=fault_at)
        recorder.deadline = recorder.capture_started + 90
        return clock, recorder

    def run_plan(self, recorder, clock, messages):
        return passive.run_phases(recorder, scope=capture.PASSIVE_SHORT_SCOPE,
                                  clock=clock.now, sleep=clock.wait, emit=messages.append)

    def test_human_schedule_has_30_second_preparation_and_separate_action_cue(self):
        phases = passive.phase_plan(capture.PASSIVE_SHORT_SCOPE)
        self.assertEqual([(p["name"], p["start"], p["end"], p["buffer_seconds"]) for p in phases],
                         [("prepare", 0, 30, 0), ("rest", 30, 40, 0),
                          ("mixed", 40, 80, 10), ("final_rest", 80, 90, 0)])
        self.assertTrue(all(p["instruction"] for p in phases))
        clock, recorder = self.recorder()
        messages = []
        cues = self.run_plan(recorder, clock, messages)
        actions = [cue for cue in cues if cue["event"] == "action_cue"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["phase"], "mixed")
        self.assertAlmostEqual(actions[0]["seconds_from_capture_request"], 50, delta=.10001)
        mixed = next(cue for cue in cues if cue["phase"] == "mixed" and cue["event"] == "phase_cue")
        self.assertAlmostEqual(mixed["seconds_from_capture_request"], 40, delta=.10001)
        self.assertIn("10", mixed["instruction"])
        self.assertIn("JETZT", actions[0]["instruction"])
        final = next(cue for cue in cues if cue["event"] == "phase_cue" and cue["phase"] == "final_rest")
        self.assertAlmostEqual(final["seconds_from_capture_request"], 80, delta=.10001)
        self.assertEqual(messages, cues)

    def test_short_deadline_uses_guest_origin_and_retains_finalization_second(self):
        clock, recorder = self.recorder()
        messages = []
        self.run_plan(recorder, clock, messages)
        self.assertGreaterEqual(clock.now(), 189)
        self.assertLess(clock.now(), 189.01)
        self.assertLess(clock.now(), recorder.deadline)
        self.assertGreater(len(recorder.checks), 800)
        self.assertTrue(all(now + remaining <= 190 for now, remaining, _ in recorder.checks))
        self.assertLessEqual(max(b[0] - a[0] for a, b in
            zip(recorder.checks, recorder.checks[1:])), .100001)
        self.assertEqual(messages[-1]["event"], "capture_finish")
        self.assertEqual(recorder.actions, [])

    def test_old_300_second_recorder_is_not_implicitly_shortened(self):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock)
        with self.assertRaises(capture.CaptureHalt):
            self.run_plan(recorder, clock, [])
        self.assertEqual(clock.sleeps, [])
        self.assertEqual(recorder.actions, [])

    def test_unverified_or_late_readiness_never_emits_a_start_signal(self):
        for ready, now in ((None, 105), (131, 131), (99, 105), (106, 105)):
            with self.subTest(ready=ready, now=now):
                clock, recorder = self.recorder()
                recorder.ready = ready
                clock.stamp = now
                messages = []
                with self.assertRaises(capture.CaptureHalt):
                    self.run_plan(recorder, clock, messages)
                self.assertEqual(messages, [])
                self.assertEqual(clock.sleeps, [])

    def test_instance_guard_failure_stops_before_remaining_action_cues(self):
        clock, recorder = self.recorder(fault_at=145)
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.run_plan(recorder, clock, messages)
        self.assertLess(clock.now(), 145.11)
        self.assertFalse(any(cue["event"] == "action_cue" for cue in messages))
        self.assertEqual(recorder.actions, [])


class ShortExecutionTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name in ("Popen", "run"):
            self.stack.enter_context(patch.object(capture.subprocess, name,
                side_effect=AssertionError("No live metadata or capture process")))

    def manifest(self):
        return passive.make_manifest(helpers.target(), helpers.metadata(),
                                     scope=capture.PASSIVE_SHORT_SCOPE)

    def invoke(self, recorder, clock, *, authorized=True, messages=None):
        messages = [] if messages is None else messages
        factory = Mock(return_value=recorder)
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(capture.os, "geteuid", return_value=0), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True), \
             patch.object(passive, "persist_result", return_value={"checksum_manifest_verified": True}):
            result = passive.execute(self.manifest(), "/unused-synthetic-output", authorized=authorized,
                readiness=lambda _: " bereit ", capture_factory=factory,
                clock=clock.now, sleep=clock.wait, emit=messages.append)
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args[0]["scope"], capture.PASSIVE_SHORT_SCOPE)
        return result, messages

    def test_explicit_short_run_starts_and_finishes_exactly_once_with_short_summary(self):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock)
        recorder.deadline = 190
        result, messages = self.invoke(recorder, clock)
        self.assertEqual(recorder.actions, ["start", "finish"])
        self.assertEqual(result["scope"], capture.PASSIVE_SHORT_SCOPE)
        self.assertFalse(result["hardware_commands_sent"])
        self.assertFalse(result["drivers_changed"])
        self.assertFalse(result["automatic_retry"])
        self.assertFalse(result["calibration_performed"])
        self.assertEqual(messages[0]["event"], "verified_start")
        self.assertTrue(all(stream.closed for stream in recorder.streams))

    def test_profile_selection_never_replaces_explicit_capture_authorization(self):
        factory, readiness = Mock(), Mock()
        with self.assertRaises(capture.CaptureHalt):
            passive.execute(self.manifest(), "/unused-synthetic-output",
                            capture_factory=factory, readiness=readiness)
        factory.assert_not_called()
        readiness.assert_not_called()

    def test_short_runtime_failure_keeps_original_cause_and_aborts_owned_recorder_only(self):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock, fault_at=145)
        recorder.deadline = 190
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.invoke(recorder, clock, messages=messages)
        self.assertEqual(recorder.actions[0], "start")
        self.assertEqual(len(recorder.actions), 2)
        self.assertEqual(recorder.actions[1][0], "abort")
        self.assertIn("Synthetic identity change", recorder.actions[1][1])
        self.assertEqual(messages[-1]["event"], "stopped")
        self.assertTrue(all(stream.closed for stream in recorder.streams))


class ShortGuestContractTests(unittest.TestCase):
    def test_short_guest_budget_preserves_full_payload_pcapng_and_existing_profiles(self):
        tree = ast.parse((helpers.NATIVE / "usb_capture/guest-check.py").read_text())
        duration = next(node.value for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                and target.id == "duration" for target in node.targets))
        argv = next(node.value for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name) and target.value.id == "r"
                and isinstance(target.slice, ast.Constant) and target.slice.value == "dumpcap_argv"
                for target in node.targets))
        allowed = (ast.Expression, ast.IfExp, ast.Compare, ast.Eq, ast.Name, ast.Load,
                   ast.Constant, ast.List, ast.BinOp, ast.Add, ast.Call)
        def pure(node, values):
            expression = ast.Expression(body=node)
            for part in ast.walk(expression):
                self.assertIsInstance(part, allowed)
                if isinstance(part, ast.Call):
                    self.assertIsInstance(part.func, ast.Name)
                    self.assertEqual(part.func.id, "str")
            return eval(compile(expression, "synthetic-short-guest-expression", "eval"),
                        {"__builtins__": {}, "str": str}, values)
        for profile, expected in ((None, 450), (capture.PASSIVE_SCOPE, 300),
                                  (capture.PASSIVE_SHORT_SCOPE, 90)):
            with self.subTest(profile=profile):
                seconds = pure(duration, {"profile": profile})
                self.assertEqual(seconds, expected)
                command = pure(argv, {"duration": seconds})
                self.assertEqual(command[:7], ["/usr/bin/dumpcap", "-i", "usbmon8", "-y",
                                               "USB_LINUX_MMAPPED", "-s", "0"])
                self.assertIn("duration:" + str(expected), command)
                self.assertEqual(command[command.index("-F") + 1], "pcapng")
                self.assertEqual(command[command.index("-w") + 1], "-")
                self.assertNotIn("/dev/bus/usb", command)


if __name__ == "__main__":
    unittest.main()
