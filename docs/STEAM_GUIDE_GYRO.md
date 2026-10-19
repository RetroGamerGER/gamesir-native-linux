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

## Metadata precheck stopped before authentication

The user subsequently reports that the display no longer reacts even while
Guide is held, and that Resume was run manually. The previous conditional
response is historical, not currently reproduced. A manual Resume does not
prove failed boot loading or missing gyro options. Module options take effect
at module load; an already loaded module does not re-read modprobe settings on
Resume. The service source loads the module in ExecStartPre; effective running
parameters and the current device instance must be checked rather than assumed.

One separately approved metadata-only SSH attempt returned 127 with
`fish: Unexpected '}' found, expecting ')'`. The remote shell rejected the
command before sudo authentication and before the read program. Stdout was
empty, no password marker was emitted, no precheck result exists. There was
no retry or Steam/driver change. This supplies no current motion diagnosis,
module-option evidence or current sensor-FD result.

The cause is raw nested Python source passed through POSIX `shlex.quote` to
Fish. A small own-source fixture now reproduces a Fish quote error while the
same command works in Bash. Other backslash patterns can be changed silently;
a mere zero exit status is therefore insufficient transport validation.

The pure builder `tools/sdl/ssh_python_payload.py` validates the size and Python
syntax locally, encodes the UTF-8 source in Base64 and places only its ASCII
token inside a fixed shell-quoted bootstrap. `/usr/bin/env LC_ALL=C` avoids an
implicit shell-specific assignment prefix. No source single quotes, backslashes
or newlines reach the shell parser. The fixed sudo/Python prefix remains;
stdin is not used for source delivery and remains available for authentication.
The helper constructs text only; it performs no SSH, sudo, process/device access
or authentication. Encoding is not encryption and does not make arbitrary code
read-only: the caller still reviews the exact metadata source and pins its hash.

The 14 new committed regressions use real local Fish 4.9.3, Bash and system sh,
with isolated temporary HOME/XDG directories and no user shell configuration.
They check nested quotes, Unicode, backslashes, literal shell substitutions,
unchanged source/argv/stdin, locale, size/syntax rejection and exit status with
one execution. A test-owned ordinary-user sudo substitute consumes exactly one
synthetic password line; no actual sudo or password dialog runs. Importing the
existing observer's definitions does not invoke its main routine. Large source
near the 64-KiB source limit also passes. There are 133 passing regressions in
`make test-steam`, including the existing identity and terminal guards.

Private tests additionally verify the exact next command through local Fish's
syntax parser and an argv-only fixture, without executing its metadata program.
The actual failed command's parsing failure is reproduced too. Fifteen private
tests retain backing-file guards, source-hash refusal and the one-attempt gate.
The original failed folder is unchanged; a new folder contains the same read
program, corrected transport and fresh, unconsumed one-attempt receipt location.
[Sanitized offline evidence](steam-gyro-ssh-offline.json) records these limits.

The next proposed action remains only metadata: service/module state, exact
native paired input identity, Steam's open pad/sensor FDs and pinned SDL/client/
UI versions. It opens no evdev/IIO/USB device or process-memory file, makes no
setting change and retries nothing. It needs fresh explicit approval, including
the password dialog where required. No movement or Guide comparison is part of
that precheck. Different versions, missing/changed instances or denied metadata
stop it. A later process-memory observation would require its own reviewed
scope, explicit permission and local GO. No such new live action occurred in
this correction; the underlying Steam gyro cause is still unresolved.

## Gamescope process identity corrected offline

**Latest human report:** after a full PC reboot, native binding was automatic,
without Resume; the gyro display still responds only with Guide held. This
supersedes the earlier report of no response/manual Resume for the current
session, without erasing that history. It is not an agent-run motion trace.

A second separately approved metadata-only attempt passed SSH/authentication
and started the read program. Its saved result records kernel
`7.2.11-1-cachyos-deckify` and service active/running/enabled, then exit 2:
`No user-owned Gamescope process; stop`. No retry occurred. The guard ran
before module parameters, paired-node checks, Steam FDs and binary identity;
none of those were attested by this attempt. The error does **not** prove
Gamescope was absent or that gyro options were missing.

The old selector required both the proc directory owner's UID and exact
`comm == "gamescope"`. Linux's locally installed `proc_pid_comm(5)` manual
(man-pages 6.19) describes comm as a mutable, per-thread name, not an executable
identity. Static inspection of the local Gamescope ELF found its `main`
obtaining `pthread_self` at `0x5f3c0`, retaining that thread handle, and passing
`gamescope-wl` (string at `0x21341d`) to `pthread_setname_np` at `0x5fc31`.
These are file virtual addresses, not live memory. The local file was never
executed; its hash and evidence limits are in
[the sanitized record](gamescope-identity-offline.json). The remote process
name/version was not captured, so the precise remote failure is still unproved.

A test-owned Python child reproduces a renamed `gamescope-wl` task with
unchanged executable/credentials; synthetic proc fixtures reproduce rejection
by the legacy exact-name check. A separate local dumpability probe did **not**
reproduce a proc-directory-owner mismatch: its directory stayed user-owned,
although individual metadata files became root-owned. Do not claim that
dumpability explained the actual failure. The new UID quartet check uses
explicit process credentials and does not rely on directory ownership.

The diagnostic-only `tools/sdl/gamescope_identity.py` now:

- Resolves the expected `/usr/bin/gamescope`, compares the process exe path
  and backing-file device/inode/mode/size/timestamps, and rejects a deleted,
  replaced or unrelated executable. A matching name alone is insufficient.
- Requires real/effective/saved/filesystem UIDs to equal the expected non-root
  sudo caller, with no tracing or stopped/exiting state. No hardcoded user/UID.
- Pins PID/start time and reads identity again, requires one matching process,
  then rescans at precheck completion without adopting a replacement.
- Reports selection counts or specific metadata denials instead of folding
  all failures into an unsupported conclusion about the session. `Name` is
  bounded diagnostic context only and may legitimately change.

This establishes a compositor process for the expected user, **not** display
focus, exact seat/session membership or a parent-child relationship to Steam.
Stored launcher definitions allow Steam in a separate systemd user service;
requiring Steam to descend from Gamescope would be another unjustified guard.
No broader ownership or permission fallback has been introduced.

27 new regression tests cover identity, credential, ambiguity, permission,
disappearance and replacement cases. `make test-steam` passes 160 tests;
19 private preparation tests also pass, including the exact new payload's Fish
syntax/argv round trip, source hashes, one-attempt receipt and early failure.
Only fixture processes/files and stored regular reference files are involved.
There was no target connection, real sudo, vendor/Steam execution, device open,
installation, driver/configuration change or push during this correction.

### Next metadata-only step, not executed

The two consumed attempt folders remain unchanged. A new private folder holds
the corrected selector, unchanged common observer, reviewed read program and
Fish-safe transport, with source hashes and an unconsumed one-attempt gate.
The local launcher command is supplied to the maintainer for **fresh approval**;
the prepared files do not grant execution. One password dialog may authenticate
the remote read, with no password written to logs. Existing deadlines remain:
8-second connection, 180-second password dialog, 240-second local supervisor,
30-second remote read. No automatic retry or remote script copy is performed.

The read checks service state, Gamescope/Steam identities, native paired nodes,
effective module options, Steam's open-node links and pinned SDL/client/UI
files. It opens no input/IIO/USB device or process-memory file and requests no
motion, calibration or Guide action. A changed version/instance or denied
metadata stops it. The underlying Guide-dependent gyro cause is unresolved;
any later bounded memory/motion observation needs its own scope and approval.

## Reproduce the nonhardware checks

```sh
DEBUGINFOD_URLS= LLVM_SYMBOLIZER_OPTS=--no-debuginfod make test-sensor test-sdl
python -B tests/run_sdl_sensor_test.py --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0 --check-steam-layout
python -B tests/test_steam_gyro_ssh.py
python -B tests/test_gamescope_identity.py
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
