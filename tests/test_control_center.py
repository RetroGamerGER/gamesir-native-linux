#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Phase-A state/translation contract; no Qt, host probes or real actions."""
import ast
from contextlib import redirect_stderr
from contextlib import ExitStack
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / 'tools/control_center'
sys.path.insert(0, str(UI))
from i18n import CATALOGS, choose_language
from model import Preview, SITUATIONS, LINKS
import main as launcher


class Languages(unittest.TestCase):
    def test_catalogs_are_complete_and_not_empty(self):
        self.assertEqual(set(CATALOGS['de']), set(CATALOGS['en']))
        for language, catalog in CATALOGS.items():
            for key, value in catalog.items():
                with self.subTest(language=language, key=key):
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())

    def test_system_locale_and_english_fallback(self):
        for locale, expected in [('de_DE', 'de'), ('de-AT', 'de'), ('en_GB', 'en'),
                                 ('fr_FR', 'en'), ('C', 'en'), ('', 'en')]:
            self.assertEqual(choose_language(None, locale), expected)

    def test_saved_explicit_language_wins(self):
        self.assertEqual(choose_language('en', 'de_DE'), 'en')
        self.assertEqual(choose_language('de', 'en_US'), 'de')
        self.assertEqual(choose_language('unknown', 'de_DE'), 'de')

    def test_all_scenarios_and_outcomes_are_translatable(self):
        for catalog in CATALOGS.values():
            for s in SITUATIONS:
                self.assertIn(s.notice, catalog)
                self.assertIn('scenario_' + s.key, catalog)
            for key in ('offline', 'corrupt', 'incomplete', 'package', 'cancelled', 'removal'):
                self.assertIn('error_' + key, catalog)


class PreviewFlow(unittest.TestCase):
    def at(self, key):
        p = Preview()
        p.select(next(i for i, s in enumerate(SITUATIONS) if s.key == key))
        return p

    def test_construction_has_no_pending_action(self):
        p = Preview()
        self.assertEqual(p.pending, '')
        self.assertIsNone(p.result)
        self.assertTrue(p.can_install)
        self.assertFalse(p.can_remove)

    def test_confirmation_is_required_and_consumed_once(self):
        p = Preview()
        self.assertFalse(p.confirm())
        self.assertTrue(p.request('install'))
        self.assertFalse(p.situation.installed)
        self.assertFalse(p.request('install'))
        self.assertFalse(p.request('remove'))
        self.assertTrue(p.confirm())
        self.assertFalse(p.confirm())
        self.assertTrue(p.situation.installed)
        self.assertFalse(p.situation.loaded)  # Installing never claims runtime activation.

    def test_cancel_does_not_install(self):
        p = Preview()
        p.request('install')
        self.assertTrue(p.cancel())
        self.assertFalse(p.cancel())
        self.assertFalse(p.confirm())
        self.assertFalse(p.situation.installed)
        self.assertEqual(p.result[0], 'result_cancelled')

    def test_unsupported_distribution_and_missing_headers_block_action(self):
        for key in ('unsupported', 'headers'):
            p = self.at(key)
            self.assertFalse(p.can_install)
            self.assertFalse(p.request('install'))
            self.assertFalse(p.confirm())

    def test_already_installed_does_not_allow_duplicate_install(self):
        p = self.at('installed')
        self.assertFalse(p.can_install)
        self.assertFalse(p.request('install'))
        self.assertTrue(p.can_remove)

    def test_receiver_present_controller_off_is_a_normal_state(self):
        p = self.at('waiting')
        self.assertTrue(p.situation.receiver)
        self.assertTrue(p.situation.installed)
        self.assertTrue(p.situation.loaded)
        self.assertFalse(p.situation.connected)
        self.assertEqual(p.situation.notice, 'waiting_notice')

    def test_internet_integrity_and_package_failures_never_report_installation(self):
        for key in ('offline', 'corrupt', 'incomplete', 'package', 'cancelled'):
            with self.subTest(key=key):
                p = self.at(key)
                self.assertTrue(p.request('install'))
                self.assertTrue(p.confirm())
                self.assertFalse(p.situation.installed)
                self.assertEqual(p.result[1], 'error_' + key)

    def test_removal_requires_confirmation(self):
        p = self.at('installed')
        self.assertTrue(p.request('remove'))
        self.assertTrue(p.situation.installed)
        p.cancel()
        self.assertTrue(p.situation.installed)
        p.request('remove')
        p.confirm()
        self.assertFalse(p.situation.installed)
        self.assertFalse(p.situation.loaded)
        self.assertFalse(p.situation.connected)
        self.assertTrue(p.situation.receiver)  # Physical presence is not installation.

    def test_unresolved_removal_is_not_forced(self):
        p = self.at('removal')
        p.request('remove')
        p.confirm()
        self.assertTrue(p.situation.installed)
        self.assertEqual(p.result[1], 'error_removal')

    def test_scenario_selection_cancels_pending_flow(self):
        p = Preview()
        p.request('install')
        p.select(2)
        self.assertFalse(p.confirm())
        self.assertIsNone(p.result)

    def test_invalid_selection_and_action_are_rejected(self):
        p = Preview()
        for index in (-1, len(SITUATIONS), True, '0'):
            with self.assertRaises(ValueError):
                p.select(index)
        for action in ('resume', 'release', 'reboot', 'flash', 'sudo', ''):
            self.assertFalse(p.request(action))

    def test_all_demo_flows_without_file_network_process_or_device_io(self):
        with ExitStack() as stack:
            for name in ('subprocess.run', 'subprocess.Popen', 'socket.socket',
                         'urllib.request.urlopen', 'builtins.open', 'os.open',
                         'pathlib.Path.open', 'pathlib.Path.read_text', 'pathlib.Path.write_text'):
                stack.enter_context(patch(name, side_effect=AssertionError('Unexpected I/O: ' + name)))
            for i in range(len(SITUATIONS)):
                p = Preview()
                p.select(i)
                if p.can_install:
                    p.request('install'); p.confirm()
                if p.can_remove:
                    p.request('remove'); p.cancel(); p.request('remove'); p.confirm()
                p.dismiss_result()

    def test_only_explicit_io_boundaries_may_import_process_or_network_modules(self):
        forbidden = {'subprocess', 'socket', 'ctypes', 'requests', 'urllib', 'http', 'QtNetwork'}
        for source in UI.rglob('*.py'):
            tree = ast.parse(source.read_text())
            for node in ast.walk(tree):
                names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
                for name in names:
                    # Explicit boundaries only. New package adapters are inert
                    # on import and are never constructed by normal launch.
                    allowed = {
                        'status.py': {'subprocess'}, 'privilege/transport.py': {'subprocess'},
                        'package_client.py': {'subprocess'}, 'package_host.py': {'subprocess'},
                        # Explicit sealed-byte OpenSSL signature verification;
                        # no shell/config/private key/network on import or startup.
                        'package_catalog.py': {'subprocess'},
                        'package_alpm.py': {'ctypes'},
                        # First-run setup uses validated fixed sudo/mkdir/install
                        # arguments only after its separate GUI confirmation.
                        'helper_setup.py': {'subprocess'},
                        # Explicit maintainer-only fixed-tool migration; never
                        # imported/offered as automatic repair by GUI startup.
                        'helper_migration.py': {'subprocess'},
                        # Sole explicit, user-side release downloader. Parsing
                        # and construction are inert; no root/network on launch.
                        'release_download.py': {'http', 'urllib'},
                        # Explicit calibration-only mode. Fixed installed
                        # Polkit entry and root-private manager endpoint only.
                        'tmr_client.py': {'subprocess'},
                        'tmr_channel.py': {'socket'},
                    }.get(source.relative_to(UI).as_posix(), set())
                    self.assertFalse((forbidden - allowed).intersection(name.split('.')), (source.name, name))

    def test_launcher_refuses_root_and_exposes_no_live_action(self):
        with patch.object(launcher.os, 'geteuid', return_value=0), redirect_stderr(io.StringIO()):
            self.assertEqual(launcher.main(['--demo']), 2)
        for action in ('--live', '--install', '--remove', '--flash'):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                launcher.main([action])
            self.assertEqual(error.exception.code, 2)

    def test_links_match_existing_project_references(self):
        readme = (ROOT / 'README.md').read_text()
        self.assertEqual(set(LINKS), {'github', 'deadband'})
        self.assertIn(LINKS['deadband'], readme)
        for url in LINKS.values():
            self.assertTrue(url.startswith('https://github.com/'))


if __name__ == '__main__':
    unittest.main()
