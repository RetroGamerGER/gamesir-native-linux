# SPDX-License-Identifier: GPL-2.0-only
"""Unprivileged fixed-helper pipe client. Explicit construction does no I/O."""
import os
from pathlib import Path
import selectors
import subprocess
import time

from privilege.transport import InstalledAuditor
from tmr_wire import ARGV, FILES, HELPER, LIMIT, TmrFailure, encode, decode, request


def load_pins(path):
    with Path(path).open('rb') as source:
        value = decode(source.read(LIMIT + 1))
    if (value.keys() != {'schema','files'} or type(value['schema']) is not int or value['schema'] != 1
            or type(value['files']) is not dict or set(value['files']) != set(FILES)
            or any(type(v) is not str or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                   for v in value['files'].values())):
        raise TmrFailure('unreviewed_helper')
    return value['files']


class HelperClient:
    def __init__(self, pins, *, auditor=None, spawn=subprocess.Popen, cancelled=lambda:False):
        # Validate without opening the manager, paths, devices or a process.
        if (type(pins) is not dict or set(pins) != set(FILES)
                or any(type(v) is not str or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                       for v in pins.values())):
            raise TmrFailure('unreviewed_helper')
        self.pins, self.auditor, self.spawn = dict(pins), auditor or InstalledAuditor(), spawn
        self.cancelled = cancelled
        self.child = None
        self.number = 0
        self.closed = False
        self.buffer = bytearray()

    def start(self):
        if self.closed or self.child is not None or self.cancelled():
            raise TmrFailure('client_closed')
        self.auditor.inspect(ARGV[0], executable=True)
        for path, digest in self.pins.items():
            self.auditor.inspect(path, digest, executable=path == HELPER)
        self.child = self.spawn(ARGV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                 stderr=subprocess.DEVNULL, shell=False, close_fds=True, start_new_session=True,
                 bufsize=0, env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'})

    def call(self, action, **fields):
        if self.closed:
            raise TmrFailure('client_closed')
        self.number += 1
        value = {'schema':1,'id':self.number,'action':action,**fields}
        wire = encode(value); request(wire)  # Reject before spawning/writing.
        if self.child is None:
            if action != 'list':
                raise TmrFailure('listing_required')
            self.start()
        try:
            self.child.stdin.write(wire)
            self.child.stdin.flush()
            deadline = time.monotonic() + (120 if action == 'list' else 2)
            with selectors.DefaultSelector() as selector:
                selector.register(self.child.stdout, selectors.EVENT_READ)
                while b'\n' not in self.buffer:
                    if self.cancelled():
                        raise TmrFailure('cancelled')
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TmrFailure('authorization_or_reply_timeout')
                    if not selector.select(min(0.05,remaining)):
                        continue
                    part = os.read(self.child.stdout.fileno(), LIMIT+1-len(self.buffer))
                    if not part or len(self.buffer)+len(part) > LIMIT:
                        raise TmrFailure('helper_stopped')
                    self.buffer.extend(part)
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            reply = decode(bytes(line)+b'\n')
            if (reply.get('ok') is not True or type(reply.get('schema')) is not int
                    or reply['schema'] != 1 or type(reply.get('id')) is not int
                    or reply['id'] != self.number):
                raise TmrFailure('reply_mismatch')
            return reply
        except Exception as error:
            self.close()  # EOF lets the privileged helper return its lease.
            if isinstance(error, TmrFailure):
                raise
            raise TmrFailure('permission_transport_failed') from None

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.child:
            for stream in (self.child.stdin, self.child.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
            try:
                self.child.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                # Root may not be signalable; closed stdin + watchdog end it.
                # Do not kill a reused PID or claim its completion is confirmed.
                pass
