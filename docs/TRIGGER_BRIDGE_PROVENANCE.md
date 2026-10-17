# Trigger bridge: provenance and licensing review

Review date: 2026-10-17. This review precedes the selective, offline integration
of the experimental Forza trigger bridge. It does not authorize installation,
game execution, hardware access, publication or a push. Gyroscope calibration
remains paused. See the project's [licensing baseline](LICENSING.md).

## Decision and its limits

The maintainer identifies the bridge as work developed for this project in a
separate Codex session and explicitly authorizes its integration into GameSir
Native Linux. The existing project license decision is **GPL-2.0-only** for
project-owned kernel code, userspace code, tests, tools and documentation. The
reviewed project-owned bridge contributions are integrated on that basis, with
SPDX identifiers and the root [COPYING](../COPYING) applying to the integrated
sources. The existing UAPI Linux-syscall-note exception is unchanged.

The separate bridge snapshot contains no standalone license text or SPDX
identifiers. Its Git metadata records seven locally generated commits; this is
development provenance, not an independent certificate of authorship, ownership
or permission from every possible third party. No third-party implementation
copy was identified in the bounded comparison and manual review below. This is
not exhaustive legal clearance, a clean-room claim or evidence that any
external project's developers participated in or endorsed this work. If a
third-party implementation block is later identified, preserve its notices and
resolve its license before publication; the project's license choice cannot
relicense someone else's contribution.

No unreviewed bridge history is merged or cherry-picked. Only reviewed source
changes are integrated. Original local history and evidence remain preserved
separately. Game data, proprietary binaries, runtime binaries, launcher account
configuration, private paths, captured logs and local authorization state are
not integration inputs or public fixtures.

## Reviewed source history

The original source snapshot is commit
`3a78390bf68824d4c586583ca7bd9d5922bf797a`, with seven commits in chronological
order:

| Commit | Recorded development step |
| --- | --- |
| `8bfad961efd8c43f1c2127d8340ecdd68aab7463` | Design and protection boundaries |
| `bd85744c080b3ede31c70814b623d5e53081064d` | SDL2 interception and bounded trigger relay |
| `2d9a58ee36cdf085d152f082b785d51dd7beaf4b` | Reversible per-game launcher integration and broker-access check |
| `94c6c43702b365e2236b52006ee0667fb736244b` | Per-launch raw-USB-open exclusion while retaining the native ownership guard |
| `40786273783504068f11a8b29292eb56f2b51c9b` | RT-only gain following the first real-game result |
| `70440a8ed49836c2a55741e7b7811cc88c8e62c2` | Human confirmation of both triggers and remaining limits |
| `3a78390bf68824d4c586583ca7bd9d5922bf797a` | Stop/expiry/restart regression and clarification of game-generated zero states |

The first source addition introduces the bridge-specific forwarding logic,
launcher and synthetic tests. Later changes add the broker client integration,
USB exclusion and gain behavior. No tracked vendor source archive or imported
external implementation tree occurs in these commits. Missing notices in the
old snapshot are not treated as proof that all code is original.

### Original file hashes

These SHA256 values identify the **original snapshot**, before SPDX additions,
renaming, generalized selection or safety corrections. They are not hashes of
the newly integrated versions and must not be updated to disguise that
distinction.

| Original tracked path | SHA256 |
| --- | --- |
| `Makefile` | `4621534523bbb79805c0c5e060f4b28935ecd30c476a8e8a179b02ba582b30a0` |
| `src/launch.py` | `96bd262dd12833c29ff5e9ecae1b97933237813c6c0bfaa21dadc2997131e09f` |
| `src/nexus_config.py` | `b0a55aca75f1a7bd63da0a1d7fb87d463860f6f0cdffc9e264f1135e8293dd7e` |
| `src/relay.py` | `44eda4a3beee2f243cf5a9c07c208f0ef96cc22514c539db9943a69fcaa23ac5` |
| `src/sdl_bridge.c` | `7df7091e18d720c22e02fe05f8240fc73b9c08d5a16e582b51507ed683440ea0` |
| `tests/test_bridge.py` | `300fb36df4c0b8850c8cb59f90e01fac30c69b3deaa6353f39bab0c3275a7875` |
| `tests/test_integration.py` | `905bfa412c5d0adf3401f2b397a6be041a990cc4315907b1590bd993351ef13a` |
| `tests/test_lease.py` | `7151556eeaadd0b5c2e91f13c1f0d48b4136f5a7152b24cef7a4b785e3c884a4` |

## External references and dependencies

The following locally saved references were read without executing an
application, initializing SDL, opening a device or fetching network content.
Their contents are not vendored with the bridge. URLs identify the upstream
projects; the hashes below identify the exact saved files actually compared.

| Reference / dependency | Role and observed license boundary |
| --- | --- |
| [Wine / Proton](https://github.com/ValveSoftware/wine), `winebus.sys/bus_sdl.c` in saved runtime source `11.0-20261015-g132d7a88` | Reference for explicit SDL2-handle symbol resolution and trigger ABI. File notice: LGPL-2.1-or-later, including CodeWeavers attribution. No Wine implementation block identified as copied. The Wine runtime and its many dependencies are not redistributed here. |
| [SDL](https://github.com/libsdl-org/SDL), saved SDL2 and SDL3 Linux joystick sources | API and backend reference, with zlib-style notices in the compared files. The bridge does not supply a modified SDL library. SDL3 has different API conventions and is not implicitly supported by an SDL2 hook. |
| [Xodus Nexus](https://github.com/domsvoboda/xodus-nexus), saved `game-wrapper.ts`, `proton.ts`, `index.ts` | Reference for launcher behavior. Saved project license: MIT, copyright Xodus Nexus contributors. No copied TypeScript implementation identified. If source is copied in a later integration, preserve the MIT notice. |
| [libusb](https://libusb.info), installed public `libusb.h` | Build-time declarations and dynamically resolved functions. Header notice: LGPL-2.1-or-later. The header and library are system dependencies, not bundled or relabeled GPL-2.0-only. |
| System C library, dynamic-loader and pthread interfaces; Python standard library | External build/runtime APIs. No library source or runtime binary is included. Their own license conditions remain applicable. |
| Existing GameSir Native Linux broker/client | Project-owned GPL-2.0-only code, reused through the versioned local API. It is not replaced by a second USB owner. |

The original adapter declares small SDL2 ABI function-pointer types and uses
libusb's installed header. Synthetic tests implement minimal fake functions
for linkage and transport checks. API names, ABI declarations and matching
protocol facts are distinguished from third-party implementation bodies. No
game, launcher, Wine, SDL or libusb executable is included as a fixture.

### Exact compared reference hashes

| Saved reference | SHA256 |
| --- | --- |
| Runtime Wine `winebus.sys/bus_sdl.c` | `d2e0a69c1ebdd9f49fb5d9c01ab878e0b26f4ab92121e02c741f344b25eb3be1` |
| SDL2 `src/joystick/linux/SDL_sysjoystick.c` | `62ee387eb3cca342a8081fdf7b875e9c5db120b94e91c6abefd88357e4829cda` |
| SDL3 `src/joystick/linux/SDL_sysjoystick.c` | `4c787e35305b959a680c19aedc661e90000259d0f6d2a520a169dc6821067178` |
| Nexus `src/main/game-wrapper.ts` | `c8ea90f9c1787303da1a2f35a7b9c4d73991ae36ab927869a08fb322d0504608` |
| Nexus `src/main/proton.ts` | `697be0cd713d9b054da6de2860d290ac94ad7962d939375f4a054cf843ee4abd` |
| Nexus `src/main/index.ts` | `537447b1e6a95aaf6d6b525768b3f137abdd3d38bff88fb9f4233fe8409d7589` |
| libusb public header | `a61260ab145b051b86df2b0575956f01810190abe2c7df6aca831c33bdc8082c` |

The comparison covered all eight original implementation/build/test files
listed above against the seven saved references. It removed C block comments,
blank lines, comment/preprocessor/import lines and brace-only lines, removed
whitespace, and retained lines of at least 12 characters. It compared windows
of four retained lines containing at least 120 characters. No identical
window was found among 4,050 distinct reference windows. The code, additions,
notices and synthetic fixtures were also read manually. This method can miss
short, rewritten or unprovided material; it supports, rather than proves, the
documented project-owned implementation basis.

## Evidence and publication boundaries

The historical bridge report records 16 offline tests including a synthetic
broker stop/expiry/restart test. Human feedback records both triggers felt in
the tested Forza/Xodus path with RT gain three and LT gain one. Explicit
game-generated zero states were intentional. These records are historical
evidence for the original snapshot, not hardware acceptance of an integrated
build, universal game support or validation of reconnect/suspend behavior.

New offline regression results must identify the integrated source separately.
They must use repository-owned broker/client sources and synthetic backends,
without relying on an installed driver or copied private captures. Packaging,
installation, new game/hardware testing, public release and push remain separate
decisions. Existing third-party notices and the project's public-history
privacy review remain mandatory.
