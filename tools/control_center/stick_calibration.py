# SPDX-License-Identifier: GPL-2.0-only
"""Offline calibration coordinator. Named intents only; no device transport.

The firmware owns calibration math/storage. Ring coverage is a UI observation,
never the firmware's readiness signal. See CONTROL_CENTER_STICK_CALIBRATION.md.
"""
from dataclasses import dataclass
import math
import time

SECTORS = 24
PREPARATION_SECONDS = 3.0
MAX_SAMPLE_AGE = 1.5  # Preview heartbeat policy, not a firmware timeout.
ACTIVE_PHASES = frozenset(('ready', 'preparing', 'measuring', 'ready_to_finish'))


class CalibrationFailure(RuntimeError):
    """Bounded adapter failure, never raw device/backend error text."""
    def __init__(self, *, connection_lost=False):
        super().__init__('Calibration channel unavailable')
        self.connection_lost = connection_lost


@dataclass(frozen=True)
class Instance:
    device: str
    connection: str

    def __post_init__(self):
        if any(not isinstance(v, str) or not v.strip() or len(v) > 128
               for v in (self.device, self.connection)):
            raise ValueError('An exact device and connection instance are required')


@dataclass(frozen=True)
class RunKey:
    instance: Instance
    generation: int


@dataclass(frozen=True)
class Sample:
    sequence: int
    timestamp: float
    left: tuple[float, float]
    right: tuple[float, float]
    active: int
    done: int


@dataclass(frozen=True)
class Intent:
    key: RunKey
    operation: str


class MemoryPort:
    """Records semantic test intents, never bytes or commands to a real device."""
    def __init__(self):
        self.intents = []
        self.fail_on = set()

    def submit(self, intent):
        self.intents.append(intent)
        if intent.operation in self.fail_on:
            raise RuntimeError('Simulated transfer failure')


class Calibration:
    def __init__(self, port=None, *, clock=time.monotonic):
        self.port = port if port is not None else MemoryPort()
        self.clock = clock
        self.key = None
        self.generation = 0
        self.phase = 'idle'
        self.reason = ''
        self.connected = False
        self.started = False
        self.last_sample_at = None
        self.last_sequence = -1
        self.deadline = None
        self.active = self.done = 0
        self.seen_active = False
        self.left = self.right = (0.0, 0.0)
        self.visited = [set(), set()]

    def open(self, instance):
        if not isinstance(instance, Instance) or self.phase in ACTIVE_PHASES:
            return None
        self.generation += 1
        self.key = RunKey(instance, self.generation)
        self.phase, self.reason = 'ready', ''
        self.connected, self.started, self.seen_active = True, False, False
        self.last_sample_at, self.last_sequence = None, -1
        self.deadline = None
        self.active = self.done = 0
        self.left = self.right = (0.0, 0.0)
        self.visited = [set(), set()]
        return self.key

    def _fresh(self):
        return (self.connected and self.last_sample_at is not None
                and 0 <= self.clock() - self.last_sample_at <= MAX_SAMPLE_AGE)

    def _end(self, phase, reason=''):
        self.phase, self.reason = phase, reason
        self.deadline = None
        self.active = self.done = 0

    def _submit(self, operation):
        try:
            self.port.submit(Intent(self.key, operation))
        except CalibrationFailure as failure:
            if failure.connection_lost:
                self.connected = False
            self._end('lost' if failure.connection_lost else 'error',
                      'connection' if failure.connection_lost else 'transfer')
            return False
        except Exception:
            # Delivery uncertainty is terminal. No retry, Finish or automatic Exit.
            self._end('error', 'transfer')
            return False
        return True

    def fail(self):
        """Stop an externally rejected current run without a compensating command."""
        if self.phase not in ACTIVE_PHASES:
            return False
        self._end('error', 'transfer')
        return True

    def prepare(self):
        if self.phase != 'ready':
            return False
        if not self._fresh():
            self.disconnect(self.key)
            return False
        self.phase = 'preparing'
        self.deadline = self.clock() + PREPARATION_SECONDS
        return True

    def tick(self, key):
        if key != self.key or self.phase not in ACTIVE_PHASES:
            return
        if not self._fresh():
            self.disconnect(key)
        elif self.phase == 'preparing' and self.clock() >= self.deadline:
            # Consume the delayed action before submission; duplicate timer calls
            # cannot start twice or start a later generation.
            self.phase, self.deadline = 'measuring', None
            if self._submit('Start'):
                self.started = True

    @staticmethod
    def _valid(sample, now):
        return (isinstance(sample, Sample)
                and type(sample.sequence) is int and sample.sequence >= 0
                and type(sample.timestamp) in (int, float)
                and -2**53 < sample.timestamp < 2**53
                and math.isfinite(sample.timestamp)
                and 0 <= now - sample.timestamp <= MAX_SAMPLE_AGE
                and all(type(mask) is int and 0 <= mask <= 3
                        for mask in (sample.active, sample.done))
                and all(isinstance(pair, tuple) and len(pair) == 2
                        and all(type(v) in (int, float) and -1 <= v <= 1
                                and math.isfinite(v) for v in pair)
                        for pair in (sample.left, sample.right)))

    def feed(self, key, sample):
        if key != self.key or self.phase not in ACTIVE_PHASES:
            return False
        if not self._valid(sample, self.clock()):
            self.connected = False
            self._end('error', 'invalid_sample')
            return False
        if (sample.sequence <= self.last_sequence or self.last_sample_at is not None
                and sample.timestamp <= self.last_sample_at):
            return False
        # Do not let the first report after a long gap conceal a lost session.
        if self.last_sample_at is not None and not self._fresh():
            self.disconnect(key)
            return False
        self.last_sequence, self.last_sample_at = sample.sequence, sample.timestamp
        self.left, self.right = sample.left, sample.right
        if self.phase in ('measuring', 'ready_to_finish'):
            self.active, self.done = sample.active, sample.done
            if sample.active:
                self.seen_active = True
            elif self.seen_active:
                self._end('error', 'inactive')
                return False
            for index, (x, y) in enumerate((sample.left, sample.right)):
                if math.hypot(x, y) >= 0.8:
                    sector = int((math.atan2(y, x) % math.tau) / math.tau * SECTORS) % SECTORS
                    self.visited[index].add(sector)
            self.phase = ('ready_to_finish' if (sample.active & sample.done) == 3
                          else 'measuring')
        return True

    def finish(self):
        if self.phase != 'ready_to_finish':
            return False
        if not self._fresh():
            self.disconnect(self.key)
            return False
        self._end('completed')  # Consume exactly once, before a possible error.
        return self._submit('Finish')

    def cancel(self):
        if self.phase not in ACTIVE_PHASES:
            return False
        exit_allowed = self.started and self._fresh()
        if self.started and not exit_allowed:
            self.disconnect(self.key)
            return True
        self._end('cancelled')
        if exit_allowed:
            self._submit('Exit')
        return True

    def disconnect(self, key):
        if key != self.key or self.phase not in ACTIVE_PHASES:
            return False
        self.connected = False
        self._end('lost', 'connection')
        self.left = self.right = (0.0, 0.0)
        return True

    def snapshot(self):
        return dict(phase=self.phase, reason=self.reason, connected=self.connected,
                    countdown=max(0, math.ceil(self.deadline-self.clock())) if self.deadline is not None else 0,
                    canStart=self.phase == 'ready' and self._fresh(),
                    canFinish=self.phase == 'ready_to_finish' and self._fresh(),
                    running=self.phase in ACTIVE_PHASES,
                    sticks=[dict(x=p[0], y=p[1], sectors=[i in self.visited[n] for i in range(SECTORS)],
                                 coverage=round(len(self.visited[n])*100/SECTORS),
                                 ready=bool(self.active & self.done & (1 << n)))
                            for n,p in enumerate((self.left, self.right))])
