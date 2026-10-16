#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One explicitly authorized bootstrap and motor-free input/IMU run.

Reuses Test 002's read-only input capture, client, guards, END and evidence code.
Import and offline tests never access a device. No module or sysfs writes here.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import time

from hardware_test_002 import Halt, Live, guard, process_state, ready_input, save_final_evidence
from preflight import snapshot

ROOT = Path(__file__).resolve().parents[2]
PHASES = (
    (0, "Ruhe: Controller flach ablegen, noch keine Eingaben."),
    (15, "15 Sekunden PUFFER: Controller aufnehmen. Eingaben beginnen erst bei der nächsten Ansage."),
    (30, "JETZT GAMEPAD: beide Sticks, beide Trigger, Tasten und Steuerkreuz testen. 35 Sekunden Zeit."),
    (65, "15 Sekunden PUFFER: Eingaben beenden, für langsames Kippen und Drehen bereithalten."),
    (80, "JETZT IMU: 20 Sekunden langsam um alle drei Achsen kippen/drehen; nicht schütteln."),
    (100, "10 Sekunden PUFFER: Controller wieder flach ablegen und loslassen."),
    (110, "SCHLUSSRUHE: weitere 10 Sekunden nichts berühren."),
)


def measure(backend):
    """120 seconds after confirmed session start, using only info/sample commands."""
    backend.start_client()
    until = backend.now() + 3
    started = False
    while backend.now() < until and not started:
        backend.check()
        started = any(m["type"] == "started" for m in backend.receive())
        if backend.exited():
            raise Halt("Session client exited before START confirmation")
        if not started:
            backend.wait(.01)
    if not started:
        raise Halt("START confirmation missing")
    backend.setup_input()
    start = backend.now()
    backend.record("measurement_started", {"seconds": 120, "motors": False})
    phase = 0
    next_query = 0
    sample_count = 0
    last_sample = start
    while backend.now() - start < 120:
        elapsed = backend.now() - start
        if phase < len(PHASES) and elapsed >= PHASES[phase][0]:
            backend.record("phase", {"offset": elapsed, "text": PHASES[phase][1]})
            print("\a" + PHASES[phase][1], flush=True)
            backend.input_snapshot(f"phase-{PHASES[phase][0]}")
            phase += 1
        backend.check()
        for msg in backend.receive():
            if msg["type"] == "sample":
                sample_count += 1
                last_sample = backend.now()
                backend.record("sample", msg)
            elif msg["type"] == "info":
                if (msg["pid"], msg["state"], msg["error"], msg["output"], msg["session"]) != (0x109c, 1, 0, 1, 1):
                    raise Halt("Unexpected runtime status")
                backend.record("info", msg)
            elif msg["type"] == "ended":
                raise Halt("Session ended before measurement completed")
        if backend.exited():
            raise Halt("Session client exited early")
        if backend.now() - last_sample > 2:
            raise Halt("No timely IMU snapshot received")
        if elapsed >= next_query:
            backend.send("info")
            backend.send("sample")
            next_query = elapsed + .25
        backend.wait(.01)
    backend.input_snapshot("final")
    return {"measurement_seconds": backend.now() - start, "imu_snapshots": sample_count,
            "input_events": backend.event_count, "full_imu_stream": False, "motor_pulses": 0}


def journal_cursor():
    p = subprocess.run(["/usr/bin/journalctl", "-k", "-b", "-n", "1", "--no-pager", "--output=json"],
                       capture_output=True, text=True, timeout=15)
    if p.returncode or p.stderr.strip() or not p.stdout.strip():
        raise Halt("Could not read current kernel cursor")
    return json.loads(p.stdout.strip())["__CURSOR"]


def execute(manifest_path, output):
    if os.geteuid() != 0 or not sys.stdin.isatty() or not sys.stdout.isatty():
        raise Halt("Separate approval, root and visible terminal required")
    manifest = json.loads(manifest_path.read_text())
    if manifest["scope"] != "one-native-bootstrap-input-imu-120-no-motors":
        raise Halt("Wrong authorization scope")
    for name, digest in manifest["sha256"].items():
        p = ROOT / name
        if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise Halt("Reviewed artifact changed: " + name)
    if (output.is_symlink() or not output.is_dir() or any(output.iterdir()) or
            output.resolve().parent != (ROOT / "build/hardware-tests").resolve() or
            stat.S_IMODE(output.stat().st_mode) != 0o700 or output.stat().st_uid != int(os.environ.get("SUDO_UID", -1))):
        raise Halt("Expected new private user-owned output directory")
    expected = manifest["before"]
    port = expected["port"]
    if expected["identity"]["idVendor"] != "3537" or expected["identity"]["idProduct"] != "100a" or expected["interfaces"][port+":1.0"]["driver"] != "gs_native":
        raise Halt("Expected native 100a baseline")

    def before_guard():
        if snapshot(port) != expected:
            raise Halt("Pre-bootstrap state changed")
        if any(process_state(expected["identity"]["busnum"], expected["identity"]["devnum"]).values()):
            raise Halt("Foreign USB access, Deadband or incomplete check")
        parameters = Path("/sys/module/gs_native/parameters")
        for name, value in manifest["parameters"].items():
            if (parameters/name).read_text().strip() != value:
                raise Halt("Module parameters changed")
        if Path("/sys/module/gs_native/srcversion").read_text().strip() != manifest["module_srcversion"]:
            raise Halt("Loaded module changed")

    before_guard()
    target = {"port": port, **{k: expected["identity"][k] for k in ("busnum", "devnum", "devpath")}}
    backend = Live({"target": target, "journal_cursor": journal_cursor()}, output, {"session_seconds": 125})
    result = {"passed": False, "bootstrap_succeeded": False, "end_confirmed": False,
              "xpad_restored": False, "automatic_restore": False}
    boot = None
    try:
        backend.write_object("manifest.json", manifest)
        backend.write_object("before.json", expected)
        backend.start_journal()
        print("Deadband geschlossen lassen. Keine Motorimpulse. Wenn bereit: bereit + Enter (Groß-/Kleinschreibung egal). Danach 15 Sekunden Countdown.", flush=True)
        if not select.select([sys.stdin], [], [], 300)[0] or not ready_input(sys.stdin.readline()):
            raise Halt("Local readiness missing; no bootstrap")
        for remaining in range(15, 0, -1):
            before_guard()
            backend.check_journal()
            print(f"Start ohne Deadband in {remaining} Sekunden. Controller ruhig halten, keine Guide-Taste.", flush=True)
            time.sleep(1)
        before_guard()
        backend.check_journal()
        command = [str(ROOT/"build/gsnative-ctl"), "bootstrap", "/dev/gsnative-"+port+":1.0", "--handoff-xpad"]
        backend.record("bootstrap_start", {"argv": command})
        print("\aJETZT: nativer Start 100a → 109c. Bitte ruhig halten.", flush=True)
        with (output/"bootstrap.stdout.txt").open("xb") as out, (output/"bootstrap.stderr.txt").open("xb") as err:
            for stream in (out, err):
                os.fchmod(stream.fileno(), 0o600)
                os.fchown(stream.fileno(), *backend.owner)
            boot = subprocess.Popen(command, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
            deadline = time.monotonic() + 40
            while boot.poll() is None:
                backend.check_journal()
                if time.monotonic() > deadline:
                    raise Halt("Bootstrap host supervision deadline")
                time.sleep(.02)
        backend.record("bootstrap_exit", {"returncode": boot.returncode})
        if boot.returncode:
            raise Halt("Native bootstrap failed; see bootstrap logs")
        text = (output/"bootstrap.stdout.txt").read_text()
        if "bootstrap state=7 error=0" not in text or "Native startup completed." not in text:
            raise Halt("Successful bootstrap status missing")
        result["bootstrap_succeeded"] = True
        after = snapshot(port)
        target.update({k: after["identity"][k] for k in ("busnum", "devnum", "devpath")})
        guard(after, target, "gs_native")
        backend.write_object("after-bootstrap.json", after)
        capabilities = []
        for node in (Path("/sys/bus/usb/devices")/(port+":1.0")).glob("input/input*"):
            capabilities.append({"sysfs_input": node.name, "name": (node/"name").read_text().strip(),
                                 "event_nodes": [p.name for p in node.glob("event*")],
                                 "key_bitmap": (node/"capabilities/key").read_text().strip(),
                                 "abs_bitmap": (node/"capabilities/abs").read_text().strip()})
        backend.write_object("input-capabilities.json", capabilities)
        backend.check_journal()
        backend.assert_released()
        result.update(measure(backend))
        result["passed"] = True
    except (Exception, SystemExit) as error:
        result["failure"] = f"{type(error).__name__}: {error}"
        print("STOPP: " + result["failure"], flush=True)
    finally:
        if boot is not None and boot.poll() is None:
            boot.send_signal(signal.SIGTERM)  # Kernel cancels the existing request; never retry it.
            try:
                boot.wait(timeout=3)
            except subprocess.TimeoutExpired:
                result["bootstrap_process_still_running"] = boot.pid
                result["passed"] = False
        if backend.child is not None:
            result["end_confirmed"] = backend.finish()
            result["passed"] &= result["end_confirmed"]
        elif result["bootstrap_succeeded"]:
            # No extra START after a failed guard. Existing finite runtime is the limit.
            result["runtime_watchdog_only"] = True
            result["passed"] = False
        if result.get("bootstrap_process_still_running"):
            # A still-running child may append to its files. Do not seal a false final hash.
            result["evidence_complete"] = False
            backend.write_object("result.json", result)
            if backend.journal is not None:
                backend.journal.terminate()
                backend.journal.wait(timeout=3)
                backend.journal.stdout.close()
                backend.journal.stderr.close()
            for stream in backend.logs.values():
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()
        else:
            save_final_evidence(backend, result)
        print("COMPLETED " + json.dumps(result), flush=True)
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "execute-authorized":
        raise SystemExit("Usage (separate approval): hardware_test_003.py execute-authorized MANIFEST OUTPUT")
    raise SystemExit(execute(Path(sys.argv[2]), Path(sys.argv[3])))
