# Control Center — AppImage installation/removal binding

21 October 2026. **Offline implementation and acceptance preparation only.**
The earlier local package-helper setup succeeded under its own approval. This
step neither updates that helper nor invokes it. Installed alpha3-16, services,
modules, Steam and hardware remain unchanged. Gyro calibration remains paused.

## User flow and trust

An explicitly reviewed **build** can now include `reviewed-packages/` beside
its application entry. Opening that AppImage constructs `AppImageTransactions`
and schedules only passive inspection. It does not authenticate or submit a
package request. Ordinary source launch, generic builds without this directory,
`--demo` and `--rehearse-backend` retain their previous read-only/fixture modes.
A damaged/mismatching bundle shows a stable reason and locks actions; it never
falls back to a generic privileged command or a downloaded package.

The closed `profile.json` contains schema/scope, distribution/kernel and exact
fixed helper/policy/native/catalog hashes. It accepts no commands, arbitrary
paths, URLs or unknown keys. Package bytes use fixed component filenames and
pass the existing archive/identity/license/guard verifier. The catalog bytes
must match their independently reviewed helper pin. Reads are bounded, regular
files only, without symlink/FIFO traversal. The builder snapshots and embeds
only these known data/package files, not a source directory or local path.
Public/default binary catalogs remain empty; the private Garuda build contains
only the previously audited core alpha3-16, Steam alpha2-1 and bridge alpha1-2.
Gamescope/CachyOS deployment is not covered by this local bundle.

The GUI's data cannot grant the helper trust: the installed root helper still
uses its own protected catalog and repeats host/ALPM checks independently.
No AppImage code, Python runtime, user script or source path is run as root.
Missing/modified helper files stop before planning/authentication. Root code,
policy, wire format and the deployed helper are unchanged by this binding.
A first-time helper bootstrap inside the AppImage is **not** implemented here;
this review build requires the separately reviewed installed package helper.

## Preparation, selection and one-shot execution

1. The startup worker validates the bundle, attests the installed helper and
   obtains fresh matching unprivileged planning evidence. This is distinct
   from the display's metadata snapshot and opens no ALPM handle/lock/device.
   A different target/kernel, missing helper or inspection error locks actions.
2. Install/remove offers only reviewed candidates/installed versions. Same-
   version repair and unknown transitions are unavailable. An explicitly
   reviewed upgrade also needs a matching independently reviewed installed
   version record. Dependent components require explicit user selection;
   nothing is recursively selected or removed.
3. After selection, a second background worker reattests the helper and
   collects fresh evidence for **those exact selected components**. Properties
   and QML bindings read cached data and cannot trigger repeated host scans.
   Selection is frozen during this check. Cancellation discards late results.
4. The summary shows exact packages/versions, install hashes/source/tag, target
   kernel, hook effects and retained settings. No authentication or package
   submission has occurred yet. Cancel before submission sends nothing.
5. Only explicit confirmation invokes the already reviewed fixed package
   transport and registered desktop password window. The root helper checks
   again under the actual ALPM lock, commits once and verifies the result.
   Package hooks may stop/unload the native driver and run DKMS, snapshot or
   initramfs hooks. There is no automatic activation, Resume or reboot.
6. After possible effects, both actions stay locked. Display refresh does not
   manufacture a fresh transaction session. Review the outcome and separately
   inspect/reopen before another operation. An uncertain result cannot trigger
   retry, rollback or an automatic reinstall. Do not kill running package hooks.

Each real install and removal test requires its own explicit approval, closed
games/controller tools, fresh state and an exact component/version summary.
Removing the core with a bridge installed requires explicitly selecting the
bridge as well. Removal preserves the separate GUI/helper, dependencies,
local overrides/recovery evidence and Steam/application settings. Reinstallation
and driver activation are separate steps, never automatic rollback.

## Offline build and test

Build input is a privately maintained review directory, not a runtime CLI trust
file or an automatically generated release approval:

```sh
python -B scripts/package_control_center.py stage \
  --dest build/control-center-packages \
  --reviewed-packages /absolute/path/to/independently-reviewed-bundle
```

The builder still writes only a fresh non-system output directory; it changes
no desktop/menu entry. `BUILD_INPUTS.json` records the scoped package binding
and exact bytes with `release_ready: false`. A generic build omits this option.
The local glibc/Qt/runtime distribution limits in
[AppImage packaging](CONTROL_CENTER_APPIMAGE.md) still apply; no new binary
release or runtime redistribution approval is inferred.

Tests cover bounded/closed bundle input, wrong catalog/package/helper pins,
missing helper, changed/locked/stale planning, reviewed version transitions,
explicit dependent removal, selected package changes, confirmation expiry,
cancellation including late completion, unknown replies, one-shot locking,
entry routing and build-data copying. Actual QML tests exercise worker-thread
inspection, responsive cancellation, install/removal, password boundary,
DE/EN results and display refresh after possible effects. All inspection,
authentication and system edges are fixtures; protocol/executor paths are real.

`--bundle-package-self-test` adds a **synthetic** install/remove round trip to
the existing packaged status/DE/EN/render/runtime-isolation check. It ignores
the embedded real review directory, uses private temporary synthetic packages,
readers and transport, and makes zero privileged calls. It is not a real
installation/removal or password-window acceptance test. The ordinary
`--bundle-self-test` remains read-only. Neither flag is a live test instruction.

The local build reuses the exact hash-checked runtime bytes from the previously
verified AppImage. Its large container exceeded the builder's deliberately
bounded input limit, so a private small container was made from that unchanged
runtime plus an own marker squashfs. The runtime hash remained
`77f59c85aa4b171adf01d1870d86a53fcdeee7e27b31d119beb420dc4f140b66`;
no limit was bypassed or manufacturer application executed. Detailed build
provenance and machine-specific launch commands remain ignored/private.

Final offline checkpoint: **1,544 Python cases in 55 project groups**, plus
the existing C/actual-kernel-adapter/sanitizer checks, pass. Optional Qt suite:
**46 cases in four groups**, including six new actual-QML binding cases; the
new non-Qt binding suite has sixteen cases. The final type-2 AppImage passes
both packaged smoke lanes (status and synthetic install/remove), with bundled
Python/Qt only and zero privileged calls. The build remains private/local;
there was no real binding launch, authentication, installation/removal,
helper update, driver change or push. Source/diff/privacy checks and hashes
are recorded with the local commit; live acceptance is still pending.

## First live read-only plan review

Later on 21 October, the maintainer authorized opening the exact prepared
AppImage with genuine local facts and displaying a plan, **without** any
installation/removal or driver change. The image digest and passive checks
passed; Garuda x86_64 kernel/header release `7.2.11-1-garuda` matched the scoped
bundle, and installed helper pins matched. The observed project versions were
core alpha3-16, bridge alpha1-2 and Steam integration alpha1-1. The sole reviewed
installation candidate was Steam integration alpha2-1; existing core/bridge
same-version repairs were not offered.

The AppImage was opened normally. The maintainer confirmed the visible Steam
alpha2-1 plan and explicitly reported **not confirming it**. No password window,
submission, ALPM transaction/lock/handle, package hook, installation/removal,
helper/driver/service/module/Steam change or activation occurred. This accepts
live read-only planning/display only. Real installation and removal, and their
password/result behavior, remain pending separate approval. The plan may expire;
any later operation must use fresh evidence and confirmation. Private full
planning fingerprints, inventories and window logs remain ignored.

## First real optional-package installation

Later on 21 October, the maintainer explicitly approved exactly one fresh
AppImage install of Steam integration alpha2-1, including desktop permission,
with no removal or driver activation. Passive preflight checked the exact
AppImage/helper/package bytes and the sole selected Steam integration upgrade
from alpha1-1 to alpha2-1. The user rebuilt the GUI plan and reported
“package result verified / successful” after its confirmation path.

Independent passive postchecks confirmed installed alpha2-1 and all five
root-owned payload files, exact modes and bytes against the reviewed archive
`c72599c05cfa1d0cbacafb16814f50b1ac397b82de02c78544f4ba842208001b`.
Core alpha3-16, bridge alpha1-2, installed helper pins, native module metadata/
presence and service enablement were unchanged. No removal, driver activation,
Steam restart or automatic retry ran. Environment integration applies to later
sessions; this is not a new game/paddle/gyro/runtime acceptance. Full local
pre/post evidence remains private. This accepts one real optional-package
installation through the AppImage, not core install/removal, clean-system
helper bootstrap, remote/Gamescope authentication or every possible hook.
The operation approval is consumed; further package actions need their own
fresh plan and explicit authorization.

## Verified success feedback — offline UI refinement

The maintainer selected **only the operation dialog** to close after pressing
Done; the main window stays open. A verified real-package receipt now shows
“Successfully installed” or “Successfully uninstalled”, with DE translations
“Erfolgreich installiert/deinstalliert” and “Fertig”. The existing verified
result/no-automatic-activation explanation remains below the heading. Done
accepts/closes the dialog without another submission, activation or app exit.
No timer automatically dismisses the result. Failure, cancellation, unknown
completion and fixture rehearsal do not receive this real-success heading or
Done state; errors remain visible for inspection. Closing a failed dialog
cannot unlock a transaction after possible effects. During a running operation
close/confirmation remains disabled as before.

Actual-QML offline regressions check the DE successful-install heading and
Done label, closing only the modal, retained main-window visibility, a single
submission, the EN removal result and failure/uncertainty without a false
success or automatic dismissal. No further real package operation is used to
test this refinement; the already running earlier AppImage is not modified.

Refinement checkpoint: **205 focused non-Qt cases and 48 actual-Qt cases**
pass, plus the fresh AppImage's packaged synthetic install/remove smoke test
(bundled runtime only, zero privileged calls). The final bundled UI sources
match the working source. The new AppImage has not been launched in live mode;
no second real installation or removal was used for these checks.

## Steam-only removal and success-dialog live result

Later on 21 October, the maintainer authorized a fresh **read-only** preflight
and removal-plan display through the new AppImage, with no removal by the
agent. Image hash/helper/host checks passed. Installed versions were core
alpha3-16, Steam integration alpha2-1 and bridge alpha1-2. The prepared removal
plan selected **only gamesir-native-steam alpha2-1**, with package-metadata/
later-session-environment effects and no core cleanup/activation/reboot. The
maintainer confirmed the visible plan was initially unsubmitted.

The maintainer then independently completed the GUI removal and reported
“Successfully uninstalled”. The agent did not confirm or repeat the action.
Independent passive postchecks found the package absent and all five reviewed
payload files absent. Core/bridge versions, installed helper pins, native
module presence/version/source metadata/taint and service enablement remained
unchanged. No automatic reinstall, activation, Steam restart or further package
action was attempted. Full evidence remains private; no root log read was
needed. This result accepts only this optional-package removal, not kernel
module/DKMS/core cleanup, every hook, remote sessions or Gamescope behavior.

The maintainer also confirmed **Done closes only the operation dialog and the
main AppImage window remains open**. The real verified-removal heading and
requested modal-close behavior are therefore accepted in this scoped run.
Steam integration is currently removed; an already running session may retain
its inherited settings. Reinstallation or session changes require a fresh
explicit request and are not automatic recovery.
