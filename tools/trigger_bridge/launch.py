#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Explicit per-launch trigger adapter. Import/plan never contacts the broker.

No privilege escalation, launcher configuration edits or device opens. The run
subcommand is a separately authorized live action, not an offline test.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
if not __package__:
    sys.path.insert(0, str(HERE.parent))
from trigger_bridge.devices import discover, verify

ADAPTERS = ("nexus-sdl2", "steam-proton-sdl2")
PROFILES = {"neutral": 1, "forza-horizon-6": 3}


def plan(adapter="nexus-sdl2", profile="neutral"):
    if adapter not in ADAPTERS or profile not in PROFILES:
        raise ValueError("Unknown adapter or profile")
    return dict(version=1, adapter=adapter, profile=profile,
                lt_gain=1, rt_gain=PROFILES[profile], requires_root=False,
                changes_launcher_configuration=False, opens_usb=False,
                kernel_changes=False, target_policy="exactly one verified native evdev instance",
                activation="explicit per-launch only; no global LD_PRELOAD",
                permission="existing gamesir-native-haptics group; no automatic escalation",
                live_adapter_enabled=adapter == "nexus-sdl2",
                validation="integrated version offline only; Steam/Proton needs separate runtime validation")


def client_type():
    # Checkout and installed layouts use the same core API, never an arbitrary
    # site-package or a second vendored copy with potentially different rules.
    candidates = (HERE.parent / "haptics/gamesir_haptics.py",
                  HERE.parent / "gamesir_haptics.py")
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("_gsn_launch_haptics", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Client
    raise RuntimeError("Matching GameSir haptics client is unavailable")


def validate(command, environ, adapter, hook):
    if os.geteuid() == 0:
        raise RuntimeError("The bridge and game must never run as root")
    if adapter != "nexus-sdl2":
        raise RuntimeError("Steam/Proton adapter is plan-only pending runtime validation")
    if not command or not Path(command[0]).is_absolute() or Path(command[0]).name not in ("wine", "wine64"):
        raise RuntimeError("Expected an absolute Nexus wine/wine64 executable")
    if not Path(command[0]).is_file() or not os.access(command[0], os.X_OK):
        raise RuntimeError("Wine executable is unavailable")
    prefix = environ.get("WINEPREFIX", "")
    if not prefix or not Path(prefix).is_absolute():
        raise RuntimeError("An explicit dedicated absolute WINEPREFIX is required")
    if environ.get("LD_PRELOAD"):
        raise RuntimeError("Existing LD_PRELOAD needs explicit compatibility review")
    if any(key.startswith("GSN_TRIGGER_") for key in environ):
        raise RuntimeError("Refusing inherited trigger-session configuration")
    info = hook.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
        raise RuntimeError("Hook must be a regular file without group/other write access")
    with hook.open("rb") as source:
        if source.read(5) != b"\x7fELF\x02":
            raise RuntimeError("Only the reviewed 64-bit ELF hook is supported")
    server = Path(command[0]).parent / "wineserver"
    if not server.is_file() or not os.access(server, os.X_OK):
        raise RuntimeError("Matching wineserver is unavailable")
    return server


def game_environment(environ, target, socket_path, session, hook):
    return dict(environ, GSN_TRIGGER_SOCKET=str(socket_path),
                GSN_TRIGGER_SESSION=session, GSN_TRIGGER_SOURCE=target.source_path,
                GSN_TRIGGER_USB_BUS=str(target.bus),
                GSN_TRIGGER_USB_ADDRESS=str(target.address),
                SDL_HIDAPI_LIBUSB="0", LD_PRELOAD=str(hook))


def stop_child(child):
    if child is None or child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=3)


def default_hook():
    installed = HERE / "libgamesir-trigger-sdl2.so"
    return installed if installed.is_file() else HERE.parents[1] / "build/trigger_bridge/libgamesir-trigger-sdl2.so"


def launch(command, *, adapter="nexus-sdl2", profile="neutral", hook=None,
           environ=None, client_factory=None, discoverer=discover, verifier=verify,
           popen=subprocess.Popen, clock=time.monotonic, sleeper=time.sleep):
    settings = plan(adapter, profile)
    environ = dict(os.environ if environ is None else environ)
    hook = Path(hook or default_hook()).resolve()
    server = validate(command, environ, adapter, hook)
    runtime = Path(environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.geteuid()}"))
    metadata = runtime.lstat()
    if not runtime.is_absolute() or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
        raise RuntimeError("Expected a private user runtime directory")
    # This read-only preflight opens only the control socket. discover/verify
    # read metadata; neither evdev nor usbfs is opened.
    factory = client_factory or client_type()
    with factory() as client:
        devices = client.devices()
        # Periodic passive manager jobs briefly mark a healthy instance busy.
        # Select by exact identity; the broker serializes any later motor work.
        targets = discoverer(devices, include_busy=True)
        if len(targets) != 1:
            raise RuntimeError("Expected exactly one unambiguous native target; no game launched")
        target = targets[0]
        verifier(target, client.devices())
    relay = child = None
    previous = {}
    with tempfile.TemporaryDirectory(prefix="gamesir-trigger-", dir=runtime) as directory:
        folder = Path(directory)
        session = secrets.token_hex(16)
        manifest, sock, ready = folder / "manifest.json", folder / "control.sock", folder / "ready"
        fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(dict(version=2, uid=os.geteuid(), session=session, target=target.to_dict()), stream)
        relay_command = [sys.executable, "-B", str(HERE / "relay.py"),
                         "--manifest", str(manifest), "--socket", str(sock),
                         "--ready", str(ready), "--log", str(folder / "events.jsonl"),
                         "--right-gain", str(settings["rt_gain"])]

        def interrupted(signum, _frame):
            if child is not None and child.poll() is None:
                child.send_signal(signum)
            raise InterruptedError("Trigger launch interrupted")

        try:
            for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                previous[signum] = signal.signal(signum, interrupted)
            relay = popen(relay_command, stdin=subprocess.DEVNULL, env=environ)
            deadline = clock() + 5
            while not ready.exists():
                if relay.poll() is not None:
                    raise RuntimeError("Trigger relay could not start; no game launched")
                if clock() >= deadline:
                    raise RuntimeError("Trigger relay readiness timed out; no game launched")
                sleeper(0.01)
            # Recheck before handing a stale authorization to a newly started
            # game. The relay repeats instance checks during actual effects.
            with factory() as client:
                verifier(target, client.devices())
            env = game_environment(environ, target, sock, session, hook)
            child = popen(command, env=env)
            result = child.wait()
            child = popen([str(server), "-w"], env=env)
            wait_result = child.wait()
            return result or wait_result
        finally:
            # Relay EOF closes its lease; any bounded packet still in flight
            # expires even if graceful cancellation cannot be acknowledged.
            stop_child(relay)
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("plan", "run"):
        sub = commands.add_parser(action)
        sub.add_argument("--adapter", choices=ADAPTERS, default="nexus-sdl2")
        sub.add_argument("--profile", choices=tuple(PROFILES), default="neutral")
        if action == "run":
            sub.add_argument("--hook", type=Path)
            sub.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            print(json.dumps(plan(args.adapter, args.profile), indent=2))
            return 0
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        return launch(command, adapter=args.adapter, profile=args.profile, hook=args.hook)
    except (OSError, RuntimeError, ValueError) as error:
        # Do not echo command arguments, tokens, prefixes or account state.
        detail = str(error) if isinstance(error, (RuntimeError, ValueError)) else (error.strerror or type(error).__name__)
        print(f"GameSir trigger bridge: {detail}; launch stopped", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
