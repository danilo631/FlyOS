#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import shlex, shutil, subprocess, sys
from PyQt6.QtWidgets import QApplication,QInputDialog,QLabel,QMainWindow,QMessageBox,QPushButton,QTextEdit,QVBoxLayout,QWidget

def out(*a:str)->str:
    try:return subprocess.run(a,check=False,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=3).stdout.strip()
    except (OSError,subprocess.TimeoutExpired):return ""
class GPU(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle("Fly GPU");self.resize(700,500)
        root=QWidget();box=QVBoxLayout(root);box.setContentsMargins(26,24,26,24);box.setSpacing(12)
        t=QLabel("Gráficos híbridos");t.setStyleSheet("font-size:28px;font-weight:750");box.addWidget(t)
        d=QLabel("O Fly OS usa render offload por aplicativo. Isso preserva bateria e evita trocar à força o mux/driver do notebook.");d.setWordWrap(True);d.setStyleSheet("color:#aeb8ca");box.addWidget(d)
        self.text=QTextEdit();self.text.setReadOnly(True);box.addWidget(self.text,1)
        launch=QPushButton("Executar aplicativo na GPU dedicada");launch.clicked.connect(self.launch);box.addWidget(launch)
        self.setCentralWidget(root);self.setStyleSheet("QMainWindow,QWidget{background:#11151e;color:#f5f7fb} QTextEdit{background:#171c27;border:1px solid #2a3141;border-radius:14px;padding:12px} QPushButton{background:#202837;border:1px solid #334056;border-radius:11px;padding:10px}")
        self.refresh()
    def refresh(self):
        if shutil.which("switcherooctl"):
            data=out("switcherooctl","list")
        else:
            data="switcheroo-control não está instalado.\n\nGPUs PCI detectadas:\n"+out("sh","-lc","lspci 2>/dev/null | grep -Ei 'VGA|3D|Display' || true")
        self.text.setPlainText(data or "Nenhuma GPU adicional foi detectada.")
    def launch(self):
        if not shutil.which("switcherooctl"):
            QMessageBox.information(self,"Fly GPU","switcheroo-control não está disponível.");return
        cmd,ok=QInputDialog.getText(self,"Executar na GPU dedicada","Comando do aplicativo:")
        if not ok or not cmd.strip():return
        try:argv=shlex.split(cmd)
        except ValueError as e: QMessageBox.warning(self,"Fly GPU",str(e));return
        try:subprocess.Popen(["switcherooctl","launch",*argv],start_new_session=True)
        except OSError as e:QMessageBox.warning(self,"Fly GPU",str(e))
def main():
    app=QApplication(sys.argv);w=GPU();w.show();return app.exec()
if __name__=="__main__":raise SystemExit(main())
