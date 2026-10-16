#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""API v1, virtual effects, fake ioctls and local socket buffers; no hardware."""
import importlib.util
import io
import json
from pathlib import Path
import selectors
import socket
import stat
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

api = module("haptics_broker", "tools/service/haptics_broker.py")
service = module("haptic_manager", "tools/service/gamesir_native.py")
client = module("gamesir_haptics", "tools/haptics/gamesir_haptics.py")
IDENTITY = "a" * 64


class Backend:
    def __init__(self):
        self.current = {IDENTITY: {"name": "GameSir G7 Pro", "port": "3-2.1", "busy": False}}
        self.calls = []
        self.error = None
        self.now = 0

    def devices(self):
        return self.current

    def apply(self, identity, commands):
        if self.error:
            raise self.error
        self.calls.append((self.now, identity, list(commands)))


class Policy(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.broker = api.Broker(self.backend, lambda: self.backend.now)
        self.peer = self.broker.connect(1000)

    def request(self, op, **fields):
        return self.broker.request(self.peer, {"version": 1, "op": op, **fields})

    def play(self, amplitudes=(10, 20, 30, 40), duration=5000):
        self.request("play", instance=IDENTITY, amplitudes=list(amplitudes), duration_ms=duration)
        self.broker.tick()

    def test_independent_four_channels_and_bounded_hardware_lease(self):
        self.play()
        commands = self.backend.calls[-1][2]
        self.assertEqual(commands, [(0, 10, 1000, False), (1, 20, 1000, False),
                                    (2, 30, 1000, False), (3, 40, 1000, False)])

    def test_application_controls_five_seconds_minute_and_hour(self):
        for duration in (5000, 60000, 3600000):
            with self.subTest(duration=duration):
                self.setUp()
                self.play(duration=duration)
                for step in range(1, duration // 400):
                    self.backend.now = step * 0.4
                    self.request("heartbeat")
                    self.broker.tick()
                self.backend.now = duration / 1000 - 0.001
                self.request("heartbeat")
                self.broker.tick()
                self.assertIn(IDENTITY, self.broker.effects)
                self.backend.now = duration / 1000
                self.broker.tick()
                self.assertNotIn(IDENTITY, self.broker.effects)
                for _, _, commands in self.backend.calls:
                    self.assertTrue(all(cancel or 1 <= duration <= 1000 for _, _, duration, cancel in commands))

    def test_unsigned32_duration_boundary_and_no_boolean_numbers(self):
        self.play(duration=0xffffffff)
        for duration in (0, -1, 0x100000000, True, 1.0):
            with self.subTest(duration=duration), self.assertRaises(api.Rejected):
                self.request("play", instance=IDENTITY, amplitudes=[1, 2, 3, 4], duration_ms=duration)

    def test_stop_mask_does_not_cancel_other_channels(self):
        self.play()
        self.request("stop", instance=IDENTITY, mask=1)
        self.broker.tick()
        commands = self.backend.calls[-1][2]
        self.assertEqual(commands[0], (0, 0, 0, True))
        self.assertEqual([c[1] for c in commands[1:]], [20, 30, 40])

    def test_channel_update_preserves_other_program_durations(self):
        self.play(duration=5000)
        self.backend.now = 1
        self.request("play", instance=IDENTITY, amplitudes=[99, None, None, None], duration_ms=60000)
        effect = self.broker.effects[IDENTITY]
        self.assertEqual(effect.amplitude, [99, 20, 30, 40])
        self.assertEqual(effect.until, [61, 5, 5, 5])

    def test_lease_expiry_without_heartbeat_cancels_all_owned_channels(self):
        self.play(duration=3600000)
        self.backend.now = 2
        self.broker.tick()
        self.assertNotIn(self.peer, self.broker.peers)
        self.assertNotIn(IDENTITY, self.broker.effects)
        self.assertEqual(self.backend.calls[-1][2], [(i, 0, 0, True) for i in range(4)])

    def test_disconnect_cancels_before_other_peer_can_acquire(self):
        self.play()
        self.broker.disconnect(self.peer)
        other = self.broker.connect(1001)
        request = {"version": 1, "op": "play", "instance": IDENTITY,
                   "amplitudes": [1, 2, 3, 4], "duration_ms": 5000}
        with self.assertRaises(api.Rejected):
            self.broker.request(other, request)
        self.broker.tick()
        self.broker.request(other, request)
        self.assertEqual(self.broker.effects[IDENTITY].peer, other)

    def test_device_replacement_is_not_auto_selected_or_cancelled(self):
        self.play()
        self.backend.current = {"b" * 64: {"port": "3-2.1"}}
        self.broker.tick()
        self.assertEqual(len(self.backend.calls), 1)
        with self.assertRaises(api.Rejected):
            self.play()

    def test_manager_exclusive_fd_busy_does_not_open_competing_handle(self):
        self.backend.error = api.Busy("manager info")
        self.play()
        self.assertEqual(self.backend.calls, [])
        self.backend.error = None
        self.backend.now = 0.1
        self.broker.tick()
        self.assertEqual(len(self.backend.calls), 1)

    def test_unavailable_cancel_releases_after_hardware_lease_expired(self):
        self.play()
        self.backend.error = api.Busy("manager END")
        self.broker.disconnect(self.peer)
        self.broker.tick()
        self.backend.now = 1.2
        self.broker.tick()
        self.assertNotIn(IDENTITY, self.broker.effects)

    def test_backend_error_never_replays_and_has_bounded_cleanup(self):
        self.backend.error = OSError("fake failed ioctl")
        self.play()
        self.assertTrue(self.broker.effects[IDENTITY].stopping)
        self.assertEqual(self.request("heartbeat")["last_error"], "fake failed ioctl")
        self.backend.now = 1.2
        self.broker.tick()
        self.assertNotIn(IDENTITY, self.broker.effects)
        self.assertEqual(self.backend.calls, [])

    def test_strict_protocol_rejects_unknown_fields_and_bad_amplitudes(self):
        for request in ({"version": 2, "op": "list"}, {"version": True, "op": "list"},
                        {"version": 1, "op": "raw_usb", "payload": "1234"},
                        {"version": 1, "op": "list", "extra": 1}):
            with self.subTest(request=request), self.assertRaises(api.Rejected):
                self.broker.request(self.peer, request)
        for amplitudes in ([1, 2, 3], [None] * 4, [1, -1, 2, 3], [101, 2, 3, 4], [True, 2, 3, 4]):
            with self.subTest(amplitudes=amplitudes), self.assertRaises(api.Rejected):
                self.request("play", instance=IDENTITY, amplitudes=amplitudes, duration_ms=1000)
        self.assertEqual(self.backend.calls, [])

    def test_rate_and_connection_limits(self):
        for _ in range(50):
            self.request("heartbeat")
        with self.assertRaises(api.Rejected):
            self.request("heartbeat")
        for _ in range(16):
            self.broker.connect(1000)
        with self.assertRaises(api.Rejected):
            self.broker.connect(1000)


class BackendContract(unittest.TestCase):
    def test_exact_private_ioctl_payloads_without_start_or_usb(self):
        host = service.Host("never", "never")
        device = service.Device("4-3", "generation", "parent", "109c", 4, 9, "gs_native")
        commands = [(0, 50, 1000, False), (1, 0, 0, True), (2, 70, 10, False), (3, 0, 0, True)]
        with patch.object(host, "guard"), patch.object(service.os, "open", return_value=123) as opened, \
                patch.object(service.os, "fstat", return_value=SimpleNamespace(st_mode=stat.S_IFCHR)), \
                patch.object(service.os, "close") as closed, patch.object(service.fcntl, "ioctl") as ioctl:
            host.haptics(device, commands)
            self.assertEqual(opened.call_args.args[0], "/dev/gsnative-4-3:1.0")
            self.assertEqual(ioctl.call_count, 4)
            for call, command in zip(ioctl.call_args_list, commands):
                self.assertEqual(call.args[:2], (123, 0x40204773))
                motor, amplitude, duration, cancel = command
                self.assertEqual(struct.unpack("=8I", call.args[2]),
                                 (1, motor, amplitude, duration, int(cancel), 0, 0, 0))
            closed.assert_called_once_with(123)

    def test_invalid_internal_command_rejected_before_any_open(self):
        host = service.Host("never", "never")
        with patch.object(service.os, "open") as opened:
            for commands in ([], [(0, 10, 1001, False)], [(0, 1, 1000, True)],
                             [(0, 1, 1000, False)] * 2):
                with self.subTest(commands=commands), self.assertRaises(service.Unsafe):
                    host.haptics(None, commands)
            opened.assert_not_called()

    def test_replacement_between_guard_and_open_never_receives_pulse(self):
        host = service.Host("never", "never")
        with patch.object(host, "guard", side_effect=[None, service.Unsafe("new instance")]) as guard, \
                patch.object(service.os, "open", return_value=123), \
                patch.object(service.os, "fstat", return_value=SimpleNamespace(st_mode=stat.S_IFCHR)), \
                patch.object(service.os, "close") as closed, patch.object(service.fcntl, "ioctl") as ioctl:
            with self.assertRaises(service.Unsafe):
                host.haptics(SimpleNamespace(node="/dev/gsnative-fake"), [(0, 75, 1000, False)])
            self.assertEqual(guard.call_count, 2)
            ioctl.assert_not_called()
            closed.assert_called_once_with(123)

    def test_paused_or_replaced_instance_not_available(self):
        device = service.Device("4-3", "generation", "parent", "109c", 4, 9, "gs_native")
        entry = service.Entry(device, "active")
        manager = SimpleNamespace(inhibited=False, scan_error="", port_errors={},
                                  entries={device.port: entry}, observed={device.port: device}, host=Mock())
        backend = service.HapticBackend(manager)
        identity = next(iter(backend.devices()))
        entry.job = object()
        with self.assertRaises(api.Busy):
            backend.apply(identity, [(0, 50, 1000, False)])
        manager.host.haptics.assert_not_called()
        entry.job = None
        manager.inhibited = True
        self.assertEqual(backend.devices(), {})
        with self.assertRaises(service.Unsafe):
            backend.apply(identity, [(0, 50, 1000, False)])


class Transport(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.broker = api.Broker(self.backend, lambda: self.backend.now)
        self.selector = selectors.DefaultSelector()
        self.server = api.SocketServer.__new__(api.SocketServer)
        self.server.broker, self.server.selector = self.broker, self.selector
        self.server.listener = object()
        self.app, self.accepted = socket.socketpair()
        self.app.setblocking(False)
        self.accepted.setblocking(False)
        peer = self.broker.connect(1000)
        self.connection = api.Connection(self.accepted, peer)
        self.server.connections = {self.accepted.fileno(): self.connection}
        self.selector.register(self.accepted, selectors.EVENT_READ, self.server)

    def tearDown(self):
        if self.accepted.fileno() >= 0:
            self.server.drop(self.connection)
        self.app.close()
        self.selector.close()

    def dispatch(self):
        for key, mask in self.selector.select(0):
            self.server.handle(key, mask)

    def test_fragmented_valid_request_and_socket_disconnect(self):
        self.app.sendall(b'{"version":1,"op":')
        self.dispatch()
        self.assertEqual(self.connection.outgoing, bytearray())
        self.app.sendall(b'"list"}\n')
        self.dispatch()
        response = json.loads(self.app.recv(8192))
        self.assertTrue(response["ok"])
        self.assertEqual(response["devices"][0]["instance"], IDENTITY)
        self.app.close()
        self.dispatch()
        self.assertEqual(self.broker.peers, {})

    def test_oversized_request_disconnects_client(self):
        self.app.sendall(b"x" * 4097)
        self.dispatch()
        self.assertEqual(self.broker.peers, {})

    def test_unhashable_operation_and_deep_json_do_not_crash_transport(self):
        malformed = [b'{"version":1,"op":[]}\n', b'{"version":1,"op":{}}\n',
                     (b"[" * 1200) + b"0" + (b"]" * 1200) + b"\n"]
        for message in malformed:
            with self.subTest(message=message[:40]):
                self.app.sendall(message)
                self.dispatch()
                self.assertFalse(json.loads(self.app.recv(8192))["ok"])
                self.app.sendall(b'{"version":1,"op":"list"}\n')
                self.dispatch()
                self.assertTrue(json.loads(self.app.recv(8192))["ok"])
        self.assertEqual(self.backend.calls, [])


class ClientLibrary(unittest.TestCase):
    def test_nonobject_or_deep_broker_response_closes_client_cleanly(self):
        for payload in (b"[]\n", b"true\n", b"null\n", b'{"version":true,"ok":true}\n',
                        (b"[" * 1200) + b"0" + (b"]" * 1200) + b"\n"):
            with self.subTest(payload=payload[:40]):
                connection = Mock()
                connection.recv.return_value = payload
                with patch.object(client.socket, "socket", return_value=connection):
                    with self.assertRaises(client.HapticsError):
                        client.Client("fake-only")
                connection.shutdown.assert_called_once()
                self.assertGreaterEqual(connection.close.call_count, 1)

    def test_public_client_api_needs_only_socket_and_closes_owned_effects(self):
        backend = Backend()
        broker = api.Broker(backend, lambda: backend.now)
        peer = broker.connect(1000)
        class LocalSocket:
            def settimeout(self, _):
                pass
            def connect(self, _):
                pass
            def sendall(self, payload):
                answer = broker.request(peer, json.loads(payload))
                self.response = json.dumps({"version": 1, "ok": True, **answer}).encode() + b"\n"
            def recv(self, _):
                result, self.response = self.response, b""
                return result
            def shutdown(self, _):
                broker.disconnect(peer)
            def close(self):
                broker.disconnect(peer)
        with patch.object(client.socket, "socket", return_value=LocalSocket()):
            with client.Client("not-a-real-socket") as game:
                instance = game.devices()[0]["instance"]
                game.play(instance, [10, 20, 30, 40], 3600000)
                broker.tick()
                game.set_motor(instance, client.LEFT_TRIGGER, 55, 5000)
                self.assertEqual(broker.effects[instance].amplitude, [55, 20, 30, 40])
                game.stop(instance, 2)
                self.assertEqual(broker.effects[instance].amplitude, [55, 0, 30, 40])
            broker.tick()
            self.assertNotIn(instance, broker.effects)

    def test_heartbeat_thread_contract(self):
        game = client.Client.__new__(client.Client)
        game._stop = Mock()
        game._stop.wait.side_effect = [False, False, True]
        game._exchange = Mock()
        game._heartbeat()
        self.assertEqual(game._exchange.call_count, 2)
        game._exchange.assert_called_with({"op": "heartbeat"})
        self.assertTrue(all(call.args == (0.5,) for call in game._stop.wait.call_args_list))


if __name__ == "__main__":
    unittest.main()
