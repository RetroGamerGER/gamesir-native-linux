# SPDX-License-Identifier: GPL-2.0-only
"""Small, versioned calibration-only pipe protocol. No paths or raw commands."""
import json
import re

BASE = '/usr/lib/gamesir-control-center/tmr-maintenance'
HELPER = BASE + '/execute'
ACTION = 'io.github.RetroGamerGER.gamesir_native.control_center.tmr'
POLICY = '/usr/share/polkit-1/actions/' + ACTION + '.policy'
ARGV = ('/usr/bin/pkexec', '--disable-internal-agent', HELPER)
MODULES = ('tmr_wire.py', 'tmr_channel.py', 'tmr_helper.py', 'calibration_controller.py',
           'calibration_protocol.py', 'stick_calibration.py')
FILES = (HELPER, POLICY, *(BASE + '/' + name for name in MODULES))
LIMIT = 16384
PORT = re.compile(r'[0-9]{1,3}-[0-9]{1,3}(?:\.[0-9]{1,3}){0,6}\Z')


class TmrFailure(ValueError):
    pass


def encode(value):
    data = (json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n').encode('ascii')
    if len(data) > LIMIT:
        raise TmrFailure('message_limit')
    return data


def decode(data):
    if type(data) is not bytes or not 0 < len(data) <= LIMIT or not data.endswith(b'\n'):
        raise TmrFailure('invalid_message')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise TmrFailure('duplicate_field')
            result[key] = value
        return result
    try:
        value = json.loads(data, object_pairs_hook=unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(TmrFailure('nonfinite')))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise TmrFailure('invalid_message') from error
    if type(value) is not dict:
        raise TmrFailure('invalid_message')
    return value


def uint(value):
    return type(value) is int and 0 < value < 2**64


def target(value):
    if (type(value) is not dict or value.keys() != {'port', 'pid', 'port_token', 'instance_token'}
            or type(value['port']) is not str or not PORT.fullmatch(value['port'])
            or type(value['pid']) is not int or value['pid'] not in (0x109c, 0x105e)
            or not uint(value['port_token']) or not uint(value['instance_token'])):
        raise TmrFailure('invalid_target')
    return dict(value)


def request(data):
    value = decode(data)
    if (type(value.get('schema')) is not int or value['schema'] != 1
            or not uint(value.get('id')) or type(value.get('action')) is not str
            or value['action'] not in ('list', 'select', 'poll', 'prepare', 'finish', 'cancel')):
        raise TmrFailure('invalid_request')
    fields = {'schema', 'id', 'action'} | ({'target'} if value['action'] == 'select' else set())
    if value.keys() != fields:
        raise TmrFailure('invalid_fields')
    if 'target' in value:
        target(value['target'])
    return value
