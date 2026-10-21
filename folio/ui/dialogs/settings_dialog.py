"""设置：常规、阅读、朗读、文字识别、AI 中台、更新与关于。"""
from __future__ import annotations

import sys

from PySide6.QtCore import QSize, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from ... import APP_DISPLAY_NAME, __version__
from ...config import Settings
from ...icons import logo_pixmap, pixmap, themed
from ...theme import theme
from ..widgets import Segmented, Switch, label
from .ai_settings import HubPage, OcrPage, TtsPage, group, page, row


class SettingsDialog(QDialog):
    """左边导航，右边每页是一组组卡片（和 Windows 11 的「设置」一样的排版）。"""
    PAGES = [("general", "常规", "settings"), ("reading", "阅读", "book-open"), ("tts", "朗读", "volume-2"),
             ("ocr", "文字识别", "scan-text"), ("ai", "AI 中台", "wand-sparkles"), ("about", "更新与关于", "info")]

    def __init__(self, parent, settings: Settings, page: str = ""):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.resize(940, 660)
        self.setMinimumSize(760, 520)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QFrame()
        nav.setFixedWidth(200)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(14, 24, 10, 14)
        nl.setSpacing(14)
        nl.addWidget(label("设置", "PageTitle"), 0)
        self.nav = QListWidget()
        self.nav.setObjectName("SettingsNav")
        self.nav.setIconSize(QSize(18, 18))
        self.nav.setFocusPolicy(Qt.NoFocus)
        for key, text, icon in self.PAGES:
            ic = themed(icon, 18, "text2")
            ic.addPixmap(pixmap(icon, theme.c("accent"), 18), QIcon.Selected, QIcon.Off)  # 选中的一项图标也用强调色
            it = QListWidgetItem(ic, text)
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
        foot.setObjectName("SettingsFooter")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(28, 12, 28, 12)
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
        keys = [k for k, _, _ in self.PAGES]
        self.nav.setCurrentRow(keys.index(key) if key in keys else 0)

    # ---------------------------------------------------------------- 常规
    def _general(self) -> QWidget:
        w, lay = page("常规")
        card = group(lay, "外观")
        self.theme = Segmented([("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")], self.settings.get("ui/theme"))
        card.add_row("界面主题", "浅色、深色，或者跟着系统的设置自动切换。", self.theme)
        card = group(lay, "打开文件")
        self.restore = Switch(bool(self.settings.get("view/restore_position")))
        card.add_row("回到上次阅读的位置", "再次打开同一个文件时，自动翻到上次看到的那一页。", self.restore)
        if sys.platform == "win32":
            card = group(lay, "Windows")
            self.context_menu = Switch(bool(self.settings.get("shell/context_menu")))
            card.add_row("资源管理器右键菜单",
                         "右键 PDF 时显示「用 Folio 压缩」「用 Folio 合并」，右键图片时显示「用 Folio 转为 PDF」。"
                         "可以一次选中多个文件再右键，它们会放进同一个窗口。", self.context_menu)
            b = QPushButton("设为默认…")
            b.clicked.connect(self._set_default_app)
            card.add_row("默认 PDF 阅读器", "把 Folio 注册为 PDF 的打开方式，然后在 Windows「默认应用」设置里选择 Folio。", b)
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
        w, lay = page("阅读")
        card = group(lay, "显示")
        self.tone = Segmented([("normal", "默认"), ("sepia", "护眼"), ("night", "夜间")], self.settings.get("view/tone"))
        card.add_row("页面颜色", "护眼是米黄色的纸张，夜间会把页面反色成深色。", self.tone)
        self.double = Switch(self.settings.get("view/layout") == "double")
        card.add_row("双页显示", "新打开的文件默认两页并排显示，适合宽屏。", self.double)
        lay.addStretch(1)
        return w

    # ---------------------------------------------------------------- 更新与关于
    def _about(self) -> QWidget:
        from ... import update

        w, lay = page("更新与关于")
        import time

        card = group(lay, "关于")
        head = QHBoxLayout()
        head.setSpacing(14)
        logo = label("")
        logo.setPixmap(logo_pixmap(44))
        head.addWidget(logo, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        texts.addWidget(label(f"{APP_DISPLAY_NAME} {__version__}", "H3"))
        texts.addWidget(label("PDF 阅读、批注、朗读与处理工具。基于 PySide6 (Qt) 与 PyMuPDF，图标来自 Lucide。", "Muted", wrap=True))
        head.addLayout(texts, 1)
        card.add(head)

        card = group(lay, "自动更新")
        b = QPushButton("检查更新")
        b.setProperty("primary", True)
        b.clicked.connect(self._check_update)
        last = float(self.settings.get("update/last_check") or 0)
        status = card.add_row("检查新版本", "", b)
        self.update_status = label(time.strftime("上次检查：%Y-%m-%d %H:%M", time.localtime(last)) if last else "还没有检查过",
                                   "Faint", wrap=True)
        status.text_layout.addWidget(self.update_status)
        self.auto_update = Switch(bool(self.settings.get("update/auto")))
        card.add_row("自动检查新版本", "每天最多检查一次，有新版本时在右上角提示。", self.auto_update)
        feed = card.add_block(8)
        self.feed = QLineEdit(self.settings.get("update/feed") or "")
        self.feed.setPlaceholderText(update.DEFAULT_FEED)
        feed.addLayout(row("更新地址", self.feed, width=72))
        feed.addWidget(label("一般不用改。访问 GitHub 慢时，可以把 latest.json 和安装包放到自己的服务器上，再把地址填到这里。"
                             "下载的安装包会校验 SHA-256；程序有数字签名时，还会确认新版本是同一个签名者。", "Faint", wrap=True))
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
