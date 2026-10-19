# Steam gyro: real acceleration extension (offline preparation)

19 October 2026. **Revision 9 installed under separate approval; not activated.**
The implementation/test sections below record the preceding offline preparation.
This prepares a correction for the [statically identified acceleration
notification gate](STEAM_GYRO_DOWNSTREAM.md#notification-gate-follow-up).
It does not establish Steam Input/gameplay acceptance or prove every gate in
Steam's historical live run. No Steam library or configuration is modified. The later approved package
installation is recorded below; the new module remains unloaded. Gyro
calibration remains paused.

## Contract

Keep the accepted `experimental_gyro=1` standard-109c path and its gyro
conversion unchanged. A **separate default-off** `experimental_accel=1` option
adds ABS_X/Y/Z to the same paired motion evdev node. All six values come from
one accepted IMU report, use one host receive timestamp, one MSC_TIMESTAMP
and one SYN_REPORT. There is still one USB owner, no extra reader, no IIO
buffer activation and no new USB or sensor configuration command.

Acceleration is actual signed wire data, with an explicit signed permutation:
`accel_axis_map` contains exactly three distinct signed 1-based axis selectors
for SDL X, Y, Z. `1` selects A0, `-2` selects negative A1, etc. The default
`0,0,0` is deliberately invalid when acceleration is enabled. The kernel
rejects unset/partial/duplicate/out-of-range maps and activation without gyro
**before usb_register**. No identity map or gyro-derived map is chosen.
The options are read-only after module load; there is no live map switch.

The existing replaceable experimental scale `accel_counts_per_g_num/den`
supplies the evdev counts/g resolution (default 8192/1). This extension
requires a positive integral quotient; non-integral rational resolutions
are rejected rather than rounded. Raw IIO conversion still supports its
existing rational scales. Signed permutation uses s32, including negation
of -32768 to +32768; evdev bounds include both. SDL converts these counts
using 9.80665 m/s² per g. The independent gyro factor remains 0.07 dps/raw.
Neither API returns verified-calibration status for this experiment.

Lifecycle neutralization reports zero angular velocity and pauses the sensor
clock as before. It sends **no new acceleration sample**; the last real
acceleration remains cached by evdev. It does not fabricate zero gravity,
repeat a made-up stationary vector, or bypass a Steam readiness check.
Consumers may observe retained acceleration when receiving that final sync;
it is not a new physical reading. Disconnect still removes the node.

## Remaining axis evidence and activation gate

Our six qualitative movement recordings establish gyro directions, not a
complete accelerometer frame. A0/A1/A2 must not automatically inherit G0/G1/G2.
The new tests use `-3,1,-2` only as an **artificial permutation**, not as a
proposed hardware setting. The stored packet excerpt tests transport and
units but does not establish which direction gravity acts in on the device.

Before preparing an actual activation command, confirm the accelerometer
frame using existing evidence tied to known stationary poses, or obtain
separate permission for a short gravity-orientation check. This does not
require precise 90° gyro rotations, a new gyro factor or known-angle integration.
Keep the package and current installed path gyro-only until that mapping and
a separate installation/test approval exist. There is no ready-to-run module
load example with a guessed axis map in this document.

A later approved test must check actual acceleration at rest, nonzero and
correctly oriented movement in SDL, Steam gyro display/calibration behavior,
Eden motion and independently assignable paddles, normal inputs and output
ownership. Keep existing stop/reconnect/suspend regression and fallback rules.
A static nonzero-acceleration gate alone does not prove fusion will accept
incorrect units/axes or that a particular Proton game will use gyro.

## Update preparation and independent axis evidence

A later request prepares package revision **0.1.0.alpha3-9** for installation;
no installation or activation is recorded here. Re-examining the **existing**
known-direction captures provides a test candidate without assuming that
accelerometer and gyro share a frame. The original statement above records
the evidence limit before this additional analysis; a full six-pose calibration
is still absent.

Capture and parent SHA256 sets were verified. Each capture retains its own
instance; none is merged into a fictitious continuous session. After excluding
the first ten seconds of the movement window, select samples with all three
absolute gyro counts below ten. These are low-angular-rate observations during
the instructed held tilt, not proof of zero translation or measured pose angle.

| Human movement / held pose | Selected samples | Median A0, A1, A2 |
| --- | ---: | --- |
| Front edge down | 83 | -313, -3602, 6044 |
| Front edge up | 215 | 77, 999, -9492 |
| Left grip down | 65 | 8253, -1153, -1594 |
| Right grip down | 243 | -8006, -340, -2214 |

The instructed face-up starting rests all have dominant positive A1 (about
8230 counts). With SDL +X right, +Y up/out of the face, +Z toward the player,
the opposite held tilts independently support **SDL acceleration = (A0,A1,A2)**:
left grip down makes +X point upward; front edge down makes +Z point upward.
This supports explicit **`accel_axis_map=1,2,3` for a supervised experiment**.
It is not derived from gyro axes, and not a certified calibration or automatic
package default. [Sanitized evidence and limitations](steam-accel-held-pose-evidence.json).
The earlier `-3,1,-2` test permutation remains synthetic only.

A controlled activation may therefore propose the evidence-backed candidate
instead of demanding a new precision-angle experiment. It still needs an
explicit approval covering the actual module/configuration change and
subsequent acceptance; no root operation follows automatically. Keep
`experimental_accel` off by default and preserve the existing gyro-only
configuration until that approval. No gyro scale change is proposed.

### Prepared update sequence (permission gates retained)

1. Inspect current manager ownership, USB identity and installed package/DKMS.
2. Obtain approval for one release and verify returned 100a/xpad or verified
   physical absence. A lingering 109c/xpad instance is not a proved mode return.
   Stop on a failed return; no automatic replug or repeat.
3. Review revision-9 package hash, contents and the retained revision-8 rollback
   archive. Obtain approval for the exact package transaction and its hooks:
   safe-return guard, service stop, unload only unused gs_native, DKMS rebuild,
   systemd metadata and distribution snapshot/initramfs hooks. Preserve local
   gyro options; do not resume automatically after installation.
4. Separately approve the temporary acceleration profile and new module load,
   paused service start and one native Resume with a bounded error-release.
   Use the existing startup observer, not a new fatal-on-transient helper.
5. Verify paired sensors, real acceleration and gyro, then user-guided Steam
   gyro/Eden/paddle tests. No motor pulses or stored controller settings.
6. For rollback remove only the newly approved accel override, release safely,
   and reload the accepted gyro-only profile or install the saved revision-8
   archive with its own approval. Never claim successful return from binding
   alone. No persistence change, reboot or release/push follows from this plan.

## Reproduction (offline only)

```sh
make test
make test-sdl
make kernel
python -B scripts/analyze_kernel.py
python -B tests/run_sdl_sensor_test.py \
  --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0 --check-steam-layout
```

The last command requires the already reviewed stored SDL hash; it executes
SDL in the audited device-free Bubblewrap test, **not Steam**. No devices,
Steam process memory, sudo, network, preload into Steam or user settings are
part of these checks.

Pure conversion tests cover all 48 signed permutations, signed endpoints,
null/invalid metadata, integral/rational resolution and unchanged outputs on
failure. Extracted actual adapters test opt-in validation, gyro-only behavior,
six-axis registration/emission, shared timestamp and single sync, neutralization,
paired identity, independent FF and all paddle capabilities. The IIO harness
checks the actual producer passes the same six values/time to motion and IIO.

The new `experimental-six-axis` SDL case replays the existing reviewed small
IMU excerpt through the actual conversion functions with the artificial map.
SDL2/3 must expose both sensors with expected physical units; SDL3 events must
share sensor time. Both API tests retain all 32 A/paddle button combinations.
The original gyro-only case and Steam sensor-enable/cache-layout checks remain.
These are device-free integration tests, not live E2E acceptance.

Results and build limitations: [offline validation](steam-accel-extension-validation.json).

## Approved revision-9 installation result

The maintainer separately approved one Release, its return checks, and then
exactly the revision-9 package transaction including password entry and hooks.
Release confirmed pause, empty leases and 100a/xpad. A fresh preinstall guard
reconfirmed those conditions, zero module references, the current headers,
revision-8 installation and pinned package SHA256 before invoking pacman.

The one-package update from 0.1.0.alpha3-8 to **0.1.0.alpha3-9** exited 0.
The installed guard verified safe return, stopped the service and removed only
the unused native module. DKMS rebuilt/installed for `7.2.11-1-garuda` with
source version `DF7D42B1E7909084ED9BEB1`, matching vermagic and no autoload
aliases. Normal/fallback dracut images and pre/post snapshots completed.
The existing Clang-version advisory (23.1.1 versus 23.1.3) and deprecated DKMS
CLEAN feature were reported; the module build exited 0 with no code warnings.
`pacman -Qkk` reports 143 entries and zero alterations. The existing local
gyro configuration hash is unchanged; no acceleration override was created.

**Postcheck stopped before activation:** the USB device had re-enumerated
from 100a/xpad to a new 109c/xpad instance at the same port. The user reports
that the controller switched itself off due to inactivity. This is temporal
context, not a proved cause of that exact enumeration. The guard preserved
its failed report and stopped before its additional custom payload comparison;
the independent pacman integrity check had already passed. No automatic
retry, repair, extra Release, module load or Resume followed.

The checked final state is inactive/dead service with successful exit,
autostart still enabled, persistent pause true, empty leases, no native
bindings and no loaded gs_native. A 109c/xpad binding is **not** a confirmed
return to 100a or a native-runtime test. Next activation requires a fresh
state check and explicit approval. Gyro calibration remains paused; no Steam,
Eden, paddle, motor or reboot test was performed by this transaction.

Package SHA256: `74994d3e19ae0d7a8c5f9b9758885c6656153b3a0c14c6cf9b404289c262f503`.
[Sanitized installation/check record](evidence/STEAM_ACCEL_INSTALL_20261019.json).
