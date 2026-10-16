#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build and inspect an external module; never load/install it or touch USB."""
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from kernel_toolchain import build_plan

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/kernel"
REPORT = ROOT / "build/results"
COMPILER_MISMATCH = "warning: the compiler differs from the one used to build the kernel"


def classify_warnings(output, compiler_family):
    """Keep the exact Kbuild compiler advisory separate from code diagnostics.

    This records an environment difference, not compiler/ABI compatibility.
    Incomplete messages, a different compiler family, and every other warning
    still fail validation. No diagnostic is discarded from the saved log.
    """
    lines = output.splitlines()
    environment, unclassified = [], []
    family_pattern = (r"\bclang\b" if compiler_family == "clang" else
                      r"\b(?:gcc|GCC)\b" if compiler_family == "gcc" else None)
    for index, line in enumerate(lines):
        if "warning:" not in line.lower():
            continue
        built_by = using = None
        if line == COMPILER_MISMATCH and index + 2 < len(lines):
            built_by = re.fullmatch(r"  The kernel was built by: (.+)", lines[index + 1])
            using = re.fullmatch(r"  You are using:           (.+)", lines[index + 2])
        if built_by and using and family_pattern:
            kernel_compiler, module_compiler = built_by[1], using[1]
            versions = (kernel_compiler, module_compiler)
            if (kernel_compiler != module_compiler and
                    all(re.search(family_pattern, value) and
                        "warning:" not in value.lower() for value in versions)):
                environment.append({"kind": "kernel_compiler_mismatch", "message": line,
                                    "kernel_compiler": kernel_compiler,
                                    "module_compiler": module_compiler})
                continue
        unclassified.append(line)
    return {"warnings": len(environment) + len(unclassified),
            "code_warnings": len(unclassified),
            "environment_warnings": environment,
            "unclassified_warnings": unclassified}


def main():
    release = platform.release()
    headers = Path("/lib/modules") / release / "build"
    if not headers.is_dir() or not (headers / "Module.symvers").is_file():
        raise SystemExit("Matching prepared kernel headers missing; no installation attempted")
    uts = (headers / "include/generated/utsrelease.h").read_text()
    if f'"{release}"' not in uts:
        raise SystemExit("Kernel/header release mismatch")
    BUILD.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    plan = build_plan(headers, ROOT / 'kernel', output=BUILD)
    result = subprocess.run(plan['argv'], env=plan['env'], text=True,
                            capture_output=True, timeout=120)
    output = result.stdout + result.stderr
    (REPORT / "kernel-build.log").write_text(output)
    warnings = classify_warnings(output, plan['family'])
    if result.returncode:
        report = {"built": False, "build_status": "failed", "returncode": result.returncode,
                  "kernel_release": release, **warnings,
                  "loaded_or_installed": False, "hardware_access": False}
        (REPORT / "kernel-build.json").write_text(json.dumps(report, indent=2) + "\n")
        print(output)
        return result.returncode
    module = BUILD / "gs_native.ko"
    meta = subprocess.check_output(["modinfo", str(module)], text=True)
    (REPORT / "kernel-modinfo.txt").write_text(meta)
    vermagic = subprocess.check_output(["modinfo", "-F", "vermagic", str(module)], text=True).strip()
    aliases = subprocess.check_output(["modinfo", "-F", "alias", str(module)], text=True).strip()
    errors = []
    if not vermagic.startswith(release + " "):
        errors.append("Module vermagic does not match the running kernel")
    if aliases:
        errors.append("Module declares unexpected automatic USB aliases")
    if warnings['code_warnings']:
        errors.append("Build contains unclassified warnings")
    status = ("failed" if errors else "passed_with_environment_warning"
              if warnings['environment_warnings'] else "passed")
    report = {"built": True, "kernel_release": release,
              "module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
              "vermagic": vermagic, "autoload_aliases": aliases.splitlines(),
              "build_status": status, "validation_errors": errors,
              "returncode": 1 if errors else 0, **warnings,
              "compiler": subprocess.check_output([plan['compiler'], "--version"],
                                                  env=plan['env'], text=True).splitlines()[0],
              "compiler_family": plan['family'],
              "removed_build_environment": plan['removed_environment'],
              "header_compiler": (headers / "include/generated/compile.h").read_text().split('LINUX_COMPILER')[1].strip(),
              "dependencies": subprocess.check_output(["modinfo", "-F", "depends", str(module)], text=True).strip(),
              "loaded_or_installed": False, "hardware_access": False,
              "module": "build/kernel/gs_native.ko", "flags": plan['flags']}
    (REPORT / "kernel-build.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
