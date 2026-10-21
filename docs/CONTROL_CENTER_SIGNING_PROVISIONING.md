# Release signing and one-time helper migration

21 October 2026. **Production key, verified local encrypted backup and the
explicitly approved one-time signed-helper migration are complete locally.**
The independent read-only postcheck verified the new thirteen-file payload,
preserved complete old executor, unchanged policy/cache/license metadata and
unchanged encrypted backup. No driver/package/service/module/Steam change,
AppImage launch, network request or publication followed. See the current
[handover result](CONTROL_CENTER_HANDOVER.md) and
[acceptance evidence](evidence/CONTROL_CENTER_HELPER_MIGRATION_ACCEPTANCE_20261021.json).
The signed update channel remains unpublished. Off-device backup confirmation,
public distribution audit and real signed-download/package acceptance remain
pending; no new key/signature/catalog revision or implicit rollout approval.

## Historical offline preparation

## Approved offline build checkpoint

The separate Ed25519 release key was generated with system OpenSSL directly
into an exclusively created external user-owned 0600 file, in a 0700 directory.
Protected parents, no symlinks, regular single-link file, format and an offline
sign/verify challenge passed. No private key was printed, logged, copied into
Git/build/helper/AppImage or sent over the network. **Do not generate it again.**
The working key is unencrypted as required by the current publisher; a separate
encrypted offline backup is still pending before public rollout.

Only the [public trust policy](../packaging/control-center/release-signing-policy.json)
is tracked. Raw Ed25519 public key:
`2bc5d23e1900e7d529bbf226118946994a6b58caf7439cfbf3446a7855a75226`.
SHA256 key ID:
`5d9450389dafad61bb573c277557a62484e514c96dcb1acd40b9bcfe5f71544a`.

The new explicitly reviewed AppImage and thirteen-file staged helper contain
the identical public policy and retain accepted package/removal history. No
working key is needed on end-user machines. Generic/source defaults still
do not silently opt into this policy. All four previously audited immutable
public package archives are reused, not rebuilt under existing version names.

The first signed catalog is revision 1, issued 21 October 2026 at 12:36 UTC and
expires 20 November 2026 at 12:36 UTC. It remains unpublished. Its exact envelope
is also retained in an external private catalog-history directory for future
publisher `--previous` checks; this is **public metadata retention, not a
private-key backup**. Do not reuse revision 1 for changed payload bytes.

AppImage SHA256:
`ab90d0a57cb6e7134f35e74f69f7940b8b306054607f90aa1bc09f6912dc0da2`.
Root-review SHA256:
`f56140daee38e7439b11c45cb486af363f5083c41aa7c03d639261c1a5dd3803`.
The thirteen helper leaf pins and machine-specific build paths remain in
ignored local review output for the eventual migration sheet.

Both bundled-Python and staged-helper verification accept the actual new-key
catalog and reject changed payload/signature, expiry and a foreign key. 67
targeted unit/packaging tests, three QML cases and four complete AppImage
synthetic smoke lanes pass. All four actual reviewed archives pass the artifact
verifier. Inclusion scanning found no private key material among 1,719 inspected
source/AppDir/review files. All thirteen installed helper leaves and three
directory snapshots retain hashes/owners/modes/inodes/mtime; cache contents
remain unopened. No real package action or protected-state write occurred.

The runtime's public redistribution/source audit remains pending, so
`release_ready` stays false. The image is a local test build, not a published
signed binary release. The signature authenticates the package catalog; it
does not itself sign the complete AppImage executable. No live signed channel,
helper deployment, authentication or package acceptance is claimed.

## Read-only checkpoint and exact change scope

An ordinary-user read-only inspection compared the installed package helper
against the independently retained, previously accepted AppImage payload.
All **13 regular files**, root ownership, exact modes/hashes and protected
parents match. The executor contains exactly its expected eleven files. Its
directory and the license directory remain root:root0755; the existing cache
is root:root0700. Cache contents were **not** opened or assumed empty. No ALPM
lock or package/auth process with the inspected command names was observed;
this is a preparation snapshot, not a concurrency guarantee at deployment.

The offline signed-update payload changes five executable-support modules:

- `package_alpm.py`, `package_catalog.py`, `package_execution.py`;
- `package_helper.py`, `package_wire.py`.

The sixth changed leaf will be `REVIEWED_PACKAGES.json`, containing the reviewed
package/removal records and the **public** signing policy. Its final hash cannot
be approved until a real public key exists. The entry, native ALPM bridge,
other three modules, Polkit policy and GPL text retain their reviewed bytes.
No driver archive is installed by this migration. Machine-specific hashes,
paths and metadata are kept in ignored local preparation output.

## Stage 1 — approved key creation scope, completed without root

**Completed only after separate approval.** Use a new Ed25519 release key,
separate from GitHub SSH authentication. Do not reuse an SSH key, manufacturer
key or the publicly known unit-test seed. Proposed custody:

- A dedicated user-owned directory outside every repository/build/AppImage,
  mode0700; the private DER key is a single-link regular file, mode0600.
- Create the directory and key exclusively, with no symlink traversal or
  overwrite/adoption of existing paths. Check protected tool provenance and
  parent ownership/modes first. Refuse root invocation.
- System OpenSSL generates the key with its normal secure random source.
  Send private output straight into the exclusively opened file descriptor;
  never to a terminal, command argument, receipt or application log. Flush the
  file and directory before reporting completion. Failure stops without an
  automatic retry, replacement or cleanup of a possibly created key.
- Derive the 32-byte public key and its SHA256 key ID. Validate Ed25519 format,
  ownership/mode/link count and correspondence by an offline sign/verify
  challenge. Only the public key, fingerprint and non-secret status are shown.
- Preserve a separately encrypted offline backup before public rollout; never
  commit, upload or put the private key into an AppImage or privileged helper.
  The signing tool currently reads an **unencrypted** DER/PEM working key;
  encrypted-key prompts, hardware tokens and automatic backup are not
  implemented. File permissions do not protect against compromise of the
  maintainer account. The encrypted backup is a separate custody operation,
  not a promise that the signer supports encrypted working keys.

The key authorizes reviewed package metadata which can lead to privileged
package installation. Keep custody under the maintainer's control. Loss or
compromise requires a separately reviewed trust update; a downloaded catalog
cannot replace/revoke its own key. No private key is needed on end-user PCs.

## Stage 2 — approved public binding and offline build, completed

After the actual public fingerprint has been shown and reviewed:

1. Add only that public key to the initial root review and the identical
   AppImage review. Start with `minimum_revision: 1` and one active key.
   Retain all accepted removal/cleanup-guard history. There is no remote key
   lookup or trust on first use from GitHub.
2. Reuse the already audited immutable public package bytes from
   `v0.1.0-pre-alpha.3`: core alpha3-16, Steam alpha2-1, Gamescope alpha1-1 and
   bridge alpha1-2. Do not rebuild/relabel the same published versions or
   replace their archives. No repeated network download is needed for this
   offline build.
3. Compile/stage the helper and build a new AppImage **once** with the fixed
   public trust anchor. Record exact source, public fingerprint, all thirteen
   helper pins, root-catalog hash, image hash and runtime provenance. Check
   package/ABI prerequisites and the packaged Python/OpenSSL verifier. Run
   signature/protocol, first-run/reuse, package and UI regressions offline.
   The old accepted AppImage and helper remain retained, not overwritten.
4. Prepare signed catalog revision1 with reviewed package metadata and a
   proposed 30-day lifetime (the format permits at most90 days). Verify it
   independently from the GUI and root-side code against the same policy.
   Signing, tests and building perform no ALPM transaction, root checkpoint or
   publication. Clock/expiry failures block, rather than being bypassed.
5. Produce the final helper-only deployment sheet with the **actual** hashes,
   fixed paths, backup destinations, exact tool calls and recovery gates for a
   separate explicit installation approval. Unknown future hashes are not
   placeholders that count as deployment approval.

The public metadata URL remains reserved and unpublished. Catalog renewal
must happen before expiry, with a strictly increasing revision even when the
package list is unchanged. Otherwise new installations/updates stop safely;
protected known-version removal remains available. Retain the exact prior
signed envelope and use the publisher's `--previous` check. A publishing
procedure must keep revision history beyond the local root cache.

## Stage 3 — proposed one-time helper replacement

**Not authorized by this preparation.** Applies initially to the locally
reviewed KDE target only, not automatically to a remote/Gamescope machine.
Close all Control Center windows and finish package operations. Refresh only
affected gates: exact old/new payloads, protected parents, no active helper or
package operation/ALPM lock, unused backup/candidate paths, ABI/runtime and
unchanged root policy/cache metadata. Named-process inspection alone is not a
proof that no helper is running; the execution-time gate must establish this
before switching. An existing protected signed-catalog state requires explicit
compatibility review. Never infer its absence from denied cache access or reset
it to enable migration. Stop on any deviation.

Proposed ordered replacement, with independently checked intermediates:

1. Exclusively create a root-owned sibling candidate executor directory.
   Copy its eleven pinned leaves from **sealed, preverified descriptors**
   using fixed system `mkdir`/`install`, root:root0755 for the directory/entry
   and0644 for other leaves. Root does not execute AppImage, user-owned Python,
   a shell or a mutable user-provided file. Verify the complete candidate.
2. Temporarily hold the existing package Polkit policy by a nonoverwriting
   same-parent rename to a name not ending in `.policy`. Verify that its action
   is no longer registered and no invocation is in flight. This neither kills
   an already running helper nor changes other Polkit actions. Keep the normal
   administrative policy; no sudoers/passwordless-rule changes.
3. Rename the complete old executor directory to its reviewed unused sibling
   backup. Move the verified candidate into the now-absent fixed executor path.
   Both moves must be same-filesystem, no-copy/no-overwrite with postchecks;
   no incremental mixing of old and new modules. Hold the policy while the
   path is absent or incomplete. The old directory's bytes/ownership/modes
   and inode are retained for recovery.
4. Independently verify all thirteen active leaves and protected parents,
   including unchanged license/policy bytes. Restore the **identical** policy
   last, then verify the loaded action and unchanged authorization defaults.
   Preserve the complete root0700 cache directory and its contents/inode,
   legacy authorization helper, earlier backups, shared parent and all other
   packages. Do not create/advance signed state as part of migration.
5. Open the exact new AppImage only for a separately approved read-only reuse
   check: recognize the installed helper, no setup prompt or package operation.
   A signed-metadata download test and any package installation/removal remain
   distinct later approvals. No driver activation, Release/Resume, service
   restart, module reload, hardware test or automatic package chain follows.

The existing first-run setup **refuses mismatching/partial helpers**; it is
not an updater and must not be forced into this role by deleting files. This
proposal needs a separately reviewed migration executor/command sheet; it is
not an already implemented or tested privileged replacement operation.

## Failure and recovery

Stop at the first mismatch/error/unknown result. No automatic retry, package
action, recursive deletion or backup cleanup. If the new policy has been
restored, hold it again before any reviewed code recovery. Before any signed
catalog has been accepted, recovery can preserve the candidate separately,
restore the verified complete old executor by nonoverwriting rename and
restore the identical old policy last. Recheck all old pins and cache inode.
Keep both AppImages and all retained backup directories.

After a signed catalog has been checkpointed, **do not blindly reinstall an
old helper lacking rollback protection or rewind/delete protected state**.
Keep operations blocked until an explicit state-aware recovery is reviewed.
Cache corruption, an existing incompatible state, policy-registration failure,
unexpected ownership, concurrent work or incomplete copy requires its own
diagnosis. An offline fixture passing is not real migration acceptance.

## Later publication and scope

Publishing the new AppImage/public key and signed metadata needs its own
release approval, privacy/source/runtime audit and public-byte verification.
The endpoint is not enabled by this proposal. Once compatible public trust
is deployed, later **driver package versions** can use signed catalogs with
the same AppImage/helper. Changes to the helper/application protocol or trust
anchor may still require a new AppImage and reviewed helper migration.
Checking metadata does not install; every package action retains its explicit
selection, plan and administrative permission. No unattended updates or
permanent root GUI are introduced.

See [signed update protocol and offline tests](CONTROL_CENTER_RELEASE_UPDATES.md).
Current acceptance covers production key creation/public binding and offline
build checks only. Encrypted backup, migration implementation/testing/approval,
deployment, public channel and actual signed-package acceptance remain pending.
