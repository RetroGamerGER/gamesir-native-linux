#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Verify the device-free test namespace, then replace this process with probe."""
import ctypes
import json
import os
from pathlib import Path
import stat
import sys

host = json.loads(os.environ["GS_HOST_NS"])
guest = {n: os.readlink("/proc/self/ns/" + n) for n in host}
assert all(host[n] != guest[n] for n in host), (host, guest)
libc = ctypes.CDLL(None, use_errno=True)
assert libc.prctl(38, 1, 0, 0, 0) == 0  # PR_SET_NO_NEW_PRIVS; this process only
status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
caps = {k: status[k].strip() for k in ["CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"]}
assert all(int(v, 16) == 0 for v in caps.values()), caps
assert status["NoNewPrivs"].strip() == "1"
device_nodes = []
for directory, subdirs, names in os.walk("/dev", followlinks=False):
    for name in names:
        p = Path(directory) / name
        mode = p.lstat().st_mode
        if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
            device_nodes.append(str(p))
assert set(device_nodes) <= {"/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom", "/dev/tty", "/dev/pts/ptmx"}, device_nodes
assert stat.S_ISREG(Path("/dev/iio:device0").stat().st_mode)
assert not Path("/dev/input").exists() and not Path("/dev/bus/usb").exists()
assert not Path("/dev/usbmon8").exists()
print("sandbox-audit=" + json.dumps({"namespaces": guest, "all_six_separate": True,
    "capabilities": caps, "NoNewPrivs": 1, "device_nodes": sorted(device_nodes),
    "iio_fixture_is_regular_file": True, "uid": os.getuid(), "gid": os.getgid()}), flush=True)
env = dict(os.environ, LD_PRELOAD="/tests/fixture.so")
os.execve(sys.argv[1], [sys.argv[1]], env)
