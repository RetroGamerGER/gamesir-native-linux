# GameSir Native Linux v0.1.0-pre-alpha.3

**PRE-ALPHA — experimental kernel software for experienced Linux users and
developers.** Crashes, freezes, device conflicts and data loss remain possible.
GPL-2.0-only; existing UAPI Linux-syscall-note exception retained.

## Included versions

| Component | Source recipe |
| --- | --- |
| Core kernel/manager | 0.1.0.alpha3-16 |
| Optional Steam mapping | 0.1.0.alpha2-1 |
| Optional CachyOS Gamescope integration | 0.1.0.alpha1-1 |
| Optional Forza/Xodus trigger bridge | 0.1.0.alpha1-2 |

## Main change

The core package now installs the tested receiver-wait policy as a vendor
modprobe default, mode0644, at
`/usr/lib/modprobe.d/91-gamesir-native-receiver-wait.conf`. Same-name local
`/etc/modprobe.d/` overrides are preserved; there is no conflicting claim on
the existing manually created local file. Package removal removes its own
vendor file, retaining deliberate local overrides. Installation still does
not enable/start/resume the service, seize hardware or reload a running module.

The source includes standalone exact-instance acquisition, the bounded startup
query, persistent RX waiting, independently attested new USB lifetimes and the
existing manager recovery/first-error safeguards. One controller-off insertion
waited more than45 seconds; a subsequent single power-on without other inputs
re-enumerated and automatically reached active native gamepad/IMU publication.
The maintainer accepts that behavior. Reported short initial xpad contact is
not a blocker; its exact cause and completely xpad-free probing remain unproved.

Normal inputs, independent paddles, IIO/coherent IMU, optional SDL motion,
application-controlled grip rumble and the existing four-channel haptics path
remain present. Steam mapping and Forza/Xodus trigger integration remain separate
optional userspace packages. The trigger bridge is not a universal Steam/Proton
trigger implementation. Gyro/acceleration remain opt-in and calibration paused.
See the [commit/function audit](FUNCTIONAL_INTEGRATION_AUDIT.md).

## Evidence and limits

The accepted waiting/late-on evidence uses revision15 on
`7.2.11-1-cachyos-deckify`; revision16 adds packaging policy, not new kernel logic.
Garuda and CachyOS module builds and offline regressions do not establish every
boot/reconnect/suspend scenario. Steam gyro display zeros can disagree with
reported working application motion. Eden's Gaming Mode solution remains a
manual application-scoped SDL-filter workaround, not automatic launcher edits.
Unready waiting suspend/reset cancellation has no automatic reinitialization.

Public assets contain reviewed source only, not locally built binary packages,
firmware, raw USB captures or private build metadata. Full source contains tests;
component archives contain the matching smaller build inputs/PKGBUILDs.
Read [installation/removal](INSTALLATION.md), [release audit](RELEASE_AUDIT.md)
and the README warning before installation. A future installation or live test
requires separate authorization; publishing this source changes no live system.
