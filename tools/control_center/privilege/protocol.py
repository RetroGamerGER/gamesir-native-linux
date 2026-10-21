# SPDX-License-Identifier: GPL-2.0-only
"""Bounded authorization-only wire data; acknowledgements are not credentials."""
from dataclasses import dataclass
import json
import re

COMPONENTS = ('core', 'steam', 'gamescope', 'bridge')
LIMIT = 2048
HEX = re.compile(r'[0-9a-f]{64}\Z')
MODE = 'authorize_only'
ACTION = 'io.github.RetroGamerGER.gamesir_native.control_center.authorize'
BASE = '/usr/lib/gamesir-control-center'
HELPER = BASE + '/authorize'
POLICY = '/usr/share/polkit-1/actions/' + ACTION + '.policy'
FILES = (HELPER, BASE + '/privilege/__init__.py', BASE + '/privilege/protocol.py',
         BASE + '/privilege/helper.py', POLICY)
ARGV = ('/usr/bin/pkexec', '--disable-internal-agent', HELPER)


class AuthorizationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def encode(value):
    data = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
    if len(data) > LIMIT:
        raise AuthorizationError('authorization_message_limit')
    return data


def decode(data):
    if type(data) is not bytes or not 0 < len(data) <= LIMIT:
        raise AuthorizationError('authorization_message_limit')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuthorizationError('duplicate_authorization_field')
            result[key] = value
        return result
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=unique)
    except AuthorizationError:
        raise
    except (ValueError, UnicodeError, RecursionError) as error:
        raise AuthorizationError('invalid_authorization_json') from error
    if type(value) is not dict:
        raise AuthorizationError('invalid_authorization_message')
    return value


@dataclass(frozen=True)
class Probe:
    operation: str
    components: tuple
    plan_id: str
    request_id: str

    def message(self):
        return {'schema': 1, 'mode': MODE, 'operation': self.operation,
                'components': list(self.components), 'plan_id': self.plan_id,
                'request_id': self.request_id}

    def wire(self):
        data = encode(self.message())
        Probe.parse(data)
        return data

    @classmethod
    def parse(cls, data):
        value = decode(data)
        if (set(value) != {'schema', 'mode', 'operation', 'components', 'plan_id', 'request_id'}
                or type(value['schema']) is not int or value['schema'] != 1
                or value['mode'] != MODE or value['operation'] not in ('install', 'remove')
                or type(value['components']) is not list or not 0 < len(value['components']) <= 4
                or any(type(c) is not str or c not in COMPONENTS for c in value['components'])
                or len(set(value['components'])) != len(value['components'])
                or any(type(value[k]) is not str or not HEX.fullmatch(value[k])
                       for k in ('plan_id', 'request_id'))):
            raise AuthorizationError('invalid_authorization_request')
        return cls(value['operation'], tuple(value['components']), value['plan_id'], value['request_id'])


def acknowledgement(probe):
    return encode({'schema': 1, 'mode': MODE, 'plan_id': probe.plan_id,
                   'request_id': probe.request_id, 'result': 'authorized_only', 'executed': False})


def verify_acknowledgement(data, probe):
    # Exact response: no implicit installed/success state or reusable token.
    value = decode(data)
    expected = decode(acknowledgement(probe))
    if (value != expected or type(value.get('schema')) is not int
            or value.get('executed') is not False):
        raise AuthorizationError('authorization_reply_mismatch')
