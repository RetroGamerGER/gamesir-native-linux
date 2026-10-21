#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real same-user temporary filesystem; every sudo/root/host access is faked."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
import helper_migration as m
from helper_setup import SetupPayload,mode,TARGETS,COPYING,CACHE,BASE,PARENT,POLICY,SUDO,SetupCommandError
from artifacts import BackendError


class Target:
    def __init__(self,root):self.root=root;self.calls=[];self.busy=False;self.visibility=True;self.bad_owner=False
    def path(self,p):return self.root/p.lstrip('/')
    def exists(self,p):return os.path.lexists(self.path(p))
    def directory(self,p,bits=None):
        s=self.path(p).lstat()
        if not stat.S_ISDIR(s.st_mode) or bits is not None and stat.S_IMODE(s.st_mode)!=bits:
            raise BackendError('fixture_directory_changed')
    def file(self,p,digest,bits):
        f=self.path(p);s=f.lstat()
        if self.bad_owner or not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=bits or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:
            raise BackendError('fixture_file_changed')
    def snapshot(self,p,directory=False):
        s=self.path(p).lstat()
        if directory:self.directory(p)
        elif not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:raise BackendError('fixture_file_changed')
        return (s.st_dev,s.st_ino,0,0,stat.S_IMODE(s.st_mode),s.st_mtime_ns)
    def children(self,p):return frozenset(f.name for f in self.path(p).iterdir())
    def migration_tools(self):pass
    def policy(self,installed):
        if self.exists(POLICY)!=installed:raise BackendError('fixture_policy_state')
    def quiet(self):
        if self.busy:raise BackendError('migration_package_database_busy')
        if not self.visibility:raise BackendError('migration_process_visibility_unknown')
    def runner(self,argv,source=None):
        m.validate_command(argv,source);self.calls.append(argv)
        tail=list(argv[len(SUDO):])
        if argv==m.STATE_QUERY:
            tail[2]=str(self.path(CACHE))
            r=subprocess.run(tail,capture_output=True,check=False)
            if r.returncode:raise SetupCommandError('fixture_find_failed')
            return r.stdout
        if tail[0]=='/usr/bin/install':
            self.assert_sealed(source);tail[2]=str(os.getuid());tail[4]=str(os.getgid())
            tail[-1]=str(self.path(tail[-1]))
        elif tail[0]=='/usr/bin/mkdir':tail[-1]=str(self.path(tail[-1]))
        elif tail[0]=='/usr/bin/mv':tail[-2:]=[str(self.path(p)) for p in tail[-2:]]
        else:raise AssertionError('unexpected command')
        r=subprocess.run(tail,stdin=source if source is not None else subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=False)
        if r.returncode:raise SetupCommandError('fixture_command_failed')
        return b''
    def assert_sealed(self,stream):
        assert fcntl.fcntl(stream.fileno(),fcntl.F_GET_SEALS)&m.SEALS==m.SEALS
        try:os.write(stream.fileno(),b'tamper')
        except OSError:pass
        else:raise AssertionError('unsealed source')


class Migration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.addCleanup(self.tmp.cleanup)
        self.target=Target(Path(self.tmp.name));self.old=[];new=[]
        for p in TARGETS:
            data=(ROOT/'COPYING').read_bytes() if p==COPYING else b'fixture old '+p.encode()
            f=self.target.path(p);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data);f.chmod(mode(p))
            self.old.append((p,hashlib.sha256(data).hexdigest()))
            if p not in (POLICY,COPYING,m.EXECUTOR):data=b'fixture new '+p.encode()
            new.append((p,data,hashlib.sha256(data).hexdigest()))
        self.target.path(CACHE).mkdir(parents=True,mode=0o700)
        self.target.path(CACHE+'/retained-receipt').write_bytes(b'keep cache')
        self.target.path(PARENT+'/legacy-authorize').write_bytes(b'keep legacy')
        self.spec=m.MigrationSpec(tuple(self.old),SetupPayload(tuple(new)))
        self.before=self.target.snapshot(BASE,True);self.cache=self.target.snapshot(CACHE,True)
    def session(self,**kw):return m.MigrationSession(self.spec,target=self.target,runner=self.target.runner,**kw)
    def test_full_real_filesystem_migration_sealed_inputs_and_exact_command_plan(self):
        s=self.session();out=s.run();self.assertEqual(out.state,'verified_migration',out)
        self.assertEqual(self.target.calls,[a for a,b in self.spec.commands()]);self.assertEqual(len(self.target.calls),19)
        self.assertEqual(self.target.snapshot(m.BACKUP,True),self.before)
        self.assertEqual(self.target.snapshot(CACHE,True),self.cache)
        self.assertEqual(self.target.path(CACHE+'/retained-receipt').read_bytes(),b'keep cache')
        self.assertEqual(self.target.path(PARENT+'/legacy-authorize').read_bytes(),b'keep legacy')
        self.assertFalse(self.target.exists(m.HOLD));self.assertFalse(self.target.exists(m.CANDIDATE))
        self.assertEqual(s.run(),out);self.assertEqual(len(self.target.calls),19)
    def test_explicit_rollback_preserves_new_directory_and_old_inode(self):
        self.assertEqual(self.session().run().state,'verified_migration')
        newinode=self.target.snapshot(BASE,True)
        out=self.session(rollback=True).run();self.assertEqual(out.state,'verified_rollback',out)
        self.assertEqual(self.target.snapshot(BASE,True),self.before)
        self.assertEqual(self.target.snapshot(m.FAILED,True),newinode)
        self.assertEqual(self.target.snapshot(CACHE,True),self.cache)
    def test_protected_signed_state_blocks_forward_and_rollback_without_rewind(self):
        state=self.target.path(CACHE+'/release-catalog.json');state.write_bytes(b'protected metadata')
        out=self.session().run();self.assertEqual(out.error,'migration_signed_state_present');self.assertFalse(out.changes_possible)
        self.assertFalse(self.target.exists(m.CANDIDATE));state.unlink()
        self.assertEqual(self.session().run().state,'verified_migration');state.write_bytes(b'accepted revision')
        out=self.session(rollback=True).run();self.assertEqual(out.error,'migration_signed_state_present')
        self.assertFalse(out.changes_possible);self.assertTrue(self.target.exists(POLICY));self.assertFalse(self.target.exists(m.HOLD))
        self.assertEqual(state.read_bytes(),b'accepted revision')
    def test_unknown_extra_modified_owner_and_preexisting_backup_block_before_auth(self):
        for kind in ('extra','modified','owner','backup','visibility','busy'):
            with self.subTest(kind=kind):
                self.setUp()
                if kind=='extra':self.target.path(BASE+'/unexpected').write_text('keep')
                if kind=='modified':self.target.path(BASE+'/backend.py').write_text('changed')
                if kind=='owner':self.target.bad_owner=True
                if kind=='backup':self.target.path(m.BACKUP).mkdir()
                if kind=='visibility':self.target.visibility=False
                if kind=='busy':self.target.busy=True
                out=self.session().run();self.assertEqual(out.state,'blocked',out);self.assertFalse(self.target.calls)
    def test_mid_candidate_failure_no_retry_rollback_or_policy_change(self):
        original=self.target.runner
        def fail(argv,source=None):
            if len(self.target.calls)==5:raise SetupCommandError('original_copy_failure')
            return original(argv,source)
        s=self.session();s.runner=fail;out=s.run()
        self.assertEqual(out.error,'original_copy_failure');self.assertTrue(out.changes_possible)
        self.assertTrue(self.target.exists(POLICY));self.assertFalse(self.target.exists(m.BACKUP))
        self.assertEqual(self.target.snapshot(BASE,True),self.before);count=len(self.target.calls)
        s.run();self.assertEqual(count,len(self.target.calls))
    def test_failure_after_old_rename_has_separately_tested_recovery(self):
        original=self.target.runner
        def fail(argv,source=None):
            if argv[-2:]==(m.CANDIDATE,BASE):raise SetupCommandError('original_switch_failure')
            return original(argv,source)
        s=self.session();s.runner=fail;out=s.run();self.assertEqual(out.error,'original_switch_failure')
        self.assertTrue(self.target.exists(m.HOLD));self.assertFalse(self.target.exists(BASE))
        out=self.session(rollback=True).run();self.assertEqual(out.state,'verified_rollback',out)
        self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertTrue(self.target.exists(m.CANDIDATE))
    def test_final_policy_failure_retains_both_versions_and_can_explicitly_recover(self):
        original=self.target.runner
        def fail(argv,source=None):
            if argv[-2:]==(m.HOLD,POLICY):raise SetupCommandError('original_policy_restore_failure')
            return original(argv,source)
        session=self.session();session.runner=fail;out=session.run()
        self.assertEqual(out.error,'original_policy_restore_failure');self.assertTrue(self.target.exists(m.BACKUP))
        self.assertTrue(self.target.exists(BASE));self.assertTrue(self.target.exists(m.HOLD))
        out=self.session(rollback=True).run();self.assertEqual(out.state,'verified_rollback',out)
        self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertTrue(self.target.exists(m.FAILED))
    def test_old_directory_rename_failure_recovers_policy_without_moving_or_deleting_old(self):
        original=self.target.runner
        def fail(argv,source=None):
            if argv[-2:]==(BASE,m.BACKUP):raise SetupCommandError('old_rename_busy')
            return original(argv,source)
        session=self.session();session.runner=fail;self.assertEqual(session.run().error,'old_rename_busy')
        out=self.session(rollback=True).run();self.assertEqual(out.state,'verified_rollback',out)
        self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertTrue(self.target.exists(POLICY))
        self.assertTrue(self.target.exists(m.CANDIDATE));self.assertFalse(self.target.exists(m.BACKUP))
    def test_recovery_itself_can_resume_safely_after_each_rename_failure(self):
        for failure in ((m.BACKUP,BASE),(m.HOLD,POLICY)):
            with self.subTest(failure=failure):
                self.setUp();self.assertEqual(self.session().run().state,'verified_migration')
                original=self.target.runner
                def fail(argv,source=None):
                    if argv[-2:]==failure:raise SetupCommandError('recovery_rename_failed')
                    return original(argv,source)
                session=self.session(rollback=True);session.runner=fail
                self.assertEqual(session.run().error,'recovery_rename_failed')
                out=self.session(rollback=True).run();self.assertEqual(out.state,'verified_rollback',out)
                self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertTrue(self.target.exists(POLICY))
    def test_late_signed_state_stops_without_automatic_recovery_or_state_deletion(self):
        original=self.target.runner
        def race(argv,source=None):
            result=original(argv,source)
            if argv[-2:]==(POLICY,m.HOLD):self.target.path(CACHE+'/release-catalog.json').write_bytes(b'keep protected floor')
            return result
        session=self.session();session.runner=race;out=session.run()
        # Cache-directory metadata detects this late write before the following
        # fixed state query. Preserve that first error; never overwrite it.
        self.assertEqual(out.error,'migration_preserved_directory_changed');self.assertTrue(self.target.exists(m.HOLD))
        self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertFalse(self.target.exists(m.BACKUP))
        self.assertEqual(self.target.path(CACHE+'/release-catalog.json').read_bytes(),b'keep protected floor')
    def test_host_change_during_authentication_stops_before_policy_switch(self):
        calls=[0]
        def changed():
            calls[0]+=1
            if calls[0]>1:raise BackendError('host_changed')
        out=self.session(fresh_check=changed).run();self.assertEqual(out.error,'host_changed')
        self.assertTrue(self.target.exists(POLICY));self.assertFalse(self.target.exists(m.BACKUP))
    def test_move_destination_race_retains_old_and_does_not_overwrite(self):
        original=self.target.runner
        def race(argv,source=None):
            if argv[-2:]==(BASE,m.BACKUP):self.target.path(m.BACKUP).mkdir()
            return original(argv,source)
        s=self.session();s.runner=race;out=s.run();self.assertEqual(out.error,'migration_rename_unconfirmed')
        self.assertEqual(self.target.snapshot(BASE,True),self.before);self.assertTrue(self.target.exists(m.BACKUP))
    def test_unsafe_commands_unsealed_payload_and_changed_entry_rejected(self):
        for tail in (('/usr/bin/rm','-rf',BASE),('/usr/bin/mv',BASE,m.BACKUP),('/bin/sh','-c','true')):
            with self.assertRaises(SetupCommandError):m.validate_command((*SUDO,*tail),None)
        with tempfile.TemporaryFile() as source:
            with self.assertRaises(SetupCommandError):m.validate_command(self.spec.installs()[0][0],source)
        rows=list(self.spec.payload.rows);p,data,h=rows[0];rows[0]=(p,b'bad',hashlib.sha256(b'bad').hexdigest())
        # Deliberately change an authorization-critical leaf, not a module.
        rows=[(p,b'bad',hashlib.sha256(b'bad').hexdigest()) if p==POLICY else (p,d,h) for p,d,h in self.spec.payload.rows]
        with self.assertRaises(BackendError):m.MigrationSpec(self.spec.old,SetupPayload(tuple(rows))).validate()
    def test_timeout_and_inflight_helper_gate_preserve_first_error(self):
        s=self.session();s.runner=Mock(side_effect=SetupCommandError('migration_completion_unknown'))
        out=s.run();self.assertEqual(out.error,'migration_completion_unknown');self.assertEqual(s.runner.call_count,1)
        self.assertFalse(self.target.exists(m.CANDIDATE))
    def test_root_runner_environment_and_no_shell(self):
        child=Mock();child.communicate.return_value=(b'',None);child.returncode=0
        with patch.dict(os.environ,{'LD_PRELOAD':'bad','PYTHONPATH':'bad','QT_PLUGIN_PATH':'bad'}),patch('helper_migration.subprocess.Popen',return_value=child) as start:
            m.MigrationRunner()(m.STATE_QUERY)
        args,kw=start.call_args;self.assertFalse(kw['shell'])
        for name in ('LD_PRELOAD','PYTHONPATH','QT_PLUGIN_PATH'):self.assertNotIn(name,kw['env'])
        self.assertEqual(kw['env']['SUDO_ASKPASS'],'/usr/bin/ksshaskpass')
    def test_process_quiescence_recognizes_real_entry_path_and_refuses_unknown_visibility(self):
        proc=Mock();proc.name='123';proc.stat.return_value=Mock(st_uid=0)
        directory=Mock();directory.iterdir.return_value=[proc]
        for data,expected in ((b'/usr/bin/python3\0-IBS\0'+m.EXECUTOR.encode()+b'\0','migration_helper_running'),
                              (b'x'*262145,'migration_process_visibility_unknown')):
            with self.subTest(expected=expected):
                stream=Mock();stream.__enter__=Mock(return_value=stream);stream.__exit__=Mock(return_value=False)
                stream.read.return_value=data
                proc.__truediv__=Mock(return_value=Mock(open=Mock(return_value=stream)))
                with patch('helper_migration.Path',return_value=directory),patch('helper_migration.os.path.lexists',return_value=False):
                    with self.assertRaisesRegex(BackendError,expected):m.MigrationTarget().quiet()
        proc.__truediv__=Mock(return_value=Mock(open=Mock(side_effect=PermissionError)))
        with patch('helper_migration.Path',return_value=directory),patch('helper_migration.os.path.lexists',return_value=False):
            with self.assertRaisesRegex(BackendError,'migration_process_visibility_unknown'):m.MigrationTarget().quiet()
    def test_cross_filesystem_and_symlink_signed_state_fail_closed(self):
        snapshot=self.target.snapshot
        def other_device(p,directory=False):
            result=snapshot(p,directory)
            return (result[0]+1,*result[1:]) if p==BASE else result
        with patch.object(self.target,'snapshot',side_effect=other_device):
            out=self.session().run()
        self.assertEqual(out.error,'migration_cross_filesystem');self.assertFalse(self.target.calls)
        self.target.path(CACHE+'/release-catalog.json').symlink_to('/missing-public-fixture')
        out=self.session().run();self.assertEqual(out.error,'migration_signed_state_present')
        self.assertFalse(out.changes_possible)
    def test_cli_apply_requires_exact_approval_before_live_access(self):
        p=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/migrate_control_center_helper.py'),'--apply'],
            stdin=subprocess.DEVNULL,capture_output=True,check=False)
        self.assertEqual(p.returncode,2);self.assertNotIn(b'Traceback',p.stderr)
    def test_package_owned_or_unknown_helper_cannot_be_migrated(self):
        target=m.MigrationTarget()
        with patch.object(target,'prerequisites'),patch('package_host.protected'):
            for answer in ((0,'some-owner\n',''),(1,'','unknown error'),(2,'','')):
                with patch.object(target,'query',side_effect=[(0,'--no-copy --no-clobber',''),answer]):
                    with self.assertRaisesRegex(BackendError,'migration_package_managed_or_unknown_helper'):
                        target.migration_tools()


class OwnershipQueries(unittest.TestCase):
    """Replay the real exit-count failure; never call a host package manager."""
    def query(self, argv):
        if argv == ['/usr/bin/mv','--help']:
            return 0,'--no-copy --no-clobber',''
        self.assertEqual(argv[:3],['/usr/bin/pacman','-Qoq','--'])
        paths=argv[3:]
        self.assertTrue(paths and all(p in TARGETS for p in paths))
        # Exact observed aggregate result: status13, empty stdout and one
        # unowned-path diagnostic per each of the thirteen reviewed paths.
        return len(paths),'',''.join('error: No package owns '+p+'\n' for p in paths)

    def check(self, answer=None, at=0):
        target=m.MigrationTarget();seen=[]
        def query(argv):
            result=self.query(argv)
            if argv[0]=='/usr/bin/pacman':
                seen.append(argv)
                if answer is not None and len(seen)==at+1:return answer
            return result
        with patch.object(target,'prerequisites'),patch('package_host.protected'),patch.object(target,'query',side_effect=query):
            target.migration_tools()
        return seen

    def test_recorded_thirteen_failure_count_now_passes_via_individual_queries(self):
        aggregate=self.query(['/usr/bin/pacman','-Qoq','--',*TARGETS])
        self.assertEqual(aggregate[0],13)
        self.assertNotEqual(aggregate[0],1)  # The original guard rejected this.
        seen=self.check()
        self.assertEqual(seen,[['/usr/bin/pacman','-Qoq','--',p] for p in TARGETS])

    def test_owned_path_at_any_position_blocks_including_last(self):
        for index in range(len(TARGETS)):
            with self.subTest(index=index),self.assertRaisesRegex(BackendError,'migration_package_managed_or_unknown_helper'):
                self.check((0,'some-package\n',''),index)

    def test_arbitrary_or_aggregate_failure_codes_never_count_as_unowned(self):
        for code in (-9,0,2,13,255):
            with self.subTest(code=code),self.assertRaises(BackendError):
                self.check((code,'','error: No package owns '+TARGETS[0]+'\n'))

    def test_wrong_missing_extra_or_duplicate_diagnostics_block(self):
        expected='error: No package owns '+TARGETS[0]+'\n'
        for errors in ('','database unavailable\n',expected+expected,
                       'error: No package owns '+TARGETS[1]+'\n',
                       expected+'error: database unavailable\n'):
            with self.subTest(errors=errors),self.assertRaises(BackendError):
                self.check((1,'',errors))

    def test_stdout_even_whitespace_is_not_unowned_evidence(self):
        for output in ('some-package\n',' ','\n'):
            with self.subTest(output=output),self.assertRaises(BackendError):
                self.check((1,output,'error: No package owns '+TARGETS[0]+'\n'))

    def test_query_failure_stops_before_any_privileged_call(self):
        target=m.MigrationTarget();runner=Mock(side_effect=AssertionError('no sudo'))
        # Run the actual session preflight with only system observations faked.
        with patch.object(target,'prerequisites'),patch('package_host.protected'),patch.object(target,'query',side_effect=[
                (0,'--no-copy --no-clobber',''),(1,'','database unavailable')]):
            fixture=Migration();fixture.setUp()
            try:
                out=m.MigrationSession(fixture.spec,target=target,runner=runner).run()
            finally:fixture.doCleanups()
        self.assertEqual((out.state,out.phase,out.changes_possible),('blocked','preflight',False))
        self.assertEqual(out.error,'migration_package_managed_or_unknown_helper')
        runner.assert_not_called()

    def test_query_timeout_is_preserved_as_failure_not_unowned(self):
        target=m.MigrationTarget()
        with patch.object(target,'prerequisites'),patch('package_host.protected'),patch.object(target,'query',side_effect=[
                (0,'--no-copy --no-clobber',''),BackendError('query_failed')]):
            with self.assertRaisesRegex(BackendError,'query_failed'):target.migration_tools()


if __name__=='__main__':unittest.main()
