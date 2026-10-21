#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build/stage the separate package helper offline. Never deploy or elevate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from package_control_center import safe_output, copy, run, ROOT, ASSETS

MODULES = ('artifacts.py', 'backend.py', 'package_execution.py', 'package_wire.py',
           'package_host.py', 'package_alpm.py', 'package_helper.py', 'package_catalog.py')
BASE = 'usr/lib/gamesir-control-center/package-executor'
POLICY = 'io.github.RetroGamerGER.gamesir_native.control_center.packages.policy'


def stage(destination, *, catalog_review=None):
    dest = safe_output(destination)
    sys.path.insert(0, str(ROOT / 'tools/control_center'))
    from package_catalog import EMPTY, parse_catalog
    catalog_data = json.dumps(EMPTY, sort_keys=True).encode() + b'\n'
    if catalog_review is not None:
        review = Path(catalog_review)
        if review.is_symlink() or review.absolute() != review.resolve() or not review.is_file():
            raise ValueError('Redirected catalog review')
        with review.open('rb') as stream:
            catalog_data = stream.read(65537)
    if len(catalog_data) > 65536:
        raise ValueError('Oversized catalog review')
    trust = parse_catalog(catalog_data)
    sources = {BASE + '/execute': ASSETS / 'execute-packages',
               'usr/share/polkit-1/actions/' + POLICY: ASSETS / POLICY,
               'usr/share/licenses/gamesir-control-center-executor/COPYING': ROOT / 'COPYING'}
    sources.update({BASE + '/' + name: ROOT / 'tools/control_center' / name for name in MODULES})
    bridge_source = ROOT / 'tools/control_center/alpm_bridge.c'
    if any(path.is_symlink() or not path.is_file() for path in (*sources.values(), bridge_source)):
        raise ValueError('Redirected or missing package helper source')
    dest.mkdir(parents=True)
    for target, source in sources.items():
        copy(source, dest / target, 0o755 if target.endswith('/execute') else 0o644)
    bridge = dest / BASE / 'alpm_bridge.so'
    run(['/usr/bin/cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-fPIC', '-shared',
         '-Wl,-z,relro,-z,now', str(bridge_source),
         '-o', str(bridge), '-lalpm'])
    bridge.chmod(0o644)
    sources[BASE + '/alpm_bridge.so'] = bridge
    catalog_file = dest / BASE / 'REVIEWED_PACKAGES.json'
    catalog_file.write_bytes(catalog_data)
    catalog_file.chmod(0o644)
    sources[BASE + '/REVIEWED_PACKAGES.json'] = catalog_file
    report = {'schema': 1, 'purpose': 'packages', 'installed': False, 'reviewed': False,
              'release_ready': False, 'deployment_catalog_empty': not trust.catalog.records,
              'files': {'/' + target: hashlib.sha256((dest / target).read_bytes()).hexdigest()
                        for target in sorted(sources)},
              'required_private_cache': '/var/cache/gamesir-control-center',
              'cache_mode': '0700', 'activate': False}
    (dest / 'EXECUTOR_REVIEW.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    parser.add_argument('--catalog-review', help='explicit local review data, not deployment approval')
    args = parser.parse_args()
    print(json.dumps(stage(args.dest, catalog_review=args.catalog_review), sort_keys=True))
