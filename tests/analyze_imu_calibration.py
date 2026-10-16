#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Saved-file-only IMU evidence analysis. Never imports or starts Deadband."""
import datetime as dt
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import struct

from project_paths import PROJECT, RESULTS, local_directory

CAPTURE = local_directory("capture_dir")
SOURCE = local_directory("deadband_source")
INSTALLED = local_directory("deadband_installed")
EXPECTED_ORIGINAL = "4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89"


def digest(p):
    assert p.is_file() and not p.is_symlink(), p
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def timestamp_us(value):
    delta = dt.datetime.fromisoformat(value) - dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def distribution(values):
    v = sorted(values)
    assert len(v) > 1
    return {"count": len(v), "mean": st.mean(v), "median": st.median(v),
            "population_std": st.pstdev(v), "min": v[0], "max": v[-1],
            "p01": v[math.floor(.01 * (len(v) - 1))],
            "p05": v[math.floor(.05 * (len(v) - 1))],
            "p95": v[math.floor(.95 * (len(v) - 1))],
            "p99": v[math.floor(.99 * (len(v) - 1))]}


def summarize(rows):
    assert rows
    result = {"count": len(rows), "first_timestamp_us": rows[0]["timestamp_us"],
              "last_timestamp_us": rows[-1]["timestamp_us"]}
    for key in ["gyro_raw", "accel_raw"]:
        columns = list(zip(*(r[key] for r in rows)))
        result[key] = [distribution(c) for c in columns]
        energy = [st.pvariance(c) for c in columns]
        result[key + "_variance_fraction"] = [e / sum(energy) for e in energy]
    result["accel_norm_raw"] = distribution([math.sqrt(sum(v * v for v in r["accel_raw"])) for r in rows])
    result["gyro_norm_raw"] = distribution([math.sqrt(sum(v * v for v in r["gyro_raw"])) for r in rows])
    return result


def global_statistics(rows):
    """Every sample contributes; low-motion windows are heuristic, not known poses."""
    intervals = [b["timestamp_us"] - a["timestamp_us"] for a, b in zip(rows, rows[1:])]
    raw_keys = ["gyro_raw", "accel_raw"]
    duplicate_six_axes = sum(a["gyro_raw"] + a["accel_raw"] == b["gyro_raw"] + b["accel_raw"]
                             for a, b in zip(rows, rows[1:]))
    blocks = {}
    for r in rows:
        blocks.setdefault(math.floor(r["seconds"] / 2), []).append(r)
    quiet = []
    for block, samples in sorted(blocks.items()):
        if len(samples) < 120 or samples[-1]["timestamp_us"] - samples[0]["timestamp_us"] < 1900000:
            continue
        s = summarize(samples)
        if (max(x["population_std"] for x in s["gyro_raw"]) <= 5
                and s["gyro_norm_raw"]["max"] <= 25
                and max(x["population_std"] for x in s["accel_raw"]) <= 25):
            quiet.append({"relative_window_seconds": [block * 2, block * 2 + 2], "summary": s})
    norms = [math.sqrt(sum(v*v for v in r["accel_raw"])) for r in rows]
    directions = []
    for q in quiet:
        a = [d["mean"] for d in q["summary"]["accel_raw"]]
        length = math.sqrt(sum(v*v for v in a))
        directions.append([v / length for v in a])
    separation = max((math.degrees(math.acos(max(-1, min(1, sum(x*y for x,y in zip(a,b))))))
                      for a in directions for b in directions), default=0)
    return {"summary_all_samples": summarize(rows),
        "host_completion_intervals_us": distribution(intervals),
        "interval_counts": {"less_than_8_ms": sum(t < 8000 for t in intervals),
                            "8_to_less_than_24_ms": sum(8000 <= t < 24000 for t in intervals),
                            "at_least_24_ms": sum(t >= 24000 for t in intervals),
                            "at_least_32_ms": sum(t >= 32000 for t in intervals)},
        "host_observed_rate_hz": (len(rows)-1) * 1e6 / (rows[-1]["timestamp_us"]-rows[0]["timestamp_us"]),
        "host_intervals_are_not_sensor_internal_odr": True,
        "identical_consecutive_six_axis_values": duplicate_six_axes,
        "signed_16bit_endpoint_counts": {key: [sum(r[key][i] in [-32768, 32767] for r in rows)
                                               for i in range(3)] for key in raw_keys},
        "per_axis_distinct_raw_values": {key: [len({r[key][i] for r in rows}) for i in range(3)] for key in raw_keys},
        "accel_norm_within_candidate_percent_counts": {str(p): sum(abs(n/8192-1) <= p/100 for n in norms)
                                                        for p in [1, 2, 5, 10]},
        "dynamic_norms_are_not_scale_references": True,
        "quiet_window_selection": {"block_width_seconds": 2, "minimum_samples": 120,
            "minimum_span_us": 1900000, "maximum_axis_gyro_std_raw": 5, "maximum_gyro_norm_raw": 25,
            "maximum_axis_accel_std_raw": 25,
            "heuristic_not_proof_of_static_pose_or_zero_translation": True},
        "quiet_windows": quiet,
        "quiet_orientation_coverage": {"window_count": len(quiet),
            "sample_count": sum(q["summary"]["count"] for q in quiet),
            "maximum_pairwise_mean_gravity_direction_degrees": separation,
            "minimum_A1_fraction_of_mean_vector": min((a[1] for a in directions), default=None),
            "median_norm_range_raw": [min(q["summary"]["accel_norm_raw"]["median"] for q in quiet),
                                      max(q["summary"]["accel_norm_raw"]["median"] for q in quiet)],
            "not_six_independent_known_poses": True},
        "all_sample_norm_histogram_256_count_bins": [{"lower_inclusive": b*256, "upper_exclusive": (b+1)*256,
                                                       "count": n} for b, n in sorted(Counter(math.floor(v/256) for v in norms).items())]}


def main():
    original = digest(CAPTURE / "original-usbmon8.pcapng")
    assert original == EXPECTED_ORIGINAL, "Original capture checksum mismatch"
    manifests = {}
    for filename in ["SHA256SUMS", "SHA256SUMS-ANALYSIS"]:
        for line in (CAPTURE / filename).read_text().splitlines():
            sha, name = line.split("  ", 1)
            manifests[name] = sha
    selected = ["derived/telemetry-raw.json", "derived/parser-records.jsonl", "events.jsonl"]
    evidence = [{"path": "original-usbmon8.pcapng", "sha256": original, "verified": True}]
    for name in selected:
        found = digest(CAPTURE / name)
        assert found == manifests[name], name
        evidence.append({"path": name, "sha256": found, "verified": True})
    rows = json.loads((CAPTURE / selected[0]).read_text())
    assert len(rows) == 12204
    # Independently decode wire bytes and verify each analysis sample.
    packets = {}
    for line in (CAPTURE / selected[1]).read_text().splitlines():
        r = json.loads(line)
        b = bytes.fromhex(r["data_hex"])
        if (r["endpoint"] == "82" and r["status"] == 0 and not r["capture_truncated"]
                and len(b) == 64 and b[:2] == b"\x10\x00" and b[3:5] == b"\x3c\xe0"):
            assert r["device"]["vid"] == "3537" and r["device"]["pid"] == "109c"
            stamp = r["timestamp_us"]
            assert stamp not in packets, "Duplicate timestamp needs explicit disambiguation"
            packets[stamp] = struct.unpack_from("<6h", b, 17)
    assert len(packets) == len(rows)
    for r in rows:
        assert tuple(r["gyro_raw"] + r["accel_raw"]) == packets[r["timestamp_us"]]
    assert all(a["timestamp_us"] < b["timestamp_us"] for a, b in zip(rows, rows[1:]))

    source_files = []
    for name, ranges in [
        ("vendors/gamesir/models/g7pro/protocol.py", [[361, 410], [214, 235]]),
        ("reader.py", [[788, 808]]), ("bridge.py", [[340, 352]]),
        ("gs_state.py", [[24, 28]]), ("qml/App/MotionSensors.qml", [[1, 80]]),
        ("tests/test_motion.py", [[82, 108]]),
    ]:
        p = SOURCE / name
        installed = INSTALLED / name
        source_files.append({"path": name, "sha256": digest(p), "line_ranges": ranges,
            "installed_identical": installed.is_file() and digest(installed) == digest(p),
            "url": "https://github.com/broroeror/gamesir-linux-tools/blob/771b28ae75b0a614a6a7fec9aa606606a27b3b8d/" + name})
    # Packaging need not install upstream tests; application files must match.
    assert all(r["installed_identical"] for r in source_files if not r["path"].startswith("tests/"))
    events = [json.loads(line) for line in (CAPTURE / "events.jsonl").read_text().splitlines()]
    cues = {e["data"]["phase"]: e for e in events if e["event"] == "phase_cue"}
    phases = {}
    for name in ["imu_still", "gyro_yaw", "gyro_pitch", "gyro_roll", "accel_left_right", "accel_front_back", "accel_up_down"]:
        cue = cues[name]
        start = timestamp_us(cue["utc"])
        chosen = [r for r in rows if start + 2000000 <= r["timestamp_us"] < start + 8000000]
        phases[name] = {"cue_utc": cue["utc"], "cue_seconds": cue["seconds_from_verified_recorder"],
                       "window": "cue+2 seconds <= sample < cue+8 seconds", "instruction": cue["data"]["instruction"],
                       "summary": summarize(chosen), "labels_are_instructions_not_verified_actions": True}
    still = phases["imu_still"]["summary"]
    norm = still["accel_norm_raw"]["median"]
    gyro = still["gyro_raw"]
    start = timestamp_us(cues["gyro_yaw"]["utc"])
    # Explicit heuristic for motion timing only, not an angular-speed calibration.
    burst = []
    detected = None
    for r in rows:
        if r["timestamp_us"] < start:
            continue
        if math.sqrt(sum(v*v for v in r["gyro_raw"])) > 100:
            if burst and r["timestamp_us"] - burst[-1]["timestamp_us"] > 40000:
                burst = []
            burst.append(r)
            if r["timestamp_us"] - burst[0]["timestamp_us"] >= 250000:
                detected = burst[0]
                break
        else:
            burst = []
    timing = {"heuristic": "gyro norm > 100 raw counts continuously for >=250 ms; sample gaps <=40 ms",
        "first_burst_timestamp_us": detected["timestamp_us"] if detected else None,
        "seconds_after_yaw_cue": (detected["timestamp_us"] - start) / 1e6 if detected else None,
        "not_a_verified_movement_direction": True}
    early = [r for r in rows if 47 <= r["seconds"] < 64]
    trailing = [r for r in rows if 235 <= r["seconds"] < 240]
    result = {"schema_version": 2, "offline_only": True, "hardware_access": False,
        "capture_sha256": original, "verified_evidence": evidence, "wire_samples_verified": len(rows),
        "source_commit": "771b28ae75b0a614a6a7fec9aa606606a27b3b8d", "source_files": source_files,
        "wire_layout": {"gyro_signed_le16_offsets": [17, 19, 21], "accel_signed_le16_offsets": [23, 25, 27]},
        "global_statistics": global_statistics(rows),
        "phase_windows": phases, "additional_windows": {"early_flat_T47_to64": summarize(early), "trailing_T235_to240": summarize(trailing)},
        "motion_timing": timing,
        "candidate_only": {"accel_counts_per_g": 8192, "still_norm_median": norm,
            "difference_percent_from_8192": (norm / 8192 - 1) * 100,
            "still_gyro_mean_raw": [g["mean"] for g in gyro],
            "scale_verified": False, "gyro_scale_counts_per_degree_per_second": None,
            "sdl_from_accel_wire_axes": None, "sdl_from_gyro_wire_axes": None,
            "bias_verified": False, "usable_as_runtime_calibration": False},
        "missing": ["independent angular reference or documented sensor sensitivity",
                    "signed mapping from every wire axis to controller/SDL axes",
                    "multiple known static poses to separate gravity, bias and per-axis gains",
                    "verified movement times/directions; cue times alone are insufficient"],
        "timestamp_limit": {"available": "host capture timestamps", "device_clock_proven": False,
            "blocks_sdl_with_host_event_timestamps": False,
            "note": "No invented device clock. Angle integration needs checked delivery intervals/latency."}}
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "imu-calibration-analysis.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"wire_samples_verified": len(rows), "gyro_still_mean": [g["mean"] for g in gyro],
        "accel_still_mean": [a["mean"] for a in still["accel_raw"]], "accel_norm_median": norm,
        "difference_percent_from_8192": result["candidate_only"]["difference_percent_from_8192"],
        "motion_timing": timing, "runtime_calibration_ready": False, "report": str(output)}))


if __name__ == "__main__":
    main()
