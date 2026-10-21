# Reviewed GitHub package downloads and signed updates

## Signed update implementation — later offline checkpoint

The previously proposed signed catalog path is now implemented and tested
with public fixture keys, fake HTTPS/host/root and temporary state. Both app
and helper independently verify; update checks do not authenticate/install.
Compatible new package versions no longer require changing the app/helper
trust anchor. No production key/channel or installed helper was changed.
[Protocol, acceptance and deployment gates](CONTROL_CENTER_RELEASE_UPDATES.md).
Older fixed-pin descriptions below document the original implementation.

## Original pinned-download implementation

21 October 2026. Original download implementation: **offline fixture acceptance only.**
No network request, AppImage launch, authentication, package operation,
installed-helper update or driver/bridge/service/Steam change was performed.
The accepted local first-/second-start AppImage is not replaced or restarted.
Public binary records remain empty; no release asset is invented or approved
by this implementation. No push, tag or publication. Gyro calibration paused.

## Later authorized package supplement

The maintainer subsequently approved installable packages in the existing
public release. Four archives rebuilt from its exact source tag pass the
existing AppImage archive verifier. The [release upload schema](RELEASE_PACKAGE_SCHEMA.md)
records versions, provenance, supplemental manifest/checksums and download
index. This does not replace the installed helper catalog or turn the older
local AppImage pins into approval for rebuilt bytes. No package operation
occurs. The supplement was then published, and the actual ReleaseDownloader
fetched all four archives through GitHub/CDN: exact size/hash/archive checks
passed. All original assets were preserved. A reviewed new AppImage/helper
catalog remains a separate deployment step.

## Source and trust

The new local metadata-only AppImage profile selects the four reviewed public
packages from v0.1.0-pre-alpha.3. It retains accepted removal guards and the
previously reviewed Steam alpha1-1 -> alpha2-1 upgrade rule. No installed helper
catalog changes with this build. Its new catalog pin differs from the old
installed helper, so existing-helper replacement remains blocked rather than
silently bypassed. The build is a local Garuda/kernel-scoped test artifact.
Five new pin/bundle regressions and 84 existing download, reinstall, package,
first-run and packaging cases pass offline.

The maintainer requires future package updates without replacing the AppImage.
That is **not implemented by fixed hashes**: both GUI and root helper need a
signed catalog path. See the [proposed update architecture](CONTROL_CENTER_RELEASE_UPDATES.md).
No production signing key is generated, and no dynamic trust is enabled here.

A deliberately reviewed build can now contain metadata instead of embedded
driver packages. Its existing pinned catalog still supplies each component's
exact version, tag, source commit, SHA256, byte size, dependencies, upgrade
rules and core cleanup-guard hashes. A closed `release-assets.json` adds only
the fixed repository `RetroGamerGER/gamesir-native-linux` and each approved
component's release asset filename. Every catalog component must occur once;
unknown fields, paths, URLs, foreign repositories and duplicate assets fail.

Canonical URLs are derived from the reviewed tag and filename under
`https://github.com/RetroGamerGER/gamesir-native-linux/releases/download/`.
There is no latest-release lookup, GitHub API/catalog download, token/login,
runtime arbitrary URL or remote checksum that grants itself approval.
Changing a tag's bytes fails the independently pinned hash; a new version
needs a new reviewed catalog/build and matching protected helper trust. The
installed root helper/catalog/protocol are unchanged and never trust the
network or a GUI-supplied approval. TLS and SHA256 do not replace reviewing
package provenance or securing the project's release process.

Only metadata is staged for this mode; embedded package archives mixed with
a release index are refused. The generic source/default build remains inert
with no approved public binary catalog. Existing explicit embedded-bundle
tests/builds remain supported separately; there is no automatic fallback.

## User flow

1. Startup and helper detection/setup read only local reviewed metadata. No
   download occurs on launch, language/status refresh, property access, helper
   reuse/setup or removal. A missing helper retains its separately confirmed
   setup flow; downloading a driver does not install or repair the helper.
2. Select installation components. **Download and check packages / Pakete
   laden und prüfen** explicitly starts the network step in the existing Qt
   worker. The UI explains the source and that installation/password approval
   comes later. It fetches only selected reviewed components, not dependencies
   or other catalog entries. Fresh helper/platform/header/dependency/version
   checks precede transfer.
3. Validate exact declared/received size, hash, safe archive structure,
   package identity/architecture/license/dependencies and core guard contents
   using the existing verifier. Downloads are immutable in-memory bytes; no
   arbitrary cache paths, extraction, downloaded code execution or shell.
4. Collect fresh host facts and reattest the helper **after** download. A
   changed host/session/package state blocks the plan. Only after every chosen
   package passes does the existing exact installation plan appear, including
   canonical release URLs, versions, hashes, source/tag and hook effects.
5. Separate **Confirm and authenticate** remains necessary. Existing root
   verification and ALPM transaction boundaries are unchanged. Successful
   download alone never opens a password window or starts a package action.

Cancel propagates to the worker between bounded I/O calls; late results cannot
recreate a review. Closing the app cancels a pre-authentication download/reader,
then waits for worker completion; it never cancels package hooks/helper setup.
Failure of any selected transfer publishes no partial plan and triggers no
automatic retry, fallback, installation, rollback or activation. Retry, if
desired later, is a new explicit selection/check, never password confirmation
of an incomplete transfer. Verified bytes from an older review cannot replace
a new selected download.

## Later complete uninstall/reinstall test — prepared, not authorized live

The maintainer additionally wants a later complete cycle on the local PC.
The current instruction remains **offline preparation**, with no installation
or live driver change. Complete removal here covers the installed GameSir
package components. The AppImage and separately installed package helper are
retained as the reinstall tool; user overrides/settings, recovery evidence,
dependencies and unrelated controllers/packages remain preserved. This does
not add a factory-reset or automatic deletion of configuration/backups.

Earlier local receipts recorded core alpha3-16 and bridge alpha1-2 installed,
Steam integration absent. These are historical facts, not a fresh inventory
or approval to operate on them. Future execution must use this staged plan:

1. Fresh passive inventory of actual installed components/versions, matching
   kernel/headers, module/service and relevant manager ownership state. Review
   exact package scope and installed cleanup guards, plus retained settings
   and helper ownership. Keep tested recovery archives/configuration backups
   available before removing a working driver.
2. Independently approve/review the actual published binary assets and their
   catalog. Separately verify release availability/bytes before live removal;
   do not first uninstall and discover that no accepted replacement is
   available. Current public binary records are still empty. No download-only
   acceptance, publication or same-version reinstall is implied by fixtures.
3. Show the exact removal plan for all intended installed components, including
   explicitly selected dependents. After a separate approval, close affected
   games/tools and confirm the GUI operation once. Core hooks may return the
   controller, stop/disable service and remove DKMS/module files; their actual
   effects need fresh review. Never interrupt hooks or force-remove a module.
4. Verify actual package/file/DKMS absence and inactive/disabled native service
   and module, plus preservation of the helper, settings, backups and unrelated
   packages. A partial/unknown result stops here, without retry or reinstall.
5. Only after confirmed removal, reopen a **fresh** AppImage transaction session
   and explicitly select the intended previously installed components. The
   normal same-version guard is retained: a real preceding removal makes a
   reviewed version installable; no repair/force switch bypasses that guard.
6. Download/verify selected release bytes, refresh host/helper checks, review
   the new installation plan and obtain separate install/password approval.
   Postcheck package files/DKMS/version and preserved settings. No automatic
   service enable/start, Resume, controller test or reboot; activation remains
   a subsequent separately approved step.

Six additional offline tests exercise core+bridge and all-four-component
remove/reinstall round trips through the existing coordinator, wire parser
and synthetic executor. They also prove dependent omission blocks removal,
failed removal does not chain/retry, failure during the later download creates
no partial install plan and an unexpected remaining native module blocks
reinstallation without being unloaded. They use only temporary metadata,
synthetic inventories/verification records and fake HTTPS/transport; they do
**not** prove real DKMS/hooks/file removal or actual package disappearance.

## Transport limits

The user-side transport uses standard-library HTTPS with certificate/hostname
verification, no proxy environment, credentials, cookies or automatic retries.
Only the exact canonical GitHub URL and explicit GitHub asset CDN hosts
`release-assets.githubusercontent.com` / `objects.githubusercontent.com`, on
their release-asset path, are accepted. HTTP downgrade, userinfo, explicit
ports, fragments, control characters, foreign/other-repository URLs and loops
fail. At most four requests (three redirects); every response is closed.
Signed CDN queries are neither stored nor exposed as errors or plan sources.

Headers/counts, exact Content-Length, unencoded bodies, package byte limits,
10-second socket I/O timeouts and a 90-second per-asset budget checked between
operations bound processing. Chunked/encoded or ambiguous length responses
fail rather than weakening checks. These are cooperative I/O/deadline limits,
not a hard kill of system DNS resolution. Root never performs network I/O.
Real GitHub/CDN response compatibility is deliberately **not** claimed by
offline fakes and must be separately checked with approved published assets.

## Build and tests

The existing build-only `--reviewed-packages` input accepts either the earlier
embedded bundle or the new reviewed metadata-only bundle. The latter contains
`profile.json`, `REVIEWED_PACKAGES.json` and `release-assets.json`; filename/tag
links are supplied only after independent binary-release review. Optional
`--reviewed-helper` still stages the independently reviewed fixed helper bytes
locally. No build step fetches or authenticates; `release_ready` remains false.
Current distribution/kernel/GLIBC/runtime provenance and redistribution gates
are retained. This step does not make the local Garuda profile universal.

Offline tests inject synthetic archives, HTTPS replies, clocks, cancellation,
host snapshots and helper transports. They cover TLS settings, explicit
selection, redirects/loops/downgrades, malformed headers, truncation/oversize,
hash and archive-identity failures, deadlines, sanitized errors, cancellation,
partial-batch refusal, host changes and unchanged authentication boundaries.
Actual offscreen QML tests check download wording in DE/EN, background work,
the distinct later confirmation, errors and cancellation/late completion.
Existing embedded-package and first-run regressions remain required.

Final offline checkpoint: **1,589 Python cases in 57 project groups**, plus
the existing C/kernel-adapter/sanitizer checks, and **58 Qt cases in six
groups** pass. New coverage contributes 23 download/integration cases and
four actual-QML cases. The old blanket network-import guard was narrowed to
permit HTTP/URL parsing only in the explicit downloader (and strengthened to
include HTTP imports elsewhere); the new README guide is included in the
existing package-document export so its links remain valid.

A fresh **generic, read-only** local AppImage was built separately, leaving
the previously accepted image unchanged. All four packaged smoke lanes pass
with bundled Python/Qt and zero privileged calls: status, embedded synthetic
packages, synthetic first run and new `--bundle-release-self-test`. The new
lane ignores real review bundles and injects fake HTTPS replies for a verified
synthetic download, then the existing fake install/removal round trip. No
network or live host transaction occurs. Artifact digest/build logs remain
private; no real binary-release catalog is embedded or enabled by that test.

Before a live/release test: publish/review the actual binary assets separately,
review exact filenames/hashes and helper catalog, finish the distributable
AppImage's runtime/license/privacy/platform audits, then request a narrowly
scoped real download-only test. Installation is another explicit approval.
