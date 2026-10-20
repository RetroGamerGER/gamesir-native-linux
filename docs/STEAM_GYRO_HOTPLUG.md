# Gamescope: later power-on and gyro reconnection

19 October 2026. **One user-led radio reconnect under revision 11 now has a
positive Steam/Gamescope gyro result without held Guide or Steam restart;
see the bounded acceptance below. General hotplug reliability remains open.**
Kernel/client/manager readiness integration was implemented and tested
offline at `f1f6c00`; subsequent revision-10 installation and failed late-gyro
observations are retained below. This supersedes
the unintegrated prototype at `468ddc6`. The existing gyro/acceleration units,
axis maps, raw IIO, paddles, FF and trigger ownership remain unchanged. During
the initial offline integration no installed file, running module, Steam or
controller was changed or opened.
The separately requested CachyOS check reads kernel/header metadata over SSH
and builds selected sources in an unprivileged working directory only.
Calibration remains paused. Historical SDL reproduction below retains its scope.

## Revision 11 user-led radio reconnect — 19 October 2026

Following the separately verified revision-11 installation, the maintainer
reported starting the service and invoking Resume manually. Unprivileged
readback confirms the new loaded srcversion `06354BBF7CEC05B29300CC8`, the two
root-write-only acquisition attributes, and an active/enabled service with no
automatic restart recorded. Available journals report bootstrap state 7,
error 0, failed stage 0, gamepad/IMU readiness and confirmed input publication.
The gamepad and six-axis motion node have the same nonempty session identity
and native USB parent. Registration/capabilities are not themselves motion proof.

The maintainer then explicitly confirms all of the following:

- The radio controller was switched off and back on; its USB dongle stayed
  connected.
- Gyro continued working in **Steam's gyro display in Gaming Mode**.
- Guide was not held and Steam was not restarted.

This is a **positive application result for this reported radio reconnect**.
The later metadata read still shows the same native USB instance, module and
service. No continuous RF trace, live input capture, game-gyro mapping, timed
radio-outage measurement or fresh paddle/motor regression was performed.
The protected manager socket and effective root-only module parameters were
not newly read with elevated rights; available journal and sysfs evidence have
their stated scope. Codex performed no start, Resume or device operation in
this user-led phase.

The observed startup began with an already xpad-initialized 100a device; kernel
logs show the optional handoff, including `handover=1` for the transition.
It therefore does **not** prove cold startup without previous xpad activity,
nor that removing such activity caused this gyro improvement. Revision 11 did
not change the sensor units or Steam configuration. Keep the earlier failures
and startup workaround as historical/known-limit evidence until repeatable
late-power-on, USB replug and boot cases are separately accepted on both hosts.
No extra test or automatic retry is authorized by this successful report.

## Result and evidence boundary

The maintainer reports that motion works in Gamescope when the controller is
on before Steam starts, but not reliably after later power-on/reconnection.
The earlier [same-host comparison](STEAM_ACCEL_EXTENSION.md#same-host-kde-and-gamescope-comparison)
found Steam opening only the gamepad in a failed case and both nodes in a
successful case. Those observations did not measure the exact arrival/ACL order.

The new device-free tests reproduce **a sufficient failure mechanism** in
system SDL 3.4.18 and each of the three previously hashed Steam SDL3 libraries,
including the observed ELF32 runtime. They do not establish that this is the
exclusive cause of the historical Gamescope failure.

| Synthetic sequence, same running SDL process | Result in all four libraries |
| --- | --- |
| Paired nodes exist at SDL initialization | Gyro found, synthetic nonzero values readable |
| SDL already running; sensor detected first, gamepad arrives afterwards | Gyro found without application restart |
| Gamepad opened; paired sensor added afterwards | Existing open gamepad remains without gyro; closing/reopening the test handle finds it |
| Sensor node exists but open returns EACCES; gamepad opened; sensor later readable | Existing gamepad remains without gyro after the permission-change notification |
| Prototype withholds gamepad publication until the paired sensor is detected/readable | Gyro available at first gamepad open; sensor-first reconnect in same process also succeeds |

Each case then removes both fake nodes, verifies the joystick count becomes
zero and reconnects sensor-first in the **same SDL process**, retaining gyro.
There are 20 scenario runs and 15 additional pure policy tests. Negative
scenarios pass by reproducing missing gyro, not by pretending they are fixed.
Sensor values are synthetic; these tests make no new physical calibration,
packet-loss, sample-rate, motor, paddle or hardware-lifecycle claim.
[Portable hashes and results](steam-gyro-hotplug-offline.json).

## Why registration order is insufficient

The preserved official [Linux SDL source](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c)
(`docs/sdl-source-manifest.json`, file hash rechecked) selects `GetSensor()`
from `LINUX_JoystickOpen()`. `MaybeAddDevice()` records later sensor discovery
without reconfiguring already-open joysticks. The enable path uses the selected
sensor. These source facts agree with the independently executed library tests;
the reference is not claimed as the exact source of Steam's bundled binary.

`gsn_input_register()` already registers the motion device before the gamepad.
That orders kernel registration, not completion of both udev workers, seat ACLs,
or SDL discovery. A node being present or readable *after* Steam opened its
gamepad does not prove it was usable at that first open. A later readable
snapshot cannot repair the missed association in the tested backend.

The tests use real inotify notifications on **regular files inside a private
/dev**, with our existing syscall fixture handling evdev queries. A synthetic
access-denial switch models an unavailable sensor. They do not execute real
udev/logind ACL processing, Steam event handling or Gamescope. No actual
compositor defect or universally necessary Steam restart is established.

## Implemented optional two-phase publication

`defer_input` defaults to **false** in the module. The prepared revision-10
service requests it explicitly, while the kernel actually defers only persistent
standard-109c bindings with **both** experimental gyro and real acceleration
enabled. Gyro-only, default-off motion, 100a and experimental 105e retain their
existing registration path. Old clients retain their behavior when the new
option is not selected; do not combine an old manager with explicit deferral.
A new manager using a kernel without this parameter takes the legacy path.
A coordinated future update must verify the actual loaded parameter/module.

1. The daemon establishes a filtered libudev **processed `udev`** monitor before
   any claim/bootstrap. It never treats raw kernel creation, a sysfs node or
   a udev database entry alone as completed sensor readiness.
2. The kernel prepares the gamepad and registers the existing motion node first,
   retaining raw IIO and the single USB reader. Gamepad input is not reported
   into an unregistered input object. The last pad/extra/guide state is retained
   and replayed on publication; idle neutralization clears this retained state.
3. After successful bootstrap and exact native-token attestation, the manager
   queries `input-info`, then enters `awaiting_sensor`. It matches the expected
   native interface, shared session `uniq`, sysfs input/event objects and the
   character-node lifetime to a processed receipt. Reused event numbers cannot
   inherit readiness from another binding, port or dongle.
4. The active seat UID is read through libsystemd. A bounded child resolves
   account/groups, drops its own real/effective/saved credentials and calls
   `access(2)` as that user **without opening the device**. Parent credentials,
   ACLs and permissions are untouched. No active seat is a defined headless
   case: once the processed receipt exists, publish normally; a later login
   discovers both existing nodes. Unknown seat/access-check failures are errors.
5. Only then does the manager issue **one** checked `publish-input`. The kernel
   takes USB-device then I/O locks, verifies the live binding, exact tokens,
   successful handoff, persistent 109c runtime and nonquiesced/nonfaulted state,
   then registers the prepared gamepad. It does not send USB commands, change
   identity, re-register an active pad or restart Steam. The following status
   read must confirm publication before the manager reports `active`/`ready`.

The private ABI gains additive `GSN_GET_INPUT_STATUS` / `GSN_PUBLISH_INPUT`
commands, with fixed 176-/24-byte layouts checked in ELF32 and ELF64 clients.
Existing structs and ABI version remain unchanged. Names/tokens are temporary
kernel/session identifiers, not hardware serials. Unknown commands and malformed,
wrong-instance or non-admin requests fail; STOP, END, PM/quiesce and disconnect
prevent pending publication. Registration failure consumes publication permission.
A fault during sleeping registration is reported as failure while retaining the
actual published state for cleanup; it cannot be claimed as a clean nonpublication.
The adapter tests model this case. They do not prove real kernel race freedom.

## Deadlines, supervision and recovery

Readiness has a fixed ten-second deadline after native attestation, not a
fixed startup sleep or a limit on normal play. Getter conflicts/duplicate events
cannot extend it. Account/access checking is bounded to one second, including
potential NSS work, and runs only while waiting. There is no automatic Steam,
USB or controller restart loop and no wider device access permission.

The lease persists the original deadline, publication-attempt latch and first
publication failure. Waiting does not consume new start budget or remove END/
cleanup authority. Release while waiting uses the existing attested END path.
Timeout, missing receipt, monitor overflow, denied access or failed publication
retain the first cause in status/failure history even if cleanup later fails.
A failed monitor inhibits further takeover and is visible in `status`.

After manager restart, an already-published exact instance can be recovered via
fresh kernel proof/status without another publish. An attempted but unpublished
operation is cleanup-only. A never-attempted pending instance retains its old
deadline and requires a fresh processed receipt; the new daemon does not invent
one from stored metadata. If none arrives, it fails within the original budget.
This deliberately favors an explicit recovery over an uncertain mutation.

The existing return guard remains authoritative: **END or xpad binding is not
a proved 109c→100a identity change**. If the USB device stays 109c, the manager
reports blocked/manual recovery; it does not guess a reset or mode-switch
packet. Disconnect/replacement invalidates the old permission. Startup, fallback,
PM and haptic-owner policies outside this readiness phase are retained.

A successful seat-access snapshot cannot atomically guarantee a future Steam
open while a user is switching sessions or ACLs change. Kernel tokens protect
binding/publication identity, not that application race. No full Gamescope
hotplug, arbitrary seat transition or suspend guarantee follows from offline tests.
The earlier SDL failure remains a sufficient mechanism, not the proved exclusive
cause of the historical Gamescope case. No Steam patch/library replacement or
global preload is introduced; the preload fixture remains test-only.

## Validation and next boundary

[Integrated offline evidence](input-publication-offline.json) records the final
source hashes, tests and module result. `make test` includes 25 new Python tests
for manager/processed receipts/access/cleanup/restart plus 28 actual-client
command cases over two ABIs. The extracted real registration/control adapter
checks exact tokens, capability/copy failures, legacy opt-in, STOP/PM/fault
rejection, failed/duplicate publication, an in-flight registration fault and
held standard/paddle replay. Existing startup, FF-lifetime, raw IIO, broker,
manager and package regressions remain required, not replaced by the prototype.

The source/package allowlist now includes the shared policy and processed-input
backend in the manager directory. Source-only staging verifies these files;
no package hook activates the service as part of this work. Package release is
prepared as `0.1.0.alpha3-10`; no installer is executed or transferred.
The same kernel/protocol/UAPI sources are built against matching prepared headers:

| Kernel | Toolchain | Build result |
| --- | --- | --- |
| `7.2.11-1-garuda` | Clang 23.1.3 | Passed; zero code warnings, one recorded compiler-version advisory (kernel Clang 23.1.1) |
| `7.2.11-1-cachyos-deckify` | GCC 16.2.1, matching header compiler | Passed; zero warnings, matching vermagic, no automatic USB aliases |

The CachyOS build uses only 17 explicit source/build-helper files transferred to
a fresh user-owned working directory over the existing SSH connection. All 17
hashes are verified before and after compilation, and the running kernel stays
the same. No sudo, package hooks, DKMS installation, service operation or module
load is performed. The module remains a build artifact, not runtime acceptance.

**Build preparation passed for both kernels; controlled first hardware
acceptance remains open. No unattended deployment acceptance.** Before any installation,
verify matching target kernel/headers, package/module/client versions and the
saved gyro opt-in. Then obtain separate permission for update/activation and
observe late power-on and radio reconnect in Gamescope, motion FD/UI response,
normal input/paddles, Eden and haptic ownership/STOP. Suspend and application-
startup races remain separate acceptance cases. Keep enough human preparation
buffer; no test is started by this implementation.

## Separately approved installation and paused start

The [19 October installation record](evidence/INPUT_PUBLICATION_INSTALL_20261019.json)
confirms one upgrade to revision 10 on the matching CachyOS kernel, all 118
payload files, real DKMS build with no compiler warning, matching module
srcversion/vermagic, retained sensor configuration and unchanged Steam packages.
The known deprecated DKMS `CLEAN` advisory was retained, not silently repaired.
Snapshot hooks created 137/138 and the initramfs hook completed.

A separate maintainer request then started the service once. It remains enabled;
the revision-10 module and processed-input monitor are active, but the manager
is deliberately paused with no leases/native bindings. No Resume occurred.
After the approved physical replug with controller reported off, the new USB
instance is still 109c/xpad. Read-only session/process metadata shows KDE and
no Gamescope. This precheck stops before takeover or sensor testing. Do not
adopt the unowned 109c, repeat the replug automatically or call this a successful
Gamescope correction. A verified supported start and actual Gaming Mode are
still required; subsequent actions retain their individual approval boundary.

## Subsequent controlled late-arrival run: Steam gyro still zero

The user rebooted after an unsuccessful KDE-to-Gaming-Mode transition. The
new boot confirms revision 10's service autostart, same kernel/module source
and Gaming Mode. The off-state device was 0575/usbhid and ignored; a separately
approved normal power-on produced a supported 100a/xpad source. Steam was
already running. One approved Resume then completed native bootstrap and
confirmed publication of that exact 109c instance. No second Resume or manual
error Release was issued. This sequence resumes management **after** power-on;
it does not establish autonomous late-power-on/reconnect acceptance.

The existing device-free observation policy needed three new legitimate phases
before the run: `input_check`, `awaiting_sensor`, `publishing_input`. They require
native 109c, remain nonactive, retain the original deadline and exact known-gap
quarantine, and cannot bypass errors or final lease attestation. 34 regressions
pass, including actual observer-loop waiting for final `active`. Only the copied
observer changes; no installed driver, manager or Steam file is changed by it.

The kernel handoff, original source, same parent, lease/tokens and publication
attempt are attested. The processed-input monitor and manager report no current
failure. At first the Steam main-process snapshot opens just the pad; after
the user opens the gyro UI it opens **both** readable paired pad/motion nodes
with matching session `uniq`. This differs from the earlier no-motion-FD case.
It does not prove read calls, SDL cache updates or downstream notification.

The user reports all three gyro UI rates remain zero during motion, while
normal inputs and all four independent paddles including combinations/release
work. **The requested late Steam gyro test fails despite successful native
publication.** No radio-reconnect repetition, Steam restart/calibration, motor
test or further runtime change follows. Do not present the ordering correction
as a complete fix or infer the exact remaining cause; inspect the actual
sensor events and SDL/downstream readiness offline before proposing another
separately approved live observation. Installation and normal-input success
remain valid. Original negative records and the earlier SDL mechanism remain
separate evidence, not a universal explanation.

## Human follow-up: display works while Guide is held

After the zero-rate report the maintainer reports that pressing Guide makes
the gyro react, then clarifies: **while holding Guide, the gyro display works**.
This qualifies the earlier zero-display conclusion; it must not be summarized
as complete absence of sensor response. It is a human observation without a
new agent-run capture, numeric/event trace, measured release behavior or any
new host/device access. The earlier records remain unchanged.

A Guide-dependent event-pump, notification or UI-refresh path is plausible.
A pure display defect is a hypothesis, not a proved diagnosis: the observation
does not separate input/event/cache processing from notification delivery or
rendering. The earlier static downstream map in STEAM_GYRO_DOWNSTREAM.md is a
reference for that separation, not a trace of this run. It also does not rule
out a driver-side or other data-path dependency. Do not infer normal game motion
or full kernel-to-application acceptance solely from this conditional UI result.

Continuous gyro display without holding Guide and radio-reconnect acceptance
remain open. No Guide/keyboard keepalive, fake button event, Steam modification,
new sensor selection or calibration is installed as a workaround. Existing
normal-input/paddle success and the running system are preserved. Any new live
comparison needs its own concrete approval.

The subsequent [targeted offline Guide investigation](STEAM_GUIDE_GYRO.md)
adds actual-emitter and SDL Guide-hold/release checks, the pinned Steam
background-hint call and the selected-motion-source notification boundary.
These narrow the cause without proving the target's failing runtime branch;
they do not change the negative acceptance or authorize a new live run.

## Reproduce without devices

```sh
DEBUGINFOD_URLS= LLVM_SYMBOLIZER_OPTS=--no-debuginfod make test
DEBUGINFOD_URLS= LLVM_SYMBOLIZER_OPTS=--no-debuginfod make test-sdl
python -B scripts/build_kernel.py
python -B scripts/analyze_kernel.py
```

All outputs stay under ignored `build/`. No module is loaded, no service changed,
no real input/USB/IIO node opened. Synthetic syscall fixtures run only inside
the existing audited device-free Bubblewrap namespace. The earlier 20 SDL
reproduction cases and their original hashes stay historical at `468ddc6`;
current integrated evidence is separate. No current-cache compatibility beyond
the pinned references is implied. No external symbols are downloaded by the
accepted regression commands. Failed intermediate build/analyzer logs are
retained; no sanitizer or required diagnostic was disabled to get a pass.
