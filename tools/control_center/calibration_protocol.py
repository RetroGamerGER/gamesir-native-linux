# SPDX-License-Identifier: GPL-2.0-only
"""Pure calibration message/telemetry codecs. No USB frame builder or I/O.

Provider payloads are source-backed internal GIP contents, NOT complete USB
packets. Position mapping is an explicit candidate policy, not calibration math.
See docs/CONTROL_CENTER_CALIBRATION_ADAPTER.md for provenance and open boundaries.
"""
from dataclasses import dataclass


class InvalidTelemetry(ValueError):
    pass


@dataclass(frozen=True)
class ProviderMessage:
    message_type: int
    payload: bytes


def calibration_message(operation):
    """Closed set of internal provider messages; never add header/sequence/padding."""
    payloads = {'Start': b'\xfe\x00\x03', 'Finish': b'\xfe\x01\x00',
                'Exit': b'\xfe\x02\x00'}
    if type(operation) is not str or operation not in payloads:
        raise ValueError('Unknown calibration operation')
    return ProviderMessage(0x0f, payloads[operation])


@dataclass(frozen=True)
class Telemetry:
    processed: tuple[int, int, int, int]
    raw: tuple[int, int, int, int]
    active: int
    done: int
    wire_sequence: int  # An opaque wrapping byte, NOT a host monotonic counter.


def decode_telemetry(report):
    """Strict existing full E0 report, plus the statically traced status bytes."""
    if (type(report) is not bytes or len(report) != 64 or report[0] != 0x10
            or report[1] != 0 or report[3:5] != b'\x3c\xe0'):
        raise InvalidTelemetry('Unsupported or incomplete telemetry layout')
    if report[30] & ~3 or report[31] & ~3:
        # Do not silently adopt trigger/motion calibration or unknown flag bits.
        raise InvalidTelemetry('Non-stick calibration fields present')
    return Telemetry(tuple(report[5:9]), tuple(report[51:55]),
                     report[30], report[31], report[2])


@dataclass(frozen=True)
class PositionPolicy:
    source: str
    signs: tuple[int, int, int, int]

    def __post_init__(self):
        if (self.source not in ('processed', 'raw') or type(self.signs) is not tuple
                or len(self.signs) != 4
                or any(type(v) is not int or v not in (-1, 1) for v in self.signs)):
            raise ValueError('An explicit position source and four axis signs are required')

    def positions(self, telemetry):
        values = telemetry.processed if self.source == 'processed' else telemetry.raw
        # Piecewise endpoint normalization only: 0 -> -1, 128 -> 0, 255 -> +1.
        # No deadzone, bias estimate, calibration record or device-setting write.
        axes = tuple(sign * (v-128) / (128 if v < 128 else 127)
                     for v, sign in zip(values, self.signs))
        return axes[:2], axes[2:]
