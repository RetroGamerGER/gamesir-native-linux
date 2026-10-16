#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Correlate saved Steam mapping/attribute logs with an inspected UI build.

Read-only, offline: never initializes SDL, launches Steam, opens devices or
executes the supplied JavaScript. Internal capability bits are observations of
fingerprinted Steam builds, NOT a public API for setting capabilities.
"""
import argparse
import hashlib
import json
import re

from steam_mapping_audit import AuditError, audit_text, read_regular_log
from gamesir_mapping import native_guid_pid

UI_SHA256 = 'f9606b111203c9140dcdd6fc016a0ee00e4c8406aeb786187c42873f08d071fb'
CLIENT_VERSION = '1788652215'
# The legacy constants remain the default for existing offline callers. Each
# hash identifies the complete inspected gate implementation, not any JS file
# distributed with that client version. In the newer build it lives in sp.js.
INSPECTED_UI_BUILDS = {
    UI_SHA256: CLIENT_VERSION,
    '5a28c25041d07e69cf591a414519e0cf970b6884c1a0106659dcd9f1fb9586f9': '1791918634',
}
MAX_UI_BYTES = 32 * 1024 * 1024
GRIPS = 1 << 10
UPPER_GRIPS = 1 << 22
TIMESTAMP = r'\[([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\]'
HEADER = re.compile(TIMESTAMP + r' !! Controller ([0-9]+) attributes:')
CLIENT = re.compile(TIMESTAMP + r' Client version: ([0-9]+)')
PADDLES = {'L4': ('paddle2', 'b11'), 'R4': ('paddle1', 'b12'),
           'L5': ('paddle4', 'b13'), 'R5': ('paddle3', 'b14')}


def verify_ui_source(text):
    """Fail closed after a Steam update; never evaluate untrusted JS."""
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    if digest not in INSPECTED_UI_BUILDS:
        raise AuditError('Unreviewed Steam UI build; inspect its capability gates before use')
    return digest


def attribute_records(text):
    records = []
    current = None
    version = None
    for number, line in enumerate(text.splitlines(), 1):
        client = CLIENT.fullmatch(line)
        if client:
            version = client[2]
        header = HEADER.fullmatch(line)
        if header:
            current = {'timestamp': header[1], 'index': int(header[2]),
                       'line': number, 'client_version': version, 'fields': {}}
            records.append(current)
        elif line.startswith('['):
            current = None
        elif current is not None and line.strip():
            key, separator, value = line.strip().partition(': ')
            if key not in ('Type', 'ProductID', 'Serial', 'Capabilities'):
                continue
            if not separator or key in current['fields']:
                raise AuditError('Malformed or duplicate controller attribute')
            current['fields'][key] = value
    return records


def classify(mapping_text, ui_log, guid, controller_index, ui_sha256=UI_SHA256):
    """Inspected-build gate model; CLI additionally verifies the source hash.

    Require the selected mapping and attribute block to have exactly the same
    logged second. This is saved-log correlation, not current device identity.
    Serial prefix is a family check only; never emit the local serial string.
    The selected log version must belong to the supplied inspected hash. The
    default preserves the original build contract for existing offline callers.
    """
    client_version = INSPECTED_UI_BUILDS.get(ui_sha256)
    if client_version is None:
        raise AuditError('Unreviewed Steam UI build; inspect its capability gates before use')
    mapping = audit_text(mapping_text, guid)
    number = mapping['selection']['last_matching_line']
    line = mapping_text.splitlines()[number - 1]
    timestamp = re.match(TIMESTAMP, line)
    if not timestamp:
        raise AuditError('Selected mapping has no timestamp for attribute correlation')
    records = [r for r in attribute_records(ui_log)
               if r['timestamp'] == timestamp[1] and r['index'] == controller_index]
    if len(records) != 1:
        raise AuditError('Need exactly one attribute record for selected controller and mapping timestamp')
    record = records[0]
    if record['client_version'] != client_version:
        raise AuditError('Attribute log client version does not match the inspected UI build')
    fields = record['fields']
    if set(fields) != {'Type', 'ProductID', 'Serial', 'Capabilities'}:
        raise AuditError('Incomplete controller attributes')
    pid = native_guid_pid(mapping['guid'])
    if (fields['ProductID'] != str(pid) or
            not re.fullmatch(rf'3537-{pid:04x}-[a-zA-Z0-9_-]+', fields['Serial'])):
        raise AuditError('Attribute record is not the expected native GameSir family')
    # Only Type 30 has been reviewed. Joy-Con exclusions and other types need
    # their own source review; no inference from an Elite-looking device name.
    if fields['Type'] != '30':
        raise AuditError('Unreviewed Steam controller classification')
    if not re.fullmatch(r'[0-9a-fA-F]{16}', fields['Capabilities']):
        raise AuditError('Expected a 64-bit hexadecimal capability value')
    caps = int(fields['Capabilities'], 16)
    observed = dict(part.split(':', 1) for part in mapping['observed_mapping'].split(',')[2:] if part)
    # 109c retains its established output labels. For 105e only SDL field
    # identities are established offline; do not imply physical label proof.
    bindings = {label if pid == 0x109c else field: observed.get(field) == binding
                for label, (field, binding) in PADDLES.items()}
    gates = {'LeftGrip_Upper': caps & (GRIPS | UPPER_GRIPS) == (GRIPS | UPPER_GRIPS),
             'RightGrip_Upper': caps & (GRIPS | UPPER_GRIPS) == (GRIPS | UPPER_GRIPS),
             'LeftGrip': bool(caps & GRIPS), 'RightGrip': bool(caps & GRIPS)}
    mapped = all(bindings.values())
    capable = all(gates.values())
    status = ('mapping_and_ui_capability_gap' if not mapped and not capable else
              'mapping_gap' if not mapped else
              'mapped_paddles_not_advertised_to_ui' if not capable else
              'mapping_and_capability_gate_ready_live_acceptance_required')
    result = {
        'schema_version': 1, 'scope': 'saved_logs_and_inspected_static_ui',
        'status': status, 'timestamp': timestamp[1],
        'controller_index': controller_index, 'controller_type': 30,
        'client_version': record['client_version'],
        'mapping_line': number, 'attribute_line': record['line'],
        'guid': mapping['guid'], 'capabilities_hex': f'{caps:016x}',
        'grips': bool(caps & GRIPS), 'upper_grips': bool(caps & UPPER_GRIPS),
        'paddle_bindings_match': bindings, 'ui_capability_gate': gates,
        'standard_bindings_unchanged': mapping['standard_bindings_unchanged'],
        'raw_button_reception': 'not_measured', 'steam_editor_acceptance': 'not_measured',
        'game_rebinding': 'not_measured', 'system_changes': False,
        'limitations': [
            'Private UI bits are build-specific observations, never a configuration interface',
            'Matching timestamps identify saved log records, not a live device or unique dongle',
            'Capability gates alone do not prove input delivery or editor acceptance',
            'Classic XInput does not gain four button fields',
        ],
    }
    if pid == 0x105e:
        result['physical_paddle_labels'] = 'unconfirmed'
        result['limitations'].append(
            '105e paddle matches describe SDL fields only; physical L4/R4/L5/R5 labels remain unconfirmed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping-log', required=True)
    parser.add_argument('--ui-log', required=True)
    parser.add_argument('--ui-bundle', required=True, help='Read-only installed JS file; never executed')
    parser.add_argument('--guid', required=True)
    parser.add_argument('--controller-index', required=True, type=int)
    args = parser.parse_args()
    try:
        if args.controller_index < 0:
            raise AuditError('Controller index must be non-negative')
        digest = verify_ui_source(read_regular_log(args.ui_bundle, MAX_UI_BYTES))
        result = classify(read_regular_log(args.mapping_log), read_regular_log(args.ui_log),
                          args.guid, args.controller_index, ui_sha256=digest)
        result['ui_sha256'] = digest
    except AuditError as error:
        print(json.dumps({'schema_version': 1, 'ok': False, 'error': str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
