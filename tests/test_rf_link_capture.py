# SPDX-License-Identifier: GPL-2.0-only
"""File-only RF regressions: synthetic sysfs, pipes, clocks and recorders."""
import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_hid_sidechannel_capture as helpers
import test_native_usb_capture as legacy
import rf_link_capture as rf
import rf_link_policy as policy

spec = importlib.util.spec_from_file_location('rf_identity', rf.ASSETS / 'rf-identity-check.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
scan_descriptors = identity.scan_descriptors
manager_paused = identity.manager_paused


def target():
    value = helpers.target()
    value.update(pid='109c')
    value['interfaces']['1'] = {'driver': None, 'endpoints': []}
    return value


def observation(value=None, kind='present'):
    value = copy.deepcopy(value or target())
    return {'observation': kind, 'identity': value if kind == 'present' else None,
        'boot_id': value['boot_id'], 'parent': {k: v for k, v in value['sysfs_identity'].items()
                                              if k.startswith('parent_')},
        'manager_paused_empty': True, 'input_consumer_open': kind == 'present', 'reason': ''}


class PolicyTests(unittest.TestCase):
    def tracker(self):
        obj = policy.Tracker(target())
        obj.observe(observation(), 0, initial=True)
        return obj

    def test_baseline_strict_and_first_boundary_required(self):
        for key, value in [('port', '8-5'), ('pid', '105e'), ('pid', '100a'),
                           ('vid', '045e'), ('devnum', '128'), ('busnum', '9'), ('boot_id', '')]:
            with self.subTest(key=key, value=value):
                invalid = target()
                invalid[key] = value
                with self.assertRaises(ValueError):
                    policy.Tracker(invalid)
        with self.assertRaises(ValueError):
            policy.Tracker(target()).observe(observation(), 0)

    def test_complete_epoch_not_address_is_identity(self):
        obj = self.tracker()
        second = target()
        second['sysfs_identity']['st_ino'] += 1
        obj.observe(observation(second), 1)
        self.assertEqual(len(obj.epochs), 2)  # Reused address, distinct object.
        third = copy.deepcopy(second)
        third['sysfs_identity']['st_ino'] += 1
        third.update(devnum='9', pid='100a')
        third['interfaces']['1'] = {'driver': 'usbhid', 'endpoints': [4, 132]}
        obj.observe(observation(third), 2)
        self.assertEqual(len(obj.epochs), 3)
        self.assertFalse(obj.observe(observation(third), 3, final=True)['radio_connected_proven'])

    def test_same_object_mutation_and_retired_epoch_rejected(self):
        obj = self.tracker()
        changed = target()
        changed['devnum'] = '9'
        with self.assertRaisesRegex(ValueError, 'Same USB object'):
            obj.observe(observation(changed), 1)
        obj = self.tracker()
        changed['sysfs_identity']['st_ino'] += 1
        obj.observe(observation(changed), 1)
        with self.assertRaisesRegex(ValueError, 'Retired'):
            obj.observe(observation(), 2)

    def test_unknown_metadata_is_bounded_not_connection_proof(self):
        for kind, limit in [('pending', 2), ('absent', 5)]:
            with self.subTest(kind=kind):
                obj = self.tracker()
                self.assertFalse(obj.observe(observation(kind=kind), 1)['radio_connected_proven'])
                obj.observe(observation(kind=kind), 1 + limit)
                with self.assertRaises(ValueError):
                    obj.observe(observation(kind=kind), 1.01 + limit)
                with self.assertRaisesRegex(ValueError, 'terminal'):
                    obj.observe(observation(), 10)

    def test_late_complete_metadata_cannot_erase_deadline(self):
        obj = self.tracker()
        obj.observe(observation(kind='pending'), 1)
        with self.assertRaisesRegex(ValueError, 'Late metadata'):
            obj.observe(observation(), 3.1)

    def test_unknown_final_and_initial_cannot_pass(self):
        for kind in ('pending', 'absent'):
            with self.assertRaises(ValueError):
                policy.Tracker(target()).observe(observation(kind=kind), 0, initial=True)
            with self.assertRaises(ValueError):
                self.tracker().observe(observation(kind=kind), 1, final=True)

    def test_foreign_owner_parent_boot_and_no_consumer_stop(self):
        for key, value in [('boot_id', 'different'), ('parent', {}),
                           ('manager_paused_empty', False), ('input_consumer_open', False)]:
            with self.subTest(key=key):
                changed = observation()
                changed[key] = value
                with self.assertRaises(ValueError):
                    self.tracker().observe(changed, 1)
        for field, value in [('driver', 'gs_native'), ('endpoints', [1, 129])]:
            changed = observation()
            changed['identity']['interfaces']['0'][field] = value
            with self.assertRaises(ValueError):
                self.tracker().observe(changed, 1)

    def test_epoch_limit_and_clock_guards(self):
        obj = self.tracker()
        for n in range(1, 4):
            changed = target()
            changed['sysfs_identity']['st_ino'] += n
            obj.observe(observation(changed), n)
        changed['sysfs_identity']['st_ino'] += 1
        with self.assertRaisesRegex(ValueError, 'Too many'):
            obj.observe(observation(changed), 4)
        for stamp in (True, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.tracker().observe(observation(), stamp)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name in ('run', 'Popen'):
            self.stack.enter_context(patch.object(rf.subprocess, name,
                side_effect=AssertionError('No live subprocess allowed')))

    def test_plan_and_manifest_are_file_only(self):
        value = rf.make_manifest(target(), helpers.metadata())
        self.assertEqual(value['scope'], policy.SCOPE)
        self.assertEqual(value['usb_capture']['duration_seconds'], 90)
        self.assertEqual(value['usb_capture']['outer_timeout_seconds'], 120)
        self.assertFalse(rf.plan()['hardware_access'])
        self.assertEqual(set(value['sha256']), {str(p.relative_to(rf.ROOT)) for p in rf.source_paths()})
        self.assertEqual(rf.validate_manifest(value), value)
        with self.assertRaises(helpers.capture.CaptureHalt):
            helpers.passive.validate_manifest(value)  # No widening legacy scopes.

    def test_modified_pin_scope_and_budget_rejected(self):
        for mutate in (
            lambda v: v.update(scope='passive-hid-100a-90'),
            lambda v: v['usb_capture'].update(duration_seconds=300),
            lambda v: v['usb_capture'].update(outer_timeout_seconds=120.0),
            lambda v: v['sha256'].update({'tools/native/rf_link_policy.py': '0'*64}),
            lambda v: v['sha256'].update({'extra': '0'*64})):
            value = rf.make_manifest(target(), helpers.metadata())
            mutate(value)
            with self.assertRaises(helpers.capture.CaptureHalt):
                rf.validate_manifest(value)

    def test_shared_guest_rf_budget_and_existing_profile_limits(self):
        tree = ast.parse((rf.ASSETS / 'guest-check.py').read_text())
        duration = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'duration' for t in n.targets))
        expression = ast.Expression(duration)
        for node in ast.walk(expression):
            self.assertIsInstance(node, (ast.Expression, ast.IfExp, ast.Compare, ast.Eq,
                                        ast.Name, ast.Load, ast.Constant))
        for profile, expected in ((policy.SCOPE, 90), ('passive-hid-100a-90', 90),
                                   ('passive-hid-100a-300', 300), (None, 450)):
            self.assertEqual(eval(compile(expression, 'pure-duration-expression', 'eval'),
                                  {'__builtins__': {}}, {'profile': profile}), expected)

    def test_file_import_refuses_duplicate_keys_symlinks_and_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.json'
            path.write_text('{"scope":1,"scope":2}')
            with self.assertRaises(helpers.capture.CaptureHalt):
                rf.read_json(path)
            link = Path(directory) / 'link'
            link.symlink_to(path)
            with self.assertRaises(helpers.capture.CaptureHalt):
                rf.read_json(link)
            for name in ('/dev/null', '/proc/self/status', '/sys/kernel/uevent_seqnum'):
                with self.assertRaises(helpers.capture.CaptureHalt):
                    rf.read_json(name)

    def test_attach_is_inert_and_rf_not_legacy_identity_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / 'build/hardware-tests/rf-synthetic'
            parent.mkdir(parents=True, mode=0o700)
            value = rf.make_manifest(target(), helpers.metadata())
            with patch.object(helpers.capture, 'ROOT', Path(directory)), \
                 patch.object(helpers.capture, 'verify_sources', return_value=value['sha256']):
                obj = helpers.capture.attach(value, parent)
            self.assertTrue(obj.rf and obj.passive)
            self.assertEqual((obj.duration, obj.outer_timeout, obj.tail), (90, 120, 0))
            self.assertEqual(obj.identity_asset, 'rf-identity-check.py')
            self.assertFalse(obj.directory.exists())


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.clock = helpers.VirtualClock()
        self.recorder = helpers.SyntheticRecorder(self.clock)
        self.recorder.deadline = 190
        self.events = []

    def terminal(self, messages):
        pending = list(messages)
        def poll():
            lines = []
            while pending and self.clock.now() >= 100 + pending[0][0]:
                lines.append(pending.pop(0)[1])
            return lines
        return SimpleNamespace(poll=poll)

    def run_series(self, messages):
        return rf.run_phases(self.recorder, self.terminal(messages), clock=self.clock.now,
            sleep=self.clock.wait, emit=self.events.append)

    def test_exact_phases_and_connection_receipt(self):
        value = self.run_series([(35, 'verbunden')])
        by_name = {e['event']: e for e in self.events}
        for name, expected in [('heads_up', 20), ('power_on', 30), ('inputs', 60),
                               ('final_rest', 80), ('capture_finish', 89)]:
            self.assertAlmostEqual(by_name[name]['seconds_from_capture_request'], expected, delta=.11)
        self.assertFalse(value['radio_connected_proven'])
        self.assertGreaterEqual(value['user_connected_at_seconds'], 35)
        self.assertLess(self.clock.now(), 190)

    def test_no_connection_and_premature_confirmation_stop_at_60(self):
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'No connection confirmation'):
            self.run_series([(10, 'verbunden')])
        self.assertTrue(any(e['event'] == 'confirmation_not_accepted' for e in self.events))
        self.assertFalse(any(e['event'] == 'inputs' for e in self.events))
        self.assertLess(self.clock.now(), 161)

    def test_stop_and_recorder_fault_are_terminal(self):
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'Local STOP'):
            self.run_series([(32, 'stop')])
        self.assertEqual(self.recorder.actions, [])  # Coordinator never manipulates driver.
        self.clock.stamp = 105
        self.recorder.fault_at = 110
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'Synthetic identity'):
            self.run_series([])

    def test_clock_jump_stops_before_late_power_on(self):
        def jump(seconds):
            self.clock.stamp += 26
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'clock jumped'):
            rf.run_phases(self.recorder, self.terminal([]), clock=self.clock.now,
                          sleep=jump, emit=self.events.append)
        self.assertFalse(any(e['event'] == 'power_on' for e in self.events))

    def test_same_unbuffered_input_handles_go_then_connection(self):
        read, write = os.pipe()
        try:
            tty = rf.TerminalLines(read)
            os.write(write, b'G')
            self.assertEqual(tty.poll(), [])
            os.write(write, b'O\n')
            rf.await_go(tty, clock=self.clock.now, sleep=self.clock.wait)
            os.write(write, b'VERBUNDEN\n')
            self.assertEqual(tty.poll(), ['verbunden'])
            os.close(write)
            write = None
            with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'EOF'):
                tty.poll()
        finally:
            os.close(read)
            if write is not None:
                os.close(write)

    def test_oversized_terminal_line_rejected(self):
        tty = rf.TerminalLines(999)
        with patch.object(rf.select, 'select', return_value=([999], [], [])), \
             patch.object(rf.os, 'read', return_value=b'x'*512):
            tty.poll()
            tty.poll()
            with self.assertRaises(helpers.capture.CaptureHalt):
                tty.poll()

    def test_go_timeout_never_attaches_recorder(self):
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'No local GO'):
            rf.await_go(self.terminal([]), clock=self.clock.now, sleep=self.clock.wait)

    def test_go_and_stop_in_same_terminal_batch_never_start(self):
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'STOP before capture'):
            rf.await_go(SimpleNamespace(poll=lambda: ['go', 'stop']),
                        clock=self.clock.now, sleep=self.clock.wait)

    def test_real_pseudoterminal_keeps_go_and_connection_input(self):
        master, slave = os.openpty()
        try:
            self.assertTrue(os.isatty(slave))
            terminal = rf.TerminalLines(slave)
            os.write(master, b'GO\n')
            self.assertTrue(rf.select.select([slave], [], [], 1)[0])
            rf.await_go(terminal, clock=self.clock.now, sleep=self.clock.wait)
            os.write(master, b'VERBUNDEN\n')
            self.assertTrue(rf.select.select([slave], [], [], 1)[0])
            self.assertEqual(terminal.poll(), ['verbunden'])
        finally:
            os.close(master)
            os.close(slave)

    def test_slow_metadata_check_does_not_emit_late_power_on_cue(self):
        def slow(*args):
            self.clock.stamp += 25
        self.recorder.check = slow
        with self.assertRaisesRegex(helpers.capture.CaptureHalt, 'Metadata check exceeded'):
            self.run_series([])
        self.assertFalse(any(e['event'] == 'power_on' for e in self.events))


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.usb = self.root / 'sys/bus/usb/devices'
        self.usb.mkdir(parents=True)
        self.parent = self.root / 'fake-sysfs/usb8'
        self.device = self.parent / '8-6'
        self.device.mkdir(parents=True)
        (self.usb / 'usb8').symlink_to(self.parent)
        (self.usb / '8-6').symlink_to(self.device)
        self.put('proc/sys/kernel/random/boot_id', target()['boot_id'])
        for key, value in {'idVendor': '3537', 'idProduct': '109c', 'busnum': '8',
                           'devnum': '8', 'devpath': '6', 'bNumInterfaces': '2'}.items():
            (self.device / key).write_text(value)
        for i in (0, 1):
            iface = self.device / f'8-6:1.{i}'
            iface.mkdir()
            (self.usb / iface.name).symlink_to(iface)
            (iface / 'bInterfaceNumber').write_text(f'{i:02x}')
            if i == 0:
                driver = self.root / 'drivers/xpad'
                driver.mkdir(parents=True)
                (iface / 'driver').symlink_to(driver)
                for number in ('02', '82'):
                    ep = iface / ('ep_' + number)
                    ep.mkdir()
                    (ep / 'bEndpointAddress').write_text(number)
        event = self.device / '8-6:1.0/input/input4/event7'
        event.mkdir(parents=True)
        event_class = self.root / 'sys/class/input'
        event_class.mkdir(parents=True)
        (event_class / 'event7').symlink_to(event)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.manager = self.stack.enter_context(patch.object(identity, 'manager_paused'))
        self.scanner = self.stack.enter_context(patch.object(identity, 'scan_descriptors', return_value=True))
        self.stack.enter_context(patch.object(identity, 'character_rdev', return_value=99))

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def snapshot(self, diagnostics=None):
        return identity.snapshot({'capture_profile': policy.SCOPE}, self.root, diagnostics=diagnostics)

    def test_complete_cached_metadata_and_consumer(self):
        value = self.snapshot()
        self.assertEqual(value['observation'], 'present')
        policy.Tracker(value['identity']).observe(value, 0, initial=True)
        self.assertEqual(self.manager.call_count, 2)

    def test_empty_and_missing_fields_are_unknown_not_connected(self):
        path = self.device / 'devnum'
        path.write_text('')
        self.assertEqual(self.snapshot()['observation'], 'pending')
        path.unlink()
        self.assertIsNone(self.snapshot()['identity'])
        (self.usb / '8-6').unlink()
        self.assertEqual(self.snapshot()['observation'], 'absent')

    def test_permission_failure_not_unknown(self):
        with patch.object(identity, 'attribute', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                self.snapshot()

    def test_no_consumer_is_pending_not_silent_negative_rf(self):
        self.scanner.return_value = False
        value = self.snapshot()
        self.assertEqual((value['observation'], value['identity']), ('pending', None))
        self.assertIn('consumer', value['reason'])

    def test_diagnostics_identify_empty_attribute_without_inventing_no_input_node(self):
        (self.device / 'devnum').write_text('')
        details = []
        value = self.snapshot(details)
        self.assertEqual(value['observation'], 'pending')
        item = next(d for d in details if d['field'] == 'device.devnum' and d['status'] == 'unknown')
        self.assertEqual(item['observed'], '')
        self.assertEqual(item['error_type'], 'Pending')
        nodes = next(d for d in details if d['field'] == 'input.IF0.event_nodes')
        self.assertEqual(nodes['status'], 'not_evaluated')
        self.assertIsNone(nodes['observed'])

    def test_missing_attribute_reports_field_and_errno(self):
        (self.device / 'devnum').unlink()
        details = []
        self.snapshot(details)
        item = next(d for d in details if d['field'] == 'device.devnum' and d['status'] == 'unknown')
        self.assertEqual((item['error_type'], item['errno']), ('FileNotFoundError', 2))

    def test_missing_input_node_and_existing_unopened_node_are_distinct(self):
        self.scanner.return_value = False
        details = []
        self.snapshot(details)
        consumer = next(d for d in details if d['field'] == 'input.IF0.consumer_open')
        self.assertEqual((consumer['status'], consumer['observed']), ('failed', False))
        nodes = next(d for d in details if d['field'] == 'input.IF0.event_nodes')
        self.assertEqual((nodes['status'], nodes['observed']), ('passed', 1))
        (self.root / 'sys/class/input/event7').unlink()
        details = []
        self.snapshot(details)
        nodes = next(d for d in details if d['field'] == 'input.IF0.event_nodes')
        self.assertEqual((nodes['status'], nodes['observed']), ('failed', 0))
        consumer = next(d for d in details if d['field'] == 'input.IF0.consumer_open')
        self.assertEqual(consumer['status'], 'not_evaluated')
        self.assertIsNone(consumer['observed'])

    def test_binding_and_endpoint_diagnostics_identify_exact_interface(self):
        link = self.device / '8-6:1.0/driver'
        link.unlink()
        details = []
        self.snapshot(details)
        driver = next(d for d in details if d['field'] == 'interfaces.0.driver')
        self.assertEqual((driver['status'], driver['expected'], driver['observed']), ('unknown', 'xpad', None))
        link.symlink_to(self.root / 'drivers/xpad')
        (self.device / '8-6:1.0/ep_82/bEndpointAddress').write_text('81')
        details = []
        with self.assertRaisesRegex(ValueError, 'Unexpected endpoints'):
            self.snapshot(details)
        failure = next(d for d in details if d['status'] == 'failed')
        self.assertEqual(failure['field'], 'interfaces.0.endpoints')
        self.assertEqual((failure['expected'], failure['observed']), ([2, 130], [2, 129]))

    def test_real_asset_propagates_consumer_details_into_failed_preflight(self):
        self.scanner.return_value = False
        manager = {'ok': True, 'paused': True, 'returned': True, 'devices': {}}
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(manager), stderr=''))
        later = Mock(side_effect=AssertionError('No later inspection after failure'))
        with patch.object(rf.os, 'geteuid', return_value=0), self.assertRaises(rf.PreflightFailure) as caught:
            rf.inspect(authorized=True, run=run,
                reader=lambda *, diagnostics: self.snapshot(diagnostics),
                metadata_reader=later, monitor_reader=later)
        run.assert_called_once()
        self.scanner.assert_called_once()
        later.assert_not_called()
        report = caught.exception.report
        details = report['metadata_details']['baseline']
        self.assertTrue(any(d['field'] == 'device.idProduct' and d.get('observed') == '109c' for d in details))
        self.assertTrue(any(d['field'] == 'input.IF0.consumer_open' and d['status'] == 'failed' for d in details))
        self.assertIn('input.IF0.consumer_open', str(caught.exception))
        self.assertEqual(report['stages']['dumpcap_metadata'], 'not_evaluated')

    def test_disappearing_driver_link_is_unknown_not_no_native_owner_proof(self):
        original = Path.resolve
        seen = []
        def unstable(path, **kwargs):
            if path.name == 'driver' and not seen:
                seen.append(path)
                raise FileNotFoundError('synthetic enumeration race')
            return original(path, **kwargs)
        with patch.object(Path, 'resolve', autospec=True, side_effect=unstable):
            value = self.snapshot()
        self.assertEqual((value['observation'], value['identity']), ('pending', None))
        self.assertIn('binding_metadata_changed', value['reason'])

    def test_wrong_product_driver_endpoint_and_parent_are_hard_failures(self):
        product = self.device / 'idProduct'
        product.write_text('105e')
        with self.assertRaisesRegex(ValueError, 'VID/PID'):
            self.snapshot()
        product.write_text('109c')
        ep = self.device / '8-6:1.0/ep_82/bEndpointAddress'
        ep.write_text('81')
        with self.assertRaisesRegex(ValueError, 'endpoints'):
            self.snapshot()
        ep.write_text('82')
        other = self.root / 'drivers/usbfs'
        other.mkdir()
        link = self.device / '8-6:1.0/driver'
        link.unlink()
        link.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'owner'):
            self.snapshot()

    def test_other_supported_receiver_and_any_native_binding_stop(self):
        other = self.usb / '8-5'
        other.mkdir()
        (other / 'idVendor').write_text('3537')
        (other / 'idProduct').write_text('105e')
        with self.assertRaisesRegex(ValueError, 'Another supported'):
            self.snapshot()
        (other / 'idVendor').write_text('045e')
        native = self.root / 'drivers/gs_native'
        native.mkdir()
        iface = self.usb / '8-5:1.0'
        iface.mkdir()
        (iface / 'driver').symlink_to(native)
        with self.assertRaisesRegex(ValueError, 'Native USB binding'):
            self.snapshot()

    def test_open_usb_alias_and_deadband_rejected_by_fd_metadata(self):
        self.put('proc/12/cmdline', 'example\0')
        self.put('proc/12/fd/4', '')
        fake = SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=44)
        with patch.object(Path, 'stat', return_value=fake):
            with self.assertRaisesRegex(ValueError, 'raw USB'):
                scan_descriptors(self.root, {44}, set())
        self.put('proc/12/cmdline', '/usr/bin/deadband\0')
        with self.assertRaisesRegex(ValueError, 'Deadband'):
            scan_descriptors(self.root, set(), set())

    def test_inaccessible_pseudo_fd_is_not_bypassed(self):
        self.put('proc/12/cmdline', 'example\0')
        self.put('proc/12/fd/4', '')
        with patch.object(Path, 'stat', side_effect=PermissionError(13, 'denied')):
            with self.assertRaisesRegex(ValueError, 'pid=12 operation=fd-stat fd=4 errno=13'):
                scan_descriptors(self.root, set(), set())

    def test_only_exact_input_rdev_counts_as_consumer(self):
        self.put('proc/12/cmdline', 'ordinary-test-client\0')
        self.put('proc/12/fd/4', '')
        fake = SimpleNamespace(st_mode=stat.S_IFCHR, st_rdev=44)
        with patch.object(Path, 'stat', return_value=fake):
            self.assertFalse(scan_descriptors(self.root, set(), {45}))
            self.assertTrue(scan_descriptors(self.root, set(), {44}))

    def test_manager_guard_checks_root_private_empty_pause_without_writing(self):
        self.put('var/lib/gamesir-native/state.json', '{"paused":true,"leases":{}}')
        path = self.root / 'var/lib/gamesir-native/state.json'
        path.chmod(0o600)
        actual_fstat, actual_lstat = os.fstat, Path.lstat
        def root_owner(value):
            return SimpleNamespace(**{k: (0 if k == 'st_uid' else getattr(value, k)) for k in (
                'st_dev', 'st_ino', 'st_uid', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')})
        # Do not chown a real file or require actual root for this regression.
        with patch.object(identity.os, 'fstat', side_effect=lambda fd: root_owner(actual_fstat(fd))), \
             patch.object(Path, 'lstat', autospec=True,
                          side_effect=lambda p: root_owner(actual_lstat(p))):
            # Call the real implementation retained separately from snapshot's mock.
            manager_paused(self.root)
            path.write_text('{"paused":false,"leases":{}}')
            with self.assertRaisesRegex(ValueError, 'paused with empty'):
                manager_paused(self.root)
            path.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'Unsafe manager'):
                manager_paused(self.root)


class PreflightTests(unittest.TestCase):
    def inspect(self, status=None, reader=None):
        status = status or {'ok': True, 'paused': True, 'returned': True, 'devices': {},
                            'scan_error': '', 'port_errors': {}}
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(status), stderr=''))
        with patch.object(rf.os, 'geteuid', return_value=0):
            result = rf.inspect(authorized=True, run=run, reader=reader or Mock(return_value=observation()),
                                metadata_reader=helpers.metadata, monitor_reader=lambda: None)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ['/usr/bin/gamesir-native', 'status'])
        return result

    def test_success_is_read_only_and_contains_pinned_manifest(self):
        result = self.inspect()
        self.assertTrue(result['read_only'])
        self.assertFalse(result['capture_started'])
        self.assertTrue(result['needs_separately_approved_usbmon'])
        self.assertTrue(result['ok'])
        self.assertTrue(all(value == 'passed' for value in result['stages'].values()))
        rf.validate_manifest(result['manifest'])

    def test_no_approval_no_root_no_read(self):
        run = Mock()
        with self.assertRaises(helpers.capture.CaptureHalt):
            rf.inspect(run=run)
        with patch.object(rf.os, 'geteuid', return_value=1000):
            with self.assertRaises(helpers.capture.CaptureHalt):
                rf.inspect(authorized=True, run=run)
        run.assert_not_called()

    def test_pause_error_empty_ownership_and_second_snapshot_guards(self):
        for key, value in [('paused', False), ('returned', False), ('devices', {'8-6': {}}),
                           ('port_errors', {'8-6': 'blocked'})]:
            state = {'ok': True, 'paused': True, 'returned': True, 'devices': {}}
            state[key] = value
            with self.assertRaises(helpers.capture.CaptureHalt):
                self.inspect(status=state)
        changed = observation()
        changed['input_consumer_open'] = False
        with self.assertRaises(helpers.capture.CaptureHalt):
            self.inspect(reader=Mock(side_effect=[observation(), changed]))

    def failure(self, *, before=None, run=None, reader=None):
        manager = {'ok': True, 'paused': True, 'returned': True, 'devices': {}}
        run = run or Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(manager), stderr=''))
        reader = reader or Mock(return_value=before or observation())
        later = Mock(side_effect=AssertionError('No reads after failed baseline'))
        with patch.object(rf.os, 'geteuid', return_value=0), self.assertRaises(rf.PreflightFailure) as caught:
            rf.inspect(authorized=True, run=run, reader=reader, metadata_reader=later, monitor_reader=later)
        later.assert_not_called()
        return caught.exception

    def test_prior_compound_failure_replayed_as_separate_unknown_and_missing_conditions(self):
        # Synthetic alternatives, not a claim about the missing old live snapshot.
        for kind, reason in [('absent', 'enumeration_metadata_missing'),
                             ('pending', 'enumeration_metadata_empty'),
                             ('pending', 'ordinary_IF0_consumer_missing')]:
            with self.subTest(kind=kind, reason=reason):
                before = observation(kind=kind)
                before['reason'] = reason
                reader = Mock(return_value=before)
                error = self.failure(reader=reader)
                report = error.report
                reader.assert_called_once()
                self.assertEqual(report['snapshot'], before)
                self.assertEqual(report['failure']['stage'], 'baseline_conditions')
                self.assertIn(reason, report['failure']['message'])
                self.assertEqual(report['stages']['confirmation_metadata'], 'not_evaluated')
                self.assertFalse(report['ok'] or report['capture_started'] or report['module_load_attempted'])

    def test_consumer_gate_is_separate_even_for_malformed_present_snapshot(self):
        before = observation()
        before['input_consumer_open'] = False
        error = self.failure(before=before)
        self.assertIn('baseline.input_consumer_open', error.report['failure']['message'])
        self.assertEqual(error.report['checks'][-1]['observed'], False)

    def test_manager_command_failure_keeps_original_output_and_skips_receiver(self):
        run = Mock(return_value=SimpleNamespace(returncode=7, stdout='original output', stderr='original fault'))
        reader = Mock(side_effect=AssertionError('No receiver read after manager failure'))
        report = self.failure(run=run, reader=reader).report
        reader.assert_not_called()
        run.assert_called_once()
        self.assertEqual(report['manager_status_read'], {
            'returncode': 7, 'stdout': 'original output', 'stderr': 'original fault', 'output_truncated': False})
        self.assertEqual(report['failure']['stage'], 'manager_status')
        self.assertIn('manager.command_exit', report['failure']['message'])
        self.assertEqual(report['stages']['baseline_metadata'], 'not_evaluated')

    def test_manager_pause_and_schema_failures_name_exact_condition(self):
        for status, field in [({'ok': True, 'paused': False}, 'manager.paused'),
                              ({'ok': True, 'paused': True, 'returned': False}, 'manager.returned'),
                              ([], 'manager.schema')]:
            run = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(status), stderr=''))
            error = self.failure(run=run, reader=Mock(side_effect=AssertionError('No later read')))
            self.assertIn(field, error.report['failure']['message'])

    def test_permission_failure_keeps_unknown_instead_of_fabricating_no_consumer(self):
        reader = Mock(side_effect=PermissionError(13, 'synthetic inspection denied'))
        error = self.failure(reader=reader)
        self.assertEqual(error.report['failure']['type'], 'PermissionError')
        self.assertEqual(error.report['failure']['stage'], 'baseline_metadata')
        self.assertNotIn('snapshot', error.report)
        self.assertEqual(error.report['stages']['baseline_conditions'], 'not_evaluated')

    def test_confirmation_pinpoints_address_change_and_preserves_both_snapshots(self):
        before = observation()
        after = copy.deepcopy(before)
        after['identity']['devnum'] = '9'
        with self.assertRaises(rf.PreflightFailure) as caught:
            self.inspect(reader=Mock(side_effect=[before, after]))
        report = caught.exception.report
        self.assertEqual(report['snapshot'], before)
        self.assertEqual(report['confirmation_snapshot'], after)
        self.assertIn('confirmation.identity.devnum', report['failure']['message'])
        self.assertEqual(report['stages']['monitor_metadata'], 'not_evaluated')
        self.assertFalse(report['ok'])

    def test_cli_failure_emits_valid_json_and_nonzero_exit(self):
        failure = self.failure(before=observation(kind='absent'))
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(rf, 'inspect', side_effect=failure), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = rf.main(['inspect', '--authorize-read-only'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout.getvalue()), failure.report)
        self.assertIn(failure.report['failure']['message'], stderr.getvalue())

    def test_failed_report_with_valid_intermediate_manifest_cannot_prepare_capture(self):
        before = observation()
        changed = copy.deepcopy(before)
        changed['input_consumer_open'] = False
        with self.assertRaises(rf.PreflightFailure) as caught:
            self.inspect(reader=Mock(side_effect=[before, changed]))
        self.assertIn('manifest', caught.exception.report)  # Already built, but later check failed.
        with tempfile.TemporaryDirectory() as directory:
            preflight, output = Path(directory) / 'failed.json', Path(directory) / 'must-not-exist.json'
            preflight.write_text(json.dumps(caught.exception.report))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(rf.main(['prepare', '--preflight', str(preflight), '--manifest', str(output)]), 1)
            self.assertFalse(output.exists())

    def test_successful_report_can_prepare_manifest_offline(self):
        report = self.inspect()
        with tempfile.TemporaryDirectory() as directory:
            preflight, output = Path(directory) / 'ok.json', Path(directory) / 'manifest.json'
            preflight.write_text(json.dumps(report))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rf.main(['prepare', '--preflight', str(preflight), '--manifest', str(output)]), 0)
            self.assertEqual(rf.read_json(output), report['manifest'])


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.parent = self.directory / 'build/hardware-tests/rf-synthetic'
        self.parent.mkdir(parents=True, mode=0o700)
        self.manifest = rf.make_manifest(target(), helpers.metadata())
        for name in ('run', 'Popen'):
            self.stack.enter_context(patch.object(helpers.capture.subprocess, name,
                side_effect=AssertionError('No live process')))

    def active(self):
        with patch.object(helpers.capture, 'ROOT', self.directory), \
             patch.object(helpers.capture, 'verify_sources', return_value=self.manifest['sha256']):
            obj = helpers.capture.attach(self.manifest, self.parent)
        obj.directory.mkdir(mode=0o700)
        obj.created_directory = obj.started = True
        obj.ready, obj.deadline = 100, 190
        obj.process, obj.observer = Mock(), Mock()
        obj.process.poll.return_value = obj.observer.poll.return_value = 0
        obj.process.returncode = 0
        obj.baseline = {'identity': observation(), 'target': target(),
                        'capture_profile': policy.SCOPE, 'synthetic_host': True}
        obj.rf_tracker.observe(observation(), 0, initial=True)
        obj.rf_log = obj._file('rf-observations.jsonl')
        (obj.directory / 'capture.log').write_text(
            'MEASUREMENT_B_RESULT_JSON {"passed":true,"dumpcap_reaped":true}\n')
        (obj.directory / 'original-usbmon8.pcapng').write_bytes(b'\x0a\x0d\x0d\x0asynthetic')
        return obj

    def test_rf_start_selects_pinned_observer_and_bounded_existing_sandbox(self):
        capture = helpers.capture
        with patch.object(capture, 'ROOT', self.directory), \
             patch.object(capture, 'verify_sources', return_value=self.manifest['sha256']):
            obj = capture.attach(self.manifest, self.parent)
        host, records = legacy.evidence()
        host.pop('identity')
        snapshot = observation()
        records['STAGE4_IDENTITY_JSON']['identity'] = snapshot
        ready = records['MEASUREMENT_B_DUMPCAP_JSON']
        ready.update(checked_monotonic_ns=102000000000, capture_started_monotonic_ns=102000000000)
        supervisor = {'pid': 123, 'starttime': '100'}
        records['MEASUREMENT_B_SUPERVISOR_JSON'] = supervisor
        observer, process = Mock(), Mock()
        observer.poll.return_value = process.poll.return_value = None
        process.pid = 123
        try:
            with patch.object(capture.os, 'geteuid', return_value=0), \
                 patch.object(capture.os, 'chown'), \
                 patch.object(capture.os, 'pidfd_open', return_value=99), \
                 patch.object(capture, 'verify_sources', return_value=self.manifest['sha256']), \
                 patch.object(capture, 'dumpcap_metadata', return_value=helpers.metadata()), \
                 patch.object(capture.shutil, 'disk_usage', return_value=SimpleNamespace(free=5*capture.GIB)), \
                 patch.object(obj, '_metadata', side_effect=[host, snapshot, snapshot]), \
                 patch.object(capture.subprocess, 'Popen', side_effect=[observer, process]) as spawn, \
                 patch.object(capture.time, 'monotonic', return_value=102), \
                 patch.object(capture.select, 'poll') as poll, \
                 patch.object(capture, 'marker_records', return_value=records), \
                 patch.object(obj, '_supervisor_identity', return_value=supervisor), \
                 patch.object(obj, '_dumpcap_identity', return_value={'pid': 127, 'starttime': '101'}):
                poll.return_value.poll.return_value = []
                obj.start()
            argv = spawn.call_args_list[-1].args[0]
            self.assertEqual(argv[:4], ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2s', '120s'])
            self.assertEqual(argv[-1], (rf.ASSETS / 'rf-identity-check.py').read_text())
            self.assertIn('/usr/bin/unshare', argv)
            self.assertEqual(obj.deadline, 192)
            self.assertEqual(len(obj.rf_tracker.epochs), 1)
            self.assertEqual(stat.S_IMODE((obj.directory / 'original-usbmon8.pcapng').stat().st_mode), 0o600)
        finally:
            for stream in obj.streams:
                if not stream.closed:
                    stream.close()

    def test_final_new_epoch_allowed_without_merging_and_checksums_cover_cues(self):
        obj = self.active()
        changed = target()
        changed['sysfs_identity']['st_ino'] += 1
        changed['devnum'] = '9'
        cue = obj._file('phase-cues.jsonl')
        cue.write(b'{"event":"synthetic"}\n')
        with patch.object(obj, '_metadata', side_effect=[{'synthetic_host': True}, observation(changed)]):
            result = obj.finish()
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['rf_epochs']), 2)
        self.assertTrue(cue.closed and obj.rf_log.closed)
        self.assertIn('phase-cues.jsonl', (obj.directory / 'SHA256SUMS').read_text())
        self.assertIn('rf-observations.jsonl', (obj.directory / 'SHA256SUMS').read_text())
        self.assertTrue(rf.persist_result(self.parent, {'capture': result}, obj.owner)['checksum_manifest_verified'])

    def test_failed_final_unknown_preserves_primary_error_and_original(self):
        obj = self.active()
        with patch.object(obj, '_metadata', side_effect=[{'synthetic_host': True}, observation(kind='pending')]):
            result = obj.abort('Original failure at power-on')
        self.assertFalse(result['passed'])
        self.assertTrue(result['failure'].startswith('Original failure at power-on'))
        self.assertIn('final verification', result['failure'])
        self.assertTrue((obj.directory / 'original-usbmon8.pcapng').exists())
        self.assertTrue(obj.rf_log.closed)

    def test_periodic_check_accepts_bounded_unknown_and_stops_foreign_owner(self):
        obj = self.active()
        obj.process.poll.return_value = obj.observer.poll.return_value = None
        obj.dumpcap_fd = 99
        for name in ('usb-udev-events.log', 'udev-stderr.log'):
            (obj.directory / name).write_bytes(b'')
        with patch.object(helpers.capture.time, 'monotonic', return_value=110), \
             patch.object(helpers.capture.shutil, 'disk_usage', return_value=SimpleNamespace(free=5*helpers.capture.GIB)), \
             patch.object(helpers.capture.select, 'poll') as poll, \
             patch.object(obj, '_metadata', return_value=observation(kind='pending')):
            poll.return_value.poll.return_value = []
            obj.check(0, 'synthetic RF')
            self.assertEqual(obj.rf_tracker.current, None)
        obj.rf_log.close()

    def test_execute_requires_authorization_before_terminal_or_attach(self):
        factory = Mock()
        with self.assertRaises(helpers.capture.CaptureHalt):
            rf.execute(self.manifest, self.parent, capture_factory=factory)
        factory.assert_not_called()

    def execute_fake(self, recorder, clock, *, persist=None, emit=None):
        terminal = SimpleNamespace(poll=lambda: ['go'] if clock.now() < 106 else (
            ['verbunden'] if 135 <= clock.now() < 136 else []))
        with contextlib.redirect_stdout(io.StringIO()), \
             patch.object(rf.os, 'geteuid', return_value=0), \
             patch.object(sys.stdin, 'isatty', return_value=True), \
             patch.object(sys.stdout, 'isatty', return_value=True), \
             patch.object(rf, 'persist_result', side_effect=persist,
                          return_value={'checksum_manifest_verified': True}):
            return rf.execute(self.manifest, self.parent, authorized=True, terminal=terminal,
                capture_factory=Mock(return_value=recorder), clock=clock.now,
                sleep=clock.wait, emit=emit or (lambda _: None))

    def test_execute_single_run_never_changes_driver(self):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock)
        recorder.deadline, recorder.owner = 190, (1000, 1000)
        old_finish = recorder.finish
        def finish():
            for stream in recorder.streams:
                stream.close()
            return old_finish()
        recorder.finish = finish
        result = self.execute_fake(recorder, clock)
        self.assertEqual(recorder.actions, ['start', 'finish'])
        self.assertTrue(all(stream.closed for stream in recorder.streams))
        self.assertFalse(result['drivers_changed'] or result['hardware_commands_sent_by_helper'])

    def test_execute_failure_preserved_even_when_abort_and_persistence_fail(self):
        clock = helpers.VirtualClock()
        recorder = helpers.SyntheticRecorder(clock)
        recorder.owner = (1000, 1000)
        recorder.start = Mock(side_effect=ValueError('Original start fault'))
        recorder.abort = Mock(side_effect=ValueError('Secondary stop fault'))
        with self.assertRaisesRegex(ValueError, 'Original start fault'):
            self.execute_fake(recorder, clock, persist=OSError('Secondary storage fault'))
        recorder.start.assert_called_once()
        recorder.abort.assert_called_once_with('ValueError: Original start fault')


if __name__ == '__main__':
    unittest.main(verbosity=2)
