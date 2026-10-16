#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Coherent stream tests use constructed bytes, temporary files and mocks only."""
import copy
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/imu"))
import gamesir_imu_stream as stream
import gyro_reference as reference


def frame(counter=73, stamp=1_000_000_000, accel=(-8192, 0, 8192), gyro=(-123, 456, -789)):
    """Own full scan: six LE16 values, zero alignment, LE64 counter, CPU timestamp."""
    data = bytearray(32)
    struct.pack_into("<6h", data, 0, *accel, *gyro)
    struct.pack_into("<Q", data, 16, counter)
    data[24:32] = stamp.to_bytes(8, sys.byteorder, signed=True)
    return bytes(data)


def frames(count=5, *, start_counter=73, start_stamp=1_000_000_000, step=10_000_000):
    return b"".join(frame(start_counter + i, start_stamp + i * step) for i in range(count))


def fake_tree(parent):
    directory = Path(parent) / "iio:device77"
    directory.mkdir()
    values = {"name": stream.IIO_NAME, "current_timestamp_clock": "monotonic",
              "buffer/enable": "1", "buffer/length": "512",
              "buffer_push_errors": "0", "buffer_stream_active": "1", "dev": "240:77"}
    for index, name in enumerate(stream.CHANNELS):
        values[f"scan_elements/{name}_en"] = "1"
        values[f"scan_elements/{name}_index"] = str(index)
        values[f"scan_elements/{name}_type"] = (
            "le:s16/16>>0" if index < 6 else "le:u64/64>>0" if index == 6 else
            f"{'le' if sys.byteorder == 'little' else 'be'}:s64/64>>0")
    for name, value in values.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + "\n", encoding="ascii")
    return directory


class ScanDecoding(unittest.TestCase):
    def decoder(self, gap=10_000_000, source="synthetic"):
        return stream.ScanDecoder("constructed-instance", gap, source)

    def test_exact_layout_preserves_six_signed_channels_and_metadata(self):
        decoder = self.decoder()
        row, = list(decoder.feed(frame()))
        decoder.finish()
        self.assertEqual(row, {"timestamp_ns": 1_000_000_000, "sample_number": 73,
                              "accel_raw": [-8192, 0, 8192], "gyro_raw": [-123, 456, -789],
                              "coherent": True, "timebase": "host_monotonic_receive",
                              "source_kind": "synthetic", "instance_id": "constructed-instance"})

    def test_signed_int16_endpoints_are_preserved_without_conversion(self):
        decoder = self.decoder()
        row, = list(decoder.feed(frame(accel=(-32768, 32767, -1), gyro=(32767, -32768, 0))))
        self.assertEqual(row["accel_raw"], [-32768, 32767, -1])
        self.assertEqual(row["gyro_raw"], [32767, -32768, 0])

    def test_counter_and_timestamp_byte_offsets(self):
        stamp, counter = 0x0102030405060708, 0x1011121314151617
        row, = list(self.decoder().feed(frame(counter, stamp)))
        self.assertEqual(row["timestamp_ns"], stamp)
        self.assertEqual(row["sample_number"], counter)

    def test_first_nonzero_counter_is_arbitrary_then_exactly_consecutive(self):
        decoder = self.decoder()
        result = list(decoder.feed(frames(start_counter=8100)))
        decoder.finish()
        self.assertEqual([row["sample_number"] for row in result], list(range(8100, 8105)))

    def test_all_chunk_boundaries_and_byte_at_a_time_match_full_buffer(self):
        raw = frames()
        expected = list(self.decoder().feed(raw))
        for boundary in range(len(raw) + 1):
            with self.subTest(boundary=boundary):
                decoder = self.decoder()
                actual = list(decoder.feed(raw[:boundary])) + list(decoder.feed(raw[boundary:]))
                decoder.finish()
                self.assertEqual(actual, expected)
        decoder = self.decoder()
        actual = []
        for value in raw:
            actual.extend(decoder.feed(bytes([value])))
        decoder.finish()
        self.assertEqual(actual, expected)

    def test_partial_scan_yields_nothing_until_complete(self):
        decoder = self.decoder()
        self.assertEqual(list(decoder.feed(frame()[:31])), [])
        self.assertEqual(len(list(decoder.feed(frame()[31:]))), 1)
        decoder.finish()

    def test_trailing_partial_scan_and_empty_input_rejected(self):
        for data in (b"", frame()[:1], frame() + frame(74, 1_010_000_000)[:31]):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                decoder = self.decoder()
                list(decoder.feed(data))
                decoder.finish()

    def test_nonzero_alignment_padding_rejected(self):
        for index in range(12, 16):
            raw = bytearray(frame())
            raw[index] = 1
            with self.subTest(index=index), self.assertRaises(ValueError):
                list(self.decoder().feed(bytes(raw)))

    def test_duplicate_gap_reset_and_counter_wrap_rejected(self):
        for first, second in ((73, 73), (73, 75), (73, 1), ((1 << 64) - 1, 1)):
            with self.subTest(first=first, second=second), self.assertRaises(ValueError):
                list(self.decoder().feed(frame(first) + frame(second, 1_010_000_000)))

    def test_duplicate_backward_and_too_wide_timestamps_rejected(self):
        for stamp in (1_000_000_000, 999_999_999, 1_010_000_001):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                list(self.decoder().feed(frame() + frame(74, stamp)))

    def test_zero_counter_and_nonpositive_timestamp_rejected(self):
        for raw in (frame(counter=0), frame(stamp=0), frame(stamp=-1)):
            with self.subTest(raw=raw.hex()), self.assertRaises(ValueError):
                list(self.decoder().feed(raw))

    def test_receive_time_rejects_future_and_older_than_one_second(self):
        for received in (999_999_999, 2_000_000_001):
            with self.subTest(received=received), self.assertRaises(ValueError):
                list(self.decoder().feed(frame(), received_ns=received))
        self.assertEqual(len(list(self.decoder().feed(frame(), received_ns=2_000_000_000))), 1)

    def test_receive_time_requires_positive_integer_including_before_partial_chunk(self):
        for received in (0, -1, True, False, 1.0, float("nan"), float("inf"), "1000000000"):
            for raw in (frame(), b""):
                with self.subTest(received=received, size=len(raw)), self.assertRaisesRegex(ValueError, "positive integer"):
                    list(self.decoder().feed(raw, received_ns=received))

    def test_constructor_requires_explicit_bounded_gap_and_instance(self):
        for gap in (None, 0, -1, True, 1.0, 60_000_000_001):
            with self.subTest(gap=gap), self.assertRaises(ValueError):
                stream.ScanDecoder("test", gap)
        for identity in ("", None, "line\nbreak", "a" * 1025):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                stream.ScanDecoder(identity, 1)

    def test_constructor_rejects_unknown_source_and_chunk_type(self):
        with self.assertRaises(ValueError):
            self.decoder(source="iio_attribute_observation")
        for chunk in (bytearray(frame()), memoryview(frame()), "bytes", bytes(65537)):
            with self.subTest(kind=type(chunk)), self.assertRaises(ValueError):
                list(self.decoder().feed(chunk))


class IioMetadata(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-buffer-tree-")
        self.directory = fake_tree(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, value):
        (self.directory / name).write_text(str(value) + "\n", encoding="ascii")

    def test_full_layout_device_number_and_host_clock_inspected_without_writes(self):
        before = {p.relative_to(self.directory): p.read_bytes() for p in self.directory.rglob("*") if p.is_file()}
        result = stream.inspect_iio(self.directory)
        self.assertEqual((result["major"], result["minor"]), (240, 77))
        self.assertEqual(result["scan_bytes"], 32)
        self.assertEqual(result["clock"], "monotonic")
        self.assertEqual(result["buffer_push_errors"], 0)
        self.assertEqual(set(result["types"]), set(stream.CHANNELS))
        self.assertIn(str(self.directory), result["instance_id"])
        self.assertEqual({p.relative_to(self.directory): p.read_bytes() for p in self.directory.rglob("*") if p.is_file()}, before)

    def test_wrong_name_or_clock_rejected(self):
        for name, value in (("name", "unrelated_sensor"), ("current_timestamp_clock", "realtime")):
            old = (self.directory / name).read_text()
            self.write(name, value)
            with self.subTest(name=name), self.assertRaises(ValueError):
                stream.inspect_iio(self.directory)
            (self.directory / name).write_text(old)

    def test_all_channels_must_be_enabled(self):
        self.write(f"scan_elements/{stream.CHANNELS[0]}_en", "0")
        with self.assertRaises(ValueError):
            stream.inspect_iio(self.directory)

    def test_additional_enabled_channel_rejected(self):
        self.write("scan_elements/in_unexpected_en", "1")
        with self.assertRaises(ValueError):
            stream.inspect_iio(self.directory)

    def test_extra_disabled_channel_does_not_change_full_scan(self):
        self.write("scan_elements/in_unexpected_en", "0")
        self.assertEqual(stream.inspect_iio(self.directory)["scan_bytes"], 32)

    def test_each_scan_type_and_index_is_checked(self):
        for name in stream.CHANNELS:
            for suffix, bad in (("type", "le:u16/16>>0"), ("index", "999")):
                path = self.directory / f"scan_elements/{name}_{suffix}"
                old = path.read_text()
                self.write(str(path.relative_to(self.directory)), bad)
                with self.subTest(name=name, suffix=suffix), self.assertRaises(ValueError):
                    stream.inspect_iio(self.directory)
                path.write_text(old)

    def test_counter_must_be_le64_and_timestamp_cpu_signed64(self):
        self.assertEqual(stream.inspect_iio(self.directory)["types"]["in_count0"], "le:u64/64>>0")
        expected = f"{'le' if sys.byteorder == 'little' else 'be'}:s64/64>>0"
        self.assertEqual(stream.inspect_iio(self.directory)["types"]["in_timestamp"], expected)

    def test_disabled_buffer_invalid_length_and_negative_errors_rejected(self):
        for path, value in (("buffer/enable", "0"), ("buffer/length", "1"), ("buffer_push_errors", "-1")):
            old = (self.directory / path).read_text()
            self.write(path, value)
            with self.subTest(path=path), self.assertRaises(ValueError):
                stream.inspect_iio(self.directory)
            (self.directory / path).write_text(old)

    def test_missing_metadata_is_not_invented(self):
        (self.directory / "buffer_push_errors").unlink()
        with self.assertRaises((ValueError, OSError)):
            stream.inspect_iio(self.directory)

    def test_quiesced_producer_gate_rejected_even_when_iio_buffer_remains_enabled(self):
        self.write("buffer_stream_active", "0")
        self.assertEqual((self.directory / "buffer/enable").read_text().strip(), "1")
        with self.assertRaisesRegex(ValueError, "producer gate stopped"):
            stream.inspect_iio(self.directory)

    def test_missing_producer_gate_metadata_rejected(self):
        (self.directory / "buffer_stream_active").unlink()
        with self.assertRaises((ValueError, OSError)):
            stream.inspect_iio(self.directory)

    def test_changed_instance_inode_rejected(self):
        original = Path.stat
        count = 0

        def changed(path, *args, **kwargs):
            nonlocal count
            result = original(path, *args, **kwargs)
            if path == self.directory:
                count += 1
                return SimpleNamespace(st_dev=result.st_dev, st_ino=result.st_ino + (count > 1))
            return result
        with patch.object(Path, "stat", changed), self.assertRaises(ValueError):
            stream.inspect_iio(self.directory)

    def test_configuration_plan_is_declarative_without_attribute_access(self):
        with patch.object(stream, "read_attribute", side_effect=AssertionError("no live IIO")):
            plan = stream.configuration_plan()
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(stream.main(["configuration-plan"]), 0)
        self.assertTrue(plan["plan_only"])
        self.assertFalse(plan["executed"])
        self.assertTrue(plan["requires_separate_approval"])
        self.assertFalse(plan["close_reader_disables_buffer"])
        self.assertFalse(plan["usb_or_sensor_configuration_commands"])
        self.assertEqual(json.loads(output.getvalue()), plan)


class OfflineBundles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-scan-bundle-")
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "source.bin"
        self.output = self.folder / "bundle"

    def tearDown(self):
        self.temporary.cleanup()

    def decode(self, raw):
        self.source.write_bytes(raw)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = stream.main(["decode-file", "--scans", str(self.source), "--output", str(self.output),
                                "--instance-id", "constructed-instance", "--source-kind", "synthetic",
                                "--max-gap-ms", "10"])
        return code

    def test_saved_binary_bundle_has_original_bytes_layout_timestamps_and_hashes(self):
        raw = frames(9)
        self.assertEqual(self.decode(raw), 0)
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual((self.output / "scans.bin").read_bytes(), raw)
        report = json.loads((self.output / "report.json").read_text())
        layout = json.loads((self.output / "layout.json").read_text())
        self.assertTrue(report["completed"])
        self.assertTrue(report["coherent"])
        self.assertEqual(report["observations"], 9)
        self.assertFalse(report["buffer_configuration_modified"])
        self.assertFalse(report["buffer_disabled_by_reader"])
        self.assertFalse(report["calibration_verified"])
        self.assertFalse(report["radio_or_sensor_loss_known"])
        self.assertEqual(layout["host_timestamp_offset"], 24)
        self.assertEqual(layout["counter_offset"], 16)
        self.assertEqual(layout["scan_bytes"], 32)
        listed = set()
        for line in (self.output / "SHA256SUMS").read_text().splitlines():
            expected, name = line.split("  ", 1)
            listed.add(name)
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(listed, {"observations.jsonl", "report.json", "scans.bin", "layout.json"})
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in self.output.iterdir()))

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        protected = self.output / "keep.txt"
        protected.write_text("keep")
        self.assertEqual(self.decode(frames()), 1)
        self.assertEqual(protected.read_text(), "keep")
        self.assertEqual(set(self.output.iterdir()), {protected})

    def test_partial_trailing_scan_is_preserved_and_marks_failed_report(self):
        raw = frames(2) + frame(75, 1_020_000_000)[:13]
        self.assertEqual(self.decode(raw), 1)
        self.assertEqual((self.output / "scans.bin").read_bytes(), raw)
        report = json.loads((self.output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertIn("incomplete trailing scan", report["failure"])
        self.assertEqual(report["observations"], 2)
        self.assertTrue((self.output / "SHA256SUMS").is_file())

    def test_invalid_frame_stops_and_preserves_received_bytes(self):
        raw = frame() + frame(99, 1_010_000_000) + frame(100, 1_020_000_000)
        self.assertEqual(self.decode(raw), 1)
        self.assertEqual((self.output / "scans.bin").read_bytes(), raw)
        report = json.loads((self.output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertEqual(report["observations"], 1)

    def test_growing_saved_input_cannot_exceed_bounded_byte_limit(self):
        raw = frames(2)
        with patch.object(stream, "MAX_FILE_BYTES", 32), \
                patch.object(stream, "saved_binary", return_value=io.BytesIO(raw)):
            self.assertEqual(self.decode(raw), 1)
        report = json.loads((self.output / "report.json").read_text())
        self.assertFalse(report["completed"])
        self.assertIn("stored input grew beyond bounded file limit", report["failure"])
        self.assertEqual(report["observations"], 0)
        self.assertEqual((self.output / "scans.bin").read_bytes(), b"")
        self.assertEqual(self.source.read_bytes(), raw)

    def capture_with_failed_collector_close(self, raw):
        class Collector:
            closes = 0

            def __iter__(self):
                yield raw, 1_040_000_000

            def close(self):
                self.closes += 1
                raise OSError("constructed IIO fd close failure")

        collector = Collector()
        metadata = {"instance_id": "constructed-instance"}
        with patch.object(stream, "inspect_iio", return_value=metadata), \
                patch.object(stream, "live_chunks", return_value=collector), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = stream.main(["capture", "--experimental", "--iio-dir", "/synthetic-metadata",
                                "--device-node", "/synthetic-node", "--output", str(self.output),
                                "--duration", ".1", "--max-gap-ms", "10"])
        self.assertEqual(collector.closes, 1)
        return code, json.loads((self.output / "report.json").read_text())

    def test_primary_decoder_failure_preserved_when_collector_close_also_fails(self):
        raw = frame() + frame(99, 1_010_000_000)
        code, report = self.capture_with_failed_collector_close(raw)
        self.assertEqual(code, 1)
        self.assertFalse(report["completed"])
        self.assertIn("accepted-report counter gap", report["failure"])
        self.assertNotIn("close failure", report["failure"])
        self.assertEqual(report["cleanup_errors"], ["close: constructed IIO fd close failure"])
        self.assertEqual((self.output / "scans.bin").read_bytes(), raw)

    def test_collector_close_failure_invalidates_otherwise_complete_capture(self):
        code, report = self.capture_with_failed_collector_close(frames(2))
        self.assertEqual(code, 1)
        self.assertFalse(report["completed"])
        self.assertIn("cleanup failed: close: constructed IIO fd close failure", report["failure"])
        self.assertEqual(report["observations"], 2)
        self.assertEqual(report["cleanup_errors"], ["close: constructed IIO fd close failure"])

    def test_saved_file_reader_uses_regular_file_and_readonly_flags(self):
        self.source.write_bytes(frames())
        original = stream.os.open
        calls = []

        def recording(path, flags, *args):
            calls.append((path, flags))
            return original(path, flags, *args)
        with patch.object(stream.os, "open", recording):
            with stream.saved_binary(self.source) as handle:
                self.assertEqual(handle.read(), frames())
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)

    def test_saved_directory_rejected_without_device_open(self):
        with patch.object(stream.os, "open", side_effect=AssertionError("no open")), self.assertRaises(ValueError):
            stream.saved_binary(self.folder)

    def test_decoded_saved_rows_satisfy_reference_contract_and_integrate_without_clock_invention(self):
        from test_gyro_reference import fixture, STEP
        records, metadata = fixture()
        raw = b"".join(frame(row["sample_number"], row["timestamp_ns"],
                             row["accel_raw"], row["gyro_raw"]) for row in records)
        self.assertEqual(self.decode(raw), 0)
        decoded = [json.loads(line) for line in (self.output / "observations.jsonl").read_text().splitlines()]
        self.assertEqual(decoded, [dict(row, instance_id="constructed-instance") for row in records])
        analyzed = reference.analyze_reference(decoded, metadata, STEP)
        self.assertEqual(analyzed["intervals_discarded"], 0)
        self.assertFalse(analyzed["timestamps_reconstructed"])
        self.assertFalse(analyzed["calibration_verified"])


class MockedCapture(unittest.TestCase):
    """All node and clock interactions mocked: never inspect/open a real node."""
    def setUp(self):
        self.metadata = {"major": 240, "minor": 77, "directory": "/synthetic/iio:device77",
                         "instance_id": "constructed-instance", "buffer_push_errors": 0}
        self.char = SimpleNamespace(st_mode=stat.S_IFCHR | 0o600, st_rdev=os.makedev(240, 77))

    def harness(self, *, times=None, reads=None, inspections=None, offsets=None, ready=True):
        stack = ExitStack()
        self.addCleanup(stack.close)
        mocks = {}
        mocks["lstat"] = stack.enter_context(patch.object(Path, "lstat", return_value=self.char))
        mocks["open"] = stack.enter_context(patch.object(stream.os, "open", return_value=99))
        mocks["fstat"] = stack.enter_context(patch.object(stream.os, "fstat", return_value=self.char))
        mocks["close"] = stack.enter_context(patch.object(stream.os, "close"))
        stack.enter_context(patch.object(stream.time, "monotonic", side_effect=times or [0, .01, .02, .03, .04, .11, .12]))
        stack.enter_context(patch.object(stream.time, "monotonic_ns", return_value=1_040_000_000))
        mocks["sleep"] = stack.enter_context(patch.object(stream.time, "sleep"))
        stack.enter_context(patch.object(stream, "boottime_offset", side_effect=offsets, return_value=0))
        if inspections is None:
            stack.enter_context(patch.object(stream, "inspect_iio", return_value=self.metadata))
        else:
            stack.enter_context(patch.object(stream, "inspect_iio", side_effect=inspections))
        stack.enter_context(patch.object(stream.select, "select", return_value=([99] if ready else [], [], [])))
        mocks["read"] = stack.enter_context(patch.object(stream.os, "read", side_effect=reads or [frames(2)]))
        return mocks

    def test_only_matching_node_opened_readonly_nonblocking_without_attribute_writes(self):
        mocks = self.harness()
        rows = list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        self.assertEqual(rows, [(frames(2), 1_040_000_000)])
        mocks["open"].assert_called_once_with(Path("/synthetic-node"), os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
        mocks["close"].assert_called_once_with(99)

    def test_wrong_node_number_rejected_before_open(self):
        mocks = self.harness()
        mocks["lstat"].return_value = SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=os.makedev(240, 78))
        with self.assertRaises(ValueError):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["open"].assert_not_called()

    def test_non_character_node_rejected_before_open(self):
        mocks = self.harness()
        mocks["lstat"].return_value = SimpleNamespace(st_mode=stat.S_IFREG, st_rdev=os.makedev(240, 77))
        with self.assertRaises(ValueError):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["open"].assert_not_called()

    def test_changed_opened_node_is_closed(self):
        mocks = self.harness()
        mocks["fstat"].return_value = SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=os.makedev(240, 78))
        with self.assertRaises(ValueError):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["close"].assert_called_once_with(99)

    def test_suspend_discontinuity_stops_and_closes(self):
        mocks = self.harness(offsets=[0, 50_000_001])
        with self.assertRaisesRegex(ValueError, "suspend"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["read"].assert_not_called()
        mocks["close"].assert_called_once_with(99)

    def test_primary_suspend_failure_not_overwritten_by_fd_close_error(self):
        mocks = self.harness(offsets=[0, 50_000_001])
        mocks["close"].side_effect = OSError("constructed fd close error")
        with self.assertRaisesRegex(ValueError, "suspend"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["read"].assert_not_called()
        mocks["close"].assert_called_once_with(99)

    def test_producer_error_and_instance_change_stop(self):
        for field, value in (("buffer_push_errors", 1), ("instance_id", "different")):
            with self.subTest(field=field):
                changed = dict(self.metadata, **{field: value})
                mocks = self.harness(inspections=[changed])
                with self.assertRaises(ValueError):
                    list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
                mocks["read"].assert_not_called()
                mocks["close"].assert_called_once_with(99)

    def test_no_data_timeout_stops_without_reconnect(self):
        mocks = self.harness(times=[0, .01, .02, .11], ready=False)
        with self.assertRaisesRegex(ValueError, "no fresh"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", 1, .05))
        mocks["read"].assert_not_called()
        mocks["close"].assert_called_once_with(99)

    def test_read_eof_stops_and_closes(self):
        mocks = self.harness(reads=[b""])
        with self.assertRaisesRegex(ValueError, "EOF"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["close"].assert_called_once_with(99)

    def test_transient_nonblocking_read_is_not_fabricated_data(self):
        mocks = self.harness(reads=[BlockingIOError()])
        self.assertEqual(list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2)), [])
        mocks["close"].assert_called_once_with(99)
        mocks["sleep"].assert_called_once_with(.005)

    def test_eagain_cannot_bypass_no_data_timeout_or_busy_loop(self):
        mocks = self.harness(times=[0, .01, .02, .03, .11], reads=[BlockingIOError()])
        with self.assertRaisesRegex(ValueError, "no fresh coherent samples after EAGAIN"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", 1, .05))
        mocks["read"].assert_called_once_with(99, 4096)
        mocks["sleep"].assert_not_called()
        mocks["close"].assert_called_once_with(99)

    def test_stale_tail_after_final_chunk_is_not_success(self):
        mocks = self.harness()
        with self.assertRaisesRegex(ValueError, "no fresh coherent samples at capture end"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, .05))
        mocks["close"].assert_called_once_with(99)

    def test_partial_reads_can_feed_decoder(self):
        raw = frame()
        mocks = self.harness(times=[0, .01, .02, .03, .04, .05, .06, .07, .08, .11, .12], reads=[raw[:7], raw[7:]])
        decoder = stream.ScanDecoder("constructed-instance", 10_000_000, "synthetic")
        rows = []
        for chunk, received in stream.live_chunks(self.metadata, "/synthetic-node", .1, 2):
            rows.extend(decoder.feed(chunk, received))
        decoder.finish()
        self.assertEqual(len(rows), 1)
        mocks["close"].assert_called_once_with(99)

    def test_tail_error_after_last_data_is_not_success(self):
        changed = dict(self.metadata, buffer_push_errors=1)
        mocks = self.harness(inspections=[self.metadata, changed])
        with self.assertRaisesRegex(ValueError, "tail"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["close"].assert_called_once_with(99)

    def test_suspend_at_tail_is_not_success(self):
        mocks = self.harness(offsets=[0, 0, 50_000_001])
        with self.assertRaisesRegex(ValueError, "suspend at capture end"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2))
        mocks["close"].assert_called_once_with(99)

    def test_explicit_collector_close_closes_its_own_fd(self):
        mocks = self.harness()
        collector = stream.live_chunks(self.metadata, "/synthetic-node", .1, 2)
        next(collector)
        collector.close()
        mocks["close"].assert_called_once_with(99)

    def test_transaction_descriptor_is_reused_and_never_closed_by_reader(self):
        mocks = self.harness()
        with patch.object(stream.fcntl, "fcntl", return_value=os.O_RDONLY | os.O_NONBLOCK):
            rows = list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2, descriptor=99))
        self.assertEqual(rows, [(frames(2), 1_040_000_000)])
        mocks["open"].assert_not_called()
        mocks["close"].assert_not_called()

    def test_borrowed_descriptor_requires_readonly_nonblocking_flags(self):
        for flags in (os.O_RDONLY, os.O_RDWR | os.O_NONBLOCK, os.O_WRONLY | os.O_NONBLOCK):
            with self.subTest(flags=flags):
                mocks = self.harness()
                with patch.object(stream.fcntl, "fcntl", return_value=flags), self.assertRaises(ValueError):
                    list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2, descriptor=99))
                mocks["open"].assert_not_called()
                mocks["close"].assert_not_called()

    def test_frontend_cancellation_before_read_preserves_transaction_descriptor(self):
        mocks = self.harness()
        with patch.object(stream.fcntl, "fcntl", return_value=os.O_NONBLOCK), self.assertRaisesRegex(ValueError, "frontend gone"):
            list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2, descriptor=99,
                                    check_alive=lambda: (_ for _ in ()).throw(ValueError("frontend gone"))))
        mocks["read"].assert_not_called()
        mocks["close"].assert_not_called()

    def test_frontend_cancellation_after_select_prevents_read(self):
        mocks = self.harness()
        with patch.object(stream.fcntl, "fcntl", return_value=os.O_NONBLOCK):
            calls = iter([None, ValueError("STOP after select")])

            def cancellation():
                result = next(calls)
                if result is not None:
                    raise result

            with self.assertRaisesRegex(ValueError, "STOP after select"):
                list(stream.live_chunks(self.metadata, "/synthetic-node", .1, 2, descriptor=99,
                                        check_alive=cancellation))
        mocks["read"].assert_not_called()
        mocks["close"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
