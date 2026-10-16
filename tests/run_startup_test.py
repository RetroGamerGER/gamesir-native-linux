#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build the transport-free C startup core; saved bytes + virtual clock only."""
import hashlib
import json
import subprocess

from project_paths import PROJECT, BUILD, RESULTS


def byte_array(value):
    return "{" + ",".join(f"0x{b:02x}" for b in bytes.fromhex(value)) + "}"


def main():
    BUILD.mkdir(exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    fixture_path = PROJECT / "fixtures/startup-capture.json"
    fixture = json.loads(fixture_path.read_text())
    assert fixture["origin"] == "real_saved_target_packets_two_independent_recordings"
    lines = ["/* Generated only in build/ from saved target-only evidence. */",
             "struct captured_tx { unsigned long long submit_us, complete_us; unsigned int length; unsigned char data[64]; };"]
    for key, name, count in (("transition", "transition", 9), ("native_init", "native", 6)):
        rows = fixture[key]["packets"]
        assert len(rows) == count
        lines.append(f"static const struct captured_tx captured_{name}[] = {{")
        for row in rows:
            assert row["status"] == 0 and row["endpoint"] == 2
            assert row["length"] == len(bytes.fromhex(row["data_hex"]))
            assert 0 <= row["submit_us"] <= row["complete_us"]
            lines.append("{%dULL,%dULL,%d,%s}," % (row["submit_us"], row["complete_us"], row["length"], byte_array(row["data_hex"])))
        lines.append("};")
    for key in ("remove_us", "add_us"):
        lines.append(f"static const unsigned long long captured_{key} = {fixture['transition'][key]}ULL;")
    imu = fixture["native_init"]["imu_after_settle"]
    lines.append(f"static const unsigned long long captured_imu_us = {imu['complete_us']}ULL;")
    lines.append(f"static const unsigned char captured_imu[] = {byte_array(imu['data_hex'])};")
    lines.append(f"static const unsigned char captured_pad[] = {byte_array(fixture['native_init']['first_gamepad']['data_hex'])};")
    (BUILD / "startup_fixture.h").write_text("\n".join(lines) + "\n")
    sources = ["src/gs_protocol.c", "src/gs_runtime.c", "src/gs_startup.c", "tests/test_startup.c"]
    args = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-I", str(BUILD),
            *[str(PROJECT / s) for s in sources], "-o", str(BUILD / "test_startup")]
    compiled = subprocess.run(args, capture_output=True, text=True, timeout=30, check=True)
    tested = subprocess.run([str(BUILD / "test_startup")], capture_output=True, text=True, timeout=20)
    (RESULTS / "startup-test.log").write_text(compiled.stdout + compiled.stderr + tested.stdout + tested.stderr)
    tested.check_returncode()
    report = {"passed": True, "hardware_access": False, "system_changes": False,
              "native_cold_start_hardware_validated": False,
              "method": "Actual shared C startup state machine; synthetic clock/transport/port ownership. Two recorded segments are joined synthetically, not a new capture.",
              "sanitizers": ["address", "undefined"], "coverage": tested.stdout.strip(),
              "source_sha256": {s: hashlib.sha256((PROJECT / s).read_bytes()).hexdigest()
                                for s in sources + ["src/gs_startup.h", "src/gs_protocol.h", "src/gs_runtime.h",
                                                    "tests/run_startup_test.py", "fixtures/startup-capture.json"]},
              "limits": ["No live USB or kernel lifecycle executed.",
                         "This shared-core test excludes the kernel coordinator and activation interface; see kernel-startup-test.json for their separate simulation.",
                         "Returned TX intents do not open, claim, write, bind or initialize actual hardware.",
                         "READY marks completed init USB transfers and fresh raw IMU; firmware acknowledgement and gamepad evidence are separate.",
                         "Topology tokens simulate arbitrary root/hub ports; this test does not execute live Linux topology discovery or token allocation.",
                         "Gyroscope scale and physical axes remain uncalibrated."]}
    (RESULTS / "startup-test.json").write_text(json.dumps(report, indent=2) + "\n")
    print(tested.stdout.strip())


if __name__ == "__main__":
    main()
