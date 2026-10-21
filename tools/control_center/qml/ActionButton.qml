// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import QtQuick.Controls.Basic

Button {
    id: root
    property bool primary: false
    property string iconKind: ""
    property bool compact: false
    implicitHeight: compact ? 34 : 44
    implicitWidth: label.implicitWidth + (iconKind ? 60 : 32)
    leftPadding: 16
    rightPadding: 16
    topPadding: 8
    bottomPadding: 8
    activeFocusOnTab: true
    hoverEnabled: true
    Accessible.name: text
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()
    contentItem: Item {
        implicitWidth: label.implicitWidth + (root.iconKind ? 28 : 0)
        implicitHeight: label.implicitHeight
        Copy {
            id: label
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: root.iconKind ? -12 : 0
            text: root.text
            color: !root.enabled ? "#69737d" : root.primary ? "#10241e" : "#e0e5e8"
            font.pixelSize: 13
            font.bold: root.primary
            wrapMode: Text.NoWrap
        }
        Icon {
            visible: !!root.iconKind
            kind: root.iconKind
            width: 15; height: 15
            x: label.x + label.width + 10
            anchors.verticalCenter: parent.verticalCenter
            ink: label.color
        }
    }
    background: Rectangle {
        radius: root.compact ? 9 : 11
        color: !root.enabled ? "#23292e" : root.down ? "#8bc7b0" : root.primary ? (root.hovered ? "#bee8d7" : "#a6d8c2") : (root.hovered ? "#2b333a" : "#20262b")
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? "#c4f5e0" : root.primary && root.enabled ? "#a6d8c2" : "#384149"
    }
}
