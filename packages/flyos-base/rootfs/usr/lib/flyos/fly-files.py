#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import os, sys
from pathlib import Path
from gi.repository import Gio
from PyQt6.QtCore import QFileInfo, QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication,QFileIconProvider,QHBoxLayout,QInputDialog,QLabel,QLineEdit,QListWidget,QListWidgetItem,QMainWindow,QMessageBox,QPushButton,QVBoxLayout,QWidget

class FlyFiles(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Fly Files'); self.resize(920,620)
        self.path=Path.home(); self.history=[]; self.icons=QFileIconProvider()
        root=QWidget(); box=QVBoxLayout(root); box.setContentsMargins(18,16,18,18); box.setSpacing(10)
        top=QHBoxLayout();
        back=QPushButton('←'); back.clicked.connect(self.go_back); top.addWidget(back)
        home=QPushButton('Início'); home.clicked.connect(lambda:self.open_dir(Path.home())); top.addWidget(home)
        self.location=QLineEdit(); self.location.returnPressed.connect(self.location_entered); top.addWidget(self.location,1)
        mkdir=QPushButton('Nova pasta'); mkdir.clicked.connect(self.make_dir); top.addWidget(mkdir)
        box.addLayout(top)
        self.title=QLabel(); self.title.setStyleSheet('font-size:22px;font-weight:700'); box.addWidget(self.title)
        self.list=QListWidget(); self.list.setViewMode(QListWidget.ViewMode.IconMode); self.list.setResizeMode(QListWidget.ResizeMode.Adjust); self.list.setIconSize(QSize(48,48)); self.list.setGridSize(QSize(125,92)); self.list.itemDoubleClicked.connect(self.open_item); box.addWidget(self.list,1)
        actions=QHBoxLayout(); rename=QPushButton('Renomear'); rename.clicked.connect(self.rename_item); actions.addWidget(rename); trash=QPushButton('Mover para lixeira'); trash.clicked.connect(self.trash_item); actions.addWidget(trash); actions.addStretch(1); box.addLayout(actions)
        self.setCentralWidget(root); self.setStyleSheet('''QMainWindow,QWidget{background:#11161f;color:#f5f7fb} QLineEdit,QListWidget,QPushButton{background:#1c2431;border:1px solid #303b4e;border-radius:10px;padding:8px;color:#f5f7fb} QListWidget::item{padding:6px} QListWidget::item:selected{background:#345b93}''')
        self.open_dir(self.path, push=False)
    def open_dir(self,p:Path,push=True):
        try:p=p.expanduser().resolve()
        except OSError:return
        if not p.is_dir():return
        if push and self.path!=p:self.history.append(self.path)
        self.path=p; self.location.setText(str(p)); self.title.setText(p.name or str(p)); self.list.clear()
        try: entries=sorted(p.iterdir(), key=lambda x:(not x.is_dir(), x.name.casefold()))
        except OSError as e: QMessageBox.warning(self,'Fly Files',str(e)); return
        for f in entries:
            if f.name.startswith('.') and not bool(os.environ.get('FLY_FILES_SHOW_HIDDEN')): continue
            it=QListWidgetItem(f.name); it.setData(Qt.ItemDataRole.UserRole,str(f));
            info=QFileInfo(str(f)); it.setIcon(self.icons.icon(info)); self.list.addItem(it)
    def go_back(self):
        if self.history:self.open_dir(self.history.pop(),push=False)
    def location_entered(self):
        p=Path(self.location.text()); self.open_dir(p)
    @staticmethod
    def valid_name(name: str) -> bool:
        name=name.strip()
        return bool(name) and name not in {".", ".."} and "/" not in name and "\\" not in name and "\x00" not in name
    def selected(self):
        it=self.list.currentItem(); return Path(it.data(Qt.ItemDataRole.UserRole)) if it else None
    def open_item(self,it):
        p=Path(it.data(Qt.ItemDataRole.UserRole)); self.open_dir(p) if p.is_dir() else QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
    def make_dir(self):
        name,ok=QInputDialog.getText(self,'Nova pasta','Nome:');
        if ok and self.valid_name(name):
            try:(self.path/name.strip()).mkdir(); self.open_dir(self.path,push=False)
            except OSError as e: QMessageBox.warning(self,'Fly Files',str(e))
    def rename_item(self):
        p=self.selected();
        if not p:return
        name,ok=QInputDialog.getText(self,'Renomear','Novo nome:',text=p.name)
        if ok and self.valid_name(name):
            try:p.rename(p.with_name(name.strip())); self.open_dir(self.path,push=False)
            except OSError as e: QMessageBox.warning(self,'Fly Files',str(e))
    def trash_item(self):
        p=self.selected();
        if not p:return
        if QMessageBox.question(self,'Fly Files',f'Mover “{p.name}” para a lixeira?')!=QMessageBox.StandardButton.Yes:return
        try:
            Gio.File.new_for_path(str(p)).trash(None); self.open_dir(self.path,push=False)
        except Exception as e: QMessageBox.warning(self,'Fly Files',str(e))

def main():
    app=QApplication(sys.argv); w=FlyFiles(); w.show(); return app.exec()
if __name__=='__main__': raise SystemExit(main())
