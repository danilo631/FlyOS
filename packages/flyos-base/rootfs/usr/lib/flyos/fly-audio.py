#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import sys
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtWidgets import QApplication,QComboBox,QHBoxLayout,QLabel,QMainWindow,QPushButton,QSlider,QVBoxLayout,QWidget
sys.path.insert(0,'/usr/lib/flyos')
from flyplatform import audio_endpoints,audio_set_default,audio_set_volume,audio_toggle_mute,audio_volume
class Audio(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle('Fly Audio'); self.resize(650,470); self.updating=False
  root=QWidget(); b=QVBoxLayout(root); b.setContentsMargins(26,22,26,22); b.setSpacing(14)
  t=QLabel('Áudio'); t.setStyleSheet('font-size:29px;font-weight:750'); b.addWidget(t)
  self.out=QComboBox(); self.out.currentIndexChanged.connect(lambda _i:self.change(False)); b.addWidget(QLabel('Saída')); b.addWidget(self.out)
  self.vol=QSlider(Qt.Orientation.Horizontal); self.vol.setRange(0,150); self.vol.sliderReleased.connect(lambda:self.volume(False)); b.addWidget(QLabel('Volume de saída')); b.addWidget(self.vol)
  mute=QPushButton('Alternar mute da saída'); mute.clicked.connect(lambda:self.mute(False)); b.addWidget(mute)
  self.inp=QComboBox(); self.inp.currentIndexChanged.connect(lambda _i:self.change(True)); b.addWidget(QLabel('Entrada / microfone')); b.addWidget(self.inp)
  self.mic=QSlider(Qt.Orientation.Horizontal); self.mic.setRange(0,150); self.mic.sliderReleased.connect(lambda:self.volume(True)); b.addWidget(QLabel('Volume do microfone')); b.addWidget(self.mic)
  mm=QPushButton('Alternar mute do microfone'); mm.clicked.connect(lambda:self.mute(True)); b.addWidget(mm)
  note=QLabel('Fly Audio usa WirePlumber diretamente. Configurações avançadas continuam disponíveis por ferramentas upstream opcionais.'); note.setWordWrap(True); note.setStyleSheet('color:#aab4c4'); b.addWidget(note)
  self.setCentralWidget(root); self.setStyleSheet('QMainWindow,QWidget{background:#11161f;color:#f6f8fb} QComboBox,QPushButton{background:#1c2532;border:1px solid #344258;border-radius:10px;padding:9px;color:#f6f8fb}')
  self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(5000); self.refresh()
 def fill(self,combo,items):
  combo.blockSignals(True); combo.clear(); idx=0
  for i,x in enumerate(items): combo.addItem(x['label'],x['id']); idx=i if x.get('default') else idx
  if combo.count():combo.setCurrentIndex(idx)
  combo.blockSignals(False)
 def refresh(self):
  self.updating=True; self.fill(self.out,audio_endpoints(False)); self.fill(self.inp,audio_endpoints(True)); self.vol.setValue(audio_volume(False)[0]); self.mic.setValue(audio_volume(True)[0]); self.updating=False
 def change(self,source):
  if self.updating:return
  combo=self.inp if source else self.out; ident=combo.currentData();
  if ident: audio_set_default(str(ident)); QTimer.singleShot(300,self.refresh)
 def volume(self,source): audio_set_volume(self.mic.value() if source else self.vol.value(),source)
 def mute(self,source): audio_toggle_mute(source); QTimer.singleShot(250,self.refresh)
def main():
 app=QApplication(sys.argv); w=Audio(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
