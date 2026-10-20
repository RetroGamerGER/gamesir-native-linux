# Passive radio-start reference: 109c/xpad, 90 seconds

Status, 20 October 2026: **one approved RF capture completed**; see the completed
run below. Earlier, a metadata-only preflight stopped at its combined baseline
gate; its diagnostic correction was developed offline before later separately
approved reads, usbmon loading and capture. Native is confirmed paused/empty
through the final audit. The controller was reported off before GO and powered
on at the cue; the maintainer confirms normal input after completion. This is
a new scope after physical reinsertion failed to produce 100a; see
[the previous attempt and its limits](RF_LINK_CAPTURE_PLAN.md#approved-physical-return-attempt-administration-cleared-still-109c).

## Approved capture completed

The subsequent [offline payload and connection-witness review](RF_LINK_CONNECTION_WITNESS.md)
confirms XInput framing but finds eleven initial all-neutral reports and a
34.707839-second input gap. These are not a sufficient automatic RF-ready
witness. Four startup queries and separate HID/LED reports are now identified;
no production startup policy or installed code was changed. The metadata-only
section below records the earlier review, not the extent of the newer analysis.

After the refined read established the missing ordinary input consumer, the
maintainer opened KDE's controller test. A new approved read proved the exact
109c/xpad baseline and open consumer. usbmon was absent. A separately approved
operation repeated the read, checked the single current-kernel module plan,
loaded usbmon once and verified its dynamic registration and strict node metadata
without opening a monitor. Native remained paused/empty and the receiver/consumer
unchanged. No recording was started by that module operation.

The maintainer then approved one fresh preflight and capture. Fresh gates matched;
the visible terminal inherited its real stdin/stdout, waited for local GO and
then started the isolated recorder. The 30 s power-on cue, human confirmation
at 40.079 s, 60 s input cue, 80 s rest cue and 89 s finalization cue are retained
privately. The terminal exited 0; guest/host/descriptor/isolation and final
topology/pause audits passed. Twenty-four original recorder/parent checksum
entries were independently verified after completion. The original PCAPNG is
346,867,656 bytes and remains private, including unrelated whole-bus traffic.
There was one recording, no retry, Native Resume, driver-control or forced
mode/reset command. The maintainer confirmed visible KDE input during the run,
normal input afterward and a responsive desktop.

Importantly, power-on naturally ended the old 109c/xpad lifetime and created a
new 100a/xpad+usbhid lifetime at the same parent, with the receiver left plugged.
The recorder preserved separate device anchors/addresses; it did not adopt
ownership or force the transition. Final metadata proves Native pause and empty
ownership, with the new instance still on xpad. Do not silently resume Native.

The initial **file-only, metadata-only** review of selected addressed traffic is:

| Approximate host time from capture request | Observation |
| --- | --- |
| 30.053 s | Power-on cue; human power-on time is not measured directly. |
| 31.884 s | Old 109c EP82 completion: -108/ESHUTDOWN, zero data. |
| 33.403 s | First addressed USB record of the new 100a epoch. |
| 33.557 s | New instance host OUT submission at EP02, three bytes. |
| 33.569 s | First of two short HID EP84 completions (13 and 8 bytes). |
| 33.641 s | First successful 20-byte EP82 completion; 3,571 observed in total. |

The timestamp correlation uses USB wall-clock metadata against cue UTC/elapsed
time, not a physical RF clock. Separate cached enumeration anchors support the
epoch association; address alone is not individual-device identity. The ending
old -108 is not a new-session fault or proof that an earlier native bootstrap
failure has been reproduced. No successful input payload from the old 109c epoch
was observed in this recording; it had an ordinary input consumer already open.
No successful 64-byte EP82/84 completion was observed in the selected traffic.
Those facts do **not** establish a negative RF-status bit, a required Hello/ACK
order, global IMU absence or a working activation sequence. Payload-level
decoding and comparison remain separate offline research.

[Sanitized result, timings and proof limits](evidence/RF_LINK_109C_CAPTURE_20261020.json).
Only metadata/hashes are added to Git; original PCAPNG, identities, source copies,
terminal receipts and additional offline review/checksum chains remain private.

## Preflight diagnostics corrected offline

The one approved read with source commit `5949a46` returned exit 1 and:

```text
STOPPED CaptureHalt: Complete 109c/xpad baseline and ordinary input consumer required
```

Its stdout file is empty: the old helper raised before returning its report.
Original stderr, one-use authorization, exit receipt and verified checksums
are retained privately. They cannot establish which individual condition was
missing. Do not retrospectively claim that KDE was closed, the receiver was
absent or a specific attribute was missing. The consumed read is not retried.

The refined helper preserves a version-2 JSON report on both success and
failure, with nonzero exit status and `ok=false` on failure. It records the
first failed stage/type/message, original bounded manager command output,
completed checks, source pins and all cached observations collected so far.
Later stages remain explicitly `not_evaluated`; no missing observation becomes
a negative device finding or a permission to continue. Both snapshots survive
if the confirmation fails, with the exact differing nested field identified.
Authentication or interpreter failures before the helper starts remain external
errors: retain the caller's stderr/exit receipt, and do not invent a JSON report
or target observation for a helper that never ran.

Field diagnostics distinguish, for example:

| Diagnostic field | Meaning of the recorded observation |
| --- | --- |
| `device.present` | Receiver path missing, distinct from an incomplete attribute. |
| `device.devnum` | Attribute empty or missing, with error type/errno; later input inventory remains untested. |
| `interfaces.0.driver` | Expected xpad versus observed owner or temporarily unbound interface. |
| `interfaces.0.endpoints` | Expected EP02/82 versus the actual cached endpoint list. |
| `input.IF0.event_nodes` | No matching physical IF0 input node versus one or more known nodes. |
| `input.IF0.consumer_open` | A matching node exists, but no ordinary process holds it open; distinct from an incomplete FD inspection. |
| `process_access` | Inspection failed or was denied; not evidence of no consumer/raw access. |
| `manager.paused` / `manager.protected.leases` | Exact failed live-status or protected-state prerequisite. |
| `confirmation.identity.devnum` | Address changed between snapshots; the helper stops without adopting it. |

These are diagnostic examples, **not recovered observations of the old failed
run**. Report data can contain private host/process information and stays in
the private evidence directory. Only selected metadata fields are traced; no
process argument lists, serial numbers, input samples or firmware bytes are
added. Runtime snapshot schema, allowed instances, access guards, timeouts and
capture approval rules remain unchanged. Source pins change, so old prepared
manifests/approval plans must not be silently updated or reused.

`prepare` now requires explicit `ok=true` and absence of a failure. A valid
intermediate manifest inside a failed report cannot authorize preparation or
capture. A new live preflight still requires new approval and a fresh output
directory. No self-repair, retries, application launch or module load is added.

## Purpose and evidence boundaries

Compare the chronological sequence with the receiver already enumerated:
receiver/off baseline → reports around power-on → first ordinary gamepad
reports → first IMU-shaped reports, if any. Preserve unknown packets and actual
host OUT submissions as evidence; do not search only for a preferred status bit
or assume Hello is always first. A healthy ordinary xpad input stream with no
IMU proves neither an activation method nor a negative radio-status encoding.
109c is a GIP reference and must not be labelled 100a/XInput.

The recorder sends **no USB/controller commands itself** and opens no raw USB,
hidraw, evdev or native-control node. It passively observes usbmon through the
existing isolated dumpcap chain and reads cached host/process metadata. xpad
still performs its own ordinary initialization when an input client opens the
device. Opening KDE's test before recording may place that first initialization
outside the capture; do not compensate by replaying it or claim the capture
includes the entire USB enumeration. RF power-on is the planned observed edge.

Keep one ordinary KDE controller-test window open throughout, including while
the radio controller is off. It must hold an evdev descriptor belonging to the
exact receiver IF0. A name or bound xpad interface is insufficient. If no such
input device/client exists while off, this plan stops before capture and needs
review; it does not secretly open input or power on the controller. Steam,
games, Deadband and other raw-controller tools remain closed for this reference.
Do not require button presses to establish a receiver-off precondition.

## Timeline after local GO

| Capture time | Instruction |
| --- | --- |
| 0–30 s | Keep the controller **off**; preparation and receiver-only baseline. A heads-up is printed at 20 s. |
| 30–60 s | On **JETZT**, power on once. Do not press buttons or move sticks. When the LED indicates a connection, enter `VERBUNDEN` + Enter in the same terminal. |
| 60–80 s | Only after accepted connection confirmation: press A, move both sticks and gently rotate the controller. Observe normal input in KDE. |
| 80–90 s | Put the controller down; at 89 s begin controlled finalization, leaving one second reserve. No receiver or driver return command. |

`GO` is case insensitive and requires Enter. No password is entered into the
test's text input. The inherited terminal uses one unbuffered reader across GO
and confirmation; no alternate `/dev/tty`, pipe-to-sudo or buffered-input path.
`STOP`, Ctrl+C, EOF, a failed guard or a missed deadline aborts only the owned
recorder, retains the first error/evidence and never retries or resumes Native.
Confirmation before 30 s does not count; absence of confirmation at 60 s ends
the run without extending it. It is a human observation timestamp, **not proof
of the exact RF connection instant**. The packet chronology remains to analyze.

## Instance and isolation rules

The reviewed test scope is deliberately limited to the current primary-machine
bus 8, port 8-6, standard model 3537:109c, IF0 xpad/EP02+82, IF1 unbound/empty.
This is a test restriction, not hardcoded production driver discovery. A fresh
boot ID, USB device/parent lifetime anchors and actual address are mandatory.
No previously consumed approval or old metadata is a fresh capture baseline.

Every second the recorder checks pause/empty protected leases, absence of **all**
native bindings, no second supported receiver, ordinary IF0 consumer and no
foreign raw USB/hidraw/Deadband access. Inaccessible process descriptors fail
closed, including pseudo-FDs. Character-device `rdev` detects raw-node aliases.
No process argument lists or serial numbers are published.

An RF reconnect can re-enumerate USB despite the receiver staying plugged.
The full-bus capture has no fixed-address filter. At most four separately
logged lifetimes may appear at that same parent and boot, each with xpad IF0:
109c/unbound IF1 or 100a/usbhid IF1 with its known EP04+84. This observes a
natural PID change; it never requests one. No ZZZ/105e or foreign driver/port is
accepted. Address reuse with a new inode is a separate epoch; identity mutation
within one inode and return of an already retired epoch fail. Topology here is
only a temporary capture association, not proof of an individual device UID.

Missing metadata is **unknown**, not connected/disconnected. An already-started
run tolerates at most 2 s of incomplete metadata or 5 s of absence, measured
from the first unknown read; changing unknown kind cannot reset that deadline.
A complete target/consumer is required at both capture boundaries. Permission,
ownership, boot or parent faults are immediate failures. If the KDE consumer
does not reopen the replacement input instance in that window, stop rather
than interpreting silent input as a radio failure.

The existing private mount namespace, bubblewrap isolation, six namespaces,
zero capabilities/NoNewPrivs, usbmon-only device exposure, pidfd child identity,
2 GB capture bound, free-space guards, guest final audit and durable checksum
chain remain in use. Dumpcap's capture ceiling is 90 s, reap allowance 95 s,
outer recorder/observer timeout 120 s. No post-END motor tail is used. Host
metadata polling and userspace cues are not precise RF hardware timestamps.

## Proposed commands — not executed

Run from the project checkout. These Bash examples describe **separate approval
gates**, not a script to execute all at once. Use a fresh private directory once;
never overwrite an old report, manifest or capture. The test does not install
anything, load a module, unpause Native or change a binding.

First, after opening the KDE test while leaving the controller off, a new
approved read would collect live manager status, the protected empty paused
state, boot/USB/consumer/process metadata, executable provenance and monitor
node metadata. It does not open the monitor:

```bash
umask 077
mkdir -p build/hardware-tests
rf_run_dir=$(mktemp -d "$PWD/build/hardware-tests/rf-link-109c-xpad-90-XXXXXXXX")
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' \
  /usr/bin/python -B tools/native/rf_link_capture.py inspect \
  --authorize-read-only > "$rf_run_dir/preflight.json"
```

Stop if that command fails. Review the report before proceeding. If usbmon is
absent, `needs_separately_approved_usbmon` is true: **do not record**. Loading it
would be a separately disclosed/approved `/usr/bin/modprobe usbmon` followed by
fresh read checks; the helper has no such operation. An unexpected monitor
owner/mode/type also stops; do not chmod a device to bypass the guard. The full
dynamic monitor major/minor, mount and namespace checks repeat at recorder start.

Only from a successful reviewed fresh preflight, these commands read ordinary
project/evidence files and prepare/validate the pinned manifest:

```bash
/usr/bin/python -B tools/native/rf_link_capture.py prepare \
  --preflight "$rf_run_dir/preflight.json" --manifest "$rf_run_dir/capture-manifest.json"
/usr/bin/python -B tools/native/rf_link_capture.py validate \
  --manifest "$rf_run_dir/capture-manifest.json"
```

After **separate capture approval**, launch this single command in a visible
terminal using those exact reviewed absolute paths. Keep its stdin/stdout on
that terminal; do not pipe it or rely on shell variables from another terminal:

```bash
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A -p 'Password: ' \
  /usr/bin/python -B tools/native/rf_link_capture.py execute \
  --manifest "$rf_run_dir/capture-manifest.json" --output "$rf_run_dir" \
  --authorize-rf-capture
```

Enter GO only after the concrete approval and then wait for JETZT. Source,
dumpcap, instance and isolation checks repeat before verified readiness. No
automatic recorder start follows `inspect`, `prepare`, `validate` or import.

## Evidence and verification

Private output retains original PCAPNG, source pins/copies, actual dumpcap
provenance, namespace/descriptor audits, udev events, monotonic+UTC phase cues,
human connection confirmation and per-instance metadata JSONL. Finalization
fsyncs/closes streams and verifies nested and parent SHA256SUMS before returning
a completion receipt. The capture audit's `passed` describes recorder integrity,
not hardware behavior, gyro, or a proved radio-status packet. Failed recordings
retain the original fault plus separate stop/final-audit failures. Whole-bus raw
traffic can include unrelated inputs: keep these artifacts private. Publish
only reviewed, anonymized findings; no raw payload, private boot ID or host path.

After a future run, ask whether ordinary input remains normal; do not infer it
from usbmon audit success or automatically restore/release/Resume. Native stays
paused for this reference.

Original preparation checks: `python -B tests/test_rf_link_capture.py` exercises synthetic
topology/FDs, lifetime separation, unknown deadlines, strict manifests, input
consumer and raw-device guards, real local PTY input, virtual-clock phases,
one-shot abort/primary-fault preservation and final evidence checksums. Existing
450/300/90-second scopes keep their original gates. No test executes dumpcap,
udev, sudo, namespace setup, USB commands or a vendor application. Those tests
validate preparation; the later approved live result is documented separately
above and must not be inferred from unit-test success.

Initial validation checkpoint: 44 RF tests pass, followed by the complete `make
test` suite (exit 0; 1,313 Python test executions plus the existing C/adapter
and sanitizer checks). The legacy recorder and both 100a profiles pass their
unchanged regressions. Source/manifest diff and licensing are checked locally;
no capture result or fresh hardware-state claim is implied by those tests.

Diagnostic-correction checkpoint: 58 RF tests pass (14 added regressions), and
the complete `make test` suite passes again. Synthetic unknown/absent/consumer
alternatives reproduce the former combined gate without pretending to recover
its missing live snapshot. Tests cover exact expected/observed fields, raw
manager failure retention, incomplete inspection, JSON output on CLI failure,
skipped later reads, nested confirmation differences and refusal of failed
reports even when they contain a valid intermediate manifest. No live access,
capture, driver change, installed update or push in this correction.
