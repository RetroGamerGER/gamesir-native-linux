#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Explicitly authorized, bounded host-IIO setup and restoration.

Importing this module does nothing. No USB, private controller node, ioctl,
service, module, permission or firmware operations are implemented here.
The caller must obtain approval and local readiness before calling setup().
"""
import copy
import os
from pathlib import Path
import re
import stat
import sys

from gamesir_imu_stream import CHANNELS, IIO_NAME, SCAN_SIZE


# Reviewed offline build with incremental IIO scan selection fixed. Older
# modules fail metadata preflight; do not retry the known EINVAL on hardware.
MODULE_SRCVERSION = "A15BC39B5A21D181E4E5C49"


def _identity(info):
    return [info.st_dev, info.st_ino]


def _close_preserving_primary(fd):
    primary = sys.exc_info()[1]
    try:
        os.close(fd)
    except BaseException as close_error:
        if primary is None:
            raise
        primary.add_note(f"descriptor close also failed: {close_error}")


def _read(path):
    with open(path, "r", encoding="ascii") as handle:
        value = handle.read(1025)
    if len(value) > 1024:
        raise ValueError(f"oversized metadata: {path}")
    return value.strip()


def _nonnegative(value, label):
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError(f"invalid nonnegative {label}")
    return int(value)


def _snapshot(directory, node):
    directory = Path(directory).resolve(strict=True)
    node = Path(node)
    if not str(directory).startswith("/sys/devices/") or not re.fullmatch(r"iio:device[0-9]+", directory.name):
        raise ValueError("canonical /sys/devices/.../iio:deviceN required")
    if node != Path("/dev") / directory.name:
        raise ValueError("matching /dev/iio:deviceN required")
    before = directory.stat()
    if not stat.S_ISDIR(before.st_mode) or _read(directory / "name") != IIO_NAME:
        raise ValueError("unexpected native IIO instance")
    interface = next((p for p in directory.parents if (p / "bInterfaceNumber").is_file()), None)
    if interface is None or _read(interface / "bInterfaceNumber") != "00":
        raise ValueError("native USB interface 0 required")
    usb = interface.parent
    usb_before, interface_before, parent_before = usb.stat(), interface.stat(), usb.parent.stat()
    if _read(usb / "idVendor") != "3537" or _read(usb / "idProduct") != "109c":
        raise ValueError("only 3537:109c is approved")
    driver = (interface / "driver").resolve(strict=True)
    if driver.name != "gs_native":
        raise ValueError("USB interface must remain bound to gs_native")
    version = _read(driver / "module/srcversion")
    if version != MODULE_SRCVERSION:
        raise ValueError("unexpected native module srcversion")
    settings = {"current_timestamp_clock": _read(directory / "current_timestamp_clock"),
                "buffer/length": _read(directory / "buffer/length")}
    if (directory / "buffer/watermark").exists():
        settings["buffer/watermark"] = _read(directory / "buffer/watermark")
    if _nonnegative(settings["buffer/length"], "buffer length") < 2:
        raise ValueError("buffer length must be >=2")
    if "buffer/watermark" in settings and _nonnegative(settings["buffer/watermark"], "watermark") < 1:
        raise ValueError("watermark must be >=1")
    names = {p.name[:-3] for p in (directory / "scan_elements").glob("*_en")}
    if names != set(CHANNELS):
        raise ValueError("exactly eight expected scan channels required")
    types = {}
    for index, name in enumerate(CHANNELS):
        kind = "le:s16/16>>0" if index < 6 else "le:u64/64>>0" if index == 6 else f"{'le' if sys.byteorder == 'little' else 'be'}:s64/64>>0"
        if _read(directory / f"scan_elements/{name}_index") != str(index) or _read(directory / f"scan_elements/{name}_type") != kind:
            raise ValueError(f"unexpected scan layout: {name}")
        value = _read(directory / f"scan_elements/{name}_en")
        if value not in ("0", "1"):
            raise ValueError(f"invalid scan enable: {name}")
        settings[f"scan_elements/{name}_en"] = value
        types[name] = kind
    enable, gate = _read(directory / "buffer/enable"), _read(directory / "buffer_stream_active")
    if enable not in ("0", "1") or gate not in ("0", "1"):
        raise ValueError("invalid buffer/gate state")
    major, minor = map(int, _read(directory / "dev").split(":"))
    node_info = node.lstat()
    if not stat.S_ISCHR(node_info.st_mode) or (os.major(node_info.st_rdev), os.minor(node_info.st_rdev)) != (major, minor):
        raise ValueError("IIO node type or device number mismatch")
    topology = {"directory": str(usb), "identity": _identity(usb_before),
                "parent_identity": _identity(parent_before), "interface_directory": str(interface),
                "interface_identity": _identity(interface_before), "interface_number": 0,
                "vid": "3537", "pid": "109c", "bus": _nonnegative(_read(usb / "busnum"), "USB bus"),
                "address": _nonnegative(_read(usb / "devnum"), "USB address"), "driver": "gs_native"}
    if (_identity(directory.stat()) != _identity(before) or _identity(usb.stat()) != topology["identity"] or
            _identity(interface.stat()) != topology["interface_identity"] or
            _identity(usb.parent.stat()) != topology["parent_identity"] or
            (interface / "driver").resolve(strict=True) != driver or _read(driver / "module/srcversion") != version):
        raise ValueError("instance changed during metadata inspection")
    return {"schema_version": 1, "directory": str(directory), "iio_identity": _identity(before),
            "device_node": str(node), "major": major, "minor": minor, "usb": topology,
            "module_srcversion": version, "settings": settings, "types": types,
            "buffer_enable": enable, "buffer_stream_active": gate,
            "buffer_push_errors": _nonnegative(_read(directory / "buffer_push_errors"), "push errors")}


class MetadataBackend:
    """Production boundary. Tests inject a fake object, never a CLI bypass."""
    snapshot = staticmethod(_snapshot)

    @staticmethod
    def open_directory(directory):
        return os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)

    @staticmethod
    def directory_identity(fd):
        return _identity(os.fstat(fd))

    @staticmethod
    def open_node(node, major, minor):
        fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if not stat.S_ISCHR(info.st_mode) or (os.major(info.st_rdev), os.minor(info.st_rdev)) != (major, minor):
                raise ValueError("opened IIO device changed")
            return fd
        except BaseException:
            _close_preserving_primary(fd)
            raise

    @staticmethod
    def write_at(directory_fd, relative, value):
        parts = Path(relative).parts
        if len(parts) not in (1, 2) or any(part in ("", ".", "..") for part in parts) or Path(relative).is_absolute():
            raise ValueError("bounded relative sysfs attribute required")
        parent_fd, owns_parent = directory_fd, False
        try:
            if len(parts) == 2:
                parent_fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory_fd)
                owns_parent = True
            fd = os.open(parts[-1], os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent_fd)
            try:
                data = (value + "\n").encode("ascii")
                if os.write(fd, data) != len(data):
                    raise OSError("short sysfs write; restoration still required")
            finally:
                _close_preserving_primary(fd)
        finally:
            if owns_parent:
                _close_preserving_primary(parent_fd)

    close = staticmethod(os.close)


def snapshot_iio(directory, node, *, backend=None):
    """Read metadata only, including lstat of the node; never open the node."""
    return (backend or MetadataBackend()).snapshot(directory, node)


class BufferTransaction:
    def __init__(self, expected_snapshot, *, backend=None, after_reserve=None):
        self.before = copy.deepcopy(expected_snapshot)
        if self.before.get("schema_version") != 1:
            raise ValueError("snapshot schema version 1 required")
        self.backend = backend or MetadataBackend()
        self.after_reserve = after_reserve
        self.directory_fd = self.fd = None
        self.attempted, self.writes = [], []
        self.restore_report = None
        self.started = False

    def _current(self):
        current = self.backend.snapshot(self.before["directory"], self.before["device_node"])
        for field in ("schema_version", "directory", "iio_identity", "device_node", "major", "minor", "usb", "module_srcversion", "types"):
            if current[field] != self.before[field]:
                raise ValueError(f"original IIO/USB instance changed: {field}; no replacement writes")
        if self.directory_fd is not None and self.backend.directory_identity(self.directory_fd) != self.before["iio_identity"]:
            raise ValueError("pinned IIO directory identity changed")
        return current

    def _write(self, relative, value):
        self._current()  # Pin plus identity check before EVERY write, including cleanup.
        self.writes.append({"attribute": relative, "value": value, "ok": False})
        self.backend.write_at(self.directory_fd, relative, value)
        self.writes[-1]["ok"] = True

    def setup(self):
        """Caller needs an explicit Go before this method. No data are read."""
        if self.started or self.restore_report is not None:
            raise ValueError("transaction can only be started once")
        self.started = True
        try:
            if self._current() != self.before or self.before["buffer_enable"] != "0" or self.before["buffer_stream_active"] != "0":
                raise ValueError("original metadata/settings changed or buffer was not inactive")
            self.directory_fd = self.backend.open_directory(self.before["directory"])
            self._current()
            # Reserve our one FD BEFORE configuration; EBUSY makes no writes.
            self.fd = self.backend.open_node(self.before["device_node"], self.before["major"], self.before["minor"])
            if self.after_reserve is not None:
                self.after_reserve(self.fd)
            if self._current() != self.before:
                raise ValueError("original metadata changed while claiming reader")
            desired = {"current_timestamp_clock": "monotonic", "buffer/length": "512"}
            if "buffer/watermark" in self.before["settings"]:
                desired["buffer/watermark"] = "1"
            desired.update({f"scan_elements/{name}_en": "1" for name in CHANNELS})
            for relative, value in desired.items():
                current = self._current()
                if current["buffer_enable"] != "0" or current["buffer_stream_active"] != "0":
                    raise ValueError("buffer became active during setup")
                if current["settings"][relative] != self.before["settings"][relative]:
                    raise ValueError(f"attribute changed concurrently: {relative}")
                if value != self.before["settings"][relative]:
                    self.attempted.append(relative)  # Even a failed/short write may have changed state.
                    self._write(relative, value)
            current = self._current()
            if current["settings"] != desired or current["buffer_push_errors"] != self.before["buffer_push_errors"]:
                raise ValueError("configured settings/error count changed")
            if current["buffer_enable"] != "0" or current["buffer_stream_active"] != "0":
                raise ValueError("buffer became active before enable")
            self.attempted.append("buffer/enable")
            self._write("buffer/enable", "1")
            current = self._current()
            if current["buffer_enable"] != "1" or current["buffer_stream_active"] != "1" or current["settings"] != desired or current["buffer_push_errors"] != self.before["buffer_push_errors"]:
                raise ValueError("buffer enable/readiness verification failed")
            metadata = {"directory": current["directory"],
                        "instance_id": f"{current['directory']}:{current['iio_identity'][0]}:{current['iio_identity'][1]}",
                        "major": current["major"], "minor": current["minor"], "scan_bytes": SCAN_SIZE,
                        "types": current["types"], "clock": "monotonic",
                        "buffer_push_errors": current["buffer_push_errors"]}
            return metadata, self.fd
        except BaseException as error:
            report = self.restore()
            if report["errors"]:
                error.add_note("IIO restoration errors: " + "; ".join(report["errors"]))
            raise

    def restore(self):
        """Never replace a primary capture error; no replacement-device repair."""
        if self.restore_report is not None:
            return self.restore_report
        errors, after = [], None
        try:
            if self.directory_fd is not None:
                try:
                    current = self._current()
                    if not self.attempted:
                        # Nothing belongs to this transaction yet. In particular,
                        # never disable somebody else's raced buffer activation.
                        if current != self.before:
                            raise ValueError("metadata changed before our first write; no cleanup writes authorized")
                        after = current
                    else:
                        after = self._restore_configured(current)
                except BaseException as error:
                    errors.append(f"{type(error).__name__}: {error}")
            else:
                try:
                    after = self._current()
                    if after != self.before:
                        raise ValueError("original metadata no longer matches")
                except BaseException as error:
                    errors.append(f"{type(error).__name__}: {error}")
        finally:
            for field in ("fd", "directory_fd"):
                descriptor = getattr(self, field)
                setattr(self, field, None)
                if descriptor is not None:
                    try:
                        self.backend.close(descriptor)
                    except BaseException as error:
                        errors.append(f"close {field}: {type(error).__name__}: {error}")
        self.restore_report = {"restored": not errors, "errors": errors,
                               "writes": copy.deepcopy(self.writes), "before": self.before, "after": after}
        return self.restore_report

    def _restore_configured(self, current):
        """Only reached once this transaction attempted an actual write."""
        if current["buffer_enable"] != "0" or "buffer/enable" in self.attempted:
            self._write("buffer/enable", "0")
        current = self._current()
        if current["buffer_enable"] != "0" or current["buffer_stream_active"] != "0":
            raise ValueError("producer still active; cannot restore scan settings")
        for relative in reversed(self.attempted):
            if relative == "buffer/enable":
                continue
            current = self._current()
            original = self.before["settings"][relative]
            if current["settings"][relative] != original:
                self._write(relative, original)
        after = self._current()
        if after["settings"] != self.before["settings"] or after["buffer_enable"] != "0" or after["buffer_stream_active"] != "0":
            raise ValueError("original inactive buffer settings not verified")
        return after
