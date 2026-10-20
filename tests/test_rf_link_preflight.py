#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline RF preflight tests: fake filesystem, no real processes/devices."""
import importlib.util
import io
import json
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rf_link_preflight", ROOT / "tools/native/rf_link_preflight.py")
rf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rf)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        usb = self.root / "sys/bus/usb/devices"
        usb.mkdir(parents=True)
        boot = self.root / "proc/sys/kernel/random/boot_id"
        boot.parent.mkdir(parents=True)
        boot.write_text("synthetic-boot")
        self.add_receiver()
        self.run = Mock(side_effect=self.response)

    def add_receiver(self, name="1-2", vid="3537", pid="109c"):
        path = self.root / "sys/bus/usb/devices" / name
        path.mkdir()
        for key, value in {"idVendor": vid, "idProduct": pid, "busnum": "1",
                           "devnum": "7", "devpath": "2"}.items():
            (path / key).write_text(value)
        interface = path.parent / (name + ":1.0")
        interface.mkdir()
        driver = self.root / "sys/bus/usb/drivers/gs_native"
        driver.mkdir(parents=True, exist_ok=True)
        (interface / "driver").symlink_to(driver)
        return path

    @staticmethod
    def response(command, **kwargs):
        value = {"ok": True, "paused": False, "scan_error": "", "port_errors": {},
                 "devices": {}}
        return SimpleNamespace(returncode=0, stdout=json.dumps(value) if command[0].endswith("gamesir-native") else "synthetic metadata", stderr="")

    def collect(self):
        return rf.collect(self.root, run=self.run, kernel_release="synthetic-kernel")

    def test_default_plan_never_collects_or_starts_any_process(self):
        with patch.object(rf, "collect", side_effect=AssertionError("live collection forbidden")), redirect_stdout(io.StringIO()):
            self.assertEqual(rf.main([]), 0)
        self.assertFalse(rf.plan()["capture_ready"])

    def test_inspect_requires_root_but_does_not_prompt_itself(self):
        with patch.object(rf.os, "geteuid", return_value=1000), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rf.main(["inspect"])

    def test_cached_identity_and_binding_are_read_without_serial(self):
        report = self.collect()
        self.assertEqual(report["receivers"][0]["interfaces"], {"1-2:1.0": "gs_native"})
        self.assertEqual(report["receivers"][0]["pid"], "109c")
        self.assertNotIn("serial", json.dumps(report))
        self.assertFalse(report["capture_ready"])

    def test_no_monitor_node_is_reported_without_loading_module(self):
        report = self.collect()
        self.assertIn("usbmon node absent; no automatic module load", report["blockers"])
        self.assertEqual(self.run.call_count, len(rf.COMMANDS))
        for call, (_, expected) in zip(self.run.call_args_list, rf.COMMANDS):
            self.assertEqual(call.args[0], list(expected))
            self.assertNotIn("shell", call.kwargs)
            self.assertEqual(call.kwargs["timeout"], 10)

    def test_multiple_receivers_prevent_target_guess_and_any_command(self):
        self.add_receiver("1-3")
        report = self.collect()
        self.assertTrue(report["blockers"])
        self.run.assert_not_called()

    def test_foreign_and_unsupported_products_never_selected(self):
        path = self.root / "sys/bus/usb/devices/1-2"
        for vid, pid in (("045e", "109c"), ("3537", "ffff")):
            (path / "idVendor").write_text(vid)
            (path / "idProduct").write_text(pid)
            self.assertEqual(self.collect()["receivers"], [])
        self.run.assert_not_called()

    def test_zzz_does_not_become_the_standard_model_test(self):
        (self.root / "sys/bus/usb/devices/1-2/idProduct").write_text("105e")
        self.assertTrue(self.collect()["blockers"])
        self.run.assert_not_called()

    def test_blocked_manager_preserves_original_diagnostic_and_stops(self):
        original = {"paused": False, "devices": {"1-2": {"phase": "blocked", "error": "return timeout",
                     "bootstrap_diagnostic": {"error": -110, "failed_stage": 5}}}}
        self.run.side_effect = None
        self.run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(original), stderr="")
        report = self.collect()
        self.assertEqual(json.loads(report["reads"]["manager"]["stdout"]), original)
        self.assertTrue(report["blockers"])
        self.assertEqual(self.run.call_count, 1)

    def test_failed_read_is_not_retried_or_replaced_by_another_operation(self):
        self.run.side_effect = None
        self.run.return_value = SimpleNamespace(returncode=1, stdout="", stderr="access denied")
        report = self.collect()
        self.assertEqual(report["blockers"], ["Read failed: manager"])
        self.assertEqual(self.run.call_count, 1)

    def test_missing_manager_fields_are_not_treated_as_empty_healthy_state(self):
        self.run.side_effect = None
        self.run.return_value = SimpleNamespace(returncode=0, stdout="{}", stderr="")
        with self.assertRaises(ValueError):
            self.collect()
        self.assertEqual(self.run.call_count, 1)

    def test_unexpected_regular_monitor_file_is_rejected(self):
        node = self.root / "dev/usbmon1"
        node.parent.mkdir()
        node.write_text("not a device; never read this payload")
        self.assertIn("Monitor node is not a character device", self.collect()["blockers"])

    def test_changed_cached_metadata_is_not_silently_adopted(self):
        original = self.response
        def changed(command, **kwargs):
            if command[0].endswith("journalctl"):
                (self.root / "sys/bus/usb/devices/1-2/devnum").write_text("8")
            return original(command, **kwargs)
        self.run.side_effect = changed
        self.assertIn("Receiver/boot metadata changed during preflight; no retry", self.collect()["blockers"])


if __name__ == "__main__":
    unittest.main()
