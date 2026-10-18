#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Saved-file-only, experimental known-angle planning and raw integration.

This module opens no devices, changes no calibration, and never selects a
runtime sensor profile. All timestamps and sample numbers must be recorded,
not reconstructed. Physical axes remain separate from raw channel indices.
"""
import argparse
import json
import math
import os
from pathlib import Path
import stat
import statistics
import sys

from gamesir_imu_diagnostic import PROFILES


BODY_FRAME = {
    "X": "right, viewed while holding the controller normally",
    "Y": "away from the player, toward the USB/top edge",
    "Z": "out of the button face; right-handed body-frame convention",
    "raw_axis_mapping_verified": False,
}
SESSION_SPECS = {
    "yaw90left": ("Z", 90, "90° nach links drehen"),
    "yaw90right": ("Z", -90, "90° nach rechts drehen"),
    "pitch90forward": ("X", -90, "90° nach vorne neigen: USB-Kante nach unten"),
    "pitch90back": ("X", 90, "90° nach hinten neigen: USB-Kante nach oben"),
    "roll90left": ("Y", -90, "90° nach links kippen: linke Griffseite nach unten"),
    "roll90right": ("Y", 90, "90° nach rechts kippen: rechte Griffseite nach unten"),
    "yaw180left": ("Z", 180, "180° nach links drehen"),
    "yaw180right": ("Z", -180, "180° nach rechts drehen"),
    "pitch180forward": ("X", -180, "180° nach vorne neigen"),
    "pitch180back": ("X", 180, "180° nach hinten neigen"),
    "roll180left": ("Y", -180, "180° nach links kippen"),
    "roll180right": ("Y", 180, "180° nach rechts kippen"),
}


def calibration_plan(session_id="yaw90left"):
    """One explicitly selected session; repetitions require separate readiness."""
    if session_id not in SESSION_SPECS:
        raise ValueError("unknown individually selected reference session")
    axis, angle, instruction = SESSION_SPECS[session_id]
    phases = [
        {"phase": "rest_before", "seconds": 20, "instruction": "Ruhig liegen lassen."},
        {"phase": "pickup_buffer", "seconds": 15,
         "instruction": "Aufnehmen und an der externen Startmarkierung ausrichten; noch nicht drehen."},
        {"phase": "hold_start", "seconds": 5, "instruction": "An der Startmarke stillhalten."},
        {"phase": "motion", "maximum_seconds": 15,
         "instruction": instruction + "; Endmarke erreichen und dort stillhalten.",
         "independent_start_and_end_angle_marks_required": True},
        {"phase": "hold_end", "seconds": 5,
         "instruction": "An der Endmarke stillhalten, noch nicht ablegen oder zurückdrehen."},
        {"phase": "put_down_buffer", "seconds": 15,
         "instruction": "Vorsichtig ablegen; keine unmarkierte Rückdrehung im Auswertefenster."},
        {"phase": "rest_after", "seconds": 30, "instruction": "Ruhig liegen lassen."},
        {"phase": "reset_outside_analysis", "minimum_seconds": 15,
         "instruction": "Erst nach Abschluss und außerhalb des Auswertefensters zur Startmarke zurücksetzen."},
    ]
    return {
        "schema_version": 1, "kind": "offline_reference_plan", "hardware_authorized": False,
        "session_id": session_id, "body_frame_convention": dict(BODY_FRAME),
        "physical_axis_label": axis, "signed_known_angle_deg": angle,
        "prepare_seconds": 30, "repetitions": 3,
        "readiness_required_before_each_repetition": True,
        "automatic_next_repetition": False, "automatic_next_session": False,
        "phases_per_repetition": phases,
        "next_separate_sessions_in_order": ["yaw90left", "yaw90right", "pitch90forward", "pitch90back"],
        "later_separate_sessions": [name for name in SESSION_SPECS
                                    if name not in ("yaw90left", "yaw90right", "pitch90forward", "pitch90back")],
        "optional_accel_session": {
            "separate_approval_and_readiness_per_pose": True,
            "poses": ["+X up", "-X up", "+Y up", "-Y up", "+Z up", "-Z up"],
            "reposition_buffer_seconds": 15, "rest_seconds": 30,
            "counts_per_g_assumption": 8192, "scale_verified": False,
        },
        "requirements": [
            "Winkel durch externe 0°/90°/180°-Marken oder Winkelvorrichtung festlegen; nicht aus dem Gyro ableiten.",
            "Jede Wiederholung einzeln bestätigen. Bei Unsicherheit stoppen, nicht automatisch nachholen.",
            "Drehung vollständig innerhalb eines Fensters mit stationären Rändern markieren.",
            "Keine Rückdrehung oder Umpositionierung innerhalb des Integrationsfensters.",
            "Rohkanäle G0/G1/G2 sind keine bestätigten Gehäuseachsen.",
        ],
    }


def metadata_schema():
    """Machine-readable contract for manually selected, recorded boundaries."""
    span = {"type": "array", "items": {"type": "integer", "minimum": 0},
            "minItems": 2, "maxItems": 2,
            "description": "Existing sample timestamps; start < end. No interpolation or invented times."}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GameSir experimental known-angle metadata v1", "type": "object",
        "required": ["schema_version", "kind", "windows"],
        "properties": {
            "schema_version": {"const": 1}, "kind": {"const": "experimental_known_angle"},
            "axis_mapping": {"description": "Optional explicit hypothesis: X/Y/Z each {raw_axis:0..2, sign:-1|1}; permutation required."},
            "windows": {"type": "array", "minItems": 1, "items": {
                "type": "object", "required": ["label", "physical_axis", "known_angle_deg",
                    "reference_kind", "angle_reference_description", "reference_completed",
                    "motion_bounds_include_stationary_margins", "rest_before", "motion", "rest_after"],
                "properties": {
                    "label": {"type": "string", "minLength": 1},
                    "physical_axis": {"enum": ["X", "Y", "Z"]},
                    "known_angle_deg": {"enum": [-180, -90, 90, 180]},
                    "reference_kind": {"enum": ["external_angle_marker", "angle_fixture"]},
                    "angle_reference_description": {"type": "string", "minLength": 1},
                    "reference_completed": {"const": True},
                    "motion_bounds_include_stationary_margins": {"const": True},
                    "rest_before": span, "motion": span, "rest_after": span,
                }}},
        },
    }


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: integer >= {minimum} required")
    return value


def _vector(value, name):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name}: three signed int16 raw channels required")
    if any(type(x) is not int or not -32768 <= x <= 32767 for x in value):
        raise ValueError(f"{name}: three signed int16 raw channels required")
    return list(value)


def validate_samples(samples, max_gap_ns, *, allow_single=False):
    """Reject a broken complete stream before producing any angle integral."""
    _integer(max_gap_ns, "max_gap_ns", 1)
    if not isinstance(samples, list) or len(samples) < (1 if allow_single else 2):
        raise ValueError("at least two coherent samples required")
    instance, source, previous = None, None, None
    for sample in samples:
        if not isinstance(sample, dict) or sample.get("coherent") is not True:
            raise ValueError("noncoherent sample: no reference integration")
        if sample.get("timebase") != "host_monotonic_receive":
            raise ValueError("recorded host_monotonic_receive timestamps required")
        if sample.get("source_kind") not in ("synthetic", "iio_buffer"):
            raise ValueError("coherent synthetic or iio_buffer source required")
        identity = sample.get("instance_id")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("explicit nonempty instance_id required")
        if instance is None:
            instance, source = identity, sample["source_kind"]
        if identity != instance or sample["source_kind"] != source:
            raise ValueError("device instance or source changed")
        stamp = _integer(sample.get("timestamp_ns"), "timestamp_ns")
        number = _integer(sample.get("sample_number"), "sample_number")
        if stamp > (1 << 63) - 1 or number > (1 << 64) - 1:
            raise ValueError("timestamp/counter exceeds the recorded IIO integer width")
        _vector(sample.get("gyro_raw"), "gyro_raw")
        _vector(sample.get("accel_raw"), "accel_raw")
        if any(value in (-32768, 32767) for value in sample["gyro_raw"]):
            raise ValueError("gyro reaches int16 endpoint; possible clipping invalidates reference integration")
        if previous is not None:
            if stamp <= previous["timestamp_ns"]:
                raise ValueError("duplicate or backward timestamp")
            if number != previous["sample_number"] + 1:
                raise ValueError("sample counter gap, duplicate or reset")
            if stamp - previous["timestamp_ns"] > max_gap_ns:
                raise ValueError("timestamp gap exceeds explicitly selected bound")
        previous = sample
    return {"instance_id": instance, "source_kind": source, "sample_count": len(samples),
            "timebase": "host_monotonic_receive", "max_gap_ns": max_gap_ns,
            "counter_scope": "driver-accepted IMU reports; not hardware/RF loss detection",
            "device_sample_clock_verified": False, "hardware_packet_loss_known": False}


def _mapping(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"X", "Y", "Z"}:
        raise ValueError("explicit X/Y/Z mapping hypothesis required")
    indices = []
    for item in value.values():
        if not isinstance(item, dict) or set(item) != {"raw_axis", "sign"}:
            raise ValueError("mapping entries require raw_axis and sign")
        if type(item["raw_axis"]) is not int or item["raw_axis"] not in range(3):
            raise ValueError("raw_axis must be 0, 1 or 2")
        if type(item["sign"]) is not int or item["sign"] not in (-1, 1):
            raise ValueError("mapping sign must be -1 or 1")
        indices.append(item["raw_axis"])
    if set(indices) != {0, 1, 2}:
        raise ValueError("axis mapping must be a permutation")
    return value


def _span(samples, indices, window, name):
    bounds = window.get(name)
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError(f"{name}: recorded start/end timestamps required")
    for stamp in bounds:
        _integer(stamp, name)
        if stamp not in indices:
            raise ValueError(f"{name}: boundary is not a recorded sample timestamp")
    start, end = (indices[stamp] for stamp in bounds)
    if start >= end:
        raise ValueError(f"{name}: at least two ordered samples required")
    return samples[start:end + 1]


def _stats(rows, key):
    return [{"mean": statistics.mean(row[key][axis] for row in rows),
             "std_population": statistics.pstdev(row[key][axis] for row in rows),
             "min": min(row[key][axis] for row in rows),
             "max": max(row[key][axis] for row in rows)} for axis in range(3)]


def analyze_reference(samples, metadata, max_gap_ns):
    """Integrate recorded raw channels with an explicit, experimental rest bias.

    A single invalid interval invalidates the whole input, including intervals
    outside motion windows. No dropped intervals, interpolation or extrapolation.
    External reference accuracy and host receive jitter remain unverified.
    """
    stream = validate_samples(samples, max_gap_ns)
    if (not isinstance(metadata, dict) or type(metadata.get("schema_version")) is not int or
            metadata.get("schema_version") != 1 or metadata.get("kind") != "experimental_known_angle"):
        raise ValueError("experimental known-angle metadata schema v1 required")
    windows = metadata.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("independent known-angle windows required")
    mapping = _mapping(metadata.get("axis_mapping"))
    indices = {row["timestamp_ns"]: index for index, row in enumerate(samples)}
    validated, labels, previous_end = [], set(), -1
    # Validate all metadata before calculating an integral.
    for window in windows:
        if not isinstance(window, dict):
            raise ValueError("reference window object required")
        label = window.get("label")
        if not isinstance(label, str) or not label.strip() or label in labels:
            raise ValueError("unique nonempty reference label required")
        labels.add(label)
        if not isinstance(window.get("physical_axis"), str) or window["physical_axis"] not in ("X", "Y", "Z"):
            raise ValueError("physical axis label must be X, Y or Z")
        if type(window.get("known_angle_deg")) not in (int, float) or window["known_angle_deg"] not in (-180, -90, 90, 180):
            raise ValueError("independently marked signed 90/180 degree rotation required")
        if window.get("reference_kind") not in ("external_angle_marker", "angle_fixture"):
            raise ValueError("angle must come from an external reference, not this IMU")
        if not isinstance(window.get("angle_reference_description"), str) or not window["angle_reference_description"].strip():
            raise ValueError("external angle reference description required")
        if window.get("reference_completed") is not True or window.get("motion_bounds_include_stationary_margins") is not True:
            raise ValueError("complete marked rotation and stationary integration margins required")
        before, motion, after = (_span(samples, indices, window, name)
                                  for name in ("rest_before", "motion", "rest_after"))
        if not (previous_end < before[0]["timestamp_ns"] < before[-1]["timestamp_ns"] <
                motion[0]["timestamp_ns"] < motion[-1]["timestamp_ns"] <
                after[0]["timestamp_ns"] < after[-1]["timestamp_ns"]):
            raise ValueError("ordered, separated, nonoverlapping rest/motion windows required")
        previous_end = after[-1]["timestamp_ns"]
        validated.append((window, before, motion, after))
    results = []
    for window, before, motion, after in validated:
        before_stats, after_stats = _stats(before, "gyro_raw"), _stats(after, "gyro_raw")
        rest_stats = _stats(before + after, "gyro_raw")
        bias = [value["mean"] for value in rest_stats]
        raw_integral = [sum(((a["gyro_raw"][axis] - bias[axis]) +
                             (b["gyro_raw"][axis] - bias[axis])) * 0.5 *
                            (b["timestamp_ns"] - a["timestamp_ns"]) / 1e9
                            for a, b in zip(motion, motion[1:])) for axis in range(3)]
        profiles = []
        for profile, factor in PROFILES.items():
            angles = [value * float(factor) for value in raw_integral]
            comparison = None
            if mapping is not None:
                target = mapping[window["physical_axis"]]
                projected = angles[target["raw_axis"]] * target["sign"]
                expected = window["known_angle_deg"]
                comparison = {"explicit_mapping_hypothesis": target,
                              "projected_angle_deg": projected,
                              "error_deg": projected - expected,
                              "relative_error": (projected - expected) / abs(expected)}
            profiles.append({"assumed_sensor": "LSM6DS3TR-C", "assumed_range_dps": profile,
                             "dps_per_count": float(factor), "angle_raw_axes_deg": angles,
                             "angle_raw_axes_rad": [math.radians(x) for x in angles],
                             "physical_axis_comparison": comparison,
                             "profile_confirmed": False, "selected_for_runtime": False})
        result = {"label": window["label"], "physical_axis_label": window["physical_axis"],
                  "known_angle_deg": window["known_angle_deg"],
                  "angle_reference_description": window["angle_reference_description"],
                  "external_reference_accuracy_verified": False,
                  "motion_timestamp_bounds_ns": list(window["motion"]),
                  "motion_sample_count": len(motion),
                  "integrated_duration_ns": motion[-1]["timestamp_ns"] - motion[0]["timestamp_ns"],
                  "bias_raw_experimental": bias,
                  "rest_before_gyro_raw_stats": before_stats,
                  "rest_after_gyro_raw_stats": after_stats,
                  "bias_shift_after_minus_before_raw": [after_stats[i]["mean"] - before_stats[i]["mean"] for i in range(3)],
                  "raw_integral_count_seconds": raw_integral, "profiles": profiles,
                  "axis_mapping_verified": False, "calibration_verified": False}
        if mapping is not None:
            target = mapping[window["physical_axis"]]
            projection = raw_integral[target["raw_axis"]] * target["sign"]
            result["empirical_dps_per_count_under_mapping_hypothesis"] = window["known_angle_deg"] / projection if projection else None
            other = math.sqrt(sum(value * value for i, value in enumerate(raw_integral) if i != target["raw_axis"]))
            result["off_axis_integral_fraction_under_mapping_hypothesis"] = other / abs(projection) if projection else None
        results.append(result)
    return {"schema_version": 1, "kind": "experimental_known_angle_analysis", "stream": stream,
            "body_frame_convention": dict(BODY_FRAME), "axis_mapping_hypothesis": mapping,
            "windows": results, "complete_input_validated": True, "intervals_discarded": 0,
            "timestamps_reconstructed": False, "timestamp_interpolation": False,
            "bias_method": "arithmetic mean of explicitly selected bracketing rest samples, experimental",
            "integration_method": "trapezoidal raw-count integral on recorded host receive timestamps",
            "limitations": ["Host receive timestamps are not the sensor sampling clock.",
                            "USB transport jitter and sensor averaging remain unknown.",
                            "Counter continuity does not prove absence of device/RF packet loss.",
                            "Rest labels, physical reference accuracy and axis mapping require human validation."],
            "calibration_verified": False, "selected_as_actual_hardware_profile": False,
            "sdl_runtime_enable": False}


def _regular_text(path):
    path = Path(path)
    resolved = path.resolve(strict=True)
    if any(resolved == root or root in resolved.parents for root in map(Path, ("/dev", "/proc", "/sys"))):
        raise ValueError("saved files only; device/proc/sys paths forbidden")
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_size > 64 * 1024 * 1024:
        raise ValueError("saved regular file <=64 MiB required; no devices or symlinks")
    with path.open("r", encoding="utf-8") as stream:
        content = stream.read(64 * 1024 * 1024 + 1)
    if len(content) > 64 * 1024 * 1024:
        raise ValueError("saved file grew beyond maximum size")
    return content


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="print one offline session plan; no timer or GUI")
    plan.add_argument("--session", choices=tuple(SESSION_SPECS), default="yaw90left")
    commands.add_parser("metadata-schema", help="print reference-window metadata schema")
    analyze = commands.add_parser("analyze", help="analyze existing coherent JSONL and marker JSON only")
    analyze.add_argument("samples")
    analyze.add_argument("metadata")
    analyze.add_argument("--max-gap-ns", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = calibration_plan(args.session)
        elif args.command == "metadata-schema":
            result = metadata_schema()
        else:
            samples = [json.loads(line) for line in _regular_text(args.samples).splitlines() if line.strip()]
            result = analyze_reference(samples, json.loads(_regular_text(args.metadata)), args.max_gap_ns)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
