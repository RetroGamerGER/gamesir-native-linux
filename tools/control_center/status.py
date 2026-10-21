# SPDX-License-Identifier: GPL-2.0-only
"""Unprivileged local metadata snapshot. No device, manager or network I/O.

Configuration is parsed as data, never executed. The sole child process is a
fixed systemctl SHOW query; DKMS/package status comes from on-disk metadata.
These observations are neither a build audit nor permission to activate things.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import selectors
import shlex
import stat
import subprocess
import time


SERVICE_QUERY = ('/usr/bin/systemctl', '--system', '--no-pager', 'show',
                 'gamesir-native.service', '--property=LoadState,ActiveState,SubState,UnitFileState')
PACKAGES = ('gamesir-native-dkms', 'gamesir-native-steam',
            'gamesir-native-steam-gamescope', 'gamesir-native-trigger-bridge')
DEPENDENCIES = ('dkms', 'python', 'systemd', 'kmod', 'clang', 'llvm', 'lld',
                'make', 'gcc', 'binutils')
PIDS = frozenset(('100a', '109c', '105e', '1022'))
TOKEN = re.compile(r'[A-Za-z0-9_.+\-]{1,160}\Z')


@dataclass(frozen=True)
class Fact:
    state: str = 'unknown'
    value: str = ''


@dataclass(frozen=True)
class Device:
    port: str
    identity: Fact
    binding: Fact


@dataclass(frozen=True)
class Snapshot:
    started: str
    finished: str
    facts: dict
    devices: tuple = ()


def clean(value):
    """Plain short labels; no terminal/markup/control characters or host paths."""
    return ''.join(c for c in value if c.isprintable())[:200]


class LocalReader:
    """Narrow reader, injectable in tests. Never opens /dev or writes files."""
    def text(self, path):
        with Path(path).open('rb') as stream:
            raw = stream.read(1048577)
        if len(raw) > 1048576:
            raise ValueError('Metadata too large')
        return raw.decode('utf-8', errors='strict').strip()

    def entries(self, path):
        with os.scandir(path) as entries:
            result = []
            for entry in entries:
                result.append(entry.name)
                if len(result) > 16384:
                    raise ValueError('Too many metadata entries')
        return sorted(result)

    def stamp(self, path):
        s = os.stat(path)
        return s.st_dev, s.st_ino

    def link(self, path):
        return os.readlink(path)

    def directory(self, path):
        return stat.S_ISDIR(os.stat(path).st_mode)

    def regular(self, path):
        return stat.S_ISREG(os.stat(path).st_mode)

    def uname(self):
        u = os.uname()
        return u.release, u.machine

    def clock(self):
        return datetime.now(timezone.utc).isoformat(timespec='seconds')

    def service(self):
        """Fixed read-only request, clean env, bounded time AND captured bytes."""
        env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'SYSTEMD_PAGER': 'cat',
               'SYSTEMD_COLORS': '0', 'SYSTEMD_OFFLINE': '0'}
        with subprocess.Popen(SERVICE_QUERY, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=env, shell=False, close_fds=True) as child:
            data = bytearray()
            deadline = time.monotonic() + 3
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(child.stdout, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not selector.select(remaining):
                            raise TimeoutError('Status query timed out')
                        chunk = os.read(child.stdout.fileno(), 4096)
                        if not chunk:
                            break
                        data.extend(chunk)
                        if len(data) > 16384:
                            raise ValueError('Status query output too large')
                code = child.wait(timeout=max(0.01, deadline - time.monotonic()))
                if code != 0:
                    # Do not expose stderr, environment or a private host identifier.
                    raise OSError('Status query unavailable')
                return data.decode('utf-8', errors='strict')
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()


def failure(error):
    if isinstance(error, PermissionError):
        return Fact('denied')
    if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
        return Fact('timeout')
    return Fact('unknown')


def fields(text):
    result = {}
    for line in text.splitlines():
        key, separator, value = line.partition('=')
        if separator:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
    return result


def os_release(text):
    result = {}
    for key, value in fields(text).items():
        parts = shlex.split(value, comments=False, posix=True)
        if len(parts) != 1:
            raise ValueError('Malformed os-release')
        result[key] = parts[0]
    if not result.get('ID') or not result.get('PRETTY_NAME'):
        raise ValueError('Missing distribution identity')
    return result


class Collector:
    def __init__(self, reader=None):
        self.r = reader or LocalReader()

    def collect(self):
        r = self.r
        started = r.clock()
        facts = {}
        try:
            release, arch = r.uname()
            if not TOKEN.fullmatch(release) or not TOKEN.fullmatch(arch):
                raise ValueError('Invalid uname')
            facts.update(kernel=Fact('ok', release), architecture=Fact('ok', arch))
        except (OSError, ValueError) as error:
            release = arch = ''
            facts.update(kernel=failure(error), architecture=failure(error))
        try:
            try:
                text = r.text('/etc/os-release')
            except FileNotFoundError:
                text = r.text('/usr/lib/os-release')
            distro = os_release(text)
            facts['os'] = Fact('ok', clean(distro['PRETTY_NAME']))
            # ID_LIKE=arch alone is no evidence of a reviewed installation path.
            facts['support'] = Fact('ok' if distro['ID'] in ('garuda', 'cachyos')
                                    and arch == 'x86_64' else 'unsupported')
        except (OSError, ValueError) as error:
            facts.update(os=failure(error), support=Fact())
        facts.update(self.packages())
        facts.update(self.headers(release))
        facts['dkms'] = self.dkms(release, arch)
        try:
            if not r.directory('/sys/module/gs_native'):
                raise ValueError('Not a module directory')
            try:
                version = clean(r.text('/sys/module/gs_native/version'))
            except FileNotFoundError:
                version = ''
            facts['module'] = Fact('loaded', version) if r.directory('/sys/module/gs_native') else Fact('changed')
        except FileNotFoundError:
            facts['module'] = Fact('absent')
        except (OSError, ValueError) as error:
            facts['module'] = failure(error)
        try:
            values = fields(r.service())
            load, active, sub, enabled = (values[k] for k in
                                         ('LoadState', 'ActiveState', 'SubState', 'UnitFileState'))
            if load not in ('loaded', 'not-found', 'masked', 'error') or active not in (
                    'active', 'inactive', 'activating', 'deactivating', 'failed',
                    'reloading', 'maintenance', 'refreshing') or not TOKEN.fullmatch(sub):
                raise ValueError('Invalid service response')
            facts['service'] = Fact('ok', f'{load} · {active}/{sub}')
            facts['autostart'] = Fact('ok', clean(enabled)) if enabled else Fact()
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            facts.update(service=failure(error), autostart=failure(error))
        # No status socket or on-disk ownership state is accessed in Phase B.
        facts['manager'] = Fact('restricted')
        facts['connection'] = Fact('unobserved')
        devices, facts['receiver'] = self.usb()
        return Snapshot(started, r.clock(), facts, devices)

    def packages(self):
        """Arch ALPM local database only; no executable, lock or repository refresh."""
        r = self.r
        names = (*PACKAGES, *DEPENDENCIES)
        try:
            entries = r.entries('/var/lib/pacman/local')
            found = {}
            for entry in entries:
                if not TOKEN.fullmatch(entry) or not any(entry.startswith(n + '-') for n in names):
                    continue
                before = r.stamp('/var/lib/pacman/local/' + entry)
                desc = r.text('/var/lib/pacman/local/' + entry + '/desc')
                data = {}
                for block in desc.split('\n\n'):
                    lines = block.splitlines()
                    if len(lines) == 2 and lines[0] in ('%NAME%', '%VERSION%'):
                        if lines[0] in data:
                            raise ValueError('Duplicate ALPM field')
                        data[lines[0]] = lines[1]
                name, version = data['%NAME%'], data['%VERSION%']
                if name not in names:
                    continue
                if name in found or not TOKEN.fullmatch(version):
                    raise ValueError('Ambiguous package metadata')
                if before != r.stamp('/var/lib/pacman/local/' + entry):
                    raise ValueError('Package changed during read')
                found[name] = version
            # Detect a transaction during collection instead of claiming removal.
            if entries != r.entries('/var/lib/pacman/local'):
                raise ValueError('Package list changed')
            facts = {name: Fact('ok', found[name]) if name in found else Fact('absent') for name in PACKAGES}
            missing = [n for n in DEPENDENCIES if n not in found]
            facts['dependencies'] = Fact('missing', ', '.join(missing)) if missing else Fact('metadata')
            return facts
        except FileNotFoundError:
            # No ALPM database is not proof that every package is absent.
            return {name: Fact('not_available') for name in (*PACKAGES, 'dependencies')}
        except (OSError, ValueError, KeyError) as error:
            return {name: failure(error) for name in (*PACKAGES, 'dependencies')}

    def headers(self, release):
        if not release:
            return {'headers': Fact(), 'compiler': Fact()}
        base = f'/usr/lib/modules/{release}/build'
        try:
            text = self.r.text(base + '/include/generated/utsrelease.h')
            match = re.fullmatch(r'#define UTS_RELEASE "([A-Za-z0-9_.+\-]+)"', text)
            if not match:
                raise ValueError('Invalid kernel header release')
            if match[1] != release:
                return {'headers': Fact('mismatch', clean(match[1])), 'compiler': Fact()}
            for name in ('Module.symvers', 'Makefile'):
                if not self.r.regular(base + '/' + name):
                    raise FileNotFoundError(name)
            config = fields(self.r.text(base + '/include/config/auto.conf'))
            families = [key for key in ('CONFIG_CC_IS_CLANG', 'CONFIG_CC_IS_GCC') if config.get(key) == 'y']
            if len(families) != 1:
                raise ValueError('Ambiguous kernel compiler family')
            family = 'clang' if families[0] == 'CONFIG_CC_IS_CLANG' else 'gcc'
            return {'headers': Fact('match', release), 'compiler': Fact('ok', family)}
        except FileNotFoundError:
            return {'headers': Fact('missing'), 'compiler': Fact()}
        except (OSError, ValueError) as error:
            return {'headers': failure(error), 'compiler': failure(error)}

    def dkms(self, release, arch):
        if not release or not arch:
            return Fact()
        base = '/var/lib/dkms/gamesir-native'
        try:
            try:
                versions = [n for n in self.r.entries(base) if TOKEN.fullmatch(n) and not n.startswith('kernel-')]
            except FileNotFoundError:
                return Fact('unregistered')
            target = f'kernel-{release}-{arch}'
            try:
                link = self.r.link(base + '/' + target)
            except FileNotFoundError:
                return Fact('unregistered')
            parts = link.split('/')
            if link.startswith('/'):
                parts = parts[len(base.split('/')):]
                if not link.startswith(base + '/'):
                    raise ValueError('Unexpected DKMS target')
            if len(parts) != 3 or parts[0] not in versions or parts[1:] != [release, arch]:
                raise ValueError('Mismatched DKMS registration')
            dest = base + '/' + '/'.join(parts)
            modules = self.r.entries(dest + '/module')
            if not any(n in modules for n in ('gs_native.ko', 'gs_native.ko.zst', 'gs_native.ko.xz', 'gs_native.ko.gz')):
                raise ValueError('Missing built module')
            if not self.r.directory(base + '/' + parts[0] + '/source'):
                raise ValueError('Missing DKMS source')
            if self.r.link(base + '/' + target) != link:
                return Fact('changed')
            return Fact('registered', parts[0])
        except FileNotFoundError:
            # A registered target whose build/source disappeared is inconsistent.
            return Fact('unknown')
        except (OSError, ValueError) as error:
            return failure(error)

    def usb(self):
        base = '/sys/bus/usb/devices'
        try:
            entries = self.r.entries(base)
        except (OSError, ValueError) as error:
            return (), failure(error)
        devices = []
        partial = False
        for name in entries:
            if not re.fullmatch(r'\d+-\d+(?:\.\d+)*', name):
                continue
            path = base + '/' + name
            vendor = ''
            try:
                stamp = self.r.stamp(path)
                vendor = self.r.text(path + '/idVendor').lower()
                if vendor != '3537':
                    continue
                pid = self.r.text(path + '/idProduct').lower()
                if pid not in PIDS:
                    continue
                address = self.r.text(path + '/devnum')
                if not address.isdecimal():
                    raise ValueError('Incomplete USB identity')
                # Interface ownership is metadata, never a binding operation.
                owners = []
                for interface in entries:
                    if re.fullmatch(re.escape(name) + r':\d+\.\d+', interface):
                        try:
                            owners.append(Path(self.r.link(base + '/' + interface + '/driver')).name)
                        except FileNotFoundError:
                            owners.append('unbound')
                if (stamp != self.r.stamp(path) or address != self.r.text(path + '/devnum') or
                        vendor != self.r.text(path + '/idVendor').lower() or
                        pid != self.r.text(path + '/idProduct').lower()):
                    devices.append(Device(name, Fact('changed'), Fact()))
                    partial = True
                    continue
                binding = Fact('ok', ', '.join(sorted({clean(n) for n in owners}))) if owners else Fact()
                devices.append(Device(name, Fact('ok', '3537:' + pid), binding))
            except (OSError, ValueError) as error:
                # An incomplete device might be GameSir: do not infer absence.
                partial = True
                if vendor == '3537':
                    devices.append(Device(name, failure(error), failure(error)))
        try:
            if entries != self.r.entries(base):
                partial = True
        except (OSError, ValueError):
            partial = True
        return tuple(devices), Fact('partial' if partial else 'present' if devices else 'absent')
