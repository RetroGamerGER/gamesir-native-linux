# SPDX-License-Identifier: GPL-2.0-only
"""Protected local trust anchors and independently verified signed catalogs.

Remote data cannot supply keys or commands. Source/public defaults have no key.
Deployment is a separately approved step; import and construction are inert.
"""
from dataclasses import asdict, dataclass
import base64
import fcntl
import hashlib
import os
from pathlib import Path
import secrets
import stat
import subprocess
import time

from artifacts import BackendError, Catalog, Review
from package_execution import ExecutionTrust, InstalledReview
from package_wire import decode, encode

CATALOG = '/usr/lib/gamesir-control-center/package-executor/REVIEWED_PACKAGES.json'
EMPTY = {'schema': 1, 'scope': 'local_review', 'packages': [], 'installed': []}


def parse_catalog(data):
    value = decode(data)
    if (type(value) is not dict or set(value) not in (set(EMPTY), set(EMPTY) | {'updates'})
            or type(value['schema']) is not int or value['schema'] != 1
            or value['scope'] != 'local_review'
            or type(value['packages']) is not list or len(value['packages']) > 4
            or type(value['installed']) is not list or len(value['installed']) > 64):
        raise BackendError('invalid_deployment_catalog')
    records, installed = [], []
    try:
        for raw in value['packages']:
            if type(raw) is not dict or set(raw) != set(Review.__dataclass_fields__):
                raise BackendError('invalid_deployment_catalog')
            row = dict(raw)
            for name in ('dependencies', 'upgrade_from', 'guards'):
                if type(row[name]) is not list:
                    raise BackendError('invalid_deployment_catalog')
                row[name] = tuple(row[name])
            if any(type(r) is not list for r in row['guards']):
                raise BackendError('invalid_deployment_catalog')
            row['guards'] = tuple(tuple(r) for r in row['guards'])
            record = Review(**row)
            record.validate()
            records.append(record)
        for raw in value['installed']:
            if (type(raw) is not dict or set(raw) != set(InstalledReview.__dataclass_fields__)
                    or type(raw['guards']) is not list or any(type(r) is not list for r in raw['guards'])):
                raise BackendError('invalid_deployment_catalog')
            installed.append(InstalledReview(raw['component'], raw['version'],
                                             tuple(tuple(r) for r in raw['guards'])))
        if len({r.component for r in records}) != len(records):
            raise BackendError('duplicate_review_component')
        policy = parse_policy(value['updates']) if 'updates' in value else None
        return ExecutionTrust(Catalog(records), installed, policy)
    except (TypeError, KeyError):
        raise BackendError('invalid_deployment_catalog') from None


def serialize_catalog(trust):
    value = {'schema': 1, 'scope': 'local_review',
             'packages': [asdict(r) for r in trust.catalog.records],
             'installed': [asdict(r) for r in trust.installed]}
    if trust.release_policy is not None:
        value['updates'] = trust.release_policy
    data = encode(value)
    parse_catalog(data)
    return data + b'\n'


def load_installed_catalog():
    from package_host import protected
    protected(CATALOG)
    fd = os.open(CATALOG, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as source:
        info = os.fstat(source.fileno())
        if (info.st_uid != 0 or info.st_gid != 0 or not stat.S_ISREG(info.st_mode)
                or info.st_mode & 0o022 or info.st_size > 65536):
            raise BackendError('unsafe_deployment_catalog')
        data = source.read(65537)
    if len(data) > 65536:
        raise BackendError('invalid_deployment_catalog')
    return parse_catalog(data)


# The trust anchor stays in protected local review data. None of these fields
# may be obtained from a remote envelope. No production key is supplied here.
REPOSITORY = 'RetroGamerGER/gamesir-native-linux'
CATALOG_LIMIT = 196608
DOMAIN = b'GameSir Native Linux signed release catalog v1\x00'
MAX_VALIDITY = 90 * 86400
STATE = '/var/cache/gamesir-control-center/release-catalog.json'


def parse_policy(value):
    from artifacts import HEX
    if (type(value) is not dict or set(value) != {'schema', 'minimum_revision', 'keys'}
            or type(value['schema']) is not int or value['schema'] != 1
            or type(value['minimum_revision']) is not int
            or not 1 <= value['minimum_revision'] <= 2**53-1
            or type(value['keys']) is not list or not 1 <= len(value['keys']) <= 4):
        raise BackendError('invalid_release_policy')
    seen = set()
    for row in value['keys']:
        if (type(row) is not dict or set(row) != {'id', 'public_key'}
                or any(type(row[k]) is not str or not HEX.fullmatch(row[k]) for k in row)
                or row['id'] in seen
                or hashlib.sha256(bytes.fromhex(row['public_key'])).hexdigest() != row['id']):
            raise BackendError('invalid_release_policy')
        seen.add(row['id'])
    return value


def ed25519_verify(public_key, message, signature):
    """Use system OpenSSL, not handwritten crypto or user-supplied executables.

    Sealed anonymous files keep the exact bytes stable; no private key, shell,
    configuration, output log or filesystem payload is passed to OpenSSL.
    """
    from package_host import protected
    protected('/usr/bin/openssl')
    fds = []
    try:
        for name, data in (('key', bytes.fromhex('302a300506032b6570032100') + public_key),
                           ('data', DOMAIN + message), ('signature', signature)):
            fd = os.memfd_create('gamesir-release-' + name, os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
            fds.append(fd)
            with os.fdopen(os.dup(fd), 'wb') as stream: stream.write(data)
            os.lseek(fd, 0, os.SEEK_SET)
            fcntl.fcntl(fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW |
                        fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
        key, data, sig = ('/proc/self/fd/' + str(fd) for fd in fds)
        result = subprocess.run(('/usr/bin/openssl', 'pkeyutl', '-verify', '-pubin',
            '-keyform', 'DER', '-inkey', key, '-rawin', '-in', data, '-sigfile', sig),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            pass_fds=tuple(fds), close_fds=True, timeout=5, check=False,
            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'OPENSSL_CONF': '/dev/null',
                 'OPENSSL_ENGINES': '/nonexistent', 'OPENSSL_MODULES': '/nonexistent'})
        if result.returncode != 0:
            raise BackendError('release_signature_invalid')
    except (OSError, subprocess.TimeoutExpired):
        raise BackendError('release_verifier_unavailable') from None
    finally:
        for fd in fds: os.close(fd)


@dataclass(frozen=True)
class SignedRelease:
    envelope: bytes
    revision: int
    payload_digest: str
    issued_at: int
    expires_at: int
    trust: object
    assets: bytes
    expired: bool = False


def verify_signed_catalog(data, root, *, now=None, previous=None, allow_expired=False):
    """Both GUI and root call this independently with their local trust anchor."""
    from artifacts import COMPONENTS, HEX
    from package_alpm import version_compare
    policy = parse_policy(root.release_policy)
    if type(data) is not bytes or not 0 < len(data) <= CATALOG_LIMIT:
        raise BackendError('release_catalog_limit')
    envelope = decode(data)
    if (type(envelope) is not dict or set(envelope) != {'schema', 'algorithm', 'key_id', 'payload', 'signature'}
            or type(envelope['schema']) is not int or envelope['schema'] != 1
            or envelope['algorithm'] != 'ed25519'
            or any(type(envelope[k]) is not str for k in ('key_id', 'payload', 'signature'))
            or not HEX.fullmatch(envelope['key_id']) or len(envelope['signature']) != 128
            or any(c not in '0123456789abcdef' for c in envelope['signature'])):
        raise BackendError('invalid_release_envelope')
    key = next((k for k in policy['keys'] if k['id'] == envelope['key_id']), None)
    if key is None: raise BackendError('release_key_untrusted')
    try:
        payload = base64.b64decode(envelope['payload'], validate=True)
        if base64.b64encode(payload).decode() != envelope['payload'] or not 0 < len(payload) <= 131072:
            raise ValueError
    except ValueError:
        raise BackendError('invalid_release_envelope') from None
    ed25519_verify(bytes.fromhex(key['public_key']), payload, bytes.fromhex(envelope['signature']))
    value = decode(payload)
    if (type(value) is not dict or set(value) != {'schema', 'repository', 'protocol', 'revision',
            'issued_at', 'expires_at', 'packages', 'installed', 'assets'}
            or type(value['schema']) is not int or value['schema'] != 1
            or value['repository'] != REPOSITORY or type(value['protocol']) is not int or value['protocol'] != 3
            or any(type(value[k]) is not int or not 1 <= value[k] <= 2**53-1
                   for k in ('revision', 'issued_at', 'expires_at'))
            or not 0 < value['expires_at'] - value['issued_at'] <= MAX_VALIDITY):
        raise BackendError('invalid_signed_catalog')
    now = time.time() if now is None else now
    import math
    if type(now) not in (int, float) or not math.isfinite(now):
        raise BackendError('release_clock_invalid')
    clock_early = now < value['issued_at'] - 300
    if clock_early and not allow_expired: raise BackendError('release_clock_invalid')
    expired = now >= value['expires_at'] or clock_early
    if expired and not allow_expired: raise BackendError('release_catalog_expired')
    digest = hashlib.sha256(payload).hexdigest()
    if (value['revision'] < policy['minimum_revision'] or previous is not None and
            (value['revision'] < previous.revision or value['revision'] == previous.revision
             and digest != previous.payload_digest or value['issued_at'] < previous.issued_at)):
        raise BackendError('release_catalog_rollback')
    incoming = parse_catalog(encode({**EMPTY, 'packages': value['packages'], 'installed': value['installed']}))
    if {r.component for r in incoming.catalog.records} != set(COMPONENTS):
        raise BackendError('incomplete_signed_catalog')
    baseline = previous.trust if previous is not None else root
    before = {r.component: r for r in baseline.catalog.records}
    installed = {(r.component, r.version): r for r in baseline.installed}
    if not set(installed) <= {(r.component, r.version) for r in incoming.installed}:
        raise BackendError('release_history_missing')
    for record in incoming.installed:
        key = record.component, record.version
        if key in installed and installed[key] != record:
            raise BackendError('release_guard_history_changed')
        installed[key] = record
    for record in incoming.catalog.records:
        old = before.get(record.component)
        if old is not None:
            comparison = version_compare(record.version, old.version)
            if comparison < 0 or comparison == 0 and record.digest != old.digest:
                raise BackendError('release_package_rollback')
        for origin in record.upgrade_from:
            if version_compare(origin, record.version) >= 0:
                raise BackendError('release_package_rollback')
            if (record.component, origin) not in installed:
                raise BackendError('release_upgrade_origin_unreviewed')
        current = installed.get((record.component, record.version))
        if current is None or current.guards != record.guards:
            raise BackendError('release_removal_record_missing')
    if len(installed) > 64: raise BackendError('release_history_limit')
    trust = ExecutionTrust(incoming.catalog, tuple(installed.values()), policy)
    # Reuse the closed release-index parser in the GUI; root validates the same
    # filenames locally without importing a network-enabled module.
    assets = value['assets']
    import re
    if (type(assets) is not list or len(assets) != 4 or any(type(a) is not dict or
            set(a) != {'component', 'filename'} or type(a['component']) is not str or
            a['component'] not in COMPONENTS or type(a['filename']) is not str or
            not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+\-]{0,180}\.pkg\.tar\.zst', a['filename'])
            or '..' in a['filename'] for a in assets)
            or {a['component'] for a in assets} != set(COMPONENTS)
            or len({a['filename'] for a in assets}) != 4):
        raise BackendError('invalid_signed_assets')
    return SignedRelease(data, value['revision'], digest, value['issued_at'], value['expires_at'],
                         trust, encode({'schema': 1, 'repository': REPOSITORY, 'assets': assets}), expired)


class CatalogState:
    """Atomic signed metadata only; no installed-package success is recorded.

    Production supplies a fixed root0700 parent and owner=0. Tests inject a
    same-user temporary directory/guard. Paths are never accepted over the wire.
    """
    def __init__(self, path, *, owner=0, parent_guard=None):
        self.path, self.owner = Path(path), owner
        self.parent_guard = parent_guard

    def parent(self):
        if self.parent_guard is None:
            from package_host import protected
            protected(self.path.parent, directory=True)
        else: self.parent_guard(self.path.parent)
        fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        info = os.fstat(fd)
        if info.st_uid != self.owner or stat.S_IMODE(info.st_mode) != 0o700:
            os.close(fd); raise BackendError('release_state_unsafe')
        return fd

    def read(self):
        directory = self.parent()
        try:
            try: fd = os.open(self.path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
            except FileNotFoundError: return None
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner
                        or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                        or not 0 < info.st_size <= CATALOG_LIMIT):
                    raise BackendError('release_state_unsafe')
                data = stream.read(CATALOG_LIMIT + 1)
            if len(data) != info.st_size: raise BackendError('release_state_changed')
            return data
        except OSError: raise BackendError('release_state_unavailable') from None
        finally: os.close(directory)

    def write(self, data):
        if type(data) is not bytes or not 0 < len(data) <= CATALOG_LIMIT:
            raise BackendError('release_catalog_limit')
        # Validate an existing leaf too; never repair unsafe/corrupt state.
        self.read()
        directory = self.parent(); name = '.release-' + secrets.token_hex(16)
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o600); stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, self.path.name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        except OSError: raise BackendError('release_state_persistence_failed') from None
        finally:
            try: os.unlink(name, dir_fd=directory)
            except OSError: pass  # Never overwrite a persistence failure during cleanup.
            os.close(directory)


class ReleaseResolver:
    """Independent helper verifier; checkpoint is called under the ALPM lock."""
    def __init__(self, root, state, *, clock=time.time):
        self.root, self.state, self.clock = root, state, clock
        self.envelope, self.operation, self.trust = None, None, root
        self.accept_signed = False

    def previous(self):
        data = self.state.read()
        return (verify_signed_catalog(data, self.root, now=self.clock(), allow_expired=True)
                if data is not None else None)

    def resolve(self, envelope, operation):
        self.operation, self.envelope = operation, envelope
        self.accept_signed = False
        if self.root.release_policy is None:
            if envelope is not None: raise BackendError('signed_updates_disabled')
            return self.root
        previous = self.previous()
        if operation == 'remove':
            # Expired/replayed data cannot grant new cleanup rights. A current
            # fresh signed catalog can also review a manually installed package.
            self.trust = previous.trust if previous is not None else self.root
            if envelope is not None:
                try:
                    candidate = verify_signed_catalog(envelope, self.root, now=self.clock(),
                                                      previous=previous, allow_expired=True)
                except BackendError:
                    # Authenticate historical data, but use protected history,
                    # never its unaccepted installed-version/guard records.
                    verify_signed_catalog(envelope, self.root, now=self.clock(), allow_expired=True)
                else:
                    if not candidate.expired:
                        self.trust, self.accept_signed = candidate.trust, True
            return self.trust
        if envelope is None: raise BackendError('signed_catalog_required')
        self.trust = verify_signed_catalog(envelope, self.root, now=self.clock(), previous=previous).trust
        self.accept_signed = True
        return self.trust

    def checkpoint(self):
        if self.root.release_policy is None: return
        if not self.accept_signed:
            self.previous()  # Still require intact state under the lock.
            return
        previous = self.previous()
        checked = verify_signed_catalog(self.envelope, self.root, now=self.clock(), previous=previous)
        if previous is None or checked.payload_digest != previous.payload_digest:
            self.state.write(checked.envelope)
