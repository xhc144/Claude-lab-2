"""一个打开的文档：封装 PyMuPDF 文档、渲染、文字缓存、批注编辑、页面管理、撤销与保存。

注意：不要长期持有 pymupdf.Page 对象——MuPDF 会复用仍打开的页面，导致读到过期的批注列表。
"""
from __future__ import annotations

import getpass
import math
import os

import pymupdf
from PySide6.QtCore import QObject, Signal

from ..core.textmap import PageText, extract_page_text
from ..core.util import write_atomic
from . import undo as U

PDF_EXTS = {".pdf"}
OPENABLE_EXTS = {".pdf", ".epub", ".xps", ".oxps", ".cbz", ".fb2", ".mobi", ".svg"}
SNAPSHOT_LIMIT = 150 * 1024 * 1024  # 超过这个大小的文档，页面结构改动不做快照（无法撤销）

ANNOT_LABELS = {
    "Ink": "手写", "Highlight": "高亮", "Underline": "下划线", "StrikeOut": "删除线",
    "Squiggly": "波浪线", "FreeText": "文本框", "Text": "便签", "Square": "矩形",
    "Circle": "椭圆", "Line": "直线", "PolyLine": "折线", "Polygon": "多边形",
    "Stamp": "印章", "Caret": "插入符", "FileAttachment": "附件", "Sound": "声音",
}


class NeedsPassword(Exception):
    pass


def _author() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "Folio"


def _seg_dist(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class PdfDocument(QObject):
    pagesChanged = Signal(list)       # 这些页需要重新渲染
    structureChanged = Signal()       # 页数/顺序/尺寸变了
    modifiedChanged = Signal(bool)
    undoChanged = Signal()

    def __init__(self, path: str, password: str | None = None, data: bytes | None = None):
        super().__init__()
        self.path = os.path.abspath(path) if path else ""
        ext = os.path.splitext(path)[1].lower() if path else ".pdf"
        if data is None:
            with open(path, "rb") as f:
                data = f.read()
        self.file_size = len(data)
        filetype = ext.lstrip(".") or "pdf"
        self._fz = pymupdf.open(stream=data, filetype=filetype)
        self.password = password or ""
        if self._fz.needs_pass:
            if not password or not self._fz.authenticate(password):
                self._fz.close()
                raise NeedsPassword()
        self.is_pdf = self._fz.is_pdf
        self._undo = U.UndoStack()
        self._rev: dict[int, int] = {}
        self._text_cache: dict[int, tuple[int, PageText]] = {}
        self._sizes: list[tuple[float, float]] = []
        self._xref_index: dict[int, int] | None = None
        self.epoch = 0  # 每次结构变化 +1，用于让渲染缓存整体失效
        self._macro: tuple[str, list] | None = None
        self.closed = False
        self._compute_sizes()

    # ---------- 基本属性 ----------
    @property
    def fz(self) -> pymupdf.Document:
        return self._fz

    @property
    def name(self) -> str:
        return os.path.basename(self.path) if self.path else "未命名.pdf"

    @property
    def editable(self) -> bool:
        return self.is_pdf

    @property
    def page_count(self) -> int:
        return self._fz.page_count

    @property
    def modified(self) -> bool:
        return not self._undo.is_clean

    def page(self, i: int) -> pymupdf.Page:
        return self._fz.load_page(i)

    def page_size(self, i: int) -> tuple[float, float]:
        return self._sizes[i]

    def revision(self, i: int) -> int:
        return self._rev.get(i, 0)

    def title(self) -> str:
        t = (self._fz.metadata or {}).get("title") or ""
        return t.strip() or self.name

    def _compute_sizes(self):
        sizes = []
        for i in range(self._fz.page_count):
            r = self._fz.load_page(i).rect
            sizes.append((max(r.width, 1.0), max(r.height, 1.0)))
        self._sizes = sizes

    # ---------- 坐标 ----------
    def to_unrot(self, i: int, x: float, y: float) -> tuple[float, float]:
        """显示坐标（已旋转，单位 pt）→ 页面未旋转坐标（文字/批注用）。"""
        p = pymupdf.Point(x, y) * self.page(i).derotation_matrix
        return p.x, p.y

    def matrices(self, i: int) -> tuple[pymupdf.Matrix, pymupdf.Matrix]:
        pg = self.page(i)
        return pg.rotation_matrix, pg.derotation_matrix

    # ---------- 文字 ----------
    def text(self, i: int) -> PageText:
        rev = self.revision(i) + self.epoch * 100000
        hit = self._text_cache.get(i)
        if hit and hit[0] == rev:
            return hit[1]
        pt = extract_page_text(self.page(i))
        self._text_cache[i] = (rev, pt)
        return pt

    def links(self, i: int) -> list[dict]:
        try:
            return self.page(i).get_links()
        except Exception:
            return []

    def search(self, i: int, term: str) -> list[pymupdf.Rect]:
        try:
            return self.page(i).search_for(term)
        except Exception:
            return []

    # ---------- 渲染 ----------
    def render(self, i: int, scale: float, clip: pymupdf.Rect | None = None,
               annots: bool = True, gray: bool = False) -> pymupdf.Pixmap:
        pg = self.page(i)
        cs = pymupdf.csGRAY if gray else pymupdf.csRGB
        return pg.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False, annots=annots, colorspace=cs)

    # ---------- 变更通知 ----------
    def _page_touched(self, i: int | None):
        if i is None:
            return
        self._rev[i] = self.revision(i) + 1
        self.pagesChanged.emit([i])

    def _structure_touched(self):
        self.epoch += 1
        self._rev.clear()
        self._text_cache.clear()
        self._xref_index = None
        self._compute_sizes()
        self.structureChanged.emit()

    def page_index_of_xref(self, xref: int) -> int | None:
        if self._xref_index is None:
            self._xref_index = {self._fz.page_xref(i): i for i in range(self._fz.page_count)}
        return self._xref_index.get(xref)

    def begin_macro(self, label: str):
        """把接下来的多步操作合并成一次撤销（例如一次拖动擦掉多条批注）。"""
        self._macro = (label, [])

    def end_macro(self):
        macro, self._macro = self._macro, None
        if macro and macro[1]:
            cmds = macro[1]
            self._push(cmds[0] if len(cmds) == 1 else U.Compound(macro[0], cmds))

    def _push(self, cmd: U.Command):
        macro = self._macro
        if macro is not None:
            macro[1].append(cmd)
            return
        was = self.modified
        self._undo.push(cmd)
        self.undoChanged.emit()
        if was != self.modified:
            self.modifiedChanged.emit(self.modified)

    # ---------- 撤销 ----------
    @property
    def can_undo(self) -> bool:
        return self._undo.can_undo

    @property
    def can_redo(self) -> bool:
        return self._undo.can_redo

    def undo_label(self) -> str:
        return self._undo.undo_label()

    def redo_label(self) -> str:
        return self._undo.redo_label()

    def undo(self):
        was = self.modified
        c = self._undo.pop_undo()
        if c:
            c.undo(self)
            self.undoChanged.emit()
            if was != self.modified:
                self.modifiedChanged.emit(self.modified)

    def redo(self):
        was = self.modified
        c = self._undo.pop_redo()
        if c:
            c.redo(self)
            self.undoChanged.emit()
            if was != self.modified:
                self.modifiedChanged.emit(self.modified)

    def _restore(self, data: bytes):
        self._fz.close()
        self._fz = pymupdf.open("pdf", data)
        if self._fz.needs_pass:
            self._fz.authenticate(self.password)
        self._structure_touched()

    # ---------- 批注：创建 ----------
    def _finish_new_annot(self, i: int, annot, label: str, color=None, width=None, opacity=None, fill=None):
        if color is not None:
            annot.set_colors(stroke=color, fill=fill)
        if width is not None:
            annot.set_border(width=width)
        if opacity is not None:
            annot.set_opacity(opacity)
        annot.set_info(title=_author())
        annot.update()
        page_xref = self._fz.page_xref(i)
        xrefs = U.with_popup(self._fz, annot.xref)
        self._push(U.AnnotToggle(label, page_xref, xrefs, added=True))
        self._page_touched(i)
        return annot.xref

    def add_ink(self, i: int, strokes: list[list[tuple[float, float]]], color, width: float, opacity: float = 1.0):
        annot = self.page(i).add_ink_annot(strokes)
        return self._finish_new_annot(i, annot, "手写", color, width, opacity)

    def add_markup(self, i: int, kind: str, rects: list, color):
        pg = self.page(i)
        quads = [pymupdf.Rect(r).quad for r in rects]
        fn = {"highlight": pg.add_highlight_annot, "underline": pg.add_underline_annot,
              "strikeout": pg.add_strikeout_annot, "squiggly": pg.add_squiggly_annot}[kind]
        annot = fn(quads)
        label = {"highlight": "高亮", "underline": "下划线", "strikeout": "删除线", "squiggly": "波浪线"}[kind]
        return self._finish_new_annot(i, annot, label, color, None, None)

    def add_freetext(self, i: int, rect, text: str, fontsize: float, color):
        pg = self.page(i)
        annot = pg.add_freetext_annot(pymupdf.Rect(rect), text, fontsize=fontsize, fontname="china-s",
                                      text_color=color, rotate=pg.rotation)
        return self._finish_new_annot(i, annot, "文本框")

    def add_note(self, i: int, point, text: str, color):
        annot = self.page(i).add_text_annot(pymupdf.Point(point), text, icon="Comment")
        return self._finish_new_annot(i, annot, "便签", color)

    def add_image_stamp(self, i: int, rect, png: bytes, label: str = "图章"):
        annot = self.page(i).add_stamp_annot(pymupdf.Rect(rect), stamp=png)
        return self._finish_new_annot(i, annot, label)

    def add_shape(self, i: int, kind: str, p0, p1, color, width: float):
        pg = self.page(i)
        if kind in ("rect", "ellipse"):
            r = pymupdf.Rect(p0, p1).normalize()
            if r.width < 2 or r.height < 2:
                return None
            annot = pg.add_rect_annot(r) if kind == "rect" else pg.add_circle_annot(r)
            label = "矩形" if kind == "rect" else "椭圆"
        else:
            if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 2:
                return None
            annot = pg.add_line_annot(pymupdf.Point(p0), pymupdf.Point(p1))
            if kind == "arrow":
                annot.set_line_ends(pymupdf.PDF_ANNOT_LE_NONE, pymupdf.PDF_ANNOT_LE_OPEN_ARROW)
            label = "箭头" if kind == "arrow" else "直线"
        return self._finish_new_annot(i, annot, label, color, width, None)

    # ---------- 批注：查询 / 删除 / 修改 ----------
    def annots_at(self, i: int, x: float, y: float, radius: float = 4.0) -> list[int]:
        hits = []
        for a in self.page(i).annots():
            t = a.type[1]
            if t == "Popup":
                continue
            r = a.rect
            if not pymupdf.Rect(r.x0 - radius, r.y0 - radius, r.x1 + radius, r.y1 + radius).contains(pymupdf.Point(x, y)):
                continue
            if t == "Ink":
                w = (a.border or {}).get("width") or 1
                ok = False
                for stroke in a.vertices or []:
                    pts = [tuple(p) for p in stroke]
                    if len(pts) == 1:
                        pts = pts * 2
                    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                        if _seg_dist(x, y, ax, ay, bx, by) <= radius + w / 2:
                            ok = True
                            break
                    if ok:
                        break
                if not ok:
                    continue
            elif t in ("Line", "PolyLine"):
                v = [tuple(p) for p in (a.vertices or [])]
                if len(v) >= 2 and min(_seg_dist(x, y, *v[k], *v[k + 1]) for k in range(len(v) - 1)) > radius + 3:
                    continue
            elif t in ("Square", "Circle") and not (a.colors or {}).get("fill"):
                # 空心形状：只在边框附近才算命中
                inner = pymupdf.Rect(r.x0 + radius + 4, r.y0 + radius + 4, r.x1 - radius - 4, r.y1 - radius - 4)
                if inner.is_valid and not inner.is_empty and inner.contains(pymupdf.Point(x, y)):
                    continue
            hits.append(a.xref)
        return hits

    def delete_annots(self, i: int, xrefs: list[int], label: str = "删除批注"):
        if not xrefs:
            return
        page_xref = self._fz.page_xref(i)
        all_x: list[int] = []
        for x in xrefs:
            all_x += U.with_popup(self._fz, x)
        cmd = U.AnnotToggle(label, page_xref, all_x, added=False)
        cmd.redo(self)
        self._push(cmd)

    def _modify(self, i: int, xref: int, label: str, fn):
        before = U.AnnotModify.capture(self._fz, xref)
        pg = self.page(i)
        annot = pg.load_annot(xref)
        fn(annot)
        annot.update()
        del annot, pg
        after = U.AnnotModify.capture(self._fz, xref)
        self._push(U.AnnotModify(label, self._fz.page_xref(i), before, after))
        self._page_touched(i)

    def set_annot_color(self, i: int, xref: int, color):
        def fn(a):
            t = a.type[1]
            if t == "FreeText":
                a.update(text_color=color)
            else:
                a.set_colors(stroke=color)
        self._modify(i, xref, "修改颜色", fn)

    def set_annot_text(self, i: int, xref: int, text: str):
        def fn(a):
            info = a.info
            info["content"] = text
            a.set_info(info)
        self._modify(i, xref, "编辑批注", fn)

    def annot_info(self, i: int, xref: int) -> dict:
        pg = self.page(i)
        a = pg.load_annot(xref)
        return {"type": a.type[1], "content": a.info.get("content", ""), "rect": tuple(a.rect),
                "colors": a.colors}

    def list_annots(self) -> list[dict]:
        out = []
        for i in range(self.page_count):
            pg = self.page(i)
            for a in pg.annots():
                t = a.type[1]
                if t in ("Popup", "Link", "Widget"):
                    continue
                content = (a.info or {}).get("content", "")
                if not content and t in ("Highlight", "Underline", "StrikeOut", "Squiggly"):
                    try:
                        content = pg.get_textbox(a.rect).strip()
                    except Exception:
                        content = ""
                col = (a.colors or {}).get("stroke") or (a.colors or {}).get("fill") or (0.4, 0.4, 0.4)
                out.append({"page": i, "xref": a.xref, "type": t, "label": ANNOT_LABELS.get(t, t),
                            "content": " ".join(content.split())[:120], "color": tuple(col),
                            "rect": tuple(a.rect)})
        return out

    # ---------- 页面管理 ----------
    def snapshot(self) -> bytes | None:
        """整份文档的快照，用于撤销大范围改动；文档太大时不做（返回 None）。"""
        return self._fz.tobytes(garbage=0) if self.file_size < SNAPSHOT_LIMIT else None

    def commit_snapshot(self, label: str, before: bytes | None):
        if before is None:
            self._undo = U.UndoStack()
            self._undo.clean_index = -1  # 标记为已修改
            self.undoChanged.emit()
            self.modifiedChanged.emit(True)
        else:
            self._push(_LazySnapshot(label, before))

    def _structural(self, label: str, fn):
        before = self.snapshot()
        fn()
        self._structure_touched()
        self.commit_snapshot(label, before)

    # ---------- 文字识别 ----------
    def pages_needing_ocr(self, pages: list[int] | None = None) -> list[int]:
        from ..ocr.layer import needs_ocr

        if not self.is_pdf:
            return []
        out = []
        for i in (range(self.page_count) if pages is None else pages):
            try:
                if needs_ocr(self.page(i)):
                    out.append(i)
            except Exception:
                pass
        return out

    def looks_scanned(self, sample: int = 3) -> bool:
        """前几页都没有文字但有图片：大概率是扫描件。"""
        n = min(sample, self.page_count)
        return self.is_pdf and n > 0 and len(self.pages_needing_ocr(list(range(n)))) == n

    def ocr_image(self, i: int, gray: bool = True):
        from ..ocr.layer import render_for_ocr
        from ..ocr.system import OcrImage

        pix = render_for_ocr(self.page(i), gray=gray)
        return OcrImage(pix.width, pix.height, pix.samples, pix.tobytes("png"), pix.tobytes("jpeg", jpg_quality=85))

    def apply_ocr(self, i: int, lines) -> int:
        """写入识别出的文字层（调用方负责用 snapshot/commit_snapshot 包成一次撤销）。"""
        from ..ocr.layer import add_text_layer

        n = add_text_layer(self.page(i), lines)
        self._text_cache.pop(i, None)
        self._page_touched(i)
        return n

    def rotate_pages(self, pages: list[int], delta: int):
        xrefs = [self._fz.page_xref(i) for i in pages]
        before = [self._fz[i].rotation for i in pages]
        after = [(r + delta) % 360 for r in before]
        cmd = U.Rotate(xrefs, before, after)
        cmd.redo(self)
        self._push(cmd)

    def delete_pages(self, pages: list[int]):
        pages = sorted(set(pages))
        if len(pages) >= self.page_count:
            raise ValueError("不能删除全部页面")
        self._structural("删除页面", lambda: self._fz.delete_pages(pages))

    def move_pages(self, pages: list[int], dest: int):
        """把 pages 移动到原顺序中 dest 位置之前（dest 可等于 page_count 表示末尾）。"""
        pages = sorted(set(pages))
        rest = [p for p in range(self.page_count) if p not in pages]
        insert_at = len([p for p in rest if p < dest])
        order = rest[:insert_at] + pages + rest[insert_at:]
        if order == list(range(self.page_count)):
            return
        self._structural("移动页面", lambda: self._fz.select(order))

    def reorder(self, order: list[int]):
        if order == list(range(self.page_count)):
            return
        self._structural("调整页面顺序", lambda: self._fz.select(order))

    def insert_blank(self, after: int):
        w, h = self.page_size(max(0, min(after, self.page_count - 1))) if self.page_count else (595, 842)
        self._structural("插入空白页", lambda: self._fz.new_page(pno=after + 1, width=w, height=h))

    def insert_file(self, path: str, at: int):
        from ..core.merge import open_as_pdf

        src = open_as_pdf(path)

        def fn():
            self._fz.insert_pdf(src, start_at=at)
        try:
            self._structural("插入文件", fn)
        finally:
            src.close()

    def extract_pages(self, pages: list[int], out_path: str):
        from ..core.split import subset

        d = subset(self._fz, sorted(set(pages)))
        try:
            write_atomic(out_path, d.tobytes(garbage=3, deflate=True))
        finally:
            d.close()

    # ---------- 保存 ----------
    def save(self, path: str | None = None):
        path = os.path.abspath(path or self.path)
        if self.is_pdf:
            # 不做垃圾回收：保留被"删除"的批注对象，保存后仍能撤销
            data = self._fz.tobytes(garbage=0, deflate=True)
        else:
            data = self._fz.convert_to_pdf()
        write_atomic(path, data)
        if path != self.path and not self.is_pdf:
            # 另存为 PDF 后切换到新文档
            self._fz.close()
            self._fz = pymupdf.open("pdf", data)
            self.is_pdf = True
            self._structure_touched()
        self.path = path
        self.file_size = len(data)
        self._undo.mark_clean()
        self.modifiedChanged.emit(False)

    def close(self):
        self.closed = True
        try:
            self._fz.close()
        except Exception:
            pass


class _LazySnapshot(U.Command):
    """只在操作前存快照；撤销时再把当前状态存下来供重做。"""

    def __init__(self, label: str, before: bytes):
        self.label = label
        self.before = before
        self.after: bytes | None = None
        self.snapshot_bytes = len(before)

    def undo(self, doc):
        if self.after is None:
            self.after = doc.fz.tobytes(garbage=0)
            self.snapshot_bytes += len(self.after)
        doc._restore(self.before)

    def redo(self, doc):
        doc._restore(self.after)
