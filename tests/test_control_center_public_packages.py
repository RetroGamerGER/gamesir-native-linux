#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Public release pin consistency, no network/host/helper/package operations."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import BackendError, COMPONENTS, PUBLIC_BINARIES
from app_packages import load_bundle
from package_catalog import CATALOG, parse_catalog
from package_client import FILES
from release_download import parse_assets

REVIEW = ROOT / 'packaging/control-center/releases/v0.1.0-pre-alpha.3'


class PublicPackagePins(unittest.TestCase):
    def setUp(self):
        self.data = (REVIEW / 'REVIEWED_PACKAGES.json').read_bytes()
        self.trust = parse_catalog(self.data)
        self.assets = parse_assets((REVIEW / 'release-assets.json').read_bytes(), self.trust.catalog)

    def test_exact_four_components_have_public_source_provenance(self):
        self.assertEqual({r.component for r in self.trust.catalog.records}, set(COMPONENTS))
        self.assertEqual({r.source_commit for r in self.trust.catalog.records},
                         {'b5b9cc34534e5afdb6505322308b364f15e31c2b'})
        self.assertEqual({r.tag for r in self.trust.catalog.records}, {'v0.1.0-pre-alpha.3'})
        for a in self.assets:
            name, arch = COMPONENTS[a.component]
            self.assertEqual(a.filename, f'{name}-{a.review.version}-{arch}.pkg.tar.zst')
            self.assertIn('/RetroGamerGER/gamesir-native-linux/releases/download/', a.url)

    def test_removal_records_and_previously_reviewed_upgrade_are_retained(self):
        for r in self.trust.catalog.records:
            installed = self.trust.installed_record(r.component, r.version)
            self.assertEqual(installed.guards, r.guards)
        steam = next(r for r in self.trust.catalog.records if r.component == 'steam')
        self.assertEqual(steam.upgrade_from, ('0.1.0.alpha1-1',))
        self.trust.installed_record('steam', steam.upgrade_from[0])

    def test_remote_or_changed_bytes_cannot_self_approve(self):
        for r in self.trust.catalog.records:
            with self.assertRaisesRegex(BackendError, 'no_reviewed_binary'):
                self.trust.catalog.verify(r.component, b'newer version or modified same-version asset')
        with self.assertRaisesRegex(BackendError, 'unreviewed_installed_version'):
            self.trust.installed_record('core', '0.1.0.alpha3-17')

    def test_explicit_metadata_bundle_is_loaded_without_embedded_package_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'REVIEWED_PACKAGES.json').write_bytes(self.data)
            (root / 'release-assets.json').write_bytes((REVIEW / 'release-assets.json').read_bytes())
            pins = [[p, hashlib.sha256(self.data).hexdigest() if p == CATALOG else 'a'*64] for p in FILES]
            profile = dict(schema=1, scope='local_review', pins=pins, distribution='garuda', kernel='test-kernel')
            (root / 'profile.json').write_text(json.dumps(profile))
            bundle = load_bundle(root)
            self.assertFalse(bundle.blobs)
            self.assertEqual(len(bundle.release_assets), 4)
            # An otherwise valid catalog cannot bypass the independently pinned helper catalog.
            changed = json.loads(self.data)
            changed['packages'][0]['digest'] = 'b'*64
            (root / 'REVIEWED_PACKAGES.json').write_text(json.dumps(changed))
            with self.assertRaisesRegex(BackendError, 'bundle_catalog_mismatch'):
                load_bundle(root)

    def test_source_default_does_not_enable_remote_trust_implicitly(self):
        self.assertFalse(PUBLIC_BINARIES.records)


if __name__ == '__main__':
    unittest.main()
