#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication,QFrame,QLabel,QMainWindow,QPushButton,QVBoxLayout,QWidget
RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')); STATE=RUNTIME/'fly-privacy.json'
class Privacy(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Fly Privacy'); self.resize(620,480)
        root=QWidget(); box=QVBoxLayout(root); box.setContentsMargins(26,24,26,24); box.setSpacing(14)
        t=QLabel('Privacidade em tempo real'); t.setObjectName('title'); box.addWidget(t)
        s=QLabel('Indicadores locais da sessão. O Fly OS não envia esse estado para servidores e não mantém histórico persistente por padrão.'); s.setWordWrap(True); s.setObjectName('muted'); box.addWidget(s)
        self.mic=self.card('Microfone'); self.cam=self.card('Câmera'); box.addWidget(self.mic[0]); box.addWidget(self.cam[0])
        b=QPushButton('Abrir Fly Center'); b.clicked.connect(lambda: subprocess.Popen(['fly-center'],start_new_session=True)); box.addWidget(b); box.addStretch(1)
        self.setCentralWidget(root)
        self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f7f8fc} QLabel#title{font-size:28px;font-weight:750} QLabel#muted{color:rgba(225,232,245,.67)} QFrame#card{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.09);border-radius:16px} QPushButton{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11);border-radius:10px;min-height:38px;padding:0 14px;color:#f7f8fc}')
        self.refresh(); self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1200)
    def card(self,name):
        f=QFrame(); f.setObjectName('card'); l=QVBoxLayout(f); l.setContentsMargins(18,15,18,15)
        title=QLabel(name); title.setStyleSheet('font-size:16px;font-weight:650'); status=QLabel('Sem uso'); apps=QLabel(''); apps.setObjectName('muted'); apps.setWordWrap(True)
        l.addWidget(title); l.addWidget(status); l.addWidget(apps); return f,status,apps
    def refresh(self):
        try: data=json.loads(STATE.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError): data={}
        for prefix, widgets in [('microphone',self.mic),('camera',self.cam)]:
            active=bool(data.get(prefix+'_active')); apps=data.get(prefix+'_apps') or []
            widgets[1].setText('Em uso agora' if active else 'Sem uso')
            widgets[1].setStyleSheet('color:#ffad66;font-weight:650' if active else 'color:#7fe0a8;font-weight:650')
            widgets[2].setText('Aplicativos: '+', '.join(map(str,apps)) if apps else 'Nenhum aplicativo detectado nesta sessão.')
def main():
    app=QApplication(sys.argv); w=Privacy(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
