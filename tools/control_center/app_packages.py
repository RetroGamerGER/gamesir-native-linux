# SPDX-License-Identifier: GPL-2.0-only
"""Opt-in build-time AppImage package binding. Imports never inspect the host.

A private reviewed bundle supplies data/bytes, never privileged code or paths.
The installed helper retains its independent trust. All inspection runs in a
Qt worker; properties use only cached facts. There is no install-on-launch.
"""
from dataclasses import dataclass, field, replace
import hashlib
import os
from pathlib import Path
import stat
import time
import threading

from artifacts import BackendError, Catalog, COMPONENTS, MAX_PACKAGE
from backend import Request
from package_catalog import CATALOG, parse_catalog
from package_client import ExecutionTransactions, PackageTransport
from package_wire import EXECUTOR, decode
from privilege.protocol import AuthorizationError


def bounded_file(path, limit):
    path = Path(path)
    if path.absolute() != path.resolve():
        raise BackendError('redirected_bundle_input')
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
            raise BackendError('invalid_bundle_input')
        data = source.read(limit + 1)
    if len(data) > limit:
        raise BackendError('invalid_bundle_input')
    return data


@dataclass(frozen=True)
class PackageBundle:
    trust: object
    pins: tuple
    blobs: tuple
    distribution: str
    kernel: str
    release_assets: tuple = ()
    root_trust: object = None
    signed_release: object = None

    def attest(self, auditor):
        auditor.inspect('/usr/bin/pkexec', executable=True)
        for path, expected in self.pins:
            auditor.inspect(path, expected, executable=path == EXECUTOR)

    def check_host(self, host, now):
        host.validate(now)
        if (host.distribution != self.distribution or host.architecture != 'x86_64'
                or host.kernel != self.kernel and self.trust.release_policy is None):
            raise BackendError('bundle_target_mismatch')


def load_bundle(directory):
    """Fixed names inside the build-selected directory; no environment/CLI paths."""
    root = Path(directory)
    raw = decode(bounded_file(root / 'profile.json', 65536))
    if (type(raw) is not dict or set(raw) != {'schema', 'scope', 'pins', 'distribution', 'kernel'}
            or type(raw['schema']) is not int or raw['schema'] != 1
            or raw['scope'] != 'local_review' or raw['distribution'] not in ('garuda', 'cachyos')
            or type(raw['kernel']) is not str):
        raise BackendError('invalid_appimage_profile')
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.+\-]{1,160}', raw['kernel']):
        raise BackendError('invalid_appimage_profile')
    if type(raw['pins']) is not list or any(type(row) is not list for row in raw['pins']):
        raise BackendError('invalid_appimage_profile')
    pins = tuple(tuple(row) for row in raw['pins'])
    PackageTransport(pins)  # Validate exact independent helper set, no I/O/spawn.
    catalog = bounded_file(root / 'REVIEWED_PACKAGES.json', 65536)
    if hashlib.sha256(catalog).hexdigest() != dict(pins)[CATALOG]:
        raise BackendError('bundle_catalog_mismatch')
    trust = parse_catalog(catalog)
    if not trust.catalog.records:
        raise BackendError('empty_appimage_catalog')
    index = root / 'release-assets.json'
    if os.path.lexists(index):
        from release_download import parse_assets
        assets = parse_assets(bounded_file(index, 65536), trust.catalog)
        if any(root.glob('*.pkg.tar.zst')):
            raise BackendError('mixed_package_sources')
        return PackageBundle(trust, pins, (), raw['distribution'], raw['kernel'], assets)
    blobs = []
    for record in trust.catalog.records:
        data = bounded_file(root / (record.component + '.pkg.tar.zst'), MAX_PACKAGE)
        trust.catalog.verify(record.component, data)
        blobs.append((record.component, data))
    return PackageBundle(trust, pins, tuple(blobs), raw['distribution'], raw['kernel'])


class CachedEvidence:
    host = None

    def observe(self):
        if self.host is None:
            raise BackendError('package_inspection_required')
        return self.host


def installable(trust, host):
    installed = dict(host.installed)
    reviewed = {(r.component, r.version) for r in trust.installed}
    return tuple(r.component for r in trust.catalog.records
                 if (COMPONENTS[r.component][0] not in installed
                     or (installed[COMPONENTS[r.component][0]] in r.upgrade_from
                         and (r.component, installed[COMPONENTS[r.component][0]]) in reviewed)))


def signed_bundle(bundle, data, *, now, previous=None, allow_expired=False):
    from package_catalog import verify_signed_catalog
    from release_download import parse_assets
    root = bundle.root_trust or bundle.trust
    release = verify_signed_catalog(data, root, now=now, previous=previous, allow_expired=allow_expired)
    return replace(bundle, root_trust=root, trust=release.trust, blobs=(), signed_release=release,
                   release_assets=parse_assets(release.assets, release.trust.catalog))


class UserCatalogCache:
    """Signature-checked acceleration only; this cache is never root authority."""
    def __init__(self, directory):
        self.directory = Path(directory)

    def store(self):
        from package_catalog import CatalogState
        def local_parent(path):
            if path.absolute() != path.resolve(): raise BackendError('release_state_unsafe')
        return CatalogState(self.directory / 'catalog.json', owner=os.getuid(), parent_guard=local_parent)

    def read(self):
        if not os.path.lexists(self.directory): return None
        return self.store().read()

    def write(self, data):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.store().write(data)


@dataclass(frozen=True)
class UpdateInspection:
    owner: object
    cancellation: object = field(default_factory=threading.Event)

    def run(self):
        try:
            o = self.owner
            o.bundle.attest(o.transport.auditor)
            data = o.downloader.fetch_catalog(cancelled=self.cancellation.is_set)
            bundle = signed_bundle(o.bundle, data, now=o.wall_clock(), previous=o.bundle.signed_release)
            host = o.reader(Request('install', ('core',))).collect()
            bundle.check_host(host, o.clock()); bundle.attest(o.transport.auditor)
            if self.cancellation.is_set(): raise BackendError('release_download_cancelled')
            if o.update_cache is not None: o.update_cache.write(data)
            return bundle, o.transport, host, ''
        except (BackendError, AuthorizationError) as error:
            return None, None, None, error.code
        except Exception:
            return None, None, None, 'release_update_check_failed'


@dataclass(frozen=True)
class Inspection:
    owner: object
    request: object = None
    cancellation: object = field(default_factory=threading.Event)

    def run(self):
        # No Qt mutation in the worker. Errors are codes, not raw process output.
        try:
            o = self.owner
            bundle = o.loader(o.directory) if self.request is None else o.bundle
            if self.request is None:
                bundle = o.cached_bundle(bundle)
            transport = o.transport_factory(bundle.pins) if self.request is None else o.transport
            bundle.attest(transport.auditor)
            request = self.request or Request('install', ('core',))
            host = o.reader(request).collect()
            bundle.check_host(host, o.clock())
            if self.cancellation.is_set():
                raise BackendError('release_download_cancelled')
            if self.request is not None and request.operation == 'install' and bundle.release_assets:
                if bundle.trust.release_policy is not None:
                    if bundle.signed_release is None: raise BackendError('signed_catalog_required')
                    bundle = signed_bundle(bundle, bundle.signed_release.envelope, now=o.wall_clock(),
                                           previous=bundle.signed_release)
                if not set(request.components) <= set(installable(bundle.trust, host)):
                    raise BackendError('host_changed')
                if host.missing_dependencies:
                    raise BackendError('resolve_dependencies_separately')
                if 'core' in request.components and host.headers_release != host.kernel:
                    raise BackendError('matching_headers_required')
                before = host.fingerprint()
                by_component = {a.component: a for a in bundle.release_assets}
                blobs = tuple((c, o.downloader.fetch(by_component[c],
                              cancelled=self.cancellation.is_set)) for c in request.components)
                # A slow download must never preserve a stale package/session
                # snapshot or manufacture a pre-authentication success.
                host = o.reader(request).collect()
                bundle.check_host(host, o.clock())
                bundle.attest(transport.auditor)
                if self.cancellation.is_set():
                    raise BackendError('release_download_cancelled')
                if host.fingerprint() != before:
                    raise BackendError('host_changed')
                bundle = replace(bundle, blobs=blobs)
            return bundle, transport, host, ''
        except (BackendError, AuthorizationError) as error:
            return None, None, None, error.code
        except Exception:
            return None, None, None, 'package_inspection_failed'


def planning_reader(request):
    from package_preflight import PlanningEvidence
    return PlanningEvidence(request)


class AppImageTransactions(ExecutionTransactions):
    """One bounded operation per inspected session after possible effects.

    Absence/unknown reviews never become permission to remove arbitrary packages.
    Refreshing the ordinary display cannot unlock an uncertain transaction.
    """
    def __init__(self, directory, *, loader=load_bundle, reader=planning_reader,
                 transport_factory=PackageTransport, clock=time.monotonic, downloader=None,
                 wall_clock=time.time, update_cache=None):
        super().__init__(CachedEvidence(), Catalog(), {}, clock, transport=None)
        self.directory, self.loader, self.reader = directory, loader, reader
        self.transport_factory = transport_factory
        from release_download import ReleaseDownloader
        self.downloader = ReleaseDownloader() if downloader is None else downloader
        self.bundle, self.pending = None, None
        self.wall_clock, self.update_cache = wall_clock, update_cache
        self.update_error, self.update_result = '', ''
        self.state = 'loading'

    def cached_bundle(self, bundle):
        if bundle.trust.release_policy is not None and self.update_cache is not None:
            data = self.update_cache.read()
            if data is not None:
                bundle = signed_bundle(bundle, data, now=self.wall_clock(), allow_expired=True)
        return bundle

    def can_check_updates(self):
        return (self.bundle is not None and self.bundle.trust.release_policy is not None
                and self.state == 'idle' and self.pending is None and not self.uncertain)

    def begin_update_check(self):
        if not self.can_check_updates(): return None
        self.state, self.update_error, self.update_result = 'checking_updates', '', ''
        self.pending = UpdateInspection(self)
        return self.pending

    def initial_inspection(self):
        if self.state != 'loading' or self.pending is not None:
            return None
        self.pending = Inspection(self)
        return self.pending

    def begin_preparation(self):
        if self.state != 'editing':
            return None
        try:
            request = Request.parse({'schema': 1, 'operation': self.operation,
                                     'components': list(self.selected)})
        except BackendError as error:
            self.error = error.code
            return None
        self.state, self.error = 'checking', ''
        self.pending = Inspection(self, request)
        return self.pending

    def receive_inspection(self, task, result):
        if isinstance(task, UpdateInspection):
            if task is not self.pending or self.state != 'checking_updates': return False
            self.pending = None
            bundle, transport, host, error = result
            self.state = 'idle'
            if error:
                self.update_error = error
                return False
            self.bundle, self.transport, self.port.host = bundle, transport, host
            self.catalog, self.blobs = bundle.trust.catalog, {}
            self.update_result = str(bundle.signed_release.revision)
            return True
        if task is not self.pending or self.state not in ('loading', 'checking'):
            return False
        self.pending = None
        bundle, transport, host, error = result
        if error:
            self.state, self.error = ('blocked' if task.request is None else 'editing'), error
            self.port.host = None
            return False
        self.bundle, self.transport, self.port.host = bundle, transport, host
        self.catalog, self.blobs = bundle.trust.catalog, dict(bundle.blobs)
        self.transport.release_catalog = (bundle.signed_release.envelope if bundle.signed_release else None)
        if task.request is None:
            self.state, self.error = 'idle', ''
            return True
        self.state = 'editing'
        # Selection is frozen while checking; all selected versions must still
        # be reviewed, then the inherited planner uses exactly this fresh host.
        if not set(self.selected) <= set(self.available(self.operation)):
            self.error = 'host_changed'
            return False
        return super().prepare()

    def available(self, operation):
        if (self.bundle is None or self.port.host is None or self.uncertain
                or self.state in ('loading', 'blocked', 'checking_updates') or operation not in ('install', 'remove')):
            return ()
        installed = dict(self.port.host.installed)
        if operation == 'remove':
            approved = {(r.component, r.version) for r in self.bundle.trust.installed}
            return tuple(c for c, (name, _) in COMPONENTS.items() if (c, installed.get(name)) in approved)
        if self.bundle.trust.release_policy is not None and (
                self.bundle.signed_release is None or self.bundle.signed_release.expired):
            return ()
        return installable(self.bundle.trust, self.port.host)

    def prepare(self):
        # The GUI must schedule begin_preparation(), never reuse initial facts.
        return False

    def cancel(self):
        if self.state == 'checking_updates':
            if self.pending is not None: self.pending.cancellation.set()
            self.pending, self.state, self.update_error = None, 'idle', 'release_download_cancelled'
            return True
        if self.state == 'checking':
            if self.pending is not None:
                self.pending.cancellation.set()
            self.pending = None  # Late worker completion cannot recreate review.
            self.state, self.error = 'cancelled', ''
            return True
        return super().cancel()
