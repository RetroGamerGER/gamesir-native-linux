# Steam gyro: optional real acceleration extension

19 October 2026. **Revision 9 activated under separate approval; Steam gyro
UI accepted in the controlled run.** The user reports all three gyro values
respond and normal inputs plus all four independent paddles still work.
This is UI acceptance, not a particular Proton game's gyro acceptance or
complete physical calibration. No Steam library/configuration was modified.

The running experimental profile is gyro 0.07 dps/raw, acceleration 8192
counts/g and explicit accel map 1,2,3. Acceleration is not enabled by package
default. The separately approved local persistent profile is now installed
and verified without reloading the module or restarting the service.
Earlier gyro-only Eden acceptance remains recorded separately. The user
subsequently reports that Eden continues working with this profile; no new
per-axis measurements were reported. Actual reboot/lifecycle acceptance
remains pending. Gyro calibration remains paused.

Implementation, preparation, installation and intermediate stopped checks
below retain their original stages and limits. The later approved activation
and [sanitized result](evidence/STEAM_ACCEL_ACTIVATION_20261019.json) supersede
the earlier not-yet-activated status, not those evidence limits.

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

### User-driven service start and Resume follow-up

The maintainer subsequently reported starting the service, then confirmed that
both service start **and Resume** had been run. The agent issued neither action.
Read-only checks show active/enabled service and the expected loaded revision-9
module, with gyro Y but acceleration N/no explicit acceleration map. The
manager is unpaused, with no scan/port errors, empty leases and managed devices,
and no native bindings. The dongle remains 109c/xpad.

The first read guard expected pause and failed; its report remains unchanged.
The user's subsequent confirmation explains that mismatch; it is not evidence
of a spontaneous manager unpause. Discovery starts only 100a/experimental105e
sources and deliberately does not adopt an unowned 109c instance. Hence service
activity alone proves neither native takeover nor the new acceleration profile.
Pause and the actual experimental profile reload/fresh 100a bootstrap still
need concrete approval. No extra agent Start/Resume/Release, USB command or
Steam test followed this read-only check.

## Approved profile activation and Steam UI acceptance

A fresh read saw native ownership again after the user's prior Resume and
reconnection. The separately approved Release validated current idle managed
ownership, ran once and confirmed pause, empty leases, no native bindings and
100a/xpad. No old device address or prior unowned-109c assumption was reused
as ownership proof.

The next explicit approval covered four successful, one-time operations:
service stop, removal of only unbound/zero-reference gs_native, reload with
experimental_gyro=1, experimental_accel=1, accel_axis_map=1,2,3 and 8192/1
counts/g, then paused service start. The old persistent gyro file was unchanged.
That stage left 100a/xpad unchanged and did not issue Resume.

A further approval authorized one Resume with read-only startup monitoring
and one Release only on error. The existing StartupWindow/wait_for_native
policy (31 offline regressions passed) observed 100a to 109c and attested the
new same-parent instance, active manager lease and kernel ownership tokens.
The kernel bootstrap finished with error 0/failed stage 0 and positive pad/IMU
stream evidence. No error Release or retry was used. The journal retains the
known xpad detach -ENOENT message, not a new kernel fault or failed bootstrap.

Sysfs-only checks confirmed paired nonempty identities, standard 109c,
ABS_X/Y/Z/RX/RY/RZ capability mask 0x3f and active-user read access. This
metadata checker opened no input/IIO/USB device and did not read EVIOCGABS
resolution or capture sensor values. Expected units remain grounded in the
loaded profile/code and earlier offline SDL tests.

Only after attestation did the user start Steam normally. The user confirms:
all three gyro rates respond to the corresponding rotations, ordinary
buttons/sticks/triggers work, and all four paddles remain independent. This
resolves the formerly all-zero UI in this run with real acceleration present.
No calibration button, motor pulse, Proton-game gyro test, Steam memory
observation or Steam binary-identity recheck was part of the acceptance.

This strengthens the contract-mismatch explanation without claiming that
every historical failed gate or every Steam build has been measured. The
qualitative acceleration map and scale remain experimental. Six-axis Eden,
reboot/persistent opt-in, lifecycle and shared output acceptance remain
separate; earlier gyro-only Eden/FF/bridge evidence must not be relabelled
as new combined hardware acceptance. [Activation record](evidence/STEAM_ACCEL_ACTIVATION_20261019.json).

## Eden follow-up and approved persistence update

After the successful Steam UI test, the maintainer reports: “Eden funktioniert
auch weiterhin”. Record this as continued functional operation with the current
profile. It does not supply new axis-by-axis values, button assignment results,
calibration or long-duration/lifecycle evidence. No extra agent-driven hardware
test was started and no further gyro calibration is required by this feedback.

The separately approved local-only persistence change updated the existing
`/etc/modprobe.d/90-gamesir-native-gyro.conf` to the following exact content:

```conf
# GameSir G7 Pro: explicitly enabled experimental SDL motion profile.
# Gyro 0.07 dps/raw; experimental accel axes 1,2,3 and 8192 LSB/g.
options gs_native experimental_gyro=1 experimental_accel=1 accel_axis_map=1,2,3 accel_counts_per_g_num=8192 accel_counts_per_g_den=1
```

The installed file SHA256 is
`9d95386466a13e641a7b1ee579cbf11d01715732668a50efa95d2157b17229c2`.
The previous file SHA256 was
`5960ba3dff0e568341f88040162b81ebfa522f50e42662b11667925878767d51`.
The old content is retained privately for a concrete rollback.
A device-free `modprobe -C <candidate> --show-depends gs_native bootstrap_mode=1
enable_output=1 persistent_mode=1` shows all profile and service options
combined correctly. After installation the ordinary system listing also
combines all these values, and `modprobe -c` has exactly one native options
line with the six-axis profile. These commands print configuration only.
No module install/softdep override or service drop-in was found. Readable
module-load/dracut configuration and the kernel command line contain no
explicit gs_native early-load entry.

**Installed and read-only verified:** the password-approved helper validated
the original regular root-owned file/hash and active profile before exactly
one file installation. Exact bytes/hash, root:root ownership, mode 0644 and
effective options passed. Before/after service PID/state, module instance,
source version and all module parameters match. The current running profile
already had these values; this file update did not change it. Private evidence
and the saved old file passed SHA256 verification.

No reload, Release/Resume, service restart, initramfs rebuild or reboot was
performed. Actual next-boot and fallback-image behavior remain acceptance
work, not a guarantee from the configuration listing. Package defaults remain
off. Reverting only this acceleration opt-in would restore the saved previous
gyro-only content after fresh checks and separate approval; it would not
change the running module until a separately approved reload/reboot.

## Read-only CachyOS/Gamescope transfer assessment

On 19 October an unprivileged SSH inspection found the CachyOS/Gamescope test
host on `7.2.9-2-cachyos-deckify`, matching kernel/header packages `7.2.9-2`,
DKMS 3.4.4-2 and core revision 6. The installed core passes its package check
(127 entries, zero alterations). It has neither the new gyro/acceleration
parameters nor the new sensor udev rule or local motion opt-in. Copying only
the modprobe profile onto revision 6 would therefore be incorrect.

The same reviewed **revision-9 DKMS source package** and explicit experimental
profile above are transfer candidates; no CachyOS-specific source patch was
identified. Prepared headers and required GCC tools exist. The unchanged build
planner selects GCC and the matching kernel in dry-run mode. Required input
APIs are present (the resolution setter is macro-generated); the packaged
userspace client's five GLIBC version requirements are available. This was
**not a revision-9 kernel build**. Do not copy the Garuda-built `.ko`.

The installed manager, removal guard, system service, compiler planner,
Steam entrypoint and Gamescope wrapper/drop-in match current source hashes.
Steam integration `0.1.0.alpha2-1` and Gamescope `0.1.0.alpha1-1` pass package
checks (17/15 entries, zero alterations). The expected drop-in is active in
`steam-launcher.service`, with an active seat0 session. All three stored Steam
SDL3 libraries have the hashes already examined in our offline reference.
No Steam integration replacement or downgrade is indicated by these checks.
Library identity alone does not prove live sensor access or UI acceptance.

Next, under separate authorization: build revision 9 for the target kernel,
verify fresh ownership and the safe release/update path, then install only the
reviewed core update. The target's absent opt-in file would be **created** with
the same content after fresh checks, rather than updating an existing gyro-only
file. Approval must cover later activation and actual sensor-node/session ACL,
Steam/Eden/paddle regression and lifecycle checks as appropriate.

No GameSir USB device was visible during this inspection. Protected module
parameters and manager ownership were not available to the ordinary SSH user;
no privilege escalation or claim of a safe update-ready ownership state was
made. The active/enabled service retained its PID and zero restarts, and the
loaded source version stayed unchanged. No build, installation, file write on
the target, module/service action, device open or hardware test occurred.
[Sanitized assessment](evidence/STEAM_ACCEL_ACTIVATION_20261019.json).

## CachyOS revision-9 installation: passed, activation pending

The subsequent installation request first completed the real unprivileged
GCC build for `7.2.9-2-cachyos-deckify`: zero warnings, matching vermagic and
no automatic USB aliases. The reviewed revision-9 package, prior revision-6
rollback archive and exact local motion profile were copied over SSH with
verified hashes. No module was loaded by that build or transfer.

The first privileged precheck stopped before calling pacman or installing
the configuration: a GameSir device had appeared after the earlier no-device
baseline. The user confirmed connection. Preserve that stopped report;
it is not evidence of a new driver defect. A subsequent read-only manager
inspection confirmed one healthy active native instance and its matching
lease. Older resolved failure records remained historical context.

The maintainer separately approved exactly one new connected-device update
with its controlled return, package hooks and motion configuration. The
upgrade hook verified release, stopped the service and removed the unused
module. Pacman updated **only gamesir-native-dkms, revision 6 to 9**, exiting
0. DKMS installed for the matching CachyOS kernel. Its actual make log has
zero warnings/errors; the known deprecated DKMS CLEAN advisory is separate.
The distribution's initcpio generation, Limine update and pre/post snapshots
completed. No kernel package upgrade or manually requested reboot occurred.

Verification matched all **111 regular payload files**, 143 package entries
with zero alterations, source version `DF7D42B1E7909084ED9BEB1`, matching
vermagic and no autoload aliases. The new root:root/0644 motion config has
SHA256 `9d95386466a13e641a7b1ee579cbf11d01715732668a50efa95d2157b17229c2`,
byte-identical to the accepted opt-in on the other test host. Ordinary
modprobe listings combine its profile with all service options without a load.
Package defaults stay off. Steam/Gamescope packages and integration hashes
remain unchanged; their 17/15-entry checks report zero alterations. No Steam
restart was performed.

Final checked state: **100a/xpad**, no native binding or loaded native module,
empty leases, saved pause true, service inactive/dead with successful exit,
existing autostart enablement retained. All six older failure records remain.
This confirms the return state, not a new physical input-function test.
No post-update service start, Resume, sensor or game test followed. Actual
Gamescope sensor ACL/stream/UI acceptance, reboot and lifecycle behavior still
require their separately approved steps. Gyro calibration remains paused.
[Sanitized installation record](evidence/STEAM_ACCEL_ACTIVATION_20261019.json).
