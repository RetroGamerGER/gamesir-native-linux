#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic source/publication gate; no network or installed files."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_control_center_distribution as audit


class Distribution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'; self.app.mkdir()
        self.src = self.root / 'sources'; self.src.mkdir()
        (self.app / 'app.py').write_bytes(b'public fixture')
        (self.src / 'source.tar').write_bytes(b'fixture source')
        (self.src / 'COPYING').write_bytes(b'fixture license')
        checksum = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.lock = {'schema': 1, 'scope': 'control-center-corresponding-source-review',
            'appdir_files': {'app.py': checksum(self.app / 'app.py')},
            'source_files': {p.name: checksum(p) for p in self.src.iterdir()},
            'files': {'app.py': 'project'},
            'components': {'project': {'version': '1', 'license_basis': 'GPL-2.0-only',
                'sources': ['source.tar'], 'notices': ['COPYING']}},
            'runtime': {'sha256': 'a'*64, 'source_revision': 'b'*40, 'components': ['project']},
            'source_archive_name': 'fixture-sources.tar.zst',
            'license_review': {'reviewed': True, 'project_license': 'GPL-2.0-only'}}
        self.write()

    def write(self):
        (self.app / 'BUILD_INPUTS.json').write_text(json.dumps({'files': self.lock['appdir_files']}))
        (self.src / 'DISTRIBUTION_LOCK.json').write_text(json.dumps(self.lock))

    def check(self):
        return audit.verify(self.app, self.src, self.lock)

    def test_complete_corresponding_material_is_accepted_without_publication(self):
        result = self.check()
        self.assertTrue(result['technical_source_closure_verified'])
        self.assertFalse(result['publication_authorized'])
        self.assertFalse(result['legal_guarantee'])

    def test_tampered_app_or_source_or_notice_is_rejected(self):
        for folder, name in ((self.app, 'app.py'), (self.src, 'source.tar'), (self.src, 'COPYING')):
            p = folder / name; old = p.read_bytes(); p.write_bytes(b'changed')
            with self.assertRaises(ValueError): self.check()
            p.write_bytes(old)

    def test_missing_and_extra_files_are_rejected(self):
        extra = self.src / 'unexpected'; extra.write_text('unreviewed')
        with self.assertRaises(ValueError): self.check()
        extra.unlink(); (self.src / 'source.tar').unlink()
        with self.assertRaises(ValueError): self.check()

    def test_unattributed_and_unknown_components_are_rejected(self):
        for owner in (None, 'unknown'):
            self.lock['files'] = {} if owner is None else {'app.py': owner}
            with self.assertRaises(ValueError): self.check()

    def test_missing_source_and_license_evidence_are_rejected(self):
        for key in ('sources', 'notices', 'license_basis', 'version'):
            old = self.lock['components']['project'][key]
            self.lock['components']['project'][key] = []
            self.write()
            with self.assertRaises(ValueError): self.check()
            self.lock['components']['project'][key] = old

    def test_unreviewed_decisions_and_license_changes_are_rejected(self):
        for value in ({'reviewed': False, 'project_license': 'GPL-2.0-only'},
                      {'reviewed': True, 'project_license': 'GPL-3.0-only'}):
            self.lock['license_review'] = value; self.write()
            with self.assertRaises(ValueError): self.check()

    def test_path_traversal_and_symlinks_are_rejected(self):
        for value in ('../outside', '/etc/passwd', 'a/../b', './a', 'a\\b', 'a\nb'):
            with self.assertRaises(ValueError): audit.relative(value)
        p = self.src / 'COPYING'; p.unlink(); p.symlink_to(self.app / 'app.py')
        with self.assertRaises(ValueError): self.check()

    def test_manifest_and_runtime_disagreement_is_rejected(self):
        (self.app / 'BUILD_INPUTS.json').write_text('{}')
        with self.assertRaises((ValueError, KeyError)): self.check()
        self.write(); self.lock['runtime']['components'] = ['unknown']; self.write()
        with self.assertRaises(ValueError): self.check()

    def test_malformed_review_records_are_not_accepted_as_decisions(self):
        for key, value in (('license_review', []), ('components', []), ('runtime', [])):
            original = self.lock[key]; self.lock[key] = value; self.write()
            with self.assertRaises(ValueError): self.check()
            self.lock[key] = original

    def test_exact_runtime_is_bound_to_the_actual_image_without_execution(self):
        prefix = b'\x7fELF\x02\x01\x01\x00AI\x02' + b'fixture runtime'.ljust(100, b'\0')
        image = self.root / 'fixture.AppImage'; image.write_bytes(prefix + b'hsqsfixture payload')
        self.lock['runtime'].update(bytes=len(prefix), sha256=hashlib.sha256(prefix).hexdigest())
        self.assertEqual(audit.verify_image(image, self.lock), hashlib.sha256(image.read_bytes()).hexdigest())
        image.write_bytes(prefix[:-1] + b'xhsqsfixture payload')
        with self.assertRaises(ValueError): audit.verify_image(image, self.lock)

    def test_runtime_boundaries_and_unrelated_files_do_not_pass(self):
        image = self.root / 'fixture'; image.write_bytes(b'not an AppImage')
        for size in (None, True, -1, 16*1024*1024+1, 100):
            self.lock['runtime']['bytes'] = size
            with self.assertRaises(ValueError): audit.verify_image(image, self.lock)

    def archive(self, *, changes=None, extra=None, omit=None, link=False, trailing=b''):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as tar:
            entries = {p.name: p.read_bytes() for p in self.src.iterdir()}
            entries.update(changes or {}); entries.update(extra or {})
            for name, content in entries.items():
                if name == omit: continue
                info = tarfile.TarInfo('./' + name); info.size = len(content)
                if link and name == 'COPYING':
                    info.type = tarfile.SYMTYPE; info.linkname = '/etc/passwd'; info.size = 0
                tar.addfile(info, io.BytesIO(content) if info.isfile() else None)
        path = self.root / 'fixture.tar.zst'
        result = subprocess.run(['/usr/bin/zstd', '-q'], input=data.getvalue()+trailing, capture_output=True, check=True)
        path.write_bytes(result.stdout); return path

    @unittest.skipUnless(Path('/usr/bin/zstd').is_file(), 'optional source compression tool absent')
    def test_actual_sources_archive_is_verified_without_extracting(self):
        path = self.archive()
        self.assertEqual(audit.verify_source_archive(path, self.lock), hashlib.sha256(path.read_bytes()).hexdigest())

    @unittest.skipUnless(Path('/usr/bin/zstd').is_file(), 'optional source compression tool absent')
    def test_changed_extra_missing_and_linked_archive_members_are_rejected(self):
        for options in ({'changes': {'source.tar': b'changed'}}, {'extra': {'unreviewed': b'x'}},
                        {'omit': 'COPYING'}, {'link': True}, {'extra': {'../outside': b'x'}}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                audit.verify_source_archive(self.archive(**options), self.lock)

    @unittest.skipUnless(Path('/usr/bin/zstd').is_file(), 'optional source compression tool absent')
    def test_archive_lock_disagreement_is_rejected(self):
        with self.assertRaises(ValueError):
            audit.verify_source_archive(self.archive(changes={'DISTRIBUTION_LOCK.json': b'{}'}), self.lock)

    @unittest.skipUnless(Path('/usr/bin/zstd').is_file(), 'optional source compression tool absent')
    def test_hidden_trailing_payload_after_tar_end_is_rejected(self):
        with self.assertRaises(ValueError):
            audit.verify_source_archive(self.archive(trailing=b'not reviewed'), self.lock)


if __name__ == '__main__':
    unittest.main()
