#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise actual kernel startup functions with fake USB objects/syscalls only."""
import hashlib
import json
import re
import subprocess
from project_paths import PROJECT, BUILD, RESULTS

source = (PROJECT / 'kernel/gs_native_usb.c').read_text()
names = ['gsn_boot_delete', 'gsn_now_us', 'gsn_now_ms', 'gsn_delete', 'gsn_sequence',
         'gsn_fault', 'gsn_send', 'gsn_stop', 'gsn_flush_motors', 'gsn_check_idle', 'gsn_service',
         'gsn_open', 'gsn_release', 'gsn_start', 'gsn_root', 'gsn_boot_route', 'gsn_boot_owned_route',
         'gsn_describe', 'gsn_boot_cancel_device', 'gsn_boot_detach', 'gsn_boot_pending',
         'gsn_boot_connect', 'gsn_boot_rx', 'gsn_boot_adopt', 'gsn_boot_service',
         'gsn_boot_find', 'gsn_boot_handover', 'gsn_bootstrap', 'gsn_boot_status', 'gsn_quiesce',
         'gsn_resume_session', 'gsn_failed_boot_owned', 'gsn_end', 'gsn_ioctl',
         'gsn_sample_snapshot', 'gsn_play_effect', 'gsn_suspend', 'gsn_resume',
         'gsn_pre_reset', 'gsn_shutdown', 'gsn_pad', 'gsn_neutral', 'gsn_neutral_locked',
         'gsn_rx', 'gsn_imu', 'gsn_boot_rx_teardown', 'gsn_boot_old_rx', 'gsn_boot_retire_rx']
# Whole source blocks, never a translated/reimplemented copy of the adapter.
def function(name):
    match = re.search(r'^static [^;{}]*\b' + name + r'\([^;{}]*\)\n\{', source, re.M)
    assert match, name
    end = source.index('\n}', match.end()) + 2  # Kernel top-level closing brace.
    return source[match.start():end]

structs = []
for name in ('gsn_boot', 'gsn_device', 'gsn_boot_search'):
    start = source.index(f'struct {name} {{')
    structs.append(source[start:source.index('\n};', start) + 3])
blocks = [function(name) for name in names]
prototypes = [block[:block.index('\n{')] + ';' for block in blocks]
BUILD.mkdir(exist_ok=True)
(BUILD / 'kernel-startup-functions.h').write_text('\n\n'.join(structs + prototypes + blocks) + '\n')
args = ['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
        '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-g', '-I', str(BUILD),
        str(PROJECT / 'tests/kernel_startup_fake.c'),
        *[str(PROJECT / 'src' / f'{name}.c') for name in ('gs_protocol', 'gs_runtime', 'gs_startup', 'gs_sensor')],
        '-o', str(BUILD / 'test-kernel-startup')]
built = subprocess.run(args, capture_output=True, text=True, timeout=40)
RESULTS.mkdir(parents=True, exist_ok=True)
(RESULTS / 'kernel-startup-build.log').write_text(built.stdout + built.stderr)
if built.returncode:
    raise SystemExit(built.stderr)
result = subprocess.run([str(BUILD / 'test-kernel-startup')], capture_output=True, text=True, timeout=30)
(RESULTS / 'kernel-startup-test.log').write_text(result.stdout + result.stderr)
if result.returncode:
    raise SystemExit(result.stdout + result.stderr)
report = {'passed': True, 'hardware_access': False, 'method': 'Actual extracted kernel C functions; synthetic USB tree, enumeration, ownership, workqueue, time and syscalls',
          'functions': names, 'sanitizers': ['address', 'undefined'], 'coverage': result.stdout.strip(),
          'source_sha256': {name: hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in
                            ['kernel/gs_native_usb.c', 'src/gs_startup.c', 'src/gs_sensor.c',
                             'tests/kernel_startup_fake.c', 'tests/check_kernel_startup.py']},
          'limits': ['Does not execute Linux USB/input/IIO cores or real kernel locks/URBs.',
                     'Probe allocation/registration is simulated; the actual full module is built and analyzed separately.',
                     'No proof of race freedom, cold-start hardware success or suspend/resume support.']}
(RESULTS / 'kernel-startup-test.json').write_text(json.dumps(report, indent=2) + '\n')
print(result.stdout.strip())
