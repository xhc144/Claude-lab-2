"""页面上的交互工具：选择、抓手、高亮、画笔、形状、文本框、便签、橡皮擦、激光笔、点读。"""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QCursor, QDesktopServices, QFont, QFontMetricsF, QPainter, QPen, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QPlainTextEdit

from ..theme import theme
from .page_view import PageView, smooth_path


def rgb(color: str) -> tuple[float, float, float]:
    c = QColor(color)
    return (c.redF(), c.greenF(), c.blueF())


def _simplify(points: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
    """Ramer–Douglas–Peucker 简化，减小墨迹数据量。"""
    if len(points) < 3:
        return points
    (x0, y0), (x1, y1) = points[0], points[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1e-9
    idx, dmax = 0, 0.0
    for k in range(1, len(points) - 1):
        px, py = points[k]
        d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / norm if (dx or dy) else math.hypot(px - x0, py - y0)
        if d > dmax:
            idx, dmax = k, d
    if dmax > eps:
        left = _simplify(points[:idx + 1], eps)
        right = _simplify(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]


class Tool:
    name = ""

    def __init__(self, view: PageView, opts: dict | None = None):
        self.view = view
        self.opts = opts if opts is not None else {}

    # 生命周期
    def activate(self): ...
    def deactivate(self): ...

    def cursor(self):
        return Qt.ArrowCursor

    # 事件
    def press(self, e, hit): ...
    def move(self, e, hit): ...
    def release(self, e, hit): ...
    def double_click(self, e, hit): ...
    def leave(self): ...

    def key(self, e) -> bool:
        return False

    def paint(self, p: QPainter): ...

    @property
    def doc(self):
        return self.view.doc

    def editable(self) -> bool:
        return self.doc.editable


# ---------------------------------------------------------------- 选择
class SelectTool(Tool):
    name = "select"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._anchor = None
        self._press_pos = None
        self._dragging = False
        self._link = None

    def cursor(self):
        return Qt.ArrowCursor

    def _link_at(self, hit):
        if not hit:
            return None
        i, x, y = hit
        for ln in self.doc.links(i):
            r = ln.get("from")
            if r is not None and r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1:
                return ln
        return None

    def _caret(self, hit):
        i, x, y = hit
        ux, uy = self.view.unrot(i, x, y)
        pt = self.doc.text(i)
        c = pt.hit_caret(ux, uy)
        return (i, c) if c is not None else None

    def press(self, e, hit):
        if e.button() != Qt.LeftButton:
            return
        self._press_pos = e.position()
        self._dragging = False
        self._link = self._link_at(hit)
        if hit:
            self._anchor = self._caret(hit)
            if e.modifiers() & Qt.ShiftModifier and self.view.selection and self._anchor:
                pa, ia, _, _ = self.view.selection
                self.view.set_selection((pa, ia, *self._anchor))
                self._anchor = (pa, ia)
                self._dragging = True
                return
        else:
            self._anchor = None

    def move(self, e, hit):
        if self._press_pos is None:
            # 悬停：根据位置切换光标
            cur = Qt.ArrowCursor
            if hit:
                if self._link_at(hit):
                    cur = Qt.PointingHandCursor
                else:
                    i, x, y = hit
                    ux, uy = self.view.unrot(i, x, y)
                    if self.doc.text(i).hit(ux, uy, max_dist=3) is not None:
                        cur = Qt.IBeamCursor
            self.view.viewport().setCursor(cur)
            return
        if (e.position() - self._press_pos).manhattanLength() > 4:
            self._dragging = True
        if self._dragging and self._anchor:
            self.view.autoscroll(e.position())
            h = self.view.page_at(e.position(), nearest=True)
            if h:
                c = self._caret(h)
                if c:
                    self.view.set_selection((*self._anchor, *c))

    def release(self, e, hit):
        if self._press_pos is None:
            return
        if not self._dragging:
            if self._link:
                self._follow(self._link)
            self.view.set_selection(None)
        self._press_pos = None
        self._dragging = False

    def double_click(self, e, hit):
        if not hit:
            return
        i, x, y = hit
        ux, uy = self.view.unrot(i, x, y)
        pt = self.doc.text(i)
        k = pt.hit(ux, uy, max_dist=6)
        if k is not None:
            a, b = pt.word_at(k)
            self.view.set_selection((i, a, i, b))
            self._press_pos = None

    def _follow(self, ln):
        kind = ln.get("kind")
        if kind in (1, 4) and ln.get("page", -1) >= 0:  # LINK_GOTO / LINK_NAMED
            to = ln.get("to")
            y = None
            if to is not None:
                i = ln["page"]
                _, yy = self.view.disp(i, to.x, to.y) if hasattr(to, "x") else (0, None)
                y = yy
            self.view.go_to(ln["page"], y_pt=y)
        elif ln.get("uri"):
            QDesktopServices.openUrl(QUrl(ln["uri"]))

    def key(self, e):
        if e.key() == Qt.Key_A and e.modifiers() & Qt.ControlModifier:
            i = self.view.current_page
            self.view.set_selection((i, 0, i, len(self.doc.text(i))))
            return True
        return False


# ---------------------------------------------------------------- 抓手
class HandTool(Tool):
    name = "hand"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._last = None

    def cursor(self):
        return Qt.OpenHandCursor

    def press(self, e, hit):
        self._last = e.position()
        self.view.viewport().setCursor(Qt.ClosedHandCursor)

    def move(self, e, hit):
        if self._last is None:
            return
        d = e.position() - self._last
        self._last = e.position()
        hs, vs = self.view.horizontalScrollBar(), self.view.verticalScrollBar()
        hs.setValue(int(hs.value() - d.x()))
        vs.setValue(int(vs.value() - d.y()))

    def release(self, e, hit):
        self._last = None
        self.view.viewport().setCursor(Qt.OpenHandCursor)


# ---------------------------------------------------------------- 高亮 / 下划线 / 删除线
class HighlightTool(Tool):
    name = "highlight"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._page = None
        self._a = None
        self._b = None
        self._free: list[QPointF] | None = None  # 没有文字时退化为荧光笔手绘

    def cursor(self):
        return Qt.IBeamCursor

    @property
    def color(self):
        return self.opts.get("highlight/color", "#FFD43B")

    @property
    def kind(self):
        return self.opts.get("highlight/kind", "highlight")

    def press(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        i, x, y = hit
        ux, uy = self.view.unrot(i, x, y)
        pt = self.doc.text(i)
        if pt.hit(ux, uy, max_dist=12) is None:
            self._page = i
            self._free = [QPointF(x, y)]
            return
        self._page = i
        self._a = self._b = pt.hit_caret(ux, uy)

    def move(self, e, hit):
        if self._page is None:
            return
        h = self.view.page_at(e.position(), nearest=True)
        if not h or h[0] != self._page:
            return
        i, x, y = h
        if self._free is not None:
            self._free.append(QPointF(x, y))
        else:
            ux, uy = self.view.unrot(i, x, y)
            c = self.doc.text(i).hit_caret(ux, uy)
            if c is not None:
                self._b = c
        self.view.viewport().update()

    def release(self, e, hit):
        if self._page is None:
            return
        i = self._page
        color = rgb(self.color)
        if self._free is not None:
            if len(self._free) > 1:
                pts = [self.view.unrot(i, p.x(), p.y()) for p in self._free]
                self.doc.add_ink(i, [_simplify(pts, 0.4)], color, 12, opacity=0.4)
        elif self._a is not None and self._b is not None and self._a != self._b:
            a, b = sorted((self._a, self._b))
            rects = self.doc.text(i).rects_for_range(a, b)
            if rects:
                self.doc.add_markup(i, self.kind, rects, color)
        self._page = self._a = self._b = self._free = None
        self.view.viewport().update()

    def paint(self, p: QPainter):
        if self._page is None:
            return
        i = self._page
        c = QColor(self.color)
        if self._free is not None:
            c.setAlphaF(0.4)
            pen = QPen(c, 12 * self.view.scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            r = self.view.page_rect(i)
            pts = [QPointF(r.x() + q.x() * self.view.scale, r.y() + q.y() * self.view.scale) for q in self._free]
            p.drawPath(smooth_path(pts))
            return
        if self._a is None or self._b is None:
            return
        a, b = sorted((self._a, self._b))
        rects = self.doc.text(i).rects_for_range(a, b)
        c.setAlphaF(0.45)
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        for rect in rects:
            vr = self.view.unrot_rect_to_view(i, rect)
            if self.kind == "highlight":
                p.drawRect(vr)
            elif self.kind == "underline":
                p.drawRect(QRectF(vr.left(), vr.bottom() - 2, vr.width(), 2))
            elif self.kind == "strikeout":
                p.drawRect(QRectF(vr.left(), vr.center().y() - 1, vr.width(), 2))
            else:
                p.drawRect(QRectF(vr.left(), vr.bottom() - 3, vr.width(), 3))


# ---------------------------------------------------------------- 画笔
class InkTool(Tool):
    name = "pen"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._page = None
        self._pts: list[QPointF] = []

    def cursor(self):
        return pen_cursor(self.opts.get("pen/color", "#E5484D"))

    def press(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        i, x, y = hit
        self._page = i
        self._pts = [QPointF(x, y)]

    def move(self, e, hit):
        if self._page is None:
            return
        r = self.view.page_rect(self._page)
        s = self.view.scale
        x = min(max(e.position().x(), r.left()), r.right())
        y = min(max(e.position().y(), r.top()), r.bottom())
        q = QPointF((x - r.x()) / s, (y - r.y()) / s)
        if (q - self._pts[-1]).manhattanLength() * s >= 1.5:
            self._pts.append(q)
            self.view.viewport().update()

    def release(self, e, hit):
        if self._page is None:
            return
        i = self._page
        pts = self._pts
        if len(pts) == 1:
            pts = [pts[0], pts[0] + QPointF(0.3, 0.3)]
        unrot = [self.view.unrot(i, q.x(), q.y()) for q in pts]
        width = float(self.opts.get("pen/width", 2.0))
        self.doc.add_ink(i, [_simplify(unrot, 0.25)], rgb(self.opts.get("pen/color", "#E5484D")), width)
        self._page = None
        self._pts = []

    def paint(self, p: QPainter):
        if self._page is None:
            return
        r = self.view.page_rect(self._page)
        s = self.view.scale
        width = float(self.opts.get("pen/width", 2.0))
        pen = QPen(QColor(self.opts.get("pen/color", "#E5484D")), max(1.0, width * s), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        pts = [QPointF(r.x() + q.x() * s, r.y() + q.y() * s) for q in self._pts]
        p.drawPath(smooth_path(pts))


# ---------------------------------------------------------------- 形状
class ShapeTool(Tool):
    name = "shape"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._page = None
        self._p0 = self._p1 = None

    def cursor(self):
        return Qt.CrossCursor

    def press(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        i, x, y = hit
        self._page = i
        self._p0 = self._p1 = QPointF(x, y)

    def _constrain(self, p0: QPointF, p1: QPointF, shift: bool) -> QPointF:
        if not shift:
            return p1
        d = p1 - p0
        kind = self.opts.get("shape/kind", "rect")
        if kind in ("rect", "ellipse"):
            m = max(abs(d.x()), abs(d.y()))
            return QPointF(p0.x() + math.copysign(m, d.x() or 1), p0.y() + math.copysign(m, d.y() or 1))
        ang = round(math.atan2(d.y(), d.x()) / (math.pi / 4)) * (math.pi / 4)
        ln = math.hypot(d.x(), d.y())
        return QPointF(p0.x() + ln * math.cos(ang), p0.y() + ln * math.sin(ang))

    def move(self, e, hit):
        if self._page is None:
            return
        h = self.view.page_at(e.position(), nearest=True)
        if h and h[0] == self._page:
            self._p1 = self._constrain(self._p0, QPointF(h[1], h[2]), bool(e.modifiers() & Qt.ShiftModifier))
            self.view.viewport().update()

    def release(self, e, hit):
        if self._page is None:
            return
        i = self._page
        a = self.view.unrot(i, self._p0.x(), self._p0.y())
        b = self.view.unrot(i, self._p1.x(), self._p1.y())
        self.doc.add_shape(i, self.opts.get("shape/kind", "rect"), a, b,
                           rgb(self.opts.get("shape/color", "#E5484D")), float(self.opts.get("shape/width", 2.0)))
        self._page = None
        self.view.viewport().update()

    def paint(self, p: QPainter):
        if self._page is None:
            return
        r = self.view.page_rect(self._page)
        s = self.view.scale
        a = QPointF(r.x() + self._p0.x() * s, r.y() + self._p0.y() * s)
        b = QPointF(r.x() + self._p1.x() * s, r.y() + self._p1.y() * s)
        pen = QPen(QColor(self.opts.get("shape/color", "#E5484D")), max(1.0, float(self.opts.get("shape/width", 2)) * s))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        kind = self.opts.get("shape/kind", "rect")
        if kind == "rect":
            p.drawRect(QRectF(a, b).normalized())
        elif kind == "ellipse":
            p.drawEllipse(QRectF(a, b).normalized())
        else:
            p.drawLine(a, b)
            if kind == "arrow":
                ang = math.atan2(b.y() - a.y(), b.x() - a.x())
                L = max(8.0, pen.widthF() * 4)
                for d in (math.radians(150), -math.radians(150)):
                    p.drawLine(b, QPointF(b.x() + L * math.cos(ang + d), b.y() + L * math.sin(ang + d)))


# ---------------------------------------------------------------- 文本框
class _InlineEditor(QPlainTextEdit):
    def __init__(self, tool: "TextTool", parent):
        super().__init__(parent)
        self.tool = tool
        self.setFrameShape(QPlainTextEdit.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.textChanged.connect(self._grow)

    def _grow(self):
        fm = QFontMetricsF(self.font())
        lines = self.toPlainText().split("\n") or [""]
        w = max(fm.horizontalAdvance(l) for l in lines) + fm.averageCharWidth() * 2 + 12
        h = fm.lineSpacing() * len(lines) + 12
        self.resize(int(max(60, w)), int(h))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.tool.cancel()
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and e.modifiers() & Qt.ControlModifier:
            self.tool.commit()
            return
        super().keyPressEvent(e)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        QTimer.singleShot(0, self.tool.commit)


class TextTool(Tool):
    name = "text"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._editor: _InlineEditor | None = None
        self._page = None
        self._pos = None

    def cursor(self):
        return Qt.IBeamCursor

    def press(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        if self._editor:
            self.commit()
            return
        i, x, y = hit
        self._page, self._pos = i, QPointF(x, y)
        ed = _InlineEditor(self, self.view.viewport())
        f = QFont()
        f.setPixelSize(max(6, int(float(self.opts.get("text/size", 14)) * self.view.scale)))
        ed.setFont(f)
        color = self.opts.get("text/color", "#E5484D")
        ed.setStyleSheet(f"QPlainTextEdit {{ background: rgba(255,255,255,0.85); color: {color};"
                         f" border: 1.5px dashed {theme.c('accent')}; border-radius: 4px; padding: 2px; }}")
        ed.move(int(e.position().x()), int(e.position().y() - f.pixelSize() * 0.8))
        ed._grow()
        ed.show()
        ed.setFocus()
        self._editor = ed

    def commit(self):
        ed = self._editor
        if ed is None:
            return
        self._editor = None
        text = ed.toPlainText().rstrip()
        i = self._page
        if text:
            s = self.view.scale
            r = self.view.page_rect(i)
            x0 = (ed.x() - r.x()) / s
            y0 = (ed.y() - r.y()) / s
            size = float(self.opts.get("text/size", 14))
            fm = QFontMetricsF(ed.font())
            lines = text.split("\n")
            w = max(fm.horizontalAdvance(l) for l in lines) / s * 1.18 + size
            h = size * 1.35 * len(lines) + size * 0.6
            a = self.view.unrot(i, x0, y0)
            b = self.view.unrot(i, x0 + w, y0 + h)
            rect = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
            self.doc.add_freetext(i, rect, text, size, rgb(self.opts.get("text/color", "#E5484D")))
        ed.deleteLater()
        self.view.setFocus()

    def cancel(self):
        if self._editor:
            ed = self._editor
            self._editor = None
            ed.deleteLater()
            self.view.setFocus()

    def deactivate(self):
        self.commit()


# ---------------------------------------------------------------- 便签
class NoteTool(Tool):
    name = "note"

    def cursor(self):
        return Qt.CrossCursor

    def release(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        from .dialogs.note_dialog import NoteDialog

        text = NoteDialog.ask(self.view.window(), "添加便签", "")
        if text:
            i, x, y = hit
            self.doc.add_note(i, self.view.unrot(i, x, y), text, rgb(self.opts.get("note/color", "#F5A524")))


# ---------------------------------------------------------------- 橡皮擦
class EraserTool(Tool):
    name = "eraser"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._pos: QPointF | None = None
        self._down = False
        self._erased = 0

    def cursor(self):
        return Qt.BlankCursor

    @property
    def radius_px(self) -> float:
        return float(self.opts.get("eraser/size", 12))

    def _erase_at(self, vp: QPointF):
        hit = self.view.page_at(vp)
        if not hit:
            return
        i, x, y = hit
        ux, uy = self.view.unrot(i, x, y)
        xrefs = self.doc.annots_at(i, ux, uy, self.radius_px / self.view.scale)
        if xrefs:
            self.doc.delete_annots(i, xrefs, "擦除批注")
            self._erased += 1

    def press(self, e, hit):
        if e.button() != Qt.LeftButton or not self.editable():
            return
        self._down = True
        self._erased = 0
        self.doc.begin_macro("擦除批注")
        self._erase_at(e.position())

    def move(self, e, hit):
        self._pos = e.position()
        if self._down:
            self._erase_at(e.position())
        self.view.viewport().update()

    def release(self, e, hit):
        if self._down:
            self._down = False
            self.doc.end_macro()

    def leave(self):
        self._pos = None
        self.view.viewport().update()

    def deactivate(self):
        if self._down:
            self._down = False
            self.doc.end_macro()

    def paint(self, p: QPainter):
        if self._pos is None:
            return
        r = self.radius_px
        p.setPen(QPen(theme.qc("text2"), 1.2))
        p.setBrush(QColor(255, 255, 255, 90))
        p.drawEllipse(self._pos, r, r)


# ---------------------------------------------------------------- 激光笔
class LaserTool(Tool):
    name = "laser"
    FADE = 0.9  # 轨迹消失时间（秒）

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._pos: QPointF | None = None
        self._strokes: list[list[tuple[QPointF, float]]] = []
        self._down = False
        self._timer = QTimer(view)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def cursor(self):
        return Qt.BlankCursor

    def activate(self):
        self._timer.start()

    def deactivate(self):
        self._timer.stop()
        self._strokes = []
        self._pos = None

    def press(self, e, hit):
        if e.button() == Qt.LeftButton:
            self._down = True
            self._strokes.append([(e.position(), time.monotonic())])

    def move(self, e, hit):
        self._pos = e.position()
        if self._down and self._strokes:
            self._strokes[-1].append((e.position(), time.monotonic()))

    def release(self, e, hit):
        self._down = False

    def leave(self):
        self._pos = None

    def _tick(self):
        now = time.monotonic()
        alive = []
        for st in self._strokes:
            if self._down and st is self._strokes[-1]:
                alive.append(st)
            elif st and now - st[-1][1] < self.FADE:
                alive.append(st)
        self._strokes = alive
        self.view.viewport().update()

    def paint(self, p: QPainter):
        color = QColor(self.opts.get("laser/color", "#FF3B30"))
        now = time.monotonic()
        p.setRenderHint(QPainter.Antialiasing, True)
        for st in self._strokes:
            if len(st) < 2:
                continue
            end_age = 0 if (self._down and st is self._strokes[-1]) else now - st[-1][1]
            fade = max(0.0, 1 - end_age / self.FADE)
            for width, alpha in ((14, 0.18), (7, 0.35), (3, 1.0)):
                c = QColor(color) if width > 3 else QColor(255, 236, 236)  # 外圈发光，内芯偏白
                c.setAlphaF(alpha * fade)
                pen = QPen(c, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                p.drawPath(smooth_path([q for q, _ in st]))
        if self._pos is not None:
            for rad, alpha in ((16, 0.15), (10, 0.3), (6, 0.85)):
                c = QColor(color)
                c.setAlphaF(alpha)
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                p.drawEllipse(self._pos, rad, rad)
            p.setBrush(QColor(255, 255, 255, 230))
            p.drawEllipse(self._pos, 2.2, 2.2)


# ---------------------------------------------------------------- 点读
class ReadTool(Tool):
    name = "read"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._hover = None

    def cursor(self):
        return Qt.PointingHandCursor

    def move(self, e, hit):
        new = None
        if hit:
            i, x, y = hit
            ux, uy = self.view.unrot(i, x, y)
            pt = self.doc.text(i)
            k = pt.hit(ux, uy, max_dist=40)
            if k is not None:
                sents = pt.sentences()
                if sents:
                    s = sents[pt.sentence_index_at(k)]
                    new = (i, s.start, s.end)
        if new != self._hover:
            self._hover = new
            self.view.viewport().update()

    def leave(self):
        self._hover = None
        self.view.viewport().update()

    def release(self, e, hit):
        if e.button() != Qt.LeftButton or not hit:
            return
        i, x, y = hit
        ux, uy = self.view.unrot(i, x, y)
        k = self.doc.text(i).hit(ux, uy)
        self.view.readRequested.emit(i, k if k is not None else 0)

    def paint(self, p: QPainter):
        if not self._hover:
            return
        i, a, b = self._hover
        c = QColor(theme.qc("accent"))
        c.setAlphaF(0.55)
        p.setPen(QPen(c, 1.5, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        for rect in self.doc.text(i).rects_for_range(a, b):
            vr = self.view.unrot_rect_to_view(i, rect)
            p.drawLine(QPointF(vr.left(), vr.bottom() + 1.5), QPointF(vr.right(), vr.bottom() + 1.5))


def pen_cursor(color: str):
    """画笔光标：小圆点。"""
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(255, 255, 255), 1.5))
    p.setBrush(QBrush(QColor(color)))
    p.drawEllipse(QPointF(8, 8), 4, 4)
    p.end()
    return QCursor(pm, 8, 8)


TOOL_CLASSES = {
    "select": SelectTool, "hand": HandTool, "highlight": HighlightTool, "pen": InkTool,
    "shape": ShapeTool, "text": TextTool, "note": NoteTool, "eraser": EraserTool,
    "laser": LaserTool, "read": ReadTool,
}

EDIT_TOOLS = {"highlight", "pen", "shape", "text", "note", "sign", "eraser"}
