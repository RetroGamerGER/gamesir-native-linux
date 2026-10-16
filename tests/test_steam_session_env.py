#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Source the optional session hint in child shells; never start SDL or Steam."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tools/sdl/gamesir-plasma-env.sh'
GUID = '03004535373500009c10000053010000'
ZZZ_GUID = '03004535373500005e10000007060000'
# Freeze the previously hardware-confirmed line independently of the helper.
STANDARD_MAPPING = (GUID + ',GameSir G7 Pro,a:b0,b:b1,x:b2,y:b3,back:b6,guide:b8,start:b7,'
                    'leftstick:b9,rightstick:b10,leftshoulder:b4,rightshoulder:b5,'
                    'dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,misc1:b16,'
                    'leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,'
                    'paddle1:b12,paddle2:b11,paddle3:b14,paddle4:b13,platform:Linux,crc:3545,')
ZZZ_MAPPING = ZZZ_GUID + STANDARD_MAPPING[len(GUID):]
sys.path.insert(0, str(ROOT / 'tools/sdl'))
from steam_mapping_audit import audit_text


def sourced(hints=None, times=1):
    # Explicit minimal environment: never consume the developer's live hints.
    env = {'PATH': '/usr/bin:/bin', 'KEEP_SESSION_SENTINEL': 'unchanged',
           **(hints or {})}
    command = '. "$1"; ' * times + 'exec "$2" -B -c "$3"'
    result = subprocess.run(['/bin/sh', '-c', command, 'session-hint-test',
                             str(HELPER), sys.executable,
                             'import json,os; print(json.dumps(dict(os.environ)))'],
                            env=env, text=True, capture_output=True, check=True,
                            timeout=5)
    if result.stderr:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class SteamSessionEnvironment(unittest.TestCase):
    def test_unset_and_empty_use_audited_target_mapping(self):
        for hints in ({}, {'SDL_GAMECONTROLLERCONFIG': ''}):
            with self.subTest(hints=hints):
                env = sourced(hints)
                value = env['SDL_GAMECONTROLLERCONFIG']
                self.assertEqual(value.splitlines(), [STANDARD_MAPPING, ZZZ_MAPPING])
                for pid, guid, line in zip(('109c', '105e'), (GUID, ZZZ_GUID), value.splitlines()):
                    result = audit_text('SDL Mapping for 3537/' + pid + ': ' + line, guid)
                    self.assertEqual(result['status'], 'already_matches')
                    self.assertTrue(result['standard_bindings_unchanged'])
                    # Keep name restriction explicit: do not broaden the
                    # same-PID xpad/CRC fallback to native alpha17 capabilities.
                    self.assertIn('crc:3545,', line)
                    self.assertIn('misc1:b16,', line)
                    self.assertNotIn('misc2:', line)
                    if pid == '105e':
                        self.assertEqual(result['physical_paddle_labels'], 'unconfirmed')

    def test_other_controller_mapping_is_preserved_exactly(self):
        prior = '030000005e0400008e02000001000000,Other Controller,a:b1,b:b0,platform:Linux,'
        for value in (prior, prior + '\n'):
            with self.subTest(trailing_newline=value.endswith('\n')):
                result = sourced({'SDL_GAMECONTROLLERCONFIG': value})
                self.assertTrue(result['SDL_GAMECONTROLLERCONFIG'].startswith(value + '\n'))
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(GUID + ','), 1)
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(ZZZ_GUID + ','), 1)

    def test_repeated_sourcing_has_no_duplicate_or_other_environment_change(self):
        once = sourced()
        self.assertEqual(sourced(times=3), once)
        self.assertEqual({k: v for k, v in once.items() if k != 'SDL_GAMECONTROLLERCONFIG'},
                         sourced(times=0))

    def test_existing_target_conflict_is_never_replaced(self):
        for guid, addition in ((GUID, ZZZ_MAPPING), (GUID.upper(), ZZZ_MAPPING),
                               (ZZZ_GUID, STANDARD_MAPPING), (ZZZ_GUID.upper(), STANDARD_MAPPING)):
            for prefix in ('', 'other-controller-line\n'):
                with self.subTest(guid=guid, prefix=prefix):
                    value = prefix + guid + ',My Mapping,a:b7,paddle1:b0,\n'
                    result = sourced({'SDL_GAMECONTROLLERCONFIG': value}, times=2)
                    self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'], value + '\n' + addition)

    def test_either_or_both_existing_defaults_are_idempotent(self):
        for value, expected in ((STANDARD_MAPPING, STANDARD_MAPPING + '\n' + ZZZ_MAPPING),
                                (ZZZ_MAPPING, ZZZ_MAPPING + '\n' + STANDARD_MAPPING),
                                (STANDARD_MAPPING + '\n' + ZZZ_MAPPING,
                                 STANDARD_MAPPING + '\n' + ZZZ_MAPPING)):
            with self.subTest(value=value):
                self.assertEqual(sourced({'SDL_GAMECONTROLLERCONFIG': value}, times=3)
                                 ['SDL_GAMECONTROLLERCONFIG'], expected)

    def test_mixed_user_families_are_preserved_in_any_order(self):
        standard = '0300bEeF373500009C100000aBcD0000,User standard,a:b8,'
        zzz = '03000000373500005E10000000000000,User ZZZ,paddle1:b0,crc:1234,'
        for value in (standard + '\n' + zzz, zzz + '\n' + standard + '\n'):
            hints = {'SDL_GAMECONTROLLERCONFIG': value, 'OTHER_HINT': 'original'}
            with self.subTest(value=value):
                self.assertEqual(sourced(hints, times=3), sourced(hints, times=0))

    def test_existing_usb_evdev_family_mapping_is_never_overridden(self):
        # SDL moves GUID CRC into a mapping field and may ignore the version.
        # Preserve the whole family conservatively, even when fields differ.
        variants = (
            ('03000000373500009c10000053010000', ''),
            ('03000000373500009c10000053010000', 'crc:3545,'),
            ('03000000373500009c10000053010000', 'crc:1234,'),
            ('03004535373500009c10000054010000', ''),
            ('03000000373500009c10000000000000', ''),
            ('0300bEeF373500009C100000aBcD0000', ''),
        )
        for base_guid, fields in variants:
            for guid, addition in ((base_guid, ZZZ_MAPPING),
                                   (base_guid.replace('9c10', '5e10').replace('9C10', '5E10'),
                                    STANDARD_MAPPING)):
                for prefix in ('', 'other-guid,Other mapping,a:b0,\n'):
                    with self.subTest(guid=guid, fields=fields, prefix=prefix):
                        value = prefix + guid + ',User mapping,a:b7,' + fields + 'platform:Linux,\n'
                        hints = {'SDL_GAMECONTROLLERCONFIG': value}
                        actual = sourced(hints, times=2)
                        self.assertEqual(actual['SDL_GAMECONTROLLERCONFIG'], value + '\n' + addition)
                        del actual['SDL_GAMECONTROLLERCONFIG']
                        self.assertEqual(actual, sourced(times=0))

    def test_other_identity_transport_or_backend_does_not_block_addition(self):
        variants = (
            '03000000373500000a10000053010000',  # XInput PID 100a.
            '03000000383500009c10000053010000',  # Different VID.
            '05000000373500009c10000053010000',  # Bluetooth transport.
            '03000000373500009c10000053016800',  # SDL HIDAPI backend.
            '0300zzzz373500009c10000053010000',  # Invalid CRC hex.
            '03000000373500009c100000zzzz0000',  # Invalid version hex.
            '03000000373500009c1000005301000',   # Truncated GUID.
        )
        variants += tuple(guid.replace('9c10', '5e10') for guid in variants if '9c10' in guid)
        for guid in variants:
            with self.subTest(guid=guid):
                value = guid + ',Other mapping,a:b7,platform:Linux,'
                result = sourced({'SDL_GAMECONTROLLERCONFIG': value}, times=2)
                self.assertTrue(result['SDL_GAMECONTROLLERCONFIG'].startswith(value + '\n'))
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(GUID + ','), 1)
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(ZZZ_GUID + ','), 1)

    def test_only_a_mapping_line_prefix_counts_as_existing_target(self):
        for guid in (GUID, ZZZ_GUID, '03000000373500009c10000000000000',
                     '03000000373500005e10000000000000'):
            with self.subTest(guid=guid):
                value = 'other-guid,Name contains ' + guid + ',a:b0,'
                result = sourced({'SDL_GAMECONTROLLERCONFIG': value})
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].splitlines()[0], value)
                self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].splitlines(),
                                 [value, STANDARD_MAPPING, ZZZ_MAPPING])

    def test_nonempty_file_hint_prevents_all_changes(self):
        for prior in (None, '', 'other-guid,Existing mapping,a:b1,'):
            hints = {'SDL_GAMECONTROLLERCONFIG_FILE': '/nonexistent/mapping file.txt',
                     'SDL_JOYSTICK_HIDAPI': '0', 'UNRELATED_VARIABLE': 'original'}
            if prior is not None:
                hints['SDL_GAMECONTROLLERCONFIG'] = prior
            with self.subTest(prior=prior):
                self.assertEqual(sourced(hints, times=2), sourced(hints, times=0))

    def test_empty_file_hint_permits_addition_and_preserves_other_hints(self):
        hints = {'SDL_GAMECONTROLLERCONFIG_FILE': '',
                 'SDL_JOYSTICK_HIDAPI': '0', 'UNRELATED_VARIABLE': 'original'}
        result = sourced(hints)
        self.assertTrue(result['SDL_GAMECONTROLLERCONFIG'].startswith(GUID + ','))
        for key, value in hints.items():
            self.assertEqual(result[key], value)

    def test_explicit_disable_prevents_all_changes(self):
        for prior in (None, '', 'other-guid,Existing mapping,a:b1,'):
            hints = {'GAMESIR_NATIVE_STEAM_DISABLE': '1'}
            if prior is not None:
                hints['SDL_GAMECONTROLLERCONFIG'] = prior
            with self.subTest(prior=prior):
                self.assertEqual(sourced(hints, times=2), sourced(hints, times=0))
        result = sourced({'GAMESIR_NATIVE_STEAM_DISABLE': '0'})
        self.assertEqual(result['GAMESIR_NATIVE_STEAM_DISABLE'], '0')
        self.assertTrue(result['SDL_GAMECONTROLLERCONFIG'].startswith(GUID + ','))

    def test_quoted_existing_content_is_data_not_shell_code(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'must not exist'
            payload = 'other-guid,Quotes " and $(touch ' + shlex.quote(str(marker)) + ') '
            payload += '`touch ' + shlex.quote(str(marker)) + '`,a:b0,'
            result = sourced({'SDL_GAMECONTROLLERCONFIG': payload}, times=2)
            self.assertFalse(marker.exists())
            self.assertTrue(result['SDL_GAMECONTROLLERCONFIG'].startswith(payload + '\n'))
            self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(GUID + ','), 1)
            self.assertEqual(result['SDL_GAMECONTROLLERCONFIG'].count(ZZZ_GUID + ','), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
