# SPDX-License-Identifier: GPL-2.0-only
"""Passive startup hypothesis replay, never a driver or command generator.

Only regular saved records enter through the existing CLI/record reader.
No binding, RF connection, transport ownership or sensor calibration is proved
by this model. See docs/STARTUP_TIMELINE_PROTOTYPE.md for evidence boundaries.
"""

from collections import Counter
from dataclasses import dataclass, field

from .protocol import decode_packet


KINDS = frozenset({"attach", "tick", "hello", "start_submit", "status_positive",
                   "status_negative", "pad", "imu", "unknown", "detach",
                   "cancel", "fault"})


@dataclass
class InstanceTimeline:
    """One immutable source/boot/enumeration lifetime, supplied by its caller.

    `freshness_us` is an explicit replay policy, not a hardware measurement.
    Missing data expires observations, never grants a retry or asserts RF-off.
    An announce-led start *candidate* is counted once; no bytes/actions result.
    """

    freshness_us: int = 3_000_000
    last_us: int | None = None
    first_error: dict | None = None
    terminal: str | None = None
    candidate_consumed: bool = False
    start_seen: bool = False
    hello_seen: bool = False
    last_pad_us: int | None = None
    last_imu_us: int | None = None
    status_candidate: str = "unknown"
    uncertain: bool = False
    counts: Counter = field(default_factory=Counter)

    def __post_init__(self):
        if type(self.freshness_us) is not int or not 1 <= self.freshness_us <= 60_000_000:
            raise ValueError("freshness_us must be an integer in 1..60000000")

    def _error(self, reason, timestamp_us):
        if self.first_error is None:
            self.first_error = {"reason": reason, "timestamp_us": timestamp_us}
        self.terminal = self.terminal or "blocked"
        self.last_pad_us = self.last_imu_us = None

    def observe(self, kind, timestamp_us, *, reason=None):
        if kind not in KINDS:
            raise ValueError("unsupported timeline event")
        if type(timestamp_us) is not int or timestamp_us < 0:
            raise ValueError("timestamp_us must be a nonnegative integer")
        if kind == "fault" and (not isinstance(reason, str) or not reason):
            raise ValueError("fault needs its original reason")
        self.counts[kind] += 1
        # Never sort, revive a terminal instance or overwrite its first fault.
        if self.last_us is not None and timestamp_us < self.last_us:
            self._error("host_clock_regression", timestamp_us)
            return self.snapshot()
        self.last_us = timestamp_us
        if self.terminal:
            return self.snapshot()
        if kind == "fault":
            self._error(reason, timestamp_us)
        elif kind in ("detach", "cancel"):
            self.terminal = kind
            self.last_pad_us = self.last_imu_us = None
        elif kind == "hello":
            # Hello after data may be a new controller generation, but
            # does not authorize replaying initialization on the same epoch.
            if self.last_pad_us is not None or self.last_imu_us is not None:
                self.uncertain = True
                self.last_pad_us = self.last_imu_us = None
            elif not self.uncertain and not self.candidate_consumed:
                self.candidate_consumed = True
                self.counts["announce_start_candidates"] += 1
            self.hello_seen = True
            self.status_candidate = "unknown"
        elif kind == "start_submit":
            self.start_seen = True
            self.candidate_consumed = True
            # Submission is neither a successful completion nor an ACK.
        elif kind.startswith("status_"):
            self.status_candidate = kind.removeprefix("status_")
            if kind == "status_negative":
                self.uncertain = True
                self.last_pad_us = self.last_imu_us = None
        elif kind in ("pad", "imu"):
            if not self.uncertain:
                if kind == "pad":
                    self.last_pad_us = timestamp_us
                else:
                    self.last_imu_us = timestamp_us
                # Already-streaming attachment needs no invented Hello/START.
                self.candidate_consumed = True
        return self.snapshot()

    def snapshot(self):
        def fresh(at):
            return at is not None and self.last_us - at <= self.freshness_us

        pad, imu = fresh(self.last_pad_us), fresh(self.last_imu_us)
        if self.terminal:
            phase = self.terminal
        elif self.uncertain:
            phase = "link_uncertain"
        elif pad and imu:
            phase = "pad_and_imu_observed"
        elif pad:
            phase = "pad_only_observed"
        elif imu:
            phase = "imu_only_observed"
        elif self.start_seen:
            phase = "waiting_after_start"
        elif self.hello_seen:
            phase = "announced"
        else:
            phase = "waiting_receiver"
        return {"phase": phase, "pad_fresh_under_replay_policy": pad,
                "imu_fresh_under_replay_policy": imu,
                "hello_seen": self.hello_seen, "start_submission_seen": self.start_seen,
                "status_bit_candidate": self.status_candidate,
                "rf_connected_proven": False, "runtime_ready_proven": False,
                "first_error": self.first_error, "counts": dict(self.counts)}


def classify_record(record):
    """Classify only the observed 3537:109c IF0 native routes. No raw output.

    Returns (kind, reason). Negative/partial transfers never supply evidence.
    Pending OUT submission -EINPROGRESS is normal; it is not a completion.
    """
    if (record.vid, record.pid, record.interface) != (0x3537, 0x109C, 0):
        return "ignored", "unsupported_identity_or_interface"
    if record.endpoint not in (0x82, 0x02):
        return "ignored", "unsupported_endpoint"
    if record.stage == "error" or (record.stage == "complete" and record.status != 0):
        return "fault", f"usb_{record.stage}_status_{record.status}"
    data = record.payload
    if record.capture_truncated or record.reported_length > len(data):
        return "truncated", "full_payload_required"
    if record.reported_length != len(data):
        return "malformed", "length_mismatch"
    if record.endpoint == 0x02:
        if record.stage == "submit" and record.status in (0, -115):
            if len(data) == 5 and data[:2] == b"\x05\x20" and data[3:] == b"\x01\x00":
                return "start_submit", None
        return "ignored", "only_observed_START_submission"
    if record.stage != "complete":
        return "ignored", "input_completion_required"
    if not data or len(data) > 64:
        return "malformed", "native_payload_length"
    if data[0] == 0x02:
        if len(data) != 32 or data[1] != 0x20 or data[3] != 28:
            return "malformed", "hello_header_or_length"
        if data[12:16] != b"\x37\x35\x9c\x10":
            return "malformed", "hello_identity_mismatch"
        return "hello", None
    if data[0] == 0x03:
        if len(data) != 8 or data[1] != 0x20 or data[3] != 4:
            return "malformed", "status_header_or_length"
        return ("status_positive" if data[4] & 0x80 else "status_negative"), None
    # Deliberately narrower than the existing general byte decoder.
    if len(data) == 36 and data[:2] == b"\x20\x00" and data[3] == 32:
        decoded = decode_packet(data)
        if decoded.disposition == "decoded":
            return "pad", None
    if len(data) == 64 and data[0] == 0x10 and data[3:5] == b"\x3c\xe0":
        return "imu", None
    return "unknown", None


def analyze_startup(records, *, pid=None, bus=None, address=None, include_events=False,
                    freshness_us=3_000_000):
    """File order, separate provenance/enumeration keys, payload-free output.

    First packet metadata merely implies a receiver observation. It is not
    proof of descriptor timing, native ownership, radio-on or a physical port.
    The input session MUST identify one boot/enumeration epoch, even if bus and
    address are reused. Neither USB addresses nor source IDs are individual UIDs.
    """
    InstanceTimeline(freshness_us)  # validate even for an empty/foreign file
    instances, events, counts = {}, [], Counter()
    for index, record in enumerate(records, 1):
        counts["records_total"] += 1
        if ((pid is not None and record.pid != pid) or
                (bus is not None and record.bus != bus) or
                (address is not None and record.address != address)):
            counts["filtered"] += 1
            continue
        kind, reason = classify_record(record)
        counts[kind] += 1
        if kind == "ignored":
            continue
        # IN/OUT share one instance, never source/session/PID/address/IF epochs.
        key = record.stream_key[:-1]
        if key not in instances:
            metadata = record.metadata()
            metadata.pop("endpoint")
            instance = InstanceTimeline(freshness_us)
            instance.observe("attach", record.timestamp_us)
            instances[key] = (metadata, instance, len(instances))
        _, instance, instance_index = instances[key]
        event_kind = "unknown" if kind in ("malformed", "truncated") else kind
        snapshot = instance.observe(event_kind, record.timestamp_us, reason=reason)
        if include_events:
            events.append({"record_index": index, "instance_index": instance_index,
                           "timestamp_us": record.timestamp_us, "kind": kind,
                           "reason": reason, "phase": snapshot["phase"]})
    return {"schema_version": 1, "scope": "passive_offline_startup_hypothesis",
            "freshness_policy_us": freshness_us, "counts": dict(counts),
            "commands_sent": 0, "ownership_or_recovery_proven": False,
            "instances": [{"identity": metadata, **instance.snapshot()}
                          for metadata, instance, _ in instances.values()],
            **({"events": events} if include_events else {})}
