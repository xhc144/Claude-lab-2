"""第 1 章 绕圈的重心：特征函数 φ(t) = E[e^{itX}] 是把样本绕到单位圆上之后的重心，也就是密度的傅里叶变换。"""

import math

import numpy as np
import skia

from dist import X1
from gfx import (CYAN, GOLD, GREY, MAGENTA, RED, WHITE, Disk, Plot, arrow, colored_dots, colored_segments,
                 dashed, draw_math, env, eout, glow_dot, lerp, mix, paint, panel, ramp, readout, stroke_xy,
                 text)
from scene import Scene

N = 1300
XS = X1.quantiles(N, seed=21)
_rng = np.random.default_rng(4)
HU = _rng.random(N) ** 0.9
JIT = _rng.normal(0, 1, N)
STAG = _rng.random(N)
VAL = np.clip((XS + 2.2) / 4.4, 0, 1)
ONE = int(np.argmin(np.abs(XS - 1.05)))      # 单独拿出来演示的那个点

LINE = Plot(110, 300, 830, 560, -3, 3, 0, 0.75)     # 左边：直线和密度
PHI = Plot(150, 690, 820, 860, 0, 10, 0, 1.05)      # 左下：|φ(t)|
DISK = Disk(1370, 505, 265)

# 时间点（场景内，秒）
T_LINE = 4.0
T_ONE = 13.2
T_FLY = 17.0
T_CEN = 25.0
T_SWEEP = 35.5
T_FOURIER = 56.0
T_WIDTH = 67.5
T_MGF = 82.0
T_INV = 96.0
DUR = 113.0


def freq(u):
    """每个时刻的频率 t。"""
    if u < T_SWEEP:
        return 1.6
    if u < T_SWEEP + 1.6:                       # 先退回 t = 0
        return lerp(1.6, 0.0, ramp(u, T_SWEEP, T_SWEEP + 1.6))
    if u < T_SWEEP + 3.0:
        return 0.0
    if u < T_FOURIER:                           # 再慢慢加到 10
        return 10 * ramp(u, T_SWEEP + 3.0, T_FOURIER - 1.0, lambda x: x * x * (3 - 2 * x) * 0.4 + 0.6 * x)
    if u < T_FOURIER + 2.5:
        return lerp(10, 2.2, ramp(u, T_FOURIER, T_FOURIER + 2.5))
    return 2.2


def scale(u):
    """分布的宽度倍数 a（X 换成 aX）。"""
    if u < T_WIDTH + 1:
        return 1.0
    k1 = ramp(u, T_WIDTH + 1.0, T_WIDTH + 3.5)
    k2 = ramp(u, T_WIDTH + 8.0, T_WIDTH + 10.5)
    k3 = ramp(u, T_WIDTH + 12.0, T_WIDTH + 14.0)
    a = lerp(1.0, 0.45, k1)
    a = lerp(a, 2.0, k2)
    return lerp(a, 1.0, k3)


def pile_xy(a):
    px = LINE.sx(XS * a)
    py = LINE.sy(HU * X1.pdf(XS) / a * 0.98) - 3
    return px, py


def circle_xy(t, a=1.0, r_jit=6.0):
    ang = t * a * XS
    r = DISK.R + r_jit * JIT
    return DISK.cx + r * np.cos(ang), DISK.cy - r * np.sin(ang)


def fly_progress(u):
    return np.clip((u - T_FLY - 2.6 * STAG) / 1.3, 0, 1)


# ---------------------------------------------------------------- 左边：直线上的样本和密度
def draw_line(c, u, a_scale):
    a = env(u, T_LINE, DUR, 0.8, 0.6) * (1 - env(u, T_MGF, T_INV, 0.7, 0.6))
    if a <= 0.003:
        return
    LINE.axes(c, a, CYAN, xticks=range(-3, 4))
    for k in range(-3, 4):
        draw_math(c, str(k) if k >= 0 else f"-{-k}", float(LINE.sx(k)), float(LINE.sy(0)) + 34, 22, CYAN, 0.5 * a)
    draw_math(c, "x", LINE.R + 26, float(LINE.sy(0)) + 8, 28, CYAN, 0.7 * a, align="l")
    xs = np.linspace(-3, 3, 400)
    inv = u > T_INV
    k_inv = ramp(u, T_INV, T_INV + 1.0)
    fx = X1.pdf(xs / a_scale) / a_scale
    LINE.fill(c, xs, fx, CYAN, a * (1 - 0.7 * k_inv))
    if inv:
        LINE.curve(c, xs, fx, GREY, 0.5 * a, 1.6, effect=dashed(8, 7))
    else:
        LINE.curve(c, xs, fx, CYAN, a, 2.6)
    draw_math(c, "f(x)", float(LINE.sx(-0.75 * a_scale)) - 30, float(LINE.sy(X1.pdf(-0.75) / a_scale)) - 26, 30,
              CYAN, a * (1 - k_inv))


def draw_particles(c, u, t, a_scale):
    a = env(u, T_LINE + 0.3, DUR, 1.2, 0.6) * (1 - ramp(u, T_MGF - 0.5, T_MGF + 0.3))
    if a <= 0.003:
        return
    px, py = pile_xy(a_scale)
    cx, cy = circle_xy(t, a_scale)
    fp = fly_progress(u)
    on_line = fp <= 0
    # 还在直线上的点
    if on_line.any():
        appear = np.clip((u - T_LINE - 0.3 - 1.5 * STAG) / 0.6, 0, 1)
        sel = on_line & (appear > 0)
        colored_dots(c, px[sel], py[sel], VAL[sel], a, 3.4)
    # 飞行中 / 到达圆上
    mv = ~on_line
    if mv.any():
        k = eout(fp[mv])
        mx = (px[mv] + cx[mv]) / 2
        my = np.minimum(py[mv], cy[mv]) - 160
        qx = (1 - k) ** 2 * px[mv] + 2 * (1 - k) * k * mx + k * k * cx[mv]
        qy = (1 - k) ** 2 * py[mv] + 2 * (1 - k) * k * my + k * k * cy[mv]
        colored_dots(c, qx, qy, VAL[mv], a, 3.4)
        # 旋转时的拖尾
        if T_SWEEP + 3 < u < T_FOURIER + 2.5 or (T_WIDTH < u < T_MGF):
            t0 = freq(u - 0.08)
            x0, y0 = circle_xy(t0, scale(u - 0.08))
            colored_segments(c, x0[mv], y0[mv], qx, qy, VAL[mv], 0.4 * a, 2.0)
        # 留在直线上的淡影
        colored_dots(c, px, py, VAL, 0.18 * a * float(np.mean(fp)), 2.4)


def draw_one(c, u):
    """单独演示一个点 x 怎么被送到 e^{itx}。"""
    a = env(u, T_ONE, T_CEN, 0.6, 0.8)
    if a <= 0.003:
        return
    t = 1.6
    x = XS[ONE]
    px, py = float(LINE.sx(x)), float(LINE.sy(0))
    glow_dot(c, px, py, 7, GOLD, a, halo=5)
    draw_math(c, "x", px, py + 40, 30, GOLD, a)
    k = ramp(u, T_ONE + 0.8, T_ONE + 2.6)
    ang = t * x * k
    tx, ty = DISK.cx + DISK.R * math.cos(ang), DISK.cy - DISK.R * math.sin(ang)
    # 从 1 出发转过角度 tx 的弧
    rect = skia.Rect(DISK.cx - 70, DISK.cy - 70, DISK.cx + 70, DISK.cy + 70)
    c.drawArc(rect, 0, -math.degrees(ang), False, paint(GOLD, 0.9 * a, stroke=3))
    c.drawLine(DISK.cx, DISK.cy, tx, ty, paint(GOLD, 0.6 * a, stroke=2))
    c.drawLine(DISK.cx, DISK.cy, DISK.cx + DISK.R, DISK.cy, paint(GOLD, 0.35 * a, stroke=1.5))
    draw_math(c, "tx", DISK.cx + 95 * math.cos(ang / 2), DISK.cy - 95 * math.sin(ang / 2) + 10, 30, GOLD, a * k)
    glow_dot(c, tx, ty, 8, GOLD, a * k, halo=5)
    draw_math(c, "e^{itx}", tx + 20, ty - 20, 34, GOLD, a * k, align="l")
    # 曲线箭头
    if k > 0:
        n = 60
        ss = np.linspace(0, min(1, k * 1.2), n)
        mx, my = (px + tx) / 2, min(py, ty) - 220
        bx = (1 - ss) ** 2 * px + 2 * (1 - ss) * ss * mx + ss * ss * tx
        by = (1 - ss) ** 2 * (py - 14) + 2 * (1 - ss) * ss * my + ss * ss * ty
        stroke_xy(c, bx, by, GOLD, 0.5 * a, 2, effect=dashed(9, 7, -u * 30))
    draw_math(c, r"x\ \mapsto\ e^{itx}", 960, 165, 50, WHITE, a * env(u, T_ONE + 1.0, T_CEN, 0.5, 0.5),
              reveal=ramp(u, T_ONE + 1.0, T_ONE + 2.4), glow=0.25)


def draw_disk(c, u, t, a_scale):
    a = env(u, T_ONE - 0.5, T_MGF + 0.3, 0.8, 0.8)
    if a <= 0.003:
        return
    DISK.draw(c, a)
    readout(c, "t =", f"{t:5.2f}", DISK.cx + DISK.R - 30, DISK.cy + DISK.R + 70, a, MAGENTA, 28)
    if abs(a_scale - 1) > 0.01 or (T_WIDTH < u < T_MGF):
        readout(c, r"a =", f"{a_scale:4.2f}", DISK.cx - DISK.R - 60, DISK.cy + DISK.R + 70, a, CYAN, 28)


def draw_centroid(c, u, t, a_scale):
    a = env(u, T_CEN, T_MGF, 0.8, 0.5)
    if a <= 0.003:
        return
    z = complex(X1.cf(t * a_scale))
    gx, gy = DISK.xy(z)
    gx, gy = float(gx), float(gy)
    # 平均：从一些点牵向重心的细线
    k = env(u, T_CEN + 0.2, T_CEN + 4.5, 0.6, 1.5)
    if k > 0.01:
        idx = np.arange(0, N, 9)
        x0, y0 = circle_xy(t, a_scale, 0)
        x0, y0 = x0[idx], y0[idx]
        grow = ramp(u, T_CEN + 0.2, T_CEN + 2.0)
        colored_segments(c, x0, y0, x0 + (gx - x0) * grow, y0 + (gy - y0) * grow, VAL[idx], 0.25 * k, 1.2)
    # 重心的轨迹
    if u > T_SWEEP + 3:
        t_end = t
        ts = np.linspace(0, t_end, max(2, int(60 * t_end) + 2))
        zz = X1.cf(ts)
        tx, ty = DISK.xy(zz)
        ta = a * (1 - ramp(u, T_FOURIER + 0.5, T_FOURIER + 2.5))
        stroke_xy(c, tx, ty, GOLD, 0.22 * ta, 9)
        stroke_xy(c, tx, ty, mix(GOLD, WHITE, 0.3), 0.85 * ta, 2.4)
    c.drawLine(DISK.cx, DISK.cy, gx, gy, paint(GOLD, 0.7 * a, stroke=2.4))
    glow_dot(c, gx, gy, 9, GOLD, a, halo=6)
    draw_math(c, r"\varphi(t)", gx + 18, gy - 18, 34, GOLD, a * ramp(u, T_CEN + 1.5, T_CEN + 2.5), align="l")
    readout(c, r"|\varphi(t)| =", f"{abs(z):5.3f}", DISK.cx + DISK.R - 30, DISK.cy + DISK.R + 112, a, GOLD, 28)
    # 公式
    fa = env(u, T_CEN + 2.0, T_FOURIER, 0.6, 0.5)
    draw_math(c, r"\varphi(t)\ =\ \mathbb{E}\,\left[\,e^{itX}\,\right]", 960, 170, 56, WHITE, fa,
              reveal=ramp(u, T_CEN + 2.0, T_CEN + 3.6), glow=0.25)


def draw_phi_plot(c, u, t, a_scale):
    a = env(u, T_SWEEP + 2.5, T_MGF, 0.8, 0.5)
    ai = ramp(u, T_INV - 0.6, T_INV + 0.6)
    a = max(a, ai * env(u, T_INV - 0.6, DUR, 0.6, 0.6))
    if a <= 0.003:
        return
    PHI.axes(c, a, GREY)
    for v in (0, 2, 4, 6, 8, 10):
        draw_math(c, str(v), float(PHI.sx(v)), PHI.B + 32, 22, GREY, 0.6 * a)
    draw_math(c, "t", PHI.R + 22, PHI.B + 8, 28, MAGENTA, 0.8 * a, align="l")
    draw_math(c, "1", PHI.L - 22, float(PHI.sy(1)) + 8, 22, GREY, 0.6 * a)
    c.drawLine(PHI.L - 5, float(PHI.sy(1)), PHI.L + 5, float(PHI.sy(1)), paint(GREY, 0.5 * a, stroke=1.4))
    draw_math(c, r"|\varphi(t)|", PHI.L + 10, PHI.T - 8, 28, GOLD, 0.9 * a, align="l")
    ts = np.linspace(0, 10, 500)
    if u < T_FOURIER:
        n = int(np.searchsorted(ts, t)) + 1
        if n > 1:
            PHI.curve(c, ts[:n], np.abs(X1.cf(ts[:n])), GOLD, a, 2.6)
            glow_dot(c, float(PHI.sx(t)), float(PHI.sy(abs(X1.cf(t)))), 5, GOLD, a)
    else:
        PHI.curve(c, ts, np.abs(X1.cf(ts * a_scale)), GOLD, a, 2.6)
        if T_WIDTH < u < T_MGF:
            PHI.curve(c, ts, np.abs(X1.cf(ts)), GREY, 0.45 * a, 1.4, effect=dashed(6, 6))
    if u > T_INV:
        T = inv_T(u)
        sel = ts <= T
        PHI.fill(c, ts[sel], np.abs(X1.cf(ts[sel])), MAGENTA, a)
        c.drawLine(float(PHI.sx(T)), PHI.T, float(PHI.sx(T)), PHI.B, paint(MAGENTA, 0.8 * a, stroke=2))
        draw_math(c, "T", float(PHI.sx(T)), PHI.T - 10, 26, MAGENTA, a)


# ---------------------------------------------------------------- 傅里叶变换
def draw_fourier(c, u):
    a = env(u, T_FOURIER + 0.3, T_WIDTH, 0.6, 0.6)
    if a <= 0.003:
        return
    rv = ramp(u, T_FOURIER + 0.3, T_FOURIER + 2.3)
    draw_math(c, r"\varphi(t)\ =\ \mathbb{E}\,\left[\,e^{itX}\,\right]\ =\ \int_{-\infty}^{\infty} e^{itx}\,f(x)\,dx",
              960, 175, 54, WHITE, a, reveal=rv, glow=0.25)
    k = ramp(u, T_FOURIER + 6.0, T_FOURIER + 7.0)
    if k > 0:
        x0, x1 = 1060, 1440
        c.drawRect(skia.Rect(x0, 222, x0 + (x1 - x0) * k, 225), paint(MAGENTA, a))
        text(c, "密度 f 的傅里叶变换", (x0 + x1) / 2, 266, 30, "sans", MAGENTA, a * k)


def draw_width_tag(c, u, a_scale):
    a = env(u, T_WIDTH + 0.5, T_MGF - 0.2, 0.6, 0.5)
    if a <= 0.003:
        return
    draw_math(c, r"X\ \to\ aX\qquad \varphi_{aX}(t)=\varphi_X(at)", 960, 175, 48, WHITE, a,
              reveal=ramp(u, T_WIDTH + 0.5, T_WIDTH + 2.0), glow=0.2)


# ---------------------------------------------------------------- 矩母函数 vs 特征函数
def draw_mgf(c, u):
    a = env(u, T_MGF, T_INV, 0.7, 0.6)
    if a <= 0.003:
        return
    k = u - T_MGF
    # 左：e^{sx} 往上冲出画面
    panel(c, 150, 230, 760, 600, a, RED)
    text(c, "矩母函数", 530, 290, 34, "bold", WHITE, a)
    draw_math(c, r"M(s)=\mathbb{E}\,[e^{sX}]", 530, 360, 44, WHITE, a)
    P = Plot(220, 400, 840, 780, -3, 3, 0, 20)
    P.axes(c, a, GREY)
    xs = np.linspace(-3, 3, 300)
    s = 1.0
    grow = ramp(u, T_MGF + 0.8, T_MGF + 3.0)
    ys = np.minimum(np.exp(s * xs), 40)
    n = max(2, int(300 * grow))
    P.curve(c, xs[:n], np.minimum(ys[:n], 20.5), RED, a, 3)
    draw_math(c, r"e^{sx}", float(P.sx(1.6)), float(P.sy(12)), 36, RED, a * grow)
    blink = 0.6 + 0.4 * math.sin(k * 6)
    text(c, "可能是 ∞", 530, 815, 30, "bold", RED, a * ramp(u, T_MGF + 3.0, T_MGF + 3.6) * blink)
    # 右：e^{itx} 只在圆上转
    panel(c, 1010, 230, 760, 600, a, CYAN)
    text(c, "特征函数", 1390, 290, 34, "bold", WHITE, a)
    draw_math(c, r"\varphi(t)=\mathbb{E}\,[e^{itX}]=M(it)", 1390, 360, 44, WHITE, a)
    D = Disk(1390, 600, 165)
    D.draw(c, a, labels=False)
    ang = k * 1.7
    for j, x in enumerate((-1.6, -0.7, 0.4, 1.2, 2.1)):
        th = ang * x
        glow_dot(c, D.cx + D.R * math.cos(th), D.cy - D.R * math.sin(th), 5, mix(CYAN, MAGENTA, j / 4), a, 4)
    text(c, "永远在单位圆上", 1390, 815, 30, "bold", CYAN, a * ramp(u, T_MGF + 6.5, T_MGF + 7.2))
    arrow(c, 925, 530, 995, 530, GOLD, a * ramp(u, T_MGF + 6.0, T_MGF + 6.8), 3, 18)
    draw_math(c, r"s\to it", 960, 505, 30, GOLD, a * ramp(u, T_MGF + 6.0, T_MGF + 6.8))


# ---------------------------------------------------------------- 反演
XG = np.linspace(-3, 3, 360)
TG = np.linspace(0, 10, 2001)
_dt = TG[1] - TG[0]
_integrand = np.real(np.exp(-1j * np.outer(TG, XG)) * X1.cf(TG)[:, None])
_cum = np.cumsum(_integrand, 0) * _dt - 0.5 * _dt * (_integrand[0][None, :] + _integrand)
F_T = _cum / np.pi            # f_T(x) = (1/π) ∫_0^T Re(e^{-itx} φ(t)) dt


def inv_T(u):
    return 0.15 + 9.8 * ramp(u, T_INV + 1.5, T_INV + 13.0, lambda x: x ** 1.6)


def draw_inversion(c, u):
    a = env(u, T_INV + 0.3, DUR, 0.6, 0.6)
    if a <= 0.003:
        return
    T = inv_T(u)
    j = int(np.clip(T / _dt, 1, len(TG) - 1))
    fT = F_T[j]
    LINE.curve(c, XG, fT, GOLD, 0.25 * a, 9)
    LINE.curve(c, XG, fT, mix(GOLD, WHITE, 0.3), a, 2.8)
    draw_math(c, r"f(x)\ =\ \dfrac{1}{2\pi}\int_{-\infty}^{\infty} e^{-itx}\,\varphi(t)\,dt", 1370, 420, 52, WHITE, a,
              reveal=ramp(u, T_INV + 0.3, T_INV + 2.0), glow=0.25)
    text(c, "傅里叶反演", 1370, 290, 34, "bold", GOLD, a)
    readout(c, "T =", f"{T:5.2f}", 1250, 600, a * ramp(u, T_INV + 1.5, T_INV + 2.5), MAGENTA, 30)
    draw_math(c, r"f_T(x)=\frac{1}{2\pi}\int_{-T}^{T} e^{-itx}\,\varphi(t)\,dt", 1370, 720, 40, GOLD,
              a * ramp(u, T_INV + 3.0, T_INV + 4.0))


def draw(c, u):
    t = freq(u)
    a_scale = scale(u)
    draw_line(c, u, a_scale)
    draw_phi_plot(c, u, t, a_scale)
    draw_disk(c, u, t, a_scale)
    draw_particles(c, u, t, a_scale)
    draw_one(c, u)
    draw_centroid(c, u, t, a_scale)
    draw_fourier(c, u)
    draw_width_tag(c, u, a_scale)
    draw_mgf(c, u)
    draw_inversion(c, u)


def tone(u):
    t = np.array([freq(x) for x in u[::480]])
    a = np.array([scale(x) for x in u[::480]])
    t = np.interp(np.arange(len(u)), np.arange(0, len(u), 480)[:len(t)], t)
    a = np.interp(np.arange(len(u)), np.arange(0, len(u), 480)[:len(a)], a)
    amp = np.abs(X1.cf(t * a)) * ((u > T_SWEEP + 2.5) & (u < T_MGF - 0.5))
    return 110 * 2 ** (np.log2(1 + t) * 1.1), 0.2 * amp


CAPS = [
    (4.4, 8.6, "$X$ 是一个随机变量：每抽一次，直线上就落下一个点。"),
    (8.8, 12.9, "把片头那一幕放慢，一步一步看。"),
    (13.4, 18.8, "先选定一个频率 $t$，把直线上的点 $x$ 送到单位圆上角度为 $tx$ 的位置。"),
    (19.0, 24.6, "所有点都这样做：$x$ 越大，转过的角度越大。"),
    (25.4, 30.4, "再求圆上所有点的重心，也就是 $e^{itX}$ 的平均值。"),
    (30.6, 35.2, "这个重心记作 $\\varphi(t)$，叫做 $X$ 的特征函数。"),
    (35.8, 41.4, "$t=0$ 时，所有点都叠在 $1$ 上，重心就是 $1$。"),
    (41.6, 48.0, "$t$ 渐渐变大，点开始各转各的，重心向圆心塌缩。"),
    (48.2, 55.6, "重心随 $t$ 走出的这条轨迹，就是特征函数的全貌。"),
    (56.4, 61.8, "把平均写成积分：每个 $x$ 按密度 $f(x)$ 加权，转到 $e^{itx}$。"),
    (62.0, 67.2, "这正是密度 $f$ 的傅里叶变换。在概率论里，它叫特征函数。"),
    (67.8, 74.8, "把分布压窄：点要转得更快才散得开，$|\\varphi|$ 变宽了。"),
    (75.0, 81.6, "把分布拉宽：稍一转就散开，$|\\varphi|$ 立刻变窄。一边窄，另一边就宽。"),
    (82.4, 88.6, "第 1 集的矩母函数用实数 $s$：$e^{sX}$ 指数增长，柯西分布的矩母函数根本不存在。"),
    (88.8, 95.6, "把 $s$ 换成 $it$，增长变成了旋转：点永远在单位圆上，所以 $|\\varphi(t)|\\leq 1$，对任何分布都存在。"),
    (96.4, 103.0, "反过来，知道了每个频率下的重心，就能把密度一点不差地还原出来。"),
    (103.2, 112.0, "用到的频率越高，还原得越细：这是傅里叶反演公式。重心曲线记住了分布的一切。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_LINE + 0.3, "shimmer", {"dur": 2.0}),
    (T_ONE + 1.0, "chime", {"f": 880}),
    (T_FLY, "whoosh", {"dur": 3.2}), (T_FLY + 0.4, "shimmer", {"dur": 3.0}),
    (T_CEN + 0.2, "swell", {"dur": 2.5}), (T_CEN + 2.0, "chime", {"f": 660}),
    (T_SWEEP, "rewind", {"dur": 1.6}),
    (T_FOURIER + 0.3, "chime", {"f": 990}), (T_FOURIER + 6.0, "chime", {"f": 1320}),
    (T_WIDTH + 0.5, "whoosh", {"dur": 1.5}), (T_WIDTH + 1.0, "pitch", {"dur": 2.5, "up": False}),
    (T_WIDTH + 8.0, "pitch", {"dur": 2.5, "up": True}),
    (T_MGF, "glitch", {}), (T_MGF + 1.0, "riser", {"dur": 2.0}), (T_MGF + 3.0, "alarm", {}),
    (T_MGF + 6.0, "chime", {"f": 880}),
    (T_INV, "whoosh", {"dur": 1.5}), (T_INV + 0.3, "chime", {"f": 740}), (T_INV + 1.5, "riser", {"dur": 11.5}),
]

SCENES = [Scene("ch1", DUR, draw, CAPS, SFX, tone=tone, chapter=("01", "绕圈的重心", "THE CENTER OF A WINDING"),
                theme=1, bed=1)]
