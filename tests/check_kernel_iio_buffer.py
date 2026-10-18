#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise extracted IIO adapter code with synthetic kernel objects only."""
import copy
import errno
import hashlib
import json
import math
import os
import re
import subprocess
import sys

from project_paths import BUILD, PROJECT, RESULTS

sys.path.insert(0, str(PROJECT / "tools/imu"))
from gamesir_imu_stream import ScanDecoder
import gyro_reference
import gamesir_iio_buffer
from test_iio_buffer_setup import FakeBackend


NAMES = ["gsn_delete", "gsn_imu", "gsn_sample_snapshot", "gsn_iio_raw",
         "buffer_push_errors_show", "buffer_stream_active_show", "gsn_iio_preenable",
         "gsn_iio_postenable", "gsn_iio_predisable", "gsn_quiesce",
         "gsn_disconnect", "gsn_suspend", "gsn_resume"]


def extract(source):
    start = source.index("struct gsn_device {")
    structure = source[start:source.index("\n};", start) + 3]
    blocks = []
    for name in NAMES:
        match = re.search(r"^static [^;{}]*\b" + name + r"\([^;{}]*\)\n\{", source, re.M)
        assert match, name
        blocks.append(source[match.start():source.index("\n}", match.end()) + 2])
    start = source.index("#define GSN_CHANNEL(")
    end = source.index("\nstatic int gsn_iio_preenable", start)
    channels = source[start:end]
    declarations = [block[:block.index("\n{")] + ";" for block in blocks]
    ops_start = source.index("static const struct iio_buffer_setup_ops gsn_iio_buffer_ops = {")
    ops = source[ops_start:source.index("\n};", ops_start) + 3]
    return "\n\n".join([structure, channels, *declarations, *blocks, ops]) + "\n"


def build(label, source):
    directory = BUILD / "iio-buffer" / label
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "kernel-iio-buffer-functions.h").write_text(extract(source))
    executable = directory / "test-kernel-iio-buffer"
    command = ["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror",
               "-Wno-unused-parameter", "-fsanitize=address,undefined",
               "-fno-sanitize-recover=all", "-g", "-I", str(directory),
               str(PROJECT / "tests/kernel_iio_buffer_fake.c"),
               *[str(PROJECT / "src" / (name + ".c")) for name in
                 ("gs_protocol", "gs_runtime", "gs_sensor")], "-o", str(executable)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=40)
    (RESULTS / f"kernel-iio-buffer-{label}-build.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.stderr)
    return executable


def transaction_cases(executable, env, *, legacy=False):
    """Real Python setup/rollback -> actual C driver callback registration.

    Only the narrow IIO mask-selection boundary is modelled, as reviewed in
    the installed core binary. No devices, sysfs writes or kernel execution.
    """
    class CoreBackend(FakeBackend):
        def write_at(self, directory_fd, relative, value):
            if relative.startswith("scan_elements/"):
                names = [f"scan_elements/{name}_en" for name in gamesir_iio_buffer.CHANNELS]
                mask = sum(1 << n for n, name in enumerate(names)
                           if self.value["settings"][name] == "1")
                active = self.value["buffer_enable"] == "1"
                result = subprocess.run([str(executable), "--select-scan", str(mask),
                    str(names.index(relative)), value, str(int(active))], env=env,
                    capture_output=True, text=True, timeout=10, check=True)
                selected = json.loads(result.stdout)
                if selected["result"]:
                    assert selected["requested"] == mask
                    raise OSError(-selected["result"], "modelled IIO channel selection")
                expected = (mask | (1 << names.index(relative))) if value == "1" else (
                    mask & ~(1 << names.index(relative)))
                assert selected["requested"] == expected
            super().write_at(directory_fd, relative, value)

    completed = 0
    for fail_at in ([None] if legacy else [None, *range(1, 11)]):
        backend = CoreBackend()
        before = copy.deepcopy(backend.value)
        if fail_at:
            backend.fail_write = {fail_at}
        transaction = gamesir_iio_buffer.BufferTransaction(before, backend=backend)
        try:
            _, fd = transaction.setup()
        except OSError as error:
            if legacy:
                assert error.errno == errno.EINVAL
                assert transaction.writes[:2] == [
                    {"attribute": "buffer/length", "value": "512", "ok": True},
                    {"attribute": "scan_elements/in_accel_x_en", "value": "1", "ok": False}]
            else:
                assert fail_at and "injected write failure" in str(error)
        else:
            assert not legacy and fail_at is None
            assert fd == 102 and backend.value["buffer_stream_active"] == "1"
            assert all(v == "1" for k, v in backend.value["settings"].items() if k.endswith("_en"))
        restored = transaction.restore()
        assert restored["restored"] and not restored["errors"]
        assert backend.value == before and backend.closed == [102, 101]
        completed += 1
    return completed


def main():
    source = (PROJECT / "kernel/gs_native_usb.c").read_text()
    RESULTS.mkdir(parents=True, exist_ok=True)
    executable = build("actual", source)
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:halt_on_error=1",
               UBSAN_OPTIONS="halt_on_error=1")
    result = subprocess.run([str(executable)], env=env, capture_output=True, text=True, timeout=20)
    (RESULTS / "kernel-iio-buffer-actual.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    transactions = transaction_cases(executable, env)
    # Cross-language contract: actual gsn_imu serializes all bytes. Decode them
    # using the real userspace consumer and pass those decoded rows unchanged
    # into the known-angle analyzer. No Python struct.pack duplicate is used.
    crossings = []
    for axis in range(3):
        for angle in (-180, -90, 90, 180):
            stream = subprocess.run([str(executable), "--emit-synthetic-angle", str(axis), str(angle)],
                                    env=env, capture_output=True, timeout=20)
            if stream.returncode:
                raise SystemExit(stream.stderr.decode())
            assert len(stream.stdout) == 405 * 32
            path = BUILD / "iio-buffer" / f"synthetic-axis{axis}-angle{angle}.bin"
            path.write_bytes(stream.stdout)
            decoder = ScanDecoder(f"synthetic-actual-c-{axis}-{angle}", 5_041_523, "synthetic")
            rows = []
            # Odd byte chunks exercise reader carry-over across C frame edges.
            for offset in range(0, len(stream.stdout), 73):
                rows.extend(decoder.feed(stream.stdout[offset:offset + 73]))
            decoder.finish()
            assert len(rows) == 405 and rows[0]["sample_number"] == 2
            assert rows[-1]["sample_number"] == 406
            assert all(row["accel_raw"] == [123, -456, 8192] for row in rows)
            assert rows[0]["gyro_raw"] == [7, -11, 23]
            stamps = [row["timestamp_ns"] for row in rows]
            assert stamps[0] == 1_000_000_000
            assert stamps[-1] == stamps[0] + 404 * 5_041_523
            metadata = {
                "schema_version": 1, "kind": "experimental_known_angle",
                "axis_mapping": {name: {"raw_axis": i, "sign": 1} for i, name in enumerate("XYZ")},
                "windows": [{"label": f"synthetic-c-{axis}-{angle}", "physical_axis": "XYZ"[axis],
                    "known_angle_deg": angle, "reference_kind": "angle_fixture",
                    "angle_reference_description": "own analytic triangular raw signal; synthetic reference only",
                    "reference_completed": True, "motion_bounds_include_stationary_margins": True,
                    "rest_before": [stamps[0], stamps[100]], "motion": [stamps[101], stamps[303]],
                    "rest_after": [stamps[304], stamps[404]]}],
            }
            analysis = gyro_reference.analyze_reference(rows, metadata, 5_041_523)
            window = analysis["windows"][0]
            expected_raw = math.copysign(10100 * 101 * 5_041_523 / 1e9 * abs(angle) / 90, angle)
            assert window["bias_raw_experimental"] == [7, -11, 23]
            for channel, actual in enumerate(window["raw_integral_count_seconds"]):
                assert math.isclose(actual, expected_raw if channel == axis else 0, abs_tol=1e-7)
            profile = next(p for p in window["profiles"] if p["assumed_range_dps"] == 500)
            assert abs(profile["angle_raw_axes_deg"][axis] - angle) < 0.00002
            assert len(window["profiles"]) == 5
            assert all(not p["profile_confirmed"] and not p["selected_for_runtime"] for p in window["profiles"])
            assert not analysis["calibration_verified"] and not analysis["sdl_runtime_enable"]
            crossings.append({"raw_axis": axis, "known_angle_deg": angle, "samples": len(rows),
                              "synthetic_scan_sha256": hashlib.sha256(stream.stdout).hexdigest()})
    # Isolated generated-code mutations check that the fixture detects actual
    # sample mixing, padding disclosure and missing PM interruption. Sources and
    # the installed driver are never changed by these negative controls.
    mutations = {
        "mixed-axis": ("scan.accel[i] = cpu_to_le16(sample.accel_raw[i]);",
                       "scan.accel[i] = cpu_to_le16(sample.gyro_raw[i]);"),
        "padding": ("} scan = {0};", "} scan = { .padding = 1 };"),
        "quiesce-gate": ("g->iio_buffer_active = false;\n\tspin_unlock_irqrestore(&g->report_lock, flags);\n\tif (state != GS_DISCONNECTED)",
                         "/* negative control: leave active gate set */\n\tspin_unlock_irqrestore(&g->report_lock, flags);\n\tif (state != GS_DISCONNECTED)"),
    }
    legacy_callback = """static bool gsn_iio_scan_mask(struct iio_dev *indio, const unsigned long *mask)
{
	return mask[0] == gsn_scan_masks[0];
}

"""
    legacy_source = source.replace("static int gsn_iio_preenable", legacy_callback + "static int gsn_iio_preenable", 1)
    legacy_source = legacy_source.replace(".predisable = gsn_iio_predisable,",
        ".predisable = gsn_iio_predisable,\n\t.validate_scan_mask = gsn_iio_scan_mask,", 1)
    broken_sources = {label: source.replace(old, new) for label, (old, new) in mutations.items()}
    broken_sources["strict-request-mask"] = legacy_source
    guard = """	if (!indio->active_scan_mask ||
	    indio->active_scan_mask[0] != gsn_scan_masks[0])
		return -EINVAL;
"""
    assert source.count(guard) == 1
    broken_sources["missing-producer-mask-guard"] = source.replace(guard, "", 1)
    negative = {}
    for old, _ in mutations.values():
        assert source.count(old) == 1
    for label, broken_source in broken_sources.items():
        broken = build(label, broken_source)
        if label == "strict-request-mask":
            assert transaction_cases(broken, env, legacy=True) == 1
        control = subprocess.run([str(broken)], env=env, capture_output=True, text=True, timeout=20)
        output = control.stdout + control.stderr
        (RESULTS / f"kernel-iio-buffer-{label}.log").write_text(output)
        if control.returncode == 0 or "Assertion" not in output:
            raise SystemExit(f"Negative control {label} did not fail an assertion:\n{output}")
        negative[label] = "rejected by invariant assertion"
    report = {
        "passed": True, "hardware_access": False, "functions": NAMES,
        "method": "Actual extracted driver structures, channel metadata and C functions; synthetic IIO/input/USB/lock boundaries",
        "sanitizers": ["address", "undefined", "leak"],
        "coverage": result.stdout.strip(), "negative_controls": negative,
        "python_transaction_core_selection_cases": transactions,
        "old_callback_exact_EINVAL_and_rollback_reproduced": True,
        "cross_language_scan_decoder_reference_cases": crossings,
        "source_sha256": {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()
                          for name in ("kernel/gs_native_usb.c", "tests/kernel_iio_buffer_fake.c",
                                       "tests/check_kernel_iio_buffer.py", "src/gs_sensor.c",
                                       "tools/imu/gamesir_imu_stream.py", "tools/imu/gyro_reference.py",
                                       "tools/imu/gamesir_imu_diagnostic.py")},
        "limits": ["Does not execute Linux IIO FIFO, sysfs, open-file, USB or input cores.",
                   "Locks and retained IIO references are invariant models, not a proof of race freedom.",
                   "No hardware timing, wireless-loss, suspend/resume or physical calibration validation."],
    }
    (RESULTS / "kernel-iio-buffer.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout.strip())
    print(f"PASS: {transactions} real Python setup/rollback to C selection cases; legacy EINVAL reproduced")
    print(f"PASS: {len(negative)} isolated IIO-adapter negative controls rejected")
    print(f"PASS: {len(crossings)} actual-C-scan to Python decoder/known-angle analyzer paths, synthetic only")


if __name__ == "__main__":
    main()
