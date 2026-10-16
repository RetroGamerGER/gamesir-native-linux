#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Choose the prepared kernel's compiler family and run Kbuild; never load it.

DKMS and the offline builder use the same plan. Kernel configuration is parsed
as data, never sourced. The selected compiler family overrides inherited build
variables, including GNU make's recursive override variables.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SELECTORS = ('CONFIG_CC_IS_CLANG', 'CONFIG_CC_IS_GCC')
TOOLCHAINS = {
    'clang': {
        'CC': 'clang', 'LD': 'ld.lld', 'AR': 'llvm-ar', 'NM': 'llvm-nm',
        'STRIP': 'llvm-strip', 'OBJCOPY': 'llvm-objcopy', 'OBJDUMP': 'llvm-objdump',
        'READELF': 'llvm-readelf', 'HOSTCC': 'clang', 'HOSTCXX': 'clang++',
        'HOSTAR': 'llvm-ar', 'HOSTLD': 'ld.lld', 'AS': 'as',
    },
    'gcc': {
        'CC': 'gcc', 'LD': 'ld.bfd', 'AR': 'ar', 'NM': 'nm',
        'STRIP': 'strip', 'OBJCOPY': 'objcopy', 'OBJDUMP': 'objdump',
        'READELF': 'readelf', 'HOSTCC': 'gcc', 'HOSTCXX': 'g++',
        'HOSTAR': 'ar', 'HOSTLD': 'ld.bfd', 'AS': 'as',
    },
}
BUILD_ENV = frozenset({
    *TOOLCHAINS['clang'], 'CPP', 'CXX', 'LEX', 'YACC', 'PAHOLE',
    'ARCH', 'SUBARCH', 'KERNELRELEASE', 'KERNEL_SRC', 'KERNEL_DIR',
    'M', 'MO', 'O', 'W', 'V', 'C', 'KCONFIG_CONFIG',
    'MAKE', 'MAKEFLAGS', 'MAKEOVERRIDES', 'MAKEFILES', 'MFLAGS', 'GNUMAKEFLAGS',
    'MAKELEVEL', 'MAKE_RESTARTS',
    'CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'LDFLAGS', 'ASFLAGS', 'CFLAGS_CPP',
    'EXTRA_CFLAGS', 'EXTRA_AFLAGS', 'EXTRA_CPPFLAGS', 'EXTRA_LDFLAGS',
    'KCFLAGS', 'KCPPFLAGS', 'KAFLAGS', 'KRUSTFLAGS',
    'CFLAGS_KERNEL', 'CFLAGS_MODULE', 'AFLAGS_KERNEL', 'AFLAGS_MODULE',
    'RUSTFLAGS_KERNEL', 'RUSTFLAGS_MODULE', 'LDFLAGS_MODULE',
    'COMPILER_PATH', 'GCC_EXEC_PREFIX', 'CPATH', 'C_INCLUDE_PATH',
    'CPLUS_INCLUDE_PATH', 'OBJC_INCLUDE_PATH', 'LIBRARY_PATH',
    'LD_PRELOAD', 'LD_LIBRARY_PATH', 'CCC_OVERRIDE_OPTIONS', 'RC_DEBUG_OPTIONS',
})
BUILD_PREFIXES = ('LLVM', 'CROSS_COMPILE', 'KBUILD', 'HOST', 'CLANG_CONFIG_FILE_')


def kernel_family(headers):
    """Accept exactly one compiler-family selector in prepared auto.conf."""
    path = Path(headers) / 'include/config/auto.conf'
    if not path.is_file():
        raise ValueError('Prepared kernel include/config/auto.conf is missing')
    found = {}
    for line in path.read_text().splitlines():
        key, separator, value = line.strip().partition('=')
        if key not in SELECTORS:
            continue
        if not separator or key in found or value not in ('y', 'n'):
            raise ValueError('Invalid or duplicate kernel compiler-family selector')
        found[key] = value
    enabled = [name for name in SELECTORS if found.get(name) == 'y']
    if len(enabled) != 1:
        raise ValueError('Kernel compiler family is missing or contradictory')
    return 'clang' if enabled[0] == 'CONFIG_CC_IS_CLANG' else 'gcc'


def build_plan(headers, module_source, *, output=None, environment=None, target='modules'):
    """Return deterministic argv/env without executing tools or writing files."""
    if target not in ('modules', 'clean'):
        raise ValueError('Only modules and clean Kbuild targets are supported')
    headers = Path(headers).resolve()
    module_source = Path(module_source).resolve()
    family = kernel_family(headers)
    if not (module_source / 'Kbuild').is_file():
        raise ValueError('Module source Kbuild is missing')
    for relative in ('Module.symvers', 'include/generated/utsrelease.h'):
        if not (headers / relative).is_file():
            raise ValueError(f'Matching prepared kernel file missing: {relative}')
    release = (headers / 'include/generated/utsrelease.h').read_text()
    match = re.search(r'^#define UTS_RELEASE "([A-Za-z0-9._+\-]+)"$', release, re.MULTILINE)
    if not match:
        raise ValueError('Prepared kernel release is invalid')

    original = dict(os.environ if environment is None else environment)
    removed = sorted(key for key in original
                     if key in BUILD_ENV or key.startswith(BUILD_PREFIXES))
    env = {key: value for key, value in original.items() if key not in removed}
    env.setdefault('PATH', os.defpath)
    resolved = {}
    for name in dict.fromkeys(('make', *TOOLCHAINS[family].values())):
        executable = shutil.which(name, path=env['PATH'])
        if not executable:
            raise ValueError(f'Required {family} kernel build tool missing: {name}')
        resolved[name] = str(Path(executable).absolute())
    # LLVM=0 is truthy to Kbuild. Clear it explicitly for the GNU family.
    flags = ['LLVM=1', 'LLVM_IAS=1'] if family == 'clang' else ['LLVM=', 'LLVM_IAS=']
    flags += [f'{key}={resolved[name]}' for key, name in TOOLCHAINS[family].items()]
    flags += ['W=1', 'KCFLAGS=-Werror']
    argv = [resolved['make'], '-C', str(headers), f'M={module_source}']
    if output is not None:
        argv.append(f'MO={Path(output).resolve()}')
    argv += [*flags, target]
    return {'family': family, 'compiler': resolved[TOOLCHAINS[family]['CC']],
            'kernel_release': match[1], 'argv': argv, 'env': env,
            'flags': flags, 'removed_environment': removed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headers', required=True)
    parser.add_argument('--module-source', required=True)
    parser.add_argument('--output')
    parser.add_argument('--target', choices=('modules', 'clean'), default='modules')
    parser.add_argument('--dry-run', action='store_true')
    # DKMS 3.4.3 appends this heuristic hint even to a custom MAKE command.
    # Recognize it only as data; prepared auto.conf remains authoritative.
    parser.add_argument('dkms_hints', nargs='*')
    args = parser.parse_args(argv)
    if any(hint != 'LLVM=1' for hint in args.dkms_hints):
        parser.error('Unsupported DKMS build argument; only its LLVM=1 hint is accepted')
    try:
        plan = build_plan(args.headers, args.module_source, output=args.output, target=args.target)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    public = {key: value for key, value in plan.items() if key != 'env'}
    public['dkms_hints'] = args.dkms_hints
    print(json.dumps(public), flush=True)
    if args.dry_run:
        return 0
    return subprocess.run(plan['argv'], env=plan['env'], check=False).returncode


if __name__ == '__main__':
    sys.exit(main())
