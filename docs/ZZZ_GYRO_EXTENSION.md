# Experimental ZZZ motion profile — revision 17

Prepared offline, then installed after approval on the secondary CachyOS host
on 21 October 2026. The subsequently approved activation and qualitative
Steam/Gamescope input/motion test passed; see
[acceptance evidence](evidence/ZZZ_GYRO_ACCEPTANCE_20261021.json).
The public release remains PRE-ALPHA.3/core revision16. See the
[installation receipt](evidence/ZZZ_GYRO_INSTALLATION_20261021.json); the
standard/main host remains on revision16.

## Finding and scope

The read-only secondary-host diagnosis found core alpha3-16 and the optional
Steam/Gamescope integration installed. Earlier-boot logs showed successful
native `3537:105e` startup (bootstrap result 0, failed_stage 0). The controller
was off during the current inspection; no live sensor stream was measured.
Source review found that conversion, evdev registration, paired identity,
deferred gamepad publication and the manager's readiness dispatch all limited
motion to `109c`. A saved standard-model configuration cannot override that.

Revision 17 adds a separately opted-in `105e` candidate to the **same module
and manager**. The primary switch `experimental_gyro=1` keeps its old meaning
for `109c`. ZZZ additionally requires `experimental_gyro_105e=1` (default off,
read-only module parameter). Neither `100a`, receiver-off `0575`, `1022` nor
other PIDs gain sensors. There is no new USB request, firmware command, PID
spoofing or sensor-setting write. The standard profile remains unchanged.

## Candidate units and association

- Gyro: SDL `(G0,G1,G2)`, `7 * raw`, resolution 100 counts/(degree/s), hence
  **0.07 degree/s per raw count**, signed endpoints -229376 through 229369.
- Acceleration: separately opt-in real reports, explicit signed axis map and
  integral counts/g. The planned trial reuses `1,2,3` and 8192 counts/g.
- These values/directions are a **ZZZ test hypothesis**, not measured ZZZ
  calibration. Raw six-axis IIO samples remain unchanged. No display gain,
  bias subtraction or guessed Sony calibration is introduced.
- Real USB vendor/product/version and per-binding `uniq` pair the gamepad
  and sensor. Concurrent dongles and replacement lifetimes remain distinct.
- With persistent mode, deferred input and both sensor opt-ins, register the
  sensor first, then publish the gamepad only through the existing exact
  token/binding, processed-udev and seat-access checks. The manager reads
  the loaded ZZZ flag; older modules or an absent/disabled flag retain the
  original immediate `105e` gamepad path. Deadlines/first-error retention,
  STOP/PM guards and one-shot publication are unchanged.
- Existing direct `105e` bootstrap/return-to-xpad, `100a`→`109c` startup, receiver
  waiting, FF, four motor channels and paddle mapping are not redesigned.

## Offline checks

The pure conversion suite exhausts all 65,536 PIDs and four opt-in combinations;
it checks both signed full ranges, invalid pointers and unchanged error output.
Actual extracted kernel adapters run the existing registration, emission,
Guide-independence, allocation-error, publication and held-input replay cases
for `109c` with/without the new flag and `105e` with it.192 model/option combinations
and simultaneous mixed-model pairing are checked under ASan/UBSan.

The manager's complete readiness/failure suite also runs through direct `105e`
startup. A 24-combination synthetic module-parameter test covers default/legacy
handling; an unopted ZZZ remains immediate. The original109c-only manager gate
failed 13 of these ZZZ cases before correction. The full manager/reconnect,
startup, FF and package tests remain part of `make test`.

`make test-sdl` uses device-free namespaces, synthetic evdev reports and real
local SDL2/SDL3 libraries. 32 sensor cases cover both identities, wrong/missing
pairing, units/timestamps, 32 paddle/A-button combinations and Guide-independent
updates. ZZZ report values are synthetic (standard-model fixture bytes), not a
new ZZZ capture. Passing these tests does not establish game/hardware behavior.
See [validation receipt](evidence/ZZZ_GYRO_OFFLINE_20261021.json).

## Deployment preparation and approved installation

The candidate is `gamesir-native-dkms 0.1.0.alpha3-17`. It packages the updated
module **sources**, manager and existing hooks, with receiver_wait=1 as before.
DKMS builds for the target's matching kernel headers; a local Garuda `.ko`
must never be installed on CachyOS. The new ZZZ opt-in is not installed by the
package and the signed public update catalog is not changed.

For a separately approved trial, retain the existing reviewed standard sensor
configuration and add only this extra local override after backing up any
existing file at the chosen path:

```conf
# Experimental ZZZ profile: scale/axes not yet validated on this edition.
options gs_native experimental_gyro_105e=1
```

Proposed path: `/etc/modprobe.d/92-gamesir-native-zzz-gyro.conf`. It complements
`experimental_gyro=1 experimental_accel=1 accel_axis_map=1,2,3
accel_counts_per_g_num=8192 accel_counts_per_g_den=1`; it does not replace the
existing standard profile. It takes effect only on the next authorized module
load. Do not reload a module while a managed controller is still active.

The approved update completed after target kernel/header/application/ownership
checks and a warning-free CachyOS build. The old module was safely unloaded by
the package hook; revision16 is retained for rollback. Existing90/91 configs
were preserved and only the previously absent92 config was added. Service start,
Resume and hardware testing were not part of that installation transaction.
The subsequent approved activation/test is described below. No automatic
retries or firmware actions occurred.

Rollback: remove only the newly added override, or restore its exact previous
backup, then use the existing controlled release/update procedure to restore
revision 16 if needed. Preserve the standard gyro config, user mappings and
other controllers. Removing a config file does not change the already-loaded
module; verification/reload/restart remains a separate approved action.

## Approved ZZZ Steam/Gamescope test

On the same CachyOS host, one service start and one Resume loaded the 105e opt-in.
Steam was already running before the ZZZ was switched on. Direct 105e startup
succeeded (bootstrap error 0, failed_stage 0, pad/IMU present, no handover), and
the manager confirmed exact input publication. Gamepad and sensor shared the
native per-binding identity while retaining the real 3537:105e device IDs.

The maintainer confirmed all three Steam gyro axes respond appropriately without
holding Guide, four independent paddles and normal buttons/sticks/triggers,
including simultaneous presses/releases, with a responsive desktop. This accepts
qualitative functionality with the candidate profile; no known-angle integration,
six-position acceleration or motor test was performed in this run. The maintainer
subsequently confirmed gyro also works in Eden, and both Eden and Steam displays
match physical controller movements. This follow-up is user-reported; no further
agent-run capture or system change accompanied the documentation update.

The kernel journal records the sensor about 1.15 seconds before the gamepad.
The extension applies the existing readiness gate to 105e, so this is consistent
with the intended sensor-before-gamepad discovery. Direct 105e also avoids the
standard 100a-to109c identity transition in this run. These are observed differences,
not a controlled proof that either alone fixes Steam hotplug. Earlier Steam
zero-display cases also do not establish a universal requirement to power the
controller before Steam. Long-off/reconnection behavior remains open.

## Separate unresolved report

The maintainer reports failure to bind after a long controller-off interval
and sometimes missing ordinary buttons after reconnect until a PC restart.
Duration, exact device/runtime state and failing buttons are not yet recorded;
this symptom has not been reproduced or diagnosed in this offline change.
**Revision 17 is not a reconnect or partial-input fix.** Investigate those
lifecycle failures as the next task; do not silently clear manager history,
restart services, or weaken ownership guards to make a sensor test pass.
Precise known-angle gyro calibration remains paused.
