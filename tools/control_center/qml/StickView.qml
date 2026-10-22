// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property var stick
    required property var texts
    required property string label
    required property string phase
    property bool simulated: true
    readonly property string statusText: phase === "completed" ? (simulated ? texts.cal_stick_done : texts.cal_live_stick_done)
                                         : phase === "lost" || phase === "cancelled" || phase === "error"
                                           ? texts.cal_stick_stopped
                                         : stick.ready ? texts.cal_ready_stick : texts.cal_waiting
    spacing: 10
    Accessible.role: Accessible.Indicator
    Accessible.name: label + ": " + texts.cal_coverage + " " + stick.coverage + "% · "
                     + statusText

    Copy { Layout.alignment: Qt.AlignHCenter; text: root.label; font.bold: true; font.pixelSize: 16 }
    Item {
        id: plot
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(width, 240)
        readonly property real diameter: Math.max(0, Math.min(width, height) - 20)
        readonly property real radius: diameter / 2
        // Preserve direction while keeping square-axis corner values in the disc.
        readonly property real magnitude: Math.max(1, Math.hypot(root.stick.x, root.stick.y))
        Rectangle {
            width: plot.diameter; height: width; radius: width / 2
            anchors.centerIn: parent; color: "#10191c"
            border.color: "#2e4147"
        }
        Rectangle { anchors.centerIn: parent; width: plot.diameter - 22; height: 1; color: "#293b40" }
        Rectangle { anchors.centerIn: parent; width: 1; height: plot.diameter - 22; color: "#293b40" }
        Canvas {
            id: ring
            anchors.fill: parent
            property var sectors: root.stick.sectors
            onSectorsChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                const count = sectors.length
                ctx.lineWidth = 7
                ctx.lineCap = "round"
                for (let i = 0; i < count; ++i) {
                    ctx.strokeStyle = sectors[i] ? "#8ddbb9" : "#35434b"
                    ctx.beginPath()
                    // Model +Y points up; the canvas +Y points down.
                    ctx.arc(width / 2, height / 2, plot.radius,
                            -(i + 0.91) * Math.PI * 2 / count,
                            -(i + 0.09) * Math.PI * 2 / count)
                    ctx.stroke()
                }
            }
        }
        Rectangle {
            width: 18; height: 18; radius: 9
            x: plot.width / 2 + root.stick.x / plot.magnitude * (plot.radius - 12) - width / 2
            y: plot.height / 2 - root.stick.y / plot.magnitude * (plot.radius - 12) - height / 2
            color: "#c5f4df"; border.width: 2; border.color: "#6bb294"
        }
    }
    Copy {
        Layout.alignment: Qt.AlignHCenter
        text: root.texts.cal_coverage + " · " + root.stick.coverage + "%"
        color: "#a6d8c2"; font.pixelSize: 13
    }
    Copy {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        text: root.statusText
        color: root.stick.ready ? "#a6d8c2" : "#9aa5af"; font.pixelSize: 12
    }
}
