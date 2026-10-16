#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Sanitized tests of the existing offline protocol/motor state contracts."""
import json
import shlex
import subprocess

from project_paths import PROJECT, BUILD, RESULTS


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    command = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g",
               str(PROJECT / "src/gs_protocol.c"), str(PROJECT / "tests/test_protocol_state.c"),
               "-o", str(BUILD / "test_protocol_state")]
    compile_result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=True)
    result = subprocess.run([str(BUILD / "test_protocol_state")], capture_output=True,
                            text=True, timeout=20, check=True)
    (RESULTS / "protocol-state-test.log").write_text(shlex.join(command) + "\n" +
        compile_result.stdout + compile_result.stderr + result.stdout + result.stderr)
    report = {"passed": "PASS:" in result.stdout, "hardware_access": False,
              "kernel_build_or_changes": False, "sanitizers": ["address", "undefined"],
              "coverage": ["independent motor stop", "all 15 channel masks", "exact expiry boundaries",
                           "FF preserves trigger pulses", "atomic invalid requests", "deadline overflow",
                           "FF endpoints and quarter values", "zero motor packet", "incomplete frame rejection"],
              "limits": "No live transport, competing writers, mechanical motor test or hardware lifecycle validation"}
    (RESULTS / "protocol-state-test.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
