#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline regression of the observer's bounded USB re-enumeration window.

These synthetic status records reproduce the observed empty-metadata sequence;
they are not evidence of a successful hardware bootstrap. No host devices,
services or clocks are consulted.
"""
import copy
from dataclasses import FrozenInstanceError
import importlib.util
import math
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_observation", ROOT / "tools/native/bootstrap_observation.py")
policy = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = policy
SPEC.loader.exec_module(policy)

PORT = "1-3.2"


def diagnostic(error=0, returncode=0, timed_out=False):
    """Real manager field layout; identifiers and output are synthetic."""
    return {
        "version": 1, "returncode": returncode, "timed_out": timed_out,
        "source_instance": "synthetic-source-100a-instance",
        "reported_kernel_status": {
            "state": 8 if error else 7, "error": error,
            "failed_stage": 3 if error else 0, "pad": 0, "imu": 0 if error else 1,
            "handover": 0 if error else 1, "port_token": 1, "instance_token": 2,
        },
        "combined_output": "", "output_bytes": 0, "output_sha256": "0" * 64,
        "output_scope": "supervisor-bounded combined stdout/stderr, not the complete original child stream",
        "excerpt_truncated": False,
    }


def metadata_error(field="bConfigurationValue", port=PORT, base=None):
    if base is None:
        base = 16 if field in ("idVendor", "idProduct") else 10
    return f"Empty USB metadata: /sys/bus/usb/devices/{port}/{field} (base {base})"


def status(phase="bootstrapping", *, port=PORT, error="", port_errors=None,
           busy=None, diag=None):
    if busy is None:
        busy = phase == "bootstrapping"
    return {
        "ok": True, "paused": False, "scan_error": "",
        "port_errors": {} if port_errors is None else port_errors,
        "devices": {port: {
            "pid": "109c" if phase == "active" else "100a",
            "phase": phase, "error": error, "busy": busy,
            "bootstrap_diagnostic": {} if diag is None else diag,
        }},
        "recent_failures": [],
    }


class StartupObservationTests(unittest.TestCase):
    def window(self, port=PORT):
        return policy.StartupWindow(port, 90.0)

    def rejected(self, value, *, now=12.0):
        with self.assertRaises(policy.ObservationError):
            self.window().check_status(value, now)

    def test_observed_empty_configuration_does_not_cancel_live_bootstrap(self):
        window = self.window()
        history = [{
            "port": PORT, "source_instance": "old-removed-instance",
            "origin_pid": "100a", "message": "Historical ENODEV",
            "bootstrap_diagnostic": diagnostic(-19, 1),
            "resolution": "physically_absent",
        }]
        sequence = [
            (0.5, status("waiting_input"), "waiting_input", False),
            (2.0, status(), "bootstrapping", False),
            (2.25, status(port_errors={PORT: metadata_error()}), "bootstrapping", True),
            (2.75, status(port_errors={PORT: "USB metadata changed during enumeration"}),
             "bootstrapping", True),
            (3.25, status("locating"), "locating", False),
            (3.75, status("attesting"), "attesting", False),
            (4.25, status("active", diag=diagnostic()), "active", False),
        ]
        for now, sample, phase, quarantined in sequence:
            sample["recent_failures"] = copy.deepcopy(history)
            before = copy.deepcopy(sample)
            result = window.check_status(sample, now)
            self.assertEqual((result.phase, result.quarantined), (phase, quarantined))
            self.assertEqual(sample, before, "Observation must not alter recorded evidence")

    def test_disappeared_scan_is_not_a_ready_device(self):
        window = self.window()
        sample = status()
        sample["devices"] = {}
        result = window.check_status(sample, 0.1)
        self.assertIsNone(result.phase)
        self.assertFalse(result.quarantined)
        self.assertTrue(window.check_scan({PORT: metadata_error()}, 1.0))
        self.assertFalse(window.check_scan({}, 1.5))
        # A clean external scan alone never yields an active observation.
        self.assertIsNone(window.check_status(sample, 2.0).phase)
        sample["port_errors"] = {PORT: metadata_error()}
        with self.assertRaises(policy.ObservationError):
            window.check_status(sample, 2.5)

    def test_result_cannot_be_rewritten_from_quarantine_to_ready(self):
        result = self.window().check_status(status(port_errors={PORT: metadata_error()}), 1.0)
        with self.assertRaises(FrozenInstanceError):
            result.quarantined = False

    def test_window_expires_instead_of_restarting_after_repeated_metadata_gaps(self):
        window = self.window()
        for now in (1.0, 15.0, 55.0, 89.9):
            self.assertTrue(window.check_status(
                status(port_errors={PORT: metadata_error()}), now).quarantined)
        for now in (90.0, 90.1):
            with self.subTest(now=now), self.assertRaises(policy.ObservationError):
                window.check_status(status(port_errors={PORT: metadata_error()}), now)

    def test_last_moment_readiness_cannot_override_original_deadline(self):
        window = self.window()
        self.assertEqual(window.check_status(status("active"), 89.9).phase, "active")
        for now in (90.0, 90.1):
            with self.subTest(now=now), self.assertRaises(policy.ObservationError):
                window.check_status(status("active"), now)

    def test_scan_gap_and_clean_scan_both_respect_deadline(self):
        window = self.window()
        for errors in ({PORT: metadata_error()}, {}):
            for now in (90.0, 90.1):
                with self.subTest(errors=errors, now=now), self.assertRaises(policy.ObservationError):
                    window.check_scan(errors, now)

    def test_invalid_clock_cannot_make_deadline_unbounded(self):
        for now in (math.nan, math.inf, -math.inf, None, "1", True):
            with self.subTest(now=now), self.assertRaises(policy.ObservationError):
                self.window().check_deadline(now)

    def test_invalid_deadline_or_port_is_rejected(self):
        for port, deadline in ((PORT, math.nan), (PORT, math.inf), (PORT, None),
                               (PORT, "90"), (PORT, True), ("", 90.0),
                               ("1-3.2/../1-4", 90.0), ("1-3.2:1.0", 90.0)):
            with self.subTest(port=port, deadline=deadline), self.assertRaises(policy.ObservationError):
                window = policy.StartupWindow(port, deadline)
                window.check_deadline(1.0)

    def test_only_known_device_metadata_and_expected_numeric_bases_are_quarantined(self):
        for field in ("idVendor", "idProduct", "bConfigurationValue", "busnum", "devnum"):
            for phase in ("bootstrapping", "locating", "attesting"):
                with self.subTest(field=field, phase=phase):
                    sample = status(phase, port_errors={PORT: metadata_error(field)})
                    self.assertTrue(self.window().check_status(sample, 1.0).quarantined)
                    self.assertTrue(self.window().check_scan(sample["port_errors"], 1.0))

    def test_reenumeration_phrase_is_quarantined_only_on_exact_target(self):
        self.assertTrue(self.window().check_scan(
            {PORT: "USB metadata changed during enumeration"}, 1.0))
        for text in ("USB metadata changed during enumeration ",
                     "USB metadata changed during enumeration: unexpected", ""):
            with self.subTest(text=text), self.assertRaises(policy.ObservationError):
                self.window().check_scan({PORT: text}, 1.0)

    def test_quarantine_does_not_hide_nontransient_or_unclassified_metadata_errors(self):
        errors = [
            metadata_error("bInterfaceNumber"), metadata_error("bNumInterfaces"),
            metadata_error("idVendor", base=10), metadata_error("devnum", base=16),
            metadata_error().replace("/sys/bus/usb/", "/sys/devices/usb/"),
            metadata_error().replace("/1-3.2/", "/1-3.2:1.0/"),
            metadata_error().replace("/1-3.2/", "/1-3.2/../1-3.2/"),
            "Invalid USB metadata: /sys/bus/usb/devices/1-3.2/devnum (base 10)",
            "Permission denied: /sys/bus/usb/devices/1-3.2/devnum",
            "invalid literal for int() with base 10: ''",
            "Empty USB metadata", "", None, {"error": metadata_error()},
        ]
        for text in errors:
            with self.subTest(text=text):
                self.rejected(status(port_errors={PORT: text}))
                with self.assertRaises(policy.ObservationError):
                    self.window().check_scan({PORT: text}, 1.0)

    def test_initial_input_wait_and_active_runtime_have_no_metadata_exception(self):
        for phase in ("waiting_input", "active"):
            with self.subTest(phase=phase):
                self.rejected(status(phase, port_errors={PORT: metadata_error()}))

    def test_same_vid_pid_on_another_port_does_not_satisfy_target(self):
        self.rejected(status("active", port="1-3.3"))
        sample = status()
        sample["devices"]["1-3.3"] = copy.deepcopy(sample["devices"][PORT])
        self.rejected(sample)
        for errors in ({"1-3.3": metadata_error(port="1-3.3")},
                       {PORT: metadata_error(port="1-3.3")},
                       {PORT: metadata_error(), "1-3.3": metadata_error(port="1-3.3")}):
            with self.subTest(errors=errors):
                self.rejected(status(port_errors=errors))
                with self.assertRaises(policy.ObservationError):
                    self.window().check_scan(errors, 1.0)

    def test_policy_has_no_fixed_usb_port(self):
        for port in ("2-7", "11-3.2.4"):
            with self.subTest(port=port):
                window = self.window(port)
                self.assertTrue(window.check_status(
                    status(port=port, port_errors={port: metadata_error(port=port)}), 1.0).quarantined)
                self.assertEqual(window.check_status(status("active", port=port), 2.0).phase, "active")

    def test_primary_error_is_fatal_even_with_expected_metadata_gap(self):
        self.rejected(status(error="Bootstrap failed: No such device",
                             port_errors={PORT: metadata_error()}))
        self.rejected(status("failed", error="original -19 retained"))
        self.rejected(status("blocked", error="Unowned new 109c instance; no END attempted"))

    def test_new_negative_bootstrap_diagnostic_is_never_treated_as_old_history(self):
        for diag in (diagnostic(-19, 1), diagnostic(-4, 1),
                     diagnostic(-110, 1, True), diagnostic(0, 1),
                     diagnostic(0, 0, True)):
            with self.subTest(diag=diag):
                self.rejected(status(diag=diag, port_errors={PORT: metadata_error()}))
                self.rejected(status("active", diag=diag))

    def test_incomplete_new_diagnostic_does_not_attest_health(self):
        for diag in ({"returncode": 0}, {"timed_out": False},
                     {"returncode": 0, "timed_out": False, "reported_kernel_status": None}):
            with self.subTest(diag=diag):
                self.rejected(status(diag=diag))
        for field, value in (("error", "0"), ("error", False)):
            diag = diagnostic()
            diag["reported_kernel_status"][field] = value
            self.rejected(status(diag=diag))

    def test_failure_at_global_scan_level_cannot_use_port_quarantine(self):
        sample = status(port_errors={PORT: metadata_error()})
        sample["scan_error"] = "Incomplete ownership view"
        self.rejected(sample)

    def test_busy_is_not_an_implicit_permission_to_ignore_other_failures(self):
        self.rejected(status(busy=False))
        sample = status()
        sample["paused"] = True
        self.rejected(sample)
        sample = status()
        sample["ok"] = False
        self.rejected(sample)

    def test_unknown_or_wrongly_typed_schema_fails_closed(self):
        for field in ("ok", "paused", "scan_error", "port_errors", "devices"):
            sample = status()
            del sample[field]
            with self.subTest(missing=field):
                self.rejected(sample)
        for field in ("pid", "phase", "error", "busy", "bootstrap_diagnostic"):
            sample = status()
            del sample["devices"][PORT][field]
            with self.subTest(missing_entry=field):
                self.rejected(sample)
        for field, value in (("ok", 1), ("paused", 0), ("scan_error", None),
                             ("port_errors", []), ("devices", [])):
            sample = status()
            sample[field] = value
            with self.subTest(field=field, value=value):
                self.rejected(sample)
        for field, value in (("pid", "105e"), ("phase", "mystery"), ("error", None),
                             ("busy", 1), ("bootstrap_diagnostic", [])):
            sample = status()
            sample["devices"][PORT][field] = value
            with self.subTest(field=field, value=value):
                self.rejected(sample)
        for bad in (None, [], True, "status"):
            with self.subTest(bad=bad):
                self.rejected(bad)
        for errors in (None, [], True, "errors"):
            with self.subTest(errors=errors), self.assertRaises(policy.ObservationError):
                self.window().check_scan(errors, 1.0)

    def test_wrong_pid_cannot_claim_bootstrap_success(self):
        sample = status("active")
        sample["devices"][PORT]["pid"] = "100a"
        self.rejected(sample)
        sample = status()
        sample["devices"][PORT]["pid"] = "109c"
        self.rejected(sample)

    def test_runtime_accepts_clean_active_only_and_keeps_old_failure_history(self):
        sample = status("active", diag=diagnostic())
        sample["recent_failures"] = [{"bootstrap_diagnostic": diagnostic(-19, 1)}]
        self.assertIsNone(policy.check_runtime_status(sample, PORT))
        for phase in ("waiting_input", "bootstrapping", "locating", "attesting"):
            with self.subTest(phase=phase), self.assertRaises(policy.ObservationError):
                policy.check_runtime_status(status(phase), PORT)

    def test_runtime_rejects_metadata_gap_instead_of_reopening_start_window(self):
        sample = status("active", port_errors={PORT: metadata_error()})
        with self.assertRaises(policy.ObservationError):
            policy.check_runtime_status(sample, PORT)
        sample = status("active")
        sample["devices"] = {}
        with self.assertRaises(policy.ObservationError):
            policy.check_runtime_status(sample, PORT)
        with self.assertRaises(policy.ObservationError):
            policy.check_runtime_status(status("active", port="1-3.3"), PORT)


class VirtualStartup:
    """Clock and I/O callbacks, with no real waiting or privileged side effects."""
    def __init__(self, samples, inventories=None, start=0.0):
        self.samples = list(samples)
        self.inventories = list(inventories or [({PORT: {"synthetic": True}}, {})])
        self.time = start
        self.calls = []
        self.events = []
        self.status_delay = 0.0
        self.attest_delay = 0.0
        self.journal_error = None

    def now(self):
        return self.time

    def read_status(self):
        self.calls.append("status")
        self.time += self.status_delay
        sample = self.samples[0]
        if len(self.samples) > 1:
            self.samples.pop(0)
        return copy.deepcopy(sample)

    def read_inventory(self):
        self.calls.append("inventory")
        inventory = self.inventories[0]
        if len(self.inventories) > 1:
            self.inventories.pop(0)
        return copy.deepcopy(inventory)

    def attest(self, inventory):
        self.calls.append("attest")
        self.time += self.attest_delay
        if set(inventory) != {PORT}:
            raise AssertionError("The loop offered an unverified/foreign inventory")
        return {"synthetic_proof": "exact-instance-and-lease-attested"}

    def check_journal(self):
        self.calls.append("journal")
        if self.journal_error:
            raise self.journal_error

    def emit(self, event, data):
        self.events.append((event, data))

    def wait(self, duration):
        if not (0 < duration <= 1.0):
            raise AssertionError("Expected bounded observation wait")
        self.calls.append("wait")
        self.time += duration

    def run(self):
        return policy.wait_for_native(
            policy.StartupWindow(PORT, 90.0), read_status=self.read_status,
            read_inventory=self.read_inventory, attest=self.attest,
            check_journal=self.check_journal, emit=self.emit,
            now=self.now, wait=self.wait)


class ActualObservationLoopTests(unittest.TestCase):
    def test_real_abort_shape_recovers_only_after_clean_active_and_full_attestation(self):
        fake = VirtualStartup([
            status("waiting_input"),
            status(port_errors={PORT: metadata_error()}),
            status("locating", port_errors={PORT: "USB metadata changed during enumeration"}),
            status("attesting"), status("active", diag=diagnostic()),
        ])
        proof, final_status = fake.run()
        self.assertEqual(proof, {"synthetic_proof": "exact-instance-and-lease-attested"})
        self.assertEqual(final_status["devices"][PORT]["phase"], "active")
        self.assertEqual(fake.calls.count("attest"), 1)
        self.assertEqual(fake.calls.count("inventory"), 1)
        self.assertGreaterEqual(fake.calls.count("journal"), 2)
        self.assertIn("wait", fake.calls)

    def test_cached_active_plus_fresh_metadata_gap_waits_and_revalidates(self):
        fake = VirtualStartup(
            [status("active"), status("active")],
            [({}, {PORT: metadata_error("devnum")}), ({PORT: {"synthetic": True}}, {})])
        fake.run()
        self.assertEqual(fake.calls.count("status"), 2)
        self.assertEqual(fake.calls.count("inventory"), 2)
        self.assertEqual(fake.calls.count("attest"), 1)
        self.assertLess(fake.calls.index("wait"), fake.calls.index("attest"))

    def test_blocking_status_that_returns_active_too_late_is_not_success(self):
        fake = VirtualStartup([status("active")], start=89.9)
        fake.status_delay = 0.2
        with self.assertRaises(policy.ObservationError):
            fake.run()
        self.assertNotIn("attest", fake.calls)
        self.assertNotIn("inventory", fake.calls)

    def test_repeated_quarantine_does_not_restart_start_budget(self):
        fake = VirtualStartup([status(port_errors={PORT: metadata_error()})], start=89.9)
        with self.assertRaises(policy.ObservationError):
            fake.run()
        self.assertGreaterEqual(fake.time, 90.0)
        self.assertNotIn("attest", fake.calls)
        self.assertNotIn("inventory", fake.calls)
        self.assertIn("journal", fake.calls)

    def test_last_attestation_taking_past_deadline_cannot_open_observer(self):
        fake = VirtualStartup([status("active")], start=89.9)
        fake.attest_delay = 0.2
        with self.assertRaises(policy.ObservationError):
            fake.run()
        self.assertEqual(fake.calls.count("attest"), 1)
        self.assertGreater(fake.time, 90.0)

    def test_quarantine_cleared_notification_cannot_push_success_past_deadline(self):
        fake = VirtualStartup([
            status(port_errors={PORT: metadata_error()}), status("active")], start=89.4)
        original_emit = fake.emit

        def delayed_notification(event, data):
            original_emit(event, data)
            if event == "metadata_quarantine_cleared":
                self.assertAlmostEqual(fake.time, 89.9)
                fake.time += 0.2

        fake.emit = delayed_notification
        with self.assertRaises(policy.ObservationError):
            fake.run()
        self.assertEqual(fake.calls.count("attest"), 1)
        self.assertAlmostEqual(fake.time, 90.1)

    def test_kernel_failure_is_not_ignored_during_quarantine(self):
        fake = VirtualStartup([status(port_errors={PORT: metadata_error()})])
        fake.journal_error = policy.ObservationError("Synthetic new USB kernel error")
        with self.assertRaisesRegex(policy.ObservationError, "Synthetic new USB kernel error"):
            fake.run()
        self.assertNotIn("attest", fake.calls)

    def test_foreign_inventory_cannot_be_hidden_by_target_metadata_gap(self):
        fake = VirtualStartup([status("active")], [
            ({"1-3.3": {"synthetic": True}}, {PORT: metadata_error()})])
        with self.assertRaises(policy.ObservationError):
            fake.run()
        self.assertNotIn("attest", fake.calls)


if __name__ == "__main__":
    unittest.main()
