# SPDX-License-Identifier: GPL-2.0-only
"""Independent constructed packets, measured event times and negative cases."""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from gamesir_offline.cli import main
from gamesir_offline.records import Record
from gamesir_offline.startup_timeline import InstanceTimeline, analyze_startup, classify_record


ROOT = Path(__file__).resolve().parents[1]


def packet(kind, at=1000):
    # All bytes here are constructed; no captured unique device ID is included.
    payload = {
        "hello": bytes.fromhex("0220011c") + bytes(8) + bytes.fromhex("37359c10") + bytes(16),
        "status": bytes.fromhex("0320010487000000"),
        "start": bytes.fromhex("0520010100"),
        "pad": bytes.fromhex("20000120") + bytes(32),
        "imu": bytes.fromhex("1000013ce0") + bytes(59),
        "unknown": b"\xff\x00",
    }[kind]
    return Record("synthetic", "constructed-startup", "boot-A-enumeration-A", at,
                  "synthetic", 0x3537, 0x109C, 1, 3, 0,
                  0x02 if kind == "start" else 0x82,
                  "submit" if kind == "start" else "complete",
                  -115 if kind == "start" else 0, len(payload), False, payload)


def instance(records, **kwargs):
    return analyze_startup(records, **kwargs)["instances"][0]


class TimelineTests(unittest.TestCase):
    def test_receiver_can_wait_a_day_without_error_candidate_or_command(self):
        model = InstanceTimeline()
        model.observe("attach", 0)
        result = model.observe("tick", 86_400_000_000)
        self.assertEqual(result["phase"], "waiting_receiver")
        self.assertIsNone(result["first_error"])
        self.assertNotIn("announce_start_candidates", result["counts"])

    def test_late_hello_does_not_need_gamepad_movement(self):
        model = InstanceTimeline()
        model.observe("attach", 0)
        model.observe("tick", 30_000_000)
        result = model.observe("hello", 60_000_000)
        self.assertEqual(result["phase"], "announced")
        self.assertEqual(result["counts"]["announce_start_candidates"], 1)
        self.assertFalse(result["rf_connected_proven"])

    def test_duplicate_hello_and_silence_never_replenish_start_candidate(self):
        model = InstanceTimeline()
        for t in (0, 500000, 1000000):
            model.observe("hello", t)
        model.observe("tick", 20_000_000)
        self.assertEqual(model.snapshot()["counts"]["announce_start_candidates"], 1)
        self.assertFalse(model.snapshot()["start_submission_seen"])

    def test_status_alone_neither_proves_connection_nor_proposes_start(self):
        result = instance([packet("status")])
        self.assertEqual(result["phase"], "waiting_receiver")
        self.assertEqual(result["status_bit_candidate"], "positive")
        self.assertNotIn("announce_start_candidates", result["counts"])
        self.assertFalse(result["runtime_ready_proven"])

    def test_start_before_status_is_observed_without_circular_gate(self):
        result = instance([packet("start"), packet("status", 2000)])
        self.assertTrue(result["start_submission_seen"])
        self.assertEqual(result["phase"], "waiting_after_start")
        self.assertFalse(result["runtime_ready_proven"])

    def test_missing_imu_does_not_erase_pad_or_trigger_retry(self):
        result = instance([packet("start"), packet("pad", 10000000)])
        self.assertEqual(result["phase"], "pad_only_observed")
        self.assertFalse(result["imu_fresh_under_replay_policy"])
        self.assertIsNone(result["first_error"])
        self.assertNotIn("announce_start_candidates", result["counts"])

    def test_both_streams_are_observations_not_proven_runtime(self):
        result = instance([packet("hello"), packet("start", 2000),
                           packet("pad", 3000), packet("imu", 800000)])
        self.assertEqual(result["phase"], "pad_and_imu_observed")
        self.assertFalse(result["runtime_ready_proven"])

    def test_already_running_imu_before_pad_needs_no_announce(self):
        result = instance([packet("imu"), packet("pad", 2000)])
        self.assertEqual(result["phase"], "pad_and_imu_observed")
        self.assertFalse(result["hello_seen"])
        self.assertFalse(result["start_submission_seen"])
        self.assertNotIn("announce_start_candidates", result["counts"])

    def test_expiry_is_separate_for_each_stream_and_never_rf_off(self):
        model = InstanceTimeline(freshness_us=100)
        model.observe("imu", 0)
        model.observe("pad", 100)
        self.assertEqual(model.snapshot()["phase"], "pad_and_imu_observed")
        self.assertEqual(model.observe("tick", 101)["phase"], "pad_only_observed")
        self.assertEqual(model.observe("tick", 201)["phase"], "waiting_receiver")
        self.assertIsNone(model.snapshot()["first_error"])
        self.assertTrue(model.candidate_consumed)

    def test_reannounce_after_data_is_quarantined_no_restart_or_adoption(self):
        result = instance([packet("pad"), packet("hello", 2000),
                           packet("start", 3000), packet("imu", 4000), packet("pad", 5000)])
        self.assertEqual(result["phase"], "link_uncertain")
        self.assertFalse(result["pad_fresh_under_replay_policy"])
        self.assertNotIn("announce_start_candidates", result["counts"])

    def test_negative_bit_is_uncertainty_not_a_claim_of_disconnection(self):
        status = replace(packet("status", 2000), payload=bytes.fromhex("0320010407000000"))
        result = instance([packet("pad"), status, packet("imu", 3000)])
        self.assertEqual(result["phase"], "link_uncertain")
        self.assertEqual(result["status_bit_candidate"], "negative")
        self.assertFalse(result["rf_connected_proven"])

    def test_terminal_error_is_preserved_and_later_data_cannot_revive(self):
        model = InstanceTimeline()
        model.observe("fault", 100, reason="initial_protocol_fault")
        model.observe("fault", 200, reason="later_cleanup_timeout")
        model.observe("detach", 300)
        model.observe("hello", 400)
        model.observe("imu", 500)
        self.assertEqual(model.snapshot()["phase"], "blocked")
        self.assertEqual(model.snapshot()["first_error"]["reason"], "initial_protocol_fault")

    def test_detach_and_cancel_are_terminal_even_if_same_epoch_reappears(self):
        for terminal in ("detach", "cancel"):
            model = InstanceTimeline()
            model.observe("pad", 0)
            model.observe(terminal, 1)
            result = model.observe("imu", 2)
            self.assertEqual(result["phase"], terminal)
            self.assertFalse(result["pad_fresh_under_replay_policy"])

    def test_clock_regression_is_not_sorted_away(self):
        report = analyze_startup([packet("pad", 2000), packet("imu", 1000), packet("pad", 3000)],
                                 include_events=True)
        self.assertEqual(report["instances"][0]["phase"], "blocked")
        self.assertEqual(report["instances"][0]["first_error"]["reason"], "host_clock_regression")
        self.assertEqual([e["timestamp_us"] for e in report["events"]], [2000, 1000, 3000])

    def test_same_instance_in_out_join_but_each_provenance_boundary_separates(self):
        self.assertTrue(instance([packet("start"), packet("pad", 2000)])["start_submission_seen"])
        for change in ({"source_id": "other"}, {"session": "boot-B-enumeration-B"},
                       {"source_kind": "capture_excerpt", "timebase": "host_capture"},
                       {"bus": 2}, {"address": 4}):
            with self.subTest(change=change):
                report = analyze_startup([packet("pad"), replace(packet("imu", 2000), **change)])
                self.assertEqual(len(report["instances"]), 2)
                self.assertTrue(all(i["phase"] != "pad_and_imu_observed" for i in report["instances"]))

    def test_foreign_packets_and_hid_returns_cannot_supply_link_evidence(self):
        for change in ({"pid": 0x100A}, {"pid": 0x105E}, {"vid": 0x045E},
                       {"interface": 1}, {"endpoint": 0x84}):
            with self.subTest(change=change):
                report = analyze_startup([replace(packet("imu"), **change)])
                self.assertEqual(report["instances"], [])

    def test_complete_success_and_full_payload_required(self):
        for change in ({"stage": "submit"}, {"capture_truncated": True},
                       {"reported_length": 65}, {"reported_length": 63}):
            with self.subTest(change=change):
                report = analyze_startup([replace(packet("imu"), **change)])
                self.assertFalse(any(i["imu_fresh_under_replay_policy"] for i in report["instances"]))

    def test_transport_error_retains_original_status(self):
        result = instance([replace(packet("imu"), status=-71), packet("pad", 2000)])
        self.assertEqual(result["phase"], "blocked")
        self.assertEqual(result["first_error"]["reason"], "usb_complete_status_-71")

    def test_hello_requires_correct_layout_and_embedded_identity(self):
        hello = packet("hello")
        for data in (hello.payload[:-1], b"\x02\x00" + hello.payload[2:],
                     hello.payload[:3] + b"\x1b" + hello.payload[4:],
                     hello.payload[:12] + bytes(4) + hello.payload[16:]):
            with self.subTest(data=data):
                result = classify_record(replace(hello, payload=data, reported_length=len(data)))
                self.assertEqual(result[0], "malformed")

    def test_status_and_sensor_lengths_are_not_inferred_from_opcode_alone(self):
        for kind in ("status", "imu", "pad"):
            record = packet(kind)
            bad = replace(record, payload=record.payload[:-1], reported_length=len(record.payload)-1)
            self.assertNotIn(classify_record(bad)[0], ("status_positive", "imu", "pad"))

    def test_start_completion_is_not_counted_again_or_treated_as_ack(self):
        start = packet("start")
        result = instance([start, replace(start, timestamp_us=2000, stage="complete", status=0)])
        self.assertEqual(result["counts"]["start_submit"], 1)
        self.assertFalse(result["runtime_ready_proven"])

    def test_empty_and_filtered_inputs_do_not_manufacture_devices(self):
        self.assertEqual(analyze_startup([])["instances"], [])
        self.assertEqual(analyze_startup([packet("pad")], address=4)["instances"], [])

    def test_output_does_not_expose_hello_unique_id_or_input_payloads(self):
        hello = packet("hello")
        private = bytes.fromhex("a1b2c3d4e5f60708")
        hello = replace(hello, payload=hello.payload[:4] + private + hello.payload[12:])
        report = analyze_startup([hello, packet("imu", 2000)], include_events=True)
        self.assertNotIn(private.hex(), json.dumps(report))
        self.assertNotIn("data_hex", json.dumps(report))
        self.assertEqual(report["commands_sent"], 0)

    def test_invalid_policy_and_event_inputs_are_rejected(self):
        for value in (0, -1, True, 1.5, 60000001):
            with self.assertRaises(ValueError):
                analyze_startup([], freshness_us=value)
        for kind, at in (("send_start", 0), ("tick", -1), ("tick", True)):
            with self.assertRaises(ValueError):
                InstanceTimeline().observe(kind, at)

    def test_measured_metadata_timelines_replay_without_invented_order(self):
        fixture = json.loads((ROOT / "fixtures/startup_chronology.json").read_text())
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                model = InstanceTimeline()
                kinds = []
                for event in case["events"]:
                    model.observe(event["kind"], event["relative_us"])
                    kinds.append(event["kind"])
                self.assertEqual(model.snapshot()["phase"], case["expected_final_phase"])
                self.assertEqual(model.snapshot()["counts"].get("announce_start_candidates", 0),
                                 case["expected_start_candidates"])
                if case["id"] == "D":
                    self.assertEqual(case["events"][2]["relative_us"] -
                                     case["events"][1]["relative_us"], 45)
                if case["id"] == "already-streaming":
                    self.assertEqual(kinds[0], "imu")
                    self.assertNotIn("hello", kinds)

    def test_cli_uses_regular_file_guard_and_strict_malformed_exit(self):
        for path in ("/dev/null", "/proc/self/status", "/sys/kernel/uevent_seqnum"):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["startup-replay", path]), 2)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.jsonl"
            record = packet("hello")
            obj = record.metadata()
            obj.update(schema_version=1, timestamp_us=1000, stage="complete", status=0,
                       reported_length=1, capture_truncated=False, data_hex="02")
            path.write_text(json.dumps(obj) + "\n")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["startup-replay", str(path), "--strict"]), 1)
            self.assertEqual(json.loads(output.getvalue())["counts"]["malformed"], 1)

    def test_cli_synthetic_example_is_successful_and_explicitly_not_hardware(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["startup-replay", str(ROOT / "fixtures/synthetic_startup.jsonl"),
                         "--events", "--strict"])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["instances"][0]["phase"], "pad_and_imu_observed")
        self.assertEqual(report["instances"][0]["identity"]["source"]["kind"], "synthetic")
        self.assertFalse(report["ownership_or_recovery_proven"])

    def test_cli_strict_faults_fail_but_waiting_status_does_not(self):
        for status, expected in ((0, 0), (-71, 1)):
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "one.jsonl"
                obj = packet("status").metadata()
                obj.update(schema_version=1, timestamp_us=1000, stage="complete", status=status,
                           reported_length=8, capture_truncated=False, data_hex="0320010487000000")
                path.write_text(json.dumps(obj)+'\n')
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["startup-replay", str(path), "--strict"]), expected)

    def test_clock_error_stays_local_to_its_epoch(self):
        report = analyze_startup([packet("pad", 2000), packet("imu", 1000),
                                  replace(packet("pad", 3000), session="new-epoch"),
                                  replace(packet("imu", 4000), session="new-epoch")])
        self.assertEqual([i["phase"] for i in report["instances"]],
                         ["blocked", "pad_and_imu_observed"])

    def test_observed_repeated_starts_do_not_become_generated_retries(self):
        report = analyze_startup([packet("hello"), packet("start", 2000),
                                  packet("start", 3000), packet("status", 20_000_000)])
        self.assertEqual(report["instances"][0]["counts"]["start_submit"], 2)
        self.assertEqual(report["instances"][0]["counts"]["announce_start_candidates"], 1)
        self.assertEqual(report["commands_sent"], 0)


if __name__ == "__main__":
    unittest.main()
