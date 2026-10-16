# SPDX-License-Identifier: GPL-2.0-only
"""Command line interface for existing regular JSONL files only."""

import argparse
import json
import sys

from .records import RecordError, read_records
from .replay import analyze


def _pid(value):
    if len(value) != 4 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise argparse.ArgumentTypeError("PID must contain four hex characters, e.g. 100a")
    return int(value, 16)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GameSir file-only offline protocol replay; no USB access")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="decode a saved JSONL file")
    replay.add_argument("file")
    replay.add_argument("--pid", type=_pid, help="select one product identity; no mode inference")
    replay.add_argument("--bus", type=int)
    replay.add_argument("--address", type=int)
    replay.add_argument("--events", action="store_true", help="include every selected record and its decoded fields")
    replay.add_argument("--strict", action="store_true", help="exit 1 on malformed/truncated selected packets")
    args = parser.parse_args(argv)
    if args.bus is not None and not 1 <= args.bus <= 65535:
        parser.error("bus must be in 1..65535")
    if args.address is not None and not 1 <= args.address <= 127:
        parser.error("address must be in 1..127")
    try:
        result = analyze(read_records(args.file), pid=args.pid, bus=args.bus,
                         address=args.address, include_events=args.events)
    except (OSError, RecordError) as error:
        print(f"offline replay: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if args.strict and any(result["counts"].get(key, 0) for key in ("malformed", "truncated")):
        return 1
    return 0
