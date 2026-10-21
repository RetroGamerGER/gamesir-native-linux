# SPDX-License-Identifier: GPL-2.0-only
"""Strict separate package protocol. No commands, filenames or permissions tokens."""
from dataclasses import asdict, dataclass
import json
import math
import secrets
import struct

from artifacts import BackendError, COMPONENTS, MAX_PACKAGE, HEX
from backend import HostEvidence, Outcome, PLAN_LIFETIME, Plan, Request

HEADER_LIMIT = 1024 * 1024
TOTAL_LIMIT = HEADER_LIMIT + 4 * MAX_PACKAGE + 4
EXECUTOR = '/usr/lib/gamesir-control-center/package-executor/execute'
ACTION = 'io.github.RetroGamerGER.gamesir_native.control_center.packages'
POLICY = '/usr/share/polkit-1/actions/' + ACTION + '.policy'
ARGV = ('/usr/bin/pkexec', '--disable-internal-agent', EXECUTOR)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackendError('duplicate_package_field')
        result[key] = value
    return result


def decode(data):
    if type(data) is not bytes or not 0 < len(data) <= HEADER_LIMIT:
        raise BackendError('package_message_limit')
    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise BackendError('invalid_package_json') from None


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


@dataclass(frozen=True)
class PackageMessage:
    plan: Plan
    request_id: str
    release_catalog: bytes | None = None

    @classmethod
    def create(cls, plan, release_catalog=None):
        return cls(plan, secrets.token_hex(32), release_catalog)

    def chunks(self):
        if self.plan.purpose != 'packages':
            raise BackendError('package_plan_required')
        value = {'schema': 2, 'mode': 'packages', 'request_id': self.request_id,
                 'plan_id': self.plan.confirmation_id, 'expires_at': self.plan.expires_at,
                 'request': {'schema': 1, 'operation': self.plan.request.operation,
                             'components': list(self.plan.request.components)},
                 'host': asdict(self.plan.host),
                 'artifacts': [{'component': a.review.component, 'sha256': a.review.digest,
                                'size': len(a.data)} for a in self.plan.artifacts]}
        if self.release_catalog is not None:
            from package_catalog import CATALOG_LIMIT
            if type(self.release_catalog) is not bytes or not 0 < len(self.release_catalog) <= CATALOG_LIMIT:
                raise BackendError('release_catalog_limit')
            try: value['release_catalog'] = self.release_catalog.decode('ascii')
            except UnicodeError: raise BackendError('invalid_release_envelope') from None
            value['schema'] = 3
        header = encode(value)
        if len(header) > HEADER_LIMIT:
            raise BackendError('package_message_limit')
        yield struct.pack('!I', len(header))
        yield header
        for artifact in self.plan.artifacts:
            yield artifact.data  # Exact verified bytes, never a mutable client path.


def parse_message(read_exact, trust, *, resolver=None):
    prefix = read_exact(4)
    if len(prefix) != 4:
        raise BackendError('incomplete_package_message')
    size = struct.unpack('!I', prefix)[0]
    if not 0 < size <= HEADER_LIMIT:
        raise BackendError('package_message_limit')
    value = decode(read_exact(size))
    base = {'schema', 'mode', 'request_id', 'plan_id', 'expires_at', 'request', 'host', 'artifacts'}
    if (type(value) is not dict or type(value.get('schema')) is not int
            or value['schema'] not in (2, 3)
            or set(value) != (base | {'release_catalog'} if value['schema'] == 3 else base)
            or value['mode'] != 'packages'
            or any(type(value[k]) is not str or not HEX.fullmatch(value[k])
                   for k in ('request_id', 'plan_id'))
            or type(value['expires_at']) not in (int, float) or not math.isfinite(value['expires_at'])
            or type(value['host']) is not dict
            or set(value['host']) != set(HostEvidence.__dataclass_fields__)
            or type(value['artifacts']) is not list or len(value['artifacts']) > 4):
        raise BackendError('invalid_package_message')
    request = Request.parse(value['request'])
    envelope = None
    if value['schema'] == 3:
        from package_catalog import CATALOG_LIMIT
        if (type(value['release_catalog']) is not str or not value['release_catalog'].isascii()
                or not 0 < len(value['release_catalog']) <= CATALOG_LIMIT):
            raise BackendError('release_catalog_limit')
        envelope = value['release_catalog'].encode('ascii')
    if envelope is not None or trust.release_policy is not None:
        if resolver is None: raise BackendError('release_resolver_required')
        trust = resolver(envelope, request.operation)
    host_data = dict(value['host'])
    for key in ('installed', 'missing_dependencies'):
        if type(host_data[key]) is not list:
            raise BackendError('invalid_host_evidence')
    if any(type(row) is not list for row in host_data['installed']):
        raise BackendError('invalid_host_evidence')
    host_data['installed'] = tuple(tuple(row) for row in host_data['installed'])
    host_data['missing_dependencies'] = tuple(host_data['missing_dependencies'])
    host = HostEvidence(**host_data)
    host.validate(value['expires_at'] - PLAN_LIFETIME)
    artifacts, seen = [], set()
    for row in value['artifacts']:
        if (type(row) is not dict or set(row) != {'component', 'sha256', 'size'}
                or type(row['component']) is not str or row['component'] not in request.components
                or row['component'] in seen or type(row['size']) is not int
                or not 0 < row['size'] <= MAX_PACKAGE
                or type(row['sha256']) is not str or not HEX.fullmatch(row['sha256'])):
            raise BackendError('invalid_package_artifact')
        seen.add(row['component'])
        # Declared identity must be in the HELPER's installed trust catalog
        # before accepting payload bytes. It is not supplied by the GUI.
        record = next((r for r in trust.catalog.records
                       if r.component == row['component'] and r.digest == row['sha256']
                       and r.size == row['size']), None)
        if record is None:
            raise BackendError('no_reviewed_binary')
        artifacts.append(trust.catalog.verify(row['component'], read_exact(row['size'])))
    if (request.operation == 'remove' and artifacts or request.operation == 'install'
            and tuple(a.review.component for a in artifacts) != request.components):
        raise BackendError('package_artifact_selection_mismatch')
    plan = Plan(request, host, tuple(artifacts), value['expires_at'], purpose='packages')
    if plan.confirmation_id != value['plan_id']:
        raise BackendError('confirmation_mismatch')
    return PackageMessage(plan, value['request_id'], envelope)


def receipt(message, outcome):
    return encode({'schema': 2, 'request_id': message.request_id,
                   'plan_id': message.plan.confirmation_id, 'outcome': asdict(outcome)})


def parse_receipt(data, message):
    value = decode(data)
    if (type(value) is not dict or set(value) != {'schema', 'request_id', 'plan_id', 'outcome'}
            or type(value['schema']) is not int or value['schema'] != 2
            or value['request_id'] != message.request_id
            or value['plan_id'] != message.plan.confirmation_id
            or type(value['outcome']) is not dict
            or set(value['outcome']) != set(Outcome.__dataclass_fields__)):
        raise BackendError('invalid_package_receipt')
    row = value['outcome']
    if (row['state'] not in ('verified_success', 'blocked', 'failed', 'uncertain')
            or type(row['changes_possible']) is not bool
            or any(type(row[k]) is not str or len(row[k]) > 100
                   or any(c not in 'abcdefghijklmnopqrstuvwxyz_0123456789' for c in row[k])
                   for k in ('stage', 'error'))
            or row['state'] == 'verified_success' and (row['error'] or not row['changes_possible']
                                                       or row['stage'] != 'privileged_postcheck')
            or row['state'] in ('failed', 'uncertain') and not row['changes_possible']
            or row['state'] == 'blocked' and (not row['error'] or row['changes_possible'])):
        raise BackendError('invalid_package_receipt')
    return Outcome(**row)
