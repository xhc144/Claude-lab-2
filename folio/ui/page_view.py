"""页面视图：连续滚动 / 双页 / 演示模式，按需渲染（放大时分块），以及各种覆盖层的绘制。"""
from __future__ import annotations

import math
import time
from collections import OrderedDict

import numpy as np
import pymupdf
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractScrollArea, QApplication

from ..model.document import PdfDocument
from ..theme import parse_color, theme

PT_TO_PX = 96.0 / 72.0
MIN_ZOOM, MAX_ZOOM = 0.1, 8.0
ZOOM_STEPS = [0.25, 0.33, 0.5, 0.67, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]
TILE = 1024
TILE_THRESHOLD = 2600 * 2600   # 页面像素数超过它就分块渲染
CACHE_BYTES = 320 * 1024 * 1024


def pix_to_qimage(pix: pymupdf.Pixmap, tone: str) -> QImage:
    w, h, n = pix.width, pix.height, pix.n
    if tone != "normal" or n == 1:
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, pix.stride)[:, :w * n].reshape(h, w, n)
        if n == 1:
            arr = np.repeat(arr, 3, axis=2)
        arr = arr.astype(np.float32)
        if tone == "night":
            # 反色并压缩到柔和的灰阶区间，避免纯黑纯白刺眼
            arr = 34 + (255 - arr) * (205 / 255)
        elif tone == "sepia":
            arr = arr * np.array([0.98, 0.94, 0.84], dtype=np.float32)
        out = np.ascontiguousarray(arr.clip(0, 255).astype(np.uint8))
        img = QImage(out.data, w, h, w * 3, QImage.Format_RGB888)
        return img.copy()
    return QImage(pix.samples, w, h, pix.stride, QImage.Format_RGB888).copy()


class PageView(QAbstractScrollArea):
    currentPageChanged = Signal(int)
    zoomChanged = Signal(float)
    contextMenuAt = Signal(object, object)   # (QPoint 全局坐标, hit 或 None)
    selectionChanged = Signal()
    readRequested = Signal(int, int)          # 页码, 字符下标

    GAP = 16
    MARGIN = 24

    def __init__(self, doc: PdfDocument, parent=None, presentation: bool = False):
        super().__init__(parent)
        self.doc = doc
        self.presentation = presentation
        self.zoom = 1.0
        self.fit_mode: str | None = "page" if presentation else "width"
        self.layout_mode = "present" if presentation else "single"
        self.tone = "normal"
        self.present_page = 0
        self._rects: list[QRectF] = []
        self._content_w = 0.0
        self._content_h = 0.0
        self._cache: OrderedDict = OrderedDict()
        self._cache_bytes = 0
        self._fallback: dict[int, tuple[float, int, QImage]] = {}
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._render_next)
        self._zooming_until = 0.0
        self._current = 0
        self._mats: dict[int, tuple] = {}

        # 覆盖层数据（均为未旋转页面坐标）
        self.search_hits: dict[int, list] = {}
        self.search_current: tuple[int, int] | None = None
        self.read_highlight: tuple[int, list] | None = None
        self.selection: tuple[int, int, int, int] | None = None   # (页a, 下标a, 页b, 下标b)
        self.flash: tuple[int, tuple, float] | None = None          # 跳转后闪烁提示

        self.tool = None
        self._panning: QPoint | None = None
        self._space_down = False

        self.setFrameShape(QAbstractScrollArea.NoFrame)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().setAttribute(Qt.WA_OpaquePaintEvent)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        self.verticalScrollBar().setSingleStep(40)
        self.horizontalScrollBar().setSingleStep(40)
        if presentation:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        doc.pagesChanged.connect(self._on_pages_changed)
        doc.structureChanged.connect(self._on_structure_changed)
        theme.changed.connect(self.viewport().update)
        self._relayout()

    # ================= 布局 =================
    @property
    def scale(self) -> float:
        return self.zoom * PT_TO_PX

    def _rows(self) -> list[list[int]]:
        n = self.doc.page_count
        if self.layout_mode == "present":
            return [[min(self.present_page, n - 1)]] if n else []
        if self.layout_mode == "double":
            return [list(range(i, min(i + 2, n))) for i in range(0, n, 2)]
        return [[i] for i in range(n)]

    def _relayout(self):
        s = self.scale
        n = self.doc.page_count
        rects = [QRectF() for _ in range(n)]
        margin = 0 if self.layout_mode == "present" else self.MARGIN
        y = margin
        max_w = 0.0
        for row in self._rows():
            ws = [self.doc.page_size(i)[0] * s for i in row]
            hs = [self.doc.page_size(i)[1] * s for i in row]
            row_w = sum(ws) + self.GAP * (len(row) - 1)
            row_h = max(hs)
            x = -row_w / 2
            for i, w, h in zip(row, ws, hs):
                rects[i] = QRectF(x, y + (row_h - h) / 2, w, h)
                x += w + self.GAP
            y += row_h + self.GAP
            max_w = max(max_w, row_w)
        self._rects = rects
        self._content_w = max_w + 2 * margin
        self._content_h = y - self.GAP + margin if n else 0
        self._update_scrollbars()

    def _update_scrollbars(self):
        vw, vh = self.viewport().width(), self.viewport().height()
        hs, vs = self.horizontalScrollBar(), self.verticalScrollBar()
        hs.setRange(0, max(0, int(math.ceil(self._content_w - vw))))
        hs.setPageStep(vw)
        vs.setRange(0, max(0, int(math.ceil(self._content_h - vh))))
        vs.setPageStep(int(vh * 0.9))

    def _origin(self) -> QPointF:
        """布局坐标 → 视口坐标的偏移。"""
        vw, vh = self.viewport().width(), self.viewport().height()
        ox = max(self._content_w, vw) / 2 - self.horizontalScrollBar().value()
        oy = -self.verticalScrollBar().value()
        if self.layout_mode == "present" and self._content_h < vh:
            oy = (vh - self._content_h) / 2
        return QPointF(ox, oy)

    def page_rect(self, i: int) -> QRectF:
        if i < 0 or i >= len(self._rects) or self._rects[i].isNull():
            return QRectF()
        return self._rects[i].translated(self._origin())

    def visible_pages(self) -> list[int]:
        vr = QRectF(self.viewport().rect())
        o = self._origin()
        out = []
        for i, r in enumerate(self._rects):
            if r.isNull():
                continue
            if r.translated(o).intersects(vr):
                out.append(i)
            elif out:
                if self.layout_mode != "double":
                    break
        return out

    # ================= 缩放 =================
    def fit_zoom(self, mode: str) -> float:
        vw = max(50, self.viewport().width() - (0 if self.presentation else 2 * self.MARGIN + 4))
        vh = max(50, self.viewport().height() - (0 if self.presentation else 2 * self.MARGIN))
        if not self.doc.page_count:
            return 1.0
        row = next((r for r in self._rows() if self._current in r), [0])
        w = sum(self.doc.page_size(i)[0] for i in row) + self.GAP / PT_TO_PX * (len(row) - 1)
        h = max(self.doc.page_size(i)[1] for i in row)
        zw = vw / (w * PT_TO_PX)
        if mode == "width":
            return max(MIN_ZOOM, min(MAX_ZOOM, zw))
        zh = vh / (h * PT_TO_PX)
        return max(MIN_ZOOM, min(MAX_ZOOM, min(zw, zh)))

    def set_zoom(self, zoom: float, anchor: QPointF | None = None, keep_fit: bool = False):
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        if not keep_fit:
            self.fit_mode = None
        if abs(zoom - self.zoom) < 1e-4:
            self.zoomChanged.emit(self.zoom)
            return
        anchor = anchor if anchor is not None else QPointF(self.viewport().width() / 2, self.viewport().height() / 2)
        ref = self._doc_point(anchor)
        self.zoom = zoom
        self._zooming_until = time.monotonic() + 0.15
        self._relayout()
        if ref is not None:
            i, fx, fy = ref
            r = self._rects[i]
            target = QPointF(r.x() + fx * r.width(), r.y() + fy * r.height())
            vw = self.viewport().width()
            self.horizontalScrollBar().setValue(int(target.x() + max(self._content_w, vw) / 2 - anchor.x()))
            self.verticalScrollBar().setValue(int(target.y() - anchor.y()))
        self.viewport().update()
        self._schedule_render(delay=160)
        self.zoomChanged.emit(self.zoom)

    def set_fit(self, mode: str | None):
        self.fit_mode = mode
        if mode:
            cur = self._current
            self.set_zoom(self.fit_zoom(mode), keep_fit=True)
            self.go_to(cur, smooth=False)

    def zoom_step(self, direction: int, anchor: QPointF | None = None):
        z = self.zoom
        if direction > 0:
            nxt = next((s for s in ZOOM_STEPS if s > z + 1e-3), MAX_ZOOM)
        else:
            nxt = next((s for s in reversed(ZOOM_STEPS) if s < z - 1e-3), MIN_ZOOM)
        self.set_zoom(nxt, anchor)

    def set_layout_mode(self, mode: str):
        if mode == self.layout_mode:
            return
        cur = self._current
        self.layout_mode = mode
        self._relayout()
        if self.fit_mode:
            self.zoom = self.fit_zoom(self.fit_mode)
            self._relayout()
            self.zoomChanged.emit(self.zoom)
        self.go_to(cur)

    def set_tone(self, tone: str):
        if tone != self.tone:
            self.tone = tone
            self._cache.clear()
            self._cache_bytes = 0
            self._fallback.clear()
            self.viewport().update()
            self._schedule_render()

    # ================= 坐标换算 =================
    def _doc_point(self, vp: QPointF):
        """视口坐标 → (页码, 页内相对位置 fx, fy)，用于缩放时保持锚点。"""
        hit = self.page_at(vp, nearest=True)
        if not hit:
            return None
        i = hit[0]
        r = self.page_rect(i)
        return i, (vp.x() - r.x()) / max(1, r.width()), (vp.y() - r.y()) / max(1, r.height())

    def page_at(self, vp: QPointF, nearest: bool = False):
        """视口坐标 → (页码, 显示坐标 x_pt, y_pt)。nearest=True 时取最近的页面并夹到页面范围内。"""
        best, best_d = None, 1e18
        for i in self.visible_pages() or range(len(self._rects)):
            r = self.page_rect(i)
            if r.contains(vp):
                return i, (vp.x() - r.x()) / self.scale, (vp.y() - r.y()) / self.scale
            if nearest:
                dx = max(r.left() - vp.x(), 0, vp.x() - r.right())
                dy = max(r.top() - vp.y(), 0, vp.y() - r.bottom())
                d = dx * dx + dy * dy
                if d < best_d:
                    best, best_d = i, d
        if nearest and best is not None:
            r = self.page_rect(best)
            x = min(max(vp.x(), r.left()), r.right())
            y = min(max(vp.y(), r.top()), r.bottom())
            return best, (x - r.x()) / self.scale, (y - r.y()) / self.scale
        return None

    def _matrices(self, i: int):
        key = (i, self.doc.epoch)
        m = self._mats.get(key)
        if m is None:
            m = self.doc.matrices(i)
            self._mats[key] = m
        return m

    def unrot(self, i: int, x: float, y: float) -> tuple[float, float]:
        p = pymupdf.Point(x, y) * self._matrices(i)[1]
        return p.x, p.y

    def disp(self, i: int, x: float, y: float) -> tuple[float, float]:
        p = pymupdf.Point(x, y) * self._matrices(i)[0]
        return p.x, p.y

    def unrot_to_view(self, i: int, x: float, y: float) -> QPointF:
        dx, dy = self.disp(i, x, y)
        r = self.page_rect(i)
        return QPointF(r.x() + dx * self.scale, r.y() + dy * self.scale)

    def unrot_rect_to_view(self, i: int, rect) -> QRectF:
        x0, y0, x1, y1 = rect
        a = self.unrot_to_view(i, x0, y0)
        b = self.unrot_to_view(i, x1, y1)
        return QRectF(a, b).normalized()

    def view_to_unrot(self, i: int, vp: QPointF) -> tuple[float, float]:
        r = self.page_rect(i)
        return self.unrot(i, (vp.x() - r.x()) / self.scale, (vp.y() - r.y()) / self.scale)

    # ================= 导航 =================
    @property
    def current_page(self) -> int:
        return self._current

    def go_to(self, i: int, y_pt: float | None = None, smooth: bool = False, x_pt: float | None = None):
        n = self.doc.page_count
        if not n:
            return
        i = max(0, min(n - 1, i))
        if self.layout_mode == "present":
            self.present_page = i
            self._relayout()
            self._set_current(i)
            self.viewport().update()
            self._schedule_render()
            return
        r = self._rects[i]
        top = r.y() - self.MARGIN / 2 if y_pt is None else r.y() + y_pt * self.scale - 40
        self.verticalScrollBar().setValue(int(top))
        if x_pt is not None:
            vw = self.viewport().width()
            x = r.x() + x_pt * self.scale + max(self._content_w, vw) / 2
            if not (0 <= x - self.horizontalScrollBar().value() <= vw):
                self.horizontalScrollBar().setValue(int(x - vw / 2))
        self._set_current(i)

    def next_page(self):
        step = 2 if self.layout_mode == "double" else 1
        self.go_to(self._current + step)

    def prev_page(self):
        step = 2 if self.layout_mode == "double" else 1
        self.go_to(self._current - step)

    def ensure_visible(self, i: int, rect_unrot, margin: int = 80):
        """让页面上的某块区域可见（朗读、搜索跳转用）。"""
        if self.layout_mode == "present":
            if i != self.present_page:
                self.go_to(i)
            return
        vr = self.unrot_rect_to_view(i, rect_unrot)
        vh, vw = self.viewport().height(), self.viewport().width()
        vs, hs = self.verticalScrollBar(), self.horizontalScrollBar()
        if vr.top() < margin or vr.bottom() > vh - margin:
            vs.setValue(int(vs.value() + vr.top() - vh * 0.3))
        if vr.left() < 0 or vr.right() > vw:
            hs.setValue(int(hs.value() + vr.center().x() - vw / 2))

    def _set_current(self, i: int):
        if i != self._current:
            self._current = i
            self.currentPageChanged.emit(i)

    def _on_scroll(self):
        if self.layout_mode != "present":
            vh = self.viewport().height()
            probe = vh * 0.35
            o = self._origin()
            cur = self._current
            for i in self.visible_pages():
                r = self._rects[i].translated(o)
                if r.top() <= probe <= r.bottom() + self.GAP:
                    cur = i
                    break
            else:
                vis = self.visible_pages()
                if vis:
                    cur = vis[0]
            self._set_current(cur)
        self.viewport().update()
        self._schedule_render()

    def position_state(self) -> dict:
        r = self._rects[self._current] if self._rects else QRectF()
        frac = 0.0
        if not r.isNull():
            frac = (self.verticalScrollBar().value() - r.y()) / max(1.0, r.height())
        return {"page": self._current, "frac": round(frac, 4), "zoom": round(self.zoom, 4),
                "fit": self.fit_mode, "layout": self.layout_mode}

    def restore_position(self, st: dict):
        layout = st.get("layout")
        if layout in ("single", "double"):
            self.layout_mode = layout
        fit = st.get("fit")
        if fit in ("width", "page"):
            self.fit_mode = fit
            self.zoom = self.fit_zoom(fit)
        elif st.get("zoom"):
            self.fit_mode = None
            self.zoom = float(st["zoom"])
        self._relayout()
        i = int(st.get("page", 0))
        if 0 <= i < self.doc.page_count:
            r = self._rects[i]
            self.verticalScrollBar().setValue(int(r.y() + float(st.get("frac", 0)) * r.height()))
            self._set_current(i)
        self.zoomChanged.emit(self.zoom)

    # ================= 文档变化 =================
    def _on_pages_changed(self, pages: list[int]):
        for i in pages:
            self._fallback.pop(i, None)
        self.viewport().update()
        # 修改过的页面立即同步渲染，避免闪烁
        for i in pages:
            if i in self.visible_pages():
                self._render_now(i)
        self._schedule_render()

    def _on_structure_changed(self):
        self._cache.clear()
        self._cache_bytes = 0
        self._fallback.clear()
        self._mats.clear()
        self.search_hits = {}
        self.search_current = None
        self.selection = None
        cur = min(self._current, self.doc.page_count - 1)
        self.present_page = min(self.present_page, max(0, self.doc.page_count - 1))
        self._relayout()
        if self.fit_mode:
            self.zoom = self.fit_zoom(self.fit_mode)
            self._relayout()
        self._current = -1
        self._set_current(max(0, cur))
        self.viewport().update()
        self._schedule_render()

    # ================= 渲染 =================
    def _dpr(self) -> float:
        return self.devicePixelRatioF()

    def _needed(self, extra: bool = False):
        """返回需要渲染的项：(key, page, clip(display pt) 或 None, 渲染比例)。"""
        s = self.scale * self._dpr()
        s_key = round(s, 3)
        vr = QRectF(self.viewport().rect())
        pages = self.visible_pages()
        if extra and pages:
            pages = pages + [p for p in (pages[-1] + 1, pages[0] - 1) if 0 <= p < self.doc.page_count]
        center = vr.center()
        out = []
        for i in pages:
            pr = self.page_rect(i)
            w, h = self.doc.page_size(i)
            rev = (self.doc.revision(i), self.doc.epoch)
            if w * s * h * s <= TILE_THRESHOLD:
                key = (i, s_key, None, rev, self.tone)
                if key not in self._cache:
                    d = abs(pr.center().y() - center.y()) + (1e6 if i not in self.visible_pages() else 0)
                    out.append((d, key, i, None, s))
                continue
            # 分块：只渲染可见区域
            vis = pr.intersected(vr.adjusted(-200, -200, 200, 200))
            if vis.isEmpty():
                continue
            dpr = self._dpr()
            x0 = (vis.left() - pr.left()) * dpr
            y0 = (vis.top() - pr.top()) * dpr
            x1 = (vis.right() - pr.left()) * dpr
            y1 = (vis.bottom() - pr.top()) * dpr
            for ty in range(int(y0 // TILE), int(y1 // TILE) + 1):
                for tx in range(int(x0 // TILE), int(x1 // TILE) + 1):
                    key = (i, s_key, (tx, ty), rev, self.tone)
                    if key in self._cache:
                        continue
                    clip = pymupdf.Rect(tx * TILE / s, ty * TILE / s, (tx + 1) * TILE / s, (ty + 1) * TILE / s)
                    clip = clip & pymupdf.Rect(0, 0, w, h)
                    if clip.is_empty:
                        continue
                    tc = QPointF(pr.left() + (tx + 0.5) * TILE / dpr, pr.top() + (ty + 0.5) * TILE / dpr)
                    d = math.hypot(tc.x() - center.x(), tc.y() - center.y())
                    out.append((d, key, i, clip, s))
        out.sort(key=lambda t: t[0])
        return [t[1:] for t in out]

    def _schedule_render(self, delay: int = 0):
        if not self._render_timer.isActive() or delay:
            self._render_timer.start(delay)

    def _render_next(self):
        if self.doc.closed:
            return
        if time.monotonic() < self._zooming_until:
            self._schedule_render(60)
            return
        items = self._needed()
        prefetch = False
        if not items:
            items = self._needed(extra=True)
            prefetch = True
        if not items:
            return
        key, i, clip, s = items[0]
        self._render_item(key, i, clip, s)
        if not prefetch:
            self.viewport().update()
        self._schedule_render(0 if not prefetch else 30)

    def _render_item(self, key, i, clip, s):
        try:
            pix = self.doc.render(i, s, clip=clip)
            img = pix_to_qimage(pix, self.tone)
        except Exception:
            img = QImage(8, 8, QImage.Format_RGB888)
            img.fill(QColor("white"))
        self._cache[key] = img
        self._cache_bytes += img.sizeInBytes()
        if clip is None:
            self._fallback[i] = (s, key[3], img)
        while self._cache_bytes > CACHE_BYTES and len(self._cache) > 4:
            _, old = self._cache.popitem(last=False)
            self._cache_bytes -= old.sizeInBytes()

    def _render_now(self, i: int):
        for key, pi, clip, s in self._needed():
            if pi == i:
                self._render_item(key, pi, clip, s)
        self.viewport().update()

    # ================= 绘制 =================
    def paintEvent(self, e):
        p = QPainter(self.viewport())
        canvas = QColor(0, 0, 0) if self.presentation else theme.qc("canvas")
        p.fillRect(self.viewport().rect(), canvas)
        s = self.scale
        sd = s * self._dpr()
        s_key = round(sd, 3)
        shadow = parse_color(theme.c("page_shadow"))
        for i in self.visible_pages():
            r = self.page_rect(i)
            if not self.presentation:
                for k, a in ((6, 0.18), (3, 0.35), (1, 0.6)):
                    c = QColor(shadow)
                    c.setAlphaF(shadow.alphaF() * a)
                    p.setPen(Qt.NoPen)
                    p.setBrush(c)
                    p.drawRoundedRect(r.adjusted(-k, -k + 2, k, k + 2), k + 2, k + 2)
            p.fillRect(r, QColor("#202124") if self.tone == "night" else QColor("#F7EFDE") if self.tone == "sepia" else QColor("white"))
            rev = (self.doc.revision(i), self.doc.epoch)
            full = self._cache.get((i, s_key, None, rev, self.tone))
            w, h = self.doc.page_size(i)
            if full is not None:
                self._cache.move_to_end((i, s_key, None, rev, self.tone))
                p.drawImage(r, full)
            else:
                fb = self._fallback.get(i)
                if fb is not None:
                    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    p.drawImage(r, fb[2])
                    p.setRenderHint(QPainter.SmoothPixmapTransform, False)
                if w * sd * h * sd > TILE_THRESHOLD:
                    dpr = self._dpr()
                    for key in list(self._cache.keys()):
                        if key[0] == i and key[1] == s_key and key[2] is not None and key[3] == rev and key[4] == self.tone:
                            tx, ty = key[2]
                            img = self._cache[key]
                            tr = QRectF(r.left() + tx * TILE / dpr, r.top() + ty * TILE / dpr,
                                        img.width() / dpr, img.height() / dpr)
                            p.drawImage(tr, img)
            self._paint_overlays(p, i)
        if self.tool is not None:
            p.setRenderHint(QPainter.Antialiasing, True)
            self.tool.paint(p)
        p.end()

    def _paint_overlays(self, p: QPainter, i: int):
        p.setPen(Qt.NoPen)
        hits = self.search_hits.get(i)
        if hits:
            p.setBrush(theme.qc("search_hit"))
            for k, rect in enumerate(hits):
                if self.search_current == (i, k):
                    p.setBrush(theme.qc("search_current"))
                    p.drawRect(self.unrot_rect_to_view(i, rect))
                    p.setBrush(theme.qc("search_hit"))
                else:
                    p.drawRect(self.unrot_rect_to_view(i, rect))
        if self.read_highlight and self.read_highlight[0] == i:
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setBrush(theme.qc("read_hl"))
            for rect in self.read_highlight[1]:
                p.drawRoundedRect(self.unrot_rect_to_view(i, rect).adjusted(-2, -1, 2, 1), 3, 3)
            under = QColor(theme.qc("accent"))
            p.setPen(QPen(under, 2))
            for rect in self.read_highlight[1]:
                vr = self.unrot_rect_to_view(i, rect)
                p.drawLine(QPointF(vr.left(), vr.bottom() + 1), QPointF(vr.right(), vr.bottom() + 1))
            p.setPen(Qt.NoPen)
            p.setRenderHint(QPainter.Antialiasing, False)
        sel = self.selection_rects(i)
        if sel:
            p.setBrush(theme.qc("selection"))
            for rect in sel:
                p.drawRect(self.unrot_rect_to_view(i, rect))
        if self.flash and self.flash[0] == i:
            age = time.monotonic() - self.flash[2]
            if age < 1.2:
                c = QColor(theme.qc("accent"))
                c.setAlphaF(max(0.0, 0.9 * (1 - age / 1.2)))
                p.setPen(QPen(c, 3))
                p.setBrush(Qt.NoBrush)
                p.setRenderHint(QPainter.Antialiasing, True)
                p.drawRoundedRect(self.unrot_rect_to_view(i, self.flash[1]).adjusted(-4, -4, 4, 4), 4, 4)
                p.setRenderHint(QPainter.Antialiasing, False)
                QTimer.singleShot(40, self.viewport().update)
            else:
                self.flash = None

    def flash_rect(self, i: int, rect):
        self.flash = (i, tuple(rect), time.monotonic())
        self.viewport().update()

    # ================= 文字选择 =================
    def selection_rects(self, i: int) -> list:
        if not self.selection:
            return []
        pa, ia, pb, ib = self.selection
        if not (pa <= i <= pb):
            return []
        pt = self.doc.text(i)
        a = ia if i == pa else 0
        b = ib if i == pb else len(pt)
        return pt.rects_for_range(a, b)

    def set_selection(self, sel):
        if sel is not None:
            pa, ia, pb, ib = sel
            if (pb, ib) < (pa, ia):
                sel = (pb, ib, pa, ia)
            if sel[0] == sel[2] and sel[1] == sel[3]:
                sel = None
        if sel != self.selection:
            self.selection = sel
            self.viewport().update()
            self.selectionChanged.emit()

    def selected_text(self) -> str:
        if not self.selection:
            return ""
        pa, ia, pb, ib = self.selection
        parts = []
        for i in range(pa, pb + 1):
            pt = self.doc.text(i)
            a = ia if i == pa else 0
            b = ib if i == pb else len(pt)
            parts.append(pt.range_text(a, b))
        return "\n".join(x for x in parts if x)

    def copy_selection(self):
        t = self.selected_text()
        if t:
            QApplication.clipboard().setText(t)
            return True
        return False

    # ================= 事件 =================
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.fit_mode:
            cur = self._current
            frac = self.position_state()["frac"]
            self.zoom = self.fit_zoom(self.fit_mode)
            self._relayout()
            if self.layout_mode != "present" and self._rects:
                r = self._rects[cur]
                self.verticalScrollBar().setValue(int(r.y() + frac * r.height()))
            self.zoomChanged.emit(self.zoom)
        else:
            self._update_scrollbars()
        self._schedule_render(50)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            dy = e.angleDelta().y()
            if dy:
                factor = 1.0 + max(-0.5, min(0.5, dy / 1200.0))
                self.set_zoom(self.zoom * factor, e.position())
            return
        if self.layout_mode == "present":
            dy = e.angleDelta().y()
            if dy < 0:
                self.next_page()
            elif dy > 0:
                self.prev_page()
            return
        super().wheelEvent(e)

    def _hit(self, e, nearest=False):
        return self.page_at(e.position(), nearest)

    def mousePressEvent(self, e):
        self.setFocus()
        if e.button() == Qt.MiddleButton or (e.button() == Qt.LeftButton and self._space_down):
            self._panning = e.position().toPoint()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            return
        if e.button() == Qt.RightButton:
            return
        if self.tool:
            self.tool.press(e, self._hit(e))

    def mouseMoveEvent(self, e):
        if self._panning is not None:
            d = e.position().toPoint() - self._panning
            self._panning = e.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - d.y())
            return
        if self.tool:
            self.tool.move(e, self._hit(e))

    def mouseReleaseEvent(self, e):
        if self._panning is not None:
            self._panning = None
            self.viewport().setCursor(Qt.OpenHandCursor if self._space_down else (self.tool.cursor() if self.tool else Qt.ArrowCursor))
            return
        if e.button() == Qt.RightButton:
            self.contextMenuAt.emit(e.globalPosition().toPoint(), self._hit(e))
            return
        if self.tool:
            self.tool.release(e, self._hit(e))

    def mouseDoubleClickEvent(self, e):
        if self.tool and e.button() == Qt.LeftButton:
            self.tool.double_click(e, self._hit(e))

    def leaveEvent(self, e):
        if self.tool:
            self.tool.leave()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Space and not e.isAutoRepeat() and self.layout_mode != "present":
            self._space_down = True
            self.viewport().setCursor(Qt.OpenHandCursor)
            return
        if self.tool and self.tool.key(e):
            return
        if e.matches(QKeySequence.Copy):
            self.copy_selection()
            return
        if k == Qt.Key_Escape and self.selection:
            self.set_selection(None)
            return
        if self.layout_mode == "present":
            if k in (Qt.Key_Right, Qt.Key_Down, Qt.Key_PageDown, Qt.Key_Space, Qt.Key_Return, Qt.Key_N):
                self.next_page()
                return
            if k in (Qt.Key_Left, Qt.Key_Up, Qt.Key_PageUp, Qt.Key_Backspace, Qt.Key_P):
                self.prev_page()
                return
        if k == Qt.Key_PageDown or (k == Qt.Key_Right and self.horizontalScrollBar().maximum() == 0):
            if self.fit_mode == "page":
                self.next_page()
            else:
                self.verticalScrollBar().triggerAction(self.verticalScrollBar().SliderPageStepAdd)
            return
        if k == Qt.Key_PageUp or (k == Qt.Key_Left and self.horizontalScrollBar().maximum() == 0):
            if self.fit_mode == "page":
                self.prev_page()
            else:
                self.verticalScrollBar().triggerAction(self.verticalScrollBar().SliderPageStepSub)
            return
        if k == Qt.Key_Home and e.modifiers() & Qt.ControlModifier:
            self.go_to(0)
            return
        if k == Qt.Key_End and e.modifiers() & Qt.ControlModifier:
            self.go_to(self.doc.page_count - 1)
            return
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Space and not e.isAutoRepeat():
            self._space_down = False
            self.viewport().setCursor(self.tool.cursor() if self.tool else Qt.ArrowCursor)
            return
        super().keyReleaseEvent(e)

    # ================= 工具 =================
    def set_tool(self, tool):
        if self.tool is not None:
            self.tool.deactivate()
        self.tool = tool
        if tool is not None:
            tool.activate()
            self.viewport().setCursor(tool.cursor())
        self.viewport().update()

    def autoscroll(self, vp: QPointF):
        """拖动到边缘时自动滚动。"""
        vh = self.viewport().height()
        edge = 30
        vs = self.verticalScrollBar()
        if vp.y() < edge:
            vs.setValue(vs.value() - int((edge - vp.y()) / 2) - 2)
        elif vp.y() > vh - edge:
            vs.setValue(vs.value() + int((vp.y() - vh + edge) / 2) + 2)


def smooth_path(points: list[QPointF]) -> QPainterPath:
    path = QPainterPath()
    if not points:
        return path
    path.moveTo(points[0])
    if len(points) < 3:
        for pt in points[1:]:
            path.lineTo(pt)
        return path
    for k in range(1, len(points) - 1):
        mid = (points[k] + points[k + 1]) / 2
        path.quadTo(points[k], mid)
    path.lineTo(points[-1])
    return path
