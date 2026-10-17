#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Prepare a passive 100a HID test; execution always needs separate approval.

Default/show-plan/validate only read ordinary project or manifest files. They
never collect host metadata. The execute subcommand is a future, explicitly
authorized root operation; it only starts the existing isolated USB recorder.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import stat
import sys
import time

from native_usb_capture import (ASSETS, ASSET_NAMES, ROOT, CaptureHalt, PASSIVE_SCOPE,
    PASSIVE_DURATION, PASSIVE_OUTER_TIMEOUT, attach, digest, need, regular, utc,
    validate_passive_target, verify_sources)

FINALIZE_GRACE_SECONDS = 1


def phase_plan():
    """Host cue times relative to guest recorder request, not a sensor clock."""
    phases = [
        ('prepare', 0, 30, 'Vorbereitung: Controller bequem ablegen.', 0),
        ('rest', 30, 50, 'RUHE: Controller liegen lassen.', 0),
        ('buttons', 50, 80, 'Normale Tasten und Steuerkreuz.', 10),
        ('sticks', 80, 110, 'Beide Sticks und analoge Trigger.', 10),
        ('l4', 110, 135, 'Nur L4 mehrfach drücken und vollständig loslassen.', 10),
        ('r4', 135, 160, 'Nur R4 mehrfach drücken und vollständig loslassen.', 10),
        ('l5', 160, 185, 'Nur L5 mehrfach drücken und vollständig loslassen.', 10),
        ('r5', 185, 210, 'Nur R5 mehrfach drücken und vollständig loslassen.', 10),
        ('combinations', 210, 240, 'Zusatztasten paarweise drücken, dann loslassen.', 10),
        ('movement', 240, 270, 'Langsam um die drei Achsen bewegen; keine Kalibrierung.', 10),
        ('final_rest', 270, 300, 'SCHLUSSRUHE: Controller ablegen. Letzte Sekunde ist Abschlussreserve.', 0),
    ]
    return [dict(name=name, start=start, end=end, instruction=instruction,
                 buffer_seconds=buffer_seconds)
            for name, start, end, instruction, buffer_seconds in phases]


def _metadata_valid(value):
    need(isinstance(value, dict) and set(value) == {
        'uid', 'gid', 'mode', 'sha256', 'file_capability_xattr_hex'},
        'Exact cached dumpcap metadata required')
    need(type(value['uid']) is int and value['uid'] == 0
         and type(value['gid']) is int and 0 <= value['gid'] < 2**32 - 1,
         'dumpcap must retain its approved root owner and integer group')
    mode = value['mode']
    need(isinstance(mode, str) and re.fullmatch(r'0o[0-7]{3,4}', mode)
         and int(mode, 8) & 0o100 and not int(mode, 8) & 0o6022,
         'Unsafe dumpcap mode')
    need(isinstance(value['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', value['sha256']),
         'Invalid dumpcap digest')
    caps = value['file_capability_xattr_hex']
    need(caps is None or isinstance(caps, str) and len(caps) <= 128
         and re.fullmatch(r'(?:[0-9a-f]{2})*', caps), 'Invalid cached capability bytes')


def make_manifest(target, dumpcap_metadata):
    """Use explicitly supplied cached metadata; do not inspect live host state."""
    value = {'schema_version': 1, 'scope': PASSIVE_SCOPE, 'target': copy.deepcopy(target),
             'usb_capture': {'duration_seconds': PASSIVE_DURATION,
                 'outer_timeout_seconds': PASSIVE_OUTER_TIMEOUT,
                 'dumpcap_file_metadata': copy.deepcopy(dumpcap_metadata)}, 'sha256': {}}
    validate_passive_target(value['target'])
    _metadata_valid(value['usb_capture']['dumpcap_file_metadata'])
    paths = [ROOT / 'tools/native/native_usb_capture.py', Path(__file__).absolute()]
    paths.extend(ASSETS / name for name in ASSET_NAMES)
    for path in paths:
        regular(path)
        value['sha256'][str(path.relative_to(ROOT))] = digest(path)
    return validate_manifest(value)


def validate_manifest(manifest):
    """File-only validation; no subprocess, manager, device or live sysfs read."""
    need(isinstance(manifest, dict) and set(manifest) == {
        'schema_version', 'scope', 'target', 'usb_capture', 'sha256'}, 'Unknown manifest fields')
    need(type(manifest['schema_version']) is int and manifest['schema_version'] == 1
         and manifest['scope'] == PASSIVE_SCOPE, 'Wrong passive manifest version/scope')
    validate_passive_target(manifest['target'])
    conf = manifest['usb_capture']
    need(isinstance(conf, dict) and set(conf) == {
        'duration_seconds', 'outer_timeout_seconds', 'dumpcap_file_metadata'}
        and type(conf['duration_seconds']) is int and conf['duration_seconds'] == PASSIVE_DURATION
        and type(conf['outer_timeout_seconds']) is int and conf['outer_timeout_seconds'] == PASSIVE_OUTER_TIMEOUT,
        'Only the approved 300/330 second limits are supported')
    _metadata_valid(conf['dumpcap_file_metadata'])
    need(isinstance(manifest['sha256'], dict), 'Missing source pins')
    checked = verify_sources(manifest)
    need(set(manifest['sha256']) == set(checked), 'Unexpected source pin set')
    return copy.deepcopy(manifest)


def read_manifest(path):
    """Bounded ordinary-file import; FIFOs/devices and symlinks are rejected."""
    path = Path(path).absolute()
    need(not any(path == base or base in path.parents for base in map(Path, ('/dev', '/proc', '/sys'))),
         'Manifest must be an ordinary file, never a device/live metadata path')
    regular(path)
    need(path.resolve() == path and path.stat().st_size <= 1024 * 1024,
         'Manifest path must be canonical and at most 1 MiB')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'r') as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Manifest changed type')
        text = stream.read(1024 * 1024 + 1)
    need(len(text) <= 1024 * 1024, 'Manifest grew beyond limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate manifest key: ' + key)
            result[key] = value
        return result
    return validate_manifest(json.loads(text, object_pairs_hook=unique))


def persist_result(output, value, owner):
    """Durable standalone checksum chain, separate from immutable raw capture.

    The JSON records facts, not an unverified overall-success bit. Completion
    requires verification of the adjacent SHA256SUMS, returned only afterward.
    """
    output = Path(output)
    need(output.is_dir() and not output.is_symlink()
         and stat.S_IMODE(output.stat().st_mode) == 0o700
         and owner == (output.stat().st_uid, output.stat().st_gid),
         'Private evidence directory/owner changed before result persistence')
    report = copy.deepcopy(value)
    report.pop('passed', None)
    report['completion_contract'] = 'Completion requires verified adjacent SHA256SUMS; capture.passed describes the recorder audit only.'
    report['completed_utc'] = utc()
    capture_result = report.get('capture') or {}
    outcome = output / 'usb-capture/capture-outcome.json'
    chain = output / 'usb-capture/SHA256SUMS'
    covered = []
    for path in (outcome, chain):
        if os.path.lexists(path):
            regular(path)
            covered.append(path)
    if outcome in covered:
        need(digest(outcome) == capture_result.get('capture_outcome_sha256'),
             'Standalone capture outcome digest does not match returned receipt')
    if capture_result.get('passed') is True:
        need(outcome in covered and chain in covered,
             'Successful capture requires a durable nested checksum chain')
    def write(name, data):
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            os.fchown(stream.fileno(), *owner)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    report_path = output / 'result.json'
    write('result.json', (json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode())
    covered.insert(0, report_path)
    sums = ''.join(digest(path) + '  ' + str(path.relative_to(output)) + '\n' for path in covered)
    write('SHA256SUMS', sums.encode())
    fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    for line in (output / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        need(digest(output / name) == expected, 'Standalone result checksum verification failed')
    return {'report_sha256': digest(report_path), 'checksum_manifest_verified': True}


def run_phases(recorder, *, clock=time.monotonic, sleep=time.sleep, emit=print):
    """Only cues and owned-recorder guards; no USB commands or input readers."""
    origin = recorder.capture_started
    now = clock()
    need(type(origin) in (int, float) and math.isfinite(origin)
         and recorder.ready is not None and origin <= recorder.ready <= now < origin + 30,
         'Verified recorder/preparation clock required')
    need(recorder.deadline == origin + PASSIVE_DURATION, 'Passive recording deadline differs')
    events = []
    def cue(event, phase, instruction):
        stamp = clock()
        item = {'utc': utc(), 'monotonic_ns': int(stamp * 1e9),
                'seconds_from_capture_request': stamp - origin,
                'event': event, 'phase': phase, 'instruction': instruction}
        events.append(item)
        emit(item)
    def wait_until(deadline, label):
        while clock() < deadline:
            recorder.check(0, label)
            sleep(min(.1, max(0, deadline - clock())))
        recorder.check(0, label)
        need(clock() <= deadline + 2, 'Phase timing exceeded two-second cue tolerance: ' + label)
    cue('verified_start', 'prepare', 'AUFNAHME LÄUFT. Isolation geprüft. ' +
        f'Noch ungefähr {max(0, math.floor(origin + 30 - now))} Sekunden Vorbereitung.')
    for phase in phase_plan():
        # The preparation phase has deliberately begun before verified readiness.
        if phase['start']:
            wait_until(origin + phase['start'], phase['name'])
        cue('phase_cue', phase['name'], phase['instruction'] +
            (f" Zunächst {phase['buffer_seconds']} Sekunden Reaktionspuffer."
             if phase['buffer_seconds'] else ''))
        if phase['buffer_seconds']:
            wait_until(origin + phase['start'] + phase['buffer_seconds'], phase['name'] + '-buffer')
            cue('action_cue', phase['name'], 'JETZT: ' + phase['instruction'])
    wait_until(origin + PASSIVE_DURATION - FINALIZE_GRACE_SECONDS, 'final-rest')
    cue('capture_finish', 'final_rest', 'Messphasen beendet. Aufnahme wird kontrolliert geschlossen; keine Rückbindung.')
    return events


def execute(manifest, output, *, authorized=False, readiness=input, capture_factory=attach,
            clock=time.monotonic, sleep=time.sleep, emit=print):
    """Future single approved run, with evidence preserved on every abort."""
    need(authorized is True, 'Specific passive-capture authorization flag required')
    checked = validate_manifest(manifest)
    need(os.geteuid() == 0 and sys.stdin.isatty() and sys.stdout.isatty(),
         'Approved root operation must run in a visible terminal')
    print('Nur nach konkreter Freigabe BEREIT eingeben. Keine USB-Befehle oder Treiberwechsel.', flush=True)
    if readiness is input:
        need(bool(select.select([sys.stdin], [], [], 300)[0]), 'Local readiness timed out; no capture')
    need(readiness('BEREIT: ').strip().casefold() == 'bereit', 'No explicit local readiness; no capture')
    recorder = capture_factory(checked, output)
    cues, cue_stream, result = [], None, None
    def recorded_emit(item):
        cues.append(item)
        if cue_stream is not None:
            cue_stream.write((json.dumps(item, ensure_ascii=False) + '\n').encode())
            cue_stream.flush()
        emit(item)
    try:
        recorder.start()
        cue_stream = recorder._file('phase-cues.jsonl')
        run_phases(recorder, clock=clock, sleep=sleep, emit=recorded_emit)
        cue_stream.flush()
        os.fsync(cue_stream.fileno())
        cue_stream.close()
        result = recorder.finish()
        need(result.get('passed') is True, 'Passive recorder final audit failed; preserve evidence')
        summary = {'scope': PASSIVE_SCOPE, 'capture': result, 'cue_count': len(cues),
                   'hardware_commands_sent': False, 'drivers_changed': False,
                   'calibration_performed': False, 'automatic_retry': False}
        receipt = persist_result(output, summary, getattr(recorder, 'owner', None))
    except BaseException as error:
        cleanup_errors = []
        try:
            if cue_stream is not None and not cue_stream.closed:
                cue_stream.flush()
                os.fsync(cue_stream.fileno())
                cue_stream.close()
        except BaseException as close_error:
            cleanup_errors.append('Cue log close: ' + str(close_error))
        finally:
            if cue_stream is not None and not cue_stream.closed:
                try:
                    cue_stream.close()
                except BaseException as close_error:
                    cleanup_errors.append('Cue log descriptor close: ' + str(close_error))
        try:
            result = recorder.abort(type(error).__name__ + ': ' + str(error))
        except BaseException as stop_error:
            cleanup_errors.append('Owned recorder abort: ' + str(stop_error))
        try:
            persist_result(output, {'scope': PASSIVE_SCOPE, 'capture': result,
                'primary_error': type(error).__name__ + ': ' + str(error),
                'cleanup_errors': cleanup_errors, 'cue_count': len(cues),
                'hardware_commands_sent': False, 'drivers_changed': False,
                'automatic_retry': False}, getattr(recorder, 'owner', None))
        except BaseException as persist_error:
            cleanup_errors.append('Standalone result persistence: ' + str(persist_error))
        try:
            emit({'event': 'stopped', 'error': type(error).__name__ + ': ' + str(error),
                  'capture': result, 'cleanup_errors': cleanup_errors})
        except BaseException:
            pass  # A broken display must not replace the original test failure.
        raise
    return dict(summary, evidence=receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('show-plan', help='File-only plan; no host metadata collection')
    validation = sub.add_parser('validate', help='Validate existing ordinary manifest/source files only')
    validation.add_argument('--manifest', type=Path, required=True)
    live = sub.add_parser('execute', help='Not authorized by source code; requires a new explicit hardware approval')
    live.add_argument('--manifest', type=Path, required=True)
    live.add_argument('--output', type=Path, required=True)
    live.add_argument('--authorize-passive-capture', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command in (None, 'show-plan'):
            value = {'scope': PASSIVE_SCOPE, 'hardware_access': False, 'phases': phase_plan(),
                'duration_ceiling_seconds': PASSIVE_DURATION,
                'outer_timeout_seconds': PASSIVE_OUTER_TIMEOUT,
                'clock': 'guest recorder request monotonic clock; preparation absorbs readiness latency',
                'finalization_grace_seconds': FINALIZE_GRACE_SECONDS}
        elif args.command == 'validate':
            value = {'valid': True, 'hardware_access': False, 'manifest': read_manifest(args.manifest)}
        else:
            need(args.authorize_passive_capture, 'Missing explicit passive-capture authorization flag')
            def interrupted(signum, frame):
                raise KeyboardInterrupt('Capture interrupted by signal ' + str(signum))
            for signum in (signal.SIGTERM, signal.SIGHUP):
                signal.signal(signum, interrupted)
            value = execute(read_manifest(args.manifest), args.output, authorized=True,
                            emit=lambda event: print('CUE ' + json.dumps(event, ensure_ascii=False), flush=True))
        print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (CaptureHalt, OSError, ValueError, KeyboardInterrupt) as error:
        print('STOPPED ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
