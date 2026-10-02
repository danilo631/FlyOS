#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fly Shell - user-facing shell layer for Fly OS.

KWin remains the Wayland compositor. Fly Shell owns the desktop surface, top
bar, dock, launcher/universal search and quick settings. The implementation is
kept deliberately small and auditable; hardware-facing operations are delegated
to stable system interfaces (NetworkManager, WirePlumber, power-profiles-daemon,
systemd/logind) instead of vendor-specific tweaks.
"""

from __future__ import annotations

import ast
import configparser
import json
import os
import re
import shlex
import shutil
import sqlite3
import time
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QFileSystemWatcher, QObject, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

APP_DIRS = [
    Path.home() / ".local/share/applications",
    Path.home() / ".local/share/flatpak/exports/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    Path("/var/lib/snapd/desktop/applications"),
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
]
FIELD_CODE = re.compile(r"%[fFuUdDnNickvm]")
SEARCH_DB = Path.home() / ".cache/flyos/search.db"
NOTIFICATION_FILE_NAME = "fly-notifications.json"
NOTIFICATION_COMMAND_NAME = "fly-notification-command"
PRIVACY_FILE_NAME = "fly-privacy.json"
PERFORMANCE_FILE_NAME = "fly-performance.json"
AIRPLANE_STATE_FILE = Path.home() / ".local/state/flyos/airplane.json"
USAGE_FILE = Path.home() / ".local/state/flyos/app-usage.json"


def popen(argv: list[str], *, quiet: bool = True) -> subprocess.Popen | None:
    try:
        return subprocess.Popen(
            argv,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
            start_new_session=True,
        )
    except (OSError, ValueError):
        return None


def output(argv: list[str], timeout: float = 2.0) -> str:
    try:
        return subprocess.run(
            argv,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


from flyconfig import load_settings, save_settings
from flyplatform import (
    audio_endpoints, audio_set_default, audio_toggle_mute, audio_volume,
    bluez_powered, bluez_set_powered, brightness_percent, media_action, media_state,
    nm_primary_connection_name, nm_radio, nm_set_radio, notify,
    kwin_call, kwin_current_desktop, kwin_reconfigure, kwin_toggle_overview, kwin_workspace,
    set_brightness_percent,
)


@dataclass
class DesktopApp:
    desktop_id: str
    name: str
    icon: str
    path: str
    exec_line: str
    keywords: str

    def result(self) -> dict[str, str]:
        return {
            "kind": "app",
            "id": self.desktop_id,
            "name": self.name,
            "subtitle": "Aplicativo",
            "icon": self.icon or "application-x-executable",
            "target": self.desktop_id,
        }


ACTIONS = [
    ("Fly Center", "Configurações integradas do Fly OS", "preferences-system", "center", "configurações settings aparência energia sistema"),
    ("Atualizar sistema", "APT, Flatpak, firmware e snapshot", "system-software-update", "update", "update atualizar atualização upgrade pacotes"),
    ("Saúde do sistema", "Diagnóstico de segurança, drivers e memória", "utilities-system-monitor", "health", "health saúde diagnóstico doctor"),
    ("Recovery", "Snapshots, reparo APT e boot", "document-revert", "recovery", "recovery recuperar snapshot rollback boot grub"),
    ("Backup", "Backup dos seus arquivos pessoais", "document-save-all", "backup", "backup cópia segurança arquivos"),
    ("Windows / Wine", "Executar e configurar aplicativos Windows", "wine", "wine", "wine windows exe compatibilidade"),
    ("Terminal", "Abrir terminal", "utilities-terminal", "terminal", "terminal konsole shell linha comando"),
    ("Visão geral", "Janelas e áreas de trabalho", "view-grid", "overview", "overview visão geral janelas desktop workspace"),
    ("Captura de tela", "Capturar a tela", "fly-screenshot", "screenshot", "screenshot captura tela print"),
    ("Bloquear", "Bloquear a sessão", "system-lock-screen", "lock", "lock bloquear segurança"),
    ("Aplicativos", "Instalar e remover programas", "system-software-install", "apps", "apps aplicativos loja software flatpak"),
    ("Área de transferência", "Histórico temporário desta sessão", "edit-paste", "clipboard", "clipboard colar copiar área transferência histórico"),
    ("Arquivos", "Navegar, abrir, renomear e mover para lixeira", "system-file-manager", "files", "arquivos files documentos downloads pastas"),
    ("Áudio", "Saída, entrada, volume e microfone", "audio-volume-high", "audio", "audio som volume microfone headset hdmi"),
    ("Firewall", "Proteção de conexões de entrada", "security-high", "firewall", "firewall ufw segurança rede proteção"),
    ("Wi-Fi e rede", "Conectar, esquecer e editar redes", "network-wireless", "network", "wifi wi-fi rede internet ethernet conexão"),
    ("Bluetooth", "Parear e gerenciar dispositivos", "bluetooth", "bluetooth", "bluetooth fone mouse teclado parear dispositivo"),
    ("Modo avião", "Desativar rádios e restaurá-los depois", "network-wireless-offline", "airplane", "modo avião airplane offline wifi bluetooth rádio"),
    ("Bateria", "Saúde, consumo e Battery Care", "battery", "battery", "battery bateria saúde carga energia autonomia"),
    ("GPU híbrida", "Executar apps na GPU dedicada", "video-display", "gpu", "gpu gráficos nvidia amd intel dedicada hybrid"),
    ("Privacidade", "Uso local de câmera e microfone", "security-high", "privacy", "privacidade câmera camera microfone permissões"),
    ("Atividade", "CPU, memória, pressão e processos", "utilities-system-monitor", "activity", "cpu ram memória processos atividade desempenho psi"),
    ("Armazenamento", "Uso de disco e limpeza segura", "drive-harddisk", "storage", "armazenamento disco cache lixeira espaço limpeza"),
    ("Itens de Inicialização", "Controle os apps que iniciam com a sessão", "system-run", "login-items", "inicialização startup autostart login sessão apps"),
    ("Aplicativos padrão", "Escolha navegador, mídia, PDF e texto", "preferences-desktop-default-applications", "defaults", "padrão default navegador pdf vídeo audio texto"),
    ("Relatório de suporte", "Diagnóstico local com dados sensíveis reduzidos", "help-about", "support", "suporte relatório diagnóstico log bug ajuda"),
]


_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}
_ALLOWED_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}

def calculate_expression(text: str) -> str | None:
    """Evaluate a tiny arithmetic grammar for launcher calculations."""
    raw = text.strip().replace(",", ".")
    if not raw or len(raw) > 80 or not re.fullmatch(r"[0-9eE+\-*/%(). \t]+", raw):
        return None
    try:
        tree = ast.parse(raw, mode="eval")
    except SyntaxError:
        return None
    def walk(node: ast.AST, depth: int = 0) -> float | int:
        if depth > 12:
            raise ValueError
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            value = node.value
            if abs(float(value)) > 1e15:
                raise ValueError
            return value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = walk(node.left, depth + 1); right = walk(node.right, depth + 1)
            if isinstance(node.op, ast.Pow) and abs(float(right)) > 12:
                raise ValueError
            value = _ALLOWED_BINOPS[type(node.op)](left, right)
            if abs(float(value)) > 1e18:
                raise ValueError
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](walk(node.operand, depth + 1))
        raise ValueError
    try:
        value = walk(tree)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    if isinstance(value, float):
        if not (float("-inf") < value < float("inf")):
            return None
        return f"{value:.10g}"
    return str(value)

def load_usage() -> dict[str, dict[str, float]]:
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except (OSError, json.JSONDecodeError):
        pass
    return {}

def record_usage(desktop_id: str) -> None:
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = load_usage(); item = data.setdefault(desktop_id, {})
        item["count"] = float(item.get("count", 0)) + 1
        item["last"] = time.time()
        tmp = USAGE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
        tmp.chmod(0o600); tmp.replace(USAGE_FILE)
    except OSError:
        pass


class Backend(QObject):
    statusChanged = pyqtSignal()
    resultsChanged = pyqtSignal()
    pinnedChanged = pyqtSignal()
    launcherVisibleChanged = pyqtSignal()
    quickVisibleChanged = pyqtSignal()
    effectsReducedChanged = pyqtSignal()
    osdChanged = pyqtSignal()
    mediaChanged = pyqtSignal()
    notificationsChanged = pyqtSignal()
    notificationsVisibleChanged = pyqtSignal()
    toastChanged = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._clock = ""
        self._date = ""
        self._battery = ""
        self._network = "Offline"
        self._power = "balanced"
        self._volume = 0
        self._muted = False
        self._audio_outputs: list[dict[str, str]] = []
        self._audio_inputs: list[dict[str, str]] = []
        self._current_audio_input = ""
        self._brightness = -1
        self._wifi = False
        self._bluetooth = False
        self._airplane = False
        self._microphone_active = False
        self._camera_active = False
        self._privacy_apps = ""
        self._microphone_muted = False
        self._night_light = False
        self._current_desktop = 1
        self._update_ready = False
        self._update_state = "idle"
        self._update_detail = ""
        self._recovery_available = False
        self._current_audio_output = ""
        self._performance_state = "normal"
        self._cpu_load = 0
        self._memory_load = 0
        self._memory_psi = 0.0
        self._results: list[dict[str, str]] = []
        self._apps: dict[str, DesktopApp] = {}
        self._launcher_visible = False
        self._quick_visible = False
        self._effects_reduced = False
        self._transparency_reduced = False
        self._high_contrast = False
        self._osd_visible = False
        self._osd_kind = ""
        self._osd_value = 0
        self._media_title = ""
        self._media_artist = ""
        self._media_playing = False
        self._notifications_visible = False
        self._notifications: list[dict[str, Any]] = []
        self._toast_visible = False
        self._toast_summary = ""
        self._toast_body = ""
        self._toast_app = ""
        self._toast_id = 0
        self._last_notification_id = 0
        self.settings = load_settings()
        self.runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        self.clipboard_file = self.runtime_dir / "flyos-clipboard.json"
        app = QGuiApplication.instance()
        if app is not None:
            app.clipboard().dataChanged.connect(self.captureClipboard)

        self.command_file = self.runtime_dir / "fly-shell-command"
        self.notification_file = self.runtime_dir / NOTIFICATION_FILE_NAME
        self.notification_command = self.runtime_dir / NOTIFICATION_COMMAND_NAME
        self.privacy_file = self.runtime_dir / PRIVACY_FILE_NAME
        self.performance_file = self.runtime_dir / PERFORMANCE_FILE_NAME

        self.refresh_apps()
        self.refresh_notifications(show_toast=False)
        self.refresh_status()
        self.setQuery("")

        # Avoid spawning hardware utilities every ~2 seconds. Fast UI state,
        # interactive device state and slow hardware/update state use separate
        # cadences to keep idle wakeups low on laptops.
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.refresh_clock)
        # The top bar shows minutes, not seconds; 5 s keeps minute rollover
        # responsive without waking Qt every second while the laptop is idle.
        self.clock_timer.start(5000)

        self.interactive_timer = QTimer(self)
        self.interactive_timer.timeout.connect(self.refresh_interactive)
        self.interactive_timer.start(4500)

        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.refresh_slow)
        self.slow_timer.start(12000)

        self.command_watcher = QFileSystemWatcher(self)
        try:
            self.command_watcher.addPath(str(self.runtime_dir))
            self.command_watcher.directoryChanged.connect(lambda _path: self.consume_command())
        except (OSError, RuntimeError):
            pass
        # Slow safety poll covers filesystems/backends that do not emit a
        # directory notification. Normal shortcut latency is event-driven.
        self.command_timer = QTimer(self)
        self.command_timer.timeout.connect(self.consume_command)
        self.command_timer.start(2000)

        self.osd_timer = QTimer(self)
        self.osd_timer.setSingleShot(True)
        self.osd_timer.timeout.connect(self.hideOsd)

        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.hideToast)

        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(lambda: self.refresh_notifications(show_toast=False))
        self.notification_timer.start(10000)

    @pyqtProperty(str, notify=statusChanged)
    def clock(self) -> str:
        return self._clock

    @pyqtProperty(str, notify=statusChanged)
    def dateText(self) -> str:
        return self._date

    @pyqtProperty(str, notify=statusChanged)
    def battery(self) -> str:
        return self._battery

    @pyqtProperty(str, notify=statusChanged)
    def network(self) -> str:
        return self._network

    @pyqtProperty(str, notify=statusChanged)
    def powerProfile(self) -> str:
        return self._power

    @pyqtProperty(int, notify=statusChanged)
    def volume(self) -> int:
        return self._volume

    @pyqtProperty(bool, notify=statusChanged)
    def muted(self) -> bool:
        return self._muted

    @pyqtProperty("QVariantList", notify=statusChanged)
    def audioOutputs(self) -> list[dict[str, str]]:
        return self._audio_outputs

    @pyqtProperty("QVariantList", notify=statusChanged)
    def audioInputs(self) -> list[dict[str, str]]:
        return self._audio_inputs

    @pyqtProperty(str, notify=statusChanged)
    def currentAudioInput(self) -> str:
        return self._current_audio_input

    @pyqtProperty(int, notify=statusChanged)
    def brightness(self) -> int:
        return self._brightness

    @pyqtProperty(bool, notify=statusChanged)
    def wifiEnabled(self) -> bool:
        return self._wifi

    @pyqtProperty(bool, notify=statusChanged)
    def bluetoothEnabled(self) -> bool:
        return self._bluetooth

    @pyqtProperty(bool, notify=statusChanged)
    def airplaneMode(self) -> bool:
        return self._airplane

    @pyqtProperty(bool, notify=statusChanged)
    def microphoneActive(self) -> bool:
        return self._microphone_active

    @pyqtProperty(bool, notify=statusChanged)
    def microphoneMuted(self) -> bool:
        return self._microphone_muted

    @pyqtProperty(bool, notify=statusChanged)
    def cameraActive(self) -> bool:
        return self._camera_active

    @pyqtProperty(str, notify=statusChanged)
    def privacyApps(self) -> str:
        return self._privacy_apps

    @pyqtProperty(bool, notify=statusChanged)
    def focusMode(self) -> bool:
        return bool(self.settings.get("focus_mode", False))

    @pyqtProperty(bool, notify=statusChanged)
    def nightLightEnabled(self) -> bool:
        return self._night_light

    @pyqtProperty(int, notify=statusChanged)
    def currentDesktop(self) -> int:
        return self._current_desktop

    @pyqtProperty(bool, notify=statusChanged)
    def updateReady(self) -> bool:
        return self._update_ready

    @pyqtProperty(str, notify=statusChanged)
    def updateState(self) -> str:
        return self._update_state

    @pyqtProperty(str, notify=statusChanged)
    def updateDetail(self) -> str:
        return self._update_detail

    @pyqtProperty(bool, notify=statusChanged)
    def recoveryAvailable(self) -> bool:
        return self._recovery_available

    @pyqtProperty(str, notify=statusChanged)
    def currentAudioOutput(self) -> str:
        return self._current_audio_output

    @pyqtProperty(str, notify=statusChanged)
    def performanceState(self) -> str:
        return self._performance_state

    @pyqtProperty(int, notify=statusChanged)
    def cpuLoad(self) -> int:
        return self._cpu_load

    @pyqtProperty(int, notify=statusChanged)
    def memoryLoad(self) -> int:
        return self._memory_load

    @pyqtProperty(float, notify=statusChanged)
    def memoryPressure(self) -> float:
        return self._memory_psi

    @pyqtProperty(bool, notify=statusChanged)
    def dndEnabled(self) -> bool:
        return bool(self.settings.get("dnd", False))

    @pyqtProperty("QVariantList", notify=resultsChanged)
    def results(self) -> list[dict[str, str]]:
        return self._results

    @pyqtProperty("QVariantList", notify=pinnedChanged)
    def pinned(self) -> list[dict[str, str]]:
        configured = self.settings.get("pinned") or []
        preferred = configured or [
            "org.kde.dolphin.desktop",
            "firefox.desktop",
            "org.kde.konsole.desktop",
            "fly-center.desktop",
            "org.kde.discover.desktop",
        ]
        chosen: list[dict[str, str]] = []
        seen: set[str] = set()
        for desktop_id in preferred:
            app = self._apps.get(str(desktop_id))
            if app and app.name not in seen:
                chosen.append(app.result())
                seen.add(app.name)
        if len(chosen) < 6:
            for app in sorted(self._apps.values(), key=lambda a: a.name.casefold()):
                if app.name in seen:
                    continue
                if any(token in app.name.casefold() for token in ("files", "arquivo", "browser", "navegador", "terminal", "discover")):
                    chosen.append(app.result())
                    seen.add(app.name)
                if len(chosen) >= 7:
                    break
        return chosen[:7]

    @pyqtProperty(bool, notify=launcherVisibleChanged)
    def launcherVisible(self) -> bool:
        return self._launcher_visible

    @pyqtProperty(bool, notify=quickVisibleChanged)
    def quickVisible(self) -> bool:
        return self._quick_visible

    @pyqtProperty(bool, notify=effectsReducedChanged)
    def effectsReduced(self) -> bool:
        return self._effects_reduced

    @pyqtProperty(bool, notify=effectsReducedChanged)
    def transparencyReduced(self) -> bool:
        return self._transparency_reduced

    @pyqtProperty(bool, notify=effectsReducedChanged)
    def highContrast(self) -> bool:
        return self._high_contrast

    @pyqtProperty(float, notify=effectsReducedChanged)
    def textScale(self) -> float:
        try:
            return max(0.9, min(1.5, float(self.settings.get("text_scale", 1.0))))
        except (TypeError, ValueError):
            return 1.0

    @pyqtProperty(bool, notify=effectsReducedChanged)
    def dockMagnification(self) -> bool:
        return bool(self.settings.get("dock_magnification", True)) and not self._effects_reduced

    @pyqtProperty(bool, notify=osdChanged)
    def osdVisible(self) -> bool:
        return self._osd_visible

    @pyqtProperty(str, notify=osdChanged)
    def osdKind(self) -> str:
        return self._osd_kind

    @pyqtProperty(int, notify=osdChanged)
    def osdValue(self) -> int:
        return self._osd_value

    @pyqtProperty(str, notify=mediaChanged)
    def mediaTitle(self) -> str:
        return self._media_title

    @pyqtProperty(str, notify=mediaChanged)
    def mediaArtist(self) -> str:
        return self._media_artist

    @pyqtProperty(bool, notify=mediaChanged)
    def mediaPlaying(self) -> bool:
        return self._media_playing

    @pyqtProperty(bool, notify=mediaChanged)
    def mediaAvailable(self) -> bool:
        return bool(self._media_title)

    @pyqtProperty("QVariantList", notify=notificationsChanged)
    def notifications(self) -> list[dict[str, Any]]:
        return list(reversed(self._notifications))

    @pyqtProperty(int, notify=notificationsChanged)
    def notificationCount(self) -> int:
        return len(self._notifications)

    @pyqtProperty(bool, notify=notificationsVisibleChanged)
    def notificationsVisible(self) -> bool:
        return self._notifications_visible

    @pyqtProperty(bool, notify=toastChanged)
    def toastVisible(self) -> bool:
        return self._toast_visible

    @pyqtProperty(str, notify=toastChanged)
    def toastSummary(self) -> str:
        return self._toast_summary

    @pyqtProperty(str, notify=toastChanged)
    def toastBody(self) -> str:
        return self._toast_body

    @pyqtProperty(str, notify=toastChanged)
    def toastApp(self) -> str:
        return self._toast_app

    def show_osd(self, kind: str, value: int) -> None:
        self._osd_kind = kind
        self._osd_value = max(0, min(100, int(value)))
        self._osd_visible = True
        self.osdChanged.emit()
        self.osd_timer.start(1200 if not self._effects_reduced else 800)

    @pyqtSlot()
    def hideOsd(self) -> None:
        if self._osd_visible:
            self._osd_visible = False
            self.osdChanged.emit()

    def set_launcher_visible(self, value: bool) -> None:
        value = bool(value)
        if self._launcher_visible != value:
            self._launcher_visible = value
            if value and self._quick_visible:
                self._quick_visible = False
                self.quickVisibleChanged.emit()
            if value and self._notifications_visible:
                self._notifications_visible = False
                self.notificationsVisibleChanged.emit()
            self.launcherVisibleChanged.emit()

    def set_quick_visible(self, value: bool) -> None:
        value = bool(value)
        if self._quick_visible != value:
            self._quick_visible = value
            self.update_polling_policy()
            if value and self._launcher_visible:
                self._launcher_visible = False
                self.launcherVisibleChanged.emit()
            if value and self._notifications_visible:
                self._notifications_visible = False
                self.notificationsVisibleChanged.emit()
            self.quickVisibleChanged.emit()

    def update_polling_policy(self) -> None:
        # Device/audio/media state is sampled more often while the user is
        # actively looking at Quick Settings, and less often in idle desktop
        # use. Command/file events remain event-driven regardless of this.
        if self._quick_visible:
            self.interactive_timer.setInterval(1600)
            self.slow_timer.setInterval(4000)
        else:
            self.interactive_timer.setInterval(4500)
            self.slow_timer.setInterval(12000)

    @pyqtSlot()
    def toggleLauncher(self) -> None:
        self.set_launcher_visible(not self._launcher_visible)

    @pyqtSlot()
    def toggleQuick(self) -> None:
        self.set_quick_visible(not self._quick_visible)

    @pyqtSlot()
    def hideOverlays(self) -> None:
        self.set_launcher_visible(False)
        self.set_quick_visible(False)
        if self._notifications_visible:
            self._notifications_visible = False
            self.notificationsVisibleChanged.emit()

    def refresh_notifications(self, *, show_toast: bool = False, preferred_id: int = 0) -> None:
        try:
            data = json.loads(self.notification_file.read_text(encoding="utf-8"))
            items = [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            items = []
        items = items[-100:]
        old_ids = [int(x.get("id", 0)) for x in self._notifications]
        new_ids = [int(x.get("id", 0)) for x in items]
        if old_ids != new_ids or self._notifications != items:
            self._notifications = items
            self.notificationsChanged.emit()
        if show_toast and items:
            item = next((x for x in reversed(items) if int(x.get("id", 0)) == preferred_id), items[-1])
            urgency = int(item.get("urgency", 1)) if isinstance(item, dict) else 1
            if bool(self.settings.get("dnd", False)) and urgency < 2:
                return
            ident = int(item.get("id", 0))
            if ident and ident != self._last_notification_id:
                self._last_notification_id = ident
                self._toast_id = ident
                self._toast_app = str(item.get("app", "Aplicativo"))[:80]
                self._toast_summary = str(item.get("summary", "Notificação"))[:180]
                self._toast_body = str(item.get("body", ""))[:500]
                self._toast_visible = True
                self.toastChanged.emit()
                self.toast_timer.start(5200 if self._toast_body else 3600)

    @pyqtSlot()
    def hideToast(self) -> None:
        if self._toast_visible:
            self._toast_visible = False
            self.toastChanged.emit()

    @pyqtSlot(int)
    def dismissNotification(self, ident: int) -> None:
        try:
            with self.notification_command.open("a", encoding="utf-8") as stream:
                stream.write(f"close:{int(ident)}\n")
        except OSError:
            return
        QTimer.singleShot(250, lambda: self.refresh_notifications(show_toast=False))


    @pyqtSlot(int, str)
    def notificationAction(self, ident: int, action_key: str) -> None:
        key = str(action_key).replace("\n", " ").replace("\r", " ")[:120]
        if not key:
            return
        try:
            with self.notification_command.open("a", encoding="utf-8") as stream:
                stream.write(f"action:{int(ident)}:{key}\n")
        except OSError:
            return
        self.hideToast()
        QTimer.singleShot(250, lambda: self.refresh_notifications(show_toast=False))

    @pyqtSlot()
    def activateToast(self) -> None:
        item = next((x for x in self._notifications if int(x.get("id", 0)) == self._toast_id), None)
        if item:
            actions = item.get("actions", []) if isinstance(item, dict) else []
            if isinstance(actions, list):
                default = next((a for a in actions if isinstance(a, dict) and str(a.get("key", "")) == "default"), None)
                if default:
                    self.notificationAction(self._toast_id, "default")
                    return
        self.hideToast()
        self.openNotifications()

    @pyqtSlot()
    def clearNotifications(self) -> None:
        try:
            with self.notification_command.open("a", encoding="utf-8") as stream:
                stream.write("clear\n")
        except OSError:
            return
        QTimer.singleShot(250, lambda: self.refresh_notifications(show_toast=False))

    def consume_command(self) -> None:
        processing = self.command_file.with_name(f"{self.command_file.name}.processing-{os.getpid()}")
        try:
            os.replace(self.command_file, processing)
            queued = processing.read_text(encoding="utf-8")
        except OSError:
            return
        finally:
            try:
                processing.unlink(missing_ok=True)
            except OSError:
                pass
        commands = {
            "launcher": self.toggleLauncher,
            "quick": self.toggleQuick,
            "notifications": self.openNotifications,
            "overview": self.openOverview,
            "health": self.openHealth,
            "settings": self.openCenter,
            "apps": self.openApps,
            "settings-reload": self.reloadSettings,
        }
        for command in (line.strip() for line in queued.splitlines()):
            if command.startswith("notification:"):
                try:
                    ident = int(command.split(":", 1)[1])
                except ValueError:
                    ident = 0
                self.refresh_notifications(show_toast=True, preferred_id=ident)
                continue
            if command == "notifications-refresh":
                self.refresh_notifications(show_toast=False)
                continue
            if command.startswith("osd-volume:") or command.startswith("osd-brightness:"):
                kind, _, raw = command.partition(":")
                try:
                    value = int(raw)
                except ValueError:
                    continue
                self.show_osd("brightness" if kind == "osd-brightness" else "volume", value)
                QTimer.singleShot(120, self.refresh_status)
                continue
            handler = commands.get(command)
            if handler:
                handler()

    def refresh_apps(self) -> None:
        apps: dict[str, DesktopApp] = {}
        for directory in APP_DIRS:
            if not directory.is_dir():
                continue
            for path in directory.rglob("*.desktop"):
                desktop_id = path.name if path.parent == directory else str(path.relative_to(directory)).replace("/", "-")
                if desktop_id in apps:
                    continue
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                parser.optionxform = str
                try:
                    parser.read(path, encoding="utf-8")
                    sec = parser["Desktop Entry"]
                except (OSError, KeyError, configparser.Error):
                    continue
                if sec.get("Type", "Application") != "Application":
                    continue
                if sec.get("Hidden", "false").lower() == "true" or sec.get("NoDisplay", "false").lower() == "true":
                    continue
                only_show = sec.get("OnlyShowIn", "")
                not_show = sec.get("NotShowIn", "")
                if only_show and not any(x in only_show for x in ("KDE", "FlyOS")):
                    continue
                if "KDE" in not_show and "FlyOS" in not_show:
                    continue
                name = sec.get("Name[pt_BR]") or sec.get("Name") or path.stem
                exec_line = sec.get("Exec", "")
                if not exec_line:
                    continue
                keywords = " ".join([
                    sec.get("GenericName", ""), sec.get("Comment", ""), sec.get("Keywords", ""), desktop_id
                ])
                apps[desktop_id] = DesktopApp(
                    desktop_id=desktop_id,
                    name=name,
                    icon=sec.get("Icon", "application-x-executable"),
                    path=str(path),
                    exec_line=exec_line,
                    keywords=keywords,
                )
        self._apps = apps
        self.pinnedChanged.emit()

    def file_results(self, query: str, limit: int = 12) -> list[dict[str, str]]:
        if len(query.strip()) < 2 or not SEARCH_DB.exists():
            return []
        try:
            con = sqlite3.connect(f"file:{SEARCH_DB}?mode=ro", uri=True, timeout=0.15)
            con.row_factory = sqlite3.Row
            words = [w.replace('"', '') for w in query.split() if w]
            match = " AND ".join(f'"{w}"*' for w in words)
            rows = con.execute(
                "SELECT path, name, parent FROM files_fts WHERE files_fts MATCH ? LIMIT ?",
                (match, limit),
            ).fetchall()
            con.close()
        except (sqlite3.Error, OSError):
            return []
        out: list[dict[str, str]] = []
        for row in rows:
            p = Path(row["path"])
            out.append({
                "kind": "file",
                "id": str(p),
                "name": row["name"],
                "subtitle": row["parent"],
                "icon": "folder" if p.is_dir() else "text-x-generic",
                "target": str(p),
            })
        return out

    @pyqtSlot(str)
    def setQuery(self, query: str) -> None:
        raw_query = query.strip()
        q = raw_query.casefold()
        ranked: list[tuple[int, str, dict[str, str]]] = []
        usage = load_usage()
        now = time.time()
        for app in self._apps.values():
            name = app.name.casefold()
            haystack = f"{name} {app.keywords.casefold()}"
            used = usage.get(app.desktop_id, {})
            count = min(20.0, float(used.get("count", 0.0)))
            last = float(used.get("last", 0.0))
            recent_bonus = 8 if last and now - last < 86400 else (4 if last and now - last < 604800 else 0)
            if not q:
                score = max(20, int(50 - min(20, count) - recent_bonus))
            elif name.startswith(q):
                score = 0
            elif q in name:
                score = 8
            elif all(word in haystack for word in q.split()):
                score = 18
            else:
                continue
            score = max(0, score - min(6, int(count // 3)) - (2 if recent_bonus else 0))
            ranked.append((score, name, app.result()))

        calc = calculate_expression(raw_query) if raw_query else None
        if calc is not None:
            ranked.append((-2, "calculator", {
                "kind": "calc", "id": "calculator", "name": calc,
                "subtitle": "Resultado • clique para copiar", "icon": "accessories-calculator", "target": calc,
            }))

        for name, subtitle, icon, action, keywords in ACTIONS:
            haystack = f"{name} {subtitle} {keywords}".casefold()
            if not q:
                if action not in {"center", "update", "health", "apps"}:
                    continue
                score = 35
            elif name.casefold().startswith(q):
                score = 1
            elif q in haystack or all(word in haystack for word in q.split()):
                score = 15
            else:
                continue
            ranked.append((score, name.casefold(), {
                "kind": "action", "id": action, "name": name,
                "subtitle": subtitle, "icon": icon, "target": action,
            }))

        ranked.sort(key=lambda item: (item[0], item[1]))
        results = [item for _, _, item in ranked[:22]]
        if q:
            results.extend(self.file_results(q, max(0, 28 - len(results))))
        self._results = results[:28]
        self.resultsChanged.emit()

    @pyqtSlot(str, str)
    def activateResult(self, kind: str, target: str) -> None:
        self.set_launcher_visible(False)
        if kind == "app":
            self.launchById(target)
        elif kind == "file":
            popen(["xdg-open", target])
        elif kind == "action":
            self.runAction(target)
        elif kind == "calc":
            app = QGuiApplication.instance()
            if app is not None:
                app.clipboard().setText(target)
            notify("Fly Search", f"{target} copiado")

    @pyqtSlot(str)
    def launchById(self, desktop_id: str) -> None:
        app = self._apps.get(desktop_id)
        if not app:
            return
        self.set_launcher_visible(False)
        record_usage(desktop_id)
        if shutil.which("gio") and popen(["gio", "launch", app.path]):
            return
        try:
            argv = shlex.split(FIELD_CODE.sub("", app.exec_line))
        except ValueError:
            return
        if argv:
            popen(argv)

    @pyqtSlot(str)
    def runAction(self, action: str) -> None:
        actions: dict[str, list[str] | None] = {
            "center": ["fly-center"],
            "update": ["fly-update", "gui"],
            "health": ["fly-health"],
            "recovery": ["fly-recovery-ui"],
            "backup": ["fly-backup"],
            "wine": ["fly-wine"],
            "terminal": ["x-terminal-emulator"],
            "screenshot": ["fly-screenshot"],
            "apps": ["fly-apps"],
            "clipboard": ["fly-clipboard"],
            "network": ["fly-connect"],
            "files": ["fly-files"],
            "audio": ["fly-audio"],
            "firewall": ["fly-firewall"],
            "bluetooth": ["fly-bluetooth"],
            "airplane": ["fly-airplane", "toggle"],
            "battery": ["fly-battery-dashboard"],
            "gpu": ["fly-gpu"],
            "privacy": ["fly-privacy"],
            "activity": ["fly-activity"],
            "storage": ["fly-storage"],
            "login-items": ["fly-login-items"],
            "defaults": ["fly-defaults"],
            "support": ["fly-support-report"],
        }
        if action == "lock":
            self.lock()
        elif action == "overview":
            self.openOverview()
        elif action == "airplane":
            self.toggleAirplane()
        elif action in actions and actions[action]:
            popen(actions[action] or [])

    @pyqtSlot()
    def openCenter(self) -> None:
        popen(["fly-center"])

    @pyqtSlot()
    def openHealth(self) -> None:
        popen(["fly-health"])

    @pyqtSlot()
    def openSettings(self) -> None:
        # Fly Center is the primary settings surface; System Settings remains
        # available for deep compositor/device configuration.
        popen(["fly-center"])

    @pyqtSlot()
    def openSystemSettings(self) -> None:
        popen(["systemsettings"])

    @pyqtSlot()
    def openApps(self) -> None:
        popen(["fly-apps"])

    @pyqtSlot()
    def openNotifications(self) -> None:
        self.refresh_notifications(show_toast=False)
        self.set_launcher_visible(False)
        self.set_quick_visible(False)
        self._notifications_visible = not self._notifications_visible
        self.notificationsVisibleChanged.emit()

    @pyqtSlot()
    def openOverview(self) -> None:
        if not kwin_toggle_overview():
            popen(["fly-shellctl", "launcher"])

    @pyqtSlot(str)
    def switchWorkspace(self, direction: str) -> None:
        if kwin_workspace(direction):
            QTimer.singleShot(160, self.refresh_status)

    @pyqtSlot()
    def lock(self) -> None:
        if shutil.which("fly-lock"):
            popen(["fly-lock"])
        elif shutil.which("loginctl"):
            popen(["loginctl", "lock-session"])

    @pyqtSlot(str)
    def powerAction(self, action: str) -> None:
        if action == "logout":
            session = os.environ.get("XDG_SESSION_ID", "")
            if session and shutil.which("loginctl"):
                popen(["loginctl", "terminate-session", session])
            else:
                popen(["systemctl", "--user", "stop", "flyos-session.target"])
        elif action == "suspend":
            popen(["systemctl", "suspend"])
        elif action == "reboot":
            popen(["systemctl", "reboot"])
        elif action == "poweroff":
            popen(["systemctl", "poweroff"])

    @pyqtSlot()
    def toggleWifi(self) -> None:
        if self._airplane and shutil.which("fly-airplane"):
            popen(["fly-airplane", "off"])
        else:
            nm_set_radio("wifi", not self._wifi)
        QTimer.singleShot(900, self.refresh_status)

    @pyqtSlot()
    def toggleBluetooth(self) -> None:
        if self._airplane and shutil.which("fly-airplane"):
            popen(["fly-airplane", "off"])
        else:
            bluez_set_powered(not self._bluetooth)
        QTimer.singleShot(900, self.refresh_status)

    @pyqtSlot()
    def toggleAirplane(self) -> None:
        if shutil.which("fly-airplane"):
            popen(["fly-airplane", "off" if self._airplane else "on"])
            QTimer.singleShot(1100, self.refresh_status)

    @pyqtSlot()
    def toggleDnd(self) -> None:
        new_state = not bool(self.settings.get("dnd", False))
        self.settings["dnd"] = new_state
        save_settings(self.settings)
        if new_state:
            self.hideToast()
        self.statusChanged.emit()

    @pyqtSlot()
    def toggleFocusMode(self) -> None:
        enabled = not bool(self.settings.get("focus_mode", False))
        self.settings["focus_mode"] = enabled
        self.settings["dnd"] = enabled
        save_settings(self.settings)
        if enabled:
            self.hideToast()
            if shutil.which("fly-profile"):
                popen(["fly-profile", "balanced"])
        self.statusChanged.emit()

    @pyqtSlot()
    def captureClipboard(self) -> None:
        if not bool(self.settings.get("clipboard_history", False)):
            return
        app = QGuiApplication.instance()
        if app is None:
            return
        text = app.clipboard().text().strip()
        if not text or len(text.encode("utf-8", errors="ignore")) > 65536:
            return
        try:
            try:
                items = json.loads(self.clipboard_file.read_text(encoding="utf-8"))
                if not isinstance(items, list):
                    items = []
            except (OSError, json.JSONDecodeError):
                items = []
            items = [x for x in items if isinstance(x, dict) and x.get("text") != text]
            items.insert(0, {"text": text, "time": int(time.time())})
            tmp = self.clipboard_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(items[:20], ensure_ascii=False), encoding="utf-8")
            tmp.chmod(0o600); os.replace(tmp, self.clipboard_file)
        except OSError:
            pass

    @pyqtSlot()
    def reloadSettings(self) -> None:
        latest = load_settings()
        if latest == self.settings:
            return
        old_clipboard = bool(self.settings.get("clipboard_history", False))
        self.settings = latest
        new_clipboard = bool(self.settings.get("clipboard_history", False))
        if old_clipboard and not new_clipboard:
            self.clipboard_file.unlink(missing_ok=True)
        if bool(self.settings.get("dnd", False)):
            self.hideToast()
        self.effectsReducedChanged.emit()
        self.pinnedChanged.emit()
        self.statusChanged.emit()

    @pyqtSlot(str)
    def setAudioOutput(self, sink_name: str) -> None:
        if audio_set_default(str(sink_name).strip()):
            QTimer.singleShot(180, self.refresh_slow)

    @pyqtSlot(str)
    def setAudioInput(self, source_name: str) -> None:
        if audio_set_default(str(source_name).strip()):
            QTimer.singleShot(180, self.refresh_slow)

    @pyqtSlot(int)
    def setVolume(self, value: int) -> None:
        value = max(0, min(150, int(value)))
        if audio_set_volume(value, False):
            self._volume = value
            self.statusChanged.emit()
            self.show_osd("volume", value)

    @pyqtSlot()
    def toggleMute(self) -> None:
        if audio_toggle_mute(False):
            QTimer.singleShot(120, self.refresh_interactive)

    @pyqtSlot()
    def toggleMicrophoneMute(self) -> None:
        if audio_toggle_mute(True):
            QTimer.singleShot(120, self.refresh_interactive)

    @pyqtSlot()
    def toggleNightLight(self) -> None:
        if not shutil.which("kwriteconfig6"):
            return
        new_state = not self._night_light
        subprocess.run(
            ["kwriteconfig6", "--file", "kwinrc", "--group", "NightColor",
             "--key", "Active", "true" if new_state else "false"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        kwin_reconfigure()
        self._night_light = new_state
        self.statusChanged.emit()

    @pyqtSlot(int)
    def setBrightness(self, value: int) -> None:
        value = max(1, min(100, int(value)))
        if set_brightness_percent(value):
            self._brightness = value
            self.statusChanged.emit()
            self.show_osd("brightness", value)

    @pyqtSlot(str)
    def setPowerProfile(self, profile: str) -> None:
        if profile not in {"balanced", "performance", "power-saver"}:
            return
        if shutil.which("fly-profile"):
            popen(["fly-profile", profile])
        elif shutil.which("powerprofilesctl"):
            popen(["powerprofilesctl", "set", profile])
        QTimer.singleShot(500, self.refresh_status)

    @pyqtSlot(str)
    def mediaAction(self, action: str) -> None:
        if action in {"play-pause", "next", "previous"}:
            media_action(action)
        QTimer.singleShot(220, self.refresh_status)

    def refresh_clock(self) -> None:
        now = datetime.now()
        clock = now.strftime("%H:%M")
        date = now.strftime("%a, %d %b")
        if (clock, date) != (self._clock, self._date):
            self._clock, self._date = clock, date
            self.statusChanged.emit()

    def refresh_interactive(self) -> None:
        old_status = (
            self._volume, self._muted, self._brightness,
            self._microphone_active, self._camera_active, self._privacy_apps,
            self._microphone_muted, self._current_desktop,
        )
        old_media = (self._media_title, self._media_artist, self._media_playing)
        self._volume, self._muted = self.read_volume()
        self._brightness = self.read_brightness()
        self._microphone_active, self._camera_active, self._privacy_apps = self.read_privacy_state()
        self._microphone_muted = self.read_microphone_muted()
        self._current_desktop = self.read_current_desktop()
        self._media_title, self._media_artist, self._media_playing = self.read_media()
        if old_media != (self._media_title, self._media_artist, self._media_playing):
            self.mediaChanged.emit()
        new_status = (
            self._volume, self._muted, self._brightness,
            self._microphone_active, self._camera_active, self._privacy_apps,
            self._microphone_muted, self._current_desktop,
        )
        if old_status != new_status:
            self.statusChanged.emit()

    def refresh_slow(self) -> None:
        old_status = (
            self._battery, self._network, self._power, self._wifi, self._bluetooth, self._airplane,
            self._audio_outputs, self._audio_inputs, self._current_audio_output,
            self._current_audio_input, self._night_light, self._update_ready,
            self._update_state, self._update_detail, self._recovery_available,
            self._performance_state, self._cpu_load, self._memory_load, self._memory_psi,
        )
        self._battery = self.read_battery()
        self._network = self.read_network()
        self._power = output(["powerprofilesctl", "get"], timeout=0.7) if shutil.which("powerprofilesctl") else "balanced"
        self._power = self._power or "balanced"
        self._wifi = nm_radio("wifi")
        self._bluetooth = bluez_powered()
        self._airplane = self.read_airplane_mode()
        self._audio_outputs = self.read_audio_outputs()
        self._current_audio_output = next((str(x.get("name", "")) for x in self._audio_outputs if bool(x.get("default", False))), "")
        self._audio_inputs = self.read_audio_inputs()
        self._current_audio_input = next((str(x.get("name", "")) for x in self._audio_inputs if bool(x.get("default", False))), "")
        self._night_light = self.read_night_light()
        self._update_ready = Path("/system-update").is_symlink()
        self._update_state, self._update_detail, self._recovery_available = self.read_update_state()
        self._performance_state, self._cpu_load, self._memory_load, self._memory_psi = self.read_performance_state()

        latest_settings = load_settings()
        if latest_settings != self.settings:
            self.settings = latest_settings
            self.effectsReducedChanged.emit()
            self.pinnedChanged.emit()

        animation_factor = output([
            "kreadconfig6", "--file", "kdeglobals", "--group", "KDE", "--key", "AnimationDurationFactor"
        ], timeout=0.6) if shutil.which("kreadconfig6") else ""
        safe = os.environ.get("FLYOS_SAFE_MODE") == "1"
        pressure_reduce = bool(self.settings.get("adaptive_performance", True)) and self._performance_state == "pressure"
        reduced = (
            safe
            or self._power == "power-saver"
            or animation_factor in {"0", "0.0", "0.00"}
            or bool(self.settings.get("reduce_motion", False))
            or pressure_reduce
        )
        transparency_reduced = (
            safe or self._power == "power-saver"
            or bool(self.settings.get("reduce_transparency", False))
            or pressure_reduce
        )
        high_contrast = bool(self.settings.get("high_contrast", False))
        changed = (reduced != self._effects_reduced or transparency_reduced != self._transparency_reduced or high_contrast != self._high_contrast)
        self._effects_reduced = reduced
        self._transparency_reduced = transparency_reduced
        self._high_contrast = high_contrast
        if changed:
            self.effectsReducedChanged.emit()
        new_status = (
            self._battery, self._network, self._power, self._wifi, self._bluetooth, self._airplane,
            self._audio_outputs, self._audio_inputs, self._current_audio_output,
            self._current_audio_input, self._night_light, self._update_ready,
            self._update_state, self._update_detail, self._recovery_available,
            self._performance_state, self._cpu_load, self._memory_load, self._memory_psi,
        )
        if old_status != new_status:
            self.statusChanged.emit()

    @pyqtSlot()
    def refresh_status(self) -> None:
        # Full refresh is reserved for startup and explicit user actions.
        self.refresh_clock()
        self.refresh_interactive()
        self.refresh_slow()


    @staticmethod
    def read_update_state() -> tuple[str, str, bool]:
        state_file = Path("/var/lib/flyos/offline-update/state")
        snapshot_file = Path("/var/lib/flyos/offline-update/snapshot-id")
        state = "idle"
        detail = ""
        try:
            values: dict[str, str] = {}
            for raw in state_file.read_text(encoding="utf-8").splitlines():
                key, sep, value = raw.partition("=")
                if sep:
                    values[key.strip()] = value.strip()
            state = values.get("state", "idle") or "idle"
            detail = values.get("detail", "")[:180]
        except OSError:
            pass
        recovery = state == "failed"
        if snapshot_file.exists():
            try:
                recovery = recovery or snapshot_file.read_text(encoding="utf-8").strip().isdigit()
            except OSError:
                pass
        return state, detail, recovery

    @staticmethod
    def read_media() -> tuple[str, str, bool]:
        title, artist, playing, _player = media_state()
        return title, artist, playing

    @staticmethod
    def read_volume() -> tuple[int, bool]:
        return audio_volume(False)

    @staticmethod
    def read_audio_outputs() -> list[dict[str, str]]:
        return audio_endpoints(False)

    @staticmethod
    def read_audio_inputs() -> list[dict[str, str]]:
        return audio_endpoints(True)

    def read_performance_state(self) -> tuple[str, int, int, float]:
        try:
            data = json.loads(self.performance_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                updated = int(data.get("updated", 0))
                if updated and time.time() - updated <= 20:
                    return (
                        str(data.get("state", "normal")),
                        int(round(float(data.get("cpu_percent", 0)))),
                        int(round(float(data.get("memory_percent", 0)))),
                        float(data.get("memory_psi_avg10", 0.0)),
                    )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
        return "normal", 0, 0, 0.0

    def read_privacy_state(self) -> tuple[bool, bool, str]:
        try:
            data = json.loads(self.privacy_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                mic = bool(data.get("microphone_active", False))
                cam = bool(data.get("camera_active", False))
                apps = []
                for key in ("microphone_apps", "camera_apps"):
                    value = data.get(key, [])
                    if isinstance(value, list):
                        for item in value:
                            name = str(item).strip()
                            if name and name not in apps:
                                apps.append(name)
                return mic, cam, ", ".join(apps[:5])
        except (OSError, json.JSONDecodeError):
            pass
        return self.read_microphone_active(), False, ""

    @staticmethod
    def read_microphone_muted() -> bool:
        return audio_volume(True)[1]

    @staticmethod
    def read_airplane_mode() -> bool:
        try:
            data = json.loads(AIRPLANE_STATE_FILE.read_text(encoding="utf-8"))
            return bool(data.get("active", False)) if isinstance(data, dict) else False
        except (OSError, json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def read_night_light() -> bool:
        if not shutil.which("kreadconfig6"):
            return False
        value = output([
            "kreadconfig6", "--file", "kwinrc", "--group", "NightColor",
            "--key", "Active", "--default", "false"
        ], timeout=0.5).casefold()
        return value in {"true", "1", "yes", "on"}

    @staticmethod
    def read_current_desktop() -> int:
        return kwin_current_desktop()

    @staticmethod
    def read_microphone_active() -> bool:
        # Primary privacy state comes from fly-privacy-monitor. Keep this
        # conservative fallback off instead of guessing from a Pulse shim.
        return False

    @staticmethod
    def read_brightness() -> int:
        return brightness_percent()

    @staticmethod
    def read_battery() -> str:
        for path in sorted(Path("/sys/class/power_supply").glob("BAT*")):
            try:
                capacity = (path / "capacity").read_text().strip()
                status = (path / "status").read_text().strip().casefold()
                mark = "⚡" if status == "charging" else ""
                return f"{mark}{capacity}%"
            except OSError:
                continue
        return ""

    @staticmethod
    def read_network() -> str:
        return nm_primary_connection_name()


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Fly Shell")
    app.setOrganizationName("Fly OS")
    app.setDesktopFileName("fly-shell")

    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("fly", backend)
    qml = Path("/usr/share/flyos/shell/Main.qml")
    if not qml.exists():
        qml = Path(__file__).resolve().parents[2] / "share/flyos/shell/Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    if not engine.rootObjects():
        return 2
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
