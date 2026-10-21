"""一个文档标签页：侧栏 + 页面视图 + 朗读条，以及右键菜单。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QSplitter, QVBoxLayout, QWidget

from ..config import Settings
from ..model.document import ANNOT_LABELS, PdfDocument
from .bars import HL_COLORS, PEN_COLORS, ReadBar
from .dialogs.note_dialog import NoteDialog
from .page_view import PageView
from .sidebar import Sidebar
from .signature import SignTool
from .tools import TOOL_CLASSES, rgb
from .widgets import IconButton


def color_icon(color: str) -> QIcon:
    pm = QPixmap(14, 14)
    pm.fill(QColor(color))
    return QIcon(pm)


class ViewHost(QWidget):
    """承载 PageView，并让浮动条跟随尺寸变化。"""
    resized = Signal()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.resized.emit()


class DocTab(QWidget):
    def __init__(self, doc: PdfDocument, settings: Settings, main):
        super().__init__()
        self.doc = doc
        self.settings = settings
        self.main = main
        self.view = PageView(doc)
        self.view.set_tone(settings.get("view/tone"))
        self.sidebar = Sidebar(doc, self.view)

        host = ViewHost()
        hl = QVBoxLayout(host)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        self.scan_bar = self._build_scan_bar()
        hl.addWidget(self.scan_bar)
        hl.addWidget(self.view)
        self.host = host
        self.read_bar = ReadBar(main.reader, host)
        self.read_bar.hide()
        self.read_bar.closeRequested.connect(self.close_read_bar)
        self.read_bar.settingsRequested.connect(lambda: main.open_settings("tts"))
        host.resized.connect(self.read_bar.reposition)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(host)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setHandleWidth(1)
        w = int(settings.get("ui/sidebar_width") or 230)
        self.splitter.setSizes([w, 1000])
        self.splitter.splitterMoved.connect(lambda *_: self._remember_sidebar())
        self.sidebar.setVisible(bool(settings.get("ui/sidebar")))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.splitter)

        self.tools = {name: cls(self.view, settings) for name, cls in TOOL_CLASSES.items()}
        self.tools["sign"] = SignTool(self.view, settings)
        self.tool_name = "select"
        self.view.set_tool(self.tools["select"])
        self.view.contextMenuAt.connect(self._context_menu)
        self.view.readRequested.connect(lambda i, k: main.reader.start(doc, i, k))
        QTimer.singleShot(400, self._check_scanned)

    # ---------- 扫描件提示 ----------
    def _build_scan_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("InfoBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 6, 8, 6)
        lay.setSpacing(10)
        icon = IconButton("scan-text", size=16, color_key="accent")
        icon.setEnabled(True)
        lay.addWidget(icon)
        lay.addWidget(QLabel("这是扫描件，页面上没有文字。识别文字后就能搜索、选择和朗读。"), 1)
        go = QPushButton("识别文字")
        go.setProperty("primary", True)
        go.clicked.connect(lambda: self.main.run_ocr(self))
        lay.addWidget(go)
        close = IconButton("x", "不再提示", size=14)
        close.clicked.connect(bar.hide)
        lay.addWidget(close)
        bar.hide()
        return bar

    def _check_scanned(self):
        if not self.doc.closed and self.doc.looks_scanned():
            self.scan_bar.show()

    def refresh_scan_bar(self):
        if self.scan_bar.isVisible() and not self.doc.looks_scanned():
            self.scan_bar.hide()

    # ---------- 工具 ----------
    def set_tool(self, name: str):
        if name not in self.tools:
            return
        self.tool_name = name
        self.view.set_tool(self.tools[name])
        if name == "read":
            self.show_read_bar()
        self.view.setFocus()

    def refresh_tool_cursor(self):
        if self.view.tool:
            self.view.viewport().setCursor(self.view.tool.cursor())

    def show_read_bar(self):
        self.read_bar.show()
        self.read_bar.raise_()
        self.read_bar.reposition()

    def close_read_bar(self):
        self.main.reader.stop()
        self.read_bar.hide()
        if self.tool_name == "read":
            self.main.select_tool("select")

    def _remember_sidebar(self):
        sizes = self.splitter.sizes()
        if sizes and sizes[0] > 40:
            self.settings.set("ui/sidebar_width", sizes[0])

    def toggle_sidebar(self, show: bool | None = None):
        show = (not self.sidebar.isVisible()) if show is None else show
        self.sidebar.setVisible(show)
        if show and self.splitter.sizes()[0] < 60:
            self.splitter.setSizes([int(self.settings.get("ui/sidebar_width") or 230), 1000])

    # ---------- 右键菜单 ----------
    def _context_menu(self, gpos, hit):
        m = QMenu(self)
        view, doc = self.view, self.doc
        if view.selection:
            m.addAction("复制", view.copy_selection)
            if doc.editable:
                for kind, text in (("highlight", "高亮"), ("underline", "下划线"), ("strikeout", "删除线")):
                    m.addAction(text, lambda k=kind: self.markup_selection(k))
            m.addAction("朗读选中文字", lambda: (self.show_read_bar(), self.main.reader.read_text(view.selected_text())))
            m.addAction("搜索选中文字", lambda: self.main.search(view.selected_text()))
            m.addSeparator()
        annot = None
        if hit and doc.editable:
            i, x, y = hit
            ux, uy = view.unrot(i, x, y)
            xs = doc.annots_at(i, ux, uy, 4 / view.scale + 2)
            if xs:
                annot = (i, xs[-1])
        if annot:
            i, xref = annot
            info = doc.annot_info(i, xref)
            m.addSection(ANNOT_LABELS.get(info["type"], "批注"))
            if info["type"] in ("FreeText", "Text"):
                m.addAction("编辑内容…", lambda: self._edit_annot(i, xref, info["content"]))
            cm = m.addMenu("颜色")
            palette = HL_COLORS if info["type"] in ("Highlight",) else PEN_COLORS
            for c in palette:
                cm.addAction(color_icon(c), c, lambda c=c: doc.set_annot_color(i, xref, rgb(c)))
            m.addAction("删除批注", lambda: doc.delete_annots(i, [xref]))
            m.addSeparator()
        if hit:
            i, x, y = hit
            ux, uy = view.unrot(i, x, y)
            k = doc.text(i).hit(ux, uy)
            if k is not None:
                m.addAction("从这里开始朗读", lambda: (self.show_read_bar(), self.main.reader.start(doc, i, k)))
            m.addAction("选择本页文字", lambda: view.set_selection((i, 0, i, len(doc.text(i)))))
            if doc.editable:
                rm = m.addMenu("旋转本页")
                rm.addAction("向左旋转 90°", lambda: doc.rotate_pages([i], -90))
                rm.addAction("向右旋转 90°", lambda: doc.rotate_pages([i], 90))
        if not m.isEmpty():
            m.exec(gpos)

    def markup_selection(self, kind: str):
        sel = self.view.selection
        if not sel or not self.doc.editable:
            return
        pa, ia, pb, ib = sel
        color = rgb(self.settings.get("highlight/color") if kind == "highlight" else "#E5484D")
        self.doc.begin_macro("标注")
        for i in range(pa, pb + 1):
            pt = self.doc.text(i)
            a = ia if i == pa else 0
            b = ib if i == pb else len(pt)
            rects = pt.rects_for_range(a, b)
            if rects:
                self.doc.add_markup(i, kind, rects, color)
        self.doc.end_macro()
        self.view.set_selection(None)

    def _edit_annot(self, i, xref, content):
        text = NoteDialog.ask(self.window(), "编辑内容", content)
        if text is not None and text != content:
            self.doc.set_annot_text(i, xref, text)

    # ---------- 朗读高亮 ----------
    def set_read_highlight(self, page: int, rects: list):
        if page < 0:
            self.view.read_highlight = None
        else:
            self.view.read_highlight = (page, rects)
            if rects:
                x0 = min(r[0] for r in rects)
                y0 = min(r[1] for r in rects)
                x1 = max(r[2] for r in rects)
                y1 = max(r[3] for r in rects)
                if page not in self.view.visible_pages():
                    self.view.go_to(page)
                self.view.ensure_visible(page, (x0, y0, x1, y1), margin=120)
        self.view.viewport().update()

    def save_position(self):
        if self.doc.path and self.doc.page_count:
            self.settings.set_position(self.doc.path, self.view.position_state())

    def cleanup(self):
        self.save_position()
        self.view.set_tool(None)
        self.view._render_timer.stop()
        self.doc.close()

