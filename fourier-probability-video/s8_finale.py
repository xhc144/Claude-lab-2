"""尾声：傅里叶分析 ↔ 概率论 的对照表，一句总结，片名。"""

import numpy as np

from gfx import (CYAN, GOLD, GREY, H, MAGENTA, W, WHITE, clamp, colored_dots, env, eout, font, glow_dot, mix,
                 paint, ramp, ring_flare, smooth, text)
from scene import Scene

ROWS = [
    ("傅里叶变换", "特征函数：绕圈的重心"),
    ("反演公式", "重心曲线记住了整个分布"),
    ("卷积定理", "独立随机变量相加"),
    ("高斯是自己的变换", "中心极限定理"),
    ("傅里叶级数", "圆上的随机变量"),
    ("泊松求和公式", "把直线缠到圆上"),
    ("热方程", "随机游走"),
    ("韦达公式", "二进制位是独立的硬币"),
    ("帕塞瓦尔恒等式", "总概率守恒"),
    ("不确定性原理", "两个标准差之积 ≥ 1/2"),
]
T_ROW0 = 1.2
ROW_DT = 1.7
T_SUM = 22.5
T_END = 33.0
DUR = 44.0
Y0, DYR = 236, 66


def table(c, u):
    a = env(u, 0.3, T_SUM, 0.8, 0.8)
    if a <= 0.003:
        return
    text(c, "傅里叶分析", 860, 160, 40, "serif", MAGENTA, a, align="r")
    text(c, "概率论", 1060, 160, 40, "serif", CYAN, a, align="l")
    c.drawLine(960, 120, 960, Y0 + DYR * len(ROWS) - 20, paint(WHITE, 0.18 * a, stroke=1.2))
    for i, (l, r) in enumerate(ROWS):
        t0 = T_ROW0 + i * ROW_DT
        k = ramp(u, t0, t0 + 0.6, eout)
        if k <= 0:
            continue
        y = Y0 + DYR * i + 30
        dx = 40 * (1 - k)
        text(c, l, 860 + dx, y, 34, "sans", WHITE, a * k, align="r")
        text(c, r, 1060 - dx, y, 34, "sans", mix(CYAN, WHITE, 0.55), a * k, align="l")
        # 中间的连接：一颗沿竖线滑下来的光点，到位后横向展开
        g = ramp(u, t0, t0 + 0.5)
        c.drawLine(960 - 70 * g, y - 12, 960 + 70 * g, y - 12, paint(GOLD, 0.8 * a * k, stroke=2))
        glow_dot(c, 960, y - 12, 5, GOLD, a * k, 5)
        flash = 1 - clamp((u - t0) / 0.6)
        if flash > 0:
            c.drawCircle(960, y - 12, 30 * (1 - flash) + 6, paint(GOLD, 0.6 * flash * a, stroke=2))


RING_N = 900
_rng = np.random.default_rng(88)
RING_TH = np.linspace(0, 2 * np.pi, RING_N, endpoint=False)
RING_J = _rng.normal(0, 1, RING_N)
RING_X = _rng.normal(0, 1, RING_N)


def summary(c, u):
    a = env(u, T_SUM, T_END + 0.3, 0.8, 0.9)
    if a <= 0.003:
        return
    k = u - T_SUM
    # 一圈缓慢转动的粒子，重心在中间
    t = 0.6 + 0.35 * k
    ang = t * RING_X * 2.2 + 0.08 * k
    r = 330 + 8 * RING_J
    xs = W / 2 + r * np.cos(ang)
    ys = H / 2 - 40 - r * np.sin(ang)
    colored_dots(c, xs, ys, (RING_X + 2.5) / 5, 0.55 * a, 3)
    z = np.mean(np.exp(1j * ang))
    glow_dot(c, W / 2 + 330 * z.real, H / 2 - 40 - 330 * z.imag, 7, GOLD, a, 6)
    l1 = "傅里叶分析问的是："
    l2 = "把一个随机的东西绕成圆，"
    l3 = "在每一种转速下，它的重心在哪里。"
    for j, (s, size, rgb) in enumerate(((l1, 40, GREY), (l2, 60, WHITE), (l3, 60, GOLD))):
        kk = ramp(u, T_SUM + 0.4 + j * 1.6, T_SUM + 1.4 + j * 1.6)
        y = H / 2 - 110 + j * 96 + 16 * (1 - kk)
        if rgb is GOLD:
            text(c, s, W / 2, y, size, "serif", GOLD, 0.3 * a * kk, p=paint(GOLD, 0.3 * a * kk, stroke=5))
        text(c, s, W / 2, y, size, "serif" if size > 50 else "sans", rgb, a * kk)


def ending(c, u):
    a = env(u, T_END, DUR, 1.0, 1.4)
    if a <= 0.003:
        return
    k = u - T_END
    cx, cy = W / 2, H / 2 - 30
    ring_flare(c, cx, cy, 230, k / 2.2, GOLD, a)
    s = "当概率开始旋转"
    size = 96
    f = font("serif", size)
    w = sum(f.measureText(ch) for ch in s) + 14 * (len(s) - 1)
    x = cx - w / 2
    for i, ch in enumerate(s):
        kk = clamp((k - 0.2 - i * 0.06) / 0.6)
        if kk > 0:
            c.drawString(ch, x, cy + 30, f, paint(GOLD, 0.3 * a * smooth(kk), stroke=5))
            c.drawString(ch, x, cy + 30, f, paint(WHITE, a * smooth(kk)))
        x += f.measureText(ch) + 14
    sa = a * ramp(u, T_END + 1.4, T_END + 2.4)
    text(c, "WHEN  PROBABILITY  SPINS", cx, cy - 80, 22, "orbm", CYAN, 0.8 * sa, track=10)
    text(c, "画面与声音全部由 Python 程序生成  ·  Claude-lab-2", cx, cy + 120, 26, "sans", GREY, 0.8 * sa)


def draw(c, u):
    table(c, u)
    summary(c, u)
    ending(c, u)


SFX = [(0.0, "whoosh", {"dur": 1.6})]
_PENTA = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51, 1567.98, 1760.0]
SFX += [(T_ROW0 + i * ROW_DT, "chime", {"f": _PENTA[i], "amp": 0.7}) for i in range(len(ROWS))]
SFX += [(T_SUM - 0.3, "whoosh", {"dur": 1.6}), (T_SUM + 0.4, "swell", {"dur": 6.0}),
        (T_END, "impact", {}), (T_END + 0.1, "shimmer", {"dur": 5.0}), (T_END + 0.2, "outro", {"dur": DUR - T_END})]

SCENES = [Scene("finale", DUR, draw, (), SFX, theme=8, hud=0.6, fade_in=0.6, fade_out=0.1, bed=8)]
