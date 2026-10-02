#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import subprocess,sys
from PyQt6.QtCore import QProcess,QTimer
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QLabel,QMainWindow,QPushButton,QTextEdit,QVBoxLayout,QWidget
class W(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('Fly Firewall'); self.resize(650,470); root=QWidget(); b=QVBoxLayout(root); b.setContentsMargins(25,22,25,22)
  t=QLabel('Firewall'); t.setStyleSheet('font-size:28px;font-weight:700'); b.addWidget(t); self.state=QLabel(); b.addWidget(self.state)
  row=QHBoxLayout(); on=QPushButton('Ativar'); on.clicked.connect(lambda:self.act('enable')); off=QPushButton('Desativar'); off.clicked.connect(lambda:self.act('disable')); reload=QPushButton('Recarregar'); reload.clicked.connect(lambda:self.act('reload')); row.addWidget(on); row.addWidget(off); row.addWidget(reload); b.addLayout(row)
  self.details=QTextEdit(); self.details.setReadOnly(True); b.addWidget(self.details,1); self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f5f7fb} QPushButton,QTextEdit{background:#1d2633;border:1px solid #344156;border-radius:10px;padding:9px;color:#f5f7fb}'); self.refresh()
 def refresh(self):
  try: t=subprocess.run(['ufw','status','verbose'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=3).stdout
  except Exception:t='UFW não disponível.'
  self.details.setPlainText(t); self.state.setText('Ativo' if 'Status: active' in t else 'Desativado/indisponível')
 def act(self,a):
  QProcess.startDetached('pkexec',['/usr/lib/flyos/fly-firewall-helper',a]); QTimer.singleShot(1800,self.refresh)
def main():
 app=QApplication(sys.argv); w=W(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
