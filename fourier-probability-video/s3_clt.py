"""第 3 章 钟形曲线是不动点：小频率下重心只往里缩 t²/2；n 次方把 (1 − t²/2n)^n 推向 e^{−t²/2}——中心极限定理；
正态的特征函数还是钟形；柯西的 e^{−|t|} 有尖角，平均不会收敛。"""

import math

import numpy as np
from scipy.special import gammaln
from scipy.stats import norm

from dist import X1
from gfx import (CYAN, GOLD, GREY, MAGENTA, WHITE, Disk, Plot, arrow, clamp, colored_dots, dashed, draw_math,
                 env, glow_dot, mix, paint, ramp, readout, smooth, stroke_xy, text)
from scene import Scene

Z1 = X1.standardized()
N = 1000
XS = Z1.quantiles(N, seed=33)
_rng = np.random.default_rng(12)
JIT = _rng.normal(0, 1, N)
VAL = np.clip((XS + 2.3) / 4.6, 0, 1)

T_ARC = 4.0
T_CLT = 19.0
T_GAUSS = 42.0
T_CAUCHY = 58.0
DUR = 81.0


# ---------------------------------------------------------------- 小频率：重心只往里缩 t²/2
DA = Disk(560, 540, 340)


def t_arc(u):
    return 0.5 * ramp(u, T_ARC + 1.0, T_ARC + 5.0)


def arc(c, u):
    a = env(u, T_ARC, T_CLT, 0.8, 0.6)
    if a <= 0.003:
        return
    t = t_arc(u)
    D = DA
    D.draw(c, a)
    ang = t * XS
    r = D.R + 5 * JIT
    colored_dots(c, D.cx + r * np.cos(ang), D.cy - r * np.sin(ang), VAL, a, 3.4)
    z = complex(Z1.cf(t))
    gx, gy = D.xy(z)
    gx, gy = float(gx), float(gy)
    glow_dot(c, gx, gy, 8, GOLD, a, 6)
    draw_math(c, r"\varphi(t)", gx - 16, gy - 22, 32, GOLD, a, align="r")
    readout(c, "t =", f"{t:4.2f}", D.cx + D.R - 40, D.cy + D.R + 40, a, MAGENTA, 26)
    # 1 到重心的距离
    k = ramp(u, T_ARC + 6.5, T_ARC + 7.5)
    if k > 0:
        x1 = D.cx + D.R
        c.drawLine(gx, gy + 30, x1, gy + 30, paint(GOLD, a * k, stroke=2))
        c.drawLine(gx, gy + 22, gx, gy + 38, paint(GOLD, a * k, stroke=2))
        c.drawLine(x1, gy + 22, x1, gy + 38, paint(GOLD, a * k, stroke=2))
        draw_math(c, r"\approx t^2/2", (gx + x1) / 2 + 30, gy + 76, 30, GOLD, a * k, align="l")
    fa = env(u, T_ARC + 8.0, T_CLT, 0.6, 0.6)
    draw_math(c, r"\varphi(t)\ \approx\ 1+it\,\mathbb{E}[X]-\dfrac{t^2}{2}\,\mathbb{E}[X^2]", 1390, 400, 46, WHITE, fa,
              reveal=ramp(u, T_ARC + 8.0, T_ARC + 9.6), glow=0.2)
    k2 = ramp(u, T_ARC + 10.5, T_ARC + 11.5)
    text(c, "均值 0，方差 1", 1390, 500, 32, "sans", GREY, fa * k2)
    draw_math(c, r"\varphi(t)\ \approx\ 1-\dfrac{t^2}{2}", 1390, 620, 58, GOLD, fa * k2, reveal=k2, glow=0.3)


# ---------------------------------------------------------------- 中心极限定理
NSEQ = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]
PL = Plot(130, 300, 900, 760, -4, 4, 0, 0.62)
DC = Disk(1390, 520, 270)
ZG = np.linspace(-4, 4, 500)
TG = np.linspace(0, 7, 500)


def sum_pdf(n, z):
    """Z1 的 n 个独立副本之和除以 √n 的密度（二项混合的正态）。"""
    w1, w2 = Z1.w
    m1, m2 = Z1.mu
    s1, s2 = Z1.sd
    k = np.arange(n + 1)
    logw = gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1) + k * np.log(w1) + (n - k) * np.log(w2)
    mu = (k * m1 + (n - k) * m2) / math.sqrt(n)
    var = (k * s1 ** 2 + (n - k) * s2 ** 2) / n
    z = np.asarray(z)[:, None]
    return np.sum(np.exp(logw) * np.exp(-0.5 * (z - mu) ** 2 / var) / np.sqrt(2 * np.pi * var), 1)


PDFS = [sum_pdf(n, ZG) for n in NSEQ]
CFS = [Z1.cf(TG / math.sqrt(n)) ** n for n in NSEQ]
GAUSS = np.exp(-ZG ** 2 / 2) / math.sqrt(2 * math.pi)


def n_state(u):
    k = ramp(u, T_CLT + 3.0, T_CLT + 17.0, lambda x: x) * (len(NSEQ) - 1)
    i = min(int(k), len(NSEQ) - 2)
    f = smooth(clamp((k - i) * 1.6))
    return i, f


def clt(c, u):
    a = env(u, T_CLT, T_GAUSS, 0.8, 0.6)
    if a <= 0.003:
        return
    i, f = n_state(u)
    pdf = (1 - f) * PDFS[i] + f * PDFS[i + 1]
    cf = (1 - f) * CFS[i] + f * CFS[i + 1]
    n = NSEQ[i] if f < 0.5 else NSEQ[i + 1]
    PL.axes(c, a, GREY)
    for v in range(-4, 5, 2):
        draw_math(c, str(v) if v >= 0 else f"-{-v}", float(PL.sx(v)), PL.B + 32, 22, GREY, 0.6 * a)
    PL.curve(c, ZG, GAUSS, WHITE, 0.5 * a, 1.6, effect=dashed(8, 7))
    PL.fill(c, ZG, pdf, CYAN, a)
    PL.curve(c, ZG, pdf, CYAN, a, 2.8)
    draw_math(c, r"\dfrac{X_1+\cdots+X_n}{\sqrt{n}}", 515, 250, 40, CYAN, a)
    readout(c, "n =", f"{n:3d}", PL.R - 150, PL.T + 40, a, GOLD, 32)
    # 复平面上的曲线 t ↦ φ_n(t)
    DC.draw(c, a)
    xx, yy = DC.xy(cf)
    stroke_xy(c, xx, yy, GOLD, 0.25 * a, 9)
    stroke_xy(c, xx, yy, mix(GOLD, WHITE, 0.3), a, 2.6)
    gx, gy = DC.xy(np.exp(-TG ** 2 / 2))
    stroke_xy(c, gx, gy, WHITE, 0.45 * a, 1.5, effect=dashed(8, 7))
    tt = (u * 1.3) % 7
    zt = complex((1 - f) * Z1.cf(tt / math.sqrt(NSEQ[i])) ** NSEQ[i] + f * Z1.cf(tt / math.sqrt(NSEQ[i + 1])) ** NSEQ[i + 1])
    px, py = DC.xy(zt)
    glow_dot(c, float(px), float(py), 7, GOLD, a, 5)
    draw_math(c, r"\varphi(t/\sqrt{n})^{\,n}", DC.cx + DC.R + 20, DC.cy - DC.R + 30, 34, GOLD, a, align="r")
    draw_math(c, r"e^{-t^2/2}", DC.cx + 0.45 * DC.R, DC.cy + 44, 28, WHITE, 0.7 * a)
    fa = env(u, T_CLT + 7.0, T_GAUSS, 0.6, 0.6)
    draw_math(c, r"\varphi\!\left(\dfrac{t}{\sqrt{n}}\right)^{n}\ \approx\ \left(1-\dfrac{t^2}{2n}\right)^{n}\ \longrightarrow\ e^{-t^2/2}",
              960, 875, 44, WHITE, fa, reveal=ramp(u, T_CLT + 7.0, T_CLT + 9.0), glow=0.2)


# ---------------------------------------------------------------- 正态：自己的傅里叶变换
GD = Disk(1390, 470, 230)
GXS = norm.ppf((np.arange(900) + 0.5) / 900)
GXS = GXS[_rng.permutation(900)]
GJ = _rng.normal(0, 1, 900)
GH = _rng.random(900)


def t_gauss(u):
    return 3.6 * ramp(u, T_GAUSS + 1.0, T_GAUSS + 7.0, lambda x: x)


def gauss(c, u):
    a = env(u, T_GAUSS, T_CAUCHY, 0.8, 0.6)
    if a <= 0.003:
        return
    P = Plot(130, 330, 860, 620, -4, 4, 0, 0.45)
    P.axes(c, a, CYAN)
    P.fill(c, ZG, GAUSS, CYAN, a)
    P.curve(c, ZG, GAUSS, CYAN, a, 2.8)
    draw_math(c, r"\dfrac{1}{\sqrt{2\pi}}\,e^{-x^2/2}", 495, 280, 38, CYAN, a)
    t = t_gauss(u)
    # 样本：在钟形下面，同时绕到右边的圆上
    colored_dots(c, P.sx(GXS), P.sy(GH * np.exp(-GXS ** 2 / 2) / math.sqrt(2 * math.pi)) - 2,
                 np.clip((GXS + 2.5) / 5, 0, 1), 0.7 * a, 2.8)
    GD.draw(c, a)
    ang = t * GXS
    r = GD.R + 5 * GJ
    colored_dots(c, GD.cx + r * np.cos(ang), GD.cy - r * np.sin(ang), np.clip((GXS + 2.5) / 5, 0, 1), a, 3.0)
    z = math.exp(-t * t / 2)
    glow_dot(c, GD.cx + GD.R * z, GD.cy, 8, GOLD, a, 6)
    c.drawLine(GD.cx, GD.cy, GD.cx + GD.R * z, GD.cy, paint(GOLD, 0.8 * a, stroke=3))
    readout(c, "t =", f"{t:4.2f}", GD.cx + GD.R - 40, GD.cy + GD.R + 50, a, MAGENTA, 26)
    # 重心随 t 的高度，画在右下：又是一个钟
    Q = Plot(1130, 790, 1650, 900, -3.6, 3.6, 0, 1.05)
    Q.axes(c, a, GREY)
    ts = np.linspace(-3.6, 3.6, 400)
    sel = np.abs(ts) <= t
    if sel.sum() > 1:
        Q.curve(c, ts[sel], np.exp(-ts[sel] ** 2 / 2), GOLD, a, 2.8)
    draw_math(c, r"\varphi(t)=e^{-t^2/2}", 1390, 760, 34, GOLD, a * ramp(u, T_GAUSS + 6.0, T_GAUSS + 7.0))
    k = ramp(u, T_GAUSS + 7.2, T_GAUSS + 8.4)
    arrow(c, 880, 470, 1110, 470, GOLD, a * k, 3, 18)
    draw_math(c, r"\mathcal{F}", 995, 445, 44, GOLD, a * k)
    # 不动点
    fa = env(u, T_GAUSS + 7.6, T_CAUCHY, 0.6, 0.6)
    draw_math(c, r"\varphi\!\left(\dfrac{t}{\sqrt{2}}\right)^{2}=\ \varphi(t)", 495, 760, 44, WHITE, fa,
              reveal=ramp(u, T_GAUSS + 7.6, T_GAUSS + 9.0), glow=0.2)
    text(c, "相加再缩放，形状不变", 495, 850, 30, "sans", GREY, fa * ramp(u, T_GAUSS + 9.0, T_GAUSS + 10.0))


# ---------------------------------------------------------------- 柯西：尖角，平均不收敛
_cr = np.random.default_rng(23)       # 挑过的种子：一千次以后还会猛跳一下
NN = 4000
CAU = np.cumsum(np.tan(np.pi * (_cr.random(NN) - 0.5))) / np.arange(1, NN + 1)
NOR = np.cumsum(_cr.normal(0, 1, NN)) / np.arange(1, NN + 1)


def cauchy(c, u):
    a = env(u, T_CAUCHY, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    P = Plot(140, 320, 860, 760, -4, 4, 0, 1.08)
    P.axes(c, a, GREY)
    ts = np.linspace(-4, 4, 801)
    prog = ramp(u, T_CAUCHY + 0.5, T_CAUCHY + 2.5)
    P.curve(c, ts, np.exp(-ts ** 2 / 2), GOLD, a, 2.6)
    n = max(2, int(801 * prog))
    P.curve(c, ts[:n], np.exp(-np.abs(ts[:n])), MAGENTA, a, 3.0)
    draw_math(c, r"e^{-t^2/2}", float(P.sx(1.5)), float(P.sy(0.55)), 30, GOLD, a, align="l")
    draw_math(c, r"e^{-|t|}", float(P.sx(-1.4)), float(P.sy(0.42)), 32, MAGENTA, a * prog, align="r")
    draw_math(c, "t", P.R + 20, P.B + 8, 28, GREY, a, align="l")
    k = env(u, T_CAUCHY + 3.0, DUR, 0.5, 0.5)
    if k > 0:
        px, py = float(P.sx(0)), float(P.sy(1))
        pulse = 1 + 0.15 * math.sin(u * 5)
        c.drawCircle(px, py, 34 * pulse, paint(MAGENTA, 0.8 * k * a, stroke=2.5))
        text(c, "尖角", px + 70, py + 12, 30, "bold", MAGENTA, k * a, align="l")
    text(c, "特征函数：正态 vs 柯西", 500, 270, 34, "bold", WHITE, a)
    # 右边：样本平均随 n 的变化（横轴是 log n）
    Q = Plot(1040, 330, 1780, 760, 0, math.log10(NN), -3, 3)
    qa = a * ramp(u, T_CAUCHY + 6.0, T_CAUCHY + 7.0)
    Q.axes(c, qa, GREY)
    for e in range(0, 4):
        draw_math(c, f"10^{e}", float(Q.sx(e)), Q.B + 34, 22, GREY, 0.6 * qa)
    draw_math(c, "n", Q.R + 20, float(Q.sy(0)) + 8, 26, GREY, qa, align="l")
    text(c, "样本平均", 1410, 290, 30, "bold", WHITE, qa)
    m = min(NN, int(NN * ramp(u, T_CAUCHY + 7.0, T_CAUCHY + 20.0, lambda x: x ** 2.2)) + 1)
    if m > 1:
        ns = np.arange(1, m + 1)
        lx = np.log10(ns)
        Q.curve(c, lx, np.clip(NOR[:m], -3, 3), GOLD, qa, 2.0)
        Q.curve(c, lx, np.clip(CAU[:m], -3, 3), MAGENTA, qa, 2.0)
        glow_dot(c, float(Q.sx(lx[-1])), float(Q.sy(np.clip(CAU[m - 1], -3, 3))), 6, MAGENTA, qa, 5)
        glow_dot(c, float(Q.sx(lx[-1])), float(Q.sy(np.clip(NOR[m - 1], -3, 3))), 6, GOLD, qa, 5)
    draw_math(c, "N(0,1)", Q.R - 10, Q.T + 20, 26, GOLD, qa, align="r")
    draw_math(c, r"\mathrm{Cauchy}", Q.R - 10, Q.T + 56, 26, MAGENTA, qa, align="r")
    fa = env(u, T_CAUCHY + 7.0, DUR, 0.6, 0.6)
    draw_math(c, r"\varphi\!\left(\dfrac{t}{n}\right)^{n}=\ e^{-n|t|/n}\ =\ e^{-|t|}", 960, 880, 44, WHITE, fa,
              reveal=ramp(u, T_CAUCHY + 7.0, T_CAUCHY + 8.6), glow=0.2)


def draw(c, u):
    arc(c, u)
    clt(c, u)
    gauss(c, u)
    cauchy(c, u)


def _cauchy_jumps():
    """柯西样本平均跳得最厉害的几个时刻，配上故障音。"""
    out = []
    m_prev = 1
    for k in range(1, 400):
        uu = T_CAUCHY + 7.0 + 13.0 * k / 400
        m = int(NN * ((k / 400) ** 2.2)) + 1
        if m > m_prev + 1:
            jump = np.max(np.abs(np.diff(CAU[m_prev - 1:m])))
            if jump > 0.35:
                out.append((uu, "glitch_sfx", {"amp": min(1.0, jump)}))
        m_prev = m
    return out[:14]


def tone(u):
    t = 3.6 * np.clip((u - T_GAUSS - 1.0) / 6.0, 0, 1)
    amp = np.exp(-t ** 2 / 2) * ((u > T_GAUSS + 0.8) & (u < T_CAUCHY - 0.5))
    return 110 * 2 ** (np.log2(1 + t) * 1.1), 0.2 * amp


CAPS = [
    (4.4, 10.6, "设 $X$ 均值为 $0$、方差为 $1$。频率 $t$ 很小时，点只铺开一小段弧。"),
    (10.8, 18.6, "上下的点互相抵消，重心只往里缩了 $t^2/2$：$\\varphi(t)\\approx 1-t^2/2$。"),
    (19.4, 25.6, "把 $n$ 个这样独立同分布的变量加起来，再除以 $\\sqrt{n}$。"),
    (25.8, 32.6, "相加让特征函数变成 $n$ 次方；除以 $\\sqrt{n}$，让频率缩小 $\\sqrt{n}$ 倍。"),
    (32.8, 41.6, "$n$ 次方把 $1-t^2/2n$ 推向 $e^{-t^2/2}$——不管 $X$ 原来长什么样。这就是中心极限定理。"),
    (42.4, 49.2, "$e^{-t^2/2}$ 恰好是标准正态的特征函数：钟形曲线的傅里叶变换，还是钟形曲线。"),
    (49.4, 57.6, "它是“相加再缩放”的不动点：两个独立的标准正态相加再除以 $\\sqrt{2}$，还是标准正态。"),
    (58.4, 64.6, "第 6 集的灯塔：柯西分布的特征函数是 $e^{-|t|}$，在 $t=0$ 处有一个尖角。"),
    (64.8, 71.6, "尖角意味着连均值都不存在。$n$ 个柯西的平均，特征函数一点都没变。"),
    (71.8, 80.0, "所以平均多少次都没用，柯西的样本平均永远在乱跳——中心极限定理需要那个 $t^2$。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_ARC + 1.0, "pitch", {"dur": 4.0, "up": True}), (T_ARC + 6.5, "chime", {"f": 880}),
    (T_ARC + 8.0, "chime", {"f": 660}), (T_ARC + 10.5, "chime", {"f": 990}),
    (T_CLT, "whoosh", {"dur": 1.4}), (T_CLT + 7.0, "chime", {"f": 740}),
    (T_GAUSS, "whoosh", {"dur": 1.4}), (T_GAUSS + 7.2, "boom", {}), (T_GAUSS + 7.6, "chime", {"f": 1320}),
    (T_CAUCHY, "glitch", {}), (T_CAUCHY + 3.0, "alarm", {}), (T_CAUCHY + 7.0, "chime", {"f": 660}),
]
SFX += [(T_CLT + 3.0 + 14.0 * k / (len(NSEQ) - 1), "tick", {"f": 900 + 90 * k}) for k in range(1, len(NSEQ))]
SFX += _cauchy_jumps()

SCENES = [Scene("ch3", DUR, draw, CAPS, SFX, tone=tone, chapter=("03", "钟形曲线是不动点", "THE BELL CURVE IS A FIXED POINT"),
                theme=3, bed=3)]
