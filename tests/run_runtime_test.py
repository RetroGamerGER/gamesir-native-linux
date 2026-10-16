#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Test the actual shared runtime policy without a USB bus or loaded module."""
import json
import subprocess
from project_paths import PROJECT, BUILD, RESULTS


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    args = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(PROJECT / "src/gs_protocol.c"), str(PROJECT / "src/gs_runtime.c"),
            str(PROJECT / "tests/test_runtime.c"), "-o", str(BUILD / "test_runtime")]
    compile_result = subprocess.run(args, capture_output=True, text=True, timeout=30, check=True)
    result = subprocess.run([str(BUILD / "test_runtime")], capture_output=True, text=True, timeout=20, check=True)
    report = {"passed": True, "hardware_access": False, "sanitizers": ["address", "undefined"],
              "actual_runtime_source_tested": "src/gs_runtime.c", "uapi_sizes": {"info": 56, "sample": 48, "pulse": 32},
              "coverage": result.stdout.strip(),
              "limits": ["no kernel URB/workqueue execution", "no physical disconnect", "no kernel race/fault injection"]}
    (RESULTS / "runtime-test.log").write_text(compile_result.stdout + compile_result.stderr + result.stdout + result.stderr)
    (RESULTS / "runtime-test.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
