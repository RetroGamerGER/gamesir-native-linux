# SPDX-License-Identifier: GPL-2.0-only
"""Root helper -> fixed root manager. No device opens or raw USB fallback."""
import os
import socket
import stat
import struct
import time

from calibration_controller import (Target, Lease, Report, CONTINUITY_CAPABILITIES)
from calibration_protocol import calibration_message, decode_telemetry
from stick_calibration import Instance
from tmr_wire import TmrFailure, target, uint, encode, decode, LIMIT

SOCKET = '/run/gamesir-native/control.sock'


class ManagerSocket:
    def __call__(self, value):
        # Fixed root-private endpoint and authenticated root peer. A substituted
        # user socket cannot impersonate the manager, even on a permissive host.
        info = os.lstat('/run/gamesir-native')
        leaf = os.lstat(SOCKET)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_mode & 0o077
                or not stat.S_ISSOCK(leaf.st_mode) or leaf.st_uid or leaf.st_mode & 0o077):
            raise TmrFailure('unsafe_manager_socket')
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(0.8)
            connection.connect(SOCKET)
            _, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if uid != 0:
                raise TmrFailure('manager_peer')
            connection.sendall(encode(value))
            data = bytearray(); deadline = time.monotonic() + 0.8
            while b'\n' not in data:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TmrFailure('manager_timeout')
                connection.settimeout(remaining)
                part = connection.recv(LIMIT + 1 - len(data))
                if not part or len(data) + len(part) > LIMIT:
                    raise TmrFailure('manager_reply')
                data.extend(part)
        reply = decode(bytes(data))
        if reply.pop('ok', None) is not True:
            raise TmrFailure('manager_rejected')
        return reply


class NativeChannel:
    def __init__(self, call, selection, *, clock=time.monotonic):
        self.call, self.selection, self.clock = call, target(selection), clock
        self.status = self.key = self.lease = None
        self.generation = None
        self.last_number = 0
        self.last_time = 0
        self.returned = False

    def _request(self, action, **fields):
        return self.call({'version': 1, 'tmr': action, 'port': self.selection['port'], **fields})

    def _status(self, reply, *, leased):
        value = reply.get('status')
        keys = {'flags', 'pid', 'phase', 'error', 'port_token', 'instance_token', 'stream_epoch',
                'generation', 'report_number', 'host_monotonic_ns', 'lease_deadline_ns', 'report'}
        if (type(value) is not dict or value.keys() != keys
                or any(type(value[k]) is not int for k in keys - {'report'})
                or value['pid'] != self.selection['pid'] or value['error'] != 0
                or any(value[k] != self.selection[k] for k in ('port_token', 'instance_token'))
                or not uint(value['stream_epoch']) or not uint(value['report_number'])
                or not uint(value['host_monotonic_ns']) or value['flags'] != (7 if leased else 3)
                or not (1 <= value['phase'] <= 4 if leased else value['phase'] == 0)
                or not 0 <= self.clock()*1e9-value['host_monotonic_ns'] <= 1_500_000_000
                or (self.status is not None and value['stream_epoch'] != self.status['stream_epoch'])
                or (leased and (not uint(value['generation'])
                    or not uint(value['lease_deadline_ns'])
                    or value['lease_deadline_ns'] <= self.clock()*1e9
                    or self.generation is not None and value['generation'] != self.generation))
                or type(value['report']) is not str or len(value['report']) != 128):
            raise TmrFailure('native_identity_or_stream')
        try:
            decode_telemetry(bytes.fromhex(value['report']))
        except ValueError as error:
            raise TmrFailure('invalid_e0') from error
        if (value['report_number'] < self.last_number or value['host_monotonic_ns'] < self.last_time
                or self.last_number and ((value['report_number'] == self.last_number)
                                        != (value['host_monotonic_ns'] == self.last_time))):
            raise TmrFailure('native_sequence')
        self.status = dict(value)
        self.last_number, self.last_time = value['report_number'], value['host_monotonic_ns']
        if leased:
            self.generation = value['generation']
        return value

    def probe_target(self):
        reply = self._request('probe', **{k:self.selection[k] for k in ('port_token','instance_token')})
        if reply.get('link_basis') != 'fresh_e0_continuity_only':
            raise TmrFailure('unsupported_link_basis')
        status = self._status(reply, leased=False)
        if status['phase'] != 0:
            raise TmrFailure('maintenance_not_idle')
        return Target(Instance(self.selection['port'], 'e0-epoch-' + str(status['stream_epoch'])),
                      0x3537, status['pid'], status['port_token'], status['instance_token'])

    def acquire(self, selected, key):
        if self.status is None or self.key is not None:
            raise TmrFailure('acquisition_sequence')
        self.key, self.selected = key, selected
        reply = self._request('acquire', **{k:self.status[k] for k in
                              ('port_token','instance_token','stream_epoch')})
        if (reply.get('link_basis') != 'fresh_e0_continuity_only'
                or type(reply.get('lease')) is not str or len(reply['lease']) != 48
                or any(c not in '0123456789abcdef' for c in reply['lease'])):
            raise TmrFailure('invalid_lease')
        # Retain only this token even if later validation fails; cleanup may
        # release it locally, never send a compensating device command.
        self.token = reply['lease']
        status = self._status(reply, leased=True)
        if status['phase'] != 1:
            raise TmrFailure('acquisition_phase')
        self.lease = self._lease()
        return self.lease

    def _lease(self):
        return Lease(self.key, self.selected, self.token, self.status['lease_deadline_ns']/1e9,
                     False, True, 'gs_native', CONTINUITY_CAPABILITIES, 'fresh_e0_continuity_only')

    def inspect(self, lease):
        if self.returned or lease.key != self.key or lease.token != self.token or lease.target != self.selected:
            raise TmrFailure('foreign_lease')
        self._status(self._request('poll', lease=self.token), leased=True)
        return self._lease()

    def send_message(self, lease, message):
        actions = [name for name in ('Start','Finish','Exit') if calibration_message(name) == message]
        if len(actions) != 1 or lease.key != self.key or lease.token != self.token or self.returned:
            raise TmrFailure('unsupported_command')
        self._status(self._request(actions[0], lease=self.token), leased=True)
        if self.status['phase'] != {'Start':2, 'Finish':3, 'Exit':4}[actions[0]]:
            raise TmrFailure('command_phase')
        return True

    def report(self):
        return Report(self.key, self.selected, self.token, self.status['report_number'],
                      self.status['host_monotonic_ns']/1e9, bytes.fromhex(self.status['report']))

    def release(self, lease):
        if lease.key != self.key or lease.token != self.token:
            raise TmrFailure('foreign_release')
        return self.drop()

    def drop(self):
        if self.returned:
            return False
        self.returned = True  # No retries, including an ambiguous reply.
        if not hasattr(self, 'token'):
            return True  # Unknown acquisition expires in the manager.
        reply = self._request('release', lease=self.token)
        return reply.get('error', '') == '' and reply.get('cleanup_error', '') == ''
