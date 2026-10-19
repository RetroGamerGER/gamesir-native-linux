# Steam gyro: downstream static investigation

19 October 2026. **A sufficient gyro-only UI blocker is now identified
statically; the historical run's exclusive failing branch was not observed.**
Steam's enabled SDL cache receives changing real gyro values, while its UI
remains at zero in the completed observation. This follow-up narrows the
remaining path without executing Steam, reading a live process/device, using
privileges/network or modifying Steam, the driver or installed configuration.

The [notification-gate follow-up below](#notification-gate-follow-up) resolves
the previously unidentified three-field test: it checks the selected side's
**acceleration**, not its angular velocity. All-zero acceleration skips the
gyro notifications even if gyro values, source validity and subscriptions
are present. This is a concrete contract mismatch for our documented
gyro-only evdev interface, not a demonstrated defect in its working SDL/Eden
delivery. Additional failed gates in the historical run remain possible.

See [portable addresses, hashes and replay results](steam-gyro-downstream-offline.json)
and the [previous live evidence](steam-gyro-observation-live-001.json).
Addresses below refer to the hashed **ELF32** `linux32/steamclient.so`, not
runtime addresses. JavaScript offsets count decoded characters in the hashed
`steamui/sp.js`. Findings are specific to those files, not every Steam version.
Only independently described facts and aggregate results are distributed;
proprietary binaries, JavaScript excerpts and disassemblies stay outside Git.

## Event routing and internal packet conversion

The statically reconstructed path is:

```text
SDL gamepad sensor event (0x659)
  → event.which must match the backend object's SDL instance
  → standard gyro / left gyro classification
  → timestamp conversion and signed 16-bit angular-rate representation
  → per-device pending record → backend reader → internal packet converter
  → sensor timing / downstream motion processing
  ... remaining runtime selection/readiness/subscription checks ...
  → gyro-speed notification (controller_index, imu_index)
  → UI feed store → displayed GyroRawSpeed
```

This is a static map with an explicitly incomplete middle section, **not a
trace proving that every arrow executed during the observed run**. In
particular, changing SDL cache values do not prove that Steam's event watch
received the matching event or that the backend object retained the same ID.

| Stage | Concrete finding | Evidence anchor |
| --- | --- | --- |
| Sensor dispatch | `0x659` selects sensor handling; `event.which` must equal the backend object's SDL instance. No USB address, physical port or product-name comparison in this gate. | `0x19c2e2b`, `0x19c2f60` |
| Sensor lane | Standard gyro type 2 uses the main lane; gyro type 4 uses the left lane. Types 6/5 have fallback checks against base gyro/accel availability. | `0x19c28c0`, `0x19c2af0` |
| Sensor time | The ELF32 sensor timestamp is at event offsets `0x24/0x28`; integer division by 100 retains the low 32 bits for the internal lane tick. The separate event timestamp supplies another time field. | `0x19c2c91`, `0x19c21b9` |
| Packet gyro | Main gyro sets flags `0x402` and three int16 fields. Acceleration has a separate flag `0x4` and fields. | `0x19c2c58`, `0x19c2c80` |
| Record turnover | Once a pending main-lane tick is nonzero, a following gyro event can flush that record without an acceleration event. The ordinary flush enqueues the record. | `0x19c22c0`, `0x19c2074` |
| Backend read | The pending queue is read with a representation-dependent copy, capped at 72 bytes. Queue delivery beyond the cache was not observed live. | `0x19bf990` |
| Next conversion | The main gyro branch tests `(flags & 0x402) == 0x402`, copies the gyro fields and reaches timing processing even when acceleration flag `0x4` is absent. | `0x1243959`, `0x1243f83`, `0x1243fb4` |

**Important negative result:** these inspected early branches do not require
gyro and acceleration to arrive together. That narrows the earlier acceleration
hypothesis; it does not establish that later motion fusion, initialization or
calibration supports gyro-only devices. Nor does it justify adding synthetic
acceleration to the accepted SDL/Eden interface.

The conversion uses an approximately ±34.906586 rad/s range (±2000 degree/s)
mapped to signed int16, with clamping. This is **Steam's internal transport
range**, not evidence of the GameSir sensor's configured physical range or a
new GameSir calibration factor. An independent arithmetic replay of the 194
saved movement-cache samples produces 192 nonzero vectors; component ranges
are X −9873…7522, Y −5850…5607, Z −4780…4158. Therefore ordinary quantization
in this first conversion cannot explain a continuously zero display for those
values, **if they reach this branch**. Two replayed vectors are all zero; the
analysis does not assume continuous motion in every sample.

The replay does not execute Steam code, emulate all filters or prove bit-exact
x87 rounding. Cache snapshots sampled about ten times per second are not an
event-rate or packet-loss recording.
For reproduction, use the hashed constants in the JSON: normalize each saved
rad/s value as `(value + offset) / span`, saturate outside [0,1], otherwise
multiply by 65535, subtract 32768, round to float32 and truncate toward zero.
This is an arithmetic comparison, not a replacement implementation of Steam.

## The display has its own controller/IMU feed

The rate display is module 84508, starting at character 9,586,996. It reads
`GyroRawSpeed.pitch/yaw/roll`; it does **not** display `GyroFilteredSpeed`.
The bar uses a monotonic tanh transformation; the numeric suffix formats the
raw-speed field to one decimal place. Orientation graphics separately read
`GyroRawQuaternion`. The internal label “Raw” does not mean these are the
original USB counts or prove absence of earlier Steam processing.

Module 35137, starting at character 11,411,606, initializes both main and left
speed stores to zero. Its gyro-speed notification callback at character
11,426,669 copies the notification fields, indexed by `controller_index`:
`imu_index == 1` selects the main store; other values select the left store.
The displayed side chooses the corresponding store. No gyro deadzone,
calibration-complete check or accelerometer test occurs in this callback or
the inspected numeric rendering branch.

The feed hook near character 11,434,656 starts `ControllerStateFlow` when
mounted and ends it when unmounted. Gyro speed requests flow mode 3;
quaternion requests mode 2. Thus three identities must not be conflated:

- the USB/evdev session identity used for SDL pairing;
- the SDL joystick instance used by the backend event dispatcher;
- Steam's controller index and IMU side used by UI subscriptions/notifications.

The saved cache observation established one enabled SDL instance, **not**
the other mappings or active UI subscriptions. A stale controller index,
wrong side or missing notification could leave the zero-initialized UI store
unchanged. These are concrete candidates, not observed runtime failures.
Changing the controller's display name would not repair the inspected
instance/index gates.

## Later readiness, subscription and timing gates

The native notification producer at `0x1235db0` checks controller presence,
object pointers and subscription state. Before its motion notifications,
`0x123619b` checks a returned object's byte at offset `0x5c`, then requires
at least one nonzero 16-bit field at selected controller-state offsets
`0x1a4/0x1a6/0x1a8`. At the initial checkpoint their meaning was unknown.
The follow-up below identifies them as acceleration by tracing the writer,
cached report base, lane stride and independent sensor reader. Their live
values were not sampled. The gyro-speed branch at `0x12361e8` checks a
subscriber count before constructing its message at `0x1236578`; the send
path references `SteamInputManager.NotifyGyroSpeedStateChanged#1` at
`0x1236618`. These are additional possible reasons for an unchanged UI store,
not proof that one of them blocked this controller.

The sensor-timing helper at `0x127fbb0` uses the lane ticks, packet timing
and configurable estimation/fallback paths. Its surrounding diagnostics
distinguish expected, sensor and Steam-polling intervals. The previous
`gyro_auto_detect_polling_rate` finding remains relevant, but the active
setting and the selected branch were not read. The saved observer log has
cache values and observer timestamps, **not SDL event sensor timestamps**;
it cannot establish the internal delta time, wrap handling or filter state.
The 32-bit 100-ns lane counter wraps after about 429.5 seconds; that fact
alone is not a bug or evidence that wrap occurred in the failed path.

## Assessment and next targeted investigation

At the initial checkpoint we confirmed delivery into enabled SDL, an instance-gated event path, separate
gyro packet fields that can advance without accel, a conversion preserving
the recorded motion, and a separate controller/side-specific UI feed with
default zero values. The follow-up now identifies a sufficient static block
on that UI path; it does not establish the exclusive historical runtime cause.

The remaining investigation should follow the backend packet consumer into
the motion object returned to the notification producer: identify the
three-field/readiness gate, its writers and controller/side assignment, then
connect those fields to speed-message production and timing/filter updates.
The notification-gate follow-up below completes the field and source mapping;
historical runtime subscription, source validity and event routing remain unmeasured.
This is more specific than repeating SDL pairing tests or adding guessed
sensor capabilities. Any later runtime observation would require a separate
reviewed proposal and permission; none is started or authorized here.

Preserve the existing driver, accepted Eden motion, four independent paddles,
grip FF, trigger bridge, raw IIO and single USB owner. No Steam setting,
replacement library, synthetic accelerometer or driver change is recommended
from this evidence. Gyro calibration remains paused; no push.

## Notification-gate follow-up

The [new evidence manifest](steam-gyro-notification-gates-offline.json) pins
19 bounded ELF32 text regions by address and SHA256. Disassembly starts at
known function/branch boundaries; nearest exported-symbol names printed by
objdump are not treated as internal function names. RTTI independently
identifies the relevant classes as `CGenericGamepadControllerAbstraction`
and `CGyroSource`. No vendor code is executed or redistributed.

### The unknown triple is acceleration

The poll loop derives its destination from the passed context plus `0x180`
(`0x1231cd7`), calls the device abstraction's virtual slot `+0x34` with that
destination (`0x1231f11`) and advances it by `0x210` for each controller
(`0x12325c4`). The generic abstraction's vtable maps that slot to the packet
converter `0x1243770`. A separate snapshot reader at `0x11c52c8` copies the
same context/slot `+0x180` report; an initialization/reset path at `0x11f97cc`
zeroes its 176 bytes.

The converter's acceleration branch uses the SDL acceleration flag `0x4`:
`0x1243cc4` writes the left triple to report offsets `0x24/0x26/0x28`;
`0x1243972` writes the main triple to `0x58/0x5a/0x5c` only when that flag is
present. Gyro writes different fields, `0x2a/0x2c/0x2e` and
`0x5e/0x60/0x62`. Thus gyro updates alone do not fill the acceleration triple.
`CGyroSource` independently reads the same triple at
`report + side*0x34 + 0x24` (`0x1347968`), scaling it for its acceleration/
orientation calculations. This is a writer/reader mapping, not a guess from
an offset or from three zero UI numbers.

| Side | Report acceleration | Cached controller-state acceleration | Report gyro |
| --- | --- | --- | --- |
| Left / IMU 0 | `0x24, 0x26, 0x28` | `0x1a4, 0x1a6, 0x1a8` | `0x2a, 0x2c, 0x2e` |
| Main / IMU 1 | `0x58, 0x5a, 0x5c` | `0x1d8, 0x1da, 0x1dc` | `0x5e, 0x60, 0x62` |

The second notification iteration adds `0x34` to the selected cached-state
base (`0x1235edc`). Its same three comparisons therefore test **main**
acceleration at `0x1d8/0x1da/0x1dc`, not the unused left sensor. That rules
out the interpretation that the new finding concerns only left Joy-Con data.

### Source validity and subscriptions

Notification lookup first asks for feature 16, then feature 10. The factory
constructs the same `CGyroSource` with side 0 or 1 respectively
(`0x1345550`, `0x1345600`). Lookup at `0x1293130` uses the feature cache;
the notification calls pass `create=false`, so this path does not itself
create a missing source.

The source getter's virtual slot `+0x2c` returns `source + 0x138`
(`0x1345f90`). Its tested state byte `+0x5c` is therefore source offset
`0x194`. The constructor clears it; the finite-quaternion publication path
sets it to 1 at `0x1347e29`. It is a published-state validity marker, not
proof of current connectivity, freshness or completed software calibration.
Its actual historical value remains unknown.

The flow handler at `0x12395d0` accepts controller indices 0–15 and flow modes
0–5; its index arithmetic makes mode 3 select the counter at
`context + controller_index*24 + 0xb960`. The speed-notification branch tests
that counter at `0x12361e8`, matching the UI's speed-flow mode 3. Both flow
registration and the periodic 16-controller pass (`0x1236ea8`) invoke the
notification producer. An absent subscription remains another possible
runtime failure, but a valid subscription cannot bypass its acceleration gate.

### What this establishes

With the other guards assumed to pass, the selected notification block still
requires **source validity AND at least one nonzero acceleration component**;
speed messages additionally require a speed subscriber. A zero gyro vector
does not itself fail this particular gate. Therefore ordinary stationary
gravity from a real accelerometer can permit updates, whereas arbitrarily
large gyro values with zero acceleration cannot. This is not a gyro deadzone.

Our source registers only the three rotational evdev axes in
`gs_gyro_register_input`; raw acceleration stays in IIO. Earlier SDL tests
confirm gyro present and acceleration absent. In a freshly zeroed cache fed
only by that contract, the acceleration fields remain zero and this Steam
UI path cannot publish the gyro rates. That is a **sufficient static
explanation of the observed zero display**, beyond the earlier general
acceleration hypothesis.

It does not prove this was the only failing condition, establish the exact
historical branch values, or decide whether Valve considers gyro-only support
an omission or unsupported contract. It also does not establish that every
Steam gameplay/mouse/Steam Input API path uses this UI gate. Calibration
progress notifications share the gated block, which can explain an apparently
stalled wizard without proving that the internal calibration algorithm failed.

An independent model on own zeroed buffers checked 64 combinations of side,
acceleration, gyro, validity and subscription, plus two wrong-side negative
cases. Nonzero gyro never satisfied the missing-acceleration gate; a nonzero
component on the other side did not satisfy it either. Two static vtable
cross-checks passed. These are selected-gate/offset counterexamples, **not
tests of Steam execution, complete fusion or real hardware**.

No forcing of validity/capability flags, synthetic gravity, modified Steam
library or sensor-interface change follows from this investigation. A later
integration proposal can address genuine acceleration with independently
validated axes/units, or seek upstream gyro-only handling. Neither is
implemented here; preserve the accepted Eden path and all other functions.

## Validation of this documentation change

`make test-steam` passes all 104 existing observer, terminal, session and
Steam/Gamescope packaging tests using their own fixtures/stubs. The seven
public-README and three licensing tests also pass. These 114 checks protect
the existing offline tooling/integration boundaries; they do not verify the
inferred proprietary branches or establish a root cause.

Both vendor-file hashes were checked before and after static inspection;
the saved source log hash, arithmetic boundary checks, JSON, local report
links, private-path scan and Git whitespace check pass. The documentation
and evidence are the only tracked changes. No new live run or push occurred.
