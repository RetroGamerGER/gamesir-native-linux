# Public pre-alpha release audit

## PRE-ALPHA.3 package/default and function audit — 20 October 2026

The maintainer explicitly requests integrating the accepted receiver-wait
configuration into installation, updating README, pushing the reviewed full
source and creating a tagged PRE-ALPHA release. Revision16 ships the same-name
vendor configuration under `/usr/lib/modprobe.d/`, mode0644. Existing `/etc`
overrides remain user-owned and higher priority; core removal removes its own
vendor file. Service enable/start/Resume, gyro opt-in and running hardware are
not changed by preparing or publishing these source files.

The [functional/commit review](FUNCTIONAL_INTEGRATION_AUDIT.md) maps the existing
startup/reconnect, input/paddle, IIO/SDL motion, rumble/haptics, trigger adapter,
Steam/Gamescope and safe-removal implementations to package contents and tests.
No missing operational runtime fix was identified. Kernel/core/manager/client
hashes still match the accepted revision15 implementation; revision16 changes
packaging policy and documentation. Complete `make test` passes: **1,339 Python
cases in46 groups**, plus the C/actual-kernel-adapter/sanitizer/client suites.
The extended package test parses the staged configuration with `modprobe -c`
without loading a module and preserves no `/etc` ownership/service forcing.
The local `7.2.11-1-garuda` module builds with zero code warnings; the retained
Kbuild advisory is header Clang23.1.1 versus installed Clang23.1.3. The earlier
matching CachyOS build/accepted scoped hardware results remain separate evidence.

The43 unpublished development commits were reviewed for feature provenance and
public identity. Three subjects contain internal machine labels. Preserve those
commits privately; publish one exact reviewed final-tree snapshot with the
existing audited public `main` as parent. Compare its complete tree before any
push. This preserves every source feature and public history without publishing
those intermediate metadata labels. No public force push or private raw source
history is intended. Current tracked source has no candidate private machine/
home/IP/key material; new source/configuration/documents are reviewed as well.

Assets remain source-only: full audited repository source, core and optional
Steam/Gamescope/trigger-bridge build inputs with recipes, release notes and
checksums. No local `.BUILDINFO`, binary package, raw USB capture, manufacturer
app/firmware, credentials or private run directory belongs in public assets.
The tag is `v0.1.0-pre-alpha.3` and component versions are listed in its
[release notes](RELEASE_PRE_ALPHA_3.md). Publication is performed only after the
frozen archive/package/manifest checks; source publication is not another
installation or hardware acceptance.

## Revision 15 automatic binding accepted — 20 October 2026

Following the successful scoped late-power-on test, the maintainer explicitly
accepts the present state: the controller binds automatically without manual
intervention, and the reported brief initial xpad contact is acceptable and
**not a blocker**. The proposed explanation of a short SteamOS reaction remains
unconfirmed. Preserve the measured sequence and its limits below; this decision
neither proves xpad independence nor supplies missing cold-boot/reconnect or
application tests. First-probe research is optional follow-up, not required
rework for this accepted checkpoint. No additional live access/system change,
source push, tag or release was performed or authorized by this acceptance.

## Revision 15 late power-on starts automatically — 20 October 2026

After the receiver-only waiting check, the maintainer explicitly approved one
controller power-on on cue and read-only monitoring, with no other buttons or
stick movements and a stop on error. Fresh protected preflight reattested the
same waiting receiver lifetime/tokens, module flags, service and ownership.
The observer reported armed before the power-on cue. The maintainer confirms
one power-on and no additional inputs.

Twenty-seven read-only snapshots show the waiting `109c` lifetime, then a new
`100a` instance already on gs_native in the sampled `checking_start` and
`bootstrapping` phases. A later sample sees the normal disappearance during
that bootstrap, followed by an attested new `109c`/gs_native instance. Its
kernel result is `state=7 error=0 failed_stage=0 pad=1 imu=1 handover=1`, child
exit0; manager phase is active and `Exact input publication confirmed`.
Metadata exposes both `GameSir G7 Pro` and `GameSir G7 Pro Motion Sensors`.
The active identity/tokens remain stable for **10.415 seconds**, with no new
failure, metadata/publication error or service restart. A busy informational
status job at the final sample is not a failed startup.

**This is a successful automatic late-power-on run without additional user
input or manual Resume.** It is **not same-kernel-object WAIT9→READY7**: the
receiver presented a new 100a lifetime after power-on, and the manager performed
its normal controlled 100a→109c bootstrap for that lifetime. The per-port start
budget contains two entries: original receiver setup/wait, then the new source
lifetime. Do not describe that as repeated initialization of one waiting
instance, a single shared setup across all lifetimes, or a measured RF latency.
Historical error entries remain unchanged and must not be recast as new faults.

The maintainer additionally reports that the initial connection was through
xpad. The assistant's first reply treated this as independently established;
the detailed crosscheck corrected that overstatement. These status samples
already see 100a bound to gs_native and do **not** resolve a possible short xpad
first binding. Preserve the human report and the uncertainty together. Neither
this test nor a transient Xbox name establishes that xpad is a necessary
startup dependency. **Completely xpad-free first-probe behavior is not accepted.**
A future targeted initial-binding review must keep this separate from the
successful automatic takeover and preserve other controllers' xpad support.

No manual Release, Resume, service/module/binding/configuration change,
additional reconnect, motor/input/motion test or push occurred. No USB trace
was taken. Controller-off cold boot, a second RF reconnect and application
acceptance remain separate tests. [Sanitized receipt](evidence/RECEIVER_WAIT_LATE_ON_20261020.json).

## Revision 15 receiver-off waiting confirmed — 20 October 2026

The maintainer approved receiver reinsertion and read-only inspection only,
with controller power-on explicitly withheld until a confirmed wait and a
separate Go. Fresh target inspection matched the loaded revision15 module,
current boot/kernel/headers, package integrity, service/configuration and
unpaused empty live/persisted management. The maintainer then confirmed the
receiver reinserted while the radio controller remained off.

The first read-only observer halted before any status samples because its
service guard compared raw versus stripped output, including the trailing
newline; its local summary also mishandled an empty sample list. Both original
errors are preserved privately. Offline reproduction, four changed-service
negative controls and empty-list rendering checks pass after normalization;
no service/identity fields were dropped. A fresh corrected read-only observer
then completed. An independent ordinary inventory confirms the actual same
service/configuration and new `109c`/gs_native binding. Nothing was restarted,
resumed, released or reconfigured to obtain the result.

**Result: one bounded setup reached kernel WAIT_RECEIVER=9** with error=0,
failed_stage=0, pad=0, imu=0, handover=0 and child exit0. The manager and saved
lease both show `receiver_wait`. Ten status/ownership/metadata samples retain
that state for **45.653 seconds**, beyond the old 30-second verification bound.
USB lifetime, kernel tokens, diagnostic and the one-entry start budget remain
unchanged. The retained unit journal contains one matching bootstrap-result
event; no new failure/metadata/publication error or xpad return is observed.
The manager's existing read-only polling attests the continuing instance;
this observer itself opens no native control/USB/input/IIO device.

Receiver-only waiting is therefore confirmed for this approved insertion,
**not yet later power-on, controller-off cold boot, RF reconnect or application
use**. No packet capture was made, so this is not an independently measured
wire-level no-OUT proof. Controller remains off; receiver remains plugged.
Wait for a separate explicit Go before power-on. No runtime code/system change,
manual bootstrap, new Release/Resume or push occurred in this read-only phase.
[Sanitized receipt](evidence/RECEIVER_WAIT_CHECK_20261020.json).

## Revision 15 installed and opt-in activated — 20 October 2026

The maintainer explicitly approved the staged update, graphical authentication,
normal package hooks and controlled removal, excluding the power-on test.
Fresh unprivileged and protected reads matched the prepared revision14 boot,
headers, configuration and blocked lease. Human-confirmed receiver removal was
followed by at least 15 seconds independently observed absence and exactly one
explicit Release. Live and persisted management were paused, returned and empty;
no native binding remained. Original failure history was retained.

The exact revision15 package from `3b7b7de` was transferred and checksum-verified.
One reviewed pacman transaction completed, including the normal guarded cleanup,
DKMS build/install for `7.2.11-1-cachyos-deckify`, snap-pac pre/post snapshots and
configured Limine/initramfs hooks. The known DKMS `CLEAN` deprecation is retained
as a diagnostic, not hidden; no transaction failed. All 137 installed payload
files match, and all three driver/Steam/Gamescope package integrity checks pass.
The service was inactive and the old module absent before activation.

The approved single receiver-wait configuration file was created only after
proving its prior absence. One service start loaded the expected new module,
`srcversion=CA96E675200CE5CCEFB7DD0`, with receiver_wait/bootstrap/output/persistent/
deferred-input options enabled and the existing sensor parameters unchanged.
The immediate status command returned ENOENT; the guard stopped **before Resume**.
A separate read-only check then proved the same service process active/enabled,
zero restarts and responsive paused/returned/empty management. This supports a
short manager-socket startup window rather than a confirmed daemon failure.
No config creation or service start was repeated. The remaining authorized
single Resume then passed its fresh guards and completed successfully.

Final independent inventory confirms revision15, matching loaded/on-disk module,
DKMS installed, active/enabled service and no receiver/native bindings. Protected
readback confirms unpaused empty devices/persisted leases, preserved failures,
`receiver_wait=Y` and unchanged gyro/acceleration settings. Sensor and Steam
configuration hashes remain unchanged. No other host was updated and no push
occurred. See the [sanitized receipt](evidence/RECEIVER_WAIT_INSTALL_20261020.json).

**Installation and opt-in activation pass. Receiver-wait hardware acceptance is
still pending:** the receiver remains physically removed/controller off. There
is no observed state9 instance, late-on handoff, game/gyro/motor test or reboot
in this run. Do not claim the revision14 off-boot blocker is resolved from an
empty successful Resume. Further insertion/power-on requires new approval.

## Revision 15 receiver-wait preparation — 20 October 2026

Fresh approved target reads and an unprivileged hash-pinned module build pass
for `7.2.11-1-cachyos-deckify` and matching headers. GCC matches; zero warnings,
matching vermagic, no automatic USB aliases. Runtime kernel/manager code is
unchanged from offline commit `159a83f`. The new package revision bundles that
implementation and its operator documentation, without enabling it by default.

Current revision14 ownership is still blocked with retained original -110 at
VERIFY5 and an unresolved 109c/xpad return. No installation or activation is
performed. Do not bypass the cleanup hook; require approved physical absence,
paused/returned/empty persisted ownership before a package transaction.
[Exact preparation scope and staged activation](RECEIVER_WAIT_UPDATE.md).
Hardware late-on acceptance, publication and push remain pending.

## Revision 14 controller-off restart fails — 20 October 2026

The maintainer requested one final reboot test before a later push: receiver
stays connected, radio controller stays off, no manual service start/Resume.
The reboot began before the preboot SSH inspection completed; that read timed
out. It issued no mutation and is not treated as a completed preboot baseline.
After the maintainer confirmed Gaming Mode ready and controller still off,
fresh unprivileged readback confirms a different boot, revision 14, matching
`7.2.11-1-cachyos-deckify` module, all three package integrity checks clean,
service active/running/enabled with zero restarts, and `109c` IF0 on `gs_native`.
Protected parameter reads are unavailable to the ordinary account; their
postboot effective values are not claimed from that inspection.

The maintainer separately approved exactly one protected
`gamesir-native status` query, including graphical authentication. It reports
unpaused management, no scan/metadata errors, but the device is **blocked**.
The original nested kernel diagnostic is retained: child exit 1, supervisor
not timed out, `state=8 error=-110 failed_stage=5 pad=0 imu=0 handover=0`.
The outer current error is `Return deadline: still 109c; manual attention
required`, with actual `109c`/`gs_native` still present. Do not describe this as
successful cleanup or xpad fallback. This is no proof that revision 14's
narrow new-100a-after-END exception was exercised.

**Result:** automatic service/module loading passes; healthy controller-off
startup and return are not accepted. The recorded bootstrap has no accepted
pad/IMU data while the maintainer reports the controller off. An unready-radio
startup being treated as failure is a lead; the exact lower-layer cause is not
established by status alone. No new packet trace, protected journal/state read
or postboot parameter check was performed. No radio power-on was cued after
this failure, and no Resume/release, service restart, binding change, retry or
system repair was executed. The pre-push acceptance remains open; no push.
The earlier running-session game/paddle/gyro results are not invalidated.

## Revision 14 activation readback — 20 October 2026

The maintainer requested activation. Fresh checks matched the exact package,
matching running kernel/headers, clean package integrity, stopped/enabled
service, absent module/receiver and paused empty ownership. Displayed commands
were one `systemctl start gamesir-native.service`, then one
`gamesir-native resume`. The guarded runner verified the installed manager and
configuration hashes, loaded module srcversion and effective persistent/sensor
options before Resume. Both completed with no receiver connected; service is
active/enabled, unpaused and has no service restart.

The intended next step was receiver insertion with the controller still off.
The maintainer instead reported the controller already on, then clarified it
automatically powered/connected when removed from the charging cradle. The
relative radio/receiver timing is not established precisely. Readback observes
one native `109c` instance, a successful direct-109c bootstrap with accepted
pad and IMU data, a matching saved device/lease and kernel tokens, and exact
input publication. No current port/status/publication fault is present; the
original failure history is unchanged. No manual second attempt or error
release occurred.

The journal shows a generic xpad gamepad briefly before the native sensor and
gamepad publication. This verifies automatic native takeover, not absence of
transient xpad probing or proof that xpad is required. No new controller-related
kernel fault or panic/lockup signature appears. Separate AMDGPU CRB configuration
warnings are retained in private evidence; they are not attributed to this
controller and no GPU setting was changed.

The maintainer confirms normal Steam buttons/sticks/triggers and all four
independent paddles, including simultaneous presses and release. All three
Steam gyro UI values remained zero during movement, so the initial display
check was negative. Later in the same follow-up, the maintainer reports that
Eden recognizes gyro through SDL and that gyro movement actually steers the
camera in Arc Raiders, after announcing a Steam Input gyro-as-right-stick test.
This is a positive application-use report despite the zero UI values; it
supersedes the earlier inference of failed overall gyro acceptance.

Record the Steam display discrepancy as a deferred TODO, not a blocker for the
reported application use. The precise rendering/notification/context cause is
not isolated. There was no synchronized instrumented game trace or separate
confirmation of Guide independence, rest drift or further reconnect cases.
The application reports do not prove universal compatibility. No further
system/driver/Steam change was made to obtain or document these reports.

The planned late power-on with a receiver already present, cold boot and the
revision-14 returned-timeout exception are not validated by this direct startup.
No reboot, calibration, motor test, other-host update or push was performed. The frozen
revision-14 artifact is unchanged; this records activation only.

## Revision 14 installed on CachyOS — 20 October 2026

The maintainer explicitly approved the displayed transfer/removal/release and
single package transaction with the reviewed hooks, readback only afterward.
Fresh inventory matched the prepared kernel/headers, package/configuration,
service and healthy native instance. The maintainer removed the receiver after
the cue and confirmed it stayed out. Readback proved physical absence and no
native binding. One manual `release` succeeded: paused, returned=true, empty
manager devices and leases. No mode/reset/firmware command was used.

A new one-attempt updater was prepared against this returned/empty baseline;
eleven offline tests passed, including table/count/version refusal and denial
of changed ownership or an unreturned/unpaused state. Package/helper/payload
hashes and the retained revision-13 rollback archive passed before and after
transfer. Previous consumed receipts were not reused. The root helper rechecked
boot/kernel/headers, exact package scope, files/hooks and ownership both before
pacman and at its confirmation prompt.

Exactly one `0.1.0.alpha3-13` to `0.1.0.alpha3-14` package transaction completed
with exit 0. Existing hooks confirmed release, stopped management, unloaded the
unused old module, rebuilt DKMS and completed snapshot/systemd/udev/rebuild-check
and Limine/initramfs work. The known deprecated DKMS `CLEAN` notice was present;
no speculative repair or retry occurred. No unrelated package was updated.

| Final readback | Result |
| --- | --- |
| Package | `gamesir-native-dkms 0.1.0.alpha3-14`, 160 package entries, zero altered files. |
| Payload | All 128 regular installed files match the frozen artifact's hash, mode and root ownership. |
| Kernel/DKMS | Installed for `7.2.11-1-cachyos-deckify`, matching vermagic, module version `0.1.0.alpha3`. |
| Module identity | Expected unchanged srcversion `8207CE72AE527F13E1D1B1D`; no generic USB aliases. The manager payload is separately hash-verified. |
| Service | Inactive/dead, clean exit, no main/control process; prior enabled flag retained. |
| Ownership | Persistent pause true, empty leases, no native binding, no loaded module and receiver absent. |
| Preserved | Sensor configuration and both Steam integrations unchanged; original error history retained. Steam package checks show zero altered files. |

A final independent unprivileged inventory also confirms the same boot,
kernel/headers, absent hardware/module and preserved files. Authentication-free
reports, before-state/profile backup, rollback package and consumed receipts
remain private. The frozen artifact is still source `54d70fc`, SHA256
`313c164a2efe266763b48cbc4251c6c6633c8af99419f92144d94e6aebc8e195`;
this later documentation does not rebuild it under the same revision.
No activation, Resume, reboot, controller functional test, other-host update
or push followed. Leave the receiver out until the next approved step.
Neither installation nor the maintainer's earlier three revision-13 hotplug
successes validate the new correction's first-power-on behavior.

## Revision 14 prepared for CachyOS — 20 October 2026

The maintainer requested the next controlled trial. Fresh read-only target
checks confirm installed revision 13, a healthy unpaused native session,
active/enabled service, matching `7.2.11-1-cachyos-deckify` headers and preserved
sensor/Steam files. The revision-13 rollback package is checksum-verified.
Games, emulator and maintenance app are confirmed closed; Steam may stay open.
Final inventory matches boot, kernel/headers, service process, module, USB
instance/binding, package and configuration before preparation.

Revision 14 source is frozen at `54d70fc6d4bc026594138db3f799c02aec24e8cc`.
Only manager runtime code changes, as reviewed at `ac47724`; protocol, kernel
behavior, sensor profile, haptics and the two Steam integrations are unchanged.
The source archive also includes the first-start/Sony comparison documents so
bundled documentation links resolve. The separately repeated 25 packaging
tests and public README/license checks pass. Full runtime offline results are
in the preceding implementation report below.

An unprivileged build of all 17 selected source files on the target passes
with GCC 16.2.1, zero warnings and unchanged headers/service/package. Expected
srcversion remains `8207CE72AE527F13E1D1B1D`; target vermagic matches.
The locally built Arch package passes its client self-test; all 128 regular
payload files match the staged hashes and modes. No module was installed/loaded.

| Frozen artifact | SHA-256 |
| --- | --- |
| PRE-ALPHA `0.1.0.alpha3-14` x86_64 package | `313c164a2efe266763b48cbc4251c6c6633c8af99419f92144d94e6aebc8e195` |
| Allowlisted source archive | `a84faa9f563c06c218af48bacd5ba614e6b06e6d9975aaa888ab44a1ac4f620b` |
| Standalone target-built module, not the later DKMS-installed/compressed file | `6356923a14377058a740af8f51fb8457cd04edd0040d69bde41905779ef1009a` |

Concrete update steps are prepared privately for explicit approval: physical
receiver removal, one release and verified paused/returned/empty ownership,
then one exact revision-13-to-14 package transaction with the existing hooks
and readback. Do not reuse the previous consumed updater or bypass its return
guard. No package transfer/installation, release, activation, Resume or new
hardware test was performed. This later report does not rebuild the frozen
artifact under the same revision. Other-host update and push remain excluded.
The first missing IMU's cause and real revision-14 startup acceptance are open.

## Offline returned-timeout correction and Sony comparison — 20 October 2026

The manager now retires the old entry after attested direct-109c no-data VERIFY
timeout and verified END, only on a new unattempted `100a` observed on xpad at
the same parent lifetime. No mutation uses that snapshot; a new scan and normal
ownership/budget gates are required. History, failed tokens, pause and cleanup
authority remain intact. Old suppressed state is not automatically migrated.
Other faults and uncertain END/identity/metadata remain excluded. Sixteen new
manager tests reproduce the former refusal and confirm the bounded exception.
Seven real shared-core cases investigate sensor timing without changing it.

Full `make test`: 1,227 Python tests in 43 suites plus existing C/protocol checks
pass, including 56 standalone-manager tests and 282 ASan/UBSan kernel-startup
scenarios. Local module build passes, zero code warnings, one disclosed
Clang 23.1.1/23.1.3 environment advisory. Kernel behavior and ABI are unchanged.
The missing first IMU is not proved to be a decoder/RF/firmware fault. Pinned
Sony/SDL source hashes reverified; no PS5 hardware or complete proprietary
Steam HID path was tested. See [fix](REVISION13_FIRST_START.md#offline-manager-correction--20-october-2026)
and [comparison](DUALSENSE_STARTUP_GAMESCOPE.md). No SSH, runtime change, package,
installation, new hardware test or push. Precision calibration remains paused.

## Revision-13 first-start read-only diagnosis — 20 October 2026

After maintainer-led activation/power cycles, a new read-only inspection confirms
revision 13 and its expected loaded module, active/enabled service, unpaused
management and attested native runtime. Installed manager/service hashes match.
Two saved epochs expose direct-109c VERIFY timeout (`-110`, no accepted pad/IMU),
then an intermediate `100a` retained as observed xpad return, and successful
startup of a subsequent `109c`. The actual manager reproduces the intermediate
released/attempted suppression without devices. See the anonymized
[technical report](REVISION13_FIRST_START.md) for timing, code path and limits.

Forty existing standalone-manager tests, shared C startup tests and 282
sanitizer-backed kernel-adapter scenarios pass. Final inventory confirms the
same boot, service process, module, USB instance/binding, package and configuration
as before inspection. No installation, activation, binding or controller command,
capture, Steam change or new hardware test was performed. Evidence/backups remain
private; no push. This diagnoses the suppression policy, but does not prove why
the first IMU is absent or fix hardware startup. Precision calibration stays paused.
The installation-time state in the following entries is historical.

## Revision 13 installed after verified physical removal

19 October 2026. Following the stopped first transaction, the maintainer
explicitly authorized physical dongle removal and read-only confirmation, then
separately authorized a new update if all checks were green. The dongle was
removed by the maintainer and remains absent. No guessed USB command, reset,
Resume or direct binding change was used to resolve the old entry.

Fresh unprivileged inventory and a protected read confirmed:

- No GameSir USB device or native binding; installed revision 12, kernel/headers,
  package files, hooks, sensor/Steam configuration and service process unchanged.
- Management paused, `returned=true`, empty devices and leases, no scan/port or
  input-monitor errors. The manager recorded physical absence for the old entry;
  this is verified absence, not an assertion of a working `100a` fallback.

A new private one-attempt helper was prepared against that exact baseline.
It requires both paused and confirmed returned state with empty devices/leases,
checks kernel/boot/headers and the unchanged artifacts, and rechecks immediately
before accepting only the revision-12-to-13 pacman transaction. Eleven offline
tests passed, including refusal of unpaused, unreturned, owned or newly present
states. The prior consumed receipts and abort logs were preserved. The concrete
new helper invocation was displayed before execution; no duplicate permission
was requested after the maintainer's explicit conditional authorization.

The original candidate package from source `ec7adf8` was transferred unchanged:
SHA-256 `826c9e32521e8814250f943c8355fea6ce6c7541993f8b71b0622174d0aab96b`.
The retained revision-12 rollback artifact was reverified, not executed. Fresh
checks passed; one package transaction completed with exit 0. The existing
pre-hook confirmed release, stopped the manager and unloaded the unused old
module. Snapshot, DKMS, systemd/udev, rebuild-check and Limine/initramfs hooks
completed. The only logged warning is DKMS's known deprecated `CLEAN` field.
No full system update or unrelated package transaction occurred.

| Final check | Verified result |
| --- | --- |
| Installed package | `gamesir-native-dkms 0.1.0.alpha3-13`; 158 package entries, zero altered files. |
| Payload | All 126 regular installed files match archive hash, mode and root ownership. |
| DKMS/kernel | Installed for `7.2.11-1-cachyos-deckify`; version `0.1.0.alpha3`, matching vermagic and no generic USB aliases. |
| Module identity | srcversion `8207CE72AE527F13E1D1B1D`, matching the separately tested target build. |
| Service | Inactive/dead, clean exit, no remaining main/control process; prior enabled flag retained. |
| Runtime | Management paused; no loaded native module, native bindings, USB dongle or ownership leases. |
| Preserved state | Original failure history retained; sensor configuration and both Steam integrations unchanged and intact. |

Full reports, authentication-free logs, before-state/config backup and receipts
are retained privately. This documentation was added after freezing/installing
the artifact; it does not rebuild the package under the same revision. Local
commit only, no push. No activation, Resume, reboot, motor/gyro/input test or
other-host update followed. The dongle stays disconnected. The enabled flag
alone does not clear the management pause; activation and cold-start acceptance
need their own reviewed next step. The xpad query's necessity/effect on real
cold startup is still unconfirmed. Precision calibration remains paused.

## Revision-13 update stopped before package replacement

19 October 2026. The maintainer explicitly approved the prepared transfer and
one revision-12-to-13 package transaction, password prompt and documented hooks,
with readback only afterward. The fixed package/helper/payload hashes matched
after transfer; the retained revision-12 rollback artifact was also reverified.
The guard's fresh kernel, headers, package integrity, module, parameters,
USB identity, manager state/history and exact transaction checks passed.

The installed **revision-12 pre-transaction hook** then ran `release`. That
paused management but could not establish `returned=true`: the previous
blocked `100a` entry still observed a new `109c` on xpad. `managed_returned`
checks the union of entries and leases; this entry remains in scope even
though there are no leases or native bindings. Its expected fallback PID is
`100a`, not `109c`. The known block therefore prevented release within its
bounded wait. The hook correctly refused to continue; pacman exited 1 and
reported that no packages were upgraded. No automatic repeat was attempted.

**Preparation gap:** the update preflight pinned the blocked entry and empty
ownership but did not account for that entry's return predicate. Empty leases
alone were insufficient to call this baseline ready for the package hook.
The hook was not bypassed, and there is no reason to weaken PID/return proof.
Any next attempt must first establish a newly approved recovery baseline.

Protected post-read and an additional unprivileged inventory confirm:

| Check | Verified aftermath |
| --- | --- |
| Installed package | Still `gamesir-native-dkms 0.1.0.alpha3-12`; no package replacement. |
| Integrity | Driver 156 files, Steam integration 17, Gamescope integration 15; zero altered files in each package. |
| Service | Same active/running process, enabled, no restart; management now persistently paused. |
| Module | Revision-12 srcversion `FA9FE508DE0DF7C8E1F8019` still loaded/on disk; no native bindings. |
| USB | Same unowned `109c` instance, IF0 xpad; no claim of working fallback or physical input acceptance. |
| Recovery state | Leases empty; original failure history unchanged. |
| Preserved files | Kernel/header hashes, hooks, sensor and Steam configuration unchanged. |
| Hook effects | Pre-transaction snapshot created and release set pause. Guard stopped before service stop, module unload, DKMS replacement or post-installation hooks. |

The source/package hashes and successful offline/target builds below remain
valid. Revision 13 has not been installed or exercised on hardware. Preserve
the consumed one-attempt receipts, state/config backup and full private logs.
No firmware/Steam change, activation, Resume, reboot, additional hardware test,
other-host update or push occurred. Documentation only is committed locally.

Next proposed step: separately authorize removing only the GameSir dongle and
read-only confirmation of stable absence, no native ownership and the manager's
return status. Leave it absent until instructed. Do not clear failures manually,
infer a mode change from xpad binding, or reuse the old installation receipt.
Once the baseline is confirmed, prepare a fresh single transaction and display
it for approval; activation and the cold-start acceptance remain later steps.

## Revision 13 candidate: observed xpad startup query — 19 October 2026

Revision `0.1.0.alpha3-13` combines the preceding manager autoprobe correction
with the maintainer-requested captured control-IN startup query. One explicit
`100a` bootstrap issues it before the first transition OUT, with exact setup,
20-byte reply requirement, a 25-ms timeout and no retry. Post-transfer ownership
and deadlines are rechecked; earlier RX errors remain primary. Direct `109c`,
experimental `105e`, sensor profile, input publication and force feedback are
unchanged. [Details and acceptance limits](ACQUISITION_AUTOPROBE_FIX.md#revision-13-explicitly-requested-startup-query-integration).

Offline checks: **1,211 Python tests in 43 suites**, all C/protocol checks,
**282 extracted actual-kernel bootstrap scenarios** (15 new query cases), and
**98 acquisition scenarios** pass. ASan/UBSan, strict checkpatch and the five
Clang-analyzed translation units pass. The local `7.2.11-1-garuda` module builds
with no code warnings. Its one environment warning is the documented compiler
patch difference (kernel Clang 23.1.1; local Clang 23.1.3), not a clean-warning
claim. These checks do not replace real cold-start and recovery acceptance.

Fresh authorized read-only target inspection finds `7.2.11-1-cachyos-deckify`
and matching `7.2.11-1` headers/GCC 16.2.1, intact installed revision 12 and
Steam packages, available dependencies and no package lock. The active/enabled,
unpaused manager retains its old blocked pre-acquisition entry, with no leases
or native bindings. The current unowned dongle is `109c` on xpad. This is not
an input test or a confirmed recovery. Sensor settings are still enabled as
reviewed. Build/package results are recorded below when complete.

Only candidate preparation, read-only inspection and an unprivileged target
build are authorized at this point. No installation, activation, Resume,
reboot, Steam change, hardware test or push. Installation will pause management
via the reviewed package hook; the existing boot-enable flag alone will not
undo that pause. Keep the retained rollback package and original error history.

### Revision-13 build/package preparation completed

Frozen source `ec7adf881faa2829100c2495475f66f638f9dd12` was built unprivileged
against the freshly checked CachyOS `7.2.11-1-cachyos-deckify` headers with GCC
16.2.1, zero warnings, matching vermagic and no generic USB aliases. Header
hashes, installed package and service state were identical before/after build.
Target module srcversion: `8207CE72AE527F13E1D1B1D`; standalone build SHA-256:
`08a5a244cf817899db56e0d6394867fcf0d0e2385daffb61499ab3bc4b2e8cb0`.

The local Arch package `gamesir-native-dkms 0.1.0.alpha3-13` passed its client
self-test and contains 126 verified regular payload files. Package SHA-256:
`826c9e32521e8814250f943c8355fea6ce6c7541993f8b71b0622174d0aab96b`.
The allowlisted source archive hash is
`15d53dc407bba1fbe20080548bc2f19dadd677f0a8c259f199bd16fcf6821f38`.
This final audit was added after freezing the package; the artifact was not
rebuilt under the same revision. Public source/notice checks and whitespace
review pass. Private build directories, host/user identities and raw state/logs
remain excluded from Git. No artifact or source has been pushed.

The private one-attempt updater is prepared, not executed or transferred. It
pins this boot, kernel, header and package hashes, the observed unowned device,
empty ownership, manager state/history, old loaded module and unchanged hooks.
It checks the single revision-12-to-13 transaction immediately before confirming.
Nine offline tests cover compact/verbose pacman previews, extra/wrong packages,
changed device state and negative confirmation. The approved transaction would
use the existing pause/return/stop/unload guard, DKMS, Snapshot and Limine/
initramfs hooks, then verify payload, DKMS/srcversion, stopped/paused state and
unchanged sensor/Steam settings. It does not start the new service or Resume.

A final unprivileged read confirms unchanged target state and verifies the
retained revision-12 rollback package hash/metadata. This only establishes a
rollback artifact, not a tested downgrade or wireless recovery. No automatic
rollback, repeat installation or error-history deletion is planned. Activation
and both physical startup cases still need separate approval and acceptance.

**Ready to request the scoped update; no cold-start success claim.**

## Offline pre-acquisition race correction and xpad query review — 19 October 2026

After the user-led revision-12 cold boot, saved read-only evidence confirms
an active/enabled, unpaused manager and expected module, but a refusal before
acquisition: `Device changed during ownership check`. No native lease/binding
or bootstrap was established. The old diagnostic does not identify changed
fields; it does not prove a firmware, RF or xpad-query fault.

The real manager Host adapter's same-instance free-to-xpad autoprobe race was
reproduced offline with the old error. It now permits exactly one complete
read-only ownership/identity recheck before the single scoped acquisition.
All identity fields remain pinned. The second check is strict; original
metadata errors and uncertain-write failures are preserved, and no old blocked
attempt is silently reopened. The normal status/return guards, start budget,
pause, kernel acquisition proof and bootstrap are unchanged.
[Implementation and evidence](ACQUISITION_AUTOPROBE_FIX.md).

`make test` passes **1,211 Python tests in 43 suites**, including twelve new
regression cases (40 standalone-manager tests in total), plus the existing
C/protocol/sanitizer tests. Extracted kernel checks include 267 bootstrap and
98 acquisition scenarios. Packaging regression tests include the new report
and sanitized evidence in the source-document allowlist. No kernel source
changed; no new module or installable release package was built in this task.
A future package must use a fresh revision rather than reuse the previously
installed revision-12 artifact or its hash. No installation approval follows
from this software validation.

Ten saved original USB captures match their recorded hashes. A tshark file-only
review and independent raw PCAPNG/URB checks agree on **16 matching xpad control
IN queries and 16 successful, identical 20-byte replies**. Some normal inputs
precede the observed queries; recording boundaries cannot rule out earlier
queries. Previously initialized return epochs are not cold-start evidence.
The necessity of this request for a fresh native start remains unproven; no
USB command was added. [Frame-level manifest](evidence/XPAD_START_QUERY_REVIEW_20261019.json).

Changed public files contain no host paths, private identity/USB tokens or
raw captures; originals, analysis scripts and validation logs stay private.
Diff/whitespace and public-documentation checks pass. Local commit only. No
SSH, live read, installation, module/service action, device access, Steam
change, new hardware test or push. Precision calibration stays paused.


## Revision 12 CachyOS build and installation — 19 October 2026

Following explicit installation authorization, fresh read-only checks verified
kernel/header `7.2.11-1-cachyos-deckify`, matching GCC 16.2.1, intact revision
11 and optional Steam packages, available dependencies and no package lock.
At this checkpoint the active manager had no leases or native bindings; the
dongle was already `109c` on xpad. Historical resolved failures were preserved.
This baseline is not a new controller-input or recovery acceptance test.

The frozen source commit `057270a` built unprivileged on the target with zero
warnings and unchanged header fingerprints. The module has no generic USB
aliases, matching vermagic and srcversion `FA9FE508DE0DF7C8E1F8019`.
Its standalone build SHA-256 is
`f65913bf1986983d58d4a611d5596a09f959e0a38ec8e3e9ce9b72f881ffa4b1`.
The private Arch package is `gamesir-native-dkms 0.1.0.alpha3-12`, SHA-256
`41cf732a39ae064e9d30887440b77c0aacd91676bd819b37d88a46db5d30d6f8`.
It was not rebuilt after this installation evidence was added to the docs.

The concrete update command and hook effects were displayed before execution.
The one-attempt wrapper passed nine offline transaction tests, accepted only
the reviewed revision-11-to-12 transaction and rechecked live ownership before
confirmation. Package, wrapper and payload hashes were verified after transfer;
the retained revision-11 package was verified as a possible rollback source.
No rollback was executed or newly hardware-validated.

| Check | Verified result |
| --- | --- |
| Pre-transaction guard | Management paused, ownership empty, service stopped and unused old module unloaded; no device rebind was needed. |
| Package transaction | One update, exit 0; existing Snapshot, DKMS, systemd/udev, rebuild-check and Limine/initramfs hooks completed. |
| Installed payload | All 124 regular files match archive hashes/modes and root ownership; package integrity reports zero altered files. |
| Target DKMS/module | Installed for `7.2.11-1-cachyos-deckify`; version `0.1.0.alpha3`, matching srcversion above and vermagic, no generic aliases. |
| Runtime | Service inactive/dead, clean exit; existing enabled setting retained. Management paused, leases empty; no loaded native module or native bindings. |
| USB metadata | Same initial `109c` instance remains on xpad. No claim that this is a transition to `100a` or proven working fallback. |
| Preserved settings | Sensor configuration, base Steam integration `0.1.0.alpha2-1` and Gamescope integration `0.1.0.alpha1-1` unchanged and intact. |

DKMS reports only its already-known deprecated `CLEAN` field; the target build
and installation succeed. Host paths, state/configuration backups, logs and
one-attempt receipts remain private. No password is saved. No other-host update,
service activation, Resume, reboot, motor/gyro test or push occurred.

**Installation checks pass; both power-on hardware cases remain untested.**
The persistent management pause is not removed by the enabled boot setting.
Review activation separately before testing power-on without button input,
including an initial `109c`, RF-off-at-boot and late connection.

## Revision 12 power-on startup correction — 19 October 2026

Revision 12 removes the accepted-pad-counter prerequisite after validated
passive `100a` status and adds exact-instance `acquire_109c` for an initially
native-mode dongle. The latter sends only the six existing native startup
packets on the pinned instance. No new USB command, sensor unit, paddle,
force-feedback or bridge behavior is introduced. Fresh IMU, ownership proof,
input-publication readiness, bounded attempts and original errors remain
required. Still-`109c` cleanup is not claimed as a usable xpad return.
See [startup design and acceptance limits](STANDALONE_STARTUP.md).

The complete offline suite passes: 1,199 Python tests across 43 suites,
C/protocol/sanitizer regressions and tests of extracted kernel code. Scoped
acquisition covers 98 scenarios; kernel startup covers 267 cases. Regression
coverage includes zero pad reports, direct native startup, wrong/replaced
instances, missing or stale proof, daemon/client loss, budget exhaustion,
failed STOP, original-error retention and absence-based recovery.

The module builds for `7.2.11-1-garuda` with zero code warnings. Its single
classified environment warning is the existing kernel/compiler patch-version
difference (Clang 23.1.1 versus 23.1.3). Checkpatch passes; Clang static analysis
reports zero diagnostics in five translation units. Sparse is unavailable.
These checks do not establish physical power-on, RF-off-at-boot or late-on
acceptance. Missing fresh IMU still terminates the bounded attempt; no
unbounded waiting or speculative retry is introduced.

The maintainer subsequently authorized preparing and installing revision 12
on the CachyOS target. Target-specific build and installation results will be
recorded separately; this offline checkpoint does not imply either occurred.
No activation, hardware acceptance, other-host update or publication is implied.
Precise gyro calibration remains paused.

## Revision 11 cold boot still requires input — 19 October 2026

The maintainer's subsequent cold-boot report narrows acceptance: only the
controller was switched on/operated, with no manual service start or Resume;
power-on alone was insufficient. Fresh read-only metadata/journals show the
enabled service and expected module started automatically. Initial `109c`
was xpad-bound; a later fresh `100a` was acquired, bootstrapped successfully
and published with paired native input/sensor nodes. No service restart was
recorded. [Timeline and source findings](STANDALONE_STARTUP.md#cold-boot-and-input-dependency--19-october-2026).

Offline inspection confirms both the deliberate exclusion of unrelated
pre-existing `109c` and the `100a` accepted-pad-report gate. The latter waits
without starting bootstrap when reports are absent; existing synthetic tests
cover both behaviors. There is no timestamped input trace proving the exact
trigger or allocating the delay. Native binding and completed runtime must
not be conflated. This is **not** acceptance of power-on-only readiness or
cold startup without previous xpad initialization. The earlier positive
Steam gyro radio-reconnect observation retains its separate limited scope.

Validation: 14 existing standalone-manager regressions and the targeted
passive-wait service regression pass; seven public-documentation tests pass,
the tracked-file checksum manifest is regenerated and the diff checked.
No production code, package, installed configuration, Steam setting or
runtime state is changed. No new hardware test, elevated authentication or
push; original host-specific evidence remains private.

## Revision 11 user-led activation and gyro report — 19 October 2026

After the installation-only checkpoint below, the maintainer independently
started the service and ran Resume. Read-only follow-up identifies the newly
loaded module, its acquisition attributes, active/enabled service, successful
native bootstrap and paired gamepad/motion nodes. The maintainer explicitly
confirms one radio off/on cycle with the dongle left connected: Steam's gyro
display in Gaming Mode works without held Guide and without restarting Steam.
[Detailed evidence and limits](STEAM_GYRO_HOTPLUG.md#revision-11-user-led-radio-reconnect--19-october-2026).

The observed startup used the optional xpad handoff from a previously
initialized device. No cold no-xpad proof, causal explanation of the gyro
improvement, full input/haptics regression or repeated hotplug acceptance is
claimed. Codex only read metadata/journals during this phase; it did not open
input/sensor nodes, run another activation or request elevated authentication.
Private logs retain the original identities; no raw logs or private paths are
added to the repository. No push or further hardware test follows automatically.

## Revision 11 CachyOS installation — 19 October 2026

After the preview-only refusal below, the maintainer explicitly approved one
new update attempt with the corrected private helper, fresh inspection,
password window and previously reviewed hooks. Activation remained excluded.
The original attempt and receipt were preserved. The new helper passed both
preflight and exact single-package transaction review before confirming once.

| Check | Result |
| --- | --- |
| Package | `gamesir-native-dkms 0.1.0.alpha3-11`, SHA-256 `f0d3dc3f9a9a9e2e8b2d9aafb38cb0b8dc55f308583b46c743ea2dd2e4ec67bd`; same reviewed artifact, not rebuilt after the wrapper correction. |
| Fresh baseline | Kernel `7.2.11-1-cachyos-deckify`, matching unchanged header fingerprints, intact revision 10 and optional Steam packages, same healthy manager/native instance and sensor settings. |
| Guarded return | Existing package guard confirmed return and empty ownership, stopped the service and verified the old module absent before DKMS removal. No forced unload or recovery bypass. |
| Transaction | One confirmed `pacman -U` update, exit 0. Snapper pre/post, DKMS remove/install, systemd/udev, rebuild check and effective Limine/mkinitcpio hooks completed. The initramfs log reports successful image generation and boot-entry update. No other package upgrade. |
| Installed source/payload | Package check: 156 files, zero altered. All 124 regular payload files match the reviewed archive's hashes, modes and root ownership. |
| Target DKMS/module | DKMS reports installed for `7.2.11-1-cachyos-deckify`; version `0.1.0.alpha3`, srcversion `06354BBF7CEC05B29300CC8`, matching vermagic, no generic USB aliases. This is the new on-disk module, not a loaded-module test. |
| Runtime after update | Service inactive/dead, clean exit, existing enabled setting retained; `gs_native` absent, no native bindings. Saved management pause true, leases empty, historical failures preserved. |
| USB readback | Actual `3537:100a`, IF0 xpad, IF1 usbhid. This is verified identity/binding return, not a human normal-input test. |
| Preserved configuration | Experimental gyro/accelerometer configuration unchanged; base Steam integration `0.1.0.alpha2-1` and Gamescope integration `0.1.0.alpha1-1` unchanged and intact. |

DKMS reports its deprecated `CLEAN` configuration field; the installation and
matching target build succeeded. No packaging cleanup was mixed into this
approved transaction. Full logs, configuration/state backups, receipts and
host-specific details remain private. No password is stored in those logs.

**Installation checks pass; activation and hardware acceptance remain pending.**
No service start, module load, Resume, reboot, motor/sensor test, Steam change,
push or tag occurred after the update. The existing autostart setting does not
remove the persistent management pause. This observed xpad-bound instance is
not evidence of a cold native start without earlier xpad initialization.
Review that isolation and the next activation separately. Precise calibration
remains paused; the Steam late-arrival/Guide issue is still unresolved.

## Revision 11 installation preview stopped — 19 October 2026

The maintainer approved transfer and one package update, including the reviewed
hooks and password window, followed only by inspection. Fresh unprivileged and
protected checks confirmed the same kernel/headers, intact installed revision
10, healthy active/enabled manager and the exact managed native instance.
The revision-11 package and private wrapper were transferred and hash-checked;
the prior revision-10 package was also verified as a potential rollback source.

The wrapper expected pacman's compact `Packages (1)` display. This target uses
the verbose `Package (1)` table with separate old/new-version columns. The
wrapper rejected that valid preview and supplied `n` before confirmation.
No package hooks, release, stop, unload, DKMS replacement or activation ran.
The final readback still shows revision 10, its original module srcversion,
the same active/enabled manager process, unpaused management and the same
native USB instance with no current port error. Revision 11 is **not installed**.

The private helper was corrected offline against the recorded preview. It
accepts either reviewed format for exactly the one intended upgrade; extra
packages, wrong versions, warnings/errors, unexpected prompts and changed
device ownership remain refusals. The ordinary phrase about looking for
conflicting packages is not itself a reported conflict. Nine tests pass,
including 17 negative preview variants and five synthetic child-process
confirmation/denial scenarios. No real pacman, sudo, SSH or device operation
ran in these tests. Original logs and consumed receipts remain intact; the
next attempt exists only locally and has not been transferred or executed.

This was a private installation-wrapper defect, not a kernel/manager failure.
No production code or package was changed. Another live attempt needs new
explicit approval, with fresh checks; no push or hardware acceptance follows.
Independent native acquisition could remove an enumeration transition, but
there is still no evidence that revision 11 fixes Steam's late-arrival or
Guide-dependent gyro behavior. Successful Eden motion already distinguishes
that application symptom from complete sensor failure.

## Revision 11 CachyOS module build — 19 October 2026

The subsequent request explicitly authorized a read-only target kernel/header
check and an unprivileged module build. This closes the missing CachyOS build
item in the earlier offline checkpoint below; it does not authorize installation
or establish runtime acceptance.

| Check | Result |
| --- | --- |
| Source | `5b14c85d980756b04edadcab2d87a2a85a8b97b6`; exactly 17 selected kernel/core/UAPI/build-helper files, hashes verified before transfer and after build. No private files or entire repository transfer. |
| Running kernel and headers | `7.2.11-1-cachyos-deckify`, `linux-cachyos-deckify-headers 7.2.11-1`; prepared UTS release matches. Kernel/boot identity and five required header fingerprints unchanged before/after. |
| Toolchain | Build compiler GCC 16.2.1 20260810 matches the prepared kernel compiler family/version. The kernel metadata records GNU ld 2.47; the build planner selects GNU ld.bfd and explicitly clears LLVM selection. |
| Module build | Passed with `W=1` and `KCFLAGS=-Werror`, zero warnings/errors. No package hooks, DKMS install or module load. |
| Module verification | Version `0.1.0.alpha3`, vermagic `7.2.11-1-cachyos-deckify SMP preempt mod_unload`, srcversion `06354BBF7CEC05B29300CC8`, no automatic USB aliases. Both new acquisition entry points are present. |
| Module SHA-256 | `1bff312e543d3dddff38e15b28c800604d4c2167ddf3f6970ead9bf4ba43289b`; a local copy matches the remote build result. |
| Runtime observation | Installed package remains `gamesir-native-dkms 0.1.0.alpha3-10`; service remains active/running/enabled with the same process. No service or binding operation was executed. |

Build outputs remain in a separate user-owned target directory and private local
evidence storage. Raw SSH/build logs, paths and module binaries are not committed
or uploaded. SSH uses the existing authenticated alias; no sudo/password prompt
was necessary. This is a build result, not a hardware, cold-start, Gamescope,
reconnect, PM or game acceptance result. The installed controller remains on
the previously running version. New installation/activation and each host's
runtime tests require separate authorization; calibration remains paused.

## Revision 11 standalone startup — offline audit, 19 October 2026

Base: the approved and published `e2415a9`. New work is isolated on
`codex/standalone-startup`, with core package recipe `0.1.0.alpha3-11`.
[Design, ownership boundaries and later acceptance](STANDALONE_STARTUP.md).
No installed module, system service, Steam setting or controller was changed;
no SSH, new hardware trial or push is part of this change.

| Check | Result |
| --- | --- |
| `make test` | Passed: 1,185 Python tests across 43 suites, plus default C/sanitizer, real-adapter extraction, protocol and package checks. |
| New startup regression | 14 manager/host scenarios plus 81 actual-kernel claim/acquisition scenarios total. Covers no xpad driver directory, free 100a/105e, optional scoped xpad, foreign/native rejection, replacement, pause/budget, restart and failed/absent fallback. |
| `make test-sdl` | Passed: 18 button, 5 hotplug and 16 sensor scenarios, synthetic devices only. |
| `make test-gyro-viewer` | 14 offscreen tests passed. |
| Arch/DKMS packaging | Revision-11 source archive and unprivileged `makepkg --cleanbuild` completed. Package stages the matching kernel sources, manager and new guide; no installation, package hooks or module load. Generated artifacts remain private pending a separate release review. |
| `make kernel-analyze` | Garuda `7.2.11-1-garuda` module built with matching vermagic, zero code/unclassified warnings. Kernel Clang 23.1.1 versus build Clang 23.1.3 remains an explicitly recorded compiler advisory. Strict checkpatch passed; all five Clang-analyzed translation units had zero diagnostics. Sparse unavailable. |

Kernel acquisition now pins and validates the exact IF0 before optional xpad
detach. The manager no longer needs xpad for free-interface discovery and
does not perform its previous name-based initial unbind. Missing new kernel
attributes cause a pre-write rejection. Acquisition intent alone cannot justify
native cleanup after a failed write or daemon loss. The first failure remains
separate from later cleanup errors, and absence of the xpad bind interface
stops fallback before native unbind. Existing fallback replacement-race limits
remain documented, as does uncertain 109c → 100a physical return.

The common protocol, runtime, sensor conversion, UAPI, Steam/Gamescope mapping
and userspace trigger bridge are unchanged. Their offline regression results
do not repeat or extend earlier real-game evidence. Warning text, GPL-2.0-only,
COPYING, UAPI exception and source provenance remain intact. Added tests and
documentation contain synthetic identities; proprietary inputs and private
test logs/build products stay outside Git. The source/package manifest includes
the new startup guide. Optional package versions are unchanged.

**Decision:** ready for review of a controlled next validation, not for claiming
new hardware acceptance or automatic installation. A new CachyOS module build
is still required: no matching CachyOS headers are available in the local
build environment/cache, and this offline task does not access the target.
Prior CachyOS builds do not validate these new kernel changes. Both hosts need
separate runtime tests, especially cold free-interface startup without prior
xpad initialization. Steam's late-power-on/Guide-dependent gyro issue remains
open; controller-on-before-Steam and the manual Eden workaround remain
documented. Precise calibration stays paused; GUI work follows integration.

## Final unpublished-source check — 19 October 2026

This checkpoint supersedes older publication decisions below. The current
request is **audit first, then separate push approval**. No push, new tag,
release, installation or runtime change is authorized or performed here.

The freshly fetched public `main` is
`947790b50a8f21e3c27d53e297ffabf469ff1a0a`. The reviewed implementation and
Eden-documentation tip is `2e9c8539ca66722334a706849bef42c2fc08e7d7`, with
78 unpublished commits and no missing upstream commits. The audit follow-up
changes documentation and its checksum manifest only. The proposed publication
is this complete public-repository history, not the separate private original
history, a mirror push, new release tags or binary artifacts.

### Fresh offline validation

Tests ran from a fresh `git archive` extraction of that tip, without `.git`,
private evidence, proprietary firmware or previously built project outputs:

| Check | Result |
| --- | --- |
| `make test` | Passed: 1,171 Python tests across 42 suites, plus the default C, sanitizer, adapter, fixture and package checks; no skipped Python tests. |
| `make test-sdl` | Passed: 18 button, 5 hotplug and 16 sensor scenarios using synthetic devices and the installed SDL libraries. No controller access. |
| `make test-gyro-viewer` | 14 offscreen GUI tests passed. |
| `make test-rea-local` | 39 tests passed with synthetic inputs/backends; no manufacturer application or firmware execution. |
| `make kernel` | Built for `7.2.11-1-garuda`, matching vermagic, zero code warnings and zero unexpected warnings. The known compiler advisory remains: kernel Clang 23.1.1 versus build Clang 23.1.3. Module not loaded or installed. |
| Documentation | All local Markdown file/directory links resolve. README warning and GPL/UAPI checks pass. Eden steps preserve the existing executable/arguments and have an application-only rollback. |
| Build-source archives | Core, Steam, Gamescope and trigger-bridge archives each reproduce byte-for-byte in two generations from the reviewed source. Explicit member lists, source bytes, license files and neutral ownership metadata are checked. No binary package installation or release upload. |

The CachyOS module build and target checks remain the separately recorded
historical evidence; this final audit does not reconnect to a target or claim
a fresh CachyOS build. Offline regression success is not additional hardware,
Steam Input, game, suspend or reconnect acceptance.

### Publication privacy and provenance

The initial scan covers every newly reachable object, including intermediate
versions and commit messages: 78 commits, 579 file blobs (17,767,854 bytes)
and 287 trees. All 88 commits reachable from the reviewed public tip use the
approved public GitHub-noreply identity for both author and committer. No
private email, host/home reference, credential, private key or real network
address was identified. The final documentation commit is checked again
before requesting permission; these counts identify the initial frozen tip.

Reviewed matches are public attribution already present upstream, public
noreply metadata, Windows/firmware version numbers, the reserved test address,
a systemd instance-unit name and synthetic example/sandbox paths. Existing
authorship and third-party notices are retained. This is a bounded pattern
scan and manual review, not a guarantee against every possible secret format.

No new binary blobs, device captures, manufacturer packages/firmware, symlinks,
submodules or private working directories occur in the unpublished trees.
Own, reduced protocol fixtures are explicitly documented; they are not raw
USB captures or bundled firmware. The withdrawn Eden launcher prototype stays
private and absent from the publication tree and package lists. GPL-2.0-only,
COPYING and the Linux-syscall-note UAPI exception remain unchanged. Static
research reports do not license or distribute their proprietary reference files.

Five stale documentation hashes were found in SHA256SUMS at the initial tip;
the audit follow-up regenerates the manifest after the documentation updates.
Historical source/evidence manifests retain their original meaning and are
not rewritten as fresh measurements. Raw audit logs and build outputs remain
private and excluded from Git.

### Decision and remaining limits

The source is suitable for a **PRE-ALPHA source push after explicit approval**,
subject to the final clean-tree, manifest and archive checks recorded with the
local audit commit. This is not a stable-release recommendation or a new tag.
Core package revision is `0.1.0.alpha3-10`; existing optional component versions
remain unchanged. No package-version bump is needed for this documentation audit.

- Revision 10 was installed and tested on CachyOS. The late-power-on Steam
  gyro case failed; later Guide-held display response does not close it.
  README now states this instead of describing an uninstalled preparation.
- Eden's manual Gamescope launch workaround is application-tested: physical
  pad and sensor opened, gyro without Guide, four independent paddles and
  ordinary inputs accepted. It is documentation only, not kernel/installer/
  Control Center automation, and does not solve Steam's gyro display case.
- Removing both inherited SDL filters can expose other controllers within
  Eden. Selection and duplicate-input checks remain necessary; global Steam
  Input/SDL settings and the existing paddle mapping remain unchanged.
- Precise gyro calibration stays paused. ZZZ feature coverage, general
  trigger support in Steam/Proton, repeated reconnect, suspend and long-term
  reliability remain limited as documented. No new stability promises.

## Gamescope metadata identity corrected offline — 19 October 2026

The second separately approved metadata attempt reached the remote program,
recorded service active/running/enabled, then stopped at its name/owner-based
Gamescope guard. No module-option, Steam-FD or library attestation followed.
The latest human report is automatic binding after full reboot without Resume
and gyro display only with held Guide. [The follow-up](STEAM_GUIDE_GYRO.md#gamescope-process-identity-corrected-offline)
and [sanitized evidence](gamescope-identity-offline.json) preserve both limits.
The helper now verifies exact executable backing, the four process UIDs and
stable PID/start, rejecting replacements, ambiguity and denied metadata.
`make test-steam`: 160 passed, including 27 new identity tests; 19 private
preparation tests passed, including exact-payload Fish transport checks.
No Steam/vendor application execution, remote access, real sudo, device access,
installation or runtime change in this correction. Only synthetic metadata
and a test-owned Python child are used. No kernel rebuild/package bump is
needed for this diagnostic-only change. The third read is prepared but needs
new approval; the Guide/gyro cause and Gamescope reconnect remain unresolved.

## SSH metadata transport corrected offline — 19 October 2026

The approved metadata attempt stopped in the remote Fish parser before sudo
authentication/read-program execution; it supplies no current gyro diagnosis.
The user now reports no Guide-held response and manual Resume, not autostart
acceptance. [Follow-up and sanitized evidence](STEAM_GUIDE_GYRO.md#metadata-precheck-stopped-before-authentication)
record a pure source-encoding helper and 14 real local Fish/Bash/sh regressions,
with a synthetic sudo/password fixture only. `make test-steam`: 133 passed;
private exact-command/identity/one-attempt checks: 15 passed. No actual SSH,
sudo, GUI authentication, Steam/vendor execution, device access or installed
change occurred in the correction. A new metadata-only run is prepared but
not executed; it needs fresh permission. Original failure retained, no retry,
package/version change or publication. Real gyro hotplug acceptance stays open.

## Targeted Guide investigation remains offline — 19 October 2026

[Report and evidence](STEAM_GUIDE_GYRO.md): actual extracted emitter adapters
and both tested SDL3 libraries pass eight fresh frames across Guide holds and
releases; 24 total SDL scenario runs pass including SDL2. The pinned Steam
reference requests background events, while its notification path requires an
existing selected motion source and does not create one through that lookup.
Internal Guide handling is mapped, but its causal connection to the failed
target run remains unproved. No live/controller/target access or installed
driver/Steam change, no package-version bump or publication. Real Guide-free
motion and reconnect acceptance remain blocked. Only own tests, independent
analysis and sanitized hashes enter Git; proprietary excerpts remain excluded.

## Guide-held response qualifies the zero display — 19 October 2026

The maintainer subsequently clarifies that the gyro display works while Guide
is held. The previous zero-rate observation remains historical; a complete
absence of gyro response is no longer an accurate summary. The Guide dependency
suggests an event/notification/refresh issue but does not establish a pure UI
defect or the exact failing layer. Continuous operation without holding Guide
and reconnect remain unaccepted. This is a human report, not another agent-run
capture or an authorized runtime change. See the updated target evidence.

## Late Steam gyro acceptance failed — 19 October 2026

[Updated target evidence](evidence/INPUT_PUBLICATION_INSTALL_20261019.json): after
user reboot and normal power-on with Steam already running, one approved Resume
attests native 109c and exact input publication. Steam later opens both paired,
readable nodes, but the user reports all three gyro UI rates stay zero. Normal
inputs and independent paddles pass. This is a failed motion-application case,
not a validated complete hotplug fix. No further radio-reconnect attempt or
runtime change follows. Service remains active/enabled and manager unpaused;
installation, native startup and existing basic inputs remain confirmed.
The observer-only three-phase update has 34 offline regressions; it changes no
installed runtime. Release acceptance remains blocked by the unresolved gyro case.

## Subsequent target installation — 19 October 2026

[Evidence](evidence/INPUT_PUBLICATION_INSTALL_20261019.json): revision 10 installed
on CachyOS, matching real DKMS build and all 118 payload files verified. A
separately requested start loads the new module and readiness monitor; service
is active/enabled but management remains paused. Steam integrations and the
sensor opt-in are unchanged. The next read-only precheck finds a new unowned
109c/xpad instance and KDE, not Gamescope; no Resume or hardware test follows.
This closes installation/start checks only, not late-power-on/reconnect or
release acceptance. The preparation checkpoint below retains its original scope.

## Integrated readiness correction — 19 October 2026

Revision `0.1.0.alpha3-10` prepares the optional kernel/client/manager publication
handshake and includes its backend/shared policy in the explicit package list.
[Current implementation and limits](STEAM_GYRO_HOTPLUG.md) supersede the
prototype-only checkpoint below; it is retained as historical evidence.
Module build, complete offline regressions, real-adapter guards and dual-ABI
client checks are recorded separately in `input-publication-offline.json`.
Garuda `7.2.11-1-garuda` and CachyOS `7.2.11-1-cachyos-deckify` builds pass
against their matching prepared headers. CachyOS has zero warnings; Garuda has
zero code warnings and the recorded Clang-version advisory. Only selected
sources are transferred for the unprivileged CachyOS build, not an installer.
No installation, running-driver/Steam change, hardware acceptance, public push
or release/tag is part of this work. Future live acceptance must
prove actual late power-on/reconnect, ordinary input/paddles and retained
sensor/output ownership. Existing opt-ins, GPL/UAPI exceptions and release gates
remain unchanged. The prepared service adds only explicit defer_input selection.

## Offline gyro hotplug preparation — 19 October 2026

The [new discovery study](STEAM_GYRO_HOTPLUG.md) adds 20 device-free SDL runs
and 15 pure policy regressions. A late/unreadable sensor is not assigned to an
already-open gamepad in the four tested libraries; sensor-first hotplug works.
The readiness gate is an unintegrated offline prototype, not a release feature,
new package revision or installable fix. No kernel/production manager, Steam,
system configuration, hardware or remote system was changed or accessed.
Source hashes and sanitized results are in `steam-gyro-hotplug-offline.json`.
Existing feature defaults, licenses and future release/push approval gates remain.
Final `make test` and `make test-sdl` pass with external debug-symbol lookup
disabled for the test processes. The initial ASan negative-control timeout and
corrected packaged-document omission remain recorded in the study and private
logs. No sanitizer check was relaxed. Only the two report documents enter the
package allowlist; the prototype and device-free probes remain development-only.

## Local six-axis persistence follow-up — 19 October 2026

Revision 9's real acceleration extension passed one approved Steam gyro-UI
test with normal input and independent paddles; Eden continued working by
user report. A later file-only approval persisted that same experimental
profile in the existing local modprobe opt-in. Bytes/hash, root:root/0644,
effective options and unchanged running service/module were checked. No
reload, restart, initramfs rebuild or reboot accompanied that file update.
Actual six-axis boot/lifecycle, physical calibration and Proton-game acceptance
remain open. Package defaults remain off. This adds no release or push approval.
[Evidence and scope](STEAM_ACCEL_EXTENSION.md).

## Unreleased SDL/Eden addition — 18 October 2026

The opt-in 109c gyro input path passed offline validation and a separately
approved local installation/activation as `0.1.0.alpha3-8`. In Eden's controller
settings the user confirmed SDL motion, matching direction/sensitivity and
four independently assignable paddles with ordinary input preserved. The
first observer-induced cancellation, manual recovery and separately approved
successful run are retained in [the installation/test report](SDL_EDEN_GYRO.md).
An additional approved local change persisted experimental_gyro=1 in one
modprobe file. Content/rights, effective options and unchanged runtime were
verified without reloading or rebooting; actual gyro boot acceptance is pending.
No new tag or push, accelerometer-axis claim, specific game acceptance or
universal support is added. Existing release checkpoints
below retain their historical scope; the [offline result](sdl-eden-gyro-validation.json)
still describes the earlier device-free preparation.


Current candidate `v0.1.0-pre-alpha.2`, 2026-10-17: the corrected optional
bridge `0.1.0.alpha1-2` passed one approved Forza Horizon 6 / Xodus Nexus run.
Both triggers were felt with pauses/restarts; normal inputs and grip rumble
remained usable and normal exit left the triggers quiet. The relay recorded
171 play/498 stop acceptances, no error, and clean producer EOF. Native
ownership and service remained unchanged. [Evidence and limits](TRIGGER_BRIDGE.md#corrected-integrated-forza-test--limited-acceptance-passed).

The maintainer's conditional authorization for the next push/release now
applies, subject to final source/history/artifact checks. The release remains
source-only and PRE-ALPHA: core `0.1.0.alpha3-6`, Steam `0.1.0.alpha2-1`,
Gamescope `0.1.0.alpha1-1`, bridge `0.1.0.alpha1-2`. Private binary builds,
logs, original captures and development history are excluded. Other bridge
games/runtimes, reconnect, suspend, crashes and multiple devices remain open.
No additional live action or gyro calibration is part of publication.

Local candidate, 2026-10-17: core package revision `0.1.0.alpha3-6` adds a
userspace manager reconnect correction. Kernel sources/ABI, haptics broker,
paddles and IMU calibration are unchanged. Offline regressions and an update
plan are recorded in [MANAGER_RECONNECT_FIX.md](MANAGER_RECONNECT_FIX.md);
installation, activation, hardware acceptance and publication remain separate.

Update 2026-10-17: the sanitized source baseline was published as
`v0.1.0-pre-alpha.1`. The historical preparation audit below retains its
original scope. The new optional [trigger bridge](TRIGGER_BRIDGE.md) is a
subsequent offline-tested change, not part of that tag. It was installed
locally under separate authorization; its integrated hardware acceptance is
still pending. Its separate provenance check precedes source integration;
publication remains conditional on the approved test and release review.
The optional package does not change kernel, manager, paddle or IMU sources.

Earlier local test on 2026-10-17: the first installed integrated Forza/Xodus
trial failed trigger acceptance, although normal input and grip rumble worked.
The relay disappeared before its first recorded output. A manager-busy versus
identity-loss defect was reproduced offline and a correction is being prepared;
the live exit cause was not conclusively logged. This does not invalidate the
older separate bridge result, and that older result cannot validate the new
integration. The maintainer's condition for the next push/release was
**not met at that checkpoint**. The corrected-package test above now records its real outcome;
see [the failed trial and correction](TRIGGER_BRIDGE.md#first-integrated-forza-test--trigger-acceptance-failed).

Date: 2026-10-16. This is a local readiness assessment, not a published release
or permission to install, activate, test hardware, create a remote, or push.
The licensing baseline is commit `6abb83e`, following the paused-calibration
checkpoint `3a3ac91`. Package revisions identify different tested snapshots;
an older hardware result is not a new test of the final release artifacts.

**Decision:** the project can be prepared for a first public **PRE-ALPHA**
with the limitations below. It is not ready to be described as stable,
production-ready, universally compatible, or fully calibrated. Final release
approval and the mandatory publication checks remain open.

## Required public warning

The README must prominently begin with **“⚠️ WARNING: EXPERIMENTAL SOFTWARE”**
and identify the development stage as **PRE-ALPHA**. The warning must cover
crashes/freezes, boot failures, USB/HID conflicts, data loss, and kernel-update
breakage; limit use to experienced users, advise against production-critical
systems, and state own-risk use without guarantees. The complete warning is
maintained in the [README](../README.md). Seven public-documentation tests
now check the complete wording, its position immediately after the title,
both Project Goals sentences, reference-only acknowledgements, links,
licensing and portable public instructions. This is not a hardware safety
certification.

## Feature and support matrix

“Hardware-confirmed” means the particular recorded test passed. It does not
extend that result to every controller, firmware, kernel, or session type.

| Area | Evidence currently available | Public pre-alpha boundary |
| --- | --- | --- |
| Standard G7 Pro, 2.4-GHz dongle, `3537:100a → 109c` | Autonomous bootstrap, native input and IMU reception, controlled return to xpad; later automatic startup confirmed | Supported experimental path; no claim for Bluetooth, wired operation, or unknown PIDs |
| ZZZ edition, `3537:105e` | One 180-second direct-start/input/IMU test and return to xpad; 13 of 15 target button codes actually exercised | Experimental variant in the same driver; complete paddle, motor, Steam, reconnect and long-run validation still missing |
| Garuda KDE | Real installation/DKMS builds, native inputs, one radio reconnect, normal KDE-menu Steam startup and independent paddles | Tested configurations only; matching headers/build tools required; no promise for all kernel updates |
| CachyOS Handheld/Gamescope | Real installation, 150-second native input/IMU test, persistent Steam mapping and one controlled PC-boot/controller-on sequence | Evidence applies to that CachyOS session; it is not universal Valve SteamOS or Steam Deck support |
| Normal gamepad inputs | Buttons, D-pad, both sticks and both analog triggers received; full ranges observed | No established long-term drift, latency or polling-rate guarantee |
| L4/R4/L5/R5 | Independent Linux codes 704–707; four independent Steam paddles, combinations and releases confirmed with the optional integration | Steam Input can map their actions; ordinary XInput games do not gain four new native XInput buttons |
| Four physical motors | Twelve native single-motor impulses, including both triggers, felt and stopped while input/IMU continued | Confirms the packet/runtime foundation, not universal four-motor game support |
| Standard game rumble | `FF_RUMBLE` for the two grips, game-controlled duration and renewed short hardware leases implemented and offline tested | No artificial one-second game-effect limit; final current-build application/stop smoke test remains open |
| Independent trigger rumble | Versioned local four-channel broker/API implemented and offline tested | Applications need an explicit adapter; the tested SDL evdev trigger API reports unsupported; no invented Linux FF UAPI |
| IMU | Six changing raw channels observed on both models; experimental acceleration conversion is replaceable | Gyro scale, physical axes/signs and bias are not calibrated; no calibrated SDL/Eden claim |
| Coherent IIO buffer | Implemented, offline-tested, separately installed/registered; last documented buffer state is disabled | No real coherent-buffer capture or known-angle measurement; gyro calibration is paused |
| Firmware and configuration | Static research only | No firmware updater, flashing, bootloader support, or automatic manufacturer-app configuration |

Hardware evidence: [standard startup](HARDWARE_TEST_003.md),
[CachyOS bootstrap](BOOTSTRAP_CACHYOS_FIX.md#revision-4-korrigierter-bootstrap-realtest-bestanden),
[controlled Gamescope boot](STEAM_GAMESCOPE.md#kontrollierter-neustart-am-15-oktober-bestanden),
[KDE Steam persistence](STEAM_INTEGRATION.md#reale-anmeldung-und-normaler-kde-menüstart-bestanden),
[ZZZ test](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026),
[native motor comparison](NATIVE_MOTOR_COMPARISON_RESULTS.md),
[local haptics API](HAPTICS_API.md), and
[paused coherent-sensor work](COHERENT_IMU_CALIBRATION.md).
These are dated records; their old machine states and consumed approvals
are not current installation instructions.

## Completed preparatory checks

PASS below describes repository or offline evidence. The clean source-copy
test covers the local preparation tree; it does not certify a future release
commit, running system or untested race.

| Check | Result and scope |
| --- | --- |
| License decision | PASS: own project code/documentation uses GPL-2.0-only; full GPL text and the UAPI Linux-syscall-note exception are present. `MODULE_LICENSE("GPL")` remains valid. |
| Provenance review | PASS within the documented review: own sources compared with saved references, historical own parser preserved; no identified imported implementation blocks. This is not exhaustive legal clearance. |
| Licensing/package regression | PASS at `6abb83e`: 124 source/config files checked, one intentional UAPI exception; 25 DKMS packaging tests cover exact license bytes, modes, archive/staging destinations and missing-license rejection. |
| Current licensing/package regression | PASS for this preparation: 125 source/config files, including the new README test, retain the correct SPDX identifiers; one intentional UAPI exception. All 25 DKMS packaging tests pass with the new public guides in the source/staging allowlist. |
| Public README review | PASS: seven tests verify the exact warning, goals, original-project links, reference-only wording, license links and absence of personal paths/hostnames in the three public entry guides. The historical README remains available in Git; detailed evidence documents are retained. |
| Official reference repositories | PASS: the Deadband and g7ctl repository pages were checked read-only on 2026-10-16 and linked directly. This acknowledgement does not imply participation, collaboration, endorsement or developer support. Fixed provenance references remain in `LICENSING.md`. |
| Full offline suite | PASS for the updated working tree (`build/prealpha-readme-tests.log`) and an isolated copy of all 237 intended source files (`build/prealpha-public-readme-audit/tests.log`). The copy has no `.git`, private `.local` data or pre-existing build products. It is based on `6abb83e` plus this preparation, not a tagged release. |
| Portable installation/removal instructions | Reviewed: matching headers, separate installation/activation, DKMS checks, optional Steam/Gamescope packages, honest USB-identity recovery and guarded removal of retained state are documented in `INSTALLATION.md`. Commands were inspected and syntax-checked, not executed on the running system. |
| Historic repository-content review | Reviewed before `6abb83e`: 91 commits and 946 blobs, with no detected secret, vendor binary or raw-capture payload in the reviewed history. Subsequent changes still require review. |
| Final privacy check through `3e620f3` | NO-GO for unchanged history/tree: personal commit email, home paths and machine labels found. All 93 commits/1,037 blobs and the 237-file tree were inspected; no identified credentials or vendor/raw-capture payloads. Prepare separate sanitized source artifacts; see `PUBLIC_RELEASE_CHECK.md`. |
| Repository destination | No configured remote, release tag or published release at this audit's starting check. No public destination has been invented. |
| Runtime safety changes | The known FF ownership bug and bootstrap/error-reporting defects have targeted regressions and limited follow-up hardware evidence; see the boundaries below. |

The test logs and source-copy inventory are local ignored build outputs, not
public release assets. The source-copy inventory records per-file hashes and
its baseline; final documentation and the repository checksum manifest are
reviewed separately before the local commit. No new hardware result, kernel
module build, live installation or complete live removal is claimed here.

See [licensing and provenance](LICENSING.md) for original license hashes,
upstream source references, preserved historical licenses and redistribution
boundaries. License compatibility does not itself establish upstream acceptance.

## Open publication gates

These checks must be completed against the selected final source commit
before calling an archive or tag the public pre-alpha release.

| Gate | Required completion |
| --- | --- |
| Clean public source copy | Completed for this local preparation: the full default offline suite passes in the 237-file copy. Freeze and recheck the selected publication commit and any offered artifacts; optional private-capture/SDL checks remain separate. |
| Final source/package alignment | Rebuild any offered source or Arch/DKMS packages from the chosen release commit; verify contents, complete corresponding sources, license notices and SHA256 checksums. Existing historical packages are not automatically releasable. |
| Public content and history | The original history/tree is blocked by personal metadata and historical paths. A separately sanitized source snapshot can be reviewed independently; no existing history is approved for push. Preserve private originals and obtain a separate history/identity decision. |
| Current documentation | Completed for this preparation: exact warning, goals, reference-only thanks, feature/support boundaries, recovery/removal and known issues reviewed and regression-tested. Review again if the selected release tree changes. |
| Owner approval | Obtain explicit approval of the repository destination, visibility and release scope before creating a public repository, remote, tag, upload or push. |

## Open validation and claims

The following are open engineering checks, not already passed release tests.
A limited public pre-alpha may leave them open **only with the corresponding
limits explicit**; stable support or the untested feature must not be claimed.

| Open check | Present boundary |
| --- | --- |
| Current-build game force feedback | Verify longer grip effects, expiry, explicit stop, application exit and independent channel behavior. Older manual motor pulses and fake ioctls do not close this application chain. |
| Suspend/resume and resets | PM code and simulated regressions exist; real suspend/resume reliability is not established. |
| Hotplug, repeated radio reconnect and multiple dongles | Limited reconnect/boot evidence exists; repeated cycles, rapid same-port replacement, hub changes and concurrent controllers are not generally validated. |
| Additional kernels/distributions | DKMS is intended to rebuild for matching installed headers; untested generic kernels, ABI changes, signing/Secure Boot and other distributions remain unsupported claims. |
| Full deinstallation on hardware | Packaging guards and recovery paths are offline-tested, with controlled release/update records; a complete final-version live package-removal and functional fallback acceptance is not established. |
| Initial `109c` at boot | The manager deliberately does not adopt an unrelated pre-existing `109c` instance. Boot with an already-on controller and no fresh `100a` enumeration needs a separate test/solution. |
| Precise gyro/SDL sensors | Calibration remains on ice. No range may be selected from the five diagnostic hypotheses and no gyro factor may be derived from 8192 LSB/g. |

## Known safety limits and failure history

The previous FF-private ownership defect was a confirmed use-after-free/
double-free risk. The fix and targeted negative controls are documented in
[FF_LIFETIME_FIX.md](FF_LIFETIME_FIX.md). One later controlled radio cycle
passed. This does not prove that every earlier freeze had the same cause,
that graphics-path failures were unrelated, or that all races are removed.
The original [freeze investigation](SYSTEM_FREEZE_20261014.md) remains intact.

The initial userspace xpad-unbind and fallback bind are not fully atomic
against extremely rapid replacement at the same port. Kernel instance checks
prevent an unchecked bootstrap but cannot erase that userspace timing window.
See [ownership and runtime limits](ALPHA_RUNTIME.md). A still-`109c` device
bound to xpad is not proof of a successful mode return to `100a`; failed
recovery must be reported honestly and may need the documented manual path.

The earlier non-felt 400-ms left-grip pulse was not causally explained by the
later successful 1-second comparison. Unknown successful type-`0x03` reports
remain distinct from USB transfer errors. Neither finding permits an
unqualified claim of perfect rumble or complete protocol coverage.

No installation, service/module/binding change, USB command, new recording,
gyro measurement, public upload or push is authorized by this audit.
