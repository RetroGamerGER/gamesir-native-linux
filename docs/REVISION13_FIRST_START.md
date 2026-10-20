# Revision 13: first power-on and the retained fallback instance

20 October 2026. Read-only inspection of existing CachyOS/Gamescope journals,
installed metadata and the unchanged source. No new hardware test or runtime
change. The maintainer reports xpad at first power-on, native GameSir after
another radio off/on. Human power-on times were not captured; USB enumeration
times are not a timestamped RF trace.

The diagnosis below is the historical read-only checkpoint. The subsequently
requested offline manager correction is recorded at the end; installed revision
13 and its runtime remain unchanged.

## Current verified state

Package `0.1.0.alpha3-13`, kernel `7.2.11-1-cachyos-deckify` with matching
headers, and loaded/on-disk srcversion `8207CE72AE527F13E1D1B1D` are correct.
Installed manager/service hashes match the reviewed source. Service active,
enabled, zero restarts; management unpaused with no scan/port/monitor errors.
The current `109c` is native-owned, attested and active, input publication
confirmed. Gyro, acceleration, persistent mode and deferred publication are
enabled; the retained acceleration profile is `1,2,3`, `8192/1`.
`returned=false` is expected for this active native session, not a recovery fault.
This metadata is not a new application, paddle or four-motor acceptance test.

## Two recorded sequences

Seconds since each relevant host boot; machine names, serials, addresses,
paths and ownership tokens are omitted.

| Event | Installation-day boot | Current boot |
| --- | ---: | ---: |
| Initial `109c` native binding | 2899.354 | 14.848 |
| Bootstrap fails: `-110`, `failed_stage=5`, `step=6`, `pad=0`, `imu=0` | 2902.731 | 18.217 |
| Replacement `100a`, xpad registration | 2907.793 | 48.102 |
| Later replacement `109c` | 2937.648 | 61.356 |
| Direct native bootstrap succeeds, `pad=1`, `imu=1` | 2938.411 | 61.963 |
| Manager confirms input publication | 2939.287 | 62.872 |

The first instance **was acquired by gs_native**; this is not a missing module
or pre-acquisition refusal. Stage 5 is `GS_BOOT_VERIFY`. All six initial native
OUT transfers completed; the final logged transfer succeeded with 64/64 bytes.
No accepted pad or IMU report was recorded before the approximately 3.37-second
bootstrap failure. The three-second verification window, initial pacing and
heartbeats explain the timeout location. USB OUT completion is not a firmware
acknowledgement or proof that a radio controller is ready.

Both direct-`109c` failure and success have `xinput_query_attempted=0`, as
designed. Revision 13's query applies only to the `100a` transition. In the
intervening boot, a `100a` start completed with query result 20, native transition
and input publication. That proves execution in that run, not necessity or
cold-start sufficiency. Prior xpad initialization is not excluded by these logs.

## Why the next xpad instance is skipped

`Manager.poll_job()` retains the terminal bootstrap proof, attests the exact
failed native instance and permits cleanup only. When a replacement `100a`
already bound to xpad appears, `Manager.return_one()`:

1. Marks the entry `released` and records `observed_100a_xpad`.
2. Saves the replacement device, removes the old lease and adds the
   **replacement's token** to `attempted`.
3. `Manager.tick()` then skips that released entry while it remains the same
   xpad instance; the attempted set also prevents a fresh start on it.

The protected state has that resolution and the intermediate token in
`attempted`. No bootstrap was logged for that `100a`. A further new `109c`
replaces the released entry and becomes eligible for budgeted discovery;
its recorded bootstrap and publication succeed. The original timeout remains.
This explains the extra enumeration needed for native startup, without proving
a required button press or a dependency on xpad initialization. The generic
manager message says "failed after native handoff" even here; `handover=0`
identifies the actual same-instance direct path.

## Offline confirmation and remaining uncertainty

A private device-free reproduction uses the actual manager and existing Fake
adapter: fail direct `109c` verification, finish attested END, introduce xpad
`100a`, then a new xpad `109c`. Thirty-one further ticks on the first replacement
perform no claim/bootstrap: it remains released, attempted and xpad-owned.
The later replacement becomes active through a fresh claim/bootstrap. There
are two bootstraps total, one cleanup END, no speculative restore, and the
original `-110` diagnostic survives.

The unchanged 40 standalone-manager tests, shared C startup tests and 282
ASan/UBSan kernel-adapter scenarios pass. Existing direct-native scenarios
already cover missing IMU as terminal failure. These synthetic checks do not
validate RF timing, real USB locking or a corrected hardware startup.

**Unknown:** why the first native attempt lacks accepted sensor data. Starting
before RF readiness, firmware settling or another native initialization state
remain hypotheses. There is no simultaneous RF/power-on/input trace to choose
between them. A longer arbitrary delay, the `100a` query on `109c`, or blind
initialization replay is not justified by these reads.

## Recommendation for separate offline development

Distinguish a present dongle awaiting controller readiness from a faulted active
runtime using an evidenced readiness contract. Revisit permanent suppression
of a **new, verified returned instance** after cleanup. Preserve the failed
instance's diagnostic, attempt/start budgets, exact ownership and separate
cleanup authority. Do not turn this into unbounded retries or another command
on an old failed instance. Binding `109c` to xpad does not convert it to `100a`.

No correction is implemented here. Final inventory confirms the same boot,
service process, module, USB instance/binding, installed package and configuration
as before inspection. Raw evidence and the reproduction remain private. Only
this anonymized analysis is added to the public source tree. No push or calibration.

## Offline manager correction — 20 October 2026

The later explicit development request is implemented in
`Manager.retire_returned_timeout()`. It applies only when all of these hold:

- An originally direct `109c` bootstrap reported terminal VERIFY timeout,
  no pad/IMU and no handover. The child completed normally with failure, not a
  supervisor timeout. Its diagnostic source is still that exact old instance.
- The old instance was independently attested, matching kernel tokens remain,
  and its one cleanup END completed successfully. A lease still exists.
- Management is neither paused nor shutting down. A complete current scan
  sees a different, not-yet-attempted `100a` on xpad at the same parent lifetime.

The manager records observed return in the original failure, drops only the
old lease/entry and defers discovery until a **new scan on the next tick**.
It does not mark this new instance attempted without actually starting it.
Ordinary discovery repeats ownership/access validation and checks the unchanged
per-port three-start budget before acquisition. The original failed token,
diagnostic, budget and pause policy survive; no command is issued using the
return snapshot. Persistence before discovery also preserves this distinction
over daemon restart. A new unknown/foreign owner or metadata error prevents
acquisition normally.

Paused release, shutdown, successful runtimes with later faults, other error
codes/stages, uncertain child results, failed END, absent/mismatched tokens,
changed hubs and attempted instances retain their prior recovery policy.
The failing old instance is never restarted. A failure of the newly started
`100a` does not recursively authorize this direct-`109c` exception. Historical
revision-13 attempted tokens are not migrated or deleted: installing later code
is not permission to retry an already suppressed instance.

Sixteen new manager tests first reproduced the old failure and now pass,
alongside the prior 40. They cover the saved sequence, zero-pad new bootstrap,
completed runtime, restart before/after return, late observed return, bounded
second failure, pause/shutdown, exhausted budget, uncertain metadata and foreign
owners, and all negative proof fields. Old proof alone never owns a replacement.

### Missing first sensor: what the offline tests can establish

Seven new shared-C cases exercise the real unchanged direct-start core:
silence, unknown packets, non-IMU vendor packets and pad-only input cannot pass
IMU verification; a valid IMU just before deadline succeeds without a button;
malformed telemetry fails with `-EPROTO`; a valid frame at/after deadline cannot
erase `-ETIMEDOUT`. None of these packets resets the original deadline.

Code review also finds that interrupt IN is submitted in probe before the
explicit bootstrap. Direct `109c` starts initialization immediately; its
descriptor is not an RF-ready test. Known gyro gain, axis mapping and downstream
Steam/Eden filtering do not decide this raw bootstrap's `imu_seen`. The existing
`first_rx_status=0` records no terminal RX error, not the number or content of
successful RX completions. Silence and accepted unknown/vendor reports cannot
be distinguished by the saved zero-pad/zero-IMU record. Thus the missing first
sample is not yet a proved decoder, RF or firmware defect.

The [Sony/Gamescope comparison](DUALSENSE_STARTUP_GAMESCOPE.md) reinforces the
need for an evidenced connection/readiness state; Sony's older PS4 receiver has
one, but no equivalent GameSir bit is established. No startup packet, deadline,
sensor gate, kernel ABI, identity or calibration change is made here.

Full offline validation: 1,227 Python tests in 43 suites, shared C/protocol tests
and 282 sanitizer-backed kernel-startup scenarios pass. Local Garuda module
build passes with zero code warnings; the existing Clang 23.1.1 versus 23.1.3
environment advisory remains disclosed. No target SSH, installation, hardware
test or running driver/Steam change. No new package or push; prepare a separately
versioned update and hardware acceptance only after review.

## Maintainer's subsequent hotplug check

The maintainer independently reports three successful repetitions with the
controller already powered on/seeking connection, then insertion of its USB
receiver. It connects as GameSir without an observed xpad stage. Installed code
is still revision 13; the offline manager correction is not responsible for
these results. No synchronized trace proves that xpad never bound transiently,
and this report does not separately confirm sensors, paddles or motor effects.
Steam's exact state and the initial PID/timing of each repetition were not
recorded. This supports a receiver/controller startup-order lead, not proof
that Steam requires an RF connection or causes the native IMU timeout.

The later request is to prepare revision 14 for the CachyOS target, inspect
fresh state and present the concrete update/test steps for approval. Its only
runtime-code change is the bounded manager correction above. Kernel behavior,
sensor timing and protocol remain unchanged. Preparation is not installation
or cold-start acceptance; retain the three reports as user evidence only.
