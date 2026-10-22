#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Independent startup policy and real host adapter against synthetic sysfs only."""
import copy
from dataclasses import replace
import unittest
from unittest.mock import patch

import test_service_manager as fixture

service, device, proof = fixture.service, fixture.device, fixture.proof


class Standalone(unittest.TestCase):
    def setup(self, pid='100a', owner=None):
        self.host = fixture.Fake([device(pid=pid, driver=owner)])
        self.manager = service.Manager(self.host, lambda: self.host.now)
        return next(iter(self.host.devices.values()))

    def tick(self, count=1):
        for _ in range(count):
            self.manager.tick()

    def boot(self, pid='100a'):
        old = self.setup(pid)
        self.tick(2 if pid == '100a' else 1)
        native = (device(pid='109c', generation=2, driver='gs_native') if pid == '100a'
                  else self.host.devices[old.port])
        self.host.devices[old.port] = native
        self.host.complete('bootstrap', output=proof(native).replace('handover=1', 'handover=0'))
        self.tick(2)
        self.assertEqual(self.manager.entries[old.port].phase, 'active')
        return native

    def test_free_standard_and_direct_models_boot_without_xpad(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                native = self.boot(pid)
                self.assertEqual(self.host.devices[native.port].driver, 'gs_native')
                self.assertEqual([op for op, _ in self.host.calls],
                                 ['claim', *(['info'] if pid == '100a' else []), 'bootstrap', 'boot-info'])
                self.assertTrue(self.manager.entries[native.port].kernel_tokens)

    def test_standard_bootstrap_needs_no_button_report_evdev_consumer_or_xpad(self):
        d = self.setup()
        self.host.pad = 0
        self.tick(2)
        entry = self.manager.entries[d.port]
        self.assertEqual(entry.phase, 'bootstrapping')
        self.assertEqual(entry.device.driver, 'gs_native')
        self.assertEqual(len(self.manager.budgets[d.port]), 1)
        self.assertEqual([op for op, _ in self.host.calls], ['claim', 'info', 'bootstrap'])
        for second in range(20):
            self.host.now = second
            self.tick()
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 1)

    def test_pause_budget_and_monitor_failure_each_prevent_any_free_claim(self):
        for guard in ('pause', 'budget', 'monitor'):
            with self.subTest(guard=guard):
                d = self.setup()
                if guard == 'pause': self.manager.command('release')
                if guard == 'monitor': self.host.input_error = 'monitor failed'
                if guard == 'budget':
                    self.manager.budgets[d.port] = service.deque([0, 0, 0])
                    self.manager.budget_boot = self.host.boot_id
                self.tick(3)
                self.assertEqual(self.host.calls, [])
                self.assertIsNone(self.host.devices[d.port].driver)

    def test_free_reconnect_after_pending_getter_requires_new_budgeted_claim(self):
        native = self.boot()
        self.tick()  # Running healthy getter for the OLD instance.
        fresh = device(generation=3, driver=None)
        self.host.devices[native.port] = fresh
        self.host.complete('info', output='pid=109c state=1 error=0 OUT=1 session=1 pad=0 imu=99')
        self.tick(4)
        self.assertEqual(self.manager.entries[native.port].device.token, fresh.token)
        self.assertEqual(self.manager.entries[native.port].phase, 'bootstrapping')
        self.assertEqual([op for op, _ in self.host.calls].count('claim'), 2)
        self.assertFalse(any(op in ('end', 'restore') for op, _ in self.host.calls))

    def test_real_old_fault_is_not_erased_by_a_free_replacement(self):
        native = self.boot()
        self.tick()
        self.host.devices[native.port] = device(generation=3, driver=None)
        self.host.complete('info', rc=1, output='pid=109c state=2 error=-5 OUT=1 session=0 pad=0 imu=99')
        self.tick(5)
        self.assertEqual([op for op, _ in self.host.calls].count('claim'), 1)
        self.assertTrue(self.manager.entries[native.port].error)
        self.assertIsNone(self.host.devices[native.port].driver)

    def test_free_multiport_discovery_does_not_touch_foreign_or_unowned_native(self):
        self.setup()
        devices = [device('1-2', driver=None), device('5-3.2', pid='105e', driver=None),
                   device('6-4', driver='usbfs'), device('7-1', driver='gs_native'),
                   device('9-2', pid='109c', driver=None)]
        self.host.devices = {d.port: d for d in devices}
        self.tick(2)
        self.assertEqual({port for op, port in self.host.calls if op == 'claim'}, {'1-2', '5-3.2', '9-2'})
        self.assertTrue(all(port in ('1-2', '5-3.2', '9-2') for _, port in self.host.calls))

    def test_verified_free_start_restores_active_lease_after_manager_restart(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                native = self.boot(pid)
                before = list(self.host.calls)
                self.manager = service.Manager(self.host, lambda: self.host.now)
                self.tick(2)
                self.assertEqual(self.manager.entries[native.port].phase, 'active')
                self.assertTrue(all(op == 'boot-info' for op, _ in self.host.calls[len(before):]))

    def test_failed_free_claim_cleanup_attempt_is_bounded_and_original_error_survives(self):
        d = self.setup()
        def failed_status(*args, **kwargs):
            raise service.Unsafe('first acquisition failure')
        self.host.start = failed_status  # Claim succeeded/was verified, status launch failed.
        with patch.object(self.host, 'restore', side_effect=service.Unsafe('xpad not available')) as restore:
            self.tick(4)
            saved = copy.deepcopy(self.host.saved)
            self.manager = service.Manager(self.host, lambda: self.host.now)
            self.tick(3)
            self.assertEqual(restore.call_count, 1)
            self.assertEqual(self.manager.entries[d.port].acquisition_failure, 'first acquisition failure')
            self.assertEqual(self.manager.status()['devices'][d.port]['acquisition_failure'], 'first acquisition failure')
            self.assertEqual(self.host.saved['recent_failures'][-1]['message'], 'first acquisition failure')
            self.assertFalse(self.manager.returned())
            self.assertTrue(saved['leases'][d.port]['cleanup_attempted'])

    def test_unconfirmed_native_binding_after_write_failure_is_never_unbound(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                d = self.setup(pid)
                def failed_claim(old):
                    self.host.devices[old.port] = replace(old, driver='gs_native')
                    raise service.Unsafe('write did not confirm acquisition')
                self.host.claim = failed_claim
                self.tick(4)
                self.assertEqual(self.host.calls, [])
                self.assertIn('unconfirmed', self.manager.entries[d.port].error)
                self.assertFalse(self.manager.returned())

    def test_prewrite_refusal_grants_no_cleanup_and_survives_restart_without_retry(self):
        d = self.setup()
        with patch.object(self.host, 'claim', side_effect=service.AcquisitionUnchanged('old kernel')) as claim:
            self.tick(4)
            self.assertEqual(self.host.calls, [])
            self.assertFalse(self.manager.leases)
            self.assertIn(d.token, self.manager.attempted)
            self.manager = service.Manager(self.host, lambda: self.host.now)
            self.tick(4)
            claim.assert_called_once()

    def test_crash_between_intent_and_confirmation_grants_no_native_cleanup(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                d = self.setup(pid)
                self.manager.remember(service.Entry(d, 'waiting_input', origin_pid=pid))
                self.host.devices[d.port] = replace(d, driver='gs_native')
                self.manager = service.Manager(self.host, lambda: self.host.now)
                self.tick(4)
                self.assertEqual(self.host.calls, [])
                self.assertEqual(self.manager.entries[d.port].phase, 'blocked')
                self.assertIn('unconfirmed', self.manager.entries[d.port].error)
                self.assertFalse(self.manager.returned())


class ColdNative(unittest.TestCase):
    """Native-mode-at-boot is a new claim, never inherited bootstrap proof."""
    def setup(self, owner='xpad'):
        self.host = fixture.Fake([device(pid='109c', driver=owner)])
        self.host.pad = 0
        self.manager = service.Manager(self.host, lambda: self.host.now)

    def tick(self, count=1):
        for _ in range(count):
            self.manager.tick()

    def begin(self):
        self.setup()
        self.tick()
        return self.host.devices['2-3.4']

    def finish(self, d, failed=False):
        payload = proof(d, failed=failed).replace('pad=1', 'pad=0').replace('handover=1', 'handover=0')
        self.host.attest[d.port] = (int(failed), payload)
        self.host.complete('bootstrap', rc=int(failed), output=payload)
        self.tick(2)
        return self.manager.entries[d.port]

    def test_cold_boot_requires_no_resume_or_button_and_keeps_same_instance(self):
        for owner in (None, 'xpad'):
            with self.subTest(owner=owner):
                self.setup(owner)
                original = next(iter(self.host.devices.values()))
                self.tick()
                d = self.host.devices[original.port]
                self.assertEqual(d.token, original.token)
                self.assertEqual(self.host.calls, [('claim', d.port), ('bootstrap', d.port)])
                entry = self.finish(d)
                self.assertEqual(entry.phase, 'active')
                self.assertEqual(entry.origin_pid, '109c')
                self.assertEqual(len(self.manager.budgets[d.port]), 1)
                self.assertTrue(entry.kernel_tokens)

    def test_direct_start_preserves_sensor_readiness_before_publication(self):
        from test_input_publication import FeatureHost
        self.host = FeatureHost()
        self.host.devices = {'2-3.4': device(pid='109c', driver=None)}
        self.host.pad = 0
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick()
        entry = self.finish(self.host.devices['2-3.4'])
        self.tick()
        self.assertEqual(entry.phase, 'awaiting_sensor')
        self.assertFalse(self.host.published)
        self.host.processed = True
        self.tick()
        self.assertFalse(self.host.published)
        self.host.readable = True
        self.tick(2)
        self.assertEqual(entry.phase, 'active')
        self.assertTrue(self.host.published)

    def test_pause_budget_monitor_and_foreign_access_block_before_acquisition(self):
        for guard in ('pause', 'budget', 'monitor', 'foreign-access'):
            with self.subTest(guard=guard):
                self.setup()
                if guard == 'pause': self.manager.command('release')
                if guard == 'budget':
                    self.manager.budget_boot = self.host.boot_id
                    self.manager.budgets['2-3.4'] = service.deque([0, 0, 0])
                if guard == 'monitor': self.host.input_error = 'observation lost'
                if guard == 'foreign-access': self.host.block.add('2-3.4')
                self.tick(4)
                self.assertEqual(self.host.calls, [])
                self.assertEqual(self.host.devices['2-3.4'].driver, 'xpad')

    def test_successful_lease_restart_only_attests_and_never_reinitializes(self):
        d = self.begin()
        self.finish(d)
        before = len(self.host.calls)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(2)
        self.assertEqual(self.manager.entries[d.port].phase, 'active')
        self.assertEqual(self.host.calls[before:], [('boot-info', d.port)])

    def test_missing_child_result_recovers_only_terminal_proof_then_stops(self):
        d = self.begin()
        self.host.attest[d.port] = (1, proof(d, failed=True))
        self.host.complete('bootstrap', rc=1, output='lost child output')
        self.tick(3)
        self.assertEqual([op for op, _ in self.host.calls], ['claim', 'bootstrap', 'boot-info', 'end'])
        self.assertTrue(self.manager.entries[d.port].error)
        self.assertEqual(self.host.devices[d.port], d)

    def test_daemon_loss_during_start_recovers_proof_without_second_bootstrap(self):
        d = self.begin()
        self.host.attest[d.port] = (1, proof(d, failed=True))
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(3)
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 1)
        self.assertEqual(self.host.calls[-1][0], 'end')

    def test_failed_start_preserves_original_error_and_manual_109c_recovery(self):
        d = self.begin()
        entry = self.finish(d, failed=True)
        primary = copy.deepcopy(entry.bootstrap_diagnostic)
        self.tick()
        self.host.complete('end')
        self.tick()
        self.host.now = entry.deadline + 1
        self.tick(10)
        self.assertEqual(entry.phase, 'blocked')
        self.assertEqual(entry.bootstrap_diagnostic, primary)
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 1)
        self.assertEqual([op for op, _ in self.host.calls].count('end'), 1)
        self.assertNotIn('restore', [op for op, _ in self.host.calls])
        self.manager.command('release')
        self.host.devices[d.port] = replace(d, driver='xpad')
        self.tick()
        self.assertFalse(self.manager.returned())  # xpad/109c != usable 100a fallback.
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(5)
        self.assertEqual([op for op, _ in self.host.calls].count('end'), 1)
        self.assertEqual(self.manager.entries[d.port].bootstrap_diagnostic, primary)

    def test_end_failure_never_rebinds_or_retries(self):
        d = self.begin()
        entry = self.finish(d)
        self.manager.command('release')
        self.tick()
        self.host.complete('end', rc=1, output='stop failed')
        self.tick()
        self.host.now = entry.deadline + 1
        self.tick(10)
        self.assertFalse(self.manager.returned())
        self.assertNotIn('restore', [op for op, _ in self.host.calls])
        self.assertEqual([op for op, _ in self.host.calls].count('end'), 1)

    def test_exhausted_budget_still_allows_one_proven_end(self):
        d = self.begin()
        self.finish(d)
        self.manager.budgets[d.port].extend([0, 0, 0])
        self.manager.command('release')
        self.tick()
        self.assertEqual(self.host.calls[-1][0], 'end')

    def test_mismatched_handoff_proof_or_replacement_never_gets_end(self):
        for change in ('token', 'instance', 'parent', 'owner'):
            with self.subTest(change=change):
                d = self.begin()
                payload = proof(d)
                if change == 'token':
                    self.host.attest[d.port] = (0, payload.replace('instance_token=1', 'instance_token=99'))
                else:
                    fields = {'instance': {'token': 'replacement'},
                              'parent': {'parent': 'replacement-hub'},
                              'owner': {'driver': 'usbfs'}}[change]
                    self.host.devices[d.port] = replace(d, **fields)
                self.host.complete('bootstrap', output=payload)
                self.tick(2)
                self.host.now = 100
                self.tick(4)
                self.assertNotEqual(self.manager.entries[d.port].phase, 'active')
                self.assertFalse(any(op in ('end', 'restore') for op, _ in self.host.calls))

    def test_replacement_during_claim_grants_no_native_ownership(self):
        self.setup()
        self.host.race = lambda d: self.host.devices.update({d.port: replace(d, token='replacement', driver='gs_native')})
        self.tick(4)
        self.assertEqual([op for op, _ in self.host.calls], ['claim'])
        self.assertEqual(self.manager.entries['2-3.4'].phase, 'blocked')

    def test_missing_proof_after_restart_needs_manual_recovery(self):
        d = self.begin()
        self.host.attest[d.port] = (1, 'no terminal proof')
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(4)
        self.assertEqual(self.manager.entries[d.port].phase, 'blocked')
        self.assertFalse(any(op in ('end', 'restore') for op, _ in self.host.calls))

    def test_absence_clears_recovery_only_after_release_and_observation(self):
        d = self.begin()
        self.finish(d, failed=True)
        self.manager.command('release')
        self.host.devices.clear()
        self.tick()
        self.host.now = 11
        self.tick(2)
        self.host.now = 13
        self.tick()
        self.assertTrue(self.manager.returned())
        self.assertFalse(self.host.saved['leases'])
        self.assertEqual(self.host.saved['recent_failures'][-1]['resolution'], 'physically_absent')

    def test_pending_healthy_status_reconnect_requires_fresh_claim_and_budget(self):
        for pid in ('100a', '109c'):
            with self.subTest(pid=pid):
                d = self.begin()
                self.finish(d)
                self.tick()  # Getter pins the OLD native session.
                fresh = device(pid=pid, generation=2, driver=None)
                self.host.devices[d.port] = fresh
                self.host.complete('info', output='pid=109c state=1 error=0 OUT=1 session=1 pad=0 imu=22')
                self.tick(4)
                self.assertEqual(self.manager.entries[d.port].device.token, fresh.token)
                self.assertEqual([op for op, _ in self.host.calls].count('claim'), 2)
                self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 2)
                self.assertEqual(len(self.manager.budgets[d.port]), 2)
                self.assertFalse(any(op in ('end', 'restore') for op, _ in self.host.calls))


class HostAdapter(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.Adapter()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.host = self.fixture.host
        self.sysfs = self.fixture.sysfs

    def free_device(self, pid='100a'):
        path = self.fixture.fixture(pid=pid)
        link = path / f'{path.name}:1.0/driver'
        link.unlink()
        return self.host.scan()[path.name], link

    def test_xpad_autoprobe_during_acquisition_rechecks_before_one_write(self):
        original, link = self.free_device()
        scan = self.host.scan
        reads = []

        def autoprobe():
            # xpad finishes probing while the foreign-FD scan is running.
            if len(reads) == 1:
                link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
            current = scan()
            reads.append(current[original.port].driver)
            return current

        with patch.object(self.host, 'scan', side_effect=autoprobe), \
                patch.object(self.host, 'write_binding') as bind:
            self.host.claim(original)
        bind.assert_not_called()
        self.assertEqual(reads, [None, 'xpad', 'xpad', 'xpad'])
        attr = self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a'
        self.assertEqual(attr.read_text(), self.host.claim_request(original))

    def test_xpad_autoprobe_before_first_check_is_valid_for_every_start_pid(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                # Each iteration uses a fresh synthetic host, never real sysfs.
                self.setUp()
                original, link = self.free_device(pid)
                link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
                self.host.claim(original)
                attr = self.sysfs / f'bus/usb/drivers/gs_native/acquire_{pid}'
                self.assertEqual(attr.read_text(), self.host.claim_request(original))

    def test_autoprobe_cannot_hide_any_other_identity_change(self):
        original, _ = self.free_device()
        changes = dict(port='6-8', token='replacement', parent='other-parent',
                       pid='109c', bus=7, address=10, sysfs_inode=1, parent_inode=1)
        for field, value in changes.items():
            with self.subTest(field=field):
                actual = replace(original, driver='xpad', **{field: value})
                with patch.object(self.host, 'scan', return_value={original.port: actual}), \
                        self.assertRaisesRegex(service.AcquisitionUnchanged, field):
                    self.host.claim(original)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_foreign_native_and_reverse_owner_changes_are_not_retried(self):
        original, _ = self.free_device()
        for before, after in ((None, 'usbfs'), (None, 'gs_native'), ('xpad', None),
                              ('xpad', 'foreign'), ('xpad', 'gs_native')):
            with self.subTest(before=before, after=after):
                with patch.object(self.host, 'scan', return_value={
                        original.port: replace(original, driver=after)}) as scan, \
                        self.assertRaises(service.AcquisitionUnchanged):
                    self.host.claim(replace(original, driver=before))
                self.assertEqual(scan.call_count, 1)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_second_check_is_strict_and_never_loops(self):
        original, _ = self.free_device()
        xpad = replace(original, driver='xpad')
        for second in (original, replace(xpad, driver='gs_native'),
                       replace(xpad, address=10), None):
            with self.subTest(second=second):
                with patch.object(self.host, 'scan', side_effect=[
                        {original.port: xpad}, {original.port: second}]) as scan, \
                        self.assertRaises(service.AcquisitionUnchanged):
                    self.host.claim(original)
                self.assertEqual(scan.call_count, 2)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_post_recheck_change_still_refuses_the_write(self):
        original, _ = self.free_device()
        xpad = replace(original, driver='xpad')
        with patch.object(self.host, 'scan', side_effect=[{original.port: xpad},
                {original.port: xpad}, {original.port: original}]) as scan, \
                self.assertRaisesRegex(service.AcquisitionUnchanged, 'during ownership check: driver'):
            self.host.claim(original)
        self.assertEqual(scan.call_count, 3)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_new_foreign_usb_handle_is_checked_again_after_autoprobe(self):
        original, link = self.free_device()
        scan = self.host.scan
        count = 0

        def race():
            nonlocal count
            count += 1
            if count == 2:
                link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
                fd = self.fixture.proc / '999999/fd'
                fd.mkdir(parents=True)
                (fd / '5').symlink_to(f'/dev/bus/usb/{original.bus:03d}/{original.address:03d}')
            return scan()

        with patch.object(self.host, 'scan', side_effect=race), \
                self.assertRaisesRegex(service.AcquisitionUnchanged, 'Foreign device handle'):
            self.host.claim(original)
        self.assertEqual(count, 3)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_incomplete_scan_after_autoprobe_is_not_absence_or_permission(self):
        original, _ = self.free_device()
        incomplete = service.Scan()
        incomplete.errors[original.port] = 'Empty USB metadata'
        with patch.object(self.host, 'scan', side_effect=[
                {original.port: replace(original, driver='xpad')}, incomplete]), \
                self.assertRaisesRegex(service.AcquisitionUnchanged, 'Empty USB metadata'):
            self.host.claim(original)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_permission_failure_during_recheck_is_not_retried(self):
        original, link = self.free_device()
        link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
        # sysfs enumeration uses glob; iterdir is the independent process scan.
        with patch.object(service.Path, 'iterdir', side_effect=PermissionError('process scan denied')), \
                self.assertRaisesRegex(service.AcquisitionUnchanged, 'process scan denied'):
            self.host.claim(original)
        self.assertEqual((self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a').read_text(), '')

    def test_ordinary_guards_remain_strict_for_same_instance_autoprobe(self):
        original, link = self.free_device()
        link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
        for operation in (self.host.guard, self.host.observe_guard, self.host.write_claim):
            with self.subTest(operation=operation.__name__), self.assertRaises(service.Unsafe):
                operation(original)

    def test_manager_reaches_bootstrap_once_after_real_adapter_autoprobe(self):
        original, link = self.free_device()
        fake = fixture.Fake([original])
        fake.pad = 0

        def acquire(d):
            link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
            self.host.claim(d)
            fake.calls.append(('claim', d.port))
            fake.devices[d.port] = replace(d, driver='gs_native')

        fake.claim = acquire
        manager = service.Manager(fake, lambda: fake.now)
        for _ in range(10):
            manager.tick()
        self.assertEqual(manager.entries[original.port].phase, 'bootstrapping')
        self.assertEqual([op for op, _ in fake.calls], ['claim', 'info', 'bootstrap'])
        self.assertFalse(manager.entries[original.port].acquisition_failure)
        self.assertEqual(len(manager.budgets[original.port]), 1)

    def test_actual_write_error_is_never_reclassified_or_repeated(self):
        original, link = self.free_device()
        link.symlink_to(self.sysfs / 'bus/usb/drivers/xpad')
        fake = fixture.Fake([original])
        fake.claim = self.host.claim
        opened = []
        real_open = service.Path.open

        class PartialWrite:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def write(self, request):
                fake.devices[original.port] = replace(original, driver='gs_native')
                raise OSError('scoped write failed; outcome unknown')

        def fail_write(path, *args, **kwargs):
            if path.name == 'acquire_100a':
                opened.append(path)
                return PartialWrite()
            return real_open(path, *args, **kwargs)

        manager = service.Manager(fake, lambda: fake.now)
        with patch.object(service.Path, 'open', fail_write):
            for _ in range(10):
                manager.tick()
            restarted = service.Manager(fake, lambda: fake.now)
            for _ in range(10):
                restarted.tick()
        self.assertEqual(len(opened), 1)
        entry = manager.entries[original.port]
        self.assertIn('outcome unknown', entry.acquisition_failure)
        # Uncertain write retains intent for recovery, unlike a pre-write refusal.
        self.assertIn(original.port, manager.leases)
        self.assertEqual(fake.calls, [])

    def test_unbound_start_has_no_xpad_directory_or_userspace_unbind(self):
        for pid in ('100a', '105e', '109c'):
            with self.subTest(pid=pid):
                port = {'100a': '6-2.3', '105e': '6-4', '109c': '6-5'}[pid]
                path = self.fixture.fixture(port=port, pid=pid)
                (path / f'{port}:1.0/driver').unlink()
                fallback = self.sysfs / 'bus/usb/drivers/xpad'
                if fallback.exists():
                    (fallback / 'bind').unlink()
                    fallback.rmdir()
                d = self.host.scan()[port]
                with patch.object(self.host, 'write_binding') as bind, \
                        patch.object(service.subprocess, 'Popen') as process:
                    self.host.claim(d)
                    bind.assert_not_called()
                    process.assert_not_called()
                attr = self.sysfs / 'bus/usb/drivers/gs_native'
                self.assertEqual((attr / f'acquire_{pid}').read_text(), self.host.claim_request(d))
                self.assertEqual((attr / f'claim_{pid}').read_text() if pid != '109c' else '', '')
                self.assertFalse(fallback.exists())

    def test_missing_acquire_contract_preserves_both_initial_owner_states(self):
        path = self.fixture.fixture()
        attr = self.sysfs / 'bus/usb/drivers/gs_native/acquire_100a'
        attr.unlink()
        for owner in ('xpad', None):
            with self.subTest(owner=owner):
                if owner is None: (path / '6-2.3:1.0/driver').unlink()
                d = self.host.scan()[path.name]
                with patch.object(self.host, 'write_binding') as bind, self.assertRaises(service.Unsafe):
                    self.host.claim(d)
                bind.assert_not_called()
                self.assertEqual(self.host.scan()[path.name], d)

    def test_missing_fallback_never_unbinds_owned_native_instance(self):
        path = self.fixture.fixture()
        link = path / '6-2.3:1.0/driver'
        link.unlink(); link.symlink_to(self.sysfs / 'bus/usb/drivers/gs_native')
        (self.sysfs / 'bus/usb/drivers/xpad/bind').unlink()
        d = self.host.scan()[path.name]
        with patch.object(self.host, 'write_binding') as bind, \
                self.assertRaisesRegex(service.Unsafe, 'fallback unavailable'):
            self.host.restore(d)
        bind.assert_not_called()
        self.assertEqual(self.host.scan()[path.name], d)


class ReturnedNativeTimeout(unittest.TestCase):
    """Late controller return is a new discovery, not an old boot retry."""
    def setUp(self):
        self.host = fixture.Fake([device(pid='109c')])
        self.host.pad = 0
        self.manager = service.Manager(self.host, lambda: self.host.now)

    def tick(self, count=1):
        for _ in range(count):
            self.manager.tick()

    def failed_and_ended(self):
        self.tick()
        old = self.host.devices['2-3.4']
        output = proof(old, failed=True).replace('pad=1', 'pad=0').replace('handover=1', 'handover=0')
        self.host.attest[old.port] = (1, output)
        self.host.complete('bootstrap', rc=1, output=output)
        self.tick(3)
        self.host.complete('end')
        self.tick()
        entry = self.manager.entries[old.port]
        self.assertTrue(entry.end_succeeded)
        self.assertEqual(entry.phase, 'returning')
        self.failure = copy.deepcopy(entry.bootstrap_diagnostic)
        return entry

    def replacement(self, **changes):
        fresh = device(generation=2, **changes)
        self.host.devices[fresh.port] = fresh
        return fresh

    def test_recorded_first_100a_is_fresh_discovery_after_a_separate_scan(self):
        entry = self.failed_and_ended()
        fresh = self.replacement()
        before = list(self.host.calls)
        self.tick()
        self.assertEqual(self.host.calls, before)  # No mutation using return snapshot.
        self.assertNotIn(fresh.port, self.manager.entries)
        self.assertNotIn(fresh.port, self.host.saved['leases'])
        self.assertNotIn(fresh.token, self.manager.attempted)
        self.assertIn(entry.device.token, self.manager.attempted)
        self.assertEqual(self.manager.recent_failures[-1]['bootstrap_diagnostic'], self.failure)
        self.assertEqual(self.manager.recent_failures[-1]['resolution'], 'observed_100a_xpad')
        self.tick(2)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 2)
        self.assertEqual([op for op, _ in self.host.calls].count('end'), 1)
        self.assertNotIn('restore', [op for op, _ in self.host.calls])
        native = device(pid='109c', generation=3, driver='gs_native')
        self.host.devices[native.port] = native
        self.host.attest[native.port] = (0, proof(native))
        self.host.complete('bootstrap', output=proof(native))
        self.tick(2)
        self.assertEqual(self.manager.entries[native.port].phase, 'active')

    def test_restart_between_return_and_discovery_preserves_first_failure_and_budget(self):
        entry = self.failed_and_ended()
        fresh = self.replacement()
        self.tick()
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(2)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')
        self.assertEqual(len(self.manager.budgets[fresh.port]), 2)
        self.assertIn(entry.device.token, self.manager.attempted)
        self.assertEqual(self.manager.recent_failures[-1]['bootstrap_diagnostic'], self.failure)

    def test_cleanup_timeout_does_not_suppress_a_later_verified_new_100a(self):
        entry = self.failed_and_ended()
        self.host.now = entry.deadline + 1
        self.tick()
        self.assertEqual(entry.phase, 'blocked')
        fresh = self.replacement()
        self.tick(3)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')
        self.assertEqual(self.manager.recent_failures[-1]['bootstrap_diagnostic'], self.failure)

    def test_restart_after_end_only_attests_old_proof_then_allows_new_discovery(self):
        self.failed_and_ended()
        before = list(self.host.calls)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.tick(2)
        self.assertEqual(self.host.calls[len(before):], [('boot-info', '2-3.4')])
        self.replacement()
        self.tick(3)
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 2)
        self.assertEqual([op for op, _ in self.host.calls].count('end'), 1)

    def test_foreign_owner_on_next_scan_cannot_inherit_the_return_snapshot(self):
        self.failed_and_ended()
        fresh = self.replacement()
        self.tick()
        self.host.devices[fresh.port] = replace(fresh, driver='usbfs')
        before = list(self.host.calls)
        self.tick(5)
        self.assertEqual(self.host.calls, before)
        self.assertNotIn(fresh.port, self.manager.leases)

    def test_global_scan_failure_before_discovery_blocks_acquisition(self):
        self.failed_and_ended()
        fresh = self.replacement()
        self.tick()
        self.host.scan_failure = True
        before = list(self.host.calls)
        self.tick(5)
        self.assertEqual(self.host.calls, before)
        self.host.scan_failure = False
        self.tick(2)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')

    def test_second_failed_boot_is_not_an_automatic_repeat_on_returned_100a(self):
        self.failed_and_ended()
        fresh = self.replacement()
        self.tick(3)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')
        native = device(pid='109c', generation=3, driver='gs_native')
        self.host.devices[native.port] = native
        failed = proof(native, failed=True).replace('pad=1', 'pad=0')
        self.host.attest[native.port] = (1, failed)
        self.host.complete('bootstrap', rc=1, output=failed)
        self.tick(3)
        self.host.complete('end')
        self.tick()
        returned = device(generation=4)
        self.host.devices[returned.port] = returned
        before = list(self.host.calls)
        self.tick(30)
        self.assertEqual(self.host.calls, before)
        self.assertEqual(self.manager.entries[returned.port].phase, 'released')
        self.assertEqual([op for op, _ in self.host.calls].count('bootstrap'), 2)
        self.assertEqual(len(self.manager.budgets[returned.port]), 2)

    def test_pause_and_shutdown_keep_fallback_without_new_claim(self):
        for stopping in (False, True):
            with self.subTest(stopping=stopping):
                self.setUp()
                self.failed_and_ended()
                if stopping:
                    self.manager.stopping = True
                else:
                    self.manager.command('release')
                fresh = self.replacement()
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)
                self.assertEqual(self.manager.entries[fresh.port].phase, 'released')
                self.assertEqual(self.host.devices[fresh.port].driver, 'xpad')

    def test_exhausted_budget_allows_cleanup_but_defers_new_acquisition(self):
        entry = self.failed_and_ended()
        self.manager.budgets[entry.device.port] = service.deque([0, 0, 0])
        fresh = self.replacement()
        before = list(self.host.calls)
        self.tick(5)
        self.assertEqual(self.host.calls, before)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'cooldown')
        self.assertGreater(self.manager.status()['devices'][fresh.port]['start_retry_in'], 0)
        self.assertNotIn(fresh.port, self.manager.leases)

    def test_old_or_already_attempted_instance_is_never_retried(self):
        entry = self.failed_and_ended()
        before = list(self.host.calls)
        self.tick(10)
        self.assertEqual(self.host.calls, before)
        fresh = self.replacement()
        self.manager.attempted.add(fresh.token)
        self.tick(5)
        self.assertEqual(self.host.calls, before)

    def test_no_automatic_migration_of_revision13_suppressed_tokens(self):
        entry = self.failed_and_ended()
        fresh = self.replacement()
        # Model the already consumed old policy, not a new cleanup decision.
        self.host.saved['leases'] = {}
        self.host.saved['attempted'].append(fresh.token)
        self.manager = service.Manager(self.host, lambda: self.host.now)
        before = list(self.host.calls)
        self.tick(5)
        self.assertEqual(self.host.calls, before)
        self.assertIn(entry.device.token, self.manager.attempted)

    def test_missing_proof_or_unverified_end_never_grants_a_new_start(self):
        for field, value in (('end_succeeded', False), ('end_attempted', False),
                             ('kernel_tokens', []), ('bootstrap_started', False),
                             ('origin_pid', '100a'), ('bootstrap_diagnostic', {})):
            with self.subTest(field=field):
                self.setUp()
                entry = self.failed_and_ended()
                setattr(entry, field, value)
                self.replacement()
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)

    def test_only_attested_direct_no_data_verify_timeout_is_eligible(self):
        for field, value in (('state', 7), ('error', -5), ('failed_stage', 4),
                             ('pad', 1), ('imu', 1), ('handover', 1),
                             ('port_token', 999), ('instance_token', 999)):
            with self.subTest(field=field):
                self.setUp()
                entry = self.failed_and_ended()
                entry.bootstrap_diagnostic['reported_kernel_status'][field] = value
                self.replacement()
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)

    def test_uncertain_child_or_different_source_is_not_a_readiness_timeout(self):
        for field, value in (('timed_out', True), ('returncode', 0), ('source_instance', 'other')):
            with self.subTest(field=field):
                self.setUp()
                entry = self.failed_and_ended()
                entry.bootstrap_diagnostic[field] = value
                self.replacement()
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)

    def test_foreign_owner_or_hub_change_is_never_a_verified_return(self):
        for changes in ({'driver': None}, {'driver': 'usbfs'}, {'driver': 'gs_native'},
                        {'parent': 'replacement-hub'}, {'pid': '105e'}):
            with self.subTest(changes=changes):
                self.setUp()
                self.failed_and_ended()
                self.replacement(**changes)
                before = list(self.host.calls)
                self.tick(5)
                self.assertEqual(self.host.calls, before)

    def test_incomplete_metadata_defers_return_and_discovery(self):
        self.failed_and_ended()
        fresh = self.replacement()
        original = self.host.scan
        def partial():
            scan = service.Scan()
            scan.errors[fresh.port] = 'Synthetic incomplete metadata'
            return scan
        self.host.scan = partial
        before = list(self.host.calls)
        self.tick(5)
        self.assertEqual(self.host.calls, before)
        self.host.scan = original
        self.tick(3)
        self.assertEqual(self.manager.entries[fresh.port].phase, 'bootstrapping')


if __name__ == '__main__':
    unittest.main()
