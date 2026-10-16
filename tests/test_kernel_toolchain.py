#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline compiler selection regressions; synthetic headers and fake tools only."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'scripts/kernel_toolchain.py'
spec = importlib.util.spec_from_file_location('kernel_toolchain', HELPER)
toolchain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolchain)

# Include both families so a successful test cannot merely fall back to the
# host's compiler. Nothing in this directory compiles or installs anything.
TOOLS = ('make', 'gcc', 'g++', 'ld.bfd', 'as', 'ar', 'nm', 'strip', 'objcopy',
         'objdump', 'readelf', 'clang', 'clang++', 'ld.lld', 'llvm-ar',
         'llvm-nm', 'llvm-strip', 'llvm-objcopy', 'llvm-objdump', 'llvm-readelf')
CONFIG = {
    'gcc': 'CONFIG_CC_IS_GCC=y\n# CONFIG_CC_IS_CLANG is not set\nCONFIG_LD_IS_BFD=y\n',
    'clang': 'CONFIG_CC_IS_CLANG=y\n# CONFIG_CC_IS_GCC is not set\nCONFIG_LD_IS_LLD=y\n',
}


class KernelToolchainTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'build').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='toolchain-', dir=ROOT / 'build')
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.headers = self.tmp / 'headers $(touch HEADER_WAS_EVALUATED) with spaces'
        self.source = self.tmp / 'module ;$(touch SOURCE_WAS_EVALUATED)'
        self.output = self.tmp / 'output with spaces'
        self.bin = self.tmp / 'fake tools'
        self.trace = self.tmp / 'make.json'
        self.bin.mkdir()
        self.source.mkdir()
        (self.source / 'Kbuild').write_text('obj-m := fixture.o\nccflags-y += -Werror\n')
        for name, text in {
            'include/config/auto.conf': CONFIG['gcc'],
            'include/generated/utsrelease.h': '#define UTS_RELEASE "9.9.9-fixture"\n',
            'include/generated/compile.h': '#define LINUX_COMPILER "fixture compiler"\n',
            'Module.symvers': '0x00000000\tfixture\tvmlinux\tEXPORT_SYMBOL\n',
            'Makefile': '# Synthetic prepared headers. Never run a real build.\n',
        }.items():
            target = self.headers / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        stub = ('#!' + sys.executable + '\n'
                'import json,os,pathlib,sys\n'
                'if pathlib.Path(sys.argv[0]).name == "make":\n'
                ' pathlib.Path(os.environ["TOOLCHAIN_TRACE"]).write_text(json.dumps({\n'
                '  "argv":sys.argv[1:], "env":dict(os.environ)}))\n'
                ' sys.exit(int(os.environ.get("TOOLCHAIN_MAKE_EXIT", "0")))\n'
                'print(pathlib.Path(sys.argv[0]).name + " fixture version")\n')
        for name in TOOLS:
            path = self.bin / name
            path.write_text(stub)
            path.chmod(0o755)
        self.env = {'PATH': str(self.bin), 'TOOLCHAIN_TRACE': str(self.trace),
                    'TOOLCHAIN_SENTINEL': 'preserve this ordinary value'}

    def select(self, family):
        (self.headers / 'include/config/auto.conf').write_text(CONFIG[family])

    def plan(self, **kwargs):
        return toolchain.build_plan(self.headers, self.source,
                                    environment=self.env, **kwargs)

    def cli(self, *extra, environment=None):
        return subprocess.run(
            [sys.executable, '-B', str(HELPER), '--headers', str(self.headers),
             '--module-source', str(self.source), *extra],
            env=self.env if environment is None else environment, cwd=self.tmp,
            text=True, capture_output=True, timeout=10)

    @staticmethod
    def assignments(argv):
        return dict(arg.split('=', 1) for arg in argv if '=' in arg)

    def assert_not_built(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.trace.exists(), 'make must not run after failed preflight')

    def test_gcc_headers_select_gcc_and_disable_inherited_llvm(self):
        self.env.update(LLVM='1', CC='clang', LD='ld.lld')
        plan = self.plan()
        args = self.assignments(plan['argv'])
        self.assertEqual(plan['family'], 'gcc')
        self.assertEqual(Path(plan['compiler']), self.bin / 'gcc')
        self.assertEqual(args['LLVM'], '')
        self.assertNotIn('LLVM=0', plan['argv'])
        self.assertEqual(Path(args['CC']), self.bin / 'gcc')
        self.assertEqual(Path(args['LD']), self.bin / 'ld.bfd')
        self.assertEqual(Path(args['HOSTCXX']), self.bin / 'g++')
        self.assertFalse(self.trace.exists())

    def test_clang_headers_select_complete_llvm_family(self):
        self.select('clang')
        self.env.update(LLVM='0', CC='gcc', LD='ld.bfd')
        plan = self.plan()
        args = self.assignments(plan['argv'])
        self.assertEqual(plan['family'], 'clang')
        self.assertEqual(Path(plan['compiler']), self.bin / 'clang')
        self.assertEqual(args['LLVM'], '1')
        self.assertEqual(args['LLVM_IAS'], '1')
        for key, name in {'CC': 'clang', 'LD': 'ld.lld', 'AR': 'llvm-ar',
                          'NM': 'llvm-nm', 'STRIP': 'llvm-strip',
                          'OBJCOPY': 'llvm-objcopy', 'OBJDUMP': 'llvm-objdump',
                          'READELF': 'llvm-readelf', 'HOSTCC': 'clang',
                          'HOSTCXX': 'clang++'}.items():
            self.assertEqual(Path(args[key]), self.bin / name, key)

    def test_missing_or_ambiguous_compiler_config_stops_before_make(self):
        for config in (
            '', 'CONFIG_CC_IS_GCC=n\nCONFIG_CC_IS_CLANG=n\n',
            'CONFIG_CC_IS_GCC=y\nCONFIG_CC_IS_CLANG=y\n',
            'CONFIG_CC_IS_GCC=y\nCONFIG_CC_IS_GCC=y\n',
            'CONFIG_CC_IS_GCC=y\nCONFIG_CC_IS_CLANG=maybe\n',
            'CONFIG_CC_IS_GCC=m\n',
        ):
            with self.subTest(config=config):
                (self.headers / 'include/config/auto.conf').write_text(config)
                with self.assertRaises(ValueError):
                    self.plan()
                self.assert_not_built(self.cli())

    def test_unprepared_headers_or_missing_module_definition_stop(self):
        for path in (self.headers / 'include/config/auto.conf',
                     self.headers / 'Module.symvers',
                     self.headers / 'include/generated/utsrelease.h',
                     self.source / 'Kbuild'):
            original = path.read_bytes()
            with self.subTest(missing=str(path)):
                path.unlink()
                try:
                    self.assert_not_built(self.cli())
                finally:
                    path.write_bytes(original)

    def test_missing_selected_tools_do_not_fall_back_to_other_family(self):
        for family, name in (('gcc', 'gcc'), ('gcc', 'g++'), ('gcc', 'ld.bfd'),
                             ('clang', 'clang'), ('clang', 'clang++'), ('clang', 'ld.lld'),
                             ('clang', 'llvm-objcopy'), ('gcc', 'make')):
            self.select(family)
            tool = self.bin / name
            original = tool.read_bytes()
            with self.subTest(family=family, missing=name):
                tool.unlink()
                try:
                    self.assert_not_built(self.cli())
                finally:
                    tool.write_bytes(original)
                    tool.chmod(0o755)

    def test_make_receives_selected_paths_warnings_output_and_target(self):
        for family in ('gcc', 'clang'):
            self.select(family)
            with self.subTest(family=family):
                result = self.cli('--output', str(self.output))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                observed = json.loads(self.trace.read_text())
                args = self.assignments(observed['argv'])
                self.assertEqual(observed['argv'][:2], ['-C', str(self.headers.resolve())])
                self.assertEqual(args['M'], str(self.source.resolve()))
                self.assertEqual(args['MO'], str(self.output.resolve()))
                self.assertEqual(args['W'], '1')
                self.assertIn('-Werror', args['KCFLAGS'].split())
                self.assertEqual(observed['argv'][-1], 'modules')
                self.assertNotIn('LLVM=0', observed['argv'])
                self.assertEqual(observed['env']['TOOLCHAIN_SENTINEL'],
                                 self.env['TOOLCHAIN_SENTINEL'])

    def test_inherited_build_overrides_are_removed_without_evaluation(self):
        (self.headers / 'include/config/auto.conf').write_text(
            CONFIG['gcc'] + 'CONFIG_CMDLINE="$(touch CONFIG_WAS_EVALUATED)"\n')
        contamination = {
            name: '$(touch ENV_WAS_EVALUATED); unintended override'
            for name in ('LLVM', 'LLVM_IAS', 'CC', 'CXX', 'LD', 'AS', 'AR', 'NM',
                         'STRIP', 'OBJCOPY', 'OBJDUMP', 'READELF', 'HOSTCC',
                         'HOSTCXX', 'HOSTLD', 'HOSTAR', 'CROSS_COMPILE',
                         'CROSS_COMPILE_COMPAT', 'MAKEFLAGS', 'MAKEOVERRIDES', 'MAKEFILES',
                         'MFLAGS', 'GNUMAKEFLAGS', 'KBUILD_OUTPUT', 'KBUILD_SRC',
                         'KBUILD_EXTMOD', 'KCFLAGS', 'KCPPFLAGS', 'CFLAGS_CPP',
                         'HOSTCFLAGS', 'HOSTCXXFLAGS', 'HOSTLDFLAGS')
        }
        environment = dict(self.env, **contamination)
        before = environment.copy()
        plan = toolchain.build_plan(self.headers, self.source, environment=environment)
        self.assertEqual(environment, before, 'caller environment must not be mutated')
        for name in contamination:
            self.assertNotIn(name, plan['env'], name)
        result = self.cli(environment=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(self.trace.read_text())
        for name in contamination:
            self.assertNotIn(name, observed['env'], name)
        self.assertEqual(observed['env']['TOOLCHAIN_SENTINEL'], self.env['TOOLCHAIN_SENTINEL'])
        for marker in ('ENV_WAS_EVALUATED', 'HEADER_WAS_EVALUATED',
                       'SOURCE_WAS_EVALUATED', 'CONFIG_WAS_EVALUATED'):
            self.assertFalse((self.tmp / marker).exists())

    def test_dkms_advisory_llvm_suffix_cannot_override_gcc_headers(self):
        result = self.cli('LLVM=1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        args = self.assignments(json.loads(self.trace.read_text())['argv'])
        self.assertEqual(args['LLVM'], '')
        self.assertEqual(Path(args['CC']), self.bin / 'gcc')

    def test_unexpected_dkms_suffix_cannot_inject_make_options(self):
        for extra in (('LLVM=0',), ('CC=clang',), ('--eval=touch INJECTED',),
                      ('LLVM=1', 'CC=clang'), ('modules_install',)):
            with self.subTest(extra=extra):
                self.assert_not_built(self.cli(*extra))
        self.assertFalse((self.tmp / 'INJECTED').exists())

    def test_make_failure_is_returned_to_dkms(self):
        environment = dict(self.env, TOOLCHAIN_MAKE_EXIT='23')
        result = self.cli(environment=environment)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertTrue(self.trace.is_file())

    def test_clean_preserves_module_path_and_cannot_install(self):
        result = self.cli('--target', 'clean')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        args = json.loads(self.trace.read_text())['argv']
        self.assertEqual(args[-1], 'clean')
        self.assertEqual(self.assignments(args)['M'], str(self.source.resolve()))
        self.assertNotIn('MO', self.assignments(args))
        self.trace.unlink()
        self.assert_not_built(self.cli('--target', 'modules_install'))

    def test_dry_run_never_starts_make_or_exposes_environment_values(self):
        self.env['TOOLCHAIN_SECRET_SENTINEL'] = 'private-env-must-not-appear'
        result = self.cli('--dry-run')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.trace.exists())
        self.assertNotIn(self.env['TOOLCHAIN_SECRET_SENTINEL'], result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['family'], 'gcc')

    def test_local_builder_uses_header_selection_and_sanitized_environment(self):
        # Follow the actual local-builder entry point through the same fake
        # make. A deliberate failure ends the path before modinfo or .ko reads.
        builder_spec = importlib.util.spec_from_file_location(
            'local_kernel_builder', ROOT / 'scripts/build_kernel.py')
        builder = importlib.util.module_from_spec(builder_spec)
        with patch.dict(sys.modules, {'kernel_toolchain': toolchain}):
            builder_spec.loader.exec_module(builder)
        release = '9.9.9-fixture'
        modules = self.tmp / 'fake-module-directory'
        (modules / release).mkdir(parents=True)
        (modules / release / 'build').symlink_to(self.headers, target_is_directory=True)
        (self.tmp / 'kernel').symlink_to(self.source, target_is_directory=True)
        environment = dict(self.env, LLVM='1', CC='clang', MAKEFLAGS='-e',
                           TOOLCHAIN_MAKE_EXIT='23')

        def fixture_path(value):
            return modules if value == '/lib/modules' else Path(value)

        with patch.object(builder, 'Path', side_effect=fixture_path), \
                patch.object(builder.platform, 'release', return_value=release), \
                patch.object(builder, 'ROOT', self.tmp), \
                patch.object(builder, 'BUILD', self.output), \
                patch.object(builder, 'REPORT', self.tmp / 'reports'), \
                patch.dict(os.environ, environment, clear=True), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 23)
        observed = json.loads(self.trace.read_text())
        args = self.assignments(observed['argv'])
        self.assertEqual(args['LLVM'], '')
        self.assertEqual(Path(args['CC']), self.bin / 'gcc')
        self.assertEqual(args['MO'], str(self.output.resolve()))
        for name in ('LLVM', 'CC', 'MAKEFLAGS'):
            self.assertNotIn(name, observed['env'])
        self.assertFalse((self.output / 'gs_native.ko').exists())

    def run_fake_successful_builder(self, *, output='', make_exit=0, family='clang',
                                    vermagic=None, aliases=''):
        """Exercise reporting without running make, modinfo, or any real module."""
        self.select(family)
        builder_spec = importlib.util.spec_from_file_location(
            'reporting_kernel_builder', ROOT / 'scripts/build_kernel.py')
        builder = importlib.util.module_from_spec(builder_spec)
        with patch.dict(sys.modules, {'kernel_toolchain': toolchain}):
            builder_spec.loader.exec_module(builder)
        release = '9.9.9-fixture'
        modules = self.tmp / 'reporting-module-directory'
        (modules / release).mkdir(parents=True)
        (modules / release / 'build').symlink_to(self.headers, target_is_directory=True)
        self.output.mkdir()
        (self.output / 'gs_native.ko').write_bytes(b'\x7fELFsynthetic-module-for-hashing-only')
        reports = self.tmp / 'reporting-results'
        plan = self.plan(output=self.output)
        metadata_calls = []

        def fixture_path(value):
            return modules if value == '/lib/modules' else Path(value)

        def metadata(argv, **kwargs):
            metadata_calls.append(argv)
            if argv[0] == 'modinfo':
                if len(argv) == 2:
                    return 'filename: synthetic-module-only\n'
                return {'vermagic': vermagic if vermagic is not None else release + ' SMP',
                        'alias': aliases, 'depends': 'industrialio,kfifo_buf'}[argv[2]] + '\n'
            self.assertEqual(argv, [plan['compiler'], '--version'])
            return family + ' fixture compiler version\n'

        with patch.object(builder, 'Path', side_effect=fixture_path), \
                patch.object(builder.platform, 'release', return_value=release), \
                patch.object(builder, 'ROOT', self.tmp), \
                patch.object(builder, 'BUILD', self.output), \
                patch.object(builder, 'REPORT', reports), \
                patch.object(builder, 'build_plan', return_value=plan), \
                patch.object(builder.subprocess, 'run', return_value=
                             subprocess.CompletedProcess(plan['argv'], make_exit, '', output)), \
                patch.object(builder.subprocess, 'check_output', side_effect=metadata), \
                contextlib.redirect_stdout(io.StringIO()):
            result = builder.main()
        self.assertEqual((reports / 'kernel-build.log').read_text(), output)
        self.assertFalse(self.trace.exists(), 'No real/fake external make is needed for reporting')
        return result, json.loads((reports / 'kernel-build.json').read_text()), metadata_calls

    @staticmethod
    def compiler_advisory(*, kernel='clang version 23.1.1', module='clang version 23.1.3'):
        return ('warning: the compiler differs from the one used to build the kernel\n'
                '  The kernel was built by: ' + kernel + '\n'
                '  You are using:           ' + module + '\n')

    def test_local_builder_reports_warning_free_synthetic_build(self):
        result, report, _ = self.run_fake_successful_builder()
        self.assertEqual(result, 0)
        self.assertEqual(report['build_status'], 'passed')
        self.assertEqual((report['warnings'], report['code_warnings']), (0, 0))
        self.assertEqual(report['environment_warnings'], [])
        self.assertEqual(report['autoload_aliases'], [])
        self.assertFalse(report['loaded_or_installed'])
        self.assertFalse(report['hardware_access'])

    def test_local_builder_preserves_exact_compiler_advisory_in_report(self):
        result, report, _ = self.run_fake_successful_builder(output=self.compiler_advisory())
        self.assertEqual(result, 0)
        self.assertEqual(report['build_status'], 'passed_with_environment_warning')
        self.assertEqual((report['warnings'], report['code_warnings']), (1, 0))
        self.assertEqual(report['unclassified_warnings'], [])
        self.assertEqual(report['environment_warnings'], [{
            'kind': 'kernel_compiler_mismatch',
            'message': 'warning: the compiler differs from the one used to build the kernel',
            'kernel_compiler': 'clang version 23.1.1',
            'module_compiler': 'clang version 23.1.3',
        }])

    def test_local_builder_additional_warning_is_not_hidden_by_advisory(self):
        text = self.compiler_advisory() + 'source.c:5: warning: real diagnostic\n'
        result, report, _ = self.run_fake_successful_builder(output=text)
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual((report['warnings'], report['code_warnings']), (2, 1))
        self.assertEqual(report['unclassified_warnings'], ['source.c:5: warning: real diagnostic'])
        self.assertEqual(len(report['environment_warnings']), 1)

    def test_local_builder_records_gcc_advisory_without_switching_family(self):
        result, report, _ = self.run_fake_successful_builder(
            family='gcc', output=self.compiler_advisory(
                kernel='gcc (GCC) 16.2.0', module='gcc (GCC) 16.2.1'))
        self.assertEqual(result, 0)
        self.assertEqual(report['compiler_family'], 'gcc')
        self.assertEqual(report['build_status'], 'passed_with_environment_warning')
        self.assertEqual((report['warnings'], report['code_warnings']), (1, 0))

    def test_local_builder_incomplete_advisory_remains_fatal(self):
        result, report, _ = self.run_fake_successful_builder(
            output=self.compiler_advisory().rsplit('  You are using:', 1)[0])
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual((report['warnings'], report['code_warnings']), (1, 1))
        self.assertEqual(report['environment_warnings'], [])

    def test_local_builder_wrong_compiler_family_remains_fatal(self):
        result, report, _ = self.run_fake_successful_builder(
            output=self.compiler_advisory(kernel='gcc (GCC) 16.2.1'))
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual(report['code_warnings'], 1)
        self.assertEqual(report['environment_warnings'], [])

    def test_local_builder_warning_inside_version_line_is_not_hidden(self):
        result, report, _ = self.run_fake_successful_builder(
            output=self.compiler_advisory(module='clang version 23.1.3 warning: additional defect'))
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual(report['environment_warnings'], [])
        self.assertEqual(report['code_warnings'], 2)

    def test_local_builder_keeps_kbuild_failure_despite_known_advisory(self):
        result, report, metadata_calls = self.run_fake_successful_builder(
            output=self.compiler_advisory(), make_exit=23)
        self.assertEqual(result, 23)
        self.assertFalse(report['built'])
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual(report['returncode'], 23)
        self.assertEqual((report['warnings'], report['code_warnings']), (1, 0))
        self.assertEqual(metadata_calls, [], 'Never inspect a stale module after failed Kbuild')

    def test_local_builder_vermagic_mismatch_remains_fatal(self):
        result, report, _ = self.run_fake_successful_builder(vermagic='different-kernel SMP')
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertIn('Module vermagic does not match the running kernel', report['validation_errors'])

    def test_local_builder_automatic_usb_alias_remains_fatal(self):
        result, report, _ = self.run_fake_successful_builder(aliases='usb:unexpected')
        self.assertEqual(result, 1)
        self.assertEqual(report['build_status'], 'failed')
        self.assertEqual(report['autoload_aliases'], ['usb:unexpected'])
        self.assertIn('Module declares unexpected automatic USB aliases', report['validation_errors'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
