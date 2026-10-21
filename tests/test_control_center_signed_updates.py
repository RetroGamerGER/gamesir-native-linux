#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real OpenSSL fixture signatures, fake HTTPS/host/root and temporary state only.

The RFC 8032 section 7.1 seed below is public TEST DATA, not a project key.
No production key, network, authorization, installed DB or hardware access.
"""
from dataclasses import asdict, replace
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/control_center'))
from artifacts import BackendError, Catalog, COMPONENTS
from app_packages import AppImageTransactions, load_bundle, UserCatalogCache
from backend import Request, build_plan
from package_catalog import (DOMAIN, CATALOG_LIMIT, CatalogState, ReleaseResolver,
    verify_signed_catalog, parse_catalog, serialize_catalog, CATALOG)
from package_execution import ExecutionTrust, InstalledReview, PackageExecutor
from package_wire import encode, decode, PackageMessage, parse_message, receipt
from release_download import ReleaseDownloader, CATALOG_URL
from test_control_center_app_packages import fixture, FakeTransport, Adapter
from test_control_center_release_download import Client, Reply

SEED = bytes.fromhex('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60')
PUBLIC = 'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a'
KEY_ID = hashlib.sha256(bytes.fromhex(PUBLIC)).hexdigest()
POLICY = {'schema': 1, 'minimum_revision': 1, 'keys': [{'id': KEY_ID, 'public_key': PUBLIC}]}
NOW = 1000000


def sign_payload(payload, *, private_seed=SEED):
    fds=[]
    try:
        for data in (bytes.fromhex('302e020100300506032b657004220420')+private_seed, DOMAIN+payload):
            fd=os.memfd_create('public-fixture',os.MFD_CLOEXEC); fds.append(fd)
            os.write(fd,data);os.lseek(fd,0,os.SEEK_SET)
        signed=subprocess.run(['/usr/bin/openssl','pkeyutl','-sign','-keyform','DER',
            '-inkey','/proc/self/fd/'+str(fds[0]),'-rawin','-in','/proc/self/fd/'+str(fds[1])],
            pass_fds=fds,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/bin:/bin','OPENSSL_CONF':'/dev/null'},timeout=5,check=True).stdout
        return encode(dict(schema=1,algorithm='ed25519',key_id=KEY_ID,
            payload=base64.b64encode(payload).decode(),signature=signed.hex()))
    finally:
        for fd in fds: os.close(fd)


def content(trust, *, revision=1, issued=NOW-10, expires=NOW+86400):
    return dict(schema=1,repository='RetroGamerGER/gamesir-native-linux',protocol=3,
        revision=revision,issued_at=issued,expires_at=expires,
        packages=[asdict(r) for r in trust.catalog.records],installed=[asdict(i) for i in trust.installed],
        assets=[dict(component=r.component,filename=f'{COMPONENTS[r.component][0]}-{r.version}-{COMPONENTS[r.component][1]}.pkg.tar.zst') for r in trust.catalog.records])


def signed_fixture(root):
    profile,trust=fixture(root)
    anchor=ExecutionTrust(trust.catalog,trust.installed,decode(encode(POLICY)))
    data=serialize_catalog(anchor)
    (root/'REVIEWED_PACKAGES.json').write_bytes(data)
    for pin in profile['pins']:
        if pin[0]==CATALOG: pin[1]=hashlib.sha256(data).hexdigest()
    (root/'profile.json').write_bytes(encode(profile))
    blobs={r.component:(root/(r.component+'.pkg.tar.zst')).read_bytes() for r in anchor.catalog.records}
    for p in root.glob('*.pkg.tar.zst'):p.unlink()
    (root/'release-assets.json').write_bytes(encode({'schema':1,'repository':'RetroGamerGER/gamesir-native-linux','assets':content(anchor)['assets']}))
    return anchor,blobs


class SignedUpdates(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.bundle_dir=self.root/'bundle';self.bundle_dir.mkdir()
        self.anchor,self.blobs=signed_fixture(self.bundle_dir)
        self.value=content(self.anchor);self.envelope=sign_payload(encode(self.value))
        self.state_dir=self.root/'root-state';self.state_dir.mkdir(mode=0o700)
        self.state=CatalogState(self.state_dir/'catalog.json',owner=os.getuid(),parent_guard=lambda p:None)

    def verify(self, value=None, **kwargs):
        return verify_signed_catalog(self.envelope if value is None else sign_payload(encode(value)),
                                     self.anchor,now=NOW,**kwargs)

    def test_real_ed25519_and_closed_policy_round_trip(self):
        release=self.verify(); self.assertEqual(release.revision,1)
        self.assertEqual(parse_catalog(serialize_catalog(self.anchor)).release_policy,POLICY)
        self.assertEqual({r.component for r in release.trust.catalog.records},set(COMPONENTS))
        self.assertIsNone(self.state.read())

    def test_tampered_signature_payload_key_and_unsigned_envelope_are_rejected(self):
        original=decode(self.envelope)
        for change in ({'signature':'0'*128},{'payload':base64.b64encode(b'{}').decode()},
                       {'key_id':'0'*64},{'algorithm':'none'},{'schema':True},{'command':'evil'}):
            with self.subTest(change=tuple(change)):
                with self.assertRaises(BackendError):verify_signed_catalog(encode({**original,**change}),self.anchor,now=NOW)
        with self.assertRaisesRegex(BackendError,'release_signature_invalid'):
            verify_signed_catalog(sign_payload(encode(self.value),private_seed=b'\x01'*32),self.anchor,now=NOW)

    def test_no_shell_configuration_private_key_or_disk_input_in_verifier(self):
        real=subprocess.run
        with patch('package_catalog.subprocess.run',wraps=real) as run:
            self.verify()
        call=run.call_args
        self.assertEqual(call.args[0][0:3],('/usr/bin/openssl','pkeyutl','-verify'))
        self.assertNotIn('shell',call.kwargs);self.assertEqual(len(call.kwargs['pass_fds']),3)
        self.assertEqual(call.kwargs['env']['OPENSSL_CONF'],'/dev/null')
        self.assertEqual(call.kwargs['stderr'],subprocess.DEVNULL)

    def test_wrong_repository_protocol_schema_fields_and_duplicate_fields_fail(self):
        for fields in ({'repository':'foreign/repo'},{'protocol':2},{'protocol':True},
                       {'schema':2},{'unexpected':0},{'revision':True},{'revision':0}):
            with self.subTest(fields=fields):
                with self.assertRaises(BackendError):self.verify({**self.value,**fields})
        with self.assertRaises(BackendError):
            verify_signed_catalog(sign_payload(b'{"schema":1,"schema":1}'),self.anchor,now=NOW)

    def test_expiry_future_clock_and_excessive_validity_fail_for_install(self):
        for fields in ({'expires_at':NOW},{'issued_at':NOW+301},
                       {'expires_at':NOW+91*86400},{'expires_at':NOW-20}):
            with self.subTest(fields=fields):
                with self.assertRaises(BackendError):self.verify({**self.value,**fields})
        expired=self.verify({**self.value,'expires_at':NOW},allow_expired=True)
        self.assertTrue(expired.expired)
        with self.assertRaises(BackendError):verify_signed_catalog(self.envelope,self.anchor,now=float('nan'))

    def test_limits_base64_and_signature_length_fail(self):
        with self.assertRaisesRegex(BackendError,'release_catalog_limit'):
            verify_signed_catalog(b'x'*(CATALOG_LIMIT+1),self.anchor,now=NOW)
        for change in ({'payload':'!!'},{'signature':'f'*126},{'signature':'F'*128}):
            with self.assertRaises(BackendError):verify_signed_catalog(encode({**decode(self.envelope),**change}),self.anchor,now=NOW)

    def test_revision_rollback_equivocation_and_backdated_catalog_fail(self):
        current=self.verify({**self.value,'revision':2})
        for fields in ({'revision':1},{'revision':2,'expires_at':NOW+100},
                       {'revision':3,'issued_at':NOW-20}):
            with self.assertRaisesRegex(BackendError,'release_catalog_rollback'):
                self.verify({**self.value,**fields},previous=current)
        self.verify({**self.value,'revision':2},previous=current) # exact same catalog is reusable.

    def test_signed_downgrade_same_version_rebuild_and_invalid_upgrade_origins_fail(self):
        for mutate in ('downgrade','rebuild','upgrade_origin'):
            value=decode(encode(self.value));row=value['packages'][0]
            if mutate=='downgrade':row['version']='0.0.1-1'
            elif mutate=='rebuild':row['digest']='f'*64
            else:row['upgrade_from']=['99.0-1']
            with self.subTest(mutate=mutate):
                with self.assertRaisesRegex(BackendError,'release_package_rollback'):self.verify(value)

    def test_all_components_assets_and_cleanup_history_are_required(self):
        for mutate in ('missing_component','asset','history','guard'):
            value=decode(encode(self.value))
            if mutate=='missing_component':value['packages'].pop()
            elif mutate=='asset':value['assets'][0]['filename']='../evil.pkg.tar.zst'
            elif mutate=='history':value['installed'].pop(0)
            else:value['installed'][0]['guards'][0][1]='0'*64
            with self.subTest(mutate=mutate):
                with self.assertRaises(BackendError):self.verify(value)

    def test_state_roundtrip_atomic_replace_and_no_temp_files(self):
        self.state.write(self.envelope);self.assertEqual(self.state.read(),self.envelope)
        newer=sign_payload(encode({**self.value,'revision':2}))
        with patch('package_catalog.os.replace',side_effect=OSError('fixture')):
            with self.assertRaisesRegex(BackendError,'release_state_persistence_failed'):self.state.write(newer)
        self.assertEqual(self.state.read(),self.envelope)
        self.assertEqual([p.name for p in self.state_dir.iterdir()],['catalog.json'])
        self.assertEqual(self.state.path.stat().st_mode & 0o777,0o600)

    def test_state_symlink_wrong_mode_hardlink_and_corruption_fail_closed(self):
        self.state.path.symlink_to(self.root/'elsewhere')
        with self.assertRaises(BackendError):self.state.read()
        self.state.path.unlink();self.state.write(self.envelope);self.state.path.chmod(0o644)
        with self.assertRaises(BackendError):self.state.read()
        self.state.path.chmod(0o600);os.link(self.state.path,self.root/'linked')
        with self.assertRaises(BackendError):self.state.read()
        (self.root/'linked').unlink();self.state.path.write_bytes(b'corrupt')
        with self.assertRaises(BackendError):ReleaseResolver(self.anchor,self.state,clock=lambda:NOW).previous()

    def test_helper_independently_rejects_signature_before_any_payload_read(self):
        release=self.verify();adapter=Adapter()
        plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=release.trust.catalog,now=100,purpose='packages')
        bad=encode({**decode(self.envelope),'signature':'0'*128})
        message=PackageMessage.create(plan,bad);stream=io.BytesIO(b''.join(message.chunks()));reads=[]
        def read(size):reads.append(size);return stream.read(size)
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW)
        with self.assertRaisesRegex(BackendError,'release_signature_invalid'):
            parse_message(read,self.anchor,resolver=resolver.resolve)
        self.assertEqual(len(reads),2);self.assertFalse(adapter.calls);self.assertIsNone(self.state.read())

    def test_signed_policy_disallows_legacy_install_but_keeps_legacy_removal(self):
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW)
        with self.assertRaisesRegex(BackendError,'signed_catalog_required'):resolver.resolve(None,'install')
        self.assertEqual(resolver.resolve(None,'remove').installed,self.anchor.installed)
        resolver.checkpoint();self.assertIsNone(self.state.read())

    def test_checkpoint_revalidates_races_expiry_and_persistence_before_commit(self):
        for case in ('newer','expired','write_failed'):
            with self.subTest(case=case):
                if self.state.path.exists():self.state.path.unlink()
                now=[NOW];resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:now[0])
                trust=resolver.resolve(self.envelope,'install');adapter=Adapter()
                plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=trust.catalog,now=100,purpose='packages')
                if case=='newer':self.state.write(sign_payload(encode({**self.value,'revision':2})))
                elif case=='expired':now[0]=self.value['expires_at']
                writer=patch.object(self.state,'write',side_effect=BackendError('release_state_persistence_failed')) if case=='write_failed' else patch('builtins.id',wraps=id)
                with writer:outcome=PackageExecutor(trust,adapter,clock=lambda:100,release_guard=resolver).run(plan)
                self.assertEqual(outcome.state,'blocked');self.assertNotIn('commit',adapter.calls)

    def test_checkpoint_failure_after_rename_does_not_run_package_commit(self):
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW);trust=resolver.resolve(self.envelope,'install')
        adapter=Adapter();plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=trust.catalog,now=100,purpose='packages')
        real_fsync=os.fsync;calls=[]
        def fail_directory(fd):
            calls.append(fd)
            if len(calls)==2:raise OSError('directory sync failure')
            return real_fsync(fd)
        with patch('package_catalog.os.fsync',side_effect=fail_directory):
            outcome=PackageExecutor(trust,adapter,clock=lambda:100,release_guard=resolver).run(plan)
        self.assertEqual(outcome.state,'blocked');self.assertNotIn('commit',adapter.calls)
        self.assertEqual(self.state.read(),self.envelope) # metadata advanced, no installed-state success claimed.

    def test_accepted_catalog_survives_package_failure_and_removal_after_expiry(self):
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW);trust=resolver.resolve(self.envelope,'install')
        adapter=Adapter();adapter.scenario='transaction_failed'
        plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=trust.catalog,now=100,purpose='packages')
        adapter.plan=plan
        result=PackageExecutor(trust,adapter,clock=lambda:100,release_guard=resolver).run(plan)
        self.assertEqual(result.state,'failed');self.assertEqual(self.state.read(),self.envelope)
        offline=ReleaseResolver(self.anchor,self.state,clock=lambda:self.value['expires_at']+10)
        self.assertEqual(offline.resolve(None,'remove').installed,trust.installed)
        offline.checkpoint()
        with self.assertRaisesRegex(BackendError,'release_catalog_expired'):offline.resolve(self.envelope,'install')

    def transaction(self, client=None, cache=None, transport_factory=None):
        adapter=Adapter();client=client or Client([])
        tx=AppImageTransactions(self.bundle_dir,clock=lambda:100,wall_clock=lambda:NOW,update_cache=cache,
            downloader=ReleaseDownloader(client,clock=lambda:100),reader=lambda r:Mock(collect=adapter.observe),
            transport_factory=transport_factory or (lambda pins:FakeTransport(pins,adapter,self.anchor)))
        task=tx.initial_inspection();self.assertTrue(tx.receive_inspection(task,task.run()),tx.error)
        return tx,adapter,client

    def test_explicit_check_only_and_no_authentication_on_check(self):
        tx,adapter,client=self.transaction(Client([Reply(self.envelope)]))
        self.assertFalse(client.calls);self.assertEqual(tx.available('install'),())
        task=tx.begin_update_check();self.assertIsNone(tx.begin_update_check())
        self.assertTrue(tx.receive_inspection(task,task.run()),tx.update_error)
        self.assertEqual(client.calls[0][0],CATALOG_URL);self.assertTrue(tx.available('install'))
        self.assertFalse(tx.transport.sent);self.assertNotIn('lock',adapter.calls)
        self.assertIsNone(self.state.read())

    def test_cancel_and_bad_catalog_cannot_replace_good_catalog_or_open_auth(self):
        client=Client([Reply(self.envelope)]);tx,_,_=self.transaction(client)
        task=tx.begin_update_check();result=task.run();self.assertTrue(tx.cancel())
        self.assertFalse(tx.receive_inspection(task,result));self.assertIsNone(tx.bundle.signed_release)
        client.replies=[Reply(self.envelope)];task=tx.begin_update_check();tx.receive_inspection(task,task.run())
        accepted=tx.bundle
        client.replies=[Reply(encode({**decode(self.envelope),'signature':'0'*128}))]
        task=tx.begin_update_check();self.assertFalse(tx.receive_inspection(task,task.run()))
        self.assertIs(tx.bundle,accepted);self.assertFalse(tx.transport.sent)

    def test_catalog_download_limits_transport_and_failure_preserve_state(self):
        for reply in (Reply(b'x',headers=[('Content-Length',str(CATALOG_LIMIT+1))]),
                      Reply(status=302,headers=[('Location','https://evil.example/catalog')]),OSError('offline')):
            tx,_,_=self.transaction(Client([reply]))
            task=tx.begin_update_check();self.assertFalse(tx.receive_inspection(task,task.run()))
            self.assertIsNone(tx.bundle.signed_release);self.assertFalse(tx.transport.sent)

    def test_verified_user_cache_restores_offline_and_cannot_replace_root_authority(self):
        cache=UserCatalogCache(self.root/'user-cache');tx,_,client=self.transaction(Client([Reply(self.envelope)]),cache)
        self.assertFalse((self.root/'user-cache').exists())
        task=tx.begin_update_check();self.assertTrue(tx.receive_inspection(task,task.run()))
        self.assertEqual(cache.read(),self.envelope)
        restored,_,net=self.transaction(cache=cache);self.assertFalse(net.calls)
        self.assertEqual(restored.bundle.signed_release.revision,1);self.assertIsNone(self.state.read())
        cache.store().path.write_bytes(encode({**decode(self.envelope),'signature':'0'*128}))
        with self.assertRaisesRegex(BackendError,'release_signature_invalid'):
            restored.cached_bundle(load_bundle(self.bundle_dir))

    def test_different_prepared_kernel_does_not_require_appimage_rebuild(self):
        bundle=load_bundle(self.bundle_dir)
        host=replace(Adapter().host,kernel='new-prepared-kernel',headers_release='new-prepared-kernel')
        bundle.check_host(host,100) # planner still enforces matching headers at installation.

    def test_two_driver_versions_with_unchanged_appimage_and_helper_anchor(self):
        import tarfile
        original=(self.bundle_dir/'REVIEWED_PACKAGES.json').read_bytes()
        profile=(self.bundle_dir/'profile.json').read_bytes()
        cache=UserCatalogCache(self.root/'client-cache')
        adapter=Adapter();net=Client([Reply(self.envelope)])
        root_state=self.state;anchor=self.anchor;wall=[NOW]
        class IndependentTransport:
            def __init__(self,pins):self.auditor=Mock();self.sent=[];self.release_catalog=None
            def invoke(self,message):
                self.sent.append(message)
                resolver=ReleaseResolver(anchor,root_state,clock=lambda:wall[0])
                stream=io.BytesIO(b''.join(message.chunks()))
                parsed=parse_message(stream.read,anchor,resolver=resolver.resolve)
                adapter.plan=parsed.plan
                outcome=PackageExecutor(resolver.trust,adapter,clock=lambda:100,release_guard=resolver).run(parsed.plan)
                return 0,receipt(parsed,outcome)
        def session():
            tx=AppImageTransactions(self.bundle_dir,clock=lambda:100,wall_clock=lambda:wall[0],update_cache=cache,
                reader=lambda r:Mock(collect=adapter.observe),transport_factory=IndependentTransport,
                downloader=ReleaseDownloader(net,clock=lambda:100))
            task=tx.initial_inspection();self.assertTrue(tx.receive_inspection(task,task.run()),tx.error)
            return tx
        def check(tx):
            task=tx.begin_update_check();self.assertTrue(tx.receive_inspection(task,task.run()),tx.update_error)
            self.assertFalse(tx.transport.sent)
        def commit(tx,operation,blob=None):
            self.assertTrue(tx.request(operation))
            for c in COMPONENTS:tx.select(c,c=='core')
            if blob is not None:net.replies=[Reply(blob)]
            task=tx.begin_preparation();self.assertTrue(tx.receive_inspection(task,task.run()),tx.error)
            self.assertFalse(tx.transport.sent)
            sub=tx.begin();result=sub.run();self.assertTrue(tx.finish(sub,result));self.assertEqual(result.state,'verified_success',result)
        first=session();check(first);commit(first,'install',self.blobs['core'])
        self.assertEqual(ReleaseResolver(anchor,root_state,clock=lambda:NOW).previous().revision,1)
        records=[];new_blobs={}
        for old in anchor.catalog.records:
            source=io.BytesIO(self.blobs[old.component]);target=io.BytesIO()
            with tarfile.open(fileobj=source) as src,tarfile.open(fileobj=target,mode='w') as dst:
                for m in src:
                    data=src.extractfile(m).read()
                    if m.name=='.PKGINFO':data=data.replace(old.version.encode(),b'0.1.0.offline-2')
                    m.size=len(data);dst.addfile(m,io.BytesIO(data))
            blob=target.getvalue();new_blobs[old.component]=blob
            records.append(replace(old,version='0.1.0.offline-2',digest=hashlib.sha256(blob).hexdigest(),
                size=len(blob),upgrade_from=(old.version,),tag='v0.0.1-offline-fixture'))
        new_trust=ExecutionTrust(Catalog(records),(*anchor.installed,*(InstalledReview(r.component,r.version,r.guards) for r in records)))
        v2=content(new_trust,revision=2);envelope2=sign_payload(encode(v2))
        net.replies=[Reply(envelope2)];second=session();check(second);commit(second,'install',new_blobs['core'])
        self.assertEqual(dict(adapter.host.installed)['gamesir-native-dkms'],'0.1.0.offline-2')
        self.assertEqual(ReleaseResolver(anchor,root_state,clock=lambda:NOW).previous().revision,2)
        self.assertEqual((self.bundle_dir/'REVIEWED_PACKAGES.json').read_bytes(),original)
        self.assertEqual((self.bundle_dir/'profile.json').read_bytes(),profile)
        # Restart and uninstall after expiry, with no network or new GUI build.
        wall[0]=v2['expires_at']+1;before=len(net.calls)
        offline=session();self.assertEqual(offline.available('install'),())
        commit(offline,'remove');self.assertEqual(len(net.calls),before)
        self.assertNotIn('gamesir-native-dkms',dict(adapter.host.installed))

    def test_root_rejects_client_forged_authority_even_if_client_plan_is_valid(self):
        release=self.verify();adapter=Adapter()
        plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=release.trust.catalog,now=100,purpose='packages')
        with self.assertRaisesRegex(BackendError,'release_resolver_required'):
            parse_message(io.BytesIO(b''.join(PackageMessage.create(plan,self.envelope).chunks())).read,self.anchor)
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW)
        with self.assertRaisesRegex(BackendError,'signed_catalog_required'):
            parse_message(io.BytesIO(b''.join(PackageMessage.create(plan).chunks())).read,self.anchor,resolver=resolver.resolve)
        self.assertIsNone(self.state.read())

    def test_offline_publisher_uses_existing_external_key_and_checks_policy(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        import sign_release_catalog as publisher
        with tempfile.TemporaryDirectory() as external:
            key=Path(external)/'public-fixture-only.der'
            key.write_bytes(bytes.fromhex('302e020100300506032b657004220420')+SEED);key.chmod(0o600)
            signed=publisher.sign(encode(self.value),key,serialize_catalog(self.anchor),now=NOW)
            self.assertEqual(self.verify().payload_digest,verify_signed_catalog(signed,self.anchor,now=NOW).payload_digest)
            key.chmod(0o644)
            with self.assertRaisesRegex(BackendError,'release_private_key_permissions'):
                publisher.sign(encode(self.value),key,serialize_catalog(self.anchor),now=NOW)
        with self.assertRaisesRegex(BackendError,'release_private_key_location'):
            publisher.sign(encode(self.value),self.root/'not-a-production-key',serialize_catalog(self.anchor),now=NOW)

    def test_no_resolver_means_no_package_execution_with_signed_trust(self):
        release=self.verify();adapter=Adapter()
        plan=build_plan(Request('install',('core',)),adapter.host,{'core':self.blobs['core']},catalog=release.trust.catalog,now=100,purpose='packages')
        result=PackageExecutor(release.trust,adapter,clock=lambda:100).run(plan)
        self.assertEqual(result.error,'release_resolver_required');self.assertFalse(adapter.calls)

    def test_protected_removal_history_remains_usable_with_an_incorrect_clock(self):
        self.state.write(self.envelope)
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:1)
        self.assertEqual(resolver.resolve(None,'remove').installed,self.anchor.installed)
        resolver.checkpoint()
        with self.assertRaisesRegex(BackendError,'release_clock_invalid'):resolver.resolve(self.envelope,'install')

    def test_fresh_signed_catalog_can_review_manual_install_but_expired_unseen_data_cannot(self):
        newer=decode(encode(self.value));newer['revision']=2
        newer['installed'].append({'component':'steam','version':'9.0-1','guards':[]})
        fresh=sign_payload(encode(newer))
        resolver=ReleaseResolver(self.anchor,self.state,clock=lambda:NOW)
        resolver.resolve(fresh,'remove').installed_record('steam','9.0-1')
        resolver.checkpoint();self.assertEqual(resolver.previous().revision,2)
        with patch.object(self.state,'write',side_effect=AssertionError('same catalog must not rewrite state')):
            resolver.resolve(fresh,'remove');resolver.checkpoint()
        self.state.path.unlink()
        expired=ReleaseResolver(self.anchor,self.state,clock=lambda:newer['expires_at']+1)
        trust=expired.resolve(fresh,'remove')
        with self.assertRaisesRegex(BackendError,'unreviewed_installed_version'):trust.installed_record('steam','9.0-1')
        expired.checkpoint();self.assertIsNone(self.state.read())

    def test_minimum_revision_bad_policy_and_verifier_failure_are_closed(self):
        policy=decode(encode(POLICY));policy['minimum_revision']=2
        anchor=ExecutionTrust(self.anchor.catalog,self.anchor.installed,policy)
        with self.assertRaisesRegex(BackendError,'release_catalog_rollback'):
            verify_signed_catalog(self.envelope,anchor,now=NOW)
        policy['keys'][0]['public_key']='0'*64
        with self.assertRaisesRegex(BackendError,'invalid_release_policy'):
            parse_catalog(encode({**decode(serialize_catalog(self.anchor)),'updates':policy}))
        with patch('package_catalog.subprocess.run',side_effect=subprocess.TimeoutExpired('openssl',5)):
            with self.assertRaisesRegex(BackendError,'release_verifier_unavailable'):self.verify()


if __name__=='__main__':unittest.main()
