"""片头：一把随机的点落在直线上 → 直线卷成圆 → 旋转起来，重心画出螺线 → 片名。"""

import math

import numpy as np
import skia

from dist import X1
from gfx import (CYAN, GOLD, H, W, WHITE, clamp, colored_dots, colored_segments, draw_math, env, eout,
                 font, glow_dot, lerp, mix, paint, ramp, shockwave, smooth, stroke_xy, text)
from scene import Scene

N = 1100
XS = X1.quantiles(N, seed=3)
_rng = np.random.default_rng(11)
HU = _rng.random(N) ** 0.9            # 在密度曲线下面的高度比例（铺成一座沙丘）
DROP = 0.4 + 4.4 * _rng.random(N)      # 每个点开始下落的时刻
JIT = _rng.normal(0, 1, N)
VAL = np.clip((XS + 2.2) / 4.4, 0, 1)   # 颜色按样本的位置

CX, CY, R = W / 2, 500, 300           # 卷成的圆
LINE_Y = CY + R                       # 直线就是圆底下的切线
HSCALE = 360                          # 密度 → 像素高度

T_FALL = (0.4, 5.6)
T_CURVE = 6.4
T_ROLL = (10.0, 13.2)
T_SPIN = (13.6, 21.0)
T_TITLE = 21.4
DUR = 30.0


def freq(u):
    """“频率” t：卷成圆时等于 1，然后加速到 9。"""
    return 1 + 8 * ramp(u, T_SPIN[0], T_SPIN[1], lambda x: x * x * (3 - 2 * x))


def curl_pos(s, kappa):
    """一条直线卷向半径 1/kappa 的圆：弧长 s 处的点（相对切点，屏幕坐标 y 向下）。"""
    if kappa < 1e-6:
        return s, np.zeros_like(s)
    return np.sin(kappa * s) / kappa, -(1 - np.cos(kappa * s)) / kappa


def particles(c, u):
    a = 1 - smooth((u - T_TITLE - 0.2) / 0.5)
    if a <= 0.003:
        return
    k_roll = ramp(u, *T_ROLL)
    t = freq(u)
    # 沙丘里的位置
    px = CX + R * XS
    hy = HU * X1.pdf(XS) * HSCALE
    py = LINE_Y - 6 - hy
    # 下落
    fall = np.clip((u - DROP) / 0.75, 0, 1)
    vis = fall > 0
    y_now = -60 + (py + 60) * fall ** 2   # 匀加速下落
    if k_roll <= 0:
        sz = 3.6
        colored_dots(c, px[vis], y_now[vis], VAL[vis], a, sz)
        # 刚落地的点闪一下
        just = vis & (fall >= 1) & (u - DROP - 0.75 < 0.25)
        if just.any():
            colored_dots(c, px[just], py[just], VAL[just], a * 0.8, 9)
        return
    # 卷成圆：弧长 s = t·x·R，沙丘高度收成圆环上的一点抖动
    kappa = k_roll / R
    s = t * XS * R
    lx, ly = curl_pos(s, kappa)
    h = lerp(hy, 7 * JIT, eout(k_roll))
    # 沙丘高度朝圆心方向（外法线 (sin κs, cos κs) 的反方向）
    nx = np.sin(kappa * s)
    ny = np.cos(kappa * s)
    qx = CX + lx - nx * h
    qy = LINE_Y + ly - ny * h - 6 * (1 - k_roll)
    colored_dots(c, qx, qy, VAL, a, 3.6)
    # 旋转时的拖尾
    if u > T_SPIN[0]:
        dt = 0.10
        t0 = freq(u - dt)
        ang0 = t0 * XS - math.pi / 2
        x0 = CX + (R + 7 * JIT) * np.cos(ang0)
        y0 = CY - (R + 7 * JIT) * np.sin(ang0)
        colored_segments(c, x0, y0, qx, qy, VAL, 0.35 * a * ramp(u, T_SPIN[0], T_SPIN[0] + 1), 2.2)


def centroid(c, u):
    a = env(u, T_SPIN[0] - 0.4, T_TITLE + 0.3, 0.8, 0.4)
    if a <= 0.003:
        return
    t = freq(u)
    rot = np.exp(-1j * math.pi / 2)
    ts = np.linspace(1, t, 400)
    z = X1.cf(ts) * rot
    xs, ys = CX + R * z.real, CY - R * z.imag
    stroke_xy(c, xs, ys, GOLD, 0.25 * a, 9)
    stroke_xy(c, xs, ys, mix(GOLD, WHITE, 0.3), 0.9 * a, 2.6)
    zc = complex(z[-1])
    gx, gy = CX + R * zc.real, CY - R * zc.imag
    c.drawLine(CX, CY, gx, gy, paint(GOLD, 0.45 * a, stroke=1.6))
    glow_dot(c, gx, gy, 7, GOLD, a, halo=6)
    c.drawCircle(CX, CY, 3, paint(WHITE, 0.5 * a))


def density_curve(c, u):
    a = env(u, T_CURVE, T_ROLL[0] + 0.6, 0.6, 0.6)
    if a <= 0.003:
        return
    prog = ramp(u, T_CURVE, T_CURVE + 2.2)
    xs = np.linspace(-3, 3, 500)
    n = max(2, int(500 * prog))
    px = CX + R * xs[:n]
    py = LINE_Y - 6 - X1.pdf(xs[:n]) * HSCALE
    stroke_xy(c, px, py, CYAN, 0.25 * a, 10)
    stroke_xy(c, px, py, mix(CYAN, WHITE, 0.4), a, 2.6)
    draw_math(c, "f(x)", CX - R * 0.75 - 40, LINE_Y - X1.pdf(-0.75) * HSCALE - 40, 34, CYAN, a * prog)


def line(c, u):
    a = env(u, 0.2, T_ROLL[0] + 0.4, 1.0, 0.6)
    if a <= 0.003:
        return
    grow = eout(clamp(u / 1.6))
    x0, x1 = CX - 900 * grow, CX + 900 * grow
    sh = skia.GradientShader.MakeLinear([skia.Point(x0, 0), skia.Point(x1, 0)],
                                        [paint(CYAN, 0).getColor(), paint(CYAN, 0.6 * a).getColor(),
                                         paint(CYAN, 0.6 * a).getColor(), paint(CYAN, 0).getColor()],
                                        [0, 0.2, 0.8, 1])
    c.drawRect(skia.Rect(x0, LINE_Y - 1, x1, LINE_Y + 1), paint(CYAN, 1, shader=sh))
    for k in range(-3, 4):
        x = CX + R * k
        if abs(x - CX) <= 900 * grow:
            c.drawLine(x, LINE_Y - 6, x, LINE_Y + 6, paint(CYAN, 0.5 * a, stroke=1.4))
            draw_math(c, str(k) if k >= 0 else f"-{-k}", x, LINE_Y + 40, 24, CYAN, 0.55 * a)


def ring_guide(c, u):
    a = env(u, T_ROLL[1] - 0.5, T_TITLE + 0.3, 0.8, 0.4)
    if a <= 0.003:
        return
    c.drawCircle(CX, CY, R, paint(CYAN, 0.10 * a, stroke=16))
    c.drawCircle(CX, CY, R, paint(CYAN, 0.35 * a, stroke=1.5))


# ---------------------------------------------------------------- 片名
TITLE_RING = np.linspace(0, 2 * np.pi, 720, endpoint=False)
_r2 = np.random.default_rng(5)
TR_J = _r2.normal(0, 1, 720)
TR_SP = 0.25 + 0.75 * _r2.random(720)


def title(c, u):
    k = u - T_TITLE
    if k < -0.1:
        return
    a = env(u, T_TITLE, DUR, 0.2, 1.2)
    cx, cy = W / 2, H / 2 - 30
    shockwave(c, k / 1.6, cx, cy, GOLD, 1.0)
    # 炸开的点变成一圈缓慢旋转的光环
    r = 560 + 30 * TR_J
    spread = eout(clamp(k / 1.4))
    ang = TITLE_RING + 0.06 * k * TR_SP + 0.4 * (1 - spread)
    rr = R * (1 - spread) + r * spread
    xs = cx + rr * np.cos(ang)
    ys = cy + rr * np.sin(ang) * lerp(1.0, 0.42, spread)
    vals = (TITLE_RING / (2 * np.pi) + 0.03 * k) % 1.0
    colored_dots(c, xs, ys, vals, a * 0.8, 3.2)
    # 片名
    ta = a * smooth(clamp((k - 0.15) / 0.7))
    s = "当概率开始旋转"
    size = 128
    f = font("serif", size)
    w = sum(f.measureText(ch) for ch in s) + 18 * (len(s) - 1)
    x = cx - w / 2
    for i, ch in enumerate(s):
        kk = clamp((k - 0.1 - i * 0.07) / 0.6)
        if kk > 0:
            y = cy + 40 + 30 * (1 - eout(kk))
            c.drawString(ch, x, y, f, paint(GOLD, 0.35 * ta * smooth(kk), stroke=6))
            c.drawString(ch, x, y, f, paint(WHITE, ta * smooth(kk)))
        x += f.measureText(ch) + 18
    sa = a * smooth(clamp((k - 1.2) / 0.8))
    text(c, "WHEN  PROBABILITY  SPINS", cx, cy - 110, 24, "orbm", CYAN, 0.8 * sa, track=10)
    c.drawRect(skia.Rect(cx - 260 * sa, cy + 86, cx + 260 * sa, cy + 88), paint(GOLD, 0.7 * sa))
    text(c, "用概率论重新理解傅里叶变换、傅里叶级数，以及更多", cx, cy + 142, 34, "sans", WHITE, 0.85 * sa)


def draw(c, u):
    line(c, u)
    ring_guide(c, u)
    density_curve(c, u)
    particles(c, u)
    centroid(c, u)
    title(c, u)


def tone(u):
    """旋转时一个随频率升高的音，音量跟着重心离圆心的距离 |φ(t)|。"""
    k = np.clip((u - T_SPIN[0]) / (T_SPIN[1] - T_SPIN[0]), 0, 1)
    t = 1 + 8 * k * k * (3 - 2 * k)
    amp = np.abs(X1.cf(t)) * np.clip((u - T_SPIN[0] + 0.5) / 1.0, 0, 1) * np.clip((T_TITLE - u) / 0.4, 0, 1)
    return 110 * 2 ** (np.log2(t) * 0.9), 0.22 * amp


_land = np.sort(DROP + 0.75)
SFX = [(0.0, "drone_in", {})]
SFX += [(float(x), "drop", {"seed": i}) for i, x in enumerate(_land[::9])]
SFX += [(T_CURVE, "chime", {"f": 660}), (T_ROLL[0], "whoosh", {"dur": 3.0}), (T_SPIN[0], "riser", {"dur": T_TITLE - T_SPIN[0]}),
        (T_TITLE, "impact", {}), (T_TITLE + 0.1, "shimmer", {"dur": 4.0})]

CAPS = [
    (1.6, 5.8, "随机，是撒在直线上的一把点。"),
    (6.6, 9.8, "点越密的地方，密度 $f(x)$ 越高。"),
    (10.2, 13.4, "把直线卷到圆上……"),
    (13.8, 17.2, "再让它们旋转起来：$x$ 越大，转得越快。"),
    (17.4, 21.0, "所有点的重心画出一条曲线——它就是傅里叶变换。"),
]

SCENES = [Scene("open", DUR, draw, CAPS, SFX, tone=tone, theme=0, hud=0.0, fade_in=0.0, fade_out=1.0, bed=0)]
