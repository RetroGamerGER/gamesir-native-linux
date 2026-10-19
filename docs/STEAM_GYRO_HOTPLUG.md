# Gamescope: later power-on and gyro reconnection

19 October 2026. **Offline investigation and correction prototype, not an
installable fix or hardware acceptance.** The running driver, manager, Steam,
session files and remote system were not accessed or changed. No Steam/client,
controller, uinput or USB/IIO device was used. There was no web lookup or source
download; SDL probes use an isolated network namespace. The full-suite debug
lookup caveat is retained below. Calibration stays paused.

## Result and evidence boundary

The maintainer reports that motion works in Gamescope when the controller is
on before Steam starts, but not reliably after later power-on/reconnection.
The earlier [same-host comparison](STEAM_ACCEL_EXTENSION.md#same-host-kde-and-gamescope-comparison)
found Steam opening only the gamepad in a failed case and both nodes in a
successful case. Those observations did not measure the exact arrival/ACL order.

The new device-free tests reproduce **a sufficient failure mechanism** in
system SDL 3.4.18 and each of the three previously hashed Steam SDL3 libraries,
including the observed ELF32 runtime. They do not establish that this is the
exclusive cause of the historical Gamescope failure.

| Synthetic sequence, same running SDL process | Result in all four libraries |
| --- | --- |
| Paired nodes exist at SDL initialization | Gyro found, synthetic nonzero values readable |
| SDL already running; sensor detected first, gamepad arrives afterwards | Gyro found without application restart |
| Gamepad opened; paired sensor added afterwards | Existing open gamepad remains without gyro; closing/reopening the test handle finds it |
| Sensor node exists but open returns EACCES; gamepad opened; sensor later readable | Existing gamepad remains without gyro after the permission-change notification |
| Prototype withholds gamepad publication until the paired sensor is detected/readable | Gyro available at first gamepad open; sensor-first reconnect in same process also succeeds |

Each case then removes both fake nodes, verifies the joystick count becomes
zero and reconnects sensor-first in the **same SDL process**, retaining gyro.
There are 20 scenario runs and 15 additional pure policy tests. Negative
scenarios pass by reproducing missing gyro, not by pretending they are fixed.
Sensor values are synthetic; these tests make no new physical calibration,
packet-loss, sample-rate, motor, paddle or hardware-lifecycle claim.
[Portable hashes and results](steam-gyro-hotplug-offline.json).

## Why registration order is insufficient

The preserved official [Linux SDL source](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c)
(`docs/sdl-source-manifest.json`, file hash rechecked) selects `GetSensor()`
from `LINUX_JoystickOpen()`. `MaybeAddDevice()` records later sensor discovery
without reconfiguring already-open joysticks. The enable path uses the selected
sensor. These source facts agree with the independently executed library tests;
the reference is not claimed as the exact source of Steam's bundled binary.

`gsn_input_register()` already registers the motion device before the gamepad.
That orders kernel registration, not completion of both udev workers, seat ACLs,
or SDL discovery. A node being present or readable *after* Steam opened its
gamepad does not prove it was usable at that first open. A later readable
snapshot cannot repair the missed association in the tested backend.

The tests use real inotify notifications on **regular files inside a private
/dev**, with our existing syscall fixture handling evdev queries. A synthetic
access-denial switch models an unavailable sensor. They do not execute real
udev/logind ACL processing, Steam event handling or Gamescope. No actual
compositor defect or universally necessary Steam restart is established.

## Prepared correction: a bounded two-phase publication gate

The prototype is `tools/sdl/input_pair_readiness.py`. It is **not imported by
the current manager, included in the installed package, or connected to an
input-publication command**. It is intentionally a reviewable policy prototype
before changing a working kernel/manager lifecycle.

The proposed sequence for the opt-in standard-109c motion profile is:

1. Attest the exact owned native binding using existing kernel/session tokens.
   Prepare the gamepad and publish the existing motion node. Keep the raw IIO,
   IMU stream, existing scale/axes and single USB owner.
2. Observe the **processed** input hotplug notification for that exact motion
   node and check access for the intended active session. Match the binding,
   nonempty shared `uniq`, native interface and input-node lifetime; an event
   number, PID or earlier udev database entry is insufficient.
3. Only then publish the prepared gamepad once, after a fresh exact-instance
   check in the kernel. SDL can discover the usable sensor before opening the
   newly announced gamepad. There is no Steam restart, fake gyro capability,
   controller identity change or global delay.
4. A replacement/disconnect invalidates the old gate. A new binding needs its
   own existing manager ownership/start checks and a new gate. This is not a
   new USB-retry authority. Multiple dongles cannot lend each other readiness.
5. Timeout, invalid six-axis metadata or an uncertain publication must retain
   the original error and use existing verified cleanup. Never claim fallback
   or input publication succeeded merely because a plan was returned.

The prototype checks missing/old processed-node proof, unavailable access,
invalid resolution, changed hub/interface/instance, disappearance, duplicate
events, a fixed deadline and mismatched acknowledgements. Publication is a plan
until explicitly acknowledged. It does **not** provide atomic system-level
TOCTOU protection; the future kernel operation must supply that protection.
Its three-second synthetic deadline tests boundedness, not a recommended
production startup delay or a measured hardware requirement.

The gated SDL scenario models the intended ordering using ordinary test-file
publication. It does not exercise an implemented kernel/manager handshake.
The sensor-first ordering also passes without the gate; this is evidence for
the precondition, not evidence that the prototype modified SDL's behavior.

## Remaining implementation before an installation candidate

**No-Go for installation of this prototype as a gyro-hotplug fix.** Existing
production package versions and installed behavior remain unchanged. Necessary
work is now explicit, rather than another unbounded firmware/gyro investigation:

- Add an optional, backward-compatible two-phase input-publication operation
  to the private kernel/client contract. Old clients keep their current behavior.
  Validate exact native instance tokens under the existing lifetime locks;
  reject publication after STOP, suspend/quiesce, disconnect or replacement.
  Do not unregister/re-register an active gamepad to manufacture a reconnect.
- Integrate the gate into the existing manager with a processed-input-event
  backend established before takeover. A sysfs node or `udev` database entry
  alone must not stand in for completed notification and session access.
  Pin the input-node lifetime, preserve cleanup authority/start-budget separation,
  failure persistence and leases across manager/client interruption. No global
  `udevadm settle`, permissions widening or polling/restart loop.
- Define no-active-session, denied ACL, missing notification and timeout behavior
  without blocking ordinary controls indefinitely or claiming a successful
  automatic `109c`→`100a` return. The existing guarded manual path remains valid.
- Execute the actual registration/teardown adapter with fake kernel objects,
  manager restart/timeout/disconnect regressions and packaged-kernel/client
  compatibility tests. Build the module and package only after the handshake
  is implemented. This study does not bump a package version or generate an
  installer containing a nonfunctional gate.
- Under separate permission, validate actual Gamescope discovery/FDs/UI for
  later power-on and radio reconnect, then combined ordinary input/paddles,
  Eden, FF and trigger ownership/STOP. Cover application-start races and
  suspend separately. Passing synthetic inotify tests cannot replace this.

A source-level SDL improvement for late sensor association remains an upstream
alternative, but patching/replacing Steam's private library or injecting a global
preload is not selected. The current approach preserves the accepted evdev
contract and keeps the remedy in our own kernel/manager boundary.

## Reproduce without devices

```sh
python -B tests/test_input_pair_readiness.py
make test-sdl-hotplug
python -B tests/run_sdl_hotplug_test.py --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0
```

Use a full source checkout with existing Bubblewrap/clang/SDL and multilib for
ELF32. The runner does not install dependencies or start Steam. The existing
sandbox auditor verifies six isolated namespaces, zero capabilities,
NoNewPrivs and no host input/USB/IIO nodes before the child creates its fake
input directory. Only the explicitly selected SDL file is mounted read-only;
its loaded path and before/after hash are checked. The test-only preload is
confined to that child. Logs remain under ignored `build/results/sdl-hotplug/`.
The full regression suite still covers existing paddles, IIO, FF, manager and
packaging; no new combined real-hardware acceptance is implied.

Final `make test` passes, as does `make test-sdl` (18 existing button scenarios,
16 existing sensor scenarios and the five system-SDL hotplug scenarios).
Accepted regression commands set `DEBUGINFOD_URLS=` and
`LLVM_SYMBOLIZER_OPTS=--no-debuginfod` for those test processes only. The first
suite attempt timed out in an existing ASan ownership-bug negative control;
the inherited environment enabled external debug-symbol lookup. That lookup
was not traced, so it is not a proved exclusive timeout cause. The isolated
control and full final suite pass with external lookup disabled. A subsequent
package regression also caught the new README link missing from the explicit
document allowlist; the two report files are now included, not the prototype.
Original interrupted/failed logs are retained alongside final results in ignored
`build/gyro-hotplug-*.log`. No sanitizer check was disabled or test timeout raised.
