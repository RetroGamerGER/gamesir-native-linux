# Pre-acquisition xpad race and startup-query review

19 October 2026. The initial offline manager correction is now included in
the revision-13 candidate below. No installation or hardware validation of
revision 13 has occurred; running driver and Steam settings remain unchanged.

## What the saved cold-boot evidence proves

The service started automatically, was enabled and unpaused, and had loaded
the expected revision-12 module. A new `100a` instance appeared; xpad input
registration and the manager failure occurred approximately 18 ms apart.
The recorded error was `Device changed during ownership check`. The manager
had no native binding, lease or bootstrap result. Thus this failure happened
**before the scoped acquisition write**, not inside native bootstrap and not
because of a missing button report. Subsequent button presses could not reopen
that instance: the original policy persisted it in the attempted set.

The old error does not identify the changed fields. Same-instance free-to-xpad
probe completion is a plausible cause, reproduced below with the exact error,
but the log alone cannot exclude incomplete metadata or a true replacement.
The user's pulsing Guide-ring report is retained as an observation, not proof
of RF pairing state or a missing USB initialization message.

## Bounded manager correction

The real Host adapter is tested against synthetic sysfs and process trees:
start with free IF0, let xpad bind while the ownership scan runs, and finish
the scan. Previously this raised `AcquisitionUnchanged` and the manager blocked
the instance. The correction accepts this **one specific pre-write transition**:

1. The immutable device object must match in every field except IF0 owner:
   port, boot/instance token, parent identity, PID, bus, address and both inode
   identities. The only accepted owner change is `None` to `xpad`.
2. Repeat the complete read-only descriptor/identity and foreign-handle check
   once, using that xpad-owned snapshot. Its initial and final observations
   must both be stable. No sleep, hardware command or retry loop is involved.
3. Issue at most one existing exact-instance `acquire_PID` request. The kernel
   still validates the USB object and permitted owner under its USB locks.
4. Only the existing post-write native proof authorizes bootstrap and cleanup.
   Start budget and persistent pause remain checked before entering this path.

Missing metadata, changed identity, foreign/native owner, xpad-to-free changes,
a second owner change, or inaccessible process handles still refuse the write.
Metadata errors are retained; identity mismatches now name the differing fields
without dumping identity tokens. Ordinary status, binding, return and scoped
claim guards remain strict. Errors opening/writing the actual acquisition
attribute are never caught as a harmless autoprobe event or retried. Partial
acquisition retains the existing conservative ownership/recovery behavior.

There is no migration that clears previous attempted instances, saved errors
or ownership intent. The old generic error is insufficient to authorize a new
attempt. A separately approved installation/recovery must establish a fresh,
reviewed start; this offline change does not unblock the running machine.
Kernel protocol, gamepad/paddle handling, gyro profile, IIO, force feedback and
the trigger bridge are untouched.

## What xpad's startup query actually does in the saved source

The pinned Linux reference is
[`drivers/input/joystick/xpad.c`, commit 5fce1616](https://github.com/gregkh/linux/blob/5fce161649b4d779d1b76d9fcd52dc77779774b8/drivers/input/joystick/xpad.c).
Its local source hash is in the [evidence manifest](evidence/XPAD_START_QUERY_REVIEW_20261019.json).
This is not a claim that the currently running distribution module has
identical source.

For an Xbox-360-style interface, `xpad_start_input` submits interrupt IN and
then sends this vendor/interface control IN request:

| Field | Value |
| --- | --- |
| bmRequestType | `0xc1` |
| bRequest | `0x01` |
| wValue | `0x0100` |
| wIndex | `0x0000` |
| wLength | 20 bytes |
| Timeout in the reference | 25 ms |
| Setup bytes on the wire | `c1 01 00 01 00 00 14 00` |

The source says some third-party devices need this to finish initialization.
Its response is discarded; an error produces a warning rather than failing
`xpad_start_input`. `xpad_open` reaches this path when an input consumer opens
the device. USB binding alone is therefore not evidence of this call.
The GameSir `100a` descriptor uses the Xbox-360-style interface despite the
controller's radio connection; the Microsoft Xbox 360 wireless-controller
power-on path is a different case.

xpad also sends IF0 LED commands `01 03 NN` on interrupt OUT. We observe
`01 03 00` and `01 03 02` in the stored files. These are distinct from IF1's
keyboard LED report `03 01` and from native GameSir bootstrap. A changed ring
appearance cannot by itself identify which initialization or RF event happened.

## Existing captures: observed, but necessity not established

Ten originals were rehashed against earlier evidence, read with `tshark -n -r`
and independently checked against raw PCAPNG USB headers/payloads. URB IDs,
request/completion frames and exact setup/response bytes agree. Initial
identity comes from saved baseline snapshots; return identities also have
`3537:100a` descriptors. There is no observed address reuse within these epochs.
The public manifest omits host paths, USB addresses and kernel URB pointers.

| Stored recording | Matching requests / successful replies | Successful `00 14` input reports in its `100a` epochs |
| --- | ---: | ---: |
| 11 October stage-4 five-second capture | 0 / 0 | 4,870 |
| 11 October measurement B, 13:39 label | 1 / 1 | 752 |
| 11 October measurement B, 13:43 label | 2 / 2 | 0 |
| 11 October measurement B, 14:00 label | 0 / 0 | 0 |
| 11 October measurement B, 14:11 label | 7 / 7 | 1,458 |
| 12 October Deadband motor comparison | 4 / 4 | 0 |
| 11 October test A | 0 / 0 | 2,093 |
| Native 300-second motor comparison, return epoch | 2 / 2 | 0 |
| First passive 90-second capture | 0 / 0 | 0 |
| Second passive 90-second capture with an input consumer | 0 / 0 | 10,787 |

All 16 observed replies succeed with the same 20 bytes:
`0014fff7ffffc0ffc0ffc0ffc0ff000000000000`.
This constant, capability-shaped response is not a measured live-input report;
its individual fields and any firmware side effects remain unproven here.
A vendor **IN** request can still change internal firmware state.

In measurement B at 13:39, all 752 input reports precede request frame 31484.
In the initial epoch at 14:11, all 261 input reports precede three later
requests (25787, 25801, 25824). Those particular later requests cannot have
started the already observed input. However, recording began after initial
setup in these cases; an earlier request outside the window remains possible.
Fully observed return epochs have already run native firmware mode and are
not clean cold starts. Successful replies without subsequent input likewise
do not prove RF pairing or bootstrap readiness.

**Decision:** the captures prove the query exists on this model; they prove
neither that it is necessary nor that it is unnecessary for a cold native
start. Do not add it, its LED sequence, or any other guessed USB command to
`gs_native` on this evidence alone. Correct the independent manager refusal
first. Any later experiment must isolate a fresh power-on with no prior xpad
initialization and needs separate hardware approval. No new test is started
by this report.

## Offline regression coverage

The new synthetic tests first reproduced the old rejection, then passed with
the correction. Coverage includes autoprobe before/during the ownership scan,
all three supported start PIDs, every identity field, foreign/native/reverse
owner changes, bounded second-check failure, new foreign handles, incomplete
metadata, permission failure, unchanged ordinary guards, one manager bootstrap
with zero pad reports, and a partially effective write failure across restart.
Full-suite validation is recorded in [the release audit](RELEASE_AUDIT.md).
These tests do not establish cold-start hardware reliability.


## Revision 13: explicitly requested startup-query integration

The later maintainer request authorizes integrating the observed query and
preparing a package, with fresh read-only target checks and an unprivileged
module build. Installation and cold-start acceptance still require separate
approval. Microsoft Xbox certification is not evidence that this particular
request is necessary or sufficient; the capture limitations above remain.

`gsn_boot_xinput_query` implements the exact control IN request above. This is
an original small adapter around the Linux USB API, using the pinned GPL-2.0-
or-later xpad source as a protocol reference and the recorded setup/replies
as evidence. No xpad source file or vendor binary is imported. Own code retains
GPL-2.0-only; the provenance record in LICENSING.md remains applicable.

The request executes only after an explicit bootstrap has passed ownership,
descriptor and permission gates on `100a`. Interrupt IN is already submitted.
After the existing five-second settle interval, the core reserves the first
8-byte transition OUT; the adapter performs the query before sending that OUT.
No pad report, button press or xpad input consumer is required. Probe, open,
passive status and scoped acquisition alone do not send this request. The
same-instance `109c`, experimental `105e` and native PM-resume paths skip it.

- Exactly one attempt per bootstrap, with 25-ms USB timeout, endpoint 0,
  interface 0 and an allocated DMA-safe buffer protected by `io_lock`.
- No spinlock spans the sleeping USB operation. A concurrent receive failure
  remains the primary error; the query result is recorded separately.
- Exactly 20 bytes are required. Negative USB errors are retained; every
  nonnegative short/oversized result becomes `-EREMOTEIO`. No interrupt OUT or
  mode switch follows failure, and no query retry is permitted. This is a
  deliberately stricter experimental policy than xpad's warning-only handling.
- The full device description, native ownership and existing deadlines are
  rechecked after the transfer. The existing first-OUT 250-ms deadline includes
  this query; the overall bootstrap deadline is not extended. A delayed reply
  cannot reopen a timed-out or failed bootstrap.
- The response bytes are not interpreted as RF connection or readiness proof.
  Existing initialization/acknowledgement, fresh IMU, token and input-publication
  checks still decide success. The 9+6 interrupt-OUT sequence stays unchanged.
- Journal fields `xinput_query_attempted` and `xinput_query_result` distinguish
  this operation from the existing interrupt-OUT counters, without changing
  the public ioctl ABI. Result 20 means a complete transport reply, not a
  validated wireless connection. Result 0 must be read with the attempted flag.

The extracted actual kernel adapter passes 282 sanitizer-backed scenarios,
including 15 new query cases. They exercise the captured setup and ordering,
negative/short/oversized replies, one-attempt enforcement, forbidden native END
on failed `100a`, post-transfer owner/descriptor/disconnect changes, the original
receive error winning over a later query error, timeout and success without pad
input. Existing direct-start/PM and permission tests also assert no query.
This fake USB environment does not prove real cold-start behavior or kernel
concurrency safety. Manager and packaging tests remain part of the full suite.

### Subsequent acceptance plan (not executed)

First approve and verify the single revision-13 package update, including its
pause/stop/unload/DKMS hooks. Preserve the existing sensor/Steam configuration
and old failure history. Activation/Resume is a separate reviewed step; an
enabled but persistently paused manager is not ready for an autostart test.
If the previous blocked device prevents recovery, use the already documented
manual physical return after separate approval, not automatic error deletion.

Then test an actual cold PC boot with the controller powered on, no buttons or
sticks, no manual service/Resume command and no Deadband. Record service,
instance/owner, query result, bootstrap/readiness and user-observed inputs.
Distinguish an initial `100a` (query expected) from an initial `109c` (query
must be absent). An initially xpad-bound device or previous xpad-open cannot
prove zero prior xpad initialization. Never blacklist xpad globally to force
that conclusion; other controllers must remain functional. A second separate
RF-off/late-power-on and reconnect test follows only after approval. On failure
stop once, preserve the original diagnostics, and verify any return against the
real PID; binding `109c` to xpad is not a `100a` recovery.
