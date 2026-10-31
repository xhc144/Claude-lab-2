"""第 4 章 圆上的随机：傅里叶级数。随机角度 Θ 只能用整数圈数去绕（θ 和 θ+2π 是同一个点），
于是频率变成离散的 k；c_k = E[e^{ikΘ}] 是绕 k 圈的重心，叠回去就是傅里叶级数。
最后把直线缠到圆上：Θ = X mod 2π 的系数正好是 φ_X(k)——泊松求和公式。"""

import math

import numpy as np
import skia

from dist import circle_density, vonmises_mix_coef
from gfx import (CYAN, GOLD, GREY, MAGENTA, RED, WHITE, Disk, Plot, clamp, colored_dots, draw_math, env,
                 glow_dot, lerp, mix, paint, path_xy, ramp, readout, smooth, stroke_xy, text)
from scene import Scene

# 圆上的分布：两个 von Mises 的混合
VW, VMU, VK = [0.62, 0.38], [0.7, 3.4], [3.5, 9.0]
KMAX = 40
COEF = vonmises_mix_coef(VW, VMU, VK, KMAX)
TH = np.linspace(-np.pi, np.pi, 721)
PTH = circle_density(COEF, TH)

N = 1000
_cdf = np.cumsum(PTH)
_cdf /= _cdf[-1]
_rng = np.random.default_rng(44)
THS = np.interp((np.arange(N) + 0.5) / N, _cdf, TH)[_rng.permutation(N)]
HU = _rng.random(N) ** 0.85
VAL = (THS + np.pi) / (2 * np.pi)
STAG = _rng.random(N)

MC = (560, 520)
R0 = 200
HS = 210          # 密度 → 径向像素

T_A = 4.0
T_SPIN = (4.6, 8.4)
T_B = 16.0
T_C = 34.0
T_D = 50.0
T_E = 64.0
T_E2 = 76.5
DUR = 93.0
THETA_STOP = 0.95


def spin_angle(u):
    k = clamp((u - T_SPIN[0]) / (T_SPIN[1] - T_SPIN[0]))
    return THETA_STOP - 14 * math.pi * (1 - k) ** 3


def radial(theta, h, base=R0, cx=MC[0], cy=MC[1]):
    r = base + h
    return cx + r * np.cos(theta), cy - r * np.sin(theta)


def band(c, theta, h_in, h_out, rgb, a, cx=MC[0], cy=MC[1], base=R0):
    """圆周上一圈带子：内缘 base+h_in，外缘 base+h_out。"""
    xo, yo = radial(theta, h_out, base, cx, cy)
    xi, yi = radial(theta[::-1], h_in[::-1], base, cx, cy)
    p = path_xy(np.concatenate([xo, xi]), np.concatenate([yo, yi]), close=True)
    c.drawPath(p, paint(rgb, 0.16 * a))
    stroke_xy(c, xo, yo, rgb, a, 2.6)


# ---------------------------------------------------------------- A：圆上的分布
def partial_sum(K):
    return circle_density(COEF[:K + 1], TH)


def k_partial(u):
    """D 段里部分和的项数 K（可以是小数，用来平滑过渡）。"""
    return 10 * ramp(u, T_D + 1.0, T_D + 11.0, lambda x: x)


def main_circle(c, u):
    a = env(u, T_A, T_E + 0.5, 0.8, 0.8)
    if a <= 0.003:
        return
    cx, cy = MC
    c.drawCircle(cx, cy, R0, paint(CYAN, 0.16 * a, stroke=10))
    c.drawCircle(cx, cy, R0, paint(CYAN, 0.6 * a, stroke=2))
    # 密度曲线（D 段换成部分和）
    k_in = ramp(u, T_SPIN[1] + 0.5, T_SPIN[1] + 3.0)
    if u < T_D:
        h = HS * PTH * k_in
        if k_in > 0:
            band(c, TH, np.zeros_like(TH), h, CYAN, a * k_in)
    else:
        K = k_partial(u)
        i = int(K)
        f = smooth(clamp((K - i) * 2))
        p = (1 - f) * partial_sum(i) + f * partial_sum(min(i + 1, KMAX))
        h = HS * p
        stroke_xy(c, *radial(TH, HS * PTH), GREY, 0.45 * a, 1.4)
        band(c, TH, np.zeros_like(TH), h, GOLD, a)
        Kn = i if f < 0.5 else i + 1
        readout(c, "K =", f"{Kn:2d}", cx - 60, cy + R0 + 175, a, GOLD, 30)
        # 刚加上的那一项：k 个起伏的波
        if Kn >= 1:
            term = np.real(COEF[Kn] * np.exp(-1j * Kn * TH))
            term /= np.max(np.abs(term)) + 1e-9
            rr = 120 + 26 * term
            xs, ys = cx + rr * np.cos(TH), cy - rr * np.sin(TH)
            stroke_xy(c, xs, ys, MAGENTA, 0.8 * a, 2.2)
    # 粒子
    pa = a * ramp(u, T_SPIN[1], T_SPIN[1] + 1.5) * (1 - ramp(u, T_D - 0.5, T_D + 0.5))
    if pa > 0.003:
        appear = np.clip((u - T_SPIN[1] - 1.8 * STAG) / 0.5, 0, 1)
        sel = appear > 0
        r = R0 + 4 + HU * HS * np.interp(THS, TH, PTH)
        colored_dots(c, cx + r[sel] * np.cos(THS[sel]), cy - r[sel] * np.sin(THS[sel]), VAL[sel], pa, 3.2)
    # 转盘指针
    sa = env(u, T_A + 0.2, T_SPIN[1] + 1.6, 0.4, 0.8)
    if sa > 0.003:
        ang = spin_angle(u)
        tip = (cx + (R0 - 18) * math.cos(ang), cy - (R0 - 18) * math.sin(ang))
        c.drawLine(cx, cy, *tip, paint(WHITE, 0.9 * sa, stroke=4))
        c.drawCircle(cx, cy, 10, paint(WHITE, sa))
        if u > T_SPIN[1]:
            glow_dot(c, cx + R0 * math.cos(THETA_STOP), cy - R0 * math.sin(THETA_STOP), 9, GOLD, sa, 6)
    draw_math(c, r"\Theta", cx, cy + 12, 40, WHITE, a * ramp(u, T_SPIN[1] + 1.0, T_SPIN[1] + 2.0) * (1 - ramp(u, T_D - 0.5, T_D)))


# ---------------------------------------------------------------- B：只能用整数圈数去绕
TH0 = 2.25
DB = Disk(1390, 500, 210)


def t_wind(u):
    if u < T_B + 5.5:
        return 1.5
    if u < T_B + 8.0:
        return lerp(1.5, 2.0, ramp(u, T_B + 5.5, T_B + 8.0))
    if u < T_B + 10.0:
        return 2.0
    return lerp(2.0, 3.5, ramp(u, T_B + 10.0, T_C - 1.0, lambda x: x))


def winding(c, u):
    a = env(u, T_B, T_C, 0.8, 0.6)
    if a <= 0.003:
        return
    cx, cy = MC
    p0 = (cx + R0 * math.cos(TH0), cy - R0 * math.sin(TH0))
    glow_dot(c, *p0, 9, GOLD, a, 6)
    draw_math(c, r"\theta", p0[0] - 30, p0[1] - 30, 34, GOLD, a, align="r")
    draw_math(c, r"\theta+2\pi", p0[0] - 30, p0[1] + 8, 34, GOLD, a * ramp(u, T_B + 1.0, T_B + 1.8), align="r")
    t = t_wind(u)
    DB.draw(c, a)
    readout(c, "t =", f"{t:4.2f}", DB.cx - 70, DB.cy + DB.R + 80, a, MAGENTA, 32)
    k = ramp(u, T_B + 1.6, T_B + 3.0)
    a1 = t * TH0
    a2 = t * (TH0 + 2 * math.pi)
    q1 = (DB.cx + DB.R * math.cos(a1), DB.cy - DB.R * math.sin(a1))
    q2 = (DB.cx + DB.R * math.cos(a2), DB.cy - DB.R * math.sin(a2))
    gap = abs((t % 1.0 + 0.5) % 1.0 - 0.5)       # 离最近的整数有多远
    ok = gap < 0.02
    rgb2 = GOLD if ok else RED
    glow_dot(c, *q1, 9, GOLD, a * k, 6)
    glow_dot(c, *q2, 8 if not ok else 11, rgb2, a * k, 6)
    draw_math(c, r"e^{it\theta}", q1[0] + 22 * math.cos(a1), q1[1] - 22 * math.sin(a1) + 10, 30, GOLD, a * k,
              align="l" if math.cos(a1) > 0 else "r")
    if not ok:
        draw_math(c, r"e^{it(\theta+2\pi)}", q2[0] + 26 * math.cos(a2), q2[1] - 26 * math.sin(a2) + 10, 30, RED,
                  a * k, align="l" if math.cos(a2) > 0 else "r")
    # 弯曲的连线：从左边的点射向两个像
    for q, rgb in ((q1, GOLD), (q2, rgb2)):
        ss = np.linspace(0, 1, 50)
        mx, my = (p0[0] + q[0]) / 2, min(p0[1], q[1]) - 160
        bx = (1 - ss) ** 2 * p0[0] + 2 * (1 - ss) * ss * mx + ss ** 2 * q[0]
        by = (1 - ss) ** 2 * p0[1] + 2 * (1 - ss) * ss * my + ss ** 2 * q[1]
        n = max(2, int(50 * k))
        stroke_xy(c, bx[:n], by[:n], rgb, 0.35 * a, 1.6)
    mark = "重合 ✓" if ok else "不是同一个点 ×"
    text(c, mark, DB.cx, DB.cy - DB.R - 50, 34, "bold", GOLD if ok else RED, a * k)
    fa = env(u, T_B + 8.6, T_C, 0.6, 0.6)
    draw_math(c, r"e^{it(\theta+2\pi)}=e^{it\theta}\ \ \Longleftrightarrow\ \ e^{2\pi it}=1\ \ \Longleftrightarrow\ \ t\in\mathbb{Z}",
              960, 170, 44, WHITE, fa, reveal=ramp(u, T_B + 8.6, T_B + 10.4), glow=0.2)


# ---------------------------------------------------------------- C：绕 k 圈的重心 = 傅里叶系数
SMALL = [(1120, 300), (1390, 300), (1660, 300), (1120, 560), (1390, 560), (1660, 560)]
SR = 95
SUB = np.arange(0, N, 3)
BARS = Plot(1040, 700, 1780, 880, -0.6, 10.6, 0, 1.05)


def coeffs(c, u):
    a = env(u, T_C, T_E + 0.3, 0.8, 0.6)
    if a <= 0.003:
        return
    da = a * (1 - ramp(u, T_D - 0.6, T_D + 0.2))
    for j, (x, y) in enumerate(SMALL):
        k = j + 1
        kk = ramp(u, T_C + 0.6 + j * 0.9, T_C + 2.0 + j * 0.9)
        if kk <= 0 or da <= 0.003:
            continue
        m = lerp(1.0, k, kk)
        c.drawCircle(x, y, SR, paint(CYAN, 0.45 * da * kk, stroke=1.5))
        ang = m * THS[SUB]
        colored_dots(c, x + SR * np.cos(ang), y - SR * np.sin(ang), VAL[SUB], da * kk, 2.6)
        # 重心：用当前的（可能是小数的）圈数直接对样本求平均
        z = complex(np.mean(np.exp(1j * m * THS)))
        gx, gy = x + SR * z.real, y - SR * z.imag
        c.drawLine(x, y, gx, gy, paint(GOLD, 0.9 * da * kk, stroke=2.4))
        glow_dot(c, gx, gy, 6, GOLD, da * kk, 5)
        draw_math(c, f"k={k}", x, y + SR + 40, 26, WHITE, 0.8 * da * kk)
    # 系数的柱状图
    ba = a * ramp(u, T_C + 2.0, T_C + 3.0)
    BARS.axes(c, ba, GREY)
    draw_math(c, r"|c_k|", BARS.L - 10, BARS.T - 14, 28, GOLD, ba, align="l")
    Kd = k_partial(u) if u > T_D else 99
    for k in range(0, 11):
        v = abs(COEF[k])
        x = float(BARS.sx(k))
        y = float(BARS.sy(v))
        on = k <= Kd + 0.5
        col_ = GOLD if on else GREY
        c.drawRect(skia.Rect(x - 18, y, x + 18, BARS.B), paint(col_, (0.35 if on else 0.15) * ba))
        c.drawRect(skia.Rect(x - 18, y, x + 18, y + 3), paint(mix(col_, WHITE, 0.4), ba))
        draw_math(c, str(k), x, BARS.B + 30, 22, GREY, 0.7 * ba)
    fa = env(u, T_C + 0.4, T_D, 0.6, 0.6)
    draw_math(c, r"c_k\ =\ \mathbb{E}\,[\,e^{ik\Theta}\,]", 960, 165, 50, WHITE, fa,
              reveal=ramp(u, T_C + 0.4, T_C + 1.8), glow=0.25)
    fd = env(u, T_D + 0.3, T_E + 0.3, 0.6, 0.6)
    draw_math(c, r"p(\theta)\ =\ \dfrac{1}{2\pi}\sum_{k=-\infty}^{\infty} c_k\,e^{-ik\theta}", 1390, 330, 56, WHITE, fd,
              reveal=ramp(u, T_D + 0.3, T_D + 2.0), glow=0.25)
    text(c, "傅里叶级数", 1390, 480, 38, "bold", GOLD, fd * ramp(u, T_D + 2.0, T_D + 3.0))
    text(c, "FOURIER SERIES", 1390, 520, 18, "orbm", GOLD, 0.6 * fd * ramp(u, T_D + 2.0, T_D + 3.0), track=6)


# ---------------------------------------------------------------- E：把直线缠到圆上（泊松求和）
MU, SD = 1.6, 1.5
LS = 80                      # 直线上每单位的像素；一段 2π 长 503 像素，正好绕成半径 80 的圆
LX0 = 960 - 3 * math.pi * LS
LY = 600
SEG_RGB = [MAGENTA, CYAN, GOLD]
FINAL = (560, 470)
FR = 190
HSE = 520                    # 密度 → 像素


def fline(x):
    return np.exp(-0.5 * ((x - MU) / SD) ** 2) / (SD * math.sqrt(2 * math.pi))


def phiX(t):
    return np.exp(1j * MU * t - 0.5 * (SD * t) ** 2)


SEG_X = [np.linspace(-3 * math.pi + 2 * math.pi * j, -math.pi + 2 * math.pi * j, 361) for j in range(3)]


def seg_geometry(j, kb, km):
    """第 j 段在弯曲进度 kb、合并进度 km 时的位置。返回 (点 x, 点 y, 外法线 nx, ny, 缩放)。"""
    xs = SEG_X[j]
    xc = -2 * math.pi + 2 * math.pi * j
    sigma = (xs - xc) * LS
    ax = LX0 + (xc + 3 * math.pi) * LS
    r = LS
    if kb < 1e-4:
        px, py = ax + sigma, np.full_like(sigma, LY)
        nx, ny = np.zeros_like(sigma), -np.ones_like(sigma)
    else:
        kap = kb / r
        px = ax + np.sin(kap * sigma) / kap
        py = LY + (1 - np.cos(kap * sigma)) / kap
        nx, ny = np.sin(kap * sigma), -np.cos(kap * sigma)
    if km > 0:
        # 弯成圆以后：圆心 (ax, LY+r)，平移并放大到 FINAL
        cx0, cy0 = ax, LY + r
        s = lerp(1.0, FR / r, km)
        cx1, cy1 = lerp(cx0, FINAL[0], km), lerp(cy0, FINAL[1], km)
        px = cx1 + (px - cx0) * s
        py = cy1 + (py - cy0) * s
    return px, py, nx, ny


def wrap_scene(c, u):
    a = env(u, T_E, DUR, 0.8, 0.8)
    if a <= 0.003:
        return
    kb = ramp(u, T_E + 4.0, T_E + 6.5)
    km = ramp(u, T_E + 7.0, T_E + 9.5)
    ks = ramp(u, T_E + 9.5, T_E + 11.0)       # 叠起来
    # 直线和分段刻度
    la = a * (1 - kb)
    if la > 0.003:
        c.drawLine(LX0 - 40, LY, LX0 + 6 * math.pi * LS + 40, LY, paint(GREY, 0.5 * la, stroke=1.5))
        for m, lab in ((-3, r"-3\pi"), (-1, r"-\pi"), (1, r"\pi"), (3, r"3\pi")):
            x = LX0 + (m + 3) * math.pi * LS
            c.drawLine(x, LY - 8, x, LY + 8, paint(WHITE, 0.6 * la, stroke=1.6))
            draw_math(c, lab, x, LY + 40, 26, GREY, 0.8 * la)
        draw_math(c, r"f(x)", float(LX0 + (MU + 3 * math.pi) * LS) + 70, LY - 150, 34, WHITE, la)
    # 叠放的基线：中间那段在最里，然后是右段、左段
    order = [1, 2, 0]
    hs = [HSE * fline(SEG_X[j]) for j in range(3)]
    base_cum = {1: np.zeros(361), 2: hs[1], 0: hs[1] + hs[2]}
    for j in order:
        px, py, nx, ny = seg_geometry(j, kb, km)
        h = hs[j]
        off = base_cum[j] * ks
        x_in, y_in = px + nx * off, py + ny * off
        x_out, y_out = px + nx * (off + h), py + ny * (off + h)
        p = path_xy(np.concatenate([x_out, x_in[::-1]]), np.concatenate([y_out, y_in[::-1]]), close=True)
        c.drawPath(p, paint(SEG_RGB[j], 0.32 * a))
        stroke_xy(c, x_out, y_out, SEG_RGB[j], a, 2.4)
        stroke_xy(c, px, py, SEG_RGB[j], 0.6 * a, 1.6)
    # 叠好以后的总轮廓
    if ks > 0.5:
        px, py, nx, ny = seg_geometry(1, kb, km)
        tot = hs[0] + hs[1] + hs[2]
        stroke_xy(c, px + nx * tot, py + ny * tot, WHITE, a * smooth((ks - 0.5) * 2), 2.2)
    fa = env(u, T_E + 6.0, T_E2, 0.6, 0.6)
    draw_math(c, r"\Theta\ =\ X\ \mathrm{mod}\ 2\pi", 1390, 300, 52, WHITE, fa * ramp(u, T_E + 6.0, T_E + 7.0),
              reveal=ramp(u, T_E + 6.0, T_E + 7.4), glow=0.2)
    draw_math(c, r"p_\Theta(\theta)=\sum_{n=-\infty}^{\infty} f(\theta+2\pi n)", 1390, 460, 46, WHITE,
              fa * ramp(u, T_E + 10.0, T_E + 11.0), reveal=ramp(u, T_E + 10.0, T_E + 11.6), glow=0.2)
    # E2：系数 = φ(k)
    ea = env(u, T_E2, DUR, 0.8, 0.8)
    if ea > 0.003:
        P = Plot(1080, 250, 1780, 560, -3.4, 3.4, 0, 1.08)
        P.axes(c, ea, GREY)
        ts = np.linspace(-3.4, 3.4, 400)
        P.fill(c, ts, np.abs(phiX(ts)), MAGENTA, ea * 0.6)
        P.curve(c, ts, np.abs(phiX(ts)), MAGENTA, ea, 2.6)
        draw_math(c, r"|\varphi_X(t)|", float(P.sx(0.9)), float(P.sy(0.85)), 30, MAGENTA, ea, align="l")
        draw_math(c, "t", P.R + 20, P.B + 8, 28, GREY, ea, align="l")
        kk = ramp(u, T_E2 + 1.5, T_E2 + 3.5)
        for k in range(-3, 4):
            x = float(P.sx(k))
            v = abs(complex(phiX(k)))
            on = clamp(kk * 7 - abs(k) * 2)
            c.drawLine(x, P.B, x, float(P.sy(v)), paint(GOLD, ea * on, stroke=3))
            glow_dot(c, x, float(P.sy(v)), 6, GOLD, ea * on, 5)
            draw_math(c, str(k) if k >= 0 else f"-{-k}", x, P.B + 32, 22, GREY, 0.7 * ea)
        draw_math(c, r"c_k\ =\ \mathbb{E}\,[e^{ik\Theta}]\ =\ \mathbb{E}\,[e^{ikX}]\ =\ \varphi_X(k)", 1390, 680, 42, GOLD,
                  ea * ramp(u, T_E2 + 1.0, T_E2 + 2.0), reveal=ramp(u, T_E2 + 1.0, T_E2 + 2.6), glow=0.2)
        fb = ea * ramp(u, T_E2 + 7.0, T_E2 + 8.0)
        draw_math(c, r"\sum_{n=-\infty}^{\infty} f(\theta+2\pi n)\ =\ \dfrac{1}{2\pi}\sum_{k=-\infty}^{\infty}\varphi_X(k)\,e^{-ik\theta}",
                  960, 860, 46, WHITE, fb, reveal=ramp(u, T_E2 + 7.0, T_E2 + 9.0), glow=0.3)
        text(c, "泊松求和公式", 1390, 200, 34, "bold", GOLD, fb)


def draw(c, u):
    main_circle(c, u)
    winding(c, u)
    coeffs(c, u)
    wrap_scene(c, u)


def _spin_ticks():
    """指针每转过 30° 响一下。"""
    out = []
    us = np.linspace(T_SPIN[0], T_SPIN[1], 4000)
    ang = np.array([spin_angle(x) for x in us])
    step = np.floor(ang / (math.pi / 6))
    for i in np.nonzero(np.diff(step))[0]:
        out.append((float(us[i]), "tick", {"f": 2200, "amp": 0.35}))
    return out


CAPS = [
    (4.4, 9.4, "现在随机变量本身就住在圆上：一个角度 $\\Theta$，转一圈回到原处。"),
    (9.6, 15.6, "像一个不均匀的转盘：有的方向更容易停下，密度画在圆周外面。"),
    (16.4, 23.0, "还能用任意频率 $t$ 去绕吗？$\\theta$ 和 $\\theta+2\\pi$ 是同一个点，绕完也必须是同一个点。"),
    (23.2, 28.6, "这要求 $e^{2\\pi it}=1$：只有整数 $t$ 才行。"),
    (28.8, 33.6, "于是频率不再连续，只剩下 $k=0,\\pm1,\\pm2,\\dots$"),
    (34.4, 41.0, "绕 $k$ 圈之后的重心，就是第 $k$ 个傅里叶系数 $c_k$。"),
    (41.2, 49.6, "$k$ 越大，点被绕得越乱，重心越靠近圆心：分布的细节藏在高频里。"),
    (50.4, 56.4, "把这些重心按频率一项一项叠回去，密度就一点点长出来——"),
    (56.6, 63.6, "这就是傅里叶级数。圆上的分布，由一列重心 $c_k$ 完全决定。"),
    (64.4, 70.4, "最后把两件事连起来：直线上的随机变量 $X$，缠到圆上。"),
    (70.6, 76.2, "每 $2\\pi$ 一段，一圈一圈叠起来，密度相加。"),
    (76.8, 83.2, "绕 $k$ 圈时，$x$ 和 $x+2\\pi n$ 落在同一处，所以圆上的系数就是 $\\varphi_X(k)$。"),
    (83.4, 92.0, "傅里叶级数的系数，就是傅里叶变换在整数点的取样——这就是泊松求和公式。"),
]

SFX = [
    (0.0, "whoosh", {"dur": 1.2}), (0.25, "impact", {}),
    (T_SPIN[1], "chime", {"f": 880}), (T_SPIN[1] + 0.2, "shimmer", {"dur": 2.0}),
    (T_B, "whoosh", {"dur": 1.4}), (T_B + 1.6, "alarm", {}), (T_B + 7.9, "chime", {"f": 1320}),
    (T_B + 8.6, "chime", {"f": 660}),
    (T_C, "whoosh", {"dur": 1.4}), (T_C + 0.4, "chime", {"f": 740}),
    (T_D, "whoosh", {"dur": 1.2}), (T_D + 0.3, "chime", {"f": 880}),
    (T_E, "glitch", {}), (T_E + 4.0, "whoosh", {"dur": 2.5}), (T_E + 7.0, "whoosh", {"dur": 2.5}),
    (T_E + 9.6, "boom", {}),
    (T_E2, "whoosh", {"dur": 1.2}), (T_E2 + 1.0, "chime", {"f": 990}), (T_E2 + 7.0, "riser", {"dur": 1.8}),
    (T_E2 + 8.8, "impact", {}),
]
SFX += _spin_ticks()
SFX += [(T_C + 0.6 + j * 0.9, "pitch", {"dur": 1.4, "up": True, "f0": 300 + 60 * j}) for j in range(6)]
SFX += [(T_D + 1.0 + k, "tick", {"f": 700 + 110 * k}) for k in range(1, 11)]
# t 扫过整数时：重合的那一下
SFX += [(T_B + 10.0 + (T_C - 1.0 - T_B - 10.0) * (3.0 - 2.0) / 1.5, "chime", {"f": 1320, "amp": 0.6})]

SCENES = [Scene("ch4", DUR, draw, CAPS, SFX, chapter=("04", "圆上的随机：傅里叶级数", "RANDOMNESS ON A CIRCLE"),
                theme=4, bed=4)]
