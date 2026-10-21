"""设置：常规、阅读、朗读、文字识别、AI 中台、更新与关于。"""
from __future__ import annotations

import sys

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from ... import APP_DISPLAY_NAME, __version__
from ...config import Settings
from ..widgets import Segmented, label
from .ai_settings import HubPage, OcrPage, TtsPage
from .base import section


def _row(label_text: str, widget, hint: str = "") -> QHBoxLayout:
    r = QHBoxLayout()
    r.setSpacing(12)
    lb = QLabel(label_text)
    lb.setFixedWidth(96)
    r.addWidget(lb)
    if isinstance(widget, QWidget):
        r.addWidget(widget, 1)
    else:
        r.addLayout(widget, 1)
    if hint:
        h = QLabel(hint)
        h.setObjectName("Faint")
        r.addWidget(h)
    return r


class SettingsDialog(QDialog):
    PAGES = [("general", "常规"), ("reading", "阅读"), ("tts", "朗读"), ("ocr", "文字识别"), ("ai", "AI 中台"),
             ("about", "更新与关于")]

    def __init__(self, parent, settings: Settings, page: str = ""):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.resize(900, 620)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("Surface")
        nav.setFixedWidth(180)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 18, 12, 12)
        t = QLabel("设置")
        t.setObjectName("H2")
        t.setContentsMargins(8, 0, 0, 8)
        nl.addWidget(t)
        self.nav = QListWidget()
        for key, text in self.PAGES:
            it = QListWidgetItem(text)
            it.setData(Qt.UserRole, key)
            self.nav.addItem(it)
        nl.addWidget(self.nav, 1)
        root.addWidget(nav)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.stack = QStackedWidget()
        self.hub_page = HubPage(settings)
        self.tts_page = TtsPage(settings, self.hub_page)
        self.ocr_page = OcrPage(settings, self.hub_page)
        self.tts_page.openHub.connect(lambda: self.show_page("ai"))
        self.ocr_page.openHub.connect(lambda: self.show_page("ai"))
        self.stack.addWidget(self._general())
        self.stack.addWidget(self._reading())
        self.stack.addWidget(self.tts_page)
        self.stack.addWidget(self.ocr_page)
        self.stack.addWidget(self.hub_page)
        self.stack.addWidget(self._about())
        right.addWidget(self.stack, 1)
        foot = QFrame()
        foot.setObjectName("DialogFooter")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(22, 12, 22, 12)
        fl.addStretch(1)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("保存")
        ok.setProperty("primary", True)
        ok.clicked.connect(self._save)
        fl.addWidget(cancel)
        fl.addWidget(ok)
        right.addWidget(foot)
        rw = QWidget()
        rw.setLayout(right)
        root.addWidget(rw, 1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.show_page(page)

    def show_page(self, key: str):
        keys = [k for k, _ in self.PAGES]
        self.nav.setCurrentRow(keys.index(key) if key in keys else 0)

    def _page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("H2")
        lay.addWidget(t)
        return w, lay

    # ---------------------------------------------------------------- 常规
    def _general(self) -> QWidget:
        w, lay = self._page("常规")
        lay.addWidget(section("界面主题"))
        self.theme = Segmented([("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")], self.settings.get("ui/theme"))
        lay.addWidget(self.theme)
        lay.addSpacing(6)
        lay.addWidget(section("打开文件"))
        self.restore = QCheckBox("打开文件时回到上次阅读的位置")
        self.restore.setChecked(bool(self.settings.get("view/restore_position")))
        lay.addWidget(self.restore)
        if sys.platform == "win32":
            lay.addSpacing(6)
            lay.addWidget(section("资源管理器右键菜单"))
            self.context_menu = QCheckBox("右键 PDF 时显示「用 Folio 压缩」「用 Folio 合并」，右键图片时显示「用 Folio 转为 PDF」")
            self.context_menu.setChecked(bool(self.settings.get("shell/context_menu")))
            lay.addWidget(self.context_menu)
            hint = QLabel("可以一次选中多个文件再右键，它们会放进同一个窗口。Windows 11 上在「显示更多选项」里"
                          "（或按住 Shift 再右键）。")
            hint.setObjectName("Faint")
            hint.setWordWrap(True)
            lay.addWidget(hint)
            lay.addSpacing(6)
            lay.addWidget(section("默认程序"))
            b = QPushButton("设为默认 PDF 阅读器…")
            b.clicked.connect(self._set_default_app)
            row = QHBoxLayout()
            row.addWidget(b)
            row.addStretch(1)
            lay.addLayout(row)
            hint = QLabel("会把 Folio 注册为 PDF 的打开方式，然后打开 Windows「默认应用」设置，在那里选择 Folio。")
            hint.setObjectName("Faint")
            hint.setWordWrap(True)
            lay.addWidget(hint)
        lay.addStretch(1)
        return w

    def _set_default_app(self):
        from ...platform_win import register_file_association

        ok, msg = register_file_association()
        if ok:
            QDesktopServices.openUrl(QUrl("ms-settings:defaultapps"))
        QMessageBox.information(self, "设为默认", msg)

    # ---------------------------------------------------------------- 阅读
    def _reading(self) -> QWidget:
        w, lay = self._page("阅读")
        lay.addWidget(section("页面颜色"))
        self.tone = Segmented([("normal", "默认"), ("sepia", "护眼（米黄）"), ("night", "夜间（反色）")],
                              self.settings.get("view/tone"))
        lay.addWidget(self.tone)
        lay.addSpacing(6)
        lay.addWidget(section("页面布局"))
        self.double = QCheckBox("默认双页显示")
        self.double.setChecked(self.settings.get("view/layout") == "double")
        lay.addWidget(self.double)
        lay.addStretch(1)
        return w

    # ---------------------------------------------------------------- 更新与关于
    def _about(self) -> QWidget:
        from ... import update

        w, lay = self._page("更新与关于")
        import time

        lay.addWidget(label(f"{APP_DISPLAY_NAME} {__version__}", "H3"))
        lay.addWidget(label("PDF 阅读、批注、朗读与处理工具。基于 PySide6 (Qt) 与 PyMuPDF，图标来自 Lucide。", "Muted", wrap=True))
        lay.addSpacing(6)
        lay.addWidget(section("自动更新"))
        self.auto_update = QCheckBox("自动检查新版本（每天最多一次）")
        self.auto_update.setChecked(bool(self.settings.get("update/auto")))
        lay.addWidget(self.auto_update)
        self.feed = QLineEdit(self.settings.get("update/feed") or "")
        self.feed.setPlaceholderText(update.DEFAULT_FEED)
        lay.addLayout(_row("更新地址", self.feed))
        lay.addWidget(label("一般不用改。访问 GitHub 慢时，可以把 latest.json 和安装包放到自己的服务器上，再把地址填到这里。"
                            "下载的安装包会校验 SHA-256；程序有数字签名时，还会确认新版本是同一个签名者。", "Faint", wrap=True))
        crow = QHBoxLayout()
        b = QPushButton("检查更新")
        b.setProperty("primary", True)
        b.clicked.connect(self._check_update)
        crow.addWidget(b)
        last = float(self.settings.get("update/last_check") or 0)
        self.update_status = label(time.strftime("上次检查：%Y-%m-%d %H:%M", time.localtime(last)) if last else "还没有检查过",
                                   "Muted", wrap=True)
        crow.addWidget(self.update_status, 1)
        lay.addLayout(crow)
        lay.addStretch(1)
        return w

    def _check_update(self):
        self.settings.set("update/feed", self.feed.text().strip())
        parent = self.parent()
        if parent is not None and hasattr(parent, "check_update"):
            self.update_status.setText("正在检查…")
            parent.check_update(silent=False, dialog_parent=self, status=self.update_status.setText)

    # ---------------------------------------------------------------- 保存
    def _save(self):
        st = self.settings
        st.set("ui/theme", self.theme.value())
        st.set("view/restore_position", self.restore.isChecked())
        st.set("view/tone", self.tone.value())
        st.set("view/layout", "double" if self.double.isChecked() else "single")
        self.hub_page.save()
        self.tts_page.save()
        self.ocr_page.save()
        st.set("update/auto", self.auto_update.isChecked())
        st.set("update/feed", self.feed.text().strip())
        if hasattr(self, "context_menu") and self.context_menu.isChecked() != bool(st.get("shell/context_menu")):
            st.set("shell/context_menu", self.context_menu.isChecked())
            from ...platform_win import sync_context_menu

            sync_context_menu(self.context_menu.isChecked())  # 只在开关改变时写注册表
        st.sync()
        parent = self.parent()
        if parent is not None and hasattr(parent, "set_tone"):
            parent.set_tone(self.tone.value())
        self.accept()
