# SPDX-License-Identifier: GPL-2.0-only
"""Read cached identity only; called solely by the explicitly authorized adapter."""
import datetime, json, os, re, stat, sys
from pathlib import Path
host = json.loads(sys.argv[1])
target = host['target']
profile = host.get('capture_profile')
if profile not in (None, 'passive-hid-100a-300'):
    raise SystemExit('ABBRUCH: Unbekanntes Aufnahmeprofil')
passive = profile == 'passive-hid-100a-300'
if (target['port'] != '8-6' or str(target['busnum']) != '8' or str(target['devpath']) != '6'
        or not re.fullmatch(r'[0-9]{1,3}', str(target['devnum'])) or not 1 <= int(target['devnum']) <= 127):
    raise SystemExit('ABBRUCH: Erwartet Bus 8, Port 8-6 und frische Geräteadresse')
p = Path('/sys/bus/usb/devices') / target['port']
resolved = p.resolve(strict=True)
identity = {'physical_port': resolved.name, 'sysfs_path': str(resolved)}
for name in ('idVendor', 'idProduct', 'busnum', 'devnum', 'devpath', 'bNumInterfaces'):
    identity[name] = (p / name).read_text().strip()
identity['interfaces'] = {}
for index in (0, 1):
    interface = p.parent / (target['port'] + ':1.' + str(index))
    link = interface / 'driver'
    driver = link.resolve(strict=True) if link.is_symlink() else None
    identity['interfaces'][str(index)] = {
        'driver': driver.name if driver else None, 'driver_path': str(driver) if driver else None,
        'endpoints': sorted(int((ep / 'bEndpointAddress').read_text().strip(), 16)
                            for ep in interface.glob('ep_*'))}
if passive:
    identity['boot_id'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    s, parent = resolved.stat(), resolved.parent.stat()
    identity['sysfs_identity'] = {'st_dev': s.st_dev, 'st_ino': s.st_ino,
                                  'parent_st_dev': parent.st_dev, 'parent_st_ino': parent.st_ino}
    if not (identity['physical_port'] == target['port'] and identity['idVendor'] == '3537'
            and identity['idProduct'] == '100a' and identity['bNumInterfaces'] == '2'
            and target.get('vid') == '3537' and target.get('pid') == '100a'
            and identity['boot_id'] == target.get('boot_id')
            and all(identity[key] == str(target[key]) for key in ('busnum', 'devnum', 'devpath'))
            and identity['interfaces']['0']['driver'] == 'xpad'
            and identity['interfaces']['0']['endpoints'] == [2, 130]
            and identity['interfaces']['1']['driver'] == 'usbhid'
            and identity['interfaces']['1']['endpoints'] == [4, 132]
            and identity['sysfs_identity'] == target.get('sysfs_identity')):
        raise SystemExit('ABBRUCH: Passive 100a-Instanz oder Treiberbindung abweichend')
    state_path = Path('/var/lib/gamesir-native/state.json')
    s = state_path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o077 or s.st_size > 1048576:
        raise SystemExit('ABBRUCH: Managerzustand nicht sicher lesbar')
    manager = json.loads(state_path.read_text())
    if manager.get('paused') is not True or manager.get('leases') != {}:
        raise SystemExit('ABBRUCH: Manager muss pausiert und sein Besitzstand leer sein')
    forbidden = {f'/dev/bus/usb/{int(target["busnum"]):03d}/{int(target["devnum"]):03d}'}
    for hidraw in Path('/sys/class/hidraw').glob('hidraw*'):
        if hidraw.resolve(strict=True).is_relative_to(resolved):
            forbidden.add('/dev/' + hidraw.name)
    forbidden_rdevs = set()
    for node in forbidden:
        node_stat = os.lstat(node)
        if not stat.S_ISCHR(node_stat.st_mode):
            raise SystemExit('ABBRUCH: Erwarteter USB-/hidraw-Geräteknoten abweichend')
        forbidden_rdevs.add(node_stat.st_rdev)
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if any(Path(arg).name.lower() in ('deadband', 'deadband.py') or
                   arg.startswith('/usr/share/deadband/') for arg in argv if arg):
                raise SystemExit('ABBRUCH: Deadband ist geöffnet')
            for fd in (proc / 'fd').iterdir():
                try:
                    if os.readlink(fd).removesuffix(' (deleted)') in forbidden:
                        raise SystemExit('ABBRUCH: Fremder USB-/hidraw-Zugriff auf das Zielgerät')
                    descriptor = os.stat(fd)  # Metadata only; never open the referenced node.
                    if stat.S_ISCHR(descriptor.st_mode) and descriptor.st_rdev in forbidden_rdevs:
                        raise SystemExit('ABBRUCH: Fremder USB-/hidraw-Gerätealias geöffnet')
                except FileNotFoundError:
                    continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            raise SystemExit('ABBRUCH: Prozesszugriffsprüfung unvollständig')
elif not (identity['physical_port'] == target['port'] and identity['idVendor'] == '3537'
        and identity['idProduct'] == '109c' and identity['bNumInterfaces'] == '2'
        and all(identity[key] == str(target[key]) for key in ('busnum', 'devnum', 'devpath'))
        and identity['interfaces']['0']['driver'] == 'usbfs'
        and identity['interfaces']['0']['endpoints'] == [2, 130]
        and identity['interfaces']['1']['driver'] is None
        and identity['interfaces']['1']['endpoints'] == []):
    raise SystemExit('ABBRUCH: Erwartete 109c-Vorbereitung mit Deadband fehlt')
# Legacy exclusive ownership is checked separately by its native coordinator.
if 'identity' in host:
    if identity != host['identity']:
        raise SystemExit('ABBRUCH: Identität seit Vorprüfung verändert')
    launcher = str(host['host_launcher_pid'])
    for name, value in host['ns'].items():
        if os.readlink('/proc/' + launcher + '/ns/' + name) != value:
            raise SystemExit('ABBRUCH: Host-Namespace verändert')
    mounts = [line for line in Path('/proc/' + launcher + '/mountinfo').read_text().splitlines()
              if line.split()[4] in ('/', '/dev', '/dev/usbmon8')]
    if mounts != host['host_mounts']:
        raise SystemExit('ABBRUCH: Host-Mounts verändert')
    record = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'identity': identity, 'host_mounts_and_namespaces_unchanged': True}
    os.write(2, ('STAGE4_IDENTITY_JSON ' + json.dumps(record) + '\n').encode())
else:
    print(json.dumps(identity, sort_keys=True))
