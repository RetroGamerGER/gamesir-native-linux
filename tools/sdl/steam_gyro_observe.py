#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded, read-only SDL cache observation; never attaches a debugger.

Default/--help opens nothing. --precheck reads process/sysfs metadata only.
--observe additionally requires explicit approval and local GO before opening
one /proc/PID/mem O_RDONLY. No device opens, ptrace, signals or target calls.
This private diagnostic supports ONE pinned ELF32 SDL build, not a stable ABI.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import select
import stat
import struct
import sys
import time

SDL_SHA = '770801484962a75780b8eebed5e16b4f4735c1dbf422445af48764cff415ea97'
LIST_OFFSET = 0x3b3a00
FUNCTION_SLOT = 0x3aadec
FUNCTION_OFFSET = 0x221030
PHASES = ((30, 'prepare'), (10, 'rest'), (20, 'move'), (10, 'settle'))
MAX_SECONDS = sum(t for t, _ in PHASES)


class Halt(RuntimeError):
    pass


class BusySnapshot(Halt):
    pass


def require(condition, message):
    if not condition:
        raise Halt(message)


def u32(data, offset=0):
    return struct.unpack_from('<I', data, offset)[0]


def maps_parse(text):
    rows = []
    for line in text.splitlines():
        p = line.split(None, 5)
        require(len(p) >= 5, 'Malformed process map')
        start, end = (int(x, 16) for x in p[0].split('-'))
        rows.append((start, end, p[1], int(p[2], 16), p[3], int(p[4]), p[5] if len(p) == 6 else ''))
    return rows


def library_identity(rows):
    files = {x[6] for x in rows if 'libSDL3.so' in x[6]}
    require(len(files) == 1, 'Expected exactly one SDL3 library')
    path = Path(next(iter(files)))
    require(path.is_absolute() and path.is_file(), 'Missing/deleted SDL library')
    require(path.stat().st_size == 3911164, 'SDL file size not reviewed; stop')
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == SDL_SHA, 'SDL version not reviewed; stop')
    require(data[:6] == b'\x7fELF\x01\x01', 'Expected little-endian ELF32')
    info = path.stat()
    dev = f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}'
    own = [x for x in rows if x[6] == str(path)]
    require(all(x[4] == dev and x[5] == info.st_ino for x in own), 'Mapped/file identity differs')
    zero = [x for x in own if x[3] == 0]
    require(len(zero) == 1 and any('x' in x[2] for x in own), 'Ambiguous SDL load base')
    return zero[0][0], str(path), info.st_dev, info.st_ino


def process_identity(pid, uid):
    proc = Path('/proc') / str(pid)
    fields = dict(line.split(':', 1) for line in (proc/'status').read_text().splitlines() if ':' in line)
    require(all(int(x) == uid for x in fields['Uid'].split()), 'Unexpected process owner')
    require(fields['Name'].strip() == 'steam', 'Target is not Steam')
    require(fields['TracerPid'].strip() == '0', 'Steam already has a tracer')
    require(fields['State'].strip()[0] not in 'TtXZ', 'Steam is stopped or exiting')
    exe = (proc/'exe').resolve(strict=True)
    require(exe.name == 'steam' and exe.parent.name == 'ubuntu12_32', 'Unexpected Steam executable')
    # stat field 22; comm can contain spaces/parentheses.
    start = (proc/'stat').read_text().rsplit(')', 1)[1].split()[19]
    return pid, start, str(exe), uid


def find_steam(uid):
    candidates = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        try:
            if proc.stat().st_uid == uid and (proc/'comm').read_text().strip() == 'steam':
                candidates.append(int(proc.name))
        except FileNotFoundError:
            continue
    require(len(candidates) == 1, 'Expected exactly one Steam process owned by this user')
    process_identity(candidates[0], uid)
    return candidates[0]


def target_identity():
    found = {}
    for event in Path('/sys/class/input').glob('event*'):
        device = event/'device'
        try:
            name = (device/'name').read_text().strip()
        except FileNotFoundError:
            continue
        if name not in ('GameSir G7 Pro', 'GameSir G7 Pro Motion Sensors'):
            continue
        require(name not in found, 'More than one GameSir; no automatic selection')
        require((device/'id/vendor').read_text().strip() == '3537' and
                (device/'id/product').read_text().strip() == '109c', 'Unexpected GameSir ID')
        interface = next((p for p in device.resolve().parents if (p/'bInterfaceNumber').exists()), None)
        require(interface is not None, 'No USB interface parent')
        require((interface/'bInterfaceNumber').read_text().strip() == '00' and
                (interface/'driver').resolve(strict=True).name == 'gs_native', 'Not native IF0')
        node = Path('/dev/input')/event.name
        meta = node.stat()  # metadata only; no open()
        require(stat.S_ISCHR(meta.st_mode), 'Input node is not a character device')
        require((event/'dev').read_text().strip() == f'{os.major(meta.st_rdev)}:{os.minor(meta.st_rdev)}',
                'Input device-number mismatch')
        uniq = (device/'uniq').read_text().strip()
        require(bool(uniq), 'Missing paired session identity')
        found[name] = (str(node), str(interface), uniq, meta.st_rdev,
                       (interface.parent/'busnum').read_text().strip(),
                       (interface.parent/'devnum').read_text().strip())
    require(len(found) == 2, 'Expected native gamepad and gyro nodes')
    pad, sensor = found['GameSir G7 Pro'], found['GameSir G7 Pro Motion Sensors']
    require(pad[1:3] == sensor[1:3] and pad[4:] == sensor[4:], 'Unpaired native nodes')
    return pad, sensor


def descriptors(pid, target):
    counts = [0, 0]
    for fd in (Path('/proc')/str(pid)/'fd').iterdir():
        try:
            link = os.readlink(fd)
        except FileNotFoundError:
            continue
        for i in range(2):
            if link == target[i][0]:
                counts[i] += 1
    return {'gamepad_fds': counts[0], 'sensor_fds': counts[1]}


class Memory:
    def __init__(self, fd, rows):
        self.fd, self.rows, self.total = fd, rows, 0

    def read(self, address, size):
        require(0 < size <= 256 and 0x1000 <= address < 2**32-size, 'Invalid bounded memory read')
        require(any(a <= address and address+size <= b and 'r' in p for a,b,p,*_ in self.rows),
                'Pointer outside readable mapping')
        self.total += size
        require(self.total <= 4*1024*1024, 'Memory-read budget exceeded')
        data = os.pread(self.fd, size, address)
        require(len(data) == size, 'Short memory read')
        return data

    def string(self, address):
        # Read only through NUL; never dump the adjoining memory.
        value = bytearray()
        for offset in range(160):
            b = self.read(address+offset, 1)
            if b == b'\x00':
                return value.decode('utf-8', 'strict')
            value.extend(b)
        raise Halt('Unterminated SDL device path')


def snapshot(mem, base, pad_path):
    require(u32(mem.read(base+FUNCTION_SLOT, 4)) == base+FUNCTION_OFFSET,
            'Unexpected SDL dynamic API target')
    head = mem.read(base+LIST_OFFSET, 4)
    node, seen, matches = u32(head), set(), []
    while node:
        require(node not in seen and len(seen) < 16, 'Invalid/busy SDL joystick list')
        seen.add(node)
        ident = mem.read(node, 12)
        next_node = u32(mem.read(node+0x100, 4))
        path = mem.string(u32(ident, 8)) if u32(ident, 8) else ''
        if path == pad_path:
            metadata = mem.read(node+0x58, 12)
            count, enabled_count, sensors = struct.unpack('<III', metadata)
            require(0 < count <= 8 and enabled_count <= count, 'Invalid SDL sensor metadata')
            entries = mem.read(sensors, count*24)
            require(metadata == mem.read(node+0x58, 12) and ident == mem.read(node, 12),
                    'SDL metadata changed during read; stop')
            if entries != mem.read(sensors, count*24):
                raise BusySnapshot('SDL sensor values changed during snapshot')
            gyro = []
            for i in range(count):
                entry = entries[i*24:(i+1)*24]
                kind, enabled = u32(entry), entry[4]
                require(kind in range(1, 7) and enabled in (0, 1), 'Invalid SDL sensor entry')
                if kind == 2:
                    values = struct.unpack_from('<3f', entry, 12)
                    require(all(math.isfinite(v) and abs(v) <= 1000 for v in values), 'Invalid gyro values')
                    gyro.append({'enabled':bool(enabled), 'rad_s':values})
            require(len(gyro) == 1, 'Expected exactly one SDL gyro')
            matches.append((node, u32(ident), sensors, gyro[0]))
        node = next_node
    require(mem.read(base+LIST_OFFSET, 4) == head, 'SDL joystick list changed')
    require(len(matches) == 1, 'Expected exactly one matching SDL joystick')
    return matches[0]


def emit(event, **data):
    print(json.dumps({'event':event, 'monotonic_ns':time.monotonic_ns(), **data}), flush=True)


def cue(phase):
    messages = {
        'prepare':'30 Sekunden Vorbereitung: Steam-Gyroseite öffnen, NICHT Kalibrieren drücken.',
        'rest':'JETZT 10 Sekunden ruhig halten.',
        'move':'JETZT 20 Sekunden langsam in verschiedene Richtungen drehen; kein genauer Winkel nötig.',
        'settle':'Bewegungsphase vorbei. Ablegen; Rückbewegung ist jetzt erlaubt. Noch 10 Sekunden.',
    }
    print(messages[phase], file=sys.stderr, flush=True)
    emit('phase', phase=phase)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--precheck', action='store_true')
    mode.add_argument('--observe', action='store_true')
    args = parser.parse_args()
    uid = int(os.environ.get('SUDO_UID', os.getuid()))
    require(uid != 0, 'Run from the desktop user; sudo preserves SUDO_UID')
    pid = find_steam(uid)
    process = process_identity(pid, uid)
    target = target_identity()
    proc = Path('/proc')/str(pid)
    library = library_identity(maps_parse((proc/'maps').read_text()))
    emit('precheck', pid=pid, sdl_sha256=SDL_SHA, **descriptors(pid,target),
         gamepad=Path(target[0][0]).name, sensor=Path(target[1][0]).name,
         process_memory_opened=False)
    if args.precheck:
        return 0
    print('Nur nach konkreter Freigabe: GO eingeben (120 Sekunden Zeit). Danach 30 Sekunden Vorbereitung.',
          file=sys.stderr, flush=True)
    ready,_,_ = select.select([sys.stdin],[],[],120)
    require(bool(ready) and sys.stdin.readline().strip().lower() == 'go', 'No local GO; no memory open')
    require(process_identity(pid,uid) == process and target_identity() == target, 'Instance changed before GO')
    require(library_identity(maps_parse((proc/'maps').read_text())) == library, 'Library changed before GO')
    # Only metadata was read above. This is the sole process-memory open.
    with os.fdopen(os.open(proc/'mem', os.O_RDONLY | os.O_CLOEXEC), 'rb') as stream:
        memory = Memory(stream.fileno(), maps_parse((proc/'maps').read_text()))
        begin, initial, samples, last_phase = time.monotonic(), None, 0, None
        busy_total = busy_consecutive = 0
        while (elapsed := time.monotonic()-begin) < MAX_SECONDS:
            require(process_identity(pid,uid) == process and target_identity() == target,
                    'Process or controller instance changed')
            rows = maps_parse((proc/'maps').read_text())
            # Compare mapped library identity/base without hashing every sample.
            current = [x for x in rows if x[6] == library[1] and x[3] == 0]
            require(len(current) == 1 and current[0][0] == library[0] and current[0][5] == library[3],
                    'SDL mapping changed')
            memory.rows = rows
            try:
                node, instance, sensors, data = snapshot(memory,library[0],target[0][0])
            except BusySnapshot:
                busy_total += 1
                busy_consecutive += 1
                require(busy_total <= 20 and busy_consecutive < 3, 'Too many inconsistent SDL samples')
                emit('sample_skipped', reason='concurrent_sensor_update')
                time.sleep(.1)
                continue
            busy_consecutive = 0
            identity = node,instance,sensors
            if initial is None:
                initial = identity
            require(identity == initial, 'SDL object replaced; no automatic adoption')
            deadline = 0
            for duration,phase in PHASES:
                deadline += duration
                if elapsed < deadline:
                    break
            if phase != last_phase:
                cue(phase)
                last_phase = phase
            emit('sample', phase=phase, elapsed_s=round(elapsed,3), sdl_instance=instance,
                 **data, **descriptors(pid,target))
            samples += 1
            time.sleep(.1)
        require(process_identity(pid,uid) == process and target_identity() == target, 'Final instance changed')
        require(library_identity(maps_parse((proc/'maps').read_text())) == library, 'Final library check failed')
    emit('complete', samples=samples, samples_skipped=busy_total,
         memory_bytes_read=memory.total, process_memory_closed=True,
         settings_changed=False, target_calls=False, debugger_attached=False)
    print('Beobachtung beendet. Steam und Controller bleiben unverändert. Keine weitere Messung.',
          file=sys.stderr, flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Halt, OSError, ValueError, KeyError, UnicodeError, KeyboardInterrupt) as error:
        # Do not dump process paths, memory or a traceback on failure.
        emit('stopped', reason=str(error) if isinstance(error,Halt) else type(error).__name__,
             automatic_retry=False)
        print('STOPP: Beobachtung beendet; keine Wiederholung und keine Systemänderung.', file=sys.stderr)
        sys.exit(2)
