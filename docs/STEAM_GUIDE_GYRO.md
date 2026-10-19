# Steam gyro response only while Guide is held

19 October 2026. **Offline isolation, not a completed diagnosis or fix.**
The maintainer reports that the Gamescope gyro display responds while Guide
is held. The investigation now rules out a Guide requirement in the tested
sensor emitter and SDL fixture, and identifies concrete Steam-side selection
and notification boundaries. It does **not** establish which boundary changed
in that real run. A pure rendering defect and a Guide-selected motion context
remain hypotheses. The earlier failed late-arrival test remains unaccepted.

[Hashes, addresses, test results and evidence limits](steam-guide-gyro-offline.json)
supplement [the real-run record](STEAM_GYRO_HOTPLUG.md#human-follow-up-display-works-while-guide-is-held)
and [the prior downstream map](STEAM_GYRO_DOWNSTREAM.md).

## Method and scope

Only stored regular reference files, project sources and synthetic test
objects were inspected. The pinned ELF32 client and UI have the same hashes
as the earlier downstream study. Their equivalence to the running Gamescope
target's Steam binaries was **not** checked in this offline task. Native
addresses below are file-backed ELF virtual addresses, never live addresses.
The manifest maps each region through its actual ELF section; the button
tables in `.data` have a different file/virtual offset from `.text`.

No Steam application/vendor client was executed. SDL alone runs inside the
existing audited device-free Bubblewrap namespace. There was no SSH, network,
sudo, process-memory read, real input/IIO/USB open, Steam setting change,
installation, module operation or live trial. Proprietary files, code excerpts
and disassemblies are not included in Git. Calibration remains paused.

## Driver and SDL do not require Guide in the tested paths

`gsn_gyro_report()` checks sensor registration and the selected experimental
conversion; it does not inspect `last_guide`, `BTN_MODE` or the extra-button
bits. `gsn_imu()` calls that emitter before passing the same packet's extras
to `gsn_extras()`. Guide is reported separately on the gamepad. Changing the
Guide bit cannot select a new scale or enable branch in this emitter.

The actual extracted adapter functions now run against fake input objects
through eight released/held/released states. Each supplied frame produces
fresh six-axis values and its timestamp, with Guide and a paddle tracked
independently. ASan/UBSan pass. This covers emission from a supplied frame;
it does not prove physical packets arrive independently of Guide, or test
Linux input-core suppression, USB acknowledgements, runtime idle or RF.

The existing SDL sensor probe adds the real Guide button mapping and two
synthetic holds, with eight distinct motion frames before/during/after them.
It verifies Guide state, both enabled sensors, event instance IDs, timestamps,
fresh gyro values in events and cache, and unchanged finite acceleration.
It respects SDL's minimum Guide-hold delay before checking release.

Both system SDL3 and the pinned Steam ELF32 SDL pass all eight stages. The
other sensor/paddle scenarios and SDL2 baseline still pass: **24 scenario
runs overall**, including the two SDL3 Guide sequences. This reproduces no
Guide gate in SDL under these conditions. The probes explicitly allow
background events and create no actual window; they do not reproduce Steam's
mapping contexts, UI subscriptions, window focus or Gamescope.

## The simple background-focus explanation is insufficient

The pinned client's SDL initializer at `0x11e7970` explicitly requests
`SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` at `0x11e79ab`. This is the same hint
used in our probes. Therefore assuming Steam simply left SDL's background
events disabled is not supported by this reference code.

This is an initialization call, not a live measurement of its success or
later overrides. It does not rule out Steam's own application/focus policy,
device selection or Gamescope input routing.

## What Guide actually changes in the inspected Steam code

The SDL event dispatcher sends button events to `0x19c2500` and sensor events
to `0x19c28c0`. The button handler can ignore SDL Guide button index 5 when
backend flag `+0x6e` is set. That branch controls the button path; it is not
an IMU-enable instruction. The converter's two button tables at `0x2fb7220`
and `0x2fb7140` both translate index 5 to internal mask `0x2000`.

A later configured-context path at `0x1288538` tests that mask when its
configuration byte `+0xcc` is set. It writes context state `+0x4d1` and passes
the Guide boolean through virtual slot `+0x58` of its accumulator. The
constructor and RTTI identify that object as `CInputAccumulator`; that slot
is `0x12808e0`, which writes accumulator byte `+0x5ec`. **This proves internal
Guide-dependent processing exists. It does not prove that this byte gates
gyro acquisition or causes the observed display failure.** A generic
Guide/chord branch must not be relabeled as a sensor-enable fix.

## The display needs an existing selected motion source

The notification producer reads a selected per-controller context at
`context + index*0x210 + 0x238` (`0x1235e64`). If absent, it skips motion
notifications. It looks up the left/main motion source as feature 16/10
with **creation disabled** (`0x1235e93`, `0x1235ef1`). Lookup at `0x1293130`
returns NULL when the requested cached source is missing and creation is
false. Opening the UI/subscribing therefore does not create that source
through this lookup. A source that is missing in the selected context is a
sufficient block here even if the lower SDL cache contains motion.

An existing source must also expose valid published state, selected nonzero
acceleration and a speed subscriber before a rate notification is built.
The inspected periodic pass over all sixteen controller slots (`0x1236ea8`)
contains no Guide-button condition. The UI speed callback then copies the
message by controller index and IMU side, and the numeric renderer reads
`GyroRawSpeed`; neither inspected branch tests Guide. These facts narrow the
simple claim that holding a button merely repaints an otherwise complete
rate message, without ruling out other UI scheduling behavior.

**Leading hypothesis:** Guide changes Steam's active input context, motion
source processing or delivery policy, allowing the selected source to become
usable for notifications. A missing/stale context or invalid source after
late arrival would fit the symptom. We have not traced the complete Guide-to-
context selector or observed those states in the target. This is not yet a
proved root cause, a Steam bug verdict, or grounds for another kernel patch.

## Decision and next evidence boundary

Preserve the working driver, real six-axis contract, raw IIO, paddles, normal
FF and trigger bridge. No fake Guide hold, extra key events, forced layout,
different calibration factor or repeated publication is warranted.

The next useful evidence would distinguish these stages for the **same**
controller instance before/during/after Guide: lower sensor/event freshness;
selected context and main motion source; source validity and cached real
acceleration; speed subscriber and notification payload; displayed result.
If source or validity changes only with Guide while lower samples continue,
the failure precedes rendering. If valid notifications continue without
Guide but the display stops, the UI-delivery/rendering boundary is implicated.
If lower samples stop, return to the driver/runtime/USB boundary instead.

That would need a separately reviewed, explicitly authorized read-only live
observation, with exact target binary identity and bounded access. Existing
open-node snapshots do not supply it; the older desktop SDL-cache capture
is not a Guide-synchronized Gamescope trace. No such observation starts here.
Continuous motion without Guide and real reconnect acceptance remain open.

## Reproduce the nonhardware checks

```sh
DEBUGINFOD_URLS= LLVM_SYMBOLIZER_OPTS=--no-debuginfod make test-sensor test-sdl
python -B tests/run_sdl_sensor_test.py --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0 --check-steam-layout
```

The layout option rejects any library hash except the previously reviewed
ELF32 reference. It executes only SDL in the audited namespace. Static client
inspection is separately hash-pinned in the manifest and does not execute
the client. All private test artifacts stay under ignored `build/`.
The new adapter test initially exposed a **test-fixture** conflation of button
capabilities and current pressed state; these are now separate fake fields.
It was not a production driver defect. No runtime/package version changes.
The checksum inventory is refreshed for all 341 tracked project files other
than itself, including already committed files missing from its older state.
This is an inventory refresh, not additional source changes or release approval.
