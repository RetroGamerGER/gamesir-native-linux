#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure mapping-contract tests; no SDL initialization or device access."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mapping', ROOT/'tools/sdl/gamesir_mapping.py')
mapper = importlib.util.module_from_spec(spec); spec.loader.exec_module(mapper)
GUID = '03004535373500009c10000001000000'  # Synthetic fixture only; no hardware GUID claim.
ZZZ_GUID = '03004535373500005e10000007060000'  # SDL fixture-derived 105e/0607 candidate, not a live Steam GUID.


class Mapping(unittest.TestCase):
    def fields(self, profile='alpha17'):
        return dict(part.split(':',1) for part in mapper.mapping(GUID,profile).split(',')[2:] if part)

    def test_four_paddles_independent_of_all_standard_buttons(self):
        normal = {name:f'b{i}' for i,name in enumerate(('a','b','x','y','leftshoulder','rightshoulder','back','start','guide','leftstick','rightstick'))}
        for profile in mapper.PROFILES:
            fields = self.fields(profile)
            self.assertEqual({name:fields[name] for name in normal},normal)
            self.assertEqual({name:fields[name] for name in ('paddle1','paddle2','paddle3','paddle4')},
                             {'paddle1':'b12','paddle2':'b11','paddle3':'b14','paddle4':'b13'})
            button_targets = [v for v in fields.values() if v.startswith('b') and v[1:].isdecimal()]
            self.assertEqual(len(button_targets),len(set(button_targets)))

    def test_axes_and_dpad_preserved(self):
        fields = self.fields()
        self.assertEqual([fields[key] for key in ('leftx','lefty','rightx','righty','lefttrigger','righttrigger')],
                         ['a0','a1','a3','a4','a2','a5'])
        self.assertEqual([fields[key] for key in ('dpup','dpright','dpdown','dpleft')],['h0.1','h0.2','h0.4','h0.8'])

    def test_extra_alpha_keys_are_not_mistaken_for_paddles(self):
        self.assertEqual(self.fields()['misc1'],'b16')
        self.assertEqual(self.fields()['misc2'],'b15')
        self.assertNotIn('misc1',self.fields('native15'))

    def test_rejects_xpad_other_vid_and_non_evdev(self):
        for base in (GUID, ZZZ_GUID):
            for guid in (base[:16] + '0a10' + base[20:],
                         base[:16] + '2210' + base[20:],
                         base[:16] + '5d10' + base[20:],
                         base[:16] + 'bb10' + base[20:],
                         base.replace('3735', '5e04'), '0500' + base[4:],
                         base[:28] + '6800', 'not-a-guid', base + ',a:b9'):
                with self.subTest(guid=guid),self.assertRaises(ValueError):
                    mapper.mapping(guid)

    def test_105e_reuses_native_order_and_preserves_its_own_identity(self):
        self.assertEqual(mapper.native_guid_pid(GUID), 0x109c)
        self.assertEqual(mapper.native_guid_pid(ZZZ_GUID), 0x105e)
        for profile in mapper.PROFILES:
            with self.subTest(profile=profile):
                value = mapper.mapping(ZZZ_GUID, profile)
                self.assertTrue(value.startswith(ZZZ_GUID + ',GameSir G7 Pro,'))
                self.assertEqual(value.replace(ZZZ_GUID, GUID), mapper.mapping(GUID, profile))
                self.assertEqual(mapper.mapping(ZZZ_GUID.upper(), profile), value)

    def test_unknown_profile_and_case(self):
        self.assertEqual(mapper.mapping(GUID.upper()),mapper.mapping(GUID))
        with self.assertRaises(ValueError):
            mapper.mapping(GUID,'guessed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
