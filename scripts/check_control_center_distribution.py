#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline consistency gate for a reviewed AppDir and corresponding sources.

No network, extraction, package manager, authentication or installed-system
changes. License decisions must be reviewed separately; a hash is not a license.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile


def relative(value):
    if (type(value) is not str or not value or '\\' in value
            or any(ord(c) < 32 for c in value)):
        raise ValueError('invalid relative path')
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('invalid relative path')
    return value


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(root, name):
    path = root / relative(name)
    if path.is_symlink() or path.resolve() != path.absolute() or not path.is_file():
        raise ValueError('missing or redirected reviewed file')
    return path


def hashes(root, expected, *, ignore=(), icon=False):
    if type(expected) is not dict or not expected:
        raise ValueError('empty file inventory')
    actual = set()
    for p in root.rglob('*'):
        name = p.relative_to(root).as_posix()
        if p.is_symlink():
            if icon and name == '.DirIcon' and p.readlink() == Path('gamesir-control-center.svg'):
                continue
            raise ValueError('unreviewed symbolic link')
        if p.is_file() and name not in ignore:
            actual.add(name)
    if actual != set(expected):
        raise ValueError('file inventory incomplete or extra files present')
    for name, value in expected.items():
        if type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('invalid checksum')
        if digest(regular(root, name)) != value:
            raise ValueError('reviewed file changed')


def verify(appdir, sources, lock):
    appdir, sources = Path(appdir).absolute(), Path(sources).absolute()
    if appdir.resolve() != appdir or sources.resolve() != sources:
        raise ValueError('redirected review root')
    if (type(lock) is not dict or set(lock) != {'schema', 'scope', 'appdir_files', 'source_files', 'files',
                     'components', 'runtime', 'source_archive_name', 'license_review'}
            or type(lock['schema']) is not int or lock['schema'] != 1
            or lock['scope'] != 'control-center-corresponding-source-review'):
        raise ValueError('invalid distribution review')
    if type(lock['license_review']) is not dict or lock['license_review'].get('reviewed') is not True:
        raise ValueError('license decisions not reviewed')
    if lock['license_review'].get('project_license') != 'GPL-2.0-only':
        raise ValueError('unexpected project license')
    relative(lock['source_archive_name'])
    hashes(appdir, lock['appdir_files'], ignore=('BUILD_INPUTS.json',), icon=True)
    hashes(sources, lock['source_files'], ignore=('DISTRIBUTION_LOCK.json',))
    embedded = json.loads(regular(appdir, 'BUILD_INPUTS.json').read_bytes())
    if embedded['files'] != lock['appdir_files']:
        raise ValueError('AppDir build inputs disagree')
    if json.loads(regular(sources, 'DISTRIBUTION_LOCK.json').read_bytes()) != lock:
        raise ValueError('source copy of review disagrees')
    components = lock['components']
    if (type(components) is not dict or not components or type(lock['files']) is not dict
            or set(lock['files']) != set(lock['appdir_files'])):
        raise ValueError('unattributed AppDir file')
    for component, row in components.items():
        if (type(component) is not str or not component or type(row) is not dict
                or type(row.get('version')) is not str or not row['version'] or not row.get('license_basis')
                or type(row.get('sources')) is not list or not row['sources']
                or type(row.get('notices')) is not list or not row['notices']):
            raise ValueError('component lacks version/source/license evidence')
        for key in ('sources', 'notices'):
            if not all(name in lock['source_files'] for name in row[key]):
                raise ValueError('source or license evidence not delivered')
    for name, component in lock['files'].items():
        relative(name)
        if component not in components:
            raise ValueError('unknown file owner')
    runtime = lock['runtime']
    if (type(runtime) is not dict or type(runtime.get('sha256')) is not str
            or not re.fullmatch('[0-9a-f]{64}', runtime['sha256'])):
        raise ValueError('runtime hash required')
    if (type(runtime.get('components')) is not list or not runtime['components']
            or type(runtime.get('source_revision')) is not str
            or not re.fullmatch('[0-9a-f]{40}', runtime['source_revision'])
            or not all(c in components for c in runtime['components'])):
        raise ValueError('runtime source closure missing')
    return {'technical_source_closure_verified': True,
            'appdir_files': len(lock['appdir_files']), 'source_files': len(lock['source_files']),
            'components': len(components), 'legal_guarantee': False,
            'publication_authorized': False, 'installed': False}


def verify_image(image, lock):
    runtime = lock['runtime']
    size = runtime.get('bytes')
    if type(size) is not int or not 64 <= size <= 16*1024*1024:
        raise ValueError('invalid runtime boundary')
    image = Path(image).absolute()
    if image.resolve() != image or image.is_symlink() or not image.is_file():
        raise ValueError('redirected image')
    with image.open('rb') as stream:
        prefix = stream.read(size)
        magic = stream.read(4)
    if (prefix[:11] != b'\x7fELF\x02\x01\x01\x00AI\x02' or magic != b'hsqs'
            or hashlib.sha256(prefix).hexdigest() != runtime['sha256']):
        raise ValueError('image runtime/source review differs')
    return digest(image)


def verify_source_archive(archive, lock):
    """Hash the actual compressed delivery without extracting or executing it."""
    archive = Path(archive).absolute()
    if archive.resolve() != archive or archive.is_symlink() or not archive.is_file():
        raise ValueError('redirected sources archive')
    expected = lock['source_files']; seen = set(); total = 0
    child = subprocess.Popen(['/usr/bin/zstd', '-q', '-d', '-c', '--', str(archive)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
    try:
        with tarfile.open(fileobj=child.stdout, mode='r|') as stream:
            for member in stream:
                name = member.name[2:] if member.name.startswith('./') else member.name
                if member.isdir():
                    if name not in ('', '.'):
                        relative(name)
                    continue
                relative(name)
                if (not member.isfile() or name in seen or member.size > 2*1024**3
                        or name not in expected and name != 'DISTRIBUTION_LOCK.json'):
                    raise ValueError('unreviewed source archive member')
                total += member.size
                if total > 8*1024**3:
                    raise ValueError('source archive limit')
                source = stream.extractfile(member)
                if name == 'DISTRIBUTION_LOCK.json':
                    if member.size > 4*1024**2 or json.loads(source.read()) != lock:
                        raise ValueError('source archive review differs')
                else:
                    h = hashlib.sha256()
                    while data := source.read(1024*1024):
                        h.update(data)
                    if h.hexdigest() != expected[name]:
                        raise ValueError('source archive contents changed')
                seen.add(name)
            # Inspect buffered bytes too: a second hidden archive or arbitrary
            # data after tar's end marker is not part of the reviewed delivery.
            padding = 0
            while data := stream.fileobj.read(65536):
                padding += len(data)
                if padding > 4*1024**2 or any(data):
                    raise ValueError('unreviewed trailing archive data')
        if child.wait(timeout=30) or seen != set(expected) | {'DISTRIBUTION_LOCK.json'}:
            raise ValueError('incomplete sources archive')
    finally:
        child.stdout.close()
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait(timeout=5)
    return digest(archive)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--appdir', required=True)
    p.add_argument('--sources', required=True)
    p.add_argument('--lock', required=True)
    p.add_argument('--image', help='also bind the exact type-2 runtime prefix and image hash')
    p.add_argument('--source-archive', help='verify actual delivered zstd/tar bytes without extraction')
    a = p.parse_args()
    try:
        lock = json.loads(Path(a.lock).read_bytes())
        result = verify(a.appdir, a.sources, lock)
        if a.image:
            result['image_sha256'] = verify_image(a.image, lock)
        if a.source_archive:
            result['source_archive_sha256'] = verify_source_archive(a.source_archive, lock)
        print(json.dumps(result)); return 0
    except (ValueError, KeyError, TypeError, OSError, tarfile.TarError, subprocess.SubprocessError):
        print('Distribution review failed; nothing installed or published.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
