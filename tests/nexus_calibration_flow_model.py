# SPDX-License-Identifier: GPL-2.0-only
"""Research-only transition model of observed Nexus dialog behavior.

Independently authored from static observations, not extracted vendor code.
No target execution, transport, real timers, I/O, or firmware semantics.
Each method represents an already-dispatched UI action/watch notification;
this deliberately does not emulate Vue scheduling or its component lifecycle.
See docs/NEXUS_STICK_CALIBRATION_FLOW.md for evidence and limits.
"""

from dataclasses import dataclass, field


@dataclass
class ObservedDialog:
    device: str | None = "device-A"
    phase: int = 0
    visible: bool = True
    left: bool = False
    right: bool = False
    preparation_active: bool = False
    pending_completions: int = 0
    requests: list = field(default_factory=list)

    def request(self, operation):
        # deviceReq resolves the *current* selection for each invocation.
        if self.device is None:
            raise LookupError("No selected device; not a successful abort")
        self.requests.append((self.device, operation))

    def change_phase(self, destination):
        previous = self.phase
        self.phase = destination
        if previous == 3 and destination < previous:
            self.request("Exit")
        if destination == 0:
            self.left = self.right = False
        elif destination == 2:
            self.preparation_active = True
        elif destination == 4:
            self.request("Finish")

    def close(self):
        self.visible = False
        if self.phase == 3:
            self.request("Exit")

    def preparation_elapsed(self):
        if self.preparation_active:
            self.preparation_active = False
            self.change_phase(self.phase + 1)
            self.request("Start")

    def notification(self, device, *, active, left, right):
        # The inspected IPC/handler does not filter this event by device ID.
        if not active:
            return
        previously_complete = self.left and self.right
        self.left, self.right = left, right
        complete = self.left and self.right
        if complete != previously_complete and complete and self.phase == 3:
            self.pending_completions += 1

    def completion_elapsed(self):
        if self.pending_completions:
            self.pending_completions -= 1
            # No fresh visibility, phase, identity, or completion check.
            self.change_phase(self.phase + 1)

    def destroy(self):
        # Timer cleanup observed for interval only; no Exit here.
        self.preparation_active = False


def measuring():
    dialog = ObservedDialog()
    dialog.change_phase(1)
    dialog.change_phase(2)
    dialog.preparation_elapsed()
    return dialog
