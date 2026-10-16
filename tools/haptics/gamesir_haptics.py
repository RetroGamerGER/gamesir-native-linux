# SPDX-License-Identifier: GPL-2.0-only
"""GameSir local haptic API v1. Games need the dedicated group, never root/USB.

Use Client as a context manager. Its heartbeat thread maintains a two-second
application lease; closing, process death or transport failure stops its motors.
Application duration is a finite unsigned-32 millisecond value, not a 1 s test.
"""
import json
from pathlib import Path
import socket
import threading

SOCKET = Path("/run/gamesir-native-haptics/control.sock")
LEFT_TRIGGER, RIGHT_TRIGGER, LEFT_GRIP, RIGHT_GRIP = range(4)
MAX_DURATION_MS = 0xffffffff


class HapticsError(RuntimeError):
    pass


class Client:
    def __init__(self, path=SOCKET):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._error = None
        self._input = bytearray()
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.settimeout(0.8)
        try:
            self._socket.connect(str(path))
            self._exchange({"op": "heartbeat"})
        except Exception:
            self._socket.close()
            raise
        self._thread = threading.Thread(target=self._heartbeat, name="GameSir haptic lease", daemon=True)
        self._thread.start()

    def _exchange(self, command):
        with self._lock:
            if self._stop.is_set():
                raise HapticsError(self._error or "Haptic client is closed")
            message = json.dumps({"version": 1, **command}, allow_nan=False).encode() + b"\n"
            if len(message) > 4096:
                raise HapticsError("Request exceeds protocol limit")
            try:
                self._socket.sendall(message)
                while b"\n" not in self._input:
                    chunk = self._socket.recv(8192)
                    if not chunk or len(self._input) + len(chunk) > 8192:
                        raise HapticsError("Incomplete or oversized broker response")
                    self._input.extend(chunk)
                line, _, rest = self._input.partition(b"\n")
                self._input = bytearray(rest)
                response = json.loads(line)
                if type(response) is not dict:
                    raise HapticsError("Broker response must be a JSON object")
                if type(response.get("version")) is not int or response.get("version") != 1 or response.get("ok") is not True:
                    raise HapticsError(response.get("error", "Unsupported response version"))
                if response.get("last_error"):
                    raise HapticsError(response["last_error"])
                return response
            except (OSError, ValueError, RecursionError, HapticsError) as error:
                self._error = str(error)
                self._stop.set()
                try:
                    self._socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self._socket.close()
                raise HapticsError(self._error) from error

    def _heartbeat(self):
        while not self._stop.wait(0.5):
            try:
                self._exchange({"op": "heartbeat"})
            except HapticsError:
                return

    def devices(self):
        """Return current opaque instance IDs; select again after USB reconnect."""
        return self._exchange({"op": "list"})["devices"]

    def play(self, instance, amplitudes, duration_ms):
        """Four 0..100 values in LT, RT, left, right order; None preserves one.

        duration_ms applies only to non-None channels and accepts 1..0xffffffff.
        The reply means queued, not mechanical confirmation. No firmware writes.
        """
        return self._exchange({"op": "play", "instance": instance,
                               "amplitudes": list(amplitudes), "duration_ms": duration_ms})

    def set_motor(self, instance, motor, amplitude, duration_ms):
        if type(motor) is not int or not 0 <= motor <= 3:
            raise ValueError("motor must be 0 LT, 1 RT, 2 left grip or 3 right grip")
        amplitudes = [None] * 4
        amplitudes[motor] = amplitude
        return self.play(instance, amplitudes, duration_ms)

    def stop(self, instance, mask=15):
        """Stop only selected channels owned by this connection."""
        return self._exchange({"op": "stop", "instance": instance, "mask": mask})

    def release(self, instance):
        """Stop this connection's channels and release exclusive application use."""
        return self._exchange({"op": "release", "instance": instance})

    def close(self):
        self._stop.set()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._socket.close()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=1)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
