# Radio connection witness: offline chronology review

20 October 2026. Analysis of the one completed approved reference, not a new
recording or an implemented manager fix. Only retained regular files were read.
No hardware, network, SSH, privileged query, service or installed change.

## Result

Follow-up: the [focused PID-transition comparison](RF_PID_TRANSITION_COMPARISON.md)
tests whether the 109c->100a edge can supply the missing witness. One passive
power-on association and three software-return contexts do not establish a
sufficient RF-ready trigger. It recommends explicit receiver waiting without
changing the running kernel or manager.

**The capture proves a working XInput input path after power-on, but does not
identify a sufficient automatic, pre-button RF connection witness.** Eleven
initial reports are entirely neutral. They may be initial-state reports from
the receiver; they cannot by themselves distinguish a linked controller from
a receiver-generated neutral state. Later changed inputs, together with the
maintainer's confirmation, demonstrate actual controller operation in this run.
Do not make a changed button/stick value a production startup requirement.

An input channel can also be quiet for a long time without a proved disconnect.
Here the gap between the last neutral report and the first changed input is
**34.707839 seconds**. The human connection confirmation falls inside that gap.
There is no instructed power-off or continuous RF measurement in the gap.
Neither silence nor a neutral packet is an adequate universal RF-state test.

## Evidence and method

Original SHA256:
`dc5f5f2b2b68ed85a2162a591d6a50ddb1b5acb1ea60c7b2324153fd936a35bd`.
Recorder source was `a2522d3`; the preceding metadata review is `c431f4d`.
The original, whole-bus capture remains private and unchanged.

A separate USB_LINUX_MMAPPED reader was reused from the previous offline
chronology investigation. After rehashing the original, its 7,195 selected
records matched the independent `tshark -n -r` export for timestamps, endpoint,
transfer type, submission/completion stage, status and captured data length.
All 3,575 exported interrupt payloads matched byte for byte. USB addresses were
only selectors: retained descriptors and cached enumeration anchors establish
the two lifetimes. Old and new instances were never merged. A separate tshark
check matched all four startup-query setup packets. Private analysis scripts,
exports and checksum receipts are retained outside Git.

All times below are approximate host seconds from the recorder request,
correlated with cue UTC and elapsed times. They are not physical RF timestamps.

| Time | Frame | Observation |
| --- | ---: | --- |
| 30.053 | — | Power-on cue; exact human action time is not measured. |
| 31.884 | 15369 | Old `109c` EP82 ends with -108/ESHUTDOWN and no payload. |
| 33.403 | 16208 | First addressed USB record of the new `100a` lifetime. |
| 33.431 | 16243 | Full device descriptor for that new lifetime. |
| 33.557 | 16332 | EP02 `01 03 02` LED command submitted; completion succeeds. |
| 33.569 | 16341 / 16343 | Two short HID reports, IDs 3 and 9, with zero bodies. |
| Before first pad | 16380 | First vendor Control-IN startup query submitted. |
| 33.641 | 16381 | First successful 20-byte `00 14` XInput report; neutral. |
| After first pad | 16387 | First startup-query completion succeeds, 20 bytes. |
| 33.662 | 16399 | HID EP04 `03 01` LED output; completion succeeds. |
| 33.924 | 16546 | Last of eleven identical neutral XInput reports. |
| 40.079 | — | Human confirms visible connection, before input instructions. |
| 60.092 | — | Cue to press A, move sticks and gently move the controller. |
| 68.632 | 33528 | First non-neutral XInput report, including button/trigger fields. |
| 72.718 | 42526 | Last observed XInput report; no power-off cue followed. |

There are 3,571 successful, complete interrupt-IN reports on new `100a`/IF0
EP82. Every one is 20 bytes with the `00 14` XInput prefix. Eleven precede the
input cue and are identical, with all bytes after that prefix zero. The pinned
xpad `xpad360_process_packet` decoder agrees with the ordinary button, trigger
and stick layout; changing user input is observed only later. No ordinary
GIP Hello/status or native 64-byte IMU report was observed in these selected
interrupt completions. Later silence does not prove that the controller slept.

### Commands and short reports are not connection messages

The cached xpad reference is commit
`5fce161649b4d779d1b76d9fcd52dc77779774b8`, file SHA256
`19dd00fc4b0341ef18575a87b9b3fbd5f809e4588ff2909e2c357af2f2358517`.
`xpad_send_led_command` identifies the three-byte EP02 command as an LED
operation, not `xpad_inquiry_pad_presence` or GIP initialization.

Four vendor Control-IN requests have exactly
`bmRequestType=c1, bRequest=01, wValue=0100, wIndex=0000, wLength=20`.
Submission/completion frames are 16380/16387, 16390/16395, 16536/16541 and
16563/16570. All replies succeed with 20 bytes. This matches the setup used by
`xpad_start_input` and the existing Revision 13 adapter. Interrupt IN is already
pending; the first neutral report completes between the first query's
submission and completion. This is temporal association, not evidence that
the query is necessary or sufficient. No controlled no-query comparison is
available. The queries are observations of ordinary software during the
passive recording, not permission to replay them or introduce polling.

The captured 214-byte HID descriptor at frame 16339 separates report ID 3:
13-byte keyboard input / two-byte LED output, from ID 9: eight-byte input on
Generic Desktop/Button usage pages. The observed input bodies are zero;
neither is the native eight-byte GIP `03 20 seq 04` status. Thus the HID
`03 01` output belongs to the declared LED report, not a demonstrated sensor
enable. IDs 16 and 18 declare 64-byte vendor input reports, but declaring a
report does not prove it was sent or carries an active sensor stream.

## Comparison with earlier native starts

The [earlier four native enumeration sequences](DUALSENSE_STARTUP_GAMESCOPE.md#saved-capture-connection-chronology--20-october-2026)
show candidate GIP status/Hello → GIP pad → IMU, with 514.028–606.020 ms from
pad to IMU. In three starts initialization had already begun before the
candidate; a fifth, already-streaming capture begins with IMU before Hello
or pad. None establishes a mandatory pre-initialization RF message.

The new sequence instead is old `109c` removal → new `100a` enumeration →
ordinary HID/LED/startup-query traffic → neutral XInput burst → quiet interval
→ changed XInput input. It contains no corresponding native IMU phase.
Do not splice the historical native IMU timings onto this new run, treat HID
ID 3 as GIP status, or transfer the old lifetime's shutdown to the new one.
The initial `109c` input consumer was open before capture, so earlier xpad
initialization is outside this window. The natural re-enumeration with Native
paused does not prove a native bootstrap bug or its cause.

## Recommendation for the manager

Keep four distinct facts, scoped to the exact enumeration and ownership proof:

| Fact | Evidence in this reference | What it must not authorize |
| --- | --- | --- |
| Receiver identified | Exact descriptors and retained lifetime anchors | Claiming RF connection, transferring old ownership or starting repeated attempts |
| Input transport observed | Successful, correctly framed `100a` EP82 reports | Treating neutral initialization reports as a universal RF-connected bit |
| Actual input demonstrated in this run | Changed input after the cue plus human confirmation | Requiring a button press or nonzero stick value for future automatic startup |
| Native runtime ready | Not tested in this recording | Publishing sensors or declaring `gs_native` ready based on XInput/HID traffic |

The manager already uses terminal kernel bootstrap status and exact cross-FD
tokens; native READY requires successful initialization and fresh native IMU.
Preserve those gates. This reference offers no replacement for them and no
authority for a reset, repeat bootstrap, new lease or xpad round trip.

For a future fix, separate passive receiver waiting from a bounded, explicitly
started initialization attempt. An idle input channel must not alone consume
retry budget or become a terminal RF-disconnect decision. Keep last observed
input time as a timestamp, not a perpetual `connected=true` flag. Preserve
first transport/initialization errors and exact new-instance attestation.
The 34.7-second XInput gap is **not** a reason to weaken native IMU verification,
motor STOP/watchdogs, disconnect handling or cleanup authority.

**Open proof gap:** an unsolicited, sufficiently specific connection transition
before user input, or a separately validated native initialization/readiness
path that works without such a message. The neutral burst, short HID reports,
successful query replies, descriptor presence and old USB teardown do not close
that gap. Continue examining saved captures before proposing another test.

[Sanitized machine-readable findings](evidence/RF_LINK_WITNESS_20261020.json).
Validation: the 105 existing offline decoder/replay tests, seven public README
tests and three licensing tests pass. Additional file-only assertions verify
the new evidence's chronology, neutral count, gap arithmetic and negative proof
boundaries. The cached xpad file hash matches its pinned reference. No new
production decoder, connection gate or manager state machine is introduced.
No runtime code changed; Native remains last verified paused with empty
ownership. No current device state is inferred from this offline review.
