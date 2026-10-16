#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline package and shell-adapter tests. Never invoke the installed Steam client."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('steam_package', ROOT / 'scripts/package_steam.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)
GUID = '03004535373500009c10000053010000'
ZZZ_GUID = '03004535373500005e10000007060000'
INSTALLED_HELPER = '/usr/share/gamesir-native-steam/session.sh'


class SteamPackageTests(unittest.TestCase):
    def temporary(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def copy_sources(self, dest):
        for relative in package.SOURCE_FILES:
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return dest

    def test_reproducible_allowlist_and_archive_permissions(self):
        tmp = self.temporary()
        with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': '12345'}):
            first = package.source_archive(tmp / 'one')
            second = package.source_archive(tmp / 'two')
        self.assertEqual(first['sha256'], second['sha256'])
        prefix = f'gamesir-native-steam-{package.version()}/'
        with tarfile.open(first['archive']) as archive:
            self.assertEqual(archive.getnames(), [prefix + p for p in package.source_files()])
            for member in archive.getmembers():
                self.assertTrue(member.isfile())
                self.assertEqual((member.uid, member.gid, member.mode, member.mtime),
                                 (0, 0, 0o644, 12345))
                self.assertEqual(archive.extractfile(member).read(),
                                 (ROOT / member.name.removeprefix(prefix)).read_bytes())
        recipe = (tmp / 'one/PKGBUILD').read_text()
        self.assertIn(first['sha256'], recipe)
        self.assertNotIn('@VERSION@', recipe)
        self.assertNotIn('@SOURCE_SHA256@', recipe)

    def test_exact_payload_and_source_only_hooks(self):
        dest = self.temporary() / 'dest'
        result = package.stage(dest)
        self.assertEqual(result['files'], 5)
        self.assertFalse(result['installed'])
        expected = {
            'usr/share/gamesir-native-steam/session.sh',
            'etc/xdg/plasma-workspace/env/90-gamesir-native-steam.sh',
            'usr/bin/gamesir-native-steam',
            'usr/share/doc/gamesir-native-steam/STEAM_INTEGRATION.md',
            'usr/share/licenses/gamesir-native-steam/COPYING',
        }
        actual = {p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)
        self.assertFalse(any(p.is_symlink() for p in dest.rglob('*')))
        for source, target, mode in package.PAYLOAD:
            self.assertEqual((dest / target).read_bytes(), (ROOT / source).read_bytes())
            self.assertEqual(stat.S_IMODE((dest / target).stat().st_mode), mode)
        # The package creates neither DKMS/runtime-manager state nor Steam profiles.
        for forbidden in ('usr/src', 'usr/lib/systemd', 'usr/share/libalpm',
                          'usr/share/applications', 'usr/bin/steam', 'home', 'var'):
            self.assertFalse((dest / forbidden).exists())

    def test_arch_recipe_has_no_activation_or_kernel_dependency(self):
        recipe = (ROOT / 'packaging/steam/PKGBUILD.in').read_text()
        self.assertIn("pkgname=gamesir-native-steam", recipe)
        self.assertIn("pkgrel=1", recipe)
        self.assertIn("arch=('any')", recipe)
        self.assertIn("depends=('bash')", recipe)
        self.assertIn("makedepends=('python')", recipe)
        self.assertIn("optdepends=('steam:", recipe)
        for forbidden in ('dkms', 'modprobe', 'systemctl', 'post_install', 'post_upgrade',
                          'install=', '.desktop', 'gamesir-native-dkms'):
            self.assertNotIn(forbidden, recipe)

    def test_missing_input_rejected_before_destination_is_created(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        (root / 'tools/sdl/gamesir-plasma-env.sh').unlink()
        for method in (package.stage, package.source_archive):
            with self.subTest(method=method.__name__), self.assertRaises(ValueError):
                method(tmp / 'dest', root)
            self.assertFalse((tmp / 'dest').exists())

    def test_file_and_parent_symlinks_rejected(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        helper = root / 'tools/sdl/gamesir-plasma-env.sh'
        original = helper.read_bytes()
        helper.unlink()
        helper.symlink_to(ROOT / 'tools/sdl/gamesir-plasma-env.sh')
        with self.assertRaises(ValueError):
            package.source_files(root)
        helper.unlink()
        helper.write_bytes(original)
        (root / 'tools/sdl').rename(root / 'tools/sdl-real')
        (root / 'tools/sdl').symlink_to('sdl-real')
        with self.assertRaises(ValueError):
            package.source_files(root)

    def test_collision_is_not_overwritten(self):
        tmp = self.temporary()
        for target in (tmp / 'file', tmp / 'directory'):
            if target.name == 'file':
                target.write_text('preserve me')
            else:
                target.mkdir()
                (target / 'original').write_text('preserve me')
            for method in (package.stage, package.source_archive):
                with self.subTest(target=target.name, method=method.__name__), \
                        self.assertRaises(ValueError):
                    method(target)
            saved = target if target.is_file() else target / 'original'
            self.assertEqual(saved.read_text(), 'preserve me')

    def test_system_privileged_and_redirected_destinations_rejected(self):
        tmp = self.temporary()
        for target in ('/', '/usr/local/gamesir', '/etc/example', '/var/tmp/example',
                       '/run/example', '/sys/example', '/dev/example'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                package.safe_destination(target)
        for target in (tmp / 'empty-link', tmp / 'system-link'):
            target.symlink_to(tmp / 'missing' if target.name == 'empty-link' else '/usr')
            with self.assertRaises(ValueError):
                package.safe_destination(target)
        with patch.object(package, 'real_effective_uid', return_value=0), \
                self.assertRaises(ValueError):
            package.safe_destination(tmp / 'new')

    def test_invalid_version_and_epoch_do_not_write(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        for value in ('../escape', '0.1\nhello', '', '0.1;touch unexpected'):
            (root / 'packaging/steam/VERSION').write_text(value)
            for method in (package.source_archive, package.stage):
                with self.subTest(value=value, method=method.__name__), self.assertRaises(ValueError):
                    method(tmp / 'dest', root)
                self.assertFalse((tmp / 'dest').exists())
        (root / 'packaging/steam/VERSION').write_text('0.1.0.alpha1\n')
        for epoch in ('-1', 'invalid'):
            with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': epoch}), self.assertRaises(ValueError):
                package.source_archive(tmp / 'dest', root)
            self.assertFalse((tmp / 'dest').exists())

    def test_unallowlisted_files_are_not_packaged(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        for relative in ('private.txt', 'kernel/driver.ko', 'packaging/steam/evil.hook',
                         'packaging/steam/installer.exe', 'captures/raw.pcapng'):
            file = root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('must stay outside')
        archive = package.source_archive(tmp / 'archive', root)
        with tarfile.open(archive['archive']) as handle:
            self.assertEqual(len(handle.getnames()), len(package.SOURCE_FILES))
        package.stage(tmp / 'dest', root)
        self.assertEqual(sum(p.is_file() for p in (tmp / 'dest').rglob('*')), 5)

    def test_shell_syntax(self):
        for relative in ('tools/sdl/gamesir-plasma-env.sh', 'packaging/steam/plasma-env.sh',
                         'packaging/steam/gamesir-native-steam'):
            with self.subTest(path=relative):
                subprocess.run(['/bin/sh', '-n', str(ROOT / relative)], check=True,
                               capture_output=True, timeout=5)

    def shell_fixture(self, *, missing=False):
        """Substitute only installed absolute paths, with a fake Steam executable."""
        tmp = self.temporary()
        helper = tmp / 'session.sh'
        if not missing:
            shutil.copyfile(ROOT / 'tools/sdl/gamesir-plasma-env.sh', helper)
        fake = tmp / 'steam-stub'
        fake.write_text('#!' + sys.executable + '\nimport json,os,sys\n'
                        'print(json.dumps({"argv":sys.argv[1:],"env":dict(os.environ)}))\n')
        fake.chmod(0o755)
        for name in ('gamesir-native-steam', 'plasma-env.sh'):
            text = (ROOT / 'packaging/steam' / name).read_text()
            text = text.replace(INSTALLED_HELPER, shlex.quote(str(helper)))
            text = text.replace('/usr/bin/steam', shlex.quote(str(fake)))
            (tmp / name).write_text(text)
        return tmp

    def test_wrapper_preserves_arguments_and_launches_only_stub(self):
        tmp = self.shell_fixture()
        args = ['steam://rungameid/123', 'spaces and quotes "', '$(touch should-not-exist)', '']
        result = subprocess.run(['/bin/sh', str(tmp / 'gamesir-native-steam'), *args],
                                env={'PATH': '/usr/bin:/bin', 'SENTINEL': 'preserved'},
                                text=True, capture_output=True, check=True, timeout=5)
        data = json.loads(result.stdout)
        self.assertEqual(data['argv'], args)
        self.assertEqual(data['env']['SENTINEL'], 'preserved')
        mapping = data['env']['SDL_GAMECONTROLLERCONFIG']
        self.assertEqual(len(mapping.splitlines()), 2)
        for guid, line in zip((GUID, ZZZ_GUID), mapping.splitlines()):
            self.assertTrue(line.startswith(guid + ',GameSir G7 Pro,'))
            for field in ('paddle1:b12,', 'paddle2:b11,', 'paddle3:b14,', 'paddle4:b13,'):
                self.assertIn(field, line)
        self.assertEqual(result.stderr, '')

    def test_wrapper_preserves_explicit_optout(self):
        tmp = self.shell_fixture()
        for hints in ({'GAMESIR_NATIVE_STEAM_DISABLE': '1'},
                      {'SDL_GAMECONTROLLERCONFIG_FILE': '/not-read'}):
            result = subprocess.run(['/bin/sh', str(tmp / 'gamesir-native-steam')],
                                    env={'PATH': '/usr/bin:/bin', **hints}, text=True,
                                    capture_output=True, check=True, timeout=5)
            env = json.loads(result.stdout)['env']
            for key, value in hints.items():
                self.assertEqual(env[key], value)
            if 'SDL_GAMECONTROLLERCONFIG' not in hints:
                self.assertNotIn('SDL_GAMECONTROLLERCONFIG', env)

    def test_wrapper_and_plasma_preserve_each_conflicting_family(self):
        tmp = self.shell_fixture()
        standard = '03000000373500009C10000000000000,My standard,a:b15,'
        zzz = '0300abCd373500005E10000001230000,My ZZZ,a:b7,'
        for prior, missing in ((standard, ZZZ_GUID), (zzz, GUID),
                               (standard + '\n' + zzz, None)):
            with self.subTest(prior=prior):
                hints = {'PATH': '/usr/bin:/bin', 'SDL_GAMECONTROLLERCONFIG': prior}
                wrapper = subprocess.run(['/bin/sh', str(tmp / 'gamesir-native-steam')],
                                         env=hints, text=True, capture_output=True,
                                         check=True, timeout=5)
                value = json.loads(wrapper.stdout)['env']['SDL_GAMECONTROLLERCONFIG']
                command = '. "$1"; . "$1"; printf "%s" "$SDL_GAMECONTROLLERCONFIG"'
                plasma = subprocess.run(['/bin/sh', '-c', command, 'adapter-test',
                                         str(tmp / 'plasma-env.sh')],
                                        env=hints, text=True, capture_output=True,
                                        check=True, timeout=5)
                self.assertEqual(plasma.stdout, value)
                if missing is None:
                    self.assertEqual(value, prior)
                else:
                    self.assertTrue(value.startswith(prior + '\n' + missing + ','))
                    self.assertEqual(len(value.splitlines()), 2)
                self.assertEqual(wrapper.stderr + plasma.stderr, '')

    def test_missing_helper_skips_adapter_but_blocks_explicit_wrapper(self):
        tmp = self.shell_fixture(missing=True)
        command = '. "$1"; printf "%s" "${SDL_GAMECONTROLLERCONFIG-unset}"'
        result = subprocess.run(['/bin/sh', '-c', command, 'adapter-test', str(tmp / 'plasma-env.sh')],
                                env={'PATH': '/usr/bin:/bin'}, text=True,
                                capture_output=True, check=True, timeout=5)
        self.assertEqual(result.stdout, 'unset')
        result = subprocess.run(['/bin/sh', str(tmp / 'gamesir-native-steam')],
                                env={'PATH': '/usr/bin:/bin'}, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('missing readable session helper', result.stderr)

    def test_plasma_adapter_sources_in_current_child_shell_without_launch(self):
        tmp = self.shell_fixture()
        command = '. "$1"; . "$1"; printf "%s" "$SDL_GAMECONTROLLERCONFIG"'
        result = subprocess.run(['/bin/sh', '-c', command, 'adapter-test', str(tmp / 'plasma-env.sh')],
                                env={'PATH': '/usr/bin:/bin'}, text=True,
                                capture_output=True, check=True, timeout=5)
        self.assertEqual(result.stdout.count(GUID + ','), 1)
        self.assertEqual(result.stdout.count(ZZZ_GUID + ','), 1)
        self.assertEqual(len(result.stdout.splitlines()), 2)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    (ROOT / 'build').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
