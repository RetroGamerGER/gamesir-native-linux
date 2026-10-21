#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline auth boundary; pkexec/Polkit/root are never invoked by these tests."""
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
sys.path.insert(0, str(ROOT / 'scripts'))
from artifacts import COMPONENTS as PACKAGE_COMPONENTS
from privilege.protocol import (ACTION, ARGV, COMPONENTS, FILES, HELPER, LIMIT, MODE, POLICY,
                                AuthorizationError, Probe, acknowledgement, encode,
                                verify_acknowledgement)
from privilege.client import AuthorizationAttempt
from privilege.helper import answer, bounded_input
from privilege.transport import BoundedRunner, HelperPins, InstalledAuditor, PkexecTransport, Reply
from rehearsal import create_rehearsal
import package_control_center_auth as package


class FakeAgent:
    def __init__(self, code=0):
        self.calls = []
        self.code = code

    def invoke(self, data, *, cancelled):
        self.calls.append(data)
        # Effective UID is a synthetic parameter; the test has no root rights.
        output = answer(data, effective_uid=0, invoking_uid='1000') if self.code == 0 else b''
        return Reply('complete', self.code, output)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.probe = Probe('install', ('core', 'steam'), 'a' * 64, 'b' * 64)

    def test_exact_small_roundtrip_and_component_allowlist(self):
        self.assertEqual(set(COMPONENTS), set(PACKAGE_COMPONENTS))
        self.assertEqual(Probe.parse(self.probe.wire()), self.probe)
        self.assertLess(len(self.probe.wire()), LIMIT)
        verify_acknowledgement(acknowledgement(self.probe), self.probe)

    def test_command_path_password_and_activation_fields_are_rejected(self):
        for field in ('command', 'argv', 'path', 'password', 'activate', 'resume', 'reboot', 'package_url'):
            value = {**self.probe.message(), field: '/tmp/not-an-authority'}
            with self.subTest(field=field), self.assertRaises(AuthorizationError):
                Probe.parse(encode(value))

    def test_malformed_and_duplicate_json_stops(self):
        for data in (b'', b'[]', b'null', b'\xff', b'x' * (LIMIT+1),
                     b'{"schema":1,"schema":1}', b'{"schema":1} trailing'):
            with self.subTest(data=data[:30]), self.assertRaises(AuthorizationError):
                Probe.parse(data)

    def test_untyped_fields_duplicates_and_unknown_operations_stop(self):
        for field, value in (('schema', True), ('schema', 2), ('mode', 'execute'),
                             ('operation', 'pacman'), ('operation', ['install']),
                             ('components', ['core', 'core']), ('components', ['unrelated']),
                             ('components', []), ('components', [['core']]),
                             ('request_id', 'not-a-nonce'), ('plan_id', 'A' * 64)):
            with self.subTest(field=field, value=value), self.assertRaises(AuthorizationError):
                Probe.parse(encode({**self.probe.message(), field: value}))

    def test_root_and_pkexec_caller_are_both_required(self):
        for uid, caller in ((1000, '1000'), (0, None), (0, '0'), (0, '-1'),
                            (0, '١٢٣'), (0, '9' * 12), (0, '4294967295')):
            with self.subTest(uid=uid, caller=caller), self.assertRaises(AuthorizationError):
                answer(self.probe.wire(), effective_uid=uid, invoking_uid=caller)
        verify_acknowledgement(answer(self.probe.wire(), effective_uid=0, invoking_uid='1000'), self.probe)

    def test_result_cannot_claim_execution_or_act_as_a_different_plan(self):
        original = json.loads(acknowledgement(self.probe))
        for field, value in (('executed', True), ('executed', 0), ('schema', True),
                             ('result', 'installed'), ('plan_id', 'f' * 64), ('request_id', 'f' * 64),
                             ('token', 'reuse-me')):
            with self.subTest(field=field), self.assertRaises(AuthorizationError):
                verify_acknowledgement(encode({**original, field: value}), self.probe)

    def test_input_reader_is_bounded_and_waits_only_for_eof(self):
        read, write = os.pipe()
        try:
            os.write(write, self.probe.wire()); os.close(write); write = -1
            self.assertEqual(bounded_input(read), self.probe.wire())
        finally:
            os.close(read)
            if write != -1:
                os.close(write)
        for content, seconds in ((b'', 0.01), (b'x' * (LIMIT + 1), 1)):
            read, write = os.pipe()
            try:
                if content:
                    os.write(write, content)
                with self.assertRaises(AuthorizationError):
                    bounded_input(read, seconds=seconds)
            finally:
                os.close(read); os.close(write)


class ClientTests(unittest.TestCase):
    def plan(self):
        tx = create_rehearsal(clock=lambda: 100)
        tx.request('install'); self.assertTrue(tx.prepare())
        return tx.session.plan

    def test_disabled_by_default_and_one_shot(self):
        attempt = AuthorizationAttempt(self.plan(), nonce='b' * 64)
        result = attempt.run()
        self.assertEqual(result.error, 'authorization_transport_disabled')
        self.assertFalse(result.executed)
        self.assertIs(attempt.run(), result)

    def test_authorization_only_ack_is_not_package_success(self):
        agent = FakeAgent()
        attempt = AuthorizationAttempt(self.plan(), agent, nonce='b' * 64)
        result = attempt.run()
        self.assertEqual(result.state, 'authorized_only')
        self.assertFalse(result.executed)
        self.assertIs(attempt.run(), result)
        self.assertEqual(len(agent.calls), 1)

    def test_cancelled_and_denied_have_no_fallback_or_retry(self):
        for code, state in ((126, 'cancelled'), (127, 'blocked'), (2, 'blocked')):
            agent = FakeAgent(code)
            attempt = AuthorizationAttempt(self.plan(), agent)
            result = attempt.run()
            self.assertEqual(result.state, state)
            self.assertIs(attempt.run(), result)
            self.assertEqual(len(agent.calls), 1)
        agent = FakeAgent()
        result = AuthorizationAttempt(self.plan(), agent).run(cancelled=lambda: True)
        self.assertEqual(result.state, 'cancelled')
        self.assertFalse(agent.calls)

    def test_timeout_unknown_and_malformed_reply_do_not_authorize(self):
        for reply in (Reply('timeout'), Reply('completion_unknown'), Reply('output_limit'),
                      Reply('complete', 0, b'{"result":"installed"}')):
            agent = Mock()
            agent.invoke.return_value = reply
            result = AuthorizationAttempt(self.plan(), agent).run()
            self.assertNotEqual(result.state, 'authorized_only')
            self.assertFalse(result.executed)
        agent.invoke.side_effect = RuntimeError('/home/private/name credential secret')
        result = AuthorizationAttempt(self.plan(), agent).run()
        self.assertNotIn('private', repr(result))
        self.assertNotIn('secret', repr(result))

    def test_client_receipt_binds_exact_plan_and_nonce(self):
        agent = FakeAgent()
        attempt = AuthorizationAttempt(self.plan(), agent, nonce='c' * 64)
        self.assertEqual(attempt.run().state, 'authorized_only')
        sent = Probe.parse(agent.calls[0])
        self.assertEqual(sent.plan_id, attempt.probe.plan_id)
        self.assertEqual(sent.request_id, 'c' * 64)

    def test_backend_uses_the_auth_adapter_only_on_in_memory_port(self):
        for code in (0, 126, 127):
            agent = FakeAgent(code)
            tx = create_rehearsal(clock=lambda: 100, authorization=lambda plan:
                                 AuthorizationAttempt(plan, agent, nonce='c'*64).run())
            tx.request('install'); self.assertTrue(tx.prepare())
            submission = tx.begin(); result = submission.run(); tx.finish(submission, result)
            self.assertEqual(len(agent.calls), 1)
            self.assertEqual('commit' in tx.port.calls, code == 0)
            if code == 126:
                self.assertEqual(result.state, 'cancelled')
            elif code == 127:
                self.assertEqual(result.error, 'authorization_denied_or_agent_unavailable')


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.data = Probe('install', ('core',), 'a' * 64, 'b' * 64).wire()
        self.pins = HelperPins(tuple((name, 'a' * 64) for name in FILES))

    def test_missing_or_malformed_review_is_blocked_before_execution(self):
        for pins in (None, HelperPins(()), HelperPins(tuple((p, 'bad') for p in FILES))):
            with self.assertRaises(AuthorizationError):
                PkexecTransport(pins)

    def test_every_installed_file_and_fixed_command_are_attested(self):
        auditor, runner = Mock(), Mock()
        runner.invoke.return_value = Reply('complete', 126)
        transport = PkexecTransport(self.pins, auditor=auditor, runner=runner)
        self.assertEqual(transport.invoke(self.data, cancelled=lambda: False).returncode, 126)
        self.assertEqual(auditor.inspect.call_args_list[0].args, (ARGV[0],))
        self.assertEqual({c.args[0] for c in auditor.inspect.call_args_list[1:]}, set(FILES))
        self.assertEqual(runner.invoke.call_count, 1)
        auditor.inspect.side_effect = AuthorizationError('authorization_helper_changed')
        runner.reset_mock()
        with self.assertRaises(AuthorizationError):
            transport.invoke(self.data, cancelled=lambda: False)
        runner.invoke.assert_not_called()

    def test_installed_audit_rejects_symlink_or_writable_ancestor(self):
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFDIR | 0o777):
            metadata = os.stat_result((mode, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            with patch('pathlib.Path.lstat', return_value=metadata), self.assertRaises(AuthorizationError):
                InstalledAuditor().inspect(HELPER, 'a' * 64)

    def test_installed_audit_checks_opened_file_owner_mode_and_hash(self):
        directory = os.stat_result((stat.S_IFDIR | 0o755, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        with tempfile.TemporaryFile() as fixture:
            fixture.write(b'reviewed'); fixture.flush()
            for uid, mode, expected, success in (
                    (0, 0o755, hashlib.sha256(b'reviewed').hexdigest(), True),
                    (1000, 0o755, 'a'*64, False), (0, 0o775, 'a'*64, False),
                    (0, 0o644, 'a'*64, False), (0, 0o755, 'a'*64, False)):
                fixture.seek(0)
                file_info = os.stat_result((stat.S_IFREG | mode, 0, 0, 0, uid, 0, 0, 0, 0, 0))
                def opened(path, flags):
                    self.assertTrue(flags & os.O_NOFOLLOW)
                    return os.dup(fixture.fileno())
                with patch('pathlib.Path.lstat', return_value=directory), patch('os.open', side_effect=opened), \
                     patch('os.fstat', return_value=file_info):
                    if success:
                        InstalledAuditor().inspect(HELPER, expected, executable=True)
                    else:
                        with self.assertRaises(AuthorizationError):
                            InstalledAuditor().inspect(HELPER, expected, executable=True)

    def run_fake_child(self, program, *, timeout=1, cancelled=lambda: False):
        real_popen = subprocess.Popen
        recorded = []
        def fake(argv, **kwargs):
            self.assertEqual(tuple(argv), ARGV)
            self.assertNotIn('PYTHONPATH', kwargs['env'])
            self.assertNotIn('LD_PRELOAD', kwargs['env'])
            self.assertNotIn('DISPLAY', kwargs['env'])
            self.assertFalse(kwargs['shell'])
            recorded.append(argv)
            # This explicit test double runs harmless standard-library code as
            # this same user. Production pkexec is never started.
            return real_popen([sys.executable, '-I', '-B', '-c', program], **kwargs)
        with patch('privilege.transport.subprocess.Popen', side_effect=fake):
            result = BoundedRunner(timeout=timeout).invoke(self.data, cancelled=cancelled)
        self.assertEqual(len(recorded), 1)
        return result

    def test_fixed_runner_carries_only_json_and_separates_stdout_stderr(self):
        program = ('import sys;data=sys.stdin.buffer.read();sys.stdout.buffer.write(data);'
                   'sys.stderr.write("private diagnostic")')
        result = self.run_fake_child(program)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, self.data)
        self.assertNotIn('private', repr(result))

    def test_cancelled_agent_exit_and_closed_stdin_are_not_transport_failure(self):
        result = self.run_fake_child('raise SystemExit(126)')
        self.assertEqual(result.state, 'complete')
        self.assertEqual(result.returncode, 126)

    def test_output_and_time_limits_stop_only_the_fake_child(self):
        self.assertEqual(self.run_fake_child('print("x"*10000)').state, 'output_limit')
        self.assertEqual(self.run_fake_child('import sys;sys.stderr.write("x"*10000)').state, 'output_limit')
        self.assertEqual(self.run_fake_child('import time;time.sleep(3)', timeout=0.03).state, 'timeout')

    def test_cancellation_before_spawn_and_during_wait(self):
        with patch('privilege.transport.subprocess.Popen', side_effect=AssertionError('No spawn')):
            self.assertEqual(BoundedRunner().invoke(self.data, cancelled=lambda: True).state, 'cancelled')
        checks = []
        def cancelled():
            checks.append(True)
            return len(checks) > 2
        self.assertEqual(self.run_fake_child('import time;time.sleep(3)', cancelled=cancelled).state, 'cancelled')

    def test_cannot_claim_termination_when_privilege_boundary_denies_signals(self):
        child = Mock()
        child.poll.return_value = None
        child.terminate.side_effect = PermissionError()
        child.kill.side_effect = PermissionError()
        self.assertEqual(BoundedRunner().stop(child, 'timeout').state, 'completion_unknown')

    def test_process_io_failure_preserves_unknown_stop_state(self):
        child = Mock()
        child.stdin = io.BytesIO()
        child.poll.return_value = None
        child.stdout.fileno.return_value = -1
        child.terminate.side_effect = PermissionError()
        child.kill.side_effect = PermissionError()
        with patch('privilege.transport.subprocess.Popen', return_value=child):
            result = BoundedRunner().invoke(self.data, cancelled=lambda: False)
        self.assertEqual(result.state, 'completion_unknown')


class PolicyAndStaging(unittest.TestCase):
    def test_root_import_guard_checks_each_ancestor_without_following_links(self):
        entry = runpy.run_path(str(ROOT/'packaging/control-center/authorize'), run_name='offline_entry_test')
        target = Path(HELPER)
        def metadata(path, *, unsafe=None, mode=None, uid=None):
            node_mode = stat.S_IFREG | 0o755 if path == target else stat.S_IFDIR | 0o755
            if path == unsafe and mode is not None:
                node_mode = mode
            return os.stat_result((node_mode, 0, 0, 0, uid if path == unsafe and uid is not None else 0,
                                   0, 0, 0, 0, 0))
        with patch.object(Path, 'lstat', metadata):
            self.assertTrue(entry['protected'](target))
        for unsafe, mode, uid in ((target, stat.S_IFLNK | 0o777, 0),
                                  (target, stat.S_IFREG | 0o775, 0),
                                  (target.parent, None, 1000),
                                  (target.parent.parent, stat.S_IFLNK | 0o777, 0)):
            def changed(path):
                return metadata(path, unsafe=unsafe, mode=mode, uid=uid)
            with patch.object(Path, 'lstat', changed):
                self.assertFalse(entry['protected'](target))

    def test_policy_is_fixed_local_active_admin_only_without_cached_authorization(self):
        policy = ET.parse(ROOT / 'packaging/control-center' / Path(POLICY).name).getroot()
        actions = policy.findall('action')
        self.assertEqual([a.attrib['id'] for a in actions], [ACTION])
        action = actions[0]
        self.assertEqual(action.findtext('defaults/allow_any'), 'no')
        self.assertEqual(action.findtext('defaults/allow_inactive'), 'no')
        self.assertEqual(action.findtext('defaults/allow_active'), 'auth_admin')
        self.assertEqual([(a.attrib['key'], a.text) for a in action.findall('annotate')],
                         [('org.freedesktop.policykit.exec.path', HELPER)])
        messages = [m.text for m in action.findall('message')]
        self.assertEqual(len(messages), 2)
        self.assertIn('nicht verändert', messages[1])

    def test_staged_payload_is_optional_noninstalled_and_preserves_existing_destinations(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            dest = Path(temporary)/'stage'
            report = package.stage(dest)
            self.assertFalse(report['installed'])
            self.assertFalse(report['reviewed'])
            self.assertFalse(report['release_ready'])
            self.assertEqual(set(report['files']), set(FILES))
            for name, digest in report['files'].items():
                target = dest/name.lstrip('/')
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest)
                self.assertEqual(target.stat().st_mode & 0o777, 0o755 if name == HELPER else 0o644)
            with self.assertRaises(ValueError):
                package.stage(dest)
            self.assertTrue((dest/POLICY.lstrip('/')).is_file())

    def test_helper_refuses_uninstalled_path_without_reading_requests_or_elevating(self):
        result = subprocess.run([sys.executable, '-IBS', str(ROOT/'packaging/control-center/authorize')],
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=3)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr, b'')


if __name__ == '__main__':
    unittest.main()
