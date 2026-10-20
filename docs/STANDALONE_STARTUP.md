# Standalone native startup — revisions 11 to 13

Latest read-only follow-up, 20 October: revision 13 is installed and active,
but first-power-on acceptance fails. Direct `109c` verification times out;
the following `100a` remains suppressed as observed xpad return until another
enumeration. See [diagnosis and evidence limits](REVISION13_FIRST_START.md).
The implementation/preparation statements below are historical checkpoints.

Revision 13 combines the bounded pre-acquisition autoprobe correction with
one captured xpad control-IN query in the explicit `100a` bootstrap. It is a
prepared candidate, not hardware-validated. See the
[revision-13 implementation and acceptance plan](ACQUISITION_AUTOPROBE_FIX.md#revision-13-explicitly-requested-startup-query-integration).
The query does not load or depend on xpad. Direct `109c`/`105e` remain unchanged;
first-error, input readiness and controlled return rules remain in force.
The following revision-12 text describes the preceding implementation.

Revision 12 is an offline correction of two startup gaps found after the
separately installed revision 11. The `100a` path no longer waits for a button
report, and a validated free/xpad-owned `109c` can be acquired and initialized
on that same instance. Revision 12 was subsequently installed on CachyOS.
Its user-led cold boot failed in the manager before acquisition; the offline
[autoprobe correction and xpad-query review](ACQUISITION_AUTOPROBE_FIX.md)
document the follow-up. Hardware acceptance is still incomplete. Earlier
results retain their original version/scope.

Revision 11 removed xpad as a software startup prerequisite. Its user-led
service start/Resume used the optional xpad handoff, and the user reported a
positive [Steam gyro radio reconnect](STEAM_GYRO_HOTPLUG.md#revision-11-user-led-radio-reconnect--19-october-2026).
The subsequent cold boot below still required control input. Neither case
proves cold startup without prior xpad initialization.

## Revision 12: start without a button report

| Initial identity | New offline path |
| --- | --- |
| `100a` | Exact acquisition, one valid passive status check (zero pad packets allowed), then the existing nine transition packets and six native-init packets. The existing settle delay and deadlines remain. |
| `109c` | New scoped `acquire_109c` grant, one direct six-packet native initialization on the same pinned USB object; no identity-switch packets and no correlated-device search. |
| Experimental `105e` | Existing direct initialization retained, with the same instance, proof and edition limits. |

Only the dependency on prior gamepad reports is removed. Passive status must
still be healthy, with matching PID and output/session inactive under `100a`.
The manager's `checking_start` phase replaces the misleading input-wait phase;
old saved `waiting_input` states do not grant a fresh start after daemon loss.
Ready still requires completed initialization, fresh IMU and matching kernel
proof. The existing sensor-readiness/access checks still precede deferred
input publication. Paddles, gyro/acceleration units, IIO, FF and bridge behavior
are unchanged. No new USB bytes, sensor writes or firmware operations are added.

A direct `109c` grant is root-only, exact-instance and consumed once during
probe. It skips only the *pending transition* requirement; it does not bypass
ownership validation. Generic probes/binds and unexplained native owners stay
rejected. Probe starts reception, not initialization. The manager saves the
attempt before invoking bootstrap, and same-instance kernel proof is required
before the runtime is accepted. Correlated `100a` → `109c` handover remains
separate and cannot gain permission for a second direct initialization.

Cleanup of direct `109c` preserves the standard model's conservative boundary:
one END only with proven ownership; no automatic xpad rebind of still-`109c`.
It is not a successful return to `100a`, even if another actor binds xpad.
An unresolved return needs the documented manual recovery. Missing terminal
proof blocks cleanup rather than guessing; a daemon restart may recover proof
but must not reinitialize. First errors and start budgets survive as before.
A healthy session replaced by a fresh `100a`/`109c` is retired; its replacement
must pass discovery, acquisition and budget anew. A faulted session is not
silently retired as healthy to allow another attempt.

**Still requires hardware validation:** starting without prior xpad activity,
an idle connected controller, pre-existing `109c` at boot, and both controller
power-on timings relative to service/Steam startup. A dongle enumerating while
the controller is off is not proof of a live RF link. Missing fresh IMU still
causes a bounded startup failure; there is no unlimited standby initialization
or automatic retry introduced by this correction. Do not claim every cold boot
or late power-on is fixed from these synthetic tests. Target-kernel builds and
separate Garuda/CachyOS acceptance must precede such claims.

## Cold boot and input dependency — 19 October 2026

The subsequent user-led cold boot did not meet the power-on-only goal. The
maintainer reports no manual service start or Resume, and explicitly says
that switching on was insufficient: native readiness appeared only after
operating the controls. Read-only inspection of that boot on revision 11,
kernel `7.2.11-1-cachyos-deckify`, records:

| Seconds after boot (rounded) | Recorded event |
| --- | --- |
| 5–9 | Dongle already enumerates as `109c`; xpad creates a generic gamepad. |
| 14 | systemd starts the enabled service and loads the expected new native module. |
| 96–98 | Initial device disappears; a fresh `100a` enumerates, briefly binds xpad, then binds `gs_native`. |
| 125–127 | Controlled transition to `109c`; native bootstrap completes with error 0, pad/IMU acknowledgement and verified handover. |
| 128 | Manager confirms exact input publication. |

The inspected final state is an active/enabled service with no service
restart, native `109c` ownership and paired `GameSir G7 Pro`/motion nodes.
The original report of initial xpad binding was correct. Service/module
autostart worked; that does not prove immediate controller readiness.

Two revision-11 code paths explain the remaining scope at that checkpoint:

1. `tools/service/gamesir_native.py` accepts fresh start PIDs `100a`/`105e`.
   It excludes an unrelated pre-existing `109c`. The kernel also requires
   a matching pending bootstrap before accepting `109c` in bootstrap mode.
   Simply adding a discovery PID would neither satisfy that contract nor
   establish safe ownership and initialization.
2. For an acquired `100a`, the manager waits in `waiting_input` until its
   native status reports at least one accepted pad packet. Zero packets
   cause another passive check, without a deadline or USB initialization
   output. The gate is report arrival, not a particular button or an IMU
   identity check. It is consistent with the user's need to operate controls;
   binding to native `100a` can already have happened before this gate opens.

There is no timestamped human-input trace or continuous status trace for
this boot. The source proves the report gate, but the retained logs do not
prove what caused the initial `109c` disappearance, when the first accepted
packet arrived, or how much of the subsequent delay belongs to that wait
versus protocol execution. Do not infer a physical unplug, automatic reset,
particular button trigger or exact wait duration.

The regressions at that checkpoint verified zero-report waiting and exclusion
of unowned `109c`; they did not fix either gap. The later revision-12 correction
above replaces those policy expectations while retaining ownership, pause,
budget, cleanup and protocol guards. Hardware acceptance is still outstanding.
That earlier follow-up changed documentation only. Private boot IDs, USB serial numbers
and raw logs remain outside Git; no new device observation, system action,
hardware repetition or push follows from the user's clarification.

## Shared acquisition design

The kernel already receives passive `100a` reports and performs the native
`100a` → `109c` bootstrap. The old manager only discovered xpad-owned start
interfaces and detached xpad through a separate userspace write. Revision 11
also discovers **free** `100a` and `105e` interfaces and acquires them directly.
Revision 12 extends this scoped contract to pre-existing `109c`.
It neither loads nor binds xpad to initialize a GameSir.

The enabled system service remains responsible for loading `gs_native` and
authorizing acquisition. There are deliberately no generic USB autoload aliases
or unrestricted native probes: those would bypass the pause and start budget.
If xpad happens to win the initial USB probe, the manager requests a targeted
handoff of the validated GameSir IF0. This does not promise that xpad can never
appear briefly in the binding history. Other Xbox controllers retain xpad;
there is no global blacklist, driver unload or replacement of xpad.

## Acquisition contract and ownership

The private root-only driver attributes are `acquire_100a`, `acquire_105e`
and, since revision 12, `acquire_109c`. All three accept exactly the existing version-1 identity format:

```text
1 IFNAME BUS ADDRESS DEVICE_INODE PARENT_INODE
```

The request includes a final newline. The manager validates the supported
USB descriptors, port, instance, parent lifetime, existing owner and competing
access. It checks pause, observation health and the per-port start budget
before saving acquisition intent and issuing the request. No fixed USB port,
device address or presumed unique serial is used as the production identity.

Under the USB device lock the kernel validates the exact device/parent objects,
VID/PID, interface and endpoints, pins that interface, and releases an optional
xpad owner only there. A foreign or unexplained native owner is rejected.
The subsequent attach retains the task/interface-specific one-shot probe gate
and rechecks identity. No reusable claim ticket survives. The old `claim_100a`
and `claim_105e` remain unbound-only for compatibility with older test helpers.
The new manager refuses an old module without the acquisition attributes;
it does not silently fall back to the old userspace-unbind sequence.

This narrows the initial detach race, not every race in USB driver binding.
Another probe, unplug or replacement during attach can still make acquisition
fail. The kernel must not bootstrap a replacement. Failure stops acquisition;
there is no automatic loop to regain the interface.

A pre-write refusal removes the intent lease and records the attempted
instance. It grants no cleanup ownership. A write failure or daemon crash
before native binding was verified cannot authorize detaching an unexplained
native owner: that case is blocked for manual recovery. The first acquisition
failure survives subsequent cleanup errors and manager restarts. A verified
native lease can still be cleaned up independently of the new-start budget.

## Runtime and fallback

After acquisition the existing protocol/runtime remains in use:

- `100a`: validated passive native state, then one bootstrap without requiring
  input packets; correlated `109c` acquisition accepts a free interface or an
  optional xpad handoff.
- Initial `109c`: separately scoped acquisition and one direct initialization;
  foreign or unexplained existing native bindings remain excluded.
- `105e`: direct native startup on the same verified instance. ZZZ acceptance
  remains more limited than standard-model acceptance.
- Persistent operation has no developer session timer. Existing RF-loss,
  disconnect, suspend, STOP, client-lifetime and bounded retry policies remain.
- Paddles, raw/coherent IIO, opted-in evdev motion, grip FF and independent
  trigger API are unchanged. Gyro stays at the accepted experimental
  `0.07 °/s/raw`; `1.00×` is a diagnostic display gain, not a new physical unit.
  Precise calibration remains paused. The optional Forza bridge stays in
  userspace, with its current game and lifecycle validation limits.

xpad is a recovery destination, not a normal runtime stage. Before releasing
a verified native start interface, the manager checks that xpad's bind
attribute exists. If absent, it reports that fallback is unavailable and does
not unbind native or silently load another module. Presence of that attribute
is not proof of a successful return: the subsequent guard and observation are
still required. The existing userspace fallback has a remaining replacement
race and is not described as atomic.

`END` and an xpad binding do **not** prove `109c` became `100a`. An unresolved
`109c` requires the documented, explicitly approved physical recovery. No USB
reset, guessed reverse-mode packet, automatic replug or automatic second try
is introduced. See [recovery/removal](INSTALLATION.md) and
[ownership rules](ALPHA_RUNTIME.md).

## Offline validation and acceptance boundary

The regression tests use synthetic sysfs/process/device models. Kernel claim
tests compile the actual extracted acquisition functions with ASan/UBSan;
they do not exercise real USB-core locking or hardware timing.

- `tests/test_manager_standalone.py`: free standard/direct startup, absent
  xpad, zero-report startup, direct native startup, pause/budget/monitor gates, multiple ports,
  reconnect, manager restart, missing contract/fallback and unconfirmed
  acquisition. Original errors and bounded cleanup persist across restart.
- Existing manager, kernel startup, lifetime, input publication, sensor,
  paddle, FF and userspace bridge regressions remain required.
- The final build/package results are recorded in [the release audit](RELEASE_AUDIT.md).

**Hardware acceptance remains pending on each host separately.** In particular,
we have not proved cold bootstrap without xpad having previously initialized
that physical device, or both new power-on paths. No speculative initialization
packet was added to hide that evidence gap.

## Next controlled validation, not an authorization

1. Review each host's exact kernel, matching headers, package/module versions,
   current ownership and saved state. Build for that kernel before installation.
   Keep a verified prior package and its configuration backup for rollback.
2. Separately approve installation and activation on one host first. Verify
   that the loaded module exposes the new contract before any acquisition.
3. Test free-interface cold startup without relying on prior xpad activity,
   then the optional xpad-owned compatibility path. Do not globally blacklist
   or unload xpad when other controllers depend on it. The exact isolation
   method and commands must be reviewed against the actual host state.
4. Confirm identity, bootstrap, persistent native ownership, normal inputs,
   four independent paddles, motion and the approved motor/application paths.
   Confirm other controllers remain unchanged. Test reconnect, reboot and PM
   as separate controlled cases with a failure stop and verified recovery.
5. Repeat acceptance on Garuda KDE and CachyOS Gamescope separately. Preserve
   the known Steam startup limitation: have the GameSir connected before Steam
   starts. Late-discovery/Guide-dependent Steam gyro is still unresolved.
   Eden's accepted application-only SDL-filter workaround remains manual.

For rollback, pause/return only proven managed instances, verify real USB and
ownership state, and use the documented physical recovery if necessary. Restore
the previously reviewed package/configuration only after safe return is proved;
do not force module removal or infer success from a package command alone.
No GUI, installation, new live test, tag or push is part of this offline change.
