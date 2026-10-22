#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic dependency-baseline preservation, no installed files or network."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_control_center_distribution as prepare


class Rebase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new = self.root / 'old', self.root / 'new'
        self.code = prepare.APP + '/app/main.py'
        self.lib = 'usr/lib/libQtFixture.so'
        for folder, version, code, lib in [(self.old, '1', b'old code', b'reviewed library'),
                                           (self.new, '2', b'new code', b'new unreviewed library')]:
            for name, data in [(self.code, code), (self.lib, lib), ('AppRun', b'fixed launcher')]:
                path = folder / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            prepare.save(folder / 'BUILD_INPUTS.json', {'files': prepare.inventory(folder),
                         'version': version, 'package_binding': {'unchanged': True},
                         'packages': {'qt': 'reviewed version'}})
        before = json.loads((self.old / 'BUILD_INPUTS.json').read_text())
        self.lock = {'appdir_files': before['files'], 'files': {
            self.code: 'project', self.lib: 'package:qt', 'AppRun': 'project'}}

    def run_rebase(self):
        return prepare.rebase_app(self.old, self.new, self.root / 'result', self.lock)

    def test_new_app_uses_exact_previous_dependency_and_its_version(self):
        meta, owners = self.run_rebase()
        result = self.root / 'result'
        self.assertEqual((result / self.code).read_bytes(), b'new code')
        self.assertEqual((result / self.lib).read_bytes(), b'reviewed library')
        self.assertEqual(meta['packages'], {'qt': 'reviewed version'})
        self.assertEqual(meta['version'], '2')
        self.assertFalse(meta['release_ready'])
        self.assertEqual(owners[self.lib], 'package:qt')
        self.assertEqual((self.old / self.code).read_bytes(), b'old code')

    def test_tampered_previous_dependency_is_refused_before_copy(self):
        (self.old / self.lib).write_bytes(b'tampered')
        with self.assertRaises(ValueError): self.run_rebase()
        self.assertFalse((self.root / 'result').exists())

    def test_tampered_current_app_is_refused_before_copy(self):
        (self.new / self.code).write_bytes(b'tampered')
        with self.assertRaises(ValueError): self.run_rebase()

    def test_project_scope_cannot_overwrite_foreign_component(self):
        self.lock['files'][self.code] = 'package:qt'
        with self.assertRaises(ValueError): self.run_rebase()

    def test_new_unattributed_dependency_is_refused(self):
        path = self.new / 'usr/lib/extra.so'; path.write_bytes(b'extra')
        meta = json.loads((self.new / 'BUILD_INPUTS.json').read_text())
        meta['files'][path.relative_to(self.new).as_posix()] = hashlib.sha256(b'extra').hexdigest()
        prepare.save(self.new / 'BUILD_INPUTS.json', meta)
        with self.assertRaises(ValueError): self.run_rebase()

    def test_project_payload_links_are_refused(self):
        path = self.new / self.code; path.unlink(); path.symlink_to(self.old / self.code)
        with self.assertRaises(ValueError): self.run_rebase()


if __name__ == '__main__':
    unittest.main()
