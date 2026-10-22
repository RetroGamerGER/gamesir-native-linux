# Current: PRE-ALPHA.4 distribution and publication — 22 October 2026

Publish the accepted alpha2 GUI with exact sources/licenses, core alpha3-20 and
the separately installed TMR helper alpha1-2 after the authorized checks.
[Publication scope and sequence](CONTROL_CENTER_ALPHA2_RELEASE.md).
Preserve the existing trust anchor, old assets and private development history.
No system/driver activation or new live test; wider TMR platform/loss acceptance,
five-component GUI installation and firmware updates remain separate work.

# Earlier: normal Control Center calibration / alpha2 prepared — 22 October 2026

The accepted TMR GUI path is available in the normal reviewed local build,
with a shorter main page and three-step guidance. Existing package operations
and calibration are mutually excluded through backend guards; simulations stay
isolated. [Integration scope](CONTROL_CENTER_NORMAL_CALIBRATION.md).
No install, system or hardware change, public binary or push in this step.

Later: separately approve distribution of matching TMR-capable driver/helper
packages and the exact alpha2 image/sources. Keep existing signing, source and
license review before publication; never overwrite the historical alpha1 lock
or make first-run setup silently enable calibration. Wider live cancellation,
firmware/platform acceptance and firmware flashing remain separate work.

# Earlier: ZZZ TMR calibration and off/on retention accepted — 22 October 2026

Completed: one selected ZZZ105e calibration using the responsive GUI, both-stick
readiness, explicit Finish and clean maintenance return. Quantitative left-stick
rest measurements show mean X/Y moving from -0.9743%/+1.1025% to 0%/-0.0031%,
with no observed variation after calibration or after controller off/on.
The maintainer confirmed movement after reconnect and reports no remaining
jitter. [Evidence](evidence/TMR_ZZZ_CALIBRATION_20261022.json).

This adds observed ZZZ retention to the earlier normal109c workflow acceptance.
Still open: normal109c retention, numerical right-stick/range quality, other
firmware/platforms, live cancel/loss acceptance and wider GUI distribution.
No extra storage ACK is required; no direct coefficient readback was performed.
Keep the completed run and installation; no automatic retest, update or push.

# Earlier: resolve TMR preview load before calibration — 22 October 2026

**First standard-controller calibration workflow passed:** An explicitly
approved run completed Start, both-stick readiness and Finish. Manager
confirmed clean lease return and continued native input; the maintainer
confirms centers, full travel, normal controls and all paddles in KDE.
[Evidence](evidence/TMR_FIRST_LIVE_CALIBRATION_20261022.json).
Completed: corrected live preview and one standard109c calibration workflow
with independent same-connection functional check. Still open: separately
approved persistence/power-cycle checks, quantitative quality, other
firmware/models/platforms and wider GUI distribution. No new run or firmware
update is implied. Earlier preview preparation follows.

**Deployment completed:** Approved Mainrig installation of core alpha3-20,
helper alpha1-2 and matching GUI is verified. The maintainer confirms no button
flicker or perceived stick lag. Ten-second live preview means were 6.3% CPU
for manager, 5.1% for GUI and 0.9% for helper (one-core basis).
[Evidence](evidence/TMR_DISPLAY_UPDATE_20261022.json).
Next is a separately authorized calibration Go, then explicit Start/Finish and
independent center/range/persistence checks. The GUI remains in preview.
No further update, firmware work or push is authorized by that preview result.
The earlier offline checkpoint follows.

The first real GUI preview exposed flashing Start, delayed positions and high
manager CPU before calibration started. Dialog cancellation removed the
reported load. The [offline correction](TMR_DISPLAY_POLLING_FIX.md) and 16 new
regressions are ready; existing installation remains unchanged.

Next, separately approve a matching manager/helper/GUI update and check only
preview responsiveness/CPU first. Then explicitly approve Start/Finish and
independent stick-center/range checks. No completed calibration or firmware
storage acceptance follows from a functioning preview. Firmware updater and
precision gyro research remain deferred; no installation or publication here.

# Earlier: TMR GUI and permission integration prepared offline — 22 October 2026

**Activation checkpoint (22 October):** The maintainer then authorized temporary
TMR module enablement, paused service start and one Resume after reconnecting
the receiver/controller. Native startup completed successfully (gamepad + IMU,
input publication confirmed). TMR is enabled for this module lifetime only;
no persistent option was written. No calibration helper/session/Start/Finish/Exit
has run. [Activation receipt](evidence/TMR_MAINRIG_ACTIVATION_20261022.json).
Wait for the maintainer's explicit Go before the real calibration GUI/test.
The initial monitor stopped on transient empty USB configuration metadata during
handover; a read-only follow-up confirmed the original bootstrap succeeded.
No second Resume or driver restart was needed. Earlier checkpoints below retain
their own historical scope.

**Deployment checkpoint (22 October):** The maintainer subsequently authorized
installation on the Garuda main system. Local test core alpha3-19 and optional
TMR helper alpha1-1 are installed and verified; module/service remain stopped,
the receiver remains removed and no calibration command ran. Gyro configuration,
Steam/bridge versions and the service's enabled preference are preserved.
[Installation receipt](evidence/TMR_MAINRIG_INSTALL_20261022.json). Activation
and hardware acceptance still need separate approval; no public release/push.

The [scoped GUI/permission path](CONTROL_CENTER_TMR_PERMISSION.md) now connects
the accepted stick dialog to a separate fixed Polkit helper and the native
manager API. One permission session, explicit controller selection, serial
background work, genuine E0 snapshots, one-shot Start/Finish/Exit and local
lease return are covered offline. Ordinary input, gyro, haptics and package
flows remain unchanged. No root GUI or elevated AppImage script is introduced.

The experimental helper explicitly uses the weaker fresh-E0 continuity contract;
it never claims proven RF identity or a lossless stream. Repeated snapshots
cannot refresh liveness. Firmware storage remains firmware-owned; no extra ACK.
The default application and existing first-run helper remain unchanged. Optional
staging prepares eight own helper/policy files and a hash-pinned AppDir companion;
there is no automatic installation or enablement.

43 new pipe/permission/native-manager cases and 12 new real-QML worker cases
pass offline alongside the existing regression. See the linked receipt.
Next: separately approved helper/driver setup and controlled hardware acceptance
of framing, report freshness, display orientation, cancel and explicit Finish.
No installation, activation, hardware, system changes, network or push here.
Precision gyro remains paused and lower RF analysis deferred.

# Earlier: TMR USB format reconstruction — 22 October 2026

The [native USB ingress and full Linux candidate](TMR_USB_FRAMING.md) have been
checked offline against Nexus and six bundled firmware images. Endpoint2,
64-byte receive configuration and unchanged GIP queue copy are now traced.
The exact Windows-provider USB output is still not captured; field confidence
is documented instead of claiming byte-for-byte identity with Windows.

Next: connect the scoped GUI/permission path and prepare a separately approved
controlled calibration run. Keep experimental_tmr off and normal app hardware
calibration unavailable until approval. No extra persistence ACK, host RF CRC
or blind retransmission. Lower RF analysis and precision gyro remain deferred.
Documentation/tests/local commit only; no installation, hardware or push.

# Earlier: TMR native maintenance interface — 22 October 2026

Offline kernel/manager implementation of the [scoped interface](TMR_NATIVE_INTERFACE.md)
now shares native sequencing/output, exact-object identity and exclusive FD
ownership. Full E0 snapshots and one-shot Start/Finish/Exit have regression tests;
normal installation/service does not enable experimental_tmr. No hardware,
installation, activation or push. The complete USB frame is still an unvalidated
candidate and E0 freshness an imperfect continuity guard, not physical RF proof.

Next: separately approved packet/stream acceptance and scoped GUI permission
wiring. Keep the normal app's calibration unavailable until those boundaries
are reviewed; never satisfy its RF capability check by simply trusting USB PID
or a recent snapshot. No firmware-flash work or precision gyro calibration here.

# Earlier: TMR owner/stream adapter prepared offline — 22 October 2026

Implemented the [bounded controller adapter](CONTROL_CENTER_CALIBRATION_ADAPTER.md)
with strict E0 field projection, known provider contents, exclusive per-instance
maintenance contract and stop/cleanup tests. No USB framing guesses, storage ACK
requirement, command replay or live backend. Normal app and accepted preview
remain isolated from real devices. The default backend reports missing API.

Next: separately authorize a narrow kernel/manager command and E0 stream API
that shares native sequencing, ownership, credential checks and RF lifetime
proof. Existing ABI1/IMU getter and management/haptics channels do not provide
that interface. Prepare its packet/stream proof before enabling real hardware;
review change-only telemetry/heartbeat behavior and candidate display mapping.
No kernel/UAPI/manager/helper implementation or live test in this step.
35 new offline cases plus existing GUI/package regressions; local commit only,
no network, hardware, installation or push. Precision gyro remains paused.

# Earlier: offline TMR dialog prepared — 22 October 2026

Implemented the [Control Center calibration preview](CONTROL_CENTER_STICK_CALIBRATION.md)
with two stick plots, independently colored edge coverage and status-based
readiness. Explicit Finish replaces delayed automatic completion; cancel/loss
invalidates the run, and reconnect needs a deliberate new start. Semantic
Start/Finish/Exit are recorded in memory only. No proprietary packets, live
adapter, firmware math or new storage acknowledgement implemented.

The next separate milestone is a reviewed Linux transport/ownership and status
adapter, followed by an explicitly authorized hardware test. This preview's
normalization and heartbeat policy are not validated firmware parameters.
Keep real calibration unavailable in normal status/package launch and the
published AppImage until that integration is tested. Firmware flash work stays
separate; avoid treating speculative calibration bricks as this UI's blocker.
Offline tests, software-rendered DE/EN/compact views and local commit only.
No device access, installation, publication, driver/helper change or push;
precision gyro remains paused and both installed driver states stay intact.

# Earlier: TMR off/wake investigation bounded — 22 October 2026

The [off/wake follow-up](NEXUS_STICK_WAKE_RETENTION.md) resolves the outer RAM
off loop and reset fallback; it is not calibration-command replay. Completed
startup clears the known sequence/calibration RAM. Exact wake/Boot-ROM choice,
physical SRAM retention and actual stale dongle delivery remain unproven.
The stick Finish done-bit guard limits a lone late Finish after fresh startup;
it does not cancel transport data or cover a later ready calibration session.

For the future calibration UI, retain the simple Start/readiness/Finish-or-Exit
contract. Stop the run on loss, do not blindly replay uncertain commands, and
start a fresh run only on user action. No new storage ACK requirement. An
incorrectly saved stick calibration is a plausible recoverable failure to
consider; neither this loss-induced outcome nor a brick has been demonstrated.
No automatic indefinite wake-path investigation is required by this milestone.
Exact physical retention remains a documented research limit for future work.
No writable calibration backend or new hardware test was added.

22 ranges/539 records, independent operand/target checks and 16 dialog tests
passed. Offline documentation/local commit only; no target execution/emulation,
network/hardware, installation, driver/system change or push. Both installations
and deferred diagnosis preserved; precise gyro paused.

# Earlier: TMR reconnect reset routes — 22 October 2026

The [reconnect selection follow-up](NEXUS_STICK_RECONNECT_ROUTES.md) resolves
the deferred joypadtask consumers and separates receiver reset selection,
controller conditional reset, page scan and sleep preparation. Only completed
normal startup has the already established complete clearing of the examined
RAM. A controller reset is not cancellation of dongle pending data.

Next bounded offline work: wake/retention behind controller RAM 0xc7a, distinct
from reset entry RAM 0x10a. Actual selected runtime branches and end-to-end
late-delivery/purge remain unproven. No need to repeat the resolved generic
reset or 0x400008/0x40000b consumer search. Preserve known decoder limits;
exclude DV 0xe976 and do not equate 0x82f0 with calibration helper 0x82f4.

44 bounded ranges/669 records, independently checked transfers/tables,
cached-reference operands, limited write intervals and 16 dialog tests passed.
No automatic replay, automatic loss-triggered Exit, new persistence ACK or
writable calibration backend. Offline docs/local commit only; no firmware
execution/emulation, network/hardware, installation, driver change or push.
Both installations and deferred driver diagnosis preserved; precise gyro paused.

# Earlier: TMR reset lifetime bounded — 22 October 2026

The [soft-reset/startup follow-up](NEXUS_STICK_RESET_LIFETIME.md) resolves the
P33 reset primitive in both RAM suffixes and proves that completed normal
startup clears the reviewed transport/sequence/calibration RAM fields. It does
not establish that every RF reconnect runs this startup or cancels host-side
commands. Controller-only and dongle-only resets must remain separate cases.
No stored-calibration erase, automatic Exit, actual stale Finish or global
exactly-once claim. Passing a sequence filter is not storage execution.

Next offline work: deferred joypadtask 0x400008/0x40000b consumers and actual
reset selection across reconnect. Keep DV 0xe976 operand ambiguity explicit.
Known NOT misdecode and unsupported REP were cross-checked against cached
official Jieli bytes, without modifying the decoder. Do not repeat the now
resolved generic external-reset search or treat a clean decode as proof.
22 ranges/224 records, reference/operand/mutation/bounds checks and 16 dialog
tests passed. No extra persistence ACK or automatic replay in the planned UI.
Research/docs/local commit only; no writable backend, target execution/emulation,
network/hardware, installed changes or push. Deferred driver work stays deferred.

# Earlier: TMR reset paths and deferred actions — 21 October 2026

The [reset-path report](NEXUS_STICK_RESET_PATHS.md) narrows actual internal
HCI-shaped connection/disconnection event handlers. Bounded loss paths reset
connection fields and can stop an output branch without proving cancellation
of its retained command. A separate mode-dependent soft-reset path and
controller task messages prevent a complete RAM-lifetime claim.

Next offline work: resolve DG external 0x20008c/startup initialization, DV
joypadtask 0x400008/0x40000b consumers, and the sequence state across reconnect.
Verify unresolved DV 0xe976 operand/parallel semantics before using that write.
Do not reclassify USB-resume helper 0x53f8 or working-area initialization 0x82f4
as a proven radio-loss Exit. No guaranteed replay/purge, endless radio retry,
or automatic calibration-RAM recovery is established. Same-sequence filtering
remains conditional on sequence retention; sending is not execution/storage.

40 bounded ranges/542 records; 135 anchors; 24 transfer and 4 table checks with
changed controls; 60 memory bounds; 16 dialog tests. Documentation/local commit
only, no writable calibration backend or driver change. Preserve firmware-owned
Finish contract without an extra persistence ACK; no blind reconnect commands.
No target execution/emulation, network, hardware, installation or push.

# Earlier: TMR retry/acknowledgement narrowed — 21 October 2026

The [pending/reconnect report](NEXUS_STICK_RECONNECT.md) separates new-message
queue, retained pending copy and per-cycle send gate. Matching transport
status 0x14 clears the receiver pending flag under the checked header conditions;
the controller filters equal-sequence duplicates but builds another response.
These are conditional static findings, not storage verification or guaranteed
exactly-once delivery across reconnect. Bounded queue flush is not cancellation
of the separate pending copy. Automatic loss-triggered RAM restoration remains
unproven; keep the explicit active-session Exit contract.

Next offline target: writers/indirect reset of D+0x2d0, the retained payload and
B+0x50 across actual loss/reconnect, and the link to calibration flags/restores.
Do not restart the already resolved ACK/duplicate-filter investigation. Preserve
provider/USB/model boundaries and the simple proposed UI. No blind Start,
Finish or Exit replay on reconnect; an uncertain delivery remains uncertain.
No extra persistence ACK requirement or writable implementation in this step.
22 bounded ranges/331 records, 95 anchors, scoped operand/condition/geometry
checks and 16 dialog tests passed. Research/docs/local commit only; no target
execution/emulation, network/hardware, installed changes or push. Both driver
installations unchanged; diagnosis deferred, precise gyro paused.

# Earlier: TMR USB/radio path narrowed — 21 October 2026

The [wire-path report](NEXUS_STICK_WIRE_PATH.md) follows ordinary GIP calibration
through the reviewed DG144 queue/second radio block and DV209's shared
dispatcher. A0/sequence wrapping and matching lengths/check fields are now
located; the first block is a different queue. Cable USB reaches the shared
wrapper separately. Complete provider framing, USB mode selection, lower
delivery and active model/firmware selection remain open.

Next offline work: trace the pending A0 copy's acknowledgement/flush lifetime
across radio loss and reconnect, then the actual loss handler's relation to
active stick calibration/RAM restoration. Do not equate no Finish with an
automatic live-RAM reset or assume the direct Nexus call prohibits transport
retries. Preserve the simple Start/readiness/Finish OR Exit UI contract below;
no extra persistence ACK requirement, automatic retry or writable backend.
23 static ranges/494 records and scoped source/geometry checks; existing 16
dialog tests. No hardware trial, installation, driver change or push.

# Earlier: TMR transport and cancellation boundaries — 21 October 2026

The [transport follow-up](NEXUS_STICK_TRANSPORT.md) closes the untyped D4X
provider step through RTTI, constructor and field evidence. All three commands
use the direct path; signed HRESULT failures are checked at the native boundary.
This is not yet a complete wire-format or dialog-error-handling proof.

Preserve the simple planned UI below. Cancel/disconnect must invalidate pending
Start/Finish and retain one device-instance identity. Normal Exit reaches the
active-session RAM restore; automatic restoration on radio loss remains open.
No Finish means no new save in the reviewed finalizer, not automatic recovery
of already altered working RAM. Do not replay a possibly delivered Finish.
No additional storage ACK or host-side calibration algorithm is imposed.

Next offline targets: provider payload to USB/receiver dispatch, loss handling
of an active calibration and availability of live stick-position reports.
Four restore call candidates were bounded; the two outside Exit have table
conditions. They do not establish a radio-loss path. Sixteen own dialog-model
tests pass, including three new loss cases. No writable Linux backend, target
execution/emulation, hardware/network access, driver changes or push. Both
installed systems preserved; precise gyro calibration remains paused.

# Earlier: firmware-owned TMR calibration and visible guidance — 21 October 2026

Resume offline Nexus research per maintainer request. The primary-host issue
reported after the acceptance below is deferred; firmware as its cause is
unproved. Preserve both installations and the positive secondary-host report.

[Readback/status evidence](NEXUS_STICK_READBACK.md) identifies active/ready
report fields and marker-gated loading of both stick records. Finish requests
firmware-owned storage. Do not require inventing a separate storage ACK merely
to reproduce this contract; distinguish normal workflow completion from an
optional, actually verified readback. Firmware updating retains separate
integrity/recovery requirements.

Control Center target: two live stick-position circles with a blue trace of
the visited rim; each turns fully green only on its firmware-ready indication,
also shown as text. No inferred calibration percentage. Reset the trace per
session. This completes the requested UI scope for now.
Start → firmware completion → Finish; Exit for cancellation.
Visual movement alone must not substitute for the firmware's ready flags.
Bind the session to the device, invalidate pending Finish on cancel/disconnect,
and do not promise rollback after queued storage. First close the existing
transport and model-selection path and verify availability of live stick input
during calibration. No GUI implementation, new commands or hardware trials in
this research step. Keep exact EE53/bus semantics and full persistence-error
visibility as explicit open points, not evidence of a reproduced vendor bug.
Local documentation commit only; no runtime changes or push. Precise gyro paused.

# Earlier: revision18 accepted for current use — 21 October 2026

After the activation below, the maintainer reports both hosts working and
secondary-host Steam Gaming Mode recognizing gyro after later controller
power-on. The working state is accepted as it stands. No additional search,
test or runtime change is requested; preserve both installations. See the
[bounded user report](STEAM_GYRO_HOTPLUG.md). Historical causes remain open,
without an active investigation. Nexus and precision calibration stay paused.

# Earlier: revision18 active; functional acceptance pending — 21 October 2026

[Offline manager correction](MANAGER_RECONNECT_FIX.md): unowned cooldown
expires for fresh discovery; 60 seconds of confirmed healthy active runtime
clears the port's recent charges. Short start loops, true faults and ownership
checks remain guarded. 19 new regressions and 328 related tests pass.

Revision18 is installed and activated on both hosts after separate approval;
see the [installation](evidence/START_BUDGET_INSTALLATION_20261021.json) and
[activation](evidence/START_BUDGET_ACTIVATION_20261021.json) receipts. Both managers
are unpaused. The primary receiver is natively bound in receiver_wait with its
controller off; no secondary receiver was observed at activation. Next: ordinary
use or separately agreed input/reconnect acceptance. No functional test, public
catalog update or push occurred during activation.
The missing X/Y/RT and earlier binding loss need their own evidence; they are
not resolved by budget recovery. Preserve the last observed running state.
Nexus remains saved at50e8c13; precise gyro calibration remains paused.

# Earlier: reconnect budget and partial-input diagnosis — 21 October 2026

Nexus work is saved at local commit50e8c13 and paused; its next questions below
remain intact. Prioritize the maintainer's current reconnect incident.
The primary host is on xpad with a confirmed start-budget block. An offline
in-memory reproduction in revisions16/17 shows the entry remains blocked even
after the ten-minute budget window expires, including after healthy starts.
Separate this policy from true ownership/bootstrap faults before changing it;
do not remove the initialization-loop guard. The missing X/Y/RT and reported
secondary-host failures still need their own evidence. See
[the incident checkpoint](PROJECT_STATE.md).
No installation, runtime change, new input test, SSH, push or calibration.

# Earlier: calibration storage result and readback — 21 October 2026

[Copy/storage follow-up](NEXUS_STICK_STORAGE.md) narrows EE53 to a structurally
supported negative-displacement byte store and traces the write queue through
the registered RAM handler to an internal completion log. Shared normal/rejected
stop flags and submission-based progress prevent treating that log as verified
durable success. This is a static evidence limit, not a reproduced device bug.

Next: find an exact independent EE53 ISA example; establish the bus status
register semantics and actual host success/error route. Determine whether the
calibration path has a readback verification mechanism, distinct from the
separate clean/verify routine. Keep session ownership, queued-buffer lifetime,
atomicity and power-loss recovery open. Do not implement writable maintenance
from the internal finished flag alone. No runtime/system changes, hardware,
network or push; precise gyro calibration remains paused.

# Earlier: firmware calibration persistence boundary — 21 October 2026

[Offline firmware follow-up](NEXUS_STICK_FIRMWARE.md) identifies Start's RAM
backup, Finish's deferred requests and Exit's conditional RAM restoration.
The two 30-byte stick records reach an asynchronous storage worker; they are
also read back by a firmware loading path. This is not a completed hardware
calibration or a guarantee that Exit reverses an already queued write.

Next: corroborate EE53 backup stores independently, close physical completion/
error handling and host transport routing, then design per-device session and
readback checks. Prevent new sessions while persistence is unresolved. Keep
Start/Finish/Exit out of runtime driver/manager/GUI until separately reviewed.
Do not infer destructive effects from the UI Exit→Finish race alone: the serial
firmware path clears its completion preconditions. Broader races remain open.
No hardware/network/installation/driver changes or push; precise gyro paused.

# Earlier: Nexus stick calibration, save and abort — 21 October 2026

The [static dialog follow-up](NEXUS_STICK_CALIBRATION_FLOW.md) now covers all
visible steps and separates automatic Finish from the final window-close button.
G7Pro.Proxy mapping is established. A pending completion survives close in the
observed logic; thirteen own model cases document interruption/identity limits.
No vendor runtime or hardware fault has been reproduced.

Next: follow Start/Finish/Exit into the device firmware and complete transport
framing; establish persistence, readback and rollback before any writable
calibration implementation. A later Linux session must invalidate pending work
on abort, pin the device instance, and distinguish requested/confirmed/saved.
The current research model has no transport and is not a maintenance backend.
Firmware updating remains separately blocked on component-specific recovery.
No installation, hardware, network, driver change or push; gyro calibration paused.

# Earlier: Nexus maintenance research — 21 October 2026

Offline investigation of TMR-stick calibration and separate controller/dongle
firmware updates resumes while the maintainer observes the installed drivers
in ordinary use. [Current findings](NEXUS_MAINTENANCE_RESEARCH.md).

- Stick calibration: UI sequence and device-side start/finish/exit control are
  traced; transport, model routing, persistence and rollback remain before an
  offline state model and any separately approved hardware test.
- Firmware: six REA-inspected functions clarify the default path's flash/CRC
  checks and timeout/result limits. Complete alternate-path/compatibility
  analysis, then file and response validation without a writing transport.
- Recovery for both components must be substantiated before a writable updater.
  No zero-brick promise; CRC, progress100 and a successful normal update are
  insufficient. Existing later-milestone requirements remain in force.

No installation, live maintenance, firmware execution, network or driver change.
These stay optional userspace functions, not kernel/bootstrap operations.
Control Center entries stay planned; precision gyro calibration remains paused.

# Earlier driver follow-up — 21 October 2026

- Revision 17: experimental `105e` ZZZ sensor profile prepared offline, default off;
  [tests and controlled deployment plan](ZZZ_GYRO_EXTENSION.md). Hardware
  acceptance and target-kernel build/installation remain separate.
- Next: investigate long-off binding failure and incomplete ordinary inputs
  after reconnect. User observations only; no claimed root cause or fix yet.
- Preserve published AppImage/signed channel and standard controller functions.
  Precise gyro calibration remains paused.

# Control Center publication checkpoint — 21 October 2026

- Alpha1 AppImage license/source closure completed; reviewed Garuda x86_64
  profile, matching sources/recipes/notices, source lock and packaged checks.
- Publish with the exact signed revision1 and existing PRE-ALPHA.3 assets.
- Next: investigate reported driver faults on both PCs in a separate task.
- Other distro/ABI GUI profiles, broader lifecycle acceptance and a real full
  signed removal/reinstall test remain separate work. Gyro calibration paused.

> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

# GameSir Native Linux: Roadmap

Stand: 21. Oktober 2026. Prioritäten ergänzen den
[aktuellen Projektstand](PROJECT_STATE.md); historische Tests behalten ihren
jeweiligen begrenzten Nachweisumfang. Ein Roadmap-Eintrag ist keine Hardware-,
Installations-, Veröffentlichungs- oder Netzwerkfreigabe.

## Aktuell: alpha3-16 im Alltagstest; lokale GUI-Helfereinrichtung abgenommen

Zusätzlich offline vorbereitet: vollständiger GameSir-Paketabbau und spätere
Neuinstallation über GitHub in getrennten, frisch geprüften Sitzungen. Sechs
neue synthetische Regressionen decken beide Paketumfänge und Fehlerstopps ab.
AppImage/Helfer und Benutzereinstellungen bleiben erhalten. Vor echter
Entfernung zuerst Release-Dateien und Rückweg prüfen; noch keine Live-Aktion.
[Gestufter Testplan](CONTROL_CENTER_GITHUB_PACKAGES.md#later-complete-uninstallreinstall-test--prepared-not-authorized-live).

Neu offline vorbereitet: [geprüfte GitHub-Release-Pakete](CONTROL_CENTER_GITHUB_PACKAGES.md)
statt eingebetteter Archive. Download nur nach ausdrücklicher Komponentenauswahl,
danach vollständige Paket- und frische Systemprüfung vor separatem Installations-
und Passwortschritt. Start/Helfereinrichtung/Entfernung bleiben ohne Download.
Keine echte Netz-/Paketaktion; reale Release-Assets, öffentlicher Build und
separater Downloadtest bleiben Freigabe-/Prüfschritte.
Offline bestätigt: 1.589 Python- und58 Qt-Fälle sowie vier simulierte
AppImage-Testläufe; neuer Downloadpfad mit23 Integrations-/vier GUI-Fällen.

Auch der separat freigegebene zweite AppImage-Start ist lokal abgenommen:
Helfer ohne neue Einrichtung oder Passwortabfrage erkannt. Unabhängige
Nachprüfung bestätigt unveränderte Helferdateien/-verzeichnisse und erhaltene
Sicherungen; Treiber/Bridge/Dienst unverändert. Keine Paketaktion.

Neuester separat freigegebener Live-Schritt: der Helfer-Erststart über das
geprüfte AppImage ist lokal unter Garuda abgenommen. Frische Vorprüfung,
13 Dateien/drei Verzeichnisse, GUI-/Passwortweg, unabhängige Nachprüfung und
„Fertig“ mit offenbleibendem Hauptfenster erfolgreich. Alte Sicherungen und
Cache bleiben intakt, Treiber/Bridge/Dienst unverändert; Steam-Paket bleibt
entfernt. Keine Paketinstallation/-entfernung oder Aktivierung im Anschluss.
Generische Neuinstallation, CachyOS/Gamescope-Erststart und öffentliche
Binärfreigabe bleiben eigene offene Prüfungen. Keine automatische Bereinigung.
[Nachweis und Grenzen](CONTROL_CENTER_FIRST_RUN.md#local-first-run-acceptance).

Frühere Rückbauvorbereitung und -abnahme:

Neuester separat freigegebener Live-Schritt: der kontrollierte Helferrückbau
ist mit vier einzelnen Umbenennungen und allen lesenden Zwischen-/Endprüfungen
abgeschlossen. Sicherungen inklusive ungeöffnetem root0700-Cache bleiben
vollständig erhalten; alter Berechtigungshelfer, Treiber/Bridge/Dienst bleiben
unverändert. Keine Paketaktion, Wiederherstellung oder Erststarteinrichtung.
Als Nächstes ist nur nach eigener Freigabe der echte Erststarttest möglich;
dessen Abnahme ist weiterhin offen. Keine automatische Sicherungsbereinigung.

Neuester lesender Prüfstand: vorhandener Pakethelfer und alter
Berechtigungshelfer passen. Für einen späteren Erststarttest ist ein separat
freizugebender Rückbau vorbereitet: vier feste Umbenennungen erhalten Policy,
Code, Lizenz und den gesamten geschützten Cache; keine rekursive Löschung.
Zwischenprüfungen und gesperrter Rückweg bei neuer/teilweiser Einrichtung sind
mit acht temporären Fixtures geprüft;22 vorhandene Erststarttests bestehen.
Noch kein Rückbau/Passwort-/Erststartlauf und keine Systemänderung.
[Vorbereitung und Grenzen](CONTROL_CENTER_FIRST_RUN.md#controlled-rollback-preparation-for-a-later-first-start-test).

Konkrete lokale Pakete und der neue Helfer sind inzwischen separat geprüft:
bekannter Kernstand16, aus dem öffentlichen Tag gebaute Steam-/Bridge-Kandidaten,
gemeinsame rein lesende Plan-/Root-Fakten und ein geschützter Datenkatalog.
Auf dem lokalen Garuda-Ziel passen Kernel/Header und Bauvoraussetzungen.
Die reine Helfereinrichtung mit13 Dateien/drei Verzeichnissen und geprüftem
Rückbau liegt zur Freigabe bereit; noch keine Einrichtung oder Treiberänderung.
Gamescope/CachyOS ist von dieser lokalen Freigabevorbereitung ausgenommen.
[Nachweise und genaue Grenzen](CONTROL_CENTER_DEPLOYMENT_REVIEW.md).

Der separate echte Paketexecutor ist jetzt offline vorbereitet: eigener
Polkit-Helfer, begrenzte Byteübergabe, unabhängige Root-Prüfung, gleiche
ALPM-Sperre für Vorbereitung/Commit/Nachprüfung und explizite GUI-Anbindung.
Regressionen nutzen Test-Doubles; echte libalpm läuft ausschließlich auf einem
leeren temporären Testsystem mit harmlosen Markerpaketen. Keine Installation
auf dem laufenden System. Der bereits abgenommene reine Berechtigungstest
erteilt dafür keine Paketfreigabe. Freigegebene Binärpakete/Vertrauenskatalog,
Zieldeployment, explizite Planleser-Anbindung und normale Live-Freischaltung sowie die
getrennte Installations-/Deinstallationsabnahme bleiben offen.
[Vorbereiteter Ablauf und Grenzen](CONTROL_CENTER_PACKAGES.md).

Der veröffentlichte PRE-ALPHA.3-Stand und seine Paketvorgabe receiver_wait=1
sind auf beiden Testsystemen separat freigegeben installiert/aktiviert. Der
Nutzer akzeptiert den bisherigen begrenzten Lauf und sammelt nun mehrere Tage
Alltagsfehler. Kein neuer Start-/Funk-/Gyro-Eingriff während dieser Phase.
Die folgenden älteren Startprüfungen bleiben historische Nachweise mit ihren
jeweiligen Grenzen; kein neuer Push-Blocker wird daraus pauschal abgeleitet.

Nach akzeptierten echten lesenden AppImage-Statusdaten folgt nun die Offline-
Verknüpfung von QML und vorhandenen Backend-Sitzungsprüfungen. Explizite Auswahl,
Paketplan, Bestätigung, Hintergrund-Probelauf und Ergebnis sind über reine
Speicherfixtures verbunden und getestet. Die normale Statusansicht bleibt
gesperrt. Reale Paketfreigaben, Polkit/Systemhelfer, geschützte Artefaktübergabe
und Installation/Entfernung auf Zielsystemen bleiben separat zu prüfen; der
[geplante echte Ablauf](CONTROL_CENTER.md#future-real-flow-presented-for-maintainer-approval)
liegt zur späteren Freigabe vor. Kein laufender Treiber wird geändert.

Nach akzeptiertem GUI-Probelauf ist jetzt auch der feste Polkit-/Passwortweg
offline vorbereitet: optionaler Systemhelfer und Policy als Staging-Dateien,
begrenztes Protokoll und Tests mit simulierten Agenten. Der erste Helfer kann
ausschließlich eine Berechtigungsprüfung quittieren; er installiert nichts.
Echter Passworttest, Installation der Policy und der spätere Paketexecutor
bleiben getrennte Freigabe-/Prüfschritte. [Details](CONTROL_CENTER_AUTHORIZATION.md).

Neue Offline-Vorbereitung: [Erststart-Helfereinrichtung](CONTROL_CENTER_FIRST_RUN.md)
mit automatischer Erkennung, ausdrücklicher Bestätigung und Passwortfenster,
festen Systemprogrammen und versiegelten Daten. Passende Helfer unverändert
weiterverwenden; Teilstände sperren, keine automatische Reparatur/Paketaktion.
Echter Erstinstallations-/Passworttest und Gamescope bleiben separat offen;
vorhandenen Helfer nicht ohne eigene Freigabe für einen Test entfernen.

Vorheriger begrenzter Nachweis: Die vom Nutzer abgeschlossene Entfernung nur
der Steam-Integration wurde lesend nachgeprüft; das Paket und fünf Nutzdateien
sind entfernt. Treiber/Bridge blieben unverändert. „Erfolgreich deinstalliert“
und „Fertig“ (nur Dialog schließen, Hauptfenster offen) sind live bestätigt.
Keine automatische Wiederinstallation; Kerneltreiber-Deinstallation bleibt
separat offen.

Vorheriger begrenzter Nachweis: ein echtes AppImage-Update der lokalen
Steam-Integration auf alpha2-1 ist einschließlich unabhängiger Nachkontrolle
bestanden. Kerneltreiber/Bridge blieben unverändert. Kerneltreiberinstallation,
Deinstallation, Erst-Helfereinrichtung und Gamescope bleiben getrennt offen.
Die Erfolgsanzeige mit „Fertig“ schließt nur den Vorgangsdialog und ist offline
getestet; dafür wurde keine weitere Paketaktion ausgeführt.

Historischer Vorbereitungsstand, 21. Oktober: [AppImage-Paketanbindung](CONTROL_CENTER_APPIMAGE_PACKAGES.md)
offline umgesetzt. Ein gezielt geprüfter Build verbindet lokale Paketdaten,
Hintergrund-Vorprüfung und Einmalbestätigung mit dem separat eingerichteten
Helfer. Kein Paketaufruf beim Öffnen; generische Builds bleiben lesend.
Gebündelter synthetischer Installations-/Entfernungstest; echte GUI-Installation
und Deinstallation, Erstinstallation des Helfers aus dem AppImage und
Gamescope-Freigabe bleiben getrennte nächste Schritte.

Historischer Phasenstand:

[Control Center](CONTROL_CENTER.md): Phase A visuell abgenommen. Phase B ergänzt
echte lokale Metadaten für System, Kernel/Header, Pakete/DKMS, Modul, Dienst
und USB-Geräte mit manueller Hintergrundaktualisierung und eindeutigen
Unbekannt-/Zugriffsfehleranzeigen. Funkverbindung bleibt ohne Datenbeleg unbekannt;
keine Manager-Befehle oder Geräteöffnung. Regressionen und eine lokale lesende
Bildprüfung abgeschlossen. Die DE/EN-Demo bleibt getrennt verfügbar; reale
Installation/Entfernung und vier geplante Funktionen bleiben gesperrt.

Phase C, die schmale Installations-/Entfernungsschnittstelle über vorhandene
Paket-Hooks, ist zunächst **offline
vorbereitet**: Artefaktprüfung, versionierter Plan, Einmalbestätigung,
Transaktionssimulation und Nachkontrolle. 45 neue Backend-Prüfungen verwenden
die vorhandenen Paketierer und den echten Rückbaucode mit Test-Doubles.
GUI-Aktionen bleiben gesperrt; kein produktiver Root-/ALPM-Adapter und keine
erfundenen Binär-Releases. Vertrauenswürdige Artefakte, unter ALPM-Sperre
erneut geprüfte Transaktion und reale Berechtigungs-/Rückbauabnahme stehen aus.
Phase D bereitet AppDir/AppImage und Desktop-Payload offline vor: eigene
Python-/Qt-Laufzeit, synthetischer Selbsttest und begrenzte Rückbauvorschau,
keine Menü-/Desktop-/Autostart-Installation. Der lokale Build verlangt glibc
2.44; Portabilität und vollständige Drittanbieter-/Runtime-Quellfreigabe bleiben
offen. [Details](CONTROL_CENTER_APPIMAGE.md). Danach Phase E mit getrennter
KDE/Gamescope- und realer Integrationsabnahme.
Download-Provenienz, passende freigegebene Artefakte und echte Administrator-
aktionen müssen vor Freischaltung geprüft werden. Gamepad-Navigation braucht
eine spätere Gerätefreigabe. Firmware-/Stick-/Software-Update bleiben Coming
soon; keine vorgezogene Hardwareimplementierung und kein Push/Release.

## Vor Push offen: Neustart bei ausgeschaltetem Funkcontroller

Der wartende Kernel-Zustand ist inzwischen **offline implementiert**, bleibt
aber als Option receiver_wait standardmäßig ausgeschaltet. Einmalige begrenzte
Einrichtung, danach passiver Empfang ohne Init-Wiederholung; Client/Manager
unterscheiden wartend von betriebsbereit. Installation und Hardwareabnahme
stehen aus, einschließlich späterem Einschalten und neuer USB-Instanz.
Ein im Suspend abgebrochener unbereiter Wartezustand wird nicht automatisch
neu gestartet. Den laufenden Treiber und die aktive Konfiguration unverändert
lassen. [Stand, Tests und Grenzen](RECEIVER_WAIT_KERNEL.md).

Der Revision-14-Neustart am 20. Oktober lädt Dienst und Modul automatisch.
Bei weiterhin ausgeschaltetem Controller meldet der Manager jedoch einen
blockierten direkten `109c`-Bootstrap (`-110`, VERIFY, kein Pad/IMU) und keinen
bestätigten Rückweg. Native Bindung allein ist keine Betriebsbereitschaft.
Der Schritt zum späteren Einschalten wurde deshalb angehalten; kein Resume,
Release oder neuer Versuch und kein Push. Diesen Start-/Wartezustand getrennt
vom nachrangigen Steam-Anzeige-TODO untersuchen und gezielt abnehmen.
[Nachweis und Grenzen](RELEASE_AUDIT.md#revision-14-controller-off-restart-fails--20-october-2026).

Als nächster Entwurf: schlanken Manager für Übernahme/Verwaltung erhalten;
Empfängerpräsenz, Funkbereitschaft und Laufzeit im Kernel getrennt behandeln.
Kein bloßes Verlängern der IMU-Frist oder Entfernen des Managers. Erst belegen,
welcher GameSir-Verbindungsnachweis vor Initialisierung verfügbar ist oder ob
eine einmalige Empfängerinitialisierung spätere Daten erlaubt. Keine erfundene
Sony-Statusbit-Übernahme oder unbedingte Init-Wiederholung.
[Architekturprüfung und Testanforderungen](DUALSENSE_STARTUP_GAMESCOPE.md#manager-architecture-review-after-the-controller-off-reboot).

Die gespeicherten Mitschnitte liefern inzwischen konkrete Zeitfolgen und zwei
Kandidaten: periodischer Typ-03-Status sowie Typ-02-ANNOUNCE. In vier neuen
nativen USB-Epochen folgt auf Status/Ankündigung erst Pad, dann IMU; meistens
begann Initialisierung aber schon vorher. Noch kein belegter RF-Startauslöser.
Bereits laufende IMU und neue USB-Instanzen beim Funkzyklus separat behandeln.
[Zeitvergleich mit Gegenbeispielen](DUALSENSE_STARTUP_GAMESCOPE.md#saved-capture-connection-chronology--20-october-2026).

Öffentliche Microsoft-GIPUSB-Dokumentation erklärt nun Hello → START → Status;
Typ 03 als Vorbedingung vor START wäre zirkulär. Zwei Hello-Pakete sind anhand
der vollständigen Struktur bestätigt. xones Verbindungsbit passt zu allen 51
positiven Statusberichten, der ausgeschaltete Gegenfall bleibt offen. Als
nächsten Offline-Schritt einen passiven Zustandsprototyp mit Ankündigungs- und
bereits laufendem Datenpfad prüfen; noch keine Hardwarefreigabe daraus.
[Online-Abgleich und Grenzen](DUALSENSE_STARTUP_GAMESCOPE.md#online-gip-sequence-cross-check--20-october-2026).

Der passive Offline-Prototyp ist inzwischen umgesetzt: Wartezustand ohne
Fehlerfrist, höchstens ein Ankündigungs-Startkandidat pro Epoche, separate
Pad-/IMU-Beobachtungen sowie unverlierbarer Erstfehler und terminale Instanzen.
30 neue Tests und 23 gespeicherte Payload-Abgleiche aus fünf historischen
Zeitfolgen bestehen. Nächster Schritt bleibt die Prüfung des Integrationsvertrags
und des fehlenden ausgeschalteten Gegenfalls; noch kein Kernel-/Manager-Fix
oder neuer Hardwareversuch. [Modell und Grenzen](STARTUP_TIMELINE_PROTOTYPE.md).

## Aktueller Spielnachweis und zurückgestellte Steam-Gyroanzeige

Revision 14 ist auf dem CachyOS-Testsystem aktiviert. Normale Eingaben und
Paddles sind bestätigt; Eden erkennt den Gyro über SDL, und in Arc Raiders
steuert Gyro über den angekündigten Steam-Input-Rechter-Stick-Pfad die Kamera.
Die gleichzeitig gemeldete Nullanzeige in Steams Gyromenü wird als separates,
nachrangiges TODO geführt und blockiert diesen bestätigten Spielpfad nicht.
Ursache und weitere Start-/Reconnect-Fälle bleiben offen; keinen reinen
Renderingfehler oder universelle Unterstützung behaupten.
[Anwendungsnachweis und Grenzen](STEAM_GAMESCOPE.md#revision-14-spiel-gyro-bestätigt-nullanzeige-als-todo).

Die folgenden früheren Start-/Anzeigeprüfungen behalten ihren jeweiligen
Zeitpunkt und Nachweisumfang; sie sind keine neue Test- oder Änderungsfreigabe.

## Aktuelle Priorität: eigenständige Übernahme und gemeinsame Regression

Revision 12 ergänzt den eigenständigen Start um Bootstrap ohne Tastendruck und
direkte, instanzgeprüfte Übernahme eines bereits vorhandenen 109c. Beide neuen
Startfälle sind offline geprüft; eine Hardwareabnahme fehlt. Revision 11
entfernte zuvor xpad als Software-Voraussetzung. Freie
unterstützte IF0 werden direkt gebunden; optionale xpad-Vorbesitzer nur am
geprüften Kernelobjekt abgegeben. Keine globale Blacklist und keine neue
USB-Sequenz. [Vertrag, Fehlerpfade und getrennte Abnahme](STANDALONE_STARTUP.md).
Nach abgeschlossener Offline-Prüfung folgen separat freigegebene Installation
und Regression auf Garuda sowie CachyOS. Kaltstart ohne vorherige xpad-Aktivität
ist ein eigener fehlender Nachweis. Paddles, Gyro/Accel, vier Motoren, SDL,
Steam und Eden gemeinsam erhalten; Forza-Bridge bleibt Userspace.
Die spätere GUI mit DE/EN, Deadband-Link und klar bezeichneten geplanten
Funktionen folgt erst nach dieser Integration. Kein GUI-Code in diesem Schritt.

## Weiterhin offen: Gyro bei spätem Einschalten / Wiederverbinden in Gamescope

Offline-Reproduktion und zweistufiger Kernel-/Client-/Manager-Pfad sind jetzt
implementiert. Der bestehende Sensorvertrag, Roh-IIO, Paddles und Haptik bleiben
erhalten; verarbeitete Sensorbenachrichtigung, Sitzungszugriff und exakte Instanz
gehen der Gamepad-Veröffentlichung voraus. Modulbauten für die vorhandenen
Garuda- und CachyOS-7.2.11-Kernel sind bestanden. Vor später Installation
Kernel-/Header-/Modulstand und Zustand erneut prüfen; echte späte Einschalt-/
Reconnect-Abnahme unter Gamescope steht aus. Keine Steam-Neustarts, globale Wartezeit oder Bibliotheksersetzung.
[Implementierung, Nachweise und Grenzen](STEAM_GYRO_HOTPLUG.md).

Der separat freigegebene Revision-10-Realtest ist nach Installation und
bestätigter nativer Veröffentlichung negativ: Steam öffnet inzwischen beide
gepaarten Knoten, die drei Gyro-Anzeigen bleiben laut Nutzer null. Normale
Eingaben und Paddles funktionieren. Keine weitere Wiederverbindung testen,
bevor die Lücke hinter dem offenen Sensorknoten gezielt offline eingegrenzt ist;
keine Steam-/Treiberänderung daraus automatisch ableiten.
[Negativer Anwendungsnachweis](STEAM_GYRO_HOTPLUG.md#subsequent-controlled-late-arrival-run-steam-gyro-still-zero).

Neuere Nutzerpräzisierung: Bei gehaltener Guide-Taste funktioniert die
Gyro-Anzeige. Die verbleibende Guide-Abhängigkeit in Ereignisverarbeitung,
Benachrichtigung oder Anzeige offline abgrenzen; reinen Darstellungsfehler nicht
als bewiesen ausgeben. Kein Guide-Keepalive oder neuer Liveversuch daraus.
[Guide-Nachtrag](STEAM_GYRO_HOTPLUG.md#human-follow-up-display-works-while-guide-is-held).

Die [gezielte Offline-Untersuchung](STEAM_GUIDE_GYRO.md) grenzt nun den
Sensor-Ausgabeadapter und SDL mit Guide-Halte-/Loslasssequenzen ab. Nächste
Beweisgrenze ist Steams ausgewählter Bewegungskontext, Quellgültigkeit und
Benachrichtigung gegenüber frischen unteren Sensordaten. Die statisch
nachgewiesene Guide-Verarbeitung allein beweist diese Verbindung nicht.
Ohne eine separat freigegebene, instanzgleiche Beobachtung keine sichere
Ursachenzuweisung oder weitere Laufzeitkorrektur. Kein Guide-Keepalive.

Der nächste reine Metadatencheck scheiterte bereits an Fish vor sudo/Prüfung;
keine Wiederholung. Nutzer meldet jetzt auch mit Guide null und manuellen
Resume. Die SSH-Übergabe ist offline mit echten lokalen Shells korrigiert und
getestet. Zuerst separat freigegeben effektive Moduloptionen, Dienst/Instanz,
Steams offene Knoten und Versionen prüfen; daraus erst den nächsten gezielten
Beobachtungsschritt ableiten. Noch kein neuer SSH-/Hardwarezugriff.
[Transportkorrektur](STEAM_GUIDE_GYRO.md#metadata-precheck-stopped-before-authentication).

Nach vollständigem Nutzer-Neustart automatische Bindung ohne Resume gemeldet,
Guide-Abhängigkeit erneut vorhanden. Der separat genehmigte zweite Leseschritt
bestätigt Dienst aktiv/laufend/aktiviert, scheitert dann an der Gamescope-Suche.
Die Prozesszuordnung ist offline auf ausführbare Datei, tatsächliche UIDs und
stabile Instanz korrigiert; 160 Integrationstests bestanden. Nächster Schritt
bleibt der separat freizugebende reine Metadatencheck, keine neue Bewegungs-
oder Speicherbeobachtung. Genauere Diagnose erst mit dessen Ergebnis.
[Prüfhelferkorrektur und Grenzen](STEAM_GUIDE_GYRO.md#gamescope-process-identity-corrected-offline).

## Bazzite als mögliche Zielplattform

Quellenvergleich abgeschlossen, noch kein Bazzite-Zielbau oder installierbares
Angebot. Gemeinsamen Treiber erhalten; Fedora-RPM-/akmods-Pfad, Kernel-/Image-
Updatekopplung und eigenen Session-Adapter vorbereiten, sofern separat beauftragt.
OpenGamepadUI/InputPlumber, Secure Boot/SELinux und Managerzustand beim Rollback
berücksichtigen. Kein CachyOS-Unit-Drop-in blind übernehmen, kein Desktop-/Gyro-
Stabilitätsversprechen aus dem Distributionswechsel. Vor einer zugesagten
funktionsgleichen Ablösung Zielimage bauen und Kernfunktionen/Update/Rückweg
abnehmen. [Machbarkeit und Entscheidung](STEAM_GAMESCOPE.md#bazzite-machbarkeitsprüfung-und-migrationsgrenze).

## Abgeschlossener Meilenstein: SDL / Eden

Der Nutzer nimmt den aktuellen Gyro-Funktionsumfang als abgeschlossen an.
Eine eigene Steam-Gyro-Integration war zunächst zurückgestellt; die danach
angeforderte Offline-Machbarkeitsprüfung ist unten getrennt aufgeführt.
Bestehende Steam-Paddles bleiben unverändert. Zusätzliche Messungen und die unten
verbliebenen Abnahmefälle werden nicht automatisch begonnen.

Die bevorzugte Gyroeinstellung bleibt bei 0,07 °/s; keine neue Faktorsuche.
Der optionale evdev-Gyropfad ist lokal installiert und in Edens
Controller-Einstellungen angenommen: Bewegung über SDL, passende Richtung/
Empfindlichkeit und vier unabhängig belegbare Paddles bei normalen Eingaben.
Die dauerhafte lokale Gyro-Moduloption wurde separat freigegeben, angelegt
und lesend geprüft; ohne Dienst-/Modulneustart oder neue Geräteaktion.
Offen bleiben die tatsächliche Abnahme nach einem nutzergeführten PC-Neustart
und die Abnahme in einem konkreten Spiel.
Eden-Hotplug und Wechsel der Zeitbasis bleiben separat zu lösen;
keine universelle Spielefreigabe oder erfundene Beschleunigungsachsen.
[Test, korrigierter Prüfhelfer und Grenzen](SDL_EDEN_GYRO.md).

## Steam-Gyro-Korrektur: optionaler Beschleunigungspfad

Die separat freigegebene Revision 9 ist installiert und mit temporärem
realem Beschleunigungsprofil nativ gestartet. Steam zeigt jetzt alle drei
Gyro-Achsen an; normale Eingaben und unabhängige Paddles wurden bestätigt.
Das löst die Nullanzeige dieses Laufs. Die anschließend separat freigegebene
lokale Accel-Konfiguration ist dauerhaft gespeichert und lesend verifiziert;
laufendes Modul und Dienst blieben unverändert. Nächste Schritte unter eigener
Freigabe: tatsächliche Boot-/Lebenszyklusabnahme. Der
Nutzer bestätigt inzwischen die weitere Funktion von Eden; zusätzliche
Einzelmessungen wurden dazu nicht dokumentiert. Keine neue Winkel-/Gyrofaktorsuche und kein
universelles Proton-Spieleversprechen. [Resultat und Grenzen](STEAM_ACCEL_EXTENSION.md).
Das CachyOS-/Gamescope-Testsystem ist danach separat auf dasselbe Revision-9-
Kernpaket samt lokalem Sensorprofil aktualisiert und geprüft. Es bleibt nach
bestätigter Rückgabe pausiert, Dienst inaktiv/aktiviert und Modul entladen.
Nächste dortige Grenze: eigens freigegebene Aktivierung und Sensor-/UI-Abnahme;
die erfolgreiche Installation ist kein Live-Nachweis.
Die anschließende separate Aktivierung bestätigte inzwischen nativen Bootstrap
und gepaarten, für die Gamescope-Sitzung lesbaren Sechsachsen-Sensor. Dienst
aktiv/aktiviert, Manager unpausiert. Normale Eingaben/Paddles sind bestätigt;
Steams Gyro-Anzeige bleibt null. Die lesende FD-Prüfung sieht nur das Gamepad
im Steam-Hauptprozess geöffnet. Nächster vorgeschlagener Test: regulärer
nutzergeführter Neustart und frische Sensor-/Steam-Prüfung. Ursache und
Boot-/Lebenszyklusabnahme bleiben offen; keine erneute Kalibrierung beginnen.
Der anschließende nutzergeführte Neustart bestätigt einen automatischen
Dienst-/Bootstrap-Fall samt lesbarem Sensor. Steams Hauptprozess öffnet den
Sensor auch mit geöffneter Gyro-Anzeige weiterhin nicht; Werte bleiben null.
Neustart allein löste diesen Steam-Fall nicht. Ursache gezielt weiter
eingrenzen; keine allgemeine Boot- oder Steam-Gyro-Abnahme daraus ableiten.
Der folgende KDE-Test auf demselben CachyOS-PC ist positiv; lesend bestätigt
Steam dort den geöffneten Sensor bei gleichem Boot, Profil und Gerätepaar.
In Gamescope startete Steam vor dem nativen Controller, außerdem nutzt der
Vendor-Launcher Steam-Deck-Optionen. Zuerst Startreihenfolge gegen Startmodus
abgrenzen: normaler Steam-Neustart in Gamescope bei bereits vorhandenem Sensor
nur nach eigener Freigabe. Kein neuer Treiberpatch oder künstlicher Boot-Delay
auf Verdacht. [Sitzungsvergleich](STEAM_ACCEL_EXTENSION.md#same-host-kde-and-gamescope-comparison).
Nach nutzergeführtem Update/Neustart mit CachyOS-Kernel 7.2.11 ist nun auch
Gamescope-Steam-Gyro positiv gemeldet; Steam öffnet den Sensor bei unverändertem
Revision-9-Profil und weiterhin vorhandenen Vendor-Optionen. Der Nutzer nennt
den vor Steam eingeschalteten Controller. Das ist kein isolierter Ursachenbeweis
für Kernel oder Startreihenfolge. Nächste offene Zuverlässigkeitsfrage: spätes
Einschalten bei laufendem Steam und Wiederverbindung, getrennt freizugeben.
Die folgende Nutzerrückmeldung zum Wiederverbindungscheck nennt als Gyro-
Voraussetzung einen beim Laden von SteamOS bereits eingeschalteten Controller.
Diese Einschränkung gezielt lösen; keine uneingeschränkte Wiederverbindungs-
Abnahme oder bloße Verzögerung des Steamstarts als fertige Lösung behaupten.
[Aktueller Erfolg](STEAM_ACCEL_EXTENSION.md#gamescope-success-after-user-led-kernel-update-and-reboot).
Die folgende Machbarkeitsnotiz beschreibt den früheren Zwischenstand.

## Neu angefragte Steam-Gyro-Machbarkeit: offline geprüft

Beide vorhandenen Steam-SDL3-Varianten akzeptieren den bestehenden
Gyro-only-evdev-Pfad samt Paddles im gerätefreien Test. Noch offen: Steams
tatsächliche Backendauswahl, Gyro-Fähigkeitsbit, Verhalten ohne Accel und
Anwendung im Proton-Spiel. Zuerst unter eigener Freigabe vorhandene
Erkennung prüfen; keine zweite Sensorausgabe oder Treiberneuentwicklung.
Gyro-zu-Maus/Stick ist der bevorzugte Kompatibilitätspfad; natives
Steam-Input-Motion und proprietäre Spielepfade haben eigene Grenzen.

Alle Komponenten müssen zusammengeführt und gemeinsam abgenommen werden:
SDL/Eden, Steam/Paddles, normale Eingaben, Griff-FF, Trigger-Bridge und IIO
erhalten; gemeinsame Geräteidentität, eindeutige Ausgabezuständigkeit und
STOP-/Reconnect-/Suspend-Regeln. Die bestandenen Einzeltests ersetzen keine
Abnahme ihres Zusammenspiels. Details und Abnahmematrix:
[Steam-Gyro-Prüfung](STEAM_GYRO_FEASIBILITY.md). Noch keine Steam-Änderung,
Installation, Hardware-/Spielprüfung oder neue Kalibrierung freigegeben.

## 1. Stabile Alpha und Release-Abnahme

Lokal installiert: Manager-Reconnect-Korrektur in Paketrevision 6,
unverändertes Kernelmodul/ABI. Nach bestandenen Offline-Regressionen wurde das
ausdrücklich freigegebene Update installiert und lesend geprüft. Danach wurde
der Dienst vom Benutzer gestartet; ein erfolgreicher nativer Bootstrap ist
inzwischen beobachtet. Kontrollierte reale Wiederverbindung weiterhin
getrennt freigeben und abnehmen. Der freigegebene integrierte Forza-/Xodus-Test
nutzt zunächst die bestehende Verbindung und ersetzt diese Reconnect-Abnahme
nicht. Alter Fehlerzustand
wird nicht automatisch entsperrt. [Korrektur und Rückweg](MANAGER_RECONNECT_FIX.md).

Öffentliche Fassung ausdrücklich als **PRE-ALPHA** vorbereiten. Vollständigen
Warntext, Project Goals, unabhängige Referenzwürdigung sowie belegte
Funktions-/Plattformgrenzen in der README erhalten. Portable Installation,
Prüfung, Fehler-Rückweg und vollständige Entfernung stehen getrennt von den
historischen Laborberichten. [Release-Audit](RELEASE_AUDIT.md) trennt bestandene
Vorbereitungsprüfungen von offenen Artefakt-/Publikations- und Hardwareabnahmen.
Das ist keine neue Hardware-, Installations- oder Push-Freigabe.

Lizenzgrundlage für die Pre-Alpha: eigener Bestand GPL-2.0-only, vollständige
`COPYING` und UAPI-Ausnahme auch im DKMS-Paket, geprüfte Herkunft und klare
Grenze zu g7ctl/Herstellerreferenzen. Für spätere Kernel-Einreichung Herkunft,
Standard-Schnittstellen, Maintainerreview und wahrheitsgemäßen DCO nachweisen;
die Lizenz allein bewirkt keine Mainline-Aufnahme. [Lizenzbericht](LICENSING.md).

Den bestätigten autonomen CachyOS-/Gamescope-Betrieb, vier unabhängigen
Paddles, normale Eingaben, IMU-Rohdaten und Viermotor-Runtime erhalten.
[tester] testet Ship of Harkinian in Ruhe; währenddessen keine Treiber-/
Systemänderungen. Ein Boot-E2E-Fall ist bestätigt, keine allgemeine
Boot-/Suspend-/Hotplug- oder Langzeitzuverlässigkeit daraus ableiten.

Weitere Bootkonstellationen, Wiederverbindungen, Suspend, konkurrierende
Anwendungen, Kernel-/Steam-Updates und gegebenenfalls mehrere Dongles
getrennt planen, ausdrücklich freigeben und mit geprüftem Rückweg testen.
Garuda test host erst nach gesonderter Updatefreigabe angleichen. Release und Push
bleiben bis zur ausdrücklichen Entscheidung gesperrt.
Belege: [Gamescope](STEAM_GAMESCOPE.md),
[Bootstrap-Korrektur](BOOTSTRAP_CACHYOS_FIX.md).

## 2. Spielintegration und kalibrierte Sensoren

**Qualitative Achsen ins Offline-Testprofil übernommen:** Das explizite
`g7pro-observed-20261018` bewahrt Rohdaten und getrennte Skalierungswahl;
Replay aller sechs gespeicherten Richtungen bestanden. Das lokale
[Diagnosefenster](GYRO_VIEWER.md) mit Fadenkreuz, relativer Drehungsanzeige
und getrenntem Darstellungsfaktor ist jetzt im reinen Offline-Replay geprüft.
Nächster Schritt: den begrenzten lokalen Transport vom vorhandenen kohärenten
IIO-Worker zur GUI offline vorbereiten und prüfen, dann einen E2E-Anzeigelauf
separat freigeben. Kein neuer Treiber nötig für diesen Diagnosepfad. Eine spätere
SDL-/Eden-Abnahme benötigt weiterhin die zusätzliche Sensorschnittstelle
und passende Kalibrierungsbelege. [Plan und Grenzen](EXPERIMENTAL_GYRO_TEST.md#visueller-e2e-empfindlichkeitstest-geplanter-nächster-schritt).

**Architekturvereinfachung offline bewerten:** Den
[xpad-/HID-Vergleich mit PandaPro8K](XPAD_HID_FEASIBILITY.md) weiterverfolgen.
Gespeicherte normale `100a`-Deskriptoren und einzelne IF1-Telemetriepakete
stützen einen möglichen Zusatzpfad bei erhaltenem XInput. Zuerst den
behaupteten Linux-Patch und die modellspezifische Aktivierung prüfen;
keine dauerhafte Ausgabe von Paddles/IMU oder vier Motoren daraus ableiten.
Ein gemeinsames Input-Gerät und koordinierte Motorstopps müssen beim
Entwurf erhalten bleiben. Kein Austausch der funktionierenden Runtime,
kein neuer USB-Befehl oder Hardwaretest aus diesem Analyseauftrag.

Der [separate Dateiprototyp](XPAD_HID_PROTOTYPE.md) ist inzwischen umgesetzt:
acht vorhandene Mitschnitte, 14 strukturell passende IF1-Berichte in drei kurzen
Rückkehr-Bursts, aber kein belegter Aktivierungsbefehl. Keyboard-LED-Ausgabe
`03 01`, framed IF0-Heartbeat und Pandas `0f f2` bleiben getrennt. Nächste
offene Hürde ist ein belastbarer normaler G7-Pro-IF1-Aktivierungsvertrag;
danach separat freigegebene Dauerstrom-/Paddle-/Release-/Reconnect-Nachweise.
Keine laufende Architektur ersetzen, bevor Input-Zusammenführung und alle
vier Motoren samt Besitz/Stopps gleichwertig gelöst sind. Kalibrierung pausiert.

Die [passiven 90-/300-Sekunden-Adapter](HID_PASSIVE_CAPTURE.md) sind separat
offline vorbereitet. Der spätere, eigens freigegebene Rückweg bestätigte eine
saubere `100a`-Ausgangsinstanz; der erste Aufnahmeversuch brach vor Modulladen
an der Prozesszugriffsprüfung ab. Die lesende Diagnose vom 18. Oktober konnte
diesen Fehler nicht reproduzieren. Genaue künftige Fehlerdiagnostik ist ergänzt;
Zugriffsfehler werden nicht ignoriert. Zwei später separat freigegebene
90-Sekunden-Läufe sind abgeschlossen. Erst der zweite mit geprüft offenem
Eingabeclient zeigte normale XInput-Berichte; IF1 lieferte nur kurze andere
HID-Berichte. Kein beobachteter Vendor-IMU-Strom oder Einzeltasten-Nachweis.
[Auswertung und Grenzen](HID_PASSIVE_CAPTURE_RESULTS.md).
Nächster Schritt ist gezielte Offline-Arbeit am belegbaren Aktivierungsvertrag,
ohne das 8K-Protokoll auf Verdacht zu senden oder den nativen Treiber zu ersetzen.
Manager pausiert/ohne Besitz, vollständige Zugriffsprüfung, usbmon-Verfügbarkeit
und frische Hash-/Instanzmetadaten bleiben Voraussetzungen. Offline-Tests ersetzen
keine Aufnahmefreigabe; Aktivierungsbefehle bleiben unbestätigt/gesperrt.

**Trigger-Bridge:** Der geprüfte eigenständige Forza-/Xodus-Nachweis wird als
optionale Userspace-Komponente integriert, nicht in den Kernel verschoben.
Die neue Fassung ergänzt eindeutige Instanz-/Quellzuordnung, versionierten
Transport, Frischeprüfung, Stopbarrieren und Geräteersatz-Abbruch sowie einen
getrennten Paketquellhelfer. Offline-Regressionen und die separat freigegebene
lokale Installation sind abgeschlossen. Xodus-Startzusatz vorbereitet;
effektive Benutzerberechtigung und native Brokerzuordnung geprüft.
Der erste integrierte Forza-Test zeigte keine Trigger-Vibration. Nach
Offline-Korrektur und gesondert freigegebenem Update/Lauf hat Revision 2
beide Trigger samt Pausen/Neustart und ruhigem regulärem Spielende bestätigt;
normale Eingaben und Griff-Rumble blieben erhalten. Die genaue Live-Ursache
des ersten Fehlversuchs bleibt unbekannt. Bestehende Eingaben,
Paddles, Griff-FF und Roh-IMU erhalten. [Umfang](TRIGGER_BRIDGE.md).

Nächste getrennte Schritte: weitere Xodus-Lifecycle-Fälle und den
Steam-/Proton-Ausgabepfad/ABI/Container prüfen. Unterstützte
Launcher-Hooks für automatische Nutzung entwickeln; keine globale Preload-
Umgebung oder unkontrollierten Konfigurationsänderungen. Fehlende getrennte
Spiel-Triggerbefehle nicht aus Achsen/Griff-Rumble erfinden. Reconnect, PM und
mehrere Geräte gesondert belegen. Forza-RT3x nicht global übernehmen.

Die [Offline-Machbarkeit für Steam/Proton](STEAM_PROTON_TRIGGER_BRIDGE.md)
ist inzwischen untersucht: SDL2-Einstieg in Proton vorhanden, aber aktuelle
Startvalidierung, Container-Pfade/Peer-PID und virtuelle Steam-Input-Geräte
verhindern eine pauschale Freischaltung. Als Nächstes einen separaten
geschlossenen Adapter mit Fake-Runtime/IPC-Tests entwickeln. Danach eine
ausdrücklich freigegebene technische Proton-Probe mit eigenem API-Test und
Fake-Ausgabe durchführen; dafür ist kein Trigger-Spiel erforderlich. Ein
solches Spiel steht derzeit nicht bereit, reale Spieleabnahme bleibt offen.
Paddles, Griffe und normale Eingaben erhalten; keine neuen Kernel-Patches.

**Referenzkalibrierung pausiert:** [tester] hat derzeit keinen geeigneten
Anschlagwinkel. Die vorbereitete IIO-Puffertransaktion und der einzelne
KDE-geführte 90°-Linkslauf bleiben als offline geprüfter Zwischenstand
erhalten. Erst nach neuem Auftrag, externer Winkelreferenz und frischer
Geräte-/Befehlsfreigabe weiterarbeiten. Keine automatische Wiederaufnahme;
der produktive Treiber und die bisherige SDL-Grenze bleiben bestehen.

**Eigenes Gyrofenster:** Offline-Replay ist vorhanden. Die zusätzliche
Live-Vorschau ist jetzt offline implementiert und geprüft: vorhandener
IIO-Worker, lokales Go, fünf explizite Testprofile, Fadenkreuz-Gain und
Zentrierung. Auf Nutzerwunsch kein festes Laufzeitlimit; STOP/Fenster schließen
oder ein Sicherheitsfehler beendet die Sitzung mit Rückstellungsprüfung.
Eine separat freigegebene Live-Abnahme am 18. Oktober verarbeitete 11.466
Werte und endete auf Nutzerwunsch mit bestätigter Rückstellung und normaler
Gamepad-Funktion. Der Nutzer behält 0,07 °/s pro Rohwert bei 1,00× als
bevorzugte Einstellung: natürliches, zur realen Bewegung passendes Gefühl.
Keine weitere Faktorsuche angefordert. Drift ist noch nicht quantifiziert;
physikalische Referenzkalibrierung bleibt pausiert, SDL-/Eden-Integration
eine separate offene Aufgabe. Neue Live-Aktionen benötigen eigene Freigabe.
[Ergebnis und Grenzen](GYRO_VIEWER.md#erster-live-test--18-oktober-2026).
[Bedienung und Freigabeplan](GYRO_VIEWER.md#live-test-zur-freigabe-vorbereitet).

Davon getrennt ist jetzt der [qualitative Achsentest](GYRO_AXIS_TEST.md)
offline vorbereitet: zunächst nur bequeme Linksdrehungen ohne Winkelvorgabe,
jede Wiederholung nach eigenem Go. Rohkanal und Vorzeichen untersuchen,
keinen Faktor kalibrieren. Live-Ausführung und Host-Pufferänderung bleiben
separat freizugeben; der vorhandene 90°-Referenzablauf bleibt pausiert.

**Funkanalyse zurückgestellt (18. Oktober):** Die bereits nachgewiesene
IMU-Ausgabe genügt als Ausgangspunkt für eine spätere Referenzkalibrierung;
eine vollständige Rekonstruktion der unteren Funkverarbeitung ist dafür
nicht erforderlich. **0,07 °/s pro USB-Rohwert bleibt ein unbestätigter
Testkandidat**, ohne Profilaktivierung oder Treiberänderung.
[Herkunft und Prüfgrenzen](PROTOCOL.md#unbestätigter-gyro-testkandidat).
Kalibrierung und Funkanalyse werden nicht automatisch wieder aufgenommen.

Der separate [experimentelle Gyrodiagnosepfad](EXPERIMENTAL_GYRO_TEST.md)
bereitet fünf LSM6DS3TR-C-Hypothesen vor; kein Messbereich wird automatisch
ausgewählt. Gespeicherte IMU-Pakete sind unter allen fünf Faktoren vergleichbar,
ohne daraus eine bestätigte Kalibrierung zu machen. Die
[kohärente Standard-IIO-Pufferquelle](COHERENT_IMU_CALIBRATION.md) ist nun
offline implementiert: sechs Werte desselben Berichts, Host-Monotonzeit,
Annahmezähler, Pushfehler und PM-Gate. IIO-Einzelattribute genügen weiterhin
nur für die Live-Anzeige. Nächster Schritt ist nach gesonderter Freigabe
der Abgleich dieses neuen Pufferpfads auf Hardware, noch keine SDL-Freigabe.
Der private Control-Snapshot ist wegen Besitz-/STOP-Semantik keine harmlose
Abkürzung. Erst nach gesonderter Freigabe bekannte Drehwinkel mit Puffern,
Wiederholungen und sechs Ruhelagen messen. [tester]' Reihenfolge: erst eine
eigene Sitzung mit drei einzelnen 90° links, dann getrennt rechts, vorne,
hinten; Bereitschaft vor jeder Wiederholung, Rücksetzen außerhalb Integration.
180° und Rollen erst später separat. Danach Bias/Achsen/Faktor prüfen,
evdev-Sensorgerät ergänzen und lokalen SDL3-Tester vor Eden verwenden.
Weder heutige Implementierung noch Plan erlauben Hardware-/Systemänderungen.
Der inzwischen separat freigegebene 90-s-KDE-/IIO-Anzeigelauf ist bestanden:
alle drei Gyro-Rohkanäle reagieren. Der nächste Schritt bleibt die kohärente
passive Referenzmessung, keine Auswahl des realen Faktors aus diesem Anzeigetest.

- Unabhängige Paddle-Quellen erhalten; direkte Spielbelegung von Steam-
  Übersetzung und den Grenzen der jeweiligen Spiel-API unterscheiden.
- Spiele-FF_RUMBLE und die versionierte Viermotor-Schnittstelle erhalten;
  Trigger-Anwendungsadapter gezielt integrieren. Keine zusätzliche Kernel-UAPI
  oder universelle Steam-/Proton-Triggerunterstützung behaupten.
- IIO-Rohdaten weiter anbieten. Eigenständigen Gyrofaktor, Bias,
  physische Achsen/Vorzeichen, Zeitbasis und Accel-Kalibrierung belegen.
  8192 LSB/g bleibt austauschbarer experimenteller Wert. Danach zusätzliche
  kalibrierte evdev-Sensoren mit nachvollziehbarer SDL-Gamepad-Zuordnung prüfen.

Neuer externer Identifikationsbeleg am 16. Oktober: [tester] bestätigt die
DigiKey-Zuordnung LSM6DSO/LSM6DSOTR zu seinem Controllerfoto. [tester] stellt
inzwischen die exakte Variante infrage; Fotoauskunft erhalten, tatsächliches
Modell wieder offen. Keine erwiesene Korrektur auf TR-C. Originalfoto,
QR-Inhalt und Vendorantwort sind hier noch nicht lokal geprüft. Die fünf
berichteten Gyro-Sensitivitäten sind mögliche Referenzen, keine Auswahl.
Die lokale Linux-ST-Referenz bestätigt inzwischen 0x11/0x0c und vier
Gyrogewinne, nicht den aktiven GameSir-Messbereich oder die ±125-Kodierung.
Die innere Appstruktur ist nun über 288 Header-, 48 Bereichs- und 96
Datei-CRC aufgelöst; `app.bin`/`cfg_tool.bin` sind prüfsummengültig lesbar.
Drei MCU-Teilformate sind nun empirisch geprüft, aber Kompaktoperanden,
Speicher-/Vergleichsbefehle und ABI fehlen. Diese gezielt vervollständigen,
WHO_AM_I 0f mit Referenz 6a(TR-C)/6c(DSO) zum ID-/Sensorwahl-/Init-Pfad
verfolgen, dann letzte wirksame CTRL2_G-Einstellung und Sensorregister→USB-
Skalierung belegen. Kompilierte LSM6DS3TR-/QMI8658-Meldungen sind keine
neue Bestückungsfeststellung. Keine erneute
breite Chipsuche voraussetzen; weitere Varianten nicht automatisch mitidentifizieren.
[Quellenstatus und Rechnung](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst).

Firmwareseitig erwartete IDs von der tatsächlichen ID des konkreten
Controllers trennen. Ein generischer ST-Pfad für mehrere Varianten bleibt
eine Hypothese. Später kann ein bereits vorhandener dokumentierter
Sensor-ID-Diagnoseweg gesondert bewertet werden; keine unbekannten
Gerätebefehle oder experimentellen I2C-Schreibzugriffe und keine aktuelle
Hardwarefreigabe daraus ableiten.

Abnahme: korrekte physikalische Einheiten und nachvollziehbare Achsen, keine
Ableitung des Gyrofaktors aus Accel oder ungeprüften Sony-Werten. Neue
Referenzmessungen brauchen eigene Freigabe. Embercade bleibt ein späteres
Integrationsziel, ist nicht installiert und kein Alpha-Blocker.
Referenzen: [SDL-/DualSense-Vergleich](DUALSENSE_SENSOR_COMPARISON.md),
[Haptik-API](HAPTICS_API.md), [Steam-Grenzen](STEAM_PROTON_BUTTONS.md).

## 3. Nexus als statische Referenz weiter nutzen

Ausgangsbasis: [Nexus 2.1.23.0](GAMESIR_NEXUS_RESEARCH.md), identifizierte
GIP-Update-DLL, getrennte Edition-/Controller-/Dongle-Paketkandidaten,
Windows-Versionsschnittstelle und Motion-/Kalibrierungsdialog.
Noch keine bestätigte Gyro-Skalierung oder sichere Firmwareimplementierung.

Forschungsbacklog; weitere Arbeit nur nach neuem Auftrag und Erläuterung
des Ansatzes. Die untere Funkanalyse ist ausdrücklich zurückgestellt:

1. Native Modell-/DFU-Verbraucher, Live-Versionsquellen, Updatevergleich und
   Controller-/Dongle-Paketpaarung vollständig zuordnen. Konstruktoren und
   Dateinamen-Katalogversionen sind bereits statisch belegt. Paketnamen sind keine geprüfte
   VID/PID-/Hardwarekompatibilität. Gemeinsamen Standard-/ZZZ-Treiber behalten.
2. Mögliche weitere Sensorproduzenten und Kalibrierungsantworten
   verfolgen. [Belegte Datenflüsse](NEXUS_SENSOR_DATAFLOW.md): alle sechs
   Int32-Zugriffe aufgelöst, sieben geprüfte Eingabe-Zustandspfade lassen sie
   null; C2-Profilblock und /255 betreffen Konfiguration. D4X-Sendeweg und
   F1-Firmwarebridge sind zugeordnet. Folgepass vom 18. Oktober: typgebundene
   Profilantworten und generische JSON-/WebView-Weitergabe belegt. MessageC
   liefert im geprüften D4X-Körper auf normalen Rückwegen E_FAIL; tatsächlicher
   Caller und Sensor-Tag bleiben unbelegt. Diesen hypothetischen Abruf
   nachrangig behandeln. Gezielt offen: globale JSON-Settings/Converter,
   weitere Provider und vollständige Header-/Modellzuordnung. Kein Gyrofaktor
   oder Koeffizientenabruf; keine globale Abwesenheit behaupten.
   Profil-/EEPROM-Schreiben von Rohdaten- und Kalibrierungsabrufen trennen.
3. Äußerer Firmwarecontainer inzwischen mit eigenem Offline-Leser geöffnet:
   zwölf Header/Tabellen und 126 logische Eintrags-CRC bestätigt. Weitere
   Firmware-Sensorsuche hat inzwischen den Packed-Split (Feld `+8`) und
   48 gespeicherte Appcontainer belegt; 24 komplette Inhaltspaare sind nach
   Key-/No-Key-Normalisierung gleich. Der anschließende Positionsdecoder
   bestätigt app.bin/cfg_tool.bin vollständig einschließlich Inhalts-CRC.
   **Für den Gyrofaktor jetzt vorrangig:** MCU-Instruktionen und
   Sensorinitialisierung bis zum IMU-Report verfolgen: Sensor-ID/gewählter
   Pfad → letzter wirksamer Messbereich → mögliche Nachskalierung → USB.
   Den aktiven Registerwert nicht ohne Nachweis mit der USB-Skala gleichsetzen;
   Paketfirmware und tatsächlich installierte Version getrennt behandeln.
   Bestehende Werkzeuge weiter nutzen. Nach späterer ausdrücklicher Freigabe
   ist REA zusätzlich lokal und wiederverwendbar eingerichtet, mit
   kopierten Eingaben, privater Ausgabe und Netzwerk-/Geräteisolation.
   Keine Ausführung oder Emulation des untersuchten Herstellercodes.
   REA 6.5.0 unterstützt Jieli-Rohcode nicht direkt; der lokale Quarkslab-
   Pi32v2-Beschreiber ist an drei App-Versionen
   teilvalidiert: 150 Literal- und 150 Transferstellen stimmen mit bekannten
   Ankern überein; die geprüften Transfers verwenden `inst_next`. Die frühere
   `E041`-Nullerweiterungsdeutung ist korrigiert: Die ursprüngliche
   SLEIGH-Regel sagt Nullerweiterung,
   während 44/44 `E040`-Immediates im offiziellen Jieli-Pi32v2-ROM-Listing
   zur Vorzeichenerweiterung passen; 14 negative Werte widerlegen dort
   Nullerweiterung. Ein isolierter privater Decoderlauf findet je 16
   Maskeneinträge, die zu einem gemeinsamen maskierten Update-Helfer führen
   (Laden, AND mit Maske, Zurückschreiben). Das ist kein Sensorpfad.
   Ein Scan der getesteten kompakten und 22-Bit-Sprungformen fand keine
   eingehenden direkten Sprünge zu diesen Einträgen; indirekte Tabellen und
   die Erreichbarkeit bleiben offen. Die Kalibrierungs-/ADC-Loganker enden
   jeweils mit unbedingtem Sprung zum Logger; die vorher behaupteten
   nachfolgenden Stores sind keine bewiesene Fortsetzung. Die getrennten
   EEPROM-Callbacks bleiben ungelöst und sind kein Sensorbeleg.

   **Neuer Stand:** Basis-plus-Versatz-Textadressen führen in DV209/515/608
   zu Lesevorbereitung `0x0f`, Vergleich `0x6a` und Schreibvorbereitung
   `0x11 ← 0x6c`, `0x10 ← 0x68`. Der ST-Kandidat entspricht ±2000 Grad/s
   und 0,07 Grad/s je Sensorzählwert; kein bewiesener USB-Gyrofaktor.
   Der Folgepass verfolgt den Zwölf-Byte-Lesepfad, die sechs 16-Bit-Felder
   und den Tabellensprung `0x10ad4` bis zur vorbereiteten Reportkopie:
   bedingter sechsfacher Offset-Abzug, ST-Reihenfolge `Gy,Gz,Gx,Ay,Az,Ax`,
   keine zusätzliche Gyro-Verstärkung in diesem ST-Abschnitt. Die
   Kopiergeometrie trifft die bekannten Positionen 17–27. Andere Sensor-/
   Ausgabezweige skalieren oder negieren; nicht vermischen.
   Im Transportfolgepass ist die Kopie dem SDK-ROM-Stub `memcpy`/`memmove`
   zugeordnet; der Controllerpfad erreicht IN `0x84`, ein getrennter
   DG144-64-Byte-Pfad IN `0x82`. 37 Forschungstests und 83 unabhängige
   SDK-Instruktionskontrollen bestanden; drei private Decoderformen korrigiert.
   Der [Funkrahmen-Folgepass](JIELI_WIRELESS_DATAFLOW.md) hat inzwischen
   den Formatcache-Writer und einen getrennten passenden `A2`-/Queue-Pfad
   nach IN `0x82` eingegrenzt. In den Transportkopien keine Sensorarithmetik;
   49 Forschungstests, 127 SDK-Kontrollen, vier private Decoderkorrekturen.
   Der [Callback-Folgepass](JIELI_RADIO_CALLBACK.md) ordnet inzwischen die
   tabellenbasierte Registrierung in drei Apps zu; 61 Forschungstests und
   29 abschließende statische Fenster ohne Decodeabbrüche. Der
   [Routingfolgepass](JIELI_LINK_ROUTING.md) klärt nun Listen-/Slot-Auswahl
   anhand der zwölf Bit Verbindungskennung und ordnet den DG-Empfang vom
   aufbereiteten Deskriptor bis zur A2-Queue zu; 70 Forschungstests und
   30 abschließende Fenster bestanden. Der
   [Empfangs-/Kontextfolgepass](JIELI_RX_CONTEXT.md) korrigiert nun den
   privaten Exporter und Stack-Abstände; 81 Forschungstests, 140 SDK-
   Einzelbefehls-Kontrollen und fünf einfache Bedingungsblöcke bestehen.
   Die Callback-Auswahl ist statisch zugeordnet. `0xfe42` verarbeitet
   Paketpuffer über einen Hardwareblock; CCM bleibt eine Hypothese.
   Zurückgestellte Fragen: unabhängige Zuordnung von Registerblock/Parametern,
   Deskriptorursprung, Zustands-/Freigabe- und Kennungs-/Kanalschreiber.
   Diese Lücken blockieren keine spätere Messung des effektiven USB-Faktors.
   Bedingte Parallelblöcke und bestimmte negative Konstanten bleiben
   zusätzliche Decodergrenzen.
   Statische Registrierung beweist keine Laufzeitaktivierung oder Funkzustellung.
   Die weiterhin offenen Halfword-/Vorzeichenformen unabhängig absichern,
   einschließlich des verwandten skalierten Halfword-Stores; außerdem
   weitere Offsetschreiber, Busabschluss und
   letzte wirksame Registerkonfiguration prüfen.
   Aktive Hardwarevariante und Firmwareversion sind dadurch nicht bestimmt.
   [Sensorinitialisierung und konkrete Grenzen](JIELI_SENSOR_INITIALIZATION.md).
   [Datenfluss bis zum Berichtskonstruktor](JIELI_SENSOR_REPORT_DATAFLOW.md).
   [Kopierhelfer und getrennte USB-Sendepfade](JIELI_USB_TRANSPORT.md).
   Der bekannte 64-Byte-Capture bleibt von den untersuchten 60-Byte-Nexus-
   Parsern getrennt; deren Sensorfelder werden weiterhin nicht gesetzt.
   Code-/Datengrenzen, Kontext-/Parallelsemantik und Speicheradressierung
   des unvollständigen Decoders nicht pauschal als bestätigt behandeln.
   Globale Bank-/Modellauswahl und der DV-Inhalt hinter dem
   inneren Appbereich bleiben getrennt offen. MCU-Label
   AC695X und Flashversatz EOFFSET sind keine IMU-Kalibrierung. Key-/No-Key-/Kompatibilitäts- und
   Authentizitätsfragen bleiben getrennt offen. Keine Firmwareausführung
   oder Hardwareaktion aus der Dateidekodierung ableiten.
   Synthetische beschädigte/falsche Pakete müssen sicher zurückgewiesen werden.

Abnahme dieser Phase: reproduzierbare eigene Decoder und belegte
Anfrage-/Antwortspezifikationen auf gespeicherten Daten. Keine Ausführung
proprietären Codes, Online-Abfrage, USB-Kommandos, Bootloaderaktion oder
Weiterverteilung von Herstellerpaketen aus diesem Auftrag.

## 4. Spätere Firmwareunterstützung: eigene Entscheidung erforderlich

**Späterer Meilenstein: optionaler Linux-Firmware-Updater für Controller und
USB-Dongle.** Geplant, noch nicht als Linux-Updater implementiert oder an
Hardware validiert. Diese Aufnahme in die Roadmap beauftragt keine weiteren
Geräteversuche. Die Gyrokalibrierung bleibt pausiert, die untere Funkanalyse
zurückgestellt; beides wird durch diesen Meilenstein nicht wieder aufgenommen.

Ziel ist, beide Komponenten und ihre Firmwareversionen eindeutig anzuzeigen,
passende offizielle Firmwaredateien vorab zu prüfen und erst nach ausdrücklicher
Bestätigung zu aktualisieren. Anschließend sind die tatsächliche Version und
der normale Controllerbetrieb zu überprüfen. Controller und Dongle erhalten
jeweils eigene Kompatibilitäts- und Abnahmenachweise.

Vorhandene Grundlage: Die [statische Nexus-Analyse](GAMESIR_NEXUS_RESEARCH.md)
belegt getrennte Controller-/Dongle-Paketmodelle, Firmwarevarianten,
Containerstrukturen und Prüfsummen sowie Teile des Updatecodes. Sie belegt
weder einen vollständigen Linux-Updateablauf noch dessen sicheren Rückweg.
Ein Offline-Containerprüfer oder erkannter CRC ist keine Flashfreigabe.

Vor der Implementierung eines schreibenden Updaters zu klären:

- **Geräte- und Paketzuordnung:** Hardware-Revisionen, tatsächliche
  Versionsabfragen und die Kompatibilität der Standard-, WFF- und ZZZ-Pakete;
  Controller-/Dongle-Versionspaarung und gegebenenfalls Update-Reihenfolge.
  Ähnliche Hardware, PID oder Dateiname allein erlauben keinen Paketwechsel.
- **Transport und Bestätigungen:** vollständige Anfrage-/Antwortfolge,
  Blockadressen, Größen, Bestätigungen, Zeitlimits und zulässige Wiederholungen.
  Gesondert nachweisen, ob Controllerupdates per Kabel, über den Dongle oder
  per Funk möglich sind; kein drahtloses Update voraussetzen.
- **Bootloader und Besitz:** Ein-/Austritt, USB-Identitäten und Zuordnung nach
  Neuanmeldung; exklusiver Zugriff auf genau die gewählte Geräteinstanz.
- **Herkunft und Integrität:** offizielle Bezugsquelle, Paketformat,
  Signatur-/Authentizitätsprüfung und Vertrauensbasis. CRC-Prüfungen erkennen
  bestimmte Beschädigungen, beweisen aber keine Herstellerherkunft.
  Download-Endpunkte und Weiterverteilungsrechte sind nicht geklärt.
- **Unterbrechung und Wiederherstellung:** Verhalten bei Stromausfall,
  Abziehen, Funkverlust, Abbruch und fehlerhafter Übertragung für beide
  Komponenten. Dual-Bank, Rollback oder Wiederaufnahme nicht aus gefundenen
  Funktionsnamen als vorhanden ableiten. Eine xpad-Rückbindung ist keine
  Wiederherstellung beschädigter Firmware.
- **Erhalt vorhandener Daten:** Auswirkungen auf Kopplung, Profile und
  Kalibrierungsdaten untersuchen; Sicherung oder Wiederherstellung nur dann
  zusagen, wenn das jeweilige Verfahren tatsächlich nachgewiesen ist.

Architekturziel: separate optionale Userspace-Anwendung mit exklusiver,
expliziter Übergabe durch den nativen Manager. Kein Flashen im Kernel oder
Alpha-Autostart, keine automatischen Firmwareupdates und keine parallelen
USB-Besitzer. Die Update-Übergabe ist ein zukünftiger Vertrag, keine bereits
validierte Managerfunktion. Keine proprietäre Firmware in Repository oder
Linux-Paket; die Bezugsmöglichkeit und Rechte müssen vor einer Veröffentlichung
geklärt sein.

Geplante Reihenfolge nach gesondertem Entwicklungsauftrag:

1. Vorhandene statische Befunde zu einer belegten Protokoll- und
   Kompatibilitätsspezifikation zusammenführen; offene Stellen kennzeichnen.
2. Offline-Prüfer und simulierten Updateablauf einschließlich beschädigter
   Pakete, falscher Gerätezuordnung, Zeitüberschreitungen und Abbrüchen testen.
3. Erst mit dokumentiertem Update- und Wiederherstellungsplan einen begrenzten
   Hardwareversuch zur konkreten Freigabe vorlegen. Kein Flashen auf Verdacht,
   keine automatische Wiederholung und keine behauptete Rückkehr ohne Nachweis.
4. Abnahme je unterstützter Hardware-/Firmwarekombination: passende Datei,
   bestätigte Übertragung und Prüfung, erwartete neue Version, funktionsfähige
   Kopplung und normaler Spielbetrieb. Grenzen der Wiederherstellung offen
   dokumentieren; keine allgemeine Updategarantie aus einem einzelnen Erfolg.

Dieser spätere Meilenstein blockiert weder den stabilen Spielbetrieb noch
die unabhängige Entwicklung der Sensor-/Spielintegration.


## Revision 15 startup follow-up — 20 October 2026

Receiver-off waiting and one late power-on now pass their scoped target tests;
see [the late-on audit](RELEASE_AUDIT.md#revision-15-late-power-on-starts-automatically--20-october-2026).
The maintainer accepts automatic binding with the reported brief initial xpad
contact; this is not a blocker. Optional later research may resolve that contact:
snapshots first see the new100a lifetime already native. Do not claim xpad independence
or change global xpad registration/blacklisting from this evidence. Review
supported-device first-probe ordering and saved kernel/manager chronology
before proposing any acquisition change. Controller-off cold boot, second RF
reconnect and application regression remain separate acceptance items.

## Control Center: package updates without replacing the AppImage

Maintainer requirement, 21 October: compatible driver-package releases should
be discoverable/installable through the existing application. The current
reviewed public-package rebuild uses immutable per-version pins and does not
implement this yet. Follow the [signed catalog design](CONTROL_CENTER_RELEASE_UPDATES.md):
review verifier/key lifecycle and bounded versioned protocol, independently
verify in both GUI and root helper, preserve upgrade/removal guards and reject
replay/downgrade. Start with offline fixture tests; a production signing key,
publication and one-time helper migration require explicit review. No silent
adoption of GitHub latest/checksums or installed helper overwrite.

### Signed update implementation checkpoint

Offline app/helper verification, protocol v3, replay/downgrade/guard checks,
atomic root catalog checkpoint, explicit DE/EN worker UI/cancellation, user
cache/offline removal and external-key publisher are implemented with fixtures.
Two driver versions use unchanged app/helper anchors in the end-to-end test.
Pending: production key lifecycle/policy review, one-time helper/profile
migration, publication of the signed metadata channel, real metadata-only
transport acceptance and separately authorized installation/hardware tests.
No production key or live change is part of this checkpoint.

### Approved production-key/offline-build checkpoint

A separate external Ed25519 release key and explicit public-only policy now
exist after maintainer approval. The new local AppImage and staged helper share
that public anchor and verify catalog revision1 offline. Existing public core16,
Steam2, Gamescope1 and bridge2 archives/removal history are unchanged. Targeted
67 unit/packaging +3 QML cases, four packaged synthetic smoke lanes, actual-key
positive/negative checks and private-material inclusion checks pass. Installed
helper/driver/state and all live services/Steam remain unchanged. Nothing
published or uploaded. Generic unbound builds still have no automatic key.

Next: encrypted offline key backup; tested/exactly reviewed helper-only migration
and separate approval; runtime/source redistribution audit; signed-channel
publication/download-only acceptance; separately approved package acceptance.
No blind legacy-helper rollback after signed-state acceptance. See
[custody, public fingerprint and build limits](CONTROL_CENTER_SIGNING_PROVISIONING.md).

### Consolidated backup/handover preparation complete

The offline maintainer backup, exact helper migration and partial recovery,
single approval launcher and final local AppImage are implemented/tested.
388 Control Center cases incl61 QML, four packaged lanes and an actual-payload
temporary-root forward/reverse proof pass; zero production backup/root/live
driver operations. Source defaults/normal first-run remain unchanged. Next is
one exact approved local handover, followed by off-device encrypted backup
confirmation and the existing public distribution/channel/package acceptance
gates. No new driver/kernel work or automatic package action is required for
the helper migration. [Final workflow](CONTROL_CENTER_HANDOVER.md).
