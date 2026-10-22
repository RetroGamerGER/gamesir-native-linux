# TMR preview: button flicker, lag and manager CPU

22 October 2026. **Preview correction installed and checked on Garuda;
first standard-controller calibration workflow also checked.**
[Machine-readable results](evidence/TMR_DISPLAY_POLLING_20261022.json).
[Later installation/preview receipt](evidence/TMR_DISPLAY_UPDATE_20261022.json).
[Subsequent first calibration receipt](evidence/TMR_FIRST_LIVE_CALIBRATION_20261022.json).

**Subsequent calibration:** A new explicit Go led to one guided standard109c
run. Both-stick readiness and Finish were followed by clean manager lease
return and a positive independent KDE input/center/travel check. No power
cycle or independent NVM readback was performed. The preview-only statements
below describe the earlier installation checkpoint.

## Later approved installation and preview

The maintainer approved a matching manager/helper/GUI update and preview,
while retaining the Go gate for actual calibration. Local core alpha3-20
and helper alpha1-2 were installed in one package transaction after controlled
receiver removal. Installed payloads, all eight helper pins, root modes,
DKMS/vermagic and unchanged sensor configuration were checked.
All 16 kernel/shared source files match revision 19 byte for byte.
No new permanent TMR setting was added; the previous temporary opt-in and
active/enabled service were restored. Steam/bridge packages are unchanged.

After the maintainer reconnected the receiver/controller, one Resume reached
native runtime with gamepad, IMU and input publication confirmed. The initial
read-only journal precondition had stopped before Resume because `-n0` produced
no cursor; `-n1` and explicit cursor-line parsing fixed that observer input.
The interrupted log is retained privately; no duplicate Resume was issued.

The matching corrected GUI then opened. The maintainer confirms that Start
stays steady and both sticks respond without perceived delay. An unprivileged
ten-second process-counter sample during the selected-controller preview found:

| Process role | Mean CPU (100% = one core) |
|---|---:|
| Manager | 6.3% |
| GUI (software-rendered Qt) | 5.1% |
| TMR helper | 0.9% |

All three processes survived the interval with unchanged process start IDs.
The new GUI log was empty. The old approximately 49% manager figure was a
screenshot at a different time, so this is not an identical before/after
benchmark. Actual end-to-end display latency was not instrumented.

The GUI remains in preview; no calibration Start/Finish or persistence test
has been performed. The maintainer's next explicit Go is still required.
Package recipes were overridden only in private local build directories;
public versions, signed catalogs and releases were not changed or pushed.
The following sections preserve the preceding offline investigation.

## What was actually observed

After the maintainer's Go, the experimental GUI opened and explicit controller
selection produced moving stick plots. The maintainer reported:

- “Kalibrierung starten” continuously blinked.
- Stick movements appeared with some delay.
- The manager process used approximately 49% CPU in their screenshot.

They explicitly confirmed they had **not pressed Start**. At our request they
closed only the calibration dialog; the main window stayed open and the
reported CPU load disappeared. These reports do not establish successful
Start/Finish, persistence, exact display latency or a calibrated controller.
No new live observation run, device read, calibration command or installation
was initiated while preparing this correction.

## Reproduced causes

Every background poll set the same busy flag as an explicit action. QML
therefore disabled and enabled the primary button for each read. A click
during a read could also be discarded. The existing deterministic GUI tests
stopped the periodic timer and missed this interaction.

The 100ms timer restarted after each reply, adding the full IPC round-trip
latency to every interval. In addition, helper update first inspected/ticked
the adapter and then inspected it again to accept a new snapshot.

Each native poll called the manager's TMR watchdog and selection checks.
Those called the ordinary ownership guard, which scans every process FD and
rechecks USB descriptors before and after that scan. The daemon's normal
watchdog repeated it. These costly scans were on the display path although
the manager already held an exclusive, kernel-checked maintenance FD.

## Correction

Display activity no longer changes the action-busy flag. A fixed 33ms timer
offers about 30 snapshots per second when responses are fast enough; a slow
read causes ticks to be skipped, never queued or replayed. There is at most
one request in flight and one pending explicit Start/Finish click. The click
is rechecked against the returned state, consumed once and discarded on
close, lost readiness or failure. A background reply cannot re-enable a
button while its explicit action is pending.

One adapter inspection now supplies the exact cached snapshot to normal
identity/format/freshness checks before advancing the preparation timer.
Rereading a report never advances its RX count or timestamp.
Device submissions retain independent pre/post confirmation.

For an already held lease, display polling and the watchdog check current USB
metadata/binding, exact tokens, kernel FD status, stream epoch, generation,
lease expiry and genuine E0 freshness. They do not enumerate process FDs.
This read check cannot acquire a device or authorize USB output.

Listing, probing and lease admission retain the complete ownership audit.
Start, Finish and Exit also require complete process-FD/ownership checks
before **and after** submission. A conflict after uncertain submission ends
the run without retry or compensating device command. No cached scan result
is treated as command authority. Lease renewal/return remains local to the
kernel and does not send a calibration USB command.

Kernel sources, wire format, calibration values, module options, gyro,
paddles, ordinary rumble and Steam settings are unchanged. The 1.5-second
freshness limit and two-second lease remain unchanged. Short unobservable
radio gaps remain an explicit limitation.

## Offline evidence and limits

The old source failed negative controls for the disabled/flashing button,
lost click during a read, fixed polling cadence, duplicate helper polls and
process-audit count. The corrected source passes 16 added regressions:
seven real-QML/worker cases, two helper/session cases, five manager-policy
cases and two tests of the real metadata adapter against injected files.
They include slow reads, duplicate clicks, cancellation, revoked Finish
readiness, device replacement, foreign USB ownership and post-submit conflict.

Complete `make test`: 1,868 Python test cases in 69 unittest groups, plus
the existing compiled C/fake-kernel/ASan/UBSan checks, all passed.
`make test-control-center-ui`: 98 cases in ten groups, all passed.
No kernel/module build is needed for these userspace-only source changes.

A separate offline comparison used the real metadata/FD guard with a temporary
synthetic USB tree and 120 fake processes, each with 64 unrelated FD symlinks.
The unchanged native backend was replaced by a memory-only test double.

| Same workload | Before | Corrected |
|---|---:|---:|
| Display polls + explicit watchdog ticks | 30 + 30 | 30 + 30 |
| Full process-FD scans during this workload | 90 | 0 |
| Fresh metadata checks in the scoped read guard | 0 | 60 |
| CPU time for this workload | 0.872463 s | 0.014265 s |
| Start/Finish/Exit sent | 0 | 0 |

The timing is a synthetic local comparison, **not** a prediction of exact CPU
usage or latency on either installed system. The faster display cadence also
means the live workload differs. A separately approved preview must verify
the actual improvement before calibration continues.

## Historical offline deployment boundary

The installed alpha3-19 manager and alpha1-1 TMR helper, loaded module, main
window and frozen original GUI snapshot were not replaced. A matching corrected
manager, root-owned helper and hash-pinned GUI must be deployed together.
Changing only the GUI would retain the expensive installed read path; changing
only helper bytes would fail its expected-hash check.

Prepare that update as a separate reviewed transaction. No implicit service
restart, Release/Resume, new calibration run, package installation, public
AppImage, release, tag or push is part of this fix. The earlier Go was for
the interrupted preview, not automatic retries. Precision gyro work stays paused.
