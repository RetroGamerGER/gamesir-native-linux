# SPDX-License-Identifier: GPL-2.0-only
"""First-run helper setup: unprivileged orchestration, fixed system tools only.

Import/construct is inert. No package/driver action, root AppImage code, shell,
overwrite/update, credential handling, automatic retry or rollback exists here.
"""
from dataclasses import dataclass
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import threading
import time

from artifacts import BackendError
from app_packages import bounded_file
from package_client import FILES
from package_wire import ACTION, EXECUTOR, POLICY
from privilege.protocol import AuthorizationError

BASE = '/usr/lib/gamesir-control-center/package-executor'
PARENT = '/usr/lib/gamesir-control-center'
LICENSE = '/usr/share/licenses/gamesir-control-center-executor'
COPYING = LICENSE + '/COPYING'
CACHE = '/var/cache/gamesir-control-center'
GPL_SHA = 'e6d6a009505e345fe949e1310334fcb0747f28dae2856759de102ab66b722cb4'
DIRS = ((BASE, 0o755), (LICENSE, 0o755), (CACHE, 0o700))
TARGETS = (*FILES, COPYING)
TOOLS = ('/usr/bin/sudo', '/usr/bin/mkdir', '/usr/bin/install', '/usr/bin/ksshaskpass',
         '/usr/bin/pkaction', '/usr/bin/pkexec', '/usr/bin/python3')
SUDO = ('/usr/bin/sudo', '-A', '-p', 'Password: ', '--')
SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}


def mode(path):
    return 0o755 if path == EXECUTOR else 0o644


@dataclass(frozen=True)
class SetupPayload:
    rows: tuple  # fixed (target, immutable bytes, digest), never an arbitrary path.

    def validate(self):
        if (type(self.rows) is not tuple or len(self.rows) != len(TARGETS)
                or any(type(r) is not tuple or len(r) != 3 for r in self.rows)
                or {r[0] for r in self.rows} != set(TARGETS)):
            raise BackendError('invalid_setup_payload')
        for path, data, digest in self.rows:
            if (type(path) is not str or type(data) is not bytes or not 0 < len(data) <= 262144
                    or type(digest) is not str or hashlib.sha256(data).hexdigest() != digest):
                raise BackendError('invalid_setup_payload')


def load_payload(directory, bundle):
    # Review pins come from an explicitly reviewed build; no staging manifest
    # becomes approval and no installed catalog is replaced by a runtime input.
    expected = {**dict(bundle.pins), COPYING: GPL_SHA}
    rows = tuple((p, bounded_file(Path(directory) / p.lstrip('/'), 262144), expected[p])
                 for p in TARGETS)
    payload = SetupPayload(rows); payload.validate()
    return payload


class FixedTarget:
    """Passive fixed-target metadata queries; methods only run when scheduled."""
    def exists(self, path):
        try:
            os.lstat(path)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            # Denied/invalid metadata is never proof that a target is absent.
            raise BackendError('setup_target_unreadable') from None

    def directory(self, path, expected=None):
        from package_host import protected
        protected(path, directory=True)
        if expected is not None and stat.S_IMODE(Path(path).stat().st_mode) != expected:
            raise BackendError('setup_directory_changed')

    def file(self, path, digest, expected_mode):
        from package_host import protected
        protected(path)
        info = Path(path).stat()
        if (info.st_size > 262144 or stat.S_IMODE(info.st_mode) != expected_mode
                or hashlib.sha256(bounded_file(path, 262144)).hexdigest() != digest):
            raise BackendError('setup_file_changed')

    def query(self, argv):
        from package_host import protected
        protected(str(Path(argv[0]).resolve(strict=True)))
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                env=ENV, timeout=10, check=False)
        if len(result.stdout) + len(result.stderr) > 32768:
            raise BackendError('setup_query_limit')
        return result.returncode, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

    def policy(self, installed):
        code, out, err = self.query(['/usr/bin/pkaction', '--action-id', ACTION, '--verbose'])
        if not installed:
            if code != 1 or err.strip() != 'No action with action id ' + ACTION:
                raise BackendError('unexpected_setup_policy')
            return
        if code or ACTION not in out:
            raise BackendError('setup_policy_unconfirmed')
        for name, value in (('any', 'no'), ('inactive', 'no'), ('active', 'auth_admin')):
            if not re.search(r'implicit\s+' + name + r':\s*' + value + r'\s*(?:\n|$)', out):
                raise BackendError('setup_policy_changed')
        if ('org.freedesktop.policykit.exec.path -> ' + EXECUTOR not in out
                or 'Authenticate to install or remove the reviewed GameSir packages.' not in out):
            raise BackendError('setup_policy_changed')

    def prerequisites(self):
        if os.geteuid() == 0:
            raise BackendError('desktop_user_required')
        from privilege.transport import InstalledAuditor
        auditor = InstalledAuditor()
        for path in TOOLS:
            # Conventional system links are permitted only to a protected root
            # executable. Nothing is resolved through PATH or an AppImage.
            auditor.inspect(str(Path(path).resolve(strict=True)), executable=True)
        library = Path('/usr/lib/libalpm.so').resolve(strict=True)
        auditor.inspect(str(library))
        if not re.fullmatch(r'libalpm\.so\.16(?:\.[0-9]+)+', library.name):
            raise BackendError('setup_runtime_abi_mismatch')
        if self.query(['/usr/bin/systemctl', 'is-active', 'polkit.service'])[:2] != (0, 'active\n'):
            raise BackendError('setup_agent_unavailable')
        session = os.environ.get('XDG_SESSION_ID', '')
        if not re.fullmatch(r'(?:[0-9]+|c[0-9]+)', session):
            raise BackendError('setup_desktop_session_required')
        code, text, _ = self.query(['/usr/bin/loginctl', 'show-session', session,
            '-p', 'User', '-p', 'Remote', '-p', 'Active', '-p', 'State', '-p', 'Type'])
        facts = dict(line.split('=', 1) for line in text.splitlines())
        if (code or facts.get('User') != str(os.getuid()) or facts.get('Remote') != 'no'
                or facts.get('Active') != 'yes' or facts.get('State') != 'active'
                or facts.get('Type') not in ('wayland', 'x11')
                or not any(os.environ.get(k) for k in ('DISPLAY', 'WAYLAND_DISPLAY'))):
            raise BackendError('setup_desktop_session_required')


@dataclass(frozen=True)
class SetupReview:
    directories: tuple

    def summary(self):
        return {'files': len(TARGETS), 'directories': len(self.directories),
                'targets': list(TARGETS), 'directory_paths': [p for p, m in self.directories],
                'package_action': False, 'activation': False}


class SetupInspector:
    def __init__(self, target=None):
        self.target = FixedTarget() if target is None else target

    def inspect(self, payload):
        payload.validate()
        t = self.target
        present = tuple(t.exists(p) for p in TARGETS)
        if any(present):
            if not all(present):
                raise BackendError('setup_partial_installation')
            t.directory(PARENT)
            for path, expected in DIRS: t.directory(path, expected)
            for path, data, digest in payload.rows: t.file(path, digest, mode(path))
            t.policy(True)
            return None  # Already exact; never reinstall or authenticate.
        if any(t.exists(p) for p, _ in DIRS):
            raise BackendError('setup_partial_installation')
        for parent in ('/usr/lib', '/usr/share/licenses', '/usr/share/polkit-1/actions', '/var/cache'):
            t.directory(parent)
        parents = ()
        if t.exists(PARENT): t.directory(PARENT)
        else: parents = ((PARENT, 0o755),)
        t.prerequisites(); t.policy(False)
        return SetupReview(parents + DIRS)


class SetupCommandError(Exception):
    def __init__(self, code): self.code = code


def validate_command(argv, source):
    if type(argv) is not tuple or argv[:len(SUDO)] != SUDO:
        raise SetupCommandError('invalid_setup_command')
    tail = argv[len(SUDO):]
    directories = dict(((PARENT, 0o755), *DIRS))
    if (len(tail) == 5 and tail[0] == '/usr/bin/mkdir' and source is None
            and tail[-1] in directories
            and tail[1:4] == ('-m', format(directories[tail[-1]], '04o'), '--')):
        return
    if (len(tail) == 10 and tail[-1] in TARGETS and source is not None
            and tail[:-1] == ('/usr/bin/install', '-o', 'root', '-g', 'root', '-m',
                             format(mode(tail[-1]), '04o'), '--', '/dev/stdin')
            and fcntl.fcntl(source.fileno(), fcntl.F_GET_SEALS) & SEALS == SEALS):
        return
    raise SetupCommandError('invalid_setup_command')


class SystemSetupRunner:
    """Only called after GUI setup confirmation; no root-owned script is run."""
    def __call__(self, argv, source=None):
        validate_command(argv, source)
        env = {k: os.environ[k] for k in ('HOME', 'DISPLAY', 'WAYLAND_DISPLAY',
            'DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR', 'XAUTHORITY',
            'KDE_FULL_SESSION', 'KDE_SESSION_VERSION') if k in os.environ}
        env.update(ENV, SUDO_ASKPASS='/usr/bin/ksshaskpass')
        # Do not retain passwords or raw errors. A timeout cannot safely imply
        # the privileged child stopped, and never triggers another command.
        with open(os.devnull, 'wb') as sink:
            child = subprocess.Popen(argv, stdin=source if source is not None else subprocess.DEVNULL,
                                     stdout=sink, stderr=sink, env=env, close_fds=True, shell=False)
        try:
            code = child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            threading.Thread(target=child.wait, daemon=True).start()
            raise SetupCommandError('setup_completion_unknown') from None
        if code:
            raise SetupCommandError('setup_command_failed')


@dataclass(frozen=True)
class SetupResult:
    state: str
    error: str = ''
    changes_possible: bool = False


class SetupSession:
    def __init__(self, payload, review, *, inspector, fresh_check, runner=None,
                 clock=time.monotonic, expires_at=None):
        self.payload, self.review, self.inspector = payload, review, inspector
        self.fresh_check = fresh_check
        self.runner = SystemSetupRunner() if runner is None else runner
        self.clock = clock
        self.expires_at = clock() + 120 if expires_at is None else expires_at
        self.used, self.outcome = False, None

    def run(self):
        if self.used: return self.outcome
        self.used = True
        handles, possible = {}, False
        try:
            if not self.expires_at - 120 <= self.clock() <= self.expires_at:
                raise BackendError('setup_review_expired')
            self.fresh_check()
            if self.inspector.inspect(self.payload) != self.review or self.review is None:
                raise BackendError('setup_target_changed')
            for path, data, digest in self.payload.rows:
                stream = os.fdopen(os.memfd_create('gamesir-reviewed-helper',
                    os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING), 'w+b')
                handles[path] = stream
                stream.write(data); stream.flush(); stream.seek(0)
                fcntl.fcntl(stream.fileno(), fcntl.F_ADD_SEALS, SEALS)
            for path, bits in self.review.directories:
                # No -p: exclusive creation reserves the helper path and stops
                # another setup instance without adopting existing directories.
                possible = True
                self.runner((*SUDO, '/usr/bin/mkdir', '-m', format(bits, '04o'), '--', path))
            # Authentication can outlive the initial snapshot. Root helper
            # setup takes no ALPM lock, so changes are checked again instead
            # of silently installing against a changed runtime/host.
            self.fresh_check()
            for path in [p for p in TARGETS if p != POLICY] + [POLICY]:
                if self.inspector.target.exists(path):
                    raise BackendError('setup_target_changed')
                self.runner((*SUDO, '/usr/bin/install', '-o', 'root', '-g', 'root',
                    '-m', format(mode(path), '04o'), '--', '/dev/stdin', path), handles[path])
            self.fresh_check()
            # Allow only a bounded read-only policy-watch delay, no setup retry.
            until = time.monotonic() + 3
            while True:
                try:
                    if self.inspector.inspect(self.payload) is not None:
                        raise BackendError('setup_postcheck_failed')
                    break
                except BackendError as error:
                    if error.code != 'setup_policy_unconfirmed' or time.monotonic() >= until:
                        raise
                    time.sleep(0.1)
            self.outcome = SetupResult('verified_setup', changes_possible=True)
        except (BackendError, AuthorizationError, SetupCommandError) as error:
            self.outcome = SetupResult('uncertain' if possible else 'blocked', error.code, possible)
        except Exception:
            self.outcome = SetupResult('uncertain' if possible else 'blocked', 'setup_failed', possible)
        finally:
            for stream in handles.values(): stream.close()
        return self.outcome
