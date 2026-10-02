#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QLabel,QListWidget,QListWidgetItem,QMainWindow,QMessageBox,QPushButton,QVBoxLayout,QWidget
sys.path.insert(0,'/usr/lib/flyos')
from flyplatform import bluez_adapter_action, bluez_device_action, bluez_devices, bluez_powered, bluez_set_powered
class Bluetooth(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('Fly Bluetooth'); self.resize(720,570); self.scanning=False
  root=QWidget(); b=QVBoxLayout(root); b.setContentsMargins(24,22,24,22); b.setSpacing(11)
  t=QLabel('Bluetooth'); t.setStyleSheet('font-size:29px;font-weight:750'); b.addWidget(t); self.status=QLabel(); b.addWidget(self.status)
  row=QHBoxLayout(); self.power=QPushButton(); self.power.clicked.connect(self.toggle_power); row.addWidget(self.power); scan=QPushButton('Procurar dispositivos'); scan.clicked.connect(self.scan); row.addWidget(scan); row.addStretch(1); b.addLayout(row)
  self.list=QListWidget(); self.list.currentItemChanged.connect(self.selection); b.addWidget(self.list,1)
  actions=QHBoxLayout();
  self.pair=QPushButton('Parear'); self.pair.clicked.connect(lambda:self.action('pair')); actions.addWidget(self.pair)
  self.connectb=QPushButton('Conectar'); self.connectb.clicked.connect(lambda:self.action('connect')); actions.addWidget(self.connectb)
  self.trust=QPushButton('Confiar'); self.trust.clicked.connect(lambda:self.action('trust')); actions.addWidget(self.trust)
  self.remove=QPushButton('Remover'); self.remove.clicked.connect(lambda:self.action('remove')); actions.addWidget(self.remove); b.addLayout(actions)
  note=QLabel('O Fly OS usa a API D-Bus do BlueZ diretamente; não interpreta saída de clientes Bluetooth de linha de comando. Alguns dispositivos exigem confirmação de PIN pelo agente Bluetooth da sessão.'); note.setWordWrap(True); note.setStyleSheet('color:#aab4c4'); b.addWidget(note)
  self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f6f8fb} QListWidget,QPushButton{background:#1c2532;border:1px solid #344258;border-radius:10px;padding:9px;color:#f6f8fb} QListWidget::item{padding:10px} QListWidget::item:selected{background:#365f98}')
  self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(4000); self.refresh()
 def current(self):
  it=self.list.currentItem(); return it.data(32) if it else None
 def refresh(self):
  powered=bluez_powered(); self.power.setText('Desligar Bluetooth' if powered else 'Ligar Bluetooth'); self.status.setText('Ativo' if powered else 'Desligado'); current=self.current(); self.list.clear()
  for d in bluez_devices():
   marks=[]
   if d['connected']: marks.append('conectado')
   elif d['paired']: marks.append('pareado')
   if d['trusted']: marks.append('confiável')
   it=QListWidgetItem(f"{d['name']}\n{d['address']}" + (f" • {', '.join(marks)}" if marks else '')); it.setData(32,d); self.list.addItem(it)
   if current and current.get('path')==d['path']: self.list.setCurrentItem(it)
  self.selection()
 def selection(self,*_):
  d=self.current(); enabled=bool(d)
  for x in (self.pair,self.connectb,self.trust,self.remove): x.setEnabled(enabled)
  if d:
   self.pair.setText('Pareado' if d['paired'] else 'Parear'); self.pair.setEnabled(not d['paired']); self.connectb.setText('Desconectar' if d['connected'] else 'Conectar'); self.trust.setText('Remover confiança' if d['trusted'] else 'Confiar')
 def toggle_power(self): bluez_set_powered(not bluez_powered()); QTimer.singleShot(500,self.refresh)
 def scan(self):
  if not bluez_powered(): bluez_set_powered(True)
  bluez_adapter_action('discover-start'); self.scanning=True; self.status.setText('Procurando…'); QTimer.singleShot(9000,self.stop_scan)
 def stop_scan(self): bluez_adapter_action('discover-stop'); self.scanning=False; self.refresh()
 def action(self,a):
  d=self.current();
  if not d:return
  real=a
  if a=='connect' and d['connected']: real='disconnect'
  if a=='trust' and d['trusted']: real='untrust'
  if a=='remove' and QMessageBox.question(self,'Fly Bluetooth',f'Remover {d["name"]}?')!=QMessageBox.StandardButton.Yes:return
  if not bluez_device_action(d['path'],real): QMessageBox.warning(self,'Fly Bluetooth','A operação não foi concluída pelo BlueZ.')
  QTimer.singleShot(500,self.refresh)
def main():
 app=QApplication(sys.argv); w=Bluetooth(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
