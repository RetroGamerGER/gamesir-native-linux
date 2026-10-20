#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real C client against synthetic syscalls; verify Python/C output contract."""
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hw002", ROOT / "tools/native/hardware_test_002.py")
hw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hw)
build = ROOT / "build/test-native-client"
build.mkdir(parents=True, exist_ok=True)
binary = build / "fake-client"
subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
                str(ROOT / "tests/native_client_fake.c"), "-o", str(binary)], check=True)
prefix = ["start_call", "started", "help"]
normal = prefix + ["info", "sample", "pulse", "stop"]
cases = (
    ("normal", 0, normal + ["ended"], ""),
    ("deadline", 0, prefix + ["ended"], ""),
    ("limit-300", 0, ["info"] + prefix + ["ended"], ""),
    ("limit-301", 2, [], ""),
    ("default-session", 0, ["info"] + prefix + ["ended"], ""),
    ("pulse-1000", 0, prefix + ["pulse", "stop", "ended"], ""),
    ("pulse-1001", 1, prefix + ["ended"], "Invalid command; ending session"),
    ("start-fail", 1, ["start_call"], "START_SESSION"),
    ("pulse-fail", 1, prefix + ["info", "sample", "ended"], "Command failed; ending session"),
    ("stop-fail", 1, prefix + ["info", "sample", "pulse", "ended"], "Command failed; ending session"),
    ("end-fail", 1, normal, "FINAL STOP failed"),
)
for case, status, expected_kinds, expected_error in cases:
    result = subprocess.run([str(binary), case], capture_output=True, text=True, timeout=5)
    assert result.returncode == status, (case, result.returncode, result.stderr)
    messages = [hw.parse_line(line) for line in result.stdout.splitlines()]
    kinds = [m["type"] for m in messages]
    assert kinds == expected_kinds, (case, kinds)
    if "sample" in kinds:
        assert next(m for m in messages if m["type"] == "sample")["gyro_raw"] == [-32768, 0, 32767]
    if expected_error:
        assert expected_error in result.stderr, (case, result.stderr)
    else:
        assert not result.stderr, (case, result.stderr)
bootstrap_cases = (("bootstrap-normal", 0), ("bootstrap-handover", 0),
                   ("bootstrap-invalid", 2), ("bootstrap-fail", 1), ("bootstrap-wait", 0))
for case, status in bootstrap_cases:
    result = subprocess.run([str(binary), case], capture_output=True, text=True, timeout=5)
    assert result.returncode == status, (case, result.stderr)
    if case == "bootstrap-invalid":
        assert not result.stdout and not result.stderr
    elif case == 'bootstrap-wait':
        assert 'bootstrap state=9 error=0' in result.stdout and not result.stderr
        assert 'Native receiver waiting.' in result.stdout
        assert 'Native startup completed.' not in result.stdout
    elif status == 0:
        assert "bootstrap state=7 error=0" in result.stdout and not result.stderr
        assert "Native startup completed" in result.stdout
    else:
        assert "bootstrap state=8 error=-5" in result.stdout
        assert "BOOTSTRAP failed" in result.stderr
for case, status in (('end-wait', 0), ('info-wait', 1)):
    result = subprocess.run([str(binary), case], capture_output=True, text=True, timeout=5)
    assert result.returncode == status, (case, result.stderr)
    assert 'bootstrap state=9 error=0' in result.stdout
    if case == 'info-wait':
        assert 'INFO ownership proof mismatch' in result.stderr
    else:
        assert not result.stderr
print(json.dumps({"passed": True, "hardware_access": False, "synthetic_syscalls": True,
                  "real_client_source": True, "asan_ubsan": True,
                  "cases": [case[0] for case in cases],
                  "bootstrap_cases": [case[0] for case in bootstrap_cases],
                  "receiver_wait_gate_cases": ["end-wait", "info-wait"],
                  "session_limits_seconds": {"client": 300, "kernel": 315, "default_client": 20},
                  "pulse_limits_ms": {"accepted": [400, 1000], "rejected": 1001},
                  "deadline_uses_virtual_time": True, "301_seconds_rejected_before_open": True}))
