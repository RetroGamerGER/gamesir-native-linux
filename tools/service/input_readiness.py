# SPDX-License-Identifier: GPL-2.0-only
"""Processed-udev receipts and seat access for one attested input pair.

No device opens/writes or permission changes. Construct only in the root
daemon, before takeover. Imports alone do not access the running system.
"""
import ctypes as c
import errno
import hashlib
import os
from pathlib import Path
import select
import stat
import subprocess
import sys

from input_pair_readiness import Sensor


class ReadinessError(RuntimeError):
    pass


def fingerprint(path, devroot=Path('/dev')):
    """Pin canonical input and event objects plus the device-node lifetime."""
    path = Path(path).resolve(strict=True)
    if not path.name.startswith('event') or not path.name[5:].isdigit():
        raise ReadinessError('Not an input event object')
    parent = path.parent
    before = parent.stat()
    event = path.stat()
    major, minor = map(int, (path / 'dev').read_text().strip().split(':'))
    node = devroot / 'input' / path.name
    metadata = node.lstat()
    if not stat.S_ISCHR(metadata.st_mode) or metadata.st_rdev != os.makedev(major, minor):
        raise ReadinessError('Input node is not the expected character device')
    uniq = (parent / 'uniq').read_text().strip()
    if not uniq.startswith('gsn-'):
        raise ReadinessError('Missing native session identity')
    values = (str(path), before.st_dev, before.st_ino, event.st_dev, event.st_ino,
              metadata.st_dev, metadata.st_ino, metadata.st_rdev, uniq)
    if parent.stat() != before or path.stat() != event or node.lstat() != metadata:
        raise ReadinessError('Input metadata changed while checking')
    token = hashlib.sha256(repr(values).encode()).hexdigest()
    return token, uniq, node


def active_uid(seat):
    lib = c.CDLL('libsystemd.so.0')
    function = lib.sd_seat_get_active
    function.argtypes = [c.c_char_p, c.c_void_p, c.POINTER(c.c_uint)]
    function.restype = c.c_int
    uid = c.c_uint()
    result = function(seat.encode(), None, c.byref(uid))
    if result in (-errno.ENODATA, -errno.ENOENT):
        return None  # No active seat client; later login discovers both nodes.
    if result < 0:
        raise ReadinessError('Cannot establish active seat identity')
    return uid.value


def user_can_read(node, uid):
    if type(uid) is not int or not 0 <= uid < 2**32:
        raise ReadinessError('Invalid active seat UID')
    # Bound account/group lookup as well as access(2). Credentials are dropped
    # only inside this short-lived child, before checking the device node.
    script = """import os,pwd,sys
try:
 uid=int(sys.argv[2]);account=pwd.getpwuid(uid)
 os.initgroups(account.pw_name,account.pw_gid)
 os.setresgid(account.pw_gid,account.pw_gid,account.pw_gid)
 os.setresuid(uid,uid,uid)
 readable=os.access(sys.argv[1],os.R_OK)
except Exception:
 sys.exit(2)
sys.exit(0 if readable else 1)
"""
    result = subprocess.run([sys.executable, '-I', '-c', script, str(node), str(uid)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        close_fds=True, timeout=1)
    if result.returncode not in (0, 1):
        raise ReadinessError('Session access checker failed')
    return result.returncode == 0


class ProcessedInputs:
    """Listen to trusted *udev* events, not raw kernel creation/database state.

Receipts are deliberately not persisted. After a daemon restart an unpublished
pair without a fresh receipt times out and keeps its existing cleanup lease.
An already published pair needs no new publication or fabricated udev event.
"""
    def __init__(self, devroot=Path('/dev'), access=user_can_read, uid=active_uid):
        self.devroot, self.access, self.uid = devroot, access, uid
        self.receipts = {}
        self.lib = c.CDLL('libudev.so.1', use_errno=True)
        signatures = {
            'udev_new': ([], c.c_void_p),
            'udev_monitor_new_from_netlink': ([c.c_void_p, c.c_char_p], c.c_void_p),
            'udev_monitor_filter_add_match_subsystem_devtype': ([c.c_void_p, c.c_char_p, c.c_char_p], c.c_int),
            'udev_monitor_enable_receiving': ([c.c_void_p], c.c_int),
            'udev_monitor_get_fd': ([c.c_void_p], c.c_int),
            'udev_monitor_receive_device': ([c.c_void_p], c.c_void_p),
            'udev_device_get_syspath': ([c.c_void_p], c.c_char_p),
            'udev_device_get_action': ([c.c_void_p], c.c_char_p),
            'udev_device_get_property_value': ([c.c_void_p, c.c_char_p], c.c_char_p),
            'udev_device_get_seqnum': ([c.c_void_p], c.c_ulonglong),
            'udev_device_unref': ([c.c_void_p], c.c_void_p),
            'udev_monitor_unref': ([c.c_void_p], c.c_void_p),
            'udev_unref': ([c.c_void_p], c.c_void_p),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.lib, name)
            function.argtypes, function.restype = args, result
        self.context = self.lib.udev_new()
        self.monitor = None
        try:
            self.monitor = self.lib.udev_monitor_new_from_netlink(self.context, b'udev') if self.context else None
            if (not self.monitor or
                    self.lib.udev_monitor_filter_add_match_subsystem_devtype(self.monitor, b'input', None) < 0 or
                    self.lib.udev_monitor_enable_receiving(self.monitor) < 0):
                raise ReadinessError('Processed input monitor unavailable; no takeover')
            self.fd = self.lib.udev_monitor_get_fd(self.monitor)
            if self.fd < 0:
                raise ReadinessError('Processed input monitor has no descriptor')
            os.set_blocking(self.fd, False)
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.monitor:
            self.lib.udev_monitor_unref(self.monitor)
            self.monitor = None
        if self.context:
            self.lib.udev_unref(self.context)
            self.context = None

    def record(self, path, action, accelerometer, sequence, seat='seat0'):
        path = str(path)
        if action == 'remove':
            self.receipts.pop(path, None)
        elif action in ('add', 'change') and accelerometer and sequence > 0:
            try:
                token, _, _ = fingerprint(path, self.devroot)
            except (OSError, ValueError, ReadinessError):
                return  # Not complete; no guessed creation/readiness receipt.
            if len(self.receipts) >= 256 and path not in self.receipts:
                raise ReadinessError('Input receipt capacity exceeded')
            self.receipts[path] = (token, seat)

    def drain(self):
        for _ in range(256):
            if not select.select([self.fd], [], [], 0)[0]:
                return
            device = self.lib.udev_monitor_receive_device(self.monitor)
            if not device:
                if c.get_errno() == errno.EAGAIN:
                    return
                raise ReadinessError('Processed input event lost or unreadable')
            try:
                path = self.lib.udev_device_get_syspath(device)
                action = self.lib.udev_device_get_action(device)
                prop = self.lib.udev_device_get_property_value
                if path and action:
                    seat = prop(device, b'ID_SEAT') or b'seat0'
                    self.record(path.decode(), action.decode(), prop(device, b'ID_INPUT_ACCELEROMETER') == b'1',
                                self.lib.udev_device_get_seqnum(device), seat.decode())
            finally:
                self.lib.udev_device_unref(device)
        raise ReadinessError('Processed input monitor flood; no publication')

    def sensor(self, binding, name, gyro, accel):
        parent = Path(binding.interface_path) / 'input' / name
        if not parent.is_dir():
            return None
        if parent.resolve().parent.parent != Path(binding.interface_path):
            raise ReadinessError('Motion parent differs from exact native interface')
        events = list(parent.glob('event[0-9]*'))
        if len(events) != 1:
            return None
        token, uniq, node = fingerprint(events[0], self.devroot)
        if uniq != binding.uniq:
            raise ReadinessError('Motion session identity differs')
        receipt = self.receipts.get(str(events[0].resolve()))
        processed = receipt and receipt[0] == token
        readable = False
        if processed:
            uid = self.uid(receipt[1])
            readable = uid is None or self.access(node, uid)
            if fingerprint(events[0], self.devroot)[0] != token:
                raise ReadinessError('Motion instance changed during access check')
        return Sensor(binding, token, token if processed else '', readable,
                      (gyro,) * 3, (accel,) * 3)
