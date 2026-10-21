#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline encrypted backup tests use ONLY the public RFC8032 test seed."""
import hashlib
import json
import os
import pty
import select
import signal
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import backup_release_key as b
SEED=bytes.fromhex('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60')
KEY=bytes.fromhex('302e020100300506032b657004220420')+SEED
PUBLIC='d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a'
ID=hashlib.sha256(bytes.fromhex(PUBLIC)).hexdigest()
PASSWORD='public fixture passphrase only'


class Backup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.encrypted=b.encrypt(KEY,PASSWORD,ID)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='gamesir-public-backup-fixture-')
        self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.key=self.root/'public-fixture.der';self.key.write_bytes(KEY);self.key.chmod(0o600)
        self.output=self.root/'fixture-encrypted.p8'
    def test_encrypted_pkcs8_round_trip_and_kdf(self):
        b.verify_encrypted(self.encrypted,PASSWORD,ID)
        self.assertNotIn(KEY,self.encrypted);self.assertNotIn(SEED,self.encrypted)
        fd=b.memfd(self.encrypted)
        try:
            output=b.openssl(('asn1parse','-inform','DER','-in','/proc/self/fd/'+str(fd)),(fd,))
        finally:os.close(fd)
        for value in (b'PBES2',b'PBKDF2',b'hmacWithSHA256',b'aes-256-cbc',b'0927C0'):
            self.assertIn(value,output)
    def test_wrong_passphrase_corruption_and_other_key_rejected(self):
        for encrypted,password,expected in ((self.encrypted,'incorrect public fixture phrase',ID),
                (self.encrypted[:-1]+bytes([self.encrypted[-1]^1]),PASSWORD,ID),
                (self.encrypted,PASSWORD,'0'*64)):
            with self.assertRaises(b.BackupError):b.verify_encrypted(encrypted,password,expected)
    def test_invalid_recovery_phrase_closes_all_anonymous_descriptors(self):
        before=len(list(Path('/proc/self/fd').iterdir()))
        for _ in range(5):
            with self.assertRaises(b.BackupError):b.verify_encrypted(self.encrypted,'short',ID)
        self.assertEqual(len(list(Path('/proc/self/fd').iterdir())),before)
    def test_real_exclusive_write_mode_and_readback(self):
        result=b.backup(self.key,self.output,PASSWORD,ID)
        self.assertTrue(result['encrypted_backup_verified']);self.assertFalse(result['off_device_copy_confirmed'])
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode),0o600)
        self.assertEqual(self.key.read_bytes(),KEY)
        b.verify_encrypted(self.output.read_bytes(),PASSWORD,ID)
    def test_existing_file_and_symlink_preserved(self):
        self.output.write_bytes(b'keep')
        with self.assertRaises(b.BackupError):b.backup(self.key,self.output,PASSWORD,ID)
        self.assertEqual(self.output.read_bytes(),b'keep');self.output.unlink()
        self.output.symlink_to(self.key)
        with self.assertRaises(b.BackupError):b.backup(self.key,self.output,PASSWORD,ID)
        self.assertEqual(self.key.read_bytes(),KEY)
    def test_repository_destination_and_unsafe_key_mode_hardlink_rejected(self):
        with self.assertRaises(b.BackupError):b.backup(self.key,ROOT/'build/secret.p8',PASSWORD,ID)
        self.key.chmod(0o644)
        with self.assertRaises(b.BackupError):b.backup(self.key,self.output,PASSWORD,ID)
        self.key.chmod(0o600);os.link(self.key,self.root/'linked')
        with self.assertRaises(b.BackupError):b.backup(self.key,self.output,PASSWORD,ID)
        self.assertFalse(self.output.exists())
    def test_short_control_and_wrong_key_fail_before_output(self):
        for password in ('short','long enough but\nnewline','\x00'*20):
            with self.assertRaises(b.BackupError):b.backup(self.key,self.output,password,ID)
        with self.assertRaises(b.BackupError):b.backup(self.key,self.output,PASSWORD,'0'*64)
        self.assertFalse(self.output.exists())
    def test_root_rejected_and_errors_do_not_include_private_material(self):
        with patch.object(b.os,'geteuid',return_value=0),self.assertRaises(b.BackupError):
            b.backup(self.key,self.output,PASSWORD,ID)
        with patch.object(b.os,'getuid',return_value=0),self.assertRaises(b.BackupError):
            b.backup(self.key,self.output,PASSWORD,ID)
    def test_no_passphrase_or_plaintext_key_in_child_arguments_environment(self):
        real=subprocess.run
        with patch.object(b.subprocess,'run',wraps=real) as calls:b.encrypt(KEY,PASSWORD,ID)
        for call in calls.call_args_list:
            args,kw=call
            self.assertNotIn(PASSWORD,repr(args)+repr(kw['env']))
            self.assertEqual(kw['stdin'],subprocess.DEVNULL)
            self.assertNotIn('shell',kw)
            self.assertTrue(kw['pass_fds'])
        self.assertNotIn(KEY,self.encrypted)
    def test_cli_without_create_does_not_open_secret_or_prompt(self):
        p=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/backup_release_key.py'),
            '--private-key',str(self.root/'not-read.der'),'--destination',str(self.output)],
            stdin=subprocess.DEVNULL,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(json.loads(p.stdout)['created']);self.assertFalse(self.output.exists())
    def test_sealed_password_input_cannot_change(self):
        fd=b.memfd(b'public fixture\n')
        try:
            with self.assertRaises(OSError):os.write(fd,b'change')
        finally:os.close(fd)
    def test_destination_race_preserves_existing_file_and_failure_never_writes_plaintext(self):
        def race(*args):self.output.write_bytes(b'concurrent keep');return self.encrypted
        with patch.object(b,'encrypt',side_effect=race),self.assertRaises(FileExistsError):
            b.backup(self.key,self.output,PASSWORD,ID)
        self.assertEqual(self.output.read_bytes(),b'concurrent keep');self.output.unlink()
        with patch.object(b.os,'fsync',side_effect=OSError('fixture sync failure')),self.assertRaises(OSError):
            b.backup(self.key,self.output,PASSWORD,ID)
        self.assertTrue(self.output.exists());self.assertNotIn(KEY,self.output.read_bytes())
    def test_password_warning_never_falls_back_to_echoed_or_piped_input(self):
        tty=Mock();tty.__enter__=Mock(return_value=tty);tty.__exit__=Mock(return_value=False)
        with patch.object(b.os,'open',return_value=999),patch.object(b.os,'fdopen',return_value=tty),patch.object(b.os,'isatty',return_value=True), \
             patch.object(b.getpass,'getpass',side_effect=b.getpass.GetPassWarning('fixture no echo unavailable')):
            with self.assertRaises(b.getpass.GetPassWarning):b.interactive_password()
    def test_real_controlling_terminal_input_is_not_echoed(self):
        pid,fd=pty.fork()
        if pid==0:
            code="import sys;sys.path.insert(0,sys.argv[1]);import backup_release_key as b;assert b.interactive_password()==sys.argv[2];print('BACKUP_TTY_OK')"
            os.execv(sys.executable,[sys.executable,'-I','-B','-c',code,str(ROOT/'scripts'),PASSWORD])
        log=b'';sent=0;done=False;deadline=time.monotonic()+10
        try:
            while time.monotonic()<deadline:
                ready,_,_=select.select([fd],[],[],0.1)
                if ready:
                    try:block=os.read(fd,4096)
                    except OSError:break
                    if not block:break
                    log+=block
                    if sent==0 and b'Zeichen): ' in log:os.write(fd,PASSWORD.encode()+b'\n');sent=1
                    if sent==1 and b'wiederholen: ' in log:os.write(fd,PASSWORD.encode()+b'\n');sent=2
                    if b'BACKUP_TTY_OK\r\n' in log:done=True;break
            self.assertTrue(done,log);self.assertEqual(sent,2);self.assertNotIn(PASSWORD.encode(),log)
        finally:
            os.close(fd)
            if not done:os.kill(pid,signal.SIGTERM)
            os.waitpid(pid,0)


if __name__=='__main__':unittest.main()
