# SPDX-License-Identifier: GPL-2.0-only
"""Metadata-only Gamescope selection for an explicitly approved diagnostic.

Importing this module does nothing. No executable is launched and no process
memory, environment, command line, input device or socket is opened. Presence
under the same UID does not establish display focus, seat or Steam ancestry.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import stat


class IdentityError(RuntimeError):
    pass


def require(ok, reason):
    if not ok:
        raise IdentityError(reason)


def _text(path):
    with path.open('r', encoding='utf-8') as stream:
        text = stream.read(65537)
    require(len(text) <= 65536, 'Oversized process metadata')
    return text


def _status(proc):
    fields = {}
    for line in _text(proc/'status').splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        require(key not in fields, 'Duplicate process status field')
        fields[key] = value.strip()
    parts = fields.get('Uid', '').split()
    require(len(parts) == 4 and all(p.isascii() and p.isdecimal() for p in parts),
            'Malformed process Uid quartet')
    return fields, tuple(int(p) for p in parts)


def _start(proc):
    raw = _text(proc/'stat')
    head, separator, tail = raw.rpartition(')')
    fields = tail.split()
    require(separator and head.split(' ', 1)[0] == proc.name and
            len(fields) >= 20 and fields[19].isascii() and fields[19].isdecimal(),
            'Malformed process start identity')
    require(fields[0] not in ('T', 't', 'X', 'Z'), 'Gamescope is stopped or exiting')
    return int(fields[19])


def _stamp(path):
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_mode & 0o111,
            'Expected a regular executable')
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


@dataclass(frozen=True)
class Identity:
    pid: int
    start_ticks: int
    uids: tuple
    executable: str
    stamp: tuple
    # comm/Name can change without exec or a credential change.
    name: str = field(compare=False)


def _snapshot(proc, uid, executable, stamp):
    start = _start(proc)
    fields, uids = _status(proc)
    require(uids == (uid,) * 4, 'Gamescope credentials differ from expected user')
    require(fields.get('TracerPid') == '0', 'Gamescope already has a tracer')
    state = fields.get('State', '').split()
    require(state and state[0] not in ('T', 't', 'X', 'Z'),
            'Gamescope is stopped or exiting')
    require(os.readlink(proc/'exe') == str(executable),
            'Gamescope executable path changed or deleted')
    require(_stamp(proc/'exe') == stamp and _stamp(executable) == stamp,
            'Gamescope executable backing file changed')
    require(_start(proc) == start, 'Gamescope PID was reused')
    return Identity(int(proc.name), start, uids, str(executable), stamp,
                    fields.get('Name', '')[:64])


def _stable_identity(proc, uid, executable, stamp):
    before = _snapshot(proc, uid, executable, stamp)
    require(_snapshot(proc, uid, executable, stamp) == before,
            'Gamescope identity changed during read')
    return before


def find_gamescope(uid, *, proc_root=Path('/proc'), executable=Path('/usr/bin/gamescope')):
    """Require exactly one stable executable owned wholly by the requested UID.

    A non-default proc root/executable is for offline fixtures. Only unrelated
    processes that genuinely disappear may be skipped. Inaccessible metadata
    for the requested user's processes stops selection instead of guessing.
    """
    require(type(uid) is int and uid > 0, 'Expected a non-root desktop UID')
    proc_root, executable = Path(proc_root), Path(executable)
    try:
        resolved = executable.resolve(strict=True)
        stamp = _stamp(resolved)
        candidates = []
        same_uid = named_only = vanished = 0
        for proc in sorted(proc_root.iterdir(), key=lambda p: p.name):
            if not proc.name.isascii() or not proc.name.isdecimal():
                continue
            selected = False
            try:
                fields, uids = _status(proc)
                if uid not in uids:
                    continue
                same_uid += 1
                link = os.readlink(proc/'exe')
                selected = link in (str(resolved), str(resolved) + ' (deleted)')
                if not selected:
                    named_only += fields.get('Name', '').startswith('gamescope')
                    continue
                candidates.append(_stable_identity(proc, uid, resolved, stamp))
            except (FileNotFoundError, ProcessLookupError):
                # An existing zombie has no exe either; do not silently treat
                # that or a missing selected process as a successful selection.
                if selected or proc.exists():
                    raise IdentityError(f'Process {proc.name} metadata disappeared; stop')
                vanished += 1
            except (OSError, UnicodeError) as error:
                raise IdentityError(f'Process {proc.name} metadata unavailable: '
                                    f'{type(error).__name__}; stop') from error
        require(len(candidates) == 1,
                f'Expected one Gamescope executable for UID {uid}; '
                f'matches={len(candidates)}, same_uid={same_uid}, '
                f'name_only={named_only}, vanished={vanished}; stop')
        chosen = candidates[0]
        require(_stable_identity(proc_root/str(chosen.pid), uid, resolved, stamp) == chosen,
                'Gamescope identity changed after selection')
        require(executable.resolve(strict=True) == resolved and _stamp(resolved) == stamp,
                'Configured Gamescope executable changed')
        return chosen
    except (OSError, UnicodeError) as error:
        raise IdentityError(f'Gamescope metadata unavailable: {type(error).__name__}; stop') from error


def verify_gamescope(identity, uid, **paths):
    """Rescan without adopting a replacement or accepting a second compositor."""
    require(find_gamescope(uid, **paths) == identity,
            'Gamescope identity changed since precheck; stop')
