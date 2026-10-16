#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run installed SDL against synthetic keys/FF inside audited, device-free bwrap."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/sdl-buttons-test'
REPORT = ROOT / 'build/results/sdl-buttons'
sys.path.insert(0, str(ROOT / 'tools/sdl'))
import gamesir_mapping as mapper  # noqa: E402
import steam_mapping_audit as steam_audit  # noqa: E402

# Sanitized native metadata from the completed 2026-10-14 105e trial. This
# fixture derives an SDL GUID; no real application/backend GUID was recorded.
ZZZ_METADATA = {'name': 'GameSir G7 Pro', 'bustype': '0003', 'vendor': '3537',
                'product': '105e', 'version': '0607',
                'capabilities': {'ev': '20000b', 'abs': '3003f',
                    'key': '1f 0 0 0 0 0 0 7cdb000000000000 0 8000000000 0 0',
                    'ff': '107030000 0'}}


def bitmap_codes(value):
    bits = int(''.join(word.zfill(16) for word in value.split()), 16)
    return [index for index in range(bits.bit_length()) if bits & (1 << index)]


def native_zzz_hint():
    source = (ROOT / 'tools/sdl/gamesir-plasma-env.sh').read_text()
    value = re.search(r'(03004535373500005e10000007060000,[^"\n]+)', source)[1]
    assert value.endswith(',') and ',crc:3545,' in value
    return value


def run(args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f'{args}\n{result.stdout}\n{result.stderr}')
    return result.stdout + result.stderr


def main():
    assert bitmap_codes(ZZZ_METADATA['capabilities']['key']) == sorted(mapper.PROFILES['alpha17'])
    assert bitmap_codes(ZZZ_METADATA['capabilities']['abs']) == [0, 1, 2, 3, 4, 5, 16, 17]
    assert bitmap_codes(ZZZ_METADATA['capabilities']['ff']) == [80, 81, 88, 89, 90, 96]
    BUILD.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    fixture = BUILD / 'fixture'
    (fixture / 'evdev').mkdir(parents=True, exist_ok=True)
    (fixture / 'sys').mkdir(exist_ok=True)
    for path in ('evdev/event0','iio-device','sandbox-marker'):
        (fixture / path).write_bytes(b'')
    shutil.copyfile(ROOT / 'tests/audit_sdl_sandbox.py', BUILD / 'audit_sdl_sandbox.py')
    flags = ['clang','-std=c11','-Wall','-Wextra','-Werror','-O2']
    run(flags + ['-shared','-fPIC',str(ROOT/'tests/sdl_buttons_fixture.c'),'-ldl','-o',str(BUILD/'fixture.so')])
    for version in (3,2):
        run(flags + (['-DTEST_SDL2'] if version == 2 else []) + [str(ROOT/'tests/sdl_buttons_probe.c'),f'-lSDL{version}','-ldl','-o',str(BUILD/f'probe{version}')])
    host_ns = {name: os.readlink('/proc/self/ns/'+name) for name in ('mnt','user','pid','net','ipc','uts')}
    results = []
    for version in (3,2):
        for product, profile in (('109c', 'native15'), ('109c', 'alpha17'), ('105e', 'alpha17'), ('105e', 'xpad11')):
            guid = None
            variants = (('native-hint',) if profile == 'xpad11' else
                        ('automatic', 'mapped', 'steam-proposal') if profile == 'alpha17' else ('automatic', 'mapped'))
            for variant in variants:
                explicit = variant != 'automatic'
                scenario = product + '-' + profile + '-' + variant
                mapping = native_zzz_hint() if profile == 'xpad11' else mapper.mapping(guid,profile) if explicit else None
                if variant == 'steam-proposal':
                    # Reproduce the observed shape with a synthetic GUID:
                    # misc1 is present; misc2 and all four paddles are absent.
                    prior = ','.join(part for part in mapping.split(',')
                                     if not part.startswith(('paddle', 'misc2:')))
                    proposal = steam_audit.audit_text(f'SDL Mapping for 3537/{product}: ' + prior)
                    assert {field['field'] for field in proposal['field_diff']} == steam_audit.PADDLE_FIELDS
                    mapping = proposal['candidate_mapping']
                    assert 'misc1:b16,' in mapping and 'misc2:' not in mapping
                args = ['bwrap','--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL',
                    '--clearenv','--setenv','PATH','/usr/bin','--setenv','HOME','/tmp',
                    '--setenv','GS_HOST_NS',json.dumps(host_ns),'--setenv','GS_SCENARIO',scenario,
                    '--setenv','GS_VARIANT',product]
                if explicit:
                    args += ['--setenv','GS_MAPPING',mapping]
                if profile == 'xpad11':
                    args += ['--setenv','SDL_GAMECONTROLLERCONFIG',mapping]
                args += ['--ro-bind','/usr','/usr','--symlink','usr/lib','/lib','--symlink','usr/lib','/lib64',
                    '--proc','/proc','--dev','/dev','--ro-bind',str(fixture/'sys'),'/sys',
                    '--tmpfs','/run','--tmpfs','/tmp','--ro-bind',str(fixture),'/fixture',
                    '--ro-bind',str(fixture/'iio-device'),'/dev/iio:device0',
                    '--ro-bind',str(BUILD),'/tests','--chdir','/tmp',
                    '/usr/bin/python','/tests/audit_sdl_sandbox.py',f'/tests/probe{version}']
                output = run(args)
                name = f'sdl{version}-{scenario}.log'
                (REPORT/name).write_text(output)
                guid = re.search(r'guid=([0-9a-f]{32})',output)[1]
                identity_version = '0607' if product == '105e' else '0001'
                if profile == 'xpad11':
                    passed = ('mapping_scope_negative=xpad105e native_hint_applied=0' in output and
                              'result=PASS' in output and 'raw_buttons=11' in output and
                              'iio opens=0;' in output and '"all_six_separate": true' in output)
                    results.append({'SDL_API':version, 'product':product, 'input_version':identity_version,
                                    'profile':profile, 'explicit_mapping':True, 'guid':guid, 'passed':passed,
                                    'log':name, 'mapping':mapping, 'mapping_variant':variant,
                                    'guid_source':'installed SDL, synthetic xpad-equivalent metadata fixture',
                                    'hardware_guid_observed':False, 'native_hint_applied':False,
                                    'synthetic_key_edges':0})
                    continue
                if not explicit:
                    print(json.dumps({'SDL_API':version, 'product':product, 'profile':profile,
                                      'synthetically_derived_guid':guid, 'hardware_guid_observed':False}), flush=True)
                edges = int(re.search(r'tested_keys=\d+ edges=(\d+)', output)[1])
                passed = ('result=PASS' in output and 'iio opens=0;' in output and
                          '"all_six_separate": true' in output and 'trigger_rumble=0' in output and
                          'combination_masks=32 combination_frames=34 combination_key_edges=62 held_duplicate_and_release=PASS' in output and
                          'axis_snapshots=18 dpad_snapshots=9 standard_controls=PASS' in output and
                          f'synthetic_identity=3537:{product} version={identity_version} hardware_guid_observed=0' in output and
                          'steam_ui_verified=0' in output)
                results.append({'SDL_API':version,'product':product,'input_version':identity_version,
                                'profile':profile,'explicit_mapping':explicit,'guid':guid,
                                'guid_source':'installed SDL, synthetic evdev metadata fixture',
                                'hardware_guid_observed':False,
                                'passed':passed,'log':name,'mapping':mapping,'mapping_variant':variant,
                                'synthetic_key_edges':edges,'combination_masks':32,'combination_frames':34,
                                'axis_snapshots':18,'dpad_snapshots':9})
    report = {'schema':3,'hardware_access':False,'uinput_devices':False,'system_changes':False,
              'zzz_captured_metadata_replayed_synthetically':ZZZ_METADATA,
              'hardware_guid_observed':False,
              'synthetic_key_edges':sum(r['synthetic_key_edges'] for r in results),
              'steam_ui_verified':False,'game_binding_verified':False,
              'physical_labels_confirmed':False,'packages':run(['pacman','-Q','sdl3','sdl2-compat']).strip(),
              'all_passed':all(r['passed'] for r in results),'results':results}
    (REPORT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'all_passed':report['all_passed'],'cases':len(results),'reports':str(REPORT)}))
    return not report['all_passed']


if __name__ == '__main__':
    sys.exit(main())
