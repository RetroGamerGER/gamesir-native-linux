# Does 109c → 100a prove a radio connection?

20 October 2026. File-only comparison requested after the
[input-witness review](RF_LINK_CONNECTION_WITNESS.md). No new packet-byte
search, recording, SSH, network, device access, runtime change or push.

**Result:** the transition accompanies the labelled power-on in one passive
reference. It is not established as a sufficient or mandatory RF-ready trigger.
No synchronously labelled `100a`/controller-off counterexample was found in
the selected evidence. That absence is a coverage gap, not proof that `100a`
always means connected.

## Compared evidence

All ten originals from the earlier chronology inventory and the new passive
reference were rehashed: **eleven matching originals**. The saved, previously
crosschecked descriptor chronology identifies four captured `109c→100a`
transitions. These counts concern the selected recorded epochs; an initial
`100a` snapshot does not imply a captured preceding transition. Times below
are from each file's first packet, not physical RF timestamps.

| Reference | First new 100a descriptor | Context and temporal limit |
| --- | --- | --- |
| 11 October Deadband sensor/motor run | Frame 174003, 243.290142 s | 10.260455 s after the Release-to-games/close cue. Actual close time and RF state at the transition are not synchronously labelled. |
| 12 October Deadband motor run | Frame 177348, 239.827530 s | 6.825579 s after the Release-to-games/close cue. Again a return-phase observation, not an isolated RF power-on test. |
| 12 October native 300-second motor run | Frame 298575, 320.358494 s | 3.015841 s after recorded finalization began, in the END/stop/return context. This is not a precise timestamp of an END packet or a labelled RF edge. |
| 20 October passive reference | Frame 16243, 33.431024 s | After the 30.053342 s power-on cue and before human connection confirmation at 40.078859 s; receiver stayed inserted and Native remained paused. |

The first two runs explicitly instructed software release/closure and later
verified the returned `100a` identity. The third retains the approved finalization
record and successful return result. Their ordering establishes **return
context**, not that a particular END packet caused the personality change.
No radio-off/on contrast isolates the cause of those transitions.

In the fourth run the old `109c` lifetime ends at 31.883869 s, a new addressed
record appears at 33.403244 s and its complete device descriptor follows at
33.431024 s. The latter two times are distinct observations. Native did not
send a mode command. Ordinary xpad/HID initialization of the new instance is
recorded and must not be excluded from the history. The trace supports a
power-on-associated personality change, not the exact instant of RF pairing,
universal causality or successful native initialization.

Hashes and offsets are retained in the
[sanitized comparison](evidence/RF_PID_TRANSITIONS_20261020.json). Original
captures, phase receipts and analysis scripts remain private. No raw reports,
USB addresses, individual IDs, machine names or personal paths are published.

## What the controller-off records establish

- The approved 20 October physical reinsertion was explicitly confirmed with
  the controller off. Its fresh protected snapshot is **109c/xpad**, with empty
  paused management. The planned `100a` baseline was not reached. See the
  [recorded result](evidence/RF_LINK_100A_RETURN_ATTEMPT_20261020.json).
  This proves `109c` can be present without the radio controller; it is not a
  `100a`/off observation and says nothing about a transition that did not occur.
- The revision-14 controller-off boot also retains **109c**, with a failed
  native initialization and no accepted pad/IMU. It is an independently
  labelled off-state failure, not proof of a `109c→100a` transition. See
  [the reboot audit](RELEASE_AUDIT.md#revision-14-controller-off-restart-fails--20-october-2026).
  Older `100a` records inside `recent_failures` belong to historical instances
  and boots; do not relabel them as that boot's current USB device.
- The retained 14 October radio cycle has 217 manager observations and user
  confirmations of off/on with the receiver left inserted. The three original
  observation/confirmation files still match their original manifest. Kernel
  history shows `109c` removal → new `109c` → new `100a` → initialized `109c`.
  The off confirmation has no timestamp or packet-clock marker. Consequently
  the intermediate `100a` cannot be honestly labelled controller-off or
  controller-on from that confirmation alone.

There is therefore one labelled passive power-on association, three
software-return-context transitions, and no adequate paired negative control
for `100a` under radio-off. Do not substitute packet silence, neutral reports,
missing consumer activity, file modification times or historical leases for
that missing label. This is a comparison of selected readable saved evidence,
not an exhaustive claim about all possible device states.

## Decision and proposed waiting architecture

Follow-up: [an opt-in receiver-wait implementation](RECEIVER_WAIT_KERNEL.md)
is now prepared offline. It preserves the proof limits below; it has not been
installed or hardware-validated and does not introduce a PID-only RF gate.

**Do not use the PID transition as the sole connection/start authority.** It
can notify discovery that a *new* USB lifetime needs validation. Exact identity,
ownership, cleanup, per-instance attempt history and start budget still apply.
A software return must not become an automatic reinitialization loop. A manager
started after enumeration must also handle an already-present supported device
without insisting on seeing a prior `109c→100a` edge.

Prefer an explicit **receiver waiting** state in the kernel for normal
receiver/link operation, supervised by the existing thin manager. Waiting may
last until the user turns on the controller; a receiver alone is healthy and
does not imply a ready gamepad or sensors. Keep the following distinct:

1. Acquire the exact supported receiver once, with existing ownership guards.
2. Complete only separately justified receiver setup with finite USB transfer
   deadlines; retain one known receive context while awaiting controller data.
3. Accept native readiness only after the required initialization and valid
   current-instance sensor evidence. Do not require nonzero inputs or buttons.
4. On real USB removal, retire that lifetime. Rediscover and attest any
   replacement independently. Pause, release and suspend must work while waiting.

This is a proposed contract, **not an implemented or hardware-validated fix**.
It is not enough to remove VERIFY's timeout or keep sending the initialization
sequence. Existing writes sent while the controller is off may be discarded;
whether known receiver setup makes later data arrive without replay is still
unproved. Any maintenance traffic needs its own evidence. Keep genuine transport
errors, malformed data and uncertain stops terminal, preserve the first error,
and retain motor neutralization and all safety deadlines. A previously failed
instance must not be silently rehabilitated into healthy waiting.

The existing [file-only timeline prototype](STARTUP_TIMELINE_PROTOTYPE.md)
already demonstrates waiting without generating commands or consuming repeated
start candidates; it does not implement this kernel contract. This architecture
is preferable to more speculative byte interpretation or PID-only RF inference,
but the receiver-setup/readiness split needs separate offline implementation
and subsequently approved hardware acceptance. The manager should administer
ownership and recovery rather than repeatedly bootstrap an absent controller.

Validation: original hash/phase comparisons and evidence arithmetic pass;
existing offline decoder/replay, public README and licensing tests are rerun.
Only documentation/evidence changes are made. No installed state is read or
changed; Native remains *last verified* paused/empty, not freshly inspected.
