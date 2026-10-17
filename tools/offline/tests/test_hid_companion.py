# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic protocol/state regressions; no device, packet sender or uinput."""

from dataclasses import replace
import json
import struct
import unittest
from unittest.mock import patch

from gamesir_offline.hid_companion import analyze_hid_companion
from gamesir_offline.records import Record
from gamesir_offline.replay import decode_record


def normal(timestamp=1000):
    # Constructed independently: lx=12345, ly=-32768, rx=1, ry=32767.
    data = bytes.fromhex("00142111017f393000800100ff7f000000000000")
    return Record("synthetic", "constructed-companion-test", "epoch-A", timestamp,
                  "synthetic", 0x3537, 0x100A, 8, 12, 0, 0x82,
                  "complete", 0, len(data), False, data)


def hid(timestamp=1100):
    data = bytearray(64)
    data[:5] = b"\x10\x00\x01\x3c\xe0"
    struct.pack_into("<3h", data, 17, -32768, -1, 32767)
    struct.pack_into("<3h", data, 23, 8192, -8192, 0)
    data[5:9] = b"\x01\x02\x03\x04"
    data[57], data[58] = 0x18, 0x03
    return replace(normal(timestamp), interface=1, endpoint=0x84,
                   reported_length=64, payload=bytes(data))


def recorded_candidate(timestamp=1050):
    # Synthetic matching saved bytes only; not a command builder or sender.
    return replace(hid(timestamp), endpoint=0x04, payload=b"\x0f\xf2" + bytes(62))


class HidCompanionTests(unittest.TestCase):
    def test_normal_16bit_input_is_not_replaced_by_vendor_8bit_fields(self):
        report = analyze_hid_companion([normal(), hid()], include_events=True)
        snapshot = report["instances"][0]["latest_observation"]
        self.assertEqual(snapshot["normal"]["fields"]["sticks_raw_i16"],
                         {"lx": 12345, "ly": -32768, "rx": 1, "ry": 32767})
        self.assertEqual(snapshot["raw_hid"]["fields"]["sticks_processed_u8"], [1, 2, 3, 4])
        self.assertEqual(snapshot["normal"]["fields"]["triggers_u8"], {"lt": 1, "rt": 127})
        self.assertTrue(snapshot["same_instance_samples_present"])
        self.assertEqual(snapshot["normal"]["timestamp_us"], 1000)
        self.assertEqual(snapshot["raw_hid"]["timestamp_us"], 1100)
        self.assertEqual(report["counts"], {"records_total": 2, "decoded": 2})

    def test_sensors_and_extras_are_raw_tentative_fields(self):
        report = analyze_hid_companion([hid()])
        fields = report["instances"][0]["latest_observation"]["raw_hid"]["fields"]
        self.assertEqual(fields["gyro_raw_i16"], [-32768, -1, 32767])
        self.assertEqual(fields["accel_raw_i16"], [8192, -8192, 0])
        self.assertIsNone(fields["device_timestamp"])
        self.assertFalse(fields["paddle_layout_100a_verified"])
        self.assertTrue(all(fields["extra_buttons"][key] for key in ("l4", "r4", "l5", "r5")))
        self.assertNotIn("buttons", fields)

    def test_foreign_identity_never_becomes_a_companion_instance(self):
        records = [normal(), replace(hid(), pid=0x109C), replace(hid(), pid=0x10C5),
                   replace(hid(), vid=0x045E)]
        report = analyze_hid_companion(records)
        self.assertEqual(len(report["instances"]), 1)
        self.assertEqual(report["counts"], {"records_total": 4, "decoded": 1, "ignored": 3})
        self.assertIsNone(report["instances"][0]["latest_observation"]["raw_hid"])

    def test_cross_interface_endpoint_mismatch_is_not_accepted(self):
        report = analyze_hid_companion([replace(hid(), interface=0),
                                        replace(hid(), endpoint=0x82),
                                        replace(hid(), endpoint=0x04, interface=0)])
        self.assertEqual(report["packet_kinds"], {"unsupported_channel": 3})
        self.assertEqual(report["instances"], [])

    def test_report12_remains_unknown_even_with_apparent_8k_extra_bits(self):
        payload = bytearray(hid().payload)
        payload[0], payload[60], payload[63] = 0x12, 0xFF, 0xFF
        report = analyze_hid_companion([replace(hid(), payload=bytes(payload))], include_events=True)
        self.assertEqual(report["packet_kinds"], {"hid_report_12_unknown": 1})
        self.assertEqual(report["events"][0]["fields"], {})
        self.assertIsNone(report["instances"][0]["latest_observation"]["raw_hid"])

    def test_hid_report10_needs_exact_length_and_signature(self):
        records = [replace(hid(), payload=hid().payload[:61], reported_length=61),
                   replace(hid(), payload=hid().payload[:3] + b"\x99" + hid().payload[4:])]
        report = analyze_hid_companion(records)
        self.assertEqual(report["counts"], {"records_total": 2, "malformed": 1, "unknown": 1})
        self.assertFalse(report["instances"][0]["channel_cadence"])

    def test_keyboard_mouse_consumer_and_null_are_not_gamepad_buttons(self):
        records = [replace(hid(), payload=bytes((first,)) + bytes(12), reported_length=13)
                   for first in (0x03, 0x09, 0x02, 0)]
        report = analyze_hid_companion(records, include_events=True)
        self.assertEqual(report["packet_kinds"], {"hid_nonvendor_ignored": 4})
        self.assertTrue(all(event["fields"] == {} for event in report["events"]))
        self.assertTrue(all(event["payload_redacted"] for event in report["events"]))
        self.assertTrue(all(event["data_hex"] is None for event in report["events"]))

    def test_failed_nonvendor_and_unrelated_payloads_are_redacted(self):
        private_payload = b"\x03" + bytes.fromhex("abcdef102030405060708090")
        keyboard = replace(hid(), payload=private_payload, reported_length=13)
        records = [replace(keyboard, capture_truncated=True),
                   replace(keyboard, status=-32), replace(keyboard, stage="submit"),
                   replace(hid(), vid=0x045E), replace(hid(), pid=0x109C),
                   replace(hid(), interface=0)]
        report = analyze_hid_companion(records, include_events=True)
        self.assertTrue(all(event["payload_redacted"] for event in report["events"]))
        self.assertTrue(all(event["data_hex"] is None for event in report["events"]))
        self.assertNotIn(private_payload.hex(), json.dumps(report))

    def test_target_protocol_payloads_are_preserved_in_explicit_events(self):
        report12 = replace(hid(1200), payload=b"\x12" + hid().payload[1:])
        report = analyze_hid_companion([normal(), hid(), report12], include_events=True)
        self.assertTrue(all(not event["payload_redacted"] for event in report["events"]))
        self.assertEqual([event["data_hex"] for event in report["events"]],
                         [normal().payload.hex(), hid().payload.hex(), report12.payload.hex()])

    def test_each_provenance_epoch_and_address_boundary_prevents_pairing(self):
        changes = [{"source_id": "another-file"}, {"session": "epoch-B"},
                   {"source_kind": "capture", "timebase": "host_capture"},
                   {"bus": 9}, {"address": 13}]
        for change in changes:
            with self.subTest(change=change):
                report = analyze_hid_companion([normal(), replace(hid(), **change)])
                self.assertEqual(len(report["instances"]), 2)
                self.assertTrue(all(not item["latest_observation"]["same_instance_samples_present"]
                                    for item in report["instances"]))

    def test_transfers_missing_success_or_full_bytes_do_not_supply_sensor_state(self):
        records = [replace(hid(), stage="submit", status=-115),
                   replace(hid(), status=-32), replace(hid(), stage="error", status=-71),
                   replace(hid(), capture_truncated=True),
                   replace(hid(), payload=hid().payload[:61]),
                   replace(hid(), reported_length=63)]
        report = analyze_hid_companion(records)
        self.assertEqual(report["counts"], {"records_total": 6, "ignored": 3,
                                            "truncated": 2, "malformed": 1})
        self.assertFalse(report["instances"][0]["channel_cadence"])
        self.assertIsNone(report["instances"][0]["latest_observation"]["raw_hid"])

    def test_submit_does_not_clear_completed_normal_or_hid_observation(self):
        records = [normal(), hid(), replace(normal(1200), stage="submit", status=-115),
                   replace(hid(1300), stage="submit", status=-115)]
        snapshot = analyze_hid_companion(records)["instances"][0]["latest_observation"]
        self.assertTrue(snapshot["same_instance_samples_present"])
        self.assertEqual(snapshot["normal"]["timestamp_us"], 1000)
        self.assertEqual(snapshot["raw_hid"]["timestamp_us"], 1100)

    def test_actual_channel_error_clears_only_its_observation(self):
        records = [normal(), hid(), replace(hid(1200), status=-32)]
        snapshot = analyze_hid_companion(records)["instances"][0]["latest_observation"]
        self.assertIsNone(snapshot["raw_hid"])
        self.assertIsNotNone(snapshot["normal"])

    def test_old_sensor_sample_expires_under_explicit_display_age_policy(self):
        report = analyze_hid_companion([hid(1000), normal(101001)])
        snapshot = report["instances"][0]["latest_observation"]
        self.assertEqual(snapshot["stale_channels"], ["raw_hid"])
        self.assertEqual(snapshot["age_us"]["raw_hid"], 100001)
        self.assertIsNone(snapshot["raw_hid"])
        self.assertIsNotNone(snapshot["normal"])
        self.assertFalse(snapshot["same_instance_samples_present"])
        self.assertFalse(snapshot["freshness_proven"])

    def test_display_policy_boundary_and_explicit_override(self):
        for ceiling in (0, 100000, 200000):
            records = [hid(1000), normal(1000 + ceiling)]
            snapshot = analyze_hid_companion(records, max_observation_age_us=ceiling)["instances"][0]["latest_observation"]
            self.assertTrue(snapshot["same_instance_samples_present"])
        for bad in (-1, True, 1.5, None, 1000001):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                analyze_hid_companion([], max_observation_age_us=bad)

    def test_clock_regression_quarantines_without_sorting_or_recovery_promotion(self):
        records = [normal(1000), hid(2000), normal(1500), hid(3000), normal(4000)]
        report = analyze_hid_companion(records, include_events=True)
        instance = report["instances"][0]
        self.assertEqual(instance["clock_regressions"], 1)
        self.assertTrue(instance["chronology_quarantined"])
        self.assertIsNone(instance["latest_observation"]["normal"])
        self.assertIsNone(instance["latest_observation"]["raw_hid"])
        self.assertEqual([event["timestamp_us"] for event in report["events"]],
                         [1000, 2000, 1500, 3000, 4000])

    def test_regression_on_one_instance_does_not_poison_another(self):
        records = [normal(1000), hid(500), replace(normal(2000), address=13),
                   replace(hid(2100), address=13)]
        instances = analyze_hid_companion(records)["instances"]
        self.assertTrue(instances[0]["chronology_quarantined"])
        self.assertFalse(instances[1]["chronology_quarantined"])
        self.assertTrue(instances[1]["latest_observation"]["same_instance_samples_present"])

    def test_heartbeat_shape_classification_never_claims_activation_or_output_support(self):
        report = analyze_hid_companion([normal(), recorded_candidate(), hid()], include_events=True)
        self.assertEqual(report["counts"]["heartbeat_candidate_successful_completions"], 1)
        candidate = report["events"][1]
        self.assertEqual(candidate["disposition"], "candidate")
        self.assertTrue(candidate["fields"]["successful_transport_completion"])
        self.assertFalse(candidate["fields"]["activation_proven"])
        self.assertFalse(report["activation_proven"])
        self.assertFalse(report["motor_support_proven"])

    def test_candidate_submissions_errors_truncations_never_become_success(self):
        records = [replace(recorded_candidate(), stage="submit", status=-115),
                   replace(recorded_candidate(), status=-32),
                   replace(recorded_candidate(), capture_truncated=True)]
        report = analyze_hid_companion(records, include_events=True)
        self.assertEqual(report["counts"]["heartbeat_candidate_submissions"], 1)
        self.assertEqual(report["counts"]["heartbeat_candidate_unproven_transfers"], 2)
        self.assertNotIn("heartbeat_candidate_successful_completions", report["counts"])
        self.assertTrue(all(event["disposition"] != "candidate" for event in report["events"]))

    def test_short_shape_other_endpoint_and_extended_heartbeat_are_not_8k_candidate(self):
        records = [replace(recorded_candidate(), payload=b"\x0f\xf2", reported_length=2),
                   replace(recorded_candidate(), interface=0, endpoint=0x02),
                   replace(recorded_candidate(), payload=b"\x0f\x00\x01\x02\xf2" + bytes(59))]
        report = analyze_hid_companion(records, include_events=True)
        self.assertTrue(all(not event["heartbeat_candidate_shape"] for event in report["events"]))
        self.assertFalse(any(key.startswith("heartbeat_candidate_") for key in report["counts"]))

    def test_candidate_requires_zero_padding_not_just_prefix(self):
        payload = b"\x0f\xf2" + bytes(61) + b"\x01"
        report = analyze_hid_companion([replace(recorded_candidate(), payload=payload)],
                                       include_events=True)
        self.assertEqual(report["packet_kinds"], {"hid_output_unknown": 1})
        self.assertFalse(report["events"][0]["heartbeat_candidate_shape"])
        self.assertFalse(any(key.startswith("heartbeat_candidate_") for key in report["counts"]))

    def test_filters_do_not_override_supported_identity(self):
        report = analyze_hid_companion([normal(), hid(), replace(hid(), pid=0x109C)], pid=0x109C)
        self.assertEqual(report["counts"], {"records_total": 3, "filtered": 2, "ignored": 1})
        self.assertEqual(report["instances"], [])
        self.assertEqual(analyze_hid_companion([normal()], bus=9)["counts"]["filtered"], 1)
        self.assertEqual(analyze_hid_companion([normal()], address=13)["counts"]["filtered"], 1)

    def test_old_replay_transport_gate_is_unchanged(self):
        self.assertEqual(decode_record(hid()).disposition, "ignored")
        self.assertEqual(decode_record(hid()).kind, "unsupported_interface")

    def test_plain_json_output_and_no_implicit_file_access(self):
        with patch("builtins.open", side_effect=AssertionError("unexpected file access")):
            report = analyze_hid_companion(iter([normal(), hid()]))
        self.assertNotIn("events", report)
        json.dumps(report)
        for name in ("hardware_access", "readiness_proven", "activation_proven",
                     "continuous_stream_proven", "paddle_layout_100a_verified"):
            self.assertFalse(report[name])


if __name__ == "__main__":
    unittest.main()
