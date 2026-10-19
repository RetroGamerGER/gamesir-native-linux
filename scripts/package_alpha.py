#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Create an offline source archive or unprivileged DESTDIR. Never install/load."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOTS = ('/usr', '/etc', '/var', '/opt', '/bin', '/sbin', '/lib', '/lib64',
                '/boot', '/dev', '/proc', '/sys', '/run')
LICENSE_FILES = ('COPYING', 'LICENSES/exceptions/Linux-syscall-note')
DOCUMENT_FILES = (
    'README.md', 'AGENTS.md',
    'docs/LICENSING.md',
    'docs/INSTALLATION.md', 'docs/RELEASE_AUDIT.md', 'docs/PUBLIC_RELEASE_CHECK.md',
    'tools/offline/docs/source-map.json',
    'docs/ALPHA_INSTALLATION.md', 'docs/ALPHA_RUNTIME.md', 'docs/ALPHA_INSTALL_AUDIT.md',
    'docs/MANAGER_CONFLICT_FIX.md',
    'docs/MANAGER_RECONNECT_FIX.md',
    'docs/BOOTSTRAP_CACHYOS_FIX.md',
    'docs/evidence/CACHYOS_BOOTSTRAP_20261015.json',
    'docs/DUALSENSE_SENSOR_COMPARISON.md',
    'docs/SDL_EDEN_GYRO.md', 'docs/sdl-eden-gyro-validation.json',
    'docs/STEAM_ACCEL_EXTENSION.md', 'docs/steam-accel-extension-validation.json',
    'docs/evidence/STEAM_ACCEL_INSTALL_20261019.json',
    'docs/evidence/STEAM_ACCEL_ACTIVATION_20261019.json',
    'docs/steam-accel-held-pose-evidence.json', 'docs/STEAM_GYRO_DOWNSTREAM.md',
    'docs/steam-gyro-downstream-offline.json', 'docs/steam-gyro-notification-gates-offline.json',
    'docs/steam-gyro-observation-live-001.json', 'docs/STEAM_GYRO_FEASIBILITY.md',
    'docs/STEAM_GYRO_HOTPLUG.md', 'docs/steam-gyro-hotplug-offline.json',
    'docs/STEAM_GUIDE_GYRO.md', 'docs/steam-guide-gyro-offline.json',
    'docs/input-publication-offline.json',
    'docs/evidence/INPUT_PUBLICATION_INSTALL_20261019.json',
    'docs/EXPERIMENTAL_GYRO_TEST.md', 'docs/experimental-gyro-validation.json',
    'docs/COHERENT_IMU_CALIBRATION.md', 'docs/coherent-imu-validation.json',
    'docs/COHERENT_IMU_UPDATE.md', 'docs/evidence/COHERENT_IMU_INSTALL_20261016.json',
    'docs/GYRO_AXIS_TEST.md', 'docs/IIO_SCAN_SELECTION_FIX.md',
    'docs/experimental-gyro-live-001.json',
    'docs/experimental-gyro-live-002.json',
    'docs/GAMESIR_NEXUS_RESEARCH.md', 'docs/NEXUS_SENSOR_DATAFLOW.md',
    'docs/ROADMAP.md',
    'docs/SDL-SENSOR-ERGEBNIS.rst', 'docs/SDL-SKALIERUNG-UND-ACHSEN.rst',
    'docs/imu-calibration-analysis.json', 'docs/sdl-source-manifest.json',
    'docs/ARCHITECTURE.md', 'docs/G7_PRO_VARIANTS.md', 'docs/FOUR_MOTOR_KERNEL.md',
    'docs/GIT_SETUP_VALIDATION.md', 'docs/HAPTICS_API.md',
    'docs/TRIGGER_BRIDGE.md', 'docs/TRIGGER_BRIDGE_PROVENANCE.md',
    'docs/STEAM_PROTON_TRIGGER_BRIDGE.md',
    'docs/HARDWARE_TEST_001.md', 'docs/HARDWARE_TEST_002.md',
    'docs/HARDWARE_TEST_002_OFFLINE_CHECK.md', 'docs/HARDWARE_TEST_002_PROGRESS.md',
    'docs/HARDWARE_TEST_003.md', 'docs/HARDWARE_TEST_PLAN.md',
    'docs/KERNEL_PROTOTYPE.md', 'docs/MOTOR_COMPARISON_PLAN.md',
    'docs/MOTOR_COMPARISON_RESULTS.md', 'docs/NATIVE_INSTALLATION_READINESS.md',
    'docs/NATIVE_MOTOR_COMPARISON.md', 'docs/NATIVE_MOTOR_COMPARISON_RESULTS.md',
    'docs/NATIVE_STARTUP_KERNEL.md', 'docs/NATIVE_STARTUP_OFFLINE.md',
    'docs/PROJECT_STATE.md', 'docs/PROJECT_STRUCTURE.md', 'docs/PROTOCOL.md',
    'docs/SDL_EXTRA_BUTTONS.md', 'docs/STEAM_PROTON_BUTTONS.md',
    'docs/STEAM_ELITE_PADDLES.md', 'docs/STEAM_INTEGRATION.md', 'docs/STEAM_GAMESCOPE.md',
    'docs/SYSTEM_FREEZE_20261014.md',
    'docs/FF_LIFETIME_FIX.md', 'docs/TESTING.md',
    'docs/sdl-sensor-calibration.json',
)


def version(root=ROOT):
    value = (root / 'packaging/VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:\.[0-9A-Za-z]+)+', value):
        raise ValueError('Invalid package version')
    return value


def source_files(root=ROOT):
    """Explicit allowlist; never sweep captures, build outputs or local settings."""
    paths = [*DOCUMENT_FILES, *LICENSE_FILES,
             'scripts/package_alpha.py', 'scripts/kernel_toolchain.py',
             'tools/native/gsnative-ctl.c',
             'tools/service/gamesir_native.py', 'tools/service/haptics_broker.py',
             'tools/service/input_readiness.py', 'tools/sdl/input_pair_readiness.py',
             'tools/haptics/gamesir_haptics.py', 'tools/sdl/gamesir_mapping.py']
    patterns = {
        'kernel': ('gs_native_usb.c', 'gs_protocol.c', 'gs_sensor.c',
                   'gs_runtime.c', 'gs_startup.c', 'Kbuild'),
        'src': ('gs_protocol.c', 'gs_protocol.h', 'gs_sensor.c', 'gs_sensor.h',
                'gs_runtime.c', 'gs_runtime.h', 'gs_startup.c', 'gs_startup.h'),
        'include/uapi': ('gs_native.h',),
        'packaging': ('VERSION', 'dkms.conf.in', 'prepare_remove.py',
                      'bin/gamesir-native', 'systemd/gamesir-native.service',
                      'sysusers/gamesir-native.conf',
                      'udev/70-gamesir-native-sensors.rules',
                      'arch/PKGBUILD.in', 'arch/60-gamesir-native-release.hook',
                      'arch/60-gamesir-native-upgrade.hook'),
    }
    for folder, names in patterns.items():
        paths.extend(f'{folder}/{name}' for name in names)
    unique = sorted(set(paths))
    for path in unique:
        item = root / path
        if item.is_symlink() or not item.is_file():
            raise ValueError(f'Required regular source missing: {path}')
    return unique


def real_effective_uid():
    # makepkg's fakeroot intentionally reports euid 0 via libc. The kernel
    # process record distinguishes it from an actual privileged build.
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('Uid:'):
            fields = line.split()[1:]
            if len(fields) == 4 and all(field.isdecimal() for field in fields):
                return int(fields[1])
    raise ValueError('Cannot verify unprivileged packaging process')


def safe_destination(path):
    if real_effective_uid() == 0:
        raise ValueError('Packaging runs unprivileged; no root build or live installation')
    path = Path(path).resolve()
    if path == Path('/') or any(path == Path(p) or Path(p) in path.parents for p in SYSTEM_ROOTS):
        raise ValueError('System destinations are forbidden; use an offline staging directory')
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError('Destination must be absent or empty; existing files are preserved')
    return path


def source_archive(dest, root=ROOT):
    dest = safe_destination(dest)
    files = source_files(root)
    ver = version(root)
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '0'))
    if epoch < 0:
        raise ValueError('SOURCE_DATE_EPOCH must not be negative')
    stream = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=epoch) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for path in files:
                data = (root / path).read_bytes()
                info = tarfile.TarInfo(f'gamesir-native-{ver}/{path}')
                info.size, info.mtime, info.mode = len(data), epoch, 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                archive.addfile(info, io.BytesIO(data))
    data = stream.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    pkgbuild = (root / 'packaging/arch/PKGBUILD.in').read_text().replace(
        '@VERSION@', ver).replace('@SOURCE_SHA256@', digest)
    dest.mkdir(parents=True, exist_ok=True)
    name = f'gamesir-native-{ver}.tar.gz'
    (dest / name).write_bytes(data)
    (dest / 'PKGBUILD').write_text(pkgbuild)
    (dest / 'SHA256SUMS').write_text(
        f'{digest}  {name}\n{hashlib.sha256(pkgbuild.encode()).hexdigest()}  PKGBUILD\n')
    return {'version': ver, 'archive': str(dest / name), 'sha256': digest,
            'source_files': len(files), 'installed': False}


def stage(dest, client, root=ROOT):
    dest = safe_destination(dest)
    ver = version(root)
    source_files(root)  # Validate the complete input before creating output.
    client = Path(client).resolve()
    if not client.is_file() or client.read_bytes()[:4] != b'\x7fELF':
        raise ValueError('Expected the locally built ELF gsnative-ctl')
    dest.mkdir(parents=True, exist_ok=True)

    def copy(source, target, mode=0o644):
        out = dest / target
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, out)
        out.chmod(mode)

    source_prefix = f'usr/src/gamesir-native-{ver}'
    for relative in source_files(root):
        if (relative.startswith(('kernel/', 'src/', 'include/uapi/')) or
                relative == 'scripts/kernel_toolchain.py' or relative in LICENSE_FILES):
            copy(root / relative, f'{source_prefix}/{relative}')
    dkms = dest / source_prefix / 'dkms.conf'
    dkms.write_text((root / 'packaging/dkms.conf.in').read_text().replace('@VERSION@', ver))
    copy(client, 'usr/lib/gamesir-native/gsnative-ctl', 0o755)
    copy(root / 'tools/service/gamesir_native.py', 'usr/lib/gamesir-native/gamesir_native.py')
    copy(root / 'tools/service/haptics_broker.py', 'usr/lib/gamesir-native/haptics_broker.py')
    copy(root / 'tools/service/input_readiness.py', 'usr/lib/gamesir-native/input_readiness.py')
    copy(root / 'tools/sdl/input_pair_readiness.py', 'usr/lib/gamesir-native/input_pair_readiness.py')
    copy(root / 'tools/haptics/gamesir_haptics.py', 'usr/lib/gamesir-native/gamesir_haptics.py')
    copy(root / 'tools/sdl/gamesir_mapping.py', 'usr/lib/gamesir-native/gamesir_mapping.py')
    copy(root / 'packaging/prepare_remove.py', 'usr/lib/gamesir-native/prepare_remove.py')
    copy(root / 'packaging/bin/gamesir-native', 'usr/bin/gamesir-native', 0o755)
    copy(root / 'packaging/systemd/gamesir-native.service',
         'usr/lib/systemd/system/gamesir-native.service')
    copy(root / 'packaging/sysusers/gamesir-native.conf',
         'usr/lib/sysusers.d/gamesir-native.conf')
    copy(root / 'packaging/udev/70-gamesir-native-sensors.rules',
         'usr/lib/udev/rules.d/70-gamesir-native-sensors.rules')
    for hook in (root / 'packaging/arch').glob('*.hook'):
        copy(hook, f'usr/share/libalpm/hooks/{hook.name}')
    for doc in DOCUMENT_FILES:
        copy(root / doc, f'usr/share/doc/gamesir-native/{doc}')
    # Retain the source-relative paths for license links in the documentation
    # and DKMS tree; Arch's standard license directory also carries both texts.
    for relative in LICENSE_FILES:
        copy(root / relative, f'usr/share/doc/gamesir-native/{relative}')
        copy(root / relative,
             f'usr/share/licenses/gamesir-native-dkms/{Path(relative).name}')
    return {'version': ver, 'staged': str(dest),
            'files': sum(p.is_file() for p in dest.rglob('*')), 'installed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    archive = sub.add_parser('source')
    archive.add_argument('--dest', required=True)
    staged = sub.add_parser('stage')
    staged.add_argument('--dest', required=True)
    staged.add_argument('--client', default=str(ROOT / 'build/gsnative-ctl'))
    args = parser.parse_args()
    result = source_archive(args.dest) if args.action == 'source' else stage(args.dest, args.client)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
