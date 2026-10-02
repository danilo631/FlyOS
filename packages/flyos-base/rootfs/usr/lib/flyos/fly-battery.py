#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import glob, re, shutil, subprocess, sys
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication,QGridLayout,QHBoxLayout,QLabel,QMainWindow,QProgressBar,QPushButton,QVBoxLayout,QWidget

def out(*a:str)->str:
    try:return subprocess.run(a,check=False,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=2).stdout.strip()
    except (OSError,subprocess.TimeoutExpired):return ""

def prop(text:str,name:str)->str:
    m=re.search(rf"^\s*{re.escape(name)}:\s*(.+)$",text,re.M|re.I); return m.group(1).strip() if m else "—"

def read_int(path:Path)->int|None:
    try:return int(path.read_text().strip())
    except (OSError,ValueError):return None

class Battery(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Fly Battery"); self.resize(650,470)
        root=QWidget(); self.box=QVBoxLayout(root); self.box.setContentsMargins(28,24,28,24); self.box.setSpacing(14)
        t=QLabel("Bateria");t.setStyleSheet("font-size:30px;font-weight:750");self.box.addWidget(t)
        self.percent=QProgressBar(); self.percent.setRange(0,100); self.box.addWidget(self.percent)
        self.grid=QGridLayout(); self.box.addLayout(self.grid)
        self.labels={}
        for i,(k,n) in enumerate([("state","Estado"),("rate","Consumo"),("time","Tempo restante"),("health","Saúde estimada"),("cycles","Ciclos"),("profile","Perfil de energia")]):
            self.grid.addWidget(QLabel(n),i,0); lab=QLabel("—");lab.setStyleSheet("font-weight:600");self.grid.addWidget(lab,i,1);self.labels[k]=lab
        row=QHBoxLayout(); care=QPushButton("Ver Battery Care");care.clicked.connect(self.open_care); row.addWidget(care)
        limit80=QPushButton("Limite 80%"); limit80.clicked.connect(lambda: self.set_limit(80)); row.addWidget(limit80)
        limit100=QPushButton("Limite 100%"); limit100.clicked.connect(lambda: self.set_limit(100)); row.addWidget(limit100)
        profiles=QPushButton("Perfis de energia");profiles.clicked.connect(lambda: subprocess.Popen(["fly-center"]));row.addWidget(profiles);row.addStretch(1);self.box.addLayout(row)
        note=QLabel("A saúde é mostrada apenas quando o firmware/kernel expõe capacidade de projeto e capacidade cheia. O Fly OS não inventa um valor em hardware sem suporte.");note.setWordWrap(True);note.setStyleSheet("color:#aeb8ca");self.box.addWidget(note)
        self.setCentralWidget(root);self.setStyleSheet("QMainWindow,QWidget{background:#11151e;color:#f5f7fb} QPushButton{background:#202837;border:1px solid #334056;border-radius:11px;padding:9px 13px} QProgressBar{height:18px;border:0;background:#232b39;border-radius:9px} QProgressBar::chunk{background:#72a7ff;border-radius:9px}")
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(10000);self.refresh()
    def refresh(self):
        text=""; devs=out("upower","-e").splitlines() if shutil.which("upower") else []
        bat=next((x for x in devs if "battery" in x.lower()),"")
        if bat:text=out("upower","-i",bat)
        p=prop(text,"percentage").replace("%","");
        try:self.percent.setValue(int(float(p)))
        except ValueError:self.percent.setValue(0)
        self.percent.setFormat((p+"%") if p not in {"","—"} else "Sem dados")
        self.labels["state"].setText(prop(text,"state")); self.labels["rate"].setText(prop(text,"energy-rate"))
        tm=prop(text,"time to empty"); tm = prop(text,"time to full") if tm=="—" else tm; self.labels["time"].setText(tm)
        health="—";cycles="—"
        for base_s in glob.glob("/sys/class/power_supply/BAT*"):
            base=Path(base_s); full=read_int(base/"energy_full") or read_int(base/"charge_full"); design=read_int(base/"energy_full_design") or read_int(base/"charge_full_design")
            cyc=read_int(base/"cycle_count")
            if full and design and design>0: health=f"{max(0,min(150,round(full/design*100)))}%"
            if cyc is not None and cyc>=0: cycles=str(cyc)
            break
        self.labels["health"].setText(health);self.labels["cycles"].setText(cycles)
        self.labels["profile"].setText(out("powerprofilesctl","get") or "balanced")
    def open_care(self):
        text=out("fly-battery","status")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self,"Battery Care",text or "Sem informação disponível.")
    def set_limit(self,value:int):
        if not shutil.which("fly-battery"): return
        try: subprocess.Popen(["fly-battery","set",str(value)], start_new_session=True)
        except OSError: pass

def main():
    app=QApplication(sys.argv);w=Battery();w.show();return app.exec()
if __name__=="__main__":raise SystemExit(main())
