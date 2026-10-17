#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Only temporary files/fake children; never start Wine, Steam or a broker."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from trigger_bridge import launch


class Child:
    def __init__(self, code=None):
        self.code = code
        self.terminated = False

    def poll(self):
        return self.code

    def wait(self, timeout=None):
        return self.code or 0

    def terminate(self):
        self.terminated = True
        self.code = 0


class Launcher(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gsn-launch-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.wine, self.server, self.hook = (self.folder / name for name in ("wine", "wineserver", "hook.so"))
        for path in (self.wine, self.server):
            path.write_text("never executed\n")
            path.chmod(0o700)
        self.hook.write_bytes(b"\x7fELF\x02synthetic; never loaded")
        self.hook.chmod(0o600)
        self.env = dict(WINEPREFIX=str(self.folder / "prefix"), XDG_RUNTIME_DIR=str(self.folder))
        self.target = SimpleNamespace(source_path="/dev/input/event42", bus=2, address=9,
                                      to_dict=lambda: {"synthetic": True})

    def test_plan_has_no_process_broker_or_host_discovery_side_effect(self):
        with patch.object(launch, "client_type", side_effect=AssertionError("live access")), \
                patch.object(launch.subprocess, "Popen", side_effect=AssertionError("child")), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(launch.main(["plan", "--adapter", "steam-proton-sdl2"]), 0)
        plan = json.loads(out.getvalue())
        self.assertFalse(plan["live_adapter_enabled"])
        self.assertFalse(plan["requires_root"])
        self.assertEqual(plan["rt_gain"], 1)
        self.assertEqual(launch.plan(profile="forza-horizon-6")["rt_gain"], 3)

    def test_validation_never_authorizes_root_steam_or_inherited_preload(self):
        with patch.object(launch.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "root"):
                launch.validate([str(self.wine)], self.env, "nexus-sdl2", self.hook)
        with patch.object(launch.os, "geteuid", return_value=1000):
            for env, adapter in [(self.env, "steam-proton-sdl2"),
                                 (dict(self.env, LD_PRELOAD="other.so"), "nexus-sdl2"),
                                 (dict(self.env, GSN_TRIGGER_SESSION="old"), "nexus-sdl2"),
                                 (dict(self.env, WINEPREFIX="relative"), "nexus-sdl2")]:
                with self.subTest(adapter=adapter, env=tuple(env)):
                    with self.assertRaises(RuntimeError):
                        launch.validate([str(self.wine)], env, adapter, self.hook)

    def test_other_games_have_no_forza_gain_or_identity_in_environment(self):
        env = launch.game_environment(self.env, self.target, Path("/private/control.sock"), "a" * 32, self.hook)
        self.assertEqual(env["GSN_TRIGGER_SOURCE"], "/dev/input/event42")
        self.assertEqual((env["GSN_TRIGGER_USB_BUS"], env["GSN_TRIGGER_USB_ADDRESS"]), ("2", "9"))
        self.assertEqual(env["SDL_HIDAPI_LIBUSB"], "0")
        self.assertEqual(env["LD_PRELOAD"], str(self.hook))
        self.assertEqual(self.env.keys(), {"WINEPREFIX", "XDG_RUNTIME_DIR"})

    def fake_client(self, entries=None):
        class Client:
            def __enter__(client):
                return client
            def __exit__(client, *_):
                pass
            def devices(client):
                return [{"synthetic": True}] if entries is None else entries
        return Client

    def test_reversible_ephemeral_launch_without_root_or_configuration_edits(self):
        calls = []
        relay = Child()
        manifest = []
        def popen(args, **kw):
            calls.append((args, kw))
            if "--manifest" in args:
                path = Path(args[args.index("--manifest") + 1])
                manifest.append((path, json.loads(path.read_text()), path.stat().st_mode & 0o777))
                Path(args[args.index("--ready") + 1]).write_text("synthetic-ready")
                return relay
            return Child(0)
        verifier = []
        with patch.object(launch, "validate", return_value=self.server), \
                patch.object(launch.signal, "signal", return_value=None):
            result = launch.launch([str(self.wine), "private-argument"], hook=self.hook,
                                   environ=self.env, client_factory=self.fake_client(),
                                   discoverer=lambda _, **_kw: [self.target],
                                   verifier=lambda *a: verifier.append(a), popen=popen)
        self.assertEqual(result, 0)
        self.assertEqual(len(verifier), 2)
        self.assertEqual(len(calls), 3)
        self.assertTrue(relay.terminated)
        self.assertEqual(manifest[0][2], 0o600)
        self.assertEqual(manifest[0][1]["version"], 2)
        self.assertEqual(len(manifest[0][1]["session"]), 32)
        self.assertFalse(manifest[0][0].parent.exists())
        argv = calls[0][0]
        self.assertNotIn("pkexec", " ".join(argv))
        self.assertNotIn("setpriv", " ".join(argv))
        self.assertNotIn("GSN_TRIGGER_SESSION", calls[0][1]["env"])
        self.assertEqual(calls[1][1]["env"]["GSN_TRIGGER_SESSION"], manifest[0][1]["session"])

    def test_periodic_manager_busy_does_not_randomly_block_launch(self):
        entries = [{"instance": "a" * 64, "port": "2-3", "busy": True}]
        discovery, checked, calls = [], [], []
        relay = Child()
        def discoverer(current, *, include_busy=False):
            discovery.append((current, include_busy))
            return [self.target] if include_busy else []
        def popen(args, **kw):
            calls.append(args)
            if "--ready" in args:
                Path(args[args.index("--ready") + 1]).write_text("synthetic-ready")
                return relay
            return Child(0)
        with patch.object(launch, "validate", return_value=self.server), \
                patch.object(launch.signal, "signal", return_value=None):
            result = launch.launch([str(self.wine)], hook=self.hook, environ=self.env,
                                   client_factory=self.fake_client(entries), discoverer=discoverer,
                                   verifier=lambda *args: checked.append(args), popen=popen)
        self.assertEqual(result, 0)
        self.assertEqual(discovery, [(entries, True)])
        self.assertEqual(checked, [(self.target, entries), (self.target, entries)])
        self.assertEqual(len(calls), 3)
        self.assertTrue(relay.terminated)

    def test_ambiguous_or_stale_identity_never_launches_game(self):
        for targets in ([], [self.target, self.target]):
            with self.subTest(count=len(targets)), patch.object(launch, "validate", return_value=self.server):
                with self.assertRaisesRegex(RuntimeError, "exactly one"):
                    launch.launch([str(self.wine)], hook=self.hook, environ=self.env,
                                  client_factory=self.fake_client(), discoverer=lambda _, **_kw: targets,
                                  verifier=lambda *_: None,
                                  popen=lambda *_a, **_k: self.fail("game launched"))

    def test_post_authorization_instance_change_cleans_relay_and_never_starts_game(self):
        relay = Child()
        calls = []
        def popen(args, **kw):
            calls.append(args)
            if "--ready" not in args:
                self.fail("game launched with stale authorization")
            Path(args[args.index("--ready") + 1]).write_text("synthetic-ready")
            return relay
        checked = [0]
        def verify(*_args):
            checked[0] += 1
            if checked[0] == 2:
                raise RuntimeError("replaced device")
        with patch.object(launch, "validate", return_value=self.server), \
                patch.object(launch.signal, "signal", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "replaced device"):
                launch.launch([str(self.wine)], hook=self.hook, environ=self.env,
                              client_factory=self.fake_client(), discoverer=lambda _, **_kw: [self.target],
                              verifier=verify, popen=popen)
        self.assertEqual(len(calls), 1)
        self.assertTrue(relay.terminated)

    def test_relay_start_failure_never_launches_game(self):
        with patch.object(launch, "validate", return_value=self.server), \
                patch.object(launch.signal, "signal", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "relay could not start"):
                launch.launch([str(self.wine)], hook=self.hook, environ=self.env,
                              client_factory=self.fake_client(), discoverer=lambda _, **_kw: [self.target],
                              verifier=lambda *_: None, popen=lambda *_a, **_k: Child(1))


if __name__ == "__main__":
    unittest.main()
