# Optional game trigger bridge — integration and local acceptance

Status: 2026-10-17, PRE-ALPHA. Optional revision `0.1.0.alpha1-2` passed
one approved integrated Forza/Xodus test after correction of a failed first
trial. Both triggers, effect pauses/restarts and quiet normal exit were felt;
normal input and grip rumble remained usable. This is limited acceptance,
not general game, reconnect, suspend or crash validation.
Gyroscope calibration remains paused.
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
unique active opaque broker instance at the current physical USB path.
Temporary manager `busy` is availability, not identity loss: the same exact
instance remains valid, and the existing broker serializes and defers hardware
work while retaining finite effect deadlines. Missing metadata, a replaced
instance or a foreign binding still terminates the launch/lease.
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

Check the effective groups of the actual desktop/launcher process. On a
system whose user manager survives desktop logout, logging in again can
leave desktop-launched applications with their old groups. A regular PC
reboot refreshes that process tree; changing socket permissions or repeatedly
restarting the controller service is not the remedy. An account-database
membership listing alone does not prove a running process can connect.

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

Next gates: broader simultaneous-channel coverage, process crash, reconnect,
suspend and multiple devices. The later corrected Xodus run below confirms
both triggers and preserved normal input/grip rumble for one game session.
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

At the initial installation checkpoint the account lacked `gamesir-native-haptics` membership.
No membership, socket permissions or launcher process credentials were
changed. One-time group enrollment and a fresh login are required before
ordinary unprivileged launches can access the broker. Installation and the
device-free `plan` command do not establish working trigger effects.
No integrated Forza run has started, and no push or new release has occurred.
Keep original transaction and verification logs private; the integrated
hardware result must be documented separately after the actual test.

The user subsequently performed the one-time group enrollment and authorized
a regular reboot. Afterwards the ordinary desktop, Nexus and broker preflight
had effective group access without sudo. Exactly one native evdev/USB/broker
instance passed the existing discovery and verification guards. A successful
native bootstrap was observed between fresh checks, without any agent-issued
resume, mode packet or recovery action. The integrated Forza launch was then
cued; its mechanical effect/stop acceptance is still pending. No game launch
or effect is inferred from the permission or discovery checks alone.

## First integrated Forza test — trigger acceptance failed

On 2026-10-17, the installed bridge `0.1.0.alpha1-1` was started through the
prepared Nexus launch option. The user confirmed that Forza was drivable,
normal inputs and grip rumble worked, but no trigger vibration was felt.
Forza was then ended normally; no error was visible in Nexus or its terminal.
This is a failed integrated trigger test, not a successful four-motor result.

Read-only process metadata confirmed the installed launcher and hook inside
Wine device services and the actual game. The sampled game processes used
the ordinary account with effective capabilities zero and the dedicated
haptics group. The older workspace hook was absent from their mappings.
The relay was initially present, then absent before its first recorded motor
operation. Its copied effect log remained empty. The native service retained
its process and zero restart count through this test.

There was no lifecycle/error record or retained relay traceback, so the live
exit cause is **not conclusively identified**. Empty effect logs can mean a
failure before forwarding, or a producer that connected and closed without
a frame. They do not establish whether a stop reached the physical triggers.

Two independent device-free reproductions identified a concrete integration
defect: the periodic manager status job reports the unchanged active instance
as temporarily `busy`. Discovery excluded busy entries, and ongoing identity
verification consequently treated that state as target loss. The relay's
idle health check could then terminate it before any effect. A synthetic
unchanged target toggling only `busy` reproduced the exit and empty effect
log. Clean producer EOF was separately reproduced and remains a distinct
possible explanation of the incomplete live evidence.

The targeted offline correction separates identity from availability. The
same attested instance must still satisfy all metadata, parent, driver,
device-number and opaque-instance checks. Temporary manager use must not
authorize a replacement or bypass broker ownership; the existing broker
remains responsible for deferring hardware commands while busy and expiring
finite effects. Bounded lifecycle diagnostics are added for a future test.
The candidate optional package is revision `0.1.0.alpha1-2`; core module,
manager, broker, C hook and installed revision 1 are not changed by this
offline work. No automatic reinstallation or hardware retry,
push or new release follows this failed test.

### Offline correction validation

The complete `make test` run passed: **843 Python unittest cases in 31
batches**, plus the existing native C, sanitizer and static checks. Eighteen
additional cases cover busy identity/start selection, broker-side expiry and
stop barriers, idle health, actual identity loss, clean EOF versus CLOSE,
startup/cleanup failures (including preservation of a forwarding failure),
private-data exclusion and the bounded diagnostic
log. The existing real ELF-to-Unix-to-fake-broker pipeline also passed.
All backends and metadata in these regressions are synthetic.

The revised logger records fixed lifecycle/error categories and counters,
never raw exception text, arguments, prefixes or session tokens. Its maximum
1,000 records include two reserved error/exit slots. No producer/identity,
age, STOP, CLOSE, device-replacement or broker-ownership guard was removed.
The broker still serializes actual hardware access and expires finite effects
during temporary manager work; the bridge does not open control or USB nodes.

The optional revision-2 package was built from reviewed commit `e264c1f`
without dependency installation or root. Its exact one-package update and
one corrected Forza run were subsequently approved; see the outcome below.
It required no new group membership, login, core update or Nexus launch edit.
Offline success alone did not establish the live outcome.

## Corrected integrated Forza test — limited acceptance passed

On 2026-10-17, only `gamesir-native-trigger-bridge 0.1.0.alpha1-2` was
updated. All 14 regular installed payload files matched the reviewed archive;
all 97 regular core-package files, the Nexus launch option, running service
and native target identity were unchanged. Normal Garuda package hooks made
pre/post snapshots; no DKMS, module, service or binding action was performed.

Forza Horizon 6 was manually launched through Xodus Nexus with the existing
explicit `forza-horizon-6` profile: LT gain 1, RT gain 3. The user confirmed
felt vibration on each trigger, intentional quiet intervals and renewed
effects afterwards. Normal input and grip rumble remained uninterrupted.
Forza was ended normally and both triggers became completely quiet.

The ordinary-user passive observer captured 2,337 producer frames and
669 accepted broker operations: 171 play and 498 stop. Of the recorded play
operations, 66 had nonzero LT and 100 nonzero RT; none had both nonzero.
This does not establish simultaneous nonzero LT/RT output in this run.
The 672 lifecycle/effect records contained no error or dropped records.
The relay ended on producer EOF with `cleanup_failed=false`; the launcher
then exited. Installed-hook mappings were observed in Wine and the game,
with no old workspace hook and effective capabilities zero. The same native
instance and service remained active with no service restart afterwards.

The producer connects on its first eligible trigger call, so readiness
without a producer connection during loading or menus is expected. It is not
by itself evidence of failure. The successful corrected trial supports the
busy/identity correction; the first trial's exact exit cause remains unknown.

This is one real game/launcher acceptance, not a USB capture or mechanical
latency measurement. Broker acceptance is not physical confirmation by
itself; the separate user report supplies the tactile result. Crash cleanup,
reconnect, suspend, multiple devices, Steam/Proton runtimes and automatic
launcher setup still need their own review and explicit tests. No new
hardware action is implied by documentation or source publication.
