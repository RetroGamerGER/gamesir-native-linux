#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Local Fish/POSIX round trips only: no SSH, sudo, GUI or live target."""
import base64
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ssh_payload', ROOT/'tools/sdl/ssh_python_payload.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
SHELLS = (('/usr/bin/fish', '-N'), ('/usr/bin/bash', '--noprofile', '--norc'),
          ('/usr/bin/sh',))

# A test-owned executable replaces the fixed sudo path before shell execution.
# It consumes exactly one synthetic password line, without buffering subsequent
# stdin, and execs the ordinary-user Python fixture. It grants no privileges.
SUDO_STUB = '''#!/usr/bin/python
import os, sys
assert sys.argv[1:5] == ["-S", "-p", "GAMESIR_GUIDE_READ_PASSWORD:", "--"]
os.write(2, sys.argv[3].encode())
line = bytearray()
while not line.endswith(b"\\n"):
    part = os.read(0, 1)
    if not part: sys.exit(71)
    line.extend(part)
if line != b"synthetic-test-secret\\n": sys.exit(72)
for i in range(len(line)): line[i] = 0
os.execv(sys.argv[5], sys.argv[5:])
'''


class ShellTransport(unittest.TestCase):
    def setUp(self):
        for shell in SHELLS:
            self.assertTrue(Path(shell[0]).is_file(), f'Required local shell missing: {shell[0]}')
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.env = {'HOME': str(self.root), 'XDG_CONFIG_HOME': str(self.root),
                    'XDG_DATA_HOME': str(self.root), 'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}
        self.stub = self.root/'own sudo fixture'
        self.stub.write_text(SUDO_STUB)
        self.stub.chmod(0o700)

    def command(self, source, *, elevate=False):
        command = m.read_check_command(source)
        self.assertEqual(command.count('/usr/bin/sudo'), 1)
        if elevate:
            return command.replace('/usr/bin/sudo', "'" + str(self.stub) + "'", 1)
        return command.replace('/usr/bin/sudo -S -p '+m.PASSWORD_MARKER+' -- ', '', 1)

    def execute(self, source, *, stdin='', elevate=False):
        results = []
        for shell in SHELLS:
            result = subprocess.run([*shell, '-c', self.command(source, elevate=elevate)],
                                    input=stdin, text=True, capture_output=True,
                                    env=self.env, cwd=self.root, timeout=5)
            results.append((shell[0], result))
        return results

    def test_legacy_posix_quoting_reproduces_fish_failure(self):
        inner = 'value = \'single\'\nother = "double"\nprint(value, other)\n'
        source = 'exec(compile('+repr(inner)+',"fixture","exec"),{})'
        legacy = '/usr/bin/python -B -c '+shlex.quote(source)
        fish = subprocess.run([*SHELLS[0], '-c', legacy], env=self.env,
                              capture_output=True, text=True, timeout=5)
        bash = subprocess.run([*SHELLS[1], '-c', legacy], env=self.env,
                              capture_output=True, text=True, timeout=5)
        self.assertNotEqual(fish.returncode, 0)
        self.assertTrue('quotes' in fish.stderr or 'Unexpected' in fish.stderr)
        self.assertEqual(bash.returncode, 0, bash.stderr)
        self.assertEqual(bash.stdout, 'single double\n')

    def test_nested_source_quotes_backslashes_and_unicode_preserved(self):
        value = "single' double\" slash\\ newline\n tab\t braces{} ß 🎮"
        inner = 'import json\nvalue='+repr(value)+'\nprint(json.dumps(value))\n'
        source = 'exec(compile('+repr(inner)+',"fixture","exec"),{})'
        for shell, result in self.execute(source):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), value)
                self.assertEqual(result.stderr, '')

    def test_shell_substitutions_are_literal_data(self):
        values = ["$(touch INJECTION)", '`touch INJECTION`', '; touch INJECTION;',
                  "' ; touch INJECTION; #", '\\', '$HOME', '*?[abc]', '\r\n',
                  '"}])\\\'\"', '😄'*64]
        source = 'import json\nprint(json.dumps('+repr(values)+'))\n'
        for shell, result in self.execute(source):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), values)
        self.assertFalse((self.root/'INJECTION').exists())

    def test_source_bytes_and_argv_are_identical(self):
        source = 'import json,sys\nprint(json.dumps(sys.argv))\n'
        expected = ['-c']
        for shell, result in self.execute(source):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected)
        bootstrap = m.python_bootstrap(source)
        token = bootstrap.split('base64.b64decode("', 1)[1].split('"', 1)[0]
        self.assertEqual(base64.b64decode(token, validate=True), source.encode('utf-8'))

    def test_stdin_and_locale_survive_without_a_here_document(self):
        source = 'import json,sys,os\nprint(json.dumps([sys.stdin.read(),os.environ["LC_ALL"]]))'
        for shell, result in self.execute(source, stdin='GO\nfollowing line\n'):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), ['GO\nfollowing line\n', 'C'])

    def test_synthetic_sudo_password_uses_stdin_without_corrupting_source(self):
        source = 'import json,sys\nprint(json.dumps(sys.stdin.read()))'
        for shell, result in self.execute(source, stdin='synthetic-test-secret\nREMAINDER\n', elevate=True):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, m.PASSWORD_MARKER)
                self.assertEqual(json.loads(result.stdout), 'REMAINDER\n')
                self.assertNotIn('synthetic-test-secret', self.command(source, elevate=True))

    def test_synthetic_password_rejection_stops_before_source(self):
        source = 'raise AssertionError("SOURCE_MUST_NOT_RUN")'
        for shell, result in self.execute(source, stdin='incorrect\n', elevate=True):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 72)
                self.assertNotIn('SOURCE_MUST_NOT_RUN', result.stderr+result.stdout)

    def test_source_error_exit_propagates_without_retry(self):
        for shell in SHELLS:
            counter = self.root/('invocations-'+Path(shell[0]).name)
            source = ('from pathlib import Path\nwith Path('+repr(str(counter))+').open("a") as f:f.write("once\\n")\n'
                      'raise SystemExit(23)')
            result = subprocess.run([*shell, '-c', self.command(source)], env=self.env,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual(counter.read_text(), 'once\n')

    def test_common_module_definitions_do_not_run_observer(self):
        common = (ROOT/'tools/sdl/steam_gyro_observe.py').read_text()
        check = 'assert m.__name__=="steam_gyro_observe"\nprint("DEFINITIONS_ONLY")'
        source = ('import sys,types\nm=types.ModuleType("steam_gyro_observe")\n'
                  'sys.modules["steam_gyro_observe"]=m\nexec(compile('+repr(common)+
                  ',"reviewed-common","exec"),m.__dict__)\nexec(compile('+repr(check)+
                  ',"synthetic-check","exec"),{"__name__":"__main__","m":m})')
        for shell, result in self.execute(source):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, 'DEFINITIONS_ONLY\n')
                self.assertEqual(result.stderr, '')

    def test_large_source_near_limit_round_trips(self):
        source = '#'+('x'*(m.MAX_SOURCE_BYTES-24))+'\nprint("LARGE")\n'
        for shell, result in self.execute(source):
            with self.subTest(shell=shell):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, 'LARGE\n')


class LocalValidation(unittest.TestCase):
    def test_non_text_empty_and_oversized_rejected(self):
        for value in (b'print(1)', None, 42):
            with self.subTest(value=value), self.assertRaises(TypeError):m.read_check_command(value)
        for value in ('', '#'+('x'*m.MAX_SOURCE_BYTES)):
            with self.assertRaises(ValueError):m.read_check_command(value)

    def test_nul_and_invalid_syntax_rejected_before_transport(self):
        for value in ('x=\x00', 'if:'):
            with self.subTest(value=value), self.assertRaises((ValueError, SyntaxError)):
                m.read_check_command(value)

    def test_validation_never_executes_source(self):
        m.read_check_command('raise AssertionError("Must not execute during construction")')

    def test_bootstrap_has_only_fixed_shell_delimiters(self):
        command = m.read_check_command('print("quoted \\\\ \u00df")')
        bootstrap = m.python_bootstrap('print("quoted \\\\ \u00df")')
        self.assertTrue(bootstrap.isascii())
        for value in ("'", '\\', '\n', '\r', '$', '`'):
            self.assertNotIn(value, bootstrap)
        self.assertEqual(command.count("'"), 2)
        self.assertEqual(shlex.split(command)[:8], ['/usr/bin/env','LC_ALL=C','/usr/bin/sudo',
                         '-S','-p',m.PASSWORD_MARKER,'--','/usr/bin/python'])


if __name__ == '__main__':
    unittest.main()
