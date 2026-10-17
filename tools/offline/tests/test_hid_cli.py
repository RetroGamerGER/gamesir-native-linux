# SPDX-License-Identifier: GPL-2.0-only
"""File-only integration with small owned excerpts and independent test data."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from gamesir_offline.cli import main


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
EVIDENCE = ROOT.parents[1] / "docs/evidence/XPAD_HID_ACTIVATION_REVIEW_20261017.json"


def invoke(arguments):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


class HidCliTests(unittest.TestCase):
    def test_owned_fixture_preserves_exact_payload_hash_and_epoch_provenance(self):
        evidence = json.loads(EVIDENCE.read_text())
        path = FIXTURES / "captured_hid_returns.jsonl"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         evidence["fixture"]["sha256"])
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(rows), 17)
        self.assertEqual(len(evidence["coverage"]), 8)
        for origin in evidence["fixture"]["records_provenance"]:
            row = rows[origin["fixture_line"] - 1]
            self.assertEqual(row["source"]["id"], origin["source_id"])
            self.assertEqual(hashlib.sha256(bytes.fromhex(row["data_hex"])).hexdigest(),
                             origin["payload_sha256"])
            self.assertEqual(row["source"]["kind"], "capture_excerpt")
            self.assertEqual(row["timebase"], "host_capture")
            # Anonymized labels, never an inferred real port or identity.
            self.assertEqual((row["device"]["bus"], row["device"]["address"]), (1, 1))
            if row["endpoint"] == "04":
                self.assertEqual(row["stage"], "submit")
                self.assertEqual(row["data_hex"], "0301")
                self.assertEqual(origin["paired_completion_status"], 0)

    def test_real_reports_decode_separately_without_activation_or_normal_input_claim(self):
        code, output, error = invoke(["hid-replay", str(FIXTURES / "captured_hid_returns.jsonl"),
                                      "--events", "--strict"])
        self.assertEqual((code, error), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["counts"], {"records_total": 17, "decoded": 14, "ignored": 3})
        self.assertEqual(len(report["instances"]), 3)
        self.assertEqual([item["counts"]["decoded"] for item in report["instances"]], [1, 2, 11])
        for key in ("hardware_access", "activation_proven", "readiness_proven",
                    "continuous_stream_proven", "paddle_layout_100a_verified"):
            self.assertFalse(report[key])
        for item in report["instances"]:
            self.assertIsNone(item["latest_observation"]["normal"])
            self.assertFalse(item["latest_observation"]["same_instance_samples_present"])
        # Original second capture bytes encode gyro(-2,0,1), accel(-6,8220,46).
        fields = report["events"][2]["fields"]
        self.assertEqual(fields["gyro_raw_i16"], [-2, 0, 1])
        self.assertEqual(fields["accel_raw_i16"], [-6, 8220, 46])
        self.assertTrue(all(not any(event["fields"]["extra_buttons"].values())
                            for event in report["events"] if event["disposition"] == "decoded"))

    def test_synthetic_example_keeps_native_axes_and_expires_old_hid(self):
        code, output, error = invoke(["hid-replay", str(FIXTURES / "synthetic_hid_companion.jsonl"),
                                      "--events", "--strict"])
        self.assertEqual((code, error), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["packet_kinds"], {"x360_input": 2,
                         "hid_raw_telemetry_hypothesis": 2, "hid_report_12_unknown": 1})
        snapshot = report["instances"][0]["latest_observation"]
        self.assertEqual(snapshot["normal"]["fields"]["sticks_raw_i16"],
                         {"lx": 12345, "ly": -32768, "rx": 1, "ry": 32767})
        self.assertEqual(snapshot["stale_channels"], ["raw_hid"])
        self.assertIsNone(snapshot["raw_hid"])
        self.assertEqual(report["events"][-1]["fields"], {})
        for index, pressed in ((1, True), (2, False)):
            extras = report["events"][index]["fields"]["extra_buttons"]
            self.assertEqual([extras[name] for name in ("l4", "r4", "l5", "r5")], [pressed] * 4)

    def test_new_command_does_not_widen_existing_replay_transport_gate(self):
        code, output, error = invoke(["replay", str(FIXTURES / "captured_hid_returns.jsonl"), "--strict"])
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(json.loads(output)["counts"].get("decoded", 0), 0)

    def test_malformed_or_truncated_input_gives_strict_failure_with_report(self):
        row = json.loads((FIXTURES / "captured_hid_returns.jsonl").read_text().splitlines()[0])
        for change in ({"data_hex": row["data_hex"][:-2]}, {"reported_length": 63}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "bad.jsonl"
                path.write_text(json.dumps({**row, **change}) + "\n")
                code, output, error = invoke(["hid-replay", str(path), "--strict"])
                self.assertEqual((code, error), (1, ""))
                self.assertFalse(json.loads(output)["activation_proven"])

    def test_special_paths_and_symlinks_are_refused_without_opening_devices(self):
        for path in ("/dev/null", "/proc/version", "/sys/kernel"):
            code, output, error = invoke(["hid-replay", path])
            self.assertEqual((code, output), (2, ""))
            self.assertIn("not permitted", error)
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "not-a-capture"
            link.symlink_to("/dev/null")
            self.assertEqual(invoke(["hid-replay", str(link)])[0], 2)
            fifo = Path(temp) / "fifo"
            os.mkfifo(fifo)
            self.assertEqual(invoke(["hid-replay", str(fifo)])[0], 2)

    def test_live_options_and_invalid_age_limits_have_no_backend(self):
        for option in (["--live"], ["--send"], ["--max-age-us", "0"],
                       ["--max-age-us", "1000001"]):
            with self.subTest(option=option), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(["hid-replay", str(FIXTURES / "synthetic_hid_companion.jsonl"), *option])
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
