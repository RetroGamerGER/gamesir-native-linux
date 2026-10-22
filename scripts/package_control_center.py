#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline Linux x86_64 AppDir/type-2 AppImage and desktop-payload staging.

No downloads, tool/dependency installation, user integration or driver actions.
Local SDK bundling is a host-baseline test build, not binary-release approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from package_alpha import safe_destination, real_effective_uid

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'packaging/control-center'
APP_ID = 'gamesir-control-center'
QML_TREES = ('QtQml/Models', 'QtQml/WorkerScript', 'QtQuick/Window',
             'QtQuick/Layouts', 'QtQuick/Templates', 'QtQuick/Controls/Basic', 'QtQuick/Controls/impl')
QML_ROOTS = ('QtQml', 'QtQuick', 'QtQuick/Controls')
PLUGINS = ('platforms/libqxcb.so', 'platforms/libqwayland.so', 'platforms/libqoffscreen.so',
           'platforminputcontexts/libcomposeplatforminputcontextplugin.so',
           'imageformats/libqsvg.so', 'iconengines/libqsvgicon.so')
PLUGIN_TREES = ('wayland-shell-integration', 'wayland-graphics-integration-client', 'xcbglintegrations')
PYSIDE_MODULES = ('QtCore', 'QtGui', 'QtNetwork', 'QtOpenGL', 'QtQml', 'QtQuick')
HOST_LIBS = frozenset(('libc.so.6', 'libm.so.6', 'libpthread.so.0', 'libdl.so.2', 'librt.so.1',
                      'libresolv.so.2', 'ld-linux-x86-64.so.2', 'libGL.so.1', 'libEGL.so.1',
                      'libGLX.so.0', 'libGLdispatch.so.0', 'libOpenGL.so.0', 'libvulkan.so.1',
                      'libgbm.so.1', 'libdrm.so.2'))
SKIP_DIRS = frozenset(('__pycache__', 'site-packages', 'test', 'tests', 'ensurepip',
                      'idlelib', 'tkinter', 'turtledemo'))
UNUSED_STDLIB_EXTENSIONS = ('_tkinter*', '_test*', 'xx*', 'readline.*', '_gdbm.*', '_dbm.*')


def remove_unused_stdlib_extensions(directory):
    # This GUI uses JSON files, not an interactive Python shell or DBM storage.
    # Remove optional adapters before resolving ELF dependencies, so their
    # unrelated readline/GDBM libraries do not enter the redistributed bundle.
    for pattern in UNUSED_STDLIB_EXTENSIONS:
        for path in Path(directory).glob(pattern):
            path.unlink()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_output(path):
    raw = Path(path).absolute()
    if raw != raw.resolve():
        raise ValueError('Redirected destinations are refused')
    home = Path.home().resolve()
    forbidden = [home, home / '.local/share', home / '.config', home / 'Desktop', home / 'Schreibtisch']
    forbidden += [Path(os.environ[k]).resolve() for k in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME')
                  if os.environ.get(k)]
    if any(raw == p or (p != home and p in raw.parents) for p in forbidden):
        raise ValueError('No user-profile, desktop or live-integration destination')
    return safe_destination(raw)


def version():
    value = (ASSETS / 'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:\.[0-9A-Za-z]+)+', value):
        raise ValueError('Invalid Control Center version')
    return value


def run(argv, *, timeout=120):
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}
    result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, timeout=timeout, check=False)
    if result.returncode:
        raise ValueError(f'Offline tool failed: {Path(argv[0]).name}: {result.stderr[-1500:]}')
    return result.stdout


def copy(source, target, mode=None):
    source, target = Path(source), Path(target)
    if not source.is_file():
        raise ValueError('Required local build input is missing: ' + source.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(mode if mode is not None else (0o755 if source.stat().st_mode & 0o111 else 0o644))


def tree(source, target, *, recursive=True, skip=()):
    source, target = Path(source), Path(target)
    if not source.is_dir():
        raise ValueError('Required local runtime directory is missing: ' + source.name)
    for folder, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in skip and not (Path(folder) / d).is_symlink()) if recursive else []
        for name in sorted(files):
            if name.endswith(('.pyc', '.pyo')):
                continue
            path = Path(folder) / name
            if path.is_file():
                copy(path, target / path.relative_to(source))


def elf_needed(path):
    output = run(['/usr/bin/readelf', '-d', '--', str(path)])
    names = re.findall(r'\(NEEDED\).*\[([^\]]+)\]', output)
    if any(not re.fullmatch(r'[A-Za-z0-9_.+\-]+', name) for name in names):
        raise ValueError('Unsafe ELF dependency name')
    return names


def bundle_libraries(appdir):
    queue = []
    for path in appdir.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                if stream.read(4) == b'\x7fELF':
                    queue.append(path)
    seen, sources, external = set(), set(), set()
    for binary in queue:
        for name in elf_needed(binary):
            if name in HOST_LIBS:
                external.add(name)
                continue
            if name in seen:
                continue
            source = next((Path(folder) / name for folder in ('/usr/lib', '/usr/lib/libproxy')
                           if (Path(folder) / name).is_file()), None)
            if source is None:
                raise ValueError('Unresolved local ELF dependency: ' + name)
            seen.add(name)
            target = appdir / 'usr/lib' / name
            copy(source, target)
            sources.add(source.resolve())
            queue.append(target)
    # Record the highest declared GLIBC symbol requirement, not a portability claim.
    versions = []
    for binary in queue:
        text = run(['/usr/bin/readelf', '--version-info', '--', str(binary)])
        versions += [tuple(map(int, value.split('.'))) for value in re.findall(r'\bGLIBC_([0-9.]+)', text)]
    return sources, sorted(external), '.'.join(map(str, max(versions))) if versions else 'unknown'


def package_notices(appdir, sources):
    """Preserve locally installed notices; no inference of complete source fulfilment."""
    wanted = {str(p).lstrip('/') for p in sources if str(p).startswith('/usr/')}
    owners, missing = {}, []
    local = Path('/var/lib/pacman/local')
    if local.is_dir():
        for directory in sorted(local.iterdir()):
            files = directory / 'files'
            if not files.is_file() or not wanted.intersection(files.read_text().splitlines()):
                continue
            desc = (directory / 'desc').read_text()
            name = re.search(r'%NAME%\n([^\n]+)', desc)[1]
            ver = re.search(r'%VERSION%\n([^\n]+)', desc)[1]
            owners[name] = ver
            notices = Path('/usr/share/licenses') / name
            if notices.is_dir():
                tree(notices, appdir / 'usr/share/licenses/control-center-bundle' / name)
            else:
                missing.append(name)
    return owners, missing


def stage_reviewed_packages(directory, target):
    # Explicit build-only profile. Never derive trust from a package, host probe
    # or a generated staging manifest; no helper invocation or authentication.
    import sys
    sys.path.insert(0, str(ROOT / 'tools/control_center'))
    from app_packages import load_bundle, bounded_file
    from package_catalog import CATALOG
    bundle = load_bundle(directory)
    catalog = bounded_file(Path(directory) / 'REVIEWED_PACKAGES.json', 65536)
    if sha(catalog) != dict(bundle.pins)[CATALOG]:
        raise ValueError('Reviewed catalog changed during staging')
    profile = {'schema': 1, 'scope': 'local_review', 'pins': bundle.pins,
               'distribution': bundle.distribution, 'kernel': bundle.kernel}
    target.mkdir(parents=True, exist_ok=False)
    (target / 'profile.json').write_text(json.dumps(profile, sort_keys=True) + '\n')
    (target / 'REVIEWED_PACKAGES.json').write_bytes(catalog)
    for component, data in bundle.blobs:
        (target / (component + '.pkg.tar.zst')).write_bytes(data)
    if bundle.release_assets:
        from release_download import serialize_assets
        (target / 'release-assets.json').write_bytes(serialize_assets(bundle.release_assets))
    return {'scope': 'local_review', 'distribution': bundle.distribution,
            'kernel': bundle.kernel, 'components': [r.component for r in bundle.trust.catalog.records],
            'source_mode': 'github_release' if bundle.release_assets else 'embedded',
            'helper_setup_included': False, 'release_ready': False}


def stage_reviewed_helper(directory, package_directory, target):
    # Separate explicit independent helper review, not a runtime path or root
    # script. Snapshot only the fixed thirteen already pinned payload files.
    sys.path.insert(0, str(ROOT / 'tools/control_center'))
    from app_packages import load_bundle
    from helper_setup import load_payload
    bundle = load_bundle(package_directory)
    payload = load_payload(directory, bundle)
    target.mkdir(parents=True, exist_ok=False)
    for path, data, digest in payload.rows:
        output = target / path.lstrip('/')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data); output.chmod(0o644)
    return {'files': len(payload.rows), 'root_script': False, 'installed': False}


def stage_calibration_helper(directory, app):
    """Copy an explicit reviewed companion, never install/elevate its payload."""
    sys.path.insert(0, str(ROOT / 'tools/control_center'))
    from tmr_client import load_pins
    from tmr_wire import HELPER
    source = Path(directory)
    pins = load_pins(source / 'tmr-helper.json')
    for name, digest in pins.items():
        path = source / 'root' / name.lstrip('/')
        if any(p.is_symlink() for p in (path, *path.parents)) or sha(path.read_bytes()) != digest:
            raise ValueError('Calibration helper differs from reviewed manifest')
        copy(path, app / 'tmr-helper-payload' / name.lstrip('/'), 0o755 if name == HELPER else 0o644)
    copy(source / 'tmr-helper.json', app / 'tmr-helper.json')


def stage(destination, *, reviewed_packages=None, reviewed_helper=None, reviewed_tmr=None):
    if reviewed_helper is not None and reviewed_packages is None:
        raise ValueError('Helper payload requires an independently reviewed package bundle')
    dest = safe_output(destination)
    if os.uname().machine != 'x86_64' or sys.platform != 'linux':
        raise ValueError('Current local build profile requires Linux x86_64')
    import sysconfig
    import PySide6
    import shiboken6
    from PySide6.QtCore import QLibraryInfo
    prefix = f'python{sys.version_info.major}.{sys.version_info.minor}'
    stdlib = Path(sysconfig.get_path('stdlib'))
    pyside = Path(PySide6.__file__).parent
    shiboken = Path(shiboken6.__file__).parent
    qml = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath))
    plugins = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
    appdir = dest / 'GameSir-Control-Center.AppDir'
    appdir.mkdir(parents=True)
    copy(Path(sys.executable).resolve(), appdir / 'usr/bin/python3', 0o755)
    tree(stdlib, appdir / 'usr/lib' / prefix, skip=SKIP_DIRS)
    remove_unused_stdlib_extensions(appdir / 'usr/lib' / prefix / 'lib-dynload')
    site = appdir / 'usr/lib' / prefix / 'site-packages'
    tree(pyside, site / 'PySide6', recursive=False)
    # App bindings plus QML's Network/OpenGL type dependencies; no WebEngine,
    # Qt Charts, virtual keyboard, controller reader or unrelated extension.
    for path in (site / 'PySide6').glob('*.so'):
        if not any(path.name.startswith(name + '.') for name in PYSIDE_MODULES):
            path.unlink()
    tree(pyside / 'support', site / 'PySide6/support')
    tree(shiboken, site / 'shiboken6')
    for module in QML_ROOTS:
        tree(qml / module, appdir / 'usr/lib/qt6/qml' / module, recursive=False)
    for module in QML_TREES:
        tree(qml / module, appdir / 'usr/lib/qt6/qml' / module)
    for plugin in PLUGINS:
        copy(plugins / plugin, appdir / 'usr/lib/qt6/plugins' / plugin)
    for folder in PLUGIN_TREES:
        if (plugins / folder).is_dir():
            tree(plugins / folder, appdir / 'usr/lib/qt6/plugins' / folder)
    app = appdir / 'usr/share' / APP_ID
    tree(ROOT / 'tools/control_center', app / 'app')
    copy(ASSETS / 'entry.py', app / 'entry.py')
    if reviewed_tmr is not None:
        stage_calibration_helper(reviewed_tmr, app)
    binding = (stage_reviewed_packages(reviewed_packages, app / 'reviewed-packages')
               if reviewed_packages is not None else None)
    if reviewed_helper is not None:
        binding['helper_setup_included'] = True
        binding['helper_setup'] = stage_reviewed_helper(reviewed_helper, reviewed_packages, app / 'helper-payload')
    copy(ASSETS / 'AppRun', appdir / 'AppRun', 0o755)
    copy(ASSETS / f'{APP_ID}.desktop', appdir / f'{APP_ID}.desktop')
    copy(ASSETS / f'{APP_ID}.desktop', appdir / 'usr/share/applications' / f'{APP_ID}.desktop')
    if binding is not None:
        for desktop in (appdir / f'{APP_ID}.desktop', appdir / 'usr/share/applications' / f'{APP_ID}.desktop'):
            text = desktop.read_text().replace(
                'Read-only GameSir Native Linux status (PRE-ALPHA)',
                'Review GameSir package installation and removal (PRE-ALPHA)').replace(
                'GameSir Native Linux Statusanzeige (PRE-ALPHA, nur lesend)',
                'GameSir-Pakete prüfen, installieren und entfernen (PRE-ALPHA)')
            desktop.write_text(text)
    copy(ASSETS / f'{APP_ID}.svg', appdir / f'{APP_ID}.svg')
    copy(ASSETS / f'{APP_ID}.svg', appdir / 'usr/share/icons/hicolor/scalable/apps' / f'{APP_ID}.svg')
    (appdir / '.DirIcon').symlink_to(f'{APP_ID}.svg')
    (appdir / 'usr/bin' / APP_ID).write_text(
        '#!/bin/sh\n# SPDX-License-Identifier: GPL-2.0-only\n'
        'base=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd -P)\nexec "$base/AppRun" "$@"\n')
    (appdir / 'usr/bin' / APP_ID).chmod(0o755)
    (appdir / 'usr/bin/qt.conf').write_text('[Paths]\nPrefix=..\nPlugins=lib/qt6/plugins\nQmlImports=lib/qt6/qml\n')
    sources, external, glibc = bundle_libraries(appdir)
    sources.update((pyside / '__init__.py', shiboken / '__init__.py', Path(sys.executable).resolve()))
    packages, absent_notices = package_notices(appdir, sources)
    licenses = appdir / 'usr/share/licenses' / APP_ID
    copy(ROOT / 'COPYING', licenses / 'COPYING')
    copy(stdlib / 'LICENSE.txt', licenses / 'PYTHON-LICENSE.txt')
    for name, path in (
            ('QtCore-header.h', '/usr/include/qt6/QtCore/qobject.h'),
            ('QtQuick-header.h', '/usr/include/qt6/QtQuick/qquickitem.h'),
            ('QtControls-header.h', '/usr/include/qt6/QtQuickControls2/qquickstyle.h'),
            ('PySide6-header.h', '/usr/include/PySide6/pyside.h'),
            ('Shiboken6-header.h', '/usr/include/shiboken6/sbkpython.h')):
        copy(path, licenses / 'selected-license-evidence' / name)
    # Include build/launcher sources alongside readable application sources.
    docs = appdir / 'usr/share/doc' / APP_ID
    copy(Path(__file__), docs / 'source/scripts/package_control_center.py')
    copy(ROOT / 'scripts/package_alpha.py', docs / 'source/scripts/package_alpha.py')
    tree(ASSETS, docs / 'source/packaging/control-center')
    manifest = {'schema': 1, 'name': APP_ID, 'version': version(),
                'python': sys.version.split()[0], 'pyside': PySide6.__version__,
                'qt': QLibraryInfo.version().toString(), 'architecture': 'x86_64',
                'required_glibc': glibc, 'host_libraries': external,
                'packages': packages, 'packages_without_local_notices': absent_notices,
                'release_ready': False, 'corresponding_source_review': 'pending',
                'runtime_provenance_review': 'pending', 'installed': False,
                'package_binding': binding,
                'files': {p.relative_to(appdir).as_posix(): sha(p.read_bytes())
                          for p in sorted(appdir.rglob('*')) if p.is_file() and not p.is_symlink()}}
    (appdir / 'BUILD_INPUTS.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    run(['/usr/bin/desktop-file-validate', str(appdir / f'{APP_ID}.desktop')])
    return appdir


def runtime_from_appimage(path, expected):
    if not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('Explicit SHA256 pin required for local runtime container')
    with Path(path).open('rb') as stream:
        data = stream.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024:
        raise ValueError('Runtime container exceeds local profile size limit')
    if sha(data) != expected or len(data) < 64 or data[:11] != b'\x7fELF\x02\x01\x01\x00AI\x02':
        raise ValueError('Runtime container hash or type-2 ELF identity differs')
    if struct.unpack_from('<H', data, 18)[0] != 62:
        raise ValueError('Runtime must be x86_64')
    offset, size, count = struct.unpack_from('<Q', data, 40)[0], *struct.unpack_from('<HH', data, 58)
    if size != 64 or not 0 < count < 256 or offset + size * count > len(data):
        raise ValueError('Invalid runtime section table')
    end = offset + size * count
    for index in range(count):
        section = struct.unpack_from('<IIQQQQIIQQ', data, offset + index * size)
        if section[1] != 8:  # SHT_NOBITS has no bytes in the runtime file.
            end = max(end, section[4] + section[5])
    if data[end:end + 4] != b'hsqs':
        raise ValueError('Expected squashfs directly after runtime ELF')
    return data[:end]


def image(appdir, destination, runtime_container, container_sha, *, epoch=0):
    dest = safe_output(destination)
    appdir = Path(appdir).resolve()
    if type(epoch) is not int or epoch < 0 or epoch > 0xffffffff:
        raise ValueError('Invalid reproducible image timestamp')
    if not (appdir / 'BUILD_INPUTS.json').is_file() or not (appdir / 'AppRun').is_file():
        raise ValueError('Expected a staged Control Center AppDir')
    if appdir == dest or appdir in dest.parents:
        raise ValueError('Image output cannot be inside its AppDir')
    manifest = json.loads((appdir / 'BUILD_INPUTS.json').read_text())
    recorded = manifest.get('files', {})
    actual = {p.relative_to(appdir).as_posix(): sha(p.read_bytes()) for p in appdir.rglob('*')
              if p.is_file() and not p.is_symlink() and p != appdir / 'BUILD_INPUTS.json'}
    if recorded != actual or (appdir / '.DirIcon').readlink() != Path(APP_ID + '.svg'):
        raise ValueError('Staged payload changed after input review')
    if any(p.is_symlink() and p != appdir / '.DirIcon' for p in appdir.rglob('*')):
        raise ValueError('Unexpected redirected AppDir content')
    runtime = runtime_from_appimage(runtime_container, container_sha)
    dest.mkdir(parents=True)
    squash = dest / 'payload.squashfs'
    run(['/usr/bin/mksquashfs', str(appdir), str(squash), '-noappend', '-all-root',
         '-no-xattrs', '-comp', 'gzip', '-processors', '1', '-mkfs-time', str(epoch),
         '-all-time', str(epoch), '-no-progress', '-quiet'], timeout=300)
    target = dest / f'GameSir-Control-Center-PRE-ALPHA-{version()}-x86_64.AppImage'
    with target.open('wb') as stream:
        stream.write(runtime)
        with squash.open('rb') as payload:
            shutil.copyfileobj(payload, stream)
    target.chmod(0o755)
    squash.unlink()
    (dest / 'SHA256SUMS').write_text(f'{sha(target.read_bytes())}  {target.name}\n')
    (dest / 'BUILD_REPORT.json').write_text(json.dumps({
        'schema': 1, 'runtime_container_sha256': container_sha,
        'runtime_sha256': sha(runtime), 'squashfs_offset': len(runtime), 'epoch': epoch,
        'release_ready': False, 'installed': False}, sort_keys=True, indent=2) + '\n')
    return target


def quote_exec(path):
    if any(not c.isprintable() for c in path) or not path.startswith('/'):
        raise ValueError('Expected a printable absolute AppImage path')
    # Desktop Entry string escaping happens before Exec argument escaping.
    escaped = ''.join('\\' + c if c in '\\"`$' else '%%' if c == '%' else c for c in path)
    return '"' + escaped.replace('\\', '\\\\') + '"'


def desktop_payload(appimage, destination):
    dest = safe_output(destination)
    path = Path(appimage).absolute()
    if not path.name.endswith('.AppImage'):
        raise ValueError('Expected an AppImage filename')
    quoted = quote_exec(str(path))
    content = (ASSETS / f'{APP_ID}.desktop').read_text()
    # GIO resolves the first token before expanding %% field codes. A fixed env
    # exec trampoline keeps a literal % in the AppImage filename usable too.
    content = re.sub(r'^Exec=.*$', lambda _: 'Exec=/usr/bin/env -- ' + quoted, content, flags=re.M)
    # TryExec is a literal executable path, not a quoted Exec command line.
    literal = str(path).replace('\\', '\\\\')
    content = re.sub(r'^TryExec=.*$', lambda _: 'TryExec=' + literal, content, flags=re.M)
    dest.mkdir(parents=True)
    desktop = dest / f'applications/{APP_ID}.desktop'
    desktop.parent.mkdir()
    desktop.write_text(content)
    desktop.chmod(0o644)
    icon = dest / f'icons/hicolor/scalable/apps/{APP_ID}.svg'
    copy(ASSETS / f'{APP_ID}.svg', icon)
    run(['/usr/bin/desktop-file-validate', str(desktop)])
    receipt = {'schema': 1, 'installed': False, 'files': {
        p.relative_to(dest).as_posix(): sha(p.read_bytes()) for p in (desktop, icon)}}
    (dest / 'DESKTOP_PAYLOAD.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    return receipt


def removal_preview(payload):
    """Read staged files only; no unlink or live profile operation exists."""
    root = Path(payload)
    receipt = json.loads((root / 'DESKTOP_PAYLOAD.json').read_text())
    allowed = {f'applications/{APP_ID}.desktop', f'icons/hicolor/scalable/apps/{APP_ID}.svg'}
    if (type(receipt.get('schema')) is not int or receipt.get('schema') != 1
            or type(receipt.get('files')) is not dict or set(receipt['files']) != allowed
            or any(not isinstance(h, str) or not re.fullmatch('[0-9a-f]{64}', h)
                   for h in receipt['files'].values())
            or receipt.get('installed') is not False):
        raise ValueError('Unknown desktop payload')
    result = {'matching': [], 'preserve': [], 'missing': []}
    for name, expected in receipt['files'].items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            result['preserve'].append(name)
        elif not path.exists():
            result['missing'].append(name)
        elif sha(path.read_bytes()) == expected:
            result['matching'].append(name)
        else:
            result['preserve'].append(name)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    s = sub.add_parser('stage'); s.add_argument('--dest', required=True)
    s.add_argument('--reviewed-packages', help='explicit independently reviewed local bundle directory')
    s.add_argument('--reviewed-helper', help='explicit independently reviewed helper payload directory')
    s.add_argument('--reviewed-tmr', help='reviewed calibration companion; enables the normal app entry without installing it')
    i = sub.add_parser('image')
    i.add_argument('--appdir', required=True); i.add_argument('--dest', required=True)
    i.add_argument('--runtime-container', required=True); i.add_argument('--container-sha256', required=True)
    i.add_argument('--epoch', type=int, default=0)
    d = sub.add_parser('desktop'); d.add_argument('--appimage', required=True); d.add_argument('--dest', required=True)
    r = sub.add_parser('removal-preview'); r.add_argument('--payload', required=True)
    args = p.parse_args()
    if real_effective_uid() == 0:
        p.error('Build and stage as the ordinary user, never as root')
    if args.action == 'stage':
        print(stage(args.dest, reviewed_packages=args.reviewed_packages, reviewed_helper=args.reviewed_helper,
                    reviewed_tmr=args.reviewed_tmr))
    elif args.action == 'image':
        print(image(args.appdir, args.dest, args.runtime_container, args.container_sha256, epoch=args.epoch))
    elif args.action == 'desktop':
        print(json.dumps(desktop_payload(args.appimage, args.dest), sort_keys=True))
    else:
        print(json.dumps(removal_preview(args.payload), sort_keys=True))


if __name__ == '__main__':
    main()
