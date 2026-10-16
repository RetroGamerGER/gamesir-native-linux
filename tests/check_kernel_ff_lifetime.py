#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Verify actual input/FF teardown functions with ASan; never access hardware."""
import hashlib
import json
import os
import re
import subprocess

from project_paths import BUILD, PROJECT, RESULTS

source = (PROJECT / "kernel/gs_native_usb.c").read_text()
names = ["gsn_delete", "gsn_open", "gsn_release", "gsn_play_effect",
         "gsn_input_register", "gsn_quiesce", "gsn_disconnect"]


def extract(text):
    start = text.index("struct gsn_device {")
    structure = text[start:text.index("\n};", start) + 3]
    blocks = []
    for name in names:
        match = re.search(r"^static [^;{}]*\b" + name + r"\([^;{}]*\)\n\{", text, re.M)
        assert match, name
        blocks.append(text[match.start():text.index("\n}", match.end()) + 2])
    prototypes = [b[:b.index("\n{")] + ";" for b in blocks]
    return "\n\n".join([structure, *prototypes, *blocks]) + "\n"


def build(label, text):
    directory = BUILD / "ff-lifetime" / label
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "kernel-ff-lifetime-functions.h").write_text(extract(text))
    exe = directory / "test-kernel-ff-lifetime"
    command = ["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror",
               "-Wno-unused-parameter", "-fsanitize=address,undefined",
               "-fno-sanitize-recover=all", "-g", "-I", str(directory),
               str(PROJECT / "tests/kernel_ff_lifetime_fake.c"),
               str(PROJECT / "src/gs_runtime.c"), str(PROJECT / "src/gs_protocol.c"),
               "-o", str(exe)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=40)
    (RESULTS / f"kernel-ff-lifetime-{label}-build.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.stderr)
    return exe


RESULTS.mkdir(parents=True, exist_ok=True)
cases = ["immediate", "control", "deferred", "deferred-control",
         "deferred-control-input-first", "playback", "deferred-playback", "100a",
         "input-allocation-failure", "ff-create-failure", "input-register-failure"]
fixed = build("fixed", source)
env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1", UBSAN_OPTIONS="halt_on_error=1")
for pid in ("109c", "105e"):
    for case in cases:
        args = [str(fixed), case] + (["105e"] if pid == "105e" else [])
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=10)
        (RESULTS / f"kernel-ff-lifetime-fixed-{pid}-{case}.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)

# Negative control restores only the two defective ownership lines in an
# isolated generated header, never in the repository or installed driver.
original_call = "input_ff_create_memless(g->input, NULL, gsn_play_effect)"
original_callback = "struct gsn_device *g = input_get_drvdata(input);"
assert source.count(original_call) == source.count(original_callback) == 1
broken = source.replace(original_call, "input_ff_create_memless(g->input, g, gsn_play_effect)")
broken = broken.replace(original_callback, "struct gsn_device *g = data;")
negative = build("ownership-bug", broken)
negative_results = {}
for case in ("immediate", "control", "deferred", "input-register-failure"):
    result = subprocess.run([str(negative), case], env=env, capture_output=True, text=True, timeout=10)
    output = result.stdout + result.stderr
    (RESULTS / f"kernel-ff-lifetime-ownership-bug-{case}.log").write_text(output)
    expected = "double-free" if case == "deferred" else "heap-use-after-free"
    if not result.returncode or "AddressSanitizer" not in output or expected not in output:
        raise SystemExit(f"Negative control did not expose {expected} for {case}:\n{output}")
    negative_results[case] = expected

report = {
    "passed": True, "hardware_access": False, "cases": cases, "native_pids": ["109c", "105e"],
    "negative_control": negative_results, "functions": names,
    "sanitizers": ["address", "undefined", "leak"],
    "method": "Actual extracted adapter functions; synthetic Linux input references and memless private-data destructor",
    "source_sha256": {p: hashlib.sha256((PROJECT / p).read_bytes()).hexdigest() for p in
                      ("kernel/gs_native_usb.c", "tests/kernel_ff_lifetime_fake.c", "tests/check_kernel_ff_lifetime.py")},
    "limits": ["No real kernel, USB, input handlers, locks, timers or workqueue execution.",
               "Model checks the confirmed ownership contract, not general race freedom or freeze causality."]}
(RESULTS / "kernel-ff-lifetime.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"PASS: {len(cases) * 2} actual-adapter FF lifetime cases; 4 ownership-bug controls rejected by ASan")
