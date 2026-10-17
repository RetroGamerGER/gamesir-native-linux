# Optional game trigger bridge — integration and local acceptance

Status: 2026-10-17, PRE-ALPHA. This integrated revision is offline-tested and
installed locally, **not yet hardware-accepted**. Gyroscope calibration remains paused.
Kernel, manager, paddle mapping, firmware and controller settings are unchanged.
[Provenance and licensing](TRIGGER_BRIDGE_PROVENANCE.md) were checked first.

## Evidence and supported scope

The separate project-owned bridge at `3a78390` has seven local commits. Its
recorded Forza Horizon 6 / Xodus Nexus experiment felt both impulse triggers:
LT gain 1, RT gain 3, bounded to 100 percent. Explicit game zeros are intentional
pauses; effects must not be synthesized from trigger position. Its 16 tests
include effect restart with a synthetic backend, **not** a PC restart,
hotplug or suspend test. That tactile result does not validate this revision.

The adapter intercepts explicit `dlsym()` lookup of SDL2
`SDL_JoystickRumbleTriggers`/`SDL_JoystickClose` on glibc x86_64.
SDL2 >= 2.24 and `SDL_JoystickPath` exposing the real canonical evdev path are
required. SDL3, direct SDL symbol calls, 32-bit Wine, Steam Runtime/Pressure
Vessel, other Wine backends and the ZZZ edition are not validated.

## Architecture and ownership

```text
game / Wine SDL2 -> per-launch hook -> private socket / transport v2
                -> ordinary-user relay -> existing haptics broker API v1
                -> existing GSN_PULSE ABI / gs_native -> trigger motors
```

Only `[LT, RT, null, null]` reaches the broker. Trigger stops use mask 3.
Normal grip `FF_RUMBLE` stays separate. The kernel remains the sole native
USB owner; game gains, Wine hooks and launcher details remain in userspace.
The broker grants private ownership per entire device instance, not per
channel to multiple private clients. A second private haptics application
can therefore conflict, although normal kernel grip FF remains available.

The launcher opens only the broker socket and reads sysfs/node metadata,
never evdev or USB nodes. Exactly one eligible native target is required;
zero/multiple candidates stop the adapted launch rather than choosing first.
Selection verifies name `GameSir G7 Pro`, input/USB `3537:109c`, native IF0
ownership, matching character-device number, inode/device metadata, and a
unique non-busy opaque broker instance at the current physical USB path.
There is no configured port, address or per-machine game-prefix hash.

The current topology is frozen only for this launch. SDL's actual event path
must match. Before each broker output and periodically while idle, identity
and metadata are rechecked. Disconnect/replacement/binding change ends the
lease; a replacement at the same port or event number is never adopted.

A random 16-byte session and target are stored in a 0600 manifest inside a
fresh private 0700 user runtime directory. The producer socket is 0600;
`SO_PEERCRED` checks UID/PID, and one producer/SDL instance owns the session.

## Transport and stop semantics

Hook-to-relay v2 is separate from unchanged broker API v1. Each frame is
128 bytes, little endian; unknown values/reserves are rejected:

| Offset | Field |
| --- | --- |
| 0 | magic `GST2` |
| 4, 6 | version u16 = 2; type u16 = EFFECT 1 or CLOSE 2 |
| 8, 12 | frame size u32 = 128; reserved u32 = 0 |
| 16, 24 | sequence u64; emission CLOCK_MONOTONIC nanoseconds u64 |
| 32, 36 | PID u32; SDL instance signed i32 |
| 40, 42, 44 | LT u16; RT u16; finite duration u32 milliseconds |
| 48 | 64-byte canonical event path, NUL/zero-padded |
| 112 | nonzero 16-byte session |

Wrong sessions/sources/PIDs, reordered frames and excessively old/future
timestamps close the lease. Duration is reduced from emission time, including
socket delay and broker validation time; receipt does not restart an effect.
Host timestamps do not prove physical actuation time.

Broker API v1 accepts relative milliseconds. After the relay calculates the
remaining time, client-lock contention and broker IPC/scheduling can still
add delay. This is not a strict end-to-end absolute-deadline guarantee; a
future deadline-aware broker contract would need separate review/tests.

A newly zeroed channel is a queue barrier. Following nonzero updates cannot
replace that zero/STOP/CLOSE. Ordinary states coalesce only between barriers.
The queue is bounded to 16 entries; overload closes the lease instead of
discarding stop barriers. At most 20 broker updates/s are forwarded, each
requiring list + play/stop, leaving room for heartbeat/health checks under
the existing 50 requests/s limit. This adds latency, not real-time fidelity.

EOF, transport/broker failure, malformed packets and identity changes close
the broker connection. Existing broker leases and bounded hardware commands
provide cleanup if cancellation cannot be acknowledged. A successful socket
send is not broker/USB/mechanical confirmation. The input thread never waits
for a broker reply, silently retries effects or changes a driver binding.

During play, a failed relay ends trigger forwarding without killing the game;
the per-launch USB filter remains. Startup failures currently stop that
explicit adapted launch. There is no fallback that silently removes USB
ownership protection. Reconnect/failure requires a fresh explicit launch.

The libusb filter matches only the authorized bus/address plus `3537:109c`
in the game process tree. Other devices pass through. This is a compatibility
filter for inspected libusb paths, **not a sandbox** against every USB access
method. No native ownership guard is bypassed.

## Permissions and launchers

No `sudo`, `pkexec` or `setpriv` is invoked. The existing haptics group must
already allow broker access. A separately approved one-time enrollment and
new login can remove per-game password prompts. Membership permits the
account's processes to use the bounded four-motor API, not only this relay;
it grants no USB/root/manager rights. This work changes no memberships.

This optional version never edits Nexus JSON, Steam settings, shared
Wine/Proton files, global environment, services or Steam paddle integration.
Existing preloads/inherited bridge sessions are rejected for explicit review.
A dedicated absolute WINEPREFIX is required; validation checks the absolute
path, not whether unrelated applications share it. Matching `wineserver -w` keeps
the relay until that prefix exits. Unrelated applications sharing that prefix
are outside this version's lifecycle assumptions. Arguments/prefixes are not
logged; bounded diagnostics stay in the ephemeral private runtime directory.

`neutral` uses LT 1x / RT 1x. Explicit `forza-horizon-6` uses LT 1x / RT 3x,
not a universal GameSir correction or sensor calibration. No effects are
inferred from axes or grip rumble.

Device-free plans:

```sh
python -B tools/trigger_bridge/launch.py plan --adapter nexus-sdl2
python -B tools/trigger_bridge/launch.py plan --adapter nexus-sdl2 --profile forza-horizon-6
python -B tools/trigger_bridge/launch.py plan --adapter steam-proton-sdl2
```

The live `run` subcommand accepts `--adapter nexus-sdl2`, optional `--profile`
and `--` followed by the original absolute wine/wine64 command. It requires
separate real-use approval and is not run in tests. Steam/Proton is plan-only;
live execution is rejected pending runtime/ABI validation. Games without a
separate trigger-command path do not acquire it merely through this package.

## Offline checks and packaging

```sh
make test-trigger-bridge
make trigger-bridge-source
```

Tests use fake sysfs/node metadata, fake SDL/libusb libraries, source compiler
outputs and synthetic socket/broker backends. No installed client/broker
copy, Wine/Steam process or real USB/input device is used. The optional Arch
build-source has its own `gamesir-native-trigger-bridge` package/version,
no activation hooks, group enrollment or launcher edits. Building/staging
is not installation; complete regression tests require the full repository.

Validation on 2026-10-17: `make test` passed, including 791 Python unittest
cases in 29 batches plus the existing C/native assertion and static checks.
The 64 new bridge cases comprise 11 ELF-hook, 33 protocol/identity/relay,
one cross-language pipeline, seven launcher and 12 package tests. The pipeline
uses the actual C hook, fragmented Unix transport, Python forwarding and the
repository broker with fake motors; it checks expiry, zero/restart/CLOSE and
preserves concurrent synthetic grip states. Independent review found and
corrected an EOF queue-flush defect before this passing full run.

The optional source recipe was also built and staged unprivileged in an
ignored build directory; no Arch binary package was installed. Package tests
check deterministic source archives and an extracted build-source copy.
Kernel, core manager/client, paddle integrations and all IMU sources remain
byte-unchanged from the pre-integration source baseline. The core package
allowlist adds only the new linked documentation so installed README links
continue to resolve. Existing public-export metadata describes its historical
snapshot and is not relabeled as a new audit; current SHA256SUMS is regenerated.

Next gates: separately approved integrated Xodus test, simultaneous grip and
trigger effects/stops, process crash, reconnect, suspend and multiple devices.
Steam/Proton needs its own supported launch hook, container/ABI tests and real
game acceptance. Automatic launcher setup without per-game configuration
remains a future adapter task, not a completed feature of this offline phase.

## Local installation and prepared Xodus test

The maintainer separately authorized installation and a subsequent integrated
Forza/Xodus test. Only `gamesir-native-trigger-bridge 0.1.0.alpha1-1` was
installed. The transaction completed successfully; package checking reported
27 entries and zero altered files, and all 14 regular payload files matched
the reviewed archive. Its SHA256 is
`801e17786cecae38d7e80c318ffa48a8bc3bbf0c110d70f5096b9b4efe960528`.
There are no package-specific activation hooks, services or kernel modules.
The running native service retained its process and zero restart count;
core package `0.1.0.alpha3-6` and Steam integration were unchanged.

After Forza and Nexus were closed, only Forza's existing launch option was
replaced with the installed adapter:

```text
/usr/bin/gamesir-native-trigger-bridge run --adapter nexus-sdl2 --profile forza-horizon-6 -- %command%
```

The former launch-tools field was backed up privately with mode 0600. The
configuration was compared structurally before/after: every other profile
value was preserved. This is an explicit local test setup, not automatic
configuration for all games or a change to Nexus binaries.

At this checkpoint the account lacks `gamesir-native-haptics` membership.
No membership, socket permissions or launcher process credentials were
changed. One-time group enrollment and a fresh login are required before
ordinary unprivileged launches can access the broker. Installation and the
device-free `plan` command do not establish working trigger effects.
No integrated Forza run has started, and no push or new release has occurred.
Keep original transaction and verification logs private; the integrated
hardware result must be documented separately after the actual test.
