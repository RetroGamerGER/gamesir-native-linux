# SPDX-License-Identifier: GPL-2.0-only
"""Explicit in-memory GUI fixtures, never real packages or release approvals.

Fake archives carry marker guard bytes, not executable installers. They are
trusted only by this synthetic catalog. PUBLIC_BINARIES stays empty.
"""
from dataclasses import replace
import hashlib
import io
import tarfile
import time

from artifacts import BackendError, Catalog, Review, COMPONENTS, CORE_GUARDS
from backend import HostEvidence, RehearsalPort, TransactionPreview, Verification
from transactions import Transactions

SCENARIOS = ('success', 'authorization_cancelled', 'host_changed',
             'transaction_failed', 'verification_failed')
KERNEL = '7.2.11-offline-fixture'
VERSION = '0.1.0.offline-1'


def fixture_catalog():
    records, blobs = [], {}
    for component, (name, arch) in COMPONENTS.items():
        dependencies = ((COMPONENTS['core'][0],) if component == 'bridge' else
                        (COMPONENTS['steam'][0],) if component == 'gamescope' else ())
        files = {'.PKGINFO': (f'pkgname = {name}\npkgver = {VERSION}\narch = {arch}\n'
                             'license = GPL-2.0-only\n' + ''.join(
                                 f'depend = {d}\n' for d in dependencies)).encode()}
        guards = {name: b'OFFLINE FIXTURE ONLY: NOT EXECUTABLE\n'
                  for name in CORE_GUARDS} if component == 'core' else {}
        files.update(guards)
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as archive:
            for path, content in files.items():
                member = tarfile.TarInfo(path)
                member.size, member.mode = len(content), 0o644
                archive.addfile(member, io.BytesIO(content))
        data = stream.getvalue()
        blobs[component] = data
        records.append(Review(component, VERSION, hashlib.sha256(data).hexdigest(), len(data),
                              '0' * 40, 'v0.0.0-offline-fixture', dependencies=dependencies,
                              guards=tuple((p, hashlib.sha256(v).hexdigest()) for p, v in guards.items())))
    return Catalog(records), blobs


class OfflinePort(RehearsalPort):
    def __init__(self, scenario, clock, authorization=None):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown offline scenario')
        self.scenario, self.clock = scenario, clock
        self.authorization = authorization
        self.host = HostEvidence('cachyos', 'x86_64', KERNEL, KERNEL,
                                 '00000000-0000-0000-0000-000000000000', '0' * 64, clock(),
                                 installed=(('unrelated-controller', '1.0-1'),))
        self.calls, self.after = [], None

    def observe(self):
        return replace(self.host, observed_at=self.clock())

    def prepare(self, plan):
        self.calls.append('prepare')
        if self.scenario == 'host_changed':
            self.host = replace(self.host, database_token='1' * 64)
        return TransactionPreview(plan.packages,
                                  tuple((a.package, a.review.version) for a in plan.artifacts),
                                  guard_verified=True)

    def authorize(self, plan):
        self.calls.append('authorize')
        if self.authorization is not None:
            # Injected offline tests can exercise the actual wire/client path.
            # This port still modifies only its synthetic inventory.
            from privilege.client import AuthorizationResult
            result = self.authorization(plan)
            if not isinstance(result, AuthorizationResult) or result.executed is not False:
                raise BackendError('invalid_authorization_result')
            if result.state == 'cancelled':
                return False
            if result.state != 'authorized_only':
                raise BackendError(result.error or 'authorization_not_granted')
            return True
        return self.scenario != 'authorization_cancelled'

    def commit(self, plan):
        self.calls.append('commit')
        if self.scenario == 'transaction_failed':
            raise BackendError('offline_transaction_failed')
        installed = dict(self.host.installed)
        if plan.request.operation == 'install':
            installed.update((a.package, a.review.version) for a in plan.artifacts)
        else:
            for package in plan.packages:
                installed.pop(package)
        enabled = self.host.service_enabled if plan.request.operation == 'install' and plan.needs_core_guard else False
        self.after = Verification(tuple(sorted(installed.items())), core_guard_clear=True,
                                  dkms_kernel=KERNEL, module_version='0.1.0.offline',
                                  vermagic_kernel=KERNEL, service_inactive=True, module_absent=True,
                                  service_enabled=enabled, dkms_installed=plan.request.operation == 'install',
                                  dkms_absent=plan.request.operation == 'remove')

    def verify(self, plan):
        self.calls.append('verify')
        if self.scenario == 'verification_failed':
            return replace(self.after, installed=())
        self.host = replace(self.host, installed=self.after.installed,
                            native_loaded=False, service_enabled=self.after.service_enabled,
                            database_token=hashlib.sha256(repr(self.after.installed).encode()).hexdigest())
        return self.after


def create_rehearsal(scenario='success', *, clock=time.monotonic, authorization=None):
    catalog, blobs = fixture_catalog()
    return Transactions(OfflinePort(scenario, clock, authorization), catalog, blobs, clock)
