# Current: approved public README refresh — 21 October 2026

The README now introduces the project in plain language, with the maintainer's
motivation, a real Control Center screenshot, visible credits, user-oriented
installation steps and concise limitations. The short PRE-ALPHA warning remains
visible; the original full text and GPL-2.0-only notices are retained. Published
versions stay PRE-ALPHA.3/core revision16/Control Center alpha1. ZZZ motion and the
app shutdown correction remain unpublished. Old source-only/unpublished wording
in the linked installation/first-run guides is corrected. Existing technical
documents and release approval rules remain in place. No installed system change.

# Earlier: Control Center alpha1 published — 21 October 2026

The approved clean app snapshot eb99dce is on public main. The existing
v0.1.0-pre-alpha.3 release now also contains the five app assets: AppImage,
complete corresponding sources, distribution lock, manifest and checksums.
GitHub's SHA256 digest, byte size and uploaded state match every local asset;
all previous release asset IDs/sizes/digests remain unchanged, with no new tag.
The actual public signed catalog matches unchanged revision1 and verifies in
both the bundled app runtime and installed helper imported as an ordinary user.
No root invocation/transaction, driver/helper/service/Steam/hardware change.

The license/source publication gap is closed for this Garuda x86_64/glibc2.44
profile. 412 app cases and four final packaged synthetic lanes passed. Keep
private working history and key material private. The encrypted separate-storage
backup copy is complete; no regeneration or resigning. Further app uploads must
retain matching sources/notices/lock/manifest/checksums. Catalog expiry remains
20 November2026,12:36UTC. Driver faults reported on both PCs are the separate
next task; this publication does not fix or certify them. Gyro calibration paused.
See docs/evidence/CONTROL_CENTER_PUBLICATION_20261021.json.

# Earlier: Control Center alpha1 distribution closure — 21 October 2026

The maintainer explicitly requests finishing and pushing the AppImage before
investigating different driver faults on both PCs. Scope is app/source/metadata
publication only: no live driver/helper/service/Steam/hardware changes. Keep
alpha3-16 installed state untouched and precise gyro calibration paused.
Reuse the verified encrypted backup and exact signed revision1; no private-key
read, regeneration or resigning. The requested encrypted off-device copy was
hash-verified on separate network storage (not offline media).

The license/source gap is closed for the reviewed Garuda x86_64/glibc2.44
AppImage profile: 1,859 payload files, 1,530 source-kit files,77 components,
complete recipes/patches/submodules/notices. 412 app tests/25 groups including
61 QML and four final packaged synthetic lanes pass; four real GitHub package
archives pass both download and ordinary-user installed-verifier checks.
Publish binary plus companion sources/lock/manifest/checksums together. Preserve
existing release assets and tag; publish the unchanged signed revision1 at
updates/pre-alpha.json (expires20 November2026,12:36UTC). No new tag is requested.
Use a clean final-tree public snapshot atop public main; retain private working
history locally. See docs/CONTROL_CENTER_DISTRIBUTION.md and its evidence.

# Earlier: AppImage recognizes migrated signed helper — 21 October 2026

After explicit approval, the final reviewed AppImage was opened as the ordinary
user with actual status data, without demo/rehearsal options. Image SHA256 and
staged inputs match the retained build. Its bundled runtime's independent
passive first-run inspection returned idle with no error, setup review/session
or authentication/package invocation. The maintainer confirmed the new main
window appeared normally, with no helper-setup offer or password window.

Read-only postchecks found all thirteen helper hashes and helper/policy/retained
old-executor/cache/license metadata unchanged. The app remains open. No package
installation/removal, updates lookup/download, driver/service/module/Steam change,
hardware test, network or publication occurred. This accepts local Garuda/KDE
reuse of the new signed helper, not signed-download/package acceptance or broader
platform support. Public rollout gates and paused gyro calibration remain.
See docs/evidence/CONTROL_CENTER_SIGNED_HELPER_APPIMAGE_ACCEPTANCE_20261021.json.

# Earlier: signed helper migrated and independently verified — 21 October 2026

Following explicit approval of the newly pinned migration-only plan, the single
run completed with verified_migration/policy_restored and no error. The existing
recovery-verified encrypted key backup was reused without a passphrase prompt,
private-key read, regeneration, decryption or overwrite. The corrected exact
per-path ownership guard passed. No retry, rollback or cleanup was performed.

Independent read-only postchecks confirm all thirteen active helper files match
the approved new hashes, root ownership, modes and single-link requirements;
there are no extra executor entries. The complete old executor is retained at
its fixed before-signed-v1 sibling with original file/directory inodes and
metadata. The identical policy retains its original inode/hash/metadata and
registered auth_admin action. Cache/license directory metadata and the encrypted
backup hash/inode/metadata are unchanged. Candidate, held-policy and failed-new
paths are absent. No package install/removal, driver/service/module/Steam change,
hardware access, AppImage launch, network request, publication or push occurred.

This consumes the one-time migration approval. Do NOT repeat apply or invoke
rollback automatically. The final local AppImage matches the now installed
public-key-bound helper, but no new GUI/package acceptance was performed here.
Public signed-channel publication, actual download/package acceptance, runtime/
corresponding-source redistribution audit and off-device encrypted-backup copy
confirmation remain separate pending rollout gates. Gyro calibration stays paused.
See docs/evidence/CONTROL_CENTER_HELPER_MIGRATION_ACCEPTANCE_20261021.json.

# Earlier: ownership correction tested; migration-only plan ready — 21 October 2026

Following the maintainer request, the migration now checks each of its thirteen
fixed helper paths separately. Each query must return exactly 1, empty stdout
and exactly that path's unowned diagnostic. Never accept arbitrary nonzero
codes or silently skip a path. This removes the erroneous aggregate-status
assumption (the observed thirteen missing owners returned 13), retaining all
other ownership/runtime/quiescence/state/rollback protections.

334 Control Center tests in 17 groups pass, including 26 migration tests and
seven new regressions: reproduced aggregate 13, all per-file queries, owned
paths at every position, invalid codes/diagnostics/stdout, timeout and blocking
before any privileged command. No actual host package query or live migration
was run during this correction. The installed helper/driver remain unchanged.
A new exact migration-only plan pins corrected sources; old/new root payloads,
public key and all 19 privileged commands are unchanged. The existing encrypted
backup matches the earlier recovery-verified hash and safe 0600 metadata; it was
not decrypted/recreated and the private key was not read. No new signing.
The previous final AppImage still matches the root payload; this fix is in the
separate maintainer migration path, never invoked by normal first-run GUI.

Execution still needs approval of the newly pinned plan, passive backup recheck,
then one migration-only run/password flow and read-only postcheck. Do not rerun
the old backup-then-migration command or overwrite the existing backup. No
installation/activation/hardware/system change or publication under preparation.
Off-device backup confirmation and public rollout gates remain open.
See docs/evidence/CONTROL_CENTER_OWNERSHIP_FIX_20261021.json and the normal-user
flow in docs/CONTROL_CENTER_FIRST_RUN.md. Gyro calibration remains paused.

# Earlier: backup verified; helper migration blocked — 21 October 2026

The maintainer approved the complete encrypted-backup/helper-only handover.
The real production-key backup was created with hidden terminal input and
verified by RAM-only recovery/public-key identity. The local encrypted file is
0600, user-owned and single-link; an off-device copy is still pending. Do NOT
rerun the original backup-then-migration command: its exclusive destination now
exists. Preserve the key, backup and signed catalog; no regeneration/resigning.

Migration stopped in preflight before any sudo/system mutation: the exact
thirteen-path ownership query returned 13 with all thirteen expected unowned
file diagnostics and empty stdout, while our guard incorrectly required 1.
Independent checks confirm all 13 old helper files retain hash/owner/mode/inode/
mtime, the executor/license/cache directories retain metadata, and all migration
staging/backup/held-policy paths are absent. No driver, bridge, Steam, module,
service, package or publication action occurred; no automatic retry/rollback.
Only read-only diagnosis followed. The signed helper has NOT been installed.
Next: correct this aggregate return-code assumption offline with regression
coverage, then prepare a new exact migration-only approval reusing the verified
backup. Do not loosen ownership diagnostics or change approved pinned bytes
silently. Latest instruction after this run is checks only.
See docs/evidence/CONTROL_CENTER_HANDOVER_EXECUTION_20261021.json.

# Earlier: consolidated handover/final local AppImage — 21 October 2026

The requested offline preparation is complete in one pass: encrypted PKCS8
backup utility, exact legacy-to-signed helper migration, explicit partial-stage
recovery and a single approved backup-then-migration launcher. No real production
backup, key read, sudo/authentication, installed helper/state/package, service,
driver/Steam/hardware/network change or publication. Concrete private plan and
commands are retained outside Git; [workflow and limits](CONTROL_CENTER_HANDOVER.md).
AppImage SHA256:
`19cacca0bac2ac009749c05065a9d4f81ca050d9aa1beabab72cf4aa508d7ad9`.

388 Control Center cases/24 groups (including61 QML), four full packaged
synthetic lanes and actual-old/new-payload fixture migration/recovery pass.
38 new regressions include encrypted backup/recovery/KDF, actual tty/no-echo,
no stdin fallback, exclusive outputs, ownership/lock/process/state rejection,
whole-directory replacement, failure preservation and partial recovery.
The public key, signed revision1 and thirteen helper pins remain unchanged.
Unchanged artifact bytes reuse the preceding private-material scan; only public
migration code/hash-only legacy manifest were added. No production key was
regenerated or copied. End-user first-run is unchanged; no GUI auto-repair.

Next requires only one exact consolidated handover approval: backup phrase
twice in a real terminal, verify encrypted file, fixed helper-only system
commands/password flow, postcheck, stop. Local encrypted staging backup still
needs a separate-storage copy/confirmation before public rollout. No driver
package reinstall or automatic AppImage launch is part of this plan. Runtime/
corresponding-source redistribution audit, signed-channel publication and real
package acceptance remain separate. Gyro calibration stays paused.

# Earlier: production key and offline-bound builds — 21 October 2026

Following explicit approval, a new external Ed25519 release key was created
without root or private-key terminal/log output. User-owned custody directory
0700, private regular single-link DER0600; no private key in Git, AppImage,
helper or build. Only the [public policy](../packaging/control-center/release-signing-policy.json)
is tracked. Public key ID:
`5d9450389dafad61bb573c277557a62484e514c96dcb1acd40b9bcfe5f71544a`.
An explicit new helper/AppImage build uses this same public anchor; generic
source defaults remain opt-in/no-key. Core16/Steam2/Gamescope1/bridge2 archive
bytes and five accepted removal records are reused unchanged. No rebuilding
or replacement of published package versions.

Catalog revision1 is signed and independently verified from bundled AppImage
Python and the staged helper modules; lifetime30 days, currently unpublished.
Signature/payload tampering, expiry and an unknown key are rejected in both
contexts. 67 targeted unit/packaging tests +3 QML cases and four actual packaged
synthetic smoke lanes pass. Private-material inclusion checks pass; all thirteen
installed helper leaves and three directory metadata snapshots remain identical.
Cache contents unopened. No authentication, installed trust/state/package,
service/module/driver/Steam/hardware/network change or push/publication.

AppImage SHA256:
`ab90d0a57cb6e7134f35e74f69f7940b8b306054607f90aa1bc09f6912dc0da2`.
[Sanitized evidence](evidence/CONTROL_CENTER_PRODUCTION_SIGNING_20261021.json).
Retained signed metadata history is not a private-key backup; encrypted offline
key backup remains pending before publication. One-time helper migration still
needs its tested implementation/exact command review and explicit approval.
The current installed helper is deliberately unchanged and will not match the
new image's helper pins. Public runtime/source distribution review, real signed
channel acceptance and package tests remain separate. Gyro stays paused.

# Earlier: production signing/migration approval plan — 21 October 2026

The maintainer requested the plan before productive key creation or helper
replacement. [The staged proposal](CONTROL_CENTER_SIGNING_PROVISIONING.md)
covers external Ed25519 custody, public fingerprint review, an offline-bound
AppImage/helper build, then a separately approved exact helper-only migration
and preserved recovery. All thirteen installed helper leaves match independent
accepted pins in ordinary-user read-only inspection; no unexpected executor
entries. Five helper modules plus the future public-key catalog change. Entry,
policy, native bridge, license and remaining modules retain reviewed bytes.
Root0700 cache metadata is preserved; contents were not read/assumed empty.
No ALPM lock or scoped named package/auth process was observed; deployment
must establish absence of in-flight helpers before switching, not assume it.

No key generation, signing, authentication, candidate deployment, installation,
package/service/module/driver/Steam change, network, hardware access or push.
Final public fingerprint/artifact pins and migration implementation/tests are
pending. Existing first-run setup is not a helper updater. No protected-state
reset or automatic rollback after signed-catalog acceptance. Publication and
real signed-package acceptance remain separate. Gyro calibration stays paused.

# Current: signed package updates implemented offline — 21 October 2026

The Control Center and root package helper now independently verify signed
Ed25519 release catalogs through system OpenSSL. Static public-key/helper pins
remain unchanged across compatible driver releases; no remote self-approval or
root network I/O. Version-3 requests carry bounded signed metadata. Native ALPM
comparison rejects downgrades/rebuilt same-version bytes; root checkpoint under
the ALPM lock enforces revision/time/history and atomic protected-state writes.
Accepted metadata and actual package success are recorded separately. Legacy
fixed-pin builds stay supported; no production update key is configured.

An explicit worker-based DE/EN update check, cancellation and reverified user
cache are connected. Offline removal can use protected prior approvals after
expiry. An offline publisher utility signs with an existing external key only;
no key generation or upload. The two-version end-to-end regression retains the
same AppImage profile and helper anchor, then removes after restart/expiry
without network. Details and deployment limits: [signed updates](CONTROL_CENTER_RELEASE_UPDATES.md).
No installation, active helper/state/driver/service/Steam/hardware change or
publication. No real channel request or production signing key. Gyro paused.

Final acceptance: 1,628 Python cases in 60 groups and 61 offscreen QML cases
in seven groups pass; 28 + three specifically exercise signed updates. The
helper payload/native bridge stages successfully with the existing 13 files.
Signature verification also passes under bundled AppImage Python with public
fixtures. [Sanitized acceptance record](evidence/CONTROL_CENTER_SIGNED_UPDATES_20261021.json).

# Current: public-package AppImage rebuild — 21 October 2026

New local metadata-only AppImage embeds the reviewed v0.1.0-pre-alpha.3
package hashes/URLs for core16, Steam2, Gamescope1 and bridge2. It includes no
package archives and performs no startup download. Accepted removal records,
core cleanup guards and Steam alpha1-1 upgrade eligibility are preserved.
89 targeted tests and four complete AppImage bundled-runtime/QML self-test
lanes pass offline. The real reviewed package bytes also passed an offline
fake-download/wire/helper install/remove round trip for core/Steam/bridge;
Gamescope remains rejected by the Garuda planner. No live package action.
The old installed helper catalog is deliberately not adopted or overwritten;
its differing pin blocks authentication until a separately approved helper
catalog deployment. The old accepted AppImage is preserved. No installed
helper, driver, service, module, package or Steam change; no public upload.

Future driver versions must not require a new AppImage. The current fixed-pin
build does not meet that additional requirement yet. The [signed release
catalog design](CONTROL_CENTER_RELEASE_UPDATES.md) covers independent GUI/root
verification, stable key trust, replay/rollback controls and protocol migration.
It is a design, not an implemented updater. No production signing key was
created, no root trust changed and gyro calibration remains paused.

# Installable release supplement — 21 October 2026

The maintainer approved adding installable packages to existing public release
v0.1.0-pre-alpha.3. Four ALPM packages were rebuilt from exact public source
commit b5b9cc34534e5afdb6505322308b364f15e31c2b in a neutral build directory:
core alpha3-16, Steam alpha2-1, Gamescope alpha1-1 and bridge alpha1-2.
Build check phases, existing Control Center archive verifier, staged payload
comparison and private-marker review passed. Supplemental manifest/checksums
and closed download index follow [the upload policy](RELEASE_PACKAGE_SCHEMA.md).
New archive hashes need an explicitly reviewed AppImage/helper catalog build;
the installed catalog remains unchanged. No installation/removal, service,
module, hardware or running-driver change. Gyro calibration remains paused.

The supplement is now published in the existing release. All nine added assets
match GitHub SHA256/size records; all eight original assets remain unchanged.
The real user-side ReleaseDownloader downloaded and verified all four package
archives through GitHub/CDN against the independently reviewed local pins.
This confirms download/format acceptance, not a real install or helper update.

> Public export: personal tester, host and path references were anonymized. Historical evidence hashes refer to the private originals.

## Current: alpha3-16 frozen; local AppImage helper first run accepted

Latest offline addition, 21 October: the requested later full uninstall/reinstall
cycle has six extra synthetic regressions and a
[staged live-test proposal](CONTROL_CENTER_GITHUB_PACKAGES.md#later-complete-uninstallreinstall-test--prepared-not-authorized-live).
Core+bridge and all-component removal -> fresh release-install session pass;
dependents, failed removal/download and an unexpected remaining module stop
safely. No automatic chaining/repair/unload. AppImage/helper and retained user
settings/recovery records remain the future reinstall foundation. No fresh
live inventory, network, authentication, package/driver change or GUI launch
occurred; real assets/preflight/removal/install/activation need separate stages.

Latest offline work, 21 October: [reviewed GitHub package downloads](CONTROL_CENTER_GITHUB_PACKAGES.md)
are prepared as an alternative to embedded packages. Build-selected metadata
maps fixed reviewed tags/hashes/sizes to project release asset filenames;
startup/helper reuse/setup/removal stay offline. Explicit selected download
and archive checks precede fresh host/helper checks and a separate install/
password confirmation. Cancellation/failure cannot publish a partial plan.
Root helper/catalog/protocol unchanged, public binary records still empty.
No network/live launch, authentication, installed-helper/package/driver/bridge
change or publication. Real CDN/assets and distributable build acceptance are
separate; the accepted local AppImage remains untouched.
Final offline checks pass: 1,589 Python cases/57 groups, existing native suites,
58 Qt cases/six groups and four packaged fake smoke lanes, including the new
release-download lane. The fresh generic read-only artifact uses no public
binary catalog and made zero network/auth/host package calls.

Latest local acceptance, 21 October: a separately authorized second launch of
the exact AppImage recognizes the installed helper without setup offer or
password window, confirmed by the maintainer. Fresh passive inspection is idle;
independent postchecks verify unchanged bytes/owners/modes/inodes/mtime for all
thirteen leaves/three directories, preserved legacy helper/backups and unchanged
core/bridge/module/service baseline. No setup/auth/package or driver change;
Steam remains absent. Scope remains local reviewed Garuda, not Gamescope.

Latest separately approved local result, 21 October: fresh retained-backup,
exact image/source/payload, Garuda kernel/header and missing-helper gates
passed. The maintainer completed the thirteen-file/three-directory helper-only
setup through the AppImage/password flow and reported success. Independent
passive file/hash/mode/root-owner/loaded-policy checks passed; fresh inspection
reuses the installed helper without authentication. Done closes only the modal
and leaves the main window normal, as confirmed by the maintainer.
Old backups/unopened cache and legacy helper remain intact; core16/bridge2,
module metadata and enabled/active service unchanged, Steam still absent.
No package action, activation, restore/cleanup or further authentication.
Approval consumed; this is local reviewed Garuda helper bootstrap acceptance,
not generic clean-system/Gamescope deployment or public binary approval.
[Evidence and scope](CONTROL_CENTER_FIRST_RUN.md#local-first-run-acceptance).

Earlier controlled rollback result:

Latest separately approved local result, 21 October: all four controlled
same-parent helper/policy/license/cache renames succeeded after fresh pins/
before checks and individual intermediate gates. Held and restore-ready
checks passed: thirteen original leaves/three dedicated live directories and
registered package action absent; saved bytes/owners/modes/inodes match.
Root0700 cache contents remain unopened in their complete original directory.
Legacy authorization helper/shared parent, core16/bridge2, loaded module
metadata and enabled/active service remain unchanged; Steam stays absent.
No package action, restoration, cleanup or first-run AppImage test followed.
This rollback approval is consumed; new setup/restore needs separate approval.
[Scoped result and recovery limits](CONTROL_CENTER_FIRST_RUN.md#controlled-rollback-preparation-for-a-later-first-start-test).

Latest read-only checkpoint, 21 October: the existing thirteen-file package
helper, three directories and six legacy authorization leaves match the
reviewed hashes/ownership/modes; no package-owned helper file or observed
package/auth operation/ALPM lock. A private controlled rollback plan for a
later first-run test preserves policy/code/license/cache by four fixed
same-parent nonoverwriting renames, with intermediate passive gates and a
separate reverse path. Root0700 cache contents were not inspected or assumed
empty. Eight temporary-fixture checks and22 first-run unit tests pass.
No authentication, removal/rename, setup or system change occurred. Core16,
bridge2 and service state stay unchanged; Steam integration stays absent.
Actual rollback and later first-run confirmation require separate approval.
[Scope and recovery limits](CONTROL_CENTER_FIRST_RUN.md#controlled-rollback-preparation-for-a-later-first-start-test).

Latest development, 21 October: [first-run helper setup](CONTROL_CENTER_FIRST_RUN.md)
is prepared offline. A build-selected payload enables passive missing/exact/
partial detection and an explicit setup review/password flow. Only fixed
system mkdir/install commands receive sealed bytes; root never executes
AppImage code. Exact existing helpers are reused, partial/conflicting state
blocks, policy is last and failure stops without retry/rollback. Done closes
only the modal and triggers fresh passive planning, never a package action.
No live inspection through this setup path, authentication, helper update,
package action or driver change occurred. Real first-install/agent acceptance
remains separate; the current host's existing helper is not removed for a test.

Earlier scoped live result:

Latest scoped result, 21 October: after a Steam-only read-only removal-plan
review in the new AppImage, the maintainer independently completed removal
and reported “Successfully uninstalled”. Independent passive postchecks
verified Steam integration/package absence and all five payload files absent;
core alpha3-16, bridge alpha1-2, helper pins, native module metadata/presence
and service enablement were unchanged. The maintainer confirmed Done closes
only the operation dialog and leaves the main window open. Steam integration
is now **absent**; no automatic reinstall or activation was attempted. This
accepts that optional-package removal and success UI only, not core removal,
remote/Gamescope or clean-system bootstrap. No new package action is implied.

Earlier installation/refinement checkpoint:

Latest 21 October: the separately approved real AppImage installation of
**Steam integration alpha1-1 → alpha2-1** succeeded. The maintainer reported the
verified package result; independent passive postchecks verified its five
root-owned payload files/modes/bytes and version, unchanged helper pins, core
alpha3-16/bridge alpha1-2, native module metadata/presence and service enablement.
No removal, driver activation or Steam restart ran. This accepts this one local
optional-package install, not core installation/removal, Gamescope or clean-
system helper bootstrap. The operation approval is consumed.

The requested success-dialog refinement is prepared offline: a verified
install/removal shows “Successfully installed/uninstalled” (DE/EN) and Done.
Done closes only the operation dialog; the main window stays open. Failures,
cancellation, uncertainty and fixture rehearsals cannot claim real success.
No extra package operation is part of the UI tests/build.

Earlier read-only acceptance:

Latest acceptance, 21 October: the maintainer approved a live **read-only**
AppImage opening and package-plan display. The exact image hash and passive
helper/kernel/header/inventory checks passed. The maintainer confirmed the
visible Steam integration alpha1-1 → alpha2-1 plan without final confirmation.
Core alpha3-16/bridge alpha1-2 are already present; no same-version repair is
offered. No password request, submission, package action or driver/service/
Steam change occurred. Real installation/removal remains separately gated;
expired or changed plans need fresh review before any later action.

Earlier offline checkpoint:

Latest 21 October: [AppImage package binding](CONTROL_CENTER_APPIMAGE_PACKAGES.md)
is now implemented/tested offline. Explicit build-selected local review data
connects startup/selection background inspection, exact plan and one-shot
install/removal confirmation to the existing separately installed helper.
No request on launch/review; missing/mismatching data locks actions. Properties
use cached facts; selected planning is refreshed before confirmation. Demo,
generic read-only builds and the synthetic packaged test remain separate.
No live launch through this binding, authentication, host package action,
helper/driver/service/Steam change or push occurred. Separate real install and
removal acceptance remain pending; gyro calibration stays paused.

21 October, after explicit approval of the concrete setup from `f30638e`:
the separate local Garuda package helper/catalog/policy is now installed.
Fresh passive gates passed; thirteen exact root-owned files and three new
directories were created through fixed install commands using sealed inputs.
Installed hashes/modes and the registered Polkit action passed; the existing
authorization-only helper was preserved. No package/permission probe,
transaction, hook, manager/device access or driver/service/module/Steam change
ran. Normal GUI/AppImage remains read-only. This is helper deployment only,
not GUI installation/removal acceptance or remote/Gamescope approval. No push;
gyro calibration remains paused. [Scope and result](CONTROL_CENTER_DEPLOYMENT_REVIEW.md).

Earlier preparation checkpoint (before that approval):

Later 21 October review: [concrete packages, passive planning and helper setup](CONTROL_CENTER_DEPLOYMENT_REVIEW.md)
are checked locally. Core alpha3-16 matches its retained receipt and public-tag
payload; optional Steam/bridge candidates were rebuilt/audited from that tag.
Gamescope is excluded on this Garuda target after missing dependencies stopped
its build. An explicit data-only full-inventory reader shares the root adapter's
facts and passes two successive unprivileged snapshots with matching headers/
prerequisites. Empty optional makepkg URLs and r-prefixed VCS inventory versions
have targeted parser regressions. The package helper gains a fixed protected
closed-data catalog; public/default catalogs stay empty, the local three-package
review is private/noninstalled. Thirteen-file/three-directory setup and guarded
removal are prepared separately, using sealed stdin and no privileged script.
No sudo/pkexec prompt, host ALPM handle/lock/transaction, hardware/manager access,
helper deployment or installed driver/service/Steam change. Normal GUI remains
read-only; separate live integration/installation acceptance is still required.

21 October 2026: after the successful permission-only checkpoint, a distinct
package action/helper, strict byte-stream protocol, one-shot GUI submission,
independently checked root executor and narrow native ALPM bridge are prepared
offline. Actual Qt confirmation/worker/result wiring is tested with injected
boundaries; real libalpm only uses an empty temporary root and harmless marker
packages. System adapter and optional helper staging are source-only; root
catalog/public binary approvals remain empty. Normal CLI/AppImage stays
read-only; no live factory/flag is enabled. No new helper deployment, password
request, host package/driver/service/module/Steam change or hardware test.
The [package design, safety limits and proposed separate live steps](CONTROL_CENTER_PACKAGES.md)
are ready for review. Local commit only; no push. Gyro calibration stays paused.

20 October 2026. PRE-ALPHA.3 source/tag has been published. Under separate
approval both test systems received core alpha3-16 and were reactivated; the
matching DKMS builds, source revisions, module options, sensor configuration,
service/autostart and receiver waiting were checked. No new game, cold-boot,
suspend or repeated-reconnect acceptance is implied by those operations.
The maintainer now tests both systems in normal play over several days and
records problems. No driver runtime changes during the GUI task; only the
separately approved helper setups documented here were installed.

After visual acceptance of Phase A, the [Control Center](CONTROL_CENTER.md)
adds **Phase B**: genuine unprivileged local metadata snapshots of distro,
architecture, kernel/prepared headers, packages/dependencies, loaded module,
DKMS registration, system service/enablement and individual GameSir USB
identities/bindings. Explicit asynchronous refresh, timestamps/age warning and
unknown/denied/partial states; no overlapping collection or automatic retry.
Real install/remove handlers and buttons stay disabled. The privileged manager
is not queried and RF connection is not inferred from USB presence. No direct
device or network access, administrator adapter or system mutation.
The maintainer approved a compact main view: a System details button now opens
technical metadata in a separate read-only dialog for experienced users. It
reuses the snapshot without extra queries or displacing the main page; DE/EN,
keyboard/focus and small-window scrolling are covered by 26 QML tests.
Phase C adds an offline artifact verifier, strict schema-1 component requests,
review-bound install/remove plans, one-shot acknowledgements, injected-only
transaction rehearsal and independent postchecks. Existing four staging
helpers/ALPM cleanup policy are exercised on synthetic inventories; no new
USB/recovery implementation. First failures survive, unexpected package
transactions and activation are rejected. The binary catalog remains empty
for the source-only publication. No live transport, real authentication,
downloads or package actions; GUI install/remove remain locked. Gamescope
status lookup now uses the actual `gamesir-native-steam-gamescope` recipe name.
See [contracts, offline tests and live-integration gates](CONTROL_CENTER.md).
DE/EN, the isolated demo and explicit GitHub/Deadband links remain. Synthetic
detector/transport regressions and QML input tests pass; one authorized local
metadata snapshot rendered successfully. No remote/Gamescope or controller
acceptance is inferred. Phase D adds offline AppDir/type-2 AppImage and Desktop
Entry/icon staging with a synthetic self-test. Interpreter/Qt are bundled;
local glibc baseline 2.44, runtime/dependency redistribution review pending.
No cross-target or public binary-release acceptance is implied.
[Build and limits](CONTROL_CENTER_APPIMAGE.md). Live backend and desktop
installation require separate review and authorization.
The maintainer then accepted genuine read-only AppImage status on the local
desktop. The new explicit --rehearse-backend source mode connects QML selection
and review to the real Phase C planner/one-shot Session through a background
Qt worker, using only in-memory catalog/package/host fixtures. Normal status
actions remain locked; no privileged helper or live package transport exists.
Fifteen coordinator and eight extra QML cases cover install/removal, dependency
gates, stale/mutated plans, cancellation, worker responsiveness and first errors.
The future real authorization/transaction flow is documented for review in
[Control Center](CONTROL_CENTER.md#future-real-flow-presented-for-maintainer-approval).
No built AppImage or installed runtime is replaced by this source-only step.
The GUI install/removal rehearsal was then accepted. Authorization-only Polkit
helper/policy source, a pinned fixed pkexec transport and strict correlated
one-shot JSON client are now prepared and staged offline. The helper has no
package executor, arbitrary command/path or device operation; it returns only
`authorized_only`/`executed: false`. Twenty-seven offline boundary cases and an
extra QML cancellation case use fake agents/root identity and harmless same-user
process fixtures; no real pkexec, root prompt or installation. GUI defaults
remain locked. [Scope and deployment gates](CONTROL_CENTER_AUTHORIZATION.md).
Subsequent read-only local preparation confirms active nonremote KDE Wayland,
running Polkit/KDE agent and compatible protected system prerequisites. All
optional helper/policy/license destinations and the custom action are absent.
Source/payload pins match commit `580124c`. Exact sealed-input setup, one probe
and guarded rollback commands are prepared privately for review; a same-user
fake-root exercise passes. No sudo/pkexec prompt, root installation, live probe
or runtime change occurred during that preparation checkpoint.
After explicit approval, fresh gates passed and the exact six root-owned
helper/module/policy/license files plus three directories were installed from
sealed inputs. Installed hashes/modes/ownership and loaded action matched.
Exactly one real local KDE Wayland permission-only probe returned
`authorized_only`, empty error and `executed: false`; final read-only file/action
attestation passed again. No package transaction, manager/service/module/Steam
action or driver change. The optional helper stays installed; normal GUI
actions remain locked. This does not accept a real package executor,
Gamescope authorization, live cancellation or rollback. No retries or removal.
See [scoped live result](CONTROL_CENTER_AUTHORIZATION.md#approved-local-permission-only-result).
Local commits only; no new push/release. Gyro calibration remains paused.

The earlier entries below preserve their original scopes and dates.

## Current: accepted revision15 runtime; revision16 package policy for PRE-ALPHA.3

Revision16 packages receiver_wait=1 as a vendor modprobe default, preserving
same-name /etc overrides and leaving service activation explicit. It changes
no kernel runtime or installed system. The maintainer requests a source push
and new tagged PRE-ALPHA release after tests/privacy/function audit.
[Release notes](RELEASE_PRE_ALPHA_3.md), [functional audit](FUNCTIONAL_INTEGRATION_AUDIT.md).

**The maintainer accepts the demonstrated automatic binding as a usable current
state.** The reported brief initial xpad contact is not a blocker. A SteamOS
reaction is a possible explanation suggested by the maintainer, not a proven
cause. No additional first-binding investigation is required for this accepted
checkpoint. Fully xpad-free first probe is not claimed; cold-boot/reconnect and
application coverage retain their existing scope. This decision requests no
new system changes, live test, push or release.

Measured late-on result:

**One approved late power-on completed automatically without extra inputs.**
Fresh preflight reattested the waiting lifetime before the armed cue. After the
maintainer's single power-on, a new 100a lifetime appeared and received its own
controlled bootstrap/handoff to native109c, state7/error0/pad1/imu1/handover1.
Manager active, exact input publication and both gamepad/motion names confirmed;
10.415 seconds of stable active ownership, no new error or service restart.
This was a new-lifetime acquisition, not same-object WAIT9→READY7. Budget has
two starts across the original wait and new source, with no manual replay.
The maintainer reports initial xpad contact; polls first see 100a already
native, so the short first-bind interval is unresolved. Do not claim fully
xpad-free startup, cold-boot/reconnect or application acceptance from this run.
No further input, manual Resume/Release, installed change or push.
[Late-on audit](RELEASE_AUDIT.md#revision-15-late-power-on-starts-automatically--20-october-2026),
[sanitized receipt](evidence/RECEIVER_WAIT_LATE_ON_20261020.json).

Earlier receiver-off waiting checkpoint:

**Receiver-off waiting is confirmed in one approved insertion test.** Fresh
preflight passed; the maintainer reinserted the receiver with controller off.
Kernel startup returned state9/error0 with no pad/IMU, and manager plus saved
lease remain receiver_wait for 45.653 seconds across ten samples. Same USB
lifetime/tokens/diagnostic, unchanged one-attempt budget, one matching bootstrap
result in the retained journal; no new error or xpad fallback. A private observer
newline/empty-list reporting defect was corrected offline before a fresh
read-only observation; service and runtime were not changed. Receiver stays in,
controller stays off, and **no power-on Go has been given**. Later power-on,
controller-off boot/reconnect and application acceptance remain pending.
[Waiting audit](RELEASE_AUDIT.md#revision-15-receiver-off-waiting-confirmed--20-october-2026),
[sanitized receipt](evidence/RECEIVER_WAIT_CHECK_20261020.json).

Earlier installation checkpoint:

**Revision15 is now installed and explicitly opted in on the CachyOS target.**
One approved removal/Release proved empty paused ownership, one package update
passed all hooks/DKMS/payload checks, and one config creation/service start loaded
receiver_wait=Y with the unchanged sensor profile. The immediate status query
returned ENOENT; its guard stopped before Resume. Independent readback
proved the same service responsive, paused/empty and healthy; only the remaining
once-approved Resume was then executed. Final state: service active/enabled,
zero restarts, new module srcversion, unpaused empty devices and persisted leases.
Receiver remains out/controller off. No actual state9/late-on/game/boot acceptance
is implied; no other host, Steam configuration or push changed.
[Installation audit](RELEASE_AUDIT.md#revision-15-installed-and-opt-in-activated--20-october-2026),
[sanitized receipt](evidence/RECEIVER_WAIT_INSTALL_20261020.json).

Earlier preparation checkpoint:

**Revision 15 update is prepared for the CachyOS target, not installed.** Fresh
approved reads find matching kernel/headers `7.2.11-1-cachyos-deckify`, clean
revision14/integration packages, active/enabled service, and 109c/xpad with a
blocked current-boot lease and retained -110 VERIFY5. The new receiver-wait
module builds unprivileged with matching GCC and zero warnings. Installation
needs controlled physical return and independently verified paused/empty
ownership before the exact update; activation is a separate explicit opt-in.
No package/module/service/binding/configuration change or test occurred.
[Build, update gates, activation and rollback](RECEIVER_WAIT_UPDATE.md).

An experimental **kernel receiver-wait implementation is now prepared offline**.
Opt-in receiver_wait defaults false; packaged configuration is unchanged. One
bounded setup can return pending state 9 and keep RX indefinitely without
initialization replay/OUT traffic. Fresh native IMU alone permits the bounded
handoff; updated client/manager preserve exact ownership, no-repeat budgets,
restart attestation and END/fault handling. Active-runtime functionality and
publication gates remain on their existing paths. Suspend of an unready wait
cancels safely; automatic restart of that cancelled wait is not implemented.
No installation, loaded module change, SSH/hardware access or push. Real
controller-off/late-on behavior remains unaccepted; the historical reboot
failure is not retroactively fixed. [Implementation and validation](RECEIVER_WAIT_KERNEL.md).

The focused **offline PID-transition comparison** rehashes eleven originals
and identifies four captured 109c->100a transitions: one passive power-on
association, three in software-return contexts. No synchronized 100a/off
counterexample is established, but neither is a sufficient automatic RF-ready
trigger. The old radio-cycle confirmation is too coarsely timed to label its
intermediate 100a. Prefer a kernel receiver-wait contract, retaining finite
initialization/transfer bounds and a thin ownership/recovery manager. This is
an architectural recommendation, not an implemented standby or late-on fix.
No byte hunt, live access, runtime change or push.
[Comparison, negative controls and decision](RF_PID_TRANSITION_COMPARISON.md).

The new reference has now been decoded **offline**: all 3,571 new-epoch EP82
reports have valid 20-byte XInput framing. Eleven initial reports are entirely
neutral; changed inputs arrive only after a 34.707839-second gap and the human
input cue. This demonstrates input transport/operation in this run, not a
sufficient automatic RF-ready witness before user input. Four full startup-query
replies are observed; short HID reports and LED outputs are distinct from GIP
status or IMU activation. Earlier native starts cannot supply a missing native
IMU phase for this XInput run. Preserve exact-instance ownership and native
init/IMU READY; do not introduce a button gate, silence-based disconnection or
retry on this evidence. 7,195 records independently crosschecked; original
rehashed, raw data private. No live access or runtime code changed; no push.
[Findings, chronology and manager recommendation](RF_LINK_CONNECTION_WITNESS.md).

One approved primary-machine passive RF reference now **completed successfully**.
KDE's exact IF0 consumer was confirmed open, then usbmon separately loaded once
and its dynamic monitor identity verified. Fresh preflight and local terminal GO
preceded the bounded capture. Isolation/finalization and 24 original checksum
entries pass; the maintainer confirms visible normal input and desktop stability.
After the power-on cue, the old 109c/xpad epoch ended (-108, zero data), followed
by a new same-parent 100a/xpad+usbhid epoch and 3,571 successful 20-byte EP82
transfers. No 64-byte EP82/84 completion observed in this selected reference;
no RF-ready bit proved by that initial metadata review. Native remains paused/empty, no
Resume/retry/reset or forced mode change. Raw whole-bus evidence stays private.
[Completed run and limits](RF_LINK_109C_CAPTURE.md#approved-capture-completed).

One separately approved primary-machine RF preflight stopped at the old combined
109c/xpad/ordinary-consumer gate. Empty stdout and retained generic stderr do not
identify its individual missing condition. The helper is now refined **offline**:
success/failure JSON keeps original diagnostics, partial cached observations,
exact expected/observed fields and untested stages. No input node, an unopened
node and incomplete inspection remain distinct. Failed reports cannot produce
a capture manifest. 58 RF tests (14 added) and full make test pass. No further
live read, capture or installed change; no retry/push. Native remains last
verified paused, controller reported off. [Details and limits](RF_LINK_109C_CAPTURE.md#preflight-diagnostics-corrected-offline).

New primary-machine reference recorder is now prepared **offline only** for
109c/xpad, 90 s. See [scope and staged commands](RF_LINK_109C_CAPTURE.md).
Local GO starts the reviewed isolated chain; 30 s preparation precedes one
power-on, confirmation before 60 s gates the input/motion phase, final rest
starts at 80 s. Metadata/source/process/consumer guards, separate enumeration
epochs and bounded unknown reads do not imply RF readiness. Native remains last
verified paused with empty ownership; controller reported off, receiver plugged.
No fresh host/SSH read, capture, usbmon load or runtime change this step. New
privileged reads and capture need explicit future approval. No push.

Primary-machine staged physical return stopped on PID mismatch. One approved
removal proved absence, empty ownership and returned=true after the pause;
original -108 history is retained. After approved reinsertion with controller
confirmed off, the new device is still 109c/xpad (IF1 unbound), not 100a. Native
remains paused and leases/devices/native bindings are empty. No capture, retry,
power-on or new release/resume/module/binding operation followed.
[Completed phases and proof limits](RF_LINK_CAPTURE_PLAN.md#approved-physical-return-attempt-administration-cleared-still-109c).

The selected primary-machine reference now starts from 100a under xpad to
observe radio registration. Controlled physical return is prepared only:
fresh paused baseline, cue removal, at least 15 s absent plus verified empty
ownership/returned=true, then cue same-port reinsertion and prove 100a/xpad/usbhid
with pause retained. Actual installed-policy offline checks preserve diagnostics
and treat unknown metadata as unknown. No live read or physical action yet;
last verified state remains paused 109c/xpad with one old blocked lease.
[Prepared return sequence and approval boundary](RF_LINK_CAPTURE_PLAN.md#manual-return-to-100a-prepared-not-started).

Primary-machine Native management is now **paused**, confirmed independently
in live status and persisted state after exactly one approved release. The
client returned exit 1/returned=false; current 109c/xpad binding and the single
blocked old 100a lease/failure history are unchanged. A complete return is not
confirmed. No retry, resume, recording, module/binding or physical action.
[Completed release, proof and remaining boundary](RF_LINK_CAPTURE_PLAN.md#approved-release-completed-pause-confirmed-return-unresolved).

Primary-machine pause preparation now includes a stable protected ownership
read: one blocked old 100a lease without tokens/candidate/job remains, while the
replacement 109c is on xpad. Installed manager source and pure-method offline
simulation support proposing one release to persist pause, not a successful
fallback. The client can wait 45 s and return exit 1/returned=false. No actual
release, stop/resume, recording or system change occurred.
[Concrete command and limits](RF_LINK_CAPTURE_PLAN.md#controlled-pause-prepared-after-ownership-read).

Primary-machine preflight is now read and stopped: the approved one-shot helper
observes `109c` on xpad but unpaused native management with a blocked, unowned
replacement entry. Stored bootstrap error is -108 at stage 1, not the separate
Gamescope target's -110 VERIFY timeout. Only the manager status query ran; no
remaining queries, monitor open, recording or system change. Actual leases and
recovery are not established by xpad binding. [Checkpoint and next gate](RF_LINK_CAPTURE_PLAN.md#approved-first-read-stopped-at-manager-fault).

Earlier preparation targets the primary KDE machine: user reports receiver plugged,
controller off. No fresh target read/capture/change occurred. A separately
approvable read-only preflight and a 90-second human-paced capture plan are
prepared; the lifecycle recorder profile itself still needs adaptation after
baseline/reference-path review. An xpad reference may isolate native-manager
effects, but changing ownership requires separate approval and its transport
identity must remain explicit. [Plan and concrete first read command](RF_LINK_CAPTURE_PLAN.md).

The separately requested passive offline prototype is now implemented as
`startup-replay`. It distinguishes receiver waiting, Hello/observed START,
tentative status and independent pad/IMU observations, preserving first errors
and terminal epochs. Thirty new tests and 23 private original-payload checks
against five saved timelines pass. No commands or runtime readiness are claimed.
[Model, repeatable checks and integration boundary](STARTUP_TIMELINE_PROTOTYPE.md).
No kernel/manager integration, target access or installed change. The user
reports controller off/dongle attached; the last inspected blocked state has
not been rechecked or recovered. No new hardware attempt or push.

Authorized online GIP research now explains the saved chronology: Microsoft
specifies Hello, host START, then status/input; periodic status is not a
pre-START gate. Two captured GameSir Hello reports match its full layout.
xone's connected-bit interpretation matches all 51 positive status frames but
still lacks a G7 radio-off contrast. A passive offline event/state prototype
is recommended next; not implemented or activated here.
[Sources, refined times and proof limits](DUALSENSE_STARTUP_GAMESCOPE.md#online-gip-sequence-cross-check--20-october-2026).
No private data uploaded, target access or installed change.

A subsequent offline search of ten saved USB originals finds four repeated
native-enumeration chronologies: status/announce → pad → IMU, with 514–606 ms
between pad and IMU. Init has already begun before the candidate in three.
Type 03 is periodic; type 02 is a concrete announce candidate, not a validated
RF-ready event. Existing radio-cycle logs also show USB replacement while the
receiver remains plugged. No synchronized raw off/on contrast is available in
this selected corpus. [Frames, timing, counterexamples and limits](DUALSENSE_STARTUP_GAMESCOPE.md#saved-capture-connection-chronology--20-october-2026).
No implementation or live access followed this finding.

Offline architecture review recommends retaining a thin scoped acquisition/
admin manager while introducing an explicit receiver/link waiting contract in
the kernel. The current three-second IMU failure is not solely Python policy;
removing the manager alone preserves it. PS4 dongle provides the closer
connection-state reference; no corresponding GameSir status field is proved.
[Source comparison, responsibility split and implementation gates](DUALSENSE_STARTUP_GAMESCOPE.md#manager-architecture-review-after-the-controller-off-reboot).
Existing 56 manager tests and shared-C ASan/UBSan startup cases pass unchanged.
No implementation, SSH or installed change followed this analysis.

20 October 2026. The maintainer rebooted with the receiver connected and the
radio controller off, then confirmed Gaming Mode ready without manual service
start or Resume. A fresh new-boot inspection confirms revision 14, matching
CachyOS kernel/module, service active/enabled with zero restarts, and native IF0
binding. The approved single protected status query then shows direct-`109c`
bootstrap failure: `state=8 error=-110 failed_stage=5 pad=0 imu=0`. The manager
is blocked with `Return deadline: still 109c; manual attention required` and
still observes `109c` owned by `gs_native`; recovery is not confirmed.
[Restart evidence and limits](RELEASE_AUDIT.md#revision-14-controller-off-restart-fails--20-october-2026).

Autoload works, but binding is not proof of healthy controller startup. The
late power-on step is stopped before asking the maintainer to turn on the
controller. No postboot Resume, release, manual service start, rebind or retry
was executed. The requested pre-push startup acceptance remains incomplete;
no push. Earlier Eden/Arc Raiders gyro and paddle successes remain valid for
their earlier session; the display-only TODO does not resolve this new boot
failure. Precision calibration remains paused.

## Earlier session: revision 14 application gyro works, Steam display TODO

20 October 2026. Fresh checks confirmed the installed package, stopped/enabled
service, matching CachyOS module/profile and absent receiver. One guarded
service start and one Resume completed while no receiver was connected.
The service is active/enabled and management unpaused. The maintainer reports
automatic controller power/connection on removal from its charging cradle.
Readback confirms successful direct-`109c` bootstrap, pad/IMU reception, exact
native lease/kernel identity and input publication, without a new manager fault.
[Activation evidence and limits](RELEASE_AUDIT.md#revision-14-activation-readback--20-october-2026).

The maintainer confirms normal Steam inputs and four independent paddles,
including simultaneous presses and release. All three Steam gyro UI values
remain zero during movement. Subsequent application checks are positive:
Eden recognizes gyro through SDL, and moving the controller steers the camera
in Arc Raiders during the announced Steam Input gyro-as-right-stick test.
This confirms useful application motion input in the tested session; the zero
UI values do not establish a general sensor/Steam Input failure.

The display discrepancy is a deferred, non-blocking TODO for this tested use.
Its exact internal cause is not proved. No separate Guide-independence,
neutral-drift, cold-boot or late-power-on/reconnect acceptance follows from the
camera report. Transient xpad probing and the new timeout recovery branch are
also not resolved by this run. No new system/driver/Steam change or push;
precision calibration remains paused.

## Historical: revision 14 installed, activation pending

20 October 2026. The explicitly approved transfer, physical removal, one manual
release and one guarded revision-13-to-14 package update passed. All 128 regular
payload files, package integrity and CachyOS DKMS/module identity pass; sensor
and Steam files and original error history are preserved.
[Installation and checks](RELEASE_AUDIT.md#revision-14-installed-on-cachyos--20-october-2026).
The service is stopped with its enabled setting retained, management paused,
no module loaded, no dongle/native binding and empty ownership. No activation,
Resume or startup test followed. Leave the dongle disconnected until the next
approved step. The manager correction still requires hardware acceptance;
first-IMU causation and precision calibration remain open/paused respectively.
No other-host update or push.

## Historical: revision 14 ready for review; installed revision 13 unchanged

20 October 2026. Source `54d70fc` and the fixed-hash PRE-ALPHA package are
prepared. Fresh target checks and the unprivileged matching CachyOS module
build pass with zero warnings. The package self-test and all 128 payload files
pass; 25 packaging tests and public docs/license checks pass. Installed native
runtime, service, sensor/Steam files and USB identity remain unchanged.
[Artifacts and update boundary](RELEASE_AUDIT.md#revision-14-prepared-for-cachyos--20-october-2026).
The next step requires approval for physical removal/release and a single
guarded update, then readback only. No installation or new startup test has
occurred. The manager correction does not establish an RF-ready indication.

## Current offline work: returned-instance suppression corrected

20 October 2026. Only a new unattempted `100a` observed on xpad after an
attested, successfully ended direct-`109c` no-data VERIFY timeout is released
for fresh discovery. The next full scan, ownership gates and existing budget
decide its start. Old failures/tokens persist; pause, unknown metadata and other
faults retain their guards. No historical-state migration or old-instance retry.
[Implementation, tests and limits](REVISION13_FIRST_START.md#offline-manager-correction--20-october-2026).
The [PS5/Gamescope reference](DUALSENSE_STARTUP_GAMESCOPE.md) supports separating
receiver presence from controller readiness; it supplies no GameSir RF flag.
Missing initial sensor data remains unexplained. Full offline tests and local
module build pass. Nothing installed or changed on either running system; no
SSH/hardware test, new package or push. Precision calibration stays paused.

## Last runtime observation: revision 13 active; first-start failure diagnosed

20 October 2026. The maintainer independently activated the installation and
reports xpad at first power-on, native GameSir after another radio cycle.
Fresh checks confirm the correct loaded module, active/enabled service,
unpaused management and an attested native `109c` runtime. Existing journals
show direct `109c` verification timing out without accepted IMU/pad reports.
The next `100a` is classified as observed xpad return and suppressed for startup;
another `109c` enumeration succeeds. The manager interaction is reproduced
offline, with the original diagnostic preserved. The RF/firmware reason for
missing initial data remains unknown. No driver/runtime change or new hardware
test; local documentation only, no push. See
[evidence, reproduction and boundaries](REVISION13_FIRST_START.md).

## Historical: revision 13 installed; activation pending at that checkpoint

After explicit authorization for removal/readback and a new update when green,
read-only checks confirmed dongle absence, paused management, returned=true,
empty entries/leases and no native bindings. The new guarded package update to
`0.1.0.alpha3-13` completed successfully. Target DKMS, expected module identity,
all 126 regular payload files and unchanged sensor/Steam settings are verified.
[Installation and checks](RELEASE_AUDIT.md#revision-13-installed-after-verified-physical-removal).

The service is stopped with its existing enabled setting retained; management
is persistently paused. No native module is loaded, the dongle remains absent,
and ownership is empty. Original errors remain recorded; no manual deletion.
No service start, Resume, reboot or physical startup/input test followed the
update. Keep the dongle disconnected until the next approved step. Both cold
startup cases and the effect of the new query remain unproven on hardware.
Local documentation commit only; no push or precision calibration.

## Historical first revision-13 update: stopped before replacement

The explicitly authorized package transfer passed hashes. Fresh guarded checks
and the exact single-package transaction preview passed, but the installed
pre-update hook refused release: the blocked old `100a` entry observes an
unowned `109c` on xpad. Empty leases alone do not satisfy its return check.
No package was upgraded. The old manager is active/enabled but now persistently
paused; revision-12 module remains loaded, without native bindings. Package
integrity, USB state, sensor/Steam files and original error history are unchanged.
One pre-transaction snapshot was created. No activation, Resume, reboot or retry.
[Abort and verified aftermath](RELEASE_AUDIT.md#revision-13-update-stopped-before-package-replacement).

The revision-13 artifact remains prepared and unchanged. Manual physical return
and a new update attempt need separately reviewed approval. Do not repeat the
consumed helper or treat xpad-bound `109c` as confirmed `100a` recovery.

## Historical revision-13 preparation

The pre-acquisition autoprobe correction is combined with the explicitly
requested, captured xpad control-IN startup query in the `100a` native bootstrap.
It runs once before the first mode-switch OUT, after ownership/settle checks,
without requiring a button report. A failed/short reply or changed identity
stops that bootstrap; `109c`/`105e` skip the query. No global xpad changes.
[Implementation, provenance, tests and limits](ACQUISITION_AUTOPROBE_FIX.md#revision-13-explicitly-requested-startup-query-integration).
Hardware necessity and cold-start success remain unproven.

Fresh target reads find matching CachyOS kernel/headers, intact revision 12,
active/enabled management, an old blocked pre-acquisition entry with no leases
or native bindings, and an unowned `109c` on xpad. Source/package preparation
and an unprivileged module build are authorized; installation and cold-start
acceptance are separate. Installed sensor/Steam settings remain untouched.
Revision 13 has now passed the full offline suite, local build/static checks,
and a warning-free target build; its verified Arch package and guarded update
are prepared. [Build and package audit](RELEASE_AUDIT.md#revision-13-buildpackage-preparation-completed).
Nothing has been installed or activated. Local commits only; precision
calibration remains paused.

## Historical revision-12 installation checkpoint; activation then pending

Source `057270a` passed the full offline suite and both Garuda/CachyOS module
builds. The explicitly authorized target update to `0.1.0.alpha3-12` completed;
DKMS, module identity, all 124 regular payload files and unchanged sensor/Steam
configuration were verified. Service is stopped, management paused, no native
module loaded; its existing enabled setting remains. The initial unowned
`109c` stays on xpad. No new runtime test or proof of working fallback follows
from this metadata. [Installation evidence](RELEASE_AUDIT.md#revision-12-cachyos-build-and-installation--19-october-2026).

Both power-on cases still need separately authorized activation and hardware
acceptance. No update to the other host, push or precision calibration.


# Projektstand

**19. Oktober 2026 — beide Startpfade offline korrigiert, Revision 12:** Nach
exakter Übernahme und gültigem passivem Status startet `100a` ohne vorherigen
Tastendruck. Ein bereits als `109c` vorhandenes freies/xpad-gebundenes IF0 wird
über ein neues instanzgebundenes Kernelattribut übernommen und auf derselben
Instanz mit der vorhandenen nativen Sequenz initialisiert. Keine neuen
USB-Pakete, keine Änderung an Paddles, Sensorprofil oder Haptik. Frische IMU,
Kernel-Tokens und die Sensor-Bereitschaftsprüfung bleiben erforderlich.
Unklare Rückgabe unter `109c` bleibt ein gemeldeter manueller Rückweg; keine
Wiederholung auf derselben Instanz und keine stillschweigende Fehlerlöschung.
[Implementierung und Abnahmegrenzen](STANDALONE_STARTUP.md#revision-12-start-without-a-button-report).
Historischer Implementierungsstand vor der oben dokumentierten Installation:
Offline-Entwicklung, Tests und lokaler Modulbau; damals noch nicht installiert;
keine neue Hardwareabnahme, insbesondere nicht für ausgeschalteten Controller
bei bereits vorhandenem Dongle. Kein Push; präzise Kalibrierung bleibt pausiert.

**19. Oktober 2026 — Kaltstart braucht noch Bedienung:** Der Nutzer bestätigt
für den folgenden Kaltstart: kein manueller Dienststart oder Resume, nur
Einschalten und Bedienung; Einschalten allein reichte nicht. Die bereits
erfassten Bootmeldungen bestätigen automatischen Dienst-/Modulstart, zunächst
`109c` an xpad und später eine neue `100a`-Instanz mit nativer Übernahme und
erfolgreichem Bootstrap. Der Code wartet vor diesem Bootstrap weiterhin auf
einen akzeptierten normalen Eingabebericht. Eine bereits beim Boot vorhandene,
nicht nachgewiesen verwaltete `109c`-Instanz wird weiterhin ausgeschlossen.
Native Bindung unter `100a` und vollständige Betriebsbereitschaft unter `109c`
sind getrennte Schritte. Die genaue Bedienung und der Auslöser der ersten
Neuanmeldung wurden nicht zeitlich aufgezeichnet. Damit bleiben der Start
allein durch Einschalten und der Kaltstart ohne vorherige xpad-Aktivität offen.
Nur lesende Befunde und Offline-Codeprüfung; keine Laufzeitänderung oder
Wiederholung. [Ablauf und Grenzen](STANDALONE_STARTUP.md#cold-boot-and-input-dependency--19-october-2026).

**19. Oktober 2026 — Revision 11 gestartet; Steam-Gyro nach Funk-Reconnect
positiv:** Der Nutzer hat Dienststart und Resume selbst ausgeführt. Die
anschließende lesende Kontrolle bestätigt das neue geladene Modul, aktiven und
aktivierten Dienst, erfolgreichen Bootstrap sowie gepaarte Gamepad-/Sensorknoten.
Der Nutzer bestätigt ausdrücklich: Funkcontroller aus/ein, Dongle blieb
eingesteckt, Steams Gyro-Anzeige im Gaming Mode funktioniert ohne gehaltene
Guide-Taste und ohne Steam-Neustart. Das ist eine begrenzte positive
Anwendungsabnahme dieses Funk-Reconnects. Ursache der Verbesserung und
allgemeine Hotplug-/Neustart-Zuverlässigkeit bleiben offen. Der Start ging
von einem zuvor xpad-initialisierten 100a-Gerät aus; kein Kaltstartnachweis
ohne xpad. Codex hat nur gelesen und keine weiteren Laufzeitaktionen ausgeführt.
[Nachweise und Grenzen](STEAM_GYRO_HOTPLUG.md#revision-11-user-led-radio-reconnect--19-october-2026).

**19. Oktober 2026 — Revision 11 auf CachyOS installiert, noch nicht
aktiviert:** Der separat freigegebene neue Einmallauf mit korrigiertem
Prüfhelfer ist erfolgreich. Der Paket-Hook bestätigte die Rückgabe, stoppte
den Dienst und entlud das alte Modul. Paketprüfung ohne Abweichung, 124
Nutzdateien stimmen mit dem geprüften Archiv überein; DKMS und Modulkennung
passen zum zuvor gebauten CachyOS-Stand. Abschließend `100a` an xpad, IF1
usbhid, keine native Bindung, leere Besitznachweise und gespeicherte Pause.
Der Dienst ist inaktiv; seine bisherige Autostart-Einstellung blieb erhalten.
Gyro-Konfiguration und Steam-Pakete sind unverändert. Kein Resume, Neustart
oder Eingabetest. Die Hardwareabnahme des eigenständigen Starts bleibt offen.
[Installationsnachweis](RELEASE_AUDIT.md#revision-11-cachyos-installation--19-october-2026).

**19. Oktober 2026 — Updateversuch vor Installation abgebrochen:** Das
freigegebene Revision-11-Paket wurde übertragen und seine Prüfsumme bestätigt.
Die frische geschützte Vorprüfung bestand. Der private Prüfhelfer erkannte
jedoch CachyOS' ausführliche pacman-Tabelle nicht und verneinte die
Installationsbestätigung. Keine Paket-Hooks, Rückgabe oder Moduländerung;
die Nachprüfung bestätigt weiterhin Revision 10, denselben aktiven/aktivierten
Dienst und dieselbe native Controllerinstanz. Die Tabellenprüfung ist offline
korrigiert; neun Tests bestanden, einschließlich simulierter Kindprozesse und
Ablehnung abweichender Pakete/Instanzen. Der nächste Lauf ist nur lokal
vorbereitet und benötigt eine neue ausdrückliche Einmalfreigabe. Kein neuer
Hardwaretest oder Push. [Details](RELEASE_AUDIT.md#revision-11-installation-preview-stopped--19-october-2026).

**19. Oktober 2026 — Revision 11 auch für CachyOS gebaut:** Der separat
freigegebene lesende Vorabcheck bestätigt `7.2.11-1-cachyos-deckify` und passende
`linux-cachyos-deckify-headers 7.2.11-1`. Die 17 ausgewählten Quelldateien aus
`5b14c85` wurden in einen neuen unprivilegierten Arbeitsordner übertragen und
mit GCC 16.2.1 gebaut: keine Warnungen, passende Vermagic und geprüfte Modul-
Prüfsumme. Header und Quelldateien blieben während des Baus unverändert.
Installierte Revision 10 und aktiver/aktivierter Dienst blieben unverändert;
kein Laden, keine Aktivierung, kein Hardwaretest. Damit sind beide Modulbauten
belegt, die getrennten Hardwareabnahmen des neuen Pfads stehen weiterhin aus.
[CachyOS-Baunachweis](RELEASE_AUDIT.md#revision-11-cachyos-module-build--19-october-2026).

**19. Oktober 2026 — eigenständige Übernahme offline vorbereitet:** Nach der
Freigabe wurde e2415a9 auf main veröffentlicht. Neue Entwicklung auf dem
isolierten lokalen Zweig codex/standalone-startup, Paketrevision 11: freie
100a-/105e-Interfaces direkt übernehmen; einen vorhandenen xpad-Besitzer nur
am exakt geprüften Kernelobjekt lösen. Kein Laden oder Binden von xpad als
Startvoraussetzung. Budget, Pause, separate Bereinigungsrechte und ursprüngliche
Fehler bleiben erhalten. Bestehende Runtime, Paddles, Sensorprofil und Haptik
bleiben unverändert. [Implementierung und Abnahmeplan](STANDALONE_STARTUP.md),
[abschließende Offline-Ergebnisse](RELEASE_AUDIT.md).
Keine Installation, Zugriffe auf die Testrechner oder neue Hardwareabnahme.
Insbesondere ist der Kaltstart ohne vorherige xpad-Aktivität noch nicht auf
Hardware belegt. Steam-Gyro bei spätem Einschalten bleibt offen; Eden bleibt
ein manueller Kompatibilitätshinweis. Kalibrierung pausiert, GUI später.
Kein neuer Push oder Release in diesem Auftrag.

**19. Oktober 2026 — abschließender GitHub-Check:** Der gesamte bislang
unveröffentlichte öffentliche Projektstand einschließlich des manuellen
Eden-Hinweises wird vor einer neuen Push-Freigabe geprüft. Die frische
Quellkopie besteht die vollständigen Offline-Tests, gerätefreie SDL-Prüfungen,
GUI-/Analysehelfer-Tests und den lokalen Modulbau. Die README stellt jetzt
klar, dass Revision 10 den späten Steam-Gyrofall trotz Installation/Test
nicht behoben hat. Private Originalhistorie, Firmware, Aufzeichnungen und
der zurückgezogene Eden-Starthelfer bleiben ausgeschlossen. Details und
Nachweisgrenzen stehen im [Abschlussaudit](RELEASE_AUDIT.md#final-unpublished-source-check--19-october-2026).
Kein Push, Tag oder Release ohne nächste ausdrückliche Freigabe; keine
Systemänderungen oder neuen Hardwaretests. Gyrokalibrierung bleibt pausiert.

**19. Oktober 2026 — Eden im Gaming Mode bestätigt; Workaround nur als
Dokumentation:** Der geerbte SDL-Ausschlussfilter versteckte den echten
GameSir vor Eden. Nach gesicherten, manuell geänderten Startoptionen öffnet
Eden das physische Gamepad und den gepaarten Sensor; Gyro ist ohne Guide
aktivierbar, alle vier Paddles und normale Eingaben funktionieren unabhängig.
Der Nutzer bestätigt den Anwendungstest ausdrücklich. Die genaue
[manuelle Lösung und der Rückbau](SDL_EDEN_GYRO.md#manual-steps-for-the-tested-launcher-shape)
ersetzen keine allgemeine Mehrcontroller- oder Hotplug-Abnahme.
Auf ausdrücklichen Wunsch keine Übernahme in Kernel, Installer oder Control
Center und keine automatische Steam-Verknüpfungsänderung. Ein begonnener,
uncommitteter Starthelfer wurde aus dem Veröffentlichungsbaum genommen;
keine Installation oder Änderung des laufenden Treibers. Die Veröffentlichung
des gesamten lokalen Stands ist bis zur nächsten Freigabe zurückgestellt;
dieser Nachtrag wird ausschließlich lokal committed. Kalibrierung bleibt pausiert.

Die folgenden Abschnitte beschreiben frühere beziehungsweise getrennte
Steam-Gyro-Untersuchungen; der Eden-Erfolg löst die Guide-Abhängigkeit in
Steams eigener Anzeige nicht.

**Gamescope-Prüfhelfer offline korrigiert:** Nach vollständigem Neustart meldet
der Nutzer automatische native Bindung ohne Resume, weiterhin Gyro nur bei
gehaltener Guide-Taste. Der danach freigegebene reine Metadatencheck bestätigt
Dienst aktiv/laufend/aktiviert, stoppt aber an der bisherigen Gamescope-Suche.
Moduloptionen und Steam-Sensorknoten wurden dabei noch nicht geprüft.
Der Helfer erkennt jetzt die ausführbare Datei, alle vier Benutzerkennungen
und die stabile Prozessinstanz statt eines exakten, veränderlichen Threadnamens.
Die lokale Gamescope-Datei verwendet `gamescope-wl`; ein entsprechender
Fehlalarm ist offline reproduziert. Der tatsächliche entfernte Name wurde
nicht gespeichert, die genaue Abbruchursache bleibt daher noch unbestätigt.
160 Steam-Integrationstests und 19 private Vorbereitungstests bestanden.
Neuer einmaliger Leseschritt vorbereitet, noch nicht gestartet oder freigegeben.
Keine Zugriffe auf den Ziel-PC, keine Änderungen an Steam oder Treiber.
[Befunde und nächster Schritt](STEAM_GUIDE_GYRO.md#gamescope-process-identity-corrected-offline).

Historischer Zwischenstand vor diesem Neustart und zweiten Metadatenversuch:

**Lesender SSH-Vorabcheck vor der Prüfung abgebrochen; Übergabe offline
korrigiert:** Die entfernte Fish-Shell verwarf den verschachtelten Python-Text
vor sudo/Passwortfenster und Prüfprogramm. Keine neue Laufzeitdiagnose; der
Nutzer meldet inzwischen auch mit Guide keine Reaktion und einen vorherigen
manuellen Resume. Das beweist weder einen automatischen Start noch fehlende
Gyro-Moduloptionen. Die korrigierte Übergabe besteht echte lokale Fish-/Bash-/
sh-Prüfungen einschließlich eigener Passwort-/stdin-Fixture. 133 Prüfungen in
`make test-steam` bestanden, dazu 15 private Vorabcheck-/Einmal-Regressionen.
Nächster reiner Metadatenlauf ist separat vorbereitet und noch nicht gestartet.
Kein neuer SSH-/Hardwarezugriff, keine Steam-/Treiberänderung oder Installation.
[Fehler, Korrektur und Nachweisgrenzen](STEAM_GUIDE_GYRO.md#metadata-precheck-stopped-before-authentication).

**Guide-Abhängigkeit gezielt offline eingegrenzt:** Der tatsächliche
Sensor-Ausgabeadapter und System-/Steam-32-Bit-SDL liefern frische Werte vor,
während und nach Guide-Haltephasen. Steam fordert Hintergrundereignisse
ausdrücklich an. Seine Gyro-Benachrichtigung benötigt jedoch einen vorhandenen,
gültigen Bewegungskontext/-quellzustand; der untersuchte Abruf erzeugt keine
fehlende Quelle. Separate Guide-Verarbeitung ist nachgewiesen, ihre Verbindung
zum blockierenden Gyrozustand dieses Realtests noch nicht. Eine durch Guide
veränderte Quellenauswahl/-verarbeitung bleibt die führende Hypothese, kein
bewiesener reiner Anzeigefehler. 24 SDL-Szenarien und erweiterter Adaptertest
bestanden; keine Zugriffe auf Zielsystem oder Hardware, keine Laufzeitänderung.
Kontinuierlicher Gyro ohne Guide und Reconnect weiter offen.
[Befunde, Nachweise und genaue Beweisgrenzen](STEAM_GUIDE_GYRO.md).

Stand: 19. Oktober 2026. Ältere Abschnitte/RST-Berichte belegen ihre jeweiligen
Prüfläufe, keine neue Freigabe oder aktuelle Systemkontrolle.

**Nachtrag: Gyro-Anzeige reagiert bei gehaltener Guide-Taste:** Der Nutzer
präzisiert den vorangehenden Null-Befund: Solange Guide gedrückt bleibt,
funktioniert die Gyro-Anzeige. Das ist eine gemeldete bedingte Reaktion,
kein belegter vollständiger Sensorausfall. Ein reiner Anzeigefehler bleibt
eine Hypothese; Ereignisverarbeitung, Benachrichtigung und Darstellung sind
noch nicht voneinander getrennt. Keine neuen Zahlen-/Ereignisaufzeichnungen,
keine quantifizierte Loslassfolge und kein zusätzlicher Agenten-Livetest.
Gyrobetrieb ohne gehaltene Guide-Taste ist weiterhin nicht abgenommen.
Laufender Treiber und Steam unverändert; frühere Beobachtung bleibt erhalten.
[Präzisierter Anwendungsbefund](evidence/INPUT_PUBLICATION_INSTALL_20261019.json).

**Revision-10-Steam-Gyrotest nach spätem Einschalten negativ:** Nach eigenem
Neustart des Nutzers laufen Gaming Mode und der automatisch gestartete Dienst
mit demselben neuen Modul. Ausgeschalteter Dongle zunächst 0575/usbhid, nach
separat freigegebenem Einschalten 100a/xpad. Genau ein anschließend freigegebenes
Resume bestätigt Bootstrap nach 109c, exakte Lease und zweistufige Gamepad-
Veröffentlichung. Manager aktiv/unpausiert, kein aktueller Fehler; keine neue
Kernelwarnung im beobachteten Fenster. Steam lief bereits vor dem Einschalten
und öffnet nach der Gyro-Anzeige beide lesbaren, sitzungsgleich gepaarten Knoten.
Der Nutzer meldet trotzdem alle drei Gyro-Werte null, normale Eingaben und vier
unabhängige Paddles funktionieren. Damit ist der gewünschte Steam-Gyrofall
**nicht bestanden**. Keine weitere Wiederverbindung oder Wiederholung; kein
manueller Fehler-Release und keine anschließende Laufzeitänderung. Die Ursache
hinter dem offenen Sensorknoten bleibt offen; FD offen beweist keine Datenlesung.
Der reine Beobachter wurde vorher offline um die drei neuen Bereitschaftsphasen
ergänzt (34 Tests); Deadline, Fehler-/Instanzprüfung und Attestation bleiben.
[Installations-, Übernahme- und negativer Anwendungsnachweis](evidence/INPUT_PUBLICATION_INSTALL_20261019.json).

**Revision 10 auf CachyOS installiert und pausiert gestartet:** Genau eine
freigegebene Pakettransaktion, DKMS für `7.2.11-1-cachyos-deckify`, 118
bytegeprüfte Nutzdateien und neue Modulkennung bestätigt. Sensor-Konfiguration,
Steam-/Gamescope-Erweiterungen und Fehlerhistorie erhalten; Snapshots 137/138
und Initramfs erfolgreich. Der anschließend separat angeforderte Dienststart
lädt das neue Modul einschließlich `defer_input=1`; Autostart bleibt aktiviert,
Manager aber pausiert und ohne Leases/native Bindung. Nach freigegebenem
Neustecken bleibt der neue Dongle unter 109c an xpad; aktive Sitzung ist KDE,
kein Gamescope-Prozess sichtbar. Deshalb kein Resume oder Sensortest. Das ist
noch keine Gamescope-Reconnect-Abnahme und keine bewiesene 100a-Rückkehr.
[Installations-/Startnachweis und offene Testvoraussetzungen](evidence/INPUT_PUBLICATION_INSTALL_20261019.json).

**Gyro-Bereitschaft jetzt offline an Kernel und Manager angebunden:** Revision 10
bereitet optionale zweistufige Input-Veröffentlichung vor. Der Manager wartet
nach nativer Attestation auf die verarbeitete Sensorbenachrichtigung und
Sitzungsleserechte; der Kernel veröffentlicht anschließend genau das vorbereitete
Gamepad derselben Instanz. Neue private Befehle, feste Deadline, Neustart-/Abbruch-
und Fehlerhistorie sowie gehaltene normale/Paddle-Eingaben sind offline getestet.
Kerneldefault bleibt ohne Deferral; die vorbereitete Dienstdatei fordert den
neuen Pfad für das bestehende opt-in Sechsachsenprofil an. Kein Steam-Neustart,
kein Eingriff in laufende Software, keine Installation oder Hardwareabnahme.
Modulbau für `7.2.11-1-garuda` und separat für `7.2.11-1-cachyos-deckify`
bestanden: gleiche Quellen, passende Header/Modulkennung; CachyOS GCC ohne
Warnungen, Garuda ohne Codewarnungen mit dokumentiertem Compiler-Versionshinweis.
Der CachyOS-Bau erfolgt unprivilegiert im gesonderten Arbeitsordner über SSH.
[Implementierung, Tests und nächste Freigabegrenze](STEAM_GYRO_HOTPLUG.md).

**Bazzite als mögliche Ablösung geprüft:** Quellen-/Dokumentationsvergleich
ergibt einen plausiblen Port mit gemeinsamem Treiberkern. Erforderlich sind
Fedora-akmod/kmod-/RPM-Paketierung und eine eigene Steam-/Gamescope-Einbindung;
aktuelle Bazzite-Quellen berücksichtigen OpenGamepadUI und InputPlumber. Kein
Bazzite-Zielsystem, Zielbau oder Hardwaretest geprüft. Empfehlung: Kernel und
Modul gemeinsam im abgeleiteten Image pflegen; RPM-Layering bleibt gesondert zu
validieren. Go zur Vorbereitung, keine zugesagte funktionsgleiche Migration.
Nur Dokumentation/lokale Referenzdateien, keine System- oder Treiberänderungen.
[Befunde, Quellen und Umstiegsgrenzen](STEAM_GAMESCOPE.md#bazzite-machbarkeitsprüfung-und-migrationsgrenze).

**Steam-Gyro jetzt auch in Gamescope positiv gemeldet:** Nach nutzergeführtem
Kernelupdate und Neustart läuft `7.2.11-1-cachyos-deckify` mit passenden Headern
und Modulkennung. Kernpaket Revision 9 und Sensorprofil unverändert; Dienst
aktiv/aktiviert. Steam öffnet jetzt in Gamescope Gamepad und Sensor, weiterhin
mit den üblichen Steam-Deck-Optionen. Nutzer bestätigt funktionierenden Gyro
und nennt den vor Steam eingeschalteten Controller. Kernel/Boot und Timing
änderten sich gemeinsam; die alleinige Ursache ist damit nicht bewiesen.
Neuere Nutzerrückmeldung zum Wiederverbindungscheck: Für Gyro muss der Controller
bereits beim Laden von SteamOS eingeschaltet sein. Uneingeschränkte Gyro-
Wiederverbindung ist damit nicht abgenommen; zuverlässige spätere Erkennung
bleibt zu lösen. Genauer Ablauf und interne Ursache nicht aufgezeichnet.
Nur der vorangehende Lauf wurde lesend nachgeprüft; zum neuen Bericht kein
Systemzugriff, keine Änderung oder zusätzliche Testbewegung durch den Agenten.
[Erfolgreicher Lauf und Grenzen](STEAM_ACCEL_EXTENSION.md#gamescope-success-after-user-led-kernel-update-and-reboot).

**Sitzungsunterschied auf demselben CachyOS-PC bestätigt:** Der Nutzer meldet
funktionierenden Steam-Gyro im KDE-Desktopmodus. Lesend geprüft: gleicher Boot,
Kernel, Paketstand, Modulquellstand, Manager-PID, Profil und gepaarte Geräte;
KDE-Steam öffnet zusätzlich den Sensor, Gamescope-Steam zuvor nur das Gamepad.
Die Startreihenfolge ist ein offener Unterschied: Gamescope-Steam-Launcher
startete bei etwa 18 Sekunden, der native Start war bei etwa 64 Sekunden fertig.
Der Vendor-Launcher verwendet außerdem Steam-Deck-Optionen. Weder deren Einfluss
noch ein Erkennungsrennen ist als Ursache bewiesen. Nächster gezielter Test unter
eigener Freigabe: einmaliger normaler Steam-Neustart in Gamescope bei bereits
vorhandenem Sensor. Kein Treiberpatch oder neuer Live-Versuch ausgeführt.
[Vergleich und Grenzen](STEAM_ACCEL_EXTENSION.md#same-host-kde-and-gamescope-comparison).

**Nach nutzergeführtem CachyOS-Neustart lesend bestätigt:** Dienst automatisch
beim Boot gestartet (etwa 16 Sekunden), aktiv/aktiviert, keine automatischen
Neustarts; neuer erfolgreicher Bootstrap und `109c/gs_native` beobachtet.
Persistiertes Sensorprofil unverändert, gepaarter Sechsachsen-Sensor vorhanden
und für den Nutzer lesbar. Steam öffnet im Hauptprozess weiterhin nur das
Gamepad, den Sensor nicht – auch im zweiten Schnappschuss bei bestätigter
geöffneter Gyro-Anzeige. Nutzer meldet weiterhin drei Nullwerte. Damit ist ein
Boot-/Startfall bestätigt, Steam-Gyro aber weiterhin nicht funktionsfähig.
Keine Systemänderung, Geräteöffnung, Speicherbeobachtung oder Reparatur.
[Nachweis und Grenzen](STEAM_ACCEL_EXTENSION.md#read-only-check-after-user-led-cachyos-reboot).

**CachyOS nativ mit sechs Sensorachsen aktiviert:** Ein separat freigegebener
Dienststart und ein Resume bestanden; kein Fehler-Release und keine Wiederholung.
Neue `109c/gs_native`-Instanz, Elternzuordnung, Besitznachweise/Kernel-Tokens und
Gamepad-/IMU-Start bestätigt. Leere USB-Metadaten während des Übergangs wurden
von der bestehenden begrenzten Beobachtung korrekt abgewartet. Gepaarter
Sechsachsen-Sensor und Gamepad sind für den aktiven Gamescope-Nutzer lesbar.
Dienst aktiv/aktiviert, Manager unpausiert. Zuvor gefundene unverwaltete
`109c/xpad` wurde nicht übernommen; nutzerfreigegebenes Neustecken lieferte den
frisch geprüften `100a/xpad`-Ausgangspunkt. Nutzer bestätigt normale Eingaben und
vier unabhängige Paddles; Steams drei Gyro-Werte bleiben jedoch null. Eine
lesende Hauptprozess-FD-Prüfung sieht das Gamepad geöffnet, den zugehörigen
Sensor nicht. Ursache damit nicht bewiesen. Regulärer nutzergeführter Neustart
als nächster Test vorgeschlagen, nicht per SSH ausgeführt. Keine erfolgreiche
Steam-Gyro-, Kalibrierungs-, Boot- oder Spieleabnahme behauptet.
[Aktivierung und Grenzen](STEAM_ACCEL_EXTENSION.md#cachyos-activation-and-session-access-verified).

**CachyOS auf Revision 9 aktualisiert, noch nicht aktiviert:** Der echte
GCC-Zielbau und anschließend das separat freigegebene Paketupdate von
alpha3-6 auf alpha3-9 sind bestanden. DKMS für `7.2.9-2-cachyos-deckify`,
alle 111 Nutzdateien, 143 Paketeinträge ohne Änderung und Modulkennung passen.
Sensor-Konfiguration bytegleich zum angenommenen Profil angelegt und geprüft.
Steam/Gamescope unverändert. Kontrollierte Rückgabe zu `100a/xpad` bestätigt;
Dienst inaktiv/weiter aktiviert, Modul entladen, Pause aktiv und Besitz leer.
Der erste Vorcheck stoppte vor jedem Paket-/Konfigurationsaufruf wegen des
inzwischen verbundenen Controllers; Originalnachweis bleibt erhalten. Der
neue Anlauf war separat freigegeben. Kein Dienststart/Resume, kein Sensor- oder
Spieletest nach dem Update. [Ergebnis und nächste Grenze](STEAM_ACCEL_EXTENSION.md#cachyos-revision-9-installation-passed-activation-pending).

**CachyOS-/Gamescope-Übernahme lesend geprüft:** Kernpaket noch Revision 6;
laufender Kernel `7.2.9-2-cachyos-deckify`, passende Header und DKMS/GCC-Werkzeuge
vorhanden. Dasselbe Revision-9-Quellpaket und experimentelle Sensorprofil sind
geeignete Kandidaten, ohne erkannten Sonderpatch. Manager/Dienst sowie die
installierte Steam-/Gamescope-Einbindung stimmen mit den aktuellen Quellen
überein; Steam-SDL-Prüfsummen entsprechen unseren geprüften Referenzen.
Zielbau und echte Sensor-/Zugriffsabnahme bleiben offen. Kein GameSir-Dongle
sichtbar; geschützter Besitzstand nicht abgefragt. Nur unprivilegiert gelesen,
keine Installation, Konfigurationsänderung, Aktivierung oder Hardwareprüfung.
[Übertragbarkeit und Grenzen](STEAM_ACCEL_EXTENSION.md#read-only-cachyosgamescope-transfer-assessment).

**Dauerhaftes lokales Sensorprofil gespeichert und lesend geprüft:** Die exakt
freigegebene Datei `/etc/modprobe.d/90-gamesir-native-gyro.conf` wurde einmal
aktualisiert: Gyro und Accel aktiviert, Accel-Achsen 1,2,3 und 8192/1 LSB/g.
Inhalt/Prüfsumme, root:root/0644 und effektive Moduloptionen stimmen. Dienst-PID
und -Zustand, Modulinstanz/-Quellversion und sämtliche laufenden Parameter
blieben gleich. Alte Datei und private Nachweise sind prüfsummenverifiziert.
Kein Neuladen, Dienstneustart, Resume, initramfs-Neubau oder PC-Neustart.
Paketstandard bleibt aus; reale Boot-/Lebenszyklusabnahme weiterhin offen.
[Ergebnis und Grenzen](STEAM_ACCEL_EXTENSION.md#eden-follow-up-and-approved-persistence-update).

**Vorheriger Vorbereitungsstand – Eden funktioniert weiterhin (Nutzerrückmeldung):** Der Nutzer bestätigt nach
dem Steam-Test die weitere Funktion von Eden mit dem laufenden Profil.
Keine zusätzlichen Einzelachsen-, Tasten-, Kalibrierungs- oder Langzeitwerte
wurden dazu erhoben. Die vorbereitete dauerhafte Option ergänzt nur die
bestehende lokale Gyro-Moduldatei um Accel/Achsen 1,2,3 und 8192/1; ein
gerätefreier modprobe-Ausgabevergleich besteht. Systemdatei noch unverändert,
keine neue Aktivierung oder neuer Test durch diese Dokumentation. Für das
Schreiben der Datei und einen späteren Neustart bleiben getrennte Freigaben
nötig. [Rückmeldung und Konfigurationsvorschlag](evidence/STEAM_ACCEL_ACTIVATION_20261019.json).

**Steam-Gyroanzeige mit realem Beschleunigungspfad erfolgreich:** Nach getrennten
Freigaben sind Release/Rückkehr, temporärer Profilwechsel und genau ein neuer
nativer Bootstrap bestätigt. `100a` → `109c/gs_native`, attestierte neue Instanz
und aktive Kernel-/Manager-Zuständigkeit; beide Sensorarten sind am gepaarten,
für den Nutzer lesbaren evdev-Knoten registriert. Nutzer bestätigt in Steam:
alle drei Gyro-Werte reagieren; normale Eingaben und vier unabhängige Paddles
funktionieren. Damit ist die Nullanzeige in diesem Lauf behoben.
Bei dieser Aktivierung war das Profil noch temporär: Accel 8192 LSB/g,
Achsen 1,2,3; Gyro unverändert 0,07 °/s/raw. Damals kein permanenter Accel-Eintrag,
kein Proton-Spiel-/Motortest und
keine erneute Eden-Abnahme mit sechs Achsen. Frühere Fehlprüfungen bleiben
historisch erhalten. [Aktivierung und Grenzen](evidence/STEAM_ACCEL_ACTIVATION_20261019.json).

**Nutzer hat Dienststart und Resume ausgeführt:** Lesend bestätigt sind der
aktive/aktivierte Dienst und das geladene Revision-9-Modul. Die Verwaltung
ist dadurch bereits freigegeben (`paused=false`), aber es gibt keine
verwaltete/native Bindung; der Dongle bleibt `109c/xpad`. Der Manager übernimmt
unbesessene `109c`-Instanzen bewusst nicht als neuen Bootstrap-Ausgangspunkt.
`experimental_gyro=Y`, neue Beschleunigungsausgabe `experimental_accel=N`.
Die zunächst erwartete Pause-Prüfung blieb als fehlgeschlagen erhalten;
der Nutzer bestätigte anschließend seinen zusätzlichen Resume-Aufruf.
Agent hat weder Dienststart noch Resume ausgeführt und keine Reparatur
angestoßen. Vor dem geplanten Test ist ein separat freigegebener Profilwechsel
mit sauberem Bootstrap-Ausgangspunkt erforderlich. [Aktueller Nachtrag](evidence/STEAM_ACCEL_INSTALL_20261019.json).

**Revision 9 installiert, noch nicht aktiviert:** Das gesondert freigegebene
Update von `gamesir-native-dkms` auf `0.1.0.alpha3-9` ist mit Exit 0 abgeschlossen.
DKMS für `7.2.11-1-garuda`, Modul-srcversion und Paketintegrität passen
(143 Einträge, keine Abweichung). Dienst gestoppt, Autostart unverändert
aktiviert, Verwaltung weiterhin pausiert, keine Besitznachweise/native
Bindungen und kein geladenes `gs_native`; bisherige Gyro-Konfiguration erhalten.
Die Abschlussprüfung stoppte an einer neuen USB-Instanz `109c/xpad` statt
`100a/xpad`. Nutzer meldet selbsttätiges Ausschalten durch Inaktivität;
Ursache dieser konkreten Neuanmeldung nicht bewiesen. Keine automatische
Reparatur, Wiederholung, Aktivierung oder Test. [Installationsbericht](evidence/STEAM_ACCEL_INSTALL_20261019.json).

**Updatevorbereitung auf Revision 9:** Vier vorhandene, prüfsummenverifizierte
Aufnahmen liefern unabhängig vom Gyro-Mapping den Beschleunigungskandidaten
`1,2,3`: A1 positiv bei Tastenfläche oben, A0 +/- bei linkem/rechtem Griff
unten, A2 +/- bei Vorderkante unten/oben. Niedrige Drehrate während der
gehaltenen Neigung ist ein qualitativer Nachweis für einen kontrollierten
Test, keine vollständige Lage-/Skalen-/Bias-Kalibrierung. Paketstandard bleibt
aus; Installation, Modulwechsel und Aktivierung sind hier nicht ausgeführt.
[Updateablauf, Zahlen und Grenzen](STEAM_ACCEL_EXTENSION.md#update-preparation-and-independent-axis-evidence).

**Korrektur offline vorbereitet:** Ein separater, standardmäßig deaktivierter
Beschleunigungspfad ergänzt den bestehenden evdev-Gyropfad aus demselben
IMU-Bericht und Zeitstempel. Keine erfundene Gravitation und keine zweite
USB-Zuständigkeit. Ungültige oder fehlende explizite Beschleunigungsachsen
verhindern das Aktivieren bereits vor USB-Registrierung. Eine vollständige
Beschleunigungskalibrierung fehlt; der spätere Testkandidat ist oben getrennt
dokumentiert. Synthetische Zuordnungen sind keine Hardwareempfehlung. Der installierte Treiber, Steam
und das angenommene Eden-Verhalten bleiben unverändert. Offline-Tests sind
keine Steam-Live-Abnahme. [Implementierung und nächste Grenze](STEAM_ACCEL_EXTENSION.md).
Gyrokalibrierung weiterhin pausiert; kein Push.

**Konkrete Steam-UI-Sperre offline identifiziert:** Die bisher unbekannte
Dreierprüfung vor den Gyro-Benachrichtigungen prüft tatsächlich Beschleunigung.
Schreibpfad, Cachebasis `0x180`, IMU-Abstand `0x34` und ein unabhängiger
`CGyroSource`-Leser bestätigen das für beide Seiten. Sind alle drei Werte der
gewählten Seite null, werden die Gyro-Statusmeldungen übersprungen – auch bei
vorhandener Drehbewegung, gültigem Quellzustand und Abonnement. Unser bewusst
Gyro-only ausgelegter evdev-Pfad kann deshalb die UI-Sperre nicht passieren,
wenn dessen frischer Cache keine Beschleunigung enthält. Das ist eine
hinreichende statische Erklärung für die Nullanzeige; die alleinige Ursache
des damaligen Live-Laufs und eine Spieleinschränkung sind damit nicht bewiesen.
Bereitschaftsmarker, Geräte-/Seitenzuordnung und Abonnementpfad sind ebenfalls
weiter verfolgt. 64 eigene Modellfälle und zwei Gegenseitenfälle bestehen;
keine Steam-Ausführung. [Fundstellen und Beweisgrenzen](STEAM_GYRO_DOWNSTREAM.md#notification-gate-follow-up).
Bei dieser vorherigen Analyse keine Steam-/Treiberänderung, kein Live-Test oder Push;
Gyrokalibrierung pausiert.

**Vorheriger Zwischenstand – Steam-Folgepfad eingegrenzt:** Der ELF32-Client routet Gyroereignisse
über die SDL-Instanz und führt separate Gyro-Paketfelder weiter, auch ohne
gleichzeitiges Accel-Ereignis. Die erste Zahlenkonvertierung erhält in einer
mathematischen Nachrechnung 192 von 194 gespeicherten Bewegungsvektoren als
ungleich null. Steams Anzeige liest einen eigenen Statusstrom nach Controller-
und IMU-Index; dessen Ausgangswerte sind null. Vor dessen Benachrichtigungen
liegen weitere Objekt-, Bereitschafts- und Abonnementprüfungen. Am Zwischenstand
`7203032` waren deren Laufzeitwerte und die vollständige Verbindung zur
Filterverarbeitung noch unbelegt; die obige Folgeanalyse ergänzt den statischen
Beschleunigungsblocker.
Statische Fundstellen, Gegenbelege zur einfachen Accel-/Quantisierungshypothese
und gezielte Restfragen sind [dokumentiert](STEAM_GYRO_DOWNSTREAM.md).
Nur lokale Dateien und vorhandene Daten untersucht; kein Live-Test, sudo,
Netzwerk, Steam-/Treiberwechsel oder Push. Gyrokalibrierung bleibt pausiert.

**Steam-Livebeobachtung erfolgreich: Gyro erreicht SDL, UI bleibt null.** Ein
gesondert freigegebener Lauf mit `ef64ee5` bestand Vorprüfung, lokales Go,
Terminalübergabe und Abschlussprüfung. 682 Stichproben über 70 Sekunden zeigen
aktiviertes Gyro derselben SDL-Instanz; alle drei Achsen ändern sich während
der Bewegung deutlich. Ein gleichzeitig aktualisierter Snapshot wurde erkannt
und ausgelassen. Der Prozessspeicherzugriff ist geschlossen; Exit 0 und
SHA256-Prüfungen sind bestätigt. Der Nutzer meldet weiterhin drei Nullwerte in
Steam und normale Eingaben/flüssigen Desktop. Damit ist die Lieferung bis in
Steams eigene SDL nachgewiesen; die weitere Ereignis-/Auswahl-/Filter-/UI-
Verarbeitung bleibt zu klären. Keine bewiesene Verwerfungsursache, keine
Kalibrierung oder Steam-Spielabnahme. Steam, Treiber, Dienste und Sensorpuffer
blieben unverändert. Kein weiterer Versuch oder Push.
[Befund und Grenzen](STEAM_GYRO_FEASIBILITY.md#read-only-live-cache-observation--19-october-2026).

**sudo-/Konsole-Eingabeweg offline korrigiert:** Auch der folgende freigegebene
Lauf bestand die Metadatenprüfung, stoppte aber an der vorgezogenen
Vordergrundprüfung. Eine neue Nachbildung mit zwei eigenen PTYs bildet den
dokumentierten sudo-Monitor ab: Erst ein echter Lesezugriff erlaubt dessen
Terminalübergabe; der bisherige Prüfer brach vorher ab. Ein zwischen Monitor
und Python laufender timeout-Prozess kann die Übergabe ebenfalls verhindern.
Der vorbereitete Aufruf startet Python nun direkt unter sudo und legt den
äußeren Watchdog davor. Eigene Prozessalarme begrenzen Vorprüfung, Gesamtlauf
und Go-Abfrage auf 30/210/120 Sekunden. Go+Enter und bestätigter Vordergrund
nach dem Lesen bleiben zwingend; erst danach werden alle Identitäten erneut
geprüft. 49 Beobachter-, 15 Terminal-/Monitor-, 40 Steam-/Gamescope- und zehn
Lizenz-/README-Prüfungen bestehen offline. Alle drei früheren Abbrüche bleiben
erhalten. Kein sudo, Live-Versuch, Steam-/Treiberzugriff oder Push bei dieser
Korrektur. Der später separat freigegebene Desktop-Lauf bestand; siehe oben.
[Befehle, Belege und Grenzen](STEAM_GYRO_OBSERVATION_PLAN.md).

**Steam-Beobachter: Go-Weitergabe offline korrigiert:** Die danach freigegebene
Identitäts-Vorprüfung einschließlich echter `map_files`-Metadaten bestand.
Der anschließende Helfer erkannte trotz sichtbarer GO-Eingabe im Terminal
keine Freigabe und stoppte vor dem Prozessspeicherzugriff. Eine eigene
PTY-/Bash-/timeout-/tee-Reproduktion zeigt: Der Standardaufruf von timeout
versetzt das Kind in eine andere Prozessgruppe und verhindert die Eingabe.
Die vorbereiteten Befehle nutzen jetzt `--foreground`; der Helfer prüft den
Terminal-Vordergrund und meldet Bereitschaft/angenommenes GO ausdrücklich.
45 Beobachter-, neun Terminal-, 40 Steam-/Gamescope- und zehn Lizenz-/README-
Prüfungen bestehen offline. Kein neuer Live-Versuch, kein sudo, keine
Installation, keine Steam-/Treiberänderung und kein Push bei dieser Korrektur.
Die anschließende sudo-/Desktop-Prüfung scheiterte; siehe die Korrektur darüber.
[Ablauf, Befehle und Grenzen](STEAM_GYRO_OBSERVATION_PLAN.md).

**Steam-Beobachter: Identitätsprüfung offline korrigiert:** Die freigegebene
Metadaten-Vorprüfung stoppte bei `Mapped/file identity differs`, nach gültigem
SDL-Hash, vor jedem Prozessspeicherzugriff. Kein Beobachtungslauf wurde gestartet.
Eine eigene künstliche Datei reproduziert auf Btrfs unterschiedliche
Gerätekennungen in `stat` und `maps`; der bisherige Direktvergleich war falsch.
Die konkrete abweichende Komponente der Steam-Prüfung wurde nicht protokolliert.
Der Helfer prüft jetzt die tatsächlichen Dateien aller SDL-Speicherbereiche
über reine `map_files`-Metadaten und vergleicht stat mit stat; kein Ausweichen
auf Hash/Pfad allein. Dateiaustausch, fehlende Rechte und veränderte Bereiche
stoppen weiterhin. 41 Beobachtertests sowie 40 Steam-/Gamescope- und zehn
Lizenz-/README-Prüfungen bestanden an diesem Prüfpunkt. Der erhöhte
Metadatenzugriff bestand danach separat freigegeben; der GO-Abbruch steht oben.
Keine Installation, Steam-/Treiberänderung, Hardwareprüfung oder Push.

**Gezielte Steam-Beobachtung weiterhin vorbereitet:** Ein auf die
vorhandene 32-Bit-SDL-Version begrenzter Helfer kann deren Gyro-Aktivierung und
zwischengespeicherte Drehraten im Steam-Prozess lesend beobachten. Kein
Debugger-Anhängen, kein Aufruf im Zielprozess, keine Geräteöffnung. Die
Feldadressen sind in der gerätefreien Sandbox gegen SDL-Getter geprüft;
die Guard-/Parserfälle bestehen. Vorgesehen sind frische Prüfungen,
ein lokales Go, 30 Sekunden Vorbereitung und insgesamt 70 Sekunden Beobachtung.
Das grenzt den Datenweg vor/hinter SDLs Cache ein, beweist aber keinen bestimmten
Verwerfungsgrund in Steam. Ausführung inklusive Prozessspeicherzugriff benötigt
eigene Freigabe. [Ablauf und Befehle](STEAM_GYRO_OBSERVATION_PLAN.md).

**Steam-Gyro offline weiter eingegrenzt (19. Oktober):** Die statisch
nachgewiesene Sensor-Einschaltfolge beider Steam-Client-ABIs aktiviert Gyro,
Accel, Gyro-L und Accel-L; Rückgabefehler werden dort nicht ausgewertet.
Der erweiterte gerätefreie Test zeigt: Fehler der drei fehlenden Kanäle
deaktivieren unseren Gyro in SDL nicht. Wiederholte Zeitstempel, 31-Bit-
Überlauf und Aus-/Einschalten bestehen ebenfalls. Dabei wurde ein Fehler
im künstlichen Ereignisrahmen korrigiert; der produktive Treiber bleibt
unverändert. Je sieben Fälle mit drei Steam-SDL-Bibliotheken sowie 14
System-Sensor- und 18 Buttontests bestehen. Der 32-Bit-Lauf ist nun ohne
private Anpassung reproduzierbar. Die Verarbeitung hinter SDL in Steam
und die Ursache seiner Nullanzeige bleiben offen. Keine neue Hardware-
oder Steam-Abnahme, keine Installation, kein Push.
[Befunde und nächster Freigabeschritt](STEAM_GYRO_FEASIBILITY.md#sensor-activation-and-timestamp-follow-up--19-october-2026).

**Aktueller Gyro-Meilenstein vom Nutzer abgeschlossen:** SDL-/Eden-Livetest
angenommen und dauerhafte lokale Konfiguration eingerichtet. Eine eigene
Steam-Gyro-Integration wurde zunächst mangels Bedarfs zurückgestellt;
die vorhandene Steam-Paddle-Unterstützung bleibt erhalten. Dies ist keine
Aussage, dass Windows-Spiele grundsätzlich kein Gyro unterstützen.
Der noch offene Neustartnachweis und weitere unten benannte Prüfgrenzen
bleiben offen; keine automatische Fortsetzung von Tests oder Kalibrierung.

**Anschließend angeforderte Steam-Gyro-Offline-Prüfung:** Beide lokal
mitgelieferten 64-Bit-SDL3-Bibliotheken von Steam bestehen je sieben
Sensorfälle, einschließlich unseres Gyro-ohne-Accel-Pfads, Ereigniszeitstempel
und 32 Kombinationen aus A und vier Paddles. System-SDL, Buttons, Bridge und
Steam-/Gamescope-Regressionen bleiben bestanden. Steams UI hängt Gyro an ein
Fähigkeitsbit; ob sein Backend dieses für den echten GameSir setzt und nutzt,
ist noch nicht nachgewiesen. Für Proton ist Gyro-zu-Maus/Stick der erste
sinnvolle Prüfpfad; kein universeller Rohgyro-Transport über XInput.
Der Nutzer fordert ausdrücklich eine gemeinsame kompatible Lösung: ein
USB-Eigentümer, derselbe evdev-Sensorpfad für SDL/Eden/Steam und gemeinsame
Input-/Output-/Lifecycle-Abnahme. Kein Steam-Start, keine Konfigurations-,
Treiber- oder Hardwareänderung; kein Netz und kein Push.
[Befunde, Grenzen und gemeinsame Abnahme](STEAM_GYRO_FEASIBILITY.md).

**Erster manueller Steam-Gyro-Check danach:** Die Gyro-Seite ist vorhanden,
zeigt laut Nutzer jedoch auch bei Bewegung null; der Kalibrierdialog bleibt
nach dem Countdown stehen. Abbrechen und Desktop funktionieren. Eden hat
nach dem Reconnect weiterhin Gyro, vom Nutzer erneut bestätigt. Lesend sind
gepaarte native Gamepad-/Sensorknoten nachgewiesen; Steam hat zeitweise beide
geöffnet. Seine tatsächlich geladene 32-Bit-SDL besteht ebenfalls alle sieben
gerätefreien Sensorfälle. Eine fehlende Beschleunigungsquelle für Steams
Kalibrierung/Filter ist eine Hypothese, keine bewiesene Ursache. Der konkrete
Steam-Verarbeitungspfad bleibt offen; keine Treiber-/Steam-Änderung, kein
Neustart und keine neue Hardwareaufzeichnung durch diese Diagnose.
Der abschließende DualSense-Vergleich trennt Sony-HID- und Linux-evdev-Pfad:
DualSense bietet sechs Achsen und Gerätezeit, wir bisher Gyro mit Hostzeit.
Steams vorhandene Behandlung unerwarteter SDL-Sensorzeitabstände ist eine
zweite Prüfspur neben fehlender Beschleunigung; keine Ursache ist bewiesen.
Keine Sony-Identität oder Kalibrierwerte übernehmen. Diese Untersuchung
endete am 18. Oktober auf Nutzerwunsch; die neu beauftragte Offline-
Fortsetzung vom 19. Oktober steht oben.

**SDL-/Eden-Erstabnahme erfolgreich:** Paket `0.1.0.alpha3-8` ist lokal
installiert und der neue Build unter gesonderter Freigabe mit
`experimental_gyro=1` geladen. Eden erkennt Bewegung über SDL; der Nutzer
bestätigt passende Richtung/Empfindlichkeit, vier unabhängig zuordenbare
Paddles und unveränderte normale Eingaben. Anschließend ausdrücklich
bestätigt: Die Live-Bewegungsanzeige im Eden-Controllermenü folgt der realen
Controllerbewegung wie erwartet; der Nutzer bewertet den Livetest positiv.
Abschlussprüfung: aktive native
109c-Sitzung, keine aktuellen Managerfehler, IIO-Puffer weiterhin aus.
Ein erster Start wurde durch einen fehlerhaften privaten Prüfhelfer
unterbrochen; Rückweg, Korrektur durch Wiederverwendung der vorhandenen
Übergangsprüfung und der separat freigegebene Erfolgslauf sind dokumentiert.
Danach wurde unter eigener Freigabe ausschließlich die dauerhafte lokale
Moduloption `experimental_gyro=1` eingerichtet. Dateiinhalt, Rechte und
effektiver Ladebefehl geprüft; Dienst, Modul, Geräteinstanz und Sensorpaar
blieben unverändert, beide IIO-Pufferschalter aus. Kein Neuladen oder Neustart.
Die tatsächliche Gyro-Abnahme nach einem PC-Neustart, ein konkreter Spiel-/
Hotplug-/Suspend-Langzeittest und der Push bleiben offen.
[Ergebnis und Grenzen](SDL_EDEN_GYRO.md#persistent-opt-in-installed-after-acceptance).

**Vorherige Offline-Vorbereitung:** Nach Annahme der bevorzugten
Gyroeinstellung wurde ein zusätzliches, ausdrücklich aktivierbares evdev-
Gyrogerät für `109c` ergänzt. 0,07 °/s und beobachtete Achsen bleiben erhalten;
SDL erhält rad/s, rohe IIO-Daten und Paddles bleiben unabhängig. Eden akzeptiert
im geprüften Quellstand auch Gyro ohne Beschleunigung; dessen Zeitbasisgrenze
bei spätem Hotplug ist dokumentiert. Alle vier Paddles sollen weiterhin eigenständig erkennbar und zuordenbar
bleiben; ihre gemeinsame Nutzung mit Gyro wurde offline geprüft. Zu diesem
Vorbereitungszeitpunkt noch kein neues Paket oder Hardware-/Eden-Test; die
spätere begrenzte Abnahme steht oben.
[Implementierung, Tests und nächster Freigabeschritt](SDL_EDEN_GYRO.md).

**Erster Live-Test des Gyrofensters bestanden (18. Oktober):** Nach eigener
Freigabe, frischer Instanz-/Buildprüfung und lokalem Go wurden 11.466
kohärente Sensorwerte im unbegrenzt angelegten Vorschaufenster verarbeitet.
Der Nutzer beendete den Lauf; Worker und GUI melden Erfolg, keine Fehler
und bestätigte Rückstellung. Ein zusätzlicher lesender Vergleich bestätigt
die ursprüngliche Instanz und alle Pufferwerte; Dienst und native Bindung
bleiben erhalten. Normale Tasten, Sticks, Trigger und flüssiger Rechner
wurden nach Stopp ebenfalls bestätigt. Kein neuer Treiber installiert.
**Bevorzugte Einstellung: 0,07 °/s pro Rohwert und 1,00× Fadenkreuz-Gain.**
Der Nutzer ließ beide unverändert und beschreibt natürliche, zur realen
Bewegung passende Reaktion, subjektiv sauberer als beim PS5-Controller.
Damit ist diese Kombination qualitativ im eigenen Fenster bestätigt;
kein exakter Winkel-/Driftnachweis und keine SDL-/Eden-Abnahme. Keine weitere
Faktorsuche angefordert; Winkelkalibrierung bleibt pausiert. Originale privat,
kein Rohmitschnitt. [Ergebnis und Prüfsummen](gyro-viewer-live-001.json),
[Bericht und Grenzen](GYRO_VIEWER.md#erster-live-test--18-oktober-2026).

**Vorherige Vorbereitung: Live-Anbindung offline umgesetzt:** Ein separater
`--live`-Modus verbindet das vorhandene Fenster mit dem bestehenden
IIO-Puffer-Worker. Vorbereitung und lokales Go bleiben ausdrücklich;
Fensteröffnung allein öffnet kein Gerät. Auf Nutzerwunsch kein festes
Laufzeitlimit: Vorschau bis Stopp/Fenster schließen oder Sicherheitsfehler,
mit konstantem Sample-Speicher und kleinem Abschlussbericht statt Rohmitschnitt.
Profilwechsel und Empfindlichkeit betreffen nur die Anzeige. STOP, EOF,
fehlende Daten, Suspend/Instanzwechsel und blockierte Kommunikation führen
zur Rückstellung; kein automatischer Reconnect. Ein Fehler bleibt als Fehler
sichtbar, auch wenn die Rückstellung gelingt. Offline-Regressionen und
40.486 gespeicherte Scans geprüft; bei diesem Vorbereitungsschritt keine Hardwareabnahme.
[Ablauf und konkrete Befehle zur gesonderten Freigabe](GYRO_VIEWER.md#live-test-zur-freigabe-vorbereitet).
Keine Installation, Treiberänderung oder Wiederaufnahme der Winkelkalibrierung.

**Vorheriger Stand: lokales Gyrofenster offline umgesetzt:** Das optionale PySide6-Werkzeug
zeigt Fadenkreuz, relative räumliche Drehung, benannte Drehraten und Rohwerte.
Pausierter Start, Zeitleiste, Wiedergabetempo, Zentrieren und ein separater
Fadenkreuz-Regler (0,25–4×) sind vorhanden. Auswahl des experimentellen
Sensorfaktors bleibt ausdrücklich erforderlich; `0,07 °/s` ist unbestätigt.
Alle sechs vorhandenen Aufnahmen mit 40.486 Scans wurden jeweils geprüft und
wiedergegeben, ohne ihre Dateien zu verändern. Die abgebrochene Aufnahme
wird abgelehnt. Quaternionen berücksichtigen kombinierte Drehungen; keine
Bias-Korrektur, keine Sensorfusion und keine neue Kalibrierung. Qt-Fenster
gerätefrei gerendert und geprüft; damals ohne Live-Transport, Treiberupdate
oder neuen Hardwaretest. Live-Erweiterung siehe oben. [Bedienung und Grenzen](GYRO_VIEWER.md).

**Beobachtete Gyroachsen als optionales Offline-Profil:**
`g7pro-observed-20261018` ergänzt die bestehende Diagnose, ohne Rohwerte oder
produktive Kalibrierung zu ändern. Die benannten positiven Bewegungen sind
Vorderkante hoch = G0, links drehen = G1, linker Griff ab = G2. Im bisherigen
rechtshändigen Gehäusekoordinatensystem ergibt sich `(G0, −G2, G1)`.
Explizite Auswahl erforderlich; `0,07 °/s` bleibt unbestätigter Testwert.
Alle 40.486 gespeicherten Scans der sechs Richtungen wurden einzeln offline
wiedergegeben: Kanal, Vorzeichen und unveränderte Rohdaten/Zeitstempel geprüft.
330 Python-Tests und der C-Sensorvertrag bestanden. Kein neues Live-Ergebnis,
keine Installation. Das darauf aufbauende Offline-Fenster ist inzwischen
implementiert (oben); der Live-Empfindlichkeitstest ist vorbereitet, noch nicht ausgeführt.
[Profil, Replay und E2E-Plan](EXPERIMENTAL_GYRO_TEST.md#beobachtetes-achsenprofil-v1-offline).

**Sechs Richtungen qualitativ beobachtet:** Nach frischer Vorprüfung und
separater Freigabe wurden links/rechts und Vorderkante ab aufgenommen. Der
Controller ging während der Vorbereitung des vierten Abschnitts von selbst
aus; der Helfer stoppte vor Pufferänderung/Geräteöffnung. Nach erneuter
Nutzerfreigabe, Einschalten und frischer Instanzprüfung wurden Vorderkante auf
und beide seitlichen Kipprichtungen einzeln nachgeholt. Insgesamt 40.486
kohärente Scans in sechs bestätigten 108-Sekunden-Aufnahmen, alle Puffer
zurückgestellt. Beobachtung: links/rechts → G1 +/−, Vorderkante ab/auf →
G0 −/+, linker/rechter Griff ab → G2 +/−. Zwei getrennte Geräteinstanzen;
keine als durchgehend erfolgreich ausgegebene Serie, keine Änderung der
Zuordnung im Treiber. Normale Eingaben und flüssiger Rechner bestätigt.
[Messwerte, Abbruch und Grenzen](GYRO_AXIS_TEST.md#hardwarebeobachtung-in-zwei-freigegebenen-blöcken).
Winkelkalibrierung, Skalierung und SDL-Freigabe bleiben offen.

**Vorbereitung des Sechs-Richtungs-Helfers:** Der bestehende KDE-Helfer bietet
jetzt `plan-axes` und `run-axes` für links/rechts drehen, Vorderkante ab/auf
neigen und linken/rechten Griff absenken. Ein Durchgang umfasst sechs getrennte
108-Sekunden-Aufnahmen, jeweils mit lokalem Go, 30 Sekunden Vorbereitung und
Rückstellungsprüfung. Rückbewegung erst nach der eigenen Ansage, außerhalb
des Auswertungsfensters. Fehler oder unbestätigte Bewegung stoppen die Serie.
Bei diesem damaligen Vorbereitungsschritt keine Hardwareausführung und keine
Änderung am installierten Treiber. Die spätere begrenzte Live-Prüfung steht
oben. [Ablauf und Freigabegrenzen](GYRO_AXIS_TEST.md#sechs-richtungen-in-einem-geführten-durchgang-offline-vorbereitet).
Die Zuordnungsheuristik liefert nur zu prüfende Gyro-Kandidaten; Beschleunigung
benötigt eigene Schwerkraft-Ruhelagen. Winkelkalibrierung bleibt pausiert.

**IIO-Kanalauswahl korrigiert und begrenzt hardwarebestätigt:** Der erste echte Pufferaufbau scheiterte
an der vollständigen Maske im pro Kanal aufgerufenen `validate_scan_mask`.
Ein neuer Regressionstest reproduziert den Fehler und den Rückweg. Die
Korrektur nutzt die vorhandene vollständige Produzentenmaske und prüft sie
beim Aktivieren; schrittweise Kanalauswahl ist möglich. Vollständige Rohscans,
Zeitstempel und übrige Controllerfunktionen bleiben erhalten. Neuer geprüfter
Quellstand `A15BC39B5A21D181E4E5C49`; PRE-ALPHA-Paketkandidat
`0.1.0.alpha3-7`, inzwischen separat freigegeben auf dem Garuda-Testsystem
installiert, per DKMS geprüft und aktiviert. Zwei vollständige 108-Sekunden-
Pufferläufe samt unabhängiger Rückstellungsprüfung bestanden. Der erste
bleibt wegen vorzeitiger Rückdrehung von der Achsenauswertung ausgeschlossen;
der ausdrücklich neu angeforderte Versuch wurde lokal bestätigt.
6.749 kohärente Scans mit Host-Zeitstempeln, ohne Sprung im akzeptierten
Berichtszähler, etwa 62,49 Hz. Erste qualitative Beobachtung: links reagiert
G1 vorwiegend positiv; keine vollständige Achsenzuordnung oder Skalierung.
Native Bindung, gesunder Dienst und normale Eingaben nach dem Test bestätigt.
[Installation, Messwerte und Grenzen](IIO_SCAN_SELECTION_FIX.md#installation-und-hardwareabnahme-am-18-oktober-2026).

**Qualitativer Achsentest:** Zunächst nur eine bequeme
waagerechte Linksdrehung pro eigenem Go, ohne Winkelvorgabe; höchstens drei
getrennte Wiederholungen. Der vorhandene KDE-/IIO-Helfer bietet dafür einen
separaten Modus mit Rohkanalvergleich ohne Winkelintegration oder Profilwahl.
[Ablauf, Befehle und Grenzen](GYRO_AXIS_TEST.md). Eine separat freigegebene
qualitative Bewegung ist inzwischen bestätigt; weitere Wiederholungen
benötigen jeweils einen neuen Auftrag und lokales Go. Die bekannte
Winkelkalibrierung bleibt pausiert.

Nachtrag: Die separat freigegebene lesende Vorprüfung war erfolgreich.
Der danach freigegebene erste Achsenlauf endete durch einen nachträglich
reproduzierten Dialogfehler vor der Geräteöffnung: KDialog unterstützt die
verwendete Option `--defaultno` nicht. Dies war keine bestätigte Nutzerabsage.
Null Sensorbeobachtungen, keine Pufferänderung; unveränderter Zustand und
private Prüfsummen bestätigt. Der korrigierte Dialog verwendet eine explizite
Auswahl mit Abbrechen als Vorgabe und bewahrt Startfehler. Ein gerätefreier
Fenstertest wurde als sichtbar bestätigt.

Der danach separat freigegebene neue Einzellauf erhielt ein ausdrückliches
lokales Go und hielt nach 30 Sekunden Vorbereitung bei der ersten
Scan-Kanalaktivierung mit `EINVAL` an. Keine Pufferaktivierung, kein
Aufnahmestart und keine Sensordaten. Die vorübergehend geänderte Pufferlänge
wurde zurückgestellt; ursprüngliche Instanz, Einstellungen und native Bindung
sind lesend bestätigt. Der damalige Verdacht einer nur vollständige Masken
akzeptierenden Treiberprüfung ist inzwischen offline bestätigt und korrigiert
(siehe oben). Im Hardwarelauf keine automatische Wiederholung oder
Treiberänderung. Noch kein
Achsennachweis. [Befund und Grenzen](GYRO_AXIS_TEST.md#neuer-einzellauf-kanalauswahl-vor-aufnahmebeginn-abgelehnt).

**Entscheidung vom 18. Oktober: Funkanalyse zurückgestellt.** Der Empfang
veränderlicher IMU-Rohdaten ist durch die bisherigen Hardwaretests belegt.
Die vollständige Rekonstruktion der unteren Funk-/Kryptoverarbeitung ist
keine Voraussetzung für die Bestimmung der effektiven USB-Gyroskalierung.
Vorhandene Befunde, private Prüfartefakte und offene Fragen bleiben erhalten.

**0,07 °/s pro USB-Rohwert ist ausschließlich ein unbestätigter Testkandidat.**
Er stammt aus der ST-/±2000-°/s-Arbeitshypothese und setzt eine unveränderte
Verstärkung bis zu den USB-Werten voraus. Aktiver Sensor/Messbereich und
dieser Gesamtfaktor sind damit nicht bewiesen. Herkunft und Grenzen stehen
im [Protokollbericht](PROTOCOL.md#unbestätigter-gyro-testkandidat).
Keine Profilwahl, Treiberänderung oder Freigabe kalibrierter SDL-Ausgabe.
Die Gyrokalibrierung bleibt pausiert; eine spätere bekannte Winkelreferenz
mit kohärenten Zeitstempeln, Bias- und Achsenprüfung benötigt neue Freigabe.

**Späterer Meilenstein aufgenommen: Linux-Firmware-Updater für Controller und
Dongle.** Die [Roadmap](ROADMAP.md#4-spätere-firmwareunterstützung-eigene-entscheidung-erforderlich)
hält Ziel, Userspace-Architektur, offene Protokoll-/Kompatibilitätsfragen,
Wiederherstellung und getrennte Abnahmekriterien fest. Noch kein implementierter
oder hardwarevalidierter Linux-Updater; keine neue Firmware- oder Hardwarefreigabe.
Laufender Treiber, pausierte Gyrokalibrierung und zurückgestellte Funkanalyse
bleiben unverändert.

**Zwölf Sensorbytes bis zum Berichtskonstruktor verfolgt:** Der ST-Pfad
ordnet die Registerachsen um und zieht bedingt sechs gespeicherte Offsets ab.
Die Folge `Gy,Gz,Gx,Ay,Az,Ax` passt über die vorbereitete Kopiergeometrie
exakt zu den bekannten Reportpositionen 17–27. In diesem ST-Ausgabeabschnitt
keine zusätzliche Gyro-Verstärkung; andere Sensor-/Ausgabezweige verwenden
`976/1000`, Negationen oder Halbierung. Diese Zweige bleiben getrennt.
Der [Transportfolgepass](JIELI_USB_TRANSPORT.md) ordnet den externen
Kopieraufruf unabhängig dem SDK-ROM-Stub `memcpy`/`memmove` zu und verfolgt
einen Controller-Zweig bis USB-IN `0x84`. Der neue
[Funkrahmen-Folgepass](JIELI_WIRELESS_DATAFLOW.md) verbindet beidseitig einen
`A2`-Kandidaten: Bericht → Queue `B+0x3dc` → Abschnitt mit zwei Kopfbytes →
DG-Queue `D+0x2e0` → Sendepuffer `D+0x8a4` → IN `0x82`. In diesen Kopien
keine zusätzliche Sensorrechnung. Der [Callback-Folgepass](JIELI_RADIO_CALLBACK.md)
ordnet nun in drei Apps die ausgewählte Transporttabelle, deren Setter und
den registrierten Daten-Callback zu. Die
[Routingfortsetzung](JIELI_LINK_ROUTING.md) klärt die Auswahlregel:
zwölf Bit Verbindungskennung, zuerst dynamische Liste, danach zwei feste
Slots. Die DG-Kette vom aufbereiteten Empfangsdeskriptor über Transporttabelle
und `btstack`-Nachricht bis zum A2-Parser ist zugeordnet. Welche dieser
Firmwarezweige bei den bereits empfangenen realen Paketen aktiv waren,
ist durch die statische Analyse nicht nachgewiesen.
Der [Empfangs-/Kontextfolgepass](JIELI_RX_CONTEXT.md) korrigiert nun unseren
privaten Exporthelfer und klärt die einfache Callback-Auswahl. `0xfe42`
verarbeitet variable Paketpuffer über einen Hardware-Registerblock; der
zweite Caller hängt vier Ergebnisbytes an. CCM-artige Transportbearbeitung
ist eine Hypothese, keine bestätigte Register-/Algorithmuszuordnung.
Der Formatcache `D+0xa24` und der alternative
IN-`0x84`-Pfad sind getrennt. Halfword- und Vorzeichenoperationen haben
weiterhin eine Decodergrenze. Kein
bestätigter USB-Gyrofaktor oder physischer Achsennachweis; keine Änderung
am Parser oder Treiber.
[Datenfluss, Codeanker und Grenzen](JIELI_SENSOR_REPORT_DATAFLOW.md).

Im aktuellen Empfangs-/Kontextfolgepass bestanden **81 Forschungstests**
(elf neu), **140 SDK-Einzelbefehls-Kontrollen** und fünf einfache
Bedingungsblöcke. Private Korrekturen: adressbezogene Kontextübernahme im
Exporter und E9D4-Stack-Abstände. Ein bedingter Parallelblock und zwei
Negativ-Konstantenformen bleiben ausdrücklich ausgeschlossen. Die acht
abschließenden DG-Fenster umfassen 294 Datensätze ohne Decodeabbruch;
kein vollständiger ISA-, Funk- oder Gyrofaktornachweis. Keine Installation,
Firmwareausführung, Netzwerk-/Hardwarezugriffe oder Treiberänderungen.

Im vorherigen Routingfolgepass bestanden **70 Forschungstests** (neun neu) und
30 abschließende Fenster mit 461 Decode-Datensätzen ohne Abbruch. Keine
weitere Sensorrechnung im untersuchten oberen DG-Transport-/Queuepfad.
Die bedingten Callback-Zuweisungen dürfen wegen fehlender Kontext-Wrapper
im damaligen statischen P-Code nicht als linearer Ablauf gelesen werden.
Die oben genannte Kontextkorrektur ersetzt diese historische Decodergrenze
für die gezielt geprüften einfachen Blöcke. Firmware und Treiber unverändert.

Im vorherigen Callback-Folgepass bestanden **61 Forschungstests** (zwölf neu) und
29 abschließende Fenster mit 389 Decode-Datensätzen ohne Abbruch. Kein
neuer Decoderpatch: weitere interne Gegenproben stützen die vorgeschlagenen
Halfword-/Signed-Modelle, liefern aber keine unabhängige ISA-Bestätigung.
Firmware und laufender Treiber unverändert, Gyrokalibrierung pausiert.

Im vorherigen Funkrahmen-Folgepass bestanden **49 Forschungstests** (zwölf neu),
127 SDK-Instruktionskontrollen und 19 abschließende Fenster mit 286
Decode-Datensätzen ohne Abbruch. Eine zusätzliche private Byte-Store-
Korrektur behebt die Verwechslung hoher Quellenregister. Die zwei offenen
Operationen wurden mit konkreten Gegenbeispielen eingegrenzt, nicht als
validiert freigegeben. Alle vier Original-App-Hashes stimmen weiterhin;
öffentlicher Commit ausschließlich Dokumentation, kein Push.

Im vorherigen Transportfolgepass bestanden **37 lokale Forschungstests** (zwölf neu).
Drei private Decoderkorrekturen und unsigned-extract wurden anhand von
83 SDK-Instruktionen geprüft. Abschließende Controller-Fenster: 324
Decode-Datensätze in drei Apps; getrennte DG-Fenster: 65 plus 15,
jeweils ohne Decodeabbrüche. Firmware und SDK bleiben privat; der damalige
öffentliche Commit enthält nur Dokumentation. Die damalige Funk-/Sensorlücke wird durch
den oben beschriebenen Folgepass eingegrenzt.

Im vorherigen Datenflusspass bestanden 25 Forschungstests und 15 vorhandene
Protokollparsertests. Zehn Codeblöcke sind in drei Apps eindeutig bytegleich; vier
Halfword-Loads, sechs Stores, 23 Byte-Loads und elf Adressadditionen wurden
gegen das gespeicherte Jieli-Listing geprüft. Der abschließende begrenzte
Sandboxlauf liefert 501 Decode-Datensätze ohne Fehler. Explorative
Decodeabbrüche sind privat dokumentiert und kein positiver Codebeleg.
Firmwaredateien unverändert; keine Ausführung, Netzwerk-/Hardwarezugriffe
oder Treiberänderungen. Gyrokalibrierung bleibt pausiert.

**Sensorinitialisierung offline eingegrenzt:** In den drei gehashten Apps
DV209, DV515 und DV608 führen zusammengesetzte Textadressen zu einem
ST-Sensorpfad: Registerargument `0x0f`, Vergleich mit `0x6a`, anschließend
Datenbyte `0x6c` für Registerargument `0x11` und `0x68` für `0x10`.
Die Argumentvorbereitung und Aufrufe sind statisch belegt; die vollständige
Busübertragung und aktive Auswahl im konkreten Controller bleiben offen.
Unter der LSM6DS3TR-C-Annahme ergibt sich ein Kandidat von ±2000 Grad/s
und 0,07 Grad/s je **Sensor**zählwert. Das ist noch kein bestätigter
Skalierungsfaktor der GameSir-USB-Daten. Der damals gefundene Zwölf-Byte-
Leseaufruf und die sechs zusammengesetzten Felder sind Ausgangspunkte
der oben dokumentierten Fortsetzung.
[Codeanker, Beweisgrenzen und nächster Schritt](JIELI_SENSOR_INITIALIZATION.md).

Im Initialisierungspass bestanden 15 lokale Forschungstests; die Teilformen
wurden zusätzlich gegen das gespeicherte offizielle Jieli-ROM-Listing geprüft. Der
Drei-Versionen-Sandboxlauf erzeugte 436 begrenzte Decode-Datensätze ohne
Decodefehler und mit unveränderten Dateien. Keine vollständige
ISA-/Kontrollflussvalidierung oder Hardwareabnahme. Frühere Formulierungen
über Stores „nach“ dem Kalibrierungs-/ADC-Log wurden korrigiert: Unbedingte
Sprünge erlauben keinen solchen Fallthrough-Schluss. Der EEPROM-Callback
bleibt unabhängig davon ungeklärt. Keine Netzwerk-/Hardwarezugriffe,
Firmwareausführung, Installation, Treiberänderung oder Kalibrierungsfreigabe.

**REA lokal wiederverwendbar eingerichtet:** Fünf begrenzte statische Wege
mit privater Kopie, Hashkontrolle und Netzwerk-/Geräteisolation. REA 6.5.0
hat keinen eigenen Jieli-Rohcode-Backend; der private Quarkslab-Pi32v2-
Beschreiber wurde nur in Teilformen validiert, einschließlich der anhand
des Jieli-Listings korrigierten E040-Vorzeichenerweiterung.
[Werkzeugstand und historische Befunde](GAMESIR_NEXUS_RESEARCH.md#lokales-rea-und-neuer-jieli-referenzkandidat-18-oktober).
Gyrokalibrierung bleibt pausiert; kein automatischer Profilwechsel.

**Normaler nativer Dauerbetrieb nach den HID-Aufnahmen wieder bestätigt:**
Der Maintainer führte Resume selbst aus. Die anschließende rein lesende
Kontrolle bestätigt den zugehörigen erfolgreichen Bootstrap nach `109c`,
IF0 `gs_native`, Manager `active` ohne aktuelle Fehler und `persistent_mode=Y`.
Dienst aktiv, Autostart aktiviert, kein Dienstneustart. `GameSir G7 Pro` und
normale Tasten-/Stick-/Triggereingaben vom Maintainer bestätigt. Die bekannte
xpad-Abbaumeldung `-2` trat vor dem danach erfolgreichen Bootstrap erneut auf.
Kein weiterer Resume, Release, direktes Geräteöffnen oder Reparaturbefehl durch die
Assistenz; keine neuen Motor-, Paddle-, Reconnect- oder Kalibrierungstests.
[Lesender Nachweis und Grenzen](HID_PASSIVE_CAPTURE_RESULTS.md#subsequent-return-to-normal-native-operation).

**Zwei freigegebene 90-Sekunden-Aufnahmen abgeschlossen:** Recorder,
Isolation und Prüfsummen bestanden. Der erste Lauf ohne bestätigten offenen
Eingabeclient hatte keine XInput-Berichte. Nach ausdrücklicher Wiederholungs-
freigabe wurden offene IF0-Eingaben lesend geprüft und der KDE-Test offen
gehalten: 10.787 erfolgreiche 20-Byte-XInput-Berichte und 20 erfolgreiche
13-Byte-HID-Berichte (`03`). Streamingauswertung, TShark und vorhandener Parser
stimmen überein. Keine 64-Byte-`10/3c/e0`-Telemetrie, kein Report `12`.
Normale Eingaben im KDE-Test vor/während/nach dem zweiten Lauf bestätigt;
volle Stick-/Triggerbereiche beobachtet, keine D-Pad-Aktivität belegt.

Originale bleiben privat, unverändert und dauerhaft gespeichert; keine
Rohmitschnitte oder HID-Tasteninhalte in Git. usbmon einmal geladen, danach
kein Resume, Treiberwechsel oder weiterer Modulladevorgang während der Aufnahmen.
Zum Aufnahmeende war der Manager pausiert und dieselbe
`100a`-/`xpad`-/`usbhid`-Instanz bestätigt. Kein Beleg für
Paddle-Zuordnung oder passive IMU-Nutzbarkeit unter XInput; Gyrokalibrierung
pausiert. Beide einmaligen Freigaben verbraucht, keine weitere Hardwareaktion.
[Ergebnisse, Grenzen und Prüfsummen](HID_PASSIVE_CAPTURE_RESULTS.md).

**Vorbereitungsstand vor den beiden Aufnahmen:**
**90-Sekunden-HID-Kurztest offline ergänzt, nicht gestartet:** Eigenes Profil
mit 30 Sekunden Vorbereitung, 10 Sekunden Ruhe, 10 Sekunden Reaktionspuffer,
30 Sekunden Mischtest und 10 Sekunden Schlussruhe einschließlich Abschlussreserve.
300-/450-Sekunden-Profile bleiben erhalten. Der Kurztest prüft nur das Auftreten
des Nebenkanals, keine einzelne Tastenzuordnung oder Gyrokalibrierung.

Der vorherige 300-Sekunden-Anlauf brach vor Modulladen/Aufnahme an der
Prozesszugriffsprüfung ab. Die heutige freigegebene lesende Root-Diagnose konnte
624 Prozesse und 5.167 Deskriptoren ohne Zugriffsfehler prüfen; der frühere Fehler
ist nicht reproduziert und sein konkreter Auslöser mangels alter Detaildaten
unbekannt. Künftig protokolliert der Helfer PID, Operation, FD und errno und
bricht weiterhin bei unvollständiger Prüfung ab. Keine Aufnahme, kein Resume
oder Eingriff in laufenden Treiber, Bindungen oder Systemrechte. Neue Aufnahme
braucht frische Vorprüfung, Manifest und Freigabe.
[Befund, Kurzablauf und Grenzen](HID_PASSIVE_CAPTURE.md).
100 gezielte Recorder-Tests und die vollständige Offline-Suite bestehen:
940 Python-Fälle in 33 Batches sowie bestehende C-/Sanitizer-/statische Prüfungen.

**Historischer Vorbereitungsstand vom 17. Oktober:**
**Passiver 100a-HID-Test offline vorbereitet, Hardware-Go gesperrt:** Der
Recorder hat jetzt ein eigenes 300-Sekunden-Profil mit separatem Einstieg,
30-Sekunden-Vorbereitungsfenster, Reaktionspuffern und geschützter PCAPNG-
Ausgabe. Es verlangt dieselbe frisch bestätigte `100a`-Instanz, IF0 `xpad`,
IF1 `usbhid`, pausierten Manager und leeren Besitzstand. Der alte 450-Sekunden-
Motorvergleich bleibt ein anderes Profil. Keine Aufnahme oder Änderung am
installierten Treiber; geänderte Hilfsquellen brauchen neue Freigabemanifeste.
46 neue und 34 bisherige Recorder-Tests bestehen; vollständige Offline-Suite:
920 Python-Fälle in 32 Batches plus bestehende C-/Sanitizer-/statische Prüfungen.

Die zugleich freigegebene lesende Managerdiagnose belegt einen echten
ungelösten Zustand der vorhandenen Instanz: Übergang nach `109c` und sechs
Initialisierungstransfers abgeschlossen, anschließend Timeout in VERIFY ohne
angenommenen IMU-Bericht. END wurde bestätigt; ein Wechsel zurück nach `100a`
blieb aus. Manager-Lease und aktuelle sysfs-/Boot-Identität stimmen überein;
die Sperre wird nicht automatisch gelöscht. Ursache der ausbleibenden
passenden Eingangsdaten noch unbekannt. Kein Release/Resume oder neuer Versuch.
[Diagnose, Adapter, Messablauf und Freigabegrenzen](HID_PASSIVE_CAPTURE.md).

**Gerätefreier xpad-/HID-Prototyp ergänzt:** Acht vorhandene Originalmitschnitte
wurden offline geprüft. In drei Rückkehr-Epochen nach `100a` liegen insgesamt
14 IF1-Berichte mit bekannter `10/3c/e0`-Form vor, darunter ein neuer kurzer
Elf-Paket-Burst. Kein belegter IF1-Aktivierungsbefehl: weder `0f f2` noch
passendes HID-`SET_REPORT`. Die drei beobachteten `03 01`-Ausgaben gehören zu
Tastatur-LEDs und folgen den Telemetriepaketen. Dauerstrom und physische
Paddle-Zuordnung in `100a` bleiben offen.

Der separate Dateiprototyp `hid-replay` erhält normale 16-Bit-XInput-Werte und
tentative HID-Rohfelder getrennt, sperrt veraltete/zeitlich widersprüchliche
Zusammenführung und schützt Quellen-/Anmeldegrenzen. Kleine echte Ausschnitte
mit Hash-/Frame-Herkunft und ausdrücklich künstliche Tests sind enthalten.
Keine Hardwareanbindung, Aktivierung, Kernel-/Systemänderung oder neuer
Gyrofaktor. Der laufende Treiber und bisherige IF0-Filter bleiben unverändert;
Kalibrierung pausiert. 75 Parser-Tests bestehen; vollständige Offline-Suite:
874 Python-Fälle in 31 Batches sowie bestehende C-/statische Prüfungen.
[Befunde, Prototyp und offene Aktivierung](XPAD_HID_PROTOTYPE.md).

**Vorheriger Prüfpunkt – Vereinfachung über xpad plus HID untersucht:** Der PandaPro8K-
Ansatz betrifft ein anderes Modell, hat aber einen konkreten Anknüpfungspunkt
in unseren normalen G7-Pro-Mitschnitten: `100a`-IF1 deklariert die 64-Byte-
Berichte `10`/`12` und Ausgabe `0f`; im damaligen Zwei-Capture-Umfang wurden
nach Rückkehr aus `109c` dort drei einzelne Berichte mit bekannter IMU-Signatur
aufgezeichnet. Kein beobachteter
`12`-Bericht, kein belegter dauerhafter Stream oder Viermotor-Ausgabepfad auf
IF1. Bisherige IF0-Filter beweisen keine Unbrauchbarkeit des Nebenkanals.
Eine kleinere Architektur ist deshalb ernsthaft zu prüfen; der laufende
Treiber bleibt unverändert. Kein neuer Gyrofaktor, Kalibrierung pausiert.
[Vergleich, Belege und nächster Offline-Schritt](XPAD_HID_FEASIBILITY.md).

**Nachfolgende native Aktivierung auf CachyOS lesend bestätigt:** Bei der
Kontrolle nach Rückmeldung des Benutzers liefen Dienst und Modul bereits;
dieser Prüfschritt führte weder Dienststart noch Resume aus. Der gespeicherte
Managerzustand meldete Pause aus, eine aktive Sitzung und erfolgreichen
Bootstrap. Die anschließend frisch gelesene `109c`-Instanz stimmte mit dieser
Sitzung überein und war an `gs_native` gebunden. Das registrierte Input-Gerät
heißt `GameSir G7 Pro` und enthält die vier Paddle-Codes 704–707. Dienst aktiv,
Autostart aktiviert, keine Dienstneustarts. Dies ist eine Zustandsbestätigung,
kein neuer Eingabe-, Motor-, Reconnect- oder Boot-Test. Gyrokalibrierung bleibt
pausiert. [Nachweis und Grenzen](MANAGER_RECONNECT_FIX.md#subsequent-native-activation--read-only-corroboration).

**Kernpaket auf dem CachyOS-/Gamescope-Testsystem angeglichen:** Nach gesonderter
Freigabe wurde ausschließlich `gamesir-native-dkms` von `0.1.0.alpha3-4` auf
`0.1.0.alpha3-6` aktualisiert. Der vorherige gerätefreie Modulbau und der
installierte DKMS-Build für `7.2.9-2-cachyos-deckify` bestanden ohne
Codewarnungen. Alle 97 regulären Paketdateien stimmen mit dem geprüften
Archiv überein; die Paketprüfung meldet 127 Einträge ohne Änderungen.
Die Modul-/DKMS-Version bleibt `0.1.0.alpha3`.

Der Update-Hook bestätigte die Rückgabe, stoppte den Dienst und entlud das
unbenutzte Modul. Abschließend: Dienst inaktiv, Autostart weiterhin aktiviert,
gespeicherte Pause aktiv und Besitzstand leer; die beobachtete
`100a/xpad`-/`usbhid`-Instanz blieb unverändert. Steam-/Gamescope-Pakete,
Dateien und laufende Steam-Unit blieben unverändert. Keine Trigger-Bridge
installiert, kein Resume oder Hardwaretest. Der ebenfalls enthaltene
kohärente IIO-Puffer wurde nicht aktiviert; Gyrokalibrierung pausiert.
[Installationsnachweis und Grenzen](MANAGER_RECONNECT_FIX.md#cachyosgamescope-core-update--installation-only).

**Steam-/Proton-Triggerpfad ausschließlich offline untersucht:** Der
Quellrelease `v0.1.0-pre-alpha.2` auf Commit `947790b` ist veröffentlicht;
der nachfolgende Untersuchungsstand bleibt lokal. Installiertes Proton
Experimental enthält einen passenden SDL2-Triggeraufruf. Bestehender
Nexus-Launcher, Container-/PID-Grenzen, Preloads und Steam-Input-Quellen
erfordern jedoch einen eigenen Adapter; Liveausführung bleibt gesperrt.
82 bestehende Bridge-Tests bestanden ausschließlich gegen künstliche
Bibliotheken/Metadaten/Broker. Steam, Proton, Wine und Hardware wurden dabei
nicht gestartet oder angesprochen. Kein geeignetes Steam-Spiel steht zur
Trigger-Abnahme bereit; technische API-/Runtime-Proben sind künftig auch
ohne Spiel möglich, benötigen aber eine getrennte Freigabe und ersetzen
keinen Spielenachweis. [Befunde und nächster Entwicklungsschritt](STEAM_PROTON_TRIGGER_BRIDGE.md).

**Korrigierter integrierter Forza-/Xodus-Test bestanden, begrenzter Umfang:**
Das separat freigegebene Bridge-Update `0.1.0.alpha1-2` ist installiert und
geprüft: 14 Paketdateien stimmen, 97 Dateien des Kernpakets unverändert.
Dienst und native Geräteinstanz blieben während Update und Spiel unverändert,
ohne Dienstneustart. Beide Trigger waren spürbar, stoppten zwischen Effekten
und starteten bei neuen Effekten erneut. Normale Eingaben und Griff-Rumble
blieben ohne Aussetzer; nach regulärem Spielende waren beide Trigger ruhig.

Die passive Beobachtung sicherte 2.337 Producer-Frames, 171 angenommene
Play- und 498 Stoppaufträge. 66 Play-Aufträge enthielten LT, 100 RT;
gleichzeitig von null verschiedene LT/RT wurden in diesem Lauf nicht
aufgezeichnet. 672 Logeinträge, keine verworfenen Einträge und kein
Relayfehler; reguläres Producer-EOF, Aufräumen ohne gemeldeten Fehler.
Brokerannahme ist keine USB- oder mechanische Zeitmessung; die fühlbare
Wirkung bestätigt der Benutzer. Nur der installierte Hook wurde beobachtet,
Spiel/Bridge liefen unprivilegiert. [Auswertung](TRIGGER_BRIDGE.md#corrected-integrated-forza-test--limited-acceptance-passed).

Die vom Maintainer an diesen erfolgreichen Spieltest gebundene Vorbereitung
von Push und neuem PRE-ALPHA-Release ist nun möglich, nach abschließendem
Quell-/Historien-/Artefaktaudit. Kein zusätzlicher Hardwarelauf oder
Systemeingriff folgt daraus. Steam-/Proton-Bridge, Reconnect, Suspend,
Prozessabbruch und Mehrgerätebetrieb bleiben unbestätigt. Gyrokalibrierung pausiert.

**Vorheriger Prüfpunkt: Erster integrierter Forza-Test fehlgeschlagen.** Normale
Eingaben und Griff-Rumble funktionierten laut Benutzer, Trigger-Vibration war
nicht spürbar. Die installierte Bridge wurde in Wine und Spiel nachgewiesen;
ihr Relay verschwand vor dem ersten protokollierten Motorauftrag. Kein Fehler
war in Nexus sichtbar. Der tatsächliche Live-Exitgrund ist nicht abschließend
belegt, weil der alte Logger keine Lifecycle-/Fehlerereignisse erfasste.

Ein konkreter Fehler ist unabhängig offline reproduziert: Eine normale kurze
Statusabfrage des Managers setzt `busy`; die Bridge verwechselte das mit
Identitätsverlust. Die gezielte Korrektur trennt Identität/Verfügbarkeit und
ergänzt begrenzte Diagnoseereignisse. Die vollständige Offline-Suite besteht:
843 Python-Testfälle in 31 Batches plus bestehende C-/statische Prüfungen,
darunter 18 zusätzliche Regressionen. Optionales Update `0.1.0.alpha1-2` wurde
aus Commit `e264c1f` gebaut; zu diesem Prüfpunkt war Bridge `0.1.0.alpha1-1` installiert, Kerneltreiber
und Broker unverändert. Kein automatischer neuer Hardwarelauf, Push oder
Release. Gyrokalibrierung bleibt pausiert.
[Befund und Korrektur](TRIGGER_BRIDGE.md#first-integrated-forza-test--trigger-acceptance-failed).

**Vorheriger Prüfpunkt: Integrierte Trigger-Bridge lokal installiert:** Das
separat freigegebene Zusatzpaket `gamesir-native-trigger-bridge 0.1.0.alpha1-1`
ist installiert; alle 14 regulären Paketdateien stimmen mit dem geprüften
Archiv überein. Der native Dienst läuft nach dem vom Benutzer ausgeführten
Start mit erfolgreichem Bootstrap unter `109c`, Name `GameSir G7 Pro`;
keine Dienstneustarts während der Bridge-Installation. Nur Forzas vorhandener
Xodus-Startzusatz wurde bei geschlossenen Anwendungen ersetzt und gesichert.
Der Benutzer hat die einmalige Mitgliedschaft in der Haptikgruppe gesetzt.
Nach regulärem PC-Neustart sind die effektiven Gruppenrechte auch im normal
gestarteten Nexus vorhanden; unprivilegiertes Broker-Listing und eindeutige
native Gerätezuordnung bestanden. Ein bloßer Desktop-Neulogin hatte den
weiterlaufenden Benutzer-Manager hier nicht mit neuen Gruppen versehen.
Keine Socketrechte aufgeweitet; integrierte Spielabnahme weiter offen.
Gyrokalibrierung pausiert, kein Push oder Release.
[Installation und nächste Testgrenze](TRIGGER_BRIDGE.md#local-installation-and-prepared-xodus-test).

**Vorheriger Prüfpunkt: Reconnect-Korrektur als PRE-ALPHA-Update lokal installiert:** Der belegte Fehler
`Device changed during native status access` konnte eine neue 100a/xpad-
Instanz dauerhaft als `released`/bereits versucht blockieren. Gesunde veraltete
Getter werden jetzt getrennt von echten Runtime-/Bootstrapfehlern behandelt.
Eine neue Instanz wird erst nach frischer Enumeration/Guard/Budgetprüfung
übernommen, kein END oder Restore am unbekannten Ersatzgerät. Temporäre
Metadatenfehler behalten abgeschlossene Leseergebnisse; globale Fehler stoppen
weitere Geräteaktionen im aktuellen Durchlauf. Echte Fehler bleiben erhalten.

34 neue gerätefreie Regressionen ergänzen die bestehenden 139 Managerfälle.
Vollständiges `make test` bestanden: 825 Python-Testfälle in 30 Teilprüfungen
plus bestehende C-/statische Prüfungen. Offline-Modulbau für `7.2.11-1-garuda`
bestanden, keine Codewarnungen, bekannter Clang-Umgebungshinweis 23.1.1→23.1.3.
Installiert: `gamesir-native-dkms 0.1.0.alpha3-6`, sichtbarer Installationsdateiname
mit PRE-ALPHA, interne Modul-/DKMS-Version bleibt `0.1.0.alpha3`. Keine Änderung
an Kernel/ABI/Broker/Trigger-Bridge/Paddles/IMU. Nach ausdrücklich freigegebener
Installation stimmen alle 97 regulären Paketdateien mit dem geprüften Archiv
überein; DKMS ist für den aktuellen Kernel installiert. Dienst inaktiv,
gespeicherte Pause aktiv, Besitzstand leer, Modul nicht geladen. Der bisherige
Autostart bleibt aktiviert; die Verwaltungspause bleibt auch darüber erhalten.
Keine Aktivierung, kein Resume oder Forza-Test; Gyrokalibrierung pausiert, kein
Push. Das Drei-Starts-Budget in zehn Minuten bleibt bestehen. Kontrollierter
Start/Resume und reale Reconnect-Abnahme benötigen eine separate Freigabe;
keine automatische Migration per Fehlermeldung.
[Befund und Installationsprüfung](MANAGER_RECONNECT_FIX.md).

**Vorheriger Bridge-Zwischenstand 0a4012b, offline integriert:** Ausgangsbasis ist die getrennte
projektinterne Forza-/Xodus-Bridge bis `3a78390`, deren LT-/RT-Spieleffekte
fühlbar bestätigt wurden. Herkunft/Lizenz wurden vor selektiver Übernahme
geprüft; GPL-2.0-only gemäß Projektentscheidung, keine private Historie oder
Rohlogs übernommen. Die Prüfung ist begrenzt, keine vollständige Rechtegarantie.

Der neue Userspace-Pfad bindet SDL-Quelle, aktuelle evdev-/USB-Metadaten und
Brokerinstanz an eine zufällige Sitzung. Kein fester Port und keine Auswahl
des ersten Geräts. Versionierter Transport mit Ursprungszeit/Sequenz, erhaltenen
Null-/Stoppbarrieren und begrenzten Warteschlangen; bei Instanzwechsel/Fehler
endet die Lease. Bestehender Kernel/Broker unverändert, Griffe `null`, STOP
Maske 3. Forza-RT3x ist ein explizites Profil; andere Profile bleiben 1x.

Optionaler Paketquell-/Staginghelfer ohne Installation, Hooks oder Gruppen-
änderungen vorbereitet. Bereits berechtigte Benutzer benötigen keine erneute
Passwortabfrage. Xodus-SDL2 ist für eine spätere gesonderte Abnahme vorbereitet;
Steam/Proton bewusst nur Planmodus. Automatische Launcher-Konfiguration,
Reconnect/PM und Mehrcontrollerbetrieb sind noch keine bestätigten Features.
Gyrokalibrierung bleibt pausiert. [Implementierung und Grenzen](TRIGGER_BRIDGE.md),
[Herkunftsprüfung](TRIGGER_BRIDGE_PROVENANCE.md).

Validierung: vollständiges `make test` bestanden (791 Python-unittest-Fälle
in 29 Batches plus bestehende C-/statische Prüfungen), darunter 64 neue Bridge-
Fälle. Neuer C→Unix→Python→Broker-Durchstich verwendet ausschließlich künstliche
Motoren. Paketquellen und unprivilegiertes Staging geprüft, nichts installiert.
Öffentliche Identität für den lokalen Commit; kein Push oder neuer Release.

Die folgenden Release-Vorbereitungsabschnitte beschreiben den historischen
privaten Ausgangsstand. Der bereinigte öffentliche Quellstand wurde inzwischen
als `v0.1.0-pre-alpha.1` veröffentlicht; die neue Bridge ist noch nicht gepusht.

**Letzter öffentlicher Release-Check:** Bis `3e620f3` alle 93 erreichbaren
Commits/1.037 Blobs und 237 aktuelle Dateien geprüft. Keine erkannten echten
Credentials, Hersteller-Binaries oder Rohcaptures, aber persönliche Commit-
E-Mail, Rechnerbezeichnungen und historische Home-Pfade. Unveränderte Historie
und Baum deshalb **nicht veröffentlichen**. Originale bleiben lokal erhalten;
getrennten bereinigten PRE-ALPHA-Quellsnapshot und daraus alle drei Komponenten-
Quellartefakte vorbereiten. Keine System-/Hardwareänderung und kein Push.
Verfahren und Grenzen: [PUBLIC_RELEASE_CHECK.md](PUBLIC_RELEASE_CHECK.md).

**Öffentliche PRE-ALPHA-Dokumentation vorbereitet:** Die README ist jetzt ein
englischer Einstieg mit vollständigem vorgegebenem Warntext, langfristigen
Projektzielen und sichtbarer, ausdrücklich unabhängiger Referenzwürdigung von
Deadband/g7ctl. Aktuelle begrenzte Hardwarebelege und offene Funktionsketten
sind getrennt; die widersprüchlichen älteren README-Zustände bleiben in Git-
Historie und ihren vorhandenen Belegberichten erhalten. Keine alten Tests als
neue Abnahme behaupten. Allgemeine, portable Nutzeranleitung:
[Installation und Entfernung](INSTALLATION.md); [Release-Audits und offene
Publikationsschritte](RELEASE_AUDIT.md). Alle Änderungen sind lokal; keine
Hardware-/Systemaktion oder Veröffentlichung. Gyrokalibrierung bleibt pausiert.

**Pre-Alpha-Lizenzentscheidung umgesetzt:** Eigener Projektbestand ausdrücklich
GPL-2.0-only, vollständiger Text in `COPYING`, vereinheitlichte Quellkopf-
Kennzeichnungen und erhaltene Linux-syscall-Ausnahme für den UAPI-Header.
Vorherige lokale Herkunftsprüfung fand keine übernommenen Apache-/GPLv3-
Codeblöcke; g7ctl bleibt entsprechend begrenzte Protokollreferenz. DKMS-
Quell-/Paketgenerator liefert die Lizenztexte mit. Keine installierten
Pakete oder laufenden Treiber geändert, keine Veröffentlichung. Herkunft,
Prüfgrenzen und Mainline-Perspektive: [Lizenzbericht](LICENSING.md).

**Gyrokalibrierung auf Eis; Offline-Zwischenstand gesichert.** [tester] fehlt
eine geeignete externe 90°-Winkelreferenz. Die vorbereiteten Helfer werden
lokal geprüft und committet, danach keine Fortsetzung ohne neuen Auftrag.
KDE-Frontend, begrenzter IIO-Worker und transaktionaler Pufferaufbau gehören
zusammen: eine Linksdrehung pro Aufruf und Go, 30 s Vorbereitung, Ruhe- und
Reaktionspuffer, 108 s Aufnahme, Rückstellung vor Rückdrehung. Ein physischer
Winkelbeleg wird zusätzlich bestätigt; alle fünf Faktoren bleiben Hypothesen.
Nur künstliche Dateien/Prozesse/Zeit getestet. Noch kein Live-Pufferlauf,
keine GUI-Abnahme, kein empirischer Gyrofaktor oder SDL-Freigabe. Keine neue
Treiber-/Systemänderung oder Netzwerkaktion im Abschluss; Kernel und Manager
unverändert. [Vorbereitung und Grenzen](COHERENT_IMU_CALIBRATION.md).

**Neuester Zustand: nativer Betrieb mit Revision5 bereits aktiv.** [tester]
meldete den Controller vor dem geplanten Resume bereits verbunden/gebunden.
Frische öffentliche und freigegebene geschützte Lesekontrollen um 18:49 MESZ
bestätigen 100a/16→109c/17, gs_native an IF0, aktiven unpausierten Manager und
exakt passende persistierte Lease/Inode99051/Kernel-Tokens [1,2]. Erfolgreiche
Bootstrapdiagnose mit READY/Fehler0/pad1/imu1; Dienst PID51607/NRestarts0 und
dieselbe USB-/IIO-Instanz während der Kontrollen erhalten. Kein zusätzlicher
Resume oder anderer Geräteeingriff durch Codex.

Das neue IIO-Gerät bietet acht erwartete Scanindizes/-typen, monotonic und
235:0; Länge128/Watermark1 unverändert, alle Kanäle sowie Puffer/Gate aus,
Pushfehler0. Diese Registrierung ist kein Nachweis eines gelesenen kohärenten
32-Byte-Scans. Keine Rohdaten/Control-FDs geöffnet, keine Pufferwerte geändert,
kein Drehtest oder neue physikalische Kalibrierung. Aktiven Betrieb erhalten;
gesonderte Puffer-/Messfreigabe bleibt erforderlich.
[Aktualisierte Lesebestätigung](COHERENT_IMU_UPDATE.md),
[Prüfmetadaten](evidence/COHERENT_IMU_INSTALL_20261016.json).

**Vorangegangener Garuda test host-Systemstand: Revision5 installiert, Dienst pausiert gestartet.**
Ein freigegebener Release brachte das Ziel real auf100a/Adresse14/xpadIF0/
usbhidIF1 zurück; paused=true/Leasesleer/returned=true geprüft. Die danach
ausdrücklich freigegebene Pakettransaktion änderte ausschließlich
gamesir-native-dkms0.1.0.alpha3-3→-5. Qkk102Einträge/0 verändert und81
bytegenau geprüfte Nutzdateien. Echter DKMS-Bau Exit0/installed für
7.2.11-1-garuda, Srcversion71D6C2E25BA80E69BB4818D und neue Abhängigkeit
kfifo_buf bestätigt. Bekannter Clang23.1.1→23.1.3-Hinweis und CLEAN-Deprecation
erhalten; vorhandene Garuda-/Initramfs-/Snapper-Hooks bestanden, Snapshots91/92.

Nach nachträglicher eigener Freigabe einmaliger Dienststart: aktiv/laufend,
Autostart weiter enabled, PID51607/NRestarts0, neuer Build mit ParameterY/Y/Y
und kfifo_buf geladen. Manager bleibt pausiert, Leases leer, keine native
Bindung und kein neues IIO-Gerät. USB-Identität/Adresse/Inode und xpad-/
usbhid-Bindung beim Start unverändert. Keine erneute Übernahme, Messung,
Motorprüfung oder SDL-Freigabe; nicht aus Modulbau/-laden ableiten.
Nur Installation und pausierter Start sind jetzt nachgewiesen.
[Ergebnis, Grenzen und nächste Einzelbefehle](COHERENT_IMU_UPDATE.md),
[eigene Prüfmetadaten](evidence/COHERENT_IMU_INSTALL_20261016.json).

**Neuester Stand: kohärente Referenzmessung offline vorbereitet.** Der
Kernelquellcode ergänzt Standard-IIO-KFIFO mit zusammengehörigen sechs
Rohwerten, Host-Monotonzeit und Zähler angenommener IMU-Berichte. Ein
separater Leser konfiguriert keine Attribute, erhält Binärdaten/JSONL/SHA256
und bricht bei Lücken, Instanzwechsel, Pushfehler oder geschlossenem Gate ab.
Ein lesender Client erzeugt keinen Control-/Motorbesitz. Suspend erfordert
später explizites Puffer-Deaktivieren/Wiederaktivieren, kein automatisches
Fortsetzen einer Kalibrierung. Die Uhr ist keine Geräteuhr; Funk-/Sensorverluste
sind aus dem Hostzähler nicht vollständig messbar.

Bekannte Winkel werden nur zwischen tatsächlich gespeicherten Zeitmarken
trapezförmig integriert, mit dokumentiertem Ruhe-Bias und allen fünf
Hypothesen. Keine automatische Profil- oder Achsenauswahl und keine SDL-
Freigabe. Zuerst eine Sitzung mit drei einzelnen 90° links, jede nach neuer
Bereitschaft; rechts/vorne/hinten separat, Rücksetzen außerhalb Auswertung.
180°, Rollen und sechs Beschleunigungslagen folgen später. Installierter
Treiber, Dienst, Daten und Hardware unangetastet; noch kein neuer Installer
oder Sensorlauf. [Implementierung, Prüfung und Freigabegrenze](COHERENT_IMU_CALIBRATION.md).

**Geführter KDE-/IIO-Anzeigetest bestanden:** Nach neuem ausdrücklichem Go
lief der Helfer `b0fc0a1` auf dem Garuda test host einmal mit 30 s Vorbereitung und
90 s Beobachtung. 4.305 Sätze, 89,9878 s zwischen erstem/letztem Lese-
mittelpunkt, alle sieben lokalen Ansagen korrekt; maximale protokollierte
Anforderungsverspätung 20,365 ms. [tester] bestätigt sichtbare Hinweise und
ausgeführten Bewegungs-/Ablegeablauf. Keine Reads während Vorbereitung
oder nach Endansage, Prüfsummen vollständig bestätigt.

Alle drei Gyro-Rohkanäle zeigen im Bewegungsfenster deutlich höhere
Streuung und danach wieder ruhige Werte; keine physische Achsenzuordnung.
Die rund 47,83 Leser-Snapshots/s sind weder USB-Pollingrate noch Sensor-ODR.
Profil 500 war nur eine Umrechnungshypothese; fünf Kandidaten anschließend
offline verglichen, kein echter Bereich ausgewählt. IIO-Werte bleiben
nicht atomar, Winkelintegration null, Bias/Skalierung/Verlustrate offen.
Dienst active/running/PID1060/NRestarts0 und dieselbe 109c/Adresse7/native
USB-/IIO-Instanz blieben erhalten. Kein Dienst-/Treiber-/Systemeingriff,
kein neuer Kernellogabruf oder weiterer Test. Produktive SDL-Ausgabe bleibt
unverändert gesperrt. Originale privat erhalten; [Befunde und Prüfsummen](experimental-gyro-live-002.json).

**Erster Gyro-Anzeigelauf abgebrochen:** [tester] gab einmalig 90 s IIO-Anzeige
mit 30 s Vorbereitung frei. Codex beendete die Aufnahme nach rund 74,76 s,
weil die manuellen Chatansagen nicht zum vorbereiteten Zeitplan passten.
3.600 Beobachtungen samt Rohwerten, Host-Lesefenstern und SHA256 erhalten;
kein Sensorlesefehler gemeldet, aber kein bestandener Ablauf oder belegter
Gyrofaktor. Die ursprüngliche `user_interrupted`-Meldung ist ein generischer
SIGINT-Status; der Abbruch ging von Codex aus. Dienst active/running/PID1060,
NRestarts0 und 109c/gs_native/IIO blieben erhalten. Keine System- oder
Treiberänderung, keine automatische Wiederholung und keine neue Behauptung
über Kernelwarnungen. [Zeitmarken und Befunde](experimental-gyro-live-001.json).

Der Helfer erhält deshalb offline `--guided-kde`: lokale Monotonzeit und
asynchrone Hinweise des vorhandenen `/usr/bin/kdialog`, Vorbereitung ohne
Sensorreads, 90 s Phasenplan, Endhinweis ohne weitere Reads. GUI-Fehler,
übersprungene oder über 2 s verspätete Ansagen stoppen den Lauf und erhalten
den ursprünglichen Fehler. Die echte GUI-Zustellung war hier noch nicht geprüft;
erneuter GUI-/IIO-Test nur nach neuer Freigabe. [Ablauf und Aufruf](EXPERIMENTAL_GYRO_TEST.md).
65 synthetische Diagnosefälle einschließlich vollständig simulierter lokaler
Ansagen und die vollständige Suite `make test` bestehen. Reale Popup-Anzeige
und erneute Sensorbeobachtung wurden dabei nicht ausgeführt.

**Experimentelle LSM6DS3TR-C-Diagnose:** Auf ausdrücklichen Nutzerwunsch ist
der Typ als Arbeitshypothese für einen eigenständigen Offline-/IIO-Anzeiger
vorbereitet. Alle fünf Gyrogewinne separat wählen, Rohwerte und Testwerte
trennen; kein automatisch bestimmter aktiver Bereich und keine Übernahme
in `sdl-sensor-calibration.json`. 125 dps ist eine berichtete ST-Tabellen-
hypothese ohne hier geprüftes lokales Original; vier weitere Gewinne sind
zusätzlich Linux-quellenbelegt. Der vorhandene Kernel interpretiert keine
neuen Register und wird dafür nicht verändert.

Die 12.204 gespeicherten Pakete lassen sich unter allen fünf Annahmen
auswerten. Fehlende bekannte Drehwinkel verhindern weiterhin eine Auswahl.
IIO liefert sechs Einzelattribute ohne gemeinsamen Zeitstempel/Zähler;
der neue Beobachter dokumentiert Lesezeitfenster und Geräteinstanz, integriert
solche Sätze aber nicht zu Winkeln. Präzise Referenzmessungen benötigen
zunächst eine kohärente passive Datenquelle. Dies war der Offline-Stand vor
dem anschließend separat freigegebenen Anzeigelauf, siehe oben.
[Werkzeug und geführter Plan](EXPERIMENTAL_GYRO_TEST.md),
[reproduzierbare Prüfungen](TESTING.md#experimentelle-gyrodiagnose).
Offline-Abschluss: 44 neue synthetische Diagnosefälle und `make test`
bestanden, ebenso 18 Paddle-/12 Sensorfälle aus `make test-sdl`. Alle
12.204 gespeicherten Pakete unter fünf Faktoren verglichen; Rohwerte und
Zeitstempel stimmen vollständig mit der vorhandenen Telemetrieableitung
überein, drei Original-/Ableitungsprüfsummen bestätigt. Keine Rangeauswahl
oder neue Messung. Der Paket-Dokumentenallowlist fehlten verlinkte Berichte;
gezielt ergänzt und vollständige Suite danach erneut bestanden. Kein
Installer oder produktives Paket aktualisiert.
[Prüfmetadaten und Profilvergleich](experimental-gyro-validation.json).

**Sensorhinweise (16. Oktober):** [tester] berichtet DigiKeys Fotozuordnung
LSM6DSO/LSM6DSOTR, stellt die exakte Variante inzwischen aber infrage.
Fotoauskunft als Quelle erhalten; tatsächliches Modell wieder offen,
kein Beweis eines DigiKey-Fehlers oder eines TR-C. Originalfoto/-antwort
wurden hier nicht geprüft. Aktiver Gyro-Messbereich und Firmware-/USB-Skalierung bleiben
unbekannt. Der gezielte Offline-Folgepass belegt anhand des vorhandenen
Linux-ST-Moduls Gyroregister 0x11, Maske 0x0c und vier Referenzgewinne;
der folgende Strukturpass löst jetzt die Appdatei-Dekodierung: 288 Header-,
48 Bereichs- und 96 Datei-CRC bestätigt, alle 48 Inhalte unabhängig
reproduziert. `app.bin`/`cfg_tool.bin` lesbar; Sensor-/Kalibriermeldungen
LSM6DS3TR/QMI8658 sind Firmwareanker und kein realer Chipnachweis.
Drei MCU-Teilformate sind inzwischen empirisch erhärtet; die Kalibriermeldung
führt zu einem versionsübergreifend gleichen Textausgabe-Zielkandidaten.
Kompakte Argumente, Speicher-/Vergleichsbefehle und ABI bleiben offen.
Lokale Referenz bestätigt WHO_AM_I 0f→6a(TR-C)/6c(DSO), gleiche Gewinntabellen;
noch kein solcher GameSir-Lese-/Vergleichspfad belegt. Nächster Schritt:
WHO-/ID-/Sensorwahl-/Init-Pfad und letzter wirksamer CTRL2_G-Schreibwert,
danach Register→USB-Skalierung.
Keine neue Kalibrierung, Datenblatt-/Netzwerkabfrage
oder Hardwareaktion. [Identifikation und CTRL2_G-Folgepass](IMU-STATISTIK-UND-SENSORIDENTIFIKATION.rst),
[maschineller Quellenstatus](imu-sensor-identification.json).

**MCU-Fortsetzung vom 18. Oktober, ohne REA:** Zwei weitere begrenzte
Feldmodelle geprüft: kompakte positive Vorwärtsziele in vier getrennten
Bereichen und signed6-Operanden im Maskenkontext. 132 kurze Zielfelder,
drei Gegenbeispiele gegen falsche Displacementdeutungen und 66 Maskenwerte
über drei Versionen passen. Startliterale und 75 RTOS-Textverweise stützen
einen Suffix mit eigener Load-/Run-Abbildung; alle acht gewählten
Sensoranker pro Version liegen außerhalb davon. Keine vollständige ISA,
Register-/Speicher-/Vergleichssemantik oder Sensorinitialisierung gewonnen;
CTRL2_G, Gyrofaktor und Register→USB-Skalierung bleiben offen.
Eigene Grenz-/Packing-/Layouttests und unabhängige Bytekontrollen bestanden.
Die blattartigen anderen Kompaktformen bleiben mehrdeutig. Details und
Bereichshashes im [Nexus-Bericht](GAMESIR_NEXUS_RESEARCH.md) und
[Quellmanifest](nexus-source-manifest.json). Keine Netzwerk-, Firmware-
oder Hardwareaktion, keine Treiberänderung; Gyrokalibrierung pausiert.

**Neue Offline-Forschung:** GameSir Nexus 2.1.23.0 aus dem lokalen Download
statisch geprüft. Hauptpaket mit 223 Dateien, darunter zwölf G7-Pro-UFW-Dateien;
native Geräte-/Versionsschnittstelle, GIP-Updater mit CRC-Pfaden und
Motion-Kalibrierungsoberfläche identifiziert. Kein bestätigter Gyrofaktor,
keine fertig dekodierte Kalibrierungsantwort und kein sicherer Firmware-
Update-/Rückweg. 8192 LSB/g bleibt experimentell; Laufzeit und installierte
Pakete unverändert. Herstellerdateien/Auszüge bleiben privat; eigene
[Analyse und Quellenmetadaten](GAMESIR_NEXUS_RESEARCH.md) versioniert.
[Roadmap](ROADMAP.md) ordnet Firmwareforschung hinter stabiler Release-Abnahme
und Sensorintegration ein. Keine neue Hardwareabnahme und kein Push.

**Sensor-Fortsetzung:** Die sechs Eigenschaften gehören samt privaten Feldern
als System.Int32 zum gemeinsamen nativen KeyState. Statische Runtime- und
Verweistabellenprüfung löst alle sechs Getter/Setter und Feldoffsets
`0x50…0x64` auf; sie kopieren ohne Skalierung. Sieben geprüfte Eingabe-
Zustandspfade lassen die Felder null. C2-Profilblock mit 34 Byte und /255-
Kurvenumrechnung betreffen Konfiguration. `D4X.SendMessage` ist zugeordnet,
F1 gehört zur JL-Firmwarebridge. MessageC mit getaggten UInt64-Werten und
weitere indirekte Provider bleiben ohne belegten Sensor-/Kalibrierungstag
offen; ebenso die vollständige Header-/Modellzuordnung. Kein Gyrofaktor
und keine globale Abwesenheit einer Nexus-Umrechnung bewiesen. Laufzeit,
experimentelle Accel-Ausgabe und SDL-Grenzen unverändert.
[Datenfluss, Fundstellen und Konsequenz](NEXUS_SENSOR_DATAFLOW.md).

**Nexus-Folgepass vom 18. Oktober, ohne REA:** Profilantworten jetzt über
Typ-/Feld-/Methodenmaps mit dem C2-Enum verknüpft. Zustandsereignisse werden
über generische JSON-Serialisierung an WebView/Testbeobachter geleitet;
globale Serializer-Settings lassen mögliche Converter offen. Die konkrete
MessageC-Methode setzt auch nach möglicher Antwortkopie auf normalen
Rückwegen E_FAIL. Kein tatsächlicher Anwendungscaller oder Sensor-Tag
belegt, daher kein reproduzierter Nexus-Bug behauptet. 178 Typmap-Prüfungen,
drei eigene Integer-Lesertests und abgegrenzte Call-/Hashprüfungen bestanden.
Kein Gyrofaktor. Nächste Priorität ist die vorhandene Controller-`app.bin`:
Sensorwahl → letzte wirksame Initialisierung → mögliche Nachskalierung →
USB-Rohwerte. Keine neue Kalibrierung, Hersteller-Codeausführung, Netzwerk-,
Hardware- oder Laufzeitänderung; kein Push.
Der anschließende begrenzte Firmware-Folgepass reproduziert die bekannten
Kalibrierverweise in drei Appversionen, aber keinen neuen Sensorwriter.
Ein versionsstabiler scheinbarer Sensorverweis ist als gespeicherter
HID-Deskriptorblock widerlegt. Die verbleibende MCU-Decode-Lücke ist damit
präziser dokumentiert; aktives CTRL2_G und Gyroskala bleiben unbekannt.

**Firmware-Fortsetzung, nur offline:** Alle zwölf G7-Pro-Container geöffnet;
Header/Tabellen sowie 126 logische Einträge mit CRC16 bestätigt. Die gelesene
MCU-/Packtoolkonfiguration nennt AC695X, keinen IMU-Chip oder Gyrofaktor.
Der innere Packed-Split ist inzwischen code-/CRC-belegt: 48 Appcontainer
und Metadaten validiert, 24 komplette Key-/No-Key-Inhaltspaare normalisiert
identisch. Der neue Positionsdecoder validiert nun sechs innere Records
und beide enthaltenen Dateien. Feld+8 von app_area ist das Bereichsende,
CRC über [32, Ende); der DV209-Nachlauf enthält nun bestätigte Tondateien
und ein zlib-Objekt. Andere Nachlaufteile bleiben getrennt ungeklärt.
Globale Bank-/Modellauswahl, MCU-Instruktionen und ausgeführter Sensorpfad
bleiben offen. Keine Runtime-/Installations- oder Kalibrierungsänderung.
[Befunde, neue Sensoranker und Grenzen](GAMESIR_NEXUS_RESEARCH.md).

**Neuester Realnachweis: ein kontrollierter Boot-E2E-Test bestanden.**
[tester] kündigte den CachyOS test host-Neustart an und führte ihn selbst aus.
Vorher-/Nachher-Bootkennungen verschieden, erster Nachcheck bei64,43s Laufzeit.
Dienst automatisch nach13,830289s active/running/enabled, PID807/NRestarts0;
Steam-Gamescope startet mit dauerhaftem Wrapper/Mapping. Der Funkcontroller
war zuerst aus (109c/4/xpad), nach dem Einschalten erfolgreiche automatische
100a/9→109c/10/gs_native-Übernahme und READY/Fehler0 im aktuellen Dienstjournal.
GameSir-Inputgerät mit vier registrierten Zusatzcodes und fortbestehendem
Paddle-Mapping im laufenden Steam bestätigt. User bestätigt alle vier Paddles
unabhängig, Kombinationen/Loslassen, normale Eingaben sowie ausschließlich
Controller eingeschaltet, kein manueller Start/Resume/Deadband.

Codex führte nur unprivilegierte Leseabfragen aus; keine manuelle Übernahme,
Reparatur, zusätzliche Wiederholung oder Systemänderung durch Codex. Dieser
Fall belegt PC-Neustart mit anschließendem Funkcontroller-Einschalten; weitere
Bootkonstellationen, Suspend/Hotplug/Mehrfachzyklen und konkretes Spiel nicht
zusätzlich geprüft. Privater Manager-State und Kerneljournal wurden hierbei
nicht neu gelesen. [Kontrollierter Neustart: Belege und Grenzen](STEAM_GAMESCOPE.md#kontrollierter-neustart-am-15-oktober-bestanden).

**Vorangegangene Bestätigung, 18:16 MESZ:** Nach neuer SteamOS-/Gamescope-
Sitzung bestätigt [tester] alle vier Paddles unabhängig und normale Eingaben.
Aktuelle Steam-Prozessumgebung enthält die geprüfte native GUID mit allen vier
Paddlefeldern. Der Dienst wurde schon vor unserer neuen Vorprüfung als
active/running/enabled vorgefunden, PID 2982, NRestarts 0. Persistenter
multi-user.target-Startlink, unveränderte Unit und passendes Modul bestätigt.
Manager unpausiert/gesund, 109c/Adresse 11/Inode 50958 an gs_native und exakt
passende eigene aktive Lease/Tokens [1, 2]. Aktuelle Bootlogs zeigen Start um
18:12:13 und erfolgreichen 100a/10→109c/11-Bootstrap mit READY/Fehler 0.

[tester] hat Vorprüfung und enable --now einschließlich Passwort/Modulladen/
Übernahme freigegeben. Da Zielzustand bereits bestand, ausschließlich lesend
bestätigt, keine erneute System-/Hardwareaktion durch Codex. Alle zehn Checks
bestanden. Autostart ist konfiguriert; ein neuer beaufsichtigter Bootlauf nach
dieser Bestätigung, Suspend, Reconnect und Ship of Harkinian wurden nicht
zusätzlich getestet. Native Laufzeit/Autostart erhalten, Garuda test host unverändert,
kein Push. [Aktueller Bericht und Originalnachweise](STEAM_GAMESCOPE.md#gamescope-paddles-und-autostart-am-15-oktober-bestätigt).

Die folgenden Tagesabschlüsse beschreiben ihre jeweiligen Zeitpunkte; der
aktuelle Betriebs-/Freigabestand steht oben.

**Aktueller CachyOS test host-Betrieb: nativer Bootstrap-Realtest bestanden.**
Am 15. Oktober 17:45–17:48 MESZ genau ein freigegebener Resume-Lauf mit
`gamesir-native-dkms 0.1.0.alpha3-4`, Kernel `7.2.9-2-cachyos-deckify` und
korrigiertem Beobachtungshelfer. Quelle `100a/Adresse 21/xpad`, Ziel
`109c/Adresse 22/gs_native` am selben Hub-Port 1-3.2, neuer Instanztoken und
passende aktive Lease/Kernel-Tokens. Bootstrap `READY`, Fehler 0, Gamepad,
IMU und Handoff bestätigt. Metadatenquarantäne nach rund 561 ms beendet;
keine Fristverlängerung, keine Wiederholung und kein Fehler-Release.

150,075 Sekunden native Beobachtung, 14.691 EV_ABS-/EV_KEY-Ereignisse,
alle 15 geforderten Codes mit Druck und Loslassen, alle vier Stickachsen
−32768…32767 und beide Trigger 0…1023. 611 IIO-Snapshots mit jeweils allen
sechs variierenden Rohkanälen. Kein gemeldetes SYN_DROPPED und keine neuen
kritischen Kernelmeldungen im erfassten Fenster. [tester] bestätigt stabile
Eingaben und einen normal bedienbaren Rechner. Freies Testen belegt keine
neue physische Beschriftungszuordnung der vier Zusatzcodes.
[Zeitplan, Messwerte, Originalnachweise und Grenzen](BOOTSTRAP_CACHYOS_FIX.md#revision-4-korrigierter-bootstrap-realtest-bestanden).

**Endzustand des damaligen Bootstrap-Tests:** Dienst active/running, NRestarts 0,
**Autostart disabled**, paused=false, Zielinstanz an gs_native, eigene Lease
active, aktuelle Fehler leer. `returned=false` bedeutet hier laufenden nativen
Besitz, keinen fehlgeschlagenen Rückweg. Alte Fehler bleiben aufgelöste Historie.
Native Laufzeit bleibt wie freigegeben aktiv; Einmallauf verbraucht, den
bedingten Fehler-Release bei diesem Erfolg nicht nachholen. Kein neuer
Dienst-/Modul-/Bindungs-/USB-Schritt, kein Autostart ohne konkrete Freigabe.
Garuda test host-System unverändert bei Revision 3, kein Push.

**Offline-Grundlage:** Kernel-/Managerkorrektur aus `08bc857` mit vollständigem
`make test`, 246 Adapterfällen unter ASan/UBSan, 139 Managerfällen, Garuda-
Kernelbau/statischer Analyse und tatsächlichem CachyOS-GCC-/DKMS-Bau bestätigt.
Die danach korrigierte Beobachtungspolitik aus `1f90e89` besteht 31 neue
Regressionen und das bestehende Helfer-Make-Ziel. Kernel/Manager/Paket wurden
für die Helferkorrektur nicht nochmals verändert oder installiert. Der reale
Erfolg ersetzt nicht den fehlenden Erstfehlerstatus der historischen Läufe.

**Neuester Installationsabschluss, 18:06 MESZ:** [tester] gab Übertragung und
Installation der beiden optionalen Mappingpakete einschließlich Passwort und
benannter Hooks frei, danach nur Prüfung ohne Steam-Neustart. Genau
`gamesir-native-steam 0.1.0.alpha2-1` und
`gamesir-native-steam-gamescope 0.1.0.alpha1-1` installiert; keine weiteren
Pakete/Upgrades/Entfernungen. Neun Nutzdateien stimmen bytegenau mit den
Archiven, Rechte/Eigentümer und Paketprüfung bestanden. Snapper88/89,
Limine-Sperre, systemd-Benutzermanager neu eingelesen/reexecutiert und
/usr-Zeitmarke aktualisiert. Steam-UnitPID1139, Prozess/Startzeit/Umgebung und
native PID28673 bleiben unverändert. Während dieser Installation aktuelle
109c/Adresse25/Inode60931/gs_native mit eigener aktiver Lease/Tokens[4,5]
vor/nach identisch; keine neue kritische Kernelmeldung im Installationsfenster.
Die seit dem früheren Test geänderte Adresse ist kein kontrollierter
Reconnect-Nachweis. Native Autostart-Einstellung weiterhin disabled.

Der neue Gamescope-ExecStart war bei diesem Installationsabschluss eingelesen,
aber noch nicht gestartet. Die danach bestätigte reale Paddle-Abnahme und
dauerhafte Dienstaktivierung stehen im aktuellen Abschnitt oben. [tester] möchte später
in Ruhe Ship of Harkinian testen; kein ungefragter Spielstart/Profilwechsel.
[Installation, Originale und Grenzen](STEAM_GAMESCOPE.md#installation-am-15-oktober-bestanden-steam-unverändert).

### Frühere Prüfschritte

Die folgenden Befunde beschreiben jeweils ihren damaligen Stand. Vollständige
CachyOS-Fehlstart-, Installations-, Rückweg- und Vorprüfprotokolle bleiben im
[chronologischen Bericht](BOOTSTRAP_CACHYOS_FIX.md) erhalten. Für heutigen
Besitz-/Dienst-/Freigabestand gilt ausschließlich der aktuelle Abschnitt oben.

**Sensorvergleich abgeschlossen:** Offizielles `hid-playstation` und lokal
vorhandene SDL3-Quellen anhand fester Revisionen/Hashes gelesen. Empfehlung:
IIO-Rohdaten behalten; später ein separates evdev-Sensorgerät aus demselben
Decoder mit gemeinsamer nichtleerer `uniq` und verifizierten physikalischen
Skalen. DualSense normalisiert Gyro auf 1024 Einheiten/(°/s); dieser Wert ist
keine pauschale Rohsensitivität und kein GameSir-Faktor. Eigene Gyro-Bias-/
Winkel-/Zeitreferenzen sowie sechs Accel-Lagen und Achsenbelege fehlen.
Keine neue Sensorimplementierung, kein Netzwerk-/Hardwarezugriff; heutiger
Upstream-HEAD im Offline-Auftrag nicht überprüft.
[Technischer Vergleich und Empfehlung](DUALSENSE_SENSOR_COMPARISON.md).

**Frühere Garuda test host-Diagnose vor dem oben dokumentierten Update:** Garuda `7.2.10-1`, passende
Header und DKMS-Neubau von Alpha3 bestanden; `gs_native` bereits geladen,
Dienst active/running/enabled. Ausbleibende Übernahme ist durch gespeicherte
und aktuell bestätigte `paused=true` erklärt: Wartungspause nach dem vorherigen
Alpha3-/ZZZ-Test bleibt über Bootwechsel erhalten. Leere Leases, keine
Port-/Scanfehler; Dongle weiter 100a/xpad/usbhid. Nur lesend untersucht,
keine Wiederaktivierung durch Codex in dieser Diagnose. [tester] führte danach
selbst `gamesir-native resume` aus (Antwort paused=false) und bestätigte
funktionierenden Betrieb. Keine neue lesende Bindungs-/IMU-Messung daraus
ableiten. Der Garuda test host blieb während dieses früheren Offline-Auftrags unberührt;
das spätere freigegebene Update steht oben.
[Diagnose](ALPHA_INSTALLATION.md#Garuda test host-nach-kernelupdate-am-15-oktober-2026).

**Vorheriger CachyOS test host-Hardwarestand:** `0.1.0.alpha3-2` ist installiert; GCC-/DKMS-Bau
für `7.2.9-2-cachyos-deckify` ohne Compilerwarnungen bestanden. Die anschließende
Erstaktivierung und ein einzeln freigegebener neuer Versuch scheiterten jeweils
mit Bootstrapfehler `-19/ENODEV`. Neue 109c-Instanz an xpad, kein nativer
Dauerbetriebsnachweis. Automatischer Fehler-Release im zweiten Lauf pausierte,
konnte die Rückgabe aber nicht bestätigen. Manueller Rückweg danach geprüft:
100a/xpad/usbhid, Nutzer bestätigt normale Eingaben in Steam. Dienst läuft
pausiert mit deaktiviertem Autostart; Modul geladen/ungebunden/Referenzen 0.
Startfehler gezielt offline klären, kein weiterer Hardwareversuch freigegeben.
Gamescope-/Steam-Ergänzung noch nicht installiert; kein Push.
[Belege, Einschränkungen und nächster Schritt](ALPHA_INSTALLATION.md#cachyos-erstaktivierung-bootstrap-blockiert-manueller-rückweg-bestätigt).
Die folgenden früheren Zielstände sind historische Zwischenstände.

**Alpha3 auf Garuda installiert; begrenzter ZZZ-Realtest bestanden.** Nach dem
lesenden Vergleich hat [tester] die Implementierung für `3537:105e` ohne vorherigen
Paketmitschnitt beauftragt. Ein gemeinsamer Treiber/Manager, direkter Start auf
derselben 105e-Instanz und derselbe Eingabe-/IMU-/Motorpfad. Der bestehende
100a→109c-Pfad bleibt erhalten. Die anschließend ausdrücklich freigegebene
Installation ist abgeschlossen. Ein anschließend separat freigegebener
180-Sekunden-Lauf bestätigt den direkten nativen Betrieb und den Rückweg
dieses Exemplars; allgemeine Protokollgleichheit und Dauerstabilität folgen
daraus nicht.
Vollständige Offline-Suite bestanden, darunter 125 Manager-Tests und beide
nativen PIDs im C-Runtime-/Motor-/FF-Lebensdauertest. Modul für den vorhandenen
Garuda-Kernel gebaut. Das Update von `0.1.0.alpha2-3` auf `0.1.0.alpha3-1`
aus `f8ef66b` umfasste genau ein Paket. Tatsächlicher DKMS-Bau für
`7.2.9-2-garuda` ohne Compilerwarnungen/-fehler, srcversion
`67138C65BCA95D0ABEAB517` wie im Referenzbau; 82 Paketeinträge/0 verändert,
63 Nutzdateien bytegleich. Snapper 73/74 und beide dracut-Initramfs gebaut;
bekannter CLEAN-Hinweis, keine neuen Kernel-Fehler/Oops im Installationsfenster,
jedoch vier fremde Split-Lock-Warnungen.

Der Upgrade-Hook pausierte und stoppte den globalen Dienst und entlud das
alte ungebundene Modul. Installationsabschluss: `paused=true`, leere Leases,
`enabled` erhalten; ZZZ `8-5/105e/Adresse 21` und anderer Dongle
`8-6/109c/Adresse 17` unverändert an xpad. Nach gesondert freigegebenem
Modulladen und begrenztem ZZZ-Test sind erfolgreicher END und Rückkehr derselben
105e-Instanz zu xpad bestätigt; der andere Dongle blieb unverändert.
[tester] bestätigt normale Eingaben ohne Freeze und normale KDE-Eingaben nach
der Rückkehr. Aufgezeichnet sind Druck und Loslassen aller elf normalen
Zieltastencodes sowie 704 und 707, insgesamt 13 von 15 Zielcodes; 705 und 706
fehlen. Die physische Zuordnung zu L4/L5/R4/R5 bleibt unbestätigt.
Abschluss: globaler Dienst `inactive/dead`,
weiterhin `enabled`, pausiert und ohne Leases; `gs_native 0.1.0.alpha3` geladen,
ungebunden, Referenzzähler 0. Die Steam-Komponente bleibt unverändert
`0.1.0.alpha1-1` mit ausschließlich bestätigtem 109c-Mapping. Neu vorbereitet:
optionale Steam-Komponente `0.1.0.alpha2-1` mit zusätzlicher, aus gespeicherten
Merkmalen synthetisch SDL-geprüfter 105e-Zuordnung. Keine Installation oder
reale ZZZ-Steam-Abnahme. Der weitere CachyOS test host-Test verwendet auf [tester]' Wunsch
den normalen G7 Pro; frischer SSH-Check bestätigt 100a/xpad/usbhid am Hub.
DKMS/lld sind auf dem Ziel noch nicht installiert. Die gezielte optionale
Gamescope-Launcher-Einbindung ist inzwischen offline implementiert und geprüft;
Installation und reale Abnahme bleiben offen. [tester] aktualisiert das Ziel
selbst, möglicherweise einschließlich Kernel. Keine parallelen Zieländerungen;
nach Abschluss/Neustart sämtliche Voraussetzungen erneut lesend prüfen.
[Gamescope-Paket und kontrollierter Installationsplan](STEAM_GAMESCOPE.md).
[Ergänzung und nächste Etappen](STEAM_INTEGRATION.md#zzz-ergänzung-und-rückkehr-zum-CachyOS test host).
Optionales Paket gebaut: `gamesir-native-steam-0.1.0.alpha2-1-any.pkg.tar.zst`,
SHA256 `2a1219d261fa6105d5f1aaa466f6b9890c4849a10b16ceaf9221707bd1664b33`.
Fünf eigene Nutzdateien bytegleich, Eigentümer/Rechte geprüft, keine
Installationsscriptlets. 77 gezielte Tests und 18 gerätefreie SDL-Fälle mit
1.520 künstlichen Eingabekanten bestanden; zusätzlich 24 native Pakettests.
Alle 15 Steam-Pakettests auch im entpackten Quellarchiv bestanden.
Artefakte und Prüfbeleg: `build/steam-zzz-alpha2-release/`.

Gamescope-Ergänzung separat gebaut:
`gamesir-native-steam-gamescope-0.1.0.alpha1-1-any.pkg.tar.zst`, SHA256
`6a7c1776710f4510599d4d00958f91351d22e6dea4db3c4e60269221d276c4d0`.
Quellarchiv mit acht expliziten Dateien, SHA256
`764a74ed347b29cacae6d5e3afe3f51f92986351951bc7b1bca79c45fe9d80ac`.
Vier Paketnutzdateien bytegleich, root-Eigentümer/Rechte geprüft, kein
Installationsscriptlet. 12 neue Gamescope-, 13 gemeinsame Sitzungs-, 15
bisherige Steam-Paket- und 24 native Pakettests bestanden; Gamescope-Tests
auch aus dem entpackten Quellarchiv erfolgreich. Build und Prüfnachweis:
`build/steam-gamescope-alpha1-release/`. Ausschließlich lokale Offline-Arbeit,
keine Änderung von Kernel-/Managercode und keine Systeminstallation.

[Installationsnachweis und Umfang](ALPHA_INSTALLATION.md#kontrolliertes-alpha3-update-am-14-oktober-2026).
[Realtest und Grenzen](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026).

**CachyOS-Handheld-Vorprüfung, ausschließlich lesend:** Zweiter Rechner mit
`7.2.9-1-cachyos-deckify`, passenden Headern und erforderlichem FF-Stop-Vertrag
grundsätzlich geeignet für den nächsten Buildschritt; `dkms` und `lld` fehlen.
Der tatsächliche Gamescope-Start verwendet `steam-launcher.service` und braucht
eine eigene optionale Mapping-Einbindung. Zweiter G7 Pro laut [tester] über
2,4-GHz-Dongle: zunächst `3537:1022/usbhid`, nach seinem eigenen XInput-Wechsel
um 17:54 MESZ **`3537:105e/xpad`** lesend bestätigt. [tester] bestätigt die
Zenless-Zone-Zero-Ausführung und normales Steam-Rumble. Deadband katalogisiert
105e bislang ohne bestätigten Konfigurationspfad. Die damals installierte Alpha2
unterstützte 105e nicht; eine Hardwareabnahme lag damals nicht vor. Der externe `1022→10bb`-Bericht
beschreibt eine andere Ziel-ID.
Auf CachyOS kein Zielbuild, keine Installation oder Geräteänderung durch Codex erfolgt;
funktionierenden xpad-Zustand erhalten. Offline-Prüfung inzwischen abgeschlossen:
gemeinsamer GIP-Code wiederverwendbar nach Paketnachweis, direkter 105e-Start
plausibel, keine belegte Notwendigkeit eines Wechsels nach 109c. Die damaligen
USB-Aufnahmen enthalten kein 105e; der spätere begrenzte Garuda-Realtest steht oben.
Die damaligen Ablehnungsregressionen bestanden mit 97 Manager-Tests; die
anschließend beauftragte Erweiterung ersetzt diese Grenze gezielt.
Ein gemeinsamer Treiber für Editionen ist verbindlich, keine separate ZZZ-
Implementierung. [Offline-Ergebnis und nächster Nachweis](G7_PRO_VARIANTS.md).
[Befunde und verbleibende Voraussetzungen](STEAM_INTEGRATION.md#cachyos-handheld-lesende-kompatibilitätsprüfung).

**Vorheriger Alpha2-Beleg: FF-Lebensdauerfehler behoben, Reconnect bestanden.** Erneuter Voll-Freeze
bei Funk-Wiederverbindung am 14. Oktober gegen 16:27 MESZ; Reset erforderlich.
Der Fehler bei Besitz/Freigabe von FF-private ist inzwischen anhand des
Treiberquellcodes und des installierten Kernels bestätigt. Automatische
Übernahme wurde zunächst nach Freigabe pausiert. Korrektur besteht
vollständige Offline-Tests, elf neue Lifetime-Fälle, vier erwartungsgemäß
fehlschlagende Altcode-Kontrollen und Kernelbau/statische Analyse. Revision
`0.1.0.alpha2-3` wurde installiert: Paketintegrität und tatsächlicher DKMS-Bau
bestätigt, neuer srcversion, keine neue Kernelwarnung. Anschließend ausdrücklich
freigegeben aktiviert und einmal Funk-Aus/Ein mit eingestecktem Dongle geprüft:
automatischer neuer Bootstrap ohne Deadband/zweites Resume, anschließend echte
Eingaben aller 15 Zielcodes. Nutzer bestätigt normale Funktion ohne Freeze.
Damals Dienst active/enabled, Manager active, Pause aufgehoben; Beobachtung beendet.
Der spätere Alpha3-Installations- und Pausenstand steht oben.
Ein Zyklus belegt keine allgemeine Langzeit-/Boot-/Suspendzuverlässigkeit.
[Detailstand und Grenzen](FF_LIFETIME_FIX.md).

**Neuester Integrationsbeleg: KDE-Anmeldepersistenz bestanden.** Nach manueller
Ab-/Anmeldung und normalem Steam-Start im KDE-Menü enthalten neue Plasma-/
Steam-Prozesse das Mapping automatisch. Frischer Logsatz 17:29:38 MESZ belegt
alle vier Paddlefelder und Maske `0000000000d847ff`. [tester] bestätigt vier
unabhängige Eingaben, Kombinationen, Loslassen und erhaltene normale Eingaben;
auch KDE zeigt die vier Tasten. Dieselbe native Geräteinstanz, Dienst weiter
active/enabled ohne Neustart. Kein spezieller Starter/Terminalhinweis im Test.
Boot-/Update-/Autostart-/Gamescope- und neue Ingame-Abnahme bleiben getrennt.
[Reale Abnahme und Belege](STEAM_INTEGRATION.md#reale-anmeldung-und-normaler-kde-menüstart-bestanden).

**Vorheriger temporärer Integrationsbeleg:** Nach ausdrücklicher Freigabe erkannte Steam
1791918634 mit temporärem SDL-Mapping alle vier Paddles unabhängig, einschließlich
Kombinationen und Loslassen; normale Eingaben blieben erhalten. Der Screenshot
des Dark-Souls-III-Layouts belegt vier getrennte Steam-Belegungsplätze mit
[tester]' Auswahl L4→Y, R4→B, L5→X und R5→A sowie den über das reguläre Namensfeld
gesetzten Anzeigenamen „Gamesir G7 Pro“. Keine neue Constance-Spielabnahme und
keine zusätzlichen XInput-Spielbuttons nachgewiesen.

**Historische Persistenzlücke:** Beim separat erlaubten Normalstart ohne SDL-Hinweis um
14:04:52 UTC verschwanden die Paddles wieder: Standardmapping und Capability-
Maske `00000000009843ff` statt `0000000000d847ff`, vom Nutzer bestätigt.
Regulärer UI-Import und zusätzlicher Normalstart um 14:17 UTC blieben ebenfalls
ohne Paddles. Nach korrigiertem und real geprüftem FF-Abbau hat [tester] die
dauerhafte optionale Komponente `gamesir-native-steam` erneut beauftragt.
Separates Paket `0.1.0.alpha1-1`: gemeinsame Plasma-Sitzungsumgebung für
Menü/Desktop/Autostart; expliziter Starter für separate Gamescope-Einbindung.
Konflikte mit vorhandenen Gerätefamilien-/Dateimappings erhalten deren Vorrang.
Separat freigegebene Installation am 14. Oktober um 17:21 MESZ abgeschlossen:
ein Paket, fünf Nutzdateien bytegenau, Paketintegrität 17 Einträge/0 verändert.
Native Alpha/Dienst/Modul unverändert, Steam geschlossen, keine Abmeldung oder
Aktualisierung der laufenden Sitzungsumgebung. Anschließender realer
Anmelde-/Menütest inzwischen bestanden, siehe neuesten Beleg oben.
[Paket, Grenzen und konkrete Abnahme](STEAM_INTEGRATION.md).
[Realtest, Belege und Grenzen](STEAM_ELITE_PADDLES.md).

**Offener Absturzbefund:** Vollständiger Rechnerstillstand am 14. Oktober,
Kernel-Listenkorruption im DRM/TTM-Abbau, AMDGPU-Oops und Soft-Lockup.
GPU-Undervolting −120 mV bestätigt, vom Nutzer anschließend zurückgestellt;
Ursache weiterhin offen. Auch `gs_native` ist nicht ausgeschlossen. [tester] gab
nach eigener Rückstellung die oben dokumentierte Fortsetzung ausdrücklich frei.
Native Instanz/Bindung blieben dabei unverändert; keine neuen kritischen
Kernelmeldungen im beobachteten Fenster. Kein Langzeitstabilitäts- oder
Reparaturnachweis. [Diagnose und Belegsicherung](SYSTEM_FREEZE_20261014.md).

Vorheriger Aktivierungs-/Spielebeleg: Manager-Korrektur `0.1.0.alpha2-2` installiert und am
14. Oktober kontrolliert wieder aktiviert. Dienst active/enabled, Manager
active ohne Konflikt, Pause aufgehoben; Dongle in 109c mit IF0 gs_native,
IF1 ungebunden. Name GameSir G7 Pro und normale KDE-Eingaben nutzerbestätigt.
Alle 15 geforderten Tastencodes registriert. Im anschließenden Constance-Test
bestätigt [tester] durchgehend normale Eingaben; 55 Statusproben über 272 Sekunden
zeigen dieselbe gesunde native Instanz ohne Managerkonflikt. Die vier Paddles
ließen sich im Spiel nicht belegen. Überwachung auf Nutzerwunsch beendet,
Mapping/Steam-Einstellungen unverändert, Dienst weiter aktiv.
[Spielelauf und Grenzen](STEAM_PROTON_BUTTONS.md#constance-test-am-14-oktober-2026-stabiler-kurztest-paddles-nicht-belegbar).
[Update und Wiederaktivierung](MANAGER_CONFLICT_FIX.md#kontrollierte-wiederaktivierung-am-14-oktober-2026).

Offline-Prüfung zum Realtest: neue `sp.js` des Clients 1791918634 statisch geprüft,
SHA256 `5a28c25041d07e69cf591a414519e0cf970b6884c1a0106659dcd9f1fb9586f9`.
Die Grip-Gates gelten unverändert. `make test` und 18 Paddle-/17 Mapping-Audittests
bestanden. Erweiterter SDL-Nachweis: zehn Fälle, 944 Kanten mit Kombinationen,
Achsen und D-Pad. Kein virtuelles Elite-Gerät und keine Änderung am Kernel-/
Managercode oder der installierten Alpha.
[Quellen, Grenzen und konkrete Abnahme](STEAM_ELITE_PADDLES.md).

## Nachgewiesen

- Revision-4-Bootstrap am CachyOS test host: realer 100a→109c-Wechsel ohne Deadband,
  bestätigte native Übernahme, 150 Sekunden Eingaben/IMU, alle 15 Zielcodes mit
  Druck/Loslassen und vollständige Stick-/Triggerbereiche. Nutzer bestätigt
  stabilen Rechner und normale Eingaben. Native Verwaltung bleibt aktiv,
  Autostart aus; kein neuer Motor-/Boot-/Suspend-/Reconnect-Nachweis.
  [Belege und Grenzen](BOOTSTRAP_CACHYOS_FIX.md#revision-4-korrigierter-bootstrap-realtest-bestanden).

- Kontrolliertes Alpha3-Update am 14. Oktober auf Garuda abgeschlossen:
  genau `gamesir-native-dkms 0.1.0.alpha3-1`, echter DKMS-Bau und 63
  Nutzdateien geprüft, 82 Einträge/0 verändert. Globaler Dienst blieb nach
  dem Upgrade gestoppt/pausiert, beide Dongles unverändert an xpad.
  [Installation und Grenzen](ALPHA_INSTALLATION.md#kontrolliertes-alpha3-update-am-14-oktober-2026).

- Separat freigegebener 180-Sekunden-ZZZ-Lauf abgeschlossen: native 105e-
  Instanz, erfolgreicher END und bestätigte Rückkehr derselben Instanz zu xpad;
  anderer Dongle unverändert. Nutzer bestätigt normale Eingaben ohne Freeze
  und danach normale KDE-Funktion. Vier physische Zusatztasten noch nicht
  bestätigt; keine allgemeine Dauerbetriebs- oder Motorabnahme.
  [Realtest und Grenzen](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026).

- Dauerhafte Alpha2-Aktivierung am 13. Oktober 2026 separat freigegeben und
  erfolgreich ausgeführt. Dienst `active/running` und `enabled`, keine
  Dienstneustarts, alle drei Dauerbetriebsparameter aktiv. Automatischer
  Bootstrap ohne Deadband von 100a/17 nach 109c/18; Interface 0 bleibt bei
  `gs_native`, Gerätename `GameSir G7 Pro`. Alle 15 geforderten Tastencodes
  tatsächlich gedrückt/losgelassen, volle Stick-/Triggerbereiche und D-Pad.
  L4=704, R4=705, L5=706, R5=707 nach ausdrücklich korrigierter Nutzerangabe:
  bei den Ansagen waren die Tastenpaare vertauscht. Der Dienst blieb damals zum
  Spielen aktiv; aktueller Installations-/Pausenstand siehe oben. Reale Boot-,
  Suspend- und Hotplug-Tests stehen aus.
  [Aktivierungsbericht und Grenzen](ALPHA_INSTALLATION.md#ergebnis-der-dauerhaften-aktivierung).

- Kontrollierte Erstinstallation am 13. Oktober 2026 abgeschlossen:
  `gamesir-native-dkms 0.1.0.alpha2-1`, Quellen aus `8d566f0`.
  DKMS meldet für `7.2.9-2-garuda` installiert; Modulversion/vermagic passen,
  reales Bauprotokoll ohne Compilerwarnung/-fehler. Paketprüfung: 75 Einträge,
  keine veränderten Dateien. Dienst `disabled`/`inactive`, Modul nicht geladen,
  USB-Metadaten und xpad-Bindung vor/nachher identisch. Der neue DKMS-Hinweis
  auf veraltetes `CLEAN` wurde dokumentiert und nicht automatisch korrigiert.
  Keine Aktivierung oder Bindungsänderung während dieses Installationsschritts;
  spätere Aktivierung siehe oben. [Nachweis](ALPHA_INSTALLATION.md).

- Hardwaretest 003 erfolgreich abgeschlossen: eigenständiger Bootstrap ohne
  Deadband von 100a/11 nach 109c/12 in 2,310 s; 120,009 s Eingaben/IMU,
  22.337 Input-Ereignisse, volle Stick-/Triggerbereiche und Drücken/Loslassen
  aller 15 getesteten Tastencodes einschließlich 704–707. 451 IMU-Snapshots,
  alle sechs Rohkanäle variieren. END bestätigt; anschließend 100a/13 mit
  xpad/usbhid, normale KDE-Eingaben nutzerbestätigt. Das ungebundene Modul
  um 14:08:22 UTC separat entladen. Keine Motorimpulse in diesem Lauf.
  Die physische Einzelbeschriftung blieb in diesem historischen Lauf offen;
  spätere Alpha-Zuordnung siehe oben.
  [Ergebnis, Grenzen und Belege](HARDWARE_TEST_003.md).

- Der Startkern ist im Kerneladapter angebunden und offline gebaut: expliziter
  Bootstrap-Aufruf, dynamische Root-/Hub-/Portzuordnung, neue Instanzen bei
  Wiederverbindung und einmalige Runtime-Übergabe. 55 simulierte Adapterfälle,
  vollständige Regression, Modulbau und statische Analyse bestehen. Kein
  allgemeiner Langzeitbetrieb nachgewiesen; der explizite Start und die spätere
  automatische Alpha-Aktivierung sind oben belegt.
  [Kernelanbindung und Grenzen](NATIVE_STARTUP_KERNEL.md).

- Eigenständiger Startablauf als transportfreier C-Baustein implementiert:
  neun Übergangs- und sechs native Initialisierungspakete bytegenau aus
  gespeicherten Aufnahmen geprüft; 75 Sendefehler und weitere Identitäts-/
  Frist-/Besitztests erfolgreich. Die Verbindung der getrennten Aufnahmen
  ist synthetisch. Die Kernelanbindung und der reale Start sind inzwischen geprüft, siehe oben.
  [Offline-Implementierung](NATIVE_STARTUP_OFFLINE.md).
- Gerätezuordnung ist im Offline-Startkern portunabhängig und von IMU-/
  Gamepad-Bereitschaft getrennt; zwei gleichartige Dongles und Wiederanmeldung
  sind mit künstlichen Adapterereignissen geprüft. Linux-Probe/Disconnect sind
  inzwischen angebunden; echte Hub-/Hotplug-Integrationstests bleiben offen. Gespeicherte USB-Serienstrings
  unterscheiden sich zwischen 100a und 109c; keine gemeinsame UID belegt.
- Der kontrollierte native 300-s-Lauf vom 12. Oktober ist abgeschlossen:
  je drei Impulse pro Motor bei 100 % und 1.000 ms, alle zwölf laut [tester]
  spürbar und beendet. Eingaben und alle sechs IMU-Rohkanäle liefen während
  jedes Impulsfensters weiter. Mindestens fünf Sekunden Pause nach jedem
  bestätigten STOP wurden eingehalten.
- Der native USB-Mitschnitt belegt 36 vollständige erfolgreiche
  13-Byte-Motorpakete: zwölf Starts und 24 Nullpakete, alle exakt durch den
  C-Encoder reproduziert. Der gemeinsame Sequenzzähler läuft über
  697 Übertragungen einschließlich zweier Überläufe ohne Lücke weiter.
- Im nativen Fenster wurden 34.125 GIP- und 18.744 IMU-Berichte erfasst,
  ohne USB-Fehler oder neue Kernelwarnung. Weitere 15 vollständige erfolgreiche
  8-Byte-Berichte mit Kennung `0x03` werden von beiden Decodern als unbekannt
  behandelt und erklären `rejected=15`; ihre Bedeutung ist noch ungeklärt.
- Nach END kehrte das Gerät ohne zusätzlichen Umschalt- oder Rückbindebefehl
  zu 100a/Adresse 33 mit xpad/usbhid zurück. `gs_native` wurde anschließend
  separat freigegeben um 18:01:05 UTC entladen. Normale Eingaben im KDE Center
  sind vom Nutzer bestätigt. [Nativer Ergebnisbericht](NATIVE_MOTOR_COMPARISON_RESULTS.md).
- Sprint-002-Aufnahme mit VID `3537`, PIDs `100a`/`109c` und Neuanmeldungen.
  Busadresse und PID müssen vom Treiberbesitz getrennt betrachtet werden.
- Im Sprint-002-Mitschnitt stimmen C-Kern und eigener unabhängiger Python-Parser
  bei 1.458 XInput-, 3.786 GIP- und 12.204 IMU-Berichten im geprüften Umfang überein.
- Im früheren Sprint-002-Auszug werden zehn Viermotor-, neun Übergangs- und
  521 Wartungspakete bytegenau reproduziert. Fehlerhafte/abgeschnittene
  Übertragungen bleiben ausgeschlossen. Alle vier Motoren wurden damals
  laut Nutzer bei 100 % einzeln gespürt.
- Der aufgezeichnete Deadband-Vergleich vom 12. Oktober bestätigt zusätzlich
  drei erfolgreiche Start-/Stopp-Paare je Motor, alle zwölf laut [tester] spürbar
  und beendet. 24 Motorpakete stimmen bytegenau mit dem nativen C-Encoder
  überein. Das beweist nicht die mechanische Wirkung des früheren nativen Laufs.
  [Historischer Deadband-Vergleich](MOTOR_COMPARISON_RESULTS.md).
- Zwölf gerätefreie SDL-Bibliotheksfälle bestätigen den geplanten evdev-Weg:
  IIO allein wird nicht als Gamepad-IMU übernommen, ein separates geeignetes
  Input-Sensorgerät mit passender eindeutiger `uniq` dagegen schon.
  SDL2-Compat nutzt SDL3; dies sind keine zwei unabhängigen Implementierungen.
- Hardwaretest 001 belegt native 100a-Eingaben mit vollen Stick-/Triggerbereichen,
  D-Pad und elf Tastencodes. xpad-Rückbindung lesend geprüft; normale Funktion
  anschließend vom Nutzer im KDE Center bestätigt. [Bericht](HARDWARE_TEST_001.md).

Nachweise: `core-capture-validation.json`, `experimental-accel-validation.json`,
`imu-calibration-analysis.json`, `SDL-SENSOR-ERGEBNIS.rst` und [PROTOCOL.md](PROTOCOL.md).

## Experimentell und offen

- Manager-/Statusclient-Korrektur für Paketrevision `0.1.0.alpha2-2`:
  passive Getter von aktiven Operationen getrennt, periodischer Status mit
  Kernel-Tokens auf demselben FD gebunden, exklusiven Kontrollkanalkonflikt
  sichtbar abwarten und echte Quarantäne konsistent speichern. Kein pauschales
  Prozess-Allowlisting, kein Entfernen der Mutationsguards. Kernel/UAPI,
  alle 15 Tastencodes, IMU und vier Motoren unverändert. `make test`, acht
  SDL-Zusatztastenfälle, Paketbau/-audit und Bau der extrahierten DKMS-Quellen
  erfolgreich; Paketquellencommit `3326e02`. Paketupdate am 14. Oktober
  gesondert freigegeben und mit Nachkontrolle abgeschlossen. Anschließend
  native Wiederaufnahme mit KDE-Funktionsbestätigung erfolgreich; konkrete
  Constance-Kurzprüfung ohne Managerkonflikt siehe oben. Langzeittest und
  gezieltes Auslösen sämtlicher Konfliktpfade auf Hardware bleiben offen.
  [Vertrag, Nachweise und Aktivierungsplan](MANAGER_CONFLICT_FIX.md).

- Reale Steam-Testvorprüfung am 13. Oktober angehalten: Dienst weiterhin aktiv,
  aber Manager für die native 109c-Instanz `blocked` nach fremdem Gerätehandle.
  Ein früherer gleichartiger Konflikt lässt sich anhand derselben PID dem
  Constance-Prozessverbund zuordnen; die genaue USB-Operation bleibt unbekannt.
  Ein verschwundener Prozess hebt diese Sperre nicht auf. Kein neues
  Steam-Mapping oder Spieltest ausgeführt. Zusätzlich liegen zwei Kernel-Oops
  im AMDGPU-Pfad vor; Ursache offen, regulärer Neustart vor weiteren Spieletests
  empfohlen. Der separat freigegebene Rückweg ist abgeschlossen: persistente
  Managerpause, Dongle entfernt, Besitzauflösung geprüft, wieder eingesteckt,
  `100a/xpad/usbhid` beobachtet und normale KDE-Eingaben nutzerbestätigt.
  Damals Dienst aktiv/aktiviert, native Übernahme ausdrücklich pausiert, auch
  über Neustarts. Korrektur und Wiederaufnahme am 14. Oktober siehe oben;
  die konkrete Konfliktabnahme beim Steam-/Proton-Spielstart bleibt offen.
  [Befunde und Grenzen](STEAM_PROTON_BUTTONS.md#reale-vorprüfung-am-13-oktober-2026-test-angehalten).

- Aktuelles Abnahmekriterium: L4/R4/L5/R5 im eigenen Belegungsmenü eines Spiels
  direkt zuweisen, ohne vorab Spielaktionen/Profile einzurichten. Constance ist
  Prüffall, keine Sonderlösung. Die früheren Steam-Logs zeigen native evdev-/SDL-
  Erkennung ohne Paddle-Felder; Constances Player.log zeigt
  `XInputControllerWindows`. Das allgemeine SDL-Gerätemapping ist inzwischen
  temporär in Steam bestätigt, aber noch nicht persistent. XInput hat keine Paddlefelder;
  DirectInput, SDL und WGI besitzen erweiterte Möglichkeiten. Protons vorhandener
  Raw-Joystickpfad ist ein zweiter Kandidat, noch kein nachgewiesener Spielefix.
  [Befunde, Werkzeug und Testplan](STEAM_PROTON_BUTTONS.md).
- Embercade ist ausdrücklich nicht installiert. Seine Installation bleibt der
  separaten Videoaufnahme vorbehalten; keine Projektänderungen vorwegnehmen.
  Späteres Integrationsziel und kein Blocker für diese Alpha.

- Alpha `0.1.0.alpha2` korrigiert die beiden im Installationsaudit gefundenen
  Rückwegblocker: fehlgeschlagene korrelierte 109c-Übernahme wird über Kernel-
  Tokens attestiert und kann kontrolliert neutralisiert werden; das Startbudget
  wird vor der Übernahme geprüft und sperrt keine Bereinigung eigener Instanzen.
  Der zusätzliche einmalige `claim_100a` verhindert, dass USB-Autoprobe eines
  geladenen Moduls das Budget im Dauerbetrieb umgeht.
  Recovery-Besitz und bereits begonnene END-/Rückgabeversuche bleiben über
  Dienstneustarts erhalten. Ein neuer Hostboot verwirft alte Kernelinstanzen,
  ein bloßer Dienstneustart dagegen nicht. Offene Rückwege verhindern die
  Entfernung auch ohne laufenden Dienstsocket. [Audit und Grenzen](ALPHA_INSTALL_AUDIT.md).
- Verbindliche Architektur: `gs_native` ist der normale eigenständige
  Laufzeitbesitzer ohne Entwickler-Zeitlimit. `xpad` ist ausschließlich Fallback
  bei Deaktivierung, Deinstallation oder terminalem Fehler. Weder Funkpause
  noch unveränderte Eingaben führen planmäßig zu xpad zurück. END bestätigt
  keinen Moduswechsel. Bei verbleibendem 109c wird der manuelle Rückweg klar
  ausgewiesen, ohne erfolgreiche normale Spielfunktion zu behaupten.

- Die Plug-&-Play-Alpha ist auf dem vorhandenen Kern implementiert: expliziter
  Dauerbetrieb, dynamischer Sitzungsmanager, begrenzte neue Startversuche,
  Funkdatenverlust/PM-Zustände und kontrollierte Freigabe. DKMS-/Arch-Paket,
  deaktivierte systemd-Unit und überprüfbare Deinstallation sind vorbereitet.
  Zielumgebungen sind Garuda KDE und CachyOS/Gamescope. Diese neuen Abläufe
  sind offline geprüft. Paket und DKMS sind inzwischen installiert, die neue
  Laufzeit wurde aktiviert und mit realen Eingaben geprüft. Funk-/USB-/PM-
  Wiederverbindung und längerer Spielbetrieb bleiben gesondert zu testen.
  [Laufzeit und bekannte Grenzen](ALPHA_RUNTIME.md),
  [Paketierung](ALPHA_INSTALLATION.md).

- 8192 LSB/g ist ein austauschbarer Versuchsmaßstab. Ein gespeichertes
  Ruhefenster ergibt median 1,00291 g: plausibel, keine vollständige Kalibrierung.
- Gyroskop-Empfindlichkeit bleibt eigenständig unbekannt; kein Ableiten aus 8192.
- SDL-Achsenorientierung, Vorzeichen und Bias sind nicht abschließend belegt.
- IMU-Host-Abschlussintervalle im Sprint-002-Mitschnitt: median 16 ms,
  beobachtet etwa 62,53 Hz.
  Dies beweist weder interne Sensor-ODR noch 1000 Hz IMU-Ausgabe.
- Native 100a- und 109c-Eingaben, sechs 109c-IMU-Rohkanäle und Rückgabe an xpad
  sowie die Wirkung aller vier Motoren sind im kontrollierten Umfang getestet.
  Der frühere Motorlauf benötigte den manuellen Deadband-Übergang; Test 003
  belegt inzwischen den eigenständigen Start. Allgemeiner Hotplug,
  konkurrierender Treiberbesitz und udev/SDL-Integration bleiben offen.
- Im früheren 120-s-Lauf war der 400-ms-Impuls am linken Griff laut [tester]
  nicht spürbar. Die Ursache ist weiterhin ungeklärt. Der spätere erfolgreiche
  Vergleich verwendet 1.000 ms und beweist keine behobene Ursache.
- Standard-FF_RUMBLE für Griffmotoren ist implementiert; das Spiel bestimmt
  die Dauer. Der Kernel erneuert kurze Motor-Leases, ohne den Effekt nach
  einer Sekunde abzubrechen. Vier unabhängige Kanäle erhalten eine
  [versionierte lokale Anwendungsschnittstelle](HAPTICS_API.md). Der tatsächliche
  Kernel-Core lehnt den vorgeschlagenen Trigger-Effekttyp ab;
  [statischer Nachweis](FOUR_MOTOR_KERNEL.md). SDLs evdev-Triggerfunktion bleibt
  ohne Anwendungsadapter im Bibliothekstest nicht unterstützt.
  Ein Deadband-Konfigurationsadapter steht weiter aus.
- Die installierte SDL3 und SDL2-Compat erkennen mit dem neuen Mapping vier
  zusätzliche Paddles, ohne normale Tasten zu ersetzen: acht gerätefreie Fälle,
  256 künstliche Druck-/Loslasskanten. Ohne Mapping bleiben es rohe Buttons.
  [Beleg und Grenzen](SDL_EXTRA_BUTTONS.md). Die physische Zuordnung ist mit
  nachträglicher Nutzerkorrektur dokumentiert; reale SDL-Ereignisse und freie
  Embercade-Belegung bleiben gesondert offen.
- Installation und Dienstaktivierung sind abgeschlossen. Die verbleibenden
  Integrationsprüfungen stehen in [NATIVE_INSTALLATION_READINESS.md](NATIVE_INSTALLATION_READINESS.md).

## Git-Grundlage für Sprint 003

Die vorhandene Projektwurzel bleibt bestehen. Der ältere Offline-Parser wurde
kontrolliert kopiert. Keine Originalarbeit wurde verschoben oder gelöscht.
70 ursprüngliche Dateien sind mit SHA256 inventarisiert und lokal gesichert;
Rohmitschnitte bleiben unverändert am bisherigen Ort.

Tests verwenden Projektpfade und ignorierte lokale Konfiguration für private
Belege. Synthetische Fixtures und ein kleiner Zielgeräteauszug erlauben Grundtests
ohne private Capture-Dateien. Neue Ausgaben entstehen ausschließlich in `build/`.

## Historischer Stand: erste Offline-Absicherung in Sprint 003

Die bestehende Motor-/Protokolllogik ist zusätzlich unter ASan/UBSan geprüft:
alle 15 Kanalmasken, unabhängiger Motorstopp, exakte Ablaufgrenzen, FF_RUMBLE
bei laufenden Triggerimpulsen, atomare Zurückweisung ungültiger Anforderungen,
Zeitüberlauf, Null-Motorpaket und unvollständige Eingaben. Die C-Implementierung
musste dafür nicht verändert werden. `make test` führt die neuen Fälle mit aus.
Nachweis: `sprint003-offline-validation.json`.

Diese damalige Prüfung bestätigte Zustandslogik; USB-Serialisierung, gleichzeitige
Schreiber und tatsächliche Motor-/Disconnect-Wirkung waren darin nicht getestet.
Die späteren Hardwarebefunde oben erweitern den Nachweis für die kontrollierten
Läufe, nicht für allgemeine Konkurrenz- oder Disconnect-Fälle.

## Historischer Stand: Kernel-Prototyp offline abgeschlossen

`kernel/gs_native_usb.c` bindet nur das ausdrücklich gewählte Interface 0 und
unterscheidet 100a/XInput von 109c/GIP/IMU. Keine Autoload-Aliase, new_id,
automatischen Identitätswechsel oder erneuten Probeversuche. Implementiert:
Gamepad, IIO-Rohwerte, experimentelle Beschleunigung, atomare Sensor-Snapshots,
begrenzt/exklusiv steuerbare vier Motoren und serialisierte Wartungsbefehle.

Modulbau für Kernel/Header 7.2.9-2-garuda mit clang/LLD 23.1.1, W=1 und Werror
erfolgreich. Clang-Analyse und checkpatch bestehen. Regressionen umfassen
zusätzlich alle 21 aufgezeichneten GIP-Initialisierungen und 17.448 PID-geprüfte
Eingaben. Build, Tests und Grenzen: [KERNEL_PROTOTYPE.md](KERNEL_PROTOTYPE.md),
maschinell lesbarer Nachweis: `SPRINT003_RESULTS.json`.

Bis zu diesem Offline-Abschluss wurde kein Modul geladen, kein USB-Knoten
geöffnet und kein Treiber abgelöst. Es gab keine Firmware-/Profiländerung
oder Systeminstallation.
Damals galt ein bedingtes Go nur für den kurzen 100a-Test nach frischem
Vorabcheck und schrittweiser Freigabe. 109c-IMU/Motoren blieben bis zum
separat freigegebenen Hin-/Rückweg ausgeschlossen; siehe den damaligen
[Hardwareplan](HARDWARE_TEST_PLAN.md).

## Hardwaretest 001: abgeschlossen mit dokumentierten Grenzen

Am 11. Oktober wurden industrialio und der unveränderte USB-Prototyp nach
Einzelfreigaben erfolgreich geladen. xpad wurde ausschließlich von IF0
abgebunden. Eine einzelne xpad-Submit-Meldung mit -ENOENT führte zum Halt;
die anschließend eigens freigegebene Rückbindung stellte xpad/usbhid und die
Input-Registrierung ohne neue Kernelwarnungen wieder her. An diesem ersten Tag
fanden keine native Bindung und kein Eingabetest statt.

Am 12. Oktober wurden nach frischen Prüfungen und einzelnen Freigaben
industrialio und der unveränderte Build aus `4e76ff7` geladen. Der kontrollierte
Test verwendete 3537:100a, Bus 8, Adresse 8, Port 8-6, ausschließlich IF0.
Die identische einzelne xpad-Abbaumeldung -ENOENT entsprach der dokumentierten
Ausnahme; native Bindung, Eingaben und Rückweg erzeugten keine neuen Warnungen.

Auf Nutzerwunsch wurde der ursprüngliche 12-s-Vorschlag vor Ausführung durch
60 s ersetzt: 10 s Ruhe, 40 s Eingaben, 10 s vorgesehene Schlussruhe.
83.475 evdev-Ereignisse belegen Sticks, Trigger, D-Pad und elf Tastencodes.
Beide Sticks: anfänglich stabil und im Endsnapshot X=0/Y=-1; -1 folgt aus der
Y-Umrechnung. In der Schlussphase wurde weiter getestet, laut Nutzer wegen
seiner Reaktionszeit auf die Chatansage. Dieses Fenster gilt nicht als
vollständig unberührte Ruheprüfung; Langzeitdrift/Kalibrierung bleiben offen.

gs_native wurde erfolgreich abgebunden und entladen, IF0 an xpad zurückgebunden;
IF1 blieb usbhid. Nach der lesenden Prüfung bestätigte der Nutzer normale
Funktion im KDE Center. industrialio blieb ohne Referenzen geladen; die
Kernel-Markierung des externen/unsignierten Moduls bleibt bestehen.
[Belege und Grenzen](HARDWARE_TEST_001.md),
[kompakte Messwerte](HARDWARE_TEST_001_RESULTS.json).

## Hardwaretest 002: historische Läufe und abgeschlossener Motorvergleich

Der frühere 120-s-Lauf aus `743407f` erfasste 73.023 Input-Ereignisse und
5.318 IMU-Snapshots. Beide Datenströme liefen während der vier Motorbefehle
weiter; am linken Griff blieb der 400-ms-Impuls für [tester] nicht spürbar.
Der anschließende aufgezeichnete Deadband-Lauf aus `3c64312` bestätigte zwölf
spürbare, beendete Impulse. Frühere Anläufe, damalige Freigaben, Rückwege und
Beleggrenzen bleiben im [Verlauf](HARDWARE_TEST_002_PROGRESS.md) und im
[Deadband-Ergebnisbericht](MOTOR_COMPARISON_RESULTS.md) erhalten.
Die damaligen Client-/Kernelgrenzen 120/135 s und die 400-ms-Impulsgrenze
sind historische Implementierungsstände.

Der neue native Vergleich dauerte von START_CALL bis zur protokollierten
END-Bestätigung 300,013 s. Er belegt den kontrollierten Ablauf vom vorbereiteten
109c-Zustand über native Eingaben, IMU und alle zwölf Motorimpulse bis zur
Rückkehr zu xpad. Dieser historische Lauf bewies noch keinen autonomen Start;
Hardwaretest 003 hat ihn inzwischen bestätigt. Im Entwicklermodus gelten maximal 300 s im Client, 315 s im Kernel und
1.000 ms pro Impuls; die Standard-Sitzungsdauern bleiben 20 bzw. 30 s.
400-ms-Aufrufe bleiben gültig.
[Ablaufplan](NATIVE_MOTOR_COMPARISON.md),
[Ergebnisse und Messgrenzen](NATIVE_MOTOR_COMPARISON_RESULTS.md).

## Nächste Schritte

1. Erfolgreichen CachyOS test host-Bootstrap und laufenden nativen Betrieb erhalten.
   Keine weiteren Wiederverbindungen oder Treiberwechsel aus der verbrauchten
   Testfreigabe ableiten. Bestätigten Autostart und den einen Boot-E2E-Nachweis erhalten; weitere
   Boot-, Hotplug-,
   Konkurrenz-, Suspend- und Mehrgerätefälle gesondert planen/freigeben.
   Garuda test host erst nach konkreter Updatefreigabe auf denselben Stand bringen.
   Den früheren ZZZ-Nachweis samt offenen physischen Zusatzcodes erhalten;
   [tester] bewahrt dieses Exemplar vorerst auf.
2. Die bestätigte Gamescope-Paddle-Abnahme erhalten. Vier native Zusatzcodes
   und eine Paketinstallation allein bleiben ein anderer Nachweis; jetzt ist
   auch der echte Nutzer-/Steam-Umgebungsbeleg vorhanden. KDE-Menüstart ist auf
   Garuda test host bestätigt. Weitere Steam-/Sitzungs-/Updatefälle bleiben getrennt. Direkte Belegung im eigenen
   Spielemenü ist zusätzlich von dessen Eingabe-API abhängig. Keine festen
   Spielaktionsprofile als universelle Lösung. Viermotor-Anbindung getrennt
   verfolgen; Embercade bleibt späteres Ziel und kein Alpha-Blocker. Langfristig
   Deadband-Konfiguration über definierte native Schnittstelle.
3. Gyrofaktor, Achsenorientierung und Bias unabhängig kalibrieren.
   8192 LSB/g bleibt experimentell; finale SDL-Sensorausgabe bleibt gesperrt.
4. Die unbekannten `0x03`-Berichte anhand vorhandener Daten einordnen und die
   ungeklärte frühere 400-ms-Wirkung getrennt vom erfolgreichen längeren Test
   dokumentieren. Neue Hardwareprüfungen brauchen jeweils konkrete Freigaben.
5. Nexus-Erkenntnisse nach der [Roadmap](ROADMAP.md) weiterverfolgen: zuerst
   native Versions-/Modellzuordnung und Sensorpfade offline klären. Firmware-
   Container-/CRC-Prüfung getrennt von Flashen behandeln; kein Updatewerkzeug
   oder neuer USB-Befehl ist durch den Forschungsauftrag freigegeben.

Verbindlich bleiben: Deadband erhalten, native Laufzeit ohne Deadband und
langfristig Zusammenarbeit über eine definierte Schnittstelle.
