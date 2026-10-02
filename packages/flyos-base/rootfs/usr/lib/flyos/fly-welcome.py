#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)


def run(*args):
    try:
        subprocess.Popen(args)
        return True
    except FileNotFoundError:
        return False


class Page(QFrame):
    def __init__(self, title, body):
        super().__init__()
        self.setObjectName("page")
        box = QVBoxLayout(self)
        box.setContentsMargins(38, 34, 38, 34)
        box.setSpacing(18)
        heading = QLabel(title); heading.setObjectName("heading"); heading.setWordWrap(True)
        text = QLabel(body); text.setObjectName("body"); text.setWordWrap(True); text.setAlignment(Qt.AlignmentFlag.AlignTop)
        box.addWidget(heading); box.addWidget(text)
        self.content = box


class FlyWelcome(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to Fly OS")
        self.setWindowIcon(QIcon.fromTheme("flyos"))
        self.resize(860, 590)
        self.setMinimumSize(740, 520)

        root = QWidget(); root.setObjectName("root")
        outer = QVBoxLayout(root); outer.setContentsMargins(22, 22, 22, 22)
        brand = QLabel("FLY OS"); brand.setObjectName("brand"); outer.addWidget(brand)
        self.pages = QStackedWidget(); outer.addWidget(self.pages, 1)

        p0 = Page(
            "Seu desktop, sem ruído",
            "Fly Shell fornece barra superior, dock, launcher e controles rápidos próprios. KWin continua sendo o compositor Wayland para manter compatibilidade com GPUs, monitores, input e aplicativos KDE.",
        )
        row = QHBoxLayout()
        open_launcher = QPushButton("Testar Launcher"); open_launcher.clicked.connect(lambda: run("fly-shellctl", "launcher"))
        center = QPushButton("Abrir Fly Center"); center.clicked.connect(lambda: run("fly-center"))
        row.addWidget(open_launcher); row.addWidget(center); p0.content.addLayout(row)
        p0.content.addWidget(QLabel("Escolha o perfil visual inicial:"))
        profiles = QHBoxLayout()
        for text, profile in (("Glass", "glass"), ("Equilibrado", "balanced"), ("Performance", "performance")):
            b = QPushButton(text); b.clicked.connect(lambda _=False, p=profile: subprocess.run(["fly-glass", p], check=False)); profiles.addWidget(b)
        p0.content.addLayout(profiles); p0.content.addStretch(1)

        p1 = Page(
            "Aplicativos e firmware em um lugar",
            "Fly Apps agora tem uma camada própria para aplicativos recomendados e usa PackageKit/APT por baixo. O catálogo completo continua opcional via Discover, com Flatpak e fwupd quando instalados.",
        )
        row = QHBoxLayout()
        apps = QPushButton("Abrir Fly Apps"); apps.clicked.connect(lambda: run("fly-apps"))
        flathub = QPushButton("Ativar Flathub"); flathub.clicked.connect(lambda: run("fly-apps"))
        row.addWidget(apps); row.addWidget(flathub); p1.content.addLayout(row); p1.content.addStretch(1)

        p2 = Page(
            "Windows e jogos",
            "Wine vem integrado em um prefixo Fly OS separado. O modo gaming combina GameMode e, opcionalmente, MangoHud/Gamescope. Quando o kernel disponibiliza NTSYNC, Wine/Proton podem aproveitar a sincronização otimizada do Linux moderno.",
        )
        row = QHBoxLayout()
        wine = QPushButton("Configurar Wine"); wine.clicked.connect(lambda: run("fly-wine"))
        game = QPushButton("Guia Fly Gaming"); game.clicked.connect(lambda: run("fly-center"))
        row.addWidget(wine); row.addWidget(game); p2.content.addLayout(row); p2.content.addStretch(1)

        p3 = Page(
            "Segurança e recuperação",
            "Fly OS usa AppArmor, firewall, atualizações de segurança, Secure Boot quando suportado e diagnóstico local. Em raiz Btrfs, Snapper pode criar snapshots antes de upgrades; em ext4 o sistema continua compatível sem conversões automáticas.",
        )
        row = QHBoxLayout()
        health = QPushButton("Fly Health"); health.clicked.connect(lambda: run("fly-health"))
        recovery = QPushButton("Fly Recovery"); recovery.clicked.connect(lambda: run("fly-recovery-ui"))
        row.addWidget(health); row.addWidget(recovery); p3.content.addLayout(row); p3.content.addStretch(1)

        p4 = Page(
            "Privacidade e atualizações",
            "O Fly OS não adiciona telemetria própria por padrão. Fly Search é local-first e indexa apenas nomes/caminhos. Fly Update coordena pacotes, Flatpak, firmware e snapshots quando disponíveis.",
        )
        up = QPushButton("Ver atualizações"); up.clicked.connect(lambda: run("fly-update", "gui")); p4.content.addWidget(up)
        self.startup = QCheckBox("Mostrar esta tela na próxima sessão"); self.startup.setChecked(False); p4.content.addWidget(self.startup); p4.content.addStretch(1)

        for page in (p0, p1, p2, p3, p4): self.pages.addWidget(page)

        nav = QHBoxLayout()
        self.back = QPushButton("Voltar"); self.next = QPushButton("Continuar")
        self.back.clicked.connect(self.go_back); self.next.clicked.connect(self.go_next)
        nav.addWidget(self.back); nav.addStretch(1); nav.addWidget(self.next); outer.addLayout(nav)
        self.setCentralWidget(root); self.update_nav()
        self.setStyleSheet("""
            QWidget#root { background: #111722; color: #f4f7fb; }
            QLabel#brand { font-size: 21px; font-weight: 700; letter-spacing: 5px; padding: 8px 4px 16px 4px; }
            QFrame#page { background: rgba(255,255,255,12); border: 1px solid rgba(255,255,255,24); border-radius: 22px; }
            QLabel#heading { font-size: 29px; font-weight: 700; }
            QLabel#body { font-size: 15px; color: rgba(236,242,251,190); }
            QPushButton { background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,28); border-radius: 11px; min-height: 38px; padding: 0 16px; color: #f5f8ff; }
            QPushButton:hover { background: rgba(105,168,255,55); }
            QPushButton:disabled { color: rgba(255,255,255,80); }
        """)

    def go_back(self):
        self.pages.setCurrentIndex(max(0, self.pages.currentIndex() - 1)); self.update_nav()

    def go_next(self):
        idx = self.pages.currentIndex()
        if idx < self.pages.count() - 1:
            self.pages.setCurrentIndex(idx + 1); self.update_nav(); return
        marker = Path.home() / ".config/flyos/welcome-complete-v6"
        marker.parent.mkdir(parents=True, exist_ok=True)
        if self.startup.isChecked(): marker.unlink(missing_ok=True)
        else: marker.touch()
        self.close()

    def update_nav(self):
        idx = self.pages.currentIndex(); self.back.setEnabled(idx > 0)
        self.next.setText("Concluir" if idx == self.pages.count() - 1 else "Continuar")


if __name__ == "__main__":
    marker = Path.home() / ".config/flyos/welcome-complete-v6"
    if "--force" not in sys.argv and marker.exists(): raise SystemExit(0)
    app = QApplication(sys.argv); win = FlyWelcome(); win.show(); raise SystemExit(app.exec())
