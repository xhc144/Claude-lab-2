"""第 6 章 抛硬币，抛出 π。[-1,1] 上的均匀分布 = 二进制展开 = 一串独立硬币 ε_k/2^k（步长减半的高尔顿板）。
一枚 ±a 的硬币重心是 cos(ta)；独立 → 相乘：sin t / t = ∏ cos(t/2^k)。代入 t = π/2 就是韦达 1593 年的公式。"""

import math

import numpy as np
import skia

from gfx import (CYAN, GOLD, GREY, MAGENTA, VIOLET, WHITE, Disk, Plot, dots, draw_math, env, font, glow_dot, mix,
                 paint, ramp, readout, rich, segments, smooth, text)
from scene import Scene

DEPTH = 9
ROOT = (960, 262)
DY = 58
SPAN = 700           # [-1,1] → ±700 像素
BASE_Y = ROOT[1] + DY * DEPTH + 60

T_TREE = 4.0
T_FALL = 8.6
T_COIN = 22.0
T_PROD = 35.0
T_PI = 49.0
DUR = 71.0

NP = 512
_rng = np.random.default_rng(66)
LEAF = _rng.permutation(NP)                      # 每个叶子正好落一个粒子：落下来是均匀的
BITS = ((LEAF[:, None] >> np.arange(DEPTH - 1, -1, -1)[None, :]) & 1) * 2 - 1   # ε_k = ±1
START = T_FALL + 9.0 * np.sort(_rng.random(NP))
STEP = 0.11
NBIN = 32


def node_x(eps_prefix):
    k = np.arange(1, len(eps_prefix) + 1)
    return ROOT[0] + SPAN * float(np.sum(np.asarray(eps_prefix) / 2.0 ** k))


def tree(c, u):
    a = env(u, T_TREE, T_COIN + 0.3, 0.6, 0.8)
    if a <= 0.003:
        return
    # 一层一层长出来
    xs = np.array([ROOT[0]], float)
    for k in range(1, DEPTH + 1):
        g = ramp(u, T_TREE + 0.45 * (k - 1), T_TREE + 0.45 * k)
        if g <= 0:
            break
        y0 = ROOT[1] + DY * (k - 1)
        child = np.concatenate([xs - SPAN / 2 ** k, xs + SPAN / 2 ** k])
        par = np.concatenate([xs, xs])
        segments(c, par, np.full_like(par, y0), par + (child - par) * g, np.full_like(par, y0 + DY * g),
                 mix(CYAN, VIOLET, k / DEPTH), (0.55 - 0.035 * k) * a, 1.6)
        dots(c, child, np.full_like(child, y0 + DY), mix(CYAN, VIOLET, k / DEPTH), 0.6 * a * g, 4 - 0.25 * k)
        lab = rf"\pm\frac{{1}}{{{2 ** k}}}" if k <= 4 else None
        if lab:
            draw_math(c, lab, ROOT[0] + SPAN + 90, y0 + DY * 0.6, 26, GREY, 0.7 * a * g, align="l")
        xs = child
    glow_dot(c, *ROOT, 7, WHITE, a, 5)
    # 底下的数轴和直方图
    la = a * ramp(u, T_TREE + 3.0, T_TREE + 4.0)
    c.drawLine(ROOT[0] - SPAN - 30, BASE_Y, ROOT[0] + SPAN + 30, BASE_Y, paint(GREY, 0.6 * la, stroke=1.5))
    for v, lab in ((-1, "-1"), (0, "0"), (1, "1")):
        x = ROOT[0] + SPAN * v
        c.drawLine(x, BASE_Y - 6, x, BASE_Y + 6, paint(GREY, 0.7 * la, stroke=1.5))
        draw_math(c, lab, x, BASE_Y + 34, 24, GREY, 0.7 * la)


def falling(c, u):
    a = env(u, T_FALL - 0.2, T_COIN + 0.3, 0.4, 0.8)
    if a <= 0.003:
        return
    lv = (u - START) / STEP                      # 每个粒子走到第几层（小数）
    active = (lv > 0) & (lv < DEPTH)
    landed = lv >= DEPTH
    if active.any():
        idx = np.nonzero(active)[0]
        k = np.floor(lv[idx]).astype(int)
        f = lv[idx] - k
        cum = np.cumsum(BITS[idx] / 2.0 ** np.arange(1, DEPTH + 1), 1)
        x0 = np.where(k > 0, cum[np.arange(len(idx)), np.maximum(k - 1, 0)], 0.0)
        x1 = cum[np.arange(len(idx)), k]
        px = ROOT[0] + SPAN * (x0 + (x1 - x0) * f)
        py = ROOT[1] + DY * (k + f) - 10 * np.sin(np.pi * f)
        dots(c, px, py, GOLD, a, 5)
    # 落地的堆成直方图
    if landed.any():
        xl = np.sum(BITS[landed] / 2.0 ** np.arange(1, DEPTH + 1), 1)
        b = np.clip(((xl + 1) / 2 * NBIN).astype(int), 0, NBIN - 1)
        cnt = np.bincount(b, minlength=NBIN)
        bw = 2 * SPAN / NBIN
        for i in range(NBIN):
            if cnt[i]:
                x = ROOT[0] - SPAN + i * bw
                h = cnt[i] * 3.2
                c.drawRect(skia.Rect(x + 2, BASE_Y - h, x + bw - 2, BASE_Y), paint(GOLD, 0.35 * a))
                c.drawRect(skia.Rect(x + 2, BASE_Y - h, x + bw - 2, BASE_Y - h + 2.5), paint(mix(GOLD, WHITE, 0.4), a))
    fa = env(u, T_TREE + 1.0, T_COIN, 0.6, 0.6)
    draw_math(c, r"U\ =\ \sum_{k=1}^{\infty}\dfrac{\varepsilon_k}{2^k}", 760, 160, 44, WHITE, fa,
              reveal=ramp(u, T_TREE + 1.0, T_TREE + 2.2), glow=0.2)
    rich(c, "$\\varepsilon_k=\\pm1$，各占一半，相互独立", 960, 158, 32, WHITE, fa * ramp(u, T_TREE + 2.0, T_TREE + 2.8),
         align="l")


# ---------------------------------------------------------------- 一枚硬币的重心 = cos(ta)
DCOIN = Disk(560, 540, 240)


def coin(c, u):
    a = env(u, T_COIN, T_PROD, 0.8, 0.6)
    if a <= 0.003:
        return
    D = DCOIN
    D.draw(c, a)
    ang = 2.4 * math.sin((u - T_COIN) * 0.8) + 0.3 * math.sin((u - T_COIN) * 2.1)
    p1 = (D.cx + D.R * math.cos(ang), D.cy - D.R * math.sin(ang))
    p2 = (D.cx + D.R * math.cos(ang), D.cy + D.R * math.sin(ang))
    for p, lab in ((p1, r"e^{ita}"), (p2, r"e^{-ita}")):
        c.drawLine(D.cx, D.cy, *p, paint(CYAN, 0.6 * a, stroke=2))
        glow_dot(c, *p, 9, CYAN, a, 5)
        draw_math(c, lab, p[0] + 18 * (1 if math.cos(ang) >= 0 else -1), p[1] + (-14 if p is p1 else 34), 30, CYAN, a,
                  align="l" if math.cos(ang) >= 0 else "r")
    c.drawLine(*p1, *p2, paint(GOLD, 0.4 * a, stroke=1.5))
    gx = D.cx + D.R * math.cos(ang)
    glow_dot(c, gx, D.cy, 9, GOLD, a, 6)
    draw_math(c, r"\cos(ta)", gx, D.cy + 44, 30, GOLD, a)
    fa = env(u, T_COIN + 1.0, T_PROD, 0.6, 0.6)
    draw_math(c, r"\mathbb{E}\,[e^{it\varepsilon a}]\ =\ \dfrac{e^{ita}+e^{-ita}}{2}\ =\ \cos(ta)", 1380, 400, 46, WHITE, fa,
              reveal=ramp(u, T_COIN + 1.0, T_COIN + 2.6), glow=0.2)
    fb = env(u, T_COIN + 5.5, T_PROD, 0.6, 0.6)
    draw_math(c, r"\mathbb{E}\,[e^{itU}]\ =\ \dfrac{1}{2}\int_{-1}^{1}e^{itx}\,dx\ =\ \dfrac{\sin t}{t}", 1380, 620, 46, CYAN, fb,
              reveal=ramp(u, T_COIN + 5.5, T_COIN + 7.0), glow=0.2)
    text(c, "均匀分布的重心", 1380, 520, 30, "bold", GREY, fb)


# ---------------------------------------------------------------- 乘起来：sin t / t = ∏ cos(t/2^k)
PP = Plot(200, 380, 1720, 800, 0, 14, -0.3, 1.05)


def prod_K(t, K):
    out = np.ones_like(t)
    for k in range(1, K + 1):
        out = out * np.cos(t / 2 ** k)
    return out


def product(c, u):
    a = env(u, T_PROD, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    pa = a
    PP.axes(c, pa, GREY)
    for v, lab in ((math.pi, r"\pi"), (2 * math.pi, r"2\pi"), (3 * math.pi, r"3\pi"), (4 * math.pi, r"4\pi")):
        draw_math(c, lab, float(PP.sx(v)), float(PP.sy(0)) + 36, 24, GREY, 0.7 * pa)
        c.drawLine(float(PP.sx(v)), float(PP.sy(0)) - 5, float(PP.sx(v)), float(PP.sy(0)) + 5, paint(GREY, 0.6 * pa, stroke=1.4))
    draw_math(c, "t", PP.R + 20, float(PP.sy(0)) + 8, 28, GREY, pa, align="l")
    ts = np.linspace(0.001, 14, 700)
    PP.curve(c, ts, np.sin(ts) / ts, CYAN, 0.9 * pa, 3.0)
    K = 1 + 7 * ramp(u, T_PROD + 3.0, T_PROD + 11.0, lambda x: x)
    k0 = int(K)
    f = smooth(K - k0)
    y = (1 - f) * prod_K(ts, k0) + f * prod_K(ts, min(k0 + 1, 12))
    PP.curve(c, ts, y, GOLD, 0.3 * pa, 9)
    PP.curve(c, ts, y, mix(GOLD, WHITE, 0.25), pa, 2.4)
    Kn = k0 if f < 0.5 else k0 + 1
    readout(c, "K =", f"{Kn:2d}", PP.R - 160, PP.T + 10, pa * (1 - ramp(u, T_PI - 0.5, T_PI)), GOLD, 30)
    draw_math(c, r"\prod_{k=1}^{K}\cos\dfrac{t}{2^k}", float(PP.sx(9.5)), float(PP.sy(0.62)), 36, GOLD,
              pa * (1 - ramp(u, T_PI - 0.5, T_PI)), align="l")
    draw_math(c, r"\frac{\sin t}{t}", float(PP.sx(4.9)), float(PP.sy(-0.2)) + 10, 30, CYAN, pa, align="l")
    fa = env(u, T_PROD + 0.5, T_PI, 0.6, 0.6)
    draw_math(c, r"\dfrac{\sin t}{t}\ =\ \prod_{k=1}^{\infty}\cos\dfrac{t}{2^k}", 960, 210, 60, WHITE, fa,
              reveal=ramp(u, T_PROD + 0.5, T_PROD + 2.2), glow=0.3)
    # π/2 处的竖线
    ka = a * ramp(u, T_PI + 0.3, T_PI + 1.3)
    if ka > 0.003:
        x = float(PP.sx(math.pi / 2))
        c.drawLine(x, PP.T, x, float(PP.sy(0)), paint(MAGENTA, 0.9 * ka, stroke=2))
        glow_dot(c, x, float(PP.sy(2 / math.pi)), 8, MAGENTA, ka, 6)
        draw_math(c, r"t=\frac{\pi}{2}", x + 16, PP.T + 30, 30, MAGENTA, ka, align="l")
        draw_math(c, r"\frac{2}{\pi}", x - 16, float(PP.sy(2 / math.pi)) - 12, 30, MAGENTA, ka, align="r")


# ---------------------------------------------------------------- 韦达公式与 π 的数字
PI_STR = "3.14159265358"


def viete(c, u):
    a = env(u, T_PI, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    draw_math(c, r"\dfrac{2}{\pi}\ =\ \dfrac{\sqrt{2}}{2}\cdot\dfrac{\sqrt{2+\sqrt{2}}}{2}\cdot\dfrac{\sqrt{2+\sqrt{2+\sqrt{2}}}}{2}\cdots",
              960, 215, 54, GOLD, a, reveal=ramp(u, T_PI + 1.5, T_PI + 3.5), glow=0.35)
    k = ramp(u, T_PI + 7.0, T_PI + 8.0)
    text(c, "François Viète · 1593", 960, 340, 28, "serifm", GREY, a * k)
    # 部分积给出的 π 的近似值
    K = int(1 + 15 * ramp(u, T_PI + 4.0, T_PI + 14.0, lambda x: x))
    P = np.prod([math.cos(math.pi / 2 ** (j + 1)) for j in range(1, K + 1)])
    est = 2 / P
    s = f"{est:.11f}"
    ra = a * ramp(u, T_PI + 4.0, T_PI + 4.8)
    if ra > 0.003:
        x0, y0 = 1250, 560
        box = skia.Rect(x0 - 150, y0 - 80, x0 + 470, y0 + 60)
        c.drawRoundRect(box, 12, 12, paint((0.01, 0.014, 0.034), 0.85 * ra))
        c.drawRoundRect(box, 12, 12, paint(GOLD, 0.3 * ra, stroke=1.2))
        text(c, f"抛 {K} 枚硬币（乘到第 {K} 项）", x0 - 130, y0 - 44, 22, "sans", GREY, ra, align="l")
        text(c, "π ≈", x0 - 20, y0 + 22, 40, "serifm", WHITE, ra, align="r")
        f = font("mono", 46)
        x = x0
        good = True
        for i, ch in enumerate(s):
            ok = good and i < len(PI_STR) and ch == PI_STR[i]
            good = ok
            c.drawString(ch, x, y0 + 22, f, paint(GOLD if ok else GREY, ra))
            x += f.measureText(ch)


def draw(c, u):
    tree(c, u)
    falling(c, u)
    coin(c, u)
    product(c, u)
    viete(c, u)


CAPS = [
    (4.4, 10.4, "在 $[-1,1]$ 上均匀地取一个数，等于连续抛硬币：第 $k$ 次决定往左还是往右走 $1/2^k$。"),
    (10.6, 16.4, "像第 2 集的高尔顿板，只是每往下一层，步子就减半——落下来不是钟形，而是均匀的。"),
    (16.6, 21.6, "这就是二进制展开：每一位数字，都是一枚独立的硬币。"),
    (22.4, 28.6, "一枚硬币 $\\pm a$：两个点关于实轴对称，上下抵消，重心正好落在 $\\cos(ta)$。"),
    (28.8, 34.6, "而整个均匀分布的重心是 $\\sin t/t$（第 2 章见过）。"),
    (35.4, 41.4, "硬币相互独立，重心相乘：均匀分布的特征函数，等于一串余弦的乘积。"),
    (41.6, 48.6, "这个恒等式是欧拉写下的。在概率论里，它只是在说“二进制的各位相互独立”。"),
    (49.4, 55.6, "代入 $t=\\pi/2$：左边是 $2/\\pi$，右边每一项都是嵌套的根号——"),
    (55.8, 62.6, "这正是韦达在 1593 年写下的 $\\pi$ 的无穷乘积。每多抛一枚硬币，误差就缩小到约四分之一。"),
    (62.8, 70.0, "四百多年后再看：它不过是在抛硬币。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_TREE + 1.0, "chime", {"f": 660}),
    (T_FALL, "rain", {"dur": 10.0}),
    (T_COIN, "whoosh", {"dur": 1.4}), (T_COIN + 1.0, "chime", {"f": 880}), (T_COIN + 5.5, "chime", {"f": 740}),
    (T_PROD, "whoosh", {"dur": 1.2}), (T_PROD + 0.5, "boom", {}),
    (T_PI, "glitch", {}), (T_PI + 1.5, "riser", {"dur": 2.0}), (T_PI + 3.5, "impact", {}),
]
SFX += [(T_TREE + 0.45 * k, "tick", {"f": 600 + 120 * k}) for k in range(DEPTH)]
SFX += [(T_PROD + 3.0 + 8.0 * (k - 1) / 7, "tick", {"f": 800 + 150 * k}) for k in range(2, 9)]
SFX += [(T_PI + 4.0 + 10.0 * (K - 1) / 15, "coin", {"f": 1500 + 40 * K}) for K in range(2, 17)]

SCENES = [Scene("ch6", DUR, draw, CAPS, SFX, chapter=("06", "抛硬币，抛出 π", "FLIPPING COINS FOR π"), theme=6, bed=6)]
