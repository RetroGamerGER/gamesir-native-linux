#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Optional session integration: source this before the desktop starts.
# No device access, process startup, Steam file edits or shell evaluation of
# mapping data. This hint also reaches other SDL applications in the session,
# using the native GameSir GUIDs. The 109c mapping is hardware-confirmed; the
# 105e GUID is derived and tested offline from saved native input metadata.
# ZZZ physical paddle labels and Steam behavior still require a real test.
# SDL may also match other firmware versions; this is not a firmware-version
# or individual-device safety gate. Explicit crc:3545 restricts both added
# mappings to the native name CRC rather than matching a differently named xpad.
# Preserve any existing USB/evdev mapping for each supported PID independently,
# including a conflicting one with a different/zero name CRC or version.
# SDL normalizes CRC and has a
# version fallback, so exact GUID-string comparison would silently override
# some effective user mappings. This conservative guard does not parse fields;
# installation must report such conflicts instead of silently overriding them.
# A nonempty SDL_GAMECONTROLLERCONFIG_FILE disables this addition entirely:
# it may contain a user mapping that the session hint would otherwise override.
# This source-only helper never reads configuration or unsets other hints.

if [ "${GAMESIR_NATIVE_STEAM_DISABLE-}" != 1 ] &&
   [ -z "${SDL_GAMECONTROLLERCONFIG_FILE-}" ]; then
    case "
${SDL_GAMECONTROLLERCONFIG-}" in
        *"
0300"[[:xdigit:]][[:xdigit:]][[:xdigit:]][[:xdigit:]]"373500009"[cC]"100000"[[:xdigit:]][[:xdigit:]][[:xdigit:]][[:xdigit:]]"0000,"*)
            ;;
        *)
            SDL_GAMECONTROLLERCONFIG="${SDL_GAMECONTROLLERCONFIG:+${SDL_GAMECONTROLLERCONFIG}
}03004535373500009c10000053010000,GameSir G7 Pro,a:b0,b:b1,x:b2,y:b3,back:b6,guide:b8,start:b7,leftstick:b9,rightstick:b10,leftshoulder:b4,rightshoulder:b5,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,misc1:b16,leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,paddle1:b12,paddle2:b11,paddle3:b14,paddle4:b13,platform:Linux,crc:3545,"
            ;;
    esac
    case "
${SDL_GAMECONTROLLERCONFIG-}" in
        *"
0300"[[:xdigit:]][[:xdigit:]][[:xdigit:]][[:xdigit:]]"373500005"[eE]"100000"[[:xdigit:]][[:xdigit:]][[:xdigit:]][[:xdigit:]]"0000,"*)
            ;;
        *)
            SDL_GAMECONTROLLERCONFIG="${SDL_GAMECONTROLLERCONFIG:+${SDL_GAMECONTROLLERCONFIG}
}03004535373500005e10000007060000,GameSir G7 Pro,a:b0,b:b1,x:b2,y:b3,back:b6,guide:b8,start:b7,leftstick:b9,rightstick:b10,leftshoulder:b4,rightshoulder:b5,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,misc1:b16,leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,paddle1:b12,paddle2:b11,paddle3:b14,paddle4:b13,platform:Linux,crc:3545,"
            ;;
    esac
    export SDL_GAMECONTROLLERCONFIG
fi
