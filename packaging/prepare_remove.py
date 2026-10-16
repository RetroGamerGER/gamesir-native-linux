#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Installed ALPM guard: stop safely BEFORE DKMS/package files are removed.

Importing this module performs no host actions. Tests inject a fake backend.
There is intentionally no --force, fallback rebind, or automatic repair.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

SERVICE_PROPERTIES = ('LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlPID',
                      'Result', 'ExecMainCode', 'ExecMainStatus',
                      'ExecMainStartTimestampMonotonic', 'ExecMainExitTimestampMonotonic')
SERVICE_NUMBERS = ('MainPID', 'ControlPID', 'ExecMainCode', 'ExecMainStatus',
                   'ExecMainStartTimestampMonotonic', 'ExecMainExitTimestampMonotonic')
EXIT_RECORD = ('Result', 'ExecMainCode', 'ExecMainStatus',
               'ExecMainStartTimestampMonotonic', 'ExecMainExitTimestampMonotonic')
BOOT_ID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


class RemovalBlocked(RuntimeError):
    pass


class Host:
    def run(self, argv, timeout=90, allow_failure=False):
        result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
        if result.returncode and not allow_failure:
            raise RemovalBlocked(f"{' '.join(argv)}: {result.stderr.strip() or result.stdout.strip()}")
        return result

    def service_state(self):
        result = self.run(['/usr/bin/systemctl', 'show',
                           '--property=' + ','.join(SERVICE_PROPERTIES),
                           'gamesir-native.service'])
        state = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition('=')
            if not separator or key not in SERVICE_PROPERTIES or key in state:
                raise RemovalBlocked('Malformed service status; no removal')
            state[key] = value
        if set(state) != set(SERVICE_PROPERTIES):
            raise RemovalBlocked('Incomplete service status; no removal')
        for key in SERVICE_NUMBERS:
            if not state[key].isascii() or not state[key].isdecimal():
                raise RemovalBlocked('Invalid service process/exit status; no removal')
            state[key] = int(state[key])
        return state

    def unresolved_ownership(self, *, allow_prior_boot=False):
        path = Path('/var/lib/gamesir-native/state.json')
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            return False  # Installed but never started is a valid removal case.
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or
                metadata.st_mode & 0o077 or metadata.st_size > 1024 * 1024):
            raise RemovalBlocked('Unsafe manager recovery state; no removal')
        state = json.loads(path.read_text())
        if not isinstance(state, dict) or not isinstance(state.get('leases'), dict):
            raise RemovalBlocked('Invalid manager recovery state; no removal')
        # Only leases describe unresolved ownership. Persistent pause, previous
        # errors and the attempt budget are not an automatic removal block.
        if not state['leases']:
            return False
        saved_boot = state.get('boot_id')
        if (allow_prior_boot and isinstance(saved_boot, str) and
                BOOT_ID.fullmatch(saved_boot) and not self.module_loaded()):
            current_boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            if BOOT_ID.fullmatch(current_boot) and current_boot != saved_boot:
                # A previous kernel's instance tokens cannot retain ownership
                # across host boots. This exemption requires an inactive
                # supervisor and absent module; never alter/start recovery.
                return False
        return True

    def module_loaded(self):
        return Path('/sys/module/gs_native').is_dir()

    def native_bindings(self):
        driver = Path('/sys/bus/usb/drivers/gs_native')
        return sorted(p.name for p in driver.glob('*:*') if p.is_symlink())

    def module_references(self):
        return int(Path('/sys/module/gs_native/refcnt').read_text().strip())

    def manager_present(self):
        # The socket alone is not proof of a working server; release must reply.
        return Path('/run/gamesir-native/control.sock').exists()


def prepare_removal(host, *, disable=False):
    """Return controllers, stop service, unload only the verified unused module."""
    before = host.service_state()
    phase = (before['ActiveState'], before['SubState'])
    if (before['LoadState'] != 'loaded' or phase not in
            (('active', 'running'), ('inactive', 'dead'), ('failed', 'failed')) or
            before['ControlPID'] or (bool(before['MainPID']) != (phase[0] == 'active'))):
        raise RemovalBlocked(f"Unexpected service state: {phase!r}; no removal")
    if phase[0] == 'active' or host.manager_present():
        # release verifies the actual origin/xpad return or physical absence.
        host.run(['/usr/bin/gamesir-native', 'release'])
    if host.unresolved_ownership(allow_prior_boot=phase[0] in ('inactive', 'failed')):
        raise RemovalBlocked('Unresolved manager ownership/return; verify release before removal')
    if host.native_bindings():
        raise RemovalBlocked('Native interfaces remain bound; package files retained')
    host.run(['/usr/bin/systemctl', 'stop', 'gamesir-native.service'])
    after = host.service_state()
    if (after['LoadState'] != 'loaded' or after['ActiveState'] != 'inactive' or
            after['SubState'] != 'dead' or after['MainPID'] or after['ControlPID']):
        raise RemovalBlocked('Service stop is not complete; package files retained')
    clean_exit = (after['Result'] == 'success' and after['ExecMainCode'] in (0, 1) and
                  after['ExecMainStatus'] == 0)
    unchanged_old_failure = (phase[0] in ('inactive', 'failed') and
                             all(before[key] == after[key] for key in EXIT_RECORD))
    if not clean_exit and not unchanged_old_failure:
        raise RemovalBlocked('New service exit/stop failure; verify return before removal')
    if host.unresolved_ownership(allow_prior_boot=True):
        raise RemovalBlocked('Unresolved manager ownership after shutdown; package files retained')
    if host.native_bindings():
        raise RemovalBlocked('Native binding appeared during shutdown; removal blocked')
    if host.module_loaded():
        if host.module_references() != 0:
            raise RemovalBlocked('gs_native has live references; refusing to unload')
        # Unlike modprobe -r, this does not remove unrelated unused dependencies.
        host.run(['/usr/bin/rmmod', 'gs_native'], timeout=15)
        if host.module_loaded():
            raise RemovalBlocked('gs_native still loaded after unload request')
    if disable:
        host.run(['/usr/bin/systemctl', 'disable', 'gamesir-native.service'])
    return {'safe_to_remove': True, 'native_bindings': [], 'module_loaded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--remove', action='store_true')
    mode.add_argument('--upgrade', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('This installed package-removal guard requires root')
    try:
        prepare_removal(Host(), disable=args.remove)
    except (RemovalBlocked, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'GameSir removal BLOCKED: {exc}', file=sys.stderr)
        return 1
    print('GameSir release verified; module absent. Package removal may proceed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
