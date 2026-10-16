#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Experimental IMU checks against constructed data only; never open devices."""
import copy
from fractions import Fraction
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gamesir_imu_diagnostic", ROOT / "tools/imu/gamesir_imu_diagnostic.py")
diag = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = diag
SPEC.loader.exec_module(diag)


def record(timestamp_us=1000000, *, gyro=(100, -200, 300), accel=(0, 0, 8192)):
    """Own canonical telemetry bytes with explicit synthetic provenance."""
    payload = bytearray(64)
    payload[:5] = bytes.fromhex("1000013ce0")
    struct.pack_into("<6h", payload, 17, *gyro, *accel)
    return {
        "schema_version": 1,
        "source": {"kind": "synthetic", "id": "constructed-imu-diagnostic-v1"},
        "session": "synthetic-motion-window",
        "timestamp_us": timestamp_us,
        "timebase": "synthetic",
        "device": {"vid": "3537", "pid": "109c", "bus": 1,
                   "address": 4, "interface": 0},
        "endpoint": "82", "stage": "complete", "status": 0,
        "reported_length": 64, "capture_truncated": False,
        "data_hex": payload.hex(),
    }


def sample(timestamp_ns=1000000000, *, gyro=(0, 0, 0), accel=(0, 0, 8192),
           coherent=True):
    return {"timestamp_ns": timestamp_ns, "gyro_raw": list(gyro),
            "accel_raw": list(accel), "coherent": coherent,
            "timebase": "synthetic" if coherent else "host_monotonic_read_window"}


class ProfilesAndConversion(unittest.TestCase):
    def test_all_five_factors_are_exact_separate_hypotheses(self):
        self.assertEqual(diag.PROFILES, {
            125: Fraction(7, 1600), 250: Fraction(7, 800),
            500: Fraction(7, 400), 1000: Fraction(7, 200),
            2000: Fraction(7, 100),
        })
        self.assertTrue(all(type(value) is Fraction for value in diag.PROFILES.values()))

    def test_each_profile_converts_both_signs_and_preserves_axis_order(self):
        for profile, multiplier in diag.PROFILES.items():
            with self.subTest(profile=profile):
                result = diag.convert([1600, -800, 400], [8192, 0, -8192], profile)
                expected = [float(multiplier * value) for value in (1600, -800, 400)]
                self.assertTrue(result["experiment"])
                self.assertEqual(result["gyro_raw"], [1600, -800, 400])
                self.assertEqual(result["accel_raw"], [8192, 0, -8192])
                for actual, degrees in zip(result["test_values"]["gyro_dps"], expected):
                    self.assertAlmostEqual(actual, degrees, places=12)
                for actual, degrees in zip(result["test_values"]["gyro_rad_s"], expected):
                    self.assertAlmostEqual(actual, degrees * math.pi / 180, places=12)
                self.assertEqual(result["test_values"]["accel_g"], [1.0, 0.0, -1.0])
                self.assertEqual(result["test_values"]["accel_m_s2"], [9.80665, 0.0, -9.80665])

    def test_signed_int16_extremes_are_not_clipped_or_unsigned(self):
        result = diag.convert([-32768, 32767, -1], [32767, -32768, -1], 2000)
        self.assertEqual(result["test_values"]["gyro_dps"], [-2293.76, 2293.69, -0.07])
        self.assertEqual(result["test_values"]["accel_g"], [32767 / 8192, -4.0, -1 / 8192])

    def test_explicit_raw_count_bias_is_subtracted_before_conversion(self):
        result = diag.convert([100, -200, 300], [0, 0, 8192], 250,
                              bias=[0.5, -1.5, 300])
        for actual, expected in zip(result["test_values"]["gyro_dps"],
                                    [99.5 * 0.00875, -198.5 * 0.00875, 0.0]):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertEqual(result["gyro_raw"], [100, -200, 300])

    def test_conversion_does_not_mutate_or_alias_raw_vectors(self):
        gyro, accel, bias = [100, -200, 300], [0, 0, 8192], [1.0, 2.0, 3.0]
        before = copy.deepcopy([gyro, accel, bias])
        result = diag.convert(gyro, accel, 500, bias=bias)
        self.assertEqual([gyro, accel, bias], before)
        gyro[0], accel[2], bias[0] = 7, 8, 9
        self.assertEqual(result["gyro_raw"], before[0])
        self.assertEqual(result["accel_raw"], before[1])

    def test_profile_is_required_and_unknown_range_cannot_be_selected(self):
        with self.assertRaises(TypeError):
            diag.convert([0, 0, 0], [0, 0, 8192])
        for profile in (None, 0, 124, 126, 4000, "250", True):
            with self.subTest(profile=profile), self.assertRaises((TypeError, ValueError)):
                diag.convert([0, 0, 0], [0, 0, 8192], profile)

    def test_raw_vectors_require_exactly_three_signed_int16_integers(self):
        invalid = ([], [0, 0], [0, 0, 0, 0], [32768, 0, 0], [-32769, 0, 0],
                   [True, 0, 0], [1.0, 0, 0], ["1", 0, 0], [None, 0, 0])
        for vector in invalid:
            for channel in ("gyro", "accel"):
                with self.subTest(vector=vector, channel=channel):
                    args = [vector, [0, 0, 0]] if channel == "gyro" else [[0, 0, 0], vector]
                    with self.assertRaises((TypeError, ValueError)):
                        diag.convert(*args, 250)

    def test_bias_requires_three_finite_numbers(self):
        for bias in ([], [0, 0], [0, 0, 0, 0], [math.nan, 0, 0],
                     [0, math.inf, 0], [0, 0, -math.inf], ["zero", 0, 0], [True, 0, 0]):
            with self.subTest(bias=bias), self.assertRaises((TypeError, ValueError)):
                diag.convert([0, 0, 0], [0, 0, 8192], 250, bias=bias)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-imu-replay-")
        self.root = Path(self.temporary.name)
        self.path = self.root / "constructed.jsonl"

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, rows):
        self.path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return self.path

    def test_existing_parser_wire_layout_and_timebase_are_retained(self):
        path = self.write([record(1234567, gyro=(-32768, -1, 32767), accel=(1, 8192, -8)),
                           record(1250567, gyro=(4, 5, 6), accel=(7, 8, 9))])
        before = path.read_bytes()
        samples, metadata = diag.replay(path)
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["timestamp_ns"], 1234567000)
        self.assertEqual(samples[0]["gyro_raw"], [-32768, -1, 32767])
        self.assertEqual(samples[0]["accel_raw"], [1, 8192, -8])
        self.assertTrue(samples[0]["coherent"])
        self.assertEqual(samples[0]["timebase"], "synthetic")
        self.assertEqual(path.read_bytes(), before)
        self.assertIsInstance(metadata, dict)

    def test_unsuccessful_incomplete_truncated_foreign_records_are_skipped(self):
        good = record(1000000)
        rejected = []
        for update in ({"status": -32}, {"stage": "submit"}, {"stage": "error"},
                       {"capture_truncated": True}, {"reported_length": 65},
                       {"endpoint": "02"}):
            row = copy.deepcopy(good)
            row.update(update)
            rejected.append(row)
        for device_update in ({"vid": "1234"}, {"pid": "ffff"}, {"interface": 1}):
            row = copy.deepcopy(good)
            row["device"].update(device_update)
            rejected.append(row)
        short = copy.deepcopy(good)
        short["data_hex"] = short["data_hex"][:122]
        short["reported_length"] = 61
        rejected.append(short)
        samples, metadata = diag.replay(self.write([good, *rejected, record(1016000)]))
        self.assertEqual(len(samples), 2)
        self.assertEqual(metadata["record_counts"], {
            "records": 12, "other_device_or_endpoint": 4,
            "not_successful_completion": 3, "truncated_or_length_mismatch": 2,
            "not_full_imu_telemetry": 1,
        })

    def test_different_accepted_telemetry_streams_are_never_merged(self):
        changes = (("session", "other-session"), ("source_id", "another-source"),
                   ("address", 5), ("bus", 2), ("pid", "105e"))
        for field, value in changes:
            other = record(1016000)
            if field in ("address", "bus", "pid"):
                other["device"][field] = value
            elif field == "source_id":
                other["source"]["id"] = value
            else:
                other[field] = value
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                diag.replay(self.write([record(), other]))

    def test_nonmonotonic_and_duplicate_accepted_timestamps_are_rejected(self):
        for timestamp in (1000000, 999999):
            with self.subTest(timestamp=timestamp), self.assertRaises((TypeError, ValueError)):
                diag.replay(self.write([record(1000000), record(timestamp)]))

    def test_empty_or_only_rejected_file_has_no_usable_samples(self):
        foreign = record()
        foreign["device"]["vid"] = "1234"
        for rows in ([], [foreign]):
            with self.subTest(rows=rows), self.assertRaises((TypeError, ValueError)):
                diag.replay(self.write(rows))

    def test_duplicate_json_keys_are_not_silently_overwritten(self):
        text = json.dumps(record())
        self.path.write_text(text[:-1] + ', "timestamp_us": 2000000}\n', encoding="utf-8")
        with self.assertRaises((TypeError, ValueError)):
            diag.replay(self.path)


class AnalysisTests(unittest.TestCase):
    def test_synthetic_known_angles_both_signs_on_each_axis_under_every_profile(self):
        # Constant speed, independently specified angle/duration; synthetic
        # evidence exercises integration, never chooses a real sensor range.
        for profile, gain in diag.PROFILES.items():
            speed = float(gain * 1600)
            for axis in range(3):
                for degrees in (-180, -90, 90, 180):
                    vector = [0, 0, 0]
                    vector[axis] = 1600 if degrees > 0 else -1600
                    duration_ns = round(abs(degrees) / speed * 1e9)
                    rows = [sample(0, gyro=vector), sample(duration_ns // 2, gyro=vector),
                            sample(duration_ns, gyro=vector)]
                    result = diag.analyze(rows, profile)
                    with self.subTest(profile=profile, axis=axis, degrees=degrees):
                        for actual_axis, angle in enumerate(result["angle_integration_deg"]):
                            self.assertAlmostEqual(angle, degrees if actual_axis == axis else 0, places=6)
                        self.assertFalse(result["selected_as_actual_hardware_profile"])

    def test_synthetic_six_gravity_poses_retain_signs_without_claiming_housing_map(self):
        for axis in range(3):
            for sign in (-1, 1):
                acceleration = [0, 0, 0]
                acceleration[axis] = sign * 8192
                converted = diag.convert([0, 0, 0], acceleration, 125)
                self.assertEqual(converted["test_values"]["accel_g"],
                                 [sign if i == axis else 0 for i in range(3)])
                result = diag.analyze([sample(accel=acceleration)], 125)
                self.assertEqual(result["accel_norm_g_stats"]["mean"], 1)
                self.assertFalse(result["calibration_verified"])

    def test_no_analysis_claims_real_calibration_or_known_packet_loss(self):
        result = diag.analyze([sample(), sample(1016000000)], 250)
        self.assertEqual(result["sample_count"], 2)
        self.assertFalse(result["calibration_verified"])
        self.assertFalse(result["packet_loss_known"])
        self.assertIn("timing", result)
        self.assertIn("gyro_dps_stats", result)
        self.assertIn("accel_norm_g_stats", result)

    def test_iio_attribute_snapshots_must_not_be_integrated(self):
        rows = [sample(1000000000, gyro=(1000, 0, 0), coherent=False),
                sample(2000000000, gyro=(1000, 0, 0), coherent=False)]
        result = diag.analyze(rows, 250)
        self.assertIsNone(result["angle_integration_deg"])
        self.assertFalse(result["calibration_verified"])

    def test_analysis_preserves_original_samples_and_physical_axis_order(self):
        rows = [sample(gyro=(10, -20, 30)), sample(1016000000, gyro=(10, -20, 30))]
        before = copy.deepcopy(rows)
        result = diag.analyze(rows, 250)
        self.assertEqual(rows, before)
        self.assertEqual(len(result["gyro_dps_stats"]), 3)
        for stats, value in zip(result["gyro_dps_stats"], [0.0875, -0.175, 0.2625]):
            self.assertAlmostEqual(stats["mean"], value, places=12)
            self.assertEqual(stats["std_population"], 0.0)
            self.assertAlmostEqual(stats["min"], value, places=12)
            self.assertAlmostEqual(stats["max"], value, places=12)
        self.assertEqual(result["accel_norm_g_stats"]["mean"], 1.0)

    def test_large_host_time_gap_is_reported_and_excluded_from_illustrative_integral(self):
        rows = [sample(stamp * 1000000000, gyro=(800, -800, 0)) for stamp in (0, 1, 2, 12, 13)]
        result = diag.analyze(rows, 250)
        timing = result["timing"]
        self.assertEqual(timing["median_interval_ns"], 1000000000)
        self.assertEqual(timing["max_interval_ns"], 10000000000)
        self.assertEqual(timing["gap_candidates_over_2x_median"], 1)
        self.assertEqual(timing["gap_intervals_excluded_from_integral"], 1)
        self.assertTrue(timing["gap_threshold_is_heuristic_not_packet_loss"])
        self.assertIsNone(timing["internal_sensor_rate_hz"])
        self.assertEqual(timing["observed_span_ns"], 13000000000)
        self.assertEqual(timing["integral_covered_ns"], 3000000000)
        self.assertEqual(timing["integral_excluded_ns"], 10000000000)
        self.assertAlmostEqual(timing["integral_coverage_fraction"], 3 / 13)
        for actual, expected in zip(result["angle_integration_deg"], (21.0, -21.0, 0.0)):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertIn("synthetic", result["angle_integration_status"])
        self.assertIn("partial", result["angle_integration_status"])
        self.assertFalse(result["packet_loss_known"])
        self.assertFalse(result["calibration_verified"])

    def test_single_sample_retains_stats_without_inventing_timing_or_rotation(self):
        result = diag.analyze([sample()], 250)
        self.assertIsNone(result["timing"]["median_interval_ns"])
        self.assertIsNone(result["timing"]["max_interval_ns"])
        self.assertIsNone(result["angle_integration_deg"])

    def test_mixed_timebases_are_rejected_even_when_timestamps_increase(self):
        rows = [sample(), sample(1016000000)]
        rows[1]["timebase"] = "host_capture"
        with self.assertRaises(ValueError):
            diag.analyze(rows, 250)

    def test_any_noncoherent_snapshot_prevents_angle_integration(self):
        rows = [sample(), sample(1016000000, coherent=False)]
        rows[1]["timebase"] = "synthetic"
        result = diag.analyze(rows, 250)
        self.assertIsNone(result["angle_integration_deg"])

    def test_invalid_or_nonmonotonic_analysis_samples_are_rejected(self):
        for rows in ([], [sample(), sample()], [sample(), sample(1)],
                     [sample(gyro=(0, 1, 32768))]):
            with self.subTest(rows=rows), self.assertRaises((TypeError, ValueError)):
                diag.analyze(rows, 250)


class FakeIioTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-iio-tree-")
        self.directory = Path(self.temporary.name) / "iio:device99"
        self.directory.mkdir()
        (self.directory / "name").write_text("gamesir_g7pro_raw_experimental\n", encoding="ascii")
        values = {
            "in_anglvel_x_raw": -32768, "in_anglvel_y_raw": -1, "in_anglvel_z_raw": 32767,
            "in_accel_x_raw": 0, "in_accel_y_raw": 8192, "in_accel_z_raw": -8192,
        }
        for name, value in values.items():
            (self.directory / name).write_text(f"{value}\n", encoding="ascii")

    def tearDown(self):
        self.temporary.cleanup()

    def test_raw_snapshot_reports_host_read_window_and_no_packet_coherence(self):
        snapshot = diag.read_iio_snapshot(self.directory)
        self.assertFalse(snapshot["coherent"])
        self.assertEqual(snapshot["timebase"], "host_monotonic_read_window")
        self.assertEqual(snapshot["gyro_raw"], [-32768, -1, 32767])
        self.assertEqual(snapshot["accel_raw"], [0, 8192, -8192])
        self.assertLessEqual(snapshot["read_begin_ns"], snapshot["timestamp_ns"])
        self.assertLessEqual(snapshot["timestamp_ns"], snapshot["read_end_ns"])

    def test_wrong_iio_device_name_prevents_reading_sensor_values(self):
        (self.directory / "name").write_text("unrelated_sensor\n", encoding="ascii")
        with self.assertRaises((TypeError, ValueError, OSError)):
            diag.read_iio_snapshot(self.directory)

    def test_missing_channel_is_not_replaced_by_zero(self):
        (self.directory / "in_anglvel_y_raw").unlink()
        with self.assertRaises((TypeError, ValueError, OSError)):
            diag.read_iio_snapshot(self.directory)

    def test_invalid_iio_channel_text_and_range_are_rejected(self):
        for text in ("", "no sample\n", "0 1\n", "1.5\n", "32768\n", "-32769\n"):
            (self.directory / "in_accel_x_raw").write_text(text, encoding="ascii")
            with self.subTest(text=text), self.assertRaises((TypeError, ValueError, OSError)):
                diag.read_iio_snapshot(self.directory)

    def test_snapshot_does_not_change_any_iio_attribute(self):
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        diag.read_iio_snapshot(self.directory)
        self.assertEqual({path.name: path.read_bytes() for path in self.directory.iterdir()}, before)

    def test_read_window_uses_midpoint_of_two_host_timestamps(self):
        with patch.object(diag.time, "monotonic_ns", side_effect=[1000000, 1200000]):
            snapshot = diag.read_iio_snapshot(self.directory)
        self.assertEqual(snapshot["read_begin_ns"], 1000000)
        self.assertEqual(snapshot["read_end_ns"], 1200000)
        self.assertEqual(snapshot["timestamp_ns"], 1100000)

    def test_stalled_attribute_sweep_is_rejected(self):
        with patch.object(diag.time, "monotonic_ns", side_effect=[0, 100000001]):
            with self.assertRaises(ValueError):
                diag.read_iio_snapshot(self.directory)

    def test_symlink_channel_is_not_followed(self):
        channel = self.directory / "in_accel_x_raw"
        channel.unlink()
        channel.symlink_to(self.directory / "in_accel_y_raw")
        with self.assertRaises((ValueError, OSError)):
            diag.read_iio_snapshot(self.directory)

    def test_oversized_channel_text_is_rejected(self):
        (self.directory / "in_accel_x_raw").write_bytes(b"0" * 257)
        with self.assertRaises(ValueError):
            diag.read_iio_snapshot(self.directory)

    def test_fifo_attribute_is_rejected_before_open(self):
        channel = self.directory / "in_accel_x_raw"
        channel.unlink()
        os.mkfifo(channel)
        with self.assertRaises((ValueError, OSError)):
            diag.read_iio_snapshot(self.directory)


class GuidedPhaseTests(unittest.TestCase):
    def test_exact_phase_boundaries_and_open_intervals(self):
        expected = ((0, 0), (14.999, 0), (15, 1), (29.999, 1),
                    (30, 2), (59.999, 2), (60, 3), (74.999, 3),
                    (75, 4), (89.999, 4), (90, None), (100, None))
        for elapsed, phase in expected:
            with self.subTest(elapsed=elapsed):
                self.assertEqual(diag.guided_phase(elapsed), phase)

    def test_invalid_elapsed_time_is_rejected(self):
        for elapsed in (-1, -0.001, math.nan, math.inf, -math.inf, None, "15", True):
            with self.subTest(elapsed=elapsed), self.assertRaises((TypeError, ValueError)):
                diag.guided_phase(elapsed)

    def test_cue_due_advances_once_and_never_catches_up_missed_phases(self):
        self.assertEqual(diag.cue_due(0, -1), 0)
        self.assertEqual(diag.cue_due(14.5, 0), 0)
        self.assertEqual(diag.cue_due(15, 0), 1)
        self.assertEqual(diag.cue_due(21, 1), 1)
        self.assertEqual(diag.cue_due(30, 1), 2)
        self.assertEqual(diag.cue_due(60, 2), 3)
        self.assertEqual(diag.cue_due(75, 3), 4)
        self.assertIsNone(diag.cue_due(90, 4))
        for elapsed, previous in ((30, 0), (60, 1), (75, 2), (0, 1)):
            with self.subTest(elapsed=elapsed, previous=previous), self.assertRaises(ValueError):
                diag.cue_due(elapsed, previous)

    def test_phase_transition_more_than_two_seconds_late_stops(self):
        self.assertEqual(diag.cue_due(2, -1), 0)
        self.assertEqual(diag.cue_due(17, 0), 1)
        for elapsed, previous in ((2.001, -1), (17.001, 0), (32.001, 1),
                                  (62.001, 2), (77.001, 3)):
            with self.subTest(elapsed=elapsed), self.assertRaises(ValueError):
                diag.cue_due(elapsed, previous)


class GuidedCueTests(unittest.TestCase):
    def test_popup_uses_fixed_argv_without_shell_and_records_actual_cue_time(self):
        events = []
        child = Mock()
        child.poll.return_value = 0
        text = "Test ; $(touch must-not-execute)"
        with patch.object(diag.subprocess, "Popen", return_value=child) as spawn, \
                patch.object(diag.time, "monotonic_ns", return_value=100), redirect_stdout(io.StringIO()):
            cues = diag.GuidedCues(events.append)
            cues.show("rest", text, 15, scheduled_ns=80)
            cues.close()
        spawn.assert_called_once_with(
            ["/usr/bin/kdialog", "--title", "GameSir – Gyro-Anzeigetest", "--passivepopup", text, "15"],
            shell=False, stdin=diag.subprocess.DEVNULL,
            stdout=diag.subprocess.DEVNULL, stderr=diag.subprocess.DEVNULL)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["monotonic_ns"], 100)
        self.assertEqual(events[0]["scheduled_monotonic_ns"], 80)
        self.assertEqual(events[0]["requested_lateness_ns"], 20)
        self.assertFalse(events[0]["user_saw_notification_verified"])
        child.wait.assert_called_once_with(timeout=.5)

    def test_nonzero_popup_exit_is_an_error_and_no_new_popup_is_started(self):
        child = Mock()
        child.poll.return_value = 1
        cues = diag.GuidedCues()
        cues.child = child
        with self.assertRaisesRegex(ValueError, "KDE cue process failed"):
            cues.check()
        with patch.object(diag.subprocess, "Popen") as spawn:
            with self.assertRaises(ValueError):
                cues.show("motion", "Do not show after failed notification", 30)
            spawn.assert_not_called()

    def test_popup_replacement_and_close_reap_only_owned_children(self):
        children = [Mock(), Mock()]
        for child in children:
            child.poll.return_value = None
        unrelated = Mock()
        with patch.object(diag.subprocess, "Popen", side_effect=children), redirect_stdout(io.StringIO()):
            cues = diag.GuidedCues()
            cues.show("rest", "rest", 15)
            cues.show("pickup", "pickup", 15)
            children[0].terminate.assert_called()
            cues.close()
        for child in children:
            child.terminate.assert_called()
            child.wait.assert_called_once_with(timeout=.5)
        self.assertEqual(unrelated.mock_calls, [])

    def test_unresponsive_owned_popup_is_killed_and_reaped(self):
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [diag.subprocess.TimeoutExpired("synthetic popup", .5), 0]
        cues = diag.GuidedCues()
        cues.child = child
        cues.close()
        child.terminate.assert_called_once()
        child.kill.assert_called_once()
        self.assertEqual(child.wait.call_count, 2)

    def test_late_popup_launch_records_attempt_and_stops(self):
        events = []
        child = Mock()
        child.poll.return_value = 0
        with patch.object(diag.subprocess, "Popen", return_value=child), \
                patch.object(diag.time, "monotonic_ns", return_value=2000000001):
            cues = diag.GuidedCues(events.append)
            with self.assertRaisesRegex(ValueError, "launch delayed"):
                cues.show("motion", "too late", 30, scheduled_ns=0)
            cues.close()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["requested_lateness_ns"], 2000000001)

    def test_cleanup_continues_to_other_owned_children_after_first_error(self):
        first, second = Mock(), Mock()
        first.poll.return_value = second.poll.return_value = 0
        first.wait.side_effect = OSError("synthetic reap failure")
        cues = diag.GuidedCues()
        cues.retired = [first]
        cues.child = second
        with self.assertRaisesRegex(OSError, "synthetic reap failure"):
            cues.close()
        first.wait.assert_called_once_with(timeout=.5)
        second.wait.assert_called_once_with(timeout=.5)

    def test_process_exit_race_during_termination_is_tolerated_and_reaped(self):
        first, second = Mock(), Mock()
        first.poll.return_value = None
        first.terminate.side_effect = ProcessLookupError("already exited")
        second.poll.return_value = 0
        with patch.object(diag.subprocess, "Popen", side_effect=[first, second]), redirect_stdout(io.StringIO()):
            cues = diag.GuidedCues()
            cues.show("rest", "rest", 15)
            cues.show("pickup", "pickup", 15)
            cues.close()
        first.wait.assert_called_once_with(timeout=.5)
        second.wait.assert_called_once_with(timeout=.5)


class VirtualClock:
    """Virtual wall time for guided tests; no actual waiting or GUI."""
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def monotonic_ns(self):
        return round(self.now * 1000000000)

    def sleep(self, seconds):
        if seconds < 0:
            raise AssertionError("negative sleep")
        self.now += seconds


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-imu-cli-")
        self.root = Path(self.temporary.name)
        self.records = self.root / "constructed.jsonl"
        self.records.write_text("".join(json.dumps(row) + "\n" for row in
                                        (record(), record(1016000))), encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = diag.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def run_guided(self, *, clock=None, reader=None, popup_status=0, cleanup_error=False, name="guided-result"):
        clock = clock or VirtualClock()
        read_times, children = [], []
        output = self.root / name

        def read_fake(directory):
            read_times.append(clock.now)
            if reader is not None:
                return reader(clock)
            return dict(sample(clock.monotonic_ns(), coherent=False),
                        read_begin_ns=clock.monotonic_ns(), read_end_ns=clock.monotonic_ns(),
                        iio_instance=[123, 456])

        def popup(*args, **kwargs):
            child = Mock()
            child.poll.return_value = popup_status
            if cleanup_error:
                child.wait.side_effect = OSError("synthetic cleanup failure")
            children.append(child)
            return child

        arguments = ["observe-iio", "--experimental", "--profile", "250", "--guided-kde",
                     "--iio-dir", str(self.root / "never-read"), "--duration", "90",
                     "--period-ms", "1000", "--output", str(output)]
        with patch.dict(diag.os.environ, {"DISPLAY": ":synthetic"}), \
                patch.object(diag.Path, "is_file", return_value=True), \
                patch.object(diag, "cached_iio_identity", return_value=[123, 456]), \
                patch.object(diag, "read_iio_snapshot", side_effect=read_fake), \
                patch.object(diag.subprocess, "Popen", side_effect=popup), \
                patch.object(diag.time, "monotonic", side_effect=clock.monotonic), \
                patch.object(diag.time, "monotonic_ns", side_effect=clock.monotonic_ns), \
                patch.object(diag.time, "sleep", side_effect=clock.sleep):
            result = self.run_cli(arguments)
        return (*result, output, clock, read_times, children)

    def test_profiles_and_plan_never_read_a_device_or_capture(self):
        for command in ("profiles", "plan"):
            with patch.object(diag, "replay", side_effect=AssertionError("file read forbidden")), \
                    patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("device read forbidden")):
                code, output, _ = self.run_cli([command])
            self.assertEqual(code, 0)
            self.assertIsInstance(json.loads(output), (list, dict))

    def test_guided_plan_has_human_buffers_and_does_not_authorize_measurement(self):
        code, output, _ = self.run_cli(["plan"])
        self.assertEqual(code, 0)
        plan = json.loads(output)
        self.assertTrue(plan["plan_only"])
        self.assertFalse(plan["hardware_authorized_by_plan"])
        self.assertEqual(plan["seconds"], sum(phase["seconds"] for phase in plan["phases"]))
        phases = plan["phases"]
        for index, phase in enumerate(phases):
            if phase["phase"].startswith(("rotate_", "pose_")):
                self.assertGreater(index, 0)
                self.assertTrue(phases[index - 1]["phase"].startswith("buffer_"))
                self.assertGreaterEqual(phases[index - 1]["seconds"], 15)

    def test_no_implicit_profile_or_experimental_opt_in(self):
        base = ["replay", "--records", str(self.records), "--output", str(self.root / "result")]
        for incomplete in (base, base + ["--experimental"], base + ["--profile", "250"]):
            with patch.object(diag, "replay", side_effect=AssertionError("parser must reject first")):
                with self.subTest(args=incomplete), self.assertRaises(SystemExit) as raised:
                    self.run_cli(incomplete)
                self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.root / "result").exists())

    def test_replay_all_profiles_creates_private_checked_output(self):
        output = self.root / "result"
        code, _, error = self.run_cli(["replay", "--experimental", "--profile", "all",
                                       "--records", str(self.records), "--output", str(output)])
        self.assertEqual(code, 0, error)
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["completed"])
        self.assertFalse(report["runtime_calibration_changed"])
        self.assertFalse(report["automatic_profile_selection"])
        self.assertEqual(set(report["profiles"]), {"125", "250", "500", "1000", "2000"})
        self.assertEqual(output.stat().st_mode & 0o777, 0o700)
        for name in ("observations.jsonl", "report.json", "SHA256SUMS"):
            self.assertEqual((output / name).stat().st_mode & 0o777, 0o600)
        for line in (output / "SHA256SUMS").read_text(encoding="ascii").splitlines():
            expected, name = line.split("  ", 1)
            self.assertEqual(diag.digest(output / name), expected)
        observations = [json.loads(line) for line in (output / "observations.jsonl").read_text().splitlines()]
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0]["timebase"], "synthetic")
        self.assertEqual(observations[0]["gyro_raw"], [100, -200, 300])

    def test_existing_result_directory_is_never_overwritten(self):
        output = self.root / "existing"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("original evidence", encoding="ascii")
        code, _, error = self.run_cli(["replay", "--experimental", "--profile", "250",
                                       "--records", str(self.records), "--output", str(output)])
        self.assertEqual(code, 1)
        self.assertIn("STOP:", error)
        self.assertEqual(list(output.iterdir()), [marker])
        self.assertEqual(marker.read_text(encoding="ascii"), "original evidence")

    def test_invalid_saved_file_does_not_fall_back_to_iio(self):
        self.records.write_text("not json\n", encoding="ascii")
        with patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("no IIO fallback")):
            code, _, error = self.run_cli(["replay", "--experimental", "--profile", "250",
                                           "--records", str(self.records), "--output", str(self.root / "result")])
        self.assertEqual(code, 1)
        self.assertIn("STOP:", error)
        self.assertFalse((self.root / "result").exists())

    def test_invalid_observation_bounds_are_rejected_before_iio_reads(self):
        for option, value in (("--duration", "0"), ("--duration", "1801"),
                              ("--duration", "nan"), ("--period-ms", "4"),
                              ("--period-ms", "1001"), ("--period-ms", "inf")):
            arguments = ["observe-iio", "--experimental", "--profile", "250",
                         "--iio-dir", str(self.root / "never-read"),
                         "--output", str(self.root / "result"), option, value]
            with patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("must reject bounds first")):
                code, _, error = self.run_cli(arguments)
            self.assertEqual(code, 1)
            self.assertIn("STOP:", error)
        self.assertFalse((self.root / "result").exists())

    def test_guided_observation_rejects_non_ninety_second_duration_before_reads(self):
        for duration in ("0", "30", "89", "91", "1800"):
            arguments = ["observe-iio", "--experimental", "--profile", "250",
                         "--iio-dir", str(self.root / "never-read"), "--guided-kde",
                         "--duration", duration, "--output", str(self.root / "guided-result")]
            with patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("reject before read")):
                with self.subTest(duration=duration):
                    code, _, error = self.run_cli(arguments)
                    self.assertEqual(code, 1)
                    self.assertIn("STOP:", error)
        self.assertFalse((self.root / "guided-result").exists())

    def test_guided_run_schedules_all_cues_locally_and_reads_only_after_preparation(self):
        code, _, error, output, clock, read_times, children = self.run_guided()
        self.assertEqual(code, 0, error)
        self.assertEqual(len(read_times), 90)
        self.assertEqual(read_times[0], 30)
        self.assertEqual(read_times[-1], 119)
        self.assertEqual(clock.now, 123)
        self.assertTrue(all(30 <= when < 120 for when in read_times))
        cues = [json.loads(line) for line in (output / "cues.jsonl").read_text().splitlines()]
        self.assertEqual([cue["event"] for cue in cues],
                         ["preparation", "rest", "pickup_buffer", "motion",
                          "put_down_buffer", "rest_end", "finished"])
        self.assertEqual([cue["monotonic_ns"] for cue in cues],
                         [second * 1000000000 for second in (0, 30, 45, 60, 90, 105, 120)])
        self.assertTrue(all(not cue["user_saw_notification_verified"] for cue in cues))
        report = json.loads((output / "report.json").read_text())
        self.assertTrue(report["completed"])
        self.assertTrue(report["metadata"]["guided_kde"])
        self.assertIsNone(report["profiles"]["250"]["angle_integration_deg"])
        hashes = (output / "SHA256SUMS").read_text().splitlines()
        self.assertTrue(any(line.endswith("  cues.jsonl") for line in hashes))
        for line in hashes:
            expected, filename = line.split("  ", 1)
            self.assertEqual(diag.digest(output / filename), expected)
            self.assertEqual((output / filename).stat().st_mode & 0o777, 0o600)
        self.assertTrue(children)
        for child in children:
            child.wait.assert_called()

    def test_guided_mode_requires_graphical_session_before_any_iio_access(self):
        arguments = ["observe-iio", "--experimental", "--profile", "250", "--guided-kde",
                     "--iio-dir", str(self.root / "never-read"), "--duration", "90",
                     "--output", str(self.root / "no-gui")]
        with patch.dict(diag.os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}), \
                patch.object(diag.Path, "is_file", return_value=True), \
                patch.object(diag, "cached_iio_identity", side_effect=AssertionError("no metadata read")), \
                patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("no raw read")), \
                patch.object(diag.subprocess, "Popen", side_effect=AssertionError("no process")):
            code, _, error = self.run_cli(arguments)
        self.assertEqual(code, 1)
        self.assertIn("graphical session", error)
        self.assertFalse((self.root / "no-gui").exists())

    def test_popup_failure_during_preparation_preserves_error_and_reads_no_channels(self):
        code, _, error, output, _, read_times, _ = self.run_guided(popup_status=1)
        self.assertEqual(code, 1)
        self.assertEqual(read_times, [])
        self.assertIn("KDE cue process failed", error)
        report = json.loads((output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertEqual(report["profiles"], {})
        self.assertEqual((output / "observations.jsonl").read_bytes(), b"")

    def test_primary_popup_failure_survives_additional_cleanup_error(self):
        code, _, error, output, _, read_times, _ = self.run_guided(popup_status=1, cleanup_error=True)
        self.assertEqual(code, 1)
        self.assertEqual(read_times, [])
        self.assertIn("KDE cue process failed", error)
        report = json.loads((output / "report.json").read_text())
        self.assertIn("KDE cue process failed", report["failure"])
        self.assertNotIn("synthetic cleanup failure", report["failure"])

    def test_preparation_stall_aborts_before_sampling(self):
        class StalledPreparation(VirtualClock):
            def sleep(self, seconds):
                self.now = 33

        code, _, error, output, _, read_times, _ = self.run_guided(clock=StalledPreparation())
        self.assertEqual(code, 1)
        self.assertEqual(read_times, [])
        self.assertIn("preparation deadline missed", error)
        self.assertFalse(json.loads((output / "report.json").read_text())["completed"])

    def test_skipping_last_phase_cannot_be_reported_as_successful_completion(self):
        class SkippingFinalPhase(VirtualClock):
            def sleep(self, seconds):
                if 104 <= self.now < 105:
                    self.now = 120
                else:
                    super().sleep(seconds)

        code, _, error, output, _, read_times, _ = self.run_guided(clock=SkippingFinalPhase())
        self.assertEqual(code, 1)
        self.assertIn("last guided phase skipped", error)
        self.assertTrue(all(when < 105 for when in read_times))
        cues = [json.loads(line) for line in (output / "cues.jsonl").read_text().splitlines()]
        self.assertNotIn("finished", [cue["event"] for cue in cues])
        self.assertFalse(json.loads((output / "report.json").read_text())["completed"])

    def test_late_completion_is_rejected_without_more_raw_reads(self):
        class LateCompletion(VirtualClock):
            def sleep(self, seconds):
                if 119 <= self.now < 120:
                    self.now = 123
                else:
                    super().sleep(seconds)

        code, _, error, output, _, read_times, _ = self.run_guided(clock=LateCompletion())
        self.assertEqual(code, 1)
        self.assertIn("completion delayed", error)
        self.assertEqual(read_times[-1], 119)
        self.assertFalse(json.loads((output / "report.json").read_text())["completed"])

    def test_missed_phase_aborts_without_replaying_instructions_or_automatic_retry(self):
        class SkippingClock(VirtualClock):
            def sleep(self, seconds):
                if 44 <= self.now < 45:
                    self.now = 60
                else:
                    super().sleep(seconds)

        code, _, error, output, _, read_times, _ = self.run_guided(clock=SkippingClock())
        self.assertEqual(code, 1)
        self.assertIn("guided phase missed", error)
        self.assertTrue(read_times)
        self.assertTrue(all(30 <= when <= 44 for when in read_times))
        report = json.loads((output / "report.json").read_text())
        self.assertFalse(report["completed"])
        cues = [json.loads(line) for line in (output / "cues.jsonl").read_text().splitlines()]
        self.assertEqual([cue["event"] for cue in cues], ["preparation", "rest"])

    def test_replaced_iio_instance_during_preparation_is_not_adopted(self):
        def other_device(clock):
            return dict(sample(clock.monotonic_ns(), coherent=False),
                        read_begin_ns=clock.monotonic_ns(), read_end_ns=clock.monotonic_ns(),
                        iio_instance=[123, 999])

        code, _, error, output, _, read_times, _ = self.run_guided(reader=other_device)
        self.assertEqual(code, 1)
        self.assertEqual(read_times, [30])
        self.assertIn("instance changed during preparation", error)
        self.assertFalse(json.loads((output / "report.json").read_text())["completed"])
        self.assertEqual((output / "observations.jsonl").read_bytes(), b"")

    def test_fake_iio_read_error_preserves_partial_private_observations(self):
        output = self.root / "partial"
        observation = dict(sample(coherent=False), read_begin_ns=999999999,
                           read_end_ns=1000000001, iio_instance=[123, 456])
        arguments = ["observe-iio", "--experimental", "--profile", "250",
                     "--iio-dir", str(self.root / "never-read"), "--duration", "10",
                     "--output", str(output)]
        with patch.object(diag, "read_iio_snapshot", side_effect=[observation, ValueError("sample unavailable")]), \
                patch.object(diag.time, "monotonic", side_effect=[0.0, 0.0, 0.1]), \
                patch.object(diag.time, "sleep"):
            code, _, error = self.run_cli(arguments)
        self.assertEqual(code, 1)
        self.assertIn("sample unavailable", error)
        report = json.loads((output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertEqual(report["profiles"]["250"]["sample_count"], 1)
        self.assertIsNone(report["profiles"]["250"]["angle_integration_deg"])
        self.assertEqual(len((output / "observations.jsonl").read_text().splitlines()), 1)

    def test_fake_iio_no_sample_before_deadline_cannot_report_success(self):
        output = self.root / "no-observations"
        arguments = ["observe-iio", "--experimental", "--profile", "250",
                     "--iio-dir", str(self.root / "never-read"), "--duration", "10",
                     "--output", str(output)]
        with patch.object(diag, "read_iio_snapshot", side_effect=AssertionError("deadline already passed")), \
                patch.object(diag.time, "monotonic", side_effect=[0.0, 11.0]):
            code, _, error = self.run_cli(arguments)
        self.assertEqual(code, 1)
        self.assertIn("no observations", error)
        self.assertFalse(json.loads((output / "report.json").read_text())["completed"])

    def test_fake_iio_instance_change_stops_before_mixing_device_samples(self):
        output = self.root / "changed-instance"
        first = dict(sample(coherent=False), read_begin_ns=999999999,
                     read_end_ns=1000000001, iio_instance=[123, 456])
        second = dict(sample(1016000000, coherent=False), read_begin_ns=1015999999,
                      read_end_ns=1016000001, iio_instance=[123, 457])
        arguments = ["observe-iio", "--experimental", "--profile", "250",
                     "--iio-dir", str(self.root / "never-read"), "--duration", "10",
                     "--output", str(output)]
        with patch.object(diag, "read_iio_snapshot", side_effect=[first, second]), \
                patch.object(diag.time, "monotonic", side_effect=[0.0, 0.0, 0.1]), \
                patch.object(diag.time, "sleep"):
            code, _, error = self.run_cli(arguments)
        self.assertEqual(code, 1)
        self.assertIn("instance changed", error)
        report = json.loads((output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertEqual(report["profiles"]["250"]["sample_count"], 1)
        self.assertEqual(len((output / "observations.jsonl").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
