# Steam gyro: downstream static investigation

19 October 2026. **Offline investigation; exact failing gate still unresolved.**
Steam's enabled SDL cache receives changing real gyro values, while its UI
remains at zero in the completed observation. This follow-up narrows the
remaining path without executing Steam, reading a live process/device, using
privileges/network or modifying Steam, the driver or installed configuration.

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
`0x1a4/0x1a6/0x1a8`. Their exact semantic meaning and the relevant live values
are **not established**; do not label that triplet as acceleration or gyro
merely from its position. The gyro-speed branch at `0x12361e8` checks a
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

Confirmed: delivery into enabled SDL, an instance-gated event path, separate
gyro packet fields that can advance without accel, a conversion preserving
the recorded motion, and a separate controller/side-specific UI feed with
default zero values. **The exact cause of the zero display is not yet proved.**

The remaining investigation should follow the backend packet consumer into
the motion object returned to the notification producer: identify the
three-field/readiness gate, its writers and controller/side assignment, then
connect those fields to speed-message production and timing/filter updates.
This is more specific than repeating SDL pairing tests or adding guessed
sensor capabilities. Any later runtime observation would require a separate
reviewed proposal and permission; none is started or authorized here.

Preserve the existing driver, accepted Eden motion, four independent paddles,
grip FF, trigger bridge, raw IIO and single USB owner. No Steam setting,
replacement library, synthetic accelerometer or driver change is recommended
from this evidence. Gyro calibration remains paused; no push.

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
