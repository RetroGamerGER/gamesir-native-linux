#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Integrated manager/readiness tests with test-owned metadata only."""
from dataclasses import replace
import importlib.util
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_service_manager import Fake, device, proof, service
from input_pair_readiness import Binding, Sensor
from input_readiness import ProcessedInputs, ReadinessError, fingerprint, user_can_read


class FeatureHost(Fake):
    readiness_enabled = True

    def __init__(self):
        super().__init__([device()])
        self.processed = False
        self.readable = False
        self.published = False
        self.input_error = ''
        self.publish_error = False

    def input_binding(self, d, meta):
        return Binding(d.parent, d.token, '/fixture/' + d.interface, meta['uniq'])

    def input_sensor(self, binding, meta):
        if self.input_error:
            raise ReadinessError(self.input_error)
        return Sensor(binding, 'node-life', 'node-life' if self.processed else '',
                      self.readable, (meta['gyro'],)*3, (meta['accel'],)*3)

    def start(self, operation, d, kernel_tokens=None):
        job = super().start(operation, d, kernel_tokens)
        if operation in ('input-info', 'publish-input'):
            assert kernel_tokens == service.boot_proof(proof(d))['tokens']
            if operation == 'publish-input':
                self.published = not self.publish_error
            value = dict(flags=7 if self.published else 5,
                         port=kernel_tokens[0], instance=kernel_tokens[1],
                         sensor='input42', uniq=f'gsn-{d.interface}-{d.address}', gyro=100, accel=8192)
            job['result'] = (1 if self.publish_error else 0, 'input-publication ' + json.dumps(value))
        return job


class Integration(unittest.TestCase):
    def setUp(self):
        self.host = FeatureHost()
        self.manager = service.Manager(self.host, lambda: self.host.now)

    def waiting(self):
        self.manager.tick(); self.manager.tick()
        old = self.host.devices['2-3.4']
        current = device(pid='109c', generation=2, driver='gs_native', parent=old.parent)
        self.host.devices[current.port] = current
        self.host.complete('bootstrap', output=proof(current))
        for _ in range(3):
            self.manager.tick()
        self.assertEqual(self.manager.entries[current.port].phase, 'awaiting_sensor')
        return self.manager.entries[current.port]

    def publications(self):
        return [call for call in self.host.calls if call[0] == 'publish-input']

    def test_receipt_and_access_required_before_exact_once_publication(self):
        self.waiting()
        self.manager.tick(); self.assertFalse(self.publications())
        self.host.processed = True
        self.manager.tick(); self.assertFalse(self.publications())
        self.host.readable = True
        self.manager.tick(); self.assertEqual(len(self.publications()), 1)
        self.manager.tick()
        self.assertEqual(self.manager.entries['2-3.4'].phase, 'active')
        self.assertTrue(self.host.published)
        self.assertEqual(len(self.publications()), 1)

    def test_timeout_keeps_cleanup_authority_despite_exhausted_start_budget(self):
        entry = self.waiting()
        self.host.now = entry.publication_deadline + 1
        self.manager.budgets[entry.device.port].extend([0, 0, 0])
        self.manager.tick(); self.assertEqual(entry.phase, 'failed')
        self.manager.tick()
        self.assertEqual(entry.operation, 'end')
        self.assertEqual(len([c for c in self.host.calls if c[0] == 'end']), 1)
        self.assertFalse(self.publications())

    def test_release_while_waiting_ends_owned_binding(self):
        entry = self.waiting()
        self.manager.command('release'); self.manager.tick()
        self.assertTrue(self.manager.paused)
        self.assertEqual(entry.operation, 'end')
        self.assertFalse(self.publications())

    def test_monitor_failure_cleans_pending_binding_and_blocks_new_claims(self):
        entry = self.waiting()
        self.host.input_error = 'synthetic receipt overflow'
        self.host.devices['4-1'] = device('4-1')
        self.manager.tick()
        self.assertEqual(entry.phase, 'failed')
        self.assertIn('receipt overflow', entry.error)
        self.manager.tick(); self.assertEqual(entry.operation, 'end')
        self.assertNotIn(('claim', '4-1'), self.host.calls)

    def test_replacement_cannot_inherit_a_pending_permission(self):
        entry = self.waiting()
        self.host.processed = self.host.readable = True
        self.host.devices[entry.device.port] = replace(entry.device, token='replacement', parent='new-hub')
        self.manager.tick()
        self.assertFalse(self.publications())

    def test_failed_publication_is_not_repeated_and_retains_failure(self):
        entry = self.waiting()
        self.host.processed = self.host.readable = True
        self.host.publish_error = True
        self.manager.tick(); self.manager.tick()
        self.assertEqual(entry.phase, 'failed')
        self.assertTrue(self.host.saved['recent_failures'])
        self.manager.tick()
        self.assertEqual(entry.operation, 'end')
        self.assertEqual(len(self.publications()), 1)

    def test_cleanup_failure_cannot_erase_original_publication_error(self):
        entry = self.waiting()
        self.host.processed = self.host.readable = True
        self.host.publish_error = True
        self.manager.tick(); self.manager.tick()
        primary = entry.publication_failure
        self.assertIn('rc=1', primary)
        self.manager.fail(entry, 'Return deadline; manual recovery required', 'blocked')
        self.manager.remember(entry)
        self.assertEqual(self.host.saved['recent_failures'][-1]['message'], primary)
        recovered = service.Manager(self.host, lambda: self.host.now)
        self.assertEqual(recovered.entries['2-3.4'].publication_failure, primary)

    def test_success_requires_a_fresh_postpublication_instance_scan(self):
        entry=self.waiting();self.host.processed=self.host.readable=True
        self.manager.tick()
        original=self.host.poll
        def replace_after_poll(job):
            result=original(job)
            self.host.devices[entry.device.port]=replace(entry.device,token='replacement-after-publish')
            return result
        with patch.object(self.host,'poll',side_effect=replace_after_poll): self.manager.tick()
        self.assertNotEqual(entry.phase,'active')
        self.assertEqual(len(self.publications()),1)

    def test_original_publish_error_survives_newly_incomplete_metadata(self):
        entry=self.waiting();self.host.processed=self.host.readable=True;self.host.publish_error=True
        self.manager.tick()
        original=self.host.poll
        def fail_scan_after_poll(job):
            result=original(job);self.host.scan_failure=True;return result
        with patch.object(self.host,'poll',side_effect=fail_scan_after_poll): self.manager.tick()
        self.assertEqual(entry.phase,'failed')
        self.assertIn('rc=1',entry.publication_failure)
        self.assertIn('rc=1',self.host.saved['recent_failures'][-1]['message'])

    def test_success_with_unknown_scan_retains_result_without_repeating_publish(self):
        entry=self.waiting();self.host.processed=self.host.readable=True
        self.manager.tick()
        original=self.host.poll
        def fail_scan_after_poll(job):
            result=original(job);self.host.scan_failure=True;return result
        with patch.object(self.host,'poll',side_effect=fail_scan_after_poll): self.manager.tick()
        self.assertEqual(entry.phase,'publishing_input')
        self.assertIsNotNone(entry.pending_status)
        self.host.scan_failure=False
        self.manager.tick()
        self.assertEqual(entry.phase,'active')
        self.assertEqual(len(self.publications()),1)

    def test_restart_pending_keeps_original_deadline_and_missing_receipt(self):
        entry = self.waiting()
        deadline = entry.publication_deadline
        self.host.now = 9
        self.manager = service.Manager(self.host, lambda: self.host.now)
        for _ in range(3): self.manager.tick()
        entry = self.manager.entries['2-3.4']
        self.assertEqual(entry.publication_deadline, deadline)
        self.host.now = deadline + 1
        self.manager.tick()
        self.assertEqual(entry.phase, 'failed')
        self.assertFalse(self.publications())

    def test_restart_after_uncertain_attempt_recovers_published_without_retry(self):
        self.waiting()
        self.host.processed = self.host.readable = True
        self.manager.tick()  # Kernel succeeded; manager has not read result.
        self.manager = service.Manager(self.host, lambda: self.host.now)
        for _ in range(3): self.manager.tick()
        self.assertEqual(self.manager.entries['2-3.4'].phase, 'active')
        self.assertEqual(len(self.publications()), 1)

    def test_restart_after_attempt_without_publication_never_repeats(self):
        self.waiting()
        self.host.processed = self.host.readable = True
        self.manager.tick()
        self.host.published = False
        self.manager = service.Manager(self.host, lambda: self.host.now)
        for _ in range(3): self.manager.tick()
        self.assertEqual(self.manager.entries['2-3.4'].phase, 'failed')
        self.assertEqual(len(self.publications()), 1)

    def test_bad_status_cannot_claim_success(self):
        d = device(pid='109c', driver='gs_native')
        tokens = service.boot_proof(proof(d))['tokens']
        for output in ('', 'input-publication {}', 'input-publication {"flags":true}'):
            with self.assertRaises((service.Unsafe, ValueError)):
                service.input_status(output, tokens)

    def test_host_pair_identity_and_source_resolve_without_device_access(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            root=Path(tmp); d=device(pid='109c',driver='gs_native')
            (root/'bus/usb/devices'/d.interface).mkdir(parents=True)
            host=service.Host('/never-run',root/'state',sysfs=root)
            meta={'instance':42,'uniq':f'gsn-{d.interface}-42'}
            self.assertEqual(host.input_binding(d,meta).uniq,meta['uniq'])
            with self.assertRaises(ReadinessError): host.input_binding(d,{**meta,'uniq':'gsn-other'})


class Receipts(unittest.TestCase):
    def backend(self):
        backend = object.__new__(ProcessedInputs)
        backend.devroot = Path('/test-owned-dev')
        backend.receipts = {}
        backend.uid = lambda seat: 1001
        backend.access = lambda node, uid: True
        return backend

    def test_creation_or_database_only_is_not_a_receipt(self):
        backend = self.backend()
        with patch('input_readiness.fingerprint', return_value=('life-1', 'gsn-1', Path('/fake'))):
            backend.record('/test/event1', 'add', False, 1)
            backend.record('/test/event1', 'add', True, 0)
            self.assertFalse(backend.receipts)
            backend.record('/test/event1', 'add', True, 2)
            self.assertEqual(backend.receipts['/test/event1'], ('life-1', 'seat0'))
            backend.record('/test/event1', 'remove', False, 3)
            self.assertFalse(backend.receipts)

    def test_partial_metadata_does_not_create_readiness(self):
        backend = self.backend()
        with patch('input_readiness.fingerprint', side_effect=FileNotFoundError):
            backend.record('/test/event1', 'add', True, 2)
        self.assertFalse(backend.receipts)

    def test_regular_file_or_symlink_cannot_impersonate_event_device(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            root = Path(tmp)
            event = root/'input42/event3'; event.mkdir(parents=True)
            (event/'dev').write_text('13:67')
            (event.parent/'uniq').write_text('gsn-test')
            node = root/'dev/input/event3'; node.parent.mkdir(parents=True); node.touch()
            with self.assertRaises(ReadinessError): fingerprint(event, root/'dev')
            node.unlink(); node.symlink_to(root/'input42/uniq')
            with self.assertRaises(ReadinessError): fingerprint(event, root/'dev')

    def test_access_check_is_unprivileged_child_and_does_not_open_device(self):
        from types import SimpleNamespace
        with patch('input_readiness.subprocess.run', return_value=SimpleNamespace(returncode=0)) as run:
            self.assertTrue(user_can_read(Path('/test-owned-dev/input/event1'), 1001))
            script=run.call_args.args[0][3]
            compile(script, '<bounded-access-check>', 'exec')
            self.assertEqual(run.call_args.args[0][-1], '1001')
            self.assertLess(script.index('os.setresgid'),script.index('os.setresuid'))
            self.assertLess(script.index('os.setresuid'),script.index('os.access'))
            self.assertEqual(run.call_args.kwargs['timeout'],1)
            self.assertIn('os.access', run.call_args.args[0][3])
            self.assertNotIn('open(', run.call_args.args[0][3])

    def test_exact_sensor_receipt_access_and_replacement(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            interface = Path(tmp)/'interface0'
            event = interface/'input/input42/event3'; event.mkdir(parents=True)
            binding = Binding('parent-life','native-life',str(interface),'gsn-test')
            backend = self.backend()
            path = str(event.resolve())
            value = ('sensor-life','gsn-test',Path('/test-owned-dev/input/event3'))
            with patch('input_readiness.fingerprint', return_value=value):
                self.assertFalse(backend.sensor(binding,'input42',100,8192).readable)
                backend.receipts[path] = ('old-life','seat0')
                self.assertFalse(backend.sensor(binding,'input42',100,8192).readable)
                backend.receipts[path] = ('sensor-life','seat0')
                sensor = backend.sensor(binding,'input42',100,8192)
                self.assertTrue(sensor.readable)
                self.assertEqual(sensor.processed_node_token,sensor.node_token)
                backend.access = lambda node,uid: False
                self.assertFalse(backend.sensor(binding,'input42',100,8192).readable)
                backend.uid = lambda seat: None
                self.assertTrue(backend.sensor(binding,'input42',100,8192).readable)
            with patch('input_readiness.fingerprint', side_effect=[value,('replacement','gsn-test',value[2])]):
                with self.assertRaises(ReadinessError): backend.sensor(binding,'input42',100,8192)

    def test_mismatched_uniq_never_uses_receipt_from_another_dongle(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            interface = Path(tmp)/'interface0'
            (interface/'input/input42/event3').mkdir(parents=True)
            binding = Binding('parent','instance',str(interface),'gsn-test')
            with patch('input_readiness.fingerprint', return_value=('life','gsn-other',Path('/fake'))):
                with self.assertRaises(ReadinessError): self.backend().sensor(binding,'input42',100,8192)

    def test_sensor_parent_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            root=Path(tmp); interface=root/'interface'; (interface/'input').mkdir(parents=True)
            other=root/'other'; other.mkdir()
            (interface/'input/input42').symlink_to(other)
            with self.assertRaises(ReadinessError):
                self.backend().sensor(Binding('parent','life',str(interface),'gsn-test'),'input42',100,8192)

    def test_monitor_uses_processed_channel_and_closes_on_setup_failure(self):
        from types import SimpleNamespace
        names = ('udev_new','udev_monitor_new_from_netlink',
                 'udev_monitor_filter_add_match_subsystem_devtype','udev_monitor_enable_receiving',
                 'udev_monitor_get_fd','udev_monitor_receive_device','udev_device_get_syspath',
                 'udev_device_get_action','udev_device_get_property_value','udev_device_get_seqnum',
                 'udev_device_unref','udev_monitor_unref','udev_unref')
        for fail in (False,True):
            lib=SimpleNamespace(**{name:Mock(return_value=0) for name in names})
            lib.udev_new.return_value=11
            lib.udev_monitor_new_from_netlink.return_value=12
            lib.udev_monitor_get_fd.return_value=23
            lib.udev_monitor_enable_receiving.return_value=-1 if fail else 0
            with patch('input_readiness.c.CDLL',return_value=lib), patch('input_readiness.os.set_blocking') as nonblock:
                if fail:
                    with self.assertRaises(ReadinessError): ProcessedInputs()
                else:
                    backend=ProcessedInputs(); nonblock.assert_called_once_with(23,False); backend.close()
                lib.udev_monitor_new_from_netlink.assert_called_once_with(11,b'udev')
                lib.udev_monitor_filter_add_match_subsystem_devtype.assert_called_once_with(12,b'input',None)
                lib.udev_monitor_unref.assert_called_once_with(12)
                lib.udev_unref.assert_called_once_with(11)

    def test_monitor_dispatch_retains_processed_properties_and_drains_without_opening(self):
        from types import SimpleNamespace
        backend=self.backend();backend.fd=23;backend.monitor=12
        backend.record=Mock()
        backend.lib=SimpleNamespace(
            udev_monitor_receive_device=lambda mon:7,
            udev_device_get_syspath=lambda dev:b'/test/event1',
            udev_device_get_action=lambda dev:b'add',
            udev_device_get_property_value=lambda dev,key:b'1' if key==b'ID_INPUT_ACCELEROMETER' else b'seat0',
            udev_device_get_seqnum=lambda dev:10,udev_device_unref=Mock())
        with patch('input_readiness.select.select',side_effect=[([23],[],[]),([],[],[])]):
            backend.drain()
        backend.record.assert_called_once_with('/test/event1','add',True,10,'seat0')
        backend.lib.udev_device_unref.assert_called_once_with(7)


class Client(unittest.TestCase):
    def test_actual_client_checked_publication_both_abis(self):
        build=ROOT/'build/input-publication-client';build.mkdir(exist_ok=True)
        for bits in (64,32):
            binary=build/f'client{bits}'
            subprocess.run(['clang',f'-m{bits}','-std=c11','-Wall','-Wextra','-Werror',
                            str(ROOT/'tests/input_publication_client_fake.c'),'-o',str(binary)],check=True)
            for command in ('input-info','publish-input'):
                for mode in ('ok','wrong-owner','publish-failure','bad-status','bad-strings','unsupported','busy'):
                    with self.subTest(bits=bits,command=command,mode=mode):
                        result=subprocess.run([str(binary),command,mode],capture_output=True,text=True,timeout=3)
                        expected=(0 if mode=='ok' or (command=='input-info' and mode=='publish-failure') else
                                  4 if mode=='busy' and command=='input-info' else 1)
                        self.assertEqual(result.returncode,expected,result.stderr)


if __name__ == '__main__':
    unittest.main()
