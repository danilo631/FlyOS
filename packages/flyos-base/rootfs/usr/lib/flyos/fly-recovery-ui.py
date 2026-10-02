#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os,subprocess,sys
from pathlib import Path
from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QProgressBar,QPushButton,QTextEdit,QVBoxLayout,QWidget
class Recovery(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('Fly Recovery'); self.resize(760,600); self.proc=None
  root=QWidget(); b=QVBoxLayout(root); b.setContentsMargins(26,22,26,22); b.setSpacing(12)
  t=QLabel('Fly Recovery'); t.setStyleSheet('font-size:30px;font-weight:750'); b.addWidget(t)
  d=QLabel('Reparo seguro, snapshots e diagnóstico sem depender de um terminal.'); d.setStyleSheet('color:#aab4c4'); b.addWidget(d)
  row=QHBoxLayout()
  for text,fn in [('Fly Doctor',lambda:self.local(['fly-doctor'])),('Snapshots',lambda:self.local(['fly-snapshot','status'])),('Reparar pacotes',lambda:self.rootop('apt-repair')),('Reparar boot',lambda:self.rootop('boot-repair'))]:
   x=QPushButton(text); x.clicked.connect(fn); row.addWidget(x)
  b.addLayout(row)
  row2=QHBoxLayout(); reset=QPushButton('Restaurar Fly Shell'); reset.clicked.connect(self.reset_shell); row2.addWidget(reset); cancel=QPushButton('Cancelar update offline'); cancel.clicked.connect(lambda:self.local(['fly-offline-update','cancel'])); row2.addWidget(cancel); row2.addStretch(1); b.addLayout(row2)
  self.progress=QProgressBar(); self.progress.setRange(0,0); self.progress.hide(); b.addWidget(self.progress)
  self.log=QTextEdit(); self.log.setReadOnly(True); b.addWidget(self.log,1)
  self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f5f7fb} QPushButton,QTextEdit{background:#1d2633;border:1px solid #344156;border-radius:10px;padding:9px;color:#f5f7fb}')
  self.local(['fly-offline-update','status'])
 def runq(self,program,args):
  if self.proc: return
  self.proc=QProcess(self); self.proc.setProgram(program); self.proc.setArguments(args); self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels); self.proc.readyReadStandardOutput.connect(self.read); self.proc.finished.connect(self.done); self.progress.show(); self.proc.start()
 def local(self,argv): self.runq(argv[0],argv[1:])
 def rootop(self,op): self.runq('pkexec',['/usr/lib/flyos/fly-recovery-helper',op])
 def read(self):
  if self.proc:self.log.append(bytes(self.proc.readAllStandardOutput()).decode(errors='replace'))
 def done(self,code,_status):
  self.progress.hide(); self.log.append(f'\nOperação concluída (código {code}).'); self.proc=None
 def reset_shell(self):
  cfg=Path.home()/'.config/flyos'
  if cfg.exists():
   stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
   backup=cfg.with_name(f'flyos.recovery-backup-{stamp}')
   cfg.rename(backup)
   try: backup.chmod(0o700)
   except OSError: pass
  subprocess.run(['systemctl','--user','restart','fly-shell.service'],check=False); self.log.append('Preferências do Fly Shell restauradas.')
def main():
 app=QApplication(sys.argv); w=Recovery(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
