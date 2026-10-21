# SPDX-License-Identifier: GPL-2.0-only
"""Independently checked package transaction, with injected system boundaries.

Import is inert. No production factory or GUI flag constructs this executor.
The caller's plan is a proposal, never the helper's trust source. The ALPM
adapter owns one lock from observation through commit and post-verification.
"""
from dataclasses import dataclass, replace
import time

from artifacts import BackendError, Catalog, COMPONENTS
from backend import Outcome, Session, TransactionPreview, build_plan


@dataclass(frozen=True)
class InstalledReview:
    component: str
    version: str
    guards: tuple = ()


class ExecutionTrust:
    def __init__(self, catalog, installed=(), release_policy=None):
        if not isinstance(catalog, Catalog):
            raise BackendError('invalid_execution_trust')
        self.catalog = catalog
        self.installed = tuple(installed)
        self.release_policy = release_policy
        keys = set()
        from artifacts import VERSION, CORE_GUARDS, HEX
        for row in self.installed:
            if (not isinstance(row, InstalledReview) or type(row.component) is not str
                    or row.component not in COMPONENTS or type(row.version) is not str
                    or not VERSION.fullmatch(row.version)
                    or (row.component, row.version) in keys or type(row.guards) is not tuple):
                raise BackendError('invalid_execution_trust')
            keys.add((row.component, row.version))
            if any(type(r) is not tuple or len(r) != 2 or any(type(v) is not str for v in r)
                   for r in row.guards):
                raise BackendError('invalid_execution_trust')
            if row.component == 'core':
                if (len(row.guards) != len(CORE_GUARDS)
                        or {p for p, _ in row.guards} != set(CORE_GUARDS)
                        or any(not HEX.fullmatch(h) for _, h in row.guards)):
                    raise BackendError('unreviewed_core_guards')
            elif row.guards:
                raise BackendError('unexpected_core_guards')

    def installed_record(self, component, version):
        record = next((r for r in self.installed
                       if r.component == component and r.version == version), None)
        if record is None:
            raise BackendError('unreviewed_installed_version')
        return record


# Separate root-owned deployment review must populate these. Never read a
# catalog, approval, package path or executable from a GUI/user JSON document.
DEPLOYMENT_TRUST = ExecutionTrust(Catalog())


class PackageExecutor:
    def __init__(self, trust, adapter, *, clock=time.monotonic, release_guard=None):
        self.trust, self.adapter, self.clock = trust, adapter, clock
        self.used = False
        self.outcome = None
        self.first_failure = None
        self.release_guard = release_guard

    def run(self, proposal):
        if self.used:
            return self.outcome
        self.used = True
        changes, stage, locked = False, 'privileged_preflight', False
        try:
            if not isinstance(self.trust, ExecutionTrust):
                raise BackendError('invalid_execution_trust')
            if self.trust.release_policy is not None and self.release_guard is None:
                raise BackendError('release_resolver_required')
            if proposal.purpose != 'packages':
                raise BackendError('package_plan_required')
            # Reject expired requests before opening a transaction. Authentication
            # already happened in the distinct fixed pkexec entry, not via a
            # reusable authorization-only acknowledgement.
            Session(proposal).check_time(self.clock())
            self.adapter.acquire()
            locked = True
            fresh = self.adapter.observe()  # Authoritative, under our ALPM lock.
            fresh.validate(self.clock())
            if fresh.fingerprint() != proposal.host.fingerprint():
                raise BackendError('host_changed')
            blobs = {a.review.component: a.data for a in proposal.artifacts}
            plan = build_plan(proposal.request, fresh, blobs, catalog=self.trust.catalog,
                              now=self.clock(), purpose='packages')
            # Fresh evidence is newer than the original confirmation. Validate
            # it against NOW, but never extend that confirmation's deadline.
            plan = replace(plan, expires_at=proposal.expires_at)
            if plan.confirmation_id != proposal.confirmation_id:
                raise BackendError('privileged_plan_mismatch')
            for component in plan.request.components:
                version = dict(fresh.installed).get(COMPONENTS[component][0])
                if version is not None:
                    record = self.trust.installed_record(component, version)
                    if component == 'core':
                        # Hash and package ownership, plus effective hook override
                        # resolution, are inspected. This never runs cleanup.
                        self.adapter.attest_core_guard(record)
            stage = 'locked_package_preview'
            preview = self.adapter.prepare(plan)
            additions = tuple(sorted((a.package, a.review.version) for a in plan.artifacts))
            removals = tuple(sorted(plan.packages)) if plan.request.operation == 'remove' else ()
            if (not isinstance(preview, TransactionPreview)
                    or preview.packages != tuple(sorted(plan.packages))
                    or preview.versions != additions or preview.downloads
                    or preview.other_removals != removals
                    or plan.needs_core_guard and preview.guard_verified is not True):
                raise BackendError('unexpected_package_transaction')
            # No implicit dependency installation/removal, sync, recursive flags,
            # overwrite or hidden activation. Recheck after slow preparation.
            stage = 'final_privileged_preflight'
            Session(proposal).check_time(self.clock())
            final = self.adapter.observe()
            final.validate(self.clock())
            if final.fingerprint() != fresh.fingerprint():
                raise BackendError('host_changed')
            if plan.needs_core_guard:
                record = self.trust.installed_record('core', dict(fresh.installed)[COMPONENTS['core'][0]])
                self.adapter.attest_core_guard(record)
            if self.release_guard is not None:
                stage = 'release_catalog_checkpoint'
                self.release_guard.checkpoint()
            stage, changes = 'package_transaction', True
            # Existing ALPM hooks are the sole cleanup implementation. Hooks may
            # already have effects even if commit subsequently reports failure.
            self.adapter.commit()
            stage = 'privileged_postcheck'
            Session(plan).check_postflight(self.adapter.verify(plan))
            self.outcome = Outcome('verified_success', stage, changes_possible=True)
        except BackendError as error:
            self.first_failure = error
            self.outcome = Outcome('failed' if changes else 'blocked', stage, error.code, changes)
        except Exception as error:
            self.first_failure = error
            self.outcome = Outcome('uncertain' if changes else 'blocked', stage,
                                   'package_adapter_failure', changes)
        finally:
            if locked:
                try:
                    self.adapter.close()
                except Exception as error:
                    # Never overwrite an earlier error with cleanup failure.
                    if self.first_failure is None:
                        self.first_failure = error
                        self.outcome = Outcome('uncertain' if changes else 'blocked', 'lock_release',
                                               'package_lock_release_unverified', changes)
        return self.outcome
