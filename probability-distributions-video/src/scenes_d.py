# -*- coding: utf-8 -*-
"""第四章抽样分布（S06）和第五章多元正态（S07）。"""
from common import *  # noqa: F401,F403


class S06(VScene):
    SID = "S06"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "04", hold=1.2)
        iid = mixed("设 ", "$Z,Z_1,\\dots,Z_k\\overset{\\text{iid}}{\\sim}N(0,1)$", size=32).move_to(UP * 1.2)
        chips = VGroup()
        for name, tex in (("卡方", r"\chi^2_k"), ("t 分布", r"t_\nu"), ("F 分布", r"F(d_1,d_2)")):
            lab = VGroup(T(name, 26, INK, bold=True), M(tex, 34, INDIGO)).arrange(DOWN, buff=0.15)
            box = RoundedRectangle(corner_radius=0.1, width=2.8, height=1.5, fill_color=tint(INDIGO, 0.12),
                                   fill_opacity=1, stroke_color=INDIGO, stroke_width=2)
            chips.add(VGroup(box, lab.move_to(box)))
        chips.arrange(RIGHT, buff=0.6).move_to(DOWN * 0.5)
        use = T("区间估计与假设检验的基础", 24, MUTED).next_to(chips, DOWN, buff=0.45)
        self.play(FadeIn(iid, shift=DOWN * 0.2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in chips], lag_ratio=0.3), run_time=1.4)
        self.play(FadeIn(use), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(chips, use)), iid.animate.scale(0.75).to_corner(UL, buff=0.32).shift(DOWN * 0.0),
                  run_time=0.7)
        self.play(FadeOut(iid), run_time=0.3)

        # --- 卡方 ---
        self.seg(1)
        eh = entry_header("卡方分布", "Chi-squared", r"X\sim\chi^2_k", INDIGO)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.7)
        ax = axes([0, 14.3, 1], [0, 0.55, 0.2], 8.6, 4.2, xnums=[0, 2, 4, 6, 8, 10, 12, 14], ynums=[0.2, 0.4],
                  ydec=1, xlabel="x", ylabel="f(x)")
        ax.move_to(LEFT * 2.1 + DOWN * 0.55)
        k = ValueTracker(1.0)
        cv = always_redraw(lambda: curve(ax, lambda x: chi2_pdf(x, k.get_value()), 0.004, 14.2, INDIGO, width=4.5,
                                         ymax=0.53))
        kl = VGroup(M("k=", 36), DecimalNumber(1, num_decimal_places=1, font_size=36, color=INK)).arrange(RIGHT,
                                                                                                    buff=0.1)
        kl.move_to(ax.c2p(10.5, 0.45))
        kl[1].add_updater(lambda m: m.set_value(k.get_value()))
        fx = M(r"X=Z_1^2+\cdots+Z_k^2", 36)
        cards = VGroup(mixed("$\\mathbb{E}X=k,\\ \\ \\operatorname{Var}X=2k$", size=28),
                       mixed("就是伽马：", "$\\chi^2_k=\\Gamma(\\tfrac k2,\\tfrac12)$", size=26),
                       mixed("$k\\to\\infty$", " 时趋于正态", size=26)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        col = VGroup(fx, cards).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(RIGHT * 4.3 + UP * 0.6)
        if col.get_right()[0] > 6.95:
            col.shift(LEFT * (col.get_right()[0] - 6.95))
        self.play(Create(ax), Write(fx), run_time=1.2)
        self.play(Create(cv), FadeIn(kl), run_time=1.0)
        traces = VGroup()
        for i, v in enumerate((2, 3, 4, 6, 9)):
            traces.add(curve(ax, lambda x, kk=k.get_value(): chi2_pdf(x, kk), 0.004, 14.2, INDIGO, width=2,
                             ymax=0.53).set_stroke(opacity=0.22))
            self.add(traces[-1])
            anims = [k.animate.set_value(v)]
            if i < 3:
                anims.append(FadeIn(cards[i], shift=RIGHT * 0.2))
            self.play(*anims, run_time=1.4, rate_func=smooth)
            self.wait(0.35)
        self.catch_up()
        kl[1].clear_updaters()

        # --- 样本方差 ---
        self.seg(2)
        self.play(FadeOut(VGroup(ax, cv, traces, kl, col)), run_time=0.6)
        sv = MathTex(r"\frac{(n-1)S^2}{\sigma^2}\ \sim\ \chi^2_{", r"n-1", r"}", font_size=72)
        sv.move_to(UP * 0.6)
        hl = SurroundingRectangle(sv[1], color=GOLD, buff=0.08, stroke_width=3, corner_radius=0.06)
        why = T("估计 X̄ 用掉了一个自由度", 28, GOLD).next_to(sv, DOWN, buff=0.6)
        ind = mixed("并且 ", "$\\bar X$", " 与 ", "$S^2$", " 独立（只有正态总体才这样）", size=24, color=MUTED)
        ind.next_to(why, DOWN, buff=0.35)
        self.play(Write(sv), run_time=1.8)
        self.play(Create(hl), sv[1].animate.set_color(GOLD), run_time=0.8)
        self.play(FadeIn(why, shift=UP * 0.2), run_time=0.7)
        self.wait(max(0.2, self.durs[2] * 0.7 - 3.9))
        self.play(FadeIn(ind), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(sv, hl, why, ind)), run_time=0.6)

        # --- t 分布 ---
        self.seg(3)
        eh2 = entry_header("学生 t 分布", "Student's t", r"T\sim t_\nu", INDIGO)
        self.play(FadeTransform(eh, eh2), run_time=0.7)
        ax2 = axes([-5, 5.3, 1], [0, 0.43, 0.1], 8.6, 4.2, xnums=[-4, -2, 0, 2, 4], ynums=[0.1, 0.2, 0.3, 0.4],
                   ydec=1, xlabel="t", ylabel="f(t)")
        ax2.move_to(LEFT * 2.1 + DOWN * 0.55)
        ft = mixed("$T=\\dfrac{Z}{\\sqrt{V/\\nu}}$", "，", "$V\\sim\\chi^2_\\nu$", " 与 ", "$Z$", " 独立", size=26)
        ft.move_to(RIGHT * 4.0 + UP * 1.75)
        if ft.get_right()[0] > 6.95:
            ft.shift(LEFT * (ft.get_right()[0] - 6.95))
        nc = DashedVMobject(curve(ax2, norm_pdf, -5, 5, INK, width=3), num_dashes=60)
        self.play(Create(ax2), Write(ft), run_time=1.3)
        self.play(Create(nc), run_time=0.8)
        specs = [(1, PLUM, r"\nu=1"), (2, TEAL, r"\nu=2"), (5, BRICK, r"\nu=5"), (30, GOLD, r"\nu=30")]
        lgs = legend([(c, "$" + s + "$") for _, c, s in specs] + [(INK, "$N(0,1)$", "dash")], size=18)
        lgs.move_to(ax2.c2p(-3.7, 0.32))
        self.play(FadeIn(lgs[-1]), run_time=0.3)
        for (v, c, s), row in zip(specs, lgs):
            self.play(Create(curve(ax2, lambda x, v=v: t_pdf(x, v), -5, 5, c, width=3.5)), FadeIn(row), run_time=1.1)
        notes = VGroup(mixed("$\\nu=1$", "：柯西", size=24),
                       mixed("$\\nu\\to\\infty$", "：", "$N(0,1)$", size=24),
                       T("自由度越小，峰越低、尾越厚", 24),
                       mixed("$\\dfrac{\\bar X-\\mu}{S/\\sqrt n}\\sim t_{n-1}$", "：方差未知时的", size=24),
                       T("区间估计与 t 检验", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        notes[4].shift(RIGHT * 0.0)
        notes.move_to(RIGHT * 4.35 + DOWN * 0.15)
        if notes.get_right()[0] > 6.95:
            notes.shift(LEFT * (notes.get_right()[0] - 6.95))
        self.play(LaggedStart(*[FadeIn(n_, shift=RIGHT * 0.2) for n_ in notes[:3]], lag_ratio=0.5), run_time=2.2)
        self.wait(max(0.2, self.durs[3] * 0.72 - 9.5))
        self.play(FadeIn(notes[3:], shift=RIGHT * 0.2), run_time=0.9)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, eh2)], run_time=0.6)

        # --- F 分布 ---
        self.seg(4)
        eh3 = entry_header("F 分布", "Fisher–Snedecor F", r"X\sim F(d_1,d_2)", INDIGO)
        self.play(FadeTransform(eh2, eh3), run_time=0.7)
        ax3 = axes([0, 4.15, 0.5], [0, 1.6, 0.5], 8.6, 4.2, xnums=[0, 1, 2, 3, 4], ynums=[0.5, 1, 1.5],
                   xlabel="x", ylabel="f(x)")
        ax3.move_to(LEFT * 2.1 + DOWN * 0.55)
        fF = mixed("$X=\\dfrac{U/d_1}{V/d_2}$", "，", "$U\\sim\\chi^2_{d_1},\\ V\\sim\\chi^2_{d_2}$", " 独立", size=26)
        fF.move_to(RIGHT * 3.6 + UP * 1.75)
        if fF.get_right()[0] > 6.95:
            fF.shift(LEFT * (fF.get_right()[0] - 6.95))
        self.play(Create(ax3), Write(fF), run_time=1.2)
        specs = [((1, 1), PLUM), ((2, 5), TEAL), ((5, 2), BRICK), ((10, 20), GOLD), ((50, 50), INDIGO)]
        cs = VGroup(*[curve(ax3, lambda x, d=d: f_pdf(x, *d), 0.004, 4.1, c, width=3.5, ymax=1.58) for d, c in specs])
        lg = legend([(c, f"$F({d[0]},{d[1]})$") for d, c in specs], size=18).move_to(ax3.c2p(2.4, 1.25))
        self.play(LaggedStart(*[Create(c) for c in cs], lag_ratio=0.25), FadeIn(lg), run_time=2.4)
        notes = VGroup(T("比较两个正态总体的方差", 24), T("方差分析、回归的整体显著性", 24),
                       mixed("$t_\\nu^2=F(1,\\nu)$", size=30), mixed("$1/X\\sim F(d_2,d_1)$", size=28))
        notes.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(RIGHT * 4.6 + DOWN * 0.3)
        if notes.get_right()[0] > 6.95:
            notes.shift(LEFT * (notes.get_right()[0] - 6.95))
        self.play(LaggedStart(*[FadeIn(n_, shift=RIGHT * 0.2) for n_ in notes[:2]], lag_ratio=0.5), run_time=1.4)
        self.wait(max(0.2, self.durs[4] * 0.68 - 5.8))
        hl = SurroundingRectangle(notes[2], color=GOLD, buff=0.1, stroke_width=3, corner_radius=0.06)
        self.play(FadeIn(notes[2:]), Create(hl), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(ax3, fF, cs, lg, notes, hl, eh3, hdr)), run_time=0.7)


class S07(VScene):
    SID = "S07"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "05")

        # --- 等高椭圆与点云 ---
        self.seg(1)
        R = 3.3
        ax = Axes(x_range=[-R, R, 1], y_range=[-R, R, 1], x_length=5.5, y_length=5.5, tips=True,
                  axis_config={"color": AXIS, "stroke_width": 2, "include_ticks": False, "tip_width": 0.12,
                               "tip_height": 0.12})
        ax.move_to(LEFT * 3.4 + DOWN * 0.25)
        x1l = M("x_1", 28).next_to(ax.x_axis.get_end(), DOWN, buff=0.1)
        x2l = M("x_2", 28).next_to(ax.y_axis.get_end(), RIGHT, buff=0.1)
        u = ax.c2p(1, 0)[0] - ax.c2p(0, 0)[0]
        O = ax.c2p(0, 0)
        rho = ValueTracker(0.5)
        Z = np.random.default_rng(11).standard_normal((360, 2))

        def cloud():
            r = rho.get_value()
            s = math.sqrt(max(1 - r * r, 1e-6))
            g = VGroup()
            for z1, z2 in Z:
                x, y = z1, r * z1 + s * z2
                if abs(x) < R - 0.1 and abs(y) < R - 0.1:
                    g.add(Dot(ax.c2p(x, y), radius=0.028, color=INDIGO, fill_opacity=0.55))
            return g

        def ellipses():
            r = rho.get_value()
            g = VGroup()
            for c, op in ((2.5, 0.10), (1.6, 0.16), (0.8, 0.24)):
                e = Ellipse(width=2 * c * math.sqrt(1 + r) * u, height=2 * c * math.sqrt(max(1 - r, 1e-4)) * u,
                            stroke_color=INDIGO, stroke_width=2.2, fill_color=INDIGO, fill_opacity=op)
                e.rotate(PI / 4).move_to(O)
                g.add(e)
            return g

        def eigs():
            r = rho.get_value()
            v1 = np.array([1, 1, 0]) / math.sqrt(2)
            v2 = np.array([-1, 1, 0]) / math.sqrt(2)
            a1 = Arrow(O, O + v1 * 1.6 * math.sqrt(1 + r) * u, buff=0, color=BRICK, stroke_width=4,
                       max_tip_length_to_length_ratio=0.15)
            a2 = Arrow(O, O + v2 * 1.6 * math.sqrt(max(1 - r, 1e-4)) * u, buff=0, color=BRICK, stroke_width=4,
                       max_tip_length_to_length_ratio=0.25)
            return VGroup(a1, a2)

        C = always_redraw(cloud)
        E = always_redraw(ellipses)
        V = always_redraw(eigs)
        self.play(Create(ax), FadeIn(x1l), FadeIn(x2l), run_time=0.8)
        self.play(FadeIn(C, lag_ratio=0.02), run_time=1.4)
        self.add(E, C)
        self.play(FadeIn(E), run_time=1.0)
        self.play(FadeIn(V), run_time=0.7)
        fx = M(r"f(\boldsymbol x)=\frac{\exp\!\big(-\frac12(\boldsymbol x-\boldsymbol\mu)^{\!\top}\Sigma^{-1}"
               r"(\boldsymbol x-\boldsymbol\mu)\big)}{(2\pi)^{d/2}|\Sigma|^{1/2}}", 30)
        lv = mixed("等高线 ", "$(\\boldsymbol x-\\boldsymbol\\mu)^{\\!\\top}\\Sigma^{-1}(\\boldsymbol x-\\boldsymbol\\mu)=c^2$",
                   " 是椭圆", size=22)
        ax_n = mixed("主轴沿 ", "$\\Sigma$", " 的特征向量，半轴 ", "$c\\sqrt{\\lambda_i}$", size=22)
        col = VGroup(fx, lv, ax_n).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(RIGHT * 3.5 + UP * 1.25)
        if col.get_right()[0] > 6.95:
            col.shift(LEFT * (col.get_right()[0] - 6.95))
        self.play(FadeIn(fx), run_time=0.8)
        self.play(FadeIn(lv, shift=RIGHT * 0.2), run_time=0.7)
        self.play(FadeIn(ax_n, shift=RIGHT * 0.2), run_time=0.7)
        self.catch_up()

        # --- ρ 变化 ---
        self.seg(2)
        rl = VGroup(M(r"\rho=", 40), DecimalNumber(0.5, num_decimal_places=2, font_size=40, color=INK))
        rl.arrange(RIGHT, buff=0.1).move_to(RIGHT * 2.0 + DOWN * 0.5)
        rl[1].add_updater(lambda m: m.set_value(rho.get_value()))
        self.play(FadeIn(rl), run_time=0.4)
        for v, t_ in ((0.0, 1.4), (0.7, 1.6), (-0.6, 2.0), (0.7, 2.0)):
            self.play(rho.animate.set_value(v), run_time=t_, rate_func=smooth)
            self.wait(0.15)
        ind = VGroup(mixed("联合正态：", "不相关 ", "$\\Longleftrightarrow$", " 独立", size=26),
                     T("（对一般分布不成立）", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        indb = note_box(ind, INDIGO, pad=0.22).next_to(rl, DOWN, buff=0.45, aligned_edge=LEFT)
        self.play(FadeIn(indb, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        rl[1].clear_updaters()

        # --- 条件分布与回归线 ---
        self.seg(3)
        self.play(FadeOut(VGroup(rl, indb, col)), C.animate.set_opacity(0.25), V.animate.set_opacity(0), run_time=0.7)
        self.remove(V)
        r = 0.7
        main = DashedLine(ax.c2p(-R + 0.2, -R + 0.2), ax.c2p(R - 0.2, R - 0.2), color=GREY, stroke_width=2,
                          dash_length=0.08)
        reg = Line(ax.c2p(-R + 0.1, r * (-R + 0.1)), ax.c2p(R - 0.1, r * (R - 0.1)), color=BRICK, stroke_width=4)
        keys = VGroup(
            VGroup(DashedLine(ORIGIN, RIGHT * 0.5, color=GREY, stroke_width=2.5, dash_length=0.08),
                   mixed("主轴 ", "$x_2=x_1$", size=22, color=MUTED)).arrange(RIGHT, buff=0.15),
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=BRICK, stroke_width=4),
                   mixed("回归线 ", "$x_2=\\rho x_1$", size=22, color=BRICK)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(RIGHT * 2.2 + UP * 2.35, aligned_edge=LEFT)
        main_l, reg_l = keys
        self.play(Create(main), FadeIn(main_l), run_time=0.9)
        self.play(Create(reg), FadeIn(reg_l), run_time=0.9)
        x0 = 1.5
        vl = DashedLine(ax.c2p(x0, -R + 0.1), ax.c2p(x0, R - 0.1), color=GOLD, stroke_width=2, dash_length=0.06)
        m_, s_ = r * x0, math.sqrt(1 - r * r)
        ys = np.linspace(m_ - 3.2 * s_, m_ + 3.2 * s_, 120)
        bump = VMobject(stroke_color=GOLD, stroke_width=4).set_points_as_corners(
            [ax.c2p(x0, y) + RIGHT * 1.15 * u * norm_pdf(y, m_, s_) / norm_pdf(0, 0, s_) for y in ys])
        dot = Dot(ax.c2p(x0, m_), radius=0.08, color=BRICK)
        self.play(Create(vl), run_time=0.6)
        self.play(Create(bump), FadeIn(dot, scale=1.5), run_time=1.2)
        cond = mixed("$X_2\\mid X_1=x_1\\ \\sim\\ N(\\rho x_1,\\ 1-\\rho^2)$", size=28)
        cond.move_to(RIGHT * 3.5 + UP * 1.4)
        reg_t = VGroup(T("回归线比主轴更平", 26, BRICK, bold=True), T("——这就是“向均值回归”", 24, INK))
        reg_t.arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(cond, DOWN, buff=0.6).align_to(cond, LEFT)
        gen = mixed("一般地：", "$\\boldsymbol\\mu_1+\\Sigma_{12}\\Sigma_{22}^{-1}(\\boldsymbol x_2-\\boldsymbol\\mu_2)$",
                    size=20, color=MUTED).next_to(reg_t, DOWN, buff=0.5).align_to(cond, LEFT)
        self.play(Write(cond), run_time=1.4)
        self.wait(max(0.2, self.durs[3] * 0.55 - 7.1))
        self.play(FadeIn(reg_t, shift=UP * 0.2), Indicate(reg, color=BRICK, scale_factor=1.0), run_time=1.0)
        self.play(FadeIn(gen), run_time=0.6)
        self.catch_up()

        # --- 等价定义与封闭性 ---
        self.seg(4)
        self.play(FadeOut(VGroup(cond, reg_t, gen)), run_time=0.5)
        d1 = VGroup(T("等价定义", 26, INDIGO, bold=True),
                    mixed("$\\boldsymbol X$", " 多元正态 ", "$\\Longleftrightarrow$", " 每个 ", "$\\boldsymbol a^{\\!\\top}\\boldsymbol X$",
                          " 都是一元正态", size=24)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        d2 = VGroup(T("仿射封闭", 26, INDIGO, bold=True),
                    mixed("$A\\boldsymbol X+\\boldsymbol b\\sim N(A\\boldsymbol\\mu+\\boldsymbol b,\\ A\\Sigma A^{\\!\\top})$",
                          size=24)).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cross = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(BRICK, 5).scale(0.14)
        d3 = VGroup(cross, mixed("各分量分别正态 ", "$\\not\\Rightarrow$", " 联合正态", size=24, color=BRICK)).arrange(
            RIGHT, buff=0.2)
        stack = VGroup(note_box(d1, INDIGO, pad=0.22), note_box(d2, INDIGO, pad=0.22), d3)
        stack.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to(RIGHT * 3.55 + UP * 0.2)
        if stack.get_right()[0] > 6.95:
            stack.shift(LEFT * (stack.get_right()[0] - 6.95))
        self.play(FadeIn(stack[0], shift=LEFT * 0.2), run_time=0.8)
        self.wait(max(0.2, self.durs[4] * 0.3 - 1.3))
        self.play(FadeIn(stack[1], shift=LEFT * 0.2), run_time=0.8)
        self.wait(max(0.2, self.durs[4] * 0.62 - self.durs[4] * 0.3 - 0.8))
        self.play(FadeIn(stack[2], shift=LEFT * 0.2), run_time=0.8)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
