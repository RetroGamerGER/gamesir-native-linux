# SPDX-License-Identifier: GPL-2.0-only
"""One-shot GUI-side authorization adapter; no implicit live transport."""
from dataclasses import dataclass
import secrets

from .protocol import AuthorizationError, Probe, verify_acknowledgement


@dataclass(frozen=True)
class AuthorizationResult:
    state: str
    error: str = ''
    # Authorizing this probe never executes or permits a package transaction.
    executed: bool = False


class AuthorizationAttempt:
    def __init__(self, plan, transport=None, *, nonce=None):
        self.probe = Probe(plan.request.operation, tuple(plan.request.components),
                           plan.confirmation_id, nonce or secrets.token_hex(32))
        self.transport = transport
        self.outcome = None
        self.used = False

    def run(self, *, cancelled=lambda: False):
        if self.used:
            return self.outcome
        self.used = True
        try:
            if cancelled():
                self.outcome = AuthorizationResult('cancelled')
            elif self.transport is None:
                raise AuthorizationError('authorization_transport_disabled')
            else:
                reply = self.transport.invoke(self.probe.wire(), cancelled=cancelled)
                if reply.state != 'complete':
                    states = {'cancelled': 'cancelled', 'timeout': 'timeout',
                              'completion_unknown': 'uncertain', 'output_limit': 'blocked'}
                    self.outcome = AuthorizationResult(states.get(reply.state, 'blocked'),
                                                       'authorization_' + reply.state)
                elif reply.returncode == 126:
                    self.outcome = AuthorizationResult('cancelled')
                elif reply.returncode == 127:
                    raise AuthorizationError('authorization_denied_or_agent_unavailable')
                elif reply.returncode != 0:
                    raise AuthorizationError('authorization_helper_failed')
                else:
                    verify_acknowledgement(reply.stdout, self.probe)
                    self.outcome = AuthorizationResult('authorized_only')
        except AuthorizationError as error:
            self.outcome = AuthorizationResult('blocked', error.code)
        except Exception:
            self.outcome = AuthorizationResult('blocked', 'authorization_transport_failed')
        return self.outcome
