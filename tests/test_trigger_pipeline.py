#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real ELF hook -> Unix bytes -> relay -> repository broker, fake motors only."""
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from trigger_bridge import protocol, relay


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


hook_fixture = load("trigger_pipeline_hook_fixture", "tests/test_trigger_hook.py")
relay_fixture = load("trigger_pipeline_relay_fixture", "tests/test_trigger_relay.py")

# No SDL initialization: this process calls the synthetic library through the
# actual compiled interposer, with real producer timestamps and peer PID.
PRODUCER = r"""
#define _DEFAULT_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if(argc != 2) return 90;
    void *sdl = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if(!sdl) return 91;
    int (*rumble)(void *,uint16_t,uint16_t,uint32_t) = dlsym(sdl,"SDL_JoystickRumbleTriggers");
    void (*finish)(void *) = dlsym(sdl,"SDL_JoystickClose");
    if(!rumble || !finish) return 92;
    if(rumble((void *)1,10000,20000,120)) return 93;
    usleep(150000);
    if(rumble((void *)1,0,0,0)) return 94;
    usleep(60000);
    if(rumble((void *)1,30000,40000,120)) return 95;
    usleep(150000);
    finish((void *)1);
    return 0;
}
"""


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse repository-owned fixture builders, never an installed runtime.
        hook_fixture.Hook.setUpClass()
        cls.path = hook_fixture.Hook.path
        source = cls.path / "pipeline-producer.c"
        source.write_text(PRODUCER)
        result = subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
                                 str(source), "-o", str(cls.path / "pipeline-producer"), "-ldl"],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        hook_fixture.Hook.tearDownClass()

    def test_actual_hook_stream_session_binding_stop_expiry_and_restart(self):
        fixture = hook_fixture.Hook()
        with tempfile.TemporaryDirectory() as directory:
            metadata = relay_fixture.Metadata(Path(directory))
            entries = [metadata.add("8-6", 24, "event17")]
            target = metadata.discover(entries)[0]
            path = self.path / "events.sock"
            path.unlink(missing_ok=True)
            frames = []
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(str(path))
                server.listen(1)
                server.settimeout(3)
                process = subprocess.Popen([str(self.path / "pipeline-producer"), str(self.path / "libSDL2-fake.so")],
                                           env=fixture.environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                connection, _address = server.accept()
                with connection:
                    pending = bytearray()
                    while chunk := connection.recv(17):  # Deliberately fragment frames.
                        pending.extend(chunk)
                        while len(pending) >= protocol.SIZE:
                            frames.append(protocol.decode(bytes(pending[:protocol.SIZE])))
                            del pending[:protocol.SIZE]
                    self.assertEqual(pending, b"")
                _stdout, stderr = process.communicate(timeout=3)
                self.assertEqual(process.returncode, 0, stderr.decode())
            path.unlink(missing_ok=True)
            self.assertEqual(len(frames), 4)
            self.assertEqual([frame.sequence for frame in frames], [1, 2, 3, 4])
            self.assertEqual({frame.pid for frame in frames}, {process.pid})
            self.assertEqual({frame.source_path for frame in frames}, {target.source_path})
            self.assertEqual({frame.session for frame in frames}, {bytes.fromhex(hook_fixture.TOKEN)})

            api = load("trigger_pipeline_core_broker", "tools/service/haptics_broker.py")
            now = [frames[0].monotonic_ns]
            class Backend:
                def __init__(self):
                    # Model concurrent ordinary grip FF. The bridge must not
                    # touch either value when it starts/stops/expires triggers.
                    self.motors = [0, 0, 77, 66]
                    self.calls = []
                def devices(self):
                    return {target.instance: {key: value for key, value in entries[0].items() if key != "instance"}}
                def apply(self, instance, commands):
                    self.assert_identity(instance)
                    for channel, amplitude, duration, cancel in commands:
                        self.motors[channel] = amplitude
                        self.calls.append((channel, amplitude, duration, cancel))
                def assert_identity(self, identity):
                    if identity != target.instance:
                        raise AssertionError("A foreign instance was addressed")
            backend = Backend()
            broker = api.Broker(backend, clock=lambda: now[0] / 1e9)
            peer = broker.connect(os.getuid())
            class Adapter:
                closed = False
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
            client = Adapter()
            forwarder = relay.Forwarder(client, target, bytes.fromhex(hook_fixture.TOKEN), process.pid,
                                        clock_ns=lambda: now[0], validator=metadata.verify)
            starts = 0
            for frame in frames:
                now[0] = max(now[0], frame.monotonic_ns)
                forwarder.receive(frame.encode())
                self.assertTrue(forwarder.flush())
                if frame.kind == protocol.EFFECT and frame.duration_ms:
                    starts += 1
                    self.assertTrue(all(value > 0 for value in backend.motors[:2]))
                    now[0] += 121_000_000
                    broker.tick()
                    self.assertEqual(backend.motors[:2], [0, 0], "finite effect must expire before next game call")
                else:
                    self.assertEqual(backend.motors[:2], [0, 0])
                self.assertEqual(backend.motors[2:], [77, 66])
            self.assertEqual(starts, 2)
            self.assertEqual({command[0] for command in backend.calls}, {0, 1})
            self.assertTrue(all(command[2] <= 1000 for command in backend.calls))
            forwarder.close()
            self.assertTrue(client.closed)


if __name__ == "__main__":
    unittest.main()
