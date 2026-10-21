# SPDX-License-Identifier: GPL-2.0-only
"""Separate first-run offer/confirmation, then fresh normal package planning."""
from dataclasses import dataclass
from pathlib import Path

from artifacts import BackendError
from backend import Request
from app_packages import AppImageTransactions
from helper_setup import load_payload, SetupInspector, SetupSession
from privilege.protocol import AuthorizationError


@dataclass(frozen=True)
class FirstInspection:
    owner: object

    def run(self):
        try:
            o = self.owner
            bundle = o.cached_bundle(o.loader(o.directory))
            payload = o.payload_loader(Path(o.directory).parent / 'helper-payload', bundle)
            review = o.inspector.inspect(payload)
            host = o.reader(Request('install', ('core',))).collect()
            bundle.check_host(host, o.clock())
            transport = o.transport_factory(bundle.pins)
            if review is None: bundle.attest(transport.auditor)
            return bundle, payload, review, host, transport, ''
        except (BackendError, AuthorizationError) as error:
            return None, None, None, None, None, error.code
        except Exception:
            return None, None, None, None, None, 'setup_inspection_failed'


class FirstRunTransactions(AppImageTransactions):
    def __init__(self, directory, *, inspector=None, payload_loader=load_payload,
                 setup_runner=None, **kwargs):
        super().__init__(directory, **kwargs)
        self.inspector = SetupInspector() if inspector is None else inspector
        self.payload_loader, self.setup_runner = payload_loader, setup_runner
        self.setup_payload = self.setup_review = self.setup_session = self.setup_result = None

    def initial_inspection(self):
        if self.state != 'loading' or self.pending is not None: return None
        self.pending = FirstInspection(self)
        return self.pending

    def receive_inspection(self, task, result):
        if not isinstance(task, FirstInspection):
            return super().receive_inspection(task, result)
        if task is not self.pending or self.state != 'loading': return False
        self.pending = None
        bundle, payload, review, host, transport, error = result
        if error:
            self.state, self.error = 'blocked', error
            return False
        self.bundle, self.setup_payload, self.setup_review = bundle, payload, review
        if review is not None:
            self.port.host = host
            self.state, self.error = 'setup_required', ''
            return True
        self.catalog, self.blobs = bundle.trust.catalog, dict(bundle.blobs)
        transport.release_catalog = bundle.signed_release.envelope if bundle.signed_release else None
        self.port.host, self.transport = host, transport
        self.state, self.error = 'idle', ''
        return True

    def available(self, operation):
        if self.state.startswith('setup_'): return ()
        return super().available(operation)

    def request_setup(self):
        if self.state != 'setup_required': return False
        self.state = 'setup_review'
        original = self.port.host.fingerprint()
        bundle = self.bundle
        def fresh_check():
            host = self.reader(Request('install', ('core',))).collect()
            bundle.check_host(host, self.clock())
            if host.fingerprint() != original:
                raise BackendError('host_changed')
        self.setup_session = SetupSession(self.setup_payload, self.setup_review,
            inspector=self.inspector, fresh_check=fresh_check, runner=self.setup_runner, clock=self.clock)
        return True

    def begin_setup(self):
        if self.state != 'setup_review' or self.setup_session is None: return None
        self.state = 'setup_running'
        return self.setup_session

    def receive_setup(self, session, outcome):
        if (self.state != 'setup_running' or session is not self.setup_session
                or outcome is None or session.outcome is not outcome):
            return False
        self.setup_result = outcome
        self.state = 'setup_done' if outcome.state == 'verified_setup' else 'setup_failed'
        self.error = outcome.error
        return True

    def cancel_setup(self):
        if self.state != 'setup_review': return False
        self.setup_session = None
        self.state = 'setup_required'
        return True

    def finish_setup(self):
        if self.state != 'setup_done': return False
        # Fresh reinspection is passive only. Never install a selected package
        # or invoke pkexec in response to a helper-setup result.
        self.setup_session = self.setup_result = None
        self.state, self.error = 'loading', ''
        return True
