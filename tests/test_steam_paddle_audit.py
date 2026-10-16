#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic saved-log cases; no proprietary JS copied or executed."""
from pathlib import Path
from contextlib import redirect_stdout
import io
import json
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/sdl'))
import steam_paddle_audit as audit
from gamesir_mapping import mapping
from steam_mapping_audit import AuditError, read_regular_log

GUID = '03004535373500009c10000053010000'
ZZZ_GUID = '03004535373500005e10000007060000'  # SDL fixture-derived 105e/0607 candidate; logs remain synthetic.
STAMP = '2026-01-01 12:00:00'
NEW_UI_SHA256 = '5a28c25041d07e69cf591a414519e0cf970b6884c1a0106659dcd9f1fb9586f9'
NEW_CLIENT_VERSION = '1791918634'


def mapping_log(paddles=True, guid=GUID, pid='109c'):
    value = mapping(guid).replace('misc2:b15,', '')
    if not paddles:
        value = ','.join(p for p in value.split(',') if not p.startswith('paddle'))
    return f'[{STAMP}] SDL Mapping for 3537/{pid}: {value}\n'


def ui_log(caps=0x9843ff, stamp=STAMP, index=0, version=audit.CLIENT_VERSION, pid=0x109c):
    return (f'[{stamp}] Client version: {version}\n'
            f'[{stamp}] !! Controller {index} attributes:\n'
            f'  Type: 30\n  ProductID: {pid}\n  Serial: 3537-{pid:04x}-private\n'
            f'  Capabilities: {caps:016x}\n  Firmware Version: 0\n')


class SteamPaddleAudit(unittest.TestCase):
    def test_current_gap_distinguishes_mapping_from_capabilities(self):
        r = audit.classify(mapping_log(False), ui_log(), GUID, 0)
        self.assertEqual(r['status'], 'mapping_and_ui_capability_gap')
        self.assertFalse(any(r['paddle_bindings_match'].values()))
        self.assertFalse(any(r['ui_capability_gate'].values()))
        self.assertEqual(r['raw_button_reception'], 'not_measured')

    def test_mapping_alone_never_claims_editor_support(self):
        r = audit.classify(mapping_log(), ui_log(), GUID, 0)
        self.assertEqual(r['status'], 'mapped_paddles_not_advertised_to_ui')
        self.assertTrue(all(r['paddle_bindings_match'].values()))
        self.assertEqual(r['steam_editor_acceptance'], 'not_measured')
        self.assertNotIn('physical_paddle_labels', r)

    def test_105e_matches_sdl_fields_without_claiming_physical_labels(self):
        r = audit.classify(mapping_log(guid=ZZZ_GUID, pid='105e'),
                           ui_log(audit.GRIPS | audit.UPPER_GRIPS, pid=0x105e), ZZZ_GUID, 0)
        self.assertEqual(r['status'], 'mapping_and_capability_gate_ready_live_acceptance_required')
        self.assertEqual(r['paddle_bindings_match'],
                         {'paddle1': True, 'paddle2': True, 'paddle3': True, 'paddle4': True})
        self.assertEqual(r['physical_paddle_labels'], 'unconfirmed')
        self.assertEqual(r['raw_button_reception'], 'not_measured')
        self.assertEqual(r['steam_editor_acceptance'], 'not_measured')
        self.assertEqual(r['game_rebinding'], 'not_measured')

    def test_105e_checks_exact_bindings_and_both_capability_gates(self):
        r = audit.classify(mapping_log(guid=ZZZ_GUID, pid='105e').replace('paddle2:b11', 'paddle2:b12'),
                           ui_log(audit.GRIPS, pid=0x105e), ZZZ_GUID, 0)
        self.assertFalse(r['paddle_bindings_match']['paddle2'])
        self.assertTrue(r['paddle_bindings_match']['paddle1'])
        self.assertEqual(r['status'], 'mapping_and_ui_capability_gap')
        self.assertFalse(r['ui_capability_gate']['LeftGrip_Upper'])
        self.assertTrue(r['ui_capability_gate']['LeftGrip'])

    def test_mixed_models_correlate_only_selected_guid_product_and_controller(self):
        mappings = mapping_log() + mapping_log(guid=ZZZ_GUID, pid='105e')
        attributes = ui_log(index=0) + ui_log(audit.GRIPS | audit.UPPER_GRIPS, index=1, pid=0x105e)
        standard = audit.classify(mappings, attributes, GUID, 0)
        zzz = audit.classify(mappings, attributes, ZZZ_GUID, 1)
        self.assertEqual(standard['mapping_line'], 1)
        self.assertEqual(standard['status'], 'mapped_paddles_not_advertised_to_ui')
        self.assertEqual(zzz['mapping_line'], 2)
        self.assertTrue(all(zzz['ui_capability_gate'].values()))
        for guid, index in ((GUID, 1), (ZZZ_GUID, 0)):
            with self.subTest(guid=guid), self.assertRaisesRegex(AuditError, 'expected native GameSir family'):
                audit.classify(mappings, attributes, guid, index)

    def test_product_and_serial_family_each_match_selected_guid(self):
        for guid, pid, wrong in ((GUID, 0x109c, 0x105e), (ZZZ_GUID, 0x105e, 0x109c)):
            mapping_text = mapping_log(guid=guid, pid=f'{pid:04x}')
            for attributes in (ui_log(pid=pid).replace(f'ProductID: {pid}', f'ProductID: {wrong}'),
                               ui_log(pid=pid).replace(f'3537-{pid:04x}-', f'3537-{wrong:04x}-')):
                with self.subTest(guid=guid, attributes=attributes), self.assertRaises(AuditError):
                    audit.classify(mapping_text, attributes, guid, 0)

    def test_declared_mapping_pid_mismatch_is_rejected_before_attribute_matching(self):
        for guid, pid, declared in ((GUID, 0x109c, '105e'), (ZZZ_GUID, 0x105e, '109c')):
            with self.subTest(guid=guid), self.assertRaisesRegex(AuditError, 'Declared mapping product'):
                audit.classify(mapping_log(guid=guid, pid=declared), ui_log(pid=pid), guid, 0)

    def test_capabilities_alone_never_claim_mapping_or_delivery(self):
        r = audit.classify(mapping_log(False), ui_log(audit.GRIPS | audit.UPPER_GRIPS), GUID, 0)
        self.assertEqual(r['status'], 'mapping_gap')
        self.assertTrue(all(r['ui_capability_gate'].values()))

    def test_four_capability_combinations(self):
        for lower in (False, True):
            for upper in (False, True):
                with self.subTest(lower=lower, upper=upper):
                    r = audit.classify(mapping_log(), ui_log(lower*audit.GRIPS | upper*audit.UPPER_GRIPS), GUID, 0)
                    self.assertEqual(r['ui_capability_gate'],
                                     {'LeftGrip_Upper': lower and upper, 'RightGrip_Upper': lower and upper,
                                      'LeftGrip': lower, 'RightGrip': lower})
                    self.assertEqual(r['game_rebinding'], 'not_measured')
                    if lower and upper:
                        self.assertEqual(r['status'], 'mapping_and_capability_gate_ready_live_acceptance_required')

    def test_exact_paddle_identity_not_merely_four_fields(self):
        r = audit.classify(mapping_log().replace('paddle2:b11', 'paddle2:b12'), ui_log(), GUID, 0)
        self.assertFalse(r['paddle_bindings_match']['L4'])
        self.assertTrue(r['paddle_bindings_match']['R4'])

    def test_requires_matching_record_time_and_controller(self):
        for log in (ui_log(stamp='2026-01-01 11:59:59'), ui_log(index=1), ''):
            with self.subTest(log=log), self.assertRaises(AuditError):
                audit.classify(mapping_log(), log, GUID, 0)

    def test_ambiguous_record_rejected_not_last_chosen(self):
        with self.assertRaises(AuditError):
            audit.classify(mapping_log(), ui_log()+ui_log(), GUID, 0)

    def test_record_does_not_leak_across_timestamp(self):
        log = ui_log().replace('  Capabilities:', f'[{STAMP}] unrelated\n  Capabilities:')
        with self.assertRaises(AuditError):
            audit.classify(mapping_log(), log, GUID, 0)

    def test_missing_duplicate_and_wrong_attributes(self):
        for before, after in (
            ('  Type: 30\n', ''), ('  Type: 30\n', '  Type: 30\n  Type: 30\n'),
            ('Type: 30', 'Type: 32'), ('ProductID: 4252', 'ProductID: 4106'),
            ('3537-109c-private', 'Awaiting_Logon'),
            ('3537-109c-private', '045e-109c-private'),
            ('00000000009843ff', '9843ff'), ('00000000009843ff', 'not-a-capability'),
        ):
            with self.subTest(before=before, after=after), self.assertRaises(AuditError):
                audit.classify(mapping_log(), ui_log().replace(before, after), GUID, 0)

    def test_log_without_mapping_timestamp_rejected(self):
        with self.assertRaises(AuditError):
            audit.classify(mapping_log().replace(f'[{STAMP}] ', ''), ui_log(), GUID, 0)

    def test_private_values_not_reflected(self):
        text = json.dumps(audit.classify(mapping_log(), ui_log(), GUID, 0))
        self.assertNotIn('private', text)
        self.assertNotIn('Serial', text)

    def test_source_update_requires_manual_review(self):
        for source in ('', 'throw new Error("must never execute");'):
            with self.assertRaisesRegex(AuditError, 'Unreviewed Steam UI'):
                audit.verify_ui_source(source)

    def test_reviewed_build_pairs_preserve_four_slot_gates(self):
        for digest, version in ((audit.UI_SHA256, audit.CLIENT_VERSION),
                                (NEW_UI_SHA256, NEW_CLIENT_VERSION)):
            with self.subTest(version=version):
                r = audit.classify(mapping_log(),
                                   ui_log(audit.GRIPS | audit.UPPER_GRIPS, version=version),
                                   GUID, 0, ui_sha256=digest)
                self.assertEqual(r['client_version'], version)
                self.assertTrue(all(r['ui_capability_gate'].values()))
                self.assertEqual(r['steam_editor_acceptance'], 'not_measured')
                # Synthetic digest substitution; never include/execute vendor JS.
                with mock.patch.object(audit.hashlib, 'sha256') as sha:
                    sha.return_value.hexdigest.return_value = digest
                    self.assertEqual(audit.verify_ui_source('synthetic source'), digest)

    def test_crossed_build_pairs_and_unreviewed_hash_rejected(self):
        for digest, version in ((audit.UI_SHA256, NEW_CLIENT_VERSION),
                                (NEW_UI_SHA256, audit.CLIENT_VERSION),
                                (NEW_UI_SHA256, '1234567890')):
            with self.subTest(version=version, digest=digest), self.assertRaisesRegex(AuditError, 'client version'):
                audit.classify(mapping_log(), ui_log(version=version), GUID, 0,
                               ui_sha256=digest)
        with self.assertRaisesRegex(AuditError, 'Unreviewed Steam UI'):
            audit.classify(mapping_log(), ui_log(), GUID, 0, ui_sha256='0' * 64)

    def test_new_client_requires_explicit_reviewed_hash(self):
        with self.assertRaisesRegex(AuditError, 'client version'):
            audit.classify(mapping_log(), ui_log(version=NEW_CLIENT_VERSION), GUID, 0)

    def test_cli_correlates_version_with_verified_source(self):
        args = ['steam_paddle_audit.py', '--mapping-log', 'mapping.txt',
                '--ui-log', 'attributes.txt', '--ui-bundle', 'sp.js',
                '--guid', GUID, '--controller-index', '0']
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', args), \
             mock.patch.object(audit, 'read_regular_log',
                               side_effect=['synthetic source', mapping_log(),
                                            ui_log(version=NEW_CLIENT_VERSION)]), \
             mock.patch.object(audit, 'verify_ui_source', return_value=NEW_UI_SHA256), \
             redirect_stdout(output):
            self.assertEqual(audit.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['ui_sha256'], NEW_UI_SHA256)
        self.assertEqual(result['client_version'], NEW_CLIENT_VERSION)

    def test_wrong_or_missing_client_version_rejected(self):
        for log in (ui_log().replace('1788652215', '1234567890'),
                    '\n'.join(ui_log().splitlines()[1:])):
            with self.assertRaisesRegex(AuditError, 'client version'):
                audit.classify(mapping_log(), log, GUID, 0)

    def test_bounded_reader_custom_limit(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'source.txt'
            path.write_text('12345')
            self.assertEqual(read_regular_log(path, 5), '12345')
            with self.assertRaises(AuditError):
                read_regular_log(path, 4)
            alias = Path(d)/'alias'
            alias.symlink_to(path)
            with self.assertRaises(AuditError):
                read_regular_log(alias, 5)


if __name__ == '__main__':
    unittest.main()
