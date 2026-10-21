# SPDX-License-Identifier: GPL-2.0-only
"""Offline byte verifier. No downloads, extraction, executables or file access.

Review records are supplied by a trusted maintainer/build review, NOT by the
package or GUI request. There are currently no approved public binary records.
This module is not a privilege boundary or a signature/trust-root substitute.
"""
from dataclasses import dataclass
import hashlib
import io
from pathlib import PurePosixPath
import re
import tarfile

COMPONENTS = {
    'core': ('gamesir-native-dkms', 'x86_64'),
    'steam': ('gamesir-native-steam', 'any'),
    'gamescope': ('gamesir-native-steam-gamescope', 'any'),
    'bridge': ('gamesir-native-trigger-bridge', 'x86_64'),
}
HEX = re.compile(r'[0-9a-f]{64}\Z')
VERSION = re.compile(r'[0-9][0-9A-Za-z.+_:~-]{0,95}\Z')
MAX_PACKAGE = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_MEMBER = 16 * 1024 * 1024
CORE_GUARDS = (
    'usr/lib/gamesir-native/prepare_remove.py',
    'usr/share/libalpm/hooks/60-gamesir-native-release.hook',
    'usr/share/libalpm/hooks/60-gamesir-native-upgrade.hook',
)


class BackendError(ValueError):
    """Stable public code, never arbitrary process stderr or private filenames."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Review:
    component: str
    version: str
    digest: str
    size: int
    source_commit: str
    tag: str
    dependencies: tuple = ()
    upgrade_from: tuple = ()
    guards: tuple = ()

    def validate(self):
        if (any(type(v) is not str for v in (self.component, self.version, self.digest, self.source_commit, self.tag))
                or self.component not in COMPONENTS or not VERSION.fullmatch(self.version)
                or not HEX.fullmatch(self.digest) or type(self.size) is not int
                or not 0 < self.size <= MAX_PACKAGE
                or not re.fullmatch(r'[0-9a-f]{40}', self.source_commit)
                or not re.fullmatch(r'v[0-9A-Za-z._-]{1,80}', self.tag)):
            raise BackendError('invalid_review_record')
        if (type(self.dependencies) is not tuple or type(self.upgrade_from) is not tuple
                or any(not isinstance(v, str) or not VERSION.fullmatch(v) or v == self.version
                       for v in self.upgrade_from)):
            raise BackendError('invalid_review_record')
        if any(not isinstance(d, str) or not re.fullmatch(r'[a-z0-9@+_.-]+(?:[<>=]+[0-9A-Za-z.+_:~-]+)?', d)
               for d in self.dependencies):
            raise BackendError('invalid_review_record')
        if (type(self.guards) is not tuple or any(type(row) is not tuple or len(row) != 2
                or any(type(v) is not str for v in row) for row in self.guards)):
            raise BackendError('invalid_review_record')
        if self.component == 'core':
            if (len(self.guards) != 3 or {p for p, _ in self.guards} != set(CORE_GUARDS)
                    or any(not HEX.fullmatch(d) for _, d in self.guards)):
                raise BackendError('unreviewed_core_guards')
        elif self.guards:
            raise BackendError('unexpected_core_guards')


@dataclass(frozen=True)
class Artifact:
    review: Review
    data: bytes

    @property
    def package(self):
        return COMPONENTS[self.review.component][0]


class Catalog:
    def __init__(self, records=()):
        self.records = tuple(records)
        seen = set()
        for record in self.records:
            record.validate()
            key = record.component, record.digest
            if key in seen:
                raise BackendError('duplicate_review_record')
            seen.add(key)

    def verify(self, component, data):
        if component not in COMPONENTS or type(data) is not bytes or not 0 < len(data) <= MAX_PACKAGE:
            raise BackendError('invalid_artifact_bytes')
        digest = hashlib.sha256(data).hexdigest()
        record = next((r for r in self.records if r.component == component and r.digest == digest), None)
        if record is None:
            raise BackendError('no_reviewed_binary')
        if record.size != len(data):
            raise BackendError('artifact_size_mismatch')
        inspect_package(record, data)
        return Artifact(record, data)


def package_info(data):
    if len(data) > 32768:
        raise BackendError('invalid_package_metadata')
    info = {}
    try:
        for line in data.decode('utf-8').splitlines():
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition(' = ')
            # makepkg legitimately emits an empty optional URL. Required
            # identity/dependency fields must never accept empty values.
            if not sep or not re.fullmatch(r'[a-z_]+', key) or not value and key != 'url':
                raise BackendError('invalid_package_metadata')
            info.setdefault(key, []).append(value)
    except UnicodeError:
        raise BackendError('invalid_package_metadata') from None
    return info


def inspect_package(review, data):
    """Stream a reviewed ALPM archive, bounded, without extracting any files.

    Python's tar reader supplies gzip/xz and, on Python 3.14+, zstd support.
    Missing decoder support blocks instead of installing an extra dependency.
    """
    review.validate()
    names, guards = set(), {}
    info = None
    total = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r|*') as archive:
            for index, member in enumerate(archive):
                name = member.name.rstrip('/')
                parts = PurePosixPath(name)
                if (index >= 8192 or not name or name.startswith('/') or '\\' in name
                        or '..' in parts.parts or parts.as_posix() != name
                        or any(ord(c) < 32 for c in name) or name in names
                        or not (member.isfile() or member.isdir())
                        or member.uid != 0 or member.gid != 0 or member.mode & 0o7000
                        or member.size < 0 or member.size > MAX_MEMBER):
                    raise BackendError('unsafe_package_archive')
                names.add(name)
                total += member.size
                if total > MAX_EXPANDED:
                    raise BackendError('package_limit_exceeded')
                if name == '.INSTALL':
                    raise BackendError('package_install_script_refused')
                if member.isdir():
                    continue
                content = archive.extractfile(member).read(MAX_MEMBER + 1)
                if len(content) != member.size:
                    raise BackendError('incomplete_package_archive')
                if name == '.PKGINFO' or name in CORE_GUARDS:
                    if name == '.PKGINFO':
                        info = package_info(content)
                    else:
                        guards[name] = hashlib.sha256(content).hexdigest()
    except BackendError:
        raise
    except (tarfile.TarError, OSError, EOFError, ValueError):
        raise BackendError('unsupported_or_invalid_package_archive') from None
    if info is None:
        raise BackendError('missing_package_metadata')
    name, arch = COMPONENTS[review.component]
    expected = {'pkgname': [name], 'pkgver': [review.version], 'arch': [arch],
                'license': ['GPL-2.0-only']}
    if any(info.get(k) != v for k, v in expected.items()):
        raise BackendError('package_identity_mismatch')
    if (tuple(sorted(info.get('depend', ()))) != tuple(sorted(review.dependencies))
            or any(info.get(k) for k in ('conflict', 'replaces', 'provides'))):
        raise BackendError('package_relationship_mismatch')
    if review.component == 'core' and guards != dict(review.guards):
        raise BackendError('package_guard_mismatch')
    if review.component != 'core' and guards:
        raise BackendError('unexpected_core_guards')


# Source-only publication: no invented release URLs or self-trusted checksums.
PUBLIC_BINARIES = Catalog()
