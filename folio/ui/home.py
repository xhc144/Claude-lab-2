"""主页：打开文件、常用工具、最近打开。"""
from __future__ import annotations

import hashlib
import os
import time

import pymupdf
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
                               QVBoxLayout, QWidget)

from .. import __version__
from ..config import Settings, cache_dir
from ..icons import logo_pixmap, pixmap
from ..theme import theme
from .widgets import ElidedLabel, IconButton

TOOLS = [
    ("compress", "压缩 PDF", "设定目标大小，自动找到最合适的压缩程度", "shrink"),
    ("images", "图片转 PDF", "照片、截图、长图一键转换，长图自动分页", "images"),
    ("merge", "合并文件", "PDF、图片、Word/PPT 合成一个 PDF", "combine"),
    ("split", "拆分 PDF", "按页数、页码范围或文件大小拆分", "scissors"),
]


def time_ago(ts: float) -> str:
    d = time.time() - ts
    if d < 60:
        return "刚刚"
    if d < 3600:
        return f"{int(d // 60)} 分钟前"
    if d < 86400:
        return f"{int(d // 3600)} 小时前"
    if d < 86400 * 30:
        return f"{int(d // 86400)} 天前"
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def thumb_for(path: str, width: int = 72) -> QImage | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = hashlib.sha1(f"{path}|{st.st_mtime}|{width}".encode()).hexdigest()
    out = os.path.join(cache_dir("thumbs"), key + ".png")
    if os.path.exists(out):
        img = QImage(out)
        if not img.isNull():
            return img
    try:
        doc = pymupdf.open(path)
        if doc.needs_pass:
            return None
        page = doc[0]
        z = width / max(1, page.rect.width)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
        pix.save(out)
        doc.close()
        return QImage(out)
    except Exception:
        return None


class Card(QFrame):
    clicked = Signal()

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name)
        self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(e)


class ToolCard(Card):
    def __init__(self, title: str, desc: str, icon: str):
        super().__init__("ToolCard")
        self.icon = icon
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        self.badge = QLabel()
        self.badge.setFixedSize(40, 40)
        self.badge.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.badge)
        t = QLabel(title)
        t.setObjectName("H3")
        lay.addWidget(t)
        d = QLabel(desc)
        d.setObjectName("Muted")
        d.setWordWrap(True)
        lay.addWidget(d)
        lay.addStretch(1)
        self.setMinimumHeight(140)
        self.retheme()
        theme.changed.connect(self.retheme)

    def retheme(self):
        self.badge.setPixmap(pixmap(self.icon, theme.c("accent"), 22))
        self.badge.setStyleSheet(f"background: {theme.c('accent_soft')}; border-radius: 10px;")


class DropZone(Card):
    def __init__(self):
        super().__init__("DropZone")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 26)
        lay.setSpacing(20)
        self.icon = QLabel()
        self.icon.setFixedSize(56, 56)
        self.icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.icon)
        col = QVBoxLayout()
        col.setSpacing(4)
        t = QLabel("打开文件")
        t.setObjectName("H2")
        col.addWidget(t)
        d = QLabel("把 PDF 拖到这里，或点击选择文件。也支持 EPUB、XPS 等格式。")
        d.setObjectName("Muted")
        col.addWidget(d)
        lay.addLayout(col, 1)
        self.button = QPushButton("选择文件")
        self.button.setProperty("primary", True)
        self.button.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.button)
        self.retheme()
        theme.changed.connect(self.retheme)

    def retheme(self):
        self.icon.setPixmap(pixmap("file-up", theme.c("accent"), 28))
        self.icon.setStyleSheet(f"background: {theme.c('accent_soft')}; border-radius: 14px;")

    def set_hover(self, on: bool):
        self.setProperty("hover", on)
        self.style().unpolish(self)
        self.style().polish(self)


class RecentRow(Card):
    removeRequested = Signal(str)

    def __init__(self, entry: dict):
        super().__init__("RecentItem")
        self.path = entry["path"]
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 8, 8)
        lay.setSpacing(12)
        self.thumb = QLabel()
        self.thumb.setFixedSize(36, 46)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet(f"background: white; border: 1px solid {theme.c('border')}; border-radius: 3px;")
        lay.addWidget(self.thumb)
        col = QVBoxLayout()
        col.setSpacing(2)
        name = ElidedLabel(os.path.basename(self.path), mode=Qt.ElideRight)
        name.setObjectName("H3")
        col.addWidget(name)
        exists = os.path.exists(self.path)
        sub = os.path.dirname(self.path)
        if not exists:
            sub = "文件已移动或删除 · " + sub
        folder = ElidedLabel(sub)
        folder.setObjectName("Faint")
        col.addWidget(folder)
        lay.addLayout(col, 1)
        when = QLabel(time_ago(entry.get("time", 0)))
        when.setObjectName("Faint")
        lay.addWidget(when)
        rm = IconButton("x", "从列表移除", size=14)
        rm.clicked.connect(lambda: self.removeRequested.emit(self.path))
        lay.addWidget(rm)
        if not exists:
            self.setEnabled(False)

    def set_thumb(self, img: QImage | None):
        if img is None or img.isNull():
            self.thumb.setPixmap(pixmap("file-text", theme.c("text3"), 18))
            return
        pm = QPixmap.fromImage(img).scaled(QSize(34, 44) * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pm.setDevicePixelRatio(2)
        self.thumb.setPixmap(pm)


class HomePage(QScrollArea):
    openRequested = Signal()
    openPath = Signal(str)
    toolRequested = Signal(str)
    settingsRequested = Signal()
    updateRequested = Signal()

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setAcceptDrops(False)
        inner = QWidget()
        inner.setObjectName("Root")
        self.setWidget(inner)
        outer = QHBoxLayout(inner)
        outer.setContentsMargins(32, 36, 32, 36)
        outer.addStretch(1)
        col_w = QWidget()
        col_w.setMaximumWidth(980)
        col_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        outer.addWidget(col_w, 100)
        outer.addStretch(1)
        col = QVBoxLayout(col_w)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(18)

        head = QHBoxLayout()
        head.setSpacing(14)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(48))
        head.addWidget(logo)
        tcol = QVBoxLayout()
        tcol.setSpacing(0)
        h1 = QLabel("Folio")
        h1.setObjectName("H1")
        tcol.addWidget(h1)
        sub = QLabel("阅读 · 批注 · 朗读 · 处理 PDF")
        sub.setObjectName("Muted")
        tcol.addWidget(sub)
        head.addLayout(tcol)
        head.addStretch(1)
        col.addLayout(head)
        col.addSpacing(6)

        self.drop = DropZone()
        self.drop.clicked.connect(self.openRequested.emit)
        self.drop.button.clicked.connect(self.openRequested.emit)
        col.addWidget(self.drop)

        col.addSpacing(4)
        t = QLabel("常用工具")
        t.setObjectName("SectionTitle")
        col.addWidget(t)
        grid = QGridLayout()
        grid.setSpacing(12)
        for k, (key, title, desc, icon) in enumerate(TOOLS):
            card = ToolCard(title, desc, icon)
            card.clicked.connect(lambda k=key: self.toolRequested.emit(k))
            grid.addWidget(card, 0, k)
        col.addLayout(grid)

        col.addSpacing(4)
        rh = QHBoxLayout()
        t2 = QLabel("最近打开")
        t2.setObjectName("SectionTitle")
        rh.addWidget(t2)
        rh.addStretch(1)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setProperty("flat", True)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_recent)
        rh.addWidget(self.clear_btn)
        col.addLayout(rh)
        self.recent_box = QFrame()
        self.recent_box.setObjectName("Card")
        self.recent_lay = QVBoxLayout(self.recent_box)
        self.recent_lay.setContentsMargins(6, 6, 6, 6)
        self.recent_lay.setSpacing(0)
        col.addWidget(self.recent_box)
        col.addStretch(1)

        # 底部：版本和自动更新状态，检查更新、设置的入口
        foot = QHBoxLayout()
        foot.setSpacing(4)
        self.version_label = QLabel()
        self.version_label.setObjectName("Faint")
        foot.addWidget(self.version_label)
        foot.addStretch(1)
        self.update_link = QPushButton("检查更新")
        self.settings_link = QPushButton("设置")
        for b, sig in ((self.update_link, self.updateRequested), (self.settings_link, self.settingsRequested)):
            b.setProperty("flat", True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(sig.emit)
            foot.addWidget(b)
        col.addSpacing(8)
        col.addLayout(foot)
        self._rows: list[RecentRow] = []
        self._thumb_queue: list[RecentRow] = []
        self._thumb_timer = QTimer(self)
        self._thumb_timer.timeout.connect(self._next_thumb)
        self.refresh()
        self.refresh_footer()

    def refresh_footer(self, update_info=None):
        auto = "已开启自动检查更新" if self.settings.get("update/auto") else "自动检查更新已关闭"
        last = float(self.settings.get("update/last_check") or 0)
        when = f"，上次检查：{time_ago(last)}" if last else ""
        self.version_label.setText(f"Folio {__version__} · {auto}{when}")
        if update_info is not None:
            self.update_link.setText(f"安装新版本 {update_info.version}")
        else:
            self.update_link.setText("检查更新")

    def refresh(self):
        if hasattr(self, "version_label"):
            self.refresh_footer(getattr(self.window(), "update_info", None))
        while self.recent_lay.count():
            w = self.recent_lay.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        items = self.settings.recent()
        self._rows = []
        if not items:
            empty = QLabel("还没有打开过文件")
            empty.setObjectName("Faint")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(80)
            self.recent_lay.addWidget(empty)
        for e in items[:12]:
            row = RecentRow(e)
            row.clicked.connect(lambda p=e["path"]: self.openPath.emit(p))
            row.removeRequested.connect(self._remove)
            self.recent_lay.addWidget(row)
            self._rows.append(row)
        self.clear_btn.setVisible(bool(items))
        self._thumb_queue = list(self._rows)
        self._thumb_timer.start(15)

    def _next_thumb(self):
        if not self._thumb_queue:
            self._thumb_timer.stop()
            return
        row = self._thumb_queue.pop(0)
        try:
            row.set_thumb(thumb_for(row.path) if row.isEnabled() else None)
        except RuntimeError:
            pass

    def _remove(self, path):
        self.settings.remove_recent(path)
        self.refresh()

    def _clear_recent(self):
        self.settings.clear_recent()
        self.refresh()

