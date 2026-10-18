# Steam Input / Proton: offline gyro feasibility

18 October 2026. Initial scope: offline investigation, not Steam hardware
acceptance. Steam, Proton and games were not started by that investigation;
installed configuration, driver and device state were not changed. No network,
root, USB, evdev or IIO
hardware access was used. Only the existing device-free test harness ran with
local SDL libraries. Vendor libraries/source remain outside Git and packages.
The later user-operated Steam check and read-only diagnosis are recorded below.

## Decision

**Steam's locally bundled SDL3 can consume our existing gyro-only evdev
contract, with the paddles intact. Actual Steam Input motion remains
unconfirmed: its gyro UI is available, but the first manual check showed no
movement.** Passing an SDL probe does not execute the Steam motion backend.

Preserve one shared implementation: `gs_native` owns USB; paired gamepad and
motion evdev devices serve SDL/Eden and, if accepted, Steam Input. Raw IIO,
normal input, independent paddles, FF_RUMBLE and the optional trigger bridge
retain their existing interfaces. No second sensor decoder, alternate scale,
fake Sony identity, forced capability bit or new USB reader is justified by
these results. The accepted SDL/Eden milestone remains closed; known-angle
calibration is not reopened.

## Reproducible local evidence

See [the portable evidence manifest](steam-gyro-offline-evidence.json) for
hashes, versions, source locations and test counts. Paths in that manifest are
relative to the relevant locally available distribution/source tree. No
download is required or performed. References include the previously saved
Wine runtime sources and Xodus-derived Proton/Steamworks sources. They are
not asserted to be the exact source of the installed Steam/Proton binaries.

The local Steam manifest says build `1791918634`. Both 64-bit SDL3 libraries
(`ubuntu12_64` and `steamrt64`) report API version `3005000` and revision
`SDL-release-3.4.0-1576-gab5541ec5`. Presence does not prove which library a
future Steam launch selects. Each library was separately bound read-only into
the existing Bubblewrap harness; `dladdr` checks the loaded path, and hashes
are checked before/after. The Steam client binary was only inspected statically.

All six namespaces are separate, five capability sets zero, NoNewPrivs=1.
The sandbox exposes synthetic regular fixture files and basic pseudo devices,
no host input/USB/IIO devices, session IPC, Steam home or network. HIDAPI is
disabled **inside the probe only**, making this a targeted Linux-evdev test,
not evidence about Steam's eventual backend selection or access permissions.

| Case, run with each bundled SDL3 | Result |
| --- | --- |
| IIO fixture alone | No gamepad gyro; raw IIO is not sufficient |
| Paired evdev nodes with matching nonempty identity | Gyro and synthetic acceleration found |
| Mismatched sensor identity | Sensor is not assigned to the gamepad |
| Missing gyro Z axis | Incomplete gyro rejected |
| Zero axis resolution | Non-finite conversion detected; intentional negative case |
| Artificial 1 g / 90 degree/s reference | Expected m/s² and rad/s |
| Current observed gyro-only contract | Gyro present, acceleration absent, expected values and timestamp |

The last case uses the reviewed 12-byte saved IMU excerpt through our existing
conversion (`7 * raw`, resolution 100 counts/degree/s), not live input. Both
libraries deliver the expected SDL gyro event and the fixture's 16,000 µs
timestamp as 16,000,000 ns. All 32 combinations of A and the four paddles,
including release, pass while gyro remains readable. This does not measure
live timing, drift, packet loss or multi-application behavior.

The initial bundled-library attempt failed because its old-glibc `__fxstat`
entry point bypassed the fixture's existing `fstat` interception: both fake
files had device number zero and were deduplicated. The fixture now models
both ABI forms identically. The final tests include positive and negative
pairing cases; this was a harness defect, not a driver or Steam sensor defect.
System SDL3 and SDL2-compat retain all 14 sensor tests, and the existing
18-case button suite also passes. No proprietary library is copied into the
project or distributed with the tests.

## Initial static Steam client evidence

Both inspected 64-bit `steamclient.so` files reference
`SDL_GamepadHasSensor` and `SDL_SetGamepadSensorEnabled`, and contain gyro
processing / gyro-to-mouse / gyro-to-joystick components. The local UI checks
`ATTRIBCAP_GYRO` (bit 11) before exposing gyro sources/settings. The examined
gyro-source eligibility branch tests that capability, without a separate
generic-Xbox type exclusion in that branch.

These are positive static indications, **not a complete reconstructed call
chain**. We have not proved that the backend sets bit 11 for VID 3537/PID109c,
chooses evdev, pairs the nodes at the right time, accepts gyro without
acceleration, or implements every motion mode without gravity information.
Neither the old generic-Xbox display classification nor successful paddle
mapping alone answers that question. Do not edit Steam's capability mask or
invent acceleration data to make its UI appear compatible.

## First manual Steam check: UI present, motion not accepted

Later on the same date, the user started Steam normally and reported that
the gyro calibration countdown remained at zero. Cancel still worked and
the desktop remained responsive. The gyro settings page then showed three
zero angular velocities; the user reported no response to movement. This
is a failed Steam-motion check, not evidence of a system freeze. The user
subsequently confirmed that Eden still had working gyro after the reconnect.
That current countercheck supports a working driver-to-SDL/Eden path; a
reboot is not required simply to restore gyro after every reconnect.

Read-only inspection, without opening input/USB/IIO devices, established:

- The current native `109c` instance has both gamepad and gyro-only motion
  nodes, with the same nonempty session identity and user read access.
  Registration alone would not establish fresh samples; the Eden response
  above is separate user evidence.
- The running Steam process loads **`ubuntu12_32/libSDL3.so.0`**. The earlier
  64-bit tests did not establish this runtime choice.
- Process file-descriptor snapshots showed Steam opening both the gamepad
  and motion node during the investigation. Other snapshots showed only the
  gamepad. These are snapshots, not a continuous trace or proof of sensor
  event consumption. A persistent permission denial is not established.
- The same seven synthetic sensor scenarios also pass with the bundled
  **32-bit** SDL3: gyro-only events, units/timestamp and all 32 A/paddle
  combinations included. Existing fixture/probe sources were compiled with
  `clang -m32`, with a private auditor-path adjustment, in the same audited
  device-free sandbox. No package was installed. The checked library hash
  and API revision are in the evidence manifest. This manually adapted run
  does not add automatic 32-bit support to the committed test runner.

Static inspection of the local `steamui/sp.js` explains the visible wait:
after the countdown reaches zero, `StartGyroSoftwareCalibration` is sent
and the timer stops. Progress then depends on a calibration-state update
from the backend. The wizard includes accelerometer-tolerance and gyro-drift
stages; its success handler saves the tolerances only when **both** are
positive. Relevant character offsets in the hashed file are approximately
9,962,728 (stages/countdown) and 9,963,677 (save condition). No UI JavaScript
was evaluated or modified for this inspection.

Our evdev node deliberately exposes **gyro only**; acceleration remains in
raw IIO. A dependence of Steam's calibration or motion processing on
acceleration is therefore a concrete **hypothesis**, not a proven root cause.
The UI save condition does not prove that missing acceleration suppresses
all angular-velocity events. Do not add fabricated acceleration, silently
reuse gyro axis signs for acceleration, or replace the working Eden path.

A bounded static trace of the hashed `linux64/steamclient.so` also identifies
an SDL gyro-capability query and sensor-event handling (virtual addresses
`0x17e837b` and `0x17e96b0`, respectively). Gyro events are recorded separately
from acceleration in that handler. This is neither the full downstream
motion filter nor proof about the active 32-bit client implementation.
Disassembler labels inherited from the nearest exported symbol are not
recovered function names. No proprietary code or disassembly is distributed.

**Next investigation:** distinguish sensor reattachment/event processing
inside Steam from its calibration/filter prerequisites. Preserve the current
Eden result, gamepad, paddles and output interfaces. Live tracing, restarting
Steam or changing its settings require a separately agreed next step. This
diagnosis made no privileged calls, driver changes, new captures, Steam
configuration edits or restarts. Raw logs, account identifiers, local paths
and screenshots remain private. The exact Steam-side failure remains open.

## DualSense comparison: two input routes, not just a different name

The maintainer requested one final offline comparison on 18 October 2026.
No DualSense was opened or tested; no application, setting or driver changed.
The [earlier Linux/SDL comparison](DUALSENSE_SENSOR_COMPARISON.md) describes
its historical GameSir implementation. The following table uses the current
opt-in GameSir path in [SDL_EDEN_GYRO.md](SDL_EDEN_GYRO.md).

There are two distinct reference routes:

1. **Sony-specific HID handling:** the saved SDL HIDAPI dispatcher registers
   `SDL_HIDAPI_DriverPS5`, opens HID device paths and delegates sensor enabling
   to that device driver's `SetJoystickSensorsEnabled`. The installed SDL
   headers document `SDL_JOYSTICK_HIDAPI_PS5`; Steam's bundled 32-bit SDL
   contains that option and DualSense identification strings. The local
   Steam client also contains the controller-type string `PS5ControllerInput`.
   These establish Sony-specific support machinery, **not which route Steam
   selects for a particular DualSense**. The PS5-specific SDL implementation
   file is absent from the saved source subset; its complete report/calibration
   chain was not reconstructed here. Do not infer an exact proprietary Steam
   handler merely from a type-name string.
2. **Linux input handling:** the reviewed official `hid-playstation` source
   decodes Sony reports and publishes a separate six-axis motion evdev node.
   SDL's general Linux backend can pair that node with its gamepad and expose
   standard gamepad sensor events. This architecture is also the basis of
   our current GameSir sensor path. It is not necessary to impersonate a Sony
   device to provide a valid SDL sensor.

| Aspect | DualSense Linux reference | Current GameSir path |
| --- | --- | --- |
| Hardware report | Sony USB report `0x01` / 64 bytes or Bluetooth `0x31` / 78 bytes; gyro, acceleration and device timestamp | Existing decoded GameSir `109c` IMU packets; one USB owner, `gs_native` |
| Sensor channels exposed to SDL | Three gyro **and** three acceleration axes | Three gyro axes; acceleration remains raw IIO and is not available to Steam through this SDL path |
| Kernel normalization | Sony feature report `0x05` supplies calibration references; per-axis conversion, with documented fallback limits | User-accepted experimental 0.07 degrees/s/raw; no Sony calibration values, no certified angle/bias calibration |
| evdev gyro representation | 1024 counts/(degree/s), normalized by the kernel | `7 * raw`, 100 counts/(degree/s); SDL converts either representation to rad/s using its declared resolution |
| Acceleration representation | 8192 normalized counts/g; SDL converts to m/s² | No evdev acceleration axes; the experimental raw-IIO 8192 LSB/g value does not establish physical axis signs |
| Pairing | Shared kernel `uniq` derived from the Sony device identity | Shared nonempty per-binding session `uniq`; not a claimed hardware serial |
| Timing | Device ticks at nominal 1/3 microsecond, accumulated into `MSC_TIMESTAMP` | Host-derived active-stream microseconds; not a device clock |
| Acceptance here | Source comparison only; no new DualSense/Steam hardware test | Current Eden motion confirmed; Steam UI visible but movement still absent |

The differing integer resolutions are **not themselves an incompatibility**:
SDL converts both to the same physical units. Copying Sony's 1024 constant
would not resolve an unproven Steam processing problem. Likewise, renaming
the controller or editing a button mapping does not supply missing sensor
channels, calibration or event timing.

**Additional timing lead:** the installed Steam client contains
`gyro_auto_detect_polling_rate`. Its help text describes handling zero or
unexpected SDL3 sensor intervals, a legacy high-polling-rate issue, and a
packet-rate fallback. In the hashed 64-bit client, the registration sequence at
`0x1170ee1` ties this help text to that setting and a default string of `1`.
The matching help text is also present in the 32-bit client. This is static
evidence of timing-dependent processing, **not a read of the active setting,
proof that the GameSir hits that branch, or permission to change it**.
No 1000-Hz IMU rate is inferred from the controller's configured input rate.

**Recommendation for the next session:** compare Steam's sensor activation,
reattachment and timestamp consumption before attributing the zero display
solely to absent acceleration. If a six-axis requirement is then established,
extend the same existing evdev node using real coherent acceleration samples
and separately supported physical axis/sign metadata. Keep raw IIO, the
accepted gyro profile, Eden, all paddles and output ownership intact. Do not
add fake gravity, a Sony identity or a competing HID/USB reader. No further
live work follows from this comparison; the user requested stopping for today.

## Routes to Proton games

| Route | Evidence / limit |
| --- | --- |
| Steam Input gyro → mouse | Existing Steam gyro-to-mouse components make this the preferred route to investigate. The game receives ordinary mouse input, not a gyro-specific XInput field. Requires actual Steam recognition and appropriate layout; mixed mouse/gamepad behavior varies by game. |
| Steam Input gyro → stick | Existing gyro-to-joystick components are present. Can target ordinary controller input, subject to the game's deadzones/response. Not an unmodified sensor stream. |
| Native Steam Input API | Cached SDK defines `GetMotionData`; cached Proton `lsteamclient` forwards it, including the wow64 path. Requires a game using that API and actual backend support. Not proof of this installed runtime or GameSir output. |
| Ordinary Wine SDL → XInput | Reviewed `winebus` source handles buttons/axes/hats, not SDL controller sensor events. `XINPUT_GAMEPAD` has no gyro field. Our Linux evdev gyro is not automatically exposed to every Windows game. |
| Games expecting Sony-specific raw HID | Our current real GameSir identity/evdev contract does not emulate a DualSense. No compatibility promise for that path. |

The cached SDK's `InputMotionData_t` uses its own normalized velocity fields
and quaternion/acceleration contract; do not pass those units straight through
as SDL rad/s. Its gravity-based orientation description is an additional reason
to keep gyro-only versus full six-axis support explicit. Absence of gyro
handling in the reviewed Wine SDL backend is not a claim about every Wine,
RawInput, GameInput or native Steam Input path.

## Shared integration and compatibility acceptance

The maintainer explicitly requires all features to fit together. The final
deliverable must therefore be one coherent project/component set, with the
following boundaries and combined acceptance, rather than separate solutions
that replace one another:

- **One physical owner:** `gs_native` remains the only controller USB owner.
  SDL/Eden/Steam read the existing evdev contract. No raw-device hooks, global
  preload or exclusive input grab are introduced by this investigation.
- **One motion contract:** retain identity pairing, axis signs, rad/s,
  timestamps, the explicit experimental opt-in and unchanged IIO. Existing
  Eden acceptance does not validate Steam's defaults or motion filtering.
- **Inputs together:** test gyro while holding/releasing each paddle and
  combinations, plus ordinary buttons, sticks and triggers. Keep the real
  VID/PID, name and existing Paddle mapping. Steam layouts may still be needed;
  no automatic universal game action mapping is promised.
- **Outputs together:** existing grip FF and trigger-broker ownership/STOP
  rules remain authoritative. The Forza/Xodus bridge's 82 offline cases and
  Steam/Gamescope integration's 40 cases pass unchanged. They do not establish
  Steam trigger support or simultaneous live gyro/rumble acceptance.
- **Application ownership:** future tests must cover direct Eden use and
  Steam-mediated use separately, then their interaction. Steam's virtual pad,
  input hiding/grabbing, focus and physical/virtual duplication must not
  remove Eden motion or route input to two controllers accidentally.
- **Lifecycle:** after separate permission, check reconnect, suspend,
  application exit and reboot with stable pairing and stopped outputs. Repeat
  the relevant Steam/Gamescope case on the other supported environment;
  local 32-/64-bit library tests are not a remote-device/Flatpak acceptance.

Initial live plan (the first manual check above now records its outcome):
keep the current driver unchanged, verify the paired accessible nodes, start Steam normally with the
existing paddle integration and check whether it offers and reacts to a gyro
source. If it does, test a reversible mouse/stick layout and all existing
inputs/outputs. A game with native gyro support is not required for the
translated-input test. If recognition fails, retain Steam logs/capabilities
and investigate the backend-selection/gyro-only gate before proposing code.
No Steam library replacement, fabricated sensor capability or driver rewrite
is currently recommended.
