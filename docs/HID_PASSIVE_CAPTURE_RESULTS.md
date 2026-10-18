# Passive 100a HID smoke test — 18 October 2026

PRE-ALPHA. Two separately approved, bounded recordings completed using source
commit `29b3f8f`. **Normal XInput was confirmed in the second run; vendor HID
telemetry for IMU/additional-button decoding was not observed.** Neither run
authorizes another capture or any change to the installed driver.

## Scope and retained state

Standard G7 Pro, VID `3537`, PID `100a`, IF0 `xpad`, IF1 `usbhid`, on the freshly
checked test instance. Kernel `7.2.11-1-garuda`; dumpcap `4.7.4`, PCAPNG,
`USB_LINUX_MMAPPED` linktype 220, host timestamps at microsecond precision.
Both fresh process-access checks passed. usbmon was loaded exactly once under
approval, before the first recording; it was already present for the second.

The isolated recorder exposed only `/dev/usbmon8`, with no raw USB or hidraw
nodes. All six namespaces differed from the host; all five capability sets
were zero after dumpcap exec, with `NoNewPrivs=1`. Final audits passed: recorder
processes reaped, monitor handle closed, host mount/namespace/node metadata
unchanged, same target lifetime/identity/bindings and paused empty manager.

No resume, driver rebind, identity change, native module operation, motor test,
manufacturer application or firmware access was performed. usbmon remains
loaded; no unapproved module unload or automatic recovery followed. Normal
inputs in the open KDE test were confirmed by the maintainer before, during
and after the second run. The device remained `100a` with `xpad`/`usbhid`.

## Why the first run was insufficient

Run 005 completed its recorder audit but contained no EP82 XInput traffic.
The maintainer clarified that the KDE controller test was not open. The earlier
combined response about normal inputs therefore does not establish visible KDE
events during that first recording.

The existing local Linux 7.2.9 `drivers/input/joystick/xpad.c` reference registers
`xpad_open`/`xpad_close` for non-XBOX360W input devices. Open calls
`xpad_start_input`, which submits the IN URB; close kills it. This provides a
plausible explanation for missing traffic with no input consumer. The exact
running 7.2.11 source and historical open handles were not attested, so it is
not a conclusive reconstruction of run 005.

After a new explicit approval, run 006 added a fresh read-only check for an
open ordinary input handle belonging to the exact target IF0. One consumer
was found; the maintainer confirmed visible A/stick inputs and kept the KDE
test open throughout. No raw-device opening, replayed initialization command,
driver change or extra module load was used to remedy the prerequisite.

## Measured results

| Observation | Run 005 | Run 006, with verified input consumer |
| --- | ---: | ---: |
| All bus USB events | 55,956 | 70,262 |
| Target events, submissions plus completions | 32 | 21,614 |
| Successful EP82 input completions | 0 | 10,787 |
| EP82 payload length | None | 20 bytes |
| Successful EP84 input completions | 16 | 20 |
| EP84 payload | 13-byte report `03` | 13-byte report `03` |
| Known 64-byte `10/3c/e0` telemetry | 0 | 0 |
| Report `12` | 0 | 0 |
| Target failed completions or error events | 0 | 0 |
| Packet timestamp span | 88.912305 s | 88.975048 s |

Each successful target completion was followed by a new submission with
status `-115` (`EINPROGRESS`); that submission status is not a failed transfer.
Pending submissions at window boundaries are not counted as lost samples.
There were no target control or output transfers in these capture windows.
Short report03 payload contents remain private: they are other HID collection
data, not a demonstrated vendor sensor/paddle stream.

The streaming USB_LINUX_MMAPPED parser and independent TShark target metadata
agree. The existing strict HID replay accepts all 21,614 normalized target
records in run 006: 10,787 decoded `x360_input`, 10,807 ignored submissions and
20 `hid_nonvendor_ignored` completions. Both analog triggers span 0–255; each
of the four stick axes spans −32768–32767. Eleven named normal button bits
were exercised. D-pad activity was not observed, so this is not an all-controls
acceptance test. The mixed phase also cannot establish physical paddle mapping.

There were still 2,693 EP82 and six EP84 completions in run 006's final-rest
window. Treat that as recorded continued activity/reaction time, not a clean
rest, sensor calibration or stick-centering measurement.

## Intervals and completeness

Run 006 has 10,786 positive EP82 completion intervals. Median: **1.000 ms**;
p95: 2.000 ms; p99: 44.991 ms. **93.73%** fall within 0.9–1.1 ms. Minimum:
0.774 ms; maximum: 1,778.038 ms. Activity gaps are included. These are host USB
completion intervals, not guaranteed controller polling, RF/sample rate,
sample freshness or end-to-end latency. No universal 1000-Hz claim follows.

No captured frame or target payload was truncated. PCAPNG statistics report
`ifrecv=55956/70262` and `ifdrop=0` for the respective runs; dumpcap also reports
zero drops. `osdrop` is absent/unknown. This is not a guarantee that every
possible upstream loss is measurable. The 90-second limit included the final
one-second closure reserve, explaining packet spans just under 89 seconds.

## Storage and integrity

Both original captures remain unchanged, private and persistent under
`build/hardware-tests/<run>/usb-capture/original-usbmon8.pcapng`. Parent run
directories are 0700 and recorder files 0600. Neither originals nor nonvendor
HID payloads, host IDs or process details belong in Git. Target-only JSONL,
analysis scripts, independent TShark metadata, parser output and their checksums
remain in each private `derived/` directory.

| Original | Bytes | SHA256 |
| --- | ---: | --- |
| Run 005 | 350,452,008 | `6c93e41d81fe50bd6d6f92a52a7605cc9659a9323a656be506d0024e96af21ce` |
| Run 006 | 351,350,096 | `85cc7d24dc98069e345348cfddf6f2ecefd3de2e7241f7a600a458be046ca125` |

Each run's 22 inner/outer checksum entries were verified, including its exact
capture-outcome receipt. Derived outputs have separate verified checksums;
analyses do not alter the original recorder checksum chain. Public-safe
aggregates and source receipts are in
[the sanitized evidence](evidence/HID_PASSIVE_90_RESULTS_20261018.json).
After documentation/provenance updates, all 34 recorder regressions, seven
public-README checks and three licensing checks passed. Recorder/runtime source
files are unchanged from the tested commit; no module rebuild was needed.

## Decision and next boundary

Recorder/isolation/finalization: passed within these approved runs. Concurrent
normal XInput plus short HID traffic: established in run 006. Passive vendor
IMU/additional-button telemetry: **not established**. This does not prove that
no activation contract exists or justify copying the different 8K model's
heartbeat into the standard G7 Pro.

Further work should first compare saved protocol evidence offline. Any future
capture requires fresh authorization, target/process checks, and a verified
ordinary input consumer kept open throughout. No automatic repeats, release,
resume, recovery or replacement of the native architecture follow from this
result. Gyro calibration remains paused.
