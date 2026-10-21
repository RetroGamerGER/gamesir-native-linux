#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline GUI/session boundary: real validators, synthetic bytes and inventory."""
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import COMPONENTS, PUBLIC_BINARIES
from rehearsal import create_rehearsal


class TransactionsTest(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.tx = create_rehearsal(clock=lambda: self.now)

    def prepare(self, operation='install', components=('core',)):
        self.assertTrue(self.tx.request(operation))
        for c in tuple(self.tx.selected):
            self.tx.select(c, False)
        for c in components:
            self.assertTrue(self.tx.select(c, True))
        return self.tx.prepare()

    def run_plan(self):
        submission = self.tx.begin()
        self.assertIsNotNone(submission)
        outcome = submission.run()
        self.assertTrue(self.tx.finish(submission, outcome))
        return outcome

    def test_status_is_not_authority_and_no_public_binaries_are_added(self):
        self.assertEqual(PUBLIC_BINARIES.records, ())
        self.assertEqual(self.tx.state, 'idle')
        self.assertEqual(self.tx.port.host.distribution, 'cachyos')
        self.assertFalse(self.tx.port.calls)
        self.assertIsNone(self.tx.begin())

    def test_selection_is_explicit_and_confirm_is_not_an_install(self):
        self.assertTrue(self.prepare())
        self.assertNotIn(COMPONENTS['core'][0], self.tx.installed)
        self.assertFalse(self.tx.summary()['activate'])
        self.assertFalse(self.tx.summary()['reboot'])
        self.assertEqual(self.tx.summary()['packages'], [COMPONENTS['core'][0]])
        self.assertEqual(self.run_plan().state, 'simulated_success')
        self.assertIn(COMPONENTS['core'][0], self.tx.installed)
        self.assertFalse(self.tx.port.host.native_loaded)
        self.assertFalse(self.tx.port.host.service_enabled)

    def test_install_and_remove_all_components_keep_unrelated_inventory(self):
        self.assertTrue(self.prepare(components=tuple(COMPONENTS)))
        self.assertEqual(self.run_plan().state, 'simulated_success')
        self.assertTrue(self.prepare('remove', tuple(COMPONENTS)))
        self.assertTrue(self.tx.summary()['existing_alpm_core_guard_required'])
        self.assertEqual(self.run_plan().state, 'simulated_success')
        self.assertEqual(self.tx.installed, {'unrelated-controller': '1.0-1'})

    def test_dependency_is_never_selected_silently(self):
        self.assertFalse(self.prepare(components=('bridge',)))
        self.assertEqual(self.tx.error, 'dependent_component_requires_explicit_selection')
        self.assertEqual(self.tx.selected, ('bridge',))
        self.assertFalse(self.tx.port.calls)

    def test_empty_or_unknown_selection_and_unknown_action_are_blocked(self):
        for action in ('resume', 'release', 'reboot', 'install --force', ''):
            self.assertFalse(self.tx.request(action))
        self.assertFalse(self.prepare(components=()))
        self.assertEqual(self.tx.error, 'invalid_components')
        self.assertFalse(self.tx.select('arbitrary-package', True))
        self.assertFalse(self.tx.select('core', 'true'))

    def test_review_cannot_be_mutated_or_submitted_twice(self):
        self.assertTrue(self.prepare())
        identity = self.tx.session.plan.confirmation_id
        self.assertFalse(self.tx.select('steam', True))
        self.assertFalse(self.tx.request('remove'))
        self.assertEqual(identity, self.tx.session.plan.confirmation_id)
        submission = self.tx.begin()
        self.assertIsNone(self.tx.begin())
        self.assertFalse(self.tx.cancel())
        outcome = submission.run()
        calls = list(self.tx.port.calls)
        self.assertIs(submission.run(), outcome)
        self.assertEqual(self.tx.port.calls, calls)
        self.assertTrue(self.tx.finish(submission, outcome))
        self.assertFalse(self.tx.finish(submission, outcome))

    def test_foreign_completion_cannot_replace_current_session(self):
        self.assertTrue(self.prepare())
        submission = self.tx.begin()
        other = create_rehearsal(clock=lambda: self.now)
        other.request('install'); other.prepare()
        foreign = other.begin()
        result = foreign.run()
        self.assertFalse(self.tx.finish(foreign, result))
        self.assertEqual(self.tx.state, 'running')
        result = submission.run()
        self.assertTrue(self.tx.finish(submission, result))

    def test_demo_and_backend_rehearsal_modes_are_exclusive(self):
        import io
        from contextlib import redirect_stderr
        import main
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main.main(['--demo', '--rehearse-backend'])
        self.assertEqual(error.exception.code, 2)

    def test_escape_cancel_consumes_prepared_session_without_transport(self):
        self.assertTrue(self.prepare())
        session = self.tx.session
        self.assertTrue(self.tx.cancel())
        self.assertTrue(session.used)
        self.assertFalse(self.tx.cancel())
        self.assertIsNone(self.tx.begin())
        self.assertFalse(self.tx.port.calls)

    def test_expired_plan_blocks_before_transport(self):
        self.assertTrue(self.prepare())
        self.now += 121
        outcome = self.run_plan()
        self.assertEqual(outcome.error, 'plan_expired')
        self.assertFalse(outcome.changes_possible)
        self.assertFalse(self.tx.port.calls)

    def test_host_changed_after_review_blocks(self):
        self.assertTrue(self.prepare())
        self.tx.port.host = replace(self.tx.port.host, database_token='f' * 64)
        self.assertEqual(self.run_plan().error, 'host_changed')
        self.assertNotIn('commit', self.tx.port.calls)

    def test_package_mutation_is_not_trusted(self):
        self.tx.blobs['core'] += b'changed'
        self.assertFalse(self.prepare())
        self.assertEqual(self.tx.error, 'no_reviewed_binary')
        self.assertFalse(self.tx.port.calls)

    def test_missing_artifact_is_reported_without_starting_a_transaction(self):
        self.tx.blobs.pop('core')
        self.assertFalse(self.prepare())
        self.assertEqual(self.tx.error, 'missing_reviewed_artifact')
        self.assertEqual(self.tx.state, 'editing')
        self.assertFalse(self.tx.port.calls)

    def test_authorization_cancellation_and_original_errors_survive(self):
        for scenario, expected in (('authorization_cancelled', ''),
                                   ('host_changed', 'host_changed'),
                                   ('transaction_failed', 'offline_transaction_failed'),
                                   ('verification_failed', 'package_postcheck_mismatch')):
            with self.subTest(scenario=scenario):
                self.tx = create_rehearsal(scenario, clock=lambda: self.now)
                self.assertTrue(self.prepare())
                outcome = self.run_plan()
                self.assertEqual(outcome.error, expected)
                self.assertIsNone(self.tx.begin())
                self.assertFalse(self.tx.cancel())
                self.assertIs(self.tx.outcome, outcome)
                if expected:
                    self.assertIsNotNone(self.tx.session.first_failure)
                self.assertEqual(outcome.changes_possible,
                                 scenario in ('transaction_failed', 'verification_failed'))
                if outcome.changes_possible:
                    self.assertTrue(self.tx.uncertain)
                    self.assertFalse(self.tx.request('install'))
                    self.assertFalse(self.tx.request('remove'))

    def test_complete_gui_transaction_has_no_file_process_socket_or_network_io(self):
        with ExitStack() as stack:
            for name in ('builtins.open', 'pathlib.Path.open', 'os.open', 'socket.socket',
                         'subprocess.run', 'subprocess.Popen', 'urllib.request.urlopen'):
                stack.enter_context(patch(name, side_effect=AssertionError('I/O forbidden: ' + name)))
            self.tx = create_rehearsal(clock=lambda: self.now)
            self.assertTrue(self.prepare(components=tuple(COMPONENTS)))
            self.assertEqual(self.run_plan().state, 'simulated_success')
            self.assertTrue(self.prepare('remove', tuple(COMPONENTS)))
            self.assertEqual(self.run_plan().state, 'simulated_success')


if __name__ == '__main__':
    unittest.main()
