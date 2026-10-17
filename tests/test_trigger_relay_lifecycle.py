#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Relay lifecycle diagnostics using fake metadata/broker and private Unix IPC."""
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from trigger_bridge import devices, protocol, relay

spec = importlib.util.spec_from_file_location("trigger_lifecycle_metadata", ROOT / "tests/test_trigger_relay.py")
fixtures = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fixtures
spec.loader.exec_module(fixtures)


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.metadata = fixtures.Metadata(base)
        self.entries = [self.metadata.add()]
        self.target = self.metadata.discover(self.entries)[0]
        self.directory = base / "session"
        self.directory.mkdir(mode=0o700)
        self.manifest = self.directory / "manifest.json"
        self.manifest.write_text(json.dumps({"version": 2, "uid": os.geteuid(),
            "session": fixtures.SESSION.hex(), "target": self.target.to_dict()}))
        self.manifest.chmod(0o600)
        self.path, self.ready = self.directory / "control.sock", self.directory / "ready"
        self.log = io.StringIO()
        self.client = fixtures.FakeClient(self.entries)
        self.errors = []
        self.worker = None

    def records(self):
        return [json.loads(line) for line in self.log.getvalue().splitlines()]

    def start(self, client_factory=None):
        # Python installs process signals only on the main thread. Suppress
        # that operation in this synthetic thread; production keeps signals.
        context = patch.object(relay.signal, "signal", return_value=relay.signal.SIG_DFL)
        context.start()
        self.addCleanup(context.stop)

        def run():
            try:
                relay.serve(self.path, self.manifest, self.ready, self.log,
                    client_factory=client_factory or (lambda _path: self.client),
                    validator=self.metadata.verify, allow_root=True)
            except Exception as error:
                self.errors.append(error)

        self.worker = threading.Thread(target=run, daemon=True)
        self.worker.start()
        self.addCleanup(self.finish)
        deadline = time.monotonic() + 2
        while not self.ready.exists() and self.worker.is_alive() and time.monotonic() < deadline:
            time.sleep(0.005)

    def finish(self):
        if self.worker is None:
            return
        if self.worker.is_alive() and self.path.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
                    producer.settimeout(0.5)
                    producer.connect(str(self.path))
            except OSError:
                pass
        self.worker.join(2)
        self.assertFalse(self.worker.is_alive(), "Synthetic relay did not terminate")

    def assert_cleaned(self):
        self.assertTrue(self.client.closed)
        self.assertFalse(self.path.exists())
        self.assertFalse(self.ready.exists())

    def test_clean_empty_producer_eof_has_terminal_reason_without_effects(self):
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        self.finish()
        self.assertEqual(self.errors, [])
        events = self.records()
        self.assertEqual([event["event"] for event in events],
                         ["relay_ready", "producer_connected", "relay_exit"])
        self.assertEqual(events[-1]["reason"], "producer_eof")
        self.assertEqual((events[-1]["frames"], events[-1]["outputs"]), (0, 0))
        self.assert_cleaned()

    def test_periodic_busy_is_not_identity_loss_or_terminal(self):
        self.entries[0]["busy"] = True  # Normal manager status job at startup.
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        # Exercise at least one real idle-health iteration without any effect.
        time.sleep(1.1)
        self.assertTrue(self.worker.is_alive(), self.errors)
        self.entries[0]["busy"] = False
        self.finish()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.records()[-1]["reason"], "producer_eof")
        self.assertFalse(any(event["event"] == "relay_error" for event in self.records()))
        self.assertFalse(any(call[0] in ("play", "stop") for call in self.client.calls))
        self.assert_cleaned()

    def test_real_identity_loss_is_distinguished_from_eof(self):
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        self.entries[0]["instance"] = "b" * 64
        self.worker.join(2)
        self.assertFalse(self.worker.is_alive())
        self.assertEqual(len(self.errors), 1)
        self.assertIsInstance(self.errors[0], devices.IdentityError)
        events = self.records()
        self.assertEqual(events[-2]["event"], "relay_error")
        self.assertEqual(events[-2]["stage"], "health")
        self.assertEqual(events[-2]["error_type"], "IdentityError")
        self.assertEqual(events[-1]["reason"], "error")
        self.assertEqual((events[-1]["frames"], events[-1]["outputs"]), (0, 0))
        self.assert_cleaned()

    def test_startup_failure_is_logged_without_private_error_text(self):
        private = "private-prefix/account/session-secret"

        def failed(_path):
            raise RuntimeError(private)

        self.start(failed)
        self.worker.join(2)
        self.assertEqual(len(self.errors), 1)
        events = self.records()
        self.assertEqual([event["event"] for event in events], ["relay_error", "relay_exit"])
        self.assertEqual(events[0]["stage"], "broker_connect")
        self.assertEqual(events[-1]["reason"], "error")
        self.assertNotIn(private, self.log.getvalue())
        self.assertNotIn(fixtures.SESSION.hex(), self.log.getvalue())
        self.assertNotIn(str(self.directory), self.log.getvalue())
        self.assertFalse(self.path.exists())
        self.assertFalse(self.ready.exists())

    def test_explicit_zero_keeps_session_until_terminal_close(self):
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
            producer.connect(str(self.path))
            zero = protocol.Message(protocol.EFFECT, 1, time.monotonic_ns(), os.getpid(), 7,
                                    0, 0, 0, self.target.source_path, fixtures.SESSION)
            producer.sendall(zero.encode())
            deadline = time.monotonic() + 1
            while not any(call[0] == "stop" for call in self.client.calls) and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(self.worker.is_alive())
            close = protocol.Message(protocol.CLOSE, 2, time.monotonic_ns(), os.getpid(), 7,
                                     0, 0, 0, self.target.source_path, fixtures.SESSION)
            producer.sendall(close.encode())
            self.worker.join(2)
        self.assertEqual(self.errors, [])
        self.assertFalse(self.worker.is_alive())
        self.assertEqual(self.records()[-1]["reason"], "producer_close")
        self.assertEqual((self.records()[-1]["frames"], self.records()[-1]["outputs"]), (2, 2))
        self.assert_cleaned()

    def test_cleanup_failure_does_not_mask_original_identity_error(self):
        def broken_close():
            self.client.closed = True
            raise OSError("private-cleanup-path")

        self.client.close = broken_close
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        self.entries[0]["instance"] = "b" * 64
        self.worker.join(2)
        self.assertFalse(self.worker.is_alive())
        self.assertIsInstance(self.errors[0], devices.IdentityError)
        self.assertTrue(self.records()[-1]["cleanup_failed"])
        self.assertNotIn("private-cleanup-path", self.log.getvalue())
        self.assert_cleaned()

    def test_decode_error_survives_forwarder_cleanup_failure(self):
        close_calls = []

        def broken_close():
            close_calls.append(True)
            self.client.closed = True
            raise OSError("private-decode-cleanup-path")

        self.client.close = broken_close
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
            producer.connect(str(self.path))
            wrong_session = protocol.Message(protocol.EFFECT, 1, time.monotonic_ns(), os.getpid(), 7,
                10000, 20000, 1000, self.target.source_path, bytes.fromhex("34" * 16))
            producer.sendall(wrong_session.encode())
            self.worker.join(2)
        self.assertFalse(self.worker.is_alive())
        self.assertEqual(len(self.errors), 1)
        self.assertIsInstance(self.errors[0], protocol.ProtocolError)
        self.assertEqual(self.records()[-2]["error_type"], "ProtocolError")
        self.assertEqual(self.records()[-2]["stage"], "decode")
        self.assertTrue(self.records()[-1]["cleanup_failed"])
        self.assertGreaterEqual(len(close_calls), 2)
        self.assertFalse(any(call[0] in ("play", "stop") for call in self.client.calls))
        self.assertNotIn("private-decode-cleanup-path", self.log.getvalue())
        self.assert_cleaned()

    def test_forward_identity_error_survives_forwarder_cleanup_failure(self):
        close_calls = []

        def broken_close():
            close_calls.append(True)
            self.client.closed = True
            raise OSError("private-forward-cleanup-path")

        self.client.close = broken_close
        self.start()
        self.assertTrue(self.ready.exists(), self.errors)
        self.entries[0]["instance"] = "b" * 64
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as producer:
            producer.connect(str(self.path))
            message = protocol.Message(protocol.EFFECT, 1, time.monotonic_ns(), os.getpid(), 7,
                10000, 20000, 1000, self.target.source_path, fixtures.SESSION)
            producer.sendall(message.encode())
            self.worker.join(2)
        self.assertFalse(self.worker.is_alive())
        self.assertEqual(len(self.errors), 1)
        self.assertIsInstance(self.errors[0], devices.IdentityError)
        self.assertEqual(self.records()[-2]["error_type"], "IdentityError")
        self.assertEqual(self.records()[-2]["stage"], "forward")
        self.assertEqual(self.records()[-1]["frames"], 1)
        self.assertTrue(self.records()[-1]["cleanup_failed"])
        self.assertGreaterEqual(len(close_calls), 2)
        self.assertFalse(any(call[0] in ("play", "stop") for call in self.client.calls))
        self.assertNotIn("private-forward-cleanup-path", self.log.getvalue())
        self.assert_cleaned()


class DiagnosticBounds(unittest.TestCase):
    def test_full_effect_log_retains_error_and_terminal_record(self):
        output = io.StringIO()
        diagnostics = relay._Diagnostics(output)
        for sequence in range(relay.MAX_LOG_RECORDS + 10):
            diagnostics(event="play_accepted", sequence=sequence, lt=1, rt=1, duration_ms=10)
        diagnostics.terminal(event="relay_error", stage="health", error_type="IdentityError")
        diagnostics.terminal(event="relay_exit", reason="error", frames=0, outputs=0,
                             dropped_records=diagnostics.dropped, cleanup_failed=False)
        diagnostics.terminal(event="relay_exit", reason="error")
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(records), relay.MAX_LOG_RECORDS)
        self.assertEqual([record["event"] for record in records[-2:]], ["relay_error", "relay_exit"])
        self.assertEqual(records[-1]["dropped_records"], 12)

    def test_broken_log_is_best_effort_and_does_not_raise(self):
        class BrokenLog:
            def write(self, _value):
                raise OSError("private-output-path")

        diagnostics = relay._Diagnostics(BrokenLog())
        diagnostics(event="relay_ready")
        diagnostics.terminal(event="relay_exit", reason="producer_eof")
        self.assertTrue(diagnostics.unavailable)


if __name__ == "__main__":
    unittest.main()
