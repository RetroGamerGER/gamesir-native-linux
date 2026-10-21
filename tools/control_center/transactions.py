# SPDX-License-Identifier: GPL-2.0-only
"""GUI-facing offline session coordinator. No host reader or live transport.

An ordinary status snapshot is never authoritative transaction evidence.
Only the separate in-memory rehearsal factory supplies this coordinator.
"""
from dataclasses import dataclass

from artifacts import BackendError, COMPONENTS
from backend import Request, Session, build_plan


@dataclass(frozen=True)
class Submission:
    session: Session
    confirmation_id: str
    port: object
    clock: object

    def run(self):
        return self.session.rehearse(self.confirmation_id, self.port, clock=self.clock)


class Transactions:
    def __init__(self, port, catalog, blobs, clock):
        self.port, self.catalog, self.blobs, self.clock = port, catalog, blobs, clock
        self.operation = ''
        self.selected = ()
        self.session = None
        self.state = 'idle'
        self.error = ''
        self.outcome = None

    @property
    def installed(self):
        return dict(self.port.observe().installed)

    @property
    def uncertain(self):
        return (self.outcome is not None and self.outcome.changes_possible
                and self.outcome.state != 'simulated_success')

    def available(self, operation):
        if self.uncertain or operation not in ('install', 'remove'):
            return ()
        installed = self.installed
        return tuple(c for c, (name, _) in COMPONENTS.items()
                     if (name in installed) == (operation == 'remove'))

    def request(self, operation):
        if self.state in ('editing', 'review', 'running') or not self.available(operation):
            return False
        self.operation, self.state = operation, 'editing'
        available = self.available(operation)
        self.selected = ('core',) if 'core' in available else (available[0],)
        self.session = self.outcome = None
        self.error = ''
        return True

    def select(self, component, checked):
        if (self.state != 'editing' or type(checked) is not bool
                or component not in self.available(self.operation)):
            return False
        chosen = set(self.selected)
        chosen.add(component) if checked else chosen.discard(component)
        self.selected = tuple(c for c in COMPONENTS if c in chosen)
        self.error = ''
        return True

    def prepare(self):
        if self.state != 'editing':
            return False
        try:
            request = Request.parse({'schema': 1, 'operation': self.operation,
                                     'components': list(self.selected)})
            blobs = {c: self.blobs[c] for c in self.selected if c in self.blobs} if self.operation == 'install' else {}
            plan = build_plan(request, self.port.observe(), blobs,
                              catalog=self.catalog, now=self.clock())
            self.session = Session(plan)
            self.state, self.error = 'review', ''
            return True
        except BackendError as error:
            self.error = error.code
            return False

    def begin(self):
        if self.state != 'review' or self.session is None:
            return None
        self.state = 'running'  # Reserve once on the GUI thread before scheduling.
        return Submission(self.session, self.session.plan.confirmation_id, self.port, self.clock)

    def finish(self, submission, outcome):
        if (self.state != 'running' or submission.session is not self.session
                or self.session.outcome is not outcome or outcome is None):
            return False
        self.outcome, self.error = outcome, outcome.error
        self.state = 'done'
        return True

    def cancel(self):
        if self.state not in ('editing', 'review'):
            return False
        self.outcome = self.session.cancel() if self.session else None
        self.state = 'cancelled'
        self.error = ''
        return True

    def summary(self):
        return self.session.plan.summary() if self.session else None
