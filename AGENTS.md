# GameSir Native Linux — contributor rules

## Project goal and release stage

Native, community-driven Linux support for the GameSir G7 Pro: gamepad
inputs, independent paddles, raw IMU and four motor channels. PRE-ALPHA only;
read README.md, docs/RELEASE_AUDIT.md and docs/PUBLIC_RELEASE_CHECK.md first.
Wider support and Linux-kernel inclusion are long-term goals.

## Work rules

Read the project state and existing implementation before changing it.
Extend existing code, keep changes small and distinguish confirmed evidence,
hypotheses and open questions. Run suitable offline tests and commit completed
changes locally. No public remote, tag, upload or push without explicit
maintainer approval. Preserve third-party notices and source provenance.
Own sources use GPL-2.0-only; preserve the UAPI Linux-syscall-note exception.

## Standalone startup preparation (19 October 2026)

Current publication request: the maintainer explicitly authorizes integrating
the accepted wait policy into package installation, updating README, pushing
the reviewed full source and creating a new tagged PRE-ALPHA release. Revision16
ships same-basename vendor modprobe defaults under /usr/lib, preserving /etc
local overrides. Kernel runtime is unchanged from accepted revision15; no
live installation or hardware test is included. Review commit/function/package
coverage, tests, privacy/history and source-only assets before publishing
v0.1.0-pre-alpha.3. Optional userspace and experimental gyro boundaries remain.

Maintainer acceptance, 20 October: the demonstrated revision15 automatic
binding is accepted as a usable current state. The reported brief initial
xpad/SteamOS reaction is not a blocker and does not require further live
investigation now. Its actual cause remains unproved; do not turn the SteamOS
suggestion into a technical finding or claim completely xpad-free first probe.
Keep scoped cold-boot/reconnect/application tests distinct from this acceptance.
No system change, additional test, push or release is authorized by acceptance.

Latest approved revision15 late-on run: read RELEASE_AUDIT's newest entry and
docs/evidence/RECEIVER_WAIT_LATE_ON_20261020.json. Fresh waiting lifetime and
options reattested; observer armed before cue; maintainer confirms one power-on
without additional inputs. New100a lifetime received controlled startup to
native109c state7/error0/pad1/imu1/handover1, exact input publication, correct
pad/motion names and 10.415 seconds stable active ownership. Final readiness
belongs to the new lifetime; budget2 represents old wait plus new source,
not same-instance replay. No new error, manual bootstrap/Resume/Release
or service change. Human reports initial xpad; samples first see100a already
native and cannot time-resolve first binding. Initial reply overclaimed that
independent proof; correction is retained. Fully xpad-free first probe, cold
boot/reconnect and new application acceptance remain open. No further live
input, power cycle or system changes follow from this completed approval.

Latest approved revision15 receiver-off insertion check: read the newest
RELEASE_AUDIT entry and docs/evidence/RECEIVER_WAIT_CHECK_20261020.json.
Fresh baseline matched; maintainer reinserted receiver, controller remained off.
Kernel bootstrap state9/error0/zero pad+IMU, manager/saved lease receiver_wait;
ten read-only samples confirm 45.653 seconds, unchanged lifetime/tokens and one
start-budget entry, one matching bootstrap result, no new faults/xpad return.
The private observer first stopped on raw/stripped service newline mismatch
and an empty-list renderer defect. Preserve originals; offline controls pass;
new reader completed without runtime/guard-field relaxation. No USB trace or
independent wire-level no-OUT measurement. Current target has the receiver
plugged and native waiting; no manual bootstrap/Release/Resume/service change.
Controller stays off: require the maintainer's separate explicit Go before
power-on. No late-on, cold-boot/reconnect/game acceptance or push is implied.

Revision15 installation/activation completed under explicit staged approval;
read the newest RELEASE_AUDIT entry and docs/evidence/RECEIVER_WAIT_INSTALL_20261020.json.
Actual receiver removal, continuous absence and one explicit Release proved
paused/returned/empty ownership before the single update and normal hooks.
137 payload files match, target DKMS installed; one opt-in config and one
service start load the expected module/sensor/wait flags. Immediate status
ENOENT stopped the guard before Resume; independent readback proved the same
responsive paused service. Only the still-unused approved Resume then ran;
no repeated config/start/error Release. Current target: active/enabled, zero
restarts, unpaused empty devices/leases, receiver removed/controller off.
No actual state9/late-on/game/boot acceptance or push. Never interpret empty
Resume as readiness or reuse consumed one-shot helpers. Further physical
insertion/power-on tests require separate approval. Other host unchanged.

Revision-15 target preparation, 20 October: read docs/RECEIVER_WAIT_UPDATE.md.
The maintainer authorized fresh read-only SSH inspection and an unprivileged
build for the current CachyOS kernel, not installation/activation. Matching
7.2.11-1-cachyos-deckify build passes W=1/-Werror without warnings. Revision14
remains loaded/installed, service active/enabled; current 109c/xpad has an
unresolved blocked current-boot lease and retained original -110 VERIFY5.
Do not install against it or bypass the package cleanup hook. Proposed next
approval must first cover physical receiver absence, one explicit Release,
verified paused/returned empty devices and persisted leases, then exact pinned
package15 and opt-in receiver_wait configuration/start/Resume in stages.
No state clearing, initialization replay, hardware test or push. Sensor/Steam
configuration is preserved and real late-on behavior remains unvalidated.

Latest authorized offline implementation, 20 October: read
docs/RECEIVER_WAIT_KERNEL.md. Experimental receiver_wait defaults false and
requires persistent/bootstrap/output modes; no packaged setting enables it.
Append WAIT_RECEIVER=9 without renumbering statuses or resizing private ABI.
After one bounded setup, keep RX but generate no OUT until fresh native IMU
allows one bounded runtime handoff. No button/neutral/PID/status RF inference,
init replay, heartbeat polling or budget consumption while waiting. The ioctl
returns pending; updated ctl/manager attest tokens, persist receiver_wait and
only poll read-only. Restarts reattest, never reinitialize. Root END cancels
the exact waiting instance; late worker faults retain the first error and are
locally END-able. Waiting suspend/reset/shutdown cancels; no automatic unready
PM restart. Real 109c fallback may still require manual return. Existing active
runtime, input publication, gyro scale, motors and Steam settings are unchanged.
Offline day-long/core/actual-kernel/manager/client regressions and local build
are required; no hardware acceptance is implied. Installation, activation,
remote build/read and live tests still need separate approval. No push.

Latest offline PID-transition comparison, 20 October: read
docs/RF_PID_TRANSITION_COMPARISON.md and its sanitized evidence JSON. Eleven
original captures rehash correctly; four recorded 109c->100a transitions are
identified: one labelled passive power-on association, three software-return
contexts. No synchronously labelled 100a/controller-off negative control is
established; absence of that control does not prove 100a means RF connected.
The coarse 14 October off confirmation cannot time-label its intermediate
100a. Preserve current versus historical boot/lease separation. A PID edge
may prompt exact-instance discovery, never confer connection/ownership/retry
authority. Prefer kernel receiver waiting with a thin ownership/recovery
manager; no implementation, timeout relaxation or initialization replay is
authorized by this research. Offline only; no live access, installation or push.

Latest offline connection-witness review, 20 October: read
docs/RF_LINK_CONNECTION_WITNESS.md and evidence/RF_LINK_WITNESS_20261020.json.
7,195 selected records independently match the saved capture; all 3,571 new
100a EP82 reports are full 20-byte 00/14 XInput. Eleven initial reports are
identical/all-neutral, not a sufficient RF-connected proof. First changed
input follows a 34.707839-second gap; do not infer disconnect from pad silence
or require a button press/nonzero stick for automatic startup. Keep HID IDs
3/9 separate from native GIP status; their zero reports and LED output are
not an IMU activation proof. Four c1/01/0100/0000/20 queries succeed, but their
necessity/sufficiency remains unproved. Preserve exact-instance ownership,
first errors, native init/fresh-IMU READY and all motor STOP guards. No receiver
waiting/automatic retry fix is implemented by this evidence. Original -108
belongs to the old lifetime. Raw exports remain private; offline only, no
production code, new capture, live read or push. Last verified Native state
remains paused/empty; this review does not establish a fresh runtime state.

Latest approved RF reference completed, 20 October: read the completed section
of docs/RF_LINK_109C_CAPTURE.md and sanitized RF_LINK_109C_CAPTURE_20261020.json.
After separate successful KDE-consumer and usbmon gates, one fresh read/recording
was approved. Local terminal GO, 30 s preparation and explicit human connection
confirmation preceded the input phase. Recorder/terminal exit 0, isolation and
finalization pass; 24 original chain entries independently verified. User confirms
KDE-visible input and normal responsive system afterward. Receiver stayed plugged
but naturally re-enumerated from 109c/xpad to a new 100a/xpad+usbhid lifetime.
Keep both epochs separate. Old -108/zero-length completion belongs to shutdown
of that first lifetime, not proof of a reproduced native startup fault. Offline
metadata-only review finds 3,571 successful 20-byte EP82 completions after new
enumeration, two short EP84 reports and no 64-byte completion in selected target
traffic. Do not infer a radio-ready bit, mandatory Hello/ACK, absent IMU globally
or an activation recipe. No payload export in this review. Native remains
paused with empty ownership; no Resume, retry, reset or forced mode command.
Capture permission is consumed. Preserve private raw/source/terminal/checksum
evidence; no raw bus traffic/host identifiers in Git and no push. A new live
action needs new authorization. No production driver or manager code changed.

Latest offline preflight diagnostic correction, 20 October: read the diagnostic
section of docs/RF_LINK_109C_CAPTURE.md. The separately approved first inspect
failed its old compound baseline/consumer gate with empty stdout. Retain original
private stderr, authorization and checksum receipts; the actual missing condition
cannot be recovered. No retry occurred. The refined inspect emits version-2 JSON
on failure as well as success, retaining first stage/type/message, manager output,
field-level cached details and explicitly untested later stages. Distinguish no
IF0 input node, an existing unopened node, missing attributes, wrong bindings and
inaccessible inspection. Do not infer radio state from any of these. `prepare`
requires explicit ok=true/no failure; never reuse an intermediate manifest from
a failed report. Runtime snapshot/identity/ownership guards remain unchanged.
58 RF tests and full make test pass offline. No new host/SSH read, capture,
module, binding, service or installed change; no push. Old approval is consumed
and source pins have changed; a further read requires fresh explicit approval
and a new private output directory. Controller remains reported off/Native
last verified paused; no current state is invented from synthetic fixtures.

Latest offline RF recorder preparation, 20 October: read
docs/RF_LINK_109C_CAPTURE.md before using rf_link_capture.py. It is a new passive
109c/xpad/90 s scope, not relaxation of the legacy 100a HID profiles. Default/
prepare/validate are file-only; inspect and capture are separate approved gates.
Require fresh live/persistent pause, empty ownership, no native bindings, exact
standard-model IF0 consumer and no foreign raw access. Controller stays off
until the 30 s cue after local GO; connection confirmation before 60 s is human
evidence only. Keep epochs distinct across natural same-parent 100a/109c USB
re-enumeration; unknown metadata has bounded grace, never connection authority.
No replayed initialization, mode command, module load or return operation exists
in this path. Preserve original errors and private whole-bus artifacts. Source
pins and all sandbox/stop/checksum guards remain required. New RF profile has
offline tests only, no live validation. This step performs no host/SSH read,
recording or runtime change. Native remains last verified paused/empty, receiver
plugged/controller reported off. No push; future use requires new approval.

Latest primary physical-return attempt: staged approval executed one removal
and one same-port reinsertion with controller confirmed off. Fresh precheck
matched; after >=15 s post-confirmation, protected absence read proves leases/
devices empty, returned=true and pause retained; original -108 history records
physical absence. Reinsertion is a new same-parent/source/boot USB lifetime but
still 109c/xpad, IF1 unbound, not 100a. Read RF_LINK_CAPTURE_PLAN.md final section
and RF_LINK_100A_RETURN_ATTEMPT_20261020.json. Stop at PID mismatch; no repeat,
recording, power-on, release/resume or module/binding/reset operation. Native
remains paused with empty ownership. returned=true describes that managed set,
not 100a or tested RF/input functionality. Don't claim power cycling guarantees
mode return or invent a mode command; clean 109c/xpad capture is a new scope.
Preserve consumed physical approval, private phase evidence/checksums and fault
history. Receiver remains plugged/controller off; no push.

Latest primary-machine 100a return preparation: user selected an xpad radio-on
reference and requests steps/cues for approval, controller off/native paused.
Read RF_LINK_CAPTURE_PLAN.md's manual-return section and its preparation JSON.
No fresh privileged read, removal, reinsertion or capture in this step. Private
read helper with -B/source pins is prepared, not executed. Installed-source
pure-method fake-host checks validate ten-second continuous known-absence
retirement, unknown-metadata reset, original diagnostic retention and no paused
acquisition. Plan: fresh paused 109c baseline -> cue remove -> at least 15 s out
and prove absent/leases empty/returned=true -> cue reinsert -> prove fresh 100a
xpad/usbhid endpoints with pause retained. Stop on deviation; don't promise
100a, infer retirement from time or use a guessed mode/return command. No new
release/resume/stop/module action or recording; physical/read steps await
explicit approval. Last verified primary receiver remains paused 109c/xpad.

Latest primary-machine release checkpoint: explicit approval covered one release
and readback only, controller off, no capture/resume. Fresh precheck matched
source/boot/state/USB. Exactly one release completed exit 1 paused=true and
returned=false. Protected postcheck confirms persistent/live pause, unchanged
109c/xpad binding, one unchanged blocked old 100a lease and original diagnostics.
Read RF_LINK_CAPTURE_PLAN.md and docs/evidence/RF_LINK_RELEASE_20261020.json.
Inhibition passes; complete return/empty ownership does not. Preserve the
consumed receipt, raw private reports/checksums and old fault; don't repeat,
resume, stop/restart, clear state, unplug or power on from this approval.
No capture, module or explicit binding operation; no push. Further recovery
and the reference recorder remain separately reviewed/approved work.

Latest primary-machine pause preparation: a newly requested protected ownership
read matches unchanged boot/state/USB before/after. One blocked old 100a lease
has no kernel tokens/candidate/job; current 109c/xpad is a different device inode
at the same parent. Read RF_LINK_CAPTURE_PLAN.md's controlled-pause section and
RF_LINK_PAUSE_PREPARATION_20261020.json. The actually installed manager was
reviewed and its three pure methods simulated offline with fake host methods:
one release would persist pause without END/restore for this blocked replacement,
preserve the lease, return false; unresolved resume is rejected. Client waits
up to 45 s polling status. No actual release/stop/resume occurred. Proposal is
one separately approved release after fresh source/ownership check, then only
readback. Don't equate pause with returned=true, retry, clear state, remove the
receiver or power on from preparation alone. No capture or system change.
The protected reader created one local root-owned bytecode cache; the exact
source-matching cache was removed and license checks pass afterward. Use -B
for future root Python helpers/imports; never reuse the consumed reader.

Latest primary-machine read checkpoint: one approved rf_link_preflight inspect
stopped at its manager-fault gate. Read RF_LINK_CAPTURE_PLAN.md and sanitized
RF_LINK_PREFLIGHT_20261020.json in docs/evidence. Actual observed IF0 is xpad,
PID109c; manager unpaused/blocked with unowned replacement and stored -108
bootstrap error at stage1. This is not the other-host -110 VERIFY failure and
not a fresh native-control query. Only manager status ran; all subsequent reads,
monitor access and capture were skipped. No release/resume, module/binding
change or power-on cue; don't reuse this one-shot approval. Preserve original
private output/checksums. xpad binding alone proves neither empty leases,
100a return nor cleared management. Any pause/recovery or capture requires a
separately approved concrete step. Controller remains reported off/dongle in.

Earlier capture preparation targets the primary KDE machine, not the separate
Gamescope host. User reports receiver plugged/controller off; only preparation
is authorized. Read docs/RF_LINK_CAPTURE_PLAN.md. The new rf_link_preflight.py
defaults to a file-only plan; inspect is a separately approved root read with
fixed status/package/service/journal commands and cached metadata, no device
open or automatic recovery. Twelve fake-backend tests cover it. No inspect was
run. Existing recorder scopes cannot be reused for radio re-enumeration. Fresh
read baseline, reference-path choice and reviewed recorder need separate gates.
The user asks whether xpad is the better reference; no deactivation approved.
Never confuse 100a/XInput with 109c/GIP, infer receive silence from a quiesced
native fault or assume the prior other-host blocked state on this machine.

Latest offline prototype, 20 October: read docs/STARTUP_TIMELINE_PROTOTYPE.md.
The separate file-only startup-replay models receiver waiting, Hello, observed
START submissions, tentative status bits and separate pad/IMU observations.
Thirty new tests plus 23 private saved-payload classifications cover five
historical timelines; no live capture or RF-off contrast is established.
Never treat candidate/observation phases as native ownership, recovery, RF
connection or automatic start authority. Silence expires observations only;
first errors and terminal instance boundaries persist. No production callback,
transport, retry loop or manager/kernel integration was added. Keep the saved
boot/enumeration epoch explicit; do not infer detach or boot from EOF/addresses.
The maintainer reports controller off/dongle attached; no SSH/target inspection
or installed change occurred. Previous blocked state remains unverified; no
hardware test, installation, push or precision calibration is authorized.

Latest authorized online research, 20 October: Microsoft GIPUSB documents
Hello → START → status/input; type 03 normally follows START and later repeats
at 20 s, so it is not a prerequisite for sending START. Two saved GameSir Hello
reports match the full standard field layout. xone uses status payload bit 7 as
connected; all 51 positive GameSir status reports set it, but no bit-clear/off
contrast proves G7 semantics. Do not confuse it with SDL extended device-active.
Pinned xone/SDL code is cached privately, not executed/imported. Read the final
online cross-check in docs/DUALSENSE_STARTUP_GAMESCOPE.md and protocol research
rows. Plan a passive offline state prototype with announce-led and already-
streaming paths; no prototype implemented yet. No new raw synchronized G7
receiver-off/late-on recording found in the checked public pages, not a global
absence claim. No SSH/hardware/installed change or push; target remains blocked.

Latest offline saved-capture search, 20 October: read the final connection
chronology in docs/DUALSENSE_STARTUP_GAMESCOPE.md. Ten originals rehashed;
nine contain identified traffic; 106 selected frames independently match
Wireshark payload/endpoint/stage/timing. Four native-enumeration epochs show
unknown/status-or-announce → pad → IMU (pad-to-IMU 514–606 ms), but three start
init before that unknown report. Type 03 is periodic (51, constant payload),
type 02 ANNOUNCE occurs twice, and an already-streaming capture starts with
IMU before status/pad. Never turn these into a mandatory RF-ready bit or ACK.
Returned-100a IMU-shaped bursts use HID EP84, not native EP82. Confirmed radio
cycle logs show USB re-enumeration with dongle plugged but no raw RF-edge
payloads. xpad delayed-init-on-announce is a relevant design for other hardware,
not a proved G7 quirk. No raw synchronized off/on control is established in
this selected corpus. Preserve ownership/lifetimes and unknown states. Analysis
only; no SSH/hardware/installed change, initialization replay or push.

Latest offline architecture review, 20 October: rechecked the pinned Sony/SDL
sources against saved controller-off reboot evidence. Read the final manager
review in docs/DUALSENSE_STARTUP_GAMESCOPE.md. Retain a thin acquisition/admin
manager for now; ordinary receiver/link/runtime lifecycle belongs in the kernel
with a distinct waiting contract. Direct discovery starts too early, but the
terminal three-second IMU gate is in shared kernel-used C, so removing Python
or lengthening a timeout alone is insufficient. PS4 dongle has a real status
bit and kernel connection states; PS5 HID attachment is a different topology.
No GameSir equivalent RF bit or proven init-once/late-data contract is known.
Do not guess one, add unconditional retries/heartbeats, weaken identity/STOP,
add USB aliases or alter publication as an unreviewed side effect. Existing
56 manager and shared-C ASan/UBSan startup checks pass; they characterize the
old behavior, not a fix. Analysis/documentation only; no SSH, hardware, runtime
change or push. Installed blocked instance/recovery remains unconfirmed.

Latest revision-14 restart checkpoint, 20 October: the maintainer rebooted with
the receiver connected and confirms Gaming Mode ready, radio controller off,
no manual start/Resume. Fresh unprivileged readback proves a new boot, correct
package/module, service active/enabled with zero restarts and native IF0 binding.
The separately approved single protected status read shows a BLOCKED direct
109c bootstrap: state=8, error=-110, failed_stage=5, pad=0, imu=0. The outer error
is "Return deadline: still 109c; manual attention required"; actual owner remains
gs_native. Autoload passes; healthy startup/recovery does not. Do not equate
native binding with readiness or claim successful fallback. Stop before radio
power-on; no Resume/release, retry, state reset or rebind is authorized here.
Documented push prerequisite remains unmet. Preserve the connection/state and
original diagnostics; no push or other-host change. Prior application gyro and
paddle successes remain valid only for their earlier running session. The
activation/checkpoints below are historical.

Latest activation checkpoint, 20 October: the maintainer requested starting
revision 14. Fresh checks matched the stopped/enabled/paused/absent baseline;
one service start loaded the verified module/profile, followed by one Resume
while the receiver was absent. Service is now active/enabled and unpaused.
The maintainer then reports automatic radio power/connection on removal from
the charging cradle. Readback confirms direct-109c bootstrap success, matching
native lease/kernel tokens, pad/IMU reception and exact input publication.
Original failure history is preserved. Normal Steam inputs and four independent
paddles pass. Although all three Steam gyro UI values remain zero, the maintainer
subsequently confirms SDL gyro recognition in Eden and actual gyro-controlled
camera movement in Arc Raiders, in the announced Steam Input right-stick test.
Treat application gyro use as positive for this run and the display discrepancy
as deferred TODO. Its exact internal cause is unproved; Guide independence,
neutral drift and all reconnect/startup cases were not separately reported.
This is not the planned receiver-present/controller-off late-power-on or a
cold-boot test. A transient xpad gamepad is in the journal; do not claim no xpad
probe, or that the revision-14 returned-timeout branch was exercised.
No additional system/Steam/driver change, automatic retry or push follows from
these reports. Keep the current connection intact.
The installation-only checkpoint below is historical.

Latest installation checkpoint, 20 October: explicit approval covered transfer,
physical removal after cue, one manual release, the exact revision-13-to-14
package transaction/hooks and readback only. All completed successfully.
Read RELEASE_AUDIT.md#revision-14-installed-on-cachyos--20-october-2026.
Absence was freshly verified, release returned paused/returned/empty ownership;
eleven updater tests passed before the new one-attempt guarded transaction.
Target DKMS/srcversion and all 128 regular payload files pass; sensor/Steam
configuration and original failure history are preserved. The service is
inactive/dead/enabled, management paused, module absent, dongle absent, leases
empty. No activation/Resume/reboot or hardware acceptance followed. Leave the
dongle out until the next approved step. Preserve consumed receipts, backups,
fixed-hash source/package and rollback 13; no reuse, other-host update or push.
The following preparation/checkpoint paragraphs are historical.

The later maintainer request authorizes revision-14 preparation and fresh target
inspection/build, then concrete update/test commands for approval. Do not install
or activate from preparation alone. Steam may stay open; games/Eden/Deadband are
confirmed closed. Preserve the currently native target, rollback package, sensor
and Steam settings. Package revision 14 changes only manager runtime code and
adds the diagnosis/Sony comparison to the document allowlist; kernel behavior
is unchanged. Three user-led successes with controller powered before receiver
insertion are observations on installed revision 13, not acceptance of this fix,
proof of no transient xpad binding, sensor tests or a Steam-causation finding.
No other-host update, public push or precision calibration is authorized.

Revision-14 preparation now passes: source 54d70fc, fixed-hash package, 128
regular payload files, local client self-test and 25 packaging tests. Fresh
protected state is active/unpaused with one healthy native lease; rollback 13
is verified. Target GCC module build passes without warnings; final metadata
is unchanged. Read the latest RELEASE_AUDIT.md artifact record. Package transfer,
release/removal, installation and activation have not occurred. Obtain concrete
update approval and freshly verify physical absence, pause, returned=true and
empty ownership before installation; do not reuse a consumed helper or assume
empty leases alone establish return. Activation/Resume and hardware acceptance
remain separate. Preserve the frozen source/package across later doc commits.

Latest offline implementation, 20 October: the separately requested manager fix
now retires only an attested and successfully ended direct-109c no-data VERIFY
timeout when a new unattempted 100a is observed on xpad at the same hub lifetime.
Read REVISION13_FIRST_START.md and DUALSENSE_STARTUP_GAMESCOPE.md in docs/.
Defer fresh discovery to the next complete scan; retain old attempted tokens,
first diagnostics, pause, exact ownership checks and the three-start budget.
Never migrate already-suppressed historical state, retry the failed instance,
reuse old cleanup authority for a replacement or generalize to other faults.
56 manager tests, seven added shared-C sensor cases and full offline tests pass.
The raw first-IMU cause remains unknown. Sony's native HID/paired evdev path
and PS4 dongle's explicit connection state are design references, not GameSir
commands or RF-bit evidence. No kernel behavior/ABI, packet, sensor profile or
deadline changed. Local build only; no SSH, install, hardware test or push.
Installed revision 13 remains unchanged; later packaging/acceptance is separate.

Latest read-only follow-up, 20 October: the maintainer independently activated
revision 13 and reports xpad on first power-on, GameSir after another radio cycle.
Read docs/REVISION13_FIRST_START.md. Fresh checks confirm the expected module,
automatic active/enabled service and an unpaused, attested native runtime.
Two saved epochs show direct-109c VERIFY timeout with pad/IMU=0, then a new
100a/xpad retained as observed return, followed by successful direct 109c.
The actual manager reproduces the intermediate released/attempted suppression
offline. The missing first IMU's RF/firmware cause remains unproved; do not
attribute it to the 100a-only query, missing module load or a required button.
No live test, runtime/driver change or push occurred. Preserve original errors,
attempt/budget/ownership guards and the currently working session. Further
correction and hardware acceptance are separate. The checkpoints below are
historical, including their activation-pending state at installation time.

Latest checkpoint: revision 13 is now installed on the CachyOS target after
explicit approval of physical removal/readback and a new conditional update.
Read RELEASE_AUDIT.md#revision-13-installed-after-verified-physical-removal.
Dongle absence, paused management, returned=true, empty devices/leases and
no native bindings were confirmed before the new one-attempt guard ran.
It pins that absent baseline and requires verified return, not just empty leases.
Eleven offline helper tests passed. Transfer, one package transaction, all hooks,
126 regular payload hashes, DKMS and target srcversion
8207CE72AE527F13E1D1B1D passed. Service inactive/dead with enabled setting
retained, management paused, module absent, dongle absent and ownership empty.
Sensor/Steam settings and original failure history remain intact. No activation,
Resume, reboot or cold-start/functional test was performed. Leave the dongle out
until an explicitly approved next step. Preserve both consumed attempt receipts,
private reports/backups and revision-12 rollback artifact; do not reuse helpers.
The installed package is the original fixed-hash ec7adf8 source artifact, not
rebuilt after these documentation updates. Local docs commit only; no push.
The following abort/preparation paragraphs are historical checkpoints.

Historical first attempt: the explicitly authorized one-shot revision-13 transfer
and update was attempted and STOPPED by the installed revision-12 pre-hook.
Read RELEASE_AUDIT.md#revision-13-update-stopped-before-package-replacement.
No package was upgraded. The old blocked 100a entry still observes an unowned
109c/xpad replacement, so release cannot confirm returned despite empty leases.
The hook set persistent pause, then stopped before service stop/module unload;
revision 12 remains intact, loaded, active/enabled but paused, with no native
binding. Sensor/Steam files and error history are unchanged. One pre-snapshot
was created. Do not rerun consumed local/remote receipts, bypass the hook,
force-stop/reset state, Resume, activate or reboot under that spent approval.
Next step needs authorization for manual physical removal and read-only
absence/ownership confirmation; leave the dongle out until the next instruction.
Then prepare a newly guarded single update against that fresh baseline.
An empty lease table is not sufficient proof that manager release can succeed:
check the existing entries and actual PID as well. No new runtime attempt or
push; calibration remains paused. The following preparation scope is historical.

Current authorization: prepare revision 13 with the captured xpad control-IN
startup request, offline regression tests, fresh read-only target inspection
and an unprivileged target-kernel build. Show the concrete package transaction
for separate approval; do not install, activate, Resume, reboot or hardware-test.
Read docs/ACQUISITION_AUTOPROBE_FIX.md and docs/STANDALONE_STARTUP.md.
The query is allowed only in the explicit 100a bootstrap after native ownership
and IN reception, once before its first mode-switch OUT. Exact known setup,
20-byte response, 25-ms USB timeout; no retries, guessed command or query on
109c/105e/probe/status. Preserve first failure and recheck identity/deadlines
after the sleeping transfer. Its hardware necessity is still unproven; Xbox
certification and the Guide ring do not establish it. Keep the manager's one
strict pre-write autoprobe recheck, old blocked attempts, budgets/pause and
cleanup authority. No automatic deletion of historical errors or leases.
Fresh reads show revision 12 still active/enabled with a pre-acquisition blocked
entry, no leases/native bindings and an unowned 109c on xpad. Do not call this
successful recovery. Preserve installed sensor/Steam settings and the rollback
package. Local commits only; precision calibration remains paused. The following
installation/activation paragraphs are historical checkpoints.
Revision-13 source ec7adf8 now passes full offline checks and both module
builds (target GCC: zero warnings; local Clang patch difference disclosed).
The fixed-hash package and one-attempt updater are prepared privately, not
transferred/installed. Read RELEASE_AUDIT.md for artifact hashes and gates.
The final target read was unchanged and verified the retained revision-12
rollback artifact. Await scoped update approval; activation remains separate.


The subsequent revision-12 installation request is completed. Source 057270a
built for the checked CachyOS headers with zero warnings. The one approved
package transaction verified exact ownership, hooks, hashes and single-package
scope; DKMS/module identity and 124 payload files pass. The target is stopped
and persistently paused, with enabled setting retained, empty ownership and
no loaded native module. Its initial unowned 109c remains xpad-bound; do not
call that a successful 109c-to-100a return or input acceptance. Preserve private
logs/backups and the unused revision-11 rollback package. Activation, Resume,
both physical power-on cases and other-host update remain separate; no push.
See docs/RELEASE_AUDIT.md. Do not rerun the consumed installation receipt.

The cold-start correction was developed offline. The subsequent explicit
request authorizes preparation and installation of revision 12 on the CachyOS
target, following fresh checks and a displayed concrete update command. Keep
activation/Resume and hardware acceptance separate; no other-host update or push.
Preserve exact one-attempt guards, package hooks and private backup evidence.
The implementation scope remains correction of both cold-start gaps, tests
and local commit. Revision 12 removes the positive pad-counter gate after
valid passive 100a status and adds scoped acquire_109c plus same-instance native
bootstrap. Never weaken exact acquisition, fresh IMU, token attestation, budgets
or first-error/cleanup rules. Direct 109c does not authorize xpad fallback while
still 109c, a guessed reverse command, or automatic retry. Foreign/native owners
stay excluded. Preserve the historical revision-11 report below as evidence of
the old policy, not current implementation instructions. The approved update
may perform its reviewed release/stop/unload/DKMS hooks; do not independently
activate, test, change Steam or push. Cold startup
and late power-on, including a dongle present while RF is off, remain hardware
acceptance cases; do not claim they passed offline. Calibration stays paused.

The later user-led cold boot exposes two remaining startup limits. Read-only
journals confirm service/module autostart, initially unowned 109c on xpad,
then a fresh 100a acquired natively and a successful bootstrap/publication.
The maintainer explicitly reports no service/Resume commands and that power-on
alone did not suffice: native readiness appeared only after operating controls.
Distinguish binding from readiness: the 100a native bind precedes the completed
109c runtime. Source still gates bootstrap on accepted passive pad reports;
initial unrelated 109c is excluded. No timestamped human-input trace exists,
so do not assign the entire delay or the earlier re-enumeration to a particular
button. Record this as incomplete power-on-only acceptance, not an autostart
failure or a cold no-xpad pass. See docs/STANDALONE_STARTUP.md. No new live
action or runtime change follows from this observation; local documentation
and existing offline policy tests only.

After installation the maintainer independently started the service and ran
Resume. Read-only follow-up confirms the loaded revision-11 srcversion and
new acquisition attributes, active/enabled service, successful bootstrap and
paired gamepad/sensor nodes. The maintainer explicitly reports a successful
radio off/on cycle with the dongle left plugged in: Steam's gyro display in
Gaming Mode works without held Guide and without restarting Steam. Record
this limited positive application result; do not repeat hardware tests from
this report. The observed USB instance remained the same across the metadata
snapshots; no continuous RF trace was collected. This startup used an already
xpad-initialized 100a device and the logged handover path. Independent cold
startup, causation of the gyro improvement, repeated cycles and the new build's
other input/haptics regression remain separate. Protected manager status and
effective parameters were not reread with a password; only unprivileged reads
and available journals. No additional activation or runtime change by Codex.

The subsequent explicit one-shot approval completed the revision-11 package
update on the CachyOS target. Fresh checks and the corrected transaction guard
passed; the package hook verified release, stopped management and unloaded
the old module. Readback confirms revision 11, all 124 regular payload files,
target DKMS installed and srcversion 06354BBF7CEC05B29300CC8. The device is
observed as 100a/xpad (IF1 usbhid), with paused empty ownership; normal input
was not tested. Service is inactive/dead with its existing enabled setting
retained; no native module is loaded. Sensor/Steam files are unchanged.
No activation, Resume, reboot or new runtime test was authorized/executed.
Prepare activation and cold-start isolation separately; do not treat this
previously xpad-initialized instance as proof of independent cold startup.
Private logs/backups remain outside Git; no push. See the latest release audit.

The earlier approved revision-11 update attempt reached only pacman's preview.
The private wrapper rejected CachyOS's verbose old/new-version table and
answered no before confirmation or hooks. Readback confirms revision 10,
the same active/enabled manager and native instance; nothing was activated.
The helper now handles the recorded table and compact format offline, with
exact single-package/version checks and preserved one-attempt receipts.
Nine tests include fake-child confirmation/denial and changed-device refusal.
That attempt's consumed receipt remains intact; the successful separately
approved second attempt is documented above. Do not reuse either receipt.
See the latest release audit. Direct acquisition may reduce enumeration
transitions, but is not evidence that the Steam/Guide gyro issue is fixed.

The maintainer authorized isolated offline consolidation after the explicit
publication of e2415a9. New work remains local on codex/standalone-startup;
that prior exact-tip push permission does not authorize this branch's push.
Read docs/STANDALONE_STARTUP.md. Revision 11 accepts free or optional xpad-owned
100a/105e IF0 through new scoped kernel acquisition attributes. Never load/bind
xpad as a startup prerequisite, blacklist it globally, or adopt foreign/native
owners. Preserve budget/pause, one-shot instance checks, original errors and
separate cleanup authority. An unconfirmed acquisition is not native ownership.
Missing xpad fallback must stop before native unbind, without implied recovery.
Keep protocol, paddle, motion, FF and userspace bridge behavior intact; display
gain is not physical sensor scaling. No installation, SSH/hardware test, running
configuration change or GUI integration. Precise calibration stays paused.
Fresh Garuda/CachyOS hardware acceptance is separate, especially a cold start
without earlier xpad initialization. Retain Steam's controller-on-before-start
limitation and manual-only Eden guidance. No new command guesses to bypass it.

The subsequent explicit request authorized a read-only CachyOS kernel/header
check and an unprivileged remote module build only. Source 5b14c85 built for
7.2.11-1-cachyos-deckify with matching headers/GCC and zero warnings; transferred
source hashes, header fingerprints and module vermagic/hash were verified.
Only a fresh user-owned build directory was created on the target. Installed
revision 10 and its active/enabled service were unchanged. No installation,
module load, Resume, controller test or push follows from this build approval.
See the latest release audit. Both distribution builds now exist; independent
cold-start and runtime acceptance of revision 11 remain pending.

## Historical final publication checkpoint (19 October 2026)

The latest request is a final check of the entire unpublished public history,
including Eden documentation, offline tests and private-data exclusion, then
presentation for explicit push approval. See the latest RELEASE_AUDIT.md entry.
Earlier push permissions are superseded by this gate. No tag/release, runtime
change or new hardware test is included. Keep the Eden workaround manual and
application-scoped; the withdrawn launcher remains outside Git. Do not describe
revision 10 as an accepted Steam gyro hotplug fix. Calibration stays paused.

## Hardware safety

No module loading/unloading, driver rebinding, identity switch, active motor
or sensor test, installation or firmware access without separate explicit
authorization. Never flash firmware or guess undocumented device commands.
Document and verify the safe return to xpad. Deadband must retain a supported
exclusive maintenance path; normal play must not depend on it.

## Offline Gamescope gyro hotplug integration (19 October 2026)

The later Eden-only launch test is documented in docs/SDL_EDEN_GYRO.md under
"Eden through Steam in Gamescope". With verified private backups, the user
edited only Eden's Steam launch options to unset the two SDL controller
exclusion filters via its existing env executable. Fresh process metadata
confirms the unchanged paddle mapping and opened physical pad/sensor nodes;
the user accepts gyro without Guide, four independent paddles and normal input
without duplicates. Keep the original shortcut identity/arguments and restore
only its saved launch options for rollback. This is not Steam gyro UI/hotplug
acceptance, a kernel fix or authorization to modify other applications. No
global Steam/driver change, calibration, package update or push occurred.

The maintainer subsequently chose documentation only for this workaround:
keep the tested manual steps/rollback in the compatibility guides, with no
Eden-specific driver, installer or Control Center feature and no automatic
Steam option edits. The uncommitted launcher prototype is withdrawn from the
publication tree. Explain that removing both filters can expose other devices
within Eden; do not promise selective filtering or universal duplicate-input
prevention. The current request defers the previously discussed whole-project
push until the next explicit publication approval. Commit these docs locally;
do not install, repeat the already accepted test or push from this checkpoint.

Earlier Steam-specific follow-up: after a full reboot
the maintainer reports automatic native binding without Resume, but gyro only
while Guide is held. A separately approved metadata attempt passed SSH/sudo
and recorded service active/running/enabled, then stopped at the Gamescope
guard. It did not reach module parameters, Steam FDs or library identities.
Do not call that guard failure proof that Gaming Mode was absent. The offline
correction is tools/sdl/gamescope_identity.py: executable path/backing file,
four actual UIDs and stable PID/start, not directory owner or mutable comm.
The local binary names its main thread gamescope-wl; no remote name was saved,
so this is a reproduced guard defect and plausible cause, not target proof.
Do not infer the Steam/Guide root cause from it. Reject ambiguous identities,
inaccessible metadata and replacements; rescan at completion. No Steam-parent
requirement: the recorded launcher can run in a separate user service.
160 make test-steam tests and 19 private preparation tests pass. Consumed
attempts stay unchanged; a third metadata-only folder is prepared, unstarted.
Fresh approval remains required. No SSH, real sudo, live target or device
access in this correction; no Steam/driver change, package bump or push.
Read the latest section in docs/STEAM_GUIDE_GYRO.md before another read.

The later metadata-only SSH precheck stopped in the remote Fish parser, before
sudo authentication or the read program. Preserve that failed attempt; never
reuse its receipt or infer module options, open sensors or motion from it.
The user also reports manually running Resume and now no Guide-held gyro
response. This is not current autostart acceptance or a reproduced Guide gate.
The offline correction is tools/sdl/ssh_python_payload.py: encode reviewed
UTF-8 Python as Base64 inside a fixed ASCII shell bootstrap, without shlex.quote
on raw nested source, a heredoc or piped GO. Real local Fish/Bash/sh tests use
only own children and a synthetic sudo stub; no actual SSH/sudo/GUI/target.
Keep source hashes, exact device/library guards, one-attempt receipt and all
existing deadlines. Encoding is not encryption or a read-only sandbox.
A separate untouched next-run directory is prepared, not executed or approved.
Fresh live permission remains necessary; inspect effective module parameters
and sensor FDs before any new motion/process-memory observation.

Read docs/STEAM_GYRO_HOTPLUG.md. Revision 10 now integrates the shared policy,
processed-libudev backend, checked client and optional two-phase kernel input
publication. This supersedes the unintegrated prototype at 468ddc6. Preserve
all real-motion units/axes and existing raw IIO, paddles, FF and trigger STOP.
The module defaults defer_input off; prepared service requests it, effective
only for persistent 109c with the six-axis opt-in. Exact tokens, current binding,
processed node lifetime and seat-access proof are required; no sysfs/database-
only readiness. Bounded child account/access check opens no device, changes no
parent credentials or ACLs. No-active-seat publication is defined separately.
Keep the ten-second deadline and attempt/first-error record across restarts;
missing fresh receipts do not authorize retries. Release/cleanup is distinct
from startup budget. Never claim END/xpad binding proves 109c became 100a.
No active-pad re-registration, Steam restart, global sleep, library/preload
replacement or wider permissions. Offline tests/build are not real Gamescope
reconnect or PM acceptance. The separately requested CachyOS build transfers
only selected sources to an unprivileged working directory, not an installer
or running configuration.
Both Garuda and CachyOS builds pass; no installation, live action or push is
authorized by this implementation. Calibration stays paused.

The subsequent explicit installation approval installed revision 10 on the
CachyOS target; a separate service-start request loaded the new module/monitor
with management still paused and empty ownership. Read the follow-up evidence
in docs/evidence/INPUT_PUBLICATION_INSTALL_20261019.json. After approved replug,
the new device remains 109c/xpad and the observed session is KDE, not Gamescope.
No Resume or hardware test ran. Do not infer 100a return, adopt unowned 109c,
repeat replug or claim Gamescope acceptance; clarify prerequisites first.

A later user-led reboot reaches Gaming Mode. Off-state 0575/usbhid is ignored;
approved normal power-on yields 100a/xpad. One separately approved Resume
attests 109c, exact lease/tokens and input publication. The observer-only policy
now recognizes input_check/awaiting_sensor/publishing_input (34 regressions),
without changing installed code or weakening deadlines/error/final proof.
Steam ran before power-on and, after its gyro UI opens, has both readable paired
nodes open. User reports all gyro UI rates zero, normal input/paddles working.
This is a FAILED late Steam gyro application test, not complete hotplug acceptance
or proof of the downstream cause. Do not infer reads from an open FD, retry,
perform the radio-reconnect test or change runtime automatically. No manual
error-Release was authorized or executed. Leave the healthy normal-input runtime
unchanged; record active/enabled and unpaused separately from the earlier pause.

The maintainer then qualifies the all-zero UI report: the gyro display works
while Guide is held. Preserve the earlier negative observation as history,
but do not claim complete sensor nonresponse or a proved pure display bug.
This is a human report, without an additional agent-run trace. Guide-dependent
event/cache/notification/refresh handling remains unresolved; continuous gyro
without held Guide and reconnect remain unaccepted. Do not add fake Guide
keepalives, change runtime or start a live comparison from this report alone.

The targeted offline follow-up is docs/STEAM_GUIDE_GYRO.md. Actual sensor-emitter
adapters and both system/Steam ELF32 SDL pass fresh frames across Guide holds
and releases. This is not a real USB/RF or Steam/Gamescope trace. Pinned Steam
explicitly requests background SDL events; its motion notification needs an
existing selected context/source and does not create a missing source through
that lookup. Internal Guide processing is mapped separately; do not call its
accumulator flag a proved gyro gate or infer the target's live source state.
Guide-selected source/processing remains a hypothesis, pure display bug and
exclusive cause unproved. Reference binaries are not freshly verified on the
Gamescope target. No installed code/settings, sensor profile, source publication
or hardware changes; no push or new observation approval. Preserve calibration
pause and the failing late-arrival acceptance. Capabilities/pressed state were
separated only in the fake kernel test, not the production adapter.

## Bazzite assessment (19 October 2026)

Read STEAM_GAMESCOPE.md's Bazzite feasibility section before a distribution port.
The request authorizes research as a possible CachyOS replacement, not system
migration, package/image installation or new hardware tests. No Bazzite target
build/acceptance or RPM spec exists. Keep the common kernel/protocol core;
adapt Fedora akmod/kmod/RPM and the actual Bazzite session separately. Preserve
vendor launch behavior and mapping conflict guards; current reference uses
OpenGamepadUI/InputPlumber, not CachyOS's steam-launcher unit. Do not assume a
particular image/session, disable input stacks/SELinux or claim Secure Boot
trust from an image signature. Plan kernel-matched updates and persistent
state/profile rollback handling. Late Steam gyro discovery remains open.
No upload, push, calibration or running-driver change follows from this study.

## Current SDL/Eden implementation decision (18 October 2026)

The user accepted the observed gyro response at 0.07 dps/raw, 1.00x display
and requested SDL/Eden integration. This supersedes earlier prohibitions on
**offline implementation** of that profile, not hardware/installation gates
or evidence standards. Do not restart chip/factor/known-angle research.
Read docs/SDL_EDEN_GYRO.md. Preserve the explicit experimental_gyro opt-in,
109c-only scope, gyro-only evdev node, nonempty paired session identity and
unchanged raw IIO. Do not infer accelerometer axes or add display gain to
physical units. Default configuration stays off until separate activation.
Eden's pinned input path accepts gyro-only; source-method tests are not an
emulator acceptance test. Retain its documented initial timestamp-domain
limitation; start Eden after native startup for the first approved test.
No Eden GPL-3.0-or-later sources/binaries are distributable with our GPL-2.0-only
sources. The user also requires independent assignable paddles;
maintain them and test their combinations alongside gyro. No push authorized.

Revision alpha3-8 was subsequently installed under explicit permission. A
separately approved activation and Eden controller-settings test confirmed
SDL motion, matching directions/sensitivity, all four independently assignable
paddles and preserved normal inputs. A later separate approval installed only
the local /etc/modprobe.d/90-gamesir-native-gyro.conf opt-in. Its effective
options and unchanged active runtime were checked; no module reload or reboot
occurred. The local boot option is now persistent; the package default remains
off. Actual gyro reboot/hotplug/PM and particular-game acceptance remain open.
Do not restart calibration research from this qualitative result.
The maintainer closed the current gyro milestone after Eden acceptance and
persistent local configuration. Dedicated Steam gyro integration is deferred
for lack of a current use case, not because Windows games cannot support gyro.
Preserve the working SDL/Eden path and existing Steam paddle support. Remaining
boot/hotplug/PM evidence limits stay documented; do not start further tests,
calibration or Steam changes without a new request.
The subsequent request authorizes offline Steam-gyro feasibility only, with
all features required to remain compatible in one project. Read
docs/STEAM_GYRO_FEASIBILITY.md: both local Steam SDL3 libraries pass the
device-free gyro-only/paddle tests, but actual Steam Input capability and
Proton gameplay remain unverified. Keep one existing evdev sensor contract
and one USB owner; do not replace libraries, fabricate acceleration, change
Steam settings or globally preload a bridge. Shared input/output and lifecycle
acceptance is required before claiming integration. Preserve Eden acceptance;
no new hardware, installation, calibration or push is authorized.
The user subsequently started Steam manually: its gyro UI exists but stays
at zero during reported motion, and calibration waits after its countdown.
Cancel and the desktop work; the user confirms Eden gyro still works after
reconnect. Read-only snapshots found paired native nodes and Steam opening
the motion node; its actually loaded 32-bit SDL also passes seven synthetic
cases. Steam's accel/gyro calibration stages suggest an acceleration-related
dependency, not a proved root cause. Do not equate UI presence, an open FD or
SDL probe success with Steam motion acceptance. Do not fabricate acceleration
or change the functioning driver/Eden path. See the follow-up in
docs/STEAM_GYRO_FEASIBILITY.md; next live tracing/settings changes need approval.
The 19 October offline follow-up reproduces the statically observed Steam
sensor-enable sequence in SDL: absent accel/left sensors do not disable gyro.
Repeated ticks, 31-bit wrap and sensor disable/re-enable pass with three Steam
SDL libraries. The stricter test caught and fixed extra empty SYN_REPORTs
in the synthetic fixture; this is not a runtime driver defect. ELF32 testing
now uses the committed runner. Steam's downstream filter remains unproved;
do not infer a fix or rule out an acceleration requirement from SDL success.
The observer in docs/STEAM_GYRO_OBSERVATION_PLAN.md had one authorized metadata
precheck, which stopped before process memory at `Mapped/file identity differs`.
No cache observation ran. An own-file offline Btrfs reproduction shows that
maps' device and stat.st_dev can differ legitimately; the failed log did not
record the exact differing component. The corrected guard compares stat
metadata of the hashed file/FD with every kernel map_files alias, and pins all
SDL segments. Never weaken this to hash/path/inode-only acceptance or bypass
denied alias access. It follows aliases with stat only, never opens them.
Subsequent separately approved prechecks passed actual elevated alias traversal;
the observation then stopped before memory at `No local GO`, despite the user
typing GO as shown in their screenshot. A following direct-PTY correction still
failed actual sudo/monitor foreground checks before GO. Preserve both failures.
The newer nested-PTY model follows locally documented sudo behavior: an initial
background command needs a real read to request monitor foreground handover.
Do not reject that transient state before reading or poll with select instead.
Use the current reviewed sudo → Python command directly, with any external
timeout OUTSIDE sudo, never between its monitor and Python. The helper's own
SIGALRM bounds precheck/observation/GO to 30/210/120 seconds; nested waits must
retain the original enclosing deadline/error and restore timers/handlers.
Terminal stdin, a bounded GO+Enter read and confirmed foreground ownership
AFTER the read remain mandatory before fresh identity checks and memory open.
Readiness may report foreground false pending handover; acceptance must be true.
Never pipe GO, substitute a terminal, remove the gate or retry automatically.
49 observer and 15 terminal/monitor tests pass offline; all signals/processes
in the model are test-owned. The live helper signals no other process and
changes no terminal groups. No sudo, Steam process or controller access occurred
during the correction. A later separately approved ef64ee5 desktop run completed
with exit 0, human GO and confirmed handover: 682 enabled cache samples, one
concurrent update omitted, unchanged final identities and closed memory FD.
Read docs/steam-gyro-observation-live-001.json and the live section of
docs/STEAM_GYRO_FEASIBILITY.md. Real motion changes all three SDL cache axes,
while the user reports all three Steam UI rates remain zero; normal inputs and
desktop remain normal. Delivery into Steam's SDL is now proved for this run.
Downstream event/selection/filter/UI handling remains unresolved: do not claim
intentional discard, accelerometer dependency or a specific defect/fix. Preserve
Eden, paddles and current driver; no fake acceleration or extra raw USB reader.
One successful observer run is not universal monitor/lifecycle acceptance.
A new attempt requires separate permission and local GO before process memory;
no debugger attach, target calls or device opens. Unknown hashes, multiple
targets and instance changes stop it. Cache updates
prove delivery inside SDL, not Steam's downstream acceptance or exact discard
reason. Do not silently substitute GDB/ptrace or invoke this live helper in tests.
The subsequent offline downstream analysis is in docs/STEAM_GYRO_DOWNSTREAM.md.
Instance routing, gyro-only early record turnover/conversion and a separate
controller/IMU-indexed UI notification feed are statically identified. Do not
claim the first quantizer erases motion: the saved movement replay preserves
192/194 nonzero vectors. The subsequent notification-gate follow-up maps the
previously unknown triple to acceleration through writer, cached-report base,
lane stride and CGyroSource reader. Zero selected acceleration is a sufficient
static blocker for UI gyro notifications, even with nonzero gyro, valid source
and subscription. Read docs/steam-gyro-notification-gates-offline.json.
Do not downgrade this back to an offset-only guess, or overstate it as the
exclusive measured live cause or a universal Steam gameplay restriction.
Source validity is a published finite-quaternion marker, not connectivity or
calibration completion. UI RawSpeed is not raw USB counts. No fake gravity,
forced flags, installed changes or new live observation follows automatically.
Preserve accepted SDL/Eden, gyro-only opt-in and all other features; any real
accel extension needs its own axes/units evidence and implementation request.
The subsequent implementation request authorizes the offline real-accel
extension in docs/STEAM_ACCEL_EXTENSION.md. Keep experimental_accel default off
and separate from the accepted gyro opt-in. Require an explicit signed map;
no accelerometer frame is confirmed by the gyro movement recordings. Synthetic
map -3,1,-2 is a test only, never a recommended device configuration. Reject
invalid activation before USB registration. Preserve same-report/time/sync,
raw IIO, gyro-only defaults, Eden, paddles and output ownership. No installed
change or live/Steam acceptance follows from offline success. Obtain actual
accelerometer-frame evidence and separate activation approval first.
The installation-preparation follow-up re-examined four checksum-verified
known-direction captures at low angular rate during held tilts. Face-up A1+,
left/right grip down A0+/-, and front down/up A2+/- independently support
accel_axis_map=1,2,3 as an explicit supervised test candidate. Read
steam-accel-held-pose-evidence.json and STEAM_ACCEL_EXTENSION.md. This is
not gyro-map inference, six-pose calibration or verified device gain/bias.
Do not force another precise-angle gyro test, silently enable the candidate,
or claim Steam acceptance. Revision 9 is prepared; package defaults stay off.
The later separately approved revision-9 package update completed (pacman 0,
DKMS for 7.2.11-1-garuda and Qkk 143 entries/0 alterations). Read
docs/evidence/STEAM_ACCEL_INSTALL_20261019.json. Its postcheck stopped on
100a/xpad -> new 109c/xpad; the user reports inactivity shutdown, not a
proved causal diagnosis. Preserve the failed guard report. Final checked
service inactive/enabled, persistent pause true, empty leases/no native
binding, module unloaded, existing gyro config unchanged. Do not auto-retry,
load, resume or enable acceleration based on the package update approval.
The user then independently started the service AND ran Resume, confirmed
in chat after the paused-only read guard failed. Latest read-only follow-up:
service active/enabled, revision-9 module loaded, paused=false, empty leases/
managed devices/native bindings, USB 109c/xpad, gyro Y, accel N. The agent ran
neither start nor resume. Preserve the failed guard and user context, not a
new driver-defect diagnosis. Pause/profile reload/cold-source return and any
bootstrap require fresh concrete approval. Do not adopt unowned 109c or claim
that the installed accel extension is active merely because service runs.
Subsequent explicit approvals authorized one Release, four profile-load
operations and one Resume with one error-Release only if needed. All passed;
no error-Release/retry occurred. Current accepted run: module accel/gyro Y,
map 1,2,3, 8192/1 counts/g, same gyro 0.07; native 109c active with attested
lease/tokens and paired six-axis node readable by the session user. The user
confirms Steam's three gyro rates now respond and ordinary inputs/all four
paddles work. Read docs/evidence/STEAM_ACCEL_ACTIVATION_20261019.json.
Do not continue claiming the UI fix is untested, or expand it into a Proton
game/six-axis Eden/lifecycle/calibration acceptance. No persistent accel file
was written. Preserve temporary profile and working features; persistence,
extra app/hardware tests and public push need their own approval.
The maintainer subsequently reports "Eden funktioniert auch weiterhin".
Record continued functional use with this profile; do not invent repeated
axis/button/calibration/lifecycle measurements or require precision gyro
calibration again. A file-only persistence candidate is prepared and validated
with modprobe --show-depends (no load): update the existing local gyro file to
include accel=1, map 1,2,3, 8192/1. It has not been written to /etc. Separate
explicit approval is still required; do not restart/reload/reboot as part of
that file-only action or change package defaults.
The subsequent explicit file-only approval was executed once: the existing
local modprobe file now includes gyro/accel=1, map 1,2,3 and 8192/1. Exact
bytes/SHA256, root:root/0644 and effective options passed, as did unchanged
service PID/state, module instance/srcversion and all runtime parameters.
Private evidence and the saved gyro-only file are checksum-verified. This
supersedes the prepared-only state above. No reload, service restart, Resume,
initramfs rebuild or reboot occurred. Package defaults remain off; actual
next-boot/lifecycle acceptance still needs its own approval. Do not start
extra hardware/app tests or resume calibration from this file-only approval.
A later read-only SSH comparison found matching CachyOS 7.2.9 headers/tools,
unchanged manager/service/Steam integration and known Steam SDL hashes. The
same revision-9 source package/profile are candidates, not target build or
sensor acceptance. Read STEAM_ACCEL_EXTENSION.md's transfer assessment. The
target remains revision 6; no GameSir device was visible and protected ownership
was not read. No install, target file write, activation or hardware approval
follows. Do not copy a Garuda-built module or apply new options to revision 6.
The later installation request passed the real GCC target build and, after
a no-device-baseline precheck halt, one separately authorized connected-device
transaction. CachyOS now has revision 9 and the identical local six-axis opt-in;
111 payload files, DKMS/srcversion/vermagic, rights/options and unchanged
Steam/Gamescope passed. Final return is 100a/xpad, empty leases, paused=true,
service inactive/enabled and module absent. The earlier stopped report and six
resolved historical failures remain intact. No start/Resume/test was authorized
after that update; activation and actual sensor/application acceptance still
need their own concrete permission. Do not call the installed update active.
A subsequent activation approval and separately authorized manual cold replug
led to exactly one start and one Resume. The existing observation policy
attested native 109c, same parent/lease/kernel tokens, pad+IMU and the paired
six-axis node readable by the active Gamescope user. Service active/enabled,
manager unpaused; no error Release or retry. The initial unowned 109c/xpad
snapshot is retained. User confirms normal inputs/all four independent paddles,
but Steam's three gyro rates remain zero. A read-only main-Steam-process FD
snapshot sees the gamepad open, not the paired motion node; this is not proof
of the exact cause or all processes' behavior. A normal user-led reboot was
suggested after the user's question, not performed by the agent. Do not claim
CachyOS Steam gyro, reboot or calibration acceptance. Preserve the working
native session; no extra release/reload, Steam change, motor test or push.
The later user-led reboot was checked read-only: changed boot ID, enabled
service started around 16 seconds into boot, successful native startup and
paired readable six-axis node. This supports one boot case, not general
lifecycle acceptance. Steam's main process still has only the gamepad open,
not motion, in two snapshots including a human-confirmed open gyro UI; the
user reports all three rates zero. Reboot did not resolve this case. Runtime
parameters/protected lease were not read; no sudo, device/process-memory open,
start/reload/Resume/Release or Steam change. Keep Steam gyro failure open.
The subsequent same-host KDE report is positive: read-only SSH confirms the
same boot, kernel/package/module source, manager PID, profile and paired nodes;
KDE Steam opens both nodes, Gamescope previously only the gamepad. Read
STEAM_ACCEL_EXTENSION.md's same-host comparison. The Gamescope launcher started
before native readiness and defaults to Steam Deck flags; timing and launch
mode remain confounded, neither is a proved cause. Reference SDL pairs sensors
at gamepad open, with no late-sensor reassociation in the inspected path; the
kernel already publishes motion first. Do not claim a compositor defect, change
the driver, strip flags or add an arbitrary boot delay. A normal Steam restart
in Gamescope with nodes already present is a proposed separately approved test,
not executed here. Preserve KDE success and the Gamescope failures separately.
The later maintainer report is positive for Gamescope too, after a user-led
kernel update/reboot: fresh read-only SSH sees matching 7.2.11 CachyOS headers
and module vermagic, unchanged revision-9 source/profile, service active/enabled,
paired readable nodes and Steam opening both. Targeted metadata confirms
Gamescope and the vendor Steam Deck flags still present. The user reports the
controller was on before Steam; kernel/boot/timing changed together, so neither
a kernel fix nor startup order alone is proved causal. Read the new success
section of STEAM_ACCEL_EXTENSION.md; preserve earlier failures. Late controller
arrival/reconnect/PM remain open; no automatic restart, installation, driver or
Steam patch, new hardware test or calibration follows from this report.
The next human reconnect-check report requires the controller already on when
SteamOS loads for gyro. Record a reported startup precondition, not unrestricted
gyro reconnect acceptance or proof of normal-input failure. Sequence/count and
sensor FDs were not captured; no new agent access/test occurred. Reliable late
sensor discovery remains open; do not silently add Steam restarts or boot waits.
The first activation was interrupted by a private helper that mistakenly
aborted on transient metadata errors. Reuse the existing bounded
tools/native/bootstrap_observation.py policy for future startup observers;
do not write an ad-hoc fatal-on-any-port_errors check. Retain complete
observations and original failures across cleanup. Read the recovery and
successful separately approved run in docs/SDL_EDEN_GYRO.md before new tests.

## Historical boundaries and evidence

VID3537; standard PIDs100a/109c; ZZZ105e remains experimental. Keep existing
XInput/GIP/IMU formats and hardware-confirmed four-motor packet support.
8192 LSB/g is an interchangeable experimental accelerometer value. Gyro scale
is unknown; calibration is paused and calibrated SDL output is not approved.
Decision of 2026-10-18: defer further lower-radio/crypto analysis. Received
IMU packets are already hardware-confirmed; reconstructing every RF stage is
not a prerequisite for measuring the effective USB gyro scale. Document
0.07 degrees/s per USB raw count only as an unconfirmed test candidate,
based on the ST +/-2000 dps hypothesis and assumed unchanged gain to USB.
Do not select it automatically, change the driver or enable calibrated SDL
output. Known-angle, timestamped reference measurements require a new request
and separate hardware approval; calibration stays paused. Preserve existing
research and its unresolved questions without automatically continuing it.
The separately prepared qualitative left-turn test in docs/GYRO_AXIS_TEST.md
requires no known angle. Use its explicit run-axis-left mode only after fresh
instance checks and separate live approval, with one local Go per repetition.
No automatic repeat, reference-angle claim, scale selection or runtime mapping;
raw channel/sign evidence does not validate a full axis map or calibrated SDL.
The first actual buffer setup exposed an IIO scan-selection bug, corrected
offline in docs/IIO_SCAN_SELECTION_FIX.md. Do not reinstate a full-request-mask
validate_scan_mask callback: IIO calls it for intermediate channel enables.
Keep the full producer mask and enable-time layout guard, plus reader/build
and instance checks. The corrected module was subsequently installed under
separate authorization as alpha3-7 on the Garuda test host. Two bounded
buffered runs restored all settings; exclude the first from axis analysis
because the user rotated back. The explicitly requested replacement run has
6,749 coherent scans and one human-confirmed qualitative left turn: G1
predominantly positive is a candidate, not a complete axis map or scale.
Further runs require a new request and local Go; do not reuse an old manifest
or module hash.
The six-direction extension in docs/GYRO_AXIS_TEST.md now has a limited live
observation: three accepted directions, then an inactivity shutdown before
the fourth capture. The user separately authorized continuation on a fresh
instance; three existing single-direction transactions completed the set.
Keep both blocks and the failed series report intact. Never merge their
instance identities or bypass summarize_axes' single-instance guard. Reviewed
raw candidates are left/right G1 +/-, front down/up G0 -/+ and left/right
grip down G2 +/-. These are qualitative observations, not installed axes,
scale calibration or full sensor/SDL validation. All six captures restored
their buffers; the stopped fourth attempt made no buffer writes or reads.
For future approved work, ordinary user button activity between captures,
before Go, may avoid idle shutdown; do not invent automatic keepalive commands.
Its run-axes sequence reuses the unchanged 108-second
worker once per direction, with fresh manifests, the same approved instance,
local Go and restoration checks each time. Cancel, unconfirmed motion or any
failure stops the series; never skip/retry or adopt a replacement. In this
new mode only, return motion is permitted after MESSBEWEGUNG VORBEI and
excluded from the analysis window. Preserve the legacy run-axis-left cues.
Channel/sign heuristics are review candidates only. Separate gravity poses
are still needed for accelerometer axis mapping; no scale or SDL activation.
The user subsequently authorized applying these observations to the opt-in
offline profile g7pro-observed-20261018 in gamesir_imu_diagnostic.py. Keep the
wire vectors unchanged; right-handed body X=right, Y=front, Z=face-up uses
(G0,-G2,G1). Named positive motions are pitch-up G0, yaw-left G1, roll-left G2.
This is not the SDL frame. Require explicit axis and gain selection, limit
the observed profile to standard 109c evidence, and retain false calibration/
runtime verification flags. 0.07 dps/raw is still only a test hypothesis.
Never reuse the gyro mapping for acceleration without separate pose evidence.
Offline replay-buffer verifies saved worker checksums, restoration and binary/
JSON agreement; it must not open live devices or merge capture instances.
The optional PySide6 window in tools/imu/gamesir_gyro_viewer.py retains
verified file-only replay and now offers a separate --live frontend. Read
docs/GYRO_VIEWER.md before any live use. Window construction
does not discover/open devices. Preparation, password/metadata checks, then
local Go are explicit; live execution still requires separate approval.
The user requested no fixed preview duration: keep only current samples in
memory, save summary evidence only, and continue until STOP/window close or
a safety fault. Preserve bounded heartbeat/stall/setup/cleanup deadlines;
never silently adopt another instance or retry after disconnect/suspend.
Reuse the existing single-FD host-IIO transaction and verify restoration
independently before claiming success. Do not install/rebind/start a driver.
The legacy 108-second capture remains bounded and retains its raw evidence.
Factor changes reset only displayed orientation, never transport identity/
counter checks. Quaternion integration uses host sample timestamps; crosshair
gain/centering are display-only. No bias correction or acceleration mapping.
One separately approved live preview on 2026-10-18 processed 11,466 samples
and ended through user STOP with verified host-buffer restoration and normal
gamepad function. The user confirmed unchanged 0.07 dps/raw and 1.00x display
gain, natural movement and a subjective preference over a PS5 controller.
Retain that pair as the user-preferred experimental diagnostic setting;
do not start another factor search or silently install calibrated runtime
output. No known-angle reference, quantified drift or SDL/Eden test was done.
Read docs/gyro-viewer-live-001.json; subsequent live sessions need new approval.
Display gain, a plausible animation and offline tests do not prove calibration.
No universal trigger-game support or general stability guarantee.

The optional `tools/offline` HID companion is file-only research, not runtime
authority. Read docs/XPAD_HID_PROTOTYPE.md before extending it. Existing captures
show brief 100a/IF1 telemetry but no proven activation or continuous stream.
Do not transmit the 8K heartbeat, apply report12 offsets, merge enumeration
epochs or loosen native IF0 gates from that evidence. Keep keyboard/mouse data
private and raw sensor units uncalibrated. Hardware transport requires new approval.
The passive 100a/300-second and separate 90-second recorders are test tools,
not an activation path. The 90-second recorder completed two separately approved
runs; only the second had verified normal XInput alongside short nonvendor HID,
with no vendor IMU telemetry observed. Read docs/HID_PASSIVE_CAPTURE_RESULTS.md
and docs/HID_PASSIVE_CAPTURE.md; never invoke the motor-test
coordinator for it. Require fresh source/boot/instance metadata, manager pause
and empty ownership. A blocked 109c lease must not be cleared or bypassed to
make a capture run. No release/resume, module load or recovery from test code.
The short profile is a stream-presence smoke test, not physical paddle mapping
or gyro calibration. Incomplete process inspection remains fail-closed;
report PID/operation/FD/errno without argv or private paths. Never bypass a
permission failure just because a descriptor appears to be a pseudo-FD.
Before another passive 100a test, verify an ordinary input consumer for the
exact IF0 instance, visible normal input and that the test client stays open.
The first run lacked that prerequisite and had no XInput completions. A bound
xpad interface alone does not prove its input receive path is active. Do not
open raw USB/HID or replay an initialization request to compensate.

Passive getter results are observations of one instance, never authority over
a replacement. Reconnect fixes must preserve actual faults, unknown-metadata
quarantine, parent/instance checks and start budgets. Read
docs/MANAGER_RECONNECT_FIX.md before changing this lifecycle. No automatic
error-text migration or repeated resume/rebind attempts on the running system.

## Optional trigger bridge

Keep game/Wine/SDL adapters and per-game gains in userspace. Use the existing
broker; never open USB/input nodes or bypass native ownership guards. Require
exact evdev-to-native-instance association and preserve zero/stop barriers.
Reject stale sessions rather than adopting replacement devices. Read
docs/TRIGGER_BRIDGE.md and its provenance audit before extending this path.
Revision 2 passed one approved Forza/Xodus run after a failed first trial:
both triggers, effect pauses/restarts, normal input/grip rumble and quiet
normal exit were confirmed. This does not validate reconnect, PM, crashes,
multiple devices or other games. Further live actions require new approval.
Steam/Proton is plan-only until its runtime is separately validated. Never
globally preload the hook into Steam
or a desktop session. Existing paddle mapping remains independent.
Read docs/STEAM_PROTON_TRIGGER_BRIDGE.md before implementing that adapter.
Prove host/container placement, peer-PID namespace mapping, exact source
identity and preload composition; never drop those guards to enable Steam.
Synthetic API tests are not game acceptance. No supporting game is currently
available for the planned Steam trigger test.

## Local static research tools

The optional `tools/research/rea_local` helper is separate from the runtime
driver. Its five static lanes use private copied inputs and a verified
network/device-isolated sandbox; never replace them with an unrestricted
REA/MCP invocation or execute/emulate a target. Keep raw results private.
Read the local-tool section of docs/GAMESIR_NEXUS_RESEARCH.md before use.
REA 6.5.0 has no built-in Jieli raw-code backend. A private local Ghidra
Pi32v2 processor description from pinned Quarkslab commit
`e1bd0707874b77b759401555d24839ad43af1267` is available for static analysis.
Its tested literal and 22-bit transfer forms matched known anchors in three
private app images; the tested transfers use `inst_next`, four bytes beyond
the former empirical target. The pinned SLEIGH source describes `E040` as
zero-extending, but this conflicts with the official Jieli-Tech
`fw-AC63_BT_SDK` Pi32v2 ROM listing at commit
`fdc018de81629e21e594d677cf05f87d288be0f0`: all 44 checked `E040`
immediates match sign extension and register selection, while 14 negative
values do not match zero extension. An isolated, private sign-extending
decoder variant finds 16 mask-entry patterns in each of three app images;
each branches to a shared handler whose decoded operations load a value,
AND it with the mask register, and store it back. This supports a generic
masked-update helper, not a sensor-register path. A byte-aligned scan for
the tested compact and 22-bit branch encodings found no incoming branch to
these entries; indirect-table reachability remains open. The sole direct
reference to `Enter Sensor Cal Mode!` still reaches the shared text logger.
That log ends in an unconditional branch: the linearly following zero
halfword store is not a proven continuation. P-code register-space offsets
are not register numbers (offset 4 means r1, not r4). Do not infer execution
order from linear decode, especially across branches, delay slots or tables.
Correction: the code at `0x10730`/`0x10738` refers to `eeprom read over:`,
not `adc scan not over`; its EEPROM read/write neighbors conditionally call
an unresolved indirect target. The actual ADC log literal is at `0x7426` and
reaches the shared text logger, with no proven IMU link. Neither path proves
sensor initialization. Tested direct-branch and exact-pointer scans found no
incoming candidate to the calibration/EEPROM log blocks; other addressing
forms and indirect-table reachability remain open.
New base-plus-offset string references identify a much stronger sensor path;
read docs/JIELI_SENSOR_INITIALIZATION.md before continuing. Three app images
prepare a read argument 0x0f followed by comparison with 0x6a, then pass
buffer byte 0x6c for register argument 0x11 and 0x68 for 0x10 to a shared
write helper. This supports an ST initialization candidate: under the
LSM6DS3TR-C assumption, +/-2000 dps and 0.07 dps per sensor count. It does
not prove the active sensor, successful bus completion, the last effective
configuration or unchanged USB scaling. Keep the QMI branch separate.
The twelve-byte follow-up now links the ST selector, byte assembly, conditional
six-offset subtraction and a report-construction candidate. Read
docs/JIELI_SENSOR_REPORT_DATAFLOW.md. Under the documented addressing/copy
assumptions, the 10/3c/e0 report carries Gy,Gz,Gx,Ay,Az,Ax after optional bias
subtraction at offsets 17..27, without extra ST gyro gain in that section.
Other output/sensor branches negate, divide or use 976/1000; keep them separate.
The transport follow-up independently matches the external copy CALLs to
the cached SDK's __stub_memcpy/memmove via code base 0xffe000c0. This is
an ABI/address model, not a measured silicon ROM revision or global alias mask.
Read docs/JIELI_USB_TRANSPORT.md and docs/JIELI_WIRELESS_DATAFLOW.md.
The two-ended A2 transport candidate now connects the report queue through
B+0x3dc, an A2/sequence section, DG queue D+0x2e0 and buffer D+0x8a4 to IN 0x82.
The callback-registration follow-up in docs/JIELI_RADIO_CALLBACK.md resolves
the selected H4_Controller table, setter and data callback in three apps.
This proves a static initialization relationship, not observed task execution
or active radio delivery. Read docs/JIELI_LINK_ROUTING.md for the follow-up:
the low-12-bit handle selects a dynamic list first, then two fixed slots.
The DG descriptor-to-table-to-btstack-message-to-A2-parser chain is now
identified; actual membership, lower radio delivery and descriptor origin
remain open. Read docs/JIELI_RX_CONTEXT.md for the follow-up. The private
exporter's former ProcessorContextImpl silently lost future context commits;
use the tested address-aware DisassemblerContextImpl helper for new ranges.
Old context labels do not validate conditional blocks. DG state byte r14+9
!=1 selects 0x1d81c, ==1 selects 0x1c8fe, under the reviewed simple-block
model; actual state remains unknown. A fifth private decoder correction
preserves E9D4 stack-offset bits: 13 SDK controls, two discriminators, plus
the prior 127 controls pass. Five simple conditional blocks pass, but the
SDK's conditional parallel block still loses its guard at 0x110130; the
negative-immediate forms at 0x1103ec/0x11042a remain unsupported. These are
not fixed by restoring the separately omitted repeat family. The unchanged
conditional grammar and the own exporter have distinct limitations.
DG 0xfe42 uses a hardware register block, variable packet buffers and a
separate result area; another caller appends four result bytes. CCM-like
packet crypto is a hypothesis, not a confirmed algorithm/register identity
or validated authentication path. Do not infer sensor scaling, byte-preserving
radio transit or a security bug from it. Descriptor origin, state writers
and the engine's independent definition remain deferred research questions,
not the next task or prerequisites for a reference calibration.
The D+0xa24 format-cache writer is identified but is a separate path.
Likewise DG queue D+0x2a8 leads to IN 0x84; do not equate these queues/endpoints.
DG's tag 0x0a rewrite does not apply to the reviewed tag 0xe0 telemetry.
A fourth private decoder repair preserves all four source-register bits in
EE52 byte stores: 44 official SDK examples (25 high-register discriminators)
and the previous 83 controls pass. Without it the A2 header is misread.
Scaled indexed-halfword and signed-extract still lack exact independent SDK
examples; exhaustive integer counterexamples are not ISA/hardware proof.
The related EDD8 mode-9 store also has a suspect base/index shift order.
The monotone table and shifted signed-field checks in the callback report
are internal consistency evidence only. Do not treat the table's 16384 as
a sensor scale or confuse the table's data callback with its opposite-direction
send handler. Preserve the distinct text-pointer, ROM and RAM-suffix models.
Last effective sensor configuration and physical calibration are still open.
Never treat the 0x10ad4/0xc60c tables as code, trust the original broken
P-code forms, or count parallel members twice. Nexus's separate 60-byte
parser paths still leave their sensor fields unset. The decoder is incomplete; never infer
code/data boundaries, sensor writes, or `CTRL2_G` from numeric matches alone.
No target execution/emulation,
hardware access, or driver edit. Calibration remains paused and the driver
unchanged.

## Public snapshot

This export omits private development-session instructions and consumed
hardware approvals. Historical reports are anonymized where indicated;
original evidence hashes remain historical. See PUBLIC_EXPORT.md and
PUBLIC_SOURCE_MANIFEST.json. No live system action is authorized by this tree.
