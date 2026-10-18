# SPDX-License-Identifier: GPL-2.0-only
"""Explicitly armed live-window transport. Importing this module touches no devices.

Only start()/poll() on an approved session discover metadata or launch the
existing privileged worker. Tests inject Python dependencies, never CLI bypasses.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import stat
import time

from gamesir_gyro_guided import (ROOT, WorkerLink, private_target, write_json,
                                read_regular, worker_command)
from gamesir_gyro_worker import LIVE_KIND, LIVE_SOURCES
from gamesir_iio_buffer import snapshot_iio
from gamesir_imu_diagnostic import IIO_NAME, OBSERVED_AXIS_PROFILE, PROFILES
from gyro_reference import validate_samples
from gyro_view_model import LivePose


def source_hashes():
    result = {}
    for name in LIVE_SOURCES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('fixed live source missing or symlinked')
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def discover_native():
    """Metadata only, no device opens; never choose the first of multiple devices."""
    candidates = []
    for entry in Path('/sys/bus/iio/devices').glob('iio:device*'):
        try:
            if (entry/'name').read_text().strip() == IIO_NAME:
                candidates.append(entry.resolve(strict=True))
        except FileNotFoundError:
            continue  # Device may be appearing; nothing has been claimed yet.
    if len(candidates) > 1:
        raise ValueError('multiple native IIO devices; no automatic selection')
    if not candidates:
        return None
    directory = candidates[0]
    result = snapshot_iio(directory, Path('/dev')/directory.name)
    if result['buffer_enable'] != '0' or result['buffer_stream_active'] != '0':
        raise ValueError('IIO buffer already active; no takeover')
    return result


def manifest_for(snapshot, profile):
    if type(profile) is not int or profile not in PROFILES:
        raise ValueError('explicit experimental profile required')
    return {'schema_version': 1, 'kind': LIVE_KIND, 'snapshot': snapshot,
            'source_sha256': source_hashes(), 'profile': profile,
            'axis_profile': OBSERVED_AXIS_PROFILE}


class LiveEvents:
    """Constant-memory, strict v1 parser; sample timestamps drive orientation."""
    def __init__(self, snapshot, profile):
        self.instance = snapshot['directory']+':'+':'.join(map(str,snapshot['iio_identity']))
        self.pose = LivePose(profile, OBSERVED_AXIS_PROFILE)
        self.state = 'new'
        self.started_ns = None
        self.last_row = None
        self.count = 0
        self.finished = None
        self.profile_changes = 0

    def select_profile(self, profile):
        # Keep transport identity/counter checks across display-only changes.
        gain = self.pose.gain
        self.pose = LivePose(profile, OBSERVED_AXIS_PROFILE)
        self.pose.gain = gain
        self.profile_changes += 1

    def accept(self, event, now_ns):
        if (not isinstance(event,dict) or type(event.get('protocol_version')) is not int or
                event['protocol_version'] != 1 or self.finished):
            raise ValueError('unexpected live protocol/version or event after finish')
        name = event.get('event')
        if name == 'ready':
            if (self.state != 'new' or event.get('capture_seconds','missing') is not None or
                    event.get('device_opened') is not False or event.get('buffer_modified') is not False):
                raise ValueError('unexpected live readiness')
            self.state = 'ready'
        elif name == 'capture_started':
            stamp = event.get('monotonic_ns')
            if (self.state != 'ready' or event.get('instance_id') != self.instance or
                    type(stamp) is not int or not 0 < stamp <= now_ns or now_ns-stamp > 10_000_000_000):
                raise ValueError('unexpected live start/instance/clock')
            self.started_ns, self.state = stamp, 'streaming'
        elif name == 'sample':
            row = event.get('row')
            if self.state != 'streaming' or not isinstance(row,dict):
                raise ValueError('sample outside live stream')
            if row.get('instance_id') != self.instance or row.get('source_kind') != 'iio_buffer':
                raise ValueError('wrong live sample instance/source')
            validate_samples(([self.last_row] if self.last_row else [])+[row],
                             250_000_000, allow_single=True)
            stamp = row['timestamp_ns']
            if stamp < self.started_ns or stamp > now_ns or now_ns-stamp > 1_000_000_000:
                raise ValueError('future, pre-start or stale sample')
            self.pose.integrator.feed(row)
            self.last_row = self.pose.integrator.previous_row
            self.count += 1
        elif name == 'finished':
            if (type(event.get('passed')) is not bool or type(event.get('restored')) is not bool or
                    type(event.get('observations')) is not int or event['observations'] < 0 or
                    not isinstance(event.get('cleanup_errors'),list)):
                raise ValueError('explicit live finish and rollback result required')
            if event['passed'] and (not event['restored'] or event.get('failure') is not None or
                                    event['cleanup_errors'] or event['observations'] != self.count):
                raise ValueError('inconsistent successful live finish')
            self.finished, self.state = event, 'finished'
        else:
            raise ValueError('unknown live event')
        return name


class LiveLink(WorkerLink):
    def __init__(self, process, events):
        super().__init__(process)
        self.events = events

    def accept_event(self,event):
        name = self.events.accept(event,time.monotonic_ns())
        if name != 'sample':
            self.pending.append(event)
            self.event_order.append(name)
        if name == 'finished':
            self.finished = event


def launch_worker(manifest, output, log):
    environment = os.environ.copy()
    environment.update(SUDO_ASKPASS='/usr/bin/ksshaskpass', LC_ALL='C.UTF-8')
    return subprocess.Popen(worker_command(manifest,output/'capture'), shell=False,
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,
                            env=environment,bufsize=0)


def verify_result(output, manifest):
    """Summary-only live evidence, independent of stdout. No raw recording."""
    path = output/'capture'
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private returned live summary directory required')
    expected = {'report.json','buffer-transaction.json'}
    allowed = expected|{'layout.json'}
    sums = {}
    for line in read_regular(path/'SHA256SUMS',16384).decode('ascii').splitlines():
        digest,name = line.split('  ',1)
        if (name not in allowed or name in sums or len(digest) != 64 or
                any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('invalid live summary checksum manifest')
        sums[name] = digest
    if not expected <= set(sums):
        raise ValueError('live cleanup evidence missing')
    if {entry.name for entry in path.iterdir()} != set(sums)|{'SHA256SUMS'}:
        raise ValueError('unexpected live summary files')
    data = {}
    for name,digest in sums.items():
        raw=read_regular(path/name,1_048_576)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('live summary checksum mismatch')
        data[name] = json.loads(raw)
    report,transaction = data['report.json'],data['buffer-transaction.json']
    if (not isinstance(report,dict) or not isinstance(transaction,dict) or
            report.get('session') != 'live_view' or report.get('raw_recording') is not False or
            report.get('capture_seconds','missing') is not None or
            report.get('restored') is not True or transaction.get('restored') is not True or
            transaction.get('errors') != [] or report.get('cleanup_errors') != [] or
            report.get('evidence_finalization_errors') or transaction.get('before') != manifest['snapshot']):
        raise ValueError('saved live restoration is not verified')
    return report


class LiveSession:
    """One manually armed session, no automatic retry or replacement adoption."""
    TERMINAL = ('done','error')

    def __init__(self, output, profile, *, discover=discover_native, snapshot=snapshot_iio,
                 launch=launch_worker, verify=verify_result, clock=time.monotonic):
        if os.geteuid() == 0:
            raise ValueError('live GUI must run as desktop user, not root')
        if type(profile) is not int or profile not in PROFILES:
            raise ValueError('explicit experimental profile required')
        self.output, self.profile = Path(output), profile
        self.discover,self.snapshot,self.launch,self.verify,self.clock = discover,snapshot,launch,verify,clock
        self.state = 'idle'
        self.message = 'Controller verbinden und Verbindung vorbereiten.'
        self.failure = None
        self.link = self.events = self.manifest = None
        self.restored = False
        self.stop_sent = False
        self.protocol_failed = False
        self.deadline = None
        self.last_discovery = -1.
        self.finalized = False

    def start(self):
        if self.state != 'idle':
            raise ValueError('one live attempt only')
        self.output = private_target(self.output)
        self.output.mkdir(mode=0o700)
        self.state = 'waiting'
        self.deadline = self.clock()+60
        self.message = 'Controller verbinden … warte auf den vorhandenen nativen Treiber.'

    def go(self):
        if self.state != 'ready':
            raise ValueError('worker must be ready before local Go')
        self.link.send('GO')
        self.state = 'starting'
        self.deadline = self.clock()+10
        self.message = 'Sensorstrom startet …'

    def select_profile(self, profile):
        if type(profile) is not int or profile not in PROFILES:
            raise ValueError('explicit experimental profile required')
        self.profile = profile
        if self.events:
            self.events.select_profile(profile)

    def stop(self, error=None):
        if error and self.failure is None:
            self.failure = str(error)
        if self.state in self.TERMINAL or self.state == 'stopping':
            return
        if not self.link:
            self.state = 'error' if self.failure else 'done'
            self.message = self.failure or 'Beendet; Sensorpuffer nicht geöffnet.'
            return
        self.state = 'stopping'
        self.deadline = self.clock()+120
        self.message = 'Stoppe Sensorstrom und prüfe die Rückstellung …'
        try:
            self.link.send('STOP')
            self.stop_sent = True
        except (OSError,ValueError) as exc:
            self.failure = self.failure or str(exc)
        finally:
            try:self.link.close_input()
            except OSError as exc:self.failure = self.failure or str(exc)

    def _finish(self, code):
        errors=[]
        try:
            report=self.verify(self.output,self.manifest)
            before=self.manifest['snapshot']
            if self.snapshot(before['directory'],before['device_node']) != before:
                raise ValueError('fresh IIO state differs; restoration not independently confirmed')
            self.restored=True
            if report.get('failure'):
                self.failure=self.failure or report['failure']
            if code != 0 or not self.link.finished:
                self.failure=self.failure or 'worker exit/final event not confirmed'
            if report.get('completed') is not True or report.get('stopped_by_user') is not True:
                self.failure=self.failure or 'live preview did not end through normal STOP'
            if report.get('observations') != self.events.count:
                self.failure=self.failure or 'live sample count differs from saved report'
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
            errors.append(str(exc));self.failure=self.failure or str(exc)
        for stream in (self.link.process.stdin,self.link.process.stdout):
            try:stream.close()
            except OSError as exc:errors.append(str(exc));self.failure=self.failure or str(exc)
        self.state='error' if self.failure else 'done'
        self.message = ('Beendet · ursprünglicher Sensorpuffer bestätigt.' if not self.failure else
                        f'Gestoppt: {self.failure} · Rückstellung '+('bestätigt.' if self.restored else 'NICHT bestätigt.'))
        try:
            write_json(self.output/'frontend-result.json',{
                'schema_version':1,'kind':'live_gyro_window','passed':not self.failure,
                'failure':self.failure,'restored_independently':self.restored,'worker_exit':code,
                'observations':self.events.count,'display_profile':self.profile,
                'display_profile_changes':self.events.profile_changes,'errors':errors,
                'calibration_verified':False,'raw_recording':False})
        except OSError as exc:
            self.failure=self.failure or str(exc);self.state='error'
            self.message+=' Abschlussbericht nicht gespeichert: '+str(exc)
        self.finalized=True

    def poll(self):
        if self.state in (*self.TERMINAL,'idle'):
            return
        now=self.clock()
        try:
            if self.state=='waiting':
                if now > self.deadline:
                    raise ValueError('kein eindeutiger nativer Controller innerhalb 60 Sekunden')
                if now-self.last_discovery < .5:
                    return
                self.last_discovery=now
                snap=self.discover()
                if snap is None:return
                self.manifest=manifest_for(snap,self.profile)
                write_json(self.output/'manifest.json',self.manifest)
                self.events=LiveEvents(snap,self.profile)
                fd=os.open(self.output/'worker.stderr.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as log:
                    process=self.launch(self.output/'manifest.json',self.output,log)
                self.link=LiveLink(process,self.events)
                self.state='authorizing';self.deadline=now+300
                self.message='Passwort nur im Systemfenster eingeben. Noch kein Sensorstart.'
            if not self.protocol_failed:
                self.link.pulse(heartbeat=self.state!='stopping')
                while (event:=self.link.pop()) is not None:
                    name=event['event']
                    if name=='ready' and self.state=='authorizing':
                        self.state='ready';self.deadline=now+900
                        self.message='Verbunden. Mit „Live starten“ direkt testen; kein fester Winkel nötig.'
                    elif name=='capture_started' and self.state=='starting':
                        self.state='running';self.deadline=None
                        self.message='LIVE · Bewegen, zentrieren und Empfindlichkeit ausprobieren. Ende mit Stopp.'
                    elif name=='finished':
                        if not event['passed']:self.failure=self.failure or event.get('failure') or 'worker failed'
                        if self.state!='stopping':
                            self.state='stopping';self.deadline=now+120
                        self.message='Sensorstrom beendet; Rückstellung wird geprüft …'
                if self.state=='running':
                    stamp=self.events.last_row['timestamp_ns'] if self.events.last_row else self.events.started_ns
                    if time.monotonic_ns()-stamp > 2_000_000_000:
                        raise ValueError('keine frischen Sensordaten; kein automatischer Reconnect')
            code=self.link.process.poll()
            if code is not None:
                self._finish(code)
            elif self.deadline is not None and now > self.deadline:
                if self.state=='stopping':
                    self.failure=self.failure or 'Rückstellung/Workerende nach 120 Sekunden nicht bestätigt'
                    self.state='error';self.message=self.failure+'; kein erzwungenes Beenden oder Reparaturversuch.'
                else:
                    raise ValueError('Zeitlimit für Vorbereitung/Start überschritten; kein Sensor-Dauerlimit')
        except Exception as exc:
            self.stop(exc)
            if self.link:
                self.protocol_failed=True
                # Force a broken pipe instead of letting a stalled writer wait;
                # the worker always restores before final process exit.
                self.link.process.stdout.close()
