# SPDX-License-Identifier: GPL-2.0-only
"""Explicit production adapter, never constructed by normal GUI or tests.

Fixed Arch-family paths and read commands; actual mutation is ALPM commit only.
No network, dependency fetch, manager activation or alternative cleanup path.
"""
from dataclasses import replace
import hashlib
import fnmatch
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

from artifacts import BackendError, COMPONENTS
from backend import HostEvidence, Verification, digest
from package_alpm import Alpm

BASE = Path('/usr/lib/gamesir-control-center/package-executor')
CACHE = Path('/var/cache/gamesir-control-center')
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
DEPENDENCIES = ('dkms', 'python', 'systemd', 'kmod', 'clang', 'llvm', 'lld', 'make', 'gcc', 'binutils')


def protected(path, *, directory=False):
    path = Path(path)
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if (info.st_uid != 0 or info.st_gid != 0 or info.st_mode & 0o022
                or stat.S_ISLNK(info.st_mode)
                or candidate != path and not stat.S_ISDIR(info.st_mode)):
            raise BackendError('unsafe_package_helper_installation')
    info = path.lstat()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise BackendError('unsafe_package_helper_installation')
    return path


def read(path, limit=1024 * 1024):
    with open(path, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise BackendError('system_evidence_limit')
    return data.decode('utf-8').strip()


def command(argv, *, acceptable=(0,)):
    protected(argv[0])
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                            env=ENV, timeout=30, check=False)
    if result.returncode not in acceptable or len(result.stdout) > 1024 * 1024:
        raise BackendError('system_evidence_unavailable')
    return result.stdout.decode('utf-8').strip()


class SystemEvidence:
    """Shared passive facts; inventory is supplied by a read-only or locked adapter."""

    def configuration(self):
        return {key: command(['/usr/bin/pacman-conf', key]) for key in (
            'RootDir', 'DBPath', 'HookDir', 'HoldPkg', 'NoUpgrade', 'NoExtract',
            'IgnorePkg', 'IgnoreGroup', 'LogFile')}

    def service(self):
        text = command(['/usr/bin/systemctl', '--system', '--no-pager', 'show',
                        '-p', 'LoadState', '-p', 'ActiveState', '-p', 'SubState',
                        '-p', 'MainPID', '-p', 'ControlPID', '-p', 'UnitFileState',
                        'gamesir-native.service'])
        result = {}
        for line in text.splitlines():
            key, sep, value = line.partition('=')
            if not sep or key in result:
                raise BackendError('invalid_service_evidence')
            result[key] = value
        if set(result) != {'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlPID', 'UnitFileState'}:
            raise BackendError('invalid_service_evidence')
        if result['UnitFileState'] not in ('enabled', 'disabled', ''):
            raise BackendError('unsupported_service_enablement')
        if result['LoadState'] == 'not-found' and result['UnitFileState'] == '':
            return result, False
        if result['LoadState'] != 'loaded':
            raise BackendError('unsupported_service_state')
        return result, result['UnitFileState'] == 'enabled'

    def observe(self):
        installed = self.alpm.rows()
        # No arbitrary file sourcing/evaluation. Match only the explicit ID.
        os_release = read('/etc/os-release', 32768)
        ids = re.findall(r'^ID=[\"\']?([a-z0-9_-]+)[\"\']?$', os_release, re.M)
        if len(ids) != 1:
            raise BackendError('unsupported_platform')
        kernel = os.uname().release
        if not re.fullmatch(r'[A-Za-z0-9_.+\-]{1,160}', kernel):
            raise BackendError('invalid_kernel_evidence')
        headers = ''
        if self.request.operation == 'install' and 'core' in self.request.components:
            base = Path('/usr/lib/modules') / kernel / 'build'
            # Distribution build symlinks are expected; resolved target must be
            # protected. Never execute Makefile/header content.
            protected(base.resolve(strict=True), directory=True)
            if read(base / 'include/generated/utsrelease.h') == '#define UTS_RELEASE "' + kernel + '"':
                for name in ('Module.symvers', 'Makefile', 'include/config/auto.conf'):
                    protected((base / name).resolve(strict=True))
                headers = kernel
        state, enabled = self.service()
        config = self.configuration()
        if config != self.config:
            raise BackendError('package_configuration_changed')
        # All packages, not just GameSir. Service state belongs to the token,
        # not only its enabled bit. An external change invalidates confirmation.
        token = digest({'installed': installed, 'config': config, 'service': state})
        missing = tuple(p for p in DEPENDENCIES if p not in dict(installed)) if (
            'core' in self.request.components and self.request.operation == 'install') else ()
        return HostEvidence(ids[0], os.uname().machine, kernel, headers,
                            read('/proc/sys/kernel/random/boot_id'), token, self.clock(),
                            installed=installed, missing_dependencies=missing,
                            database_locked=(not getattr(self, 'owns_lock', False)
                                             and Path('/var/lib/pacman/db.lck').exists()),
                            native_loaded=Path('/sys/module/gs_native').exists(), service_enabled=enabled)


class SystemPackages(SystemEvidence):
    def __init__(self, request, *, clock=time.monotonic):
        # This factory must only be called by the installed fixed entry after
        # independent wire/trust checks. Nothing calls it from ordinary status.
        self.request, self.clock = request, clock
        self.alpm = None
        self.guard_verified = False
        protected(CACHE, directory=True)
        if stat.S_IMODE(CACHE.stat().st_mode) != 0o700:
            raise BackendError('unsafe_package_cache')
        self.config = self.configuration()
        # Query separately below; do not guess multi-value directive boundaries.
        if (command(['/usr/bin/pacman-conf', 'RootDir']) != '/'
                or command(['/usr/bin/pacman-conf', 'DBPath']).rstrip('/') != '/var/lib/pacman'):
            raise BackendError('unsupported_package_database')
        self.hookdirs = ['/usr/share/libalpm/hooks'] + command(
            ['/usr/bin/pacman-conf', 'HookDir']).splitlines()
        if not self.hookdirs:
            raise BackendError('package_hook_configuration_unavailable')
        for path in self.hookdirs:
            if not Path(path).is_absolute() or Path(path).as_posix() != path.rstrip('/'):
                raise BackendError('unsafe_package_hook_directory')
            # A missing conventional /etc directory is allowed only if its
            # parent is protected; ALPM treats it as an empty hook directory.
            if Path(path).exists():
                protected(path, directory=True)
            else:
                protected(Path(path).parent, directory=True)
        protected(BASE / 'alpm_bridge.so')

    def acquire(self):
        self.alpm = Alpm(BASE / 'alpm_bridge.so', '/', '/var/lib/pacman', self.hookdirs)
        try:
            self.alpm.call('option', b'Architecture', b'x86_64')
            self.alpm.call('option', b'CheckSpace', b'1')
            logfile = Path(self.config['LogFile'])
            if not logfile.is_absolute():
                raise BackendError('unsafe_package_log')
            protected(logfile if logfile.exists() else logfile.parent,
                      directory=not logfile.exists())
            self.alpm.call('option', b'LogFile', os.fsencode(logfile))
            for name in ('NoUpgrade', 'NoExtract', 'IgnorePkg', 'IgnoreGroup'):
                for value in self.config[name].splitlines():
                    self.alpm.call('option', name.encode('ascii'), value.encode('utf-8'))
            selected = [COMPONENTS[c][0] for c in self.request.components]
            if self.request.operation == 'install' and any(
                    fnmatch.fnmatchcase(name, pattern) for name in selected
                    for pattern in self.config['IgnorePkg'].splitlines()):
                raise BackendError('ignored_package_requires_separate_review')
            # No group-override prompt or assumed yes answer. Group policies
            # need an explicit target-group adapter before enabling this case.
            if self.config['IgnoreGroup']:
                raise BackendError('ignored_group_policy_requires_separate_review')
            if self.request.operation == 'remove' and any(
                    fnmatch.fnmatchcase(name, pattern) for name in selected
                    for pattern in self.config['HoldPkg'].splitlines()):
                raise BackendError('held_package_requires_separate_review')
            self.alpm.acquire()
            self.owns_lock = True
            for name in selected:
                if name in dict(self.alpm.rows()) and self.alpm.lib.gs_alpm_scriptlet(
                        self.alpm.ctx, name.encode('ascii')) != 0:
                    raise BackendError('installed_scriptlet_requires_separate_review')
        except Exception:
            alpm, self.alpm = self.alpm, None
            try:
                alpm.close()
            except Exception:
                pass  # Preserve the original acquisition/preflight failure.
            raise


    def attest_core_guard(self, record):
        for relative, expected in record.guards:
            path = protected('/' + relative)
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise BackendError('installed_core_guard_changed')
            if command(['/usr/bin/pacman', '-Qoq', '--', str(path)]) != COMPONENTS['core'][0]:
                raise BackendError('installed_core_guard_owner_mismatch')
            if relative.endswith('.hook'):
                effective = next((Path(d) / path.name for d in reversed(self.hookdirs)
                                  if os.path.lexists(Path(d) / path.name)), None)
                if effective != path:
                    raise BackendError('installed_core_guard_overridden')
        self.guard_verified = True

    def prepare(self, plan):
        return replace(self.alpm.prepare(plan, CACHE), guard_verified=self.guard_verified)

    def commit(self):
        self.alpm.commit()

    def verify(self, plan):
        installed = self.alpm.rows()
        state, enabled = self.service()
        inactive = (state['ActiveState'] == 'inactive' and state['SubState'] == 'dead'
                    and state['MainPID'] == '0' and state['ControlPID'] == '0')
        module_absent = not Path('/sys/module/gs_native').exists()
        clear = module_absent and not any(Path('/sys/bus/usb/drivers/gs_native').glob('*:*'))
        recovery = Path('/var/lib/gamesir-native/state.json')
        if recovery.exists():
            protected(recovery)
            saved = json.loads(read(recovery))
            clear = clear and type(saved) is dict and saved.get('leases') == {}
        dkms_kernel = version = vermagic = ''
        dkms_installed = dkms_absent = False
        if 'core' in plan.request.components:
            status = command(['/usr/bin/dkms', 'status', '-m', 'gamesir-native'])
            dkms_absent = not status
            if plan.request.operation == 'install':
                artifact = next(a for a in plan.artifacts if a.review.component == 'core')
                version = artifact.review.version.rsplit('-', 1)[0]
                expected = f'gamesir-native/{version}, {plan.host.kernel}, {plan.host.architecture}: installed'
                dkms_installed = expected in status.splitlines()
                dkms_kernel = plan.host.kernel if dkms_installed else ''
                version = command(['/usr/bin/modinfo', '-k', plan.host.kernel, '-F', 'version', 'gs_native'])
                vermagic = command(['/usr/bin/modinfo', '-k', plan.host.kernel, '-F', 'vermagic', 'gs_native']).split()[0]
        return Verification(installed, core_guard_clear=clear, dkms_kernel=dkms_kernel,
                            module_version=version, vermagic_kernel=vermagic,
                            service_inactive=inactive, module_absent=module_absent,
                            service_enabled=enabled, dkms_installed=dkms_installed,
                            dkms_absent=dkms_absent)

    def close(self):
        if self.alpm is not None:
            alpm, self.alpm = self.alpm, None
            self.owns_lock = False
            alpm.close()
