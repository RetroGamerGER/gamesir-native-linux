# Current AppImage publication check — 21 October 2026

The maintainer authorizes the completed Control Center app and source/metadata
push before driver diagnosis. Preserve private development history and the
existing public main ancestry: publish one reviewed final-tree snapshot.
Current public tree and both project-source companion archives were scanned
for private home paths, machine/network identifiers and private key/token
patterns; no such findings were identified. Only the public release trust
anchor and the public GitHub noreply identity are included. Third-party
source author/license notices must remain. Raw evidence, custody/backup paths,
private keys and firmware remain outside the publication. This is a bounded
content review, not a guarantee against every possible disclosure.

[Distribution/source closure and exact evidence](CONTROL_CENTER_DISTRIBUTION.md)
cover the final AppImage and companion sources. Driver/kernel/source byte
changes are not part of this app publication. Older checks below retain their
historical scope.

# PRE-ALPHA publication check and artifact policy

Historical initial preparation: 2026-10-16. The counts, versions and pending
decisions below describe that checkpoint, not the present public repository.
The sanitized history was subsequently published as `v0.1.0-pre-alpha.1`.
For candidate `v0.1.0-pre-alpha.3`, see the [current release audit](RELEASE_AUDIT.md):
review all newly reachable public commits/blobs and the exact final source
commit, regenerate source-only assets and checksums, and test the frozen
export. Include the separately reviewed optional trigger-bridge source.
Never upload the private original history, captures, installed inventories,
local build logs or binary-package build metadata. Historical export manifests
remain historical; each release has its own exact artifact manifest.
Publication approval never authorizes system installation or hardware work.

## Current public-history checkpoint — 19 October 2026

The [latest audit](RELEASE_AUDIT.md#final-unpublished-source-check--19-october-2026)
checks the unpublished descendants of the already public repository, including
intermediate file contents and commit metadata. This is a different history
from the private original described below. No private original commits are to
be pushed. The current audit requests a new, explicit permission before any
source push; historical conditional approvals below are not current authority.
The Eden/Gamescope workaround remains a tested manual compatibility note.

## Historical private-source privacy decision

The complete reachable history through `3e620f3` was inspected: 93 commits,
1,515 reachable objects including 1,037 distinct file blobs, 18,670,815 blob
bytes and 237 distinct file paths. All author/committer records were checked
in addition to blob contents and filenames.

**The existing development history is NOT approved for publication.** All
93 commits contain a personal author/committer email address; five subjects
contain private machine references. Historical documents include personal
names, local home paths and host labels. A clean current README does not
remove information from earlier commits. No history was rewritten, deleted,
uploaded or placed in the release artifacts.

The current 237-file tree was also inspected (3,379,063 bytes). No real
credential, private key, authentication URL, email, MAC address, network IP,
USB serial or UID value was identified in its contents. Version numbers,
documented password prompts, synthetic session tokens and privacy-detection
expressions were reviewed as false positives. This is a bounded inspection,
not a guarantee that no possible sensitive information exists.

No raw captures, manufacturer executables, firmware, installed drivers,
ELF/PE files or files larger than 1 MiB were found among the tracked files.
The sole binary is the project's own IMU statistics plot: no private labels
or EXIF were identified, only a plotting-software metadata field. Source
authors, public upstream references and required license notices must remain
intact; the module's existing author attribution is intentionally retained.

## Conservative public-source preparation

Prepare a separate source snapshot without `.git`, ignored files, local
evidence, build logs, installed-package inventories or original captures.
Keep the development repository and original evidence unchanged locally.

For that snapshot only:

- Replace the private development-session `AGENTS.md` with public contributor
  rules containing the same project, license and hardware-safety boundaries.
- Replace private home/workspace paths and machine labels with neutral
  placeholders. Anonymize personal tester references in historical prose.
- Generalize the synthetic home paths in the guided-test fixture; do not
  change runtime logic, protocol constants, firmware assumptions or guards.
- Preserve historical evidence/source hashes as historical hashes. Record
  transformed file hashes separately and regenerate the snapshot's outer
  checksum manifest. An anonymized report is not the original evidence file.
- Keep all linked documents and package-allowlisted files. Removing historical
  files indiscriminately would break links and package generation.
- Record the original source commit, fixed archive timestamp, transformation
  categories and per-file hashes in public export metadata, without copying
  private replacement values or commit identities.

Do not represent this snapshot as an anonymization of the Git history.
Publishing the existing history, rewriting it, creating a replacement public
history or selecting a public author identity requires a separate decision.

## Historical first-release PRE-ALPHA artifacts

The intended source release candidate contains:

1. The complete sanitized development source, including tests, GPL-v2 text,
   UAPI exception and provenance documentation.
2. The existing DKMS build-source archive and PKGBUILD (`0.1.0.alpha3-5`).
3. The optional Steam build-source archive and PKGBUILD (`0.1.0.alpha2-1`).
4. The optional CachyOS Gamescope build-source archive and PKGBUILD
   (`0.1.0.alpha1-1`).
5. PRE-ALPHA release notes, an exact artifact inventory and SHA256 checksums.

All three component archives must be generated from the sanitized source,
not directly from the private working tree. Retaining old package versions
does not make old local binaries match the candidate. The collection is
explicitly PRE-ALPHA even though internal module versions contain `alpha`.
No tag is created by this preparation.

Unprivileged staging can verify installed paths without installing anything.
Run the full default offline suite in the sanitized source and compare two
independent generations of each component archive. Check license bytes,
links, modes, ownership metadata, archive paths, private data and checksums.

No Arch binary packages are offered by this source-only preparation.
Ordinary `makepkg` embeds local build/start paths, packager metadata and the
installed-package inventory in `.BUILDINFO`; these require a controlled
neutral build environment before a binary release. In addition, the current
build host lacks the optional Gamescope runtime dependencies required by its
normal dependency check. Do not install dependencies or use `--nodeps` as
part of this check. Source recipes remain buildable on a prepared target.

## Build-environment warning found during preparation

The first sanitized snapshot passed the full offline suite and produced a
module for `7.2.11-1-garuda`, but the local build helper then raised an
assertion on Kbuild's compiler-metadata warning: headers report Clang 23.1.1,
the available compiler is Clang 23.1.3. Kbuild itself returned success. This
must not be described as a warning-free or hardware-validated build.

The narrow offline correction recognizes only the complete known Kbuild
message with both compiler-version lines and matching compiler family. It
records an environment warning separately in the JSON report. Incomplete,
unexpected or additional warnings still fail the helper; Kbuild failure,
module identity and alias checks are preserved. `W=1` and `-Werror` remain
enabled. This is a build-reporting change, not a loaded-driver change.

## Historical approval and validation boundaries

The artifact inventory must record the actual source commit and results;
the source-only candidate is not an installed or hardware-tested build.
Any module build is offline and does not replace the loaded driver. Gyro
calibration remains paused. Existing limits for game-trigger integration,
ZZZ coverage, suspend/resume and repeated reconnect remain unchanged.

Before publication, review the exact candidate and choose repository
destination, visibility, history strategy and public contributor identity.
There is no permission to create a remote, tag, upload or push. The original
history remains a publication blocker even if the sanitized artifacts pass.

See [release audit](RELEASE_AUDIT.md), [installation/removal](INSTALLATION.md)
and [licensing/provenance](LICENSING.md).
