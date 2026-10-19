#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise SDL hotplug with regular files in a device-free private /dev.

No Steam execution, system configuration, uinput, actual evdev/IIO/USB or sudo.
The preload fixture belongs only to the isolated test child.
"""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import ctypes
import stat

from project_paths import PROJECT, BUILD, RESULTS

sys.path.insert(0, str(PROJECT / "tools/sdl"))
from input_pair_readiness import Action, Binding, PublicationGate, Sensor


def run(command):
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f"{command}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdl3-library", type=Path)
    args = parser.parse_args()
    library = args.sdl3_library.resolve(strict=True) if args.sdl3_library else None
    bits = ctypes.sizeof(ctypes.c_void_p) * 8
    digest = None
    if library:
        assert stat.S_ISREG(library.stat().st_mode)
        data = library.read_bytes()
        assert data[:4] == b"\x7fELF" and data[4] in (1, 2)
        bits = 32 if data[4] == 1 else 64
        digest = hashlib.sha256(data).hexdigest()
    build = BUILD / "sdl-hotplug" / (digest[:16] if digest else "system")
    report = RESULTS / "sdl-hotplug" / build.name
    build.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    fixture = build / "fixture"
    (fixture / "evdev").mkdir(parents=True, exist_ok=True)
    (fixture / "sys").mkdir(exist_ok=True)
    for name in ("evdev/event0", "evdev/event1", "iio-device", "sandbox-marker"):
        (fixture / name).write_bytes(b"")
    shutil.copyfile(PROJECT / "tests/audit_sdl_sandbox.py", build / "audit_sdl_sandbox.py")
    flags = ["clang", *(["-m32"] if bits == 32 else []), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2"]
    run([*flags, "-shared", "-fPIC", str(PROJECT / "tests/sdl_hotplug_fixture.c"), "-ldl", "-o", str(build / "fixture.so")])
    run([*flags, str(PROJECT / "tests/sdl_hotplug_probe.c"),
         str(library) if library else "-lSDL3", "-o", str(build / "probe")])
    host_ns = {name: os.readlink("/proc/self/ns/" + name)
               for name in ("mnt", "user", "pid", "net", "ipc", "uts")}
    binding = Binding("fake-hub-life", "fake-native-life", "/fixture/interface0", "gsn-fixture-life")
    gate = PublicationGate(binding, 0)
    sensor = Sensor(binding, "fake-sensor-life", "fake-sensor-life", True,
                    (100, 100, 100), (8192, 8192, 8192))
    assert gate.observe(binding, None, 0.1).action == Action.WAIT
    assert gate.observe(binding, replace(sensor, readable=False), 0.2).action == Action.WAIT
    permitted = gate.observe(binding, sensor, 0.3)
    assert permitted.action == Action.PUBLISH
    gate.acknowledge(binding, permitted.sensor_node_token)
    cases = []
    for scenario in ("present-at-init", "sensor-first-hotplug", "sensor-after-open", "readability-race", "readiness-gated"):
        command = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL",
                   "--clearenv", "--setenv", "PATH", "/usr/bin", "--setenv", "HOME", "/tmp",
                   "--setenv", "GS_HOST_NS", json.dumps(host_ns),
                   "--setenv", "GS_SCENARIO", "experimental-six-axis",
                   "--setenv", "GS_HOTPLUG_SCENARIO", scenario,
                   "--setenv", "GS_GATE_PERMISSION", str(int(gate.published)),
                   "--setenv", "GS_ACCEL_RES", "8192", "--setenv", "GS_GYRO_RES", "100",
                   "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib", "/lib64",
                   "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/run", "--tmpfs", "/tmp",
                   "--ro-bind", str(fixture / "sys"), "/sys", "--ro-bind", str(fixture), "/fixture",
                   "--ro-bind", str(fixture / "iio-device"), "/dev/iio:device0",
                   "--ro-bind", str(build), "/tests", "--chdir", "/tmp"]
        if library:
            command += ["--ro-bind", str(library), "/sdl-override/libSDL3.so.0",
                        "--setenv", "LD_LIBRARY_PATH", "/sdl-override",
                        "--setenv", "GS_EXPECT_SDL3_LIBRARY", "/sdl-override/libSDL3.so.0"]
        command += ["/usr/bin/python", "/tests/audit_sdl_sandbox.py", "/tests/probe"]
        output = run(command)
        (report / (scenario + ".log")).write_text(output)
        assert "result=PASS" in output and '"all_six_separate": true' in output and "iio opens=0;" in output
        cases.append({"scenario": scenario, "passed": True})
    if library:
        assert hashlib.sha256(library.read_bytes()).hexdigest() == digest
    result = {"schema": 1, "hardware_access": False, "steam_execution": False,
              "system_changes": False, "sdl_sha256": digest, "elf_bits": bits, "cases": cases,
              "all_passed": True, "policy_prototype": True, "production_integration": False,
              "limits": "Synthetic inotify backend and access-denial injection; no real udev, ACL, Steam or Gamescope execution."}
    (report / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": len(cases), "report": str(report)}))


if __name__ == "__main__":
    main()
