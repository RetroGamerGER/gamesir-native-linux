#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Constructed known-angle recordings only; no sensors or hardware access."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/imu"))
import gyro_reference as ref


STEP = 5_041_523
MAPPING = {axis: {"raw_axis": i, "sign": 1} for i, axis in enumerate("XYZ")}


def fixture(axis=0, angle=90, bias=(7, -11, 23), *, off_axis=0):
    """Own analytic triangle, constructed using the 500-dps hypothesis.

    10100 counts peak * 101 intervals * STEP ns is its known raw integral.
    STEP is rounded to recorded integer nanoseconds; its 500-dps hypothesis
    yields 90.00000821525 degrees. This selected construction is synthetic
    ground truth only and never chooses a hardware/runtime calibration.
    """
    rows = []
    # Initial rest, triangle with zero at both ends, final rest.
    for i in range(405):
        gyro = list(bias)
        if 101 <= i <= 303:
            relative = i - 101
            # All raw samples are signed integers, not inferred angles.
            pulse = min(relative, 202 - relative) * 100
            gyro[axis] += (1 if angle > 0 else -1) * pulse * abs(angle) // 90
            if off_axis:
                gyro[(axis + 1) % 3] += pulse // off_axis
        rows.append({"timestamp_ns": 1_000_000_000 + i * STEP,
                     "sample_number": i + 17, "gyro_raw": gyro,
                     "accel_raw": [0, 0, 8192], "coherent": True,
                     "timebase": "host_monotonic_receive", "source_kind": "synthetic",
                     "instance_id": "constructed-instance-1"})
    stamps = [row["timestamp_ns"] for row in rows]
    window = {"label": f"reference-{axis}-{angle}", "physical_axis": "XYZ"[axis],
              "known_angle_deg": angle, "reference_kind": "external_angle_marker",
              "angle_reference_description": "constructed protractor reference, synthetic only",
              "reference_completed": True, "motion_bounds_include_stationary_margins": True,
              "rest_before": [stamps[0], stamps[100]],
              "motion": [stamps[101], stamps[303]],
              "rest_after": [stamps[304], stamps[404]]}
    metadata = {"schema_version": 1, "kind": "experimental_known_angle",
                "windows": [window], "axis_mapping": copy.deepcopy(MAPPING)}
    return rows, metadata


class HumanPlan(unittest.TestCase):
    def test_default_plan_is_one_left_yaw_session(self):
        plan = ref.calibration_plan()
        self.assertEqual(plan["session_id"], "yaw90left")
        self.assertEqual(plan["repetitions"], 3)
        self.assertEqual(plan["prepare_seconds"], 30)
        self.assertTrue(plan["readiness_required_before_each_repetition"])
        self.assertFalse(plan["automatic_next_repetition"])
        self.assertFalse(plan["automatic_next_session"])
        self.assertFalse(plan["hardware_authorized"])

    def test_all_90_180_axis_directions_have_separate_sessions(self):
        cases = set()
        for name in ref.SESSION_SPECS:
            plan = ref.calibration_plan(name)
            cases.add((plan["physical_axis_label"], plan["signed_known_angle_deg"]))
            self.assertFalse(plan["automatic_next_session"])
        self.assertEqual(cases, {(axis, angle) for axis in "XYZ" for angle in (-180, -90, 90, 180)})

    def test_human_buffers_and_explicit_reset(self):
        plan = ref.calibration_plan()
        phases = {row["phase"]: row for row in plan["phases_per_repetition"]}
        self.assertEqual(phases["rest_before"]["seconds"], 20)
        self.assertEqual(phases["rest_after"]["seconds"], 30)
        self.assertEqual(phases["pickup_buffer"]["seconds"], 15)
        self.assertEqual(phases["put_down_buffer"]["seconds"], 15)
        self.assertEqual(phases["reset_outside_analysis"]["minimum_seconds"], 15)
        self.assertEqual(phases["hold_start"]["seconds"], 5)
        self.assertEqual(phases["hold_end"]["seconds"], 5)
        self.assertTrue(phases["motion"]["independent_start_and_end_angle_marks_required"])

    def test_six_accel_poses_are_optional_separate_session(self):
        accel = ref.calibration_plan()["optional_accel_session"]
        self.assertEqual(set(accel["poses"]), {f"{sign}{axis} up" for sign in "+-" for axis in "XYZ"})
        self.assertTrue(accel["separate_approval_and_readiness_per_pose"])
        self.assertFalse(accel["scale_verified"])

    def test_unknown_session_rejected(self):
        with self.assertRaises(ValueError):
            ref.calibration_plan("all automatically")

    def test_metadata_schema_has_independent_reference_and_recorded_times(self):
        schema = ref.metadata_schema()
        window = schema["properties"]["windows"]["items"]
        self.assertIn("reference_kind", window["required"])
        self.assertIn("reference_completed", window["required"])
        self.assertEqual(window["properties"]["known_angle_deg"]["enum"], [-180, -90, 90, 180])


class ReferenceIntegration(unittest.TestCase):
    def analyze(self, rows, metadata):
        return ref.analyze_reference(rows, metadata, max_gap_ns=STEP)

    def test_all_signed_90_180_axis_cases_and_five_profiles(self):
        for axis in range(3):
            for angle in (-180, -90, 90, 180):
                with self.subTest(axis=axis, angle=angle):
                    rows, meta = fixture(axis, angle)
                    result = self.analyze(rows, meta)
                    window = result["windows"][0]
                    raw = math.copysign(10100 * 101 * STEP / 1e9 * abs(angle) / 90, angle)
                    expected = [raw if index == axis else 0 for index in range(3)]
                    for actual, value in zip(window["raw_integral_count_seconds"], expected):
                        self.assertAlmostEqual(actual, value, places=7)
                    self.assertEqual(len(window["profiles"]), 5)
                    for profile in window["profiles"]:
                        factor = float(ref.PROFILES[profile["assumed_range_dps"]])
                        degrees = profile["angle_raw_axes_deg"][axis]
                        self.assertAlmostEqual(degrees, raw * factor, places=7)
                        self.assertAlmostEqual(profile["angle_raw_axes_rad"][axis], math.radians(degrees))
                        self.assertAlmostEqual(profile["physical_axis_comparison"]["error_deg"], degrees - angle)
                        self.assertFalse(profile["profile_confirmed"])
                        self.assertFalse(profile["selected_for_runtime"])
                        if profile["assumed_range_dps"] == 500:
                            self.assertLess(abs(profile["physical_axis_comparison"]["error_deg"]), .00002)
                    self.assertFalse(result["selected_as_actual_hardware_profile"])
                    self.assertFalse(result["calibration_verified"])
                    self.assertFalse(result["sdl_runtime_enable"])
                    self.assertEqual(result["intervals_discarded"], 0)

    def test_bias_is_bracketed_and_preserves_raw_records(self):
        rows, meta = fixture(bias=(51, -32, 125))
        original = copy.deepcopy((rows, meta))
        window = self.analyze(rows, meta)["windows"][0]
        self.assertEqual(window["bias_raw_experimental"], [51, -32, 125])
        self.assertEqual(window["bias_shift_after_minus_before_raw"], [0, 0, 0])
        self.assertEqual((rows, meta), original)

    def test_drift_is_reported_separately_not_hidden(self):
        rows, meta = fixture()
        for row in rows[304:]:
            row["gyro_raw"][0] += 20
        window = self.analyze(rows, meta)["windows"][0]
        self.assertEqual(window["bias_shift_after_minus_before_raw"], [20, 0, 0])
        self.assertEqual(window["bias_raw_experimental"][0], 17)
        self.assertAlmostEqual(window["raw_integral_count_seconds"][0],
                               10100 * 101 * STEP / 1e9 - 10 * 202 * STEP / 1e9)

    def test_off_axis_integral_is_measured_without_axis_relabel(self):
        rows, meta = fixture(off_axis=2)
        window = self.analyze(rows, meta)["windows"][0]
        self.assertAlmostEqual(window["off_axis_integral_fraction_under_mapping_hypothesis"], .5)
        self.assertFalse(window["axis_mapping_verified"])

    def test_absent_mapping_never_infers_physical_axis(self):
        rows, meta = fixture()
        del meta["axis_mapping"]
        result = self.analyze(rows, meta)
        window = result["windows"][0]
        self.assertIsNone(result["axis_mapping_hypothesis"])
        self.assertNotIn("empirical_dps_per_count_under_mapping_hypothesis", window)
        self.assertTrue(all(row["physical_axis_comparison"] is None for row in window["profiles"]))

    def test_explicit_sign_mapping_is_hypothesis_only(self):
        rows, meta = fixture(angle=-90)
        meta["axis_mapping"]["X"]["sign"] = -1
        window = self.analyze(rows, meta)["windows"][0]
        self.assertLess(window["empirical_dps_per_count_under_mapping_hypothesis"], 0)
        self.assertFalse(window["axis_mapping_verified"])

    def test_zero_projection_has_no_fabricated_factor(self):
        rows, meta = fixture()
        for row in rows:
            row["gyro_raw"] = [0, 0, 0]
        window = self.analyze(rows, meta)["windows"][0]
        self.assertIsNone(window["empirical_dps_per_count_under_mapping_hypothesis"])
        self.assertIsNone(window["off_axis_integral_fraction_under_mapping_hypothesis"])

    def test_multiple_nonoverlapping_repetitions(self):
        rows, meta = fixture()
        rows2, meta2 = fixture(angle=-90)
        offset = rows[-1]["timestamp_ns"] + STEP - rows2[0]["timestamp_ns"]
        sequence = rows[-1]["sample_number"] + 1 - rows2[0]["sample_number"]
        for row in rows2:
            row["timestamp_ns"] += offset
            row["sample_number"] += sequence
        for name in ("rest_before", "motion", "rest_after"):
            meta2["windows"][0][name] = [value + offset for value in meta2["windows"][0][name]]
        meta["windows"].extend(meta2["windows"])
        result = self.analyze(rows + rows2, meta)
        self.assertEqual(len(result["windows"]), 2)
        self.assertAlmostEqual(sum(row["raw_integral_count_seconds"][0] for row in result["windows"]), 0)


class FailClosed(unittest.TestCase):
    def rejected(self, mutate):
        rows, meta = fixture()
        mutate(rows, meta)
        with self.assertRaises(ValueError):
            ref.analyze_reference(rows, meta, STEP)

    def test_noncoherent_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(coherent=False))

    def test_wrong_timebase_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(timebase="fabricated_sensor_clock"))

    def test_duplicate_timestamp_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(timestamp_ns=rows[19]["timestamp_ns"]))

    def test_backward_timestamp_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(timestamp_ns=rows[19]["timestamp_ns"] - 1))

    def test_gap_outside_motion_rejects_whole_analysis(self):
        self.rejected(lambda rows, meta: rows[20].update(sample_number=99999))

    def test_duplicate_sample_number_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(sample_number=rows[19]["sample_number"]))

    def test_counter_reset_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(sample_number=0))

    def test_host_gap_rejected_instead_of_partial_integral(self):
        self.rejected(lambda rows, meta: rows[20].update(timestamp_ns=rows[20]["timestamp_ns"] + 1))

    def test_instance_change_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(instance_id="another-controller"))

    def test_source_change_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(source_kind="iio_buffer"))

    def test_missing_instance_rejected(self):
        self.rejected(lambda rows, meta: rows[20].pop("instance_id"))

    def test_counter_integer_width_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(sample_number=1 << 64))

    def test_timestamp_integer_width_rejected(self):
        self.rejected(lambda rows, meta: rows[20].update(timestamp_ns=1 << 63))

    def test_raw_boolean_rejected(self):
        self.rejected(lambda rows, meta: rows[20]["gyro_raw"].__setitem__(0, True))

    def test_raw_overflow_rejected(self):
        self.rejected(lambda rows, meta: rows[20]["accel_raw"].__setitem__(0, 32768))

    def test_potential_gyro_clipping_rejected(self):
        self.rejected(lambda rows, meta: rows[150]["gyro_raw"].__setitem__(0, 32767))

    def test_missing_recorded_boundary_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0]["motion"].__setitem__(0, rows[101]["timestamp_ns"] + 1))

    def test_incomplete_rotation_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0].update(reference_completed=False))

    def test_no_stationary_margins_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0].update(motion_bounds_include_stationary_margins=False))

    def test_imu_derived_angle_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0].update(reference_kind="integrated_same_imu"))

    def test_unknown_angle_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0].update(known_angle_deg=45))

    def test_overlapping_rest_motion_rejected(self):
        self.rejected(lambda rows, meta: meta["windows"][0].update(motion=meta["windows"][0]["rest_before"]))

    def test_duplicate_mapping_axis_rejected(self):
        self.rejected(lambda rows, meta: meta["axis_mapping"]["Y"].update(raw_axis=0))

    def test_missing_explicit_gap_bound_rejected(self):
        rows, meta = fixture()
        for bound in (None, True, 0, -1, 1.5):
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                ref.analyze_reference(rows, meta, bound)


class SavedFileCli(unittest.TestCase):
    def test_plan_never_opens_data_or_devices(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(ref.main(["plan", "--session", "yaw90right"]), 0)
        self.assertEqual(json.loads(out.getvalue())["signed_known_angle_deg"], -90)

    def test_schema_prints_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(ref.main(["metadata-schema"]), 0)
        self.assertEqual(json.loads(out.getvalue())["title"], "GameSir experimental known-angle metadata v1")

    def test_saved_jsonl_analysis_round_trip(self):
        rows, meta = fixture()
        with tempfile.TemporaryDirectory() as folder:
            samples = Path(folder) / "samples.jsonl"
            markers = Path(folder) / "markers.json"
            samples.write_text("".join(json.dumps(row) + "\n" for row in rows))
            markers.write_text(json.dumps(meta))
            out = io.StringIO()
            with redirect_stdout(out):
                code = ref.main(["analyze", str(samples), str(markers), "--max-gap-ns", str(STEP)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["intervals_discarded"], 0)

    def test_directories_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"
            source.write_text("{}")
            linked = Path(folder) / "link.json"
            linked.symlink_to(source)
            for path in (Path(folder), linked):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    ref._regular_text(path)

    def test_device_path_rejected_before_open(self):
        with self.assertRaises(ValueError):
            ref._regular_text("/dev/null")


if __name__ == "__main__":
    unittest.main()
