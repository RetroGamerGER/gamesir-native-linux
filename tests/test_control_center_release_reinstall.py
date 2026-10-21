#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Remove -> fresh session -> release reinstall; synthetic inventory/HTTPS only.

No installed package database, package hooks, devices, helper or root calls.
This verifies orchestration/protocol boundaries, not real DKMS removal.
"""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import BackendError, COMPONENTS
from app_packages import AppImageTransactions
from release_download import ReleaseAsset, ReleaseDownloader, serialize_assets
from test_control_center_app_packages import fixture, FakeTransport, Adapter
from test_control_center_release_download import Client, Reply


class Reinstall(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        _, self.trust = fixture(self.root)
        self.blobs = {r.component: (self.root / (r.component + '.pkg.tar.zst')).read_bytes()
                      for r in self.trust.catalog.records}
        self.assets = tuple(ReleaseAsset(r.component, 'offline-reinstall-' + r.component + '.pkg.tar.zst', r)
                            for r in self.trust.catalog.records)
        for p in self.root.glob('*.pkg.tar.zst'): p.unlink()
        (self.root / 'release-assets.json').write_bytes(serialize_assets(self.assets))
        self.adapter, self.client = Adapter(), Client([])
        self.unrelated = self.adapter.host.installed

    def seed(self, components):
        rows = [(COMPONENTS[r.component][0], r.version)
                for r in self.trust.catalog.records if r.component in components]
        self.original = tuple(sorted((*self.unrelated, *rows)))
        self.adapter.host = replace(self.adapter.host, installed=self.original,
                                    native_loaded=True, service_enabled=True)

    def session(self):
        tx = AppImageTransactions(self.root, clock=lambda: 100,
            downloader=ReleaseDownloader(self.client, clock=lambda: 100),
            reader=lambda request: Mock(collect=self.adapter.observe),
            transport_factory=lambda pins: FakeTransport(pins, self.adapter, self.trust))
        task = tx.initial_inspection(); self.assertTrue(tx.receive_inspection(task, task.run()))
        return tx

    def prepare(self, tx, operation, components):
        self.assertTrue(tx.request(operation))
        for component in COMPONENTS: tx.select(component, component in components)
        task = tx.begin_preparation()
        return tx.receive_inspection(task, task.run())

    def confirm(self, tx):
        submission = tx.begin(); self.assertIsNotNone(submission)
        outcome = submission.run(); self.assertTrue(tx.finish(submission, outcome))
        return outcome

    def remove(self, components):
        tx = self.session(); self.assertTrue(self.prepare(tx, 'remove', components))
        self.assertEqual(set(tx.session.plan.packages), {COMPONENTS[c][0] for c in components})
        self.assertFalse(tx.transport.sent); self.assertFalse(self.client.calls)
        self.assertEqual(self.confirm(tx).state, 'verified_success')
        self.assertTrue(self.adapter.guard)
        self.assertEqual(self.adapter.host.installed, self.unrelated)
        self.assertFalse(self.adapter.host.native_loaded or self.adapter.host.service_enabled)
        # Successful removal cannot chain into installation in the same session.
        self.assertFalse(tx.request('install')); self.assertIsNone(tx.begin())
        self.assertFalse(self.client.calls)
        return tx

    def roundtrip(self, components):
        self.seed(components); old = self.remove(components)
        self.client.replies = [Reply(self.blobs[c]) for c in COMPONENTS if c in components]
        tx = self.session()
        self.assertFalse(self.client.calls); self.assertFalse(tx.transport.sent)
        self.assertTrue(self.prepare(tx, 'install', components))
        self.assertEqual(len(self.client.calls), len(components))
        self.assertFalse(tx.transport.sent)
        self.assertEqual(self.adapter.host.installed, self.unrelated)
        self.assertEqual(set(tx.session.plan.packages), {COMPONENTS[c][0] for c in components})
        self.assertEqual(self.confirm(tx).state, 'verified_success')
        self.assertEqual(self.adapter.host.installed, self.original)
        # Reinstallation retains the existing no-activation policy.
        self.assertFalse(self.adapter.host.native_loaded or self.adapter.host.service_enabled)
        self.assertEqual(len(old.transport.sent), 1); self.assertEqual(len(tx.transport.sent), 1)
        self.assertFalse(tx.request('remove'))

    def test_core_bridge_shape_remove_then_selected_release_reinstall(self):
        self.roundtrip(('core', 'bridge'))
        self.assertNotIn('steam', {a.component for a in self.assets
                                  if any(a.url == u for u, timeout in self.client.calls)})

    def test_all_four_components_remove_then_release_reinstall(self):
        self.roundtrip(tuple(COMPONENTS))

    def test_omitted_dependent_prevents_partial_core_removal(self):
        self.seed(('core', 'bridge')); tx = self.session()
        self.assertFalse(self.prepare(tx, 'remove', ('core',)))
        self.assertEqual(tx.error, 'dependent_component_requires_explicit_selection')
        self.assertIsNone(tx.begin()); self.assertFalse(tx.transport.sent)
        self.assertFalse(self.client.calls); self.assertEqual(self.adapter.host.installed, self.original)

    def test_failed_removal_does_not_start_download_retry_or_reinstall(self):
        self.seed(('core', 'bridge')); tx = self.session()
        self.assertTrue(self.prepare(tx, 'remove', ('core', 'bridge')))
        def fail(): raise BackendError('synthetic_remove_failure')
        self.adapter.commit = fail
        result = self.confirm(tx)
        self.assertEqual(result.error, 'synthetic_remove_failure')
        self.assertTrue(result.changes_possible)
        self.assertFalse(tx.request('install')); self.assertIsNone(tx.begin())
        self.assertFalse(self.client.calls); self.assertEqual(len(tx.transport.sent), 1)

    def test_download_failure_after_removal_leaves_no_partial_reinstall(self):
        self.seed(('core', 'bridge')); self.remove(('core', 'bridge'))
        self.adapter.calls.clear()
        self.client.replies = [Reply(self.blobs['core']), OSError('offline fixture')]
        tx = self.session()
        self.assertFalse(self.prepare(tx, 'install', ('core', 'bridge')))
        self.assertEqual(tx.error, 'release_download_unavailable')
        self.assertIsNone(tx.session); self.assertIsNone(tx.begin()); self.assertFalse(tx.transport.sent)
        self.assertNotIn('commit', self.adapter.calls)
        self.assertEqual(self.adapter.host.installed, self.unrelated)

    def test_unexpected_loaded_module_after_removal_blocks_new_install(self):
        self.seed(('core', 'bridge')); self.remove(('core', 'bridge'))
        self.adapter.host = replace(self.adapter.host, native_loaded=True)
        self.client.replies = [Reply(self.blobs['core']), Reply(self.blobs['bridge'])]
        tx = self.session()
        self.assertFalse(self.prepare(tx, 'install', ('core', 'bridge')))
        self.assertEqual(tx.error, 'unowned_loaded_module')
        self.assertIsNone(tx.begin()); self.assertFalse(tx.transport.sent)
        self.assertTrue(self.adapter.host.native_loaded)  # Never force-unload.


if __name__ == '__main__':
    unittest.main()
