"""发现新版本时的提示窗口：显示更新说明，下载、校验并在退出后安装。"""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextBrowser,
                               QVBoxLayout)

from ... import __version__, update
from ..widgets import label
from .base import Worker


class UpdateDialog(QDialog):
    def __init__(self, main, info: update.UpdateInfo, parent=None):
        super().__init__(parent or main)
        self.main, self.info = main, info
        self.setWindowTitle("发现新版本")
        self.resize(520, 440)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 16)
        lay.setSpacing(10)
        t = QLabel(f"Folio {info.version} 已发布")
        t.setObjectName("H2")
        lay.addWidget(t)
        lay.addWidget(label(f"当前版本 {__version__}" + (f" · 发布于 {info.date[:10]}" if info.date else ""), "Muted"))
        notes = QTextBrowser()
        notes.setOpenExternalLinks(True)
        notes.setMarkdown(info.notes or "（没有更新说明）")
        lay.addWidget(notes, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.hide()
        lay.addWidget(self.progress)
        self.status = label("", "Muted", wrap=True)
        lay.addWidget(self.status)

        foot = QFrame()
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(0, 4, 0, 0)
        self.skip_btn = QPushButton("跳过这个版本")
        self.skip_btn.setProperty("flat", True)
        self.skip_btn.clicked.connect(self._skip)
        fl.addWidget(self.skip_btn)
        fl.addStretch(1)
        self.later_btn = QPushButton("以后再说")
        self.later_btn.clicked.connect(self._later)
        fl.addWidget(self.later_btn)
        self.ok_btn = QPushButton("立即更新")
        self.ok_btn.setProperty("primary", True)
        self.ok_btn.setDefault(True)
        fl.addWidget(self.ok_btn)
        lay.addWidget(foot)

        self.can_install, why = update.can_self_update()
        if not info.url:
            self.can_install, why = False, "这个版本没有适合当前系统的安装包。"
        if self.can_install:
            self.ok_btn.clicked.connect(self._install)
        else:
            self.ok_btn.setText("打开下载页面")
            self.ok_btn.clicked.connect(self._open_page)
            self.status.setText(why)
        self._worker = None

    def _skip(self):
        self.main.settings.set("update/skip", self.info.version)
        self.reject()

    def _later(self):
        if self._worker is not None:
            self._worker.cancel()
            self._worker.wait(3000)
        self.reject()

    def _open_page(self):
        QDesktopServices.openUrl(QUrl(self.info.page or update.RELEASES_PAGE))
        self.accept()

    def _install(self):
        self.ok_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.later_btn.setText("取消")
        self.progress.setValue(0)
        self.progress.show()
        self.status.setText("正在下载…")
        self._worker = Worker(lambda progress, cancel: update.prepare(self.info, progress, cancel), self)
        self._worker.progress.connect(lambda f, m: (self.progress.setValue(int(f * 1000)), self.status.setText(m)))
        self._worker.done.connect(self._ready)
        self._worker.failed.connect(self._failed)
        self._worker.start()

    def _failed(self, msg: str):
        self._worker = None
        self.progress.hide()
        self.ok_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.later_btn.setText("以后再说")
        self.status.setText(f"⚠ {msg}")

    def _ready(self, new_root: str):
        self._worker = None
        self.progress.setValue(1000)
        self.main.pending_update = new_root
        self.status.setText("✓ 新版本已准备好。Folio 会关闭并自动重新打开（有未保存的文件会先提示保存）。")
        self.accept()
        self.main.close()
