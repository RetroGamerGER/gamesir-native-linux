# SPDX-License-Identifier: GPL-2.0-only
"""Strict JSONL records from regular files, with explicit evidence provenance."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat


MAX_LINE_BYTES = 65536
MAX_RECORDS = 250000
_HEX = re.compile(r"[0-9a-fA-F]*\Z")


class RecordError(ValueError):
    pass


def _integer(value, name: str, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise RecordError(f"{name}: integer in {lower}..{upper} required")
    return value


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or any(ord(c) < 32 for c in value):
        raise RecordError(f"{name}: nonempty text without control characters required")
    return value


def _hex_number(value, name: str, width: int) -> int:
    if not isinstance(value, str) or len(value) != width or not _HEX.fullmatch(value):
        raise RecordError(f"{name}: exactly {width} hexadecimal characters required")
    return int(value, 16)


def _keys(value, expected: set, name: str):
    if not isinstance(value, dict) or set(value) != expected:
        raise RecordError(f"{name}: fields must be {', '.join(sorted(expected))}")


@dataclass(frozen=True)
class Record:
    source_kind: str
    source_id: str
    session: str
    timestamp_us: int
    timebase: str
    vid: int
    pid: int
    bus: int
    address: int
    interface: int
    endpoint: int
    stage: str
    status: int
    reported_length: int
    capture_truncated: bool
    payload: bytes

    @property
    def stream_key(self) -> tuple:
        # A changed identity, source, session, timebase or endpoint is never merged.
        return (self.source_kind, self.source_id, self.session, self.timebase,
                self.vid, self.pid, self.bus, self.address, self.interface, self.endpoint)

    def metadata(self) -> dict:
        return {
            "source": {"kind": self.source_kind, "id": self.source_id},
            "session": self.session, "timebase": self.timebase,
            "device": {"vid": f"{self.vid:04x}", "pid": f"{self.pid:04x}",
                       "bus": self.bus, "address": self.address, "interface": self.interface},
            "endpoint": f"{self.endpoint:02x}",
        }


def record_from_object(value: dict) -> Record:
    _keys(value, {"schema_version", "source", "session", "timestamp_us", "timebase",
                  "device", "endpoint", "stage", "status", "reported_length",
                  "capture_truncated", "data_hex"}, "record")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise RecordError("schema_version must be 1")
    source = value["source"]
    device = value["device"]
    _keys(source, {"kind", "id"}, "source")
    _keys(device, {"vid", "pid", "bus", "address", "interface"}, "device")
    if source["kind"] not in ("synthetic", "capture", "capture_excerpt"):
        raise RecordError("source.kind must be synthetic, capture or capture_excerpt")
    expected_timebase = "synthetic" if source["kind"] == "synthetic" else "host_capture"
    if value["timebase"] != expected_timebase:
        raise RecordError(f"timebase must be {expected_timebase} for this source kind")
    if value["stage"] not in ("submit", "complete", "error"):
        raise RecordError("stage must be submit, complete or error")
    if type(value["capture_truncated"]) is not bool:
        raise RecordError("capture_truncated must be boolean")
    hex_data = value["data_hex"]
    if (not isinstance(hex_data, str) or len(hex_data) > 8192 or len(hex_data) % 2
            or not _HEX.fullmatch(hex_data)):
        raise RecordError("data_hex must contain at most 4096 bytes of even-length plain hex")
    endpoint = _hex_number(value["endpoint"], "endpoint", 2)
    if endpoint & 0x70:
        raise RecordError("endpoint contains reserved address bits")
    return Record(
        source_kind=source["kind"], source_id=_text(source["id"], "source.id"),
        session=_text(value["session"], "session"),
        timestamp_us=_integer(value["timestamp_us"], "timestamp_us", 0, 2**63 - 1),
        timebase=value["timebase"], vid=_hex_number(device["vid"], "vid", 4),
        pid=_hex_number(device["pid"], "pid", 4),
        bus=_integer(device["bus"], "bus", 1, 65535),
        address=_integer(device["address"], "address", 1, 127),
        interface=_integer(device["interface"], "interface", 0, 255),
        endpoint=endpoint, stage=value["stage"],
        status=_integer(value["status"], "status", -(2**31), 2**31 - 1),
        reported_length=_integer(value["reported_length"], "reported_length", 0, 65535),
        capture_truncated=value["capture_truncated"], payload=bytes.fromhex(hex_data),
    )


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecordError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_records(path: str | Path):
    """Read regular saved files only. Reject device/proc/sys paths and FIFOs."""
    original = Path(path).absolute()
    special_trees = (("dev",), ("proc",), ("sys",))
    if original.parts[1:2] in special_trees:
        raise RecordError("device, proc and sys paths are not permitted")
    resolved = original.resolve(strict=True)
    if resolved.parts[1:2] in special_trees:
        raise RecordError("device, proc and sys paths are not permitted")
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise RecordError("input must be a regular saved file")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY
    descriptor = os.open(resolved, flags)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise RecordError("input changed and is no longer a regular file")
        records = 0
        line_number = 0
        while line := handle.readline(MAX_LINE_BYTES + 1):
            line_number += 1
            if len(line) > MAX_LINE_BYTES:
                raise RecordError(f"line {line_number}: exceeds {MAX_LINE_BYTES} bytes")
            if not line.strip():
                continue
            records += 1
            if records > MAX_RECORDS:
                raise RecordError(f"input exceeds {MAX_RECORDS} records")
            try:
                obj = json.loads(line, object_pairs_hook=_unique_object)
                yield record_from_object(obj)
            except (ValueError, TypeError, KeyError, UnicodeDecodeError, RecursionError) as error:
                raise RecordError(f"line {line_number}: {error}") from error
