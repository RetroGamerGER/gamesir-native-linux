#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline Phase-C contracts, archive checks and existing ALPM guard integration."""
from contextlib import ExitStack
from dataclasses import replace
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import (BackendError, Catalog, Review, CORE_GUARDS, COMPONENTS,
                       PUBLIC_BINARIES, MAX_MEMBER)
from backend import (HostEvidence, Request, RehearsalPort, Session, TransactionPreview,
                     Verification, build_plan)
from status import PACKAGES
from test_packaging_alpha import FakeHost, remove, package


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


steam = load('cc_steam_package', 'scripts/package_steam.py')
bridge = load('cc_bridge_package', 'scripts/package_trigger_bridge.py')
KERNEL = '7.2.11-1-test'
CORE = COMPONENTS['core'][0]
BASE = HostEvidence('garuda', 'x86_64', KERNEL, KERNEL,
                    '12345678-1234-1234-1234-123456789abc', 'b' * 64, 100.0,
                    installed=(('other-controller-driver', '9.0-1'),))
GUARDS = (
    (CORE_GUARDS[0], ROOT / 'packaging/prepare_remove.py'),
    (CORE_GUARDS[1], ROOT / 'packaging/arch/60-gamesir-native-release.hook'),
    (CORE_GUARDS[2], ROOT / 'packaging/arch/60-gamesir-native-upgrade.hook'),
)


def request(op='install', parts=('core',)):
    return Request.parse({'schema': 1, 'operation': op, 'components': list(parts)})


def archive_bytes(component='core', *, version='0.1.0.alpha3-16', files=None,
                  info=None, extra=(), compression=''):
    if files is None:
        files = {name: path.read_bytes() for name, path in GUARDS} if component == 'core' else {}
    name, arch = COMPONENTS[component]
    info = info if info is not None else (f'pkgname = {name}\npkgver = {version}\n'
                                         f'arch = {arch}\nlicense = GPL-2.0-only\n').encode()
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w' + (':' + compression if compression else '')) as t:
        for path, value in {'.PKGINFO': info, **files}.items():
            entry = tarfile.TarInfo(path)
            if isinstance(value, tuple):
                value, entry.mode = value
            else:
                entry.mode = 0o644
            entry.size = len(value)
            t.addfile(entry, io.BytesIO(value))
        for entry, value in extra:
            t.addfile(entry, io.BytesIO(value) if value is not None else None)
    return output.getvalue()


def reviewed(data, component='core', **kwargs):
    record = Review(component, kwargs.pop('version', '0.1.0.alpha3-16'),
                    hashlib.sha256(data).hexdigest(), len(data), 'a' * 40,
                    'v0.1.0-pre-alpha.test',
                    guards=tuple((name, hashlib.sha256(path.read_bytes()).hexdigest())
                                 for name, path in GUARDS) if component == 'core' else (), **kwargs)
    return Catalog((record,))


class FakePort(RehearsalPort):
    """No Host or subprocess calls: mutate only this synthetic inventory."""
    def __init__(self, host, *, cleanup=None):
        self.host = host
        self.cleanup = cleanup or FakeHost()
        self.calls = []
        self.hook_calls = 0
        self.granted = True
        self.preview_extra = False
        self.guard_verified = True
        self.failure = None
        self.after = None

    def observe(self):
        self.calls.append('observe')
        return self.host

    def prepare(self, plan):
        self.calls.append('prepare')
        return TransactionPreview(plan.packages + (('unrelated-package',) if self.preview_extra else ()),
                                  tuple((a.package, a.review.version) for a in plan.artifacts),
                                  guard_verified=self.guard_verified)

    def authorize(self, plan):
        self.calls.append('authorize')
        return self.granted

    def commit(self, plan):
        self.calls.append('commit')
        if plan.needs_core_guard:
            self.hook_calls += 1
            try:
                remove.prepare_removal(self.cleanup, disable=plan.request.operation == 'remove')
            except remove.RemovalBlocked as error:
                raise BackendError('existing_alpm_guard_blocked') from error
        if self.failure:
            raise self.failure
        packages = dict(self.host.installed)
        if plan.request.operation == 'install':
            packages.update((a.package, a.review.version) for a in plan.artifacts)
        else:
            for name in plan.packages:
                packages.pop(name)
        self.after = Verification(tuple(sorted(packages.items())), core_guard_clear=True,
                                  dkms_kernel=self.host.kernel, module_version='0.1.0.alpha3',
                                  vermagic_kernel=self.host.kernel, service_inactive=True,
                                  module_absent=True, service_enabled=self.host.service_enabled
                                  if plan.request.operation == 'install' and plan.needs_core_guard else False,
                                  dkms_installed=plan.request.operation == 'install',
                                  dkms_absent=plan.request.operation == 'remove')

    def verify(self, plan):
        self.calls.append('verify')
        return self.after


class Contracts(unittest.TestCase):
    def setUp(self):
        self.data = archive_bytes()
        self.catalog = reviewed(self.data, upgrade_from=('0.1.0.alpha3-15',))

    def plan(self, host=BASE, op='install', parts=('core',), **kwargs):
        return build_plan(request(op, parts), host, {'core': self.data} if op == 'install' else {},
                          catalog=self.catalog, now=100, **kwargs)

    def run_plan(self, plan=None, port=None):
        plan = self.plan() if plan is None else plan
        port = FakePort(plan.host) if port is None else port
        session = Session(plan)
        return session.rehearse(plan.confirmation_id, port, clock=lambda: 100), port, session

    def test_request_rejects_commands_flags_paths_unknown_fields_and_schema(self):
        for value in [
                {'schema': True, 'operation': 'install', 'components': ['core']},
                {'schema': 2, 'operation': 'install', 'components': ['core']},
                {'schema': 1, 'operation': 'resume', 'components': ['core']},
                {'schema': 1, 'operation': 'remove', 'components': ['xpad']},
                {'schema': 1, 'operation': 'install', 'components': ['core'], 'command': 'sudo'},
                {'schema': 1, 'operation': 'remove', 'components': ['--nodeps']},
                {'schema': 1, 'operation': 'install', 'components': ['/tmp/package']},
                {'schema': 1, 'operation': 'remove', 'components': ['core', 'core']},
                {'schema': 1, 'operation': 'install', 'components': []}]:
            with self.subTest(value=value), self.assertRaises(BackendError):
                Request.parse(value)

    def test_summary_is_versioned_and_has_no_activation_or_arbitrary_shell(self):
        p = self.plan()
        result = json.loads(json.dumps(p.summary()))
        self.assertEqual(result['schema'], 1)
        self.assertFalse(result['activate'] or result['reboot'])
        self.assertTrue(result['offline_preparation_only'])
        self.assertIn('possible_snapshot', result['hook_effects'])
        self.assertIn('user_modprobe_overrides', result['preserved'])
        self.assertNotIn('command', result)
        self.assertEqual(len(p.confirmation_id), 64)

    def test_public_binary_catalog_is_empty_no_fabricated_download(self):
        self.assertEqual(PUBLIC_BINARIES.records, ())
        with self.assertRaisesRegex(BackendError, 'no_reviewed_binary'):
            build_plan(request(), BASE, {'core': self.data}, now=100)

    def test_missing_headers_or_dependencies_block_install(self):
        for host, code in [(replace(BASE, headers_release='other'), 'matching_headers_required'),
                           (replace(BASE, missing_dependencies=('lld',)), 'resolve_dependencies_separately')]:
            with self.assertRaisesRegex(BackendError, code):
                self.plan(host)

    def test_unknown_or_nonreviewed_platform_blocks(self):
        for host in (replace(BASE, distribution='bazzite'), replace(BASE, architecture='aarch64')):
            with self.assertRaisesRegex(BackendError, 'unsupported_platform'):
                self.plan(host)

    def test_stale_future_or_malformed_evidence_and_db_lock_block(self):
        for host in (replace(BASE, observed_at=0), replace(BASE, observed_at=101),
                     replace(BASE, database_locked=True), replace(BASE, boot_id='unknown'),
                     replace(BASE, installed=((CORE, '1-1'), (CORE, '2-1')))):
            with self.assertRaises(BackendError):
                self.plan(host)

    def test_loaded_unowned_module_blocks_first_install(self):
        with self.assertRaisesRegex(BackendError, 'unowned_loaded_module'):
            self.plan(replace(BASE, native_loaded=True))

    def test_unowned_enabled_service_cannot_implicitly_activate_new_install(self):
        with self.assertRaisesRegex(BackendError, 'unowned_enabled_service'):
            self.plan(replace(BASE, service_enabled=True))

    def test_same_version_and_unreviewed_update_or_downgrade_block(self):
        for old, error in [('0.1.0.alpha3-16', 'already_installed'),
                           ('0.1.0.alpha3-17', 'unreviewed_version_transition'),
                           ('0.1.0.alpha3-10', 'unreviewed_version_transition')]:
            with self.assertRaisesRegex(BackendError, error):
                self.plan(replace(BASE, installed=BASE.installed + ((CORE, old),)))

    def test_removal_does_not_require_headers_build_tools_or_network(self):
        host = replace(BASE, installed=BASE.installed + ((CORE, '0.1.0.alpha3-16'),),
                       headers_release='', missing_dependencies=('lld',), native_loaded=True)
        result, port, _ = self.run_plan(self.plan(host, op='remove'))
        self.assertEqual(result.state, 'simulated_success')
        self.assertEqual(port.hook_calls, 1)
        self.assertIn(('/usr/bin/systemctl', 'disable', 'gamesir-native.service'), port.cleanup.calls)

    def test_absent_selected_package_is_not_removed(self):
        with self.assertRaisesRegex(BackendError, 'selected_package_absent'):
            self.plan(op='remove')

    def test_dependents_must_be_explicitly_selected_for_removal(self):
        host = replace(BASE, installed=((CORE, '0.1.0.alpha3-16'),
                                       (COMPONENTS['bridge'][0], '0.1.0.alpha1-2')))
        with self.assertRaisesRegex(BackendError, 'dependent_component'):
            self.plan(host, op='remove')
        plan = self.plan(host, op='remove', parts=('core', 'bridge'))
        self.assertEqual(plan.packages, (COMPONENTS['bridge'][0], CORE))

    def test_cancellation_and_repeated_confirmation_never_replay(self):
        plan = self.plan(); port = FakePort(BASE); session = Session(plan)
        first = session.cancel()
        self.assertEqual(first.state, 'cancelled')
        self.assertIs(session.rehearse(plan.confirmation_id, port, clock=lambda: 100), first)
        self.assertEqual(port.calls, [])

    def test_wrong_confirmation_consumed_before_adapter_contact(self):
        plan = self.plan(); port = FakePort(BASE); session = Session(plan)
        result = session.rehearse('wrong', port, clock=lambda: 100)
        self.assertEqual(result.error, 'confirmation_mismatch')
        self.assertEqual(port.calls, [])
        self.assertIs(session.rehearse(plan.confirmation_id, port, clock=lambda: 100), result)

    def test_no_implicit_or_live_transport(self):
        plan = self.plan()
        result = Session(plan).rehearse(plan.confirmation_id, object(), clock=lambda: 100)
        self.assertEqual(result.error, 'offline_test_double_required')

    def test_expired_plan_blocks_and_host_change_requires_new_review(self):
        plan = self.plan(); port = FakePort(BASE)
        result = Session(plan).rehearse(plan.confirmation_id, port, clock=lambda: 221)
        self.assertEqual(result.error, 'plan_expired')
        for host in (replace(BASE, kernel='new-kernel'), replace(BASE, database_token='c'*64),
                     replace(BASE, boot_id='22345678-1234-1234-1234-123456789abc')):
            port = FakePort(host)
            result, _, _ = self.run_plan(plan, port)
            self.assertEqual(result.error, 'host_changed')
            self.assertNotIn('authorize', port.calls)

    def test_unexpected_transaction_blocks_before_admin_prompt(self):
        port = FakePort(BASE); port.preview_extra = True
        result, _, _ = self.run_plan(port=port)
        self.assertEqual(result.error, 'unexpected_package_transaction')
        self.assertNotIn('authorize', port.calls)

    def test_downloads_external_removals_or_wrong_versions_are_not_approved(self):
        for extra in ({'downloads': ('dependency',)}, {'other_removals': ('xpad',)},
                      {'versions': ((CORE, 'other-version'),)}, {'guard_verified': 1}):
            port = FakePort(BASE)
            original = port.prepare
            port.prepare = lambda plan, extra=extra: replace(original(plan), **extra)
            result, _, _ = self.run_plan(port=port)
            self.assertEqual(result.error, 'unexpected_package_transaction')
            self.assertNotIn('authorize', port.calls)

    def test_freshness_and_confirmation_bind_selected_components_and_bytes(self):
        plan = self.plan()
        new_host = replace(BASE, database_token='c' * 64)
        changed = self.plan(new_host)
        self.assertNotEqual(plan.confirmation_id, changed.confirmation_id)
        port = FakePort(replace(BASE, observed_at=0))
        result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.error, 'stale_host_evidence')

    def test_original_adapter_exception_is_retained_privately_without_path_leak(self):
        port = FakePort(BASE)
        error = TimeoutError('private diagnostic details')
        port.failure = error
        result, _, session = self.run_plan(port=port)
        self.assertIs(session.first_failure, error)
        self.assertNotIn('private diagnostic', repr(result))
        session.cancel()
        self.assertIs(session.first_failure, error)

    def test_cancelled_admin_prompt_has_no_package_or_guard_calls(self):
        port = FakePort(BASE); port.granted = False
        result, _, _ = self.run_plan(port=port)
        self.assertEqual(result.state, 'cancelled')
        self.assertFalse(result.changes_possible)
        self.assertNotIn('commit', port.calls)
        self.assertEqual(port.hook_calls, 0)

    def test_changes_or_expiry_during_admin_interaction_block_commit(self):
        plan = self.plan(); port = FakePort(BASE); clock_value = [100]
        def authorize(_):
            clock_value[0] = 300
            return True
        port.authorize = authorize
        result = Session(plan).rehearse(plan.confirmation_id, port, clock=lambda: clock_value[0])
        self.assertEqual(result.error, 'plan_expired')
        self.assertNotIn('commit', port.calls)
        port = FakePort(BASE)
        def change(_):
            port.host = replace(BASE, database_token='d'*64)
            return True
        port.authorize = change
        result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.error, 'host_changed')
        self.assertNotIn('commit', port.calls)

    def test_first_install_never_runs_guard_or_starts_service(self):
        result, port, session = self.run_plan()
        self.assertEqual(result.state, 'simulated_success')
        self.assertEqual(port.hook_calls, 0)
        self.assertEqual(port.calls, ['observe', 'prepare', 'authorize', 'observe', 'commit', 'verify'])
        self.assertIs(session.rehearse(session.plan.confirmation_id, port, clock=lambda: 100), result)
        self.assertEqual(port.calls.count('commit'), 1)
        self.assertNotIn('controller_release', session.plan.summary()['hook_effects'])

    def upgrade(self):
        host = replace(BASE, installed=BASE.installed + ((CORE, '0.1.0.alpha3-15'),),
                       native_loaded=True, service_enabled=True)
        return self.plan(host)

    def test_upgrade_reuses_existing_real_guard_exactly_once(self):
        plan = self.upgrade(); result, port, _ = self.run_plan(plan)
        self.assertEqual(result.state, 'simulated_success')
        self.assertEqual(port.hook_calls, 1)
        changes = [call for call in port.cleanup.calls if call[:2] != ('/usr/bin/systemctl', 'show')]
        self.assertEqual(changes, [('/usr/bin/gamesir-native', 'release'),
                                   ('/usr/bin/systemctl', 'stop', 'gamesir-native.service'),
                                   ('/usr/bin/rmmod', 'gs_native')])
        self.assertEqual(len(port.cleanup.calls) - len(changes), 2)
        self.assertTrue(port.after.service_enabled)  # Existing enablement is preserved, not activated.

    def test_unverified_installed_guard_blocks_before_authorization(self):
        plan = self.upgrade(); port = FakePort(plan.host); port.guard_verified = False
        result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.error, 'installed_core_guard_unverified')
        self.assertNotIn('authorize', port.calls)

    def test_guard_failures_preserve_first_error_and_do_not_advance(self):
        for kwargs in ({'release_fail': True}, {'release_keeps_pending': True, 'pending': True},
                       {'refs': 1}, {'unload_fail': True}, {'rebound': True},
                       {'stopped_status': {'ExecMainStatus': 1, 'Result': 'exit-code'}}):
            with self.subTest(kwargs=kwargs):
                plan = self.upgrade(); port = FakePort(plan.host, cleanup=FakeHost(**kwargs))
                result, _, session = self.run_plan(plan, port)
                self.assertEqual(result.error, 'existing_alpm_guard_blocked')
                self.assertIsNotNone(session.first_failure.__cause__)
                self.assertTrue(result.changes_possible)
                self.assertNotIn('verify', port.calls)
                self.assertIsNone(port.after)
                self.assertIs(session.rehearse(plan.confirmation_id, port, clock=lambda: 100), result)
                self.assertEqual(port.hook_calls, 1)

    def test_package_failure_or_timeout_never_claims_no_changes(self):
        for error, state in [(BackendError('package_failed'), 'failed'), (TimeoutError(), 'uncertain')]:
            port = FakePort(BASE); port.failure = error
            result, _, _ = self.run_plan(port=port)
            self.assertEqual(result.state, state)
            self.assertTrue(result.changes_possible)
            self.assertNotIn('verify', port.calls)

    def test_wrong_dkms_kernel_module_vermagic_or_activation_fails_postcheck(self):
        for kwargs in ({'dkms_kernel': 'wrong'}, {'module_version': 'old'},
                       {'vermagic_kernel': 'wrong'}, {'service_inactive': False},
                       {'module_absent': False}, {'service_enabled': True},
                       {'module_absent': 'true'}, {'service_inactive': 1}, {'dkms_installed': False}):
            port = FakePort(BASE)
            original = port.verify
            port.verify = lambda plan, kwargs=kwargs: replace(original(plan), **kwargs)
            result, _, _ = self.run_plan(port=port)
            self.assertNotEqual(result.state, 'simulated_success')
            self.assertEqual(result.stage, 'post_verification')

    def test_core_removal_requires_verified_absence_of_project_dkms_entries(self):
        host = replace(BASE, installed=BASE.installed + ((CORE, '0.1.0.alpha3-16'),))
        plan = self.plan(host, op='remove'); port = FakePort(host)
        original = port.verify
        port.verify = lambda p: replace(original(p), dkms_absent=False)
        result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.error, 'dkms_removal_unverified')

    def test_postcheck_preserves_other_packages_and_requires_return_proof(self):
        port = FakePort(BASE)
        port.verify = lambda p: Verification((), service_inactive=True, module_absent=True)
        result, _, _ = self.run_plan(port=port)
        self.assertEqual(result.error, 'package_postcheck_mismatch')
        plan = self.upgrade(); port = FakePort(plan.host)
        original = port.verify
        port.verify = lambda p: replace(original(p), core_guard_clear=False)
        result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.error, 'return_not_verified')

    def test_optional_only_transaction_keeps_core_runtime_out_of_scope(self):
        blob = archive_bytes('steam', version='0.1.0.alpha2-1')
        catalog = reviewed(blob, 'steam', version='0.1.0.alpha2-1')
        host = replace(BASE, native_loaded=True,
                       installed=BASE.installed + ((CORE, '0.1.0.alpha3-16'),))
        plan = build_plan(request(parts=('steam',)), host, {'steam': blob}, catalog=catalog, now=100)
        result, port, _ = self.run_plan(plan)
        self.assertEqual(result.state, 'simulated_success')
        self.assertFalse(plan.needs_core_guard)
        self.assertEqual(port.cleanup.calls, [])

    def test_rehearsal_has_no_files_process_network_or_device_io(self):
        plan = self.upgrade(); port = FakePort(plan.host)
        with ExitStack() as stack:
            for name in ('builtins.open', 'os.open', 'pathlib.Path.open', 'socket.socket',
                         'subprocess.run', 'subprocess.Popen', 'urllib.request.urlopen'):
                stack.enter_context(patch(name, side_effect=AssertionError('Forbidden live I/O')))
            result, _, _ = self.run_plan(plan, port)
        self.assertEqual(result.state, 'simulated_success')


class ArtifactTests(unittest.TestCase):
    def assert_invalid(self, data, code=None, **kwargs):
        with self.assertRaises(BackendError) as caught:
            reviewed(data, **kwargs).verify(kwargs.get('component', 'core'), data)
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_valid_archive_immutable_bytes_and_exact_identity(self):
        data = archive_bytes()
        self.assertEqual(reviewed(data).verify('core', data).package, CORE)
        with self.assertRaisesRegex(BackendError, 'invalid_artifact_bytes'):
            reviewed(data).verify('core', bytearray(data))

    def test_untrusted_or_changed_bytes_cannot_self_authenticate(self):
        data = archive_bytes(); catalog = reviewed(data)
        with self.assertRaisesRegex(BackendError, 'no_reviewed_binary'):
            catalog.verify('core', data + b'changed')

    def test_wrong_name_version_arch_license_and_relationships_rejected(self):
        good = (f'pkgname = {CORE}\npkgver = 0.1.0.alpha3-16\narch = x86_64\nlicense = GPL-2.0-only\n').encode()
        for data in (good.replace(CORE.encode(), b'unrelated'), good.replace(b'x86_64', b'any'),
                     good.replace(b'alpha3-16', b'alpha3-15'), good.replace(b'GPL-2.0-only', b'proprietary'),
                     good + b'replaces = xpad\n', good + b'conflict = steam\n',
                     good + b'depend = unexpected\n', good + b'provides = other-package\n'):
            self.assert_invalid(archive_bytes(info=data))

    def test_path_traversal_absolute_duplicate_and_install_script_blocked(self):
        for name in ('../escape', '/etc/shadow', 'usr/../etc/shadow', './hidden', '.INSTALL', '.PKGINFO'):
            entry = tarfile.TarInfo(name); entry.size = 1
            self.assert_invalid(archive_bytes(extra=((entry, b'x'),)))

    def test_links_devices_special_permissions_and_limit_blocked(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE):
            entry = tarfile.TarInfo('usr/extra'); entry.type = kind; entry.linkname = '/etc/shadow'
            self.assert_invalid(archive_bytes(extra=((entry, None),)))
        entry = tarfile.TarInfo('usr/setuid'); entry.mode = 0o4755
        self.assert_invalid(archive_bytes(extra=((entry, b''),)))
        with patch('artifacts.MAX_MEMBER', 2):
            self.assert_invalid(archive_bytes())

    def test_incomplete_bad_compression_missing_info_and_guard_change_blocked(self):
        self.assert_invalid(b'not an archive')
        good = archive_bytes()
        self.assert_invalid(good[:700])
        self.assert_invalid(archive_bytes(files={name: b'changed' for name, _ in GUARDS}), 'package_guard_mismatch')
        out = io.BytesIO()
        with tarfile.open(fileobj=out, mode='w'):
            pass
        self.assert_invalid(out.getvalue(), 'missing_package_metadata')

    def test_gzip_and_zstd_when_stdlib_supports_it(self):
        data = archive_bytes(compression='gz')
        self.assertEqual(reviewed(data).verify('core', data).package, CORE)
        if sys.version_info >= (3, 14):
            from compression import zstd
            data = zstd.compress(archive_bytes())
            self.assertEqual(reviewed(data).verify('core', data).package, CORE)

    def test_invalid_review_or_duplicate_record_is_rejected(self):
        catalog = reviewed(archive_bytes()); record = catalog.records[0]
        for bad in (replace(record, source_commit='unknown'), replace(record, size=True),
                    replace(record, digest='x'), replace(record, guards=()),
                    replace(record, upgrade_from=(record.version,))):
            with self.assertRaises(BackendError):
                Catalog((bad,))
        with self.assertRaisesRegex(BackendError, 'duplicate_review_record'):
            Catalog((record, record))

    def test_artifact_size_and_core_guard_review_cannot_be_skipped(self):
        data = archive_bytes(); record = reviewed(data).records[0]
        with self.assertRaisesRegex(BackendError, 'artifact_size_mismatch'):
            Catalog((replace(record, size=len(data) + 1),)).verify('core', data)
        for change in ({'guards': (('wrong', 'a'*64),)}, {'dependencies': ('command;unsafe',)}):
            with self.assertRaises(BackendError):
                Catalog((replace(record, **change),))


class ExistingPackagingIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        root = Path(cls.temp.name)
        client = root / 'gsnative-ctl'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                        str(ROOT / 'tools/native/gsnative-ctl.c'), '-o', str(client)], check=True)
        package.stage(root / 'core', client)
        steam.stage(root / 'steam')
        steam.stage(root / 'gamescope', component='gamescope')
        built = bridge.build(root / 'shim')
        bridge.stage(root / 'bridge', built['shim'])
        cls.blobs, records = {}, []
        for component in COMPONENTS:
            folder = {'core': 'packaging', 'steam': 'packaging/steam',
                      'gamescope': 'packaging/steam-gamescope', 'bridge': 'packaging/trigger-bridge'}[component]
            recipe = (ROOT / folder / ('arch/PKGBUILD.in' if component == 'core' else 'PKGBUILD.in')).read_text()
            cls.assert_recipe = re.search(r'^pkgname=(.+)$', recipe, re.M)[1]
            assert cls.assert_recipe == COMPONENTS[component][0]
            version = (ROOT / folder / 'VERSION').read_text().strip() + '-' + re.search(r'^pkgrel=(\d+)$', recipe, re.M)[1]
            dependencies = tuple(shlex.split(re.search(r'^depends=\((.*?)\)', recipe, re.M | re.S)[1]))
            metadata = (f'pkgname = {COMPONENTS[component][0]}\npkgver = {version}\n'
                        f'arch = {COMPONENTS[component][1]}\nlicense = GPL-2.0-only\n' +
                        ''.join('depend = ' + d + '\n' for d in dependencies)).encode()
            files = {p.relative_to(root / component).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
                     for p in (root / component).rglob('*') if p.is_file()}
            blob = archive_bytes(component, version=version, info=metadata, files=files)
            review = reviewed(blob, component, version=version, dependencies=dependencies).records[0]
            cls.blobs[component] = blob
            records.append(review)
        cls.catalog = Catalog(records)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_four_component_stagers_pass_offline_package_review(self):
        self.assertEqual(set(PACKAGES), {name for name, _ in COMPONENTS.values()})
        for component, blob in self.blobs.items():
            with self.subTest(component=component):
                self.assertEqual(self.catalog.verify(component, blob).package, COMPONENTS[component][0])

    def test_install_all_and_remove_all_keep_unrelated_inventory(self):
        host = replace(BASE, distribution='cachyos')
        plan = build_plan(request(parts=tuple(COMPONENTS)), host, self.blobs, catalog=self.catalog, now=100)
        port = FakePort(host)
        result = Session(plan).rehearse(plan.confirmation_id, port, clock=lambda: 100)
        self.assertEqual(result.state, 'simulated_success')
        after = replace(host, installed=port.after.installed, native_loaded=True, service_enabled=True,
                        headers_release='', missing_dependencies=('lld',))
        plan = build_plan(request('remove', tuple(COMPONENTS)), after, now=100)
        port = FakePort(after)
        result = Session(plan).rehearse(plan.confirmation_id, port, clock=lambda: 100)
        self.assertEqual(result.state, 'simulated_success')
        self.assertEqual(port.after.installed, BASE.installed)
        self.assertEqual(port.hook_calls, 1)

    def test_gamescope_scope_and_dependency_selection(self):
        blobs = {c: self.blobs[c] for c in ('steam', 'gamescope')}
        with self.assertRaisesRegex(BackendError, 'gamescope_requires_cachyos'):
            build_plan(request(parts=('steam', 'gamescope')), BASE, blobs, catalog=self.catalog, now=100)
        with self.assertRaisesRegex(BackendError, 'dependent_component'):
            build_plan(request(parts=('gamescope',)), replace(BASE, distribution='cachyos'),
                       {'gamescope': self.blobs['gamescope']}, catalog=self.catalog, now=100)

    def test_core_hooks_still_abort_before_transaction_and_backend_not_in_payload(self):
        for path in ('packaging/arch/60-gamesir-native-upgrade.hook',
                     'packaging/arch/60-gamesir-native-release.hook'):
            text = (ROOT / path).read_text()
            self.assertIn('When = PreTransaction', text)
            self.assertIn('AbortOnFail', text)
        self.assertFalse(any('control_center' in p for p in package.source_files()))


if __name__ == '__main__':
    unittest.main()
