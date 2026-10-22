# SPDX-License-Identifier: GPL-2.0-only
"""Asynchronous QML adapter for one explicit experimental permission session."""
import queue
import threading
from PySide6.QtCore import QObject, Property, Signal, Slot, QThread, QTimer, Qt
from stick_calibration import Calibration


class CalibrationWorker(QThread):
    result = Signal(int, object)

    def __init__(self, generation, factory, parent=None):
        super().__init__(parent)
        self.generation, self.factory = generation, factory
        self.stop_requested = threading.Event()
        self.commands = queue.Queue(maxsize=1)

    def submit(self, action, fields=None):
        try:
            self.commands.put_nowait((action, fields or {}))
            return True
        except queue.Full:
            return False

    def run(self):
        client = None
        selected = False
        try:
            client = self.factory(self.stop_requested.is_set)
            reply = client.call('list')
            self.result.emit(self.generation, reply)
            while not self.stop_requested.is_set():
                try:
                    action, fields = self.commands.get(timeout=0.05)
                except queue.Empty:
                    continue
                if self.stop_requested.is_set():
                    break
                reply = client.call(action, **fields)
                selected = selected or action == 'select'
                self.result.emit(self.generation, reply)
                if action == 'cancel' or reply.get('view') and not reply['view']['running']:
                    return
            # Cancellation during an outstanding call closes the pipe instead:
            # no Exit after uncertain delivery. If idle, an explicit close may
            # cancel a fresh started run through the helper once.
            if selected:
                client.cancelled = lambda:False
                reply = client.call('cancel')
                self.result.emit(self.generation, reply)
        except Exception:
            self.result.emit(self.generation, {'failed':True})
        finally:
            if client:
                client.close()


class CalibrationLive(QObject):
    changed = Signal()

    def __init__(self, factory, *, parent=None, allow_open=lambda: True):
        super().__init__(parent)
        self.factory = factory
        self.allow_open = allow_open
        self.worker = None
        self.generation = 0
        self.busy = False
        self.inflight = None
        self.pending = None
        self.closed = False
        self.blocked = False
        self.session_active = False
        self.state = Calibration().snapshot()
        self.state.update(simulated=False, targets=[], adapterProblem='', cleanupProblem='')
        self.timer = QTimer(self)
        self.timer.setInterval(33)  # About 30 display snapshots/s; never queue polls.
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.poll)

    @Property(bool, constant=True)
    def available(self):
        return True

    @Property(bool, notify=changed)
    def inUse(self):
        # Keep package changes blocked until the worker has actually returned.
        return self.blocked or self.session_active

    def worker_finished(self, generation):
        if generation == self.generation:
            self.session_active = False
            self.changed.emit()

    @Slot()
    def receive_worker_finished(self):
        worker = self.sender()
        if worker is self.worker:
            self.worker_finished(worker.generation)

    @Property('QVariantMap', notify=changed)
    def view(self):
        value = dict(self.state, busy=self.busy)
        value['canStart'] = value['canStart'] and not self.busy
        value['canFinish'] = value['canFinish'] and not self.busy
        return value

    @Slot(result=bool)
    def open(self):
        if self.inUse or not self.allow_open():
            return False
        self.generation += 1
        self.closed = False
        self.inflight, self.pending = 'list', None
        self.state = Calibration().snapshot()
        self.state.update(phase='authorizing', simulated=False, targets=[],
                          adapterProblem='',cleanupProblem='')
        self.busy = True
        self.session_active = True
        self.worker = CalibrationWorker(self.generation, self.factory, self)
        self.worker.result.connect(self.receive)
        self.worker.finished.connect(self.receive_worker_finished)
        self.worker.start()
        self.changed.emit()
        return True

    @Slot(int, object)
    def receive(self, generation, reply):
        if generation != self.generation:
            return
        if self.closed:
            # A closed dialog must not consume late UI state, but uncertainty
            # still blocks package changes until separately revalidated.
            view = reply.get('view') or {}
            if reply.get('failed') or view.get('cleanupProblem') or view.get('acquisitionUncertain'):
                self.blocked = True
                self.changed.emit()
            return
        self.inflight = None
        if reply.get('failed'):
            self.state.update(phase='error',reason='transfer',running=False,canStart=False,canFinish=False)
            self.blocked = True  # Uncertain submission/return: no reopen/replay.
            self.timer.stop()
        elif 'targets' in reply:
            self.state.update(phase='selecting',targets=reply['targets'])
        elif reply.get('view') is not None:
            targets = self.state['targets']
            self.state = dict(reply['view'], simulated=False,targets=targets)
            if self.state.get('cleanupProblem') or self.state.get('acquisitionUncertain'):
                self.blocked = True
            if self.state['running']:
                if not self.timer.isActive():
                    self.timer.start()  # Do not add RPC latency to every period.
            else:
                self.timer.stop()
        pending, self.pending = self.pending, None
        self.busy = False
        if pending and self.state.get({'prepare':'canStart', 'finish':'canFinish'}[pending[0]]):
            self.dispatch(*pending)
        self.changed.emit()

    def submit(self, action, fields=None):
        if self.closed or self.busy or self.worker is None or not self.worker.isRunning():
            return
        if self.inflight:
            # An explicit click may wait behind ONE display read. Do not lose
            # clicks or accumulate old polls; cancel drops the pending action.
            if self.inflight == 'poll' and action in ('prepare', 'finish'):
                self.pending = (action, fields)
                self.busy = True
                self.changed.emit()
            return
        if self.dispatch(action, fields) and action != 'poll':
            self.changed.emit()

    def dispatch(self, action, fields=None):
        if self.worker.submit(action, fields):
            self.inflight = action
            self.busy = action != 'poll'
            return True
        return False

    @Slot(int)
    def select(self, index):
        if self.state['phase'] == 'selecting' and 0 <= index < len(self.state['targets']):
            self.submit('select', {'target':self.state['targets'][index]})

    @Slot()
    def poll(self):
        if self.state.get('running'):
            self.submit('poll')

    @Slot()
    def start(self):
        if self.state['canStart']:
            self.submit('prepare')

    @Slot()
    def finish(self):
        if self.state['canFinish']:
            self.submit('finish')

    @Slot()
    def close(self):
        self.timer.stop()
        if self.closed:
            return
        self.closed = True
        self.pending = None
        if self.worker and self.worker.isRunning():
            self.worker.stop_requested.set()
            # Root watchdog returns the lease if a reply was uncertain. Never
            # block the GUI or send commands concurrently from another thread.
        self.changed.emit()

    def shutdown(self):
        self.close()
        if self.worker:
            self.worker.wait(3000)
            # Helper reads are bounded and cancellable; never terminate a thread
            # during a possible root submission.
