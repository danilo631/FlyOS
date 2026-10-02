import QtQuick 2.15
import QtQuick.Controls 2.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#0b1018"

    Image {
        anchors.fill: parent
        source: config.background
        fillMode: Image.PreserveAspectCrop
    }

    Rectangle {
        anchors.fill: parent
        color: "#30040a12"
    }

    Rectangle {
        width: 430
        height: 390
        radius: 30
        anchors.centerIn: parent
        color: "#c21a202b"
        border.color: "#3affffff"
        border.width: 1

        Column {
            anchors.fill: parent
            anchors.margins: 42
            spacing: 16

            Image {
                width: 82
                height: 82
                anchors.horizontalCenter: parent.horizontalCenter
                source: "file:///usr/share/pixmaps/flyos-logo.svg"
                fillMode: Image.PreserveAspectFit
            }

            Text {
                text: "FLY OS"
                anchors.horizontalCenter: parent.horizontalCenter
                color: "white"
                font.pixelSize: 28
                font.weight: Font.DemiBold
                font.letterSpacing: 4
            }

            TextField {
                id: user
                width: parent.width
                placeholderText: "Usuário"
                text: userModel.lastUser
                selectByMouse: true
            }

            TextField {
                id: pass
                width: parent.width
                placeholderText: "Senha"
                echoMode: TextInput.Password
                onAccepted: sddm.login(user.text, pass.text, session.index)
            }

            ComboBox {
                id: session
                width: parent.width
                model: sessionModel
                textRole: "name"
            }

            Button {
                width: parent.width
                text: "Entrar"
                onClicked: sddm.login(user.text, pass.text, session.index)
            }
        }
    }
}
