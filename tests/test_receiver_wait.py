#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Persistent standby policy with fake time/devices only; no device backend."""
import unittest
from dataclasses import replace

import test_service_manager as fixture

s, device = fixture.service, fixture.device


def waiting(d):
    return (f'bootstrap state=9 error=0 failed_stage=0 pad=0 imu=0 handover=0 '
            f'port_token={sum(d.port.encode())} instance_token={d.address}\n'
            'Native receiver waiting. One setup completed; no runtime readiness or radio connection claimed.')


class ReceiverWait(unittest.TestCase):
    def boot(self, pid='109c'):
        old = device(pid=pid, driver=None)
        self.h = fixture.Fake([old])
        self.m = s.Manager(self.h, lambda: self.h.now)
        self.tick(2 if pid == '100a' else 1)
        d = device(pid='109c', generation=2, driver='gs_native') if pid == '100a' else replace(old, driver='gs_native')
        self.h.devices[d.port] = d
        self.h.attest[d.port] = (0, waiting(d))
        self.h.complete('bootstrap', output=waiting(d))
        self.tick(2)
        self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
        self.d = d
        return d

    def tick(self, n=1):
        for _ in range(n):
            self.m.tick()

    def poll(self):
        self.h.now += 3
        self.tick(2)

    def test_day_of_waiting_never_reinitializes_or_declares_ready(self):
        for pid in ('100a', '109c', '105e'):
            with self.subTest(pid=pid):
                d = self.boot(pid)
                for _ in range(24):
                    self.h.now += 3600
                    self.tick(2)
                self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
                self.assertFalse(self.m.entries[d.port].error)
                self.assertEqual(len(self.m.budgets[d.port]), 1)
                self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)
                self.assertFalse(any(op in ('end', 'restore', 'resume', 'publish-input') for op, _ in self.h.calls))
                self.assertFalse(any(args[0] == 'ready' for args, _ in self.h.logs))

    def test_ready_without_pad_still_uses_normal_publication_gate(self):
        d = self.boot()
        self.h.readiness_enabled = True
        self.h.attest[d.port] = (0, fixture.proof(d).replace('pad=1', 'pad=0'))
        self.poll()
        self.assertEqual(self.m.entries[d.port].phase, 'input_check')
        self.assertEqual(self.m.entries[d.port].operation, 'input-info')
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)

    def test_restart_reattests_wait_and_never_replays_setup(self):
        d = self.boot()
        self.m = s.Manager(self.h, lambda: self.h.now)
        self.tick(2)
        self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
        self.h.attest[d.port] = (0, fixture.proof(d))
        self.poll()
        self.assertEqual(self.m.entries[d.port].phase, 'active')
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)

    def test_explicit_resume_keeps_healthy_wait(self):
        d = self.boot()
        self.m.command('resume')
        self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
        self.poll()
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)

    def test_release_can_end_wait_once_even_if_start_budget_exhausted(self):
        d = self.boot()
        self.m.budgets[d.port] = s.deque([0, 0, 0])
        self.m.command('release')
        self.tick()
        self.assertTrue(self.h.saved['paused'])
        self.assertEqual(self.m.entries[d.port].operation, 'end')
        self.h.complete('end')
        self.tick()
        self.h.now += 100
        self.tick(4)
        self.assertEqual(sum(op == 'end' for op, _ in self.h.calls), 1)
        self.assertFalse(self.m.returned())  # Still 109c is not xpad/100a return.

    def test_fault_is_retained_and_never_converted_back_to_wait(self):
        d = self.boot()
        bad = fixture.proof(d, failed=True, stage=9).replace('error=-110', 'error=-32')
        self.h.attest[d.port] = (1, bad)
        self.poll()
        e = self.m.entries[d.port]
        self.assertEqual(e.phase, 'failed')
        self.assertEqual(e.bootstrap_diagnostic['reported_kernel_status']['error'], -32)
        self.h.attest[d.port] = (0, waiting(d))
        self.tick()
        self.assertEqual(e.operation, 'end')
        self.h.complete('end')
        self.tick()
        self.assertEqual(e.bootstrap_diagnostic['reported_kernel_status']['error'], -32)
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)

    def test_foreign_kernel_tokens_block_instead_of_adopting(self):
        d = self.boot()
        self.h.attest[d.port] = (0, waiting(d).replace(f'instance_token={d.address}', 'instance_token=99'))
        self.poll()
        self.assertEqual(self.m.entries[d.port].phase, 'blocked')
        self.assertFalse(any(op == 'end' for op, _ in self.h.calls))

    def test_unknown_metadata_keeps_wait_and_original_ownership(self):
        d = self.boot()
        tokens = self.m.entries[d.port].kernel_tokens[:]
        self.h.scan_failure = True
        self.h.now += 86400
        self.tick(5)
        self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
        self.assertEqual(self.m.entries[d.port].kernel_tokens, tokens)
        self.assertFalse(self.m.returned())

    def test_control_busy_defers_read_only_without_retrying_setup(self):
        d = self.boot()
        self.h.control_busy.add(d.port)
        for _ in range(10):
            self.poll()
        self.assertEqual(self.m.entries[d.port].phase, 'receiver_wait')
        self.assertFalse(self.m.entries[d.port].error)
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 1)

    def test_old_pending_status_and_new_lifetime_require_fresh_discovery(self):
        for old_error in (0, -19, -5):
            with self.subTest(old_error=old_error):
                d = self.boot()
                if old_error:
                    self.h.attest[d.port] = (1, fixture.proof(d, failed=True, stage=9).replace('error=-110', f'error={old_error}'))
                self.h.now += 3
                self.tick()  # Getter pinned to old receiver.
                fresh = device(generation=3, driver=None)
                self.h.devices[d.port] = fresh
                self.tick()
                if old_error == -5:
                    self.assertEqual(self.m.entries[d.port].phase, 'blocked')
                    self.assertEqual(self.m.entries[d.port].bootstrap_diagnostic['reported_kernel_status']['error'], -5)
                else:
                    self.assertNotIn(d.port, self.m.entries)
                    self.tick(3)
                    self.assertEqual(self.m.entries[d.port].device.token, fresh.token)
                    self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 2)
                self.assertFalse(any(op in ('end', 'restore') for op, _ in self.h.calls))

    def test_wait_proof_cannot_impersonate_terminal_failure_or_ready(self):
        d = device(pid='109c')
        proof = s.boot_proof(waiting(d))
        self.assertTrue(proof['waiting'])
        self.assertFalse(proof['ready'])
        self.assertIsNone(s.boot_proof(waiting(d).replace('failed_stage=0', 'failed_stage=5')))
        self.assertIsNone(s.boot_proof(waiting(d).replace('error=0', 'error=-5')))

    def test_busy_old_getter_cannot_authorize_replacement_or_block_fresh_discovery(self):
        d = self.boot()
        self.h.attest[d.port] = (s.STATUS_BUSY_EXIT, '')
        self.h.now += 3
        self.tick()
        fresh = device(generation=3, driver=None)
        self.h.devices[d.port] = fresh
        self.tick()
        self.assertNotIn(d.port, self.m.entries)
        self.assertFalse(any(op in ('end', 'restore') for op, _ in self.h.calls))
        self.tick(3)
        self.assertEqual(self.m.entries[d.port].device.token, fresh.token)
        self.assertEqual(sum(op == 'bootstrap' for op, _ in self.h.calls), 2)


if __name__ == '__main__':
    unittest.main()
