#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Stage calibration helper/policy/pins offline. Never installs or authorizes."""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/control_center'))
from tmr_wire import BASE, HELPER, POLICY, MODULES, encode


def stage(destination):
    dest = Path(destination).absolute()
    build = ROOT/'build'
    if not dest.is_relative_to(build) or dest == build or any(p.is_symlink() for p in (dest,*dest.parents)):
        raise ValueError('Use a new directory inside the project build directory')
    dest.mkdir(parents=True, exist_ok=False)
    rows = [(HELPER,ROOT/'packaging/control-center/tmr/execute'),
            (POLICY,ROOT/'packaging/control-center/tmr'/Path(POLICY).name)]
    rows += [(BASE+'/'+name,ROOT/'tools/control_center'/name) for name in MODULES]
    pins = {}
    for target, source in rows:
        output = dest/'root'/target.lstrip('/')
        output.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        output.write_bytes(data); output.chmod(0o755 if target == HELPER else 0o644)
        pins[target] = hashlib.sha256(data).hexdigest()
    (dest/'tmr-helper.json').write_bytes(encode({'schema':1,'files':pins}))
    return dest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    args = parser.parse_args()
    print(stage(args.dest))
