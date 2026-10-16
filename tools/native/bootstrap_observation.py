#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure observation policy for an explicitly approved 100a -> 109c test.

Unknown metadata is neither absence nor ownership proof. This module issues
no commands and performs no I/O. The runner retains its exact instance,
parent, kernel-token and lease checks before opening any input observer.
"""
from dataclasses import dataclass
import math
import re

POLICY_VERSION = 1


class ObservationError(RuntimeError):
    """The test must halt; cleanup still requires its own prior approval."""


TRANSITION_PHASES = frozenset(("bootstrapping", "locating", "attesting"))
STARTUP_PHASES = TRANSITION_PHASES | {"waiting_input", "active"}
PORT = re.compile(r"[1-9][0-9]*-[1-9][0-9]*(?:\.[1-9][0-9]*)*")
EMPTY_BASES = {"idVendor": 16, "idProduct": 16, "bConfigurationValue": 10,
               "busnum": 10, "devnum": 10}


@dataclass(frozen=True)
class StartupObservation:
    phase: str | None
    quarantined: bool = False


def _valid_port(port):
    if type(port) is not str or not PORT.fullmatch(port):
        raise ObservationError("Invalid expected USB port")


def _metadata_gap(message, port):
    if type(message) is not str:
        return False
    if message == "USB metadata changed during enumeration":
        return True
    # Only known root-device fields, exact path and matching numeric base.
    # Invalid values, permissions, interface/endpoint changes are NOT gaps.
    for field, base in EMPTY_BASES.items():
        if message == (f"Empty USB metadata: /sys/bus/usb/devices/{port}/"
                       f"{field} (base {base})"):
            return True
    return False


def _error_map(errors, port):
    if type(errors) is not dict:
        raise ObservationError("Invalid per-port metadata error map")
    if not errors:
        return False
    if set(errors) != {port} or not _metadata_gap(errors[port], port):
        raise ObservationError("Unexpected USB metadata error: " + repr(errors))
    return True


def _healthy_status(status, port):
    if type(status) is not dict or status.get("ok") is not True:
        raise ObservationError("Manager status unavailable or invalid")
    if status.get("paused") is not False or status.get("scan_error") != "":
        raise ObservationError("Manager paused or global scan failed")
    devices, errors = status.get("devices"), status.get("port_errors")
    if type(devices) is not dict or type(errors) is not dict:
        raise ObservationError("Invalid manager device/error inventory")
    if set(devices) - {port}:
        raise ObservationError("Unexpected managed USB device")
    if port not in devices:
        if errors:
            raise ObservationError("Metadata error without expected managed transition")
        return None, errors
    entry = devices[port]
    if type(entry) is not dict or entry.get("error") != "":
        raise ObservationError("Current manager device error or invalid entry")
    phase = entry.get("phase")
    if type(phase) is not str or phase not in STARTUP_PHASES:
        raise ObservationError("Unexpected manager phase: " + repr(phase))
    if entry.get("pid") != ("109c" if phase == "active" else "100a"):
        raise ObservationError("Manager source/native identity changed")
    if type(entry.get("busy")) is not bool:
        raise ObservationError("Invalid manager operation state")
    if phase == "bootstrapping" and not entry["busy"]:
        raise ObservationError("Bootstrap has no running operation")
    diagnostic = entry.get("bootstrap_diagnostic")
    if type(diagnostic) is not dict:
        raise ObservationError("Invalid current bootstrap diagnostic")
    if diagnostic:
        kernel = diagnostic.get("reported_kernel_status")
        if (type(diagnostic.get("returncode")) is not int or diagnostic["returncode"] != 0 or
                diagnostic.get("timed_out") is not False or type(kernel) is not dict or
                type(kernel.get("error")) is not int or kernel["error"] != 0):
            raise ObservationError("Current bootstrap diagnostic reports failure")
    # recent_failures is preserved history, never the result of this run.
    return phase, errors


@dataclass(frozen=True)
class StartupWindow:
    port: str
    deadline: float

    def __post_init__(self):
        _valid_port(self.port)
        if (type(self.deadline) not in (int, float) or
                not math.isfinite(self.deadline) or self.deadline <= 0):
            raise ObservationError("Invalid fixed startup deadline")

    def check_deadline(self, now):
        if (type(now) not in (int, float) or not math.isfinite(now) or
                now < 0 or now >= self.deadline):
            raise ObservationError("Native startup observation deadline reached; no extension")

    def check_status(self, status, now):
        self.check_deadline(now)  # Even clean 'active' must arrive in time.
        phase, errors = _healthy_status(status, self.port)
        quarantined = _error_map(errors, self.port)
        if quarantined and phase not in TRANSITION_PHASES:
            raise ObservationError("Metadata gap outside the expected USB transition")
        return StartupObservation(phase, quarantined)

    def check_scan(self, errors, now):
        """Fresh-scan race after cached active: True means wait, NEVER ready.

        The runner must first reject foreign inventory, keep journal checks
        running and later repeat its complete identity/lease attestation.
        """
        self.check_deadline(now)
        return _error_map(errors, self.port)


def check_runtime_status(status, port):
    """No transition exception after the input/IMU observer has started."""
    _valid_port(port)
    phase, errors = _healthy_status(status, port)
    if errors or phase != "active":
        raise ObservationError("Native runtime or metadata state lost")


def wait_for_native(window, *, read_status, read_inventory, attest,
                    check_journal, emit, now, wait):
    """Observe the existing runner's startup; callbacks supply all I/O.

    There are no resume/release/bind/observer callbacks here. A metadata gap
    only delays complete validation inside the original fixed deadline.
    ``attest`` must verify the exact new instance, parent and kernel lease;
    the input observer may be opened only after this function returns.
    """
    previous_phase = object()
    previous_gap = None
    while True:
        window.check_deadline(now())
        status = read_status()
        observation = window.check_status(status, now())
        check_journal()  # A gap must never hide a new kernel error.
        window.check_deadline(now())
        if observation.phase != previous_phase:
            emit("manager_phase", {"phase": observation.phase})
            if observation.phase == "waiting_input":
                emit("waiting_input", {"instruction":
                     "Bitte jetzt A drücken und beide Sticks bewegen, bis der Start bestätigt wird."})
            previous_phase = observation.phase

        gap = "manager" if observation.quarantined else None
        if not gap and observation.phase == "active":
            devices, errors = read_inventory()
            window.check_deadline(now())
            if not isinstance(devices, dict) or set(devices) - {window.port}:
                raise ObservationError("Unexpected device in fresh startup inventory")
            if window.check_scan(errors, now()):
                gap = "fresh_inventory"
            else:
                proof = attest(devices)
                check_journal()
                window.check_deadline(now())  # Includes time spent checking the lease.
                if previous_gap:
                    emit("metadata_quarantine_cleared", {"port": window.port})
                window.check_deadline(now())  # Evidence output can block, too.
                return proof, status

        if gap != previous_gap:
            if gap:
                emit("metadata_quarantine", {"port": window.port,
                     "source": gap, "phase": observation.phase,
                     "fixed_deadline": window.deadline})
            elif previous_gap:
                emit("metadata_quarantine_cleared", {"port": window.port})
            previous_gap = gap
        wait(0.5)
