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
change this status. The first tagged PRE-ALPHA source release is
[`v0.1.0-pre-alpha.1`](https://github.com/RetroGamerGER/gamesir-native-linux/releases/tag/v0.1.0-pre-alpha.1).

| Device / environment | Evidence and limits |
| --- | --- |
| GameSir G7 Pro, 2.4 GHz dongle, observed `3537:100a` → `3537:109c` | Controlled native startup, gamepad input, raw IMU and individual motor tests recorded. No general firmware or edition guarantee. |
| G7 Pro Zenless Zone Zero edition, `3537:105e` | **Experimental:** a bounded native input/raw-IMU run and return to `xpad` were confirmed. Complete paddle, motor, Steam and long-term validation is still missing for this edition. |
| Garuda Linux with KDE Plasma, x86_64 | Recorded builds and controlled tests with `7.2.9-2-garuda` and `7.2.11-1-garuda`; feature coverage differs between recorded runs. |
| CachyOS Handheld Edition with Gamescope, x86_64 | Controlled startup/input testing with `7.2.9-2-cachyos-deckify`, Steam paddles and one boot followed by controller power-on confirmed. This is not a Valve SteamOS compatibility claim. |
| Other controllers, wired/Bluetooth operation, distributions and kernels | Not validated by this project's current hardware evidence. |

This matrix describes recorded configurations, not a minimum-kernel promise
or a guarantee for every later update. The [release audit](docs/RELEASE_AUDIT.md)
separates hardware results, offline tests and outstanding validation.

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
- **Four physical vibration motors:** the native driver sent separately
  captured commands to the left/right grip and left/right impulse-trigger
  motors. Three one-second pulses per motor were felt and stopped while
  input and raw IMU data continued. This proves the tested hardware commands,
  not universal game integration.
- **Raw motion data:** all six gyro/accelerometer channels were observed.
  Physical sensor axes, bias and the gyro scaling factor are not calibrated.

Individual evidence and its limits are linked from the
[release audit](docs/RELEASE_AUDIT.md). Historical reports remain available;
they describe their own test runs rather than the present state of a user's
computer.

## Known Limitations

- **Gyroscope calibration is paused.** Raw data is available, but calibrated
  SDL gyro output and gyro-enabled game compatibility are not confirmed.
  `8192 LSB/g` remains an experimental accelerometer assumption, not a gyro
  factor. The newer coherent IIO buffer defaults to disabled and has not yet
  completed a real buffered reference measurement.
- **Trigger vibration has no confirmed universal games path.** Standard
  Linux `FF_RUMBLE` for the two grip motors is implemented and tested offline,
  with game-specified effect duration. Four-channel hardware support and the
  experimental application API do not automatically enable impulse triggers
  in SDL, Steam or Proton games. A separate Forza/Xodus bridge recorded felt
  LT/RT game effects; the [reviewed integration](docs/TRIGGER_BRIDGE.md) is
  offline-only and still needs its own hardware acceptance. Steam/Proton
  integration and automatic launcher setup remain unvalidated.
- **Steam paddles do not extend XInput.** Steam Input can map four independent
  sources, but a game's input API determines whether it can bind additional
  controller buttons directly. Universal in-game binding is not promised.
- **Suspend/resume, repeated hotplug, many reconnect cycles, multiple active
  dongles and long-term operation are not comprehensively hardware-tested.**
  A pre-existing unowned `109c` session is intentionally not seized. There
  are documented race limits during initial takeover and fallback binding.
- A manager race could latch a newly reconnected `100a/xpad` instance as
  released after an obsolete status query. The local revision-6
  [reconnect correction](docs/MANAGER_RECONNECT_FIX.md) is offline-tested;
  its installation and real reconnect acceptance are still pending.
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

- `gamesir-native-dkms` — kernel sources, session manager and guarded removal.
- `gamesir-native-steam` — Steam paddle mapping for supported session starts.
- `gamesir-native-steam-gamescope` — additional integration for the tested
  CachyOS Gamescope session layout.
- `gamesir-native-trigger-bridge` — optional, offline-prepared SDL2 trigger
  adapter; no automatic activation or launcher edits. See its
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
