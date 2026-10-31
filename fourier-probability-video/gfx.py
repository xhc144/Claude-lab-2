"""画面用到的公共工具：缓动、颜色、文字、公式、坐标系、粒子、背景、辉光。

所有东西都画在 skia 的 CPU 画布上，1920×1080。公式不用 LaTeX：matplotlib 的 mathtext
（Computer Modern 字形）把公式排成轮廓，再转成 skia 的 Path，所以公式和别的图形一样是矢量、能发光。
"""

import functools
import math
from pathlib import Path

import matplotlib
import numpy as np
import skia
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser
from matplotlib.path import Path as MPath
from matplotlib.textpath import TextPath

W, H = 1920, 1080
FPS = 30
ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "build" / "fonts"

matplotlib.rcParams["mathtext.fontset"] = "cm"

# ---------------------------------------------------------------- 配色
BG = (0.010, 0.014, 0.034)
CYAN = (0.30, 0.92, 1.00)      # 样本、概率
MAGENTA = (1.00, 0.30, 0.72)   # 频率、旋转
GOLD = (1.00, 0.80, 0.38)      # 重心、结论
VIOLET = (0.62, 0.50, 1.00)
TEAL = (0.36, 1.00, 0.72)
ORANGE = (1.00, 0.52, 0.22)
RED = (1.00, 0.30, 0.30)
WHITE = (1.0, 1.0, 1.0)
GREY = (0.55, 0.60, 0.72)
DIM = (0.30, 0.36, 0.50)


# ---------------------------------------------------------------- 缓动
def clamp(x, a=0.0, b=1.0):
    if isinstance(x, np.ndarray):
        return np.clip(x, a, b)
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x)
    return x * x * x


def eio(x):
    x = clamp(x)
    if isinstance(x, np.ndarray):
        return np.where(x < 0.5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ramp(u, t0, t1, f=eio):
    """u 从 t0 到 t1 时由 0 走到 1。"""
    if t1 <= t0:
        return float(u >= t0)
    return f(clamp((u - t0) / (t1 - t0)))


def env(u, t0, t1=None, fi=0.5, fo=0.5):
    """t0 开始淡入（fi 秒），t1 结束前淡出（fo 秒）。"""
    a = clamp((u - t0) / fi) if fi > 0 else float(u >= t0)
    if t1 is not None:
        a = min(a, clamp((t1 - u) / fo) if fo > 0 else float(u < t1))
    return smooth(a)


def mix(c1, c2, u):
    return tuple(lerp(a, b, u) for a, b in zip(c1, c2))


def spectrum(v):
    """0~1 映射到 青 → 紫 → 品红 → 金 的渐变，用来给粒子按位置上色。"""
    stops = [CYAN, VIOLET, MAGENTA, GOLD]
    v = clamp(v) * (len(stops) - 1)
    k = min(int(v), len(stops) - 2)
    return mix(stops[k], stops[k + 1], v - k)


def heat(v):
    """温度色：黑 → 深红 → 橙 → 黄 → 白。"""
    stops = [(0.05, 0.02, 0.08), (0.55, 0.05, 0.12), (1.0, 0.35, 0.08), (1.0, 0.78, 0.25), (1.0, 1.0, 0.92)]
    v = clamp(v) * (len(stops) - 1)
    k = min(int(v), len(stops) - 2)
    return mix(stops[k], stops[k + 1], v - k)


# ---------------------------------------------------------------- 画笔
def col(rgb, a=1.0):
    return skia.Color4f(float(rgb[0]), float(rgb[1]), float(rgb[2]), clamp(float(a))).toColor()


def paint(rgb=WHITE, a=1.0, stroke=None, shader=None, cap=True, blend=None, effect=None):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if shader is not None:
        p.setShader(shader)
    if blend is not None:
        p.setBlendMode(blend)
    if effect is not None:
        p.setPathEffect(effect)
    return p


def radial(x, y, r, rgb, a):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 1), [col(rgb, a), col(rgb, 0)])


def glow_dot(c, x, y, r, rgb, a=1.0, halo=4.0):
    if a <= 0.003:
        return
    c.drawCircle(x, y, r * halo, paint(rgb, 1, shader=radial(x, y, r * halo, rgb, a * 0.45)))
    c.drawCircle(x, y, r, paint(mix(rgb, WHITE, 0.55), a))


def path_xy(xs, ys, close=False):
    p = skia.Path()
    n = len(xs)
    if n:
        p.moveTo(float(xs[0]), float(ys[0]))
        for i in range(1, n):
            p.lineTo(float(xs[i]), float(ys[i]))
        if close:
            p.close()
    return p


def stroke_xy(c, xs, ys, rgb, a=1.0, w=3.0, close=False, effect=None):
    if a <= 0.003 or len(xs) < 2:
        return
    c.drawPath(path_xy(xs, ys, close), paint(rgb, a, stroke=w, effect=effect))


def dashed(on=10, off=8, phase=0):
    return skia.DashPathEffect.Make([on, off], phase)


def dots(c, xs, ys, rgb, a=1.0, size=4.0):
    """一次画很多个圆点（drawPoints 比逐个 drawCircle 快得多）。"""
    if a <= 0.003 or len(xs) == 0:
        return
    pts = [skia.Point(float(x), float(y)) for x, y in zip(xs, ys)]
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(rgb, a, stroke=size))


def segments(c, x0, y0, x1, y1, rgb, a=1.0, w=2.0):
    """一次画很多条线段。"""
    if a <= 0.003 or len(x0) == 0:
        return
    pts = []
    for i in range(len(x0)):
        pts.append(skia.Point(float(x0[i]), float(y0[i])))
        pts.append(skia.Point(float(x1[i]), float(y1[i])))
    c.drawPoints(skia.Canvas.kLines_PointMode, pts, paint(rgb, a, stroke=w))


def colored_dots(c, xs, ys, vals, a=1.0, size=4.0, bins=16, cmap=spectrum, alphas=None):
    """按 vals（0~1）分成几组颜色，每组一次画完。alphas 是每个点的透明度（可选）。"""
    if a <= 0.003 or len(xs) == 0:
        return
    q = np.clip((np.asarray(vals) * bins).astype(int), 0, bins - 1)
    if alphas is None:
        for b in range(bins):
            sel = q == b
            if sel.any():
                dots(c, xs[sel], ys[sel], cmap((b + 0.5) / bins), a, size)
    else:
        aq = np.clip((np.asarray(alphas) * 4).astype(int), 0, 3)
        for b in range(bins):
            for lv in range(4):
                sel = (q == b) & (aq == lv)
                if sel.any():
                    dots(c, xs[sel], ys[sel], cmap((b + 0.5) / bins), a * (lv + 1) / 4, size)


def colored_segments(c, x0, y0, x1, y1, vals, a=1.0, w=2.0, bins=12, cmap=spectrum):
    if a <= 0.003 or len(x0) == 0:
        return
    q = np.clip((np.asarray(vals) * bins).astype(int), 0, bins - 1)
    for b in range(bins):
        sel = q == b
        if sel.any():
            segments(c, x0[sel], y0[sel], x1[sel], y1[sel], cmap((b + 0.5) / bins), a, w)


# ---------------------------------------------------------------- 字体与文字
FONTS = {
    "serif": "NotoSerifSC-Black.ttf",
    "serifm": "NotoSerifSC-Medium.ttf",
    "sans": "NotoSansSC-Medium.ttf",
    "bold": "NotoSansSC-Bold.ttf",
    "orb": "Orbitron-Black.ttf",
    "orbm": "Orbitron-Medium.ttf",
    "mono": "JetBrainsMono-Medium.ttf",
}


@functools.lru_cache(None)
def typeface(fam):
    return skia.Typeface.MakeFromFile(str(FONT_DIR / FONTS[fam]))


@functools.lru_cache(None)
def font(fam, size):
    f = skia.Font(typeface(fam), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text_width(s, size, fam="sans", track=0.0):
    f = font(fam, size)
    if not track:
        return f.measureText(s)
    return sum(f.measureText(ch) for ch in s) + track * max(0, len(s) - 1)


def text(c, s, x, y, size, fam="sans", rgb=WHITE, a=1.0, align="c", track=0.0, p=None):
    """在基线 y 处画一行字，返回宽度。"""
    if a <= 0.003 or not s:
        return 0
    f = font(fam, size)
    w = text_width(s, size, fam, track)
    x0 = x - w / 2 if align == "c" else x - w if align == "r" else x
    p = p or paint(rgb, a)
    if not track:
        c.drawString(s, x0, y, f, p)
    else:
        for ch in s:
            c.drawString(ch, x0, y, f, p)
            x0 += f.measureText(ch) + track
    return w


# ---------------------------------------------------------------- 公式（mathtext → skia.Path）
_PARSER = MathTextParser("path")


@functools.lru_cache(None)
def math_path(tex, size):
    """返回 (path, 宽, 基线以上高度, 基线以下深度)。path 的原点在基线左端，y 向下。"""
    s = tex if tex.startswith("$") else f"${tex}$"
    prop = FontProperties(size=size)
    tp = TextPath((0, 0), s, size=size, prop=prop)
    w, h, d, _, _ = _PARSER.parse(s, dpi=72, prop=prop)
    p = skia.Path()
    verts, codes = tp.vertices, tp.codes
    i, n = 0, len(codes)
    while i < n:
        code = codes[i]
        x, y = verts[i]
        if code == MPath.MOVETO:
            p.moveTo(x, -y)
            i += 1
        elif code == MPath.LINETO:
            p.lineTo(x, -y)
            i += 1
        elif code == MPath.CURVE3:
            (x2, y2) = verts[i + 1]
            p.quadTo(x, -y, x2, -y2)
            i += 2
        elif code == MPath.CURVE4:
            (x2, y2), (x3, y3) = verts[i + 1], verts[i + 2]
            p.cubicTo(x, -y, x2, -y2, x3, -y3)
            i += 3
        elif code == MPath.CLOSEPOLY:
            p.close()
            i += 1
        else:
            i += 1
    p.setFillType(skia.PathFillType.kWinding)
    return p, float(w), float(h - d), float(d)


def math_width(tex, size):
    return math_path(tex, size)[1]


def draw_math(c, tex, x, y, size, rgb=WHITE, a=1.0, align="c", reveal=1.0, scan=True, glow=0.0):
    """在基线 y 处画公式。reveal<1 时从左往右揭开，揭开的边缘有一道亮光。返回宽度。"""
    if a <= 0.003:
        return 0
    path, w, asc, desc = math_path(tex, size)
    x0 = x - w / 2 if align == "c" else x - w if align == "r" else x
    c.save()
    c.translate(x0, y)
    if reveal < 1:
        edge = (w + 40) * reveal - 20
        c.clipRect(skia.Rect(-10, -asc - size, edge, desc + size))
    if glow > 0:
        c.drawPath(path, paint(rgb, a * glow, stroke=size * 0.10))
    c.drawPath(path, paint(rgb, a))
    c.restore()
    if scan and 0 < reveal < 1:
        ex = x0 + (w + 40) * reveal - 20
        hh = asc + desc + size * 0.5
        c.drawRect(skia.Rect(ex - 2, y - asc - size * 0.25, ex + 2, y - asc - size * 0.25 + hh),
                   paint(mix(rgb, WHITE, 0.6), a * 0.9))
        c.drawCircle(ex, y - (asc - desc) / 2, size * 0.9, paint(rgb, 1, shader=radial(ex, y - (asc - desc) / 2, size * 0.9, rgb, a * 0.5)))
    return w


def split_rich(s):
    """'把点 $x$ 送到…' → [('t','把点 '), ('m','x'), ('t',' 送到…')]"""
    parts = s.split("$")
    out = []
    for i, seg in enumerate(parts):
        if seg:
            out.append(("m" if i % 2 else "t", seg))
    return out


def rich_tokens(s, size, fam="sans"):
    """切成可折行的小块：中文按字，公式整块。"""
    toks = []
    for kind, seg in split_rich(s):
        if kind == "m":
            toks.append(("m", seg, math_width(seg, size * 1.12) + 4))
        else:
            for ch in seg:
                toks.append(("t", ch, text_width(ch, size, fam)))
    return toks


NO_START = set("，。、；：！？”」）…—,.;:!?)")
BREAK_AFTER = set("，。、；：！？…）")


def rich_lines(s, size, fam="sans", maxw=1560):
    toks = rich_tokens(s, size, fam)
    total = sum(t[2] for t in toks)
    nlines = max(1, math.ceil(total / maxw))
    if nlines == 1:
        return [toks]
    if nlines == 2:
        # 两行：在标点后面断开，选两行最接近等长、又都不超宽的位置
        best, best_d = None, 1e9
        acc = 0.0
        for i, tok in enumerate(toks[:-1]):
            acc += tok[2]
            if tok[1] in BREAK_AFTER and toks[i + 1][1] not in NO_START:
                w2 = total - acc
                if acc <= maxw and w2 <= maxw and abs(acc - w2) < best_d:
                    best, best_d = i + 1, abs(acc - w2)
        if best is not None:
            return [toks[:best], toks[best:]]
    target = min(maxw, total / nlines + size * 1.5)
    lines, cur, cw = [], [], 0.0
    for tok in toks:
        if cw + tok[2] > target and cur and tok[1] not in NO_START:
            # 尽量在最近的标点后面断行，不把一个词拆到两行
            cut = len(cur)
            for j in range(len(cur) - 1, max(0, len(cur) - 12), -1):
                if cur[j][1] in BREAK_AFTER:
                    cut = j + 1
                    break
            lines.append(cur[:cut])
            cur = cur[cut:]
            cw = sum(x[2] for x in cur)
            if tok[1] == " " and not cur:
                continue
        cur.append(tok)
        cw += tok[2]
    if cur:
        lines.append(cur)
    return lines


def draw_tokens(c, toks, x, y, size, rgb=WHITE, a=1.0, align="c", fam="sans", upto=None, mrgb=None):
    """画一行 token；upto 是显示到第几个 token（打字机效果）。"""
    w = sum(t[2] for t in toks)
    x0 = x - w / 2 if align == "c" else x - w if align == "r" else x
    p = paint(rgb, a)
    f = font(fam, size)
    for i, (kind, s, tw) in enumerate(toks):
        if upto is not None and i >= upto:
            break
        if kind == "t":
            c.drawString(s, x0, y, f, p)
        else:
            draw_math(c, s, x0 + 2, y, size * 1.12, mrgb or mix(rgb, GOLD, 0.35), a, align="l")
        x0 += tw
    return w


def rich(c, s, x, y, size, rgb=WHITE, a=1.0, align="c", fam="sans", maxw=1560, lh=1.5, mrgb=None):
    """多行富文本（中文 + $公式$），y 是第一行基线。返回行数。"""
    if a <= 0.003:
        return 0
    lines = rich_lines(s, size, fam, maxw)
    for k, toks in enumerate(lines):
        draw_tokens(c, toks, x, y + k * size * lh, size, rgb, a, align, fam, mrgb=mrgb)
    return len(lines)


# ---------------------------------------------------------------- 坐标系
class Plot:
    """把数学坐标 [x0,x1]×[y0,y1] 映到屏幕矩形 (L, T, R, B)。"""

    def __init__(self, L, T, R, B, x0, x1, y0, y1):
        self.L, self.T, self.R, self.B = L, T, R, B
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

    def sx(self, x):
        return self.L + (np.asarray(x) - self.x0) / (self.x1 - self.x0) * (self.R - self.L)

    def sy(self, y):
        return self.B - (np.asarray(y) - self.y0) / (self.y1 - self.y0) * (self.B - self.T)

    def axes(self, c, a=1.0, rgb=GREY, xticks=(), yticks=(), xlabel=None, ylabel=None, grow=1.0, zero_y=0.0):
        if a <= 0.003:
            return
        yz = float(self.sy(zero_y))
        xr = self.L + (self.R - self.L) * grow
        c.drawLine(self.L, yz, xr, yz, paint(rgb, 0.55 * a, stroke=1.6))
        if self.x0 < 0 < self.x1:
            xz = float(self.sx(0))
            c.drawLine(xz, self.B, xz, self.T, paint(rgb, 0.30 * a, stroke=1.2))
        for v in xticks:
            px = float(self.sx(v))
            if px > xr:
                continue
            c.drawLine(px, yz - 5, px, yz + 5, paint(rgb, 0.5 * a, stroke=1.4))
        for v in yticks:
            py = float(self.sy(v))
            c.drawLine(self.L - 5, py, self.L + 5, py, paint(rgb, 0.5 * a, stroke=1.4))
        if xlabel:
            draw_math(c, xlabel, xr + 22, yz + 8, 30, rgb, 0.8 * a, align="l")
        if ylabel:
            draw_math(c, ylabel, self.L, self.T - 14, 30, rgb, 0.8 * a, align="c")

    def xtick_labels(self, c, ticks, a=1.0, rgb=GREY, size=24, dy=36):
        """ticks: [(值, 'tex'), ...]"""
        yz = float(self.sy(0)) if self.y0 <= 0 <= self.y1 else self.B
        for v, lab in ticks:
            draw_math(c, lab, float(self.sx(v)), yz + dy, size, rgb, 0.75 * a)

    def curve(self, c, xs, ys, rgb, a=1.0, w=3.0, effect=None):
        stroke_xy(c, self.sx(xs), self.sy(ys), rgb, a, w, effect=effect)

    def fill(self, c, xs, ys, rgb, a=1.0, base=0.0):
        if a <= 0.003 or len(xs) < 2:
            return
        px, py = self.sx(xs), self.sy(ys)
        yb = float(self.sy(base))
        p = path_xy(px, py)
        p.lineTo(float(px[-1]), yb)
        p.lineTo(float(px[0]), yb)
        p.close()
        top = float(np.min(py))
        sh = skia.GradientShader.MakeLinear([skia.Point(0, top), skia.Point(0, yb)],
                                            [col(rgb, 0.42 * a), col(rgb, 0.06 * a)])
        c.drawPath(p, paint(rgb, 1, shader=sh))


class Disk:
    """复平面上的单位圆：z ↦ 屏幕坐标。"""

    def __init__(self, cx, cy, R):
        self.cx, self.cy, self.R = cx, cy, R

    def xy(self, z):
        z = np.asarray(z)
        return self.cx + self.R * z.real, self.cy - self.R * z.imag

    def draw(self, c, a=1.0, rgb=GREY, ring=CYAN, axes=True, labels=True, ring_w=2.0):
        if a <= 0.003:
            return
        R = self.R
        if axes:
            gp = paint(rgb, 0.28 * a, stroke=1.2)
            c.drawLine(self.cx - R * 1.25, self.cy, self.cx + R * 1.25, self.cy, gp)
            c.drawLine(self.cx, self.cy - R * 1.25, self.cx, self.cy + R * 1.25, gp)
        c.drawCircle(self.cx, self.cy, R, paint(ring, 0.18 * a, stroke=ring_w * 4))
        c.drawCircle(self.cx, self.cy, R, paint(ring, 0.55 * a, stroke=ring_w))
        if labels:
            draw_math(c, "1", self.cx + R + 16, self.cy + 30, 26, rgb, 0.7 * a, align="l")
            draw_math(c, "i", self.cx + 10, self.cy - R - 14, 26, rgb, 0.7 * a, align="l")


# ---------------------------------------------------------------- 背景
_rng = np.random.default_rng(7)
STARS = {
    "x": _rng.random(420), "y": _rng.random(420),
    "z": _rng.choice([0.25, 0.5, 1.0], 420, p=[0.6, 0.3, 0.1]),
    "ph": _rng.random(420) * 6.283, "r": _rng.random(420),
}
_NEB = []

NEBULA = {
    0: (VIOLET, CYAN), 1: (CYAN, MAGENTA), 2: (MAGENTA, VIOLET), 3: (GOLD, CYAN), 4: (TEAL, VIOLET),
    5: (ORANGE, MAGENTA), 6: (GOLD, VIOLET), 7: (CYAN, MAGENTA), 8: (VIOLET, GOLD),
}


def background(c, t, theme=0, spin=1.0):
    # 星云是大面积的渐变，先在 1/4 分辨率上画好再放大（全分辨率画渐变很慢，看不出区别）
    if not _NEB:
        _NEB.append(skia.Surface(W // 4, H // 4))
    nc = _NEB[0].getCanvas()
    nc.clear(col(BG))
    c1, c2 = NEBULA.get(theme, (VIOLET, CYAN))
    x1 = (520 + 200 * math.sin(t * 0.05)) / 4
    y1 = (360 + 90 * math.cos(t * 0.07)) / 4
    x2 = (1420 + 170 * math.cos(t * 0.043)) / 4
    y2 = (720 + 80 * math.sin(t * 0.061)) / 4
    nc.drawRect(skia.Rect(0, 0, W / 4, H / 4), paint(shader=radial(x1, y1, 240, c1, 0.085)))
    nc.drawRect(skia.Rect(0, 0, W / 4, H / 4), paint(shader=radial(x2, y2, 250, c2, 0.07)))
    c.drawImageRect(_NEB[0].makeImageSnapshot(), skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear))

    # 缓慢旋转的极坐标网格（整部片子的母题就是旋转）
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(t * 1.2 * spin)
    gp = paint(CYAN, 0.028, stroke=1)
    for r in range(180, 1400, 140):
        c.drawCircle(0, 0, r, gp)
    for k in range(24):
        ang = k * math.pi / 12
        c.drawLine(180 * math.cos(ang), 180 * math.sin(ang), 1400 * math.cos(ang), 1400 * math.sin(ang), gp)
    c.restore()

    xs = (STARS["x"] * W - t * 5 * STARS["z"]) % W
    ys = STARS["y"] * H
    tw = 0.45 + 0.55 * np.sin(t * (0.6 + STARS["r"] * 1.8) + STARS["ph"])
    a = tw * (0.22 + 0.55 * STARS["z"])
    q = np.minimum((a * 6).astype(int), 5)
    star_rgb = mix(CYAN, WHITE, 0.7)
    for z in (0.25, 0.5, 1.0):
        for lvl in range(6):
            sel = (STARS["z"] == z) & (q == lvl)
            if sel.any():
                dots(c, xs[sel], ys[sel], star_rgb, (lvl + 0.5) / 6, 1.6 * (0.7 + 1.3 * z))


# ---------------------------------------------------------------- 常用小部件
def bracket_box(c, x, y, w, h, rgb, a, L=16, sw=2):
    if a <= 0.003:
        return
    p = paint(rgb, a, stroke=sw, cap=False)
    for sx, sy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        c.drawLine(sx, sy, sx + dx * L, sy, p)
        c.drawLine(sx, sy, sx, sy + dy * L, p)


def panel(c, x, y, w, h, a, rgb=CYAN):
    """半透明的深色面板 + 四角括号。"""
    if a <= 0.003:
        return
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 14, 14, paint(BG, 0.72 * a))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 14, 14, paint(rgb, 0.16 * a, stroke=1.2))
    bracket_box(c, x - 4, y - 4, w + 8, h + 8, rgb, 0.7 * a)


def readout(c, label, value, x, y, a=1.0, rgb=CYAN, size=28, align="l"):
    """HUD 读数：t = 1.25 这种，公式标签 + 等宽数字。"""
    if a <= 0.003:
        return
    lw = math_width(label, size * 1.1)
    if align == "r":
        x -= lw + 14 + text_width(value, size, "mono")
    draw_math(c, label, x, y, size * 1.1, rgb, a, align="l")
    text(c, value, x + lw + 14, y, size, "mono", WHITE, a * 0.9, align="l")


def arrow(c, x0, y0, x1, y1, rgb, a=1.0, w=3.0, head=16):
    if a <= 0.003:
        return
    c.drawLine(x0, y0, x1, y1, paint(rgb, a, stroke=w))
    ang = math.atan2(y1 - y0, x1 - x0)
    p = skia.Path()
    p.moveTo(x1, y1)
    p.lineTo(x1 - head * math.cos(ang - 0.42), y1 - head * math.sin(ang - 0.42))
    p.lineTo(x1 - head * math.cos(ang + 0.42), y1 - head * math.sin(ang + 0.42))
    p.close()
    c.drawPath(p, paint(rgb, a))


def ring_flare(c, cx, cy, r, u, rgb=GOLD, a=1.0):
    """一道沿圆周扫过的亮弧（转场、强调用）。u 从 0 到 1。"""
    if a <= 0.003 or u <= 0 or u >= 1:
        return
    sweep = 360 * eout(u)
    fade = 1 - smooth((u - 0.6) / 0.4)
    rect = skia.Rect(cx - r, cy - r, cx + r, cy + r)
    c.drawArc(rect, -90, sweep, False, paint(rgb, 0.25 * a * fade, stroke=14))
    c.drawArc(rect, -90, sweep, False, paint(mix(rgb, WHITE, 0.4), a * fade, stroke=2.5))
    ang = math.radians(-90 + sweep)
    glow_dot(c, cx + r * math.cos(ang), cy + r * math.sin(ang), 6, rgb, a * fade, halo=6)


def shockwave(c, u, cx, cy, rgb=WHITE, scale=1.0):
    """u∈[0,1]：一圈向外扩散并变淡的冲击波。"""
    if u <= 0 or u >= 1:
        return
    r = 40 + 900 * eout(u) * scale
    a = (1 - u) ** 2
    c.drawCircle(cx, cy, r, paint(rgb, 0.5 * a, stroke=3 + 26 * (1 - u)))
    c.drawCircle(cx, cy, r * 0.82, paint(rgb, 0.18 * a, stroke=2))
