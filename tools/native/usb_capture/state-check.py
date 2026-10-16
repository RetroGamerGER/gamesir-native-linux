# SPDX-License-Identifier: GPL-2.0-only
import json, os, stat
from pathlib import Path

s = os.lstat("/dev/usbmon8")
if not stat.S_ISCHR(s.st_mode):
    raise SystemExit("ABBRUCH: usbmon8 ist kein Zeichen-Geräteknoten")
if (s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode)) != (0, 0, 0o600):
    raise SystemExit("ABBRUCH: Eigentümer oder Modus abweichend")

major, minor = os.major(s.st_rdev), os.minor(s.st_rdev)
if minor != 8:
    raise SystemExit("ABBRUCH: usbmon-Minornummer ist nicht Bus 8")
# usbmon allocates its major dynamically; module load order can change it.
# Bind it to the CURRENT kernel registration, never to a historical number.
character_section = Path('/proc/devices').read_text().split('Character devices:\n', 1)[1].split('Block devices:', 1)[0]
registered = [int(parts[0]) for line in character_section.splitlines()
              if len(parts := line.split()) == 2 and parts[1] == 'usbmon']
if registered != [major]:
    raise SystemExit("ABBRUCH: Major nicht eindeutig als usbmon registriert")
char_path = Path(f'/sys/dev/char/{major}:{minor}')
class_path = Path('/sys/class/usbmon/usbmon8')
if (char_path.resolve(strict=True) != class_path.resolve(strict=True)
        or (char_path / 'subsystem').resolve(strict=True) != Path('/sys/class/usbmon').resolve(strict=True)
        or (class_path / 'dev').read_text().strip() != f'{major}:{minor}'
        or (char_path / 'dev').read_text().strip() != f'{major}:{minor}'):
    raise SystemExit("ABBRUCH: usbmon-Klassenpfad oder Gerätenummer widersprüchlich")
uevent = dict(line.split("=", 1) for line in
              Path(f"/sys/dev/char/{major}:{minor}/uevent").read_text().splitlines()
              if "=" in line)
if (uevent.get("DEVNAME") != "usbmon8" or minor != 8
        or uevent.get("MAJOR") != str(major)
        or uevent.get("MINOR") != str(minor)):
    raise SystemExit("ABBRUCH: Kernel-Geräteidentifikation abweichend")

keys = ("st_dev", "st_ino", "st_rdev", "st_uid", "st_gid", "st_mode")
names = ("mnt", "pid", "net", "ipc", "uts", "user")
mounts = [line for line in Path("/proc/self/mountinfo").read_text().splitlines()
          if line.split()[4] in ("/", "/dev", "/dev/usbmon8")]
print(json.dumps({
    "ns": {n: os.readlink("/proc/self/ns/" + n) for n in names},
    "uid_map": Path("/proc/self/uid_map").read_text(),
    "gid_map": Path("/proc/self/gid_map").read_text(),
    "node": {k: getattr(s, k) for k in keys},
    "major": major, "minor": minor, "uevent": uevent,
    "host_mounts": mounts, "host_launcher_pid": os.getppid(),
}, sort_keys=True))
