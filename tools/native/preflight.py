#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read cached sysfs identity/bindings only. No device open, commands or writes."""
import argparse
import json
from pathlib import Path
import platform
import re
import sys


def text(path):
    return path.read_text().strip()


def snapshot(port, sysfs_root=Path("/sys/bus/usb/devices"), modules_path=Path("/proc/modules")):
    """Cached metadata only; injectable roots allow device-free guard tests."""
    if not re.fullmatch(r"[0-9]+-[0-9]+(?:\.[0-9]+)*", port):
        raise ValueError("Expected a physical USB port name")
    root = sysfs_root / port
    if not root.is_dir():
        raise SystemExit("Selected port absent; stop")
    result = {"method": "cached sysfs attributes; no USB node opened", "port": port,
              "kernel_release": platform.release(),
              "identity": {key: text(root / key) for key in ["idVendor", "idProduct", "busnum", "devnum", "devpath", "bConfigurationValue"]},
              "interfaces": {}}
    for interface in sorted(root.glob(port + ":*")):
        desc = {key: text(interface / key) for key in ["bInterfaceNumber", "bAlternateSetting", "bInterfaceClass", "bInterfaceSubClass", "bInterfaceProtocol"]}
        desc["driver"] = (interface / "driver").resolve().name if (interface / "driver").is_symlink() else None
        desc["endpoints"] = {p.name: {key: text(p / key) for key in ["bEndpointAddress", "bmAttributes", "wMaxPacketSize", "bInterval"]}
                             for p in sorted(interface.glob("ep_*"))}
        result["interfaces"][interface.name] = desc
    modules = {line.split()[0] for line in modules_path.read_text().splitlines()}
    result["industrialio_already_loaded"] = "industrialio" in modules
    result["gs_native_loaded"] = "gs_native" in modules
    normal = {r["bInterfaceNumber"]: r["driver"] for r in result["interfaces"].values()}
    result["normal_baseline_matches"] = (result["identity"]["idVendor"] == "3537" and
        result["identity"]["idProduct"] == "100a" and normal == {"00": "xpad", "01": "usbhid"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Explicit physical USB port, e.g. 8-6")
    args = parser.parse_args()
    try:
        result = snapshot(args.port)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0 if result["normal_baseline_matches"] else 2


if __name__ == "__main__":
    sys.exit(main())
