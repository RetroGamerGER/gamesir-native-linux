#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""No hardware: actual transaction class against fake IIO, and writer temp files."""
import copy
import errno
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/imu"))
import gamesir_iio_buffer as setup


def state():
    return {"schema_version": 1, "directory": "/sys/devices/fake/8-6/8-6:1.0/iio:device77",
            "iio_identity": [19, 990], "device_node": "/dev/iio:device77", "major": 240, "minor": 77,
            "usb": {"directory": "/sys/devices/fake/8-6", "identity": [19, 980],
                    "parent_identity": [19, 970], "interface_directory": "/sys/devices/fake/8-6/8-6:1.0",
                    "interface_identity": [19, 981], "interface_number": 0, "vid": "3537", "pid": "109c",
                    "bus": 8, "address": 17, "driver": "gs_native"},
            "module_srcversion": setup.MODULE_SRCVERSION,
            "settings": {"current_timestamp_clock": "monotonic", "buffer/length": "128",
                         "buffer/watermark": "1", **{f"scan_elements/{name}_en": "0" for name in setup.CHANNELS}},
            "types": {name: "le:s16/16>>0" if index < 6 else "le:u64/64>>0" if index == 6 else
                      f"{'le' if sys.byteorder == 'little' else 'be'}:s64/64>>0" for index, name in enumerate(setup.CHANNELS)},
            "buffer_enable": "0", "buffer_stream_active": "0", "buffer_push_errors": 0}


class FakeBackend:
    def __init__(self):
        self.value = state()
        self.pinned = self.value["iio_identity"][:]
        self.events, self.closed, self.written = [], [], []
        self.busy = self.removed = False
        self.fail_write = set()
        self.fail_close = set()
        self.write_count = 0
        self.after_open = self.before_write = None

    def snapshot(self, directory, node):
        self.events.append("snapshot")
        if self.removed:
            raise FileNotFoundError("original IIO removed")
        assert directory == self.value["directory"] and node == self.value["device_node"]
        return copy.deepcopy(self.value)

    def open_directory(self, directory):
        self.events.append("pin")
        return 101

    def directory_identity(self, fd):
        assert fd == 101
        return self.pinned[:]

    def open_node(self, node, major, minor):
        self.events.append("open-reader")
        if self.busy:
            raise OSError(errno.EBUSY, "single reader occupied")
        if self.after_open:
            self.after_open()
        return 102

    def write_at(self, directory_fd, relative, value):
        assert directory_fd == 101
        self.write_count += 1
        self.events.append((relative, value))
        if self.before_write:
            self.before_write(relative, value)
        # A short/failed sysfs write can have applied the value already.
        if relative == "buffer/enable":
            self.value["buffer_enable"] = value
            self.value["buffer_stream_active"] = value
        else:
            self.value["settings"][relative] = value
        self.written.append((relative, value))
        if self.write_count in self.fail_write:
            raise OSError("injected write failure")

    def close(self, fd):
        self.events.append(("close", fd))
        self.closed.append(fd)
        if fd in self.fail_close:
            raise OSError("injected close failure")


class Transactions(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.expected = copy.deepcopy(self.backend.value)
        self.transaction = setup.BufferTransaction(self.expected, backend=self.backend)

    def test_snapshot_boundary_reads_only_metadata(self):
        self.assertEqual(setup.snapshot_iio("ignored", "ignored", backend=type("Fake", (), {
            "snapshot": lambda this, directory, node: self.expected})()), self.expected)
        self.assertEqual(self.backend.events, [])

    def test_setup_claims_exactly_one_reader_before_any_write_and_keeps_it(self):
        metadata, fd = self.transaction.setup()
        self.assertEqual(fd, 102)
        self.assertEqual(self.backend.events.count("open-reader"), 1)
        self.assertLess(self.backend.events.index("open-reader"), self.backend.events.index(("buffer/length", "512")))
        self.assertEqual(self.backend.closed, [])
        self.assertEqual(metadata["instance_id"], self.expected["directory"] + ":19:990")
        self.assertEqual(metadata["scan_bytes"], 32)
        self.assertEqual(self.backend.value["buffer_stream_active"], "1")
        self.assertEqual(self.backend.value["usb"], self.expected["usb"])
        self.assertNotIn(("current_timestamp_clock", "monotonic"), self.backend.written)
        self.assertNotIn(("buffer/watermark", "1"), self.backend.written)

    def test_restore_disables_first_restores_original_once_and_closes_last(self):
        self.transaction.setup()
        boundary = len(self.backend.written)
        report = self.transaction.restore()
        self.assertTrue(report["restored"], report)
        self.assertEqual(self.backend.written[boundary], ("buffer/enable", "0"))
        self.assertEqual(self.backend.value, self.expected)
        self.assertEqual(self.backend.closed, [102, 101])
        self.assertEqual(len({name for name, _ in self.backend.written[boundary:]}), len(self.backend.written[boundary:]))
        self.assertEqual(self.transaction.restore(), report)
        self.assertEqual(self.backend.closed, [102, 101])

    def test_optional_watermark_absent_is_not_created(self):
        del self.backend.value["settings"]["buffer/watermark"]
        expected = copy.deepcopy(self.backend.value)
        transaction = setup.BufferTransaction(expected, backend=self.backend)
        transaction.setup()
        self.assertTrue(transaction.restore()["restored"])
        self.assertFalse(any(name == "buffer/watermark" for name, _ in self.backend.written))

    def test_different_original_clock_and_watermark_are_restored(self):
        self.backend.value["settings"]["current_timestamp_clock"] = "realtime"
        self.backend.value["settings"]["buffer/watermark"] = "8"
        expected = copy.deepcopy(self.backend.value)
        transaction = setup.BufferTransaction(expected, backend=self.backend)
        transaction.setup()
        self.assertTrue(transaction.restore()["restored"])
        self.assertEqual(self.backend.value, expected)

    def test_busy_reader_produces_no_writes(self):
        self.backend.busy = True
        with self.assertRaises(OSError):
            self.transaction.setup()
        self.assertEqual(self.backend.written, [])
        self.assertEqual(self.backend.closed, [101])
        self.assertTrue(self.transaction.restore_report["restored"])

    def test_initial_snapshot_change_aborts_without_device_open(self):
        for field, changed in (("buffer_enable", "1"), ("buffer_stream_active", "1"),
                               ("buffer_push_errors", 1), ("module_srcversion", "OTHER")):
            with self.subTest(field=field):
                backend = FakeBackend()
                transaction = setup.BufferTransaction(copy.deepcopy(backend.value), backend=backend)
                backend.value[field] = changed
                with self.assertRaises(ValueError):
                    transaction.setup()
                self.assertNotIn("open-reader", backend.events)
                self.assertEqual(backend.written, [])

    def test_changed_original_setting_aborts_without_writes(self):
        self.backend.value["settings"]["buffer/length"] = "256"
        with self.assertRaises(ValueError):
            self.transaction.setup()
        self.assertEqual(self.backend.written, [])

    def test_reader_claim_race_is_detected(self):
        self.backend.after_open = lambda: self.backend.value.update(buffer_enable="1")
        with self.assertRaises(ValueError):
            self.transaction.setup()
        # Configuration never starts: raced activation does not belong to us.
        self.assertEqual(self.backend.written, [])
        self.assertFalse(self.transaction.restore_report["restored"])
        self.assertEqual(self.backend.closed, [102, 101])

    def test_failure_at_every_setup_write_rolls_back_partial_application(self):
        for failure in range(1, 11):  # length, eight enables, buffer enable
            with self.subTest(write=failure):
                backend = FakeBackend()
                before = copy.deepcopy(backend.value)
                backend.fail_write = {failure}
                transaction = setup.BufferTransaction(before, backend=backend)
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    transaction.setup()
                self.assertTrue(transaction.restore_report["restored"], transaction.restore_report)
                self.assertEqual(backend.value, before)
                self.assertEqual(backend.closed, [102, 101])

    def test_disconnect_never_attempts_replacement_writes(self):
        self.transaction.setup()
        count = len(self.backend.written)
        self.backend.removed = True
        report = self.transaction.restore()
        self.assertFalse(report["restored"])
        self.assertIn("removed", report["errors"][0])
        self.assertEqual(len(self.backend.written), count)
        self.assertEqual(self.backend.closed, [102, 101])

    def test_every_relevant_identity_change_blocks_cleanup_writes(self):
        changes = [lambda x: x.update(iio_identity=[19, 991]),
                   lambda x: x["usb"].update(identity=[19, 981]),
                   lambda x: x["usb"].update(parent_identity=[19, 971]),
                   lambda x: x["usb"].update(interface_identity=[19, 982]),
                   lambda x: x["usb"].update(driver="xpad"),
                   lambda x: x["usb"].update(address=18),
                   lambda x: x.update(major=241),
                   lambda x: x.update(module_srcversion="OTHER")]
        for change in changes:
            with self.subTest(change=change):
                backend = FakeBackend()
                transaction = setup.BufferTransaction(copy.deepcopy(backend.value), backend=backend)
                transaction.setup()
                count = len(backend.written)
                change(backend.value)
                self.assertFalse(transaction.restore()["restored"])
                self.assertEqual(len(backend.written), count)

    def test_pinned_directory_mismatch_blocks_write(self):
        self.backend.pinned = [19, 991]
        with self.assertRaises(ValueError):
            self.transaction.setup()
        self.assertEqual(self.backend.written, [])
        self.assertEqual(self.backend.closed, [101])

    def test_failed_disable_is_reported_without_changing_active_scan_attributes(self):
        self.transaction.setup()
        self.backend.fail_write = {11}
        count = len(self.backend.written)
        report = self.transaction.restore()
        self.assertFalse(report["restored"])
        self.assertEqual(self.backend.written[count:], [("buffer/enable", "0")])
        self.assertEqual(self.backend.closed, [102, 101])

    def test_primary_setup_error_not_replaced_by_rollback_failure(self):
        self.backend.fail_write = {10, 11}
        with self.assertRaisesRegex(OSError, "injected write failure") as raised:
            self.transaction.setup()
        self.assertTrue(any("restoration errors" in note for note in raised.exception.__notes__))
        self.assertFalse(self.transaction.restore_report["restored"])

    def test_failed_restore_attribute_is_not_retried(self):
        self.transaction.setup()
        self.backend.fail_write = {12}
        report = self.transaction.restore()
        count = len(self.backend.written)
        self.assertFalse(report["restored"])
        self.transaction.restore()
        self.assertEqual(len(self.backend.written), count)

    def test_close_failure_is_explicit(self):
        self.transaction.setup()
        self.backend.fail_close = {102, 101}
        report = self.transaction.restore()
        self.assertFalse(report["restored"])
        self.assertEqual(len(report["errors"]), 2)

    def test_second_setup_cannot_restart_transaction(self):
        self.transaction.setup()
        self.transaction.restore()
        with self.assertRaisesRegex(ValueError, "once"):
            self.transaction.setup()

    def test_setup_after_explicit_restore_never_opens_a_node(self):
        self.transaction.restore()
        # Restoring before setup makes a transaction unusable.
        with self.assertRaises(ValueError):
            self.transaction.setup()
        self.assertNotIn("open-reader", self.backend.events)


class SafeWriter(unittest.TestCase):
    def test_only_relative_attribute_inside_pinned_directory_is_written(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "buffer").mkdir()
            path = directory / "buffer/enable"
            path.write_text("0\n", encoding="ascii")
            fd = setup.MetadataBackend.open_directory(directory)
            try:
                setup.MetadataBackend.write_at(fd, "buffer/enable", "1")
                self.assertEqual(path.read_text(), "1\n")
                for invalid in ("../escape", "/absolute", "a/b/c", "buffer/../escape"):
                    with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                        setup.MetadataBackend.write_at(fd, invalid, "1")
            finally:
                os.close(fd)

    def test_symlink_parent_and_leaf_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "real").mkdir()
            (root / "real/enable").write_text("0\n")
            (root / "buffer").symlink_to("real", target_is_directory=True)
            (root / "leaf").symlink_to("real/enable")
            fd = setup.MetadataBackend.open_directory(root)
            try:
                for relative in ("buffer/enable", "leaf"):
                    with self.subTest(relative=relative), self.assertRaises(OSError):
                        setup.MetadataBackend.write_at(fd, relative, "1")
                self.assertEqual((root / "real/enable").read_text(), "0\n")
            finally:
                os.close(fd)

    def test_production_snapshot_rejects_a_regular_temp_tree(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "iio:device77"
            directory.mkdir()
            with self.assertRaisesRegex(ValueError, "canonical /sys/devices"):
                setup.snapshot_iio(directory, "/dev/iio:device77")

    def test_open_node_is_readonly_nonblocking_cloexec_nofollow(self):
        fake = type("Info", (), {"st_mode": 0o020600, "st_rdev": os.makedev(240, 77)})()
        with patch.object(setup.os, "open", return_value=7) as opened, patch.object(setup.os, "fstat", return_value=fake):
            self.assertEqual(setup.MetadataBackend.open_node("/dev/iio:device77", 240, 77), 7)
        self.assertEqual(opened.call_args.args, ("/dev/iio:device77", os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW))

    def test_node_fstat_mismatch_closes_without_reading(self):
        fake = type("Info", (), {"st_mode": 0o100600, "st_rdev": 0})()
        with patch.object(setup.os, "open", return_value=7), patch.object(setup.os, "fstat", return_value=fake), patch.object(setup.os, "close") as closed, patch.object(setup.os, "read") as read:
            with self.assertRaises(ValueError):
                setup.MetadataBackend.open_node("/dev/iio:device77", 240, 77)
        closed.assert_called_once_with(7)
        read.assert_not_called()

    def test_node_validation_error_survives_close_failure(self):
        fake = type("Info", (), {"st_mode": 0o100600, "st_rdev": 0})()
        with patch.object(setup.os, "open", return_value=7), patch.object(setup.os, "fstat", return_value=fake), patch.object(setup.os, "close", side_effect=OSError("close failed")):
            with self.assertRaisesRegex(ValueError, "opened IIO device changed") as caught:
                setup.MetadataBackend.open_node("/dev/iio:device77", 240, 77)
        self.assertIn("close failed", caught.exception.__notes__[0])

    def test_short_write_error_survives_both_descriptor_close_failures(self):
        with patch.object(setup.os, "open", side_effect=[8, 9]), patch.object(setup.os, "write", return_value=1), patch.object(setup.os, "close", side_effect=OSError("close failed")) as closed:
            with self.assertRaisesRegex(OSError, "short sysfs write") as caught:
                setup.MetadataBackend.write_at(7, "buffer/enable", "1")
        self.assertEqual(closed.call_count, 2)
        self.assertEqual(len(caught.exception.__notes__), 2)


class VirtualMetadata:
    """Path-like metadata tree: exercises the REAL snapshot, never real /sys."""
    directory = "/sys/devices/fake/8-6/8-6:1.0/iio:device77"
    interface = "/sys/devices/fake/8-6/8-6:1.0"
    usb = "/sys/devices/fake/8-6"
    driver = "/sys/bus/usb/drivers/gs_native"
    node = "/dev/iio:device77"

    def __init__(self):
        self.files = {self.directory + "/name": setup.IIO_NAME,
                      self.directory + "/dev": "240:77",
                      self.directory + "/buffer/enable": "0",
                      self.directory + "/buffer_stream_active": "0",
                      self.directory + "/buffer_push_errors": "0",
                      self.interface + "/bInterfaceNumber": "00",
                      self.usb + "/idVendor": "3537", self.usb + "/idProduct": "109c",
                      self.usb + "/busnum": "8", self.usb + "/devnum": "17",
                      self.driver + "/module/srcversion": setup.MODULE_SRCVERSION}
        for relative, value in state()["settings"].items():
            self.files[self.directory + "/" + relative] = value
        for index, name in enumerate(setup.CHANNELS):
            self.files[self.directory + f"/scan_elements/{name}_index"] = str(index)
            self.files[self.directory + f"/scan_elements/{name}_type"] = state()["types"][name]
        self.dirs = {str(parent) for name in self.files for parent in PurePosixPath(name).parents}
        self.dirs.add(self.directory)
        self.inodes = {name: index + 700 for index, name in enumerate(sorted(self.dirs))}
        self.node_character = True
        self.node_minor = 77
        self.stat_hook = None
        self.calls = {}

    def read(self, path):
        return self.files[str(path)]

    def path(self, value):
        tree = self
        class Entry:
            def __init__(self, value):
                self.value = str(PurePosixPath(str(value)))
            def __str__(self):
                return self.value
            def __fspath__(self):
                return self.value
            def __truediv__(self, name):
                return tree.path(self.value + "/" + name)
            def __eq__(self, other):
                return self.value == str(other)
            @property
            def name(self):
                return PurePosixPath(self.value).name
            @property
            def parent(self):
                return tree.path(PurePosixPath(self.value).parent)
            @property
            def parents(self):
                return [tree.path(parent) for parent in PurePosixPath(self.value).parents]
            def resolve(self, strict=True):
                if self.value == tree.interface + "/driver":
                    return tree.path(tree.driver)
                if self.value not in tree.dirs and self.value not in tree.files:
                    raise FileNotFoundError(self.value)
                return self
            def stat(self):
                tree.calls[self.value] = tree.calls.get(self.value, 0) + 1
                if tree.stat_hook:
                    tree.stat_hook(self.value, tree.calls[self.value])
                return type("Stat", (), {"st_dev": 19, "st_ino": tree.inodes[self.value], "st_mode": 0o040755})()
            def lstat(self):
                if self.value != tree.node:
                    raise AssertionError("unexpected node stat")
                return type("Stat", (), {"st_mode": 0o020600 if tree.node_character else 0o100600,
                                          "st_rdev": os.makedev(240, tree.node_minor)})()
            def is_file(self):
                return self.value in tree.files
            def exists(self):
                return self.value in tree.files or self.value in tree.dirs
            def glob(self, pattern):
                assert pattern == "*_en"
                return [tree.path(name) for name in tree.files if str(PurePosixPath(name).parent) == self.value and name.endswith("_en")]
        return Entry(value)

    def run(self):
        with patch.object(setup, "Path", side_effect=self.path), patch.object(setup, "_read", side_effect=self.read):
            return setup.snapshot_iio(self.directory, self.node)


class RealSnapshotVirtualTree(unittest.TestCase):
    def test_real_snapshot_validates_complete_virtual_metadata_without_open(self):
        tree = VirtualMetadata()
        with patch.object(setup.os, "open", side_effect=AssertionError("metadata inspection must not open device")):
            snapshot = tree.run()
        self.assertEqual(snapshot["settings"], state()["settings"])
        self.assertEqual(snapshot["usb"]["pid"], "109c")
        self.assertEqual(snapshot["usb"]["driver"], "gs_native")
        self.assertEqual(snapshot["buffer_enable"], "0")
        self.assertEqual(snapshot["module_srcversion"], setup.MODULE_SRCVERSION)
        self.assertEqual(snapshot["types"], state()["types"])
        self.assertFalse(any("_raw" in name for name in tree.calls))

    def test_wrong_layout_index_type_name_identity_and_interface_are_rejected(self):
        examples = [(VirtualMetadata.directory + "/name", "wrong"),
                    (VirtualMetadata.usb + "/idVendor", "045e"),
                    (VirtualMetadata.usb + "/idProduct", "100a"),
                    (VirtualMetadata.interface + "/bInterfaceNumber", "01"),
                    (VirtualMetadata.driver + "/module/srcversion", "OLD"),
                    (VirtualMetadata.directory + "/scan_elements/in_accel_x_index", "1"),
                    (VirtualMetadata.directory + "/scan_elements/in_count0_type", "le:s64/64>>0"),
                    (VirtualMetadata.directory + "/scan_elements/in_timestamp_en", "2"),
                    (VirtualMetadata.directory + "/buffer_stream_active", "unknown"),
                    (VirtualMetadata.directory + "/buffer/length", "1")]
        for path, value in examples:
            with self.subTest(path=path):
                tree = VirtualMetadata()
                tree.files[path] = value
                with self.assertRaises(ValueError):
                    tree.run()

    def test_other_driver_rejected(self):
        tree = VirtualMetadata()
        tree.driver = "/sys/bus/usb/drivers/xpad"
        with self.assertRaisesRegex(ValueError, "gs_native"):
            tree.run()

    def test_missing_or_additional_scan_channel_rejected(self):
        tree = VirtualMetadata()
        del tree.files[tree.directory + "/scan_elements/in_count0_en"]
        with self.assertRaisesRegex(ValueError, "eight"):
            tree.run()
        tree = VirtualMetadata()
        tree.files[tree.directory + "/scan_elements/in_other_en"] = "0"
        with self.assertRaisesRegex(ValueError, "eight"):
            tree.run()

    def test_wrong_node_type_or_number_rejected_without_open(self):
        for regular, minor in ((True, 77), (False, 78)):
            tree = VirtualMetadata()
            tree.node_character = not regular
            tree.node_minor = minor
            with self.subTest(regular=regular), self.assertRaisesRegex(ValueError, "node type or device number"):
                tree.run()

    def test_inode_changes_during_snapshot_rejected(self):
        for changed_path in (VirtualMetadata.directory, VirtualMetadata.usb, VirtualMetadata.interface,
                             str(PurePosixPath(VirtualMetadata.usb).parent)):
            with self.subTest(path=changed_path):
                tree = VirtualMetadata()
                def hook(path, count):
                    if path == changed_path and count == 2:
                        tree.inodes[path] += 100
                tree.stat_hook = hook
                with self.assertRaisesRegex(ValueError, "instance changed"):
                    tree.run()


if __name__ == "__main__":
    unittest.main()
