# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic metadata/argv tests only. Never launches Bubblewrap or REA."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reviewed_sandbox', HERE.parent / 'sandbox/sandbox_plan.py')
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)


class SandboxPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sandbox-synthetic-', dir=HERE)
        self.root = Path(self.temp.name)
        self.tools = self.root / 'tools'
        self.tools.mkdir(mode=0o700)
        node = self.tools / 'node-v24.19.0/bin/node'
        node.parent.mkdir(parents=True)
        node.write_bytes(b'SYNTHETIC NONEXECUTED NODE PLACEHOLDER')
        node.chmod(0o700)
        rea = self.tools / 'rea-6.5.0/node_modules/rea-agents/scripts/rea.mjs'
        rea.parent.mkdir(parents=True)
        rea.write_text('// SYNTHETIC NONEXECUTED REA PLACEHOLDER\n')
        rea.chmod(0o600)
        (self.tools / 'ghidra_12.1.4_PUBLIC').mkdir()
        (self.tools / 'jdk-21.0.12.1+1').mkdir()
        self.job = self.root / 'job'
        self.job.mkdir(mode=0o700)
        self.work = self.job / 'work'
        self.work.mkdir(mode=0o700)
        self.input = self.job / 'input'
        self.input.mkdir(mode=0o700)
        self.target = self.input / 'source.exe'
        self.target.write_bytes(b'SYNTHETIC INERT INPUT')
        self.target.chmod(0o400)
        self.input.chmod(0o500)
        self.no_run = patch.object(sandbox.subprocess, 'run', side_effect=AssertionError('Must not launch any subprocess'))
        self.no_popen = patch.object(sandbox.subprocess, 'Popen', side_effect=AssertionError('Must not launch any subprocess'))
        self.no_run.start()
        self.no_popen.start()

    def tearDown(self):
        self.no_run.stop()
        self.no_popen.stop()
        for root, dirs, files in os.walk(self.root):
            Path(root).chmod(0o700)
        self.temp.cleanup()

    def prepare(self, command=None):
        return sandbox.prepare_analysis_argv(tools_root=str(self.tools), input_dir=str(self.input),
            work_dir=str(self.work), command=command or ['inspect', '/input/source.exe', '--provider', 'ghidra', '--json'])

    def pure(self):
        return sandbox.build_argv(bwrap='/usr/bin/bwrap', node_binary='/private/tools/node-v24.19.0/bin/node',
            tools_root='/private/tools', out_dir='/private/job/work', baseline='/private/job/baseline.json',
            probe_python='/reviewed/probe.py', probe_node='/reviewed/probe.mjs', uid=1000, gid=1000,
            system_aliases={'/bin': 'usr/bin', '/sbin': 'usr/bin', '/lib': 'usr/lib', '/lib64': 'usr/lib'},
            ld_cache='/etc/ld.so.cache')

    def test_exact_five_static_lanes(self):
        vectors = [
            ['inspect', '/input/source.exe', '--provider', 'ghidra', '--json'],
            ['function', '/input/source.exe', '0x1a2b', '--provider', 'ghidra', '--json'],
            ['analyze-javascript-application', '/input/application', '--json'],
            ['inspect-managed-artifact', '/input/source.dll', '--json'],
            ['inspect-artifact', '/input/source.msix', '--json'],
        ]
        for vector in vectors:
            with self.subTest(vector=vector):
                self.assertEqual(sandbox.validate_analysis_command(vector), vector)

    def test_runtime_setup_mcp_and_unknown_operations_rejected(self):
        for name in ('mcp', 'setup', 'update', 'run', 'capture', 'debug-with-gdb', 'decompile', 'search'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                sandbox.validate_analysis_command([name, '/input/source.exe', '--json'])

    def test_extra_flags_raw_arch_and_other_provider_rejected(self):
        base = ['inspect', '/input/source.exe', '--provider', 'ghidra', '--json']
        for extra in (['--target-format', 'raw-binary'], ['--architecture', 'arm'], ['--entry-point', '0x0'], ['--snapshot', '/work/a']):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                sandbox.validate_analysis_command(base + extra)
        with self.assertRaises(ValueError):
            sandbox.validate_analysis_command(['inspect', '/input/source.exe', '--provider', 'auto', '--json'])

    def test_target_escape_and_free_option_rejected(self):
        for target in ('/input/../secret', '/home/user/file', '/input/a/b', '--setup', '/input/source.EXE'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                sandbox.validate_analysis_command(['inspect-artifact', target, '--json'])

    def test_function_address_not_arbitrary_command(self):
        for address in ('main', '--procedure=x', '0x10;id', '0x' + '1' * 17, '0x'):
            with self.subTest(address=address), self.assertRaises(ValueError):
                sandbox.validate_analysis_command(['function', '/input/source.exe', address, '--provider', 'ghidra', '--json'])

    def test_pure_argv_requires_namespace_and_capability_guards(self):
        argv = self.pure()
        self.assertEqual(set(sandbox.NAMESPACES), {'mnt', 'pid', 'user', 'net', 'ipc', 'uts', 'cgroup'})
        # Bubblewrap always creates its private mount namespace; the other six
        # are explicit. Runtime isolation is separately verified by the probe.
        for flag in ('--unshare-user', '--unshare-pid', '--unshare-net', '--unshare-ipc', '--unshare-uts', '--unshare-cgroup', '--clearenv', '--die-with-parent', '--new-session'):
            self.assertIn(flag, argv)
        at = argv.index('--cap-drop')
        self.assertEqual(argv[at:at + 2], ['--cap-drop', 'ALL'])
        self.assertNotIn('--share-net', argv)

    def test_pure_argv_mounts_tools_read_only_and_no_host_home(self):
        argv = self.pure()
        triples = [argv[i:i + 3] for i in range(len(argv) - 2)]
        self.assertIn(['--ro-bind', '/private/tools', '/tools'], triples)
        self.assertIn(['--bind', '/private/job/work', '/out'], triples)
        self.assertIn(['--dev', '/dev'], [argv[i:i + 2] for i in range(len(argv) - 1)])
        self.assertNotIn('/dev/bus/usb', argv)
        self.assertNotIn('/run', argv)
        self.assertNotIn(str(Path.home()), argv)
        writable = [argv[i + 1:i + 3] for i, item in enumerate(argv) if item == '--bind']
        self.assertEqual(writable, [['/private/job/work', '/out']])

    def test_prepare_native_adds_ro_input_and_reviewed_environment(self):
        argv = self.prepare()
        triples = [argv[i:i + 3] for i in range(len(argv) - 2)]
        self.assertIn(['--ro-bind', str(self.input), '/input'], triples)
        self.assertIn(['--setenv', 'JAVA_HOME', '/tools/jdk-21.0.12.1+1'], triples)
        self.assertIn(['--setenv', 'GHIDRA_INSTALL_DIR', '/tools/ghidra_12.1.4_PUBLIC'], triples)
        self.assertEqual(argv[-3:], ['/usr/bin/python3', '-I', '/opt/rea-check/analysis-guard.py'])
        request = json.loads((self.job / '.sandbox/request.json').read_text())
        self.assertFalse(request['target_execution'])
        self.assertFalse(request['network'])
        self.assertEqual(request['command'], ['inspect', '/input/source.exe', '--provider', 'ghidra', '--json'])
        self.assertEqual(list(self.work.iterdir()), [])

    def test_prepare_javascript_tree_requires_no_ghidra_environment(self):
        self.input.chmod(0o700)
        application = self.input / 'application'
        application.mkdir(mode=0o700)
        module = application / 'module.js'
        module.write_text('throw new Error("NEVER RUN THIS INPUT");')
        module.chmod(0o400)
        application.chmod(0o500)
        self.input.chmod(0o500)
        argv = self.prepare(['analyze-javascript-application', '/input/application', '--json'])
        self.assertNotIn('GHIDRA_INSTALL_DIR', argv)
        self.assertNotIn('JAVA_HOME', argv)
        self.assertIn('/input', argv)

    def test_staged_symlink_refused(self):
        self.input.chmod(0o700)
        (self.input / 'link').symlink_to(self.target)
        self.input.chmod(0o500)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_staged_special_inode_refused_without_opening(self):
        self.input.chmod(0o700)
        os.mkfifo(self.input / 'pipe', 0o400)
        self.input.chmod(0o500)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_nonfresh_or_reused_work_refused(self):
        (self.work / 'old').write_text('prior result')
        with self.assertRaises(ValueError):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
