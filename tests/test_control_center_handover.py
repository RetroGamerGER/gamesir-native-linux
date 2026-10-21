#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One-confirmation handover safety; no key/policy/host/root access."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'tools/control_center'))
import control_center_handover as h
from helper_migration import MigrationResult
from artifacts import BackendError


class Handover(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'build');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.spec=object()
        self.appdir=self.root/'AppDir';self.bundle=self.appdir/'usr/share/gamesir-control-center'
        self.bundle.mkdir(parents=True);(self.bundle/'fixture').write_text('unchanged')
        (self.appdir/'BUILD_INPUTS.json').write_text(json.dumps({'files':{
            'usr/share/gamesir-control-center/fixture':hashlib.sha256(b'unchanged').hexdigest()}}))
        self.image=self.root/'fixture.AppImage';self.image.write_bytes(b'\x7fELF\x02\x01\x01\x00AI\x02public fixture')
        self.migration={'bundle':str(self.bundle),'key_id':'a'*64}
        # Only fictional external path strings; neither is opened in plan mode.
        self.key='/tmp/gamesir-public-fixture-not-opened.der';self.destination='/tmp/gamesir-public-fixture-not-created.p8'
    def prepare(self):
        with patch.object(h.migration,'prepare',return_value=(self.spec,self.migration)):
            return h.prepare(self.bundle,self.image,self.key,self.destination)
    def test_plan_reads_artifacts_but_never_key_password_or_live_target(self):
        with patch.object(h.backup,'secret_file',side_effect=AssertionError),patch.object(h.backup,'interactive_password',side_effect=AssertionError),patch.object(h.migration,'execute',side_effect=AssertionError):
            spec,plan=self.prepare()
        self.assertIs(spec,self.spec);self.assertFalse(plan['executed']);self.assertFalse(plan['publish'])
        self.assertEqual(plan['image']['sha256'],hashlib.sha256(self.image.read_bytes()).hexdigest())
    def test_approved_plan_rechecks_image_appdir_and_sources(self):
        _,plan=self.prepare();p=self.root/'plan.json';data=json.dumps(plan).encode();p.write_bytes(data)
        digest=hashlib.sha256(data).hexdigest()
        with patch.object(h.migration,'prepare',return_value=(self.spec,self.migration)):
            self.assertIs(h.load_approved(p,digest)[0],self.spec)
            with self.assertRaises(BackendError):h.load_approved(p,'0'*64)
            self.image.write_bytes(self.image.read_bytes()+b'changed')
            with self.assertRaises(BackendError):h.load_approved(p,digest)
        self.image.write_bytes(b'\x7fELF\x02\x01\x01\x00AI\x02public fixture')
        (self.bundle/'fixture').write_text('changed')
        with self.assertRaises(BackendError):self.prepare()
    def test_failed_or_cancelled_backup_never_enters_privileged_phase(self):
        _,plan=self.prepare();migrate=Mock(side_effect=AssertionError)
        for action in (Mock(side_effect=OSError('public fixture')),Mock(return_value={'encrypted_backup_verified':False})):
            with self.assertRaises(Exception):h.run(self.spec,plan,password='public fixture long phrase',backup_action=action,migrate_action=migrate)
        migrate.assert_not_called()
        with patch.object(h.backup,'interactive_password',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):h.run(self.spec,plan,migrate_action=migrate)
        migrate.assert_not_called()
    def test_one_run_backup_before_migration_no_package_launch_or_retry(self):
        _,plan=self.prepare();order=[]
        def backup(*args):order.append('backup');return {'encrypted_backup_verified':True}
        def migrate(*args):order.append('migration');return MigrationResult('verified_migration','policy_restored')
        with contextlib.redirect_stdout(io.StringIO()):
            result=h.run(self.spec,plan,password='public fixture long phrase',backup_action=backup,migrate_action=migrate)
        self.assertEqual(order,['backup','migration']);self.assertFalse(result['driver_changed'])
        self.assertTrue(result['off_device_copy_still_required'])
    def test_cli_cannot_apply_without_exact_approval(self):
        p=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/control_center_handover.py'),'--apply'],stdin=subprocess.DEVNULL,capture_output=True,check=False)
        self.assertEqual(p.returncode,2);self.assertNotIn(b'Traceback',p.stderr)


if __name__=='__main__':unittest.main()
