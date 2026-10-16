# SPDX-License-Identifier: GPL-2.0-only
"""Read cached identity only; called solely by the explicitly authorized adapter."""
import datetime, json, os, re, sys
from pathlib import Path
host = json.loads(sys.argv[1])
target = host['target']
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
if not (identity['physical_port'] == target['port'] and identity['idVendor'] == '3537'
        and identity['idProduct'] == '109c' and identity['bNumInterfaces'] == '2'
        and all(identity[key] == str(target[key]) for key in ('busnum', 'devnum', 'devpath'))
        and identity['interfaces']['0']['driver'] == 'usbfs'
        and identity['interfaces']['0']['endpoints'] == [2, 130]
        and identity['interfaces']['1']['driver'] is None
        and identity['interfaces']['1']['endpoints'] == []):
    raise SystemExit('ABBRUCH: Erwartete 109c-Vorbereitung mit Deadband fehlt')
# Exclusive process ownership is checked separately by the native coordinator.
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
