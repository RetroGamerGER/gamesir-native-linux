# SPDX-License-Identifier: GPL-2.0-only
"""Fixed package entry body. Not used by the installed authorization-only probe."""
import os
from pathlib import Path
import selectors
import sys
import tempfile
import time

from artifacts import BackendError
from backend import Outcome
from package_execution import PackageExecutor
from package_catalog import load_installed_catalog, ReleaseResolver, CatalogState, STATE
from package_wire import parse_message, receipt


class Input:
    def __init__(self, fd):
        self.fd, self.deadline = fd, time.monotonic() + 90

    def exact(self, size):
        result = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(self.fd, selectors.EVENT_READ)
            while len(result) < size:
                remaining = self.deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise BackendError('package_input_timeout')
                data = os.read(self.fd, min(65536, size - len(result)))
                if not data:
                    raise BackendError('incomplete_package_message')
                result.extend(data)
        return bytes(result)

    def eof(self):
        with selectors.DefaultSelector() as selector:
            selector.register(self.fd, selectors.EVENT_READ)
            remaining = self.deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining) or os.read(self.fd, 1):
                raise BackendError('trailing_package_input')


def main():
    # The protected entry checked isolated Python and all installed modules.
    caller = os.environ.get('PKEXEC_UID', '')
    if (os.geteuid() != 0 or len(sys.argv) != 1 or not caller.isascii()
            or not caller.isdigit() or len(caller) > 10 or not 0 < int(caller) < 0xffffffff):
        return 2
    message, result_fd = None, None
    try:
        trust = load_installed_catalog()  # Fixed root-owned data, never GUI input.
        resolver = ReleaseResolver(trust, CatalogState(STATE))
        source = Input(sys.stdin.fileno())
        message = parse_message(source.exact, trust, resolver=resolver.resolve)
        trust = resolver.trust
        source.eof()
        # Empty deployment trust is deliberately not an installer approval.
        if not trust.catalog.records and not trust.installed:
            raise BackendError('no_reviewed_deployment')
        from package_host import SystemPackages, protected, CACHE
        protected(CACHE, directory=True)
        # Capture all hook/native child stdout/stderr in a private root log.
        # Otherwise a hook could corrupt or forge the GUI's JSON receipt.
        result_fd = os.dup(sys.stdout.fileno())
        log_fd, _ = tempfile.mkstemp(prefix='package-log-', dir=CACHE)
        os.dup2(log_fd, 1)
        os.dup2(log_fd, 2)
        os.close(log_fd)
        try:
            adapter = SystemPackages(message.plan.request)
            outcome = PackageExecutor(trust, adapter, release_guard=resolver).run(message.plan)
        except BackendError as error:
            outcome = Outcome('blocked', 'privileged_setup', error.code)
        except Exception:
            outcome = Outcome('blocked', 'privileged_setup', 'package_adapter_failure')
        data = receipt(message, outcome)
        with os.fdopen(result_fd, 'wb', closefd=True) as output:
            result_fd = None
            output.write(data)
            output.flush()
        return 0
    except (BackendError, OSError, ValueError):
        # No raw request, private paths or credentials in public output.
        return 2
    finally:
        if result_fd is not None:
            os.close(result_fd)


if __name__ == '__main__':
    raise SystemExit(main())
