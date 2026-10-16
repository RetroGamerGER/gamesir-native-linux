# SPDX-License-Identifier: GPL-2.0-only
"""File replay statistics. Observation cadence is not device sampling rate."""

from collections import Counter, defaultdict
from dataclasses import asdict
import math
import statistics

from .protocol import Decoded, decode_packet


def decode_record(record) -> Decoded:
    if record.vid != 0x3537:
        return Decoded("ignored", "foreign_vendor", reason="target_vendor_is_3537")
    if record.interface != 0:
        return Decoded("ignored", "unsupported_interface", reason="interface_1_not_a_verified_channel")
    if record.endpoint not in (0x82, 0x02):
        return Decoded("ignored", "unsupported_endpoint", reason="only_82_and_02_supported")
    if record.stage != "complete":
        return Decoded("ignored", "transfer_not_complete", reason="submissions_and_errors_not_replayed")
    if record.status != 0:
        return Decoded("ignored", "transfer_error", reason="nonzero_completion_status")
    if record.reported_length < len(record.payload):
        return Decoded("malformed", "capture_length_mismatch", reason="captured_bytes_exceed_reported_length")
    if record.capture_truncated or record.reported_length > len(record.payload):
        return Decoded("truncated", "capture_truncated", reason="full_payload_required")
    return decode_packet(record.payload, endpoint=record.endpoint)


def timing_summary(timestamps: list[int]) -> dict:
    intervals = [right - left for left, right in zip(timestamps, timestamps[1:])]
    regressions = sum(delta < 0 for delta in intervals)
    output = {
        "records": len(timestamps), "intervals": len(intervals),
        "first_timestamp_us": timestamps[0] if timestamps else None,
        "last_timestamp_us": timestamps[-1] if timestamps else None,
        "zero_intervals": intervals.count(0), "clock_regressions": regressions,
        "statistics_us": None, "observation_rate_hz": None,
        "meaning": "file_order_and_host_or_synthetic_time; not_sensor_sampling_or_latency",
    }
    if intervals and not regressions:
        ordered = sorted(intervals)
        output["statistics_us"] = {
            "min": min(intervals), "max": max(intervals),
            "median": statistics.median(intervals),
            "p95_nearest_rank": ordered[math.ceil(0.95 * len(ordered)) - 1],
        }
        span = timestamps[-1] - timestamps[0]
        if span > 0:
            output["observation_rate_hz"] = len(intervals) * 1000000 / span
    return output


def analyze(records, *, pid: int | None = None, bus: int | None = None,
            address: int | None = None, include_events: bool = False) -> dict:
    counts = Counter()
    kinds = Counter()
    groups = {}
    events = []
    for index, record in enumerate(records, 1):
        counts["records_total"] += 1
        if ((pid is not None and record.pid != pid)
                or (bus is not None and record.bus != bus)
                or (address is not None and record.address != address)):
            counts["filtered"] += 1
            continue
        result = decode_record(record)
        counts[result.disposition] += 1
        kinds[result.kind] += 1
        if record.stream_key not in groups:
            groups[record.stream_key] = {
                "metadata": record.metadata(), "counts": Counter(),
                "accepted_kind_timestamps": defaultdict(list), "accepted_timestamps": [],
            }
        group = groups[record.stream_key]
        group["counts"][result.disposition] += 1
        if result.disposition == "decoded":
            group["accepted_kind_timestamps"][result.kind].append(record.timestamp_us)
            group["accepted_timestamps"].append(record.timestamp_us)
        if include_events:
            events.append({
                "record_number": index, **record.metadata(),
                "timestamp_us": record.timestamp_us, "stage": record.stage,
                "completion_status": record.status, "reported_length": record.reported_length,
                "captured_length": len(record.payload), "data_hex": record.payload.hex(),
                **asdict(result),
            })
    streams = []
    for group in groups.values():
        normal_count = sum(len(group["accepted_kind_timestamps"].get(kind, []))
                           for kind in ("x360_input", "gip_input_basic"))
        imu_count = len(group["accepted_kind_timestamps"].get("gamesir_telemetry", []))
        streams.append({
            **group["metadata"], "counts": dict(group["counts"]),
            "accepted_transfer_cadence": timing_summary(group["accepted_timestamps"]),
            "cadence_by_packet_kind": {kind: timing_summary(times)
                                       for kind, times in group["accepted_kind_timestamps"].items()},
            "normal_and_imu_records_in_same_stream": bool(normal_count and imu_count),
            "co_presence_meaning": "records_present_only; not_continuous_simultaneous_hardware_support",
        })
    return {
        "poc_version": "0.1.0", "operation": "offline_file_replay",
        "counts": dict(counts), "packet_kinds": dict(kinds), "streams": streams,
        "hardware_access": False, "hardware_feasibility_proven": False,
        "evidence_limit": "synthetic_records_are_parser_tests; capture_metadata_is_user_supplied",
        "transport_limit": "mixed_synthetic_frames_are_not_a_USB_bandwidth_model",
        **({"events": events} if include_events else {}),
    }
