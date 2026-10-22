#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline source recipe for the optional, explicitly enabled TMR helper."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
import sys

from package_control_center import safe_output, ROOT
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from tmr_wire import BASE, HELPER, POLICY, MODULES


def source(destination):
    dest = safe_output(destination)
    rows = [(HELPER, ROOT / 'packaging/control-center/tmr/execute'),
            (POLICY, ROOT / 'packaging/control-center/tmr' / Path(POLICY).name),
            ('/usr/share/licenses/gamesir-native-tmr-helper/COPYING', ROOT / 'COPYING')]
    rows += [(BASE + '/' + name, ROOT / 'tools/control_center' / name) for name in MODULES]
    memory = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=memory, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.PAX_FORMAT) as tar:
            for name, path in sorted(rows):
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Missing or redirected helper source')
                data = path.read_bytes()
                member = tarfile.TarInfo('gamesir-native-tmr-helper-0.1.0.alpha1/' + name.lstrip('/'))
                member.size = len(data); member.mode = 0o755 if name == HELPER else 0o644
                member.uid = member.gid = member.mtime = 0
                tar.addfile(member, io.BytesIO(data))
    data = memory.getvalue(); digest = hashlib.sha256(data).hexdigest()
    recipe = (ROOT / 'packaging/tmr-helper/PKGBUILD.in').read_text().replace('@SOURCE_SHA256@', digest)
    dest.mkdir(parents=True, exist_ok=True)
    filename = 'gamesir-native-tmr-helper-0.1.0.alpha1.tar.gz'
    (dest / filename).write_bytes(data); (dest / 'PKGBUILD').write_text(recipe)
    (dest / 'SHA256SUMS').write_text(digest + '  ' + filename + '\n'
        + hashlib.sha256(recipe.encode()).hexdigest() + '  PKGBUILD\n')
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    print(source(parser.parse_args().dest))
