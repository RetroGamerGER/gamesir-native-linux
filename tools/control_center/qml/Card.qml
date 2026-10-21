// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    default property alias contents: body.data
    property real inset: 20
    color: "#181c20"
    border.color: "#2b3036"
    radius: 16
    implicitHeight: body.implicitHeight + inset * 2
    ColumnLayout {
        id: body
        x: root.inset
        y: root.inset
        width: Math.max(0, root.width - root.inset * 2)
        spacing: 12
    }
}
