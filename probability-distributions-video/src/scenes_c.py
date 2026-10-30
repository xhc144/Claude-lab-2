# -*- coding: utf-8 -*-
"""第三章：连续分布（S04 均匀、指数、伽马、正态；S05 对数正态、贝塔、韦布尔、柯西）。"""
from common import *  # noqa: F401,F403


def lognorm_pdf(x, mu, s):
    if x <= 0:
        return 0.0
    return math.exp(-(math.log(x) - mu) ** 2 / (2 * s * s)) / (x * s * math.sqrt(2 * math.pi))


def weibull_pdf(x, k, lam=1.0):
    if x <= 0:
        return 0.0
    return k / lam * (x / lam) ** (k - 1) * math.exp(-(x / lam) ** k)


def weibull_h(x, k, lam=1.0):
    if x <= 0:
        return 0.0
    return k / lam * (x / lam) ** (k - 1)


def cauchy_pdf(x):
    return 1 / (math.pi * (1 + x * x))


class S04(VScene):
    SID = "S04"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "03")

        # --- 均匀分布 ---
        self.seg(1)
        eh = entry_header("均匀分布", "Uniform", r"X\sim U(a,b)", BRICK)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.7)
        a, b = 1.0, 2.6
        axl = axes([-0.6, 3.4, 1], [0, 1.0, 0.5], 5.4, 2.2, xnums=[(0, "0"), (a, "a"), (b, "b")],
                   ynums=[(0.62, r"\frac{1}{b-a}")], xlabel="x", ylabel="f(x)")
        axr = axes([-0.6, 3.4, 1], [0, 1.2, 0.5], 5.4, 2.2, xnums=[(0, "0"), (a, "a"), (b, "b")],
                   ynums=[(1, "1")], xlabel="x", ylabel="F(x)")
        VGroup(axl, axr).arrange(RIGHT, buff=1.4).move_to(UP * 0.95)
        h = 0.62
        dens = VGroup(Line(axl.c2p(-0.6, 0), axl.c2p(a, 0), color=BRICK, stroke_width=4),
                      Line(axl.c2p(a, h), axl.c2p(b, h), color=BRICK, stroke_width=4),
                      Line(axl.c2p(b, 0), axl.c2p(3.3, 0), color=BRICK, stroke_width=4))
        fill = Polygon(axl.c2p(a, 0), axl.c2p(a, h), axl.c2p(b, h), axl.c2p(b, 0), fill_color=BRICK,
                       fill_opacity=0.2, stroke_width=0)
        cdf = VMobject(stroke_color=BRICK, stroke_width=4).set_points_as_corners(
            [axr.c2p(-0.6, 0), axr.c2p(a, 0), axr.c2p(b, 1), axr.c2p(3.3, 1)])
        self.play(Create(axl), Create(axr), run_time=0.9)
        self.play(Create(dens), FadeIn(fill), Create(cdf), run_time=1.4)
        cards = stat_cards([("期望", r"\frac{a+b}{2}"), ("方差", r"\frac{(b-a)^2}{12}"),
                            ("矩母函数", r"\frac{e^{tb}-e^{ta}}{t(b-a)}")], BRICK, y=-1.25, value_size=32)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.25), run_time=1.3)
        inv = mixed("随机数之源：", "$-\\frac{1}{\\lambda}\\ln U\\sim\\mathrm{Exp}(\\lambda)$", size=24)
        inv.move_to(DOWN * 2.55)
        self.wait(max(0.2, self.durs[1] * 0.62 - 4.3))
        self.play(FadeIn(inv, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(axl, axr, dens, fill, cdf, cards, inv)), run_time=0.6)

        # --- 指数分布 ---
        self.seg(2)
        eh2 = entry_header("指数分布", "Exponential", r"X\sim\mathrm{Exp}(\lambda)", BRICK)
        self.play(FadeTransform(eh, eh2), run_time=0.7)
        ax = axes([0, 5.3, 1], [0, 2.15, 0.5], 8.2, 4.3, xnums=[0, 1, 2, 3, 4, 5], ynums=[0.5, 1, 1.5, 2],
                  xlabel="x", ylabel="f(x)")
        ax.move_to(LEFT * 2.3 + DOWN * 0.55)
        specs = [(0.5, INK), (1, TEAL), (2, BRICK)]
        cs = VGroup(*[curve(ax, lambda x, l=l: l * math.exp(-l * x), 0, 5.2, c, width=4) for l, c in specs])
        lg = legend([(INK, r"$\lambda=0.5$"), (TEAL, r"$\lambda=1$"), (BRICK, r"$\lambda=2$")])
        lg.move_to(ax.c2p(3.8, 1.7))
        self.play(Create(ax), run_time=0.7)
        self.play(LaggedStart(*[Create(c) for c in cs], lag_ratio=0.35), FadeIn(lg), run_time=2.0)
        col = VGroup(M(r"f(x)=\lambda e^{-\lambda x}", 38), M(r"\mathbb{E}X=\frac{1}{\lambda}", 38),
                     mixed("风险率 ", "$h(x)=\\lambda$", "：不老化", size=26)).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        col.move_to(RIGHT * 4.3 + UP * 0.6)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.2) for m in col], lag_ratio=0.4), run_time=1.8)
        self.catch_up()

        # --- 无记忆性的几何含义 ---
        self.seg(3)
        f1 = lambda x: math.exp(-x)  # noqa: E731
        s = 1.0
        self.play(FadeOut(cs[0]), FadeOut(cs[2]), FadeOut(lg), cs[1].animate.set_color(BRICK), run_time=0.8)
        head = area(ax, f1, 0, s, GREY, opacity=0.25)
        tail = area(ax, f1, s, 5.2, BRICK, opacity=0.25)
        sl = DashedLine(ax.c2p(s, 0), ax.c2p(s, 2.0), color=GOLD, stroke_width=3, dash_length=0.07)
        sll = M("s", 30, GOLD).next_to(ax.c2p(s, 0), DOWN, buff=0.3)
        self.play(FadeIn(head), FadeIn(tail), Create(sl), FadeIn(sll), run_time=1.0)
        cut_t = T("截去 [0, s]，再重新归一化", 24, INK).move_to(ax.c2p(3.4, 1.85))
        self.play(FadeIn(cut_t), FadeOut(head), run_time=0.8)
        tail_curve = curve(ax, f1, s, 5.2, BRICK, width=4)
        scaled = curve(ax, lambda x: math.exp(-(x - s)), s, 5.2, BRICK, width=4)
        scaled_area = area(ax, lambda x: math.exp(-(x - s)), s, 5.2, BRICK, opacity=0.25)
        ghost = DashedVMobject(curve(ax, f1, 0, 4.2, INK, width=3), num_dashes=40)
        self.add(tail_curve)
        self.play(Transform(tail_curve, scaled), Transform(tail, scaled_area), run_time=1.6, rate_func=smooth)
        self.play(FadeIn(ghost), run_time=0.4)
        self.play(ghost.animate.shift(ax.c2p(s, 0) - ax.c2p(0, 0)), run_time=1.4, rate_func=smooth)
        mem = M(r"P(X>s+t\mid X>s)=P(X>t)", 34)
        mem_n = T("连续分布中唯一无记忆：几何分布的连续版本", 22, MUTED)
        memg = VGroup(mem, mem_n).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(col, DOWN, buff=0.6)
        memg.align_to(col, LEFT)
        if memg.get_right()[0] > 6.9:
            memg.shift(LEFT * (memg.get_right()[0] - 6.9))
        self.play(Write(mem), run_time=1.2)
        self.play(FadeIn(mem_n), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, cs[1], tail, tail_curve, sl, sll, cut_t, ghost, col, memg)), run_time=0.6)

        # --- 伽马分布 ---
        self.seg(4)
        eh3 = entry_header("伽马分布", "Gamma", r"X\sim\Gamma(\alpha,\lambda)", BRICK)
        self.play(FadeTransform(eh2, eh3), run_time=0.7)
        ax3 = axes([0, 8.3, 1], [0, 1.1, 0.5], 8.4, 4.2, xnums=list(range(0, 9)), ynums=[0.5, 1],
                   xlabel="x", ylabel="f(x)")
        ax3.move_to(LEFT * 2.3 + DOWN * 0.55)
        al = ValueTracker(0.5)
        g = always_redraw(lambda: curve(ax3, lambda x: gamma_pdf(x, al.get_value()), 0.004, 8.2, BRICK, width=4.5,
                                        ymax=1.08))
        alab = VGroup(M(r"\alpha=", 36), DecimalNumber(0.5, num_decimal_places=1, font_size=36, color=INK))
        alab.arrange(RIGHT, buff=0.1).move_to(ax3.c2p(6.2, 0.95))
        alab[1].add_updater(lambda m: m.set_value(al.get_value()))
        fg = M(r"f(x)=\frac{\lambda^\alpha}{\Gamma(\alpha)}x^{\alpha-1}e^{-\lambda x}", 34)
        b1 = bullet("$\\alpha=1$", "：指数分布", size=22)
        b2 = bullet("$n$", " 个独立 ", "$\\mathrm{Exp}(\\lambda)$", " 之和 ", "$\\sim\\Gamma(n,\\lambda)$", size=22)
        b3 = bullet("$\\alpha<1$", " 在 0 处发散；", "$\\alpha\\to\\infty$", " 趋于正态", size=22)
        col3 = VGroup(fg, b1, b2, b3).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(RIGHT * 4.25 + UP * 0.55)
        if col3.get_right()[0] > 6.95:
            col3.shift(LEFT * (col3.get_right()[0] - 6.95))
        self.play(Create(ax3), FadeIn(alab), run_time=0.8)
        self.play(Create(g), FadeIn(fg), run_time=1.2)
        traces = VGroup()
        stops = [(1, b1), (2, b2), (3, None), (5, b3)]
        for v, bl in stops:
            traces.add(curve(ax3, lambda x, a_=al.get_value(): gamma_pdf(x, a_), 0.004, 8.2, BRICK, width=2,
                             ymax=1.08).set_stroke(opacity=0.25))
            self.add(traces[-1])
            anims = [al.animate.set_value(v)]
            if bl is not None:
                anims.append(FadeIn(bl, shift=RIGHT * 0.2))
            self.play(*anims, run_time=2.0, rate_func=smooth)
            self.wait(0.6)
        self.catch_up()
        alab[1].clear_updaters()
        self.play(FadeOut(VGroup(ax3, g, traces, alab, col3)), run_time=0.6)

        # --- 正态分布 ---
        self.seg(5)
        eh4 = entry_header("正态分布", "Normal / Gaussian", r"X\sim N(\mu,\sigma^2)", BRICK)
        self.play(FadeTransform(eh3, eh4), run_time=0.7)
        ax4 = axes([-4, 4.2, 1], [0, 0.45, 0.1], 11.0, 3.6, xnums=(), ynums=(), xlabel="x")
        ax4.move_to(DOWN * 1.05)
        bell = curve(ax4, norm_pdf, -4, 4, BRICK, width=5)
        gl = glow(bell, BRICK, layers=4, width=14, opacity=0.06)
        fn = M(r"f(x)=\frac{1}{\sqrt{2\pi}\,\sigma}\exp\!\Big(-\frac{(x-\mu)^2}{2\sigma^2}\Big)", 40)
        fn.move_to(UP * 1.75)
        self.play(Create(ax4), run_time=0.7)
        self.play(Create(bell), FadeIn(gl), run_time=1.6)
        self.play(Write(fn), run_time=1.5)
        self.catch_up()

        # --- 经验法则 ---
        self.seg(6)
        ticks = VGroup()
        names = {-3: r"\mu-3\sigma", -2: r"\mu-2\sigma", -1: r"\mu-\sigma", 0: r"\mu", 1: r"\mu+\sigma",
                 2: r"\mu+2\sigma", 3: r"\mu+3\sigma"}
        for k, s_ in names.items():
            ticks.add(VGroup(Line(ax4.c2p(k, 0) + UP * 0.05, ax4.c2p(k, 0) + DOWN * 0.05, color=AXIS),
                             M(s_, 22, MUTED).next_to(ax4.c2p(k, 0), DOWN, buff=0.12)))
        self.play(FadeOut(fn), FadeIn(ticks), run_time=0.7)
        bands = []
        for k, op in ((1, 0.55), (2, 0.32), (3, 0.16)):
            parts = VGroup(area(ax4, norm_pdf, -k, -(k - 1), BRICK, opacity=op),
                           area(ax4, norm_pdf, k - 1, k, BRICK, opacity=op)) if k > 1 else \
                VGroup(area(ax4, norm_pdf, -1, 1, BRICK, opacity=op))
            bands.append(parts)
        p68 = T("68.27%", 30, WHITE, bold=True).move_to(ax4.c2p(0, 0.17))
        arrows = VGroup()
        for k, txt, y in ((2, "95.45%", 0.47), (3, "99.73%", 0.555)):
            l_, r_ = ax4.c2p(-k, y), ax4.c2p(k, y)
            ar = DoubleArrow(l_, r_, buff=0, color=GREY, stroke_width=2, tip_length=0.15,
                             max_tip_length_to_length_ratio=0.05)
            lab = T(txt, 22, BRICK, bold=True)
            bg = BackgroundRectangle(lab, color=BG, fill_opacity=1, buff=0.06)
            vg = VGroup(ar, bg, lab.move_to(ar))
            bg.move_to(ar)
            drops = VGroup(DashedLine(ax4.c2p(-k, 0), l_, color=GREY, stroke_width=1.2, dash_length=0.05),
                           DashedLine(ax4.c2p(k, 0), r_, color=GREY, stroke_width=1.2, dash_length=0.05))
            arrows.add(VGroup(drops, vg))
        self.add(bands[0], bell)
        self.play(FadeIn(bands[0]), run_time=0.8)
        self.play(FadeIn(p68, scale=0.6), run_time=0.6)
        self.play(FadeIn(bands[1]), GrowFromCenter(arrows[0]), run_time=1.1)
        self.play(FadeIn(bands[2]), GrowFromCenter(arrows[1]), run_time=1.1)
        self.bring_to_front(bell)
        q = mixed("双侧 95% 分位点 ", "$1.96$", size=24)
        qb = note_box(q, BRICK, pad=0.2).to_edge(RIGHT, buff=0.4).set_y(0.95)
        self.wait(max(0.2, self.durs[6] * 0.7 - 4.3))
        self.play(FadeIn(qb, shift=LEFT * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(*bands, p68, arrows, qb, ticks, gl)), run_time=0.6)

        # --- 平移与伸缩 ---
        self.seg(7)
        ax5 = axes([-6, 8.3, 1], [0, 0.85, 0.2], 11.0, 3.9, xnums=[-6, -4, -2, 0, 2, 4, 6, 8],
                   ynums=[0.2, 0.4, 0.6, 0.8], ydec=1, xlabel="x", ylabel="f(x)")
        ax5.move_to(LEFT * 0.4 + DOWN * 0.75)
        mu, sg = ValueTracker(0.0), ValueTracker(1.0)
        moving = always_redraw(lambda: curve(ax5, lambda x: norm_pdf(x, mu.get_value(), sg.get_value()), -6, 8.2,
                                             BRICK, width=4.5, ymax=0.84))
        base = DashedVMobject(curve(ax5, norm_pdf, -6, 8.2, INK, width=2.5), num_dashes=70)
        self.play(ReplacementTransform(ax4, ax5), ReplacementTransform(bell, moving), run_time=1.2)
        self.add(base, moving)
        lab = VGroup(M(r"\mu=", 34), DecimalNumber(0, num_decimal_places=1, font_size=34, color=INK),
                     M(r"\sigma=", 34), DecimalNumber(1, num_decimal_places=2, font_size=34, color=INK))
        lab.arrange(RIGHT, buff=0.1)
        lab[2].shift(RIGHT * 0.35)
        lab[3].shift(RIGHT * 0.35)
        lab.move_to(ax5.c2p(5.4, 0.72))
        lab[1].add_updater(lambda m: m.set_value(mu.get_value()))
        lab[3].add_updater(lambda m: m.set_value(sg.get_value()))
        self.play(FadeIn(base), FadeIn(lab), run_time=0.6)
        t1 = T("μ 只管平移", 26, GOLD, bold=True).move_to(ax5.c2p(-3.8, 0.72))
        self.play(FadeIn(t1), mu.animate.set_value(3), run_time=1.6, rate_func=smooth)
        self.play(mu.animate.set_value(0), run_time=1.0, rate_func=smooth)
        t2 = T("σ 只管伸缩", 26, GOLD, bold=True).move_to(t1).shift(DOWN * 0.55)
        self.play(FadeIn(t2), sg.animate.set_value(2), run_time=1.4, rate_func=smooth)
        self.play(sg.animate.set_value(0.5), run_time=1.4, rate_func=smooth)
        self.play(sg.animate.set_value(1), run_time=0.9, rate_func=smooth)
        lin = mixed("$\\sum a_iX_i\\sim N\\big(\\sum a_i\\mu_i,\\ \\sum a_i^2\\sigma_i^2\\big)$", size=26)
        clt = T("中心极限定理：正态到处出现的根本原因", 22, MUTED)
        colx = VGroup(lin, clt).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ax5.c2p(4.9, 0.42))
        self.play(FadeIn(colx, shift=UP * 0.2), run_time=0.9)
        self.catch_up()
        lab[1].clear_updaters()
        lab[3].clear_updaters()
        self.play(FadeOut(VGroup(ax5, moving, base, lab, t1, t2, colx, eh4)), run_time=0.7)


class S05(VScene):
    SID = "S05"

    def construct(self):
        hdr = running_header("03")
        self.add(hdr)

        # --- 对数正态 ---
        self.seg(0)
        eh = entry_header("对数正态分布", "Log-normal", r"X\sim\mathrm{LN}(\mu,\sigma^2)", BRICK)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.7)
        ax = axes([0, 4.15, 0.5], [0, 1.75, 0.5], 8.4, 4.2, xnums=[0, 1, 2, 3, 4], ynums=[0.5, 1, 1.5],
                  xlabel="x", ylabel="f(x)")
        ax.move_to(LEFT * 2.3 + DOWN * 0.55)
        df = M(r"X=e^{Y},\quad Y\sim N(\mu,\sigma^2)", 36).move_to(RIGHT * 4.2 + UP * 1.75)
        self.play(Create(ax), Write(df), run_time=1.2)
        specs = [(0.25, INK), (0.5, TEAL), (1.0, BRICK)]
        cs = VGroup(*[curve(ax, lambda x, s=s: lognorm_pdf(x, 0, s), 0.01, 4.1, c, width=4) for s, c in specs])
        lg = legend([(INK, r"$\sigma=0.25$"), (TEAL, r"$\sigma=0.5$"), (BRICK, r"$\sigma=1$")])
        lg.move_to(ax.c2p(2.75, 1.45))
        self.play(LaggedStart(*[Create(c) for c in cs], lag_ratio=0.3), FadeIn(lg), run_time=2.0)
        mult = VGroup(T("乘积封闭", 24, INK, bold=True),
                      T("许多独立正因子相乘：收入、颗粒尺寸……", 20, MUTED),
                      T("乘法版的中心极限定理", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        multb = note_box(mult, BRICK, pad=0.22).move_to(RIGHT * 4.25 + UP * 0.45)
        self.wait(max(0.2, self.durs[0] * 0.2 - 3.9))
        self.play(FadeIn(multb, shift=LEFT * 0.2), run_time=0.8)
        self.wait(max(0.2, self.durs[0] * 0.6 - self.durs[0] * 0.2 - 0.8))
        marks = VGroup()
        for xv, name in ((math.exp(-1), "众数"), (1.0, "中位数"), (math.exp(0.5), "均值")):
            yv = lognorm_pdf(xv, 0, 1)
            ln = DashedLine(ax.c2p(xv, 0), ax.c2p(xv, yv), color=BRICK, stroke_width=2.2, dash_length=0.06)
            t_ = T(name, 18, BRICK).next_to(ax.c2p(xv, yv), UP + RIGHT * 0.3, buff=0.08)
            marks.add(VGroup(ln, t_))
        self.play(LaggedStart(*[Create(m[0]) for m in marks], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(m[1]) for m in marks], lag_ratio=0.3), run_time=1.5)
        ineq = M(r"e^{\mu-\sigma^2}<e^{\mu}<e^{\mu+\sigma^2/2}", 34).next_to(multb, DOWN, buff=0.5)
        self.play(Write(ineq), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, cs, lg, marks, df, multb, ineq)), run_time=0.6)

        # --- 贝塔：形状变化 ---
        self.seg(1)
        eh2 = entry_header("贝塔分布", "Beta", r"X\sim\mathrm{Beta}(\alpha,\beta)", BRICK)
        self.play(FadeTransform(eh, eh2), run_time=0.7)
        axb = axes([0, 1.04, 0.1], [0, 3.6, 1], 8.4, 4.2, xnums=[0, 0.5, 1], ynums=[1, 2, 3],
                   xlabel="x", ylabel="f(x)")
        axb.move_to(LEFT * 2.3 + DOWN * 0.55)
        A, B = ValueTracker(0.5), ValueTracker(0.5)
        bc = always_redraw(lambda: curve(axb, lambda x: beta_pdf(x, A.get_value(), B.get_value()), 0.002, 0.998,
                                         BRICK, width=4.5, ymax=3.55))
        bf = always_redraw(lambda: area(axb, lambda x: beta_pdf(x, A.get_value(), B.get_value()), 0.002, 0.998,
                                        BRICK, opacity=0.15, ymax=3.55))
        ab = VGroup(M(r"\alpha=", 34), DecimalNumber(0.5, num_decimal_places=1, font_size=34, color=INK),
                    M(r"\beta=", 34), DecimalNumber(0.5, num_decimal_places=1, font_size=34, color=INK))
        ab.arrange(RIGHT, buff=0.1)
        ab[2:].shift(RIGHT * 0.35)
        ab.move_to(axb.c2p(0.5, 3.3))
        ab[1].add_updater(lambda m: m.set_value(A.get_value()))
        ab[3].add_updater(lambda m: m.set_value(B.get_value()))
        fb = M(r"f(x)=\frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha,\beta)}", 34)
        eb = M(r"\mathbb{E}X=\frac{\alpha}{\alpha+\beta}", 34)
        nb = VGroup(T("U 形、均匀、单调、单峰、偏斜", 22, MUTED),
                    mixed("$\\alpha+\\beta$", " 越大越集中", size=22, color=MUTED)).arrange(DOWN, aligned_edge=LEFT,
                                                                                     buff=0.15)
        colb = VGroup(fb, eb, nb).arrange(DOWN, aligned_edge=LEFT, buff=0.38).move_to(RIGHT * 4.35 + UP * 0.5)
        self.play(Create(axb), FadeIn(ab), run_time=0.8)
        self.play(Create(bc), FadeIn(bf), FadeIn(fb), run_time=1.0)
        shapes = [(1, 1), (2, 5), (5, 2), (2, 2), (8, 8)]
        extras = {1: eb, 3: nb}
        for i, (a_, b_) in enumerate(shapes):
            anims = [A.animate.set_value(a_), B.animate.set_value(b_)]
            if i in extras:
                anims.append(FadeIn(extras[i], shift=RIGHT * 0.2))
            self.play(*anims, run_time=1.5, rate_func=smooth)
            self.wait(0.9)
        self.catch_up()

        # --- 共轭更新 ---
        self.seg(2)
        ab[1].clear_updaters()
        ab[3].clear_updaters()
        self.play(FadeOut(colb), FadeOut(ab), A.animate.set_value(2), B.animate.set_value(2), run_time=1.0)
        prior = DashedVMobject(curve(axb, lambda x: beta_pdf(x, 2, 2), 0.002, 0.998, BRICK, width=3), num_dashes=50)
        pl = mixed("先验 ", "$\\mathrm{Beta}(2,2)$", size=24)
        pl.move_to(axb.c2p(0.5, 3.3))
        self.play(FadeIn(prior), FadeIn(pl), run_time=0.7)
        seq = [1, 1, 0, 1, 1, 1, 0, 1, 0, 1]
        toks = VGroup()
        for r_ in seq:
            c = Circle(radius=0.17, color=TEAL, stroke_width=3, fill_color=TEAL if r_ else BG, fill_opacity=1)
            toks.add(c)
        toks.arrange(RIGHT, buff=0.12).move_to(RIGHT * 4.3 + UP * 1.75)
        tok_l = mixed("10 次试验，成功 7 次", size=22, color=MUTED).next_to(toks, DOWN, buff=0.2)
        self.play(FadeIn(tok_l), run_time=0.5)
        a_, b_ = 2, 2
        cnt = M(r"\mathrm{Beta}(2,\,2)", 36).next_to(tok_l, DOWN, buff=0.45)
        self.play(FadeIn(cnt), run_time=0.4)
        for tk, r_ in zip(toks, seq):
            a_ += r_
            b_ += 1 - r_
            new_cnt = M(rf"\mathrm{{Beta}}({a_},\,{b_})", 36).move_to(cnt)
            self.play(FadeIn(tk, scale=1.5), A.animate.set_value(a_), B.animate.set_value(b_),
                      Transform(cnt, new_cnt), run_time=0.75)
        post = mixed("后验 ", "$\\mathrm{Beta}(9,5)$", size=24, color=BRICK).move_to(axb.c2p(0.25, 3.3))
        self.play(pl.animate.move_to(axb.c2p(0.2, 2.9)).set_opacity(0.6), FadeIn(post.move_to(axb.c2p(0.22, 3.35))),
                  run_time=0.6)
        rule = M(r"\mathrm{Beta}(\alpha,\beta)\ \longrightarrow\ \mathrm{Beta}(\alpha+k,\ \beta+n-k)", 30)
        rule_n = T("α、β：先验中的成功与失败次数", 22, MUTED)
        rg = VGroup(rule, rule_n).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(cnt, DOWN, buff=0.5)
        rg.set_x(4.1)
        if rg.get_right()[0] > 6.95:
            rg.shift(LEFT * (rg.get_right()[0] - 6.95))
        self.play(Write(rule), run_time=1.2)
        self.play(FadeIn(rule_n), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(axb, bc, bf, prior, pl, post, toks, tok_l, cnt, rg)), run_time=0.6)

        # --- 韦布尔 ---
        self.seg(3)
        eh3 = entry_header("韦布尔分布", "Weibull", r"X\sim\mathrm{Weibull}(k,\lambda)", BRICK)
        self.play(FadeTransform(eh2, eh3), run_time=0.7)
        hf = M(r"h(x)=\frac{k}{\lambda}\Big(\frac{x}{\lambda}\Big)^{k-1}", 34).move_to(UP * 1.85)
        axd = axes([0, 2.65, 0.5], [0, 1.6, 0.5], 5.6, 3.3, xnums=[0, 1, 2], ynums=[0.5, 1, 1.5],
                   xlabel="x", ylabel="f(x)")
        axh = axes([0, 2.65, 0.5], [0, 4.2, 1], 5.6, 3.3, xnums=[0, 1, 2], ynums=[1, 2, 3, 4],
                   xlabel="x", ylabel="h(x)")
        VGroup(axd, axh).arrange(RIGHT, buff=1.2).move_to(DOWN * 1.05)
        td = T("密度（λ = 1）", 22, MUTED).next_to(axd, UP, buff=0.1)
        th = T("风险率", 22, MUTED).next_to(axh, UP, buff=0.1)
        self.play(Create(axd), Create(axh), FadeIn(td), FadeIn(th), Write(hf), run_time=1.2)
        specs = [(0.5, PLUM, "递减：早期失效"), (1.0, INK, "恒定：随机失效"), (3.0, BRICK, "递增：老化磨损")]
        rows = VGroup()
        for k, c, name in specs:
            rows.add(VGroup(Line(ORIGIN, RIGHT * 0.4, color=c, stroke_width=3.5), M(f"k={k:g}", 24, c),
                            T(name, 18, c)).arrange(RIGHT, buff=0.12))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(axh.c2p(1.95, 3.2))
        for (k, c, name), row in zip(specs, rows):
            dcv = curve(axd, lambda x, k=k: weibull_pdf(x, k), 0.004, 2.6, c, width=4, ymax=1.58)
            hcv = curve(axh, lambda x, k=k: weibull_h(x, k), 0.004, 2.6, c, width=4, ymax=4.15)
            self.play(Create(dcv), Create(hcv), FadeIn(row), run_time=1.6)
            self.wait(0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, eh3)], run_time=0.6)

        # --- 柯西 ---
        self.seg(4)
        eh4 = entry_header("柯西分布", "Cauchy", r"X\sim\mathrm{Cauchy}(x_0,\gamma)", BRICK)
        self.play(FadeTransform(eh3, eh4), run_time=0.7)
        axc = axes([-6, 6.3, 2], [0, 0.44, 0.2], 8.2, 4.0, xnums=[-6, -4, -2, 0, 2, 4, 6], ynums=[0.2, 0.4],
                   ydec=1, xlabel="x", ylabel="f(x)")
        axc.move_to(LEFT * 2.4 + DOWN * 0.6)
        nc = DashedVMobject(curve(axc, norm_pdf, -6, 6, INK, width=3), num_dashes=60)
        cc = curve(axc, cauchy_pdf, -6, 6, BRICK, width=4.5)
        tails = VGroup(area(axc, cauchy_pdf, -6, -2.5, BRICK, opacity=0.3), area(axc, cauchy_pdf, 2.5, 6, BRICK,
                                                                               opacity=0.3))
        lgc = legend([(BRICK, "柯西"), (INK, "$N(0,1)$", "dash")]).move_to(axc.c2p(4.2, 0.36))
        colc = VGroup(M(r"\mathbb{E}|X|=\infty", 38), T("均值、方差都不存在", 24, INK),
                      T("中位数 x₀、四分位距 2γ", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        colc.move_to(RIGHT * 4.6 + UP * 0.5)
        self.play(Create(axc), run_time=0.6)
        self.play(Create(nc), Create(cc), FadeIn(lgc), run_time=1.4)
        self.play(FadeIn(tails), FadeIn(colc[0]), run_time=0.8)
        self.play(FadeIn(colc[1:]), run_time=0.6)
        self.catch_up()

        # --- 样本均值轨迹 ---
        self.seg(5)
        self.play(FadeOut(VGroup(axc, nc, cc, tails, lgc, colc)), run_time=0.5)
        axm = axes([0, 3.08, 1], [-4, 4.3, 2], 9.4, 4.2,
                   xnums=[(0, r"10^0"), (1, r"10^1"), (2, r"10^2"), (3, r"10^3")], ynums=[-4, -2, 0, 2, 4],
                   ylabel=r"\bar X_n", tips=False, xnums_at=-4)
        axm.move_to(LEFT * 1.75 + DOWN * 0.5)
        xl = T("样本量 n（对数刻度）", 20, MUTED).next_to(axm, DOWN, buff=0.45)
        zero = DashedLine(axm.c2p(0, 0), axm.c2p(3.05, 0), color=GREY, stroke_width=1.5, dash_length=0.05)
        rng = np.random.default_rng(245)
        c_ = rng.standard_cauchy(1000)
        z_ = rng.standard_normal(1000)
        n_ = np.arange(1, 1001)
        mc, mz = np.cumsum(c_) / n_, np.cumsum(z_) / n_
        pc = VMobject(stroke_color=BRICK, stroke_width=3).set_points_as_corners(
            [axm.c2p(math.log10(n), float(np.clip(v, -4, 4))) for n, v in zip(n_, mc)])
        pz = VMobject(stroke_color=INK, stroke_width=3.5).set_points_as_corners(
            [axm.c2p(math.log10(n), float(np.clip(v, -4, 4))) for n, v in zip(n_, mz)])
        lgm = legend([(BRICK, "柯西"), (INK, "正态")]).move_to(axm.c2p(0.45, -3.0))
        self.play(Create(axm), FadeIn(xl), Create(zero), FadeIn(lgm), run_time=0.9)
        self.play(Create(pz), Create(pc), run_time=5.5, rate_func=linear)
        res = VGroup(M(r"\bar X_n\sim\mathrm{Cauchy}(x_0,\gamma)", 32),
                     T("不随 n 集中：大数定律失效", 22, BRICK, bold=True),
                     T("“方差有限”是否必要？第一个反例", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        res.to_edge(RIGHT, buff=0.35).set_y(0.9)
        self.play(FadeIn(res[0]), run_time=0.8)
        self.play(FadeIn(res[1]), run_time=0.6)
        self.wait(max(0.2, self.durs[5] * 0.78 - 8.8))
        self.play(FadeIn(res[2]), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(axm, xl, zero, pc, pz, lgm, res, eh4, hdr)), run_time=0.7)
