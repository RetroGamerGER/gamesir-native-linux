#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Check the shared C core against saved packets and the existing own parser."""
from collections import Counter
import ctypes as c
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

from project_paths import PROJECT, BUILD, RESULTS, local_directory

sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "tools/offline"))
from gamesir_offline.protocol import decode_packet

class Frame(c.Structure):
    _fields_ = [("kind", c.c_int), ("buttons", c.c_uint16), ("sticks", c.c_int16 * 4),
        ("triggers", c.c_uint16 * 2), ("gyro", c.c_int16 * 3), ("accel", c.c_int16 * 3),
        ("extras", c.c_uint8 * 2), ("sequence", c.c_uint8), ("guide", c.c_uint8), ("ack", c.c_uint8)]

class SensorAxis(c.Structure):
    _fields_ = [("numerator", c.c_uint32), ("denominator", c.c_uint32),
        ("bias_raw", c.c_int32), ("source", c.c_uint8), ("sign", c.c_int8)]

class Calibration(c.Structure):
    _fields_ = [("verified", c.c_uint32), ("resolution", c.c_uint32), ("axis", SensorAxis * 3)]

class ExperimentalAccelScale(c.Structure):
    _fields_ = [("counts_per_g_num", c.c_uint32), ("counts_per_g_den", c.c_uint32)]

def main():
    build = BUILD
    build.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
        str(PROJECT / "src/gs_protocol.c"), str(PROJECT / "src/gs_sensor.c"), str(PROJECT / "src/gs_runtime.c"), "-o", str(build / "protocol.so")], check=True)
    lib = c.CDLL(str(build / "protocol.so"))
    lib.gs_decode.argtypes = [c.c_void_p, c.c_size_t, c.POINTER(Frame)]
    lib.gs_motor_packet.argtypes = [c.c_void_p, c.c_uint8, c.c_void_p]
    lib.gs_transition.argtypes = [c.c_void_p, c.c_uint]
    lib.gs_gip_init.argtypes = [c.c_void_p, c.c_uint8, c.c_uint]
    lib.gs_runtime_init.argtypes = [c.c_void_p, c.c_uint, c.c_int]
    lib.gs_runtime_accepts.argtypes = [c.c_void_p, c.c_int]
    modes = {pid: (c.c_uint64 * 16)() for pid in ("100a", "109c")}
    for pid, state in modes.items():
        assert lib.gs_runtime_init(state, int(pid, 16), 0) == 0
    lib.gs_sensor_convert.argtypes = [c.POINTER(Calibration), c.c_void_p, c.c_void_p]
    lib.gs_accel_convert_experimental.argtypes = [c.POINTER(ExperimentalAccelScale), c.c_void_p, c.c_void_p]
    profile_path = PROJECT / "docs/sdl-sensor-calibration.json"
    profile = json.loads(profile_path.read_text())
    accel = profile["accelerometer"]
    num, den = accel["counts_per_g"], accel["counts_per_g_denominator"]
    assert type(num) is int and type(den) is int and 0 < num <= 1000000 and 0 < den <= 1000000
    assert accel["experimental_conversion"]["enabled_for_offline_replay"] is True
    assert accel["experimental_conversion"]["apply_bias"] is False
    assert accel["experimental_conversion"]["axis_order"] == "wire_A0_A1_A2"
    assert accel["experimental_conversion"]["standard_gravity_m_s2"] == 9.80665
    assert accel["scale_verified"] is False and accel["orientation_verified"] is False
    assert profile["runtime_enable"] is False and profile["verified_flags"] == 0
    assert profile["gyroscope"]["counts_per_degree_per_second"] is None
    assert profile["gyroscope"]["derive_from_accelerometer"] is False
    assert profile["gyroscope"]["fallback_factor"] is None
    experimental = ExperimentalAccelScale(num, den)
    unverified = Calibration()
    counts = Counter()
    capture = local_directory("capture_dir")
    evidence = json.loads((PROJECT / "docs/imu-calibration-analysis.json").read_text())
    assert profile["scope"]["capture_sha256"] == evidence["capture_sha256"]
    hashes = {}
    for name in ("original-usbmon8.pcapng", "derived/parser-records.jsonl", "derived/telemetry-raw.json"):
        with (capture / name).open("rb") as src:
            actual = hashlib.file_digest(src, "sha256").hexdigest()
        expected = next(e["sha256"] for e in evidence["verified_evidence"] if e["path"] == name)
        assert actual == expected, (name, "saved evidence checksum mismatch")
        hashes[name] = actual
    telemetry = {r["timestamp_us"]: r for r in json.loads((capture / "derived/telemetry-raw.json").read_text())}
    physical = []
    quiet_norms = []
    max_error_m_s2 = 0.0
    with (capture / "derived/parser-records.jsonl").open() as src:
        for line in src:
            r = json.loads(line)
            if r["status"] != 0 or r["capture_truncated"]:
                counts["failed_or_truncated_skipped"] += 1
                continue
            d = bytes.fromhex(r["data_hex"])
            if r["endpoint"] == "02":
                if len(d) == 13 and d[0] == 9:
                    out = c.create_string_buffer(13)
                    assert lib.gs_motor_packet(out, d[2], d[6:10]) == 13
                    assert out.raw == d
                    counts["motor_exact_bytes"] += 1
                elif len(d) in (5, 7, 6) and d[:2] in (b"\x05\x20", b"\x0a\x20", b"\x06\x20"):
                    step = {5: 0, 7: 1, 6: 2}[len(d)]
                    out = c.create_string_buffer(64)
                    assert lib.gs_gip_init(out, d[2], step) == len(d)
                    assert out.raw[:len(d)] == d
                    counts["gip_initialization_exact_bytes"] += 1
                elif len(d) == 64 and d[:2] == b"\x0f\x00" and d[3] in (1, 2):
                    out = c.create_string_buffer(64)
                    if d[3] == 2: lib.gs_heartbeat(out, d[2])
                    else: lib.gs_info_request(out, d[2], d[4])
                    assert out.raw == d
                    counts["maintenance_exact_bytes"] += 1
                continue
            f = Frame()
            kind = lib.gs_decode(d, len(d), c.byref(f))
            old = decode_packet(d)
            mode_accepted = lib.gs_runtime_accepts(modes[r["device"]["pid"]], kind)
            assert bool(mode_accepted) == (old.kind in ("x360_input", "gip_input_basic", "gamesir_telemetry"))
            if mode_accepted:
                counts["native_mode_policy_accepted"] += 1
            fields = old.fields
            if old.kind == "gamesir_telemetry":
                assert (r["device"]["vid"], r["device"]["pid"]) == (profile["scope"]["vid"], profile["scope"]["pid"])
                assert kind == 3
                assert list(f.gyro) == fields["gyro_raw_i16"]
                assert list(f.accel) == fields["accel_raw_i16"]
                assert list(f.extras) == list(d[57:59])
                saved = telemetry[r["timestamp_us"]]
                assert list(f.accel) == saved["accel_raw"] and list(f.gyro) == saved["gyro_raw"]
                before_frame = bytes(f)
                converted = (c.c_int32 * 3)()
                # Explicit experimental API; raw A0/A1/A2 order, no bias correction.
                assert lib.gs_accel_convert_experimental(c.byref(experimental), f.accel, converted) == 1
                assert bytes(f) == before_frame  # raw accel, gyro, buttons and sticks survive unchanged
                si = [v / 1000000 for v in converted]
                for raw, value in zip(f.accel, si):
                    reference = raw * 9.80665 * den / num
                    error = abs(value - reference)
                    assert error <= 0.500001e-6, (raw, value, reference)
                    max_error_m_s2 = max(max_error_m_s2, error)
                physical.append(si)
                if 67.03886 <= saved["seconds"] <= 73.03886:
                    quiet_norms.append(math.sqrt(sum(v * v for v in si)))
                counts["experimental_accel_frames_converted"] += 1
                counts["gyro_frames_preserved_raw"] += 1
                for group in (f.gyro, f.accel):
                    out = (c.c_int32 * 3)(101, 102, 103)
                    assert lib.gs_sensor_convert(c.byref(unverified), group, out) == -1
                    assert list(out) == [101, 102, 103]
                    counts["unverified_sensor_groups_blocked"] += 1
            elif old.kind in ("gip_input_basic", "x360_input"):
                assert kind == (1 if old.kind == "gip_input_basic" else 2)
                assert list(f.sticks) == list(fields["sticks_raw_i16"].values())
                if kind == 1:
                    assert list(f.triggers) == list(fields["triggers_raw_u16"].values())
                    assert f.buttons == int.from_bytes(d[4:6], "little")
                else:
                    assert list(f.triggers) == [(v * 1023 + 127) // 255 for v in fields["triggers_u8"].values()]
                    names = {2: "menu", 3: "view", 4: "a", 5: "b", 6: "x", 7: "y", 8: "up", 9: "down", 10: "left", 11: "right", 12: "lb", 13: "rb", 14: "ls", 15: "rs"}
                    for bit, name in names.items(): assert bool(f.buttons & (1 << bit)) == fields["buttons"][name]
                    assert bool(f.guide) == fields["buttons"]["home"]
            else:
                assert kind in (0, 5), (kind, old.kind, d.hex())
            counts[old.kind] += 1
    for step, r in enumerate(json.loads((capture / "derived/initialization-0008-packets.json").read_text())):
        out = c.create_string_buffer(8)
        assert lib.gs_transition(out, step) == 8
        assert out.raw.hex() == r["data_hex"]
        counts["handshake_exact_bytes"] += 1
    assert counts["handshake_exact_bytes"] == 9
    assert counts["motor_exact_bytes"] == 10
    assert counts["gip_initialization_exact_bytes"] == 21
    assert counts["native_mode_policy_accepted"] == 17448
    assert counts["gamesir_telemetry"] == 12204
    assert counts["gip_input_basic"] == 3786
    assert counts["x360_input"] == 1458
    assert counts["unverified_sensor_groups_blocked"] == 24408
    assert counts["experimental_accel_frames_converted"] == 12204
    assert counts["gyro_frames_preserved_raw"] == 12204
    assert len(quiet_norms) == 375
    # A statistical check on a saved still window, not a calibration proof.
    quiet_median = statistics.median(quiet_norms)
    norm_raw = statistics.median(math.sqrt(sum(v * v for v in r["accel_raw"]))
        for r in telemetry.values() if 67.03886 <= r["seconds"] <= 73.03886)
    assert abs(quiet_median - norm_raw * 9.80665 * den / num) <= math.sqrt(3) * 0.500001e-6
    experimental_result = {
        "passed": True, "hardware_access": False, "kernel_build_or_changes": False,
        "status": "experimental_not_verified_calibration", "profile": str(profile_path.relative_to(PROJECT)),
        "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        "capture_sha256_verified": hashes["original-usbmon8.pcapng"],
        "current_input_sha256_verified": hashes, "sample_count": len(physical),
        "counts_per_g": {"numerator": num, "denominator": den},
        "output_unit": "m/s^2 (C integer output: micrometres/s^2)",
        "axis_order": "wire_A0_A1_A2", "axis_orientation_verified": False,
        "bias_applied": False, "includes_gravity": True,
        "max_abs_rounding_error_m_s2": max_error_m_s2,
        "range_per_wire_axis_m_s2": [
            [min(v[i] for v in physical), max(v[i] for v in physical)] for i in range(3)],
        "quiet_window": {"seconds": [67.03886, 73.03886], "samples": len(quiet_norms),
            "median_norm_raw_counts": norm_raw, "median_norm_m_s2": quiet_median,
            "median_norm_g": quiet_median / 9.80665,
            "deviation_percent_from_one_g": (quiet_median / 9.80665 - 1) * 100,
            "establishes_calibration": False},
        "gyro_factor": None, "gyro_derived_from_accel": False, "gyro_frames_unchanged": 12204,
        "strict_unverified_sensor_groups_blocked": 24408, "final_sdl_release": False,
        "limitations": ["experimental common accel scale", "wire axes only; SDL orientation unresolved",
                        "no bias or temperature correction", "gyro physical factor unresolved"]}
    (RESULTS / "experimental-accel-validation.json").write_text(json.dumps(experimental_result, indent=2) + "\n")
    result = {"passed": True, "hardware_access": False, "runtime_calibration_ready": False, "counts": dict(counts)}
    (RESULTS / "core-capture-validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
