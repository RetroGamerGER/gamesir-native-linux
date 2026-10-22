#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline launcher/staging/desktop safety. No live GUI or user integration."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_control_center as package


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_optional_repl_dbm_and_test_adapters_are_excluded_before_link_closure(self):
        directory = self.root / 'lib-dynload'; directory.mkdir()
        omitted = ('readline.cpython-314.so', '_gdbm.cpython-314.so', '_dbm.cpython-314.so',
                   '_tkinter.cpython-314.so', '_testinternalcapi.cpython-314.so', 'xxlimited.so')
        retained = ('_ssl.cpython-314.so', '_sqlite3.cpython-314.so', '_json.cpython-314.so',
                    '_hashlib.cpython-314.so', 'zlib.cpython-314.so', '_socket.cpython-314.so')
        for name in omitted + retained: (directory / name).write_bytes(name.encode())
        package.remove_unused_stdlib_extensions(directory)
        self.assertEqual({p.name for p in directory.iterdir()}, set(retained))
        for name in retained: self.assertEqual((directory / name).read_bytes(), name.encode())

    def test_extension_pruning_does_not_remove_python_sources_or_other_folders(self):
        directory = self.root / 'lib-dynload'; directory.mkdir()
        (self.root / 'readline.py').write_text('retained standard-library source')
        (self.root / 'dbm').mkdir()
        package.remove_unused_stdlib_extensions(directory)
        self.assertTrue((self.root / 'readline.py').is_file())
        self.assertTrue((self.root / 'dbm').is_dir())

    def test_runtime_mapping_proof_preserves_spaces_and_still_detects_host_paths(self):
        spec = importlib.util.spec_from_file_location('bundle_entry', package.ASSETS / 'entry.py')
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        bundled = '/tmp/folder with spaces/usr/lib/libQt6Core.so.6'
        host = '/usr/lib/libpython3.14.so.1.0'
        maps = (f'1000-2000 r-xp 00000000 08:01 100 {bundled}\n'
                f'2000-3000 r--p 00000000 08:01 101 {host}\n'
                '3000-4000 rw-p 00000000 00:00 0 [heap]\n')
        self.assertEqual(entry.loaded_runtime_paths(maps), {bundled, host})
        self.assertFalse(all(Path(p).is_relative_to('/tmp/folder with spaces')
                             for p in entry.loaded_runtime_paths(maps)))

    def test_assets_are_separate_from_driver_and_desktop_is_read_only(self):
        self.assertEqual(package.version(), '0.1.0.alpha2')
        source = (package.ASSETS / 'gamesir-control-center.desktop').read_text()
        for expected in ('Type=Application', 'Exec=gamesir-control-center',
                         'Icon=gamesir-control-center', 'Terminal=false', 'nur lesend'):
            self.assertIn(expected, source)
        for forbidden in ('pkexec', 'sudo', 'Autostart', 'MimeType=', 'DBusActivatable=', '%f', '%u'):
            self.assertNotIn(forbidden, source)
        if Path('/usr/bin/desktop-file-validate').is_file():
            package.run(['/usr/bin/desktop-file-validate', str(package.ASSETS / 'gamesir-control-center.desktop')])

    def test_app_run_uses_isolated_python_and_no_exported_bundled_library_path(self):
        text = (package.ASSETS / 'AppRun').read_text()
        self.assertIn(' -I -B ', text)
        self.assertIn('--library-path', text)
        self.assertNotIn('export LD_LIBRARY_PATH', text)
        self.assertIn('unset PYTHONHOME PYTHONPATH', text)
        self.assertNotIn('systemctl', '\n'.join(line for line in text.splitlines() if not line.startswith('#')))
        for forbidden in ('pacman ', 'sudo ', 'pkexec ', 'xdg-desktop-menu ', 'curl ', 'wget '):
            self.assertNotIn(forbidden, text)

    def test_profile_and_system_destinations_are_rejected(self):
        for path in ('/usr/share/applications/fake', '/etc/fake', Path.home(),
                     Path.home() / '.local/share/applications/fake', Path.home() / '.config/fake',
                     Path.home() / 'Desktop/fake'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                package.safe_output(path)
        with patch.dict(os.environ, {'XDG_DATA_HOME': str(self.root / 'user-data')}):
            with self.assertRaises(ValueError):
                package.safe_output(self.root / 'user-data/applications')

    def test_existing_or_redirected_destination_is_preserved(self):
        output = self.root / 'out'; output.mkdir(); (output / 'mine').write_text('keep')
        with self.assertRaises(ValueError):
            package.safe_output(output)
        link = self.root / 'link'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            package.safe_output(link / 'new')
        self.assertEqual((output / 'mine').read_text(), 'keep')

    def test_root_staging_is_refused(self):
        with patch('package_alpha.real_effective_uid', return_value=0), self.assertRaises(ValueError):
            package.safe_output(self.root / 'root-output')

    def test_no_install_remove_or_network_cli_exists(self):
        for action in ('install', 'remove', 'download', 'activate'):
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/package_control_center.py'), action],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)

    def test_exec_path_rejects_controls_and_relative_names(self):
        for value in ('relative.AppImage', '/tmp/new\nline.AppImage', '/tmp/null\0.AppImage'):
            with self.assertRaises(ValueError):
                package.quote_exec(value)

    @unittest.skipUnless(Path('/usr/bin/desktop-file-validate').is_file(), 'Optional desktop validator absent')
    def test_staged_receipt_and_rollback_are_bounded_and_nonmutating(self):
        target = self.root / 'payload'
        result = package.desktop_payload(self.root / 'GameSir with spaces.AppImage', target)
        self.assertFalse(result['installed'])
        before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
        review = package.removal_preview(target)
        self.assertEqual(len(review['matching']), 2)
        self.assertEqual(review['preserve'], [])
        self.assertEqual(before, {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()})
        desktop = target / 'applications/gamesir-control-center.desktop'
        desktop.write_text(desktop.read_text() + '# user modification\n')
        review = package.removal_preview(target)
        self.assertIn('applications/gamesir-control-center.desktop', review['preserve'])
        self.assertTrue(desktop.exists())

    @unittest.skipUnless(Path('/usr/bin/desktop-file-validate').is_file(), 'Optional desktop validator absent')
    def test_removal_preview_retains_links_missing_files_and_unrelated_content(self):
        target = self.root / 'payload'
        package.desktop_payload(self.root / 'test.AppImage', target)
        desktop = target / 'applications/gamesir-control-center.desktop'
        desktop.unlink(); desktop.symlink_to(self.root / 'outside')
        icon = target / 'icons/hicolor/scalable/apps/gamesir-control-center.svg'; icon.unlink()
        (target / 'unrelated').write_text('keep')
        result = package.removal_preview(target)
        self.assertEqual(result['preserve'], ['applications/gamesir-control-center.desktop'])
        self.assertEqual(result['missing'], ['icons/hicolor/scalable/apps/gamesir-control-center.svg'])
        self.assertEqual((target / 'unrelated').read_text(), 'keep')

    def test_malicious_removal_receipt_has_no_effect(self):
        root = self.root / 'payload'; root.mkdir()
        (root / 'DESKTOP_PAYLOAD.json').write_text(json.dumps({'schema': 1, 'installed': False,
                                                             'files': {'../../escape': 'a'*64}}))
        with self.assertRaises(ValueError):
            package.removal_preview(root)

    @unittest.skipUnless(Path('/usr/bin/gio').is_file() and Path('/usr/bin/desktop-file-validate').is_file(),
                         'Optional GIO desktop parser absent')
    def test_real_desktop_exec_parser_handles_quotes_dollars_backticks_and_percent(self):
        folder = self.root / 'folder with spaces'; folder.mkdir()
        executable = folder / 'name "quoted" $cash `tick` 100%.AppImage'
        result_file = self.root / 'launched.json'
        executable.write_text('#!/usr/bin/python3\nimport json,os,sys\n'
                              'open(os.environ["CC_TEST_RESULT"],"w").write(json.dumps(sys.argv))\n')
        executable.chmod(0o755)
        payload = self.root / 'payload'
        package.desktop_payload(executable, payload)
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.root), 'CC_TEST_RESULT': str(result_file),
               'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/nonexistent-gamesir-test-bus'}
        result = subprocess.run(['/usr/bin/gio', 'launch', str(payload / 'applications/gamesir-control-center.desktop')],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        for _ in range(100):
            if result_file.exists():
                break
            time.sleep(0.01)
        self.assertTrue(result_file.exists())
        self.assertEqual(json.loads(result_file.read_text()), [str(executable)])

    def runtime(self):
        data = bytearray(132)
        data[:11] = b'\x7fELF\x02\x01\x01\x00AI\x02'
        struct.pack_into('<H', data, 18, 62)
        struct.pack_into('<Q', data, 40, 64)
        struct.pack_into('<HH', data, 58, 64, 1)
        data[128:] = b'hsqs'
        path = self.root / 'runtime.AppImage'; path.write_bytes(data)
        return path, bytes(data)

    def test_runtime_pin_and_elf_boundary_are_checked_without_execution(self):
        path, data = self.runtime()
        with patch.object(package, 'run', side_effect=AssertionError('No execution')):
            self.assertEqual(package.runtime_from_appimage(path, package.sha(data)), data[:128])
            for bad_hash in ('', 'bad', 'f'*64):
                with self.assertRaises(ValueError):
                    package.runtime_from_appimage(path, bad_hash)
        changed = bytearray(data); struct.pack_into('<H', changed, 18, 183); path.write_bytes(changed)
        with self.assertRaises(ValueError):
            package.runtime_from_appimage(path, package.sha(changed))

    def test_bad_runtime_table_or_missing_squash_is_refused(self):
        path, data = self.runtime()
        for field, value, fmt in ((40, 99999, '<Q'), (58, 1, '<H'), (60, 0, '<H')):
            changed = bytearray(data); struct.pack_into(fmt, changed, field, value); path.write_bytes(changed)
            with self.assertRaises(ValueError):
                package.runtime_from_appimage(path, package.sha(changed))
        changed = data[:-4] + b'none'; path.write_bytes(changed)
        with self.assertRaises(ValueError):
            package.runtime_from_appimage(path, package.sha(changed))

    def test_unknown_appdir_and_invalid_epoch_do_not_execute_builder(self):
        with patch.object(package, 'run', side_effect=AssertionError('No execution')):
            for epoch in (-1, True, 0x100000000):
                with self.assertRaises(ValueError):
                    package.image(self.root, self.root / 'out', self.root / 'missing', 'a'*64, epoch=epoch)
            with self.assertRaises(ValueError):
                package.image(self.root, self.root / 'out', self.root / 'missing', 'a'*64)

    def appdir(self):
        root = self.root / 'appdir'; root.mkdir()
        (root / 'AppRun').write_bytes(b'#!/bin/sh\nexit 0\n')
        (root / 'gamesir-control-center.svg').write_bytes(b'<svg/>')
        (root / '.DirIcon').symlink_to('gamesir-control-center.svg')
        files = {p.name: package.sha(p.read_bytes()) for p in root.iterdir() if p.is_file() and not p.is_symlink()}
        (root / 'BUILD_INPUTS.json').write_text(json.dumps({'files': files}))
        return root

    def test_changed_or_redirected_appdir_is_refused_before_compression(self):
        appdir = self.appdir()
        (appdir / 'AppRun').write_text('changed')
        with patch.object(package, 'run', side_effect=AssertionError('No compression')):
            with self.assertRaises(ValueError):
                package.image(appdir, self.root / 'out', self.root / 'missing', 'a'*64)
        self.assertFalse((self.root / 'out').exists())

    def test_image_uses_reproducible_compression_and_records_runtime_pin(self):
        appdir = self.appdir(); runtime, data = self.runtime(); calls = []
        def compress(argv, **kwargs):
            calls.append(argv)
            self.assertEqual(argv[0], '/usr/bin/mksquashfs')
            self.assertIn('-noappend', argv)
            self.assertIn('-all-root', argv)
            self.assertIn('-no-xattrs', argv)
            self.assertEqual(argv[argv.index('-mkfs-time')+1], '123')
            Path(argv[2]).write_bytes(b'synthetic squash bytes')
            return ''
        with patch.object(package, 'run', side_effect=compress):
            target = package.image(appdir, self.root / 'out', runtime, package.sha(data), epoch=123)
        self.assertEqual(len(calls), 1)
        self.assertEqual(target.read_bytes(), data[:128] + b'synthetic squash bytes')
        report = json.loads((target.parent / 'BUILD_REPORT.json').read_text())
        self.assertEqual(report['runtime_sha256'], package.sha(data[:128]))
        self.assertFalse(report['installed'] or report['release_ready'])


if __name__ == '__main__':
    unittest.main()
