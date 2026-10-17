# Installing and removing GameSir Native Linux

**PRE-ALPHA — for experienced Linux testers.** Keep a keyboard available and know the recovery
procedure before enabling this experimental out-of-tree driver. This guide describes commands; it
does not execute or authorize installation.

The current source recipe is `gamesir-native-dkms 0.1.0.alpha3-6` for Arch-family `x86_64`
systems. The published first source tag retains its original revision-5 recipe. Revision 6 adds an
offline-tested manager reconnect correction; a subsequent native bootstrap and limited
Forza/Xodus run succeeded. Repeated reconnect acceptance is still open. Read the
[reconnect update scope and approval plan](MANAGER_RECONNECT_FIX.md) before updating.
This is a preparation guide, not an available public binary release. Build the reviewed source;
older local packages do not contain newly added licensing files merely because their name matches.
Garuda KDE and CachyOS Gamescope have limited real-hardware evidence; this is not a promise for
every kernel, distribution, or SteamOS image. The standard G7 Pro uses `3537:100a` → `3537:109c`;
ZZZ `3537:105e` has a separate direct-start path and more limited hardware coverage. USB ports are
discovered dynamically. Bluetooth and wired operation are outside this tested scope.

The standard model has confirmed normal input and four independent extra buttons; ZZZ's four
physical extra buttons remain unconfirmed. Steam paddle recognition needs the optional integration
below. Standard `FF_RUMBLE` controls the grip motors; separate trigger motors
need an application adapter through the local API. IMU output is experimental raw data: gyro
calibration is paused, and calibrated SDL sensors are not available. See
[project status](../README.md#project-status-and-supported-scope).

## 1. Check the target system

Close games and Deadband; do not run concurrent controller configuration tools. Use the full source
tree at the reviewed commit, not the smaller DKMS build archive, for development tests. Read
[licensing](LICENSING.md) before distributing packages. Do not build as root.

```sh
uname -r
pacman -Q dkms python systemd kmod clang llvm lld make gcc binutils
test -f "/usr/lib/modules/$(uname -r)/build/Module.symvers"
cat "/usr/lib/modules/$(uname -r)/build/include/generated/utsrelease.h"
```

Install headers matching **each exact target kernel**, using the distribution's package names.
Generic `linux-headers` cannot replace another variant's headers. Also provide normal Arch
package-building tools. Resolve missing prerequisites separately; do not use partial database
refreshes or bypass dependencies. Secure Boot/enforced module signatures require signing/enrolment;
no bypass is provided.

## 2. Build without installing

From the full source-tree root, with prerequisites already present:

```sh
make test
make kernel
make tools
python -B scripts/package_alpha.py source --dest build/package-source
cd build/package-source
sha256sum -c SHA256SUMS
makepkg --cleanbuild
makepkg --packagelist
```

Use a new empty output directory for another build; existing output is preserved. These commands do
not load/install modules. Do not add `--nodeps`, `-s`, or `-i`. The DKMS archive is a build subset,
not the full repository/test environment. Save commit ID, logs, and package hash together. A locally
computed hash checks recorded bytes; it does not authenticate an untrusted download.

## 3. Review and install the package, with the service inactive

```sh
GS_PACKAGE=./GameSir-Native-Linux-PRE-ALPHA-0.1.0.alpha3-6-x86_64.pkg.tar.zst
sha256sum "$GS_PACKAGE"
pacman -Qip "$GS_PACKAGE"
pacman -Qlp "$GS_PACKAGE"
sudo pacman -U -- "$GS_PACKAGE"
```

Review the complete transaction; stop for unexpected packages, conflicts, stale databases, or a
required system upgrade. Do not use `--noconfirm`. Review host hooks: DKMS, boot-image/initramfs
rebuilds, module dependencies, snapshots, and systemd metadata reloads can occur. First installation
does not start/enable the service; these other hook effects still belong to the transaction.

After installation, verify the actual DKMS result rather than trusting the package-manager exit
status alone:

```sh
pacman -Qkk gamesir-native-dkms
dkms status
modinfo -k "$(uname -r)" -F version gs_native
modinfo -k "$(uname -r)" -F vermagic gs_native
systemctl is-active gamesir-native.service
systemctl is-enabled gamesir-native.service
```

Require DKMS `installed` for the intended kernel, module version `0.1.0.alpha3` (the package adds
revision `-6`), matching vermagic, and inactive/disabled service on first installation. Investigate
differences before activation. Installing files does not replace an older loaded module; do not
force its removal.

## 4. Enable normal automatic operation

```sh
sudo systemctl enable --now gamesir-native.service
systemctl is-active gamesir-native.service
systemctl is-enabled gamesir-native.service
sudo gamesir-native status
journalctl -u gamesir-native.service -b --no-pager
```

The service loads the module and manages supported interfaces. Connect the dongle, turn on the
controller, and use normal inputs: routine play needs no Deadband, terminal, or password. Bootstrap
may wait for ordinary input from a quiet controller. Check `GameSir G7 Pro`, normal controls, and
four extra buttons in an input tester. Steam integration is separate.

`gamesir-native status` reads the manager's cached state through its protected administrative
socket; it is not a new direct USB status probe. An active session normally reports `returned:
false`. A persisted maintenance pause needs an intentional `sudo gamesir-native resume` only after
checking the reported state. Do not repeat resume or restart the service in a failure loop.

For updates, the guard releases ownership, stops the service, and unloads only the verified unused
native module. Check the new DKMS build, then deliberately restart/resume management; its pause
persists. Kernel updates also need matching headers and a successful target DKMS build before
booting. DKMS does not guarantee compatibility with every future kernel.

## 5. Optional Steam and CachyOS Gamescope integration

The kernel driver has no Steam dependency. `gamesir-native-steam` adds a conservative SDL mapping in
a new Plasma login; it preserves existing mappings and individual game bindings. A running Steam
process keeps its old environment. Close Steam normally and start a new login session when testing
persistence.

Build optional packages separately from the full source-tree root:

```sh
python -B scripts/package_steam.py source --dest build/steam-package-source
python -B scripts/package_steam.py source --component gamescope --dest build/gamescope-package-source
```

In each selected generated directory, verify `SHA256SUMS`, run `makepkg --cleanbuild`, inspect the
resulting archive and dependencies, then install only the reviewed package with `sudo pacman -U --
<reviewed-package>`. The Gamescope package additionally requires the base Steam package and
`gamescope-session-cachyos`; it is not generic Gamescope or SteamOS support. Check `systemctl --user
cat steam-launcher.service` and existing drop-ins first. The integration replaces only its
`ExecStart` with a wrapper that delegates to `/usr/lib/steamos/steam-launcher`. Changes to the
vendor start contract require rechecking it; see [Gamescope integration](STEAM_GAMESCOPE.md).

Test all four paddles separately, together, and on release. They are Steam Input sources, not
additional XInput output buttons; a game's input API can still prevent direct in-game assignment.
Existing SDL mapping/file overrides can block the addition. Do not erase those overrides
indiscriminately. Flatpak and other session arrangements need separate validation.

## 6. Release ownership and recover safely

```sh
sudo gamesir-native release
sudo gamesir-native status
```

Require `returned: true` with no unresolved managed ownership, plus an independent check of the
actual USB identity and interface bindings. Read these from sysfs; USB addresses and port names can
change. Standard-model fallback means observed `3537:100a` with interface 0 bound to `xpad`
(normally interface 1 `usbhid`). ZZZ can return to `3537:105e` with `xpad`. Binding `xpad` to `109c`
is **not** proof of a return to `100a`. Confirm ordinary inputs separately.

Read-only identity/binding listing; stop if metadata changes during the check:

```sh
python -B - <<'PY'
from pathlib import Path
for vendor in sorted(Path('/sys/bus/usb/devices').glob('*/idVendor')):
    if vendor.read_text().strip() != '3537':
        continue
    device = vendor.parent
    print(device.name, '3537:' + (device / 'idProduct').read_text().strip())
    for interface in sorted(device.parent.glob(device.name + ':*')):
        driver = interface / 'driver'
        print(' ', interface.name, driver.resolve().name if driver.is_symlink() else 'unbound')
PY
```

If release fails, retain the error and stop. Do not reset USB, guess a mode command, force-unload a
module, or bypass the package guards. For a verified stuck managed dongle, keep automatic management
paused, physically unplug only that dongle, and wait for confirmed absence and cleared ownership.
Absence is not proof of normal gamepad function. After stopping management, reconnect and inspect
its new identity/bindings before testing input. An unexpected identity or unresolved ownership
requires diagnosis, not another bootstrap attempt.

## 7. Complete removal

Close games, Steam, and Deadband. Prevent the next automatic start, then release:

```sh
sudo systemctl disable gamesir-native.service
sudo gamesir-native release
```

Proceed only after the recovery checks above, then stop the service. If it was never started and has
no socket, skip the unavailable release call; the removal guard must still confirm empty ownership
and no native bindings.

```sh
sudo systemctl stop gamesir-native.service
```

Check each package with `pacman -Q <name>`. Remove **only installed packages**, in this order, one
reviewed transaction at a time; skip absent optional packages:

```sh
sudo pacman -R gamesir-native-steam-gamescope
sudo pacman -R gamesir-native-steam
sudo pacman -R gamesir-native-dkms
```

The native package's `AbortOnFail` guard blocks removal for unresolved ownership, bindings, live
module references, or incomplete shutdown. Do not use force or `--nodeps`. Review DKMS and
boot-image hooks again. Read-only verification after removal:

```sh
pacman -Q gamesir-native-dkms
pacman -Q gamesir-native-steam
pacman -Q gamesir-native-steam-gamescope
dkms status
test ! -d /sys/module/gs_native
systemctl show gamesir-native.service -p LoadState -p ActiveState -p MainPID -p ControlPID
test ! -e /usr/bin/gamesir-native-steam
test ! -e /etc/xdg/plasma-workspace/env/90-gamesir-native-steam.sh
test ! -e /usr/share/gamesir-native-steam/session.sh
test ! -e /usr/lib/gamesir-native-steam/gamescope-launcher
test ! -e /usr/lib/systemd/user/steam-launcher.service.d/50-gamesir-native.conf
test ! -e /run/gamesir-native/control.sock
test ! -e /run/gamesir-native-haptics/control.sock
systemctl --user cat steam-launcher.service
```

The three package queries should now report “not found”; absence checks should succeed. Require
no GameSir DKMS entry, no loaded native module, no running service processes, no remaining native
bindings, and no project Steam override in the merged user unit. Recheck sysfs and normal `xpad`
inputs on reconnected hardware. Do not remove `xpad`, `usbhid`, or unrelated DKMS modules.

For the Steam integrations, check that their packaged wrappers/drop-in are gone, then reload user
systemd metadata and start a fresh session. Existing processes or a lingering user manager may
retain the old mapping. Remove only the exact project-added mapping if necessary; preserve unrelated
SDL values, Steam names, and game profiles. Package removal alone does not erase inherited
environments.

### Optional retained-state cleanup

Removal intentionally leaves `/var/lib/gamesir-native/state.json`, the dedicated haptics group,
and deliberate memberships. No service socket means no motor access. These cleanup steps are
optional: first prove all three packages absent, the service stopped, the module absent, and all
ownership resolved. Preserve any desired private evidence before deleting state.

The manager normally writes only `state.json`; an interrupted save can leave `state.new`. Do not
discard that file or any unexpected entry automatically. This bounded command checks the private
directory and empty leases, deletes only `state.json`, then removes only the empty directory:

```sh
sudo python -B - <<'PY'
import json, stat, subprocess
from pathlib import Path
directory = Path('/var/lib/gamesir-native')
for package in ('gamesir-native-dkms', 'gamesir-native-steam', 'gamesir-native-steam-gamescope'):
    result = subprocess.run(['pacman', '-Q', package], capture_output=True)
    if result.returncode != 1:
        raise SystemExit('STOP: package present or package query failed')
result = subprocess.run(['systemctl', 'show', 'gamesir-native.service',
                         '-p', 'LoadState', '-p', 'ActiveState', '-p', 'MainPID', '-p', 'ControlPID'],
                        capture_output=True, text=True)
properties = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
if (properties.get('LoadState') != 'not-found' or properties.get('ActiveState') != 'inactive'
        or properties.get('MainPID') != '0' or properties.get('ControlPID') != '0'):
    raise SystemExit('STOP: service absence/stop not verified')
if Path('/sys/module/gs_native').exists():
    raise SystemExit('STOP: native module still loaded')
metadata = directory.lstat()
if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_mode & 0o077:
    raise SystemExit('STOP: unexpected state directory ownership/type/permissions')
entries = {entry.name for entry in directory.iterdir()}
if entries == {'state.json'}:
    state = directory / 'state.json'
    metadata = state.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0
            or metadata.st_mode & 0o077 or metadata.st_size > 1024 * 1024):
        raise SystemExit('STOP: unexpected state file')
    data = json.loads(state.read_text())
    if type(data) is not dict or data.get('leases') != {}:
        raise SystemExit('STOP: invalid state or unresolved ownership')
    state.unlink()
elif entries:
    raise SystemExit('STOP: unexpected state entries; investigate before cleanup')
directory.rmdir()
print('Removed only verified state.json and its empty directory')
PY
```

If the directory is already absent, skip this command. No recursive deletion or recovery-state
bypass is intended. Stop if the preconditions cannot be independently confirmed.

After checking ownership and emptiness, remove only existing empty runtime directories if desired:

```sh
sudo rmdir -- /run/gamesir-native-haptics
sudo rmdir -- /run/gamesir-native
```

Skip absent directories. Unexpected remaining files or sockets require investigation; `rmdir`
refuses a nonempty directory. These runtime paths also normally disappear at shutdown.

Inspect the dedicated group and primary/supplementary users before changing it:

```sh
getent group gamesir-native-haptics
getent passwd
id -nG "$USER"
```

Only if **you deliberately added your own membership for this project**, remove that membership:

```sh
sudo gpasswd -d "$USER" gamesir-native-haptics
```

Recheck group membership, passwd GIDs, and other uses. Only if the group has no remaining users
or unrelated purpose, remove this specific group:

```sh
sudo groupdel gamesir-native-haptics
```

Preserve shared configuration, journals, snapshots, other groups, and unrelated SDL values.
Package removal/cleanup does not reverse host hooks byte for byte: rebuilt boot images, snapshots,
journal records, and already inherited process environments are not automatically undone.
