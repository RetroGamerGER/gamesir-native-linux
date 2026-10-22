// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Dialog {
    id: root
    objectName: "calibrationDialog"
    required property var controller
    required property var texts
    property var v: controller.view
    property bool simulation: v.simulated !== false
    readonly property int step: v.phase === "ready_to_finish" || v.phase === "completed" ? 3
                                : v.phase === "authorizing" || v.phase === "selecting" ? 1 : 2
    modal: true; focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(Overlay.overlay.width - 32, 760)
    height: Math.min(Overlay.overlay.height - 32,
                     implicitHeaderHeight + implicitFooterHeight + topPadding + bottomPadding
                     + body.implicitHeight + spacing * 2)
    padding: 22
    closePolicy: Popup.CloseOnEscape
    title: texts.cal_title
    background: Rectangle { color: "#181f23"; radius: 18; border.color: "#476052" }
    header: ColumnLayout {
        spacing: 7
        Copy { Layout.leftMargin: 24; Layout.topMargin: 22; text: root.simulation ? root.texts.cal_badge : root.texts.cal_live_badge; font.pixelSize: 11; color: "#9ad5b9" }
        Copy { Layout.fillWidth: true; Layout.leftMargin: 24; Layout.rightMargin: 24; text: root.title; font.pixelSize: 23; font.bold: true }
    }
    contentItem: ScrollView {
        id: scroll
        objectName: "calibrationScroll"
        contentWidth: availableWidth
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            id: body
            width: scroll.availableWidth; spacing: 18
            Copy {
                objectName: "calibrationStep"
                Layout.fillWidth: true
                text: root.texts.cal_step + " " + root.step + " / 3 · " + root.texts["cal_step_" + root.step]
                font.bold: true; color: "#a6d8c2"
            }
            Copy { visible: root.simulation || root.step === 1; Layout.fillWidth: true; text: root.simulation ? root.texts.cal_intro : root.texts.cal_live_intro; color: "#a4aeb7"; font.pixelSize: 12 }
            ComboBox {
                id: targetChoice
                objectName: "calibrationTarget"
                Layout.fillWidth: true
                visible: root.v.phase === "selecting"
                enabled: !root.v.busy
                model: (root.v.targets || []).map(function(row) {
                    return (row.pid === 4190 ? "GameSir G7 Pro ZZZ" : "GameSir G7 Pro") + " · USB " + row.port
                })
            }
            ActionButton {
                objectName: "calibrationSelect"
                visible: root.v.phase === "selecting"
                text: root.texts.cal_select
                enabled: !root.v.busy && targetChoice.currentIndex >= 0
                onClicked: root.controller.select(targetChoice.currentIndex)
            }
            Copy {
                Layout.fillWidth: true
                visible: !root.simulation && root.v.phase === "selecting" && !(root.v.targets || []).length
                text: root.texts.cal_no_targets; color: "#edc28e"
            }
            Card {
                Layout.fillWidth: true; inset: 16; color: "#1b2b26"
                Copy {
                    objectName: "calibrationStatus"
                    Layout.fillWidth: true
                    text: (!root.simulation && root.texts["cal_live_state_" + root.v.phase]
                          ? root.texts["cal_live_state_" + root.v.phase]
                          : root.texts["cal_state_" + root.v.phase])
                          + (root.v.phase === "preparing" ? " " + root.v.countdown + " s" : "")
                    font.pixelSize: 15; font.bold: true
                    color: root.v.phase === "lost" || root.v.phase === "error" ? "#edc28e" : "#d3eadf"
                }
                Copy {
                    Layout.fillWidth: true
                    visible: !!text
                    text: !root.simulation && root.v.phase === "completed" ? root.texts.cal_live_completed_note
                          : !root.simulation && root.v.phase === "error" ? root.texts.cal_live_error
                          : root.v.phase === "completed" ? root.texts.cal_completed_note
                          : root.v.phase === "lost" ? root.texts.cal_lost_note
                          : root.v.phase === "cancelled" ? root.texts.cal_cancelled_note
                          : root.v.phase === "error" ? root.texts["cal_error_" + root.v.reason] : ""
                    color: "#b9c9c0"; font.pixelSize: 12
                }
            }
            GridLayout {
                objectName: "calibrationPlots"
                visible: root.simulation || ["ready", "preparing", "measuring", "ready_to_finish"].indexOf(root.v.phase) >= 0
                Layout.fillWidth: true
                columns: root.width < 600 ? 1 : 2
                columnSpacing: 28; rowSpacing: 24
                StickView {
                    objectName: "calibrationLeft"
                    Layout.fillWidth: true; Layout.preferredWidth: 1
                    label: root.texts.cal_left; texts: root.texts; stick: root.v.sticks[0]; phase: root.v.phase
                    simulated: root.simulation
                }
                StickView {
                    objectName: "calibrationRight"
                    Layout.fillWidth: true; Layout.preferredWidth: 1
                    label: root.texts.cal_right; texts: root.texts; stick: root.v.sticks[1]; phase: root.v.phase
                    simulated: root.simulation
                }
            }
            Copy { visible: root.v.phase === "measuring" || root.v.phase === "ready_to_finish"; Layout.fillWidth: true; text: root.texts.cal_legend; color: "#9aa5af"; font.pixelSize: 12 }
            Copy {
                Layout.fillWidth: true
                visible: !root.simulation && !!root.v.cleanupProblem
                text: root.texts.cal_cleanup_error; color: "#edc28e"
            }
            ActionButton {
                objectName: "calibrationDisconnect"
                text: root.texts.cal_disconnect
                visible: root.simulation && root.v.running
                onClicked: root.controller.disconnect()
            }
            ActionButton {
                objectName: "calibrationNew"
                text: root.texts.cal_new
                visible: root.simulation && !root.v.running && root.v.phase !== "idle"
                onClicked: root.controller.open()
            }
        }
    }
    footer: RowLayout {
        spacing: 10
        Item { Layout.fillWidth: true }
        ActionButton {
            objectName: "calibrationCancel"
            text: root.v.phase === "completed" ? root.texts.cal_done : root.v.running ? root.texts.cal_cancel : root.texts.close
            Layout.bottomMargin: 20
            Layout.rightMargin: root.v.canStart || root.v.canFinish ? 0 : 22
            onClicked: root.reject()
        }
        ActionButton {
            id: start
            objectName: "calibrationStart"
            text: root.simulation ? root.texts.cal_start : root.texts.cal_live_start
            visible: root.v.phase === "ready"
            enabled: root.v.canStart; primary: true
            Layout.bottomMargin: 20; Layout.rightMargin: 22
            onClicked: root.controller.start()
        }
        ActionButton {
            objectName: "calibrationFinish"
            text: root.texts.cal_finish
            visible: root.v.phase === "ready_to_finish"
            enabled: root.v.canFinish; primary: true
            Layout.bottomMargin: 20; Layout.rightMargin: 22
            onClicked: root.controller.finish()
        }
    }
    onOpened: start.forceActiveFocus()
    onAboutToHide: controller.close()
    // Keep keyboard focus visible within this independently scrollable dialog.
    function revealFocus(item) {
        let ancestor = item
        while (ancestor && ancestor !== body) ancestor = ancestor.parent
        if (ancestor !== body) return false
        const top = item.mapToItem(body, 0, 0).y
        const flick = scroll.contentItem
        if (top < flick.contentY + 8) flick.contentY = Math.max(0, top - 8)
        else if (top + item.height > flick.contentY + scroll.availableHeight - 8)
            flick.contentY = Math.min(Math.max(0, flick.contentHeight - scroll.availableHeight),
                                     top + item.height - scroll.availableHeight + 8)
        return true
    }
}
