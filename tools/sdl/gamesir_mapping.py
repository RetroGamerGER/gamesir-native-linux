#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Generate a native 109c/105e SDL evdev mapping; never open any device.

Use the target application's SDL evdev GUID or an explicitly identified offline
candidate. Native capabilities must be established separately: the GUID alone
does not prove the driver or button order. The physical L4/R4/L5/R5 labels for
105e remain unconfirmed; its paddle fields reuse the common native key order.
"""
import argparse
import re

NORMAL = (304, 305, 307, 308, 310, 311, 314, 315, 316, 317, 318)
PROFILES = {'native15': NORMAL + (704, 705, 706, 707),
            'alpha17': NORMAL + (704, 705, 706, 707, 708, 167)}
BUTTONS = {'a': 304, 'b': 305, 'x': 307, 'y': 308,
           'leftshoulder': 310, 'rightshoulder': 311,
           'back': 314, 'start': 315, 'guide': 316,
           'leftstick': 317, 'rightstick': 318,
           'paddle1': 705, 'paddle2': 704, 'paddle3': 707, 'paddle4': 706}
NATIVE_PIDS = frozenset((0x109c, 0x105e))


def native_guid_pid(guid):
    """Validate the exact USB/evdev identity allowlist and return its product ID."""
    if not re.fullmatch(r'[0-9a-fA-F]{32}', guid):
        raise ValueError('Expected a 32-digit SDL GUID, not a USB address')
    value = bytes.fromhex(guid)
    # SDL Linux USB GUID vendor/product fields are little endian at offsets4/8.
    pid = int.from_bytes(value[8:10], 'little')
    if (int.from_bytes(value[0:2], 'little') != 3 or
            int.from_bytes(value[4:6], 'little') != 0x3537 or pid not in NATIVE_PIDS):
        raise ValueError('Only native USB 3537:109c/105e evdev GUIDs are supported; never remap xpad100a or 1022')
    if value[14:16] != b'\0\0':
        raise ValueError('Expected the Linux evdev backend, not HIDAPI, virtual or XInput GUIDs')
    return pid


def mapping(guid, profile='alpha17'):
    native_guid_pid(guid)
    if profile not in PROFILES:
        raise ValueError('Unknown native capability profile')
    keys = PROFILES[profile]
    # SDL ConfigJoystick enumerates >= BTN_JOYSTICK first, then lower keycodes.
    order = sorted(k for k in keys if k >= 0x120) + sorted(k for k in keys if k < 0x120)
    fields = [guid.lower(), 'GameSir G7 Pro']
    fields += [f'{name}:b{order.index(code)}' for name, code in BUTTONS.items()]
    if profile == 'alpha17':
        fields += [f'misc1:b{order.index(167)}', f'misc2:b{order.index(708)}']
    fields += ['leftx:a0', 'lefty:a1', 'rightx:a3', 'righty:a4',
               'lefttrigger:a2', 'righttrigger:a5', 'dpup:h0.1', 'dpdown:h0.4',
               'dpleft:h0.8', 'dpright:h0.2', 'platform:Linux']
    return ','.join(fields) + ','


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guid', required=True, help='GUID read by the target app SDL evdev backend')
    parser.add_argument('--profile', choices=PROFILES, default='alpha17')
    args = parser.parse_args()
    try:
        print(mapping(args.guid, args.profile))
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
