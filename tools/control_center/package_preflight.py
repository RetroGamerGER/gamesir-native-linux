# SPDX-License-Identifier: GPL-2.0-only
"""Explicit unprivileged planning inspection. No ALPM handle, lock or activation.

Uses the exact same passive facts/fingerprint as the root executor, reading
the full installed inventory as data. Normal GUI status never invokes this.
"""
import os
from pathlib import Path
import re
import time

from artifacts import BackendError
from backend import Request
from package_host import SystemEvidence, protected, read


class FileInventory:
    def __init__(self, database=Path('/var/lib/pacman/local')):
        self.database = Path(database)

    def rows(self):
        # No library initialization, executable package metadata or DB writes.
        root = protected(self.database, directory=True)
        before = tuple(sorted(p.name for p in root.iterdir()))
        if len(before) > 50000:
            raise BackendError('package_database_limit')
        found = {}
        for name in before:
            if name == 'ALPM_DB_VERSION':
                continue
            if not re.fullmatch(r'[A-Za-z0-9@+_.:~\-]{1,300}', name):
                raise BackendError('invalid_package_database_entry')
            folder = protected(root / name, directory=True)
            path = protected(folder / 'desc')
            first = path.stat()
            metadata = read(path, 1024 * 1024)
            after = path.stat()
            if (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise BackendError('package_database_changed')
            fields = {}
            for block in metadata.split('\n\n'):
                parts = block.splitlines()
                if parts and parts[0] in ('%NAME%', '%VERSION%'):
                    if len(parts) != 2 or parts[0] in fields:
                        raise BackendError('invalid_package_metadata')
                    fields[parts[0]] = parts[1]
            if set(fields) != {'%NAME%', '%VERSION%'} or fields['%NAME%'] in found:
                raise BackendError('invalid_package_metadata')
            found[fields['%NAME%']] = fields['%VERSION%']
        if before != tuple(sorted(p.name for p in root.iterdir())):
            raise BackendError('package_database_changed')
        return tuple(sorted(found.items()))


class PlanningEvidence(SystemEvidence):
    def __init__(self, request, *, inventory=None, clock=time.monotonic):
        self.request = Request.parse({'schema': 1, 'operation': request.operation,
                                      'components': list(request.components)})
        self.clock, self.owns_lock = clock, False
        self.alpm = FileInventory() if inventory is None else inventory  # rows() only, no ALPM handle.
        self.config = self.configuration()
        if self.config['RootDir'] != '/' or self.config['DBPath'].rstrip('/') != '/var/lib/pacman':
            raise BackendError('unsupported_package_database')

    def collect(self):
        if os.geteuid() == 0:
            raise BackendError('desktop_user_required')
        first = self.observe()
        first.validate(self.clock())
        second = self.observe()
        second.validate(self.clock())
        if first.fingerprint() != second.fingerprint():
            raise BackendError('host_changed')
        return second
