#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Check the private recorder's metadata guard using synthetic metadata only."""
import argparse
import ast
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace


def fixture(major=234):
    char = f"/sys/dev/char/{major}:8"
    cls = "/sys/class/usbmon/usbmon8"
    real = "/synthetic/controller/usbmon/usbmon8"
    values = {
        "/proc/devices": f"Character devices:\n{major} usbmon\n235 iio\n\nBlock devices:\n8 sd\n",
        cls + "/dev": f"{major}:8\n",
        char + "/dev": f"{major}:8\n",
        char + "/uevent": f"MAJOR={major}\nMINOR=8\nDEVNAME=usbmon8\n",
    }
    links = {char: real, cls: real,
             char + "/subsystem": "/sys/class/usbmon",
             "/sys/class/usbmon": "/sys/class/usbmon"}
    node = SimpleNamespace(st_uid=0, st_gid=0,
                           st_mode=stat.S_IFCHR | 0o600,
                           st_rdev=os.makedev(major, 8))
    return node, values, links


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    tree = ast.parse(args.source.read_text())
    guard = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "keys" for t in node.targets):
            break  # Remaining source gathers real namespace metadata; never execute it.
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            guard.append(node)
    else:
        raise AssertionError("Guard boundary missing; refuse to execute source")
    code = compile(ast.Module(body=guard, type_ignores=[]), "<metadata guard>", "exec")
    cases = [
        ("current dynamic major", 234, None, True),
        ("different valid dynamic major", 236, None, True),
        ("other registered character driver", 234, "registration", False),
        ("block entry cannot authorize character device", 234, "block_only", False),
        ("duplicate registration", 234, "duplicate", False),
        ("wrong bus minor", 234, "minor", False),
        ("symlink instead of character node", 234, "symlink", False),
        ("wrong owner", 234, "owner", False),
        ("broadened permissions", 234, "permissions", False),
        ("class resolves elsewhere", 234, "class", False),
        ("wrong subsystem", 234, "subsystem", False),
        ("inconsistent device number", 234, "dev", False),
        ("wrong kernel device name", 234, "uevent", False),
    ]
    results = []
    for label, major, change, expected in cases:
        node, values, links = fixture(major)
        char = f"/sys/dev/char/{major}:8"
        if change == "registration": values["/proc/devices"] = "Character devices:\n234 iio\n"
        if change == "block_only": values["/proc/devices"] = "Character devices:\n234 iio\nBlock devices:\n234 usbmon\n"
        if change == "duplicate": values["/proc/devices"] = "Character devices:\n234 usbmon\n233 usbmon\n"
        if change == "minor": node.st_rdev = os.makedev(major, 7)
        if change == "symlink": node.st_mode = stat.S_IFLNK | 0o600
        if change == "owner": node.st_uid = 1000
        if change == "permissions": node.st_mode = stat.S_IFCHR | 0o666
        if change == "class": links["/sys/class/usbmon/usbmon8"] = "/synthetic/other"
        if change == "subsystem": links[char + "/subsystem"] = "/sys/class/other"
        if change == "dev": values[char + "/dev"] = "235:8\n"
        if change == "uevent": values[char + "/uevent"] = "MAJOR=234\nMINOR=8\nDEVNAME=other\n"

        class FakePath(str):
            def __truediv__(self, component): return FakePath(str(self) + "/" + component)
            def read_text(self): return values[str(self)]
            def resolve(self, strict=False): return FakePath(links[str(self)])

        def fake_lstat(path):
            assert path == "/dev/usbmon8"
            return node

        try:
            exec(code, {"Path": FakePath, "stat": stat,
                        "os": SimpleNamespace(lstat=fake_lstat, major=os.major, minor=os.minor)})
            accepted = True
        except SystemExit:
            accepted = False
        assert accepted == expected, label
        results.append({"case": label, "accepted": accepted})
    print(json.dumps({"passed": True, "hardware_access": False,
                      "source_imported": False, "cases": results}, indent=2))


if __name__ == "__main__":
    main()
