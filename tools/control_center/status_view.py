# SPDX-License-Identifier: GPL-2.0-only
"""Translate metadata without promoting it to hardware readiness or activation."""
from status import Fact


DETAILS = (
    ('headers_label', 'headers'), ('compiler_label', 'compiler'),
    ('dependencies_label', 'dependencies'), ('dkms_label', 'dkms'),
    ('service_label', 'service'), ('autostart_label', 'autostart'),
    ('manager_details', 'manager'), ('steam_package', 'gamesir-native-steam'),
    ('gamescope_package', 'gamesir-native-steam-gamescope'),
    ('bridge_package', 'gamesir-native-trigger-bridge'),
)


def format_fact(fact, t):
    if fact.state == 'ok':
        return fact.value or t['fact_unknown']
    label = t.get('fact_' + fact.state, t['fact_unknown'])
    return label + (' · ' + fact.value if fact.value else '')


def present(snapshot, t, *, busy=False, failed=False, stale=False):
    facts = snapshot.facts if snapshot else {}
    fact = lambda name: facts.get(name, Fact())
    value = lambda name: format_fact(fact(name), t)
    details = [{'label': t[label], 'value': value(name)} for label, name in DETAILS]
    devices = [{'port': device.port, 'identity': format_fact(device.identity, t),
                'binding': format_fact(device.binding, t)} for device in snapshot.devices] if snapshot else []
    return {
        'installed': fact('gamesir-native-dkms').state == 'ok',
        'loaded': fact('module').state == 'loaded',
        'receiver': fact('receiver').state == 'present', 'connected': False,
        'supported': fact('support').state == 'ok', 'headers': fact('headers').state == 'match',
        'canInstall': False, 'canRemove': False,
        'notice': t['read_failed' if failed else 'read_collecting' if busy else 'read_notice'],
        'noticeWarning': failed or fact('headers').state in ('mismatch', 'missing'),
        'os': value('os') + ' · ' + value('architecture'), 'kernel': value('kernel'),
        'driver': value('gamesir-native-dkms'), 'module': value('module'),
        'manager': value('service'), 'dongle': value('receiver'),
        'controller': value('connection'),
        'requirements': t['reviewed_platform'] if fact('support').state == 'ok' else value('support'),
        'details': details, 'devices': devices,
        'sampleTime': snapshot.finished if snapshot else '',
        'sampleState': t['sample_stale' if stale else 'sample_fixed'],
    }
