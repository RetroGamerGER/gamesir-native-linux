# SPDX-License-Identifier: GPL-2.0-only
"""GUI worker submission for a separately deployed package helper.

No default transport, credential reuse or production launch flag. The existing
authorization-only helper is intentionally insufficient for this interface.
"""
from dataclasses import dataclass, replace
import os
import selectors
import subprocess
import threading
import time

from artifacts import BackendError
from backend import Outcome, Session
from package_wire import ARGV, EXECUTOR, POLICY, PackageMessage, parse_receipt
from transactions import Transactions

MODULES = ('artifacts.py', 'backend.py', 'package_execution.py', 'package_wire.py',
           'package_host.py', 'package_alpm.py', 'package_helper.py', 'package_catalog.py',
           'REVIEWED_PACKAGES.json', 'alpm_bridge.so')
FILES = (EXECUTOR, POLICY, *(EXECUTOR.rsplit('/', 1)[0] + '/' + name for name in MODULES))


class PackageTransport:
    def __init__(self, pins, *, auditor=None, deadline=1200):
        # Explicit independent review pins required, never taken from a staging
        # manifest. No defaults or acceptance of authorization-only helper pins.
        from artifacts import HEX
        if (type(pins) is not tuple or len(pins) != len(FILES)
                or any(type(row) is not tuple or len(row) != 2
                       or type(row[0]) is not str or type(row[1]) is not str
                       or not HEX.fullmatch(row[1]) for row in pins)
                or {p for p, _ in pins} != set(FILES)):
            raise BackendError('unreviewed_package_helper')
        if type(deadline) not in (int, float) or not 1 <= deadline <= 3600:
            raise BackendError('invalid_package_deadline')
        from privilege.transport import InstalledAuditor
        self.pins, self.deadline = pins, deadline
        self.auditor = auditor if auditor is not None else InstalledAuditor()

    @staticmethod
    def reap(child):
        # Do not kill a package manager or close its stdout while hooks run.
        # On a lost result retain uncertainty, drain pipes and reap later.
        def drain(stream):
            try:
                while os.read(stream.fileno(), 65536):
                    pass
            except OSError:
                pass
            finally:
                stream.close()
        for stream in (child.stdout, child.stderr):
            os.set_blocking(stream.fileno(), True)
            threading.Thread(target=drain, args=(stream,), daemon=True).start()
        threading.Thread(target=child.wait, daemon=True).start()

    def invoke(self, message):
        # Returns (returncode, receipt); None means started completion unknown.
        # Only an agent's 126/127 is a pre-execution cancellation/denial.
        try:
            self.auditor.inspect(ARGV[0], executable=True)
            for path, expected in self.pins:
                self.auditor.inspect(path, expected, executable=path == EXECUTOR)
        except Exception:
            raise BackendError('package_helper_attestation_failed') from None
        environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
        # Materialize/check header before spawning; payloads are immutable bytes.
        chunks = iter(tuple(message.chunks()))
        child = subprocess.Popen(ARGV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=environment, shell=False,
                                 close_fds=True, start_new_session=True)
        detached = False
        try:
            for stream in (child.stdin, child.stdout, child.stderr):
                os.set_blocking(stream.fileno(), False)
            output, errors, pending = bytearray(), 0, memoryview(next(chunks))
            end = time.monotonic() + self.deadline
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdin, selectors.EVENT_WRITE, 'input')
                selector.register(child.stdout, selectors.EVENT_READ, 'output')
                selector.register(child.stderr, selectors.EVENT_READ, 'error')
                while selector.get_map() or child.poll() is None:
                    if time.monotonic() >= end:
                        detached = True
                        break
                    for key, _ in selector.select(0.05):
                        if key.data == 'input':
                            try:
                                size = os.write(key.fd, pending[:65536])
                                pending = pending[size:]
                                if not pending:
                                    pending = memoryview(next(chunks))
                            except BlockingIOError:
                                continue
                            except (StopIteration, BrokenPipeError):
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            try:
                                block = os.read(key.fd, 65536)
                            except BlockingIOError:
                                continue
                            if not block:
                                selector.unregister(key.fileobj)
                            elif key.data == 'output':
                                output.extend(block)
                            else:
                                errors += len(block)  # Never retain raw stderr.
                            if len(output) > 4096 or errors > 65536:
                                detached = True
                                break
                    if detached:
                        break
            if detached:
                return None, b''
            return child.wait(), bytes(output)
        except Exception:
            detached = True
            return None, b''
        finally:
            if not child.stdin.closed:
                child.stdin.close()
            if detached:
                self.reap(child)
            else:
                child.stdout.close(); child.stderr.close()


class ExecutionSession:
    def __init__(self, plan, transport, clock):
        self.plan, self.transport, self.clock = plan, transport, clock
        self.used = False
        self.outcome = None

    def cancel(self):
        if not self.used:
            self.used = True
            self.outcome = Outcome('cancelled', 'confirmation')
        return self.outcome

    def run(self):
        if self.used:
            return self.outcome
        self.used = True
        launched = False
        try:
            Session(self.plan).check_time(self.clock())
            if self.transport is None:
                raise BackendError('package_transport_disabled')
            message = PackageMessage.create(self.plan, getattr(self.transport, 'release_catalog', None))
            launched = True
            code, data = self.transport.invoke(message)
            if code in (126, 127):
                self.outcome = (Outcome('cancelled', 'authorization') if code == 126 else
                                Outcome('blocked', 'authorization', 'package_authorization_denied'))
            elif code == 0:
                self.outcome = parse_receipt(data, message)
            else:
                self.outcome = Outcome('uncertain', 'package_result',
                                       'package_completion_unknown', changes_possible=True)
        except BackendError as error:
            # An attestation/pre-spawn error guarantees no child; malformed
            # output after spawn cannot establish that hooks did not run.
            known_before = error.code in ('package_helper_attestation_failed', 'plan_expired',
                                           'package_transport_disabled', 'package_message_limit')
            possible = launched and not known_before
            self.outcome = Outcome('uncertain' if possible else 'blocked', 'package_result',
                                   error.code, possible)
        except Exception:
            self.outcome = Outcome('uncertain' if launched else 'blocked', 'package_result',
                                   'package_transport_failure', launched)
        return self.outcome


@dataclass(frozen=True)
class ExecutionSubmission:
    session: ExecutionSession

    def run(self):
        return self.session.run()


class ExecutionTransactions(Transactions):
    """Explicit injected GUI coordinator; never constructed by normal launch.

    observe() must use the matching authoritative planning reader, not a Phase-B
    snapshot. Helper re-observes and compares independently under ALPM lock.
    """
    simulated = False

    def __init__(self, observer, catalog, blobs, clock, *, transport=None):
        super().__init__(observer, catalog, blobs, clock)
        self.transport = transport

    @property
    def uncertain(self):
        # Even a verified package result invalidates the GUI's earlier status
        # and planning snapshot. Require a separately refreshed session.
        return self.outcome is not None and self.outcome.changes_possible

    def request(self, operation):
        if self.transport is None:
            self.error = 'package_transport_disabled'
            return False
        return super().request(operation)

    def prepare(self):
        if not super().prepare():
            return False
        self.session = ExecutionSession(replace(self.session.plan, purpose='packages'), self.transport, self.clock)
        return True

    def begin(self):
        if self.state != 'review' or self.session is None:
            return None
        self.state = 'running'
        return ExecutionSubmission(self.session)
