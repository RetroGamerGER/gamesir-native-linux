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

## Hardware safety

No module loading/unloading, driver rebinding, identity switch, active motor
or sensor test, installation or firmware access without separate explicit
authorization. Never flash firmware or guess undocumented device commands.
Document and verify the safe return to xpad. Deadband must retain a supported
exclusive maintenance path; normal play must not depend on it.

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
192/194 nonzero vectors. Later object/readiness/subscription/timing gates are
not established for the failed run. Do not call the unidentified three-field
notification gate acceleration, or equate UI RawSpeed with raw USB counts.
No exact root cause or fix is proved; preserve working SDL/Eden and runtime.
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
