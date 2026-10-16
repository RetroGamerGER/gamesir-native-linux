# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

# Before any bind operation, verify the private outer mount namespace.
/usr/bin/python -I -c '
import json, os, sys
from pathlib import Path
host = json.loads(sys.argv[1])
if os.readlink("/proc/self/ns/mnt") == host["ns"]["mnt"]:
    raise SystemExit("ABBRUCH: äußerer Mount-Namensraum unverändert")
for line in Path("/proc/self/mountinfo").read_text().splitlines():
    f = line.split()
    if any(x.startswith(("shared:", "master:", "propagate_from:"))
           for x in f[6:f.index("-")]):
        raise SystemExit("ABBRUCH: Mount-Weitergabe nicht vollständig privat")
' "$1"

# Record the exact timeout supervisor for a capture-only abort if needed.
/usr/bin/python -I -c '
import json, os
from pathlib import Path
pid = int(next(x.split()[1] for x in Path("/proc/"+str(os.getppid())+"/status").read_text().splitlines() if x.startswith("PPid:")))
start = Path("/proc/"+str(pid)+"/stat").read_text().rsplit(")",1)[1].split()[19]
assert os.readlink("/proc/"+str(pid)+"/exe") == "/usr/bin/timeout"
os.write(2, ("MEASUREMENT_B_SUPERVISOR_JSON "+json.dumps({"pid":pid,"starttime":start})+"\n").encode())
'

# Fresh cached identity and unchanged host mounts after authentication.
/usr/bin/python -I -c "$3" "$1"

/usr/bin/mount --no-mtab --internal-only --options-source disable \
    --bind /dev/usbmon8 /dev/usbmon8
/usr/bin/mount --no-mtab --internal-only --options-source disable \
    -o remount,bind,ro,nosuid,noexec,dev \
    /dev/usbmon8 /dev/usbmon8

exec /usr/bin/bwrap \
    --die-with-parent --new-session \
    --unshare-user --uid 0 --gid 0 \
    --unshare-pid --unshare-net --unshare-ipc --unshare-uts \
    --clearenv --setenv PATH /usr/bin --setenv LANG C \
    --setenv TZ UTC --setenv HOME / --chdir / \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 \
    --dir /etc --ro-bind /etc/ld.so.cache /etc/ld.so.cache \
    --proc /proc --remount-ro /proc \
    --tmpfs /dev \
    --dev-bind /dev/usbmon8 /dev/usbmon8 \
    --remount-ro /dev \
    --dir /sys --dir /run --dir /home \
    --remount-ro / \
    --cap-drop ALL \
    -- /usr/bin/setpriv --no-new-privs \
    /usr/bin/python -I -c "$2" "$1" "$(/usr/bin/readlink /proc/self/ns/mnt)"
