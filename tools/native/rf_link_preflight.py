#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Preparation only. `inspect` reads cached host metadata after separate approval.

No recording, USB node open, driver control, service change or module load.
Default output is the offline plan; importing this module inspects no host.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


COMMANDS = (
    ("manager", ("/usr/bin/gamesir-native", "status")),
    ("service", ("/usr/bin/systemctl", "show", "gamesir-native.service",
                 "--property=ActiveState,SubState,UnitFileState,NRestarts,MainPID")),
    ("packages", ("/usr/bin/pacman", "-Q", "gamesir-native-dkms", "gamesir-native-steam")),
    ("service_journal", ("/usr/bin/journalctl", "-b", "-u", "gamesir-native.service",
                         "-n", "80", "--no-pager", "-o", "short-monotonic")),
    ("kernel_journal", ("/usr/bin/journalctl", "-b", "-k", "-n", "100",
                        "--no-pager", "-o", "short-monotonic")),
)


def plan():
    return {"scope": "RF link capture preparation, no capture backend",
            "initial_condition": "User reports controller off, receiver plugged",
            "proposed_capture_seconds": 90,
            "phases": [{"seconds": [0, 30], "cue": "Controller stays OFF"},
                       {"seconds": [30, 60], "cue": "Power ON once; no pad input"},
                       {"seconds": [60, 80], "cue": "Only after confirmed connection: A, sticks, gentle motion"},
                       {"seconds": [80, 90], "cue": "Rest, then stop recorder"}],
            "prerequisites": ["Fresh read-only state, actual bus and port",
                              "Explicit capture approval and local GO",
                              "Reviewed isolated recorder for observed native lifecycle",
                              "Separate approval if usbmon module is absent"],
            "commands_sent": 0, "capture_ready": False}


def cached_receivers(root=Path("/")):
    """No descriptors requested: sysfs cached attributes only, no serial read."""
    found = []
    for path in sorted((root / "sys/bus/usb/devices").iterdir()):
        if ":" in path.name or not (path / "idVendor").exists():
            continue
        if (path / "idVendor").read_text().strip().lower() != "3537":
            continue
        pid = (path / "idProduct").read_text().strip().lower()
        if pid not in ("100a", "109c", "105e"):
            continue
        resolved = path.resolve(strict=True)
        interfaces = {}
        for interface in sorted(path.parent.glob(path.name + ":*")):
            driver = interface / "driver"
            interfaces[interface.name] = driver.resolve(strict=True).name if driver.is_symlink() else None
        found.append({"port": path.name, "pid": pid,
                      **{name: (path / name).read_text().strip()
                         for name in ("busnum", "devnum", "devpath")},
                      "interfaces": interfaces,
                      "instance_inode": resolved.stat().st_ino,
                      "parent_inode": resolved.parent.stat().st_ino})
    return found


def collect(root=Path("/"), *, run=subprocess.run, kernel_release=None):
    """Explicit caller only; injected saved filesystem/commands support tests."""
    report = {"scope": "read-only RF capture preflight", "capture_ready": False,
              "commands_sent": 0, "receivers": cached_receivers(root),
              "boot_id": (root / "proc/sys/kernel/random/boot_id").read_text().strip(),
              "kernel": kernel_release or os.uname().release, "reads": {}, "blockers": []}
    if len(report["receivers"]) != 1:
        report["blockers"].append("Expected exactly one supported receiver; do not select by guess")
        return report
    target = report["receivers"][0]
    if target["pid"] == "105e":
        report["blockers"].append("ZZZ is outside the proposed standard-model run")
        return report
    for name, command in COMMANDS:
        result = run(list(command), stdin=subprocess.DEVNULL, capture_output=True,
                     text=True, timeout=10, check=False,
                     env={"PATH": "/usr/bin", "LANG": "C", "LC_ALL": "C"})
        if len(result.stdout) + len(result.stderr) > 512 * 1024:
            raise ValueError("Read-only command output exceeds report limit: " + name)
        report["reads"][name] = {"returncode": result.returncode,
                                 "stdout": result.stdout, "stderr": result.stderr}
        if result.returncode:
            report["blockers"].append("Read failed: " + name)
            return report  # No retry or alternative privileged operation.
        if name == "manager":
            value = json.loads(result.stdout)
            if (not isinstance(value, dict) or type(value.get("paused")) is not bool or
                    not isinstance(value.get("devices"), dict)):
                raise ValueError("Incomplete manager status schema")
            if (value.get("ok") is False or value.get("scan_error") or value.get("port_errors") or
                    any(e.get("error") or e.get("busy") or e.get("phase") == "blocked"
                        for e in value.get("devices", {}).values())):
                report["blockers"].append("Manager fault/busy/unknown state; preserve original report and stop")
                return report
    monitor = root / "dev" / ("usbmon" + str(int(target["busnum"])))
    try:
        node = monitor.lstat()  # Never open a monitor or USB node.
        if not stat.S_ISCHR(node.st_mode):
            report["blockers"].append("Monitor node is not a character device")
        report["monitor_metadata"] = {"uid": node.st_uid, "gid": node.st_gid,
                                      "mode": oct(stat.S_IMODE(node.st_mode)),
                                      "major": os.major(node.st_rdev), "minor": os.minor(node.st_rdev)}
    except FileNotFoundError:
        report["blockers"].append("usbmon node absent; no automatic module load")
    if cached_receivers(root) != report["receivers"] or (
            (root / "proc/sys/kernel/random/boot_id").read_text().strip() != report["boot_id"]):
        report["blockers"].append("Receiver/boot metadata changed during preflight; no retry")
    report["next_gate"] = "Review baseline and new recorder profile before capture approval"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "inspect"), nargs="?", default="plan")
    args = parser.parse_args(argv)
    if args.mode == "plan":
        value = plan()
    else:
        if os.geteuid() != 0:
            parser.error("inspect requires separately approved root read access")
        try:
            value = collect()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(json.dumps({"read_failed": str(error), "capture_ready": False}))
            return 2
        value["helper_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(value, indent=2))
    return 1 if value.get("blockers") else 0


if __name__ == "__main__":
    raise SystemExit(main())
