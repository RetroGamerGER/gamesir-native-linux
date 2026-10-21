#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline fake HTTPS and existing synthetic package/host/transport only."""
from dataclasses import replace
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
sys.path.insert(0, str(ROOT / 'scripts'))
from artifacts import BackendError, PUBLIC_BINARIES
from app_packages import AppImageTransactions, load_bundle
from backend import Request
from first_run import FirstRunTransactions
from helper_setup import SetupInspector
from release_download import (ReleaseAsset, ReleaseDownloader, HTTPSClient, HTTPSReply,
                              REPOSITORY, parse_assets, serialize_assets)
from test_control_center_app_packages import fixture, FakeTransport, Adapter
from test_control_center_first_run import FakeTarget, setup_fixture
import package_control_center as packaging


class Reply:
    def __init__(self, data=b'', status=200, headers=None, on_read=None):
        self.data = io.BytesIO(data)
        self.status = status
        self.headers = [('Content-Length', str(len(data)))] if headers is None else headers
        self.closed = False
        self.on_read = on_read

    def read(self, size, timeout):
        if self.on_read: self.on_read()
        return self.data.read(size)

    def close(self): self.closed = True


class Client:
    def __init__(self, replies):
        self.replies = list(replies); self.calls = []

    def open(self, url, timeout):
        self.calls.append((url, timeout))
        if not self.replies: raise AssertionError('Unexpected network attempt')
        r = self.replies.pop(0)
        if isinstance(r, Exception): raise r
        return r


class Downloads(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        self.profile, self.trust = fixture(self.root)
        self.blobs = {r.component: (self.root / (r.component + '.pkg.tar.zst')).read_bytes()
                      for r in self.trust.catalog.records}
        # Synthetic, nonexistent release asset names. No public record enabled.
        self.assets = tuple(ReleaseAsset(r.component, 'offline-test-' + r.component + '.pkg.tar.zst', r)
                            for r in self.trust.catalog.records)
        self.asset = self.assets[0]; self.data = self.blobs[self.asset.component]

    def fetch(self, replies, asset=None, **kwargs):
        client = Client(replies); downloader = ReleaseDownloader(client, clock=lambda: 100)
        return downloader.fetch(asset or self.asset, **kwargs), client

    def error(self, replies, expected, **kwargs):
        client = Client(replies)
        with self.assertRaises(BackendError) as e:
            ReleaseDownloader(client, clock=lambda: 100).fetch(self.asset, **kwargs)
        self.assertEqual(e.exception.code, expected)
        return client

    def remote(self):
        for p in self.root.glob('*.pkg.tar.zst'): p.unlink()
        (self.root / 'release-assets.json').write_bytes(serialize_assets(self.assets))

    def tx(self, client=None, reader=None):
        self.remote(); self.adapter = Adapter()
        self.client = Client([]) if client is None else client
        self.execution = AppImageTransactions(self.root, clock=lambda: 100,
            downloader=ReleaseDownloader(self.client, clock=lambda: 100),
            reader=reader or (lambda request: Mock(collect=self.adapter.observe)),
            transport_factory=lambda pins: FakeTransport(pins, self.adapter, self.trust))
        t = self.execution.initial_inspection()
        self.assertTrue(self.execution.receive_inspection(t, t.run()))
        return self.execution

    def prepare(self, tx, components=('core',), operation='install'):
        self.assertTrue(tx.request(operation))
        for c in ('core', 'steam', 'gamescope', 'bridge'): tx.select(c, c in components)
        return tx.begin_preparation()

    def test_import_construction_and_empty_public_catalog_never_connect(self):
        with patch('socket.create_connection', side_effect=AssertionError('Offline only')):
            ReleaseDownloader(); self.remote(); load_bundle(self.root)
            self.assertEqual(PUBLIC_BINARIES.records, ())

    def test_release_index_roundtrip_and_url_from_reviewed_tag(self):
        found = parse_assets(serialize_assets(self.assets), self.trust.catalog)
        self.assertEqual(found, self.assets)
        self.assertEqual(self.asset.url, 'https://github.com/' + REPOSITORY +
                         '/releases/download/' + self.asset.review.tag + '/' + self.asset.filename)

    def test_index_rejects_foreign_repo_extra_keys_missing_duplicates_or_unknown(self):
        base = json.loads(serialize_assets(self.assets))
        variants = [dict(base, repository='other/repo'), dict(base, url='https://evil.invalid'),
                    dict(base, assets=base['assets'][:-1]), dict(base, assets=[base['assets'][0]] * 2),
                    dict(base, assets=[{'component': 'other', 'filename': 'x.pkg.tar.zst'}])]
        for v in variants:
            with self.subTest(value=v), self.assertRaises(BackendError):
                parse_assets(json.dumps(v).encode(), self.trust.catalog)

    def test_asset_filenames_reject_paths_query_encoding_and_controls(self):
        for name in ('../x.pkg.tar.zst', '/x.pkg.tar.zst', 'x?y.pkg.tar.zst',
                     'x%2fy.pkg.tar.zst', 'x\\y.pkg.tar.zst', 'x\ny.pkg.tar.zst', 'x.exe'):
            with self.subTest(name=name), self.assertRaises(BackendError):
                replace(self.asset, filename=name).validate()

    def test_success_verifies_exact_immutable_package_and_closes_reply(self):
        r = Reply(self.data); data, c = self.fetch([r])
        self.assertEqual(data, self.data); self.assertIs(type(data), bytes)
        self.assertTrue(r.closed); self.assertEqual(c.calls, [(self.asset.url, 10)])

    def test_only_explicit_github_cdn_redirect_is_followed(self):
        url = 'https://release-assets.githubusercontent.com/github-production-release-asset/1/2?sig=offline'
        first, second = Reply(status=302, headers=[('Location', url)]), Reply(self.data)
        data, c = self.fetch([first, second])
        self.assertEqual(data, self.data); self.assertEqual(c.calls[1][0], url)
        self.assertTrue(first.closed and second.closed)

    def test_redirect_refuses_http_foreign_local_userinfo_port_fragment_and_other_repo(self):
        for url in ('http://github.com/x', 'https://evil.invalid/x', 'https://127.0.0.1/x',
                    'https://user:pass@release-assets.githubusercontent.com/github-production-release-asset/x',
                    'https://release-assets.githubusercontent.com:443/github-production-release-asset/x',
                    'https://release-assets.githubusercontent.com/github-production-release-asset/x#fragment',
                    'https://github.com/other/repo/releases/download/v1/x.pkg.tar.zst',
                    '//github.com/x', 'file:///tmp/x', 'https://github.com/x\r\nHeader: x'):
            with self.subTest(url=url):
                r = Reply(status=302, headers=[('Location', url)])
                c = self.error([r], 'release_redirect_refused')
                self.assertEqual(len(c.calls), 1); self.assertTrue(r.closed)

    def test_redirect_loop_and_budget_close_without_retry(self):
        self.error([Reply(status=302, headers=[('Location', self.asset.url)])], 'release_redirect_refused')
        replies = [Reply(status=302, headers=[('Location',
            'https://objects.githubusercontent.com/github-production-release-asset/x/' + str(i))]) for i in range(4)]
        c = self.error(replies, 'release_redirect_limit')
        self.assertEqual(len(c.calls), 4); self.assertTrue(all(r.closed for r in replies))

    def test_wrong_size_missing_duplicate_length_encoding_or_chunked_refused(self):
        n = str(len(self.data))
        for h in ([], [('Content-Length', '1')], [('Content-Length', n)] * 2,
                  [('Content-Length', n), ('Content-Encoding', 'gzip')],
                  [('Content-Length', n), ('Transfer-Encoding', 'chunked')]):
            with self.subTest(headers=h):
                self.error([Reply(self.data, headers=h)],
                           'invalid_release_response' if len(h) == 2 and h[0] == h[1]
                           else 'release_download_size_mismatch')

    def test_truncation_extra_bytes_and_same_size_corruption_never_pass(self):
        h = [('Content-Length', str(len(self.data)))]
        self.error([Reply(self.data[:-1], headers=h)], 'release_download_incomplete')
        self.error([Reply(self.data + b'x', headers=h)], 'release_download_size_mismatch')
        self.error([Reply(b'x' * len(self.data), headers=h)], 'no_reviewed_binary')

    def test_matching_hash_does_not_skip_archive_identity_checks(self):
        review = replace(self.asset.review, version='9.9-1')
        with self.assertRaises(BackendError) as e:
            self.fetch([Reply(self.data)], replace(self.asset, review=review))
        self.assertEqual(e.exception.code, 'package_identity_mismatch')

    def test_network_errors_are_sanitized_and_never_retried(self):
        for error in (OSError('private/signed?secret=do-not-show'), ssl.SSLError('private cert path')):
            c = self.error([error], 'release_download_unavailable')
            self.assertEqual(len(c.calls), 1)

    def test_cancel_before_open_and_during_read_discards_partial_bytes(self):
        c = self.error([], 'release_download_cancelled', cancelled=lambda: True)
        self.assertFalse(c.calls)
        flag = [False]
        r = Reply(self.data, on_read=lambda: flag.__setitem__(0, True))
        self.error([r], 'release_download_cancelled', cancelled=lambda: flag[0]); self.assertTrue(r.closed)

    def test_total_deadline_closes_reply_and_discards_bytes(self):
        now = [0]; r = Reply(self.data, on_read=lambda: now.__setitem__(0, 100))
        with self.assertRaises(BackendError) as e:
            ReleaseDownloader(Client([r]), clock=lambda: now[0]).fetch(self.asset)
        self.assertEqual(e.exception.code, 'release_download_timeout'); self.assertTrue(r.closed)

    def test_https_client_certificate_checks_no_auth_and_closed_body_eof(self):
        connection = Mock(); connection.getresponse.return_value = Mock(status=200, getheaders=lambda: [])
        with patch('release_download.http.client.HTTPSConnection', return_value=connection) as factory:
            reply = HTTPSClient().open(self.asset.url, 3)
        context = factory.call_args.kwargs['context']
        self.assertTrue(context.check_hostname); self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        sent = connection.request.call_args.kwargs['headers']
        self.assertNotIn('Authorization', sent); self.assertNotIn('Cookie', sent)
        self.assertEqual(sent['Accept-Encoding'], 'identity')
        reply.response.isclosed.return_value = True
        self.assertEqual(reply.read(1, 3), b''); reply.sock.settimeout.assert_not_called(); reply.close()

    def test_initial_reuse_properties_and_removal_never_download(self):
        tx = self.tx(); self.assertEqual(tx.state, 'idle'); self.assertFalse(self.client.calls)
        for _ in range(10): tx.available('install'); tx.available('remove')
        self.adapter.host = replace(self.adapter.host, installed=(('gamesir-native-dkms', self.asset.review.version),))
        tx = AppImageTransactions(self.root, clock=lambda: 100,
            downloader=ReleaseDownloader(self.client),
            reader=lambda r: Mock(collect=self.adapter.observe),
            transport_factory=lambda pins: FakeTransport(pins, self.adapter, self.trust))
        initial = tx.initial_inspection()
        self.assertTrue(tx.receive_inspection(initial, initial.run()))
        t = self.prepare(tx, operation='remove')
        self.assertTrue(tx.receive_inspection(t, t.run())); self.assertFalse(self.client.calls)
        self.assertFalse(tx.transport.sent)

    def test_selected_verified_download_then_fresh_review_without_auth(self):
        tx = self.tx(Client([Reply(self.blobs['steam'])])); t = self.prepare(tx, ('steam',))
        self.assertFalse(self.client.calls); self.assertIsNone(tx.begin())
        self.assertTrue(tx.receive_inspection(t, t.run()))
        self.assertEqual(tx.state, 'review'); self.assertEqual(len(self.client.calls), 1)
        self.assertIn('offline-test-steam.pkg.tar.zst', self.client.calls[0][0])
        self.assertEqual([a.review.component for a in tx.session.plan.artifacts], ['steam'])
        self.assertFalse(tx.transport.sent); self.assertNotIn('lock', self.adapter.calls)

    def test_failure_of_second_selected_package_publishes_no_partial_plan(self):
        tx = self.tx(Client([Reply(self.data), OSError('offline')]))
        t = self.prepare(tx, ('core', 'bridge'))
        self.assertFalse(tx.receive_inspection(t, t.run())); self.assertEqual(tx.state, 'editing')
        self.assertIsNone(tx.session); self.assertFalse(tx.blobs); self.assertFalse(tx.transport.sent)

    def test_cancellation_before_and_during_worker_cannot_resurrect_review(self):
        tx = self.tx(); t = self.prepare(tx); self.assertTrue(tx.cancel())
        self.assertFalse(tx.receive_inspection(t, t.run())); self.assertFalse(self.client.calls)
        self.assertIsNone(tx.session)
        # A user cancellation during a bounded read is also propagated.
        tx = self.execution; self.assertTrue(tx.request('install'))
        t = tx.begin_preparation()
        self.client.replies = [Reply(self.data, on_read=tx.cancel)]
        self.assertFalse(tx.receive_inspection(t, t.run())); self.assertIsNone(tx.session)
        self.assertFalse(tx.transport.sent)

    def test_host_change_during_transfer_blocks_confirmation(self):
        tx = self.tx()
        def changed(): self.adapter.host = replace(self.adapter.host, service_enabled=True)
        self.client.replies = [Reply(self.data, on_read=changed)]
        t = self.prepare(tx)
        self.assertFalse(tx.receive_inspection(t, t.run())); self.assertEqual(tx.error, 'host_changed')
        self.assertIsNone(tx.begin()); self.assertFalse(tx.transport.sent)

    def test_changed_install_eligibility_or_missing_requirements_block_before_download(self):
        for changes, code in (({'headers_release': 'other-kernel'}, 'matching_headers_required'),
                              ({'missing_dependencies': ('dkms',)}, 'resolve_dependencies_separately'),
                              ({'installed': (('gamesir-native-dkms', self.asset.review.version),)}, 'host_changed')):
            with self.subTest(changes=changes):
                # A new metadata-only session; no simulated response is allowed.
                tx = self.tx()
                self.adapter.host = replace(self.adapter.host, **changes)
                task = self.prepare(tx)
                self.assertFalse(tx.receive_inspection(task, task.run()))
                self.assertEqual(tx.error, code); self.assertFalse(self.client.calls)
                self.assertIsNone(tx.begin()); self.assertFalse(tx.transport.sent)

    def test_metadata_only_staging_is_offline_and_mixed_inputs_block(self):
        self.remote()
        with patch('socket.create_connection', side_effect=AssertionError('Offline staging')):
            result = packaging.stage_reviewed_packages(self.root, self.root / 'staged')
        self.assertEqual(result['source_mode'], 'github_release')
        self.assertFalse(list((self.root / 'staged').glob('*.pkg.tar.zst')))
        self.assertEqual(load_bundle(self.root / 'staged').release_assets, self.assets)
        (self.root / 'core.pkg.tar.zst').write_bytes(self.data)
        with self.assertRaises(BackendError) as e: load_bundle(self.root)
        self.assertEqual(e.exception.code, 'mixed_package_sources')

    def test_missing_or_existing_helper_first_run_never_downloads(self):
        root = self.root / 'first-run'; root.mkdir()
        packages, payload_dir, bundle, payload, trust = setup_fixture(root)
        assets = tuple(ReleaseAsset(r.component, 'offline-' + r.component + '.pkg.tar.zst', r)
                       for r in trust.catalog.records)
        for p in packages.glob('*.pkg.tar.zst'): p.unlink()
        (packages / 'release-assets.json').write_bytes(serialize_assets(assets))
        target, adapter, client = FakeTarget(), Adapter(), Client([])
        for expected in ('setup_required', 'idle'):
            tx = FirstRunTransactions(packages, clock=lambda: 100,
                inspector=SetupInspector(target), downloader=ReleaseDownloader(client),
                reader=lambda r: Mock(collect=adapter.observe),
                transport_factory=lambda pins: FakeTransport(pins, adapter, trust))
            task = tx.initial_inspection(); self.assertTrue(tx.receive_inspection(task, task.run()))
            self.assertEqual(tx.state, expected); self.assertFalse(client.calls)
            self.assertFalse(target.calls)
            target.seed(payload)


if __name__ == '__main__':
    unittest.main()
