# SPDX-License-Identifier: GPL-2.0-only
"""Explicit maintainer migration, not automatic first-run repair.

Only fixed mkdir/install/mv/find system tools may run privileged. Sources are
sealed before authentication. No package/driver action, deletion or state reset.
"""
from dataclasses import dataclass
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import threading
import time

from artifacts import BackendError
from helper_setup import (BASE, PARENT, COPYING, CACHE, POLICY, TARGETS, SUDO, SEALS,
                          ENV, SetupPayload, FixedTarget, SetupCommandError, mode)
from package_wire import EXECUTOR
from privilege.protocol import AuthorizationError

CANDIDATE = PARENT + '/.package-executor-signed-v1'
BACKUP = PARENT + '/.package-executor-before-signed-v1'
FAILED = PARENT + '/.package-executor-retained-signed-v1'
HOLD = POLICY + '.before-signed-v1'
STATE_QUERY = (*SUDO, '/usr/bin/find', '--', CACHE, '-maxdepth', '1', '-mindepth', '1',
               '-name', 'release-catalog.json', '-printf', '%f\n')
MOVES = ((POLICY, HOLD), (BASE, BACKUP), (CANDIDATE, BASE), (HOLD, POLICY),
         (BASE, FAILED), (BACKUP, BASE))


def translated(path, base):
    return base + path[len(BASE):] if path.startswith(BASE + '/') else path


def validate_command(argv, source):
    if type(argv) is not tuple or argv[:len(SUDO)] != SUDO:
        raise SetupCommandError('invalid_migration_command')
    tail = argv[len(SUDO):]
    if argv == STATE_QUERY and source is None: return
    if tail == ('/usr/bin/mkdir', '-m', '0755', '--', CANDIDATE) and source is None: return
    if (len(tail) == 7 and tail[:5] == ('/usr/bin/mv', '-T', '--no-copy', '--no-clobber', '--')
            and (tail[-2], tail[-1]) in MOVES and source is None): return
    for target in TARGETS:
        if not target.startswith(BASE + '/'): continue
        if (tail == ('/usr/bin/install', '-o', 'root', '-g', 'root', '-m',
                     format(mode(target), '04o'), '--', '/dev/stdin', translated(target, CANDIDATE))
                and source is not None
                and fcntl.fcntl(source.fileno(), fcntl.F_GET_SEALS) & SEALS == SEALS): return
    raise SetupCommandError('invalid_migration_command')


class MigrationRunner:
    def __call__(self, argv, source=None):
        validate_command(argv, source)
        env = {k: os.environ[k] for k in ('HOME', 'DISPLAY', 'WAYLAND_DISPLAY',
            'DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR', 'XAUTHORITY',
            'KDE_FULL_SESSION', 'KDE_SESSION_VERSION') if k in os.environ}
        env.update(ENV, SUDO_ASKPASS='/usr/bin/ksshaskpass')
        # The only privileged stdout retained is a fixed filename existence
        # query. Never read cached catalog/log contents or raw sudo errors.
        child = subprocess.Popen(argv, stdin=source if source is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE if argv == STATE_QUERY else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True, shell=False, env=env)
        try:
            if argv == STATE_QUERY:
                output, _ = child.communicate(timeout=120)
                if len(output) > 4096: raise SetupCommandError('migration_query_limit')
            else:
                child.wait(timeout=120); output = b''
        except subprocess.TimeoutExpired:
            # Do not kill or assume a privileged child stopped. No next command.
            threading.Thread(target=child.communicate, daemon=True).start()
            raise SetupCommandError('migration_completion_unknown') from None
        if child.returncode: raise SetupCommandError('migration_command_failed')
        return output


class MigrationTarget(FixedTarget):
    def snapshot(self, path, directory=False):
        self.directory(path) if directory else self.file_parent(path)
        s = Path(path).lstat()
        if (s.st_uid != 0 or s.st_gid != 0 or s.st_mode & 0o022
                or not directory and (not stat.S_ISREG(s.st_mode) or s.st_nlink != 1)):
            raise BackendError('migration_unsafe_target')
        return (s.st_dev, s.st_ino, s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode), s.st_mtime_ns)

    def file_parent(self, path):
        from package_host import protected
        protected(path)

    def children(self, path):
        self.directory(path, 0o755)
        return frozenset(p.name for p in Path(path).iterdir())

    def quiet(self):
        if os.path.lexists('/var/lib/pacman/db.lck'):
            raise BackendError('migration_package_database_busy')
        # Read root process argv only into memory to establish quiescence;
        # retain neither raw argv (potential unrelated secrets) nor PID logs.
        for p in Path('/proc').iterdir():
            if not p.name.isdecimal(): continue
            try:
                if p.stat().st_uid != 0: continue
                with (p/'cmdline').open('rb') as stream: data = stream.read(262145)
            except FileNotFoundError:
                continue  # Exited process, not proof of a surviving invocation.
            except OSError:
                raise BackendError('migration_process_visibility_unknown') from None
            if len(data) > 262144: raise BackendError('migration_process_visibility_unknown')
            if EXECUTOR.encode() in data.split(b'\x00'):
                raise BackendError('migration_helper_running')

    def migration_tools(self):
        self.prerequisites()
        from package_host import protected
        for name in ('/usr/bin/mv', '/usr/bin/find'): protected(name)
        code, output, _ = self.query(['/usr/bin/mv', '--help'])
        if code or '--no-copy' not in output or '--no-clobber' not in output:
            raise BackendError('migration_required_mv_options_missing')
        # A multi-path query counts failed lookups (13 unowned paths returned
        # 13 on the reviewed host), not simply 1. Check each fixed path alone
        # instead of assuming one aggregate status or accepting any failure.
        for path in TARGETS:
            code, output, errors = self.query(['/usr/bin/pacman', '-Qoq', '--', path])
            if code != 1 or output or errors.splitlines() != ['error: No package owns ' + path]:
                raise BackendError('migration_package_managed_or_unknown_helper')


@dataclass(frozen=True)
class MigrationSpec:
    old: tuple
    payload: SetupPayload
    distribution: str = 'garuda'

    def validate(self):
        self.payload.validate()
        if self.distribution not in ('garuda', 'cachyos'):
            raise BackendError('migration_target_mismatch')
        if (type(self.old) is not tuple or len(self.old) != len(TARGETS)
                or {p for p, h in self.old} != set(TARGETS)
                or any(type(h) is not str or len(h) != 64 or any(c not in '0123456789abcdef' for c in h)
                       for p, h in self.old)):
            raise BackendError('invalid_migration_review')
        old = dict(self.old); new = {p:h for p,d,h in self.payload.rows}
        for p in (POLICY, COPYING, EXECUTOR):
            if old[p] != new[p]: raise BackendError('migration_authorization_or_entry_changed')
        if old == new: raise BackendError('migration_not_needed')

    def installs(self):
        self.validate()
        rows = []
        for p, data, digest in self.payload.rows:
            if p.startswith(BASE + '/'):
                rows.append(((*SUDO, '/usr/bin/install', '-o', 'root', '-g', 'root', '-m',
                    format(mode(p), '04o'), '--', '/dev/stdin', translated(p, CANDIDATE)), p))
        return tuple(rows)

    def commands(self):
        moves = [((*SUDO, '/usr/bin/mv', '-T', '--no-copy', '--no-clobber', '--', src, dst), None)
                 for src, dst in MOVES[:4]]
        return ((STATE_QUERY, None),
                ((*SUDO, '/usr/bin/mkdir', '-m', '0755', '--', CANDIDATE), None),
                *self.installs(), moves[0], (STATE_QUERY, None), moves[1], moves[2],
                (STATE_QUERY, None), moves[3])


@dataclass(frozen=True)
class MigrationResult:
    state: str
    phase: str
    error: str = ''
    changes_possible: bool = False


class MigrationSession:
    def __init__(self, spec, *, target=None, runner=None, fresh_check=lambda:None, rollback=False):
        spec.validate(); self.spec = spec
        self.target = MigrationTarget() if target is None else target
        self.runner = MigrationRunner() if runner is None else runner
        self.fresh_check, self.rollback = fresh_check, rollback
        self.used, self.outcome = False, None
        self.phase, self.possible = 'unstarted', False

    def files(self, rows, base=BASE, held=False):
        t = self.target
        for path, digest in rows:
            destination = HOLD if held and path == POLICY else translated(path, base)
            t.file(destination, digest, mode(path)); t.snapshot(destination)
        names = frozenset(Path(p).name for p,h in rows if p.startswith(BASE + '/'))
        if t.children(base) != names: raise BackendError('migration_unexpected_executor_entry')

    def state_absent(self):
        if self.runner(STATE_QUERY): raise BackendError('migration_signed_state_present')

    def move(self, src, dst):
        if self.target.exists(dst): raise BackendError('migration_destination_exists')
        if self.target.snapshot(src, directory=src in (BASE, BACKUP, CANDIDATE))[0] != self.target.snapshot(
                str(Path(dst).parent), directory=True)[0]:
            raise BackendError('migration_cross_filesystem')
        self.possible = True
        self.runner((*SUDO, '/usr/bin/mv', '-T', '--no-copy', '--no-clobber', '--', src, dst))
        if self.target.exists(src) or not self.target.exists(dst):
            raise BackendError('migration_rename_unconfirmed')

    def policy(self, installed):
        end = time.monotonic() + 3
        while True:
            try:
                self.target.policy(installed); return
            except BackendError as error:
                if error.code not in ('setup_policy_unconfirmed', 'unexpected_setup_policy') or time.monotonic() >= end:
                    raise
                time.sleep(0.1)

    def preserved(self, baseline):
        for path, snapshot in baseline.items():
            if self.target.snapshot(path, directory=True) != snapshot:
                raise BackendError('migration_preserved_directory_changed')
        self.fresh_check(); self.target.quiet()

    def run(self):
        if self.used: return self.outcome
        self.used = True
        handles = {}
        try:
            t = self.target; self.phase = 'preflight'
            t.migration_tools(); self.fresh_check(); t.quiet()
            for path, bits in ((PARENT, 0o755), (CACHE, 0o700), (str(Path(COPYING).parent), 0o755)):
                t.directory(path, bits)
            baseline = {p:t.snapshot(p, directory=True) for p in (CACHE, str(Path(COPYING).parent))}
            new = tuple((p,h) for p,d,h in self.spec.payload.rows)
            if self.rollback:
                self.recover(new, baseline)
            else:
                self.files(self.spec.old); t.policy(True)
                for path in (CANDIDATE, BACKUP, FAILED, HOLD):
                    if t.exists(path): raise BackendError('migration_destination_exists')
                original = t.snapshot(BASE, directory=True)
                if (original[0] != t.snapshot(PARENT, directory=True)[0]
                        or t.snapshot(POLICY)[0] != t.snapshot(str(Path(POLICY).parent), directory=True)[0]):
                    raise BackendError('migration_cross_filesystem')
                for p, data, digest in self.spec.payload.rows:
                    if not p.startswith(BASE + '/'): continue
                    stream = os.fdopen(os.memfd_create('gamesir-migration-pinned',
                        os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING), 'w+b')
                    handles[p] = stream; stream.write(data); stream.flush(); stream.seek(0)
                    fcntl.fcntl(stream.fileno(), fcntl.F_ADD_SEALS, SEALS)
                self.state_absent()
                self.phase = 'candidate'; self.possible = True
                self.runner((*SUDO, '/usr/bin/mkdir', '-m', '0755', '--', CANDIDATE))
                for argv, source in self.spec.installs(): self.runner(argv, handles[source])
                self.files(new, CANDIDATE); self.files(self.spec.old)
                if t.snapshot(BASE, directory=True) != original: raise BackendError('migration_target_changed')
                self.preserved(baseline)
                self.phase = 'policy_held'; self.move(POLICY, HOLD); self.policy(False)
                self.preserved(baseline); self.state_absent(); self.files(self.spec.old, held=True)
                self.phase = 'old_saved'; self.move(BASE, BACKUP)
                if t.snapshot(BACKUP, directory=True) != original: raise BackendError('migration_backup_changed')
                self.files(self.spec.old, BACKUP, held=True)
                self.phase = 'new_placed'; self.move(CANDIDATE, BASE)
                self.files(new, held=True); self.preserved(baseline); self.state_absent()
                self.phase = 'policy_restored'; self.move(HOLD, POLICY); self.policy(True)
                self.files(new); self.preserved(baseline)
            self.outcome = MigrationResult('verified_rollback' if self.rollback else 'verified_migration',
                                           self.phase, changes_possible=self.possible)
        except (BackendError, AuthorizationError, SetupCommandError) as error:
            self.outcome = MigrationResult('uncertain' if self.possible else 'blocked', self.phase,
                                           error.code, self.possible)
        except Exception:
            self.outcome = MigrationResult('uncertain' if self.possible else 'blocked', self.phase,
                                           'migration_failed', self.possible)
        finally:
            for stream in handles.values(): stream.close()
        return self.outcome

    def recover(self, new, baseline):
        """Separate explicit recovery, never an automatic error handler."""
        t = self.target; self.phase = 'rollback_preflight'
        held = t.exists(HOLD)
        if held:
            if t.exists(POLICY): raise BackendError('migration_conflicting_policy')
            self.policy(False)
        else:
            t.policy(True)
        if not t.exists(BACKUP):
            # Failed before saving the old directory, or after restoring it
            # but before the last policy rename. No deletion of staged bytes.
            self.files(self.spec.old, held=held)
            if held:
                for path in (CANDIDATE, FAILED):
                    if t.exists(path): self.files(new, path, held=True)
            self.preserved(baseline); self.state_absent()
            if held:
                self.phase = 'rollback_old_policy_restored'; self.move(HOLD, POLICY); self.policy(True)
                self.files(self.spec.old); self.preserved(baseline)
            else:
                self.phase = 'rollback_old_unchanged'
            return
        # Verify complete old backup and exact new-or-absent active directory
        # before holding the policy. No guessing at modified/partial bytes.
        self.files(self.spec.old, BACKUP, held=held)
        active = t.exists(BASE)
        if t.exists(FAILED):
            if active:raise BackendError('migration_conflicting_retained_new')
            self.files(new, FAILED, held=held)
        if active: self.files(new, held=held)
        original = t.snapshot(BACKUP, directory=True)
        self.state_absent()
        if not held:
            self.phase = 'rollback_policy_held'; self.move(POLICY, HOLD); self.policy(False)
        self.preserved(baseline); self.state_absent()
        if active:
            self.phase = 'new_retained'; self.move(BASE, FAILED)
        self.phase = 'old_restored'; self.move(BACKUP, BASE)
        if t.snapshot(BASE, directory=True) != original: raise BackendError('migration_backup_changed')
        self.files(self.spec.old, held=True); self.preserved(baseline); self.state_absent()
        self.phase = 'rollback_policy_restored'; self.move(HOLD, POLICY); self.policy(True)
        self.files(self.spec.old); self.preserved(baseline)
