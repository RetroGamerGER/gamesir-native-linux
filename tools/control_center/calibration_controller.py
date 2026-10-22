# SPDX-License-Identifier: GPL-2.0-only
"""Offline-prepared controller adapter. Default channel has no hardware backend.

The injected channel must own the native per-device maintenance/stream path.
The optional native adapter has a separately opted-in E0 continuity contract.
It must never claim a physically identified radio lifetime. No raw USB,
sysfs, ioctl, device enumeration, mode change, driver detach or replay fallback.
"""
from dataclasses import dataclass
import math
import time
from typing import Protocol

from calibration_protocol import PositionPolicy, calibration_message, decode_telemetry
from stick_calibration import (Calibration, CalibrationFailure, Instance, Intent,
                               RunKey, Sample, ACTIVE_PHASES, MAX_SAMPLE_AGE)

CAPABILITIES = frozenset(('tmr-provider-v1', 'e0-stream-v1', 'exclusive-maintenance-v1'))
CONTINUITY_CAPABILITIES = frozenset(('tmr-provider-v1', 'e0-snapshot-v1',
                                    'exclusive-maintenance-v1', 'fresh-e0-continuity-v1'))


@dataclass(frozen=True)
class Target:
    instance: Instance
    vendor: int
    product: int
    port_token: int
    instance_token: int

    def __post_init__(self):
        if (not isinstance(self.instance, Instance) or type(self.vendor) is not int
                or self.vendor != 0x3537 or type(self.product) is not int
                or self.product not in (0x109c, 0x105e)
                or any(type(v) is not int or not 0 < v < 2**64
                       for v in (self.port_token, self.instance_token))):
            raise ValueError('Unsupported or incomplete native controller identity')


@dataclass(frozen=True)
class Lease:
    key: RunKey
    target: Target
    token: str
    expires_at: float
    connected: bool
    exclusive: bool
    owner: str
    capabilities: frozenset[str]
    link_basis: str = 'rf_identity'


@dataclass(frozen=True)
class Report:
    key: RunKey
    target: Target
    lease_token: str
    number: int
    timestamp: float
    data: bytes


class Channel(Protocol):
    """Proposed provider-level API, not an existing gs_native ABI or wire format.

    Operations are bounded and serialized by the owner. acquire never unbinds a
    driver; inspect must attest the current RF connection, not just USB presence.
    send_message shares the owner's GIP sequence/output serialization and returns
    immediate submission success only. release drops this lease, not device mode.
    """
    def acquire(self, target, key): ...
    def inspect(self, lease): ...
    def send_message(self, lease, message): ...
    def release(self, lease): ...


class ChannelUnavailable(RuntimeError):
    """Conclusive rejection before any lease was acquired."""


class UnavailableChannel:
    """Production default. No methods open a path, socket or hardware handle."""
    def acquire(self, target, key):
        raise ChannelUnavailable('Native calibration API is not implemented')

    def inspect(self, lease):
        raise RuntimeError('No calibration lease')

    def send_message(self, lease, message):
        raise RuntimeError('No calibration transport')

    def release(self, lease):
        raise RuntimeError('No calibration lease')


class _Port:
    def __init__(self, adapter):
        self.adapter = adapter
        self.state = 'new'

    def submit(self, intent):
        a = self.adapter
        if (not isinstance(intent, Intent) or intent.key != a.session.key
                or intent.operation not in ('Start', 'Finish', 'Exit')):
            raise CalibrationFailure()
        if not a._confirm():
            raise CalibrationFailure(connection_lost=True)
        if (intent.operation == 'Start' and self.state != 'new'
                or intent.operation != 'Start' and self.state != 'started'):
            raise CalibrationFailure()
        if intent.operation == 'Finish' and (a.latest is None
                or (a.latest.active & a.latest.done) != 3):
            raise CalibrationFailure()
        expected = {'Start': 'measuring', 'Finish': 'completed', 'Exit': 'cancelled'}
        if a.session.phase != expected[intent.operation]:
            raise CalibrationFailure()
        # Consume BEFORE calling the channel. Even uncertain/partial delivery
        # must not become another Start/Finish/Exit attempt.
        self.state = 'failed'
        try:
            accepted = a.channel.send_message(a.lease, calibration_message(intent.operation))
        except Exception:
            a._problem('submission_failed')
            raise CalibrationFailure() from None
        if accepted is not True:
            a._problem('submission_failed')
            raise CalibrationFailure()
        if not a._confirm():
            raise CalibrationFailure(connection_lost=True)
        self.state = {'Start': 'started', 'Finish': 'finished', 'Exit': 'exited'}[intent.operation]


class ControllerCalibration:
    """Bind the accepted session logic to scoped provider reports and commands.

    Inert on construction. The experimental root helper explicitly opts into
    fresh-E0 continuity; the default remains the stronger RF-identity contract.
    """
    def __init__(self, positions, *, channel=None, clock=time.monotonic, allow_continuity=False):
        if not isinstance(positions, PositionPolicy):
            raise ValueError('Choose an explicit position-mapping policy')
        self.positions = positions
        self.channel = channel if channel is not None else UnavailableChannel()
        self.clock = clock
        self.allow_continuity = allow_continuity is True
        self.lease = None
        self.target = None
        self.latest = None
        self.first_report_deadline = None
        self.problem = ''
        self.cleanup_problem = ''
        self.release_attempted = False
        self.acquisition_uncertain = False
        self.port = _Port(self)
        self.session = Calibration(self.port, clock=clock)

    def _problem(self, reason):
        if not self.problem:
            self.problem = reason  # Cleanup or a later check cannot hide the cause.

    def _valid_lease(self, lease):
        return (isinstance(lease, Lease) and lease.key == self.session.key
                and lease.target == self.target and type(lease.token) is str
                and 16 <= len(lease.token) <= 128
                and type(lease.expires_at) in (float, int) and 0 < lease.expires_at < 2**53
                and math.isfinite(lease.expires_at)
                and lease.expires_at > self.clock()
                and lease.exclusive is True and lease.owner == 'gs_native'
                and type(lease.capabilities) is frozenset
                and ((lease.link_basis == 'rf_identity' and lease.connected is True
                      and CAPABILITIES <= lease.capabilities)
                     or (self.allow_continuity and lease.connected is False
                         and lease.link_basis == 'fresh_e0_continuity_only'
                         and CONTINUITY_CAPABILITIES <= lease.capabilities)))

    def open(self, target):
        if (not isinstance(target, Target) or self.lease is not None or self.acquisition_uncertain
                or self.session.phase in ACTIVE_PHASES):
            return False
        key = self.session.open(target.instance)
        if key is None:
            return False
        self.target, self.latest = target, None
        self.problem = self.cleanup_problem = ''
        self.release_attempted = False
        self.port.state = 'new'
        try:
            candidate = self.channel.acquire(target, key)
        except ChannelUnavailable:
            self._problem('calibration_api_unavailable')
            self.session.fail()
            return False
        except Exception:
            self.acquisition_uncertain = True
            self._problem('acquisition_unconfirmed')
            self.session.fail()
            return False
        if not self._valid_lease(candidate):
            self.acquisition_uncertain = True
            self._problem('acquisition_not_attested')
            self.session.fail()
            # Never release another device/client's unexpected lease. A real
            # broker must expire unconfirmed acquisitions under its own lease.
            return False
        self.lease = candidate
        if not self._confirm():
            self.session.disconnect(key)
            self._settle()
            return False
        self.first_report_deadline = self.clock() + MAX_SAMPLE_AGE
        return True

    def _confirm(self):
        if self.lease is None:
            self._problem('lease_missing')
            return False
        try:
            current = self.channel.inspect(self.lease)
        except Exception:
            self._problem('observation_failed')
            return False
        if (not self._valid_lease(current) or current.token != self.lease.token):
            self._problem('connection_or_owner_changed')
            return False
        self.lease = current
        return True

    def _settle(self):
        if self.session.phase in ACTIVE_PHASES or self.lease is None or self.release_attempted:
            return
        self.release_attempted = True
        try:
            released = self.channel.release(self.lease)
        except Exception:
            released = False
        if released is True:
            self.lease = None
        else:
            self.cleanup_problem = 'lease_release_unconfirmed'
            # Keep the unresolved original lease, block another run, never
            # retry a protocol command or automatically resume the manager.

    def _check(self):
        if self.session.phase not in ACTIVE_PHASES:
            return False
        if not self._confirm():
            self.session.disconnect(self.session.key)
            self._settle()
            return False
        return True

    def _first_report_wait(self):
        if self.latest is not None:
            return False
        if self.first_report_deadline is not None and self.clock() >= self.first_report_deadline:
            self._problem('first_report_timeout')
            self.session.disconnect(self.session.key)
            self._settle()
        return True

    def receive(self, report):
        return self._receive(report, confirmed=False)

    def _receive(self, report, *, confirmed):
        if (not isinstance(report, Report) or self.lease is None
                or report.key != self.session.key or report.target != self.target
                or report.lease_token != self.lease.token):
            return False  # Foreign/stale input never refreshes connection proof.
        if not confirmed and not self._check():
            return False
        if self.latest is None and self.first_report_deadline is not None and self.clock() >= self.first_report_deadline:
            self._first_report_wait()
            return False
        if type(report.data) is not bytes:
            self._problem('invalid_telemetry')
            self.session.fail(); self._settle()
            return False
        if report.data and report.data[0] != 0x10:
            return False  # Gamepad/Guide/status traffic is not an E0 heartbeat.
        if len(report.data) >= 5 and report.data[4] != 0xe0:
            return False  # Other vendor replies do not manufacture readiness.
        try:
            telemetry = decode_telemetry(report.data)
            left, right = self.positions.positions(telemetry)
        except ValueError:
            self._problem('invalid_telemetry')
            self.session.fail(); self._settle()
            return False
        sample = Sample(report.number, report.timestamp, left, right,
                        telemetry.active, telemetry.done)
        accepted = self.session.feed(report.key, sample)
        if accepted:
            self.latest = telemetry
        elif self.session.phase not in ACTIVE_PHASES:
            self._problem('stale_or_invalid_stream')
        self._settle()
        return accepted

    def poll(self):
        """Inspect once, consume that exact snapshot, then advance the timer.

        report() reads the channel's already inspected snapshot, not a new
        transport read. Device commands retain independent pre/post checks.
        """
        if self._check():
            try:
                report = self.channel.report()
            except Exception:
                self._problem('observation_failed')
                self.session.disconnect(self.session.key)
            else:
                # feed() rejects a repeated number/time pair without refreshing
                # liveness; keep normal identity/format checks for every read.
                self._receive(report, confirmed=True)
                if self.session.phase in ACTIVE_PHASES and not self._first_report_wait():
                    self.session.tick(self.session.key)
        self._settle()

    def prepare(self):
        result = self._check() and not self._first_report_wait() and self.session.prepare()
        self._settle()
        return result

    def tick(self):
        if self._check() and not self._first_report_wait():
            self.session.tick(self.session.key)
        self._settle()

    def finish(self):
        result = self._check() and self.session.finish()
        self._settle()
        return result

    def close(self):
        if self._check():
            self.session.cancel()
        self._settle()

    def connection_lost(self, key):
        if key != self.session.key:
            return False
        changed = self.session.disconnect(key)
        if changed:
            self._problem('connection_lost')
            self._settle()
        return changed

    def view(self):
        return dict(self.session.snapshot(), adapterProblem=self.problem,
                    cleanupProblem=self.cleanup_problem,
                    leaseHeld=self.lease is not None,
                    acquisitionUncertain=self.acquisition_uncertain,
                    linkBasis=self.lease.link_basis if self.lease else '')
