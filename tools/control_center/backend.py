# SPDX-License-Identifier: GPL-2.0-only
"""Phase C planning/rehearsal. No installed-system transport is built here.

The separate package executor reuses the planner and independently attests
host state, trust records and exact ALPM transactions. Client JSON is never
authority. Session.rehearse accepts explicitly injected rehearsal doubles only;
normal GUI launch constructs neither a rehearsal nor a package executor.
"""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re

from artifacts import BackendError, Catalog, COMPONENTS, HEX, PUBLIC_BINARIES, VERSION

SCHEMA = 1
MAX_AGE = 30.0
PLAN_LIFETIME = 120.0
# Foreign/AUR inventory can legitimately begin with an r-prefixed VCS version.
# Project artifact versions retain the separate stricter VERSION grammar.
INSTALLED_VERSION = re.compile(r'[0-9A-Za-z][0-9A-Za-z.+_:~\-]{0,95}\Z')
ORDER = ('core', 'steam', 'gamescope', 'bridge')
REMOVE_ORDER = ('gamescope', 'bridge', 'steam', 'core')
HOOK_EFFECTS = ('controller_release', 'service_stop', 'verified_module_unload',
                'dkms', 'module_dependencies', 'systemd_metadata',
                'possible_snapshot', 'possible_initramfs')
PRESERVED = ('xpad', 'usbhid', 'other_controllers', 'user_modprobe_overrides',
             'manager_recovery_state', 'haptics_group_memberships',
             'steam_profiles', 'global_sdl_environment', 'application_launch_options')


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class Request:
    operation: str
    components: tuple

    @classmethod
    def parse(cls, data):
        if (type(data) is not dict or set(data) != {'schema', 'operation', 'components'}
                or type(data['schema']) is not int or data['schema'] != SCHEMA
                or type(data['operation']) is not str or data['operation'] not in ('install', 'remove')
                or type(data['components']) is not list):
            raise BackendError('invalid_request')
        parts = data['components']
        if (not parts or len(parts) > len(ORDER) or any(type(p) is not str or p not in ORDER for p in parts)
                or len(set(parts)) != len(parts)):
            raise BackendError('invalid_components')
        order = ORDER if data['operation'] == 'install' else REMOVE_ORDER
        return cls(data['operation'], tuple(p for p in order if p in parts))


@dataclass(frozen=True)
class HostEvidence:
    """Synthetic authoritative-adapter contract, NOT a Phase-B GUI snapshot."""
    distribution: str
    architecture: str
    kernel: str
    headers_release: str
    boot_id: str
    database_token: str
    observed_at: float
    installed: tuple = ()
    missing_dependencies: tuple = ()
    database_locked: bool = False
    native_loaded: bool = False
    service_enabled: bool = False

    def validate(self, now):
        if (not isinstance(now, (int, float)) or isinstance(now, bool) or not math.isfinite(now)
                or not isinstance(self.observed_at, (int, float)) or isinstance(self.observed_at, bool)
                or not math.isfinite(self.observed_at) or not 0 <= now - self.observed_at <= MAX_AGE):
            raise BackendError('stale_host_evidence')
        if (any(type(v) is not str for v in (self.distribution, self.architecture, self.kernel,
                                            self.headers_release, self.boot_id, self.database_token))
                or not HEX.fullmatch(self.database_token) or not re.fullmatch(
                r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', self.boot_id)
                or not re.fullmatch(r'[A-Za-z0-9_.+\-]{1,160}', self.kernel)
                or type(self.installed) is not tuple or type(self.missing_dependencies) is not tuple
                or type(self.database_locked) is not bool or type(self.native_loaded) is not bool
                or type(self.service_enabled) is not bool):
            raise BackendError('invalid_host_evidence')
        seen = set()
        for row in self.installed:
            if (type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
                    or type(row[1]) is not str or not re.fullmatch(r'[a-z0-9@+_.-]+', row[0])
                    or not INSTALLED_VERSION.fullmatch(row[1]) or row[0] in seen):
                raise BackendError('invalid_installed_packages')
            seen.add(row[0])
        if self.database_locked:
            raise BackendError('package_database_locked')

    def fingerprint(self):
        # Freshness time can change; every material host precondition must match.
        state = asdict(self)
        state.pop('observed_at')
        state['installed'] = sorted(state['installed'])
        return digest(state)


@dataclass(frozen=True)
class Plan:
    request: Request
    host: HostEvidence
    artifacts: tuple
    expires_at: float
    purpose: str = 'offline_rehearsal'

    @property
    def packages(self):
        return tuple(COMPONENTS[c][0] for c in self.request.components)

    @property
    def needs_core_guard(self):
        return 'core' in self.request.components and COMPONENTS['core'][0] in dict(self.host.installed)

    def summary(self):
        """Stable versioned data, no shell fragments, user paths or activation."""
        effects = list(HOOK_EFFECTS[3:]) if 'core' in self.request.components else [
            'package_metadata', 'next_session_environment']
        if self.needs_core_guard:
            effects = list(HOOK_EFFECTS[:3]) + effects
            if self.request.operation == 'remove':
                effects.append('service_disable')
        return {'schema': SCHEMA, 'operation': self.request.operation,
                'packages': list(self.packages),
                'artifacts': [{'component': a.review.component, 'version': a.review.version,
                               'sha256': a.review.digest, 'source_commit': a.review.source_commit,
                               'tag': a.review.tag} for a in self.artifacts],
                'host_fingerprint': self.host.fingerprint(), 'expires_at': self.expires_at,
                'existing_alpm_core_guard_required': self.needs_core_guard,
                'hook_effects': effects,
                'preserved': list(PRESERVED), 'activate': False, 'reboot': False,
                'offline_preparation_only': self.purpose != 'packages'}

    @property
    def confirmation_id(self):
        # An acknowledgement identifier, NOT a credential or administrator grant.
        return digest(self.summary())


def build_plan(request, host, blobs=None, *, catalog=PUBLIC_BINARIES, now, purpose='offline_rehearsal'):
    # Revalidate even directly constructed Request objects.
    request = Request.parse({'schema': SCHEMA, 'operation': request.operation,
                             'components': list(request.components)})
    if purpose not in ('offline_rehearsal', 'packages'):
        raise BackendError('invalid_plan_purpose')
    host.validate(now)
    if host.distribution not in ('garuda', 'cachyos') or host.architecture != 'x86_64':
        raise BackendError('unsupported_platform')
    installed = dict(host.installed)
    artifacts = []
    blobs = {} if blobs is None else blobs
    if type(blobs) is not dict or set(blobs) - set(request.components):
        raise BackendError('unexpected_artifact')
    if request.operation == 'install':
        if host.missing_dependencies:
            raise BackendError('resolve_dependencies_separately')
        if set(blobs) != set(request.components):
            raise BackendError('missing_reviewed_artifact')
        if 'core' in request.components:
            if host.headers_release != host.kernel:
                raise BackendError('matching_headers_required')
            if COMPONENTS['core'][0] not in installed and host.native_loaded:
                raise BackendError('unowned_loaded_module')
            if COMPONENTS['core'][0] not in installed and host.service_enabled:
                raise BackendError('unowned_enabled_service')
        for component in request.components:
            artifact = catalog.verify(component, blobs[component])
            previous = installed.get(artifact.package)
            if previous == artifact.review.version:
                raise BackendError('already_installed')
            if previous and previous not in artifact.review.upgrade_from:
                raise BackendError('unreviewed_version_transition')
            artifacts.append(artifact)
        after = {**installed, **{a.package: a.review.version for a in artifacts}}
    else:
        if blobs:
            raise BackendError('unexpected_artifact')
        if any(COMPONENTS[c][0] not in installed for c in request.components):
            raise BackendError('selected_package_absent')
        after = {name: value for name, value in installed.items()
                 if name not in {COMPONENTS[c][0] for c in request.components}}
    # Match existing recipes, never use recursive removal or remove dependents silently.
    if (COMPONENTS['gamescope'][0] in after and COMPONENTS['steam'][0] not in after
            or COMPONENTS['bridge'][0] in after and COMPONENTS['core'][0] not in after):
        raise BackendError('dependent_component_requires_explicit_selection')
    if 'gamescope' in request.components and request.operation == 'install' and host.distribution != 'cachyos':
        raise BackendError('gamescope_requires_cachyos')
    return Plan(request, host, tuple(artifacts), now + PLAN_LIFETIME, purpose)


@dataclass(frozen=True)
class TransactionPreview:
    """Future ALPM prepare result must exactly match the reviewed transaction."""
    packages: tuple
    versions: tuple
    downloads: tuple = ()
    other_removals: tuple = ()
    guard_verified: bool = False


@dataclass(frozen=True)
class Verification:
    installed: tuple
    core_guard_clear: bool = False
    dkms_kernel: str = ''
    module_version: str = ''
    vermagic_kernel: str = ''
    service_inactive: bool = False
    module_absent: bool = False
    service_enabled: bool = False
    dkms_installed: bool = False
    dkms_absent: bool = False


class RehearsalPort(ABC):
    """Only test doubles implement this. No live/default implementation supplied."""
    @abstractmethod
    def observe(self):
        pass

    @abstractmethod
    def prepare(self, plan):
        pass

    @abstractmethod
    def authorize(self, plan):
        pass

    @abstractmethod
    def commit(self, plan):
        """The ALPM pretransaction hook owns cleanup; never run a second guard."""

    @abstractmethod
    def verify(self, plan):
        pass


@dataclass(frozen=True)
class Outcome:
    state: str
    stage: str
    error: str = ''
    changes_possible: bool = False


class Session:
    def __init__(self, plan):
        self.plan = plan
        self.used = False
        self.outcome = None
        self.first_failure = None

    def cancel(self):
        if self.used:
            return self.outcome
        self.used = True
        self.outcome = Outcome('cancelled', 'confirmation')
        return self.outcome

    def rehearse(self, confirmation_id, port, *, clock):
        if self.used:
            # Preserve the FIRST outcome, including its original error.
            return self.outcome
        self.used = True
        stage, changes = 'confirmation', False
        try:
            if not isinstance(port, RehearsalPort):
                raise BackendError('offline_test_double_required')
            if confirmation_id != self.plan.confirmation_id:
                raise BackendError('confirmation_mismatch')
            self.check_time(clock())
            stage = 'fresh_preflight'
            fresh = port.observe()
            fresh.validate(self.check_time(clock()))
            if fresh.fingerprint() != self.plan.host.fingerprint():
                raise BackendError('host_changed')
            # Immutable bytes are rechecked; no mutable user path is passed to an executor.
            for artifact in self.plan.artifacts:
                Catalog((artifact.review,)).verify(artifact.review.component, artifact.data)
            stage = 'transaction_preview'
            preview = port.prepare(self.plan)
            versions = tuple((a.package, a.review.version) for a in self.plan.artifacts)
            if (not isinstance(preview, TransactionPreview) or preview.packages != self.plan.packages
                    or any(type(v) is not tuple for v in (preview.packages, preview.versions,
                                                         preview.downloads, preview.other_removals))
                    or type(preview.guard_verified) is not bool
                    or preview.versions != versions or preview.downloads or preview.other_removals):
                raise BackendError('unexpected_package_transaction')
            if self.plan.needs_core_guard and preview.guard_verified is not True:
                raise BackendError('installed_core_guard_unverified')
            stage = 'authorization'
            if port.authorize(self.plan) is not True:
                self.outcome = Outcome('cancelled', stage)
                return self.outcome
            # Reattest after the administrator-interaction boundary as well.
            stage = 'final_preflight'
            final = port.observe()
            final.validate(self.check_time(clock()))
            if final.fingerprint() != fresh.fingerprint():
                raise BackendError('host_changed')
            stage, changes = 'package_transaction', True
            port.commit(self.plan)
            stage = 'post_verification'
            check = port.verify(self.plan)
            self.check_postflight(check)
            self.outcome = Outcome('simulated_success', stage, changes_possible=True)
        except BackendError as error:
            self.first_failure = error
            self.outcome = Outcome('blocked' if not changes else 'failed', stage, error.code, changes)
        except Exception as error:
            self.first_failure = error
            self.outcome = Outcome('blocked' if not changes else 'uncertain', stage, 'adapter_failure', changes)
        return self.outcome

    def check_time(self, now):
        if (not isinstance(now, (int, float)) or isinstance(now, bool) or not math.isfinite(now)
                or not self.plan.expires_at - PLAN_LIFETIME <= now <= self.plan.expires_at):
            raise BackendError('plan_expired')
        return now

    def check_postflight(self, check):
        if not isinstance(check, Verification):
            raise BackendError('verification_unavailable')
        before = dict(self.plan.host.installed)
        expected = dict(before)
        if self.plan.request.operation == 'install':
            expected.update((a.package, a.review.version) for a in self.plan.artifacts)
        else:
            for name in self.plan.packages:
                expected.pop(name)
        if dict(check.installed) != expected or len(check.installed) != len(expected):
            raise BackendError('package_postcheck_mismatch')
        if 'core' in self.plan.request.components:
            if check.service_inactive is not True or check.module_absent is not True:
                raise BackendError('unexpected_runtime_activation')
            expected_enabled = (self.plan.host.service_enabled if self.plan.needs_core_guard
                                and self.plan.request.operation == 'install' else False)
            if check.service_enabled is not expected_enabled:
                raise BackendError('unexpected_service_enablement')
            if self.plan.needs_core_guard and check.core_guard_clear is not True:
                raise BackendError('return_not_verified')
            if self.plan.request.operation == 'install':
                version = next(a.review.version.rsplit('-', 1)[0] for a in self.plan.artifacts
                               if a.review.component == 'core')
                if (check.dkms_kernel != self.plan.host.kernel or check.module_version != version
                        or check.vermagic_kernel != self.plan.host.kernel or check.dkms_installed is not True):
                    raise BackendError('dkms_or_module_postcheck_mismatch')
            elif check.dkms_absent is not True:
                raise BackendError('dkms_removal_unverified')
