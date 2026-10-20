#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Existing isolated recorder attached to the explicitly authorized native test.

Import/attach do not inspect live device/process metadata or start processes.
Only start(), after authorization and local BEREIT, starts the bounded recorder.
No module, USB configuration or driver-binding operation exists in this module.
"""
import datetime as dt
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import select
import signal
import stat
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'tools/native/usb_capture'
SCOPE = 'native-motor-comparison-300-handover-twelve-pulses-capture-end-only'
DURATION, OUTER_TIMEOUT, TAIL = 450, 480, 30
PASSIVE_SCOPE = 'passive-hid-100a-300'
PASSIVE_DURATION, PASSIVE_OUTER_TIMEOUT = 300, 330
PASSIVE_SHORT_SCOPE = 'passive-hid-100a-90'
PASSIVE_SHORT_DURATION, PASSIVE_SHORT_OUTER_TIMEOUT = 90, 120
RF_SCOPE = 'passive-rf-109c-xpad-90'
PASSIVE_PROFILES = {
    PASSIVE_SCOPE: (PASSIVE_DURATION, PASSIVE_OUTER_TIMEOUT),
    PASSIVE_SHORT_SCOPE: (PASSIVE_SHORT_DURATION, PASSIVE_SHORT_OUTER_TIMEOUT),
}
GIB, MAX_LOG = 1024 ** 3, 16 * 1024 ** 2
ASSET_NAMES = ('setup.sh', 'guest-check.py', 'identity-check.py', 'state-check.py')


class CaptureHalt(RuntimeError):
    pass


def need(ok, message):
    if not ok:
        raise CaptureHalt(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def regular(path):
    need(stat.S_ISREG(path.lstat().st_mode), 'Expected regular non-symlink file: ' + str(path))


def validate_passive_target(target):
    """Validate approved cached metadata, without collecting any host metadata."""
    need(isinstance(target, dict) and set(target) == {
        'port', 'busnum', 'devnum', 'devpath', 'vid', 'pid', 'interfaces', 'sysfs_identity', 'boot_id'},
        'Explicit passive target metadata required')
    need(target['vid'] == '3537' and target['pid'] == '100a',
         'Passive profile supports only 3537:100a')
    need(isinstance(target['boot_id'], str) and re.fullmatch(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', target['boot_id']),
        'Current boot identity required')
    need(target['port'] == '8-6' and target['busnum'] == '8' and target['devpath'] == '6'
         and isinstance(target['devnum'], str) and re.fullmatch(r'[1-9][0-9]{0,2}', target['devnum'])
         and int(target['devnum']) <= 127, 'Only fresh bus 8 / port 8-6 target supported')
    need(target['interfaces'] == {
        '0': {'driver': 'xpad', 'endpoints': [2, 130]},
        '1': {'driver': 'usbhid', 'endpoints': [4, 132]}},
        'Expected xpad IF0 and usbhid IF1 with exact endpoints')
    value = target['sysfs_identity']
    need(isinstance(value, dict) and set(value) == {
        'st_dev', 'st_ino', 'parent_st_dev', 'parent_st_ino'}
        and all(type(v) is int and v >= (1 if k.endswith('ino') else 0) for k, v in value.items()),
        'Fresh sysfs device and parent instance metadata required')
    return target


def verify_sources(manifest):
    result = {}
    paths = [Path(__file__).absolute()] + [ASSETS / name for name in ASSET_NAMES]
    if isinstance(manifest.get('scope'), str) and manifest['scope'] in PASSIVE_PROFILES:
        paths.append(ROOT / 'tools/native/hid_sidechannel_capture.py')
    if manifest.get('scope') == RF_SCOPE:
        paths.extend([ASSETS / 'rf-identity-check.py', ROOT / 'tools/native/rf_link_capture.py',
                      ROOT / 'tools/native/rf_link_policy.py', ROOT / 'tools/native/hid_sidechannel_capture.py'])
    for path in paths:
        regular(path)
        relative, value = str(path.relative_to(ROOT)), digest(path)
        need(manifest.get('sha256', {}).get(relative) == value,
             'Source differs from approved manifest: ' + relative)
        result[relative] = value
    return result


def dumpcap_metadata():
    path = Path('/usr/bin/dumpcap')
    regular(path)
    value = path.stat()
    try:
        caps = os.getxattr(path, 'security.capability').hex()
    except OSError as error:
        if error.errno != errno.ENODATA:
            raise
        caps = None
    return {'uid': value.st_uid, 'gid': value.st_gid,
            'mode': oct(stat.S_IMODE(value.st_mode)), 'sha256': digest(path),
            'file_capability_xattr_hex': caps}


def marker_records(path):
    if not path.exists():
        return {}
    regular(path)
    need(path.stat().st_size <= MAX_LOG, 'Recorder log limit exceeded')
    records = {}
    for line in path.read_text().splitlines(keepends=True):
        if not line.endswith('\n'):
            continue  # Writer may still be completing an audit record.
        marker, _, value = line.strip().partition(' ')
        if marker.startswith(('MEASUREMENT_B_', 'STAGE4_IDENTITY_')) and marker.endswith('_JSON'):
            need(marker not in records, 'Duplicate recorder audit marker: ' + marker)
            records[marker] = json.loads(value)
    return records


def validate_ready(records, baseline, launched, now):
    pre = records.get('MEASUREMENT_B_PREFLIGHT_JSON', {})
    ready = records.get('MEASUREMENT_B_DUMPCAP_JSON', {})
    ident = records.get('STAGE4_IDENTITY_JSON', {})
    need(pre.get('preflight_passed') is True, 'Missing isolated preflight proof')
    need(ident.get('host_mounts_and_namespaces_unchanged') is True
         and ident.get('identity') == baseline['identity'], 'Missing immediate identity proof')
    need(ready.get('exe') == '/usr/bin/dumpcap' and ready.get('monitor_fds')
         and ready.get('raw_usb_absent') is True and ready.get('mountinfo_unchanged') is True,
         'No verified isolated dumpcap with monitor descriptor')
    need(ready.get('rights') == pre.get('rights') and ready.get('namespaces') == pre.get('ns'),
         'Recorder rights/namespaces differ from preflight')
    rights = ready['rights']
    need(all(int(rights.get(key, '-1'), 16) == 0
             for key in ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb'))
         and rights.get('NoNewPrivs') == '1', 'Capabilities or NoNewPrivs invalid')
    need(set(ready['namespaces']) == {'mnt', 'pid', 'net', 'ipc', 'uts', 'user'}
         and all(value != baseline['ns'][key] for key, value in ready['namespaces'].items()),
         'All six namespaces must be isolated')
    stamp = ready.get('checked_monotonic_ns', 0) / 1e9
    need(launched <= stamp <= now and now - stamp <= 2, 'Stale/future recorder readiness')
    return stamp


class Capture:
    def __init__(self, manifest, output):
        self.manifest, self.parent = manifest, Path(output)
        self.scope = manifest.get('scope')
        need(self.scope in (SCOPE, RF_SCOPE, *PASSIVE_PROFILES), 'Wrong native capture scope')
        self.rf = self.scope == RF_SCOPE
        self.passive = self.scope in PASSIVE_PROFILES or self.rf
        self.duration, self.outer_timeout = ((90, 120) if self.rf else
            PASSIVE_PROFILES[self.scope] if self.passive else (DURATION, OUTER_TIMEOUT))
        self.tail = 0 if self.passive else TAIL
        conf = manifest.get('usb_capture', {})
        need((conf.get('duration_seconds'), conf.get('outer_timeout_seconds')) == (self.duration, self.outer_timeout),
             'Unexpected recording time limits')
        ref = conf.get('dumpcap_file_metadata', {})
        need(set(ref) == {'uid', 'gid', 'mode', 'sha256', 'file_capability_xattr_hex'}
             and type(ref.get('uid')) is int and ref['uid'] == 0
             and type(ref.get('gid')) is int and 0 <= ref['gid'] < 2**32 - 1
             and isinstance(ref.get('sha256'), str) and len(ref['sha256']) == 64,
             'Fresh dumpcap provenance required')
        target = manifest['target']
        if self.passive and not self.rf:
            validate_passive_target(target)
        need(target['port'] == '8-6' and str(target['busnum']) == '8'
             and str(target['devpath']) == '6' and str(target['devnum']).isdigit()
             and 1 <= int(target['devnum']) <= 127, 'Only fresh bus 8 / port 8-6 identity supported')
        need(self.parent.is_dir() and not self.parent.is_symlink()
             and self.parent.resolve().parent == (ROOT / 'build/hardware-tests').resolve()
             and stat.S_IMODE(self.parent.stat().st_mode) == 0o700,
             'Expected private native evidence directory')
        self.owner = (self.parent.stat().st_uid, self.parent.stat().st_gid)
        self.source_hashes = verify_sources(manifest)
        self.rf_tracker = self.rf_log = None
        self.identity_asset = 'rf-identity-check.py' if self.rf else 'identity-check.py'
        if self.rf:
            from rf_link_policy import Tracker
            self.rf_tracker = Tracker(target)
        self.directory = self.parent / 'usb-capture'
        need(not os.path.lexists(self.directory), 'Capture output exists; never overwrite')
        self.process = self.observer = self.baseline = self.launched = None
        self.deadline = self.ready = self.supervisor = self.result = None
        self.started = self.stop_sent = False
        self.created_directory = False
        self.streams, self.last_check = [], 0
        self.dumpcap = None
        self.dumpcap_fd = self.capture_namespaces = None
        self.sources = None
        self.capture_started = None
        self.next_identity_check = 0

    def _file(self, name):
        fd = os.open(self.directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.fchown(fd, *self.owner)
        stream = os.fdopen(fd, 'wb')
        self.streams.append(stream)
        return stream

    def _object(self, name, value):
        stream = self._file(name)
        stream.write((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()

    def _metadata(self, asset, argument=None):
        argv = ['/usr/bin/python', '-I', '-B', '-c', self.sources[asset]]
        if argument is not None:
            argv.append(json.dumps(argument, sort_keys=True))
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=5, env={'PATH': '/usr/bin', 'LANG': 'C', 'TZ': 'UTC'}, close_fds=True)
        need(result.returncode == 0, 'Read-only check failed: ' + asset + ': ' + result.stderr.decode(errors='replace'))
        return json.loads(result.stdout)

    def _supervisor_identity(self):
        pid = str(self.process.pid)
        need(os.readlink('/proc/' + pid + '/exe') == '/usr/bin/timeout', 'Recorder supervisor executable changed')
        start = Path('/proc/' + pid + '/stat').read_text().rsplit(')', 1)[1].split()[19]
        return {'pid': self.process.pid, 'starttime': start}

    def _dumpcap_identity(self):
        """Locate only a descendant of this live supervisor, never a global name."""
        need(self._supervisor_identity() == self.supervisor, 'Supervisor identity changed')
        expected = self.capture_namespaces
        need(expected is not None, 'Missing verified capture namespaces')
        found, pending, seen = [], [self.process.pid], set()
        while pending:
            pid = pending.pop()
            need(pid not in seen and len(seen) < 24, 'Unexpected recorder process tree')
            seen.add(pid)
            proc = Path('/proc') / str(pid)
            try:
                pending.extend(int(value) for value in (proc / 'task' / str(pid) / 'children').read_text().split())
                if os.readlink(proc / 'exe') != '/usr/bin/dumpcap':
                    continue
                need({name: os.readlink(proc / 'ns' / name) for name in expected} == expected,
                     'Owned dumpcap namespace mismatch')
                found.append({'pid': pid, 'starttime': (proc / 'stat').read_text().rsplit(')', 1)[1].split()[19]})
            except FileNotFoundError:
                continue
        need(len(found) == 1, 'Expected exactly one isolated dumpcap descendant')
        return found[0]

    def start(self):
        need(not self.started and self.result is None, 'Recorder is single use; no automatic retry')
        self.started = True
        need(os.geteuid() == 0, 'Separately approved root coordinator required')
        need(callable(getattr(os, 'pidfd_open', None)) and callable(getattr(signal, 'pidfd_send_signal', None)),
             'Existing Python runtime lacks required process-identity protection')
        need(verify_sources(self.manifest) == self.source_hashes, 'Sources changed after attach')
        self.sources = {name: (ASSETS / name).read_text() for name in
                        (*ASSET_NAMES, 'rf-identity-check.py') if name in ASSET_NAMES or self.rf}
        need(all(hashlib.sha256(value.encode()).hexdigest() == self.source_hashes[
                 'tools/native/usb_capture/' + name] for name, value in self.sources.items()),
             'Capture source changed while reading; stop before metadata')
        need(dumpcap_metadata() == self.manifest['usb_capture']['dumpcap_file_metadata'], 'dumpcap provenance changed')
        need(shutil.disk_usage(self.parent).free >= 5 * GIB, 'At least 5 GiB free required')
        self.directory.mkdir(mode=0o700)
        self.created_directory = True
        os.chown(self.directory, *self.owner)
        try:
            self._object('capture-manifest.json', self.manifest)
            host = self._metadata('state-check.py')
            identity_argument = {'target': self.manifest['target']}
            if self.passive:
                identity_argument['capture_profile'] = self.scope
            ident = self._metadata(self.identity_asset, identity_argument)
            if self.rf:
                self.rf_tracker.observe(ident, time.monotonic(), initial=True)
                self.rf_log = self._file('rf-observations.jsonl')
                self._record_rf(ident, 'initial')
            self.baseline = dict(host, identity=ident, target=self.manifest['target'])
            if self.passive:
                self.baseline['capture_profile'] = self.scope
            self._object('host-before.json', host)
            self._object('identity-before.json', ident)
            self._object('dumpcap-file-metadata.json', self.manifest['usb_capture']['dumpcap_file_metadata'])
            for name in self.sources:
                stream = self._file(name)
                stream.write(self.sources[name].encode())
                stream.close()
            self._object('source-hashes.json', self.source_hashes)
            argv = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2s', str(self.outer_timeout) + 's',
                '/usr/bin/env', '-i', 'PATH=/usr/bin', 'LANG=C', 'TZ=UTC', 'HOME=/',
                '/usr/bin/unshare', '--mount', '--propagation', 'private',
                '/usr/bin/bash', '-euc', self.sources['setup.sh'],
                self.scope if self.passive else 'native-motor-comparison',
                json.dumps(self.baseline, sort_keys=True), self.sources['guest-check.py'],
                self.sources[self.identity_asset]]
            self._object('command-argv.json', argv)
            self.observer = subprocess.Popen(['/usr/bin/timeout', '--signal=TERM', '--kill-after=2s',
                str(self.outer_timeout) + 's', '/usr/bin/udevadm', 'monitor', '--kernel', '--udev',
                '--property', '--subsystem-match=usb'], stdin=subprocess.DEVNULL,
                stdout=self._file('usb-udev-events.log'), stderr=self._file('udev-stderr.log'),
                close_fds=True, start_new_session=True)
            self.launched = time.monotonic()
            self.deadline = self.launched + self.duration
            self.process = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                stdout=self._file('original-usbmon8.pcapng'), stderr=self._file('capture.log'),
                close_fds=True, start_new_session=True)
            until = self.launched + 5
            while time.monotonic() < until:
                records = marker_records(self.directory / 'capture.log')
                need(self.process.poll() is None, 'Recorder exited before verified readiness')
                need(self.observer.poll() is None, 'Passive epoch observer exited before readiness')
                if 'MEASUREMENT_B_DUMPCAP_JSON' in records:
                    self.ready = validate_ready(records, self.baseline, self.launched, time.monotonic())
                    if self.passive:
                        self.capture_started = records['MEASUREMENT_B_DUMPCAP_JSON'].get('capture_started_monotonic_ns', 0) / 1e9
                        need(self.launched <= self.capture_started <= self.ready,
                             'Missing/future passive capture clock origin')
                        self.deadline = self.capture_started + self.duration
                    self.supervisor = self._supervisor_identity()
                    need(records.get('MEASUREMENT_B_SUPERVISOR_JSON') == self.supervisor,
                         'Sandbox supervisor differs from own recorder process')
                    self.capture_namespaces = dict(records['MEASUREMENT_B_DUMPCAP_JSON']['namespaces'])
                    candidate = self._dumpcap_identity()
                    self.dumpcap_fd = os.pidfd_open(candidate['pid'], 0)
                    need(self._dumpcap_identity() == candidate, 'dumpcap changed while pinning PID')
                    self.dumpcap = candidate
                    self._object('host-dumpcap-process.json', self.dumpcap)
                    self._object('recorder-ready.json', records)
                    self.check(0 if self.passive else 300 + TAIL + 15, 'initial-ready')
                    print(('USB-AUFNAHME LÄUFT und Isolation geprüft. Vorbereitung läuft seit Recorderstart.'
                           if self.passive else
                           'USB-AUFNAHME LÄUFT und Isolation geprüft. Es folgt der native Countdown.'), flush=True)
                    return
                time.sleep(.02)
            raise CaptureHalt('No verified isolated recorder readiness within five seconds')
        except BaseException as error:
            self._finalize(tail=False, failure=type(error).__name__ + ': ' + str(error))
            raise

    def check(self, required_remaining_seconds, stage):
        need(self.started and self.ready is not None and self.result is None, 'Recorder is not ready')
        need(isinstance(required_remaining_seconds, (int, float))
             and math.isfinite(required_remaining_seconds) and required_remaining_seconds >= 0,
             'Invalid recording budget')
        now = time.monotonic()
        need(now + required_remaining_seconds <= self.deadline, 'Insufficient recording time before ' + stage)
        need(self.process.poll() is None, 'Recorder exited early at ' + stage)
        need(self.observer.poll() is None, 'Epoch observer exited at ' + stage)
        need(self.dumpcap_fd is not None, 'Missing pinned dumpcap process')
        poller = select.poll()
        poller.register(self.dumpcap_fd, select.POLLIN | select.POLLHUP | select.POLLERR)
        need(not poller.poll(0), 'dumpcap exited before supervisor at ' + stage)
        if self.passive and now >= self.next_identity_check:
            identity = self._metadata(self.identity_asset, {
                'target': self.manifest['target'], 'capture_profile': self.scope})
            if self.rf:
                self._record_rf(identity, stage)
                self.rf_tracker.observe(identity, time.monotonic())
            else:
                need(identity == self.baseline['identity'], 'Passive target instance/bindings changed at ' + stage)
            self.next_identity_check = time.monotonic() + 1
        if now >= self.last_check:
            need(shutil.disk_usage(self.parent).free >= GIB, 'Less than 1 GiB free at ' + stage)
            for name, limit in (('capture.log', MAX_LOG), ('usb-udev-events.log', MAX_LOG),
                               ('udev-stderr.log', MAX_LOG), ('original-usbmon8.pcapng', 2_000_000_000)):
                need((self.directory / name).stat().st_size < limit, 'Capture/log size limit: ' + name)
            need((self.directory / 'udev-stderr.log').stat().st_size == 0, 'Epoch observer error')
            self.last_check = now + .25

    def _record_rf(self, snapshot, stage):
        need(self.rf_log is not None, 'Missing RF observation log')
        self.rf_log.write((json.dumps({'utc': utc(), 'monotonic_ns': time.monotonic_ns(),
            'stage': stage, 'snapshot': snapshot}, ensure_ascii=False) + '\n').encode())
        self.rf_log.flush()

    def _stop(self):
        if self.process is None or self.process.poll() is not None:
            return
        if self.stop_sent:
            self.process.wait(timeout=5)  # Never send a second stop signal.
            return
        current = self._supervisor_identity()
        if self.supervisor is not None:
            need(current == self.supervisor, 'Refuse to signal changed recorder PID/start time')
        else:
            self.supervisor = current  # Own live Popen child, before readiness.
        if self.dumpcap is not None:
            # pidfd pins this process even if its numeric PID is later reused.
            need(self.dumpcap_fd is not None, 'Cannot safely signal dumpcap without pinned process')
            need(self._dumpcap_identity() == self.dumpcap,
                 'Refuse to signal changed dumpcap PID/start time')
            signal.pidfd_send_signal(self.dumpcap_fd, signal.SIGINT)
            self.stop_sent = True
        else:
            # Before a verified child exists, only abort the exact own timeout.
            # Such a run cannot pass, and requires a new explicit authorization.
            self.process.send_signal(signal.SIGINT)
            self.stop_sent = True
        self.process.wait(timeout=5)

    def finish(self):
        """Finalize passive recording, or legacy capture after native END/cleanup."""
        return self._finalize(tail=not self.passive)

    def abort(self, reason):
        """Stop only this recorder; preserve the failed capture and all evidence."""
        return self._finalize(tail=False, failure=str(reason))

    def _finalize(self, tail, failure=None):
        if self.result is not None:
            return self.result
        result = {'passed': False, 'failure': failure, 'finalization_started_utc': utc(),
                  'duration_ceiling_seconds': self.duration, 'post_end_tail_seconds': self.tail if tail else 0}
        try:
            if tail and self.ready is not None and self.process is not None:
                until = time.monotonic() + TAIL
                print('Motorlauf beendet. USB-Aufnahme läuft noch 30 Sekunden passiv für den Rückweg.', flush=True)
                while time.monotonic() < until:
                    self.check(max(0, until - time.monotonic()), 'post-END tail')
                    time.sleep(min(.1, max(0, until - time.monotonic())))
            self._stop()
        except BaseException as error:
            result['failure'] = (result.get('failure') or '') + '; capture stop/tail: ' + str(error)
            try:
                self._stop()
            except BaseException as stop_error:
                result['stop_error'] = str(stop_error)
        finally:
            if self.observer is not None and self.observer.poll() is None:
                try:
                    self.observer.terminate()
                    self.observer.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired) as error:
                    result['observer_stop_error'] = str(error)
        if not self.created_directory:
            result['failure'] = result.get('failure') or 'Recorder did not start'
            self.result = result
            return result
        records = {}
        try:
            records = marker_records(self.directory / 'capture.log')
            result['markers'] = records
            result['capture_chain_exit_status'] = None if self.process is None else self.process.poll()
            need(self.process is None or self.process.poll() is not None, 'Recorder alive; original not yet immutable')
            need(self.process is not None and self.ready is not None,
                 'No verified recorder was started')
            if self.process is not None:
                guest = records.get('MEASUREMENT_B_RESULT_JSON', {})
                need(guest.get('passed') is True and guest.get('dumpcap_reaped') is True,
                     'Missing successful final sandbox/descriptor audit')
                need(self.process.returncode == 0,
                     'Recorder supervisor failed')
            if self.baseline is not None:
                after = self._metadata('state-check.py')
                self._object('host-after.json', after)
                expected = {key: value for key, value in self.baseline.items() if key not in ('identity', 'target', 'capture_profile')}
                result['host_mounts_namespaces_node_unchanged'] = after == expected
                need(after == expected, 'Host mount/node/namespace changed')
                if self.passive:
                    identity = self._metadata(self.identity_asset, {
                        'target': self.manifest['target'], 'capture_profile': self.scope})
                    self._object('identity-after.json', identity)
                    if self.rf:
                        self._record_rf(identity, 'final')
                        self.rf_tracker.observe(identity, time.monotonic(), final=True)
                        result['rf_epochs'] = self.rf_tracker.epochs
                        result['rf_topology_pause_bindings_verified'] = True
                    else:
                        need(identity == self.baseline['identity'], 'Passive target changed before final audit')
                        result['target_identity_bindings_pause_unchanged'] = True
            original = self.directory / 'original-usbmon8.pcapng'
            need(original.exists(), 'Missing original capture')
            if original.exists():
                regular(original)
                with original.open('rb') as stream:
                    need(stream.read(4) == b'\x0a\x0d\x0d\x0a', 'Missing PCAPNG section header')
                result['original_sha256'], result['original_bytes'] = digest(original), original.stat().st_size
            result['passed'] = result.get('failure') is None and 'observer_stop_error' not in result
        except BaseException as error:
            result['failure'] = (result.get('failure') or '') + '; final verification: ' + str(error)
        if self.baseline is not None and not (self.directory / 'host-after.json').exists():
            # Preserve host-return metadata even when the guest audit failed.
            try:
                after = self._metadata('state-check.py')
                self._object('host-after.json', after)
                expected = {key: value for key, value in self.baseline.items() if key not in ('identity', 'target', 'capture_profile')}
                result['host_mounts_namespaces_node_unchanged'] = after == expected
            except BaseException as error:
                result['host_after_error'] = str(error)
                result['passed'] = False
        for stream in self.streams:
            if not stream.closed:
                try:
                    stream.flush()
                    os.fsync(stream.fileno())
                except BaseException as error:
                    result.setdefault('stream_sync_errors', []).append(str(error))
                    result['failure'] = (result.get('failure') or '') + '; evidence sync: ' + str(error)
                    result['passed'] = False
                finally:
                    try:
                        stream.close()
                    except BaseException as error:
                        result.setdefault('stream_close_errors', []).append(str(error))
                        result['failure'] = (result.get('failure') or '') + '; evidence close: ' + str(error)
                        result['passed'] = False
        if self.dumpcap_fd is not None:
            os.close(self.dumpcap_fd)
            self.dumpcap_fd = None
        result['completed_utc'] = utc()
        immutable = ((self.observer is None or self.observer.poll() is not None)
            and (self.process is None or (self.process.poll() is not None
            and records.get('MEASUREMENT_B_RESULT_JSON', {}).get('dumpcap_reaped') is True)))
        result['checksum_manifest_verified'] = False
        if immutable:
            stream = None
            try:
                paths = sorted(path for path in self.directory.iterdir() if path.is_file())
                stream = self._file('SHA256SUMS')
                for path in paths:
                    stream.write((digest(path) + '  ' + path.name + '\n').encode())
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()
                for line in (self.directory / 'SHA256SUMS').read_text().splitlines():
                    value, name = line.split('  ', 1)
                    need(digest(self.directory / name) == value, 'Capture checksum mismatch')
                result['checksum_manifest_verified'] = True
            except BaseException as error:
                result['passed'] = False
                result['failure'] = (result.get('failure') or '') + '; checksum finalization: ' + str(error)
            finally:
                if stream is not None and not stream.closed:
                    stream.close()
        # Only declare success AFTER checksum verification. The outcome itself
        # is written afterward; its digest is returned to the native coordinator
        # and covered by that coordinator's result.json/SHA256SUMS chain.
        if not result['checksum_manifest_verified']:
            result['passed'] = False
        outcome_bytes = (json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode()
        outcome_digest = hashlib.sha256(outcome_bytes).hexdigest()
        self._object('capture-outcome.json', result)
        result['capture_outcome_sha256'] = outcome_digest
        self.result = result
        return result


def attach(manifest, output):
    return Capture(manifest, output)
