#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""No live root/DB/device access. Injected boundaries and temporary ALPM root."""
from dataclasses import replace
import hashlib
import io
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import tarfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import BackendError, Catalog, COMPONENTS
from backend import Outcome, Session, TransactionPreview, build_plan
from rehearsal import OfflinePort, fixture_catalog, KERNEL, VERSION
from package_execution import DEPLOYMENT_TRUST, ExecutionTrust, InstalledReview, PackageExecutor
from package_wire import PackageMessage, parse_message, receipt, parse_receipt, encode, decode
from package_alpm import Alpm
from package_client import ExecutionSession, ExecutionTransactions, PackageTransport, FILES


def trust_records(catalog):
    return tuple(InstalledReview(r.component, r.version, r.guards) for r in catalog.records)


class Adapter(OfflinePort):
    def __init__(self):
        super().__init__('success', lambda: 100)
        self.calls, self.guard, self.closed = [], False, False
        self.extra = False
        self.fail_close = False

    def acquire(self):
        self.calls.append('lock')

    def observe(self):
        self.calls.append('observe')
        return super().observe()

    def attest_core_guard(self, record):
        self.calls.append('guard')
        self.guard = True

    def prepare(self, plan):
        self.calls.append('prepare')
        return TransactionPreview(tuple(sorted(plan.packages)) + (('other',) if self.extra else ()),
                                  tuple(sorted((a.package, a.review.version) for a in plan.artifacts)),
                                  other_removals=tuple(sorted(plan.packages))
                                  if plan.request.operation == 'remove' else (),
                                  guard_verified=self.guard)

    def commit(self):
        return super().commit(self.plan)

    def close(self):
        self.closed = True
        self.calls.append('close')
        if self.fail_close:
            raise RuntimeError('do not overwrite original error')


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.blobs = fixture_catalog()
        self.trust = ExecutionTrust(self.catalog, trust_records(self.catalog))
        self.adapter = Adapter()

    def plan(self, operation='install', components=('core',)):
        from backend import Request
        request = Request.parse({'schema': 1, 'operation': operation, 'components': list(components)})
        plan = build_plan(request, self.adapter.host,
                          {c: self.blobs[c] for c in components} if operation == 'install' else {},
                          catalog=self.catalog, now=100, purpose='packages')
        self.adapter.plan = plan
        return plan

    def run_plan(self, plan=None, trust=None):
        executor = PackageExecutor(trust or self.trust, self.adapter, clock=lambda: 100)
        result = executor.run(plan or self.plan())
        self.assertIs(result, executor.run(self.adapter.plan))
        self.assertTrue(self.adapter.closed)
        return result, executor

    def test_install_and_remove_all_components_only_once_under_one_lock(self):
        result, _ = self.run_plan(self.plan(components=tuple(COMPONENTS)))
        self.assertEqual(result.state, 'verified_success')
        self.assertEqual(self.adapter.calls, ['lock', 'observe', 'prepare', 'observe', 'commit', 'verify', 'close'])
        self.assertEqual(self.adapter.hook_calls if hasattr(self.adapter, 'hook_calls') else 0, 0)
        self.adapter.closed = False
        self.adapter.calls.clear()
        result, _ = self.run_plan(self.plan('remove', tuple(COMPONENTS)))
        self.assertEqual(result.state, 'verified_success')
        self.assertIn('guard', self.adapter.calls)
        self.assertEqual(self.adapter.host.installed, (('unrelated-controller', '1.0-1'),))

    def test_empty_deployment_catalog_never_installs_client_approved_bytes(self):
        self.assertEqual(DEPLOYMENT_TRUST.catalog.records, ())
        self.assertEqual(DEPLOYMENT_TRUST.installed, ())
        result, _ = self.run_plan(trust=DEPLOYMENT_TRUST)
        self.assertEqual(result.error, 'no_reviewed_binary')
        self.assertNotIn('prepare', self.adapter.calls)
        self.assertNotIn('commit', self.adapter.calls)

    def test_changed_host_or_expiry_stops_before_commit(self):
        plan = self.plan()
        self.adapter.host = replace(self.adapter.host, native_loaded=True)
        result, _ = self.run_plan(plan)
        self.assertEqual(result.error, 'host_changed')
        self.assertNotIn('commit', self.adapter.calls)
        executor = PackageExecutor(self.trust, Adapter(), clock=lambda: 221)
        self.assertEqual(executor.run(plan).error, 'plan_expired')

    def test_new_root_observation_after_password_wait_does_not_rewind_time_or_extend_plan(self):
        plan = self.plan()
        self.adapter.clock = lambda: 150
        executor = PackageExecutor(self.trust, self.adapter, clock=lambda: 150)
        result = executor.run(plan)
        self.assertEqual(result.state, 'verified_success')
        self.assertEqual(plan.expires_at, 220)
        self.assertEqual(self.adapter.calls.count('commit'), 1)

    def test_changed_prepared_transaction_and_unknown_installed_version_stop(self):
        self.adapter.extra = True
        result, _ = self.run_plan()
        self.assertEqual(result.error, 'unexpected_package_transaction')
        self.assertNotIn('commit', self.adapter.calls)
        self.adapter = Adapter()
        self.adapter.host = replace(self.adapter.host, installed=((COMPONENTS['core'][0], '9.0-1'),))
        result, _ = self.run_plan(self.plan('remove'))
        self.assertEqual(result.error, 'unreviewed_installed_version')
        self.assertNotIn('prepare', self.adapter.calls)

    def test_failed_commit_keeps_first_error_and_no_retry_or_activation(self):
        self.adapter.fail_close = True
        self.adapter.commit = lambda: (_ for _ in ()).throw(BackendError('original_hook_failure'))
        result, executor = self.run_plan()
        self.assertEqual(result.error, 'original_hook_failure')
        self.assertTrue(result.changes_possible)
        self.assertEqual(executor.first_failure.code, 'original_hook_failure')

    def test_unverified_postcheck_and_lock_release_never_report_success(self):
        self.adapter.verify = lambda plan: None
        result, _ = self.run_plan()
        self.assertEqual(result.error, 'verification_unavailable')
        self.assertTrue(result.changes_possible)
        self.adapter = Adapter(); self.adapter.fail_close = True
        result, _ = self.run_plan()
        self.assertEqual(result.error, 'package_lock_release_unverified')
        self.assertEqual(result.state, 'uncertain')

    def test_guard_block_stops_before_package_files_or_alternative_cleanup(self):
        self.adapter.host = replace(self.adapter.host, installed=((COMPONENTS['core'][0], VERSION),))
        self.adapter.attest_core_guard = lambda _: (_ for _ in ()).throw(BackendError('installed_core_guard_overridden'))
        result, _ = self.run_plan(self.plan('remove'))
        self.assertEqual(result.error, 'installed_core_guard_overridden')
        self.assertNotIn('prepare', self.adapter.calls)

    def test_wire_roundtrip_and_correlated_outcome(self):
        message = PackageMessage.create(self.plan(components=tuple(COMPONENTS)))
        stream = io.BytesIO(b''.join(message.chunks()))
        parsed = parse_message(stream.read, self.trust)
        self.assertEqual(parsed, message)
        self.assertEqual(stream.read(), b'')
        outcome = Outcome('verified_success', 'privileged_postcheck', changes_possible=True)
        self.assertEqual(parse_receipt(receipt(parsed, outcome), message), outcome)
        other = PackageMessage.create(message.plan)
        with self.assertRaises(BackendError):
            parse_receipt(receipt(parsed, outcome), other)

    def test_wire_rejects_paths_duplicate_fields_untrusted_catalog_and_truncation(self):
        data = b''.join(PackageMessage.create(self.plan()).chunks())
        size = struct.unpack('!I', data[:4])[0]
        header, payload = decode(data[4:4+size]), data[4+size:]
        for change in ({'command': 'pacman'}, {'path': '/tmp/package'}, {'schema': True},
                       {'artifacts': [{'component': 'core', 'sha256': '0'*64, 'size': 8}]}):
            changed = encode({**header, **change})
            stream = io.BytesIO(struct.pack('!I', len(changed)) + changed + payload)
            with self.assertRaises((BackendError, ValueError)):
                parse_message(stream.read, self.trust)
        with self.assertRaises(BackendError):
            parse_message(io.BytesIO(data).read, DEPLOYMENT_TRUST)
        with self.assertRaises(BackendError):
            decode(b'{"schema":2,"schema":2}')
        with self.assertRaises(BackendError):
            parse_message(io.BytesIO(data[:-1]).read, self.trust)

    def test_no_execution_constructed_on_import_or_normal_launch(self):
        with patch('subprocess.Popen', side_effect=AssertionError('no live processes')):
            import package_helper
            import package_host
        self.assertNotIn('pkexec', Path(ROOT / 'tools/control_center/main.py').read_text())

    def test_missing_transport_cancel_and_permission_probe_cannot_install(self):
        plan = self.plan()
        session = ExecutionSession(plan, None, lambda: 100)
        self.assertEqual(session.run().error, 'package_transport_disabled')
        class Transport:
            def invoke(self, message):
                return self.result
        transport = Transport()
        for code, data, state in ((126, b'', 'cancelled'), (127, b'', 'blocked'),
                                  (0, b'{"state":"authorized_only","executed":false}', 'uncertain'),
                                  (None, b'', 'uncertain'), (2, b'', 'uncertain')):
            transport.result = code, data
            session = ExecutionSession(plan, transport, lambda: 100)
            outcome = session.run()
            self.assertEqual(outcome.state, state)
            self.assertIs(session.run(), outcome)
        self.assertNotIn('commit', self.adapter.calls)

    def test_receipt_refuses_false_success_and_wrong_correlation(self):
        message = PackageMessage.create(self.plan())
        for result in (Outcome('verified_success', 'privileged_postcheck'),
                       Outcome('blocked', 'package_transaction', 'bad', True),
                       Outcome('failed', 'privileged_postcheck', 'bad', False)):
            with self.assertRaises(BackendError):
                parse_receipt(receipt(message, result), message)

    def test_explicit_gui_coordinator_disabled_until_transport_supplied(self):
        tx = ExecutionTransactions(self.adapter, self.catalog, self.blobs, lambda: 100)
        self.assertFalse(tx.request('install'))
        self.assertEqual(tx.error, 'package_transport_disabled')
        self.assertIsNone(tx.begin())
        with self.assertRaises(BackendError):
            PackageTransport(())

    def test_independent_privilege_action_no_auth_cache_or_gui_environment(self):
        from package_wire import ACTION, EXECUTOR
        tree = ET.parse(ROOT / 'packaging/control-center' / (ACTION + '.policy'))
        action = tree.find('action')
        self.assertEqual(action.attrib['id'], ACTION)
        self.assertEqual(action.find('annotate').text, EXECUTOR)
        self.assertEqual(action.find('defaults/allow_active').text, 'auth_admin')
        self.assertEqual(action.find('defaults/allow_any').text, 'no')
        self.assertEqual(action.find('defaults/allow_inactive').text, 'no')
        self.assertIn('alpm_bridge.so', ''.join(FILES))
        self.assertNotIn('authorize', EXECUTOR)

    def test_transport_uses_fixed_entry_and_bounded_stream_no_kill_or_shell(self):
        from package_wire import ARGV
        from privilege.transport import BoundedRunner
        from unittest.mock import Mock
        pins = tuple((p, 'a' * 64) for p in FILES)
        auditor = Mock()
        message = PackageMessage.create(self.plan())
        expected = Outcome('verified_success', 'privileged_postcheck', changes_possible=True)
        reply = receipt(message, expected)
        # Harmless same-user fixture; real pkexec is always intercepted.
        original = subprocess.Popen
        script = 'import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(' + repr(reply) + ')'
        def launch(argv, **kwargs):
            self.assertEqual(argv, ARGV)
            self.assertEqual(kwargs['env'], {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
            self.assertFalse(kwargs['shell'])
            return original([sys.executable, '-IBS', '-c', script], **kwargs)
        with patch('package_client.subprocess.Popen', side_effect=launch):
            code, output = PackageTransport(pins, auditor=auditor).invoke(message)
        self.assertEqual(code, 0)
        self.assertEqual(parse_receipt(output, message), expected)

    def test_transport_timeout_retains_unknown_and_reaps_without_kill(self):
        from unittest.mock import Mock
        original = subprocess.Popen
        children = []
        def launch(argv, **kwargs):
            child = original([sys.executable, '-IBS', '-c',
                              'import sys,time; sys.stdin.buffer.read(); time.sleep(1.1)'], **kwargs)
            children.append(child)
            return child
        pins = tuple((p, 'a' * 64) for p in FILES)
        with patch('package_client.subprocess.Popen', side_effect=launch):
            code, data = PackageTransport(pins, auditor=Mock(), deadline=1).invoke(PackageMessage.create(self.plan()))
        self.assertIsNone(code)
        self.assertEqual(data, b'')
        children[0].wait(timeout=3)

    def test_input_requires_eof_and_detects_truncation_without_a_helper_launch(self):
        from package_helper import Input
        read_fd, write_fd = os.pipe()
        try:
            os.write(write_fd, b'ab'); os.close(write_fd)
            source = Input(read_fd)
            self.assertEqual(source.exact(2), b'ab')
            source.eof()
            with self.assertRaises(BackendError): source.exact(1)
        finally:
            os.close(read_fd)

    def test_installed_guard_trust_is_strict_and_cannot_name_arbitrary_files(self):
        for row in (InstalledReview('core', VERSION), InstalledReview('core', VERSION, (('/tmp/file', 'a'*64),)),
                    InstalledReview('core', True), InstalledReview('steam', VERSION, (('x', 'y'),))):
            with self.assertRaises(BackendError): ExecutionTrust(self.catalog, (row,))

    def test_rehearsal_plan_cannot_enter_package_executor(self):
        plan = replace(self.plan(), purpose='offline_rehearsal')
        executor = PackageExecutor(self.trust, self.adapter, clock=lambda: 100)
        self.assertEqual(executor.run(plan).error, 'package_plan_required')
        self.assertNotIn('lock', self.adapter.calls)

    def test_system_postcheck_uses_dkms_package_name_and_no_mutating_commands(self):
        import package_host as host
        from unittest.mock import Mock
        adapter = host.SystemPackages.__new__(host.SystemPackages)
        adapter.alpm = Mock()
        adapter.alpm.rows.return_value = ((COMPONENTS['core'][0], VERSION),)
        adapter.service = lambda: ({'ActiveState': 'inactive', 'SubState': 'dead',
                                   'MainPID': '0', 'ControlPID': '0'}, False)
        calls = []
        def command(argv):
            calls.append(argv)
            if argv[0] == '/usr/bin/dkms':
                self.assertEqual(argv, ['/usr/bin/dkms', 'status', '-m', 'gamesir-native'])
                return f'gamesir-native/{VERSION.rsplit("-", 1)[0]}, {KERNEL}, x86_64: installed'
            if 'version' in argv:
                return VERSION.rsplit('-', 1)[0]
            return KERNEL + ' SMP preempt'
        with patch.object(host, 'command', side_effect=command), patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'glob', return_value=iter(())):
            check = adapter.verify(self.plan())
        self.assertTrue(check.dkms_installed)
        self.assertEqual(check.dkms_kernel, KERNEL)
        self.assertEqual(len(calls), 3)

    def test_guard_override_blocks_and_never_executes_cleanup(self):
        import package_host as host
        from unittest.mock import Mock
        adapter = host.SystemPackages.__new__(host.SystemPackages)
        adapter.hookdirs = ['/usr/share/libalpm/hooks', '/etc/pacman.d/hooks']
        adapter.guard_verified = False
        row = trust_records(self.catalog)[0]
        # Hashes here refer to synthetic marker bytes, never installed files.
        class File:
            name = '60-gamesir-native-release.hook'
            def read_bytes(self): return b'OFFLINE FIXTURE ONLY: NOT EXECUTABLE\n'
            def __str__(self): return '/fixed/guard'
        with patch.object(host, 'protected', return_value=File()), \
                patch.object(host, 'command', return_value=COMPONENTS['core'][0]), \
                patch.object(host.os.path, 'lexists', return_value=True):
            with self.assertRaises(BackendError) as error:
                adapter.attest_core_guard(row)
        self.assertEqual(error.exception.code, 'installed_core_guard_overridden')
        self.assertFalse(adapter.guard_verified)


class SandboxAlpm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/usr/include/alpm.h').is_file() or not Path('/usr/bin/cc').is_file():
            raise unittest.SkipTest('Optional local libalpm development files absent')
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        cls.library = Path(cls.temp.name) / 'alpm_bridge.so'
        subprocess.run(['/usr/bin/cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fPIC', '-shared',
                        '-Wl,-z,relro,-z,now', str(ROOT / 'tools/control_center/alpm_bridge.c'),
                        '-o', str(cls.library), '-lalpm'], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_library_synthetic_install_remove_and_lock_competition(self):
        # All paths, packages and hooks belong to a new temporary root. No host
        # DB/config/hook is passed to libalpm. No root or sudo process exists.
        with tempfile.TemporaryDirectory(dir=self.temp.name) as folder:
            root = Path(folder)
            database, hooks, cache = (root / p for p in ('db', 'hooks', 'cache'))
            for path in (database, hooks, cache): path.mkdir()
            first = Alpm(self.library, str(root) + '/', database, [hooks])
            second = Alpm(self.library, str(root) + '/', database, [hooks])
            try:
                first.acquire()
                with self.assertRaises(BackendError): second.acquire()
                self.assertTrue((database / 'db.lck').exists())
                catalog, blobs = fixture_catalog()
                original = blobs['steam']
                archive_data = io.BytesIO()
                marker_path, marker = 'usr/share/gamesir-offline-fixture/marker', b'offline only\n'
                with tarfile.open(fileobj=io.BytesIO(original), mode='r:') as old, \
                        tarfile.open(fileobj=archive_data, mode='w:') as new:
                    for member in old:
                        new.addfile(member, old.extractfile(member))
                    member = tarfile.TarInfo(marker_path)
                    member.size, member.mode = len(marker), 0o644
                    new.addfile(member, io.BytesIO(marker))
                blobs['steam'] = archive_data.getvalue()
                record = next(r for r in catalog.records if r.component == 'steam')
                catalog = Catalog((replace(record, size=len(blobs['steam']),
                                           digest=hashlib.sha256(blobs['steam']).hexdigest()),))
                port = Adapter()
                from backend import Request
                plan = build_plan(Request('install', ('steam',)), port.host, {'steam': blobs['steam']},
                                  catalog=catalog, now=100)
                preview = first.prepare(plan, cache)
                self.assertEqual(preview.packages, (COMPONENTS['steam'][0],))
                first.commit()
                self.assertEqual(first.rows(), ((COMPONENTS['steam'][0], VERSION),))
                self.assertEqual((root / marker_path).read_bytes(), marker)
            finally:
                first.close(); second.close()
            self.assertFalse((database / 'db.lck').exists())
            third = Alpm(self.library, str(root) + '/', database, [hooks])
            try:
                third.acquire()
                port.host = replace(port.host, installed=((COMPONENTS['steam'][0], VERSION),))
                plan = build_plan(Request('remove', ('steam',)), port.host, {}, catalog=catalog, now=100)
                preview = third.prepare(plan, cache)
                self.assertEqual(preview.other_removals, (COMPONENTS['steam'][0],))
                third.commit()
                self.assertEqual(third.rows(), ())
                self.assertFalse((root / marker_path).exists())
            finally:
                third.close()
            self.assertFalse((database / 'db.lck').exists())

    def test_missing_dependency_prepare_never_commits_or_bypasses_checks(self):
        with tempfile.TemporaryDirectory(dir=self.temp.name) as folder:
            root = Path(folder)
            database, hooks, cache = (root / p for p in ('db', 'hooks', 'cache'))
            for path in (database, hooks, cache): path.mkdir()
            alpm = Alpm(self.library, str(root) + '/', database, [hooks])
            try:
                alpm.acquire()
                catalog, blobs = fixture_catalog()
                # The planner fixture claims core is installed; actual empty
                # libalpm database independently rejects bridge dependency.
                port = Adapter()
                port.host = replace(port.host, installed=((COMPONENTS['core'][0], VERSION),))
                from backend import Request
                plan = build_plan(Request('install', ('bridge',)), port.host, {'bridge': blobs['bridge']},
                                  catalog=catalog, now=100)
                with self.assertRaises(BackendError): alpm.prepare(plan, cache)
                self.assertEqual(alpm.rows(), ())
            finally:
                alpm.close()
            self.assertFalse((database / 'db.lck').exists())

    def test_executor_stage_is_separate_noninstalled_and_hash_complete(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import package_control_center_executor as package
        import json
        with tempfile.TemporaryDirectory(dir=self.temp.name) as folder:
            dest = Path(folder) / 'stage'
            report = package.stage(dest)
            self.assertFalse(report['installed'] or report['reviewed'] or report['release_ready'])
            self.assertTrue(report['deployment_catalog_empty'])
            for target, expected in report['files'].items():
                path = dest / target.lstrip('/')
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                self.assertEqual(path.stat().st_mode & 0o777, 0o755 if path.name == 'execute' else 0o644)
            self.assertFalse((dest / 'usr/lib/gamesir-control-center/authorize').exists())
            self.assertEqual(json.loads((dest / 'EXECUTOR_REVIEW.json').read_text()), report)
            with self.assertRaises(ValueError): package.stage(dest)


if __name__ == '__main__':
    unittest.main()
