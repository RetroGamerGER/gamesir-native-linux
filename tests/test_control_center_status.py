#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read-only detector tests use fake local metadata and synthetic subprocesses."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from i18n import CATALOGS
import status
from status import Collector, LocalReader, Fact, PACKAGES, DEPENDENCIES, SERVICE_QUERY, os_release
from status_view import present

KERNEL = '7.2.11-1-test'
ARCH = 'x86_64'
SERVICE = 'LoadState=loaded\nActiveState=active\nSubState=running\nUnitFileState=enabled\n'


class FakeReader(LocalReader):
    def __init__(self, root):
        self.root = Path(root)
        self.service_result = SERVICE

    def map(self, path):
        assert path.startswith('/')
        return self.root / path.lstrip('/')

    def text(self, path):
        return super().text(self.map(path))

    def entries(self, path):
        return super().entries(self.map(path))

    def stamp(self, path):
        return super().stamp(self.map(path))

    def link(self, path):
        return super().link(self.map(path))

    def directory(self, path):
        return super().directory(self.map(path))

    def regular(self, path):
        return super().regular(self.map(path))

    def uname(self):
        return KERNEL, ARCH

    def service(self):
        if isinstance(self.service_result, Exception):
            raise self.service_result
        return self.service_result

    def clock(self):
        return '2026-10-20T12:00:00+00:00'

    def write(self, path, text):
        dest = self.map(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def package(self, name, version='0.1.0.alpha3-16'):
        self.write(f'/var/lib/pacman/local/{name}-{version}/desc',
                   f'%NAME%\n{name}\n\n%VERSION%\n{version}\n\n')

    def receiver(self, name='8-6', pid='109c', driver='gs_native'):
        for field, value in [('idVendor', '3537'), ('idProduct', pid), ('devnum', '7')]:
            self.write(f'/sys/bus/usb/devices/{name}/{field}', value)
        interface = self.map(f'/sys/bus/usb/devices/{name}:1.0')
        interface.mkdir()
        (interface / 'driver').symlink_to('/sys/bus/usb/drivers/' + driver)


def fixture(root):
    r = FakeReader(root)
    r.write('/etc/os-release', 'ID=garuda\nPRETTY_NAME="Garuda Linux"\nID_LIKE=arch')
    for package in (*PACKAGES, *DEPENDENCIES):
        r.package(package)
    base = f'/usr/lib/modules/{KERNEL}/build'
    r.write(base + '/include/generated/utsrelease.h', f'#define UTS_RELEASE "{KERNEL}"')
    r.write(base + '/include/config/auto.conf', 'CONFIG_CC_IS_CLANG=y\nCONFIG_CC_IS_GCC=n')
    r.write(base + '/Module.symvers', '')
    r.write(base + '/Makefile', '# metadata, never executed')
    r.write('/sys/module/gs_native/version', '0.1.0.alpha3')
    dkms = r.map('/var/lib/dkms/gamesir-native')
    version = dkms / '0.1.0.alpha3'
    (version / KERNEL / ARCH / 'module').mkdir(parents=True)
    (version / KERNEL / ARCH / 'module/gs_native.ko.zst').write_text('fake module')
    (version / 'source').mkdir()
    (dkms / f'kernel-{KERNEL}-{ARCH}').symlink_to(f'0.1.0.alpha3/{KERNEL}/{ARCH}')
    r.map('/sys/bus/usb/devices').mkdir(parents=True)
    return r


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.r = fixture(self.temp.name)
        self.c = Collector(self.r)

    def test_complete_metadata_never_claims_rf_connection(self):
        self.r.receiver()
        s = self.c.collect()
        self.assertEqual(s.facts['headers'], Fact('match', KERNEL))
        self.assertEqual(s.facts['module'], Fact('loaded', '0.1.0.alpha3'))
        self.assertEqual(s.facts['dkms'], Fact('registered', '0.1.0.alpha3'))
        self.assertEqual(s.facts['dependencies'], Fact('metadata'))
        self.assertEqual(s.facts['connection'], Fact('unobserved'))
        self.assertEqual(s.facts['manager'], Fact('restricted'))
        self.assertEqual(s.devices[0].binding, Fact('ok', 'gs_native'))
        for t in CATALOGS.values():
            view = present(s, t)
            self.assertTrue(view['installed'])
            self.assertFalse(view['connected'])
            self.assertFalse(view['canInstall'])
            self.assertFalse(view['canRemove'])
            self.assertNotIn('demo', view['driver'].lower())

    def test_cachyos_is_reviewed_but_arch_like_alone_is_not(self):
        for identity, state in [('cachyos', 'ok'), ('arch', 'unsupported'), ('bazzite', 'unsupported')]:
            self.r.write('/etc/os-release', f'ID={identity}\nPRETTY_NAME="Test Linux"\nID_LIKE=arch')
            self.assertEqual(self.c.collect().facts['support'].state, state)

    def test_other_architecture_does_not_offer_reviewed_path(self):
        self.r.uname = lambda: (KERNEL, 'aarch64')
        self.assertEqual(self.c.collect().facts['support'].state, 'unsupported')

    def test_os_release_is_data_not_shell_and_missing_fields_unknown(self):
        self.assertEqual(os_release('ID=garuda\nPRETTY_NAME="$(touch /tmp/no)"')['PRETTY_NAME'], '$(touch /tmp/no)')
        self.r.write('/etc/os-release', 'ID=garuda\nID=cachyos')
        self.assertEqual(self.c.collect().facts['os'].state, 'unknown')

    def test_os_release_standard_fallback(self):
        self.r.map('/etc/os-release').unlink()
        self.r.write('/usr/lib/os-release', 'ID=cachyos\nPRETTY_NAME="CachyOS"')
        self.assertEqual(self.c.collect().facts['os'], Fact('ok', 'CachyOS'))

    def test_headers_must_match_running_kernel(self):
        self.r.write(f'/usr/lib/modules/{KERNEL}/build/include/generated/utsrelease.h', '#define UTS_RELEASE "old-kernel"')
        self.assertEqual(self.c.collect().facts['headers'], Fact('mismatch', 'old-kernel'))

    def test_prepared_headers_require_symvers_and_unambiguous_compiler(self):
        base = f'/usr/lib/modules/{KERNEL}/build'
        self.r.map(base + '/Module.symvers').unlink()
        self.assertEqual(self.c.collect().facts['headers'].state, 'missing')
        self.r.write(base + '/Module.symvers', '')
        self.r.write(base + '/include/config/auto.conf', 'CONFIG_CC_IS_CLANG=y\nCONFIG_CC_IS_GCC=y')
        self.assertEqual(self.c.collect().facts['headers'].state, 'unknown')

    def test_installed_loaded_and_service_are_independent(self):
        self.r.map('/sys/module/gs_native/version').unlink()
        self.r.map('/sys/module/gs_native').rmdir()
        self.r.service_result = SERVICE.replace('active\n', 'inactive\n').replace('running', 'dead')
        facts = self.c.collect().facts
        self.assertEqual(facts[PACKAGES[0]].state, 'ok')
        self.assertEqual(facts['module'].state, 'absent')
        self.assertIn('inactive/dead', facts['service'].value)
        self.assertEqual(facts['autostart'].value, 'enabled')

    def test_loaded_module_without_version_is_still_loaded(self):
        self.r.map('/sys/module/gs_native/version').unlink()
        self.assertEqual(self.c.collect().facts['module'], Fact('loaded'))

    def test_package_missing_is_not_unknown_database(self):
        folder = self.r.map('/var/lib/pacman/local')
        for p in folder.glob(PACKAGES[0] + '-*/desc'):
            p.unlink(); p.parent.rmdir()
        self.assertEqual(self.c.collect().facts[PACKAGES[0]].state, 'absent')
        self.r.entries_original = self.r.entries
        self.r.entries = lambda path: (_ for _ in ()).throw(FileNotFoundError()) if path == '/var/lib/pacman/local' else self.r.entries_original(path)
        self.assertEqual(self.c.collect().facts[PACKAGES[0]].state, 'not_available')

    def test_missing_build_dependencies_named_without_build(self):
        folder = self.r.map('/var/lib/pacman/local')
        for p in folder.glob('lld-*/desc'):
            p.unlink(); p.parent.rmdir()
        self.assertEqual(self.c.collect().facts['dependencies'], Fact('missing', 'lld'))

    def test_duplicate_package_versions_are_ambiguous(self):
        self.r.package(PACKAGES[0], 'old-1')
        self.assertEqual(self.c.collect().facts[PACKAGES[0]].state, 'unknown')

    def test_concurrent_package_transaction_is_unknown(self):
        original = self.r.entries
        calls = []
        def entries(path):
            result = original(path)
            if path == '/var/lib/pacman/local':
                calls.append(1)
                if len(calls) == 2:
                    result.append('new-entry')
            return result
        self.r.entries = entries
        self.assertEqual(self.c.collect().facts[PACKAGES[0]].state, 'unknown')

    def test_permission_failures_never_become_absent(self):
        original = self.r.entries
        self.r.entries = lambda path: (_ for _ in ()).throw(PermissionError()) if path in ('/var/lib/pacman/local', '/sys/bus/usb/devices') else original(path)
        facts = self.c.collect().facts
        self.assertEqual(facts[PACKAGES[0]].state, 'denied')
        self.assertEqual(facts['receiver'].state, 'denied')

    def test_dkms_registration_not_claimed_for_another_kernel(self):
        self.r.map(f'/var/lib/dkms/gamesir-native/kernel-{KERNEL}-{ARCH}').unlink()
        self.assertEqual(self.c.collect().facts['dkms'].state, 'unregistered')

    def test_dkms_missing_built_module_not_installed(self):
        self.r.map(f'/var/lib/dkms/gamesir-native/0.1.0.alpha3/{KERNEL}/{ARCH}/module/gs_native.ko.zst').unlink()
        self.assertEqual(self.c.collect().facts['dkms'].state, 'unknown')

    def test_dangling_registered_build_is_not_reported_unregistered(self):
        folder = self.r.map(f'/var/lib/dkms/gamesir-native/0.1.0.alpha3/{KERNEL}/{ARCH}/module')
        (folder / 'gs_native.ko.zst').unlink(); folder.rmdir()
        self.assertEqual(self.c.collect().facts['dkms'].state, 'unknown')

    def test_dkms_external_or_wrong_kernel_link_is_rejected(self):
        link = self.r.map(f'/var/lib/dkms/gamesir-native/kernel-{KERNEL}-{ARCH}')
        for target in ('/tmp/0.1.0.alpha3/' + KERNEL + '/' + ARCH, '0.1.0.alpha3/other/' + ARCH):
            link.unlink(); link.symlink_to(target)
            self.assertEqual(self.c.collect().facts['dkms'].state, 'unknown')

    def test_service_timeout_or_denial_does_not_change_other_status(self):
        for error, state in [(TimeoutError(), 'timeout'), (PermissionError(), 'denied'), (OSError(), 'unknown')]:
            self.r.service_result = error
            facts = self.c.collect().facts
            self.assertEqual(facts['service'].state, state)
            self.assertEqual(facts[PACKAGES[0]].state, 'ok')

    def test_incomplete_service_response_unknown(self):
        self.r.service_result = 'ActiveState=active'
        self.assertEqual(self.c.collect().facts['service'].state, 'unknown')

    def test_two_receivers_retained_without_merging_identities(self):
        self.r.receiver('8-6', '109c')
        self.r.receiver('8-5', '105e', 'xpad')
        s = self.c.collect()
        self.assertEqual(len(s.devices), 2)
        self.assertEqual({d.identity.value for d in s.devices}, {'3537:105e', '3537:109c'})
        self.assertEqual(s.facts['connection'].state, 'unobserved')

    def test_other_usb_devices_are_not_gamesir(self):
        self.r.receiver('8-6')
        self.r.write('/sys/bus/usb/devices/8-6/idVendor', '045e')
        self.assertEqual(self.c.collect().facts['receiver'].state, 'absent')

    def test_partial_usb_identity_cannot_prove_absence(self):
        self.r.receiver()
        self.r.map('/sys/bus/usb/devices/8-6/idProduct').unlink()
        self.assertEqual(self.c.collect().facts['receiver'].state, 'partial')

    def test_usb_address_change_invalidates_device(self):
        self.r.receiver()
        original = self.r.text
        seen = []
        def text(path):
            if path.endswith('/devnum'):
                seen.append(1)
                return '7' if len(seen) == 1 else '8'
            return original(path)
        self.r.text = text
        s = self.c.collect()
        self.assertEqual(s.facts['receiver'].state, 'partial')
        self.assertEqual(s.devices[0].identity.state, 'changed')

    def test_stale_and_failed_presentation_never_enable_actions(self):
        for t in CATALOGS.values():
            v = present(self.c.collect(), t, stale=True)
            self.assertEqual(v['sampleState'], t['sample_stale'])
            v = present(None, t, failed=True)
            self.assertEqual(v['notice'], t['read_failed'])
            self.assertFalse(v['canInstall'] or v['canRemove'] or v['loaded'])

    def test_probes_never_open_device_socket_state_or_execute_configs(self):
        original = self.r.text
        reads = []
        def text(path):
            reads.append(path)
            return original(path)
        self.r.text = text
        self.r.receiver()
        with patch('subprocess.Popen', side_effect=AssertionError('No process with fake reader')), \
                patch('socket.socket', side_effect=AssertionError('No socket')):
            self.c.collect()
        self.assertFalse(any(p.startswith(('/dev/', '/run/', '/var/lib/gamesir-native')) for p in reads))
        self.assertFalse(any(p.endswith(('dkms.conf', '.ko', '.ko.zst')) for p in reads))


class TransportTests(unittest.TestCase):
    def run_script(self, script):
        real_popen = subprocess.Popen
        calls = []
        def spawn(argv, **kwargs):
            self.assertEqual(tuple(argv), SERVICE_QUERY)
            self.assertFalse(kwargs['shell'])
            self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
            self.assertEqual(set(kwargs['env']), {'PATH', 'LC_ALL', 'SYSTEMD_PAGER', 'SYSTEMD_COLORS', 'SYSTEMD_OFFLINE'})
            calls.append(argv)
            return real_popen([sys.executable, '-B', '-c', script], **kwargs)
        with patch.object(status.subprocess, 'Popen', side_effect=spawn):
            result = LocalReader().service()
        self.assertEqual(len(calls), 1)
        return result

    def test_only_fixed_show_query_in_clean_environment(self):
        with patch.dict(os.environ, {'LD_PRELOAD': '/not/a/library', 'SYSTEMD_HOST': 'private-host', 'PATH': '/tmp'}):
            self.assertEqual(self.run_script('print("ActiveState=active")'), 'ActiveState=active\n')

    def test_output_limit_stops_child(self):
        with self.assertRaises(ValueError):
            self.run_script('print("x" * 50000)')

    def test_child_failure_is_not_displayed_as_absent(self):
        with self.assertRaises(OSError):
            self.run_script('raise SystemExit(1)')

    def test_time_limit_stops_child_without_retry(self):
        with self.assertRaises(TimeoutError):
            self.run_script('import time; time.sleep(20)')


if __name__ == '__main__':
    unittest.main()
