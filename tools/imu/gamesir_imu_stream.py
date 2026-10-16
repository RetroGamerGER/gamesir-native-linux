#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read-only standard IIO buffer reader; offline decoder and setup plan.

Never enables/configures buffers, opens gsnative control nodes, or sends USB.
Capture is a separately authorized hardware operation, not part of any test.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import select
import stat
import struct
import sys
import time

from gamesir_imu_diagnostic import Bundle, IIO_NAME, read_attribute

CHANNELS = tuple(f"in_{sensor}_{axis}" for sensor in ("accel", "anglvel") for axis in "xyz") + ("in_count0", "in_timestamp")
SCAN_SIZE = 32
MAX_FILE_BYTES = 64 * 1024 * 1024


def configuration_plan():
    return {"plan_only": True, "executed": False, "requires_separate_approval": True,
            "coherent_buffer_capable_module_required": True,
            "module_installation_in_this_tool": False,
            "sequence": ["verify single intended native IIO instance and no other buffered reader",
                         "buffer/enable must be 0 before changing any buffer attributes",
                         "after explicit readiness: reserve exact read-only IIO FD before any configuration write",
                         "current_timestamp_clock = monotonic", "all eight listed scan_elements/*_en = 1",
                         "buffer/length = 512", "buffer/watermark = 1 if present",
                         "buffer/enable = 1, then bounded collector reuses the reserved FD",
                         "stop collector; restore buffer/enable = 0 and previous host settings before closing the reservation"],
            "scan_channels": list(CHANNELS), "full_scan_bytes": SCAN_SIZE,
            "buffer_enable_is_host_state_change": True, "usb_or_sensor_configuration_commands": False,
            "close_reader_disables_buffer": False,
            "counter_semantics": "accepted host IMU reports, not sensor/Funk loss counter",
            "clock": "CLOCK_MONOTONIC at host IMU processing; not a device timestamp"}


class ScanDecoder:
    def __init__(self, instance_id, max_gap_ns, source_kind="iio_buffer"):
        if not isinstance(instance_id, str) or not 1 <= len(instance_id) <= 1024 or any(ord(c) < 32 for c in instance_id):
            raise ValueError("explicit immutable instance_id required")
        if type(max_gap_ns) is not int or not 0 < max_gap_ns <= 60_000_000_000:
            raise ValueError("explicit positive max_gap_ns <=60s required")
        if source_kind not in ("synthetic", "iio_buffer"):
            raise ValueError("source_kind must be synthetic or iio_buffer")
        self.instance_id, self.max_gap_ns, self.source_kind = instance_id, max_gap_ns, source_kind
        self.pending = bytearray()
        self.last_count = self.last_stamp = None
        self.count = 0

    def feed(self, data, received_ns=None):
        if not isinstance(data, bytes) or len(data) > 65536:
            raise ValueError("bounded bytes chunk required")
        if received_ns is not None and (type(received_ns) is not int or received_ns <= 0):
            raise ValueError("positive integer host receipt timestamp required")
        self.pending.extend(data)
        while len(self.pending) >= SCAN_SIZE:
            frame = bytes(self.pending[:SCAN_SIZE]); del self.pending[:SCAN_SIZE]
            if frame[12:16] != bytes(4):
                raise ValueError("nonzero scan padding; wrong layout or invalid frame")
            values = struct.unpack_from("<6h", frame)
            counter = struct.unpack_from("<Q", frame, 16)[0]
            stamp = int.from_bytes(frame[24:32], sys.byteorder, signed=True)
            if counter == 0 or stamp <= 0:
                raise ValueError("nonpositive counter or timestamp")
            if received_ns is not None and (stamp > received_ns or received_ns - stamp > 1_000_000_000):
                raise ValueError("future or stale host timestamp")
            if self.last_stamp is not None:
                if stamp <= self.last_stamp or stamp - self.last_stamp > self.max_gap_ns:
                    raise ValueError("nonmonotonic timestamp or sample time gap; calibration invalid")
                if counter != self.last_count + 1:
                    raise ValueError("accepted-report counter gap/reset; calibration invalid, cause not RF-proven")
            self.last_count, self.last_stamp = counter, stamp
            self.count += 1
            yield {"timestamp_ns": stamp, "sample_number": counter,
                   "accel_raw": list(values[:3]), "gyro_raw": list(values[3:]),
                   "coherent": True, "timebase": "host_monotonic_receive",
                   "source_kind": self.source_kind, "instance_id": self.instance_id}

    def finish(self):
        if self.pending:
            raise ValueError("incomplete trailing scan; original bytes preserved")
        if not self.count:
            raise ValueError("no complete coherent scans")


def inspect_iio(directory):
    directory = Path(directory).resolve(strict=True)
    if read_attribute(directory / "name") != IIO_NAME:
        raise ValueError("unexpected native IIO name")
    before = directory.stat()
    clock = read_attribute(directory / "current_timestamp_clock")
    if clock != "monotonic":
        raise ValueError("CLOCK_MONOTONIC required")
    scan = directory / "scan_elements"
    enabled = {p.name[:-3] for p in scan.glob("*_en") if read_attribute(p) == "1"}
    if enabled != set(CHANNELS):
        raise ValueError("all and only eight full-scan channels required")
    types = {}
    for index, name in enumerate(CHANNELS):
        expected = "le:s16/16>>0" if index < 6 else "le:u64/64>>0" if index == 6 else f"{'le' if sys.byteorder == 'little' else 'be'}:s64/64>>0"
        if int(read_attribute(scan / f"{name}_index")) != index or read_attribute(scan / f"{name}_type") != expected:
            raise ValueError(f"unexpected IIO scan layout: {name}")
        types[name] = expected
    if read_attribute(directory / "buffer/enable") != "1":
        raise ValueError("buffer must already be enabled under separate authorization; reader never writes attributes")
    if read_attribute(directory / "buffer_stream_active") != "1":
        raise ValueError("producer gate stopped, including PM/quiesce; no automatic re-enable")
    if int(read_attribute(directory / "buffer/length")) < 2:
        raise ValueError("invalid buffer length")
    errors = int(read_attribute(directory / "buffer_push_errors"))
    if errors < 0:
        raise ValueError("invalid producer error counter")
    major, minor = map(int, read_attribute(directory / "dev").split(":"))
    after = directory.stat()
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError("IIO instance changed during metadata inspection")
    return {"directory": str(directory), "instance_id": f"{directory}:{before.st_dev}:{before.st_ino}",
            "major": major, "minor": minor, "scan_bytes": SCAN_SIZE, "types": types,
            "clock": clock, "buffer_push_errors": errors}


def saved_binary(path):
    path = Path(path).resolve(strict=True)
    if any(path == p or p in path.parents for p in map(Path, ("/dev", "/proc", "/sys"))):
        raise ValueError("regular stored binary only")
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("bounded regular stored binary required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    handle = os.fdopen(fd, "rb")
    if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode) or os.fstat(handle.fileno()).st_size > MAX_FILE_BYTES:
        handle.close(); raise ValueError("saved input changed file type")
    return handle


def boottime_offset():
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME) - time.monotonic_ns()


def live_chunks(metadata, node, duration, no_data_seconds, *, descriptor=None, check_alive=None):
    """Read only; an optional caller-owned FD reserves IIO through restoration.

    The transaction opens that FD before configuring the buffer. Opening a
    second IIO FD would fail EBUSY. The caller retains and closes its own FD.
    ``check_alive`` lets a bounded collector abort on frontend cancellation.
    """
    node = Path(node)
    info = node.lstat()
    if not stat.S_ISCHR(info.st_mode) or (os.major(info.st_rdev), os.minor(info.st_rdev)) != (metadata["major"], metadata["minor"]):
        raise ValueError("node must match this exact IIO character device")
    owned = descriptor is None
    fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW) if owned else descriptor
    try:
        if not owned:
            if type(fd) is not int or fd < 0:
                raise ValueError("valid caller-owned IIO descriptor required")
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            if flags & os.O_ACCMODE != os.O_RDONLY or not flags & os.O_NONBLOCK:
                raise ValueError("caller-owned IIO descriptor must be read-only and nonblocking")
        opened = os.fstat(fd)
        if not stat.S_ISCHR(opened.st_mode) or opened.st_rdev != info.st_rdev:
            raise ValueError("IIO node changed")
        start = last_data = time.monotonic()
        offset = boottime_offset()
        while time.monotonic() - start < duration:
            if check_alive is not None:
                check_alive()
            if abs(boottime_offset() - offset) > 50_000_000:
                raise ValueError("suspend/clock-domain discontinuity; no automatic resume")
            current = inspect_iio(metadata["directory"])
            if current["instance_id"] != metadata["instance_id"] or current["buffer_push_errors"] != metadata["buffer_push_errors"]:
                raise ValueError("IIO instance changed or producer buffer push failed")
            remaining = duration - (time.monotonic() - start)
            if remaining <= 0:
                break
            if not select.select([fd], [], [], min(.25, remaining))[0]:
                if time.monotonic() - last_data > no_data_seconds:
                    raise ValueError("no fresh coherent samples; stop without reconnect")
                continue
            if check_alive is not None:
                check_alive()
            if time.monotonic() - start >= duration:
                break
            try:
                data = os.read(fd, 4096)
            except BlockingIOError:
                if time.monotonic() - last_data > no_data_seconds:
                    raise ValueError("no fresh coherent samples after EAGAIN; stop without reconnect")
                time.sleep(.005)
                continue
            if not data:
                raise ValueError("IIO EOF/disconnect")
            last_data = time.monotonic()
            yield data, time.monotonic_ns()
        final = inspect_iio(metadata["directory"])
        if check_alive is not None:
            check_alive()
        if final["instance_id"] != metadata["instance_id"] or final["buffer_push_errors"] != metadata["buffer_push_errors"]:
            raise ValueError("IIO tail producer error or instance change")
        if abs(boottime_offset() - offset) > 50_000_000:
            raise ValueError("suspend at capture end; calibration invalid")
        if time.monotonic() - last_data > no_data_seconds:
            raise ValueError("no fresh coherent samples at capture end")
    finally:
        primary = sys.exc_info()[1]
        if owned:
            try:
                os.close(fd)
            except OSError as error:
                if primary is None:
                    raise
                primary.add_note(f"IIO descriptor close also failed: {error}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("configuration-plan")
    for mode in ("decode-file", "capture"):
        p = sub.add_parser(mode)
        p.add_argument("--output", type=Path, required=True)
        p.add_argument("--max-gap-ms", type=float, required=True)
        if mode == "decode-file":
            p.add_argument("--scans", type=Path, required=True)
            p.add_argument("--instance-id", required=True)
            p.add_argument("--source-kind", choices=("synthetic", "iio_buffer"), required=True)
        else:
            p.add_argument("--experimental", action="store_true", required=True)
            p.add_argument("--iio-dir", type=Path, required=True)
            p.add_argument("--device-node", type=Path, required=True)
            p.add_argument("--duration", type=float, required=True)
            p.add_argument("--no-data-seconds", type=float, default=2)
    args = parser.parse_args(argv)
    if args.command == "configuration-plan":
        print(json.dumps(configuration_plan(), indent=2)); return 0
    bundle = binary = chunks = None
    failure, count, byte_count = None, 0, 0
    cleanup_errors = []
    error_notes = []
    metadata = {"source_kind": getattr(args, "source_kind", "iio_buffer")}
    try:
        if not math.isfinite(args.max_gap_ms) or not 0 < args.max_gap_ms <= 60000:
            raise ValueError("explicit max-gap-ms in (0,60000] required")
        if args.command == "capture":
            if not math.isfinite(args.duration) or not 0 < args.duration <= 900:
                raise ValueError("capture duration must be (0,900] seconds")
            if not math.isfinite(args.no_data_seconds) or not 0 < args.no_data_seconds <= 5:
                raise ValueError("no-data-seconds must be (0,5]")
            metadata.update(inspect_iio(args.iio_dir))
            chunks = live_chunks(metadata, args.device_node, args.duration, args.no_data_seconds)
        else:
            metadata["instance_id"] = args.instance_id
        decoder = ScanDecoder(metadata["instance_id"], round(args.max_gap_ms * 1e6), metadata["source_kind"])
        bundle = Bundle(args.output)
        fd = os.open(bundle.path / "scans.bin", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        binary = os.fdopen(fd, "wb")
        with bundle.open("layout.json") as f:
            json.dump({"channels": CHANNELS, "scan_bytes": SCAN_SIZE, "counter_offset": 16,
                       "host_timestamp_offset": 24, "metadata": metadata,
                       "timestamp_is_device_time": False, "max_gap_ns": decoder.max_gap_ns}, f, indent=2);f.write("\n")
        if args.command == "decode-file":
            with saved_binary(args.scans) as source:
                def stored_chunks():
                    while data := source.read(4096):
                        yield data, None
                for data, received in stored_chunks():
                    byte_count += len(data)
                    if byte_count > MAX_FILE_BYTES:
                        raise ValueError("stored input grew beyond bounded file limit")
                    binary.write(data)
                    for row in decoder.feed(data, received):
                        bundle.append(row); count += 1
        else:
            for data, received in chunks:
                byte_count += len(data)
                if byte_count > MAX_FILE_BYTES:
                    raise ValueError("capture exceeded bounded byte limit")
                binary.write(data)
                for row in decoder.feed(data, received):
                    bundle.append(row); count += 1
        decoder.finish()
    except (ValueError, OSError, KeyboardInterrupt) as error:
        failure = "user_interrupted" if isinstance(error, KeyboardInterrupt) else f"{type(error).__name__}: {error}"
        error_notes = list(getattr(error, "__notes__", ()))
    finally:
        if chunks is not None:
            try:
                chunks.close()
            except OSError as error:
                cleanup_errors.append(f"close: {error}")
        if binary is not None:
            try:
                binary.flush();os.fsync(binary.fileno())
            except OSError as error:
                cleanup_errors.append(f"flush/fsync: {error}")
            finally:
                try:
                    binary.close()
                except OSError as error:
                    cleanup_errors.append(f"binary close: {error}")
    if cleanup_errors and failure is None:
        failure = f"cleanup failed: {cleanup_errors[0]}"
    if bundle is not None:
        bundle.finish({"schema_version": 1, "completed": failure is None, "failure": failure,
                       "observations": count, "metadata": metadata, "coherent": True,
                       "original_bytes": byte_count, "cleanup_errors": cleanup_errors,
                       "error_notes": error_notes,
                       "calibration_verified": False, "radio_or_sensor_loss_known": False,
                       "buffer_configuration_modified": False, "buffer_disabled_by_reader": False,
                       "clock": "host CLOCK_MONOTONIC, not device time"}, extra_files=("scans.bin", "layout.json"))
    if failure:
        print(f"STOP: {failure}", file=sys.stderr);return 1
    print(f"Saved {count} coherent scans in {args.output}; no calibration selected.");return 0


if __name__ == "__main__":
    sys.exit(main())
