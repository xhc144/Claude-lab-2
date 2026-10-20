"""左侧栏：缩略图（含页面管理）、目录、批注列表、全文搜索。"""
from __future__ import annotations

import os

import pymupdf
from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox, QStackedWidget, QStyle, QStyledItemDelegate,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ..core.util import format_page_ranges
from ..model.document import PdfDocument
from ..theme import theme
from .page_view import PageView, pix_to_qimage
from .widgets import IconButton, Segmented

THUMB_ROLE = Qt.UserRole + 1


# ====================================================================== 缩略图
class ThumbDelegate(QStyledItemDelegate):
    def __init__(self, panel: "ThumbPanel"):
        super().__init__(panel)
        self.panel = panel

    def sizeHint(self, option, index):
        return self.panel.item_size(index.data(Qt.UserRole))

    def paint(self, p: QPainter, option, index):
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = option.rect
        page = index.data(Qt.UserRole)
        selected = bool(option.state & QStyle.State_Selected)
        hover = bool(option.state & QStyle.State_MouseOver)
        current = page == self.panel.view.current_page
        tw, th = self.panel.thumb_dims(page)
        x = r.x() + (r.width() - tw) / 2
        y = r.y() + 8
        box = QRectF(x, y, tw, th)
        if selected or hover:
            bg = theme.qc("accent_soft") if selected else theme.qc("hover")
            p.setPen(Qt.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(QRectF(r).adjusted(6, 2, -6, -2), 8, 8)
        p.setPen(QPen(QColor(0, 0, 0, 30), 1))
        p.setBrush(QColor("white"))
        p.drawRect(box)
        img = self.panel.thumb(page)
        if img is not None:
            p.drawImage(box, img)
        if current:
            p.setPen(QPen(theme.qc("accent"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(box.adjusted(-3, -3, 3, 3), 3, 3)
        p.setPen(theme.qc("accent") if current else theme.qc("text2"))
        f = p.font()
        f.setPixelSize(11)
        p.setFont(f)
        p.drawText(QRectF(r.x(), y + th + 4, r.width(), 16), Qt.AlignHCenter | Qt.AlignTop, str(page + 1))
        p.restore()


class ThumbPanel(QListWidget):
    reordered = Signal(list)

    def __init__(self, doc: PdfDocument, view: PageView, parent=None):
        super().__init__(parent)
        self.doc, self.view = doc, view
        self._cache: dict[int, tuple[tuple, QImage]] = {}
        self.setItemDelegate(ThumbDelegate(self))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setUniformItemSizes(False)
        self.setMouseTracking(True)
        self.setDragDropMode(QAbstractItemView.InternalMove if doc.editable else QAbstractItemView.NoDragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.itemClicked.connect(lambda it: self.view.go_to(it.data(Qt.UserRole)))
        self.model().rowsMoved.connect(self._on_rows_moved)
        self.verticalScrollBar().valueChanged.connect(lambda _: self._timer.start(30))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._render_some)
        doc.pagesChanged.connect(self._on_pages_changed)
        doc.structureChanged.connect(self.rebuild)
        view.currentPageChanged.connect(self._on_current)
        QShortcut(QKeySequence.Delete, self, self.delete_selected, context=Qt.WidgetShortcut)
        self.rebuild()

    def thumb_width(self) -> int:
        return max(80, min(170, self.viewport().width() - 40))

    def thumb_dims(self, page: int) -> tuple[int, int]:
        w, h = self.doc.page_size(page)
        tw = self.thumb_width()
        th = int(tw * h / w)
        if th > tw * 1.6:
            th = int(tw * 1.6)
            tw = int(th * w / h)
        return tw, th

    def item_size(self, page: int) -> QSize:
        _, th = self.thumb_dims(page)
        return QSize(self.viewport().width() - 4, th + 34)

    def rebuild(self):
        self._cache.clear()
        self.clear()
        for i in range(self.doc.page_count):
            it = QListWidgetItem()
            it.setData(Qt.UserRole, i)
            it.setFlags(it.flags() | Qt.ItemIsDragEnabled)
            self.addItem(it)
        self._on_current(self.view.current_page)
        self._timer.start(0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.doItemsLayout()
        self._timer.start(60)

    def thumb(self, page: int) -> QImage | None:
        hit = self._cache.get(page)
        if hit is None:
            return None
        return hit[1]

    def _render_some(self):
        if self.doc.closed:
            return
        rect = self.viewport().rect().adjusted(0, -300, 0, 300)
        todo = []
        for row in range(self.count()):
            it = self.item(row)
            if self.visualItemRect(it).intersects(rect):
                page = it.data(Qt.UserRole)
                key = (self.doc.revision(page), self.doc.epoch, self.thumb_width())
                hit = self._cache.get(page)
                if hit is None or hit[0] != key:
                    todo.append((page, key))
        for page, key in todo[:4]:
            tw, _ = self.thumb_dims(page)
            scale = tw * 2 / self.doc.page_size(page)[0]
            try:
                img = pix_to_qimage(self.doc.render(page, scale), "normal")
            except Exception:
                continue
            self._cache[page] = (key, img)
        if todo:
            self.viewport().update()
        if len(todo) > 4:
            self._timer.start(10)

    def _on_pages_changed(self, pages):
        self._timer.start(200)

    def _on_current(self, i):
        if 0 <= i < self.count():
            it = self.item(i)
            if not it.isSelected() or len(self.selectedItems()) <= 1:
                self.blockSignals(True)
                self.setCurrentItem(it)
                self.blockSignals(False)
            self.scrollToItem(it, QAbstractItemView.EnsureVisible)
        self.viewport().update()

    def selected_pages(self) -> list[int]:
        return sorted(it.data(Qt.UserRole) for it in self.selectedItems())

    def _on_rows_moved(self, *args):
        order = [self.item(r).data(Qt.UserRole) for r in range(self.count())]
        if order != list(range(len(order))):
            QTimer.singleShot(0, lambda: self.doc.reorder(order))

    # ---------- 右键菜单 ----------
    def _menu(self, pos):
        it = self.itemAt(pos)
        if it is None:
            return
        if not it.isSelected():
            self.setCurrentItem(it)
        pages = self.selected_pages()
        label = f"第 {format_page_ranges(pages)} 页"
        m = QMenu(self)
        m.addSection(label)
        ed = self.doc.editable
        m.addAction("向左旋转", lambda: self.doc.rotate_pages(pages, -90)).setEnabled(ed)
        m.addAction("向右旋转", lambda: self.doc.rotate_pages(pages, 90)).setEnabled(ed)
        m.addSeparator()
        m.addAction("在后面插入空白页", lambda: self.doc.insert_blank(pages[-1])).setEnabled(ed)
        m.addAction("在后面插入文件…", lambda: self._insert_file(pages[-1] + 1)).setEnabled(ed)
        m.addAction("提取为新 PDF…", lambda: self._extract(pages))
        m.addSeparator()
        m.addAction("删除页面", self.delete_selected).setEnabled(ed and len(pages) < self.doc.page_count)
        m.exec(self.viewport().mapToGlobal(pos))

    def delete_selected(self):
        pages = self.selected_pages()
        if not pages or not self.doc.editable:
            return
        if len(pages) >= self.doc.page_count:
            QMessageBox.information(self, "删除页面", "不能删除全部页面。")
            return
        if QMessageBox.question(self, "删除页面", f"确定删除第 {format_page_ranges(pages)} 页吗？\n可以用「撤销」恢复。") \
                == QMessageBox.Yes:
            self.doc.delete_pages(pages)

    def _insert_file(self, at: int):
        path, _ = QFileDialog.getOpenFileName(self, "插入文件", "",
                                              "PDF 或图片 (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff);;所有文件 (*)")
        if path:
            try:
                self.doc.insert_file(path, at)
            except Exception as ex:  # noqa: BLE001
                QMessageBox.warning(self, "插入文件", f"插入失败：{ex}")

    def _extract(self, pages: list[int]):
        stem = os.path.splitext(self.doc.name)[0]
        default = os.path.join(os.path.dirname(self.doc.path), f"{stem}_p{format_page_ranges(pages)}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "提取页面", default, "PDF 文件 (*.pdf)")
        if path:
            self.doc.extract_pages(pages, path)
            self.window().toast(f"已提取 {len(pages)} 页到 {os.path.basename(path)}")


# ====================================================================== 目录
class OutlinePanel(QWidget):
    def __init__(self, doc: PdfDocument, view: PageView, parent=None):
        super().__init__(parent)
        self.doc, self.view = doc, view
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.itemClicked.connect(self._go)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.empty = QLabel("这份文档没有目录")
        self.empty.setObjectName("Faint")
        self.empty.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.tree)
        lay.addWidget(self.empty)
        doc.structureChanged.connect(self.rebuild)
        self.rebuild()

    def rebuild(self):
        self.tree.clear()
        try:
            toc = self.doc.fz.get_toc(simple=False)
        except Exception:
            toc = []
        stack: list[tuple[int, QTreeWidgetItem | None]] = [(0, None)]
        for entry in toc:
            lvl, title, page = entry[0], entry[1], entry[2]
            dest = entry[3] if len(entry) > 3 else {}
            it = QTreeWidgetItem([title.strip() or "（无标题）"])
            it.setToolTip(0, f"{title}  ·  第 {page} 页")
            to = dest.get("to") if isinstance(dest, dict) else None
            it.setData(0, Qt.UserRole, (page - 1, to.y if to is not None else None, to.x if to is not None else None))
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            parent = stack[-1][1] if stack else None
            (parent.addChild(it) if parent else self.tree.addTopLevelItem(it))
            stack.append((lvl, it))
        self.tree.expandToDepth(0)
        self.tree.setVisible(bool(toc))
        self.empty.setVisible(not toc)

    def _go(self, it, col=0):
        page, y, x = it.data(0, Qt.UserRole)
        if page is None or page < 0:
            return
        yd = None
        if y is not None:
            _, yd = self.view.disp(page, x or 0, y)
        self.view.go_to(page, y_pt=yd)


# ====================================================================== 批注列表
class AnnotPanel(QWidget):
    def __init__(self, doc: PdfDocument, view: PageView, parent=None):
        super().__init__(parent)
        self.doc, self.view = doc, view
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setWordWrap(True)
        self.list.itemClicked.connect(self._go)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        self.empty = QLabel("还没有批注\n用高亮、画笔、文本框等工具添加")
        self.empty.setObjectName("Faint")
        self.empty.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.list)
        lay.addWidget(self.empty)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.refresh)
        doc.pagesChanged.connect(lambda _: self._timer.start(300))
        doc.structureChanged.connect(lambda: self._timer.start(300))

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()

    def refresh(self):
        if not self.isVisible():
            return
        self.list.clear()
        items = self.doc.list_annots()
        for a in items:
            it = QListWidgetItem()
            text = f"{a['label']}  ·  第 {a['page'] + 1} 页"
            if a["content"]:
                text += f"\n{a['content']}"
            it.setText(text)
            c = QColor.fromRgbF(*a["color"][:3])
            img = QImage(12, 12, QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent)
            p = QPainter(img)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(1, 1, 10, 10)
            p.end()
            it.setIcon(QIcon(QPixmap.fromImage(img)))
            it.setData(Qt.UserRole, (a["page"], a["xref"], a["rect"]))
            self.list.addItem(it)
        self.list.setVisible(bool(items))
        self.empty.setVisible(not items)

    def _go(self, it):
        page, xref, rect = it.data(Qt.UserRole)
        self.view.go_to(page)
        self.view.ensure_visible(page, rect)
        self.view.flash_rect(page, rect)

    def _menu(self, pos):
        it = self.list.itemAt(pos)
        if not it or not self.doc.editable:
            return
        page, xref, _ = it.data(Qt.UserRole)
        m = QMenu(self)
        m.addAction("删除批注", lambda: self.doc.delete_annots(page, [xref]))
        m.exec(self.list.viewport().mapToGlobal(pos))


# ====================================================================== 搜索
class SearchPanel(QWidget):
    def __init__(self, doc: PdfDocument, view: PageView, parent=None):
        super().__init__(parent)
        self.doc, self.view = doc, view
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 0)
        lay.setSpacing(8)
        row = QHBoxLayout()
        row.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setObjectName("Search")
        self.edit.setPlaceholderText("搜索文档内容")
        self.edit.setClearButtonEnabled(True)
        self.edit.returnPressed.connect(self._enter)
        self.edit.textChanged.connect(lambda _: self._debounce.start(350))
        row.addWidget(self.edit, 1)
        self.prev_btn = IconButton("chevron-up", "上一个 (Shift+Enter)", size=16)
        self.next_btn = IconButton("chevron-down", "下一个 (Enter)", size=16)
        self.prev_btn.clicked.connect(lambda: self.step(-1))
        self.next_btn.clicked.connect(lambda: self.step(1))
        row.addWidget(self.prev_btn)
        row.addWidget(self.next_btn)
        lay.addLayout(row)
        self.info = QLabel("")
        self.info.setObjectName("Faint")
        lay.addWidget(self.info)
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.itemClicked.connect(lambda it: self.select(self.list.row(it)))
        lay.addWidget(self.list, 1)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self.run)
        self._step = QTimer(self)
        self._step.timeout.connect(self._search_chunk)
        self._results: list[tuple[int, int]] = []
        self._term = ""
        self._next_page = 0
        self._cur = -1
        doc.structureChanged.connect(lambda: self.run(force=True))
        QShortcut(QKeySequence("Shift+Return"), self.edit, lambda: self.step(-1), context=Qt.WidgetShortcut)

    def focus(self):
        sel = self.view.selected_text()
        if sel and len(sel) < 60 and "\n" not in sel:
            self.edit.setText(sel)
        self.edit.setFocus()
        self.edit.selectAll()

    def _enter(self):
        if self.edit.text().strip() != self._term:
            self.run()
        else:
            self.step(1)

    def run(self, force: bool = False):
        term = self.edit.text().strip()
        if term == self._term and not force:
            return
        self._term = term
        self._results = []
        self._cur = -1
        self.list.clear()
        self.view.search_hits = {}
        self.view.search_current = None
        self.view.viewport().update()
        if not term:
            self.info.setText("")
            self._step.stop()
            return
        self._next_page = 0
        self.info.setText("正在搜索…")
        self._step.start(0)

    def _search_chunk(self):
        n = self.doc.page_count
        end = min(n, self._next_page + 8)
        for i in range(self._next_page, end):
            rects = self.doc.search(i, self._term)
            if not rects:
                continue
            self.view.search_hits[i] = [tuple(r) for r in rects]
            pg = self.doc.page(i)
            pw = pg.rect.width + pg.rect.height
            for k, r in enumerate(rects):
                self._results.append((i, k))
                try:
                    line = pg.get_textbox(pymupdf.Rect(-pw, r.y0 + 1, pw * 2, r.y1 - 1))
                except Exception:
                    line = ""
                line = " ".join(line.split())
                pos = line.lower().find(self._term.lower())
                if pos > 24:
                    line = "…" + line[pos - 20:]
                if len(line) > 70:
                    line = line[:70] + "…"
                it = QListWidgetItem(f"第 {i + 1} 页\n{line}")
                self.list.addItem(it)
            del pg
        self._next_page = end
        self.view.viewport().update()
        if end >= n:
            self._step.stop()
            total = len(self._results)
            self.info.setText(f"共找到 {total} 处" if total else "没有找到")
            if total and self._cur < 0:
                self.select(0)
        else:
            self.info.setText(f"正在搜索… 第 {end}/{n} 页，已找到 {len(self._results)} 处")
            if self._results and self._cur < 0:
                self.select(0)

    def step(self, d: int):
        if not self._results:
            if self.edit.text().strip():
                self.run(force=True)
            return
        self.select((self._cur + d) % len(self._results))

    def select(self, idx: int):
        if not (0 <= idx < len(self._results)):
            return
        self._cur = idx
        i, k = self._results[idx]
        self.view.search_current = (i, k)
        rect = self.view.search_hits[i][k]
        self.view.go_to(i) if i not in self.view.visible_pages() else None
        self.view.ensure_visible(i, rect)
        self.view.viewport().update()
        self.list.blockSignals(True)
        self.list.setCurrentRow(idx)
        self.list.blockSignals(False)

    def clear(self):
        self.edit.clear()
        self.run(force=True)


# ====================================================================== 外壳
class Sidebar(QFrame):
    PANELS = [("thumbs", "缩略图", "layout-grid"), ("outline", "目录", "list-tree"),
              ("annots", "批注", "message-square"), ("search", "搜索", "search")]

    def __init__(self, doc: PdfDocument, view: PageView, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        head = QFrame()
        head.setObjectName("SidebarHeader")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(10, 10, 10, 8)
        self.seg = Segmented([(k, t) for k, t, _ in self.PANELS], "thumbs", icons={k: ic for k, _, ic in self.PANELS})
        hl.addWidget(self.seg)
        hl.addStretch(1)
        self.title = QLabel("缩略图")
        self.title.setObjectName("SectionTitle")
        hl.addWidget(self.title)
        lay.addWidget(head)
        self.stack = QStackedWidget()
        self.thumbs = ThumbPanel(doc, view)
        self.outline = OutlinePanel(doc, view)
        self.annots = AnnotPanel(doc, view)
        self.search = SearchPanel(doc, view)
        for w in (self.thumbs, self.outline, self.annots, self.search):
            self.stack.addWidget(w)
        lay.addWidget(self.stack, 1)
        self.seg.changed.connect(self.show_panel)

    def show_panel(self, key: str):
        idx = [k for k, _, _ in self.PANELS].index(key)
        self.seg.set_value(key)
        self.stack.setCurrentIndex(idx)
        self.title.setText(self.PANELS[idx][1])
        if key == "search":
            self.search.focus()

    def current_panel(self) -> str:
        return self.PANELS[self.stack.currentIndex()][0]

