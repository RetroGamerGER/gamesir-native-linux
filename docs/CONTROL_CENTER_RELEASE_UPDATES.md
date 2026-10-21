# Signed driver updates without replacing the Control Center

**Current distribution checkpoint (21 October 2026):** the reviewed Garuda
x86_64/glibc2.44 alpha1 build, corresponding sources, signed revision1 and
publication scope are documented in [the distribution review](CONTROL_CENTER_DISTRIBUTION.md).
Older phase entries below retain their historical dates and boundaries.

## Local deployment checkpoint — 21 October 2026

The production-public-key-bound package helper has now been migrated locally
after explicit approval, with successful independent read-only postchecks.
The existing encrypted key backup was reused unchanged. No package action,
driver/Steam change, AppImage launch or network request followed. The signed
metadata channel and final local AppImage have not been published. See the
[handover result and remaining gates](CONTROL_CENTER_HANDOVER.md); normal
end-user setup differs from this maintainer-only legacy migration as described
in the [first-run flow](CONTROL_CENTER_FIRST_RUN.md#what-a-normal-appimage-user-does).

## Historical offline implementation checkpoint

21 October 2026. **Implemented and tested offline; not deployed or published.**
No installed helper, package, driver, service or Steam setting changed. After
later explicit approval, a production key and public-key-bound local build were
created; [key/build evidence and remaining migration gates](CONTROL_CENTER_SIGNING_PROVISIONING.md).
Generic source defaults contain no update key, so normal unbound builds do not
silently enable this trust path or perform network I/O. Only the explicitly
reviewed production profile embeds the new public policy; nothing is deployed.

## Stable trust, changing releases

The reviewed AppImage and protected root helper share a fixed public-key policy
in their initial `REVIEWED_PACKAGES.json`. The policy, helper hashes and bootstrap
catalog stay unchanged across compatible driver releases. Each new release gets
its own immutable package URLs, hashes and metadata in a signed catalog. The
new package list is **not** written over the installed trust anchor.

Both sides independently verify Ed25519 with the existing system OpenSSL
executable. No handwritten signature primitives, private key, shell, user
configuration or downloaded executable is used for verification. Exact signed
bytes and their signature are passed through sealed anonymous files; OpenSSL's
configuration/provider environment is fixed. ALPM's native version comparator
runs without opening a package database. Root never performs network I/O.
The one-time deployed helper/profile must be reviewed with the intended public
key and installed system OpenSSL/ALPM prerequisites. It is not changed here.
The subsequent [production-key and helper-migration approval proposal](CONTROL_CENTER_SIGNING_PROVISIONING.md)
records the read-only installed-helper checkpoint, completed private-key
creation/public-anchor build and proposed replacement/recovery boundaries.
The installed helper and trust anchor remain unchanged.

## Format and signing

A root review may opt in with this additional field (placeholders are not keys):

```json
{"updates":{"schema":1,"minimum_revision":1,"keys":[
  {"id":"SHA256_OF_RAW_PUBLIC_KEY","public_key":"32_BYTE_ED25519_PUBLIC_KEY_AS_LOWERCASE_HEX"}
]}}
```

At most four explicitly reviewed keys are permitted. The key ID must match the
public key. A remote catalog cannot add keys or change this policy. Absence of
`updates` retains the legacy independently pinned package path.

The signed envelope has exactly `schema: 1`, `algorithm: "ed25519"`, `key_id`,
canonical base64 `payload` and a 64-byte lowercase-hex `signature`. Ed25519 signs
`b"GameSir Native Linux signed release catalog v1\x00" + payload_bytes`.
JSON payload bytes are signed as bytes; duplicate fields, nonfinite values,
unknown fields and ambiguous encodings fail. It contains exactly:

- `schema: 1`, repository `RetroGamerGER/gamesir-native-linux`, request
  `protocol: 3`, positive monotonic `revision`, integer `issued_at`/`expires_at`.
- `packages`: all four closed `Review` records, including exact source commit,
  immutable tag, SHA256, size, dependencies, upgrade origins and cleanup guards.
- `installed`: reviewed removal records for the current versions and complete
  previously accepted guard history. Changed/missing historic guards fail.
- `assets`: the closed component/filename list used by the existing downloader.

Envelope/payload bounds are 192/128 KiB. History is bounded at 64 records. All
package/identity/archive/selection/dependency checks remain in force. Same-
version changed bytes and downgrades are rejected using ALPM version ordering;
upgrade origins must be older and independently represented in the history.
Validity is at most 90 days; short validity is preferable. Five minutes of
future clock skew is tolerated. Clock problems or expiry block installations.

The ordinary-user publisher utility accepts an existing externally maintained
Ed25519 DER or PEM key, never generates one and never uploads anything:

```sh
python scripts/sign_release_catalog.py \
  --payload build/reviewed-catalog.json \
  --root-review build/reviewed-root.json \
  --private-key /secure/external/release-key.der \
  --previous build/previous-signed-catalog.json \
  --output build/new-signed-catalog.json
```

Private key: outside this repository, caller-owned regular file, single link,
mode 0600; no symlinks. Encrypted keys/hardware signing are not implemented.
Keys/passphrases are not logged. Existing output is never overwritten. The tool
checks the public key against the reviewed policy, verifies its generated
signature/schema and, with `--previous`, rejects rollback/equivocation before
producing output. Omit `--previous` only for an independently reviewed bootstrap.
An approved working key and explicit public policy now exist locally; encrypted
offline backup and rotation/revocation procedures remain pending. Never use the
public RFC fixture seed as a project key. Retain the exact unpublished revision1
envelope and increment the revision for changed metadata or validity dates.

## User-side flow

The reserved, **not yet published** metadata endpoint is fixed:
`https://raw.githubusercontent.com/RetroGamerGER/gamesir-native-linux/main/updates/pre-alpha.json`.
Only this exact metadata URL and existing strict asset CDN redirects are
accepted. It is a mutable signed metadata file; package/tag assets remain
immutable. No GitHub API/latest lookup or arbitrary URL is trusted.

1. Startup, status refresh and helper setup cause no network request. A policy-
   enabled build exposes **Check driver updates / Treiberupdates prüfen**.
2. The explicit check runs in a worker. Bounded HTTPS, signature, project, key,
   protocol, revision, time, versions, history, index and helper/host checks must
   pass before the candidate replaces the in-memory catalog. Failed/cancelled
   checks create no package plan, authentication or installation. Late results
   cannot resurrect a cancelled check.
3. An ordinary-user mode0700/mode0600 signed metadata cache permits restart and
   offline removal. It is reverified, never root authority. A cancelled in-flight
   check may already have completed a valid cache write; it cannot create a
   confirmation or privileged action. Malformed/unsafe cache is not repaired.
4. A separate component selection downloads and verifies exact packages, then
   refreshes host/helper checks and shows the separate install confirmation.
   Expiry is checked again; a successful update check alone never authenticates.
   A user cache replay cannot bypass the helper's protected revision floor.
5. Signed profiles no longer require a newly pinned kernel string for every
   kernel update: distribution/architecture and fresh matching-header/dependency
   checks remain mandatory. This is not a guarantee of module compatibility.

No production endpoint or keys are enabled by offline fixtures. Real endpoint/
CDN acceptance for signed metadata, protected-key deployment and one-time helper
migration require a later explicit review. Old installed helper bytes/pins stay
unchanged and cannot be silently adopted by a new build.

## Independent helper enforcement

Version-3 requests carry the signed envelope alongside the ordinary exact
plan/package bytes. The helper independently resolves it from its **own**
protected key policy before reading package payloads. Legacy requests cannot
bypass an enabled signed policy for installation. Receipts retain schema 2 and
request/plan binding. There are no supplied commands, executable paths or keys.

Under the existing ALPM lock the executor reconstructs the plan, checks actual
package/guard ownership, re-observes host state and revalidates signature/time/
revision directly before commit. A concurrent newer catalog blocks an older
pending installation. The protected mode0600 state is atomically replaced and
file/directory fsynced in the existing root0700 cache directory. Symlinks,
hardlinks, wrong ownership/modes, malformed state and persistence failures stop.
No signed transaction can execute without this resolver/checkpoint.

State records **accepted catalog metadata**, never package-install success.
The revision floor advances before package commit, so it can remain advanced
when installation later fails. The ordinary verified receipt/postcheck reports
package state separately. A directory-sync failure after replacement can also
leave metadata advanced while package commit is blocked. Do not silently retry,
rewind state or report success in these cases. No cleanup error overwrites the
original persistence/package error.

Previously protected removal approvals remain usable offline after expiry or
with an incorrect clock. Expired, replayed or otherwise unaccepted metadata
cannot grant new cleanup rights. A current valid signed catalog can additionally
review a manually installed project version; this is checkpointed under the
same lock before removal. Actual core cleanup hashes/ownership and dependency/
selection checks still apply. Unreviewed cleanup is never executed.

## Offline acceptance and remaining deployment gates

Tests use an explicitly public RFC Ed25519 fixture, real system OpenSSL and
ALPM comparison, fake HTTPS/host/transport and same-user temporary state only.
They exercise signatures/keys/domain, malformed fields/limits, project/protocol,
clock/expiry, revision replay/equivocation, package downgrade/rebuild, upgrade
origins/guard history, helper verification before payload reads, legacy bypass,
atomic-write races/errors, metadata-versus-package outcome, cached offline
removal, explicit worker/UI checks, DE/EN, cancellation and no authentication.

The end-to-end regression installs fixture version 1, checks version 2, and
updates via independent helper verification **without changing the original
AppImage profile or helper trust anchor**. After restart and expiry, removal
still works without any network call. No actual package operation is involved.

Signature checks and expiry cannot prove that a newer catalog exists before
this installation has seen it. A still-valid first-contact catalog can be
withheld by a network adversary; root's monotonic floor prevents replay only
after acceptance. Key revocation/rotation, history-limit migration and helper/
application protocol changes need a separately reviewed trust update. Recovery
from protected-state corruption is an administrative operation, not an
automatic reset offered by the GUI. Production channel availability, key backup,
real metadata download-only acceptance and eventual installation/hardware tests
are still pending and are not claimed by these offline results.

Implementation tests: 28 signature/protocol/state/publisher/integration cases
and three actual offscreen QML cases are included in the standard test targets.
The broad regression checkpoint additionally covers legacy package/helper and
first-run behavior. Public key provisioning and deployment are separate gates;
an unsigned/default artifact does not expose an enabled update channel.

Implementation checkpoint: **1,628 Python cases/60 groups and 61 QML cases/seven groups**
pass, plus the existing native checks. The 13-file helper/native bridge stages
successfully, and the verifier passes under bundled AppImage Python. No signing
key is enabled in the generic/default profile. See the
[sanitized acceptance record](evidence/CONTROL_CENTER_SIGNED_UPDATES_20261021.json).
The subsequent production-bound build passed67 targeted unit/packaging cases,
three QML cases, four actual packaged smoke lanes and independent actual-key
verification in the staged helper and bundled interpreter. See the
[production build record](evidence/CONTROL_CENTER_PRODUCTION_SIGNING_20261021.json).
