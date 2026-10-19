#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build local test binaries and run installed SDL in a device-free sandbox.

No uinput, real input/IIO/USB nodes, libusb, root, module or system changes.
The LD_PRELOAD fixture is private to each test child. Never run probes directly.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shlex
import struct
import subprocess
import sys
import shutil
import ctypes as c
import stat

from project_paths import PROJECT, BUILD as BUILD_ROOT, RESULTS

BUILD = BUILD_ROOT / "sdl-sensor-test"
REPORT = RESULTS / "sdl-validation"


def run(args):
    r = subprocess.run(args, text=True, capture_output=True, close_fds=True, timeout=25)
    if r.returncode:
        raise RuntimeError(f"{shlex.join(map(str, args))}\n{r.stdout}\n{r.stderr}")
    return r.stdout + r.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdl3-library", type=Path,
                        help="Test one local SDL3 shared library, mounted read-only; no Steam/client launch")
    options = parser.parse_args()
    library = options.sdl3_library
    library_hash = None
    target_bits = c.sizeof(c.c_void_p) * 8
    report = REPORT / "sequence-v2"
    if library is not None:
        library = library.expanduser().resolve(strict=True)
        if not stat.S_ISREG(library.stat().st_mode):
            parser.error("The SDL library must be a stored regular file")
        data = library.read_bytes()
        if len(data) < 16 or data[:4] != b"\x7fELF" or data[4] not in (1, 2):
            parser.error("The local SDL library must be an ELF32/ELF64 shared object")
        target_bits = 32 if data[4] == 1 else 64
        if target_bits not in (32, c.sizeof(c.c_void_p) * 8):
            parser.error("Unsupported SDL ABI for this host")
        library_hash = hashlib.sha256(data).hexdigest()
        report = report / ("sdl3-" + library_hash[:16])
    build = BUILD / f"elf{target_bits}"
    abi_flags = ["-m32"] if target_bits == 32 else []
    build.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    fixture = build / "fixture"
    (fixture / "evdev").mkdir(parents=True, exist_ok=True)
    for f in ["evdev/event0", "evdev/event1", "iio-device", "sandbox-marker"]:
        (fixture / f).write_bytes(b"")
    iio = fixture / "sys/bus/iio/devices/iio:device0"
    iio.mkdir(parents=True, exist_ok=True)
    (iio / "name").write_text("gamesir_g7pro_offline_fixture\n")
    # Reviewed target-only excerpt; the full private capture is not required.
    excerpt = json.loads((PROJECT / "fixtures/sprint002-target.json").read_text())
    case = next(r for r in excerpt["cases"] if r["name"] == "imu_nonzero")
    record = case["record"]
    index = case["source_record_line"]
    data = bytes.fromhex(record["data_hex"])
    assert record["status"] == 0 and len(data) == 64 and data[3:5] == b"\x3c\xe0"
    axes = struct.unpack_from("<6h", data, 17)
    assert all(axes)
    # Fixture order: acceleration X/Y/Z, gyro RX/RY/RZ.
    raw = (*axes[3:], *axes[:3])
    for sensor, values in [("accel", axes[3:]), ("anglvel", axes[:3])]:
        for axis, value in zip("xyz", values):
            (iio / f"in_{sensor}_{axis}_raw").write_text(str(value) + "\n")
    compile_log = []
    builds = [
        ("sensor-contract", ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
            str(PROJECT / "src/gs_sensor.c"), "-o", str(build / "sensor.so")]),
        ("fixture", ["clang", *abi_flags, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
            str(PROJECT / "tests/sdl_buttons_fixture.c"), "-ldl", "-o", str(build / "fixture.so")]),
        ("sdl3", ["clang", *abi_flags, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
            str(PROJECT / "tests/sdl_sensor_probe.c"), str(library) if library else "-lSDL3", "-ldl", "-lm", "-o", str(build / "probe3")]),
        ("sdl2", ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", "-DTEST_SDL2",
            str(PROJECT / "tests/sdl_sensor_probe.c"), "-lSDL2", "-ldl", "-lm", "-o", str(build / "probe2")]),
    ]
    for name, args in builds:
        if name == "sdl2" and library is not None:
            continue
        compile_log.append(name + ": " + shlex.join(args) + "\n" + run(args))
    (report / "build.log").write_text("\n".join(compile_log))
    shutil.copyfile(PROJECT / "tests/audit_sdl_sandbox.py", build / "audit_sdl_sandbox.py")
    host_ns = {n: os.readlink("/proc/self/ns/" + n) for n in ["mnt", "user", "pid", "net", "ipc", "uts"]}
    class Axis(c.Structure):
        _fields_ = [("numerator", c.c_uint32), ("denominator", c.c_uint32), ("bias_raw", c.c_int32), ("source", c.c_uint8), ("sign", c.c_int8)]
    class Calibration(c.Structure):
        _fields_ = [("verified", c.c_uint32), ("resolution", c.c_uint32), ("axis", Axis * 3)]
    lib = c.CDLL(str(build / "sensor.so"))
    lib.gs_sensor_convert.argtypes = [c.POINTER(Calibration), c.c_void_p, c.c_void_p]
    lib.gs_gyro_convert_observed.argtypes = [c.c_uint16, c.c_int, c.c_void_p, c.c_void_p]
    gyro = (c.c_int32 * 3)()
    assert lib.gs_gyro_convert_observed(0x109c, 1, (c.c_int16 * 3)(*axes[:3]), gyro) == 1
    assert list(gyro) == [value * 7 for value in axes[:3]]
    observed = [0, 0, 0, *gyro]
    converted = []
    # Artificial 1 g and 90 degree/s references; NOT a real device calibration.
    for sample, resolution, numerator, denominator in [
            ([8192, 0, -8192], 10000, 625, 512), ([1476, -1476, 0], 100, 250, 41)]:
        cal = Calibration(7, resolution, (Axis * 3)(*(Axis(numerator, denominator, 0, i, 1) for i in range(3))))
        out = (c.c_int32 * 3)()
        assert lib.gs_sensor_convert(c.byref(cal), (c.c_int16 * 3)(*sample), out) == 0
        converted.extend(out)
    assert converted == [10000, 0, -10000, 9000, -9000, 0]
    results = []
    for version in ([3] if library is not None else [3, 2]):
        for scenario in ["iio-only", "matching-uniq", "wrong-uniq", "missing-rz", "zero-resolution", "synthetic-converted", "observed-gyro"]:
            sample_raw = converted if scenario == "synthetic-converted" else raw
            accel_resolution, gyro_resolution = (10000, 100) if scenario == "synthetic-converted" else (8192, 16)
            if scenario == "observed-gyro":
                sample_raw = observed
                accel_resolution, gyro_resolution = 0, 100
            if scenario == "zero-resolution":
                accel_resolution = gyro_resolution = 0
            args = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL",
                "--clearenv", "--setenv", "PATH", "/usr/bin", "--setenv", "HOME", "/tmp",
                "--setenv", "GS_HOST_NS", json.dumps(host_ns),
                "--setenv", "GS_SCENARIO", scenario, "--setenv", "GS_RAW", ",".join(map(str, sample_raw)),
                "--setenv", "GS_ACCEL_RES", str(accel_resolution), "--setenv", "GS_GYRO_RES", str(gyro_resolution),
                "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib", "/lib64",
                "--proc", "/proc", "--dev", "/dev", "--ro-bind", str(fixture / "sys"), "/sys",
                "--tmpfs", "/run", "--tmpfs", "/tmp", "--ro-bind", str(fixture), "/fixture",
                "--ro-bind", str(fixture / "iio-device"), "/dev/iio:device0",
                "--ro-bind", str(build), "/tests", "--chdir", "/tmp"]
            if library is not None:
                args.extend(["--ro-bind", str(library), "/sdl-override/libSDL3.so.0",
                    "--setenv", "LD_LIBRARY_PATH", "/sdl-override",
                    "--setenv", "GS_EXPECT_SDL3_LIBRARY", "/sdl-override/libSDL3.so.0"])
            args.extend(["/usr/bin/python", "/tests/audit_sdl_sandbox.py", f"/tests/probe{version}"])
            output = run(args)
            filename = f"sdl{version}-{scenario}.log"
            (report / filename).write_text(output)
            results.append({"api": f"SDL{version}", "scenario": scenario,
                "passed": "result=PASS" in output and "iio opens=0;" in output and '"all_six_separate": true' in output,
                "sample_raw": sample_raw, "synthetic_accel_resolution": accel_resolution, "synthetic_gyro_resolution": gyro_resolution,
                "log": filename, "command": args})
    if library is not None and hashlib.sha256(library.read_bytes()).hexdigest() != library_hash:
        raise RuntimeError("SDL library changed during the offline test; results not accepted")
    result = {"schema_version": 1, "method": "local SDL + synthetic evdev syscall fixture inside device-free Bubblewrap",
        "sdl3_override": None if library is None else {"path": str(library), "sha256": library_hash,
            "loaded_path_verified_by_probe": True},
        "target_bits": target_bits,
        "hardware_test": False, "privileged_actions": False, "kernel_changes": False,
        "fixture_scales": {"synthetic_not_G7_calibration": True, "accel_units_per_g": 8192, "gyro_units_per_degree_per_second": 16},
        "capture": "target-only excerpt: fixtures/sprint002-target.json", "record_line": index, "record": record,
        "raw_packet_sha256": hashlib.sha256(data).hexdigest(), "fixture_axis_values": raw,
        "synthetic_conversion": {"source": "src/gs_sensor.c", "not_a_real_G7_calibration": True,
            "wire_accel": [8192, 0, -8192], "wire_gyro": [1476, -1476, 0], "converted_values": converted,
            "gyro_wire_counts_per_degree_per_second": 16.4},
        "installed_packages": run(["pacman", "-Q", "sdl3", "sdl2-compat"]).strip(),
        "results": results, "all_passed": all(r["passed"] for r in results)}
    (report / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"all_passed": result["all_passed"], "cases": len(results), "reports": str(report)}))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
