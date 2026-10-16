#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build optional Steam integration archives/DESTDIR offline; never install/run Steam."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOTS = ('/usr', '/etc', '/var', '/opt', '/bin', '/sbin', '/lib', '/lib64',
                '/boot', '/dev', '/proc', '/sys', '/run')
SOURCE_FILES = (
    'docs/STEAM_INTEGRATION.md',
    'packaging/steam/COPYING',
    'packaging/steam/PKGBUILD.in',
    'packaging/steam/VERSION',
    'packaging/steam/gamesir-native-steam',
    'packaging/steam/plasma-env.sh',
    'scripts/package_steam.py',
    'tests/test_packaging_steam.py',
    'tools/sdl/gamesir-plasma-env.sh',
)
PAYLOAD = (
    ('tools/sdl/gamesir-plasma-env.sh', 'usr/share/gamesir-native-steam/session.sh', 0o644),
    ('packaging/steam/plasma-env.sh', 'etc/xdg/plasma-workspace/env/90-gamesir-native-steam.sh', 0o644),
    ('packaging/steam/gamesir-native-steam', 'usr/bin/gamesir-native-steam', 0o755),
    ('docs/STEAM_INTEGRATION.md', 'usr/share/doc/gamesir-native-steam/STEAM_INTEGRATION.md', 0o644),
    ('packaging/steam/COPYING', 'usr/share/licenses/gamesir-native-steam/COPYING', 0o644),
)
GAMESCOPE_SOURCE_FILES = (
    'docs/STEAM_GAMESCOPE.md',
    'packaging/steam/COPYING',
    'packaging/steam-gamescope/PKGBUILD.in',
    'packaging/steam-gamescope/VERSION',
    'packaging/steam-gamescope/gamescope-launcher',
    'packaging/steam-gamescope/50-gamesir-native.conf',
    'scripts/package_steam.py',
    'tests/test_packaging_gamescope.py',
)
GAMESCOPE_PAYLOAD = (
    ('packaging/steam-gamescope/gamescope-launcher',
     'usr/lib/gamesir-native-steam/gamescope-launcher', 0o755),
    ('packaging/steam-gamescope/50-gamesir-native.conf',
     'usr/lib/systemd/user/steam-launcher.service.d/50-gamesir-native.conf', 0o644),
    ('docs/STEAM_GAMESCOPE.md',
     'usr/share/doc/gamesir-native-steam-gamescope/STEAM_GAMESCOPE.md', 0o644),
    ('packaging/steam/COPYING',
     'usr/share/licenses/gamesir-native-steam-gamescope/COPYING', 0o644),
)
COMPONENTS = {
    'steam': ('gamesir-native-steam', 'packaging/steam', SOURCE_FILES, PAYLOAD),
    'gamescope': ('gamesir-native-steam-gamescope', 'packaging/steam-gamescope',
                  GAMESCOPE_SOURCE_FILES, GAMESCOPE_PAYLOAD),
}


def component_profile(component):
    try:
        return COMPONENTS[component]
    except (KeyError, TypeError):
        raise ValueError('Unknown Steam integration component') from None


def version(root=ROOT, *, component='steam'):
    _, folder, _, _ = component_profile(component)
    value = (root / folder / 'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:\.[0-9A-Za-z]+)+', value):
        raise ValueError('Invalid Steam integration version')
    return value


def source_files(root=ROOT, *, component='steam'):
    """No recursive collection: private data, kernel and installers stay outside."""
    root = Path(root).resolve()
    _, _, sources, _ = component_profile(component)
    for relative in sources:
        item = root / relative
        # Parent symlinks are also forbidden: all source bytes must be in this tree.
        if item.is_symlink() or item.resolve() != item or not item.is_file():
            raise ValueError(f'Required regular source missing or redirected: {relative}')
    return sorted(sources)


def real_effective_uid():
    # makepkg fakeroot reports 0 through libc; proc reports the actual kernel UID.
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('Uid:'):
            values = line.split()[1:]
            if len(values) == 4 and all(value.isdecimal() for value in values):
                return int(values[1])
    raise ValueError('Cannot verify unprivileged packaging process')


def safe_destination(path):
    if real_effective_uid() == 0:
        raise ValueError('Packaging runs unprivileged; no root build or live installation')
    raw = Path(path).absolute()
    if raw.is_symlink():
        raise ValueError('Destination must not be a symbolic link')
    path = raw.resolve()
    if path == Path('/') or any(path == Path(p) or Path(p) in path.parents for p in SYSTEM_ROOTS):
        raise ValueError('System destinations are forbidden; use an offline staging directory')
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError('Destination must be absent or empty; existing files are preserved')
    return path


def source_archive(dest, root=ROOT, *, component='steam'):
    pkgname, folder, _, _ = component_profile(component)
    dest = safe_destination(dest)
    files = source_files(root, component=component)
    ver = version(root, component=component)
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '0'))
    if epoch < 0:
        raise ValueError('SOURCE_DATE_EPOCH must not be negative')
    stream = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=epoch) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for relative in files:
                data = (root / relative).read_bytes()
                info = tarfile.TarInfo(f'{pkgname}-{ver}/{relative}')
                info.size, info.mtime, info.mode = len(data), epoch, 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                archive.addfile(info, io.BytesIO(data))
    data = stream.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    pkgbuild = (root / folder / 'PKGBUILD.in').read_text().replace(
        '@VERSION@', ver).replace('@SOURCE_SHA256@', digest)
    dest.mkdir(parents=True, exist_ok=True)
    name = f'{pkgname}-{ver}.tar.gz'
    (dest / name).write_bytes(data)
    (dest / 'PKGBUILD').write_text(pkgbuild)
    (dest / 'SHA256SUMS').write_text(
        f'{digest}  {name}\n{hashlib.sha256(pkgbuild.encode()).hexdigest()}  PKGBUILD\n')
    return {'version': ver, 'archive': str(dest / name), 'sha256': digest,
            'source_files': len(files), 'installed': False}


def stage(dest, root=ROOT, *, component='steam'):
    _, _, _, payload = component_profile(component)
    dest = safe_destination(dest)
    source_files(root, component=component)  # Validate before writing anything.
    ver = version(root, component=component)
    dest.mkdir(parents=True, exist_ok=True)
    for relative, target, mode in payload:
        output = dest / target
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, output)
        output.chmod(mode)
    return {'version': ver, 'staged': str(dest), 'files': len(payload), 'installed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('source', 'stage'):
        item = sub.add_parser(action)
        item.add_argument('--dest', required=True)
        item.add_argument('--component', choices=COMPONENTS, default='steam')
    args = parser.parse_args()
    method = source_archive if args.action == 'source' else stage
    result = method(args.dest, component=args.component)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
