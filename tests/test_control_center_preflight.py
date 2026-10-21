#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package review/planning regressions. Synthetic metadata, no host inspection."""
from dataclasses import replace
import io
import json
import os
import stat
from types import SimpleNamespace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/control_center'))
from artifacts import BackendError, Catalog, Review, package_info
from backend import HostEvidence, Request
from rehearsal import create_rehearsal, fixture_catalog, KERNEL
from package_catalog import EMPTY, parse_catalog, serialize_catalog, load_installed_catalog
from package_execution import ExecutionTrust, InstalledReview
from package_preflight import FileInventory, PlanningEvidence
from package_host import SystemEvidence


class Preflight(unittest.TestCase):
    def test_optional_empty_makepkg_url_allowed_required_fields_not_relaxed(self):
        self.assertEqual(package_info(b'url = \npkgname = example\n')['url'], [''])
        for key in ('pkgname', 'pkgver', 'arch', 'depend', 'license'):
            with self.assertRaises(BackendError): package_info((key + ' = \n').encode())

    def test_vcs_inventory_is_valid_without_weakening_project_release_grammar(self):
        host = create_rehearsal(clock=lambda: 100).port.host
        replace(host, installed=(('unrelated-git', 'r123.abcdef-1'),)).validate(100)
        for bad in ('r1;echo', '/tmp/file', 'r1\ncommand', ''):
            with self.assertRaises(BackendError):
                replace(host, installed=(('unrelated-git', bad),)).validate(100)
        catalog, _ = fixture_catalog()
        with self.assertRaises(BackendError): replace(catalog.records[0], version='r123-1').validate()

    def test_data_inventory_never_loads_alpm_opens_devices_or_creates_a_lock(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as folder:
            root = Path(folder); (root / 'ALPM_DB_VERSION').write_text('9\n')
            pkg = root / 'unrelated-git-r123.abc-1'; pkg.mkdir()
            (pkg / 'desc').write_text('%NAME%\nunrelated-git\n\n%VERSION%\nr123.abc-1\n\n')
            before = {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with patch('package_preflight.protected', side_effect=lambda p, **_:Path(p)), \
                    patch('package_alpm.C.CDLL', side_effect=AssertionError('No native handle')), \
                    patch('subprocess.Popen', side_effect=AssertionError('No child')):
                self.assertEqual(FileInventory(root).rows(), (('unrelated-git', 'r123.abc-1'),))
            self.assertEqual(before, {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root.parent / 'db.lck').exists())

    def test_duplicate_or_malformed_description_does_not_infer_absence(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as folder:
            root = Path(folder); pkg = root/'fake-1';pkg.mkdir()
            for content in ('%NAME%\nfake\n\n', '%NAME%\nfake\n\n%NAME%\nother\n\n%VERSION%\n1\n',
                            '%NAME%\nfake\nextra\n\n%VERSION%\n1\n'):
                (pkg/'desc').write_text(content)
                with patch('package_preflight.protected', side_effect=lambda p, **_:Path(p)), \
                        self.assertRaises(BackendError): FileInventory(root).rows()

    def test_planning_and_locked_root_share_identical_fact_implementation(self):
        from package_host import SystemPackages
        self.assertIs(PlanningEvidence.observe, SystemPackages.observe)
        self.assertIs(PlanningEvidence.configuration, SystemPackages.configuration)
        host = create_rehearsal(clock=lambda: 100).port.host
        reader = PlanningEvidence.__new__(PlanningEvidence); reader.clock=lambda:100
        reader.observe=Mock(side_effect=(host, replace(host, observed_at=100)))
        with patch('package_preflight.os.geteuid', return_value=1000):
            self.assertEqual(reader.collect(), host)
        reader.observe=Mock(side_effect=(host, replace(host, database_token='1'*64)))
        with patch('package_preflight.os.geteuid', return_value=1000), self.assertRaises(BackendError):
            reader.collect()

    def test_root_or_locked_or_stale_planning_is_refused(self):
        host = create_rehearsal(clock=lambda:100).port.host
        reader=PlanningEvidence.__new__(PlanningEvidence);reader.clock=lambda:100
        reader.observe=Mock(return_value=host)
        with patch('package_preflight.os.geteuid', return_value=0), self.assertRaises(BackendError): reader.collect()
        reader.observe.assert_not_called()
        for changed in (replace(host,database_locked=True), replace(host,observed_at=0)):
            reader.observe=Mock(return_value=changed)
            with patch('package_preflight.os.geteuid', return_value=1000), self.assertRaises(BackendError):reader.collect()

    def test_closed_catalog_roundtrip_is_not_public_binary_approval(self):
        from artifacts import PUBLIC_BINARIES
        catalog,_=fixture_catalog()
        trust=ExecutionTrust(catalog, tuple(InstalledReview(r.component,r.version,r.guards) for r in catalog.records))
        parsed=parse_catalog(serialize_catalog(trust))
        self.assertEqual(parsed.catalog.records, catalog.records)
        self.assertEqual(parsed.installed, trust.installed)
        self.assertEqual(parse_catalog(json.dumps(EMPTY).encode()).catalog.records, ())
        self.assertEqual(PUBLIC_BINARIES.records, ())

    def test_catalog_refuses_commands_paths_unknown_fields_and_duplicate_reviews(self):
        for extra in ({'path':'/tmp/pkg'}, {'command':'pacman'}, {'schema':True}, {'scope':'public'}, {'installed':[{}]}):
            with self.assertRaises(BackendError):parse_catalog(json.dumps({**EMPTY,**extra}).encode())
        catalog,_=fixture_catalog()
        trust=ExecutionTrust(Catalog((catalog.records[0],)))
        value=json.loads(serialize_catalog(trust));value['packages']*=2
        with self.assertRaises(BackendError):parse_catalog(json.dumps(value).encode())

    def test_installed_catalog_uses_one_fixed_nofollow_protected_path(self):
        from package_catalog import CATALOG
        with patch('package_host.protected', side_effect=BackendError('unsafe')), \
                patch('package_catalog.os.open') as opened, self.assertRaises(BackendError):
            load_installed_catalog()
        opened.assert_not_called()
        self.assertEqual(CATALOG, '/usr/lib/gamesir-control-center/package-executor/REVIEWED_PACKAGES.json')

    def test_catalog_fd_is_reattested_and_bounded_before_trusting_data(self):
        from package_catalog import CATALOG
        data=json.dumps(EMPTY).encode()
        for uid,size in ((1000,len(data)),(0,65537)):
            with tempfile.TemporaryFile() as fixture:
                fixture.write(data);fixture.seek(0);fd=os.dup(fixture.fileno())
                info=SimpleNamespace(st_uid=uid,st_gid=0,st_mode=stat.S_IFREG|0o644,st_size=size)
                with patch('package_host.protected'),patch('package_catalog.os.open',return_value=fd) as opened, \
                        patch('package_catalog.os.fstat',return_value=info),self.assertRaises(BackendError):
                    load_installed_catalog()
                self.assertEqual(opened.call_args.args[0],CATALOG)
                self.assertTrue(opened.call_args.args[1]&os.O_NOFOLLOW)

    def test_fixed_catalog_loader_accepts_only_the_protected_typed_contents(self):
        data=json.dumps(EMPTY).encode()
        with tempfile.TemporaryFile() as fixture:
            fixture.write(data);fixture.seek(0);fd=os.dup(fixture.fileno())
            info=SimpleNamespace(st_uid=0,st_gid=0,st_mode=stat.S_IFREG|0o644,st_size=len(data))
            with patch('package_host.protected'),patch('package_catalog.os.open',return_value=fd), \
                    patch('package_catalog.os.fstat',return_value=info):
                loaded=load_installed_catalog()
            self.assertEqual(loaded.catalog.records,())
            self.assertEqual(loaded.installed,())


if __name__=='__main__':unittest.main()
