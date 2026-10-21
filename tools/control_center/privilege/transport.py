# SPDX-License-Identifier: GPL-2.0-only
"""Prepared fixed pkexec transport. Never constructed by the ordinary GUI.

Only the installed authorization-only helper can be called. There is no package
executor. A future separately approved test needs reviewed pins and installation.
"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import selectors
import stat
import subprocess
import time

from .protocol import ARGV, FILES, HEX, AuthorizationError, Probe


@dataclass(frozen=True)
class HelperPins:
    # Supplied by an independent maintainer review, not auto-loaded from a
    # package, user-selected path or the staging manifest's self-checksums.
    files: tuple

    def validate(self):
        if (type(self.files) is not tuple or len(self.files) != len(FILES)
                or any(type(row) is not tuple or len(row) != 2
                       or type(row[0]) is not str or type(row[1]) is not str
                       or not HEX.fullmatch(row[1]) for row in self.files)
                or {p for p, _ in self.files} != set(FILES)):
            raise AuthorizationError('unreviewed_authorization_helper')


class InstalledAuditor:
    def inspect(self, path, expected=None, *, executable=False):
        path = Path(path)
        try:
            for ancestor in path.parents:
                info = ancestor.lstat()
                if (not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022):
                    raise AuthorizationError('unsafe_authorization_installation')
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022
                        or executable and not info.st_mode & 0o111):
                    raise AuthorizationError('unsafe_authorization_installation')
                if expected is not None:
                    data = stream.read(256 * 1024 + 1)
                    if len(data) > 256 * 1024 or hashlib.sha256(data).hexdigest() != expected:
                        raise AuthorizationError('authorization_helper_changed')
        except OSError as error:
            raise AuthorizationError('authorization_helper_unavailable') from error


@dataclass(frozen=True)
class Reply:
    state: str
    returncode: int = -1
    stdout: bytes = b''


class BoundedRunner:
    def __init__(self, *, timeout=120.0):
        if type(timeout) not in (int, float) or not 0 < timeout <= 120:
            raise ValueError('Invalid authorization timeout')
        self.timeout = timeout

    def stop(self, child, state):
        try:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=0.5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                child.kill()
                child.wait(timeout=0.5)
            except (OSError, subprocess.TimeoutExpired):
                # A setuid/root child may no longer be signalable by this user.
                # Do not claim it stopped; this fixed helper cannot modify packages.
                return Reply('completion_unknown')
        return Reply(state)

    def invoke(self, data, *, cancelled):
        Probe.parse(data)  # Strict small request before creating any process.
        if cancelled():
            return Reply('cancelled')
        environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
        child = subprocess.Popen(ARGV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=environment, shell=False,
                                 close_fds=True, start_new_session=True)
        try:
            # <= 2048 bytes fits in a fresh Linux pipe; never feed passwords.
            try:
                child.stdin.write(data)
                child.stdin.close()
            except BrokenPipeError:
                pass  # Agent cancellation can close stdin before reading it.
            output, errors = bytearray(), bytearray()
            deadline = time.monotonic() + self.timeout
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ, output)
                selector.register(child.stderr, selectors.EVENT_READ, errors)
                while selector.get_map() or child.poll() is None:
                    if cancelled():
                        return self.stop(child, 'cancelled')
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return self.stop(child, 'timeout')
                    for key, _ in selector.select(min(remaining, 0.05)):
                        data = os.read(key.fd, 4096)
                        if not data:
                            selector.unregister(key.fileobj)
                            continue
                        key.data.extend(data)
                        if len(output) > 2048 or len(errors) > 4096:
                            return self.stop(child, 'output_limit')
            return Reply('complete', child.wait(timeout=0.5), bytes(output))
        except Exception:
            return self.stop(child, 'transport_failed')
        finally:
            # No error text or credential is retained or returned.
            for stream in (child.stdin, child.stdout, child.stderr):
                try:
                    stream.close()
                except OSError:
                    pass


class PkexecTransport:
    def __init__(self, pins, *, auditor=None, runner=None):
        if not isinstance(pins, HelperPins):
            raise AuthorizationError('unreviewed_authorization_helper')
        pins.validate()
        self.pins = pins
        self.auditor = auditor if auditor is not None else InstalledAuditor()
        self.runner = runner if runner is not None else BoundedRunner()

    def invoke(self, data, *, cancelled):
        Probe.parse(data)
        if cancelled():
            return Reply('cancelled')
        # No generic pkexec fallback if our exact reviewed policy/helper is absent.
        self.auditor.inspect(ARGV[0], executable=True)
        for path, expected in self.pins.files:
            self.auditor.inspect(path, expected, executable=path == ARGV[2])
        return self.runner.invoke(data, cancelled=cancelled)
