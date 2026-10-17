# Passive 100a HID sidechannel test — preparation only

Date: 2026-10-17. PRE-ALPHA. Recorder changes and tests are offline only.
The diagnostic work described below read existing manager state, journals and
cached sysfs. No capture, release/resume, module operation, driver binding,
USB command, application start or installed-file change was performed.
Gyro calibration remains paused. This document is not permission to run a test.

## Read-only manager diagnosis

The present `109c` instance is still bound to the native driver. The manager
has a matching **blocked** lease; it is not an unrelated record from a previous
boot. Boot identity, device and parent sysfs lifetimes, PID, bus/address and
driver all match the protected saved state. The installed manager's SHA256
matches the reviewed project source.

The actual failure sequence is now supported by the kernel and service journals:

1. The selected `100a` device was taken over and re-enumerated as `109c`.
2. Bootstrap reached `GS_BOOT_VERIFY` (`failed_stage=5`), following six completed
   initialization transfers. At failure: `step=6`, `pending=0`, `transition=1`,
   `tx_count=21`, `tx_status=0`, `tx_actual=64`, `tx_expected=64`.
3. The kernel reported `-110` (`ETIMEDOUT`), with no accepted GIP pad or IMU
   report during this attempt. The manager child itself did not time out.
   VERIFY requires a recent accepted IMU report; gamepad activity is not required.
   This supports a readiness timeout, rather than a USB OUT error or an
   incomplete mode transition. It does **not** explain why matching input was
   absent, prove zero USB traffic, or implicate a hardware defect.
4. The saved lease records `end_attempted=true` and `end_succeeded=true`.
   Roughly 30 seconds later the manager still observed `109c` and recorded
   `Return deadline: still 109c; manual attention required`.
   A successful END return value does not prove a return to `100a`.
5. The manager preserves this unresolved fault and performs no repeated END,
   speculative binding or restart. The original bootstrap error remains nested
   in `bootstrap_diagnostic`; the later return failure is separately visible.

The old `100a` address in `source_instance` is the provenance of the bootstrap
command across re-enumeration, not evidence of stale state by itself. A native
binding alone also does not establish an operational data stream: failed
bootstrap deliberately quiesces reception and neutralizes the input state.
No native control device was opened to obtain these findings.

[Sanitized evidence and source hashes](evidence/HID_PASSIVE_MANAGER_BLOCKADE_20261017.json)
are public-safe. Original protected state and journals stay outside Git with
private checksums. Serial numbers, hostnames, boot IDs and full device-lifetime tokens are
excluded from the public report. Packet-level evidence for this failed attempt
does not exist, so the cause of missing matching IN reports remains open.

## Required state before a future test

There is currently **no hardware Go**. The manager is unpaused with a blocked
lease, the device is `109c`, and usbmon is not loaded. The passive adapter must
reject this state before starting a recorder.

Recovery needs a separate, concrete authorization. Its intended sequence is:
checked manager pause/release; inspect the actual return; if needed, an explicitly
approved manual dongle removal/reinsertion; verify manager pause and empty
ownership, then confirm `100a`, IF0 `xpad`, IF1 `usbhid` and normal input.
Do not reset state files, call resume, guess a return packet or load modules
as part of this offline preparation. Missing usbmon requires its own later
module-load approval. The USB device's new address must not be guessed.

## Recorder separation

The old recorder is coupled to a 450-second native motor comparison and
`109c`/Deadband preparation. Its hardware coordinator must not be repurposed
for this passive test. The new entry point is
[`hid_sidechannel_capture.py`](../tools/native/hid_sidechannel_capture.py),
with the distinct scope `passive-hid-100a-300`.

It reuses the established isolation and finalization code in
[`native_usb_capture.py`](../tools/native/native_usb_capture.py), while keeping
the old profile's 450/480-second limits and 30-second tail separate.
No manager, native client, motor or binding operation belongs to the new entry
point. Source/asset hashes change with this adapter: old approved manifests are
not reusable, and offline regression success is not renewed hardware validation.

The passive profile requires a freshly checked standard-model `3537:100a`
instance with IF0 `xpad`/EP02+82 and IF1 `usbhid`/EP04+84. For this particular
hardware test it is deliberately restricted to bus 8, port `8-6`; that is not
a production-driver discovery rule. Device/parent lifetime anchors and boot
identity prevent reuse across enumeration or reboot. Saved manifest metadata
is not a substitute for immediate cached-state checks.

Before startup, periodically during capture and at completion, the guard
checks exact instance/bindings, paused manager with empty ownership, and
foreign target USB/hidraw handles. Unknown metadata or access-check failures
abort; they do not authorize a replacement device. The checks only read cached
metadata and process descriptors, never USB, HID or native control nodes.

## Isolation, storage and limits

- Only `/dev/usbmon8` is exposed to dumpcap. No `/dev/bus/usb` or hidraw node;
  no descriptor probing or vendor activation by the recorder.
- Preserve the outer private mount namespace, all six isolated namespaces,
  zero capability sets, `NoNewPrivs=1`, UID/GID maps and post-exec process checks.
- PCAPNG with `USB_LINUX_MMAPPED`, snaplen 0 and **at most 300 seconds**.
  The outer 330-second bound covers startup/cleanup; it does not extend capture.
- Output uses `-w -` into an already opened private regular file descriptor.
  There is **no writable output mount inside the sandbox**. The coordinator
  stores `original-usbmon8.pcapng`, cues, manifests and audits under a new
  mode-0700 `build/hardware-tests/<run>/usb-capture/` directory; files are 0600.
  This repository-local directory is persistent and ignored by Git, not a
  temporary-directory cleanup target. Existing evidence is never overwritten.
- Retain the 2-GB capture ceiling, bounded logs, disk checks, pinned process
  identity and capture-only stop. Errors preserve original data. No retry,
  driver recovery or module operation occurs automatically.
- After recorder exit, verify sandbox return, close/reap processes and compute
  and recheck SHA256SUMS. `-s0` requests full payloads but does not prove absence
  of capture losses; inspect capinfos, interface statistics and transfer lengths
  offline. Unavailable drop counters must be reported as unknown.

The standalone coordinator additionally writes parent-level `result.json` and
`SHA256SUMS`, covering its report, the inner checksum list and the exact returned
digest of `capture-outcome.json`. That outcome is written after the recorder's
inner SHA256SUMS. Completion requires the verified outer chain; `capture.passed`
alone describes only the recorder audit. Persistence errors fail the wrapper
without replacing the original cause or deleting evidence.

## Human-paced phases

After separate approval the visible terminal requires local **BEREIT**, ignoring
case, before any capture starts. The start cue follows verified recorder
readiness. Timing uses a recorded host monotonic capture-start origin, not
sensor time. Startup verification consumes a small part of the first 30-second
preparation window; the cue states the remaining preparation time. The final
second is reserved for a controlled stop, keeping capture within 300 seconds.

| Seconds from recorder request | Phase |
| --- | --- |
| 0–30 | Preparation |
| 30–50 | Rest |
| 50–80 | Normal buttons and D-pad |
| 80–110 | Sticks and analogue triggers |
| 110–135 | L4 only |
| 135–160 | R4 only |
| 160–185 | L5 only |
| 185–210 | R5 only |
| 210–240 | Paddle combinations and releases |
| 240–270 | Slow movement about each axis, no calibration |
| 270–299 | Final rest |
| 299–300 | Controlled capture closure reserve |

Action phases announce ten seconds of reaction buffer and a separate JETZT cue.
Recorded actual cue times, rather than an assumed perfect schedule or immediate
human response, delimit evaluation windows. No motor test is included.

## Offline preparation commands

From the repository root, these commands only inspect files or use fake backends:

```sh
python -B tools/native/hid_sidechannel_capture.py show-plan
python -B tests/test_hid_sidechannel_capture.py
python -B tests/test_native_usb_capture.py
make test
```

A later approved manifest contains the exact freshly checked target and dumpcap
metadata plus source hashes. It can be checked without starting anything:

```sh
python -B tools/native/hid_sidechannel_capture.py validate \
  --manifest "$GS_HID_RUN/approved-manifest.json"
```

Only after recovery, fresh checks and **new capture authorization**, the proposed
visible-terminal invocation is:

```sh
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A \
  /usr/bin/python -B tools/native/hid_sidechannel_capture.py execute \
  --manifest "$GS_HID_RUN/approved-manifest.json" \
  --output "$GS_HID_RUN" --authorize-passive-capture
```

`GS_HID_RUN` must designate a new, reviewed, private run directory beneath
this checkout's `build/hardware-tests/`. No current approved hardware manifest
was created, no capture command above was run, and the source flag is not user
authorization. End-of-test release/resume remains outside this adapter.

## Evaluation boundary

Keep full bus traffic private. Extract only the target's confirmed enumeration
epoch, including submissions/completions and endpoint 0; then inspect EP82
and EP84 separately with the existing offline HID prototype. Address alone is
not durable identity. Re-enumeration invalidates the planned measurement.

Existing IF1 reports can establish observations under XInput, not an activation
mechanism. Report `12` stays unknown; brief post-transition bursts do not prove
fresh continuous IMU data. No `0f f2`, HID SET_REPORT, sensor scaling or motor
parity is enabled by this adapter. See [offline findings](XPAD_HID_PROTOTYPE.md).

## Offline validation result

The completed revision passed **46 new passive-adapter tests** and all
**34 existing recorder tests**. `make test` passed **920 Python test cases in
32 batches**, plus the existing C, sanitizer and static checks. The new tests
use synthetic processes, virtual clocks and in-memory metadata backends;
no sandbox, usbmon, live USB interface or installed manager was exercised.

Covered cases include profile/time separation, known identity/bindings and
boot/device/parent lifetimes, manager pause/ownership, unknown metadata,
foreign descriptor aliases, explicit approval/readiness, reaction buffers,
periodic and final identity failures, bounded ordinary-file manifests,
capture aborts, original-error preservation and durable result checksums.
The independent source review's alias-detection and standalone-result-chain
findings were corrected and regression-tested. Original setup/mount and
usbmon-node guards remain byte-identical; changed assets retain historical
hashes and explicitly mark the passive variant as hardware-unvalidated.

Manager and kernel source hashes still match the read-only diagnostic snapshot.
No runtime correction was installed, no fault latch was cleared and no new
hardware test is implied by these software results.
