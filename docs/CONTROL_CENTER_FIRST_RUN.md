# Control Center — first-run helper setup

**Current distribution checkpoint (21 October 2026):** the reviewed Garuda
x86_64/glibc2.44 alpha1 build, corresponding sources, signed revision1 and
publication scope are documented in [the distribution review](CONTROL_CENTER_DISTRIBUTION.md).
Older phase entries below retain their historical dates and boundaries.

## Signed-helper AppImage reuse accepted locally (21 October 2026)

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

## What a normal AppImage user does

The signing-key backup and legacy-helper handover are maintainer operations on
the development machine, not prerequisites for end users. An approved production
AppImage contains only the public verification key, never the private signing
key. Users do not create keys, enter backup passphrases, run migration scripts
or copy our development paths.

On a supported clean system:

1. Download the reviewed AppImage from the project's GitHub release, make it
   executable and open it as the normal desktop user. Status inspection alone
   does not ask for a password or install anything.
2. If offered, choose **Set up helper**, review the small helper-only plan and
   confirm it. Enter the administrator password only in the system window.
   The whole AppImage never runs as root. This does not install the driver.
3. Select the desired components, review the exact package plan and confirm
   installation separately. Package changes use the normal authorization flow;
   helper setup does not grant permanent passwordless package administration.
4. On later starts the exact existing helper is reused without another setup
   prompt. Compatible signed driver updates can be checked/downloaded with the
   same AppImage; both the app and helper independently verify the catalog and
   packages before installation. Updating driver versions does not itself
   require a new AppImage. A changed helper/protocol/trust policy can still
   require a separately reviewed application/helper update.

A conflicting, changed or partial helper installation is blocked, not repaired
silently. The current developer machine has an older helper, hence its separate
one-time migration. Initial setup remains the tested Garuda/KDE flow; other
runtime/session support is limited to the explicitly reviewed profile. The
signed production update channel and current final AppImage are not published
yet; this describes the prepared user flow, not a completed public rollout.
See [handover state and remaining gates](CONTROL_CENTER_HANDOVER.md).

## Local first-run acceptance

Second-start acceptance, separately authorized later on 21 October: the exact
reviewed AppImage passed fresh hash/helper/action checks and passive inspection
returned idle with no setup review/session. The maintainer confirmed the new
main window opened normally, with no setup offer or password prompt. Independent
postchecks found unchanged bytes, owners, modes, inodes and modification times
for all thirteen helper leaves and three directories. Legacy helper/backups
remain intact; core/bridge/module/service baseline unchanged, Steam absent.
No setup/authentication, package action or driver/bridge/Steam change occurred.
This proves local existing-helper reuse across launches, within the same
reviewed Garuda build scope; it adds no general distro/Gamescope claim.

Earlier first-start acceptance:

21 October 2026, after separate explicit approval of helper-only setup through
the reviewed AppImage: fresh retained-backup checks, image/source/payload pins,
matching Garuda kernel/headers and the passive missing-helper prerequisite
inspection passed. The app offered exactly thirteen files and three new
directories. The maintainer confirmed setup in the GUI/password flow and
reported **Helper successfully set up**. Independent passive checks verified
every installed root-owned file's bytes/mode, directory modes and the loaded
Polkit action. A fresh inspection recognizes/reuses the exact existing helper
without authentication. No root AppImage/script execution or package action
is part of this setup path.

Original rollback backups, the unopened old cache directory inode and six
legacy authorization-helper leaves remain intact. New and old caches have
distinct inodes; no migration or cleanup occurred. Core alpha3-16, bridge
alpha1-2, loaded module metadata and enabled/active service remain unchanged;
Steam integration remains absent. The maintainer also confirmed **Done** closes
only the helper dialog and leaves the main window normal. No install/removal,
activation, service/module/Steam change or further authentication followed.
The approval is consumed; future package actions remain separately confirmed.

This accepts the scoped local Garuda first-run helper flow, not generic clean-
system/CachyOS/Gamescope installation, universal password-agent support or
public binary redistribution. Keep the saved backups; restoration over newly
installed files is blocked. Private artifact hashes and detailed receipts stay
in ignored local output. Gyro calibration remains paused; no push.

## Earlier offline implementation scope

21 October 2026. The maintainer requested automatic first-start detection and
an AppImage-guided setup, **offline implementation/tests only**. No real helper
inspection via the new path, authentication, installation/removal/update,
package action, driver/service/module/Steam change, hardware access or push is
included. Existing alpha3-16 and the already installed package helper remain
unchanged. Steam integration remains absent after its accepted manual GUI
removal. Gyro calibration stays paused.

## First-start user flow

A deliberately reviewed build may now include `helper-payload/` alongside its
reviewed package bundle. `FirstRunTransactions` runs background passive checks
and offers **Set up helper / Helfer einrichten** only when all thirteen helper
leaves and its three dedicated directories are absent. Opening the AppImage
alone never opens an authentication window. The generic build, source default,
demo and rehearsal retain their earlier boundaries.

1. Check the scoped build/profile, payload hashes, target ownership/modes,
   system tool/graphical-session prerequisites and absence/registration state.
   An exact existing installation is reused, with no prompt or copy. Partial,
   changed or conflicting state is blocked; there is no silent repair/update.
2. The user chooses Set up helper. A separate modal shows the exact number of
   files/directories, fixed destinations and the effect: helper setup only.
   Cancel/Escape before confirmation sends no command.
3. Explicit confirmation refreshes host/target facts and verifies the review
   deadline. Host facts are also rechecked after directory creation/password
   waiting, before payload copying, and after the copies; a changed package
   runtime or service state blocks success without rollback. Every immutable payload is placed in a sealed memfd **before**
   the first privileged child. Only then may the KDE password window appear.
4. The ordinary-user AppImage orchestrates fixed system tool calls. Successful
   root ownership/mode/hash and loaded-policy checks produce **Helper
   successfully set up / Helfer erfolgreich eingerichtet**.
5. Done closes only the setup modal. A fresh **passive** inspection enables the
   normal package selection/review flow. No package install, pkexec probe,
   driver activation, Resume, service restart or reboot follows automatically.

The initial setup uses the system sudo + KDE `ksshaskpass` window, matching
the previously reviewed manual sealed-input approach. sudo's normal policy may
require multiple prompts; **one prompt is not guaranteed**. No password enters
a Qt text field or log, is sent through the payload stream, or is cached by the
app. No passwordless rule or sudoers edit is installed. Later package actions
still use their separate reviewed Polkit helper/agent and confirmation.

## Fixed payload and root boundary

There is no root AppImage, bundled Python, user script, inline root code, shell,
mutable root source path or arbitrary command. The only privileged argv forms
are validated `sudo -A -p 'Password: ' -- /usr/bin/mkdir ...` and
`sudo -A -p 'Password: ' -- /usr/bin/install ...`. Absolute system executable
paths, known target paths, exact modes, no shell, sanitized environment and
sealed stdin are mandatory. Loader/Python/Qt overrides are not forwarded to the
system password tool. A bounded timeout never kills/assumes completion of the
privileged child or starts another setup command; background reaping preserves
an explicit unknown result. Raw process errors/passwords are not retained.

The thirteen pinned files are the fixed entry, eight Python modules, native
ALPM bridge, root catalog, package policy and GPL COPYING. The package build's
independently reviewed helper pins cover code/native/policy/catalog; COPYING
must match the project's existing full GPL-v2 text. The closed build-time
bundle accepts no runtime target/command paths or network URLs. An independently
reviewed AppImage is the **initial trust source**: this is not a cryptographic
bootstrap from arbitrary user-provided data. Public binary/runtime provenance
and redistribution approval remain pending; staging hashes alone are not
publication approval. The installed helper's later root catalog is independent
of ordinary GUI package requests.

Fixed new directories, root:root:

- `/usr/lib/gamesir-control-center/package-executor/` — 0755;
- `/usr/share/licenses/gamesir-control-center-executor/` — 0755;
- `/var/cache/gamesir-control-center/` — 0700;
- additionally `/usr/lib/gamesir-control-center/` — 0755 **only if absent**.

If the shared parent already exists, verify and retain it and its legacy
permission-only helper. Exclusive mkdir without `-p` reserves new paths; a
concurrent attempt stops instead of adopting someone else's directories. Root
install copies only the exact thirteen leaves from sealed stdin, entry0755 and
others0644, with package policy **last**. Every root-parent protection gate,
mode and final byte hash is checked. No existing leaf is deliberately replaced;
no old helper/policy, user configuration or package is removed. The three-dir
case needs sixteen fixed tool calls; clean shared-parent absence needs
seventeen. A race, first error, cancellation/denial or timeout stops further
commands. After the first command is attempted, failure is conservatively
marked possible partial setup even if the agent may have cancelled before
copying. There is no automatic cleanup, retry, rollback or package operation.
Only read-only policy-registration polling is bounded/repeated after a copy.

## Scope and remaining real acceptance

This is a local reviewed Garuda/x86_64/kernel build, not a universal installer.
System sudo, KDE askpass, system Python, protected libalpm16, active graphical
local session and Polkit are required; missing prerequisites block and are not
automatically installed. The helper/compiler/GLIBC/Python/runtime baseline and
kernel profile retain the limits in [AppImage packaging](CONTROL_CENTER_APPIMAGE.md).
Gamescope password display and clean CachyOS/other-system first runs are not
accepted by fixture tests. The real package-helper root code/catalog/policy
bytes are unchanged from the earlier independently reviewed installation.

A future real test must first identify the target and review exact fresh
paths/hashes and whether setup is necessary. **This machine already has the
helper**: the correct result here is reuse without authentication. A full first
installation requires an appropriately clean test environment or a separately
reviewed/approved helper removal/recovery plan. Never delete the existing helper
to force a first-run test under this offline instruction. Helper setup, driver
installation and activation remain separate approvals.

## Controlled rollback preparation for a later first-start test

Subsequent separately approved local execution, 21 October: fresh review pins
and the before gate passed. Each of the four fixed system renames succeeded,
with its expected intermediate passive gate, followed by held/restore-ready
checks. The thirteen helper leaves and three dedicated live directories are
absent; the package action is no longer registered. Original backup hashes,
owners, modes and inodes match, including the complete unopened root0700 cache
directory. The six legacy authorization leaves/shared parent are preserved.
Core alpha3-16, bridge alpha1-2, loaded module metadata and enabled/active
service are unchanged; Steam integration stays absent. No package transaction,
driver/bridge/service change, restoration, cleanup or AppImage first-start
test followed. The four-rename approval is consumed. Keep backups; a real
first-run launch/setup still needs separate approval. This accepts the scoped
local rollback only, not clean-system first-run installation or Gamescope.

Earlier preparation checkpoint:

After a separate read-only request, the existing local helper was inspected:
all thirteen installed leaves match the independently reviewed hashes,
root ownership and modes, and are not owned by a package. The three dedicated
directories and six legacy authorization-helper leaves match. Core alpha3-16
and bridge alpha1-2 remain installed; Steam integration remains absent.
No executor/package/authentication process or ALPM lock was observed. These
are point-in-time facts, not permission to remove files or interrupt a hook.

The old empty-directory rollback recipe is unsuitable after actual package
operations: private root logs may remain in the root0700 cache. Its contents
were **not inspected** and are not assumed empty. A private, target-specific
plan instead preserves the policy and three complete directory inodes at
fixed, absent sibling backup names. Each rename remains on its own filesystem;
system mv must refuse overwrites and copying fallback. There is no recursive
deletion, log loss, shared-parent removal or package-manager transaction.
Policy is moved first; after every individual step a passive gate checks the
expected intermediate state. Changed bytes, ownership, package ownership,
activity, executable pins or conflicting destinations stop the sequence.
The older authorization-only helper is preserved separately.

The prepared reverse sequence restores cache, license, code and finally policy,
only while original targets remain absent and saved metadata/inodes match.
Even partial first-run setup blocks this reverse path: never restore over new
files or automatically remove them. Keep backups after a successful new setup;
cache migration or cleanup would be a separate decision. Private check scripts
run as the ordinary user; only fixed system mv would run with authentication.

Eight same-user temporary-fixture tests exercise staged rename/reversal,
cache inode/content and legacy preservation, existing/symlink destinations,
changed helper/legacy state, unexpected files, partial-new-setup restoration
refusal and cross-filesystem no-copy refusal. All pass, as do the22 existing
first-run unit tests. No real rename, authentication, removal, setup, package
action or driver/bridge/service change occurred. Fresh checks and explicit
rollback approval are required before execution; launching/confirming the
first-run GUI remains a separate later approval. This is preparation, not
live rollback or clean-system acceptance.

## Offline build and tests

The build-only option requires both independently reviewed inputs; the public
source defaults remain empty:

```sh
python -B scripts/package_control_center.py stage \
  --dest build/control-center-first-run \
  --reviewed-packages /absolute/path/to/reviewed-package-bundle \
  --reviewed-helper /absolute/path/to/reviewed-helper-payload
```

The builder snapshots only the known thirteen helper data files and existing
reviewed package data, not a raw source folder or installation script. Its
manifest marks `helper_setup_included: true`, `installed: false`,
`release_ready: false`. No system destination or menu/desktop entry is written.
Imports/construction remain inert; detection and preparation run in Qt workers.

Offline regressions cover missing/exact/partial/modified helper state,
parent absence, preserved old helpers, no auth before confirmation, expiry,
changing host/target, exclusive directory races, immutable sealed handoff,
changed source after loading, command allowlists and clean environment,
first/mid-copy failures/timeouts and no retry/cleanup/package action. One test
runs actual mkdir/install only as the same ordinary user under a temporary fake
root, stripping ownership flags deliberately; it proves copy/seal/mode behavior,
**not** real root authorization. All real target/agent metadata is injected.
Actual QML tests cover explicit review/cancel, background workers, disabled
close/duplicate confirm while running, success/Done retaining the main window,
fresh planning only, exact existing reuse and visible failure with no retry.
The Qt test wait releases the Python GIL like the real Qt event loop; native
QTest wait alone initially starved the path-verification worker.

`--bundle-first-run-self-test` adds a wholly synthetic missing-helper → review
→ fake copy → success/Done → normal planning sequence to the packaged runtime
smoke test. It explicitly ignores the embedded real payload and host, uses no
sudo/pkexec, and never submits a package action. The packaged test retains a
strong window wrapper before accessing its dialog children; the first check
caught a short-lived PySide wrapper lifetime error. Neither test failure caused
host changes, and fixes are verified offline before any real setup is offered.

Final offline checkpoint: **1,566 Python cases in 56 project groups**, plus
existing C/kernel-adapter/sanitizer checks, and **54 Qt cases in five groups**
pass. The first-run-specific suites contain22 non-Qt and six actual-QML cases.
The final AppImage passes all three packaged smoke lanes (first run, packages,
status), using only bundled Python/Qt and zero privileged calls. Bundled app/
entry bytes match the reviewed working source; the thirteen helper payload
bytes retain their earlier independent pins. DE review/success dialog renders
were inspected offscreen; Done retains its normal right margin. Exact private
artifact hashes, source revision and future approval flow stay in ignored
build output. No real setup path, host authentication or deployment occurred.
