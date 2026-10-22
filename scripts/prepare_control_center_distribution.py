#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Prepare a new app with an unchanged reviewed dependency/source baseline.

Local files only. Never download, install, execute source recipes or publish.
The previous source lock must pass before any payload is copied.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import check_control_center_distribution as audit
from package_control_center import safe_output, real_effective_uid, ROOT

APP = 'usr/share/gamesir-control-center'
DOC = 'usr/share/doc/gamesir-control-center'
ASSETS = {'AppRun', 'gamesir-control-center.desktop', 'gamesir-control-center.svg',
          'usr/bin/gamesir-control-center', 'usr/bin/qt.conf',
          'usr/share/applications/gamesir-control-center.desktop',
          'usr/share/icons/hicolor/scalable/apps/gamesir-control-center.svg',
          'usr/share/licenses/gamesir-control-center/COPYING'}


def project_file(name):
    return name in ASSETS or name.startswith((APP + '/', DOC + '/source/'))


def inventory(root, excluded=()):
    return {p.relative_to(root).as_posix(): audit.digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not p.is_symlink() and p.relative_to(root).as_posix() not in excluded}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def rebase_app(previous, current, destination, lock):
    """Only project-owned paths may change; all dependency bytes remain pinned."""
    before = json.loads((previous / 'BUILD_INPUTS.json').read_text())
    fresh = json.loads((current / 'BUILD_INPUTS.json').read_text())
    audit.hashes(previous, lock['appdir_files'], ignore=('BUILD_INPUTS.json',), icon=True)
    audit.hashes(current, fresh['files'], ignore=('BUILD_INPUTS.json',), icon=True)
    if before['files'] != lock['appdir_files'] or set(lock['files']) != set(before['files']):
        raise ValueError('Previous dependency inventory differs')
    for name in fresh['files']:
        if not project_file(name) and name not in lock['files']:
            raise ValueError('New dependency requires separate source/license review')
    for name in lock['files']:
        if project_file(name) and lock['files'][name] != 'project':
            raise ValueError('Project replacement overlaps a third-party component')
    shutil.copytree(previous, destination, symlinks=True)
    owners = dict(lock['files'])
    for name in list(owners):
        if project_file(name):
            (destination / name).unlink()
            del owners[name]
    for name in fresh['files']:
        if project_file(name):
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current / name, path)
            owners[name] = 'project'
    metadata = dict(before, version=fresh['version'], package_binding=fresh['package_binding'],
                    release_ready=False, corresponding_source_review='new source lock required')
    metadata['files'] = inventory(destination, ('BUILD_INPUTS.json',))
    if set(metadata['files']) != set(owners):
        raise ValueError('Rebased payload is not fully attributed')
    for name, owner in owners.items():
        if owner != 'project' and metadata['files'][name] != lock['appdir_files'][name]:
            raise ValueError('Reviewed third-party bytes changed')
    save(destination / 'BUILD_INPUTS.json', metadata)
    return metadata, owners


def archive(destination, rows):
    """Deterministic source files only, no links, owner names or host paths."""
    with destination.open('xb') as output:
        child = subprocess.Popen(['/usr/bin/zstd', '-q', '-T2'], stdin=subprocess.PIPE,
                                 stdout=output, stderr=subprocess.PIPE)
        try:
            with tarfile.open(fileobj=child.stdin, mode='w|', format=tarfile.PAX_FORMAT) as tar:
                for name, path in sorted(rows):
                    audit.relative(name)
                    if path.is_symlink() or not path.is_file():
                        raise ValueError('Unreviewed source object')
                    info = tar.gettarinfo(str(path), name)
                    info.uid = info.gid = 0; info.uname = info.gname = ''; info.mtime = 0
                    info.pax_headers = {}
                    with path.open('rb') as stream:
                        tar.addfile(info, stream)
        finally:
            child.stdin.close()
        if child.wait(timeout=60):
            raise ValueError('Source compression failed')


def prepare(previous, sources, lock_file, current, destination):
    old = json.loads(lock_file.read_text())
    audit.verify(previous, sources, old)
    destination = safe_output(destination)
    destination.mkdir(parents=True, exist_ok=False)
    app = destination / 'GameSir-Control-Center.AppDir'
    meta, owners = rebase_app(previous, current, app, old)
    kit = destination / 'corresponding-sources'; kit.mkdir()
    for name in ('components', 'licenses', 'runtime'):
        shutil.copytree(sources / name, kit / name)
    for name in ('REBUILD.md', 'SUBMODULES.json'):
        shutil.copy2(sources / name, kit / name)
    project = kit / 'project'; project.mkdir()
    archive(project / 'frozen-app-sources.tar.zst', [
        (p.relative_to(app / APP).as_posix(), p) for p in (app / APP).rglob('*')
        if p.is_file() and p.suffix not in ('.so', '.pyc', '.pyo')])
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    archive(project / 'build-and-project-sources.tar.zst',
            [(n, ROOT / n) for n in names if n and n != 'SHA256SUMS'])
    components = copy.deepcopy(old['components'])
    components['project']['version'] = meta['version']
    source_name = 'GameSir-Control-Center-PRE-ALPHA-' + meta['version'] + '-Corresponding-Sources.tar.zst'
    notices = ('# Third-party notices and corresponding sources\n\n'
        'Project-owned sources: GPL-2.0-only; existing UAPI exception retained.\n'
        'Third-party files retain their original licenses and runtime exceptions.\n'
        'Full notices: usr/share/licenses/control-center-distribution/.\n'
        'All dependency bytes and matching sources use the unchanged reviewed alpha1 baseline.\n'
        'Companion source asset: ' + source_name + '\n\n'
        'Garuda x86_64, host glibc 2.44 or newer; no universal Linux or Gamescope installer claim.\n')
    (app / DOC / 'THIRD_PARTY_NOTICES.md').write_text(notices)
    save(app / DOC / 'COMPONENTS.json', components)
    save(kit / 'COMPONENTS.json', components)
    (project / 'THIRD_PARTY_NOTICES.md').write_text(notices)
    tools = project / 'review-tools'; tools.mkdir()
    for name in ('check_control_center_distribution.py', 'prepare_control_center_distribution.py'):
        shutil.copy2(ROOT / 'scripts' / name, tools / name)
    meta['files'] = inventory(app, ('BUILD_INPUTS.json',))
    meta['corresponding_source_review'] = 'technical closure verified against companion source lock'
    save(app / 'BUILD_INPUTS.json', meta)
    save(project / 'APP_BUILD_INPUTS.json', meta)
    new = dict(old, appdir_files=meta['files'], files=owners, components=components,
               source_files=inventory(kit), source_archive_name=source_name)
    save(kit / 'DISTRIBUTION_LOCK.json', new)
    save(destination / 'DISTRIBUTION_LOCK.json', new)
    result = audit.verify(app, kit, new)
    save(destination / 'SOURCE_CLOSURE.json', result)
    return app, kit, new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'sources', 'lock', 'current', 'dest'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    if real_effective_uid() == 0:
        parser.error('Use the ordinary user; this tool never installs or publishes')
    app, kit, lock = prepare(args.previous, args.sources, args.lock, args.current, args.dest)
    print(json.dumps({'version': lock['components']['project']['version'],
                      'appdir_files': len(lock['appdir_files']),
                      'source_files': len(lock['source_files']),
                      'components': len(lock['components']), 'installed': False, 'published': False}))


if __name__ == '__main__':
    main()
