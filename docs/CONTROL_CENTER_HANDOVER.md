# Control Center: encrypted key backup and one-time helper handover

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

## Signed helper migration accepted locally (21 October 2026)

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

## Ownership guard corrected offline; migration-only plan ready (21 October 2026)

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

## Approved handover stopped safely after verified backup (21 October 2026)

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

## Historical offline preparation

21 October 2026. **Complete local preparation and tests; not executed live.**
The maintainer asked for one consolidated approval flow instead of more small
preparation rounds. The final local AppImage, immutable approval plan, encrypted
backup tool, migration and explicit recovery are ready. No real release key was
read/backed up in this preparation, no installed helper changed, no password
dialog or live application opened, and no driver/package/Steam/hardware or
network operation ran. Publication remains separately authorized.

## One approved run, two deliberate secrets

`scripts/control_center_handover.py` prepares a local plan by default. It reads
only staged/public artifacts, checks the whole AppDir manifest, hashes the exact
AppImage, pins maintainer source files and the thirteen old/new helper leaves,
and records the fixed destinations. It does not read the private key, inspect
the live helper, prompt or elevate. Private paths/plans stay outside Git.

After a separate explicit approval of that exact plan SHA256, one normal-user
command can perform these steps in order:

1. Choose a new backup passphrase of at least16 characters, entered twice
   with terminal echo disabled. This is not the Linux administrator password.
   The input comes from `/dev/tty`; no chat, argv, pipe, environment variable
   or application password store. Failure to disable echo stops without
   fallback to ordinary stdin.
2. Create an encrypted backup exclusively at the approved external-to-Git
   destination. Verify the persisted backup by decrypting into anonymous
   memory and matching its Ed25519 public fingerprint. No plaintext recovery
   file is created. Failed/cancelled/unconfirmed backup prevents the root phase.
3. Refresh the passive host/runtime/helper gates and perform the fixed,
   staged helper-only replacement through the KDE administrator-password
   window. All nineteen fixed tool invocations run in the approved sequence;
   no per-file maintainer confirmation or manual command copying is needed.
   The operating system's normal sudo policy controls password prompts;
   exactly one password prompt is not guaranteed. No sudoers/passwordless rule.
4. Verify the installed thirteen-file payload, policy and preserved cache.
   Stop without launching the AppImage, installing packages or activating the
   driver. No automatic retry, rollback or cleanup follows any error.

The private signing key stays outside Git and outside the AppImage. Key custody
is a **maintainer** tool; normal driver users need no signing key or backup
passphrase. Fresh helper installation remains the accepted AppImage first-run
flow. The existing first-run GUI still refuses mismatching/partial helpers;
the migration is not an automatic repair feature.

## Backup format and custody

`scripts/backup_release_key.py` uses system OpenSSL: encrypted PKCS8 DER,
PBES2 AES-256-CBC, PBKDF2-HMAC-SHA256 with600,000 iterations and OpenSSL-generated
salt/IV. It implements no cryptographic primitive. Password/key inputs go via
sealed anonymous descriptors, not arguments or named temporary files. Full
PKCS8 recovery and the known public-key identity check detect a bad passphrase,
corrupt backup or wrong key. This does not claim CBC is authenticated encryption.

Input: existing external caller-owned0600/single-link regular DER key. Output:
external nonrepository path, protected nonsymlink parents, exclusive0600 file,
file/directory fsync and independent readback/recovery check. Never overwrite
an existing file or silently remove a partial output. The key is not regenerated
and the original remains unchanged. Passphrase protection assumes a sufficiently
strong user-selected phrase; no fixed/generated password is stored beside it.

The prepared local encrypted destination is a staging backup, **not proof of
an off-device backup**. After execution, copy the encrypted `.p8` file to
separate offline storage, retain its SHA256/public fingerprint, and store the
passphrase separately. No drive/cloud destination is guessed or accessed.
Public rollout still needs the maintainer's confirmation of that separate copy.
Production backup has not been created under this offline-only request.

## Exact helper transition and safety boundary

`scripts/migrate_control_center_helper.py` and the inert
`tools/control_center/helper_migration.py` implement the previously proposed
[handover boundaries](CONTROL_CENTER_SIGNING_PROVISIONING.md).
The independent legacy manifest is
`packaging/control-center/migration-from-first-run.json`. Only its exact
thirteen-file manually installed helper is eligible. Changed/extra files,
package-owned or unknown ownership, unsafe parents/links/modes, wrong ABI/
distribution, pending package work, inaccessible root process information,
an in-flight executor, or occupied staging/backup paths block. Host snapshots
open no ALPM handle and require no kernel headers/compiler for this helper-only
operation. Protected runtime/session requirements remain in force.

The active executor path remains
`/usr/lib/gamesir-control-center/package-executor`. Fixed sibling paths are:

- `.package-executor-signed-v1`: exclusive root0755 candidate;
- `.package-executor-before-signed-v1`: complete retained old executor;
- `.package-executor-retained-signed-v1`: retained new executor on recovery.

The unchanged package policy is temporarily held at its original path plus
`.before-signed-v1`, which does not end in `.policy`. Its normal `auth_admin`
defaults are restored unchanged. Other authorization actions are untouched.

The exact forward plan contains nineteen sudo-wrapped system tool calls:
three fixed `find` metadata queries, one exclusive `mkdir`, eleven `install`
copies and four no-copy/no-clobber same-filesystem `mv` calls. Queries output
only the presence of the fixed protected `release-catalog.json` name; they
never open cached catalog or receipt contents. Any such state, including a
symlink, blocks legacy migration/recovery rather than being reset/deleted.
The cache's complete directory inode/content, license, legacy helper, earlier
backups and unrelated controllers/packages are preserved.

Every input is verified and sealed before the first privileged call. Root
runs only those fixed system tools, never AppImage/bundled Python/user scripts,
shell code or a mutable user source. An exact command validator rejects all
other argv/source combinations. Withdraw the package policy and establish
executor quiescence before directory switching; preserve the entire old
directory, place the whole new directory, verify, restore identical policy
last. There is no mixed incremental replacement of imported modules.

Recovery is a **separately invoked** `--rollback` against the same approved
plan, not an error handler. It validates old/new/held paths and checks protected
state before restoring old authority. Supported partial stages include policy
held before the old rename, old saved/new not placed, new placed/policy not
restored, and interrupted recovery renames. Retain candidate/new bytes instead
of deleting them. Signed-state acceptance blocks legacy recovery; unknown or
modified state requires diagnosis. Never overwrite or reset the revision floor.

## Final local artifact and acceptance

AppImage SHA256:
`19cacca0bac2ac009749c05065a9d4f81ca050d9aa1beabab72cf4aa508d7ad9`.
The public key and helper pins remain those of the
[approved production-key build](CONTROL_CENTER_SIGNING_PROVISIONING.md).
No catalog revision was re-signed, and existing published packages remain
unchanged. Four complete extract-and-run synthetic AppImage lanes pass;
the actual public-key catalog also verifies under the final bundled Python.

All388 Control Center cases in24 groups pass, including61 actual QML cases.
The38 new cases cover backup/KDF/terminal/no-echo/error paths, real same-user
filesystem migration/recovery, ownership/process/lock/state guards and the
consolidated handover. An additional real-byte fixture round-trip uses the
actual independently retained old payload and the actual new thirteen-file
payload, with zero sudo/root operations and preserved old/cache inodes.
Unchanged AppDir inputs reuse the preceding private-material scan; the only
new payloads are public migration code and the hash-only legacy manifest.

The artifact is ready for the explicitly reviewed **local handover/acceptance**.
It is not a published/release-approved binary. Runtime/source redistribution
audit, off-device encrypted backup confirmation, publishing the signed metadata
channel and actual package acceptance remain explicit publication/test gates.
The current installed helper remains old until the consolidated run is
approved. No reinstall of core/bridge or change to alpha3-16 is implied.

[Sanitized offline acceptance record](evidence/CONTROL_CENTER_HANDOVER_20261021.json).
