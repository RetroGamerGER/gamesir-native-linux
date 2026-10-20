# Passive startup timeline prototype

20 October 2026. Offline research only, GPL-2.0-only own implementation.
No third-party source was copied. Protocol provenance and pinned references:
[Microsoft GIPUSB, xone, SDL and saved GameSir chronologies](DUALSENSE_STARTUP_GAMESCOPE.md#online-gip-sequence-cross-check--20-october-2026).

## Purpose and boundary

`tools/offline/gamesir_offline/startup_timeline.py` models observations of one
native receiver lifetime. It is **not** a correction installed in the manager
or kernel. No transport, command generator, retry loop, timer thread, USB alias,
state-file migration, input publication or motor handling was added. Existing
bootstrap, ownership, STOP/error guards and runtime decoders are unchanged.
This establishes an executable hypothesis, not proof that the radio-off boot
blocker is fixed. The last inspected target was blocked; the maintainer now
reports controller off/dongle plugged, without a new target inspection here.

## Observations, not an invented connection bit

| Observation | Model behavior |
| --- | --- |
| Receiver metadata / explicit test `attach` | Wait; neither RF connection nor a three-second bootstrap failure follows |
| Complete native GIP Hello | Announced; at most one announce-led start **candidate** per epoch, no output command |
| Captured START submission | Record an existing host attempt; not a successful transfer, acknowledgement or generated request |
| Type-03 status, bit 7 set | Positive candidate only; neither stream ready nor permission to start |
| Native pad / IMU | Track separately; either may arrive first without Hello or START in the recorded window |
| Observation age exceeds replay policy | Expire each channel independently; no RF-off conclusion, retry or error |
| New Hello after data, or bit 7 clear | Quarantine as uncertain; never adopt a new controller generation silently |
| Transport error / clock regression | Preserve first error; terminal for that epoch |
| Explicit test detach / cancel | Terminal; later records cannot revive that epoch |

The default three-second observation-age window is an **explicit replay
policy**, not a measured sample period or the existing kernel VERIFY timeout.
It causes no timed command or failure. Data silence can mean idle gamepad,
partial capture, suspended host or RF loss. This model cannot distinguish them.
Status is never a gate before START. A status packet is not an initialization
ACK. A repeated Hello/START in saved data is counted, not permission to resend.

The checked upstream xpad reference makes the same important distinction:
in `xpadone_process_packet()`, ANNOUNCE triggers `xpad_start_input()` only if
`delay_init` is set and `delayed_init_done` is false. It sets that flag before
the call, so another Hello is not an unconditional retry even if the call
fails. `xpad_resume()` resets it on USB resume. A new probe starts with a new
object. In this pinned source, `FLAG_DELAY_INIT` is assigned to ByoWave Proteus,
not G7 Pro. The comment explains that some receivers discard initialization
before the controller connects. This is a reference pattern, not authorization
to add that quirk to GameSir or claim that xpad restarts on every Hello.
[Pinned xpad reference](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c).

Output phases say `pad_only_observed`, `imu_only_observed` or
`pad_and_imu_observed`, never healthy runtime or recovered ownership. The
`rf_connected_proven`, `runtime_ready_proven` and ownership/recovery flags remain
false. A fresh report alone cannot grant a native lease or authorize publication.
The model does not implement the eventual production startup/cleanup deadlines,
administrative budget, resume logic or link-loss STOP. Those existing guards
must remain in the runtime when an integration is separately designed.

## Input, lifetime and privacy

The new `startup-replay` subcommand uses the existing strict saved JSONL reader:
regular files only, bounded lines/records, duplicate keys rejected, and no
`/dev`, `/proc`, `/sys`, FIFO or live transport. It accepts only `3537:109c`,
IF0 IN82/OUT02. `100a` IF1/HID telemetry and untested ZZZ routes cannot become
native connection evidence. Complete input success, exact lengths and supported
Hello/Status framing are required; embedded Hello VID/PID must match metadata.

Records remain in file order. Source kind/ID, timebase, session, VID/PID, bus,
address and interface isolate each instance; IN/OUT of that instance join.
`session` MUST name one boot/enumeration lifetime, including address reuse. A
new boot, re-enumeration or uncertain source must not reuse an old session key.
There is no automatic inference of physical port, ownership or individual UID.
The raw-file CLI only implies receiver presence from first packet metadata;
it does not invent descriptor/physical-insertion timing. Explicit attach,
tick, detach, cancel and fault events are available through the pure model for
unit tests, not inferred from empty transfers or an end-of-file.

Reports omit all payloads, Hello IDs/MACs, firmware strings, sensor samples and
button values. Input metadata may still be private: review it before publishing
a generated report. Original captures and private validation stay outside Git.

## Reproduce without a controller

From `tools/offline`:

```sh
python -B -m unittest discover -s tests -v
python -B -m gamesir_offline startup-replay fixtures/synthetic_startup.jsonl --events --strict
```

The JSONL example is **entirely synthetic**, including its Hello ID and timing.
`--freshness-us` selects an observation-age policy in 1..60,000,000 microseconds.
`--pid`, `--bus` and `--address` filter saved metadata only. Exit 2 means invalid
file/schema/options; strict exit 1 means malformed/truncated packets or terminal
model errors. Waiting/unknown status is not a strict-mode failure. No command
is sent regardless of the exit code or candidate count.

`fixtures/startup_chronology.json` separately contains **capture-derived event
metadata**: original SHA256, frame, relative host time and interpreted event
kind. It contains no raw payload or user identifier. Cases A–D preserve four
measured native enumeration sequences; B retains START before Hello and a later
START after it, D preserves the 45-microsecond Hello-to-START interval. The fifth
case starts with IMU, without Hello. Expected classifications/times were taken
from the independently checked historical evidence, not generated by the model.

These are selected events, not complete cadence. In the fifth case IMU at
capture start has expired under the explicit policy by the selected pad event
39.7 seconds later. The model correctly reports pad-only for that excerpt;
this is **not** proof that the real IMU stopped or dropped packets.

## Validation and next step

Thirty new unit tests cover waiting for a day, delayed/no-button announce,
duplicates, status without START, START without status, separate freshness,
already-running IMU, uncertain generations, negative-bit hypothesis, transfer
failure, preserved original error, cancellation/detachment, clock regression,
instance isolation, rejected routes/framing, regular-file guards, strict CLI
and the five measured metadata timelines.
The complete file-tool suite passes 105 tests; seven public documentation and
three licensing checks also pass. No module build is needed for this file-only
change; kernel/manager sources and installed packages remain untouched.

An additional private replay classified 23 saved **original packet payloads**
from those five historical cases and checked the published event labels and
final phases. No vendor payload was added to Git. Those checks are historical
positive coverage, not a new hardware measurement or radio-off/on contrast.

Next: review the observation contract before integrating it. A separately
approved receiver-off → late radio-on trace or equivalent direct evidence is
still needed to validate the start trigger/negative state. In particular,
uncertain link state and a previously failed instance must not be promoted or
automatically retried just to pass a hardware test. No system installation,
manager/kernel change, new recording or push is authorized by this prototype.
