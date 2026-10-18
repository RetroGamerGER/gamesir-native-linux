# Public pre-alpha release audit

## Unreleased SDL/Eden addition — 18 October 2026

The opt-in 109c gyro input path is prepared and tested offline after the
maintainer accepted the diagnostic response. It is not installed, hardware-
validated in SDL/Eden, tagged or pushed. Existing release checkpoints below
retain their historical scope. [New integration and limitations](SDL_EDEN_GYRO.md),
[bounded offline result](sdl-eden-gyro-validation.json). No accelerometer axis
claim, universal games support or default runtime activation is added.


Current candidate `v0.1.0-pre-alpha.2`, 2026-10-17: the corrected optional
bridge `0.1.0.alpha1-2` passed one approved Forza Horizon 6 / Xodus Nexus run.
Both triggers were felt with pauses/restarts; normal inputs and grip rumble
remained usable and normal exit left the triggers quiet. The relay recorded
171 play/498 stop acceptances, no error, and clean producer EOF. Native
ownership and service remained unchanged. [Evidence and limits](TRIGGER_BRIDGE.md#corrected-integrated-forza-test--limited-acceptance-passed).

The maintainer's conditional authorization for the next push/release now
applies, subject to final source/history/artifact checks. The release remains
source-only and PRE-ALPHA: core `0.1.0.alpha3-6`, Steam `0.1.0.alpha2-1`,
Gamescope `0.1.0.alpha1-1`, bridge `0.1.0.alpha1-2`. Private binary builds,
logs, original captures and development history are excluded. Other bridge
games/runtimes, reconnect, suspend, crashes and multiple devices remain open.
No additional live action or gyro calibration is part of publication.

Local candidate, 2026-10-17: core package revision `0.1.0.alpha3-6` adds a
userspace manager reconnect correction. Kernel sources/ABI, haptics broker,
paddles and IMU calibration are unchanged. Offline regressions and an update
plan are recorded in [MANAGER_RECONNECT_FIX.md](MANAGER_RECONNECT_FIX.md);
installation, activation, hardware acceptance and publication remain separate.

Update 2026-10-17: the sanitized source baseline was published as
`v0.1.0-pre-alpha.1`. The historical preparation audit below retains its
original scope. The new optional [trigger bridge](TRIGGER_BRIDGE.md) is a
subsequent offline-tested change, not part of that tag. It was installed
locally under separate authorization; its integrated hardware acceptance is
still pending. Its separate provenance check precedes source integration;
publication remains conditional on the approved test and release review.
The optional package does not change kernel, manager, paddle or IMU sources.

Earlier local test on 2026-10-17: the first installed integrated Forza/Xodus
trial failed trigger acceptance, although normal input and grip rumble worked.
The relay disappeared before its first recorded output. A manager-busy versus
identity-loss defect was reproduced offline and a correction is being prepared;
the live exit cause was not conclusively logged. This does not invalidate the
older separate bridge result, and that older result cannot validate the new
integration. The maintainer's condition for the next push/release was
**not met at that checkpoint**. The corrected-package test above now records its real outcome;
see [the failed trial and correction](TRIGGER_BRIDGE.md#first-integrated-forza-test--trigger-acceptance-failed).

Date: 2026-10-16. This is a local readiness assessment, not a published release
or permission to install, activate, test hardware, create a remote, or push.
The licensing baseline is commit `6abb83e`, following the paused-calibration
checkpoint `3a3ac91`. Package revisions identify different tested snapshots;
an older hardware result is not a new test of the final release artifacts.

**Decision:** the project can be prepared for a first public **PRE-ALPHA**
with the limitations below. It is not ready to be described as stable,
production-ready, universally compatible, or fully calibrated. Final release
approval and the mandatory publication checks remain open.

## Required public warning

The README must prominently begin with **“⚠️ WARNING: EXPERIMENTAL SOFTWARE”**
and identify the development stage as **PRE-ALPHA**. The warning must cover
crashes/freezes, boot failures, USB/HID conflicts, data loss, and kernel-update
breakage; limit use to experienced users, advise against production-critical
systems, and state own-risk use without guarantees. The complete warning is
maintained in the [README](../README.md). Seven public-documentation tests
now check the complete wording, its position immediately after the title,
both Project Goals sentences, reference-only acknowledgements, links,
licensing and portable public instructions. This is not a hardware safety
certification.

## Feature and support matrix

“Hardware-confirmed” means the particular recorded test passed. It does not
extend that result to every controller, firmware, kernel, or session type.

| Area | Evidence currently available | Public pre-alpha boundary |
| --- | --- | --- |
| Standard G7 Pro, 2.4-GHz dongle, `3537:100a → 109c` | Autonomous bootstrap, native input and IMU reception, controlled return to xpad; later automatic startup confirmed | Supported experimental path; no claim for Bluetooth, wired operation, or unknown PIDs |
| ZZZ edition, `3537:105e` | One 180-second direct-start/input/IMU test and return to xpad; 13 of 15 target button codes actually exercised | Experimental variant in the same driver; complete paddle, motor, Steam, reconnect and long-run validation still missing |
| Garuda KDE | Real installation/DKMS builds, native inputs, one radio reconnect, normal KDE-menu Steam startup and independent paddles | Tested configurations only; matching headers/build tools required; no promise for all kernel updates |
| CachyOS Handheld/Gamescope | Real installation, 150-second native input/IMU test, persistent Steam mapping and one controlled PC-boot/controller-on sequence | Evidence applies to that CachyOS session; it is not universal Valve SteamOS or Steam Deck support |
| Normal gamepad inputs | Buttons, D-pad, both sticks and both analog triggers received; full ranges observed | No established long-term drift, latency or polling-rate guarantee |
| L4/R4/L5/R5 | Independent Linux codes 704–707; four independent Steam paddles, combinations and releases confirmed with the optional integration | Steam Input can map their actions; ordinary XInput games do not gain four new native XInput buttons |
| Four physical motors | Twelve native single-motor impulses, including both triggers, felt and stopped while input/IMU continued | Confirms the packet/runtime foundation, not universal four-motor game support |
| Standard game rumble | `FF_RUMBLE` for the two grips, game-controlled duration and renewed short hardware leases implemented and offline tested | No artificial one-second game-effect limit; final current-build application/stop smoke test remains open |
| Independent trigger rumble | Versioned local four-channel broker/API implemented and offline tested | Applications need an explicit adapter; the tested SDL evdev trigger API reports unsupported; no invented Linux FF UAPI |
| IMU | Six changing raw channels observed on both models; experimental acceleration conversion is replaceable | Gyro scale, physical axes/signs and bias are not calibrated; no calibrated SDL/Eden claim |
| Coherent IIO buffer | Implemented, offline-tested, separately installed/registered; last documented buffer state is disabled | No real coherent-buffer capture or known-angle measurement; gyro calibration is paused |
| Firmware and configuration | Static research only | No firmware updater, flashing, bootloader support, or automatic manufacturer-app configuration |

Hardware evidence: [standard startup](HARDWARE_TEST_003.md),
[CachyOS bootstrap](BOOTSTRAP_CACHYOS_FIX.md#revision-4-korrigierter-bootstrap-realtest-bestanden),
[controlled Gamescope boot](STEAM_GAMESCOPE.md#kontrollierter-neustart-am-15-oktober-bestanden),
[KDE Steam persistence](STEAM_INTEGRATION.md#reale-anmeldung-und-normaler-kde-menüstart-bestanden),
[ZZZ test](G7_PRO_VARIANTS.md#vollständiger-zzz-realtest-am-14-oktober-2026),
[native motor comparison](NATIVE_MOTOR_COMPARISON_RESULTS.md),
[local haptics API](HAPTICS_API.md), and
[paused coherent-sensor work](COHERENT_IMU_CALIBRATION.md).
These are dated records; their old machine states and consumed approvals
are not current installation instructions.

## Completed preparatory checks

PASS below describes repository or offline evidence. The clean source-copy
test covers the local preparation tree; it does not certify a future release
commit, running system or untested race.

| Check | Result and scope |
| --- | --- |
| License decision | PASS: own project code/documentation uses GPL-2.0-only; full GPL text and the UAPI Linux-syscall-note exception are present. `MODULE_LICENSE("GPL")` remains valid. |
| Provenance review | PASS within the documented review: own sources compared with saved references, historical own parser preserved; no identified imported implementation blocks. This is not exhaustive legal clearance. |
| Licensing/package regression | PASS at `6abb83e`: 124 source/config files checked, one intentional UAPI exception; 25 DKMS packaging tests cover exact license bytes, modes, archive/staging destinations and missing-license rejection. |
| Current licensing/package regression | PASS for this preparation: 125 source/config files, including the new README test, retain the correct SPDX identifiers; one intentional UAPI exception. All 25 DKMS packaging tests pass with the new public guides in the source/staging allowlist. |
| Public README review | PASS: seven tests verify the exact warning, goals, original-project links, reference-only wording, license links and absence of personal paths/hostnames in the three public entry guides. The historical README remains available in Git; detailed evidence documents are retained. |
| Official reference repositories | PASS: the Deadband and g7ctl repository pages were checked read-only on 2026-10-16 and linked directly. This acknowledgement does not imply participation, collaboration, endorsement or developer support. Fixed provenance references remain in `LICENSING.md`. |
| Full offline suite | PASS for the updated working tree (`build/prealpha-readme-tests.log`) and an isolated copy of all 237 intended source files (`build/prealpha-public-readme-audit/tests.log`). The copy has no `.git`, private `.local` data or pre-existing build products. It is based on `6abb83e` plus this preparation, not a tagged release. |
| Portable installation/removal instructions | Reviewed: matching headers, separate installation/activation, DKMS checks, optional Steam/Gamescope packages, honest USB-identity recovery and guarded removal of retained state are documented in `INSTALLATION.md`. Commands were inspected and syntax-checked, not executed on the running system. |
| Historic repository-content review | Reviewed before `6abb83e`: 91 commits and 946 blobs, with no detected secret, vendor binary or raw-capture payload in the reviewed history. Subsequent changes still require review. |
| Final privacy check through `3e620f3` | NO-GO for unchanged history/tree: personal commit email, home paths and machine labels found. All 93 commits/1,037 blobs and the 237-file tree were inspected; no identified credentials or vendor/raw-capture payloads. Prepare separate sanitized source artifacts; see `PUBLIC_RELEASE_CHECK.md`. |
| Repository destination | No configured remote, release tag or published release at this audit's starting check. No public destination has been invented. |
| Runtime safety changes | The known FF ownership bug and bootstrap/error-reporting defects have targeted regressions and limited follow-up hardware evidence; see the boundaries below. |

The test logs and source-copy inventory are local ignored build outputs, not
public release assets. The source-copy inventory records per-file hashes and
its baseline; final documentation and the repository checksum manifest are
reviewed separately before the local commit. No new hardware result, kernel
module build, live installation or complete live removal is claimed here.

See [licensing and provenance](LICENSING.md) for original license hashes,
upstream source references, preserved historical licenses and redistribution
boundaries. License compatibility does not itself establish upstream acceptance.

## Open publication gates

These checks must be completed against the selected final source commit
before calling an archive or tag the public pre-alpha release.

| Gate | Required completion |
| --- | --- |
| Clean public source copy | Completed for this local preparation: the full default offline suite passes in the 237-file copy. Freeze and recheck the selected publication commit and any offered artifacts; optional private-capture/SDL checks remain separate. |
| Final source/package alignment | Rebuild any offered source or Arch/DKMS packages from the chosen release commit; verify contents, complete corresponding sources, license notices and SHA256 checksums. Existing historical packages are not automatically releasable. |
| Public content and history | The original history/tree is blocked by personal metadata and historical paths. A separately sanitized source snapshot can be reviewed independently; no existing history is approved for push. Preserve private originals and obtain a separate history/identity decision. |
| Current documentation | Completed for this preparation: exact warning, goals, reference-only thanks, feature/support boundaries, recovery/removal and known issues reviewed and regression-tested. Review again if the selected release tree changes. |
| Owner approval | Obtain explicit approval of the repository destination, visibility and release scope before creating a public repository, remote, tag, upload or push. |

## Open validation and claims

The following are open engineering checks, not already passed release tests.
A limited public pre-alpha may leave them open **only with the corresponding
limits explicit**; stable support or the untested feature must not be claimed.

| Open check | Present boundary |
| --- | --- |
| Current-build game force feedback | Verify longer grip effects, expiry, explicit stop, application exit and independent channel behavior. Older manual motor pulses and fake ioctls do not close this application chain. |
| Suspend/resume and resets | PM code and simulated regressions exist; real suspend/resume reliability is not established. |
| Hotplug, repeated radio reconnect and multiple dongles | Limited reconnect/boot evidence exists; repeated cycles, rapid same-port replacement, hub changes and concurrent controllers are not generally validated. |
| Additional kernels/distributions | DKMS is intended to rebuild for matching installed headers; untested generic kernels, ABI changes, signing/Secure Boot and other distributions remain unsupported claims. |
| Full deinstallation on hardware | Packaging guards and recovery paths are offline-tested, with controlled release/update records; a complete final-version live package-removal and functional fallback acceptance is not established. |
| Initial `109c` at boot | The manager deliberately does not adopt an unrelated pre-existing `109c` instance. Boot with an already-on controller and no fresh `100a` enumeration needs a separate test/solution. |
| Precise gyro/SDL sensors | Calibration remains on ice. No range may be selected from the five diagnostic hypotheses and no gyro factor may be derived from 8192 LSB/g. |

## Known safety limits and failure history

The previous FF-private ownership defect was a confirmed use-after-free/
double-free risk. The fix and targeted negative controls are documented in
[FF_LIFETIME_FIX.md](FF_LIFETIME_FIX.md). One later controlled radio cycle
passed. This does not prove that every earlier freeze had the same cause,
that graphics-path failures were unrelated, or that all races are removed.
The original [freeze investigation](SYSTEM_FREEZE_20261014.md) remains intact.

The initial userspace xpad-unbind and fallback bind are not fully atomic
against extremely rapid replacement at the same port. Kernel instance checks
prevent an unchecked bootstrap but cannot erase that userspace timing window.
See [ownership and runtime limits](ALPHA_RUNTIME.md). A still-`109c` device
bound to xpad is not proof of a successful mode return to `100a`; failed
recovery must be reported honestly and may need the documented manual path.

The earlier non-felt 400-ms left-grip pulse was not causally explained by the
later successful 1-second comparison. Unknown successful type-`0x03` reports
remain distinct from USB transfer errors. Neither finding permits an
unqualified claim of perfect rumble or complete protocol coverage.

No installation, service/module/binding change, USB command, new recording,
gyro measurement, public upload or push is authorized by this audit.
