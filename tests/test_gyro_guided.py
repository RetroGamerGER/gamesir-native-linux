#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Guidance tests: constructed samples, private temporary files and mocked GUI.

No real GUI, sudo, device open, sysfs write or network operation is performed.
"""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/imu"))
import gamesir_gyro_guided as guided


class Clock:
    def __init__(self):
        self.now = 1_000_000_000_000

    def monotonic_ns(self):
        return self.now

    def sleep(self, seconds):
        self.now += int(seconds * 1_000_000_000)


class FakeCues:
    clock = None
    fail_at = None
    instances = []

    def __init__(self, sink=None):
        self.sink = sink or (lambda row: None)
        self.rows = []
        self.closed = False
        type(self).instances.append(self)

    def check(self):
        pass

    def show(self, event, instruction, seconds, scheduled_ns=None):
        if event == self.fail_at:
            raise ValueError("constructed KDE cue failure")
        row = {"event": event, "instruction": instruction,
               "monotonic_ns": self.clock.now, "scheduled_monotonic_ns": scheduled_ns}
        self.rows.append(row)
        self.sink(row)

    def close(self):
        self.closed = True


def observations(start_ns):
    """Own 10-Hz fixture; activity outside motion deliberately excluded."""
    rows = []
    for index in range(1081):
        elapsed = index / 10
        gyro = [0, 0, 100] if 40 <= elapsed <= 55 else [0, 0, 0]
        if 20 < elapsed < 35 or 60 < elapsed < 75:
            gyro = [200, 300, -1000]
        rows.append({"timestamp_ns": start_ns + index * 100_000_000,
                     "sample_number": index + 91, "gyro_raw": gyro, "accel_raw": [0, 0, 8192],
                     "coherent": True, "timebase": "host_monotonic_receive",
                     "source_kind": "synthetic", "instance_id": "constructed-fake-only"})
    return rows


def cue_fixture(start_ns, lag_ns=0):
    return [{"event": name, "monotonic_ns": start_ns + offset * 1_000_000_000 + lag_ns,
             "scheduled_monotonic_ns": start_ns + offset * 1_000_000_000}
            for offset, name, _, _ in guided.PHASES]


def capture_fixture(path, start_ns):
    """Fake worker's private, hashed saved-file bundle; no device is opened."""
    path.mkdir(mode=0o700)
    files = {"scans.bin": b"constructed saved scan bytes; never hardware data",
             "observations.jsonl": "".join(json.dumps(row) + "\n" for row in observations(start_ns)).encode()}
    for name, data in files.items():
        fd = os.open(path / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    guided.write_json(path / "layout.json", {"constructed": True})
    guided.write_json(path / "buffer-transaction.json", {"restored": True, "errors": [], "constructed": True})
    guided.write_json(path / "report.json", {"completed": True, "restored": True, "failure": None,
                                            "cleanup_errors": [], "capture_started_monotonic_ns": start_ns,
                                            "constructed": True})
    fd = os.open(path / "SHA256SUMS", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        for name in guided.CAPTURE_FILES:
            handle.write(f"{hashlib.sha256((path / name).read_bytes()).hexdigest()}  {name}\n")


class PlanAndEvidence(unittest.TestCase):
    def test_only_three_individually_selected_left_repetitions(self):
        with patch.object(guided, "run_measurement", return_value=0) as run:
            for repetition in (1, 2, 3):
                self.assertEqual(guided.main(["run", "--manifest", "/home/fake/manifest.json",
                                              "--repetition", str(repetition), "--reference-description", "two90marks",
                                              "--output", "/home/fake/new"]), 0)
            self.assertEqual(run.call_count, 3)
        for repetition in ("0", "4", "all", "1,2,3"):
            with self.subTest(repetition=repetition), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                guided.main(["run", "--manifest", "m", "--repetition", repetition,
                             "--reference-description", "marks", "--output", "o"])

    def test_worker_argv_is_fixed_and_cannot_inject_shell(self):
        argv = guided.worker_command(Path("/home/example/a $(touch NO).json"), Path("/home/example/with spaces"))
        self.assertEqual(argv[:7], ["/usr/bin/sudo", "-A", "-p", "Password: ", "/usr/bin/python", "-B",
                                    str(guided.ROOT / "tools/imu/gamesir_gyro_worker.py")])
        self.assertEqual(argv[7:], ["--manifest", "/home/example/a $(touch NO).json", "--output", "/home/example/with spaces"])

    def test_phases_have_reaction_buffers_and_no_return_in_motion(self):
        phases = {name: (start, seconds) for start, name, seconds, _ in guided.PHASES}
        self.assertEqual(phases["rest_before"], (0, 20))
        self.assertEqual(phases["pickup_buffer"], (20, 15))
        self.assertEqual(phases["hold_start"], (35, 5))
        self.assertEqual(phases["motion"], (40, 15))
        self.assertEqual(phases["hold_end"], (55, 5))
        self.assertEqual(phases["put_down_buffer"], (60, 15))
        self.assertEqual(phases["rest_after"], (75, 30))
        self.assertEqual(phases["finish"][0], 105)

    def test_prepare_is_metadata_only_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            output = home / "manifest.json"
            snapshot = {"constructed": "metadata-only"}
            with patch.object(guided, "home_directory", return_value=home), \
                    patch.object(guided.os, "geteuid", return_value=1000), \
                    patch.object(guided, "snapshot_iio", return_value=snapshot) as metadata, \
                    patch.object(guided, "source_hashes", return_value={"fixed": "hash"}), \
                    patch.object(guided.subprocess, "Popen", side_effect=AssertionError("no GUI or worker")):
                result = guided.prepare_manifest("saved-iio-metadata", "never-opened-node", output)
                self.assertEqual(result["snapshot"], snapshot)
                metadata.assert_called_once_with("saved-iio-metadata", "never-opened-node")
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
                self.assertEqual(json.loads(output.read_text()), result)
                with self.assertRaisesRegex(ValueError, "never replaced"):
                    guided.prepare_manifest("unused", "unused", output)

    def test_manifest_requires_current_fixed_source_hashes_and_private_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            path = home / "manifest.json"
            manifest = {"schema_version": 1, "kind": guided.MANIFEST_KIND, "snapshot": {},
                        "source_sha256": {"fixed": "old"}}
            guided.write_json(path, manifest)
            with patch.object(guided, "home_directory", return_value=home), \
                    patch.object(guided, "source_hashes", return_value={"fixed": "old"}):
                self.assertEqual(guided.load_manifest(path)[1], manifest)
                path.chmod(0o644)
                with self.assertRaisesRegex(ValueError, "private"):
                    guided.load_manifest(path)
                path.chmod(0o600)
            with patch.object(guided, "home_directory", return_value=home), \
                    patch.object(guided, "source_hashes", return_value={"fixed": "new"}):
                with self.assertRaisesRegex(ValueError, "hashes changed"):
                    guided.load_manifest(path)

    def test_symlink_and_outside_home_outputs_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home = base / "home"
            home.mkdir()
            target = base / "existing"
            target.write_text("preserve")
            link = home / "link"
            link.symlink_to(target)
            with patch.object(guided, "home_directory", return_value=home):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    guided.private_target(link)
                with self.assertRaisesRegex(ValueError, "home directory"):
                    guided.private_target(base / "outside")

    def test_root_frontend_refused_before_manifest_or_gui(self):
        with patch.object(guided.os, "geteuid", return_value=0), \
                patch.object(guided, "load_manifest", side_effect=AssertionError("not reached")), \
                patch.object(guided.subprocess, "Popen", side_effect=AssertionError("no GUI")):
            with self.assertRaisesRegex(ValueError, "without sudo"):
                guided.run_measurement("unused", 1, "marks", "unused")
            with self.assertRaisesRegex(ValueError, "without sudo"):
                guided.prepare_manifest("unused", "unused", "unused")

    def test_hash_map_reads_exact_fixed_helpers_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in guided.SOURCE_FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("constructed source " + name)
            with patch.object(guided, "ROOT", root):
                hashes = guided.source_hashes()
                self.assertEqual(tuple(hashes), guided.SOURCE_FILES)
                self.assertTrue(all(len(value) == 64 for value in hashes.values()))
                path = root / guided.SOURCE_FILES[0]
                path.unlink()
                path.symlink_to(root / guided.SOURCE_FILES[1])
                with self.assertRaisesRegex(ValueError, "symlinked"):
                    guided.source_hashes()


class RecordedReference(unittest.TestCase):
    def test_boundaries_are_existing_frames_inside_actual_cues_and_reset_excluded(self):
        samples = observations(1_000_000_000)
        cues = cue_fixture(1_000_000_000, lag_ns=20_000_000)
        metadata = guided.reference_metadata(samples, cues, 2, "right angle on paper", confirmed=True)
        window = metadata["windows"][0]
        self.assertEqual(window["label"], "yaw90left-repetition-2")
        self.assertEqual(window["motion"], [36_100_000_000, 61_000_000_000])
        self.assertEqual(window["physical_axis"], "Z")
        self.assertEqual(window["known_angle_deg"], 90)
        stamps = {row["timestamp_ns"] for row in samples}
        for name in ("rest_before", "motion", "rest_after"):
            self.assertTrue(set(window[name]) <= stamps)
            original = metadata["guidance"]["intervals"][name]["actual_cue_bounds_ns"]
            self.assertGreaterEqual(window[name][0], original[0])
            self.assertLessEqual(window[name][1], original[1])
        self.assertTrue(metadata["guidance"]["reset_excluded"])
        self.assertFalse(metadata["calibration_verified"])
        self.assertFalse(metadata["sdl_runtime_enable"])

    def test_reference_requires_human_confirmation_and_external_description(self):
        samples, cues = observations(1_000_000_000), cue_fixture(1_000_000_000)
        for confirmed in (False, None, 1):
            with self.subTest(confirmed=confirmed), self.assertRaisesRegex(ValueError, "human"):
                guided.reference_metadata(samples, cues, 1, "marks", confirmed=confirmed)
        with self.assertRaisesRegex(ValueError, "external"):
            guided.reference_metadata(samples, cues, 1, " ", confirmed=True)

    def test_missing_duplicate_and_empty_boundary_cues_rejected(self):
        samples, cues = observations(1_000_000_000), cue_fixture(1_000_000_000)
        for malformed in (cues[:-1], cues + [cues[0]], cue_fixture(999_000_000_000)):
            with self.subTest(cues=malformed), self.assertRaises(ValueError):
                guided.reference_metadata(samples, malformed, 1, "marks", confirmed=True)

    def test_all_five_hypotheses_and_no_selected_profile(self):
        samples, cues = observations(1_000_000_000), cue_fixture(1_000_000_000)
        metadata = guided.reference_metadata(samples, cues, 1, "external square", confirmed=True)
        report = guided.analyze_reference(samples, metadata, guided.MAX_GAP_NS)
        self.assertEqual([p["assumed_range_dps"] for p in report["windows"][0]["profiles"]],
                         [125, 250, 500, 1000, 2000])
        self.assertTrue(all(p["selected_for_runtime"] is False for p in report["windows"][0]["profiles"]))
        self.assertIsNone(report["axis_mapping_hypothesis"])
        self.assertFalse(report["sdl_runtime_enable"])
        self.assertEqual(report["windows"][0]["raw_integral_count_seconds"][:2], [0, 0])

    def test_any_packet_gap_rejects_full_reference_without_discarding_interval(self):
        samples, cues = observations(1_000_000_000), cue_fixture(1_000_000_000)
        metadata = guided.reference_metadata(samples, cues, 1, "external square", confirmed=True)
        del samples[22]  # Outside the actual rotation; still invalidates the stream.
        with self.assertRaisesRegex(ValueError, "counter gap"):
            guided.analyze_reference(samples, metadata, guided.MAX_GAP_NS)


class CaptureEvidence(unittest.TestCase):
    def test_complete_original_bundle_verified_independently(self):
        with tempfile.TemporaryDirectory() as temporary:
            capture = Path(temporary) / "capture"
            capture_fixture(capture, 77)
            report = guided.verify_capture(capture, 77)
            self.assertTrue(report["sha256_verified"])
            self.assertEqual(set(report["files"]), set(guided.CAPTURE_FILES))

    def test_wrong_hash_preserves_original_and_refuses_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            capture = Path(temporary) / "capture"
            capture_fixture(capture, 77)
            original = capture / "scans.bin"
            original.write_bytes(b"deliberately modified fake file")
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                guided.verify_capture(capture, 77)
            self.assertEqual(original.read_bytes(), b"deliberately modified fake file")

    def test_extra_file_incomplete_hash_set_and_wrong_session_rejected(self):
        for scenario in ("extra", "missing_hash", "wrong_clock"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                capture = Path(temporary) / "capture"
                capture_fixture(capture, 77)
                if scenario == "extra":
                    guided.write_json(capture / "extra.json", {})
                elif scenario == "missing_hash":
                    sums = capture / "SHA256SUMS"
                    sums.write_text("\n".join(sums.read_text().splitlines()[:-1]) + "\n")
                with self.assertRaises(ValueError):
                    guided.verify_capture(capture, 78 if scenario == "wrong_clock" else 77)

    def test_symlink_and_unrestored_report_fail_even_with_plausible_checksums(self):
        for scenario in ("symlink", "unrestored"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                capture = Path(temporary) / "capture"
                capture_fixture(capture, 77)
                if scenario == "symlink":
                    (capture / "scans.bin").unlink()
                    (capture / "scans.bin").symlink_to(capture / "layout.json")
                else:
                    path = capture / "report.json"
                    report = json.loads(path.read_text())
                    report["restored"] = False
                    path.write_text(json.dumps(report))
                    (capture / "SHA256SUMS").write_text("".join(
                        f"{hashlib.sha256((capture / name).read_bytes()).hexdigest()}  {name}\n"
                        for name in guided.CAPTURE_FILES))
                with self.assertRaises(ValueError):
                    guided.verify_capture(capture, 77)


class PhaseClock(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        FakeCues.clock = self.clock
        FakeCues.fail_at = None
        self.worker = SimpleNamespace(pending=[], pulse=lambda: None)

    def test_all_phases_local_and_exactly_one_rotation(self):
        cues = FakeCues()
        with patch.object(guided.time, "monotonic_ns", self.clock.monotonic_ns), \
                patch.object(guided.time, "sleep", self.clock.sleep):
            guided.run_phases(self.worker, cues, self.clock.now)
        self.assertEqual([r["event"] for r in cues.rows], [p[1] for p in guided.PHASES])
        self.assertEqual(sum(r["event"] == "motion" for r in cues.rows), 1)
        self.assertEqual(self.clock.now, 1_105_000_000_000)
        self.assertTrue(all(row["monotonic_ns"] == row["scheduled_monotonic_ns"] for row in cues.rows))

    def test_delayed_first_cue_stops_without_catchup(self):
        cues = FakeCues()
        start = self.clock.now - 3_000_000_000
        with patch.object(guided.time, "monotonic_ns", self.clock.monotonic_ns), \
                self.assertRaisesRegex(ValueError, "delayed"):
            guided.run_phases(self.worker, cues, start)
        self.assertEqual(cues.rows, [])

    def test_skipped_phase_stops_without_playing_multiple_cues(self):
        cues = FakeCues()
        original = cues.show

        def jump(*args, **kwargs):
            original(*args, **kwargs)
            self.clock.now += 40_000_000_000

        cues.show = jump
        with patch.object(guided.time, "monotonic_ns", self.clock.monotonic_ns), \
                self.assertRaisesRegex(ValueError, "missed"):
            guided.run_phases(self.worker, cues, self.clock.now)
        self.assertEqual([r["event"] for r in cues.rows], ["rest_before"])

    def test_early_worker_finish_stops_cues(self):
        self.worker.pending = [{"event": "finished"}]
        cues = FakeCues()
        with self.assertRaisesRegex(ValueError, "before all"):
            guided.run_phases(self.worker, cues, self.clock.now)
        self.assertEqual(cues.rows, [])

    def test_prepare_wait_pumps_heartbeat_and_never_sends_go(self):
        calls = []
        self.worker.pulse = lambda: calls.append(self.clock.now)
        with patch.object(guided.time, "monotonic_ns", self.clock.monotonic_ns), \
                patch.object(guided.time, "sleep", self.clock.sleep):
            guided.wait_seconds(30, FakeCues(), self.worker)
        self.assertEqual(self.clock.now, 1_030_000_000_000)
        self.assertLessEqual(max(b - a for a, b in zip(calls, calls[1:])), 50_000_000)


class QualitativeAxes(unittest.TestCase):
    def test_plan_is_device_free_and_requires_separate_go_without_angle(self):
        with patch.object(guided, "snapshot_iio", side_effect=AssertionError("no metadata access")), \
                patch.object(guided.subprocess, "Popen", side_effect=AssertionError("no GUI or worker")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(guided.main(["plan-axis-left"]), 0)
        plan = json.loads(output.getvalue())
        self.assertFalse(plan["hardware_authorized"])
        self.assertFalse(plan["known_angle_required"])
        self.assertFalse(plan["automatic_next_repetition"])
        self.assertTrue(plan["local_go_required_each_time"])
        self.assertEqual(plan["prepare_seconds"], 30)
        self.assertNotIn("90°", json.dumps(plan, ensure_ascii=False))

    def test_axis_cues_keep_worker_deadline_and_single_motion(self):
        self.assertEqual([p[:3] for p in guided.AXIS_PHASES], [p[:3] for p in guided.PHASES])
        self.assertEqual(sum(p[1] == "motion" for p in guided.AXIS_PHASES), 1)
        self.assertNotIn("90°", " ".join(p[3] for p in guided.AXIS_PHASES))

    def test_raw_sign_response_excludes_large_pickup_and_putdown(self):
        samples = observations(1_000_000_000)
        # A different raw channel and negative response; no presumed G2/Z map.
        for sample in samples:
            if sample["gyro_raw"] == [0, 0, 100]:
                sample["gyro_raw"] = [-321, 0, 0]
        result = guided.analyze_axis_observation(samples, cue_fixture(1_000_000_000), 1, confirmed=True)
        channels = result["gyro_channels"]
        self.assertEqual(channels[0]["motion_min_delta_raw"], -321)
        self.assertLess(channels[0]["motion_mean_delta_raw"], 0)
        self.assertEqual(channels[1]["motion_mean_abs_delta_raw"], 0)
        self.assertEqual(channels[2]["motion_mean_abs_delta_raw"], 0)
        self.assertFalse(result["physical_axis_mapping_verified"])
        self.assertFalse(result["scale_selected"])
        self.assertNotIn("known_angle_deg", json.dumps(result))

    def test_no_motion_does_not_invent_a_channel_or_mapping(self):
        samples = observations(1_000_000_000)
        for sample in samples:
            sample["gyro_raw"] = [7, -4, 20]
        result = guided.analyze_axis_observation(samples, cue_fixture(1_000_000_000), 1, confirmed=True)
        self.assertTrue(all(c["motion_mean_abs_delta_raw"] == 0 for c in result["gyro_channels"]))
        self.assertFalse(result["physical_axis_mapping_verified"])

    def test_confirmation_gaps_and_bad_cues_rejected(self):
        samples, cues = observations(1_000_000_000), cue_fixture(1_000_000_000)
        with self.assertRaisesRegex(ValueError, "human-confirmed"):
            guided.analyze_axis_observation(samples, cues, 1, confirmed=False)
        for malformed in (cues[:-1], cues + [cues[0]], list(reversed(cues))):
            with self.subTest(cues=malformed), self.assertRaisesRegex(ValueError, "ordered axis cues"):
                guided.analyze_axis_observation(samples, malformed, 1, confirmed=True)
        with self.assertRaisesRegex(ValueError, "counter gap"):
            guided.analyze_axis_observation(samples[:2] + samples[3:], cues, 1, confirmed=True)


class WorkerProtocol(unittest.TestCase):
    def setUp(self):
        self.command_reader, command_writer = os.pipe()
        stdout_reader, self.event_writer = os.pipe()
        self.process = SimpleNamespace(stdin=os.fdopen(command_writer, "wb", buffering=0),
                                       stdout=os.fdopen(stdout_reader, "rb", buffering=0),
                                       poll=lambda: None, wait=lambda **kwargs: 0)
        self.link = guided.WorkerLink(self.process)
        os.set_blocking(self.command_reader, False)

    def tearDown(self):
        self.process.stdin.close()
        self.process.stdout.close()
        os.close(self.command_reader)
        os.close(self.event_writer)

    def event(self, event):
        os.write(self.event_writer, json.dumps(event).encode() + b"\n")

    def test_ordered_events_and_quarter_second_heartbeat(self):
        with patch.object(guided.time, "monotonic_ns", side_effect=[1_000_000_000, 1_100_000_000, 1_250_000_000]):
            self.event({"event": "ready"})
            self.link.pulse()
            self.assertEqual(self.link.pop(), {"event": "ready"})
            self.link.pulse()
            self.link.pulse()
        self.assertEqual(os.read(self.command_reader, 4096), b"PING\nPING\n")
        self.event({"event": "capture_started", "monotonic_ns": 50})
        self.link.pulse()
        self.assertEqual(self.link.pop()["monotonic_ns"], 50)
        self.event({"event": "finished", "passed": True, "restored": True})
        self.link.pulse()
        self.assertTrue(self.link.finished["restored"])

    def test_unknown_duplicate_and_out_of_order_events_fail(self):
        for value in ({"event": "random"}, {"event": "capture_started", "monotonic_ns": 2}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.event(value)
                self.link.pulse()
        self.event({"event": "ready"})
        self.link.pulse()
        self.event({"event": "ready"})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.link.pulse()

    def test_finished_requires_explicit_boolean_rollback_not_truthy(self):
        self.event({"event": "finished", "passed": True, "restored": 1})
        with self.assertRaisesRegex(ValueError, "rollback"):
            self.link.pulse()

    def test_oversized_and_partial_event_lines_rejected(self):
        self.link.buffer = bytearray(b"x" * guided.MAX_EVENT_BYTES)
        os.write(self.event_writer, b"x")
        with self.assertRaisesRegex(ValueError, "too large"):
            self.link.pulse()
        self.link.buffer = bytearray(b'{"event":')
        os.close(self.event_writer)
        self.event_writer = os.open(os.devnull, os.O_WRONLY)
        with self.assertRaisesRegex(ValueError, "partial final"):
            self.link.pulse()

    def test_stop_and_eof_wait_for_rollback_never_kill_root(self):
        self.event({"event": "finished", "passed": False, "restored": True, "failure": "cancelled before Go"})
        result = self.link.stop_and_wait()
        self.assertTrue(result["restored"])
        self.assertEqual(result["cleanup_errors"], [])
        self.assertEqual(os.read(self.command_reader, 4096), b"STOP\n")
        self.assertTrue(self.process.stdin.closed)
        self.assertIn("cancelled", result["worker_result"]["failure"])

    def test_arbitrary_commands_refused(self):
        for command in ("USB", "GO\nSTOP", "", "rm -rf"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.link.send(command)

    def test_stop_during_setup_drains_late_started_event_until_final_restore(self):
        clock = Clock()
        self.event({"event": "ready"})
        self.link.pulse()
        emitted = []

        def step(seconds):
            clock.sleep(seconds)
            if not emitted:
                self.event({"event": "capture_started", "monotonic_ns": clock.now})
                emitted.append("started")
            elif len(emitted) == 1:
                self.event({"event": "finished", "passed": False, "restored": True,
                            "failure": "STOP received during setup"})
                emitted.append("finished")

        with patch.object(guided.time, "monotonic_ns", clock.monotonic_ns), \
                patch.object(guided.time, "sleep", step):
            result = self.link.stop_and_wait()
        self.assertEqual(emitted, ["started", "finished"])
        self.assertTrue(result["restored"])
        self.assertEqual(result["cleanup_errors"], [])
        self.assertIn("STOP received", result["worker_result"]["failure"])
        self.assertEqual(os.read(self.command_reader, 4096), b"PING\nSTOP\n")


class EndToEndFakeRun(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        self.clock = Clock()
        FakeCues.clock, FakeCues.fail_at, FakeCues.instances = self.clock, None, []
        self.links = []

    def tearDown(self):
        self.temporary.cleanup()

    def execute(self, answers, *, cue_failure=None, restored=True, corrupt_capture=False, axis_only=False):
        output = self.home / "repetition-2"
        clock, links = self.clock, self.links
        fake_process = SimpleNamespace(wait=lambda **kwargs: 0)
        popen_calls = []

        def popen(argv, **kwargs):
            popen_calls.append((argv, kwargs))
            # First sample starts after the separately timed 30-second preparation.
            capture = output / "capture"
            capture_fixture(capture, clock.now + 30_000_000_000)
            if corrupt_capture:
                (capture / "scans.bin").write_bytes(b"modified fake evidence")
            return fake_process

        class Link:
            def __init__(self, process):
                self.pending, self.sent = [], []
                self.finished = None
                links.append(self)

            def pulse(self, **kwargs):
                pass

            def send(self, command):
                self.sent.append(command)

            def close_input(self):
                pass

            def await_event(self, name, **kwargs):
                if name == "capture_started":
                    return {"event": name, "monotonic_ns": clock.now}
                if name == "finished":
                    clock.sleep(3)
                    self.finished = {"event": name, "passed": True, "restored": restored}
                    return self.finished
                return {"event": name}

            def stop_and_wait(self):
                self.sent.append("STOP")
                return {"restored": restored, "cleanup_errors": [], "worker_result": self.finished}

        FakeCues.fail_at = cue_failure
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(guided.os, "geteuid", return_value=1000))
            stack.enter_context(patch.object(guided, "home_directory", return_value=self.home))
            stack.enter_context(patch.object(guided, "load_manifest", return_value=(self.home / "manifest.json", {"constructed": True})))
            stack.enter_context(patch.object(guided, "GuidedCues", FakeCues))
            stack.enter_context(patch.object(guided, "WorkerLink", Link))
            stack.enter_context(patch.object(guided, "question", side_effect=answers))
            stack.enter_context(patch.object(guided.subprocess, "Popen", side_effect=popen))
            stack.enter_context(patch.object(guided.time, "monotonic_ns", self.clock.monotonic_ns))
            stack.enter_context(patch.object(guided.time, "sleep", self.clock.sleep))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if axis_only:
                stack.enter_context(patch.object(guided, "reference_metadata", side_effect=AssertionError("no angle metadata")))
                stack.enter_context(patch.object(guided, "analyze_reference", side_effect=AssertionError("no angle analysis")))
            result = guided.run_measurement(self.home / "manifest.json", 2,
                                           None if axis_only else "external paper square", output, axis_only=axis_only)
        return result, output, json.loads((output / "report.json").read_text()), popen_calls

    def test_axis_run_is_one_go_no_angle_profile_or_reference_file(self):
        code, output, report, calls = self.execute([True, True], axis_only=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["kind"], "guided_axis_left")
        self.assertTrue(report["motion_confirmed"])
        self.assertFalse(report["reference_confirmed"])
        self.assertFalse(report["calibration_verified"])
        self.assertFalse(report["scale_selected"])
        self.assertEqual(self.links[0].sent, ["GO", "STOP"])
        self.assertEqual(len(calls), 1)
        self.assertFalse((output / "reference.json").exists())
        analysis = json.loads((output / "analysis.json").read_text())
        self.assertEqual(analysis["kind"], "qualitative_yaw_left_observation")
        self.assertFalse(analysis["physical_axis_mapping_verified"])
        self.assertNotIn("90°", (output / "cues.jsonl").read_text())
        self.assertEqual(self.clock.now, 1_153_000_000_000)

    def test_axis_missed_motion_keeps_capture_without_analysis(self):
        code, output, report, _ = self.execute([True, False], axis_only=True)
        self.assertEqual(code, 0)
        self.assertFalse(report["motion_confirmed"])
        self.assertFalse(report["analysis_created"])
        self.assertTrue((output / "capture/scans.bin").exists())
        self.assertFalse((output / "analysis.json").exists())

    def test_axis_cancel_before_go_does_not_send_go(self):
        code, output, report, _ = self.execute([False], axis_only=True)
        self.assertEqual(code, 1)
        self.assertNotIn("GO", self.links[0].sent)
        self.assertTrue(report["cleanup"]["restored"])
        self.assertFalse((output / "analysis.json").exists())

    def test_axis_failed_restore_blocks_analysis(self):
        code, output, report, _ = self.execute([True], restored=False, axis_only=True)
        self.assertEqual(code, 1)
        self.assertFalse(report["motion_confirmed"])
        self.assertFalse(report["cleanup"]["restored"])
        self.assertFalse((output / "analysis.json").exists())

    def test_one_go_one_left_rotation_and_private_analysis_bundle(self):
        code, output, report, calls = self.execute([True, True])
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        self.assertTrue(report["reference_confirmed"])
        self.assertEqual(self.links[0].sent, ["GO", "STOP"])
        events = [row["event"] for row in FakeCues.instances[0].rows]
        self.assertEqual(events, ["prepare", *[p[1] for p in guided.PHASES], "reset_outside_analysis"])
        self.assertEqual(events.count("motion"), 1)
        self.assertEqual(self.clock.now, 1_153_000_000_000)  # 30+108+15; no next repetition.
        analysis = json.loads((output / "analysis.json").read_text())
        self.assertFalse(analysis["calibration_verified"])
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
        for name in ("report.json", "analysis.json", "reference.json", "cues.jsonl", "worker.stderr.log", "SHA256SUMS"):
            self.assertEqual(stat.S_IMODE((output / name).stat().st_mode), 0o600)
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0][1]["shell"])
        self.assertEqual(calls[0][1]["env"]["SUDO_ASKPASS"], "/usr/bin/ksshaskpass")

    def test_declined_go_opens_no_capture_and_requests_rollback(self):
        code, output, report, _ = self.execute([False])
        self.assertEqual(code, 1)
        self.assertIn("Go declined", report["failure"])
        self.assertNotIn("GO", self.links[0].sent)
        self.assertEqual(FakeCues.instances[0].rows, [])
        self.assertTrue(report["cleanup"]["restored"])
        self.assertFalse((output / "analysis.json").exists())

    def test_unconfirmed_reference_keeps_raw_data_without_analysis(self):
        code, output, report, _ = self.execute([True, False])
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])
        self.assertFalse(report["reference_confirmed"])
        self.assertFalse(report["analysis_created"])
        self.assertTrue((output / "capture/observations.jsonl").exists())
        self.assertFalse((output / "reference.json").exists())
        self.assertFalse((output / "analysis.json").exists())

    def test_cue_failure_stops_and_retains_original_failure(self):
        code, output, report, _ = self.execute([True], cue_failure="motion")
        self.assertEqual(code, 1)
        self.assertIn("constructed KDE cue failure", report["failure"])
        self.assertEqual(self.links[0].sent, ["GO", "STOP"])
        self.assertTrue(report["cleanup"]["restored"])
        self.assertFalse((output / "analysis.json").exists())
        self.assertTrue(FakeCues.instances[0].closed)

    def test_failed_restore_never_allows_reference_confirmation(self):
        code, output, report, _ = self.execute([True], restored=False)
        self.assertEqual(code, 1)
        self.assertFalse(report["passed"])
        self.assertFalse(report["reference_confirmed"])
        self.assertFalse(report["cleanup"]["restored"])
        self.assertFalse((output / "analysis.json").exists())

    def test_bad_checksum_blocks_confirmation_and_keeps_originals(self):
        code, output, report, _ = self.execute([True], corrupt_capture=True)
        self.assertEqual(code, 1)
        self.assertIn("SHA256 mismatch", report["failure"])
        self.assertFalse(report["reference_confirmed"])
        self.assertTrue(report["cleanup"]["restored"])
        self.assertEqual((output / "capture/scans.bin").read_bytes(), b"modified fake evidence")
        self.assertFalse((output / "analysis.json").exists())

    def test_secondary_finalization_failure_keeps_original_cue_failure(self):
        original_finish = guided.Bundle.finish

        def finish_then_fail(bundle, *args, **kwargs):
            original_finish(bundle, *args, **kwargs)
            raise OSError("constructed finalization failure")

        with patch.object(guided.Bundle, "finish", finish_then_fail):
            code, output, _, _ = self.execute([True], cue_failure="motion")
        self.assertEqual(code, 1)
        note = json.loads((output / "frontend-finalization-error.json").read_text())
        self.assertIn("constructed KDE cue failure", note["failure"])
        self.assertTrue(note["cleanup"]["restored"])
        self.assertTrue(any("constructed finalization failure" in error for error in note["finalization_errors"]))


if __name__ == "__main__":
    unittest.main()
