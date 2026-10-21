# Control Center — local package and helper review

21 October 2026. Preparation for a **local Garuda/KDE target only**. The
maintainer authorized package/source inspection, passive system checks and a
helper setup proposal. No sudo/pkexec authentication, installed file change,
manager command, host ALPM handle/lock/transaction, driver/service/Steam change,
hardware test, SSH or push is included. Existing alpha3-16 remains in use.

## Concrete packages and provenance

The already used core archive's digest matches the retained installation
receipt. All143 payload paths/modes and non-native bytes were reconstructed
from public tag `v0.1.0-pre-alpha.3`, commit
`b5b9cc34534e5afdb6505322308b364f15e31c2b`. Its native control client was rebuilt
and stripped in an ordinary-user temporary build; those bytes match exactly.
Package metadata, GPL texts, dependencies, safe archive members and the three
cleanup guard hashes pass the existing closed artifact verifier.

Older optional archives contain earlier documentation (and some native build
metadata). They were not silently labelled as exact tag builds. Steam and
bridge candidates were rebuilt from that same local public-tag export with
`makepkg --noconfirm --holdver`, without install/dependency-install flags or
network sources. Non-native payload bytes, paths and modes match independently
staged tag files. The bridge's independently compiled/stripped native shim has
matching mapped sections and program headers; native debug/build metadata is
not claimed bit-for-bit reproducible. No candidate was installed or run against
a controller.

These are **private local review inputs**, not newly published binary assets:

| Component | Version | Bytes | SHA256 |
| --- | --- | ---: | --- |
| core | `0.1.0.alpha3-16` | 782080 | `9a29dd1ba57df9f183b25ab7bc20a4dd30af5bddab16fc41483bd91d9713aebd` |
| Steam | `0.1.0.alpha2-1` | 38051 | `c72599c05cfa1d0cbacafb16814f50b1ac397b82de02c78544f4ba842208001b` |
| bridge | `0.1.0.alpha1-2` | 64214 | `3331ed2a740fb4474bd69ab202eee5267d77eb5919793f6987802c70ef705667` |

The installed older Steam version `0.1.0.alpha1-1` has a separate removal-only
version record: its retained archive has exactly the known five owned payload
paths and no install script. This does not approve installing its older bytes.
The root helper must still inspect the actual installed version/scriptlet state
under its own lock. No recursive dependency removal is allowed.

Gamescope is excluded from this local deployment catalog. Its CachyOS-only
build prerequisites are absent on Garuda; normal dependency checking stopped
that build. No prerequisites were installed or bypassed. This neither rejects
the previously accepted CachyOS integration nor establishes a current remote
build/deployment acceptance.

Local package archives, build metadata, inventories, source copies and detailed
comparisons remain ignored/private. No private build paths or manufacturer
files enter the public repository. `PUBLIC_BINARIES` remains empty; these
records provide no download URL or public binary-release approval.

## Shared passive system inspection

`package_preflight.PlanningEvidence` uses the same `SystemEvidence` methods as
the privileged adapter, but supplies a bounded data-only parser for the full
local package inventory. It opens no ALPM handle, acquires/creates no lock,
queries no manager and opens no input/USB device. It rejects root invocation,
external database locks, changing/duplicate/malformed metadata and mismatching
successive snapshots. Status-view data is still not transaction authority.

The explicit ordinary-user inspection found Garuda x86_64 with matching
kernel/header release `7.2.11-1-garuda` and no missing core build prerequisites.
Core alpha3-16 and bridge alpha1-2 are present; Steam is still alpha1-1. Module
presence and service enablement were read as metadata, not changed. Full package
inventory, boot/process identities and snapshot tokens remain private. Fresh
evidence is required again for any future transaction.

Two real input-format cases were corrected and covered offline:

- makepkg's empty optional `url = ` is valid; empty name/version/architecture/
  dependency/license fields remain invalid.
- Installed VCS packages may have `r123…` versions. Only the inventory grammar
  accepts them; reviewed project artifact versions retain their stricter rule.

## Independent installed catalog and helper checks

The package helper now loads only
`/usr/lib/gamesir-control-center/package-executor/REVIEWED_PACKAGES.json`.
Closed schema1 data allows only reviewed package/installed-version records;
no commands, file paths, URLs or unknown keys. The entry protects this file
alongside its code; the loader uses a fixed path, root ownership/modes,
`O_NOFOLLOW`, `fstat` and a64KiB limit. The GUI request is never a trust source.
Default source/staging catalogs remain empty. The explicit local review is
staged privately and pinned with all other payload bytes, not auto-deployed.

The proposed payload has **13 files**: fixed entry, eight Python modules,
native ALPM bridge, catalog data, separate policy and COPYING. Compiled code,
Python/entry/policy/license bytes and catalog data receive independent source/
build/data checks and hashes; compiler/runtime ABI is local, not universally
portable. GUI and root helper package protocols remain separate from the old
authorization-only helper. Normal GUI/AppImage stays read-only; no live
launcher, transaction or permission probe is enabled by this review.

Read-only preparation found the Polkit service/KDE agent active. All13 new
leaves and three new directories were absent; the new action was unregistered,
as expected. Existing authorization-only helper files are retained. A passing
agent status is not a new authentication acceptance.

## Proposed exact setup scope — requires separate approval

Create only:

- `/usr/lib/gamesir-control-center/package-executor/` — root:root0755;
- `/usr/share/licenses/gamesir-control-center-executor/` — root:root0755;
- `/var/cache/gamesir-control-center/` — root:root0700.

Install only the13 pinned files beneath those helper/license paths plus the
single `io.github.RetroGamerGER.gamesir_native.control_center.packages.policy`
in `/usr/share/polkit-1/actions/`. Entry0755, all other files0644, root:root.
The existing authorization-only helper and its policy are not replaced.

The prepared ordinary-user setup verifies/seals all13 inputs before requesting
administrative permission. Root runs only fixed system `install` commands:
two directory calls and13 exact file copies from sealed stdin, policy last.
It executes no user-owned Python/shell script, reopens no mutable user payload
path and refuses unexpectedly existing destinations. Desktop variables passed
to the graphical sudo askpass are limited; loader/Qt/Python overrides are not
forwarded. No package manager, snapshot/DKMS/initramfs hook, service restart,
driver activation or pkexec transaction test is part of setup.

After copying, only verify exact root ownership/modes/hashes and the loaded
Polkit action. Failure stops without an automatic retry, service restart or
cleanup. The proposed separate removal first verifies unchanged manually owned
files, refuses package-managed/modified payloads, removes the policy first and
only exact files, then only empty owned directories. Cache logs/other data and
all unrelated files are preserved; no recursive removal. Removal also needs
separate approval and does not run during preparation.

The fake-root setup exercise used15 harmless same-user system-install calls
into a temporary directory, zero sudo calls. All13 inputs were sealed; attempts
to write failed. Changing a fixture source after sealing did not change the
copied bytes. The policy was last and cache mode0700. This is offline evidence,
not a real helper deployment or package installation.

Final regression checkpoint: full `make test` passes **1,528 Python cases
in54 groups**, plus the existing C/actual-kernel-adapter/sanitizer checks.
Optional GUI tests pass40 cases. The11 new planning/catalog cases cover the
two real grammar corrections, data-only unchanged inventory, changing/locked/
stale/root snapshots, identical shared fact methods, strict closed review data,
fixed protected catalog path and no-follow descriptor ownership/size checks.
The native helper is compiled with warnings-as-errors; local staged bytes and
old helper preservation are checked separately. No real deployment or package
transaction acceptance is inferred from these tests.

The exact machine-specific command, destinations and immutable review hashes
are supplied privately for approval after the local commit. Fresh setup gates
must pass again. No installation/removal/activation of driver packages follows
automatically. Connecting a reviewed planning snapshot/worker and transport to
a separately enabled live GUI remains a later explicit step.

## Approved local helper deployment result

Later on 21 October 2026, the maintainer approved exactly the prepared helper
setup from source commit `f30638ec8b01f99353b20c7b45080645e8bd905f`.
The private proposal manifest passed again. The setup repeated its passive
source/runtime/kernel/header/destination/action gates successfully, sealed all
thirteen inputs, and completed the fixed privileged install calls with the
policy last. Its read-only postcheck confirmed the exact root-owned payload,
file/directory modes and loaded policy action/defaults. The original
six-file authorization-only helper passed its preservation checks.

This created only the thirteen files and three directories listed above.
No package or permission probe, ALPM handle/lock/transaction, package hook,
manager/device access, service/module/driver/Steam change or activation ran.
Normal GUI/AppImage remains read-only. Real GUI installation/removal and
remote/Gamescope authentication remain untested and separately authorized;
helper installation alone is not their acceptance. Optional removal was not
executed. No retry, cleanup or rollback was needed. The approval is consumed;
no further live operation or push is implied. Detailed local receipts and
machine-specific commands remain ignored/private.
