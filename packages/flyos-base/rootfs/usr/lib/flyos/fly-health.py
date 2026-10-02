#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget


def out(*args: str, timeout: int = 4) -> str:
    try:
        return subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


class Health(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fly Health")
        self.resize(760, 620)
        root = QWidget()
        self.box = QVBoxLayout(root)
        self.box.setContentsMargins(24, 24, 24, 24)
        self.box.setSpacing(12)
        title = QLabel("Fly Health")
        title.setStyleSheet("font-size:28px;font-weight:700")
        self.box.addWidget(title)
        sub = QLabel("Sessão, hardware, segurança, atualizações, memória e recuperação em uma visão única.")
        sub.setStyleSheet("color:#9da7b8")
        self.box.addWidget(sub)
        self.cards = QVBoxLayout()
        self.box.addLayout(self.cards)
        row = QHBoxLayout()
        refresh = QPushButton("Atualizar diagnóstico")
        refresh.clicked.connect(self.refresh)
        updates = QPushButton("Abrir atualizações")
        updates.clicked.connect(lambda: subprocess.Popen(["fly-update", "gui"]))
        recovery = QPushButton("Abrir recovery")
        recovery.clicked.connect(lambda: subprocess.Popen(["fly-recovery-ui"]))
        row.addWidget(refresh); row.addWidget(updates); row.addWidget(recovery)
        self.box.addLayout(row)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#151922;color:#f4f7fb}
            QFrame{background:#1d222d;border:1px solid #303847;border-radius:14px}
            QPushButton{background:#272e3a;border:1px solid #3a4555;border-radius:10px;padding:9px 13px}
            QPushButton:hover{background:#303947}
        """)
        self.refresh()

    def add_card(self, title: str, value: str, detail: str = ""):
        card = QFrame(); row = QHBoxLayout(card); row.setContentsMargins(16, 13, 16, 13)
        left = QVBoxLayout(); t = QLabel(title); t.setStyleSheet("font-weight:650")
        d = QLabel(detail); d.setWordWrap(True); d.setStyleSheet("color:#9da7b8;font-size:11px")
        left.addWidget(t); left.addWidget(d)
        v = QLabel(value); v.setStyleSheet("font-weight:700")
        row.addLayout(left, 1); row.addWidget(v)
        self.cards.addWidget(card)

    def clear_cards(self):
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def refresh(self):
        self.clear_cards()
        secure = out("mokutil", "--sb-state") if exists("mokutil") else ""
        self.add_card("Secure Boot", "Ativo" if "enabled" in secure.lower() else "Indisponível/Desativado", secure or "mokutil não disponível")

        tpm = Path("/sys/class/tpm/tpm0").exists()
        self.add_card("TPM", "Detectado" if tpm else "Não detectado", "Usado por recursos de segurança suportados pelo hardware, incluindo opções de criptografia vinculadas ao TPM.")

        encrypted = False
        if exists("lsblk"):
            chain = out("lsblk", "-s", "-n", "-o", "TYPE", "/")
            encrypted = any(line.strip() == "crypt" for line in chain.splitlines())
        self.add_card("Criptografia do sistema", "Detectada" if encrypted else "Não confirmada", "Detecção conservadora pela cadeia de dispositivos; confirme detalhes no instalador/recovery antes de assumir proteção completa.")

        aa = out("systemctl", "is-active", "apparmor.service") if exists("systemctl") else ""
        self.add_card("AppArmor", "Ativo" if aa == "active" else aa or "Desconhecido", "Confinamento obrigatório de aplicações e serviços.")

        ufw_state = out("systemctl", "is-enabled", "ufw.service") if exists("systemctl") else ""
        self.add_card("Firewall", "Habilitado" if ufw_state == "enabled" else (ufw_state or "Indisponível"), "Fly OS permite KDE Connect na rede local e bloqueia conexões de entrada não solicitadas.")

        swap = out("swapon", "--show=NAME,TYPE,SIZE", "--noheadings") if exists("swapon") else ""
        zram = next((line.strip() for line in swap.splitlines() if "zram" in line), "")
        self.add_card("Memória comprimida", "ZRAM ativo" if zram else "Não detectado", zram or "Será ativado quando systemd-zram-generator estiver disponível.")

        rootfs = out("findmnt", "-n", "-o", "FSTYPE", "/") if exists("findmnt") else ""
        self.add_card("Sistema de arquivos", rootfs or "Desconhecido", "Btrfs habilita snapshots rápidos pelo Fly Recovery; ext4 continua totalmente suportado.")

        ntsync = Path("/dev/ntsync").exists() or Path("/sys/module/ntsync").exists()
        self.add_card("Windows Gaming Sync", "NTSYNC disponível" if ntsync else "Não detectado", "Quando suportado pelo kernel, Wine/Proton podem usar primitivas de sincronização do Windows mais eficientes.")

        session = os.environ.get("XDG_SESSION_TYPE", "desconhecida")
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "desconhecido")
        self.add_card("Sessão gráfica", f"{desktop} / {session.upper()}", "A sessão Fly nativa usa KWin Wayland sem exigir plasmashell.")

        shell_state = out("systemctl", "--user", "is-active", "fly-shell.service") if exists("systemctl") else ""
        self.add_card("Fly Shell", "Ativo" if shell_state == "active" else (shell_state or "Não detectado"), "Desktop, menu bar, dock, busca, OSD, mídia e quick settings do Fly OS.")

        perf_state = out("systemctl", "--user", "is-active", "fly-performance-monitor.service") if exists("systemctl") else ""
        perf_file = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "fly-performance.json"
        perf_detail = "Monitor local via procfs/PSI; não envia métricas e não altera scheduler/governor."
        perf_value = "Ativo" if perf_state == "active" else (perf_state or "Não detectado")
        try:
            import json
            pdata=json.loads(perf_file.read_text(encoding="utf-8"))
            perf_value=f"{pdata.get('state','normal')} • CPU {pdata.get('cpu_percent',0)}% • RAM {pdata.get('memory_percent',0)}%"
        except (OSError, ValueError, TypeError):
            pass
        self.add_card("Fly Performance", perf_value, perf_detail)

        components = ["flyos-core", "flyos-shell", "flyos-center", "flyos-search", "flyos-update", "flyos-recovery", "flyos-privacy", "flyos-performance", "flyos-wine", "flyos-branding", "flyos-repo"]
        if exists("dpkg-query"):
            installed = []
            missing = []
            for pkg in components:
                state = out("dpkg-query", "-W", "-f=${db:Status-Status}", pkg, timeout=1)
                (installed if state == "installed" else missing).append(pkg.removeprefix("flyos-"))
            value = f"{len(installed)}/{len(components)} componentes"
            detail = "Instalados: " + ", ".join(installed)
            if missing:
                detail += ". Ausentes: " + ", ".join(missing)
            self.add_card("Plataforma modular", value, detail)

        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            disk_value = f"{free_gb:.1f} GB livres"
        except OSError:
            disk_value = "Desconhecido"
        self.add_card("Armazenamento", disk_value, "O Fly Update alerta para pouco espaço antes de upgrades maiores.")

        index = Path.home() / ".cache/flyos/search.db"
        if index.exists():
            size = index.stat().st_size / (1024**2)
            index_value = f"Local ({size:.1f} MB)"
        else:
            index_value = "Ainda não criado"
        self.add_card("Fly Search", index_value, "Índice local apenas de nomes/caminhos; conteúdo dos arquivos não é enviado nem lido.")

        threshold = []
        for bat in Path("/sys/class/power_supply").glob("BAT*"):
            for name in ("charge_control_end_threshold", "charge_stop_threshold"):
                node = bat / name
                if node.exists():
                    try: threshold.append(node.read_text().strip() + "%")
                    except OSError: pass
        self.add_card("Battery Care", ", ".join(threshold) if threshold else "Não suportado pelo firmware", "O limite de carga só é oferecido quando o hardware expõe uma interface segura.")

        upgrades = ""
        if exists("apt"):
            text = out("apt", "list", "--upgradable", timeout=8)
            count = max(0, len([x for x in text.splitlines() if x and not x.startswith("Listing")]))
            upgrades = str(count)
        self.add_card("Atualizações APT", upgrades or "?", "Quantidade aproximada de pacotes atualizáveis.")

        offline = Path("/system-update").is_symlink()
        state_file = Path("/var/lib/flyos/offline-update/state")
        state = "idle"
        try:
            for line in state_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("state="):
                    state = line.split("=", 1)[1]
        except OSError:
            pass
        self.add_card("Atualização offline", "Preparada" if offline else state, "Pacotes do sistema podem ser aplicados no boot com a sessão gráfica parada.")

        failed = out("systemctl", "--failed", "--no-legend", timeout=3) if exists("systemctl") else ""
        failed_count = len([x for x in failed.splitlines() if x.strip()])
        self.add_card("Serviços do sistema", "OK" if failed_count == 0 else f"{failed_count} com falha", "Use Fly Recovery para logs e reparo se houver serviços falhando.")

        fw = "Suportado" if exists("fwupdmgr") else "Não instalado"
        self.add_card("Firmware", fw, "fwupd/LVFS integra firmware suportado ao fluxo de atualização.")


app = QApplication(sys.argv)
w = Health(); w.show()
sys.exit(app.exec())
