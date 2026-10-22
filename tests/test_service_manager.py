#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Hermetic policy/adapter tests: no /sys, /proc or device accesses on host."""
import copy
from dataclasses import replace
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gamesir_service", ROOT / "tools/service/gamesir_native.py")
service = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = service
spec.loader.exec_module(service)


def device(port="2-3.4", pid="100a", generation=1, driver="xpad", parent="hub-object-1"):
    return service.Device(port, f"{port}/instance-{generation}", parent, pid, 2, generation, driver)


def proof(d=None, *, failed=False, stage=5):
    d = d or device(pid="109c", generation=2, driver="gs_native")
    return (f"bootstrap state={8 if failed else 7} error={-110 if failed else 0} "
            f"failed_stage={stage if failed else 0} pad=1 imu={0 if failed else 1} handover=1 "
            f"port_token={sum(d.port.encode())} instance_token={d.address}\n" +
            ("" if failed else "Native startup completed."))


class Fake:
    def __init__(self, devices=None):
        self.devices = {d.port: d for d in devices or []}
        self.saved = {}
        self.calls = []
        self.logs = []
        self.jobs = []
        self.block = set()
        self.control_busy = set()
        self.now = 0
        self.race = None
        self.scan_failure = False
        self.pad = 1
        self.attest = {}
        self.boot_id = "synthetic-boot"

    def load(self):
        return copy.deepcopy(self.saved)

    def save(self, value):
        self.saved = copy.deepcopy(value)

    def log(self, *args, **kwargs):
        self.logs.append((args, kwargs))

    def scan(self):
        if self.scan_failure:
            raise service.Unsafe("Incomplete ownership view")
        return dict(self.devices)

    def guard(self, d):
        if (self.devices.get(d.port) != d or d.port in self.block or
                d.port in self.control_busy):
            raise service.Unsafe("Foreign owner or replaced instance")

    def observe_guard(self, d):
        if self.devices.get(d.port) != d or d.driver != "gs_native":
            raise service.Unsafe("Native status instance replaced")
        if d.port in self.control_busy:
            raise service.StatusBusy("Synthetic native control conflict")

    def tmr_guard(self, d):
        if self.scan_failure or self.devices.get(d.port) != d or d.driver != 'gs_native':
            raise service.Unsafe('Native TMR device identity/binding changed')

    def claim(self, d):
        self.guard(d)
        self.calls.append(("claim", d.port))
        if self.race:
            self.race(d)
        else:
            self.devices[d.port] = replace(d, driver="gs_native")

    def restore(self, d):
        self.guard(d)
        if d.pid not in ("100a", "105e"):
            raise AssertionError("Speculative restore of 109c")
        self.calls.append(("restore", d.port))
        self.devices[d.port] = replace(d, driver="xpad")

    def start(self, operation, d, kernel_tokens=None):
        (self.observe_guard if operation in service.READ_ONLY else self.guard)(d)
        job = {"operation": operation, "device": d, "result": None}
        if operation == "info" and d.pid in ("109c", "105e"):
            job["kernel_tokens"] = kernel_tokens
        if operation == "info" and d.pid == "100a":
            job["result"] = (0, f"pid=100a state=1 error=0 OUT=0 session=0 pad={self.pad}")
        if operation == "boot-info":
            job["result"] = self.attest.get(d.port, (0, proof(d)))
        if operation == "end":
            self.asserted_tokens = kernel_tokens
            if kernel_tokens != service.boot_proof(self.attest.get(d.port, (0, proof(d)))[1])["tokens"]:
                raise service.Unsafe("Kernel token gate rejected END")
        self.calls.append((operation, d.port))
        self.jobs.append(job)
        return job

    def poll(self, job):
        return job["result"]

    def cancel(self, job):
        if not job.get("cancelled"):
            self.calls.append(("cancel", job["device"].port))
            job["cancelled"] = True

    def complete(self, operation=None, port=None, rc=0, output=""):
        matches = [j for j in self.jobs if j["result"] is None and
                   (operation is None or j["operation"] == operation) and
                   (port is None or j["device"].port == port)]
        assert len(matches) == 1, matches
        matches[0]["result"] = (rc, output)


class Policy(unittest.TestCase):
    def setup_manager(self, devices=None):
        self.host = Fake(devices if devices is not None else [device()])
        self.manager = service.Manager(self.host, lambda: self.host.now)
        return self.manager

    def start_boot(self):
        self.manager.tick()
        self.manager.tick()

    def boot(self, port="2-3.4", generation=2):
        self.start_boot()
        before = self.host.devices[port]
        self.host.devices[port] = device(port, "109c", generation, "gs_native", before.parent)
        self.host.complete("bootstrap", port, output=proof(self.host.devices[port]))
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[port].phase, "active")

    def healthy(self, port="2-3.4"):
        self.manager.tick()
        self.host.complete("info", port, output="pid=109c state=1 error=0 OUT=1 session=1 pad=0 imu=99")
        self.manager.tick()

    def failed_boot(self, stage=5):
        self.start_boot()
        current = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[current.port] = current
        payload = proof(current, failed=True, stage=stage)
        self.host.attest[current.port] = (1, payload)
        self.host.complete("bootstrap", rc=1, output=payload)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[current.port].device, current)
        self.assertEqual(self.manager.entries[current.port].phase, "failed")

    def test_two_dongles_hubs_and_no_fixed_port(self):
        self.setup_manager([device("1-2"), device("11-3.2.7")])
        self.manager.tick()
        self.manager.tick()
        boots = [j for j in self.host.jobs if j["operation"] == "bootstrap"]
        self.assertEqual(len(boots), 2)
        self.assertEqual({j["device"].port for j in boots}, {"1-2", "11-3.2.7"})

    def test_no_implicit_native_or_foreign_driver_adoption(self):
        self.setup_manager([device(pid="109c", driver="gs_native"), device("3-7", driver="usbfs"),
                            device("4-2", pid="109c", driver="usbfs")])
        self.manager.tick()
        self.assertEqual(self.host.calls, [])

    def test_direct_105e_acquires_and_starts_without_input_or_handoff(self):
        self.setup_manager([device(pid="105e")])
        self.host.pad = 0
        self.manager.tick()
        self.assertEqual(self.host.calls, [("claim", "2-3.4"), ("bootstrap", "2-3.4")])
        original = self.host.devices["2-3.4"]
        self.host.complete("bootstrap", output=proof(original).replace("handover=1", "handover=0"))
        self.manager.tick()
        self.manager.tick()
        entry = self.manager.entries[original.port]
        self.assertEqual(entry.phase, "active")
        self.assertEqual(entry.device, original)
        self.assertEqual(entry.origin_pid, "105e")
        self.assertEqual(self.host.saved["leases"][original.port]["origin_pid"], "105e")
        self.manager.tick()
        job = self.host.jobs[-1]
        self.assertEqual(job["operation"], "info")
        self.assertEqual(job["kernel_tokens"], entry.kernel_tokens)
        self.host.complete("info", output="pid=105e state=1 error=0 OUT=1 session=1 pad=0 imu=1")
        self.manager.tick()
        self.assertEqual(entry.phase, "active")

    def direct_boot(self):
        self.setup_manager([device(pid="105e")])
        self.manager.tick()
        self.host.complete("bootstrap", output=proof(self.host.devices["2-3.4"]))
        self.manager.tick()
        self.manager.tick()
        entry = self.manager.entries["2-3.4"]
        self.assertEqual(entry.phase, "active")
        return entry

    def test_direct_release_stops_then_restores_same_105e_not_100a(self):
        entry = self.direct_boot()
        self.manager.command("release")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1][0], "end")
        self.assertNotIn("restore", [op for op, _ in self.host.calls])
        self.host.complete("end")
        self.manager.tick()
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertEqual(self.host.devices[entry.device.port].pid, "105e")
        self.assertEqual(self.host.devices[entry.device.port].driver, "xpad")
        self.assertTrue(self.manager.returned())
        self.assertEqual([op for op, _ in self.host.calls].count("restore"), 1)
        self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)

    def test_direct_restart_after_verified_end_restores_once_without_second_end(self):
        entry = self.direct_boot()
        self.manager.command("release")
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.assertTrue(self.host.saved["leases"][entry.device.port]["end_succeeded"])
        self.manager = service.Manager(self.host, lambda: self.host.now)
        for _ in range(5):
            self.manager.tick()
        self.assertEqual(self.host.devices[entry.device.port].driver, "xpad")
        self.assertEqual([op for op, _ in self.host.calls].count("restore"), 1)
        self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)

    def test_direct_replacement_after_successful_end_is_observed_only(self):
        for owner in ("xpad", "gs_native"):
            with self.subTest(owner=owner):
                entry = self.direct_boot()
                self.manager.command("release")
                self.manager.tick()
                self.host.complete("end")
                self.manager.tick()
                replacement = device(pid="105e", generation=5, driver=owner)
                self.host.devices[entry.device.port] = replacement
                for _ in range(3):
                    self.manager.tick()
                self.assertNotIn("restore", [op for op, _ in self.host.calls])
                self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)
                self.assertEqual(self.host.devices[entry.device.port], replacement)
                self.assertEqual(self.manager.entries[entry.device.port].phase,
                                 "released" if owner == "xpad" else "blocked")

    def test_direct_failed_stop_never_unbinds_retries_or_claims_return(self):
        for mode in ("error", "timeout", "crash"):
            with self.subTest(mode=mode):
                entry = self.direct_boot()
                self.manager.command("release")
                self.manager.tick()
                if mode == "crash":
                    self.manager = service.Manager(self.host, lambda: self.host.now)
                    self.manager.tick()
                    self.manager.tick()
                else:
                    if mode == "timeout":
                        self.host.now += 6
                        self.manager.tick()
                    self.host.complete("end", rc=1 if mode == "error" else 0)
                    self.manager.tick()
                for _ in range(5):
                    self.manager.tick()
                self.assertFalse(self.manager.returned())
                self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)
                self.assertNotIn("restore", [op for op, _ in self.host.calls])
                self.assertEqual(self.manager.entries[entry.device.port].phase, "blocked")

    def test_direct_failed_init_and_missing_client_output_recover_cleanup_proof(self):
        for stage in (4, 5, 6):
            for missing in (False, True):
                with self.subTest(stage=stage, missing=missing):
                    self.setup_manager([device(pid="105e")])
                    self.manager.tick()
                    current = self.host.devices["2-3.4"]
                    payload = proof(current, failed=True, stage=stage)
                    self.host.attest[current.port] = (1, payload)
                    self.host.complete("bootstrap", rc=1, output="" if missing else payload)
                    self.manager.tick()
                    self.manager.tick()
                    entry = self.manager.entries[current.port]
                    self.assertEqual(entry.phase, "failed")
                    self.assertEqual(entry.device, current)
                    self.manager.tick()
                    self.assertEqual(self.host.calls[-1][0], "end")
                    self.host.complete("end")
                    self.manager.tick()
                    self.manager.tick()
                    self.assertEqual(self.host.devices[current.port].driver, "xpad")
                    self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_direct_missing_terminal_kernel_proof_blocks_restore(self):
        self.setup_manager([device(pid="105e")])
        self.manager.tick()
        self.host.attest["2-3.4"] = (1, "bootstrap state=0 error=0")
        self.host.complete("bootstrap", rc=1)
        for _ in range(5):
            self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")
        self.assertNotIn("end", [op for op, _ in self.host.calls])
        self.assertNotIn("restore", [op for op, _ in self.host.calls])

    def test_direct_handoff_rejects_changed_pid_instance_or_hub(self):
        for change in ({"pid": "109c"}, {"generation": 2}, {"parent": "new-hub"}):
            with self.subTest(change=change):
                self.setup_manager([device(pid="105e")])
                self.manager.tick()
                original = self.host.devices["2-3.4"]
                fields = dict(pid="105e", driver="gs_native")
                fields.update(change)
                self.host.devices[original.port] = device(**fields)
                self.host.complete("bootstrap", output=proof(original))
                for _ in range(8):
                    self.manager.tick()
                    self.host.now += 1
                self.assertEqual(self.manager.entries[original.port].phase, "blocked")
                self.assertNotIn("end", [op for op, _ in self.host.calls])
                self.assertNotIn("restore", [op for op, _ in self.host.calls])

    def test_direct_release_never_restores_wrong_pid_or_foreign_instance(self):
        for change in ({"pid": "109c"}, {"pid": "100a"}, {"generation": 4}, {"parent": "new-hub"}):
            with self.subTest(change=change):
                entry = self.direct_boot()
                self.manager.command("release")
                fields = dict(pid="105e", driver="gs_native")
                fields.update(change)
                self.host.devices[entry.device.port] = device(**fields)
                for _ in range(3):
                    self.manager.tick()
                self.assertFalse(self.manager.returned())
                self.assertNotIn("end", [op for op, _ in self.host.calls])
                self.assertNotIn("restore", [op for op, _ in self.host.calls])

    def test_direct_restart_active_attests_without_new_bootstrap(self):
        entry = self.direct_boot()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[entry.device.port].phase, "active")
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_direct_restart_during_bootstrap_recovers_cleanup_only(self):
        self.setup_manager([device(pid="105e")])
        self.manager.tick()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "failed")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1][0], "end")
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_direct_claim_only_restart_can_restore_without_bootstrap_or_end(self):
        self.setup_manager([device(pid="105e")])
        with patch.object(self.manager, "begin_bootstrap"):
            self.manager.tick()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.assertEqual(self.host.calls, [("claim", "2-3.4"), ("restore", "2-3.4")])
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")

    def test_direct_legacy_record_missing_origin_is_not_cleanup_authority(self):
        entry = self.direct_boot()
        del self.host.saved["leases"][entry.device.port]["origin_pid"]
        before = list(self.host.calls)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.assertEqual(self.host.calls, before)
        self.assertEqual(self.manager.entries[entry.device.port].phase, "blocked")

    def test_direct_no_adoption_of_native_foreign_or_unknown_pid(self):
        self.setup_manager([device("1-2", pid="105e", driver="gs_native"),
                            device("1-3", pid="105e", driver="usbfs"),
                            device("1-5", pid="105d"), device("1-6", pid="1022")])
        self.manager.tick()
        self.assertEqual(self.host.calls, [])
        self.assertEqual(self.manager.entries, {})

    def test_direct_budget_checked_before_claim_and_cleanup_ignores_budget(self):
        self.setup_manager([device(pid="105e")])
        self.manager.budget_boot = self.host.boot_id
        self.manager.budgets["2-3.4"] = service.deque([0, 0, 0])
        self.manager.tick()
        self.assertEqual(self.host.calls, [])
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")
        entry = self.direct_boot()
        self.manager.budgets[entry.device.port] = service.deque([0, 0, 0])
        self.manager.command("release")
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.devices[entry.device.port].driver, "xpad")

    def test_direct_new_instance_restarts_once_with_fresh_budget(self):
        entry = self.direct_boot()
        replacement = device(pid="105e", generation=2)
        self.host.devices[entry.device.port] = replacement
        self.manager.tick()
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 2)
        self.assertEqual(self.manager.entries[replacement.port].device.token, replacement.token)
        self.host.complete("bootstrap", output=proof(self.host.devices[replacement.port]))
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[replacement.port].phase, "active")

    def test_direct_pm_resume_uses_shared_runtime_and_keeps_identity(self):
        entry = self.direct_boot()
        self.manager.tick()
        self.host.complete("info", output="pid=105e state=3 error=0 OUT=0 session=0 pad=0 imu=9")
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.calls[-1][0], "resume")
        self.host.complete("resume", rc=3)
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.host.complete("resume")
        self.manager.tick()
        self.assertEqual(entry.phase, "active")
        self.assertEqual(entry.device.pid, "105e")
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_direct_and_transition_dongles_start_independently(self):
        self.setup_manager([device("1-3", pid="105e"), device("4-1.2")])
        self.manager.tick()
        self.assertEqual(self.host.calls, [("claim", "1-3"), ("bootstrap", "1-3"),
                                          ("claim", "4-1.2"), ("info", "4-1.2")])
        self.host.complete("bootstrap", "1-3", output=proof(self.host.devices["1-3"]))
        self.manager.tick()
        before = self.host.devices["4-1.2"]
        self.host.devices[before.port] = device(before.port, "109c", 2, "gs_native", before.parent)
        self.host.complete("bootstrap", before.port, output=proof(self.host.devices[before.port]))
        self.manager.tick()
        self.manager.tick()
        self.assertEqual({p: e.phase for p, e in self.manager.entries.items()},
                         {"1-3": "active", "4-1.2": "active"})
        self.assertEqual(self.manager.entries["1-3"].origin_pid, "105e")
        self.assertEqual(self.manager.entries["4-1.2"].origin_pid, "100a")

    def test_direct_release_cancels_inflight_start_then_quiesces_once(self):
        self.setup_manager([device(pid="105e")])
        self.manager.tick()
        self.manager.command("release")
        self.manager.tick()
        current = self.host.devices["2-3.4"]
        payload = proof(current, failed=True)
        self.host.attest[current.port] = (1, payload)
        self.host.complete("bootstrap", rc=1, output=payload)
        self.manager.tick()
        self.manager.tick()
        self.manager.tick()
        self.assertEqual([op for op, _ in self.host.calls],
                         ["claim", "bootstrap", "cancel", "boot-info", "end"])
        self.host.complete("end")
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.devices[current.port].driver, "xpad")

    def test_direct_claim_failure_after_unbind_restores_without_start(self):
        self.setup_manager([device(pid="105e")])
        def fail_claim(d):
            self.host.devices[d.port] = replace(d, driver=None)
            raise service.Unsafe("Injected scoped claim failure")
        self.host.claim = fail_claim
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.calls, [("restore", "2-3.4")])
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")

    def test_direct_claim_replacement_is_not_bootstrapped_or_restored(self):
        self.setup_manager([device(pid="105e")])
        self.host.race = lambda d: self.host.devices.update({d.port: device(pid="105e", generation=2, driver="usbfs")})
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.calls, [("claim", "2-3.4")])
        self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")

    def test_direct_quiet_radio_does_not_end_runtime_and_hotplug_has_fresh_identity(self):
        entry = self.direct_boot()
        self.manager.tick()
        self.host.complete("info", output="pid=105e state=1 error=0 OUT=1 session=1 pad=0 imu=0")
        self.manager.tick()
        self.assertEqual(entry.phase, "active")
        self.assertNotIn("end", [op for op, _ in self.host.calls])
        del self.host.devices[entry.device.port]
        self.manager.tick()
        self.host.now += 11
        self.manager.tick()
        self.assertNotIn(entry.device.port, self.manager.entries)
        self.host.devices["9-7.2"] = device("9-7.2", "105e", 6, "xpad", "new-hub")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1], ("bootstrap", "9-7.2"))
        self.assertEqual([op for op, _ in self.host.calls].count("claim"), 2)

    def test_direct_restore_failure_is_not_repeated_after_restart(self):
        entry = self.direct_boot()
        self.manager.command("release")
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        with patch.object(self.host, "restore", side_effect=service.Unsafe("Injected return failure")) as restore:
            self.manager.tick()
            self.manager = service.Manager(self.host, lambda: self.host.now)
            for _ in range(5):
                self.manager.tick()
            self.assertEqual(restore.call_count, 1)
        self.assertEqual(self.manager.entries[entry.device.port].phase, "blocked")
        self.assertFalse(self.manager.returned())

    def test_direct_origin_cannot_be_mixed_with_transition_record(self):
        self.setup_manager()
        self.boot()
        self.host.saved["leases"]["2-3.4"]["origin_pid"] = "105e"
        before = list(self.host.calls)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")
        self.assertEqual(self.host.calls, before)

    def test_foreign_handle_blocks_all_mutation(self):
        self.setup_manager()
        self.host.block.add("2-3.4")
        self.manager.tick()
        self.assertEqual(self.host.calls, [])
        self.manager.tick()
        self.assertEqual(self.host.calls, [])

    def test_usbfs_observer_does_not_block_native_getter_or_end_protection(self):
        self.setup_manager()
        self.boot()
        self.host.block.add("2-3.4")  # Read-only USB enumeration, not an interface claim.
        self.healthy()
        entry = self.manager.entries["2-3.4"]
        self.assertEqual(entry.phase, "active")
        self.assertFalse(entry.status_conflict)
        info = [j for j in self.host.jobs if j["operation"] == "info"][-1]
        self.assertEqual(info["kernel_tokens"], entry.kernel_tokens)
        self.manager.command("release")
        self.manager.tick()
        self.assertTrue(self.manager.paused)
        self.assertEqual(entry.phase, "blocked")
        self.assertEqual(self.host.saved["leases"][entry.device.port]["phase"], "blocked")
        self.assertFalse(entry.end_attempted)
        self.assertNotIn("end", [op for op, _ in self.host.calls])
        self.host.block.clear()
        before = list(self.host.calls)
        restarted = service.Manager(self.host, lambda: self.host.now)
        restarted.tick()
        self.assertTrue(restarted.paused)
        self.assertEqual(restarted.entries[entry.device.port].phase, "blocked")
        self.assertEqual(self.host.calls, before)  # Restart cannot convert quarantine to END.

    def test_control_busy_preserves_runtime_with_bounded_quiet_passive_checks(self):
        self.setup_manager()
        self.boot()
        entry = self.manager.entries["2-3.4"]
        self.host.control_busy.add(entry.device.port)
        calls_before = list(self.host.calls)
        saved_before = copy.deepcopy(self.host.saved)
        with patch.object(self.host, "observe_guard", wraps=self.host.observe_guard) as guard:
            for delay in (1, 2, 4, 8, 10, 10):
                self.manager.tick()
                self.assertEqual(entry.phase, "active")
                self.assertFalse(entry.error)
                self.assertEqual(entry.next_check - self.host.now, delay)
                checks = guard.call_count
                for _ in range(100):
                    self.manager.tick()
                self.assertEqual(guard.call_count, checks)
                self.host.now = entry.next_check
        self.assertEqual(self.host.calls, calls_before)  # No client or USB command launched.
        self.assertEqual(self.host.saved, saved_before)  # No recurring fsync storm.
        self.assertEqual(sum(args == ("status_deferred",) for args, _ in self.host.logs), 1)
        self.assertTrue(self.manager.status()["devices"][entry.device.port]["status_conflict"])
        self.host.control_busy.clear()
        self.healthy()
        self.assertFalse(entry.status_conflict)
        self.assertEqual(entry.status_conflicts, 0)
        self.assertEqual(entry.phase, "active")
        self.assertEqual(sum(args == ("status_available",) for args, _ in self.host.logs), 1)

    def test_getter_open_busy_exit_is_nonterminal_and_not_text_parsed(self):
        self.setup_manager()
        self.boot()
        entry = self.manager.entries["2-3.4"]
        self.manager.tick()
        self.host.complete("info", rc=service.STATUS_BUSY_EXIT, output="arbitrary localized diagnostic")
        self.manager.tick()
        self.assertEqual(entry.phase, "active")
        self.assertTrue(entry.status_conflict)
        self.assertIsNone(entry.job)
        count = len(self.host.calls)
        self.manager.tick()
        self.assertEqual(len(self.host.calls), count)
        self.host.now = entry.next_check
        self.healthy()
        self.assertFalse(entry.status_conflict)

    def test_busy_attestation_keeps_proof_without_adopting_or_reinitializing(self):
        for busy_by in ("guard", "client"):
            with self.subTest(busy_by=busy_by):
                self.setup_manager()
                self.start_boot()
                d = device(pid="109c", generation=2, driver="gs_native")
                self.host.devices[d.port] = d
                if busy_by == "guard":
                    self.host.control_busy.add(d.port)
                else:
                    self.host.attest[d.port] = (service.STATUS_BUSY_EXIT, "busy")
                self.host.complete("bootstrap", output=proof(d))
                self.manager.tick()
                self.manager.tick()
                entry = self.manager.entries[d.port]
                self.assertEqual(entry.phase, "attesting")
                self.assertEqual(entry.device.pid, "100a")
                self.assertEqual(entry.candidate, d)
                self.assertEqual(entry.kernel_tokens, service.boot_proof(proof(d))["tokens"])
                self.assertTrue(entry.status_conflict)
                self.assertNotIn("end", [op for op, _ in self.host.calls])
                self.host.control_busy.clear()
                self.host.attest.clear()
                self.host.now = entry.next_check
                self.manager.tick()
                self.manager.tick()
                self.assertEqual(entry.phase, "active")
                self.assertEqual(entry.device, d)
                self.assertFalse(entry.status_conflict)
                self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_failed_bootstrap_busy_attestation_preserves_cleanup_only_intent(self):
        self.setup_manager()
        self.start_boot()
        d = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[d.port] = d
        self.host.attest[d.port] = (service.STATUS_BUSY_EXIT, "")
        self.host.complete("bootstrap", rc=1, output=proof(d, failed=True))
        self.manager.tick()
        self.manager.tick()
        entry = self.manager.entries[d.port]
        self.assertEqual(entry.phase, "attesting")
        self.assertEqual(entry.after_attest, "failed")
        self.host.attest[d.port] = (1, proof(d, failed=True))
        self.host.now = entry.next_check
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(entry.phase, "failed")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1][0], "end")

    def test_pause_or_shutdown_during_status_conflict_keeps_exact_end_guard(self):
        for mode in ("release", "shutdown"):
            with self.subTest(mode=mode):
                self.setup_manager()
                self.boot()
                entry = self.manager.entries["2-3.4"]
                self.host.control_busy.add(entry.device.port)
                self.manager.tick()
                self.assertTrue(entry.status_conflict)
                if mode == "release":
                    self.manager.command("release")
                else:
                    self.manager.stopping = True
                self.host.control_busy.clear()
                self.manager.tick()  # Cleanup need not wait for a status backoff.
                self.assertEqual(self.host.calls[-1], ("end", entry.device.port))
                self.assertEqual(self.host.asserted_tokens, entry.kernel_tokens)
                self.assertEqual(self.host.saved["paused"], mode == "release")

    def test_actual_control_conflict_still_blocks_end_and_is_persisted(self):
        self.setup_manager()
        self.boot()
        self.host.control_busy.add("2-3.4")
        self.manager.tick()
        self.manager.command("release")
        self.manager.tick()
        entry = self.manager.entries["2-3.4"]
        self.assertEqual(entry.phase, "blocked")
        self.assertEqual(self.host.saved["leases"][entry.device.port]["phase"], "blocked")
        self.assertFalse(entry.end_attempted)
        self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_replacement_during_deferred_status_is_terminal_and_never_owned(self):
        for during in ("guard", "child"):
            with self.subTest(during=during):
                self.setup_manager()
                self.boot()
                entry = self.manager.entries["2-3.4"]
                old = entry.device
                if during == "guard":
                    self.host.control_busy.add(old.port)
                    self.manager.tick()
                else:
                    self.manager.tick()
                    self.host.complete("info", rc=service.STATUS_BUSY_EXIT)
                self.host.devices[old.port] = device(pid="109c", generation=3, driver="gs_native")
                self.manager.tick()
                self.assertEqual(entry.phase, "blocked")
                self.assertEqual(entry.device, old)
                self.assertEqual(self.host.saved["leases"][old.port]["phase"], "blocked")
                self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_info_result_revalidates_metadata_after_child_completion(self):
        for field, value in (("driver", "usbfs"), ("token", "new-instance"), ("parent", "new-hub")):
            with self.subTest(field=field):
                self.setup_manager()
                self.boot()
                entry = self.manager.entries["2-3.4"]
                self.manager.tick()
                def complete_after_initial_scan(_job):
                    self.host.devices[entry.device.port] = replace(entry.device, **{field: value})
                    return (0, "pid=109c state=1 error=0 OUT=1 session=1 pad=1 imu=1")
                self.host.poll = complete_after_initial_scan
                self.manager.tick()
                self.assertEqual(entry.phase, "blocked")
                self.assertIn("Device changed", entry.error)
                self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_getter_timeout_takes_precedence_over_late_busy_exit(self):
        for earlier_poll in (False, True):
            with self.subTest(earlier_poll=earlier_poll):
                self.setup_manager()
                self.boot()
                entry = self.manager.entries["2-3.4"]
                self.manager.tick()
                self.host.now = entry.deadline + 1
                if earlier_poll:
                    self.manager.tick()  # Cancellation sent before the final child result.
                self.host.complete("info", rc=service.STATUS_BUSY_EXIT)
                self.manager.tick()
                self.assertEqual(entry.phase, "failed")
                self.assertIn("deadline", entry.error)
                self.assertFalse(entry.status_conflict)

    def test_arbitrary_getter_failure_cannot_be_downgraded_to_busy(self):
        for output in ("open native test node: Device or resource busy", "GET_INFO: Input/output error",
                       "pid=109c state=2 error=-5 OUT=0 session=0 pad=1 imu=1",
                       "pid=109c state=1 error=0 OUT=1 session=1 pad=1 imu=1"):
            with self.subTest(output=output):
                self.setup_manager()
                self.boot()
                self.manager.tick()
                self.host.complete("info", rc=1, output=output)
                self.manager.tick()
                entry = self.manager.entries["2-3.4"]
                self.assertEqual(entry.phase, "failed")
                self.assertFalse(entry.status_conflict)

    def test_passive_100a_control_conflict_does_not_spend_bootstrap_budget(self):
        for via in ("first-guard", "client", "later-guard"):
            with self.subTest(via=via):
                self.setup_manager()
                self.host.pad = 0
                claim = self.host.claim
                def claimed_with_busy_fd(d):
                    claim(d)
                    if via == "first-guard":
                        self.host.control_busy.add(d.port)
                self.host.claim = claimed_with_busy_fd
                self.manager.tick()
                entry = self.manager.entries["2-3.4"]
                if via == "client":
                    entry.job["result"] = (service.STATUS_BUSY_EXIT, "busy")
                    self.manager.tick()
                elif via == "later-guard":
                    entry.job["result"] = (service.STATUS_BUSY_EXIT, "busy")
                    self.manager.tick()
                    self.host.now = entry.next_check
                    self.host.control_busy.add(entry.device.port)
                    self.manager.tick()
                for _ in range(30):
                    self.manager.tick()
                self.assertEqual(entry.phase, "checking_start")
                self.assertTrue(entry.status_conflict)
                self.assertEqual(list(self.manager.budgets[entry.device.port]), [])
                self.assertEqual(self.manager.attempted, set())
                self.assertNotIn("bootstrap", [op for op, _ in self.host.calls])
                self.host.control_busy.clear()
                self.host.pad = 1
                self.host.now = entry.next_check
                self.manager.tick()
                self.manager.tick()
                self.assertEqual(entry.phase, "bootstrapping")
                self.assertEqual(len(self.manager.budgets[entry.device.port]), 1)

    def test_control_busy_between_manager_and_host_first_getter_checks(self):
        self.setup_manager()
        observe = self.host.observe_guard
        calls = 0
        def busy_before_spawn(d):
            nonlocal calls
            calls += 1
            if calls == 2:  # Manager guard succeeded, Host.start sees a new owner.
                self.host.control_busy.add(d.port)
            observe(d)
        self.host.observe_guard = busy_before_spawn
        self.manager.tick()
        entry = self.manager.entries["2-3.4"]
        self.assertEqual(calls, 2)
        self.assertEqual(entry.phase, "checking_start")
        self.assertEqual(self.host.saved["leases"][entry.device.port]["phase"], "checking_start")
        self.assertTrue(entry.status_conflict)
        self.assertIsNone(entry.job)
        self.assertEqual([op for op, _ in self.host.calls], ["claim"])
        self.assertEqual(list(self.manager.budgets[entry.device.port]), [])

    def test_true_error_replaces_previous_temporary_status_warning(self):
        self.setup_manager()
        self.boot()
        entry = self.manager.entries["2-3.4"]
        self.host.control_busy.add(entry.device.port)
        self.manager.tick()
        self.assertTrue(entry.status_conflict)
        self.host.control_busy.clear()
        self.host.now = entry.next_check
        self.manager.tick()
        self.host.complete("info", rc=1, output="GET_INFO: Input/output error")
        self.manager.tick()
        self.assertEqual(entry.phase, "failed")
        self.assertFalse(entry.status_conflict)
        self.assertEqual(entry.status_conflicts, 0)

    def test_pause_during_passive_100a_busy_uses_only_strict_known_return(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        self.manager.entries["2-3.4"].job["result"] = (service.STATUS_BUSY_EXIT, "busy")
        self.manager.tick()
        entry = self.manager.entries["2-3.4"]
        self.host.now = entry.next_check
        self.host.control_busy.add(entry.device.port)
        self.manager.tick()
        self.assertTrue(entry.status_conflict)
        self.manager.command("release")
        self.host.control_busy.clear()
        self.manager.tick()
        self.assertEqual(entry.phase, "released")
        self.assertEqual(self.host.calls[-1][0], "restore")
        self.assertEqual(self.host.devices[entry.device.port].driver, "xpad")
        self.assertNotIn("bootstrap", [op for op, _ in self.host.calls])
        self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_busy_code_from_mutating_operation_is_not_retried_as_getter(self):
        self.setup_manager()
        self.boot()
        entry = self.manager.entries["2-3.4"]
        entry.phase = "resuming"
        self.manager.tick()
        self.host.complete("resume", rc=service.STATUS_BUSY_EXIT)
        self.manager.tick()
        self.assertEqual(entry.phase, "failed")
        self.assertFalse(entry.status_conflict)
        self.assertEqual([op for op, _ in self.host.calls].count("resume"), 1)

    def test_claim_race_never_bootstraps_replacement(self):
        self.setup_manager()
        self.host.race = lambda d: self.host.devices.update({d.port: replace(d, token="replacement")})
        self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls], ["claim"])

    def test_static_gamepad_counter_is_not_failure(self):
        self.setup_manager()
        self.boot()
        for _ in range(5):
            self.healthy()
            self.host.now += 3
        self.assertEqual(self.manager.entries["2-3.4"].phase, "active")
        self.assertNotIn("end", [c[0] for c in self.host.calls])

    def test_bootstrap_wrong_port_or_hub_replacement_rejected(self):
        for change in ("port", "hub", "same-token", "wrong-driver"):
            with self.subTest(change=change):
                self.setup_manager()
                self.start_boot()
                old = self.host.devices["2-3.4"]
                new = device(pid="109c", generation=2, driver="gs_native")
                if change == "port":
                    del self.host.devices[old.port]
                    new = replace(new, port="5-1")
                elif change == "hub":
                    new = replace(new, parent="replacement-hub")
                elif change == "same-token":
                    new = replace(new, token=old.token)
                else:
                    new = replace(new, driver="other")
                self.host.devices[new.port] = new
                self.host.complete("bootstrap", output=proof())
                self.manager.tick()
                self.host.now += service.HANDOFF_SECONDS
                self.manager.tick()
                self.assertEqual(self.manager.entries[old.port].phase, "blocked")

    def test_release_once_end_then_verified_100a_only(self):
        self.setup_manager()
        self.boot()
        self.manager.command("release")
        self.assertTrue(self.host.saved["paused"])
        self.assertFalse(self.manager.returned())
        self.manager.tick()
        self.host.complete("end", output="Runtime ended; zero motor transfer accepted.")
        self.manager.tick()
        self.assertFalse(self.manager.returned())
        self.host.devices["2-3.4"] = device(generation=3)
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertEqual([c[0] for c in self.host.calls], ["claim", "info", "bootstrap", "boot-info", "end"])
        self.host.devices["2-3.4"] = device(generation=4)
        self.manager.tick()
        self.assertEqual(len(self.host.calls), 5)

    def test_release_timeout_never_guesses_mode_command_or_repeats_end(self):
        self.setup_manager()
        self.boot()
        self.manager.command("release")
        self.manager.tick()
        self.host.complete("end", rc=1)
        self.manager.tick()
        self.host.now = 100
        for _ in range(10):
            self.manager.tick()
        self.assertFalse(self.manager.returned())
        self.assertEqual([c[0] for c in self.host.calls].count("end"), 1)
        self.assertNotIn("restore", [c[0] for c in self.host.calls])

    def test_pause_survives_restart_and_explicit_resume_reopens(self):
        self.setup_manager()
        self.manager.command("release")
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.assertEqual(self.host.calls, [])
        self.manager.command("resume")
        self.start_boot()
        self.assertEqual([c[0] for c in self.host.calls], ["claim", "info", "bootstrap"])

    def test_system_stop_does_not_persist_deadband_pause(self):
        self.setup_manager()
        self.boot()
        self.manager.stopping = True
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.host.devices["2-3.4"] = device(generation=3)
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertFalse(self.host.saved["paused"])

    def test_existing_lease_adopted_only_exact_instance(self):
        self.setup_manager()
        self.boot()
        saved = copy.deepcopy(self.host.saved)
        restart = service.Manager(self.host, lambda: self.host.now)
        restart.tick()
        restart.tick()
        self.assertEqual(restart.entries["2-3.4"].phase, "active")
        self.host.saved = saved
        self.host.devices["2-3.4"] = device(pid="109c", generation=99, driver="gs_native")
        restart = service.Manager(self.host, lambda: self.host.now)
        restart.tick()
        self.assertEqual(restart.entries["2-3.4"].phase, "blocked")
        self.assertNotEqual(restart.entries["2-3.4"].device.token, self.host.devices["2-3.4"].token)

    def test_pm_resume_is_once_and_eagain_bounded(self):
        self.setup_manager()
        self.boot()
        self.manager.tick()
        self.host.complete("info", output="pid=109c state=3 error=0 OUT=1 session=0")
        self.manager.tick()
        self.manager.tick()
        self.host.complete("resume", rc=3)
        self.manager.tick()
        self.host.now += 0.5
        self.manager.tick()
        self.host.complete("resume", output="Persistent runtime resumed.")
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "active")
        self.healthy()
        self.assertEqual([c[0] for c in self.host.calls].count("resume"), 2)

    def test_pm_failure_does_not_retry_initialization(self):
        self.setup_manager()
        self.boot()
        self.manager.tick()
        self.host.complete("info", output="pid=109c state=3 error=0 OUT=1 session=0")
        self.manager.tick()
        self.manager.tick()
        self.host.complete("resume", rc=1)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls].count("resume"), 1)
        self.assertEqual(self.host.jobs[-1]["operation"], "end")

    def test_native_owner_lost_never_stolen_back(self):
        self.setup_manager()
        self.boot()
        d = self.host.devices["2-3.4"]
        self.host.devices[d.port] = replace(d, driver="usbfs")
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[d.port].phase, "blocked")
        self.assertEqual(len(self.host.calls), 4)

    def test_hotplug_new_instance_and_port(self):
        self.setup_manager()
        self.boot()
        self.host.devices.clear()
        self.manager.tick()
        self.host.now += 11
        self.manager.tick()
        self.host.devices["7-1.3"] = device("7-1.3", generation=7)
        self.start_boot()
        self.assertEqual(self.host.calls[-1], ("bootstrap", "7-1.3"))

    def test_failed_bootstrap_survives_usb_gap_and_unowned_109c_replacement(self):
        for gap in (1, 11, 600):
            for owner in ("xpad", "gs_native"):
                with self.subTest(gap=gap, owner=owner):
                    self.setup_manager()
                    self.start_boot()
                    original = self.manager.entries["2-3.4"].device
                    self.host.complete("bootstrap", rc=1, output="BOOTSTRAP: No such device\n")
                    self.manager.tick()
                    self.host.devices.clear()
                    self.manager.tick()
                    self.assertEqual(self.manager.entries[original.port].phase, "failed")
                    self.host.now += gap
                    self.manager.tick()
                    self.assertIn(original.port, self.host.saved["leases"])
                    self.host.devices[original.port] = device(pid="109c", generation=2, driver=owner)
                    self.manager.tick()
                    entry = self.manager.entries[original.port]
                    self.assertEqual(entry.phase, "blocked")
                    self.assertEqual(entry.device, original)
                    self.assertIn("Unowned new 109c", entry.error)
                    self.assertIn(original.port, self.host.saved["leases"])
                    status = self.manager.status()["devices"][original.port]
                    self.assertEqual(status["observed_pid"], "109c")
                    self.assertEqual(status["observed_driver"], owner)
                    self.assertTrue(status["present"])
                    self.assertEqual([op for op, _ in self.host.calls], ["claim", "info", "bootstrap"])

    def early_bootstrap_failure(self):
        self.start_boot()
        # Artificial early stage: the real recorded ENODEV lacked this detail.
        output = ("BOOTSTRAP: No such device\n"
                  "bootstrap state=8 error=-19 failed_stage=2 pad=1 imu=0 handover=0 "
                  "port_token=91 instance_token=1\n")
        self.host.complete("bootstrap", rc=1, output=output)
        self.manager.tick()
        return self.manager.entries["2-3.4"], output

    def test_early_kernel_failure_is_diagnostic_not_handoff_authority(self):
        self.setup_manager()
        entry, output = self.early_bootstrap_failure()
        diagnostic = entry.bootstrap_diagnostic
        self.assertEqual(diagnostic["returncode"], 1)
        self.assertEqual(diagnostic["reported_kernel_status"]["error"], -19)
        self.assertEqual(diagnostic["reported_kernel_status"]["failed_stage"], 2)
        self.assertEqual(diagnostic["combined_output"], output)
        self.assertEqual(diagnostic["output_sha256"], service.hashlib.sha256(output.encode()).hexdigest())
        self.assertEqual(entry.kernel_tokens, [])
        self.assertEqual(entry.phase, "failed")
        self.assertEqual(self.host.saved["leases"][entry.device.port]["bootstrap_diagnostic"], diagnostic)
        self.assertEqual(self.manager.status()["recent_failures"][-1]["bootstrap_diagnostic"], diagnostic)
        self.assertEqual(sum(args == ("bootstrap_result",) for args, _ in self.host.logs), 1)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        recovered = self.manager.entries[entry.device.port]
        self.assertEqual(recovered.error, entry.error)
        self.assertEqual(recovered.bootstrap_diagnostic, diagnostic)
        self.assertEqual(recovered.kernel_tokens, [])

    def test_port_metadata_error_preserves_primary_bootstrap_failure_and_diagnostic(self):
        self.setup_manager()
        entry, _ = self.early_bootstrap_failure()
        original_error = entry.error
        diagnostic = copy.deepcopy(entry.bootstrap_diagnostic)
        failure_history = copy.deepcopy(self.manager.recent_failures)
        calls = list(self.host.calls)
        original_scan = self.host.scan
        metadata_error = "Empty USB metadata: /synthetic/2-3.4/devnum (base 10)"

        def partial_scan():
            result = service.Scan()
            result.errors[entry.device.port] = metadata_error
            return result

        self.host.scan = partial_scan
        for _ in range(3):
            self.host.now += 11
            self.manager.tick()
            state = self.manager.status()
            self.assertEqual(state["port_errors"][entry.device.port], metadata_error)
            self.assertIsNone(state["devices"][entry.device.port]["present"])
            self.assertIsNone(entry.absent_since)
            self.assertEqual(entry.phase, "failed")
            self.assertEqual(entry.error, original_error)
            self.assertEqual(entry.bootstrap_diagnostic, diagnostic)
            self.assertEqual(self.manager.recent_failures, failure_history)
            self.assertEqual(self.host.saved["leases"][entry.device.port]["error"], original_error)
            self.assertFalse(self.manager.returned())
            self.assertEqual(self.host.calls, calls)

        # A following complete absence scan must not leave a stale scan error
        # masquerading as the primary bootstrap failure, nor authorize cleanup.
        self.host.scan = original_scan
        self.host.devices.clear()
        self.manager.tick()
        self.assertEqual(self.manager.status()["port_errors"], {})
        self.assertEqual(entry.error, original_error)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        restored = self.manager.entries[entry.device.port]
        self.assertEqual(restored.error, original_error)
        self.assertEqual(restored.bootstrap_diagnostic, diagnostic)

        self.host.devices[entry.device.port] = device(pid="109c", generation=2, driver="xpad")
        self.manager.tick()
        self.assertEqual(restored.phase, "blocked")
        self.assertEqual(restored.bootstrap_diagnostic, diagnostic)
        self.assertEqual(restored.kernel_tokens, [])
        self.assertFalse(restored.end_attempted)
        self.assertEqual(self.host.calls, calls)

    def test_port_metadata_error_is_separate_from_healthy_runtime_error(self):
        self.setup_manager()
        self.boot()
        entry = self.manager.entries["2-3.4"]
        original_scan = self.host.scan
        calls = list(self.host.calls)

        def partial_scan():
            result = service.Scan()
            result.errors[entry.device.port] = "Incomplete own descriptors"
            return result

        self.host.scan = partial_scan
        self.manager.tick()
        self.assertEqual(entry.phase, "active")
        self.assertEqual(entry.error, "")
        self.assertIsNone(self.manager.status()["devices"][entry.device.port]["present"])
        self.assertEqual(self.host.calls, calls)
        self.host.scan = original_scan
        self.manager.tick()
        self.assertEqual(self.manager.status()["port_errors"], {})
        self.assertEqual(entry.error, "")
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)
        self.assertNotIn("end", [op for op, _ in self.host.calls])
        self.assertNotIn("restore", [op for op, _ in self.host.calls])

    def test_failed_transition_requires_pause_for_absence_cleanup_and_retains_diagnosis(self):
        self.setup_manager()
        entry, _ = self.early_bootstrap_failure()
        self.host.devices.clear()
        self.manager.tick()
        self.host.now += 30
        self.manager.tick()
        self.assertEqual(self.manager.entries[entry.device.port].phase, "failed")
        self.assertFalse(self.manager.status()["devices"][entry.device.port]["present"])
        with self.assertRaises(service.Unsafe):
            self.manager.command("resume")
        self.manager.command("release")
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertEqual(self.manager.entries, {})
        self.assertEqual(self.host.saved["leases"], {})
        recorded = self.manager.status()["recent_failures"][-1]
        self.assertEqual(recorded["resolution"], "physically_absent")
        self.assertEqual(recorded["bootstrap_diagnostic"], entry.bootstrap_diagnostic)
        restarted = service.Manager(self.host, lambda: self.host.now)
        self.assertTrue(restarted.paused)
        self.assertEqual(restarted.status()["recent_failures"][-1], recorded)
        self.assertEqual([op for op, _ in self.host.calls], ["claim", "info", "bootstrap"])

    def test_unknown_metadata_interrupts_continuous_absence_proof(self):
        for incomplete in ("all", "port"):
            with self.subTest(incomplete=incomplete):
                self.setup_manager()
                entry, _ = self.early_bootstrap_failure()
                self.manager.command("release")
                self.host.devices.clear()
                self.manager.tick()
                self.host.now += 6
                scan = self.host.scan
                if incomplete == "all":
                    self.host.scan_failure = True
                else:
                    def partial():
                        result = service.Scan()
                        result.errors[entry.device.port] = "Unreadable descriptors"
                        return result
                    self.host.scan = partial
                self.manager.tick()
                self.assertIsNone(entry.absent_since)
                self.host.scan_failure = False
                self.host.scan = scan
                self.host.now += 6
                self.manager.tick()
                self.assertTrue(self.host.saved["leases"])
                self.host.now += 9
                self.manager.tick()
                self.assertFalse(self.manager.returned())
                self.host.now += 1
                self.manager.tick()
                self.assertEqual(self.host.saved["leases"], {})

    def test_failed_transition_observes_100a_xpad_only_without_claiming_replacement(self):
        for driver in ("xpad", None, "gs_native"):
            with self.subTest(driver=driver):
                self.setup_manager()
                entry, _ = self.early_bootstrap_failure()
                self.manager.command("release")
                self.host.devices.clear()
                self.manager.tick()
                self.host.now += 1
                self.host.devices[entry.device.port] = device(generation=3, driver=driver)
                self.manager.tick()
                self.host.now += 2
                self.manager.tick()
                self.host.now += 2
                self.manager.tick()
                self.assertEqual(self.manager.returned(), driver == "xpad")
                self.assertEqual([op for op, _ in self.host.calls], ["claim", "info", "bootstrap"])
                if driver == "xpad":
                    self.assertEqual(self.host.saved["leases"], {})
                    self.assertEqual(self.manager.status()["recent_failures"][-1]["resolution"], "observed_100a_xpad")
                else:
                    self.assertEqual(entry.phase, "blocked")
                    self.assertTrue(self.host.saved["leases"])

    def test_failed_gap_and_restart_do_not_lose_quarantine_or_repeat_bootstrap(self):
        self.setup_manager()
        entry, _ = self.early_bootstrap_failure()
        self.host.devices.clear()
        self.manager.tick()
        self.host.now += 5
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.host.devices[entry.device.port] = device(pid="109c", generation=2, driver="xpad")
        self.manager.tick()
        before = copy.deepcopy(self.host.saved)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        calls, logs = list(self.host.calls), list(self.host.logs)
        with patch.object(self.host, "save", wraps=self.host.save) as save:
            for _ in range(100):
                self.host.now += 10
                self.manager.tick()
            save.assert_not_called()
        self.assertEqual(self.manager.entries[entry.device.port].phase, "blocked")
        self.assertEqual(self.host.saved, before)
        self.assertEqual(self.host.calls, calls)
        self.assertEqual(self.host.logs, logs)

    def test_same_instance_failure_no_timer_retry(self):
        self.setup_manager()
        self.start_boot()
        self.host.complete("bootstrap", rc=1)
        self.manager.tick()
        for _ in range(10):
            self.host.now += 700
            self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls].count("bootstrap"), 1)

    def test_new_instance_failure_budget(self):
        self.setup_manager()
        for index in range(1, 5):
            self.host.devices["2-3.4"] = device(generation=index)
            self.manager.entries.clear()
            self.start_boot()
            if index < 4:
                self.host.complete("bootstrap", rc=1)
                self.manager.tick()
                self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls].count("bootstrap"), 3)
        self.assertEqual([c[0] for c in self.host.calls].count("claim"), 3)
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")
        self.assertEqual(self.manager.entries["2-3.4"].phase, "cooldown")

    def test_release_cancels_bootstrap_and_does_not_repeat(self):
        self.setup_manager()
        self.start_boot()
        self.manager.command("release")
        self.manager.tick()
        self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls].count("cancel"), 1)
        self.host.complete("bootstrap", rc=1)
        self.manager.tick()
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())

    def test_bootstrap_timeout_cancels_without_sigkill_or_retry(self):
        self.setup_manager()
        self.start_boot()
        self.host.now = 41
        self.manager.tick()
        self.manager.tick()
        self.assertEqual([c[0] for c in self.host.calls], ["claim", "info", "bootstrap", "cancel"])

    def test_scan_failure_blocks_release_success_and_all_actions(self):
        self.setup_manager()
        self.host.scan_failure = True
        self.manager.command("release")
        self.manager.tick()
        self.assertFalse(self.manager.returned())
        self.assertEqual(self.host.calls, [])

    def test_zero_pad_reports_do_not_block_validated_bootstrap(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "bootstrapping")
        self.assertEqual([op for op, _ in self.host.calls], ["claim", "info", "bootstrap"])
        for _ in range(20):
            self.manager.tick()
        self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_release_during_input_wait_returns_without_end_or_bootstrap(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        self.manager.command("release")
        self.manager.tick()
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertEqual([c[0] for c in self.host.calls], ["claim", "info", "restore"])

    def test_unknown_replacement_not_ended_or_rebound_on_release(self):
        for pid in ("100a", "109c"):
            with self.subTest(pid=pid):
                self.setup_manager()
                self.boot()
                self.host.devices["2-3.4"] = device(pid=pid, generation=99, driver="gs_native")
                self.manager.command("release")
                self.manager.tick()
                self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")
                self.assertEqual([c[0] for c in self.host.calls], ["claim", "info", "bootstrap", "boot-info"])

    def test_fault_return_does_not_immediately_restart(self):
        self.setup_manager()
        self.boot()
        self.manager.tick()
        self.host.complete("info", rc=1, output="pid=109c state=2 error=-5 OUT=1 session=0")
        self.manager.tick()
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.host.devices["2-3.4"] = device(generation=3)
        for _ in range(10):
            self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "released")
        self.assertEqual([c[0] for c in self.host.calls].count("bootstrap"), 1)

    def test_pm_eagain_deadline_stops_and_cleans_up(self):
        self.setup_manager()
        self.boot()
        self.manager.tick()
        self.host.complete("info", output="pid=109c state=3 error=0 OUT=1 session=0")
        self.manager.tick()
        self.manager.tick()
        self.host.now = 16
        self.host.complete("resume", rc=3)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.host.jobs[-1]["operation"], "end")

    def test_release_race_preserves_completed_bootstrap_proof_and_ends_it(self):
        for shutdown in (False, True):
            with self.subTest(shutdown=shutdown):
                self.setup_manager()
                self.start_boot()
                self.host.devices["2-3.4"] = device(pid="109c", generation=2, driver="gs_native")
                self.host.complete("bootstrap", output=proof())
                if shutdown:
                    self.manager.stopping = True
                else:
                    self.manager.command("release")
                self.manager.tick()
                self.manager.tick()
                self.manager.tick()
                self.assertEqual(self.manager.entries["2-3.4"].device.pid, "109c")
                self.assertEqual(self.manager.entries["2-3.4"].phase, "ending")
                self.assertEqual([c[0] for c in self.host.calls].count("end"), 1)

    def test_late_success_after_deadline_is_correlated_then_ended(self):
        self.setup_manager()
        self.start_boot()
        self.host.now = 41
        self.manager.tick()
        self.host.devices["2-3.4"] = device(pid="109c", generation=2, driver="gs_native")
        self.host.complete("bootstrap", output=proof())
        self.manager.tick()
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].device.pid, "109c")
        self.assertEqual(self.host.calls[-1], ("end", "2-3.4"))

    def test_release_scopes_owned_runtime_and_leaves_second_deadband_dongle(self):
        foreign = device("7-2.1", "109c", 50, "usbfs", "another-hub")
        self.setup_manager([device(), foreign])
        self.boot()
        self.manager.command("release")
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.host.devices["2-3.4"] = device(generation=3)
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertEqual(self.host.devices[foreign.port], foreign)
        self.assertTrue(all(port != foreign.port for _, port in self.host.calls))

    def test_quarantined_foreign_port_does_not_block_owned_end(self):
        self.setup_manager()
        self.boot()
        original_scan = self.host.scan
        def scan():
            result = service.Scan()
            result.update(original_scan())
            result.errors["9-7.1"] = "Foreign interface-1 binding"
            return result
        self.host.scan = scan
        self.manager.command("release")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1], ("end", "2-3.4"))
        self.host.complete("end")
        self.manager.tick()
        self.host.devices["2-3.4"] = device(generation=3)
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertIn("9-7.1", self.manager.status()["port_errors"])

    def test_quarantined_owned_port_never_becomes_proven_absent(self):
        self.setup_manager()
        self.boot()
        def scan():
            result = service.Scan()
            result.errors["2-3.4"] = "Incomplete own descriptors"
            return result
        self.host.scan = scan
        self.manager.command("release")
        for _ in range(20):
            self.manager.tick()
            self.host.now += 10
        self.assertFalse(self.manager.returned())
        self.assertIn("2-3.4", self.manager.entries)

    def test_failed_initialization_imu_and_handoff_retain_attested_cleanup(self):
        for stage in (4, 5, 6):
            with self.subTest(stage=stage):
                self.setup_manager()
                self.failed_boot(stage)
                self.manager.command("release")
                self.manager.tick()
                self.assertEqual(self.host.calls[-1], ("end", "2-3.4"))
                self.assertEqual(self.host.asserted_tokens, [sum(b"2-3.4"), 2])
                self.host.complete("end", output="Native runtime quiesced; return unverified.")
                self.manager.tick()
                self.host.now += 31
                self.manager.tick()
                entry = self.manager.entries["2-3.4"]
                self.assertEqual(entry.phase, "blocked")
                self.assertIn("still 109c", entry.error)
                self.assertFalse(self.manager.returned())
                self.assertEqual(self.host.devices[entry.device.port].driver, "gs_native")
                self.assertTrue(self.host.saved["leases"][entry.device.port]["end_attempted"])
                self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)
                self.assertNotIn("restore", [op for op, _ in self.host.calls])

    def test_failed_proof_requires_both_exact_kernel_tokens(self):
        for field in ("port_token", "instance_token"):
            with self.subTest(field=field):
                self.setup_manager()
                self.start_boot()
                d = device(pid="109c", generation=2, driver="gs_native")
                self.host.devices[d.port] = d
                original = proof(d, failed=True)
                expected = sum(d.port.encode()) if field == "port_token" else d.address
                self.host.attest[d.port] = (1, original.replace(f"{field}={expected}", f"{field}=999"))
                self.host.complete("bootstrap", rc=1, output=original)
                for _ in range(5):
                    self.manager.tick()
                self.assertEqual(self.manager.entries[d.port].device.pid, "100a")
                self.assertFalse(self.manager.returned())
                self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_invalid_or_early_failure_status_never_adopts_new_device(self):
        payload = proof(failed=True)
        for bad in (payload.replace("failed_stage=5", "failed_stage=3"),
                    payload.replace("instance_token=2", "instance_token=0"),
                    payload.replace("instance_token=2", "instance_token=18446744073709551616"),
                    payload.replace("error=-110", "error=0"),
                    payload + "\n" + payload, "Native startup completed."):
            with self.subTest(payload=bad):
                self.setup_manager()
                self.start_boot()
                self.host.devices["2-3.4"] = device(pid="109c", generation=2, driver="gs_native")
                self.host.complete("bootstrap", rc=1, output=bad)
                for _ in range(4):
                    self.manager.tick()
                self.assertNotIn("boot-info", [op for op, _ in self.host.calls])
                self.assertNotIn("end", [op for op, _ in self.host.calls])

    def test_replacement_during_attestation_never_acquires_cleanup_authority(self):
        self.setup_manager()
        self.start_boot()
        self.host.devices["2-3.4"] = device(pid="109c", generation=2, driver="gs_native")
        self.host.complete("bootstrap", rc=1, output=proof(failed=True))
        self.manager.tick()
        self.host.devices["2-3.4"] = device(pid="109c", generation=3, driver="gs_native")
        for _ in range(4):
            self.manager.tick()
        self.assertNotIn("end", [op for op, _ in self.host.calls])
        self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")

    def test_failed_recovery_and_end_attempt_survive_manager_restart(self):
        self.setup_manager()
        self.failed_boot()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "failed")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1], ("end", "2-3.4"))
        # Simulate death after dispatch, before the old client result arrived.
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.command("release")
        self.manager.tick()
        self.manager.tick()
        self.host.now += 31
        for _ in range(5):
            self.manager.tick()
        self.assertEqual([op for op, _ in self.host.calls].count("end"), 1)
        self.assertFalse(self.manager.returned())
        with self.assertRaises(service.Unsafe):
            self.manager.command("resume")

    def test_restart_during_candidate_attestation_recovers_failure_proof(self):
        self.setup_manager()
        self.start_boot()
        d = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[d.port] = d
        self.host.attest[d.port] = (1, proof(d, failed=True))
        self.host.complete("bootstrap", rc=1, output=proof(d, failed=True))
        self.manager.tick()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[d.port].device, d)
        self.assertEqual(self.manager.entries[d.port].phase, "failed")
        self.manager.tick()
        self.assertEqual(self.host.calls[-1], ("end", d.port))

    def test_budget_is_checked_before_claim_and_survives_restart(self):
        self.setup_manager()
        self.manager.tick()
        self.manager.tick()
        self.host.complete("bootstrap", rc=1)
        self.manager.tick()
        self.manager.tick()
        self.manager.budgets["2-3.4"] = service.deque([0, 0, 0])
        self.manager.save()
        self.host.devices["2-3.4"] = device(generation=9)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        before = len(self.host.calls)
        for _ in range(5):
            self.manager.tick()
        self.assertEqual(len(self.host.calls), before)
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")
        self.assertEqual(self.manager.entries["2-3.4"].phase, "cooldown")

    def test_blocked_known_100a_retains_one_cleanup_right(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        entry = self.manager.entries["2-3.4"]
        entry.phase = "blocked"
        entry.error = "Start budget denied"
        self.manager.budgets[entry.device.port] = service.deque([0, 0, 0])
        self.manager.remember(entry)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.command("release")
        for _ in range(4):
            self.manager.tick()
            self.host.now += 1
        self.assertEqual(self.host.devices[entry.device.port].driver, "xpad")
        self.assertTrue(self.manager.returned())
        self.assertEqual(self.host.saved["leases"], {})
        self.assertEqual([op for op, _ in self.host.calls].count("restore"), 1)
        self.assertNotIn("bootstrap", [op for op, _ in self.host.calls])

    def test_unclaimed_budget_block_does_not_authorize_foreign_cleanup(self):
        self.setup_manager()
        self.manager.budget_boot = self.host.boot_id
        self.manager.budgets["2-3.4"] = service.deque([0, 0, 0])
        self.manager.tick()
        self.host.devices["2-3.4"] = replace(self.host.devices["2-3.4"], driver="gs_native")
        self.manager.command("release")
        for _ in range(5):
            self.manager.tick()
        self.assertEqual(self.host.calls, [])
        self.assertFalse(self.manager.returned())

    def test_physical_absence_clears_lease_before_release_success(self):
        self.setup_manager()
        self.failed_boot()
        self.manager.command("release")
        self.host.devices.clear()
        self.manager.tick()
        self.host.now += 2
        self.manager.tick()
        self.assertFalse(self.manager.returned())
        self.assertTrue(self.host.saved["leases"])
        self.host.now += 10
        self.manager.tick()
        self.manager.tick()
        self.host.now += 1
        self.manager.tick()
        self.assertTrue(self.manager.returned())
        self.assertEqual(self.host.saved["leases"], {})

    def test_restart_passive_100a_cleans_up_without_rebootstrap(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        for _ in range(4):
            self.manager.tick()
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")
        self.assertEqual([op for op, _ in self.host.calls].count("restore"), 1)
        self.assertNotIn("bootstrap", [op for op, _ in self.host.calls])

    def test_direct_usbcore_probe_ready_without_xpad_handover_is_attested(self):
        self.setup_manager()
        self.start_boot()
        d = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[d.port] = d
        payload = proof(d).replace("handover=1", "handover=0")
        self.host.attest[d.port] = (0, payload)
        self.host.complete("bootstrap", output=payload)
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[d.port].phase, "active")
        self.assertEqual(self.host.saved["leases"][d.port]["kernel_tokens"], [sum(d.port.encode()), 2])

    def test_blocked_109c_observation_has_no_repeated_logs_saves_or_commands(self):
        self.setup_manager()
        self.failed_boot()
        self.manager.tick()
        self.host.complete("end")
        self.manager.tick()
        self.host.now += 31
        self.manager.tick()
        calls, logs = list(self.host.calls), list(self.host.logs)
        with patch.object(self.host, "save", wraps=self.host.save) as save:
            for _ in range(100):
                self.host.now += 0.1
                self.manager.tick()
            save.assert_not_called()
        self.assertEqual(self.host.calls, calls)
        self.assertEqual(self.host.logs, logs)

    def test_normal_replacement_cannot_hide_unresolved_lease(self):
        self.setup_manager()
        self.boot()
        self.manager.command("release")
        self.host.devices["2-3.4"] = device(generation=3, parent="replacement-hub")
        self.manager.tick()
        self.host.now += 3
        self.manager.tick()
        self.assertTrue(self.host.saved["leases"])
        self.assertFalse(self.manager.returned())

    def test_100a_quarantine_does_not_rewrite_identical_errors_forever(self):
        for cause in ("restore", "hub", "foreign"):
            with self.subTest(cause=cause):
                self.setup_manager()
                self.host.pad = 0
                self.manager.tick()
                self.manager.tick()
                self.manager.command("release")
                if cause == "restore":
                    self.host.restore = Mock(side_effect=service.Unsafe("Synthetic bind failure"))
                elif cause == "hub":
                    self.host.devices["2-3.4"] = device(parent="replacement-hub", driver="gs_native")
                else:
                    self.host.devices["2-3.4"] = device(generation=99, driver="gs_native")
                self.manager.tick()
                self.manager.tick()
                logs = len(self.host.logs)
                with patch.object(self.host, "save", wraps=self.host.save) as save:
                    for _ in range(100):
                        self.manager.tick()
                    save.assert_not_called()
                self.assertEqual(len(self.host.logs), logs)
                self.assertFalse(self.manager.returned())

    def test_partial_initial_unbind_retains_bounded_100a_cleanup(self):
        self.setup_manager()
        def partial(d):
            self.host.devices[d.port] = replace(d, driver=None)
            raise service.Unsafe("Native bind failed after xpad unbind")
        self.host.race = partial
        self.manager.tick()
        self.manager.tick()
        for _ in range(10):
            self.manager.tick()
        self.assertEqual(self.host.devices["2-3.4"].driver, "xpad")
        self.assertEqual([op for op, _ in self.host.calls], ["claim", "restore"])
        self.assertEqual(self.host.saved["leases"], {})

    def test_failed_restore_does_not_loop_or_discard_recovery(self):
        self.setup_manager()
        self.host.pad = 0
        self.manager.tick()
        self.manager.command("release")
        with patch.object(self.host, "restore", side_effect=service.Unsafe("Synthetic bind failure")) as restore:
            for _ in range(5):
                self.manager.tick()
            restore.assert_called_once()
        self.assertTrue(self.host.saved["leases"])
        self.assertFalse(self.manager.returned())

    def test_new_host_boot_drops_old_kernel_ownership_but_not_same_boot_restart(self):
        self.setup_manager()
        self.failed_boot()
        original = copy.deepcopy(self.host.saved)
        same_boot = service.Manager(self.host, lambda: self.host.now)
        same_boot.tick()
        self.assertEqual(same_boot.entries["2-3.4"].phase, "attesting")
        self.assertTrue(self.host.saved["leases"])
        self.host.saved = original
        self.host.devices["2-3.4"] = device(generation=99, parent="new-boot-hub")
        self.host.boot_id = "another-synthetic-boot"
        restart = service.Manager(self.host, lambda: self.host.now)
        before = len(self.host.calls)
        restart.tick()
        self.assertEqual(self.host.calls[before:], [("claim", "2-3.4"), ("info", "2-3.4")])
        self.assertEqual(restart.entries["2-3.4"].phase, "checking_start")
        self.assertEqual(restart.budgets["2-3.4"], service.deque())
        self.assertEqual(self.host.saved["boot_id"], self.host.boot_id)

    def test_explicit_deadband_pause_survives_host_reboot(self):
        self.setup_manager()
        self.failed_boot()
        self.manager.command("release")
        self.host.boot_id = "another-synthetic-boot"
        self.host.devices["2-3.4"] = device(generation=99, parent="new-boot-hub")
        restart = service.Manager(self.host, lambda: self.host.now)
        before = len(self.host.calls)
        restart.tick()
        self.assertTrue(restart.paused)
        self.assertEqual(self.host.saved["leases"], {})
        self.assertEqual(len(self.host.calls), before)

    def test_bootstrap_finishes_between_scan_and_poll_without_losing_tokens(self):
        for failed in (False, True):
            with self.subTest(failed=failed):
                self.setup_manager()
                self.start_boot()
                d = device(pid="109c", generation=2, driver="gs_native")
                original_poll = self.host.poll
                def poll(job):
                    if job["operation"] == "bootstrap" and job["result"] is None:
                        self.host.devices[d.port] = d
                        payload = proof(d, failed=failed)
                        self.host.attest[d.port] = (int(failed), payload)
                        job["result"] = (int(failed), payload)
                    return original_poll(job)
                self.host.poll = poll
                self.manager.tick()  # scan still saw old100a before poll.
                self.manager.tick()
                self.assertEqual(self.manager.entries[d.port].device, d)
                self.assertEqual(self.manager.entries[d.port].phase, "failed" if failed else "active")
                self.assertEqual([op for op, _ in self.host.calls].count("bootstrap"), 1)

    def test_terminal_proof_waits_boundedly_for_metadata_and_survives_restart(self):
        self.setup_manager()
        self.start_boot()
        self.host.devices.clear()
        self.host.complete("bootstrap", rc=1, output=proof(failed=True))
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "locating")
        self.assertEqual(self.host.saved["leases"]["2-3.4"]["kernel_tokens"], [sum(b"2-3.4"), 2])
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.host.now += 1
        d = device(pid="109c", generation=2, driver="gs_native")
        self.host.devices[d.port] = d
        self.host.attest[d.port] = (1, proof(d, failed=True))
        self.manager.tick()
        self.manager.tick()
        self.assertEqual(self.manager.entries[d.port].device, d)
        self.assertEqual(self.manager.entries[d.port].phase, "failed")

    def test_missing_candidate_expires_without_new_commands_or_bootstrap(self):
        self.setup_manager()
        self.start_boot()
        self.host.devices.clear()
        self.host.complete("bootstrap", rc=1, output=proof(failed=True))
        self.manager.tick()
        self.host.now += service.HANDOFF_SECONDS
        self.manager.tick()
        self.assertEqual(self.manager.entries["2-3.4"].phase, "blocked")
        self.assertEqual([op for op, _ in self.host.calls], ["claim", "info", "bootstrap"])


class ProcessAndControl(unittest.TestCase):
    def test_bootstrap_diagnostic_bounds_output_and_keeps_reported_failure_stage(self):
        suffix = ("BOOTSTRAP: No such device\nbootstrap state=8 error=-19 failed_stage=2 "
                  "pad=1 imu=0 handover=0 port_token=9 instance_token=10\n")
        output = "initial command\n" + "🎮" * 5000 + suffix
        diagnostic = service.bootstrap_diagnostic(1, output, False, "synthetic-source")
        self.assertLessEqual(len(diagnostic["combined_output"].encode()), service.DIAGNOSTIC_BYTES)
        self.assertTrue(diagnostic["combined_output"].startswith("initial command"))
        self.assertTrue(diagnostic["combined_output"].endswith(suffix))
        self.assertTrue(diagnostic["excerpt_truncated"])
        self.assertEqual(diagnostic["output_bytes"], len(output.encode()))
        self.assertEqual(diagnostic["output_sha256"], service.hashlib.sha256(output.encode()).hexdigest())
        self.assertIn("supervisor-bounded", diagnostic["output_scope"])
        self.assertEqual(diagnostic["reported_kernel_status"]["failed_stage"], 2)
        self.assertEqual(service.checked_diagnostic(diagnostic), diagnostic)
        self.assertIsNone(service.boot_proof(output))

    def test_ambiguous_bootstrap_records_are_raw_diagnostic_only(self):
        output = proof(failed=True) + "\n" + proof(failed=True, stage=4)
        diagnostic = service.bootstrap_diagnostic(1, output, True, "source")
        self.assertIsNone(diagnostic["reported_kernel_status"])
        self.assertTrue(diagnostic["timed_out"])
        self.assertIn("failed_stage=4", diagnostic["combined_output"])
        self.assertIsNone(service.boot_proof(output))

    def test_saved_diagnostic_types_and_sizes_are_checked_before_any_host_action(self):
        valid = service.bootstrap_diagnostic(1, "error", False, "source")
        corrupt = (None, [], {**valid, "combined_output": "x" * (service.DIAGNOSTIC_BYTES + 1)},
                   {**valid, "returncode": True}, {**valid, "reported_kernel_status": [1]},
                   {**valid, "output_sha256": "x" * 64}, {**valid, "source_instance": "x" * 4097},
                   {**valid, "unexpected": "value"}, {**valid, "output_bytes": -1})
        for value in corrupt:
            with self.subTest(value=str(value)[:60]):
                host = Fake([])
                host.saved = {"leases": {"2-3.4": {"device": service.asdict(device()),
                              "phase": "failed", "bootstrap_diagnostic": value}}}
                with self.assertRaises(service.Unsafe):
                    service.Manager(host, lambda: host.now)
                self.assertEqual(host.calls, [])

    def test_failure_history_is_bounded_and_corruption_is_not_silently_truncated(self):
        host = Fake([])
        manager = service.Manager(host, lambda: host.now)
        for index in range(service.RECENT_FAILURES + 3):
            d = device(port=f"2-{index + 1}")
            entry = service.Entry(d, "failed", error=f"failure-{index}",
                                  bootstrap_diagnostic=service.bootstrap_diagnostic(1, "error", False, d.token))
            manager.record_failure(entry)
        manager.save()
        self.assertEqual(len(manager.recent_failures), service.RECENT_FAILURES)
        self.assertEqual(manager.recent_failures[0]["message"], "failure-3")
        restarted = service.Manager(host, lambda: host.now)
        self.assertEqual(restarted.recent_failures, manager.recent_failures)
        valid = copy.deepcopy(host.saved)
        for bad in (None, {}, [valid["recent_failures"][0]] * (service.RECENT_FAILURES + 1),
                    [{**valid["recent_failures"][0], "message": "x" * 1025}],
                    [{**valid["recent_failures"][0], "bootstrap_diagnostic": []}]):
            with self.subTest(value=str(bad)[:60]):
                host.saved = {**valid, "recent_failures": bad}
                with self.assertRaises(service.Unsafe):
                    service.Manager(host, lambda: host.now)
                self.assertEqual(host.calls, [])

    def test_exit_between_eagain_and_poll_keeps_final_success_record(self):
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        process = Mock()
        process.stdout = os.fdopen(read_fd, "rb", buffering=0)
        payload = b"bootstrap state=7 error=0\nNative startup completed.\n"
        def exit_now():
            os.write(write_fd, payload)
            os.close(write_fd)
            return 0
        process.poll.side_effect = exit_now
        host = service.Host("/never/executed", "/never/read")
        try:
            result = host.poll(service.Job(process))
            self.assertEqual(result, (0, payload.decode()))
            self.assertTrue(process.stdout.closed)
        finally:
            process.stdout.close()

    def test_inherited_open_stdout_does_not_block_or_claim_success(self):
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        process = Mock()
        process.stdout = os.fdopen(read_fd, "rb", buffering=0)
        process.poll.return_value = 0
        host = service.Host("/never/executed", "/never/read")
        try:
            result = host.poll(service.Job(process))
            self.assertEqual(result[0], 1)
            self.assertIn("stdout remained open", result[1])
            self.assertTrue(process.stdout.closed)
        finally:
            process.stdout.close()
            os.close(write_fd)

    def test_output_limit_retains_at_most_64k_and_reports_failed_completion(self):
        process = Mock()
        process.stdout.fileno.return_value = 123
        process.poll.return_value = 0
        host = service.Host("/never/executed", "/never/read")
        job = service.Job(process)
        with patch.object(service.os, "read", side_effect=[b"x" * 4096] * 17 + [b""]):
            result = host.poll(job)
        self.assertEqual(result[0], 1)
        self.assertIn("output exceeded limit", result[1])
        self.assertEqual(len(job.output), 65536)
        process.stdout.close.assert_called_once()

    def test_broken_client_response_does_not_undo_release_or_crash_service(self):
        host = Fake([])
        manager = service.Manager(host, lambda: host.now)
        conn = Mock()
        conn.getsockopt.return_value = service.struct.pack("3i", 1, 0, 0)
        conn.recv.return_value = b"release\n"
        conn.sendall.side_effect = BrokenPipeError("disconnected client")
        service.serve_connection(conn, manager)
        self.assertTrue(manager.paused)
        self.assertTrue(host.saved["paused"])
        conn.sendall.assert_called_once()
        following = Mock()
        following.getsockopt.return_value = service.struct.pack("3i", 2, 0, 0)
        following.recv.return_value = b"status\n"
        service.serve_connection(following, manager)
        response = service.json.loads(following.sendall.call_args.args[0])
        self.assertTrue(response["ok"])
        self.assertTrue(response["paused"])

    def test_failed_receive_and_error_response_are_both_isolated(self):
        host = Fake([])
        manager = service.Manager(host, lambda: host.now)
        conn = Mock()
        conn.getsockopt.return_value = service.struct.pack("3i", 1, 0, 0)
        conn.recv.side_effect = TimeoutError("client timed out")
        conn.sendall.side_effect = BrokenPipeError("client left")
        service.serve_connection(conn, manager)
        conn.sendall.assert_called_once()
        self.assertFalse(manager.paused)

    def test_nonroot_control_request_never_runs_command(self):
        host = Fake([])
        manager = service.Manager(host, lambda: host.now)
        conn = Mock()
        conn.getsockopt.return_value = service.struct.pack("3i", 1, 1000, 1000)
        conn.recv.return_value = b"release\n"
        service.serve_connection(conn, manager)
        conn.recv.assert_not_called()
        self.assertFalse(manager.paused)
        self.assertFalse(service.json.loads(conn.sendall.call_args.args[0])["ok"])


class Adapter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sysfs = self.root / "sys"
        self.proc = self.root / "proc"
        (self.sysfs / "bus/usb/devices").mkdir(parents=True)
        self.proc.mkdir()
        boot = self.proc / "sys/kernel/random/boot_id"
        boot.parent.mkdir(parents=True)
        boot.write_text("00000000-0000-0000-0000-000000000001")
        self.host = service.Host("/never/executed", self.root / "state", self.sysfs, self.proc)
        claim = self.sysfs / "bus/usb/drivers/gs_native/claim_100a"
        claim.parent.mkdir(parents=True)
        claim.write_text("")
        (claim.parent / "claim_105e").write_text("")
        for name in ('acquire_100a', 'acquire_105e', 'acquire_109c'):
            (claim.parent / name).write_text('')
        fallback = self.sysfs / 'bus/usb/drivers/xpad/bind'
        fallback.parent.mkdir(parents=True)
        fallback.write_text('')

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, port="6-2.3", pid="100a"):
        p = self.sysfs / "bus/usb/devices" / port
        p.mkdir()
        attributes = {"idVendor": "3537", "idProduct": pid, "bConfigurationValue": "1",
                      "busnum": "6", "devnum": "9"}
        for name, value in attributes.items():
            (p / name).write_text(value)
        for index in range(2):
            interface = p / f"{port}:1.{index}"
            interface.mkdir()
            cls = ("ff", "5d", "01") if pid == "100a" and index == 0 else (
                ("03", "00", "00") if pid == "100a" else ("ff", "47", "d0"))
            attrs = {"bInterfaceNumber": f"{index:02x}", "bAlternateSetting": "0"}
            attrs.update(zip(("bInterfaceClass", "bInterfaceSubClass", "bInterfaceProtocol"), cls))
            for name, value in attrs.items():
                (interface / name).write_text(value)
            driver = "xpad" if index == 0 else "usbhid" if pid == "100a" else None
            if driver:
                (interface / "driver").symlink_to(self.sysfs / "bus/usb/drivers" / driver)
            endpoints = [2, 0x82] if index == 0 else [4, 0x84] if pid == "100a" else []
            for endpoint in endpoints:
                ep = interface / f"ep_{endpoint:02x}"
                ep.mkdir()
                for name, value in {"bEndpointAddress": f"{endpoint:02x}", "bmAttributes": "03",
                                    "bInterval": "01",
                                    "wMaxPacketSize": "0020" if pid == "100a" and index == 0 else "0040"}.items():
                    (ep / name).write_text(value)
        return p

    def test_real_metadata_adapter_reads_only_injected_tree(self):
        self.fixture()
        d = self.host.scan()["6-2.3"]
        self.assertEqual((d.pid, d.driver, d.bus, d.address), ("100a", "xpad", 6, 9))
        self.assertEqual(d.sysfs_inode, (self.sysfs / "bus/usb/devices/6-2.3").stat().st_ino)
        self.assertEqual(d.parent_inode, (self.sysfs / "bus/usb/devices").stat().st_ino)
        self.host.guard(d)

    def test_empty_or_invalid_decimal_metadata_names_field_and_quarantines_port(self):
        target = self.fixture()
        self.fixture(port="9-7.1")
        for field in ("bConfigurationValue", "busnum", "devnum", "6-2.3:1.0/bAlternateSetting"):
            path = target / field
            original = path.read_text()
            for value, kind in (("", "Empty"), (" \n", "Empty"), ("bad", "Invalid"), ("1.5", "Invalid")):
                with self.subTest(field=field, value=value):
                    path.write_text(value)
                    with self.assertRaisesRegex(service.Unsafe, kind + " USB metadata") as caught:
                        self.host.value(path, 10)
                    self.assertIn(str(path), str(caught.exception))
                    self.assertIn("base 10", str(caught.exception))
                    with patch.object(self.host, "write_binding") as bind, \
                            patch.object(self.host, "write_claim") as claim:
                        scanned = self.host.scan()
                        self.assertNotIn(target.name, scanned)
                        self.assertIn("9-7.1", scanned)
                        self.assertEqual(list(scanned.errors), [target.name])
                        self.assertIn(str(path), scanned.errors[target.name])
                        bind.assert_not_called()
                        claim.assert_not_called()
                    path.write_text(original)
        self.assertEqual(set(self.host.scan()), {target.name, "9-7.1"})

    def test_invalid_hexadecimal_metadata_keeps_path_and_never_becomes_device(self):
        target = self.fixture()
        for field, value in (("idVendor", "not-hex"), ("idProduct", "")):
            path = target / field
            original = path.read_text()
            path.write_text(value)
            scanned = self.host.scan()
            self.assertEqual(scanned, {})
            self.assertIn(str(path), scanned.errors[target.name])
            self.assertIn("base 16", scanned.errors[target.name])
            path.write_text(original)

    def test_105e_scan_uses_exact_existing_gip_descriptor_contract(self):
        # Synthetic metadata, using the observed 105e interface shape. No
        # payload or authorization is inferred from these matching fields.
        p = self.fixture(pid="109c")
        interface = p / "6-2.3:1.0"
        (interface / "ep_82/bInterval").write_text("02")
        (interface / "ep_02/bInterval").write_text("04")
        self.assertEqual(self.host.scan()["6-2.3"].pid, "109c")
        (p / "idProduct").write_text("105e")
        with patch.object(self.host, "write_binding") as bind, \
                patch.object(self.host, "write_claim") as claim:
            result = self.host.scan()
            self.assertEqual(result["6-2.3"].pid, "105e")
            self.assertEqual(result.errors, {})
            bind.assert_not_called()
            claim.assert_not_called()
        self.assertEqual((interface / "driver").resolve().name, "xpad")

    def test_105e_claim_uses_only_its_pid_pinned_attribute_and_verified_restore(self):
        p = self.fixture(pid="105e")
        original = self.host.scan()[p.name]
        calls = []
        def write(d, driver, action):
            self.host.guard(d)
            calls.append((driver, action))
            link = p / d.interface / "driver"
            if action == "unbind":
                link.unlink()
            else:
                link.symlink_to(self.sysfs / "bus/usb/drivers" / driver)
        real_claim = self.host.write_acquire
        def claim(d):
            real_claim(d)
            calls.append(("gs_native", "acquire_105e"))
            (p / d.interface / "driver").unlink()
            (p / d.interface / "driver").symlink_to(self.sysfs / "bus/usb/drivers/gs_native")
        with patch.object(self.host, "write_binding", side_effect=write), \
                patch.object(self.host, "write_acquire", side_effect=claim):
            self.host.claim(original)
            current = self.host.scan()[p.name]
            self.assertEqual(current.token, original.token)
            self.assertEqual(current.driver, "gs_native")
            self.host.restore(current)
        self.assertEqual(calls, [("gs_native", "acquire_105e"),
                                 ("gs_native", "unbind"), ("xpad", "bind")])
        expected = f"1 6-2.3:1.0 6 9 {original.sysfs_inode} {original.parent_inode}\n"
        self.assertEqual((self.sysfs / "bus/usb/drivers/gs_native/acquire_105e").read_text(), expected)
        self.assertEqual((self.sysfs / "bus/usb/drivers/gs_native/claim_100a").read_text(), "")
        self.assertEqual(self.host.scan()[p.name].pid, "105e")
        self.assertEqual(self.host.scan()[p.name].driver, "xpad")

    def test_105e_missing_claim_contract_and_foreign_owner_leave_xpad_untouched(self):
        p = self.fixture(pid="105e")
        (self.sysfs / "bus/usb/drivers/gs_native/acquire_105e").unlink()
        with patch.object(self.host, "write_binding") as bind:
            with self.assertRaises(service.Unsafe):
                self.host.claim(self.host.scan()[p.name])
            bind.assert_not_called()
        self.assertEqual(self.host.scan()[p.name].driver, "xpad")

    def test_105e_wrong_descriptors_or_interface_owner_are_quarantined(self):
        p = self.fixture(pid="105e")
        for path, value in ((p / "idVendor", "045e"),
                            (p / "idProduct", "105d"), (p / "idProduct", "1022"),
                            (p / "6-2.3:1.0/bInterfaceProtocol", "01"),
                            (p / "6-2.3:1.0/ep_82/wMaxPacketSize", "0020"),
                            (p / "6-2.3:1.0/ep_02/bInterval", "00"),
                            (p / "6-2.3:1.1/bAlternateSetting", "1")):
            with self.subTest(path=path, value=value):
                original = path.read_text()
                path.write_text(value)
                self.assertNotIn(p.name, self.host.scan())
                path.write_text(original)
        (p / "6-2.3:1.1/driver").symlink_to(self.sysfs / "bus/usb/drivers/usbhid")
        self.assertNotIn(p.name, self.host.scan())
        self.assertIn(p.name, self.host.scan().errors)

    def test_105e_claim_rejects_wrong_pid_and_replacement_before_write(self):
        p = self.fixture(pid="105e")
        original = self.host.scan()[p.name]
        for pid in ("105d", "1022", "109c/../../acquire_100a", "105e/../../claim_100a"):
            with self.subTest(pid=pid), self.assertRaises(service.Unsafe):
                self.host.claim_request(replace(original, pid=pid))
        (p / "6-2.3:1.0/driver").unlink()
        unbound = self.host.scan()[p.name]
        (p / "devnum").write_text("10")
        with self.assertRaises(service.Unsafe):
            self.host.write_claim(unbound)
        self.assertEqual((self.sysfs / "bus/usb/drivers/gs_native/claim_105e").read_text(), "")

    def test_105e_client_direct_bootstrap_has_no_handoff_and_native_info_is_tokenized(self):
        p = self.fixture(pid="105e")
        link = p / "6-2.3:1.0/driver"
        link.unlink()
        link.symlink_to(self.sysfs / "bus/usb/drivers/gs_native")
        d = self.host.scan()[p.name]
        with patch.object(service.subprocess, "Popen") as spawn, patch.object(service.os, "set_blocking"):
            self.host.start("bootstrap", d)
            self.assertEqual(spawn.call_args.args[0], [self.host.client, "bootstrap", d.node])
            for operation in ("info", "end"):
                with self.subTest(operation=operation):
                    self.host.start(operation, d, [3, 4])
                    self.assertEqual(spawn.call_args.args[0],
                                     [self.host.client, operation, d.node, "--expect-port", "3", "--expect-instance", "4"])
                    with self.assertRaises(service.Unsafe):
                        self.host.start(operation, d, None)

    def test_descriptor_changes_rejected(self):
        p = self.fixture()
        ep = p / "6-2.3:1.0/ep_82/wMaxPacketSize"
        ep.write_text("0040")
        result = self.host.scan()
        self.assertNotIn("6-2.3", result)
        self.assertIn("6-2.3", result.errors)

    def test_incomplete_enumeration_is_unknown_not_absence(self):
        p = self.fixture()
        (p / "idProduct").unlink()
        result = self.host.scan()
        self.assertNotIn("6-2.3", result)
        self.assertIn("6-2.3", result.errors)

    def test_boot_id_separates_identical_sysfs_instances(self):
        self.fixture()
        first = self.host.scan()["6-2.3"]
        boot = self.proc / "sys/kernel/random/boot_id"
        boot.write_text("00000000-0000-0000-0000-000000000002")
        fresh = service.Host("/never/executed", self.root / "state", self.sysfs, self.proc)
        second = fresh.scan()["6-2.3"]
        self.assertNotEqual(first.token, second.token)
        self.assertNotEqual(first.parent, second.parent)

    def test_foreign_handle_and_deleted_fd_rejected(self):
        self.fixture()
        d = self.host.scan()["6-2.3"]
        fds = self.proc / "999999/fd"
        fds.mkdir(parents=True)
        for target in ("/dev/bus/usb/006/009", "/dev/bus/usb/006/009 (deleted)", d.node):
            with self.subTest(target=target):
                link = fds / "10"
                link.symlink_to(target)
                with self.assertRaises(service.Unsafe):
                    self.host.guard(d)
                link.unlink()

    def native_fixture(self):
        p = self.fixture(pid="109c")
        link = p / "6-2.3:1.0/driver"
        link.unlink()
        link.symlink_to(self.sysfs / "bus/usb/drivers/gs_native")
        return p, self.host.scan()[p.name]

    def test_observation_ignores_usbfs_fd_but_not_native_control_owner(self):
        _, d = self.native_fixture()
        fds = self.proc / "999999/fd"
        fds.mkdir(parents=True)
        link = fds / "10"
        for name in ("/dev/bus/usb/006/009", "/dev/bus/usb/006/009 (deleted)",
                     "/dev/input/event13"):
            with self.subTest(name=name):
                link.symlink_to(name)
                self.host.observe_guard(d)
                if name.startswith("/dev/bus/usb"):
                    with self.assertRaises(service.Unsafe):
                        self.host.guard(d)
                link.unlink()
        for name in (d.node, d.node + " (deleted)"):
            with self.subTest(name=name):
                link.symlink_to(name)
                with self.assertRaises(service.StatusBusy):
                    self.host.observe_guard(d)
                with self.assertRaises(service.Unsafe) as failure:
                    self.host.guard(d)
                self.assertNotIsInstance(failure.exception, service.StatusBusy)
                link.unlink()

    def test_observation_rejects_wrong_binding_and_postscan_replacement(self):
        _, d = self.native_fixture()
        for replacement in (replace(d, token="new-object"), replace(d, driver="usbfs"), None):
            with self.subTest(replacement=replacement):
                with patch.object(self.host, "scan", side_effect=[{d.port: d}, {d.port: replacement}]):
                    with self.assertRaises(service.Unsafe) as failure:
                        self.host.observe_guard(d)
                    self.assertNotIsInstance(failure.exception, service.StatusBusy)
        with patch.object(self.host, "scan", return_value={d.port: replace(d, driver="xpad")}):
            with self.assertRaises(service.Unsafe):
                self.host.observe_guard(replace(d, driver="xpad"))

    def test_replacement_takes_precedence_over_observed_control_conflict(self):
        _, d = self.native_fixture()
        fds = self.proc / "999999/fd"
        fds.mkdir(parents=True)
        (fds / "10").symlink_to(d.node)
        with patch.object(self.host, "scan", side_effect=[{d.port: d}, {d.port: replace(d, token="new")} ]):
            with self.assertRaises(service.Unsafe) as failure:
                self.host.observe_guard(d)
        self.assertNotIsInstance(failure.exception, service.StatusBusy)

    def test_getter_start_only_relaxes_usbfs_check_and_passes_same_fd_tokens(self):
        _, d = self.native_fixture()
        fds = self.proc / "999999/fd"
        fds.mkdir(parents=True)
        (fds / "10").symlink_to("/dev/bus/usb/006/009")
        with patch.object(service.subprocess, "Popen") as spawn, patch.object(service.os, "set_blocking"):
            for command in ("bootstrap", "resume", "end"):
                with self.subTest(command=command), self.assertRaises(service.Unsafe):
                    self.host.start(command, d, [3, 4])
            spawn.assert_not_called()
            self.host.start("info", d, [3, 4])
            self.assertEqual(spawn.call_args.args[0],
                             [self.host.client, "info", d.node, "--expect-port", "3", "--expect-instance", "4"])
            self.assertTrue(spawn.call_args.kwargs["close_fds"])
            self.host.start("boot-info", d)
            self.assertEqual(spawn.call_args.args[0], [self.host.client, "boot-info", d.node])
        with patch.object(service.subprocess, "Popen") as spawn:
            for invalid in (None, [], [0, 4], [3, True], [3, 2**64]):
                with self.subTest(tokens=invalid), self.assertRaises(service.Unsafe):
                    self.host.start("info", d, invalid)
            spawn.assert_not_called()

    def test_usbfs_observer_cannot_bypass_haptic_guard(self):
        _, d = self.native_fixture()
        fds = self.proc / "999999/fd"
        fds.mkdir(parents=True)
        (fds / "10").symlink_to("/dev/bus/usb/006/009")
        with patch.object(service.os, "open") as opened, patch.object(service.fcntl, "ioctl") as ioctl:
            with self.assertRaises(service.Unsafe):
                self.host.haptics(d, [(0, 20, 100, False)])
            opened.assert_not_called()
            ioctl.assert_not_called()

    def test_guard_rechecks_identity(self):
        p = self.fixture()
        d = self.host.scan()["6-2.3"]
        (p / "devnum").write_text("10")
        with self.assertRaises(service.Unsafe):
            self.host.guard(d)

    def test_pinned_tmr_observation_reads_metadata_without_process_enumeration(self):
        p,d=self.native_fixture()
        original=Path.iterdir
        def no_proc(path):
            if path==self.proc:raise AssertionError('Display must not scan process FDs')
            return original(path)
        with patch.object(Path,'iterdir',no_proc):
            self.host.tmr_guard(d)
            for replacement in (replace(d,token='replacement'),replace(d,driver='xpad')):
                with self.subTest(replacement=replacement),self.assertRaises(service.Unsafe):
                    self.host.tmr_guard(replacement)
            (p/'bConfigurationValue').write_text('')
            with self.assertRaises(service.Unsafe):self.host.tmr_guard(d)

    def test_tmr_read_check_never_replaces_full_usb_command_guard(self):
        _,d=self.native_fixture()
        fds=self.proc/'999999/fd';fds.mkdir(parents=True)
        (fds/'10').symlink_to('/dev/bus/usb/006/009')
        self.host.tmr_guard(d)
        with self.assertRaises(service.Unsafe):self.host.guard(d)

    def test_claim_handover_order_and_restore(self):
        self.fixture()
        calls = []
        def write(d, driver, action):
            self.host.guard(d)
            calls.append((driver, action))
            link = self.sysfs / "bus/usb/devices" / d.port / d.interface / "driver"
            if action == "unbind":
                link.unlink()
            else:
                link.symlink_to(self.sysfs / "bus/usb/drivers" / driver)
        def claim(d):
            self.host.guard(d)
            (self.sysfs / "bus/usb/devices" / d.port / d.interface / "driver").unlink()
            write(replace(d, driver=None), "gs_native", "acquire_100a")
        with patch.object(self.host, "write_binding", side_effect=write), patch.object(self.host, "write_acquire", side_effect=claim):
            self.host.claim(self.host.scan()["6-2.3"])
            self.host.restore(self.host.scan()["6-2.3"])
        self.assertEqual(calls, [("gs_native", "acquire_100a"),
                                 ("gs_native", "unbind"), ("xpad", "bind")])

    def test_bind_race_stops_before_stealing_foreign_driver(self):
        self.fixture()
        real_acquire = self.host.write_acquire
        def acquire(d):
            link = self.sysfs / "bus/usb/devices" / d.port / d.interface / "driver"
            link.unlink()
            link.symlink_to(self.sysfs / "bus/usb/drivers/foreign")
            real_acquire(d)
        with patch.object(self.host, "write_acquire", side_effect=acquire), \
                patch.object(self.host, "write_binding") as bind:
            with self.assertRaises(service.Unsafe):
                self.host.claim(self.host.scan()["6-2.3"])
            bind.assert_not_called()
        self.assertEqual((self.sysfs / "bus/usb/drivers/gs_native/acquire_100a").read_text(), '')

    def test_claim_contract_is_exact_and_versioned_on_injected_sysfs(self):
        self.fixture()
        d = self.host.scan()["6-2.3"]
        link = self.sysfs / "bus/usb/devices" / d.port / d.interface / "driver"
        link.unlink()
        d = self.host.scan()[d.port]
        self.host.write_claim(d)
        request = (self.sysfs / "bus/usb/drivers/gs_native/claim_100a").read_text()
        self.assertEqual(request, f"1 6-2.3:1.0 6 9 {d.sysfs_inode} {d.parent_inode}\n")

    def test_missing_claim_attribute_stops_before_xpad_unbind(self):
        self.fixture()
        (self.sysfs / "bus/usb/drivers/gs_native/acquire_100a").unlink()
        with patch.object(self.host, "write_binding") as write:
            with self.assertRaises(service.Unsafe):
                self.host.claim(self.host.scan()["6-2.3"])
            write.assert_not_called()
        self.assertEqual(self.host.scan()["6-2.3"].driver, "xpad")

    def test_64_byte_interface_name_is_rejected_before_xpad_unbind(self):
        port = "6-" + "1" * 58
        self.fixture(port=port)
        d = self.host.scan()[port]
        self.assertEqual(len(d.interface), 64)
        with patch.object(self.host, "write_binding") as write:
            with self.assertRaises(service.Unsafe):
                self.host.claim(d)
            write.assert_not_called()
        self.assertEqual(self.host.scan()[port].driver, "xpad")

    def test_scoped_claim_rejects_replacement_before_attribute_write(self):
        p = self.fixture()
        (p / "6-2.3:1.0/driver").unlink()
        original = self.host.scan()["6-2.3"]
        (p / "devnum").write_text("10")
        with self.assertRaises(service.Unsafe):
            self.host.write_claim(original)
        self.assertEqual((self.sysfs / "bus/usb/drivers/gs_native/claim_100a").read_text(), "")

    def test_claim_never_adopts_already_native_100a(self):
        p = self.fixture()
        link = p / "6-2.3:1.0/driver"
        link.unlink()
        link.symlink_to(self.sysfs / "bus/usb/drivers/gs_native")
        with patch.object(self.host, "write_binding") as write:
            with self.assertRaises(service.Unsafe):
                self.host.claim(self.host.scan()["6-2.3"])
            write.assert_not_called()

    def test_claim_rejects_missing_or_out_of_range_identity_before_write(self):
        self.fixture()
        d = self.host.scan()["6-2.3"]
        for invalid in (replace(d, sysfs_inode=0), replace(d, parent_inode=0),
                        replace(d, bus=65536), replace(d, address=128),
                        replace(d, sysfs_inode=2**64), replace(d, parent_inode=-1)):
            with self.subTest(device=invalid):
                with self.assertRaises(service.Unsafe):
                    self.host.claim_request(invalid)

    def test_restore_never_touches_109c(self):
        self.fixture(pid="109c")
        with patch.object(self.host, "write_binding") as write:
            with self.assertRaises(service.Unsafe):
                self.host.restore(self.host.scan()["6-2.3"])
            write.assert_not_called()

    def test_nonroot_cli_cannot_enter_daemon(self):
        with patch.object(service.os, "geteuid", return_value=1000), patch.object(service, "daemon") as run, patch("sys.stderr", new=io.StringIO()):
            with self.assertRaises(SystemExit):
                service.main(["daemon"])
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
