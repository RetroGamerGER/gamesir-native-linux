# SPDX-License-Identifier: GPL-2.0-only
"""Offline prototype for a two-phase input publication contract.

Consumes already attested metadata. Does not read devices, sysfs or udev,
publish input devices, control a service, or grant USB ownership. Not imported
by the installed manager. See docs/STEAM_GYRO_HOTPLUG.md before integration.
"""
from dataclasses import dataclass
from enum import Enum
import math


class Action(str, Enum):
    WAIT = "wait_sensor"
    PUBLISH = "publish_gamepad_once"
    DONE = "already_published"
    ABORT = "abort_without_publication"


@dataclass(frozen=True)
class Binding:
    """Attested native session, not a hardware serial or a persistent port ID."""
    parent_token: str
    instance_token: str
    interface_path: str
    uniq: str


@dataclass(frozen=True)
class Sensor:
    binding: Binding
    node_token: str
    # Must refer to this exact input-node lifetime, not just the event number.
    processed_node_token: str
    readable: bool
    gyro_resolution: tuple[int, int, int]
    accel_resolution: tuple[int, int, int]


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    binding: Binding
    sensor_node_token: str = ""


class PublicationGate:
    """One bounded gate for one already owned binding; no retry/reconnect loop.

PUBLISH is a plan, NOT proof of publication or permission for a later mutation.
A future backend must atomically revalidate the bound kernel instance when
applying it, then acknowledge success with that same node/session proof.
"""
    def __init__(self, binding: Binding, now: float, timeout: float = 3.0):
        if (not all((binding.parent_token, binding.instance_token, binding.interface_path,
                     binding.uniq)) or not binding.uniq.startswith("gsn-") or
                not math.isfinite(now) or not math.isfinite(timeout) or
                timeout <= 0 or timeout > 10):
            raise ValueError("Invalid bounded native-pair readiness request")
        self.binding = binding
        self.deadline = now + timeout
        self.last_time = now
        self.terminal = ""
        self.published = False
        self.proposed_node = ""

    def abort(self, reason):
        self.terminal = reason
        self.proposed_node = ""
        return Decision(Action.ABORT, reason, self.binding)

    def observe(self, current: Binding | None, sensor: Sensor | None, now: float):
        if self.terminal:
            return Decision(Action.ABORT, self.terminal, self.binding)
        if not math.isfinite(now) or now < self.last_time:
            return self.abort("Invalid monotonic observation")
        self.last_time = now
        if current != self.binding:
            return self.abort("Binding disappeared or changed; no authority over replacement")
        if self.published:
            return Decision(Action.DONE, "Publication already acknowledged", self.binding)
        # Never carry a previously proposed permission across a new snapshot.
        self.proposed_node = ""
        if now >= self.deadline:
            return self.abort("Sensor readiness deadline; no unbounded wait or retry")
        if sensor is None:
            return Decision(Action.WAIT, "Paired sensor not observed", self.binding)
        if sensor.binding != current:
            return self.abort("Sensor belongs to another binding")
        if not sensor.node_token or sensor.processed_node_token != sensor.node_token:
            return Decision(Action.WAIT, "Processed hotplug event for exact sensor node missing", self.binding)
        if not sensor.readable:
            return Decision(Action.WAIT, "Target session cannot read the sensor", self.binding)
        # A gyro-only or malformed motion node must not masquerade as the
        # accepted six-axis Steam profile. No synthetic gravity or scale here.
        for values in (sensor.gyro_resolution, sensor.accel_resolution):
            if len(values) != 3 or any(type(v) is not int or v <= 0 for v in values):
                return self.abort("Missing or invalid six-axis sensor resolution")
        self.proposed_node = sensor.node_token
        return Decision(Action.PUBLISH, "Exact paired sensor processed and readable",
                        self.binding, sensor.node_token)

    def acknowledge(self, current: Binding, node_token: str):
        """Acknowledge the future backend's successful, revalidated operation.

This method does not perform that operation. A failed/uncertain backend must
report the original error and use the manager's existing guarded cleanup.
"""
        if (self.terminal or self.published or current != self.binding or
                not self.proposed_node or node_token != self.proposed_node):
            raise ValueError("No matching fresh publication proposal")
        self.published = True
        self.proposed_node = ""
