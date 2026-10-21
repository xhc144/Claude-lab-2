"""PDF 工具对话框：压缩、图片转 PDF、合并、拆分。"""
from __future__ import annotations

import os

from PIL import Image
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout,
                               QInputDialog, QLineEdit, QListWidgetItem, QMessageBox, QPushButton, QRadioButton,
                               QSpinBox, QWidget)

from ...core import compress, images, merge, split
from ...core.office import OFFICE_EXTS, find_soffice
from ...core.util import human_size, parse_page_ranges, parse_range_groups, unique_path, write_atomic
from ...icons import pixmap
from ...theme import theme
from ..widgets import FileList, Segmented, label
from .base import ToolDialog, choose_save_path, form_row, section

IMAGE_FILTER = "图片 (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.heic *.heif)"


def _list_header(title: str, add_cb, remove_cb, clear_cb=None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addWidget(section(title))
    row.addStretch(1)
    add = QPushButton("添加文件")
    add.clicked.connect(add_cb)
    row.addWidget(add)
    rm = QPushButton("移除")
    rm.clicked.connect(remove_cb)
    row.addWidget(rm)
    if clear_cb:
        cl = QPushButton("清空")
        cl.clicked.connect(clear_cb)
        row.addWidget(cl)
    return row


def _file_icon(kind: str) -> QIcon:
    name = {"pdf": "file-text", "image": "image", "office": "file", "ebook": "book-open"}.get(kind, "file")
    return QIcon(pixmap(name, theme.c("accent"), 20))


# =============================================================== 压缩
class CompressDialog(ToolDialog):
    LEVELS = [("light", "轻度"), ("medium", "推荐"), ("strong", "强力"), ("extreme", "极限")]

    def __init__(self, parent, paths=None):
        super().__init__(parent, "压缩 PDF", "设定文件最大体积，程序会自动寻找画质最好又不超过上限的压缩方式。",
                         "shrink", 660, 600, independent=True)
        b = self.body_layout
        b.addLayout(_list_header("文件", self._add, self._remove))
        self.files = FileList({".pdf"})
        self.files.filesDropped.connect(self.add_paths)
        b.addWidget(self.files, 1)

        b.addWidget(section("压缩方式"))
        self.mode = Segmented([("target", "指定最大大小"), ("level", "按压缩程度")], "target")
        self.mode.changed.connect(self._mode_changed)
        b.addWidget(self.mode)

        self.target_row = QWidget()
        tr = QHBoxLayout(self.target_row)
        tr.setContentsMargins(0, 0, 0, 0)
        self.target = QDoubleSpinBox()
        self.target.setRange(0.05, 5000)
        self.target.setDecimals(2)
        self.target.setSingleStep(0.5)
        self.target.setSuffix(" MB")
        self.target.setValue(2.0)
        self.target.setFixedWidth(130)
        tr.addLayout(form_row("每个文件不超过", self.target))
        self.target_hint = label("", "Faint")
        tr.addWidget(self.target_hint)
        tr.addStretch(1)
        b.addWidget(self.target_row)

        self.level_row = QWidget()
        lr = QHBoxLayout(self.level_row)
        lr.setContentsMargins(0, 0, 0, 0)
        self.level = Segmented(self.LEVELS, "medium")
        lr.addLayout(form_row("压缩程度", self.level))
        self.level_row.hide()
        b.addWidget(self.level_row)

        self.gray = QCheckBox("转为黑白（灰度），体积更小")
        self.raster = QCheckBox("仍达不到时，把页面转为图片（文字将无法选中、搜索）")
        b.addWidget(self.gray)
        b.addWidget(self.raster)

        out = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("与原文件相同的文件夹（文件名加「_压缩」，不会覆盖原文件）")
        browse = QPushButton("浏览…")
        browse.clicked.connect(lambda: self._pick_dir(self.out_dir))
        out.addWidget(self.out_dir, 1)
        out.addWidget(browse)
        b.addLayout(form_row("保存到", out, expand=True))
        self.run_btn.setText("开始压缩")
        if paths:
            self.add_paths(paths)

    def _pick_dir(self, edit):
        d = QFileDialog.getExistingDirectory(self, "选择文件夹", edit.text() or os.path.expanduser("~"))
        if d:
            edit.setText(d)

    def _mode_changed(self, k):
        self.target_row.setVisible(k == "target")
        self.level_row.setVisible(k == "level")

    def _add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择 PDF", "", "PDF 文件 (*.pdf)")
        self.add_paths(paths)

    def add_paths(self, paths):
        have = set(self.files.paths())
        for p in paths:
            if p in have or not p.lower().endswith(".pdf"):
                continue
            it = QListWidgetItem(_file_icon("pdf"), "")
            it.setData(Qt.UserRole, p)
            it.setToolTip(p)
            self._set_item(it, f"{human_size(os.path.getsize(p))}")
            self.files.addItem(it)
        self._update_hint()

    def _set_item(self, it, sub):
        it.setText(f"{os.path.basename(it.data(Qt.UserRole))}\n{sub}")
        it.setSizeHint(QSize(0, 46))

    def _remove(self):
        for it in self.files.selectedItems():
            self.files.takeItem(self.files.row(it))
        self._update_hint()

    def _update_hint(self):
        paths = self.files.paths()
        if len(paths) == 1:
            size = os.path.getsize(paths[0])
            self.target_hint.setText(f"原文件 {human_size(size)}")
            mb = size / 1024 / 1024
            self.target.setValue(max(0.1, round(mb / 2, 1)) if mb > 0.2 else 0.1)
        elif paths:
            self.target_hint.setText(f"共 {len(paths)} 个文件")

    def make_job(self):
        paths = self.files.paths()
        if not paths:
            self.set_status("请先添加 PDF 文件", error=True)
            return None
        mode = self.mode.value()
        target = int(self.target.value() * 1024 * 1024) if mode == "target" else None
        preset = self.level.value()
        gray, raster = self.gray.isChecked(), self.raster.isChecked()
        out_dir = self.out_dir.text().strip()

        def job(progress, cancel):
            results = []
            for k, p in enumerate(paths):
                def sub(f, m, k=k):
                    progress((k + f) / len(paths), f"[{k + 1}/{len(paths)}] {m}")
                with open(p, "rb") as fh:
                    src = fh.read()
                res = compress.compress_pdf(src, target_bytes=target, preset=preset, gray=gray,
                                            allow_rasterize=raster, progress=sub, cancel=cancel)
                stem = os.path.splitext(os.path.basename(p))[0]
                folder = out_dir or os.path.dirname(p)
                out = unique_path(os.path.join(folder, f"{stem}_压缩.pdf"))
                write_atomic(out, res.data)
                results.append((p, out, res))
            return results
        return job

    def on_done(self, results):
        ok = 0
        for row, (p, out, res) in enumerate(results):
            it = self.files.item(row)
            pct = (1 - res.ratio) * 100
            mark = "✓" if res.reached else "⚠"
            sub = f"{human_size(res.original_size)} → {human_size(res.size)}（减小 {pct:.0f}%）{mark}  {res.level}"
            if res.note:
                sub += f"\n{res.note}"
                it.setSizeHint(QSize(0, 64))
            if it:
                it.setText(f"{os.path.basename(p)}\n{sub}")
            ok += res.reached
        msg = f"完成：{ok}/{len(results)} 个文件达到目标" if self.mode.value() == "target" else f"完成：已压缩 {len(results)} 个文件"
        self.set_status(msg, ok=ok == len(results), error=ok < len(results) and self.mode.value() == "target")
        if results:
            self.show_output(results[-1][1], openable=len(results) == 1)


# =============================================================== 图片转 PDF
class ImagesDialog(ToolDialog):
    def __init__(self, parent, paths=None):
        super().__init__(parent, "图片转 PDF", "支持照片、截图和长图。长图会按页面比例自动分页，并尽量在空白处切开。",
                         "images", 720, 660, independent=True)
        b = self.body_layout
        b.addLayout(_list_header("图片（可拖动排序）", self._add, self._remove, self._clear))
        self.files = FileList(images.IMAGE_EXTS)
        self.files.setIconSize(QSize(36, 36))
        self.files.filesDropped.connect(self.add_paths)
        self.files.changed.connect(self._update_summary)
        b.addWidget(self.files, 1)

        b.addWidget(section("页面设置"))
        self.size = QComboBox()
        for key, text in (("A4", "A4"), ("A3", "A3"), ("A5", "A5"), ("Letter", "Letter"), ("fit", "与图片相同")):
            self.size.addItem(text, key)
        self.size.currentIndexChanged.connect(self._update_summary)
        self.orient = Segmented([("auto", "自动"), ("portrait", "纵向"), ("landscape", "横向")], "auto")
        self.margin = Segmented([("0", "无边距"), ("18", "窄"), ("36", "标准")], "0")
        self.margin.changed.connect(lambda _: self._update_summary())
        row = QHBoxLayout()
        row.addLayout(form_row("纸张", self.size))
        row.addSpacing(10)
        row.addWidget(self.orient)
        row.addSpacing(10)
        row.addWidget(self.margin)
        row.addStretch(1)
        b.addLayout(row)
        self.split = QCheckBox("长图自动分页")
        self.split.setChecked(True)
        self.split.toggled.connect(self._update_summary)
        self.smart = QCheckBox("智能切分（避开文字和图片）")
        self.smart.setChecked(True)
        self.split.toggled.connect(self.smart.setEnabled)
        r2 = QHBoxLayout()
        r2.addWidget(self.split)
        r2.addSpacing(16)
        r2.addWidget(self.smart)
        r2.addStretch(1)
        b.addLayout(r2)
        self.quality = Segmented([("original", "原图"), ("high", "高清"), ("medium", "标准"), ("small", "小体积")], "high")
        b.addLayout(form_row("画质", self.quality))
        self.summary = label("", "Muted")
        b.addWidget(self.summary)
        self.run_btn.setText("生成 PDF")
        self._dims: dict[str, tuple[int, int]] = {}
        if paths:
            self.add_paths(paths)

    def _add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", IMAGE_FILTER + ";;所有文件 (*)")
        self.add_paths(paths)

    def _remove(self):
        for it in self.files.selectedItems():
            self.files.takeItem(self.files.row(it))
        self._update_summary()

    def _clear(self):
        self.files.clear()
        self._update_summary()

    def add_paths(self, paths):
        for p in paths:
            if not self.files.accepts(p):
                continue
            reader = QImageReader(p)
            reader.setAutoTransform(True)
            sz = reader.size()
            if not sz.isValid():
                try:
                    with Image.open(p) as im:
                        w, h = im.size
                except Exception:
                    continue
            else:
                w, h = sz.width(), sz.height()
            self._dims[p] = (w, h)
            scale = 72 / max(w, h, 1)
            reader.setScaledSize(QSize(max(1, int(w * scale)), max(1, int(h * scale))))
            img = reader.read()
            icon = QIcon(QPixmap.fromImage(img)) if not img.isNull() else _file_icon("image")
            it = QListWidgetItem(icon, "")
            it.setData(Qt.UserRole, p)
            it.setToolTip(p)
            it.setSizeHint(QSize(0, 48))
            self.files.addItem(it)
        self._update_summary()

    def _opts(self) -> images.ImageOptions:
        return images.ImageOptions(page_size=self.size.currentData(), orientation=self.orient.value(),
                                   margin=float(self.margin.value()), split_long=self.split.isChecked(),
                                   smart_split=self.smart.isChecked(), quality=self.quality.value())

    def _update_summary(self):
        opts = self._opts()
        total = 0
        for row in range(self.files.count()):
            it = self.files.item(row)
            p = it.data(Qt.UserRole)
            w, h = self._dims.get(p, (1, 1))
            n = images.plan_slices(w, h, opts)
            total += n
            extra = f" · 长图，将分为 {n} 页" if n > 1 else ""
            it.setText(f"{os.path.basename(p)}\n{w}×{h}{extra}")
        n = self.files.count()
        self.summary.setText(f"共 {n} 张图片，预计生成 {total} 页" if n else "")

    def make_job(self):
        paths = self.files.paths()
        if not paths:
            self.set_status("请先添加图片", error=True)
            return None
        first = paths[0]
        default = os.path.join(os.path.dirname(first), os.path.splitext(os.path.basename(first))[0] + ".pdf")
        out = choose_save_path(self, "保存 PDF", unique_path(default))
        if not out:
            return None
        opts = self._opts()

        def job(progress, cancel):
            doc = images.images_to_pdf(paths, opts, progress, cancel)
            n = doc.page_count
            write_atomic(out, doc.tobytes(garbage=3, deflate=True))
            doc.close()
            return out, n
        return job

    def on_done(self, result):
        out, n = result
        self.set_status(f"已生成 {os.path.basename(out)}，共 {n} 页", ok=True)
        self.show_output(out, openable=True)


# =============================================================== 合并
class MergeDialog(ToolDialog):
    def __init__(self, parent, paths=None):
        super().__init__(parent, "合并文件", "把多个 PDF、图片、Word/Excel/PPT 合并成一个 PDF。双击文件可设置只合并其中某些页。",
                         "combine", 700, 600, independent=True)
        b = self.body_layout
        b.addLayout(_list_header("文件（可拖动排序）", self._add, self._remove, self._clear))
        self.files = FileList(merge.ALL_EXTS)
        self.files.filesDropped.connect(self.add_paths)
        self.files.itemDoubleClicked.connect(self._edit_range)
        b.addWidget(self.files, 1)
        self.bookmarks = QCheckBox("为每个文件生成书签（目录）")
        self.bookmarks.setChecked(True)
        b.addWidget(self.bookmarks)
        self.office_hint = label("", "Faint", wrap=True)
        b.addWidget(self.office_hint)
        self.run_btn.setText("合并")
        if paths:
            self.add_paths(paths)

    def _add(self):
        exts = " ".join(f"*{e}" for e in sorted(merge.ALL_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", f"支持的文件 ({exts});;所有文件 (*)")
        self.add_paths(paths)

    def _remove(self):
        for it in self.files.selectedItems():
            self.files.takeItem(self.files.row(it))
        self._update_hint()

    def _clear(self):
        self.files.clear()
        self._update_hint()

    def add_paths(self, paths):
        for p in paths:
            if not self.files.accepts(p):
                continue
            kind = merge.kind_of(p)
            it = QListWidgetItem(_file_icon(kind), "")
            it.setData(Qt.UserRole, p)
            it.setData(Qt.UserRole + 1, "")
            it.setToolTip(p)
            self._refresh_item(it)
            self.files.addItem(it)
        self._update_hint()

    def _page_count(self, p) -> int | None:
        if merge.kind_of(p) != "pdf":
            return None
        try:
            import pymupdf

            with pymupdf.open(p) as d:
                return d.page_count
        except Exception:
            return None

    def _refresh_item(self, it):
        p = it.data(Qt.UserRole)
        rng = it.data(Qt.UserRole + 1) or ""
        kind = merge.kind_of(p)
        n = self._page_count(p)
        desc = {"pdf": f"PDF · {n} 页" if n else "PDF", "image": "图片", "office": "Office 文档",
                "ebook": "电子书 / 其它"}.get(kind, "")
        if rng:
            desc += f" · 只合并第 {rng} 页"
        elif kind == "pdf":
            desc += " · 全部页（双击可选页）"
        it.setText(f"{os.path.basename(p)}\n{desc}")
        it.setSizeHint(QSize(0, 46))

    def _edit_range(self, it):
        p = it.data(Qt.UserRole)
        n = self._page_count(p)
        hint = f"（共 {n} 页）" if n else ""
        text, ok = QInputDialog.getText(self, "选择页码", f"要合并的页码{hint}，例如 1-3,5。留空表示全部：",
                                        text=it.data(Qt.UserRole + 1) or "")
        if not ok:
            return
        text = text.strip()
        if text and n:
            try:
                parse_page_ranges(text, n)
            except ValueError as ex:
                QMessageBox.warning(self, "页码", str(ex))
                return
        it.setData(Qt.UserRole + 1, text)
        self._refresh_item(it)

    def _update_hint(self):
        has_office = any(os.path.splitext(p)[1].lower() in OFFICE_EXTS for p in self.files.paths())
        if has_office and not find_soffice():
            self.office_hint.setText("⚠ 列表里有 Word/Excel/PPT 文件，转换需要先安装免费的 LibreOffice（libreoffice.org）。")
        elif has_office:
            self.office_hint.setText("Office 文档会先用 LibreOffice 转换，可能需要多等一会儿。")
        else:
            self.office_hint.setText("")

    def make_job(self):
        items = [merge.MergeItem(self.files.item(r).data(Qt.UserRole), self.files.item(r).data(Qt.UserRole + 1) or "")
                 for r in range(self.files.count())]
        if len(items) < 1:
            self.set_status("请至少添加一个文件", error=True)
            return None
        first = items[0].path
        default = os.path.join(os.path.dirname(first), "合并.pdf")
        out = choose_save_path(self, "保存合并后的 PDF", unique_path(default))
        if not out:
            return None
        bookmarks = self.bookmarks.isChecked()

        def job(progress, cancel):
            doc = merge.merge_files(items, bookmarks=bookmarks, progress=progress, cancel=cancel)
            n = doc.page_count
            write_atomic(out, doc.tobytes(garbage=3, deflate=True))
            doc.close()
            return out, n
        return job

    def on_done(self, result):
        out, n = result
        self.set_status(f"已合并为 {os.path.basename(out)}，共 {n} 页", ok=True)
        self.show_output(out, openable=True)


# =============================================================== 拆分
class SplitDialog(ToolDialog):
    def __init__(self, parent, paths=None):
        super().__init__(parent, "拆分 PDF", "把一个 PDF 拆成多个文件。", "scissors", 600, 520, independent=True)
        b = self.body_layout
        b.addWidget(section("文件"))
        src = QHBoxLayout()
        self.src = QLineEdit()
        self.src.setPlaceholderText("选择要拆分的 PDF")
        self.src.textChanged.connect(self._src_changed)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._pick)
        src.addWidget(self.src, 1)
        src.addWidget(browse)
        b.addLayout(src)
        self.info = label("", "Faint")
        b.addWidget(self.info)

        b.addWidget(section("拆分方式"))
        self.group = QButtonGroup(self)
        self.r_every = QRadioButton("每")
        self.every = QSpinBox()
        self.every.setRange(1, 100000)
        self.every.setValue(1)
        self.every.setFixedWidth(80)
        self.r_ranges = QRadioButton("按页码范围")
        self.ranges = QLineEdit()
        self.ranges.setPlaceholderText("例如 1-3, 4-10, 11-（每组一个文件）")
        self.r_size = QRadioButton("每个文件不超过")
        self.size = QDoubleSpinBox()
        self.size.setRange(0.1, 5000)
        self.size.setValue(5)
        self.size.setSuffix(" MB")
        self.size.setFixedWidth(110)
        for r in (self.r_every, self.r_ranges, self.r_size):
            self.group.addButton(r)
        self.r_every.setChecked(True)
        row1 = QHBoxLayout()
        row1.addWidget(self.r_every)
        row1.addWidget(self.every)
        row1.addWidget(label("页拆成一个文件（填 1 即每页一个文件）", "Muted"))
        row1.addStretch(1)
        b.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(self.r_ranges)
        row2.addWidget(self.ranges, 1)
        b.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(self.r_size)
        row3.addWidget(self.size)
        row3.addStretch(1)
        b.addLayout(row3)
        self.ranges.textEdited.connect(lambda _: self.r_ranges.setChecked(True))
        self.every.valueChanged.connect(lambda _: self.r_every.setChecked(True))
        self.size.valueChanged.connect(lambda _: self.r_size.setChecked(True))

        b.addWidget(section("保存到"))
        out = QHBoxLayout()
        self.out_dir = QLineEdit()
        ob = QPushButton("浏览…")
        ob.clicked.connect(self._pick_out)
        out.addWidget(self.out_dir, 1)
        out.addWidget(ob)
        b.addLayout(out)
        b.addStretch(1)
        self.run_btn.setText("拆分")
        self._pages = 0
        if paths:
            self.add_paths(paths)

    def add_paths(self, paths):
        pdfs = [p for p in paths if p.lower().endswith(".pdf")]
        if pdfs:
            self.src.setText(pdfs[0])

    def _pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 PDF", "", "PDF 文件 (*.pdf)")
        if p:
            self.src.setText(p)

    def _pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择文件夹", self.out_dir.text() or os.path.expanduser("~"))
        if d:
            self.out_dir.setText(d)

    def _src_changed(self, p):
        p = p.strip()
        self._pages = 0
        if os.path.isfile(p):
            try:
                import pymupdf

                with pymupdf.open(p) as d:
                    self._pages = d.page_count
                self.info.setText(f"共 {self._pages} 页 · {human_size(os.path.getsize(p))}")
                stem = os.path.splitext(os.path.basename(p))[0]
                self.out_dir.setText(os.path.join(os.path.dirname(p), f"{stem}_拆分"))
            except Exception as ex:  # noqa: BLE001
                self.info.setText(f"无法读取：{ex}")
        else:
            self.info.setText("")

    def make_job(self):
        path = self.src.text().strip()
        if not os.path.isfile(path) or not self._pages:
            self.set_status("请先选择一个 PDF", error=True)
            return None
        if self.r_every.isChecked():
            mode, value = ("single", None) if self.every.value() == 1 else ("every", self.every.value())
        elif self.r_ranges.isChecked():
            mode, value = "ranges", self.ranges.text()
            try:
                parse_range_groups(value, self._pages)
            except ValueError as ex:
                self.set_status(str(ex), error=True)
                return None
        else:
            mode, value = "size", int(self.size.value() * 1024 * 1024)
        out_dir = self.out_dir.text().strip() or os.path.dirname(path)

        def job(progress, cancel):
            return split.split_pdf(path, out_dir, mode, value, progress=progress, cancel=cancel)
        return job

    def on_done(self, outputs):
        self.set_status(f"已拆分为 {len(outputs)} 个文件", ok=True)
        if outputs:
            self.show_output(outputs[0])


DIALOGS = {"compress": CompressDialog, "images": ImagesDialog, "merge": MergeDialog, "split": SplitDialog}


def open_tool_dialog(main, key: str, paths: list[str] | None = None):
    if paths is None and key in ("compress", "split"):
        tab = getattr(main, "cur", None)
        if tab is not None and tab.doc.is_pdf and tab.doc.path:
            paths = [tab.doc.path]
            if tab.doc.modified:
                main.toast("提示：工具处理的是磁盘上已保存的版本，未保存的修改不包含在内", 4000)
    # 同一个工具已经开着（而且没在处理）时，把文件加进去，不再开新窗口：
    # 在资源管理器里选中好几个文件再点右键菜单，每个文件会各启动一次 Folio，最后都汇总到同一个窗口
    dlg = next((w for w in getattr(main, "tool_windows", []) if isinstance(w, DIALOGS[key]) and not w.busy), None)
    if dlg is None:
        dlg = DIALOGS[key](main, paths)
        windows = getattr(main, "tool_windows", None)
        if windows is not None:
            windows.append(dlg)
            dlg.finished.connect(lambda _=0, d=dlg: d in windows and windows.remove(d))
        if main.isVisible():  # 第一次显示在主窗口中间；之后它是独立窗口，可以随便移开
            dlg.move(main.geometry().center() - dlg.rect().center())
    elif paths:
        dlg.add_paths(paths)
    dlg.show()
    if dlg.isMinimized():
        dlg.setWindowState(dlg.windowState() & ~Qt.WindowMinimized)
    dlg.raise_()
    dlg.activateWindow()
    return dlg

