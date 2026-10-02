#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSlider, QSpinBox, QTimeEdit, QStackedWidget, QVBoxLayout, QWidget,
)


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(args, check=False, text=True, capture_output=capture)
    except FileNotFoundError:
        return None



def launch(*args: str) -> bool:
    """Start another UI/tool without blocking the Fly Center event loop."""
    try:
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except (FileNotFoundError, OSError):
        return False


def out(*args: str) -> str:
    p = run(*args, capture=True)
    return p.stdout.strip() if p else ""


def os_values() -> dict[str, str]:
    for path in (Path("/etc/os-release"), Path("/usr/lib/os-release")):
        try:
            values = {}
            for line in path.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    values[k] = v.strip().strip('"')
            if values:
                return values
        except OSError:
            pass
    return {"PRETTY_NAME": "Fly OS Developer Preview"}


from flyconfig import load_settings, save_settings


class Card(QFrame):
    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(18, 16, 18, 16)
        self.box.setSpacing(10)
        if title:
            label = QLabel(title); label.setObjectName("cardTitle"); self.box.addWidget(label)
        if subtitle:
            hint = QLabel(subtitle); hint.setWordWrap(True); hint.setObjectName("muted"); self.box.addWidget(hint)


class FlyCenter(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = load_settings()
        self.setWindowTitle("Fly Center")
        self.setWindowIcon(QIcon.fromTheme("flyos"))
        self.resize(1000, 680)
        self.setMinimumSize(850, 570)

        root = QWidget(); root.setObjectName("root")
        layout = QHBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        side = QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220)
        sb = QVBoxLayout(side); sb.setContentsMargins(16, 20, 16, 18); sb.setSpacing(10)
        brand = QLabel("✦  Fly Center"); brand.setObjectName("brand"); sb.addWidget(brand)
        desc = QLabel("Seu sistema, em um só lugar"); desc.setObjectName("muted"); sb.addWidget(desc)
        self.nav = QListWidget(); self.nav.setObjectName("nav")
        for icon, name in [
            ("preferences-desktop-theme", "Aparência"),
            ("battery", "Energia"),
            ("utilities-system-monitor", "Sistema"),
            ("preferences-desktop-peripherals", "Dispositivos"),
            ("security-high", "Privacidade"),
            ("preferences-desktop-accessibility", "Acessibilidade"),
            ("applications-games", "Gaming"),
            ("wine", "Windows"),
            ("document-save-all", "Backup & Recovery"),
            ("help-about", "Sobre"),
        ]:
            item = QListWidgetItem(QIcon.fromTheme(icon), name); self.nav.addItem(item)
        sb.addWidget(self.nav, 1)
        advanced = QPushButton("Configurações avançadas")
        advanced.clicked.connect(lambda: launch("systemsettings")); sb.addWidget(advanced)

        content = QFrame(); content.setObjectName("content")
        cb = QVBoxLayout(content); cb.setContentsMargins(28, 24, 28, 24); cb.setSpacing(14)
        self.page_title = QLabel("Aparência"); self.page_title.setObjectName("title"); cb.addWidget(self.page_title)
        self.page_hint = QLabel("Personalize o Fly OS sem perder consistência."); self.page_hint.setObjectName("subtitle"); cb.addWidget(self.page_hint)
        self.stack = QStackedWidget(); cb.addWidget(self.stack, 1)

        self.pages = [
            self.appearance_page(), self.energy_page(), self.system_page(), self.devices_page(), self.privacy_page(),
            self.accessibility_page(), self.gaming_page(), self.windows_page(), self.recovery_page(), self.about_page(),
        ]
        for page in self.pages: self.stack.addWidget(page)

        layout.addWidget(side); layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.nav.currentRowChanged.connect(self.change_page)
        self.nav.setCurrentRow(0)
        self.setStyleSheet(self.styles())

    def styles(self) -> str:
        return """
        QMainWindow, QWidget#root { background: #10141c; color: #f7f8fc; }
        QFrame#sidebar { background: rgba(255,255,255,0.035); border-right: 1px solid rgba(255,255,255,0.08); }
        QFrame#content { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #151a24, stop:1 #10141c); }
        QLabel#brand { font-size: 20px; font-weight: 700; }
        QLabel#title { font-size: 30px; font-weight: 750; }
        QLabel#subtitle, QLabel#muted { color: rgba(225,232,245,0.62); font-size: 12px; }
        QLabel#cardTitle { font-size: 15px; font-weight: 650; }
        QListWidget#nav { background: transparent; border: 0; outline: 0; }
        QListWidget#nav::item { border-radius: 11px; padding: 10px 10px; margin: 2px 0; }
        QListWidget#nav::item:hover { background: rgba(255,255,255,0.06); }
        QListWidget#nav::item:selected { background: rgba(124,174,255,0.20); border: 1px solid rgba(124,174,255,0.30); }
        QFrame#card { background: rgba(255,255,255,0.055); border: 1px solid rgba(255,255,255,0.09); border-radius: 18px; }
        QPushButton, QComboBox { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10); border-radius: 11px; min-height: 36px; padding: 0 13px; color: #f7f8fc; }
        QPushButton:hover { background: rgba(255,255,255,0.12); }
        QComboBox QAbstractItemView { background: #1d222d; color: #f7f8fc; selection-background-color: #3c5f92; }
        QCheckBox { spacing: 9px; }
        QSlider::groove:horizontal { height: 5px; background: rgba(255,255,255,0.12); border-radius: 2px; }
        QSlider::handle:horizontal { width: 17px; margin: -6px 0; border-radius: 8px; background: #7caeff; }
        """

    def change_page(self, row: int) -> None:
        titles = [
            ("Aparência", "Uma interface calma, consistente e adaptável."),
            ("Energia", "Desempenho quando precisa, eficiência quando não precisa."),
            ("Sistema", "Atualizações, saúde, apps e firmware em uma visão integrada."),
            ("Dispositivos", "Rede, áudio, monitores e periféricos sem procurar ferramentas separadas."),
            ("Privacidade", "Local-first por padrão e controles claros."),
            ("Acessibilidade", "Movimento, contraste e legibilidade adaptados a você."),
            ("Gaming", "Wine, GameMode, Gamescope e métricas sem tweaks permanentes."),
            ("Windows", "Compatibilidade Windows integrada ao desktop."),
            ("Backup & Recovery", "Se algo der errado, voltar atrás deve ser simples."),
            ("Sobre", "Identidade e arquitetura do Fly OS."),
        ]
        if 0 <= row < len(titles):
            self.stack.setCurrentIndex(row); self.page_title.setText(titles[row][0]); self.page_hint.setText(titles[row][1])

    def page(self) -> tuple[QWidget, QVBoxLayout]:
        p = QWidget(); l = QVBoxLayout(p); l.setContentsMargins(0, 8, 0, 0); l.setSpacing(13); return p, l

    def appearance_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Fly Glass", "Blur e transparência são reduzidos automaticamente no modo economia ou quando acessibilidade pede menos movimento.")
        row = QHBoxLayout()
        for label, profile in (("Glass", "glass"), ("Equilibrado", "balanced"), ("Performance", "performance")):
            b = QPushButton(label); b.clicked.connect(lambda _, v=profile: run("fly-glass", v)); row.addWidget(b)
        c.box.addLayout(row)
        self.blur = QSlider(Qt.Orientation.Horizontal); self.blur.setRange(1, 15); self.blur.setValue(9); self.blur.valueChanged.connect(self.set_blur)
        c.box.addWidget(QLabel("Intensidade do blur")); c.box.addWidget(self.blur); l.addWidget(c)

        c2 = Card("Tema e movimento", "O modo automático alterna claro/escuro localmente pelo horário; nenhuma localização é necessária.")
        row2 = QHBoxLayout()
        for label, mode in (("Automático", "auto"), ("Claro", "light"), ("Escuro", "dark")):
            b = QPushButton(label); b.clicked.connect(lambda _, v=mode: run("fly-theme", v)); row2.addWidget(b)
        c2.box.addLayout(row2)
        reduce = QCheckBox("Reduzir transparência e efeitos")
        reduce.setChecked(bool(self.cfg.get("reduce_transparency"))); reduce.toggled.connect(lambda v: self.set_cfg("reduce_transparency", v)); c2.box.addWidget(reduce)
        magnify = QCheckBox("Ampliação suave dos ícones do Dock")
        magnify.setChecked(bool(self.cfg.get("dock_magnification", True))); magnify.toggled.connect(lambda v: self.set_cfg("dock_magnification", v)); c2.box.addWidget(magnify)
        l.addWidget(c2)
        night = Card("Luz noturna", "Use o filtro de cor do próprio KWin. O Fly OS configura horário e temperatura sem precisar da sua localização.")
        night_row = QHBoxLayout()
        night_on = QPushButton("Ativar"); night_on.clicked.connect(lambda: run("fly-nightlight", "on")); night_row.addWidget(night_on)
        night_off = QPushButton("Desativar"); night_off.clicked.connect(lambda: run("fly-nightlight", "off")); night_row.addWidget(night_off)
        night.box.addLayout(night_row)
        schedule_row = QHBoxLayout()
        schedule_row.addWidget(QLabel("Começa")); evening = QTimeEdit(QTime(20, 0)); evening.setDisplayFormat("HH:mm"); schedule_row.addWidget(evening)
        schedule_row.addWidget(QLabel("Termina")); morning = QTimeEdit(QTime(7, 0)); morning.setDisplayFormat("HH:mm"); schedule_row.addWidget(morning)
        temp = QSpinBox(); temp.setRange(2500, 6500); temp.setSingleStep(100); temp.setValue(4000); temp.setSuffix(" K"); schedule_row.addWidget(temp)
        apply_night = QPushButton("Aplicar horário")
        apply_night.clicked.connect(lambda: run("fly-nightlight", "schedule", evening.time().toString("HH:mm"), morning.time().toString("HH:mm"), str(temp.value())))
        schedule_row.addWidget(apply_night); night.box.addLayout(schedule_row); l.addWidget(night)
        l.addStretch(1); return p

    def energy_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Perfis inteligentes", "Os perfis coordenam power-profiles-daemon, efeitos visuais e tarefas em segundo plano, sem alterar permanentemente o scheduler do kernel.")
        combo = QComboBox(); combo.addItems(["auto", "balanced", "performance", "power-saver", "gaming"])
        current = out("fly-profile", "mode") or "auto"; combo.setCurrentText(current if current in [combo.itemText(i) for i in range(combo.count())] else "auto")
        combo.currentTextChanged.connect(lambda v: run("fly-profile", v)); c.box.addWidget(combo)
        auto_hint = QLabel("Automático mantém Balanced normalmente e entra em economia na bateria abaixo de 35%; escolhas manuais não são sobrescritas.")
        auto_hint.setWordWrap(True); auto_hint.setObjectName("muted"); c.box.addWidget(auto_hint)
        adaptive = QCheckBox("Reduzir efeitos somente quando houver pressão real de recursos")
        adaptive.setChecked(bool(self.cfg.get("adaptive_performance", True))); adaptive.toggled.connect(lambda v: self.set_cfg("adaptive_performance", v)); c.box.addWidget(adaptive)
        battery_row = QHBoxLayout()
        battery = QPushButton("Dashboard de bateria"); battery.clicked.connect(lambda: launch("fly-battery-dashboard")); battery_row.addWidget(battery)
        care = QPushButton("Suporte a Battery Care"); care.clicked.connect(lambda: self.show_cmd("fly-battery", "status")); battery_row.addWidget(care)
        c.box.addLayout(battery_row)
        l.addWidget(c)
        c2 = Card("Memória responsiva", "Zram reduz travamentos sob pressão de RAM; PSI/systemd-oomd ficam disponíveis sem políticas agressivas específicas do Fly.")
        b = QPushButton("Abrir diagnóstico de memória"); b.clicked.connect(lambda: self.show_cmd("fly-doctor")); c2.box.addWidget(b); l.addWidget(c2); l.addStretch(1); return p

    def system_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Manutenção", "Atualização do sistema, firmware e apps sandboxados ficam coordenados por uma única camada Fly.")
        row = QHBoxLayout()
        for label, cmd in (("Atualizar", ("fly-update", "gui")), ("Saúde", ("fly-health",)), ("Aplicativos", ("fly-apps",)), ("Conectividade", ("fly-connect",)), ("Reindexar busca", ("fly-indexer",))):
            b = QPushButton(label); b.clicked.connect(lambda _, x=cmd: launch(*x)); row.addWidget(b)
        c.box.addLayout(row)
        row_tools = QHBoxLayout()
        activity = QPushButton("Fly Activity"); activity.clicked.connect(lambda: launch("fly-activity")); row_tools.addWidget(activity)
        storage = QPushButton("Armazenamento"); storage.clicked.connect(lambda: launch("fly-storage")); row_tools.addWidget(storage)
        startup = QPushButton("Itens de Inicialização"); startup.clicked.connect(lambda: launch("fly-login-items")); row_tools.addWidget(startup)
        support = QPushButton("Relatório de suporte"); support.clicked.connect(self.support_report); row_tools.addWidget(support)
        row_tools.addStretch(1); c.box.addLayout(row_tools); l.addWidget(c)
        defaults_card = Card("Aplicativos padrão", "Escolha navegador, PDF, imagens, vídeo, áudio e texto sem ficar preso aos apps que vierem na imagem.")
        defaults_btn = QPushButton("Abrir Fly Defaults"); defaults_btn.clicked.connect(lambda: launch("fly-defaults")); defaults_card.box.addWidget(defaults_btn); l.addWidget(defaults_card)
        c2 = Card("Sessão Fly nativa", "KWin é o compositor; Fly Shell fornece desktop, menu bar, dock, busca e quick settings. Plasma pode continuar instalado como fallback.")
        status = "Ativa" if os.environ.get("XDG_CURRENT_DESKTOP", "").startswith("FlyOS") else "Outra sessão está ativa"
        c2.box.addWidget(QLabel(f"Estado: {status}"))
        row2 = QHBoxLayout(); restart = QPushButton("Reiniciar Fly Shell"); restart.clicked.connect(lambda: run("systemctl", "--user", "restart", "fly-shell.service")); deep = QPushButton("Configuração avançada"); deep.clicked.connect(lambda: launch("systemsettings")); row2.addWidget(restart); row2.addWidget(deep); c2.box.addLayout(row2); l.addWidget(c2); l.addStretch(1); return p

    def devices_page(self) -> QWidget:
        p, l = self.page()
        from flyplatform import nm_primary_connection_name
        network = nm_primary_connection_name()
        active = next((line.split(":", 2)[-1] for line in network.splitlines() if ":connected:" in line), "Offline")
        c = Card("Conectividade", f"Conexão atual: {active}. O Fly Connect é a superfície principal para Wi‑Fi e Bluetooth.")
        row = QHBoxLayout()
        net = QPushButton("Abrir Fly Connect"); net.clicked.connect(lambda: launch("fly-connect")); row.addWidget(net)
        bluetooth = QPushButton("Bluetooth"); bluetooth.clicked.connect(lambda: launch("fly-bluetooth")); row.addWidget(bluetooth)
        airplane_state = out("fly-airplane", "status") if shutil.which("fly-airplane") else "off"
        airplane = QPushButton("Desativar modo avião" if airplane_state == "on" else "Modo avião")
        airplane.clicked.connect(lambda: run("fly-airplane", "toggle")); row.addWidget(airplane)
        share = QPushButton("KDE Connect"); share.clicked.connect(lambda: launch("kdeconnect-app")); row.addWidget(share)
        c.box.addLayout(row); l.addWidget(c)

        audio = Card("Áudio", "Volume e saída padrão usam PipeWire/WirePlumber; o controle rápido também fica disponível na barra do Fly Shell.")
        vol_text = out("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@") if shutil.which("wpctl") else ""
        match = re.search(r"Volume:\s+([0-9.]+)", vol_text)
        volume = int(float(match.group(1)) * 100) if match else 50
        slider = QSlider(Qt.Orientation.Horizontal); slider.setRange(0, 100); slider.setValue(max(0, min(100, volume)))
        slider.sliderReleased.connect(lambda: run("wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{slider.value()}%"))
        audio.box.addWidget(QLabel("Volume da saída padrão")); audio.box.addWidget(slider)
        row2 = QHBoxLayout()
        mute = QPushButton("Alternar mudo"); mute.clicked.connect(lambda: run("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")); row2.addWidget(mute)
        sound = QPushButton("Configuração avançada de áudio"); sound.clicked.connect(self.open_audio_settings); row2.addWidget(sound)
        audio.box.addLayout(row2); l.addWidget(audio)

        display = Card("Monitores e entrada", "O Fly OS mantém KWin/KScreen como camada de hardware para preservar HDR, escala fracionária, VRR e multi-monitor.")
        row3 = QHBoxLayout()
        screens = QPushButton("Monitores"); screens.clicked.connect(lambda: launch("systemsettings", "kcm_kscreen")); row3.addWidget(screens)
        inputb = QPushButton("Teclado e mouse"); inputb.clicked.connect(lambda: launch("systemsettings", "kcm_keyboard")); row3.addWidget(inputb)
        display.box.addLayout(row3); l.addWidget(display)
        graphics = Card("Gráficos híbridos", "Em notebooks com duas GPUs, o Fly OS pode executar um app na GPU dedicada sem mudar o sistema inteiro para alto consumo.")
        gpu = QPushButton("Abrir Fly GPU"); gpu.clicked.connect(lambda: launch("fly-gpu")); graphics.box.addWidget(gpu); l.addWidget(graphics)
        l.addStretch(1); return p

    def open_audio_settings(self) -> None:
        launch("fly-audio")

    def privacy_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Local-first", "Fly Search indexa apenas nomes e caminhos nas suas pastas pessoais. Conteúdo de arquivos não é lido e pesquisa online fica desligada por padrão.")
        online = QCheckBox("Permitir provedores de busca online no futuro")
        online.setChecked(bool(self.cfg.get("online_search", False))); online.toggled.connect(lambda v: self.set_cfg("online_search", v)); c.box.addWidget(online)
        dnd = QCheckBox("Não perturbe")
        dnd.setChecked(bool(self.cfg.get("dnd", False))); dnd.toggled.connect(self.toggle_dnd); c.box.addWidget(dnd)
        focus = QCheckBox("Focus Mode — reduzir interrupções")
        focus.setChecked(bool(self.cfg.get("focus_mode", False))); focus.toggled.connect(self.toggle_focus); c.box.addWidget(focus)
        clipboard = QCheckBox("Histórico temporário da área de transferência (apagado ao sair)")
        clipboard.setChecked(bool(self.cfg.get("clipboard_history", False))); clipboard.toggled.connect(self.toggle_clipboard); c.box.addWidget(clipboard)
        l.addWidget(c)
        c2 = Card("Proteções", "AppArmor, firewall, portals, firmware assinado e Secure Boot são verificados pelo Fly Health; telemetria própria do Fly permanece desativada por padrão.")
        row = QHBoxLayout(); privacy = QPushButton("Uso de câmera/microfone"); privacy.clicked.connect(lambda: launch("fly-privacy")); health = QPushButton("Fly Health"); health.clicked.connect(lambda: launch("fly-health")); firewall = QPushButton("Firewall"); firewall.clicked.connect(lambda: launch("fly-firewall")); row.addWidget(privacy); row.addWidget(health); row.addWidget(firewall); c2.box.addLayout(row); l.addWidget(c2); l.addStretch(1); return p

    def accessibility_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Conforto visual", "Esses controles afetam a própria experiência Fly sem exigir um tema separado ou reinicialização do computador.")
        motion = QCheckBox("Reduzir movimento e animações")
        motion.setChecked(bool(self.cfg.get("reduce_motion", False)))
        motion.toggled.connect(lambda v: self.set_cfg("reduce_motion", v)); c.box.addWidget(motion)
        transparency = QCheckBox("Reduzir transparência e blur")
        transparency.setChecked(bool(self.cfg.get("reduce_transparency", False)))
        transparency.toggled.connect(lambda v: self.set_cfg("reduce_transparency", v)); c.box.addWidget(transparency)
        contrast = QCheckBox("Alto contraste no Fly Shell")
        contrast.setChecked(bool(self.cfg.get("high_contrast", False)))
        contrast.toggled.connect(lambda v: self.set_cfg("high_contrast", v)); c.box.addWidget(contrast)
        scale = QSlider(Qt.Orientation.Horizontal); scale.setRange(90, 150); scale.setSingleStep(5)
        scale.setValue(int(float(self.cfg.get("text_scale", 1.0)) * 100))
        label = QLabel(f"Escala de texto do Fly Shell: {scale.value()}%")
        scale.valueChanged.connect(lambda v: label.setText(f"Escala de texto do Fly Shell: {v}%"))
        scale.sliderReleased.connect(lambda: self.set_cfg("text_scale", round(scale.value()/100.0, 2)))
        c.box.addWidget(label); c.box.addWidget(scale); l.addWidget(c)

        c2 = Card("Tecnologias assistivas", "O Fly OS não substitui leitores de tela maduros; ele integra as ferramentas Linux existentes e respeita preferências de movimento.")
        row = QHBoxLayout()
        reader = QPushButton("Leitor de tela")
        reader.clicked.connect(lambda: launch("orca") if shutil.which("orca") else QMessageBox.information(self, "Acessibilidade", "Orca não está instalado."))
        advanced = QPushButton("Mais opções")
        advanced.clicked.connect(lambda: launch("systemsettings", "kcm_access"))
        row.addWidget(reader); row.addWidget(advanced); c2.box.addLayout(row); l.addWidget(c2)
        l.addStretch(1); return p

    def gaming_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Modo Gaming", "Otimizações entram somente durante a sessão de jogo e são revertidas depois. GameMode evita manter a máquina permanentemente em alto consumo.")
        row = QHBoxLayout(); guide = QPushButton("Diagnóstico gaming"); guide.clicked.connect(lambda: self.show_cmd("fly-game", "--help")); perf = QPushButton("Ativar perfil Gaming"); perf.clicked.connect(lambda: run("fly-profile", "gaming")); row.addWidget(guide); row.addWidget(perf); c.box.addLayout(row); l.addWidget(c)
        c2 = Card("Compatibilidade", "Gamescope, MangoHud, NTSYNC e Wine/Proton podem ser usados sem alterar a sessão gráfica normal.")
        c2.box.addWidget(QLabel("Use 'fly-game <comando>' para iniciar um jogo com o perfil temporário.")); l.addWidget(c2); l.addStretch(1); return p

    def windows_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Fly Windows Compatibility", "O prefixo Fly fica separado em ~/.local/share/flyos/wine/default e pode ser reparado sem afetar todo o usuário.")
        row = QHBoxLayout(); cfg = QPushButton("Configurar Wine"); cfg.clicked.connect(lambda: launch("fly-wine")); repair = QPushButton("Reparar prefixo"); repair.clicked.connect(lambda: launch("fly-wine-repair")); row.addWidget(cfg); row.addWidget(repair); c.box.addLayout(row); l.addWidget(c); l.addStretch(1); return p

    def recovery_page(self) -> QWidget:
        p, l = self.page()
        c = Card("Recovery transacional", "Em Btrfs, atualizações grandes podem criar snapshots antes de mudar o sistema. Em ext4, o Fly mantém reparo APT/initramfs/GRUB sem fingir rollback atômico.")
        row = QHBoxLayout(); snap = QPushButton("Snapshots"); snap.clicked.connect(lambda: self.show_cmd("fly-snapshot", "status")); rec = QPushButton("Recovery"); rec.clicked.connect(lambda: launch("fly-recovery-ui")); update = QPushButton("Atualização segura"); update.clicked.connect(lambda: launch("fly-update", "gui")); row.addWidget(snap); row.addWidget(rec); row.addWidget(update); c.box.addLayout(row); l.addWidget(c)
        c2 = Card("Arquivos pessoais", "Snapshots do sistema não substituem backup. Kup/bup/rsync ficam disponíveis para cópias agendadas e Plasma Vault/gocryptfs para cofres privados.")
        backup = QPushButton("Abrir Backup"); backup.clicked.connect(lambda: launch("fly-backup")); c2.box.addWidget(backup); l.addWidget(c2); l.addStretch(1); return p

    def about_page(self) -> QWidget:
        p, l = self.page(); vals = os_values()
        c = Card("Fly OS", "Projeto open source com experiência própria sobre uma base Linux madura.")
        logo = QLabel("✦  FLY OS"); logo.setStyleSheet("font-size:34px;font-weight:800;letter-spacing:3px"); c.box.addWidget(logo)
        kernel = out("uname", "-r") or "desconhecido"
        text = QLabel(
            f"{vals.get('PRETTY_NAME', 'Fly OS')}\nKernel: {kernel}\nSessão: {os.environ.get('XDG_CURRENT_DESKTOP', 'desconhecida')}\n\n"
            "Fly OS mantém compatibilidade com pacotes Ubuntu, mas shell, sessão, identidade, tuning, busca, recovery, onboarding e UX pertencem ao projeto Fly. "
            "A inspiração em produtos Apple está em consistência, simplicidade e integração; nenhum ativo ou código proprietário da Apple é incluído."
        )
        text.setWordWrap(True); c.box.addWidget(text); l.addWidget(c); l.addStretch(1); return p


    def support_report(self) -> None:
        p = run("fly-support-report", capture=True)
        path = (p.stdout or "").strip() if p else ""
        if p and p.returncode == 0 and path:
            QMessageBox.information(self, "Relatório de suporte", f"Relatório criado em:\n{path}\n\nRevise o arquivo antes de compartilhar.")
        else:
            QMessageBox.warning(self, "Relatório de suporte", "Não foi possível criar o relatório.")

    def notify_shell_settings(self) -> None:
        # Avoid restarting the compositor-facing shell just to apply a small
        # preference. The shell also periodically reloads this tiny local file.
        run("fly-shellctl", "settings-reload")

    def set_cfg(self, key: str, value) -> None:
        self.cfg[key] = value
        save_settings(self.cfg)
        self.notify_shell_settings()

    def toggle_dnd(self, value: bool) -> None:
        self.cfg["dnd"] = value
        save_settings(self.cfg)
        self.notify_shell_settings()

    def toggle_focus(self, value: bool) -> None:
        self.cfg["focus_mode"] = value
        self.cfg["dnd"] = value
        save_settings(self.cfg)
        self.notify_shell_settings()

    def toggle_clipboard(self, value: bool) -> None:
        self.cfg["clipboard_history"] = value
        save_settings(self.cfg)
        if not value:
            run("fly-clipboard", "clear")
        self.notify_shell_settings()

    def set_blur(self, value: int) -> None:
        run("kwriteconfig6", "--file", "kwinrc", "--group", "Effect-blur", "--key", "BlurStrength", str(value))
        run("kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "blurEnabled", "true")
        try:
            from flyplatform import kwin_reconfigure
            kwin_reconfigure()
        except Exception:
            pass

    def show_cmd(self, *argv: str) -> None:
        if not shutil.which(argv[0]):
            QMessageBox.information(self, "Fly Center", f"{argv[0]} não está disponível nesta instalação."); return
        p = run(*argv, capture=True)
        text = ((p.stdout or "") + (p.stderr or "")) if p else ""
        QMessageBox.information(self, "Fly Center", text.strip()[:5000] or "Operação concluída.")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Fly Center")
    window = FlyCenter(); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
