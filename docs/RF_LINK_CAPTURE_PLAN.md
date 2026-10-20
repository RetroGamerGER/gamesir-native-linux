# Receiver present, controller off → on: capture preparation

20 October 2026. Preparation only, on the maintainer's primary KDE machine.
The receiver is reported plugged and the controller off. The earlier blocked
revision-14 inspection concerned the separate Gamescope machine; do not assume
the same USB path, kernel, binding or manager fault on this target. No fresh
host inspection, capture, password prompt or runtime change occurred during
initial preparation. The subsequently approved first read is recorded below.

## First authorization gate: cached-state inspection

`tools/native/rf_link_preflight.py` defaults to an offline plan. Its separate
`inspect` mode requires explicitly approved root read access, discovers cached
GameSir USB attributes and driver links without reading serials or opening USB
devices, then runs only these fixed read commands:

```sh
/usr/bin/gamesir-native status
/usr/bin/systemctl show gamesir-native.service --property=ActiveState,SubState,UnitFileState,NRestarts,MainPID
/usr/bin/pacman -Q gamesir-native-dkms gamesir-native-steam
/usr/bin/journalctl -b -u gamesir-native.service -n 80 --no-pager -o short-monotonic
/usr/bin/journalctl -b -k -n 100 --no-pager -o short-monotonic
```

They are read operations, not service controls. Each runs at most once, with a
ten-second ceiling. A failed command or manager fault/busy/unknown report stops
the collection, retaining original stdout/stderr and bootstrap diagnostics.
Multiple/foreign/ZZZ targets cannot be guessed into this standard-model run.
Missing usbmon is reported, never loaded. Only its node metadata is inspected;
the monitor is not opened. Final cached identity/boot comparison rejects a
changed baseline without repeating the scan as a new attempt.

After approval, from the repository root, the one proposed privileged entry is:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' \
  /usr/bin/python -I tools/native/rf_link_preflight.py inspect
```

The password goes only into the graphical prompt. Its report is private:
journals and metadata may contain local paths/device identities. Keep any saved
report under a new ignored, private evidence directory, never in public Git.
`capture_ready` is deliberately always false: this helper is not a recorder
audit or permission to continue. Exit 1 means blockers; exit 2 means a read or
schema failure. Neither authorizes recovery, module loading or retry.

## Choose the reference path after inspecting the baseline

An unmodified native observation can record the currently running manager's
natural reaction to radio power-on. A blocked/quiesced native receive path
cannot establish that the receiver sent no connection report. Stop and review
that state first; do not clear it or replay START to obtain a positive trace.

An **xpad reference run** can isolate the stock connection sequence from the
native manager. It may therefore be the better first baseline if native is
blocked. Any pause/release, actual return, manual unplug/replug or rebinding
requires its own concrete approval after fresh state is known. Pausing the
manager alone does not prove that xpad owns the interface or reception is open.
No such state-changing commands are approved or executed by this plan.

Preserve actual `100a` XInput versus `109c` GIP identity and endpoints. A `100a`
reference does not by itself prove the `109c` Hello sequence or vendor IMU
readiness. Keep different transport personalities and enumeration epochs in
separate analysis. Choosing xpad for a reference is not a decision to discard
native gyro/paddles/four-motor support or globally blacklist either driver.

## Proposed human-paced recording, still behind a second gate

Proposed maximum capture: **90 seconds**, after explicit approval and local GO.
No automatic start at prompt expiry. No application, Steam, driver, binding or
module changes by the recorder. Games and Deadband should remain closed. An
ordinary KDE input-test consumer, if needed by the verified binding, must be
explicitly prepared and confirmed; binding alone is not evidence of active IN.

| Capture seconds | Human action |
| --- | --- |
| 0–30 | Controller remains **off**; preparation and off baseline |
| 30–60 | Clear JETZT cue: turn it on once, then wait; no buttons/sticks |
| On visible connection | Mark keyboard confirmation with host monotonic/UTC timestamp; subjective observation, not exact RF packet time |
| 60–80 | Only if connection was confirmed: one A press, both sticks, gentle motion |
| 80–90 | Rest; controlled recorder stop, no further reconnect |

If connection is not confirmed by the end of the connection window, stop
without extending/retrying or sending initialization. Do not mix the no-button
connection interval with later deliberate gamepad activity. Mark actual cues
and confirmation times, not an assumed instantaneous human response.

Keep receiver port and parent/boot lifetime fixed, but record and validate USB
replacement at that topology. Never filter only the initial device address:
retain descriptors, endpoint zero and native IN/OUT for each confirmed epoch.
Unknown devices, an unexplained topology change or a genuine read/guard failure
stop capture; expected address changes are not permission to adopt a different
receiver. Temporary missing cached attributes need bounded, separately tested
observation handling, not invented identity. Record hello/status/input ordering
and both host submissions/completions without treating a submission as an ACK.

## Recorder readiness boundary and validation

The existing isolated recorder supports only the legacy native-motor scope or
fixed-identity `100a` HID scopes, currently pinned to one historical USB bus.
It must **not** be run with an improvised manifest, a different PID or disabled
identity guards. A native radio-lifecycle profile is not implemented in this
preparation step. Its exact execution command/source pins must follow review of
the fresh baseline and the selected reference path, then explicit approval.

Reuse the reviewed isolation principles: only the confirmed bus monitor in a
private namespace, no raw USB/HID nodes, no recorder network, no capabilities,
NoNewPrivs, bounded duration/storage/logs and process-identity checks. Preserve
raw evidence privately, verify checksums, inspect drop counters offline and
report unavailable loss/connection information as unknown. No automatic Release,
Resume, service restart, reset or module operation belongs in the recorder.

Twelve preflight tests use only temporary saved filesystem fixtures and fake
commands. They cover default-no-inspection, root gate, identity/owner reporting,
multiple/unsupported receivers, blocked/failed/malformed manager reads, missing
or wrong monitor node, no shell/retries and changed baseline. Existing recorder
tests remain separate; these tests do not validate a new live recording scope.

## Approved first read: stopped at manager fault

The maintainer approved the shown read-only step. One `inspect` invocation
with the matching committed helper/hash ran on the primary KDE machine. It
observes kernel `7.2.11-1-garuda`, one standard receiver under `3537:109c`, IF0
on xpad and IF1 unbound. Native management remains unpaused, with a blocked
entry and `Unowned new 109c instance; no END attempted`. Its stored original
bootstrap status is state 8, error -108 (`ESHUTDOWN`), failed stage 1, pad/IMU
zero. That is saved failure history, not a fresh USB/native-control query or
proof of present RF state. A current xpad binding is not a verified native
return to 100a or a cleared administration state.

The helper returned 1 at the explicit manager-fault gate. Only the single
manager status query ran; service/package/journal and monitor queries were
not reached. No repeat, recording, power-on cue, release/resume, module or
binding operation followed. Original private output and a verified checksum
chain are retained; [sanitized checkpoint](evidence/RF_LINK_PREFLIGHT_20261020.json).

Before an xpad reference recording, resolve the administration baseline with
separate approval and actual ownership checks. Do not infer empty native leases
from xpad binding alone. Preserve this original diagnostic and avoid an automatic
recovery attempt. No receiver removal or controller power-on is requested here.

## Controlled pause prepared after ownership read

The maintainer subsequently requested the read-only ownership check before
approving a pause. One protected snapshot read the private state, queried manager
status once and compared cached USB/boot/state before and after. They are stable.
Exactly one blocked lease remains for the old `100a` source. It has no kernel
ownership tokens or candidate, and no live job. The current `109c`/xpad device
has a different device inode while retaining the same parent lifetime. This is
an unresolved old management record, not authority to act on the replacement.
[Sanitized ownership and offline pause check](evidence/RF_LINK_PAUSE_PREPARATION_20261020.json).

The actual installed manager (hash in that report), rather than a newer source
checkout, was reviewed. An offline simulation of its extracted pure
`command`, `return_one` and `returned` methods used only synthetic host methods.
It confirms that release persists pause first, the blocked replacement path
issues no END/restore, the old lease remains and return is not claimed. Resume
rejects unresolved ownership. No real manager action ran in that simulation.

Proposed state-changing command, **not yet executed**, after explicit approval
and unchanged fresh ownership/source checks:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' \
  /usr/bin/gamesir-native release
```

Exactly one release is proposed. The installed client polls read-only status
for up to 45 seconds after its single release request. With this unresolved
`109c` lease, expected pause=true and returned=false/exit1 mean that management
is inhibited but a complete fallback is **not confirmed**. Do not interpret
that as a failed pause, retry release or follow it with resume. Preserve the
original -108 diagnostic, then only read back state/bindings to establish what
actually happened. No service stop/start, unbind, module unload, USB reset,
recording, physical removal or controller power-on is included in this step.

The user's suggestion of stop/resume is not the selected reference-test path:
service stop may run cleanup, while resume explicitly re-enables native
takeover. Neither is proof that the old ownership record has been resolved.
The controller remains reported off and the receiver plugged.

Validation note: the protected reader's own-module import created one local
root-owned Python bytecode cache, causing the licensing walk to fail on its
permissions. That exact generated cache was validated against the source header
and removed; no driver/service/USB file was changed. Subsequent root Python
helpers must use `-B` before imports. The seven documentation and three licensing
checks then pass. This cleanup is not release/recovery or renewed test approval.

## Approved release completed: pause confirmed, return unresolved

The maintainer explicitly approved exactly one release with password prompt
and read-only postcheck, controller remaining off, no capture or resume.
A fresh protected snapshot matched the previously inspected boot, receiver,
state bytes, blocked lease and actual installed-manager hash. A private
exclusive attempt receipt was created before the single release invocation;
it must not be reused for another attempt.

The release client completed with exit 1, `paused=true`, `returned=false`, as
anticipated. The subsequent protected read independently confirms both live
manager pause and `state.json` pause=true. Before/after cached state and USB
snapshots are stable. The receiver remains `109c` on xpad, IF1 unbound. The one
old blocked lease and recent-failure history are unchanged, including the
original unowned replacement/-108 bootstrap diagnostic. Source and boot are
unchanged, and no manager job is busy. [Sanitized result](evidence/RF_LINK_RELEASE_20261020.json).

Thus management inhibition is confirmed; a full usable return, empty ownership
or change to 100a is **not** established. Do not repeat release, resume, stop or
restart the service, clear state or manipulate the receiver from this approval.
No capture, module operation, explicit binding change or physical action was
requested/performed. The controller remains reported off, receiver plugged.
Any next recovery/reference step needs its own reviewed authorization. Private
outputs and checksum chain are retained. No public push.

## Manual return to 100a prepared, not started

The maintainer selected a `100a` reference to observe radio power-on under
xpad. That is a valid separate question: it need not provide the native 109c
IMU stream to be useful. The next request is preparation of physical return
on the primary KDE machine, keeping native management paused/controller off,
with fresh reads and physical actions still subject to approval/cues.

The installed manager's source hash still matches the inspected version.
Offline simulation of its extracted pure tick/return/failure methods confirms:
paused continuous confirmed absence retires an old lease only after ten
seconds; unknown metadata resets that clock; an unpaused fault is retained.
Retirement preserves the original diagnostic in failure history, with a
physical-absence resolution. Empty ownership plus stable normal observation
is needed for returned=true. A newly observed 100a is not acquired while
paused. This is fake-host policy coverage, not a new device/manager invocation.
[Preparation/source receipt and checks](evidence/RF_LINK_100A_RETURN_PREPARATION_20261020.json).

Proposed authorized sequence, to be executed only after approval:

1. Fresh protected read: match the last verified boot/source/current109c-xpad
   lifetime, live and persisted pause=true, no active job or native binding.
   Keep the original blocked lease/diagnostic; never delete it manually.
2. Only after that passes, cue **JETZT abziehen**. Remove only the small GameSir
   dongle; keep the controller off and leave the dongle out.
3. Allow at least **15 seconds** outside the port, then inspect. Require cached
   physical-port absence, no supported/native bindings, empty persisted leases,
   no live managed devices, pause=true and returned=true. Stop if unknown or
   unresolved; elapsed wall time alone is not sufficient proof.
4. Only after the absence/ownership proof passes, give a separate cue to reinsert
   into the same physical port. Controller remains off. Do not resume native.
5. Fresh read: require `3537:100a`, the expected same parent lifetime but a fresh
   enumeration, IF0 xpad EP02/82 and IF1 usbhid EP04/84, empty ownership and
   unchanged live/persisted pause. Actual address is observed, not assumed.
   If it remains 109c or any other field differs, stop without guessing commands
   or repeating removal. A receiver-only 100a baseline is not proof of RF link.

A new private read-only helper is prepared in the ignored evidence area. It
retains bounded protected state reads, original status stdout/stderr, source
pinning and before/after state/boot/USB consistency checks. It also observes
the explicitly selected port even if its identity is temporarily unknown,
endpoint metadata and global native binding links. It issues only status;
no device/monitor open or sysfs write. Use `python -I -B` with the graphical
askpass wrapper and record each phase separately. Its exact source hash is in
the preparation receipt; the helper has not been executed on the live host.

No new release, service stop/start, module operation, firmware/mode command,
manual state reset, input test or recording is needed for these physical
return checks. No physical action or privileged read was performed in this
preparation step. The previously approved release remains consumed, and the
current receiver is still last verified 109c/xpad with persistent pause.

## Approved physical return attempt: administration cleared, still 109c

The maintainer approved the staged physical/read sequence. Fresh protected
precheck matched the paused 109c/xpad baseline and original source/boot/lease,
with no native bindings or active job. On cue the maintainer confirmed removal
of the small receiver with controller off. At least 15 seconds after that human
confirmation, the protected check proved port/device absence, no native binding,
empty leases and managed devices, persistent/live pause=true and returned=true.
The old -108 diagnostic remains in failure history with physically-absent
resolution; no state file was manually cleared.

Only then was reinsertion at the same port cued. The maintainer confirmed the
receiver reinserted/controller still off. The next protected read is stable and
shows a new USB device lifetime at the same parent, source and boot. However,
it is **3537:109c on xpad again**, not the planned 100a personality. IF0 has
EP02/82; IF1 is unbound with no endpoints. Live/persisted pause remains true,
leases/managed devices remain empty, returned=true, and no native bindings
are present. [Sanitized result and private report hashes](evidence/RF_LINK_100A_RETURN_ATTEMPT_20261020.json).

The sequence stopped at that explicit PID mismatch, with no second removal,
new release/resume, guessed mode command, module/binding/reset operation or
capture. The receiver remains plugged and the controller reported off. The
intended 100a baseline was **not reached**. Do not infer a guaranteed 109c→100a
power-cycle transition or its persistence mechanism from earlier examples.

Administrative cleanup and pause are now confirmed; returned=true here only
covers the empty managed set. It is not proof of 100a or of ordinary input/RF
function under 109c/xpad. A reference recording on this clean 109c/xpad state
would be a separately reviewed scope, not automatic continuation of this
100a plan. Private phase outputs, actual cue/confirmation times and verified
checksums are preserved. No public push or precision calibration.

## Separate 109c/xpad recorder prepared offline

The maintainer now selected a new passive 90-second reference from the observed
clean 109c/xpad baseline. Read [RF_LINK_109C_CAPTURE.md](RF_LINK_109C_CAPTURE.md)
for scope, timeline and concrete staged commands. `rf_link_capture.py` defaults
to an offline plan; privileged inspect and isolated execute are distinct gates.
Fresh live pause/empty ownership, exact current receiver and ordinary IF0 input
consumer are required. Source/instance pins are not recycled from the physical
return. Same-parent re-enumeration is recorded as distinct lifetimes with bounded
unknown metadata; it never authorizes control or proves an RF link. No new host
read, capture, module, controller power-on or binding/service change occurred.
The old 100a recorder and its constraints remain separate and unchanged.
