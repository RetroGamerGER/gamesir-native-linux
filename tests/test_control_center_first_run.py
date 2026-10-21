#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline first-run flow. All root targets, agents and commands are fakes."""
from dataclasses import replace
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
sys.path.insert(0,str(ROOT/'scripts'))
from artifacts import BackendError
from app_packages import load_bundle
from first_run import FirstRunTransactions
from helper_setup import (BASE,CACHE,COPYING,DIRS,LICENSE,PARENT,POLICY,TARGETS,SUDO,
    SetupPayload,SetupInspector,SetupSession,SetupCommandError,SystemSetupRunner,FixedTarget,load_payload,mode)
from test_control_center_app_packages import fixture,FakeTransport,Adapter
from package_catalog import CATALOG


def setup_fixture(root):
    packages=root/'reviewed-packages';packages.mkdir()
    profile,trust=fixture(packages)
    sources=root/'helper-payload'
    data={p:(b'OFFLINE ONLY: not executable\n'+p.encode()) for p in TARGETS}
    data[COPYING]=(ROOT/'COPYING').read_bytes()
    data[CATALOG]=(packages/'REVIEWED_PACKAGES.json').read_bytes()
    profile['pins']=[[p,hashlib.sha256(data[p]).hexdigest()] for p,h in profile['pins']]
    (packages/'profile.json').write_text(json.dumps(profile))
    for p,b in data.items():
        path=sources/p.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    bundle=load_bundle(packages)
    return packages,sources,bundle,load_payload(sources,bundle),trust


class FakeTarget:
    def __init__(self,parent=True):
        self.dirs={p:0o755 for p in ('/usr/lib','/usr/share/licenses','/usr/share/polkit-1/actions','/var/cache')}
        if parent:self.dirs[PARENT]=0o755
        self.files={};self.calls=[];self.registered=False;self.bad_prerequisite=False

    def exists(self,p):return p in self.dirs or p in self.files
    def directory(self,p,expected=None):
        if p not in self.dirs or expected is not None and self.dirs[p]!=expected:raise BackendError('setup_directory_changed')
    def file(self,p,digest,bits):
        if p not in self.files or self.files[p]!=(digest,bits):raise BackendError('setup_file_changed')
    def policy(self,installed):
        if self.registered!=installed:raise BackendError('setup_policy_unconfirmed')
    def prerequisites(self):
        if self.bad_prerequisite:raise BackendError('setup_agent_unavailable')
    def seed(self,payload):
        self.dirs.update(DIRS)
        self.files={p:(digest,mode(p)) for p,data,digest in payload.rows};self.registered=True
    def runner(self,argv,source=None):
        self.calls.append(tuple(argv))
        assert tuple(argv[:len(SUDO)])==SUDO
        command=argv[len(SUDO):]
        if command[0]=='/usr/bin/mkdir':
            p=command[-1]
            if self.exists(p):raise SetupCommandError('setup_command_failed')
            self.dirs[p]=int(command[2],8)
        elif command[0]=='/usr/bin/install':
            p=command[-1]
            assert command[-2]=='/dev/stdin' and command[1:5]==('-o','root','-g','root')
            seals=fcntl.fcntl(source.fileno(),fcntl.F_GET_SEALS)
            assert seals&fcntl.F_SEAL_WRITE
            self.files[p]=(hashlib.sha256(source.read()).hexdigest(),int(command[6],8))
            if p==POLICY:self.registered=True
        else:raise AssertionError('Unexpected command')


class FirstRun(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.packages,self.sources,self.bundle,self.payload,self.trust=setup_fixture(self.root)
        self.target=FakeTarget();self.inspector=SetupInspector(self.target);self.adapter=Adapter()
        self.reads=[]
        def reader(request):
            self.reads.append(request)
            return Mock(collect=self.adapter.observe)
        self.tx=FirstRunTransactions(self.packages,inspector=self.inspector,setup_runner=self.target.runner,
            reader=reader,clock=lambda:100,transport_factory=lambda pins:FakeTransport(pins,self.adapter,self.trust))

    def initialize(self):
        task=self.tx.initial_inspection();return self.tx.receive_inspection(task,task.run())

    def session(self):
        return SetupSession(self.payload,self.inspector.inspect(self.payload),inspector=self.inspector,
                            fresh_check=lambda:None,runner=self.target.runner,clock=lambda:100)

    def test_initial_missing_offer_no_password_or_package_submission(self):
        self.assertTrue(self.initialize());self.assertEqual(self.tx.state,'setup_required')
        self.assertFalse(self.target.calls);self.assertEqual(self.tx.available('install'),())
        self.assertFalse(self.tx.request('install'));self.assertIsNone(self.tx.begin_setup())
        self.assertEqual(self.tx.setup_review.summary()['files'],13)

    def test_exact_existing_helper_is_not_reinstalled(self):
        self.target.seed(self.payload)
        self.assertTrue(self.initialize());self.assertEqual(self.tx.state,'idle')
        self.assertIn('core',self.tx.available('install'));self.assertFalse(self.target.calls)

    def test_partial_files_dirs_and_changed_existing_helper_block(self):
        for kind in ('file','directory','modified'):
            self.setUp()
            if kind=='file':self.target.files[POLICY]=('a'*64,0o644)
            if kind=='directory':self.target.dirs[CACHE]=0o700
            if kind=='modified':
                self.target.seed(self.payload);self.target.files[POLICY]=('0'*64,0o644)
            self.assertFalse(self.initialize());self.assertEqual(self.tx.state,'blocked')
            self.assertFalse(self.target.calls)

    def test_full_setup_policy_last_fresh_inventory_and_no_automatic_package_action(self):
        self.assertTrue(self.initialize());self.assertTrue(self.tx.request_setup())
        self.assertFalse(self.target.calls)
        session=self.tx.begin_setup();self.assertIsNone(self.tx.begin_setup())
        outcome=session.run();self.assertEqual(outcome.state,'verified_setup')
        self.assertEqual(len(self.target.calls),16)
        self.assertEqual(self.target.calls[-1][-1],POLICY)
        self.assertTrue(self.tx.receive_setup(session,outcome));self.assertEqual(self.tx.state,'setup_done')
        self.assertEqual(session.run(),outcome);self.assertEqual(len(self.target.calls),16)
        self.assertEqual(self.tx.available('install'),())
        self.assertTrue(self.tx.finish_setup());self.assertTrue(self.initialize())
        self.assertEqual(self.tx.state,'idle');self.assertFalse(self.tx.transport.sent)
        self.assertNotIn('lock',self.adapter.calls);self.assertEqual(len(self.target.calls),16)

    def test_legacy_authorization_helper_and_unrelated_files_are_preserved(self):
        legacy = {'/usr/lib/gamesir-control-center/authorize': ('b'*64,0o755),
                  '/usr/share/polkit-1/actions/other-project.policy': ('c'*64,0o644)}
        self.target.files.update(legacy)
        self.assertEqual(self.session().run().state,'verified_setup')
        for path,value in legacy.items():self.assertEqual(self.target.files[path],value)
        self.assertTrue(all(c[-1] not in legacy for c in self.target.calls))

    def test_clean_parent_created_only_when_missing_and_old_parent_retained(self):
        self.target=FakeTarget(parent=False);self.inspector=SetupInspector(self.target)
        outcome=self.session().run();self.assertEqual(outcome.state,'verified_setup')
        self.assertEqual(self.target.calls[0][-1],PARENT);self.assertEqual(len(self.target.calls),17)
        self.assertTrue(all('-p' not in c[len(SUDO):] for c in self.target.calls))

    def test_cancel_before_setup_sends_nothing_and_can_reopen_review(self):
        self.initialize();self.tx.request_setup();self.assertTrue(self.tx.cancel_setup())
        self.assertIsNone(self.tx.begin_setup());self.assertFalse(self.target.calls)
        self.assertTrue(self.tx.request_setup());self.assertFalse(self.target.calls)

    def test_changed_host_or_expired_review_never_authenticates(self):
        self.initialize();self.tx.request_setup()
        self.adapter.host=replace(self.adapter.host,database_token='f'*64)
        outcome=self.tx.begin_setup().run();self.assertEqual(outcome.error,'host_changed')
        self.assertFalse(outcome.changes_possible);self.assertFalse(self.target.calls)
        s=self.session();s.expires_at=99;self.assertEqual(s.run().error,'setup_review_expired')
        self.assertFalse(self.target.calls)

    def test_changed_target_after_review_does_not_authenticate(self):
        session=self.session();self.target.dirs[CACHE]=0o700
        outcome=session.run();self.assertEqual(outcome.error,'setup_partial_installation')
        self.assertFalse(self.target.calls)

    def test_host_change_during_password_wait_stops_before_payload_copy(self):
        self.initialize();self.tx.request_setup();session=self.tx.begin_setup()
        original=self.target.runner
        def changed(argv,source=None):
            original(argv,source)
            self.adapter.host=replace(self.adapter.host,database_token='e'*64)
        session.runner=changed;outcome=session.run()
        self.assertEqual(outcome.error,'host_changed');self.assertTrue(outcome.changes_possible)
        self.assertFalse(self.target.files);self.assertNotIn(POLICY,self.target.files)
        self.assertTrue(all(c[len(SUDO)]=='/usr/bin/mkdir' for c in self.target.calls))

    def test_first_command_failure_and_timeout_stop_no_policy_or_retry(self):
        for error in ('setup_command_failed','setup_completion_unknown'):
            self.setUp();session=self.session()
            session.runner=Mock(side_effect=SetupCommandError(error))
            outcome=session.run();self.assertEqual(outcome.state,'uncertain')
            self.assertTrue(outcome.changes_possible);self.assertEqual(outcome.error,error)
            self.assertEqual(session.runner.call_count,1);session.run();self.assertEqual(session.runner.call_count,1)
            self.assertNotIn(POLICY,self.target.files)

    def test_mid_copy_failure_preserves_first_error_partial_state_and_no_cleanup(self):
        session=self.session();original=self.target.runner
        def fail(argv,source=None):
            if len(self.target.calls)==6:raise SetupCommandError('original_failure')
            original(argv,source)
        session.runner=fail;outcome=session.run()
        self.assertEqual(outcome.error,'original_failure');self.assertTrue(outcome.changes_possible)
        self.assertNotIn(POLICY,self.target.files);self.assertTrue(self.target.files)
        with self.assertRaises(BackendError):self.inspector.inspect(self.payload)

    def test_source_changed_after_loading_cannot_change_sealed_handoff(self):
        expected={p:h for p,d,h in self.payload.rows}
        for path in self.sources.rglob('*'):
            if path.is_file():path.write_bytes(b'changed source')
        session=self.session();original=self.target.runner
        def check(argv,source=None):
            if source:
                with self.assertRaises(OSError):os.write(source.fileno(),b'changed')
            original(argv,source)
        session.runner=check;self.assertEqual(session.run().state,'verified_setup')
        self.assertEqual({p:h for p,(h,m) in self.target.files.items()},expected)

    def test_concurrent_exclusive_directory_reservation_stops_second_setup(self):
        session=self.session();original=self.target.runner
        def racing(argv,source=None):
            if not self.target.calls:self.target.dirs[BASE]=0o755
            original(argv,source)
        session.runner=racing;outcome=session.run()
        self.assertEqual(outcome.state,'uncertain');self.assertEqual(len(self.target.calls),1)
        self.assertFalse(self.target.files)

    def test_payload_tamper_symlink_and_arbitrary_target_refused_offline(self):
        path=self.sources/POLICY.lstrip('/');path.write_bytes(b'tampered')
        with self.assertRaises(BackendError):load_payload(self.sources,self.bundle)
        path.unlink();path.symlink_to(self.sources/COPYING.lstrip('/'))
        with self.assertRaises(BackendError):load_payload(self.sources,self.bundle)
        rows=self.payload.rows[:-1]+(('/etc/evil',b'x',hashlib.sha256(b'x').hexdigest()),)
        with self.assertRaises(BackendError):SetupPayload(rows).validate()

    def test_no_agent_or_wrong_target_block_before_offer(self):
        self.target.bad_prerequisite=True;self.assertFalse(self.initialize())
        self.assertEqual(self.tx.error,'setup_agent_unavailable');self.assertFalse(self.target.calls)
        self.target.bad_prerequisite=False;self.tx.state='loading'
        self.adapter.host=replace(self.adapter.host,kernel='unsupported')
        self.assertFalse(self.initialize());self.assertEqual(self.tx.error,'bundle_target_mismatch')
        self.assertFalse(self.target.calls)

    def test_system_runner_has_fixed_clean_environment_no_shell_or_appimage_root_code(self):
        child=Mock();child.wait.return_value=0
        command=(*SUDO,'/usr/bin/mkdir','-m','0755','--',BASE)
        with patch.dict(os.environ,{'LD_PRELOAD':'evil','PYTHONPATH':'evil','QT_PLUGIN_PATH':'evil'}), \
             patch('helper_setup.subprocess.Popen',return_value=child) as start:
            SystemSetupRunner()(command)
        args,kwargs=start.call_args
        self.assertEqual(args[0],command);self.assertFalse(kwargs['shell'])
        self.assertEqual(kwargs['env']['SUDO_ASKPASS'],'/usr/bin/ksshaskpass')
        for key in ('LD_PRELOAD','PYTHONPATH','QT_PLUGIN_PATH'):self.assertNotIn(key,kwargs['env'])
        self.assertNotIn('python',' '.join(command));self.assertNotIn('sh',' '.join(command))

    def test_system_runner_rejects_unknown_paths_modes_and_root_scripts_before_prompt(self):
        bad = ((*SUDO, '/bin/sh', '-c', 'anything'),
               (*SUDO, '/usr/bin/mkdir', '-m', '0755', '--', '/etc/unrelated'),
               (*SUDO, '/usr/bin/mkdir', '-m', '0777', '--', BASE),
               (*SUDO, '/usr/bin/install', '-o', 'root', '-g', 'root', '-m', '0644', '--', '/tmp/input', POLICY))
        with patch('helper_setup.subprocess.Popen', side_effect=AssertionError('No authentication')):
            for command in bad:
                with self.subTest(command=command), self.assertRaises(SetupCommandError):
                    SystemSetupRunner()(command)

    def test_permission_failure_never_becomes_missing_helper_evidence(self):
        with patch('helper_setup.os.lstat',side_effect=PermissionError('private error')):
            with self.assertRaisesRegex(BackendError,'setup_target_unreadable'):
                FixedTarget().exists(BASE)
        with patch('helper_setup.os.lstat',side_effect=FileNotFoundError()):
            self.assertFalse(FixedTarget().exists(BASE))

    def test_real_same_user_targets_are_never_accepted_as_protected(self):
        with self.assertRaises(BackendError):FixedTarget().directory(self.root)

    def test_real_system_copy_tools_run_only_as_same_user_in_temporary_fake_root(self):
        import subprocess,stat
        fake=self.root/'fake-root'
        for parent in ('usr/lib/gamesir-control-center','usr/share/licenses','usr/share/polkit-1/actions','var/cache'):
            (fake/parent).mkdir(parents=True,exist_ok=True)
        calls=[]
        def unprivileged(argv,source=None):
            tail=argv[len(SUDO):];target=fake/tail[-1].lstrip('/')
            if tail[0]=='/usr/bin/mkdir':cmd=[tail[0],'-m',tail[2],'--',str(target)]
            else:cmd=[tail[0],'-m',tail[6],'--','/dev/stdin',str(target)]
            subprocess.run(cmd,stdin=source if source is not None else subprocess.DEVNULL,
                           capture_output=True,check=True,timeout=5,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            if source:source.seek(0)
            self.target.runner(argv,source);calls.append(cmd)
        session=self.session();session.runner=unprivileged
        self.assertEqual(session.run().state,'verified_setup');self.assertEqual(len(calls),16)
        self.assertTrue(all(c[0] in ('/usr/bin/mkdir','/usr/bin/install') for c in calls))
        for path,data,digest in self.payload.rows:
            installed=fake/path.lstrip('/')
            self.assertEqual(installed.read_bytes(),data)
            self.assertEqual(stat.S_IMODE(installed.stat().st_mode),mode(path))
        self.assertEqual(stat.S_IMODE((fake/CACHE.lstrip('/')).stat().st_mode),0o700)

    def test_stager_copies_only_pinned_payload_not_approval_script(self):
        import package_control_center as package
        (self.sources/'unreviewed.py').write_text('raise RuntimeError()')
        out=self.root/'staged'
        result=package.stage_reviewed_helper(self.sources,self.packages,out)
        self.assertEqual(result['files'],13);self.assertFalse(result['installed'])
        self.assertFalse((out/'unreviewed.py').exists())
        self.assertEqual(load_payload(out,self.bundle),self.payload)


if __name__=='__main__':unittest.main()
