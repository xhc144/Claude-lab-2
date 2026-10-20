"""主窗口：标签栏、顶部工具栏、工具选项栏、主页与文档页。"""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QFileDialog, QFrame, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QStackedWidget, QTabBar,
                               QVBoxLayout, QWidget)

from .. import APP_DISPLAY_NAME, __version__
from ..config import Settings
from ..core.images import IMAGE_EXTS
from ..core.merge import ALL_EXTS
from ..icons import app_icon
from ..model.document import OPENABLE_EXTS, NeedsPassword, PdfDocument
from ..theme import theme
from ..tts.reader import ReadAloud
from .bars import OptionsBar
from .doc_tab import DocTab
from .home import HomePage
from .tools import EDIT_TOOLS
from .widgets import IconButton, Toast, vline

TOOL_BUTTONS = [
    ("select", "mouse-pointer-2", "选择文字 (V)", "V"),
    ("hand", "hand", "抓手 (H)", "H"),
    ("highlight", "highlighter", "高亮 / 下划线 / 删除线 (U)", "U"),
    ("pen", "pen-line", "画笔 (P)", "P"),
    ("shape", "square", "形状 (S)", "S"),
    ("text", "type", "文本框 (T)", "T"),
    ("note", "sticky-note", "便签 (N)", "N"),
    ("eraser", "eraser", "橡皮擦 (E)", "E"),
    ("laser", "laser", "激光笔 (L)", "L"),
    ("read", "audio-lines", "点读：点哪读哪 (R)", "R"),
]

OPEN_FILTER = ("所有支持的文件 (*.pdf *.epub *.xps *.oxps *.cbz *.fb2 *.mobi);;PDF 文件 (*.pdf);;"
               "电子书 (*.epub *.mobi *.fb2 *.cbz);;所有文件 (*)")


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.reader = ReadAloud(settings)
        self.reader.highlight.connect(self._on_read_highlight)
        self.reader.message.connect(lambda m: self.toast(m, 4000))
        self.setWindowIcon(app_icon())
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1360, 880)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_tabstrip())
        self.topbar = self._build_toolbar()
        lay.addWidget(self.topbar)
        self.options = OptionsBar(settings)
        self.options.changed.connect(self._on_options_changed)
        lay.addWidget(self.options)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        self.home = HomePage(settings)
        self.home.openRequested.connect(self.open_dialog)
        self.home.openPath.connect(self.open_path)
        self.home.toolRequested.connect(self.open_tool)
        self.stack.addWidget(self.home)
        self.tabs_widgets: list[DocTab] = []
        self._toast = Toast(root)
        self._build_shortcuts()
        self._sync_ui()

    # ================================================================ 构建界面
    def _build_tabstrip(self) -> QWidget:
        strip = QFrame()
        strip.setObjectName("TabStrip")
        hl = QHBoxLayout(strip)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(2)
        self.home_btn = IconButton("house", "主页", checkable=True)
        self.home_btn.clicked.connect(self.show_home)
        hl.addWidget(self.home_btn)
        self.tabbar = QTabBar()
        self.tabbar.setObjectName("DocTabs")
        self.tabbar.setTabsClosable(True)
        self.tabbar.setMovable(True)
        self.tabbar.setExpanding(False)
        self.tabbar.setDocumentMode(True)
        self.tabbar.setElideMode(Qt.ElideMiddle)
        self.tabbar.setDrawBase(False)
        self.tabbar.setUsesScrollButtons(True)
        self.tabbar.currentChanged.connect(self._on_tab_changed)
        self.tabbar.tabCloseRequested.connect(self.close_tab)
        self.tabbar.tabMoved.connect(self._on_tab_moved)
        self.tabbar.tabBarClicked.connect(lambda i: i >= 0 and self._show_tab(i))
        hl.addWidget(self.tabbar, 0)
        add = IconButton("plus", "打开文件 (Ctrl+O)", size=16)
        add.clicked.connect(self.open_dialog)
        hl.addWidget(add)
        hl.addStretch(1)
        return strip

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(50)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(10, 6, 10, 6)
        hl.setSpacing(2)

        self.btn_sidebar = IconButton("panel-left", "侧栏 (F4)", checkable=True)
        self.btn_sidebar.clicked.connect(lambda: self.cur and self._toggle_sidebar())
        self.btn_save = IconButton("save", "保存 (Ctrl+S)")
        self.btn_save.clicked.connect(self.save)
        self.btn_undo = IconButton("undo-2", "撤销 (Ctrl+Z)")
        self.btn_undo.clicked.connect(lambda: self.cur and self.cur.doc.undo())
        self.btn_redo = IconButton("redo-2", "重做 (Ctrl+Y)")
        self.btn_redo.clicked.connect(lambda: self.cur and self.cur.doc.redo())
        for b in (self.btn_sidebar, self.btn_save, self.btn_undo, self.btn_redo):
            hl.addWidget(b)
        hl.addSpacing(6)
        hl.addWidget(vline())
        hl.addSpacing(6)

        self.btn_prev = IconButton("chevron-left", "上一页")
        self.btn_prev.clicked.connect(lambda: self.cur and self.cur.view.prev_page())
        hl.addWidget(self.btn_prev)
        self.page_edit = QLineEdit()
        self.page_edit.setObjectName("Compact")
        self.page_edit.setFixedWidth(46)
        self.page_edit.setAlignment(Qt.AlignCenter)
        self.page_edit.returnPressed.connect(self._goto_typed_page)
        hl.addWidget(self.page_edit)
        self.page_total = QLabel("/ 0")
        self.page_total.setObjectName("Muted")
        self.page_total.setMinimumWidth(40)
        hl.addSpacing(4)
        hl.addWidget(self.page_total)
        self.btn_next = IconButton("chevron-right", "下一页")
        self.btn_next.clicked.connect(lambda: self.cur and self.cur.view.next_page())
        hl.addWidget(self.btn_next)
        hl.addSpacing(6)
        hl.addWidget(vline())
        hl.addSpacing(6)

        self.btn_zoom_out = IconButton("zoom-out", "缩小 (Ctrl+-)")
        self.btn_zoom_out.clicked.connect(lambda: self.cur and self.cur.view.zoom_step(-1))
        hl.addWidget(self.btn_zoom_out)
        self.zoom_box = QComboBox()
        self.zoom_box.setEditable(True)
        self.zoom_box.setFixedWidth(104)
        self.zoom_box.setInsertPolicy(QComboBox.NoInsert)
        self.zoom_box.addItem("适合宽度", "width")
        self.zoom_box.addItem("适合页面", "page")
        for z in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0):
            self.zoom_box.addItem(f"{int(z * 100)}%", z)
        self.zoom_box.activated.connect(self._zoom_chosen)
        self.zoom_box.lineEdit().returnPressed.connect(self._zoom_typed)
        hl.addWidget(self.zoom_box)
        self.btn_zoom_in = IconButton("zoom-in", "放大 (Ctrl+=)")
        self.btn_zoom_in.clicked.connect(lambda: self.cur and self.cur.view.zoom_step(1))
        hl.addWidget(self.btn_zoom_in)
        self.btn_layout = IconButton("double-page", "双页显示")
        self.btn_layout.setCheckable(True)
        self.btn_layout.clicked.connect(self._toggle_layout)
        hl.addWidget(self.btn_layout)

        hl.addStretch(1)
        # ---- 工具 ----
        tools = QFrame()
        tools.setObjectName("Segmented")
        tl = QHBoxLayout(tools)
        tl.setContentsMargins(3, 3, 3, 3)
        tl.setSpacing(1)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_btns: dict[str, IconButton] = {}
        for name, icon, tip, _ in TOOL_BUTTONS:
            b = IconButton(icon, tip, checkable=True)
            b.setFixedSize(QSize(34, 32))
            b.clicked.connect(lambda _=False, n=name: self.select_tool(n))
            self.tool_group.addButton(b)
            self.tool_btns[name] = b
            tl.addWidget(b)
            if name in ("hand", "eraser"):
                sep = vline(18)
                tl.addSpacing(2)
                tl.addWidget(sep)
                tl.addSpacing(2)
        self.tool_btns["select"].setChecked(True)
        hl.addWidget(tools)
        hl.addStretch(1)

        # ---- 右侧 ----
        self.btn_search = IconButton("search", "搜索 (Ctrl+F)")
        self.btn_search.clicked.connect(lambda: self.search())
        hl.addWidget(self.btn_search)
        self.btn_tools = IconButton("wand-sparkles", "PDF 工具", text="工具")
        self.btn_tools.setPopupMode(IconButton.InstantPopup)
        self.btn_tools.setMenu(self._build_tools_menu())
        hl.addWidget(self.btn_tools)
        self.btn_print = IconButton("printer", "打印 (Ctrl+P)")
        self.btn_print.clicked.connect(self.print_doc)
        hl.addWidget(self.btn_print)
        self.btn_present = IconButton("presentation", "演示模式 (F5)")
        self.btn_present.clicked.connect(self.present)
        hl.addWidget(self.btn_present)
        self.btn_tone = IconButton("sun-moon", "页面颜色与主题")
        self.btn_tone.setPopupMode(IconButton.InstantPopup)
        self.btn_tone.setMenu(self._build_tone_menu())
        hl.addWidget(self.btn_tone)
        self.btn_more = IconButton("ellipsis", "更多")
        self.btn_more.setPopupMode(IconButton.InstantPopup)
        self.btn_more.setMenu(self._build_more_menu())
        hl.addWidget(self.btn_more)
        return bar

    def _build_tools_menu(self) -> QMenu:
        m = QMenu(self)
        m.addAction("压缩 PDF…", lambda: self.open_tool("compress"))
        m.addAction("图片转 PDF…", lambda: self.open_tool("images"))
        m.addAction("合并文件…", lambda: self.open_tool("merge"))
        m.addAction("拆分 PDF…", lambda: self.open_tool("split"))
        m.addSeparator()
        self.act_insert_blank = m.addAction("在当前页后插入空白页", lambda: self.cur and self.cur.doc.insert_blank(self.cur.view.current_page))
        self.act_insert_file = m.addAction("在当前页后插入文件…", lambda: self.cur and self.cur.sidebar.thumbs._insert_file(self.cur.view.current_page + 1))
        self.act_rotate = m.addAction("旋转当前页", lambda: self.cur and self.cur.doc.rotate_pages([self.cur.view.current_page], 90))
        self.act_delete_page = m.addAction("删除当前页", self._delete_current_page)
        self.act_extract = m.addAction("提取页面…", self._extract_pages)
        self.page_actions = [self.act_insert_blank, self.act_insert_file, self.act_rotate, self.act_delete_page]
        return m

    def _build_tone_menu(self) -> QMenu:
        m = QMenu(self)
        m.addSection("页面颜色")
        g = QActionGroup(self)
        self.tone_actions = {}
        for key, text in (("normal", "默认"), ("sepia", "护眼（米黄）"), ("night", "夜间（反色）")):
            a = QAction(text, self, checkable=True)
            a.triggered.connect(lambda _=False, k=key: self.set_tone(k))
            g.addAction(a)
            m.addAction(a)
            self.tone_actions[key] = a
        self.tone_actions.get(self.settings.get("view/tone"), self.tone_actions["normal"]).setChecked(True)
        m.addSection("界面主题")
        g2 = QActionGroup(self)
        for key, text in (("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")):
            a = QAction(text, self, checkable=True)
            a.setChecked(self.settings.get("ui/theme") == key)
            a.triggered.connect(lambda _=False, k=key: self.set_theme(k))
            g2.addAction(a)
            m.addAction(a)
        return m

    def _build_more_menu(self) -> QMenu:
        m = QMenu(self)
        m.addAction("打开…\tCtrl+O", self.open_dialog)
        self.recent_menu = m.addMenu("最近打开")
        self.recent_menu.aboutToShow.connect(self._fill_recent_menu)
        m.addSeparator()
        m.addAction("保存\tCtrl+S", self.save)
        m.addAction("另存为…\tCtrl+Shift+S", self.save_as)
        m.addAction("打印…\tCtrl+P", self.print_doc)
        m.addSeparator()
        m.addAction("演示模式\tF5", self.present)
        m.addAction("全屏\tF11", self.toggle_fullscreen)
        m.addSeparator()
        m.addAction("设置…", lambda: self.open_settings())
        m.addAction("关于 Folio", self.about)
        m.addSeparator()
        m.addAction("退出", self.close)
        return m

    def _fill_recent_menu(self):
        self.recent_menu.clear()
        items = self.settings.recent()
        if not items:
            self.recent_menu.addAction("（空）").setEnabled(False)
        for e in items[:15]:
            self.recent_menu.addAction(os.path.basename(e["path"]), lambda p=e["path"]: self.open_path(p))

    def _build_shortcuts(self):
        def sc(key, fn):
            s = QShortcut(QKeySequence(key), self)
            s.activated.connect(fn)
            return s

        sc(QKeySequence.Open, self.open_dialog)
        sc(QKeySequence.Save, self.save)
        sc("Ctrl+Shift+S", self.save_as)
        sc(QKeySequence.Print, self.print_doc)
        sc("Ctrl+W", lambda: self.tabbar.currentIndex() >= 0 and self.stack.currentWidget() is not self.home
           and self.close_tab(self.tabbar.currentIndex()))
        sc(QKeySequence.Undo, lambda: self.cur and self.cur.doc.undo())
        sc("Ctrl+Y", lambda: self.cur and self.cur.doc.redo())
        sc("Ctrl+Shift+Z", lambda: self.cur and self.cur.doc.redo())
        sc(QKeySequence.Find, lambda: self.search())
        sc("Ctrl+=", lambda: self.cur and self.cur.view.zoom_step(1))
        sc("Ctrl++", lambda: self.cur and self.cur.view.zoom_step(1))
        sc("Ctrl+-", lambda: self.cur and self.cur.view.zoom_step(-1))
        sc("Ctrl+0", lambda: self.cur and self.cur.view.set_zoom(1.0))
        sc("Ctrl+1", lambda: self.cur and self.cur.view.set_fit("width"))
        sc("Ctrl+2", lambda: self.cur and self.cur.view.set_fit("page"))
        sc("F4", lambda: self.cur and self._toggle_sidebar())
        sc("F5", self.present)
        sc("F11", self.toggle_fullscreen)
        sc("Ctrl+Tab", lambda: self._cycle_tab(1))
        sc("Ctrl+Shift+Tab", lambda: self._cycle_tab(-1))
        sc("Ctrl+Shift+Space", lambda: self.reader.toggle_pause())
        for name, _, _, key in TOOL_BUTTONS:
            sc(key, lambda n=name: self.cur and self.select_tool(n))

    # ================================================================ 状态
    @property
    def cur(self) -> DocTab | None:
        w = self.stack.currentWidget()
        return w if isinstance(w, DocTab) else None

    def _sync_ui(self):
        tab = self.cur
        on_doc = tab is not None
        self.topbar.setVisible(on_doc)
        self.home_btn.setChecked(not on_doc)
        if not on_doc:
            self.options.hide()
            self.setWindowTitle(APP_DISPLAY_NAME)
            return
        doc, view = tab.doc, tab.view
        self.page_total.setText(f"/ {doc.page_count}")
        self.page_edit.setText(str(view.current_page + 1))
        self.btn_prev.setEnabled(view.current_page > 0)
        self.btn_next.setEnabled(view.current_page < doc.page_count - 1)
        self.btn_undo.setEnabled(doc.can_undo)
        self.btn_redo.setEnabled(doc.can_redo)
        self.btn_undo.setToolTip(f"撤销{doc.undo_label()} (Ctrl+Z)" if doc.can_undo else "撤销 (Ctrl+Z)")
        self.btn_redo.setToolTip(f"重做{doc.redo_label()} (Ctrl+Y)" if doc.can_redo else "重做 (Ctrl+Y)")
        self.btn_save.setEnabled(doc.modified or not doc.is_pdf)
        self.btn_sidebar.setChecked(tab.sidebar.isVisible())
        self.btn_layout.setChecked(view.layout_mode == "double")
        for name in EDIT_TOOLS:
            self.tool_btns[name].setEnabled(doc.editable)
            if not doc.editable:
                self.tool_btns[name].setToolTip("只有 PDF 文件可以批注（可先「另存为」PDF）")
        for a in self.page_actions:
            a.setEnabled(doc.editable)
        self.tool_btns[tab.tool_name].setChecked(True)
        self.options.show_tool(tab.tool_name)
        self._update_zoom_box()
        title = doc.name + (" •" if doc.modified else "")
        self.setWindowTitle(f"{title} — {APP_DISPLAY_NAME}")
        idx = self.tabs_widgets.index(tab)
        self.tabbar.setTabText(idx, ("● " if doc.modified else "") + doc.name)

    def _update_zoom_box(self):
        tab = self.cur
        if not tab:
            return
        v = tab.view
        text = f"{round(v.zoom * 100)}%"
        if v.fit_mode == "width":
            text = "适合宽度"
        elif v.fit_mode == "page":
            text = "适合页面"
        self.zoom_box.lineEdit().setText(text)

    # ================================================================ 标签页
    def _show_tab(self, i: int):
        if 0 <= i < len(self.tabs_widgets):
            self.stack.setCurrentWidget(self.tabs_widgets[i])
            self._sync_ui()
            self.tabs_widgets[i].view.setFocus()

    def _on_tab_changed(self, i: int):
        if i >= 0:
            self._show_tab(i)

    def _on_tab_moved(self, frm: int, to: int):
        t = self.tabs_widgets.pop(frm)
        self.tabs_widgets.insert(to, t)

    def _cycle_tab(self, d: int):
        n = len(self.tabs_widgets)
        if not n:
            return
        if self.cur is None:
            self._show_tab(0 if d > 0 else n - 1)
            self.tabbar.setCurrentIndex(0 if d > 0 else n - 1)
            return
        i = (self.tabs_widgets.index(self.cur) + d) % n
        self.tabbar.setCurrentIndex(i)
        self._show_tab(i)

    def show_home(self):
        self.home.refresh()
        self.stack.setCurrentWidget(self.home)
        self._sync_ui()

    def close_tab(self, i: int) -> bool:
        tab = self.tabs_widgets[i]
        if not self._confirm_discard(tab):
            return False
        if self.reader.doc is tab.doc:
            self.reader.stop()
        tab.cleanup()
        self.tabs_widgets.pop(i)
        self.tabbar.removeTab(i)
        self.stack.removeWidget(tab)
        tab.deleteLater()
        if not self.tabs_widgets:
            self.show_home()
        else:
            self._show_tab(self.tabbar.currentIndex())
        return True

    def _confirm_discard(self, tab: DocTab) -> bool:
        if not tab.doc.modified:
            return True
        self._show_tab(self.tabs_widgets.index(tab))
        self.tabbar.setCurrentIndex(self.tabs_widgets.index(tab))
        box = QMessageBox(self)
        box.setWindowTitle("保存修改")
        box.setText(f"「{tab.doc.name}」有未保存的修改，要保存吗？")
        save = box.addButton("保存", QMessageBox.AcceptRole)
        box.addButton("不保存", QMessageBox.DestructiveRole)
        cancel = box.addButton("取消", QMessageBox.RejectRole)
        box.setDefaultButton(save)
        box.exec()
        if box.clickedButton() is cancel:
            return False
        if box.clickedButton() is save:
            return self.save()
        return True

    # ================================================================ 打开 / 保存
    def open_dialog(self):
        start = os.path.dirname(self.settings.recent()[0]["path"]) if self.settings.recent() else os.path.expanduser("~")
        paths, _ = QFileDialog.getOpenFileNames(self, "打开文件", start, OPEN_FILTER)
        for p in paths:
            self.open_path(p)

    def open_path(self, path: str) -> DocTab | None:
        path = os.path.abspath(path)
        for k, t in enumerate(self.tabs_widgets):
            if t.doc.path and os.path.normcase(t.doc.path) == os.path.normcase(path):
                self.tabbar.setCurrentIndex(k)
                self._show_tab(k)
                return t
        if not os.path.exists(path):
            QMessageBox.warning(self, "打开文件", f"找不到文件：\n{path}")
            self.settings.remove_recent(path)
            self.home.refresh()
            return None
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTS:
            self.open_tool("images", [path])
            return None
        password = None
        while True:
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                doc = PdfDocument(path, password)
                break
            except NeedsPassword:
                QApplication.restoreOverrideCursor()
                password, ok = QInputDialog.getText(self, "需要密码", f"「{os.path.basename(path)}」已加密，请输入密码：",
                                                    QLineEdit.Password)
                if not ok:
                    return None
            except Exception as ex:  # noqa: BLE001
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self, "打开文件", f"无法打开「{os.path.basename(path)}」：\n{ex}")
                return None
            finally:
                QApplication.restoreOverrideCursor()
        return self._add_doc(doc)

    def _add_doc(self, doc: PdfDocument) -> DocTab:
        tab = DocTab(doc, self.settings, self)
        self.tabs_widgets.append(tab)
        self.stack.addWidget(tab)
        idx = self.tabbar.addTab(doc.name)
        self.tabbar.setTabToolTip(idx, doc.path)
        doc.undoChanged.connect(self._sync_if_current)
        doc.modifiedChanged.connect(lambda _: self._sync_if_current())
        doc.structureChanged.connect(self._sync_if_current)
        tab.view.currentPageChanged.connect(lambda _: self._sync_if_current())
        tab.view.zoomChanged.connect(lambda _: tab is self.cur and self._update_zoom_box())
        self.tabbar.setCurrentIndex(idx)
        self.stack.setCurrentWidget(tab)
        if doc.path:
            self.settings.add_recent(doc.path, doc.title(), doc.page_count)
        pos = self.settings.position(doc.path) if (doc.path and self.settings.get("view/restore_position")) else None
        layout = self.settings.get("view/layout")

        def restore():
            if pos:
                tab.view.restore_position(pos)
            else:
                tab.view.set_layout_mode(layout)
                tab.view.set_fit("width")
            self._sync_ui()
        QTimer.singleShot(0, restore)
        self._sync_ui()
        tab.view.setFocus()
        return tab

    def _sync_if_current(self):
        self._sync_ui()

    def save(self) -> bool:
        tab = self.cur
        if not tab:
            return False
        if not tab.doc.is_pdf or not tab.doc.path:
            return self.save_as()
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            tab.doc.save()
        except Exception as ex:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "保存失败", f"无法保存：\n{ex}\n\n可以尝试「另存为」到其他位置。")
            return False
        QApplication.restoreOverrideCursor()
        self.toast("已保存")
        self._sync_ui()
        return True

    def save_as(self) -> bool:
        tab = self.cur
        if not tab:
            return False
        stem = os.path.splitext(tab.doc.name)[0]
        folder = os.path.dirname(tab.doc.path) if tab.doc.path else os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(self, "另存为", os.path.join(folder, stem + ".pdf"), "PDF 文件 (*.pdf)")
        if not path:
            return False
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            tab.doc.save(path)
        except Exception as ex:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "保存失败", f"无法保存：\n{ex}")
            return False
        QApplication.restoreOverrideCursor()
        self.settings.add_recent(path, tab.doc.title(), tab.doc.page_count)
        i = self.tabs_widgets.index(tab)
        self.tabbar.setTabToolTip(i, path)
        self.toast(f"已保存到 {os.path.basename(path)}")
        self._sync_ui()
        return True

    # ================================================================ 视图操作
    def _goto_typed_page(self):
        tab = self.cur
        if not tab:
            return
        try:
            n = int(self.page_edit.text().strip())
            tab.view.go_to(n - 1)
        except ValueError:
            pass
        self._sync_ui()
        tab.view.setFocus()

    def _zoom_chosen(self, idx: int):
        tab = self.cur
        if not tab:
            return
        data = self.zoom_box.itemData(idx)
        if data in ("width", "page"):
            tab.view.set_fit(data)
        elif data:
            tab.view.set_zoom(float(data))
        self._update_zoom_box()
        tab.view.setFocus()

    def _zoom_typed(self):
        tab = self.cur
        if not tab:
            return
        t = self.zoom_box.lineEdit().text().strip().rstrip("%").strip()
        try:
            tab.view.set_zoom(float(t) / 100)
        except ValueError:
            pass
        self._update_zoom_box()
        tab.view.setFocus()

    def _toggle_layout(self):
        tab = self.cur
        if not tab:
            return
        mode = "single" if tab.view.layout_mode == "double" else "double"
        tab.view.set_layout_mode(mode)
        self.settings.set("view/layout", mode)
        self._sync_ui()

    def _toggle_sidebar(self):
        tab = self.cur
        show = not tab.sidebar.isVisible()
        for t in self.tabs_widgets:
            t.toggle_sidebar(show)
        self.settings.set("ui/sidebar", show)
        self._sync_ui()

    def set_tone(self, tone: str):
        self.settings.set("view/tone", tone)
        for t in self.tabs_widgets:
            t.view.set_tone(tone)

    def set_theme(self, mode: str):
        self.settings.set("ui/theme", mode)
        theme.apply(QApplication.instance(), mode)

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def select_tool(self, name: str):
        tab = self.cur
        if not tab:
            return
        if name in EDIT_TOOLS and not tab.doc.editable:
            self.toast("只有 PDF 文件可以批注，可以先「另存为」PDF")
            name = "select"
        tab.set_tool(name)
        self._sync_ui()

    def _on_options_changed(self):
        if self.cur:
            self.cur.refresh_tool_cursor()

    def search(self, text: str | None = None):
        tab = self.cur
        if not tab:
            return
        tab.toggle_sidebar(True)
        tab.sidebar.show_panel("search")
        if text:
            tab.sidebar.search.edit.setText(text)
            tab.sidebar.search.run()
        self._sync_ui()

    def _delete_current_page(self):
        tab = self.cur
        if not tab:
            return
        i = tab.view.current_page
        if tab.doc.page_count <= 1:
            self.toast("不能删除唯一的一页")
            return
        if QMessageBox.question(self, "删除页面", f"确定删除第 {i + 1} 页吗？可以用「撤销」恢复。") == QMessageBox.Yes:
            tab.doc.delete_pages([i])

    def _extract_pages(self):
        tab = self.cur
        if not tab:
            return
        text, ok = QInputDialog.getText(self, "提取页面", f"要提取的页码（共 {tab.doc.page_count} 页），例如 1-3,5：",
                                        text=str(tab.view.current_page + 1))
        if not ok:
            return
        from ..core.util import parse_page_ranges

        try:
            pages = parse_page_ranges(text, tab.doc.page_count)
        except ValueError as ex:
            QMessageBox.warning(self, "提取页面", str(ex))
            return
        tab.sidebar.thumbs._extract(pages)

    # ================================================================ 朗读
    def _on_read_highlight(self, doc, page: int, rects: list):
        for t in self.tabs_widgets:
            if t.doc is doc:
                t.set_read_highlight(page, rects)
                if page >= 0:
                    t.show_read_bar()

    # ================================================================ 其它窗口
    def open_tool(self, key: str, paths: list[str] | None = None):
        from .dialogs.tool_dialogs import open_tool_dialog

        open_tool_dialog(self, key, paths)

    def print_doc(self):
        tab = self.cur
        if not tab:
            return
        from .dialogs.print_dialog import PrintDialog

        PrintDialog(self, tab.doc, tab.view.current_page, self.settings).exec()

    def present(self):
        tab = self.cur
        if not tab:
            return
        from .presentation import PresentationWindow

        self._presenter = PresentationWindow(tab.doc, self.settings, tab.view.current_page)
        self._presenter.closed.connect(lambda page: (tab.view.go_to(page), self._sync_ui()))
        self._presenter.start()

    def open_settings(self, page: str = ""):
        from .dialogs.settings_dialog import SettingsDialog

        d = SettingsDialog(self, self.settings, page)
        if d.exec():
            self.reader.reload_engine()
            theme.apply(QApplication.instance(), self.settings.get("ui/theme"))
            for t in self.tabs_widgets:
                t.read_bar.update_state(self.reader.state)

    def about(self):
        QMessageBox.about(self, "关于 Folio",
                          f"<h3>{APP_DISPLAY_NAME} {__version__}</h3>"
                          "<p>PDF 阅读、批注、朗读与处理工具。</p>"
                          "<p>基于 PySide6 (Qt) 与 PyMuPDF，图标来自 Lucide。</p>")

    def toast(self, text: str, ms: int = 2600):
        self._toast.show_message(text, ms)

    # ================================================================ 拖放 & 关闭
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.home.drop.set_hover(True)

    def dragLeaveEvent(self, e):
        self.home.drop.set_hover(False)

    def dropEvent(self, e):
        self.home.drop.set_hover(False)
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        images = [p for p in paths if os.path.splitext(p)[1].lower() in IMAGE_EXTS]
        docs = [p for p in paths if os.path.splitext(p)[1].lower() in OPENABLE_EXTS]
        others = [p for p in paths if p not in images and p not in docs and os.path.splitext(p)[1].lower() in ALL_EXTS]
        for p in docs:
            self.open_path(p)
        if images:
            self.open_tool("images", images)
        if others:
            self.open_tool("merge", others)

    def closeEvent(self, e):
        for tab in list(self.tabs_widgets):
            if not self._confirm_discard(tab):
                e.ignore()
                return
        self.reader.stop()
        if self.reader.engine:
            self.reader.engine.shutdown()
        for tab in self.tabs_widgets:
            tab.cleanup()
        self.settings.sync()
        super().closeEvent(e)
