# Control Center alpha1 distribution review — 21 October 2026

The PRE-ALPHA AppImage is a Garuda x86_64 application profile requiring host
glibc **2.44 or newer** and a working graphical session. Driver support on
CachyOS does not establish GUI installer compatibility there. A separate
application profile and acceptance are required for other distributions.
The GUI is not intended to perform package installation inside Gaming Mode.

## Delivered licenses and corresponding sources

The reviewed image contains 1,859 attributed files from 73 distribution
packages / 69 package bases, plus project code. The AppImage runtime and six
statically linked dependencies bring the source registry to 77 components.
Every regular payload file has a SHA256 and component owner in the
[distribution lock](../packaging/control-center/source-locks/0.1.0.alpha1-linux-x86_64.json).
The separate source archive contains 1,530 reviewed files plus that lock.

Publish the following together in the existing PRE-ALPHA.3 release:

- `GameSir-Control-Center-PRE-ALPHA-0.1.0.alpha1-x86_64.AppImage`
- `GameSir-Control-Center-PRE-ALPHA-0.1.0.alpha1-Corresponding-Sources.tar.zst`
- the matching `DISTRIBUTION_LOCK.json`, manifest and SHA256SUMS assets.

The sources archive is approximately 1.14 GB; downloading it is optional for
ordinary application use, but distributing matching sources is part of our
binary publication process. It includes exact project sources, original Arch
packaging recipes and patches, hash-verified upstream inputs, fixed recursive
Git submodules, license/copyright texts and `REBUILD.md`. Mutable upstream links
alone do not substitute for these delivered sources. The AppImage itself
includes `usr/share/licenses/control-center-distribution/`, `COMPONENTS.json`
and `THIRD_PARTY_NOTICES.md`. Original third-party notices remain applicable;
project-owned sources remain **GPL-2.0-only**, with the existing UAPI exception.

Qt/PySide6 6.12 runtime source headers were checked, including QObject,
QQuickItem, QQuickControl, QSvgRenderer, libpyside and libshiboken. They
explicitly offer a GPL-2.0-only option. That option is selected where offered;
GPL3-only wasm, compiler and test tools are not included as runtime modules.
Package-level license labels are not used to relicense these sources. GCC
runtime exceptions and all other component-specific notices are retained.
Unused CPython readline/GDBM/DBM adapters are omitted before ELF dependency
collection; the application uses JSON and does not require a REPL/DBM backend.

Two source-input discrepancies were resolved explicitly:

- Zlib's GitHub patch had different index-hash abbreviations. Normalizing only
  those abbreviations to the recipe's representation matches **both** original
  checksums; no patch code was changed.
- Regenerated SQLite HTML documentation failed its original checksum and is
  excluded. The delivered, clearly modified `PKGBUILD.runtime` builds only the
  SQLite library from verified C sources and patches; no bundled runtime data
  is accepted using the failed documentation hash.

## AppImage runtime

The runtime was replaced during packaging with a directly obtained official
[type2-runtime](https://github.com/AppImage/type2-runtime) binary, pinned to
source revision `fedfad51acc2860b2916a1eef32ba4a500ff31ef` and SHA256
`617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46`.
It is 944,632 bytes. Complete runtime sources, build scripts, patches and
static dependencies accompany it: musl 1.2.5, libfuse 3.15.0, squashfuse 0.5.2,
zstd 1.5.6, mimalloc 2.1.7 and zlib 1.3.2. Static ELF/debug evidence establishes
base versions; libfuse/squashfuse source hashes also match the build pins.
The precise Alpine vendor package revision is not independently encoded in
the binary. This does not claim a byte-for-byte reproducible runtime build.

## Verification and publication boundaries

`scripts/check_control_center_distribution.py` checks the actual AppDir,
source tree, runtime prefix, image and compressed source archive. It rejects
unattributed/changed files, missing source/license evidence, unsafe names,
links, duplicate/extra archive members, altered locks and hidden trailing
payloads. It does not execute source recipes, extract firmware or access root.
The reviewed license decisions are recorded separately from checksum checks;
a matching hash is neither a license nor a blanket legal guarantee.

412 Control Center cases in 25 groups (61 QML cases included) and four
synthetic self-test lanes of the final AppImage passed. All four existing
GitHub package downloads passed real HTTPS/size/hash checks and the installed
helper's verifier, imported as an ordinary user without performing a transaction.
This does not prove a new complete signed package installation or driver test.
The exact already signed revision-1 catalog is published at `updates/pre-alpha.json`
without signing it again. Its expiry is 20 November 2026 at 12:36 UTC; maintainers
must publish reviewed, newly signed metadata before expiry. An expired or
unavailable channel fails closed; no automatic package install occurs.

The maintainer separately reports driver faults on both PCs. They are deferred
until this app publication is finished. No driver, module, service, installed
helper, Steam setting or device binding was changed by this distribution review.
Precise gyroscope calibration remains paused. See the
[evidence](evidence/CONTROL_CENTER_DISTRIBUTION_20261021.json).

## Publication result

The five assets are published in the existing
[PRE-ALPHA.3 release](https://github.com/RetroGamerGER/gamesir-native-linux/releases/tag/v0.1.0-pre-alpha.3).
GitHub's uploaded asset digests/sizes match all local bytes. Existing assets
and the original tag are unchanged. The actual public metadata download
verifies in both the bundled runtime and installed helper's unprivileged
verification path. Source snapshot: `eb99dce9068727929b37fb9683fd54bbe79bba58`.
[Publication receipt](evidence/CONTROL_CENTER_PUBLICATION_20261021.json).
