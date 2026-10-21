# Control Center — status and reviewed package operations

Latest offline work: [GitHub release packages](CONTROL_CENTER_GITHUB_PACKAGES.md)
can be selected through build-reviewed metadata, downloaded/verified only after
an explicit click and passed to the separate fresh plan/permission flow. No
network on startup/helper setup/removal; no live download or publication yet.
The separately accepted local helper first-/second-start build stays intact.

Latest offline preparation: [first-run helper setup](CONTROL_CENTER_FIRST_RUN.md)
now detects missing/exact/partial helper state and offers separate explicit
setup confirmation. Fixed system mkdir/install commands copy sealed reviewed
payload bytes; no root AppImage/script or automatic package operation. Real
first-install/password acceptance is pending; current installed helper is
unchanged. Generic builds/demo/rehearsal remain separate.

Latest scoped live result, 21 October: one AppImage Steam-integration upgrade
alpha1-1 → alpha2-1 passed, with independent payload/version postchecks and
unchanged native driver. This does not accept core installation/removal.
The requested verified-success heading and Done button (close only the
operation dialog, keep the main window) are now tested offline in a fresh
build; no further package operation is used for that UI refinement.

Earlier offline checkpoint, 21 October: [the AppImage package binding](CONTROL_CENTER_APPIMAGE_PACKAGES.md)
is implemented offline. Only a deliberately reviewed build includes its closed
local data/package bundle. Startup inspects passively; explicit selected-plan
confirmation is the only path to the separately installed helper. Generic
builds/source, demo and fixture rehearsal retain their boundaries. Real package
actions remain untested and need separate approval; no live launch is included.

Earlier checkpoint, 21 October 2026: [genuine package execution is now prepared offline](CONTROL_CENTER_PACKAGES.md),
with a separate action/helper, exact byte handoff, independent root checks,
native ALPM lock/commit/postchecks and explicitly injected Qt integration.
The existing authorization-only helper remains unchanged. No package trust
records, normal live launch flag, deployment or host transaction is enabled.
The earlier checkpoints below retain their original scopes.

20 October 2026. Phase A was visually accepted. **Phase B adds real local
metadata status, exclusively read-only**, using the already available Qt 6 /
QML / PySide6 binding. The driver remains PRE-ALPHA. Installed alpha3-16 stays
frozen during everyday testing. No installation, removal, module/service
activation, manager command, hardware I/O or Steam/SDL modification is part of
this phase. The maintainer subsequently accepted the compact System details
dialog and authorized **Phase C offline backend preparation and testing only**.
No remote inspection, installed-system action, push or release is authorized.

Latest authorization: real read-only AppImage status was visually accepted on
the local desktop. The installation/removal **GUI binding is now prepared and
tested offline**, using the existing Phase C contracts. Normal launch remains
read-only and cannot switch itself into transaction mode. No real installer or
installed helper has been added. The accepted offline flow now also has a
[prepared authorization-only Polkit path](CONTROL_CENTER_AUTHORIZATION.md):
fixed helper/policy source, strict one-shot protocol, bounded transport and
staging are tested with fake agents. No real permission request is made and
the GUI defaults cannot invoke it. Live deployment/password testing remains
separately gated; the helper cannot execute package operations.

Phase D now prepares a bundled AppDir/type-2 AppImage and staged Desktop Entry/
icon with a nonmutating removal preview. No user integration is installed.
The packaging smoke test uses synthetic data and private temporary preferences;
Python/Qt come from the bundle. Local glibc baseline 2.44; binary redistribution,
runtime/source provenance and real target-session acceptance remain open.
[Build, tests, limits and staged integration](CONTROL_CENTER_APPIMAGE.md).

## Phase C: offline installation and removal foundation

`backend.py` and `artifacts.py` prepare a versioned, narrow planning and rehearsal
interface. The ordinary GUI **still uses Phase B read-only status**: install and
remove remain disabled, and that path imports neither backend module. There is no
default/live transport, sudo/polkit prompt, pacman call, downloader, activation
entry point or new installed helper. This is an offline foundation, **not yet a
working system installer**. The separate Phase A simulation is unchanged.

## GUI binding: explicit offline rehearsal

`transactions.py` coordinates component selection, exact immutable plan,
confirmation, worker submission and first-result handling. It calls the real
`Request`, artifact verifier, `build_plan` and one-shot `Session`; it does not
imitate a successful backend response in the QML layer. `rehearsal.py` supplies
only in-memory package bytes, a synthetic review catalog and `OfflinePort`.
Its archives contain marker guard bytes, not executable installers. Fixture
hashes/zero source IDs are **not release approvals**. `PUBLIC_BINARIES` stays
empty. No Phase B snapshot or actual installed inventory is used as authority.

The Qt adapter starts a `BackendJob` only after preparing and explicitly
confirming a plan. It reserves the session on the GUI thread first, rejects
duplicate starts and accepts completion only for that exact session. The
worker stays off the UI thread. The existing status view, original demo and
new rehearsal are distinct modes; supplying real status data to a rehearsal
is rejected. Real-mode action handlers remain inert. Language alone is a
persisted preference; selections, plans, inventory and outcomes are in memory.

The modal dialog has explicit install/removal titles, component checkboxes,
package names/versions, hook effects, retained data and no-activation notice.
Dependent components are never silently selected or removed. Selection is
locked after review; cancel and reopen to edit it. Cancel/Escape before
submission consumes the prepared plan without any transaction. During the
short simulated commit the UI remains responsive, and cancel/duplicate
confirmation is disabled. Closing the application uses its existing
wait-for-worker shutdown path; it is not reported as a successful cancellation
of a started package transaction. Failures keep the original stable code;
uncertain/failed results never become success or trigger retry/reactivation.
After possible hook/transaction effects the package/runtime display becomes
unknown and new requests are locked; do not reuse the old inventory as a fresh
verified state. This rehearsal has no recovery/reset command; close it and
start a new fixture session to test another flow. A future real implementation
requires separately reviewed fresh authoritative evidence and a new explicit
flow after correcting a problem.

### Try the offline flow, as the normal desktop user

```sh
make control-center-rehearsal
# equivalent: python -B tools/control_center/main.py --rehearse-backend
```

The window is labelled **OFFLINE-PROBELAUF / OFFLINE REHEARSAL**, with synthetic
CachyOS and package data. It reads no host or controller status and opens no
password dialog. This source preview is separate from the already built Phase D
AppImage; that artifact is not silently replaced or restarted.

1. Select **Review installation flow / Installationsablauf prüfen**.
2. Explicitly choose driver/manager, Steam, CachyOS Gamescope and/or Xodus
   bridge. Press **Check selection / Auswahl prüfen**. Missing dependencies
   stop before confirmation; correct the selection or cancel.
3. Read exact example package versions, effects, retained data and the notice
   that no activation or restart follows. Cancel remains available.
4. Press **Run offline rehearsal / Offline-Probelauf starten**. The real
   backend checks execute against the in-memory port only; its example package
   inventory is the only thing that can change.
5. Read the verified simulated result. Removal uses the same review and
   confirmation sequence and keeps unrelated example packages.

### Future real flow presented for maintainer approval

This sequence is the live deployment/acceptance gate, **not approval to install
anything now**. The distinct executor has since been implemented/tested offline
as described in [package execution](CONTROL_CENTER_PACKAGES.md):

1. Obtain fresh authoritative host/kernel/header/package and cleanup evidence
   from a reviewed system helper. The ordinary status snapshot cannot replace
   it. Select reviewed, authenticated release artifacts for explicit components;
   resolve prerequisites separately, without an automatic system upgrade.
2. Present the exact target, package versions/hashes/source identities, selected
   optional components, current removal guard and package/snapshot/initramfs
   hook effects. Explain what is retained and that activation is separate.
3. User confirmation permits a single bounded authorization request, preferably
   using a fixed Polkit action and a minimal independently reviewed helper.
   Keep the GUI/AppImage unprivileged. Do not send arbitrary shell commands,
   mutable package paths or passwords through QML. Do not store a password or
   grant passwordless general sudo access. Cancelling authentication stops.
4. The helper independently reattests the plan and exact package transaction
   under the ALPM lock, then commits once. Reuse existing cleanup hooks;
   never run a second cleanup path in the GUI. No source build/download is
   guessed, and no unrelated packages are silently included or removed.
5. Verify package/DKMS/module and service results independently. Report the
   original error and possible prior hook effects on failure; no automatic
   retry, rollback, Resume, activation or reboot. Normal status/controller use
   requires no GUI administrator prompt. A later explicit activation needs its
   own concrete review and authorization.

Still required before this real flow: independent binary records, target helper/
Polkit distribution review, a matching planning observer and explicit live GUI
enablement, plus separate installation/removal acceptance. The newer executor
tests protected-byte handoff and same-lock prepare/commit using only synthetic
boundaries and a private ALPM sandbox; these are not target acceptance.

### Offline GUI-binding validation

Fifteen coordinator cases exercise genuine session/verification checks with
synthetic inventory, explicit dependency selection, immutable/expiring plans,
foreign completion rejection, cancellation, duplicate confirmation, mutated
artifacts and failure preservation. Entire install/remove cycles also run
while file/process/socket/network I/O is forbidden. Eight additional actual
QML/Qt tests use real mouse/keyboard input, DE/EN, worker completion, cancellation,
failure output, no-host mode separation, duplicate protection, responsiveness
and a scrolling 560x480 dialog. The original 26 QML tests remain unchanged.
No real package action, root prompt or driver/hardware access is used.
Final checkpoint: full `make test` passes 1,465 Python cases in 51 groups plus
the existing C/actual-kernel-adapter/sanitizer checks. Optional UI tests pass
34 cases (26 existing plus eight new). Source/Diff/privacy and manifest checks
are recorded locally; no push or runtime installation follows.

### Package ownership and reviewed input

The component allowlist matches the existing recipes:

| Component | Package | Existing source/staging reference |
| --- | --- | --- |
| core | `gamesir-native-dkms` | `scripts/package_alpha.py`, `packaging/arch/PKGBUILD.in` |
| steam | `gamesir-native-steam` | `scripts/package_steam.py`, Steam profile |
| gamescope | `gamesir-native-steam-gamescope` | same script, CachyOS Gamescope profile |
| bridge | `gamesir-native-trigger-bridge` | `scripts/package_trigger_bridge.py` |

The Phase B Gamescope package lookup was corrected to the actual recipe name;
the old `gamesir-native-gamescope` spelling could incorrectly report absence.
A regression binds detector names to the four existing package recipes.

`PUBLIC_BINARIES` is deliberately empty: the published release is source-only.
An arbitrary package plus its self-computed checksum is **not trusted**. A
maintainer-reviewed record must independently pin the exact compressed bytes,
size, package identity/architecture, dependencies, source commit/tag and core
guard hashes; explicitly reviewed previous versions bound any upgrade path.
No guessed download URL, automatic source build, dependency installation or
unreviewed downgrade/reinstall is supplied. Tests inject synthetic review
records; these are not public release approvals or proof of binary provenance.

The verifier accepts immutable bytes, checks the trusted digest first, then
streams the archive without extracting or running anything. It validates
`.PKGINFO`, GPL-2.0-only, exact dependencies and core guard content. It refuses
absolute/traversing/duplicate paths, links/special files, special permission
bits, `.INSTALL` scripts, unexpected conflicts/replacements/provides, truncated
data and oversized archives. Bounds: 64 MiB compressed, 256 MiB declared
expanded, 16 MiB/member, 8,192 members and 32 KiB metadata. Gzip/xz use Python's
standard reader; native zstd decoding requires Python 3.14+. Missing support
blocks rather than installing a decoder. The immutable bytes are reverified
before rehearsal; a future root helper must receive protected verified bytes
or pinned file handles, never reopen a mutable GUI-selected path as authority.

### Version 1 request and transaction rules

The request has exactly `schema: 1`, `operation: install|remove` and an explicit
list of `core|steam|gamescope|bridge` components. Unknown fields, commands,
flags, paths, duplicate selections and activation actions are rejected.
The plan records exact package/version/hash/source identities, the host
fingerprint, expected existing ALPM guard, hook effects, retained user data and
`activate: false`, `reboot: false`. No global xpad blacklist or second device
management policy exists.

`HostEvidence` is a **synthetic authoritative-adapter contract**, not the
unprivileged Phase B snapshot and not a wire claim a future root helper may
trust. It binds distro/architecture, exact kernel/header identity, boot, ALPM
generation, inventory, dependencies, lock and native/service state. Evidence
must be at most 30 seconds old. Plan acknowledgement expires after 120 seconds;
host identity and time are checked again after the simulated administrator
boundary. Acknowledgement IDs are not credentials. Each session is consumed
once, including cancellation or failure; no retry or automatic repair.

Install planning requires reviewed Garuda/CachyOS x86_64, explicit artifacts
and separately resolved dependencies; core additionally requires exact headers.
An unowned loaded native module or previously enabled orphan service blocks a
first install. CachyOS Gamescope and component dependencies remain explicit.
Remove planning does **not** require headers, build tools or network access.
Only installed, selected project packages can be removed. Removing a depended-on
component requires explicitly selecting its project dependent; no recursive
package removal or automatic deletion of unrelated software.

The rehearsal requires an injected `RehearsalPort` test double. It compares the
prepared transaction's exact targets and versions, refuses external downloads
or removals, simulates one authorization decision for the whole selection, then
performs final preflight, a simulated commit and independent post-verification.
Core success requires DKMS installed for the correct target kernel, module version/vermagic,
inactive service and absent loaded module. Installation does not activate it.
Core removal requires absent selected packages and project DKMS entries, confirmed return, absent module
and inactive/disabled service. Existing enablement survives an upgrade but no
service is started. Optional-only operations do not enter the core guard.
All other package inventory must remain unchanged.

### Reuse the package guard, preserve the first failure

The existing ALPM pretransaction hooks own release/stop/unload during core
upgrade/removal. Do **not** explicitly run a second cleanup pass in the GUI.
`packaging/prepare_remove.py` and its `AbortOnFail` hooks remain unmodified.
Offline package doubles invoke that actual function with the existing
`FakeHost`; this tests ownership, references, stop/return failures and disable
order without accessing a service, module or device. For future use the
installed hook and guard must be independently attested before authorization.

Post-verification cannot convert a command exit into success without the
required evidence. A started transaction can already have released/stopped
devices even when ALPM aborts before replacing files: `changes_possible`
therefore remains true on transaction failure/timeout. The original exception
and cause stay in the session for private diagnosis; public outcomes contain
stable codes, not arbitrary stderr or private paths. Repeat confirm/cancel
does not overwrite that first result. No automatic Resume, rebind, force
unload, reboot, rollback or configuration deletion follows a failure.

Removal retains user modprobe overrides, manager recovery records, haptics
group/memberships, unrelated controllers, Steam profiles, global SDL values
and application start options. It is package removal, not a claim that inherited
Steam environments or every optional user-owned file was erased. The existing
[manual cleanup and recovery guidance](INSTALLATION.md) remains applicable.

### Offline validation and gates before any live integration

`make test-control-center` adds 45 backend cases. They use generated archives
from the **existing four staging helpers** with recipe-derived metadata,
synthetic host/ALPM evidence and the actual removal function on a fake host.
Only local test builds/staging are performed, never makepkg/pacman installation,
real authentication, module loads or hardware access. Tests also reject stale
plans, changing hosts, cancelled authorization, extra dependencies/removals,
bad package bytes and wrong DKMS/module results. File/process/socket/network
I/O is prohibited during the complete in-memory transaction rehearsal. The
ordinary 19 demo, 30 detector and 26 QML tests remain intact.
Final checkpoint: `make test` passes 1,433 Python cases across 49 groups plus
the existing C/actual-kernel-adapter/sanitizer checks; the optional 26 QML
cases also pass. No installed-host inspection or system action was used for
Phase C. Generated artifacts and test logs remain ignored in `build/`.

Before any real installation backend is enabled, separately implement/review:

- Approved binary publication, authenticated trust-root/catalog distribution
  and release-asset selection. A source commit/tag or bare checksum does not
  authenticate arbitrary binary input.
- A minimal installed privileged helper with its own authoritative evidence,
  fixed operations, package/guard ownership checks, bounded IPC/output and no
  arbitrary paths or shell commands. The GUI/AppImage must never run as root.
- Final ALPM preparation and target comparison **under the transaction lock**,
  held through commit; reject stale prepared results and external changes.
  The current in-memory model does not prove this real atomicity.
- Package-manager dependency/version resolution, hook/snapshot/initramfs
  inspection, cancellation/timeout handling and trustworthy post-verification
  against each target. No implementation of a second version comparator or
  recovery controller belongs here.
- Concrete maintainer approval of real commands and separate KDE/Gamescope
  installation/removal acceptance. Existing alpha3-16 stays untouched.

## Read local status

As the ordinary desktop user, run `make control-center-status` or:

```sh
python -B tools/control_center/main.py
```

The default window is labelled **READ ONLY / NUR LESEND**. One background
collection starts when the window opens. **Refresh status** explicitly starts
another; no periodic polling, automatic retries or overlapping readers. During
refresh the preceding snapshot is removed; failure never presents old values
as current. The UTC collection time is visible, and after one minute the UI
labels the observation old. This is a snapshot, not continuous monitoring.
Closing the app waits for an outstanding bounded status reader before Qt tears
down its signal objects. It does not stop the driver or service.

The real install/remove buttons are disabled, including their Python action
handlers; changing a demo fixture cannot unlock them. Read-only mode cannot
switch into a synthetic installation mid-session. The independent demo remains
available with `--demo`, without collecting host metadata.

The main page keeps the compact status/installation layout. Technical metadata
is available only through **System details / Systemdetails**, in a separate
read-only dialog labelled for experienced users and troubleshooting. It reuses
the same snapshot without querying again or moving the main page content.
Close by button or Escape; keyboard focus returns to the originating button.
The dialog scrolls on small windows and uses two columns when space permits.
This maintainer-approved design replaces the initial oversized inline panel.

### Sources and evidence limits

| Display | Read-only source | Meaning / limits |
| --- | --- | --- |
| Distribution / architecture | `/etc/os-release` (fallback `/usr/lib/os-release`), uname | Parsed as data, never sourced. Garuda/CachyOS on x86_64 have a reviewed package path; `ID_LIKE=arch` alone does not grant support. |
| Kernel / headers | uname; matching `/usr/lib/modules/<release>/build` | Check prepared UTS_RELEASE, Module.symvers, Makefile and compiler selectors in auto.conf. Mismatch/missing/unreadable are distinct. This performs no build or full toolchain audit. |
| Packages / prerequisites | `/var/lib/pacman/local/*/desc` | Exact names/versions for core, optional integrations and core recipe dependencies. No pacman process, lock, refresh, download or package hook. Other databases/RPM are unavailable, not falsely reported uninstalled. |
| Loaded module | `/sys/module/gs_native`, version | Distinct from package installation and service activity. The module version lacks the package revision; do not claim binary/source equivalence. |
| DKMS registration | `/var/lib/dkms/gamesir-native` | Exact running kernel/architecture link, build artifact and source metadata. Labelled **registered installed · binary not verified**, not a full DKMS integrity check; dkms.conf is never executed. |
| Service / enablement | Fixed systemctl show query below | Active and enabled are independent. This is not manager pause/ownership, nor a readiness proof. |
| GameSir USB presence / bindings | `/sys/bus/usb/devices` metadata and driver symlinks | VID 3537 with PIDs 100a/109c/105e/1022; list all matches individually. Partial enumeration or changed device identity is not absence. 1022 presence does not prove native support. No raw USB or input node is opened. |
| Manager pause / ownership | Not queried | Existing manager interface is privileged. No elevation, saved ownership-state access or change to permissions. A running system service does not prove unpaused management. |
| Wireless connection | Not observed | Receiver presence, USB mode, binding, module or published input nodes are insufficient evidence. No controller/IMU stream is read in Phase B. |

The only child process is this fixed query, as the normal user:

```sh
/usr/bin/systemctl --system --no-pager show gamesir-native.service --property=LoadState,ActiveState,SubState,UnitFileState
```

It uses no shell, no inherited loader/remote-host variables, closed stdin, no
pager, a three-second timeout and a 16-KiB captured-output limit. On timeout or
failure it is stopped without retry. Metadata reads and directory enumeration
are size bounded; package-list and USB identity changes invalidate certainty.
Filesystem snapshots are not globally atomic, and a later change is visible
only after refresh. Permission failures remain explicitly inaccessible; the
GUI neither requests a password nor changes rights. The two external project
links still open only on user selection. No startup network request or online
availability check is made. No system snapshots, serials, user/host identities,
device events or command stderr are persisted by this interface.

### Phase B validation

`make test-control-center` covers the existing 19 demo tests plus 30 detector
tests with synthetic filesystem data and isolated child processes. It checks
header mismatch/preparation, distribution/architecture boundaries, package
absence versus unknown/access failure, dependencies, DKMS registration,
missing module version, partial enumeration, two receivers, changed USB
identity, service failures, output/time limits, clean environment and the
fixed read-only command. It never reads the real host or opens a device.

`make test-control-center-ui` now covers 26 offscreen cases: the 15 original
cases plus real-mode display with an injected collector, disabled actions,
background thread, overlap prevention, failure invalidation, translation,
age warning, small-window navigation, closing during a read and application
shutdown before Qt signal teardown. Additional dialog checks cover unchanged
page positions, no extra query, close/focus restoration, DE/EN, keyboard opening,
Escape and scrolling at small sizes. The complete offline suite passes 1,388
Python cases in 48 groups plus the existing C/adapter/sanitizer checks. A real Qt
event-loop render additionally inspected one authorized **local read-only**
snapshot: Garuda, exact matching prepared headers, core alpha3-16 and loaded
alpha3 module, matching DKMS metadata, active/enabled service, no matching
receiver observed. This is no RF, game, remote-host or runtime acceptance.

`python -B tests/render_control_center.py --status` optionally renders **real
local** metadata and therefore requires the same read-only authorization as
the live window. Without `--status`, rendering remains synthetic. Status
screenshots stay ignored under `build/control-center/control-center-status-*.png`.
The renderer waits in Qt's event loop for the background result; a tight loop
around Python QTest waits initially starved the filesystem reader and was
replaced before the successful capture. The normal UI has no such polling
loop. No installed package or running driver was changed.

## Run the preview

From the source checkout, as the ordinary desktop user:

```sh
python -B tools/control_center/main.py --demo
```

Alternatively `make control-center-demo`. Demo requires the explicit flag;
omitting it now opens the read-only view above. There is no install command.
Root is refused. The optional preview needs an existing PySide6 / Qt 6 installation;
the launcher installs nothing. The default software-rendering path also works
for offscreen QA without GPU access. Normal desktop use still needs a graphical
session. Phase A itself built no AppImage; the separately authorized Phase D
local test build is described in the linked packaging guide above.

## What can be tried

- DE/EN in the top right. The first language follows Qt's system locale;
  unsupported locales use English. An explicit choice, even clicking the
  currently selected language, is saved for subsequent launches.
- The example-situation selector: ready to install, installed/connected,
  receiver present/controller off, no internet, unsupported distribution,
  missing headers, integrity failure, incomplete download, package failure,
  user cancellation and blocked safe removal.
- Install/remove confirmations, cancellation by button/Escape and outcome
  dialogs. Confirmation changes **in-memory examples only**. Successful mock
  installation never pretends the module/service has also been started.
  Removal of the example driver does not claim the physical receiver vanished
  or that its controller is known to be switched off.
- The two explicit external links: the project [GitHub and guides](https://github.com/RetroGamerGER/gamesir-native-linux)
  and the already documented official [Deadband repository](https://github.com/broroeror/gamesir-linux-tools).
  Browser launch occurs only on selection; there is no startup network request.
  Deadband remains an independent project, with no implied collaboration.
- Visible, disabled roadmap cards for software updates, TMR-stick calibration,
  controller firmware and receiver firmware. They are informational cards,
  never functional hardware controls.

The always-visible demo banner separates examples from real host state.
The driver, loaded module, receiver presence and controller connection are
four separate fields. Receiver waiting is neutral, not a red error. No USB ID,
neutral packet or missing input is promoted to a connection witness.

Use mouse, Tab/Shift+Tab, Enter/Space, arrow keys in the scenario selector and
Escape in dialogs. Visible focus rings and automatic focus scrolling keep lower
controls accessible at 560×480. Wider windows use four status columns; short
windows scroll. Modal confirmations also fit the minimum size. Direct gamepad
input is **not implemented or tested** in Phase A: adding a real device reader
would exceed its no-hardware boundary. Navigation through keyboard events
translated by a user's session is possible but not a native gamepad acceptance.
Real KDE/Gamescope usability remains a subsequent user review, not a hardware
claim inferred from offscreen rendering.

## Boundaries and architecture

`tools/control_center/model.py` is a pure in-memory state machine with
synthetic `Situation` fixtures. `i18n.py` is the central EN/DE catalog.
`qt_bridge.py` presents these values to QML; `main.py` starts the unprivileged
window. The QML components and line icons are project-owned GPL-2.0-only code.
No external UI framework, manufacturer artwork or downloaded assets are used.

The only persistent preference is `language`, in the application's own
`preferences.ini` under Qt's application configuration location, normally
`$XDG_CONFIG_HOME/GameSirNativeLinux/ControlCenterPreview/` (with Qt's standard
home-config fallback). No preferences file is created merely by viewing the
window. Remove that one preview preference file to reset the language; no
driver rollback is necessary. Tests and screenshot rendering use temporary
preferences, never the user's actual selection.

`status.py` is the separate injectable metadata reader; `status_view.py` maps
facts into translated status without upgrading observations to readiness.
The Qt adapter runs the reader in a background job. The demo state machine
still performs no subprocess, socket, sysfs, input, IIO or package-manager I/O.
There is no sudo/polkit, download or installed-system transaction adapter. Real
install/remove paths cannot be enabled by changing a demo setting.
The example package is explicitly simulated. PRE-ALPHA.3 currently publishes
source/build inputs; the GUI must not advertise an existing trusted binary
download merely because the fixture can show an installation flow.
Only this guide is added to the core source/document allowlist so links in
packaged documentation resolve. The GUI is not added to the DKMS payload;
no package recipe, hook, driver or manager behavior changes.

The Phase C offline foundation references the existing reviewed
`packaging/arch/PKGBUILD.in`, `scripts/package_alpha.py`, package hooks and
`packaging/prepare_remove.py`, with the recovery contracts in
[INSTALLATION](INSTALLATION.md) and [the architecture](ARCHITECTURE.md).
There must be no second USB/driver-management implementation in the GUI.
Use an explicitly versioned narrow action interface; do not run the whole
AppImage as root or arbitrary shell fragments. Real operations need reviewed
release-asset selection, HTTPS/provenance/integrity checks, a concrete human
confirmation and then the administrator prompt. Checksums alone do not prove
trusted provenance. Package hooks, their snapshots/DKMS/boot-image effects,
first-error retention and stop-on-failure remain intact.

Support initially targets Garuda and CachyOS Handheld Edition. RPM/Bazzite
remains a separate unimplemented path. The Eden/Gamescope workaround stays a
[manual application-scoped compatibility note](STEAM_GAMESCOPE.md); no shortcut,
global SDL filter or Steam Input mutation belongs in this UI.

## Offline validation

```sh
make test-control-center
make test-control-center-ui     # optional existing PySide6 / Qt 6
python -B tests/render_control_center.py
```

19 pure tests cover complete catalogs/locale fallback, all example failures,
confirmation/one-shot consumption/cancellation, prerequisites, receiver-off
state, guarded removal and absence of file/process/network/device I/O during
every mock flow, root refusal and absence of live CLI actions. 15 QML tests exercise actual mouse/key events, translated
dialogs, durable language selection, browser-error handling using an injected
opener, both modal types and small/normal layouts. No real browser link is
opened by tests. They also check receiver presence is not equated with a known
wireless state after removal. UI screenshots use only our own rendered window:

- `build/control-center/control-center-de.png`
- `build/control-center/control-center-en.png`
- `build/control-center/control-center-small.png`
- `build/control-center/control-center-confirmation.png`

These are local review artifacts, not a release or an installer. The Phase A
`make test` checkpoint passes 1,358 Python cases across 47 groups plus the
existing C/actual-kernel-adapter/sanitizer checks. The 15 optional QML cases
also pass. GUI tests do not validate real
installation/removal, a network download, controller navigation or the
installed driver's behavior. Phase C now prepares the backend offline as
described above; Phase D adds offline packaging. Live action transport and
installed desktop integration remain separately reviewed future steps.
