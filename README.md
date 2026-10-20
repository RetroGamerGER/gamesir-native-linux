# GameSir Native Linux

⚠️ **WARNING: EXPERIMENTAL SOFTWARE**

This project is in a **PRE-ALPHA** development stage.

Intended exclusively for experienced Linux users and developers with a solid understanding of kernel modules, system recovery and debugging.

The driver is incomplete, has not undergone comprehensive hardware validation and may cause:

- Kernel crashes, freezes or boot failures
- USB/HID driver conflicts and device malfunctions
- Data loss or system instability
- Unexpected behavior after kernel updates

**DO NOT use on production-critical systems.**

Installation and use are entirely at your own risk.

No stability, compatibility or safety guarantees are provided.

## Project Goals

Our goal is to provide native, community-driven Linux support for GameSir controllers, including advanced features that are often unavailable through generic Xbox-compatible drivers.

The long-term ambition is to develop maintainable, upstream-quality support suitable for consideration in the Linux kernel.

The current implementation targets the GameSir G7 Pro over its 2.4 GHz USB
dongle. Wider device support and upstream inclusion are long-term goals,
not claims of current compatibility or acceptance.

## Acknowledgements / Special Thanks

- **[Deadband](https://github.com/broroeror/gamesir-linux-tools)** — for its
  work on GameSir controller support under Linux and valuable technical
  findings about device configuration, gyroscope functionality and trigger
  vibration.
- **[g7ctl](https://github.com/questionablesyntax/g7ctl)** — for openly
  documented research into GameSir G7 protocols and its value as a technical
  reference for this project.

These projects were used as **technical references only**. This
acknowledgement does not imply affiliation, participation, official
collaboration, endorsement, or support by their developers. Their code and
licenses remain their own; see the [provenance and licensing audit](docs/LICENSING.md).

## Project Status and Supported Scope

**Publication stage: PRE-ALPHA.** The source code is published in the
[public GitHub repository](https://github.com/RetroGamerGER/gamesir-native-linux).
Existing module/package version identifiers such as `0.1.0.alpha3` do not
change this status. [Tagged PRE-ALPHA source snapshots](https://github.com/RetroGamerGER/gamesir-native-linux/releases)
record their exact source and component-package versions.

| Device / environment | Evidence and limits |
| --- | --- |
| GameSir G7 Pro, 2.4 GHz dongle, observed `3537:100a` → `3537:109c` | Controlled native startup, gamepad input, raw IMU and individual motor tests recorded. No general firmware or edition guarantee. |
| G7 Pro Zenless Zone Zero edition, `3537:105e` | **Experimental:** a bounded native input/raw-IMU run and return to `xpad` were confirmed. Complete paddle, motor, Steam and long-term validation is still missing for this edition. |
| Garuda Linux with KDE Plasma, x86_64 | Recorded builds and controlled tests with `7.2.9-2-garuda` and `7.2.11-1-garuda`; feature coverage differs between recorded runs. |
| CachyOS Handheld Edition with Gamescope, x86_64 | Recorded builds and controlled tests with `7.2.9-2-cachyos-deckify` and `7.2.11-1-cachyos-deckify`; input/paddles and limited startup cases confirmed. Steam gyro has the startup/reconnect limits below. This is not a Valve SteamOS compatibility claim. |
| Other controllers, wired/Bluetooth operation, distributions and kernels | Not validated by this project's current hardware evidence. |

This matrix describes recorded configurations, not a minimum-kernel promise
or a guarantee for every later update. The [release audit](docs/RELEASE_AUDIT.md)
separates hardware results, offline tests and outstanding validation.

**Current source release: `v0.1.0-pre-alpha.3`; core recipe
`gamesir-native-dkms 0.1.0.alpha3-16`.** The package now supplies receiver
waiting as a vendor modprobe default. Service activation remains an explicit
installation step; no installation automatically starts or resumes management.
A same-name local override is preserved. See [installation](docs/INSTALLATION.md)
and [release notes](docs/RELEASE_PRE_ALPHA_3.md).

[Standalone acquisition](docs/STANDALONE_STARTUP.md) supports free interfaces
and scoped takeover from xpad without a global blacklist. Revision15's
receiver-only waiting and subsequent power-on without additional inputs passed
one CachyOS Gamescope test and were accepted by the maintainer. The receiver
re-enumerated and the manager acquired the new lifetime automatically. A brief
initial xpad contact was reported but not resolved by the status samples;
completely xpad-free first probing is not claimed. Cold-boot and repeated
lifecycle acceptance remain separate. [Function/commit audit](docs/FUNCTIONAL_INTEGRATION_AUDIT.md).

## Confirmed Hardware Results

- **Native gamepad input:** buttons, D-pad, both sticks and analog triggers
  were recorded through `gs_native`. The Linux input device is named
  `GameSir G7 Pro`.
- **Independent extra buttons:** L4, R4, L5 and R5 are separate Linux inputs
  alongside the normal buttons. For the standard model, all four were
  independently usable in Steam Input with the optional integration,
  including combinations and release events.
- **Standalone startup:** controlled standard-model tests started the native
  mode without Deadband. One tested boot required only turning on the
  controller afterwards; this does not establish universal boot reliability.
  Revision15 additionally kept an off-controller receiver in WAIT_RECEIVER=9
  beyond the old deadline, then reached active native input/IMU publication
  after one power-on without other inputs or manual Resume. This is one
  accepted late-power-on case, not a cold-boot/reconnect guarantee.
- **Four physical vibration motors:** the native driver sent separately
  captured commands to the left/right grip and left/right impulse-trigger
  motors. Three one-second pulses per motor were felt and stopped while
  input and raw IMU data continued. This proves the tested hardware commands,
  not universal game integration.
- **Motion data:** all six raw gyro/accelerometer channels were observed.
  Six gyro directions and a preferred 0.07 °/s/raw response were qualitatively
  tested in the local diagnostic window. One approved local test of the
  optional SDL gyro path in Eden's controller settings confirmed responsive
  motion, matching direction/sensitivity and four independently assignable
  paddles with ordinary input preserved. In-game acceptance remains separate.
  A later controlled test with optional real evdev acceleration confirmed all
  three gyro rates respond in Steam's UI, with ordinary input and independent
  paddles retained. This experimental profile is saved in a local opt-in.
  A subsequent CachyOS Gamescope reboot case succeeded with the controller
  already on before Steam started; late arrival and reconnect remain limited.
  Eden also passed the later Gaming Mode application test using the manual
  launch workaround below. A later maintainer report confirms gyro-as-right-stick
  camera control in Arc Raiders despite zero Steam gyro UI values. This remains
  a specific application report, not general Proton-game or lifecycle acceptance; no new physical calibration was performed. See
  [the activation record](docs/STEAM_ACCEL_EXTENSION.md).
- **Forza Horizon 6 through Xodus Nexus:** one controlled run of the optional
  trigger bridge `0.1.0.alpha1-2` produced felt effects on both impulse
  triggers, pauses between effects and renewed vibration on later effects.
  Normal inputs and grip rumble remained usable; both triggers were quiet
  after normal game exit. The explicit Forza profile uses LT 1x / RT 3x.
  This is a specific game/launcher result, not universal Steam/Proton support.

Individual evidence and its limits are linked from the
[release audit](docs/RELEASE_AUDIT.md). Historical reports remain available;
they describe their own test runs rather than the present state of a user's
computer.

## Known Limitations

- **Gyro integration remains experimental.** The selected 0.07 °/s/raw
  profile and experimental `8192 LSB/g` acceleration/axis mapping remain opt-in;
  the new packaged receiver-wait default does not enable them automatically.
  Steam's calibration display may remain zero although application gyro works,
  as reported with Arc Raiders. Eden's SDL path and its manual Gaming Mode
  workaround have separate accepted tests. For the established Gamescope gyro
  startup case, connect the controller before Steam starts. The successful new
  late native takeover is not a new Steam gyro/game test. Precise calibration
  remains paused; raw IIO is retained. See [SDL/Eden scope](docs/SDL_EDEN_GYRO.md),
  [Steam results](docs/STEAM_ACCEL_EXTENSION.md) and the [release audit](docs/RELEASE_AUDIT.md).
- **Receiver waiting has limited hardware acceptance.** One setup waits for
  fresh native IMU without repeatedly initializing the same instance. A new
  USB lifetime receives its own guarded startup. Waiting suspend/reset cancels
  the unready state; automatic recovery of that cancelled state is not implemented.
  Cold boot with the controller off, repeated RF/USB reconnect and long sessions
  require further acceptance. [Waiting contract](docs/RECEIVER_WAIT_KERNEL.md).
- **Trigger vibration has no confirmed universal games path.** Standard
  Linux `FF_RUMBLE` for the two grip motors is implemented and tested offline,
  with game-specified effect duration. Four-channel hardware support and the
  experimental application API do not automatically enable impulse triggers
  in SDL, Steam or Proton games. The [reviewed optional bridge](docs/TRIGGER_BRIDGE.md)
  has one successful integrated Forza/Xodus test after a failed first trial
  and an offline-tested correction. Steam/Proton integration, other game
  backends and automatic launcher setup remain unvalidated. Reconnect,
  suspend, process-crash and multi-device bridge acceptance remain open.
  The [offline Steam/Proton feasibility study](docs/STEAM_PROTON_TRIGGER_BRIDGE.md)
  identifies an SDL2 entry point and the remaining container, identity and
  Steam Input constraints; it does not enable the Steam adapter.
- **Steam paddles do not extend XInput.** Steam Input can map four independent
  sources, but a game's input API determines whether it can bind additional
  controller buttons directly. Universal in-game binding is not promised.
- **Eden in Steam Gaming Mode:** inherited SDL device filters can hide the
  physical GameSir, leaving Eden with a virtual Xbox controller without motion
  sensors. A manually configured, Eden-only workaround passed one CachyOS
  Gamescope application test with gyro and independent paddles. Follow the
  [tested steps and rollback](docs/SDL_EDEN_GYRO.md#manual-steps-for-the-tested-launcher-shape)
  for the matching shortcut type. This is a compatibility note, not an
  automatic installer or driver change; other controllers and duplicate input
  still require attention within the application.
- **Suspend/resume, repeated hotplug, many reconnect cycles, multiple active
  dongles and long-term operation are not comprehensively hardware-tested.**
  Revision 12 permits exact acquisition of free/xpad-owned `109c`; unexplained
  native or foreign owners remain excluded. General cold-start acceptance is pending. There
  are documented race limits during attach and fallback binding; revision 11
  narrows the initial xpad-detach race through exact-object kernel acquisition.
- A manager race could latch a newly reconnected `100a/xpad` instance as
  released after an obsolete status query. The local revision-6
  [reconnect correction](docs/MANAGER_RECONNECT_FIX.md) is offline-tested and
  installed locally. A subsequent native bootstrap succeeded; real reconnect
  acceptance remains pending separate approval.
- Earlier development included system freezes. A confirmed force-feedback
  teardown memory bug was corrected and regression-tested; that does not
  explain every earlier freeze or establish complete stability. An earlier
  short left-grip pulse was not felt; later successful longer pulses do not
  prove all short-duration behavior correct.
- Deadband must not concurrently own the same interface. Firmware flashing,
  automatic firmware updates and general controller profile editing are not
  release features of this driver.

See [runtime ownership rules](docs/ALPHA_RUNTIME.md),
[force-feedback API boundaries](docs/HAPTICS_API.md) and
[Steam/game API limits](docs/STEAM_PROTON_BUTTONS.md).

## Installation, Verification and Complete Removal

Read the [installation, verification, recovery and removal guide](docs/INSTALLATION.md)
**before installing anything**. It covers the core DKMS package, optional
Steam/KDE and CachyOS/Gamescope integrations, matching kernel headers,
explicit service activation, verification, fallback and removal of retained
state. No installer command is executed by reading this repository.

The optional packages are separate from the kernel driver:

- `gamesir-native-dkms` — kernel sources, session manager, packaged receiver-wait default and guarded removal.
- `gamesir-native-steam` — Steam paddle mapping for supported session starts.
- `gamesir-native-steam-gamescope` — additional integration for the tested
  CachyOS Gamescope session layout.
- `gamesir-native-trigger-bridge` — optional SDL2 trigger adapter with a
  limited Forza/Xodus hardware test; no automatic activation or launcher edits. See its
  [scope and validation boundaries](docs/TRIGGER_BRIDGE.md).

Installation and service activation are separate decisions. A successful
package transaction alone is not proof that DKMS built a loadable module.
Existing package hooks can rebuild boot images. Stop if validation or the
return to the normal driver fails; do not bypass the removal guard.

## Build and Offline Tests

From the project root of a **full source checkout**, with the required tools
already installed:

```sh
make test
```

This builds synthetic userspace tests and exercises fake device/process
backends. It does not load modules, change bindings or access controller
hardware. Optional module builds, static analysis and device-free SDL tests
are described in [TESTING.md](docs/TESTING.md).

The generated DKMS source archive is a deliberately smaller package-build
input; it does not contain the full test environment. Use the complete
repository source for `make test`. See the [build and package instructions](docs/INSTALLATION.md).

## License

GameSir Native Linux is licensed under **GNU GPL Version 2 only
(`GPL-2.0-only`)**. The complete license text is provided in [COPYING](COPYING).
The existing UAPI header exception is retained:
[`GPL-2.0-only WITH Linux-syscall-note`](LICENSES/exceptions/Linux-syscall-note).
Third-party notices and rights remain applicable. The
[licensing and provenance report](docs/LICENSING.md) documents these boundaries
and the requirements for considering a future Linux-kernel submission.

## Release Policy

The first tagged source release is explicitly labeled **PRE-ALPHA**, with
known limitations and exact source/package versions. Future releases and
GitHub pushes continue to require explicit maintainer approval.

The [publication/privacy check](docs/PUBLIC_RELEASE_CHECK.md) requires a
separate sanitized source snapshot. The private development history is not
approved for upload; source archives and future binary packages need their
own content and metadata review.

[Release audit and remaining publication gates](docs/RELEASE_AUDIT.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Protocol evidence](docs/PROTOCOL.md) ·
[Testing](docs/TESTING.md) · [Roadmap](docs/ROADMAP.md)
