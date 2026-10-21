# Control Center — package execution prepared offline

Latest scoped acceptance: one real local AppImage Steam-integration upgrade
alpha1-1 → alpha2-1 passed. Five payload files/version and unchanged helper/
native module/core/bridge were checked independently; no removal or activation.
Further package operations remain separately authorized. The success/Done
operation-dialog refinement is tested offline; see
[acceptance and limits](CONTROL_CENTER_APPIMAGE_PACKAGES.md).

Earlier checkpoint, 21 October: the separate package helper/catalog/policy was installed
under its own consumed approval. The [AppImage binding](CONTROL_CENTER_APPIMAGE_PACKAGES.md)
now connects build-selected reviewed local data, passive background planning,
selection/review and the existing one-shot transport, **tested offline only**.
Root helper code/installed files remain unchanged. No live binding launch,
authentication or host package action is included; real install/removal gates
remain separate. Generic builds/source remain read-only.

Historical preparation checkpoint, 21 October 2026. PRE-ALPHA. The maintainer authorized **offline implementation
and tests only**. No helper/policy deployment, authentication, package action
against the host, driver/service/module/Steam change or push occurs here.
Installed alpha3-16 and the separately accepted authorization-only helper are
unchanged. That helper cannot install packages and is not upgraded in place.

Later scoped preparation: concrete local package/source checks and an
unprivileged [planning/helper deployment review](CONTROL_CENTER_DEPLOYMENT_REVIEW.md)
now exist. A closed catalog loader accepts only its fixed protected installed
JSON file; default staging and public binary records remain empty. The optional
explicit local catalog and its future installation still need approval.

## Implementation and boundaries

`package_execution.py` is the independent privileged transaction coordinator.
`package_client.py` supplies a distinct one-shot GUI submission and transport;
`package_wire.py` supplies schema 2, with explicit `mode: packages`. This is
separate from schema-1 `authorize_only`; its acknowledgement cannot authorize
or report a package transaction. The GUI remains the desktop user. Passwords
belong solely to the registered desktop Polkit agent.

`ExecutionTransactions` can be explicitly injected into `create_engine` for
integration review. The actual QML confirmation/worker/result path is connected,
with distinct DE/EN package-operation wording, exact versions, hashes, source
commits, tags, kernel and hook effects. A real-mode status snapshot is display
data only; `package_preflight.py` now supplies an explicit data-only inventory
reader using the same facts as the locked root adapter. It must still be
explicitly connected to a fresh GUI selection/worker and reviewed catalog.
Normal CLI/AppImage mode constructs neither the coordinator
nor a transport. It remains read-only, with no new live execution flag.

The prepared fixed privileged invocation is internal, **not an instruction to
run it now**:

```text
/usr/bin/pkexec --disable-internal-agent /usr/lib/gamesir-control-center/package-executor/execute
```

It has its own `io.github.RetroGamerGER.gamesir_native.control_center.packages`
action: active local `auth_admin`, inactive/other `no`, no cached grant,
passwordless rule, internal-terminal fallback or elevated Qt. The fixed entry
checks isolated/no-site/no-bytecode system Python, its location and all
root-owned non-writable code before imports. The client independently attests
reviewed helper/module/native-bridge/policy hashes. Nothing executes from a
user-owned AppImage directory as root.

## Exact bytes and independent package trust

The bounded stream carries typed selection/host/expiry/correlation metadata
and up to four immutable package byte arrays. No client filename, URL, command,
activation or root script is accepted. Duplicate/unknown fields, extra input,
bad sizes, unsupported packages and mismatched receipts stop. Package identity,
architecture, GPL metadata, relationships, archive limits and cleanup guard
hashes use the existing artifact verifier. No extraction or package script is
executed during inspection.

The helper uses its **own installed deployment trust**, not review records sent
by the GUI. It accepts only exact reviewed SHA256/size/version/source records
and separately reviewed installed versions/guard hashes for removal or upgrade.
`DEPLOYMENT_TRUST` and `PUBLIC_BINARIES` source defaults are deliberately empty.
The real entry loads only fixed root-owned `REVIEWED_PACKAGES.json`, with
closed typed data and independently pinned deployment bytes; no GUI-supplied
catalog is authoritative. Source-only
GitHub assets and self-generated staging checksums are not binary approval.
No fake release URL, public binary or signing key was invented. The later local
candidate audit supplies exact hashes privately, without deploying them or
granting public binary-release approval. Real actions cannot be enabled yet;
deployment and explicit GUI/observer integration review are required first.
Same-version repairs and software updates are not
offered by the current GUI selection flow.

After byte verification, packages are placed in a unique private root-owned
0700 cache directory, files0600, held until ALPM finishes. The native adapter
loads these exact files fully. Its local signature level0 is **only** for the
independently approved exact bytes, not permission to install arbitrary unsigned
packages. A wrong/missing root catalog blocks before package preparation.
Hooks and child output go to a private root log, never to the correlated receipt
channel; raw stderr and private paths do not appear in the GUI.

## ALPM, hooks, removal and stop behavior

The small own C bridge uses the installed official `alpm.h`/`alpm_list.h` API.
The transaction uses flags0 and holds the real ALPM lock continuously from
authoritative observation through preparation, commit and postcheck. No package
database refresh, repository registration, network/download, dependency
installation, system upgrade, overwrite, recursive removal, force flag or
second cleanup implementation exists. A competing lock stops; it is never
deleted or bypassed.

The privileged helper reconstructs the plan, rechecks all package inventory,
boot/kernel/header/configuration/service facts, and compares the exact prepared
additions/removals/versions. Unexpected targets, altered host state, expired
confirmation or missing dependencies stop before commit. Preparation and commit
are on the same ALPM handle. Removal selects only named project components;
dependency checks require explicit dependent-component selection.

The production adapter resolves configured hook directories via fixed
`pacman-conf` queries and keeps system and administrator hooks, including
snapshot, DKMS and initramfs hooks. Root/DB paths must be the supported defaults.
It preserves NoUpgrade/NoExtract/IgnorePkg options, respects selected HoldPkg
and refuses configured IgnoreGroup pending a target-group implementation.
It refuses installed scriptlets and unknown installed versions. This is an
explicit limited Arch-family adapter, not a generic distro installer. RPM/
immutable-system and unusual pacman profiles need separate work.

Before touching an installed core, the helper checks the existing cleanup
code/hooks' hashes, package ownership and effective override resolution, then
reattests before commit. A masked/changed cleanup hook stops; it never runs a
second Release, rebind or unload path. Existing ALPM hooks alone perform the
controlled return, service stop and unused-module unload, and disable autostart
on core removal. They may have effects even if ALPM later fails.

Success requires independent package inventory and core DKMS/running-kernel/
module-version/vermagic, inactive service, absent loaded module, correct
enablement and clear return checks. DKMS is queried as `gamesir-native`, while
the module remains `gs_native`. A missing postcheck or unexpected activation
cannot become success. Local modprobe overrides, recovery evidence, group
memberships, other controllers, global SDL/Steam settings and application
launch options are not deleted by this layer.

Cancel before submission or in the Polkit agent stops before commit. After
submission there is no GUI kill button for a package transaction. Lost receipt,
deadline, output overflow or a crash means **completion unknown**, with possible
hook/package effects; the client drains/reaps rather than killing ALPM. It
never retries, rolls back, activates, calls Resume or reboots. The first failure
survives later cleanup errors. After possible effects, new actions are locked
until a separate fresh inspection/review; old inventory is not reused.

## Offline validation and staging

The boundary tests use synthetic host/package/permission adapters. Separate
real-library tests compile the C bridge with warnings-as-errors and use an
empty temporary root/database, a private cache and **only** an empty temporary
hook directory. They install/remove only a harmless marker package inside that
temporary tree, test lock competition and missing dependencies. They neither
read the host package database nor run its hooks or use root/sudo/pkexec.
Actual Qt tests drive the package confirmation worker through the wire parser,
executor and correlated result using the synthetic system edges. No real
system is offered as a test target.

Final checkpoint: **25 execution cases** pass, including real-library sandbox
installation/removal/lock/dependency tests, malformed/correlated wire data,
untrusted catalogs, guard overrides, lost replies, postcheck failures, one-shot
stops, root observation after a simulated password wait and noninstalled
staging. **Five new actual Qt cases** pass; optional GUI total is40. Full
`make test` passes **1,517 Python cases in53 groups**, plus existing C/actual-
kernel-adapter/sanitizer checks. Native bridge build uses warnings-as-errors.
The sandbox initially caught libalpm's required non-NULL error-list parameter;
the final adapter supplies and frees the correctly typed list. The timed test
also prevents validating newer root evidence against an older confirmation
time: evidence is validated at current time without extending plan expiry.
No live success, cross-target acceptance or public binary release is implied.

As the ordinary user, optional local libalpm development files are needed for
the native sandbox/staging checks; nothing downloads or installs them:

```sh
python -B tests/test_control_center_execution.py
python -B tests/test_control_center_execution_ui.py
python -B scripts/package_control_center_executor.py --dest build/control-center-executor
```

The stager writes only a fresh non-system directory: executor, eight Python
files, closed catalog data, compiled bridge, separate policy and COPYING,
plus a review manifest
marked `installed: false`, `reviewed: false`, `release_ready: false`. It does
not replace the installed authorization-only helper. Its compiler/runtime ABI
and hashes need independent target review; it is not a portable public binary.

## Proposed separately approved live sequence

1. Choose the target, exact versions and explicit components. Independently
   inspect the actual package build inputs, bytes, hooks and provenance, and
   populate matching GUI/root trust records. Do not use source-archive hashes
   as binary hashes. Review/build the helper for the target ALPM ABI.
2. Present exact new helper/policy/cache destinations, hashes, existing-file
   safeguards and owned-file removal steps for approval. Deploy only after
   that approval; reattest registration and ownership. The old permission-only
   test does not approve this deployment or any package action.
3. Obtain fresh matching planning evidence using a reviewed observer (not the
   ordinary status snapshot); show the GUI selection and exact plan. Resolve
   dependencies separately. Close games/controller tools before a core change.
4. A separately approved **single installation** uses GUI confirmation followed
   by the desktop password window. The root helper rechecks and commits once.
   Read the verified package/DKMS/service result before proceeding. A successful
   installation leaves activation separate.
5. A **separate removal test** requires fresh evidence, reviewed exact installed
   versions and confirmation/password flow. Check safe return, selected package
   absence and retained configuration afterward. Do not remove unrelated helper
   files or dependencies as part of driver removal.

No live approval is assumed by this document. Target-specific setup/commands
will be shown with the chosen artifacts before any real action. Cancellation,
Gamescope agent availability, real installation/removal, custom distro hooks
and cross-target acceptance remain unproved until those scoped tests.

All new implementation is own GPL-2.0-only code using local documented API
declarations; no manufacturer code/firmware or third-party implementation was
copied. The full existing GPL text and third-party notices are preserved.
