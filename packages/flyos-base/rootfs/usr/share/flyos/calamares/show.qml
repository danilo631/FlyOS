import QtQuick 2.15

Item {
    id: root
    anchors.fill: parent
    property int page: 0
    property bool running: false

    function onActivate() { running = true; ticker.start(); }
    function onLeave() { running = false; ticker.stop(); }

    Timer {
        id: ticker
        interval: 5200
        repeat: true
        running: false
        onTriggered: root.page = (root.page + 1) % 4
    }

    Rectangle {
        anchors.fill: parent
        color: "#111722"

        Rectangle {
            width: parent.width * 0.72
            height: parent.height * 0.62
            anchors.centerIn: parent
            radius: 28
            color: "#d9232d3b"
            border.width: 1
            border.color: "#38ffffff"

            Column {
                anchors.fill: parent
                anchors.margins: 42
                spacing: 18

                Text {
                    width: parent.width
                    text: ["Fly OS", "Fly Glass", "Windows apps", "Open by design"][root.page]
                    color: "#f5f8ff"
                    font.pixelSize: 34
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    color: "#cbd8ef"
                    font.pixelSize: 18
                    text: [
                        "Uma experiência Linux consistente construída sobre a compatibilidade e o ecossistema do Ubuntu.",
                        "Blur, superfícies translúcidas e animações curtas criam profundidade sem esconder controles importantes.",
                        "Wine vem integrado com um prefixo Fly separado para executar e organizar aplicativos Windows.",
                        "Código, temas, scripts e patches do Fly OS são auditáveis e modificáveis. Sem ativos proprietários da Apple."
                    ][root.page]
                }

                Rectangle {
                    width: parent.width * 0.72
                    height: 6
                    radius: 3
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "#2b3647"
                    Rectangle {
                        width: parent.width * ((root.page + 1) / 4.0)
                        height: parent.height
                        radius: 3
                        color: "#69a8ff"
                    }
                }
            }
        }
    }
}
