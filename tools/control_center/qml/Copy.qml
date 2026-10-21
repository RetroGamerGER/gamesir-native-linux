// SPDX-License-Identifier: GPL-2.0-only
import QtQuick

Text {
    textFormat: Text.PlainText
    color: "#e8e9ed"
    font.family: "DejaVu Sans"
    font.pixelSize: 13
    wrapMode: Text.WordWrap
    lineHeight: 1.18
    Accessible.role: Accessible.StaticText
    Accessible.name: text
}
