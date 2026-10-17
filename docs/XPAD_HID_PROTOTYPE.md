# XInput/HID companion: offline activation review and prototype

Date: 2026-10-17. **File-only experiment**, not a replacement kernel driver.
No hardware access, new capture, application execution, SSH, privileged command,
module/binding change, installation or push. Gyro calibration remains paused.
The working native runtime and its existing transport restrictions are unchanged.

## Result

The saved ordinary-G7-Pro traffic supports investigating a companion to xpad:
`3537:100a` IF0/IN `82` carries normal XInput, while IF1/IN `84` can carry a
64-byte report with the known `10/3c/e0` telemetry shape. **Activation of a
continuous IF1 stream is still unproven.** The prototype can inspect those saved
channels together, but has no command sender or live backend.

The expanded review covers eight original captures. Fourteen matching IF1
reports occur in three post-`109c` return epochs; the earlier review covered
the first two epochs and three reports. These counts describe the same evidence
at different coverage levels, not conflicting measurements.

| Return epoch | Successful telemetry reports | First-to-last report span | Remaining capture after last telemetry (no further telemetry reports) | Keyboard LED submission after first telemetry |
| --- | ---: | ---: | ---: | ---: |
| Oct 11, Deadband measurement | 1 | 0 ms (single report) | 26.571399 s | 107.855 ms |
| Oct 12, Deadband motor comparison | 2 | 1.000 ms | 30.037689 s | 109.335 ms |
| Oct 12, native motor comparison | 11 | 10.001 ms | 26.834705 s | 90.779 ms |

Those short bursts do not establish sustained telemetry, fresh sensor acquisition
or physical paddle mapping in `100a`. Fresh IN submissions and completions belong
to the new USB enumeration; firmware-internal samples queued before the return
remain possible. Arrival intervals near 1 ms are not a sensor-rate proof.

The [sanitized evidence index](evidence/XPAD_HID_ACTIVATION_REVIEW_20261017.json)
records all eight original SHA256 hashes, coverage, generic descriptor and
original frame references. Full bus captures and machine-specific attribution
remain private. The earlier [two-capture review](XPAD_HID_FEASIBILITY.md) is
retained with its original frame-number domain and derived-export hashes.

## Activation: what was and was not found

No IF1 `0f f2` submission or HID `SET_REPORT` targeting IF1 was found in the
eight inspected captures. Some capture windows start after initial enumeration;
absence there does not prove an unsupported command. Three fully recorded return
epochs nevertheless contain no host vendor activation before their short bursts.

The only observed IF1 OUT payload in those epochs is **`03 01`**, a two-byte
keyboard LED report declared by the generic descriptor. Each submission has a
matched successful completion in the original URB record. All three submissions
follow their telemetry burst, so they cannot have activated the preceding reports.
The public fixture retains their actual **submission** stage, without manufacturing
a completion payload.

Keep these three different byte sequences separate:

| Saved/reference sequence | Transport/context | Interpretation |
| --- | --- | --- |
| `03 01` | Ordinary model, IF1 OUT `04` | Observed keyboard LED output; no vendor activation |
| `0f 00 SEQ 02 f2 00…` (64 bytes) | Existing extended native/Deadband path, IF0 OUT `02` | Framed GameSir heartbeat; not evidence it works over IF1 or in normal `100a` |
| `0f f2` followed by 62 zeros | Pinned PandaPro8K reader, different PIDs | 8K HID heartbeat candidate; not captured or validated on our ordinary model |

The pinned Deadband code also contains a plain `0f f2` enhanced reader for
Cyclone 2. Its G7 USB session instead uses the framed IF0 path. Neither is an
ordinary-G7-Pro IF1 activation contract. References/revisions remain in
[the feasibility review](XPAD_HID_FEASIBILITY.md) and existing protocol sources.

The IF1 descriptor declares IN reports `10`/`12` and OUT `0f`, all 64 bytes
including report ID. It proves syntax/capability declaration, not semantics.
No actual report `12` was observed. The prototype never decodes it using 8K
offsets and never constructs, schedules or transmits an activation packet.
Recognizing an already saved exact 8K heartbeat only yields `candidate`, even
if its supplied metadata describes a successful transfer; activation stays false.
Record schema 1 contains no URB ID or setup fields, so any OUT pairing must be
independently documented against the original capture. The prototype does not
infer such pairing from adjacent records.

## Run the prototype without a device

Python 3.10+ and its standard library suffice. From the repository root:

```bash
cd tools/offline
python -B -m gamesir_offline hid-replay fixtures/captured_hid_returns.jsonl --strict
python -B -m gamesir_offline hid-replay fixtures/synthetic_hid_companion.jsonl --events --strict
```

The first file has **14 original telemetry payloads plus 3 keyboard LED
submissions**, each with hash/frame provenance in the evidence index. Payload
bytes are unchanged. Timestamps are rebased separately to the first telemetry
completion of each return epoch. Bus 1/address 1 are anonymized placeholder
labels, not observed topology or a device identifier. Separate source/session
keys preserve the three enumeration epochs; never merge them into a live instance.
The excerpt excludes normal-input packets and the full quiet tails: the complete
capture audit, rather than the small replay file, supplies those observations.

The second file is **entirely synthetic**: two 16-bit XInput samples, tentative
extra-field press/release, a deliberate stale-HID gap and an unknown `12` report.
Its button changes demonstrate software behavior only, not physical assignments.

Implementation: [hid_companion.py](../tools/offline/gamesir_offline/hid_companion.py).

- Accept only `3537:100a`, normal IF0/`82`, raw HID IF1/`84` and saved IF1/`04`.
  ZZZ and 8K identities are not silently enabled by this experiment.
- Reuse our existing byte decoder for the observed `10/3c/e0` shape; preserve
  six raw channels and label the known-layout paddle names unverified on `100a`.
  Vendor 8-bit stick fields never replace the normal signed 16-bit axes.
- Group by source kind/ID, explicit enumeration session, timebase, VID/PID,
  bus and address; retain independent channel timestamps and cadence. Reused
  addresses require a new session in normalized input. Metadata is asserted by
  the importer, not authenticated by the parser.
- Show separate last observations, never an atomic combined sample. The default
  100-ms display-age policy clears stale channels; `--max-age-us` permits
  1–1,000,000 us. This is not a measured sampling or transport threshold.
  Cross-channel timestamp regression quarantines composition for that instance.
- Failed/truncated/malformed channel records cannot supply a valid observation;
  normal URB submissions do not erase a previously completed sample.
- Keep `activation_proven`, `readiness_proven`, `continuous_stream_proven`,
  `paddle_layout_100a_verified` and `motor_support_proven` false. No evdev/uinput
  emission, USB ownership or sensor calibration follows from replay.

The CLI accepts existing regular files only and rejects special paths,
device files and FIFOs. There is no `--live` or `--send` mode. `--events` redacts
recognized keyboard/mouse/consumer payloads and unrelated identities/channels.
Remaining target-protocol bytes and user-supplied metadata can still be private;
do not publish a broad event export without reviewing it. Default output is
aggregate observations. `--strict` exits 1 on malformed/truncated selected
records; input-file/schema errors exit 2. Unknown formats stay unknown.
The existing `replay` command continues rejecting IF1.

## Path toward a smaller driver

The prototype establishes an independent decoder/state boundary for a possible
HID companion while leaving xpad responsible for normal inputs. It does not yet
prove a Linux hardware implementation. Before implementing an active transport:

1. Establish an ordinary-model activation contract from actual reviewed source
   or separately approved, bounded measurements. Do not substitute a command
   from an 8K/Cyclone/extended-runtime path merely because report IDs match.
2. Verify sustained `84` telemetry alongside normal `82`, then separately test
   all four physical buttons, releases, simultaneous presses and reconnect.
   Descriptor similarity and residual IMU packets are insufficient.
3. Design an opt-in HID vendor collection handler preserving keyboard/mouse
   collections. Associate it through the same USB parent and enumeration lifetime;
   a global VID/PID or fixed port is insufficient. Agree on one logical gamepad:
   a second input node alone will not give xpad four more application buttons.
4. Resolve output ownership and independent stops before replacing any proven
   four-motor path. Neither this reader nor xpad's two-channel rumble establishes
   equivalent trigger control over IF1. Recheck games/API limits independently.

**Go:** continue file-based protocol and architecture work. **No-Go:** activate
the 8K heartbeat, replace the installed driver, or claim continuous paddles/IMU
or four-motor parity from the current evidence. A hardware test needs its own
concrete plan and approval; attaching a controller is unnecessary for this stage.

## Validation and provenance

All new executable code is our own GPL-2.0-only Python, reusing our existing
payload decoder. No Panda/Deadband/g7ctl modules or source code were copied,
imported or executed. Small owned-device protocol excerpts contain no serial strings,
personal paths, other-device traffic or full captures. Their unknown bytes are
not interpreted as identifiers, calibration or device clocks.

Run `make test-parser` for the file parser, CLI, identity/privacy guards and
recorded-excerpt tests; run `make test` for the complete offline regressions.
Tests cover signed axes/raw sensors, unknown formats, submits/errors/truncation,
source/epoch separation, stale observations, clock regression, candidate padding,
keyboard/foreign-payload redaction and unchanged legacy transport gates.
Validation on this revision: **75 parser tests**, including 31 new tests;
`make test` passed **874 Python cases in 31 batches**, plus the existing C,
sanitizer and static checks. No kernel source changed or module was loaded.
These checks validate software behavior, not the proposed live HID transport.
