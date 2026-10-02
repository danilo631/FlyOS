#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal Fly UI shown only when the main shell enters a crash loop."""
from __future__ import annotations

import shutil
import subprocess
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget


def spawn(argv: list[str]) -> None:
    try:
        subprocess.Popen(argv, start_new_session=True)
    except OSError as exc:
        QMessageBox.warning(None, "Fly Rescue UI", str(exc))


class Rescue(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fly OS — Safe UI")
        self.resize(520, 430)
        root = QWidget(); box = QVBoxLayout(root)
        box.setContentsMargins(34, 30, 34, 30); box.setSpacing(12)
        title = QLabel("Fly Shell precisa de atenção")
        title.setStyleSheet("font-size:26px;font-weight:750")
        box.addWidget(title)
        detail = QLabel(
            "A sessão gráfica continua ativa, mas o shell principal falhou repetidamente. "
            "Você pode reiniciá-lo em modo seguro, abrir as configurações ou sair da sessão."
        )
        detail.setWordWrap(True); detail.setStyleSheet("color:rgba(225,232,245,.72);font-size:13px")
        box.addWidget(detail)

        restart = QPushButton("Reiniciar Fly Shell em modo seguro")
        restart.clicked.connect(self.restart_safe); box.addWidget(restart)
        normal = QPushButton("Tentar novamente no modo normal")
        normal.clicked.connect(self.restart_normal); box.addWidget(normal)
        reset = QPushButton("Restaurar configurações do Fly Shell")
        reset.clicked.connect(self.reset_shell); box.addWidget(reset)
        center = QPushButton("Abrir Fly Center")
        center.clicked.connect(lambda: spawn(["fly-center"])); box.addWidget(center)
        health = QPushButton("Abrir diagnóstico")
        health.clicked.connect(lambda: spawn(["fly-health"])); box.addWidget(health)
        if shutil.which("konsole"):
            terminal = QPushButton("Abrir terminal")
            terminal.clicked.connect(lambda: spawn(["konsole"])); box.addWidget(terminal)
        logout = QPushButton("Encerrar sessão")
        logout.clicked.connect(self.logout); box.addWidget(logout)
        box.addStretch(1)
        hint = QLabel("Este painel é independente do QML principal para continuar disponível durante falhas do Fly Shell.")
        hint.setWordWrap(True); hint.setStyleSheet("color:rgba(225,232,245,.55);font-size:11px")
        box.addWidget(hint)
        self.setCentralWidget(root)
        self.setStyleSheet('''
            QMainWindow,QWidget{background:#11161f;color:#f7f8fc}
            QPushButton{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);border-radius:12px;min-height:44px;padding:0 14px;color:#f7f8fc;text-align:left}
            QPushButton:hover{background:rgba(124,174,255,.20)}
        ''')

    def _restart_shell(self, safe: bool) -> None:
        env_cmd = "set-environment" if safe else "unset-environment"
        args = ["systemctl", "--user", env_cmd, "FLYOS_SAFE_MODE=1"] if safe else ["systemctl", "--user", env_cmd, "FLYOS_SAFE_MODE"]
        subprocess.run(args, check=False)
        subprocess.run(["systemctl", "--user", "reset-failed", "fly-shell.service"], check=False)
        result = subprocess.run(["systemctl", "--user", "start", "fly-shell.service"], check=False)
        if result.returncode == 0:
            self.close()
        else:
            QMessageBox.warning(self, "Fly Rescue UI", "O shell ainda não conseguiu iniciar. Use Fly Health ou o terminal para diagnóstico.")

    def restart_safe(self) -> None:
        self._restart_shell(True)

    def restart_normal(self) -> None:
        self._restart_shell(False)

    def reset_shell(self) -> None:
        reply = QMessageBox.question(
            self,
            "Fly Rescue UI",
            "Restaurar as configurações do Fly Shell? O arquivo atual será preservado como backup e o shell iniciará em modo seguro.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        result = subprocess.run(["fly-shellctl", "reset"], check=False, capture_output=True, text=True)
        if result.returncode == 0:
            self.close()
        else:
            QMessageBox.warning(self, "Fly Rescue UI", result.stderr.strip() or "Não foi possível restaurar o Fly Shell.")

    def logout(self) -> None:
        session = __import__('os').environ.get("XDG_SESSION_ID", "")
        if session and shutil.which("loginctl"):
            spawn(["loginctl", "terminate-session", session])
        else:
            subprocess.run(["systemctl", "--user", "stop", "flyos-session.target"], check=False)
        self.close()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Fly Rescue UI")
    window = Rescue(); window.show(); window.raise_(); window.activateWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
