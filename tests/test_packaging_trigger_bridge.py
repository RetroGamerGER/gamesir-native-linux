#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Optional bridge package tests: temporary files and compiled stubs, no devices."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge_package', ROOT / 'scripts/package_trigger_bridge.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class TriggerBridgePackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'build').mkdir(exist_ok=True)

    def temporary(self):
        temporary = tempfile.TemporaryDirectory(prefix='bridge-package-', dir=ROOT / 'build')
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def copy_sources(self, root):
        for relative in package.SOURCE_FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def synthetic_elf(self, path):
        header = bytearray(64)
        header[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<HH', header, 16, 3, 62)
        path.write_bytes(header)
        return path

    def test_deterministic_archive_has_only_reviewed_sources(self):
        tmp = self.temporary()
        with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': '12345'}):
            first = package.source_archive(tmp / 'first')
            second = package.source_archive(tmp / 'second')
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertFalse(first['installed'])
        prefix = f'{package.PKGNAME}-{package.version()}/'
        with tarfile.open(first['archive']) as archive:
            self.assertEqual(archive.getnames(), [prefix + p for p in package.source_files()])
            for member in archive.getmembers():
                self.assertTrue(member.isfile())
                self.assertEqual((member.uid, member.gid, member.mode, member.mtime),
                                 (0, 0, 0o644, 12345))
                self.assertEqual(archive.extractfile(member).read(),
                                 (ROOT / member.name.removeprefix(prefix)).read_bytes())
        recipe = (tmp / 'first/PKGBUILD').read_text()
        self.assertIn(first['sha256'], recipe)
        self.assertNotIn('@VERSION@', recipe)
        self.assertNotIn('@SOURCE_SHA256@', recipe)
        sums = (tmp / 'first/SHA256SUMS').read_text().splitlines()
        self.assertEqual(sums[1], hashlib.sha256(recipe.encode()).hexdigest() + '  PKGBUILD')

    def test_exact_payload_keeps_kernel_and_desktop_integration_untouched(self):
        tmp = self.temporary()
        shim = self.synthetic_elf(tmp / 'shim.so')
        dest = tmp / 'dest'
        result = package.stage(dest, shim)
        self.assertFalse(result['installed'])
        expected = {target for _, target, _ in package.PAYLOAD} | {package.SHIM_TARGET}
        actual = {p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(result['files'], len(actual))
        self.assertFalse(any(p.is_symlink() for p in dest.rglob('*')))
        for relative, target, mode in package.PAYLOAD:
            self.assertEqual((dest / target).read_bytes(), (ROOT / relative).read_bytes())
            self.assertEqual(stat.S_IMODE((dest / target).stat().st_mode), mode)
        self.assertEqual((dest / package.SHIM_TARGET).read_bytes(), shim.read_bytes())
        self.assertEqual(stat.S_IMODE((dest / package.SHIM_TARGET).stat().st_mode), 0o755)
        for forbidden in ('etc', 'var', 'home', 'usr/src', 'usr/lib/systemd',
                          'usr/lib/sysusers.d', 'usr/share/libalpm', 'usr/share/applications',
                          'usr/lib/gamesir-native/gamesir_haptics.py'):
            self.assertFalse((dest / forbidden).exists())

    def test_recipe_separates_build_checks_and_staging_without_activation(self):
        text = (ROOT / 'packaging/trigger-bridge/PKGBUILD.in').read_text()
        self.assertIn("arch=('x86_64')", text)
        self.assertIn("license=('GPL-2.0-only')", text)
        self.assertIn("'gamesir-native-dkms>=0.1.0.alpha3'", text)
        self.assertIn("'python' 'glibc' 'libusb'", text)
        self.assertIn("makedepends=('gcc')", text)
        self.assertIn('build --dest build/trigger_bridge', text)
        self.assertIn('tests/test_packaging_trigger_bridge.py', text)
        self.assertIn('stage --dest "$pkgdir"', text)
        for forbidden in ('sudo', 'pkexec', 'setpriv', 'modprobe', 'systemctl',
                          'usermod', 'post_install', 'post_upgrade', 'install=',
                          'LD_PRELOAD=', 'launchOptions', '.desktop', '.hook'):
            self.assertNotIn(forbidden, text)
        subprocess.run(['/bin/bash', '-n', str(ROOT / 'packaging/trigger-bridge/PKGBUILD.in')],
                       check=True, capture_output=True, timeout=5)

    def test_missing_or_incomplete_license_and_missing_sources_write_nothing(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        license_path = root / 'COPYING'
        original = license_path.read_bytes()
        for contents in (None, b'GPL-2.0-only\n'):
            if contents is None:
                license_path.unlink()
            else:
                license_path.write_bytes(contents)
            for method in (package.source_archive, package.build):
                with self.subTest(contents=contents, method=method.__name__), self.assertRaises(ValueError):
                    method(tmp / 'dest', root)
                self.assertFalse((tmp / 'dest').exists())
        license_path.write_bytes(original)
        (root / 'tools/trigger_bridge/protocol.py').unlink()
        with self.assertRaises(ValueError):
            package.source_archive(tmp / 'dest', root)
        self.assertFalse((tmp / 'dest').exists())

    def test_unallowlisted_private_and_vendor_files_are_excluded(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        for relative in ('work/config.json', 'outputs/events.jsonl', 'build/vendor.dll',
                         'firmware/app.bin', 'captures/recording.pcapng',
                         'packaging/trigger-bridge/unsafe.hook', 'kernel/gs_native.ko'):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('not public package data')
        result = package.source_archive(tmp / 'archive', root)
        with tarfile.open(result['archive']) as archive:
            self.assertEqual(len(archive.getmembers()), len(package.SOURCE_FILES))
            self.assertTrue(all(member.isfile() for member in archive))

    def test_source_and_destination_symlinks_are_rejected(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        source = root / 'tools/trigger_bridge/devices.py'
        data = source.read_bytes()
        source.unlink()
        source.symlink_to(ROOT / 'tools/trigger_bridge/devices.py')
        with self.assertRaises(ValueError):
            package.source_files(root)
        source.unlink()
        source.write_bytes(data)
        (root / 'tools/trigger_bridge').rename(root / 'tools/redirected')
        (root / 'tools/trigger_bridge').symlink_to('redirected')
        with self.assertRaises(ValueError):
            package.source_files(root)
        for name, target in (('direct', tmp / 'missing'), ('system', Path('/usr'))):
            link = tmp / name
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                package.safe_destination(link)
        (tmp / 'real').mkdir()
        (tmp / 'parent').symlink_to('real')
        with self.assertRaises(ValueError):
            package.safe_destination(tmp / 'parent/child')

    def test_privileged_system_and_existing_destinations_are_preserved(self):
        tmp = self.temporary()
        for path in ('/', '/usr/local/bridge', '/etc/bridge', '/run/bridge',
                     '/var/tmp/bridge', '/dev/bridge', '/proc/bridge', '/sys/bridge'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                package.safe_destination(path)
        with patch.object(package, 'real_effective_uid', return_value=0), self.assertRaises(ValueError):
            package.safe_destination(tmp / 'root')
        for target in (tmp / 'file', tmp / 'directory'):
            if target.name == 'file':
                target.write_text('preserve')
            else:
                target.mkdir()
                (target / 'original').write_text('preserve')
            with self.assertRaises(ValueError):
                package.source_archive(target)
            saved = target if target.is_file() else target / 'original'
            self.assertEqual(saved.read_text(), 'preserve')

    def test_version_and_epoch_reject_injection_and_invalid_values_before_write(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        version_file = root / 'packaging/trigger-bridge/VERSION'
        for value in ('../escape', '', '0.1\ntrailing', '0.1;touch unexpected'):
            version_file.write_text(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                package.source_archive(tmp / 'archive', root)
            self.assertFalse((tmp / 'archive').exists())
        version_file.write_text('0.1.0.alpha1\n')
        for epoch in ('-1', 'invalid', str(0x100000000)):
            with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': epoch}), self.assertRaises(ValueError):
                package.source_archive(tmp / 'archive', root)
            self.assertFalse((tmp / 'archive').exists())

    def test_invalid_shim_is_not_staged_or_executed(self):
        tmp = self.temporary()
        shim = tmp / 'shim.so'
        for data in (b'not ELF', b'\x7fELF', b'\x7fELF\x01\x01\x01' + bytes(57)):
            shim.write_bytes(data)
            with self.subTest(data=data[:7]), self.assertRaises(ValueError):
                package.stage(tmp / 'dest', shim)
            self.assertFalse((tmp / 'dest').exists())
        self.synthetic_elf(shim)
        redirect = tmp / 'redirect.so'
        redirect.symlink_to(shim)
        with self.assertRaises(ValueError):
            package.stage(tmp / 'dest', redirect)

    def test_build_is_device_free_and_fails_without_installing_on_compiler_error(self):
        tmp = self.temporary()
        with self.assertRaises(subprocess.CalledProcessError):
            package.build(tmp / 'failed', compiler='/usr/bin/false')
        self.assertFalse(list((tmp / 'failed').iterdir()))
        result = package.build(tmp / 'compiled')
        self.assertFalse(result['installed'])
        self.assertFalse(result['executed'])
        shim = package.validate_shim(result['shim'])
        self.assertGreater(shim.stat().st_size, 64)
        staged = package.stage(tmp / 'dest', shim)
        self.assertFalse(staged['installed'])

    def test_source_archive_can_be_staged_in_a_clean_extracted_tree(self):
        tmp = self.temporary()
        result = package.source_archive(tmp / 'archive')
        extracted = tmp / 'extracted'
        with tarfile.open(result['archive']) as archive:
            archive.extractall(extracted, filter='data')
        root = extracted / f'{package.PKGNAME}-{package.version()}'
        shim = self.synthetic_elf(tmp / 'shim.so')
        command = [sys.executable, '-B', str(root / 'scripts/package_trigger_bridge.py'),
                   'stage', '--dest', str(tmp / 'dest'), '--shim', str(shim)]
        completed = subprocess.run(command, check=True, text=True, capture_output=True, timeout=10)
        self.assertFalse(json.loads(completed.stdout)['installed'])
        self.assertEqual((tmp / 'dest/usr/share/licenses' / package.PKGNAME / 'COPYING').read_bytes(),
                         (ROOT / 'COPYING').read_bytes())

    def test_wrapper_preserves_arguments_without_invoking_launcher(self):
        tmp = self.temporary()
        stub = tmp / 'probe.py'
        stub.write_text('import json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        wrapper = tmp / 'wrapper'
        source = ROOT / 'packaging/trigger-bridge/gamesir-native-trigger-bridge'
        text = source.read_text().replace('/usr/bin/python', shlex.quote(sys.executable)).replace(
            '/usr/lib/gamesir-native/trigger_bridge/launch.py', shlex.quote(str(stub)))
        wrapper.write_text(text)
        subprocess.run(['/bin/sh', '-n', str(source)], check=True, capture_output=True, timeout=5)
        arguments = ['--help', 'space and quotes "', '$(touch should-not-exist)', '']
        result = subprocess.run(['/bin/sh', str(wrapper), *arguments], text=True,
                                capture_output=True, check=True, timeout=5)
        self.assertEqual(json.loads(result.stdout), arguments)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
