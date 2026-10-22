# TMR: native owner interface, prepared offline

**Current follow-up:** The [scoped GUI and permission path](CONTROL_CENTER_TMR_PERMISSION.md)
is now implemented and tested offline. It has a distinct explicit continuity
contract; it does not attest physical RF lifetime. The normal app, published
AppImage, installed driver and default-off kernel feature remain unchanged.
The historical implementation scope below is retained for provenance.

**Static follow-up:** [USB framing and dongle ingress](TMR_USB_FRAMING.md) now
trace endpoint2, configured64, actual receive length and unchanged queue copy.
The existing packet is receiver-backed as a Linux reconstruction; Windows'
exact USB output remains unobserved. No kernel/manager/GUI source changes or
activation were made by that follow-up; the interface remains default disabled.

22 October 2026. [Validation receipt](evidence/TMR_NATIVE_INTERFACE_20261022.json).
Continuation of the [controller adapter](CONTROL_CENTER_CALIBRATION_ADAPTER.md)
and [provider/transport research](NEXUS_STICK_TRANSPORT.md).

## Status

Kernel and manager now implement a narrow, experimental maintenance interface
for the standard `109c` and ZZZ `105e` native instances. This is an **offline
implementation**, not a successful hardware calibration. `experimental_tmr`
defaults to false and is read-only after loading. No service, installer,
modprobe default, privilege helper, normal GUI or published AppImage enables it.
No installation, activation, firmware execution, device or network access took
place. Existing installed driver behavior and precision gyro pause are preserved.

The known internal messages are Start `fe 00 03`, Finish `fe 01 00`, Exit
`fe 02 00`, type `0f`. Their values come from the locally analyzed Nexus path;
no vendor code/assets are copied. Own implementation is GPL-2.0-only, with the
existing Linux-syscall-note exception retained in the UAPI.

**Wire limitation:** the new kernel packet builder is a test candidate:
`0f 00 seq 03 fe operation parts`, zero-padded to 64 bytes on the existing
native OUT endpoint. Length three follows short GIP framing; OUT64 and zero
options follow the existing vendor transport and firmware parser. The complete
Windows-provider USB frame, padding and acknowledgement behavior have **not**
been captured for calibration. A synthetic byte comparison verifies our
implementation, not device acceptance. Separate approval and packet/target
validation are required before enabling this candidate. No success claim or
unconfirmed capability is advertised to the existing GUI adapter.

## Kernel contract

Additive ABI1 commands, preserving all older struct sizes/command numbers:

| Command | Scope |
|---|---|
| `GSN_TMR_GET`, `0x7b`, 144-byte status | Latest complete E0 and genuine RX metadata; never renews a lease |
| `GSN_TMR_COMMAND`, `0x7c`, 48-byte request | Only Acquire, Start, Finish, Exit, Release and Renew |

Both require CAP_SYS_ADMIN and the existing exclusive native control FD.
The experimental opt-in additionally requires persistent running native output
and an active normal session. No xpad detach, bootstrap, mode change, general
packet, endpoint selection, register or calibration-value write is exposed.
Requests bind exact nonzero kernel port/instance tokens, stream epoch and a
nonzero fixed run generation. ABI/reserved fields and operation ranges are
checked. Wrong target, stale identity or another operation's FD is rejected.

Start consumes phase `leased -> started` before submission. Finish and Exit
consume `started -> finished/exited` before submission. Only a current E0 with
both low active and done bits set permits Finish; other calibration-part bits
are rejected. Start refuses an already active calibration. Duplicate or
out-of-order commands cannot send a second packet. Renew and local Release
never produce USB traffic. Release is not an Exit or storage undo.

The ordinary USB output mutex, sequence allocation, DMA buffer and bounded
transfer are reused. A final send gate checks the maintenance lease/error as
well as ordinary output/session state. Failures and short transfers preserve
the first cause and cannot replay the command. A successful immediate transfer
does not mean an independently read-back nonvolatile record. No invented
storage ACK is required. Firmware remains responsible for computing/storing
the values after Finish.

Close after a TMR getter or acquisition drops only maintenance ownership; it
does not stop normal input or send a motor-zero packet. The FD cannot then
perform Pulse, Stop, End, Resume, StartSession, Bootstrap or PublishInput.
Normal legacy control-FD close behavior is unchanged. Quiesce/PM/disconnect and
fault invalidate telemetry and any current maintenance run. Closing or locally
releasing an unfinished Start latches cancellation; unsafe/failed runs are not
silently cleared for a new calibration on the same binding. Recover that
condition deliberately in a later approved step, never by automatic Resume.

## Reports and lifetime: bounded evidence

The TMR snapshot accepts exactly 64-byte `10 00 seq 3c e0 ...` reports.
The full frame stays unchanged, including processed stick bytes 5–8, raw
bytes 51–54, active byte30 and done byte31. No positions are normalized in the
kernel; the separate GUI display policy owns that transformation.

Each accepted RX records host monotonic nanoseconds and a local increasing
report count, independently of the wrapping device sequence. A snapshot is
**not a lossless queue**. A reader can see report-number gaps and knows it
skipped snapshots; it cannot infer RF packet loss from them. Polling/renewal
never fabricates RX timestamps or another report. IIO/evdev/IMU math and input
mapping remain separate.

The conservative freshness bound is 1.5 seconds; the renewable client lease is
two seconds. Clock regression, silence, PM or changed native object invalidates
the old run, even if another report later arrives. The stream epoch prevents
joining across an observed gap on unchanged USB tokens. This remains a
**continuity guard, not proven physical RF identity**: a reconnect shorter than
the gap bound may be invisible. E0 may be change-only, so a stationary device
could also hit the conservative bound. These limits must be assessed before
live GUI integration, without pretending that neutral input proves a link or
letting polling refresh old telemetry. The strict GUI Channel capability/RF
contract from the earlier adapter is therefore not yet automatically satisfied.

## Manager boundary

The protected root-only control socket accepts one newline-terminated JSON
request, at most 2048 bytes. Existing plain status/release/resume remain
supported. Peer credentials are checked before parsing or opening a device.
There is no new unprivileged group, Polkit rule, GUI flag or haptics permission.
Permission-helper wiring remains a separate step.

Example **request shapes only**, not instructions to run against hardware:

```json
{"version":1,"tmr":"probe","port":"2-3","port_token":11,"instance_token":22}
{"version":1,"tmr":"acquire","port":"2-3","port_token":11,"instance_token":22,"stream_epoch":1}
{"version":1,"tmr":"poll","port":"2-3","lease":"opaque token returned by acquire"}
```

After Acquire, Start/Finish/Exit/Release use the same shape as Poll, with only
the action changed. The server checks exact fields and types. Caller paths,
packets, operations for other calibration parts and another port's token are
not accepted. Responses state `link_basis: fresh_e0_continuity_only`.

Only an attested, present, active, error-free managed `109c/105e` with matching
kernel tokens and no outstanding manager job can be selected. A fresh ownership
guard runs before access. The FD is opened without symlink following and pinned
throughout the run. Its root-only kernel status is checked again before/after
commands; only explicit client Poll renews the lease. No command or run survives
daemon restart. Interrupted/uncertain sends are never retried.

The manager temporarily defers its regular status/return jobs and external
haptics on that port. Other ports retain their ordinary policy; kernel input,
motion reporting and serialized FF keep running. Global Release first closes
maintenance locally; it cannot proceed past an unconfirmed handle return.
Client disappearance, data loss, replacement, manager inhibition or shutdown
ends the run without inventing an Exit. First failure and cleanup failure are
reported separately; an uncertain close remains blocked and is not retried.

## Validation and next acceptance

Offline tests exercise actual extracted kernel ioctl/RX/send/close code against
synthetic Linux/USB objects, plus shared pure policy, manager requests,
credential boundaries, lease expiry and fake ioctl ABI serialization. Existing
startup, gamepad/paddle, IMU/IIO/evdev, motor/FF, trigger bridge, package and GUI
regressions are retained. The local module is built with warnings as errors.
The evidence receipt records exact results and limits; these tests do not
execute real kernel locks, firmware, radio transport or NVM writes.

The source package contains both manager modules and the shared header, with
no enablement. The packaging audit also restores two previously omitted,
already public ZZZ evidence files referenced by its shipped documentation.

Next: validate the complete candidate transport and stream/lifetime behavior,
then connect the accepted GUI through a reviewed scoped permission path.
Installation/activation and any real calibration require separate approval.
For the maintainer's later test, note the reported current stick display of
0.0 as baseline. A deliberately imperfect calibration is a proposed future
test, not something performed here. Comparing after power-off/on distinguishes
durable changed values from a merely changed current RAM/display state; the
display alone does not establish an exact physical center or hardware safety.
