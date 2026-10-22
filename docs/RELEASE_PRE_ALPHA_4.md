# GameSir Native Linux v0.1.0-pre-alpha.4 — PRE-ALPHA

⚠️ **EXPERIMENTAL SOFTWARE.** Read the README warning and recovery instructions
before installing. Intended for experienced Linux users; crashes, freezes,
device conflicts and data loss remain possible. GPL-2.0-only; the existing
UAPI exception and third-party notices are preserved.

## What is new

- **Control Center alpha2:** a simpler DE/EN interface, separate System details
  and guided stick calibration: choose controller, move sticks, finish.
- **Driver/manager alpha3-20:** includes the reviewed start-budget correction,
  ZZZ motion extension and narrow TMR maintenance API. The corrected TMR
  display avoids the earlier blinking Start button and expensive process scans.
- **Optional TMR helper alpha1-2:** a separate, restricted permission helper.
  Calibration and package operations cannot run over each other.

The normal G7 Pro passed the guided calibration and input checks. On the ZZZ,
the measured left-stick offset improved from approximately 1% to practically
zero without observed variation, including after ordinary off/on. These are
scoped results, not a guarantee for every controller or firmware.

## Which download do I need?

For the **Garuda x86_64 desktop**, start with the Control Center alpha2 AppImage.
It requires host glibc 2.44 or newer. Set up its package helper if offered, then
choose **Check driver updates** before **Review installation**. Review the
selected components and confirm in the system permission window. Driver
activation remains a separate step in the installation guide.

The app downloads checked GitHub packages; compatible future driver updates
do not require a new AppImage. The optional Steam, Gamescope and Forza/Xodus
bridge versions remain unchanged and keep their original PRE-ALPHA.3 assets.
The signed catalog records their exact original URLs and hashes.

**Stick calibration needs additional setup.** Install the optional TMR helper
and enable the TMR option as described in [TMR setup](TMR_SETUP.md). The normal
driver installation does not silently enable it. The Control Center package
installer does not yet manage that extra helper. Firmware flashing is unavailable.

CachyOS driver support does not establish AppImage-installer compatibility in
Gaming Mode. Use the manual installation guide there.

## Files, checks and limits

The release includes the new core and optional TMR-helper packages, their
reproducible source recipes, full project source, the AppImage with matching
corresponding sources and licenses, manifests and checksums. The signed update
catalog retains the existing trust key and protected cleanup history.

The application uses the previously reviewed dependency baseline with every
third-party runtime file unchanged. New project files receive their own source
mapping. No proprietary GameSir application, firmware, captures, private keys,
private Git history or personal build paths belong in these assets.

The new UI passed 603 offline cases and five packaged synthetic lanes before
distribution preparation. The release review records additional dependency,
package, source and signed-catalog checks separately; it does not claim a new
live reinstall or controller test of the release packages.

Known long-off/reconnect and partial-button failures remain under investigation.
Steam's gyro display can disagree with working motion in games. The Eden
Gamescope adjustment remains a manual, application-scoped compatibility note.
The existing Forza/Xodus trigger bridge has limited game coverage; universal
Steam/Proton trigger effects and firmware updates remain unconfirmed/unimplemented.

Preparing or publishing this release does not install, restart or activate a
driver on either test system. Precision gyro work remains paused.
