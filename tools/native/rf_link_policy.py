# SPDX-License-Identifier: GPL-2.0-only
"""Pure saved-metadata policy; no host reads, processes, devices or commands."""
import copy
import math
import re

SCOPE = 'passive-rf-109c-xpad-90'
DURATION, OUTER_TIMEOUT = 90, 120
GAP_SECONDS, PENDING_SECONDS, MAX_EPOCHS = 5, 2, 4


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_target(target):
    require(isinstance(target, dict) and set(target) == {
        'port', 'busnum', 'devnum', 'devpath', 'vid', 'pid', 'interfaces',
        'sysfs_identity', 'boot_id'}, 'Exact cached RF target required')
    require((target['port'], target['busnum'], target['devpath'], target['vid'], target['pid']) ==
            ('8-6', '8', '6', '3537', '109c'), 'RF test baseline must be standard109c at the approved bus8/port8-6')
    require(isinstance(target['devnum'], str) and re.fullmatch(r'[1-9][0-9]{0,2}', target['devnum'])
            and int(target['devnum']) <= 127, 'Current USB address required')
    require(isinstance(target['boot_id'], str) and re.fullmatch(
        r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', target['boot_id']), 'Current boot required')
    require(target['interfaces'] == {
        '0': {'driver': 'xpad', 'endpoints': [2, 130]},
        '1': {'driver': None, 'endpoints': []}}, 'Exact109c xpad/interface1 baseline required')
    anchor = target['sysfs_identity']
    require(isinstance(anchor, dict) and set(anchor) == {
        'st_dev', 'st_ino', 'parent_st_dev', 'parent_st_ino'} and
        all(type(v) is int and v >= (1 if k.endswith('ino') else 0) for k, v in anchor.items()),
        'Device and parent lifetime anchors required')
    return target


class Tracker:
    """Observe distinct epochs, never adopt control or replay initialization."""
    def __init__(self, target):
        self.target = copy.deepcopy(validate_target(target))
        self.last_time = None
        self.unknown_since = None
        self.unknown_limit = None
        self.epochs = []
        self.current = None
        self.failed = False

    def observe(self, snapshot, now, *, initial=False, final=False):
        require(not self.failed, 'RF observation is terminal; no retry')
        try:
            return self._observe(snapshot, now, initial=initial, final=final)
        except (ValueError, KeyError, TypeError):
            self.failed = True
            raise

    def _observe(self, snapshot, now, *, initial, final):
        require(type(initial) is bool and type(final) is bool and not (initial and final),
                'Explicit initial/final observation boundary required')
        require(bool(self.epochs) or initial, 'First observation must be initial')
        require(type(now) in (int, float) and math.isfinite(now) and now >= 0,
                'Finite monotonic observation time required')
        require(self.last_time is None or now >= self.last_time, 'RF observation clock regressed')
        self.last_time = now
        require(isinstance(snapshot, dict) and set(snapshot) == {
            'observation', 'boot_id', 'parent', 'manager_paused_empty', 'input_consumer_open',
            'identity', 'reason'}, 'Invalid RF snapshot schema')
        require(snapshot['boot_id'] == self.target['boot_id'], 'Host boot changed')
        expected_parent = {k: v for k, v in self.target['sysfs_identity'].items() if k.startswith('parent_')}
        require(snapshot['parent'] == expected_parent, 'Receiver parent lifetime changed')
        require(snapshot['manager_paused_empty'] is True, 'Native management pause/empty ownership lost')
        observation = snapshot['observation']
        require(observation in ('present', 'absent', 'pending'), 'Unknown RF observation kind')
        require(type(snapshot['input_consumer_open']) is bool, 'Consumer observation must be explicit')
        require(isinstance(snapshot['reason'], str), 'Explicit observation reason required')
        if observation != 'present':
            require(not initial and not final and self.epochs, 'Complete target required at capture boundaries')
            require(snapshot['identity'] is None, 'Unknown observation cannot carry a trusted instance')
            limit = GAP_SECONDS if observation == 'absent' else PENDING_SECONDS
            if self.unknown_since is None:
                self.unknown_since, self.unknown_limit = now, limit
            else:
                self.unknown_limit = min(self.unknown_limit, limit)
            require(now - self.unknown_since <= self.unknown_limit, 'RF metadata/gap observation deadline exceeded')
            self.current = None
            return {'observation': observation, 'epoch': None, 'radio_connected_proven': False}
        require(snapshot['input_consumer_open'], 'No ordinary input consumer for exact current IF0')
        identity = snapshot['identity']
        require(isinstance(identity, dict) and set(identity) == set(self.target), 'Complete epoch identity required')
        require((identity['port'], identity['busnum'], identity['devpath'], identity['vid']) ==
                ('8-6', '8', '6', '3537'), 'Foreign receiver topology/VID')
        require(identity['boot_id'] == self.target['boot_id'], 'Epoch boot differs')
        require(identity['pid'] in ('109c', '100a'), 'Unsupported replacement PID')
        require(isinstance(identity['devnum'], str) and re.fullmatch(r'[1-9][0-9]{0,2}', identity['devnum'])
                and int(identity['devnum']) <= 127, 'Invalid epoch address')
        anchors = identity['sysfs_identity']
        require(isinstance(anchors, dict) and set(anchors) == set(self.target['sysfs_identity']) and
                all(type(v) is int and v >= (1 if k.endswith('ino') else 0) for k, v in anchors.items()),
                'Complete epoch lifetime required')
        require({k: v for k, v in anchors.items() if k.startswith('parent_')} == expected_parent,
                'Epoch parent lifetime differs')
        interfaces = {'0': {'driver': 'xpad', 'endpoints': [2, 130]},
                      '1': {'driver': None, 'endpoints': []} if identity['pid'] == '109c'
                      else {'driver': 'usbhid', 'endpoints': [4, 132]}}
        require(identity['interfaces'] == interfaces, 'Replacement binding or endpoint mismatch')
        if initial:
            require(not self.epochs and identity == self.target, 'Initial instance differs from approved manifest')
        if self.unknown_since is not None:
            require(now - self.unknown_since <= self.unknown_limit, 'Late metadata cannot erase gap timeout')
        self.unknown_since = self.unknown_limit = None
        # An inode cannot silently change product/address; a distinct lifetime
        # may legitimately reuse an address. Returning to an old epoch is unsafe.
        object_key = (anchors['st_dev'], anchors['st_ino'])
        if self.epochs and object_key == self.epochs[-1]['object_key']:
            require(identity == self.epochs[-1]['identity'], 'Same USB object changed identity')
        else:
            require(all(e['object_key'] != object_key for e in self.epochs), 'Retired USB epoch reappeared')
            require(len(self.epochs) < MAX_EPOCHS, 'Too many enumeration epochs in one approved run')
            self.epochs.append({'object_key': object_key, 'first_seen_monotonic': now,
                                'identity': copy.deepcopy(identity)})
        self.current = len(self.epochs) - 1
        return {'observation': 'present', 'epoch': self.current, 'radio_connected_proven': False}
