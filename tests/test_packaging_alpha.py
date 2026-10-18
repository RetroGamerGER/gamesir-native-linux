#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package/filesystem and uninstall-state tests. No service, DKMS or device calls."""
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


package = module('alpha_package', ROOT / 'scripts/package_alpha.py')
remove = module('alpha_remove', ROOT / 'packaging/prepare_remove.py')


class FakeHost(remove.Host):
    def __init__(self, *, active='active', loaded=True, refs=0, bindings=(),
                 release_fail=False, unload_fail=False, rebound=False,
                 pending=False, release_keeps_pending=False, pending_after_stop=False,
                 initial_status=None, stopped_status=None):
        self.active, self.loaded, self.refs = active, loaded, refs
        self.bindings = list(bindings)
        self.release_fail, self.unload_fail, self.rebound = release_fail, unload_fail, rebound
        self.pending, self.release_keeps_pending = pending, release_keeps_pending
        self.pending_after_stop = pending_after_stop
        self.status = {'LoadState': 'loaded', 'ActiveState': active,
                       'SubState': {'active': 'running', 'inactive': 'dead',
                                    'failed': 'failed'}.get(active, 'start'),
                       'MainPID': 123 if active == 'active' else 0, 'ControlPID': 0,
                       'Result': 'success', 'ExecMainCode': 0, 'ExecMainStatus': 0,
                       'ExecMainStartTimestampMonotonic': 0,
                       'ExecMainExitTimestampMonotonic': 0}
        self.status.update(initial_status or {})
        self.stopped_status = stopped_status or {}
        self.calls = []

    def run(self, argv, **_kwargs):
        self.calls.append(tuple(argv))
        if argv[1] == 'show':
            return subprocess.CompletedProcess(argv, 0, '\n'.join(
                f'{key}={value}' for key, value in self.status.items()) + '\n', '')
        if argv[0] == '/usr/bin/gamesir-native':
            if self.release_fail:
                raise remove.RemovalBlocked('simulated return failure')
            self.bindings = []
            if not self.release_keeps_pending:
                self.pending = False
        elif argv[1] == 'stop':
            self.active = 'inactive'
            self.status.update(ActiveState='inactive', SubState='dead', MainPID=0, ControlPID=0)
            self.status.update(self.stopped_status)
            self.pending = self.pending_after_stop
            if self.rebound:
                self.bindings = ['2-3.4:1.0']
        elif argv[0] == '/usr/bin/rmmod':
            if self.unload_fail:
                raise remove.RemovalBlocked('simulated module busy')
            self.loaded = False
        return subprocess.CompletedProcess(argv, 0, '', '')

    def module_loaded(self):
        return self.loaded

    def native_bindings(self):
        return self.bindings

    def module_references(self):
        return self.refs

    def manager_present(self):
        return False

    def unresolved_ownership(self, *, allow_prior_boot=False):
        return self.pending


class PackageTests(unittest.TestCase):
    def test_missing_license_prevents_archive_and_staging_before_output(self):
        for missing in package.LICENSE_FILES:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory(dir=ROOT / 'build') as tmp:
                tmp = Path(tmp)
                fixture = tmp / 'fixture'
                for relative in package.source_files():
                    if relative == missing:
                        continue
                    item = fixture / relative
                    item.parent.mkdir(parents=True, exist_ok=True)
                    item.write_bytes(b'')
                (fixture / 'packaging/VERSION').write_text(package.version() + '\n')
                archive_dest, staged_dest = tmp / 'archive', tmp / 'stage'
                with self.assertRaisesRegex(ValueError, re.escape(missing)):
                    package.source_archive(archive_dest, root=fixture)
                with self.assertRaisesRegex(ValueError, re.escape(missing)):
                    package.stage(staged_dest, tmp / 'unused-client', root=fixture)
                self.assertFalse(archive_dest.exists())
                self.assertFalse(staged_dest.exists())

    def test_package_version_matches_kernel_module_version(self):
        source = (ROOT / 'kernel/gs_native_usb.c').read_text()
        declared = re.findall(r'^\s*MODULE_VERSION\s*\(\s*"([^"\n]+)"\s*\)\s*;',
                              source, re.MULTILINE)
        self.assertEqual(declared, [package.version()],
                         'The installed module must report exactly the packaged release version')

    def test_reproducible_allowlisted_archive(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as tmp:
            first = package.source_archive(Path(tmp) / 'one')
            second = package.source_archive(Path(tmp) / 'two')
            self.assertEqual(first['sha256'], second['sha256'])
            with tarfile.open(first['archive']) as archive:
                names = archive.getnames()
                self.assertTrue(any(p.endswith('/kernel/Kbuild') for p in names))
                self.assertTrue(any(p.endswith('/src/gs_startup.c') for p in names))
                self.assertTrue(any(p.endswith('/include/uapi/gs_native.h') for p in names))
                self.assertTrue(any(p.endswith('/scripts/kernel_toolchain.py') for p in names))
                for doc in package.DOCUMENT_FILES:
                    self.assertIn(f'gamesir-native-{package.version()}/{doc}', names)
                for relative in package.LICENSE_FILES:
                    member = archive.getmember(f'gamesir-native-{package.version()}/{relative}')
                    self.assertEqual(archive.extractfile(member).read(),
                                     (ROOT / relative).read_bytes())
                    self.assertEqual(member.mode, 0o644)
                uapi = archive.extractfile(
                    f'gamesir-native-{package.version()}/include/uapi/gs_native.h').read()
                self.assertIn(b'SPDX-License-Identifier: GPL-2.0-only WITH Linux-syscall-note',
                              uapi)
                self.assertFalse(any('/build/' in p or '.pcap' in p or '.local/' in p for p in names))
                self.assertTrue(all(m.uid == m.gid == 0 for m in archive.getmembers()))
            text = (Path(tmp) / 'one/PKGBUILD').read_text()
            self.assertIn(first['sha256'], text)
            with self.assertRaises(ValueError):
                package.source_archive(Path(tmp) / 'one')

    def test_stage_existing_core_and_no_activation(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as tmp:
            tmp = Path(tmp)
            client = tmp / 'gsnative-ctl'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                            str(ROOT / 'tools/native/gsnative-ctl.c'), '-o', str(client)], check=True)
            subprocess.run([str(client), '--self-test'], check=True, capture_output=True)
            staged = tmp / 'dest'
            package.stage(staged, client)
            base = staged / f'usr/src/gamesir-native-{package.version()}'
            self.assertEqual((base / 'src/gs_protocol.c').read_bytes(),
                             (ROOT / 'src/gs_protocol.c').read_bytes())
            self.assertTrue((base / 'kernel/../src/gs_runtime.h').is_file())
            self.assertTrue((base / 'kernel/../include/uapi/gs_native.h').is_file())
            self.assertEqual((base / 'scripts/kernel_toolchain.py').read_bytes(),
                             (ROOT / 'scripts/kernel_toolchain.py').read_bytes())
            for module in ('haptics_broker.py','gamesir_haptics.py','gamesir_mapping.py'):
                self.assertTrue((staged / 'usr/lib/gamesir-native' / module).is_file())
            rule = staged / 'usr/lib/udev/rules.d/70-gamesir-native-sensors.rules'
            self.assertEqual(rule.read_bytes(), (ROOT / 'packaging/udev/70-gamesir-native-sensors.rules').read_bytes())
            self.assertFalse((staged / 'etc/modprobe.d').exists())
            groups = (staged / 'usr/lib/sysusers.d/gamesir-native.conf').read_text()
            self.assertEqual([line for line in groups.splitlines() if line and not line.startswith('#')],
                             ['g gamesir-native-haptics -'])
            dkms = (base / 'dkms.conf').read_text()
            self.assertNotIn('@VERSION@', dkms)
            self.assertIn('BUILT_MODULE_LOCATION[0]="kernel"', dkms)
            self.assertIn('/scripts/kernel_toolchain.py', dkms)
            self.assertNotIn('LLVM=1', dkms)
            self.assertFalse((staged / 'etc').exists())
            self.assertFalse(any(staged.rglob('*.ko')))
            self.assertFalse(any(p.is_symlink() for p in staged.rglob('*')))
            docroot = staged / 'usr/share/doc/gamesir-native'
            for doc in package.DOCUMENT_FILES:
                self.assertEqual((docroot / doc).read_bytes(), (ROOT / doc).read_bytes())
            for relative in package.LICENSE_FILES:
                expected = (ROOT / relative).read_bytes()
                for distributed in (
                        base / relative,
                        docroot / relative,
                        staged / 'usr/share/licenses/gamesir-native-dkms' / Path(relative).name):
                    with self.subTest(license_path=distributed):
                        self.assertEqual(distributed.read_bytes(), expected)
                        self.assertEqual(stat.S_IMODE(distributed.stat().st_mode), 0o644)
            self.assertIn('docs/LICENSING.md', package.DOCUMENT_FILES)
            self.assertIn('tools/offline/docs/source-map.json', package.DOCUMENT_FILES)
            # The licensing report's local provenance/text references remain
            # usable in the installed documentation as well as the repository.
            licensing = docroot / 'docs/LICENSING.md'
            for link in re.findall(r'\]\(([^)]+)\)', licensing.read_text()):
                if not link.startswith(('https:', 'http:', '#')):
                    self.assertTrue((licensing.parent / link.split('#')[0]).is_file(), link)
            # README links stay valid after installation: retaining docs/ is
            # necessary, not merely copying all Markdown by basename.
            for link in re.findall(r'\]\(([^)]+)\)', (docroot / 'README.md').read_text()):
                if not link.startswith(('https:', 'http:', '#')):
                    self.assertTrue((docroot / link.split('#')[0]).is_file(), link)
            hook = (staged / 'usr/share/libalpm/hooks/60-gamesir-native-release.hook').read_text()
            self.assertIn('AbortOnFail', hook)
            self.assertIn('When = PreTransaction', hook)
            unit = (staged / 'usr/lib/systemd/system/gamesir-native.service').read_text()
            self.assertIn('persistent_mode=1', unit)
            self.assertIn('SendSIGKILL=no', unit)
            self.assertNotIn('xpad/unbind', unit)
            self.assertNotIn('Restart=always', unit)
            self.assertIn('Documentation=file:/usr/share/doc/gamesir-native/docs/ALPHA_INSTALLATION.md', unit)

    def test_refuses_system_or_privileged_build(self):
        for path in ('/', '/usr/local/foo', '/etc/foo', '/run/foo', '/var/tmp/stage'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                package.safe_destination(path)
        with patch.object(package, 'real_effective_uid', return_value=0):
            with self.assertRaises(ValueError):
                package.safe_destination(ROOT / 'build/unused')


class RemovalTests(unittest.TestCase):
    def test_success_returns_stops_then_unloads_only_native(self):
        host = FakeHost(bindings=['2-3.4:1.0'])
        self.assertTrue(remove.prepare_removal(host)['safe_to_remove'])
        self.assertEqual(host.calls[1:], [('/usr/bin/gamesir-native', 'release'),
            ('/usr/bin/systemctl', 'stop', 'gamesir-native.service'),
            ('/usr/bin/systemctl', 'show', '--property=' + ','.join(remove.SERVICE_PROPERTIES),
             'gamesir-native.service'), ('/usr/bin/rmmod', 'gs_native')])

    def test_already_inactive_and_absent(self):
        host = FakeHost(active='inactive', loaded=False)
        remove.prepare_removal(host)
        self.assertFalse(any(c[0] in ('/usr/bin/gamesir-native', '/usr/bin/rmmod') for c in host.calls))

    def test_removal_disables_only_after_successful_return(self):
        host = FakeHost()
        remove.prepare_removal(host, disable=True)
        self.assertEqual(host.calls[-1], ('/usr/bin/systemctl', 'disable', 'gamesir-native.service'))
        blocked = FakeHost(release_fail=True)
        with self.assertRaises(remove.RemovalBlocked):
            remove.prepare_removal(blocked, disable=True)
        self.assertFalse(any('disable' in call for call in blocked.calls))

    def test_failed_release_never_stops_or_unloads(self):
        host = FakeHost(release_fail=True)
        with self.assertRaises(remove.RemovalBlocked):
            remove.prepare_removal(host)
        self.assertEqual(len(host.calls), 2)

    def test_stale_bindings_without_manager_block(self):
        host = FakeHost(active='inactive', bindings=['8-6:1.0'])
        with self.assertRaises(remove.RemovalBlocked):
            remove.prepare_removal(host)
        self.assertEqual(len(host.calls), 1)

    def test_references_or_rebind_block_unload(self):
        for kwargs in ({'refs': 1}, {'rebound': True}):
            with self.subTest(kwargs=kwargs):
                host = FakeHost(**kwargs)
                with self.assertRaises(remove.RemovalBlocked):
                    remove.prepare_removal(host)
                self.assertFalse(any(c[0] == '/usr/bin/rmmod' for c in host.calls))

    def test_unload_error_is_not_ignored_or_retried(self):
        host = FakeHost(unload_fail=True)
        with self.assertRaises(remove.RemovalBlocked):
            remove.prepare_removal(host)
        self.assertEqual(sum(c[0] == '/usr/bin/rmmod' for c in host.calls), 1)

    def test_unclear_systemd_state_blocks(self):
        host = FakeHost(active='activating')
        with self.assertRaises(remove.RemovalBlocked):
            remove.prepare_removal(host)
        self.assertEqual(len(host.calls), 1)

    def test_failed_partial_bootstrap_without_binding_or_socket_blocks_removal(self):
        host = FakeHost(active='failed', bindings=(), pending=True,
                        initial_status={'Result': 'exit-code', 'ExecMainCode': 1,
                                        'ExecMainStatus': 1})
        with self.assertRaisesRegex(remove.RemovalBlocked, 'Unresolved manager ownership'):
            remove.prepare_removal(host, disable=True)
        self.assertEqual(len(host.calls), 1)
        self.assertTrue(host.loaded)

    def test_successful_release_must_actually_clear_recovery_record(self):
        host = FakeHost(pending=True, release_keeps_pending=True)
        with self.assertRaisesRegex(remove.RemovalBlocked, 'Unresolved manager ownership'):
            remove.prepare_removal(host)
        self.assertEqual(len(host.calls), 2)
        good = FakeHost(pending=True)
        self.assertTrue(remove.prepare_removal(good)['safe_to_remove'])

    def test_new_stop_failure_blocks_even_with_successful_stop_job_and_no_bindings(self):
        for changes in ({'Result': 'exit-code', 'ExecMainCode': 1, 'ExecMainStatus': 1},
                        {'Result': 'timeout'}, {'Result': 'success', 'ExecMainCode': 2,
                                               'ExecMainStatus': 15}):
            with self.subTest(changes=changes):
                host = FakeHost(stopped_status=changes)
                with self.assertRaisesRegex(remove.RemovalBlocked, 'New service exit/stop failure'):
                    remove.prepare_removal(host, disable=True)
                self.assertFalse(any(c[0] == '/usr/bin/rmmod' or 'disable' in c for c in host.calls))

    def test_stop_must_have_no_remaining_main_or_control_process(self):
        for changes in ({'MainPID': 123}, {'ControlPID': 456}, {'ActiveState': 'deactivating'},
                        {'SubState': 'stop-sigterm'}, {'LoadState': 'not-found'}):
            with self.subTest(changes=changes):
                host = FakeHost(stopped_status=changes)
                with self.assertRaisesRegex(remove.RemovalBlocked, 'Service stop is not complete'):
                    remove.prepare_removal(host)
                self.assertFalse(any(c[0] == '/usr/bin/rmmod' for c in host.calls))

    def test_never_started_missing_module_failure_can_be_removed(self):
        # ExecStartPre failed historically; no manager/leases/bindings exist.
        host = FakeHost(active='failed', loaded=False,
                        initial_status={'Result': 'exit-code', 'ExecMainCode': 0,
                                        'ExecMainStatus': 0})
        self.assertTrue(remove.prepare_removal(host, disable=True)['safe_to_remove'])
        self.assertFalse(any(c[0] in ('/usr/bin/gamesir-native', '/usr/bin/rmmod') for c in host.calls))

    def test_same_old_failure_is_not_a_permanent_uninstall_block(self):
        host = FakeHost(active='inactive', loaded=False,
                        initial_status={'Result': 'exit-code', 'ExecMainCode': 1,
                                        'ExecMainStatus': 1, 'ExecMainExitTimestampMonotonic': 55})
        self.assertTrue(remove.prepare_removal(host)['safe_to_remove'])
        changed = FakeHost(active='failed',
                           initial_status={'Result': 'exit-code', 'ExecMainCode': 1,
                                           'ExecMainStatus': 1, 'ExecMainExitTimestampMonotonic': 55},
                           stopped_status={'ExecMainExitTimestampMonotonic': 99})
        with self.assertRaisesRegex(remove.RemovalBlocked, 'New service exit/stop failure'):
            remove.prepare_removal(changed)

    def test_recovery_record_reappearing_after_stop_blocks_unload(self):
        host = FakeHost(pending_after_stop=True)
        with self.assertRaisesRegex(remove.RemovalBlocked, 'Unresolved manager ownership after shutdown'):
            remove.prepare_removal(host)
        self.assertFalse(any(c[0] == '/usr/bin/rmmod' for c in host.calls))


class RemovalReadbackTests(unittest.TestCase):
    def test_old_boot_ownership_requires_inactive_context_absent_module_and_valid_ids(self):
        metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0, st_size=150)
        old = '00000000-0000-0000-0000-000000000001'
        new = '00000000-0000-0000-0000-000000000002'
        cases = ((old, new, False, True, False), (old, new, True, True, True),
                 (old, new, False, False, True), (old, old, False, True, True),
                 ('invalid', new, False, True, True), (old, 'invalid', False, True, True),
                 (None, new, False, True, True), (123, new, False, True, True))
        for saved_boot, current_boot, loaded, allowed, pending in cases:
            state = json.dumps({'boot_id': saved_boot, 'leases': {'2-3.4': {'phase': 'blocked'}}})
            with self.subTest(saved=saved_boot, current=current_boot, loaded=loaded, allowed=allowed), \
                    patch.object(Path, 'lstat', return_value=metadata), \
                    patch.object(Path, 'read_text', side_effect=[state, current_boot]), \
                    patch.object(remove.Host, 'module_loaded', return_value=loaded):
                self.assertEqual(remove.Host().unresolved_ownership(allow_prior_boot=allowed), pending)

    def test_inactive_old_boot_removal_needs_no_daemon_start_or_state_rewrite(self):
        class RealReadbackFake(FakeHost):
            unresolved_ownership = remove.Host.unresolved_ownership
        host = RealReadbackFake(active='inactive', loaded=False)
        metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0, st_size=150)
        state = json.dumps({'boot_id': '00000000-0000-0000-0000-000000000001',
                            'leases': {'2-3.4': {'phase': 'blocked'}}})
        with patch.object(Path, 'lstat', return_value=metadata), \
                patch.object(Path, 'read_text', side_effect=[state,
                    '00000000-0000-0000-0000-000000000002', state,
                    '00000000-0000-0000-0000-000000000002']), \
                patch.object(Path, 'write_text') as write:
            self.assertTrue(remove.prepare_removal(host)['safe_to_remove'])
            write.assert_not_called()
        self.assertFalse(any(c[0] in ('/usr/bin/gamesir-native', '/usr/bin/rmmod') or
                             'start' in c for c in host.calls))

    def test_recovery_record_validates_ownership_not_historical_budget(self):
        metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0, st_size=100)
        for text, expected in (
                ('{"paused":true,"leases":{},"attempted":["old"],"error":"old"}', False),
                ('{"leases":{"2-3.4":{"phase":"bootstrapping","candidate":null}}}', True)):
            with self.subTest(text=text), patch.object(Path, 'lstat', return_value=metadata), \
                    patch.object(Path, 'read_text', return_value=text):
                self.assertEqual(remove.Host().unresolved_ownership(), expected)
        with patch.object(Path, 'lstat', side_effect=FileNotFoundError):
            self.assertFalse(remove.Host().unresolved_ownership())

    def test_bad_recovery_record_cannot_be_treated_as_no_ownership(self):
        metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0, st_size=100)
        for text in ('{}', '{"leases":[]}', 'null', 'not JSON'):
            with self.subTest(text=text), patch.object(Path, 'lstat', return_value=metadata), \
                    patch.object(Path, 'read_text', return_value=text), self.assertRaises(
                        (remove.RemovalBlocked, ValueError)):
                remove.Host().unresolved_ownership()
        for mode, uid, size in ((stat.S_IFLNK | 0o600, 0, 100), (stat.S_IFREG | 0o644, 0, 100),
                                (stat.S_IFREG | 0o600, 1000, 100),
                                (stat.S_IFREG | 0o600, 0, 1024 * 1024 + 1)):
            with self.subTest(mode=mode, uid=uid, size=size), patch.object(Path, 'lstat', return_value=
                    SimpleNamespace(st_mode=mode, st_uid=uid, st_size=size)), \
                    patch.object(Path, 'read_text') as read, self.assertRaises(remove.RemovalBlocked):
                remove.Host().unresolved_ownership()
            read.assert_not_called()

    def test_missing_duplicate_or_invalid_systemd_properties_block(self):
        valid = '\n'.join(f'{key}={value}' for key, value in FakeHost().status.items()) + '\n'
        invalid = (valid.replace('MainPID=123\n', ''), valid + 'MainPID=123\n',
                   valid.replace('MainPID=123', 'MainPID=invalid'), valid + 'Unknown=1\n')
        for text in invalid:
            with self.subTest(text=text), patch.object(remove.Host, 'run', return_value=
                    subprocess.CompletedProcess([], 0, text, '')), self.assertRaises(remove.RemovalBlocked):
                remove.Host().service_state()


if __name__ == '__main__':
    (ROOT / 'build').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
