#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline Gamescope package tests: private files and an artificial launcher only."""
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
spec = importlib.util.spec_from_file_location('gamescope_package', ROOT / 'scripts/package_steam.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)
PROFILE = 'gamescope'
HELPER = '/usr/share/gamesir-native-steam/session.sh'
VENDOR = '/usr/lib/steamos/steam-launcher'
WRAPPER = '/usr/lib/gamesir-native-steam/gamescope-launcher'
DROPIN = 'usr/lib/systemd/user/steam-launcher.service.d/50-gamesir-native.conf'


class GamescopePackageTests(unittest.TestCase):
    def temporary(self):
        (ROOT / 'build').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def copy_sources(self, target):
        for relative in package.GAMESCOPE_SOURCE_FILES:
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, output)
        return target

    def test_reproducible_narrow_archive_and_correct_recipe(self):
        tmp = self.temporary()
        with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': '2468'}):
            first = package.source_archive(tmp / 'one', component=PROFILE)
            second = package.source_archive(tmp / 'two', component=PROFILE)
        self.assertEqual(first['sha256'], second['sha256'])
        prefix = f'gamesir-native-steam-gamescope-{package.version(component=PROFILE)}/'
        with tarfile.open(first['archive']) as archive:
            self.assertEqual(archive.getnames(),
                             [prefix + p for p in package.source_files(component=PROFILE)])
            for member in archive.getmembers():
                self.assertTrue(member.isfile())
                self.assertEqual((member.uid, member.gid, member.mode, member.mtime),
                                 (0, 0, 0o644, 2468))
                self.assertEqual(archive.extractfile(member).read(),
                                 (ROOT / member.name.removeprefix(prefix)).read_bytes())
        recipe = (tmp / 'one/PKGBUILD').read_text()
        self.assertIn(first['sha256'], recipe)
        self.assertNotIn('@VERSION@', recipe)
        self.assertNotIn('@SOURCE_SHA256@', recipe)
        self.assertIn('gamesir-native-steam-gamescope', recipe)
        self.assertFalse(first['installed'])

    def test_four_payload_files_no_shared_mapping_or_vendor_overwrite(self):
        target = self.temporary() / 'stage'
        result = package.stage(target, component=PROFILE)
        expected = {
            WRAPPER.removeprefix('/'), DROPIN,
            'usr/share/doc/gamesir-native-steam-gamescope/STEAM_GAMESCOPE.md',
            'usr/share/licenses/gamesir-native-steam-gamescope/COPYING',
        }
        self.assertEqual({p.relative_to(target).as_posix() for p in target.rglob('*')
                          if p.is_file()}, expected)
        self.assertEqual(result['files'], 4)
        self.assertFalse(result['installed'])
        for source, output, mode in package.GAMESCOPE_PAYLOAD:
            self.assertEqual((target / output).read_bytes(), (ROOT / source).read_bytes())
            self.assertEqual(stat.S_IMODE((target / output).stat().st_mode), mode)
        self.assertFalse(any(p.is_symlink() for p in target.rglob('*')))
        for path in (HELPER, VENDOR, '/usr/lib/systemd/user/steam-launcher.service',
                     '/etc', '/var', '/home', '/usr/src', '/usr/bin/steam'):
            self.assertFalse((target / path.lstrip('/')).exists())

    def test_recipe_dependencies_without_activation(self):
        recipe = (ROOT / 'packaging/steam-gamescope/PKGBUILD.in').read_text()
        self.assertIn("depends=('gamesir-native-steam>=0.1.0.alpha2' 'gamescope-session-cachyos')", recipe)
        self.assertIn("pkgrel=1", recipe)
        self.assertIn("arch=('any')", recipe)
        self.assertIn('stage --component gamescope --dest "$pkgdir"', recipe)
        self.assertIn('tests/test_packaging_gamescope.py', recipe)
        for forbidden in ('dkms', 'modprobe', 'systemctl', 'post_install', 'post_upgrade',
                          'install=', '.desktop', 'gamesir-native-dkms'):
            self.assertNotIn(forbidden, recipe)

    def test_missing_redirected_and_private_sources_fail_closed(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        helper = root / 'packaging/steam-gamescope/gamescope-launcher'
        original = helper.read_bytes()
        helper.unlink()
        for method in (package.stage, package.source_archive):
            with self.assertRaises(ValueError):
                method(tmp / 'dest', root, component=PROFILE)
            self.assertFalse((tmp / 'dest').exists())
        helper.symlink_to(ROOT / 'packaging/steam-gamescope/gamescope-launcher')
        with self.assertRaises(ValueError):
            package.source_files(root, component=PROFILE)
        helper.unlink()
        helper.write_bytes(original)
        (root / 'packaging/steam-gamescope').rename(root / 'packaging/moved')
        (root / 'packaging/steam-gamescope').symlink_to('moved')
        with self.assertRaises(ValueError):
            package.source_files(root, component=PROFILE)

    def test_unallowlisted_files_not_in_source_or_package(self):
        tmp = self.temporary()
        root = self.copy_sources(tmp / 'sources')
        for name in ('secrets.txt', 'packaging/steam-gamescope/evil.install',
                     'packaging/steam-gamescope/raw.pcapng', 'kernel/private.ko'):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('must remain excluded')
        result = package.source_archive(tmp / 'archive', root, component=PROFILE)
        with tarfile.open(result['archive']) as archive:
            self.assertEqual(len(archive.getnames()), len(package.GAMESCOPE_SOURCE_FILES))
        result = package.stage(tmp / 'stage', root, component=PROFILE)
        self.assertEqual(result['files'], 4)

    def test_destination_and_invalid_metadata_guards_are_shared(self):
        tmp = self.temporary()
        target = tmp / 'collision'
        target.mkdir()
        (target / 'keep').write_text('untouched')
        for method in (package.stage, package.source_archive):
            for bad in (target, '/usr/local/forbidden', '/etc/forbidden', '/dev/forbidden'):
                with self.subTest(method=method.__name__, path=bad), self.assertRaises(ValueError):
                    method(bad, component=PROFILE)
            with patch.object(package, 'real_effective_uid', return_value=0), self.assertRaises(ValueError):
                method(tmp / 'root-build', component=PROFILE)
            with self.assertRaises(ValueError):
                method(tmp / 'unknown', component='../bad')
        self.assertEqual((target / 'keep').read_text(), 'untouched')
        self.assertFalse((tmp / 'unknown').exists())
        root = self.copy_sources(tmp / 'source')
        (root / 'packaging/steam-gamescope/VERSION').write_text('../bad')
        with self.assertRaises(ValueError):
            package.stage(tmp / 'bad-version', root, component=PROFILE)
        self.assertFalse((tmp / 'bad-version').exists())
        with patch.dict(os.environ, {'SOURCE_DATE_EPOCH': '-1'}), self.assertRaises(ValueError):
            package.source_archive(tmp / 'bad-epoch', component=PROFILE)
        self.assertFalse((tmp / 'bad-epoch').exists())

    def test_profile_cli_stage(self):
        dest = self.temporary() / 'stage'
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/package_steam.py'),
                                 'stage', '--component', PROFILE, '--dest', str(dest)],
                                text=True, capture_output=True, check=True, timeout=5)
        self.assertEqual(json.loads(result.stdout)['files'], 4)
        self.assertEqual(result.stderr, '')

    def fixture(self, *, helper=True, vendor=True, executable=True):
        tmp = self.temporary()
        helper_path, vendor_path = tmp / 'helper with space.sh', tmp / 'vendor with space'
        if helper:
            helper_path.write_text('export FROM_SHARED_HELPER=yes\n'
                                   'export SDL_GAMECONTROLLERCONFIG="${SDL_GAMECONTROLLERCONFIG-fixture}"\n')
        if vendor:
            vendor_path.write_text('#!' + sys.executable + '\nimport json,os,sys\n'
                                   'print(json.dumps({"argv":sys.argv[1:],"pid":os.getpid(),'
                                   '"env":dict(os.environ)}),flush=True)\n'
                                   'sys.exit(int(os.environ.get("STUB_EXIT", "0")))\n')
            vendor_path.chmod(0o755 if executable else 0o644)
        text = (ROOT / 'packaging/steam-gamescope/gamescope-launcher').read_text()
        text = text.replace(HELPER, shlex.quote(str(helper_path)))
        text = text.replace(VENDOR, shlex.quote(str(vendor_path)))
        path = tmp / 'wrapper'
        path.write_text(text)
        return tmp, path

    def test_wrapper_exec_preserves_pid_args_environment_and_exit(self):
        tmp, wrapper = self.fixture()
        marker = tmp / 'must not exist'
        args = ['-gamepadui', 'space and "quotes"', '', '$(touch ' + shlex.quote(str(marker)) + ')']
        env = {'PATH': '/usr/bin:/bin', 'SENTINEL': 'keep', 'SDL_GAMECONTROLLERCONFIG': 'user-data',
               'STUB_EXIT': '23', 'STEAM_FOO': 'preserve'}
        child = subprocess.Popen(['/bin/sh', str(wrapper), *args], env=env,
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = child.communicate(timeout=5)
        data = json.loads(stdout)
        self.assertEqual(child.returncode, 23)
        self.assertEqual(data['pid'], child.pid)
        self.assertEqual(data['argv'], args)
        self.assertEqual(data['env']['FROM_SHARED_HELPER'], 'yes')
        for key, value in env.items():
            self.assertEqual(data['env'][key], value)
        self.assertFalse(marker.exists())
        self.assertEqual(stderr, '')

    def test_missing_helper_warns_but_executes_vendor(self):
        _, wrapper = self.fixture(helper=False)
        result = subprocess.run(['/bin/sh', str(wrapper), 'argument'],
                                env={'PATH': '/usr/bin:/bin', 'SDL_GAMECONTROLLERCONFIG': 'user-data'},
                                text=True, capture_output=True, check=True, timeout=5)
        data = json.loads(result.stdout)
        self.assertEqual(data['argv'], ['argument'])
        self.assertEqual(data['env']['SDL_GAMECONTROLLERCONFIG'], 'user-data')
        self.assertNotIn('FROM_SHARED_HELPER', data['env'])
        self.assertIn('mapping helper unavailable; continuing with vendor launcher', result.stderr)

    def test_missing_or_nonexecutable_vendor_stops_with_clear_error(self):
        for options in ({'vendor': False}, {'executable': False}):
            _, wrapper = self.fixture(**options)
            with self.subTest(options=options):
                result = subprocess.run(['/bin/sh', str(wrapper)], env={'PATH': '/usr/bin:/bin'},
                                        text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 127)
                self.assertEqual(result.stdout, '')
                self.assertIn('missing executable vendor Steam launcher', result.stderr)

    def test_dropin_only_replaces_execstart_and_retains_vendor_properties(self):
        # Small declarative fixture of the observed launcher contract; no
        # private snapshot path and no connection to a systemd user manager.
        vendor = '''[Unit]
Description=Steam Launcher
After=graphical-session.target
PartOf=graphical-session.target
After=xdg-desktop-portal.service
[Service]
ExecStart=/usr/lib/steamos/steam-launcher
ExecStartPre=/usr/lib/steamos/steam-short-session-tracker --track-started
ExecStopPost=/usr/lib/steamos/steam-short-session-tracker --track-stopped
ExecStop=/bin/bash -c 'kill -TERM $(pgrep -P $MAINPID || echo $MAINPID)'
KillSignal=SIGCONT
KillMode=mixed
TimeoutStopSec=60
Type=exec
EnvironmentFile=%t/gamescope-environment
'''
        dropin = (ROOT / 'packaging/steam-gamescope/50-gamesir-native.conf').read_text()
        lines = [line.strip() for line in dropin.splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(lines, ['[Service]', 'ExecStart=', 'ExecStart=' + WRAPPER])

        def merge(*fragments):
            properties, section = {}, ''
            for text in fragments:
                for line in text.splitlines():
                    if line.startswith('['):
                        section = line
                    elif '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        target = (section, key)
                        if key == 'ExecStart' and value == '':
                            properties[target] = []
                        else:
                            properties.setdefault(target, []).append(value)
            return properties

        before, after = merge(vendor), merge(vendor, dropin)
        self.assertEqual(after.pop(('[Service]', 'ExecStart')), [WRAPPER])
        self.assertEqual(before.pop(('[Service]', 'ExecStart')), [VENDOR])
        self.assertEqual(after, before)
        # Delegate to the vendor: its Steam flags/devkit branch must not be copied.
        wrapper = (ROOT / 'packaging/steam-gamescope/gamescope-launcher').read_text()
        self.assertIn('exec ' + VENDOR + ' "$@"', wrapper)
        for forbidden in ('-steamos3', '-gamepadui', 'devkit-game', 'systemctl', 'sudo'):
            self.assertNotIn(forbidden, wrapper)

    def test_shell_syntax_and_no_install_actions(self):
        wrapper = ROOT / 'packaging/steam-gamescope/gamescope-launcher'
        subprocess.run(['/bin/sh', '-n', str(wrapper)], text=True,
                       capture_output=True, check=True, timeout=5)
        self.assertEqual(set(package.COMPONENTS), {'steam', 'gamescope'})
        self.assertEqual(package.COMPONENTS['steam'][2], package.SOURCE_FILES)
        self.assertEqual(package.COMPONENTS['steam'][3], package.PAYLOAD)


if __name__ == '__main__':
    unittest.main(verbosity=2)
