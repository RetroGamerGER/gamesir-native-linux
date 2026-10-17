#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic recorder tests. Never run a live /dev, /proc, /sys check."""
import ast
import copy
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_usb_capture', ROOT / 'tools/native/native_usb_capture.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def evidence():
    names = ('mnt', 'pid', 'net', 'ipc', 'uts', 'user')
    baseline = {'identity': {'synthetic': True}, 'ns': {key: key + ':host' for key in names}}
    rights = {key: '0000000000000000' for key in ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')}
    rights['NoNewPrivs'] = '1'
    ready = {'exe': '/usr/bin/dumpcap', 'monitor_fds': ['4'], 'raw_usb_absent': True,
             'mountinfo_unchanged': True, 'rights': rights,
             'namespaces': {key: key + ':guest' for key in names}, 'checked_monotonic_ns': 101_000_000_000}
    records = {'MEASUREMENT_B_PREFLIGHT_JSON': {'preflight_passed': True, 'rights': rights, 'ns': ready['namespaces']},
               'MEASUREMENT_B_DUMPCAP_JSON': ready,
               'STAGE4_IDENTITY_JSON': {'identity': baseline['identity'], 'host_mounts_and_namespaces_unchanged': True}}
    return baseline, records


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='synthetic-capture-')
        self.root = Path(self.tmp.name)
        self.parent = self.root / 'build/hardware-tests/test'
        self.parent.mkdir(parents=True, mode=0o700)
        self.metadata = {'uid': 0, 'gid': 0, 'mode': '0o755', 'sha256': '0' * 64,
                         'file_capability_xattr_hex': 'synthetic'}
        self.manifest = {'scope': capture.SCOPE, 'target': {'port': '8-6', 'busnum': '8', 'devnum': '29', 'devpath': '6'},
                         'sha256': {}, 'usb_capture': {'duration_seconds': 450, 'outer_timeout_seconds': 480,
                                                      'dumpcap_file_metadata': self.metadata}}
        self.root_patch = patch.object(capture, 'ROOT', self.root)
        self.root_patch.start()
        self.sources_patch = patch.object(capture, 'verify_sources', return_value={'synthetic': True})
        self.sources_patch.start()
        self.process_patch = patch.object(capture.subprocess, 'Popen', side_effect=AssertionError('Real process forbidden'))
        self.process_patch.start()
        self.run_patch = patch.object(capture.subprocess, 'run', side_effect=AssertionError('Live metadata forbidden'))
        self.run_patch.start()
        self.poll_patch = patch.object(capture.select, 'poll')
        self.poll_patch.start().return_value.poll.return_value = []
        self.close_patch = patch.object(capture.os, 'close')
        self.close_patch.start()

    def tearDown(self):
        self.close_patch.stop()
        self.poll_patch.stop()
        self.run_patch.stop()
        self.process_patch.stop()
        self.sources_patch.stop()
        self.root_patch.stop()
        self.tmp.cleanup()

    def obj(self):
        return capture.attach(self.manifest, self.parent)

    def active(self):
        obj = self.obj()
        obj.directory.mkdir(mode=0o700)
        obj.created_directory = True
        obj.started, obj.ready, obj.deadline = True, 100, 550
        obj.dumpcap_fd = 99
        obj.process, obj.observer = Mock(), Mock()
        obj.process.poll.return_value = obj.observer.poll.return_value = None
        for name in ('capture.log', 'usb-udev-events.log', 'udev-stderr.log', 'original-usbmon8.pcapng'):
            (obj.directory / name).write_bytes(b'')
        return obj

    def check(self, obj, remaining=330):
        with patch.object(capture.time, 'monotonic', return_value=110), \
             patch.object(capture.shutil, 'disk_usage', return_value=SimpleNamespace(free=5 * capture.GIB)):
            obj.check(remaining, 'synthetic-test')

    def test_attach_and_unstarted_finish_do_not_access_hardware(self):
        obj = self.obj()
        self.assertFalse(obj.directory.exists())
        result = obj.finish()
        self.assertFalse(result['passed'])
        self.assertEqual(obj.finish(), result)
        self.assertFalse(obj.directory.exists())

    def test_wrong_scope(self):
        self.manifest['scope'] = 'old-deadband-run'
        with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_wrong_bus_or_port(self):
        for key, value in (('busnum', '7'), ('port', '8-7'), ('devnum', '128')):
            old = self.manifest['target'][key]
            self.manifest['target'][key] = value
            with self.assertRaises(capture.CaptureHalt): self.obj()
            self.manifest['target'][key] = old

    def test_missing_provenance(self):
        del self.manifest['usb_capture']['dumpcap_file_metadata']['sha256']
        with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_pinned_package_group_and_owner_execute_mode_accepted(self):
        self.metadata.update(gid=150, mode='0o754')
        obj = self.obj()
        self.assertEqual(obj.manifest['usb_capture']['dumpcap_file_metadata'], self.metadata)
        self.assertFalse(obj.directory.exists())

    def test_dumpcap_owner_must_be_integer_root(self):
        for uid in (False, True, -1, 1000, '0', 0.0, None):
            with self.subTest(uid=uid):
                self.metadata['uid'] = uid
                with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_dumpcap_group_must_be_valid_integer_gid(self):
        for gid in (False, True, -1, 150.0, '150', None, 2**32 - 1, 2**32):
            with self.subTest(gid=gid):
                self.metadata['gid'] = gid
                with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_no_overwrite_or_symlink(self):
        (self.parent / 'usb-capture').symlink_to(self.root)
        with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_private_directory_required(self):
        self.parent.chmod(0o755)
        with self.assertRaises(capture.CaptureHalt): self.obj()

    def test_start_requires_root_without_starting_process(self):
        obj = self.obj()
        with patch.object(capture.os, 'geteuid', return_value=1000):
            with self.assertRaises(capture.CaptureHalt): obj.start()
        self.assertFalse(obj.directory.exists())

    def test_source_change_before_start(self):
        obj = self.obj()
        with patch.object(capture.os, 'geteuid', return_value=0), \
             patch.object(capture, 'verify_sources', return_value={'changed': True}):
            with self.assertRaises(capture.CaptureHalt): obj.start()

    def test_simulated_start_uses_only_reviewed_sandbox_chain(self):
        obj = self.obj()
        obj.source_hashes = {'tools/native/usb_capture/' + name:
            capture.digest(ROOT / 'tools/native/usb_capture' / name) for name in capture.ASSET_NAMES}
        host, records = evidence()
        host.pop('identity')
        observer, process = Mock(), Mock()
        observer.poll.return_value = process.poll.return_value = None
        process.pid = 123
        supervisor = {'pid': 123, 'starttime': '100'}
        records['MEASUREMENT_B_SUPERVISOR_JSON'] = supervisor
        with patch.object(capture.os, 'geteuid', return_value=0), \
             patch.object(capture.os, 'chown'), \
             patch.object(capture.os, 'pidfd_open', return_value=99), \
             patch.object(capture, 'verify_sources', return_value=obj.source_hashes), \
             patch.object(capture, 'dumpcap_metadata', return_value=self.metadata), \
             patch.object(capture.shutil, 'disk_usage', return_value=SimpleNamespace(free=5*capture.GIB)), \
             patch.object(obj, '_metadata', side_effect=[host, {'synthetic': True}]), \
             patch.object(capture.subprocess, 'Popen', side_effect=[observer, process]) as spawn, \
             patch.object(capture.time, 'monotonic', return_value=102), \
             patch.object(capture, 'marker_records', return_value=records), \
             patch.object(obj, '_supervisor_identity', return_value=supervisor), \
             patch.object(obj, '_dumpcap_identity', return_value={'pid': 127, 'starttime': '101'}):
            records['MEASUREMENT_B_DUMPCAP_JSON']['checked_monotonic_ns'] = 102*10**9
            obj.start()
        argv = spawn.call_args_list[-1].args[0]
        self.assertEqual(argv[:4], ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2s', '480s'])
        self.assertIn('/usr/bin/unshare', argv)
        self.assertNotIn('/usr/bin/dumpcap', argv)  # present only inside reviewed guest source
        self.assertEqual(argv[-2], (ROOT / 'tools/native/usb_capture/guest-check.py').read_text())
        self.assertEqual(stat.S_IMODE((obj.directory / 'original-usbmon8.pcapng').stat().st_mode), 0o600)
        for stream in obj.streams:
            if not stream.closed: stream.close()

    def test_dumpcap_provenance_change_blocks_spawn(self):
        self.metadata.update(gid=150, mode='0o754')
        obj = self.obj()
        obj.source_hashes = {'tools/native/usb_capture/' + name:
            capture.digest(ROOT / 'tools/native/usb_capture' / name) for name in capture.ASSET_NAMES}
        for changed in ({'uid': 1000}, {'gid': 0}, {'mode': '0o755'}):
            with self.subTest(changed=changed), \
                 patch.object(capture.os, 'geteuid', return_value=0), \
                 patch.object(capture, 'verify_sources', return_value=obj.source_hashes), \
                 patch.object(capture, 'dumpcap_metadata', return_value=dict(self.metadata, **changed)):
                obj.started = False  # Independent synthetic start scenario, no process exists.
                with self.assertRaises(capture.CaptureHalt): obj.start()
        self.assertFalse(obj.directory.exists())

    def test_descendant_namespace_and_start_identity_with_synthetic_proc(self):
        obj = self.active()
        obj.process.pid = 123
        obj.supervisor = {'pid': 123, 'starttime': '100'}
        obj.capture_namespaces = {name: name + ':guest' for name in ('mnt', 'pid', 'net', 'ipc', 'uts', 'user')}
        texts = {'/proc/123/task/123/children': '127', '/proc/127/task/127/children': '',
                 '/proc/127/stat': '127 (dumpcap) ' + ' '.join(['0']*19 + ['101'])}
        links = {'/proc/123/exe': '/usr/bin/timeout', '/proc/127/exe': '/usr/bin/dumpcap'}
        links.update({'/proc/127/ns/' + key: value for key, value in obj.capture_namespaces.items()})
        class FakePath(str):
            def __truediv__(self, part): return FakePath(str(self) + '/' + str(part))
            def read_text(self): return texts[str(self)]
        with patch.object(capture, 'Path', FakePath), \
             patch.object(obj, '_supervisor_identity', return_value=obj.supervisor), \
             patch.object(capture.os, 'readlink', side_effect=lambda path: links[str(path)]):
            self.assertEqual(obj._dumpcap_identity(), {'pid': 127, 'starttime': '101'})
            links['/proc/127/ns/net'] = 'net:host'
            with self.assertRaises(capture.CaptureHalt): obj._dumpcap_identity()

    def test_ready_success_and_reject_absent_marker(self):
        baseline, records = evidence()
        self.assertEqual(capture.validate_ready(records, baseline, 100, 102), 101)
        del records['MEASUREMENT_B_DUMPCAP_JSON']
        with self.assertRaises(capture.CaptureHalt): capture.validate_ready(records, baseline, 100, 102)

    def test_stale_or_future_readiness(self):
        baseline, records = evidence()
        for stamp in (99, 103, 90):
            records['MEASUREMENT_B_DUMPCAP_JSON']['checked_monotonic_ns'] = stamp * 10**9
            with self.assertRaises(capture.CaptureHalt): capture.validate_ready(records, baseline, 100, 102)

    def test_each_capability_and_namespace_fails_closed(self):
        for key in ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb'):
            baseline, records = evidence()
            records['MEASUREMENT_B_DUMPCAP_JSON']['rights'][key] = '1'
            with self.assertRaises(capture.CaptureHalt): capture.validate_ready(records, baseline, 100, 102)
        for key in ('mnt', 'pid', 'net', 'ipc', 'uts', 'user'):
            baseline, records = evidence()
            records['MEASUREMENT_B_DUMPCAP_JSON']['namespaces'][key] = baseline['ns'][key]
            with self.assertRaises(capture.CaptureHalt): capture.validate_ready(records, baseline, 100, 102)

    def test_raw_usb_visibility_blocks_readiness(self):
        baseline, records = evidence()
        records['MEASUREMENT_B_DUMPCAP_JSON']['raw_usb_absent'] = False
        with self.assertRaises(capture.CaptureHalt): capture.validate_ready(records, baseline, 100, 102)

    def test_marker_parser_rejects_duplicate_and_ignores_partial(self):
        p = self.root / 'audit'
        p.write_text('MEASUREMENT_B_DUMPCAP_JSON {"ready":true}\nPARTIAL')
        self.assertEqual(capture.marker_records(p), {'MEASUREMENT_B_DUMPCAP_JSON': {'ready': True}})
        p.write_text(p.read_text() + '\nMEASUREMENT_B_DUMPCAP_JSON {}\n')
        with self.assertRaises(capture.CaptureHalt): capture.marker_records(p)

    def test_budget_checked_before_every_action(self):
        obj = self.active()
        self.check(obj, 440)
        for value in (440.001, float('nan'), float('inf'), -1):
            with self.assertRaises(capture.CaptureHalt): self.check(obj, value)

    def test_early_recorder_or_epoch_exit(self):
        obj = self.active()
        obj.process.poll.return_value = 0
        with self.assertRaises(capture.CaptureHalt): self.check(obj)
        obj.process.poll.return_value = None
        obj.observer.poll.return_value = 0
        with self.assertRaises(capture.CaptureHalt): self.check(obj)

    def test_disk_and_observer_errors(self):
        obj = self.active()
        with patch.object(capture.time, 'monotonic', return_value=110), \
             patch.object(capture.shutil, 'disk_usage', return_value=SimpleNamespace(free=capture.GIB - 1)):
            with self.assertRaises(capture.CaptureHalt): obj.check(330, 'disk')
        (obj.directory / 'udev-stderr.log').write_text('synthetic error')
        with self.assertRaises(capture.CaptureHalt): self.check(obj)

    def test_signal_exact_pidfd_only(self):
        obj = self.active()
        obj.process.pid = 123
        obj.supervisor = {'pid': 123, 'starttime': '100'}
        obj.dumpcap = {'pid': 127, 'starttime': '101'}
        with patch.object(obj, '_supervisor_identity', return_value=obj.supervisor), \
             patch.object(obj, '_dumpcap_identity', return_value=obj.dumpcap), \
             patch.object(capture.signal, 'pidfd_send_signal') as send:
            obj._stop()
            send.assert_called_once_with(99, signal.SIGINT)
            obj.process.send_signal.assert_not_called()

    def test_missing_pidfd_during_start_aborts_owned_supervisor(self):
        obj = self.active()
        obj.dumpcap_fd = None
        obj.dumpcap = None  # Assigned only after successful pidfd_open and validation.
        obj.supervisor = {'pid': 123, 'starttime': '100'}
        with patch.object(obj, '_supervisor_identity', return_value=obj.supervisor):
            obj._stop()
        obj.process.send_signal.assert_called_once_with(signal.SIGINT)

    def test_directory_without_started_recorder_cannot_pass(self):
        obj = self.obj()
        obj.directory.mkdir(mode=0o700)
        result = obj.finish()
        self.assertFalse(result['passed'])
        self.assertNotIn('original_sha256', result)

    def test_directory_created_by_someone_else_remains_untouched(self):
        obj = self.obj()
        obj.directory.mkdir(mode=0o700)
        marker = obj.directory / 'untouched.txt'
        marker.write_text('preserved')
        self.assertFalse(obj.finish()['passed'])
        self.assertEqual(list(obj.directory.iterdir()), [marker])

    def test_unreaped_observer_prevents_manifest(self):
        obj = self.active()
        obj.process.poll.return_value = 0
        obj.process.returncode = 0
        obj.observer.wait.side_effect = capture.subprocess.TimeoutExpired('synthetic-observer', 3)
        (obj.directory / 'capture.log').write_text('MEASUREMENT_B_RESULT_JSON {"passed":true,"dumpcap_reaped":true}\n')
        (obj.directory / 'original-usbmon8.pcapng').write_bytes(b'\x0a\x0d\x0d\x0asynthetic')
        result = obj._finalize(tail=False)
        self.assertFalse(result['passed'])
        self.assertIn('observer_stop_error', result)
        self.assertFalse((obj.directory / 'SHA256SUMS').exists())

    def test_corrupted_audit_does_not_prevent_owned_stop(self):
        obj = self.active()
        obj.supervisor, obj.dumpcap = {'pid': 123, 'starttime': '100'}, {'pid': 127, 'starttime': '101'}
        (obj.directory / 'capture.log').write_text('MEASUREMENT_B_RESULT_JSON not-json\n')
        with patch.object(obj, '_supervisor_identity', return_value=obj.supervisor), \
             patch.object(obj, '_dumpcap_identity', return_value=obj.dumpcap), \
             patch.object(capture.signal, 'pidfd_send_signal') as send:
            obj._stop()
            obj._stop()
            send.assert_called_once_with(99, signal.SIGINT)

    def test_dumpcap_early_exit_detected_even_if_supervisor_alive(self):
        obj = self.active()
        with patch.object(capture.select, 'poll') as poll:
            poll.return_value.poll.return_value = [(99, 1)]
            with self.assertRaises(capture.CaptureHalt): self.check(obj)

    def test_reused_pid_never_signalled(self):
        obj = self.active()
        obj.supervisor, obj.dumpcap = {'pid': 123, 'starttime': '100'}, {'pid': 127, 'starttime': '101'}
        with patch.object(obj, '_supervisor_identity', return_value=obj.supervisor), \
             patch.object(obj, '_dumpcap_identity', return_value={'pid': 127, 'starttime': '999'}), \
             patch.object(capture.os, 'pidfd_open', return_value=99), \
             patch.object(capture.signal, 'pidfd_send_signal') as send, \
             patch.object(capture.os, 'close'):
            with self.assertRaises(capture.CaptureHalt): obj._stop()
            send.assert_not_called()

    def test_final_audit_failure_preserves_raw_without_false_checksum(self):
        obj = self.active()
        obj.process.poll.return_value = 0
        obj.process.returncode = 0
        obj.observer.poll.return_value = 0
        raw = obj.directory / 'original-usbmon8.pcapng'
        raw.write_bytes(b'\x0a\x0d\x0d\x0asynthetic')
        result = obj._finalize(tail=False)
        self.assertFalse(result['passed'])
        self.assertTrue(raw.exists())
        self.assertNotIn('original_sha256', result)
        self.assertFalse((obj.directory / 'SHA256SUMS').exists())

    def test_final_success_hashes_private_evidence(self):
        obj = self.active()
        obj.process.poll.return_value = 0
        obj.process.returncode = 0
        obj.observer.poll.return_value = 0
        obj.baseline = {'identity': {}, 'target': {}, 'synthetic_host': True}
        (obj.directory / 'capture.log').write_text('MEASUREMENT_B_RESULT_JSON {"passed":true,"dumpcap_reaped":true}\n')
        raw = obj.directory / 'original-usbmon8.pcapng'
        raw.write_bytes(b'\x0a\x0d\x0d\x0asynthetic')
        with patch.object(obj, '_metadata', return_value={'synthetic_host': True}):
            result = obj._finalize(tail=False)
        self.assertTrue(result['passed'])
        self.assertEqual(result['original_sha256'], capture.digest(raw))
        self.assertTrue(result['checksum_manifest_verified'])
        self.assertEqual(result['capture_outcome_sha256'], capture.digest(obj.directory / 'capture-outcome.json'))
        self.assertTrue((obj.directory / 'SHA256SUMS').is_file())
        self.assertEqual(obj.finish(), result)
        self.assertEqual(stat.S_IMODE((obj.directory / 'capture-outcome.json').stat().st_mode), 0o600)

    def test_checksum_failure_never_persists_success(self):
        obj = self.active()
        obj.process.poll.return_value = 0
        obj.process.returncode = 0
        obj.observer.poll.return_value = 0
        (obj.directory / 'capture.log').write_text('MEASUREMENT_B_RESULT_JSON {"passed":true,"dumpcap_reaped":true}\n')
        (obj.directory / 'original-usbmon8.pcapng').write_bytes(b'\x0a\x0d\x0d\x0asynthetic')
        real_digest = capture.digest
        seen = set()
        def differing_digest(path):
            # Original is read once before the manifest; corrupt log's verify.
            if path.name == 'capture.log':
                if path in seen: return '0' * 64
                seen.add(path)
            return real_digest(path)
        with patch.object(capture, 'digest', side_effect=differing_digest):
            result = obj._finalize(tail=False)
        self.assertFalse(result['passed'])
        persisted = json.loads((obj.directory / 'capture-outcome.json').read_text())
        self.assertFalse(persisted['passed'])
        self.assertFalse(persisted['checksum_manifest_verified'])

    def test_assets_are_syntax_only_and_pinned_to_original_guards(self):
        assets = ROOT / 'tools/native/usb_capture'
        provenance = json.loads((assets / 'PROVENANCE.json').read_text())
        license_comment = '# SPDX-License-Identifier: GPL-2.0-only\n'
        import hashlib
        for name in capture.ASSET_NAMES:
            self.assertTrue((assets / name).read_text().startswith(license_comment))
            self.assertEqual(capture.digest(assets / name), provenance['files'][name]['current_source_sha256'])
        for name in ('setup.sh', 'state-check.py'):
            original = (assets / name).read_text().removeprefix(license_comment)
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), provenance['files'][name]['validated_source_sha256'])
        for path in assets.glob('*.py'):
            ast.parse(path.read_text(), filename=str(path))  # never exec hardware guards
        # The source now has a separate, offline-only passive profile. Keep
        # the actual historical hashes rather than pretending a text rewrite
        # reconstructs that previously validated guest. Current behavior is
        # checked by both legacy synthetic tests and the passive profile suite.
        self.assertEqual(provenance['files']['guest-check.py']['validated_source_sha256'],
                         '105216872466430161aac6ae01e2399b54a1edd37149effcfac1cb721004e5db')
        self.assertEqual(provenance['files']['guest-check.py']['pre_passive_profile_source_sha256'],
                         'd09a529639c1ec4df84f8ba779f33480983810e8a5ae6b649b6c806dced6b7b1')
        self.assertEqual(provenance['files']['identity-check.py']['pre_passive_profile_source_sha256'],
                         'd768288ff45675b91c7c9676c120bb30c6afbf54d11791e187b50e7c3bc9369a')
        self.assertFalse(provenance['profile_validation']['passive_hardware_validated'])
        self.assertFalse(provenance['profile_validation']['setup_mount_and_state_guards_changed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
