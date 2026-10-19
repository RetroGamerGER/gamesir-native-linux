# SDL / Eden: opt-in GameSir gyro integration

Status: 18 October 2026 — **installed locally and accepted in Eden's controller
settings** after separate installation and activation approvals. The user
confirmed SDL motion, matching directions/sensitivity, four independently
assignable paddles and preserved ordinary inputs. This is not an in-game,
reboot, suspend or universal-emulator acceptance claim. No push or release approval.

The maintainer subsequently **closed the current gyro milestone** after the
accepted live result and verified persistent local opt-in. Dedicated Steam
gyro integration was initially deferred for lack of a requested use case;
the later [offline Steam feasibility study](STEAM_GYRO_FEASIBILITY.md) is a
separate request and does not reopen calibration or authorize live changes.
Existing Steam paddle support stays intact. No further calibration, tests or
runtime changes follow automatically. Pending reboot and other validation
limits below remain explicit; milestone closure does not claim those passed.

Follow-up (19 October): the separately approved
[real-acceleration extension](STEAM_ACCEL_EXTENSION.md) is now loaded and
accepted in Steam's gyro UI with ordinary inputs and independent paddles.
This six-axis profile is now also saved in the local modprobe opt-in, verified
without a reload or restart. The user subsequently reports Eden
continues working; no new per-axis details were supplied. The detailed
historical Eden acceptance below still refers to gyro-only operation;
actual six-axis reboot acceptance remains separate. No gyro calibration is reopened.

## Decision and scope

The maintainer accepted the observed gyro directions and **0.07 degrees/s
per raw count**, with the diagnostic window at 1.00x. Continue with that
setting, without reopening the chip/factor search or the paused known-angle
calibration. The display multiplier is not a physical conversion factor.
The live window established a preferred qualitative response, not a measured
scale/bias certificate. The new runtime profile is explicitly experimental.

The new `experimental_gyro=1` module option enables the reviewed standard
G7 Pro `3537:109c` profile. Default is off; `100a`, `105e` and other variants
do not inherit this sensor assumption. It does not change USB initialization,
controller configuration, the manager, the gamepad name, or motor ownership.

## Data path

```
accepted 109c IMU packet
  +-- unchanged raw sample / coherent IIO buffer
  +-- GameSir G7 Pro Motion Sensors (evdev gyro)
        +-- SDL Linux gamepad sensor API (rad/s)
              +-- Eden SDL motion input (revolutions/s internally)
```

There is no second USB reader, userspace sensor daemon or IIO-buffer setup
for this path. The optional sensor node has `INPUT_PROP_ACCELEROMETER`
(the Linux motion-device classification, also used for gyroscopes),
`ABS_RX/RY/RZ`, zero fuzz/flat, resolution **100 counts/(degree/s)** and
values `7 * raw`. This represents 0.07 exactly with integer kernel arithmetic.
The signed wire endpoints are preserved as −229376 through +229369.
No rounding to an integer 14 LSB/(degree/s), double gain or 8192-derived
gyro factor is used. The strict verified-calibration API remains unchanged.

The observed right-handed body coordinates were `(G0, -G2, G1)` with
X right, Y forward and Z out of the face. SDL uses X right, Y up/out of the
face and Z towards the player: **SDL gyro = (G0, G1, G2)**. Positive
pitch/front-up, yaw/left and roll/left-grip-down follow the recorded signs.
The separate accelerometer remains raw IIO: no inferred accelerometer
permutation, fabricated gravity vector or transplanted Sony calibration.
This is a three-axis gyro integration, not complete six-axis sensor fusion.

The gamepad and sensor share a nonempty per-binding `uniq` consisting of the
current interface path and instance counter. It is a session association,
not a claimed factory serial. Simultaneous dongles and new bindings receive
distinct associations; no fixed physical USB port or event number is used.
Sensors are registered before the gamepad, to be discoverable when it opens.
Registration failures unwind through the existing probe cleanup. Disconnect
kills RX before unregistering the sensor. Gamepad/paddle/FF ownership remains
with the existing gamepad; the sensor exposes no buttons or force feedback.

## Time and stopping

Event timestamps use the same host monotonic receive time as the raw sample.
`MSC_TIMESTAMP` carries a **host-derived active-stream microsecond counter**,
not a firmware/hardware timestamp. The extra event preserves reports even
when the angular-rate integers do not change. Sub-microsecond remainders are
retained; the nonnegative 31-bit wrap matches SDL's Linux reader.

The existing neutralization path emits a final zero-rate report and breaks
the integration segment. The first subsequent sample advances the sensor
clock by one microsecond rather than integrating the suspended/disconnected
interval. Actual event timestamps still retain host elapsed time. No new
USB commands, rebind attempts, auto-restarts or manufactured raw IIO samples
are added. Raw IIO timestamp/count semantics are unchanged.

## Eden reference and limits

The locally observed AppImage filenames identify revision
`e0d47f2790`; its full upstream commit is
`e0d47f2790e3f758fa2188926a0bb2f56af6b310`. During preparation the local
Steam Deck build was replaced by an amd64 build of that named revision.
Neither application was executed, modified or assumed binary-identical to
source. Its actual bundled SDL and real runtime remain to be checked during
the separately approved application test.

The [pinned Eden SDL backend](https://git.eden-emu.dev/eden-emu/eden/src/commit/e0d47f2790e3f758fa2188926a0bb2f56af6b310/src/input_common/drivers/sdl_driver.cpp)
uses SDL 3, enables available gyro/accel independently and accepts either in
`HasMotion`. The motion mapping is attached to the chosen gamepad. It converts
SDL rad/s to revolutions/s and maps `(x,y,z)` to `(x,-z,y)`; **do not duplicate
that conversion in our driver**. It uses nanosecond timestamps and supplies
microsecond intervals to its motion stack. Source file SHA256:
`ff6037c3d2cea0f590053f5517672a0f89d4e17f3c58b13fee1076048d49bb82`.

The [motion integration code](https://git.eden-emu.dev/eden-emu/eden/src/commit/e0d47f2790e3f758fa2188926a0bb2f56af6b310/src/hid_core/frontend/motion_input.cpp)
can integrate gyro while skipping unreliable acceleration correction.
Gyro-only output provides no gravity-based drift correction or trustworthy
accelerometer game actions. Eden applies its own thresholds and bias logic;
its perceived response need not exactly reproduce the diagnostic window.
SHA256: `50bef5fe01a7142eb5885c7860939cdbfaac36da806ca5f20c07d87f1d2d5ec5`.

**Reproduced Eden input limitation:** initial SDL events can have zero sensor
time, causing Eden to use host/application time. A later, smaller nonzero
sensor clock is rejected until it catches up. This can affect late hotplug
or enabling motion after the emulator has already been running. The optional
reference-method test reproduces it; we do not claim to have fixed Eden.
For the first test, finish native startup before starting Eden. Broader
hotplug/time-domain handling needs a separately reviewed Eden/SDL fix or
verified newer version, not a GameSir USB reset or artificial gyro scaling.

Eden reference methods are tested only from a private supplied source file.
No Eden GPL-3.0-or-later code, binary or derived test binary is shipped in this
GPL-2.0-only repository/package. There is no Eden patch or application preload.
SDL reference/provenance remains in [the earlier comparison](DUALSENSE_SENSOR_COMPARISON.md).

## Access and installation boundary

The source package now includes a narrow seat-local udev `uaccess` rule for
our exact sensor node name and `gsn-*` association. It grants no raw USB/IIO
access, no broad world-readable input permission and no input-group membership.
Active KDE/Gamescope session ACLs still require live verification. The option
is deliberately absent from the default module/service configuration.

The separately approved first test loaded `experimental_gyro=1` explicitly
after the reviewed package update. No persistent modprobe configuration was
created during that first test. The subsequent separately approved local
persistent opt-in is recorded below; package defaults remain unchanged.
The exact release/install/load/resume steps must use a fresh ownership check.
After reviewing/removing the persistent opt-in, an approved reload with the
option disabled returns to raw-IIO-only behavior.
No Steam or Eden configuration file was edited by the installation procedure.

## Offline verification

- `make test-sensor`: full signed 16-bit profile range, all PID/opt-in gates,
  overflow-safe arithmetic, positive resolution, exact conversion and clock
  pause/fraction/wrap handling; ASan/UBSan.
- The extracted actual input registration/report functions test model gates,
  distinct port/instance associations, allocation/registration failures,
  sensor-only capabilities, unchanged-rate frames, neutralization clock,
  retained paddle and grip-FF capabilities. Fake boundaries are not proof of
  Linux-core concurrency or real udev permissions.
- `make test-sdl`: installed SDL 3.4.18 plus SDL2-compat in audited device-free
  Bubblewrap. Gyro-only discovery, rad/s values, wrong-identity rejection,
  incomplete axes and invalid-resolution negative controls. The new profile
  passes all 32 simultaneous A/paddle combinations with gyro enabled, plus
  the existing independent button/axis/FF suite. No host device is opened.
- Optional `python -B tests/check_eden_motion.py --source <private-sdl_driver.cpp>`:
  exact pinned methods, six signed directions, units, intervals, duplicate/
  backward handling and the time-domain limitation. No emulator execution.
- Full regression suite and current-kernel build are required before commit.
  Evidence is recorded in `build/results/`; raw private source stays ignored.

## End-to-end procedure

1. Fresh package/kernel/device/ownership check; close games and Eden.
2. Review and approve the exact update/option/reload sequence and rollback.
3. Confirm one `GameSir G7 Pro`, its sensor partner, matching nonempty identity
   and session access. Keep current paddle integration intact.
4. Start Eden after native initialization. Select the physical GameSir through
   SDL and its motion source; enable motion if the UI requires it. Avoid a
   virtual Xbox device substituted by a launcher which hides physical sensors.
5. With no time pressure, test gyro directions/aiming, then ordinary inputs and
   each paddle independently and together. All four paddles must
   remain independently recognizable and assignable. Earlier application
   results are not evidence of the new gyro build running in Eden.
6. Close Eden and verify stable normal input. No unapproved reconnect, motor,
   reference-angle calibration or additional stress test.

Success means motion reaches the real emulator, the selected sensitivity is
usable, and existing inputs survive. Offline API/method results alone do not
constitute Eden/game hardware acceptance.

### Recorded result

The full `make test` run completed with 1,023 Python unittest cases plus the
C/protocol/kernel-adapter checks. The separate SDL suite passed 14 sensor
and 18 button/axis/FF scenarios. Kernel build for `7.2.11-1-garuda` has zero
code warnings; its known compiler-environment advisory is Clang 23.1.1
(kernel) versus 23.1.3 (module build). Kernel checkpatch and all five Clang
analyzer translation units passed. [Sanitized result](sdl-eden-gyro-validation.json).

## First local installation and Eden acceptance

The separately approved update installed only `gamesir-native-dkms`
**0.1.0.alpha3-8**, replacing revision 7 on Garuda KDE, kernel
`7.2.11-1-garuda`. The package guard first verified return to `100a/xpad`,
stopped the manager and removed only the unused native module. DKMS, Garuda
snapshot/initramfs hooks and the new udev rule installation completed.
All 103 payload files matched the archive; package verification reported
135 entries and zero alterations. Installed module source version:
`51B1928C25EC5BD2C65C70C`; matching vermagic, no automatic USB aliases.

The immutable tested archive was built from implementation commit `7e49d68`
with package revision increased to 8, before this result documentation:

- Package SHA256: `0277cf2d31921b7ee6dbd112c39071ed51f31b16668eacdaf53e835134acbd9e`.
- Source archive SHA256: `9a3f417827d2bf9b220e0cf51061631ba164cef474c82cee34328c5acf4c7867`.
- Fresh package tests: 25 passed. The preceding full implementation validation
  remains recorded above; it was not unnecessarily repeated after only a
  package-revision/documentation change.

### Interrupted first activation and recovery

A preliminary guard stopped before issuing Resume because the wireless
reconnection changed the device address. The refreshed first actual Resume
was then interrupted by an **incorrect private observation helper**: it
treated any scan/per-port metadata error as immediately fatal instead of
using the existing bounded transition policy. The triggering full status
was not retained, so its exact error text cannot be reconstructed.
The helper issued its authorized one-time Release during the handover;
the kernel recorded `-EINTR` at stage 3. The manager correctly refused to
claim successful return of the unowned new `109c/xpad` instance. This trial
did not validate or disprove the new gyro path.

Under separate permission the user removed the dongle. Read-only checks
confirmed physical absence and empty leases before reinsertion. The fresh
device returned to `100a/xpad` and normal KDE input was confirmed. No forced
rebind, state deletion, repeated Release or automatic retry was used.

The replacement private helper reuses `tools/native/bootstrap_observation.py`
(`StartupWindow` and `wait_for_native`); all **31 existing observation tests**
passed. It retains full status samples, original errors even if cleanup fails,
the fixed deadline, kernel-log checks and exact device/parent/lease/token
attestation. Future test runners must reuse this policy rather than treating
every transient metadata gap as a failed bootstrap.

### Successful separately approved attempt

One new approved Resume completed `100a → 109c`, native handover and kernel
startup state 7 with error/stage zero and both input/IMU evidence. The sensor
and gamepad had the same nonempty session identity. Both event nodes were
accessible through the active user's seat ACL, without world access or raw
USB permissions. The gyro node exposed only `ABS_RX/RY/RZ` plus timestamps;
it did not consume the raw IIO buffer. The familiar xpad teardown `-ENOENT`
message was present; no new BUG/Oops/lockup warning was observed.

Eden was started after native initialization. The user confirmed:

- GameSir is recognized and movement reacts through SDL; the private
  screenshot shows the motion binding `sdl` and enabled motion control.
- Direction and sensitivity match the intended movement.
- In a subsequent explicit confirmation, the user reported that Eden's live
  motion indicator in the controller menu follows the physical controller
  movement as expected. This confirms the live visual response, beyond
  sensor discovery and the static screenshot, and was accepted by the user
  as a positive live test.
- L4, R4, L5 and R5 are each independently assignable; ordinary buttons,
  sticks and triggers continue to work.

Final read-only inspection confirmed active native `109c`, running/enabled
service, no current manager errors, `experimental_gyro=Y`, and both IIO
buffer gates still zero. The service remains active; Eden was left to the
user. No persistent gyro option, extra motor test, firmware command, new
physical calibration or public push was performed.

This is an **Eden controller-configuration acceptance test**, with user-observed
motion and button assignment. No particular game's aiming, prolonged stability,
late hotplug or suspend was tested. No separate mapped SDL shared library was
visible in the inspected Eden process; its bundled SDL version was not independently
identified. The earlier source/time-domain limitations and gyro-only scope remain.

## Persistent opt-in installed after acceptance

This section records the earlier gyro-only creation under revision 8. On
19 October a separate file-only approval updated the same file to the accepted
six-axis profile under revision 9. Exact bytes/rights/effective options and
unchanged running module/service were verified. The current content, hashes,
saved gyro-only rollback and remaining reboot limits are in
[the persistence update](STEAM_ACCEL_EXTENSION.md#eden-follow-up-and-approved-persistence-update).
The earlier initramfs inspection below predates the revision-9 package hooks;
it is not a fresh inspection of those rebuilt images. No image rebuild was
part of the later file-only update.

The maintainer separately approved the read-only checks and creation of
exactly one persistent configuration file. **The local opt-in is installed
and verified; a real reboot test remains pending.** No service restart,
module reload, new binding, application change or reboot was performed.
Fresh checks found revision 8, the expected loaded/installed
module source version, active/enabled service, paired accessible sensor/gamepad
nodes, no service drop-in, no conflicting module options and no early-load
entry in readable modules-load/dracut configuration or the kernel command line.

The sole system configuration change is the new root-owned, mode-0644 file
`/etc/modprobe.d/90-gamesir-native-gyro.conf`, with these exact contents:

```conf
# GameSir G7 Pro: explicitly enabled experimental SDL gyro profile.
options gs_native experimental_gyro=1
```

The existing service already calls modprobe during startup, so it will combine
this option with its bootstrap/output/persistent-runtime options. A device-free
`modprobe -C <prepared-file> --show-depends gs_native bootstrap_mode=1
enable_output=1 persistent_mode=1` confirmed that combination without loading
anything. The current module already has the test option; writing the file
does not require a release, reload, rebind, service restart or daemon-reload.

The approved checks confirmed an active/unpaused manager without current
errors and running experimental_gyro=Y. The normal initramfs contains no
gs_native module. The fallback image includes the module, but inspection of
its aliases, dependencies, module-load/configuration files, units, udev rules
and dracut hooks found only its own dependency record: no automatic native
load path. The two inspections covered 157 and 182 text files respectively.
Neither image was rebuilt. Future early-load/configuration changes need a
fresh review; module presence alone is not evidence of early loading.

The destination was absent immediately before installation. Its exact bytes,
root:root ownership, 0644 mode and SHA256 were verified:
`5960ba3dff0e568341f88040162b81ebfa522f50e42662b11667925878767d51`.
The normal modprobe dependency listing now includes experimental_gyro=1
alongside all three service options;
the effective configuration has exactly one native options line. These were
read-only listings, not module loads. The service PID, loaded source version,
USB identity/binding and paired accessible event nodes were unchanged before
and after; final manager state remained healthy and both IIO buffer gates zero.
Private command outputs and before/after metadata are retained with checksums.

Rollback removes only this added file after verifying its identity/content;
the currently loaded option remains until a separately approved reload/reboot.
This local opt-in survives ordinary package updates but must also be removed
when opting out or uninstalling the driver. It is not a new package default.

Actual boot acceptance remains a separate user-led restart: confirm module
option, active/unpaused manager and paired readable event nodes, then start
Eden after native initialization. Retain the documented late-start/time-domain
limitation; persistent configuration alone does not resolve it or prove boot
behavior. No calibration, application configuration or additional hardware
test was part of this persistent-configuration change.

## Eden through Steam in Gamescope: per-shortcut filter fix

On 19 October 2026, a separately authorized test on the CachyOS Gaming Mode
system confirmed a launch-environment problem distinct from the outstanding
Steam gyro display/hotplug investigation.

Before the correction, the actual Eden process inherited
`SDL_GAMECONTROLLER_IGNORE_DEVICES` with the physical GameSir VID/PID in its
exclusion list. It opened only Steam's virtual Xbox input node, and its log
reported `accel=false gyro=false`. Neither the stored desktop launcher nor
the Steam shortcut's original launch options contained that filter. These
observations locate the exclusion in the Steam-launched process environment;
they do not identify the exact internal setter or prove Gear Lever added it.
The precise Steam Input override state was not independently established.

### Scoped correction and rollback

The original Steam shortcut database and Eden desktop entry were backed up
privately, with hashes verified before changing the shortcut. Steam remained
running, so the maintainer edited Eden's launch options through Steam's UI
instead of externally overwriting its binary shortcut database.

For this particular non-Steam shortcut, **the executable was already `env`**.
Its launch options were prefixed with:

```text
-u SDL_GAMECONTROLLER_IGNORE_DEVICES -u SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT
```

The original environment assignment and quoted AppImage path remained after
those options. This prefix is not a complete launch command or a universal
`%command%` recipe: inspect the shortcut's actual executable and arguments
first. Only Eden's child environment is affected. Preserve
`SDL_GAMECONTROLLERCONFIG`, which supplies the existing paddle mapping;
do not clear all SDL variables or modify the session-wide Steam environment.

Comparison of all parsed shortcut entries confirmed the intended launch-option
change and only an additional last-played timestamp. The desktop entry and
other shortcut settings were unchanged. Rollback is to restore **only Eden's
original launch options** through Steam properties and restart Eden normally.
Do not replace the whole database over unrelated later edits.

### Observed result and limits

- Two local synthetic child-process checks confirmed that `env -u` removes
  both filters whether present or absent, while preserving the paddle mapping
  and other selected environment values. No vendor application or device was
  used for these checks.
- After the approved Eden launch, its process environment contained neither
  exclusion filter; the existing paddle mapping was unchanged.
- Eden opened the paired physical `GameSir G7 Pro` and `GameSir G7 Pro Motion
  Sensors` input nodes. Its new log reported `accel=true gyro=true`.
- Steam's virtual Xbox input remained available as well. The maintainer
  selected the **physical GameSir** in Eden and confirmed matching motion
  without holding Guide, independent assignment of all four paddles,
  simultaneous press/release behavior and normal buttons/sticks/triggers
  without duplicate inputs.

This is an accepted Eden controller-settings test through Steam in Gamescope,
not a new gyro-scale calibration, extended gameplay or reconnect test. It
does not resolve or explain Steam's own Guide-dependent gyro display and late
device-arrival behavior. No driver/module/service, global Steam configuration,
firmware or system package was changed for this correction. Private backups,
host/user paths and raw process metadata remain outside Git. Calibration stays
paused; no push or additional release is authorized by this test.
