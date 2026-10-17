# XInput plus a GameSir HID companion: feasibility review

Date: 2026-10-17. Static source review and replay of existing owned-device
captures only. No SSH, controller access, application execution, module,
binding, Steam or installed-file change. Gyro calibration remains paused.

## Assessment

**A smaller xpad/HID architecture deserves investigation for the ordinary
G7 Pro, especially for normal inputs and independent paddles.** Existing
captures contain stronger support for it than the earlier IF0-only analysis
showed. The present evidence does not establish continuous motion/paddle
delivery or four-motor output over that alternative path. Keep the working
native backend while evaluating equivalence; neither past effort nor a
working alternative for another model settles the architecture.

## What the linked project and comment establish

[PandaPro8K](https://github.com/Ab0ut47Pandas/PandaPro8K/tree/bfdefae4372dbf3a1b21dbefca81c8776b21ad2f)
is a Windows bridge. Its normal-input source is XInput; its additional
source is a vendor HID collection, combined into a virtual DualSense Edge
for Steam Input. HIDMaestro/HidHide and application translation are part of
that design. This is not a Linux xpad patch.

The [maintained reader](https://github.com/Ab0ut47Pandas/PandaPro8K/blob/bfdefae4372dbf3a1b21dbefca81c8776b21ad2f/src/bridge/panda_enhanced_stream.cpp#L32)
accepts `3537:10c5/10c6`, sends a 64-byte `0f f2` heartbeat initially and about
every 500 ms, and selects 64-byte input report `12`. Extra bits are at bytes
60 and 63. Those IDs/offsets differ from our `100a/109c` and known `10/3c/e0`
format. The heartbeat is an output command, even if described as
nonpersistent; this review did not transmit it.

A [separate Reddit commenter](https://www.reddit.com/r/Gamesir/comments/1vxtzvv/comment/pdfnc70/)
reports incorporating the idea into xpad and seeing all buttons in Steam.
The inspected comment provides no patch, commit or source link. No Linux
implementation was found in the inspected Panda repository tree or linked
comment. That is a bounded search result, not proof that no patch exists.
Its size, device coverage, licensing and teardown behavior cannot yet be
reviewed. The author also explicitly distinguishes the ordinary G7 Pro from
the characterized 8K model in the original discussion.

## New findings in our existing captures

The ordinary model's `100a` configuration has two independent interfaces:

| Interface | Existing binding/type | Endpoints | Recorded role |
| --- | --- | --- | --- |
| IF0 | xpad, vendor `ff/5d/01` | OUT `02`, IN `82`, max packet 32 bytes | Normal 20-byte XInput reports |
| IF1 | usbhid, HID `03/00/00` | OUT `04`, IN `84`, max packet 64 bytes | Keyboard/mouse/consumer collections and vendor reports |

Both captures below contain the same **214-byte IF1 report descriptor**:
SHA256 `8dc43b12e016a9e71059620ff503b825b77355001b8054cee876f4b88d64c516`.
Its vendor collection declares **input reports `10` and `12`, and output
report `0f`, each 64 bytes including its report ID**. Declared capability is
not evidence that a particular command activates it.

| Existing capture date | Descriptor frame in owned-device export | Successful 64-byte IF1 reports after return to `100a` |
| --- | --- | --- |
| 2026-10-11 | 34146 | One report `10`, with known `3c/e0` telemetry signature |
| 2026-10-12 | 26630 | Two reports `10`, with the same signature |

All three packets match the existing IMU parser's structural checks and
contain its six little-endian channel fields. **No actual report `12` was
observed in these two return epochs.** These packets alone do not confirm
physical paddle bits or a sustained sensor stream in XInput mode.

The attribution was checked against saved kernel add/remove events, a new
USB address, new descriptor requests and fresh `84` submissions preceding
the completions. They are not merely late completions of host URBs from
the former `109c` address. Nevertheless, firmware-internal samples queued
before the mode transition remain a plausible explanation. The telemetry
stops after the initial one/two reports in the recorded remainder.

Normal `82` XInput reports also occur on the returned `100a` instance.
This establishes coexistence of the two transports in that configuration,
not continuous enhanced acquisition. An earlier passive recording without
an activation attempt cannot rule out a heartbeat-enabled stream.

The [sanitized evidence record](evidence/XPAD_HID_CAPTURE_REVIEW_20261017.json)
contains original/derived capture hashes, generic descriptor bytes and
frame references. Original captures and host-specific exports remain private.

## Why the existing driver did not use this channel

The offline [replay filter](../tools/offline/gamesir_offline/replay.py)
deliberately accepts only IF0 and endpoints `82/02`; it labels IF1 unverified.
The [native USB probe](../kernel/gs_native_usb.c) also selects IF0 only.
The [protocol core](../src/gs_protocol.c) knows normal XInput fields and the
64-byte `10/3c/e0` layout, with gyro fields at byte 17, acceleration at 23
and extra-button bytes 57/58. The runtime only accepts XInput input while
in `100a`. These scope restrictions are not evidence that IF1 is unusable.

Do not silently change those gates or apply the 8K decoder offsets to our
capture format. A separate offline transport investigation can reuse the
known payload decoder without granting runtime authority to a new channel.

## xpad versus the current implementation

| Goal | xpad plus HID extension | Current gs_native evidence |
| --- | --- | --- |
| Normal gamepad input | Reuses the established xpad path | Native input demonstrated |
| Independent paddles | Plausible, provided sustained IF1 input and button mapping are verified | Demonstrated on the standard model; Steam needs the tested integration |
| Raw IMU | HID descriptor and brief recorded telemetry are promising; activation and freshness open | Six raw channels observed through the extended runtime |
| Calibrated motion | Still needs model-specific physical units, axes and bias | Same outstanding calibration boundary |
| Four independent motors | Not established by the paddle claim or the inspected Panda input reader | Native hardware commands and one Forza/Xodus trigger adapter tested |
| Lifecycle | Could avoid the mode transition and much of its recovery manager if the complete required feature set works in `100a` | Bootstrap, ownership and return exist, with PRE-ALPHA limitations |

The official [xpad source](https://github.com/torvalds/linux/blob/41363c27b8509bd4efcba244803edac9ba25d1b5/drivers/input/joystick/xpad.c)
is a USB-interface driver, without an existing generic HID hook. A second
HID interface needs explicit integration and safe input-device lifetime.
Separate evdev nodes do not automatically become one gamepad. A companion
HID driver, coordinated xpad extension or userspace merger are different
designs, with different maintenance costs. A small patch may be practical;
it is still a driver/module change.

xpad currently exposes two-channel `FF_RUMBLE`; its Xbox-One output packet
sets trigger channels to zero. Our proven 13-byte four-motor transport uses
IF0 in the extended runtime. It cannot simply remain concurrently owned by
gs_native while xpad owns that same interface. A full replacement needs
either coordinated four-channel output in the xpad path or separately
verified output through IF1, including independent stops and lifecycle.

The official [SDL Linux backend](https://github.com/libsdl-org/SDL/blob/f9d49358d27f55fb9a9128f1bc18efb034becabb/src/joystick/linux/SDL_sysjoystick.c)
automaps `BTN_GRIP*`, while our codes 704–707 need explicit paddle mapping.
Those standard codes are a possible improvement independent of transport;
changing them would require compatibility review of existing mappings.
Its evdev trigger-rumble method still reports unsupported. A transport
change therefore does not establish direct extra-button binding in every
XInput game, or remove the application-side trigger integration gap.

## Gyro factor and reuse

Panda's [README limitations](https://github.com/Ab0ut47Pandas/PandaPro8K/blob/bfdefae4372dbf3a1b21dbefca81c8776b21ad2f/README.md#known-limitations)
explicitly leave motion scale, polarity and exact accelerometer ordering
open. Its current [bridge code](https://github.com/Ab0ut47Pandas/PandaPro8K/blob/bfdefae4372dbf3a1b21dbefca81c8776b21ad2f/src/hidmaestro/PandaControlPanel/BridgeEngine.cs#L578)
passes decoded signed raw channels into virtual-controller sensor fields.
That does not identify our sensor, active range or LSB per degree/second.
Older project notes describe a different byte ordering/offset than the
maintained reader; mode and revision must be kept explicit. No new GameSir
gyro scaling factor is established and calibration remains paused.

No third-party code was imported or executed. Panda's own project is MIT,
but its [notices](https://github.com/Ab0ut47Pandas/PandaPro8K/blob/bfdefae4372dbf3a1b21dbefca81c8776b21ad2f/THIRD_PARTY_NOTICES.md)
identify a Microsoft-licensed abandoned driver prototype separately. Any
later reuse requires a file-specific provenance review; copying the whole
tree is not the proposed approach.

## Recommended next step

Prioritize a bounded **offline IF1 investigation**, while retaining the
working installed runtime:

1. Obtain the actual claimed Linux patch and review its device IDs,
   initialization, output, lifetimes and source provenance.
2. Index the saved IF1 descriptors and traffic separately from IF0; preserve
   the distinction between declared reports, residual payloads and streaming.
3. Compare model-specific command framing and any existing IF1 output with
   the Panda heartbeat. Do not transmit that command merely because the
   descriptor resembles another model's descriptor.
4. Design one logical gamepad with independent extras, and an ownership/stop
   contract for normal rumble versus trigger output. Reuse proven parsers and
   motor semantics where appropriate; do not promise unchanged packets on a
   different transport.

Only a separately approved, bounded hardware test could establish continuous
XInput-plus-HID input and equivalent motor behavior. Success could justify
substantially simplifying the production architecture. At this checkpoint
there is no replacement implementation, live test, installation or push.
