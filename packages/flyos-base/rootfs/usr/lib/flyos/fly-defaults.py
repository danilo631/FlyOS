#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import configparser, subprocess, sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication,QComboBox,QFrame,QGridLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QVBoxLayout,QWidget
APP_DIRS=[Path.home()/'.local/share/applications',Path('/var/lib/flatpak/exports/share/applications'),Path('/usr/local/share/applications'),Path('/usr/share/applications')]
TYPES=[('Navegador','x-scheme-handler/https'),('PDF','application/pdf'),('Imagens','image/jpeg'),('Vídeo','video/mp4'),('Áudio','audio/mpeg'),('Texto','text/plain')]
def apps():
    found={}
    for d in APP_DIRS:
        if not d.is_dir(): continue
        for f in d.glob('*.desktop'):
            try:
                c=configparser.ConfigParser(interpolation=None,strict=False); c.read(f,encoding='utf-8'); sec=c['Desktop Entry']
                if sec.get('Type','')!='Application' or sec.getboolean('NoDisplay',fallback=False): continue
                found.setdefault(f.name,sec.get('Name',f.stem))
            except Exception: continue
    return sorted(found.items(),key=lambda x:x[1].casefold())
def current(mime):
    try: return subprocess.run(['xdg-mime','query','default',mime],text=True,capture_output=True,timeout=2,check=False).stdout.strip()
    except Exception: return ''
class Win(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Fly Defaults'); self.resize(650,500); self.data=apps(); self.boxes={}
        root=QWidget(); layout=QVBoxLayout(root); layout.setContentsMargins(26,24,26,24); layout.setSpacing(14)
        t=QLabel('Aplicativos padrão'); t.setObjectName('title'); layout.addWidget(t)
        h=QLabel('Escolha seus próprios apps. O Fly OS grava padrões XDG compatíveis com aplicativos Linux, Flatpak e ambientes de desktop.'); h.setWordWrap(True); h.setObjectName('muted'); layout.addWidget(h)
        card=QFrame(); card.setObjectName('card'); grid=QGridLayout(card); grid.setContentsMargins(18,16,18,16); grid.setHorizontalSpacing(14); grid.setVerticalSpacing(12)
        for row,(label,mime) in enumerate(TYPES):
            grid.addWidget(QLabel(label),row,0); combo=QComboBox(); combo.addItem('Não alterar','')
            for did,name in self.data: combo.addItem(name,did)
            cur=current(mime); idx=combo.findData(cur)
            if idx>=0: combo.setCurrentIndex(idx)
            self.boxes[mime]=combo; grid.addWidget(combo,row,1)
        layout.addWidget(card); save=QPushButton('Salvar padrões'); save.clicked.connect(self.save); layout.addWidget(save); layout.addStretch(1)
        self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f7f8fc} QLabel#title{font-size:28px;font-weight:750} QLabel#muted{color:rgba(225,232,245,.67)} QFrame#card{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.09);border-radius:16px} QPushButton,QComboBox{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11);border-radius:10px;min-height:38px;padding:0 12px;color:#f7f8fc}')
    def save(self):
        errors=[]
        for mime,combo in self.boxes.items():
            did=str(combo.currentData() or '')
            if not did: continue
            p=subprocess.run(['xdg-mime','default',did,mime],capture_output=True,text=True,check=False)
            if p.returncode: errors.append(mime)
        QMessageBox.information(self,'Fly Defaults','Padrões atualizados.' if not errors else 'Alguns padrões não puderam ser alterados: '+', '.join(errors))
def main():
    app=QApplication(sys.argv); w=Win(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
