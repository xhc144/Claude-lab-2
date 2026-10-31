"""第 7 章 两边不能同时尖。|f|² 和 |f̂|² 都是概率密度（帕塞瓦尔 = 总概率守恒），
它们的标准差之积 σ_x σ_ξ ≥ 1/2，只有高斯取等号；盒子形状的频谱方差是无穷大。量子力学里这就是海森堡不确定性原理。"""

import math

import numpy as np
import skia

from gfx import (CYAN, GOLD, GREY, MAGENTA, RED, WHITE, Plot, draw_math, env, lerp, mix, paint, ramp, smooth,
                 text)
from scene import Scene

# 计算用的网格：x ∈ [-40, 40)，FFT 得到 ξ
NX = 8192
L = 80.0
XG = (np.arange(NX) - NX // 2) * (L / NX)
DX = L / NX
XI = np.fft.fftshift(np.fft.fftfreq(NX, DX)) * 2 * np.pi
DXI = XI[1] - XI[0]


def normalize(f):
    return f / math.sqrt(np.sum(np.abs(f) ** 2) * DX)


SHAPES = {
    "gauss": normalize(np.exp(-XG ** 2 / 4)),
    "laplace": normalize(np.exp(-np.abs(XG) / math.sqrt(2))),
    "two": normalize(np.exp(-(XG - 1.6) ** 2 / (4 * 0.45 ** 2)) + np.exp(-(XG + 1.6) ** 2 / (4 * 0.45 ** 2))),
    "box": normalize((np.abs(XG) <= math.sqrt(3)).astype(float)),
}


def spectrum(f):
    F = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(f))) * DX / math.sqrt(2 * math.pi)
    return np.abs(F) ** 2


def sd(grid, dens, d):
    m = np.sum(grid * dens) * d
    return math.sqrt(max(np.sum((grid - m) ** 2 * dens) * d, 0.0))


T_A = 4.0
T_SQ = 17.0
T_SH = 33.0
T_Q = 52.5
DUR = 67.0


def scale_s(u):
    """高斯的宽度。"""
    k1 = ramp(u, T_SQ + 1.0, T_SQ + 4.0)
    k2 = ramp(u, T_SQ + 6.5, T_SQ + 10.0)
    k3 = ramp(u, T_SQ + 12.0, T_SQ + 14.5)
    s = lerp(1.0, 0.62, k1)
    s = lerp(s, 1.6, k2)
    return lerp(s, 1.0, k3)


SEQ = [(T_SH + 0.5, T_SH + 2.5, "gauss", "laplace"), (T_SH + 7.5, T_SH + 9.5, "laplace", "two"),
       (T_SH + 13.5, T_SH + 15.0, "two", "box"), (T_SH + 18.0, T_SH + 19.5, "box", "gauss")]


def shape_at(u):
    """返回 (f, 是否含跳跃间断)。"""
    if u < T_SQ:
        return SHAPES["gauss"], False
    if u < T_SH:
        s = scale_s(u)
        return normalize(np.exp(-XG ** 2 / (4 * s * s))), False
    cur = SHAPES["gauss"]
    jump = False
    for t0, t1, a, b in SEQ:
        if u >= t1:
            cur, jump = SHAPES[b], b == "box"
        elif u > t0:
            w = smooth((u - t0) / (t1 - t0))
            cur = normalize((1 - w) * SHAPES[a] + w * SHAPES[b])
            # 只要掺进一点盒子，f 就有跳跃间断，频谱的方差就是无穷大
            jump = (a == "box" and w < 0.998) or (b == "box" and w > 0.002)
            break
    if u >= T_Q:
        # 量子：加一个载波 e^{ik0x}，频谱整体平移，宽度不变
        k0 = 3.5 * ramp(u, T_Q + 0.5, T_Q + 3.0)
        cur = cur * np.exp(1j * k0 * XG)
    return cur, jump


YMAX = 1.3
PL = Plot(110, 300, 760, 720, -5, 5, 0, YMAX)
PR = Plot(1160, 300, 1810, 720, -5, 5, 0, YMAX)
SEL = (XG >= -5.2) & (XG <= 5.2)
SELK = (XI >= -5.2) & (XI <= 5.2)
METER = (960, 760, 330)        # 中间的量表：底部 y，顶部 y
MMAX = 2.0


def draw(c, u):
    a = env(u, T_A, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    f, jump = shape_at(u)
    dens = np.abs(f) ** 2
    spec = spectrum(f)
    sx = sd(XG, dens, DX)
    sk = sd(XI, spec, DXI)
    # 左：|f|²
    PL.axes(c, a, CYAN)
    xs, ys = XG[SEL], dens[SEL]
    PL.fill(c, xs, np.minimum(ys, YMAX), CYAN, a)
    PL.curve(c, xs, np.minimum(ys, YMAX), CYAN, a, 2.8)
    if u > T_Q:
        qa = a * ramp(u, T_Q + 0.5, T_Q + 1.5)
        # 波包：实部在包络 ±|f| 里振荡，相位随时间推进
        amp = 0.30 / (np.max(np.abs(f)) + 1e-9)
        re = np.real(f[SEL] * np.exp(-1j * 4.0 * (u - T_Q)))
        env_ = np.abs(f[SEL])
        PL.curve(c, xs, 0.92 + amp * env_, GREY, 0.5 * qa, 1.2)
        PL.curve(c, xs, 0.92 - amp * env_, GREY, 0.5 * qa, 1.2)
        PL.curve(c, xs, 0.92 + amp * re, WHITE, 0.85 * qa, 2.0)
    draw_math(c, r"|f(x)|^2", PL.L + 10, PL.T - 16, 34, CYAN, a, align="l")
    draw_math(c, "x", PL.R + 20, PL.B + 8, 28, GREY, a, align="l")
    # 右：|f̂|²
    PR.axes(c, a, MAGENTA)
    ks, kv = XI[SELK], spec[SELK]
    PR.fill(c, ks, np.minimum(kv, YMAX), MAGENTA, a)
    PR.curve(c, ks, np.minimum(kv, YMAX), MAGENTA, a, 2.8)
    draw_math(c, r"|\hat f(\xi)|^2", PR.L + 10, PR.T - 16, 34, MAGENTA, a, align="l")
    draw_math(c, r"\xi", PR.R + 20, PR.B + 8, 28, GREY, a, align="l")
    for P, rgb in ((PL, CYAN), (PR, MAGENTA)):
        for v in (-4, -2, 0, 2, 4):
            draw_math(c, str(v) if v >= 0 else f"-{-v}", float(P.sx(v)), P.B + 32, 22, GREY, 0.6 * a)
    # 标准差的横条
    ka = a * ramp(u, T_SQ - 1.0, T_SQ)
    for P, s_, grid, d, rgb in ((PL, sx, XG, dens, CYAN), (PR, sk, XI, spec, MAGENTA)):
        if ka <= 0.003:
            continue
        m = float(np.sum(grid * d) * (grid[1] - grid[0]))
        y = P.B + 70
        x0, x1 = float(P.sx(m - s_)), float(P.sx(m + s_))
        x0, x1 = max(x0, P.L - 20), min(x1, P.R + 20)
        c.drawLine(x0, y, x1, y, paint(rgb, ka, stroke=3))
        c.drawLine(x0, y - 8, x0, y + 8, paint(rgb, ka, stroke=3))
        c.drawLine(x1, y - 8, x1, y + 8, paint(rgb, ka, stroke=3))
    # 中间：乘积的量表
    if ka > 0.003:
        cx, yb, yt = METER
        def my(v):
            return yb - (yb - yt) * min(v, MMAX) / MMAX
        prod = sx * sk
        inf = jump or sk > 6
        c.drawRoundRect(skia.Rect(cx - 26, yt, cx + 26, yb), 8, 8, paint(GREY, 0.10 * ka))
        c.drawRoundRect(skia.Rect(cx - 26, yt, cx + 26, yb), 8, 8, paint(GREY, 0.35 * ka, stroke=1.2))
        top = yt if inf else my(prod)
        rgb = GOLD if (abs(prod - 0.5) < 0.01 and not inf) else (RED if inf else mix(GOLD, MAGENTA, 0.4))
        c.drawRoundRect(skia.Rect(cx - 20, top, cx + 20, yb - 4), 6, 6, paint(rgb, 0.55 * ka))
        c.drawRect(skia.Rect(cx - 20, top, cx + 20, top + 3), paint(mix(rgb, WHITE, 0.5), ka))
        yh = my(0.5)
        c.drawLine(cx - 60, yh, cx + 60, yh, paint(WHITE, 0.9 * ka, stroke=2))
        draw_math(c, r"\frac{1}{2}", cx + 70, yh + 10, 28, WHITE, ka, align="l")
        val = "∞" if inf else f"{prod:.3f}"
        draw_math(c, r"\sigma_x\,\sigma_\xi", cx, yt - 70, 34, WHITE, ka)
        text(c, val, cx, yt - 20, 34 if not inf else 44, "mono", rgb, ka)
        text(c, f"σx = {sx:.2f}", (PL.L + PL.R) / 2, PL.B + 110, 28, "mono", CYAN, ka)
        text(c, "σξ = ∞" if inf else f"σξ = {sk:.2f}", (PR.L + PR.R) / 2, PR.B + 110, 28, "mono", MAGENTA, ka)
    # 公式
    fa = env(u, T_A + 6.0, T_SQ, 0.6, 0.6)
    draw_math(c, r"\int|f(x)|^2dx\ =\ \int|\hat f(\xi)|^2d\xi\ =\ 1", 960, 175, 50, WHITE, fa,
              reveal=ramp(u, T_A + 6.0, T_A + 7.6), glow=0.25)
    text(c, "帕塞瓦尔恒等式 = 总概率守恒", 960, 240, 28, "bold", GOLD, fa * ramp(u, T_A + 8.0, T_A + 8.8))
    fb = env(u, T_SQ + 0.5, T_Q, 0.6, 0.6)
    draw_math(c, r"\sigma_x\,\sigma_\xi\ \geq\ \dfrac{1}{2}", 960, 180, 58, GOLD, fb,
              reveal=ramp(u, T_SQ + 0.5, T_SQ + 1.8), glow=0.3)
    fc = env(u, T_Q + 0.3, DUR, 0.6, 0.8)
    draw_math(c, r"\sigma_x\,\sigma_p\ \geq\ \dfrac{\hbar}{2}", 960, 180, 58, GOLD, fc,
              reveal=ramp(u, T_Q + 0.3, T_Q + 1.6), glow=0.3)
    text(c, "位置", (PL.L + PL.R) / 2, PL.T - 60, 30, "bold", CYAN, fc)
    text(c, "动量", (PR.L + PR.R) / 2, PR.T - 60, 30, "bold", MAGENTA, fc)
    # 形状的名字
    names = [(T_SH + 2.5, T_SH + 7.5, r"e^{-|x|/\sqrt{2}}"), (T_SH + 9.5, T_SH + 13.5, r"\mathrm{two\ bumps}"),
             (T_SH + 15.0, T_SH + 18.0, r"\mathbf{1}_{[-\sqrt{3},\sqrt{3}]}")]
    for t0, t1, tex in names:
        na = env(u, t0, t1, 0.4, 0.4) * a
        if t0 == T_SH + 9.5:
            text(c, "两个峰", (PL.L + PL.R) / 2 + 220, PL.T + 40, 30, "bold", WHITE, na)
        else:
            draw_math(c, "f=" + tex, (PL.L + PL.R) / 2 + 220, PL.T + 40, 32, WHITE, na)


CAPS = [
    (4.4, 10.4, "取一个函数 $f$，让 $|f|^2$ 的总面积为 $1$：它就是一个概率密度。"),
    (10.6, 16.6, "做傅里叶变换，$|\\hat f|^2$ 的面积还是 $1$——帕塞瓦尔恒等式，说的就是总概率守恒。"),
    (17.4, 24.6, "把一边压窄，另一边就变宽：两个标准差的乘积，始终不小于 $1/2$。"),
    (24.8, 32.6, "对高斯来说，乘积恰好等于 $1/2$——它是两边都最集中的形状。"),
    (33.4, 40.4, "换成尖顶的 $e^{-|x|/\\sqrt{2}}$：乘积是 $1/\\sqrt{2}\\approx 0.71$。"),
    (40.6, 46.4, "两个分开的峰：位置更不确定，频谱里还多出了振荡，乘积更大。"),
    (46.6, 52.0, "方方正正的盒子：边缘一跳，频谱衰减太慢，方差是无穷大。"),
    (52.8, 59.6, "在量子力学里，$|f|^2$ 是粒子位置的分布，$|\\hat f|^2$ 是动量的分布（取 $\\hbar=1$）。"),
    (59.8, 66.4, "这就是海森堡不确定性原理：位置和动量，没法同时确定。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_A + 6.0, "chime", {"f": 660}), (T_A + 8.0, "chime", {"f": 990}),
    (T_SQ + 0.5, "chime", {"f": 880}),
    (T_SQ + 1.0, "pitch", {"dur": 3.0, "up": False}), (T_SQ + 6.5, "pitch", {"dur": 3.5, "up": True}),
    (T_SQ + 12.0, "pitch", {"dur": 2.5, "up": False}),
    (T_SH + 0.5, "whoosh", {"dur": 2.0}), (T_SH + 7.5, "whoosh", {"dur": 2.0}),
    (T_SH + 13.5, "glitch", {}), (T_SH + 15.0, "alarm", {}), (T_SH + 18.0, "whoosh", {"dur": 1.5}),
    (T_Q, "boom", {}), (T_Q + 0.3, "chime", {"f": 1320}),
]


def tone(u):
    """宽度变化时一个持续音：音高跟着 σ_ξ。"""
    s = np.array([scale_s(x) for x in u[::480]])
    s = np.interp(np.arange(len(u)), np.arange(0, len(u), 480)[:len(s)], s)
    amp = 0.13 * ((u > T_SQ + 0.6) & (u < T_SH - 0.4)) * np.clip((u - T_SQ - 0.6) / 0.8, 0, 1) * np.clip((T_SH - 0.4 - u) / 0.8, 0, 1)
    return 220 / s, amp


SCENES = [Scene("ch7", DUR, draw, CAPS, SFX, tone=tone, chapter=("07", "两边不能同时尖", "THE UNCERTAINTY PRINCIPLE"),
                theme=7, bed=7)]
