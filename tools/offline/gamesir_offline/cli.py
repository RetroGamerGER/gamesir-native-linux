# SPDX-License-Identifier: GPL-2.0-only
"""Command line interface for existing regular JSONL files only."""

import argparse
import json
import sys

from .records import RecordError, read_records
from .replay import analyze
from .hid_companion import analyze_hid_companion
from .startup_timeline import analyze_startup


def _pid(value):
    if len(value) != 4 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise argparse.ArgumentTypeError("PID must contain four hex characters, e.g. 100a")
    return int(value, 16)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GameSir file-only offline protocol replay; no USB access")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="decode a saved JSONL file")
    hid_replay = sub.add_parser("hid-replay", help="observe saved XInput/IF1 HID records; no live transport")
    startup = sub.add_parser("startup-replay", help="passive native GIP startup hypothesis; saved files only")
    startup.add_argument("--freshness-us", type=int, default=3000000,
                         help="explicit replay observation age; not a measured RF timeout")
    for command in (replay, hid_replay, startup):
        command.add_argument("file")
        command.add_argument("--pid", type=_pid, help="select one product identity; no mode inference")
        command.add_argument("--bus", type=int)
        command.add_argument("--address", type=int)
        command.add_argument("--events", action="store_true", help="include selected record observations")
        command.add_argument("--strict", action="store_true", help="exit 1 on malformed/truncated selected packets")
    hid_replay.add_argument("--max-age-us", type=int, default=100000,
                            help="host display-coherence window, 1..1000000 us; not sensor freshness")
    args = parser.parse_args(argv)
    if args.bus is not None and not 1 <= args.bus <= 65535:
        parser.error("bus must be in 1..65535")
    if args.address is not None and not 1 <= args.address <= 127:
        parser.error("address must be in 1..127")
    if args.command == "hid-replay" and not 1 <= args.max_age_us <= 1000000:
        parser.error("max-age-us must be in 1..1000000")
    if args.command == "startup-replay" and not 1 <= args.freshness_us <= 60000000:
        parser.error("freshness-us must be in 1..60000000")
    try:
        if args.command == "hid-replay":
            result = analyze_hid_companion(
                read_records(args.file), pid=args.pid, bus=args.bus,
                address=args.address, include_events=args.events,
                max_observation_age_us=args.max_age_us)
        elif args.command == "startup-replay":
            result = analyze_startup(read_records(args.file), pid=args.pid, bus=args.bus,
                                     address=args.address, include_events=args.events,
                                     freshness_us=args.freshness_us)
        else:
            result = analyze(read_records(args.file), pid=args.pid, bus=args.bus,
                             address=args.address, include_events=args.events)
    except (OSError, RecordError) as error:
        label = "offline hid replay" if args.command == "hid-replay" else "offline replay"
        print(f"{label}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if args.strict and any(result["counts"].get(key, 0) for key in ("malformed", "truncated")):
        return 1
    if args.command == "startup-replay" and args.strict and any(
            item["first_error"] is not None for item in result["instances"]):
        return 1
    return 0
