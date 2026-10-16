#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run installed kernel checkpatch and Clang analyzer, without loading code."""
import json
from pathlib import Path
import platform
import plistlib
import shlex
import subprocess
import sys
from kernel_toolchain import kernel_family

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/kernel"
REPORT = ROOT / "build/results"


def main():
    headers = Path("/lib/modules") / platform.release() / "build"
    if kernel_family(headers) != 'clang':
        raise SystemExit('Clang analyzer requires a Clang kernel build; '
                         'GCC kernel flags are not translated or discarded')
    REPORT.mkdir(parents=True, exist_ok=True)
    files = ["kernel/gs_native_usb.c", "src/gs_runtime.c", "src/gs_runtime.h",
             "src/gs_startup.c", "src/gs_startup.h", "include/uapi/gs_native.h"]
    args = [str(headers / "scripts/checkpatch.pl"), "--no-tree", "--strict",
            "--ignore", "CAMELCASE", "--file", *(str(ROOT / name) for name in files)]
    checked = subprocess.run(args, cwd=BUILD, capture_output=True, text=True, timeout=30)
    (REPORT / "kernel-checkpatch.log").write_text(checked.stdout + checked.stderr)
    results = []
    for name in ["gs_native_usb", "gs_protocol", "gs_sensor", "gs_runtime", "gs_startup"]:
        cmdfile = BUILD / f".{name}.o.cmd"
        line = next(line for line in cmdfile.read_text().splitlines() if line.startswith("savedcmd_"))
        tokens = shlex.split(line.split(" := ", 1)[1])
        assert Path(tokens[0]).name == "clang" and ";" not in tokens
        command = []
        skip = False
        for token in tokens:
            if skip:
                skip = False
                continue
            if token == "-o":
                skip = True
                continue
            if token == "-c" or token.startswith("-Wp,-MMD"):
                continue
            command.append(token)
        output = BUILD / f"{name}-analysis.plist"
        command += ["--analyze", "-Xanalyzer", "-analyzer-output=plist",
                    "-Wno-unused-command-line-argument", "-o", str(output)]
        result = subprocess.run(command, cwd=BUILD, capture_output=True, text=True, timeout=60)
        (REPORT / f"{name}-analyzer.log").write_text(result.stdout + result.stderr)
        diagnostics = plistlib.loads(output.read_bytes()).get("diagnostics", []) if output.is_file() else None
        results.append({"translation_unit": name, "returncode": result.returncode,
                        "diagnostics": None if diagnostics is None else len(diagnostics),
                        "stderr_warning": "warning:" in result.stderr.lower(),
                        "passed": result.returncode == 0 and diagnostics == [] and "warning:" not in result.stderr.lower()})
    report = {"passed": checked.returncode == 0 and all(r["passed"] for r in results),
              "checkpatch_returncode": checked.returncode, "checkpatch_ignored": ["CAMELCASE: kernel USB descriptor members"],
              "clang_static_analyzer": results, "sparse": "not installed; not executed",
              "hardware_access": False, "loaded_module": False,
              "limits": "Static analysis does not model all kernel allocation/refcount/URB/workqueue concurrency semantics"}
    (REPORT / "kernel-static-analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
