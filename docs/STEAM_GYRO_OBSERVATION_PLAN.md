# Prepared read-only Steam gyro observation

19 October 2026. **One approved metadata precheck stopped; no cache observation
executed. Identity correction tested offline; a new attempt needs approval.**
This is a one-run diagnostic proposal requiring separate approval. It does
not install anything or change the working driver, Steam configuration,
gyro profile, paddles, rumble or raw IIO path.

## Question and chosen method

Read only SDL's existing gyro cache **inside the Steam process**, rather than
opening another sensor client or attaching a debugger. The observer reads
the sensor-enabled flag and three cached angular velocities in rad/s, plus
the minimum process/device identity metadata. It uses one `/proc/PID/mem`
descriptor opened `O_RDONLY`; it never writes process memory, invokes a
target function, inserts breakpoints, sends signals to Steam or opens an
evdev, IIO, hidraw or USB device. No full memory dump or environment/command
line collection. Root is required where ptrace-style permissions protect
process-memory reads, **without a ptrace attach or process stop**. The corrected
precheck also follows `/proc/PID/map_files/START-END` with `stat` only to verify
the actual backing files of every SDL segment. It never opens those links.
Linux protects this traversal with `CAP_SYS_ADMIN` or `CAP_CHECKPOINT_RESTORE`
in the initial user namespace, in addition to the process access check. The
proposed sudo command supplies the existing elevated context; no capabilities,
permissions or system settings are changed. A denial stops the run, without
falling back to weaker path/hash-only verification.

The available GDB is deliberately not used. Strace/bpftrace/perf were not
found in the current PATH; nothing is installed to work around that.

| Observation | What can be concluded |
| --- | --- |
| Enabled is false while the gyro page is open | SDL's gyro remains disabled at the sampled instants. This does not identify who disabled it or whether a very short enable occurred between samples. |
| Enabled and changing, nonzero cached velocities during movement | Gyro data has reached SDL inside Steam. If the UI stays zero, investigate the path after this cache: event handling, filtering, selected controller and UI. This alone does not prove an intentional discard or a particular calibration defect. |
| Enabled but unchanged/zero cache despite reported movement | The gap remains at or before the cache; lack of source events, background filtering and sampling limitations are not distinguished by this result. |
| Sensor FD present or absent | Context only. An open FD is not proof of a successful read; a snapshot can miss short opens. |
| Version, instance or metadata guard fails | Stop without adopting another device/process or changing configuration. No motion conclusion. |

The observer samples at approximately 10 Hz. It is **not** a lossless evdev
capture, syscall trace, IMU polling-rate measurement, calibration or end-to-end
game acceptance. Times are host observation timestamps, not the controller's
sample timestamps. It does not trace Steam's downstream discard decision.

## Exact supported layout and offline evidence

Only the reviewed `ubuntu12_32/libSDL3.so.0` is accepted: 3,911,164 bytes,
SHA256 `770801484962a75780b8eebed5e16b4f4735c1dbf422445af48764cff415ea97`.
Different Steam/SDL updates, 64-bit variants and Flatpak are stopped, not
guessed. This is a private, version-specific diagnostic, not a new runtime ABI.

The relative load base comes from the mapped file's offset-zero segment.
The pathname, open file descriptor and kernel `map_files` aliases must have
the same stat device/inode, mode, size and modification/change timestamps.
Hash and little-endian ELF32 are checked on that single open regular file;
identity is checked before and after the bounded read. All SDL mapping rows
are pinned, and their backing-file metadata is checked again each sample.
The `maps` device field is compared only within that view, never directly to
`stat.st_dev`. Static findings:

- The public `SDL_GetJoystickFromID` dynamic dispatch slot is at `0x3aadec`;
  its initialized local implementation is at `0x221030`. The observer verifies
  that pointer before following data. The implementation at `0x221054` loads
  the joystick-list head from GOT `0x3a869c + 0xb364 = 0x3b3a00`.
- Instance ID is at object offset `0`; device-path pointer at `8`; linked-list
  successor at `0x100`. The path getter's load is at `0x2212fb`.
- Sensor count/enabled-count/pointer are at `0x58/0x5c/0x60`. The sensor getter
  at `0x220d50` searches 24-byte entries and copies three floats from offset
  `12`. Type is at `0`, enabled byte at `4`; the enable path writes that byte
  at `0x220a0c`.

`--check-steam-layout` in the existing device-free test runner verifies these
offsets against **public SDL getters and known synthetic sensor values** in
the exact hashed ELF32 library. Seven scenarios pass, including the pointer,
device-path, count, enabled-state and value comparison. The target Steam
application is not loaded or executed by this test; no vendor code is copied
into the project. The independent observer unit suite uses fake memory/maps.

```sh
python -B tests/test_steam_gyro_observe.py
python -B tests/run_sdl_sensor_test.py \
  --sdl3-library /path/to/Steam/ubuntu12_32/libSDL3.so.0 \
  --check-steam-layout
```

The private offline layout report is under
`build/results/sdl-validation/sequence-v2/sdl3-770801484962a757/cache-layout/`.
[Portable offline evidence and source hashes](steam-gyro-observation-offline.json).
No live cache observation has been performed to validate the diagnostic itself.

## First precheck and offline identity correction

The approved precheck exited 2 at `Mapped/file identity differs`; it never
opened process memory and the observation command was not started. The
original private log and checksum remain intact. Its SDL size/hash/ELF checks
had passed, but it did not log which device/inode component differed. Thus
the log alone cannot establish that Steam held a replaced library.

An independent offline reproduction created and read-only-mapped **our own
synthetic file** on the local Btrfs filesystem. Its `stat.st_dev` differed
from its `/proc/self/maps` device while the inode matched. The old predicate
rejected that valid mapping. This proves a defect in the comparison and is
a plausible explanation of the precheck failure, not a retrospective proof
of the exact Steam metadata. No Steam process or controller was inspected
during this reproduction.

The fix compares stat metadata to stat metadata through each kernel-backed
`map_files` alias. Merely accepting a different map device, or comparing only
inode and hash, would not safely distinguish files in different subvolumes.
The new checker rejects a different stat device even with the same inode,
and rejects a different inode even with identical content. It detects file
replacement/modification during hashing and all SDL segment changes, not
only a changed load base. Unknown metadata remains a stop condition.

41 observer regressions pass with synthetic files/maps, including Btrfs-style
device differences, ordinary matching devices, cross-subvolume collisions,
replacements, denied/missing aliases, stale segments, changed ABI/hash and
the local-GO/no-memory-open barriers. One test maps synthetic bytes in its
own process; its `map_files` aliases remain fake. The unprivileged direct
`stat` of an own-process kernel alias returned EPERM in the offline probe.
Therefore real elevated traversal is **pending the next approved precheck**;
it is not claimed as already validated against Steam. No sudo was used for
this correction, no Steam files were changed, and no library was executed.

Reference consulted offline: installed Linux man-pages 6.19,
`proc_pid_map_files(5)` and `proc_pid_maps(5)`. They document the aliases,
map fields and access requirements; no text/code was imported into this
GPL-2.0-only tool. No network access was used.

## Prerequisites and one-run sequence

1. Steam is already running normally. Games, Eden and Deadband are closed;
   the one standard G7 Pro stays connected, with its native gamepad and motion
   node. No reconnect, new bootstrap, calibration or settings changes.
2. Obtain fresh permission for the corrected helper, then run its metadata
   precheck. It requires exactly one user-owned
   32-bit Steam process and one paired `3537:109c` GameSir at native IF0. It
   reads sysfs/proc metadata, node `stat` and the SDL `map_files` alias metadata,
   but **does not open process memory**. Missing alias permissions stop it.
3. Only after that succeeds, run the separately approved observer once. It
   repeats the checks, then waits at most 120 seconds for local `GO` (case
   insensitive). Nothing is attached to or changed in Steam while waiting.
4. After GO, revalidate the same process/controller/library, then observe for
   70 seconds: **30 s preparation**, **10 s rest**, **20 s slow movement**,
   **10 s setting down**. Open Steam's existing gyro page during preparation;
   do not press Calibrate. Any comfortable direction is fine; no exact angles.
   Cues appear in the terminal and output log. Keep the terminal visible or
   wait for the assistant's corresponding cue before moving.
5. Close the read-only descriptor, verify unchanged process/controller and
   library, write completion status, then stop. Confirm the Steam display and
   ordinary controller function manually. No automatic second observation.

Only decoded gyro samples, activation state, SDL instance ID, phases, timing,
target FD counts and a small completion/error record are saved. Other SDL
joystick paths may be examined briefly to locate the target, but are not
logged; list traversal is bounded to 16 objects. Sensor reads are bounded to
eight entries and four MiB overall, each individual read at most 256 bytes.
Double reads detect concurrent updates; inconsistent value samples are marked
and omitted. Three consecutive or more than 20 inconsistent samples stop the
run. This is not a lock-based atomic snapshot or a permission to follow new
instances. Any other metadata/identity error stops immediately.

## Commands proposed for approval — do not run automatically

Run in a Bash terminal as the desktop user, from the reviewed repository.
Private output is persistent and ignored by Git. No automatic cleanup.

```sh
set -o pipefail
umask 077
mkdir -p build/results
run_dir=$(mktemp -d "$PWD/build/results/steam-gyro-observe-XXXXXXXX")
observer="$PWD/tools/sdl/steam_gyro_observe.py"

# Approved step 1: metadata only; no /proc/PID/mem open.
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A \
  /usr/bin/timeout --signal=TERM --kill-after=2s 30s \
  /usr/bin/python3 -I -B "$observer" --precheck \
  | tee "$run_dir/precheck.jsonl"
```

If that command exits nonzero or reports `stopped`, **do not proceed**.
Only after a successful precheck and explicit observation approval:

```sh
# Approved step 2: one read-only cache observation after local GO.
SUDO_ASKPASS=/usr/bin/ksshaskpass /usr/bin/sudo -A \
  /usr/bin/timeout --signal=TERM --kill-after=2s 210s \
  /usr/bin/python3 -I -B "$observer" --observe \
  | tee "$run_dir/observation.jsonl"

# Save/check even an incomplete log; success requires a complete event and exit 0.
sha256sum "$run_dir/precheck.jsonl" "$run_dir/observation.jsonl" \
  > "$run_dir/SHA256SUMS"
sha256sum -c "$run_dir/SHA256SUMS"
```

The external deadlines terminate **only the diagnostic**, including a stuck
GO wait; Steam is not its child and receives no signal from this helper.
Ctrl+C or closing the diagnostic window aborts; no application is restarted
or repaired. Password entry stays in ksshaskpass; no password is logged.
There is no module, manager, service, USB, IIO-buffer or Steam-setting command.
The observer's exit status must be retained immediately when executing via a
tool; the later checksum command is not an acceptance test.

Unexpected data, version/library change, multiple candidates, permission
denial, device/process replacement or target exit means **stop and report**.
No fallback to GDB, breakpoint injection, another PID or additional privileges.
If results are inconclusive, propose a separate next step; do not equate
unchanged cache values with a proved driver fault.
