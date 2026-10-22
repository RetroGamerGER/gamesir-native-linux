# SPDX-License-Identifier: GPL-2.0-only
"""Narrow authenticated calibration session. All I/O injectable for offline tests."""
import os
import selectors
import sys
import time

from calibration_controller import ControllerCalibration
from calibration_protocol import PositionPolicy
from stick_calibration import ACTIVE_PHASES
from tmr_channel import ManagerSocket, NativeChannel
from tmr_wire import TmrFailure, LIMIT, request, encode, target


class Session:
    def __init__(self, manager, *, clock=time.monotonic):
        self.manager, self.clock = manager, clock
        self.number = 0
        self.targets = None
        self.adapter = self.channel = None
        self.closed = False

    def update(self):
        a = self.adapter
        if a and a.session.phase in ACTIVE_PHASES:
            a.poll()

    def view(self):
        if self.adapter is None:
            return None
        value = self.adapter.view()
        value['canStart'] = value['canStart'] and not value['cleanupProblem']
        return value

    def handle(self, data):
        value = request(data)
        if self.closed or value['id'] != self.number + 1:
            raise TmrFailure('request_order')
        self.number = value['id']  # Consume before dispatch; never replay.
        action = value['action']
        if action == 'list':
            if self.targets is not None:
                raise TmrFailure('already_listed')
            reply = self.manager({'version':1, 'tmr':'list'})
            rows = reply.get('targets')
            if type(rows) is not list or len(rows) > 16:
                raise TmrFailure('invalid_targets')
            self.targets = [target(row) for row in rows]
            if len({r['port'] for r in self.targets}) != len(self.targets):
                raise TmrFailure('duplicate_targets')
            return {'targets':[dict(row) for row in self.targets], 'view':None}
        if action == 'select':
            if self.adapter is not None or self.targets is None or value['target'] not in self.targets:
                raise TmrFailure('target_not_offered')
            self.channel = NativeChannel(self.manager, value['target'], clock=self.clock)
            selected = self.channel.probe_target()
            # Explicit display convention: raw byte Y is treated as downward,
            # while the accepted plot uses positive Y upward (unvalidated live).
            # It does not change calibration math, kernel axes or stored values.
            self.adapter = ControllerCalibration(PositionPolicy('raw',(1,-1,1,-1)),
                         channel=self.channel, clock=self.clock, allow_continuity=True)
            if not self.adapter.open(selected):
                self.close(explicit=False)
                raise TmrFailure('acquisition_failed')
            self.adapter.receive(self.channel.report())
        elif action == 'cancel':
            self.close(explicit=True)
        else:
            if self.adapter is None or self.adapter.session.phase not in ACTIVE_PHASES:
                raise TmrFailure('no_active_run')
            self.update()
            if action == 'prepare':
                self.adapter.prepare()
            elif action == 'finish':
                self.adapter.finish()
        return {'view':self.view()}

    def close(self, *, explicit=False):
        if self.closed:
            return
        self.closed = True
        if self.adapter:
            if explicit:
                self.adapter.close()  # Exit only when started AND genuinely fresh.
            else:
                self.adapter.connection_lost(self.adapter.session.key)
        if self.channel and not self.channel.returned:
            try:
                returned = self.channel.drop()  # Local lease return, never a USB Exit.
            except Exception:
                returned = False
            if not returned and self.adapter and not self.adapter.cleanup_problem:
                self.adapter.cleanup_problem = 'lease_release_unconfirmed'


class PipeInput:
    def __init__(self, fd):
        self.fd, self.buffer = fd, bytearray()

    def read(self, timeout):
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.fd, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TmrFailure('client_timeout')
                part = os.read(self.fd, LIMIT + 1 - len(self.buffer))
                if not part:
                    raise TmrFailure('client_closed')
                self.buffer.extend(part)
                if len(self.buffer) > LIMIT:
                    raise TmrFailure('input_limit')
        line, _, rest = self.buffer.partition(b'\n')
        self.buffer = bytearray(rest)
        return bytes(line) + b'\n'


def serve(reader, writer, session, *, clock=time.monotonic):
    deadline = clock() + 1800
    try:
        while not session.closed:
            if clock() >= deadline:
                raise TmrFailure('session_timeout')
            data = reader(1.5 if session.adapter else 120)
            value = request(data)
            result = session.handle(data)
            writer(encode({'schema':1, 'id':value['id'], 'ok':True, **result}))
    except Exception:
        # No raw manager errors, device paths or request data in root diagnostics.
        # The GUI reports a terminal uncertain result; no compensating retry.
        return 2
    finally:
        session.close(explicit=False)
    return 0


def main():
    uid = os.environ.get('PKEXEC_UID', '')
    if (len(sys.argv) != 1 or os.geteuid() != 0 or not 0 < len(uid) <= 10
            or not uid.isascii() or not uid.isdigit() or not 0 < int(uid) < 0xffffffff):
        return 2
    pipe = PipeInput(sys.stdin.fileno())
    def output(data):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    return serve(pipe.read, output, Session(ManagerSocket()))
