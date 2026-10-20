#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Reconnect regressions using only the existing in-memory manager backend."""
import copy
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reconnect_policy_fixture", ROOT / "tests/test_service_manager.py")
fixture = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fixture
spec.loader.exec_module(fixture)
service, device, proof = fixture.service, fixture.device, fixture.proof

HEALTHY = "pid=109c state=1 error=0 OUT=1 session=1 pad=0 imu=99"
FAULT = "pid=109c state=2 error=-5 OUT=1 session=0 pad=0 imu=99"
PORT = "2-3.4"


class Reconnect(unittest.TestCase):
    def setUp(self):
        self.host = fixture.Fake([device()])
        self.manager = service.Manager(self.host, lambda: self.host.now)

    def tick(self, count=1):
        for _ in range(count):
            self.manager.tick()

    def boot(self, generation=2):
        """Complete the already available normal 100a acquisition and handoff."""
        self.tick(2)
        original = self.host.devices[PORT]
        native = device(PORT, "109c", generation, "gs_native", original.parent)
        self.host.devices[PORT] = native
        self.host.complete("bootstrap", PORT, output=proof(native))
        self.tick(2)
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        return native

    def pending_info(self):
        native = self.boot()
        self.tick()
        job = self.host.jobs[-1]
        self.assertEqual(job["operation"], "info")
        self.assertIsNone(job["result"])
        return native, job

    def replacement(self, generation=3, **changes):
        fresh = device(generation=generation, **changes)
        self.host.devices[PORT] = fresh
        return fresh

    def assert_reclaimed(self, fresh):
        self.tick(3)
        entry = self.manager.entries[PORT]
        self.assertEqual(entry.device.token, fresh.token)
        self.assertEqual(entry.device.parent, fresh.parent)
        self.assertIn(entry.phase, ("checking_start", "bootstrapping"))
        self.assertEqual(entry.error, "")
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 2)
        self.assertFalse(any(op in ("end", "restore", "resume") for op, _ in self.host.calls))
        self.assertEqual(self.manager.recent_failures, [])

    def partial(self, error="Temporary incomplete USB metadata"):
        scan = service.Scan()
        scan.errors[PORT] = error
        return scan

    def scan_sequence(self, snapshots):
        original = self.host.scan
        pending = list(snapshots)
        self.host.scan = lambda: pending.pop(0) if pending else original()

    def test_completed_passive_read_does_not_release_or_poison_fresh_xpad_instance(self):
        self.pending_info()
        fresh = self.replacement()
        self.host.complete("info", output=HEALTHY)
        self.assert_reclaimed(fresh)

    def test_reconnect_between_tick_snapshot_and_passive_completion_is_fresh_start(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        original = self.host.poll
        fresh = device(generation=3)

        def poll(job):
            self.host.devices[PORT] = fresh
            self.host.poll = original
            return original(job)

        self.host.poll = poll
        self.assert_reclaimed(fresh)

    def test_reconnect_before_next_getter_is_equivalent_to_pending_getter(self):
        self.boot()
        self.assert_reclaimed(self.replacement())

    def test_reconnect_during_passive_guard_does_not_latch_obsolete_instance_error(self):
        self.boot()
        original = self.host.observe_guard
        fresh = device(generation=3)

        def guard(old):
            self.host.devices[PORT] = fresh
            self.host.observe_guard = original
            raise getattr(service, "StatusChanged", service.Unsafe)("Native status instance replaced")

        self.host.observe_guard = guard
        self.assert_reclaimed(fresh)

    def test_busy_child_then_reconnect_has_same_safe_new_instance_handling(self):
        self.pending_info()
        fresh = self.replacement()
        self.host.complete("info", rc=service.STATUS_BUSY_EXIT, output="Native control FD busy")
        self.assert_reclaimed(fresh)

    def test_guard_busy_backoff_does_not_quarantine_next_connection(self):
        self.boot()
        self.host.control_busy.add(PORT)
        self.tick()
        self.assertTrue(self.manager.entries[PORT].status_conflict)
        self.host.control_busy.clear()
        self.assert_reclaimed(self.replacement())

    def test_tick_snapshot_with_incomplete_metadata_cannot_consume_completed_read(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        self.scan_sequence([self.partial()])
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assertEqual(self.manager.entries[PORT].error, "")
        self.assertIn(PORT, self.manager.status()["port_errors"])
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assertEqual(self.manager.entries[PORT].error, "")

    def test_second_scan_incomplete_cannot_overwrite_completed_real_fault(self):
        self.pending_info()
        self.host.complete("info", rc=1, output=FAULT)
        self.scan_sequence([dict(self.host.devices), self.partial()])
        before = len(self.host.jobs)
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "failed")
        self.assertIn("runtime fault", self.manager.entries[PORT].error)
        self.assertEqual(len(self.host.jobs), before)

    def test_completed_fault_and_partial_metadata_survive_manager_restart(self):
        self.pending_info()
        self.host.complete("info", rc=1, output=FAULT)
        self.scan_sequence([self.partial()])
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "failed")
        self.assertIn("runtime fault", self.manager.entries[PORT].error)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.assertIn("runtime fault", self.manager.entries[PORT].error)
        self.assertTrue(any("runtime fault" in record["message"]
                            for record in self.manager.recent_failures))
        self.replacement()
        self.tick(3)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)

    def test_second_scan_incomplete_then_reconnect_does_not_poison_replacement(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        self.scan_sequence([dict(self.host.devices), self.partial()])
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assert_reclaimed(self.replacement())

    def test_completed_result_is_polled_once_across_repeated_metadata_deferrals(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        original = self.host.poll
        polled = []

        def poll(job):
            self.assertNotIn(id(job), polled, "Completed child stdout must not be consumed twice")
            polled.append(id(job))
            return original(job)

        self.host.poll = poll
        complete = dict(self.host.devices)
        self.scan_sequence([complete, self.partial(), complete, self.partial(), complete, complete])
        self.tick(3)
        self.assertEqual(len(polled), 1)
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assertEqual(self.manager.entries[PORT].error, "")
        self.assertIsNone(self.manager.entries[PORT].job)

    def test_temporary_metadata_failure_in_guard_is_not_a_runtime_failure(self):
        self.boot()
        original = self.host.observe_guard

        def guard(old):
            self.host.observe_guard = original
            raise service.StatusUnavailable("Synthetic enumeration in progress")

        self.host.observe_guard = guard
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assertEqual(self.manager.entries[PORT].error, "")
        self.assertIn(PORT, self.manager.status()["port_errors"])
        self.assertEqual(self.manager.recent_failures, [])
        self.tick()
        self.host.complete("info", output=HEALTHY)
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "active")

    def test_passive_global_scan_failure_preserves_completed_real_fault(self):
        self.pending_info()
        self.host.complete("info", rc=1, output=FAULT)
        self.host.scan_failure = True
        self.tick(2)
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.host.scan_failure = False
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "failed")
        self.assertIn("runtime fault", self.manager.entries[PORT].error)

    def test_completed_passive_fault_is_not_discarded_when_device_reconnects(self):
        self.pending_info()
        fresh = self.replacement()
        self.host.complete("info", rc=1, output=FAULT)
        self.tick(5)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertTrue(self.manager.recent_failures)
        self.assertTrue(any("runtime fault" in record["message"]
                            for record in self.manager.recent_failures))

    def test_unknown_status_failure_does_not_authorize_new_takeover(self):
        self.pending_info()
        fresh = self.replacement()
        self.host.complete("info", rc=1, output="Unclassified control failure: EIO")
        self.tick(5)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertTrue(self.manager.recent_failures)

    def test_successful_reconnects_work_within_budget_and_fourth_start_stays_bounded(self):
        self.boot()
        for generation in (3, 5):
            self.host.now += 3
            self.tick()
            self.host.complete("info", output=HEALTHY)
            fresh = self.replacement(generation=generation)
            self.tick(3)
            self.assertEqual(self.manager.entries[PORT].phase, "bootstrapping")
            native = replace(fresh, pid="109c", token=f"{PORT}/instance-{generation + 1}",
                             address=generation + 1, driver="gs_native")
            self.host.devices[PORT] = native
            self.host.complete("bootstrap", output=proof(native))
            self.tick(2)
            self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.host.now += 3
        self.tick()
        self.host.complete("info", output=HEALTHY)
        fresh = self.replacement(generation=7)
        self.tick(4)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual(self.manager.entries[PORT].phase, "blocked")
        self.assertIn("Three starts", self.manager.entries[PORT].error)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 3)
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 3)
        self.assertFalse(any(op in ("end", "restore") for op, _ in self.host.calls))

    def test_completed_safe_reconnect_persists_only_new_instance_ownership(self):
        self.pending_info()
        fresh = self.replacement()
        self.host.complete("info", output=HEALTHY)
        self.assert_reclaimed(fresh)
        native = replace(fresh, pid="109c", token=f"{PORT}/instance-4", address=4, driver="gs_native")
        self.host.devices[PORT] = native
        self.host.complete("bootstrap", output=proof(native))
        self.tick(2)
        self.assertEqual(self.host.saved["leases"][PORT]["device"]["token"], native.token)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(2)
        self.assertEqual(self.manager.entries[PORT].phase, "active")
        self.assertEqual(self.manager.entries[PORT].device.token, native.token)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 2)

    def test_real_fault_observed_before_reconnect_remains_latched(self):
        self.pending_info()
        self.host.complete("info", rc=1, output=FAULT)
        self.tick()
        self.assertEqual(self.manager.entries[PORT].phase, "failed")
        fresh = self.replacement()
        self.tick(10)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertTrue(self.manager.recent_failures)

    def test_bootstrap_failure_is_not_reclassified_as_normal_reconnect(self):
        self.tick(2)
        self.host.complete("bootstrap", rc=1, output="Original bootstrap failure")
        self.tick()
        original_error = self.manager.entries[PORT].error
        fresh = self.replacement()
        self.tick(10)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertTrue(original_error)
        self.assertTrue(self.manager.recent_failures)

    def test_unowned_native_binding_and_foreign_hub_or_owner_never_receive_commands(self):
        for changes in ({"pid": "109c", "driver": "gs_native"},
                        {"pid": "109c", "driver": "usbfs"},
                        {"driver": "gs_native"}, {"driver": "usbfs"},
                        {"parent": "different-hub-lifetime"}):
            with self.subTest(changes=changes):
                self.setUp()
                self.pending_info()
                fresh = self.replacement(**changes)
                self.host.complete("info", output=HEALTHY)
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)
                self.assertEqual(self.host.devices[PORT], fresh)

    def test_pause_during_read_never_reclaims_reconnected_device(self):
        self.pending_info()
        self.manager.command("release")
        fresh = self.replacement()
        self.host.complete("info", output=HEALTHY)
        self.tick(5)
        self.assertTrue(self.manager.paused)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        restart = service.Manager(self.host, lambda: self.host.now)
        restart.tick()
        self.assertTrue(restart.paused)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)

    def test_existing_released_error_is_not_silently_migrated_by_error_text(self):
        self.pending_info()
        self.host.complete("info", rc=1, output=FAULT)
        self.tick()
        self.replacement()
        self.tick(2)
        entry = self.manager.entries[PORT]
        entry.error = "Device changed during native status access"
        self.manager.remember(entry)
        saved = copy.deepcopy(self.host.saved)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(5)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertEqual(self.host.devices[PORT].driver, "xpad")
        self.assertTrue(saved["leases"] or saved["attempted"])

    def test_incomplete_first_getter_after_verified_claim_waits_without_reclaim(self):
        original = self.host.observe_guard

        def temporarily_unknown(expected):
            self.host.observe_guard = original
            raise service.StatusUnavailable("Incomplete native metadata after claim")

        self.host.observe_guard = temporarily_unknown
        self.tick()
        entry = self.manager.entries[PORT]
        self.assertEqual(entry.phase, "checking_start")
        self.assertEqual(entry.error, "")
        self.assertEqual(entry.device.driver, "gs_native")
        self.assertIn(PORT, self.manager.port_errors)
        self.assertEqual(self.host.calls, [("claim", PORT)])
        self.tick(2)
        self.assertEqual(entry.phase, "bootstrapping")
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_second_replacement_during_poll_requires_new_discovery_snapshot(self):
        self.pending_info()
        self.replacement(generation=3)
        self.host.complete("info", output=HEALTHY)
        original_poll = self.host.poll
        fresh = device(generation=4)

        def poll(job):
            self.host.devices[PORT] = fresh
            self.host.poll = original_poll
            return original_poll(job)

        self.host.poll = poll
        self.tick()
        self.assertNotIn(PORT, self.manager.entries)
        self.assertEqual(self.host.devices[PORT], fresh)
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 1)
        self.assert_reclaimed(fresh)

    def test_global_secondary_scan_failure_fences_other_device_claims(self):
        for source in ("completed-getter", "getter-guard", "changed-guard-rescan"):
            with self.subTest(source=source):
                self.setUp()
                if source == "completed-getter":
                    self.pending_info()
                    self.host.complete("info", output=HEALTHY)
                else:
                    self.boot()

                    def uncertain_guard(expected):
                        if source == "getter-guard":
                            raise service.StatusUnavailable("Global enumeration unavailable", global_scan=True)
                        raise service.StatusChanged("Old native instance changed")

                    self.host.observe_guard = uncertain_guard
                other = device(port="7-1", generation=9)
                self.host.devices[other.port] = other
                scan = self.host.scan
                scans = 0

                def initially_complete():
                    nonlocal scans
                    scans += 1
                    if scans == 2:
                        raise service.Unsafe("Global enumeration unavailable")
                    return scan()

                self.host.scan = initially_complete
                before = list(self.host.calls)
                self.tick()
                self.assertTrue(self.manager.scan_error)
                self.assertEqual(self.manager.entries[PORT].error, "")
                self.assertEqual(self.host.calls, before)
                self.assertEqual(self.host.devices[other.port], other)
                self.assertNotIn(other.port, self.manager.entries)

    def test_first_getter_global_unknown_stops_discovery_after_verified_claim(self):
        other = device(port="7-1", generation=9)
        self.host.devices[other.port] = other

        def globally_unknown(expected):
            raise service.StatusUnavailable("Global enumeration unavailable", global_scan=True)

        self.host.observe_guard = globally_unknown
        self.tick()
        self.assertTrue(self.manager.scan_error)
        self.assertEqual(self.manager.entries[PORT].error, "")
        self.assertEqual(self.manager.entries[PORT].device.driver, "gs_native")
        self.assertEqual(self.host.calls, [("claim", PORT)])
        self.assertEqual(self.host.devices[other.port], other)
        self.assertNotIn(other.port, self.manager.entries)

    def test_secondary_error_for_other_port_blocks_only_that_port_discovery(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        uncertain = device(port="7-1", generation=9)
        healthy = device(port="9-1", generation=11)
        self.host.devices.update({uncertain.port: uncertain, healthy.port: healthy})
        partial = service.Scan()
        partial.update(self.host.devices)
        partial.pop(uncertain.port)
        partial.errors[uncertain.port] = "Other port metadata changed during getter scan"
        self.scan_sequence([dict(self.host.devices), partial])
        self.tick()
        self.assertIn(uncertain.port, self.manager.port_errors)
        self.assertNotIn(uncertain.port, self.manager.entries)
        self.assertEqual(self.host.devices[uncertain.port], uncertain)
        self.assertNotIn(("claim", uncertain.port), self.host.calls)
        self.assertIn(("claim", healthy.port), self.host.calls)
        self.assertFalse(self.manager.scan_error)
        self.tick()
        self.assertIn(("claim", uncertain.port), self.host.calls)

    def test_secondary_error_for_existing_port_blocks_cleanup_from_old_snapshot(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        native = device(port="7-1", pid="109c", generation=9, driver="gs_native")
        self.host.devices[native.port] = native
        entry = service.Entry(native, "failed", error="Original native runtime failure",
                              kernel_tokens=service.boot_proof(proof(native))["tokens"])
        self.manager.entries[native.port] = entry
        self.manager.remember(entry)
        partial = service.Scan()
        partial.update(self.host.devices)
        partial.pop(native.port)
        partial.errors[native.port] = "Other port metadata changed during getter scan"
        self.scan_sequence([dict(self.host.devices), partial])
        before = list(self.host.calls)
        self.tick()
        self.assertEqual(self.host.calls, before)
        self.assertEqual(entry.phase, "failed")
        self.assertEqual(entry.error, "Original native runtime failure")
        self.assertFalse(entry.end_attempted)
        self.assertIn(native.port, self.manager.leases)

    def test_secondary_port_error_preserves_pending_bootstrap_proof_without_handoff(self):
        self.pending_info()
        self.host.complete("info", output=HEALTHY)
        original = device(port="7-1", generation=9, driver="gs_native")
        self.host.devices[original.port] = original
        job = self.host.start("bootstrap", original)
        entry = service.Entry(original, "bootstrapping", job=job, operation="bootstrap",
                              deadline=40, bootstrap_started=True)
        self.manager.entries[original.port] = entry
        self.manager.remember(entry)
        native = replace(original, pid="109c", token="new-native-instance", address=10)
        self.host.devices[native.port] = native
        self.host.complete("bootstrap", native.port, output=proof(native))
        partial = service.Scan()
        partial.update(self.host.devices)
        partial.pop(native.port)
        partial.errors[native.port] = "Other port metadata changed during getter scan"
        self.scan_sequence([dict(self.host.devices), partial])
        self.tick()
        self.assertEqual(entry.phase, "locating")
        self.assertEqual(entry.kernel_tokens, service.boot_proof(proof(native))["tokens"])
        self.assertNotIn(("boot-info", native.port), self.host.calls)
        self.assertEqual(self.host.saved["leases"][native.port]["kernel_tokens"], entry.kernel_tokens)
        self.tick(2)
        self.assertEqual(entry.phase, "active")
        self.assertEqual([call for call in self.host.calls if call == ("bootstrap", native.port)],
                         [("bootstrap", native.port)])

    def test_bootstrap_secondary_global_failure_keeps_proof_and_fences_new_claims(self):
        self.tick(2)
        native = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[PORT] = native
        self.host.complete("bootstrap", PORT, output=proof(native))
        other = device(port="7-1", generation=9)
        self.host.devices[other.port] = other
        scan = self.host.scan
        calls = 0

        def second_scan_unavailable():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise service.Unsafe("Global enumeration unavailable after bootstrap")
            return scan()

        self.host.scan = second_scan_unavailable
        self.tick()
        entry = self.manager.entries[PORT]
        self.assertTrue(self.manager.scan_error)
        self.assertEqual(entry.phase, "locating")
        self.assertEqual(entry.kernel_tokens, service.boot_proof(proof(native))["tokens"])
        self.assertNotIn(("claim", other.port), self.host.calls)
        self.assertNotIn(("boot-info", PORT), self.host.calls)
        self.assertEqual(self.host.devices[other.port], other)

    def test_running_getter_deadline_is_enforced_during_incomplete_metadata(self):
        _, job = self.pending_info()
        original_scan = self.host.scan
        self.host.scan = lambda: self.partial()
        self.host.now += service.JOB_SECONDS["info"] + 1
        self.tick(5)
        self.assertEqual(self.manager.entries[PORT].phase, "failed")
        self.assertTrue(self.manager.entries[PORT].timed_out)
        self.assertEqual([op for op, _ in self.host.calls].count("cancel"), 1)
        self.assertIs(self.manager.entries[PORT].job, job)
        self.assertFalse(any(op in ("end", "restore") for op, _ in self.host.calls))
        self.host.complete("info", output=HEALTHY)
        self.tick()
        self.assertIsNone(self.manager.entries[PORT].job)
        self.assertIn("deadline", self.manager.entries[PORT].error)
        self.host.scan = original_scan
        self.tick()
        self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)
        self.assertEqual([op for op, _ in self.host.calls].count("cancel"), 1)


class ObservationGuard(unittest.TestCase):
    """Real Host observation checks, rooted only in a disposable fake sysfs."""
    def setUp(self):
        self.fixture = fixture.Adapter()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.host = self.fixture.host
        self.path, self.native = self.fixture.native_fixture()

    def test_temporarily_empty_metadata_is_per_port_unknown_then_recovers(self):
        product = self.path / "idProduct"
        original = product.read_text()
        product.write_text("")
        with self.assertRaises(service.StatusUnavailable) as unavailable:
            self.host.observe_guard(self.native)
        self.assertFalse(unavailable.exception.global_scan)
        with self.assertRaises(service.Unsafe) as mutation:
            self.host.guard(self.native)
        self.assertNotIsInstance(mutation.exception, service.StatusUnavailable)
        product.write_text(original)
        self.host.observe_guard(self.native)

    def test_global_scan_failure_is_typed_without_relaxing_mutation_guard(self):
        with patch.object(self.host, "scan", side_effect=service.Unsafe("Global synthetic failure")):
            with self.assertRaises(service.StatusUnavailable) as unavailable:
                self.host.observe_guard(self.native)
            self.assertTrue(unavailable.exception.global_scan)
            with self.assertRaises(service.Unsafe) as mutation:
                self.host.guard(self.native)
            self.assertNotIsInstance(mutation.exception, service.StatusUnavailable)

    def test_replaced_device_is_distinct_from_unknown_metadata_and_runtime_fault(self):
        (self.path / "devnum").write_text("10")
        with self.assertRaises(service.StatusChanged):
            self.host.observe_guard(self.native)
        with self.assertRaises(service.Unsafe) as mutation:
            self.host.guard(self.native)
        self.assertNotIsInstance(mutation.exception, service.StatusChanged)


if __name__ == "__main__":
    unittest.main()
