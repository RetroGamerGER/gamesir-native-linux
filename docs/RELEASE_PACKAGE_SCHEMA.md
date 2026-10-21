# Installable release package schema

21 October 2026. Maintainer policy for future package uploads. PRE-ALPHA;
GPL-2.0-only and existing notices/exceptions remain unchanged.

Publish installable packages alongside the source/build inputs. Keep these
components separate so the Control Center can select only requested features:

| Component | ALPM package | Architecture |
| --- | --- | --- |
| Core / DKMS / manager | gamesir-native-dkms | x86_64 |
| Steam mapping | gamesir-native-steam | any |
| CachyOS Gamescope integration | gamesir-native-steam-gamescope | any |
| Forza / Xodus trigger bridge | gamesir-native-trigger-bridge | x86_64 |

Use makepkg's `name-version-release-architecture.pkg.tar.zst` names. These
packages target supported Arch-family systems; they are not RPMs or universal
Linux binaries. The core contains DKMS sources, not a precompiled kernel
module. Matching prepared kernel headers and declared build dependencies
remain necessary. The optional Gamescope package requires its declared
CachyOS session package. Do not imply universal Steam/Proton trigger support.

Each publication must include:

- `BINARY-RELEASE-MANIFEST.json`: repository, immutable source commit, release
  tag, component filenames, package/version/architecture/license, byte size,
  SHA256, declared dependencies, core cleanup-guard hashes and validation scope.
- `BINARY-SHA256SUMS`: checksums of the supplemental package/metadata assets.
- `release-assets.json`: closed component-to-filename index in the fixed project
  repository, matching the reviewed Control Center download schema.
- `REVIEWED_PACKAGES.json`: reviewed build input for the catalog, not a runtime
  remote authority. Any installed protected helper catalog change is a
  separate, explicitly reviewed deployment step.
- `BINARY-PACKAGES.md`: component choices, provenance, prerequisites, limitations
  and trust boundary, including any later supplement to an existing release.

Build as ordinary user from the reviewed public source commit in a neutral
directory using the public project identity. Check package build/check phases,
payload provenance, public metadata/privacy, safe archive structure,
identity/architecture/license/dependencies and cleanup guards through the
existing AppImage verifier. Record native ABI requirements. Do not upload
firmware, captures, credentials, private paths or unrelated AppImage work.

Never overwrite published asset bytes or move a tag to repair a hash. A later
supplement uses new nonconflicting metadata/checksum names and preserves old
source assets. New bytes require new reviewed pins even at the same version;
checksums fetched from GitHub cannot grant themselves approval. No automatic
`latest` lookup, arbitrary URL, privilege escalation during download, silent
installed-helper update or package installation follows publication.

The first supplement uses source commit
`b5b9cc34534e5afdb6505322308b364f15e31c2b`, tag
`v0.1.0-pre-alpha.3`, and versions core alpha3-16, Steam alpha2-1,
Gamescope alpha1-1 and bridge alpha1-2. Its four packages pass the existing
archive verifier and staged-payload comparison. Both native binaries require
glibc 2.34 or newer. This is a packaging check, not a new hardware/runtime test;
the installed driver and helper are unchanged. The current local AppImage's
older package pins must not be silently reused for these rebuilt archives.

The first supplement is published in the [existing release](https://github.com/RetroGamerGER/gamesir-native-linux/releases/tag/v0.1.0-pre-alpha.3).
GitHub digest/size records match all nine added assets; the original eight
assets are unchanged. The real Control Center ReleaseDownloader fetched all
four packages and passed its exact size/hash/archive checks against local
review pins. No installed catalog or package was modified.

## Signed catalog publication after updater deployment

For a reviewed policy-enabled Control Center, publish the reviewed signed
`updates/pre-alpha.json` metadata after the immutable release packages and
checksums are available. This is the explicit mutable metadata-channel
exception; never overwrite package/tag asset bytes. Follow
[the signed protocol and publisher procedure](CONTROL_CENTER_RELEASE_UPDATES.md).
Metadata includes versions/hashes/source/tags/index, explicit upgrades and
retained cleanup history, monotonic revision and bounded expiry. Verify against
the previous catalog before publishing. No production key, signed channel or
helper migration is authorized by the current offline implementation. Public
RFC test keys must never be trusted for real release signing.

## Control Center binary publication

AppImage uploads must also include the matching complete corresponding-source
archive, distribution lock, component/version/license inventory, SHA256 checksums
and a manifest. Preserve existing driver assets; use component-prefixed names
for app checksums/manifests. Do not publish a binary alone or claim portability
beyond the reviewed distribution/ABI profile. Run the offline distribution
gate against the actual compressed delivery and all four packaged synthetic
lanes. Exact signed catalogs are separate reviewed channel assets; never trust
an unsigned latest-file checksum or re-sign an existing revision with new bytes.
See [alpha1 review](CONTROL_CENTER_DISTRIBUTION.md).
