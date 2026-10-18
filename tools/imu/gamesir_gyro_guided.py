#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One separately approved, KDE-guided left-turn observation.

Preparing a manifest reads metadata only. Running is deliberately unprivileged:
KDE questions and cues stay in the desktop session, while a fixed, separately
authenticated worker owns the IIO buffer transaction and its rollback.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import pwd
import select
import stat
import statistics
import subprocess
import sys
import tempfile
import time

from gamesir_imu_diagnostic import Bundle, GuidedCues
from gyro_reference import analyze_reference, validate_samples


ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = tuple("tools/imu/" + name for name in (
    "gamesir_gyro_guided.py", "gamesir_gyro_worker.py", "gamesir_iio_buffer.py",
    "gamesir_imu_stream.py", "gamesir_imu_diagnostic.py", "gyro_reference.py"))
MANIFEST_KIND = "gamesir_yaw90left_manifest"
MAX_GAP_NS = 250_000_000
MAX_JSON_BYTES = 1_048_576
MAX_EVENT_BYTES = 32_768
CAPTURE_FILES = ("scans.bin", "layout.json", "observations.jsonl", "buffer-transaction.json", "report.json")
PHASES = (
    (0, "rest_before", 20, "AUFZEICHNUNG LÄUFT. 20 Sekunden ruhig liegen lassen. Noch nicht aufnehmen."),
    (20, "pickup_buffer", 15, "JETZT vorsichtig aufnehmen und an der externen 0°-Startmarke ausrichten. Du hast 15 Sekunden. Noch nicht drehen."),
    (35, "hold_start", 5, "An der Startmarke stillhalten. Noch nicht drehen; gleich folgt die Startansage."),
    (40, "motion", 15, "JETZT EINMAL langsam 90° nach LINKS drehen, bis zur externen Endmarke. Tastenfläche oben; USB-Kante von vorne nach links. Dort stillhalten, nicht zurückdrehen."),
    (55, "hold_end", 5, "An der 90°-Endmarke weiter stillhalten. Noch nicht ablegen oder zurückdrehen."),
    (60, "put_down_buffer", 15, "JETZT vorsichtig ablegen. Du hast 15 Sekunden. Die Endausrichtung beibehalten, noch nicht zurückdrehen."),
    (75, "rest_after", 30, "SCHLUSSRUHE: 30 Sekunden ruhig liegen lassen. Noch nicht zurückdrehen."),
    (105, "finish", 4, "Messphasen beendet. Noch ruhig liegen lassen, bis Puffer und Datei nachweislich geschlossen sind."),
)
AXIS_PHASES = tuple((offset, phase, seconds, {
    "pickup_buffer": "JETZT vorsichtig aufnehmen. Tastenfläche oben, USB-Kante von dir weg. Du hast 15 Sekunden. Noch nicht drehen.",
    "hold_start": "Bequem halten. Noch nicht drehen; in 5 Sekunden kommt JETZT.",
    "motion": "JETZT EINMAL langsam waagerecht nach LINKS drehen, so weit es bequem ist. Kein bestimmter Winkel. Du hast 15 Sekunden. Danach dort halten, nicht zurückdrehen.",
    "hold_end": "In der erreichten Lage weiter stillhalten. Noch nicht ablegen oder zurückdrehen.",
}.get(phase, instruction)) for offset, phase, seconds, instruction in PHASES)


def axis_plan():
    """Information only: no metadata reads, GUI, timers or device access."""
    return {"kind": "qualitative_yaw_left_plan", "hardware_authorized": False,
            "repetitions": 3, "one_repetition_per_invocation": True,
            "local_go_required_each_time": True, "prepare_seconds": 30,
            "capture_seconds": 108, "reset_minimum_seconds": 15,
            "phases": [dict(offset_seconds=o, phase=p, seconds=s, instruction=i)
                       for o, p, s, i in AXIS_PHASES],
            "known_angle_required": False, "scale_selected": False,
            "automatic_next_repetition": False, "calibration_verified": False,
            "host_buffer_changes_require_separate_approval": True}


def analyze_axis_observation(samples, cue_rows, repetition, *, confirmed):
    """Raw-channel evidence only; never manufacture a known angle or axis map."""
    if confirmed is not True or type(repetition) is not int or repetition not in (1, 2, 3):
        raise ValueError("one human-confirmed left turn required")
    stream = validate_samples(samples, MAX_GAP_NS)
    names = [p[1] for p in AXIS_PHASES]
    rows = [row for row in cue_rows if row.get("event") in names]
    if [row["event"] for row in rows] != names:
        raise ValueError("complete ordered axis cues required")
    stamps = [row["monotonic_ns"] for row in rows]
    if any(type(t) is not int for t in stamps) or any(b <= a for a, b in zip(stamps, stamps[1:])):
        raise ValueError("ordered actual cue timestamps required")
    cues = dict(zip(names, stamps))
    windows, selected = {}, {}
    for name, first, last in (("rest_before", "rest_before", "pickup_buffer"),
                              ("motion", "hold_start", "put_down_buffer"),
                              ("rest_after", "rest_after", "finish")):
        start, end = cues[first], cues[last]
        selected[name] = [s for s in samples if start <= s["timestamp_ns"] < end]
        if len(selected[name]) < 2:
            raise ValueError("insufficient samples inside axis cue window")
        windows[name] = {"cue_bounds_ns": [start, end],
                         "sample_bounds_ns": [selected[name][0]["timestamp_ns"],
                                              selected[name][-1]["timestamp_ns"]],
                         "sample_count": len(selected[name])}
    channels = []
    for axis in range(3):
        before, motion, after = ([s["gyro_raw"][axis] for s in selected[name]]
                                 for name in ("rest_before", "motion", "rest_after"))
        baseline = statistics.mean(before)
        delta = [v - baseline for v in motion]
        channels.append({"raw_channel": f"G{axis}", "rest_before_mean_raw": baseline,
                         "rest_before_std_raw": statistics.pstdev(before),
                         "rest_after_mean_raw": statistics.mean(after),
                         "rest_after_std_raw": statistics.pstdev(after),
                         "motion_mean_delta_raw": statistics.mean(delta),
                         "motion_mean_abs_delta_raw": statistics.mean(abs(v) for v in delta),
                         "motion_min_delta_raw": min(delta), "motion_max_delta_raw": max(delta)})
    return {"schema_version": 1, "kind": "qualitative_yaw_left_observation",
            "repetition": repetition, "human_confirmed_motion": "horizontal left turn",
            "stream": stream, "windows": windows, "gyro_channels": channels,
            "baseline_is_experimental": True, "physical_axis_mapping_verified": False,
            "calibration_verified": False, "scale_selected": False, "sdl_runtime_enable": False,
            "limits": "Raw response/sign evidence only; compare repetitions and human motion report. No angle, rate scale or full axis map inferred."}


def home_directory():
    return Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()


def private_target(path, *, exists=False):
    """Evidence stays in this user's real home; never overwrite old evidence."""
    path = Path(path).absolute()
    parent = path.parent.resolve(strict=True)
    home = home_directory()
    if parent != home and home not in parent.parents:
        raise ValueError("output and manifest must stay in the user's home directory")
    if parent.stat().st_uid != os.getuid():
        raise ValueError("user-owned output parent required")
    path = parent / path.name
    if path.is_symlink():
        raise ValueError("symlink output or manifest refused")
    if exists:
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
            raise ValueError("private, user-owned regular manifest required")
    elif path.exists():
        raise ValueError("new output path required; existing evidence is never replaced")
    return path


def write_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def source_hashes():
    result = {}
    for name in SOURCE_FILES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"fixed source file missing or symlinked: {name}")
        with path.open("rb") as handle:
            result[name] = hashlib.file_digest(handle, "sha256").hexdigest()
    return result


def snapshot_iio(directory, node):
    # Lazy import keeps offline analysis and --help independent of device setup.
    from gamesir_iio_buffer import snapshot_iio as snapshot
    return snapshot(directory, node)


def prepare_manifest(directory, node, output):
    if os.geteuid() == 0:
        raise ValueError("prepare as the desktop user, without sudo")
    output = private_target(output)
    manifest = {"schema_version": 1, "kind": MANIFEST_KIND,
                "snapshot": snapshot_iio(directory, node), "source_sha256": source_hashes()}
    write_json(output, manifest)
    return manifest


def load_manifest(path):
    path = private_target(path, exists=True)
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        data = handle.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("manifest exceeds bounded JSON size")
    manifest = json.loads(data)
    if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or
            manifest.get("schema_version") != 1 or manifest.get("kind") != MANIFEST_KIND or
            not isinstance(manifest.get("snapshot"), dict) or
            manifest.get("source_sha256") != source_hashes()):
        raise ValueError("manifest schema or approved helper hashes changed; prepare a fresh plan")
    return path, manifest


def worker_command(manifest, output):
    return ["/usr/bin/sudo", "-A", "-p", "Password: ", "/usr/bin/python", "-B",
            str(ROOT / "tools/imu/gamesir_gyro_worker.py"), "--manifest", str(manifest),
            "--output", str(output)]


class WorkerLink:
    """Bounded JSON-line worker events and a live frontend heartbeat."""
    def __init__(self, process):
        self.process = process
        self.pending = []
        self.buffer = bytearray()
        self.finished = None
        self.last_ping_ns = None
        self.stdin_closed = False
        self.stdout_closed = False
        self.event_order = []
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stdin.fileno(), False)

    def send(self, command):
        if command not in ("GO", "PING", "STOP"):
            raise ValueError("fixed protocol command required")
        if self.stdin_closed:
            raise ValueError("worker input already closed")
        data = (command + "\n").encode("ascii")
        if os.write(self.process.stdin.fileno(), data) != len(data):
            raise ValueError("incomplete worker command")

    def _read(self):
        # Limit work per pulse even if a malformed worker floods stdout.
        total = 0
        while not self.stdout_closed and select.select([self.process.stdout.fileno()], [], [], 0)[0]:
            block = os.read(self.process.stdout.fileno(), 4096)
            total += len(block)
            if total > 65_536:
                raise ValueError("worker event stream exceeds bounded size")
            if not block:
                self.stdout_closed = True
                if self.buffer:
                    raise ValueError("partial final worker event")
                break
            self.buffer.extend(block)
            if len(self.buffer) > MAX_EVENT_BYTES:
                raise ValueError("worker event line too large")
            while b"\n" in self.buffer:
                raw, _, self.buffer = self.buffer.partition(b"\n")
                event = json.loads(raw)
                name = event.get("event") if isinstance(event, dict) else None
                if name not in ("ready", "capture_started", "finished") or self.finished is not None:
                    raise ValueError("unexpected worker protocol event")
                expected = ["ready", "capture_started"]
                if name != "finished" and (len(self.event_order) >= 2 or name != expected[len(self.event_order)]):
                    raise ValueError("duplicate or out-of-order worker event")
                if name == "capture_started":
                    stamp = event.get("monotonic_ns")
                    if type(stamp) is not int or stamp <= 0:
                        raise ValueError("recorded capture clock required")
                if name == "finished":
                    if type(event.get("passed")) is not bool or type(event.get("restored")) is not bool:
                        raise ValueError("explicit capture and rollback result required")
                    self.finished = event
                self.event_order.append(name)
                self.pending.append(event)

    def pulse(self, *, heartbeat=True):
        self._read()
        if self.finished is None and (self.stdout_closed or self.process.poll() is not None):
            # Drain any final data once before declaring a missing result.
            self._read()
            if self.finished is None:
                raise ValueError("worker exited without a verified rollback result")
        now = time.monotonic_ns()
        if heartbeat and self.finished is None and not self.stdin_closed and (
                self.last_ping_ns is None or now - self.last_ping_ns >= 250_000_000):
            self.send("PING")
            self.last_ping_ns = now

    def pop(self):
        return self.pending.pop(0) if self.pending else None

    def close_input(self):
        if not self.stdin_closed:
            self.stdin_closed = True
            self.process.stdin.close()

    def await_event(self, expected, *, timeout, cues=None, heartbeat=True):
        deadline = time.monotonic_ns() + int(timeout * 1_000_000_000)
        while time.monotonic_ns() <= deadline:
            self.pulse(heartbeat=heartbeat)
            if cues is not None:
                cues.check()
            event = self.pop()
            if event is not None:
                if event["event"] != expected:
                    detail = event.get("failure", event["event"])
                    raise ValueError(f"worker expected {expected}: {detail}")
                return event
            time.sleep(.05)
        raise ValueError(f"worker timed out waiting for {expected}")

    def stop_and_wait(self):
        """Ask for rollback, then close input. Never kill the privileged worker."""
        errors = []
        if self.finished is None and not self.stdin_closed:
            try:
                self.send("STOP")
            except (OSError, ValueError) as error:
                errors.append(str(error))
        try:
            self.close_input()
        except OSError as error:
            errors.append(str(error))
        if self.finished is None:
            try:
                deadline = time.monotonic_ns() + 120_000_000_000
                # A setup already in progress may emit capture_started after
                # STOP. Drain valid intermediate events until final rollback.
                while self.finished is None:
                    if time.monotonic_ns() > deadline:
                        raise ValueError("worker rollback result not received within 120 seconds")
                    self.pulse(heartbeat=False)
                    while self.pop() is not None:
                        pass
                    if self.finished is None:
                        time.sleep(.05)
            except (OSError, ValueError) as error:
                errors.append(str(error))
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            errors.append("privileged worker exit not confirmed; no kill or repeated rollback attempted")
        return {"worker_result": self.finished, "cleanup_errors": errors,
                "restored": self.finished is not None and self.finished.get("restored") is True}


def question(message, *, yes="Go", no="Abbrechen", worker=None, cues=None):
    """Explicit selected tag, default cancel; startup errors are not a user's No.

    KDialog has no --defaultno. Its documented menu/default combination keeps
    confirmation opt-in. Anonymous files prevent pipe backpressure while the
    worker heartbeat continues; diagnostic/result size is checked every tick.
    """
    command = ["/usr/bin/kdialog", "--title", "GameSir – Gyrotest",
               "--ok-label", "Auswahl bestätigen", "--cancel-label", "Abbrechen",
               "--default", "cancel", "--menu", message, "cancel", no, "go", yes]
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        child = subprocess.Popen(command, shell=False, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=errors)
        deadline = time.monotonic_ns() + 900_000_000_000
        try:
            while child.poll() is None:
                if time.monotonic_ns() > deadline:
                    raise ValueError("local readiness question expired; no automatic Go")
                if any(os.fstat(f.fileno()).st_size > 4096 for f in (output, errors)):
                    raise ValueError("KDE question output exceeds diagnostic limit")
                if worker is not None:
                    worker.pulse()
                    if worker.pending:
                        raise ValueError("worker stopped during the local readiness question")
                if cues is not None:
                    cues.check()
                time.sleep(.05)
            output.seek(0)
            errors.seek(0)
            answer, diagnostic = output.read(4097), errors.read(4097)
            if len(answer) > 4096 or len(diagnostic) > 4096:
                raise ValueError("KDE question output exceeds diagnostic limit")
            diagnostic = diagnostic.decode("utf-8", errors="replace").strip()
            if child.returncode not in (0, 1) or (child.returncode == 1 and diagnostic):
                raise ValueError(f"KDE question failed: exit={child.returncode}; {diagnostic or 'no diagnostic'}")
            if child.returncode == 1:
                if answer.strip():
                    raise ValueError("KDE question exit contradicts its selected answer")
                return False  # Escape/close/cancel with no startup error.
            if answer.strip() not in (b"cancel", b"go"):
                raise ValueError("KDE question returned no recognized explicit selection")
            if diagnostic:
                print(f"KDE question diagnostic: {diagnostic}", file=sys.stderr, flush=True)
            return answer.strip() == b"go"
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    child.kill()  # Only our unprivileged KDE question, never the worker.
                    child.wait(timeout=.5)


def wait_seconds(seconds, cues, worker=None):
    deadline = time.monotonic_ns() + int(seconds * 1_000_000_000)
    while time.monotonic_ns() < deadline:
        cues.check()
        if worker is not None:
            worker.pulse()
            if worker.pending:
                raise ValueError("unexpected worker event before the capture Go")
        time.sleep(.05)


def run_phases(worker, cues, start_ns, phases=PHASES):
    """Never catch up missed cues or launch another repetition."""
    index = 0
    while index < len(phases):
        worker.pulse()
        cues.check()
        if worker.pending:
            raise ValueError("capture finished before all reference phases were completed")
        now = time.monotonic_ns()
        offset, phase, seconds, instruction = phases[index]
        scheduled = start_ns + offset * 1_000_000_000
        if now >= scheduled:
            if now - scheduled > 2_000_000_000 or (
                    index + 1 < len(phases) and now >= start_ns + phases[index + 1][0] * 1_000_000_000):
                raise ValueError("reference cue missed or delayed over two seconds; stop without catch-up")
            cues.show(phase, instruction, seconds, scheduled_ns=scheduled)
            index += 1
        else:
            time.sleep(.05)


def reference_metadata(samples, cue_rows, repetition, description, *, confirmed):
    if confirmed is not True:
        raise ValueError("explicit human reference confirmation required; keep raw evidence only")
    if type(repetition) is not int or repetition not in (1, 2, 3):
        raise ValueError("one individually selected repetition 1, 2 or 3 required")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("independent external 90° reference description required")
    stamps = [sample["timestamp_ns"] for sample in samples]
    cues = {}
    for row in cue_rows:
        if row["event"] in {p[1] for p in PHASES}:
            if row["event"] in cues:
                raise ValueError("duplicate reference phase cue")
            cues[row["event"]] = row
    if set(cues) != {p[1] for p in PHASES}:
        raise ValueError("all separately recorded reference cues required")
    window = {"label": f"yaw90left-repetition-{repetition}", "physical_axis": "Z",
              "known_angle_deg": 90, "reference_kind": "external_angle_marker",
              "angle_reference_description": description.strip(), "reference_completed": True,
              "motion_bounds_include_stationary_margins": True}
    intervals = {}
    for name, first, last in (("rest_before", "rest_before", "pickup_buffer"),
                              ("motion", "hold_start", "put_down_buffer"),
                              ("rest_after", "rest_after", "finish")):
        actual = [cues[first]["monotonic_ns"], cues[last]["monotonic_ns"]]
        if any(type(value) is not int for value in actual) or actual[0] >= actual[1]:
            raise ValueError("ordered recorded cue times required")
        contained = [stamp for stamp in stamps if actual[0] <= stamp <= actual[1]]
        if len(contained) < 2:
            raise ValueError(f"{name}: fewer than two complete recorded samples inside cue bounds")
        window[name] = [contained[0], contained[-1]]
        intervals[name] = {"actual_cue_bounds_ns": actual,
                           "scheduled_cue_bounds_ns": [cues[first]["scheduled_monotonic_ns"],
                                                       cues[last]["scheduled_monotonic_ns"]],
                           "recorded_sample_bounds_ns": window[name]}
    return {"schema_version": 1, "kind": "experimental_known_angle", "windows": [window],
            "guidance": {"session": "yaw90left", "repetition": repetition,
                         "human_confirmed_90_degrees_and_stationary_margins": True,
                         "human_confirmed_cues_visible": True, "intervals": intervals,
                         "boundary_policy": "first and last existing sample inside actual cue interval; no interpolation",
                         "reset_excluded": True, "automatic_next_repetition": False},
            "calibration_verified": False, "sdl_runtime_enable": False}


def load_samples(path):
    if path.is_symlink():
        raise ValueError("regular saved observations required")
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("regular saved observations required")
        total, samples = 0, []
        for line in handle:
            total += len(line)
            if total > 64 * 1_048_576 or len(line) > 65_536:
                raise ValueError("saved observations exceed bounded size")
            samples.append(json.loads(line))
    return samples


def read_regular(path, maximum):
    """Saved evidence only, with private ownership and a bounded regular file."""
    before = os.lstat(path)
    if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or
            before.st_mode & 0o077 or before.st_size > maximum):
        raise ValueError(f"private bounded regular capture file required: {path.name}")
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        after = os.fstat(handle.fileno())
        if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("saved capture file changed while being opened")
        data = handle.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("saved capture file grew beyond size bound")
    return data


def verify_capture(path, start_ns):
    """Independently verify originals before any known-angle analysis."""
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("returned private capture directory required")
    if {entry.name for entry in path.iterdir()} != {*CAPTURE_FILES, "SHA256SUMS"}:
        raise ValueError("capture must contain exactly the fixed evidence file set")
    entries = {}
    for line in read_regular(path / "SHA256SUMS", 4096).decode("ascii").splitlines():
        digest, separator, name = line.partition("  ")
        if (separator != "  " or name not in CAPTURE_FILES or name in entries or len(digest) != 64 or
                any(character not in "0123456789abcdef" for character in digest)):
            raise ValueError("invalid or duplicate capture SHA256 entry")
        entries[name] = digest
    if set(entries) != set(CAPTURE_FILES):
        raise ValueError("incomplete capture SHA256 file set")
    contents = {}
    for name in CAPTURE_FILES:
        data = read_regular(path / name, 64 * 1_048_576 if name in ("scans.bin", "observations.jsonl") else MAX_JSON_BYTES)
        if hashlib.sha256(data).hexdigest() != entries[name]:
            raise ValueError(f"capture SHA256 mismatch: {name}; original retained, no angle analysis")
        if name in ("report.json", "buffer-transaction.json"):
            contents[name] = json.loads(data)
    report, transaction = contents["report.json"], contents["buffer-transaction.json"]
    if (not isinstance(report, dict) or report.get("completed") is not True or
            report.get("restored") is not True or report.get("failure") is not None or
            report.get("cleanup_errors") != [] or report.get("capture_started_monotonic_ns") != start_ns or
            not isinstance(transaction, dict) or transaction.get("restored") is not True or
            transaction.get("errors") != []):
        raise ValueError("capture report or transaction does not verify successful recording and restoration")
    return {"sha256_verified": True, "files": entries, "worker_report": report}


def run_measurement(manifest_path, repetition, description, output, *, axis_only=False):
    if os.geteuid() == 0:
        raise ValueError("KDE frontend must run as the desktop user, without sudo")
    if type(repetition) is not int or repetition not in (1, 2, 3):
        raise ValueError("exactly one repetition 1, 2 or 3 required")
    if not axis_only and (not isinstance(description, str) or not description.strip() or len(description) > 1_000 or "\0" in description):
        raise ValueError("describe the external 0°/90° reference in 1..1000 characters")
    manifest_path, manifest = load_manifest(manifest_path)
    output = private_target(output)
    bundle = Bundle(output)
    cue_rows = []

    def cue_sink(row):
        cue_rows.append(row)
        bundle.append_cue(row)

    cues, worker = GuidedCues(cue_sink), None
    report = {"schema_version": 1, "kind": "guided_yaw90left", "repetition": repetition,
              "passed": False, "reference_confirmed": False, "calibration_verified": False,
              "sdl_runtime_enable": False, "automatic_next_repetition": False,
              "manifest": manifest, "max_gap_ns": MAX_GAP_NS,
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    if axis_only:
        report.update(kind="guided_axis_left", motion_confirmed=False, scale_selected=False)
    extra_files = ["worker.stderr.log"]
    failure = None
    stderr_handle = bundle.open("worker.stderr.log")
    try:
        environment = os.environ.copy()
        environment.update(SUDO_ASKPASS="/usr/bin/ksshaskpass", LC_ALL="C.UTF-8")
        process = subprocess.Popen(worker_command(manifest_path, output / "capture"),
                                   shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=stderr_handle, env=environment, bufsize=0)
        worker = WorkerLink(process)
        bundle.append({"event": "worker_authentication_requested", "monotonic_ns": time.monotonic_ns()})
        worker.await_event("ready", timeout=300, cues=cues)
        prompt = (f"Wiederholung {repetition} von 3: genau eine horizontale 90°-Drehung nach LINKS.\n"
                        "Tastenfläche bleibt oben. Start: USB-Kante zeigt von dir weg; Ende: nach links.\n"
                        f"Externe Winkelreferenz: {html.escape(description.strip())}\n\n"
                        "Nach Go bleiben 30 Sekunden zum ruhigen Ablegen. Danach jede lokale Ansage abwarten.\n"
                        "Keine automatische nächste Wiederholung. Jetzt bereit?") if not axis_only else (
                        f"Achsentest, Wiederholung {repetition} von 3: EINMAL waagerecht nach LINKS drehen.\n"
                        "Tastenfläche oben, USB-Kante anfangs von dir weg. Nur so weit wie bequem; KEIN bestimmter Winkel.\n"
                        "Erst bei JETZT drehen, dann dort halten. Zurückdrehen erst nach bestätigtem Ende.\n\n"
                        "Nach Go bleiben 30 Sekunden Vorbereitung. Keine automatische Wiederholung. Jetzt bereit?")
        if not question(prompt,
                        worker=worker, cues=cues):
            raise ValueError("local Go declined; buffer not opened or enabled")
        report["local_go_monotonic_ns"] = time.monotonic_ns()
        cues.show("prepare", "30 Sekunden Vorbereitung: Controller ruhig ablegen. Tastenfläche oben, USB-Kante von dir weg. Noch keine Sensordatenaufnahme.", 30)
        wait_seconds(30, cues, worker)
        worker.send("GO")
        started = worker.await_event("capture_started", timeout=10, cues=cues)
        report["capture_start_monotonic_ns"] = started["monotonic_ns"]
        run_phases(worker, cues, started["monotonic_ns"], AXIS_PHASES if axis_only else PHASES)
        finished = worker.await_event("finished", timeout=12, cues=cues)
        report["worker_result"] = finished
        if finished["passed"] is not True or finished["restored"] is not True:
            raise ValueError(f"capture or buffer rollback failed: {finished.get('failure', finished)}")
        worker.close_input()
        if process.wait(timeout=2) != 0:
            raise ValueError("worker exit status contradicts successful result")
        report["capture_verification"] = verify_capture(output / "capture", started["monotonic_ns"])
        cues.show("reset_outside_analysis", "PUFFER ZURÜCKGESTELLT, AUFNAHME GESCHLOSSEN. Jetzt außerhalb der Messung zur Ausgangslage zurücksetzen. Mindestens 15 Sekunden Pause; kein weiterer Lauf startet automatisch.", 15)
        wait_seconds(15, cues)
        confirmation = ("War die externe 90°-Linksdrehung vollständig, horizontal und genau einmal ausgeführt?\n"
                             "Waren die lokalen Ansagen sichtbar und Anfang/Ende der Drehung in den Stillhaltefenstern?\n"
                             "Keine Rückdrehung vor Ende der Aufnahme?\n\n"
                             "Nur bei sicherem Ja bestätigen. Andernfalls bleiben die Rohdaten erhalten, ohne Winkel-Auswertung.") if not axis_only else (
                             "Hast du nach JETZT genau einmal waagerecht nach LINKS gedreht und danach stillgehalten?\n"
                             "Waren die Ansagen sichtbar, und erfolgte keine Rückdrehung vor Aufnahmeende?\n"
                             "Der Winkel ist egal. Bei verpasster Ansage, unbequemer oder anderer Bewegung bitte nicht bestätigen.\n"
                             "Rohdaten bleiben auch dann erhalten; es startet kein neuer Versuch.")
        confirmed = question(confirmation,
                             yes="Bestätigen", no="Nicht bestätigen", cues=cues)
        report["motion_confirmed" if axis_only else "reference_confirmed"] = confirmed
        if confirmed:
            samples = load_samples(output / "capture/observations.jsonl")
            if axis_only:
                analysis = analyze_axis_observation(samples, cue_rows, repetition, confirmed=True)
            else:
                metadata = reference_metadata(samples, cue_rows, repetition, description, confirmed=True)
                analysis = analyze_reference(samples, metadata, MAX_GAP_NS)
                write_json(output / "reference.json", metadata)
                extra_files.append("reference.json")
            write_json(output / "analysis.json", analysis)
            extra_files.append("analysis.json")
            report["analysis_created"] = True
            report["sample_count"] = len(samples)
        else:
            report["analysis_created"] = False
        report["passed"] = True
    except BaseException as error:
        failure = error
        report["failure"] = f"{type(error).__name__}: {error}"
    finally:
        finalization_errors = []
        if worker is not None:
            try:
                cleanup = worker.stop_and_wait()
                report["cleanup"] = cleanup
                if cleanup["restored"] is not True or cleanup["cleanup_errors"]:
                    report["passed"] = False
                    report.setdefault("failure", "worker cleanup or original buffer state not confirmed")
            except BaseException as error:
                report["passed"] = False
                report.setdefault("failure", f"worker cleanup failed: {type(error).__name__}: {error}")
                report["cleanup"] = {"restored": False, "unexpected_cleanup_failure": str(error)}
        else:
            report["cleanup"] = {"restored": True, "worker_not_started": True}
        try:
            cues.close()
        except BaseException as error:
            finalization_errors.append(f"KDE cleanup: {type(error).__name__}: {error}")
        try:
            stderr_handle.flush()
            os.fsync(stderr_handle.fileno())
        except BaseException as error:
            finalization_errors.append(f"stderr flush/fsync: {type(error).__name__}: {error}")
        finally:
            try:
                stderr_handle.close()
            except BaseException as error:
                finalization_errors.append(f"stderr close: {type(error).__name__}: {error}")
        if finalization_errors:
            report["passed"] = False
            report.setdefault("failure", finalization_errors[0])
            report["finalization_errors"] = finalization_errors
        report["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            bundle.finish(report, extra_files=extra_files)
        except BaseException as error:
            # Capture originals and the primary failure remain untouched. If a
            # filesystem failure also prevents this separate note, the final
            # console result still explicitly fails instead of claiming success.
            report["passed"] = False
            note = f"frontend evidence finalization: {type(error).__name__}: {error}"
            report.setdefault("failure", note)
            report.setdefault("finalization_errors", []).append(note)
            try:
                write_json(output / "frontend-finalization-error.json", report)
            except BaseException as secondary:
                report["finalization_errors"].append(f"failure note could not be saved: {secondary}")
    print(json.dumps({"passed": report["passed"], "reference_confirmed": report["reference_confirmed"],
                      "motion_confirmed": report.get("motion_confirmed"),
                      "output": str(output), "failure": report.get("failure")}, ensure_ascii=False), flush=True)
    if isinstance(failure, (KeyboardInterrupt, SystemExit)):
        return 130
    return 0 if report["passed"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan-axis-left", help="print qualitative left-turn plan; no GUI or hardware access")
    prepare = commands.add_parser("prepare", help="metadata-only manifest; no device open or buffer writes")
    prepare.add_argument("--iio-dir", required=True, type=Path)
    prepare.add_argument("--device-node", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    run = commands.add_parser("run", help="one separately approved repetition; local Go and password dialog")
    run.add_argument("--manifest", required=True, type=Path)
    run.add_argument("--repetition", required=True, type=int, choices=(1, 2, 3))
    run.add_argument("--reference-description", required=True)
    run.add_argument("--output", required=True, type=Path)
    axis = commands.add_parser("run-axis-left", help="one separately approved qualitative left turn; no angle reference")
    axis.add_argument("--manifest", required=True, type=Path)
    axis.add_argument("--repetition", required=True, type=int, choices=(1, 2, 3))
    axis.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan-axis-left":
            print(json.dumps(axis_plan(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "prepare":
            prepare_manifest(args.iio_dir, args.device_node, args.output)
            print(json.dumps({"manifest": str(args.output), "device_opened": False, "buffer_changed": False}))
            return 0
        if args.command == "run-axis-left":
            return run_measurement(args.manifest, args.repetition, None, args.output, axis_only=True)
        return run_measurement(args.manifest, args.repetition, args.reference_description, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"STOPPED {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
