#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Stage optional authorization-only helper and Polkit policy, never install."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from package_control_center import safe_output, copy, ROOT, ASSETS

sys.path.insert(0, str(ROOT / 'tools/control_center'))
from privilege.protocol import BASE, FILES, POLICY


def stage(destination):
    dest = safe_output(destination)
    sources = {BASE + '/authorize': ASSETS / 'authorize',
               POLICY: ASSETS / Path(POLICY).name}
    for name in ('__init__.py', 'protocol.py', 'helper.py'):
        sources[BASE + '/privilege/' + name] = ROOT / 'tools/control_center/privilege' / name
    if set(sources) != set(FILES) or any(p.is_symlink() for p in sources.values()):
        raise ValueError('Unexpected authorization payload')
    dest.mkdir(parents=True)
    hashes = {}
    for target, source in sorted(sources.items()):
        copy(source, dest / target.lstrip('/'), 0o755 if target.endswith('/authorize') else 0o644)
        hashes[target] = hashlib.sha256(source.read_bytes()).hexdigest()
    copy(ROOT / 'COPYING', dest / 'usr/share/licenses/gamesir-control-center-auth/COPYING', 0o644)
    report = {'schema': 1, 'purpose': 'authorize_only', 'installed': False,
              'reviewed': False, 'release_ready': False, 'files': hashes}
    (dest / 'AUTHORIZATION_REVIEW.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.dest), sort_keys=True))


if __name__ == '__main__':
    main()
