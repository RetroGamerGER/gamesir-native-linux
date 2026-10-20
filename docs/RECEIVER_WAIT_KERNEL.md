# Experimental persistent receiver waiting — implementation and evidence

Packaging follow-up: revision16 supplies receiver_wait=1 in the vendor modprobe
configuration while retaining the direct kernel default false and local override
precedence. Revision15 scoped waiting/late-on tests passed; see the current
[release notes](RELEASE_PRE_ALPHA_3.md), [installation guide](INSTALLATION.md)
and [audit](RELEASE_AUDIT.md). The offline scope statements below describe the
original implementation checkpoint before that separately approved work.

20 October 2026. Implements the contract proposed after the
[PID-transition comparison](RF_PID_TRANSITION_COMPARISON.md). No installation,
module reload, SSH, controller access or Steam change. Real late-power-on
behavior remains unvalidated. The previously installed driver is unchanged.

## Scope and activation boundary

The new read-only module option **`receiver_wait` defaults to false**. It
requires persistent mode, which already requires bootstrap mode and output
permission. No packaged configuration enables it. Using it on hardware needs
a separately reviewed installation/activation; this document starts no test.
Use the matching updated manager and control client, not an older pair.

With the option disabled, existing finite and persistent bootstrap verification
remains unchanged. In particular, missing native IMU still reaches the legacy
VERIFY timeout; the historical revision-14 failure has not been reclassified
or erased. The opt-in path changes the receiver lifecycle, not the gyro scale,
axis mapping, paddles, rumble duration, trigger bridge or Steam configuration.

## State and transfer contract

The existing startup state values 0–8 stay unchanged. The shared kernel-used
core appends **WAIT_RECEIVER=9**, exposed through the existing private project
`GSN_GET_BOOT_STATUS`. Request/status sizes, ioctl numbers and ABI version stay
unchanged. This is no new Linux input/force-feedback UAPI.

```
exact acquisition → one bounded setup → WAIT_RECEIVER
                                     ↓ fresh native IMU
                                 READY → one runtime handoff
```

- `100a` retains its one bounded control-IN query and nine transition OUTs,
  actual removal/arrival checks, correlated new `109c` handover and six native
  setup OUTs. Direct `109c` and experimental `105e` use six native setup OUTs
  on the exact claimed instance. Nothing here invents another USB command.
- After all six native setup transfers and the existing final settle interval,
  the opt-in core enters WAIT_RECEIVER. It generates **no further OUT intents**
  there: no repeated initialization, periodic startup heartbeats, radio polling,
  timeout reset or motors. The existing receive URB stays active. A low-frequency
  250-ms service check supervises identity/runtime faults; it sends no USB OUT.
- Waiting may exceed the original setup deadline indefinitely. Initialization,
  transfer and USB re-enumeration deadlines remain finite *before* waiting;
  a pending transfer can never be parked in this state. Regressing clocks,
  malformed data, RX/submit failures or changed identity/ownership stay errors.
- Neutral pad reports, ordinary pad activity, unknown GIP status, HID traffic
  and descriptors do not establish native readiness. A complete current-native
  IMU frame is still required, with the existing one-second freshness check.
  Stale samples leave the receiver waiting. No button/nonzero value is required.
- Fresh IMU allows one bounded handoff to the existing persistent runtime.
  The handoff has its own one-second deadline; it cannot revive a prior error.
  Runtime heartbeat/motor scheduling starts only after this handoff, using the
  continuing sequence. Existing input-publication/seat checks still apply.

The code does not claim `radio_connected=true` merely because it is waiting.
The distinction is receiver acquired/setup complete versus native runtime ready.

## Kernel/client/manager ownership

The BOOTSTRAP ioctl returns when runtime handoff completes **or** when setup
has reached WAIT_RECEIVER. Its synchronous setup supervision and pending
handover-list lifetime stay bounded. The bound native device retains the shared
bootstrap object and passive receive context after the caller exits; no
indefinitely blocked userspace process is needed. The old control FD may remain
a diagnostic handle across a correlated `100a→109c` handover.

The client prints `Native receiver waiting.` for state 9 and explicitly does
not print `Native startup completed.`. The manager independently locates and
attests the actual native instance with exact cross-FD tokens, stores phase
`receiver_wait`, then performs bounded read-only status checks at two-second
intervals. Waiting does not consume another start budget. Busy control access
backs off; incomplete metadata retains ownership without a new mutation.

A same-boot manager restart reattests its recorded waiting instance. It does
not bootstrap it again. Explicit Resume preserves a healthy recorded wait.
Only a matching successful kernel handoff reaches the normal runtime/input
publication path. A mismatching token blocks adoption. A late failed status
retains the original bounded diagnostic and permits cleanup only.

A new USB lifetime is independently discovered, never adopted with old tokens.
If a pending old wait-status read races an observed replacement, only an
otherwise healthy old waiting/handed-off result, or its exact ENODEV/failed-stage-9
removal result, may retire the old lease under the existing same-parent and
supported free/xpad-owner checks. A different transport fault is retained and
blocks instead. Discovery waits for a fresh scan and its normal start budget;
no command is sent to the replacement using the old ownership proof. This is
USB-lifetime handling, not a claim that a PID transition proves an RF link.

## Stop, removal, failure and suspend

Root END of a waiting receiver requires the existing capability, exact bound
instance, parent/route and kernel ownership checks, plus complete setup with
no pending transfer or motor output. It cancels the core, stops receive/work
and neutralizes local state. No initialized motor runtime means no motor output
to authorize; the established active-runtime final zero packet remains intact.
Closing an informational client does not replay/cancel setup or keep a process
alive. No pulse, session START, publication or PM RESUME is granted by pending
state 9. END's client token check accepts pending ownership only for END.

Late worker/RX faults quiesce a waiting instance even though its original
supervisor has returned. A subsequent local END cannot replace the first error.
Physical USB removal retires that kernel lifetime; it grants no automatic
handover to an unrelated receiver. Manual unbind remains cancellation.

Suspend/reset/shutdown safely cancel an **unready** waiting bootstrap and
drain receive/work, preserving the existing quiesce policy. This implementation
does not automatically reinitialize or resume that cancelled wait. Active
persistent runtime PM behavior remains on the existing separately checked path.
Neither END nor cancellation pretends to change `109c` back to `100a`: unresolved
fallback remains explicitly reported and may need the documented manual return.

## Offline validation and remaining acceptance

- 28 added shared-core cases cover all three start PIDs, simulated 24-hour
  no-TX waiting, late fresh IMU without buttons, stale samples, malformed input,
  clock/ownership changes, cancellation and unchanged pending-transfer bounds.
- 21 added actual-kernel-function adapter scenarios bring that ASan/UBSan
  suite to **303**. They exercise synchronous return, day-long waiting, actual
  RX/adoption without a userspace FD, END, late fault retention, suspend and
  permission/identity rejection and boundary-signal cancellation with balanced references.
- 12 added manager tests cover long wait without extra budget/start, readiness
  publication, restart, Resume, pause/END, original error, foreign tokens,
  unknown metadata, busy status and replacement races. The real C client is
  tested with synthetic syscalls for pending output and END-versus-INFO gates.
- Full `make test` passes: **1,339 Python tests**, plus C/sanitizer/client checks.
  Packaging tests also pass with the new test file included in the tracked
  source inventory. This is offline regression evidence, not hardware acceptance.
- The module builds for the local prepared `7.2.11-1-garuda` headers with W=1
  and code warnings treated as errors. Zero code warnings; Kbuild reports the
  retained environment advisory: kernel Clang 23.1.1 versus module Clang 23.1.3.
  Strict checkpatch passes; all five Clang analyzer translation units report
  zero diagnostics. No module was installed or loaded.

**Unproved on real hardware:** whether the one setup sent with the controller
off is retained and later native IMU arrives without initialization replay.
The new state deliberately waits rather than guessing more commands if that
does not happen. Controller-off boot/late-on, same-enumeration data arrival,
natural replacement, post-ready RF reconnect, stop/recovery and application
compatibility need separately approved Garuda and CachyOS/Gamescope acceptance.
This build does not close the pre-push hardware blocker or authorize a release.

[Sanitized offline build/test evidence and source hashes](evidence/RECEIVER_WAIT_OFFLINE_20261020.json).
