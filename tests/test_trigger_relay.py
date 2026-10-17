#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Metadata fixtures and fake motors only. Never open a real input/USB device."""
from dataclasses import replace
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import stat
import struct
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from trigger_bridge import devices, protocol, relay

SESSION = bytes.fromhex("12" * 16)
INSTANCE = "a" * 64


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Metadata:
    def __init__(self, base):
        self.sys = base / "sys"
        self.dev = base / "dev"
        (self.sys / "class/input").mkdir(parents=True)
        self.nodes = {}

    def add(self, port="3-2.1", address=9, event="event13", instance=INSTANCE):
        usb = self.sys / "devices" / port
        interface = usb / (port + ":1.0")
        input_path = interface / "input/input7"
        input_path.mkdir(parents=True)
        driver = self.sys / "bus/usb/drivers/gs_native"
        driver.mkdir(parents=True, exist_ok=True)
        (interface / "driver").symlink_to(driver)
        for name, value in {"idVendor": "3537", "idProduct": "109c", "busnum": port.split("-")[0], "devnum": str(address)}.items():
            (usb / name).write_text(value + "\n")
        (input_path / "name").write_text("GameSir G7 Pro\n")
        (input_path / "id").mkdir()
        (input_path / "id/vendor").write_text("3537\n")
        (input_path / "id/product").write_text("109c\n")
        entry = self.sys / "class/input" / event
        entry.mkdir()
        (entry / "device").symlink_to(input_path)
        minor = 64 + int(event[5:])
        (entry / "dev").write_text(f"13:{minor}\n")
        self.nodes[str(self.dev / "input" / event)] = SimpleNamespace(
            st_mode=stat.S_IFCHR | 0o660, st_rdev=os.makedev(13, minor), st_ino=1000 + minor, st_dev=5)
        return {"instance": instance, "port": port, "busy": False, "name": "GameSir G7 Pro"}

    def stat(self, path):
        return self.nodes[str(path)]

    def discover(self, entries):
        return devices.discover(entries, self.sys, self.dev, self.stat)

    def verify(self, target, entries):
        return devices.verify(target, entries, self.sys, self.dev, self.stat)


class FakeClient:
    def __init__(self, entries):
        self.entries, self.calls, self.closed = entries, [], False
        self.error = None

    def devices(self):
        self.calls.append(("list",))
        if self.error:
            raise self.error
        return self.entries

    def play(self, instance, amplitudes, duration):
        self.calls.append(("play", instance, amplitudes, duration))

    def stop(self, instance, mask):
        self.calls.append(("stop", instance, mask))

    def close(self):
        self.closed = True


class ProtocolTests(unittest.TestCase):
    def message(self):
        return protocol.Message(protocol.EFFECT, 1, 1234567890, 99, 7, 0x1234, 0xabcd, 500,
                                "/dev/input/event13", SESSION)

    def test_wire_size_and_explicit_little_endian_offsets(self):
        message = self.message()
        payload = message.encode()
        self.assertEqual(len(payload), 128)
        self.assertEqual(payload[:16], b"GST2\2\0\1\0\x80\0\0\0\0\0\0\0")
        self.assertEqual(payload[40:44], b"\x34\x12\xcd\xab")
        self.assertEqual(payload[112:], SESSION)
        self.assertEqual(protocol.decode(payload), message)

    def test_unknown_version_kind_reserved_and_truncation(self):
        payload = self.message().encode()
        variants = [payload[:-1], payload + b"x"]
        for offset, value in ((4, 1), (6, 9), (12, 1), (16, 0), (32, 0), (112, 0)):
            data = bytearray(payload)
            if offset == 112:
                data[112:] = bytes(16)
            else:
                data[offset] = value
            variants.append(bytes(data))
        for data in variants:
            with self.subTest(data=data[:17]), self.assertRaises(protocol.ProtocolError):
                protocol.decode(data)

    def test_canonical_path_and_padding(self):
        for path in ("/dev/input/js0", "/dev/input/event01", "/dev/input/../event1", "event1"):
            with self.subTest(path=path), self.assertRaises(protocol.ProtocolError):
                replace(self.message(), source_path=path).encode()
        data = bytearray(self.message().encode())
        data[111] = 1
        with self.assertRaises(protocol.ProtocolError):
            protocol.decode(data)

    def test_close_is_explicit_zero(self):
        with self.assertRaises(protocol.ProtocolError):
            replace(self.message(), kind=protocol.CLOSE).encode()
        close = replace(self.message(), kind=protocol.CLOSE, left=0, right=0, duration_ms=0)
        self.assertEqual(protocol.decode(close.encode()).zero_mask, 3)


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.metadata = Metadata(Path(self.temp.name))
        self.entries = [self.metadata.add()]
        self.target = self.metadata.discover(self.entries)[0]


class IdentityTests(FixtureCase):
    def test_dynamic_hub_port_and_exact_roundtrip(self):
        self.assertEqual(self.target.port, "3-2.1")
        self.assertEqual(devices.Target.from_dict(self.target.to_dict()), self.target)
        self.metadata.verify(self.target, self.entries)

    def test_second_device_is_not_selected_by_order(self):
        self.entries.append(self.metadata.add("8-5", 22, "event19", "b" * 64))
        candidates = self.metadata.discover(self.entries)
        self.assertEqual(len(candidates), 2)
        self.assertEqual({item.instance for item in candidates}, {INSTANCE, "b" * 64})

    def test_busy_duplicate_and_replaced_broker_identity(self):
        for entries in ([{**self.entries[0], "busy": True}],
                        [{**self.entries[0], "instance": "b" * 64}],
                        self.entries * 2):
            with self.subTest(entries=entries), self.assertRaises(devices.IdentityError):
                self.metadata.verify(self.target, entries)

    def test_replaced_device_address_or_event_node_never_adopted(self):
        usb = Path(self.target.sysfs_usb)
        (usb / "devnum").write_text("10\n")
        with self.assertRaises(devices.IdentityError):
            self.metadata.verify(self.target, self.entries)
        (usb / "devnum").write_text("9\n")
        self.metadata.nodes[str(self.metadata.dev / "input/event13")].st_ino += 1
        with self.assertRaises(devices.IdentityError):
            self.metadata.verify(self.target, self.entries)

    def test_wrong_driver_identity_name_and_node_fail_closed(self):
        interface = Path(self.target.sysfs_interface)
        (interface / "driver").unlink()
        xpad = self.metadata.sys / "bus/usb/drivers/xpad"
        xpad.mkdir()
        (interface / "driver").symlink_to(xpad)
        self.assertEqual(self.metadata.discover(self.entries), [])
        (interface / "driver").unlink()
        (interface / "driver").symlink_to(self.metadata.sys / "bus/usb/drivers/gs_native")
        (Path(self.target.sysfs_usb) / "idProduct").write_text("105e\n")
        self.assertEqual(self.metadata.discover(self.entries), [])

    def test_sysfs_escape_and_invalid_node_number(self):
        entry = self.metadata.sys / "class/input/event13"
        (entry / "device").unlink()
        (entry / "device").symlink_to(Path(self.temp.name))
        self.assertEqual(self.metadata.discover(self.entries), [])

    def test_manifest_requires_exact_private_mode_and_fields(self):
        path = Path(self.temp.name) / "manifest.json"
        document = {"version": 2, "uid": os.geteuid(), "session": SESSION.hex(), "target": self.target.to_dict()}
        path.write_text(json.dumps(document))
        path.chmod(0o600)
        self.assertEqual(devices.read_manifest(path), (self.target, SESSION))
        path.chmod(0o644)
        with self.assertRaises(devices.IdentityError):
            devices.read_manifest(path)
        path.chmod(0o600)
        document["extra"] = True
        path.write_text(json.dumps(document))
        with self.assertRaises(devices.IdentityError):
            devices.read_manifest(path)


class ForwardingCase(FixtureCase):
    def setUp(self):
        super().setUp()
        self.now = 100_000_000_000
        self.sequence = 0
        self.client = FakeClient(self.entries)
        self.forwarder = relay.Forwarder(self.client, self.target, SESSION, 99,
            clock_ns=lambda: self.now, validator=self.metadata.verify, right_gain=3)

    def send(self, left=10000, right=20000, duration=1000, **changes):
        self.sequence += 1
        message = protocol.Message(protocol.EFFECT, self.sequence, self.now, 99, 7, left, right,
                                   duration, self.target.source_path, SESSION)
        self.forwarder.receive(replace(message, **changes).encode())

    def outputs(self):
        return [call for call in self.client.calls if call[0] != "list"]

    def advance(self):
        self.now += relay.INTERVAL_NS
        self.forwarder.flush()


class ForwardingTests(ForwardingCase):
    def test_gain_and_grip_channels_untouched(self):
        self.send(10000, 10000)
        self.forwarder.flush()
        self.assertEqual(self.outputs()[0], ("play", INSTANCE, [15, 46, None, None], 1000))

    def test_full_stop_barrier_survives_immediate_restart(self):
        self.send()
        self.forwarder.flush()
        self.send(0, 0)
        self.send(5000, 6000)
        self.advance()
        self.assertEqual(self.outputs()[-1], ("stop", INSTANCE, 3))
        self.advance()
        self.assertEqual(self.outputs()[-1][0:2], ("play", INSTANCE))

    def test_partial_stop_barrier_survives_positive_restart(self):
        self.send()
        self.forwarder.flush()
        self.send(0, 10000)
        self.send(5000, 10000)
        self.advance()
        self.assertEqual(self.outputs()[-1][2], [0, 46, None, None])
        self.advance()
        self.assertEqual(self.outputs()[-1][2], [8, 46, None, None])

    def test_nonzero_coalesces_without_overwriting_stops(self):
        for left in range(100, 110):
            self.send(left, 10000)
        self.assertEqual(len(self.forwarder.queue), 1)
        self.send(0, 10000)
        for left in range(200, 210):
            self.send(left, 10000)
        self.assertEqual(len(self.forwarder.queue), 2)
        self.forwarder.flush()
        self.assertEqual(self.outputs()[-1][2][0], 0)

    def test_source_time_accounts_for_socket_delay_and_queue_delay(self):
        self.send(duration=1000, monotonic_ns=self.now - 200_000_000)
        self.now += 100_000_000
        self.forwarder.flush()
        self.assertEqual(self.outputs()[-1][-1], 700)

    def test_expired_effect_stops_instead_of_restarting(self):
        self.send(duration=20, monotonic_ns=self.now - 30_000_000)
        self.forwarder.flush()
        self.assertEqual(self.outputs(), [("stop", INSTANCE, 3)])

    def test_blocked_identity_validation_does_not_revive_expired_effect(self):
        def delayed(target, entries):
            self.metadata.verify(target, entries)
            self.now += 900_000_000
        self.forwarder.validator = delayed
        self.send(duration=500)
        self.forwarder.flush()
        self.assertEqual(self.outputs(), [("stop", INSTANCE, 3)])

    def test_blocked_validation_also_rejects_stale_long_effect(self):
        def delayed(target, entries):
            self.metadata.verify(target, entries)
            self.now += relay.MAX_AGE_NS + 1
        self.forwarder.validator = delayed
        self.send(duration=5000)
        self.forwarder.flush()
        self.assertEqual(self.outputs(), [("stop", INSTANCE, 3)])

    def test_duration_zero_is_stop_even_with_positive_amplitudes(self):
        self.send(duration=0)
        self.forwarder.flush()
        self.assertEqual(self.outputs(), [("stop", INSTANCE, 3)])

    def test_pid_session_source_sequence_and_timestamp_rejected(self):
        cases = ({"pid": 98}, {"session": bytes.fromhex("34" * 16)},
                 {"source_path": "/dev/input/event19"}, {"sequence": 2},
                 {"monotonic_ns": self.now + relay.MAX_FUTURE_NS + 1},
                 {"monotonic_ns": self.now - relay.MAX_AGE_NS - 1})
        for changes in cases:
            with self.subTest(changes=changes):
                self.setUp()
                with self.assertRaises(protocol.ProtocolError):
                    self.send(**changes)
                self.assertTrue(self.client.closed)
                self.assertEqual(self.outputs(), [])

    def test_no_new_joystick_or_second_session_after_close(self):
        self.send()
        with self.assertRaises(protocol.ProtocolError):
            self.send(joystick=8)
        self.assertTrue(self.client.closed)

    def test_close_frame_is_terminal_and_stops_only_triggers(self):
        self.send()
        self.forwarder.flush()
        self.send(0, 0, 0, kind=protocol.CLOSE)
        self.advance()
        self.assertEqual(self.outputs()[-1], ("stop", INSTANCE, 3))
        with self.assertRaises(protocol.ProtocolError):
            self.send()

    def test_stop_queue_overflow_fails_closed_without_dropping_barrier(self):
        with self.assertRaises(protocol.ProtocolError):
            for index in range(2 * relay.MAX_QUEUE + 4):
                self.send(0 if index % 2 else 10000, 0 if index % 2 else 10000)
        self.assertTrue(self.client.closed)
        self.assertTrue(self.forwarder.failed)

    def test_source_rate_limit_and_broker_budget(self):
        for _ in range(500):
            self.send()
            self.forwarder.flush()
            self.now += 2_000_000
        self.assertLessEqual(len(self.outputs()), 20)
        self.assertLessEqual(len(self.client.calls), 40)
        self.setUp()
        with self.assertRaises(protocol.ProtocolError):
            for _ in range(relay.MAX_SOURCE_RATE + 1):
                self.send()
        self.assertTrue(self.client.closed)

    def test_instance_replacement_drops_queued_effect_and_no_cancel_new_device(self):
        self.send()
        self.client.entries = [{**self.entries[0], "instance": "b" * 64}]
        with self.assertRaises(devices.IdentityError):
            self.forwarder.flush()
        self.assertTrue(self.client.closed)
        self.assertEqual(self.outputs(), [])

    def test_broker_failure_and_client_close_drop_pending(self):
        self.send()
        self.client.error = RuntimeError("lease ended")
        with self.assertRaises(RuntimeError):
            self.forwarder.flush()
        self.assertTrue(self.client.closed)
        self.assertEqual(self.outputs(), [])
        self.forwarder.close()

    def test_finite_game_duration_not_clipped_to_one_second(self):
        self.send(duration=0xffffffff)
        self.forwarder.flush()
        self.assertEqual(self.outputs()[-1][-1], 0xffffffff)


class ExistingBrokerTests(ForwardingCase):
    def test_repository_broker_keeps_grips_independent(self):
        api = load("trigger_test_broker", "tools/service/haptics_broker.py")
        class Backend:
            def __init__(self, entries):
                self.current = {item["instance"]: {key: value for key, value in item.items() if key != "instance"}
                                for item in entries}
                self.commands = []
            def devices(self):
                return self.current
            def apply(self, identity, commands):
                self.commands.extend(commands)
        backend = Backend(self.entries)
        broker = api.Broker(backend, clock=lambda: self.now / 1e9)
        peer = broker.connect(os.getuid())
        class Adapter(FakeClient):
            def devices(self):
                return broker.request(peer, {"version": 1, "op": "list"})["devices"]
            def play(self, instance, amplitudes, duration):
                broker.request(peer, {"version": 1, "op": "play", "instance": instance,
                                     "amplitudes": amplitudes, "duration_ms": duration})
                broker.tick()
            def stop(self, instance, mask):
                broker.request(peer, {"version": 1, "op": "stop", "instance": instance, "mask": mask})
                broker.tick()
            def close(self):
                broker.disconnect(peer)
                broker.tick()
                self.closed = True
        self.client = Adapter(self.entries)
        self.forwarder = relay.Forwarder(self.client, self.target, SESSION, 99,
            clock_ns=lambda: self.now, validator=self.metadata.verify)
        self.send(duration=5000)
        self.forwarder.flush()
        self.assertEqual({command[0] for command in backend.commands}, {0, 1})
        self.assertTrue(all(command[2] <= 1000 for command in backend.commands))
        self.forwarder.close()
        self.assertEqual(backend.commands[-2:], [(0, 0, 0, True), (1, 0, 0, True)])

    def test_client_factory_uses_repository_client_over_local_unix_socket(self):
        api = load("trigger_socket_broker", "tools/service/haptics_broker.py")
        current = {INSTANCE: {"name": "GameSir G7 Pro", "port": "3-2.1", "busy": False}}
        backend = SimpleNamespace(devices=lambda: current, apply=lambda *_args: None)
        broker = api.Broker(backend)
        path = Path(self.temp.name) / "broker.sock"
        errors = []
        # Exercise the actual repository Client against a minimal protocol
        # listener to avoid any package/group/filesystem setup code.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(str(path))
            listener.listen(1)
            def respond():
                try:
                    connection, _ = listener.accept()
                    with connection, connection.makefile("rb") as source:
                        while line := source.readline():
                            request = json.loads(line)
                            result = broker.request(peer, request)
                            connection.sendall(json.dumps({"version": 1, "ok": True, **result}).encode() + b"\n")
                except Exception as error:
                    errors.append(error)
            peer = broker.connect(os.getuid())
            worker = threading.Thread(target=respond)
            worker.start()
            client = relay._client_factory(path)
            self.assertEqual(client.devices()[0]["instance"], INSTANCE)
            client.play(INSTANCE, [10, 20, None, None], 5000)
            client.stop(INSTANCE, mask=3)
            client.close()
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])


class TransportTests(FixtureCase):
    def test_eof_cannot_flush_a_queued_positive_command(self):
        directory = Path(self.temp.name) / "eof-session"
        directory.mkdir(mode=0o700)
        manifest = directory / "manifest.json"
        manifest.write_text(json.dumps({"version": 2, "uid": os.geteuid(),
                                      "session": SESSION.hex(), "target": self.target.to_dict()}))
        manifest.chmod(0o600)
        client = FakeClient(self.entries)
        payload = protocol.Message(protocol.EFFECT, 1, time.monotonic_ns(), os.getpid(), 7,
                                   10000, 20000, 1000, self.target.source_path, SESSION).encode()
        disconnected, flushes = [], []
        class Peer:
            def getsockopt(self, *_args):
                return struct.pack("3i", os.getpid(), os.geteuid(), os.getegid())
            def setblocking(self, _value):
                pass
            def recv(self, _size):
                if not hasattr(self, "sent"):
                    self.sent = True
                    return payload
                disconnected.append(True)
                return b""
            def close(self):
                pass
        peer = Peer()
        class Server:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def bind(self, path):
                Path(path).touch(mode=0o600)
            def listen(self, _count):
                pass
            def setblocking(self, _value):
                pass
            def accept(self):
                return peer, None
        server = Server()
        class Selector:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                pass
            def register(self, *_args):
                pass
            def select(self, _timeout):
                if not hasattr(self, "accepted"):
                    self.accepted = True
                    return [(SimpleNamespace(fileobj=server), 1)]
                return [(SimpleNamespace(fileobj=peer), 1)]
        def deferred_flush(forwarder):
            self.assertFalse(disconnected, "EOF must discard pending commands before any flush")
            flushes.append(forwarder.calls)
            return False
        with patch.object(relay.socket, "socket", return_value=server), \
                patch.object(relay.selectors, "DefaultSelector", return_value=Selector()), \
                patch.object(relay.Forwarder, "flush", deferred_flush), \
                patch.object(relay.signal, "signal", return_value=relay.signal.SIG_DFL):
            relay.serve(directory / "control.sock", manifest, directory / "ready", io.StringIO(),
                        client_factory=lambda _path: client, validator=self.metadata.verify,
                        allow_root=True)
        self.assertTrue(disconnected)
        self.assertEqual(flushes, [0, 1])
        self.assertTrue(client.closed)
        self.assertFalse(any(call[0] == "play" for call in client.calls))

    def prepare(self):
        directory = Path(self.temp.name) / "session"
        directory.mkdir(mode=0o700)
        manifest = directory / "manifest.json"
        manifest.write_text(json.dumps({"version": 2, "uid": os.geteuid(),
                                      "session": SESSION.hex(), "target": self.target.to_dict()}))
        manifest.chmod(0o600)
        path, ready = directory / "control.sock", directory / "ready"
        client, errors = FakeClient(self.entries), []
        def run():
            try:
                relay.serve(path, manifest, ready, io.StringIO(),
                            client_factory=lambda _path: client, validator=self.metadata.verify,
                            allow_root=True)
            except Exception as error:
                errors.append(error)
        # signal installation is suppressed only inside this synthetic threaded
        # invocation. Production serve still owns its normal process signals.
        context = patch.object(relay.signal, "signal", return_value=relay.signal.SIG_DFL)
        context.start()
        self.addCleanup(context.stop)
        worker = threading.Thread(target=run)
        worker.start()
        deadline = time.monotonic() + 2
        while not ready.exists() and worker.is_alive() and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertTrue(ready.exists(), errors)
        return directory, path, ready, client, errors, worker

    def test_real_stream_fragmentation_and_terminal_close(self):
        directory, path, ready, client, errors, worker = self.prepare()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
            producer.connect(str(path))
            message = protocol.Message(protocol.EFFECT, 1, time.monotonic_ns(), os.getpid(), 1,
                                       10000, 20000, 1000, self.target.source_path, SESSION)
            payload = message.encode()
            producer.sendall(payload[:13])
            time.sleep(0.01)
            producer.sendall(payload[13:])
            deadline = time.monotonic() + 1
            while not any(call[0] == "play" for call in client.calls) and time.monotonic() < deadline:
                time.sleep(0.005)
            producer.sendall(replace(message, kind=protocol.CLOSE, sequence=2,
                                     monotonic_ns=time.monotonic_ns(), left=0, right=0,
                                     duration_ms=0).encode())
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(client.closed)
        self.assertEqual([call for call in client.calls if call[0] == "stop"], [("stop", INSTANCE, 3)])
        self.assertFalse(path.exists())
        self.assertFalse(ready.exists())

    def test_truncated_stream_ends_broker_connection(self):
        _directory, path, _ready, client, errors, worker = self.prepare()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
            producer.connect(str(path))
            producer.sendall(b"GST2")
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], protocol.ProtocolError)
        self.assertTrue(client.closed)
        self.assertFalse(any(call[0] == "play" for call in client.calls))


if __name__ == "__main__":
    unittest.main()
