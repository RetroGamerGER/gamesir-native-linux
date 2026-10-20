# Revision 15: receiver-wait update preparation

20 October 2026. PRE-ALPHA `0.1.0.alpha3-15` prepares the opt-in
[receiver-wait implementation](RECEIVER_WAIT_KERNEL.md), based on source commit
`159a83f`. This is a read/build checkpoint, **not installation or hardware
acceptance**. The module/DKMS version remains `0.1.0.alpha3`; compare module
`srcversion`, source hashes and the package revision as well as version text.

## Fresh target inspection and build

The approved read-only inspection of the separate CachyOS Gamescope host finds:

- Running kernel `7.2.11-1-cachyos-deckify`, matching prepared headers, matching
  generated UTS release and the required build dependencies.
- Installed driver `0.1.0.alpha3-14`; all driver, Steam and Gamescope integration
  package integrity checks pass. DKMS reports the current kernel installed.
- Service active/running/enabled, no restarts; management unpaused. Actual
  receiver is `109c`/xpad, with no current native interface binding.
- A **blocked current-boot lease** remains. Its retained original bootstrap
  diagnostic is `state=8 error=-110 failed_stage=5 pad=0 imu=0 handover=0`.
  The outer error remains `Return deadline: still 109c; manual attention required`.
  The read does not issue another bootstrap or query a native device handle.
- Existing gyro/acceleration configuration remains intact: experimental gyro
  and acceleration enabled, axes `1,2,3`, `8192/1` counts/g. No receiver-wait
  configuration exists at the proposed new path.

Seventeen hash-pinned build files were copied to a fresh **unprivileged**
source directory on that host. Kernel release, boot and five prepared-header
hashes were checked before/after. GCC 16.2.1 matches the kernel compiler;
W=1 and `KCFLAGS=-Werror` pass with **zero warnings**, no automatic USB aliases
and matching vermagic. Module `srcversion` is `CA96E675200CE5CCEFB7DD0`;
standalone build SHA-256 is
`1d2b0a53f245a3261185d727d85dbcaa121f2bf875ac8f862a410496179c7382`.
Package and service state were unchanged throughout compilation. No module was
loaded or installed; no USB/input/IIO/control device was opened by this work.
Raw inventories, boot/instance identifiers and build logs remain private.

## Offline regressions and unchanged-state checks

Full `make test` passes: **1,339 Python cases in 46 groups**, plus the C,
actual-kernel-adapter and sanitizer suites. The extended package regression
also passes all 25 cases: matching receiver-wait documentation/reference files
are staged, no `/etc` configuration is installed, and the service does not set
`receiver_wait=1`. No new kernel/manager behavior is changed by revision packaging.

A final unprivileged target read matches the initial kernel, boot, prepared
headers, packages/integrity, DKMS, service, loaded module, parameters, USB
instance/bindings, configuration files and hook metadata. The stored revision-14
rollback package matches its prior SHA-256. The protected read attests that
its blocked lease and retained diagnostic belong to the current boot; it
neither repeats bootstrap nor clears the failure. A future update must still
repeat all time-sensitive guards rather than reuse this snapshot.

## Proposed installation gates — not executed

**Do not run a package transaction against the currently unresolved lease.**
The proposed next approval covers these separate, guarded stages:

1. Freshly attest the same target, package, kernel, service, configuration and
   ownership. Have the maintainer remove only the target receiver and leave it
   out. Confirm actual continuous absence and retirement; do not erase state,
   tokens, errors or budgets to force that result.
2. Issue one explicit `sudo /usr/bin/gamesir-native release`. Independently
   require paused management, `returned=true`, empty devices **and persisted
   leases**, and no native bindings. Failure stops the plan; no repeated Release.
3. Transfer the exact checksummed PRE-ALPHA package to an unprivileged staging
   directory. Invoke `sudo /usr/bin/pacman -U -- ./GameSir-Native-Linux-PRE-ALPHA-0.1.0.alpha3-15-x86_64.pkg.tar.zst`
   from that verified directory. No dependency installation or full system
   upgrade is included. The package's normal PreTransaction hook also performs
   its own guarded Release, service stop and unused-module unload; that hook
   must not be bypassed. A failed return aborts the transaction.
4. Review all package-hook results: snap-pac pre/post snapshots, Limine snapshot
   lock, guarded native cleanup, DKMS removal/build/install, dependency refresh,
   systemd/udev reload and the configured Limine/mkinitcpio regeneration.
   Verify installed revision 15, package integrity, DKMS for the actual kernel,
   on-disk module `srcversion` and receiver-wait parameter. Standalone module
   SHA is a build receipt, not a promised identical DKMS binary hash.
5. Require inactive service, absent old loaded module and paused empty ownership
   before activation. Preserve enabled autostart and the existing sensor/Steam
   configurations. Package installation alone must not enable receiver waiting.

Keep the hash-verified revision-14 package as the rollback artifact. Its local
filename and checksum belong in the private per-attempt approval record.
A downgrade needs the same successful cleanup and its own authorization;
installing old sources while a new same-version module is loaded is unsafe.

## Proposed activation — separate approval, not executed

After all installation gates pass, create exactly
`/etc/modprobe.d/91-gamesir-native-receiver-wait.conf`, containing:

```text
# GameSir Native Linux: explicitly enabled experimental receiver waiting.
options gs_native receiver_wait=1
```

The path was absent at inspection. Recheck absence before creating it; if it
exists or the previous sensor configuration changed, stop rather than overwrite.
Retain the source file and checksum in the private approval directory. This
activation intentionally persists across module loads; no package sets it.

Then run **once each, with checks between them**:

```sh
sudo /usr/bin/systemctl start gamesir-native.service
sudo /usr/bin/gamesir-native status
# Only after paused/empty state and loaded parameters/srcversion match:
sudo /usr/bin/gamesir-native resume
```

The service loads industrialio and the new gs_native with bootstrap/output/
persistent/deferred-input modes. Independently read effective `receiver_wait=Y`
and the unchanged experimental sensor options before Resume. Existing enabled
service autostart is retained; there is no reboot or new enable operation.
With the receiver absent, Resume may succeed with an empty device set; that is
**not** evidence that receiver waiting or native runtime works.

Only following the explicit physical-test approval, insert the receiver with
the controller confirmed off. Expect one bounded setup, then kernel state 9
and manager `receiver_wait`, no repeated bootstrap/OUT or new attempt budget.
After the wait is attested beyond the old verification deadline, cue one
controller power-on without button presses. Fresh native IMU must establish
READY/handoff before input publication/application checks. If the firmware
loses its earlier initialization, leave that result unresolved and stop;
never compensate with automatic initialization replay.

No power-on, recording, motor test, Steam restart or boot test is included in
this preparation. A later activation approval must explicitly scope one error
Release and readback; if return is still `109c`, report manual recovery rather
than success. An unready waiting state is cancelled on suspend/reset/shutdown;
automatic restart of that cancelled wait is not implemented.

## Decision

**Build/package preparation: GO. Current installation/activation: NOT EXECUTED;
blocked until controlled return and new approval.** Real controller-off/late-on
acceptance remains open. Existing application tests do not validate this new
waiting lifecycle. The gyro calibration remains paused; no push is authorized.
