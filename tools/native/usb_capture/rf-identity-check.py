# SPDX-License-Identifier: GPL-2.0-only
"""Metadata only. Never open USB/HID/input nodes or send controller requests.

Standalone source is pinned and passed inline to the existing mount supervisor.
Transient enumeration is reported as unknown, never as RF connection evidence.
"""
import datetime
import json
import os
from pathlib import Path
import stat
import sys

SCOPE = 'passive-rf-109c-xpad-90'


def require(value, message):
    if not value:
        raise ValueError(message)


class Pending(Exception):
    pass


def note(diagnostics, field, status, **details):
    if diagnostics is not None:
        diagnostics.append({'field': field, 'status': status, **details})


def checked(diagnostics, field, condition, expected, observed, message):
    note(diagnostics, field, 'passed' if condition else 'failed',
         expected=expected, observed=observed)
    require(condition, message + ': ' + field)


def read_attribute(path, field, diagnostics):
    try:
        value = attribute(path)
    except (OSError, Pending) as error:
        note(diagnostics, field, 'unknown', expected='non-empty cached attribute',
             **({'observed': ''} if isinstance(error, Pending) else {}),
             error_type=type(error).__name__, errno=getattr(error, 'errno', None))
        raise
    note(diagnostics, field, 'observed', observed=value)
    return value


def attribute(path):
    value = path.read_text().strip()
    if not value:
        raise Pending('enumeration_metadata_empty')
    return value


def manager_paused(root, diagnostics=None):
    path = root / 'var/lib/gamesir-native/state.json'
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        note(diagnostics, 'manager.protected.read', 'unknown', error_type=type(error).__name__, errno=error.errno)
        raise
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        for field, condition, expected, observed in (
            ('regular_file', stat.S_ISREG(before.st_mode), True, stat.S_ISREG(before.st_mode)),
            ('owner_uid', before.st_uid == 0, 0, before.st_uid),
            ('private_mode', not before.st_mode & 0o077, 'no group/other access', oct(stat.S_IMODE(before.st_mode))),
            ('size_bytes', before.st_size <= 1048576, '<=1048576', before.st_size)):
            checked(diagnostics, 'manager.protected.' + field, condition, expected, observed,
                    'Unsafe manager state metadata')
        try:
            value = json.loads(stream.read(1048577))
        except ValueError as error:
            note(diagnostics, 'manager.protected.json', 'failed', error_type=type(error).__name__)
            raise
        stable = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        unchanged = stable(before) == stable(os.fstat(stream.fileno())) == stable(path.lstat())
        checked(diagnostics, 'manager.protected.stability', unchanged, True, unchanged,
                'Manager state changed during read')
    checked(diagnostics, 'manager.protected.schema', isinstance(value, dict), 'object',
            type(value).__name__, 'Invalid manager state schema')
    for name, expected in (('paused', True), ('leases', {})):
        checked(diagnostics, 'manager.protected.' + name,
                (value.get(name) is True if name == 'paused' else value.get(name) == {}),
                expected, value.get(name), 'Native must remain paused with empty leases')


def scan_descriptors(root, forbidden, consumers):
    """Metadata of open FDs only, including rdev aliases; inaccessible = fail."""
    found = False
    for proc in (root / 'proc').iterdir():
        if not proc.name.isdigit():
            continue
        operation, fd_number = 'cmdline-read', '-'
        try:
            argv = (proc / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            require(not any(Path(arg).name.lower() in ('deadband', 'deadband.py') or
                    arg.startswith('/usr/share/deadband/') for arg in argv if arg),
                    'Deadband is running')
            operation = 'fd-list'
            for fd in (proc / 'fd').iterdir():
                try:
                    operation, fd_number = 'fd-stat', fd.name
                    value = fd.stat()  # No descriptor/device content read.
                    if stat.S_ISCHR(value.st_mode):
                        require(value.st_rdev not in forbidden, 'Foreign raw USB/hidraw descriptor')
                        found |= value.st_rdev in consumers
                except (FileNotFoundError, ProcessLookupError):
                    continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as error:
            raise ValueError(f'Incomplete process inspection: pid={proc.name} '
                             f'operation={operation} fd={fd_number} errno={error.errno}') from None
    return found


def character_rdev(path):
    value = path.lstat()
    require(stat.S_ISCHR(value.st_mode), 'Unexpected device node type')
    return value.st_rdev


def snapshot(host, root=Path('/'), *, diagnostics=None):
    require(host.get('capture_profile') == SCOPE, 'Wrong RF capture scope')
    cached = host.get('target')
    if cached is not None:
        require((cached['port'], cached['busnum'], cached['devpath'], cached['vid'], cached['pid']) ==
                ('8-6', '8', '6', '3537', '109c'), 'Wrong approved RF baseline')
    usb = root / 'sys/bus/usb/devices'
    boot = read_attribute(root / 'proc/sys/kernel/random/boot_id', 'host.boot_id', diagnostics)
    parent = (usb / 'usb8').resolve(strict=True)
    ps = parent.stat()
    result = {'observation': 'pending', 'identity': None, 'boot_id': boot,
              'parent': {'parent_st_dev': ps.st_dev, 'parent_st_ino': ps.st_ino},
              'manager_paused_empty': True, 'input_consumer_open': False, 'reason': ''}
    if cached is not None:
        require(boot == cached['boot_id'] and result['parent'] == {
            k: v for k, v in cached['sysfs_identity'].items() if k.startswith('parent_')},
            'Boot or parent lifetime changed')
    manager_paused(root, diagnostics=diagnostics)
    # Check *all* native bindings, not just this receiver. Never release them.
    unknown_binding = False
    for link in usb.glob('*:*/driver'):
        try:
            owner = link.resolve(strict=True).name
            if owner == 'gs_native':
                note(diagnostics, 'native_bindings', 'failed', expected='none', observed=link.parent.name)
                raise ValueError('Native USB binding exists')
        except FileNotFoundError:
            unknown_binding = True  # Re-enumeration race; not proof of no owner.
    for path in usb.iterdir():
        if ':' in path.name or path.name.startswith('usb') or path.name == '8-6':
            continue
        try:
            require(not (attribute(path / 'idVendor').lower() == '3537' and
                         attribute(path / 'idProduct').lower() in ('100a', '109c', '105e')),
                    'Another supported GameSir receiver is present')
        except (FileNotFoundError, Pending):
            continue
    node = usb / '8-6'
    # The original bus-address rdev remains forbidden during a metadata gap.
    forbidden = set()
    if cached is not None:
        old = root / f'dev/bus/usb/008/{int(cached["devnum"]):03d}'
        try:
            forbidden.add(character_rdev(old))
        except FileNotFoundError:
            pass
    consumers = set()
    input_nodes_enumerated = False
    active_field = 'device.present'
    try:
        resolved = node.resolve(strict=True)
        initial_stat = resolved.stat()
        require(resolved.parent == parent, 'Receiver moved to a different parent')
        note(diagnostics, 'device.present', 'passed', expected=True, observed=True)
        vendor = read_attribute(node / 'idVendor', 'device.idVendor', diagnostics).lower()
        product = read_attribute(node / 'idProduct', 'device.idProduct', diagnostics).lower()
        checked(diagnostics, 'device.idVendor', vendor == '3537', '3537', vendor, 'Foreign receiver VID/PID')
        checked(diagnostics, 'device.idProduct', product in ('109c', '100a'), ['109c', '100a'], product,
                'Foreign receiver VID/PID')
        values = {name: read_attribute(node / name, 'device.' + name, diagnostics)
                  for name in ('busnum', 'devnum', 'devpath', 'bNumInterfaces')}
        for name, expected in (('busnum', '8'), ('devpath', '6'), ('bNumInterfaces', '2')):
            checked(diagnostics, 'device.' + name, values[name] == expected, expected, values[name],
                    'Receiver topology/descriptors differ')
        checked(diagnostics, 'device.devnum', values['devnum'].isdigit() and 1 <= int(values['devnum']) <= 127,
                'integer 1..127', values['devnum'], 'Receiver topology/descriptors differ')
        active_field = 'device.raw_usb_node'
        forbidden.add(character_rdev(root / f'dev/bus/usb/008/{int(values["devnum"]):03d}'))
        interfaces = {}
        for index in (0, 1):
            interface = usb / ('8-6:1.' + str(index))
            active_field = f'interfaces.{index}.present'
            # A missing directory/attribute is incomplete enumeration, not a valid empty IF1.
            require(interface.resolve(strict=True).parent == resolved, 'Foreign interface topology')
            number = read_attribute(interface / 'bInterfaceNumber', f'interfaces.{index}.number', diagnostics)
            checked(diagnostics, f'interfaces.{index}.number', number == f'{index:02x}',
                    f'{index:02x}', number, 'Wrong interface number')
            driver = interface / 'driver'
            active_field = f'interfaces.{index}.driver'
            owner = driver.resolve(strict=True).name if driver.is_symlink() else None
            expected = 'xpad' if index == 0 else ('usbhid' if product == '100a' else None)
            if owner is None and expected is not None:
                note(diagnostics, f'interfaces.{index}.driver', 'unknown', expected=expected, observed=None)
                raise Pending('interface_not_bound_yet')
            checked(diagnostics, f'interfaces.{index}.driver', owner == expected, expected, owner,
                    'Unexpected interface owner')
            endpoints = sorted(int(read_attribute(ep / 'bEndpointAddress',
                f'interfaces.{index}.{ep.name}.address', diagnostics), 16) for ep in interface.glob('ep_*'))
            expected_ep = [2, 130] if index == 0 else ([4, 132] if product == '100a' else [])
            if not endpoints and expected_ep:
                note(diagnostics, f'interfaces.{index}.endpoints', 'unknown', expected=expected_ep, observed=[])
                raise Pending('endpoints_not_populated')
            checked(diagnostics, f'interfaces.{index}.endpoints', endpoints == expected_ep,
                    expected_ep, endpoints, 'Unexpected endpoints')
            interfaces[str(index)] = {'driver': owner, 'endpoints': endpoints}
        for path in (root / 'sys/class/hidraw').glob('hidraw*'):
            active_field = 'hidraw.metadata'
            if path.resolve(strict=True).is_relative_to(resolved):
                forbidden.add(character_rdev(root / 'dev' / path.name))
        if0 = (usb / '8-6:1.0').resolve(strict=True)
        active_field = 'input.IF0.event_nodes'
        for path in (root / 'sys/class/input').glob('event*'):
            if path.resolve(strict=True).is_relative_to(if0):
                consumers.add(character_rdev(root / 'dev/input' / path.name))
        input_nodes_enumerated = True
        current = resolved.stat()
        result['identity'] = {'port': '8-6', 'busnum': '8', 'devnum': values['devnum'],
            'devpath': '6', 'vid': vendor, 'pid': product, 'interfaces': interfaces, 'boot_id': boot,
            'sysfs_identity': {'st_dev': current.st_dev, 'st_ino': current.st_ino,
                               **result['parent']}}
        result['observation'] = 'present'
        if (current.st_dev, current.st_ino) != (initial_stat.st_dev, initial_stat.st_ino):
            raise Pending('receiver_lifetime_changed_during_metadata')
    except FileNotFoundError:
        result.update(observation='pending' if node.exists() else 'absent', identity=None,
                      reason='enumeration_metadata_missing')
        note(diagnostics, active_field, 'unknown', reason=result['reason'],
             device_path_exists=node.exists())
        if result['observation'] == 'absent':
            note(diagnostics, 'device.present', 'failed', expected=True, observed=False)
    except Pending as error:
        result.update(observation='pending', identity=None, reason=str(error))
    note(diagnostics, 'input.IF0.event_nodes',
         ('passed' if consumers else 'failed') if input_nodes_enumerated else 'not_evaluated',
         expected='at least one exact IF0 input node',
         observed=len(consumers) if input_nodes_enumerated else None)
    try:
        result['input_consumer_open'] = scan_descriptors(root, forbidden, consumers)
    except (ValueError, OSError) as error:
        note(diagnostics, 'process_access', 'unknown' if isinstance(error, OSError) or
             'Incomplete process inspection' in str(error) else 'failed',
             error_type=type(error).__name__, message=str(error))
        raise
    note(diagnostics, 'input.IF0.consumer_open',
         ('passed' if result['input_consumer_open'] else 'failed') if consumers else 'not_evaluated',
         expected=True, observed=result['input_consumer_open'] if consumers else None,
         reason=None if consumers else ('no_matching_IF0_event_node' if input_nodes_enumerated
                                        else 'metadata_incomplete_before_input_inventory'))
    if result['observation'] == 'present':
        try:
            after = node.resolve(strict=True).stat()
            if (after.st_dev, after.st_ino) != (initial_stat.st_dev, initial_stat.st_ino):
                raise Pending('receiver_lifetime_changed_during_FD_scan')
            for name, expected in (('idVendor', vendor), ('idProduct', product),
                                   ('busnum', '8'), ('devnum', values['devnum']), ('devpath', '6')):
                require(attribute(node / name).lower() == expected, 'Identity changed during FD inspection')
        except (FileNotFoundError, Pending):
            result.update(observation='pending', identity=None, reason='receiver_changed_during_inspection')
    if result['observation'] == 'present' and not result['input_consumer_open']:
        result.update(observation='pending', identity=None, reason='ordinary_IF0_consumer_missing')
    if unknown_binding:
        result.update(observation='pending', identity=None, reason='binding_metadata_changed_during_scan')
        note(diagnostics, 'native_bindings', 'unknown', reason=result['reason'])
    manager_paused(root, diagnostics=diagnostics)
    after_parent = parent.stat()
    require(attribute(root / 'proc/sys/kernel/random/boot_id') == boot and
            (after_parent.st_dev, after_parent.st_ino) == (ps.st_dev, ps.st_ino),
            'Boot or parent changed during inspection')
    return result


def main():
    host = json.loads(sys.argv[1])
    value = snapshot(host)
    if 'identity' not in host:
        print(json.dumps(value, sort_keys=True))
        return
    require(value == host['identity'], 'Identity changed before recorder launch')
    launcher = str(host['host_launcher_pid'])
    for name, expected in host['ns'].items():
        require(os.readlink('/proc/' + launcher + '/ns/' + name) == expected, 'Host namespace changed')
    mounts = [line for line in Path('/proc/' + launcher + '/mountinfo').read_text().splitlines()
              if line.split()[4] in ('/', '/dev', '/dev/usbmon8')]
    require(mounts == host['host_mounts'], 'Host mounts changed')
    record = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'identity': value, 'host_mounts_and_namespaces_unchanged': True}
    os.write(2, ('STAGE4_IDENTITY_JSON ' + json.dumps(record) + '\n').encode())


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, Pending) as error:
        raise SystemExit('ABBRUCH: RF metadata: ' + str(error)) from None
