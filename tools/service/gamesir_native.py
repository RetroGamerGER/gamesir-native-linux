#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Opt-in root supervisor. Importing this module never touches hardware.

All device activity is behind Host; Manager also runs with a synthetic backend.
No USB passthrough, profile writes, module loading or speculative mode resets.
"""
import argparse
from collections import deque
from dataclasses import asdict, dataclass, field, replace
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import stat
import struct
import subprocess
import sys
import time

# Same installed directory; the source checkout retains the shared SDL policy.
sys.path.insert(0, str(Path(__file__).resolve().parent))
if (Path(__file__).resolve().parent.parent / 'sdl/input_pair_readiness.py').is_file():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'sdl'))
from input_pair_readiness import Action, Binding, PublicationGate
from input_readiness import ProcessedInputs, ReadinessError

PORT = re.compile(r"[1-9][0-9]*-[1-9][0-9]*(?:\.[1-9][0-9]*)*")
INFO = re.compile(r"pid=(100a|109c|105e) state=(\d+) error=(-?\d+) OUT=([01]) session=([01])\b")
PAD = re.compile(r"\bpad=(\d+)\b")
BOOT = re.compile(r"^bootstrap state=(\d+) error=(-?\d+) failed_stage=(\d+) pad=([01]) imu=([01]) handover=([01]) port_token=(\d+) instance_token=(\d+)$", re.M)
RETURN_SECONDS = 30
HANDOFF_SECONDS = 5
JOB_SECONDS = {"bootstrap": 40, "boot-info": 3, "info": 3, "end": 5, "resume": 10,
               "input-info": 3, "publish-input": 3}
READ_ONLY = frozenset(("info", "boot-info", "input-info"))
INPUT_READY_SECONDS = 10


def input_status(output, tokens):
    lines = [line.removeprefix('input-publication ') for line in output.splitlines()
             if line.startswith('input-publication ')]
    if len(lines) != 1:
        raise Unsafe('Missing or ambiguous input publication status')
    value = json.loads(lines[0])
    if (type(value) is not dict or value.keys() != {'flags', 'port', 'instance', 'sensor', 'uniq', 'gyro', 'accel'} or
            any(type(value[k]) is not int for k in ('flags', 'port', 'instance', 'gyro', 'accel')) or
            not 0 <= value['flags'] <= 7 or [value['port'], value['instance']] != tokens or
            type(value['sensor']) is not str or not re.fullmatch(r'input[0-9]{1,10}', value['sensor']) or
            type(value['uniq']) is not str or not re.fullmatch(r'gsn-[0-9.:-]{1,100}', value['uniq']) or
            not 0 < value['gyro'] <= 1000000 or not 0 < value['accel'] <= 1000000 or
            not value['flags'] & 4):
        raise Unsafe('Invalid exact-instance six-axis publication status')
    return value
START_PIDS = frozenset(("100a", "105e", "109c"))
DIRECT_PIDS = frozenset(("105e", "109c"))
FALLBACK_PIDS = frozenset(("100a", "105e"))
# Discovery never adopts a foreign or unexplained existing native binding.
# xpad is an optional previous owner, not a source of initialization or input.
START_OWNERS = (None, "xpad")
NATIVE_PIDS = frozenset(("109c", "105e"))
STATUS_BUSY_EXIT = 4  # C client: only a getter's open(EBUSY), never an ioctl failure.
DIAGNOSTIC_BYTES = 4096
RECENT_FAILURES = 8
OUTPUT_SCOPE = "supervisor-bounded combined stdout/stderr, not the complete original child stream"


def bootstrap_diagnostic(rc, output, timed_out, source_instance):
    """Bounded reported diagnostics, never device identity/cleanup authority."""
    data = output.encode("utf-8", "replace")
    if len(data) > DIAGNOSTIC_BYTES:
        marker = "\n[... omitted ...]\n"
        half = (DIAGNOSTIC_BYTES - len(marker)) // 2
        excerpt = data[:half].decode("utf-8", "ignore") + marker + data[-half:].decode("utf-8", "ignore")
    else:
        excerpt = output
    status = None
    matches = list(BOOT.finditer(output))
    if len(matches) == 1:
        try:
            values = list(map(int, matches[0].groups()))
            if all(-(2**63) <= value < 2**64 for value in values):
                status = dict(zip(("state", "error", "failed_stage", "pad", "imu", "handover",
                                   "port_token", "instance_token"), values))
        except ValueError:
            pass
    return {"version": 1, "returncode": rc, "timed_out": timed_out,
            "source_instance": source_instance, "reported_kernel_status": status,
            "combined_output": excerpt, "output_bytes": len(data),
            "output_sha256": hashlib.sha256(data).hexdigest(),
            "output_scope": OUTPUT_SCOPE,
            "excerpt_truncated": len(data) > DIAGNOSTIC_BYTES}


def boot_proof(output):
    """Attest terminal runtime/failure or setup-complete pending ownership."""
    matches = list(BOOT.finditer(output))
    if len(matches) != 1:
        return None
    state, error, stage, pad, imu, handover, port, instance = map(int, matches[0].groups())
    if not (0 < port < 2**64 and 0 < instance < 2**64):
        return None
    # The USB core may bind the correlated instance directly; handover=0 does
    # not invalidate READY. Exact cross-FD kernel tokens are the ownership proof.
    if (state == 7 and error == 0 and imu) or (state == 8 and error < 0 and 4 <= stage <= 7):
        return {"tokens": [port, instance], "ready": state == 7}
    if state == 9 and error == 0 and stage == 0:
        return {"tokens": [port, instance], "ready": False, "waiting": True}
    if state == 8 and error < 0 and stage == 9:
        return {"tokens": [port, instance], "ready": False}
    return None


class Unsafe(RuntimeError):
    pass


class AcquisitionUnchanged(Unsafe):
    """Pre-write acquisition refusal grants no ownership or cleanup authority."""


class AcquisitionAutoprobe(Unsafe):
    """Same exact free USB instance gained xpad before any acquisition write."""
    def __init__(self, current):
        super().__init__("Same-instance xpad autoprobe; full access recheck required")
        self.current = current


class StatusBusy(Unsafe):
    """A getter cannot acquire the exclusive control FD; no runtime fault."""


class StatusChanged(Unsafe):
    """A passive getter's exact instance changed; never cleanup authority."""


class StatusUnavailable(Unsafe):
    """Incomplete observation metadata, not proven absence or runtime failure."""
    def __init__(self, message, *, global_scan=False):
        super().__init__(message)
        self.global_scan = global_scan


def checked_diagnostic(value):
    """Fail closed on corrupt new state fields; never stringify arbitrary data."""
    if type(value) is not dict:
        raise Unsafe("Invalid saved bootstrap diagnostic")
    if not value:  # Historical state, or no completed bootstrap yet.
        return {}
    expected = {"version", "returncode", "timed_out", "source_instance", "reported_kernel_status",
                "combined_output", "output_bytes", "output_sha256", "output_scope", "excerpt_truncated"}
    if (value.keys() != expected or type(value["version"]) is not int or value["version"] != 1 or
            type(value["returncode"]) is not int or not -(2**31) <= value["returncode"] < 2**31 or
            type(value["timed_out"]) is not bool or type(value["excerpt_truncated"]) is not bool or
            type(value["source_instance"]) is not str or not 0 < len(value["source_instance"].encode()) <= 4096 or
            type(value["combined_output"]) is not str or len(value["combined_output"].encode()) > DIAGNOSTIC_BYTES or
            type(value["output_bytes"]) is not int or not 0 <= value["output_bytes"] < 2**64 or
            type(value["output_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", value["output_sha256"]) or
            value["output_scope"] != OUTPUT_SCOPE):
        raise Unsafe("Invalid or oversized saved bootstrap diagnostic")
    status = value["reported_kernel_status"]
    fields = {"state", "error", "failed_stage", "pad", "imu", "handover", "port_token", "instance_token"}
    if status is not None and (type(status) is not dict or status.keys() != fields or
                              any(type(v) is not int or not -(2**63) <= v < 2**64 for v in status.values())):
        raise Unsafe("Invalid saved bootstrap kernel diagnostic")
    return value


def checked_failures(value):
    if type(value) is not list or len(value) > RECENT_FAILURES:
        raise Unsafe("Invalid or oversized saved failure history")
    fields = {"port", "source_instance", "origin_pid", "message", "bootstrap_diagnostic", "resolution"}
    resolutions = (None, "physically_absent", "observed_100a_xpad", "verified_100a_xpad",
                   "observed_105e_xpad", "verified_105e_xpad")
    for item in value:
        if (type(item) is not dict or item.keys() != fields or
                type(item["port"]) is not str or len(item["port"]) > 63 or not PORT.fullmatch(item["port"]) or
                type(item["source_instance"]) is not str or not 0 < len(item["source_instance"].encode()) <= 4096 or
                type(item["origin_pid"]) is not str or item["origin_pid"] not in START_PIDS or
                type(item["message"]) is not str or len(item["message"].encode()) > 1024 or
                item["resolution"] not in resolutions):
            raise Unsafe("Invalid or oversized saved failure record")
        checked_diagnostic(item["bootstrap_diagnostic"])
    return value


class Scan(dict):
    """Complete enumeration with independently quarantined unsafe ports."""
    def __init__(self):
        super().__init__()
        self.errors = {}


@dataclass(frozen=True)
class Device:
    port: str
    token: str
    parent: str
    pid: str
    bus: int
    address: int
    driver: str | None
    sysfs_inode: int = 0
    parent_inode: int = 0

    @property
    def interface(self):
        return self.port + ":1.0"

    @property
    def node(self):
        return "/dev/gsnative-" + self.interface


@dataclass
class Entry:
    device: Device
    phase: str
    job: object = None
    operation: str = ""
    deadline: float = 0
    next_check: float = 0
    resume_deadline: float = 0
    error: str = ""
    cancel_requested: bool = False
    timed_out: bool = False
    kernel_tokens: list = field(default_factory=list)
    candidate: Device | None = None
    after_attest: str = "failed"
    end_attempted: bool = False
    cleanup_attempted: bool = False
    status_conflict: str = ""
    status_conflicts: int = 0
    origin_pid: str = "100a"
    bootstrap_started: bool = False
    end_succeeded: bool = False
    absent_since: float | None = None
    bootstrap_diagnostic: dict = field(default_factory=dict)
    pending_status: tuple | None = None
    publication_deadline: float = 0
    publication_attempted: bool = False
    publication_gate: object = None
    publication_meta: dict = field(default_factory=dict)
    publication_reason: str = ''
    publication_failure: str = ''
    acquisition_failure: str = ''


class Manager:
    """Serialized policy; one nonblocking child operation per physical port.

    The backend must revalidate the instance, binding and foreign owners before
    every mutation. Parent identity includes the actual hub object lifetime.
    PID/address are never treated as an individual stable device identity.
    """
    def __init__(self, host, clock=time.monotonic):
        self.host, self.clock = host, clock
        saved = host.load()
        self.paused = bool(saved.get("paused", False))
        self.entries = {}
        self.attempted = set(saved.get("attempted", []))
        self.budgets = {p: deque(v) for p, v in saved.get("budgets", {}).items()}
        self.budget_boot = saved.get("boot_id")
        self.recent_failures = checked_failures(saved.get("recent_failures", []))
        self.observed = {}
        # Exact native instances saved after completed bootstrap can survive a
        # daemon restart. Never adopt an unexplained existing native binding.
        self.leases = saved.get("leases", {})
        self.stopping = False
        self.scan_error = ""
        self.port_errors = {}
        self.normal_since = None
        self.discovery_deferred = set()
        for port, record in self.leases.items():
            # Historical records contain only Device metadata. They have no
            # kernel attestation and must never authorize a new 109c END.
            if "device" not in record:
                continue
            entry = Entry(Device(**record["device"]), record["phase"],
                          error=record.get("error", ""),
                          kernel_tokens=record.get("kernel_tokens", []),
                          end_attempted=record.get("end_attempted", False),
                          cleanup_attempted=record.get("cleanup_attempted", False),
                          origin_pid=record.get("origin_pid", "100a" if record["device"]["pid"] != "105e" else ""),
                          bootstrap_started=record.get("bootstrap_started", False),
                          end_succeeded=record.get("end_succeeded", False),
                          bootstrap_diagnostic=checked_diagnostic(record.get("bootstrap_diagnostic", {})))
            entry.publication_deadline = record.get('publication_deadline', 0)
            entry.publication_attempted = record.get('publication_attempted', False)
            entry.publication_failure = record.get('publication_failure', '')
            entry.acquisition_failure = record.get('acquisition_failure', '')
            if (type(entry.publication_deadline) not in (int, float) or
                    not 0 <= entry.publication_deadline < 1e12 or
                    type(entry.publication_attempted) is not bool or
                    type(entry.publication_failure) is not str or
                    len(entry.publication_failure.encode()) > 1024 or
                    type(entry.acquisition_failure) is not str or
                    len(entry.acquisition_failure.encode()) > 1024):
                raise Unsafe('Invalid saved publication or acquisition state')
            if record.get("candidate"):
                entry.candidate = Device(**record["candidate"])
            entry.after_attest = record.get("after_attest", "failed")
            entry.deadline = record.get("deadline", 0)
            if (entry.origin_pid not in START_PIDS or
                    (entry.origin_pid in DIRECT_PIDS and entry.device.pid != entry.origin_pid) or
                    (entry.origin_pid == "100a" and entry.device.pid not in ("100a", "109c"))):
                entry.phase = "blocked"
                entry.error = "Missing or invalid original PID; no cleanup authority"
            if entry.phase == "blocked":
                # Quarantine survives restart. A process conflict must not
                # turn into a new END merely because the daemon was restarted.
                pass
            elif entry.device.pid in NATIVE_PIDS and entry.kernel_tokens:
                entry.candidate = entry.device
                entry.after_attest = ("returning" if entry.end_attempted else
                                     "receiver_wait" if entry.phase == 'receiver_wait' and not entry.error else
                                     "active" if entry.phase in ('active', 'input_check', 'awaiting_sensor', 'publishing_input')
                                     and not entry.error else "failed")
                entry.phase = "attesting"
            elif entry.candidate and entry.kernel_tokens:
                entry.phase = "attesting"
            elif entry.kernel_tokens and entry.phase == "locating":
                pass  # Same-boot monotonic deadline and old-FD proof persist.
            elif entry.origin_pid in DIRECT_PIDS and entry.bootstrap_started:
                # Same-instance direct startup can recover its terminal kernel
                # proof after client/daemon loss, but never initialize twice.
                entry.candidate = entry.device
                entry.after_attest = "failed"
                entry.phase = "attesting"
            elif entry.phase not in ("blocked", "released", "failed"):
                # A restarted passive/claim/bootstrap client is not a fresh
                # start grant. Recover its known 100a, never initialize twice.
                entry.phase = "failed"
                entry.error = "Supervisor restarted during operation; cleanup only"
            self.entries[port] = entry

    def save(self):
        self.host.save({"paused": self.paused, "leases": self.leases,
                        "recent_failures": self.recent_failures,
                        "attempted": sorted(self.attempted),
                        "budgets": {p: list(v) for p, v in self.budgets.items()},
                        "boot_id": getattr(self.host, "boot_id", None) or self.budget_boot})

    @property
    def inhibited(self):
        return self.paused or self.stopping

    def notice(self, kind, device, message):
        self.host.log(kind, port=device.port, message=message)

    def start(self, entry, operation, device=None):
        if entry.job is not None:
            raise Unsafe("Concurrent operation on one instance")
        target = device or entry.device
        guard = self.host.observe_guard if operation in READ_ONLY else self.host.guard
        guard(target)
        if operation == "end":
            if not entry.kernel_tokens:
                raise Unsafe("No kernel ownership proof for END")
            entry.end_attempted = True
            self.remember(entry)  # A crash may not repeat an uncertain END.
        needs_tokens = operation in ('end', 'input-info', 'publish-input') or (operation == "info" and target.pid in NATIVE_PIDS)
        if operation == 'publish-input':
            if entry.publication_attempted:
                raise Unsafe('Input publication already attempted; no repeat')
            entry.publication_attempted = True
            self.remember(entry)
        entry.job = self.host.start(operation, target, entry.kernel_tokens if needs_tokens else None)
        entry.operation = operation
        entry.deadline = self.clock() + JOB_SECONDS[operation]
        entry.cancel_requested = False
        entry.timed_out = False

    def fail(self, entry, message, phase="failed"):
        if entry.phase in ('input_check', 'awaiting_sensor', 'publishing_input') and not entry.publication_failure:
            entry.publication_failure = message.encode('utf-8', 'replace')[:1024].decode('utf-8', 'ignore')
        entry.status_conflict = ""
        entry.status_conflicts = 0
        if entry.error == message and entry.phase in ("failed", "blocked"):
            if phase == "blocked" and entry.phase != "blocked":
                entry.phase = "blocked"
                self.remember(entry)
            return
        entry.error = message
        entry.phase = phase
        self.record_failure(entry)
        self.notice("failure", entry.device, message)
        if entry.device.port in self.leases:
            self.remember(entry)

    def record_failure(self, entry, resolution=None):
        """Retain the last eight failures even after verified cleanup/replug."""
        if not entry.error:
            return
        source = entry.bootstrap_diagnostic.get("source_instance", entry.device.token)
        record = {"port": entry.device.port, "source_instance": source,
                  "origin_pid": entry.origin_pid,
                  "message": (entry.publication_failure or entry.acquisition_failure or entry.error).encode("utf-8", "replace")[:1024].decode("utf-8", "ignore"),
                  "bootstrap_diagnostic": entry.bootstrap_diagnostic,
                  "resolution": resolution}
        self.recent_failures = [old for old in self.recent_failures
                                if old.get("source_instance") != source]
        self.recent_failures.append(record)
        self.recent_failures = self.recent_failures[-RECENT_FAILURES:]

    def defer_status(self, entry, message):
        # These are bounded-frequency getter checks, never USB/start retries.
        # Preserve the active/waiting/attesting phase and all ownership proofs.
        if entry.status_conflict != message:
            self.notice("status_deferred", entry.device, message)
        entry.status_conflict = message
        entry.status_conflicts = min(entry.status_conflicts + 1, 5)
        entry.next_check = self.clock() + min(2 ** (entry.status_conflicts - 1), 10)

    def status_available(self, entry):
        if entry.status_conflict:
            self.notice("status_available", entry.device, "Exclusive native status access restored")
        entry.status_conflict = ""
        entry.status_conflicts = 0

    def defer_observation(self, entry, message, *, global_scan=False):
        """Unknown metadata neither proves absence nor permits new mutations."""
        self.normal_since = None
        if global_scan:
            self.scan_error = str(message)
            for known in self.entries.values():
                known.absent_since = None
        else:
            entry.absent_since = None
            self.port_errors[entry.device.port] = str(message)

    def merge_scan_errors(self, fresh):
        """Quarantine every newly uncertain port for the rest of this tick.

        A getter for A may discover unreadable metadata for B. B's earlier
        snapshot then cannot authorize discovery, cleanup or handoff. Pending
        jobs still drain their results and retain their original diagnostics.
        """
        errors = getattr(fresh, "errors", {})
        self.port_errors.update(errors)
        if isinstance(self.observed, Scan):
            self.observed.errors.update(errors)
        for port in errors:
            if port in self.entries:
                self.entries[port].absent_since = None
        if any(port in self.entries or port in self.leases for port in errors):
            self.normal_since = None

    def remember(self, entry):
        record = {
            "device": asdict(entry.device), "phase": entry.phase,
            "error": entry.error, "kernel_tokens": entry.kernel_tokens,
            "candidate": asdict(entry.candidate) if entry.candidate else None,
            "after_attest": entry.after_attest,
            "deadline": entry.deadline,
            "end_attempted": entry.end_attempted,
            "cleanup_attempted": entry.cleanup_attempted,
            "origin_pid": entry.origin_pid,
            "bootstrap_started": entry.bootstrap_started,
            "end_succeeded": entry.end_succeeded,
            "bootstrap_diagnostic": entry.bootstrap_diagnostic,
            "publication_deadline": entry.publication_deadline,
            "publication_attempted": entry.publication_attempted,
            "publication_failure": entry.publication_failure,
            "acquisition_failure": entry.acquisition_failure,
        }
        if self.leases.get(entry.device.port) == record:
            return
        self.leases[entry.device.port] = record
        self.save()

    def budget_available(self, port):
        now = self.clock()
        history = self.budgets.setdefault(port, deque())
        while history and history[0] < now - 600:
            history.popleft()
        return len(history) < 3

    def begin_bootstrap(self, entry):
        if not self.budget_available(entry.device.port):
            entry.phase = "blocked"
            entry.error = "Three starts in 10 minutes; explicit resume required"
            self.remember(entry)
            return
        self.attempted.add(entry.device.token)
        self.budgets[entry.device.port].append(self.clock())
        entry.phase = "bootstrapping"
        entry.bootstrap_started = True
        self.remember(entry)  # Persist the attempt before issuing commands.
        self.start(entry, "bootstrap")

    def command(self, command):
        if command == "release":
            self.paused = True
            self.save()  # Inhibit takeover before the first END/cancel.
            self.scan_error = "Release verification pending"
        elif command == "resume":
            if any(e.job or e.phase == "returning" for e in self.entries.values()):
                raise Unsafe("Release/operation is still in progress")
            if any(port not in self.entries or self.entries[port].phase not in ("active", "receiver_wait")
                   for port in self.leases):
                raise Unsafe("Unresolved ownership/recovery; verify return before resuming")
            self.paused = False
            self.attempted.clear()
            self.budgets.clear()
            self.entries = {p: e for p, e in self.entries.items() if e.phase in ("active", "receiver_wait")}
            self.save()
        elif command != "status":
            raise Unsafe("Only status, release and resume are accepted")
        return self.status()

    def status(self):
        return {"paused": self.paused, "scan_error": self.scan_error,
                "input_readiness": {"enabled": getattr(self.host, 'readiness_enabled', False),
                                    "monitor_error": getattr(self.host, 'input_error', '')},
                "recent_failures": self.recent_failures,
                "port_errors": self.port_errors,
                "returned": self.returned(),
                "return_scope": "managed ports only; uninstaller separately verifies all native bindings",
                "devices": {p: {"pid": e.device.pid, "phase": e.phase,
                                "error": e.error, "busy": bool(e.job),
                                "present": None if self.scan_error or p in self.port_errors else p in self.observed,
                                "observed_pid": self.observed[p].pid if p in self.observed else None,
                                "observed_driver": self.observed[p].driver if p in self.observed else None,
                                "bootstrap_diagnostic": e.bootstrap_diagnostic,
                                "status_conflict": e.status_conflict,
                                "input_publication": e.publication_reason,
                                "input_publication_failure": e.publication_failure,
                                "acquisition_failure": e.acquisition_failure,
                                "status_retry_in": max(0, e.next_check - self.clock())
                                if e.status_conflict else 0}
                            for p, e in self.entries.items()}}

    def returned(self):
        if (not self.inhibited or self.scan_error or self.leases or
                any(e.job for e in self.entries.values())):
            return False
        return (self.normal_since is not None and self.clock() - self.normal_since >= 1 and
                self.managed_returned(self.observed))

    def managed_returned(self, devices):
        # Deadband on another, never-managed dongle is outside our return scope.
        # An unexpected replacement on one of our ports remains fail-closed.
        for port in self.entries.keys() | self.leases.keys():
            if port in self.port_errors:
                return False
            current = devices.get(port)
            if current is None and port in self.leases:
                # Stable absence must clear the recovery record before a
                # removal client is told that return has been verified.
                return False
            origin = self.entries[port].origin_pid if port in self.entries else "100a"
            # xpad on 109c is not proof of a usable fallback. Keep the same
            # manual-recovery requirement as a transitioned standard device.
            fallback = "100a" if origin == "109c" else origin
            if current and (current.pid != fallback or current.driver != "xpad"):
                return False
        return True

    def locate_handoff(self, entry, devices):
        """A completed child may race the preceding scan. Never lose its proof."""
        current = devices.get(entry.device.port)
        expected_instance = (current and
            ((entry.origin_pid in DIRECT_PIDS and current.pid == entry.origin_pid and current.token == entry.device.token) or
             (entry.origin_pid == "100a" and current.pid == "109c" and current.token != entry.device.token)))
        if (entry.device.port not in self.port_errors and
                entry.device.port not in getattr(devices, "errors", {}) and expected_instance and
                current.driver == "gs_native" and current.parent == entry.device.parent):
            entry.candidate = current
            entry.phase = "attesting"
            self.remember(entry)
            self.start(entry, "boot-info", current)
        elif self.clock() >= entry.deadline:
            self.fail(entry, "Attested bootstrap finished but candidate not validated; manual attention required", "blocked")
            self.remember(entry)

    def retire_obsolete_status(self, entry, current):
        """Retire only an old healthy session, never act on its replacement.

        A getter can finish after a normal radio reconnect has produced a new
        free or xpad-owned standard device. It must pass ordinary discovery and its
        start budget; the old kernel tokens do not authorize any command on it.
        Faulted sessions, bootstrap handoffs and changed hubs stay fail-closed.
        """
        if (entry.phase not in ("active", "receiver_wait") or entry.error or entry.timed_out or
                entry.origin_pid not in ("100a", "109c") or entry.device.pid != "109c" or
                not entry.kernel_tokens):
            return False
        if current is None:
            # A complete scan proves only current absence. Keep the old lease
            # until the normal continuous-absence/replacement policy retires it.
            self.status_available(entry)
            entry.next_check = self.clock() + 1
            return True
        if (current.token == entry.device.token or current.parent != entry.device.parent or
                current.pid not in ("100a", "109c") or current.driver not in START_OWNERS):
            return False
        self.notice("session_replaced", entry.device,
                    "Obsolete passive status discarded; replacement requires fresh discovery")
        self.leases.pop(entry.device.port, None)
        self.entries.pop(entry.device.port, None)
        # The tick's first snapshot may already be obsolete too. Discovery
        # must enumerate again rather than claiming that earlier replacement.
        self.discovery_deferred.add(entry.device.port)
        self.save()
        return True

    def info_failure(self, entry, rc, output):
        """Record a completed getter failure before any uncertain rescan.

        A fault report concerns its pinned old FD, even if enumeration is now
        incomplete. Persist it immediately so restart cannot erase the primary
        failure. This grants no permission to operate on a replacement.
        """
        if entry.timed_out:
            return "Native status client exceeded deadline"
        if rc == STATUS_BUSY_EXIT:
            return None
        match = INFO.search(output)
        if not match or match[1] != entry.device.pid:
            return "Unrecognized native status"
        state, error, enabled, session = map(int, match.group(2, 3, 4, 5))
        if entry.device.pid == "100a":
            if rc or error or state != 1 or enabled or session or not PAD.search(output):
                return "Invalid passive 100a status"
        elif rc or error or (state != 3 and (state != 1 or not enabled or not session)):
            return "Native runtime fault; END and verified return only"
        return None

    def poll_job(self, entry, devices):
        result = entry.pending_status if entry.pending_status is not None else self.host.poll(entry.job)
        if result is None:
            if self.clock() >= entry.deadline and not entry.cancel_requested:
                self.host.cancel(entry.job)
                entry.cancel_requested = True
                entry.timed_out = True
                self.fail(entry, "Client deadline; cancellation requested, no retry")
            return
        operation = entry.operation
        rc, output = result
        current = devices.get(entry.device.port)
        if operation == 'publish-input' and (entry.timed_out or rc):
            # Preserve the completed mutation's first result even if the next
            # metadata scan is incomplete. Never reissue an uncertain publish.
            entry.job, entry.operation, entry.pending_status = None, '', None
            excerpt = output.encode('utf-8', 'replace')[-700:].decode('utf-8', 'ignore')
            self.fail(entry, f'Input publication failed: rc={rc} timeout={entry.timed_out}; ' + excerpt)
            return
        if operation in READ_ONLY or operation == 'publish-input':
            # The process may complete after the tick's initial enumeration.
            # Its passive result never authorizes action on a replacement.
            if entry.pending_status is None and rc == STATUS_BUSY_EXIT and self.clock() >= entry.deadline:
                entry.timed_out = True
            if operation == "info":
                failure = self.info_failure(entry, rc, output)
                if failure:
                    entry.job, entry.operation, entry.pending_status = None, "", None
                    self.fail(entry, failure)
                    return
            if operation == 'boot-info' and entry.phase == 'receiver_wait' and rc and rc != STATUS_BUSY_EXIT:
                # Preserve this pinned old FD's result even across incomplete
                # metadata or an independently enumerated replacement.
                entry.bootstrap_diagnostic = bootstrap_diagnostic(rc, output, entry.timed_out, entry.device.token)
                self.remember(entry)
            try:
                fresh = self.host.scan()
            except (OSError, Unsafe) as error:
                entry.pending_status = result
                self.defer_observation(entry, error, global_scan=True)
                return
            self.merge_scan_errors(fresh)
            if entry.device.port in self.port_errors:
                entry.pending_status = result
                self.defer_observation(entry, self.port_errors[entry.device.port])
                return
            current = fresh.get(entry.device.port)
        entry.job, entry.operation, entry.pending_status = None, "", None
        if operation == 'boot-info' and entry.phase == 'receiver_wait' and current != entry.device:
            old_proof = boot_proof(output)
            status = bootstrap_diagnostic(rc, output, entry.timed_out, entry.device.token)['reported_kernel_status'] or {}
            removed_wait = (rc == 1 and status.get('state') == 8 and
                            status.get('error') == -errno.ENODEV and status.get('failed_stage') == 9)
            if (old_proof and old_proof['tokens'] == entry.kernel_tokens and
                    ((not rc and (old_proof.get('waiting') or old_proof['ready'])) or removed_wait) and
                    not entry.timed_out and self.retire_obsolete_status(entry, current)):
                if removed_wait:
                    self.host.log('receiver_removed', port=entry.device.port,
                                  diagnostic=entry.bootstrap_diagnostic)
                return
        if operation in READ_ONLY and not entry.timed_out and rc == STATUS_BUSY_EXIT:
            expected = entry.candidate if operation == "boot-info" and entry.phase != 'receiver_wait' else entry.device
            if not expected or current != expected or current.driver != "gs_native":
                if ((operation != "info" and not (operation == 'boot-info' and entry.phase == 'receiver_wait')) or
                        not self.retire_obsolete_status(entry, current)):
                    self.fail(entry, "Device changed during deferred status access", "blocked")
            else:
                self.defer_status(entry, "Native control FD busy; status deferred")
            return
        if operation == "bootstrap":
            entry.bootstrap_diagnostic = bootstrap_diagnostic(rc, output, entry.timed_out, entry.device.token)
            self.host.log("bootstrap_result", port=entry.device.port,
                          diagnostic=entry.bootstrap_diagnostic)
            self.remember(entry)
            proof = boot_proof(output)
            if not proof:
                if entry.origin_pid in DIRECT_PIDS and current == entry.device:
                    # Direct startup cannot move to a replacement. Recover only
                    # this claimed instance's terminal proof; absent/early proof
                    # blocks cleanup rather than guessing whether output began.
                    entry.candidate = current
                    entry.after_attest = "failed"
                    entry.phase = "attesting"
                    entry.error = "Direct bootstrap result missing; recovering cleanup proof only"
                    self.record_failure(entry)
                    self.remember(entry)
                    if entry.device.port not in self.port_errors:
                        self.start(entry, "boot-info", current)
                else:
                    self.fail(entry, "Bootstrap incomplete; no second bootstrap on this instance")
                return
            # A failed initialization can already own the replacement device.
            # The old FD's token record alone is insufficient: compare it to
            # GET_BOOT_STATUS on the independently validated new instance.
            entry.kernel_tokens = proof["tokens"]
            entry.after_attest = ("active" if proof["ready"] and not rc and
                                  "Native startup completed." in output and not entry.timed_out else
                                  "receiver_wait" if proof.get('waiting') and not rc and
                                  "Native receiver waiting." in output and not entry.timed_out else "failed")
            entry.phase = "locating"
            entry.deadline = self.clock() + HANDOFF_SECONDS
            if entry.after_attest == "failed":
                entry.error = "Bootstrap failed after native handoff; cleanup only"
                self.record_failure(entry)
            self.remember(entry)
            try:
                fresh = self.host.scan()
            except (OSError, Unsafe) as error:
                self.defer_observation(entry, error, global_scan=True)
                return  # Keep the proof; bounded locating continues next tick.
            self.merge_scan_errors(fresh)
            self.locate_handoff(entry, fresh)
        elif operation == "boot-info":
            proof = boot_proof(output)
            polling_receiver = entry.phase == 'receiver_wait'
            expected = entry.device if polling_receiver else entry.candidate
            recovering_direct = (entry.origin_pid in DIRECT_PIDS and entry.bootstrap_started and
                                 not entry.kernel_tokens and entry.candidate == entry.device and
                                 entry.after_attest == "failed")
            if (entry.timed_out or rc not in (0, 1) or not proof or
                    (not recovering_direct and proof["tokens"] != entry.kernel_tokens) or not expected or
                    current != expected or current.driver != "gs_native"):
                entry.candidate = None
                self.fail(entry, "Native handoff token mismatch or unavailable; manual attention required", "blocked")
                self.remember(entry)
                return
            self.status_available(entry)
            entry.kernel_tokens = proof["tokens"]
            entry.device = current
            entry.candidate = None
            entry.phase = entry.after_attest
            if entry.after_attest == 'receiver_wait':
                if proof['ready'] and not rc:
                    entry.phase = 'active'
                    entry.after_attest = 'active'
                elif proof.get('waiting') and not rc:
                    entry.phase = 'receiver_wait'
                else:
                    entry.bootstrap_diagnostic = bootstrap_diagnostic(rc, output, entry.timed_out, entry.device.token)
                    self.fail(entry, 'Kernel receiver wait failed; original status retained, cleanup only')
            if entry.phase == "active" and not proof["ready"]:
                entry.phase = "failed"
                entry.error = "Attested native instance is faulted; cleanup only"
                self.record_failure(entry)
            if entry.end_attempted:
                entry.phase = "returning"
                entry.deadline = self.clock() + RETURN_SECONDS
            entry.next_check = self.clock() + (2 if entry.phase == 'receiver_wait' else 0)
            self.remember(entry)
            if entry.phase == "active":
                if getattr(self.host, 'readiness_enabled', False) and current.pid == '109c':
                    entry.phase = 'input_check'
                    if not entry.publication_deadline:
                        entry.publication_deadline = self.clock() + INPUT_READY_SECONDS
                    self.remember(entry)
                    self.start(entry, 'input-info')
                else:
                    self.notice("ready", current, "Persistent native runtime; IMU scale remains experimental")
        elif operation in ('input-info', 'publish-input'):
            if entry.timed_out or rc or current != entry.device or current.driver != 'gs_native':
                excerpt = output.encode('utf-8','replace')[-700:].decode('utf-8','ignore')
                self.fail(entry, f'Input publication {operation} failed: rc={rc} timeout={entry.timed_out}; '
                          + excerpt if current == entry.device else 'Input publication exact instance changed')
                return
            try:
                meta = input_status(output, entry.kernel_tokens)
                binding = self.host.input_binding(current, meta)
                if meta['flags'] & 2:
                    entry.phase = 'active'
                    entry.publication_reason = 'Exact input publication confirmed'
                    entry.next_check = self.clock()
                    self.remember(entry)
                    self.notice('ready', current, entry.publication_reason)
                elif operation == 'publish-input' or entry.publication_attempted:
                    self.fail(entry, 'Uncertain input publication; cleanup only, no repeat')
                elif meta['flags'] != 5:
                    self.fail(entry, 'Expected an unpublished deferred sensor pair')
                else:
                    if not entry.publication_deadline:
                        entry.publication_deadline = self.clock() + INPUT_READY_SECONDS
                    entry.publication_meta = meta
                    entry.publication_gate = PublicationGate(binding,
                        entry.publication_deadline - INPUT_READY_SECONDS, INPUT_READY_SECONDS)
                    entry.phase = 'awaiting_sensor'
                    self.remember(entry)
            except (ValueError, ReadinessError, Unsafe) as error:
                self.fail(entry, 'Input publication metadata: ' + str(error))
        elif operation == "info":
            if entry.timed_out:
                self.fail(entry, "Native status client exceeded deadline")
                return
            if current != entry.device or current.driver != "gs_native":
                if not self.retire_obsolete_status(entry, current):
                    self.fail(entry, "Device changed during native status access", "blocked")
                return
            match = INFO.search(output)
            if not match or match[1] != entry.device.pid:
                self.fail(entry, "Unrecognized native status")
                return
            state, error, enabled, session = map(int, match.group(2, 3, 4, 5))
            if entry.device.pid == "100a":
                pad = PAD.search(output)
                if rc or error or state != 1 or enabled or session or not pad:
                    self.fail(entry, "Invalid passive 100a status")
                elif not self.inhibited:
                    self.status_available(entry)
                    # Exact acquisition plus valid passive runtime state is
                    # the gate. A stationary controller need not send a button
                    # report before the captured bootstrap can initialize it.
                    self.begin_bootstrap(entry)
                else:
                    self.status_available(entry)
                    entry.phase = "checking_start"
                    entry.next_check = self.clock() + 1
                return
            if state == 3 and not self.inhibited:
                self.status_available(entry)
                entry.phase = "resuming"
                entry.resume_deadline = self.clock() + 15
                entry.next_check = self.clock()
            elif rc or error or state != 1 or not enabled or not session:
                self.fail(entry, "Native runtime fault; END and verified return only")
            else:
                self.status_available(entry)
                entry.next_check = self.clock() + 2
        elif operation == "resume":
            if entry.timed_out:
                self.fail(entry, "PM resume client exceeded deadline")
            elif rc == 3 and self.clock() < entry.resume_deadline:
                entry.next_check = self.clock() + 0.5
            elif rc:
                self.fail(entry, "PM resume failed or exceeded readiness deadline")
            else:
                entry.phase = "active"
                entry.next_check = self.clock()
        elif operation == "end":
            entry.end_succeeded = rc == 0 and not entry.timed_out
            entry.phase = "returning"
            entry.deadline = self.clock() + RETURN_SECONDS
            if rc and operation == "end":
                entry.error = "END failed; only observing verified return, no repeat"
            self.remember(entry)

    def retire_returned_timeout(self, entry, current):
        """Retire an attested, ended cold-native timeout, not its replacement.

        A fresh 100a already on xpad proves observed return only. It grants no
        ownership: defer discovery until a new scan and all normal start gates.
        Never migrate historical attempted tokens or retry the old instance.
        """
        diagnostic = entry.bootstrap_diagnostic
        status = diagnostic.get('reported_kernel_status') or {}
        if (self.inhibited or entry.job is not None or
                entry.origin_pid != '109c' or entry.device.pid != '109c' or
                not entry.bootstrap_started or not entry.end_attempted or
                not entry.end_succeeded or not entry.kernel_tokens or
                diagnostic.get('source_instance') != entry.device.token or
                diagnostic.get('timed_out', True) or diagnostic.get('returncode') != 1 or
                status.get('state') != 8 or status.get('error') != -errno.ETIMEDOUT or
                status.get('failed_stage') != 5 or status.get('pad') != 0 or
                status.get('imu') != 0 or status.get('handover') != 0 or
                [status.get('port_token'), status.get('instance_token')] != entry.kernel_tokens or
                current.port != entry.device.port or current.parent != entry.device.parent or
                current.token == entry.device.token or current.token in self.attempted or
                current.pid != '100a' or current.driver != 'xpad'):
            return False
        self.record_failure(entry, 'observed_100a_xpad')
        self.leases.pop(current.port, None)
        self.entries.pop(current.port)
        self.discovery_deferred.add(current.port)
        # Old failed token, history, pause and per-port budget are preserved.
        # Persist retirement before any future acquisition can be considered.
        self.save()
        self.notice('returned_start_candidate', current,
                    'Cold-native timeout ended; new 100a requires fresh budgeted discovery')
        return True

    def return_one(self, entry, current):
        if not current:
            return
        if entry.device.port not in self.leases:
            # A budget-blocked candidate was never acquired. It grants no
            # cleanup authority if somebody else subsequently binds it.
            return
        if current.parent != entry.device.parent:
            self.fail(entry, "Hub lifetime changed; return target not trusted", "blocked")
            return
        if (entry.device.driver != "gs_native" and
                current.driver == "gs_native" and not entry.kernel_tokens):
            # Also covers daemon loss between intent and confirmed acquisition.
            # An intent alone cannot prove who attached the native driver.
            self.fail(entry, "Acquisition unconfirmed; native binding needs manual recovery", "blocked")
            return
        if entry.origin_pid == "105e":
            self.return_direct(entry, current)
            return
        if entry.origin_pid not in ("100a", "109c"):
            self.fail(entry, "Unknown original PID; no return commands", "blocked")
            return
        if current.pid == "105e":
            self.fail(entry, "Unexpected 105e replacement of standard model; no return commands", "blocked")
            return
        if current.pid == "100a":
            if current.token != entry.device.token:
                if current.driver == "xpad":
                    if self.retire_returned_timeout(entry, current):
                        return
                    entry.phase = "released"  # Observed only; no write to a replacement.
                    self.record_failure(entry, "observed_100a_xpad")
                    entry.device = current
                    self.attempted.add(current.token)
                    self.leases.pop(current.port, None)
                    self.save()
                else:
                    self.fail(entry, "Unowned new 100a instance; no return binding attempted", "blocked")
                return
            if current.driver in ("gs_native", None):
                if entry.cleanup_attempted:
                    entry.phase = "blocked"
                    entry.error = "100a return attempt unresolved; manual attention required"
                    self.remember(entry)
                    return
                entry.cleanup_attempted = True
                self.remember(entry)
                self.host.restore(current)
            elif current.driver != "xpad":
                self.fail(entry, "Foreign driver prevents xpad return")
                return
            entry.phase = "released"
            self.record_failure(entry, "verified_100a_xpad")
            entry.device = current
            self.attempted.add(current.token)
            self.leases.pop(current.port, None)
            self.save()
        elif entry.phase == "blocked":
            return  # Keep observing; no repeated END, log or state-file storm.
        elif not entry.end_attempted:
            if current.token != entry.device.token:
                self.fail(entry, "Unowned new 109c instance; no END attempted", "blocked")
                return
            if current.driver != "gs_native":
                self.fail(entry, "Foreign 109c owner; no END or rebind attempted", "blocked")
                return
            entry.device = current
            self.start(entry, "end")
            entry.phase = "ending"
            self.remember(entry)
        elif self.clock() >= entry.deadline:
            # Never issue a guessed 109c→100a mode packet or bind 109c to xpad.
            self.fail(entry, "Return deadline: still 109c; manual attention required", "blocked")
            self.remember(entry)

    def return_direct(self, entry, current):
        """105e stays 105e: quiesce our exact instance, then verify xpad."""
        if current.pid != "105e":
            self.fail(entry, "Direct-start PID changed; no speculative return commands", "blocked")
            return
        if current.token != entry.device.token:
            if current.driver == "xpad":
                # Only observe a replacement's existing normal binding.
                entry.phase = "released"
                self.record_failure(entry, "observed_105e_xpad")
                entry.device = current
                self.attempted.add(current.token)
                self.leases.pop(current.port, None)
                self.save()
            else:
                self.fail(entry, "Unowned new 105e instance; no END or rebind", "blocked")
            return
        if current.driver == "xpad":
            entry.phase = "released"
            self.record_failure(entry, "observed_105e_xpad")
            entry.device = current
            self.attempted.add(current.token)
            self.leases.pop(current.port, None)
            self.save()
            return
        if entry.phase == "blocked":
            return
        if entry.bootstrap_started:
            if current.driver != "gs_native" or not entry.kernel_tokens:
                self.fail(entry, "Direct startup lacks native ownership proof; manual return required", "blocked")
                return
            if not entry.end_attempted:
                self.start(entry, "end")
                entry.phase = "ending"
                self.remember(entry)
                return
            if not entry.end_succeeded:
                self.fail(entry, "Direct END unverified; no unbind or second END", "blocked")
                return
        if current.driver not in (None, "gs_native") or entry.cleanup_attempted:
            self.fail(entry, "Direct xpad return unresolved; manual attention required", "blocked")
            return
        entry.cleanup_attempted = True
        self.remember(entry)
        self.host.restore(current)
        try:
            fresh = self.host.scan()
        except (OSError, Unsafe) as error:
            self.defer_observation(entry, error, global_scan=True)
            return  # The persisted one-shot restore is not repeated.
        self.merge_scan_errors(fresh)
        if current.port in self.port_errors:
            return  # Uncertain metadata cannot verify the persisted restore.
        restored = fresh.get(current.port)
        if (not restored or restored.token != current.token or restored.parent != current.parent or
                restored.pid != "105e" or restored.driver != "xpad"):
            self.fail(entry, "105e xpad return not verified", "blocked")
            return
        entry.phase = "released"
        self.record_failure(entry, "verified_105e_xpad")
        entry.device = restored
        self.attempted.add(restored.token)
        self.leases.pop(restored.port, None)
        self.save()

    def tick(self):
        self.discovery_deferred.clear()
        try:
            fresh = self.host.scan()
            devices = Scan()
            devices.update(fresh)
            devices.errors.update(getattr(fresh, "errors", {}))
            self.scan_error = ""
        except (OSError, Unsafe) as error:
            self.scan_error = str(error)
            self.normal_since = None
            for entry in self.entries.values():
                entry.absent_since = None  # Unknown is not continuous physical absence.
            self.host.log("scan_failed", message=str(error))
            return
        self.observed = devices
        live_boot = getattr(self.host, "boot_id", None)
        if self.budget_boot != live_boot:
            self.budgets.clear()
            if self.budget_boot is not None and live_boot is not None:
                # A proven host reboot destroys old kernel objects. This is
                # different from restarting this daemon within the same boot.
                # Keep explicit pause, discard only obsolete epoch ownership.
                self.entries.clear()
                self.leases.clear()
                self.attempted.clear()
            self.budget_boot = live_boot
            self.save()
        self.port_errors = getattr(devices, "errors", {})
        self.merge_scan_errors(devices)
        now = self.clock()
        if self.managed_returned(devices):
            if self.normal_since is None:
                self.normal_since = now
        else:
            self.normal_since = None
        for port, entry in list(self.entries.items()):
            try:
                current = devices.get(port)
                if entry.job is not None:
                    if self.inhibited and entry.operation in ("bootstrap", "resume", 'publish-input') and not entry.cancel_requested:
                        self.host.cancel(entry.job)
                        # It may have completed before cancellation reached it.
                        # Keep the operation so its handoff proof is not lost.
                        entry.cancel_requested = True
                    self.poll_job(entry, devices)
                    if self.scan_error:
                        return  # The global view became unknown after the initial scan.
                    continue
                if port in self.port_errors:
                    # Keep this instance quarantined; it is not proven absent.
                    # Other owned devices can still END and return normally.
                    # port_errors exposes this temporary observation failure.
                    # It must not replace an earlier protocol/runtime error or
                    # linger in entry.error after a complete scan succeeds.
                    entry.absent_since = None
                    continue
                if entry.phase == "locating":
                    self.locate_handoff(entry, devices)
                    continue
                if not current:
                    # Presence and protocol state are independent. A short USB
                    # gap must not erase failed/blocked and authorize replacement.
                    if entry.absent_since is None:
                        entry.absent_since = now
                    elif now - entry.absent_since >= 10:
                        if entry.error and not self.inhibited:
                            continue  # Unresolved transition requires explicit release.
                        self.record_failure(entry, "physically_absent")
                        self.leases.pop(port, None)
                        self.entries.pop(port)
                        self.save()
                    continue
                entry.absent_since = None
                same = current.token == entry.device.token and current.parent == entry.device.parent
                if entry.phase == "released" and same and current.driver == "xpad":
                    continue
                if entry.phase == "attesting":
                    if entry.candidate != current:
                        entry.candidate = None
                        self.fail(entry, "Handoff candidate changed before attestation", "blocked")
                        self.remember(entry)
                    elif now >= entry.next_check:
                        self.start(entry, "boot-info", current)
                    continue
                if self.inhibited or entry.phase in ("failed", "returning", "ending", "blocked"):
                    # Start inhibition is not cleanup inhibition. Known 100a
                    # ownership still authorizes one bounded xpad return.
                    self.return_one(entry, current)
                    if self.scan_error:
                        return
                    continue
                if not same:
                    if entry.status_conflict:
                        if not self.retire_obsolete_status(entry, current):
                            self.fail(entry, "Device changed during deferred status access", "blocked")
                        continue
                    # Re-enumeration after a running session is a fresh device.
                    # No handover follows a port or hub replacement implicitly.
                    self.leases.pop(port, None)
                    self.entries.pop(port)
                    self.save()
                    continue
                if current.driver != "gs_native" and entry.phase in ("active", "receiver_wait"):
                    self.fail(entry, "Native binding lost; never steal it back")
                    continue
                if entry.phase == "active" and now >= entry.next_check:
                    self.start(entry, "info")
                elif entry.phase == 'receiver_wait' and now >= entry.next_check:
                    self.start(entry, 'boot-info')
                elif entry.phase == 'input_check':
                    if now >= entry.publication_deadline:
                        self.fail(entry, 'Input readiness status deadline; cleanup only')
                    elif now >= entry.next_check:
                        self.start(entry, 'input-info')
                elif entry.phase == 'awaiting_sensor':
                    if now >= entry.publication_deadline:
                        self.fail(entry, 'Input readiness deadline; cleanup only')
                        continue
                    self.host.observe_guard(current)
                    binding = self.host.input_binding(current, entry.publication_meta)
                    sensor = self.host.input_sensor(binding, entry.publication_meta)
                    decision = entry.publication_gate.observe(binding, sensor, self.clock())
                    entry.publication_reason = decision.reason
                    if decision.action == Action.ABORT:
                        self.fail(entry, 'Input readiness: ' + decision.reason)
                    elif decision.action == Action.PUBLISH:
                        entry.phase = 'publishing_input'
                        self.remember(entry)
                        self.start(entry, 'publish-input')
                elif entry.phase in ("checking_start", "waiting_input") and now >= entry.next_check:
                    self.start(entry, "info")
                elif entry.phase == "resuming" and now >= entry.next_check:
                    self.start(entry, "resume")
            except StatusBusy:
                self.defer_status(entry, "Native control FD busy; status deferred")
            except StatusUnavailable as error:
                self.defer_observation(entry, error, global_scan=error.global_scan)
                if error.global_scan:
                    return
            except StatusChanged as error:
                try:
                    fresh = self.host.scan()
                except (OSError, Unsafe) as observation_error:
                    self.defer_observation(entry, observation_error, global_scan=True)
                    return
                self.merge_scan_errors(fresh)
                if port in self.port_errors:
                    self.defer_observation(entry, self.port_errors[port])
                elif not self.retire_obsolete_status(entry, fresh.get(port)):
                    self.fail(entry, str(error), "blocked")
            except (ReadinessError, subprocess.SubprocessError) as error:
                self.fail(entry, 'Input readiness: ' + str(error))
            except (OSError, Unsafe) as error:
                self.fail(entry, str(error), "blocked")

        for port, device in devices.items():
            if port in self.entries or port in self.discovery_deferred or port in self.port_errors:
                continue
            if self.inhibited or device.pid not in START_PIDS or device.token in self.attempted:
                continue
            if getattr(self.host, 'input_error', ''):
                continue  # Failed monitor must not authorize another takeover.
            if device.driver not in START_OWNERS:
                continue  # No adoption of foreign or unexplained native bindings.
            if not self.budget_available(port):
                self.entries[port] = Entry(device, "blocked",
                    error="Three starts in 10 minutes; explicit resume required", origin_pid=device.pid)
                continue  # Budget checked before acquisition, including free IF0.
            entry = self.entries[port] = Entry(device, "checking_start", origin_pid=device.pid)
            try:
                self.remember(entry)  # Claim intent survives a partial bind/crash.
                self.host.claim(device)
                try:
                    fresh = self.host.scan()
                except (OSError, Unsafe) as error:
                    self.defer_observation(entry, error, global_scan=True)
                    raise
                self.merge_scan_errors(fresh)
                current = fresh.get(port)
                if not current or current.token != device.token or current.driver != "gs_native":
                    raise Unsafe("Instance changed while acquiring native driver")
                entry.device = current
                self.remember(entry)
                if device.pid in DIRECT_PIDS:
                    self.begin_bootstrap(entry)
                else:
                    self.start(entry, "info")
            except StatusBusy:
                self.defer_status(entry, "Native control FD busy; status deferred")
            except AcquisitionUnchanged as error:
                # The host refused BEFORE any write; an intent is not ownership.
                entry.acquisition_failure = str(error).encode('utf-8', 'replace')[:1024].decode('utf-8', 'ignore')
                self.leases.pop(port, None)
                self.attempted.add(device.token)
                self.fail(entry, str(error), "blocked")
                self.save()
            except StatusUnavailable as error:
                if entry.device.driver != "gs_native":
                    entry.acquisition_failure = str(error).encode('utf-8', 'replace')[:1024].decode('utf-8', 'ignore')
                    self.fail(entry, str(error))  # Partial claim has no fresh native proof.
                else:
                    self.defer_observation(entry, error, global_scan=error.global_scan)
                if error.global_scan:
                    return
            except (OSError, Unsafe) as error:
                if not entry.bootstrap_started and not entry.acquisition_failure:
                    entry.acquisition_failure = str(error).encode('utf-8', 'replace')[:1024].decode('utf-8', 'ignore')
                self.fail(entry, str(error))
                if self.scan_error:
                    return


@dataclass
class Job:
    process: object
    output: bytearray = field(default_factory=bytearray)
    cancelled: bool = False
    output_limited: bool = False


class Host:
    def __init__(self, client, state, sysfs=Path("/sys"), proc=Path("/proc")):
        self.client, self.state, self.sysfs, self.proc = str(client), Path(state), Path(sysfs), Path(proc)
        self.boot_id = None
        self.readiness_enabled = False
        self.inputs = None
        self.input_error = ''

    def configure_inputs(self):
        parameters = self.sysfs / 'module/gs_native/parameters'
        if not (parameters / 'defer_input').is_file():
            return  # Legacy, nondeferred kernel; no new operation required.
        self.readiness_enabled = all((parameters / name).read_text().strip() == 'Y'
                                    for name in ('defer_input', 'experimental_gyro', 'experimental_accel'))
        if self.readiness_enabled:
            self.inputs = ProcessedInputs()  # Before any claim or bootstrap.

    def input_binding(self, device, meta):
        if meta['uniq'] != f"gsn-{device.interface}-{meta['instance']}":
            raise ReadinessError('Kernel motion identity differs from exact binding tokens')
        return Binding(device.parent, device.token + ':' + str(meta['instance']),
                       str((self.sysfs / 'bus/usb/devices' / device.interface).resolve(strict=True)), meta['uniq'])

    def input_sensor(self, binding, meta):
        if self.input_error:
            raise ReadinessError(self.input_error)
        self.inputs.drain()
        return self.inputs.sensor(binding, meta['sensor'], meta['gyro'], meta['accel'])

    def drain_inputs(self):
        if self.inputs and not self.input_error:
            try:
                self.inputs.drain()
            except (OSError, ReadinessError, UnicodeError) as error:
                self.input_error = str(error)
                self.log('input_monitor_failed', message=self.input_error)

    def log(self, event, **values):
        print(json.dumps({"event": event, **values}), flush=True)

    def load(self):
        path = self.state / "state.json"
        if not path.exists():
            return {}
        st = path.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_uid or st.st_mode & 0o077:
            raise Unsafe("Unsafe persistent state permissions")
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or not isinstance(data.get("leases", {}), dict):
            raise Unsafe("Invalid persistent state")
        return data

    def save(self, value):
        temporary = self.state / "state.new"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as out:
            json.dump(value, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, self.state / "state.json")
        fd = os.open(self.state, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @staticmethod
    def value(path, base=16):
        raw = path.read_text().strip()
        if not raw:
            raise Unsafe(f"Empty USB metadata: {path} (base {base})")
        try:
            return int(raw, base)
        except ValueError as error:
            # Keep the exact field for the quarantined port's diagnostics;
            # invalid/incomplete metadata must never become a device identity.
            raise Unsafe(f"Invalid USB metadata: {path} (base {base})") from error

    def scan(self):
        if self.boot_id is None:
            value = (self.proc / "sys/kernel/random/boot_id").read_text().strip()
            if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value):
                raise Unsafe("Missing or invalid host boot ID")
            self.boot_id = value
        result = Scan()
        for path in sorted((self.sysfs / "bus/usb/devices").iterdir()):
            if not PORT.fullmatch(path.name):
                continue
            try:
                if self.value(path / "idVendor") != 0x3537:
                    continue
                pid = self.value(path / "idProduct")
                if pid not in (0x100a, 0x109c, 0x105e):
                    continue
                device = self.describe(path, pid)
                result[device.port] = device
            except FileNotFoundError:
                # Incomplete enumeration is unknown, not proof of absence.
                # A following complete scan will observe the true disconnect.
                result.errors[path.name] = "USB metadata changed during enumeration"
            except (OSError, ValueError, Unsafe) as error:
                result.errors[path.name] = str(error)
        return result

    def describe(self, path, pid):
        before = path.stat()
        parent_path = path.resolve().parent
        parent = parent_path.stat()
        if self.value(path / "bConfigurationValue", 10) != 1:
            raise Unsafe("Unexpected USB configuration at " + path.name)
        interfaces = sorted(path.glob(path.name + ":*"))
        if [p.name for p in interfaces] != [path.name + ":1.0", path.name + ":1.1"]:
            raise Unsafe("Unexpected interface set at " + path.name)
        drivers = []
        for index, interface in enumerate(interfaces):
            expected_class = (0xff, 0x5d, 1) if pid == 0x100a and index == 0 else (
                (3, 0, 0) if pid == 0x100a else (0xff, 0x47, 0xd0))
            actual = tuple(self.value(interface / field) for field in
                           ("bInterfaceClass", "bInterfaceSubClass", "bInterfaceProtocol"))
            if (actual != expected_class or self.value(interface / "bInterfaceNumber") != index or
                    self.value(interface / "bAlternateSetting", 10) != 0):
                raise Unsafe("Unexpected interface descriptor at " + interface.name)
            expected = ({2: (3, 32), 0x82: (3, 32)} if pid == 0x100a else
                        {2: (3, 64), 0x82: (3, 64)}) if index == 0 else (
                            {4: (3, 64), 0x84: (3, 64)} if pid == 0x100a else {})
            endpoints = {self.value(ep / "bEndpointAddress"):
                         (self.value(ep / "bmAttributes"), self.value(ep / "wMaxPacketSize"))
                         for ep in interface.glob("ep_*")}
            if endpoints != expected:
                raise Unsafe("Unexpected endpoints at " + interface.name)
            if any(not 1 <= self.value(ep / "bInterval") <= 255 for ep in interface.glob("ep_*")):
                raise Unsafe("Invalid interrupt interval at " + interface.name)
            driver = interface / "driver"
            drivers.append(driver.resolve().name if driver.is_symlink() else None)
        if drivers[1] != ("usbhid" if pid == 0x100a else None):
            raise Unsafe("Unexpected interface-1 owner at " + path.name)
        bus, address = self.value(path / "busnum", 10), self.value(path / "devnum", 10)
        after = path.stat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise Unsafe("Device changed while reading descriptors")
        token = f"{self.boot_id}:{path.resolve()}:{before.st_dev}:{before.st_ino}:{bus}:{address}:{pid:04x}"
        parent_token = f"{self.boot_id}:{parent_path}:{parent.st_dev}:{parent.st_ino}"
        return Device(path.name, token, parent_token, f"{pid:04x}", bus, address, drivers[0],
                      before.st_ino, parent.st_ino)

    def guard(self, expected):
        self.check_access(expected, observation=False)

    def observe_guard(self, expected):
        self.check_access(expected, observation=True)

    def acquisition_guard(self, expected):
        try:
            self.check_access(expected, observation=False, acquisition=True)
        except AcquisitionAutoprobe as change:
            # One complete read-only recheck, not a retry of an acquisition or
            # bootstrap. The strict second pass must see a stable exact owner.
            self.guard(change.current)
            return change.current
        return expected

    def check_access(self, expected, *, observation, acquisition=False):
        def observe():
            try:
                result = self.scan()
            except (OSError, Unsafe) as error:
                if observation:
                    raise StatusUnavailable(str(error), global_scan=True) from error
                raise
            if expected.port in getattr(result, "errors", {}):
                raise (StatusUnavailable if observation else Unsafe)(result.errors[expected.port])
            return result.get(expected.port)

        def verify(actual, message):
            if actual == expected:
                return
            if (acquisition and expected.driver is None and
                    actual == replace(expected, driver="xpad")):
                raise AcquisitionAutoprobe(actual)
            # Name differing fields without exposing tokens/paths in diagnostics.
            changed = (','.join(key for key in asdict(expected)
                               if getattr(actual, key) != getattr(expected, key))
                       if isinstance(actual, Device) else 'missing or incomplete device metadata')
            raise (StatusChanged if observation else Unsafe)(message + ': ' + changed)

        verify(observe(), "Device identity/binding changed before operation")
        if observation and expected.driver != "gs_native":
            raise Unsafe("Native status requires the exact native binding")
        target = f"/dev/bus/usb/{expected.bus:03d}/{expected.address:03d}"
        control_busy = False
        for process in self.proc.iterdir():
            if not process.name.isdigit() or int(process.name) == os.getpid():
                continue
            try:
                for fd in (process / "fd").iterdir():
                    try:
                        name = os.readlink(fd).removesuffix(" (deleted)")
                    except FileNotFoundError:
                        continue
                    if observation and name == expected.node:
                        control_busy = True
                    elif not observation and name in (target, expected.node):
                        raise Unsafe("Foreign device handle held by PID " + process.name)
            except FileNotFoundError:
                continue
            except PermissionError as error:
                raise Unsafe("Cannot exclude foreign device ownership") from error
        # Check again after a potentially long process scan.
        verify(observe(), "Device changed during ownership check")
        if control_busy:
            raise StatusBusy("Native control FD busy; status deferred")

    def write_binding(self, device, driver, action):
        self.guard(device)
        path = self.sysfs / "bus/usb/drivers" / driver / action
        with path.open("w") as out:
            out.write(device.interface)

    def claim(self, device):
        try:
            if device.pid not in START_PIDS or device.driver not in START_OWNERS:
                raise Unsafe("Only a validated free or xpad-owned start interface can be acquired")
            self.claim_request(device)
            attribute = "acquire_" + device.pid
            if not (self.sysfs / "bus/usb/drivers/gs_native" / attribute).is_file():
                raise Unsafe("Kernel lacks scoped " + attribute + "; no binding changed")
        except (OSError, Unsafe) as error:
            raise AcquisitionUnchanged(str(error)) from error
        self.write_acquire(device)

    def write_acquire(self, device):
        try:
            device = self.acquisition_guard(device)
            if device.driver not in START_OWNERS:
                raise Unsafe("Scoped acquisition refuses a foreign or native owner")
            request = self.claim_request(device)
        except (OSError, Unsafe) as error:
            raise AcquisitionUnchanged(str(error)) from error
        # Pin and validate the exact USB object in the kernel before releasing
        # optional xpad. No userspace name-based unbind and no xpad dependency.
        path = self.sysfs / "bus/usb/drivers/gs_native" / ("acquire_" + device.pid)
        with path.open("w") as out:
            out.write(request)

    @staticmethod
    def claim_request(device):
        if (not PORT.fullmatch(device.port) or len(device.interface) >= 64 or device.pid not in START_PIDS or
                type(device.bus) is not int or not 0 < device.bus <= 65535 or
                type(device.address) is not int or not 0 < device.address <= 127 or
                any(type(value) is not int or not 0 < value < 2**64
                    for value in (device.sysfs_inode, device.parent_inode))):
            raise Unsafe("Invalid exact-instance kernel claim metadata")
        request = (f"1 {device.interface} {device.bus} {device.address} "
                   f"{device.sysfs_inode} {device.parent_inode}\n")
        if len(request.encode("ascii")) >= 192:
            raise Unsafe("Scoped kernel claim exceeds ABI limit")
        return request

    def write_claim(self, device):
        self.guard(device)
        if device.driver is not None:
            raise Unsafe("Scoped claim requires an unbound interface")
        request = self.claim_request(device)
        # Unlike generic driver/bind, the kernel atomically checks both kernfs
        # inode identities under the USB locks and grants only this synchronous
        # caller a one-shot probe. Autoprobe cannot consume or retain the grant.
        path = self.sysfs / "bus/usb/drivers/gs_native" / ("claim_" + device.pid)
        with path.open("w") as out:
            out.write(request)

    def restore(self, device):
        self.guard(device)
        if device.pid not in FALLBACK_PIDS or device.driver not in (None, "gs_native", "xpad"):
            raise Unsafe("Only known 100a/105e can be returned to xpad")
        if device.driver == "xpad":
            return
        if not (self.sysfs / "bus/usb/drivers/xpad/bind").is_file():
            raise Unsafe("xpad fallback unavailable; no native unbind, manual recovery required")
        if device.driver == "gs_native":
            self.write_binding(device, "gs_native", "unbind")
        current = self.scan().get(device.port)
        if not current or current.token != device.token or current.driver is not None:
            raise Unsafe("Return race; no xpad bind")
        self.write_binding(current, "xpad", "bind")
        current = self.scan().get(device.port)
        if not current or current.token != device.token or current.driver != "xpad":
            raise Unsafe("xpad return not verified")

    def start(self, operation, device, kernel_tokens=None):
        guard = self.observe_guard if operation in READ_ONLY else self.guard
        guard(device)
        argv = [self.client, operation, device.node]
        if operation == "bootstrap" and device.pid == "100a":
            argv.append("--handoff-xpad")
        elif operation in ('end', 'input-info', 'publish-input') or (operation == "info" and device.pid in NATIVE_PIDS):
            if (not isinstance(kernel_tokens, list) or len(kernel_tokens) != 2 or
                    any(type(value) is not int or not 0 < value < 2**64 for value in kernel_tokens)):
                raise Unsafe("Native operation requires exact positive kernel ownership tokens")
            argv.extend(["--expect-port", str(kernel_tokens[0]),
                         "--expect-instance", str(kernel_tokens[1])])
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, close_fds=True, start_new_session=True)
        os.set_blocking(child.stdout.fileno(), False)
        return Job(child)

    def haptics(self, device, commands):
        """Only the bounded private ABI, on the manager's validated instance."""
        if not 1 <= len(commands) <= 4:
            raise Unsafe("Expected one to four bounded motor commands")
        payloads = []
        seen = set()
        for motor, amplitude, duration, cancel in commands:
            if (type(motor) is not int or not 0 <= motor <= 3 or motor in seen or
                    type(amplitude) is not int or type(duration) is not int or type(cancel) is not bool or
                    (cancel and (amplitude or duration)) or
                    (not cancel and not (1 <= amplitude <= 100 and 1 <= duration <= 1000))):
                raise Unsafe("Invalid bounded haptic command")
            seen.add(motor)
            payloads.append(struct.pack("=8I", 1, motor, amplitude, duration, int(cancel), 0, 0, 0))
        self.guard(device)
        fd = os.open(device.node, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            if not stat.S_ISCHR(os.fstat(fd).st_mode):
                raise Unsafe("Native haptic control is not a character device")
            # A same-port node can be replaced between guard and open. Recheck
            # after acquiring the FD; it now pins the exact kernel instance.
            self.guard(device)
            for payload in payloads:
                # struct gsn_pulse ABI 1, GSN_PULSE_CANCEL=1. No arbitrary ioctl.
                fcntl.ioctl(fd, 0x40204773, payload)
        finally:
            os.close(fd)

    def poll(self, job):
        def drain():
            # Bound work as well as retained bytes, even for a noisy writer.
            for _ in range(32):
                try:
                    data = os.read(job.process.stdout.fileno(), 4096)
                except BlockingIOError:
                    return "again"
                if not data:
                    return "eof"
                remaining = 65536 - len(job.output)
                job.output.extend(data[:remaining])
                if len(data) > remaining:
                    job.output_limited = True
                    self.cancel(job)
            return "budget"

        first = drain()
        rc = job.process.poll()
        if rc is None:
            return None
        # Exit can follow the last EAGAIN with the success record still unread.
        # Keep nonblocking mode: inherited pipes must not hang the supervisor.
        final = first if first == "eof" else drain()
        if final == "budget":
            return None
        job.process.stdout.close()
        if final != "eof":
            return 1, job.output.decode("utf-8", "replace") + "\nERROR: stdout remained open after client exit"
        if job.output_limited:
            return 1, job.output.decode("utf-8", "replace") + "\nERROR: native client output exceeded limit"
        return rc, job.output.decode("utf-8", "replace")

    @staticmethod
    def cancel(job):
        if not job.cancelled and job.process.poll() is None:
            job.process.send_signal(signal.SIGTERM)
            job.cancelled = True


def serve_connection(conn, manager):
    """A disconnected/malformed control client cannot tear down the daemon."""
    try:
        conn.settimeout(1)
        _pid, uid, _gid = struct.unpack("3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid:
            raise Unsafe("Root control only")
        command = conn.recv(32).decode("ascii").strip()
        answer = {"ok": True, **manager.command(command)}
    except (OSError, UnicodeError, Unsafe) as error:
        answer = {"ok": False, "error": str(error)}
    try:
        conn.sendall(json.dumps(answer).encode() + b"\n")
    except OSError as error:
        # The command may already have taken effect. Do not undo it or attempt
        # another response on a broken socket; servicing other ports continues.
        manager.host.log("control_disconnected", message=str(error))


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid or st.st_mode & 0o077:
        raise Unsafe("Directory must be root-owned and mode 0700: " + str(path))


class HapticBackend:
    def __init__(self, manager):
        self.manager = manager

    def selections(self):
        if self.manager.inhibited or self.manager.scan_error:
            return {}
        return {hashlib.sha256(entry.device.token.encode()).hexdigest(): entry
                for port, entry in self.manager.entries.items()
                if entry.phase == "active" and port not in self.manager.port_errors and
                self.manager.observed.get(port) == entry.device}

    def devices(self):
        return {identity: {"name": "GameSir G7 Pro", "port": entry.device.port,
                           "busy": entry.job is not None}
                for identity, entry in self.selections().items()}

    def apply(self, identity, commands):
        from haptics_broker import Busy
        entry = self.selections().get(identity)
        if entry is None:
            raise Unsafe("Haptic instance is no longer owned and active")
        if entry.job is not None:
            raise Busy("Native control FD is in use by manager operation")
        self.manager.host.haptics(entry.device, commands)


def daemon(args):
    from haptics_broker import Broker, SocketServer
    private_directory(args.runtime)
    private_directory(args.state)
    lock = (args.runtime / "daemon.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    host = Host(args.client, args.state)
    host.configure_inputs()
    manager = Manager(host)
    # The service unit loads only this explicit opt-in configuration.
    for name in ("bootstrap_mode", "enable_output", "persistent_mode"):
        if (Path("/sys/module/gs_native/parameters") / name).read_text().strip() != "Y":
            raise Unsafe("Required gs_native parameter is not enabled: " + name)
    sockpath = args.runtime / "control.sock"
    sockpath.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sockpath))
    os.chmod(sockpath, 0o600)
    server.listen(4)
    server.setblocking(False)
    selector = selectors.DefaultSelector()
    selector.register(server, selectors.EVENT_READ)
    haptic_server = None
    try:
        haptic_server = SocketServer(Broker(HapticBackend(manager)), selector)
    except (OSError, KeyError) as error:
        manager.host.log("haptics_unavailable", message=str(error))
    stop = []

    def on_signal(_sig, _frame):
        stop.append(True)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    stop_deadline = None
    try:
        while True:
            host.drain_inputs()
            if stop and stop_deadline is None:
                # A system shutdown is not the user's persistent Deadband pause.
                manager.stopping = True
                stop_deadline = time.monotonic() + RETURN_SECONDS + JOB_SECONDS["bootstrap"] + 5
            manager.tick()
            if haptic_server:
                haptic_server.tick()
            if stop_deadline is not None and (manager.returned() or time.monotonic() > stop_deadline):
                return 0 if manager.returned() else 1
            for _key, _mask in selector.select(0.1):
                if _key.data is not None:
                    _key.data.handle(_key, _mask)
                    continue
                try:
                    conn, _ = server.accept()
                except OSError as error:
                    manager.host.log("control_accept_failed", message=str(error))
                    continue
                with conn:
                    serve_connection(conn, manager)
    finally:
        if host.inputs:
            host.inputs.close()
        if haptic_server:
            haptic_server.close()
        server.close()
        selector.close()
        sockpath.unlink(missing_ok=True)
        lock.close()


def control(args):
    def request(command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(3)
            connection.connect(str(args.runtime / "control.sock"))
            connection.sendall(command.encode() + b"\n")
            answer = bytearray()
            while not answer.endswith(b"\n"):
                chunk = connection.recv(65536)
                if not chunk or len(answer) > 1024 * 1024:
                    raise Unsafe("Incomplete/oversized service response")
                answer.extend(chunk)
            result = json.loads(answer)
            if not result.get("ok"):
                raise Unsafe(result.get("error", "Control failed"))
            return result

    result = request(args.command)
    if args.command == "release":
        deadline = time.monotonic() + RETURN_SECONDS + 15
        while not result["returned"] and time.monotonic() < deadline:
            time.sleep(0.25)
            result = request("status")
    print(json.dumps(result, indent=2))
    return 0 if args.command != "release" or result["returned"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("daemon", "status", "release", "resume"))
    parser.add_argument("--runtime", type=Path, default=Path("/run/gamesir-native"))
    parser.add_argument("--state", type=Path, default=Path("/var/lib/gamesir-native"))
    parser.add_argument("--client", type=Path, default=Path("/usr/lib/gamesir-native/gsnative-ctl"))
    args = parser.parse_args(argv)
    if os.geteuid():
        parser.error("Root authorization is required for service control")
    try:
        return daemon(args) if args.command == "daemon" else control(args)
    except (OSError, ValueError, Unsafe) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
