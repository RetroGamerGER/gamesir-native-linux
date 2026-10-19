#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic proc trees and one test-owned child only; no live target access."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('gamescope_identity', ROOT/'tools/sdl/gamescope_identity.py')
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)
UID = 4321


def status(uid=UID, name='gamescope-wl', tracer=0, state='S'):
    uids = (uid,) * 4 if isinstance(uid, int) else uid
    return (f'Name:\t{name}\nState:\t{state} (fixture)\n'
            f'Uid:\t' + '\t'.join(map(str, uids)) + f'\nTracerPid:\t{tracer}\n')


def start(pid, ticks=12345, name='gamescope-wl', state='S'):
    return f'{pid} ({name}) ' + ' '.join([state, *(['0'] * 18), str(ticks)]) + '\n'


class Selection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.proc = self.root/'proc'; self.proc.mkdir()
        self.exe = self.root/'bin/gamescope'; self.exe.parent.mkdir()
        self.exe.write_bytes(b'own executable identity fixture'); self.exe.chmod(0o700)
        self.p = self.add_process(17)

    def add_process(self, pid, uid=UID, exe=None, name='gamescope-wl'):
        proc = self.proc/str(pid); proc.mkdir()
        (proc/'status').write_text(status(uid, name))
        (proc/'comm').write_text(name+'\n')
        (proc/'stat').write_text(start(pid, name=name))
        (proc/'exe').symlink_to(exe or self.exe)
        return proc

    def find(self):
        return m.find_gamescope(UID, proc_root=self.proc, executable=self.exe)

    def verify(self, identity):
        m.verify_gamescope(identity, UID, proc_root=self.proc, executable=self.exe)

    def test_mutable_name_reproduces_legacy_false_negative(self):
        self.assertFalse((self.p/'comm').read_text().strip() == 'gamescope')
        got = self.find()
        self.assertEqual((got.pid, got.uids, got.name), (17, (UID,)*4, 'gamescope-wl'))

    def test_directory_owner_is_not_process_credentials(self):
        self.assertNotEqual(self.p.stat().st_uid, UID)
        self.assertEqual(self.find().uids, (UID,)*4)

    def test_comm_not_used_or_required(self):
        (self.p/'comm').unlink()
        (self.p/'status').write_text(status(name='renamed worker'))
        self.assertEqual(self.find().name, 'renamed worker')

    def test_renaming_does_not_invalidate_same_process(self):
        saved = self.find()
        (self.p/'status').write_text(status(name='another name'))
        (self.p/'stat').write_text(start(17, name='a (name) with ) parentheses'))
        self.verify(saved)

    def test_same_name_other_executable_rejected_with_diagnostic(self):
        other = self.root/'other'; other.write_text('own other fixture'); other.chmod(0o700)
        (self.p/'exe').unlink(); (self.p/'exe').symlink_to(other)
        with self.assertRaisesRegex(m.IdentityError, 'matches=0, same_uid=1, name_only=1'):
            self.find()

    def test_same_basename_copy_not_accepted(self):
        other = self.root/'different/gamescope'; other.parent.mkdir()
        shutil.copy2(self.exe, other)
        (self.p/'exe').unlink(); (self.p/'exe').symlink_to(other)
        with self.assertRaisesRegex(m.IdentityError, 'matches=0'): self.find()

    def test_foreign_user_is_not_adopted(self):
        (self.p/'status').write_text(status(UID+1))
        with self.assertRaisesRegex(m.IdentityError, 'matches=0, same_uid=0'): self.find()

    def test_foreign_user_does_not_conflict_with_unique_expected_user(self):
        self.add_process(18, uid=UID+1)
        self.assertEqual(self.find().pid, 17)

    def test_mixed_credentials_stop(self):
        for uids in ((UID, 0, UID, UID), (UID, UID, UID+1, UID), (0, 0, 0, UID)):
            with self.subTest(uids=uids):
                (self.p/'status').write_text(status(uids))
                with self.assertRaisesRegex(m.IdentityError, 'credentials'): self.find()

    def test_root_or_invalid_requested_uid_rejected_before_access(self):
        with patch.object(Path, 'resolve', side_effect=AssertionError('No access')):
            for uid in (0, -1, True, '4321'):
                with self.assertRaisesRegex(m.IdentityError, 'non-root'): m.find_gamescope(uid)

    def test_ambiguous_same_user_stops(self):
        self.add_process(18)
        with self.assertRaisesRegex(m.IdentityError, 'matches=2'): self.find()

    def test_missing_or_malformed_uids_stop(self):
        for text in ('Name: gamescope\n', status((UID,)*3), status(('bad',)*4), status()+f'Uid: {UID}\n'):
            with self.subTest(text=text):
                (self.p/'status').write_text(text)
                with self.assertRaises(m.IdentityError): self.find()

    def test_traced_stopped_zombie_rejected(self):
        for text in (status(tracer=9), status(state='T'), status(state='t'), status(state='Z'), status(state='X')):
            with self.subTest(text=text):
                (self.p/'status').write_text(text)
                with self.assertRaises(m.IdentityError): self.find()

    def test_malformed_or_wrong_pid_stat_rejected(self):
        for text in ('bad', start(18), start(17, ticks='nan'), start(17, state='Z')):
            with self.subTest(text=text):
                (self.p/'stat').write_text(text)
                with self.assertRaises(m.IdentityError): self.find()

    def test_deleted_executable_stops(self):
        (self.p/'exe').unlink(); (self.p/'exe').symlink_to(str(self.exe)+' (deleted)')
        with self.assertRaisesRegex(m.IdentityError, 'changed or deleted'): self.find()

    def test_permission_denied_stops_not_no_user_misdiagnosis(self):
        original = m.os.readlink
        def denied(path, *a, **kw):
            if path == self.p/'exe': raise PermissionError('fixture')
            return original(path, *a, **kw)
        with patch.object(m.os, 'readlink', denied):
            with self.assertRaisesRegex(m.IdentityError, 'metadata unavailable: PermissionError'): self.find()

    def test_disappeared_unrelated_entry_can_be_skipped(self):
        other = self.proc/'18'; other.mkdir()
        read = m._status
        def disappear(proc):
            if proc == other:
                proc.rmdir(); raise FileNotFoundError('own fixture')
            return read(proc)
        with patch.object(m, '_status', disappear): self.assertEqual(self.find().pid, 17)

    def test_existing_process_with_missing_metadata_stops(self):
        (self.proc/'18').mkdir()
        with self.assertRaisesRegex(m.IdentityError, 'metadata disappeared'): self.find()

    def test_selected_process_disappears_stops(self):
        def disappear(*args):
            shutil.rmtree(self.p); raise FileNotFoundError('own fixture')
        with patch.object(m, '_stable_identity', disappear):
            with self.assertRaisesRegex(m.IdentityError, 'metadata disappeared'): self.find()

    def test_pid_reuse_during_snapshot_rejected(self):
        with patch.object(m, '_start', side_effect=[100, 101]):
            with self.assertRaisesRegex(m.IdentityError, 'PID was reused'): self.find()

    def test_credential_change_between_snapshots_rejected(self):
        read = m._status; calls = 0
        def change(proc):
            nonlocal calls
            calls += 1
            if calls == 3: (proc/'status').write_text(status((UID, 0, UID, UID)))
            return read(proc)
        with patch.object(m, '_status', change):
            with self.assertRaisesRegex(m.IdentityError, 'credentials'): self.find()

    def test_backing_inode_change_rejected(self):
        read = m._snapshot; calls = 0
        def change(*args):
            nonlocal calls
            got = read(*args); calls += 1
            if calls == 1:
                self.exe.rename(self.exe.with_suffix('.old')); self.exe.write_text('replacement'); self.exe.chmod(0o700)
            return got
        with patch.object(m, '_snapshot', change):
            with self.assertRaisesRegex(m.IdentityError, 'backing file changed'): self.find()

    def test_final_recheck_rejects_replacement_or_second_instance(self):
        saved = self.find()
        (self.p/'stat').write_text(start(17, ticks=99999))
        with self.assertRaisesRegex(m.IdentityError, 'changed since precheck'): self.verify(saved)
        (self.p/'stat').write_text(start(17)); self.add_process(18)
        with self.assertRaisesRegex(m.IdentityError, 'matches=2'): self.verify(saved)

    def test_missing_or_nonexecutable_expected_file_rejected(self):
        self.exe.chmod(0o600)
        with self.assertRaisesRegex(m.IdentityError, 'regular executable'): self.find()
        self.exe.unlink()
        with self.assertRaisesRegex(m.IdentityError, 'FileNotFoundError'): self.find()

    def test_import_and_metadata_reads_do_not_open_executable_contents(self):
        opened = []; original = Path.open
        def only_metadata(path, *a, **kw):
            self.assertIn(path.name, ('status', 'stat'))
            self.assertTrue(path.is_relative_to(self.proc)); opened.append(path)
            return original(path, *a, **kw)
        with patch.object(Path, 'open', only_metadata): self.find()
        self.assertTrue(opened)

    def test_oversized_metadata_rejected(self):
        (self.p/'status').write_text('x' * 65537)
        with self.assertRaisesRegex(m.IdentityError, 'Oversized'): self.find()


class OwnChild(unittest.TestCase):
    def test_real_mutable_comm_with_unchanged_executable_and_uids(self):
        # Only this child is read. No scan of real /proc, vendor app or sudo.
        child = subprocess.Popen([sys.executable, '-I', '-B', '-c',
            'import ctypes,sys\n'
            'assert ctypes.CDLL(None).prctl(15,b"gamescope-wl",0,0,0)==0\n'
            'print("ready",flush=True)\nsys.stdin.buffer.read(1)\n'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            import select
            self.assertTrue(select.select([child.stdout], [], [], 5)[0], 'Own child readiness timeout')
            self.assertEqual(child.stdout.readline(), b'ready\n')
            proc = Path('/proc')/str(child.pid)
            executable = Path(sys.executable).resolve(strict=True)
            identity = m._stable_identity(proc, os.getuid(), executable, m._stamp(executable))
            self.assertEqual(identity.name, 'gamescope-wl')
            self.assertNotEqual((proc/'comm').read_text().strip(), 'gamescope')
            self.assertEqual(identity.uids, (os.getuid(),)*4)
        finally:
            child.communicate(b'x', timeout=5)
        self.assertEqual(child.returncode, 0)


if __name__ == '__main__':
    unittest.main()
