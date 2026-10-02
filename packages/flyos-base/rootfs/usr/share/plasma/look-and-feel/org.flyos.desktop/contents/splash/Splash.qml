import QtQuick 2.15
import org.kde.plasma.core as PlasmaCore

Rectangle {
    id: root
    color: "#151820"

    Text {
        anchors.centerIn: parent
        text: "FLY"
        color: "#f4f7ff"
        font.pixelSize: 72
        font.weight: Font.DemiBold
        font.letterSpacing: 8
    }

    Rectangle {
        width: 80
        height: 3
        radius: 2
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.verticalCenter
        anchors.topMargin: 62
        color: "#5ca3ff"

        SequentialAnimation on opacity {
            loops: Animation.Infinite
            NumberAnimation { to: 0.25; duration: 600 }
            NumberAnimation { to: 1.0; duration: 600 }
        }
    }
}
