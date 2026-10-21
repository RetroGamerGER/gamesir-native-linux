#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bundle -> passive worker -> exact plan -> protocol, with all host edges fake."""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
sys.path.insert(0, str(ROOT / 'scripts'))
from artifacts import BackendError, COMPONENTS
from app_packages import AppImageTransactions, load_bundle
from backend import Request
from package_catalog import CATALOG, serialize_catalog
from package_client import FILES
from package_execution import ExecutionTrust, PackageExecutor
from package_wire import parse_message, receipt
from rehearsal import fixture_catalog, KERNEL
from test_control_center_execution import Adapter, trust_records


def fixture(root):
    catalog, blobs = fixture_catalog()
    trust = ExecutionTrust(catalog, trust_records(catalog))
    data = serialize_catalog(trust)
    pins = [[p, hashlib.sha256(data).hexdigest() if p == CATALOG else 'a'*64] for p in FILES]
    profile = {'schema': 1, 'scope': 'local_review', 'pins': pins,
               'distribution': 'cachyos', 'kernel': KERNEL}
    (root/'profile.json').write_text(json.dumps(profile))
    (root/'REVIEWED_PACKAGES.json').write_bytes(data)
    for c,b in blobs.items(): (root/(c+'.pkg.tar.zst')).write_bytes(b)
    return profile, trust


class FakeTransport:
    def __init__(self, pins, adapter, trust, code=0):
        self.auditor, self.sent = Mock(), []
        self.adapter, self.trust, self.code = adapter, trust, code

    def invoke(self, message):
        self.sent.append(message)
        if self.code: return self.code, b''
        source = io.BytesIO(b''.join(message.chunks()))
        parsed = parse_message(source.read, self.trust)
        self.adapter.plan = parsed.plan
        outcome = PackageExecutor(self.trust, self.adapter, clock=lambda:100).run(parsed.plan)
        return 0, receipt(parsed, outcome)


class AppPackages(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'build');self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile, self.trust = fixture(self.root)
        self.adapter, self.reads = Adapter(), []
        def reader(request):
            self.reads.append(request)
            return Mock(collect=lambda:self.adapter.observe())
        self.tx = AppImageTransactions(self.root, reader=reader, clock=lambda:100,
            transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.trust))

    def initial(self):
        task = self.tx.initial_inspection()
        self.assertTrue(self.tx.receive_inspection(task,task.run()))

    def plan(self, operation='install', components=('core',)):
        self.initial();self.assertTrue(self.tx.request(operation))
        for c in COMPONENTS:self.tx.select(c,c in components)
        task = self.tx.begin_preparation();self.assertIsNotNone(task)
        self.assertTrue(self.tx.receive_inspection(task,task.run()))

    def test_construct_properties_and_parse_have_no_host_process_or_auth_access(self):
        with patch('subprocess.Popen',side_effect=AssertionError('No process')), \
             patch('package_preflight.PlanningEvidence',side_effect=AssertionError('No host')):
            bundle=load_bundle(self.root)
            self.assertEqual(len(bundle.blobs),4)
            self.assertEqual(self.tx.available('install'),())
            self.assertFalse(self.tx.prepare())
            self.assertIsNone(self.tx.begin())
        self.assertFalse(self.reads)

    def test_initial_and_selected_preflight_are_fresh_and_do_not_submit(self):
        self.plan(components=('core','bridge'))
        self.assertEqual(self.reads,[Request('install',('core',)),Request('install',('core','bridge'))])
        self.assertEqual(self.tx.state,'review')
        self.assertEqual(len(self.tx.transport.auditor.inspect.call_args_list),2*(len(FILES)+1))
        self.assertFalse(self.tx.transport.sent)
        self.assertEqual(self.tx.session.plan.purpose,'packages')
        self.assertNotIn('lock', self.adapter.calls)

    def test_exact_install_and_remove_protocol_through_synthetic_executor(self):
        self.plan(components=('core','bridge'))
        submission=self.tx.begin();outcome=submission.run()
        self.assertTrue(self.tx.finish(submission,outcome))
        self.assertEqual(outcome.state,'verified_success')
        self.assertEqual(len(self.tx.transport.sent),1)
        self.assertTrue(self.tx.uncertain)
        self.assertEqual(self.tx.available('remove'),())
        self.assertIsNone(self.tx.begin())
        # Separate new inspected session, then exact reviewed removal.
        self.tx=AppImageTransactions(self.root,reader=lambda r:Mock(collect=self.adapter.observe),clock=lambda:100,
            transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.trust))
        self.plan('remove',('core','bridge'))
        submission=self.tx.begin();outcome=submission.run();self.tx.finish(submission,outcome)
        self.assertEqual(outcome.state,'verified_success')
        self.assertEqual(self.adapter.host.installed,(('unrelated-controller','1.0-1'),))
        self.assertIn('guard',self.adapter.calls)

    def test_cancellation_while_preparing_discards_late_result(self):
        self.initial();self.tx.request('install')
        task=self.tx.begin_preparation()
        self.assertFalse(self.tx.select('bridge',True))
        self.assertTrue(self.tx.cancel())
        self.assertFalse(self.tx.receive_inspection(task,task.run()))
        self.assertIsNone(self.tx.session)
        self.assertFalse(self.tx.transport.sent)

    def test_missing_helper_fails_before_any_host_or_auth_access(self):
        factory=self.tx.transport_factory
        def bad(pins):
            t=factory(pins);t.auditor.inspect.side_effect=BackendError('helper_missing');return t
        self.tx.transport_factory=bad
        task=self.tx.initial_inspection();self.assertFalse(self.tx.receive_inspection(task,task.run()))
        self.assertEqual(self.tx.state,'blocked');self.assertEqual(self.tx.error,'helper_missing')
        self.assertFalse(self.reads)
        self.assertFalse(self.tx.request('install'))

    def test_changed_host_platform_and_locked_database_block_preparation(self):
        for changes in ({'kernel':'other-kernel'}, {'distribution':'garuda'}, {'database_locked':True}):
            with self.subTest(changes=changes):
                self.setUp();self.initial();self.tx.request('install')
                self.adapter.host=replace(self.adapter.host,**changes)
                task=self.tx.begin_preparation()
                self.assertFalse(self.tx.receive_inspection(task,task.run()))
                self.assertIsNone(self.tx.session)
                self.assertFalse(self.tx.transport.sent)

    def test_unknown_removal_same_version_and_unreviewed_updates_not_offered(self):
        self.adapter.host=replace(self.adapter.host,installed=((COMPONENTS['core'][0],'9.0-1'),
            (COMPONENTS['steam'][0],self.trust.catalog.records[1].version)))
        self.initial()
        self.assertNotIn('core',self.tx.available('remove'))
        self.assertNotIn('core',self.tx.available('install'))
        self.assertNotIn('steam',self.tx.available('install'))
        self.assertIn('steam',self.tx.available('remove'))

    def test_selected_package_appearing_before_confirmation_blocks(self):
        self.initial();self.tx.request('install')
        self.adapter.host=replace(self.adapter.host,installed=((COMPONENTS['core'][0],self.trust.catalog.records[0].version),))
        task=self.tx.begin_preparation()
        self.assertFalse(self.tx.receive_inspection(task,task.run()))
        self.assertEqual(self.tx.error,'host_changed')
        self.assertIsNone(self.tx.session)

    def test_confirmation_expiry_cannot_spawn_and_agent_cancel_has_no_commit(self):
        self.plan();self.tx.session.clock=lambda:221
        outcome=self.tx.begin().run()
        self.assertEqual(outcome.error,'plan_expired');self.assertFalse(self.tx.transport.sent)
        self.setUp();self.plan();self.tx.transport.code=126
        outcome=self.tx.begin().run()
        self.assertEqual(outcome.state,'cancelled');self.assertNotIn('commit',self.adapter.calls)

    def test_unknown_receipt_locks_new_actions(self):
        self.plan();self.tx.transport.code=2
        submission=self.tx.begin();outcome=submission.run();self.tx.finish(submission,outcome)
        self.assertTrue(self.tx.uncertain);self.assertFalse(self.tx.request('remove'))

    def test_reviewed_upgrade_available_only_with_independent_installed_record(self):
        from artifacts import Catalog
        from package_execution import InstalledReview
        bundle=load_bundle(self.root)
        records=tuple(replace(r,upgrade_from=('0.0.1-1',)) if r.component=='steam' else r
                      for r in bundle.trust.catalog.records)
        self.adapter.host=replace(self.adapter.host,installed=((COMPONENTS['steam'][0],'0.0.1-1'),))
        reviewed=ExecutionTrust(Catalog(records),(*bundle.trust.installed,InstalledReview('steam','0.0.1-1')))
        self.tx.loader=lambda root:replace(bundle,trust=reviewed)
        self.initial();self.assertIn('steam',self.tx.available('install'))
        self.tx.bundle=replace(bundle,trust=ExecutionTrust(Catalog(records),bundle.trust.installed))
        self.assertNotIn('steam',self.tx.available('install'))

    def test_helper_changed_after_initial_read_blocks_review_without_prompt(self):
        from privilege.protocol import AuthorizationError
        self.initial();self.tx.request('install')
        self.tx.transport.auditor.inspect.side_effect=AuthorizationError('authorization_helper_changed')
        task=self.tx.begin_preparation()
        self.assertFalse(self.tx.receive_inspection(task,task.run()))
        self.assertEqual(self.tx.error,'authorization_helper_changed')
        self.assertFalse(self.tx.transport.sent);self.assertIsNone(self.tx.session)

    def test_entry_routes_only_build_directory_and_never_launches_on_import(self):
        import runpy
        from types import SimpleNamespace
        entry=self.root/'entry.py'
        entry.write_bytes((ROOT/'packaging/control-center/entry.py').read_bytes())
        main=Mock(return_value=0)
        for present in (False,True):
            if present:(self.root/'reviewed-packages').mkdir()
            with patch.dict(sys.modules,{'main':SimpleNamespace(main=main)}), \
                 patch.object(sys,'argv',['image']), self.assertRaises(SystemExit) as result:
                runpy.run_path(str(entry),run_name='__main__')
            self.assertEqual(result.exception.code,0)
            self.assertEqual(main.call_args.kwargs['packages_directory'],
                             self.root/'reviewed-packages' if present else None)
        self.assertFalse(self.reads)

    def test_closed_profile_catalog_pins_and_duplicate_json_fail(self):
        for extra in ({'command':'sudo'}, {'schema':True}, {'distribution':'bazzite'}, {'kernel':'a\ncommand'},
                      {'pins':self.profile['pins'][:-1]}):
            with self.subTest(extra=extra):
                (self.root/'profile.json').write_text(json.dumps({**self.profile,**extra}))
                with self.assertRaises(BackendError):load_bundle(self.root)
        (self.root/'profile.json').write_text('{"schema":1,"schema":1}')
        with self.assertRaises(BackendError):load_bundle(self.root)
        fixture(self.root)
        (self.root/'REVIEWED_PACKAGES.json').write_bytes(b'{}')
        with self.assertRaisesRegex(BackendError,'bundle_catalog_mismatch'):load_bundle(self.root)

    def test_changed_symlink_fifo_and_oversized_bundle_inputs_refused(self):
        path=self.root/'core.pkg.tar.zst';path.write_bytes(b'altered')
        with self.assertRaises(BackendError):load_bundle(self.root)
        fixture(self.root);path.unlink();path.symlink_to(self.root/'steam.pkg.tar.zst')
        with self.assertRaises(BackendError):load_bundle(self.root)
        path.unlink()
        import os
        os.mkfifo(path)
        with self.assertRaises(BackendError):load_bundle(self.root)
        path.unlink();fixture(self.root)
        (self.root/'profile.json').write_bytes(b' '*65537)
        with self.assertRaises(BackendError):load_bundle(self.root)

    def test_stage_embeds_only_fixed_data_and_never_deploys_helper(self):
        import package_control_center as package
        target=self.root/'staged'
        result=package.stage_reviewed_packages(self.root,target)
        self.assertFalse(result['helper_setup_included'])
        self.assertEqual({p.name for p in target.iterdir()},
                         {'profile.json','REVIEWED_PACKAGES.json',*(c+'.pkg.tar.zst' for c in COMPONENTS)})
        self.assertEqual(load_bundle(target).blobs,load_bundle(self.root).blobs)
        self.assertNotIn(str(self.root),(target/'profile.json').read_text())


if __name__=='__main__':unittest.main()
