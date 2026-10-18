# SPDX-License-Identifier: GPL-2.0-only
import datetime, json, os, signal, stat, subprocess, sys, time
from pathlib import Path

r = {
    "scope": "measurement B one isolated dumpcap capture, maximum duration 450 seconds",
    "dumpcap_started": False,
    "capture_requested": True,
    "passed": False,
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
def need(ok, message):
    if not ok:
        raise RuntimeError(message)

p = None
def interrupted(signum, frame):
    raise RuntimeError("Recorder interrupted by signal " + str(signum))
signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)

try:
    host = json.loads(sys.argv[1])
    profile = host.get('capture_profile')
    need(profile in (None, 'passive-hid-100a-300', 'passive-hid-100a-90'), 'Unknown capture profile')
    duration = 90 if profile == 'passive-hid-100a-90' else (300 if profile == 'passive-hid-100a-300' else 450)
    if profile is not None:
        r['scope'] = 'passive HID 100a one isolated dumpcap capture, maximum duration ' + str(duration) + ' seconds'
    outer_mnt = sys.argv[2]
    names = ("mnt", "pid", "net", "ipc", "uts", "user")
    r["ns"] = {n: os.readlink("/proc/self/ns/" + n) for n in names}
    need(outer_mnt != host["ns"]["mnt"], "Outer mount namespace not isolated")
    need(r["ns"]["mnt"] != outer_mnt, "Inner mount namespace not isolated")
    for n in names:
        need(r["ns"][n] != host["ns"][n], "Host namespace retained: " + n)
    r["outer_mnt"] = outer_mnt

    for name in ("uid_map", "gid_map"):
        need(host[name].split() == ["0", "0", "4294967295"],
             "Unexpected outer identity mapping")
        r[name] = Path("/proc/self/" + name).read_text()
        need(r[name].split() == ["0", "0", "1"], "Unexpected " + name)

    status = dict(line.split(":", 1)
                  for line in Path("/proc/self/status").read_text().splitlines()
                  if ":" in line)
    keys = ("Uid", "Gid", "CapInh", "CapPrm", "CapEff",
            "CapBnd", "CapAmb", "NoNewPrivs")
    r["rights"] = {k: status[k].strip() for k in keys}
    for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"):
        need(int(status[k], 16) == 0, "Nonzero " + k)
    need(status["NoNewPrivs"].strip() == "1", "NoNewPrivs != 1")
    for k in ("Uid", "Gid"):
        need(status[k].split() == ["0"] * 4, "Unexpected " + k)
    r["groups"] = os.getgroups()
    need(set(r["groups"]) <= {0}, "Unexpected supplementary groups")

    r["dev_entries"] = sorted(os.listdir("/dev"))
    need(r["dev_entries"] == ["usbmon8"], "Unexpected /dev contents")
    for path in ("/dev/bus/usb", "/oldroot", "/newroot"):
        need(not os.path.lexists(path), "Unexpected path: " + path)
    for path in ("/sys", "/run", "/home"):
        need(not os.listdir(path), "Host contents visible: " + path)
    need(set(os.listdir("/etc")) == {"ld.so.cache"}, "Unexpected /etc contents")
    need(set(os.listdir("/")) <= {
        "bin", "lib", "lib64", "usr", "etc",
        "proc", "dev", "sys", "run", "home"
    }, "Unexpected root entry")

    mounts = {}
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        f = line.split()
        mounts[f[4]] = {
            "flags": f[5].split(","),
            "fstype": f[f.index("-") + 1],
        }
    r["mounts"] = mounts
    required = {"/", "/usr", "/etc/ld.so.cache", "/proc", "/dev", "/dev/usbmon8"}
    allowed = required | {"/proc/sys", "/proc/sysrq-trigger", "/proc/irq", "/proc/bus"}
    need(required <= set(mounts) <= allowed, "Unexpected mount layout")
    for path, info in mounts.items():
        flags = set(info["flags"])
        need({"ro", "nosuid"} <= flags, "Missing mount protection: " + path)
        if path == "/dev/usbmon8":
            need("nodev" not in flags and "noexec" in flags,
                 "Monitor mount is not device-capable or lacks noexec")
        else:
            need("nodev" in flags, "Unexpected device-capable mount: " + path)
    need(mounts["/dev"]["fstype"] == "tmpfs", "/dev is not private tmpfs")
    need(mounts["/proc"]["fstype"] == "proc", "/proc is not procfs")
    need("noexec" in mounts["/proc"]["flags"], "/proc lacks noexec")

    s = os.lstat("/dev/usbmon8")
    need(stat.S_ISCHR(s.st_mode), "Monitor is not a character device")
    keys = ("st_dev", "st_ino", "st_rdev", "st_uid", "st_gid", "st_mode")
    r["node"] = {k: getattr(s, k) for k in keys}
    need(r["node"] == host["node"], "Monitor identity or permissions changed")

    fds = {}
    for name in os.listdir("/proc/self/fd"):
        try:
            os.fstat(int(name))
            fds[name] = os.readlink("/proc/self/fd/" + name)
        except OSError:
            continue
    r["fds"] = fds
    need(set(fds) == {"0", "1", "2"}, "Unexpected inherited descriptor")
    s = os.fstat(0)
    need(stat.S_ISCHR(s.st_mode) and s.st_rdev == os.makedev(1, 3),
         "Unexpected standard input")
    for fd in (1, 2):
        need(stat.S_ISREG(os.fstat(fd).st_mode), "Output is not a regular log file")

    r["preflight_passed"] = True
    r["target_identity"] = host["identity"]
    mountinfo_before = Path("/proc/self/mountinfo").read_text()

    def rights(pid="self"):
        values = dict(line.split(":", 1) for line in
                      Path(f"/proc/{pid}/status").read_text().splitlines() if ":" in line)
        return {name: values[name].strip() for name in r["rights"]}

    def descriptors(pid="self"):
        result = {}
        for name in os.listdir(f"/proc/{pid}/fd"):
            path = f"/proc/{pid}/fd/{name}"
            try:
                s = os.stat(path)
                target = os.readlink(path)
            except FileNotFoundError:
                continue
            if stat.S_ISCHR(s.st_mode):
                need(s.st_rdev in (os.makedev(1, 3), host["node"]["st_rdev"]),
                     "Unexpected character-device descriptor")
            result[name] = {"target": target, "mode": s.st_mode, "rdev": s.st_rdev}
        return result

    def audit(marker, value):
        os.write(2, (marker + " " + json.dumps(value, sort_keys=True) + "\n").encode())

    need(os.access("/usr/bin/dumpcap", os.X_OK), "dumpcap not executable in final sandbox")
    r["dumpcap_argv"] = [
        "/usr/bin/dumpcap", "-i", "usbmon8", "-y", "USB_LINUX_MMAPPED",
        "-s", "0", "-F", "pcapng", "-a", "duration:" + str(duration), "-a", "filesize:2000000", "-q", "-w", "-",
    ]
    audit("MEASUREMENT_B_PREFLIGHT_JSON", r)
    r["capture_start_request_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    capture_started = time.monotonic()
    capture_started_monotonic_ns = time.monotonic_ns()
    p = subprocess.Popen(r["dumpcap_argv"], close_fds=True)
    r["dumpcap_started"] = True
    r["dumpcap_pid_in_namespace"] = p.pid

    deadline = time.monotonic() + 2
    while p.poll() is None and time.monotonic() < deadline:
        try:
            exe = f"/proc/{p.pid}/exe"
            if os.readlink(exe) != "/usr/bin/dumpcap":
                time.sleep(0.001)
                continue
            child_rights = rights(str(p.pid))
            need(child_rights == r["rights"], "dumpcap rights differ after exec")
            child_ns = {name: os.readlink(f"/proc/{p.pid}/ns/{name}") for name in r["ns"]}
            need(child_ns == r["ns"], "dumpcap left the verified namespaces")
            for name in ("uid_map", "gid_map"):
                need(Path(f"/proc/{p.pid}/{name}").read_text() == r[name],
                     "dumpcap identity mapping changed")
            need(Path(f"/proc/{p.pid}/mountinfo").read_text() == mountinfo_before,
                 "dumpcap mount layout changed")
            need(sorted(os.listdir(f"/proc/{p.pid}/root/dev")) == ["usbmon8"],
                 "Unexpected dumpcap device view")
            need(not os.path.lexists(f"/proc/{p.pid}/root/dev/bus/usb"),
                 "Raw USB visible to dumpcap")
            child_fds = descriptors(str(p.pid))
            monitor_fds = [name for name, info in child_fds.items()
                           if stat.S_ISCHR(info["mode"]) and
                           info["rdev"] == host["node"]["st_rdev"]]
            need(os.readlink(exe) == "/usr/bin/dumpcap", "dumpcap exec snapshot unstable")
            r["dumpcap_rights_after_exec"] = child_rights
            if monitor_fds:
                r["dumpcap_process_snapshot"] = {
                    "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "checked_monotonic_ns": time.monotonic_ns(),
                    "capture_started_monotonic_ns": capture_started_monotonic_ns,
                    "exe": "/usr/bin/dumpcap", "rights": child_rights,
                    "namespaces": child_ns, "fds": child_fds,
                    "monitor_fds": monitor_fds, "raw_usb_absent": True,
                    "mountinfo_unchanged": True,
                }
                audit("MEASUREMENT_B_DUMPCAP_JSON", r["dumpcap_process_snapshot"])
                break
        except (FileNotFoundError, ProcessLookupError):
            pass
        time.sleep(0.001)

    need("dumpcap_process_snapshot" in r, "No verified dumpcap snapshot with monitor FD")
    r["dumpcap_exit_status"] = p.wait(timeout=max(0.1, duration + 5 - (time.monotonic() - capture_started)))
    r["capture_end_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    r["dumpcap_reaped"] = True
    need(r["dumpcap_exit_status"] == 0, "dumpcap failed")
    r["rights_after_capture"] = rights()
    need(r["rights_after_capture"] == r["rights"], "Parent rights changed")
    need({name: os.readlink("/proc/self/ns/" + name) for name in r["ns"]} == r["ns"],
         "Parent namespaces changed")
    need(Path("/proc/self/mountinfo").read_text() == mountinfo_before,
         "Parent mount layout changed")
    r["fds_after_capture"] = descriptors()
    need({name: info["target"] for name, info in r["fds_after_capture"].items()} == r["fds"],
         "Unexpected parent descriptor after capture")
    remaining_monitors = []
    remaining_dumpcap = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if (proc / "comm").read_text().strip() == "dumpcap":
                remaining_dumpcap.append(int(proc.name))
            for name, info in descriptors(proc.name).items():
                if stat.S_ISCHR(info["mode"]) and info["rdev"] == host["node"]["st_rdev"]:
                    remaining_monitors.append({"pid": int(proc.name), "fd": name})
        except (FileNotFoundError, ProcessLookupError):
            continue
    r["remaining_monitor_fds_in_namespace"] = remaining_monitors
    r["remaining_dumpcap_in_namespace"] = remaining_dumpcap
    need(not remaining_monitors and not remaining_dumpcap,
         "Capture process or monitor descriptor remains")
    r["passed"] = True
except BaseException as error:
    r["failure"] = type(error).__name__ + ": " + str(error)
finally:
    if p is not None and p.poll() is None:
        r["capture_aborted"] = True
        p.send_signal(signal.SIGINT)
        try:
            p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=2)
        r["dumpcap_exit_status"] = p.returncode
    r["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    os.write(2, ("MEASUREMENT_B_RESULT_JSON " + json.dumps(r, sort_keys=True) + "\n").encode())
sys.exit(0 if r["passed"] else 1)
