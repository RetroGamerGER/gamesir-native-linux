#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic Steam-log contract tests; no SDL initialization or input devices."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/sdl"))
import steam_mapping_audit as audit  # noqa: E402
from gamesir_mapping import mapping  # noqa: E402

GUID = "03004535373500009c10000001000000"
OTHER_GUID = "03008665373500009c10000001000000"
ZZZ_GUID = "03004535373500005e10000007060000"  # SDL fixture-derived 105e/0607 candidate; log below is synthetic.


def log_line(value, stamp="2026-01-01 12:00:00", pid="109c"):
    return f"[{stamp}] SDL Mapping for 3537/{pid}: {value}\n"


def standard_mapping(guid=GUID):
    return ",".join(part for part in mapping(guid).split(",")
                    if not part.startswith(("paddle", "misc")))


class SteamMappingAudit(unittest.TestCase):
    def test_missing_paddles_proposes_only_additional_bindings(self):
        result = audit.audit_text(log_line(standard_mapping()))
        expected = ",".join(part for part in mapping(GUID).split(",")
                            if not part.startswith("misc"))
        self.assertEqual(result["candidate_mapping"], expected)
        self.assertTrue(result["standard_bindings_unchanged"])
        self.assertEqual({d["field"] for d in result["field_diff"]}, audit.PADDLE_FIELDS)
        self.assertTrue(all(d["before"] is None for d in result["field_diff"]))
        self.assertEqual(result["status"], "proposal_only")

    def test_existing_complete_mapping_needs_no_change(self):
        result = audit.audit_text(log_line(mapping(GUID)))
        self.assertEqual(result["status"], "already_matches")
        self.assertEqual(result["field_diff"], [])
        self.assertNotIn("physical_paddle_labels", result)

    def test_105e_proposal_preserves_standard_controls_and_unconfirmed_labels(self):
        for complete in (False, True):
            with self.subTest(complete=complete):
                value = (mapping(ZZZ_GUID) if complete else standard_mapping(ZZZ_GUID)) + "crc:3545,"
                result = audit.audit_text(log_line(value, pid="105E"), ZZZ_GUID.upper())
                self.assertEqual(result["guid"], ZZZ_GUID)
                self.assertEqual(result["status"], "already_matches" if complete else "proposal_only")
                self.assertEqual({d["field"] for d in result["field_diff"]},
                                 set() if complete else audit.PADDLE_FIELDS)
                self.assertTrue(result["standard_bindings_unchanged"])
                self.assertTrue(result["candidate_mapping"].endswith("crc:3545,"))
                self.assertEqual(result["physical_paddle_labels"], "unconfirmed")

    def test_mixed_products_require_selection_and_keep_each_products_latest_record(self):
        text = (log_line(standard_mapping(ZZZ_GUID), pid="105e") +
                log_line(mapping(GUID)) +
                log_line(mapping(ZZZ_GUID), "2026-01-01 12:10:00", pid="105e"))
        with self.assertRaisesRegex(audit.AuditError, "Several target GUIDs"):
            audit.audit_text(text)
        standard = audit.audit_text(text, GUID)
        zzz = audit.audit_text(text, ZZZ_GUID)
        self.assertEqual(standard["selection"], {"last_matching_line": 2,
                                               "matching_records": 1,
                                               "distinct_target_guids": 2})
        self.assertEqual(zzz["selection"], {"last_matching_line": 3,
                                          "matching_records": 2,
                                          "distinct_target_guids": 2})
        self.assertEqual(standard["candidate_mapping"], mapping(GUID))
        self.assertEqual(zzz["candidate_mapping"], mapping(ZZZ_GUID))
        self.assertNotIn("physical_paddle_labels", standard)

    def test_declared_product_must_match_guid_even_in_an_unselected_record(self):
        for guid, declared in ((GUID, "105e"), (ZZZ_GUID, "109c")):
            bad = log_line(mapping(guid), pid=declared)
            for text, selected in ((bad, None), (bad, guid),
                                   (log_line(mapping(GUID)) + bad, GUID)):
                with self.subTest(guid=guid, selected=selected), \
                     self.assertRaisesRegex(audit.AuditError, "Declared mapping product"):
                    audit.audit_text(text, selected)

    def test_crc_metadata_preserved_without_changing_standard_bindings(self):
        for complete in (False, True):
            with self.subTest(complete=complete):
                value = (mapping(GUID) if complete else standard_mapping()) + "crc:3545,"
                result = audit.audit_text(log_line(value))
                self.assertTrue(result["observed_mapping"].endswith("crc:3545,"))
                self.assertTrue(result["candidate_mapping"].endswith("crc:3545,"))
                self.assertTrue(result["standard_bindings_unchanged"])
                fields = {d["field"] for d in result["field_diff"]}
                self.assertEqual(fields, set() if complete else audit.PADDLE_FIELDS)

    def test_crc_uses_guid_little_endian_word_and_preserves_case(self):
        guid = GUID[:4] + "cdab" + GUID[8:]
        value = mapping(guid) + "crc:ABCD,"
        result = audit.audit_text(log_line(value), guid)
        self.assertEqual(result["candidate_mapping"], value)
        self.assertEqual(result["status"], "already_matches")
        for crc in ("4535", "0000", "ffff"):
            with self.subTest(crc=crc), self.assertRaisesRegex(audit.AuditError, "CRC does not match"):
                audit.audit_text(log_line(mapping(GUID) + f"crc:{crc},"))

    def test_malformed_duplicate_crc_and_unknown_hints_stay_rejected(self):
        for suffix in ("crc:,", "crc:354,", "crc:03545,", "crc:0x3545,",
                       "crc:+3545,", "crc:3545 ,", "crc:zzzz,", "crc:b1,",
                       "crc:3545,crc:3545,", "crc:3545,hint:private-token,"):
            with self.subTest(suffix=suffix), self.assertRaises(audit.AuditError) as caught:
                audit.audit_text(log_line(mapping(GUID) + suffix))
            self.assertNotIn("private-token", str(caught.exception))

    def test_crc_does_not_relax_axis_or_standard_button_validation(self):
        for before, after in (("a:b0", "a:b11"), ("lefty:a1", "lefty:a1~"),
                              ("righttrigger:a5", "righttrigger:a2"),
                              ("dpup:h0.1", "dpup:b0")):
            with self.subTest(before=before), self.assertRaisesRegex(audit.AuditError, "Standard buttons"):
                audit.audit_text(log_line(mapping(GUID).replace(before, after) + "crc:3545,"))

    def test_auxiliary_buttons_are_preserved_only_if_already_canonical(self):
        for missing in ("misc1:b16,", "misc2:b15,"):
            line = mapping(GUID).replace(missing, "")
            result = audit.audit_text(log_line(line))
            self.assertEqual(result["candidate_mapping"], line)
            self.assertEqual(result["status"], "already_matches")
        with self.assertRaisesRegex(audit.AuditError, "auxiliary buttons differ"):
            audit.audit_text(log_line(mapping(GUID).replace("misc1:b16", "misc1:b0")))

    def test_latest_record_for_same_guid_wins(self):
        text = log_line(standard_mapping()) + log_line(mapping(GUID), "2026-01-01 12:10:00")
        result = audit.audit_text(text)
        self.assertEqual(result["selection"], {"last_matching_line": 2,
                                             "matching_records": 2,
                                             "distinct_target_guids": 1})
        self.assertEqual(result["status"], "already_matches")

    def test_ambiguous_identities_require_explicit_selection(self):
        text = log_line(standard_mapping()) + log_line(mapping(OTHER_GUID))
        with self.assertRaisesRegex(audit.AuditError, "Several target GUIDs"):
            audit.audit_text(text)
        self.assertEqual(audit.audit_text(text, OTHER_GUID)["guid"], OTHER_GUID)
        self.assertEqual(audit.audit_text(text, GUID)["status"], "proposal_only")

    def test_unobserved_explicit_guid_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "does not occur"):
            audit.audit_text(log_line(mapping(GUID)), OTHER_GUID)

    def test_never_changes_standard_bindings(self):
        for before, after in (("a:b0", "a:b10"), ("lefty:a1", "lefty:a1~"),
                              ("dpup:h0.1", "dpup:b0"), ("start:b7,", ""),
                              ("platform:Linux", "platform:Windows")):
            with self.subTest(before=before), self.assertRaises(audit.AuditError):
                audit.audit_text(log_line(standard_mapping().replace(before, after)))

    def test_extra_binding_replacement_is_explicit_in_diff(self):
        result = audit.audit_text(log_line(mapping(GUID).replace("paddle1:b12", "paddle1:b14")))
        self.assertEqual(result["field_diff"], [{"field": "paddle1", "before": "b14", "after": "b12"}])

    def test_wrong_pid_vendor_bus_or_backend_rejected(self):
        for bad in (GUID.replace("9c10", "0a10"), GUID.replace("9c10", "2210"),
                    GUID.replace("9c10", "5d10"), GUID.replace("3735", "5e04"),
                    "0500" + GUID[4:], GUID[:-4] + "6800", "not-a-guid"):
            with self.subTest(guid=bad), self.assertRaises(audit.AuditError):
                audit.audit_text(log_line(mapping(GUID).replace(GUID, bad)))
            with self.assertRaises(audit.AuditError):
                audit.audit_text(log_line(mapping(GUID)), bad)
        with self.assertRaises(audit.AuditError):
            audit.audit_text(log_line(mapping(GUID)).replace("3537/109c", "3537/100a"))

    def test_unrelated_private_log_text_and_device_names_are_not_reflected(self):
        private = "account-secret-76561199999999999-token"
        text = private + "\n" + log_line(standard_mapping().replace("GameSir G7 Pro", private))
        serialized = json.dumps(audit.audit_text(text))
        self.assertNotIn(private, serialized)
        self.assertIn("<redacted-device-name>", serialized)

    def test_unreviewed_fields_and_duplicate_keys_rejected_without_echo(self):
        for suffix in ("a:b1,", "hint:private-token,", "paddle1:private-token,"):
            with self.subTest(suffix=suffix), self.assertRaises(audit.AuditError) as caught:
                audit.audit_text(log_line(standard_mapping() + suffix))
            self.assertNotIn("private-token", str(caught.exception))

    def test_bounded_regular_file_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "controller.txt"
            source.write_text(log_line(standard_mapping()), encoding="utf-8")
            self.assertEqual(audit.read_regular_log(source), source.read_text())
            result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/sdl/steam_mapping_audit.py"),
                                     "--log-file", str(source)], capture_output=True, text=True, check=True)
            self.assertTrue(json.loads(result.stdout)["ok"])
            self.assertEqual(result.stderr, "")
            self.assertEqual(list(Path(tmp).iterdir()), [source])
            alias = Path(tmp) / "alias"
            alias.symlink_to(source)
            fifo = Path(tmp) / "fifo"
            os.mkfifo(fifo)
            for rejected in (alias, fifo, Path(tmp), Path(tmp) / "missing"):
                with self.subTest(path=rejected.name), self.assertRaises(audit.AuditError):
                    audit.read_regular_log(rejected)
            source.write_bytes(b"\xff")
            with self.assertRaises(audit.AuditError):
                audit.read_regular_log(source)
            source.write_bytes(b"x" * (audit.MAX_LOG_BYTES + 1))
            with self.assertRaises(audit.AuditError):
                audit.read_regular_log(source)

    def test_text_size_and_mapping_size_limits(self):
        with self.assertRaises(audit.AuditError):
            audit.audit_text("x" * (audit.MAX_LOG_BYTES + 1))
        with self.assertRaises(audit.AuditError):
            audit.audit_text(log_line(mapping(GUID) + "x" * audit.MAX_MAPPING_CHARS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
