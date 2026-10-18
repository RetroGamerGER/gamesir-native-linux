#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Opt-in gyro hypotheses over saved packets or read-only IIO attributes.

No USB/control-node access, sensor configuration, uinput, SDL injection or
calibration installation. IIO sweeps are NOT coherent sensor samples.
"""
import argparse
from collections import Counter
import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PROFILES = {125: Fraction(7, 1600), 250: Fraction(7, 800),
            500: Fraction(7, 400), 1000: Fraction(7, 200), 2000: Fraction(7, 100)}
IIO_NAME = "gamesir_g7pro_raw_experimental"
CHANNELS = [f"in_{sensor}_{axis}_raw" for sensor in ("anglvel", "accel") for axis in "xyz"]
MAX_SWEEP_NS = 100_000_000
OBSERVED_AXIS_PROFILE = "g7pro-observed-20261018"


def axis_profile_info(name):
    if name != OBSERVED_AXIS_PROFILE:
        raise ValueError("unknown explicitly selected experimental axis profile")
    return {"id": name, "version": 1, "scope": "standard G7 Pro, 3537:109c, 2.4 GHz dongle",
            "evidence": "docs/GYRO_AXIS_TEST.md; recorded at afa840a, two separately approved instances",
            "status": "observed qualitative directions; experimental mapping, not full calibration",
            "positive_motion_from_wire": {"pitch_up": "G0", "yaw_left": "G1", "roll_left": "G2"},
            "body_frame": {"X": "right", "Y": "toward USB/front edge, away from player",
                           "Z": "out of button face; right-handed"},
            "body_xyz_from_wire": [{"raw_axis": 0, "sign": 1},
                                   {"raw_axis": 2, "sign": -1},
                                   {"raw_axis": 1, "sign": 1}],
            "accelerometer_mapping_applied": False, "scale_verified": False,
            "physical_axis_mapping_verified": False, "calibration_verified": False,
            "sdl_runtime_enable": False}


def body_vector(wire, axis_profile):
    mapping = axis_profile_info(axis_profile)["body_xyz_from_wire"]
    return [wire[item["raw_axis"]] * item["sign"] for item in mapping]


GUIDED_PHASES = (
    (0, "rest", "AUFZEICHNUNG LÄUFT. 15 Sekunden ruhig liegen lassen."),
    (15, "pickup_buffer", "15 Sekunden Vorbereitung: vorsichtig aufnehmen, noch nicht drehen."),
    (30, "motion", "JETZT 30 Sekunden langsam um alle drei Achsen bewegen, jeweils in beide Richtungen. Nicht schütteln."),
    (60, "put_down_buffer", "JETZT wieder ablegen. Du hast 15 Sekunden; danach liegen lassen."),
    (75, "rest_end", "SCHLUSSRUHE: weitere 15 Sekunden ruhig liegen lassen. Danach endet die Aufzeichnung."),
)


def guided_phase(elapsed):
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite nonnegative guided elapsed time required")
    if elapsed >= 90:
        return None
    return max(i for i, phase in enumerate(GUIDED_PHASES) if elapsed >= phase[0])


class GuidedCues:
    """Own asynchronous KDE notifications; no hardware or arbitrary commands."""
    def __init__(self, event_sink=None):
        self.event_sink = event_sink or (lambda row: None)
        self.child = None
        self.retired = []

    def check(self):
        if self.child is not None:
            code = self.child.poll()
            if code is not None and code != 0:
                raise ValueError(f"KDE cue process failed: {code}")

    def show(self, event, instruction, seconds, scheduled_ns=None):
        self.check()
        if self.child is not None:
            if self.child.poll() is None:
                try:
                    self.child.terminate()
                except ProcessLookupError:
                    pass
            self.retired.append(self.child)
        self.child = subprocess.Popen(
            ["/usr/bin/kdialog", "--title", "GameSir – Gyro-Anzeigetest", "--passivepopup", instruction, str(seconds)],
            shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        now = time.monotonic_ns()
        self.event_sink({"event": event, "instruction": instruction,
                         "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "monotonic_ns": now,
                         "scheduled_monotonic_ns": scheduled_ns,
                         "requested_lateness_ns": now - scheduled_ns if scheduled_ns is not None else None,
                         "popup_seconds": seconds, "user_saw_notification_verified": False})
        if scheduled_ns is not None and now - scheduled_ns > 2_000_000_000:
            raise ValueError("KDE cue launch delayed over 2 seconds")
        print(f"CUE {event}: {instruction}", flush=True)

    def close(self):
        errors = []
        for child in [*self.retired, *([self.child] if self.child is not None else [])]:
            try:
                if child.poll() is None:
                    try:
                        child.terminate()
                    except ProcessLookupError:
                        pass
                try:
                    child.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    try:
                        child.kill()
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=.5)
            except (OSError, subprocess.TimeoutExpired) as error:
                errors.append(str(error))
        if errors:
            raise OSError("KDE cleanup: " + "; ".join(errors))


def cue_due(elapsed, previous):
    index = guided_phase(elapsed)
    if index is None or index == previous:
        return index
    if index != previous + 1 or elapsed - GUIDED_PHASES[index][0] > 2:
        raise ValueError("guided phase missed or cue delayed over 2 seconds; stop, no catch-up")
    return index


def vector(value, *, raw=False):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("three axis values required")
    for x in value:
        if raw:
            if type(x) is not int or not -32768 <= x <= 32767:
                raise ValueError("signed int16 raw values required")
        elif type(x) not in (int, float) or not math.isfinite(x) or not -32768 <= x <= 32767:
            raise ValueError("finite bias in raw int16 range required")
    return list(value)


def convert(gyro_raw, accel_raw, profile, bias=(0., 0., 0.), *, axis_profile=None):
    if type(profile) is not int or profile not in PROFILES:
        raise ValueError("explicit experimental range required; no default")
    g, a, b = vector(gyro_raw, raw=True), vector(accel_raw, raw=True), vector(bias)
    dps = [(x - offset) * float(PROFILES[profile]) for x, offset in zip(g, b)]
    result = {"gyro_raw": g, "accel_raw": a, "experiment": True,
            "test_values": {"gyro_dps": dps, "gyro_rad_s": [math.radians(x) for x in dps],
                            "accel_g": [x / 8192 for x in a],
                            "accel_m_s2": [x / 8192 * 9.80665 for x in a]}}
    if axis_profile is not None:
        body_dps = body_vector(dps, axis_profile)
        result["experimental_axes"] = {
            "profile_id": axis_profile, "body_gyro_dps_xyz": body_dps,
            "body_gyro_rad_s_xyz": [math.radians(x) for x in body_dps],
            "positive_motion_dps": dict(zip(("pitch_up", "yaw_left", "roll_left"), dps)),
            "scale_verified": False, "calibration_verified": False, "sdl_runtime_enable": False}
    return result


def profile_info(profile, bias=(0., 0., 0.)):
    factor = PROFILES[profile]
    return {"assumed_sensor": "LSM6DS3TR-C", "assumed_range_dps": profile,
            "dps_per_raw_count": {"numerator": factor.numerator, "denominator": factor.denominator},
            "bias_raw_assumption": vector(bias), "accel_counts_per_g_assumption": 8192,
            "chip_verified": False, "range_verified": False, "usb_preserves_sensor_counts_verified": False,
            "bias_verified": False, "axis_order": "wire G0/G1/G2 and A0/A1/A2; physical axes unverified",
            "source": "user-supplied ST datasheet table; 250..2000 corroborated by stored Linux gain table",
            "local_primary_125_dps_reference_verified": False,
            "calibration_verified": False, "sdl_runtime_enable": False}


def replay(path, *, axis_profile=None):
    # Reuse our strict stored-record reader and existing byte decoder.
    sys.path.insert(0, str(ROOT / "tools/offline"))
    from gamesir_offline.records import read_records
    from gamesir_offline.protocol import decode_packet
    counters, samples, key = Counter(), [], None
    for record in read_records(path):
        counters["records"] += 1
        if record.vid != 0x3537 or record.pid not in (0x109c, 0x105e) or record.interface != 0 or record.endpoint != 0x82:
            counters["other_device_or_endpoint"] += 1
            continue
        if record.stage != "complete" or record.status != 0:
            counters["not_successful_completion"] += 1
            continue
        if record.capture_truncated or record.reported_length != len(record.payload):
            counters["truncated_or_length_mismatch"] += 1
            continue
        decoded = decode_packet(record.payload, endpoint=record.endpoint)
        if (len(record.payload) != 64 or record.payload[:2] != b"\x10\x00" or
                decoded.disposition != "decoded" or decoded.kind != "gamesir_telemetry"):
            counters["not_full_imu_telemetry"] += 1
            continue
        if axis_profile is not None:
            axis_profile_info(axis_profile)
            if record.pid != 0x109c:
                raise ValueError("observed axis profile is scoped to standard 3537:109c, not ZZZ")
        if key is not None and key != record.stream_key:
            raise ValueError("multiple IMU device/session/timebase streams; filter offline first")
        key = record.stream_key
        stamp = record.timestamp_us * 1000
        if samples and stamp <= samples[-1]["timestamp_ns"]:
            raise ValueError("duplicate or nonmonotonic packet timestamps")
        samples.append({"timestamp_ns": stamp, "gyro_raw": decoded.fields["gyro_raw_i16"],
                        "accel_raw": decoded.fields["accel_raw_i16"], "coherent": True,
                        "timebase": record.timebase, "source_kind": record.source_kind})
    if not samples:
        raise ValueError("no complete successful target IMU packets")
    return samples, {"record_counts": dict(counters), "stream_key": list(key),
                     "source_sha256": digest(Path(path)), "device_clock_verified": False}


def replay_buffer(path, *, axis_profile=None):
    """Saved bounded worker bundle only; verify originals, never inspect live IIO."""
    from gamesir_gyro_guided import read_regular, verify_capture
    from gamesir_imu_stream import ScanDecoder, CHANNELS as SCAN_CHANNELS
    path = Path(path)
    report = json.loads(read_regular(path / "report.json", 1_048_576))
    if not isinstance(report, dict):
        raise ValueError("saved worker report must be an object")
    start = report.get("capture_started_monotonic_ns")
    if type(start) is not int or start <= 0:
        raise ValueError("successful saved capture start required")
    verified = verify_capture(path, start)
    report = verified["worker_report"]

    def original(name, maximum=64 * 1_048_576):
        data = read_regular(path / name, maximum)
        if hashlib.sha256(data).hexdigest() != verified["files"][name]:
            raise ValueError("saved capture changed after checksum verification")
        return data

    layout = json.loads(original("layout.json", 1_048_576))
    transaction = json.loads(original("buffer-transaction.json", 1_048_576))
    before = transaction.get("before")
    if not isinstance(layout, dict) or not isinstance(before, dict):
        raise ValueError("saved layout and transaction metadata must be objects")
    usb, metadata = before.get("usb"), layout.get("metadata")
    identity = before.get("iio_identity")
    if (not isinstance(usb, dict) or not isinstance(metadata, dict) or
            not isinstance(before.get("directory"), str) or not before["directory"] or
            not isinstance(identity, list) or len(identity) != 2 or
            any(type(x) is not int or x < 0 for x in identity)):
        raise ValueError("saved instance metadata invalid")
    if axis_profile is not None:
        axis_profile_info(axis_profile)
        if (usb.get("vid"), usb.get("pid"), usb.get("interface_number"), usb.get("driver")) != ("3537", "109c", 0, "gs_native"):
            raise ValueError("observed axis profile requires saved standard native 3537:109c metadata")
    expected_instance = before["directory"] + ":" + ":".join(map(str, identity))
    if (layout.get("channels") != list(SCAN_CHANNELS) or layout.get("scan_bytes") != 32 or
            layout.get("counter_offset") != 16 or layout.get("host_timestamp_offset") != 24 or
            metadata.get("clock") != "monotonic" or metadata.get("instance_id") != expected_instance):
        raise ValueError("saved coherent layout/instance mismatch")
    raw = original("scans.bin")
    decoder = ScanDecoder(expected_instance, 250_000_000, "iio_buffer")
    samples = []
    for offset in range(0, len(raw), 65536):
        samples.extend(decoder.feed(raw[offset:offset + 65536]))
    decoder.finish()
    recorded = [json.loads(line) for line in original("observations.jsonl").splitlines()]
    if (samples != recorded or len(samples) != report.get("observations") or
            len(raw) != report.get("original_bytes")):
        raise ValueError("saved binary/JSON/count disagreement")
    return samples, {"capture_sha256_verified": True, "original_sha256": verified["files"],
                     "instance_id": expected_instance, "device_clock_verified": False,
                     "source_kind": "saved_coherent_worker_bundle", "max_gap_ns": 250_000_000}


def distribution(values):
    return {"mean": statistics.mean(values), "std_population": statistics.pstdev(values),
            "min": min(values), "max": max(values)}


def analyze(samples, profile, bias=(0., 0., 0.), *, axis_profile=None):
    if not samples:
        raise ValueError("no samples")
    converted = [convert(s["gyro_raw"], s["accel_raw"], profile, bias, axis_profile=axis_profile) for s in samples]
    stamps = [s["timestamp_ns"] for s in samples]
    if any(type(t) is not int or t < 0 for t in stamps):
        raise ValueError("nonnegative integer nanosecond timestamps required")
    intervals = [b - a for a, b in zip(stamps, stamps[1:])]
    if any(delta <= 0 for delta in intervals):
        raise ValueError("duplicate or nonmonotonic timestamps")
    timebases = {s["timebase"] for s in samples}
    if len(timebases) != 1:
        raise ValueError("mixed timebases")
    coherent = all(s["coherent"] is True for s in samples)
    median = statistics.median(intervals) if intervals else None
    gaps = {i for i, delta in enumerate(intervals) if delta > 2 * median}
    dps = [s["test_values"]["gyro_dps"] for s in converted]
    # Illustrative delivery-time integral only, never a verified rotation.
    integral = None
    if coherent and intervals:
        integral = [sum((dps[i][axis] + dps[i + 1][axis]) / 2 * delta / 1e9
                        for i, delta in enumerate(intervals) if i not in gaps) for axis in range(3)]
    result = {"sample_count": len(samples), "profile": profile_info(profile, bias),
            "calibration_verified": False, "packet_loss_known": False,
            "coherent_six_axes": coherent,
            "timing": {"timebase": next(iter(timebases)), "device_clock_verified": False,
                       "median_interval_ns": median, "max_interval_ns": max(intervals, default=None),
                       "gap_candidates_over_2x_median": len(gaps),
                       "gap_intervals_excluded_from_integral": len(gaps),
                       "observed_span_ns": sum(intervals),
                       "integral_covered_ns": sum(delta for i, delta in enumerate(intervals) if i not in gaps) if integral is not None else None,
                       "integral_excluded_ns": sum(intervals[i] for i in gaps) if integral is not None else None,
                       "integral_coverage_fraction": (sum(delta for i, delta in enumerate(intervals) if i not in gaps) / sum(intervals)) if integral is not None else None,
                       "gap_threshold_is_heuristic_not_packet_loss": True,
                       "internal_sensor_rate_hz": None},
            "gyro_raw_stats": [distribution([s["gyro_raw"][i] for s in samples]) for i in range(3)],
            "gyro_dps_stats": [distribution([s[i] for s in dps]) for i in range(3)],
            "gyro_rad_s_stats": [distribution([math.radians(s[i]) for s in dps]) for i in range(3)],
            "accel_norm_g_stats": distribution([math.sqrt(sum(x*x for x in s["test_values"]["accel_g"])) for s in converted]),
            "consecutive_identical_values": sum(a["gyro_raw"] == b["gyro_raw"] and a["accel_raw"] == b["accel_raw"]
                                                for a, b in zip(samples, samples[1:])),
            "signed_int16_endpoint_counts": {key: [sum(s[key][i] in (-32768, 32767) for s in samples) for i in range(3)]
                                             for key in ("gyro_raw", "accel_raw")},
            "angle_integration_deg": integral,
            "angle_integration_status": (f"illustrative {next(iter(timebases))} integral; partial when gaps excluded; not reference calibration") if integral is not None else
                                        "unavailable: noncoherent IIO sweep or fewer than two samples",
            "known_angle_reference": None, "selected_as_actual_hardware_profile": False}
    if axis_profile is not None:
        result["experimental_axes"] = {
            "profile": axis_profile_info(axis_profile),
            "body_gyro_dps_stats_xyz": [distribution([s["experimental_axes"]["body_gyro_dps_xyz"][i]
                                                      for s in converted]) for i in range(3)],
            "body_gyro_rad_s_stats_xyz": [distribution([s["experimental_axes"]["body_gyro_rad_s_xyz"][i]
                                                        for s in converted]) for i in range(3)]}
    return result


def read_attribute(path):
    resolved = path.resolve(strict=True)
    if any(resolved == p or p in resolved.parents for p in map(Path, ("/dev", "/proc"))):
        raise ValueError("IIO attribute required, not a device/control node")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("regular IIO attribute required")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("attribute changed file type")
        value = handle.read(257)
        if len(value) > 256:
            raise ValueError("oversized IIO attribute")
        return value.decode("ascii").strip()


def read_iio_snapshot(directory):
    directory = Path(directory).resolve(strict=True)
    identity = directory.stat()
    if read_attribute(directory / "name") != IIO_NAME:
        raise ValueError("not the expected gs_native raw IIO device")
    begin = time.monotonic_ns()
    values = [int(read_attribute(directory / name)) for name in CHANNELS]
    end = time.monotonic_ns()
    after = directory.stat()
    if (identity.st_dev, identity.st_ino) != (after.st_dev, after.st_ino) or read_attribute(directory / "name") != IIO_NAME:
        raise ValueError("IIO device identity changed while reading")
    vector(values[:3], raw=True)
    vector(values[3:], raw=True)
    if end - begin > MAX_SWEEP_NS:
        raise ValueError("completed IIO read sweep exceeded 100 ms quality limit; discard and stop")
    return {"timestamp_ns": (begin + end) // 2, "read_begin_ns": begin, "read_end_ns": end,
            "gyro_raw": values[:3], "accel_raw": values[3:], "coherent": False,
            "timebase": "host_monotonic_read_window", "source_kind": "iio_attribute_observation",
            "iio_instance": [identity.st_dev, identity.st_ino]}


def cached_iio_identity(directory):
    directory = Path(directory).resolve(strict=True)
    identity = directory.stat()
    if read_attribute(directory / "name") != IIO_NAME:
        raise ValueError("not the expected gs_native raw IIO device")
    return [identity.st_dev, identity.st_ino]


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


class Bundle:
    """New private directory only; persist partial observations on interruption."""
    def __init__(self, path):
        self.path = Path(path)
        # Avoid output in pseudo filesystems, even via an alias.
        resolved = self.path.resolve()
        if any(resolved == p or p in resolved.parents for p in map(Path, ("/dev", "/proc", "/sys"))):
            raise ValueError("saved-file output directory required")
        self.path.mkdir(mode=0o700, parents=False, exist_ok=False)
        self.handle = self.open("observations.jsonl")
        self.cue_handle = None

    def open(self, name):
        fd = os.open(self.path / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        return os.fdopen(fd, "w", encoding="utf-8")

    def append(self, row):
        self.handle.write(json.dumps(row, allow_nan=False) + "\n")
        self.handle.flush()

    def append_cue(self, row):
        if self.cue_handle is None:
            self.cue_handle = self.open("cues.jsonl")
        self.cue_handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        self.cue_handle.flush()

    def finish(self, report, extra_files=()):
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        if self.cue_handle is not None:
            self.cue_handle.flush()
            os.fsync(self.cue_handle.fileno())
            self.cue_handle.close()
        with self.open("report.json") as output:
            json.dump(report, output, indent=2, allow_nan=False)
            output.write("\n")
        with self.open("SHA256SUMS") as output:
            for name in ("observations.jsonl", "report.json", *(("cues.jsonl",) if self.cue_handle is not None else ()), *extra_files):
                if Path(name).name != name or (self.path / name).is_symlink():
                    raise ValueError("regular evidence filename required")
                output.write(f"{digest(self.path / name)}  {name}\n")


def measurement_plan():
    phases = [{"phase": "prepare", "seconds": 30, "instruction": "Controller ablegen; noch nicht bewegen."},
              {"phase": "rest_start", "seconds": 30, "instruction": "Ruhig liegen lassen; Bias nur als Messkandidat erfassen."}]
    for axis in ("yaw", "pitch", "roll"):
        for direction in ("positive", "negative"):
            phases += [{"phase": f"buffer_{axis}_{direction}", "seconds": 15,
                        "instruction": "Auf nächste Ansage warten, Ausgangslage und Winkelmarkierung vorbereiten."},
                       {"phase": f"rotate_{axis}_{direction}", "seconds": 30,
                        "instruction": "Eine langsame, markierte 90-Grad-Drehung nur um diese Gehäuseachse. Nicht zurückdrehen; Anfang und Ende separat markieren.",
                        "reference_angle_degrees_magnitude": 90, "reference_is_instruction_not_verified_action": True}]
    for face in ("top", "bottom", "left", "right", "front", "rear"):
        phases += [{"phase": f"buffer_pose_{face}", "seconds": 15,
                    "instruction": "Nächste Gehäuseseite nach oben legen; danach loslassen."},
                   {"phase": f"pose_{face}", "seconds": 20,
                    "instruction": "Ruhig und waagerecht liegen lassen; Gehäuseseite fotografisch/notiert belegen."}]
    phases += [{"phase": "rest_end_buffer", "seconds": 15, "instruction": "Controller ruhig ablegen."},
               {"phase": "rest_end", "seconds": 30, "instruction": "Schlussruhe und Biasänderung erfassen."}]
    return {"schema_version": 1, "plan_only": True, "hardware_authorized_by_plan": False,
            "seconds": sum(p["seconds"] for p in phases), "phases": phases,
            "required_before_qualified_rotation_test": "coherent samples with timestamps; existing separate IIO raw reads do not qualify",
            "abort": ["disconnect or stale/read error", "wrong device", "mixed timebase or nonmonotonic timestamps",
                      "unexpected controller/system change", "user stop"],
            "axis_sign_convention": "Define housing yaw/pitch/roll positive directions with drawing before measurement; wire-to-housing map unknown",
            "packet_loss": "No proven IMU sequence counter; report gaps and capture drops separately, never infer RF loss from unchanged values"}


def cli_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profiles", help="print assumptions; no device access")
    sub.add_parser("axis-profiles", help="print observed experimental axes; no device access")
    sub.add_parser("plan", help="print guided future measurement plan; no device access")
    for command in ("replay", "replay-buffer", "observe-iio"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--experimental", action="store_true", required=True)
        choices = [str(x) for x in PROFILES] + (["all"] if command != "observe-iio" else [])
        cmd.add_argument("--profile", choices=choices, required=True)
        cmd.add_argument("--bias-raw", default="0,0,0", help="explicit assumed G0,G1,G2 bias; never auto-estimated")
        cmd.add_argument("--output", type=Path, required=True, help="new persistent private directory; parent must exist")
        if command != "observe-iio":
            cmd.add_argument("--axis-profile", choices=[OBSERVED_AXIS_PROFILE], default=None,
                             help="explicit experimental axes for saved data only; no default")
        if command == "replay":
            cmd.add_argument("--records", type=Path, required=True)
        elif command == "replay-buffer":
            cmd.add_argument("--capture-dir", type=Path, required=True, help="saved bounded-worker capture bundle")
        else:
            cmd.add_argument("--iio-dir", type=Path, required=True)
            cmd.add_argument("--duration", type=float, default=30)
            cmd.add_argument("--period-ms", type=float, default=20)
            cmd.add_argument("--guided-kde", action="store_true",
                             help="30 seconds preparation then locally timed KDE cues; requires duration 90")
    return parser


def main(argv=None):
    args = cli_parser().parse_args(argv)
    if args.command == "axis-profiles":
        print(json.dumps(axis_profile_info(OBSERVED_AXIS_PROFILE), indent=2))
        return 0
    if args.command in ("profiles", "plan"):
        value = [profile_info(p) for p in PROFILES] if args.command == "profiles" else measurement_plan()
        print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    bundle, samples, failure, cues = None, [], None, None
    axis_profile = getattr(args, "axis_profile", None)
    try:
        bias = vector([float(x) for x in args.bias_raw.split(",")])
        profiles = list(PROFILES) if args.profile == "all" else [int(args.profile)]
        if args.command == "observe-iio":
            if not math.isfinite(args.duration) or not 0 < args.duration <= 1800:
                raise ValueError("duration must be >0 and <=1800 seconds")
            if not math.isfinite(args.period_ms) or not 5 <= args.period_ms <= 1000:
                raise ValueError("period must be 5..1000 ms")
            if args.guided_kde and args.duration != 90:
                raise ValueError("guided KDE mode requires exactly 90 seconds")
            if args.guided_kde and (not Path('/usr/bin/kdialog').is_file() or
                                   not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))):
                raise ValueError("guided KDE mode needs installed kdialog and a graphical session")
        elif args.command == "replay-buffer":
            samples, metadata = replay_buffer(args.capture_dir, axis_profile=axis_profile)
        else:
            samples, metadata = replay(args.records, axis_profile=axis_profile)
        bundle = Bundle(args.output)
        if args.command == "observe-iio":
            metadata = {"iio_directory": str(args.iio_dir), "atomic": False, "packet_loss_known": False,
                        "requested_reader_period_ms": args.period_ms, "requested_duration_s": args.duration,
                        "guided_kde": args.guided_kde}
            if args.guided_kde:
                expected_iio_instance = cached_iio_identity(args.iio_dir)
                cues = GuidedCues(bundle.append_cue)
                prepare_begin = time.monotonic()
                cues.show("preparation", "30 SEKUNDEN VORBEREITUNG. Controller ruhig ablegen. Erst bei BEWEGEN drehen.", 30,
                          round(prepare_begin * 1e9))
                while (remaining := prepare_begin + 30 - time.monotonic()) > 0:
                    cues.check()
                    time.sleep(min(.1, remaining))
                cues.check()
                if time.monotonic() - prepare_begin > 32:
                    raise ValueError("preparation deadline missed over 2 seconds")
            end = time.monotonic() + args.duration
            started = end - args.duration
            previous_phase = -1
            print("IIO-Beobachtung: nicht atomare Rohwerte, keine bestätigte Kalibrierung. Strg+C beendet und sichert.", flush=True)
            while time.monotonic() < end:
                if cues is not None:
                    elapsed = time.monotonic() - started
                    phase = cue_due(elapsed, previous_phase)
                    if phase is None:
                        break
                    if phase != previous_phase:
                        offset, label, instruction = GUIDED_PHASES[phase]
                        until = GUIDED_PHASES[phase + 1][0] if phase + 1 < len(GUIDED_PHASES) else 90
                        cues.show(label, instruction, max(1, math.ceil(until - elapsed)),
                                  round((started + offset) * 1e9))
                        previous_phase = phase
                    cues.check()
                    if time.monotonic() >= end:
                        break
                sample = read_iio_snapshot(args.iio_dir)
                if cues is not None and sample["iio_instance"] != expected_iio_instance:
                    raise ValueError("IIO instance changed during preparation; no automatic reconnection")
                if samples and sample["iio_instance"] != samples[0]["iio_instance"]:
                    raise ValueError("IIO instance changed; no automatic reconnection")
                if samples and sample["timestamp_ns"] <= samples[-1]["timestamp_ns"]:
                    raise ValueError("nonmonotonic read timestamp")
                samples.append(sample)
                row = dict(sample, conversions={str(p): convert(sample["gyro_raw"], sample["accel_raw"], p, bias, axis_profile=axis_profile) for p in profiles})
                bundle.append(row)
                print(json.dumps(row, allow_nan=False), flush=True)
                time.sleep(min(args.period_ms / 1000, max(0, end - time.monotonic())) if cues is not None else args.period_ms / 1000)
            if cues is not None:
                cues.check()
                if previous_phase != len(GUIDED_PHASES) - 1:
                    raise ValueError("last guided phase skipped; no successful completion")
                if time.monotonic() - end > 2:
                    raise ValueError("guided completion delayed over 2 seconds")
                cues.show("finished", "TEST BEENDET. Controller darf liegen bleiben; es werden keine Sensorwerte mehr gelesen.",
                          3, round(end * 1e9))
                finish_notice_end = time.monotonic() + 3
                while (remaining := finish_notice_end - time.monotonic()) > 0:
                    cues.check()
                    time.sleep(min(.1, remaining))
        else:
            for sample in samples:
                bundle.append(dict(sample, conversions={str(p): convert(sample["gyro_raw"], sample["accel_raw"], p, bias, axis_profile=axis_profile) for p in profiles}))
    except (ValueError, OSError, KeyError, TypeError, KeyboardInterrupt) as error:
        failure = "user_interrupted" if isinstance(error, KeyboardInterrupt) else f"{type(error).__name__}: {error}"
    if cues is not None:
        try:
            cues.close()
        except (OSError, subprocess.TimeoutExpired) as error:
            failure = failure or f"KDE cue cleanup failed: {error}"
    if bundle is not None and not samples and failure is None:
        failure = "no observations before deadline"
    if bundle is not None:
        report = {"schema_version": 1, "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "mode": args.command, "completed": failure is None, "failure": failure,
                  "metadata": metadata if "metadata" in locals() else {},
                  "profiles": {str(p): analyze(samples, p, bias, axis_profile=axis_profile) for p in profiles} if samples else {},
                  "runtime_calibration_changed": False, "automatic_profile_selection": False}
        bundle.finish(report)
    if failure:
        print(f"STOP: {failure}", file=sys.stderr)
        return 1
    print(f"Gespeichert: {args.output}; experimentell, kein aktiver Hardwarebereich nachgewiesen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
