"""画面：用 skia 逐帧绘制（抗锯齿矢量 + 辉光），原始像素通过管道交给 ffmpeg 编码。

每一帧都只由时间 t 决定（随机数在启动时用固定种子生成），所以可以把整段视频切成几块并行渲染。
"""

import functools
import io
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia

import cues
from cues import EX_PRIMES, MILESTONES
import mathdata

W, H = 1920, 1080
ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "build" / "fonts"

# ---------------------------------------------------------------- 配色
BG = (0.012, 0.018, 0.04)
CYAN = (0.24, 0.94, 1.0)      # 数论 / 伽罗瓦一侧
MAGENTA = (1.0, 0.24, 0.68)   # 调和分析 / 自守一侧
GOLD = (1.0, 0.79, 0.36)      # 两边相遇的地方
WHITE = (1.0, 1.0, 1.0)
TEAL = (0.36, 1.0, 0.69)
VIOLET = (0.61, 0.48, 1.0)
GREY = (0.55, 0.6, 0.7)


# ---------------------------------------------------------------- 小工具
def clamp(x, a=0.0, b=1.0):
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


def env(t, t0, t1=None, fi=0.4, fo=0.4):
    """t0 开始淡入（fi 秒），t1 结束前淡出（fo 秒）。"""
    a = clamp((t - t0) / fi) if fi > 0 else float(t >= t0)
    if t1 is not None:
        a = min(a, clamp((t1 - t) / fo) if fo > 0 else float(t < t1))
    return smooth(a)


def mix(c1, c2, u):
    return tuple(lerp(a, b, u) for a, b in zip(c1, c2))


def col(rgb, a=1.0):
    return skia.Color4f(rgb[0], rgb[1], rgb[2], clamp(a)).toColor()


def paint(rgb=WHITE, a=1.0, stroke=None, blend=None, cap=True, shader=None, effect=None):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if blend is not None:
        p.setBlendMode(blend)
    if shader is not None:
        p.setShader(shader)
    if effect is not None:
        p.setPathEffect(effect)
    return p


def radial(x, y, r, rgb, a):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 1), [col(rgb, a), col(rgb, 0)])


def glow_dot(c, x, y, r, rgb, a):
    if a <= 0.003:
        return
    c.drawCircle(x, y, r * 4, paint(rgb, 1, shader=radial(x, y, r * 4, rgb, a * 0.35)))
    c.drawCircle(x, y, r, paint(mix(rgb, WHITE, 0.4), a))


def polyline(pts):
    path = skia.Path()
    if len(pts):
        path.moveTo(*pts[0])
        for x, y in pts[1:]:
            path.lineTo(x, y)
    return path


# ---------------------------------------------------------------- 字体与文字
FONTS = {
    "serif": "NotoSerifSC-Black.ttf",
    "sans": "NotoSansSC-Medium.ttf",
    "bold": "NotoSansSC-Bold.ttf",
    "orb": "Orbitron-Black.ttf",
    "orbm": "Orbitron-Medium.ttf",
    "raj": "Rajdhani-SemiBold.ttf",
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


def wrap(s, size, fam, maxw):
    """按宽度折行。有空格的（英文）按单词折，中文按字折。"""
    if " " in s and not any("\u4e00" <= ch <= "\u9fff" for ch in s):
        lines, cur = [], ""
        for word in s.split(" "):
            cand = (cur + " " + word).strip()
            if text_width(cand, size, fam) > maxw and cur:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        return lines + ([cur] if cur else [])
    lines, cur = [], ""
    for ch in s:
        if text_width(cur + ch, size, fam) > maxw and cur:
            # 不让标点出现在行首
            if ch in "，。、；：！？”」）…—":
                cur += ch
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def wrap_balanced(s, size, fam, maxw):
    """字幕折行：需要两行时尽量在中间附近的标点处断开，避免最后一行只剩一两个字。"""
    if text_width(s, size, fam) <= maxw:
        return [s]
    best, best_score = None, 1e9
    for i in range(1, len(s)):
        a, b = s[:i], s[i:]
        if b[0] in "，。、；：！？”」）…—":
            continue
        wa, wb = text_width(a, size, fam), text_width(b, size, fam)
        if wa > maxw or wb > maxw:
            continue
        score = abs(wa - wb) - (120 if a[-1] in "，；：、—" else 0)
        if score < best_score:
            best, best_score = [a, b], score
    return best or wrap(s, size, fam, maxw)


GLYPHS = "ABCDEFGHKLMNPQRSTXZ0123456789#%&"  # Orbitron / Rajdhani 只有拉丁字母和数字
MATH_GLYPHS = "∑∏∫∂ζπρΓΛΩ≅∞αβγδθλμσφψ0123456789"
CJK_GLYPHS = "朗兰兹纲领数论几何群表示模形式自守伽罗瓦函子性对偶质数方程"


def scramble(s, prog, t, pool=GLYPHS, seed=0):
    """解码效果：前 prog 比例的字符已经「破译」，其余是乱跳的符号。"""
    n = len(s)
    k = int(clamp(prog) * n + 1e-6)
    rng = np.random.default_rng(int(t * 24) * 131 + seed)
    out = []
    for i, ch in enumerate(s):
        if i < k or ch == " ":
            out.append(ch)
        else:
            out.append(pool[rng.integers(len(pool))])
    return "".join(out)


# ---------------------------------------------------------------- 数学公式（matplotlib mathtext 渲染成图片）
@functools.lru_cache(None)
def math_img(tex, size):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["mathtext.fontset"] = "stix"
    from matplotlib.figure import Figure

    fig = Figure(figsize=(1, 1), dpi=144)
    fig.patch.set_alpha(0)
    fig.text(0, 0, tex, fontsize=size, color="white")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=144, transparent=True, bbox_inches="tight", pad_inches=0.06)
    img = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(buf.getvalue()))
    return img.withDefaultMipmaps()


SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def math_size(tex, size, scale=1.0):
    img = math_img(tex, size)
    return img.width() / 2 * scale, img.height() / 2 * scale


def draw_math(c, tex, x, y, size, rgb=WHITE, a=1.0, align="c", scale=1.0, reveal=1.0):
    """公式以 (x, y) 为中心（align='l' 时 x 是左边缘）。reveal<1 时只露出左边一部分。"""
    if a <= 0.003:
        return 0, 0
    img = math_img(tex, size)
    w, h = img.width() / 2 * scale, img.height() / 2 * scale
    x0 = x - w / 2 if align == "c" else x - w if align == "r" else x
    p = skia.Paint(AntiAlias=True)
    p.setColorFilter(skia.ColorFilters.Blend(col(rgb, 1), skia.BlendMode.kSrcIn))
    p.setAlphaf(clamp(a))
    c.save()
    if reveal < 1:
        c.clipRect(skia.Rect(x0 - 2, y - h, x0 + w * clamp(reveal), y + h))
    c.drawImageRect(img, skia.Rect(x0, y - h / 2, x0 + w, y + h / 2), SAMPLING, p)
    c.restore()
    return w, h


def rich(c, parts, x, y, size, rgb=WHITE, a=1.0, align="c", fam="sans"):
    """中文和公式混排：parts 里以 $ 开头结尾的是公式。y 是文字基线。"""
    widths = []
    for s in parts:
        if s.startswith("$"):
            widths.append(math_size(s, size * 0.95)[0])
        else:
            widths.append(text_width(s, size, fam))
    total = sum(widths)
    x0 = x - total / 2 if align == "c" else x - total if align == "r" else x
    for s, w in zip(parts, widths):
        if s.startswith("$"):
            draw_math(c, s, x0, y - size * 0.36, size * 0.95, rgb, a, align="l")
        else:
            text(c, s, x0, y, size, fam, rgb, a, align="l")
        x0 += w
    return total


# ---------------------------------------------------------------- 预先生成的图形（每个进程算一次）
RNG = np.random.default_rng(1967)
STARS = {
    "x": RNG.random(560), "y": RNG.random(560),
    "z": RNG.choice([0.25, 0.5, 1.0], 560, p=[0.55, 0.3, 0.15]),
    "ph": RNG.random(560) * 6.28, "r": RNG.random(560),
}


def ulam_points(n_side=53):
    """乌拉姆螺旋：把 1, 2, 3, … 绕成方形螺旋，返回 (n, x, y)。"""
    pts = [(1, 0, 0)]
    x = y = 0
    n = 1
    step = 1
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    d = 0
    while n < n_side * n_side:
        for _ in range(2):
            dx, dy = dirs[d % 4]
            for _ in range(step):
                n += 1
                x += dx
                y += dy
                pts.append((n, x, y))
            d += 1
        step += 1
    return [p for p in pts if p[0] <= n_side * n_side]


ULAM = ulam_points()
PRIME_SET = set(mathdata.primes_below(3000))


def modular_tiling(depth=13):
    """模群 PSL(2,ℤ) 作用在上半平面的基本区域，经 Cayley 变换画进庞加莱圆盘。

    返回 (左半三角形的填充路径, 所有边的路径)，坐标在单位圆盘里。
    """
    S = np.array([[0, -1], [1, 0]])
    T = np.array([[1, 1], [0, 1]])
    Ti = np.array([[1, -1], [0, 1]])

    def key(m):
        m = m if (m[0, 0] > 0 or (m[0, 0] == 0 and m[1, 0] > 0)) else -m
        return tuple(m.flatten())

    elems = [np.eye(2, dtype=int)]
    seen = {key(elems[0])}
    frontier = elems[:]
    for _ in range(depth):
        nxt = []
        for g in frontier:
            for h in (S, T, Ti):
                m = g @ h
                if abs(m).max() > 60:
                    continue
                k = key(m)
                if k not in seen:
                    seen.add(k)
                    nxt.append(m)
        elems += nxt
        frontier = nxt

    Y = 30.0
    arc = np.exp(1j * np.linspace(2 * np.pi / 3, np.pi / 2, 14))
    up = 1j * np.geomspace(1, Y, 18)
    down = -0.5 + 1j * np.geomspace(Y, math.sqrt(3) / 2, 18)
    left = np.concatenate([arc, up, down])            # 左半：ρ → i → i∞ → ρ
    right = -np.conj(left)                            # 右半：关于虚轴对称
    edge_arc = np.exp(1j * np.linspace(2 * np.pi / 3, np.pi / 3, 24))
    edge_side = -0.5 + 1j * np.geomspace(math.sqrt(3) / 2, Y, 22)

    fill = skia.Path()
    edges = skia.Path()
    fill_r = skia.Path()

    def to_disk(g, z):
        a, b, cc, d = g.flatten()
        gz = (a * z + b) / (cc * z + d)
        return (gz - 1j) / (gz + 1j)

    for g in elems:
        center = to_disk(g, np.array([2j]))[0]
        if abs(center) > 0.985:
            continue
        for poly, path in ((left, fill), (right, fill_r)):
            w = to_disk(g, poly)
            path.moveTo(w[0].real, w[0].imag)
            for v in w[1:]:
                path.lineTo(v.real, v.imag)
            path.close()
        for e in (edge_arc, edge_side):
            w = to_disk(g, e)
            edges.moveTo(w[0].real, w[0].imag)
            for v in w[1:]:
                edges.lineTo(v.real, v.imag)
    return fill, fill_r, edges


TILE_FILL, TILE_FILL_R, TILE_EDGES = modular_tiling()


def draw_tiling(c, cx, cy, R, t, a, rgb=MAGENTA, rgb2=VIOLET):
    if a <= 0.003:
        return
    c.save()
    c.translate(cx, cy)
    c.rotate(t * 6)
    c.scale(R, R)
    c.drawPath(TILE_FILL, paint(rgb, 0.24 * a))
    c.drawPath(TILE_FILL_R, paint(rgb2, 0.08 * a))
    c.drawPath(TILE_EDGES, paint(mix(rgb, WHITE, 0.3), 0.55 * a, stroke=1.2 / R))
    c.restore()
    c.drawCircle(cx, cy, R, paint(mix(rgb, WHITE, 0.4), 0.8 * a, stroke=2.2))


def curve_points():
    """实数点：y² + y = x³ − x²，两支在最左边的点接起来画成一笔。"""
    xs = np.linspace(-0.4196, 2.1, 400)
    D = np.maximum(1 + 4 * (xs ** 3 - xs ** 2), 0)
    up = (-1 + np.sqrt(D)) / 2
    lo = (-1 - np.sqrt(D)) / 2
    return np.concatenate([xs[::-1], xs]), np.concatenate([up[::-1], lo])


CURVE_X, CURVE_Y = curve_points()


def draw_curve(c, cx, cy, sc, a, prog=1.0, rgb=CYAN, axes=True, points=True):
    """以 (cx, cy) 为原点、sc 像素/单位画椭圆曲线的实数图像。"""
    if a <= 0.003:
        return
    if axes:
        ax = paint(GREY, 0.25 * a, stroke=1.2)
        c.drawLine(cx - 1.2 * sc, cy, cx + 2.6 * sc, cy, ax)
        c.drawLine(cx, cy - 2.4 * sc, cx, cy + 3.2 * sc, ax)
    n = int(len(CURVE_X) * clamp(prog))
    if n > 1:
        pts = [(cx + x * sc, cy - y * sc) for x, y in zip(CURVE_X[:n], CURVE_Y[:n])]
        c.drawPath(polyline(pts), paint(rgb, a, stroke=3.2))
        hx, hy = pts[-1]
        if prog < 1:
            glow_dot(c, hx, hy, 5, WHITE, a)
    if points and prog >= 1:
        for x, y in [(0, 0), (0, -1), (1, 0), (1, -1)]:
            glow_dot(c, cx + x * sc, cy - y * sc, 4.5, GOLD, a)


def iceberg_mesh():
    from matplotlib.path import Path as MPath
    from scipy.spatial import Delaunay

    poly = np.array([(860, 382), (1085, 382), (1250, 470), (1420, 630), (1360, 800), (1120, 930),
                     (790, 918), (575, 790), (520, 610), (660, 470)], float)
    mp = MPath(poly)
    rng = np.random.default_rng(11)
    pts = []
    while len(pts) < 170:
        p = rng.uniform([500, 385], [1440, 935])
        if mp.contains_point(p):
            pts.append(p)
    allp = np.vstack([poly, np.array(pts)])
    tri = Delaunay(allp)
    edges = set()
    for s in tri.simplices:
        for i in range(3):
            a, b = sorted((s[i], s[(i + 1) % 3]))
            mid = (allp[a] + allp[b]) / 2
            if mp.contains_point(mid, radius=-1) or mp.contains_point(mid, radius=1):
                edges.add((a, b))
    return allp, sorted(edges), poly


ICE_PTS, ICE_EDGES, ICE_POLY = iceberg_mesh()


def sphere_net(n=180):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    P = np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1)
    d = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    edges = set()
    for k in range(n):
        for j in np.argsort(d[k])[1:4]:
            edges.add(tuple(sorted((k, int(j)))))
    return P, sorted(edges)


NET_P, NET_E = sphere_net()

DECODE = ["L(s, ρ) = L(s, π)", "tr ρ(Frob_p) = a_p(π)", "ρ : Gal → GL(n)", "y² + y = x³ − x²",
          "p − N_p = a_p", "q ∏ (1 − q^n)² (1 − q^11n)²", "x^n + y^n = z^n", "π_H  ⇒  π_G",
          "ζ(s) = ∏ (1 − p^−s)^−1", "Λ(s) = Λ(2 − s)", "N = 11", "∑ a_n q^n"]
time_hint = [0.0]  # 乱码随时间跳动，用当前帧时间做种子

HAND = []  # 「手写」的每一行：一串折线点（相对纸面左上角，单位像素）
for _j in range(15):
    _rng = np.random.default_rng(100 + _j)
    _w = 400 if _j not in (0, 14) else (_rng.uniform(150, 260))
    _xs = np.linspace(0, _w, 90)
    _ys = 3.2 * np.sin(_xs * 0.21 + _j) * np.sin(_xs * 0.047 + 2 * _j) + 2.0 * np.sin(_xs * 0.9)
    HAND.append(np.stack([_xs, _ys], 1))
HAND_GAPS = [set(np.random.default_rng(300 + j).choice(np.arange(8, 88), 5, replace=False)) for j in range(15)]

DATA = mathdata.load()
ROWS = DATA["rows"]
ROW_BY_P = {r["p"]: r for r in ROWS}


# ---------------------------------------------------------------- 背景
NEBULA = {
    "letter": (CYAN, GOLD), "title": (CYAN, MAGENTA), "worlds": (CYAN, MAGENTA),
    "example": (CYAN, VIOLET), "fermat": (GOLD, CYAN), "program": (MAGENTA, CYAN),
    "history": (VIOLET, GOLD), "finale": (GOLD, MAGENTA), "end": (CYAN, MAGENTA),
}


_NEB = []


def background(c, t, sid, warp=0.0):
    # 星云是大面积的渐变，先在 1/4 分辨率上画好再放大（全分辨率画渐变很慢，而且看不出区别）
    if not _NEB:
        _NEB.append(skia.Surface(W // 4, H // 4))
    nc = _NEB[0].getCanvas()
    nc.clear(col(BG))
    c1, c2 = NEBULA[sid]
    x1 = (560 + 180 * math.sin(t * 0.05)) / 4
    y1 = (380 + 90 * math.cos(t * 0.07)) / 4
    x2 = (1400 + 160 * math.cos(t * 0.045)) / 4
    y2 = (700 + 80 * math.sin(t * 0.06)) / 4
    nc.drawRect(skia.Rect(0, 0, W / 4, H / 4), paint(shader=radial(x1, y1, 225, c1, 0.10)))
    nc.drawRect(skia.Rect(0, 0, W / 4, H / 4), paint(shader=radial(x2, y2, 238, c2, 0.08)))
    c.drawImageRect(_NEB[0].makeImageSnapshot(), skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear))

    # 极坐标网格
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(t * 1.5)
    gp = paint(CYAN, 0.035, stroke=1)
    for r in range(160, 1400, 130):
        c.drawCircle(0, 0, r, gp)
    for k in range(24):
        a = k * math.pi / 12
        c.drawLine(160 * math.cos(a), 160 * math.sin(a), 1400 * math.cos(a), 1400 * math.sin(a), gp)
    c.restore()

    # 星空（warp>0 时拉成向外飞的光线）
    xs = (STARS["x"] * W - t * 6 * STARS["z"]) % W
    ys = STARS["y"] * H
    tw = 0.45 + 0.55 * np.sin(t * (0.6 + STARS["r"] * 1.8) + STARS["ph"])
    if warp > 0.01:
        cx, cy = W / 2, H / 2
        dx, dy = xs - cx, ys - cy
        L = warp * 0.55 * STARS["z"]
        for i in range(0, len(xs), 1):
            a = float(0.25 + 0.6 * STARS["z"][i]) * (0.4 + 0.6 * warp)
            x0, y0 = cx + dx[i] * (1 + 0.04 * warp), cy + dy[i] * (1 + 0.04 * warp)
            c.drawLine(x0, y0, x0 + dx[i] * L[i], y0 + dy[i] * L[i],
                       paint(mix(CYAN, WHITE, 0.6), a, stroke=0.6 + 1.6 * STARS["z"][i]))
    else:
        # 按大小和亮度分组，每组一次 drawPoints（逐颗画太慢）
        a = tw * (0.25 + 0.6 * STARS["z"])
        q = np.minimum((a * 8).astype(int), 7)
        star_rgb = mix(CYAN, WHITE, 0.7)
        for z in (0.25, 0.5, 1.0):
            for lvl in range(8):
                sel = (STARS["z"] == z) & (q == lvl)
                if not sel.any():
                    continue
                pts = [skia.Point(float(x), float(y)) for x, y in zip(xs[sel], ys[sel])]
                c.drawPoints(skia.Canvas.kPoints_PointMode, pts,
                             paint(star_rgb, (lvl + 0.5) / 8, stroke=2 * (0.7 + 1.3 * z)))


def hud(c, t, sid, tag, a):
    if a <= 0.003:
        return
    m, L = 34, 34
    p = paint(CYAN, 0.38 * a, stroke=1.6, cap=False)
    for sx, sy in ((m, m), (W - m, m), (m, H - m), (W - m, H - m)):
        dx = L if sx < W / 2 else -L
        dy = L if sy < H / 2 else -L
        c.drawLine(sx, sy, sx + dx, sy, p)
        c.drawLine(sx, sy, sx, sy + dy, p)
    text(c, "THE LANGLANDS PROGRAM", 62, 74, 15, "orbm", CYAN, 0.45 * a, align="l", track=5)
    text(c, tag, 62, 100, 19, "raj", WHITE, 0.42 * a, align="l", track=3)
    mm, ss = divmod(t, 60)
    text(c, f"T+{int(mm):02d}:{ss:05.2f}", W - 62, 74, 20, "raj", CYAN, 0.45 * a, align="r", track=2)
    bars = 18
    for k in range(bars):
        h = 4 + 14 * abs(math.sin(t * 3.1 + k * 0.7)) * abs(math.sin(t * 1.3 + k))
        c.drawRect(skia.Rect.MakeXYWH(W - 62 - (bars - k) * 7, 92 - h, 4, h), paint(CYAN, 0.35 * a))


TAGS = {
    "letter": "PROLOGUE  //  1967", "worlds": "01  //  TWO CONTINENTS", "example": "02  //  A MIRACLE",
    "fermat": "03  //  MODULARITY", "program": "04  //  THE PROGRAM", "history": "05  //  THE EXPEDITION",
    "finale": "06  //  ROSETTA STONE",
}


# ---------------------------------------------------------------- 共用画面元素
def draw_letter(c, cx, cy, s, rot, a, ink, pages=1, glow=CYAN, salutation=True, scr=None):
    """一页信纸。ink：本页写到哪里（0~1）；pages：后面叠着几页。"""
    if a <= 0.003:
        return
    w, h = 470, 620
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.scale(s, s)
    for k in range(min(pages, 17) - 1, 0, -1):
        off = k * 4.0
        r = skia.Rect.MakeXYWH(-w / 2 + off, -h / 2 - off, w, h)
        c.drawRect(r, paint(BG, 0.9 * a))
        c.drawRect(r, paint(glow, 0.10 * a, stroke=1.2))
    r = skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h)
    c.drawRect(r, paint((0.03, 0.05, 0.09), 0.95 * a))
    c.drawRect(r, paint(glow, 0.75 * a, stroke=2.2))
    x0, y0 = -w / 2 + 36, -h / 2 + 70
    if salutation:
        draw_math(c, r"$\mathit{Dear\ Professor\ Weil,}$", x0, y0 - 14, 26, mix(glow, WHITE, 0.5), a, align="l")
    total = len(HAND) * 90
    done = int(total * clamp(ink)) if scr is None else 0
    pen = None
    for j, line in enumerate(HAND):
        n = clamp(done - j * 90, 0, 90)
        if n < 2:
            break
        n = int(n)
        yy = y0 + 34 + j * 34
        pts = [(x0 + x, yy + y) for x, y in line[:n]]
        path = skia.Path()
        pen_down = False
        for i, (x, y) in enumerate(pts):
            if i in HAND_GAPS[j]:
                pen_down = False
                continue
            if not pen_down:
                path.moveTo(x, y)
                pen_down = True
            else:
                path.lineTo(x, y)
        c.drawPath(path, paint(mix(glow, WHITE, 0.25), 0.85 * a, stroke=1.8))
        pen = pts[-1]
    if scr is not None:
        # 结尾的「破译」：纸面上的乱码一行行解成公式
        for j, ln in enumerate(DECODE):
            k = clamp(scr * 1.5 - j * 0.04)
            text(c, scramble(ln, k, time_hint[0], MATH_GLYPHS, seed=j),
                 x0, y0 + 40 + j * 38, 22, "sans", GOLD, a * (0.55 + 0.45 * k), align="l", track=1)
    if pen is not None and ink < 1:
        glow_dot(c, pen[0], pen[1], 4, GOLD, a)
    c.restore()


def shockwave(c, t, t0, cx, cy, rgb=WHITE, scale=1.0, dur=1.4):
    u = (t - t0) / dur
    if 0 <= u < 1:
        r = eout(u) * 1300 * scale
        c.drawCircle(cx, cy, r, paint(rgb, (1 - u) ** 2 * 0.9, stroke=2 + 22 * (1 - u)))
        c.drawCircle(cx, cy, r * 0.72, paint(rgb, (1 - u) ** 2 * 0.4, stroke=1 + 6 * (1 - u)))


BURST = np.random.default_rng(7).random((320, 4))


def burst(c, t, t0, cx, cy, rgb, n=320, speed=900, life=2.2):
    u = t - t0
    if u < 0 or u > life:
        return
    for i in range(n):
        ang, sp, sz, hue = BURST[i % len(BURST)]
        ang *= 6.283
        d = speed * (0.2 + sp) * (1 - math.exp(-u * 2.2)) / 2.2 * 2
        x, y = cx + math.cos(ang) * d, cy + math.sin(ang) * d
        a = (1 - u / life) ** 1.5
        c.drawCircle(x, y, 1 + 2.5 * sz, paint(mix(rgb, WHITE, hue * 0.6), a))


def flash(c, t, t0, strength=0.8, dur=0.6):
    u = (t - t0) / dur
    if 0 <= u < 1:
        c.drawRect(skia.Rect(0, 0, W, H), paint(WHITE, strength * (1 - u) ** 2))


def streak(c, t, t0, cx, cy, rgb=CYAN, dur=1.6, w=1500):
    u = (t - t0) / dur
    if 0 <= u < 1:
        a = (1 - u) ** 1.6
        c.save()
        c.translate(cx, cy)
        c.scale(1, 0.018)
        c.drawCircle(0, 0, w * (0.6 + 0.4 * u), paint(shader=radial(0, 0, w * (0.6 + 0.4 * u), rgb, a)))
        c.restore()
        c.drawRect(skia.Rect(cx - w * 0.5, cy - 1.2, cx + w * 0.5, cy + 1.2), paint(mix(rgb, WHITE, 0.6), a * 0.8))


def bracket_box(c, x, y, w, h, rgb, a, L=18, sw=2):
    p = paint(rgb, a, stroke=sw, cap=False)
    for sx, sy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
        dx = L if sx == x else -L
        dy = L if sy == y else -L
        c.drawLine(sx, sy, sx + dx, sy, p)
        c.drawLine(sx, sy, sx, sy + dy, p)


def title_block(c, t, R, cx, cy, a=1.0, scr_t=None):
    """大标题：朗兰兹纲领 / THE LANGLANDS PROGRAM / 数学的大统一理论。"""
    u = t - R
    if u < 0:
        return
    track = lerp(110, 26, eout(u / 2.2))
    s = "朗兰兹纲领"
    if scr_t is not None:
        s = scramble(s, clamp(u / 0.5), t, CJK_GLYPHS)
    ca = clamp(u / 0.25) * a
    off = 14 * (1 - eout(u / 0.6))
    if off > 0.5:
        text(c, s, cx - off, cy, 150, "serif", (1, 0.2, 0.4), ca * 0.6, track=track,
             p=paint((1, 0.2, 0.4), ca * 0.6, blend=skia.BlendMode.kPlus))
        text(c, s, cx + off, cy, 150, "serif", (0.2, 0.6, 1), ca * 0.6, track=track,
             p=paint((0.2, 0.6, 1), ca * 0.6, blend=skia.BlendMode.kPlus))
    text(c, s, cx, cy, 150, "serif", WHITE, ca, track=track)
    text(c, "THE LANGLANDS PROGRAM", cx, cy + 78, 34, "orbm", CYAN, clamp((u - 0.45) / 0.5) * a,
         track=lerp(30, 14, eout((u - 0.45) / 1.5)))
    a3 = clamp((u - 1.0) / 0.6) * a
    if a3 > 0:
        wl = 150 * eout((u - 1.0) / 1.0)
        text(c, "数学的大统一理论", cx, cy + 140, 32, "sans", GOLD, a3, track=10)
        lp = paint(GOLD, a3 * 0.7, stroke=1.5)
        c.drawLine(cx - 190 - wl, cy + 128, cx - 190, cy + 128, lp)
        c.drawLine(cx + 190, cy + 128, cx + 190 + wl, cy + 128, lp)


# ---------------------------------------------------------------- 场景
def scene_letter(c, t, S, tl):
    L = S["lines"]
    st = S["start"]
    # 日期打字机
    move = eout((t - L[0]["start"] + 0.4) / 1.2)
    dy = lerp(470, 165, move)
    n = int(clamp((t - st - 0.3) * 12, 0, len(cues.DATE_TEXT)))
    a0 = env(t, st, L[4]["start"] + 0.5, 0.2, 0.8)
    w = text(c, cues.DATE_TEXT[:n], W / 2, dy, lerp(64, 44, move), "orbm", CYAN, a0, track=lerp(16, 12, move))
    if n < len(cues.DATE_TEXT) or ((t * 2) % 1 < 0.5 and t < L[0]["start"] + 1.5):
        x = W / 2 + w / 2 + 10
        c.drawRect(skia.Rect.MakeXYWH(x, dy - 40 * lerp(1, 0.7, move), 16, 44 * lerp(1, 0.7, move)),
                   paint(CYAN, a0 * 0.8))
    text(c, "Robert P. Langlands  →  André Weil", W / 2, dy + lerp(64, 48, move), lerp(30, 24, move), "sans",
         WHITE, 0.7 * env(t, st + 1.5, L[4]["start"] + 0.5, 0.6, 0.8), track=3)

    # 信纸：L0 期间快速写满 17 页
    p0, p1 = L[0]["start"] + 0.2, L[0]["end"] + 0.2
    prog = clamp((t - p0) / (p1 - p0))
    page = min(17, 1 + int(prog * 17))
    ink = (prog * 17) % 1 if page < 17 else min(1, (t - p0 - (p1 - p0) * 16 / 17) / ((p1 - p0) / 17))
    a_paper = env(t, L[0]["start"] - 0.3, L[3]["start"], 0.6, 0.6)
    # L1 起纸往左缩、变暗，给引文让位
    side = smooth((t - L[1]["start"]) / 1.0)
    cx = lerp(W / 2, 330, side)
    cy = lerp(585, 560, side)
    sc = lerp(1.0, 0.62, side)
    draw_letter(c, cx, cy, sc, lerp(-2.5, -6, side), a_paper * lerp(1, 0.55, side), ink, page,
                salutation=(page == 1))
    if a_paper > 0.01:
        text(c, f"PAGE {page:02d} / 17", cx + 235 * sc, cy + 345 * sc, 22 * max(sc, 0.8), "raj", GOLD,
             a_paper * lerp(1, 0.6, side), align="r", track=3)

    # L2：引文
    q = L[2]
    aq = env(t, L[1]["start"] + 0.4, L[3]["start"] + 0.1, 0.5, 0.5)
    if aq > 0.003:
        bx, by, bw, bh = 640, 290, 1180, 520
        bracket_box(c, bx, by, bw, bh, GOLD, 0.7 * aq, L=26)
        text(c, "“", bx + 34, by + 120, 150, "serif", GOLD, 0.35 * aq, align="l")
        text(c, "P.S.  //  COVER NOTE", bx + bw - 30, by + 40, 18, "raj", GOLD, 0.6 * aq, align="r", track=4)
        zh = q["sub"].strip("“”")
        k = int(len(zh) * clamp((t - q["start"]) / ((q["end"] - q["start"]) * 0.92)))
        lines = wrap(zh, 46, "serif", bw - 150)
        shown = 0
        for i, ln in enumerate(lines):
            part = ln[: max(0, k - shown)]
            shown += len(ln)
            text(c, part, bx + 90, by + 130 + i * 72, 46, "serif", mix(GOLD, WHITE, 0.55), aq, align="l")
        en = ("If you are willing to read it as pure speculation I would appreciate that; "
              "if not — I am sure you have a waste basket handy.")
        en_lines = wrap(en, 27, "raj", bw - 170)
        ea = aq * 0.6 * clamp((t - q["start"] - 1.0) / 1.0)
        for i, ln in enumerate(en_lines):
            text(c, ln, bx + 90, by + 130 + len(lines) * 72 + 30 + i * 36, 27, "raj", WHITE, ea, align="l", track=1)
        text(c, "—— R. P. LANGLANDS, 1967", bx + bw - 60, by + bh - 36, 22, "raj", GOLD, ea, align="r", track=3)

    # L3：名字
    n3 = L[3]
    an = env(t, n3["start"] - 0.05, L[4]["start"] + 1.2, 0.15, 0.9)
    if an > 0.003:
        u = t - n3["start"]
        name = scramble("ROBERT P. LANGLANDS", clamp(u / 0.7), t)
        text(c, name, W / 2, 500, 88, "orb", WHITE, an, track=6)
        wl = 520 * eout(u / 0.9)
        c.drawLine(W / 2 - wl, 545, W / 2 + wl, 545, paint(CYAN, an * 0.8, stroke=2))
        text(c, "罗伯特 · 朗兰兹", W / 2, 615, 48, "serif", CYAN, an * clamp((u - 0.3) / 0.5), track=8)
        text(c, "1936 年生于加拿大  ·  时任普林斯顿大学", W / 2, 668, 24, "sans", WHITE,
             0.6 * an * clamp((u - 0.7) / 0.5), track=3)

    # L4：远征——信纸飞向远方
    u4 = t - L[4]["start"]
    if u4 > 0:
        a4 = clamp(u4 / 0.6) * (1 - smooth((t - S["end"] + 0.3) / 0.3))
        s4 = 0.9 * math.exp(-u4 * 0.38)
        draw_letter(c, W / 2, H / 2 - 20, s4, -3 + u4 * 6, a4, 1.0, 17, glow=GOLD, salutation=False)


def letter_warp(t, tl):
    """信的最后一句到标题出现前，星空逐渐变成光速飞行。"""
    s = tl.line("letter", 4)["start"] + 1.0
    r = cues.title_reveal(tl)
    if t < s:
        return 0.0
    if t < r:
        return ein((t - s) / (r - s))
    return max(0.0, 1 - (t - r) / 0.5)


def scene_title(c, t, S, tl):
    R = cues.title_reveal(tl)
    # 揭晓前：中心的光越来越亮
    if t < R:
        u = clamp((t - S["start"]) / (R - S["start"]))
        c.drawCircle(W / 2, H / 2, 40 + 300 * u, paint(shader=radial(W / 2, H / 2, 40 + 300 * u, mix(CYAN, WHITE, u), 0.5 * u)))
        return
    shockwave(c, t, R, W / 2, H / 2 - 30, mix(CYAN, WHITE, 0.4))
    burst(c, t, R, W / 2, H / 2 - 30, CYAN)
    streak(c, t, R, W / 2, H / 2 - 70, CYAN)
    a = 1 - smooth((t - S["end"] + 0.6) / 0.6)
    title_block(c, t, R, W / 2, H / 2 + 10, a)


def scene_worlds(c, t, S, tl):
    L = S["lines"]
    st = S["start"]
    a = env(t, st, S["end"], 0.8, 0.5)
    slide = 35 * smooth((t - L[3]["start"]) / 1.6)
    LC = (520 + slide, 520)
    RC = (1400 - slide, 520)
    R = 290

    # 标题
    al = a * env(t, st + 0.2, None, 0.8)
    text(c, "数论", LC[0], 175, 64, "serif", CYAN, al, track=10)
    text(c, "NUMBER THEORY", LC[0], 212, 18, "orbm", CYAN, 0.6 * al, track=8)
    ar = a * env(t, st + 0.6, None, 0.8)
    text(c, "调和分析", RC[0], 175, 64, "serif", MAGENTA, ar, track=10)
    text(c, "HARMONIC ANALYSIS", RC[0], 212, 18, "orbm", MAGENTA, 0.6 * ar, track=8)

    # 左：乌拉姆螺旋里的质数
    c.drawCircle(LC[0], LC[1], R, paint(shader=radial(LC[0], LC[1], R, CYAN, 0.10 * al)))
    c.drawCircle(LC[0], LC[1], R, paint(CYAN, 0.45 * al, stroke=1.6))
    grow = clamp((t - L[1]["start"] + 0.3) / 3.0)
    c.save()
    c.translate(*LC)
    c.rotate(t * 2.5)
    sp = 10.4
    pts_all, pts_p = [], []
    for n, x, y in ULAM:
        px, py = x * sp, y * sp
        if px * px + py * py > (R - 12) ** 2:
            continue
        if n in PRIME_SET and n < 2809 * grow:
            pts_p.append(skia.Point(px, py))
        else:
            pts_all.append(skia.Point(px, py))
    dp = paint(GREY, 0.16 * al, stroke=2.2)
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts_all, dp)
    tw = 0.75 + 0.25 * math.sin(t * 3)
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts_p, paint(CYAN, al * tw, stroke=4.2))
    c.restore()
    # 飘起来的质数
    if grow > 0:
        for k, p in enumerate([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]):
            u = (t * 0.18 + k * 0.137) % 1
            x = LC[0] + 230 * math.sin(k * 2.3)
            y = LC[1] + 220 - u * 440
            text(c, str(p), x, y, 26, "raj", WHITE, al * grow * math.sin(u * math.pi) * 0.7)
        rich(c, ["奇质数  ", r"$p = x^2 + y^2 \ \Leftrightarrow\ p \equiv 1\ (\mathrm{mod}\ 4)$"],
             LC[0], LC[1] + R + 60, 26, CYAN, 0.65 * al * grow)

    # 右：波
    c.drawCircle(RC[0], RC[1], R, paint(shader=radial(RC[0], RC[1], R, MAGENTA, 0.10 * ar)))
    c.drawCircle(RC[0], RC[1], R, paint(MAGENTA, 0.45 * ar, stroke=1.6))
    wave = clamp((t - L[2]["start"] + 0.3) / 2.0)
    c.save()
    clip = skia.Path()
    clip.addCircle(RC[0], RC[1], R - 4)
    c.clipPath(clip, doAntiAlias=True)
    for k in range(9):
        yb = RC[1] + (k - 4) * 58
        pts = []
        for i in range(0, 121):
            x = RC[0] - R + i * (2 * R / 120)
            e = math.exp(-((x - RC[0]) / 200) ** 2)
            y = yb + (8 + 26 * wave) * e * math.sin(x * (0.025 + k * 0.004) - t * (2 + k * 0.3) + k)
            pts.append((x, y))
        c.drawPath(polyline(pts), paint(mix(MAGENTA, VIOLET, k / 8), ar * (0.25 + 0.6 * wave), stroke=2.2))
    for k in range(4):
        rr = ((t * 70 + k * 75) % 300)
        c.drawCircle(RC[0], RC[1], rr, paint(MAGENTA, ar * wave * 0.5 * (1 - rr / 300), stroke=1.5))
    c.restore()
    if wave > 0:
        draw_math(c, r"$f\left(\frac{az+b}{cz+d}\right) = (cz+d)^k f(z)$", RC[0], RC[1] + R + 50, 26,
                  MAGENTA, 0.65 * ar * wave)

    # 桥
    ub = clamp((t - L[3]["start"]) / 1.4)
    if ub > 0:
        x0, x1 = LC[0] + R, RC[0] - R
        def bez(u):
            mx = (x0 + x1) / 2
            return ((1 - u) ** 2 * x0 + 2 * u * (1 - u) * mx + u * u * x1,
                    (1 - u) ** 2 * LC[1] + 2 * u * (1 - u) * (LC[1] - 70) + u * u * RC[1])
        n = int(60 * eout(ub))
        pts = [bez(i / 60) for i in range(n + 1)]
        if len(pts) > 1:
            c.drawPath(polyline(pts), paint(GOLD, a * 0.9, stroke=4.5))
            c.drawPath(polyline(pts), paint(WHITE, a * 0.7, stroke=1.5))
        if ub >= 1:
            for k in range(24):
                u = (t * 0.32 + k / 24) % 1
                x, y = bez(u)
                glow_dot(c, x, y, 3, CYAN if k % 2 else MAGENTA, a * math.sin(u * math.pi))
                x, y = bez(1 - u)
        text(c, "朗兰兹对应", (x0 + x1) / 2, LC[1] - 200, 36, "serif", GOLD, a * ub, track=6)
        text(c, "LANGLANDS CORRESPONDENCE", (x0 + x1) / 2, LC[1] - 168, 15, "orbm", GOLD, 0.7 * a * ub, track=5)


def table_layout(ty):
    rows = {"p": ty, "N": ty + 52, "d": ty + 104, "a": ty + 156}
    cols = [400 + k * 146 for k in range(len(EX_PRIMES))]
    return rows, cols


def scene_example(c, t, S, tl):
    L = S["lines"]
    st = S["start"]
    ex = cues.example_schedule(tl)
    a = env(t, st, S["end"], 0.5, 0.5)

    # L0：CASE STUDY
    a0 = a * env(t, st + 0.1, L[1]["start"] + 0.2, 0.3, 0.5)
    if a0 > 0.003:
        u = t - st
        text(c, scramble("CASE STUDY", clamp(u / 0.6), t), W / 2, 520, 92, "orb", WHITE, a0, track=14)
        text(c, "一个具体的例子", W / 2, 590, 34, "sans", CYAN, a0, track=10)
        bracket_box(c, W / 2 - 420, 400, 840, 230, CYAN, a0 * 0.7, L=30)

    split = ex["split"]
    a_main = a * env(t, L[1]["start"] - 0.2, split + 0.5, 0.4, 0.6)
    # 曲线方程（左上角，一直留着）
    if a_main > 0.003:
        draw_math(c, r"$E:\ y^2 + y = x^3 - x^2$", 110, 160, 46, CYAN, a_main, align="l")
        text(c, "CURVE 11a3  ·  CONDUCTOR 11", 115, 222, 20, "raj", WHITE, 0.55 * a_main, align="l", track=3)

    # 左：实数图像
    c0, c1 = ex["curve"]
    a_cv = a * env(t, c0 - 0.1, ex["product"], 0.4, 0.5)
    draw_curve(c, 330, 440, 105, a_cv, eout((t - c0) / (c1 - c0)))
    if a_cv > 0.003:
        rich(c, ["有理点  ", r"$E(\mathbb{Q}) \cong \mathbb{Z}/5$"], 600, 560, 24, GOLD,
             a_cv * clamp((t - c1) / 0.6), align="l", fam="sans")

    # 右：模 p 网格
    a_grid = a * env(t, ex["grids"][0][1] - 0.2, L[3]["start"], 0.3, 0.5)
    for k, (p, g0, g1) in enumerate(ex["grids"]):
        if not (g0 <= t < g1 or (k == len(ex["grids"]) - 1 and t >= g1)):
            continue
        u = (t - g0) / (g1 - g0)
        pulse = 1 + 0.06 * (1 - eout(u * 3))
        box = 380 * pulse
        gx, gy = 1380 - box / 2, 300
        s = box / p
        sol = mathdata.solutions(p)
        dots = [skia.Point(gx + (i + 0.5) * s, gy + box - (j + 0.5) * s) for i in range(p) for j in range(p)]
        c.drawPoints(skia.Canvas.kPoints_PointMode, dots, paint(GREY, 0.35 * a_grid, stroke=max(2.5, s * 0.16)))
        m = int(len(sol) * clamp(u / 0.7))
        for (x, y) in sol[:m]:
            glow_dot(c, gx + (x + 0.5) * s, gy + box - (y + 0.5) * s, max(3.5, s * 0.17), CYAN, a_grid)
        bracket_box(c, gx - 16, gy - 16, box + 32, box + 32, CYAN, 0.6 * a_grid)
        draw_math(c, rf"$\mathrm{{mod}}\ {p}$", gx - 6, gy - 46, 30, WHITE, a_grid, align="l")
        draw_math(c, rf"$N_{{{p}}} = {m}$", gx + box + 6, gy - 46, 30, CYAN, a_grid, align="r")

    # 无穷乘积 + 展开
    pt = ex["product"]
    a_prod = a * env(t, pt, split + 0.3, 0.6, 0.6)
    if a_prod > 0.003:
        sc = lerp(1.15, 1.0, eout((t - pt) / 0.8))
        draw_math(c, r"$q\prod_{n=1}^{\infty}(1-q^n)^2\,(1-q^{11n})^2$", W / 2 + 150, 270, 54, MAGENTA,
                  a_prod, scale=sc)
        text(c, "MODULAR FORM  ·  WEIGHT 2  ·  LEVEL 11", W / 2 + 150, 350, 18, "raj", MAGENTA,
             0.6 * a_prod, track=4)
    s0, s1 = ex["series"]
    if t > s0 and a_prod > 0.003:
        terms = []
        for i, v in enumerate(DATA["series"][:13], start=1):
            if v == 0:
                continue
            qq = "q" if i == 1 else f"q^{{{i}}}"
            mag = "" if abs(v) == 1 else str(abs(v))
            sign = "-" if v < 0 else "+"
            terms.append(("" if not terms and v > 0 else sign + " ") + mag + qq)
        tex = "$= " + " ".join(terms) + r" + \cdots$"
        draw_math(c, tex, W / 2, 420, 36, mix(MAGENTA, WHITE, 0.35), a_prod, reveal=eout((t - s0) / (s1 - s0)))

    # 表格
    lift = smooth((t - pt) / 1.0)
    ty = lerp(790, 520, lift)
    rows, cols = table_layout(ty)
    a_tab = a * env(t, ex["n_reveal"][0] - 0.6, split + 0.3, 0.5, 0.6)
    if a_tab > 0.003:
        sc0, sc1 = ex["scan"]
        scan = smooth((t - sc0) / (sc1 - sc0 - 0.4)) if t > sc0 else 0.0
        off = int((scan ** 1.6) * (len(ROWS) - len(EX_PRIMES)))
        primes = [r["p"] for r in ROWS[off: off + len(EX_PRIMES)]]
        labels = [("p", r"$p$", WHITE), ("N", r"$N_p$", CYAN), ("d", r"$p - N_p$", GOLD), ("a", r"$a_p$", MAGENTA)]
        for key, tex, rgb in labels:
            ra = a_tab
            if key == "d":
                ra *= env(t, ex["diff_row"], None, 0.4)
            if key == "a":
                ra *= env(t, ex["a_reveal"][0] - 0.3, None, 0.4)
            draw_math(c, tex, 300, rows[key] - 12, 32, rgb, ra, align="r")
        c.drawLine(330, ty - 34, 1820, ty - 34, paint(WHITE, 0.15 * a_tab, stroke=1))
        c.drawLine(330, ty + 18, 1820, ty + 18, paint(WHITE, 0.15 * a_tab, stroke=1))
        for k, p in enumerate(primes):
            x = cols[k]
            r = ROW_BY_P[p]
            fresh = off > 0
            text(c, str(p), x, rows["p"], 34, "raj", WHITE, a_tab)
            if fresh or t >= ex["n_reveal"][k]:
                text(c, str(r["N"]), x, rows["N"], 34, "raj", CYAN, a_tab)
            if fresh or t >= ex["a_reveal"][k]:
                text(c, str(r["a"]).replace("-", "−"), x, rows["a"], 34, "raj", MAGENTA, a_tab)
            if fresh or t >= ex["match"][k]:
                text(c, str(p - r["N"]).replace("-", "−"), x, rows["d"], 34, "raj", GOLD, a_tab)
                u = (t - ex["match"][k]) if not fresh else 9
                hi = math.exp(-u * 3)
                c.drawRoundRect(skia.Rect(x - 58, rows["d"] - 40, x + 58, rows["a"] + 14), 10, 10,
                                paint(GOLD, a_tab * (0.35 + 0.65 * hi), stroke=1.5 + 3 * hi))
                text(c, "✓", x, rows["a"] + 52, 26, "sans", GOLD, a_tab * (0.6 + 0.4 * hi))
                if hi > 0.05:
                    c.drawRoundRect(skia.Rect(x - 58, rows["d"] - 40, x + 58, rows["a"] + 14), 10, 10,
                                    paint(GOLD, a_tab * 0.25 * hi))
        if t > sc0:
            n_ok = int(len(EX_PRIMES) + scan * (len(ROWS) - len(EX_PRIMES)))
            done = scan >= 0.999
            text(c, "ALL MATCH  ✓" if done else "VERIFYING …", W / 2, ty + 268, 20, "sans", GOLD, a_tab, track=6)
            text(c, f"{n_ok:,} / {len(ROWS):,}", W / 2, ty + 330, 56, "orb", GOLD, a_tab, track=4)
            text(c, "10000 以内的全部质数", W / 2, ty + 368, 22, "sans", WHITE, 0.65 * a_tab * scan, track=4)

    # L8：左右对照
    a_sp = a * env(t, split + 0.2, None, 0.8)
    if a_sp > 0.003:
        draw_curve(c, 420, 480, 95, a_sp, 1.0, axes=False)
        text(c, "代数方程的计数", 470, 830, 44, "serif", CYAN, a_sp, track=6)
        text(c, "COUNTING SOLUTIONS", 470, 868, 16, "orbm", CYAN, 0.6 * a_sp, track=6)
        draw_tiling(c, 1430, 520, 250, t, a_sp)
        text(c, "模形式", 1430, 830, 44, "serif", MAGENTA, a_sp, track=10)
        text(c, "MODULAR FORM", 1430, 868, 16, "orbm", MAGENTA, 0.6 * a_sp, track=6)
        draw_math(c, r"$=$", W / 2, 520, 110, GOLD, a_sp * (0.8 + 0.2 * math.sin(t * 4)))


def scene_fermat(c, t, S, tl):
    L = S["lines"]
    st = S["start"]
    fe = cues.fermat_schedule(tl)
    a = env(t, st, S["end"], 0.4, 0.5)

    # L0：模性——曲线和圆盘合在一起
    a0 = a * env(t, st, fe["wiles"] + 0.4, 0.4, 0.6)
    if a0 > 0.003:
        u = eout((t - st) / 1.8)
        draw_tiling(c, lerp(1430, W / 2, u), 560, lerp(250, 230, u), t, a0)
        draw_curve(c, lerp(420, W / 2 - 70, u), 560, lerp(105, 95, u), a0, 1.0, rgb=mix(CYAN, GOLD, u), axes=False)
        text(c, "模性", W / 2, 230, 110, "serif", GOLD, a0 * clamp((t - L[0]["start"]) / 0.4), track=30)
        text(c, "MODULARITY", W / 2, 278, 24, "orbm", GOLD, 0.7 * a0 * clamp((t - L[0]["start"] - 0.3) / 0.5),
             track=20)

    # L1：怀尔斯
    a1 = a * env(t, fe["wiles"], fe["fermat"] + 0.2, 0.3, 0.5)
    if a1 > 0.003:
        u = t - fe["wiles"]
        text(c, "1994", W / 2, 640, 300, "orb", CYAN, 0.10 * a1, track=30)
        text(c, scramble("ANDREW WILES", clamp(u / 0.6), t), W / 2, 500, 80, "orb", WHITE, a1, track=10)
        text(c, "安德鲁 · 怀尔斯", W / 2, 575, 42, "serif", CYAN, a1 * clamp((u - 0.3) / 0.5), track=8)
        text(c, "证明：半稳定椭圆曲线都具有模性（谷山–志村猜想）", W / 2, 640, 26, "sans", WHITE,
             0.65 * a1 * clamp((u - 0.8) / 0.5), track=2)

    # L2：费马大定理
    f0, qed = fe["fermat"], fe["qed"]
    a2 = a * env(t, f0, fe["iceberg"] + 0.6, 0.4, 0.6)
    if a2 > 0.003:
        yr = int(lerp(1637, 1994, smooth((t - f0) / (qed - f0))))
        text(c, f"{yr}", W / 2, 230, 64, "orb", GOLD, a2, track=12)
        text(c, "1637  →  1994", W / 2, 275, 20, "sans", GOLD, 0.6 * a2, track=6)
        img = math_img(r"$x^n + y^n = z^n$", 120)
        w, h = img.width() / 2, img.height() / 2
        cx, cy = W / 2, 500
        if t < qed:
            jit = 3 * math.sin(t * 40) * clamp((t - qed + 0.8) / 0.8)
            draw_math(c, r"$x^n + y^n = z^n$", cx + jit, cy, 120, WHITE, a2)
            text(c, "当 n > 2 时，没有正整数解", W / 2, 640, 34, "sans", WHITE, 0.75 * a2, track=4)
        else:
            # 碎裂
            u = t - qed
            nx, ny = 16, 5
            rng = np.random.default_rng(5)
            pr = skia.Paint(AntiAlias=True)
            pr.setColorFilter(skia.ColorFilters.Blend(col(mix(WHITE, GOLD, clamp(u * 2)), 1), skia.BlendMode.kSrcIn))
            pr.setAlphaf(clamp(a2 * (1 - u / 1.6)))
            iw, ih = img.width(), img.height()
            for i in range(nx):
                for j in range(ny):
                    vx, vy, rot = rng.normal(0, 1, 3)
                    sx, sy = i * iw / nx, j * ih / ny
                    dx = (i + 0.5) / nx - 0.5
                    dy = (j + 0.5) / ny - 0.5
                    px = cx - w / 2 + (i + 0.5) * w / nx + (dx * 900 + vx * 160) * eout(u / 1.2)
                    py = cy - h / 2 + (j + 0.5) * h / ny + (dy * 500 + vy * 160) * eout(u / 1.2) + 200 * u * u
                    c.save()
                    c.translate(px, py)
                    c.rotate(rot * 140 * u)
                    c.drawImageRect(img, skia.Rect(sx, sy, sx + iw / nx, sy + ih / ny),
                                    skia.Rect(-w / nx / 2, -h / ny / 2, w / nx / 2, h / ny / 2), SAMPLING, pr)
                    c.restore()
            shockwave(c, t, qed, cx, cy, GOLD)
            s = lerp(1.8, 1.0, eout(u / 0.22))
            aq = clamp(u / 0.12) * env(t, qed, fe["iceberg"] + 0.3, 0.01, 0.5) * a
            c.save()
            c.translate(cx, cy)
            c.scale(s, s)
            text(c, "Q.E.D.", 0, 45, 150, "orb", GOLD, aq, track=12)
            c.restore()
            text(c, "费马大定理  ·  证毕", W / 2, 650, 36, "serif", GOLD, aq * clamp((u - 0.3) / 0.5), track=10)

    # L3：冰山
    ic = fe["iceberg"]
    a3 = a * env(t, ic + 0.2, None, 0.6)
    if a3 > 0.003:
        u = t - ic
        wl = 382
        pts = [(x, wl + 3 * math.sin(x * 0.02 + t * 2)) for x in range(0, W + 1, 16)]
        c.drawPath(polyline(pts), paint(CYAN, 0.7 * a3, stroke=2))
        tip = polyline([(870, wl), (960, wl - 110), (1060, wl)])
        tip.close()
        c.drawPath(tip, paint(GOLD, 0.25 * a3))
        c.drawPath(tip, paint(GOLD, 0.95 * a3, stroke=2.5))
        text(c, "我们看到的：模性定理", 960, wl - 135, 24, "sans", GOLD, a3, track=3)
        reveal_y = wl + 600 * eout(u / 2.6)
        c.save()
        c.clipRect(skia.Rect(0, wl, W, reveal_y))
        ep = paint(CYAN, 0.32 * a3, stroke=1.2)
        path = skia.Path()
        for i, j in ICE_EDGES:
            path.moveTo(*ICE_PTS[i])
            path.lineTo(*ICE_PTS[j])
        c.drawPath(path, ep)
        c.drawPath(polyline([tuple(p) for p in ICE_POLY] + [tuple(ICE_POLY[0])]), paint(CYAN, 0.8 * a3, stroke=2))
        for k in range(0, len(ICE_PTS), 3):
            x, y = ICE_PTS[k]
            glow_dot(c, x, y, 2.2, CYAN, a3 * (0.5 + 0.5 * math.sin(t * 2 + k)))
        for tex, (x, y) in [(r"$\mathrm{GL}_n$", (760, 520)), (r"$\mathrm{Sp}_{2n}$", (1150, 560)),
                            (r"$\mathrm{SO}_n$", (920, 660)), (r"$G_2$", (1270, 700)), (r"$E_8$", (700, 760)),
                            (r"$\mathrm{U}(n)$", (1040, 820)), (r"${}^L G$", (1180, 450))]:
            draw_math(c, tex, x, y, 30, mix(CYAN, WHITE, 0.4), a3 * 0.85)
        c.restore()
        c.drawLine(0, reveal_y, W, reveal_y, paint(CYAN, 0.5 * a3 * (1 - clamp((u - 2.6) / 0.5)), stroke=1.5))
        text(c, "水面之下：整个朗兰兹纲领", 1500, 900, 24, "sans", CYAN, a3 * clamp((u - 1.6) / 0.6), track=3)


def scene_program(c, t, S, tl):
    st = S["start"]
    pr = cues.program_schedule(tl)
    a = env(t, st, S["end"], 0.5, 0.5)

    # 旋转的网络（宏大的设想）
    a_net = a * lerp(1.0, 0.18, smooth((t - pr["columns"]) / 1.0))
    if a_net > 0.003:
        ang = t * 0.25
        ca, sa = math.cos(ang), math.sin(ang)
        P = NET_P
        x = P[:, 0] * ca + P[:, 2] * sa
        z = -P[:, 0] * sa + P[:, 2] * ca
        y = P[:, 1] * math.cos(0.4) - z * math.sin(0.4)
        z2 = P[:, 1] * math.sin(0.4) + z * math.cos(0.4)
        Rn = 380 * lerp(0.6, 1.0, eout((t - st) / 2.5))
        f = 1 / (1.8 - z2 * 0.6)
        sx, sy = W / 2 + x * Rn * f, 520 + y * Rn * f
        for i, j in NET_E:
            d = (z2[i] + z2[j]) / 2
            c.drawLine(sx[i], sy[i], sx[j], sy[j], paint(mix(MAGENTA, CYAN, (d + 1) / 2), a_net * (0.15 + 0.3 * (d + 1) / 2), stroke=1.1))
        for i in range(len(P)):
            glow_dot(c, float(sx[i]), float(sy[i]), 1.6 + 1.6 * (z2[i] + 1) / 2,
                     mix(MAGENTA, CYAN, (z2[i] + 1) / 2), a_net * (0.35 + 0.65 * (z2[i] + 1) / 2))

    # L1：两列
    co = pr["columns"]
    lf = pr["lfunc"]
    a_col = a * env(t, co - 0.1, pr["functor"] + 0.3, 0.5, 0.6)
    up = smooth((t - lf + 0.3) / 0.8)
    if a_col > 0.003:
        u = t - co
        al = a_col * clamp(u / 0.5)
        ar = a_col * clamp((u - 2.2) / 0.5)
        dim = lerp(1.0, 0.45, up)
        lx, rx = 470, 1450
        text(c, "伽罗瓦表示", lx, 200, 60, "serif", CYAN, al * dim, track=8)
        text(c, "GALOIS REPRESENTATIONS", lx, 238, 17, "orbm", CYAN, 0.6 * al * dim, track=6)
        draw_math(c, r"$\rho:\ \mathrm{Gal}(\overline{\mathbb{Q}}/\mathbb{Q}) \to \mathrm{GL}_n(\mathbb{C})$", lx, 310,
                  36, mix(CYAN, WHITE, 0.5), al * dim)
        text(c, "自守表示", rx, 200, 60, "serif", MAGENTA, ar * dim, track=8)
        text(c, "AUTOMORPHIC REPRESENTATIONS", rx, 238, 17, "orbm", MAGENTA, 0.6 * ar * dim, track=6)
        draw_math(c, r"$\pi\ \subset\ L^2(\mathrm{GL}_n(\mathbb{Q}) \backslash \mathrm{GL}_n(\mathbb{A}))$", rx, 310,
                  36, mix(MAGENTA, WHITE, 0.5), ar * dim)
        # 图标：单位根上的伽罗瓦作用 / 模形式的圆盘
        ia = (1 - up)
        cx, cy, r = lx, 470, 95
        n = 7
        pts = [(cx + r * math.cos(2 * math.pi * k / n + t * 0.4), cy + r * math.sin(2 * math.pi * k / n + t * 0.4))
               for k in range(n)]
        c.drawCircle(cx, cy, r, paint(CYAN, 0.35 * al * ia, stroke=1.4))
        for k in range(n):
            j = (3 * k) % n
            c.drawLine(*pts[k], *pts[j], paint(CYAN, 0.4 * al * ia, stroke=1.3))
            glow_dot(c, *pts[k], 4, CYAN, al * ia)
        draw_tiling(c, rx, 470, 100, t, ar * ia)

    # L2：词典
    dc = pr["dictionary"]
    a_d = a * env(t, dc, lf - 0.1, 0.4, 0.4)
    if a_d > 0.003:
        rows = [([r"$\mathrm{tr}\,\rho(\mathrm{Frob}_p)$"], ["赫克特征值 ", r"$a_p(\pi)$"]),
                (["维数 ", r"$n$"], [r"$\mathrm{GL}_n$", " 上的自守表示"]),
                (["导子 ", r"$N$"], ["级 ", r"$N$"])]
        text(c, "一部精确的词典", W / 2, 600, 26, "sans", GOLD, a_d, track=10)
        for k, (lp, rp) in enumerate(rows):
            ra = a_d * clamp((t - dc - k * 0.55) / 0.4)
            y = 680 + k * 66
            rich(c, lp, 850, y, 32, CYAN, ra, align="r")
            rich(c, rp, 1070, y, 32, MAGENTA, ra, align="l")
            u = eout((t - dc - k * 0.55 - 0.2) / 0.6)
            if u > 0:
                c.drawLine(880, y - 11, lerp(880, 1040, u), y - 11, paint(GOLD, ra, stroke=2.2))
                c.drawLine(1040 - (1040 - 880) * (1 - u), y - 11, 1040, y - 11, paint(GOLD, ra * 0.4, stroke=2.2))
                glow_dot(c, lerp(880, 1040, (t * 0.8 + k * 0.3) % 1), y - 11, 3, GOLD, ra * u)

    # L3：L 函数
    a_l = a * env(t, lf - 0.2, pr["functor"] + 0.4, 0.3, 0.6)
    if a_l > 0.003:
        u = t - lf
        cx, cy = W / 2, 560
        for k in range(16):
            r0 = 60 + k * 17
            pts = []
            for i in range(0, 121):
                th = i / 120 * 2 * math.pi
                rr = r0 + 6 * math.sin(th * 3 + k * 0.5 + t * 0.6) + 4 * math.sin(th * 5 - k * 0.3)
                pts.append((cx + rr * math.cos(th) * 1.25, cy + rr * math.sin(th) * 0.95))
            pa = polyline(pts)
            pa.close()
            c.drawPath(pa, paint(GOLD, a_l * 0.22 * eout((u - k * 0.04) / 0.5), stroke=1.5))
        shockwave(c, t, lf, cx, cy, GOLD, 0.7)
        s = lerp(1.25, 1.0, eout(u / 0.5))
        draw_math(c, r"$L(s,\rho) = L(s,\pi)$", cx, cy, 96, mix(GOLD, WHITE, 0.4), a_l * clamp(u / 0.2), scale=s)
        draw_math(c, r"$\prod_p \det\left(1-\rho(\mathrm{Frob}_p)\,p^{-s}\right)^{-1}"
                     r"\ =\ \prod_p \det\left(1-A_p(\pi)\,p^{-s}\right)^{-1}$", cx, cy + 150, 30, GOLD,
                  a_l * 0.75 * clamp((u - 0.8) / 0.6))
        text(c, "L-FUNCTION", cx, cy - 190, 18, "orbm", GOLD, a_l * 0.7, track=8)
        text(c, "共同的指纹", cx, cy - 152, 24, "sans", GOLD, a_l * 0.8, track=8)

    # L4：函子性
    fu = pr["functor"]
    a_f = a * env(t, fu + 0.2, None, 0.6)
    if a_f > 0.003:
        u = t - fu
        text(c, "函子性原理", W / 2, 190, 58, "serif", GOLD, a_f, track=12)
        text(c, "FUNCTORIALITY", W / 2, 228, 18, "orbm", GOLD, 0.65 * a_f, track=10)
        x0, x1, y0, y1 = 720, 1200, 330, 500
        draw_math(c, r"${}^L H$", x0, y0, 54, CYAN, a_f)
        draw_math(c, r"${}^L G$", x1, y0, 54, CYAN, a_f)
        k1 = eout((u - 0.4) / 0.7)
        c.drawLine(x0 + 70, y0, lerp(x0 + 70, x1 - 80, k1), y0, paint(CYAN, a_f, stroke=2.5))
        if k1 >= 1:
            c.drawLine(x1 - 92, y0 - 10, x1 - 80, y0, paint(CYAN, a_f, stroke=2.5))
            c.drawLine(x1 - 92, y0 + 10, x1 - 80, y0, paint(CYAN, a_f, stroke=2.5))
        text(c, "对称群之间的联系", W / 2, y0 - 22, 22, "sans", CYAN, 0.7 * a_f * k1)
        a2 = a_f * clamp((u - 1.1) / 0.5)
        draw_math(c, r"$\pi_H$", x0, y1, 54, MAGENTA, a2)
        draw_math(c, r"$\pi_G$", x1, y1, 54, MAGENTA, a2)
        k2 = eout((u - 1.4) / 0.7)
        for dy in (-5, 5):
            c.drawLine(x0 + 70, y1 + dy, lerp(x0 + 70, x1 - 80, k2), y1 + dy, paint(MAGENTA, a2, stroke=2.2))
        text(c, "自守形式之间的传递", W / 2, y1 + 50, 22, "sans", MAGENTA, 0.7 * a2 * k2)
        dash = skia.DashPathEffect.Make([8, 8], -t * 30)
        for x in (x0, x1):
            c.drawLine(x, y0 + 40, x, y1 - 40, paint(GOLD, 0.6 * a2, stroke=1.6, effect=dash))
        # 群的星座和它们之间的桥
        nodes = [("$\\mathrm{GL}_1$", 330, 660), ("$\\mathrm{GL}_2$", 560, 770), ("$\\mathrm{GL}_3$", 820, 660),
                 ("$\\mathrm{Sp}_4$", 1080, 770), ("$\\mathrm{SO}_5$", 1330, 660), ("$G_2$", 1560, 770),
                 ("$\\mathrm{GL}_n$", 1700, 640), ("$E_8$", 960, 840)]
        bridges = [(0, 1), (1, 2), (3, 4), (2, 6), (5, 6), (1, 7), (3, 7)]
        an = a_f * clamp((u - 2.0) / 0.6)
        for k, (i, j) in enumerate(bridges):
            tb = pr["bridges"][k]
            kb = eout((t - tb) / 0.6)
            if kb <= 0:
                continue
            _, xa, ya = nodes[i]
            _, xb, yb = nodes[j]
            mx, my = (xa + xb) / 2, min(ya, yb) - 70
            pts = []
            for q in range(41):
                v = q / 40 * kb
                pts.append(((1 - v) ** 2 * xa + 2 * v * (1 - v) * mx + v * v * xb,
                            (1 - v) ** 2 * ya + 2 * v * (1 - v) * my + v * v * yb))
            c.drawPath(polyline(pts), paint(GOLD, an * 0.8, stroke=2))
            if kb >= 1:
                v = (t * 0.5 + k * 0.3) % 1
                glow_dot(c, (1 - v) ** 2 * xa + 2 * v * (1 - v) * mx + v * v * xb,
                         (1 - v) ** 2 * ya + 2 * v * (1 - v) * my + v * v * yb, 3, WHITE, an)
        for tex, x, y in nodes:
            c.drawCircle(x, y, 34, paint(BG, an * 0.9))
            c.drawCircle(x, y, 34, paint(mix(CYAN, MAGENTA, x / W), an * 0.8, stroke=1.8))
            draw_math(c, tex, x, y, 28, WHITE, an)


def scene_history(c, t, S, tl):
    st = S["start"]
    hi = cues.history_schedule(tl)
    a = env(t, st, S["end"], 0.5, 0.5)
    focus = hi["focus"]
    gap = 600
    # 相机位置：在 focus 时刻开始移向第 k 个节点
    cam = 0.0
    for k, tf in enumerate(focus):
        if t >= tf:
            cam = lerp(cam, k * gap, smooth((t - tf) / 0.9))
    ph = hi["physics"]
    lift = smooth((t - ph) / 0.9)
    ya = 560 - 330 * lift
    ta = a * lerp(1, 0.35, lift)

    c.save()
    c.translate(W / 2 - cam, 0)
    total = (len(MILESTONES) - 1) * gap
    lp = paint(CYAN, 0.5 * ta, stroke=2)
    c.drawLine(-900, ya, total + 900, ya, lp)
    for k in range(6):
        x = ((t * 420 + k * 380) % (total + 1800)) - 900
        glow_dot(c, x, ya, 3, CYAN, ta * 0.8)
    for k, (yr, title, desc, badge) in enumerate(MILESTONES):
        x = k * gap
        d = abs(x - cam) / gap
        act = clamp(1 - d)
        na = ta * (0.35 + 0.65 * act)
        hit = math.exp(-max(0, t - focus[k]) * 3) if t >= focus[k] else 0
        glow_dot(c, x, ya, 7 + 6 * act, GOLD if act > 0.5 else CYAN, na)
        if hit > 0.01:
            c.drawCircle(x, ya, 20 + 120 * (1 - hit), paint(GOLD, hit * ta, stroke=2))
        if lift < 0.99:
            sa = na * (1 - lift)
            text(c, yr, x, ya - 60, lerp(52, 92, act), "orb", WHITE, sa, track=6)
            text(c, title, x, ya + 85, lerp(30, 42, act), "serif", mix(CYAN, GOLD, act), sa, track=4)
            text(c, desc, x, ya + 135, 26, "sans", WHITE, 0.75 * sa * act)
            if badge:
                bw = text_width(badge, 16, "orbm", 5) + 40
                c.drawRoundRect(skia.Rect(x - bw / 2, ya + 162, x + bw / 2, ya + 196), 17, 17,
                                paint(GOLD, 0.8 * sa * act, stroke=1.5))
                text(c, badge, x, ya + 186, 16, "orbm", GOLD, sa * act, track=5)
    c.restore()

    # 2024：近千页、九位作者
    f24 = focus[-1]
    a24 = a * env(t, f24 + 0.6, ph + 0.4, 0.4, 0.5)
    if a24 > 0.003:
        u = t - f24 - 0.6
        pages = int(1000 * smooth(u / 3.0))
        wp = text(c, f"{pages:,}", W / 2 - 240, 830, 56, "orb", GOLD, a24, track=4)
        text(c, "≈", W / 2 - 240 - wp / 2 - 18, 826, 50, "sans", GOLD, a24, align="r")
        text(c, "PAGES", W / 2 - 240, 862, 16, "orbm", GOLD, 0.7 * a24, track=8)
        for k in range(9):
            on = clamp((u - k * 0.25) / 0.3)
            glow_dot(c, W / 2 + 90 + k * 38, 812, 7, GOLD if on > 0.5 else GREY, a24 * (0.3 + 0.7 * on))
        text(c, "9 AUTHORS", W / 2 + 242, 862, 16, "orbm", GOLD, 0.7 * a24, track=8)

    # 物理：电磁对偶
    if lift > 0.003:
        ap = a * lift
        cx, cy, d = W / 2, 620, 120
        rot = smooth((t - ph - 1.2) / 2.0) * 90
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        clip = skia.Path()
        clip.addCircle(0, 0, 300)
        c.clipPath(clip, doAntiAlias=True)
        for k in range(-6, 7):
            cc = k * 70
            r = math.hypot(d, cc)
            c.drawCircle(0, cc, r, paint(CYAN, 0.45 * ap, stroke=1.5))
        for k in range(1, 8):
            x0 = d * (1 + 0.18 * k * k / 4) + d * 0.05
            r = math.sqrt(max(x0 * x0 - d * d, 1))
            for s in (-1, 1):
                c.drawCircle(s * x0, 0, r, paint(MAGENTA, 0.45 * ap, stroke=1.5))
        c.restore()
        c.drawCircle(cx, cy, 300, paint(WHITE, 0.4 * ap, stroke=1.5))
        glow_dot(c, cx - d * math.cos(math.radians(rot)), cy - d * math.sin(math.radians(rot)), 7, CYAN, ap)
        glow_dot(c, cx + d * math.cos(math.radians(rot)), cy + d * math.sin(math.radians(rot)), 7, MAGENTA, ap)
        text(c, "量子场论 · 电磁对偶", W / 2 - 560, 560, 44, "serif", WHITE, ap, track=6)
        text(c, "KAPUSTIN – WITTEN  2006", W / 2 - 560, 600, 18, "orbm", CYAN, 0.7 * ap, track=6)
        rich(c, ["S-对偶  ", r"$\leftrightarrow$", "  几何朗兰兹"], W / 2 + 560, 580, 36, GOLD, ap)


def scene_finale(c, t, S, tl):
    st = S["start"]
    fi = cues.finale_schedule(tl)
    a = env(t, st, S["end"] + 1, 0.5, 0.5)
    words = [("数论", "NUMBER THEORY", CYAN, (560, 340)), ("几何", "GEOMETRY", TEAL, (1360, 340)),
             ("表示论", "REPRESENTATION THEORY", MAGENTA, (560, 720)), ("量子物理", "QUANTUM PHYSICS", VIOLET, (1360, 720))]
    c0, c1 = fi["converge"]
    cv = ein(clamp((t - c0) / (c1 - c0)))
    for k, (zh, en, rgb, (x, y)) in enumerate(words):
        tw = fi["words"][k]
        aw = a * clamp((t - tw) / 0.35) * (1 - clamp((cv - 0.85) / 0.15))
        if aw <= 0.003:
            continue
        ang = cv * 2.2
        dx, dy = x - W / 2, y - 520
        rx = dx * math.cos(ang) - dy * math.sin(ang)
        ry = dx * math.sin(ang) + dy * math.cos(ang)
        px, py = W / 2 + rx * (1 - cv), 520 + ry * (1 - cv)
        s = lerp(1.0, 0.2, cv) * lerp(1.3, 1.0, eout((t - tw) / 0.4))
        c.drawCircle(px, py, 120 * s, paint(rgb, 0.45 * aw, stroke=1.6))
        ob = t * 1.2 + k
        glow_dot(c, px + 120 * s * math.cos(ob), py + 120 * s * math.sin(ob), 4, rgb, aw)
        c.save()
        c.translate(px, py)
        c.scale(s, s)
        text(c, zh, 0, 18, 64, "serif", rgb, aw, track=8)
        text(c, en, 0, 58, 15, "orbm", rgb, 0.7 * aw, track=5)
        c.restore()
        if cv > 0:
            for q in range(1, 10):
                cq = ein(clamp((t - c0 - q * 0.03) / (c1 - c0)))
                ang = cq * 2.2
                rx = dx * math.cos(ang) - dy * math.sin(ang)
                ry = dx * math.sin(ang) + dy * math.cos(ang)
                glow_dot(c, W / 2 + rx * (1 - cq), 520 + ry * (1 - cq), 3, rgb, aw * (1 - q / 10))

    # 汇聚成一点光
    ac = a * env(t, c1 - 0.15, fi["letter"] + 0.8, 0.15, 0.8)
    if ac > 0.003:
        u = t - c1
        flash(c, t, c1, 0.5)
        shockwave(c, t, c1, W / 2, 520, GOLD, 0.8)
        c.save()
        c.translate(W / 2, 520)
        c.rotate(t * 8)
        for k in range(36):
            ang = k * math.pi / 18
            r1 = 700 * (0.6 + 0.4 * math.sin(k * 1.7 + t))
            c.drawLine(60 * math.cos(ang), 60 * math.sin(ang), r1 * math.cos(ang), r1 * math.sin(ang),
                       paint(GOLD, ac * 0.25, stroke=1.2))
        c.restore()
        pr = 70 + 12 * math.sin(t * 5)
        c.drawCircle(W / 2, 520, pr * 3, paint(shader=radial(W / 2, 520, pr * 3, GOLD, ac * 0.8)))
        c.drawCircle(W / 2, 520, pr * 0.5, paint(WHITE, ac))
        text(c, "同一个真理", W / 2, 720, 40, "serif", GOLD, ac * clamp((u - 0.4) / 0.5), track=24)

    # 信和废纸篓
    lt = fi["letter"]
    al = a * env(t, lt, None, 0.6)
    if al > 0.003:
        rise = eout((t - fi["rise"]) / 2.2)
        drift = smooth((t - lt) / 3.0) * (1 - rise)
        bx, by = 1330, 640
        ab = al * (1 - smooth((t - fi["rise"]) / 1.0))
        if ab > 0.003:
            pb = paint(GREY, 0.8 * ab, stroke=2.5)
            c.drawPath(polyline([(bx - 120, by - 150), (bx - 90, by + 150), (bx + 90, by + 150), (bx + 120, by - 150)]), pb)
            c.drawLine(bx - 140, by - 150, bx + 140, by - 150, pb)
            for k in range(-2, 3):
                c.drawLine(bx + k * 40, by - 120, bx + k * 32, by + 125, paint(GREY, 0.35 * ab, stroke=1.5))
            text(c, "WASTE BASKET", bx, by + 200, 16, "orbm", GREY, 0.6 * ab, track=6)
        cx = lerp(820, 980, drift) + lerp(0, W / 2 - 820, rise)
        cy = 540 - 110 * rise
        rot = lerp(-4, 8, drift) * (1 - rise)
        s = lerp(0.72, 0.85, rise)
        glow = mix(CYAN, GOLD, rise)
        if rise > 0:
            c.drawCircle(cx, cy, 520, paint(shader=radial(cx, cy, 520, GOLD, 0.3 * rise * al)))
        scr = None
        dc = fi["decode"]
        if t > dc:
            scr = clamp((t - dc) / 3.0)
        draw_letter(c, cx, cy, s, rot, al, 1.0, 17, glow=glow, salutation=True, scr=scr)


def scene_end(c, t, S, tl):
    R = cues.end_reveal(tl)
    a = 1 - smooth((t - S["end"] + 1.8) / 1.6)
    if t < R:
        u = clamp((t - S["start"]) / (R - S["start"]))
        text(c, scramble("朗兰兹纲领", 0, t, CJK_GLYPHS), W / 2, H / 2 + 10, 150, "serif", GOLD, 0.6 * u, track=26)
        return
    flash(c, t, R, 0.7)
    shockwave(c, t, R, W / 2, H / 2 - 30, mix(GOLD, WHITE, 0.4))
    burst(c, t, R, W / 2, H / 2 - 30, GOLD)
    streak(c, t, R, W / 2, H / 2 - 70, GOLD)
    title_block(c, t, R, W / 2, H / 2 + 10, a, scr_t=True)
    ac = a * clamp((t - R - 2.4) / 0.8)
    text(c, "旁白配音：通义千问 Qwen3-TTS（Kai · Ethan）", W / 2, 880, 22, "sans", WHITE, 0.55 * ac, track=3)
    text(c, "画面与配乐：Python 程序生成（skia · numpy）", W / 2, 915, 22, "sans", WHITE, 0.55 * ac, track=3)


SCENES = {
    "letter": scene_letter, "title": scene_title, "worlds": scene_worlds, "example": scene_example,
    "fermat": scene_fermat, "program": scene_program, "history": scene_history, "finale": scene_finale,
    "end": scene_end,
}


# ---------------------------------------------------------------- 字幕
def subtitles(c, t, tl):
    for S in tl.scenes:
        for ln in S["lines"]:
            if ln["quote"] or not ln["sub"]:
                continue
            a = env(t, ln["start"] - 0.12, ln["end"] + 0.25, 0.15, 0.2)
            if a <= 0.003:
                continue
            lines = wrap_balanced(ln["sub"], 40, "sans", 1560)
            y0 = 1000 - (len(lines) - 1) * 52
            for i, s in enumerate(lines):
                y = y0 + i * 52
                text(c, s, W / 2, y, 40, "sans", BG, 0.75 * a, p=paint(BG, 0.75 * a, stroke=7))
                text(c, s, W / 2, y, 40, "sans", WHITE, a)


# ---------------------------------------------------------------- 合成一帧
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.main = skia.Surface(W, H)
        self.fg = skia.Surface(W, H)
        self.half = skia.Surface(W // 2, H // 2)
        self.small0 = skia.Surface(W // 4, H // 4)
        self.glow = skia.Surface(W // 4, H // 4)
        self.glitches = cues.glitch_times(tl)
        vs = skia.Surface(W, H)
        vc = vs.getCanvas()
        vc.clear(0)
        vc.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            skia.Point(W / 2, H / 2), W * 0.72, [col(BG, 0), col(BG, 0), col((0, 0, 0), 0.75)], [0, 0.55, 1])))
        sub = skia.Rect(0, H - 230, W, H)
        vc.drawRect(sub, skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, H - 230), skia.Point(0, H)], [col((0, 0, 0), 0), col((0, 0, 0), 0.55)])))
        self.vignette = vs.makeImageSnapshot()

    def bloom(self, img, canvas, a):
        """辉光：缩到 1/4（分两次对半缩，等于盒式滤波，细线不闪），两种半径模糊后叠在一起，再放大垫在画面下面。

        CPU 上的 skia 做全分辨率的加法混合（kPlus）非常慢，所以加法只在小图上做，
        放大后用普通的 srcOver 画在前景「下面」——前景本身清晰，光晕从背后透出来。
        """
        lin = skia.SamplingOptions(skia.FilterMode.kLinear)
        hc = self.half.getCanvas()
        hc.clear(0)
        hc.drawImageRect(img, skia.Rect(0, 0, W // 2, H // 2), lin)
        c0 = self.small0.getCanvas()
        c0.clear(0)
        c0.drawImageRect(self.half.makeImageSnapshot(), skia.Rect(0, 0, W // 4, H // 4), lin)
        small = self.small0.makeImageSnapshot()
        gc = self.glow.getCanvas()
        gc.clear(0)
        for sigma, strength in ((2.5, 0.9), (9.0, 0.8)):
            sp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma), BlendMode=skia.BlendMode.kPlus)
            sp.setAlphaf(clamp(strength * a))
            gc.drawImage(small, 0, 0, skia.SamplingOptions(), sp)
        canvas.drawImageRect(self.glow.makeImageSnapshot(), skia.Rect(0, 0, W, H), lin)

    def frame(self, t):
        time_hint[0] = t
        tl = self.tl
        S = tl.scene_at(t)
        sid = S["id"]
        warp = letter_warp(t, tl)
        mc = self.main.getCanvas()
        background(mc, t, sid, warp)

        fc = self.fg.getCanvas()
        fc.clear(0)
        hud_a = 0.0 if sid in ("title", "end") else env(t, S["start"] + 0.3, S["end"], 0.6, 0.3)
        hud(fc, t, sid, TAGS.get(sid, ""), hud_a)
        SCENES[sid](fc, t, S, tl)
        fg = self.fg.makeImageSnapshot()

        # 转场：每个场景开头轻微放大回落
        u = clamp((t - S["start"]) / 0.6)
        z = 1 + 0.035 * (1 - eout(u)) if sid not in ("title",) else 1.0
        dst = skia.Rect(W / 2 - W / 2 * z, H / 2 - H / 2 * z, W / 2 + W / 2 * z, H / 2 + H / 2 * z)
        mc.save()
        if z != 1.0:
            mc.translate(W / 2, H / 2)
            mc.scale(z, z)
            mc.translate(-W / 2, -H / 2)
        self.bloom(fg, mc, 1.0)
        mc.restore()
        mc.drawImageRect(fg, dst, skia.SamplingOptions(skia.FilterMode.kLinear))

        mc.drawImage(self.vignette, 0, 0)
        self.glitch(mc, t)
        subtitles(mc, t, tl)
        # 标题和片尾加电影遮幅
        bars = 0.0
        for sid2 in ("title", "end"):
            s2 = tl.scene(sid2)
            bars = max(bars, env(t, s2["start"] - 0.4, s2["end"] + 0.3, 0.5, 0.6))
        if bars > 0:
            bh = 92 * bars
            mc.drawRect(skia.Rect(0, 0, W, bh), paint((0, 0, 0), 1))
            mc.drawRect(skia.Rect(0, H - bh, W, H), paint((0, 0, 0), 1))
        end = tl.scene("end")["end"]
        if t > end - 1.2:
            mc.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), smooth((t - end + 1.2) / 1.1)))
        if t < 0.6:
            mc.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), 1 - smooth(t / 0.6)))

        return self.main.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)

    CHANNELS = [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    ]

    def glitch(self, mc, t):
        """故障效果：RGB 三个通道错开，再随机横向错位几条。字幕在这之后画，不受影响。"""
        g = 0.0
        for tg in self.glitches:
            if 0 <= t - tg < 0.32:
                g = max(g, (1 - (t - tg) / 0.32) ** 2)
        if g < 0.02:
            return
        img = self.main.makeImageSnapshot()
        dx = 4 + 18 * g
        mc.clear(skia.ColorBLACK)
        for k, off in enumerate((dx, 0, -dx)):
            p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
            p.setColorFilter(skia.ColorFilters.Matrix(self.CHANNELS[k]))
            mc.drawImage(img, off, 0, skia.SamplingOptions(), p)
        rng = np.random.default_rng(int(t * 1000))
        snap = self.main.makeImageSnapshot()
        for _ in range(int(2 + 6 * g)):
            y = float(rng.integers(0, H - 40))
            h = float(rng.integers(6, 40))
            sh = float(rng.integers(-60, 60) * g)
            mc.save()
            mc.clipRect(skia.Rect(0, y, W, y + h))
            mc.drawImage(snap, sh, 0)
            mc.restore()


def encode_range(tl_data, f0, f1, out, crf=18):
    from cues import Timeline
    tl = Timeline(tl_data)
    r = Renderer(tl)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(tl.fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-x264-params", "keyint=60", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        proc.stdin.write(r.frame(f / tl.fps).tobytes())
        if (f - f0) % 150 == 0:
            print(f"  [{out.name}] {f - f0}/{f1 - f0}", file=sys.stderr, flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg 编码失败")
    return out


def still(tl_data, t, out):
    from cues import Timeline
    from PIL import Image
    tl = Timeline(tl_data)
    arr = Renderer(tl).frame(t)
    Image.fromarray(arr[..., :3]).save(out)
