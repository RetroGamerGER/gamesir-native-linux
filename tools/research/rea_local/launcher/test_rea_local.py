# SPDX-License-Identifier: GPL-2.0-only
"""Own synthetic inputs and mocked process backend only; never runs REA."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rea_local', HERE / 'rea_local.py')
rea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rea)


class FakeBackend:
    calls = []

    @classmethod
    def prepare_analysis_argv(cls, **kwargs):
        cls.calls.append(kwargs)
        return ['/reviewed/bwrap', '--', *kwargs['command']]


class FakeProcess:
    pid = 123456789

    def wait(self, timeout=None):
        return 0

    def poll(self):
        return 0


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=HERE)
        self.root = Path(self.temp.name)
        self.source = self.root / 'sample.exe'
        self.source.write_bytes(b'MZ' + bytes(range(64)))
        self.jobs = self.root / 'jobs'
        self.jobs.mkdir(mode=0o700)
        FakeBackend.calls = []

    def tearDown(self):
        for root, dirs, files in os.walk(self.root):
            Path(root).chmod(0o700)
        self.temp.cleanup()

    def plan(self, mode='native', selected=None, address=None):
        return rea.prepare_job(mode, str(selected or self.source), address, jobs_root=self.jobs)

    def test_single_file_preserved_and_private(self):
        before = self.source.read_bytes()
        plan = self.plan()
        self.assertEqual(before, self.source.read_bytes())
        self.assertEqual(Path(plan['input_dir'], 'source.exe').read_bytes(), before)
        self.assertEqual(stat.S_IMODE(Path(plan['job']).stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(Path(plan['job'], 'plan.json').stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(Path(plan['input_dir'], 'source.exe').stat().st_mode), 0o400)
        self.assertFalse(Path(plan['input_dir'], 'source.exe').stat().st_mode & 0o111)

    def test_each_job_is_fresh(self):
        self.assertNotEqual(self.plan()['job_id'], self.plan()['job_id'])

    def test_directory_preserved(self):
        source = self.root / 'application'
        source.mkdir()
        (source / 'sub').mkdir()
        (source / 'package.json').write_text('{"name":"synthetic"}')
        (source / 'sub/a.js').write_text('export const a = 1;')
        plan = self.plan('javascript', source)
        self.assertEqual(plan['before']['files'], 2)
        self.assertTrue(rea.content_matches(plan['before'], rea.snapshot(Path(plan['input_dir']) / 'application')))

    def test_single_javascript_source_wrapped(self):
        source = self.root / 'module.js'
        source.write_text('throw new Error("MUST NEVER EXECUTE");')
        plan = self.plan('javascript', source)
        self.assertEqual(plan['target'], '/input/application')
        self.assertEqual(Path(plan['input_dir'], 'application/source.js').read_text(), source.read_text())

    def test_non_js_directory_refused(self):
        for mode in ('native', 'function', 'managed', 'artifact'):
            with self.subTest(mode=mode), self.assertRaises(rea.Refused):
                self.plan(mode, self.root, '0x1000' if mode == 'function' else None)

    def test_symlink_file_refused(self):
        link = self.root / 'linked'
        link.symlink_to(self.source)
        with self.assertRaises(rea.Refused):
            self.plan(selected=link)

    def test_symlink_directory_component_refused(self):
        link = self.root / 'alias'
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(rea.Refused):
            self.plan(selected=link / 'sample.exe')

    def test_nested_symlink_refused(self):
        source = self.root / 'tree'
        source.mkdir()
        (source / 'bad').symlink_to(self.source)
        with self.assertRaises(rea.Refused):
            self.plan('javascript', source)

    def test_fifo_refused_without_read_open(self):
        fifo = self.root / 'pipe'
        os.mkfifo(fifo)
        with self.assertRaises(rea.Refused):
            self.plan(selected=fifo)

    def test_socket_refused(self):
        with socket.socket(socket.AF_UNIX) as sock:
            path = self.root / 'socket'
            previous = Path.cwd()
            try:
                os.chdir(self.root)
                sock.bind('socket')
            finally:
                os.chdir(previous)
            with self.assertRaises(rea.Refused):
                self.plan(selected=path)

    def test_device_refused_without_read_open(self):
        real_open = rea.os.open
        reads = []
        def observed(path, flags, *args, **kwargs):
            if str(path) == 'null' and not flags & os.O_PATH:
                reads.append(path)
            return real_open(path, flags, *args, **kwargs)
        with patch.object(rea.os, 'open', side_effect=observed), self.assertRaises(rea.Refused):
            rea.snapshot('/dev/null')
        self.assertEqual(reads, [])

    def test_kernel_pseudo_files_refused(self):
        for path in ('/proc/version', '/sys/kernel/uevent_seqnum', '/dev/null', '/run/private'):
            with self.subTest(path=path), self.assertRaises(rea.Refused):
                rea.snapshot(path)

    def test_file_limit(self):
        with patch.object(rea, 'MAX_FILE_BYTES', 2), self.assertRaises(rea.Refused):
            self.plan()

    def test_count_limit(self):
        source = self.root / 'tree'
        source.mkdir()
        (source / 'a').write_bytes(b'a')
        (source / 'b').write_bytes(b'b')
        with patch.object(rea, 'MAX_FILES', 1), self.assertRaises(rea.Refused):
            self.plan('javascript', source)

    def test_total_limit(self):
        with patch.object(rea, 'MAX_TOTAL_BYTES', 2), self.assertRaises(rea.Refused):
            self.plan()

    def test_entry_limit(self):
        source = self.root / 'tree'
        source.mkdir()
        for i in range(4):
            (source / str(i)).mkdir()
        with patch.object(rea, 'MAX_ENTRIES', 2), self.assertRaises(rea.Refused):
            self.plan('javascript', source)

    def test_jobs_inside_source_refused(self):
        with self.assertRaises(rea.Refused):
            self.plan('javascript', self.root)

    def test_non_private_jobs_refused(self):
        self.jobs.chmod(0o755)
        with self.assertRaises(rea.Refused):
            self.plan()

    def test_whitelist_and_strict_function_selector(self):
        expected = {'native': 'inspect', 'managed': 'inspect-managed-artifact',
                    'artifact': 'inspect-artifact', 'javascript': 'analyze-javascript-application'}
        for mode, command in expected.items():
            result = rea.static_command(mode, '/input/source.exe')
            self.assertEqual(result[0], command)
            self.assertEqual(result[-1], '--json')
        for mode in ('run', 'capture', 'setup', 'update', 'mcp', 'debug'):
            with self.subTest(mode=mode), self.assertRaises(rea.Refused):
                rea.static_command(mode, '/input/source.exe')
        for address in ('main', '--procedure=x', '0x1;echo secret', '0x' + '1' * 17):
            with self.subTest(address=address), self.assertRaises(rea.Refused):
                rea.static_command('function', '/input/source.exe', address)
        self.assertEqual(rea.static_command('function', '/input/source.exe', '0xAB')[2], '0xab')

    def test_mock_process_private_stdio_and_clean_env(self):
        plan = self.plan()
        seen = {}
        def runner(argv, **kwargs):
            seen.update(kwargs)
            os.write(kwargs['stdout'], b'PRIVATE SYNTHETIC RESULT')
            os.write(kwargs['stderr'], b'PRIVATE SYNTHETIC DIAGNOSTIC')
            return FakeProcess()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = rea.run_job(plan, FakeBackend, runner=runner)
        self.assertTrue(result['completed'])
        self.assertEqual(out.getvalue() + err.getvalue(), '')
        self.assertEqual(seen['stdin'], subprocess.DEVNULL)
        self.assertEqual(seen['env'], {})
        self.assertTrue(seen['close_fds'])
        self.assertEqual(seen['pass_fds'], ())
        self.assertFalse(seen['shell'])
        self.assertEqual(Path(plan['work_dir'], 'rea.stdout.json').read_bytes(), b'PRIVATE SYNTHETIC RESULT')
        self.assertEqual(stat.S_IMODE(Path(plan['work_dir'], 'rea.stderr.log').stat().st_mode), 0o600)

    def test_missing_approved_backend_refused(self):
        with self.assertRaises(rea.Refused):
            rea.run_job(self.plan(), object())

    def test_changed_original_refused_before_launch(self):
        plan = self.plan()
        self.source.write_bytes(b'changed')
        with self.assertRaises(rea.Refused):
            rea.run_job(plan, FakeBackend, runner=lambda *a, **k: self.fail('launched'))

    def test_change_during_process_recorded(self):
        plan = self.plan()
        def runner(*args, **kwargs):
            self.source.write_bytes(b'changed')
            return FakeProcess()
        result = rea.run_job(plan, FakeBackend, runner=runner)
        self.assertFalse(result['original_unchanged'])
        self.assertFalse(result['completed'])

    def test_changed_staged_input_refused(self):
        plan = self.plan()
        copied = Path(plan['copy_path'])
        copied.chmod(0o600)
        copied.write_bytes(b'changed staging')
        with self.assertRaises(rea.Refused):
            rea.run_job(plan, FakeBackend, runner=lambda *a, **k: self.fail('launched'))

    def test_timeout_kills_own_group_only(self):
        class TimeoutProcess(FakeProcess):
            calls = 0
            def wait(self, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    raise subprocess.TimeoutExpired('synthetic', timeout)
                return -9
            def poll(self):
                return None if self.calls == 1 else -9
        with patch.object(rea.os, 'killpg') as kill:
            result = rea.run_job(self.plan(), FakeBackend, runner=lambda *a, **k: TimeoutProcess())
        kill.assert_called_once_with(FakeProcess.pid, rea.signal.SIGKILL)
        self.assertFalse(result['completed'])
        self.assertEqual(result['failure'], 'timeout-or-interruption')

    def test_extra_cli_arguments_rejected(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rea.main(['native', str(self.source), '--provider', 'other'])

    def test_unexpected_wait_exception_kills_and_reaps(self):
        class BrokenWait(FakeProcess):
            calls = 0
            def wait(self, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError('synthetic wait failure')
                return -9
            def poll(self):
                return None if self.calls == 1 else -9
        with patch.object(rea.os, 'killpg') as kill:
            result = rea.run_job(self.plan(), FakeBackend, runner=lambda *a, **k: BrokenWait())
        kill.assert_called_once_with(FakeProcess.pid, rea.signal.SIGKILL)
        self.assertFalse(result['completed'])
        self.assertEqual(result['failure'], 'sandbox-launch-failed')


if __name__ == '__main__':
    unittest.main()
