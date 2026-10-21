# Control Center — Phase D offline AppImage preparation

**Current distribution checkpoint (21 October 2026):** the reviewed Garuda
x86_64/glibc2.44 alpha1 build, corresponding sources, signed revision1 and
publication scope are documented in [the distribution review](CONTROL_CENTER_DISTRIBUTION.md).
Older phase entries below retain their historical dates and boundaries.

20 October 2026. **Local PRE-ALPHA test build only; not a published binary
release or installer.** Offline AppDir/AppImage and desktop-payload preparation,
testing and local commits only. No live installation, profile/menu/autostart
integration, driver action, network request or push. Installed alpha3-16 stays
frozen. The GUI remains read-only; Phase C has no live package transport.

## Architecture and compatibility boundary

`scripts/package_control_center.py` stages the existing Python/QML application
with its own interpreter, standard library, selected PySide/Shiboken bindings,
QML modules, platform plugins and recursively resolved ELF dependencies. It
uses already installed inputs, never pip or a package/dependency installer.
Unused Tk/test extensions, unrelated site-packages, WebEngine and unneeded Qt
bindings are excluded. Network/OpenGL bindings are included as QML type
dependencies; no network feature is added to the application.

`AppRun` uses the host x86_64 ELF loader with a per-process `--library-path`,
isolated Python (`-I -B`), fixed bundle plugin/QML directories and Basic software
rendering. Inherited Python/loader injection variables are cleared. Libraries
are **not exported as LD_LIBRARY_PATH**, so a later browser/systemctl process
does not inherit the bundle's library search path. Application/build sources
remain readable. The icon is project-owned vector artwork.

The local profile bundles Python 3.14.8, PySide6/Qt 6.12.0. It relies on the
host glibc/loader and graphics-driver interfaces. The highest observed declared
GLIBC requirement is **2.44**. This current-host build is **not** a claim that
AppImage automatically supports older distributions. Target CachyOS/Wayland/
Gamescope and older-baseline builds require separate acceptance. The smoke
test proves packaged Python/Qt are loaded, not the installed host copies.

The unprivileged builder refuses system, live user-profile/Desktop/XDG data
and config, symlinked and nonempty destinations. Failed staging outputs are
preserved rather than overwritten during an automatic retry. There is no
install, download, activation or system-removal CLI.

## Build using existing local inputs

From a complete checkout, as the normal user, in fresh output folders:

```sh
python -B scripts/package_control_center.py stage --dest build/control-center-appdir
```

`GameSir-Control-Center.AppDir` contains `AppRun`, embedded Desktop Entry/icon,
application/build sources, local notices and `BUILD_INPUTS.json`: versions,
package identities, relative file hashes, host-library exclusions and
`release_ready: false`. It contains no personal source/build paths. Kernel
headers or a running controller driver are not required for GUI packaging.

Supply the type-2 runtime from an already available local AppImage container
with its explicitly reviewed SHA256. The builder neither downloads nor
executes that container: it checks hash, ELF architecture/section bounds and
squashfs boundary, then copies the runtime prefix. Local `mksquashfs`, `readelf`
and `desktop-file-validate` are needed; absence stops without installation.

```sh
python -B scripts/package_control_center.py image \
  --appdir build/control-center-appdir/GameSir-Control-Center.AppDir \
  --dest build/control-center-image \
  --runtime-container /absolute/path/to/reviewed-runtime-container.AppImage \
  --container-sha256 EXACT_REVIEWED_64_CHARACTER_SHA256 \
  --epoch 0
```

The AppDir must still match its recorded hashes. Unexpected links, changed
contents and recursive output inside the AppDir are refused. Images use one
compressor thread, fixed timestamps, root ownership and no host extended
attributes. Outputs: named AppImage, `SHA256SUMS`, `BUILD_REPORT.json` with
container/runtime hashes, squashfs offset and epoch. This pins local bytes,
**not upstream authenticity or redistribution rights**. No automatic update
metadata, desktop registration or FUSE module load.

Local container SHA256:
`95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6`.
Extracted 944,632-byte runtime SHA256:
`77f59c85aa4b171adf01d1870d86a53fcdeee7e27b31d119beb420dc4f140b66`.
Upstream origin/license/corresponding-source review remains pending; these
local observations do not authorize publishing that runtime.

## Offline packaged smoke test

`--bundle-self-test` uses a synthetic collector and private temporary
preferences. It never constructs the real status collector, opens hardware,
authenticates or calls Phase C. It checks QML load, DE/EN, System details,
disabled real actions, software rendering and no host Python/Qt fallback.
Root execution is refused.

```sh
build/control-center-appdir/GameSir-Control-Center.AppDir/AppRun --bundle-self-test
APPIMAGE_EXTRACT_AND_RUN=1 \
  build/control-center-image/GameSir-Control-Center-PRE-ALPHA-0.1.0.alpha1-x86_64.AppImage \
  --bundle-self-test
```

For recorded tests HOME, XDG and TMPDIR additionally point into private
temporary build directories. Runtime extraction needs no FUSE mount or user
integration. Normal launch defaults to the existing read-only metadata view;
`--demo` keeps isolated examples. Normal desktop/Gamescope acceptance remains
separate from the offline smoke test.

## Desktop payload, not installation

```sh
python -B scripts/package_control_center.py desktop \
  --appimage /absolute/future/location/GameSir-Control-Center.AppImage \
  --dest build/control-center-desktop-payload
python -B scripts/package_control_center.py removal-preview \
  --payload build/control-center-desktop-payload
```

Only the project's Desktop Entry, icon and `DESKTOP_PAYLOAD.json` hash/ownership
receipt are staged. Nothing is copied into a real menu, Desktop, autostart or
XDG directory. The non-terminal Desktop Entry is read-only labelled in DE/EN,
has no file/URL handlers or privilege wrapper and passes the desktop validator.

The external entry launches one quoted absolute AppImage path using fixed
`/usr/bin/env --`, **without a shell**. This avoids GIO resolving a literal
`%%` filename before field-code expansion. Real GIO tests exercise spaces,
quotes, dollars, backticks and percent using a harmless test program, not the
real app. Controls/newlines and relative exec paths are refused. Path-dependent
payloads stay private/local, not public release assets or hardcoded developer
paths in the reusable template.

`removal-preview` only reports matching, modified/redirected and absent owned
files; it deletes nothing. Changed user files, links and unrelated content
remain preserved. Actual integration/removal needs separate approval, fresh
ownership checks and session acceptance. No Steam, SDL, Eden or default file
association changes.

## Licenses, provenance and release gates

Own application, launcher, build and icon sources stay GPL-2.0-only. Installed
QtCore/Quick/Controls, PySide and Shiboken header notices offer a GPL-2.0-only
alternative; their unmodified notices and full GPL-v2 text are retained as
local evidence. Python's full local license is included. Available dependency
notice directories are preserved; package versions and missing local notice
directories are listed separately.

This is **not a completed redistribution audit**. Some dependencies lack local
notice directories. Complete corresponding-source/relinking obligations,
transitive component terms and runtime provenance must be reviewed before
publishing a bundled binary. A source URL, package receipt or checksum alone
does not fulfil those obligations. `release_ready` stays false. No proprietary
firmware, USB traces or private package settings are bundled.

Before public binaries or actual integration: authenticate/review the runtime
and complete third-party notices/source distribution; choose an older build
baseline if required and test each target; separately validate KDE/Gamescope,
external links, relocation and user-profile integration/removal. Do not bundle
glibc/graphics drivers as an improvised portability workaround. GUI packaging
does not activate the driver or unlock Phase C's live backend.

## Validation

`make test-control-center-package` (also in the normal suite) runs 17 offline
cases: staging boundaries/root refusal, isolated launcher, Desktop Entry and
actual GIO argument parsing, nonmutating bounded removal previews, malformed
runtimes, payload integrity and deterministic compression options. Optional
desktop/GIO tests skip explicitly when those local tools are missing.

The staged AppDir and actual type-2 image passed synthetic smoke tests. Two
separately staged AppDirs have identical input manifests; the separately
compressed images are byte-identical (68,483,576 bytes), SHA256
`c393aa1ab1585b1ab4b4765903cec0fa09a3121cd7fbb7d5b3984c8f7328f5f7`.
The actual image also passes after relocation into a directory containing
spaces, with a percent sign in its filename and a private extraction directory.
This exposed and fixed a self-test parser bug: proc-maps pathnames with spaces
must remain intact while checking for host-library fallback. Its regression
also proves an actual host library path remains detectable.

The staged desktop entry validates and its nonmutating removal preview finds
exactly the two owned files. Full `make test` passes 1,450 Python cases across
50 groups plus its C/actual-kernel-adapter/sanitizer checks; this includes the
17 packaging cases. All 26 optional QML cases also pass. Reproducibility/
relocation logs and images stay as local ignored build
artifacts. These checks prove neither cross-distribution nor hardware
compatibility. No profile/driver installation, live sensor test or network
access is part of this checkpoint.

## Reviewed package binding — prepared offline, 21 October

An explicit build-only `stage --reviewed-packages` option embeds the audited
local catalog/packages and fixed installed-helper pins. The reviewed build
connects GUI installation/removal through background passive checks and a
separate exact confirmation/password flow. Generic builds/source stay read-
only; there is no runtime trust-path flag or automatic helper bootstrap.
`--bundle-package-self-test` exercises only private synthetic install/remove
fixtures and never loads the embedded real review bundle. See
[scope, safeguards and future acceptance](CONTROL_CENTER_APPIMAGE_PACKAGES.md).
No live installation/removal has been tested by this build.

## First-run helper payload — offline preparation

The optional build-only `--reviewed-helper` requires `--reviewed-packages` and
embeds only the thirteen independently pinned helper/license/policy files as
data. A reviewed build can detect missing helper state and show its separate
explicit confirmation/password flow. No privileged code runs from the bundle;
root uses only fixed system mkdir/install commands and sealed stdin. Existing
helpers are not overwritten. `--bundle-first-run-self-test` uses wholly synthetic
file/agent/command edges; no real helper inspection or authentication. See
[first-run scope, limits and future approval](CONTROL_CENTER_FIRST_RUN.md).
