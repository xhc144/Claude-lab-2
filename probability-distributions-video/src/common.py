# -*- coding: utf-8 -*-
"""公共部分：配色（沿用讲义）、字体、版式组件、坐标轴、按配音对齐的 VScene。"""
import json
import math
import os

import numpy as np
from manim import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- 配色：和讲义一致 ----------
BG = "#F4F0E6"       # 米色纸面
INK = "#1E2A44"      # 深藏青正文
MUTED = "#7D8496"    # 灰色辅助文字
AXIS = "#5E6577"     # 坐标轴
FAINT = "#D8D1C1"    # 浅分隔线
CARD = "#EAE4D6"     # 数字卡底色
TEAL = "#2A9D8F"     # 离散分布
BRICK = "#C8553D"    # 连续分布
INDIGO = "#5B5EA6"   # 抽样分布与多元正态
GOLD = "#D99A2B"     # 极限定理 / 强调
PLUM = "#9B59A6"     # 第四种曲线色
GREY = "#A5A9B4"

FONT = "Noto Sans CJK SC"

config.background_color = BG

TEX = TexTemplate()
TEX.add_to_preamble(r"\usepackage{mathpazo}\usepackage{amsmath,amssymb,bm}")
config.tex_template = TEX
MathTex.set_default(color=INK)
Tex.set_default(color=INK)
Text.set_default(font=FONT, color=INK)


def tint(c, a):
    """颜色 c 以不透明度 a 叠在纸面上的结果（用来画浅色底）。"""
    return interpolate_color(ManimColor(BG), ManimColor(c), a)


def T(s, size=30, color=INK, bold=False, **kw):
    return Text(s, font_size=size, color=color, weight=BOLD if bold else NORMAL, **kw)


def M(s, size=36, color=INK, **kw):
    return MathTex(s, font_size=size, color=color, **kw)


def mixed(*parts, size=30, color=INK, buff=0.1):
    """中文和公式混排的一行：以 $ 开头的片段当公式，其余当文字。"""
    mobs = []
    for p in parts:
        if isinstance(p, Mobject):
            mobs.append(p)
        elif p.startswith("$"):
            mobs.append(M(p.strip("$"), size=size * 1.18, color=color))
        else:
            mobs.append(T(p, size=size, color=color))
    return VGroup(*mobs).arrange(RIGHT, buff=buff)


def bullet(*parts, size=26, color=INK, mark=GOLD):
    tri = Triangle(color=mark, fill_color=mark, fill_opacity=1, stroke_width=0).rotate(-PI / 2).scale(0.07)
    row = mixed(*parts, size=size, color=color)
    return VGroup(tri, row).arrange(RIGHT, buff=0.18)


# ---------- 版式组件 ----------
EPISODE_COLORS = {1: INK, 2: TEAL, 3: TEAL, 4: TEAL, 5: BRICK, 6: BRICK, 7: INDIGO, 8: INDIGO}


def _ep(ep):
    from outline import EPISODES
    e = EPISODES[ep - 1]
    return e["title"], e["sub"], EPISODE_COLORS[ep]


def running_header(ep):
    """页眉：左边系列名，右边“第 N 集 · 集名”。"""
    title, _, color = _ep(ep)
    left = T("概率分布图鉴", 18, MUTED)
    right = VGroup(T(f"第 {ep} 集", 18, color, bold=True), T(title, 18, MUTED)).arrange(RIGHT, buff=0.14)
    left.to_corner(UL, buff=0.32)
    right.to_corner(UR, buff=0.32)
    return VGroup(left, right)


def episode_card(ep):
    title, sub, color = _ep(ep)
    num = Text(f"{ep:02d}", font=FONT, weight=BOLD, font_size=150, color=color)
    kicker = T(f"第 {ep} 集", 26, color, bold=True)
    t = T(title, 60, INK, bold=True)
    s_ = T(sub, 30, MUTED)
    words = VGroup(kicker, t, s_).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    card = VGroup(num, words).arrange(RIGHT, buff=0.5, aligned_edge=DOWN)
    bar = Line(ORIGIN, RIGHT * num.width, stroke_width=7, color=color).next_to(num, DOWN, buff=0.18, aligned_edge=LEFT)
    rule = Line(bar.get_right(), bar.get_right() + RIGHT * (card.width - num.width + 0.6), stroke_width=1.5,
                color=FAINT)
    return VGroup(num, words, bar, rule).move_to(UP * 0.3)


def play_episode_card(scene, ep, hold=None):
    """集标题卡：数字上浮、标题依次滑入、下划线生长；停到这段配音快念完，再收成页眉。"""
    card = episode_card(ep)
    num, words, bar, rule = card
    scene.play(FadeIn(num, shift=UP * 0.5, scale=0.9), run_time=0.8)
    scene.play(LaggedStart(*[FadeIn(w, shift=RIGHT * 0.4) for w in words], lag_ratio=0.3),
               GrowFromEdge(bar, LEFT), Create(rule), run_time=1.3)
    if hold is None:
        hold = max(0.5, scene._end - scene.now - 0.8)
    scene.wait(hold)
    hdr = running_header(ep)
    scene.play(FadeOut(card, shift=UP * 0.3), FadeIn(hdr), run_time=0.8)
    return hdr


def scene_title(text, color=INK):
    """场景小标题：左上角页眉下方一行加粗字 + 短色条。"""
    t = T(text, 30, INK, bold=True)
    bar = Rectangle(width=0.09, height=t.height + 0.1, fill_color=color, fill_opacity=1, stroke_width=0)
    g = VGroup(bar, t).arrange(RIGHT, buff=0.2)
    return g.to_corner(UL, buff=0.32).shift(DOWN * 0.55)


def entry_header(cn, en, notation, color, y=2.95, width=12.8):
    """条目抬头：浅色底条 + 左侧色条 + 中文名、英文名 + 右侧记号。"""
    bg = Rectangle(width=width, height=0.66, fill_color=tint(color, 0.13), fill_opacity=1, stroke_width=0)
    stripe = Rectangle(width=0.09, height=0.66, fill_color=color, fill_opacity=1, stroke_width=0)
    stripe.align_to(bg, LEFT)
    name = VGroup(T(cn, 30, INK, bold=True), T(en, 22, MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
    name.next_to(stripe, RIGHT, buff=0.3)
    note = M(notation, 36, color)
    note.align_to(bg, RIGHT).shift(LEFT * 0.3)
    g = VGroup(bg, stripe, name, note).move_to(UP * y)
    return g


def stat_cards(items, color, width=12.4, y=None, value_size=36):
    """三格“数字卡”：标签用分类色、字距拉开，数值用公式。"""
    n = len(items)
    gap = 0.22
    w = (width - gap * (n - 1)) / n
    cards = VGroup()
    for label, val in items:
        box = RoundedRectangle(corner_radius=0.08, width=w, height=1.15, fill_color=CARD, fill_opacity=1,
                               stroke_width=0)
        lab = T("  ".join(label), 19, color, bold=True)
        v = M(val, value_size) if isinstance(val, str) else val
        if v.width > w - 0.3:
            v.scale_to_fit_width(w - 0.3)
        inner = VGroup(lab, v).arrange(DOWN, buff=0.14)
        inner.move_to(box)
        cards.add(VGroup(box, inner))
    cards.arrange(RIGHT, buff=gap)
    if y is not None:
        cards.move_to(UP * y)
    return cards


def tag(s, size=18):
    """讲义里“参数”“支撑”那种灰底小标签。"""
    lab = T(s, size, INK, bold=True)
    box = RoundedRectangle(corner_radius=0.05, width=lab.width + 0.2, height=lab.height + 0.14,
                           fill_color="#DDD8CC", fill_opacity=1, stroke_width=0)
    return VGroup(box, lab.move_to(box))


def param_line(params, support, size=26):
    gap = Rectangle(width=0.35, height=0.01, stroke_width=0, fill_opacity=0)
    return mixed(tag("参数"), params, gap, tag("支撑"), support, size=size, buff=0.2)


def soft_box(mob, color=CARD, pad=0.3, radius=0.1, opacity=1.0):
    box = RoundedRectangle(corner_radius=radius, width=mob.width + 2 * pad, height=mob.height + 2 * pad,
                           fill_color=color, fill_opacity=opacity, stroke_width=0)
    box.move_to(mob)
    return box


def note_box(mob, color, pad=0.28):
    """讲义里“阅读说明”那种带左侧色条的浅底框。"""
    box = soft_box(mob, tint(color, 0.10), pad=pad, radius=0.06)
    stripe = Rectangle(width=0.07, height=box.height, fill_color=color, fill_opacity=1, stroke_width=0)
    stripe.align_to(box, LEFT)
    return VGroup(box, stripe, mob)


def legend(items, size=20, line_len=0.45):
    rows = VGroup()
    for color, label, *rest in items:
        style = rest[0] if rest else "line"
        if style == "dash":
            mark = DashedLine(ORIGIN, RIGHT * line_len, color=color, stroke_width=3, dash_length=0.06)
        elif style == "dot":
            mark = Dot(radius=0.07, color=color)
        elif style == "bar":
            mark = Rectangle(width=0.18, height=0.26, fill_color=tint(color, 0.45), fill_opacity=1,
                             stroke_color=color, stroke_width=1.5)
        else:
            mark = Line(ORIGIN, RIGHT * line_len, color=color, stroke_width=3.5)
        lab = M(label.strip("$"), size * 1.2) if label.startswith("$") else T(label, size, INK)
        rows.add(VGroup(mark, lab).arrange(RIGHT, buff=0.15))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    return rows


# ---------- 坐标轴 ----------
def axes(xr, yr, w, h, xnums=(), ynums=(), xlabel=None, ylabel=None, num_size=22, tips=True, ydec=None,
         xdec=None, xnums_at=None):
    ax = Axes(x_range=xr, y_range=yr, x_length=w, y_length=h, tips=tips,
              axis_config={"color": AXIS, "stroke_width": 2, "include_ticks": False,
                           "tip_width": 0.13, "tip_height": 0.13})
    labels = VGroup()
    y_at = xnums_at if xnums_at is not None else (0 if yr[0] <= 0 <= yr[1] else yr[0])
    x_at = 0 if xr[0] <= 0 <= xr[1] else xr[0]
    for x in xnums:
        s = (f"{x:.{xdec}f}" if xdec is not None else _fmt(x)) if not isinstance(x, tuple) else x[1]
        xv = x if not isinstance(x, tuple) else x[0]
        tick = Line(UP * 0.05, DOWN * 0.05, stroke_width=1.5, color=AXIS).move_to(ax.c2p(xv, y_at))
        lab = M(s, num_size, MUTED).next_to(tick, DOWN, buff=0.1)
        labels.add(tick, lab)
    for y in ynums:
        s = (f"{y:.{ydec}f}" if ydec is not None else _fmt(y)) if not isinstance(y, tuple) else y[1]
        yv = y if not isinstance(y, tuple) else y[0]
        tick = Line(LEFT * 0.05, RIGHT * 0.05, stroke_width=1.5, color=AXIS).move_to(ax.c2p(x_at, yv))
        lab = M(s, num_size, MUTED).next_to(tick, LEFT, buff=0.1)
        labels.add(tick, lab)
    ax.num_labels = labels
    ax.add(labels)
    if xlabel:
        xl = M(xlabel, 28, INK) if not isinstance(xlabel, Mobject) else xlabel
        xl.next_to(ax.x_axis.get_end(), DOWN + LEFT * 0.2, buff=0.18)
        ax.add(xl)
    if ylabel:
        yl = M(ylabel, 28, INK) if not isinstance(ylabel, Mobject) else ylabel
        yl.next_to(ax.y_axis.get_end(), RIGHT, buff=0.15)
        ax.add(yl)
    return ax


def _fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:g}"


def stems(ax, ks, ps, color, dot_r=0.055, width=3.0, opacity=1.0):
    g = VGroup()
    for k, p in zip(ks, ps):
        a, b = ax.c2p(k, 0), ax.c2p(k, p)
        ln = Line(a, b, color=color, stroke_width=width, stroke_opacity=opacity)
        d = Dot(b, radius=dot_r, color=color, fill_opacity=opacity)
        g.add(VGroup(ln, d))
    return g


def bars(ax, ks, ps, color, w=0.7, opacity=0.35, stroke=1.6, offset=0.0):
    g = VGroup()
    for k, p in zip(ks, ps):
        x0, x1 = k + offset - w / 2, k + offset + w / 2
        lo, hi = ax.c2p(x0, 0), ax.c2p(x1, p)
        r = Rectangle(width=max(hi[0] - lo[0], 1e-3), height=max(hi[1] - lo[1], 1e-3),
                      fill_color=tint(color, opacity), fill_opacity=1, stroke_color=color, stroke_width=stroke)
        r.move_to((lo + hi) / 2)
        g.add(r)
    return g


def _run(ax, f, a, b, n, ymax):
    """取样 (x, f(x))；有 ymax 时只保留不超过 ymax 的那一段（发散处截断，不压平）。"""
    xs = np.linspace(a, b, n)
    ys = [f(x) for x in xs]
    if ymax is None:
        return list(zip(xs, ys))
    runs, cur = [], []
    for x, y in zip(xs, ys):
        if y <= ymax:
            cur.append((x, y))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return max(runs, key=len) if runs else [(a, 0.0), (b, 0.0)]


def curve(ax, f, a, b, color, width=4, n=400, ymax=None):
    pts = [ax.c2p(x, y) for x, y in _run(ax, f, a, b, n, ymax)]
    m = VMobject(stroke_color=color, stroke_width=width)
    m.set_points_as_corners(pts)
    return m


def area(ax, f, a, b, color, opacity=0.3, n=300, ymax=None):
    run = _run(ax, f, a, b, n, ymax)
    poly = [ax.c2p(run[0][0], 0)] + [ax.c2p(x, y) for x, y in run] + [ax.c2p(run[-1][0], 0)]
    return Polygon(*poly, fill_color=color, fill_opacity=opacity, stroke_width=0)


def glow(mob, color, layers=4, width=10, opacity=0.08):
    """在曲线下面垫几层半透明的粗线，做出柔和的光晕。"""
    g = VGroup()
    for i in range(layers):
        c = mob.copy().set_stroke(color, width=width * (i + 1) / layers + mob.get_stroke_width(),
                                  opacity=opacity)
        g.add(c)
    return g


# ---------- 概率函数 ----------
def binom_pmf(n, p, k):
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def poisson_pmf(lam, k):
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1)) if lam > 0 else float(k == 0)


def norm_pdf(x, mu=0.0, s=1.0):
    return math.exp(-0.5 * ((x - mu) / s) ** 2) / (s * math.sqrt(2 * math.pi))


def gamma_pdf(x, a, lam=1.0):
    if x <= 0:
        return 0.0
    return math.exp(a * math.log(lam) + (a - 1) * math.log(x) - lam * x - math.lgamma(a))


def beta_pdf(x, a, b):
    if x <= 0 or x >= 1:
        return 0.0
    return math.exp((a - 1) * math.log(x) + (b - 1) * math.log(1 - x)
                    + math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b))


def chi2_pdf(x, k):
    return gamma_pdf(x, k / 2, 0.5)


def t_pdf(t, v):
    return math.exp(math.lgamma((v + 1) / 2) - math.lgamma(v / 2)) / math.sqrt(v * math.pi) * \
        (1 + t * t / v) ** (-(v + 1) / 2)


def f_pdf(x, d1, d2):
    if x <= 0:
        return 0.0
    lg = (math.lgamma((d1 + d2) / 2) - math.lgamma(d1 / 2) - math.lgamma(d2 / 2)
          + (d1 / 2) * math.log(d1 / d2) + (d1 / 2 - 1) * math.log(x)
          - ((d1 + d2) / 2) * math.log(1 + d1 * x / d2))
    return math.exp(lg)


# ---------- 配音对齐 ----------
TIMING_PATH = os.path.join(HERE, "timing.json")
MARKS_DIR = os.path.join(HERE, "marks")
LEAD, GAP, TAIL = 0.6, 0.7, 1.0


def _load_timing():
    if os.path.exists(TIMING_PATH):
        with open(TIMING_PATH, encoding="utf-8") as f:
            return json.load(f)["durations"]
    # 还没合成配音时按字数估计（每秒 4.9 个字），方便先调画面
    from outline import SCENES
    return {sc["id"]: [n / 4.9 for _, _, n in sc["segs"]] for sc in SCENES}


class VMixin:
    """每段配音调用一次 seg(i)：等上一段念完（加段间停顿）再开始，记下这一段的起点。

    画面比配音长也没关系：build.py 按这里记下的实际起点放配音，所以不会错位。
    """
    SID = ""

    def setup(self):
        self.durs = _load_timing()[self.SID]
        self.marks = []
        self._end = None

    @property
    def now(self):
        return self.renderer.time

    def seg(self, i):
        assert i == len(self.marks), (self.SID, i, len(self.marks))
        if self._end is None:
            if self.now < LEAD:
                self.wait(LEAD - self.now)
        else:
            self.catch_up(GAP)
        self.marks.append(self.now)
        self._end = self.now + self.durs[i]
        return self.durs[i]

    def catch_up(self, extra=0.0):
        rem = self._end + extra - self.now
        if rem > 1 / 120:
            self.wait(rem)

    def left(self, minimum=0.5):
        return max(minimum, self._end - self.now)

    def tear_down(self):
        assert len(self.marks) == len(self.durs), (self.SID, len(self.marks), len(self.durs))
        self.catch_up(TAIL)
        os.makedirs(MARKS_DIR, exist_ok=True)
        with open(os.path.join(MARKS_DIR, self.SID + ".json"), "w") as f:
            json.dump({"marks": self.marks, "durations": self.durs, "end": self.now}, f, indent=1)


class VScene(VMixin, Scene):
    pass


class VMovingScene(VMixin, MovingCameraScene):
    pass


class V3Scene(VMixin, ThreeDScene):
    pass
