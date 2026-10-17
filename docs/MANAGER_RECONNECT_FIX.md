# Manager reconnect correction — local update and acceptance status

Date: 2026-10-17. PRE-ALPHA. The correction was developed and tested offline,
then installed locally under separate explicit authorization. Installation
verification is recorded below; no resume, bootstrap, live reconnect or Forza
test has followed it. Gyroscope calibration remains paused. Core package:
`gamesir-native-dkms 0.1.0.alpha3-6`; module version/ABI remain `0.1.0.alpha3`.
The optional trigger bridge is a separate package and was not installed by this
update.

## Observed defect

A previously authorized read-only status query showed a running, unpaused
manager, a newly enumerated `3537:100a` interface owned by `xpad`, and a
`released` entry carrying `Device changed during native status access`.
The earlier bootstrap had succeeded. The service had not restarted. This is
evidence of the manager latch, not proof of why the USB re-enumeration itself
occurred or a general diagnosis of unrelated system freezes.

An `info` child for the old native instance can finish during re-enumeration.
The old manager checks that result before handling the new instance and
turns a changed identity into a terminal error. Its fallback observation then
assigns the new `100a/xpad` token to the old released entry and to `attempted`.
Both the existing-entry and attempted-token guards prevent a fresh claim.
Reconnect between status jobs uses a different path and need not trigger it.

The second enumeration after child completion also previously discarded
per-port scan errors. Temporarily missing/invalid USB metadata could appear
as absence and produce the same sticky error. Unknown metadata is not a
confirmed disconnect, replacement or new ownership grant.

## Corrected policy

- A stale passive observation is separate from a bootstrap/runtime fault.
  Discarding an obsolete getter result never grants control over its target.
- A fresh `100a/xpad` replacement must pass ordinary device, parent-lifetime,
  ownership and start-budget checks. Old lease/tokens are retired without
  sending END, restoring or issuing commands to that replacement.
- No arbitrary `109c` replacement, foreign driver, changed hub or ambiguous
  device is adopted. Unknown errors and real runtime/bootstrap failures
  remain fail-closed; cleanup permission remains separate from start permission.
- Temporary incomplete metadata defers observation processing. Completed child
  output must not be lost or polled twice; pending children remain subject to
  their cancellation/deadline rules. A known fault must not disappear behind
  a later metadata error or manager restart.
- Explicit pause, service shutdown, failed return and existing fault latches
  must not become automatic new starts.

The existing limit of **three starts per physical port in ten minutes remains**.
This patch is not a removal of the restart-loop guard or a promise of unlimited
rapid reconnects. Even successful starts currently count. A distinct budget
exhaustion requires explicit review/resume and is not this observed error.

The installed old `released` entry is not automatically migrated merely by
matching its error text. A later approved update uses the normal checked
release/stop path and retains the pause. Fresh start/resume remains a separate
explicit action after inspecting the resulting real state.

## Offline validation

Regression scope includes re-enumeration before/during/after a passive status
job, getter-busy races, incomplete metadata on either scan, preserved faults,
same-port replacement, hub changes, pause/release, state recovery and budgets.
Tests use synthetic devices/jobs/time and the repository manager, never the
installed manager, USB/input nodes, sudo or real services. Results are recorded
below; no hardware acceptance is inferred.

Final offline results on 2026-10-17:

| Check | Result and scope |
| --- | --- |
| Reproduction before the correction | Eight failures in the initial 16-case regression set, including the false released-instance latch. |
| Focused manager regressions | 34 new cases passed; the existing 139 manager cases also passed (173 total). |
| Full project suite | `make test` passed: 825 Python unittest cases in 30 batches, plus the existing C/native and static checks. The trigger bridge, broker and packaging regressions also ran. |
| Offline module build | Passed for `7.2.11-1-garuda`, with matching vermagic and zero code warnings. Kbuild's known environment advisory remains: kernel Clang 23.1.1 versus local Clang 23.1.3. No module was loaded or installed. |
| Independent review | Added fences for global follow-up scan failures, errors concerning a different port, and a second replacement between snapshots. Completed child output/proof is retained without duplicate polling or commands on an unknown instance. |
| Safety boundaries | Unknown errors and real faults remain latched; pause and three-start budget remain effective. No automatic legacy-error migration, controller commands, installed-file changes or push. |

The local ignored logs are `build/reconnect-manager-tests-final.log` and
`build/reconnect-kernel-build.log`. They are not public release assets. The
kernel, ABI, broker/client, bridge, paddle, IMU and existing system hooks are
unchanged; runtime code changes are confined to the userspace manager.

## Reviewed build and update procedure

Build source archives and any local binary from the reviewed commit only.
The normal dependency check must pass; do not install dependencies, refresh
package databases or bypass checks with `--nodeps`. Binary metadata can contain
local build paths and remains private; no release upload is approved.

Although runtime code changes are confined to the userspace manager, the
existing **DKMS package update is a system operation**. Its pre-transaction
guard releases managed devices, verifies return/ownership, stops the service
and unloads an unused native module. Failure aborts the package transaction;
there is no force unload, global xpad removal or automatic repair. DKMS then
removes/rebuilds the packaged version for installed matching kernels. Existing
host hooks may rebuild initramfs, reload systemd metadata and create snapshots.
The user must review these effects before approving installation.

Before an approved update: close games and Deadband, inspect the fresh manager
and device state, ensure the exact candidate checksum and transaction contain
only `gamesir-native-dkms 0.1.0.alpha3-6`, and retain the verified revision-5
rollback package. Abort if another package, upgrade, conflict or unresolved
ownership appears. No package command is run automatically from this guide.

The separately approved transaction has this shape:

```sh
GS_PACKAGE=/absolute/path/to/GameSir-Native-Linux-PRE-ALPHA-0.1.0.alpha3-6-x86_64.pkg.tar.zst
pacman -Qip "$GS_PACKAGE"
pacman -U --print-format '%n %v' --print "$GS_PACKAGE"
sudo /usr/bin/pacman -U "$GS_PACKAGE"
```

The locally prepared installer is additionally named
`GameSir-Native-Linux-PRE-ALPHA-0.1.0.alpha3-6-x86_64.pkg.tar.zst` at the
maintainer's request. It is byte-identical to the standard build filename;
the package metadata still says `gamesir-native-dkms 0.1.0.alpha3-6`. This
visible label does not rename the module or invent a different DKMS version.

Afterwards inspect package files, DKMS results, module version/vermagic and
saved pause/ownership. Installation is not activation. A paused service start,
then one resume/native bootstrap and controlled reconnect acceptance each
require the appropriate separate approval. No Forza session starts as a side
effect of this update.

## Authorized local installation verification

On 2026-10-17, only `gamesir-native-dkms` was upgraded from revision 5 to 6.
The complete transaction was reviewed before confirmation. The approved
upgrade guard reported a verified release and absence of the native module;
DKMS and normal/fallback initramfs generation completed with transaction
exit status zero. No dependency installation or package database refresh was
performed. DKMS emitted a deprecation notice for the existing `CLEAN` setting;
no repair or configuration change was attempted.

| Read-only check | Observed result |
| --- | --- |
| Candidate archive SHA256 | `9783b49dc32f7eed372215d02a8b2c0a30f72ec2922cc8e36ff1559a2ec6aef0` |
| Installed package | `gamesir-native-dkms 0.1.0.alpha3-6`; package check: 127 entries, zero altered files. |
| Payload comparison | All 97 regular payload files match the reviewed archive byte for byte. |
| Installed manager SHA256 | `311b41bbab5310220a869d8b1dd98898c844b26eaed00b8d4f0e6d267fcdfbcc` |
| DKMS/module metadata | `gamesir-native/0.1.0.alpha3` installed for `7.2.11-1-garuda`; module version `0.1.0.alpha3`, matching vermagic. |
| Running state | Service inactive/dead, successful exit, no process; native module absent and no native USB bindings. |
| Saved administration state | Root-owned private state, `paused: true`, empty leases. Existing service enablement retained. |
| Dongle state | Unmanaged `3537:109c`, interface 0 still bound to `xpad`, interface 1 unbound; unchanged across installation. This is not a verified return to `100a`. |
| Scope exclusions | No start/resume, bootstrap, input or motor test; optional bridge not installed, Steam integration unchanged, no push. |

The unmanaged dongle was outside the empty managed-return scope. Successful
package removal preparation therefore does not establish its normal XInput
identity or prove the reconnect correction on hardware. Private transaction
and before/after logs are retained locally with checksums; they are not public
release assets. A fresh device check and separate approval remain necessary
before activation and real reconnect acceptance.

Rollback requires stopping games, a verified release/return and an explicitly
approved transaction with the saved `0.1.0.alpha3-5` package, followed by the
same read-only checks. It is a return to the earlier manager, **including this
known reconnect defect**, not a fix. If release/return is unresolved, stop and
request the documented manual recovery rather than forcing removal or reboot.

## CachyOS/Gamescope core update — installation only

On 2026-10-17 the separately authorized CachyOS/Gamescope test system was
updated from core revision 4 to 6 using the same reviewed archive hash listed
above. The full interactive transaction contained exactly one package;
no dependency installation, database refresh or running-kernel update occurred.
The optional trigger bridge was explicitly excluded.

Before confirmation, the manager had no leases or pending operation, the
native module was unbound with reference count zero, and the current dongle
was `3537:100a`, IF0 `xpad`, IF1 `usbhid`. A historical released-entry error
was recorded before the update. The existing upgrade guard then confirmed
release, paused administration, stopped the service and unloaded the unused
module. Historical failure records remained intact.

- The unprivileged prebuild and installed DKMS build for
  `7.2.9-2-cachyos-deckify` passed without code warnings. Module version remains
  `0.1.0.alpha3`, with matching vermagic, expected source version and no
  automatic USB aliases. The installed tool's device-free self-test passed.
- Package verification found 127 entries, zero altered files; all 97 regular
  payload files matched the reviewed archive, including ownership and modes.
- Post-state: service inactive/dead with successful exit, existing enablement
  retained, saved pause true, empty leases, module absent and no native
  binding. The observed USB instance and `xpad`/`usbhid` bindings were unchanged.
- Steam `0.1.0.alpha2-1` and Gamescope integration `0.1.0.alpha1-1`, their
  regular files and the running Steam unit were unchanged. No bridge was
  installed; no client permission or launcher configuration was changed.
- Complete transaction and DKMS logs were inspected beyond their exit codes.
  The only diagnostic was the known deprecated DKMS `CLEAN` setting.
  Initramfs generation succeeded; Snapper created pre/post snapshots and
  three Limine/snapshot metadata files changed. The kernel journal contained
  only native-driver deregistration during the observed update window.

Revision 4 to 6 also includes the earlier coherent-IIO-buffer work; this is
not a claim that every kernel source stayed unchanged. The buffer was not
activated and gyro calibration remains paused. No service start, resume,
bootstrap, input/motor test or reconnect acceptance followed the update.
The other test system was not changed. Installation parity does not establish
fresh hardware acceptance; activation requires a new explicit approval.

[Sanitized verification record](evidence/CORE_UPDATE_CACHYOS_20261017.json).
Private before/after inventories, logs and checksums remain outside Git.

See [installation and removal](INSTALLATION.md), [runtime ownership](ALPHA_RUNTIME.md),
[prior conflict handling](MANAGER_CONFLICT_FIX.md), and the separate
[trigger-bridge acceptance boundary](TRIGGER_BRIDGE.md).
