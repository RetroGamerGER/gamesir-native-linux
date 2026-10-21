# SPDX-License-Identifier: GPL-2.0-only
"""Root-side authorization probe. No package/device/process/system operations.

PKEXEC_UID correlates an already privileged invocation; it cannot by itself
authenticate a caller. The root-owned entry and Polkit enforce that boundary.
"""
import os
import selectors
import sys
import time

from .protocol import AuthorizationError, LIMIT, Probe, acknowledgement


def answer(data, *, effective_uid, invoking_uid):
    if effective_uid != 0:
        raise AuthorizationError('privileged_helper_required')
    if (type(invoking_uid) is not str or not invoking_uid.isascii()
            or not invoking_uid.isdigit() or len(invoking_uid) > 10
            or not 0 < int(invoking_uid) < 0xffffffff):
        raise AuthorizationError('invalid_pkexec_caller')
    return acknowledgement(Probe.parse(data))


def bounded_input(fd, *, seconds=5):
    data = bytearray()
    deadline = time.monotonic() + seconds
    with selectors.DefaultSelector() as selector:
        selector.register(fd, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise AuthorizationError('helper_input_timeout')
            block = os.read(fd, LIMIT + 1 - len(data))
            if not block:
                return bytes(data)
            data.extend(block)
            if len(data) > LIMIT:
                raise AuthorizationError('authorization_message_limit')


def main():
    # Never turn argv into commands, paths or package-manager switches.
    try:
        if len(sys.argv) != 1:
            raise AuthorizationError('helper_arguments_refused')
        if os.geteuid() != 0:
            raise AuthorizationError('privileged_helper_required')
        data = bounded_input(sys.stdin.fileno())
        output = answer(data, effective_uid=os.geteuid(), invoking_uid=os.environ.get('PKEXEC_UID'))
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()
        return 0
    except (AuthorizationError, OSError):
        # No raw stderr, request data, username or password in the protocol.
        return 2
