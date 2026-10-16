#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded test-002 coordinator. No live backend is constructed by simulation.

execute-authorized is a future hardware operation, requiring explicit human
approval of the selected handover, START, bounded pulses and END. It never loads,
unloads, resets, changes identity, starts Deadband, or restores a driver.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/HARDWARE_TEST_002_PHASES.json"
COMPARISON_PLAN = ROOT / "docs/native-motor-comparison-plan.json"
COMPARISON_VARIANT = "motor-comparison-300"
INFO = re.compile(r"pid=([0-9a-f]{4}) state=(\d+) error=(-?\d+) OUT=(\d+) session=(\d+) pad=(\d+) imu=(\d+) rejected=(\d+) experimental_accel=(\d+)/(\d+) LSB/g")
SAMPLE = re.compile(r"host_monotonic_ns=(\d+) sample=(\d+) gyro_raw=\[(-?\d+),(-?\d+),(-?\d+)\] accel_raw=\[(-?\d+),(-?\d+),(-?\d+)\] experiment_valid=(\d+) accel_um_s2=\[(-?\d+),(-?\d+),(-?\d+)\]")


class Halt(RuntimeError):
    pass


def ready_input(text):
    """Human readiness accepts normal capitalization and surrounding whitespace."""
    return text.strip().casefold() == "bereit"


def validate_plan(plan):
    # Do not turn an editable schedule into an arbitrary command channel.
    if plan.get("variant") == COMPARISON_VARIANT:
        phases = [(0, 5, "initialization"), (5, 30, "comparison_preparation"),
                  (30, 90, "left_grip"), (90, 150, "right_grip"),
                  (150, 210, "left_trigger"), (210, 270, "right_trigger"),
                  (270, 300, "final_rest")]
        expected = [(base + offset, motor, 100, 1000)
                    for base, motor in ((30, "left"), (90, "right"), (150, "lt"), (210, "rt"))
                    for offset in (15, 21, 27)]
        required = {"vid": "3537", "pid": "109c", "interface_number": 0,
                    "session_seconds": 300, "kernel_session_limit_ms": 315000,
                    "countdown_before_handover_seconds": 15, "imu_snapshot_interval_ms": 20,
                    "repeat": False, "usbmon_capture_included": True,
                    "explicit_stop_seconds_after_pulse_ack": 1.0,
                    "minimum_pause_seconds_after_stop_ack": 5.0,
                    "input_cue_seconds_before_pulse": 5,
                    "input_required_from_pulse_until_stop_ack": True,
                    "maximum_event_lateness_seconds": .5,
                    "nominal_times_may_shift_for_confirmed_stop_and_pause": True,
                    "recorder_must_be_ready_alive_and_have_remaining_time": True,
                    "capture_return_margin_seconds": 30}
        if any(plan.get(k) != v for k, v in required.items()):
            raise Halt("Unexpected bounded motor comparison settings")
        if [(p["start"], p["end"], p["name"]) for p in plan["phases"]] != phases:
            raise Halt("Unexpected motor comparison phase boundaries")
        if [(p["at_seconds"], p["motor"], p["percent"], p["duration_ms"])
                for p in plan["pulses"]] != expected:
            raise Halt("Only the twelve specified comparison pulses are supported")
        return
    if plan.get("variant") not in (None, "legacy-120"):
        raise Halt("Unknown test variant")
    phases = [(0, 5), (5, 20), (20, 30), (30, 60), (60, 70), (70, 85),
              (85, 90), (90, 95), (95, 100), (100, 105), (105, 110), (110, 120)]
    if (plan["vid"], plan["pid"], plan["interface_number"], plan["session_seconds"],
            plan["kernel_session_limit_ms"]) != ("3537", "109c", 0, 120, 135000):
        raise Halt("Unexpected test identity/duration")
    if [(p["start"], p["end"]) for p in plan["phases"]] != phases:
        raise Halt("Unexpected phase boundaries")
    expected = [(91, "left", 100, 400), (96, "right", 100, 400),
                (101, "lt", 100, 400), (106, "rt", 100, 400)]
    if [(p["at_seconds"], p["motor"], p["percent"], p["duration_ms"])
            for p in plan["pulses"]] != expected:
        raise Halt("Only the four approved isolated pulses are supported")
    if (plan["countdown_before_handover_seconds"] != 15 or
            plan["imu_snapshot_interval_ms"] != 20 or plan["repeat"] or
            plan["usbmon_capture_included"] or
            plan["explicit_stop_seconds_after_each_pulse"] != .6):
        raise Halt("Unexpected countdown, sample cadence, repeat or stop")


def guard(snapshot, target, driver):
    identity = snapshot["identity"]
    expected = {"idVendor": "3537", "idProduct": "109c", "busnum": target["busnum"],
                "devnum": target["devnum"], "devpath": target["devpath"],
                "bConfigurationValue": "1"}
    if snapshot["port"] != target["port"] or any(identity.get(k) != v for k, v in expected.items()):
        raise Halt("USB identity/address/port changed")
    port = target["port"]
    interfaces = snapshot["interfaces"]
    if set(interfaces) != {port + ":1.0", port + ":1.1"}:
        raise Halt("Unexpected interface set")
    for number in (0, 1):
        iface = interfaces[port + f":1.{number}"]
        if (iface["bInterfaceNumber"], iface["bAlternateSetting"], iface["bInterfaceClass"],
                iface["bInterfaceSubClass"], iface["bInterfaceProtocol"]) != (f"0{number}", "0", "ff", "47", "d0"):
            raise Halt("Unexpected 109c interface descriptors")
        if iface["driver"] != (driver if number == 0 else None):
            raise Halt("Unexpected driver owner")
        endpoints = iface["endpoints"]
        if set(endpoints) != ({"ep_02", "ep_82"} if number == 0 else set()):
            raise Halt("Unexpected endpoint set")
        for name, ep in endpoints.items():
            if (ep["bEndpointAddress"] != name[3:] or int(ep["bmAttributes"], 16) & 3 != 3 or
                    int(ep["wMaxPacketSize"], 16) != 64 or not int(ep["bInterval"], 16)):
                raise Halt("Unexpected interrupt endpoint")
    if not snapshot["industrialio_already_loaded"] or not snapshot["gs_native_loaded"]:
        raise Halt("Required pre-approved modules are not loaded")


def parse_line(line):
    match = INFO.fullmatch(line)
    if match:
        values = [int(match[1], 16)] + [int(v) for v in match.groups()[1:]]
        return {"type": "info", **dict(zip(("pid", "state", "error", "output", "session", "pad", "imu", "rejected", "accel_num", "accel_den"), values))}
    match = SAMPLE.fullmatch(line)
    if match:
        v = [int(x) for x in match.groups()]
        return {"type": "sample", "timestamp_ns": v[0], "number": v[1],
                "gyro_raw": v[2:5], "accel_raw": v[5:8],
                "experimental_accel_valid": v[8], "experimental_accel_um_s2": v[9:12]}
    if line.startswith("START_CALL monotonic_ns="):
        return {"type": "start_call", "timestamp_ns": int(line.split("=", 1)[1])}
    exact = {
        "Session started. No motor runs automatically.": "started",
        "One motor pulse accepted; bounded by kernel deadline and explicit stop.": "pulse",
        "STOP accepted; zero motor transfer confirmed.": "stop",
        "Session ended; zero motor packet confirmed by USB transfer (not mechanical feedback).": "ended",
        "Commands: info | sample | pulse lt|rt|left|right PERCENT MS | stop | quit": "help",
    }
    if line not in exact:
        raise Halt("Unexpected client output")
    return {"type": exact[line]}


def kernel_warning(record):
    """No implicit ENOENT exception: a new kernel warning stops this test."""
    try:
        priority = int(record["PRIORITY"])
    except (KeyError, TypeError, ValueError) as error:
        raise Halt("Kernel journal priority missing/invalid") from error
    if not 0 <= priority <= 7 or not isinstance(record.get("MESSAGE"), str):
        raise Halt("Unexpected kernel journal entry")
    return priority <= 4


def schedule(plan):
    validate_plan(plan)
    events = [(p["start"], "phase", p["name"]) for p in plan["phases"]]
    if plan.get("variant") == COMPARISON_VARIANT:
        for number, p in enumerate(plan["pulses"]):
            cue = f"{p['motor']}:{number % 3 + 1}"
            events += [(p["at_seconds"] - 5, "input_prepare", cue),
                       (p["at_seconds"], "command", f"pulse {p['motor']} 100 1000"),
                       (p["at_seconds"] + 1, "command", "stop")]
        # Stop acknowledgements, not an unverified timer, announce feedback/rest.
        return sorted(events, key=lambda x: (x[0], x[1]))
    events += [(p["start"] - 5, "warning", p["name"]) for p in plan["phases"] if p["start"] >= 5]
    for p in plan["pulses"]:
        events += [(p["at_seconds"], "command", f"pulse {p['motor']} 100 400"),
                   (p["at_seconds"] + .6, "command", "stop"),
                   (p["at_seconds"] + .7, "command", "info")]
    return sorted(events, key=lambda x: (x[0], x[1]))


def capture_guard(backend, plan, remaining, stage):
    """An injected read-only monitor verifies an already running isolated recorder."""
    if plan is None or not plan["usbmon_capture_included"]:
        return
    required = max(0, remaining) + plan["capture_return_margin_seconds"]
    try:
        backend.capture_check(required, stage)
    except Halt:
        raise
    except Exception as error:
        raise Halt(f"Recorder guard failed at {stage}: {error}") from error


def handover(backend, target, plan=None):
    """Exactly two writes, with a fresh guard between; never retry/restore."""
    backend.assert_released()
    guard(backend.snapshot(), target, "xpad")
    capture_guard(backend, plan, plan["session_seconds"] + 2 if plan else 0, "before-unbind")
    began = backend.now()
    backend.change("xpad", "unbind")
    guard(backend.snapshot(), target, None)
    if backend.now() - began > 2:
        raise Halt("Handover deadline exceeded before native bind")
    capture_guard(backend, plan, plan["session_seconds"] + 2 if plan else 0, "before-bind")
    if backend.now() - began > 2:
        raise Halt("Handover deadline exceeded during recorder verification")
    backend.assert_released()
    backend.change("gs_native", "bind")
    guard(backend.snapshot(), target, "gs_native")
    capture_guard(backend, plan, plan["session_seconds"] if plan else 0, "before-start")
    if backend.now() - began > 2:
        raise Halt("Handover deadline exceeded before START")
    backend.start_client()


def run_session(backend, plan):
    """Single client owns the ABI; all sampling and pulse commands use its stdin."""
    events = schedule(plan)
    comparison = plan.get("variant") == COMPARISON_VARIANT
    duration, expected_pulses = plan["session_seconds"], len(plan["pulses"])
    index, pending, pending_since = 0, None, 0
    t0, started, ended = None, False, False
    first_info, last_info, last_sample = None, None, None
    last_numbers = (0, 0)
    last_pad_progress = None
    sample_due = info_due = 0
    stop_confirmed, pulses = True, 0
    pulse_acks = stop_acks = 0
    pulse_ack_time = last_stop_ack = None
    pulse_counts = None
    prestart_deadline = backend.now() + 3
    try:
        while True:
            now = backend.now()
            capture_guard(backend, plan, duration if t0 is None else duration - (now - t0), "session")
            if t0 is None or now - t0 < duration:
                backend.check()
            for message in backend.receive():
                # Messages may be generated while check()/receive() runs.
                # Compare against receipt time, never the older loop timestamp.
                now = backend.now()
                kind = message["type"]
                backend.record(kind, message)
                if kind == "start_call":
                    if t0 is not None:
                        raise Halt("Duplicate START")
                    t0 = message["timestamp_ns"] / 1e9
                    if not 0 <= now - t0 <= 1:
                        raise Halt("Invalid START timestamp")
                elif kind == "started":
                    if t0 is None or started:
                        raise Halt("Unexpected session start acknowledgement")
                    started = True
                    backend.setup_input()
                elif kind == "info":
                    if (message["pid"], message["state"], message["error"], message["output"],
                            message["accel_num"], message["accel_den"]) != (0x109c, 1, 0, 1, 8192, 1):
                        raise Halt("Client runtime/identity/calibration mismatch")
                    if started and message["session"] != 1:
                        raise Halt("Session ended unexpectedly")
                    counts = (message["pad"], message["imu"])
                    if counts[0] < last_numbers[0] or counts[1] < last_numbers[1]:
                        raise Halt("Packet counters went backwards")
                    if counts[0] > last_numbers[0]:
                        last_pad_progress = now
                    last_numbers, last_info = counts, now
                    if started and first_info is None:
                        first_info = counts
                elif kind == "sample":
                    if not started or not 0 <= now - message["timestamp_ns"] / 1e9 <= 1:
                        raise Halt("Stale/future IMU sample")
                    if message["number"] <= 0 or any(not -32768 <= v <= 32767 for v in message["gyro_raw"] + message["accel_raw"]):
                        raise Halt("Invalid raw IMU sample")
                    if last_sample and (message["number"] < last_sample["number"] or
                                        message["timestamp_ns"] < last_sample["timestamp_ns"]):
                        raise Halt("IMU sequence/time went backwards")
                    last_sample = message
                elif kind == "stop":
                    if pending != "stop":
                        raise Halt("Unsolicited stop acknowledgement")
                    stop_confirmed = True
                    stop_acks += 1
                    last_stop_ack = now
                    if comparison:
                        if pulse_counts is None or any(a <= b for a, b in zip(last_numbers, pulse_counts)):
                            raise Halt("Gamepad/IMU did not advance during the motor pulse")
                        backend.record("pulse_data_progress", {"before": pulse_counts, "after": last_numbers})
                        backend.cue("feedback", f"{pulses}:12")
                        pulse_counts = None
                elif kind == "pulse":
                    if pending != "pulse":
                        raise Halt("Unsolicited pulse acknowledgement")
                    pulse_acks += 1
                    pulse_ack_time = now
                    if comparison:
                        backend.cue("pulse", f"{pulses}:12")
                elif kind == "ended":
                    ended = True
                    if t0 is None or backend.now() - t0 < duration:
                        raise Halt("Client ended before planned session boundary")
                if pending == kind:
                    pending = None
            now = backend.now()
            if backend.exited() and not ended:
                raise Halt("Client exited early")
            if not started:
                if now >= prestart_deadline:
                    raise Halt("START acknowledgement timed out")
                backend.wait(.01)
                continue
            elapsed = now - t0
            if elapsed >= duration:
                if (not stop_confirmed or pulses != expected_pulses or pulse_acks != expected_pulses or
                        stop_acks != expected_pulses or not last_sample or first_info is None):
                    raise Halt("Incomplete motor start/stop/data run")
                if last_numbers[0] <= first_info[0] or last_numbers[1] <= first_info[1]:
                    raise Halt("Gamepad/IMU counters did not advance")
                break
            if pending and now - pending_since > .75:
                raise Halt("Client command acknowledgement timed out")
            if elapsed >= 5 and (last_info is None or now - last_info > 1):
                raise Halt("No current runtime status")
            if elapsed >= 6 and (last_sample is None or now - last_sample["timestamp_ns"] / 1e9 > 1):
                raise Halt("No current IMU data")
            input_required = (pulse_counts is not None if comparison else 90 <= elapsed < 110)
            if input_required and (last_pad_progress is None or now - last_pad_progress > 1):
                backend.record("motor_input_prerequisite_missing", {
                    "elapsed": elapsed, "pad_packets": last_numbers[0],
                    "seconds_since_progress": None if last_pad_progress is None else now - last_pad_progress})
                raise Halt("No recent gamepad changes for motor test; this alone does not prove a transport failure")
            while index < len(events) and events[index][0] <= elapsed:
                at, kind, value = events[index]
                # Re-read time after checks and cues: no compressed catch-up sequence.
                now = backend.now()
                elapsed = now - t0
                if elapsed - at > .5:
                    raise Halt("Late phase/command; no catch-up or compressed schedule")
                if kind == "command":
                    if pending:
                        break
                    if comparison and value == "stop":
                        if pulse_ack_time is None:
                            raise Halt("STOP without an acknowledged pulse")
                        if now < pulse_ack_time + plan["explicit_stop_seconds_after_pulse_ack"]:
                            break
                    if value.startswith("pulse"):
                        if not stop_confirmed or last_sample is None or last_info is None or now - last_info > .5:
                            raise Halt("Motor prerequisites not satisfied")
                        if comparison:
                            if last_stop_ack is not None and now < last_stop_ack + plan["minimum_pause_seconds_after_stop_ack"]:
                                break
                            if last_pad_progress is None or now - last_pad_progress > 1:
                                raise Halt("No recent gamepad changes in announced input window")
                            capture_guard(backend, plan, duration - elapsed, "before-pulse")
                            now = backend.now()
                            elapsed = now - t0
                            if elapsed - at > .5:
                                raise Halt("Late motor command after recorder verification; no catch-up")
                            pulse_counts = last_numbers
                        stop_confirmed = False
                        pulses += 1
                    backend.send(value)
                    pending, pending_since = value.split()[0], now
                else:
                    backend.cue(kind, value)
                backend.record("scheduled", {"at": at, "kind": kind, "value": value, "elapsed": elapsed})
                index += 1
            if pending is None:
                command = None
                if now >= info_due:
                    command, info_due = "info", now + .25
                elif elapsed >= 5 and now >= sample_due:
                    command, sample_due = "sample", now + .02
                if command:
                    backend.send(command)
                    pending, pending_since = command, now
            backend.wait(.005)
        backend.record("run_finished", {"pulses": pulses, "pulse_acknowledgements": pulse_acks,
            "stop_acknowledgements": stop_acks, "physical_motor_feedback": "requires user confirmation"})
    finally:
        # Also on pre-START failure: close stdin. No new START or bind here.
        ended = backend.finish()
        backend.record("end_confirmation", {"usb_zero_confirmed": ended})
    if not ended:
        raise Halt("Final zero transfer not confirmed")
    return {"passed_transport_run": True, "pulses": pulses, "pulse_acknowledgements": pulse_acks,
            "stop_acknowledgements": stop_acks, "full_imu_stream": False,
            "motor_perception_confirmed": False, "xpad_restored": False}


def process_state(bus, address):
    """Read proc metadata only; permissions/gaps are a hard failure for handover."""
    usb = f"/dev/bus/usb/{int(bus):03d}/{int(address):03d}"
    result = {"deadband": [], "usb_handles": [], "unreadable": []}
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            argv = (proc / "cmdline").read_bytes().decode(errors="replace").split("\0")
            if any(Path(arg).name.lower() in ("deadband", "deadband.py") or
                   arg.startswith("/usr/share/deadband/") for arg in argv if arg):
                result["deadband"].append(int(proc.name))
            for fd in (proc / "fd").iterdir():
                try:
                    if os.readlink(fd).removesuffix(" (deleted)") == usb:
                        result["usb_handles"].append({"pid": int(proc.name), "fd": fd.name})
                except FileNotFoundError:
                    continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            result["unreadable"].append(int(proc.name))
    return result


class Live:
    """Construct only after execute-authorized, root, visible tty and manifest checks."""
    def __init__(self, manifest, output, plan, capture=None):
        from preflight import snapshot
        self.read_snapshot = snapshot
        self.target = manifest["target"]
        self.plan, self.capture = plan, capture
        self.client = ROOT / "build/gsnative-ctl"
        self.child = self.input = None
        self.journal = None
        self.journal_buffer = b""
        self.journal_cursor = manifest["journal_cursor"]
        self.ended_observed = False
        self.finish_result = None
        self.buffers = {"stdout": b"", "stderr": b""}
        self.next_guard = 0
        self.event_count = 0
        self.logs = {}
        self.output = output
        self.owner = (output.stat().st_uid, output.stat().st_gid)
        for name in ("events", "input", "imu", "motors", "kernel", "client.stdout", "client.stderr"):
            path = output / (name + (".txt" if "." in name else ".jsonl"))
            stream = path.open("x", encoding="utf-8")
            os.fchmod(stream.fileno(), 0o600)
            os.fchown(stream.fileno(), *self.owner)
            self.logs[name] = stream

    def now(self):
        return time.monotonic()

    def capture_check(self, required_remaining_seconds, stage):
        if self.capture is None:
            raise Halt("An independently verified running recorder is required")
        self.capture.check(required_remaining_seconds, stage)

    def snapshot(self):
        return self.read_snapshot(self.target["port"])

    def record(self, kind, data):
        name = "imu" if kind == "sample" else "input" if kind in ("input", "input_snapshot") else "motors" if kind in ("pulse", "stop") else "events"
        self.logs[name].write(json.dumps({"kind": kind, "host_monotonic_ns": time.monotonic_ns(),
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "data": data}, separators=(",", ":")) + "\n")
        if kind not in ("input", "sample"):
            self.logs[name].flush()

    def assert_released(self):
        self.check_journal()
        state = process_state(self.target["busnum"], self.target["devnum"])
        if any(state.values()):
            raise Halt("Deadband/USB handle remains or process scan incomplete")

    def start_journal(self):
        self.journal = subprocess.Popen(["/usr/bin/journalctl", "-k", "-b", "--follow",
            "--no-pager", "--output=json", "--after-cursor=" + self.journal_cursor],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        for stream in (self.journal.stdout, self.journal.stderr):
            os.set_blocking(stream.fileno(), False)

    def check_journal(self):
        if self.journal is None:
            raise Halt("Kernel log monitor was not started")
        for name in ("stderr", "stdout"):
            try:
                data = os.read(getattr(self.journal, name).fileno(), 65536)
            except BlockingIOError:
                continue
            if not data:
                continue
            if name == "stderr":
                self.record("kernel_log_error", {"message": data.decode(errors="replace")})
                raise Halt("Kernel log monitor error")
            self.journal_buffer += data
            if len(self.journal_buffer) > 1_048_576:
                raise Halt("Kernel log monitor overflow")
            warning = False
            while b"\n" in self.journal_buffer:
                line, self.journal_buffer = self.journal_buffer.split(b"\n", 1)
                item = json.loads(line)
                self.logs["kernel"].write(json.dumps(item) + "\n")
                warning |= kernel_warning(item)
            self.logs["kernel"].flush()
            if warning:
                raise Halt("New kernel warning; see private kernel.jsonl")
        if self.journal.poll() is not None:
            raise Halt("Kernel log monitor exited")

    def change(self, driver, action):
        if (driver, action) not in (("xpad", "unbind"), ("gs_native", "bind")):
            raise Halt("Operation outside handover allowlist")
        path = Path("/sys/bus/usb/drivers") / driver / action
        # Exactly one write. No retries, recovery, identity command or shell.
        fd = os.open(path, os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            value = (self.target["port"] + ":1.0").encode()
            if os.write(fd, value) != len(value):
                raise Halt("Short sysfs write")
        finally:
            os.close(fd)
        self.record("binding_action", {"driver": driver, "action": action})

    def start_client(self):
        node = "/dev/gsnative-" + self.target["port"] + ":1.0"
        self.child = subprocess.Popen([str(self.client), "session", node, str(self.plan["session_seconds"])],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        for stream in (self.child.stdout, self.child.stderr):
            os.set_blocking(stream.fileno(), False)

    def open_input(self):
        from evdev import InputDevice
        iface = Path("/sys/bus/usb/devices") / (self.target["port"] + ":1.0")
        nodes = sorted(iface.glob("input/input*/event*"))
        if len(nodes) != 1:
            raise Halt("Expected one native input node")
        node = Path("/dev/input") / nodes[0].name
        if node.is_symlink() or not stat.S_ISCHR(node.lstat().st_mode):
            raise Halt("Unexpected evdev node type")
        dev = InputDevice(str(node), readonly=True)
        self.input = dev
        expected = tuple(int(x) for x in (nodes[0] / "dev").read_text().strip().split(":"))
        rdev = os.fstat(dev.fd).st_rdev
        if ((os.major(rdev), os.minor(rdev)) != expected or
                dev.name not in ("GameSir G7 Pro", "GameSir G7 Pro native TEST gamepad") or
                (dev.info.bustype, dev.info.vendor, dev.info.product) != (3, 0x3537, 0x109c)):
            raise Halt("Opened evdev identity/ancestry mismatch")
        guard(self.snapshot(), self.target, "gs_native")
        self.input_snapshot("initial")

    def setup_input(self):
        self.open_input()

    def input_snapshot(self, label):
        self.record("input_snapshot", {"label": label, "axes": {str(k): self.input.absinfo(k)._asdict() for k in (0, 1, 3, 4, 2, 5, 16, 17)}, "active_keys": self.input.active_keys()})

    def check(self):
        self.check_journal()
        if self.now() >= self.next_guard:
            guard(self.snapshot(), self.target, "gs_native")
            self.assert_released()
            self.next_guard = self.now() + .25
        if self.input:
            if select.select([self.input.fd], [], [], 0)[0]:
                for ev in self.input.read():
                    self.event_count += 1
                    self.record("input", {"sec": ev.sec, "usec": ev.usec, "type": ev.type, "code": ev.code, "value": ev.value})
                    if (ev.type, ev.code) == (0, 3) or self.event_count > 2_000_000:
                        raise Halt("Input SYN_DROPPED or flood")

    def receive(self):
        if not self.child:
            return []
        messages = []
        for name in ("stdout", "stderr"):
            stream = getattr(self.child, name)
            try:
                data = os.read(stream.fileno(), 65536)
            except BlockingIOError:
                continue
            if data:
                self.logs["client." + name].write(data.decode("utf-8", errors="replace"))
                if name == "stderr":
                    raise Halt("Client error; see private stderr log")
                self.buffers[name] += data
                if len(self.buffers[name]) > 65536:
                    raise Halt("Client output overflow")
                while b"\n" in self.buffers[name]:
                    line, self.buffers[name] = self.buffers[name].split(b"\n", 1)
                    message = parse_line(line.decode("ascii"))
                    if message["type"] == "ended":
                        self.ended_observed = True
                    messages.append(message)
        return messages

    def send(self, command):
        self.child.stdin.write((command + "\n").encode("ascii"))
        self.record("command_sent", {"command": command})

    def cue(self, kind, name):
        if self.plan.get("variant") == COMPARISON_VARIANT:
            motors = {"left": "linker Griff", "right": "rechter Griff", "lt": "linker Trigger", "rt": "rechter Trigger"}
            phase_motors = {"left_grip": "left", "right_grip": "right", "left_trigger": "lt", "right_trigger": "rt"}
            if kind == "input_prepare":
                motor, number = name.split(":")
                text = f"{motors[motor]}, Impuls {number}/3 in etwa 5 Sekunden: einen Stick leicht bewegen, bis nach dem dritten STOPP die PAUSE angesagt wird."
            elif kind == "pulse":
                text = f"Impuls {name.split(':')[0]}/12 bestätigt: 1 Sekunde; Stick leicht weiter bewegen."
            elif kind == "feedback":
                if int(name.split(":")[0]) % 3:
                    text = "STOPP bestätigt. Mindestens 5 Sekunden Motorpause; Stick bis zur PAUSE nach dem dritten Impuls leicht weiter bewegen."
                else:
                    text = "PAUSE: dritter STOPP bestätigt. Stick loslassen, Vibration beurteilen; auf den nächsten Motorblock warten."
            elif name in phase_motors:
                text = f"Vorbereitung: {motors[phase_motors[name]]}. Erster von drei 1-Sekunden-Impulsen in 15 Sekunden; auf die Eingabeansagen warten."
            else:
                text = {"initialization": "Initialisierung; ruhig halten.",
                        "comparison_preparation": "Vorbereitung und Ruhe: bequem halten, noch keine Eingaben. Erster Motorblock bei 30 Sekunden.",
                        "final_rest": "SCHLUSSRUHE: alle Motorprüfungen beendet. Stick loslassen, ablegen; 30 Sekunden Ruhe."}[name]
            print("\a" + text, flush=True)
            if kind == "phase" and self.input:
                self.input_snapshot(name)
            return
        text = {"initialization": "Initialisierung; ruhig halten", "initial_rest": "RUHE: flach ablegen, nichts berühren",
                "rest_to_input_buffer": "PUFFER: aufnehmen; noch keine Eingaben", "gamepad": "TEST: Sticks, Trigger, D-Pad und Tasten",
                "input_to_imu_buffer": "PUFFER: Eingaben beenden; für IMU und durchgehende Stickbewegung bereithalten",
                "imu_movement": "IMU: langsam kippen/drehen; ab jetzt einen Stick leicht im Kreis bewegen, bis SCHLUSSRUHE",
                "imu_to_motor_buffer": "PUFFER: bequem halten; Stick weiter leicht im Kreis bewegen",
                "left_grip": "Linker Griffmotor; Stick weiter bewegen", "right_grip": "Rechter Griffmotor; Stick weiter bewegen",
                "left_trigger": "Linker Triggermotor; Stick weiter bewegen", "right_trigger": "Rechter Triggermotor; Stick weiter bewegen",
                "final_rest": "SCHLUSSRUHE: Stick loslassen, ablegen, nichts berühren"}[name]
        print("\a" + ("In 5 Sekunden: " if kind == "warning" else "JETZT: ") + text, flush=True)
        if kind == "phase" and self.input:
            self.input_snapshot(name)

    def exited(self):
        return self.child is not None and self.child.poll() is not None

    def wait(self, seconds):
        time.sleep(seconds)

    def finish(self):
        if self.finish_result is not None:
            return self.finish_result
        confirmed = self.ended_observed
        if self.child:
            try:
                if self.child.poll() is None:
                    self.send("quit")
                self.child.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            until = self.now() + 2
            while self.now() < until:
                try:
                    confirmed |= any(m["type"] == "ended" for m in self.receive())
                except (Halt, OSError):
                    pass
                if self.exited():
                    break
                self.wait(.01)
            if not self.exited():
                self.child.terminate()  # Client handler performs END; no SIGKILL/retry.
                try:
                    self.child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.record("error", {"message": "Client did not exit after SIGTERM; stop and inspect; no forced kill"})
            try:
                confirmed |= any(m["type"] == "ended" for m in self.receive())
            except (Halt, OSError):
                pass
            confirmed = confirmed and self.child.returncode == 0
        if self.input:
            self.input.close()
            self.input = None
        try:
            self.check_journal()
        except (Halt, OSError, ValueError) as error:
            self.record("kernel_log_error_at_end", {"message": str(error)})
            confirmed = False
        self.finish_result = confirmed
        return confirmed

    def close_logs(self):
        monitor_error = None
        if self.journal is not None:
            # This only stops our read-only log subprocess, never a driver.
            try:
                if self.journal.poll() is None:
                    self.journal.terminate()
                    self.journal.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired) as error:
                monitor_error = error
                self.record("kernel_monitor_close_error", {"message": str(error)})
            finally:
                self.journal.stdout.close()
                self.journal.stderr.close()
        for stream in self.logs.values():
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
        paths = sorted(p for p in self.output.iterdir() if p.is_file() and p.name != "SHA256SUMS")
        sums = self.output / "SHA256SUMS"
        with sums.open("x") as out:
            os.fchmod(out.fileno(), 0o600)
            os.fchown(out.fileno(), *self.owner)
            for path in paths:
                out.write(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n")
            out.flush()
            os.fsync(out.fileno())
        for line in sums.read_text().splitlines():
            digest, name = line.split("  ", 1)
            if hashlib.sha256((self.output / name).read_bytes()).hexdigest() != digest:
                raise Halt("Evidence checksum verification failed")
        if monitor_error is not None:
            raise Halt("Kernel log monitor did not close cleanly; evidence saved") from monitor_error

    def write_object(self, name, value):
        with (self.output / name).open("x") as stream:
            os.fchmod(stream.fileno(), 0o600)
            os.fchown(stream.fileno(), *self.owner)
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())


def save_final_evidence(backend, result):
    """Even a failed metadata read must not discard or leave logs unclosed."""
    after = {"unavailable": True, "message": "Final snapshot interrupted"}
    try:
        try:
            after = backend.snapshot()
        except (Exception, SystemExit) as error:
            after = {"unavailable": True, "type": type(error).__name__, "message": str(error)}
        finally:
            backend.write_object("after.json", after)
            backend.write_object("result.json", result)
    finally:
        backend.close_logs()


def execute(manifest_path, output, plan):
    # Flags/manifests describe scope; only the actual human may authorize execution.
    validate_plan(plan)
    comparison = plan.get("variant") == COMPARISON_VARIANT
    plan_path = COMPARISON_PLAN if comparison else PLAN
    if os.geteuid() != 0 or not sys.stdin.isatty() or not sys.stdout.isatty():
        raise Halt("Future execution needs explicitly approved root operation in a visible terminal")
    manifest = json.loads(manifest_path.read_text())
    scope = ("native-motor-comparison-300-handover-twelve-pulses-capture-end-only" if comparison
             else "test002-handover-start-four-pulses-end-only")
    if manifest.get("scope") != scope:
        raise Halt("Wrong manifest scope")
    if comparison and (manifest.get("variant") != COMPARISON_VARIANT or
                       manifest.get("plan") != str(plan_path.relative_to(ROOT)) or
                       manifest.get("session_seconds") != plan["session_seconds"]):
        raise Halt("Manifest variant/plan/session mismatch")
    if not isinstance(manifest.get("journal_cursor"), str) or not re.fullmatch(r"[a-zA-Z0-9=;_-]+", manifest["journal_cursor"]):
        raise Halt("Fresh pre-approved kernel journal cursor required")
    target = manifest["target"]
    if not re.fullmatch(r"\d+-\d+(?:\.\d+)*", target["port"]) or any(not str(target[k]).isdigit() for k in ("busnum", "devnum", "devpath")):
        raise Halt("Invalid target")
    for name in ("build/gsnative-ctl", "build/kernel/gs_native.ko", str(plan_path.relative_to(ROOT)),
                 "tools/native/hardware_test_002.py", "tools/native/preflight.py"):
        path = ROOT / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"][name]:
            raise Halt("Artifact hash changed")
    if not output.is_dir() or output.is_symlink() or output.resolve().parent != (ROOT / "build/hardware-tests").resolve() or any(output.iterdir()):
        raise Halt("Expected a new empty evidence directory")
    if stat.S_IMODE(output.stat().st_mode) != 0o700 or output.stat().st_uid != int(os.environ.get("SUDO_UID", "-1")):
        raise Halt("Evidence directory must be private and owned by invoking user")
    params = Path("/sys/module/gs_native/parameters")
    expected = {"test_interface": target["port"] + ":1.0", "test_pid": str(0x109c),
                "enable_output": "Y", "session_ms": str(plan["kernel_session_limit_ms"]),
                "accel_counts_per_g_num": "8192", "accel_counts_per_g_den": "1"}
    if any((params / key).read_text().strip() != value for key, value in expected.items()):
        raise Halt("Loaded module parameters differ")
    loaded_src = Path("/sys/module/gs_native/srcversion").read_text().strip()
    if loaded_src != manifest["module_srcversion"]:
        raise Halt("Loaded module differs from approved build")
    capture = None
    if comparison:
        from native_usb_capture import attach
        try:
            capture = attach(manifest, output)
        except Exception as error:
            raise Halt(f"Recorder attachment failed: {error}") from error
    backend = Live(manifest, output, plan, capture)
    result = {"passed_transport_run": False, "xpad_restored": False}
    capture_failed = False
    try:
        backend.start_journal()
        before = backend.snapshot()
        backend.write_object("before.json", before)
        guard(before, target, "usbfs")
        state = process_state(target["busnum"], target["devnum"])
        if not state["deadband"] or not state["usb_handles"] or state["unreadable"]:
            raise Halt("Expected exclusively held Deadband preparation state")
        if any(handle["pid"] not in state["deadband"] for handle in state["usb_handles"]):
            raise Halt("USB handle belongs to another process")
        backend.record("manifest", manifest)
        if comparison:
            instructions = ("Vier Motorblöcke mit je drei 1-Sekunden-Impulsen. Nach bestätigtem STOPP mindestens 5 Sekunden Pause.\n"
                            "Nach der Eingabeansage einen Stick leicht bewegen, bis nach dem dritten STOPP PAUSE angesagt wird. Im restlichen Motorblock ist Ruhe erlaubt.\n")
        else:
            instructions = ("Für den späteren Motortest: ab der IMU-Ansage einen Stick leicht und durchgehend im Kreis bewegen, bis SCHLUSSRUHE.\n"
                            "So prüfen wir gleichzeitige Gamepad-Eingaben; in Ruhe können Gamepad-Berichte ausbleiben.\n")
        print(instructions +
              "Wenn du bereit bist: bereit eingeben und Enter drücken. Groß-/Kleinschreibung ist egal.\n"
              "Du hast dafür bis zu 5 Minuten. Deadband noch geöffnet lassen; danach folgen 15 Sekunden Countdown.", flush=True)
        if not select.select([sys.stdin], [], [], 300)[0] or not ready_input(sys.stdin.readline()):
            raise Halt("No explicit local readiness; no handover")
        backend.record("user_ready", {"accepted": True})
        if capture is not None:
            try:
                capture.start()
            except Exception as error:
                raise Halt(f"Recorder startup failed: {error}") from error
            capture_guard(backend, plan, plan["session_seconds"] + 15, "before-countdown")
        for remaining in range(15, 0, -1):
            capture_guard(backend, plan, plan["session_seconds"] + remaining, "countdown")
            backend.check_journal()
            guard(backend.snapshot(), target, "usbfs")
            print(f"In {remaining} s Deadband direkt über das Fenster schließen; Controller ruhig halten.", flush=True)
            backend.wait(1)
        print("JETZT Deadband direkt über das Fenster schließen. NICHT vorher Release to games anklicken. Danach keine weiteren Aktionen.", flush=True)
        until = backend.now() + 90
        while True:
            capture_guard(backend, plan, plan["session_seconds"] + 2, "waiting-for-release")
            backend.check_journal()
            state = process_state(target["busnum"], target["devnum"])
            if state["unreadable"]:
                raise Halt("Process scan incomplete")
            snap = backend.snapshot()
            if snap["identity"]["idProduct"] != "109c" or snap["identity"]["devnum"] != target["devnum"]:
                raise Halt("109c vanished before handover; no retry")
            if not state["deadband"] and not state["usb_handles"]:
                break
            if backend.now() >= until:
                raise Halt("Deadband release timed out; no takeover")
            backend.wait(.05)
        backend.record("handover_before", backend.snapshot())
        backend.write_object("109c-handover.json", backend.snapshot())
        handover(backend, target, plan)
        result = run_session(backend, plan)
        backend.record("result", result)
    except BaseException as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        backend.record("error", {"type": type(error).__name__, "message": str(error)})
        # run_session already performs END; finish is idempotent for an exited child.
        backend.finish()
        raise
    finally:
        try:
            # END must precede recorder tail/shutdown, including failed handovers.
            try:
                backend.finish()
            finally:
                if capture is not None:
                    try:
                        result["capture"] = capture.finish()
                        capture_failed = not result["capture"].get("passed", False)
                    except Exception as error:
                        capture_failed = True
                        result["capture"] = {"passed": False, "error": str(error)}
                    result["passed_recorded_transport_run"] = result["passed_transport_run"] and not capture_failed
        finally:
            save_final_evidence(backend, result)
    if capture_failed:
        raise Halt("Recorder did not finish successfully; preserve evidence and stop")
    print("Lauf beendet. Keine Rückbindung/Entladung ausgeführt. Rückweg separat freigeben.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    show = sub.add_parser("show-plan", help="Offline: validates and prints the schedule, no system/device reads")
    live = sub.add_parser("execute-authorized", help="NOT currently authorized; requires specific human hardware approval")
    live.add_argument("--manifest", type=Path, required=True)
    live.add_argument("--output", type=Path, required=True)
    for command in (show, live):
        command.add_argument("--variant", choices=("legacy-120", COMPARISON_VARIANT), default="legacy-120")
    args = parser.parse_args()
    plan = json.loads((COMPARISON_PLAN if args.variant == COMPARISON_VARIANT else PLAN).read_text())
    validate_plan(plan)
    if args.mode == "show-plan":
        print(json.dumps({"hardware_access": False, "session_seconds": plan["session_seconds"], "events": schedule(plan)}, indent=2))
        return 0
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"Signal {signum}; ending test")
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    try:
        execute(args.manifest, args.output, plan)
    except Halt as error:
        print(f"ABBRUCH: {error}\nKeine automatische Wiederholung. Zustand und Protokoll zuerst prüfen.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ABBRUCH auf Nutzerwunsch. Zustand und Protokoll zuerst prüfen.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
