#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Separate, bounded 109c/xpad RF reference. Default is an offline plan.

inspect needs a separately approved privileged metadata read; execute needs
capture approval AND local GO. Neither operation loads modules or controls a
driver. No automatic retry, receiver reset, mode change or recovery is present.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import time

from native_usb_capture import (ASSETS, ASSET_NAMES, ROOT, CaptureHalt, attach,
    digest, dumpcap_metadata, need, regular, utc, verify_sources)
from hid_sidechannel_capture import _metadata_valid, persist_result
from rf_link_policy import SCOPE, DURATION, OUTER_TIMEOUT, Tracker, validate_target


def plan():
    return {'scope': SCOPE, 'hardware_access': False, 'duration_ceiling_seconds': DURATION,
        'outer_timeout_seconds': OUTER_TIMEOUT, 'finalization_reserve_seconds': 1,
        'phases': [
            {'seconds': [0, 30], 'instruction': 'Controller AUS lassen; KDE-Test geöffnet halten.'},
            {'seconds': [30, 60], 'instruction': 'JETZT einmal einschalten. Keine Tasten/Sticks. Sichtbare Verbindung mit VERBUNDEN + Enter bestätigen.'},
            {'seconds': [60, 80], 'instruction': 'Nur nach Bestätigung: A, beide Sticks, sanft drehen.'},
            {'seconds': [80, 90], 'instruction': 'Ablegen; bei Sekunde 89 kontrolliert schließen.'}],
        'unknown_is_not_connected': True, 'baseline': '3537:109c, IF0 xpad, IF1 unbound, bus8/port8-6',
        'epoch_policy': 'Same boot/parent only; 100a/xpad/usbhid or 109c/xpad; at most four distinct lifetimes; no address filter.',
        'metadata_gap_limits_seconds': {'absent': 5, 'incomplete': 2},
        'prerequisites': ['Fresh paused live manager and empty protected ownership',
            'Ordinary IF0 input consumer, e.g. KDE controller test, remains open',
            'Fresh pinned sources, dumpcap metadata and exact initial instance',
            'Separately approved usbmon load only if missing', 'Separate capture approval and local GO'],
        'limits': 'USB/RF silence alone does not prove disconnect. User connection cue is approximate; this is not a calibration or paddle mapping test.'}


def source_paths():
    return [ROOT / 'tools/native' / name for name in (
        'native_usb_capture.py', 'hid_sidechannel_capture.py', 'rf_link_capture.py', 'rf_link_policy.py')] + [
        ASSETS / name for name in (*ASSET_NAMES, 'rf-identity-check.py')]


def make_manifest(target, metadata):
    validate_target(target)
    _metadata_valid(metadata)
    value = {'schema_version': 1, 'scope': SCOPE, 'target': copy.deepcopy(target),
        'usb_capture': {'duration_seconds': DURATION, 'outer_timeout_seconds': OUTER_TIMEOUT,
                        'dumpcap_file_metadata': copy.deepcopy(metadata)}, 'sha256': {}}
    for path in source_paths():
        regular(path)
        value['sha256'][str(path.relative_to(ROOT))] = digest(path)
    return validate_manifest(value)


def validate_manifest(value):
    need(isinstance(value, dict) and set(value) == {
        'schema_version', 'scope', 'target', 'usb_capture', 'sha256'}, 'Exact RF manifest required')
    need(type(value['schema_version']) is int and value['schema_version'] == 1
         and value['scope'] == SCOPE, 'Wrong RF scope/version')
    validate_target(value['target'])
    conf = value['usb_capture']
    need(isinstance(conf, dict) and set(conf) == {'duration_seconds', 'outer_timeout_seconds',
        'dumpcap_file_metadata'} and type(conf['duration_seconds']) is int
        and conf['duration_seconds'] == DURATION and type(conf['outer_timeout_seconds']) is int
        and conf['outer_timeout_seconds'] == OUTER_TIMEOUT, 'Wrong RF recording budget')
    _metadata_valid(conf['dumpcap_file_metadata'])
    need(isinstance(value['sha256'], dict) and set(verify_sources(value)) == set(value['sha256']),
         'Unexpected/missing RF source pins')
    return copy.deepcopy(value)


def read_json(path):
    path = Path(path).absolute()
    need(not any(path == base or base in path.parents for base in map(Path, ('/dev', '/proc', '/sys'))),
         'Ordinary file required, not live metadata/device')
    regular(path)
    need(path.resolve() == path and path.stat().st_size <= 1048576, 'Canonical bounded JSON file required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'r') as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'JSON file changed type')
        data = stream.read(1048577)
    need(len(data) <= 1048576, 'JSON file grew beyond limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def monitor_metadata():
    try:
        value = Path('/dev/usbmon8').lstat()  # Stat only; no monitor open.
    except FileNotFoundError:
        return None
    need(stat.S_ISCHR(value.st_mode) and value.st_uid == 0 and
         stat.S_IMODE(value.st_mode) == 0o600 and os.minor(value.st_rdev) == 8,
         'Unexpected monitor metadata; stop without changing permissions')
    return {'uid': value.st_uid, 'gid': value.st_gid, 'mode': oct(stat.S_IMODE(value.st_mode)),
            'major': os.major(value.st_rdev), 'minor': os.minor(value.st_rdev)}


class PreflightFailure(CaptureHalt):
    """Keep the original failed stage and already collected private evidence."""
    def __init__(self, report):
        self.report = report
        failure = report['failure']
        phase = 'confirmation' if failure['stage'].startswith('confirmation') else 'baseline'
        fields = [item['field'] for item in report['metadata_details'][phase]
                  if item['status'] in ('failed', 'unknown')]
        detail = '; metadata fields: ' + ', '.join(dict.fromkeys(fields)) if fields else ''
        super().__init__(failure['stage'] + ': ' + failure['type'] + ': ' + failure['message'] + detail)


def inspect(*, authorized=False, run=subprocess.run, reader=None, metadata_reader=dumpcap_metadata,
            monitor_reader=monitor_metadata):
    """Future explicit read only, not called by plan/prepare/validate/import."""
    need(authorized is True and os.geteuid() == 0, 'Separate privileged read approval required')
    stages = ('source_pins', 'manager_status', 'manager_conditions', 'baseline_metadata',
              'baseline_conditions', 'dumpcap_metadata', 'manifest', 'confirmation_metadata',
              'confirmation_matches', 'source_pins_match', 'monitor_metadata')
    report = {'report_version': 2, 'scope': SCOPE, 'read_only': True, 'ok': False, 'checked_utc': utc(),
              'capture_started': False, 'module_load_attempted': False,
              'stages': {name: 'not_evaluated' for name in stages},
              'checks': [], 'metadata_details': {'baseline': [], 'confirmation': []}}
    stage = None
    def enter(name):
        nonlocal stage
        if stage is not None:
            report['stages'][stage] = 'passed'
        stage = name
        report['stages'][stage] = 'running'
    def check(field, condition, expected, observed):
        report['checks'].append({'field': field, 'status': 'passed' if condition else 'failed',
                                 'expected': expected, 'observed': observed})
        need(condition, f'{field}: expected {expected!r}, observed {observed!r}')
    def compare(field, expected, observed):
        if isinstance(expected, dict) and isinstance(observed, dict):
            for key in sorted(set(expected) | set(observed)):
                if key not in expected or key not in observed:
                    check(field + '.' + key, False, 'present' if key in expected else 'absent',
                          'present' if key in observed else 'absent')
                compare(field + '.' + key, expected[key], observed[key])
        else:
            check(field, expected == observed, expected, observed)
    try:
        enter('source_pins')
        pins = {str(p.relative_to(ROOT)): digest(p) for p in source_paths()}
        report['source_sha256'] = pins
        enter('manager_status')
        status = run(['/usr/bin/gamesir-native', 'status'], stdin=subprocess.DEVNULL,
                     capture_output=True, text=True, timeout=10, check=False,
                     env={'PATH': '/usr/bin', 'LANG': 'C', 'LC_ALL': 'C'})
        report['manager_status_read'] = {'returncode': status.returncode,
            'stdout': status.stdout[:1048576], 'stderr': status.stderr[:1048576],
            'output_truncated': len(status.stdout) > 1048576 or len(status.stderr) > 1048576}
        check('manager.command_exit', status.returncode == 0, 0, status.returncode)
        check('manager.output_bounded', not report['manager_status_read']['output_truncated'], True,
              not report['manager_status_read']['output_truncated'])
        manager = json.loads(status.stdout)
        check('manager.schema', isinstance(manager, dict), 'object', type(manager).__name__)
        report['manager'] = manager
        enter('manager_conditions')
        for name in ('ok', 'paused', 'returned'):
            check('manager.' + name, manager.get(name) is True, True, manager.get(name))
        check('manager.devices', manager.get('devices') == {}, {}, manager.get('devices'))
        for name in ('scan_error', 'port_errors'):
            check('manager.' + name, not manager.get(name), 'empty', manager.get(name))
        if reader is None:
            namespace = {'__name__': 'rf_metadata_only'}
            path = ASSETS / 'rf-identity-check.py'
            source = path.read_bytes()
            need(hashlib.sha256(source).hexdigest() == pins[str(path.relative_to(ROOT))],
                 'Metadata source changed before use')
            exec(compile(source, str(path), 'exec'), namespace)
            reader = lambda *, diagnostics: namespace['snapshot']({'capture_profile': SCOPE}, diagnostics=diagnostics)
        enter('baseline_metadata')
        before = reader(diagnostics=report['metadata_details']['baseline'])
        report['snapshot'] = before
        enter('baseline_conditions')
        check('baseline.observation', before['observation'] == 'present', 'present',
              {'observation': before['observation'], 'reason': before['reason']})
        check('baseline.input_consumer_open', before['input_consumer_open'] is True, True,
              before['input_consumer_open'])
        check('baseline.pid', before['identity']['pid'] == '109c', '109c', before['identity']['pid'])
        enter('dumpcap_metadata')
        metadata = metadata_reader()
        report['dumpcap_file_metadata'] = metadata
        enter('manifest')
        manifest = make_manifest(before['identity'], metadata)
        Tracker(manifest['target']).observe(before, 0, initial=True)
        report['manifest'] = manifest
        enter('confirmation_metadata')
        after = reader(diagnostics=report['metadata_details']['confirmation'])
        report['confirmation_snapshot'] = after
        enter('confirmation_matches')
        # Identify the differing field instead of reporting only a whole-object mismatch.
        compare('confirmation', before, after)
        enter('source_pins_match')
        check('source_pins.unchanged', manifest['sha256'] == pins, True, manifest['sha256'] == pins)
        enter('monitor_metadata')
        monitor = monitor_reader()
        report.update(monitor_metadata=monitor, needs_separately_approved_usbmon=monitor is None,
                      ok=True, completed_utc=utc(),
                      next_gate='Review fresh manifest and monitor prerequisites before capture approval')
        report['stages'][stage] = 'passed'
        return report
    except (CaptureHalt, OSError, ValueError, KeyError, TypeError, KeyboardInterrupt, subprocess.SubprocessError) as error:
        report['stages'][stage] = 'failed'
        report['failure'] = {'stage': stage, 'type': type(error).__name__, 'message': str(error)}
        report['completed_utc'] = utc()
        report['next_gate'] = 'Stop; no retry, recovery, capture or module load. A new read requires approval.'
        raise PreflightFailure(report) from error


class TerminalLines:
    """One unbuffered inherited TTY reader throughout GO and connection cues.

    No input()/readline()/sudo stdin mixture; partial lines and both GO cases
    are supported. Never open /dev/tty or log unexpected user-entered text.
    """
    def __init__(self, fd):
        self.fd, self.buffer = fd, b''

    def poll(self):
        if select.select([self.fd], [], [], 0)[0]:
            data = os.read(self.fd, 512)
            need(bool(data), 'Terminal EOF; stop')
            self.buffer += data
            need(len(self.buffer) <= 1024, 'Terminal input exceeds limit')
        lines = self.buffer.split(b'\n')
        self.buffer = lines.pop()
        return [line.decode('utf-8', errors='strict').strip().casefold() for line in lines]


def await_go(terminal, *, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + 300
    while clock() < deadline:
        lines = terminal.poll()
        need('stop' not in lines, 'Local STOP before capture')
        if 'go' in lines:
            return
        sleep(.1)
    raise CaptureHalt('No local GO within five minutes; no capture')


def run_phases(recorder, terminal, *, clock=time.monotonic, sleep=time.sleep, emit=print):
    origin = recorder.capture_started
    need(type(origin) in (int, float) and math.isfinite(origin)
         and recorder.ready is not None and origin <= recorder.ready <= clock() < origin + 20
         and recorder.deadline == origin + DURATION, 'Verified RF recorder clock/budget required')
    confirmed, phase = None, None
    def cue(event, instruction):
        value = {'event': event, 'instruction': instruction, 'utc': utc(),
                 'monotonic_ns': int(clock() * 1e9), 'seconds_from_capture_request': clock() - origin}
        emit(value)
    cue('verified_start', 'AUFNAHME LÄUFT. Controller AUS lassen. KDE-Test offen halten.')
    last = clock()
    while True:
        now = clock()
        need(math.isfinite(now) and last <= now <= last + 2, 'RF cue clock jumped/regressed; stop')
        recorder.check(0, 'rf-phases')
        now = clock()
        need(last <= now <= last + 2, 'Metadata check exceeded cue timing tolerance; stop')
        last = now
        elapsed = now - origin
        lines = terminal.poll()
        need('stop' not in lines, 'Local STOP; preserve recording')
        desired = 'rest' if elapsed < 20 else 'heads_up' if elapsed < 30 else (
            'power_on' if elapsed < 60 else 'inputs' if elapsed < 80 else 'final_rest')
        if desired != phase:
            phase = desired
            if phase == 'heads_up':
                cue('heads_up', 'In ungefähr zehn Sekunden einschalten; noch AUS lassen.')
            elif phase == 'power_on':
                cue('power_on', 'JETZT einmal einschalten. Keine Tasten/Sticks. Sobald sichtbar verbunden: VERBUNDEN + Enter. Nicht erneut einschalten.')
            elif phase == 'inputs':
                need(confirmed is not None, 'No connection confirmation by 60 seconds; no extension/retry')
                cue('inputs', 'JETZT A, beide Sticks und sanfte Bewegung; KDE-Eingaben beobachten.')
            elif phase == 'final_rest':
                cue('final_rest', 'JETZT ablegen. Aufnahme endet kontrolliert; keine Treiberänderung.')
        for line in lines:
            if line == 'verbunden' and 30 <= elapsed < 60 and confirmed is None:
                confirmed = elapsed
                cue('user_connected', 'Sichtbare Verbindung bestätigt; genauer Funkzeitpunkt bleibt unbewiesen. Bis zur nächsten Ansage keine Eingaben.')
            elif line == 'verbunden':
                cue('confirmation_not_accepted', 'Bestätigung außerhalb des Fensters oder bereits bestätigt; Ablauf unverändert.')
        if elapsed >= 89:
            cue('capture_finish', 'Aufnahme wird geschlossen. Controller/Dongle unverändert lassen.')
            return {'user_connected_at_seconds': confirmed, 'radio_connected_proven': False}
        sleep(min(.1, max(.000001, origin + 89 - clock())))


def execute(manifest, output, *, authorized=False, terminal=None, capture_factory=attach,
            clock=time.monotonic, sleep=time.sleep, emit=print):
    need(authorized is True, 'Separate capture approval flag required')
    checked = validate_manifest(manifest)
    need(os.geteuid() == 0 and sys.stdin.isatty() and sys.stdout.isatty(), 'Visible root terminal required')
    terminal = terminal or TerminalLines(sys.stdin.fileno())
    print('Nur nach konkreter Freigabe GO + Enter. Controller AUS; KDE-Test offen. STOP beendet.', flush=True)
    await_go(terminal, clock=clock, sleep=sleep)
    recorder = capture_factory(checked, output)
    stream, result, cues = None, None, []
    def recorded_emit(value):
        cues.append(value)
        stream.write((json.dumps(value, ensure_ascii=False) + '\n').encode())
        stream.flush()
        emit(value)
    try:
        recorder.start()
        stream = recorder._file('phase-cues.jsonl')
        observations = run_phases(recorder, terminal, clock=clock, sleep=sleep, emit=recorded_emit)
        result = recorder.finish()  # Recorder owns, fsyncs and closes cue stream too.
        need(result.get('passed') is True, 'RF recorder final audit failed; preserve evidence')
        summary = {'scope': SCOPE, 'capture': result, 'cue_count': len(cues), **observations,
                   'hardware_commands_sent_by_helper': False, 'drivers_changed': False,
                   'automatic_retry': False}
        return dict(summary, evidence=persist_result(output, summary, recorder.owner))
    except BaseException as error:
        cleanup = []
        try:
            result = recorder.abort(type(error).__name__ + ': ' + str(error))
        except BaseException as stop_error:
            cleanup.append('Owned recorder abort: ' + str(stop_error))
        try:
            persist_result(output, {'scope': SCOPE, 'capture': result,
                'primary_error': type(error).__name__ + ': ' + str(error),
                'cleanup_errors': cleanup, 'cue_count': len(cues), 'automatic_retry': False}, recorder.owner)
        except BaseException as persist_error:
            cleanup.append('Result persistence: ' + str(persist_error))
        try:
            emit({'event': 'stopped', 'primary_error': type(error).__name__ + ': ' + str(error),
                  'cleanup_errors': cleanup, 'capture': result})
        except BaseException:
            pass
        raise


def display(event):
    if 'instruction' in event:
        print(f"[{event['seconds_from_capture_request']:05.1f}s] {event['instruction']}", flush=True)
    else:
        print('STOPP: ' + event.get('primary_error', 'Beobachtung beendet; Bericht prüfen.'), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('show-plan')
    read = sub.add_parser('inspect', help='Separate approved root metadata read; no monitor open')
    read.add_argument('--authorize-read-only', action='store_true')
    prepare = sub.add_parser('prepare', help='Build manifest from saved successful preflight only')
    prepare.add_argument('--preflight', type=Path, required=True)
    prepare.add_argument('--manifest', type=Path, required=True)
    validate = sub.add_parser('validate')
    validate.add_argument('--manifest', type=Path, required=True)
    live = sub.add_parser('execute', help='Separate approved isolated capture; local GO required')
    live.add_argument('--manifest', type=Path, required=True)
    live.add_argument('--output', type=Path, required=True)
    live.add_argument('--authorize-rf-capture', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command in (None, 'show-plan'):
            value = plan()
        elif args.command == 'inspect':
            value = inspect(authorized=args.authorize_read_only)
        elif args.command == 'prepare':
            saved = read_json(args.preflight)
            need(saved.get('scope') == SCOPE and saved.get('read_only') is True and saved.get('ok') is True
                 and 'failure' not in saved
                 and saved.get('capture_started') is False, 'Successful matching preflight required')
            value = validate_manifest(saved['manifest'])
            Tracker(value['target']).observe(saved['snapshot'], 0, initial=True)
            fd = os.open(args.manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w') as stream:
                json.dump(value, stream, indent=2)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            value = {'manifest_prepared': True, 'hardware_access': False}
        elif args.command == 'validate':
            value = {'valid': True, 'hardware_access': False,
                     'manifest': validate_manifest(read_json(args.manifest))}
        else:
            def interrupted(signum, frame):
                raise KeyboardInterrupt('Signal ' + str(signum))
            for signum in (signal.SIGTERM, signal.SIGHUP):
                signal.signal(signum, interrupted)
            value = execute(read_json(args.manifest), args.output, authorized=args.authorize_rf_capture,
                            emit=display)
        print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except PreflightFailure as error:
        # stdout remains a parseable private report even on failure; exit stays nonzero.
        print(json.dumps(error.report, indent=2, ensure_ascii=False, allow_nan=False))
        print('STOPPED ' + str(error), file=sys.stderr)
        return 1
    except (CaptureHalt, OSError, ValueError, KeyError, KeyboardInterrupt, subprocess.SubprocessError) as error:
        print('STOPPED ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
