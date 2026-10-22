# SPDX-License-Identifier: GPL-2.0-only
"""Qt adapter with isolated demo and asynchronous, read-only local snapshots."""
import time
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QRunnable, QThreadPool, QTimer
from PySide6.QtGui import QDesktopServices

from i18n import CATALOGS, choose_language
from model import Preview, SITUATIONS, LINKS
from status import Collector
from status_view import present


class JobSignals(QObject):
    finished = Signal(object)


class StatusJob(QRunnable):
    def __init__(self, collector):
        super().__init__()
        self.collector = collector
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.collector.collect()
        except Exception:
            # No exception text/private paths in the UI. Never reuse an old result.
            result = None
        self.signals.finished.emit(result)


class BackendJob(QRunnable):
    def __init__(self, submission):
        super().__init__()
        self.submission = submission
        self.signals = JobSignals()

    def run(self):
        self.signals.finished.emit((self.submission, self.submission.run()))


class CenterModel(QObject):
    changed = Signal()
    dialogRequested = Signal()
    resultRequested = Signal()
    backendDialogRequested = Signal()
    setupDialogRequested = Signal()

    def __init__(self, settings, system_language='en', opener=None, *, demo=True, collector=None,
                 rehearsal=None, execution=None, calibration_preview=False, calibration_factory=None):
        super().__init__()
        self.settings = settings
        self.language_code = choose_language(settings.value('language', None), system_language)
        self.preview = Preview()
        self.index = 0
        self.preference_error = False
        self.link_error = False
        self.opener = opener or QDesktopServices.openUrl
        self.demo = demo
        if calibration_preview and (not demo or collector is not None
                                    or rehearsal is not None or execution is not None):
            raise ValueError('Calibration preview requires an isolated simulation')
        from calibration_bridge import CalibrationPreview
        self.calibration_preview = CalibrationPreview(enabled=calibration_preview, parent=self)
        if calibration_factory is not None:
            if demo or rehearsal is not None or calibration_preview:
                raise ValueError('Live calibration cannot use simulated modes')
            from tmr_bridge import CalibrationLive
            self.calibration_preview = CalibrationLive(calibration_factory, parent=self,
                                                       allow_open=self.can_begin_calibration)
            self.calibration_preview.changed.connect(self.changed.emit)
        if rehearsal is not None and (not demo or collector is not None):
            raise ValueError('Backend rehearsal must not use real status evidence')
        if execution is not None:
            from package_client import ExecutionTransactions
            if demo or rehearsal is not None or not isinstance(execution, ExecutionTransactions):
                raise ValueError('Package execution requires a separate reviewed coordinator')
        self.execution = execution
        self.rehearsal = rehearsal if execution is None else execution
        self.backend_job = None
        self.inspection_job = None
        self.setup_job = None
        if execution is not None and hasattr(execution, "initial_inspection"):
            QTimer.singleShot(0, self.inspectPackages)
        self.collector = collector if collector is not None else Collector()
        self.snapshot = None
        self.busy = False
        self.failed = False
        self.received_at = None
        self.job = None
        self.age_timer = QTimer(self)
        self.age_timer.setInterval(10000)
        self.age_timer.timeout.connect(self.changed.emit)
        if not demo:
            self.age_timer.start()

    @Property(bool, constant=True)
    def isDemo(self):
        return self.demo

    @Property(QObject, constant=True)
    def stickCalibration(self):
        return self.calibration_preview

    def calibration_in_use(self):
        return bool(getattr(self.stickCalibration, 'inUse', False))

    def can_begin_calibration(self):
        tx = self.execution
        return (self.backend_job is None and self.inspection_job is None and self.setup_job is None
                and (tx is None or not tx.uncertain and tx.state not in (
                    'loading', 'editing', 'checking', 'review', 'running', 'checking_updates',
                    'setup_review', 'setup_running', 'setup_failed')))

    @Property(bool, notify=changed)
    def canCalibrate(self):
        return self.stickCalibration.available and self.can_begin_calibration() and not self.calibration_in_use()

    @Property(bool, constant=True)
    def isRehearsal(self):
        return self.rehearsal is not None and self.execution is None

    @Property(bool, constant=True)
    def hasTransactions(self):
        return self.rehearsal is not None

    @Property(bool, notify=changed)
    def reading(self):
        return self.busy

    @Slot()
    def refresh(self):
        if self.demo or self.busy:
            return
        self.snapshot = None
        self.received_at = None
        self.failed = False
        self.busy = True
        self.changed.emit()
        self.job = StatusJob(self.collector)
        self.job.signals.finished.connect(self.receive)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object)
    def receive(self, snapshot):
        self.snapshot = snapshot
        self.failed = snapshot is None
        self.busy = False
        self.received_at = time.monotonic()
        self.job = None
        self.changed.emit()

    @Property(str, notify=changed)
    def language(self):
        return self.language_code

    @Property('QVariantMap', notify=changed)
    def strings(self):
        result = dict(CATALOGS[self.language_code])
        if self.execution is not None:
            for key, value in tuple(result.items()):
                if key.startswith('packages_'):
                    result['backend_' + key[len('packages_'):]] = value
            bundle = getattr(self.execution, 'bundle', None)
            if bundle is not None and bundle.release_assets and self.execution.operation == 'install':
                result['backend_prepare'] = result['release_prepare']
                result['backend_intro'] = result['release_intro']
        return result

    @Property('QVariantList', notify=changed)
    def scenarios(self):
        return [self.strings['scenario_' + s.key] for s in SITUATIONS]

    @Property(int, notify=changed)
    def scenarioIndex(self):
        return self.index

    @Property('QVariantMap', notify=changed)
    def view(self):
        s, t = self.preview.situation, self.strings
        if not self.demo:
            result = present(self.snapshot, t, busy=self.busy, failed=self.failed,
                             stale=self.received_at is not None and time.monotonic() - self.received_at > 60)
            result.update(settingsError=t['error_settings'] if self.preference_error else '',
                          linkError=t['error_link'] if self.link_error else '')
            if self.execution is not None:
                tx = self.execution
                update_enabled = (getattr(tx, 'bundle', None) is not None
                                  and tx.bundle.trust.release_policy is not None)
                result.update(updateVisible=update_enabled,
                              canCheckUpdates=hasattr(tx, 'can_check_updates') and tx.can_check_updates()
                              and self.inspection_job is None,
                              checkingUpdates=tx.state == 'checking_updates')
                result.update(canInstall=tx.transport is not None and tx.state not in ('editing', 'checking', 'review', 'running')
                              and bool(tx.available('install')),
                              canRemove=tx.transport is not None and tx.state not in ('editing', 'checking', 'review', 'running')
                              and bool(tx.available('remove')))
                if tx.transport is not None:
                    result['requirements'] = t['package_plan_first']
                if tx.state == 'loading':
                    result.update(notice=t['packages_checking'], noticeWarning=False)
                elif tx.state == 'setup_failed':
                    result.update(notice=t['setup_failed'] + ' · ' + tx.error, noticeWarning=True)
                elif tx.state.startswith('setup_'):
                    result.update(notice=t['setup_notice'], noticeWarning=True)
                elif tx.state == 'blocked':
                    result.update(notice=t['packages_unavailable'] + ' · ' + tx.error, noticeWarning=True)
                if tx.state == 'checking_updates':
                    result.update(notice=t['signed_updates_checking'], noticeWarning=False)
                elif getattr(tx, 'update_error', ''):
                    result.update(notice=t['signed_updates_failed'] + ' · ' + tx.update_error, noticeWarning=True)
                elif getattr(tx, 'update_result', ''):
                    result.update(notice=t['signed_updates_verified'] + ' · ' + tx.update_result, noticeWarning=False)
                if tx.uncertain:
                    result.update(driver=t['unknown'], module=t['unknown'], manager=t['unknown'],
                                  notice=t['backend_changes_possible'], noticeWarning=True)
            if self.calibration_in_use():
                result.update(canInstall=False, canRemove=False, canCheckUpdates=False)
            return result
        result = {
            'installed': s.installed, 'loaded': s.loaded, 'receiver': s.receiver,
            'connected': s.connected, 'supported': s.supported, 'headers': s.headers,
            'canInstall': self.preview.can_install, 'canRemove': self.preview.can_remove,
            'notice': t[s.notice], 'noticeWarning': not (s.supported and s.headers) or s.key in (
                'offline', 'corrupt', 'incomplete', 'package', 'cancelled', 'removal'),
            'os': ('Garuda Linux' if s.supported else t['unsupported_name']) + ' · x86_64',
            'kernel': '7.x · ' + t['example'],
            'driver': ('0.1.0.alpha3-16 · ' + t['demo']) if s.installed else t['not_installed'],
            'module': '0.1.0.alpha3 · ' + t['loaded'] if s.loaded else t['not_loaded'],
            'manager': t['manager_active' if s.loaded else 'manager_inactive'],
            'dongle': t['detected' if s.receiver else 'not_detected'],
            'controller': t['connected'] if s.connected else t['controller_off' if s.receiver and s.loaded else 'unknown'],
            'requirements': t['unsupported' if not s.supported else 'prerequisites' if s.headers else 'requirements_missing'],
            'settingsError': t['error_settings'] if self.preference_error else '',
            'linkError': t['error_link'] if self.link_error else '',
        }
        if self.rehearsal is not None:
            tx = self.rehearsal
            installed = 'gamesir-native-dkms' in tx.installed
            result.update(installed=installed, loaded=False, receiver=False, connected=False,
                          canInstall=tx.state not in ('editing', 'review', 'running') and bool(tx.available('install')),
                          canRemove=tx.state not in ('editing', 'review', 'running') and bool(tx.available('remove')),
                          os='CachyOS · x86_64 · ' + t['example'], kernel=tx.port.host.kernel,
                          driver=('0.1.0.offline-1 · ' + t['backend_badge']) if installed else t['not_installed'],
                          notice=t['backend_notice'], requirements=t['backend_badge'], noticeWarning=True)
            if tx.uncertain:
                result.update(installed=False, driver=t['unknown'], module=t['unknown'],
                              manager=t['unknown'], notice=t['backend_changes_possible'])
        return result

    @Property('QVariantMap', notify=changed)
    def backend(self):
        tx, t = self.rehearsal, self.strings
        if tx is None:
            return {'state': 'disabled', 'components': [], 'review': '', 'message': '',
                    'verifiedSuccess': False, 'successTitle': ''}
        summary = tx.summary()
        review = ''
        if summary:
            versions = {a['component']: a['version'] for a in summary['artifacts']}
            before = dict(tx.session.plan.host.installed)
            rows = [f"{package} · {versions.get(c, before.get(package, ''))}"
                    for c, package in zip(tx.session.plan.request.components, summary['packages'])]
            if self.execution is not None:
                rows += [t['packages_target'] + ' ' + tx.session.plan.host.distribution + ' · '
                         + tx.session.plan.host.kernel]
                for artifact in summary['artifacts']:
                    rows += [artifact['component'] + ' · SHA256 ' + artifact['sha256'],
                             artifact['source_commit'] + ' · ' + artifact['tag']]
                bundle = getattr(tx, 'bundle', None)
                if bundle is not None and bundle.release_assets:
                    rows += [a.url for a in bundle.release_assets
                             if a.component in tx.session.plan.request.components and tx.operation == 'install']
                    if bundle.signed_release is not None:
                        rows += [t['signed_updates_verified'] + ' · ' + str(bundle.signed_release.revision)]
            effects = [t.get('effect_' + e, t['effect_package_metadata']) for e in summary['hook_effects']]
            review = (t['backend_packages'] + '\n' + '\n'.join(rows) + '\n\n'
                      + t['backend_effects'] + '\n' + '\n'.join(dict.fromkeys(effects))
                      + '\n\n' + t['backend_preserved'] + '\n' + t['backend_no_activation'])
        message = ''
        if tx.state == 'cancelled' or tx.outcome and tx.outcome.state == 'cancelled':
            message = t['backend_cancelled']
        elif tx.outcome:
            success = tx.outcome.state == ('verified_success' if self.execution is not None else 'simulated_success')
            message = t['backend_success'] if success else t['backend_failed']
            if tx.outcome.error:
                message += '\n' + t['backend_code'] + ': ' + tx.outcome.error
            if not success and tx.outcome.changes_possible:
                message += '\n\n' + t['backend_changes_possible']
        elif tx.state == 'checking':
            bundle = getattr(tx, 'bundle', None)
            message = (t['release_checking'] if bundle is not None and bundle.release_assets
                       and tx.operation == 'install' else t['packages_checking'])
        elif tx.error:
            message = t['backend_blocked'] + '\n' + t['backend_code'] + ': ' + tx.error
        verified = (self.execution is not None and tx.outcome is not None
                    and tx.outcome.state == 'verified_success')
        return {'state': tx.state, 'operation': tx.operation, 'review': review, 'message': message,
                'verifiedSuccess': verified,
                'successTitle': t['packages_installed' if tx.operation == 'install' else 'packages_removed'] if verified else '',
                'components': [{'key': c, 'label': t['component_' + c], 'selected': c in tx.selected,
                                'available': c in tx.available(tx.operation)}
                               for c in ('core', 'steam', 'gamescope', 'bridge')]}

    @Property('QVariantMap', notify=changed)
    def setup(self):
        tx, t = self.execution, self.strings
        if tx is None or not hasattr(tx, 'request_setup'):
            return {'state': 'disabled', 'offer': False, 'summary': '', 'message': '', 'success': False}
        summary = ''
        if tx.setup_review is not None:
            data = tx.setup_review.summary()
            summary = t['setup_counts'].format(files=data['files'], directories=data['directories'])
            summary += '\n\n' + '\n'.join(data['directory_paths']) + '\n' + t['setup_policy_path']
        message = ''
        if tx.state == 'setup_done': message = t['setup_success']
        elif tx.state == 'setup_failed':
            message = t['setup_failed'] + '\n' + tx.error
            if tx.setup_result and tx.setup_result.changes_possible:
                message += '\n' + t['setup_partial']
        return {'state': tx.state, 'offer': tx.state == 'setup_required', 'summary': summary,
                'message': message, 'success': tx.state == 'setup_done'}

    @Slot()
    def requestSetup(self):
        if self.calibration_in_use(): return
        if self.execution is not None and hasattr(self.execution, 'request_setup') and self.execution.request_setup():
            self.changed.emit()
            self.setupDialogRequested.emit()

    @Slot()
    def confirmSetup(self):
        if self.calibration_in_use(): return
        if self.execution is None or not hasattr(self.execution, 'begin_setup'): return
        session = self.execution.begin_setup()
        if session is None: return
        self.setup_job = BackendJob(session)
        self.setup_job.signals.finished.connect(self.receiveSetup)
        self.changed.emit()
        QThreadPool.globalInstance().start(self.setup_job)

    @Slot(object)
    def receiveSetup(self, result):
        self.execution.receive_setup(*result)
        self.setup_job = None
        self.changed.emit()

    @Slot()
    def cancelSetup(self):
        if self.execution is not None and hasattr(self.execution, 'cancel_setup') and self.execution.cancel_setup():
            self.changed.emit()

    @Slot()
    def finishSetup(self):
        if self.execution is not None and hasattr(self.execution, 'finish_setup') and self.execution.finish_setup():
            self.changed.emit()
            self.inspectPackages()

    @Slot(str, bool)
    def selectBackendComponent(self, component, checked):
        if self.rehearsal is not None and self.rehearsal.select(component, checked):
            self.changed.emit()

    def startInspection(self, task):
        if task is None or self.inspection_job is not None:
            return
        self.inspection_job = BackendJob(task)
        self.inspection_job.signals.finished.connect(self.receiveInspection)
        self.changed.emit()
        QThreadPool.globalInstance().start(self.inspection_job)

    @Slot()
    def inspectPackages(self):
        if self.execution is not None and hasattr(self.execution, 'initial_inspection'):
            self.startInspection(self.execution.initial_inspection())

    @Slot(object)
    def receiveInspection(self, result):
        task, data = result
        self.execution.receive_inspection(task, data)
        self.inspection_job = None
        self.changed.emit()

    @Slot()
    def checkUpdates(self):
        if self.calibration_in_use(): return
        if self.execution is not None and self.inspection_job is None:
            self.startInspection(self.execution.begin_update_check())

    @Slot()
    def cancelUpdateCheck(self):
        if self.execution is not None and self.execution.state == 'checking_updates':
            self.execution.cancel()
            self.changed.emit()

    @Slot()
    def prepareBackend(self):
        if self.calibration_in_use(): return
        if self.execution is not None and hasattr(self.execution, 'begin_preparation'):
            if self.inspection_job is None:
                self.startInspection(self.execution.begin_preparation())
            return
        if self.rehearsal is not None:
            self.rehearsal.prepare()
            self.changed.emit()

    @Slot()
    def confirmBackend(self):
        if self.calibration_in_use(): return
        if self.rehearsal is None:
            return
        submission = self.rehearsal.begin()
        if submission is None:
            return
        self.changed.emit()
        self.backend_job = BackendJob(submission)
        self.backend_job.signals.finished.connect(self.receiveBackend)
        QThreadPool.globalInstance().start(self.backend_job)

    @Slot(object)
    def receiveBackend(self, result):
        submission, outcome = result
        if self.rehearsal is not None:
            self.rehearsal.finish(submission, outcome)
        self.backend_job = None
        self.changed.emit()

    @Slot()
    def cancelBackend(self):
        if self.rehearsal is not None and self.rehearsal.cancel():
            self.changed.emit()

    @Property('QVariantMap', notify=changed)
    def dialog(self):
        action = self.preview.pending or 'install'
        return {'title': self.strings[action + '_dialog'], 'body': self.strings[action + '_plan']}

    @Property('QVariantMap', notify=changed)
    def result(self):
        keys = self.preview.result
        return {'title': self.strings[keys[0]], 'body': self.strings[keys[1]], 'tone': keys[2]} if keys else {
            'title': '', 'body': '', 'tone': 'neutral'}

    @Slot(str)
    def setLanguage(self, code):
        if code not in CATALOGS:
            return
        self.language_code = code
        self.settings.setValue('language', code)
        self.settings.sync()
        self.preference_error = self.settings.status() != self.settings.Status.NoError
        self.changed.emit()

    @Slot(int)
    def selectScenario(self, index):
        if not self.demo or self.rehearsal is not None:
            return
        try:
            self.preview.select(index)
        except ValueError:
            return
        self.index = index
        self.changed.emit()

    @Slot(str)
    def request(self, action):
        if self.calibration_in_use(): return
        if self.rehearsal is not None:
            if self.rehearsal.request(action):
                self.changed.emit()
                self.backendDialogRequested.emit()
            return
        if self.demo and self.preview.request(action):
            self.changed.emit()
            self.dialogRequested.emit()

    @Slot()
    def cancel(self):
        if self.demo and self.rehearsal is None and self.preview.cancel():
            self.changed.emit()
            self.resultRequested.emit()

    @Slot()
    def confirm(self):
        if self.demo and self.rehearsal is None and self.preview.confirm():
            self.changed.emit()
            self.resultRequested.emit()

    @Slot()
    def dismissResult(self):
        self.preview.dismiss_result()
        self.changed.emit()

    @Slot(str)
    def openLink(self, name):
        if name not in LINKS:
            return
        self.link_error = not bool(self.opener(QUrl(LINKS[name])))
        self.changed.emit()
