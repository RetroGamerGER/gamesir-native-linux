# SPDX-License-Identifier: GPL-2.0-only
import json
from pathlib import Path
import random
import unittest

from gamesir_offline.protocol import decode_packet
from gamesir_offline.records import read_records
from gamesir_offline.replay import decode_record


ROOT = Path(__file__).resolve().parents[1]


def telemetry():
    return bytearray.fromhex("1000013ce0" + "00" * 59)


class PacketTests(unittest.TestCase):
    def test_independent_fixture_expectations(self):
        manifest = json.loads((ROOT / "fixtures/expected.json").read_text())
        for name in ("valid", "negative"):
            records = list(read_records(ROOT / f"fixtures/synthetic_{name}.jsonl"))
            self.assertEqual(len(records), len(manifest[name]))
            for record, case in zip(records, manifest[name]):
                with self.subTest(case=case["case"]):
                    result = decode_record(record)
                    self.assertEqual((result.disposition, result.kind), (case["disposition"], case["kind"]))
                    for key, expected in case["expected_fields"].items():
                        self.assertEqual(result.fields[key], expected)

    def test_x360_signed_values_and_xpad_y_extremes(self):
        packet = bytes.fromhex("0014ff17ff00" "0080ff7fff7f0080" "000000000000")
        result = decode_packet(packet)
        self.assertEqual(result.fields["sticks_raw_i16"], {"lx": -32768, "ly": 32767, "rx": 32767, "ry": -32768})
        self.assertEqual(result.fields["sticks_xpad_default_axes"], {"lx": -32768, "ly": -32768, "rx": 32767, "ry": 32767})
        self.assertEqual(result.fields["triggers_u8"], {"lt": 255, "rt": 0})
        self.assertTrue(result.fields["buttons"]["a"])

    def test_telemetry_channel_order_sign_and_endianness(self):
        packet = telemetry()
        packet[17:29] = bytes.fromhex("0100ffff0080" "ff7f3412cced")
        result = decode_packet(bytes(packet))
        self.assertEqual(result.fields["gyro_raw_i16"], [1, -1, -32768])
        self.assertEqual(result.fields["accel_raw_i16"], [32767, 4660, -4660])
        self.assertIsNone(result.fields["device_timestamp"])

    def test_right_trigger_cannot_become_extra_buttons(self):
        for analog in (0, 1, 2, 8, 16, 32, 64, 128, 186, 255):
            packet = telemetry()
            packet[13] = packet[60] = analog
            result = decode_packet(bytes(packet))
            with self.subTest(analog=analog):
                self.assertFalse(any(result.fields["extra_buttons"].values()))

    def test_each_extra_button_is_independent(self):
        for byte, mask, name in ((57, 1, "home"), (57, 2, "share"), (57, 8, "l4"),
                                 (57, 16, "r4"), (57, 32, "m"), (58, 1, "l5"), (58, 2, "r5")):
            packet = telemetry()
            packet[byte] = mask
            result = decode_packet(bytes(packet))
            self.assertEqual([key for key, value in result.fields["extra_buttons"].items() if value], [name])

    def test_short_telemetry_never_decodes_partial_sensors(self):
        packet = bytes(telemetry())
        for length in range(61):
            with self.subTest(length=length):
                self.assertEqual(decode_packet(packet[:length]).disposition, "malformed")
        for length in (61, 62, 63, 64):
            self.assertEqual(decode_packet(packet[:length]).kind, "gamesir_telemetry")
            self.assertEqual(decode_packet(packet[:length]).disposition, "decoded")

    def test_x360_requires_canonical_length_and_header(self):
        packet = bytes.fromhex("0014" + "00" * 18)
        for length in range(20):
            self.assertEqual(decode_packet(packet[:length]).disposition, "malformed")
        self.assertEqual(decode_packet(packet + b"\x00").disposition, "malformed")
        self.assertEqual(decode_packet(b"\x00\x13" + packet[2:]).disposition, "malformed")

    def test_read_reply_offset_and_maximum_payload(self):
        packet = bytes.fromhex("1000003c0520abcd37") + bytes(range(55))
        result = decode_packet(packet)
        self.assertEqual(result.fields["offset"], 0xABCD)
        self.assertEqual(result.fields["payload_hex"], bytes(range(55)).hex())
        self.assertEqual(decode_packet(packet[:-1]).disposition, "malformed")

    def test_info_selector_echo_does_not_truncate_long_string(self):
        packet = b"\x10\x00\x00\x3c\x0a" + "02440152".encode("utf-16-le") + b"\x00\x00"
        result = decode_packet(packet)
        self.assertEqual(result.fields["firmware_text"], "02440152")
        self.assertEqual(result.fields["four_character_groups"], ["0244", "0152"])

    def test_firmware_malformed_utf16_and_missing_terminator(self):
        prefix = bytes.fromhex("1000003c0a")
        self.assertEqual(decode_packet(prefix + bytes.fromhex("00d80000")).disposition, "malformed")
        self.assertEqual(decode_packet(prefix + b"A\x00").disposition, "malformed")

    def test_unknown_vendor_discriminators_stay_unknown(self):
        self.assertEqual(decode_packet(bytes.fromhex("1000003c7f0102")).disposition, "unknown")
        self.assertEqual(decode_packet(bytes.fromhex("10000099e0") + bytes(59)).disposition, "unknown")
        self.assertEqual(decode_packet(b"\x12" + bytes(telemetry())[1:]).disposition, "unknown")

    def test_motor_order_and_all_zero_record(self):
        result = decode_packet(bytes.fromhex("09000109000f01020304280000"), endpoint=2)
        self.assertEqual(result.fields["motor_percentages"], {"lt": 1, "rt": 2, "left_grip": 3, "right_grip": 4})
        self.assertFalse(result.fields["all_amplitudes_zero"])
        result = decode_packet(bytes.fromhex("09000209000f00000000000000"), endpoint=2)
        self.assertTrue(result.fields["all_amplitudes_zero"])

    def test_input_and_output_are_not_interchangeable(self):
        packet = bytes.fromhex("09000109000f01020304280000")
        self.assertEqual(decode_packet(packet).disposition, "unknown")
        self.assertEqual(decode_packet(packet, endpoint=2).disposition, "decoded")

    def test_basic_gip_length_and_options_are_checked(self):
        packet = bytes.fromhex("2000010e") + bytes(14)
        self.assertEqual(decode_packet(packet).kind, "gip_input_basic")
        self.assertEqual(decode_packet(packet[:-1]).disposition, "malformed")
        self.assertEqual(decode_packet(b"\x20\x40" + packet[2:]).disposition, "unknown")
        self.assertEqual(decode_packet(b"\x20\x00\x01\x8e" + packet[4:]).disposition, "unknown")

    def test_deterministic_arbitrary_bytes_never_crash_decoder(self):
        rng = random.Random(0x3537100A)
        for first in (0, 0x10, 0x20, 9, 0x0F, 0x12, 0xFF):
            for length in range(81):
                for endpoint in (2, 0x82):
                    body = bytes((first,)) + rng.randbytes(max(0, length - 1)) if length else b""
                    result = decode_packet(body, endpoint=endpoint)
                    self.assertIn(result.disposition, ("decoded", "malformed", "unknown", "ignored"))


if __name__ == "__main__":
    unittest.main()
