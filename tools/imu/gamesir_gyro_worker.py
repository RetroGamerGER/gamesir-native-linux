#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One approved 108-second host-IIO transaction. Never launches a GUI.

The unprivileged frontend supplies GO/PING/STOP on a pipe. No device is opened
before GO. EOF, lost heartbeat, signal or sensor error enters restoration;
there is no reconnect, repetition, USB command or private control-node access.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import pwd
import select
import signal
import stat
import sys
import time

from gamesir_iio_buffer import BufferTransaction, snapshot_iio
from gamesir_imu_stream import CHANNELS, MAX_FILE_BYTES, SCAN_SIZE, ScanDecoder, live_chunks

ROOT = Path(__file__).resolve().parents[2]
SOURCES = tuple("tools/imu/" + name for name in (
    "gamesir_gyro_guided.py", "gamesir_gyro_worker.py", "gamesir_iio_buffer.py",
    "gamesir_imu_stream.py", "gamesir_imu_diagnostic.py", "gyro_reference.py"))
CAPTURE_SECONDS = 108
MAX_GAP_NS = 250_000_000


def read_manifest(path):
    """Stored regular JSON only; the manifest never supplies executable paths."""
    path = Path(path).resolve(strict=True)
    if any(p in path.parents for p in map(Path, ("/sys", "/proc", "/dev"))):
        raise ValueError("stored manifest required")
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1_048_576:
            raise ValueError("bounded regular manifest required")
        data = handle.read(1_048_577)
    if len(data) > 1_048_576:
        raise ValueError("oversized manifest")
    value = json.loads(data)
    if (value.get("schema_version") != 1 or value.get("kind") != "gamesir_yaw90left_manifest" or
            set(value.get("source_sha256", {})) != set(SOURCES)):
        raise ValueError("exact yaw90left manifest v1 and six fixed source hashes required")
    for relative in SOURCES:
        with (ROOT / relative).open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if value["source_sha256"][relative] != actual:
            raise ValueError(f"approved helper changed: {relative}; prepare a new manifest")
    if not isinstance(value.get("snapshot"), dict):
        raise ValueError("IIO metadata snapshot required")
    return value


def check_other_readers(snapshot, owned_fd=None):
    """Inspect process FD metadata only, never open another device.

    This is a fresh conflict check, not a claim about kernel exclusivity or
    protection against an unrelated client starting after the check.
    """
    expected = os.makedev(snapshot["major"], snapshot["minor"])
    conflicts = []
    for directory in Path("/proc").glob("[0-9]*/fd"):
        try:
            entries = list(directory.iterdir())
        except FileNotFoundError:
            continue
        for entry in entries:
            if directory.parent.name == str(os.getpid()) and entry.name == str(owned_fd):
                continue
            try:
                info = entry.stat()
            except (FileNotFoundError, ProcessLookupError):
                continue
            if stat.S_ISCHR(info.st_mode) and info.st_rdev == expected:
                conflicts.append(str(entry))
    if conflicts:
        raise ValueError("another IIO reader exists; no configuration: " + ", ".join(conflicts))


class ParentChannel:
    """Small bounded line protocol; never waits on a partial input line."""
    def __init__(self, fd=0, output=None):
        self.fd, self.output = fd, output or sys.stdout
        self.pending = bytearray()
        self.last_ping = time.monotonic()
        self.go = False

    def emit(self, event, **data):
        self.output.write(json.dumps({"event": event, **data}, allow_nan=False) + "\n")
        self.output.flush()

    def poll(self, *, awaiting_go=False, timeout=0):
        if select.select([self.fd], [], [], timeout)[0]:
            data = os.read(self.fd, 512)
            if not data:
                raise ValueError("frontend pipe closed; cancel and restore")
            self.pending.extend(data)
            while b"\n" in self.pending:
                line, _, tail = self.pending.partition(b"\n")
                self.pending[:] = tail
                if line == b"PING":
                    self.last_ping = time.monotonic()
                elif line == b"GO" and awaiting_go and not self.go:
                    self.go = True
                elif line == b"STOP":
                    raise ValueError("frontend STOP; cancel and restore")
                else:
                    raise ValueError("unexpected frontend command; cancel and restore")
            if len(self.pending) > 128:
                raise ValueError("oversized frontend command")
        if time.monotonic() - self.last_ping > 3:
            raise ValueError("frontend heartbeat lost; cancel and restore")

    def wait_go(self):
        deadline = time.monotonic() + 900
        while not self.go:
            self.poll(awaiting_go=True, timeout=.25)
            if time.monotonic() >= deadline:
                raise ValueError("local Go wait exceeded 15 minutes; no device access")


class Evidence:
    """Root-private, dir-FD anchored files; hand ownership back only at end."""
    def __init__(self, output, uid, gid, home):
        output = Path(output)
        home = Path(home).resolve(strict=True)
        if not output.is_absolute() or output.name != "capture" or output.parent.resolve(strict=True) != output.parent:
            raise ValueError("canonical absolute NEWDIR/capture output required")
        if home not in output.parents:
            raise ValueError("capture must be inside the invoking user's home")
        parent = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            info = os.fstat(parent)
            if info.st_uid != uid or stat.S_IMODE(info.st_mode) & 0o077:
                raise ValueError("frontend output parent must be user-owned and private 0700")
            os.mkdir("capture", mode=0o700, dir_fd=parent)
            self.fd = os.open("capture", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent)
        finally:
            os.close(parent)
        self.uid, self.gid, self.files = uid, gid, {}
        self.report = None

    def open(self, name, *, binary=False):
        if Path(name).name != name or name in self.files:
            raise ValueError("new fixed evidence filename required")
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        handle = os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"}))
        self.files[name] = handle
        return handle

    def json(self, name, value):
        if name == "report.json":
            self.report = value
        output = self.open(name)
        json.dump(value, output, indent=2, allow_nan=False)
        output.write("\n")

    def finish(self):
        """Hash durable originals; no symlink-following chmod/chown paths."""
        errors = []
        for name, handle in list(self.files.items()):
            try:
                handle.flush(); os.fsync(handle.fileno())
            except OSError as error:
                errors.append(f"flush/fsync {name}: {error}")
            finally:
                try:
                    handle.close()
                except OSError as error:
                    errors.append(f"close {name}: {error}")
        def amend_and_hash():
            if errors and self.report is not None:
                self.report["completed"] = False
                self.report["failure"] = self.report["failure"] or errors[0]
                self.report["evidence_finalization_errors"] = list(errors)
                fd = os.open("report.json", os.O_WRONLY | os.O_TRUNC | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(self.report, handle, indent=2, allow_nan=False)
                    handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
            fd = os.open("SHA256SUMS", os.O_WRONLY | os.O_TRUNC | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
            with os.fdopen(fd, "w", encoding="ascii") as sums:
                for name in sorted(self.files):
                    if name == "SHA256SUMS":
                        continue
                    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
                    with os.fdopen(fd, "rb") as source:
                        digest = hashlib.file_digest(source, "sha256").hexdigest()
                    sums.write(f"{digest}  {name}\n")
                sums.flush(); os.fsync(sums.fileno())
        try:
            self.open("SHA256SUMS").close()
            # The directory remains root-only while files are handed back.
            for name in self.files:
                fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=self.fd)
                try:
                    os.fchown(fd, self.uid, self.gid)
                finally:
                    os.close(fd)
            amend_and_hash()
            os.fsync(self.fd)
            try:
                os.fchown(self.fd, self.uid, self.gid)
            except OSError as error:
                errors.append(f"directory ownership handback: {error}")
                amend_and_hash()
        except OSError as error:
            errors.append(f"hash/ownership handback: {error}")
            try:
                amend_and_hash()
            except OSError as secondary:
                errors.append(f"finalization error could not be persisted: {secondary}")
        finally:
            try:
                os.close(self.fd)
            except OSError as error:
                errors.append(f"evidence directory close: {error}")
        return errors


def execute(manifest, evidence, channel, *, transaction_factory=BufferTransaction, reader=live_chunks,
            revalidate=lambda: None):
    """Dependencies are Python objects for offline tests, never CLI switches."""
    failure, notes, cleanup_errors = None, [], []
    transaction = chunks = None
    restored, count, byte_count, started_ns = True, 0, 0, None
    report = {"schema_version": 1, "session": "yaw90left", "capture_seconds": CAPTURE_SECONDS,
              "max_gap_ns": MAX_GAP_NS, "no_data_seconds": 2,
              "calibration_verified": False, "automatic_next_repetition": False,
              "radio_or_sensor_loss_known": False, "timebase": "host_monotonic_receive"}
    try:
        channel.emit("ready", capture_seconds=CAPTURE_SECONDS, device_opened=False, buffer_modified=False)
        channel.wait_go()
        revalidate()  # Source hashes and exact instance again AFTER the 30s preparation.
        channel.poll()
        transaction = transaction_factory(manifest["snapshot"])
        metadata, descriptor = transaction.setup()
        decoder = ScanDecoder(metadata["instance_id"], MAX_GAP_NS)
        binary = evidence.open("scans.bin", binary=True)
        observations = evidence.open("observations.jsonl")
        evidence.json("layout.json", {"channels": CHANNELS, "scan_bytes": SCAN_SIZE,
                      "counter_offset": 16, "host_timestamp_offset": 24, "metadata": metadata,
                      "timestamp_is_device_time": False})
        started_ns = time.monotonic_ns()
        channel.emit("capture_started", monotonic_ns=started_ns,
                     utc=dt.datetime.now(dt.timezone.utc).isoformat())
        chunks = reader(metadata, manifest["snapshot"]["device_node"], CAPTURE_SECONDS, 2,
                        descriptor=descriptor, check_alive=channel.poll)
        for data, received in chunks:
            byte_count += len(data)
            if byte_count > MAX_FILE_BYTES:
                raise ValueError("capture exceeded bounded file size")
            binary.write(data)
            for row in decoder.feed(data, received):
                observations.write(json.dumps(row, allow_nan=False) + "\n")
                count += 1
        decoder.finish()
    except (Exception, KeyboardInterrupt) as error:
        failure = f"{type(error).__name__}: {error}"
        notes = list(getattr(error, "__notes__", ()))
    finally:
        if chunks is not None:
            try:
                chunks.close()
            except Exception as error:
                cleanup_errors.append(f"reader close: {type(error).__name__}: {error}")
        # Do not let a second Ctrl-C interrupt the short restoration sequence.
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        if transaction is not None:
            try:
                result = transaction.restore()
                restored = result["restored"]
            except BaseException as error:
                restored = False
                result = {"restored": False, "errors": [f"unexpected restoration failure: {error}"],
                          "writes": [], "before": manifest["snapshot"], "after": None}
        else:
            result = {"restored": True, "errors": [], "writes": [], "before": manifest["snapshot"],
                      "after": None, "device_opened": False, "configuration_attempted": False}
        try:
            evidence.json("buffer-transaction.json", result)
        except Exception as error:
            cleanup_errors.append(f"transaction report: {type(error).__name__}: {error}")
        if not restored and failure is None:
            failure = "original IIO buffer state restoration not verified"
        if cleanup_errors and failure is None:
            failure = cleanup_errors[0]
        report.update({"completed": failure is None, "failure": failure, "error_notes": notes,
                       "restored": restored, "cleanup_errors": cleanup_errors,
                       "observations": count, "original_bytes": byte_count,
                       "capture_started_monotonic_ns": started_ns,
                       "buffer_configuration_modified": bool(result["writes"])})
        try:
            evidence.json("report.json", report)
        except Exception as error:
            cleanup_errors.append(f"final report: {type(error).__name__}: {error}")
        try:
            cleanup_errors.extend(evidence.finish())
        except BaseException as error:
            cleanup_errors.append(f"evidence finalization: {type(error).__name__}: {error}")
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    if cleanup_errors and failure is None:
        failure = cleanup_errors[0]
    # A broken pipe cannot undo the already completed restoration/evidence.
    channel.emit("finished", passed=failure is None and restored, restored=restored,
                 failure=failure, observations=count, cleanup_errors=cleanup_errors)
    return 0 if failure is None and restored else 1


def interrupted(number, _frame):
    raise KeyboardInterrupt(f"worker signal {number}; restore original IIO state")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if os.geteuid() != 0 or int(os.environ.get("SUDO_UID", "0")) <= 0:
            raise ValueError("run only through the approved unprivileged frontend with sudo askpass")
        uid, gid = int(os.environ["SUDO_UID"]), int(os.environ["SUDO_GID"])
        account = pwd.getpwuid(uid)
        if gid != account.pw_gid:
            raise ValueError("invoking primary group mismatch")
        manifest = read_manifest(args.manifest)

        def revalidate():
            if read_manifest(args.manifest) != manifest:
                raise ValueError("approved manifest changed")
            snap = manifest["snapshot"]
            if snapshot_iio(snap["directory"], snap["device_node"]) != snap:
                raise ValueError("IIO/USB instance or inactive settings changed; no automatic rediscovery")

        revalidate()
        check_other_readers(manifest["snapshot"])
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, interrupted)
        evidence = Evidence(args.output, uid, gid, account.pw_dir)
        return execute(manifest, evidence, ParentChannel(), revalidate=revalidate,
                       transaction_factory=lambda snap: BufferTransaction(snap,
                           after_reserve=lambda fd: check_other_readers(snap, fd)))
    except (Exception, KeyboardInterrupt) as error:
        print(f"STOP: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
