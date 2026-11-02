"""画面元素：基本图形、文字，以及数组、表格、树、图、坐标系等组合部件。

坐标约定：矩形、圆、文字默认以 (x, y) 为中心；组合部件的 (x, y) 是整体的中心。
组合部件的子元素用局部坐标，部件整体移动时子元素跟着走。
"""

import math

import skia

from . import text as T
from . import theme as C
from .core import Node, Group, Anim, Track, FadeIn, FadeOut, flatten


def _color(c, o):
    return skia.Color4f(c[0], c[1], c[2], max(0.0, min(1.0, c[3] * o)))


def fill_paint(c, o):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(_color(c, o))
    return p


def stroke_paint(c, o, w, dash=None):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(_color(c, o))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    return p


_BLUR = {}


def glow_paint(c, o, w, sigma=9):
    p = stroke_paint(c, o, w)
    if sigma not in _BLUR:
        _BLUR[sigma] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)
    p.setMaskFilter(_BLUR[sigma])
    return p


# ------------------------------------------------------------------ 基本图形
_SHADOW = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)


class Rect(Node):
    """圆角矩形。shadow > 0 时下面带一层柔和的投影（卡片、板书用）。"""

    def __init__(self, x=0, y=0, w=100, h=60, fill=C.BG3, stroke=C.LINE, sw=2.0, r=10.0, glow=0.0, dash=None,
                 shadow=0.0, **kw):
        super().__init__(x, y, w=float(w), h=float(h), fill=fill, stroke=stroke, sw=float(sw), r=float(r),
                         glow=float(glow), **kw)
        self.dash = dash
        self.shadow = shadow

    def paint(self, cv, t, o):
        w, h, r = self.g("w", t), self.g("h", t), self.g("r", t)
        rect = skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h)
        if self.shadow > 0:
            sp = skia.Paint(AntiAlias=True)
            sp.setColor4f(skia.Color4f(0.02, 0.02, 0.06, min(1.0, 0.55 * self.shadow * o)))
            sp.setMaskFilter(_SHADOW)
            cv.drawRoundRect(skia.Rect.MakeXYWH(-w / 2, -h / 2 + 10, w, h), r, r, sp)
        fill = self.g("fill", t)
        if fill and fill[3] > 0:
            cv.drawRoundRect(rect, r, r, fill_paint(fill, o))
        st, sw = self.g("stroke", t), self.g("sw", t)
        gl = self.g("glow", t)
        if gl > 0.01 and st:
            cv.drawRoundRect(rect, r, r, glow_paint(st, o * gl, sw * 3 + 4))
        if st and st[3] > 0 and sw > 0:
            cv.drawRoundRect(rect, r, r, stroke_paint(st, o, sw, self.dash))

    def bbox(self, t):
        w, h = self.g("w", t), self.g("h", t)
        return (-w / 2, -h / 2, w / 2, h / 2)


class Circle(Node):
    def __init__(self, x=0, y=0, r=24, fill=C.BG3, stroke=C.LINE2, sw=2.5, glow=0.0, dash=None, **kw):
        super().__init__(x, y, r=float(r), fill=fill, stroke=stroke, sw=float(sw), glow=float(glow), **kw)
        self.dash = dash

    def paint(self, cv, t, o):
        r = self.g("r", t)
        fill = self.g("fill", t)
        if fill and fill[3] > 0:
            cv.drawCircle(0, 0, r, fill_paint(fill, o))
        st, sw = self.g("stroke", t), self.g("sw", t)
        gl = self.g("glow", t)
        if gl > 0.01 and st:
            cv.drawCircle(0, 0, r, glow_paint(st, o * gl, sw * 3 + 4))
        if st and st[3] > 0 and sw > 0:
            cv.drawCircle(0, 0, r, stroke_paint(st, o, sw, self.dash))

    def bbox(self, t):
        r = self.g("r", t)
        return (-r, -r, r, r)


class Line(Node):
    """线段 / 箭头 / 弧线。prog 控制画出的比例（0→1 是“生长”），p0 是起点比例（可做“流动”效果）。
    bend ≠ 0 时画成二次贝塞尔弧线，控制点偏离中点 bend × 长度。
    attach(a, b) 后端点跟随两个同一父节点下的元素，并自动缩进 pad。"""

    def __init__(self, x1=0, y1=0, x2=100, y2=0, color=C.LINE2, w=3.0, head=0.0, prog=1.0, p0=0.0,
                 bend=0.0, dash=None, glow=0.0, **kw):
        super().__init__(0, 0, x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2), color=color,
                         w=float(w), head=float(head), prog=float(prog), p0=float(p0), bend=float(bend),
                         glow=float(glow), **kw)
        self.dash = dash
        self.a = self.b = None
        self.pa = self.pb = 0.0

    def attach(self, a, b, pa=None, pb=None):
        self.a, self.b = a, b
        self.pa = pa if pa is not None else _radius(a)
        self.pb = pb if pb is not None else _radius(b)
        return self

    def ends(self, t):
        if self.a is not None:
            x1, y1 = self.a.g("x", t), self.a.g("y", t)
            x2, y2 = self.b.g("x", t), self.b.g("y", t)
        else:
            x1, y1, x2, y2 = self.g("x1", t), self.g("y1", t), self.g("x2", t), self.g("y2", t)
        return x1, y1, x2, y2

    def geometry(self, t):
        x1, y1, x2, y2 = self.ends(t)
        bend = self.g("bend", t)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1.0
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        cx, cy = mx - dy / L * bend * L, my + dx / L * bend * L
        if self.a is not None:
            # 沿着曲线方向缩进
            ux, uy = cx - x1, cy - y1
            l1 = math.hypot(ux, uy) or 1.0
            x1, y1 = x1 + ux / l1 * self.pa, y1 + uy / l1 * self.pa
            vx, vy = cx - x2, cy - y2
            l2 = math.hypot(vx, vy) or 1.0
            x2, y2 = x2 + vx / l2 * self.pb, y2 + vy / l2 * self.pb
            if abs(bend) < 1e-6:
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        return x1, y1, cx, cy, x2, y2

    def point(self, t, u):
        x1, y1, cx, cy, x2, y2 = self.geometry(t)
        a, b, c = (1 - u) ** 2, 2 * u * (1 - u), u * u
        return a * x1 + b * cx + c * x2, a * y1 + b * cy + c * y2

    def paint(self, cv, t, o):
        prog, p0 = self.g("prog", t), self.g("p0", t)
        if prog - p0 <= 0.001:
            return
        x1, y1, cx, cy, x2, y2 = self.geometry(t)
        col, w = self.g("color", t), self.g("w", t)
        path = skia.Path()
        N = 24 if abs(self.g("bend", t)) > 1e-6 else 1
        pts = []
        for k in range(N + 1):
            u = p0 + (prog - p0) * k / N
            a, b, c = (1 - u) ** 2, 2 * u * (1 - u), u * u
            pts.append((a * x1 + b * cx + c * x2, a * y1 + b * cy + c * y2))
        head = self.g("head", t)
        if head > 0 and len(pts) >= 2:
            # 箭头：末端缩短一点，避免线头从箭头里露出来
            ex, ey = pts[-1]
            u = prog
            tx = 2 * (1 - u) * (cx - x1) + 2 * u * (x2 - cx)
            ty = 2 * (1 - u) * (cy - y1) + 2 * u * (y2 - cy)
            tl = math.hypot(tx, ty) or 1.0
            tx, ty = tx / tl, ty / tl
            pts[-1] = (ex - tx * head * 0.6, ey - ty * head * 0.6)
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        gl = self.g("glow", t)
        if gl > 0.01:
            cv.drawPath(path, glow_paint(col, o * gl, w * 3 + 4))
        cv.drawPath(path, stroke_paint(col, o, w, self.dash))
        if head > 0:
            hp = skia.Path()
            nx, ny = -ty, tx
            hp.moveTo(ex, ey)
            hp.lineTo(ex - tx * head + nx * head * 0.5, ey - ty * head + ny * head * 0.5)
            hp.lineTo(ex - tx * head - nx * head * 0.5, ey - ty * head - ny * head * 0.5)
            hp.close()
            cv.drawPath(hp, fill_paint(col, o))


def _radius(n):
    if isinstance(n, Circle):
        return n.g("r", 0) + 2
    if hasattr(n, "radius"):
        return n.radius
    return 0.0


class GradLine(Node):
    """水平渐变细线（页眉下沿、讲解区上沿）。stops: [(位置 0~1, 颜色)]。"""

    def __init__(self, x1, y, x2, stops, w=1.5, **kw):
        super().__init__(x1, y, **kw)
        self.len = x2 - x1
        self.stops = stops
        self.lw = w

    def paint(self, cv, t, o):
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear(
            [(0, 0), (self.len, 0)], [_color(c, o).toColor() for _, c in self.stops], [u for u, _ in self.stops]))
        cv.drawRect(skia.Rect.MakeXYWH(0, -self.lw / 2, self.len, self.lw), p)


class Band(Node):
    """竖直渐变的色带（讲解区背后的暗带）。"""

    def __init__(self, x, y, w, h, top, bottom, **kw):
        super().__init__(x, y, **kw)
        self.w, self.h, self.top, self.bottom = w, h, top, bottom

    def paint(self, cv, t, o):
        p = skia.Paint(AntiAlias=True)
        p.setDither(True)
        p.setShader(skia.GradientShader.MakeLinear(
            [(0, 0), (0, self.h)], [_color(self.top, o).toColor(), _color(self.bottom, o).toColor()], [0.0, 1.0]))
        cv.drawRect(skia.Rect.MakeXYWH(0, 0, self.w, self.h), p)


class Poly(Node):
    def __init__(self, pts, fill=None, stroke=C.LINE2, sw=2.0, closed=True, dash=None, **kw):
        super().__init__(0, 0, pts=tuple(tuple(map(float, p)) for p in pts), fill=fill or (0, 0, 0, 0),
                         stroke=stroke or (0, 0, 0, 0), sw=float(sw), **kw)
        self.closed = closed
        self.dash = dash

    def paint(self, cv, t, o):
        pts = self.g("pts", t)
        if len(pts) < 2:
            return
        path = skia.Path()
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        if self.closed:
            path.close()
        f = self.g("fill", t)
        if f[3] > 0:
            cv.drawPath(path, fill_paint(f, o))
        s = self.g("stroke", t)
        if s[3] > 0:
            cv.drawPath(path, stroke_paint(s, o, self.g("sw", t), self.dash))


class Arc(Node):
    """圆弧（计时环、角度）：从 a0 度开始，扫过 sweep 度。"""

    def __init__(self, x=0, y=0, r=40, a0=-90, sweep=360, color=C.YELLOW, w=6, **kw):
        super().__init__(x, y, r=float(r), a0=float(a0), sweep=float(sweep), color=color, w=float(w), **kw)

    def paint(self, cv, t, o):
        r, sw = self.g("r", t), self.g("sweep", t)
        if abs(sw) < 0.1:
            return
        rect = skia.Rect.MakeXYWH(-r, -r, 2 * r, 2 * r)
        path = skia.Path()
        path.addArc(rect, self.g("a0", t), sw)
        cv.drawPath(path, stroke_paint(self.g("color", t), o, self.g("w", t)))


class Text(Node):
    """富文本。anchor 两个字母：水平 l/c/r + 垂直 t/m/b，默认 cm（中心）。
    改 text 会交叉淡入淡出。color 是没有颜色标记部分的颜色。"""

    def __init__(self, x=0, y=0, text="", size=30, color=None, anchor="cm", maxw=None, align=None,
                 chain="sans", lh=1.45, bg=None, **kw):
        super().__init__(x, y, text=str(text), size=float(size), color=color or C.FG, **kw)
        self.bg = bg            # 底衬颜色：压在线上的标注（边权、流量）垫一块底色，线不会穿过文字
        self.anchor = anchor
        self.maxw = maxw
        self.align = align or ("c" if anchor[0] == "c" else anchor[0])
        self.chain = chain
        self.lh = lh

    def lay(self, s, size):
        if self.align == "c" and self.maxw:
            return T.balanced(s, int(round(size)), self.maxw, self.chain, self.lh)
        return T.layout(s, int(round(size)), None, self.maxw, self.chain, self.lh)

    def _origin(self, L):
        a = self.anchor
        x0 = 0 if a[0] == "l" else -L.w / 2 if a[0] == "c" else -L.w
        y0 = 0 if a[1] == "t" else -L.h / 2 if a[1] == "m" else -L.h
        return x0, y0

    def paint(self, cv, t, o):
        a, b, u = self.tr["text"].state(t)
        size = self.g("size", t)
        col = self.g("color", t)
        if self.bg is not None:
            boxes = [self.lay(s, size) for s in (a, b) if s]
            if boxes:
                L = max(boxes, key=lambda q: q.w)
                x0, y0 = self._origin(L)
                pad = size * 0.28
                h = size * 1.15
                cy = y0 + L.h / 2
                cv.drawRoundRect(skia.Rect.MakeXYWH(x0 - pad, cy - h / 2, L.w + 2 * pad, h), h / 2, h / 2,
                                 fill_paint(self.bg, o))
        if a == b or u >= 1.0:
            if b:
                L = self.lay(b, size)
                x0, y0 = self._origin(L)
                L.draw(cv, x0, y0, self.align, o, col)
            return
        for s, k in ((a, 1 - u), (b, u)):
            if s and k > 0.01:
                L = self.lay(s, size)
                x0, y0 = self._origin(L)
                L.draw(cv, x0, y0, self.align, o * k, col)

    def bbox(self, t):
        s = self.g("text", t)
        if not s:
            return None
        L = self.lay(s, self.g("size", t))
        x0, y0 = self._origin(L)
        return (x0, y0, x0 + L.w, y0 + L.h)


# ------------------------------------------------------------------ 组合部件
class Cell(Group):
    """一个方格：底框 + 文字。to() 会把 fill/stroke/sw/glow/w/h 交给方框，text/tc/size 交给文字。"""

    BOX_KEYS = ("fill", "stroke", "sw", "glow", "w", "h", "r")

    def __init__(self, x=0, y=0, w=70, h=60, text="", size=30, fill=C.BG3, stroke=C.LINE, tc=None,
                 chain="sans", r=8, sw=2, **kw):
        super().__init__(x, y, **kw)
        self.box = self.add(Rect(0, 0, w, h, fill=fill, stroke=stroke, r=r, sw=sw))
        self.label = self.add(Text(0, 0, text, size=size, color=tc or C.FG, chain=chain))
        self.radius = max(w, h) / 2

    def to(self, dur=None, ease="io", delay=0.0, **kw):
        box = {k: v for k, v in kw.items() if k in self.BOX_KEYS}
        lab = {}
        own = {}
        for k, v in kw.items():
            if k == "text":
                lab["text"] = str(v)
            elif k == "tc":
                lab["color"] = v
            elif k == "size":
                lab["size"] = float(v)
            elif k not in self.BOX_KEYS:
                own[k] = v
        anims = []
        if box:
            anims.append(self.box.to(dur, ease, delay, **box))
        if lab:
            anims.append(self.label.to(dur, ease, delay, **lab))
        if own:
            anims.append(Node.to(self, dur, ease, delay, **own))
        return anims

    def bump(self, dur=None, delay=0.0, **kw):
        box = {k: v for k, v in kw.items() if k in self.BOX_KEYS}
        own = {k: v for k, v in kw.items() if k not in self.BOX_KEYS}
        out = []
        if box:
            out.append(self.box.bump(dur, delay, **box))
        if own:
            out.append(Node.bump(self, dur, delay, **own))
        return out

    def flash(self, color=C.YELLOW, dur=0.7):
        return self.box.bump(dur=dur, glow=1.0, stroke=color)


class Pointer(Group):
    """指向数组某一格的小箭头 + 名字。"""

    def __init__(self, x, y, label="", color=C.YELLOW, side="below", size=26):
        super().__init__(x, y)
        s = 1 if side == "below" else -1
        self.add(Poly([(0, 0), (-11, 16 * s), (11, 16 * s)], fill=color, stroke=None))
        self.label = self.add(Text(0, 34 * s, label, size=size, color=color))


class _BracketLabel(Text):
    def local_xy(self, t):
        b = self.parent
        x1, x2, y = b.g("x1", t), b.g("x2", t), b.g("yy", t)
        return (x1 + x2) / 2, y + b.s * (b.tick + 6 + b.size * 0.7)


class Bracket(Group):
    """横向方括号：标出 [x1, x2] 这一段，label 写在外侧。side='above' 时括号开口朝下。"""

    def __init__(self, x1, x2, y, label="", color=C.YELLOW, side="below", size=24, w=3, tick=12):
        super().__init__(0, 0)
        self.s = 1 if side == "below" else -1
        self.tr["x1"] = Track(float(x1))
        self.tr["x2"] = Track(float(x2))
        self.tr["yy"] = Track(float(y))
        self.color = color
        self.lw = w
        self.tick = tick
        self.size = size
        self.label = self.add(_BracketLabel(0, 0, label, size=size, color=color))

    def paint(self, cv, t, o):
        x1, x2, y = self.g("x1", t), self.g("x2", t), self.g("yy", t)
        s, k = self.s, self.tick
        path = skia.Path()
        path.moveTo(x1, y)
        path.lineTo(x1, y + s * k)
        path.lineTo(x2, y + s * k)
        path.lineTo(x2, y)
        cv.drawPath(path, stroke_paint(self.color, o, self.lw))

    def span(self, x1, x2, dur=None):
        return self.to(dur, x1=float(x1), x2=float(x2))


class Array(Group):
    """一行方格。vals 是初始内容；base 是下标起点（默认 1）。(x, y) 是整行的中心。"""

    def __init__(self, vals, x=640, y=400, cw=72, ch=64, gap=8, index=True, base=1, size=30,
                 fill=C.BG3, stroke=C.LINE, idx_size=22, chain="sans", idx_labels=None, tc=None):
        super().__init__(x, y)
        self.n = len(vals)
        self.cw, self.ch, self.gap, self.base = cw, ch, gap, base
        self.width = self.n * cw + (self.n - 1) * gap
        self.cells = []
        self.idx = []
        for i, v in enumerate(vals):
            cx = -self.width / 2 + cw / 2 + i * (cw + gap)
            c = self.add(Cell(cx, 0, cw, ch, "" if v is None else str(v), size, fill, stroke, chain=chain, tc=tc))
            self.cells.append(c)
            if index:
                lab = idx_labels[i] if idx_labels else str(i + base)
                self.idx.append(self.add(Text(cx, ch / 2 + 18, lab, size=idx_size, color=C.DIM)))

    def __getitem__(self, i):
        return self.cells[i - self.base]

    def __len__(self):
        return self.n

    def lx(self, i):
        """第 i 格中心的局部 x。"""
        return -self.width / 2 + self.cw / 2 + (i - self.base) * (self.cw + self.gap)

    def X(self, i):
        """第 i 格中心的画面 x（按搭建时的位置）。"""
        return self.g("x", 0) + self.lx(i)

    def Y(self):
        return self.g("y", 0)

    def left(self, i):
        return self.lx(i) - self.cw / 2

    def right(self, i):
        return self.lx(i) + self.cw / 2

    def ptr(self, i, label="", color=C.YELLOW, side="below", hidden=True):
        dy = self.ch / 2 + (40 if self.idx else 8)
        y = dy if side == "below" else -self.ch / 2 - 8
        p = Pointer(self.lx(i), y, label, color, side)
        if hidden:
            p.tr["op"].base = 0.0
        self.add(p)
        p.arr = self
        return p

    def move(self, p, i, dur=None):
        return p.to(dur, x=self.lx(i))

    def span(self, l, r, label="", color=C.YELLOW, side="above", off=10, hidden=True, size=24):
        if side == "above":
            y = -self.ch / 2 - off
        else:
            y = self.ch / 2 + off + (30 if self.idx else 0)
        b = Bracket(self.left(l), self.right(r), y, label, color, side=side, size=size)
        if hidden:
            b.tr["op"].base = 0.0
        self.add(b)
        return b

    def respan(self, b, l, r, dur=None):
        return b.to(dur, x1=self.left(l), x2=self.right(r))

    def frame(self, l, r, color=C.YELLOW, pad=6, hidden=True, sw=3, r_=10):
        x1, x2 = self.left(l) - pad, self.right(r) + pad
        b = Rect((x1 + x2) / 2, 0, x2 - x1, self.ch + 2 * pad, fill=(0, 0, 0, 0), stroke=color, sw=sw, r=r_)
        if hidden:
            b.tr["op"].base = 0.0
        self.add(b)
        return b

    def reframe(self, b, l, r, pad=6, dur=None):
        x1, x2 = self.left(l) - pad, self.right(r) + pad
        return b.to(dur, x=(x1 + x2) / 2, w=x2 - x1)

    def fill(self, idxs, color, tc=None):
        out = []
        for i in idxs:
            kw = {"fill": color}
            if tc is not None:
                kw["tc"] = tc
            out.append(self[i].to(**kw))
        return out

    def values(self, vals, color=None):
        out = []
        for i, v in enumerate(vals):
            kw = {"text": "" if v is None else str(v)}
            out.append(self.cells[i].to(**kw))
        return out


class Grid(Group):
    """R×C 表格（DP 表）。g[r, c] 取格子；rlab / clab 是行列标题；rbase / cbase 是下标起点。"""

    def __init__(self, R, C_, x=640, y=440, cw=70, ch=58, gap=4, vals=None, rlab=None, clab=None,
                 size=26, rbase=0, cbase=0, fill=C.BG3, stroke=C.LINE, lab_size=22, lab_color=None,
                 chain="sans", r=6):
        super().__init__(x, y)
        self.R, self.C = R, C_
        self.cw, self.ch, self.gap = cw, ch, gap
        self.rbase, self.cbase = rbase, cbase
        self.width = C_ * cw + (C_ - 1) * gap
        self.height = R * ch + (R - 1) * gap
        self.cells = {}
        for i in range(R):
            for j in range(C_):
                v = vals[i][j] if vals is not None else ""
                c = self.add(Cell(self.lx(j + cbase), self.ly(i + rbase), cw, ch,
                                  "" if v is None else str(v), size, fill, stroke, chain=chain, r=r))
                self.cells[(i + rbase, j + cbase)] = c
        self.rl, self.cl = [], []
        lc = lab_color or C.DIM
        if rlab is not None:
            for i, s in enumerate(rlab):
                self.rl.append(self.add(Text(-self.width / 2 - 14, self.ly(i + rbase), s, size=lab_size,
                                             color=lc, anchor="rm")))
        if clab is not None:
            for j, s in enumerate(clab):
                self.cl.append(self.add(Text(self.lx(j + cbase), -self.height / 2 - 20, s, size=lab_size,
                                             color=lc)))

    def lx(self, j):
        return -self.width / 2 + self.cw / 2 + (j - self.cbase) * (self.cw + self.gap)

    def ly(self, i):
        return -self.height / 2 + self.ch / 2 + (i - self.rbase) * (self.ch + self.gap)

    def X(self, j):
        return self.g("x", 0) + self.lx(j)

    def Y(self, i):
        return self.g("y", 0) + self.ly(i)

    def __getitem__(self, rc):
        return self.cells[rc]

    def frame(self, r0, c0, r1, c1, color=C.YELLOW, pad=5, hidden=True, sw=3):
        x1 = self.lx(c0) - self.cw / 2 - pad
        x2 = self.lx(c1) + self.cw / 2 + pad
        y1 = self.ly(r0) - self.ch / 2 - pad
        y2 = self.ly(r1) + self.ch / 2 + pad
        b = Rect((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, fill=(0, 0, 0, 0), stroke=color, sw=sw, r=10)
        if hidden:
            b.tr["op"].base = 0.0
        self.add(b)
        return b

    def reframe(self, b, r0, c0, r1, c1, pad=5, dur=None):
        x1 = self.lx(c0) - self.cw / 2 - pad
        x2 = self.lx(c1) + self.cw / 2 + pad
        y1 = self.ly(r0) - self.ch / 2 - pad
        y2 = self.ly(r1) + self.ch / 2 + pad
        return b.to(dur, x=(x1 + x2) / 2, y=(y1 + y2) / 2, w=x2 - x1, h=y2 - y1)

    def arrow(self, a, b, color=C.YELLOW, w=3, bend=0.0, hidden=True, head=14):
        """从格子 a=(r,c) 指向格子 b 的箭头（局部坐标）。"""
        ca, cb = self.cells[a], self.cells[b]
        ln = Line(color=color, w=w, head=head, bend=bend)
        ln.attach(ca, cb, pa=min(self.cw, self.ch) * 0.42, pb=min(self.cw, self.ch) * 0.48)
        if hidden:
            ln.tr["op"].base = 0.0
        self.add(ln)
        return ln


class TNode(Group):
    """树 / 图的结点：圆 + 标签。"""

    def __init__(self, x, y, label="", r=26, size=26, fill=C.BG3, stroke=C.LINE2, tc=None, sw=2.5):
        super().__init__(x, y)
        self.c = self.add(Circle(0, 0, r, fill=fill, stroke=stroke, sw=sw))
        self.label = self.add(Text(0, 0, label, size=size, color=tc or C.FG))
        self.radius = r + 2
        self.tags = {}

    def to(self, dur=None, ease="io", delay=0.0, **kw):
        ck = {k: v for k, v in kw.items() if k in ("fill", "stroke", "sw", "glow", "r")}
        lk = {}
        own = {}
        for k, v in kw.items():
            if k == "text":
                lk["text"] = str(v)
            elif k == "tc":
                lk["color"] = v
            elif k not in ("fill", "stroke", "sw", "glow", "r"):
                own[k] = v
        out = []
        if ck:
            out.append(self.c.to(dur, ease, delay, **ck))
        if lk:
            out.append(self.label.to(dur, ease, delay, **lk))
        if own:
            out.append(Node.to(self, dur, ease, delay, **own))
        return out

    def flash(self, color=C.YELLOW, dur=0.7):
        return self.c.bump(dur=dur, glow=1.0)


_SIDES = {"r": (1, 0, "lm"), "l": (-1, 0, "rm"), "u": (0, -1, "cb"), "d": (0, 1, "ct"),
          "ur": (0.75, -0.75, "lb"), "ul": (-0.75, -0.75, "rb"), "dr": (0.75, 0.75, "lt"), "dl": (-0.75, 0.75, "rt")}


class _NodeHost(Group):
    """树和图共用的结点、边、标注操作。"""

    def _init_host(self):
        self.nodes = {}
        self.edges = {}
        self.etags = {}

    def node(self, v):
        return self.nodes[v]

    def __getitem__(self, v):
        return self.nodes[v]

    def edge(self, u, v):
        if (u, v) in self.edges:
            return self.edges[(u, v)]
        return self.edges[(v, u)]

    def has_edge(self, u, v):
        return (u, v) in self.edges or (v, u) in self.edges

    def P(self, v):
        """结点 v 的画面坐标（按搭建时的位置）。"""
        n = self.nodes[v]
        return self.g("x", 0) + n.g("x", 0), self.g("y", 0) + n.g("y", 0)

    def tag(self, v, text="", side="r", color=None, size=22, gap=8, hidden=True):
        """在结点旁边加一个小标注（返回 Text，之后用 .to(text=...) 修改）。"""
        key = (v, side)
        n = self.nodes[v]
        if key in n.tags:
            return n.tags[key]
        dx, dy, anc = _SIDES[side]
        r = n.radius + gap
        tx = Text(n.g("x", 0) + dx * r, n.g("y", 0) + dy * r, text, size=size, color=color or C.YELLOW,
                  anchor=anc)
        if hidden:
            tx.tr["op"].base = 0.0
        self.add(tx)
        n.tags[key] = tx
        return tx

    def etag(self, u, v, text="", color=None, size=22, off=16, hidden=True, t=0.5):
        """在边 (u,v) 的中点外侧加标注（边权、流量）。"""
        key = (u, v) if (u, v) in self.edges else (v, u)
        if key in self.etags:
            return self.etags[key]
        ln = self.edges[key]
        x1, y1, x2, y2 = ln.ends(0)
        mx, my = ln.point(0, t)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        if ln.g("bend", 0) != 0:
            s = 1 if ln.g("bend", 0) < 0 else -1
            nx, ny = -nx * s, -ny * s
        elif ny > 0 or (abs(ny) < 1e-6 and nx < 0):
            nx, ny = -nx, -ny
        # 标注框的半宽、半高在法线方向上的投影，保证文字不压在线上
        L0 = T.layout(str(text), int(size), None)
        ext = abs(nx) * (L0.w / 2 + size * 0.3) + abs(ny) * size * 0.58
        d = max(off, ext + 4)
        tx = Text(mx + nx * d, my + ny * d, text, size=size, color=color or C.DIM, bg=C.alpha(C.BG, 0.82))
        if hidden:
            tx.tr["op"].base = 0.0
        self.add(tx)
        self.etags[key] = tx
        return tx

    def hl_path(self, path, color=C.YELLOW, w=5, node_fill=None):
        out = []
        for a, b in zip(path, path[1:]):
            out.append(self.edge(a, b).to(color=color, w=w))
        if node_fill is not None:
            for v in path:
                out.append(self.nodes[v].to(fill=node_fill))
        return out

    def token(self, v, color=C.YELLOW, r=None, ring=True):
        """标记“当前位置”的圆环（套在结点外面，不挡住编号），可以沿边移动。"""
        x, y = self.nodes[v].g("x", 0), self.nodes[v].g("y", 0)
        if ring:
            d = Circle(x, y, self.nodes[v].radius + 6, fill=(0, 0, 0, 0), stroke=color, sw=4.5)
        else:
            d = Circle(x, y, r or 9, fill=color, stroke=None, sw=0)
        d.tr["op"].base = 0.0
        d.z = 5
        self.add(d)
        return d

    def move_token(self, d, u, v, dur=None):
        """沿边 u→v 移动（直线边直接插值；弧线边按曲线走）。"""
        ln = self.edge(u, v)
        rev = (u, v) not in self.edges

        def fn(S, t0, d_):
            steps = 8
            for k in range(1, steps + 1):
                uu = k / steps
                x, y = ln.point(t0, 1 - uu if rev else uu) if ln.g("bend", t0) != 0 else (None, None)
                if x is None:
                    a, b = self.nodes[u], self.nodes[v]
                    x = a.g("x", t0) + (b.g("x", t0) - a.g("x", t0)) * uu
                    y = a.g("y", t0) + (b.g("y", t0) - a.g("y", t0)) * uu
                ts = t0 + d_ * (k - 1) / steps
                d.tr["x"].add(ts, d_ / steps, x, "lin")
                d.tr["y"].add(ts, d_ / steps, y, "lin")
        return Anim(fn, dur)


class Tree(_NodeHost):
    """有根树。edges 是 (父, 子) 列表（顺序决定孩子左右顺序）；自动排版到 w×h 的框里，(x, y) 是框中心。
    pos 可以手工指定 {结点: (局部x, 局部y)}。"""

    def __init__(self, edges, root, x=640, y=460, w=900, h=560, r=26, labels=None, size=24,
                 pos=None, fill=C.BG3, stroke=C.LINE2, ecolor=C.LINE2, ew=3, hidden_edges=False):
        super().__init__(x, y)
        self._init_host()
        self.root = root
        self.ch = {}
        self.par = {root: None}
        order = [root]
        for p, c in edges:
            self.ch.setdefault(p, []).append(c)
            self.ch.setdefault(c, [])
            self.par[c] = p
        self.ch.setdefault(root, [])
        # 深度与先序
        self.depth = {root: 0}
        stack = [root]
        self.pre = []
        while stack:
            v = stack.pop()
            self.pre.append(v)
            for c in reversed(self.ch[v]):
                self.depth[c] = self.depth[v] + 1
                stack.append(c)
        if pos is None:
            pos = self._tidy(w, h)
        self.pos = pos
        for v in self.pre:
            px, py = pos[v]
            lab = labels[v] if labels and v in labels else str(v)
            self.nodes[v] = TNode(px, py, lab, r, size, fill, stroke)
        for p, c in edges:
            ln = Line(color=ecolor, w=ew).attach(self.nodes[p], self.nodes[c])
            if hidden_edges:
                ln.tr["op"].base = 0
            self.edges[(p, c)] = ln
            self.add(ln)
        for v in self.pre:
            self.add(self.nodes[v])

    def _tidy(self, w, h):
        # 叶子依次占一个横向位置，内部结点放在孩子的中间
        slot = {}
        cnt = [0]

        def place(v):
            if not self.ch[v]:
                slot[v] = cnt[0]
                cnt[0] += 1
            else:
                for c in self.ch[v]:
                    place(c)
                slot[v] = (slot[self.ch[v][0]] + slot[self.ch[v][-1]]) / 2

        import sys
        sys.setrecursionlimit(10000)
        place(self.root)
        nl = max(cnt[0] - 1, 1)
        md = max(self.depth.values()) or 1
        pos = {}
        for v in self.pre:
            px = -w / 2 + w * slot[v] / nl if cnt[0] > 1 else 0
            py = -h / 2 + h * self.depth[v] / md
            pos[v] = (px, py)
        return pos

    def children(self, v):
        return self.ch[v]

    def subtree(self, v):
        out = [v]
        for c in self.ch[v]:
            out += self.subtree(c)
        return out

    def path_up(self, u, a):
        """u 到祖先 a 的结点序列。"""
        out = [u]
        while u != a:
            u = self.par[u]
            out.append(u)
        return out


class Graph(_NodeHost):
    """一般图。pos = {结点: (局部x, 局部y)}；edges 是 (u, v) 或 (u, v, 标注) 列表。
    有向图里如果同时有 u→v 和 v→u，会自动画成两条弧线。"""

    def __init__(self, pos, edges, x=640, y=460, directed=False, r=26, size=24, labels=None,
                 fill=C.BG3, stroke=C.LINE2, ecolor=C.LINE2, ew=3, wsize=22, head=14, bends=None,
                 hidden_edges=False, wcolor=None, wpos=None):
        super().__init__(x, y)
        self._init_host()
        self.directed = directed
        self.adj = {v: [] for v in pos}
        for v, (px, py) in pos.items():
            lab = labels[v] if labels and v in labels else str(v)
            self.nodes[v] = TNode(px, py, lab, r, size, fill, stroke)
        es = set((e[0], e[1]) for e in edges)
        for e in edges:
            u, v = e[0], e[1]
            bend = 0.0
            if bends and (u, v) in bends:
                bend = bends[(u, v)]
            elif directed and (v, u) in es:
                bend = 0.12
            ln = Line(color=ecolor, w=ew, head=head if directed else 0, bend=bend).attach(self.nodes[u], self.nodes[v])
            if hidden_edges:
                ln.tr["op"].base = 0
            self.edges[(u, v)] = ln
            self.adj[u].append(v)
            if not directed:
                self.adj[v].append(u)
            self.add(ln)
        for v in pos:
            self.add(self.nodes[v])
        for e in edges:
            if len(e) > 2 and e[2] is not None:
                tpos = (wpos or {}).get((e[0], e[1]), 0.5)
                self.etag(e[0], e[1], str(e[2]), color=wcolor or C.DIM, size=wsize, hidden=hidden_edges, t=tpos)


class Axes(Group):
    """坐标系。(x, y) 是绘图区中心，w×h 是绘图区大小；xr / yr 是数据范围。"""

    def __init__(self, x=640, y=460, w=800, h=500, xr=(0, 10), yr=(0, 10), xlabel="", ylabel="",
                 ticks=True, xstep=1, ystep=1, color=C.LINE2, size=20, grid=False):
        super().__init__(x, y)
        self.w, self.h, self.xr, self.yr = w, h, xr, yr
        x0, y0 = self.p(xr[0], yr[0])
        x1, y1 = self.p(xr[1], yr[1])
        if grid:
            v = xr[0]
            while v <= xr[1] + 1e-9:
                px, _ = self.p(v, 0)
                self.add(Line(px, y0, px, y1, color=C.alpha(C.LINE, 0.6), w=1))
                v += xstep
            v = yr[0]
            while v <= yr[1] + 1e-9:
                _, py = self.p(0, v)
                self.add(Line(x0, py, x1, py, color=C.alpha(C.LINE, 0.6), w=1))
                v += ystep
        self.add(Line(x0, y0, x1 + 20, y0, color=color, w=2.5, head=12))
        self.add(Line(x0, y0, x0, y1 - 20, color=color, w=2.5, head=12))
        if xlabel:
            self.add(Text(x1 + 30, y0, xlabel, size=size + 2, color=C.DIM, anchor="lm"))
        if ylabel:
            self.add(Text(x0, y1 - 40, ylabel, size=size + 2, color=C.DIM, anchor="cb"))
        if ticks:
            v = xr[0]
            while v <= xr[1] + 1e-9:
                px, _ = self.p(v, 0)
                if v != xr[0] or True:
                    self.add(Text(px, y0 + 18, _fmt(v), size=size, color=C.FAINT))
                v += xstep
            v = yr[0] + ystep
            while v <= yr[1] + 1e-9:
                _, py = self.p(0, v)
                self.add(Text(x0 - 12, py, _fmt(v), size=size, color=C.FAINT, anchor="rm"))
                v += ystep

    def p(self, vx, vy):
        """数据坐标 → 局部坐标。"""
        px = -self.w / 2 + (vx - self.xr[0]) / (self.xr[1] - self.xr[0]) * self.w
        py = self.h / 2 - (vy - self.yr[0]) / (self.yr[1] - self.yr[0]) * self.h
        return px, py

    def dot(self, vx, vy, color=C.YELLOW, r=8, label=None, side="ur", hidden=True, size=20):
        px, py = self.p(vx, vy)
        d = Circle(px, py, r, fill=color, stroke=None, sw=0)
        if hidden:
            d.tr["op"].base = 0.0
        self.add(d)
        if label is not None:
            dx, dy, anc = _SIDES[side]
            tx = Text(px + dx * (r + 6), py + dy * (r + 6), label, size=size, color=color, anchor=anc)
            d.add(tx)
            tx.tr["x"].base = dx * (r + 6)
            tx.tr["y"].base = dy * (r + 6)
        return d

    def seg(self, a, b, color=C.CYAN, w=3, hidden=True, dash=None, head=0):
        x1, y1 = self.p(*a)
        x2, y2 = self.p(*b)
        ln = Line(x1, y1, x2, y2, color=color, w=w, dash=dash, head=head)
        if hidden:
            ln.tr["op"].base = 0.0
        self.add(ln)
        return ln

    def moveseg(self, ln, a, b, dur=None):
        x1, y1 = self.p(*a)
        x2, y2 = self.p(*b)
        return ln.to(dur, x1=x1, y1=y1, x2=x2, y2=y2)

    def rect(self, a, b, color=C.CYAN, fill_a=0.25, hidden=True, sw=2):
        x1, y1 = self.p(*a)
        x2, y2 = self.p(*b)
        r = Rect((x1 + x2) / 2, (y1 + y2) / 2, abs(x2 - x1), abs(y2 - y1), fill=C.alpha(color, fill_a),
                 stroke=color, sw=sw, r=0)
        if hidden:
            r.tr["op"].base = 0.0
        self.add(r)
        return r


def _fmt(v):
    return str(int(v)) if abs(v - round(v)) < 1e-9 else f"{v:g}"


class Card(Group):
    """带标题的卡片（题目、结论）。(x, y) 是中心。"""

    def __init__(self, x, y, w, h, title="", body="", color=C.YELLOW, size=30, title_size=30,
                 fill=None, maxw=None, align="l"):
        super().__init__(x, y)
        self.box = self.add(Rect(0, 0, w, h, fill=fill or C.BG2, stroke=C.alpha(color, 0.45), sw=1.8, r=20,
                                 shadow=1.0))
        top = -h / 2 + 26
        if title:
            self.add(Rect(-w / 2 + 40, top + title_size * 1.45 / 2, 6, title_size * 0.9, fill=color, stroke=None,
                          sw=0, r=3))
            self.title = self.add(Text(-w / 2 + 56, top, title, size=title_size, color=color, anchor="lt",
                                       chain="bold"))
            top += title_size * 1.7
        self.body = self.add(Text(-w / 2 + 34, top, body, size=size, color=C.FG, anchor="lt",
                                  maxw=maxw or (w - 68), align=align))


class Matrix(Group):
    """矩阵：数字 + 两侧方括号。"""

    def __init__(self, vals, x=640, y=460, cw=70, ch=56, size=28, color=None, bcolor=C.DIM):
        super().__init__(x, y)
        R, Cn = len(vals), len(vals[0])
        self.R, self.C = R, Cn
        self.cw, self.ch = cw, ch
        self.width, self.height = Cn * cw, R * ch
        self.cells = {}
        for i in range(R):
            for j in range(Cn):
                tx = self.add(Text(self.lx(j), self.ly(i), str(vals[i][j]), size=size, color=color or C.FG))
                self.cells[(i, j)] = tx
        hw, hh = self.width / 2 + 10, self.height / 2 + 6
        self.add(Poly([(-hw + 12, -hh), (-hw, -hh), (-hw, hh), (-hw + 12, hh)], stroke=bcolor, sw=3, closed=False))
        self.add(Poly([(hw - 12, -hh), (hw, -hh), (hw, hh), (hw - 12, hh)], stroke=bcolor, sw=3, closed=False))

    def lx(self, j):
        return -self.width / 2 + self.cw / 2 + j * self.cw

    def ly(self, i):
        return -self.height / 2 + self.ch / 2 + i * self.ch

    def __getitem__(self, ij):
        return self.cells[ij]


def hidden(node):
    node.tr["op"].base = 0.0
    return node


class SegTree(Group):
    """线段树的示意图：结点是圆角矩形，上方小字写区间，中间写信息。(x, y) 是根结点的中心。
    nodes[(l, r)] 是结点（Cell），info[(l, r)] 是结点下方/内部的信息文字。"""

    def __init__(self, n, x=640, y=170, w=1150, level_h=125, node_h=56, leaf_w=None, size=22, base=1,
                 info_size=20, show_range=True, vals=None):
        super().__init__(x, y)
        self.n, self.base = n, base
        self.level_h = level_h
        leaf_w = leaf_w or (w / n)
        self.leaf_w = leaf_w
        self.nodes, self.info, self.ranges, self.edges = {}, {}, {}, {}
        self.depth = {}
        self.kids = {}

        def lx(i):
            return -w / 2 + leaf_w / 2 + (i - base) * (w - leaf_w) / max(1, n - 1) if n > 1 else 0

        self.leaf_x = lx

        def build(l, r, d):
            self.depth[(l, r)] = d
            cx = (lx(l) + lx(r)) / 2
            span = (r - l + 1) * w / n
            nw = min(span - 10, 230) if l != r else leaf_w - 10
            c = Cell(cx, d * level_h, nw, node_h, "", size, fill=C.BG3, stroke=C.LINE2, r=10)
            self.nodes[(l, r)] = c
            if l < r:
                m = (l + r) // 2
                self.kids[(l, r)] = [(l, m), (m + 1, r)]
                build(l, m, d + 1)
                build(m + 1, r, d + 1)

        build(base, base + n - 1, 0)
        for p, kids in self.kids.items():
            for k in kids:
                a, b = self.nodes[p], self.nodes[k]
                ln = Line(a.g("x", 0), a.g("y", 0) + node_h / 2, b.g("x", 0), b.g("y", 0) - node_h / 2, color=C.LINE2, w=2.5)
                self.edges[(p, k)] = ln
                self.add(ln)
        for key, c in self.nodes.items():
            self.add(c)
            l, r = key
            if show_range:
                if l != r:
                    nw = c.box.g("w", 0)
                    t = Text(c.g("x", 0) - nw / 2 - 8, c.g("y", 0), f"[{l},{r}]", size=19, color=C.DIM, anchor="rm")
                else:
                    t = Text(c.g("x", 0), c.g("y", 0) + node_h / 2 + 16, f"{l}", size=19, color=C.DIM)
                self.ranges[key] = self.add(t)
            self.info[key] = c.label
            c.label.tr["size"].base = float(info_size)
        if vals is not None:
            for i, v in enumerate(vals):
                self.nodes[(base + i, base + i)].label.tr["text"].base = str(v)

    def __getitem__(self, lr):
        return self.nodes[lr]

    def up(self, lr):
        """结点 lr 的父结点（根返回 None）。"""
        for p, kids in self.kids.items():
            if lr in kids:
                return p
        return None

    def decompose(self, ql, qr):
        """查询 [ql, qr] 拆成的结点（从左到右）。"""
        out = []

        def go(l, r):
            if qr < l or r < ql:
                return
            if ql <= l and r <= qr:
                out.append((l, r))
                return
            for k in self.kids[(l, r)]:
                go(*k)

        go(self.base, self.base + self.n - 1)
        return out

    def visited(self, ql, qr):
        """查询时经过的所有结点。"""
        out = []

        def go(l, r):
            if qr < l or r < ql:
                return
            out.append((l, r))
            if ql <= l and r <= qr:
                return
            for k in self.kids[(l, r)]:
                go(*k)

        go(self.base, self.base + self.n - 1)
        return out

    def postorder(self):
        out = []

        def go(lr):
            for k in self.kids.get(lr, []):
                go(k)
            out.append(lr)

        go((self.base, self.base + self.n - 1))
        return out
