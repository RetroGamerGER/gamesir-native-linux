# SPDX-License-Identifier: GPL-2.0-only
"""Local API v1 policy and socket transport; only the injected backend uses ioctls."""
from dataclasses import dataclass, field
import grp
import json
import math
import os
from pathlib import Path
import selectors
import socket
import stat
import struct
import time

VERSION = 1
CLIENT_LEASE = 2.0
HARDWARE_LEASE_MS = 1000
REFRESH_SECONDS = 0.4
MAX_DURATION_MS = 0xffffffff
MAX_REQUEST = 4096
MAX_CLIENTS = 16
GROUP = "gamesir-native-haptics"
SOCKET = Path("/run/gamesir-native-haptics/control.sock")


class Rejected(ValueError):
    pass


class Busy(RuntimeError):
    """The manager is using the exclusive root control FD; retry before expiry."""


@dataclass
class Peer:
    uid: int
    alive_until: float
    requests: list = field(default_factory=list)
    error: str = ""


@dataclass
class Effect:
    peer: int
    amplitude: list = field(default_factory=lambda: [0] * 4)
    until: list = field(default_factory=lambda: [0.0] * 4)
    hardware_mask: int = 0
    next_refresh: float = 0
    last_attempt: float = -100
    stopping: bool = False
    failed_at: float | None = None


class Broker:
    def __init__(self, backend, clock=time.monotonic):
        self.backend, self.clock = backend, clock
        self.peers = {}
        self.effects = {}
        self.next_peer = 1

    def connect(self, uid):
        if len(self.peers) >= MAX_CLIENTS:
            raise Rejected("Too many local haptic clients")
        token = self.next_peer
        self.next_peer += 1
        self.peers[token] = Peer(uid, self.clock() + CLIENT_LEASE)
        return token

    def disconnect(self, peer):
        self.peers.pop(peer, None)
        for effect in self.effects.values():
            if effect.peer == peer:
                effect.amplitude = [0] * 4
                effect.stopping = True
                effect.next_refresh = 0

    @staticmethod
    def integer(value, low, high, name):
        if type(value) is not int or not low <= value <= high:
            raise Rejected(f"{name} must be an integer in {low}..{high}")
        return value

    def request(self, peer_id, request):
        peer = self.peers.get(peer_id)
        if not peer:
            raise Rejected("Client lease expired; reconnect explicitly")
        now = self.clock()
        if now >= peer.alive_until:
            self.disconnect(peer_id)
            raise Rejected("Client lease expired; reconnect explicitly")
        peer.requests = [instant for instant in peer.requests if instant > now - 1]
        if len(peer.requests) >= 50:
            self.disconnect(peer_id)
            raise Rejected("Request rate exceeds 50 per second")
        peer.requests.append(now)
        if type(request) is not dict or request.get("version") != VERSION or type(request.get("version")) is not int:
            raise Rejected("Expected version 1 JSON object")
        operation = request.get("op")
        allowed = {"list": {"version", "op"}, "heartbeat": {"version", "op"},
                   "play": {"version", "op", "instance", "amplitudes", "duration_ms"},
                   "stop": {"version", "op", "instance", "mask"},
                   "release": {"version", "op", "instance"}}
        if type(operation) is not str or operation not in allowed or set(request) != allowed[operation]:
            raise Rejected("Unknown operation or unexpected/missing fields")
        devices = self.backend.devices()
        if operation == "list":
            return {"devices": [{"instance": key, **value} for key, value in sorted(devices.items())],
                    "channels": ["left_trigger", "right_trigger", "left_grip", "right_grip"],
                    "max_duration_ms": MAX_DURATION_MS, "client_lease_ms": 2000}
        if operation == "heartbeat":
            peer.alive_until = now + CLIENT_LEASE
            return {"lease_ms": 2000, "last_error": peer.error}
        identity = request.get("instance")
        if type(identity) is not str or len(identity) != 64 or identity not in devices:
            raise Rejected("Unknown or replaced device instance; list and select again")
        effect = self.effects.get(identity)
        if effect and effect.peer != peer_id:
            raise Rejected("Device is owned by another haptic connection")
        if effect and effect.stopping:
            raise Rejected("Previous effect is still stopping")
        if operation == "play":
            amplitudes = request["amplitudes"]
            if type(amplitudes) is not list or len(amplitudes) != 4 or all(a is None for a in amplitudes):
                raise Rejected("Expected four amplitudes; null preserves an untouched channel")
            for amplitude in amplitudes:
                if amplitude is not None:
                    self.integer(amplitude, 0, 100, "amplitude")
            duration = self.integer(request["duration_ms"], 1, MAX_DURATION_MS, "duration_ms")
            if effect is None:
                effect = self.effects[identity] = Effect(peer_id)
            for channel, amplitude in enumerate(amplitudes):
                if amplitude is not None:
                    effect.amplitude[channel] = amplitude
                    effect.until[channel] = now + duration / 1000
            effect.next_refresh = 0
            peer.alive_until = now + CLIENT_LEASE
        elif operation == "stop":
            mask = self.integer(request["mask"], 1, 15, "mask")
            if effect:
                for channel in range(4):
                    if mask & (1 << channel):
                        effect.amplitude[channel] = 0
                effect.next_refresh = 0
        elif effect:
            effect.amplitude = [0] * 4
            effect.stopping = True
            effect.next_refresh = 0
        return {"accepted": True, "usb_or_mechanical_confirmation": False}

    def tick(self):
        now = self.clock()
        for peer_id, peer in list(self.peers.items()):
            if now >= peer.alive_until:
                self.disconnect(peer_id)
        devices = self.backend.devices()
        for identity, effect in list(self.effects.items()):
            if identity not in devices:
                # Never deliver a stale cancellation to a replacement dongle.
                self.effects.pop(identity)
                continue
            if effect.failed_at is not None and now - effect.failed_at > 1.1:
                self.effects.pop(identity)
                continue
            for channel in range(4):
                if now >= effect.until[channel]:
                    effect.amplitude[channel] = 0
            if now < effect.next_refresh and any(effect.amplitude):
                continue
            commands = []
            next_mask = 0
            for channel, amplitude in enumerate(effect.amplitude):
                if amplitude:
                    remaining = max(1, math.ceil((effect.until[channel] - now) * 1000))
                    commands.append((channel, amplitude, min(HARDWARE_LEASE_MS, remaining), False))
                    next_mask |= 1 << channel
                elif effect.hardware_mask & (1 << channel):
                    commands.append((channel, 0, 0, True))
            if commands:
                try:
                    self.backend.apply(identity, commands)
                except Busy:
                    # Existing packets expire in hardware after at most 1 s.
                    # Retry only while the application still owns this instance.
                    effect.next_refresh = now + 0.05
                    if effect.stopping and now - effect.last_attempt > 1.1:
                        self.effects.pop(identity)
                    continue
                except Exception as error:
                    peer = self.peers.get(effect.peer)
                    if peer:
                        peer.error = str(error)
                    # A failed ioctl may still have sent a bounded packet. Keep
                    # ownership through one final lease window, never re-play.
                    effect.amplitude = [0] * 4
                    effect.stopping = True
                    effect.hardware_mask |= sum(1 << command[0] for command in commands)
                    effect.last_attempt = now
                    if effect.failed_at is None:
                        effect.failed_at = now
                    effect.next_refresh = now + REFRESH_SECONDS
                    continue
                effect.last_attempt = now
            effect.hardware_mask = next_mask
            effect.next_refresh = now + REFRESH_SECONDS
            if effect.stopping or not any(effect.amplitude):
                self.effects.pop(identity)


@dataclass
class Connection:
    socket: object
    peer: int
    incoming: bytearray = field(default_factory=bytearray)
    outgoing: bytearray = field(default_factory=bytearray)


class SocketServer:
    """Nonblocking, bounded local transport in the manager's existing loop."""
    def __init__(self, broker, selector, path=SOCKET):
        self.broker, self.selector, self.path = broker, selector, Path(path)
        self.connections = {}
        group = grp.getgrnam(GROUP)
        self.path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        directory = self.path.parent.lstat()
        if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != 0 or directory.st_mode & 0o027:
            raise PermissionError("Unsafe haptic runtime directory")
        os.chown(self.path.parent, 0, group.gr_gid)
        os.chmod(self.path.parent, 0o750)
        self.path.unlink(missing_ok=True)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(self.path))
        os.chown(self.path, 0, group.gr_gid)
        os.chmod(self.path, 0o660)
        self.listener.listen(MAX_CLIENTS)
        self.listener.setblocking(False)
        self.selector.register(self.listener, selectors.EVENT_READ, self)

    def drop(self, connection):
        self.broker.disconnect(connection.peer)
        self.connections.pop(connection.socket.fileno(), None)
        self.selector.unregister(connection.socket)
        connection.socket.close()

    def handle(self, key, _mask):
        if key.fileobj is self.listener:
            try:
                client, _ = self.listener.accept()
                client.setblocking(False)
                _pid, uid, _gid = struct.unpack("3i", client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                peer = self.broker.connect(uid)
            except (OSError, Rejected):
                if "client" in locals():
                    client.close()
                return
            connection = Connection(client, peer)
            self.connections[client.fileno()] = connection
            self.selector.register(client, selectors.EVENT_READ, self)
            return
        connection = self.connections.get(key.fileobj.fileno())
        if not connection:
            return
        try:
            try:
                data = connection.socket.recv(MAX_REQUEST + 1)
            except BlockingIOError:
                data = None
            if data == b"":
                self.drop(connection)
                return
            if data:
                connection.incoming.extend(data)
                if len(connection.incoming) > MAX_REQUEST:
                    raise Rejected("Request exceeds 4096 bytes")
                # At most one bounded read batch per selector dispatch.
                while b"\n" in connection.incoming:
                    line, _, rest = connection.incoming.partition(b"\n")
                    connection.incoming = bytearray(rest)
                    try:
                        answer = self.broker.request(connection.peer, json.loads(line))
                        response = {"version": VERSION, "ok": True, **answer}
                    except (ValueError, RecursionError, Rejected) as error:
                        response = {"version": VERSION, "ok": False, "error": str(error)}
                    connection.outgoing.extend(json.dumps(response).encode() + b"\n")
                    if len(connection.outgoing) > 8192:
                        raise Rejected("Response queue exceeded limit")
            if connection.outgoing:
                try:
                    count = connection.socket.send(connection.outgoing)
                except BlockingIOError:
                    count = 0
                del connection.outgoing[:count]
            self.selector.modify(connection.socket, selectors.EVENT_READ |
                                 (selectors.EVENT_WRITE if connection.outgoing else 0), self)
        except (OSError, ValueError, Rejected):
            self.drop(connection)

    def tick(self):
        self.broker.tick()
        for connection in list(self.connections.values()):
            if connection.peer not in self.broker.peers:
                self.drop(connection)

    def close(self):
        for connection in list(self.connections.values()):
            self.drop(connection)
        self.broker.tick()
        self.selector.unregister(self.listener)
        self.listener.close()
        self.path.unlink(missing_ok=True)
