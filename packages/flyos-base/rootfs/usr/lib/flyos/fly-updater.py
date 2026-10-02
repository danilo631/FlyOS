#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

STATE = Path('/var/lib/flyos/offline-update/state')
PLAN = Path('/var/lib/flyos/offline-update/apt-plan.txt')
TRANSACTION = Path('/var/lib/flyos/offline-update/apt-transaction.txt')
LOGFILE = Path('/var/lib/flyos/offline-update/offline-update.log')
SNAPSHOT = Path('/var/lib/flyos/offline-update/snapshot-id')


def output(argv: list[str], timeout: int = 20) -> str:
    try:
        return subprocess.run(argv, check=False, text=True, capture_output=True, timeout=timeout).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ''


def counts() -> tuple[int, int, int]:
    apt = output(['apt', 'list', '--upgradable']) if shutil.which('apt') else ''
    apt_count = sum(1 for x in apt.splitlines() if '/' in x and not x.startswith('Listing'))
    flat = output(['flatpak', 'remote-ls', '--updates', '--columns=application']) if shutil.which('flatpak') else ''
    flat_count = len([x for x in flat.splitlines() if x.strip()])
    fw = output(['fwupdmgr', 'get-updates', '--json']) if shutil.which('fwupdmgr') else ''
    fw_count = len(re.findall(r'"Version"\s*:', fw)) if fw else 0
    return apt_count, flat_count, fw_count


def offline_state() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in STATE.read_text(encoding='utf-8').splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                values[key] = value
    except OSError:
        pass
    values['scheduled'] = 'yes' if Path('/system-update').is_symlink() else 'no'
    return values


class CheckThread(QThread):
    done = pyqtSignal(int, int, int)

    def run(self) -> None:
        self.done.emit(*counts())


class Updater(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Fly Update')
        self.resize(690, 520)
        self.worker: CheckThread | None = None
        self.process: QProcess | None = None

        root = QWidget()
        box = QVBoxLayout(root)
        box.setContentsMargins(28, 26, 28, 26)
        box.setSpacing(14)

        title = QLabel('Fly Update'); title.setObjectName('title'); box.addWidget(title)
        sub = QLabel(
            'Atualizações do sistema são baixadas durante a sessão normal e aplicadas no próximo boot, '
            'com o desktop parado. Isso reduz conflitos de bibliotecas e serviços em uso.'
        )
        sub.setWordWrap(True); sub.setObjectName('muted'); box.addWidget(sub)

        self.card = QFrame(); self.card.setObjectName('card')
        cb = QVBoxLayout(self.card); cb.setContentsMargins(20, 18, 20, 18); cb.setSpacing(8)
        self.status = QLabel('Verificando atualizações…'); self.status.setObjectName('status'); cb.addWidget(self.status)
        self.details = QLabel(''); self.details.setObjectName('muted'); cb.addWidget(self.details)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.setVisible(False); cb.addWidget(self.progress)
        box.addWidget(self.card)

        row = QHBoxLayout()
        self.check_btn = QPushButton('Verificar novamente'); self.check_btn.clicked.connect(self.refresh); row.addWidget(self.check_btn)
        self.prepare_btn = QPushButton('Preparar atualização segura'); self.prepare_btn.clicked.connect(self.prepare_offline); row.addWidget(self.prepare_btn)
        self.reboot_btn = QPushButton('Reiniciar e atualizar'); self.reboot_btn.clicked.connect(self.reboot); row.addWidget(self.reboot_btn)
        box.addLayout(row)

        row2 = QHBoxLayout()
        flatpak = QPushButton('Atualizar apps Flatpak'); flatpak.clicked.connect(self.update_flatpak); row2.addWidget(flatpak)
        firmware = QPushButton('Ver firmware'); firmware.clicked.connect(self.firmware); row2.addWidget(firmware)
        cancel = QPushButton('Cancelar atualização preparada'); cancel.clicked.connect(self.cancel_offline); row2.addWidget(cancel)
        details = QPushButton('Detalhes'); details.clicked.connect(self.show_details); row2.addWidget(details)
        box.addLayout(row2)

        self.log = QLabel(''); self.log.setWordWrap(True); self.log.setObjectName('muted'); box.addWidget(self.log)
        info = QLabel(
            'Quando Btrfs + Snapper estão configurados, o Fly Recovery cria um snapshot antes da transação. '
            'Em ext4 a atualização offline continua disponível, mas não promete rollback atômico.'
        )
        info.setWordWrap(True); info.setObjectName('muted'); box.addWidget(info); box.addStretch(1)
        self.setCentralWidget(root)
        self.setStyleSheet('''
            QMainWindow,QWidget{background:#11161f;color:#f7f8fc}
            QLabel#title{font-size:30px;font-weight:750}
            QLabel#status{font-size:18px;font-weight:650}
            QLabel#muted{color:rgba(225,232,245,0.68)}
            QFrame#card{background:rgba(255,255,255,0.055);border:1px solid rgba(255,255,255,0.10);border-radius:18px}
            QPushButton{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.11);border-radius:11px;min-height:38px;padding:0 14px;color:#f7f8fc}
            QPushButton:hover{background:rgba(124,174,255,0.20)}
            QPushButton:disabled{color:rgba(225,232,245,0.35);background:rgba(255,255,255,0.035)}
            QProgressBar{border:0;background:rgba(255,255,255,0.08);border-radius:5px;min-height:8px;max-height:8px;text-align:center}
            QProgressBar::chunk{background:#7caeff;border-radius:5px}
        ''')
        self.refresh_state()
        self.refresh()

    def busy(self, value: bool, message: str = '') -> None:
        self.progress.setVisible(value)
        self.check_btn.setEnabled(not value)
        self.prepare_btn.setEnabled(not value)
        if message:
            self.log.setText(message)

    def refresh_state(self) -> None:
        state = offline_state()
        ready = state.get('state') == 'ready' and state.get('scheduled') == 'yes'
        self.reboot_btn.setEnabled(ready)
        if ready:
            self.log.setText('Uma atualização do sistema já está preparada. Reinicie quando for conveniente.')
        elif state.get('state') == 'failed':
            self.log.setText('A última atualização offline falhou. Abra Fly Recovery para diagnóstico.')

    def refresh(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self.status.setText('Verificando atualizações…')
        self.details.setText('APT, Flatpak e firmware')
        self.busy(True)
        self.worker = CheckThread(self)
        self.worker.done.connect(self.check_done)
        self.worker.finished.connect(lambda: self.busy(False))
        self.worker.start()

    def check_done(self, apt_count: int, flat_count: int, fw_count: int) -> None:
        total = apt_count + flat_count + fw_count
        self.status.setText('Sistema atualizado' if total == 0 else f'{total} atualização(ões) encontrada(s)')
        self.details.setText(f'Sistema: {apt_count}   •   Flatpak: {flat_count}   •   Firmware: {fw_count}')
        self.refresh_state()

    def run_process(self, program: str, args: list[str], message: str, callback=None) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, 'Fly Update', 'Já existe uma operação em andamento.')
            return
        self.process = QProcess(self)
        self.process.setProgram(program); self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.finished.connect(lambda code, _status: self.process_done(code, callback))
        self.busy(True, message)
        self.process.start()

    def process_output(self) -> None:
        if not self.process:
            return
        text = bytes(self.process.readAllStandardOutput()).decode(errors='replace').strip()
        if text:
            self.log.setText(text[-1200:])

    def process_done(self, code: int, callback=None) -> None:
        self.busy(False)
        if code == 0:
            if callback: callback()
        else:
            QMessageBox.warning(self, 'Fly Update', 'A operação não foi concluída. Consulte a mensagem exibida e o Fly Recovery.')
        self.refresh_state(); self.refresh()

    def prepare_offline(self) -> None:
        if not shutil.which('pkexec'):
            QMessageBox.warning(self, 'Fly Update', 'pkexec/PolicyKit não está disponível nesta instalação.')
            return
        self.run_process('pkexec', ['/usr/lib/flyos/fly-offline-update-helper', 'prepare'],
                         'Baixando e validando os pacotes. Você pode continuar usando o computador…',
                         lambda: QMessageBox.information(self, 'Fly Update', 'Atualização preparada. Reinicie quando quiser aplicá-la.'))

    def cancel_offline(self) -> None:
        if shutil.which('pkexec'):
            self.run_process('pkexec', ['/usr/lib/flyos/fly-offline-update-helper', 'cancel'], 'Cancelando atualização preparada…')

    def reboot(self) -> None:
        if QMessageBox.question(self, 'Fly Update', 'Reiniciar agora e aplicar a atualização preparada?') == QMessageBox.StandardButton.Yes:
            subprocess.Popen(['systemctl', 'reboot'], start_new_session=True)

    def show_details(self) -> None:
        state = offline_state()
        sections = [f"Estado: {state.get('state', 'desconhecido')}", f"Detalhe: {state.get('detail', '—')}"]
        try:
            snap = SNAPSHOT.read_text(encoding='utf-8').strip()
            if snap: sections.append(f"Snapshot pré-update: {snap}")
        except OSError:
            pass
        try:
            transaction = TRANSACTION.read_text(encoding='utf-8')[-5000:]
            if transaction.strip():
                installs = sum(1 for line in transaction.splitlines() if line.startswith('Inst '))
                removals = sum(1 for line in transaction.splitlines() if line.startswith('Remv '))
                sections.append(f"Transação bloqueada: {installs} instalação(ões)/upgrade(s), {removals} remoção(ões)")
                sections.append("\nPacotes resolvidos:\n" + transaction)
        except OSError:
            pass
        try:
            plan = PLAN.read_text(encoding='utf-8')[-5000:]
            if plan.strip(): sections.append("\nPlano APT completo (final):\n" + plan)
        except OSError:
            pass
        try:
            log = LOGFILE.read_text(encoding='utf-8')[-5000:]
            if log.strip(): sections.append("\nLog offline (final):\n" + log)
        except OSError:
            pass
        QMessageBox.information(self, 'Fly Update — detalhes', "\n".join(sections)[:11000])

    def update_flatpak(self) -> None:
        if not shutil.which('flatpak'):
            QMessageBox.information(self, 'Fly Update', 'Flatpak não está instalado.')
            return
        self.run_process('flatpak', ['update', '--user', '-y'], 'Atualizando aplicativos Flatpak…')

    def firmware(self) -> None:
        if shutil.which('plasma-discover'):
            subprocess.Popen(['plasma-discover', '--mode', 'Update'], start_new_session=True)
        elif shutil.which('fwupdmgr'):
            text = output(['fwupdmgr', 'get-updates'], 30)
            QMessageBox.information(self, 'Firmware', text[-6000:] or 'Nenhuma atualização de firmware encontrada.')
        else:
            QMessageBox.information(self, 'Fly Update', 'fwupd não está instalado.')


def main() -> int:
    app = QApplication(sys.argv)
    window = Updater(); window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
