#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Plasma sources this before starting the desktop and its applications.
# Installation/removal does not change an already running session.
if [ -f /usr/share/gamesir-native-steam/session.sh ] &&
   [ -r /usr/share/gamesir-native-steam/session.sh ]; then
    . /usr/share/gamesir-native-steam/session.sh
fi
