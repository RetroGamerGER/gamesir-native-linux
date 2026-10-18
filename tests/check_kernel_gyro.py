#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute actual registration/report adapters against fake input objects only."""
import json
import re
import subprocess
from project_paths import PROJECT, BUILD, RESULTS

source = (PROJECT / 'kernel/gs_native_usb.c').read_text()
names = ['gsn_input_register', 'gsn_gyro_register', 'gsn_gyro_report']
blocks = []
for name in names:
    match = re.search(r'^static [^;{}]*\b' + name + r'\([^;{}]*\)\n\{', source, re.M)
    assert match, name
    blocks.append(source[match.start():source.index('\n}', match.end()) + 2])
out = BUILD / 'kernel-gyro'
out.mkdir(parents=True, exist_ok=True)
(out / 'gyro-functions.h').write_text('\n\n'.join([b[:b.index('\n{')] + ';' for b in blocks] + blocks))
command = ['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
           '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-g',
           '-I', str(out), str(PROJECT / 'tests/kernel_gyro_fake.c'),
           str(PROJECT / 'src/gs_sensor.c'), '-o', str(out / 'test')]
subprocess.run(command, check=True)
result = subprocess.run([str(out / 'test')], check=True, text=True, capture_output=True)
RESULTS.mkdir(exist_ok=True)
(RESULTS / 'kernel-gyro.json').write_text(json.dumps({
    'passed': True, 'hardware_access': False, 'functions': names,
    'coverage': result.stdout.strip(), 'sanitizers': ['address', 'undefined'],
    'limits': 'Fake input boundaries; does not execute Linux input core, USB, udev or PM.'}, indent=2)+'\n')
print(result.stdout.strip())
