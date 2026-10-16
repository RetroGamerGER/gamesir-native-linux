# SPDX-License-Identifier: GPL-2.0-only
"""Independent decoders for documented packet layouts, operating on bytes only.

Sources and the limits of each layout are recorded in docs/PROTOCOL.md.
No third-party module, packet transmitter, unit conversion or sensor clock.
"""

from dataclasses import dataclass, field
import struct


@dataclass(frozen=True)
class Decoded:
    disposition: str
    kind: str
    fields: dict = field(default_factory=dict)
    reason: str | None = None


def _bad(kind: str, reason: str) -> Decoded:
    return Decoded("malformed", kind, reason=reason)


def _bits(value: int, names: dict) -> dict:
    return {name: bool(value & mask) for name, mask in names.items()}


def _sticks(data: bytes, offset: int) -> dict:
    return dict(zip(("lx", "ly", "rx", "ry"), struct.unpack_from("<4h", data, offset)))


def _x360(data: bytes) -> Decoded:
    if len(data) != 20 or data[1] != 0x14:
        return _bad("x360_input", "expected_20_bytes_and_00_14_header")
    buttons = _bits(data[2], {
        "up": 1, "down": 2, "left": 4, "right": 8, "menu": 16,
        "view": 32, "ls": 64, "rs": 128,
    })
    buttons.update(_bits(data[3], {
        "lb": 1, "rb": 2, "home": 4, "a": 16, "b": 32, "x": 64, "y": 128,
    }))
    raw = _sticks(data, 6)
    linux_axes = dict(raw)
    linux_axes["ly"], linux_axes["ry"] = ~raw["ly"], ~raw["ry"]
    return Decoded("decoded", "x360_input", {
        "buttons": buttons, "sticks_raw_i16": raw,
        "sticks_xpad_default_axes": linux_axes,
        "triggers_u8": {"lt": data[4], "rt": data[5]},
        "reserved_button_bit_3": bool(data[3] & 8),
        "undecoded_tail_hex": data[14:].hex(),
    })


def _telemetry(data: bytes) -> Decoded:
    # Fields through byte 60 must be present. A capture truncated from 64 bytes
    # is rejected by the record layer even if these fields happen to be present.
    if len(data) < 61:
        return _bad("gamesir_telemetry", "needs_bytes_0_through_60")
    extras = _bits(data[57], {"home": 1, "share": 2, "l4": 8, "r4": 16, "m": 32})
    extras.update(_bits(data[58], {"l5": 1, "r5": 2}))
    return Decoded("decoded", "gamesir_telemetry", {
        "header_byte_1": data[1], "header_byte_2": data[2],
        "gyro_raw_i16": list(struct.unpack_from("<3h", data, 17)),
        "accel_raw_i16": list(struct.unpack_from("<3h", data, 23)),
        "sensor_units": "raw_counts; scale_and_orientation_unverified",
        "device_timestamp": None,
        "sticks_processed_u8": list(data[5:9]),
        "sticks_raw_u8": list(data[51:55]),
        "processed_buttons_hex": data[9:11].hex(),
        "raw_buttons_hex": data[55:57].hex(),
        "extra_buttons": extras,
        "unknown_extra_bits_hex": bytes((data[57] & ~0x3B, data[58] & ~3)).hex(),
        "triggers_processed_u8": {"lt": data[12], "rt": data[13]},
        "raw_trigger_bytes_59_60": list(data[59:61]),
        "battery_percent_raw": data[33],
        "charging_flag_raw": data[32],
        "undecoded_padding_hex": data[61:].hex(),
    })


def _vendor_input(data: bytes) -> Decoded:
    if len(data) < 5:
        return _bad("gamesir_vendor_input", "needs_5_byte_discriminator")
    if data[3] != 0x3C:
        return Decoded("unknown", "gamesir_vendor_unknown", reason="unrecognized_byte_3")
    marker = data[4]
    if marker == 0xE0:
        return _telemetry(data)
    if marker == 0x05:
        if len(data) < 9:
            return _bad("gamesir_read_reply", "needs_9_byte_read_header")
        size = data[8]
        if size > 55 or len(data) < 9 + size:
            return _bad("gamesir_read_reply", "invalid_or_missing_declared_payload")
        return Decoded("decoded", "gamesir_read_reply", {
            "category": data[5], "offset": int.from_bytes(data[6:8], "big"),
            "length": size, "payload_hex": data[9:9 + size].hex(),
            "trailing_bytes_hex": data[9 + size:].hex(),
        })
    if marker == 0x0A:
        payload = data[5:]
        end = next((i for i in range(0, len(payload) - 1, 2)
                    if payload[i:i + 2] == b"\x00\x00"), None)
        if end is None:
            return _bad("gamesir_firmware_reply", "missing_utf16le_terminator")
        try:
            value = payload[:end].decode("utf-16-le", errors="strict")
        except UnicodeDecodeError:
            return _bad("gamesir_firmware_reply", "invalid_utf16le")
        return Decoded("decoded", "gamesir_firmware_reply", {
            "selector_echo": marker, "firmware_text": value,
            "four_character_groups": [value[i:i + 4] for i in range(0, len(value), 4)],
            "later_groups_meaning": "unknown; not assigned to dongle firmware",
        })
    if marker == 0x0C:
        if len(data) < 6 or not 1 <= data[5] <= 4:
            return _bad("gamesir_profile_reply", "profile_not_in_1_through_4")
        return Decoded("decoded", "gamesir_profile_reply", {"active_profile": data[5]})
    return Decoded("unknown", "gamesir_response_unknown", {
        "discriminator": marker, "payload_hex": data[5:].hex(),
    }, "unrecognized_response_discriminator")


def _gip_input(data: bytes) -> Decoded:
    if len(data) < 4:
        return _bad("gip_input_basic", "needs_4_byte_header")
    # This PoC supports only a basic, unchunked header with options 0.
    # Other GIP framing is preserved as unknown, never interpreted as basic input.
    if data[1] != 0 or data[3] & 0x80:
        return Decoded("unknown", "gip_input_unsupported", reason="unsupported_gip_header")
    if data[3] < 14 or len(data) != 4 + data[3]:
        return _bad("gip_input_basic", "payload_length_mismatch_or_below_14")
    return Decoded("decoded", "gip_input_basic", {
        "sequence_raw": data[2], "buttons_raw_hex": data[4:6].hex(),
        "triggers_raw_u16": dict(zip(("lt", "rt"), struct.unpack_from("<2H", data, 6))),
        "sticks_raw_i16": _sticks(data, 10),
        "undecoded_extension_hex": data[18:].hex(),
        "scope": "basic_GIP_layout_only; G7_Pro_RF_support_unverified",
    })


def _output(data: bytes) -> Decoded:
    if data[0] == 0x09:
        if len(data) != 13 or data[1] != 0 or data[3:6] != b"\x09\x00\x0f":
            return _bad("gip_four_motor_output", "expected_documented_13_byte_all_motor_layout")
        values = data[6:10]
        if any(value > 100 for value in values):
            return _bad("gip_four_motor_output", "motor_percentage_exceeds_100")
        return Decoded("decoded", "gip_four_motor_output", {
            "sequence_raw": data[2],
            "motor_percentages": dict(zip(("lt", "rt", "left_grip", "right_grip"), values)),
            "all_amplitudes_zero": not any(values),
            "duration_ticks_10ms": data[10], "pause_ticks_10ms": data[11],
            "repeat_count_raw": data[12],
            "scope": "decoded_file_bytes; no_command_sent_or_physical_motor_verified",
        })
    if data[0] == 0x0F:
        if len(data) != 64 or data[1] != 0:
            return _bad("gamesir_vendor_output", "expected_64_byte_0f_00_layout")
        return Decoded("decoded", "gamesir_vendor_output", {
            "sequence_raw": data[2], "command": data[3],
            "command_name": {1: "device_info", 2: "heartbeat", 5: "config_read", 60: "config_write"}.get(data[3], "unknown"),
            "payload_hex": data[4:].hex(),
        })
    if data[0] == 0:
        if len(data) != 8 or data[1] != 8:
            return _bad("x360_rumble_output", "expected_8_byte_00_08_layout")
        return Decoded("decoded", "x360_rumble_output", {
            "left_grip_u8": data[3], "right_grip_u8": data[4],
            "undecoded_bytes_hex": bytes((data[2], *data[5:])).hex(),
        })
    return Decoded("unknown", "output_unknown", reason="unrecognized_output_report")


def decode_packet(data: bytes, *, endpoint: int = 0x82) -> Decoded:
    """Decode one complete transfer payload; never read or write a device."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if endpoint not in (0x82, 0x02):
        return Decoded("ignored", "unsupported_endpoint", reason="only_82_and_02_supported")
    if not data:
        return _bad("empty", "empty_payload")
    if len(data) > 64:
        return _bad("oversized", "layout_limit_64_bytes")
    if endpoint == 0x02:
        return _output(data)
    if data[0] == 0:
        return _x360(data)
    if data[0] == 0x10:
        return _vendor_input(data)
    if data[0] == 0x20:
        return _gip_input(data)
    return Decoded("unknown", "input_unknown", reason="unrecognized_input_report")
