#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QScrollArea, QTextEdit,
    QVBoxLayout, QWidget,
)


@dataclass(frozen=True)
class App:
    name: str
    ident: str
    category: str
    description: str
    backend: str = "apt"


CURATED = [
    App("Krita", "krita", "Criatividade", "Pintura e ilustração digital"),
    App("GIMP", "gimp", "Criatividade", "Edição avançada de imagens"),
    App("Kdenlive", "kdenlive", "Criatividade", "Editor de vídeo não linear"),
    App("OBS Studio", "obs-studio", "Criatividade", "Gravação e transmissão ao vivo"),
    App("Blender", "blender", "Criatividade", "Modelagem, animação e renderização 3D"),
    App("VLC", "vlc", "Mídia", "Reprodutor multimídia"),
    App("Audacity", "audacity", "Mídia", "Edição e gravação de áudio"),
    App("LibreOffice", "libreoffice", "Produtividade", "Suíte de documentos e planilhas"),
    App("Kate", "kate", "Desenvolvimento", "Editor de texto e código"),
    App("FileZilla", "filezilla", "Desenvolvimento", "Cliente FTP/SFTP"),
]


def run(argv: list[str], timeout: int = 5) -> str:
    try:
        return subprocess.run(
            argv, check=False, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=timeout,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def installed(app: App) -> bool:
    if app.backend == "flatpak":
        return bool(run(["flatpak", "info", "--user", app.ident], 2).strip()) if shutil.which("flatpak") else False
    return run(["dpkg-query", "-W", "-f=${db:Status-Status}", app.ident], 2).strip() == "installed"


def apt_search(query: str, limit: int = 28) -> list[App]:
    if not shutil.which("apt-cache") or len(query.strip()) < 2:
        return []
    text = run(["apt-cache", "search", "--names-only", query.strip()], 6)
    apps: list[App] = []
    for line in text.splitlines():
        package, sep, description = line.partition(" - ")
        package = package.strip()
        if not sep or not package or package.startswith(("lib", "linux-", "gir1.2-", "python3-")):
            continue
        apps.append(App(package, package, "Repositório APT", description.strip() or "Pacote do sistema"))
        if len(apps) >= limit:
            break
    return apps


def flatpak_search(query: str, limit: int = 16) -> list[App]:
    if not shutil.which("flatpak") or len(query.strip()) < 2:
        return []
    text = run(["flatpak", "search", "--columns=application,name,description", query.strip()], 8)
    apps: list[App] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        ident, name = parts[0].strip(), parts[1].strip()
        if not ident or "." not in ident:
            continue
        desc = parts[2].strip() if len(parts) > 2 else "Aplicativo Flatpak"
        apps.append(App(name or ident, ident, "Flatpak", desc, "flatpak"))
        if len(apps) >= limit:
            break
    return apps


def operation_command(app: App, remove: bool) -> tuple[str, list[str]] | None:
    if app.backend == "flatpak":
        if not shutil.which("flatpak"):
            return None
        verb = "uninstall" if remove else "install"
        args = [verb, "--user", "--noninteractive", "-y"]
        if not remove:
            args.append("flathub")
        args.append(app.ident)
        return "flatpak", args
    if shutil.which("pkexec") and Path("/usr/lib/flyos/fly-package-helper").exists():
        return "pkexec", ["/usr/lib/flyos/fly-package-helper", "remove" if remove else "install", app.ident]
    return None


class Row(QFrame):
    def __init__(self, app: App, owner):
        super().__init__()
        self.app = app; self.owner = owner
        self.setObjectName("card")
        layout = QHBoxLayout(self); layout.setContentsMargins(16, 13, 16, 13)
        column = QVBoxLayout(); top = QHBoxLayout()
        name = QLabel(app.name); name.setObjectName("appName")
        badge = QLabel(app.backend.upper()); badge.setObjectName("badge")
        top.addWidget(name); top.addWidget(badge); top.addStretch(1)
        desc = QLabel(app.description); desc.setObjectName("muted"); desc.setWordWrap(True)
        ident = QLabel(app.ident); ident.setObjectName("package")
        column.addLayout(top); column.addWidget(desc); column.addWidget(ident)
        layout.addLayout(column, 1)
        self.button = QPushButton(); self.button.clicked.connect(self.action); layout.addWidget(self.button)
        self.refresh()

    def refresh(self) -> None:
        self.button.setEnabled(not self.owner.busy)
        self.button.setText("Remover" if installed(self.app) else "Instalar")

    def action(self) -> None:
        self.owner.start_operation(self.app, installed(self.app))


class FlyApps(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fly Apps"); self.resize(900, 730)
        self.results = list(CURATED)
        self.process: QProcess | None = None
        self.busy = False

        root = QWidget(); box = QVBoxLayout(root); box.setContentsMargins(26, 22, 26, 22); box.setSpacing(12)
        title = QLabel("Fly Apps"); title.setObjectName("title"); box.addWidget(title)
        sub = QLabel(
            "Instale programas sem sair da experiência Fly. APT usa um helper Fly mínimo autenticado por PolicyKit; "
            "Flatpak funciona no escopo do usuário. Operações e erros aparecem aqui, sem abrir terminal."
        )
        sub.setWordWrap(True); sub.setObjectName("muted"); box.addWidget(sub)

        tools = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar aplicativo ou pacote…")
        self.search.returnPressed.connect(self.repository_search); tools.addWidget(self.search, 1)
        search_repo = QPushButton("Buscar"); search_repo.clicked.connect(self.repository_search); tools.addWidget(search_repo)
        reload_btn = QPushButton("Recarregar"); reload_btn.clicked.connect(self.reload); tools.addWidget(reload_btn)
        box.addLayout(tools)

        source_row = QHBoxLayout()
        curated = QPushButton("Recomendados"); curated.clicked.connect(self.show_curated); source_row.addWidget(curated)
        full = QPushButton("Catálogo avançado"); full.clicked.connect(self.full_catalog); source_row.addWidget(full)
        flathub = QPushButton("Ativar Flathub"); flathub.clicked.connect(self.enable_flathub); source_row.addWidget(flathub)
        source_row.addStretch(1); box.addLayout(source_row)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame); box.addWidget(self.scroll, 1)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.setVisible(False); box.addWidget(self.progress)
        self.status = QLabel("Recomendados do Fly OS"); self.status.setObjectName("muted"); box.addWidget(self.status)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(110); self.log.setVisible(False); box.addWidget(self.log)
        self.setCentralWidget(root)
        self.setStyleSheet('''
            QMainWindow,QWidget{background:#11161f;color:#f7f8fc}
            QLabel#title{font-size:30px;font-weight:750}
            QLabel#muted,QLabel#package{color:rgba(225,232,245,.65)}
            QLabel#package{font-size:10px} QLabel#badge{font-size:9px;font-weight:700;color:#9fc1ff}
            QFrame#card{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.09);border-radius:16px}
            QLabel#appName{font-size:15px;font-weight:650}
            QPushButton,QLineEdit,QTextEdit{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:10px;min-height:36px;padding:0 12px;color:#f7f8fc}
            QPushButton:hover{background:rgba(124,174,255,.2)}
            QPushButton:disabled{color:rgba(225,232,245,.35)}
            QProgressBar{border:0;background:rgba(255,255,255,.08);border-radius:5px;min-height:8px;max-height:8px;text-align:center}
            QProgressBar::chunk{background:#7caeff;border-radius:5px}
        ''')
        self.populate()

    def populate(self) -> None:
        holder = QWidget(); layout = QVBoxLayout(holder); layout.setContentsMargins(0, 4, 0, 4); layout.setSpacing(9)
        for app in self.results:
            layout.addWidget(Row(app, self))
        if not self.results:
            label = QLabel("Nenhum resultado encontrado."); label.setObjectName("muted"); layout.addWidget(label)
        layout.addStretch(1); self.scroll.setWidget(holder)

    def set_busy(self, value: bool) -> None:
        self.busy = value; self.progress.setVisible(value); self.populate()

    def start_operation(self, app: App, remove: bool) -> None:
        if self.busy:
            QMessageBox.information(self, "Fly Apps", "Já existe uma operação em andamento."); return
        command = operation_command(app, remove)
        if not command:
            QMessageBox.warning(self, "Fly Apps", "Nenhum backend de instalação disponível."); return
        program, args = command
        action = "Removendo" if remove else "Instalando"
        self.status.setText(f"{action} {app.name}…")
        self.log.clear(); self.log.setVisible(True); self.set_busy(True)
        self.process = QProcess(self)
        self.process.setProgram(program); self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.finished.connect(lambda code, _status: self.operation_done(code, app, remove))
        self.process.start()

    def process_output(self) -> None:
        if not self.process: return
        chunk = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        if chunk:
            cursor = self.log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log.setTextCursor(cursor)
            self.log.insertPlainText(chunk[-5000:])
            self.log.ensureCursorVisible()

    def operation_done(self, code: int, app: App, remove: bool) -> None:
        self.set_busy(False)
        if code == 0:
            self.status.setText(f"{app.name} {'removido' if remove else 'instalado'} com sucesso.")
        else:
            self.status.setText(f"A operação com {app.name} falhou (código {code}).")
            QMessageBox.warning(self, "Fly Apps", "Não foi possível concluir a operação. Veja os detalhes na própria janela.")
        self.populate()

    def show_curated(self) -> None:
        self.results = list(CURATED); self.status.setText("Recomendados do Fly OS"); self.populate()

    def reload(self) -> None:
        self.populate(); self.status.setText("Estado de instalação recarregado.")

    def repository_search(self) -> None:
        q = self.search.text().strip()
        if len(q) < 2:
            self.show_curated(); return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        apt: list[App] = []; flat: list[App] = []
        try:
            apt = apt_search(q); flat = flatpak_search(q)
            seen = set(); combined = []
            for app in apt + flat:
                key = (app.backend, app.ident)
                if key not in seen:
                    combined.append(app); seen.add(key)
            self.results = combined
        finally:
            QApplication.restoreOverrideCursor()
        self.status.setText(f"{len(self.results)} resultado(s) para “{q}” — {len(apt)} APT, {len(flat)} Flatpak")
        self.populate()

    def full_catalog(self) -> None:
        if shutil.which("plasma-discover"):
            subprocess.Popen(["plasma-discover"], start_new_session=True)
        else:
            QMessageBox.information(self, "Fly Apps", "A pesquisa APT/Flatpak continua disponível aqui. O catálogo avançado é opcional.")

    def enable_flathub(self) -> None:
        if not shutil.which("flatpak"):
            QMessageBox.information(self, "Fly Apps", "Flatpak não está instalado."); return
        app = App("Flathub", "https://flathub.org/repo/flathub.flatpakrepo", "Fonte", "Catálogo Flathub", "flatpak-source")
        if self.busy: return
        self.status.setText("Ativando Flathub…"); self.log.clear(); self.log.setVisible(True); self.set_busy(True)
        self.process = QProcess(self); self.process.setProgram("flatpak")
        self.process.setArguments(["remote-add", "--user", "--if-not-exists", "flathub", app.ident])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.finished.connect(lambda code, _status: self.flathub_done(code))
        self.process.start()

    def flathub_done(self, code: int) -> None:
        self.set_busy(False)
        self.status.setText("Flathub ativado para este usuário." if code == 0 else "Não foi possível ativar o Flathub.")


def main() -> int:
    app = QApplication(sys.argv)
    window = FlyApps(); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
