#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Explicit optional trigger relay, no USB/input-device access or escalation.

Reuses the isolated bridge's bounded forwarding and LT/RT-only broker access.
Transport v2 adds immutable target/session binding and source-time expiry.
"""
import argparse
from collections import deque
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import struct
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from trigger_bridge.devices import read_manifest, verify
    from trigger_bridge.protocol import CLOSE, SIZE, ProtocolError, decode
else:
    from .devices import read_manifest, verify
    from .protocol import CLOSE, SIZE, ProtocolError, decode

# Each update consumes list + play/stop; 20/s leaves room for 2/s heartbeat.
INTERVAL_NS = 50_000_000
MAX_QUEUE = 16
MAX_SOURCE_RATE = 512
MAX_BUFFER = SIZE * 32
MAX_AGE_NS = 500_000_000
MAX_FUTURE_NS = 1_000_000


def percent(value, gain=1.0):
    if type(value) is not int or not 0 <= value <= 65535:
        raise ValueError("Amplitude must be an unsigned 16-bit integer")
    if type(gain) not in (int, float) or not math.isfinite(gain) or not 0.25 <= gain <= 4:
        raise ValueError("Gain must be finite and between 0.25 and 4")
    return min(100, int(value * 100 * gain / 65535 + 0.5))


@dataclass(frozen=True)
class Queued:
    message: object
    barrier: bool


class Forwarder:
    """One game producer and target for the lifetime of one relay connection.

    A newly zeroed channel is a barrier; later nonzero states cannot replace it.
    Repeated ordinary states may coalesce *between* barriers. Overload, stale
    identity, malformed input and broken broker transport close the client,
    allowing the broker's existing finite lease to perform bounded cleanup.
    """
    def __init__(self, client, target, session, peer_pid, *, clock_ns=time.monotonic_ns,
                 validator=verify, right_gain=1.0, report=lambda **_kw: None):
        if type(session) is not bytes or len(session) != 16 or session == bytes(16):
            raise ValueError("Expected a nonzero 16-byte launch session")
        percent(0, right_gain)
        self.client, self.target, self.session, self.peer_pid = client, target, session, peer_pid
        self.clock_ns, self.validator, self.right_gain, self.report = clock_ns, validator, right_gain, report
        self.queue = deque()
        self.arrivals = deque()
        self.next_send = 0
        self.sequence, self.last_stamp = 0, 0
        self.joystick = None
        self.last_zero_mask = 0
        self.closed = self.failed = self.close_received = False
        self.calls = self.sent = 0

    def _fail(self):
        self.failed = True
        self.queue.clear()
        self.client.close()

    def receive(self, payload):
        try:
            if self.closed or self.failed or self.close_received:
                raise ProtocolError("Producer session has ended")
            message = decode(payload)
            now = self.clock_ns()
            if (message.pid != self.peer_pid or message.session != self.session or
                    message.source_path != self.target.source_path or
                    message.sequence != self.sequence + 1 or message.monotonic_ns < self.last_stamp or
                    message.monotonic_ns > now + MAX_FUTURE_NS):
                raise ProtocolError("Producer, session, target, sequence or timestamp mismatch")
            if self.joystick is not None and message.joystick != self.joystick:
                raise ProtocolError("A different joystick requires a fresh explicit launch")
            # A long-paused producer cannot replay old commands after suspend.
            if now - message.monotonic_ns > MAX_AGE_NS:
                raise ProtocolError("Source command exceeded maximum transport age")
            while self.arrivals and self.arrivals[0] <= now - 1_000_000_000:
                self.arrivals.popleft()
            if len(self.arrivals) >= MAX_SOURCE_RATE:
                raise ProtocolError("Source request rate exceeded bounded transport")
            self.arrivals.append(now)
            self.sequence, self.last_stamp, self.joystick = message.sequence, message.monotonic_ns, message.joystick
            self.close_received = message.kind == CLOSE
            barrier = bool(message.zero_mask & ~self.last_zero_mask) or self.close_received
            self.last_zero_mask = message.zero_mask
            # A stop supersedes a pending unsent positive state; it never
            # supersedes an earlier stop barrier or gets replaced by a restart.
            if self.queue and not self.queue[-1].barrier:
                self.queue.pop()
            self.queue.append(Queued(message, barrier))
            if len(self.queue) > MAX_QUEUE:
                raise ProtocolError("Stop queue overflow; refusing to drop a stop barrier")
            self.calls += 1
        except Exception:
            self._fail()
            raise

    def flush(self):
        if self.closed or self.failed or not self.queue:
            return False
        now = self.clock_ns()
        if now < self.next_send:
            return False
        try:
            # Broker identity and metadata are both revalidated. A new dongle at
            # the same port/event number must never receive an old cancellation.
            self.validator(self.target, self.client.devices())
            # Broker IPC/metadata checks may block. Expiry follows the producer
            # timestamp through that delay too, not the pre-validation clock.
            now = self.clock_ns()
            queued = self.queue.popleft()
            message = queued.message
            expiry = message.monotonic_ns + message.duration_ms * 1_000_000
            remaining = min(message.duration_ms, max(0, (expiry - now) // 1_000_000))
            if now - message.monotonic_ns > MAX_AGE_NS:
                remaining = 0  # Never replay an old state after IPC/scheduling stalls.
            if message.kind == CLOSE or not remaining or not (message.left or message.right):
                self.client.stop(self.target.instance, mask=3)
                self.report(event="stop_accepted", sequence=message.sequence, mask=3)
            else:
                amplitudes = [percent(message.left), percent(message.right, self.right_gain), None, None]
                # Zero components remain explicit in this atomic play request,
                # including partial stops while the other trigger is active.
                self.client.play(self.target.instance, amplitudes, remaining)
                self.report(event="play_accepted", sequence=message.sequence,
                            lt=amplitudes[0], rt=amplitudes[1], duration_ms=remaining)
            self.sent += 1
            self.next_send = now + INTERVAL_NS
            return True
        except Exception:
            self._fail()
            raise

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.queue.clear()
        # Closing the existing broker connection is the cleanup primitive. It
        # cannot accidentally address a replacement instance and adds no burst
        # request beyond the broker rate budget. Only LT/RT were ever owned.
        self.client.close()


def _client_factory(path):
    # Source/package-relative client, never a mutable installed developer copy.
    import importlib.util
    base = Path(__file__).resolve().parent.parent
    candidates = (base / "haptics/gamesir_haptics.py", base / "gamesir_haptics.py")
    source = next((candidate for candidate in candidates if candidate.is_file()), None)
    if source is None:
        raise RuntimeError("Packaged/repository haptics client is missing")
    spec = importlib.util.spec_from_file_location("trigger_haptics_client", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Client(**({"path": path} if path is not None else {}))


def serve(path, manifest, ready, log, *, broker_path=None, right_gain=1.0,
          client_factory=_client_factory, validator=verify, allow_root=False):
    """Single producer stream. All injection options exist for offline tests.

    allow_root only bypasses the UID guard in in-process synthetic unit tests;
    it is deliberately not exposed by the command line.
    """
    if os.geteuid() == 0 and not allow_root:
        raise RuntimeError("Relay must run as the ordinary desktop user")
    path, ready = Path(path), Path(ready)
    directory = path.parent.lstat()
    if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.geteuid() or
            stat.S_IMODE(directory.st_mode) != 0o700 or path.parent.resolve() != path.parent):
        raise RuntimeError("Relay directory must be a private real user directory, mode 0700")
    target, session = read_manifest(manifest)
    client = client_factory(broker_path)
    forwarder, connection = None, None
    old_signals = {}
    stopped = False
    count = 0

    def report(**data):
        nonlocal count
        if count < 1000:
            log.write(json.dumps({"monotonic_ns": time.monotonic_ns(), **data}) + "\n")
            log.flush()
            count += 1

    def stop(*_args):
        nonlocal stopped
        stopped = True

    bound = False
    ready_created = False
    try:
        validator(target, client.devices())
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            old_signals[signum] = signal.signal(signum, stop)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server, selectors.DefaultSelector() as selector:
            server.bind(str(path))
            bound = True
            os.chmod(path, 0o600)
            server.listen(1)
            server.setblocking(False)
            selector.register(server, selectors.EVENT_READ)
            with ready.open("x", encoding="ascii") as output:
                output.write("ready\n")
            ready_created = True
            data = bytearray()
            next_health = time.monotonic_ns() + 1_000_000_000
            while not stopped:
                # Existing client exposes asynchronous failure through its
                # normal public heartbeat request; list before each output also
                # surfaces it. No access to Client._stop/_error internals.
                for key, _events in selector.select(0.01):
                    if key.fileobj is server:
                        peer, _address = server.accept()
                        pid, uid, _gid = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                        if uid != os.geteuid() or connection is not None:
                            peer.close()
                            continue
                        connection = peer
                        peer.setblocking(False)
                        selector.register(peer, selectors.EVENT_READ)
                        forwarder = Forwarder(client, target, session, pid, validator=validator,
                                              right_gain=right_gain, report=report)
                    else:
                        chunk = connection.recv(MAX_BUFFER)
                        if not chunk:
                            if data:
                                raise ProtocolError("Truncated producer frame")
                            stopped = True
                            break
                        data.extend(chunk)
                        if len(data) > MAX_BUFFER:
                            raise ProtocolError("Producer buffer exceeded limit")
                        while len(data) >= SIZE:
                            payload = bytes(data[:SIZE])
                            del data[:SIZE]
                            forwarder.receive(payload)
                if not stopped and forwarder is not None:
                    forwarder.flush()
                    if forwarder.close_received and not forwarder.queue:
                        stopped = True
                now = time.monotonic_ns()
                if not stopped and now >= next_health:
                    validator(target, client.devices())
                    next_health = now + 1_000_000_000
    finally:
        if connection is not None:
            connection.close()
        if forwarder is not None:
            forwarder.close()
        else:
            client.close()
        if bound:
            path.unlink(missing_ok=True)
        if ready_created:
            ready.unlink(missing_ok=True)
        for signum, handler in old_signals.items():
            signal.signal(signum, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--ready", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--right-gain", default=1.0, type=float)
    args = parser.parse_args()
    percent(0, args.right_gain)
    with args.log.open("x", encoding="utf-8") as log:
        serve(args.socket, args.manifest, args.ready, log, right_gain=args.right_gain)


if __name__ == "__main__":
    main()
