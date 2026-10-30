# -*- coding: utf-8 -*-
"""片头（S00）和第一章：分布函数（S01）。"""
import random

from common import *  # noqa: F401,F403


def cover_art(base_y=-2.8):
    """仿讲义封面：一排二项竖线 + 三条彩色密度曲线。"""
    ax = Axes(x_range=[-7.1, 7.1], y_range=[0, 1], x_length=14.2, y_length=2.05, tips=False,
              axis_config={"stroke_width": 0})
    ax.shift(UP * (base_y - ax.c2p(0, 0)[1]))
    base = Line(ax.c2p(-7.1, 0), ax.c2p(7.1, 0), stroke_width=2.5, color=INDIGO)
    ks = range(8)
    ps = [binom_pmf(7, 0.42, k) for k in ks]
    xs = [-6.75 + 0.66 * k for k in ks]
    st = VGroup()
    for x, p in zip(xs, ps):
        h = p / max(ps) * 0.82
        st.add(VGroup(Line(ax.c2p(x, 0), ax.c2p(x, h), stroke_width=3, color=INK),
                      Dot(ax.c2p(x, h), radius=0.05, color=INK)))
    gmax = max(gamma_pdf(x, 2.2, 0.42) for x in np.linspace(0.01, 15, 600))
    specs = [
        (lambda x: 0.30 * gamma_pdf(x + 7.4, 2.2, 0.42) / gmax, BRICK, 0.20),
        (lambda x: 0.87 * math.exp(-0.5 * ((x + 3.25) / 0.95) ** 2), TEAL, 0.22),
        (lambda x: 0.66 * math.exp(-0.5 * ((x - 1.9) / 1.55) ** 2), INDIGO, 0.22),
    ]
    curves, fills = VGroup(), VGroup()
    for f, c, op in specs:
        curves.add(curve(ax, f, -7.1, 7.1, c, width=3))
        fills.add(area(ax, f, -7.1, 7.1, c, opacity=op))
    return ax, base, st, curves, fills


class S00(VScene):
    SID = "S00"

    def construct(self):
        ax, base, st, curves, fills = cover_art()
        kicker = T("PROBABILITY DISTRIBUTIONS", 24, BRICK, bold=True)
        title = T("概率分布图鉴", 100, INK, bold=True)
        sub = T("常用分布 · 关键性质 · 相互关系", 32, MUTED)
        head = VGroup(kicker, title, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        head.to_corner(UL, buff=0.75)

        self.seg(0)
        self.play(FadeIn(kicker, shift=RIGHT * 0.3), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.25) for ch in title], lag_ratio=0.12), run_time=1.3)
        self.play(FadeIn(sub, shift=UP * 0.15), Create(base), run_time=0.9)
        self.play(LaggedStart(*[GrowFromEdge(s, DOWN) for s in st], lag_ratio=0.15), run_time=1.6)
        self.play(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.3), run_time=2.4)
        self.play(FadeIn(fills), run_time=1.0)
        self.add(fills, curves, st)

        tags = VGroup()
        for text, c in (("离散分布", TEAL), ("连续分布", BRICK), ("抽样分布与多元正态", INDIGO)):
            lab = T(text, 22, WHITE, bold=True)
            box = RoundedRectangle(corner_radius=0.07, width=lab.width + 0.36, height=lab.height + 0.24,
                                   fill_color=c, fill_opacity=1, stroke_width=0)
            lab.move_to(box)
            tags.add(VGroup(box, lab))
        tags.arrange(DOWN, aligned_edge=LEFT, buff=0.14).next_to(head, DOWN, buff=0.4, aligned_edge=LEFT)

        def pulse(fill, op):
            return UpdateFromAlphaFunc(fill, lambda m, a: m.set_fill(opacity=op + 0.35 * there_and_back(a)))

        self.seg(1)
        links = [(VGroup(st), fills[1], 0.22), (None, fills[0], 0.20), (None, fills[2], 0.22)]
        for tag, (extra, fill, op) in zip(tags, links):
            anims = [FadeIn(tag, shift=RIGHT * 0.3), pulse(fill, op)]
            if extra is not None:
                anims.append(Indicate(extra, color=TEAL, scale_factor=1.06))
            self.play(*anims, run_time=1.4)
            self.wait(0.6)

        self.seg(2)
        art = VGroup(base, st, curves, fills)
        small = VGroup(kicker, title, sub).copy().scale(0.5).to_corner(UL, buff=0.5)
        self.play(FadeOut(tags, shift=LEFT * 0.3), art.animate.set_opacity(0.0).shift(DOWN * 0.6),
                  Transform(VGroup(kicker, title, sub), small), run_time=1.2)
        self.remove(art)
        rows = VGroup()
        for num, (name, sub_t, c) in CHAPTERS.items():
            n = T(num, 34, c, bold=True)
            t = T(name, 30, INK, bold=True)
            s = T(sub_t, 20, MUTED)
            rows.add(VGroup(n, t, s).arrange(RIGHT, buff=0.35, aligned_edge=DOWN))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(DOWN * 0.15 + RIGHT * 0.4)
        rule = Line(rows.get_corner(UL) + UP * 0.3 + LEFT * 0.2, rows.get_corner(UR) + UP * 0.3 + RIGHT * 0.4,
                    stroke_width=1.5, color=FAINT)
        self.play(Create(rule), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.4) for r in rows], lag_ratio=0.25),
                  run_time=min(4.0, self.left() * 0.6))
        self.catch_up()
        self.play(FadeOut(VGroup(rows, rule, kicker, title, sub)), run_time=0.8)


class S01(VScene):
    SID = "S01"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "01")

        # --- 定义与三种描述 ---
        self.seg(1)
        cap = T("累积分布函数  CDF", 26, MUTED)
        defn = M(r"F(x)=P(X\le x),\qquad x\in\mathbb{R}", 60)
        top = VGroup(cap, defn).arrange(DOWN, buff=0.3).move_to(UP * 1.75)
        self.play(FadeIn(cap), Write(defn), run_time=1.6)
        left = VGroup(T("离散变量：概率质量函数", 26, TEAL, bold=True), M(r"p(k)=P(X=k)", 42))
        right = VGroup(T("连续变量：概率密度", 26, BRICK, bold=True), M(r"F(x)=\int_{-\infty}^{x} f(t)\,dt", 42))
        for g in (left, right):
            g.arrange(DOWN, buff=0.3)
        boxes = VGroup(*[VGroup(soft_box(g, CARD, pad=0.35), g) for g in (left, right)])
        for b in boxes:
            b[0].stretch_to_fit_width(5.4).move_to(b[1])
        boxes.arrange(RIGHT, buff=0.6).move_to(DOWN * 0.55)
        self.wait(max(0.3, self.durs[1] * 0.18 - 1.6))
        self.play(LaggedStart(FadeIn(boxes[0], shift=UP * 0.3), FadeIn(boxes[1], shift=UP * 0.3), lag_ratio=0.4),
                  run_time=1.6)
        self.wait(max(0.3, self.durs[1] * 0.55 - 3.5))
        concl = mixed("三者描述同一个对象；", "CDF 最普遍：任何随机变量都有", size=26).move_to(DOWN * 2.45)
        hl = SurroundingRectangle(defn, color=GOLD, buff=0.18, corner_radius=0.08, stroke_width=3)
        self.play(FadeIn(concl, shift=UP * 0.2), Create(hl), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(top, boxes, concl, hl)), run_time=0.7)

        # --- 混合型分布函数 ---
        self.seg(2)
        ax = axes([-1, 3.2, 1], [0, 1.15, 0.5], 6.6, 4.3, xnums=[0, 1, 2], ynums=[0.4, 0.7, 0.85, 1],
                  xlabel="x", ylabel="F(x)", ydec=None)
        ax.move_to(LEFT * 3.0 + DOWN * 0.45)
        F = BRICK
        p1 = Line(ax.c2p(-1, 0), ax.c2p(0, 0), color=INK, stroke_width=4)
        p2 = Line(ax.c2p(0, 0), ax.c2p(1, 0.4), color=F, stroke_width=4)
        h1 = Circle(radius=0.07, color=F, stroke_width=3, fill_color=BG, fill_opacity=1).move_to(ax.c2p(1, 0.4))
        j1 = DashedLine(ax.c2p(1, 0.4), ax.c2p(1, 0.7), color=GREY, stroke_width=2, dash_length=0.05)
        d1 = Dot(ax.c2p(1, 0.7), radius=0.08, color=F)
        p3 = Line(ax.c2p(1, 0.7), ax.c2p(2, 0.85), color=F, stroke_width=4)
        h2 = Circle(radius=0.07, color=F, stroke_width=3, fill_color=BG, fill_opacity=1).move_to(ax.c2p(2, 0.85))
        j2 = DashedLine(ax.c2p(2, 0.85), ax.c2p(2, 1), color=GREY, stroke_width=2, dash_length=0.05)
        d2 = Dot(ax.c2p(2, 1), radius=0.08, color=INK)
        p4 = Line(ax.c2p(2, 1), ax.c2p(3.1, 1), color=INK, stroke_width=4)
        note = VGroup(T("实心点 = 函数值", 18, MUTED), T("空心点 = 左极限", 18, MUTED)).arrange(DOWN, aligned_edge=LEFT,
                                                                                         buff=0.08)
        note.move_to(ax.c2p(0.35, 0.95))
        self.play(Create(ax), run_time=1.0)
        self.play(Create(p1), run_time=0.4)
        self.play(Create(p2), run_time=0.7)
        self.play(FadeIn(h1), Create(j1), FadeIn(d1, scale=1.6), run_time=0.6)
        self.play(Create(p3), run_time=0.6)
        self.play(FadeIn(h2), Create(j2), FadeIn(d2, scale=1.6), run_time=0.6)
        self.play(Create(p4), FadeIn(note), run_time=0.6)
        props_t = T("刻画定理", 28, INK, bold=True)
        props = VGroup(
            bullet("单调不减"),
            bullet("右连续"),
            bullet("$\\lim_{x\\to-\\infty}F(x)=0$"),
            bullet("$\\lim_{x\\to+\\infty}F(x)=1$"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        props_g = VGroup(props_t, props).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        props_g.move_to(RIGHT * 2.9 + UP * 1.0).align_to(RIGHT * 1.6, LEFT)
        self.play(FadeIn(props_t), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.3) for b in props], lag_ratio=0.5),
                  run_time=min(3.0, self.left()))
        self.catch_up()

        # --- 跳跃高度 = 点概率 ---
        self.seg(3)
        br = BraceBetweenPoints(ax.c2p(1, 0.4), ax.c2p(1, 0.7), direction=RIGHT, color=GOLD)
        br_t = M(r"P(X=1)=0.3", 30, GOLD).next_to(br, RIGHT, buff=0.1)
        self.play(GrowFromCenter(br), Flash(d1, color=GOLD, line_length=0.15), run_time=0.9)
        self.play(Write(br_t), run_time=0.8)
        extra = VGroup(
            mixed("$P(a<X\\le b)=F(b)-F(a)$", size=24),
            mixed("$P(X=a)=F(a)-F(a^-)$", size=24),
            T("跳点至多可数个", 22),
            mixed("连续型变量 ", "$P(X=a)=0$", size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        box = note_box(extra, GOLD)
        box.next_to(props_g, DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(box, shift=UP * 0.2), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, p1, p2, p3, p4, h1, h2, j1, j2, d1, d2, note, props_g, box, br, br_t)),
                  run_time=0.7)

        # --- 逆变换抽样 ---
        self.seg(4)
        sd = 1.1
        Phi = lambda x: 0.5 * (1 + math.erf(x / (sd * math.sqrt(2))))  # noqa: E731
        top_ax = axes([-4, 4.3, 1], [0, 1.12, 0.5], 10.0, 2.55, xnums=[-4, -2, 0, 2, 4], ynums=[0.5, 1],
                      xlabel="x", ylabel="F(x)")
        top_ax.move_to(UP * 1.15 + LEFT * 0.2)
        cdf = curve(top_ax, Phi, -4, 4.2, INDIGO, width=4.5)
        self.play(Create(top_ax), run_time=0.8)
        self.play(Create(cdf), run_time=1.2)
        u = 0.8
        x_u = sd * math.sqrt(2) * _erfinv(2 * u - 1)
        ud = Dot(top_ax.c2p(-4, u), color=GOLD, radius=0.08)
        ul = M(r"u\sim U(0,1)", 28, GOLD).next_to(ud, LEFT, buff=0.15)
        h_ar = Arrow(top_ax.c2p(-4, u), top_ax.c2p(x_u, u), buff=0, color=GOLD, stroke_width=4,
                     max_tip_length_to_length_ratio=0.03)
        v_ar = Arrow(top_ax.c2p(x_u, u), top_ax.c2p(x_u, 0), buff=0, color=GOLD, stroke_width=4,
                     max_tip_length_to_length_ratio=0.12)
        xl = M(r"x=F^{-1}(u)", 28, GOLD).next_to(top_ax.c2p(x_u, 0), DOWN + RIGHT, buff=0.12)
        self.play(FadeIn(ud, scale=1.5), FadeIn(ul), run_time=0.7)
        self.play(GrowArrow(h_ar), run_time=1.0)
        self.play(GrowArrow(v_ar), run_time=0.8)
        self.play(FadeIn(xl), run_time=0.5)
        rule = M(r"F^{-1}(u)=\inf\{x:F(x)\ge u\}", 28, MUTED).move_to(top_ax.c2p(2.6, 0.38))
        self.play(FadeIn(rule), run_time=0.8)
        self.catch_up()

        # --- 很多个 u 落成直方图 ---
        self.seg(5)
        self.play(FadeOut(VGroup(ud, ul, h_ar, v_ar, xl, rule)), run_time=0.5)
        bw = 0.4
        hist_ax = axes([-4, 4.3, 1], [0, 13, 5], 10.0, 2.5, tips=False)
        hist_ax.align_to(top_ax, LEFT).move_to([top_ax.get_center()[0], -1.75, 0])
        base = Line(hist_ax.c2p(-4, 0), hist_ax.c2p(4.2, 0), color=AXIS, stroke_width=2)
        self.play(Create(base), run_time=0.4)
        N = 80
        us = [(i + 0.5) / N for i in range(N)]
        random.Random(7).shuffle(us)
        counts = {}
        movers, blocks = [], []
        unit_h = hist_ax.c2p(0, 1)[1] - hist_ax.c2p(0, 0)[1]
        for uu in us:
            xv = sd * math.sqrt(2) * _erfinv(2 * uu - 1)
            b = math.floor(xv / bw)
            c = counts.get(b, 0)
            counts[b] = c + 1
            cx = (b + 0.5) * bw
            start = top_ax.c2p(-4, uu)
            corner = top_ax.c2p(xv, uu)
            land = hist_ax.c2p(cx, c + 0.5)
            path = VMobject().set_points_as_corners([start, corner, [corner[0], land[1], 0], land])
            dot = Dot(start, radius=0.05, color=GOLD).set_opacity(0)
            blk = Rectangle(width=(hist_ax.c2p(bw, 0) - hist_ax.c2p(0, 0))[0] * 0.86, height=unit_h * 0.86,
                            fill_color=tint(INDIGO, 0.55), fill_opacity=1, stroke_color=INDIGO, stroke_width=1)
            blk.move_to(land)
            trail = path.copy().set_stroke(GOLD, width=1.2, opacity=0.35)
            movers.append((dot, path, blk, trail))

        def travel(dot, path):
            def upd(m, a):
                m.move_to(path.point_from_proportion(rate_functions.ease_in_quad(a)))
                m.set_opacity(1 if a > 0 else 0)
            return UpdateFromAlphaFunc(dot, upd)

        anims = []
        for dot, path, blk, trail in movers:
            anims.append(Succession(
                AnimationGroup(travel(dot, path), ShowPassingFlash(trail, time_width=0.6), run_time=0.9),
                Transform(dot, blk, run_time=0.15)))
        self.play(LaggedStart(*anims, lag_ratio=0.09), run_time=8.0)
        dens = curve(hist_ax, lambda x: N * bw * norm_pdf(x, 0, sd), -4, 4.2, INDIGO, width=4)
        self.play(Create(dens), run_time=1.2)
        pit = VGroup(T("概率积分变换", 24, INK, bold=True),
                     mixed("$F$", " 连续时 ", "$F(X)\\sim U(0,1)$", size=22)).arrange(DOWN, aligned_edge=LEFT,
                                                                                   buff=0.15)
        pit_b = note_box(pit, INDIGO, pad=0.22)
        pit_b.move_to(hist_ax.c2p(-2.7, 8.5))
        self.play(FadeIn(pit_b, shift=UP * 0.2), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(top_ax, cdf, hist_ax, base, dens, pit_b, *[m[0] for m in movers])), run_time=0.8)

        # --- 矩母函数与特征函数 ---
        self.seg(6)
        eh = entry_header("矩母函数与特征函数", "MGF & c.f.", r"M(t)=\mathbb{E}e^{tX},\ \ \varphi(t)=\mathbb{E}e^{itX}",
                          INK, y=2.2)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.9)
        l1 = bullet("唯一性：特征函数总存在，且唯一确定分布")
        l2 = bullet("矩母函数在 0 附近有限时也唯一确定分布，", "$\\mathbb{E}X^n=M^{(n)}(0)$")
        key = mixed("$X,Y$", " 独立 ", "$\\Rightarrow\\ M_{X+Y}=M_X M_Y,\\quad \\varphi_{X+Y}=\\varphi_X\\varphi_Y$",
                    size=32)
        keyb = VGroup(soft_box(key, tint(GOLD, 0.18), pad=0.3), key)
        l3 = bullet("下文各种“可加性”都是由这一行算出来的", mark=GOLD)
        body = VGroup(l1, l2, keyb, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.38).next_to(eh, DOWN, buff=0.55)
        body.align_to(eh, LEFT).shift(RIGHT * 0.4)
        keyb.set_x(0)
        self.play(FadeIn(l1, shift=RIGHT * 0.3), run_time=0.8)
        self.play(FadeIn(l2, shift=RIGHT * 0.3), run_time=0.8)
        self.wait(max(0.2, self.durs[6] * 0.35 - 2.5))
        self.play(FadeIn(keyb[0]), Write(key), run_time=1.8)
        self.wait(max(0.2, self.durs[6] * 0.7 - self.durs[6] * 0.35 - 1.8))
        self.play(FadeIn(l3, shift=RIGHT * 0.3), Indicate(key, color=GOLD, scale_factor=1.04), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(eh, body, hdr)), run_time=0.8)


def _erfinv(y):
    """erf 的反函数（牛顿迭代，够画图用）。"""
    y = max(min(y, 0.999999), -0.999999)
    a = 0.147
    ln = math.log(1 - y * y)
    t = 2 / (math.pi * a) + ln / 2
    x = math.copysign(math.sqrt(math.sqrt(t * t - ln / a) - t), y)
    for _ in range(3):
        err = math.erf(x) - y
        x -= err / (2 / math.sqrt(math.pi) * math.exp(-x * x))
    return x
