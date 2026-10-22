# SPDX-License-Identifier: GPL-2.0-only
"""Narrow native ABI adapter. Importing performs no I/O; no USB fallback.

Only explicitly constructed by the root manager for a guarded owned device.
All dependencies are injectable for offline tests. No node enumeration here.
"""
import fcntl
import os
import stat
import struct

REQUEST = struct.Struct('=IIQQQQII')
STATUS = struct.Struct('=IIIIiIQQQQQQQ64s')
GET = (2 << 30) | (STATUS.size << 16) | (ord('G') << 8) | 0x7b
COMMAND = (1 << 30) | (REQUEST.size << 16) | (ord('G') << 8) | 0x7c
OPERATIONS = {'acquire': 1, 'Start': 2, 'Finish': 3, 'Exit': 4, 'release': 5, 'renew': 6}


def decode_status(data):
    fields = STATUS.unpack(data)
    keys = ('abi', 'flags', 'pid', 'phase', 'error', 'reserved', 'port_token',
            'instance_token', 'stream_epoch', 'generation', 'report_number',
            'host_monotonic_ns', 'lease_deadline_ns', 'report')
    value = dict(zip(keys, fields))
    if (value.pop('abi') != 1 or value.pop('reserved') or value['flags'] & ~7
            or value['phase'] > 5 or value['pid'] not in (0x109c, 0x105e)
            or not value['port_token'] or not value['instance_token']):
        raise ValueError('Invalid native TMR status')
    # The frame remains byte-for-byte separate from its metadata.
    value['report'] = value['report'].hex()
    return value


class NativeTmr:
    def __init__(self, node, *, open_fd=os.open, fstat=os.fstat,
                 ioctl=fcntl.ioctl, close_fd=os.close):
        self.ioctl, self.close_fd = ioctl, close_fd
        self.fd = open_fd(node, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            if not stat.S_ISCHR(fstat(self.fd).st_mode):
                raise ValueError('Expected native character device')
            # First ioctl switches this FD into maintenance mode; its close
            # never ends the normal input session, including disabled API.
            self.get()
        except Exception:
            self.close()
            raise

    def get(self):
        data = bytearray(STATUS.size)
        self.ioctl(self.fd, GET, data, True)
        return decode_status(data)

    def command(self, operation, target, generation):
        data = REQUEST.pack(1, OPERATIONS[operation], target['port_token'],
                            target['instance_token'], target['stream_epoch'], generation, 0, 0)
        self.ioctl(self.fd, COMMAND, data)

    def close(self):
        if self.fd is not None:
            fd, self.fd = self.fd, None
            self.close_fd(fd)  # Never retry an ambiguous close against a reused FD.
