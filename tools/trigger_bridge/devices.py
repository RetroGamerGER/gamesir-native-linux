# SPDX-License-Identifier: GPL-2.0-only
"""Metadata-only evdev -> native USB -> broker-instance association.

No event/USB device is opened. Every metadata root and node-stat operation is
injectable for device-free tests. A physical port is temporary session evidence,
never a configured global device identity or a substitute for broker identity.
"""
from dataclasses import asdict, dataclass, fields
import json
import os
from pathlib import Path
import re
import stat

from .protocol import EVENT_PATH, VERSION

IDENTITY = re.compile(r"[0-9a-f]{64}\Z")
PORT = re.compile(r"[1-9][0-9]*-[1-9][0-9]*(?:\.[1-9][0-9]*)*\Z")


class IdentityError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    instance: str
    source_path: str
    sysfs_input: str
    sysfs_usb: str
    sysfs_interface: str
    port: str
    bus: int
    address: int
    vendor: int
    product: int
    input_inode: int
    input_device: int
    node_inode: int
    node_device: int
    node_rdev: int
    usb_inode: int
    usb_device: int

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        names = {field.name for field in fields(cls)}
        if type(value) is not dict or set(value) != names:
            raise IdentityError("Unexpected target manifest fields")
        target = cls(**value)
        strings = ("instance", "source_path", "sysfs_input", "sysfs_usb", "sysfs_interface", "port")
        if any(type(value[name]) is not str for name in strings):
            raise IdentityError("Invalid target text")
        if any(type(value[name]) is not int or value[name] < 0 for name in names - set(strings)):
            raise IdentityError("Invalid target numeric metadata")
        if (not IDENTITY.fullmatch(target.instance) or not EVENT_PATH.fullmatch(target.source_path) or
                not PORT.fullmatch(target.port) or not 1 <= target.bus <= 255 or
                not 1 <= target.address <= 127 or target.vendor != 0x3537 or target.product != 0x109c):
            raise IdentityError("Unsupported or malformed target")
        return target


def _text(path, maximum=128):
    # Sysfs scalar files only; no /dev reads. Bound every text field.
    with path.open("r", encoding="ascii") as source:
        value = source.read(maximum + 1)
    if len(value) > maximum:
        raise IdentityError("Oversized sysfs scalar")
    return value.strip()


def _inside(path, root):
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise IdentityError("Sysfs link escaped metadata root")
    return resolved


def _snapshot(event, instance, sysfs_root, dev_root, node_stat):
    root = sysfs_root.resolve(strict=True)
    entry = root / "class/input" / event
    input_path = _inside(entry / "device", root)
    if _text(input_path / "name") != "GameSir G7 Pro":
        raise IdentityError("Not the native GameSir gamepad input")
    interface, usb = None, None
    for ancestor in (input_path, *input_path.parents):
        if not ancestor.is_relative_to(root):
            break
        if interface is None and (ancestor / "driver").is_symlink():
            driver = _inside(ancestor / "driver", root)
            if driver.name != "gs_native":
                raise IdentityError("Input interface is not owned by gs_native")
            interface = ancestor
        if (ancestor / "idVendor").is_file() and (ancestor / "idProduct").is_file():
            usb = ancestor
            break
    if usb is None or interface is None or interface.name != usb.name + ":1.0":
        raise IdentityError("Missing exact native USB interface 0 parent")
    vendor, product = int(_text(usb / "idVendor"), 16), int(_text(usb / "idProduct"), 16)
    bus, address = int(_text(usb / "busnum")), int(_text(usb / "devnum"))
    if (_text(input_path / "id/vendor").lower() != f"{vendor:04x}" or
            _text(input_path / "id/product").lower() != f"{product:04x}"):
        raise IdentityError("Input and USB identities disagree")
    node = node_stat(dev_root / "input" / event)
    major, minor = (int(part) for part in _text(entry / "dev").split(":"))
    if (not stat.S_ISCHR(node.st_mode) or major != 13 or
            node.st_rdev != os.makedev(major, minor)):
        raise IdentityError("Event node does not match sysfs device number")
    input_stat, usb_stat = input_path.stat(), usb.stat()
    return Target.from_dict(dict(instance=instance, source_path=f"/dev/input/{event}",
        sysfs_input=str(input_path), sysfs_usb=str(usb), sysfs_interface=str(interface), port=usb.name,
        bus=bus, address=address, vendor=vendor, product=product,
        input_inode=input_stat.st_ino, input_device=input_stat.st_dev,
        node_inode=node.st_ino, node_device=node.st_dev, node_rdev=node.st_rdev,
        usb_inode=usb_stat.st_ino, usb_device=usb_stat.st_dev))


def discover(devices, sysfs_root=Path("/sys"), dev_root=Path("/dev"), node_stat=os.stat):
    """Return all verified candidates; callers must reject zero/multiple results.

    Incomplete/unrelated events are ignored, but duplicate broker identities or
    duplicate ports are errors. No ordering preference is an authorization.
    """
    if type(devices) is not list:
        raise IdentityError("Broker list must be an array")
    identities, ports = set(), set()
    for device in devices:
        if (type(device) is not dict or type(device.get("instance")) is not str or
                not IDENTITY.fullmatch(device["instance"]) or
                type(device.get("port")) is not str or not PORT.fullmatch(device["port"]) or
                type(device.get("busy")) is not bool):
            raise IdentityError("Malformed broker device")
        if device["instance"] in identities or device["port"] in ports:
            raise IdentityError("Ambiguous broker instance or port")
        identities.add(device["instance"])
        ports.add(device["port"])
    by_port = {device["port"]: device for device in devices if not device["busy"]}
    candidates = []
    for entry in sorted((Path(sysfs_root) / "class/input").glob("event*")):
        if not EVENT_PATH.fullmatch(f"/dev/input/{entry.name}"):
            continue
        # Probe only metadata. Unsupported PIDs and missing scalar files fail shut.
        try:
            probe = _snapshot(entry.name, "0" * 64, Path(sysfs_root), Path(dev_root), node_stat)
            device = by_port.get(probe.port)
            if device:
                candidates.append(Target.from_dict({**probe.to_dict(), "instance": device["instance"]}))
        except (OSError, ValueError, IdentityError):
            continue
    return candidates


def verify(target, devices, sysfs_root=Path("/sys"), dev_root=Path("/dev"), node_stat=os.stat):
    try:
        matches = [candidate for candidate in discover(devices, sysfs_root, dev_root, node_stat)
                   if candidate.source_path == target.source_path]
        if matches != [target]:
            raise IdentityError("Target changed, disappeared, became busy or is ambiguous; restart explicitly")
    except (OSError, ValueError) as error:
        raise IdentityError("Target metadata is unavailable; no automatic replacement") from error


def read_manifest(path, uid=None):
    path = Path(path)
    metadata = path.lstat()
    expected_uid = os.geteuid() if uid is None else uid
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != expected_uid or
            stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size > 8192):
        raise IdentityError("Manifest must be a private user-owned regular file, mode 0600")
    with path.open("r", encoding="ascii") as source:
        document = json.load(source)
    if (type(document) is not dict or set(document) != {"version", "uid", "session", "target"} or
            type(document["version"]) is not int or document["version"] != VERSION or
            type(document["uid"]) is not int or document["uid"] != expected_uid or
            type(document["session"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", document["session"]) or
            document["session"] == "0" * 32):
        raise IdentityError("Invalid launch session manifest")
    return Target.from_dict(document["target"]), bytes.fromhex(document["session"])
