# SPDX-License-Identifier: GPL-2.0-only
import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gamesir_offline.records import RecordError, read_records, record_from_object


ROOT = Path(__file__).resolve().parents[1]


def example():
    return json.loads((ROOT / "fixtures/synthetic_valid.jsonl").read_text().splitlines()[0])


class RecordTests(unittest.TestCase):
    def test_fixture_evidence_is_explicitly_synthetic(self):
        for path in (ROOT / "fixtures").glob("*.jsonl"):
            for record in read_records(path):
                self.assertEqual(record.source_kind, "synthetic")
                self.assertEqual(record.timebase, "synthetic")

    def test_metadata_bool_is_not_an_integer(self):
        value = example()
        value["timestamp_us"] = True
        with self.assertRaises(RecordError):
            record_from_object(value)

    def test_invalid_endpoint_hex_and_reserved_bits(self):
        for endpoint in ("0x82", "8z", "f2", "", 130):
            value = example()
            value["endpoint"] = endpoint
            with self.subTest(endpoint=endpoint), self.assertRaises(RecordError):
                record_from_object(value)

    def test_invalid_hex_payload_and_oversize_are_rejected(self):
        for data in ("0", "gg", "00 14", "00" * 4097):
            value = example()
            value["data_hex"] = data
            with self.assertRaises(RecordError):
                record_from_object(value)

    def test_metadata_requires_complete_identity_and_source(self):
        for path in (("device", "pid"), ("source", "kind")):
            value = example()
            del value[path[0]][path[1]]
            with self.assertRaises(RecordError):
                record_from_object(value)
        value = example()
        value["unexpected"] = "typo"
        with self.assertRaises(RecordError):
            record_from_object(value)

    def test_capture_kind_requires_host_capture_timebase(self):
        value = example()
        value["source"]["kind"] = "capture_excerpt"
        with self.assertRaises(RecordError):
            record_from_object(value)
        value["timebase"] = "host_capture"
        self.assertEqual(record_from_object(value).source_kind, "capture_excerpt")

    def test_invalid_stage_address_status_and_schema(self):
        changes = (("stage", "invented"), ("status", 0.0), ("schema_version", True),
                   ("capture_truncated", 0), ("timestamp_us", -1))
        for key, bad_value in changes:
            value = example()
            value[key] = bad_value
            with self.subTest(key=key), self.assertRaises(RecordError):
                record_from_object(value)
        value = example()
        value["device"]["address"] = 128
        with self.assertRaises(RecordError):
            record_from_object(value)

    def test_duplicate_json_keys_rejected(self):
        value = example()
        line = json.dumps(value).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.jsonl"
            path.write_text(line)
            with self.assertRaisesRegex(RecordError, "duplicate JSON key"):
                list(read_records(path))

    def test_line_limit_and_json_errors_have_line_numbers(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.jsonl"
            for body in ("x" * 65537, "\n{broken}"):
                path.write_text(body)
                with self.assertRaisesRegex(RecordError, "line [12]"):
                    list(read_records(path))

    def test_excessively_nested_json_is_a_record_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested.jsonl"
            path.write_text("[" * 2000 + "0" + "]" * 2000)
            with self.assertRaisesRegex(RecordError, "line 1"):
                list(read_records(path))

    def test_special_paths_are_rejected_before_open(self):
        for path in ("/dev/null", "/proc/version", "/sys"):
            with patch("gamesir_offline.records.os.open") as opener:
                with self.assertRaises(RecordError):
                    list(read_records(path))
                opener.assert_not_called()

    def test_proc_fd_path_cannot_bypass_guard_via_regular_file_symlink(self):
        with patch("gamesir_offline.records.Path.resolve") as resolver:
            with self.assertRaises(RecordError):
                list(read_records("/proc/self/fd/123"))
            resolver.assert_not_called()

    def test_fifo_directory_and_symlink_to_device_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / "fifo"
            os.mkfifo(fifo)
            link = Path(temp) / "device-link"
            link.symlink_to("/dev/null")
            for path in (fifo, Path(temp), link):
                with patch("gamesir_offline.records.os.open") as opener:
                    with self.assertRaises(RecordError):
                        list(read_records(path))
                    opener.assert_not_called()

    def test_source_package_has_no_transport_or_process_imports(self):
        forbidden = {"usb", "hid", "hidapi", "socket", "ctypes", "fcntl", "subprocess", "serial"}
        for path in (ROOT / "gamesir_offline").glob("*.py"):
            tree = ast.parse(path.read_text())
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(name.name.split(".")[0] for name in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module.split(".")[0])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ("system", "popen", "ioctl", "write"))
            self.assertFalse(forbidden.intersection(imports), path.name)


if __name__ == "__main__":
    unittest.main()
