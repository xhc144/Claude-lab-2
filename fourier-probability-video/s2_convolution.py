"""第 2 章 独立：加法变成乘法。X+Y 的密度是卷积；到圆上看，角度相加就是旋转相乘，
独立让“乘积的平均 = 平均的乘积”，于是 φ_{X+Y} = φ_X φ_Y —— 卷积定理。最后回到二项分布和泊松分布。"""

import math

import numpy as np
import skia
from scipy.special import erf, gammaln
from scipy.stats import norm

from gfx import (CYAN, GOLD, GREY, MAGENTA, WHITE, Disk, Plot, dots, draw_math, env, glow_dot, mix, paint,
                 panel, ramp, readout, smooth, stroke_xy, text)
from scene import Scene

# X ~ U(-1, 1)，Y ~ N(0.9, 0.35²)
MY, SY = 0.9, 0.35


def fX(x):
    return np.where(np.abs(x) <= 1, 0.5, 0.0)


def fY(y):
    return np.exp(-0.5 * ((y - MY) / SY) ** 2) / (SY * math.sqrt(2 * math.pi))


def fS(s):
    """U(-1,1) 与正态的卷积。"""
    return 0.25 * (erf((s + 1 - MY) / (SY * math.sqrt(2))) - erf((s - 1 - MY) / (SY * math.sqrt(2))))


def cfX(t):
    t = np.asarray(t, float)
    return np.where(np.abs(t) < 1e-9, 1.0, np.sin(t) / np.where(np.abs(t) < 1e-9, 1, t)) + 0j


def cfY(t):
    t = np.asarray(t, float)
    return np.exp(1j * MY * t - 0.5 * (SY * t) ** 2)


N = 720
_rng = np.random.default_rng(8)
XS = (np.arange(N) + 0.5) / N * 2 - 1
YS = norm.ppf((np.arange(N) + 0.5) / N, MY, SY)
XS = XS[_rng.permutation(N)]
YS = YS[_rng.permutation(N)]
SS = XS + YS
HX, HY, HS = _rng.random(N), _rng.random(N), _rng.random(N) ** 0.9
STAG = _rng.random(N)

PX = Plot(110, 220, 830, 330, -3, 3, 0, 0.62)
PY = Plot(110, 400, 830, 530, -3, 3, 0, 1.2)
PS = Plot(110, 640, 830, 800, -3, 3, 0, 0.55)
DISK = Disk(1370, 500, 250)

T_A = 4.0
T_DROP = 8.0
T_B = 17.0
T_C = 33.0
T_D = 49.0
T_E = 60.5
DUR = 75.0


def lines(c, u):
    a = env(u, T_A, T_C + 0.4, 0.8, 0.6)
    if a <= 0.003:
        return
    xs = np.linspace(-3, 3, 400)
    for P, f, rgb, lab, la in ((PX, fX, CYAN, "X", 1), (PY, fY, MAGENTA, "Y", 1), (PS, fS, GOLD, "X+Y", None)):
        k = a if la else a * ramp(u, T_DROP + 1.0, T_DROP + 3.0)
        P.axes(c, a, rgb)
        if la or u > T_DROP + 1:
            P.fill(c, xs, f(xs), rgb, k * 0.8)
            P.curve(c, xs, f(xs), rgb, k, 2.4)
        draw_math(c, lab, P.L - 20, float(P.sy(0)) - 12, 32, rgb, a, align="r")
    for k in range(-3, 4):
        draw_math(c, str(k) if k >= 0 else f"-{-k}", float(PS.sx(k)), PS.B + 32, 22, GOLD, 0.5 * a)


def particles(c, u):
    a = env(u, T_A + 0.4, T_C + 0.4, 0.8, 0.6)
    if a <= 0.003:
        return
    x0, y0 = PX.sx(XS), PX.sy(HX * 0.5) - 2
    x1, y1 = PY.sx(YS), PY.sy(HY * fY(YS)) - 2
    xs, ys = PS.sx(SS), PS.sy(HS * fS(SS)) - 2
    k = np.clip((u - T_DROP - 6.0 * STAG) / 1.0, 0, 1)
    k = k * k
    stay = k <= 0
    if stay.any():
        dots(c, x0[stay], y0[stay], CYAN, a, 3.2)
        dots(c, x1[stay], y1[stay], MAGENTA, a, 3.2)
    mv = (k > 0) & (k < 1)
    if mv.any():
        # 两个点一起往下落，在落点处合成一个
        kk = k[mv]
        dots(c, x0[mv] + (xs[mv] - x0[mv]) * kk, y0[mv] + (ys[mv] - y0[mv]) * kk, CYAN, a, 3.4)
        dots(c, x1[mv] + (xs[mv] - x1[mv]) * kk, y1[mv] + (ys[mv] - y1[mv]) * kk, MAGENTA, a, 3.4)
    done = k >= 1
    if done.any():
        dots(c, xs[done], ys[done], GOLD, a, 3.4)
        flash = done & (u - T_DROP - 6.0 * STAG - 1.0 < 0.25)
        if flash.any():
            dots(c, xs[flash], ys[flash], WHITE, a * 0.8, 8)
        dots(c, x0[done], y0[done], CYAN, 0.25 * a, 2.4)
        dots(c, x1[done], y1[done], MAGENTA, 0.25 * a, 2.4)
    fa = env(u, T_A + 5.6, T_B, 0.6, 0.6)
    draw_math(c, r"f_{X+Y}(s)\ =\ \int\, f_X(x)\,f_Y(s-x)\,dx", 1370, 420, 50, WHITE, fa,
              reveal=ramp(u, T_A + 5.6, T_A + 7.2), glow=0.2)
    text(c, "卷积", 1370, 520, 40, "bold", GOLD, fa * ramp(u, T_A + 7.5, T_A + 8.2))
    text(c, "CONVOLUTION", 1370, 560, 18, "orbm", GOLD, 0.6 * fa * ramp(u, T_A + 7.5, T_A + 8.2), track=6)


# ---------------------------------------------------------------- 一对点：先转 tx，再转 ty
PAIR = int(np.argmin(np.abs(XS - 0.55) + np.abs(YS - 1.15)))
T_PAIR = 1.15


def pair_demo(c, u):
    a = env(u, T_B, T_C, 0.8, 0.6)
    if a <= 0.003:
        return
    DISK.draw(c, a)
    x, y = XS[PAIR], YS[PAIR]
    t = T_PAIR
    # 在左边标出这一对
    glow_dot(c, float(PX.sx(x)), float(PX.sy(0)), 7, CYAN, a, 5)
    glow_dot(c, float(PY.sx(y)), float(PY.sy(0)), 7, MAGENTA, a, 5)
    glow_dot(c, float(PS.sx(x + y)), float(PS.sy(0)), 7, GOLD, a * ramp(u, T_B + 4.0, T_B + 4.6), 5)
    k1 = ramp(u, T_B + 0.6, T_B + 2.2)
    k2 = ramp(u, T_B + 2.6, T_B + 4.2)
    a1 = t * x * k1
    a2 = t * y * k2
    cx, cy, R = DISK.cx, DISK.cy, DISK.R
    for rr, a0, sweep, rgb in ((80, 0, a1, CYAN), (110, a1, a2, MAGENTA)):
        if abs(sweep) > 1e-3:
            rect = skia.Rect(cx - rr, cy - rr, cx + rr, cy + rr)
            c.drawArc(rect, -math.degrees(a0), -math.degrees(sweep), False, paint(rgb, a, stroke=4))
    p1 = (cx + R * math.cos(a1), cy - R * math.sin(a1))
    c.drawLine(cx, cy, *p1, paint(CYAN, 0.6 * a, stroke=2))
    glow_dot(c, *p1, 8, CYAN, a * k1, 5)
    draw_math(c, "e^{itx}", p1[0] + 18, p1[1] - 6, 32, CYAN, a * k1, align="l")
    draw_math(c, "tx", cx + 105 * math.cos(a1 / 2), cy - 105 * math.sin(a1 / 2) + 10, 28, CYAN, a * k1)
    if k2 > 0:
        p2 = (cx + R * math.cos(a1 + a2), cy - R * math.sin(a1 + a2))
        c.drawLine(cx, cy, *p2, paint(GOLD, 0.7 * a, stroke=2))
        # 沿圆周画出转过的那段
        rect = skia.Rect(cx - R, cy - R, cx + R, cy + R)
        c.drawArc(rect, -math.degrees(a1), -math.degrees(a2), False, paint(MAGENTA, 0.9 * a, stroke=5))
        glow_dot(c, *p2, 9, GOLD, a, 6)
        draw_math(c, "e^{it(x+y)}", p2[0] - 22, p2[1] - 16, 34, GOLD, a * k2, align="r")
        mid = a1 + a2 / 2
        draw_math(c, "ty", cx + 140 * math.cos(mid), cy - 140 * math.sin(mid) + 10, 28, MAGENTA, a * k2)
    fa = env(u, T_B + 7.5, T_C, 0.6, 0.6)
    draw_math(c, r"e^{it(X+Y)}\ =\ e^{itX}\cdot e^{itY}", 1370, 175, 52, WHITE, fa,
              reveal=ramp(u, T_B + 7.5, T_B + 9.0), glow=0.2)


# ---------------------------------------------------------------- 三个重心：长度相乘、角度相加
def tC(u):
    return 0.15 + 5.0 * ramp(u, T_C + 2.0, T_D - 1.0, lambda x: x)


def vectors(c, u):
    a = env(u, T_C, T_D, 0.8, 0.6)
    if a <= 0.003:
        return
    t = tC(u)
    D = DISK
    D.draw(c, a)
    zx, zy = complex(cfX(t)), complex(cfY(t))
    zs = zx * zy
    # 三条轨迹
    ts = np.linspace(0.15, t, 300)
    for f, rgb in ((cfX, CYAN), (cfY, MAGENTA), (lambda s: cfX(s) * cfY(s), GOLD)):
        xx, yy = D.xy(f(ts))
        stroke_xy(c, xx, yy, rgb, 0.35 * a, 2)
    for z, rgb, lab in ((zx, CYAN, r"\varphi_X"), (zy, MAGENTA, r"\varphi_Y"), (zs, GOLD, r"\varphi_X\varphi_Y")):
        gx, gy = D.xy(z)
        c.drawLine(D.cx, D.cy, float(gx), float(gy), paint(rgb, 0.85 * a, stroke=3))
        glow_dot(c, float(gx), float(gy), 7, rgb, a, 5)
        # 标签放在箭头尖端的外侧
        ang = math.atan2(z.imag, z.real) if abs(z) > 1e-3 else 0.0
        lx, ly = float(gx) + 34 * math.cos(ang), float(gy) - 34 * math.sin(ang) + 10
        draw_math(c, lab, lx, ly, 30, rgb, a, align="l" if math.cos(ang) >= 0 else "r")
    readout(c, "t =", f"{t:5.2f}", D.cx + D.R - 40, D.cy + D.R + 64, a, WHITE, 26)
    y0 = D.cy + D.R + 64
    readout(c, r"|\varphi_X|\,|\varphi_Y| =", f"{abs(zx) * abs(zy):5.3f}", 1000 - 10, y0 + 0, a, GOLD, 24)
    # 左边：这句话的公式版
    fa = env(u, T_C + 0.5, T_D, 0.6, 0.6)
    draw_math(c, r"\mathbb{E}\,[\,e^{itX}e^{itY}\,]\ =\ \mathbb{E}\,[\,e^{itX}\,]\ \mathbb{E}\,[\,e^{itY}\,]", 960, 175, 48,
              WHITE, fa, reveal=ramp(u, T_C + 0.5, T_C + 2.0), glow=0.2)
    text(c, "独立", 470, 360, 44, "bold", GOLD, fa)
    text(c, "INDEPENDENCE", 470, 400, 18, "orbm", GOLD, 0.6 * fa, track=6)
    k = ramp(u, T_C + 8.0, T_C + 9.0)
    text(c, "长度相乘", 470, 520, 38, "sans", WHITE, fa * k)
    text(c, "角度相加", 470, 590, 38, "sans", WHITE, fa * ramp(u, T_C + 8.6, T_C + 9.6))
    draw_math(c, r"|\varphi_{X+Y}|=|\varphi_X|\,|\varphi_Y|", 470, 700, 36, GOLD, fa * ramp(u, T_C + 9.5, T_C + 10.5))
    draw_math(c, r"\arg\varphi_{X+Y}=\arg\varphi_X+\arg\varphi_Y", 470, 770, 36, GOLD, fa * ramp(u, T_C + 10.0, T_C + 11.0))


# ---------------------------------------------------------------- 卷积定理
def theorem(c, u):
    a = env(u, T_D, T_E, 0.8, 0.6)
    if a <= 0.003:
        return
    draw_math(c, r"\varphi_{X+Y}(t)\ =\ \varphi_X(t)\,\varphi_Y(t)", 960, 230, 66, GOLD, a,
              reveal=ramp(u, T_D + 0.2, T_D + 1.8), glow=0.3)
    k = ramp(u, T_D + 2.2, T_D + 3.2)
    draw_math(c, r"\Longleftrightarrow", 960, 330, 50, WHITE, a * k)
    draw_math(c, r"\widehat{f*g}\ =\ \hat{f}\cdot\hat{g}", 960, 440, 66, WHITE, a * k,
              reveal=ramp(u, T_D + 2.4, T_D + 3.8), glow=0.25)
    text(c, "卷积定理", 960, 520, 34, "bold", MAGENTA, a * k)
    P = Plot(380, 600, 1540, 820, 0, 12, -0.3, 1.05)
    pa = a * ramp(u, T_D + 4.0, T_D + 5.0)
    P.axes(c, pa, GREY)
    ts = np.linspace(0, 12, 500)
    prog = ramp(u, T_D + 4.0, T_D + 7.0)
    n = max(2, int(500 * prog))
    P.curve(c, ts[:n], np.real(cfX(ts[:n])), CYAN, pa, 2.4)
    P.curve(c, ts[:n], np.abs(cfY(ts[:n])), MAGENTA, pa, 2.4)
    P.curve(c, ts[:n], np.abs(cfX(ts[:n]) * cfY(ts[:n])), GOLD, pa, 3.2)
    # 图例
    for j, (lab, rgb) in enumerate(((r"\varphi_X(t)=\sin t\,/\,t", CYAN), (r"|\varphi_Y(t)|", MAGENTA),
                                    (r"|\varphi_X(t)\,\varphi_Y(t)|", GOLD))):
        ly = P.T + 10 + j * 46
        c.drawLine(P.R - 330, ly - 9, P.R - 290, ly - 9, paint(rgb, pa, stroke=3))
        draw_math(c, lab, P.R - 274, ly, 28, rgb, pa, align="l")
    draw_math(c, "t", P.R + 20, float(P.sy(0)) + 8, 28, GREY, pa, align="l")


# ---------------------------------------------------------------- 二项 → 泊松
LAM = 2.0
NS = [3, 4, 6, 10, 20, 60, 0]     # 0 表示极限（泊松）


def binom_pmf(n, k):
    if n == 0:
        return np.exp(-LAM + k * np.log(LAM) - gammaln(k + 1))
    p = LAM / n
    ok = k <= n
    out = np.zeros_like(k, dtype=float)
    kk = k[ok]
    out[ok] = np.exp(gammaln(n + 1) - gammaln(kk + 1) - gammaln(n - kk + 1) + kk * np.log(p) + (n - kk) * np.log1p(-p))
    return out


def binom_cf(n, t):
    if n == 0:
        return np.exp(LAM * (np.exp(1j * t) - 1))
    return (1 + LAM * (np.exp(1j * t) - 1) / n) ** n


def n_state(u):
    """返回 (下标, 插值比例)。"""
    k = ramp(u, T_E + 5.0, T_E + 12.5, lambda x: x) * (len(NS) - 1)
    i = min(int(k), len(NS) - 2)
    return i, smooth(k - i)


def poisson(c, u):
    a = env(u, T_E, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    i, f = n_state(u)
    n0, n1 = NS[i], NS[i + 1]
    panel(c, 110, 300, 820, 520, a, CYAN)
    ks = np.arange(0, 9)
    pm = (1 - f) * binom_pmf(n0, ks) + f * binom_pmf(n1, ks)
    P = Plot(170, 400, 880, 760, -0.6, 8.6, 0, 0.45)
    P.axes(c, a, GREY)
    for k, v in zip(ks, pm):
        x = float(P.sx(k))
        y = float(P.sy(v))
        c.drawRect(skia.Rect(x - 22, y, x + 22, P.B), paint(CYAN, 0.35 * a))
        c.drawRect(skia.Rect(x - 22, y, x + 22, y + 3), paint(mix(CYAN, WHITE, 0.4), a))
        draw_math(c, str(k), x, P.B + 32, 24, GREY, 0.7 * a)
    nlab = "\\infty" if (n1 == 0 and f > 0.5) else str(n0 if f < 0.5 else n1)
    text(c, "二项分布", 300, 360, 30, "bold", CYAN, a)
    draw_math(c, rf"n = {nlab},\quad np=\lambda=2", 640, 362, 32, WHITE, a * ramp(u, T_E + 4.0, T_E + 5.0))
    # 右：复平面上的特征函数曲线 t∈[0, 2π]
    D = Disk(1380, 560, 190)
    D.draw(c, a * 0.7, labels=False)
    ts = np.linspace(0, 2 * np.pi, 600)
    z = (1 - f) * binom_cf(n0, ts) + f * binom_cf(n1, ts)
    xx, yy = D.cx + D.R * z.real, D.cy - D.R * z.imag
    stroke_xy(c, xx, yy, GOLD, 0.25 * a, 9)
    stroke_xy(c, xx, yy, mix(GOLD, WHITE, 0.3), a, 2.6)
    tt = (u * 0.9) % (2 * np.pi)
    zt = complex((1 - f) * binom_cf(n0, tt) + f * binom_cf(n1, tt))
    glow_dot(c, D.cx + D.R * zt.real, D.cy - D.R * zt.imag, 7, GOLD, a, 5)
    draw_math(c, r"\varphi(t),\ 0\leq t\leq 2\pi", D.cx, D.cy + D.R + 52, 28, GREY, a)
    fa = a * ramp(u, T_E + 0.4, T_E + 1.6)
    draw_math(c, r"\varphi_{\mathrm{Bin}}(t)=(q+p\,e^{it})^n", 1380, 220, 44, WHITE, fa, reveal=ramp(u, T_E + 0.4, T_E + 1.8))
    k2 = ramp(u, T_E + 6.5, T_E + 8.0)
    draw_math(c, r"\left(1+\frac{\lambda(e^{it}-1)}{n}\right)^{n}\ \to\ e^{\lambda(e^{it}-1)}", 1380, 845, 40, GOLD,
              a * k2, reveal=k2)
    text(c, "泊松", 1380, 300, 30, "bold", GOLD, a * ramp(u, T_E + 12.0, T_E + 12.8))


def draw(c, u):
    lines(c, u)
    particles(c, u)
    pair_demo(c, u)
    vectors(c, u)
    theorem(c, u)
    poisson(c, u)


def tone(u):
    t = 0.15 + 5.0 * np.clip((u - T_C - 2.0) / (T_D - 1.0 - T_C - 2.0), 0, 1)
    amp = np.abs(cfX(t) * cfY(t)) * ((u > T_C + 1.5) & (u < T_D - 0.3))
    return 110 * 2 ** (np.log2(1 + t) * 1.1), 0.18 * amp


CAPS = [
    (4.4, 9.4, "$X$ 和 $Y$ 相互独立。它们的和 $X+Y$ 服从什么分布？"),
    (9.6, 16.6, "要把所有 $x+y=s$ 的组合都加起来——这叫卷积，算起来很麻烦。"),
    (17.4, 24.4, "到圆上看：先转 $tx$，再转 $ty$，一共转了 $t(x+y)$。"),
    (24.6, 32.6, "角度相加，就是旋转相乘：$e^{it(X+Y)}=e^{itX}e^{itY}$。"),
    (33.4, 40.4, "独立的意思是：乘积的平均，等于平均的乘积。"),
    (40.6, 48.6, "所以 $X+Y$ 的重心，就是两个重心相乘：长度相乘，角度相加。"),
    (49.4, 54.6, "这就是傅里叶分析里的卷积定理：卷积的变换，等于变换的乘积。"),
    (54.8, 60.2, "在概率论里它只是一句话：独立的随机变量，在每个频率上各转各的。"),
    (60.8, 66.8, "第 2 集的二项分布是 $n$ 个独立伯努利之和，所以它的特征函数就是一个 $n$ 次方。"),
    (67.0, 74.4, "第 4 集让 $n\\to\\infty$、$np=\\lambda$：$n$ 次方的极限是 $e^{\\lambda(e^{it}-1)}$——泊松分布。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_A + 0.4, "shimmer", {"dur": 2.0}),
    (T_DROP, "rain", {"dur": 7.0}),
    (T_A + 5.6, "chime", {"f": 660}),
    (T_B, "whoosh", {"dur": 1.4}), (T_B + 0.6, "pitch", {"dur": 1.6, "up": True}),
    (T_B + 2.6, "pitch", {"dur": 1.6, "up": True}), (T_B + 4.2, "chime", {"f": 990}),
    (T_B + 7.5, "chime", {"f": 880}),
    (T_C, "whoosh", {"dur": 1.4}), (T_C + 0.5, "chime", {"f": 740}),
    (T_D, "glitch", {}), (T_D + 0.2, "boom", {}), (T_D + 2.4, "chime", {"f": 1320}),
    (T_E, "whoosh", {"dur": 1.4}), (T_E + 0.4, "chime", {"f": 660}),
]
SFX += [(T_E + 5.0 + k * 7.5 / (len(NS) - 1), "tick", {"f": 1400 + 120 * k}) for k in range(1, len(NS))]
SFX += [(T_E + 12.6, "chime", {"f": 1320})]

SCENES = [Scene("ch2", DUR, draw, CAPS, SFX, tone=tone, chapter=("02", "独立：加法变成乘法", "INDEPENDENCE TURNS SUMS INTO PRODUCTS"),
                theme=2, bed=2)]
