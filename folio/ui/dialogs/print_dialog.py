"""打印：选择打印机、页码、份数、双面、每张纸几页、是否带批注、黑白，以及预览。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPageLayout, QPageSize, QPainter, QPen, QTransform
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrinterInfo
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QProgressDialog, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from ...config import Settings
from ...core.util import parse_page_ranges
from ...model.document import PdfDocument
from ...theme import theme
from ..page_view import pix_to_qimage
from ..widgets import IconButton, Segmented
from .base import section

PDF_TARGET = "__pdf__"
MAX_DPI = 300

PAPERS = [("A4", QPageSize.A4), ("A3", QPageSize.A3), ("A5", QPageSize.A5), ("B5", QPageSize.B5),
          ("Letter", QPageSize.Letter), ("Legal", QPageSize.Legal)]


@dataclass
class PrintOptions:
    pages: list[int] = field(default_factory=list)
    nup: int = 1
    scale: str = "fit"          # fit / actual
    annots: bool = True
    gray: bool = False
    orientation: str = "auto"   # auto / portrait / landscape


def grid_for(nup: int, landscape: bool) -> tuple[int, int]:
    return {1: (1, 1), 2: (2, 1) if landscape else (1, 2), 4: (2, 2),
            6: (3, 2) if landscape else (2, 3), 9: (3, 3)}.get(nup, (1, 1))


def sheet_landscape(doc: PdfDocument, opts: PrintOptions) -> bool:
    if opts.orientation != "auto":
        return opts.orientation == "landscape"
    if opts.nup in (2, 6):
        return True
    if opts.nup == 1 and opts.pages:
        w, h = doc.page_size(opts.pages[0])
        return w > h
    return False


def sheets(opts: PrintOptions) -> list[list[int]]:
    n = max(1, opts.nup)
    return [opts.pages[i:i + n] for i in range(0, len(opts.pages), n)]


def paint_sheet(p: QPainter, area: QRectF, doc: PdfDocument, pages: list[int], opts: PrintOptions,
                dpi: float, landscape: bool):
    """在 area（设备像素）里按网格画出若干页。dpi 是设备分辨率。"""
    cols, rows = grid_for(opts.nup, landscape)
    gap = dpi * 0.12 if opts.nup > 1 else 0  # 约 3mm
    cw = (area.width() - gap * (cols - 1)) / cols
    ch = (area.height() - gap * (rows - 1)) / rows
    for k, i in enumerate(pages):
        r, c = divmod(k, cols)
        cell = QRectF(area.x() + c * (cw + gap), area.y() + r * (ch + gap), cw, ch)
        pw, ph = doc.page_size(i)
        rotate = (opts.orientation == "auto" and opts.nup == 1 and (pw > ph) != (cell.width() > cell.height())
                  and not landscape)
        if rotate:
            pw, ph = ph, pw
        pw_px, ph_px = pw * dpi / 72, ph * dpi / 72
        fit = min(cell.width() / pw_px, cell.height() / ph_px)
        s = fit if (opts.scale == "fit" or opts.nup > 1) else min(1.0, fit)
        tw, th = pw_px * s, ph_px * s
        target = QRectF(cell.x() + (cell.width() - tw) / 2, cell.y() + (cell.height() - th) / 2, tw, th)
        render_dpi = min(MAX_DPI, dpi * s)
        pix = doc.render(i, render_dpi / 72, annots=opts.annots, gray=opts.gray)
        img = pix_to_qimage(pix, "normal")
        if rotate:
            img = img.transformed(QTransform().rotate(90))
        p.drawImage(target, img)
        if opts.nup > 1:
            p.setPen(QPen(QColor(200, 200, 200), max(1, dpi / 150)))
            p.setBrush(Qt.NoBrush)
            p.drawRect(target)


class SheetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 340)
        self.image: QImage | None = None

    def set_image(self, img: QImage | None):
        self.image = img
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), theme.qc("canvas"))
        if self.image is None:
            return
        avail = QRectF(self.rect()).adjusted(18, 18, -18, -18)
        iw, ih = self.image.width(), self.image.height()
        s = min(avail.width() / iw, avail.height() / ih)
        w, h = iw * s, ih * s
        r = QRectF(avail.x() + (avail.width() - w) / 2, avail.y() + (avail.height() - h) / 2, w, h)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawRect(r.translated(0, 3))
        p.drawImage(r, self.image)


class PrintDialog(QDialog):
    def __init__(self, parent, doc: PdfDocument, current_page: int, settings: Settings):
        super().__init__(parent)
        self.doc = doc
        self.current = current_page
        self.settings = settings
        self.setWindowTitle("打印")
        self.resize(860, 600)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 左：选项 ----
        left = QFrame()
        left.setObjectName("Surface")
        left.setFixedWidth(400)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(22, 20, 22, 18)
        ll.setSpacing(10)
        title = QLabel("打印")
        title.setObjectName("H2")
        ll.addWidget(title)

        ll.addWidget(section("打印机"))
        self.printer = QComboBox()
        default = QPrinterInfo.defaultPrinterName()
        names = QPrinterInfo.availablePrinterNames()
        for n in names:
            self.printer.addItem(n, n)
        self.printer.addItem("导出为 PDF 文件（打印效果）", PDF_TARGET)
        if default in names:
            self.printer.setCurrentIndex(names.index(default))
        elif not names:
            self.printer.setCurrentIndex(self.printer.count() - 1)
        prow = QHBoxLayout()
        prow.addWidget(self.printer, 1)
        self.props_btn = IconButton("settings", "打印机属性（纸盒、纸张类型等）")
        self.props_btn.clicked.connect(self._printer_props)
        prow.addWidget(self.props_btn)
        ll.addLayout(prow)
        if not names:
            hint = QLabel("没有检测到打印机。请先在系统设置里添加打印机，或导出为 PDF。")
            hint.setObjectName("Faint")
            hint.setWordWrap(True)
            ll.addWidget(hint)

        ll.addWidget(section("页面"))
        self.range_seg = Segmented([("all", "全部"), ("current", "当前页"), ("custom", "自定义")], "all")
        self.range_seg.changed.connect(self._range_mode)
        ll.addWidget(self.range_seg)
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText(f"例如 1-3, 5（共 {doc.page_count} 页）")
        self.range_edit.textChanged.connect(self._refresh)
        self.range_edit.hide()
        ll.addWidget(self.range_edit)

        grid = QVBoxLayout()
        grid.setSpacing(8)

        def row(label_text, w):
            r = QHBoxLayout()
            lb = QLabel(label_text)
            lb.setFixedWidth(84)
            r.addWidget(lb)
            r.addWidget(w)
            r.addStretch(1)
            grid.addLayout(r)

        self.copies = QSpinBox()
        self.copies.setRange(1, 999)
        self.copies.setFixedWidth(80)
        row("份数", self.copies)
        self.duplex = QComboBox()
        self.duplex.addItem("单面", QPrinter.DuplexNone)
        self.duplex.addItem("双面（长边翻页）", QPrinter.DuplexLongSide)
        self.duplex.addItem("双面（短边翻页）", QPrinter.DuplexShortSide)
        row("双面", self.duplex)
        self.paper = QComboBox()
        for name, pid in PAPERS:
            self.paper.addItem(name, pid)
        row("纸张", self.paper)
        self.orient = Segmented([("auto", "自动"), ("portrait", "纵向"), ("landscape", "横向")], "auto")
        self.orient.changed.connect(lambda _: self._refresh())
        row("方向", self.orient)
        self.nup = QComboBox()
        for n in (1, 2, 4, 6, 9):
            self.nup.addItem(f"{n} 页" if n > 1 else "1 页（正常）", n)
        self.nup.setCurrentIndex([1, 2, 4, 6, 9].index(int(settings.get("print/nup") or 1)))
        self.nup.currentIndexChanged.connect(self._refresh)
        row("每张纸", self.nup)
        self.scale = Segmented([("fit", "适合纸张"), ("actual", "实际大小")], settings.get("print/scale") or "fit")
        self.scale.changed.connect(lambda _: self._refresh())
        row("缩放", self.scale)
        ll.addLayout(grid)
        self.annots = QCheckBox("打印批注（手写、高亮等）")
        self.annots.setChecked(bool(settings.get("print/annots")))
        self.annots.toggled.connect(self._refresh)
        self.gray = QCheckBox("黑白打印")
        self.gray.setChecked(bool(settings.get("print/gray")))
        self.gray.toggled.connect(self._refresh)
        ll.addWidget(self.annots)
        ll.addWidget(self.gray)
        ll.addStretch(1)
        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        self.go = QPushButton("打印")
        self.go.setProperty("primary", True)
        self.go.setDefault(True)
        self.go.clicked.connect(self._print)
        btns.addWidget(cancel)
        btns.addWidget(self.go)
        ll.addLayout(btns)
        root.addWidget(left)

        # ---- 右：预览 ----
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.preview = SheetPreview()
        right.addWidget(self.preview, 1)
        nav = QHBoxLayout()
        nav.setContentsMargins(12, 8, 12, 12)
        nav.addStretch(1)
        self.prev_btn = IconButton("chevron-left", "上一张")
        self.next_btn = IconButton("chevron-right", "下一张")
        self.sheet_label = QLabel("")
        self.sheet_label.setObjectName("Muted")
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.sheet_label)
        nav.addWidget(self.next_btn)
        nav.addStretch(1)
        right.addLayout(nav)
        rw = QWidget()
        rw.setLayout(right)
        root.addWidget(rw, 1)
        self.prev_btn.clicked.connect(lambda: self._show_sheet(self._sheet - 1))
        self.next_btn.clicked.connect(lambda: self._show_sheet(self._sheet + 1))
        self.printer.currentIndexChanged.connect(self._printer_changed)
        self._sheet = 0
        self._printer_obj: QPrinter | None = None
        self._printer_changed()
        self._refresh()

    # ---------- 选项 ----------
    def _range_mode(self, k):
        self.range_edit.setVisible(k == "custom")
        if k == "custom":
            self.range_edit.setFocus()
        self._refresh()

    def options(self) -> PrintOptions | None:
        mode = self.range_seg.value()
        if mode == "all":
            pages = list(range(self.doc.page_count))
        elif mode == "current":
            pages = [self.current]
        else:
            try:
                pages = parse_page_ranges(self.range_edit.text(), self.doc.page_count)
            except ValueError:
                return None
        return PrintOptions(pages=pages, nup=self.nup.currentData(), scale=self.scale.value(),
                            annots=self.annots.isChecked(), gray=self.gray.isChecked(), orientation=self.orient.value())

    def _printer_changed(self):
        target = self.printer.currentData()
        is_pdf = target == PDF_TARGET
        self.props_btn.setEnabled(not is_pdf)
        self.copies.setEnabled(not is_pdf)
        self.duplex.setEnabled(not is_pdf)
        self.go.setText("导出" if is_pdf else "打印")
        if not is_pdf:
            info = QPrinterInfo.printerInfo(target)
            ps = info.defaultPageSize()
            for k in range(self.paper.count()):
                if self.paper.itemData(k) == ps.id():
                    self.paper.setCurrentIndex(k)
                    break
            self._printer_obj = None

    def _printer_props(self):
        pr = self._make_printer()
        dlg = QPrintDialog(pr, self)
        dlg.setOption(QPrintDialog.PrintToFile, False)
        dlg.setOptions(dlg.options() & ~QPrintDialog.PrintPageRange)
        if dlg.exec():
            self._printer_obj = pr
            self.copies.setValue(pr.copyCount())
            for k in range(self.duplex.count()):
                if self.duplex.itemData(k) == pr.duplex():
                    self.duplex.setCurrentIndex(k)

    def _make_printer(self) -> QPrinter:
        pr = self._printer_obj or QPrinter(QPrinter.HighResolution)
        target = self.printer.currentData()
        if target == PDF_TARGET:
            pr.setOutputFormat(QPrinter.PdfFormat)
        else:
            pr.setOutputFormat(QPrinter.NativeFormat)
            pr.setPrinterName(target)
            pr.setCopyCount(self.copies.value())
            pr.setDuplex(self.duplex.currentData())
        opts = self.options() or PrintOptions(pages=[self.current])
        land = sheet_landscape(self.doc, opts)
        pr.setPageLayout(QPageLayout(QPageSize(self.paper.currentData()),
                                     QPageLayout.Landscape if land else QPageLayout.Portrait,
                                     QMarginsF(6, 6, 6, 6), QPageLayout.Millimeter))
        pr.setColorMode(QPrinter.GrayScale if self.gray.isChecked() else QPrinter.Color)
        pr.setDocName(self.doc.name)
        return pr

    # ---------- 预览 ----------
    def _refresh(self):
        opts = self.options()
        if opts is None or not opts.pages:
            self.preview.set_image(None)
            self.sheet_label.setText("页码无效")
            self.go.setEnabled(False)
            return
        self.go.setEnabled(True)
        self._show_sheet(min(self._sheet, len(sheets(opts)) - 1))

    def _show_sheet(self, k: int):
        opts = self.options()
        if not opts:
            return
        all_sheets = sheets(opts)
        k = max(0, min(k, len(all_sheets) - 1))
        self._sheet = k
        land = sheet_landscape(self.doc, opts)
        ps = QPageSize(self.paper.currentData()).sizePoints()
        w, h = ps.width(), ps.height()
        if land:
            w, h = h, w
        dpi = 72 * 1.6
        img = QImage(int(w * 1.6), int(h * 1.6), QImage.Format_RGB32)
        img.fill(QColor("white"))
        p = QPainter(img)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        margin = 6 / 25.4 * dpi
        paint_sheet(p, QRectF(margin, margin, img.width() - 2 * margin, img.height() - 2 * margin),
                    self.doc, all_sheets[k], opts, dpi, land)
        p.end()
        self.preview.set_image(img)
        total_pages = len(opts.pages)
        self.sheet_label.setText(f"第 {k + 1} / {len(all_sheets)} 张纸 · 共 {total_pages} 页")
        self.prev_btn.setEnabled(k > 0)
        self.next_btn.setEnabled(k < len(all_sheets) - 1)

    # ---------- 打印 ----------
    def _print(self):
        opts = self.options()
        if not opts:
            return
        self.settings.set("print/annots", opts.annots)
        self.settings.set("print/gray", opts.gray)
        self.settings.set("print/nup", opts.nup)
        self.settings.set("print/scale", opts.scale)
        pr = self._make_printer()
        if self.printer.currentData() == PDF_TARGET:
            stem = os.path.splitext(self.doc.name)[0]
            out, _ = QFileDialog.getSaveFileName(self, "导出为 PDF", os.path.join(os.path.dirname(self.doc.path), f"{stem}_打印版.pdf"),
                                                 "PDF 文件 (*.pdf)")
            if not out:
                return
            pr.setOutputFileName(out)
        ok = print_to(pr, self.doc, opts, self)
        if ok:
            self.accept()
            win = self.parent()
            if hasattr(win, "toast"):
                win.toast("已发送到打印机" if self.printer.currentData() != PDF_TARGET else "已导出")


def print_to(printer: QPrinter, doc: PdfDocument, opts: PrintOptions, parent=None) -> bool:
    groups = sheets(opts)
    land = sheet_landscape(doc, opts)
    prog = QProgressDialog("正在准备打印…", "取消", 0, len(groups), parent)
    prog.setWindowTitle("打印")
    prog.setMinimumDuration(400)
    prog.setWindowModality(Qt.WindowModal)
    p = QPainter()
    if not p.begin(printer):
        QMessageBox.warning(parent, "打印", "无法连接打印机，请检查打印机是否在线。")
        return False
    try:
        dpi = printer.resolution()
        area = printer.pageLayout().paintRectPixels(dpi)
        area = QRectF(0, 0, area.width(), area.height())
        for k, group in enumerate(groups):
            if prog.wasCanceled():
                printer.abort()
                return False
            if k:
                printer.newPage()
            prog.setLabelText(f"正在打印第 {k + 1}/{len(groups)} 张…")
            prog.setValue(k)
            QApplication.processEvents()
            paint_sheet(p, area, doc, group, opts, dpi, land)
    finally:
        p.end()
        prog.setValue(len(groups))
    return True

