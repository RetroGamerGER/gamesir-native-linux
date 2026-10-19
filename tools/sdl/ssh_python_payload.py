#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build, never execute, the reviewed metadata check's SSH command.

POSIX shlex.quote does not preserve arbitrary Python source through Fish.
Only an ASCII Base64 token enters the fixed shell-quoted bootstrap below.
Encoding is neither encryption nor a read-only sandbox: callers must review
the source, obtain approval and retain source hashes/one-attempt guards.
This module performs no SSH, sudo, authentication, discovery or device I/O.
"""
import base64

MAX_SOURCE_BYTES = 65536
PASSWORD_MARKER = 'GAMESIR_GUIDE_READ_PASSWORD:'


def python_bootstrap(source):
    """Preserve UTF-8 source bytes; reject invalid/oversized source locally."""
    if not isinstance(source, str):
        raise TypeError('Reviewed Python source must be text')
    data = source.encode('utf-8')
    if not data or len(data) > MAX_SOURCE_BYTES:
        raise ValueError('Reviewed Python source size outside transport limit')
    compile(data, '<reviewed-ssh-check>', 'exec')  # Validate, do not execute.
    token = base64.b64encode(data).decode('ascii')
    return ('import base64;exec(compile(base64.b64decode("' + token +
            '",validate=True),"<reviewed-ssh-check>","exec"))')


def read_check_command(source):
    """Fixed metadata-check prefix, safe for Fish and POSIX shells.

The bootstrap has no single quote, backslash, newline, substitution or glob.
stdin is untouched: the caller uses it only for the approved sudo password.
No host, executable, prompt or shell fragment is accepted from the source.
"""
    bootstrap = python_bootstrap(source)
    return ('/usr/bin/env LC_ALL=C /usr/bin/sudo -S -p ' + PASSWORD_MARKER +
            " -- /usr/bin/python -B -c '" + bootstrap + "'")
