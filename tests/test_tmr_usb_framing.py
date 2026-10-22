#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline C packet contract vs independent Nexus provider bytes, no devices.

These tests do not emulate the firmware or prove Windows USB transfer/padding.
The executable is our own packet builder, never an app/firmware binary.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from calibration_protocol import calibration_message


class TmrUsbFrame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / 'build/tmr-usb-framing-test'
        directory.mkdir(exist_ok=True)
        source = directory / 'emit.c'
        source.write_text(r'''
#include "gs_tmr.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
int main(int argc, char **argv) {
    gs_u8 out[64], before[64];
    (void)argv;
    if (argc == 2) {
        unsigned invalid[] = {0, 1, 5, 6, 7, 255, UINT_MAX};
        memset(before, 0xa5, 64);
        for (unsigned n=0;n<sizeof(invalid)/sizeof(invalid[0]);n++) {
            memcpy(out, before, 64);
            assert(gs_tmr_packet(out, 1, invalid[n]) == -EINVAL);
            assert(!memcmp(out, before, 64));
        }
        return 0;
    }
    for (unsigned sequence=0;sequence<256;sequence++)
        for (unsigned operation=2;operation<=4;operation++) {
            assert(gs_tmr_packet(out, sequence, operation) == 64);
            assert(fwrite(out, 1, 64, stdout) == 64);
        }
    return 0;
}
''')
        cls.binary = directory / 'emit'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-I', str(ROOT / 'src'), str(source), '-o', str(cls.binary)],
                       check=True, capture_output=True)
        cls.data = subprocess.run([str(cls.binary)], check=True, capture_output=True).stdout

    def frames(self):
        return [self.data[a:a+64] for a in range(0, len(self.data), 64)]

    def test_all_sequences_match_independent_fixed_field_vectors(self):
        self.assertEqual(len(self.data), 256 * 3 * 64)
        for sequence in range(256):
            for index, (operation, parts) in enumerate(((0, 3), (1, 0), (2, 0))):
                actual = self.frames()[sequence * 3 + index]
                expected = bytes((0x0f, 0, sequence, 3, 0xfe, operation, parts)) + bytes(57)
                self.assertEqual(actual, expected, (sequence, operation))
        # Sequence zero is a builder-boundary case, not the current owner's
        # policy: gsn_sequence allocates 1..255 and shares it with other output.

    def test_logical_payload_matches_existing_independent_provider_codec(self):
        names = ('Start', 'Finish', 'Exit')
        for sequence in range(256):
            for index, name in enumerate(names):
                frame = self.frames()[sequence * 3 + index]
                provider = calibration_message(name)
                self.assertEqual(frame[0], provider.message_type)
                self.assertEqual(frame[3], len(provider.payload))
                self.assertEqual(frame[4:7], provider.payload)

    def test_no_other_operation_can_produce_or_modify_a_frame(self):
        result = subprocess.run([str(self.binary), '--invalid-operations'],
                                check=True, capture_output=True)
        self.assertEqual(result.stdout, b'')


if __name__ == '__main__':
    unittest.main()
