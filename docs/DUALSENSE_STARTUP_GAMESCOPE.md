# DualSense startup as a Gamescope reference

20 October 2026. Offline source comparison added to the ongoing GameSir
first-start investigation. No PS5 controller was connected, opened or tested;
no Steam/Gamescope process, installed configuration or running driver changed.
The exact backend used by Steam for a real DualSense has not been observed.

## References and scope

Rechecked the existing local official Linux source at commit
[`a5ebb762`](https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c),
SHA256 `48a08dddf8d276a611195311a29cd4f113a949a1f5431ecc84b0396b106ec896`.
The local SDL 3.4.18 Linux backend at commit
[`829a65d7`](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/src/joystick/linux/SDL_sysjoystick.c)
matches SHA256 `4c787e35305b959a680c19aedc661e90000259d0f6d2a520a169dc6821067178`.
These are pinned references, not newly downloaded current upstream sources or
proof of the exact installed Sony driver. The saved
[CachyOS session contract](STEAM_GAMESCOPE.md#geprüfter-startvertrag) describes
the reviewed Steam launcher; a complete Gamescope source tree is not present.

The earlier [sensor comparison](DUALSENSE_SENSOR_COMPARISON.md) and
[two Steam input routes](STEAM_GYRO_FEASIBILITY.md#dualsense-comparison-two-input-routes-not-just-a-different-name)
remain applicable. Their historical GameSir sensor limitations predate the
accepted six-axis extension; current GameSir has both gyro and acceleration.

## Native Sony registration

1. `ps_devices[]` matches Sony DualSense/Edge identities on USB and Bluetooth;
   `MODULE_DEVICE_TABLE(hid, ...)` supplies HID autoload matching.
2. `ps_probe()` parses HID, starts HIDRAW support and calls `hid_hw_open()`.
   It then invokes `dualsense_create()`. There is no xpad dependency or
   GameSir-style `100a` to `109c` USB personality transition in this path.
3. Creation reads device identity, firmware and Sony calibration features.
   `ps_get_report()` checks response length/ID and, where requested on
   Bluetooth, CRC. Failure retrieving calibration aborts creation.
4. `ps_gamepad_create()` and `ps_sensors_create()` register separate input
   devices. The sensor node declares `INPUT_PROP_ACCELEROMETER`, six ABS axes,
   positive unit resolutions and `MSC_TIMESTAMP`. Both inherit the same
   `hdev->uniq`, set from Sony's read device identity.
5. `dualsense_parse_report()` validates the Sony USB or Bluetooth report,
   converts gyro/acceleration and emits sensor events with a device-derived
   timestamp. Bluetooth report CRC is checked separately.

This source does **not** wait for a first IMU sample under a three-second
startup deadline before registering the Sony gamepad. Registration and actual
first sensor delivery remain different facts. Gamepad registration precedes
sensor registration in the creation function; the pair is not atomically
published. Sony's sequence is therefore not evidence that merely changing our
registration order or copying a constant would solve a GameSir timeout.

## SDL and Steam in a Gamescope session

In the reviewed general SDL Linux path, `GetSensor()` pairs gamepad and motion
nodes by equal `EVIOCGUNIQ`. Opening/configuring the joystick discovers the
six-axis capabilities and their resolutions. Enabling sensors opens the sensor
evdev node for reads. This path does not send Sony commands or use xpad.
GameSir already provides the same kind of paired evdev interface, with its own
identity and units. Raw IIO remains a separate diagnostic interface.

Steam/SDL also has Sony-specific HID support. The saved dispatcher contains
`SDL_HIDAPI_DriverPS5`, but the PS5 implementation file is absent from the local
subset. Do not claim a complete HIDAPI startup reconstruction or that Steam
always chooses evdev instead of its Sony-specific route. The saved Gamescope
launcher starts Steam; it is not evidence of a special compositor-level sensor
enrollment step. Access, backend selection and actual late-device behavior
still need separate application evidence.

## The useful lifecycle difference

A DualSense attached through the host's Bluetooth stack is a controller HID
connection. Our G7 radio controller is behind a USB receiver whose enumeration
can precede RF readiness. The receiver's presence or native PID alone is not a
sensor-ready contract. This is an architectural distinction, not a measured
claim about the first failing GameSir radio connection.

An early logical gamepad can also be published before the final GameSir sensor
pair. Saved journals show xpad registering its gamepad before native acquisition.
Our own `gsn_input_register()` also registers the transitional `100a` gamepad:
deferred gamepad publication currently applies only to persistent, six-axis
`109c`. Thus early application discovery is not specific to the xpad name.
This is a concrete timing lead for Steam's downstream device association, not
proof of its selected backend or the cause of the earlier raw IMU timeout.
No transitional input-publication behavior is changed by the manager fix.

The **DualShock 4 dongle**, in the same Sony source, is an even closer receiver
analogy. `dualshock4_dongle_parse_report()` reads its defined connection bit
from an otherwise mostly-zero report. It separates disconnected, calibrating,
connected and disabled states, schedules its own calibration worker on a
connection transition, and gates controller report processing accordingly.
That is PS4 behavior, not a discovered PS5 dongle protocol. Its status bit,
report offsets and calibration requests have no demonstrated GameSir meaning.

## Consequences for GameSir

- Preserve the working paired six-axis contract, native USB owner, paddles,
  IIO and haptics. No Sony identity, calibration data or HID request is imported.
- Treat dongle discovery, controller connection, initialization and publication
  as separate states. A known GameSir RF-ready indication would be more useful
  than a required button press or an arbitrary boot sleep.
- The saved first-failure logs contain no accepted IMU/pad or transport error;
  they do not identify RF readiness. No equivalent connection bit is proved.
  Do not implement guessed packet recognition or initialization retries.
- Fix the independently reproduced manager suppression of the verified new
  returned `100a` through normal fresh discovery and existing budgets. Keep the
  old timeout and cleanup proof; this is not a solution for the old instance's
  missing first sensor sample.

The [first-start report](REVISION13_FIRST_START.md#offline-manager-correction--20-october-2026)
records that narrow correction and the added sensor-timing tests. The PS5
comparison supports a readiness/lifetime design direction; it does not prove
hardware startup or unrestricted Steam/Gamescope gyro reliability.

## Manager architecture review after the controller-off reboot

20 October 2026. This follow-up reads only the same hash-verified Sony/SDL
snapshots, current project sources and saved revision-14 reboot evidence. No
network, SSH, manufacturer application, device access or installed change.
Reference hashes above still match. No new Sony hardware test was performed.

**Decision:** keep a thin manager for the pre-alpha's explicit, per-device
ownership and administrative policy. The present manager/kernel startup
contract is insufficient for an always-present receiver with an absent radio
controller. Prefer kernel ownership of the normal receiver/link/runtime
lifecycle, with a manager that supervises rather than repeatedly restarts it.
Removing the manager alone, or adding more retries, does not fix this defect.

### What the source comparison actually establishes

| Case | Binding and startup | No active controller / subsequent connection |
| --- | --- | --- |
| DualSense USB / Bluetooth | `ps_devices[]`, HID modalias and `ps_probe()` bind `hid-playstation`; identity, firmware and calibration requests run in kernel. No equivalent GameSir takeover manager or xpad dependency. | Bluetooth HID connection is the controller connection; do not treat its presence as an always-present vendor receiver. Creation does not require first IMU data under our VERIFY deadline. |
| DualShock 4 USB dongle | Same HID driver, with `dualshock4_create()` selecting a dongle parser and initializing `DONGLE_DISCONNECTED`. Gamepad and sensors are registered during creation, not recreated on every RF connection. | The dongle sends reports even without a controller. Its defined status bit drives disconnected/calibrating/connected/disabled states. A connection schedules the calibration worker; processing is gated until ready. The receiver remains bound. |
| Current GameSir persistent mode | systemd loads `gs_native`; the manager validates and claims exact IF0, then invokes kernel bootstrap. No generic USB modalias is exported. Existing xpad ownership can be handed over locally. | `109c` discovery immediately starts bootstrap. Missing fresh IMU expires VERIFY and becomes terminal; manager then attempts its guarded return path, which can block if the same native personality remains. There is no explicit healthy receiver-wait state. |

Sony source landmarks at the pinned commit: `ps_probe()` 2875,
`ps_devices[]` 2937, `dualsense_create()` 1737, `dualshock4_create()` 2723,
`dualshock4_dongle_parse_report()` 2599 and
`dualshock4_dongle_calibration_work()` 1912. See the
[official source](https://github.com/torvalds/linux/blob/a5ebb76233b79db01e82e061173cb73c6d2b5c6b/drivers/hid/hid-playstation.c).
The Sony status mask, feature requests and calibration data are not GameSir
protocol evidence and must not be copied. The PS4 source also records limited
retries for competing HID feature reports from userspace; that is not a
justification for repeating GameSir initialization or sharing raw USB writes.

### Why our observed failure is a joint contract problem

- `Manager.tick()` claims a discovered direct-native device and calls
  `begin_bootstrap()` without a proved radio-ready event. The 100a status path
  likewise starts on valid passive state; requiring a button was deliberately
  removed and must not return as a workaround.
- `gs_boot_begin()` starts native initialization; `gs_boot_next()` enters
  VERIFY after its six initialization steps. `GS_BOOT_VERIFY_US` is three
  seconds. Only fresh accepted IMU data yields READY; silence, vendor frames
  and normal pad reports alone do not. `boot_fail()` is terminal and retains
  the first stage/error. This deadline is in the shared kernel-used core,
  not a systemd, Steam or Python timeout.
- `return_one()` is deliberately cautious. An unchanged native `109c` is not
  proof of a return to `100a`; the manager eventually blocks rather than
  guessing a reset/mode command. Revision 14 permits fresh discovery only
  after an attested ended timeout and an independently observed new
  `100a`/xpad replacement. That condition is absent in the saved reboot case.
- The runtime already has a useful separation: `gs_runtime_check_idle()`
  neutralizes stale input/motors while retaining the persistent session and
  identity. Initial startup has no corresponding receiver-wait contract.

The saved reboot therefore proves correct service/module autostart and a
failed startup contract under the reported controller-off condition. It does
not prove that manager scheduling alone causes missing RF data. Merely moving
unchanged code into the kernel preserves the same failure.

### Recommended responsibilities

| Component | Keep / target responsibility |
| --- | --- |
| Kernel driver | Exact receiver lifetime, USB RX/TX and known initialization, radio/data readiness evidence, gamepad/sensor events, haptics, STOP/neutralization and suspend/disconnect. Normal waiting/reconnection must not depend on a long-running root child client. |
| Thin manager | Explicit enable/pause/release, scoped acquisition from a competing driver while needed, per-instance ownership proof, diagnostic history and controlled administrative recovery. Start permission must remain separate from cleanup permission. |
| Userspace integrations | Steam mappings/session access and application launch compatibility; Forza trigger bridge stays userspace. These do not establish RF connectivity or decide whether a bootstrap succeeded. |

Long-term kernel modalias/native binding is a separate staged improvement.
Today aliases are intentionally omitted, and probe requires a consumed exact
claim or correlated handoff. Adding aliases alone does not remove those gates
or resolve competition with xpad. Do not blacklist xpad globally or remove the
existing ownership checks as part of this analysis.

### Required state contract before another implementation

Separate receiver acquisition, receiver initialization, waiting for controller,
controller initialization, running, quiet-link waiting, and genuine transport/
protocol fault. A waiting state may last until the user powers on the
controller; one initialization transaction still needs finite transfer bounds.
Waiting must not consume a new start budget on every scan, replay init packets,
run motors, create endless subprocesses or extend an uncertain failed request.
Pause/release, USB removal and suspend must remain available during waiting.

**Do not equate silence with a confirmed radio disconnect.** Without a proved
GameSir RF-status field, report link state as unknown/awaiting data. Conversely,
a matching PID, USB transfer completion or a zero-valued pad is not proof of a
connected, ready controller. A valid sensor sample is readiness evidence,
not the device's identity. A quiet controller must need no button or stick move.

There are two possible evidence-backed designs, not interchangeable promises:

1. If saved reports reveal a reliable pre-initialization connection indication,
   gate controller initialization on that indication and a fresh exact lifetime.
2. If data becomes available only after known receiver initialization, split
   receiver setup from controller readiness, keep one known receive context,
   and wait for later valid data without replaying initialization. Any required
   maintenance traffic must be separately justified by saved evidence; do not
   assume that indefinite heartbeats or entirely passive waiting will work.

No reliable GameSir equivalent of the Sony connection bit or proof of the
second design's controller-off/late-on behavior has been established here.
This is the remaining protocol/readiness question; a longer three-second
window merely moves the same problem to users who turn on the controller later.
Do not turn malformed input, USB errors or uncertain STOP/END into harmless
waiting, and do not erase the original error of an already failed instance.

The existing paired six-axis evdev/IIO interfaces and tested scaling stay
unchanged. Sony registers devices before a first motion report, including on
its receiver path; therefore withholding every input node until first IMU is
not a universal Linux requirement. Our current Steam publication gate is a
separate integration choice. Review it deliberately later; do not discard it
or blame it for this lower-level VERIFY timeout without evidence.

### Verification and next boundary

Re-ran the existing 56 standalone-manager tests and the real shared-C startup
suite with ASan/UBSan. All pass, including seven direct sensor timing cases:
silence/vendor-only/pad-only time out, valid IMU before deadline succeeds
without a button, malformed data fails, and late data cannot reopen failure.
These characterize the current contract; passing them does not fix or accept
the controller-off boot. No production code or test expectation changed.

A later implementation needs offline tests for receiver-only waiting well
beyond 3/30 seconds, late first valid data without a button, same-instance RF
loss/reconnect, replacement/hub lifetime changes, pause/release while waiting,
suspend/resume, cancellation, malformed/transport errors and independent motor
STOP. Only separately approved hardware trials can validate the unknown radio
behavior and boot/late-on/reconnect on both target environments. The installed
blocked instance is untouched and its recovery remains unconfirmed. No push.

## Saved-capture connection chronology — 20 October 2026

The maintainer requested searching existing evidence for a connection witness,
then emphasized comparing the whole sequence, not hunting one byte. Ten
original USB captures were rehashed against retained audits. Nine contain
identified target traffic; one window contains no identified target records. They include
five native `109c` epochs, four with the native USB enumeration visible and
one already streaming at capture start. This is an inventory of the selected
USB corpus, not a claim that every project test recorded USB packets.

The scanner reads regular PCAPNG USB_LINUX_MMAPPED records, keeps successful
interrupt completions separate from submissions/errors, and assigns epochs
from saved initial identities plus observed target descriptors. Endpoints are
kept distinct. Independent `tshark -n -r` checks match 106 selected frame
payloads, lengths, endpoints, stages and relative timestamps across the nine
nonempty captures. Raw reports, device identifiers, bus addresses, absolute
times and unrelated traffic remain private. No capture/SSH/network or device
operation was performed.

### Repeated order in four fresh native USB epochs

**Time zero is the first captured descriptor for the new `109c` address.** It
is neither the moment the user powered the radio on nor physical receiver
insertion. Values below are host milliseconds. OUT is the first recognized
captured GIP initialization submission in that epoch; the IN columns are
successful completions. Frame references are descriptor / first candidate /
first GIP pad / first IMU in the original.

| Capture | First init OUT | First previously unclassified IN | First GIP pad | First IMU | Frames |
| --- | ---: | --- | ---: | ---: | --- |
| A | 117.756 | `03 20 seq 04`, 167.750 | 169.785 | 739.798 | 32728 / 32857 / 32861 / 33554 |
| B | 118.691 | `02 20 seq 1c`, 127.728 | 187.730 | 719.742 | 22238 / 22343 / 22395 / 22692 |
| C | 119.729 | `03 20 seq 04`, 164.733 | 166.769 | 680.797 | 26601 / 26710 / 26716 / 27007 |
| D | 118.810 | `02 20 seq 1c`, 118.765 | 122.787 | 728.807 | 29504 / 29633 / 29645 / 30312 |

Thus all four show candidate report → GIP pad → IMU. Pad-to-IMU delay is
514.028–606.020 ms. These are real observed events, not a synthetic stitched
startup. They are native personality transitions from the saved Deadband runs,
not isolated radio-off/late-on experiments. In A/B/C initialization has already
started before the candidate report. Only D's candidate precedes its first
recognized init submission, by 45 microseconds in the host trace. This does
not establish firmware causality or a universal pre-init connection trigger.
Some epochs contain multiple initialization sequences from existing software;
this analysis neither replays nor endorses those sequences.

| Label | Original capture label | SHA-256 |
| --- | --- | --- |
| A | `20261011T133916365243Z-measurement-B-deadband` | `192200c431e8ef767ed872f79a658803418a68b991a60474aeac071575226628` |
| B | `20261011T134320608606Z-measurement-B-deadband` | `d9613598e5a22a7e3732a5bcda295c97df5f67890db47ec196c67ff7c805ed17` |
| C | `20261011T141131938846Z-measurement-B-deadband` | `4045577a7a9e7a1a0f84307a45e96fd524cd7dea1d4af276ebd7db20a0994a89` |
| D | `20261012T165154770784Z-motor-comparison-deadband` | `140c658b3615a7aa9e04571503d9f4fe1cb13df000ef3f8cb35cec91533ae954` |

### Candidate interpretation and counterchecks

- **Type 03:** 51 successful eight-byte reports across the five native epochs,
  all with the same payload `87 00 00 00` after the four-byte header. It recurs
  approximately every 20 seconds after startup bursts. It is not an exclusive
  connection edge or a demonstrated initialization ACK. The saved SDL GIP
  source calls type 03 device status and handles battery/power information.
  Its interpreted device-active field is not set by this observed payload;
  that generic interpretation must not classify our demonstrably functioning
  GameSir as disconnected. Current GameSir `gs_decode()` leaves type 03 unknown.
- **Type 02:** two successful 32-byte native reports, at B frame 22343 and D
  frame 29633. The saved xpad source names type 02 `GIP_CMD_ANNOUNCE`; SDL GIP
  names it HELLO_DEVICE. Full payloads include identifying material and stay
  private. This is the strongest explicit announce candidate, but not yet a
  proved RF connection transition. It is absent from the other two captured
  native-enumeration starts. Do not require it universally or send an unknown
  response to it.
- **Already-streaming counterexample:** the native motor capture SHA256
  `ec53d79ba5ee46ccefb4df2cc1b6c67c0d083eafdf6e1d3a52258e80a338d998`
  starts with IMU at frame 1. Its first type-03 status is frame 9278, 7.548140 s
  later, and first pad is frame 34169, 39.720933 s later. A receiver already in
  native streaming state must not require a new announce or pad as its first
  packet. Recorded current-window initialization also occurs after that IMU.
- **HID endpoint counterexample:** the returned `100a` epochs contain 1, 2 and
  11 IMU-shaped reports on endpoint `0x84`, not native endpoint `0x82`.
  Passive HID tests also contain 13-byte key press/release reports. Reusing
  opcode 03 or finding an IMU-shaped payload without PID/interface/endpoint,
  lifetime and timing checks is not a valid native readiness witness. These
  short bursts do not prove a continuously live radio stream.
- **Earlier-corpus negative coverage:** the ten captures above have no synchronized, human-labelled
  radio-off then radio-on window with raw packets on both sides. The failed
  controller-off reboot retains aggregate kernel status, not the USB payloads.
  The first passive HID trial has no ordinary XInput reports despite the user
  exercising inputs; its evdev/KDE test was not open. Missing reports there
  must not be relabelled as a confirmed radio-off control.

The later approved radio-on reference is reviewed separately in
[RF_LINK_CONNECTION_WITNESS.md](RF_LINK_CONNECTION_WITNESS.md). It starts at
109c but naturally re-enumerates to 100a; eleven neutral XInput reports precede
changed user input, with a 34.707839-second gap. It adds a labelled power-on
window but no paired 100a radio-off baseline or proved pre-button RF-ready bit.
Do not merge that run's XInput/HID reports into these native GIP timelines.

### Existing reconnect logs and the xpad analogy

The retained 14 October radio-reconnect observation has explicit human
confirmation that the radio controller went off while the dongle stayed
plugged. Its 217 manager observations and associated saved kernel messages
show an old native USB disconnect, a new `109c`, later a new `100a`, then a
new initialized `109c` and active state. Raw USB payloads were not recorded in
that observation, and the human off-confirmation has no precise packet-clock
marker. It nevertheless establishes that a user RF cycle can accompany USB
re-enumeration without physically moving the dongle. A future waiting design
must handle both same-enumeration data arrival and a fresh USB lifetime.
These logs are not a raw-message connection-bit proof.

There is a directly relevant **existing xpad design**, beyond Sony's analogy:
its `xpad_prepare_next_init_packet()` comment says some dongles discard init
before the controller connects. `FLAG_DELAY_INIT` waits for ANNOUNCE before
starting the sequence. In the inspected file this flag is attached to ByoWave
Proteus, not established for our G7. This supports investigating an event-
triggered start; it does not authorize adding the flag/packets or prove that
our type-02 frame has identical RF semantics.

Local reference files used here are identified by SHA256: xpad
`19dd00fc4b0341ef18575a87b9b3fbd5f809e4588ff2909e2c357af2f2358517`
(byte-identical in the existing Linux and Linux-7.2.9 caches; stable snapshot
metadata names `5fce161649b4d779d1b76d9fcd52dc77779774b8`) and SDL HIDAPI GIP
`d4a92cddb5cdd0bdb2f08434ce0d7c10ac9d47601ad030b65b3a4989ff2f4dec`.
The SDL GIP file is absent from the previously verified sensor-file manifest;
its directory snapshot metadata is not independent per-file commit proof.
These are offline reference observations, not a newly verified upstream HEAD
or proof of the running kernel/Steam backend.

### Result for the proposed wait contract

**Found:** a repeatable startup chronology, earlier-than-IMU status/announce
candidates, regular status cadence, an already-streaming exception and RF-
associated USB replacement history. **Not yet proved:** a mandatory, sufficient
pre-init RF-connected signal, its disconnected counterpart, or that one init
while off will enable a later controller without further initialization.

Use the chronology as evidence for separate receiver/initializing/awaiting-
data/running states. Do not promote these candidates to connected/ready or
weaken the existing ownership/IMU/error checks. The observed repeatable order
is a lead, not a reliable radio state machine by itself. No production change,
USB command, new hardware attempt or push follows from this search.

## Online GIP sequence cross-check — 20 October 2026

The maintainer explicitly authorized public online research after the local
chronology search. Only public documents/source were retrieved; no private
capture, firmware or device identifier was uploaded. No SSH, controller access,
installation, driver/Steam configuration or live experiment occurred.

### Published order and executable reference behavior

Microsoft publishes [MS-GIPUSB revision 1.0](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gipusb/e7c90904-5e21-426e-b9ad-d82adeee0dbc),
with a [startup-sequence reference](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gipusb/d50b090d-6218-4165-b097-5c23b23e02b9).
The useful message-specific requirements are:

- [Hello Device](https://learn.microsoft.com/fr-fr/openspecs/windows_protocols/ms-gipusb/767240e3-ec9e-443e-b364-9cfba82b9fe6):
  type 02, flags 20, 28-byte payload; the device should repeat it at 500 ms
  until metadata request or START. Its fields include device ID, VID/PID,
  firmware/hardware and protocol versions. This is generic GIP, not a
  GameSir-specific radio/off trace.
- [Set Device State](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gipusb/8eaad00e-97e6-4ae0-86fa-471131649d70):
  `05 20 seq 01 00` is START. This matches our already captured init command;
  no new request is proposed or sent.
- [Status Device](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gipusb/97ec033b-af57-4dad-9b6c-580bdd1b2971):
  connection/reconnection status follows START; status normally should not
  precede it, except during power-off/reset. Periodic updates later settle
  to 20 seconds. Thus status is post-START evidence, not a mandatory pre-init
  trigger. Our observed cadence agrees in that limited respect.

The downloaded SDL Xbox One backend explicitly maps ANNOUNCE to its announced
initialization state. It also treats the first input during initialization
cautiously. The separate xone handler requests identification on ANNOUNCE;
its type-03 handler tests `GIP_STATUS_CONNECTED`, defined as bit 7 of the first
payload byte. These are two implementations, not one interchangeable captured
GameSir handshake. Neither makes IMU a generic GIP registration requirement.
[xone pinned source](https://github.com/medusalix/xone/blob/3484f603484782dd7551c64e5a33fc602b127051/bus/protocol.c),
[SDL pinned source](https://github.com/libsdl-org/SDL/blob/3b2bc951500ca6a1f428af77e036e732d9a8afe3/src/joystick/hidapi/SDL_hidapi_xboxone.c).

These source files were fetched at resolved repository commits and SHA256
checked, retained privately as references, never executed/copied into the driver:

| Reference | SHA-256 |
| --- | --- |
| xone protocol.c, `3484f603` | `08bc9980acdf3346a6ca5fda9a0e5ca1a87deb1ec44e1d00e356bfb2ec1a235d` |
| SDL Xbox One backend, `3b2bc951` | `89b7fe267431f61b63d464ab8744974a202c10fab2292468f42d19d846618f63` |

### Stronger interpretation of our existing packets

Both 32-byte candidate reports (B frame 22343, D frame 29633) match the
Microsoft Hello layout, including `3537:109c`, firmware/hardware field layout
and RF/security/GIP version pairs 1.0. Identifying bytes stay private. This is
more than an opcode guess: these are structurally supported **GIP Hello**
reports. It does not identify which physical RF/receiver transition caused them.

All 51 captured eight-byte status reports have bit 7 set in payload byte zero
(`0x87`). That matches xone's positive connected interpretation. The previously
noted SDL extended device-active field is a different field; its zero value
must not be confused with xone's connected bit. There is still no captured
bit-7-clear radio-off contrast or proof that an unpaired G7 receiver cannot
emit the same positive status. Keep this as a source-backed connected-status
candidate, not an installed production decision or an IMU-ready/ACK claim.

The refined local order below adds first STATUS and the next START after
HELLO, rather than conflating all initially unknown reports. Times are still
milliseconds after the first native descriptor in the earlier table:

| Capture | Hello | Selected START | First status | First pad | First IMU |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | Not observed | 117.756 (first) | 167.750 | 169.785 | 739.798 |
| B | 127.728 | 184.705 (first after Hello) | 185.701 | 187.730 | 719.742 |
| C | Not observed | 119.729 (first) | 164.733 | 166.769 | 680.797 |
| D | 118.765 | 118.810 (first) | 120.748 | 122.787 | 728.807 |

Every first status in these four windows follows at least one captured START.
B also has earlier START submissions before Hello; the table does not erase
those. D's Hello-to-START interval is 45 microseconds, consistent with a prompt
host response, but timing alone does not prove the responsible software path.
These checks add two complete Hello-field validations and 51 positive status
bit checks to the previous 106 independent packet/timestamp crosschecks.

### Public GameSir recordings: what was and was not found

The checked [Deadband research](https://github.com/broroeror/gamesir-linux-tools/blob/main/RESEARCH.md)
and [g7ctl protocol notes](https://github.com/questionablesyntax/g7ctl/blob/main/PROTOCOL.md)
document GameSir traffic and the configuration transition. g7ctl explicitly
limits some identity/return observations to wired hardware; do not transfer
those unconditionally to our receiver. The checked
[PandaPro8K protocol notes](https://github.com/Ab0ut47Pandas/PandaPro8K/blob/main/PROTOCOL.md)
cover a different 8K HID/identity path. None of these checked pages supplied a
raw, synchronized `109c` receiver-only boot → radio-on trace matching our case.
That is a bounded search result, not a claim that no such recording exists.
No author was contacted and no proprietary data was uploaded.

### Consequence for the next offline design

There is now a documented generic route: Hello/announce → host START (optional
metadata depends on protocol support) → status/input; GameSir IMU readiness is
an additional vendor stream, not the definition of USB receiver existence.
Waiting for type 03 before sending START can deadlock. Waiting exclusively for
Hello can also strand the already-streaming case and starts whose Hello was
consumed by another owner. Keep those paths distinct and preserve exact native
ownership rather than replaying initialization on every report.

Recommended next work is a **passive offline event/state prototype** recognizing
these confirmed message structures while preserving unknown link state,
boot/instance identity, cancellation and terminal protocol errors. It should
model announce-led start and an already-active stream separately, without
claiming that mere silence or USB enumeration proves connection. A new real
receiver-off/late-on trace or equivalent direct evidence is still needed before
claiming the proposed trigger universally works on GameSir. No such prototype,
installation or hardware trial is performed in this research step; the current
blocked target is untouched. Public push remains deferred.

Follow-up: the separately authorized [passive offline prototype](STARTUP_TIMELINE_PROTOTYPE.md)
is now implemented and tested against five historical metadata timelines and
23 private saved payloads. It still grants no live start/ownership authority;
the previous paragraph records the research checkpoint before that work.
