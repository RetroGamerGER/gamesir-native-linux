#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute the actual persistent USB claim gate against fake kernel objects."""
import hashlib
import json
import re
import subprocess
from project_paths import PROJECT, BUILD, RESULTS

source = (PROJECT / 'kernel/gs_native_usb.c').read_text()
names = ['gsn_describe', 'gsn_claim_parse', 'gsn_claim_identity', 'gsn_claim_find',
         'gsn_claim_consume', 'gsn_claim_store', 'claim_100a_store', 'claim_105e_store']
blocks = []
for name in names:
    match = re.search(r'^static [^;{}]*\b' + name + r'\([^;{}]*\)\n\{', source, re.M)
    assert match, name
    blocks.append(source[match.start():source.index('\n}', match.end()) + 2])
start = source.index('struct gsn_claim {')
structure = source[start:source.index('\n};', start) + 3]
prototypes = [block[:block.index('\n{')] + ';' for block in blocks]
BUILD.mkdir(exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)
(BUILD / 'kernel-claim-functions.h').write_text('\n\n'.join([structure, *prototypes, *blocks]) + '\n')
args = ['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
        '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-g', '-I', str(BUILD),
        str(PROJECT / 'tests/kernel_claim_fake.c'),
        *[str(PROJECT / 'src' / f'{name}.c') for name in ('gs_protocol', 'gs_runtime', 'gs_startup')],
        '-o', str(BUILD / 'test-kernel-claim')]
built = subprocess.run(args, capture_output=True, text=True, timeout=40)
(RESULTS / 'kernel-claim-build.log').write_text(built.stdout + built.stderr)
if built.returncode:
    raise SystemExit(built.stderr)
result = subprocess.run([str(BUILD / 'test-kernel-claim')], capture_output=True, text=True, timeout=30)
(RESULTS / 'kernel-claim-test.log').write_text(result.stdout + result.stderr)
if result.returncode:
    raise SystemExit(result.stdout + result.stderr)
# Also require the tested gate to precede allocation, identity publication and RX.
probe = source[source.index('static int gsn_probe('):]
assert probe.index('persistent_mode && (pid == 0x100a || pid == 0x105e) && !gsn_claim_consume(intf)') < probe.index('identity.instance =')
report = {'passed': True, 'hardware_access': False,
          'method': 'Actual extracted claim/parser/descriptor/probe gate C functions; fake USB core and locks',
          'functions': names, 'sanitizers': ['address', 'undefined'], 'coverage': result.stdout.strip(),
          'source_sha256': {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in
                            ['kernel/gs_native_usb.c', 'tests/kernel_claim_fake.c', 'tests/check_kernel_claim.py']},
          'limits': ['USB core attach, locks and kernfs inode objects are simulated; no real hotplug proof.',
                     'Initial manager-side xpad-unbind sysfs race remains outside this claim gate.']}
(RESULTS / 'kernel-claim-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(result.stdout.strip())
