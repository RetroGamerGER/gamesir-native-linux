# Steam gyro: real acceleration extension (offline preparation)

19 October 2026. **Implemented and tested offline, not installed or activated.**
This prepares a correction for the [statically identified acceleration
notification gate](STEAM_GYRO_DOWNSTREAM.md#notification-gate-follow-up).
It does not establish Steam Input/gameplay acceptance or prove every gate in
Steam's historical live run. No Steam library, configuration or installed
module is modified. Gyro calibration remains paused.

## Contract

Keep the accepted `experimental_gyro=1` standard-109c path and its gyro
conversion unchanged. A **separate default-off** `experimental_accel=1` option
adds ABS_X/Y/Z to the same paired motion evdev node. All six values come from
one accepted IMU report, use one host receive timestamp, one MSC_TIMESTAMP
and one SYN_REPORT. There is still one USB owner, no extra reader, no IIO
buffer activation and no new USB or sensor configuration command.

Acceleration is actual signed wire data, with an explicit signed permutation:
`accel_axis_map` contains exactly three distinct signed 1-based axis selectors
for SDL X, Y, Z. `1` selects A0, `-2` selects negative A1, etc. The default
`0,0,0` is deliberately invalid when acceleration is enabled. The kernel
rejects unset/partial/duplicate/out-of-range maps and activation without gyro
**before usb_register**. No identity map or gyro-derived map is chosen.
The options are read-only after module load; there is no live map switch.

The existing replaceable experimental scale `accel_counts_per_g_num/den`
supplies the evdev counts/g resolution (default 8192/1). This extension
requires a positive integral quotient; non-integral rational resolutions
are rejected rather than rounded. Raw IIO conversion still supports its
existing rational scales. Signed permutation uses s32, including negation
of -32768 to +32768; evdev bounds include both. SDL converts these counts
using 9.80665 m/s² per g. The independent gyro factor remains 0.07 dps/raw.
Neither API returns verified-calibration status for this experiment.

Lifecycle neutralization reports zero angular velocity and pauses the sensor
clock as before. It sends **no new acceleration sample**; the last real
acceleration remains cached by evdev. It does not fabricate zero gravity,
repeat a made-up stationary vector, or bypass a Steam readiness check.
Consumers may observe retained acceleration when receiving that final sync;
it is not a new physical reading. Disconnect still removes the node.

## Remaining axis evidence and activation gate

Our six qualitative movement recordings establish gyro directions, not a
complete accelerometer frame. A0/A1/A2 must not automatically inherit G0/G1/G2.
The new tests use `-3,1,-2` only as an **artificial permutation**, not as a
proposed hardware setting. The stored packet excerpt tests transport and
units but does not establish which direction gravity acts in on the device.

Before preparing an actual activation command, confirm the accelerometer
frame using existing evidence tied to known stationary poses, or obtain
separate permission for a short gravity-orientation check. This does not
require precise 90° gyro rotations, a new gyro factor or known-angle integration.
Keep the package and current installed path gyro-only until that mapping and
a separate installation/test approval exist. There is no ready-to-run module
load example with a guessed axis map in this document.

A later approved test must check actual acceleration at rest, nonzero and
correctly oriented movement in SDL, Steam gyro display/calibration behavior,
Eden motion and independently assignable paddles, normal inputs and output
ownership. Keep existing stop/reconnect/suspend regression and fallback rules.
A static nonzero-acceleration gate alone does not prove fusion will accept
incorrect units/axes or that a particular Proton game will use gyro.

## Reproduction (offline only)

```sh
make test
make test-sdl
make kernel
python -B scripts/analyze_kernel.py
python -B tests/run_sdl_sensor_test.py \
  --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0 --check-steam-layout
```

The last command requires the already reviewed stored SDL hash; it executes
SDL in the audited device-free Bubblewrap test, **not Steam**. No devices,
Steam process memory, sudo, network, preload into Steam or user settings are
part of these checks.

Pure conversion tests cover all 48 signed permutations, signed endpoints,
null/invalid metadata, integral/rational resolution and unchanged outputs on
failure. Extracted actual adapters test opt-in validation, gyro-only behavior,
six-axis registration/emission, shared timestamp and single sync, neutralization,
paired identity, independent FF and all paddle capabilities. The IIO harness
checks the actual producer passes the same six values/time to motion and IIO.

The new `experimental-six-axis` SDL case replays the existing reviewed small
IMU excerpt through the actual conversion functions with the artificial map.
SDL2/3 must expose both sensors with expected physical units; SDL3 events must
share sensor time. Both API tests retain all 32 A/paddle button combinations.
The original gyro-only case and Steam sensor-enable/cache-layout checks remain.
These are device-free integration tests, not live E2E acceptance.

Results and build limitations: [offline validation](steam-accel-extension-validation.json).
