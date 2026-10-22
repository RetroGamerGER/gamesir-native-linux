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

## Current: PRE-ALPHA.4 / alpha2 published — 22 October 2026

The authorized release is published at v0.1.0-pre-alpha.4, source 48f2387.
AppImage alpha2, core alpha3-20 and optional TMR helper alpha1-2 have 12
verified release assets; previous release assets and private history are
preserved. Read docs/evidence/PRE_ALPHA4_PUBLICATION_20261022.json. Signed
catalog revision2 retains the same trust key and expires 21 November 2026
at 13:11:43 UTC. No installed driver, helper, Steam or hardware changes occurred.
This publication request is complete; further releases require new approval.
TMR setup remains separate; the GUI backend manages four components.

## Earlier: PRE-ALPHA.4 / alpha2 publication — 22 October 2026

The maintainer now explicitly authorizes pushing the new packages and creating
a tagged release after the requested source/license review. Read
docs/CONTROL_CENTER_ALPHA2_RELEASE.md and docs/RELEASE_PRE_ALPHA_4.md. Publish
alpha2 + core alpha3-20 + optional TMR helper alpha1-2; unchanged optional
components retain PRE-ALPHA.3 bytes. Preserve the public main ancestry and
private development history. No driver/system/hardware changes are authorized.
Rebase only project files onto the fully source-audited alpha1 dependency
baseline, then verify every third-party byte/owner and new source lock. Pair
AppImage with full corresponding sources/notices. Clean neutral package builds
must match tested runtime/helper pins. Existing key signs monotonic revision2;
preserve trust anchor, historical guards and version immutability. New catalog
becomes public only after its assets are downloadable and verified.
TMR remains separately installed/enabled; do not imply the four-component GUI
automatically handles the optional fifth helper. Readable setup/recovery notes
and PRE-ALPHA warnings remain required. No running-driver changes or new tests.

## Earlier: normal Control Center calibration / alpha2 — 22 October 2026

The maintainer requests promoting the accepted TMR path into normal Control
Center and simplifying the interface, offline only. Read
docs/CONTROL_CENTER_NORMAL_CALIBRATION.md. Normal reviewed bundles load TMR pins
without helper/device I/O; an explicit dialog click still owns authorization.
Demo/rehearsals stay isolated. Package and calibration actions now coexist but
must exclude each other through model AND bridge guards; preserve actual worker
return/uncertain-result locks. No automatic TMR-helper setup, module opt-in or
new signed driver catalog. Existing published packages do not gain TMR through
an AppImage alone. Keep the three-phase guide, readiness bits, one-shot commands,
freshness/instance/lease safeguards and the display polling correction intact.
Technical status stays in System details; planned firmware cards start collapsed.
Build/test local alpha2 with synthetic data, document and commit locally only.
No hardware, installation, activation, publication or push; keep gyro work paused.
Validation: 603 cases and five synthetic final-AppImage smoke lanes passed;
preserve queued-return and late-cleanup-error regression coverage.
The earlier hardware receipts below retain their separate acceptance scope.

## Earlier: ZZZ TMR calibration and off/on retention passed — 22 October 2026

Read docs/CONTROL_CENTER_TMR_PERMISSION.md and
docs/evidence/TMR_ZZZ_CALIBRATION_20261022.json. The maintainer selected ZZZ105e
beside the standard109c receiver and completed one guided Start/readiness/Finish
workflow with the already installed core alpha3-20/helper alpha1-2. Read-only
status confirmed finished, empty error/cleanup_error and no held TMR lease.
Three passive ten-second windows (200 host snapshots each) measured the ZZZ
left stick before, after and after explicitly authorized controller off/on.
Mean X/Y changed from -0.9743%/+1.1025% to 0%/-0.0031%; both post-calibration
windows stayed at raw 0/-1 without observed variation. The maintainer confirms
movement response after reconnect and centered, quiet sticks. The receiver
reenumerated: preserve separate instance identities, never merge their streams.
This is observed retention across ordinary off/on, not coefficient/NVM readback
or proof of complete RAM power loss. Normal109c persistence, right-stick numeric
quality, other firmware/platforms and live cancellation/loss remain untested.
No more calibration, reconnect, Resume, installation or push follows from this
acceptance. Record/commit locally; preserve installation and paused gyro work.
Earlier checkpoints below retain their historical scope.

## Earlier: TMR display polling correction — 22 October 2026

First calibration update: the maintainer then gave an explicit calibration Go.
Using the same corrected GUI and native instance, they reported both sticks
ready and clicked Finish once after release/centering guidance. GUI reported
Finish submitted. Read-only manager status confirmed last TMR state finished,
empty error/cleanup_error, no held lease, active native input on the same USB
instance; the helper exited. Maintainer confirms centered sticks/full travel
and normal buttons, triggers and all four paddles in the independent KDE test.
See docs/evidence/TMR_FIRST_LIVE_CALIBRATION_20261022.json. This is one normal
109c workflow and same-connection functional acceptance, not power-cycle/NVM
readback, quantified calibration quality or ZZZ/CachyOS acceptance. No extra
storage ACK is required. Calibration is finished; do not send another Finish
or Exit, replay the Go, power-cycle or start another run automatically.
Keep current installation; document/local commit only, no push. Earlier
preview/offline checkpoints below retain their historical scope.

Deployment/preview update: the maintainer approved the matching Mainrig update
and a display/CPU check, with calibration still gated by a new Go. Local core
alpha3-20 and helper alpha1-2 are installed and verified. Kernel/shared sources
are byte-identical to revision 19; temporary TMR opt-in and motion settings
were restored, service active/enabled. One Resume completed native startup.
An initial journal-cursor precondition stopped BEFORE Resume; its log is kept,
the read query was corrected, and no duplicate Resume occurred.
The corrected GUI uses matching helper pins. Maintainer confirms steady Start
and both plots without perceived delay. Ten-second live CPU means: manager
6.3%, GUI 5.1%, helper 0.9% (100% = one core); previous 49% was a screenshot, not an
identical benchmark. See docs/evidence/TMR_DISPLAY_UPDATE_20261022.json.
Preview remains open; no Start/Finish or calibration acceptance. Wait for a new
Go before calibration. No further install, rebind, replay or push is implied.
The following offline checkpoint retains its earlier scope.

Read docs/TMR_DISPLAY_POLLING_FIX.md and its receipt. The separately approved
live GUI opened and showed moving sticks; the maintainer did not press Start.
They reported flashing Start, display lag and high manager CPU. Explicit dialog
cancel left the main window open and removed the reported CPU load. Calibration
is not accepted; no repeat or live relaunch follows from this report.
Offline fixes separate display reads from action busy, coalesce a single pending
click, discard it on close/loss and use a fixed 33ms timer without poll backlog.
One checked snapshot replaces duplicate helper polls. Pinned TMR reads/watchdog
use fresh exact metadata and kernel lease/token/epoch checks without walking all
process FDs. Full ownership scans remain on admission and before/after each real
Start/Finish/Exit; no cached authorization. No kernel/protocol changes, weakened
freshness, synthetic heartbeat or command retry. CPU benchmark is synthetic,
not a live acceptance claim. Stage matching manager/helper/GUI pins together;
installed alpha3-19/helper alpha1-1 and the old GUI snapshot remain unchanged.
Run regression, document and commit locally; no install, system restart, new
hardware run or push. Gyro precision work remains paused.

## Earlier: scoped TMR GUI/permission path — 22 October 2026

Activation update: see docs/evidence/TMR_MAINRIG_ACTIVATION_20261022.json.
Explicitly authorized module TMR opt-in/service start/one Resume completed;
normal109c native runtime active, pad+IMU and input publication confirmed. No
persistent TMR option, no helper/lease/calibration command. Wait for explicit Go
before the real GUI calibration. Initial observer stopped on transient empty
bConfigurationValue during expected handover; read-only follow-up confirmed the
same bootstrap succeeded, no second Resume. Keep that cause separate from
actual driver failures and preserve the private observation log.
The installation/offline checkpoints below are historical, not current state.

Deployment update: read docs/evidence/TMR_MAINRIG_INSTALL_20261022.json. The
maintainer then approved Mainrig installation: local alpha3-19 core + alpha1-1
TMR helper verified, DKMS/initramfs complete, module absent and service inactive,
enabled preference preserved. No Resume/TMR/helper invocation, receiver remains
removed. Do not activate without the next approval. The local recipe alone uses
pkgrel19; public/tracked recipe, releases and update catalog are unchanged.
The offline-only statements below describe the preceding implementation step.

Read docs/CONTROL_CENTER_TMR_PERMISSION.md and its receipt. New explicit
experimental-tmr mode connects accepted QML through a serial background worker,
a separate fixed root-owned Polkit helper and native manager maintenance API.
No elevated AppImage scripts, arbitrary commands/paths/USB, haptics or package
permission reuse. One auth process/session; explicit target selection before
Start, genuine RX metadata, one-shot Finish/Exit and local-only failure cleanup.
New root-only TMR list returns admissible selection tokens without opening an FD.
Old RF-identity Channel stays strict by default. Only the helper explicitly opts
into separately named fresh_e0_continuity_only/e0-snapshot capabilities and
connected=False (no RF attestation). Short reconnects can remain invisible;
never manufacture heartbeat from a repeated snapshot or GUI time. Display
raw-byte signs +,-,+,- are still an unvalidated plotting convention, not stored
calibration. No extra NVM ACK or automatic replay. Uncertain return stays blocked.
Default app/installed helpers/driver unchanged; normal first-run/package setup
never installs this new helper. Optional offline companion staging pins eight
own files; later helper installation, module opt-in and hardware need separate
approval. No install, activation, live/password test, network or push here.
43 new pipe/manager/permission tests and 12 real-QML worker tests; retain all
existing regressions and demo isolation. No firmware work, precision gyro
remains paused. Document results and commit locally only.

## Earlier: TMR USB framing follow-up — 22 October 2026

Read docs/TMR_USB_FRAMING.md and docs/evidence/TMR_USB_FRAMING_20261022.json.
Static Nexus/FW review closes the DG native endpoint2 callback and actual-length
queue ingress. Existing OUT64 candidate is fully described and receiver-backed:
0f 00 seq 03 fe op parts, 57 zero bytes; op/parts=00/03,01/00,02/00.
Distinguish provider-proven three bytes / cached GIP header encoding from the
chosen USB64 padding; pinned local xone corroborates length03 and ACK flag off.
The Windows provider implementation and exact original USB transfer remain
unobserved. Do not call this a Windows capture or successful hardware test.
DG144/510/604 callback94e and DV209/515/608 parser1c98 agree; newer DG queue
offset2e0 replaces2dc. Never put those firmware RAM addresses in the driver.
USB seq is not the dongle-generated A0 duplicate key; no extra host RF CRC or
new storage ACK. Queue/link/runtime conditions still apply, no host retry.
39 bounded ranges/515 records, 88 FW and 11 Nexus anchors, 13 changed-call and
three changed-pointer checks; decoder unchanged and known limits retained.
Validation: 455 alpha/package cases (including three new C-frame contract
tests / 768 vectors), plus 26 license/README/calibration-flow cases passed.
Only offline tests/docs/package-document list change; kernel, manager, GUI,
installed state and AppImage unchanged, experimental_tmr still off. No network,
hardware, install, activation or push. Gyro calibration remains paused and lower
RF research deferred. Next is reviewed scoped GUI/permission integration and a
separately approved controlled run, not repeated broad RF investigation.

## Earlier: narrow TMR kernel/manager interface — 22 October 2026

Read docs/TMR_NATIVE_INTERFACE.md and its receipt. Offline source implementation
adds ABI1 TMR-only getter/commands, exact port/instance/stream/run binding,
exclusive existing control FD, strict E0 snapshot and genuine RX count/time.
experimental_tmr is default false, read-only, not enabled by packaging/service.
CAP_SYS_ADMIN plus root-only bounded manager requests; haptics/GUI permissions
must not authorize calibration. No passthrough, detach or global pause fallback.
Start/Finish/Exit consumed before shared-sequence serialized OUT, once; no replay
or implicit Exit on expiry/loss/close. Finish requires both active+done bits;
no extra storage ACK. Maintenance close never ends ordinary input; old legacy
close semantics remain. First error survives cleanup; uncertain close stays
blocked. Manager defers only that port's jobs/haptics, not other controllers.
The full OUT64/short-GIP frame is an EXPLICIT UNVALIDATED candidate, not a
captured Nexus USB message. Fresh E0 + epoch is continuity only, not RF identity;
short reconnects can be invisible and unchanged E0 may be suppressed. Do not
advertise the old GUI Channel's full capability contract or enable it by default.
No installation, activation, live access, driver-system changes or push in this
step. Accepted preview and both installed drivers stay unchanged; precision
gyro remains paused. The later intentionally imperfect calibration is only a
test proposal; reported current 0.0 is baseline, not measured hardware center.
Run make test, make test-control-center-ui and an offline module build. Keep
the shared header and both manager modules in staged/DKMS sources without an
enablement config. Two already-public ZZZ receipts restore existing package doc
links. Local commit only; hardware and GUI authorization are separate later work.
Validation: make test passed 1,813 Python cases plus compiled C/fake-kernel
checks; Qt/lifecycle 79 cases passed. New maintenance tests: 27 cases plus
20 added actual-kernel adapter scenarios (323 total). Local Garuda 7.3.0-2
module built with W=1/-Werror, zero warnings, no load/install.

## Earlier: offline controller calibration adapter — 22 October 2026

Read docs/CONTROL_CENTER_CALIBRATION_ADAPTER.md. New pure codecs/adapter accept
full E0 reports and issue only the three known internal provider messages to an
injected owner API. No USB frame/header/sequence guess and no live channel.
Default UnavailableChannel performs no I/O; normal GUI/CLI remain unwired.
Existing ABI1 has no TMR operation/full E0 getter; manager status/release/resume
and the haptics broker are not calibration maintenance APIs. Do not misuse them,
GSN_GET_SAMPLE, raw USB, driver detach or a global pause as a replacement.
Future narrow kernel/manager maintenance/stream API needs separate authorization.
No kernel, UAPI, manager or helper changes in this step.
Bind VID/PID, port/instance tokens, actual RF lifetime and run generation; inspect
exclusive expiring native-owner lease before/after each one-shot message. PID
109c/105e is admission scope, not a verified firmware/capability claim. Foreign
reports cannot refresh liveness; changed radio lifetime on unchanged USB tokens
stops the run. Parse full-report bytes30/31, not payload26/27 or buttons; reject
other calibration parts. Raw/processed positions stay separate; source/signs
must be explicit. UI normalization is not calibration data or a physical proof.
Use local report number/real receive time, not wrapping device byte or GUI time.
Preserve first adapter error; separately record failed lease return. Unconfirmed
acquisition or retained cleanup blocks another run without replay/resume. There
is no additional storage ACK requirement. Do not treat lease-shaped objects as
authorization; a future trusted owner must enforce credentials/serialization.
1.5-second E0 age is still a conservative preview rule; unchanged reports may be
suppressed. Review real stream/RF proof before live activation, never fake a
heartbeat. 35 new offline cases; 411 Control Center / 79 Qt-lifecycle tests
passed, plus license/README/Nexus checks. Existing core-package ZZZ doc omission
remains a separately recorded baseline issue, not a driver release acceptance.
Own code GPL-2.0-only; no vendor resources, firmware execution, network/hardware,
installation, driver change or push. Existing accepted preview/driver behavior
and paused precision gyro calibration preserved. Local commit only.

## Earlier: offline Control Center TMR calibration — 22 October 2026

Read docs/CONTROL_CENTER_STICK_CALIBRATION.md. New --rehearse-calibration mode
uses synthetic samples and an in-memory semantic Start/Finish/Exit recorder.
No USB/GIP encoding, live device backend, privilege path or hardware access.
Normal demo/status/package modes and the published AppImage keep calibration
unavailable. Do not reinterpret a receiver/status snapshot as a live session.
Two XY stick plots show independent 24-sector edge coverage; coverage is never
firmware readiness or calibration quality. Only current active+done bits for
both sticks permit explicit Finish, once. No extra storage ACK requirement.
Preparation is cancellable; loss, report gap, invalid current input or transfer
failure is terminal. Fresh monotone samples and exact device/connection/local
generation are required; stale/foreign callbacks cannot start or finish a new
run. Exit once only while started and still fresh/connected; never blind replay
on reconnect. UI cancellation cannot recall a previously delivered dongle job.
The 1.5-second heartbeat limit and 0.8 edge threshold are preview rules, not
measured firmware constants. A real transport/ownership/status adapter and a
separately approved hardware run remain future work. Firmware flashing is
separate; avoid turning hypothetical calibration bricks into a UI blocker.
Run make test-control-center and make test-control-center-ui; software-render
DE/EN/compact dialog states with tests/render_control_center_calibration.py.
Validation: 376 Control Center / 79 Qt-lifecycle cases passed, 36 new. The extra
core-package doc check still fails its existing missing ZZZ acceptance link,
confirmed with the previous HEAD allowlist; no core package is approved here.
Own code GPL-2.0-only, no proprietary bytes. Local commit only; no installation,
push, AppImage publication or changes to either installed driver. Precision
gyro calibration remains paused; existing hardware acceptance is preserved.

## Earlier: TMR sleep/off path and practical failure boundary — 22 October 2026

Read docs/NEXUS_STICK_WAKE_RETENTION.md and its evidence. DV RAM 0xc7a/file
0x50392 reaches an off sequence, not ordinary calibration continuation. The
bounded outer routine ends at 0x50620 in a loop to 0x50530; updated byte counter
0xeb39 below 0x65 skips the extra P33 a0/10 reset request. No time unit or
calibration-retransmission meaning follows. Physical shutdown/reset success,
exact Boot-ROM wake choice and retained SRAM banks remain unproven; callback
word 0x23db0 is an explicit gap. P33 argument 0x80a5 is not a second RAM clear.
Completed normal startup clears sequence/calibration BSS and reloads the RAM
suffix. Boot-argument copies at 0xda30/0xda40 are not old calibration restore.
Finish at 0x2268 requires done bits B+0x1b3b before setting B+0x1b3c; with fresh
zero flags, a lone old Finish sets neither stick request. This is not global
cancellation or proof against late delivery during a later ready session.
Controller reset does not clear dongle pending data. No actual late Finish,
endless calibration retry or calibration-induced brick demonstrated.
Keep the future UI pragmatic: end the current run on loss, no automatic old
Finish/Start/Exit replay, explicit user start for a new run. No extra storage ACK.
A failed calibration/retry is plausible; incorrect stored stick values are a
plausible worse case, not an observed loss-induced outcome or firmware-flash risk.
22 ranges/539 records, 106 transfer controls/mutations, official reference forms,
17 exact P33 witnesses and 16 existing dialog tests passed. Truth tables are
own conditional checks, not target emulation. Known NOT/REP and parallel-export
limits preserved; DV 0xe976 excluded. This bounded follow-up is complete with
stated limits; do not automatically extend the same wake search indefinitely.
Offline documentation/local commit only; no network/hardware, target execution,
installed changes, writable calibration backend or push. Both installations,
deferred driver diagnosis and paused precision gyro calibration preserved.

## Earlier: TMR reconnect reset selection — 22 October 2026

Read docs/NEXUS_STICK_RECONNECT_ROUTES.md and its evidence. DG matching event 5
with D+0x13 zero requests reset via 0x8ef0/0x79fa; otherwise state six is set.
State six selects reset through 0xa5da when D+0x238 is nonzero or D+0x16 is one;
otherwise 0x7960 enables page scan and clears D+0x1bc, not a proven pending purge.
All 18 mode-table entries in 0xa5da converge to the reset tail after helpers.
DV joypadtask consumers are resolved: 0x400008 -> 0x1713e, pairing-record work,
then conditional reset helper 0x8582; 0x40000b -> 0x17118/0x15430, posts sleep
message 0x40000c, optionally HCI Disconnect; 0x40000c -> 0x9694. The helper
0x8582 resets only if (Q|F) and (H|F) are nonzero; Q comes from 0x854e with the
pointer at B+0x538, F is B+0x724, H is 1 & ~B+0x81c. Reset tail 0x85d6 reaches
the established RAM 0x10a primitive. Its returning branch changes three other
fields, not directly last sequence/calibration RAM. Controller reset is not
dongle cancellation. Sleep tail 0x987c reaches distinct RAM 0xc7a; complete
wake/retention remains open. Post-call self-loops are not radio retries.
Reset request is not observed reset success/normal startup; completed startup
has the RAM-clearing effects from the preceding report. No universal purge,
late Finish execution, endless retry or automatic Exit proven. DV 0xe976 stays
excluded; 0x82f0 is not calibration helper 0x82f4. No new persistence ACK or
blind replay. Next: sleep wake/retention, not the now-resolved task destinations.
44 ranges/669 records; 147 transfer and 43 table checks with changed controls;
cached official operand references, bounded intervals and 16 dialog tests passed.
Offline documentation/local commit only. No target execution/emulation,
network/hardware, installed-system/driver changes or push. Both installations,
deferred diagnosis and paused precision gyro calibration preserved.

## Earlier: TMR soft reset and sequence lifetime — 22 October 2026

Read docs/NEXUS_STICK_RESET_LIFETIME.md and its evidence. The earlier external
DG target 0x20008c resolves through the established relative-call alias into
RAM 0x14c / file 0x37174. DV has the matching primitive at RAM 0x10a / file
0x4f822. Both request P33 register 0xa0 bit 4 through the reviewed helper;
independent cached Jieli chip_reset/P33 references support the reset meaning.
Completed normal startup clears DG [0x5b60,0x17804), including pending/copy/
sequence/queue pointer, and DV [0xda60,0x240e8), including last sequence and
calibration RAM. This is not nonvolatile erase or proof every RF reconnect
runs startup. A controller-only reset must not be treated as dongle cancellation.
Same-sequence filtering is one last byte, not a persistent epoch/history.
Redispatch is not effective Finish/storage; calibration guards remain relevant.
No actual late replay, universal purge, endless RF retry or automatic Exit proven.
The decoder misreads exact NOT at DG 0x3715c / DV 0x4f80a as AND; use the
independent official byte witness for this bounded interpretation. REP at 0x46
is also checked against official bytes outside clean decoder ranges. Decoder
unchanged; DV 0xe976 and deferred joypadtask 0x400008/0x40000b remain open.
22 ranges/224 records and hashed anchors; 171 literal/179 short-transfer reference
controls; 11 target checks/mutations; 13 RAM ranges/26 changed boundaries;
16 existing dialog tests passed. Own sequence truth table is not target emulation.
Next: select actual reset versus link-only reconnect through deferred consumers.
No blind Start/Finish/Exit replay or extra persistence ACK requirement.
Offline research/docs/local commit only; no target execution/emulation,
network/hardware, installed-system/driver changes or push. Both installations,
deferred driver diagnosis and paused precision gyro calibration preserved.

## Earlier: TMR loss/reset event paths — 21 October 2026

Read docs/NEXUS_STICK_RESET_PATHS.md and its evidence. DG144 event 5 maps to
0x8b12, DV209 event 5 to 0xe656, matching the local HCI Disconnection Complete
layout. This identifies internal handlers, not user-facing Bluetooth mode or
all physical RF-loss paths. DG state 6 has a scan branch clearing D+0x1bc;
that field gates both inspected output branches. Retained pending data is not
continuous transmission. 0x7960 requests Write Scan Enable 0x0c1a with page-scan 2,
not HCI Disconnect. Other branches reach a soft-reset candidate via 0xa5da,
0x6922, 0x79fa and external 0x20008c; full startup memory effects remain open.
DV clears selected connection fields, not directly B+0x50 or calibration flags.
Deferred joypadtask 0x400008/0x40000b effects remain open. The earlier 0xcf30->0x53f8
candidate is USB-resume/SOF-related; do not call it radio-loss RAM restoration.
0x82f4 clears stick working areas; no event 5 reachability or backup restore is
proven. Preserve distinctions between pending retention, output eligibility,
dispatch deduplication and storage. No universal endless retry, full purge,
replay, exactly-once or automatic Exit claim. DV 0xe976 operand/parallel meaning
is unresolved; exclude it from precise reconnect field-assignment claims.
40 bounded ranges/542 records, 135 anchors, 24 transfer checks/mutations, 4 event
entries/mutations, 60 memory-boundary checks and 16 dialog tests passed. No
firmware/decoder changes. Next: external reset/startup, deferred task handlers,
and sequence lifetime. No new storage ACK requirement or blind command replay.
Offline docs/local commit only; no target execution/emulation, network/hardware,
installed changes or push. Both installations/deferred diagnosis unchanged;
precise gyro paused.

## Earlier: TMR pending commands and reconnect boundaries — 21 October 2026

Read docs/NEXUS_STICK_RECONNECT.md and its evidence. DG144 has three distinct
states: queue D+0x2dc, retained payload D+0xb64 with pending D+0x2d0, and the
per-cycle send gate D+0x2cc. Retry reuses the sequence; counter threshold 0x64
has no established time unit. Normal queue flush at 0x699a resets queue metadata,
not the separate pending copy. Do not generalize bounded mode-reset/link-state
helpers to every loss/reset path or claim all writers have been found.
DV209 at 0xe24a dispatches only a different sequence from B+0x50, saves it and builds
status 0x14; an equal sequence skips dispatch but still builds the response.
DG144 at 0x93ac clears pending only for status 0x14 under the reviewed header/mode
conditions; status 0x15 takes another branch. This is transport-level behavior,
not verified storage, an unconditional header match or global exactly-once.
Do not misread the decoder's branch-to-else predicate as the positive condition,
or count the duplicated export of parallel members as two executions.
Actual reconnect purge/replay and sequence lifetime remain open. Retained bytes
can be formatted again IF their pending state survives and sending resumes;
no hardware replay observed. Explicit Exit restores active stick RAM, but
loss-triggered restore is still unproven. No Finish means no new save in the
reviewed finalizer, not automatic working-RAM reset. Do not replay an uncertain
Finish or blindly send Start/Exit on reconnect. No extra persistence ACK imposed.
22 bounded ranges/331 records, 95 anchors, 15 relative-transfer checks with
mutations, two simple conditional-block checks/four mutations, 256 status
layouts and the 16 existing dialog tests checked. Decoder/sources unchanged.
Only offline research/docs/local commit; no target execution/emulation,
network/hardware, installed-system/driver changes or push. Both installations
and deferred driver diagnosis preserved; precise gyro paused. Next: full
loss/reset writers of pending copy/flag and controller sequence, plus actual
loss-to-calibration-state restoration. Keep the remaining provider/USB gap.

## Earlier: TMR receiver/controller wire path — 21 October 2026

Read docs/NEXUS_STICK_WIRE_PATH.md and its evidence. In the reviewed DG144
dispatch branch, ordinary GIP type 0x0f/selector 0xfe enters D+0x2dc, then the
second radio block with an A0/sequence prefix. Do not substitute the first
D+0x2a4 block. Matching DV209 lengths/check fields lead via the second-block
handler, de2a/23ae and 1c98 to the existing calibration dispatcher, subject to
mode/state/sequence checks. USB cable has a separate route to the same wrapper.
Provider framing, DG USB callback root, lower radio delivery, active firmware
pair and full sequence/CRC semantics remain open. Never publish guessed packets.
DG144 retains a pending copy: direct Nexus dispatch does not rule out lower
transport retries. Its disconnect flush/ACK/reconnect lifetime is unresolved.
Explicit Exit restores active stick RAM; automatic loss-triggered restore is
still unproven. The bounded DV209 state helper 0x4820 has no restore call and does
not touch the calibration flags; do not extrapolate to the whole firmware.
No Finish means no new save in the reviewed finalizer, not guaranteed live-RAM
recovery. No extra persistence ACK required; do not replay an uncertain Finish.
23 static ranges/494 records, 84 anchors, 11 changed-call controls, 195 own
synthetic layouts and the full 16-bit first-length predicate checked. Existing
16 dialog tests retained. Research/docs/local commit only; no firmware/App
execution or emulation, network, hardware, installed changes or push.
Keep both driver installations and deferred diagnosis unchanged; precise gyro
paused. Next: pending A0 lifetime and actual link-loss-to-calibration handling.

## Earlier: TMR transport and interruption followed offline — 21 October 2026

Read docs/NEXUS_STICK_TRANSPORT.md and its evidence. The direct calibration path
now reaches a typed IGipGameControllerProvider: final-object RTTI, constructor
QueryInterface and field flow resolve the provider behind D4X slot 6. The member
at interface+0x70 is complete object+0x80, not its lock at+0x70. Keep the provider ABI
arguments distinct from a complete USB/GIP frame. Native signed HRESULT checking
exists; an operation-specific error result in the dialog is not yet traced.
No extra persistence ACK is required. Without Finish, the reviewed finalization
path does not initiate a new save; Start still changes RAM. Exit restores the
backup for active sticks, not finalized/queued storage. Do not equate link loss
with automatic RAM restoration: the two additional restore callers have table
checks, not an established radio-loss trigger. Input suspend/resume stubs do not
send Exit; higher lifecycle paths remain open. Three new missing-selection
counterexamples bring the existing research-only dialog model to 16 tests.
Next: full provider/USB/receiver route, radio-loss-to-calibration-state handling,
and availability of live stick positions. No implementation or hardware trial.
Preserve both installations; driver diagnosis is deferred. No target execution,
emulation, network, hardware/system/driver change or push. Precise gyro paused.

## Earlier: TMR calibration research resumed offline — 21 October 2026

The maintainer subsequently reports the primary host still has a problem and
asks whether different controller firmware could explain it. The symptom was
not clarified in this follow-up; the older ZZZ firmware is a user report, not
a verified causal comparison. The maintainer defers that investigation and
explicitly resumes Nexus/TMR research. Preserve both installed systems.

Read docs/NEXUS_STICK_READBACK.md and its evidence: the firmware puts active/
ready masks into an E0 report; Nexus has corresponding parser/notification
fields. The separate record loader checks end markers before copying fourteen
halfwords. This is not a readback verification of a fresh Finish transaction.
Finish requests firmware-owned storage; a separate persistence ACK is not a
mandatory new protocol feature or, by itself, a blocker for calibration work.
Do not claim verified durable storage without evidence. Proposed UI: two live
stick indicators, per-stick firmware readiness, Start then Finish OR Exit on
cancel, with instance-bound session handling. No GUI/backend implementation or
hardware trial authorized by this design discussion. Full transport/model and
abort boundaries remain open; firmware updater requirements are separate.
Static research/documentation/local commit only. No network, target execution,
emulation, hardware, driver/system change or push; precise gyro remains paused.

## Earlier: revision 18 accepted for current use — 21 October 2026

After activation, the maintainer reports both hosts working and gyro recognized
in the secondary host's Steam Gaming Mode when the controller is switched on
later, rather than already on at system startup. This is a user observation;
no new live inspection or cause attribution accompanies it. The maintainer
explicitly accepts this working state and requests no further investigation,
tests or changes. Preserve both installations. Do not reopen the gyro timing
question merely to explain the improvement. Earlier failure evidence remains
historical; no general reconnect guarantee or missing-button root cause follows.
Documentation only, local commit, no push. Nexus and precision calibration stay
paused until a new task.

## Earlier: revision 18 activated on both hosts — 21 October 2026

The maintainer subsequently approved one service start and Resume per host.
Both succeeded after a brief same-boot state check: services active/enabled,
managers unpaused, expected modules and existing motion options loaded, no new
reported failures. The primary receiver was then reinserted with the controller
off; read-only observation confirms 109c/gs_native in receiver_wait with its
matching saved lease. Secondary had no observed receiver at activation.
See docs/evidence/START_BUDGET_ACTIVATION_20261021.json. No input, reconnect,
motor or gyro acceptance test occurred. Missing X/Y/RT remains unexplained.
Do not repeat start/Resume or initiate tests without a new task. No source,
configuration, Steam, public release/catalog or push change. Nexus50e8c13 and
precision calibration remain paused.

## Earlier: revision 18 installed on both hosts — 21 October 2026

The maintainer approved installation after the offline manager fix. Both hosts
now have gamesir-native-dkms0.1.0.alpha3-18: primary from16, secondary from17.
Fresh matching headers and compiler-family builds passed for Garuda7.2.11-1 and
CachyOS7.2.11-1-deckify; the known primary Clang patch-version advisory remains.
Thirty private transaction-guard cases passed. Each single package transaction
succeeded through its normal snapshot/DKMS/initramfs hooks; all166 installed
payload files match the candidate. Existing sensor overrides, optional packages,
failure history and service enablement are preserved. No new ZZZ config on the
primary host; secondary's existing ZZZ opt-in retained.
See docs/evidence/START_BUDGET_INSTALLATION_20261021.json. Both services are
inactive, manager state paused, leases empty and native modules unloaded.
No activation, Resume, hardware/reconnect test, public update/catalog, tag or push.
The primary receiver was manually removed and stays out; one Release with no
receiver confirmed return before installation. Secondary had no observed device.
Do not treat installation as acceptance or missing X/Y/RT as fixed. Next: fresh
state check and separately agreed activation/test. Nexus50e8c13 remains saved.

## Earlier: start-budget correction prepared offline — 21 October 2026

Read docs/MANAGER_RECONNECT_FIX.md. Pre-acquisition rate limiting now uses
unowned cooldown with start_retry_in; exact 600-second expiry retires only that
timer and requires a later complete discovery scan. Actual faults/ownership
remain fail-closed. Existing passive status must confirm 60 seconds of healthy
active native runtime before clearing only that port's charges; long gaps,
busy/unknown reads, PM, monitor errors and restart reset the health window.
Receiver standby and readiness alone earn no credit. Keep short-start limits,
attempted tokens, history, pause, one-shot cleanup and foreign-owner guards.
19 new budget tests and 328 related tests pass. No installed files, live status,
USB/input reads, SSH, sudo, driver/kernel/Steam change or push. Local commit
only; no package revision bump. Missing X/Y/RT and earlier ownership loss remain
unexplained. Nexus checkpoint50e8c13 and paused precision calibration retained.
Next: prepare any deployment separately through existing checked update rules;
no automatic migration of an old error string and no live trial yet.

## Earlier: reconnect diagnosis; Nexus saved — 21 October 2026

Nexus checkpoint is local commit 50e8c13 and docs/NEXUS_STICK_STORAGE.md.
Research is paused at the independent EE53 oracle, bus-status semantics and
host-visible verified storage outcome; do not restart target analysis now.
The maintainer reports missing native binding plus X, Y and RT on the primary
host, with similar symptoms previously on the secondary host. Read-only primary
inspection found revision16, an active/enabled manager, and 100a/xpad. One
explicitly approved root status request is consumed: not paused, entry blocked
by "Three starts in 10 minutes; explicit resume required". Raw journals/status
and an offline Fake-backend reproduction stay private under build/.
The same sticky budget behavior reproduces in installed16 and worktree17 after
three successful starts, without Deadband or hardware, beyond 600 seconds and
across a new instance. This proves a policy limitation, not the secondary-host
incident or the missing-button cause. Prior binding loss and -125 initialization
remain separate; the maintainer briefly opened Deadband on the primary host,
but not on the secondary. Do not attribute both incidents to it.
No runtime fix, Release/Resume, device reader, installation, SSH or new hardware
test occurred. Next: separate exhausted start budget from ownership faults;
retain guards against repeated initialization and unknown owners. Missing X/Y/RT
still needs separately agreed passive input evidence. Preserve the fault state.

## Nexus calibration copy and storage completion followed offline — 21 October 2026

Read docs/NEXUS_STICK_STORAGE.md and its evidence before further maintenance
research. EE53 is strongly supported as a fixed negative signed9-displacement
byte store, not postincrement: both eight-halfword loops fill record bytes12–27
and match their restore paths. No exact independent EE53 SDK oracle exists;
the shared decoder remains unchanged. The earlier evidence's postincrement
label is withdrawn, not an ISA fact to carry forward.
The write queue now reaches the registered RAM interrupt handler and internal
`eeprom write over` log. Normal completion and selected status-bit7 rejection
paths share B+0x528; progress advances at submission. Neither flag nor log proves
verified durable storage. NACK register semantics, host result/error routing,
readback, atomicity and recovery remain open. A separate clean/readback path
cannot be assigned to calibration without a call-path proof. Exit still does
not cancel finalized/queued writes. No live maintenance implementation.
Checked 28 bounded ranges / 745 records, 41 anchors, 16 edges, four EE53 sites,
46 sibling SDK examples, four cross-image fragments and 13 negative controls.
Thirteen existing dialog-model tests and the reproducible archive test pass.
Local research/documentation commit only; no execution/emulation of targets,
network, hardware, installed-system/driver change or push. Precision gyro paused.

## Earlier: Nexus firmware Start/Finish/Exit — 21 October 2026

Read docs/NEXUS_STICK_FIRMWARE.md and its evidence before further calibration
work. DV209 dispatch matches the Nexus operation semantics: Start backs up RAM
values before resetting working state; Finish sets completion-request bits;
a later consumer packs and queues two 30-byte records at logical offsets 0x1700/
0x1720. Exit clears active/complete/request bits and restores RAM values for still
active sticks. It is not cancellation of already finalized/queued storage work.
An Exit-then-Finish sequence alone does not prove accidental saving: completed
Exit removes the required ready bits, absent another session/writer. Full backup
copy was bounded by unsupported EE53 at this checkpoint; the follow-up above
narrows that gap and traces internal completion. Verified persistence, atomicity,
transport framing and power-loss recovery remain open. Do not promise rollback
or implement live maintenance commands. 28 bounded decode ranges / 692 instruction
records, 30 anchors, 15 call edges and three cross-image matching fragments were
checked; original binaries and decompilates stay private. No firmware execution,
emulation, hardware/network, installed-system/driver changes or push. Precision
gyro calibration remains paused.

## Nexus stick-calibration flow followed offline — 21 October 2026

Read docs/NEXUS_STICK_CALIBRATION_FLOW.md and its evidence. Native metadata now
ties the shared Calibrate body explicitly to G7Pro.Proxy; this is not complete
runtime variant/provider routing. The UI sends Finish automatically before the
Finish button. Closing step3 requests Exit but does not cancel the pending
510-ms completion; the own transition model exhibits Exit followed by Finish.
Do not call this a reproduced vendor-app/hardware bug or infer persistent save,
rollback, full USB framing, or a safe calibration command. Thirteen synthetic
cases cover normal completion and interruption/identity counterexamples; they
do not execute Nexus or emulate Vue. Keep private source/decompiler data out
of Git. Only local research/docs/tests change; no hardware/network/installation,
driver/app/system changes or push. Precision gyro calibration remains paused.

## Nexus maintenance research resumed offline — 21 October 2026

The maintainer is observing the installed drivers in ordinary use. Current work
is static Nexus research for TMR-stick calibration and separate controller/dongle
firmware updates, using the existing isolated REA setup. Read
docs/NEXUS_MAINTENANCE_RESEARCH.md and its evidence. Six JL functions, source
identities, UI landmarks and critical instruction anchors were checked locally.
No application/firmware execution, network, hardware or installed-system action.
Keep runtime drivers and precise gyro calibration unchanged; local commits only.
The calibration dialog drives a device operation; framing, model routing,
persistence and rollback remain open. Finish/Exit omit calPart in the UI.
Do not equate UI completion, CRC, a zero transport return or a dual-bank name
with persistent calibration or recoverable firmware update. Default update
findings do not cover the alternate branch/model choice. Status/CRC/retry
limitations are static findings, not demonstrated hardware bugs. No zero-brick
guarantee is possible; writing remains blocked until identity, authenticity,
transfer, protection and recovery are substantiated. Neither the kernel nor
Control Center gains live maintenance commands here.

## Reader-friendly public README — 21 October 2026

The maintainer approved the shorter README, first-person project motivation and
Control Center screenshot directly after the introduction. Keep the short
PRE-ALPHA warning visible and the complete original text in an expandable block.
Keep credits personal and accurate: Deadband and g7ctl are independent technical
references. Installation should describe user actions; protocol/test detail stays
in linked docs. Check claims against published versions, not local candidates.
The screenshot belongs in the repository and packaged documentation. This change
publishes documentation only; no driver/app binaries, signed catalogs or new tag.

## Control Center shutdown lifetime corrected offline — 21 October 2026

Read docs/CONTROL_CENTER_SHUTDOWN.md. The published alpha1 entry point destroyed
its model before QML; explicit deferred engine deletion after finishing workers
now preserves the model until QML is gone. Exercise actual main() in a fresh
process, not only create_engine() with test-managed cleanup. Preserve the
pre-authentication-only cancellation rule and wait for transaction workers.
419 app tests, seven bundled-runtime lifecycle scenarios and four packaged
synthetic lanes pass. Exact reported warning text was not reproduced headlessly;
do not claim interactive desktop acceptance. New local image is unpublished;
do not overwrite the original or reuse its source lock as new release approval.
No installed helper/driver/hardware changes or push; gyro calibration paused.

## ZZZ activation and Steam/Gamescope input accepted — 21 October 2026

One approved service start/Resume on the secondary CachyOS host passed with
revision 17 and 105e motion enabled. With Steam already running, switching on the
ZZZ produced direct 105e native startup and confirmed paired input publication.
The maintainer confirms three gyro axes without Guide, four independent paddles,
ordinary inputs, combined presses/releases and a responsive desktop. A later
maintainer report also confirms Eden gyro, with both Eden and Steam displays
matching physical movements; no extra agent-run observation or system change.
See docs/evidence/ZZZ_GYRO_ACCEPTANCE_20261021.json. Sensor registration preceded
gamepad publication by about 1.15 seconds; no 100a-to109c handover occurred. This
is evidence of the intended order, not proof of a sole Steam compatibility cause.
No configuration changes/retries/main-host update/push. Service stays active.
The maintainer now defers further investigation of the standard/ZZZ Steam
startup contrast in favor of ordinary-use observations; no extra tests or
background monitoring were started. A timing/session coincidence remains possible.
Keep long-off/reconnect/partial-input failures unresolved, precise calibration
paused and ZZZ motor acceptance separate. Do not repeat unrelated checks.

## ZZZ motion package installed; activation pending — 21 October 2026

The maintainer approved installation on the secondary CachyOS host. Revision17
was target-built without warnings and installed once through the normal package
hooks, with all157 payload files verified. Added only the explicit105e92 config;
standard sensor/receiver settings, optional packages and failure history retained.
Service remains enabled but inactive, module absent, manager paused/leases empty.
Read docs/evidence/ZZZ_GYRO_INSTALLATION_20261021.json before further deployment.
No activation/Resume/new hardware acceptance or main-host update occurred.
Do not present the ZZZ axes/scale or long-off/reconnect issues as validated/fixed.
Revision16 rollback retained; no public catalog/signing/push changes authorized.

## ZZZ motion extension prepared offline — 21 October 2026

Revision 17 extends the same module/manager to `105e` behind the default-off
experimental_gyro_105e flag plus experimental_gyro. Read
docs/ZZZ_GYRO_EXTENSION.md. The new explicit request supersedes the historical
109c-only development restriction, not hardware/installation boundaries.
Preserve the standard profile, raw IIO, real PID/paired identity, exact readiness
and cleanup guards, direct105e bootstrap and all existing motor/paddle paths.
0.07 dps/raw, axis order and 8192 counts/g are unvalidated ZZZ candidates;
standard-model qualitative acceptance is not a ZZZ calibration certificate.
No installation, module/service/config/Steam change, SSH or live test in this
step. Prepare complete offline package, tests and local commit; no push.
Long-off binding failures and partial ordinary input after reconnect are new
unresolved user reports; do not present this gyro extension as their fix.
Precise calibration stays paused. Public signed catalog remains revision1.

## Published Control Center alpha1 — 21 October 2026

The approved clean app snapshot eb99dce is on public main. The existing
v0.1.0-pre-alpha.3 release now also contains the five app assets: AppImage,
complete corresponding sources, distribution lock, manifest and checksums.
GitHub's SHA256 digest, byte size and uploaded state match every local asset;
all previous release asset IDs/sizes/digests remain unchanged, with no new tag.
The actual public signed catalog matches unchanged revision1 and verifies in
both the bundled app runtime and installed helper imported as an ordinary user.
No root invocation/transaction, driver/helper/service/Steam/hardware change.

The license/source publication gap is closed for this Garuda x86_64/glibc2.44
profile. 412 app cases and four final packaged synthetic lanes passed. Keep
private working history and key material private. The encrypted separate-storage
backup copy is complete; no regeneration or resigning. Further app uploads must
retain matching sources/notices/lock/manifest/checksums. Catalog expiry remains
20 November2026,12:36UTC. Driver faults reported on both PCs are the separate
next task; this publication does not fix or certify them. Gyro calibration paused.
See docs/evidence/CONTROL_CENTER_PUBLICATION_20261021.json.

## Earlier Control Center distribution and publication — 21 October 2026

The maintainer explicitly requests finishing and pushing the AppImage before
investigating different driver faults on both PCs. Scope is app/source/metadata
publication only: no live driver/helper/service/Steam/hardware changes. Keep
alpha3-16 installed state untouched and precise gyro calibration paused.
Reuse the verified encrypted backup and exact signed revision1; no private-key
read, regeneration or resigning. The requested encrypted off-device copy was
hash-verified on separate network storage (not offline media).

The license/source gap is closed for the reviewed Garuda x86_64/glibc2.44
AppImage profile: 1,859 payload files, 1,530 source-kit files,77 components,
complete recipes/patches/submodules/notices. 412 app tests/25 groups including
61 QML and four final packaged synthetic lanes pass; four real GitHub package
archives pass both download and ordinary-user installed-verifier checks.
Publish binary plus companion sources/lock/manifest/checksums together. Preserve
existing release assets and tag; publish the unchanged signed revision1 at
updates/pre-alpha.json (expires20 November2026,12:36UTC). No new tag is requested.
Use a clean final-tree public snapshot atop public main; retain private working
history locally. See docs/CONTROL_CENTER_DISTRIBUTION.md and its evidence.

## Signed-helper AppImage reuse accepted locally (21 October 2026)

After explicit approval, the final reviewed AppImage was opened as the ordinary
user with actual status data, without demo/rehearsal options. Image SHA256 and
staged inputs match the retained build. Its bundled runtime's independent
passive first-run inspection returned idle with no error, setup review/session
or authentication/package invocation. The maintainer confirmed the new main
window appeared normally, with no helper-setup offer or password window.

Read-only postchecks found all thirteen helper hashes and helper/policy/retained
old-executor/cache/license metadata unchanged. The app remains open. No package
installation/removal, updates lookup/download, driver/service/module/Steam change,
hardware test, network or publication occurred. This accepts local Garuda/KDE
reuse of the new signed helper, not signed-download/package acceptance or broader
platform support. Public rollout gates and paused gyro calibration remain.
See docs/evidence/CONTROL_CENTER_SIGNED_HELPER_APPIMAGE_ACCEPTANCE_20261021.json.

## Signed helper migration accepted locally (21 October 2026)

Following explicit approval of the newly pinned migration-only plan, the single
run completed with verified_migration/policy_restored and no error. The existing
recovery-verified encrypted key backup was reused without a passphrase prompt,
private-key read, regeneration, decryption or overwrite. The corrected exact
per-path ownership guard passed. No retry, rollback or cleanup was performed.

Independent read-only postchecks confirm all thirteen active helper files match
the approved new hashes, root ownership, modes and single-link requirements;
there are no extra executor entries. The complete old executor is retained at
its fixed before-signed-v1 sibling with original file/directory inodes and
metadata. The identical policy retains its original inode/hash/metadata and
registered auth_admin action. Cache/license directory metadata and the encrypted
backup hash/inode/metadata are unchanged. Candidate, held-policy and failed-new
paths are absent. No package install/removal, driver/service/module/Steam change,
hardware access, AppImage launch, network request, publication or push occurred.

This consumes the one-time migration approval. Do NOT repeat apply or invoke
rollback automatically. The final local AppImage matches the now installed
public-key-bound helper, but no new GUI/package acceptance was performed here.
Public signed-channel publication, actual download/package acceptance, runtime/
corresponding-source redistribution audit and off-device encrypted-backup copy
confirmation remain separate pending rollout gates. Gyro calibration stays paused.
See docs/evidence/CONTROL_CENTER_HELPER_MIGRATION_ACCEPTANCE_20261021.json.

## Ownership guard corrected offline; migration-only plan ready (21 October 2026)

Following the maintainer request, the migration now checks each of its thirteen
fixed helper paths separately. Each query must return exactly 1, empty stdout
and exactly that path's unowned diagnostic. Never accept arbitrary nonzero
codes or silently skip a path. This removes the erroneous aggregate-status
assumption (the observed thirteen missing owners returned 13), retaining all
other ownership/runtime/quiescence/state/rollback protections.

334 Control Center tests in 17 groups pass, including 26 migration tests and
seven new regressions: reproduced aggregate 13, all per-file queries, owned
paths at every position, invalid codes/diagnostics/stdout, timeout and blocking
before any privileged command. No actual host package query or live migration
was run during this correction. The installed helper/driver remain unchanged.
A new exact migration-only plan pins corrected sources; old/new root payloads,
public key and all 19 privileged commands are unchanged. The existing encrypted
backup matches the earlier recovery-verified hash and safe 0600 metadata; it was
not decrypted/recreated and the private key was not read. No new signing.
The previous final AppImage still matches the root payload; this fix is in the
separate maintainer migration path, never invoked by normal first-run GUI.

Execution still needs approval of the newly pinned plan, passive backup recheck,
then one migration-only run/password flow and read-only postcheck. Do not rerun
the old backup-then-migration command or overwrite the existing backup. No
installation/activation/hardware/system change or publication under preparation.
Off-device backup confirmation and public rollout gates remain open.
See docs/evidence/CONTROL_CENTER_OWNERSHIP_FIX_20261021.json and the normal-user
flow in docs/CONTROL_CENTER_FIRST_RUN.md. Gyro calibration remains paused.

## Approved handover stopped safely after verified backup (21 October 2026)

The maintainer approved the complete encrypted-backup/helper-only handover.
The real production-key backup was created with hidden terminal input and
verified by RAM-only recovery/public-key identity. The local encrypted file is
0600, user-owned and single-link; an off-device copy is still pending. Do NOT
rerun the original backup-then-migration command: its exclusive destination now
exists. Preserve the key, backup and signed catalog; no regeneration/resigning.

Migration stopped in preflight before any sudo/system mutation: the exact
thirteen-path ownership query returned 13 with all thirteen expected unowned
file diagnostics and empty stdout, while our guard incorrectly required 1.
Independent checks confirm all 13 old helper files retain hash/owner/mode/inode/
mtime, the executor/license/cache directories retain metadata, and all migration
staging/backup/held-policy paths are absent. No driver, bridge, Steam, module,
service, package or publication action occurred; no automatic retry/rollback.
Only read-only diagnosis followed. The signed helper has NOT been installed.
Next: correct this aggregate return-code assumption offline with regression
coverage, then prepare a new exact migration-only approval reusing the verified
backup. Do not loosen ownership diagnostics or change approved pinned bytes
silently. Latest instruction after this run is checks only.
See docs/evidence/CONTROL_CENTER_HANDOVER_EXECUTION_20261021.json.

## Consolidated handover and final local AppImage prepared (21 October 2026)

Latest request authorizes completing all offline backup/migration/AppImage
preparation in one pass, testing and showing a concrete consolidated approval
plan. No real backup of the production key, authentication, helper installation,
publication/push or live driver/Steam/hardware change yet. Reuse unaffected
same-day facts; no repetitive inventories or per-file confirmation rounds.
Follow docs/CONTROL_CENTER_HANDOVER.md. Maintainer-only control_center_handover
CLI verifies the exact plan/source/AppDir/image, then (only after approval)
encrypted backup with hidden controlling-terminal passphrase twice, then fixed
helper-only migration. Do NOT execute --apply/--rollback under preparation.
Only public RFC fixture keys were encrypted in tests; production key not read.
38 new cases,388 full Control Center cases/24 groups incl61 QML, four packaged
synthetic lanes and actual-old/new-byte fixture migration/recovery pass.
Final local image SHA256 is
19cacca0bac2ac009749c05065a9d4f81ca050d9aa1beabab72cf4aa508d7ad9.
Legacy13-file manifest is independent; current13 helper pins/public anchor stay
unchanged from the production build. Exact whole-directory save/switch, policy
held/restored last, sealed inputs, no package-owned/extra/changed helper, quiet
root executor/ALPM checks, preserved cache/license/legacy/backups. Three fixed
root find queries only check protected-state filename presence, never its
contents; any signed state blocks legacy migration/recovery. Nineteen fixed
system calls only; no root AppImage/user Python/shell, root state reset or
automatic retry/rollback/cleanup. Recovery covers partial forward/reverse
renames and retains failed/new bytes. Secret entry is tty-only/no echo/fallback;
PKCS8/PBES2 AES256CBC/PBKDF2SHA256 600000 and RAM-only restoration/identity check.
An encrypted local file is not off-device backup: external copy confirmation
remains before rollout. Generic first-run still refuses changed/partial helper;
no GUI auto-migration or end-user signing-key management. Keep machine-specific
plan/commands/key paths ignored. Locally commit scoped code/docs; no key
generation/re-signing, package/driver action, SSH or push. Runtime/source public
distribution audit and real signed channel/package acceptance remain separate;
gyro calibration paused. Finish preparation before requesting one combined
execution approval, never many artificial intermediate approvals.

## Earlier production key and offline-bound build completed (21 October 2026)

The maintainer explicitly approved production key creation and offline builds,
then checks only. A new Ed25519 release key was generated exclusively outside
Git in a user0700 custody directory, private file0600/single link, using system
OpenSSL without private terminal/log output. Do NOT generate it again or copy
it into repository/build/AppImage. Only the public policy is tracked at
packaging/control-center/release-signing-policy.json; key ID
5d9450389dafad61bb573c277557a62484e514c96dcb1acd40b9bcfe5f71544a.
The explicit helper/AppImage profile shares that public anchor, verified offline
against catalog revision1, all four already audited release archives and five
removal records. Signed history is retained outside Git; private-key encrypted
offline backup remains pending. Never treat catalog-history retention as a
private-key backup. Future signing must retain/increase revisions; do not
overwrite/re-sign revision1 with different bytes or auto-regenerate keys.
67 unit/packaging +3 QML tests, four packaged smoke lanes, both actual-public-
anchor verifiers/negative cases and inclusion checks passed. Thirteen installed
helper leaves and three directory metadata snapshots remain identical. No root
authentication, helper/trust/state deployment, real network, package operation,
service/module/driver/Steam/hardware change or publication/push. Generic defaults
still have no key; only the explicitly reviewed build opts in. Helper migration
implementation/testing/approval, encrypted backup and public distribution audit
remain separate pending gates. Source/code modules and installed alpha3-16 stay
unchanged; gyro calibration stays paused. Locally commit public data/docs only.

## Earlier production signing and helper migration proposal (21 October 2026)

Latest maintainer request is preparation and an approval plan first: no real
key generation, installation/helper replacement, signing/publication or live
driver change yet. Ordinary-user read-only inspection matched all thirteen
installed helper leaves and dedicated directory modes against independent
accepted pins. Five helper modules plus the future public-key catalog change;
entry/policy/native bridge/license and other modules retain their bytes.
Cache contents were not read or assumed empty. Keep private inventories and
exact custody/backup paths in ignored output. Reuse unaffected same-day facts.
Follow docs/CONTROL_CENTER_SIGNING_PROVISIONING.md: external private key,
public fingerprint review, one offline-bound AppImage/helper build, then a
separately approved exact helper-only migration with preserved complete old
executor/policy/cache. Current first-run setup must not repair/update existing
helpers. Final deployment pins depend on the real key and are pending; the
proposed privileged migration is not implemented/tested/executed. No root
AppImage/user script, incremental mixed modules, state reset, automatic retry,
package action, SSH or push. Publishing and real signed-package tests remain
separate. Gyro calibration stays paused; locally commit scoped preparation.

## Signed update path offline (21 October 2026)

Latest maintainer request authorizes offline signed release updates for the
AppImage and package helper, suitable tests and a local commit only. No real
network, production key generation/provisioning, publication/push, installation,
helper/state deployment, service/driver/hardware/Steam change. Stable locally
reviewed Ed25519 public-key policy; exact signed bytes via system OpenSSL, closed
version-3 requests and independent root verification. Preserve legacy no-key
path, all archive/dependency/guard/postcheck boundaries and explicit auth.
Reject replay/downgrade/rebuild and changed guard history. Under ALPM lock,
checkpoint accepted catalog metadata atomically; never record package success
from that state alone. Retain safe offline removal and cache separation. Test
keys are publicly known fixtures, never production anchors. No active endpoint
or keys are claimed. Update docs/state/roadmap and locally commit; gyro paused.

## Release package upload schema (21 October 2026)

Latest follow-up authorizes embedding the reviewed public package hashes in a
new local AppImage and testing it without installation, authentication, live
driver/helper changes or publication. Explicit metadata-only bundle; retain
accepted removal records and previously reviewed Steam upgrade rule. Reuse
the audited public package bytes/CDN acceptance from this same-day workflow.
The maintainer additionally requires future driver releases without replacing
the AppImage. Current immutable package/helper pins do not provide that feature;
design a separately signed release-catalog trust path for both GUI and root
helper, never silently trust GitHub's latest hash or overwrite installed trust.
Do not claim automatic update readiness from this current pinned rebuild.

The maintainer explicitly approved supplementing existing release
v0.1.0-pre-alpha.3 with reviewed installable ALPM packages, checksums and
manifest. Build from its exact public tag in a neutral directory; preserve
existing assets/tag and running systems. No new release/tag, installed helper
catalog update, package installation/removal or driver activation is implied.
Future package publications must follow docs/RELEASE_PACKAGE_SCHEMA.md:
separate core/Steam/Gamescope/bridge archives, exact source provenance,
SHA256/size/identity/dependency/cleanup-guard records and AppImage-verifier
acceptance. Source archives alone are not installable packages. Remote metadata
never approves itself; new archive bytes need independently reviewed AppImage
and protected helper pins. Keep future publication approval explicit.

Reuse unaffected checks during an uninterrupted same-day workflow. Recheck
affected state after a change or interruption, and retain transaction safety
gates; do not repeat the entire inventory without a reason.

## Control Center — full package remove/reinstall rehearsal (21 October 2026)

The maintainer repeats the offline GitHub-source preparation and wants a later
complete uninstall/reinstall test. The explicit no-install/live-driver-change
boundary still applies: prepare fixtures and a reviewable staged plan only,
no live inventory, network, GUI launch, authentication, removal/install,
helper/service/module/driver/bridge change or push. Scope means installed
GameSir package components; retain AppImage/package helper as the reinstall
tool, user settings/recovery records and unrelated packages/controllers.
Exercise core+bridge and all-four-component synthetic remove -> verified
absence -> distinct fresh release-install session; exact selected packages,
explicit separate confirmations, dependency guards, failed removal, download
failure and unexpected remaining module. No automatic chaining, force unload,
rollback or unreviewed same-version repair. Old live receipts are historical,
not a fresh inventory; real assets/catalog/download and complete removal need
their own later preflight/approval. Keep reviewed offline recovery packages
before a live removal; no public binary availability is claimed. Add scoped
docs/regressions and locally commit, gyro paused.

## Control Center — GitHub package source offline (21 October 2026)

Latest instruction authorizes offline implementation/tests of reviewed GitHub
release downloads only. No network/live AppImage/auth/installed-helper/package/
driver/bridge/service/Steam change, SSH, publication or push. Preserve accepted
first-/second-start artifact and installed core16/bridge2. Public binary catalog
stays empty; do not invent available assets/URLs or turn staging hashes into
approval. Build-only metadata maps exact reviewed components to filenames in
the fixed project repository; trusted tags/sizes/hashes/guards stay in the
independently reviewed catalog. Root catalog/protocol and helper code remain
unchanged. No latest/API self-trust or arbitrary URL. Download only on explicit
selected install preparation, as ordinary user; never on startup, helper setup,
property refresh or removal. Bounded verified immutable bytes, scoped TLS/CDN
redirects, cancellation/late-result rejection, no cache/extract/execute/retry;
fresh host/helper checks before and after. Only then show the separate plan/
authentication boundary; downloads never install. Use injected HTTPS/host/
helper fakes, preserve embedded-bundle/first-run paths and test real offscreen
QML. Keep platform/runtime/publication and real CDN acceptance gates explicit.
Update docs/manifest, locally commit only; gyro calibration stays paused.

## Control Center — local second-start reuse accepted (21 October 2026)

The maintainer authorized a second launch of the exact reviewed AppImage, with
fresh passive gates only and no setup/auth/package action. Image digest and
installed helper/action checks passed; fresh FirstInspection was idle with no
setup review/session. A new AppImage process opened, and the maintainer reported
normal main window, no setup offer and no password window. Independent post-
checks confirmed unchanged bytes/owners/modes/inodes/mtime for all thirteen
leaves/three directories, preserved old six leaves/backups and unchanged core16/
bridge2/module/service baseline, Steam still absent. No root/auth/setup/package
action or driver/bridge/Steam change. Keep windows user-controlled; no more
operations or backup cleanup, SSH/push without a new request. Scope remains
local reviewed Garuda reuse, not generic/Gamescope acceptance. Commit scoped
docs locally, private receipts ignored; gyro calibration stays paused.

## Control Center — local AppImage first-run setup accepted (21 October 2026)

Latest explicit approval covered fresh passive preflight and helper-only setup
through the reviewed AppImage/password flow, then checks only. Retained-backup
gates passed; exact image digest/source/payload pins, Garuda kernel/header
profile and missing-helper prerequisites passed with thirteen leaves/three
directories and no package action. The maintainer completed the GUI setup and
reported Helper successfully set up. Independent passive installed-source,
hash/mode/root-owner/loaded-policy checks passed; fresh FirstInspection reports
idle/exact existing reuse without authentication. All old backups, unopened
old cache inode and six legacy authorization leaves remain intact; new and old
cache inodes differ. Core16/bridge2, loaded module metadata and enabled/active
service match; Steam remains absent. The maintainer confirmed Done closes only
the modal and the main window stays normal. No package action, driver/bridge/
service/module/Steam change, restore or cleanup followed. Approval consumed:
keep the window user-controlled; no more authentication/setup/package action,
activation, restoration, backup cleanup, SSH or push without a new request.
This accepts local reviewed Garuda helper bootstrap only, not general clean-
system/Gamescope deployment or public binary approval. Record private receipt
paths outside Git and sanitized results in docs; commit locally. Gyro paused.

## Control Center — controlled helper rollback completed (21 October 2026)

The maintainer explicitly approved the exact prepared rollback, graphical
password and fresh/intermediate read-only gates, then checks only. All review
hashes and before gates matched. Four individual fixed system mv operations
(same-parent, no-copy, no overwrite) succeeded: package policy first, then
executor, license and root0700 cache. All intermediate/held/restore-ready gates
passed; thirteen leaves/three dedicated live directories and loaded package
action are absent, backup bytes/modes/owners/inodes match. Cache contents were
not inspected; its original complete directory inode is preserved. Six legacy
authorization leaves/shared parent remain unchanged. Core16/bridge2, loaded
module metadata and enabled/active service match; Steam package stays absent.
Only these four privileged renames ran, no privileged script or package action.
Approval is consumed. Do NOT restore, clean backups, launch/confirm first-run,
install/update/remove packages or change driver/bridge/service/module/Steam.
Real first-run setup still needs explicit approval. Check future target state
fresh; new/partial setup blocks restoration over originals. Private receipts
and exact backup paths remain ignored; commit sanitized result docs locally,
no push. Gyro calibration stays paused.

## Control Center — first-run rollback review, not execution (21 October 2026)

Latest request authorizes fresh read-only package-helper inspection and a
concrete later approval plan only. The thirteen manually installed helper
leaves match independent pins, root ownership/modes and unowned package status;
three dedicated directories and the six legacy authorization leaves match.
Core alpha3-16/bridge alpha1-2 remain installed, Steam integration absent.
No observed executor/package/auth process or ALPM lock; recheck at execution.
Cache contents are root0700 and were NOT inspected. Preserve its entire inode
and contents through a separately approved same-parent rename, never recursive
deletion or the old empty-directory rollback recipe. Four fixed, nonoverwriting,
no-copy rename steps (policy first) and intermediate passive gates are prepared
privately, with a reverse path requiring all original targets still absent.
New/partial setup blocks restoration; no overwrite, auto-cleanup/retry or
automatic package operation. Legacy helper/shared parent stay intact. Root
would run only fixed system mv, never the private gate script or AppImage.
Offline fixture tests are not actual rollback acceptance. No authentication,
rename, removal, setup, package/service/module/Steam/driver/bridge change, SSH
or push is authorized. The later first-run GUI/password test needs its own
explicit approval. Keep exact host paths/inventories/snapshots in ignored
output; commit sanitized review docs locally. Gyro calibration stays paused.

## Control Center — first-run helper setup offline (21 October 2026)

Latest instruction authorizes implementing/testing first-start helper detection,
setup offer/explicit confirmation, fresh local AppImage build and a concrete
later approval flow. No real target inspection through this new setup path,
sudo/pkexec authentication, helper installation/removal/update, package action,
driver/service/module/Steam change, hardware I/O, SSH or push. Existing helper
and alpha3-16 stay unchanged; Steam integration remains absent after the user's
accepted removal. Use only injected file/session/agent/command boundaries and
same-user temporary fake roots in tests; packaged smoke must ignore real host
payloads and use fixtures. No subagent work is requested.

The first root-code trust step must be explicit: independently reviewed build
pins plus fixed thirteen helper/policy/license payloads, not a self-generated
staging approval. Root runs only allowlisted system sudo/mkdir/install argv,
never a user-owned AppImage/script/interpreter or shell. Seal all immutable
inputs before authentication, create only fixed absent directories exclusively
(no -p), copy exact leaves, policy last. Exact existing helper is reused without
authentication; partial/mismatching/existing unexpected files stop, never
update/overwrite/adopt/repair or auto-remove them. Preserve legacy helpers and
unrelated files. Timeout/failure stops without retry/rollback and reports
possible partial effects; new actions stay locked pending fresh review. Keep
setup separate from package confirmation and activation. Done closes only its
modal, then refreshes passively; no automatic package request. No credentials
stored; initial sudo/KDE askpass availability/prompt policy and separate later
Polkit package agent remain explicit. Local scoped ABI/kernel build and public
runtime/binary provenance limits remain; no general cross-distro claim. Update
docs/manifest and commit locally; gyro calibration remains paused.

## Control Center — user-completed Steam removal and Done accepted

21 October: current agent authorization was fresh read-only preflight and
Steam-only removal-plan display in the new AppImage; no agent confirmation,
authentication or removal. After confirming the visible unsubmitted plan,
the maintainer independently completed the GUI removal and reported
Successfully uninstalled. Passive postchecks confirmed Steam package absence
and all five payload files absent; core alpha3-16/bridge alpha1-2, helper pins,
native module metadata/presence and service enablement were unchanged. The
maintainer also confirmed Done closes only the operation dialog while the
main window stays open. Record this scoped optional-package removal/UI result,
not core removal or remote/Gamescope acceptance. Steam integration is currently
absent. No automatic reinstall, retry, activation, service/module/Steam action,
SSH or push is authorized. Further package work requires a fresh explicit
request/plan. Keep private pre/post records ignored and commit docs locally.
Gyro calibration remains paused.

## Control Center — Steam package install accepted; success-dialog refinement

21 October: the maintainer authorized exactly one AppImage installation of
Steam integration alpha2-1 after fresh passive preflight and desktop permission
window, no removal/driver activation. Exact image/helper/package/selection
checks passed. The user reported a verified GUI success; independent passive
postchecks confirmed alpha2-1, all five root-owned payload files/modes/hashes,
unchanged core alpha3-16/bridge alpha1-2, helper pins, native module metadata/
presence and service enablement. No Steam restart or activation was performed.
That package-operation approval is consumed. No further package test/removal,
retry, driver/service/module/Steam action, SSH or push is authorized.

The user additionally requested clear success feedback and chose closing only
the operation dialog after pressing Done, leaving the main window open. Apply
and test this UI refinement offline. Show install/removal success only for a
verified package receipt; never turn a fixture rehearsal, failure/cancellation
or uncertain result into real success or auto-close it. No automatic closing
or app exit; package hooks remain protected from interruption. Build a fresh
local AppImage if needed, document both the scoped real install result and
offline UI checks, and commit locally. Gyro calibration stays paused.

## Control Center — live read-only package review accepted (21 October 2026)

The maintainer approved opening the exact prepared AppImage with real local
facts and showing the package plan only. Image digest and passive helper/host
checks passed; kernel/headers match. The AppImage was opened normally, and the
maintainer confirmed the visible plan for Steam integration alpha1-1 to
alpha2-1 without final confirmation. No authentication, submission, host ALPM
handle/lock/transaction, install/removal, helper/driver/service/Steam change or
activation occurred. Keep the window under the user's control; do not confirm
it. The review is not a package-operation grant. Recreate expired/stale plans
for any later separately authorized action; no automatic retry, activation,
remote action or push. Gyro calibration remains paused.

## Control Center — AppImage package binding offline (21 October 2026)

Latest instruction authorizes connecting install/removal to the AppImage,
offline regression tests/builds and presenting the real flow for separate
approval. No real host inspection through the new binding, authentication,
package operation, helper update/removal, driver/service/module/Steam change,
hardware action, SSH or push. The previous helper setup is already completed;
its approval is consumed. A deliberately build-selected local package bundle
may enable the reviewed GUI coordinator; generic source/AppImage, demo and
rehearsal keep their distinct boundaries. Bundle only closed data, exact
reviewed package bytes and independently reviewed fixed helper pins. Never
bootstrap privileged code from the AppImage, invent public binary approval or
change the independently installed helper catalog. Inspect/attest in bounded
background jobs, refresh selected planning facts before confirmation and
keep Qt properties side-effect-free. No submission on launch or review,
no stale completion after cancel, no automatic retry/rollback/activation.
Use only fake readers/agents/system edges in GUI/packaged smoke tests. After
possible effects lock new actions; ordinary status refresh cannot unlock them.
Keep private bundle/profile/artifacts and target receipts ignored, update
public docs/manifest, commit locally and present separate install/removal gates.

## Control Center — package helper setup completed (21 October 2026)

The maintainer explicitly approved the concrete local setup prepared from
`f30638e`. Fresh passive gates passed, then the sealed-input ordinary-user
orchestrator installed exactly thirteen reviewed root-owned files and three
new directories using fixed system install commands; the separate package
policy was last. Exact installed hashes/modes and loaded action passed. The
existing authorization-only helper stayed unchanged. No pkexec execution,
permission probe, host ALPM handle/lock/transaction, package hooks, manager,
driver/service/module/Steam change or hardware access occurred. This approval
is consumed. Do not infer permission for a package action, probe, removal,
activation, remote deployment or push. Normal GUI/AppImage stays read-only;
live GUI integration and installation/removal acceptance remain separate.
Keep the local catalog private and source/public defaults empty. Gyro
calibration remains paused. Record further work locally, no push.

## Control Center — local package/helper review (21 October 2026)

Latest scope: inspect concrete local packages, the passive planning reader and
new package helper; prepare exact helper setup/removal commands for approval.
Unprivileged metadata/config/header/service reads and offline package builds
from audited local sources are allowed. No sudo/pkexec prompt, deployment,
manager/device access, host ALPM handle/lock/transaction, driver/service/Steam
change or SSH. Local Garuda preparation only; do not infer CachyOS acceptance.
Catalog data must be independently reviewed, closed schema and fixed protected
installed path; public binary defaults remain empty. Keep payload provenance,
existing-file refusal, sealed stdin handoff, exact target hashes/modes, policy
last, guarded removal and immutable review pins. Do not run prepared scripts
or consume historical installation approvals. Private paths, inventories,
packages/build metadata and deployment scripts stay ignored. Test source
corrections offline, document limits and commit locally; no push.

## Control Center — offline package execution (21 October 2026)

Latest authorization: prepare genuine GUI installation/removal offline, with
tests and a concrete flow for later approval. No deployment, authentication,
host package transaction, hardware I/O or installed driver/service/Steam change.
Read docs/CONTROL_CENTER_PACKAGES.md. Separate package action/helper/schema2
from the installed authorization-only probe; its acknowledgement is never a
transaction grant. Root trust catalogs remain empty until independent binary
review; no invented release records, deployment pins or automatic live CLI.
Keep ordinary GUI/AppImage read-only and alpha3-16 unchanged. Exercise system
edges only with injected doubles; real ALPM tests require a fresh temporary
root/database/cache and only temporary hooks, never host DB/hooks or elevation.
Preserve exact-lock preview/commit/postchecks, existing cleanup hooks and first
errors; uncertain effects lock further actions. No automatic retry, rollback,
activation, dependency fetch, system upgrade or push. Commit completed work
locally and present the separately gated installation/removal sequence.

## Control Center — completed permission-only test (20 October 2026)

The maintainer explicitly approved the reviewed helper/Polkit setup and exactly
one authorization-only probe. Both completed successfully on the local KDE
Wayland session: six pinned root-owned files and three directories installed,
loaded action verified before/after the probe, correlated result
authorized_only/executed:false. No package/driver/service/module/Steam action
ran. The optional helper remains installed; normal GUI actions remain locked.
This is neither real installation acceptance nor permission for another probe,
removal, package operation or push. Gamescope authentication and live
cancellation/removal remain untested. Keep installed alpha3-16 unchanged.

Earlier preparation scope:

Inspect local prerequisites read-only and prepare exact
helper/Polkit setup, probe and removal commands for maintainer approval. Local
service/session/agent metadata and pkaction inspection are allowed, but no
sudo/pkexec authentication, policy/helper installation, driver/system change
or live probe. Keep personal command paths/logs only in ignored build output;
record sanitized readiness in docs. Prepare sealed immutable input handoff:
root install must not reopen mutable user source paths or execute a user-owned
script. Verify exact fresh destination absence, reviewed commit/payload hashes,
installed ownership/modes and registered policy before any future probe.
Removal must retain modified/package-owned/unrelated files. Separate explicit
approval is still required before running any prepared setup/test/removal.

Earlier offline implementation scope:

The maintainer accepted GUI install/removal rehearsal and now authorizes
preparing/testing the real password-window path offline. Source and staged
Polkit policy/fixed helper are allowed; installing them, invoking pkexec or a
real authentication agent, root execution and any package/driver/system action
are not. Keep GUI defaults/read-only and accepted installed alpha3-16 unchanged.
Use test doubles for elevation; any real child in a transport test must be an
explicit harmless same-user fixture. The initial helper is authorization-only:
no package executor, credential/token storage, future authorization grant,
arbitrary commands/paths, shell, device I/O or persistent permission rule.
Keep exact policy/action/helper binding, root-owned non-writable installed
code checks, explicit reviewed pins, strict bounded protocol/output/deadlines
and first-result/cancellation handling. Stage only in a fresh build directory;
self-generated staging checksums are not trusted installation approval.
Document review and deployment gates; commit locally, no push.

Earlier GUI binding scope:

Latest scope: the maintainer accepted real read-only AppImage status on the
local desktop and now authorizes offline GUI/session integration, regression
tests, documentation and a local commit. Keep ordinary read-only mode locked;
the explicit --rehearse-backend mode uses only in-memory fixture packages,
catalog/evidence and RehearsalPort. Never promote Phase-B status into privileged
transaction evidence, fabricate trusted public binaries or bind a live adapter.
Show explicit selection, exact plan, confirmation, bounded background rehearsal
and first-result handling. No real password prompt, root helper, package action,
installation/removal, driver/system/Steam change or push is authorized. Present
the future real flow for separate review; do not perform it. Keep screenshot
and read-only windows independent from the offline test. Read docs/CONTROL_CENTER.md.

Earlier Phase D packaging scope:

The maintainer freezes installed alpha3-16 for multi-day normal-use testing.
Phases A/B, the separate System details dialog and Phase C offline backend
were accepted. Phase D authorizes offline AppDir/AppImage and desktop-integration
staging, tests, documentation and local commits. Never install a menu/desktop/
autostart entry or alter a user profile. Use only local build inputs, no download
or tool installation. Test packaged UI only with demo/synthetic data and private
temporary preferences. Keep build provenance, licenses and platform limits;
local packaging is no public binary-release approval. The GUI stays read-only.
Use synthetic host/privilege/package adapters only; never connect them to the
installed system. No real authorization, download, package action or activation
is part of this phase. Read docs/CONTROL_CENTER.md. No SSH, installation/removal,
sudo prompt, system changes, manager commands, Steam/SDL changes or direct
hardware I/O. Do not reuse
consumed activation/update approvals. The only persisted GUI setting is its own
explicit language preference; external project links open only on user action.
Keep simulated status labelled, receiver presence separate from RF readiness,
and installation separate from module/service activation. Use central DE/EN
catalogs, responsive scroll/focus and disabled future-feature cards. Direct
gamepad I/O, live action transport and real desktop integration await later phases. Keep snapshots
timestamped, refresh bounded and asynchronous, access failures explicit and all
real installation/removal controls disabled. Never infer RF connection from
receiver presence, module/service activity or input-node publication. Read
package/DKMS metadata as data; do not source configuration or run DKMS hooks.
Accepted UI refinement: keep the main view compact. Technical metadata belongs
behind the explicit DE/EN System details button in a separate read-only dialog
for experienced users; no expanded diagnostics panel in the main page. Opening
the dialog reuses the snapshot and must not refresh or change system state.
Reuse reviewed package/removal guards for future integration; no second runtime
policy or Eden-specific installer behavior. No push/release is authorized.

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
