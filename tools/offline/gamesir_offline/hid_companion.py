# SPDX-License-Identifier: GPL-2.0-only
"""File-only XInput/HID companion experiment; no device or command backend.

Reuse the payload decoder for the observed 10/3c/e0 shape, not its transport
authority. The meaning of its extra-button fields on 100a/IF1 is unverified.
Report 12 and the 8K heartbeat are not a supported ordinary-G7-Pro protocol.
"""

from collections import Counter, defaultdict
from dataclasses import asdict

from .protocol import Decoded, decode_packet
from .replay import timing_summary


def _route(record):
    if record.vid != 0x3537 or record.pid != 0x100A:
        return None
    return {(0, 0x82): "normal", (1, 0x84): "raw_hid",
            (1, 0x04): "hid_output"}.get((record.interface, record.endpoint))


def _candidate(record):
    return (record.interface == 1 and record.endpoint == 0x04
            and record.payload == b"\x0f\xf2" + bytes(62))


def _redact_payload(record, result, channel):
    if result.kind in ("unsupported_identity", "unsupported_channel", "hid_nonvendor_ignored"):
        return True
    # Classification can stop at a transfer error/truncation before its report
    # ID is inspected. Such keyboard/mouse bytes still need the same privacy.
    return bool(channel == "raw_hid" and record.payload and
                (record.payload[0] in (0x02, 0x03, 0x09) or not any(record.payload)))


def _decode(record, channel):
    if record.vid != 0x3537 or record.pid != 0x100A:
        return Decoded("ignored", "unsupported_identity", reason="only_3537_100a")
    if channel is None:
        return Decoded("ignored", "unsupported_channel", reason="only_IF0_82_IF1_84_IF1_04")
    if record.stage != "complete":
        return Decoded("ignored", "transfer_not_complete", reason="no_completed_payload")
    if record.status != 0:
        return Decoded("ignored", "transfer_error", reason="nonzero_completion_status")
    if record.reported_length < len(record.payload):
        return Decoded("malformed", "capture_length_mismatch", reason="captured_exceeds_reported")
    if record.capture_truncated or record.reported_length > len(record.payload):
        return Decoded("truncated", "capture_truncated", reason="full_payload_required")
    data = record.payload
    if not data or len(data) > 64:
        return Decoded("malformed", "invalid_payload_length", reason="requires_1_through_64_bytes")
    if channel == "normal":
        if len(data) != 20 or data[:2] != b"\x00\x14":
            return Decoded("unknown", "unsupported_normal_report", reason="only_20_byte_00_14_XInput")
        return decode_packet(data)
    if channel == "hid_output":
        if _candidate(record):
            return Decoded("candidate", "hid_8k_heartbeat_candidate", {
                "hypothesis": "8K_0f_f2_shape_only; ordinary_100a_command_unverified",
                "successful_transport_completion": True, "activation_proven": False,
            })
        return Decoded("unknown", "hid_output_unknown", reason="output_not_decoded_or_transmitted")
    if data[0] == 0x12:
        return Decoded("unknown", "hid_report_12_unknown", reason="no_8K_offsets_for_ordinary_100a")
    # Only classify these nonvendor collections; never expose their key events.
    if data[0] in (0x02, 0x03, 0x09) or (len(data) == 13 and not any(data)):
        return Decoded("ignored", "hid_nonvendor_ignored", reason="keyboard_mouse_consumer_or_null")
    if data[0] != 0x10:
        return Decoded("unknown", "hid_report_unknown", reason="unrecognized_report_id")
    if len(data) != 64:
        return Decoded("malformed", "hid_telemetry_length", reason="report_10_requires_exactly_64_bytes")
    if data[3:5] != b"\x3c\xe0":
        return Decoded("unknown", "hid_report_10_unknown", reason="requires_observed_3c_e0_signature")
    # This deliberately calls the byte decoder, not decode_record(): legacy
    # replay still rejects IF1. No USB endpoint is opened or granted ownership.
    decoded = decode_packet(data)
    fields = dict(decoded.fields)
    fields["paddle_layout_100a_verified"] = False
    fields["field_interpretation"] = "known_extended_layout_hypothesis_on_100a_IF1"
    return Decoded("decoded", "hid_raw_telemetry_hypothesis", fields)


def _base_key(record):
    return (record.source_kind, record.source_id, record.session, record.timebase,
            record.vid, record.pid, record.bus, record.address)


def _identity(record):
    return {"source": {"kind": record.source_kind, "id": record.source_id},
            "session": record.session, "timebase": record.timebase,
            "device": {"vid": f"{record.vid:04x}", "pid": f"{record.pid:04x}",
                       "bus": record.bus, "address": record.address}}


def analyze_hid_companion(records, *, pid=None, bus=None, address=None,
                          include_events=False, max_observation_age_us=100000):
    """Demultiplex saved records without asserting activation or live readiness.

    File metadata defines the instance boundary. Callers must supply a new
    session for a new epoch that reuses an address. A timestamp regression
    quarantines latest-state composition for that instance, without sorting.
    Cadence remains observation timing, never a sensor sampling-rate claim.
    The age ceiling is a conservative file-display policy, not a hardware
    sampling, transport-latency or freshness guarantee.
    """
    if type(max_observation_age_us) is not int or not 0 <= max_observation_age_us <= 1000000:
        raise ValueError("max_observation_age_us must be an integer in 0..1000000")
    counts, kinds, groups, events = Counter(), Counter(), {}, []
    for index, record in enumerate(records, 1):
        counts["records_total"] += 1
        if ((pid is not None and record.pid != pid)
                or (bus is not None and record.bus != bus)
                or (address is not None and record.address != address)):
            counts["filtered"] += 1
            continue
        channel = _route(record)
        result = _decode(record, channel)
        counts[result.disposition] += 1
        kinds[result.kind] += 1
        group = None
        if channel is not None:
            key = _base_key(record)
            if key not in groups:
                groups[key] = {"identity": _identity(record), "counts": Counter(),
                               "cadence": defaultdict(list), "last_timestamp_us": None,
                               "clock_regressions": 0, "quarantined": False,
                               "latest": {"normal": None, "raw_hid": None}}
            group = groups[key]
            group["counts"][result.disposition] += 1
            previous = group["last_timestamp_us"]
            if previous is not None and record.timestamp_us < previous:
                group["clock_regressions"] += 1
                group["quarantined"] = True
                group["latest"] = {"normal": None, "raw_hid": None}
            group["last_timestamp_us"] = record.timestamp_us
            if result.disposition == "decoded":
                group["cadence"][channel].append(record.timestamp_us)
                if not group["quarantined"]:
                    group["latest"][channel] = {"record_number": index,
                                               "timestamp_us": record.timestamp_us,
                                               "fields": result.fields}
            elif channel in group["latest"] and (
                    result.disposition in ("malformed", "truncated")
                    or record.stage == "error"
                    or (record.stage == "complete" and record.status != 0)):
                # A real failed/invalid observation invalidates that channel.
                # Normal URB submissions and unrelated HID collections do not.
                group["latest"][channel] = None
            if _candidate(record):
                name = ("successful_completions" if result.disposition == "candidate"
                        else "submissions" if record.stage == "submit"
                        else "unproven_transfers")
                counts[f"heartbeat_candidate_{name}"] += 1
        if include_events:
            redacted = _redact_payload(record, result, channel)
            events.append({"record_number": index, **record.metadata(),
                           "timestamp_us": record.timestamp_us, "stage": record.stage,
                           "completion_status": record.status,
                           "reported_length": record.reported_length,
                           "captured_length": len(record.payload),
                           "data_hex": None if redacted else record.payload.hex(),
                           "payload_redacted": redacted, "channel": channel,
                           "heartbeat_candidate_shape": bool(channel == "hid_output" and _candidate(record)),
                           "chronology_quarantined": bool(group and group["quarantined"]),
                           **asdict(result)})
    instances = []
    for group in groups.values():
        at = group["last_timestamp_us"]
        ages = {name: at - item["timestamp_us"] if item else None
                for name, item in group["latest"].items()}
        stale = [name for name, age in ages.items()
                 if age is not None and age > max_observation_age_us]
        latest = {name: None if name in stale else item
                  for name, item in group["latest"].items()}
        instances.append({**group["identity"], "counts": dict(group["counts"]),
                          "channel_cadence": {name: timing_summary(times)
                                              for name, times in group["cadence"].items()},
                          "clock_regressions": group["clock_regressions"],
                          "chronology_quarantined": group["quarantined"],
                          "latest_observation": {
                              "at_timestamp_us": at, **latest,
                              "age_us": ages, "stale_channels": stale,
                              "same_instance_samples_present": all(latest.values()),
                              "freshness_proven": False,
                              "meaning": "separate_last_file_samples; not_atomic_or_live_state",
                          }})
    return {"schema_version": 1, "operation": "offline_hid_companion",
            "counts": dict(counts), "packet_kinds": dict(kinds), "instances": instances,
            "hardware_access": False, "readiness_proven": False,
            "activation_proven": False, "continuous_stream_proven": False,
            "paddle_layout_100a_verified": False, "motor_support_proven": False,
            "sensor_units": "raw_counts; no_calibration_or_8K_scaling",
            "display_age_policy": {"max_observation_age_us": max_observation_age_us,
                                   "meaning": "host_file_display_only; not_sensor_sampling_or_live_freshness"},
            "identity_limit": "source_and_epoch_metadata_are_asserted; not_device_identity_proof",
            "output_policy": "recorded_bytes_only; no_command_builder_or_transmitter",
            **({"events": events} if include_events else {})}
