# SPDX-License-Identifier: GPL-2.0-only
"""Root-manager TMR sessions; inert until an explicit narrow request.

No GUI permission grants, haptics access, global pause, persistence or replay.
The manager event loop serializes this policy. Backend is injectable.
"""
from dataclasses import dataclass
import secrets


class TmrError(RuntimeError):
    pass


def integer(value):
    return type(value) is int and 0 < value < 2**64


@dataclass
class Run:
    device: object
    target: dict
    token: str
    generation: int
    backend: object
    deadline: float
    state: str = 'ready'
    error: str = ''
    cleanup_error: str = ''
    acquisition_attempted: bool = False


class Maintenance:
    def __init__(self, manager):
        self.manager = manager
        self.runs = {}
        self.last = {}  # Bounded by the manager's observed/managed ports.

    def busy(self, port):
        return port in self.runs

    def selection(self, port, *, ownership=True):
        m = self.manager
        e = m.entries.get(port)
        if (m.inhibited or m.scan_error or port in m.port_errors or not e
                or e.phase != 'active' or e.error or e.job is not None
                or e.device.driver != 'gs_native' or e.device.pid not in ('109c', '105e')
                or m.observed.get(port) != e.device or len(e.kernel_tokens) != 2):
            raise TmrError('Exact managed active instance is unavailable')
        # Display reads/lease watchdog already hold an exclusive kernel FD.
        # Recheck the live USB instance without enumerating every process FD.
        # Admission and real USB commands keep the complete ownership audit.
        (m.host.guard if ownership else m.host.tmr_guard)(e.device)
        return e

    def validate(self, run, status, *, leased=True):
        now = self.manager.clock()
        if (type(status) is not dict or any(status.get(k) != v for k, v in run.target.items())
                or status.get('pid') != int(run.device.pid, 16)
                or status.get('error') != 0 or status.get('flags', 0) & 3 != 3
                or not integer(status.get('report_number'))
                or not integer(status.get('host_monotonic_ns'))
                or not 0 <= now * 1e9 - status['host_monotonic_ns'] <= 1_500_000_000
                or (leased and (status.get('generation') != run.generation
                                or not status.get('flags', 0) & 4
                                or status.get('lease_deadline_ns', 0) <= now * 1e9))):
            raise TmrError('Native TMR identity, continuity or lease changed')

    def settle(self, port, error=''):
        run = self.runs.get(port)
        if run is None:
            return
        if run.cleanup_error:
            return  # A retained uncertain close is never retried.
        if error and not run.error:
            run.error = error
        try:
            # Local kernel lease return. No Exit, Finish or automatic replay.
            if run.acquisition_attempted:
                run.backend.command('release', run.target, run.generation)
        except Exception as exc:
            run.cleanup_error = str(exc)
        try:
            run.backend.close()
        except Exception as exc:
            run.cleanup_error = run.cleanup_error or str(exc)
            self.last[port] = {'error': run.error, 'cleanup_error': run.cleanup_error}
            return  # Keep this port blocked if closing was not confirmed.
        self.last[port] = {'error': run.error, 'cleanup_error': run.cleanup_error,
                           'state': run.state}
        del self.runs[port]

    def tick(self):
        for port, run in list(self.runs.items()):
            try:
                if run.cleanup_error:
                    continue  # Never retry failed cleanup or claim success.
                if self.manager.clock() >= run.deadline:
                    raise TmrError('Calibration client lease expired')
                entry = self.selection(port, ownership=False)
                if entry.device != run.device:
                    raise TmrError('Calibration device replaced')
                self.validate(run, run.backend.get())
            except Exception as exc:
                self.settle(port, str(exc))
        ports = self.manager.entries.keys() | self.runs.keys()
        self.last = {p: v for p, v in self.last.items() if p in ports}

    def request(self, value):
        if type(value) is not dict or value.get('version') != 1 or type(value.get('version')) is not int:
            raise TmrError('Invalid TMR request version')
        action = value.get('tmr')
        if action == 'list':
            if value.keys() != {'version', 'tmr'}:
                raise TmrError('Invalid TMR listing request')
            targets = []
            for port in sorted(self.manager.entries):
                try:
                    entry = self.selection(port)
                except (TmrError, OSError, ValueError):
                    continue
                if not self.busy(port):
                    targets.append({'port': port, 'pid': int(entry.device.pid, 16),
                                    'port_token': entry.kernel_tokens[0],
                                    'instance_token': entry.kernel_tokens[1]})
            if len(targets) > 16:
                raise TmrError('Too many calibration targets')
            # Selection metadata only: no control FD, acquire or USB command.
            return {'targets': targets}
        port = value.get('port')
        if type(port) is not str or port not in self.manager.entries:
            raise TmrError('Unknown managed port')
        if action in ('probe', 'acquire'):
            fields = {'version', 'tmr', 'port', 'port_token', 'instance_token'}
            if action == 'acquire':
                fields.add('stream_epoch')
            if value.keys() != fields or any(not integer(value[k]) for k in fields - {'version', 'tmr', 'port'}):
                raise TmrError('Invalid scoped TMR selection')
            if self.busy(port):
                raise TmrError('Calibration port is already reserved')
            entry = self.selection(port)
            if [value['port_token'], value['instance_token']] != entry.kernel_tokens:
                raise TmrError('Kernel selection tokens changed')
            backend = self.manager.host.open_tmr(entry.device)
            run = Run(entry.device, {k: value[k] for k in ('port_token', 'instance_token')},
                      secrets.token_hex(24), secrets.randbits(63) + 1, backend,
                      self.manager.clock() + 2)
            # Reserve before any further call: partial acquisition cannot escape cleanup.
            self.runs[port] = run
            try:
                status = backend.get()
                run.target['stream_epoch'] = value.get('stream_epoch', status.get('stream_epoch'))
                if not integer(run.target['stream_epoch']):
                    raise TmrError('No fresh E0 stream')
                self.validate(run, status, leased=False)
                if status['flags'] & 4 or status['phase'] != 0:
                    raise TmrError('Native maintenance is not idle')
                if action == 'probe':
                    self.settle(port)
                    if self.busy(port):
                        raise TmrError('Probe handle close unconfirmed')
                    return {'status': status, 'link_basis': 'fresh_e0_continuity_only'}
                run.acquisition_attempted = True
                backend.command('acquire', run.target, run.generation)
                status = backend.get()
                self.validate(run, status)
                if status['phase'] != 1:
                    raise TmrError('Acquisition phase not confirmed')
                return {'lease': run.token, 'status': status,
                        'link_basis': 'fresh_e0_continuity_only'}
            except Exception as exc:
                self.settle(port, str(exc))
                raise TmrError(str(exc)) from exc
        if action not in ('poll', 'Start', 'Finish', 'Exit', 'release') or value.keys() != {'version', 'tmr', 'port', 'lease'}:
            raise TmrError('Only scoped TMR operations are accepted')
        run = self.runs.get(port)
        if (run is None or type(value['lease']) is not str
                or not secrets.compare_digest(value['lease'], run.token)):
            raise TmrError('Unknown calibration lease')
        if action == 'release':
            self.settle(port)
            if self.busy(port):
                raise TmrError('Calibration handle close unconfirmed')
            if self.last[port]['cleanup_error']:
                raise TmrError('Calibration lease return reported: ' + self.last[port]['cleanup_error'])
            return self.last[port]
        try:
            self.tick()
            if self.runs.get(port) is not run or run.error or run.cleanup_error:
                raise TmrError(run.error or run.cleanup_error or 'Calibration lease ended')
            if action != 'poll':
                self.selection(port)
            status = run.backend.get()
            self.validate(run, status)
            if action == 'poll':
                run.backend.command('renew', run.target, run.generation)
                run.deadline = self.manager.clock() + 2
            else:
                expected = {'Start': ('ready', 1), 'Finish': ('started', 2), 'Exit': ('started', 2)}[action]
                if (run.state, status['phase']) != expected:
                    raise TmrError('Calibration operation is not in sequence')
                if action == 'Finish':
                    data = bytes.fromhex(status['report'])
                    if len(data) != 64 or (data[30] & data[31]) != 3:
                        raise TmrError('Both sticks are not ready')
                run.state = 'consumed'  # Before submission, including uncertain outcomes.
                run.backend.command(action, run.target, run.generation)
                self.selection(port)  # Full post-submit audit; never retry on failure.
                run.state = {'Start': 'started', 'Finish': 'finished', 'Exit': 'exited'}[action]
            status = run.backend.get()
            self.validate(run, status)
            expected_phase = {'Start': 2, 'Finish': 3, 'Exit': 4}.get(action)
            if expected_phase is not None and status['phase'] != expected_phase:
                raise TmrError('Operation completion is not confirmed')
            return {'status': status, 'state': run.state}
        except Exception as exc:
            self.settle(port, str(exc))
            raise TmrError(str(exc)) from exc

    def close(self):
        for port in list(self.runs):
            if not self.runs[port].cleanup_error:
                self.settle(port, 'Manager shutdown')
