#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile and test pure conversion code locally, with sanitizers, no devices."""
import json
from pathlib import Path
import shlex
import subprocess

from project_paths import PROJECT, BUILD, RESULTS

BUILD.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)
cmd = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
       "-fno-sanitize-recover=all", "-g", str(PROJECT / "src/gs_sensor.c"),
       str(PROJECT / "tests/test_sensor_contract.c"), "-o", str(BUILD / "test_sensor_contract")]
build = subprocess.run(cmd, text=True, capture_output=True, timeout=20, check=True)
test = subprocess.run([str(BUILD / "test_sensor_contract")], text=True, capture_output=True, timeout=20, check=True)
log = shlex.join(cmd) + "\n" + build.stdout + build.stderr + test.stdout + test.stderr
(RESULTS / "sensor-contract-test.log").write_text(log)
(RESULTS / "sensor-contract-test.json").write_text(json.dumps({"passed": "PASS:" in test.stdout,
    "hardware_access": False, "kernel_build_or_changes": False,
    "calibrations": "synthetic strict SDL references; experimental accel arithmetic; no device calibration proof",
    "sanitizers": ["address", "undefined"],
    "coverage": ["physical-unit examples", "fractional sensitivity", "signed axis permutation", "bias subtraction",
                 "rounding", "verification gates", "invalid metadata", "overflow", "no partial output",
                 "replaceable rational experimental accel scale", "signed full-range accel", "no gyro fallback"]}, indent=2) + "\n")
print(test.stdout.strip())
