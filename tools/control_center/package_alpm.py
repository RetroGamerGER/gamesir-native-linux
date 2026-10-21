# SPDX-License-Identifier: GPL-2.0-only
"""Narrow local ALPM adapter. Loading/locking is explicit, never on import.

Production must use independently installed protected bridge/cache/config.
Offline tests use a compiled bridge and a temporary empty root/database only.
"""
import ctypes as C
import os
from pathlib import Path
import tempfile

from artifacts import BackendError, COMPONENTS
from backend import TransactionPreview


def version_compare(left, right):
    """Use ALPM's own version ordering without opening a package database."""
    from artifacts import VERSION
    from package_host import protected
    if any(type(v) is not str or not VERSION.fullmatch(v) for v in (left, right)):
        raise BackendError('invalid_release_version')
    library = protected(Path('/usr/lib/libalpm.so').resolve(strict=True))
    function = C.CDLL(str(library)).alpm_pkg_vercmp
    function.argtypes, function.restype = (C.c_char_p, C.c_char_p), C.c_int
    return function(left.encode('ascii'), right.encode('ascii'))


class Alpm:
    def __init__(self, library, root, database, hookdirs):
        self.lib = C.CDLL(str(library))
        self.ctx = None
        self.cache = None
        for name, args, result in (
                ('open', [C.c_char_p, C.c_char_p], C.c_void_p),
                ('hookdir', [C.c_void_p, C.c_char_p], C.c_int),
                ('option', [C.c_void_p, C.c_char_p, C.c_char_p], C.c_int),
                ('scriptlet', [C.c_void_p, C.c_char_p], C.c_int),
                ('lock', [C.c_void_p], C.c_int),
                ('add', [C.c_void_p, C.c_char_p], C.c_int),
                ('remove', [C.c_void_p, C.c_char_p], C.c_int),
                ('prepare', [C.c_void_p], C.c_int),
                ('commit', [C.c_void_p], C.c_int),
                ('error', [C.c_void_p], C.c_char_p),
                ('rows', [C.c_void_p, C.c_int], C.c_void_p),
                ('next', [C.c_void_p], C.c_void_p),
                ('name', [C.c_void_p], C.c_char_p),
                ('version', [C.c_void_p], C.c_char_p),
                ('close', [C.c_void_p], C.c_int)):
            fn = getattr(self.lib, 'gs_alpm_' + name)
            fn.argtypes, fn.restype = args, result
        self.ctx = self.lib.gs_alpm_open(os.fsencode(root), os.fsencode(database))
        if not self.ctx:
            raise BackendError('package_database_unavailable')
        try:
            for path in hookdirs:
                self.call('hookdir', os.fsencode(path))
        except Exception:
            self.close()
            raise

    def call(self, name, *args):
        if not self.ctx or getattr(self.lib, 'gs_alpm_' + name)(self.ctx, *args) != 0:
            # Private chained diagnosis only; public outcome keeps stable code.
            detail = self.lib.gs_alpm_error(self.ctx) if self.ctx else b'closed'
            raise BackendError('alpm_' + name + '_failed') from RuntimeError(detail)

    def acquire(self):
        self.call('lock')  # Native ALPM lock, no advisory lock/unlink retry.

    def rows(self, kind=0):
        if not self.ctx:
            raise BackendError('package_database_closed')
        node, result = self.lib.gs_alpm_rows(self.ctx, kind), []
        while node:
            if len(result) >= 50000:
                raise BackendError('package_database_limit')
            result.append((self.lib.gs_alpm_name(node).decode('ascii'),
                           self.lib.gs_alpm_version(node).decode('ascii')))
            node = self.lib.gs_alpm_next(node)
        return tuple(sorted(result))

    def prepare(self, plan, cache_parent):
        if plan.request.operation == 'install':
            # Caller has independently verified all bytes. Private unique cache
            # is held through commit, never a client path or shared /tmp name.
            self.cache = tempfile.TemporaryDirectory(prefix='transaction-', dir=cache_parent)
            os.chmod(self.cache.name, 0o700)
            for artifact in plan.artifacts:
                path = Path(self.cache.name) / (artifact.review.digest + '.pkg.tar')
                with path.open('xb') as stream:
                    stream.write(artifact.data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(path, 0o600)
                self.call('add', os.fsencode(path))
        else:
            for component in plan.request.components:
                self.call('remove', COMPONENTS[component][0].encode('ascii'))
        self.call('prepare')
        additions, removals = self.rows(1), self.rows(2)
        packages = tuple(sorted(name for name, _ in
                                (additions if plan.request.operation == 'install' else removals)))
        return TransactionPreview(packages, additions,
                                  other_removals=tuple(name for name, _ in removals))

    def commit(self):
        self.call('commit')

    def close(self):
        result = 0
        if self.ctx:
            ctx, self.ctx = self.ctx, None
            result = self.lib.gs_alpm_close(ctx)
        try:
            if self.cache is not None:
                cache, self.cache = self.cache, None
                cache.cleanup()
        finally:
            if result:
                raise BackendError('package_lock_release_unverified')
