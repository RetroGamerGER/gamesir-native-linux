# SPDX-License-Identifier: GPL-2.0-only
from dataclasses import replace
from pathlib import Path
import unittest

from gamesir_offline.records import read_records
from gamesir_offline.replay import analyze, decode_record, timing_summary


ROOT = Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def test_valid_fixture_counts_and_identity_separation(self):
        result = analyze(read_records(ROOT / "fixtures/synthetic_valid.jsonl"), include_events=True)
        self.assertEqual(result["counts"], {"records_total": 19, "decoded": 19})
        self.assertEqual(len(result["streams"]), 3)
        self.assertEqual({stream["device"]["pid"] for stream in result["streams"]}, {"100a", "109c"})
        self.assertFalse(result["hardware_feasibility_proven"])
        self.assertFalse(result["hardware_access"])

    def test_negative_fixture_error_counts(self):
        result = analyze(read_records(ROOT / "fixtures/synthetic_negative.jsonl"))
        self.assertEqual(result["counts"], {"records_total": 19, "malformed": 9,
                         "truncated": 2, "unknown": 3, "ignored": 5})
        self.assertTrue(all(not stream["cadence_by_packet_kind"] for stream in result["streams"]))

    def test_pid_filter_does_not_merge_other_identity(self):
        result = analyze(read_records(ROOT / "fixtures/synthetic_valid.jsonl"), pid=0x100A, bus=8, address=12)
        self.assertEqual(result["counts"], {"records_total": 19, "decoded": 17, "filtered": 2})
        self.assertEqual(len(result["streams"]), 2)

    def test_report_types_have_independent_timing(self):
        result = analyze(read_records(ROOT / "fixtures/synthetic_valid.jsonl"))
        stream = next(s for s in result["streams"] if s["device"]["pid"] == "100a" and s["endpoint"] == "82")
        x360 = stream["cadence_by_packet_kind"]["x360_input"]
        self.assertEqual(x360["statistics_us"]["median"], 1000)
        self.assertEqual(x360["observation_rate_hz"], 1000)
        self.assertEqual(x360["records"], 4)
        self.assertTrue(stream["normal_and_imu_records_in_same_stream"])
        self.assertFalse(result["hardware_feasibility_proven"])

    def test_sessions_sources_and_timebases_never_merge(self):
        first = next(read_records(ROOT / "fixtures/synthetic_valid.jsonl"))
        records = [first, replace(first, session="different"),
                   replace(first, source_id="different"),
                   replace(first, source_kind="capture", timebase="host_capture")]
        self.assertEqual(len(analyze(records)["streams"]), 4)

    def test_failed_or_incomplete_transfers_cannot_enter_cadence(self):
        first = next(read_records(ROOT / "fixtures/synthetic_valid.jsonl"))
        records = [first, replace(first, timestamp_us=1, stage="submit"),
                   replace(first, timestamp_us=2, status=-32),
                   replace(first, timestamp_us=3, capture_truncated=True)]
        stream = analyze(records)["streams"][0]
        self.assertEqual(stream["cadence_by_packet_kind"]["x360_input"]["records"], 1)

    def test_nonmonotonic_timestamps_are_not_silently_sorted(self):
        result = timing_summary([1000, 2000, 1500, 3000])
        self.assertEqual(result["clock_regressions"], 1)
        self.assertIsNone(result["statistics_us"])
        self.assertIsNone(result["observation_rate_hz"])

    def test_equal_timestamps_and_single_record(self):
        result = timing_summary([1000, 1000])
        self.assertEqual(result["zero_intervals"], 1)
        self.assertIsNone(result["observation_rate_hz"])
        self.assertIsNone(timing_summary([1000])["statistics_us"])
        self.assertEqual(timing_summary([])["records"], 0)

    def test_short_capture_does_not_decode_even_if_sensor_fields_fit(self):
        record = next(r for r in read_records(ROOT / "fixtures/synthetic_valid.jsonl") if r.payload[0] == 0x10)
        result = decode_record(replace(record, payload=record.payload[:61], reported_length=64))
        self.assertEqual(result.disposition, "truncated")
        self.assertFalse(result.fields)


if __name__ == "__main__":
    unittest.main()
