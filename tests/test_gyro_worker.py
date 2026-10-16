#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Worker tests: pipes, temporary owned files and Python fakes; never devices."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/imu"))
import gamesir_gyro_worker as worker


class PipeChannel(unittest.TestCase):
    def setUp(self):
        self.read_fd, self.write_fd = os.pipe()
        self.output = io.StringIO()
        self.channel = worker.ParentChannel(self.read_fd, self.output)

    def tearDown(self):
        os.close(self.read_fd)
        if self.write_fd is not None:
            os.close(self.write_fd)

    def send(self, value):
        os.write(self.write_fd, value)

    def test_go_after_ready_and_ping(self):
        self.send(b"PING\nGO\n")
        self.channel.wait_go()
        self.assertTrue(self.channel.go)

    def test_go_outside_wait_is_rejected(self):
        self.send(b"GO\n")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            self.channel.poll()

    def test_duplicate_go_rejected(self):
        self.send(b"GO\nGO\n")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            self.channel.poll(awaiting_go=True)

    def test_stop(self):
        self.send(b"STOP\n")
        with self.assertRaisesRegex(ValueError, "STOP"):
            self.channel.poll()

    def test_eof(self):
        os.close(self.write_fd)
        self.write_fd = None
        with self.assertRaisesRegex(ValueError, "pipe closed"):
            self.channel.poll()

    def test_partial_line_returns_without_waiting_for_newline(self):
        self.send(b"PI")
        started = time.monotonic()
        self.channel.poll()
        self.assertLess(time.monotonic() - started, .5)
        self.assertEqual(self.channel.pending, b"PI")
        self.send(b"NG\n")
        self.channel.poll()
        self.assertEqual(self.channel.pending, b"")

    def test_oversized_partial_line_rejected(self):
        self.send(b"X" * 513)
        with self.assertRaisesRegex(ValueError, "oversized"):
            self.channel.poll()

    def test_large_valid_ping_backlog_then_partial_go_is_not_false_oversize(self):
        self.send(b"PING\n" * 250 + b"G")
        for _ in range(3):
            self.channel.poll(awaiting_go=True)
        self.assertFalse(self.channel.go)
        self.assertEqual(self.channel.pending, b"G")
        self.send(b"O\n")
        self.channel.poll(awaiting_go=True)
        self.assertTrue(self.channel.go)

    def test_heartbeat_expiry_even_without_readable_input(self):
        self.channel.last_ping = 100
        with patch.object(worker.time, "monotonic", return_value=103.1):
            with self.assertRaisesRegex(ValueError, "heartbeat lost"):
                self.channel.poll()

    def test_ping_refreshes_heartbeat(self):
        self.channel.last_ping = 100
        self.send(b"PING\n")
        with patch.object(worker.time, "monotonic", return_value=200):
            self.channel.poll()
        self.assertEqual(self.channel.last_ping, 200)

    def test_emit_json_and_nonfinite_rejection(self):
        self.channel.emit("ready", device_opened=False)
        self.assertEqual(json.loads(self.output.getvalue()), {"event": "ready", "device_opened": False})
        with self.assertRaises(ValueError):
            self.channel.emit("invalid", number=float("nan"))

    def test_wait_go_has_bounded_deadline_without_any_device_access(self):
        self.channel.last_ping = 901
        with patch.object(worker.time, "monotonic", side_effect=[0, 901, 901]), patch.object(worker.select, "select", return_value=([], [], [])):
            with self.assertRaisesRegex(ValueError, "15 minutes"):
                self.channel.wait_go()


class MemoryEvidence:
    def __init__(self):
        self.handles, self.documents = {}, {}
        self.finish_errors = []
        self.finished = 0

    def open(self, name, *, binary=False):
        if name in self.handles:
            raise ValueError("overwrite")
        self.handles[name] = io.BytesIO() if binary else io.StringIO()
        return self.handles[name]

    def json(self, name, value):
        self.documents[name] = copy.deepcopy(value)

    def finish(self):
        self.finished += 1
        return self.finish_errors[:]


class FakeParent:
    def __init__(self):
        self.events, self.polls, self.waited = [], 0, False
        self.poll_failure_at = None
        self.break_event = None

    def emit(self, event, **fields):
        self.events.append({"event": event, **fields})
        if event == self.break_event:
            raise BrokenPipeError("frontend disappeared")

    def wait_go(self):
        self.waited = True

    def poll(self):
        self.polls += 1
        if self.poll_failure_at == self.polls:
            raise ValueError("frontend pipe closed; cancel and restore")


class FakeTransaction:
    def __init__(self):
        self.setup_calls = self.restore_calls = 0
        self.restored = True
        self.setup_error = None

    def setup(self):
        self.setup_calls += 1
        if self.setup_error:
            raise self.setup_error
        return {"instance_id": "virtual-host-only", "directory": "/virtual/iio:device77",
                "major": 240, "minor": 77, "scan_bytes": 32, "types": {},
                "clock": "monotonic", "buffer_push_errors": 0}, 666

    def restore(self):
        self.restore_calls += 1
        return {"restored": self.restored, "errors": [] if self.restored else ["injected restore failure"],
                "writes": [{"attribute": "buffer/enable", "value": "1", "ok": True}],
                "before": {}, "after": {}}


def synthetic_frame(counter, stamp):
    data = bytearray(32)
    struct.pack_into("<6h", data, 0, -8192, 0, 0, 10, -20, 30)
    struct.pack_into("<Q", data, 16, counter)
    data[24:32] = stamp.to_bytes(8, sys.byteorder, signed=True)
    return bytes(data)


class Execute(unittest.TestCase):
    def setUp(self):
        self.manifest = {"snapshot": {"device_node": "/virtual/iio:device77"}}
        self.evidence, self.channel, self.transaction = MemoryEvidence(), FakeParent(), FakeTransaction()
        self.closed_reader = 0
        self.raw = b""

    def reader(self, metadata, node, duration, no_data, *, descriptor, check_alive):
        self.assertEqual(node, "/virtual/iio:device77")
        self.assertEqual(descriptor, 666)
        self.assertEqual(duration, worker.CAPTURE_SECONDS)
        self.assertEqual(no_data, 2)
        stamp = time.monotonic_ns() - 100_000_000
        self.raw = b"".join(synthetic_frame(70 + i, stamp + i * 10_000_000) for i in range(3))
        try:
            check_alive()
            yield self.raw[:19], time.monotonic_ns()
            check_alive()
            yield self.raw[19:], time.monotonic_ns()
        finally:
            self.closed_reader += 1

    def run_worker(self, reader=None, revalidate=lambda: None):
        return worker.execute(self.manifest, self.evidence, self.channel,
                              transaction_factory=lambda snapshot: self.transaction,
                              reader=reader or self.reader, revalidate=revalidate)

    def test_passed_capture_stores_original_bytes_and_restores(self):
        self.assertEqual(self.run_worker(), 0)
        self.assertTrue(self.channel.waited)
        self.assertEqual(self.transaction.setup_calls, 1)
        self.assertEqual(self.transaction.restore_calls, 1)
        self.assertEqual(self.closed_reader, 1)
        self.assertEqual(self.evidence.finished, 1)
        self.assertEqual(self.evidence.handles["scans.bin"].getvalue(), self.raw)
        rows = [json.loads(line) for line in self.evidence.handles["observations.jsonl"].getvalue().splitlines()]
        self.assertEqual(len(rows), 3)
        self.assertEqual([row["sample_number"] for row in rows], [70, 71, 72])
        self.assertFalse(self.evidence.documents["report.json"]["calibration_verified"])
        self.assertTrue(self.channel.events[-1]["passed"])

    def test_decode_fault_and_restore_failure_preserve_first_error_and_raw(self):
        self.transaction.restored = False
        def malformed(*args, **kwargs):
            stamp = time.monotonic_ns() - 10_000_000
            data = bytearray(synthetic_frame(70, stamp))
            data[12] = 1
            yield bytes(data), time.monotonic_ns()
        self.assertEqual(self.run_worker(malformed), 1)
        report = self.evidence.documents["report.json"]
        self.assertIn("nonzero scan padding", report["failure"])
        self.assertFalse(report["restored"])
        self.assertEqual(len(self.evidence.handles["scans.bin"].getvalue()), 32)
        self.assertEqual(self.evidence.documents["buffer-transaction.json"]["errors"], ["injected restore failure"])

    def test_setup_failure_runs_restore_and_preserves_original(self):
        self.transaction.setup_error = OSError("original setup failure")
        self.assertEqual(self.run_worker(), 1)
        self.assertEqual(self.transaction.restore_calls, 1)
        self.assertIn("original setup failure", self.evidence.documents["report.json"]["failure"])
        self.assertNotIn("scans.bin", self.evidence.handles)

    def test_revalidate_failure_never_opens_transaction(self):
        def invalid():
            raise ValueError("changed approved instance")
        self.assertEqual(self.run_worker(revalidate=invalid), 1)
        self.assertEqual(self.transaction.setup_calls, 0)
        self.assertEqual(self.transaction.restore_calls, 0)
        self.assertTrue(self.evidence.documents["buffer-transaction.json"]["restored"])

    def test_parent_eof_from_reader_callback_enters_cleanup(self):
        self.channel.poll_failure_at = 2
        self.assertEqual(self.run_worker(), 1)
        self.assertEqual(self.closed_reader, 1)
        self.assertEqual(self.transaction.restore_calls, 1)
        self.assertIn("frontend pipe closed", self.evidence.documents["report.json"]["failure"])

    def test_broken_capture_started_emit_still_restores(self):
        self.channel.break_event = "capture_started"
        self.assertEqual(self.run_worker(), 1)
        self.assertEqual(self.transaction.restore_calls, 1)
        self.assertIn("BrokenPipeError", self.evidence.documents["report.json"]["failure"])
        self.assertEqual(self.evidence.finished, 1)

    def test_finish_fsync_failure_never_reports_passed(self):
        self.evidence.finish_errors = ["fsync scans.bin: injected failure"]
        self.assertEqual(self.run_worker(), 1)
        self.assertFalse(self.channel.events[-1]["passed"])
        self.assertIn("fsync scans.bin", self.channel.events[-1]["failure"])
        self.assertEqual(self.transaction.restore_calls, 1)

    def test_partial_scan_is_not_successful(self):
        def partial(*args, **kwargs):
            yield b"\0" * 11, time.monotonic_ns()
        self.assertEqual(self.run_worker(partial), 1)
        self.assertIn("incomplete trailing", self.evidence.documents["report.json"]["failure"])

    def test_empty_stream_is_not_successful(self):
        def empty(*args, **kwargs):
            return
            yield
        self.assertEqual(self.run_worker(empty), 1)
        self.assertIn("no complete", self.evidence.documents["report.json"]["failure"])

    def test_unexpected_restore_exception_never_overwrites_primary_decoder_fault(self):
        def malformed(*args, **kwargs):
            yield b"\0" * 32, time.monotonic_ns()
        with patch.object(self.transaction, "restore", side_effect=RuntimeError("secondary rollback exception")):
            self.assertEqual(self.run_worker(malformed), 1)
        self.assertIn("nonpositive counter or timestamp", self.evidence.documents["report.json"]["failure"])
        self.assertIn("secondary rollback exception", self.evidence.documents["buffer-transaction.json"]["errors"][0])
        self.assertFalse(self.channel.events[-1]["passed"])

    def test_keyboard_interrupt_is_reported_only_after_restoration(self):
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt("local cancel")
            yield
        self.assertEqual(self.run_worker(interrupted), 1)
        self.assertEqual(self.transaction.restore_calls, 1)
        self.assertIn("KeyboardInterrupt", self.evidence.documents["report.json"]["failure"])


class ProcessAccess(unittest.TestCase):
    def entry(self, name, *, character=True, minor=77, error=None):
        class Entry:
            def __init__(self):
                self.name = name
            def stat(self):
                if error:
                    raise error
                return SimpleNamespace(st_mode=0o020600 if character else 0o100600, st_rdev=os.makedev(240, minor))
            def __str__(self):
                return "/proc/fake/fd/" + name
        return Entry()

    def run_check(self, entries, *, pid="100", owned_fd=None, directory_error=None):
        class Directory:
            parent = SimpleNamespace(name=pid)
            def iterdir(self):
                if directory_error:
                    raise directory_error
                return iter(entries)
        proc = SimpleNamespace(glob=lambda pattern: [Directory()])
        with patch.object(worker, "Path", return_value=proc), patch.object(worker.os, "getpid", return_value=100), patch.object(worker.os, "open", side_effect=AssertionError("must not open device")), patch.object(worker.os, "read", side_effect=AssertionError("must not read device")):
            worker.check_other_readers({"major": 240, "minor": 77}, owned_fd)

    def test_different_nodes_and_regular_files_do_not_conflict(self):
        self.run_check([self.entry("1", minor=78), self.entry("2", character=False)])

    def test_other_process_same_character_device_is_conflict(self):
        with self.assertRaisesRegex(ValueError, "another IIO reader"):
            self.run_check([self.entry("6")], pid="200")

    def test_only_exact_own_reserved_descriptor_is_ignored(self):
        self.run_check([self.entry("7")], owned_fd=7)
        with self.assertRaisesRegex(ValueError, "another IIO reader"):
            self.run_check([self.entry("7"), self.entry("8")], owned_fd=7)
        with self.assertRaisesRegex(ValueError, "another IIO reader"):
            self.run_check([self.entry("7")], pid="200", owned_fd=7)

    def test_disappearing_process_and_fd_are_ignored(self):
        self.run_check([], directory_error=FileNotFoundError("process exited"))
        self.run_check([self.entry("7", error=FileNotFoundError("fd closed")),
                        self.entry("8", error=ProcessLookupError("process exited"))])

    def test_permission_errors_stop_instead_of_claiming_no_conflict(self):
        with self.assertRaises(PermissionError):
            self.run_check([], directory_error=PermissionError("inaccessible proc"))
        with self.assertRaises(PermissionError):
            self.run_check([self.entry("7", error=PermissionError("inaccessible fd"))])


class Manifest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        hashes = {}
        for relative in worker.SOURCES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# constructed local test source " + relative)
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.value = {"schema_version": 1, "kind": "gamesir_yaw90left_manifest",
                      "source_sha256": hashes, "snapshot": {"synthetic": True}}
        self.path = self.root / "manifest.json"

    def tearDown(self):
        self.temporary.cleanup()

    def read(self):
        self.path.write_text(json.dumps(self.value))
        with patch.object(worker, "ROOT", self.root):
            return worker.read_manifest(self.path)

    def test_six_fixed_sources_and_snapshot(self):
        self.assertEqual(len(worker.SOURCES), 6)
        self.assertEqual(self.read(), self.value)

    def test_missing_extra_or_changed_source_hash_rejected(self):
        for mode in ("missing", "extra", "changed"):
            with self.subTest(mode=mode):
                original = copy.deepcopy(self.value)
                if mode == "missing":
                    del self.value["source_sha256"][worker.SOURCES[0]]
                elif mode == "extra":
                    self.value["source_sha256"]["/arbitrary/command"] = "0" * 64
                else:
                    self.value["source_sha256"][worker.SOURCES[0]] = "0" * 64
                with self.assertRaises(ValueError):
                    self.read()
                self.value = original

    def test_changed_source_bytes_rejected(self):
        (self.root / worker.SOURCES[2]).write_text("changed")
        with self.assertRaisesRegex(ValueError, "approved helper changed"):
            self.read()

    def test_wrong_manifest_kind_version_or_snapshot_rejected(self):
        for field, invalid in (("kind", "other"), ("schema_version", 2), ("snapshot", None)):
            with self.subTest(field=field):
                original = copy.deepcopy(self.value)
                self.value[field] = invalid
                with self.assertRaises(ValueError):
                    self.read()
                self.value = original


class RealEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.parent = Path(self.temporary.name)
        self.output = self.parent / "capture"
        self.patcher = patch.object(worker.os, "fchown")
        self.chown = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temporary.cleanup()

    def evidence(self):
        return worker.Evidence(self.output, os.getuid(), os.getgid(), self.parent)

    def test_private_files_durable_hashes_and_descriptor_handback(self):
        evidence = self.evidence()
        evidence.open("scans.bin", binary=True).write(b"constructed own bytes")
        evidence.json("report.json", {"synthetic": True})
        self.assertEqual(evidence.finish(), [])
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        sums = (self.output / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(sums), 2)
        for line in sums:
            digest, name = line.split("  ")
            self.assertEqual(digest, hashlib.sha256((self.output / name).read_bytes()).hexdigest())
            self.assertEqual(stat.S_IMODE((self.output / name).stat().st_mode), 0o600)
        self.assertEqual(self.chown.call_count, 4)  # 3 files + capture directory

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        original = self.output / "keep"
        original.write_text("untouched")
        with self.assertRaises(FileExistsError):
            self.evidence()
        self.assertEqual(original.read_text(), "untouched")

    def test_symlink_output_never_followed(self):
        other = self.parent / "other"
        other.mkdir()
        self.output.symlink_to(other, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            self.evidence()
        self.assertEqual(list(other.iterdir()), [])

    def test_symlink_parent_rejected(self):
        real = self.parent / "real"
        real.mkdir(mode=0o700)
        alias = self.parent / "alias"
        alias.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "canonical"):
            worker.Evidence(alias / "capture", os.getuid(), os.getgid(), self.parent)

    def test_nonprivate_parent_rejected(self):
        self.parent.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "private"):
            self.evidence()

    def test_file_collision_and_escape_rejected(self):
        evidence = self.evidence()
        evidence.open("report.json").write("original")
        with self.assertRaises(ValueError):
            evidence.open("report.json")
        with self.assertRaises(ValueError):
            evidence.open("../escape")
        # A preexisting malicious leaf is rejected by EXCL, never followed.
        outside = self.parent / "outside"
        outside.write_text("untouched")
        (self.output / "scans.bin").symlink_to(outside)
        with self.assertRaises(FileExistsError):
            evidence.open("scans.bin", binary=True)
        (self.output / "scans.bin").unlink()
        self.assertEqual(evidence.finish(), [])
        self.assertEqual(outside.read_text(), "untouched")

    def test_directory_rename_does_not_redirect_evidence_writes(self):
        evidence = self.evidence()
        moved = self.parent / "moved"
        self.output.rename(moved)
        self.output.mkdir()
        foreign = self.output / "report.json"
        foreign.write_text("foreign stays intact")
        evidence.json("report.json", {"own": True})
        self.assertEqual(evidence.finish(), [])
        self.assertEqual(foreign.read_text(), "foreign stays intact")
        self.assertEqual(json.loads((moved / "report.json").read_text()), {"own": True})

    def test_fsync_failure_is_explicit(self):
        evidence = self.evidence()
        evidence.open("observations.jsonl").write("{}\n")
        with patch.object(worker.os, "fsync", side_effect=OSError("injected disk failure")):
            errors = evidence.finish()
        self.assertTrue(any("injected disk failure" in error for error in errors))

    def test_one_fsync_failure_is_persisted_and_rehashed_without_overwriting_primary(self):
        for primary in (None, "original decoder fault"):
            with self.subTest(primary=primary):
                if self.output.exists():
                    import shutil
                    shutil.rmtree(self.output)
                evidence = self.evidence()
                evidence.open("scans.bin", binary=True).write(b"constructed fixture")
                evidence.json("report.json", {"completed": primary is None, "failure": primary})
                fsync = worker.os.fsync
                calls = 0
                def one_failure(fd):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        raise OSError("single injected disk failure")
                    return fsync(fd)
                with patch.object(worker.os, "fsync", side_effect=one_failure):
                    errors = evidence.finish()
                self.assertTrue(errors)
                report = json.loads((self.output / "report.json").read_text())
                self.assertFalse(report["completed"])
                self.assertEqual(report["failure"], primary or errors[0])
                self.assertTrue(report["evidence_finalization_errors"])
                for line in (self.output / "SHA256SUMS").read_text().splitlines():
                    digest, name = line.split("  ")
                    self.assertEqual(digest, hashlib.sha256((self.output / name).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
