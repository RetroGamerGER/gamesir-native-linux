# SPDX-License-Identifier: GPL-2.0-only
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from gamesir_offline.cli import main


ROOT = Path(__file__).resolve().parents[1]


def invoke(arguments):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


class CliTests(unittest.TestCase):
    def test_valid_replay_strict_success(self):
        code, output, error = invoke(["replay", str(ROOT / "fixtures/synthetic_valid.jsonl"), "--strict", "--events"])
        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        self.assertEqual(len(json.loads(output)["events"]), 19)

    def test_negative_replay_strict_exit_one_with_report(self):
        code, output, _ = invoke(["replay", str(ROOT / "fixtures/synthetic_negative.jsonl"), "--strict"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)["counts"]["malformed"], 9)

    def test_default_mode_reports_negative_cases_without_crashing(self):
        code, output, _ = invoke(["replay", str(ROOT / "fixtures/synthetic_negative.jsonl")])
        self.assertEqual(code, 0)
        self.assertNotIn("events", json.loads(output))

    def test_device_file_refused_without_json_report(self):
        code, output, error = invoke(["replay", "/dev/null"])
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("not permitted", error)

    def test_invalid_json_is_reported_as_input_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.jsonl"
            path.write_text("{broken}")
            code, output, error = invoke(["replay", str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            self.assertIn("line 1", error)

    def test_missing_file_is_reported_as_input_error(self):
        code, output, error = invoke(["replay", str(ROOT / "does-not-exist.jsonl")])
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
