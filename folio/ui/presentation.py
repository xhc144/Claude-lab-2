"""演示模式：全屏单页，键盘/点击翻页，激光笔与画笔。"""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..config import Settings
from ..model.document import PdfDocument
from .page_view import PageView
from .tools import EraserTool, InkTool, LaserTool, Tool
from .widgets import IconButton, vline


class PointerTool(Tool):
    """普通指针：单击下一页。"""
    name = "pointer"

    def cursor(self):
        return Qt.ArrowCursor

    def release(self, e, hit):
        if e.button() == Qt.LeftButton:
            self.view.next_page()


class PresentationWindow(QWidget):
    closed = Signal(int)

    def __init__(self, doc: PdfDocument, settings: Settings, page: int):
        super().__init__(None, Qt.Window)
        self.setWindowTitle("演示")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setStyleSheet("background: black;")
        self.doc = doc
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = PageView(doc, self, presentation=True)
        lay.addWidget(self.view)
        self.tools = {"pointer": PointerTool(self.view, settings), "laser": LaserTool(self.view, settings),
                      "pen": InkTool(self.view, settings), "eraser": EraserTool(self.view, settings)}
        self.view.contextMenuAt.connect(lambda *_: self.view.prev_page())
        self.view.currentPageChanged.connect(self._update_label)

        bar = QFrame(self)
        bar.setObjectName("FloatingBar")
        bar.setStyleSheet("#FloatingBar { background: rgba(30,31,34,0.92); border: 1px solid rgba(255,255,255,0.08);"
                          " border-radius: 14px; } QLabel { color: #DDD; }"
                          " QToolButton:hover { background: rgba(255,255,255,0.10); }"
                          " QToolButton:checked { background: rgba(91,140,255,0.35); }")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(8, 6, 8, 6)
        bl.setSpacing(4)
        prev = IconButton("chevron-left", "上一页 (←)", color_key="text3")
        prev.clicked.connect(self.view.prev_page)
        nxt = IconButton("chevron-right", "下一页 (→ / 空格)", color_key="text3")
        nxt.clicked.connect(self.view.next_page)
        self.label = QLabel("")
        self.label.setMinimumWidth(64)
        self.label.setAlignment(Qt.AlignCenter)
        bl.addWidget(prev)
        bl.addWidget(self.label)
        bl.addWidget(nxt)
        bl.addWidget(vline(18))
        self.group = QButtonGroup(self)
        self.btns = {}
        for key, icon, tip in (("pointer", "mouse-pointer-2", "指针：单击翻页 (A)"), ("laser", "laser", "激光笔 (L)"),
                               ("pen", "pen-line", "画笔 (D)"), ("eraser", "eraser", "橡皮擦 (E)")):
            b = IconButton(icon, tip, checkable=True, color_key="text3")
            b.clicked.connect(lambda _=False, k=key: self.set_tool(k))
            self.group.addButton(b)
            self.btns[key] = b
            bl.addWidget(b)
        bl.addWidget(vline(18))
        ex = IconButton("x", "退出演示 (Esc)", color_key="text3")
        ex.clicked.connect(self.close)
        bl.addWidget(ex)
        self.bar = bar
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._maybe_hide_bar)
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._check_mouse)
        self._last_mouse = QPoint()
        self._black = False
        self.set_tool("laser" if doc.page_count else "pointer")
        self.view.go_to(page)
        self._update_label(page)

    def start(self):
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.activateWindow()
        self.view.setFocus()
        self.view.set_fit("page")
        self._show_bar()
        self._poll.start(120)

    def set_tool(self, key: str):
        if key in ("pen", "eraser") and not self.doc.editable:
            key = "laser"
        self.btns[key].setChecked(True)
        self.view.set_tool(self.tools[key])
        self.view.setFocus()

    def _update_label(self, i):
        self.label.setText(f"{i + 1} / {self.doc.page_count}")

    def _place_bar(self):
        self.bar.adjustSize()
        self.bar.move((self.width() - self.bar.width()) // 2, self.height() - self.bar.height() - 28)

    def _show_bar(self):
        self._place_bar()
        self.bar.show()
        self.bar.raise_()
        self._hide_timer.start(2200)

    def _maybe_hide_bar(self):
        if not self.bar.geometry().contains(self.mapFromGlobal(QCursor.pos())):
            self.bar.hide()

    def _check_mouse(self):
        pos = QCursor.pos()
        if pos != self._last_mouse:
            self._last_mouse = pos
            local = self.mapFromGlobal(pos)
            if local.y() > self.height() - 140:
                self._show_bar()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place_bar()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Escape:
            self.close()
            return
        mapping = {Qt.Key_L: "laser", Qt.Key_D: "pen", Qt.Key_E: "eraser", Qt.Key_A: "pointer"}
        if k in mapping:
            self.set_tool(mapping[k])
            return
        if k in (Qt.Key_B, Qt.Key_Period):
            self._black = not self._black
            self.view.setVisible(not self._black)
            return
        super().keyPressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("black"))

    def closeEvent(self, e):
        self._poll.stop()
        self.view.set_tool(None)
        self.closed.emit(self.view.current_page)
        super().closeEvent(e)
