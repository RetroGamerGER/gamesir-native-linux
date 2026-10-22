#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Optional helper source archive only; no authorization or installed files."""
import hashlib
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_tmr_helper as package
from tmr_wire import FILES, HELPER


class HelperSource(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_exact_eight_files_full_license_and_executable_mode(self):
        result = package.source(self.root / 'one')
        with tarfile.open(result / 'gamesir-native-tmr-helper-0.1.0.alpha1.tar.gz') as archive:
            entries = {m.name.split('/', 1)[1]: m for m in archive}
            expected = {p.lstrip('/') for p in FILES}
            expected.add('usr/share/licenses/gamesir-native-tmr-helper/COPYING')
            self.assertEqual(set(entries), expected)
            for name, item in entries.items():
                self.assertTrue(item.isfile())
                self.assertEqual(item.mode, 0o755 if name == HELPER.lstrip('/') else 0o644)
                self.assertEqual(item.uid, 0); self.assertEqual(item.gid, 0)
            self.assertEqual(archive.extractfile(entries['usr/share/licenses/gamesir-native-tmr-helper/COPYING']).read(),
                             (ROOT / 'COPYING').read_bytes())

    def test_source_is_reproducible_and_recipe_binds_exact_bytes(self):
        a, b = package.source(self.root / 'one'), package.source(self.root / 'two')
        for name in ('PKGBUILD', 'SHA256SUMS', 'gamesir-native-tmr-helper-0.1.0.alpha1.tar.gz'):
            self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
        digest = hashlib.sha256((a / 'gamesir-native-tmr-helper-0.1.0.alpha1.tar.gz').read_bytes()).hexdigest()
        self.assertIn(digest, (a / 'PKGBUILD').read_text())

    def test_existing_destination_is_preserved(self):
        dest = package.source(self.root / 'one')
        with self.assertRaises(ValueError): package.source(dest)


if __name__ == '__main__':
    unittest.main()
