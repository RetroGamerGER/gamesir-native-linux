# SPDX-License-Identifier: GPL-2.0-only
"""Private bridge transport v2; deliberately separate from broker API v1.

All integers use little endian. One producer connection owns one immutable
launch session, SDL joystick and evdev path. Timestamps use CLOCK_MONOTONIC;
they are emission timestamps, not claims of sensor or USB acquisition time.
"""
from dataclasses import dataclass
import re
import struct

VERSION = 2
EFFECT, CLOSE = 1, 2
FRAME = struct.Struct("<4sHHIIQQIiHHI64s16s")
SIZE = FRAME.size
EVENT_PATH = re.compile(r"/dev/input/event(?:0|[1-9][0-9]{0,8})\Z")


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Message:
    kind: int
    sequence: int
    monotonic_ns: int
    pid: int
    joystick: int
    left: int
    right: int
    duration_ms: int
    source_path: str
    session: bytes

    @property
    def zero_mask(self):
        if self.kind == CLOSE or not self.duration_ms:
            return 3
        return int(self.left == 0) | (int(self.right == 0) << 1)

    def encode(self):
        try:
            raw = self.source_path.encode("ascii")
            if len(raw) >= 64:
                raise ProtocolError("Source path exceeds fixed field")
            result = FRAME.pack(b"GST2", VERSION, self.kind, SIZE, 0,
                                self.sequence, self.monotonic_ns, self.pid,
                                self.joystick, self.left, self.right,
                                self.duration_ms, raw.ljust(64, b"\0"), self.session)
        except (UnicodeError, struct.error) as error:
            raise ProtocolError("Invalid transport value") from error
        decode(result)  # One validation contract for producers and consumers.
        return result


def decode(payload):
    if len(payload) != SIZE:
        raise ProtocolError("Expected exactly 128 bytes")
    magic, version, kind, size, reserved, seq, stamp, pid, joystick, left, right, duration, path, session = FRAME.unpack(payload)
    if (magic != b"GST2" or version != VERSION or size != SIZE or reserved or
            kind not in (EFFECT, CLOSE) or not seq or not stamp or not pid or joystick < 0 or
            session == bytes(16)):
        raise ProtocolError("Unsupported or invalid bridge header")
    raw, separator, padding = path.partition(b"\0")
    try:
        source = raw.decode("ascii")
    except UnicodeError as error:
        raise ProtocolError("Source must be an ASCII evdev path") from error
    if not separator or any(padding) or not EVENT_PATH.fullmatch(source):
        raise ProtocolError("Source must be one canonical event path with zero padding")
    if kind == CLOSE and (left or right or duration):
        raise ProtocolError("CLOSE must carry zero amplitudes and duration")
    return Message(kind, seq, stamp, pid, joystick, left, right, duration, source, session)
