"""第 5 章 热，就是随机游走。傅里叶 1822 年用三角级数解铁环上的热传导；换个看法，热是无数个独立做布朗运动的粒子。
起点和后来走的路独立，所以绕 k 圈的重心每次乘上 E[e^{ikB_s}] = e^{−k²s/2}：高频先消失，最后只剩平均。"""

import math

import numpy as np
import skia

from dist import circle_density, vonmises_mix_coef
from gfx import (GOLD, GREY, MAGENTA, ORANGE, WHITE, Plot, dots, draw_math, env, heat, mix, paint, ramp,
                 readout, text)
from scene import Scene

W0, MU0, K0 = [0.55, 0.30, 0.15], [0.4, 2.6, -2.0], [60.0, 25.0, 120.0]
KMAX = 90
C0 = vonmises_mix_coef(W0, MU0, K0, KMAX)
NB = 360
THB = np.linspace(-np.pi, np.pi, NB, endpoint=False) + np.pi / NB
P0MAX = float(np.max(circle_density(C0, THB)))

N = 2400
_rng = np.random.default_rng(55)
_th = np.linspace(-np.pi, np.pi, 20001)
_cdf = np.cumsum(circle_density(C0, _th))
_cdf /= _cdf[-1]
TH0 = np.interp(_rng.random(N), _cdf, _th)
RJ = _rng.normal(0, 1, N)

# 布朗运动：在一组扩散时间 s 上预先生成路径
S_GRID = np.concatenate([[0.0], np.geomspace(2e-4, 3.0, 900)])
_inc = _rng.normal(0, 1, (len(S_GRID) - 1, N)).astype(np.float32) * np.sqrt(np.diff(S_GRID))[:, None].astype(np.float32)
WALK = np.vstack([np.zeros((1, N), np.float32), np.cumsum(_inc, 0)])

RC = (600, 560)
RR = 250

T_HIST = 4.0
T_WALK = 14.0
T_MODES = 32.0
T_EQ = 52.0
DUR = 71.0
S_START = T_WALK + 3.0
S_END = T_EQ + 9.0


def s_of(u):
    if u <= S_START:
        return 0.0
    k = ramp(u, S_START, S_END, lambda x: x)
    return float(2e-4 * (3.0 / 2e-4) ** k)


def coef_at(s, kmax=KMAX):
    k = np.arange(kmax + 1)
    return C0[:kmax + 1] * np.exp(-k ** 2 * s / 2)


def walkers(s):
    j = int(np.searchsorted(S_GRID, s))
    if j <= 0:
        return TH0.copy()
    j = min(j, len(S_GRID) - 1)
    s0, s1 = S_GRID[j - 1], S_GRID[j]
    f = (s - s0) / (s1 - s0) if s1 > s0 else 1.0
    return TH0 + (1 - f) * WALK[j - 1] + f * WALK[j]


def ring(c, u, s):
    a = env(u, T_HIST, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    cx, cy = RC
    dens = circle_density(coef_at(s), THB)
    v = np.clip(dens / P0MAX, 0, 1) ** 0.45
    rect = skia.Rect(cx - RR, cy - RR, cx + RR, cy + RR)
    sweep = 360 / NB + 0.6
    for i in range(NB):
        rgb = heat(v[i])
        ang = -math.degrees(THB[i]) - 180 / NB
        c.drawArc(rect, ang, sweep, False, paint(rgb, 0.35 * a, stroke=70, cap=False))
        c.drawArc(rect, ang, sweep, False, paint(rgb, a, stroke=30, cap=False))
    c.drawCircle(cx, cy, RR - 16, paint(WHITE, 0.10 * a, stroke=1))
    c.drawCircle(cx, cy, RR + 16, paint(WHITE, 0.10 * a, stroke=1))


def particles(c, u, s):
    a = env(u, T_WALK + 0.5, DUR, 1.2, 0.8)
    if a <= 0.003:
        return
    th = walkers(s)
    cx, cy = RC
    r = RR + 62 + 14 * RJ
    k = ramp(u, T_WALK + 0.5, T_WALK + 2.5)
    rr = RR + (r - RR) * k
    dots(c, cx + rr * np.cos(th), cy - rr * np.sin(th), mix(GOLD, WHITE, 0.5), 0.75 * a, 2.6)


def history(c, u):
    a = env(u, T_HIST, T_WALK + 0.3, 0.8, 0.8)
    if a <= 0.003:
        return
    x = 1390
    text(c, "1822", x, 330, 120, "orb", ORANGE, 0.25 * a, p=paint(ORANGE, 0.9 * a, stroke=2.2))
    text(c, "Joseph Fourier", x, 420, 40, "serifm", WHITE, a * ramp(u, T_HIST + 0.6, T_HIST + 1.4))
    text(c, "《热的解析理论》", x, 500, 40, "serif", GOLD, a * ramp(u, T_HIST + 1.0, T_HIST + 1.8))
    text(c, "Théorie analytique de la chaleur", x, 548, 26, "serifm", GREY, a * ramp(u, T_HIST + 1.2, T_HIST + 2.0))
    k = ramp(u, T_HIST + 4.0, T_HIST + 5.0)
    text(c, "第四章：热在一只铁环中的运动", x, 650, 30, "sans", WHITE, 0.8 * a * k)


PROF = Plot(1080, 250, 1800, 500, -math.pi, math.pi, 0, 1.0)
BARS = Plot(1080, 650, 1800, 870, 0.4, 12.6, 0, 1.0)


def plots(c, u, s):
    a = env(u, T_WALK + 1.0, T_EQ + 0.2, 0.8, 0.6)
    if a <= 0.003:
        return
    # 温度分布（展开成直线）+ 粒子直方图
    PROF.axes(c, a, GREY)
    for v, lab in ((-math.pi, r"-\pi"), (0, "0"), (math.pi, r"\pi")):
        draw_math(c, lab, float(PROF.sx(v)), PROF.B + 32, 22, GREY, 0.7 * a)
    draw_math(c, r"\theta", PROF.R + 20, PROF.B + 8, 26, GREY, a, align="l")
    th = (walkers(s) + np.pi) % (2 * np.pi) - np.pi
    hist, edges = np.histogram(th, bins=72, range=(-np.pi, np.pi))
    hd = hist / (N * (edges[1] - edges[0]))
    for i in range(72):
        x0, x1 = float(PROF.sx(edges[i])), float(PROF.sx(edges[i + 1]))
        y = float(PROF.sy(min(hd[i] / P0MAX, 1.0)))
        c.drawRect(skia.Rect(x0 + 1, y, x1 - 1, PROF.B), paint(mix(GOLD, WHITE, 0.4), 0.18 * a))
    xs = np.linspace(-np.pi, np.pi, 500)
    dens = circle_density(coef_at(s), xs) / P0MAX
    PROF.curve(c, xs, dens, ORANGE, 0.3 * a, 8)
    PROF.curve(c, xs, dens, mix(ORANGE, WHITE, 0.35), a, 2.6)
    text(c, "温度 = 粒子密度", PROF.L, PROF.T - 20, 28, "bold", WHITE, a, align="l")
    readout(c, "s =", f"{s:6.4f}" if s < 0.1 else f"{s:6.3f}", PROF.R, PROF.T - 20, a, MAGENTA, 26, align="r")
    # 各频率的系数
    ba = a * ramp(u, T_MODES, T_MODES + 1.0)
    if ba <= 0.003:
        return
    BARS.axes(c, ba, GREY)
    text(c, "绕 k 圈的重心", BARS.L, BARS.T - 20, 28, "bold", WHITE, ba, align="l")
    draw_math(c, r"|c_k(s)|", BARS.L + 200, BARS.T - 20, 28, GOLD, ba, align="l")
    cs = np.abs(coef_at(s, 12))
    c0 = np.abs(C0[:13])
    for k in range(1, 13):
        x = float(BARS.sx(k))
        y0 = float(BARS.sy(c0[k]))
        y = float(BARS.sy(cs[k]))
        c.drawRect(skia.Rect(x - 20, y0, x + 20, BARS.B), paint(GREY, 0.12 * ba))
        rgb = mix(MAGENTA, GOLD, k / 12)
        c.drawRect(skia.Rect(x - 20, y, x + 20, BARS.B), paint(rgb, 0.45 * ba))
        c.drawRect(skia.Rect(x - 20, y, x + 20, y + 3), paint(mix(rgb, WHITE, 0.4), ba))
        draw_math(c, str(k), x, BARS.B + 30, 22, GREY, 0.7 * ba)


def formulas(c, u):
    fa = env(u, T_MODES + 0.4, T_EQ, 0.6, 0.6)
    draw_math(c, r"c_k(s)\ =\ c_k(0)\cdot\mathbb{E}\,[e^{ikB_s}]\ =\ c_k(0)\,e^{-k^2 s/2}", 960, 165, 48, WHITE, fa,
              reveal=ramp(u, T_MODES + 0.4, T_MODES + 2.2), glow=0.25)
    fb = env(u, T_EQ + 0.3, DUR, 0.6, 0.8)
    text(c, "热方程", 1440, 300, 30, "bold", GREY, fb)
    draw_math(c, r"\dfrac{\partial u}{\partial s}=\dfrac{1}{2}\,\dfrac{\partial^2 u}{\partial\theta^2}", 1440, 400, 56, WHITE,
              fb, reveal=ramp(u, T_EQ + 0.3, T_EQ + 1.6), glow=0.25)
    text(c, "傅里叶的解 = 布朗运动的分布", 1440, 590, 30, "bold", GREY, fb * ramp(u, T_EQ + 1.6, T_EQ + 2.4))
    draw_math(c, r"u(\theta,s)=\dfrac{1}{2\pi}\sum_k c_k\,e^{-k^2s/2}\,e^{-ik\theta}", 1440, 700, 50, GOLD, fb,
              reveal=ramp(u, T_EQ + 1.6, T_EQ + 3.0), glow=0.25)


def draw(c, u):
    s = s_of(u)
    ring(c, u, s)
    particles(c, u, s)
    history(c, u)
    plots(c, u, s)
    formulas(c, u)


def tone(u):
    """扩散时的一个下滑的低音：音高随最高的“还活着”的频率下降。"""
    s = np.array([s_of(x) for x in u[::480]])
    s = np.interp(np.arange(len(u)), np.arange(0, len(u), 480)[:len(s)], s)
    kalive = np.sqrt(2 * 3.0 / np.maximum(s, 1e-4))        # e^{-k²s/2} = e^{-3} 的 k
    f = 80 + 18 * np.minimum(kalive, 40)
    amp = 0.06 * ((u > S_START) & (u < S_END + 2)) * np.clip((u - S_START) / 1.5, 0, 1)
    return f, amp


CAPS = [
    (4.4, 13.4, "1822 年，傅里叶在《热的解析理论》里系统地用三角级数解热传导问题，其中一个例子就是一只铁环。"),
    (14.4, 20.4, "换一个看法：热是无数个乱走的粒子，温度就是粒子的密度。"),
    (20.6, 31.4, "每个粒子独立地做随机游走（布朗运动）。粒子散开，热也就散开了。"),
    (32.4, 39.6, "起点和之后走的路相互独立，所以（第 2 章）绕 $k$ 圈的重心要乘上 $\\mathbb{E}[e^{ikB_s}]=e^{-k^2s/2}$。"),
    (39.8, 45.8, "频率越高衰减越快：$k=10$ 的起伏比 $k=1$ 快一百倍消失。"),
    (46.0, 51.6, "所以细节最先抹平，最后只剩下平均温度。"),
    (52.4, 60.6, "傅里叶写下的解，和布朗运动的分布是同一个公式：热方程，就是随机游走的平均行为。"),
    (60.8, 70.0, "热传导、墨水在水里化开、粒子的扩散……都是同一件事：独立的小扰动叠加，在每个频率上各自衰减。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_HIST, "fire", {"dur": T_WALK - T_HIST}), (T_HIST + 0.2, "chime", {"f": 440}),
    (T_WALK, "whoosh", {"dur": 1.5}), (S_START, "hiss", {"dur": S_END - S_START}),
    (T_MODES + 0.4, "chime", {"f": 880}),
    (T_EQ + 0.3, "chime", {"f": 660}), (T_EQ + 1.6, "chime", {"f": 990}),
    (S_END, "swell", {"dur": 3.0}),
]

SCENES = [Scene("ch5", DUR, draw, CAPS, SFX, tone=tone, chapter=("05", "热，就是随机游走", "HEAT IS A RANDOM WALK"),
                theme=5, bed=5)]
