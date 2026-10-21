// SPDX-License-Identifier: GPL-2.0-only
import QtQuick

Canvas {
    id: root
    property string kind: "controller"
    property color ink: "#b9c1c9"
    implicitWidth: 24
    implicitHeight: 24
    onInkChanged: requestPaint()
    onKindChanged: requestPaint()
    onPaint: {
        const c = getContext("2d")
        c.reset()
        c.scale(width / 24, height / 24)
        c.strokeStyle = ink
        c.lineWidth = 1.6
        c.lineCap = "round"
        c.lineJoin = "round"
        c.beginPath()
        if (kind === "controller") {
            c.moveTo(7, 6); c.lineTo(17, 6)
            c.bezierCurveTo(20, 6, 20, 9, 21, 16)
            c.bezierCurveTo(22, 21, 18, 20, 16, 16)
            c.lineTo(8, 16); c.bezierCurveTo(6, 20, 2, 21, 3, 16)
            c.bezierCurveTo(4, 9, 4, 6, 7, 6)
            c.moveTo(8, 9); c.lineTo(8, 13); c.moveTo(6, 11); c.lineTo(10, 11)
            c.moveTo(15, 10); c.lineTo(15.1, 10); c.moveTo(18, 12); c.lineTo(18.1, 12)
        } else if (kind === "download") {
            c.moveTo(12, 3); c.lineTo(12, 15); c.moveTo(8, 11); c.lineTo(12, 15); c.lineTo(16, 11)
            c.moveTo(4, 15); c.lineTo(4, 20); c.lineTo(20, 20); c.lineTo(20, 15)
        } else if (kind === "external") {
            c.moveTo(14, 4); c.lineTo(20, 4); c.lineTo(20, 10); c.moveTo(20, 4); c.lineTo(10, 14)
            c.moveTo(10, 5); c.lineTo(4, 5); c.lineTo(4, 20); c.lineTo(19, 20); c.lineTo(19, 14)
        } else if (kind === "sliders") {
            c.moveTo(4, 6); c.lineTo(20, 6); c.moveTo(4, 12); c.lineTo(20, 12); c.moveTo(4, 18); c.lineTo(20, 18)
            c.moveTo(8, 3); c.lineTo(8, 9); c.moveTo(16, 9); c.lineTo(16, 15); c.moveTo(10, 15); c.lineTo(10, 21)
        } else if (kind === "update") {
            c.arc(12, 12, 8, 0.4, 5.4)
            c.moveTo(15, 4); c.lineTo(19, 6); c.lineTo(20, 2)
        } else if (kind === "chip") {
            c.rect(6, 6, 12, 12)
            for (let i = 8; i <= 16; i += 4) {
                c.moveTo(i, 3); c.lineTo(i, 6); c.moveTo(i, 18); c.lineTo(i, 21)
                c.moveTo(3, i); c.lineTo(6, i); c.moveTo(18, i); c.lineTo(21, i)
            }
        } else if (kind === "shield") {
            c.moveTo(12, 2); c.lineTo(20, 6); c.lineTo(19, 14)
            c.quadraticCurveTo(18, 19, 12, 22); c.quadraticCurveTo(6, 19, 5, 14)
            c.lineTo(4, 6); c.closePath(); c.moveTo(8, 12); c.lineTo(11, 15); c.lineTo(16, 9)
        }
        c.stroke()
    }
}
