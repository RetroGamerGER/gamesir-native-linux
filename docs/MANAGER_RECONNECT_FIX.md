# Manager reconnect correction — offline update candidate

Date: 2026-10-17. PRE-ALPHA, local preparation only. No installation, service
operation, module change, controller command or live reconnect test is part
of this work. Gyroscope calibration remains paused. Core package candidate:
`gamesir-native-dkms 0.1.0.alpha3-6`; module version/ABI remain `0.1.0.alpha3`.
The optional trigger bridge is a separate package and is not installed by this
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

## Candidate build and future update approval

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

The future separately approved transaction has this shape:

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

Rollback requires stopping games, a verified release/return and an explicitly
approved transaction with the saved `0.1.0.alpha3-5` package, followed by the
same read-only checks. It is a return to the earlier manager, **including this
known reconnect defect**, not a fix. If release/return is unresolved, stop and
request the documented manual recovery rather than forcing removal or reboot.

See [installation and removal](INSTALLATION.md), [runtime ownership](ALPHA_RUNTIME.md),
[prior conflict handling](MANAGER_CONFLICT_FIX.md), and the separate
[trigger-bridge acceptance boundary](TRIGGER_BRIDGE.md).
