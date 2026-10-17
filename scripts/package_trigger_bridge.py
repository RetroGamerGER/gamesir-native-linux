#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build optional userspace bridge sources or an offline DESTDIR; never install."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PKGNAME = 'gamesir-native-trigger-bridge'
SYSTEM_ROOTS = ('/usr', '/etc', '/var', '/opt', '/bin', '/sbin', '/lib', '/lib64',
                '/boot', '/dev', '/proc', '/sys', '/run')
GPL_SHA256 = 'e6d6a009505e345fe949e1310334fcb0747f28dae2856759de102ab66b722cb4'
RUNTIME_FILES = ('__init__.py', 'launch.py', 'relay.py', 'protocol.py', 'devices.py')
DOCUMENT_FILES = ('docs/TRIGGER_BRIDGE.md', 'docs/TRIGGER_BRIDGE_PROVENANCE.md',
                  'docs/HAPTICS_API.md', 'docs/LICENSING.md')
SOURCE_FILES = (
    'COPYING', 'LICENSES/exceptions/Linux-syscall-note',
    *DOCUMENT_FILES,
    'scripts/package_trigger_bridge.py',
    'packaging/trigger-bridge/VERSION',
    'packaging/trigger-bridge/PKGBUILD.in',
    'packaging/trigger-bridge/gamesir-native-trigger-bridge',
    *(f'tools/trigger_bridge/{name}' for name in RUNTIME_FILES),
    'tools/trigger_bridge/sdl2_hook.c',
    'tests/test_packaging_trigger_bridge.py',
)
PAYLOAD = (
    *((f'tools/trigger_bridge/{name}',
       f'usr/lib/gamesir-native/trigger_bridge/{name}', 0o644) for name in RUNTIME_FILES),
    ('packaging/trigger-bridge/gamesir-native-trigger-bridge',
     'usr/bin/gamesir-native-trigger-bridge', 0o755),
    *((name, f'usr/share/doc/{PKGNAME}/{name}', 0o644) for name in DOCUMENT_FILES),
    ('COPYING', f'usr/share/doc/{PKGNAME}/COPYING', 0o644),
    ('COPYING', f'usr/share/licenses/{PKGNAME}/COPYING', 0o644),
    ('LICENSES/exceptions/Linux-syscall-note',
     f'usr/share/doc/{PKGNAME}/LICENSES/exceptions/Linux-syscall-note', 0o644),
)
SHIM_TARGET = 'usr/lib/gamesir-native/trigger_bridge/libgamesir-trigger-sdl2.so'


def version(root=ROOT):
    value = (Path(root) / 'packaging/trigger-bridge/VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:\.[0-9A-Za-z]+)+', value):
        raise ValueError('Invalid trigger bridge version')
    return value


def source_files(root=ROOT):
    """A closed list; never collect local profiles, captures or runtime binaries."""
    root = Path(root).resolve()
    for relative in SOURCE_FILES:
        path = root / relative
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError(f'Required regular source missing or redirected: {relative}')
    if hashlib.sha256((root / 'COPYING').read_bytes()).hexdigest() != GPL_SHA256:
        raise ValueError('Complete reviewed GPL-v2 license required')
    return sorted(SOURCE_FILES)


def real_effective_uid():
    # Arch fakeroot changes libc's euid result, but not this kernel record.
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('Uid:'):
            values = line.split()[1:]
            if len(values) == 4 and all(value.isdecimal() for value in values):
                return int(values[1])
    raise ValueError('Cannot verify unprivileged packaging process')


def safe_destination(path):
    if real_effective_uid() == 0:
        raise ValueError('Packaging must run unprivileged; no live installation')
    raw = Path(path).absolute()
    resolved = raw.resolve()
    if raw.is_symlink() or raw != resolved:
        raise ValueError('Destination and parent directories must not be symbolic links')
    if resolved == Path('/') or any(resolved == Path(p) or Path(p) in resolved.parents
                                     for p in SYSTEM_ROOTS):
        raise ValueError('System destinations are forbidden; use offline staging')
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ValueError('Destination must be absent or empty; existing files are preserved')
    return resolved


def source_archive(dest, root=ROOT):
    root = Path(root).resolve()
    dest = safe_destination(dest)
    files = source_files(root)
    ver = version(root)
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '0'))
    if not 0 <= epoch <= 0xffffffff:
        raise ValueError('SOURCE_DATE_EPOCH must fit unsigned 32-bit seconds')
    stream = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=epoch) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for relative in files:
                data = (root / relative).read_bytes()
                info = tarfile.TarInfo(f'{PKGNAME}-{ver}/{relative}')
                info.size, info.mtime, info.mode = len(data), epoch, 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                archive.addfile(info, io.BytesIO(data))
    data = stream.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    recipe = (root / 'packaging/trigger-bridge/PKGBUILD.in').read_text().replace(
        '@VERSION@', ver).replace('@SOURCE_SHA256@', digest)
    name = f'{PKGNAME}-{ver}.tar.gz'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / name).write_bytes(data)
    (dest / 'PKGBUILD').write_text(recipe)
    (dest / 'SHA256SUMS').write_text(
        f'{digest}  {name}\n{hashlib.sha256(recipe.encode()).hexdigest()}  PKGBUILD\n')
    return dict(version=ver, archive=str(dest / name), sha256=digest,
                source_files=len(files), installed=False)


def validate_shim(path):
    raw = Path(path).absolute()
    if raw.is_symlink() or raw.resolve() != raw or not raw.is_file():
        raise ValueError('Expected a locally built regular shim file')
    header = raw.read_bytes()[:64]
    if (len(header) != 64 or header[:7] != b'\x7fELF\x02\x01\x01' or
            struct.unpack_from('<HH', header, 16) != (3, 62)):
        raise ValueError('Expected an x86_64 little-endian ELF shared library')
    return raw


def build(dest, root=ROOT, *, compiler='cc'):
    """Compile the adapter only. It is never loaded or executed by this action."""
    root = Path(root).resolve()
    dest = safe_destination(dest)
    source_files(root)
    version(root)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / 'libgamesir-trigger-sdl2.so'
    temporary = dest / '.libgamesir-trigger-sdl2.so.tmp'
    try:
        subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                        '-fPIC', '-shared', f'-ffile-prefix-map={root}=.',
                        f'-fmacro-prefix-map={root}=.',
                        str(root / 'tools/trigger_bridge/sdl2_hook.c'),
                        '-o', str(temporary), '-ldl', '-pthread',
                        '-Wl,-z,relro,-z,now'], check=True, timeout=60)
        validate_shim(temporary)
        temporary.chmod(0o755)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return dict(shim=str(target), installed=False, executed=False)


def stage(dest, shim, root=ROOT):
    root = Path(root).resolve()
    dest = safe_destination(dest)
    source_files(root)
    ver = version(root)
    shim = validate_shim(shim)
    dest.mkdir(parents=True, exist_ok=True)
    for relative, target, mode in PAYLOAD:
        output = dest / target
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, output)
        output.chmod(mode)
    output = dest / SHIM_TARGET
    shutil.copyfile(shim, output)
    output.chmod(0o755)
    return dict(version=ver, staged=str(dest), files=len(PAYLOAD) + 1, installed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    for action in ('source', 'build', 'stage'):
        command = commands.add_parser(action)
        command.add_argument('--dest', required=True)
        if action == 'stage':
            command.add_argument('--shim', required=True)
        if action == 'build':
            command.add_argument('--cc', default='cc')
    args = parser.parse_args()
    if args.action == 'source':
        result = source_archive(args.dest)
    elif args.action == 'build':
        result = build(args.dest, compiler=args.cc)
    else:
        result = stage(args.dest, args.shim)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
