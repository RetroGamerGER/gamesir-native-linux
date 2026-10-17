# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic passive-recorder checks; no device or live metadata backend."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "tools/native"
sys.path.insert(0, str(NATIVE))
import native_usb_capture as capture
import hid_sidechannel_capture as passive


def target():
    return {"port": "8-6", "busnum": "8", "devnum": "8", "devpath": "6",
            "vid": "3537", "pid": "100a",
            "boot_id": "11111111-2222-4333-8444-555555555555",
            "sysfs_identity": {"st_dev": 11, "st_ino": 12,
                               "parent_st_dev": 11, "parent_st_ino": 13},
            "interfaces": {
                "0": {"driver": "xpad", "endpoints": [2, 130]},
                "1": {"driver": "usbhid", "endpoints": [4, 132]}}}


def metadata():
    return {"uid": 0, "gid": 150, "mode": "0o754", "sha256": "a" * 64,
            "file_capability_xattr_hex": None}


class VirtualClock:
    def __init__(self, stamp=105):
        self.stamp = stamp
        self.sleeps = []

    def now(self):
        return self.stamp

    def wait(self, seconds):
        if not 0 < seconds <= .100001:
            raise AssertionError("Unexpected unbounded wait: " + str(seconds))
        self.sleeps.append(seconds)
        self.stamp += seconds


class SyntheticRecorder:
    def __init__(self, clock, fault_at=None):
        self.clock = clock
        self.capture_started = 100
        self.ready = 104.9
        self.deadline = 400
        self.started = True
        self.result = None
        self.fault_at = fault_at
        self.checks = []
        self.actions = []
        self.streams = []

    def check(self, remaining, label):
        self.checks.append((self.clock.now(), remaining, label))
        if self.clock.now() + remaining > self.deadline:
            raise capture.CaptureHalt("Synthetic capture budget exceeded")
        if self.fault_at is not None and self.clock.now() >= self.fault_at:
            raise capture.CaptureHalt("Synthetic identity change")

    def start(self):
        self.actions.append("start")

    def finish(self):
        self.actions.append("finish")
        self.result = {"passed": True, "checksum_manifest_verified": True}
        return self.result

    def abort(self, reason):
        self.actions.append(("abort", reason))
        self.result = {"passed": False, "failure": reason}
        return self.result

    def _file(self, name):
        if name != "phase-cues.jsonl":
            raise AssertionError("Unexpected test output: " + name)
        stream = tempfile.TemporaryFile("w+b")
        self.streams.append(stream)
        return stream


class PassiveProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="synthetic-passive-profile-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.parent = self.root / "build/hardware-tests/synthetic"
        self.parent.mkdir(parents=True, mode=0o700)
        self.addCleanup(patch.stopall)
        patch.object(capture, "ROOT", self.root).start()
        patch.object(capture, "verify_sources", return_value={"synthetic": True}).start()
        patch.object(capture.subprocess, "Popen", side_effect=AssertionError("No live process")).start()
        patch.object(capture.subprocess, "run", side_effect=AssertionError("No live metadata")).start()

    def manifest(self):
        return {"scope": capture.PASSIVE_SCOPE, "target": target(), "sha256": {},
                "usb_capture": {"duration_seconds": 300, "outer_timeout_seconds": 330,
                                "dumpcap_file_metadata": metadata()}}

    def test_passive_attach_has_no_process_or_output_side_effect(self):
        obj = capture.attach(self.manifest(), self.parent)
        self.assertFalse(obj.directory.exists())
        self.assertFalse(obj.finish()["passed"])
        self.assertFalse(obj.directory.exists())

    def test_legacy_scope_keeps_450_second_contract(self):
        self.assertEqual((capture.DURATION, capture.OUTER_TIMEOUT, capture.TAIL), (450, 480, 30))
        manifest = self.manifest()
        manifest["scope"] = capture.SCOPE
        manifest["target"] = {key: value for key, value in target().items()
                              if key in ("port", "busnum", "devnum", "devpath")}
        with self.assertRaises(capture.CaptureHalt):
            capture.attach(manifest, self.parent)
        manifest["usb_capture"].update(duration_seconds=450, outer_timeout_seconds=480)
        obj = capture.attach(manifest, self.parent)
        self.assertFalse(obj.directory.exists())

    def test_passive_profile_cannot_inherit_legacy_limits(self):
        for duration, timeout in ((450, 480), (300, 480), (450, 330), (301, 330),
                                  (0, 330), (True, 330), (300, float("inf"))):
            with self.subTest(duration=duration, timeout=timeout):
                manifest = self.manifest()
                manifest["usb_capture"].update(duration_seconds=duration,
                                                outer_timeout_seconds=timeout)
                with self.assertRaises(capture.CaptureHalt):
                    capture.attach(manifest, self.parent)

    def test_passive_identity_does_not_accept_other_model_or_instance(self):
        for key, value in (("vid", "045e"), ("pid", "109c"), ("pid", "105e"),
                           ("port", "8-5"), ("busnum", "7"), ("devpath", "5"),
                           ("devnum", "0"), ("devnum", "128")):
            with self.subTest(key=key, value=value):
                manifest = self.manifest()
                manifest["target"][key] = value
                with self.assertRaises(capture.CaptureHalt):
                    capture.attach(manifest, self.parent)

    def test_private_non_symlink_new_output_is_required(self):
        self.parent.chmod(0o755)
        with self.assertRaises(capture.CaptureHalt):
            capture.attach(self.manifest(), self.parent)
        self.parent.chmod(0o700)
        (self.parent / "usb-capture").mkdir()
        marker = self.parent / "usb-capture/do-not-delete"
        marker.write_text("existing evidence")
        with self.assertRaises(capture.CaptureHalt):
            capture.attach(self.manifest(), self.parent)
        self.assertEqual(marker.read_text(), "existing evidence")

    def active(self):
        obj = capture.attach(self.manifest(), self.parent)
        obj.directory.mkdir(mode=0o700)
        obj.created_directory = obj.started = True
        obj.ready, obj.deadline = 100, 400
        obj.dumpcap_fd = 99
        obj.process, obj.observer = Mock(), Mock()
        obj.process.poll.return_value = obj.observer.poll.return_value = None
        obj.process.returncode = 0
        obj.baseline = {"identity": {"synthetic": "unchanged"}, "target": target(),
                        "capture_profile": capture.PASSIVE_SCOPE, "synthetic_host": True}
        for name in ("capture.log", "usb-udev-events.log", "udev-stderr.log"):
            (obj.directory / name).write_bytes(b"")
        (obj.directory / "original-usbmon8.pcapng").write_bytes(b"\x0a\x0d\x0d\x0asynthetic")
        return obj

    def guarded_check(self, obj, now=110):
        with patch.object(capture.time, "monotonic", return_value=now), \
             patch.object(capture.shutil, "disk_usage", return_value=SimpleNamespace(free=5*capture.GIB)), \
             patch.object(capture.select, "poll") as poll:
            poll.return_value.poll.return_value = []
            obj.check(0, "synthetic-passive-state")

    def test_periodic_identity_guard_cannot_adopt_changed_instance(self):
        obj = self.active()
        with patch.object(obj, "_metadata", return_value={"synthetic": "unchanged"}) as read:
            self.guarded_check(obj)
            read.assert_called_once()
            self.guarded_check(obj, now=110.5)
            read.assert_called_once()  # One bounded guard per second.
        with patch.object(obj, "_metadata", return_value={"synthetic": "replacement"}):
            with self.assertRaisesRegex(capture.CaptureHalt, "instance/bindings changed"):
                self.guarded_check(obj, now=112)

    def test_periodic_guard_error_is_not_ignored_or_retried(self):
        obj = self.active()
        with patch.object(obj, "_metadata", side_effect=capture.CaptureHalt("metadata unavailable")) as read:
            with self.assertRaisesRegex(capture.CaptureHalt, "metadata unavailable"):
                self.guarded_check(obj)
            read.assert_called_once()

    def test_final_identity_mismatch_preserves_original_and_cannot_pass(self):
        obj = self.active()
        obj.process.poll.return_value = obj.observer.poll.return_value = 0
        (obj.directory / "capture.log").write_text(
            'MEASUREMENT_B_RESULT_JSON {"passed":true,"dumpcap_reaped":true}\n')
        with patch.object(obj, "_metadata", side_effect=[{"synthetic_host": True},
                                                           {"synthetic": "replacement"}]), \
             patch.object(capture.os, "close"):
            result = obj.finish()
        self.assertFalse(result["passed"])
        self.assertEqual(result["post_end_tail_seconds"], 0)
        self.assertIn("target changed", result["failure"])
        self.assertTrue((obj.directory / "original-usbmon8.pcapng").exists())
        self.assertTrue((obj.directory / "identity-after.json").exists())
        self.assertNotIn("target_identity_bindings_pause_unchanged", result)
        self.assertFalse(json.loads((obj.directory / "capture-outcome.json").read_text())["passed"])


class PassiveManifestTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(capture.subprocess, "Popen",
            side_effect=AssertionError("No live process")))
        self.stack.enter_context(patch.object(capture.subprocess, "run",
            side_effect=AssertionError("No live metadata")))

    def manifest(self):
        return passive.make_manifest(target(), metadata())

    def test_manifest_generation_is_file_only_and_pins_own_code(self):
        value = self.manifest()
        checked = passive.validate_manifest(value)
        self.assertEqual(checked["scope"], capture.PASSIVE_SCOPE)
        self.assertEqual(checked["target"], target())
        conf = checked["usb_capture"]
        self.assertEqual((conf["duration_seconds"], conf["outer_timeout_seconds"]), (300, 330))
        for name in ("tools/native/hid_sidechannel_capture.py", "tools/native/native_usb_capture.py"):
            self.assertEqual(checked["sha256"][name], capture.digest(ROOT / name))

    def test_import_does_not_start_or_modify_anything(self):
        path = NATIVE / "hid_sidechannel_capture.py"
        spec = importlib.util.spec_from_file_location("synthetic_passive_import", path)
        module = importlib.util.module_from_spec(spec)
        forbidden = AssertionError("Import attempted a runtime action")
        with patch.object(capture, "attach", side_effect=forbidden), \
             patch.object(capture, "dumpcap_metadata", side_effect=forbidden), \
             patch.object(os, "open", side_effect=forbidden), \
             patch.object(Path, "mkdir", side_effect=forbidden), \
             patch.object(Path, "unlink", side_effect=forbidden):
            spec.loader.exec_module(module)
        self.assertTrue(callable(module.phase_plan))

    def test_wrong_source_hash_rejected_before_capture(self):
        value = self.manifest()
        value["sha256"]["tools/native/hid_sidechannel_capture.py"] = "0" * 64
        with self.assertRaises(capture.CaptureHalt):
            passive.validate_manifest(value)

    def test_mutated_interfaces_and_endpoint_roles_fail_closed(self):
        for interface, field, replacement in (
                ("0", "driver", "gs_native"), ("0", "driver", "usbfs"),
                ("1", "driver", None), ("1", "driver", "usbfs"),
                ("0", "endpoints", [4, 132]), ("1", "endpoints", [2, 130]),
                ("1", "endpoints", [4, 132, 133])):
            with self.subTest(interface=interface, field=field, replacement=replacement):
                value = self.manifest()
                value["target"]["interfaces"][interface][field] = replacement
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_missing_or_noninteger_instance_anchor_is_not_adopted(self):
        for key in ("st_dev", "st_ino", "parent_st_dev", "parent_st_ino"):
            for replacement in (None, False, -1, "12", 12.0):
                with self.subTest(key=key, replacement=replacement):
                    value = self.manifest()
                    value["target"]["sysfs_identity"][key] = replacement
                    with self.assertRaises(capture.CaptureHalt):
                        passive.validate_manifest(value)
        value = self.manifest()
        del value["target"]["sysfs_identity"]
        with self.assertRaises(capture.CaptureHalt):
            passive.validate_manifest(value)

    def test_boot_identity_must_be_explicit_canonical_uuid(self):
        for replacement in (None, False, "", "11111111", "../boot_id", "F" * 36):
            with self.subTest(replacement=replacement):
                value = self.manifest()
                value["target"]["boot_id"] = replacement
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_invalid_dumpcap_provenance_is_not_normalized_to_root(self):
        for key, replacement in (("uid", 1000), ("uid", False), ("gid", -1),
                                 ("sha256", "short"), ("sha256", "g" * 64)):
            with self.subTest(key=key, replacement=replacement):
                value = self.manifest()
                value["usb_capture"]["dumpcap_file_metadata"][key] = replacement
                with self.assertRaises(capture.CaptureHalt):
                    passive.validate_manifest(value)

    def test_missing_specific_authorization_never_asks_or_attaches(self):
        factory, readiness = Mock(), Mock()
        with self.assertRaises(capture.CaptureHalt):
            passive.execute(self.manifest(), "/unused-synthetic-output",
                            capture_factory=factory, readiness=readiness)
        factory.assert_not_called()
        readiness.assert_not_called()

    def test_local_readiness_is_required_before_attach_or_start(self):
        for reply in ("", "start", "yes", "ja", "not ready", "BEREIT in a moment"):
            with self.subTest(reply=reply):
                factory = Mock()
                with patch.object(capture.os, "geteuid", return_value=0), \
                     patch.object(sys.stdin, "isatty", return_value=True), \
                     patch.object(sys.stdout, "isatty", return_value=True), \
                     self.assertRaises(capture.CaptureHalt):
                    passive.execute(self.manifest(), "/unused-synthetic-output", authorized=True,
                                    capture_factory=factory, readiness=lambda _: reply)
                factory.assert_not_called()

    def test_manifest_import_never_opens_live_metadata_paths(self):
        for name in ("/dev/synthetic", "/proc/synthetic", "/sys/synthetic"):
            with self.subTest(name=name), \
                 patch.object(os, "open", side_effect=AssertionError("Must reject before open")), \
                 self.assertRaises(capture.CaptureHalt):
                passive.read_manifest(name)

    def test_manifest_import_rejects_fifo_symlink_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory(prefix="synthetic-passive-manifest-") as name:
            directory = Path(name)
            path = directory / "manifest.json"
            value = self.manifest()
            path.write_text(json.dumps(value))
            self.assertEqual(passive.read_manifest(path), value)
            link = directory / "manifest-link"
            link.symlink_to(path)
            fifo = directory / "manifest-fifo"
            os.mkfifo(fifo)
            for invalid in (link, fifo):
                with self.subTest(path=invalid), self.assertRaises(capture.CaptureHalt):
                    passive.read_manifest(invalid)
            path.write_text('{"scope":"first","scope":"second"}')
            with self.assertRaisesRegex(capture.CaptureHalt, "Duplicate"):
                passive.read_manifest(path)

    def test_manifest_import_is_bounded_before_open(self):
        with tempfile.TemporaryDirectory(prefix="synthetic-passive-large-") as name:
            path = Path(name) / "oversized.json"
            with path.open("wb") as stream:
                stream.truncate(1024 * 1024 + 1)
            with patch.object(os, "open", side_effect=AssertionError("Must reject before open")), \
                 self.assertRaises(capture.CaptureHalt):
                passive.read_manifest(path)

    def execute_synthetic(self, recorder, clock, reply=" bereit ", messages=None, persist_error=None):
        messages = [] if messages is None else messages
        factory = Mock(return_value=recorder)
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(capture.os, "geteuid", return_value=0), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True), \
             patch.object(passive, "persist_result", side_effect=persist_error,
                         return_value={"report_sha256": "a" * 64,
                                                                  "checksum_manifest_verified": True}):
            value = passive.execute(self.manifest(), "/unused-synthetic-output", authorized=True,
                readiness=lambda _: reply, capture_factory=factory,
                clock=clock.now, sleep=clock.wait, emit=messages.append)
        factory.assert_called_once()
        return value, messages

    def test_lowercase_local_readiness_permits_exactly_one_synthetic_run(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock)
        value, messages = self.execute_synthetic(recorder, clock)
        self.assertEqual(recorder.actions, ["start", "finish"])
        self.assertTrue(value["capture"]["passed"])
        self.assertFalse(value["hardware_commands_sent"])
        self.assertFalse(value["drivers_changed"])
        self.assertFalse(value["automatic_retry"])
        self.assertEqual(messages[0]["event"], "verified_start")
        self.assertTrue(all(stream.closed for stream in recorder.streams))

    def test_failure_preserves_primary_reason_and_only_aborts_owned_recorder(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock, fault_at=140)
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.execute_synthetic(recorder, clock, messages=messages)
        self.assertEqual(recorder.actions[0], "start")
        self.assertEqual(len(recorder.actions), 2)
        self.assertEqual(recorder.actions[-1][0], "abort")
        self.assertIn("Synthetic identity change", recorder.actions[-1][1])
        self.assertEqual(messages[-1]["event"], "stopped")
        self.assertTrue(all(stream.closed for stream in recorder.streams))

    def test_start_failure_never_emits_verified_start_or_retries(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock)
        recorder.start = Mock(side_effect=capture.CaptureHalt("Original sandbox check failed"))
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Original sandbox check failed"):
            self.execute_synthetic(recorder, clock, messages=messages)
        recorder.start.assert_called_once()
        self.assertTrue(all(item["event"] != "verified_start" for item in messages))
        self.assertEqual(recorder.actions, [("abort", "CaptureHalt: Original sandbox check failed")])
        self.assertEqual(recorder.streams, [])

    def test_failed_cue_flush_does_not_hide_primary_fault_or_skip_owned_abort(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock, fault_at=140)
        original_file = recorder._file
        def failing_file(name):
            stream = original_file(name)
            original_flush = stream.flush
            def failing_flush():
                if clock.now() >= 140:
                    raise OSError("secondary cue flush error")
                return original_flush()
            stream.flush = failing_flush
            return stream
        recorder._file = failing_file
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.execute_synthetic(recorder, clock, messages=messages)
        self.assertEqual(recorder.actions[-1][0], "abort")
        self.assertIn("secondary cue flush error", str(messages[-1]))

    def test_failed_owned_abort_keeps_primary_exception_and_reports_cleanup_fault(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock, fault_at=140)
        recorder.abort = Mock(side_effect=RuntimeError("secondary abort failure"))
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.execute_synthetic(recorder, clock, messages=messages)
        recorder.abort.assert_called_once()
        self.assertIn("secondary abort failure", str(messages[-1]))

    def test_broken_observer_output_never_skips_abort_or_replaces_primary_error(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock)
        factory = Mock(return_value=recorder)
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(capture.os, "geteuid", return_value=0), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True), \
             patch.object(passive, "persist_result", return_value={"checksum_manifest_verified": True}), \
             self.assertRaisesRegex(OSError, "original output failure"):
            passive.execute(self.manifest(), "/unused-synthetic-output", authorized=True,
                readiness=lambda _: "BEREIT", capture_factory=factory,
                clock=clock.now, sleep=clock.wait,
                emit=Mock(side_effect=OSError("original output failure")))
        self.assertEqual(recorder.actions[0], "start")
        self.assertEqual(recorder.actions[-1][0], "abort")

    def test_result_persistence_failure_preserves_original_test_error(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock, fault_at=140)
        messages = []
        with self.assertRaisesRegex(capture.CaptureHalt, "Synthetic identity change"):
            self.execute_synthetic(recorder, clock, messages=messages,
                                   persist_error=OSError("secondary report write error"))
        self.assertEqual(recorder.actions[-1][0], "abort")
        self.assertIn("secondary report write error", str(messages[-1]))


class PassivePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="synthetic-passive-results-")
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.directory.chmod(0o700)
        info = self.directory.stat()
        self.owner = (info.st_uid, info.st_gid)
        self.child = self.directory / "usb-capture"
        self.child.mkdir(mode=0o700)
        self.raw = self.child / "original-usbmon8.pcapng"
        self.raw.write_bytes(b"\x0a\x0d\x0d\x0asynthetic original")
        self.outcome = self.child / "capture-outcome.json"
        self.outcome.write_text('{"passed":true,"checksum_manifest_verified":true}\n')
        (self.child / "SHA256SUMS").write_text(capture.digest(self.raw) + "  " + self.raw.name + "\n")
        self.value = {"scope": capture.PASSIVE_SCOPE, "capture": {
            "passed": True, "checksum_manifest_verified": True,
            "capture_outcome_sha256": capture.digest(self.outcome)}}

    def test_standalone_receipt_closes_nested_capture_and_cue_evidence_chain(self):
        result = passive.persist_result(self.directory, self.value, self.owner)
        self.assertTrue(result["checksum_manifest_verified"])
        self.assertEqual(result["report_sha256"], capture.digest(self.directory / "result.json"))
        entries = {}
        for line in (self.directory / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            entries[name] = digest
            self.assertEqual(digest, capture.digest(self.directory / name))
        self.assertEqual(set(entries), {"result.json", "usb-capture/capture-outcome.json",
                                        "usb-capture/SHA256SUMS"})
        for name in ("result.json", "SHA256SUMS"):
            path = self.directory / name
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual((path.stat().st_uid, path.stat().st_gid), self.owner)
        persisted = json.loads((self.directory / "result.json").read_text())
        self.assertNotIn("passed", persisted)
        self.assertIn("Completion requires", persisted["completion_contract"])
        self.assertTrue(persisted["capture"]["passed"])

    def test_wrong_outcome_receipt_cannot_create_a_success_report(self):
        self.value["capture"]["capture_outcome_sha256"] = "0" * 64
        with self.assertRaisesRegex(capture.CaptureHalt, "receipt"):
            passive.persist_result(self.directory, self.value, self.owner)
        self.assertFalse((self.directory / "result.json").exists())
        self.assertTrue(self.raw.exists())

    def test_success_without_nested_manifest_is_not_accepted(self):
        (self.child / "SHA256SUMS").unlink()
        with self.assertRaisesRegex(capture.CaptureHalt, "nested checksum"):
            passive.persist_result(self.directory, self.value, self.owner)
        self.assertFalse((self.directory / "result.json").exists())

    def test_result_files_never_overwrite_existing_evidence(self):
        passive.persist_result(self.directory, self.value, self.owner)
        before = (self.directory / "result.json").read_bytes()
        before_sums = (self.directory / "SHA256SUMS").read_bytes()
        with self.assertRaises(FileExistsError):
            passive.persist_result(self.directory, dict(self.value, primary_error="different"), self.owner)
        self.assertEqual((self.directory / "result.json").read_bytes(), before)
        self.assertEqual((self.directory / "SHA256SUMS").read_bytes(), before_sums)

    def test_parent_permissions_or_owner_changes_prevent_report_write(self):
        self.directory.chmod(0o755)
        with self.assertRaises(capture.CaptureHalt):
            passive.persist_result(self.directory, self.value, self.owner)
        self.directory.chmod(0o700)
        with self.assertRaises(capture.CaptureHalt):
            passive.persist_result(self.directory, self.value, (self.owner[0] + 1, self.owner[1]))
        self.assertFalse((self.directory / "result.json").exists())

    def test_failed_fsync_never_returns_a_verified_receipt_or_deletes_original(self):
        original = self.raw.read_bytes()
        with patch.object(passive.os, "fsync", side_effect=OSError("synthetic disk error")), \
             self.assertRaisesRegex(OSError, "synthetic disk error"):
            passive.persist_result(self.directory, self.value, self.owner)
        self.assertFalse((self.directory / "SHA256SUMS").exists())
        self.assertEqual(self.raw.read_bytes(), original)

    def test_failed_run_can_record_error_without_claiming_capture_success(self):
        self.outcome.unlink()
        (self.child / "SHA256SUMS").unlink()
        value = {"scope": capture.PASSIVE_SCOPE, "capture": {"passed": False},
                 "primary_error": "Synthetic initial check failed"}
        receipt = passive.persist_result(self.directory, value, self.owner)
        self.assertTrue(receipt["checksum_manifest_verified"])
        saved = json.loads((self.directory / "result.json").read_text())
        self.assertFalse(saved["capture"]["passed"])
        self.assertEqual(saved["primary_error"], value["primary_error"])


class PassiveTimingTests(unittest.TestCase):
    def test_exact_finite_plan_with_human_buffers(self):
        phases = passive.phase_plan()
        self.assertEqual([(phase["start"], phase["end"]) for phase in phases],
            [(0, 30), (30, 50), (50, 80), (80, 110), (110, 135), (135, 160),
             (160, 185), (185, 210), (210, 240), (240, 270), (270, 300)])
        for phase in phases:
            self.assertTrue(phase["instruction"])
            self.assertLess(phase["buffer_seconds"], phase["end"] - phase["start"])
            if phase["start"] in (50, 80, 110, 135, 160, 185, 210, 240):
                self.assertGreaterEqual(phase["buffer_seconds"], 10)

    def test_real_monotonic_capture_origin_bounds_phases_and_stop_grace(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock)
        messages = []
        cues = passive.run_phases(recorder, clock=clock.now, sleep=clock.wait, emit=messages.append)
        self.assertTrue(cues)
        self.assertTrue(messages)
        self.assertGreaterEqual(clock.now(), 399)
        self.assertLess(clock.now(), 399.01)
        self.assertLess(clock.now(), recorder.deadline)
        self.assertGreater(len(recorder.checks), 2500)
        self.assertTrue(all(now + remaining <= 400 for now, remaining, _ in recorder.checks))
        self.assertLessEqual(max(b[0] - a[0] for a, b in
            zip(recorder.checks, recorder.checks[1:])), .100001)
        self.assertEqual(recorder.actions, [])  # Timing loop cannot release or restore devices.
        self.assertEqual(cues[0]["event"], "verified_start")
        actions = [cue for cue in cues if cue["event"] == "action_cue"]
        self.assertEqual([cue["phase"] for cue in actions],
                         ["buttons", "sticks", "l4", "r4", "l5", "r5", "combinations", "movement"])
        for cue, expected in zip(actions, (60, 90, 120, 145, 170, 195, 220, 250)):
            self.assertAlmostEqual(cue["seconds_from_capture_request"], expected, delta=.10001)

    def test_no_phase_or_start_signal_without_verified_recorder(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock)
        recorder.ready = None
        messages = []
        with self.assertRaises(capture.CaptureHalt):
            passive.run_phases(recorder, clock=clock.now, sleep=clock.wait, emit=messages.append)
        self.assertEqual(messages, [])
        self.assertEqual(clock.sleeps, [])

    def test_late_readiness_does_not_erase_preparation_or_extend_capture(self):
        clock = VirtualClock(131)
        recorder = SyntheticRecorder(clock)
        recorder.ready = 131
        with self.assertRaises(capture.CaptureHalt):
            passive.run_phases(recorder, clock=clock.now, sleep=clock.wait, emit=lambda _: None)
        self.assertEqual(clock.sleeps, [])

    def test_state_change_stops_cues_without_automatic_retry(self):
        clock = VirtualClock()
        recorder = SyntheticRecorder(clock, fault_at=140)
        with self.assertRaisesRegex(capture.CaptureHalt, "identity change"):
            passive.run_phases(recorder, clock=clock.now, sleep=clock.wait, emit=lambda _: None)
        self.assertLess(clock.now(), 140.11)
        self.assertEqual(recorder.actions, [])


class PassiveGuardSourceTests(unittest.TestCase):
    def test_guest_profile_and_packet_options_are_pure_bounded_expressions(self):
        tree = ast.parse((NATIVE / "usb_capture/guest-check.py").read_text())
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
        def pure_value(node, variables):
            expression = ast.Expression(body=node)
            for part in ast.walk(expression):
                self.assertIsInstance(part, allowed)
                if isinstance(part, ast.Call):
                    self.assertIsInstance(part.func, ast.Name)
                    self.assertEqual(part.func.id, "str")
            return eval(compile(expression, "synthetic-guest-expression", "eval"),
                        {"__builtins__": {}, "str": str}, variables)
        for profile, expected in ((None, 450), (capture.PASSIVE_SCOPE, 300)):
            seconds = pure_value(duration, {"profile": profile})
            self.assertEqual(seconds, expected)
            command = pure_value(argv, {"duration": seconds})
            self.assertEqual(command[:7], ["/usr/bin/dumpcap", "-i", "usbmon8", "-y",
                                           "USB_LINUX_MMAPPED", "-s", "0"])
            self.assertIn("duration:" + str(expected), command)
            self.assertEqual(command[command.index("-F") + 1], "pcapng")
            self.assertEqual(command[command.index("-w") + 1], "-")
            self.assertNotIn("/dev/bus/usb", command)

    def guard_fixture(self):
        target_value = target()
        resolved = "/sys/devices/synthetic/usb8/8-6"
        texts = {"/sys/bus/usb/devices/8-6/" + name: value for name, value in {
            "idVendor": "3537", "idProduct": "100a", "busnum": "8", "devnum": "8",
            "devpath": "6", "bNumInterfaces": "2"}.items()}
        texts["/proc/sys/kernel/random/boot_id"] = target_value["boot_id"]
        texts["/var/lib/gamesir-native/state.json"] = json.dumps({"paused": True, "leases": {}})
        links = {"/sys/bus/usb/devices/8-6": resolved,
                 "/sys/bus/usb/devices/8-6:1.0/driver": "/sys/bus/usb/drivers/xpad",
                 "/sys/bus/usb/devices/8-6:1.1/driver": "/sys/bus/usb/drivers/usbhid",
                 "/sys/class/hidraw/hidraw11": resolved + "/synthetic/hidraw/hidraw11",
                 "/proc/42/fd/3": "/dev/null"}
        globs = {"/sys/class/hidraw": ["/sys/class/hidraw/hidraw11"]}
        for index, endpoints in ((0, (2, 130)), (1, (4, 132))):
            interface = "/sys/bus/usb/devices/8-6:1." + str(index)
            globs[interface] = [interface + "/ep_" + format(ep, "02x") for ep in endpoints]
            for ep in endpoints:
                texts[interface + "/ep_" + format(ep, "02x") + "/bEndpointAddress"] = format(ep, "02x")
        stats = {resolved: SimpleNamespace(st_dev=11, st_ino=12),
                 str(PurePosixPath(resolved).parent): SimpleNamespace(st_dev=11, st_ino=13),
                 "/var/lib/gamesir-native/state.json": SimpleNamespace(
                     st_mode=stat.S_IFREG | 0o600, st_uid=0, st_size=128)}
        directories = {"/proc": ["/proc/42"], "/proc/42/fd": ["/proc/42/fd/3"]}
        byte_values = {"/proc/42/cmdline": b"synthetic-process\0"}
        node_stats = {
            "/dev/bus/usb/008/008": SimpleNamespace(st_mode=stat.S_IFCHR | 0o600,
                                                   st_rdev=os.makedev(189, 903)),
            "/dev/hidraw11": SimpleNamespace(st_mode=stat.S_IFCHR | 0o600,
                                               st_rdev=os.makedev(240, 11)),
            "/proc/42/fd/3": SimpleNamespace(st_mode=stat.S_IFCHR | 0o666,
                                              st_rdev=os.makedev(1, 3))}
        failures = {}
        class MemoryPath(PurePosixPath):
            def _read(self, values):
                if str(self) in failures:
                    raise failures[str(self)]
                if str(self) not in values:
                    raise AssertionError("Unmapped synthetic path: " + str(self))
                return values[str(self)]
            def resolve(self, strict=False):
                return MemoryPath(self._read(links))
            def is_symlink(self):
                return str(self) in links
            def read_text(self, *args, **kwargs):
                return self._read(texts)
            def read_bytes(self):
                return self._read(byte_values)
            def stat(self):
                return self._read(stats)
            def lstat(self):
                return self._read(stats)
            def glob(self, pattern):
                self_pattern = "hidraw*" if str(self) == "/sys/class/hidraw" else "ep_*"
                if pattern != self_pattern:
                    raise AssertionError("Unmapped synthetic glob: " + pattern)
                return iter(MemoryPath(name) for name in self._read(globs))
            def iterdir(self):
                return iter(MemoryPath(name) for name in self._read(directories))
        def run():
            output = io.StringIO()
            with patch("pathlib.Path", MemoryPath), \
                 patch.object(sys, "argv", ["synthetic-identity-check", json.dumps({
                     "target": target_value, "capture_profile": capture.PASSIVE_SCOPE})]), \
                 patch.object(os, "readlink", side_effect=lambda name: links[str(name)]), \
                 patch.object(os, "lstat", side_effect=lambda name, **kwargs: node_stats[str(name)]), \
                 patch.object(os, "stat", side_effect=lambda name, **kwargs: node_stats[str(name)]), \
                 patch.object(os, "write", side_effect=AssertionError("No hardware/log descriptor write")), \
                 patch.object(capture.subprocess, "run", side_effect=AssertionError("No process")), \
                 patch.object(capture.subprocess, "Popen", side_effect=AssertionError("No process")), \
                 contextlib.redirect_stdout(output):
                # The asset is executed only against an entirely in-memory Path class;
                # every unexpected lookup raises, so no host metadata can be read.
                exec(compile(source, "synthetic-identity-guard", "exec"), {"__name__": "synthetic_guard"})
            return json.loads(output.getvalue())
        source = (NATIVE / "usb_capture/identity-check.py").read_text()
        return SimpleNamespace(run=run, texts=texts, links=links, stats=stats,
                               failures=failures, byte_values=byte_values, target=target_value,
                               node_stats=node_stats)

    def test_passive_identity_guard_accepts_only_synthetic_100a_state(self):
        fixture = self.guard_fixture()
        observed = fixture.run()
        self.assertEqual(observed["idProduct"], "100a")
        self.assertEqual(observed["interfaces"]["0"]["driver"], "xpad")
        self.assertEqual(observed["interfaces"]["1"]["driver"], "usbhid")
        self.assertEqual(observed["boot_id"], target()["boot_id"])

    def test_guard_requires_paused_manager_and_empty_ownership(self):
        for manager in ({"paused": False, "leases": {}},
                        {"paused": True, "leases": {"8-6": {"state": "released"}}},
                        {"paused": True}, {}):
            with self.subTest(manager=manager):
                fixture = self.guard_fixture()
                fixture.texts["/var/lib/gamesir-native/state.json"] = json.dumps(manager)
                with self.assertRaisesRegex(SystemExit, "Manager"):
                    fixture.run()

    def test_guard_rejects_boot_instance_driver_or_unknown_metadata(self):
        for change in ("boot", "instance", "driver", "empty-pid"):
            with self.subTest(change=change):
                fixture = self.guard_fixture()
                if change == "boot":
                    fixture.texts["/proc/sys/kernel/random/boot_id"] = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
                elif change == "instance":
                    fixture.stats["/sys/devices/synthetic/usb8/8-6"] = SimpleNamespace(st_dev=11, st_ino=99)
                elif change == "driver":
                    fixture.links["/sys/bus/usb/devices/8-6:1.0/driver"] = "/sys/bus/usb/drivers/gs_native"
                else:
                    fixture.texts["/sys/bus/usb/devices/8-6/idProduct"] = ""
                with self.assertRaisesRegex(SystemExit, "Instanz oder Treiberbindung"):
                    fixture.run()

    def test_guard_rejects_foreign_usb_and_associated_hidraw_descriptors(self):
        for descriptor in ("/dev/bus/usb/008/008", "/dev/hidraw11", "/dev/hidraw11 (deleted)"):
            with self.subTest(descriptor=descriptor):
                fixture = self.guard_fixture()
                fixture.links["/proc/42/fd/3"] = descriptor
                with self.assertRaisesRegex(SystemExit, "Fremder"):
                    fixture.run()

    def test_guard_rejects_deadband_or_incomplete_process_inspection(self):
        fixture = self.guard_fixture()
        fixture.byte_values["/proc/42/cmdline"] = b"python\0/usr/share/deadband/main.py\0"
        with self.assertRaisesRegex(SystemExit, "Deadband"):
            fixture.run()
        fixture = self.guard_fixture()
        fixture.failures["/proc/42/cmdline"] = PermissionError("synthetic denied")
        with self.assertRaisesRegex(SystemExit, "unvollständig"):
            fixture.run()

    def test_guard_rejects_device_aliases_even_with_an_unrecognized_path(self):
        for node in ("/dev/bus/usb/008/008", "/dev/hidraw11"):
            with self.subTest(node=node):
                fixture = self.guard_fixture()
                fixture.links["/proc/42/fd/3"] = "/private/container/other-device-name"
                fixture.node_stats["/proc/42/fd/3"] = fixture.node_stats[node]
                with self.assertRaisesRegex(SystemExit, "Gerätealias"):
                    fixture.run()


if __name__ == "__main__":
    unittest.main()
