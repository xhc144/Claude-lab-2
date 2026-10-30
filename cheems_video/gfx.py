"""绘图基础：颜色、画笔、样条路径、渐变、文字、缓动函数（基于 skia-python）。"""
from __future__ import annotations

import math
import os

import numpy as np
import skia

W, H = 1920, 1080
FPS = 30

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("CHEEMS_FONT_DIR", os.path.join(HERE, "fonts"))


# ---------------------------------------------------------------- 数学 / 缓动
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in_out(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t * t * t


def ease_out_back(t, s=1.70158):
    t = clamp(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_elastic(t):
    t = clamp(t)
    if t in (0, 1):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def wave(t, period=1.0, phase=0.0):
    return math.sin((t / period + phase) * 2 * math.pi)


def noise1(t, seed=0):
    """平滑的一维噪声（几个正弦叠加），用于手持镜头抖动、颤抖等。"""
    s = seed * 12.9898
    return (math.sin(t * 1.7 + s) * 0.5 + math.sin(t * 3.1 + s * 1.3) * 0.3 + math.sin(t * 7.3 + s * 0.7) * 0.2)


def keyframes(t, keys, ease=ease_in_out):
    """keys: [(时间, 值)]，值可以是数或元组；在相邻关键帧之间缓动插值。"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            if isinstance(v0, (tuple, list)):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]


# ---------------------------------------------------------------- 颜色
def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def C(c, a=1.0):
    """颜色转 skia 的 ARGB 整数。c 可以是 '#rrggbb' 或 (r,g,b) 0-255。"""
    if isinstance(c, int):
        return c
    r, g, b = hex2rgb(c) if isinstance(c, str) else c[:3]
    return skia.ColorSetARGB(int(clamp(a) * 255), int(r), int(g), int(b))


def mix(c1, c2, t):
    a = hex2rgb(c1) if isinstance(c1, str) else c1
    b = hex2rgb(c2) if isinstance(c2, str) else c2
    return tuple(int(lerp(x, y, clamp(t))) for x, y in zip(a, b))


def shade(c, k):
    """k<0 变暗，k>0 变亮。"""
    return mix(c, (0, 0, 0), -k) if k < 0 else mix(c, (255, 255, 255), k)


# ---------------------------------------------------------------- 画笔
def fill(color="#000000", a=1.0, blur=0.0, shader=None, blend=None):
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setColor(C(color, a))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(clamp(a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def stroke(color="#000000", w=2.0, a=1.0, cap="round", blur=0.0, shader=None, blend=None):
    p = fill(color, a, blur, shader, blend)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                    "square": skia.Paint.kSquare_Cap}[cap])
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def layer_paint(a=1.0, blend=None, blur=0.0):
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    if blend is not None:
        p.setBlendMode(blend)
    if blur > 0:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    return p


# ---------------------------------------------------------------- 渐变
def _cc(c):
    """渐变颜色项：'#hex'、(r,g,b)、(颜色, 透明度) 都可以。"""
    if isinstance(c, int):
        return c
    if isinstance(c, str):
        return C(c)
    if len(c) == 2:
        return C(c[0], c[1])
    if len(c) == 4:
        return C(c[:3], c[3])
    return C(c)


def lin(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [_cc(c) for c in colors], pos)


def rad(center, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), max(r, 0.01), [_cc(c) for c in colors], pos)


# ---------------------------------------------------------------- 路径
def spline(pts, closed=True, tension=1.0):
    """Catmull-Rom 样条转三次贝塞尔。"""
    path = skia.Path()
    n = len(pts)
    if n < 2:
        return path
    P = [tuple(p) for p in pts]
    path.moveTo(*P[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % n] if closed else P[min(i + 1, n - 1)]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        path.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        path.close()
    return path


def poly(pts, closed=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    if closed:
        path.close()
    return path


def oval(cx, cy, rx, ry):
    path = skia.Path()
    path.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return path


def rrect(x, y, w, h, r):
    path = skia.Path()
    path.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return path


def rect(x, y, w, h):
    return skia.Rect.MakeXYWH(x, y, w, h)


def mirror_pts(pts):
    """把右半边的点（x>=0，从上到下）镜像成完整闭合轮廓。"""
    right = list(pts)
    left = [(-x, y) for x, y in reversed(pts)]
    if right[0][0] == 0:
        left = left[:-1]
    if right[-1][0] == 0:
        left = left[1:]
    return right + left


def scale_pts(pts, sx, sy=None, dx=0.0, dy=0.0):
    sy = sx if sy is None else sy
    return [(x * sx + dx, y * sy + dy) for x, y in pts]


def draw_shape(c, path, color, outline=None, ow=0.0, shade_color=None, shade_off=(0.0, 0.0), hi=None, a=1.0):
    """卡通填色：底色 + 内侧阴影（偏移的底色剪出月牙阴影）+ 描边。"""
    if shade_color is not None:
        c.drawPath(path, fill(shade_color, a))
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        p2 = skia.Path(path)
        p2.offset(*shade_off)
        c.drawPath(p2, fill(color, a))
        if hi is not None:
            hp, hc, ha = hi
            c.drawPath(hp, fill(hc, ha * a, blur=6))
        c.restore()
    else:
        c.drawPath(path, fill(color, a))
    if outline is not None and ow > 0:
        c.drawPath(path, stroke(outline, ow, a))


# ---------------------------------------------------------------- 文字
_TF = {}
_FONTS = {
    "kuaile": "ZCOOLKuaiLe-Regular.ttf",
    "huangyou": "ZCOOLQingKeHuangYou-Regular.ttf",
    "brush": "MaShanZheng-Regular.ttf",
    "hand": "LongCang-Regular.ttf",
    "sans": "NotoSansSC[wght].ttf",
}


def typeface(name="sans", weight=None):
    key = (name, weight)
    if key not in _TF:
        fn = os.path.join(FONT_DIR, _FONTS[name])
        if not os.path.exists(fn):
            fn = fn.replace("[wght]", "%5Bwght%5D")
        tf = skia.Typeface.MakeFromFile(fn)
        if weight is not None:
            coords = skia.FontArguments.VariationPosition.Coordinates(
                [skia.FontArguments.VariationPosition.Coordinate(0x77676874, float(weight))])
            pos = skia.FontArguments.VariationPosition(coords)
            args = skia.FontArguments()
            args.setVariationDesignPosition(pos)
            tf = tf.makeClone(args)
        _TF[key] = tf
    return _TF[key]


_FONT_CACHE = {}


def font(name="sans", size=40, weight=None):
    key = (name, int(size * 4), weight)
    if key not in _FONT_CACHE:
        f = skia.Font(typeface(name, weight), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


def has_glyphs(name, text):
    tf = typeface(name)
    return all(g != 0 for ch, g in zip(text, tf.textToGlyphs(text)) if not ch.isspace())


def text_width(s, f):
    return f.measureText(s)


def draw_text(c, s, x, y, size=40, name="sans", color="#ffffff", a=1.0, align="center", weight=None,
              outline=None, ow=0.0, oa=1.0, shadow=None, glow=None, spacing=0.0):
    f = font(name, size, weight)
    if spacing:
        widths = [f.measureText(ch) + spacing for ch in s]
        total = sum(widths) - spacing
    else:
        total = f.measureText(s)
    if align == "center":
        x0 = x - total / 2
    elif align == "right":
        x0 = x - total
    else:
        x0 = x

    def _draw(paint, dx=0.0, dy=0.0):
        if spacing:
            xx = x0
            for ch, wch in zip(s, widths):
                c.drawString(ch, xx + dx, y + dy, f, paint)
                xx += wch
        else:
            c.drawString(s, x0 + dx, y + dy, f, paint)

    if glow is not None:
        gc, gr, ga = glow
        _draw(fill(gc, ga * a, blur=gr))
    if shadow is not None:
        sc, sdx, sdy, sblur, sa = shadow
        _draw(fill(sc, sa * a, blur=sblur), sdx, sdy)
    if outline is not None and ow > 0:
        _draw(stroke(outline, ow, oa * a))
    _draw(fill(color, a))
    return total


# ---------------------------------------------------------------- 杂项
def image_from_array(arr):
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)


def make_noise_images(n=4, size=512, seed=7):
    rng = np.random.default_rng(seed)
    imgs = []
    for _ in range(n):
        v = rng.integers(0, 256, (size, size), dtype=np.uint8)
        arr = np.stack([v, v, v, np.full_like(v, 255)], -1)
        imgs.append(image_from_array(arr))
    return imgs


def offscreen(w, h):
    return skia.Surface(int(w), int(h))
