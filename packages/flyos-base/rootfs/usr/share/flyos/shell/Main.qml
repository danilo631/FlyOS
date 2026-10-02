// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

QtObject {
    id: shell

    readonly property color glass: fly.highContrast ? "#FF050608" : (fly.transparencyReduced ? "#F41A1E27" : "#C81A1E27")
    readonly property color glassStrong: fly.highContrast ? "#FF050608" : (fly.transparencyReduced ? "#FC171A22" : "#EC171A22")
    readonly property color surface: fly.highContrast ? "#050608" : "#181D27"
    readonly property color stroke: fly.highContrast ? "#A8FFFFFF" : "#32FFFFFF"
    readonly property color strokeStrong: fly.highContrast ? "#E0FFFFFF" : "#58FFFFFF"
    readonly property color textMain: "#F7F8FC"
    readonly property color textDim: fly.highContrast ? "#E6EAF2" : "#AEB7C7"
    readonly property color accent: "#7CAEFF"
    readonly property color accentSoft: "#407CAEFF"
    readonly property int motionDuration: fly.effectsReduced ? 0 : 145
    readonly property real uiScale: fly.textScale

    component GlassPanel: Rectangle {
        color: shell.glass
        border.color: shell.stroke
        border.width: 1
        radius: 20
    }

    component FlyButton: Button {
        id: control
        implicitHeight: 36
        leftPadding: 12
        rightPadding: 12
        font.pixelSize: Math.round(13 * shell.uiScale)
        contentItem: Text {
            text: control.text
            color: shell.textMain
            font: control.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 11
            color: control.down ? "#44FFFFFF" : (control.hovered ? "#2FFFFFFF" : "#18FFFFFF")
            border.color: control.hovered ? shell.strokeStrong : "transparent"
            Behavior on color { ColorAnimation { duration: shell.motionDuration } }
        }
    }

    component ToggleTile: Rectangle {
        id: tile
        property string title: ""
        property string subtitle: ""
        property bool checked: false
        signal clicked()
        Layout.fillWidth: true
        implicitHeight: 68
        radius: 17
        color: checked ? shell.accentSoft : "#18FFFFFF"
        border.color: checked ? "#5C9FFF" : shell.stroke

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: tile.clicked()
            onEntered: tile.scale = fly.effectsReduced ? 1 : 1.015
            onExited: tile.scale = 1
        }
        Behavior on scale { NumberAnimation { duration: shell.motionDuration } }

        Column {
            anchors.left: parent.left
            anchors.leftMargin: 15
            anchors.verticalCenter: parent.verticalCenter
            spacing: 3
            Text { text: tile.title; color: shell.textMain; font.pixelSize: Math.round(14 * shell.uiScale); font.bold: true }
            Text { text: tile.subtitle; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); elide: Text.ElideRight; width: tile.width - 28 }
        }
    }

    // Desktop surface. Fly Shell draws the wallpaper itself so the native Fly
    // session does not need plasmashell just to provide a desktop background.
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            visible: true
            screen: modelData
            color: "#0D1118"
            flags: Qt.FramelessWindowHint | Qt.Tool
            LayerShell.Window.layer: LayerShell.Window.LayerBackground
            LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
            LayerShell.Window.exclusionZone: -1
            LayerShell.Window.scope: "fly-shell-desktop"
            LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone

            Image {
                anchors.fill: parent
                source: "file:///usr/share/wallpapers/FlyOS/contents/images/3840x2160.svg"
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
            }
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#08000000" }
                    GradientStop { position: 0.55; color: "#12000000" }
                    GradientStop { position: 1.0; color: "#46000000" }
                }
            }
        }
    }

    // Menu bar on every screen, matching the Fly philosophy of predictable
    // placement while remaining usable on multi-monitor setups.
    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            visible: true
            screen: modelData
            color: "transparent"
            height: 42
            flags: Qt.FramelessWindowHint | Qt.Tool
            LayerShell.Window.layer: LayerShell.Window.LayerTop
            LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
            LayerShell.Window.exclusionZone: 42
            LayerShell.Window.scope: "fly-shell-topbar"
            LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand

            Rectangle {
                anchors.fill: parent
                color: fly.highContrast ? "#FF050608" : (fly.transparencyReduced ? "#F0181B23" : "#BA181B23")
                border.color: "#20FFFFFF"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 7

                    FlyButton {
                        text: "✦"
                        font.pixelSize: Math.round(17 * shell.uiScale)
                        font.bold: true
                        ToolTip.visible: hovered
                        ToolTip.text: "Fly Launcher"
                        onClicked: fly.toggleLauncher()
                    }
                    Text {
                        text: "Fly OS"
                        color: shell.textMain
                        font.pixelSize: Math.round(13 * shell.uiScale)
                        font.weight: Font.DemiBold
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        visible: fly.microphoneActive
                        width: 9; height: 9; radius: 5
                        color: "#FF9C5B"
                        ToolTip.visible: micArea.containsMouse
                        ToolTip.text: fly.privacyApps.length ? "Microfone em uso • " + fly.privacyApps : "Microfone em uso"
                        MouseArea { id: micArea; anchors.fill: parent; hoverEnabled: true; onClicked: fly.runAction("privacy") }
                    }
                    Rectangle {
                        visible: fly.cameraActive
                        width: 9; height: 9; radius: 5
                        color: "#7FE0A8"
                        ToolTip.visible: camArea.containsMouse
                        ToolTip.text: fly.privacyApps.length ? "Câmera em uso • " + fly.privacyApps : "Câmera em uso"
                        MouseArea { id: camArea; anchors.fill: parent; hoverEnabled: true; onClicked: fly.runAction("privacy") }
                    }
                    Rectangle {
                        visible: fly.performanceState !== "normal"
                        width: 9; height: 9; radius: 5
                        color: fly.performanceState === "pressure" ? "#FFB347" : "#FFD166"
                        ToolTip.visible: perfArea.containsMouse
                        ToolTip.text: (fly.performanceState === "pressure" ? "Pressão de recursos" : "Sistema ocupado") + " • CPU " + fly.cpuLoad + "% • RAM " + fly.memoryLoad + "%"
                        MouseArea { id: perfArea; anchors.fill: parent; hoverEnabled: true; onClicked: fly.runAction("activity") }
                    }
                    FlyButton {
                        visible: fly.updateReady
                        text: "↻"
                        ToolTip.visible: hovered
                        ToolTip.text: "Atualização preparada — reinicie quando quiser"
                        onClicked: fly.runAction("update")
                    }
                    Text {
                        visible: fly.network.length > 0
                        text: fly.network
                        color: shell.textDim
                        font.pixelSize: Math.round(11 * shell.uiScale)
                        elide: Text.ElideRight
                        Layout.maximumWidth: 150
                    }
                    Text {
                        visible: fly.battery.length > 0
                        text: fly.battery
                        color: shell.textMain
                        font.pixelSize: Math.round(11 * shell.uiScale)
                    }
                    FlyButton {
                        text: fly.notificationCount > 0 ? "◌ " + fly.notificationCount : "◌"
                        ToolTip.visible: hovered
                        ToolTip.text: fly.notificationCount > 0 ? fly.notificationCount + " notificação(ões)" : "Notificações"
                        onClicked: fly.openNotifications()
                    }
                    FlyButton {
                        text: fly.clock
                        font.bold: true
                        ToolTip.visible: hovered
                        ToolTip.text: fly.dateText
                        onClicked: fly.toggleQuick()
                    }
                }
            }
        }
    }

    Instantiator {
        model: Qt.application.screens
        delegate: Window {
            required property var modelData
            visible: true
            screen: modelData
            color: "transparent"
            width: Math.min(650, modelData.width - 36)
            height: 78
            flags: Qt.FramelessWindowHint | Qt.Tool
            LayerShell.Window.layer: LayerShell.Window.LayerTop
            LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
            LayerShell.Window.exclusionZone: 0
            LayerShell.Window.margins: Qt.margins(0, 0, 0, 12)
            LayerShell.Window.scope: "fly-shell-dock"
            LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand

            GlassPanel {
                anchors.centerIn: parent
                width: Math.min(parent.width, dockRow.implicitWidth + 32)
                height: 66
                radius: 23

                Row {
                    id: dockRow
                    anchors.centerIn: parent
                    spacing: 7

                    Repeater {
                        model: fly.pinned
                        delegate: ToolButton {
                            required property var modelData
                            id: dockButton
                            width: 51
                            height: 51
                            icon.name: modelData.icon
                            icon.width: 31
                            icon.height: 31
                            display: AbstractButton.IconOnly
                            hoverEnabled: true
                            scale: hovered && fly.dockMagnification ? 1.14 : 1.0
                            y: hovered && fly.dockMagnification ? -3 : 0
                            ToolTip.visible: hovered
                            ToolTip.text: modelData.name
                            background: Rectangle {
                                radius: 15
                                color: dockButton.hovered ? "#32FFFFFF" : "transparent"
                                border.color: dockButton.hovered ? shell.stroke : "transparent"
                            }
                            Behavior on scale { NumberAnimation { duration: shell.motionDuration; easing.type: Easing.OutCubic } }
                            Behavior on y { NumberAnimation { duration: shell.motionDuration; easing.type: Easing.OutCubic } }
                            onClicked: fly.activateResult(modelData.kind, modelData.target)
                        }
                    }

                    Rectangle { width: 1; height: 35; color: "#32FFFFFF"; anchors.verticalCenter: parent.verticalCenter }
                    ToolButton {
                        width: 51; height: 51; hoverEnabled: true
                        icon.name: "view-app-grid-symbolic"; icon.width: 28; icon.height: 28
                        ToolTip.visible: hovered; ToolTip.text: "Todos os aplicativos"
                        background: Rectangle { radius: 15; color: parent.hovered ? "#32FFFFFF" : "transparent" }
                        onClicked: fly.toggleLauncher()
                    }
                }
            }
        }
    }

    Window {
        id: launcher
        visible: fly.launcherVisible
        color: "transparent"
        width: Math.min(840, Screen.width - 44)
        height: Math.min(640, Screen.height - 94)
        flags: Qt.FramelessWindowHint | Qt.Tool
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorNone
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.scope: "fly-shell-launcher"
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
        LayerShell.Window.activateOnShow: true
        LayerShell.Window.wantsToBeOnActiveScreen: true

        onVisibleChanged: {
            if (visible) {
                search.text = ""
                fly.setQuery("")
                search.forceActiveFocus()
            }
        }

        GlassPanel {
            anchors.fill: parent
            radius: 30
            color: shell.glassStrong

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        spacing: 1
                        Text { text: "Fly Search"; color: shell.textMain; font.pixelSize: Math.round(26 * shell.uiScale); font.bold: true }
                        Text { text: "Apps, arquivos e ações do sistema"; color: shell.textDim; font.pixelSize: Math.round(11 * shell.uiScale) }
                    }
                    Item { Layout.fillWidth: true }
                    FlyButton { text: "Esc"; onClicked: fly.hideOverlays() }
                }

                TextField {
                    id: search
                    Layout.fillWidth: true
                    implicitHeight: 54
                    placeholderText: "Busque um app, arquivo ou ação…"
                    color: shell.textMain
                    placeholderTextColor: shell.textDim
                    font.pixelSize: Math.round(16 * shell.uiScale)
                    leftPadding: 18
                    rightPadding: 18
                    background: Rectangle {
                        radius: 17
                        color: "#23FFFFFF"
                        border.width: 1
                        border.color: search.activeFocus ? shell.accent : shell.stroke
                    }
                    onTextChanged: fly.setQuery(text)
                    Keys.onEscapePressed: fly.hideOverlays()
                    Keys.onDownPressed: {
                        if (fly.results.length > 0) {
                            resultList.currentIndex = Math.max(0, resultList.currentIndex)
                            resultList.forceActiveFocus()
                        }
                    }
                    Keys.onReturnPressed: {
                        if (fly.results.length > 0)
                            fly.activateResult(fly.results[0].kind, fly.results[0].target)
                    }
                }

                ListView {
                    id: resultList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: fly.results
                    currentIndex: fly.results.length > 0 ? 0 : -1
                    focus: false
                    keyNavigationEnabled: true
                    ScrollBar.vertical: ScrollBar { }
                    Keys.onEscapePressed: { search.forceActiveFocus(); fly.hideOverlays() }
                    Keys.onUpPressed: {
                        if (currentIndex <= 0) {
                            currentIndex = 0
                            search.forceActiveFocus()
                        } else {
                            decrementCurrentIndex()
                        }
                    }
                    Keys.onDownPressed: incrementCurrentIndex()
                    Keys.onReturnPressed: {
                        if (currentIndex >= 0 && currentIndex < fly.results.length)
                            fly.activateResult(fly.results[currentIndex].kind, fly.results[currentIndex].target)
                    }

                    delegate: ItemDelegate {
                        required property var modelData
                        id: result
                        width: resultList.width
                        height: 61
                        hoverEnabled: true
                        icon.name: modelData.icon
                        icon.width: 30
                        icon.height: 30
                        display: AbstractButton.IconOnly
                        background: Rectangle {
                            radius: 15
                            color: (result.hovered || result.ListView.isCurrentItem) ? "#28FFFFFF" : "transparent"
                            border.color: (result.hovered || result.ListView.isCurrentItem) ? shell.accentSoft : "transparent"
                        }
                        contentItem: RowLayout {
                            spacing: 12
                            Rectangle {
                                width: 34; height: 34; radius: 10
                                color: modelData.kind === "app" ? "#2679D8FF" : (modelData.kind === "file" ? "#2635D07F" : "#26FFFFFF")
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.name && modelData.name.length ? modelData.name.charAt(0).toUpperCase() : "•"
                                    color: shell.textMain
                                    font.pixelSize: Math.round(14 * shell.uiScale)
                                    font.bold: true
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: modelData.name; color: shell.textMain; font.pixelSize: Math.round(14 * shell.uiScale); font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                                Text { text: modelData.subtitle; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); Layout.fillWidth: true; elide: Text.ElideMiddle }
                            }
                            Text {
                                text: modelData.kind === "app" ? "APP" : (modelData.kind === "file" ? "ARQUIVO" : "AÇÃO")
                                color: shell.textDim; font.pixelSize: Math.round(9 * shell.uiScale); font.bold: true
                            }
                        }
                        onClicked: fly.activateResult(modelData.kind, modelData.target)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Meta + Espaço para abrir"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale) }
                    Item { Layout.fillWidth: true }
                    FlyButton { text: "Fly Center"; onClicked: fly.openCenter() }
                    FlyButton { text: "Atualizações"; onClicked: fly.runAction("update") }
                }
            }
        }
    }

    Window {
        id: quick
        visible: fly.quickVisible
        color: "transparent"
        width: 410
        height: Math.min(650, Screen.height - 70)
        flags: Qt.FramelessWindowHint | Qt.Tool
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorRight
        LayerShell.Window.margins: Qt.margins(0, 50, 14, 0)
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.scope: "fly-shell-quick"
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        LayerShell.Window.activateOnShow: true
        LayerShell.Window.wantsToBeOnActiveScreen: true

        GlassPanel {
            anchors.fill: parent
            radius: 27
            color: shell.glassStrong

            ScrollView {
                anchors.fill: parent
                anchors.margins: 18
                clip: true

                ColumnLayout {
                    width: quick.width - 36
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        ColumnLayout {
                            spacing: 1
                            Text { text: fly.clock; color: shell.textMain; font.pixelSize: Math.round(30 * shell.uiScale); font.bold: true }
                            Text { text: fly.dateText; color: shell.textDim; font.pixelSize: Math.round(11 * shell.uiScale) }
                        }
                        Item { Layout.fillWidth: true }
                        FlyButton { text: "Notificações"; onClicked: fly.openNotifications() }
                        FlyButton { text: "×"; onClicked: fly.hideOverlays() }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        rowSpacing: 9
                        columnSpacing: 9
                        ToggleTile {
                            title: "Wi‑Fi"; subtitle: fly.network; checked: fly.wifiEnabled
                            onClicked: fly.toggleWifi()
                        }
                        ToggleTile {
                            title: "Bluetooth"; subtitle: fly.bluetoothEnabled ? "Ativado" : "Desativado"; checked: fly.bluetoothEnabled
                            onClicked: fly.toggleBluetooth()
                        }
                        ToggleTile {
                            title: "Modo avião"; subtitle: fly.airplaneMode ? "Rádios desligados" : "Desativado"; checked: fly.airplaneMode
                            onClicked: fly.toggleAirplane()
                        }
                        ToggleTile {
                            title: "Foco"; subtitle: "Não perturbe"; checked: fly.dndEnabled
                            onClicked: fly.toggleDnd()
                        }
                        ToggleTile {
                            title: "Visão geral"; subtitle: "Janelas e áreas"; checked: false
                            onClicked: fly.openOverview()
                        }
                        ToggleTile {
                            title: "Luz noturna"; subtitle: fly.nightLightEnabled ? "Ativada" : "Desativada"; checked: fly.nightLightEnabled
                            onClicked: fly.toggleNightLight()
                        }
                        ToggleTile {
                            title: "Microfone"; subtitle: fly.microphoneMuted ? "Mudo" : (fly.microphoneActive ? "Em uso" : "Disponível"); checked: !fly.microphoneMuted
                            onClicked: fly.toggleMicrophoneMute()
                        }
                    }

                    GlassPanel {
                        Layout.fillWidth: true
                        implicitHeight: 66
                        color: "#12FFFFFF"
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 9
                            Text { text: "Área de trabalho " + fly.currentDesktop; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                            Item { Layout.fillWidth: true }
                            FlyButton { text: "‹"; ToolTip.visible: hovered; ToolTip.text: "Área anterior"; onClicked: fly.switchWorkspace("previous") }
                            FlyButton { text: "Visão geral"; onClicked: fly.openOverview() }
                            FlyButton { text: "›"; ToolTip.visible: hovered; ToolTip.text: "Próxima área"; onClicked: fly.switchWorkspace("next") }
                        }
                    }

                    GlassPanel {
                        Layout.fillWidth: true
                        implicitHeight: 92
                        color: "#12FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 4
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: fly.muted ? "Áudio mudo" : "Volume"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                                Item { Layout.fillWidth: true }
                                FlyButton { text: fly.muted ? "Ativar" : "Mudo"; onClicked: fly.toggleMute() }
                                Text { text: fly.volume + "%"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale) }
                            }
                            Slider {
                                Layout.fillWidth: true
                                from: 0; to: 100; value: Math.min(100, fly.volume)
                                onMoved: fly.setVolume(Math.round(value))
                            }
                        }
                    }

                    GlassPanel {
                        visible: fly.audioOutputs.length > 1
                        Layout.fillWidth: true
                        implicitHeight: 88
                        color: "#12FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 5
                            Text { text: "Saída de áudio"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                            ComboBox {
                                Layout.fillWidth: true
                                model: fly.audioOutputs
                                textRole: "label"
                                valueRole: "name"
                                currentIndex: {
                                    for (let i = 0; i < fly.audioOutputs.length; ++i) {
                                        if (fly.audioOutputs[i].name === fly.currentAudioOutput)
                                            return i
                                    }
                                    return 0
                                }
                                onActivated: fly.setAudioOutput(String(currentValue))
                            }
                        }
                    }

                    GlassPanel {
                        visible: fly.audioInputs.length > 1
                        Layout.fillWidth: true
                        implicitHeight: 88
                        color: "#12FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 5
                            Text { text: "Entrada de áudio"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                            ComboBox {
                                Layout.fillWidth: true
                                model: fly.audioInputs
                                textRole: "label"
                                valueRole: "name"
                                currentIndex: {
                                    for (let i = 0; i < fly.audioInputs.length; ++i) {
                                        if (fly.audioInputs[i].name === fly.currentAudioInput)
                                            return i
                                    }
                                    return 0
                                }
                                onActivated: fly.setAudioInput(String(currentValue))
                            }
                        }
                    }

                    GlassPanel {
                        visible: fly.brightness >= 0
                        Layout.fillWidth: true
                        implicitHeight: 82
                        color: "#12FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 3
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "Brilho"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                                Item { Layout.fillWidth: true }
                                Text { text: fly.brightness + "%"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale) }
                            }
                            Slider {
                                Layout.fillWidth: true
                                from: 1; to: 100; value: fly.brightness
                                onMoved: fly.setBrightness(Math.round(value))
                            }
                        }
                    }

                    GlassPanel {
                        visible: fly.mediaAvailable
                        Layout.fillWidth: true
                        implicitHeight: 112
                        color: "#12FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 6
                            Text { text: "Reproduzindo agora"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); font.bold: true }
                            Text { text: fly.mediaTitle; color: shell.textMain; font.pixelSize: Math.round(13 * shell.uiScale); font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                            Text { text: fly.mediaArtist; visible: fly.mediaArtist.length > 0; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); Layout.fillWidth: true; elide: Text.ElideRight }
                            RowLayout {
                                Layout.fillWidth: true
                                FlyButton { text: "◀"; Layout.fillWidth: true; onClicked: fly.mediaAction("previous") }
                                FlyButton { text: fly.mediaPlaying ? "Pausar" : "Reproduzir"; Layout.fillWidth: true; onClicked: fly.mediaAction("play-pause") }
                                FlyButton { text: "▶"; Layout.fillWidth: true; onClicked: fly.mediaAction("next") }
                            }
                        }
                    }

                    GlassPanel {
                        visible: fly.updateReady || fly.updateState === "failed" || fly.recoveryAvailable
                        Layout.fillWidth: true
                        implicitHeight: 86
                        color: fly.updateState === "failed" ? "#20FF6B6B" : "#167CC7FF"
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 13; spacing: 5
                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: fly.updateState === "failed" ? "Atualização precisa de atenção" : (fly.updateReady ? "Atualização pronta para reiniciar" : "Recovery disponível")
                                    color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true
                                }
                                Item { Layout.fillWidth: true }
                                FlyButton {
                                    text: fly.updateState === "failed" ? "Recovery" : "Detalhes"
                                    onClicked: fly.runAction(fly.updateState === "failed" ? "recovery" : "update")
                                }
                            }
                            Text {
                                text: fly.updateDetail.length ? fly.updateDetail : (fly.updateReady ? "Os pacotes já foram preparados e serão aplicados no modo de manutenção." : "Há um snapshot ou estado de recuperação disponível.")
                                color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); Layout.fillWidth: true
                                wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                            }
                        }
                    }

                    GlassPanel {
                        Layout.fillWidth: true
                        implicitHeight: 74
                        color: fly.performanceState === "pressure" ? "#20FFB347" : (fly.performanceState === "busy" ? "#16FFD166" : "#12FFFFFF")
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 10
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 1
                                Text { text: fly.performanceState === "pressure" ? "Sistema sob pressão" : (fly.performanceState === "busy" ? "Sistema ocupado" : "Desempenho normal"); color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                                Text { text: "CPU " + fly.cpuLoad + "%  •  RAM " + fly.memoryLoad + "%  •  PSI " + Number(fly.memoryPressure).toFixed(1); color: shell.textDim; font.pixelSize: Math.round(9 * shell.uiScale) }
                            }
                            FlyButton { text: "Atividade"; onClicked: fly.runAction("activity") }
                        }
                    }

                    GlassPanel {
                        Layout.fillWidth: true
                        implicitHeight: 62
                        color: fly.focusMode ? "#187CC7FF" : "#12FFFFFF"
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 8
                            ColumnLayout {
                                spacing: 1; Layout.fillWidth: true
                                Text { text: "Focus Mode"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                                Text { text: fly.focusMode ? "Interrupções reduzidas" : "Silencia avisos e reduz distrações"; color: shell.textDim; font.pixelSize: Math.round(9 * shell.uiScale) }
                            }
                            Switch { checked: fly.focusMode; onClicked: fly.toggleFocusMode() }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        FlyButton { text: "Privacidade"; Layout.fillWidth: true; onClicked: fly.runAction("privacy") }
                        FlyButton { text: "Atividade"; Layout.fillWidth: true; onClicked: fly.runAction("activity") }
                        FlyButton { text: "Visão geral"; Layout.fillWidth: true; onClicked: fly.runAction("overview") }
                    }

                    Text { text: "Energia"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); font.bold: true }
                    RowLayout {
                        Layout.fillWidth: true
                        FlyButton { text: "Economia"; Layout.fillWidth: true; onClicked: fly.setPowerProfile("power-saver") }
                        FlyButton { text: "Equilibrado"; Layout.fillWidth: true; onClicked: fly.setPowerProfile("balanced") }
                        FlyButton { text: "Desempenho"; Layout.fillWidth: true; onClicked: fly.setPowerProfile("performance") }
                    }
                    Text {
                        text: "Perfil: " + fly.powerProfile + (fly.battery.length ? "  •  " + fly.battery : "") + (fly.effectsReduced ? "  •  efeitos reduzidos" : "")
                        color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        FlyButton { text: "Rede"; Layout.fillWidth: true; onClicked: fly.runAction("network") }
                        FlyButton { text: "Bluetooth"; Layout.fillWidth: true; onClicked: fly.runAction("bluetooth") }
                        FlyButton { text: "Bateria"; Layout.fillWidth: true; onClicked: fly.runAction("battery") }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        FlyButton { text: "Fly Center"; Layout.fillWidth: true; onClicked: fly.openCenter() }
                        FlyButton { text: "Sistema"; Layout.fillWidth: true; onClicked: fly.openSystemSettings() }
                        FlyButton { text: "Bloquear"; Layout.fillWidth: true; onClicked: fly.lock() }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#22FFFFFF" }

                    RowLayout {
                        Layout.fillWidth: true
                        FlyButton { text: "Suspender"; Layout.fillWidth: true; onClicked: fly.powerAction("suspend") }
                        FlyButton { text: "Sair"; Layout.fillWidth: true; onClicked: fly.powerAction("logout") }
                        FlyButton { text: "Reiniciar"; Layout.fillWidth: true; onClicked: fly.powerAction("reboot") }
                        FlyButton { text: "Desligar"; Layout.fillWidth: true; onClicked: fly.powerAction("poweroff") }
                    }
                }
            }
        }
    }

    // Fly-native notification center. The D-Bus daemon keeps only session-local
    // history; this window renders it directly instead of depending on swaync.
    Window {
        id: notificationCenter
        visible: fly.notificationsVisible
        color: "transparent"
        width: Math.min(430, Screen.width - 30)
        height: Math.min(650, Screen.height - 76)
        flags: Qt.FramelessWindowHint | Qt.Tool
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorRight
        LayerShell.Window.margins: Qt.margins(0, 54, 14, 0)
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.scope: "fly-shell-notifications"
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        LayerShell.Window.wantsToBeOnActiveScreen: true

        GlassPanel {
            anchors.fill: parent
            radius: 28
            color: shell.glassStrong
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        spacing: 1
                        Text { text: "Notificações"; color: shell.textMain; font.pixelSize: Math.round(22 * shell.uiScale); font.bold: true }
                        Text { text: fly.dndEnabled ? "Foco ativado — novos avisos não interrompem" : fly.notificationCount + " nesta sessão"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale) }
                    }
                    Item { Layout.fillWidth: true }
                    FlyButton { text: fly.dndEnabled ? "Foco: on" : "Foco"; onClicked: fly.toggleDnd() }
                    FlyButton { text: "Limpar"; enabled: fly.notificationCount > 0; onClicked: fly.clearNotifications() }
                    FlyButton { text: "×"; onClicked: fly.openNotifications() }
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: "#22FFFFFF" }
                ListView {
                    id: notificationList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 8
                    model: fly.notifications
                    ScrollBar.vertical: ScrollBar { }
                    delegate: Rectangle {
                        id: notificationCard
                        required property var modelData
                        readonly property int notificationId: Number(modelData.id)
                        width: notificationList.width
                        height: notifColumn.implicitHeight + 26
                        radius: 17
                        color: modelData.urgency === 2 ? "#274D2530" : "#16FFFFFF"
                        border.color: modelData.urgency === 2 ? "#66FF8B9B" : shell.stroke
                        ColumnLayout {
                            id: notifColumn
                            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                            anchors.margins: 13
                            spacing: 4
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.app || "Aplicativo"; color: shell.textDim; font.pixelSize: Math.round(9 * shell.uiScale); font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                                FlyButton { text: "×"; implicitHeight: 28; onClicked: fly.dismissNotification(Number(modelData.id)) }
                            }
                            Text { text: modelData.summary || "Notificação"; color: shell.textMain; font.pixelSize: Math.round(13 * shell.uiScale); font.bold: true; Layout.fillWidth: true; wrapMode: Text.Wrap }
                            Text { visible: (modelData.body || "").length > 0; text: modelData.body || ""; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); Layout.fillWidth: true; wrapMode: Text.Wrap; maximumLineCount: 5; elide: Text.ElideRight }
                            RowLayout {
                                visible: (modelData.actions || []).length > 0
                                Layout.fillWidth: true
                                spacing: 6
                                Repeater {
                                    model: (modelData.actions || []).slice(0, 3)
                                    delegate: FlyButton {
                                        required property var modelData
                                        text: modelData.label || "Abrir"
                                        onClicked: fly.notificationAction(notificationCard.notificationId, String(modelData.key))
                                    }
                                }
                                Item { Layout.fillWidth: true }
                            }
                        }
                    }
                    footer: Item { width: 1; height: 4 }
                }
                Text {
                    visible: fly.notificationCount === 0
                    text: "Tudo tranquilo por aqui."
                    color: shell.textDim
                    font.pixelSize: Math.round(12 * shell.uiScale)
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    Window {
        id: notificationToast
        visible: fly.toastVisible
        color: "transparent"
        width: Math.min(380, Screen.width - 30)
        height: toastColumn.implicitHeight + 34
        flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorRight
        LayerShell.Window.margins: Qt.margins(0, 56, 14, 0)
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.scope: "fly-shell-notification-toast"
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        LayerShell.Window.wantsToBeOnActiveScreen: true

        GlassPanel {
            anchors.fill: parent
            radius: 21
            color: shell.glassStrong
            ColumnLayout {
                id: toastColumn
                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                anchors.margins: 16
                spacing: 4
                Text { text: fly.toastApp; color: shell.textDim; font.pixelSize: Math.round(9 * shell.uiScale); font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                Text { text: fly.toastSummary; color: shell.textMain; font.pixelSize: Math.round(13 * shell.uiScale); font.bold: true; Layout.fillWidth: true; wrapMode: Text.Wrap }
                Text { visible: fly.toastBody.length > 0; text: fly.toastBody; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale); Layout.fillWidth: true; wrapMode: Text.Wrap; maximumLineCount: 4; elide: Text.ElideRight }
            }
            MouseArea { anchors.fill: parent; onClicked: fly.activateToast() }
        }
    }

    Window {
        id: osd
        visible: fly.osdVisible
        color: "transparent"
        width: 300
        height: 86
        flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
        LayerShell.Window.margins: Qt.margins(0, 0, 0, 116)
        LayerShell.Window.exclusionZone: 0
        LayerShell.Window.scope: "fly-shell-osd"
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        LayerShell.Window.wantsToBeOnActiveScreen: true

        GlassPanel {
            anchors.fill: parent
            radius: 22
            color: shell.glassStrong
            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 13
                Text {
                    text: fly.osdKind === "brightness" ? "☀" : "♪"
                    color: shell.textMain
                    font.pixelSize: Math.round(24 * shell.uiScale)
                    Layout.preferredWidth: 28
                    horizontalAlignment: Text.AlignHCenter
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: fly.osdKind === "brightness" ? "Brilho" : "Volume"; color: shell.textMain; font.pixelSize: Math.round(12 * shell.uiScale); font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: fly.osdValue + "%"; color: shell.textDim; font.pixelSize: Math.round(10 * shell.uiScale) }
                    }
                    ProgressBar {
                        Layout.fillWidth: true
                        from: 0; to: 100; value: fly.osdValue
                    }
                }
            }
        }
    }
}
