# Functional integration and commit review — PRE-ALPHA.3

20 October 2026. File/history review only; no live host/device access.
The maintainer requested verification that previously implemented operational
features remain in the release. Reviewed the public base through `e2415a9`,
its unpublished descendants through `8fd923d`, and the revision16 package change.
No firmware/manufacturer binaries or private capture/helper folders are inputs.

## Operational feature map

| Feature / implementation checkpoint | Current implementation and distribution | Regression evidence / boundary |
| --- | --- | --- |
| Exact acquisition and startup (`5b14c85`, `057270a`, `9eaacad`, `ec7adf8`) | `kernel/gs_native_usb.c`, shared `src/gs_startup.*`, updated ctl and manager; core package includes all | startup/claim/shared-core and actual-kernel adapter tests; supports free or scoped xpad-owned interfaces, no global blacklist |
| Persistent receiver waiting (`159a83f`) | same kernel/core plus ctl pending9 and manager receiver_wait; revision16 vendor modprobe configuration | `test_receiver_wait.py`, startup/fake-kernel/client tests; accepted scoped revision15 waiting/late-on; cold boot/repeated cycles remain separate |
| Reconnect and first-error cleanup (`9dcd012`, `ac47724`) | manager lifetime/tokens/budget/return logic and kernel END; included core | `test_manager_reconnect.py`, `test_manager_standalone.py`, `test_service_manager.py`; unresolved109c return can need manual receiver removal |
| Normal input, naming and independent paddles | kernel gamepad/report parsing and telemetry keys704–707; preserved additional supported keys, no Xbox key sacrificed | parser/sensor/kernel regressions plus earlier human Steam/Eden acceptance; universal direct binding in XInput games is not promised |
| Coherent raw IMU and selected gyro profile (`18767d9`, `2f2271a`, `7e49d68`) | shared sensor decoder, kernel IIO buffer/timestamps, separate evdev motion device; core | sensor/coherent-stream/IIO/gyro tests; 0.07°/s/raw qualitative acceptance, precise calibration remains paused |
| Real acceleration and sensor publication (`738bfaa`, `f1f6c00`) | kernel six-axis motion and exact input publication, manager/udev readiness; core includes readiness helpers and udev rule | input publication/pair/manager/SDL contract tests; gyro+accel options remain explicit local opt-ins |
| Grip force feedback and four motors | kernel FF_RUMBLE, `src/gs_runtime.*`, native control ABI and haptics broker; core | runtime/lifetime/haptics/client tests; memless owns grip duration and renewals, no one-second game-effect cap; four-channel API retains bounded lease/stop safety |
| Trigger game adapter (`0a4012b`, `e264c1f`) | optional userspace `tools/trigger_bridge/` hook/relay/launch over core broker; separate package source | trigger hook/relay/lifecycle/pipeline/launcher/packaging tests; accepted limited Forza/Xodus run, Steam/Proton still feasibility-only |
| Steam paddles / Gamescope | `tools/sdl/gamesir_mapping.py` and optional Steam/session/Gamescope packages | mapping/session/packaging tests and prior hardware reports; external applications still choose APIs/mappings |
| Eden Gaming Mode fix (`4a23641`, `2e9c853`) | documented manual application-only environment correction | accepted human gyro/paddle application test; intentionally no kernel/installer shortcut mutation |
| DKMS, shutdown and safe removal | matching toolchain/source, package pretransaction guard, service stop and unused-module checks | toolchain/packaging/removal tests; matching headers and post-update validation remain mandatory |

## Findings

The reviewed operational implementations are present in current source and their
intended package boundaries. No missing runtime fix was identified by this review.
The remaining installation gap was the manually supplied receiver-wait option;
revision16 now owns a vendor default with mode0644 and local-override precedence.
The kernel parameter still defaults false when built/loaded outside that policy.
No forced receiver_wait service argument prevents opting out via configuration.
The package does not own existing `/etc` overrides and cannot clobber them.

"Present" does not mean all functions are enabled by installing the core:
Steam/Gamescope and the trigger game hook are separate optional components;
gyro/acceleration still require their documented opt-in. Research tools, browser
viewers and firmware studies are not driver startup dependencies. Bazzite/RPM,
firmware updater, Control Center and universal game-trigger support are not
implemented/validated release features. No experimental FF_TRIGGER_RUMBLE UAPI
or upstream patch is invented or activated.

Existing successful hardware reports retain their limited scope. The new
revision16 default is validated offline; the corresponding option/lifecycle
was tested separately on revision15. No new installation, module reload, game,
boot, motor or calibration test was performed for this source release.


## Completed offline checks for this candidate

Full make test: 1,339 Python cases across46 groups plus shared-core, actual
kernel-adapter, client and sanitizer checks pass. Packaged vendor configuration
is parsed with the real modprobe configuration-only mode; no module is loaded.
The full package regression retains guarded removal tests, mode/allowlist/license
checks and absence of installer/service autoactivation. The Garuda module build
passes with zero code diagnostics and its recorded compiler-version advisory.
Accepted CachyOS revision15 source hashes still match the unchanged kernel/core/
manager/client files. These are source/package checks, not new hardware tests.
