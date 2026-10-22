# PRE-ALPHA.4 / Control Center alpha2 publication review

22 October 2026. The maintainer first requested local release preparation and
then explicitly authorized publishing the new packages with a new release/tag.
Target: `RetroGamerGER/gamesir-native-linux`, `v0.1.0-pre-alpha.4`, marked
**pre-release**. No installation or change to either running driver is included.

## Intended contents

- Control Center `0.1.0.alpha2`, its matching corresponding-source archive,
  distribution lock, manifest and checksums.
- Core/DKMS/manager `0.1.0.alpha3-20`, including source/recipe inputs.
- Optional TMR permission helper `0.1.0.alpha1-2`, including exact sources,
  recipe and GPL-v2 text. Its eight helper/policy files must match the tested pins.
- Full reviewed project source, release notes and a signed revision-2 package
  catalog retaining the existing public trust key and cleanup/version history.

The three unchanged optional packages retain their PRE-ALPHA.3 versions and
immutable assets. A new catalog must not rebuild a same-version package with
different bytes. Existing releases/tags/assets remain unchanged.

## Installation scope

The AppImage contains a real restricted package frontend, not only a demo.
The old live install/remove results and the new offline package tests have
separate scopes; no new physical reinstall is claimed by preparing this release.
Users choose **Check driver updates**, then review a selected package plan and
authorize it in the system window. Nothing installs or activates on startup.
The signed catalog supplies alpha3-20 without replacing the fixed helper trust
anchor. Activation follows the existing installation/recovery guide.

The AppImage installer remains Garuda x86_64 / glibc 2.44+. CachyOS driver
evidence does not establish this GUI's Gamescope-installer compatibility.
TMR is an optional fifth package with [separate setup](TMR_SETUP.md); it is not
silently installed or enabled by the four-component GUI package backend.
That limit must remain visible in README and release notes.

## Sources and licenses

The local alpha2 preview used newer layer-shell-qt, qt6-declarative and PySide
package builds than the previous complete source audit. The publication build
uses the exact old reviewed dependency bytes and their complete corresponding
sources instead. This deliberately avoids treating a version label or old
license decision as provenance for changed binary files.

`prepare_control_center_distribution.py` verifies the previous full lock,
copies only the new project payload, preserves every third-party byte and
owner/version, and creates a new alpha2 source lock. It retains upstream
licenses, Qt/PySide GPL-2 options where explicitly offered, runtime exceptions,
exact recursive source snapshots, recipes/patches and the official runtime
source. The original alpha1 lock is preserved.

New code is project-owned GPL-2.0-only. Complete COPYING and the UAPI exception
remain unchanged. No manufacturer app/firmware, raw traces, private signing
material, private Git history or personal build paths belong in the upload.
Publish matching binary/source/lock assets together, never a mutable source link
alone. The checksum gate confirms technical consistency, not legal advice.

## Ordered publication

1. Freeze the source tree, dependency/source lock and privately retained build
   receipts; validate packages and all five synthetic AppImage lanes.
2. Create a clean public snapshot on the existing public main ancestry. Keep
   private development commits private; compare the intended public tree.
3. Build core/helper packages in clean neutral directories, with the public
   noreply packager identity. Compare runtime payloads with the tested builds.
4. Sign revision 2 with the existing external release key; independently verify
   signature, origins, cleanup guards and immutable asset records. Do not alter
   the trust anchor or installed helper.
5. Push the reviewed source and new tag; create a PRE-ALPHA draft, upload only
   the frozen allowlisted assets, then publish the pre-release.
6. Confirm uploaded digests/sizes and package download/verifier results before
   advancing the public signed-update channel. Commit the publication receipt.

No hardware calibration, firmware update, package installation, module load,
service restart, Steam change or automatic recovery is part of these steps.
