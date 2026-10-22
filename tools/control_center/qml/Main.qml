// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: "centerWindow"
    width: 940; height: 1020
    minimumWidth: 560; minimumHeight: 480
    visible: true
    title: t.title + " · " + t.subtitle + " · " + (appModel.isRehearsal ? t.backend_badge : appModel.isDemo ? t.demo : t.prealpha)
    color: "#101417"
    property var t: appModel.strings
    property var v: appModel.view
    property var b: appModel.backend
    property var h: appModel.setup
    property bool narrow: width < 760
    palette.window: "#181c20"
    palette.base: "#15191d"
    palette.text: "#e8e9ed"
    palette.buttonText: "#e8e9ed"
    palette.button: "#20262b"
    palette.highlight: "#354e45"
    palette.highlightedText: "#d8f3e6"
    palette.mid: "#384149"
    onClosing: appModel.stickCalibration.close()

    // Keep keyboard navigation visible even on a short Gamescope window.
    onActiveFocusItemChanged: Qt.callLater(revealMainFocus)
    function revealMainFocus() {
        const item = activeFocusItem
        if (!item || !scroll.contentItem)
            return
        if (calibrationFlow.visible && calibrationFlow.revealFocus(item))
            return
        let ancestor = item
        while (ancestor && ancestor !== page)
            ancestor = ancestor.parent
        if (ancestor !== page)
            return // Dialogs have their own modal focus scope.
        const top = item.mapToItem(page, 0, 0).y
        const flick = scroll.contentItem
        const bottom = top + item.height
        if (top < flick.contentY + 12)
            flick.contentY = Math.max(0, top - 12)
        else if (bottom > flick.contentY + scroll.availableHeight - 12)
            flick.contentY = Math.min(Math.max(0, flick.contentHeight - scroll.availableHeight),
                                     bottom - scroll.availableHeight + 12)
    }

    Connections {
        target: appModel
        function onBackendDialogRequested() { backendFlow.open() }
        function onSetupDialogRequested() { setupFlow.open() }
        function onDialogRequested() { confirmation.open() }
        function onResultRequested() { outcome.open() }
    }

    Connections {
        target: scroll.contentItem
        function onContentHeightChanged() { Qt.callLater(window.revealMainFocus) }
    }

    ScrollView {
        id: scroll
        objectName: "mainScroll"
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AsNeeded
        ColumnLayout {
            id: page
            objectName: "pageContent"
            width: scroll.availableWidth
            spacing: 16
            property int gutter: window.narrow ? 20 : 30

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                Layout.topMargin: 28; Layout.bottomMargin: 4
                spacing: 14
                Rectangle {
                    width: 48; height: 48; radius: 14; color: "#1c2925"
                    Icon { anchors.centerIn: parent; width: 29; height: 29; ink: "#a6d8c2" }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Copy { Layout.fillWidth: true; text: t.title; font.pixelSize: window.narrow ? 19 : 24; font.bold: true }
                    Copy { text: t.subtitle; color: "#9aa5af"; font.pixelSize: 12 }
                }
                RowLayout {
                    spacing: 6
                    ActionButton {
                        objectName: "languageDe"
                        text: "DE"; compact: true; primary: appModel.language === "de"
                        onClicked: appModel.setLanguage("de")
                        Accessible.name: "Deutsch"
                    }
                    ActionButton {
                        objectName: "languageEn"
                        text: "EN"; compact: true; primary: appModel.language === "en"
                        onClicked: appModel.setLanguage("en")
                        Accessible.name: "English"
                    }
                }
            }

            Card {
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                color: "#17231f"; border.color: "#304a3e"; inset: 17
                RowLayout {
                    Layout.fillWidth: true; spacing: 12
                    Icon { kind: "shield"; ink: "#a6d8c2"; Layout.alignment: Qt.AlignTop }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 5
                        Copy { Layout.fillWidth: true; text: appModel.isDemo ? t.demo_title : t.center_intro; color: "#cee8dc"; font.bold: true }
                        Copy { visible: appModel.isDemo; Layout.fillWidth: true; text: t.demo_body; color: "#a6bcb1"; font.pixelSize: 12 }
                    }
                    Copy { text: appModel.isDemo ? t.demo : t.prealpha; color: "#a6d8c2"; font.pixelSize: 10; font.bold: true; Layout.alignment: Qt.AlignTop }
                }
            }

            ActionButton {
                objectName: "setupButton"
                visible: h.offer
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                text: t.setup_offer; primary: true
                onClicked: appModel.requestSetup()
            }

            Card {
                objectName: "statusCard"
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 3
                        Copy { text: t.device; font.pixelSize: 18; font.bold: true }
                        Copy { text: appModel.isDemo ? t.status : t.read_status; color: "#9aa5af"; font.pixelSize: 12 }
                    }
                    ComboBox {
                        id: scenarioBox
                        visible: appModel.isDemo && !appModel.hasTransactions
                        objectName: "scenarioBox"
                        Layout.preferredWidth: window.narrow ? 242 : 290
                        implicitHeight: 42
                        model: appModel.scenarios
                        currentIndex: appModel.scenarioIndex
                        onActivated: index => appModel.selectScenario(index)
                        activeFocusOnTab: true
                        Accessible.name: t.scenario_label
                        font.family: "DejaVu Sans"; font.pixelSize: 12
                        contentItem: Copy {
                            text: scenarioBox.displayText
                            leftPadding: 12; rightPadding: 30
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.NoWrap; elide: Text.ElideRight
                            font.pixelSize: 12
                        }
                        background: Rectangle { radius: 9; color: "#20262b"; border.width: scenarioBox.activeFocus ? 2 : 1; border.color: scenarioBox.activeFocus ? "#a6d8c2" : "#384149" }
                        delegate: ItemDelegate {
                            required property string modelData
                            required property int index
                            width: scenarioBox.width; height: 42
                            text: modelData
                            highlighted: scenarioBox.highlightedIndex === index
                            contentItem: Copy { text: modelData; font.pixelSize: 11; verticalAlignment: Text.AlignVCenter; wrapMode: Text.NoWrap; elide: Text.ElideRight }
                            background: Rectangle { color: parent.highlighted ? "#354e45" : "#20262b" }
                        }
                    }
                    ActionButton {
                        objectName: "refreshButton"
                        visible: !appModel.isDemo
                        text: t.refresh; iconKind: "update"; enabled: !appModel.reading
                        onClicked: appModel.refresh()
                    }
                }
                GridLayout {
                    objectName: "statusGrid"
                    Layout.fillWidth: true
                    columns: window.narrow ? 1 : 3
                    columnSpacing: 10; rowSpacing: 10
                    Repeater {
                        model: [
                            { label: t.driver, value: v.driver, on: v.installed },
                            { label: t.dongle, value: v.dongle, on: v.receiver },
                            { label: t.controller, value: v.controller === t.fact_unobserved ? t.connection_status : v.controller, on: v.connected }
                        ]
                        Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            implicitHeight: window.narrow ? 70 : 94
                            radius: 10; color: "#11171b"
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 12; spacing: 7
                                RowLayout {
                                    Rectangle { width: 5; height: 5; radius: 3; color: modelData.on ? "#a6d8c2" : "#687682" }
                                    Copy { text: modelData.label; color: "#9aa5af"; font.pixelSize: 11 }
                                }
                                Copy { Layout.fillWidth: true; text: modelData.value; font.pixelSize: 12; font.bold: true }
                            }
                        }
                    }
                }
                RowLayout {
                    visible: appModel.isDemo || v.noticeWarning
                    Layout.fillWidth: true; spacing: 7
                    Rectangle { width: 5; height: 5; radius: 3; color: v.noticeWarning ? "#d4b88a" : "#a6d8c2" }
                    Copy { Layout.fillWidth: true; text: v.requirements; color: v.noticeWarning ? "#d4b88a" : "#a6d8c2"; font.pixelSize: 12 }
                }
                Copy { objectName: "scenarioNotice"; visible: v.notice !== t.read_notice; Layout.fillWidth: true; text: v.notice; color: v.noticeWarning ? "#d4b88a" : "#a4aeb7"; font.pixelSize: 12 }
                RowLayout {
                    visible: !appModel.isDemo
                    Layout.fillWidth: true
                    spacing: 12
                    Copy {
                        objectName: "sampleTime"
                        Layout.fillWidth: true
                        text: v.sampleState || ""
                        color: "#9aa5af"; font.pixelSize: 11
                    }
                    ActionButton {
                        id: detailsButton
                        objectName: "detailsButton"
                        text: t.system_details
                        onClicked: systemDetails.open()
                    }
                }
            }

            Card {
                objectName: "installationCard"
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                RowLayout {
                    spacing: 10
                    Icon { kind: "download"; ink: "#a6d8c2"; width: 22; height: 22 }
                    Copy { text: t.install; font.bold: true; font.pixelSize: 16 }
                }
                Copy { Layout.fillWidth: true; text: appModel.hasTransactions ? t.package_short_intro : appModel.isDemo ? t.install_intro : t.read_install; color: "#a4aeb7"; font.pixelSize: 12 }
                RowLayout {
                    Layout.fillWidth: true; spacing: 10
                    ActionButton {
                        id: installButton
                        objectName: "installButton"
                        Layout.fillWidth: true
                        text: appModel.hasTransactions ? t.backend_install : v.installed ? t.already_installed : t.install
                        primary: true; enabled: v.canInstall
                        onClicked: appModel.request("install")
                    }
                    ActionButton {
                        objectName: "removeButton"
                        text: appModel.hasTransactions ? t.backend_remove : t.remove; enabled: v.canRemove
                        onClicked: appModel.request("remove")
                    }
                }
                ActionButton { objectName: "githubButton"; Layout.fillWidth: true; text: t.github; iconKind: "external"; onClicked: appModel.openLink("github") }
                ActionButton {
                    objectName: "checkUpdatesButton"
                    Layout.fillWidth: true
                    visible: v.updateVisible || false
                    enabled: v.canCheckUpdates || false
                    text: t.signed_updates_check
                    iconKind: "update"
                    onClicked: appModel.checkUpdates()
                }
                ActionButton {
                    objectName: "cancelUpdateCheckButton"
                    Layout.fillWidth: true
                    visible: v.checkingUpdates || false
                    text: t.signed_updates_cancel
                    onClicked: appModel.cancelUpdateCheck()
                }
            }

            Card {
                objectName: "calibrationCard"
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                RowLayout {
                    Layout.fillWidth: true; spacing: 10
                    Icon { kind: "sliders"; ink: "#a6d8c2" }
                    Copy { Layout.fillWidth: true; text: t.sticks; font.pixelSize: 16; font.bold: true }
                }
                Copy { Layout.fillWidth: true; text: appModel.stickCalibration.available ? t.cal_card_intro : t.cal_unavailable; color: "#a4aeb7"; font.pixelSize: 12 }
                ActionButton {
                    objectName: "calibrationOpen"
                    Layout.fillWidth: true
                    text: appModel.stickCalibration.view.simulated === false ? t.cal_live_open : t.cal_open
                    enabled: appModel.canCalibrate
                    onClicked: {
                        if (appModel.stickCalibration.open()) calibrationFlow.open()
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                spacing: 10
                ActionButton {
                    id: plannedToggle
                    objectName: "plannedToggle"
                    property bool expanded: false
                    text: t.planned + (expanded ? "  −" : "  +")
                    onClicked: expanded = !expanded
                }
                GridLayout {
                    visible: plannedToggle.expanded
                    Layout.fillWidth: true; columns: window.narrow ? 1 : 2; columnSpacing: 12; rowSpacing: 12
                    Repeater {
                        model: [
                            { title: t.software_update, icon: "update" },
                            { title: t.controller_firmware, icon: "chip" },
                            { title: t.dongle_firmware, icon: "chip" }
                        ]
                        Card {
                            required property var modelData
                            objectName: "plannedFeature"
                            Layout.fillWidth: true; Layout.preferredWidth: 1
                            enabled: false; inset: 15
                            color: "#151a1e"
                            RowLayout {
                                Layout.fillWidth: true; spacing: 9
                                Icon { kind: modelData.icon; ink: "#6c7984"; width: 19; height: 19 }
                                Copy { Layout.fillWidth: true; text: modelData.title; font.pixelSize: 12; color: "#a7afb7" }
                            }
                            Copy { text: t.coming; color: "#707e89"; font.pixelSize: 11 }
                        }
                    }
                }
            }

            Card {
                objectName: "deadbandCard"
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                RowLayout {
                    Layout.fillWidth: true; spacing: 10
                    Icon { kind: "sliders"; width: 20; height: 20 }
                    Copy { Layout.fillWidth: true; text: t.deadband; font.pixelSize: 14; font.bold: true }
                }
                Copy { Layout.fillWidth: true; text: t.deadband_body; color: "#a4aeb7"; font.pixelSize: 12 }
                RowLayout {
                    Layout.fillWidth: true
                    Copy { Layout.fillWidth: true; text: t.deadband_note; color: "#707e89"; font.pixelSize: 11 }
                    ActionButton { objectName: "deadbandButton"; text: t.deadband_open; iconKind: "external"; onClicked: appModel.openLink("deadband") }
                }
            }

            Copy { Layout.fillWidth: true; Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter; visible: !!text; text: v.settingsError || v.linkError; color: "#d4b88a"; font.pixelSize: 12 }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: page.gutter; Layout.rightMargin: page.gutter
                Layout.bottomMargin: 24; spacing: 6
                Copy { text: appModel.isDemo ? t.footer : t.permission_hint; color: "#7d8a95"; font.pixelSize: 11 }
                Copy { Layout.fillWidth: true; text: t.keyboard_hint + " · " + t.links_hint; color: "#65737e"; font.pixelSize: 10 }
            }
        }
    }

    CalibrationDialog {
        id: calibrationFlow
        controller: appModel.stickCalibration
        texts: t
    }

    Dialog {
        id: systemDetails
        objectName: "detailsDialog"
        modal: true; focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(window.width - 40, 640)
        height: Math.min(window.height - 40,
                         implicitHeaderHeight + implicitFooterHeight + topPadding + bottomPadding
                         + detailsBody.implicitHeight + spacing * 2)
        padding: 24
        closePolicy: Popup.CloseOnEscape
        title: t.system_details
        background: Rectangle { color: "#1a2025"; radius: 18; border.color: "#48574f" }
        header: Copy { text: systemDetails.title; font.pixelSize: 21; font.bold: true; padding: 24; bottomPadding: 8 }
        contentItem: ScrollView {
            id: detailsScroll
            objectName: "detailsScroll"
            contentWidth: availableWidth
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ColumnLayout {
                id: detailsBody
                width: detailsScroll.availableWidth
                spacing: 18
                Copy { Layout.fillWidth: true; text: t.system_details_intro; color: "#a4aeb7"; font.pixelSize: 12 }
                Copy { Layout.fillWidth: true; text: t.os + ": " + v.os + "\n" + t.kernel + ": " + v.kernel + "\n" + t.module + ": " + v.module + "\n" + t.manager + ": " + v.manager; font.pixelSize: 12 }
                Copy { Layout.fillWidth: true; text: t.sample_label + ": " + (v.sampleTime || "—"); color: "#9aa5af"; font.pixelSize: 11 }
                Copy { Layout.fillWidth: true; text: t.read_notice; color: "#9aa5af"; font.pixelSize: 12 }
                Copy { Layout.fillWidth: true; text: v.requirements; color: "#9aa5af"; font.pixelSize: 12 }
                GridLayout {
                    Layout.fillWidth: true
                    columns: window.narrow ? 1 : 2
                    columnSpacing: 24; rowSpacing: 18
                    Repeater {
                        model: v.details || []
                        ColumnLayout {
                            required property var modelData
                            Layout.fillWidth: true; Layout.preferredWidth: 1; spacing: 4
                            Copy { Layout.fillWidth: true; text: modelData.label; color: "#9aa5af"; font.pixelSize: 11 }
                            Copy { Layout.fillWidth: true; text: modelData.value; font.pixelSize: 12 }
                        }
                    }
                }
                Copy { Layout.fillWidth: true; text: t.usb_devices; font.bold: true; font.pixelSize: 12 }
                Repeater {
                    model: v.devices || []
                    Copy {
                        required property var modelData
                        Layout.fillWidth: true
                        text: modelData.port + " · " + modelData.identity + " · " + modelData.binding
                        font.pixelSize: 12
                    }
                }
                Copy {
                    Layout.fillWidth: true
                    visible: !v.devices || !v.devices.length
                    text: v.dongle === t.fact_absent ? t.no_devices : t.devices_unknown
                    color: "#9aa5af"; font.pixelSize: 12
                }
            }
        }
        footer: RowLayout {
            spacing: 12
            Copy { Layout.fillWidth: true; Layout.leftMargin: 24; Layout.bottomMargin: 20; text: t.read_only; color: "#a6d8c2"; font.pixelSize: 11 }
            ActionButton {
                id: detailsClose
                objectName: "detailsCloseButton"
                text: t.close; primary: true
                Layout.bottomMargin: 20; Layout.rightMargin: 24
                onClicked: systemDetails.close()
            }
        }
        onOpened: detailsClose.forceActiveFocus()
        onClosed: detailsButton.forceActiveFocus()
    }

    Dialog {
        id: setupFlow
        objectName: "setupDialog"
        modal: true; focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(window.width - 40, 620)
        height: Math.min(window.height - 40,
                         implicitHeaderHeight + implicitFooterHeight + topPadding + bottomPadding
                         + setupBody.implicitHeight + spacing * 2)
        padding: 24
        closePolicy: h.state === "setup_running" ? Popup.NoAutoClose : Popup.CloseOnEscape
        title: t.setup_title
        background: Rectangle { color: "#1a2025"; radius: 18; border.color: "#48574f" }
        header: Copy { text: setupFlow.title; font.pixelSize: 21; font.bold: true; padding: 24; bottomPadding: 8 }
        contentItem: ScrollView {
            id: setupScroll
            contentWidth: availableWidth; clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ColumnLayout {
                id: setupBody
                width: setupScroll.availableWidth; spacing: 12
                Copy { Layout.fillWidth: true; text: t.setup_body; color: "#b5bec6"; font.pixelSize: 12 }
                Copy { objectName: "setupReview"; Layout.fillWidth: true; text: h.summary; color: "#b5bec6"; font.pixelSize: 12 }
                Copy { Layout.fillWidth: true; text: t.setup_password; color: "#d4b88a"; font.pixelSize: 12 }
                BusyIndicator { visible: h.state === "setup_running"; running: visible; Layout.alignment: Qt.AlignHCenter }
                Copy { Layout.fillWidth: true; visible: h.state === "setup_running"; text: t.setup_running; color: "#a6d8c2" }
                Copy { objectName: "setupMessage"; Layout.fillWidth: true; visible: !!h.message; text: h.message; color: h.success ? "#a6d8c2" : "#d4b88a"; font.pixelSize: 14; font.bold: h.success }
            }
        }
        footer: RowLayout {
            spacing: 10
            Item { Layout.fillWidth: true }
            ActionButton {
                objectName: "setupCancel"
                text: h.success ? t.packages_done : h.state === "setup_failed" ? t.close : t.cancel
                enabled: h.state !== "setup_running"
                Layout.bottomMargin: 20
                Layout.rightMargin: h.state === "setup_review" ? 0 : 24
                onClicked: {
                    if (h.success) { appModel.finishSetup(); setupFlow.accept() }
                    else setupFlow.reject()
                }
            }
            ActionButton {
                objectName: "setupConfirm"
                visible: h.state === "setup_review"
                text: t.setup_auth; primary: true
                Layout.bottomMargin: 20; Layout.rightMargin: 24
                onClicked: appModel.confirmSetup()
            }
        }
        onRejected: appModel.cancelSetup()
    }

    Dialog {
        id: backendFlow
        objectName: "backendDialog"
        modal: true; focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(window.width - 40, 650)
        height: Math.min(window.height - 40,
                         implicitHeaderHeight + implicitFooterHeight + topPadding + bottomPadding
                         + backendBody.implicitHeight + spacing * 2)
        padding: 24
        closePolicy: b.state === "running" ? Popup.NoAutoClose : Popup.CloseOnEscape
        title: b.operation === "remove" ? t.backend_remove : t.backend_install
        background: Rectangle { color: "#1a2025"; radius: 18; border.color: "#48574f" }
        header: Copy { text: backendFlow.title; font.pixelSize: 21; font.bold: true; padding: 24; bottomPadding: 8 }
        contentItem: ScrollView {
            id: backendScroll
            objectName: "backendScroll"
            contentWidth: availableWidth; clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ColumnLayout {
                id: backendBody
                width: backendScroll.availableWidth; spacing: 12
                Copy { Layout.fillWidth: true; text: t.backend_intro; color: "#d4b88a"; font.pixelSize: 12 }
                Copy { Layout.fillWidth: true; visible: b.state === "editing"; text: t.backend_select; font.bold: true }
                Repeater {
                    model: b.state === "editing" ? b.components : []
                    CheckBox {
                        required property var modelData
                        objectName: "component_" + modelData.key
                        text: modelData.label
                        checked: modelData.selected; enabled: modelData.available
                        activeFocusOnTab: true
                        Layout.fillWidth: true
                        onToggled: appModel.selectBackendComponent(modelData.key, checked)
                        contentItem: Copy { text: parent.text; leftPadding: 32; verticalAlignment: Text.AlignVCenter; font.pixelSize: 13; opacity: parent.enabled ? 1 : 0.45 }
                    }
                }
                Copy { objectName: "backendReview"; Layout.fillWidth: true; visible: !!b.review; text: b.review; color: "#b5bec6"; font.pixelSize: 12 }
                BusyIndicator { visible: b.state === "running" || b.state === "checking"; running: visible; Layout.alignment: Qt.AlignHCenter }
                Copy { Layout.fillWidth: true; visible: b.state === "running"; text: t.backend_running; color: "#a6d8c2" }
                Copy { objectName: "backendSuccessTitle"; Layout.fillWidth: true; visible: !!b.successTitle; text: b.successTitle || ""; color: "#a6d8c2"; font.pixelSize: 18; font.bold: true }
                Copy { objectName: "backendMessage"; Layout.fillWidth: true; visible: !!b.message; text: b.message; color: "#d4b88a"; font.pixelSize: 12 }
            }
        }
        footer: RowLayout {
            spacing: 10
            Item { Layout.fillWidth: true }
            ActionButton {
                objectName: "backendCancel"
                text: b.verifiedSuccess ? t.packages_done : b.state === "done" || b.state === "cancelled" ? t.close : t.cancel
                enabled: b.state !== "running"
                Layout.bottomMargin: 20
                onClicked: b.verifiedSuccess ? backendFlow.accept() : backendFlow.reject()
            }
            ActionButton {
                id: backendProceed
                objectName: "backendProceed"
                text: b.state === "editing" ? t.backend_prepare : t.backend_confirm
                visible: b.state === "editing" || b.state === "review"
                primary: true
                Layout.bottomMargin: 20; Layout.rightMargin: 24
                onClicked: b.state === "editing" ? appModel.prepareBackend() : appModel.confirmBackend()
            }
        }
        onRejected: appModel.cancelBackend()
        onOpened: backendProceed.forceActiveFocus()
    }

    Dialog {
        id: confirmation
        objectName: "confirmationDialog"
        modal: true; focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(window.width - 40, 540)
        padding: 24
        closePolicy: Popup.CloseOnEscape
        title: appModel.dialog.title
        background: Rectangle { color: "#1a2025"; radius: 18; border.color: "#48574f" }
        header: Copy { text: confirmation.title; font.pixelSize: 21; font.bold: true; padding: 24; bottomPadding: 8 }
        contentItem: ColumnLayout {
            spacing: 15
            Copy { Layout.fillWidth: true; text: t.summary; color: "#a6d8c2"; font.bold: true }
            Copy { Layout.fillWidth: true; text: t.os + ": " + v.os + "\n" + t.kernel + ": " + v.kernel; color: "#b5bec6" }
            Copy { Layout.fillWidth: true; text: t.demo_package; font.pixelSize: 12 }
            Copy { Layout.fillWidth: true; text: appModel.dialog.body; color: "#b5bec6" }
            Copy { Layout.fillWidth: true; text: t.simulation_only; color: "#d4b88a"; font.bold: true }
        }
        footer: RowLayout {
            spacing: 10
            LayoutMirroring.enabled: false
            Item { Layout.fillWidth: true }
            ActionButton { objectName: "cancelButton"; text: t.cancel; Layout.bottomMargin: 20; onClicked: confirmation.reject() }
            ActionButton { objectName: "confirmButton"; text: t.simulate; primary: true; Layout.bottomMargin: 20; Layout.rightMargin: 24; onClicked: confirmation.accept() }
        }
        onAccepted: appModel.confirm()
        onRejected: appModel.cancel()
    }

    Dialog {
        id: outcome
        objectName: "resultDialog"
        modal: true; focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(window.width - 40, 540)
        padding: 24
        closePolicy: Popup.CloseOnEscape
        title: appModel.result.title
        background: Rectangle { color: "#1a2025"; radius: 18; border.color: appModel.result.tone === "warning" ? "#806d4f" : "#48574f" }
        header: Copy { text: outcome.title; font.pixelSize: 21; font.bold: true; padding: 24; bottomPadding: 8 }
        contentItem: Copy { text: appModel.result.body; color: "#b5bec6" }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            ActionButton { objectName: "resultCloseButton"; text: t.close; primary: true; Layout.bottomMargin: 20; Layout.rightMargin: 24; onClicked: outcome.accept() }
        }
        onAccepted: appModel.dismissResult()
        onRejected: appModel.dismissResult()
    }
}
