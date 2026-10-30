# -*- coding: utf-8 -*-
"""第 1 集：从一枚硬币开始——随机变量与分布函数。"""
import random

from common import *  # noqa: F401,F403
from props import coin, die, flip, route_map, spin_to, spinner

EP = 1


def erfinv(y):
    """erf 的反函数（牛顿迭代，够画图用）。"""
    y = max(min(y, 0.999999), -0.999999)
    a = 0.147
    ln = math.log(1 - y * y)
    t = 2 / (math.pi * a) + ln / 2
    x = math.copysign(math.sqrt(math.sqrt(t * t - ln / a) - t), y)
    for _ in range(3):
        x -= (math.erf(x) - y) / (2 / math.sqrt(math.pi) * math.exp(-x * x))
    return x


DICE = {s: sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s) / 36 for s in range(2, 13)}


class E1A(VScene):
    SID = "E1A"

    def construct(self):
        kicker = T("PROBABILITY DISTRIBUTIONS", 24, BRICK, bold=True)
        title = T("概率分布图鉴", 96, INK, bold=True)
        sub = T("从一枚硬币出发，把常用分布串成一条线", 30, MUTED)
        head = VGroup(kicker, title, sub).arrange(DOWN, buff=0.25).move_to(UP * 2.55)
        path, stations = route_map()
        path.shift(DOWN * 0.45)
        for s in stations:
            s.shift(DOWN * 0.45)
        c = coin("正", r=0.38).move_to(stations[0][0])

        self.seg(0)
        self.play(FadeIn(kicker, shift=DOWN * 0.2), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.3, scale=0.8) for ch in title], lag_ratio=0.1), run_time=1.3)
        self.play(FadeIn(sub), run_time=0.6)
        self.play(FadeIn(c, scale=0.5), run_time=0.5)
        self.play(flip(c, "正", times=4, run_time=1.2, height=0.9))
        each = max(0.7, (self.durs[0] - 4.8) / len(stations) - 0.05)
        self.play(FadeOut(c, scale=0.5), GrowFromCenter(stations[0]), run_time=0.5)
        for i in range(1, len(stations)):
            seg = Line(stations[i - 1][0].get_center(), stations[i][0].get_center(), stroke_color=GREY, stroke_width=7)
            if i == 6:  # 折到下一行
                mid = np.array([5.6, stations[i][0].get_center()[1], 0])
                seg = VMobject(stroke_color=GREY, stroke_width=7).set_points_as_corners(
                    [stations[i - 1][0].get_center(), np.array([5.6, stations[i - 1][0].get_center()[1], 0]), mid,
                     stations[i][0].get_center()])
            seg.set_z_index(-1)
            color = stations[i][0].get_stroke_color()
            self.play(Create(seg), run_time=each * 0.5)
            self.play(GrowFromCenter(stations[i]), stations[i][0].animate.set_fill(tint(color, 0.6)),
                      run_time=each * 0.5)
            self.add(seg)
        self.catch_up()

        self.seg(1)
        self.play(*[FadeOut(m, shift=DOWN * 0.3) for m in self.mobjects], run_time=0.9)
        play_episode_card(self, EP)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)


class E1B(VScene):
    SID = "E1B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("随机变量")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.5)

        # --- 样本空间 ---
        self.seg(0)
        c = coin("反", r=0.6).move_to(LEFT * 3 + UP * 0.3)
        self.play(FadeIn(c), run_time=0.4)
        self.play(flip(c, "正", times=5, run_time=1.6, height=1.6))
        omega = mixed("样本空间 ", "$\\Omega=\\{$", "正面", "$,$", "反面", "$\\}$", size=34).move_to(RIGHT * 2.6 + UP * 0.3)
        self.play(Write(omega), run_time=1.4)
        q = T("“正面”不是数：没法求平均，也没法画在数轴上", 26, MUTED).move_to(DOWN * 1.6)
        self.wait(max(0.2, self.durs[0] * 0.5 - 3.4))
        self.play(FadeIn(q, shift=UP * 0.2), run_time=0.8)
        self.catch_up()

        # --- 映射到数轴 ---
        self.seg(1)
        self.play(FadeOut(q), FadeOut(omega), c.animate.scale(0.7).move_to(LEFT * 4.5 + UP * 1.3), run_time=0.8)
        c2 = coin("反", r=0.42).move_to(LEFT * 4.5 + DOWN * 0.3)
        self.play(FadeIn(c2, shift=UP * 0.2), run_time=0.5)
        nl = NumberLine(x_range=[-0.5, 1.6, 0.5], length=6, color=AXIS, include_numbers=False).move_to(RIGHT * 1.8 +
                                                                                                    DOWN * 0.6)
        n0 = M("0", 34).next_to(nl.n2p(0), DOWN, buff=0.2)
        n1 = M("1", 34).next_to(nl.n2p(1), DOWN, buff=0.2)
        d0, d1 = Dot(nl.n2p(0), radius=0.1, color=INDIGO), Dot(nl.n2p(1), radius=0.1, color=BRICK)
        self.play(Create(nl), FadeIn(n0), FadeIn(n1), run_time=0.8)
        a1 = CurvedArrow(c.get_right() + RIGHT * 0.1, d1.get_center() + UP * 0.15, angle=-0.6, color=BRICK, stroke_width=4)
        a0 = CurvedArrow(c2.get_right() + RIGHT * 0.1, d0.get_center() + UP * 0.15, angle=-0.4, color=INDIGO,
                         stroke_width=4)
        self.play(Create(a1), FadeIn(d1, scale=2), run_time=0.9)
        self.play(Create(a0), FadeIn(d0, scale=2), run_time=0.9)
        xm = M(r"X:\ \Omega\to\mathbb{R}", 44).move_to(RIGHT * 1.8 + UP * 1.6)
        self.play(Write(xm), run_time=1.0)
        bern = VGroup(T("伯努利变量", 28, TEAL, bold=True),
                      M(r"P(X=1)=p,\qquad P(X=0)=1-p", 36)).arrange(RIGHT, buff=0.4)
        bern_b = note_box(bern, TEAL, pad=0.25).move_to(DOWN * 2.25)
        self.wait(max(0.2, self.durs[1] * 0.55 - 4.9))
        self.play(FadeIn(bern_b, shift=UP * 0.2), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(c, c2, nl, n0, n1, d0, d1, a0, a1, xm, bern_b)), run_time=0.7)

        # --- 两个骰子 ---
        self.seg(2)
        s = 0.5
        grid = VGroup()
        cols = {k: interpolate_color(ManimColor(TEAL), ManimColor(BRICK), (k - 2) / 10) for k in range(2, 13)}
        for i in range(1, 7):
            for j in range(1, 7):
                sq = Square(side_length=s, fill_color=tint(cols[i + j], 0.55), fill_opacity=1, stroke_color=BG,
                            stroke_width=2)
                sq.move_to(LEFT * 4.4 + RIGHT * (j - 3.5) * s + DOWN * (i - 3.5) * s + DOWN * 0.35)
                lab = M(str(i + j), 20, INK).move_to(sq)
                cell = VGroup(sq, lab)
                cell.sum = i + j
                grid.add(cell)
        top_d = VGroup(*[die(j, 0.36).move_to(LEFT * 4.4 + RIGHT * (j - 3.5) * s + UP * 1.55 + DOWN * 0.35)
                         for j in range(1, 7)])
        left_d = VGroup(*[die(i, 0.36).move_to(LEFT * 4.4 + LEFT * 3.5 * s + LEFT * 0.35 + DOWN * (i - 3.5) * s +
                                                DOWN * 0.35) for i in range(1, 7)])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in [*top_d, *left_d]], lag_ratio=0.05), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(g, scale=0.6) for g in grid], lag_ratio=0.02), run_time=1.4)
        ax = axes([1.3, 12.8, 1], [0, 6.6, 1], 6.6, 4.0, xnums=list(range(2, 13)), ynums=(), xlabel="X")
        ax.move_to(RIGHT * 3.0 + DOWN * 0.45)
        self.play(Create(ax), run_time=0.7)
        unit = ax.c2p(0, 1)[1] - ax.c2p(0, 0)[1]
        count = {k: 0 for k in range(2, 13)}
        moves = []
        for g in sorted(grid, key=lambda g: g.sum):
            k = g.sum
            target = ax.c2p(k, count[k] + 0.5)
            count[k] += 1
            moves.append(g.animate.scale(unit * 0.92 / s).move_to(target))
        self.play(LaggedStart(*moves, lag_ratio=0.04), run_time=3.2)
        hl = SurroundingRectangle(VGroup(*[g for g in grid if g.sum == 7]), color=GOLD, buff=0.04, stroke_width=3)
        p7 = M(r"P(X=7)=\frac{6}{36}", 40, GOLD).next_to(hl, UP, buff=0.25)
        self.play(Create(hl), Write(p7), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(grid, top_d, left_d, ax, hl, p7, st)), run_time=0.7)


class E1C(VScene):
    SID = "E1C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("质量函数与分布函数")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.5)
        ks = list(range(2, 13))
        ps = [DICE[k] for k in ks]

        # --- 质量函数 ---
        self.seg(0)
        top = axes([1.3, 12.8, 1], [0, 0.2, 0.1], 9.0, 2.3, xnums=ks, ynums=[(1 / 6, r"\tfrac16")], xlabel="x",
                   ylabel="p(k)", num_size=20)
        top.move_to(UP * 0.95 + LEFT * 0.6)
        bs = bars(top, ks, ps, TEAL, w=0.8, opacity=0.4)
        sm = stems(top, ks, ps, TEAL, dot_r=0.07, width=4)
        self.play(Create(top), FadeIn(bs, lag_ratio=0.05), run_time=1.0)
        self.play(ReplacementTransform(bs, sm), run_time=1.0)
        lab = M(r"p(k)=P(X=k),\qquad \sum_k p(k)=1", 34).move_to(RIGHT * 3.9 + UP * 2.4)
        self.play(Write(lab), run_time=1.2)
        self.catch_up()

        # --- 扫出阶梯 ---
        self.seg(1)
        bot = axes([1.3, 12.8, 1], [0, 1.1, 0.5], 9.0, 2.4, xnums=ks, ynums=[0.5, 1], xlabel="x", ylabel="F(x)",
                   num_size=20)
        bot.move_to(DOWN * 2.05 + LEFT * 0.6)
        self.play(Create(bot), FadeOut(lab), run_time=0.8)
        x = ValueTracker(1.3)
        cum = np.cumsum(ps)

        def Fv(v):
            c = 0.0
            for k, p in zip(ks, ps):
                if k <= v:
                    c += p
            return c

        def stair():
            v = x.get_value()
            g = VGroup()
            xs = [1.3] + [k for k in ks if k <= v] + [v]
            for a, b in zip(xs[:-1], xs[1:]):
                if b > a:
                    g.add(Line(bot.c2p(a, Fv(a)), bot.c2p(b, Fv(a)), color=INDIGO, stroke_width=4))
            for k in ks:
                if k <= v:
                    g.add(DashedLine(bot.c2p(k, Fv(k - 0.5)), bot.c2p(k, Fv(k)), color=GREY, stroke_width=1.5,
                                     dash_length=0.04))
                    g.add(Dot(bot.c2p(k, Fv(k)), radius=0.06, color=INDIGO))
            return g

        S = always_redraw(stair)
        scan = always_redraw(lambda: DashedLine(top.c2p(x.get_value(), 0.21), bot.c2p(x.get_value(), 0), color=GOLD,
                                                stroke_width=2, dash_length=0.08))
        lit = always_redraw(lambda: VGroup(*[sm[i].copy().set_color(GOLD) for i, k in enumerate(ks)
                                             if k <= x.get_value()]))
        self.add(S, scan, lit)
        self.play(x.animate.set_value(12.7), run_time=min(8.0, self.durs[1] * 0.75), rate_func=linear)
        fdef = M(r"F(x)=P(X\le x)", 38, INDIGO).move_to(bot.c2p(4.6, 0.8))
        self.play(Write(fdef), run_time=0.9)
        self.catch_up()

        # --- 跳跃高度 ---
        self.seg(2)
        self.remove(scan)
        k = 7
        hollow = Circle(radius=0.07, color=INDIGO, stroke_width=3, fill_color=BG, fill_opacity=1).move_to(
            bot.c2p(k, Fv(k - 0.5)))
        br = BraceBetweenPoints(bot.c2p(k, Fv(k - 0.5)), bot.c2p(k, Fv(k)), direction=RIGHT, color=GOLD)
        brl = M(r"\tfrac{6}{36}", 30, GOLD).next_to(br, RIGHT, buff=0.08)
        link = DashedLine(sm[k - 2][1].get_center(), bot.c2p(k, Fv(k)), color=GOLD, stroke_width=2.5,
                          dash_length=0.07)
        self.play(FadeIn(hollow, scale=1.5), Flash(bot.c2p(k, Fv(k)), color=GOLD, line_length=0.12), run_time=0.8)
        self.play(GrowFromCenter(br), Write(brl), Create(link), Indicate(sm[k - 2], color=GOLD), run_time=1.2)
        note = VGroup(mixed("跳跃高度 = 该点概率", size=24), mixed("实心点在上：右连续", size=24),
                      mixed("从 0 升到 1，从不下降", size=24)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        noteb = note_box(note, GOLD, pad=0.22).move_to(RIGHT * 4.9 + UP * 1.0)
        self.play(FadeOut(fdef), FadeIn(noteb, shift=LEFT * 0.2), run_time=0.8)
        self.catch_up()

        # --- 四条性质 ---
        self.seg(3)
        props = VGroup(bullet("单调不减"), bullet("右连续"), bullet("$\\lim_{x\\to-\\infty}F(x)=0$"),
                       bullet("$\\lim_{x\\to+\\infty}F(x)=1$")).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        head = T("分布函数的全部特征", 28, INK, bold=True)
        pg = VGroup(head, props).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pgb = note_box(pg, INDIGO, pad=0.3).move_to(UP * 0.85)
        self.play(FadeOut(VGroup(top, sm, lit, noteb, link)), run_time=0.6)
        self.play(FadeIn(pgb[:2]), FadeIn(head), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.3) for b in props], lag_ratio=0.5), run_time=2.4)
        self.catch_up()
        self.play(FadeOut(VGroup(pgb, bot, S, hollow, br, brl, st)), run_time=0.7)


class E1D(VScene):
    SID = "E1D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("连续变量与密度")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.5)

        # --- 转盘 ---
        self.seg(0)
        sp = spinner(r=1.7).move_to(LEFT * 3.6 + DOWN * 0.3)
        self.play(FadeIn(sp, scale=0.8), run_time=0.7)
        self.play(spin_to(sp, 0.3702, turns=4, run_time=2.6))
        read = M(r"X=0.3702\ldots", 36).next_to(sp, DOWN, buff=0.35)
        self.play(FadeIn(read), run_time=0.5)
        zero = VGroup(M(r"P(X=0.37)=0", 40),
                      T("无穷多个点平分总概率 1，每个点只能分到 0", 24, MUTED)).arrange(DOWN, buff=0.3)
        zero.move_to(RIGHT * 3.2 + UP * 0.6)
        self.wait(max(0.2, self.durs[0] * 0.45 - 3.8))
        self.play(Write(zero[0]), run_time=1.0)
        self.play(FadeIn(zero[1]), run_time=0.7)
        self.catch_up()

        # --- 区间概率 ---
        self.seg(1)
        self.play(FadeOut(zero), FadeOut(read), run_time=0.5)
        ax = axes([-0.2, 1.25, 0.5], [0, 1.15, 0.5], 4.6, 3.8, xnums=[0, 1], ynums=[1], xlabel="x", ylabel="F(x)")
        ax.move_to(RIGHT * 3.4 + DOWN * 0.3)
        Fl = VMobject(stroke_color=INDIGO, stroke_width=4).set_points_as_corners(
            [ax.c2p(-0.2, 0), ax.c2p(0, 0), ax.c2p(1, 1), ax.c2p(1.2, 1)])
        self.play(Create(ax), Create(Fl), run_time=1.0)
        a, b = 0.25, 0.6
        seg_x = Line(ax.c2p(a, 0), ax.c2p(b, 0), color=GOLD, stroke_width=9)
        seg_y = Line(ax.c2p(0, a), ax.c2p(0, b), color=GOLD, stroke_width=9)
        guides = VGroup(DashedLine(ax.c2p(a, 0), ax.c2p(a, a), color=GREY, stroke_width=1.5),
                        DashedLine(ax.c2p(a, a), ax.c2p(0, a), color=GREY, stroke_width=1.5),
                        DashedLine(ax.c2p(b, 0), ax.c2p(b, b), color=GREY, stroke_width=1.5),
                        DashedLine(ax.c2p(b, b), ax.c2p(0, b), color=GREY, stroke_width=1.5))
        la, lb = M("a", 28, GOLD).next_to(ax.c2p(a, 0), DOWN, buff=0.15), M("b", 28, GOLD).next_to(ax.c2p(b, 0), DOWN,
                                                                                                  buff=0.15)
        arc = AnnularSector(inner_radius=0, outer_radius=sp[0].width / 2, angle=-(b - a) * TAU,
                            start_angle=PI / 2 - a * TAU, fill_color=GOLD, fill_opacity=0.35, stroke_width=0)
        arc.move_arc_center_to(sp[0].get_center())
        self.play(Create(seg_x), FadeIn(la), FadeIn(lb), FadeIn(arc), run_time=1.0)
        self.play(Create(guides), Create(seg_y), run_time=1.0)
        eq = M(r"P(a<X\le b)=F(b)-F(a)=b-a", 34).move_to(UP * 2.35 + RIGHT * 1.2)
        self.play(Write(eq), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(sp, arc, ax, Fl, seg_x, seg_y, guides, la, lb, eq)), run_time=0.6)

        # --- 直方图越分越细 → 密度 ---
        self.seg(2)
        f = lambda x: gamma_pdf(x, 3, 1.3)  # noqa: E731
        Fc = lambda x: 1 - math.exp(-1.3 * x) * (1 + 1.3 * x + (1.3 * x) ** 2 / 2)  # noqa: E731
        ax2 = axes([0, 6.3, 1], [0, 0.42, 0.1], 9.0, 4.2, xnums=[0, 1, 2, 3, 4, 5, 6], ynums=[0.1, 0.2, 0.3, 0.4],
                   ydec=1, xlabel="x", ylabel=T("高度 = 概率 ÷ 格宽", 20, INK))
        ax2.move_to(LEFT * 1.1 + DOWN * 0.5)
        self.play(Create(ax2), run_time=0.8)

        def hist(w):
            g = VGroup()
            x0 = 0.0
            while x0 < 6.0 - 1e-9:
                p = Fc(x0 + w) - Fc(x0)
                h = p / w
                lo, hi = ax2.c2p(x0, 0), ax2.c2p(x0 + w, h)
                g.add(Rectangle(width=hi[0] - lo[0], height=max(hi[1] - lo[1], 1e-3), fill_color=tint(BRICK, 0.45),
                                fill_opacity=1, stroke_color=BRICK, stroke_width=1.2 if w > 0.2 else 0.6)
                      .move_to((lo + hi) / 2))
                x0 += w
            return g

        widths = [1.0, 0.5, 0.25, 0.1, 0.05]
        hcur = hist(widths[0])
        wl = M(r"\Delta x=1", 34).move_to(ax2.c2p(4.8, 0.36))
        self.play(FadeIn(hcur, lag_ratio=0.1), FadeIn(wl), run_time=1.0)
        for w in widths[1:]:
            nl = M(rf"\Delta x={w:g}", 34).move_to(wl)
            self.play(Transform(hcur, hist(w)), Transform(wl, nl), run_time=1.2)
            self.wait(0.3)
        cv = curve(ax2, f, 0, 6, BRICK, width=5)
        self.play(Create(cv), hcur.animate.set_opacity(0.35), FadeOut(wl), run_time=1.2)
        fl = M(r"f(x)", 36, BRICK).next_to(ax2.c2p(1.6, f(1.6)), UP + RIGHT, buff=0.1)
        self.play(FadeIn(fl), run_time=0.4)
        sh = area(ax2, f, 1.2, 2.6, GOLD, opacity=0.55)
        res = VGroup(M(r"P(a<X\le b)=\int_a^b f(x)\,dx", 34), T("概率 = 面积，不是高度", 24, GOLD, bold=True),
                     M(r"F'(x)=f(x)", 34)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        res.move_to(RIGHT * 4.3 + UP * 1.2)
        self.wait(max(0.2, self.durs[2] * 0.55 - 8.6))
        self.play(FadeOut(hcur), FadeIn(sh), Write(res[0]), run_time=1.4)
        self.play(FadeIn(res[1]), run_time=0.6)
        self.wait(max(0.2, self.durs[2] * 0.82 - self.durs[2] * 0.55 - 2.0))
        self.play(Write(res[2]), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, cv, fl, sh, res)), run_time=0.6)

        # --- 三栏总结 ---
        self.seg(3)
        cards = VGroup()
        specs = [("离散变量", "质量函数", r"p(k)=P(X=k)", TEAL, "stems"),
                 ("连续变量", "概率密度", r"f(x)=F'(x)", BRICK, "curve"),
                 ("任何变量", "分布函数", r"F(x)=P(X\le x)", INDIGO, "cdf")]
        for who, what, tex, c, kind in specs:
            box = RoundedRectangle(corner_radius=0.15, width=3.9, height=4.2, fill_color=tint(c, 0.08), fill_opacity=1,
                                   stroke_color=c, stroke_width=2)
            mini = axes([0, 4.2, 1], [0, 1.1, 1], 2.8, 1.6, tips=False)
            if kind == "stems":
                pic = stems(mini, [0.5, 1.3, 2.1, 2.9, 3.7], [0.3, 0.8, 1.0, 0.55, 0.2], c, dot_r=0.05)
            elif kind == "curve":
                pic = VGroup(curve(mini, lambda x: math.exp(-(x - 2) ** 2) * 1.0, 0, 4, c, width=4),
                             area(mini, lambda x: math.exp(-(x - 2) ** 2), 0, 4, c, opacity=0.25))
            else:
                pic = curve(mini, lambda x: 0.5 * (1 + math.erf((x - 2) / 0.8)), 0, 4, c, width=4)
            body = VGroup(T(who, 22, MUTED), T(what, 30, c, bold=True), VGroup(mini, pic), M(tex, 30))
            body.arrange(DOWN, buff=0.25).move_to(box)
            cards.add(VGroup(box, body))
        cards.arrange(RIGHT, buff=0.4).move_to(DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(cd, shift=UP * 0.4) for cd in cards], lag_ratio=0.35), run_time=2.0)
        self.play(Indicate(cards[2], color=INDIGO, scale_factor=1.04), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(cards, st)), run_time=0.7)


class E1E(VScene):
    SID = "E1E"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("逆变换：所有随机数的起点")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.5)

        # --- 均匀随机数 ---
        self.seg(0)
        sp = spinner(r=1.3).move_to(LEFT * 4.2 + DOWN * 0.2)
        ul = M(r"U\sim U(0,1)", 38).next_to(sp, DOWN, buff=0.45)
        self.play(FadeIn(sp), FadeIn(ul), run_time=0.7)
        rng = random.Random(5)
        vals = [rng.random() for _ in range(14)]
        screen = RoundedRectangle(corner_radius=0.12, width=3.4, height=4.2, fill_color=INK, fill_opacity=1,
                                  stroke_width=0).move_to(RIGHT * 0.3 + DOWN * 0.2)
        nums = VGroup(*[Text(f"{v:.6f}", font="DejaVu Sans Mono", font_size=26, color="#9BE3C6") for v in vals])
        nums.arrange(DOWN, buff=0.12).move_to(screen).align_to(screen, UP).shift(DOWN * 0.25)
        self.play(FadeIn(screen), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(n, shift=UP * 0.2) for n in nums[:9]], lag_ratio=0.25),
                  spin_to(sp, 0.71, turns=3, run_time=2.4), run_time=2.6)
        outs = VGroup(*[T(n, 26, c, bold=True) for n, c in (("正态", BRICK), ("指数", BRICK), ("泊松", TEAL),
                                                             ("二项", TEAL))]).arrange(DOWN, buff=0.45)
        outs.move_to(RIGHT * 4.6 + DOWN * 0.2)
        arrows = VGroup(*[Arrow(screen.get_right(), o.get_left(), buff=0.2, color=GREY, stroke_width=3) for o in outs])
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(a_), FadeIn(o)) for a_, o in zip(arrows, outs)],
                              lag_ratio=0.25), run_time=1.6)
        self.catch_up()
        self.play(FadeOut(VGroup(sp, ul, screen, nums[:9], outs, arrows)), run_time=0.6)

        # --- 一次逆变换 ---
        self.seg(1)
        sd = 1.1
        Phi = lambda x: 0.5 * (1 + math.erf(x / (sd * math.sqrt(2))))  # noqa: E731
        top_ax = axes([-4, 4.3, 1], [0, 1.12, 0.5], 10.0, 2.55, xnums=[-4, -2, 0, 2, 4], ynums=[0.5, 1],
                      xlabel="x", ylabel="F(x)")
        top_ax.move_to(UP * 1.0 + LEFT * 0.2)
        cdf = curve(top_ax, Phi, -4, 4.2, INDIGO, width=4.5)
        self.play(Create(top_ax), run_time=0.7)
        self.play(Create(cdf), run_time=1.0)
        u = 0.8
        x_u = sd * math.sqrt(2) * erfinv(2 * u - 1)
        ud = Dot(top_ax.c2p(-4, u), color=GOLD, radius=0.09)
        ulab = M("u", 32, GOLD).next_to(ud, LEFT, buff=0.15)
        h_ar = Arrow(top_ax.c2p(-4, u), top_ax.c2p(x_u, u), buff=0, color=GOLD, stroke_width=4,
                     max_tip_length_to_length_ratio=0.03)
        v_ar = Arrow(top_ax.c2p(x_u, u), top_ax.c2p(x_u, 0), buff=0, color=GOLD, stroke_width=4,
                     max_tip_length_to_length_ratio=0.12)
        xl = M(r"x=F^{-1}(u)", 30, GOLD).next_to(top_ax.c2p(x_u, 0), DOWN + RIGHT, buff=0.12)
        self.play(FadeIn(ud, scale=1.8), FadeIn(ulab), run_time=0.6)
        self.play(GrowArrow(h_ar), run_time=1.2)
        self.play(GrowArrow(v_ar), run_time=0.9)
        self.play(FadeIn(xl), Flash(top_ax.c2p(x_u, 0), color=GOLD), run_time=0.7)
        self.catch_up()

        # --- 为什么对 ---
        self.seg(2)
        der = MathTex(r"P\big(F^{-1}(U)\le x\big)", r"=P\big(U\le F(x)\big)", r"=F(x)", font_size=46)
        der.move_to(DOWN * 1.9)
        bx = soft_box(der, tint(GOLD, 0.15), pad=0.25)
        self.play(FadeIn(bx), Write(der[0]), run_time=1.3)
        self.wait(max(0.2, self.durs[2] * 0.3 - 1.3))
        self.play(Write(der[1]), run_time=1.2)
        self.wait(max(0.2, self.durs[2] * 0.62 - self.durs[2] * 0.3 - 1.2))
        self.play(Write(der[2]), run_time=0.8)
        self.play(Circumscribe(der[2], color=GOLD), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(der, bx, ud, ulab, h_ar, v_ar, xl)), run_time=0.6)

        # --- 很多个 u 落成直方图 ---
        self.seg(3)
        bw = 0.4
        hist_ax = axes([-4, 4.3, 1], [0, 13, 5], 10.0, 2.5, tips=False)
        hist_ax.move_to([top_ax.get_center()[0], -1.85, 0])
        base = Line(hist_ax.c2p(-4, 0), hist_ax.c2p(4.2, 0), color=AXIS, stroke_width=2)
        self.play(Create(base), run_time=0.4)
        N = 90
        us = [(i + 0.5) / N for i in range(N)]
        random.Random(7).shuffle(us)
        counts, movers = {}, []
        unit_h = hist_ax.c2p(0, 1)[1] - hist_ax.c2p(0, 0)[1]
        for uu in us:
            xv = sd * math.sqrt(2) * erfinv(2 * uu - 1)
            b_ = math.floor(xv / bw)
            c_ = counts.get(b_, 0)
            counts[b_] = c_ + 1
            start, corner = top_ax.c2p(-4, uu), top_ax.c2p(xv, uu)
            land = hist_ax.c2p((b_ + 0.5) * bw, c_ * 0.8 + 0.4)
            path = VMobject().set_points_as_corners([start, corner, [corner[0], land[1], 0], land])
            dot = Dot(start, radius=0.05, color=GOLD).set_opacity(0)
            blk = Rectangle(width=(hist_ax.c2p(bw, 0) - hist_ax.c2p(0, 0))[0] * 0.86, height=unit_h * 0.72,
                            fill_color=tint(INDIGO, 0.55), fill_opacity=1, stroke_color=INDIGO, stroke_width=1)
            blk.move_to(land)
            movers.append((dot, path, blk, path.copy().set_stroke(GOLD, width=1.4, opacity=0.4)))

        def travel(dot, path):
            def upd(m, a):
                m.move_to(path.point_from_proportion(rate_functions.ease_in_quad(a)))
                m.set_opacity(1 if a > 0 else 0)
            return UpdateFromAlphaFunc(dot, upd)

        self.play(LaggedStart(*[Succession(AnimationGroup(travel(d, p), ShowPassingFlash(tr, time_width=0.6),
                                                          run_time=0.9), Transform(d, blk, run_time=0.15))
                                for d, p, blk, tr in movers], lag_ratio=0.08), run_time=min(9.0, self.durs[3]))
        dens = curve(hist_ax, lambda x: N * bw * norm_pdf(x, 0, sd) * 0.8, -4, 4.2, INDIGO, width=4)
        self.play(Create(dens), run_time=1.0)
        steep = T("陡处落点密", 22, GOLD, bold=True).move_to(top_ax.c2p(1.6, 0.35))
        self.play(FadeIn(steep), run_time=0.5)
        self.catch_up()

        # --- 概率积分变换 ---
        self.seg(4)
        pit = VGroup(T("概率积分变换", 26, INK, bold=True), mixed("$F$", " 连续时 ", "$F(X)\\sim U(0,1)$", size=26))
        pit.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        pitb = note_box(pit, INDIGO, pad=0.25).move_to(hist_ax.c2p(-2.6, 9))
        xs_ = top_ax.c2p(1.2, 0)
        back = VGroup(Arrow(xs_, top_ax.c2p(1.2, Phi(1.2)), buff=0, color=INDIGO, stroke_width=4,
                            max_tip_length_to_length_ratio=0.15),
                      Arrow(top_ax.c2p(1.2, Phi(1.2)), top_ax.c2p(-4, Phi(1.2)), buff=0, color=INDIGO, stroke_width=4,
                            max_tip_length_to_length_ratio=0.04))
        self.play(FadeOut(steep), FadeIn(pitb, shift=UP * 0.2), Create(back), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(top_ax, cdf, hist_ax, base, dens, pitb, back, st, *[m[0] for m in movers])),
                  run_time=0.8)


class E1F(VScene):
    SID = "E1F"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("期望、方差与矩母函数")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.5)

        # --- 跷跷板：期望是重心 ---
        self.seg(0)
        vals, probs = [0, 1, 2, 3, 4], [0.1, 0.3, 0.3, 0.2, 0.1]
        mean = sum(v * p for v, p in zip(vals, probs))
        L = 1.9  # 数轴每单位长度
        piv_y = -1.4
        fx = ValueTracker(0.6)

        def scene_beam():
            fv = fx.get_value()
            torque = sum(p * (v - fv) for v, p in zip(vals, probs))
            ang = -max(-0.18, min(0.18, torque * 0.35))
            pivot = np.array([(fv - 2) * L, piv_y, 0])
            beam = Line(LEFT * 4.9, RIGHT * 4.9, stroke_width=6, color=INK)
            g = VGroup(beam)
            for v, p in zip(vals, probs):
                blk = Rectangle(width=0.9, height=p * 9, fill_color=tint(TEAL, 0.55), fill_opacity=1,
                                stroke_color=TEAL, stroke_width=2)
                blk.next_to(np.array([(v - 2) * L, 0, 0]), UP, buff=0.03)
                lab = M(str(v), 26, MUTED).next_to(np.array([(v - 2) * L, 0, 0]), DOWN, buff=0.12)
                g.add(blk, lab)
            g.shift(UP * (piv_y + 0.32))
            g.rotate(ang, about_point=pivot + UP * 0.32)
            tri = Triangle(fill_color=GOLD, fill_opacity=1, stroke_width=0).scale(0.3).move_to(pivot)
            ground = Line(LEFT * 6, RIGHT * 6, color=FAINT, stroke_width=2).move_to([0, piv_y - 0.26, 0])
            return VGroup(ground, g, tri)

        B = always_redraw(scene_beam)
        self.play(FadeIn(B), run_time=0.8)
        self.play(fx.animate.set_value(3.2), run_time=1.6, rate_func=smooth)
        self.play(fx.animate.set_value(mean), run_time=1.6, rate_func=smooth)
        ex = M(r"\mathbb{E}X=\sum_k k\,p(k)=" + f"{mean:g}", 42).move_to(UP * 2.2)
        self.play(Write(ex), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(B), FadeOut(ex), run_time=0.6)

        # --- 方差 ---
        self.seg(1)
        axl = axes([-4.5, 4.5, 1], [0, 0.5, 0.1], 5.4, 2.6, xnums=[-4, -2, 0, 2, 4], tips=False)
        axr = axes([-4.5, 4.5, 1], [0, 0.5, 0.1], 5.4, 2.6, xnums=[-4, -2, 0, 2, 4], tips=False)
        VGroup(axl, axr).arrange(RIGHT, buff=1.0).move_to(DOWN * 0.1)
        ks = list(range(-4, 5))
        narrow = [binom_pmf(8, 0.5, k + 4) if abs(k) <= 2 else binom_pmf(8, 0.5, k + 4) * 0.2 for k in ks]
        s_ = sum(narrow)
        narrow = [v / s_ for v in narrow]
        wide = [0.11] * 9
        wide = [v / sum(wide) for v in wide]
        sl, sr = stems(axl, ks, narrow, TEAL, dot_r=0.06), stems(axr, ks, wide, BRICK, dot_r=0.06)
        tl = T("集中：方差小", 24, TEAL, bold=True).next_to(axl, UP, buff=0.15)
        tr = T("分散：方差大", 24, BRICK, bold=True).next_to(axr, UP, buff=0.15)
        self.play(Create(axl), Create(axr), FadeIn(sl), FadeIn(sr), FadeIn(tl), FadeIn(tr), run_time=1.2)
        arrs = VGroup(*[DoubleArrow(axr.c2p(0, 0.02 + 0.03 * i), axr.c2p(k, 0.02 + 0.03 * i), buff=0, color=GOLD,
                                    stroke_width=2, tip_length=0.1) for i, k in enumerate([-4, -2, 3, 4]) if k])
        self.play(LaggedStart(*[GrowFromPoint(a_, axr.c2p(0, 0)) for a_ in arrs], lag_ratio=0.2), run_time=1.0)
        var = M(r"\operatorname{Var}X=\mathbb{E}(X-\mathbb{E}X)^2=\mathbb{E}X^2-(\mathbb{E}X)^2", 38).move_to(UP * 2.25)
        self.play(Write(var), run_time=1.5)
        bern = mixed("伯努利：", "$\\mathbb{E}X=p,\\ \\ \\operatorname{Var}X=p(1-p)$", size=28, color=TEAL)
        bern.move_to(DOWN * 2.3)
        self.wait(max(0.2, self.durs[1] * 0.68 - 3.7))
        self.play(FadeIn(bern, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(axl, axr, sl, sr, tl, tr, arrs, var, bern)), run_time=0.6)

        # --- 矩母函数 ---
        self.seg(2)
        mdef = M(r"M(t)=\mathbb{E}\,e^{tX}", 52).move_to(UP * 1.9)
        self.play(Write(mdef), run_time=1.2)
        exp = MathTex(r"=1", r"+t\,\mathbb{E}X", r"+\frac{t^2}{2!}\mathbb{E}X^2", r"+\frac{t^3}{3!}\mathbb{E}X^3",
                      r"+\cdots", font_size=48).move_to(UP * 0.35)
        self.play(Write(exp[0]), run_time=0.5)
        cols = [TEAL, BRICK, INDIGO]
        for i in range(1, 4):
            self.play(Write(exp[i]), run_time=0.8)
            self.play(exp[i].animate.set_color(cols[i - 1]), run_time=0.3)
        self.play(Write(exp[4]), run_time=0.4)
        der = M(r"\mathbb{E}X^n=M^{(n)}(0)", 44, GOLD).move_to(DOWN * 1.5)
        self.play(FadeIn(der, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(exp, der)), mdef.animate.scale(0.75).move_to(UP * 2.3 + LEFT * 4.2), run_time=0.7)

        # --- 独立和 ---
        self.seg(3)
        l1 = MathTex(r"e^{t(X+Y)}", r"=", r"e^{tX}", r"\cdot", r"e^{tY}", font_size=50).move_to(UP * 1.0)
        l2 = MathTex(r"M_{X+Y}(t)", r"=", r"\mathbb{E}e^{tX}", r"\cdot", r"\mathbb{E}e^{tY}", font_size=50)
        l3 = MathTex(r"=M_X(t)\,M_Y(t)", font_size=50)
        l2.move_to(DOWN * 0.3)
        l3.next_to(l2, DOWN, buff=0.35).align_to(l2[1], LEFT)
        self.play(Write(l1), run_time=1.4)
        self.play(l1[2].animate.set_color(TEAL), l1[4].animate.set_color(BRICK), run_time=0.6)
        ind = T("（独立）", 24, GOLD, bold=True).next_to(l2, RIGHT, buff=0.3)
        self.play(TransformFromCopy(l1, l2), run_time=1.3)
        self.play(FadeIn(ind, shift=DOWN * 0.15), l2[2].animate.set_color(TEAL), l2[4].animate.set_color(BRICK),
                  run_time=0.8)
        self.play(Write(l3), run_time=1.0)
        hl = SurroundingRectangle(VGroup(l2[0], l3), color=GOLD, buff=0.15, corner_radius=0.08)
        uniq = T("矩母函数存在时唯一确定分布 → 各种“可加性”都由此推出", 24, MUTED).move_to(DOWN * 2.6)
        self.play(Create(hl), run_time=0.8)
        self.wait(max(0.2, self.durs[3] * 0.62 - 5.9))
        self.play(FadeIn(uniq, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(l1, l2, l3, hl, ind, uniq, mdef, st)), run_time=0.7)

        # --- 预告 ---
        self.seg(4)
        faces = ["正", "反", "正", "正", "反", "正", "反", "正"]
        coins = VGroup(*[coin("反", r=0.4) for _ in faces]).arrange(RIGHT, buff=0.3).move_to(UP * 0.4)
        self.play(LaggedStart(*[FadeIn(c, scale=0.5) for c in coins], lag_ratio=0.08), run_time=0.8)
        self.play(LaggedStart(*[flip(c, f, times=3, run_time=0.9, height=0.7) for c, f in zip(coins, faces)],
                              lag_ratio=0.15), run_time=2.2)
        lab = mixed("正面出现 ", "$5$", " 次", size=34).next_to(coins, DOWN, buff=0.6)
        self.play(LaggedStart(*[Indicate(c, color=GOLD) for c, f in zip(coins, faces) if f == "正"], lag_ratio=0.2),
                  FadeIn(lab), run_time=1.5)
        nxt = T("下一集：二项分布", 30, TEAL, bold=True).next_to(lab, DOWN, buff=0.5)
        self.play(FadeIn(nxt, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
