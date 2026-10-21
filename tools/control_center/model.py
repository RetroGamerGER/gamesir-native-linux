# SPDX-License-Identifier: GPL-2.0-only
"""In-memory preview state machine. Intentionally no installation backend."""
from dataclasses import dataclass, replace

GITHUB_URL = 'https://github.com/RetroGamerGER/gamesir-native-linux'
DEADBAND_URL = 'https://github.com/broroeror/gamesir-linux-tools'
LINKS = {'github': GITHUB_URL, 'deadband': DEADBAND_URL}


@dataclass(frozen=True)
class Situation:
    key: str
    notice: str
    installed: bool = False
    loaded: bool = False
    receiver: bool = False
    connected: bool = False
    supported: bool = True
    headers: bool = True


SITUATIONS = (
    Situation('ready', 'ready'),
    Situation('installed', 'installed_notice', True, True, True, True),
    Situation('waiting', 'waiting_notice', True, True, True, False),
    Situation('offline', 'offline_notice'),
    Situation('unsupported', 'unsupported_notice', supported=False),
    Situation('headers', 'headers_notice', headers=False),
    Situation('corrupt', 'corrupt_notice'),
    Situation('incomplete', 'incomplete_notice'),
    Situation('package', 'package_notice'),
    Situation('cancelled', 'cancelled_notice'),
    Situation('removal', 'removal_notice', True, True, True, True),
)


class Preview:
    """Only synthetic data. A dialog confirmation can never reach a real action."""

    def __init__(self):
        self.situation = SITUATIONS[0]
        self.pending = ''
        self.result = None

    @property
    def can_install(self):
        s = self.situation
        return s.supported and s.headers and not s.installed

    @property
    def can_remove(self):
        return self.situation.installed

    def select(self, index):
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(SITUATIONS):
            raise ValueError('Invalid preview situation')
        self.situation = SITUATIONS[index]
        self.pending = ''
        self.result = None

    def request(self, action):
        if self.pending:
            return False
        if action == 'install' and self.can_install or action == 'remove' and self.can_remove:
            self.pending = action
            self.result = None
            return True
        return False

    def cancel(self):
        if not self.pending:
            return False
        self.pending = ''
        self.result = ('result_cancelled', 'cancel_body', 'neutral')
        return True

    def confirm(self):
        action = self.pending
        if not action:
            return False
        self.pending = ''  # Consume once; repeated clicks cannot repeat an operation.
        key = self.situation.key
        if action == 'install':
            if key in ('offline', 'corrupt', 'incomplete', 'package', 'cancelled'):
                title = 'result_cancelled' if key == 'cancelled' else 'result_error'
                self.result = (title, 'error_' + key, 'warning')
                return True
            self.situation = replace(self.situation, installed=True, loaded=False)
            self.result = ('result_success', 'install_success', 'success')
        else:
            if key == 'removal':
                self.result = ('result_error', 'error_removal', 'warning')
                return True
            self.situation = replace(self.situation, installed=False, loaded=False, connected=False)
            self.result = ('result_success', 'remove_success', 'success')
        return True

    def dismiss_result(self):
        self.result = None
