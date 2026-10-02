#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import sys
from PyQt6.QtCore import QThread,pyqtSignal,QTimer
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QInputDialog,QLabel,QListWidget,QListWidgetItem,QMainWindow,QMessageBox,QPushButton,QVBoxLayout,QWidget,QLineEdit,QDialog
sys.path.insert(0,'/usr/lib/flyos')
from flyplatform import nm_hotspot,nm_hotspot_stop,nm_primary_connection_name,nm_set_radio,nm_wifi_networks,nm_radio
class Scan(QThread):
 done=pyqtSignal(list)
 def run(self): self.done.emit(nm_wifi_networks(True))
class Connect(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('Fly Connect'); self.resize(720,610); self.worker=None
  root=QWidget(); b=QVBoxLayout(root); b.setContentsMargins(24,22,24,22); b.setSpacing(11)
  t=QLabel('Wi‑Fi e rede'); t.setStyleSheet('font-size:29px;font-weight:750'); b.addWidget(t); self.state=QLabel(); b.addWidget(self.state)
  row=QHBoxLayout(); self.wifi=QPushButton(); self.wifi.clicked.connect(self.toggle_wifi); row.addWidget(self.wifi); scan=QPushButton('Procurar redes'); scan.clicked.connect(self.scan); row.addWidget(scan); hot=QPushButton('Criar hotspot'); hot.clicked.connect(self.hotspot); row.addWidget(hot); stop=QPushButton('Parar hotspot'); stop.clicked.connect(self.stop_hotspot); row.addWidget(stop); bt=QPushButton('Bluetooth'); bt.clicked.connect(lambda:__import__('subprocess').Popen(['fly-bluetooth'])); row.addWidget(bt); b.addLayout(row)
  self.list=QListWidget(); self.list.itemDoubleClicked.connect(self.connect_selected); b.addWidget(self.list,1)
  note=QLabel('O Fly Connect usa a API D-Bus oficial do NetworkManager. Senhas são enviadas apenas ao NetworkManager e não são gravadas pelo Fly OS.'); note.setWordWrap(True); note.setStyleSheet('color:#aab4c4'); b.addWidget(note)
  self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f6f8fb} QListWidget,QPushButton{background:#1c2532;border:1px solid #344258;border-radius:10px;padding:9px;color:#f6f8fb} QListWidget::item{padding:11px} QListWidget::item:selected{background:#365f98}')
  self.scan(); QTimer.singleShot(500,self.refresh_state)
 def refresh_state(self):
  on=nm_radio('wifi'); self.wifi.setText('Desligar Wi‑Fi' if on else 'Ligar Wi‑Fi'); self.state.setText(nm_primary_connection_name())
 def toggle_wifi(self): nm_set_radio('wifi',not nm_radio('wifi')); QTimer.singleShot(600,self.refresh_state)
 def scan(self):
  if self.worker and self.worker.isRunning():return
  self.state.setText('Procurando redes…'); self.worker=Scan(self); self.worker.done.connect(self.show_networks); self.worker.start()
 def show_networks(self,items):
  self.list.clear()
  for n in items:
   lock='🔒 ' if n['secure'] else ''; mark='✓ ' if n['active'] else ''; it=QListWidgetItem(f"{mark}{lock}{n['ssid']}   {n['strength']}%"); it.setData(32,n); self.list.addItem(it)
  self.refresh_state()
 def connect_selected(self,it):
  n=it.data(32); pwd=''
  if n.get('secure'):
   pwd,ok=QInputDialog.getText(self,'Conectar ao Wi‑Fi',f'Senha de {n["ssid"]}:',QLineEdit.EchoMode.Password)
   if not ok:return
  if not nm_connect_wifi(n['ssid'],pwd): QMessageBox.warning(self,'Fly Connect','O NetworkManager não conseguiu ativar essa rede. Confira a senha e o adaptador.')
  QTimer.singleShot(1600,self.scan)
 def hotspot(self):
  ssid,ok=QInputDialog.getText(self,'Fly Hotspot','Nome da rede:',text='Fly Hotspot')
  if not ok:return
  pwd,ok=QInputDialog.getText(self,'Fly Hotspot','Senha WPA2 (8–63 caracteres):',QLineEdit.EchoMode.Password)
  if not ok:return
  if not nm_hotspot(ssid.strip(),pwd): QMessageBox.warning(self,'Fly Hotspot','Não foi possível criar o hotspot. O adaptador pode não suportar modo AP.')
  QTimer.singleShot(1200,self.refresh_state)
 def stop_hotspot(self): nm_hotspot_stop(); QTimer.singleShot(800,self.refresh_state)
def main():
 app=QApplication(sys.argv); w=Connect(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
