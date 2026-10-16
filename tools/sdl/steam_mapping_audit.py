#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Audit a saved Steam controller log and print a native SDL mapping proposal.

No SDL initialization, device discovery, Steam start or configuration write.
Only an explicitly supplied, bounded regular file is read. A proposal is not
evidence that Steam exposes paddles or that a game accepts additional buttons.
"""
import argparse
import json
import os
import re
import stat

from gamesir_mapping import mapping, native_guid_pid

MAX_LOG_BYTES = 4 * 1024 * 1024
MAX_MAPPING_CHARS = 4096
TARGET_LINE = re.compile(
    r"^(?:\[[0-9 :.-]+\]\s*)?SDL Mapping for 3537/(109c|105e):\s*(.*)$",
    re.IGNORECASE,
)
PADDLE_FIELDS = frozenset(("paddle1", "paddle2", "paddle3", "paddle4"))
MISC_FIELDS = frozenset(("misc1", "misc2"))
EXTRA_FIELDS = PADDLE_FIELDS | MISC_FIELDS
SAFE_NAMES = frozenset(("GameSir G7 Pro", "Generic X-Box pad"))
BINDING = re.compile(r"[+-]?(?:b[0-9]{1,3}|a[0-9]{1,3}~?|h[0-9]{1,3}\.[0-9]{1,3})")


class AuditError(ValueError):
    """A deliberate refusal with a non-sensitive diagnostic."""


def _candidate(guid):
    try:
        return mapping(guid, "alpha17")
    except ValueError:
        raise AuditError("Expected a native USB 3537:109c/105e evdev GUID") from None


def _fields(line):
    parts = line.split(",")
    fields = {}
    for part in parts[2:]:
        if not part:
            continue
        key, separator, value = part.partition(":")
        if not separator or key in fields:
            raise AuditError("Malformed or duplicate mapping field")
        fields[key] = value
    return parts[:2], fields


def _record(line, line_number, declared_pid):
    if len(line) > MAX_MAPPING_CHARS:
        raise AuditError("Target mapping exceeds the size limit")
    head, observed = _fields(line)
    if len(head) != 2:
        raise AuditError("Incomplete target mapping")
    guid = head[0].lower()
    candidate_line = _candidate(guid)
    if native_guid_pid(guid) != declared_pid:
        raise AuditError("Declared mapping product does not match its SDL GUID")
    _, candidate = _fields(candidate_line)
    if set(observed) - set(candidate) - {"crc"}:
        # Do not silently remove a hint, inversion or other unknown metadata.
        raise AuditError("Unreviewed mapping fields require manual analysis")
    for key, value in observed.items():
        if key == "platform":
            if value != "Linux":
                raise AuditError("Expected a Linux mapping")
        elif key == "crc":
            # SDL_PrivateAddMappingForGUID writes the GUID's name CRC as four
            # hex digits. SDL_GetJoystickGUIDInfo reads it at bytes 2:4, LE.
            # This is matching metadata, not a button/hint or device-unique ID.
            if not re.fullmatch(r"[0-9a-fA-F]{4}", value):
                raise AuditError("Malformed SDL mapping CRC")
            if int(value, 16) != int.from_bytes(bytes.fromhex(guid)[2:4], "little"):
                raise AuditError("SDL mapping CRC does not match the selected GUID")
        elif not BINDING.fullmatch(value):
            raise AuditError("Malformed mapping binding")
    if "crc" in observed:
        # Preserve an explicitly validated restriction; never broaden matching
        # by dropping it, or add CRC metadata to a mapping that lacked it.
        candidate["crc"] = observed["crc"]
    # Names may contain user-supplied personal text. Never reflect that text.
    name = head[1] if head[1] in SAFE_NAMES else "<redacted-device-name>"
    return {"guid": guid, "name": name, "fields": observed,
            "line": line_number, "candidate": candidate}


def audit_text(text, guid=None):
    """Select the last mapping for one target GUID, then verify its contract.

    Multiple distinct GUIDs require an explicit selection. Repeated mappings
    of the same GUID use file order, not a guessed wall-clock interpretation.
    No source line other than validated mapping fields enters the result.
    """
    if len(text.encode("utf-8")) > MAX_LOG_BYTES:
        raise AuditError("Log exceeds the size limit")
    selected_guid = None
    if guid is not None:
        _candidate(guid)
        selected_guid = guid.lower()
    records = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = TARGET_LINE.fullmatch(line)
        if match:
            records.append(_record(match.group(2), line_number, int(match.group(1), 16)))
    if not records:
        raise AuditError("No native 3537:109c/105e SDL mapping found")
    identities = sorted({record["guid"] for record in records})
    if selected_guid is None:
        if len(identities) != 1:
            raise AuditError("Several target GUIDs found; select one explicitly with --guid")
        selected_guid = identities[0]
    selected = [record for record in records if record["guid"] == selected_guid]
    if not selected:
        raise AuditError("Selected GUID does not occur in the target log mappings")
    latest = selected[-1]
    observed, canonical = latest["fields"], latest["candidate"]
    # KEY_RECORD/code 708 are outside this four-paddle task. Preserve a proven
    # canonical binding if present, but never introduce those extra controls.
    if any(observed[key] != canonical[key] for key in MISC_FIELDS & set(observed)):
        raise AuditError("Existing auxiliary buttons differ; no proposal generated")
    candidate = {key: value for key, value in canonical.items()
                 if key not in MISC_FIELDS or key in observed}
    standard = set(candidate) - EXTRA_FIELDS
    if any(observed.get(key) != candidate[key] for key in standard):
        raise AuditError("Standard buttons, axes, D-pad or platform differ; no proposal generated")
    difference = []
    for key in sorted(candidate):
        if observed.get(key) != candidate[key]:
            difference.append({"field": key, "before": observed.get(key),
                               "after": candidate[key]})
    if latest["name"] != "GameSir G7 Pro":
        difference.append({"field": "name", "before": latest["name"],
                           "after": "GameSir G7 Pro"})
    # Reconstruct a sanitized mapping: never return arbitrary raw log text.
    sanitized = [selected_guid, latest["name"]]
    sanitized.extend(f"{key}:{value}" for key, value in observed.items())
    result = {
        "schema_version": 1,
        "ok": True,
        "guid": selected_guid,
        "profile": "alpha17",
        "selection": {"last_matching_line": latest["line"],
                      "matching_records": len(selected),
                      "distinct_target_guids": len(identities)},
        "observed_mapping": ",".join(sanitized) + ",",
        "candidate_mapping": ",".join(
            [selected_guid, "GameSir G7 Pro"] +
            [f"{key}:{value}" for key, value in candidate.items()]) + ",",
        "field_diff": difference,
        "standard_bindings_unchanged": True,
        "status": "already_matches" if not difference else "proposal_only",
        "limitations": [
            "alpha17 capabilities must be established independently for the target device",
            "selection uses the last matching entry in a saved log, not current hardware state",
            "no Steam configuration was changed",
            "no paddle recognition or in-game support was tested",
            "standard XInput does not gain additional buttons from an SDL mapping",
        ],
    }
    if native_guid_pid(selected_guid) == 0x105e:
        result["physical_paddle_labels"] = "unconfirmed"
        result["limitations"].append(
            "105e paddle fields use the common native key order; physical L4/R4/L5/R5 labels remain unconfirmed")
    return result


def read_regular_log(path, max_bytes=MAX_LOG_BYTES):
    """Read a bounded regular inode; reject symlinks, devices and pipes.

    O_PATH obtains metadata without invoking a device's open operation. Only
    after fstat proves a regular inode is its own descriptor reopened for data
    through /proc/self/fd. This is not a scan of processes or device paths and
    closes the lstat/open race for user-supplied files on Linux.
    """
    meta_fd = None
    data_fd = None
    try:
        first = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(first.st_mode):
            raise AuditError("Input must be a regular file, not a symlink, device or pipe")
        if first.st_size > max_bytes:
            raise AuditError("Log exceeds the size limit")
        meta_fd = os.open(path, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
        metadata = os.fstat(meta_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            raise AuditError("Input changed or is not a bounded regular file")
        data_fd = os.open(f"/proc/self/fd/{meta_fd}", os.O_RDONLY | os.O_CLOEXEC)
        actual = os.fstat(data_fd)
        if (actual.st_dev, actual.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise AuditError("Input inode changed")
        with os.fdopen(data_fd, "rb") as source:
            data_fd = None
            data = source.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise AuditError("Log exceeds the size limit")
        return data.decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        raise AuditError("Cannot read a regular UTF-8 log file") from None
    finally:
        if data_fd is not None:
            os.close(data_fd)
        if meta_fd is not None:
            os.close(meta_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-file", required=True, help="Saved Steam controller log (regular UTF-8 file)")
    parser.add_argument("--guid", help="Select one observed native GUID when the log contains several")
    args = parser.parse_args()
    try:
        result = audit_text(read_regular_log(args.log_file), args.guid)
    except AuditError as error:
        print(json.dumps({"schema_version": 1, "ok": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
