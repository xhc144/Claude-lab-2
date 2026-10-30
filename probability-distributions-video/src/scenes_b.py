# -*- coding: utf-8 -*-
"""第二章：离散分布（S02 二项、几何、负二项、超几何；S03 泊松分布与泊松过程）。"""
from common import *  # noqa: F401,F403


def nb_pmf(r, p, k):
    if k < r:
        return 0.0
    return math.comb(k - 1, r - 1) * p ** r * (1 - p) ** (k - r)


def hyper_pmf(N, K, n, k):
    if k < max(0, n - N + K) or k > min(n, K):
        return 0.0
    return math.comb(K, k) * math.comb(N - K, n - k) / math.comb(N, n)


class S02(VScene):
    SID = "S02"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "02")

        # --- 二项分布条目 ---
        self.seg(1)
        eh = entry_header("伯努利分布与二项分布", "Bernoulli / Binomial", r"X\sim B(n,p)", TEAL)
        pl = param_line("$n\\in\\mathbb{N}_+,\\ p\\in[0,1]$", "$\\{0,1,\\dots,n\\}$")
        pl.next_to(eh, DOWN, buff=0.3).align_to(eh, LEFT).shift(RIGHT * 0.2)
        formula = M(r"P(X=k)=\binom{n}{k}p^k(1-p)^{n-k}", 50).move_to(UP * 0.85)
        cards = stat_cards([("期望", "np"), ("方差", "np(1-p)"), ("矩母函数", "(1-p+pe^t)^n")], TEAL, y=-0.75)
        struct = bullet("结构：", "$X$", " 等于 ", "$n$", " 个独立 ", "$B(1,p)$", " 示性变量之和；", "$n$", " 次独立试验的成功次数")
        struct.move_to(DOWN * 2.2)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.8)
        self.play(FadeIn(pl), Write(formula), run_time=1.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.25) for c in cards], lag_ratio=0.25), run_time=1.4)
        self.play(FadeIn(struct, shift=RIGHT * 0.3), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(pl, formula, cards, struct)), run_time=0.6)

        # --- p 变化：对称与偏斜 ---
        self.seg(2)
        ax = axes([0, 20.6, 1], [0, 0.3, 0.1], 8.4, 4.3, xnums=[0, 5, 10, 15, 20], ynums=[0.1, 0.2],
                  xlabel="k", ylabel="P(X=k)")
        ax.move_to(LEFT * 2.1 + DOWN * 0.55)
        p = ValueTracker(0.25)
        ks = list(range(21))
        st = always_redraw(lambda: stems(ax, ks, [binom_pmf(20, p.get_value(), k) for k in ks], TEAL))
        mean = always_redraw(lambda: DashedLine(ax.c2p(20 * p.get_value(), 0), ax.c2p(20 * p.get_value(), 0.27),
                                                color=GOLD, stroke_width=2, dash_length=0.06))
        plab = VGroup(M(r"n=20,\ \ p=", 34), DecimalNumber(0.25, num_decimal_places=2, font_size=34, color=INK))
        plab.arrange(RIGHT, buff=0.1).move_to(ax.c2p(4.2, 0.27))
        plab[1].add_updater(lambda m: m.set_value(p.get_value()))
        # 右上角小图：方差因子 p(1-p)
        ins = axes([0, 1.05, 0.5], [0, 0.3, 0.25], 3.4, 2.3, xnums=[0, 0.5, 1], ynums=[(0.25, r"\tfrac14")],
                   xlabel="p", num_size=20)
        ins.move_to(RIGHT * 4.6 + UP * 0.55)
        par = curve(ins, lambda x: x * (1 - x), 0, 1, INK, width=3)
        pd = always_redraw(lambda: Dot(ins.c2p(p.get_value(), p.get_value() * (1 - p.get_value())),
                                       radius=0.08, color=GOLD))
        ins_t = M(r"p(1-p)\le\tfrac14", 30).next_to(ins, DOWN, buff=0.35)
        self.play(Create(ax), run_time=0.9)
        self.play(FadeIn(st, lag_ratio=0.05), FadeIn(plab), Create(mean), run_time=1.0)
        self.play(FadeIn(ins), Create(par), FadeIn(pd), FadeIn(ins_t), run_time=1.0)
        self.play(p.animate.set_value(0.7), run_time=3.2, rate_func=smooth)
        self.play(p.animate.set_value(0.5), run_time=2.0, rate_func=smooth)
        sym = T("p = ½ 时对称", 24, GOLD).next_to(ax.c2p(10, 0.2), UP + RIGHT, buff=0.2)
        self.play(FadeIn(sym, shift=UP * 0.2), Indicate(pd, color=GOLD), run_time=1.0)
        self.catch_up()
        plab[1].clear_updaters()
        self.play(FadeOut(VGroup(st, mean, plab, ins, par, pd, ins_t, sym, ax)), run_time=0.6)

        # --- 正态近似 ---
        self.seg(3)
        ax2 = axes([0, 26.5, 1], [0, 0.17, 0.05], 8.6, 4.3, xnums=[0, 4, 8, 12, 16, 20, 24],
                   ynums=[0.05, 0.1, 0.15], ydec=2, xlabel="k", ylabel=T("概率 / 密度", 20, INK))
        ax2.move_to(LEFT * 2.0 + DOWN * 0.55)
        ks2 = list(range(27))
        bs = bars(ax2, ks2, [binom_pmf(30, 0.4, k) for k in ks2], TEAL, w=0.9, opacity=0.38)
        nc = curve(ax2, lambda x: norm_pdf(x, 12, math.sqrt(7.2)), 0, 26, BRICK, width=4.5)
        lg = legend([(TEAL, "$B(30,\\,0.4)$", "bar"), (BRICK, "$N(12,\\,7.2)$")]).move_to(ax2.c2p(22, 0.14))
        self.play(Create(ax2), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bs], lag_ratio=0.06), run_time=1.6)
        self.play(Create(nc), FadeIn(lg), run_time=1.6)
        dml = T("棣莫弗–拉普拉斯", 24, INK, bold=True)
        lim = M(r"\frac{X-np}{\sqrt{np(1-p)}}\xrightarrow{\ d\ }N(0,1)", 34)
        cc_t = T("连续性修正", 24, INK, bold=True)
        cc = M(r"P(X\le k)\approx\Phi\!\left(\frac{k+0.5-np}{\sqrt{np(1-p)}}\right)", 30)
        col = VGroup(dml, lim, cc_t, cc).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        col[2].shift(DOWN * 0.2)
        col[3].shift(DOWN * 0.2)
        colb = note_box(col, BRICK, pad=0.25).move_to(DOWN * 0.3).to_edge(RIGHT, buff=0.35)
        self.play(FadeIn(colb[:2]), FadeIn(dml), Write(lim), run_time=1.4)
        self.wait(max(0.2, self.durs[3] * 0.55 - 5.4))
        self.play(FadeIn(cc_t), Write(cc), run_time=1.5)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, bs, nc, lg, colb)), run_time=0.6)

        # --- 几何分布 ---
        self.seg(4)
        eh2 = entry_header("几何分布", "Geometric", r"X\sim \mathrm{Geo}(p)", TEAL)
        self.play(FadeTransform(eh, eh2), run_time=0.8)
        ax3 = axes([0, 15.8, 1], [0, 0.34, 0.1], 8.2, 4.1, xnums=[1, 4, 8, 12, 15], ynums=[0.1, 0.2, 0.3],
                   xlabel="k", ylabel="P(X=k)")
        ax3.move_to(LEFT * 2.3 + DOWN * 0.55)
        kg = list(range(1, 16))
        pg = [0.7 ** (k - 1) * 0.3 for k in kg]
        st3 = stems(ax3, kg, pg, TEAL)
        f3 = M(r"P(X=k)=(1-p)^{k-1}p", 38)
        e3 = M(r"\mathbb{E}X=\frac1p", 38)
        t3 = T("首次成功所需的试验次数", 24, MUTED)
        col3 = VGroup(t3, f3, e3).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(RIGHT * 4.0 + UP * 0.7)
        pl3 = M(r"p=0.3", 30, TEAL).move_to(ax3.c2p(12, 0.28))
        self.play(Create(ax3), FadeIn(pl3), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(s, DOWN) for s in st3], lag_ratio=0.08), run_time=1.6)
        self.play(LaggedStart(FadeIn(t3), Write(f3), FadeIn(e3), lag_ratio=0.4), run_time=1.8)
        self.catch_up()

        # --- 无记忆性 ---
        self.seg(5)
        ghost = bars(ax3, kg, pg, TEAL, w=0.42, opacity=0.35, stroke=1.2)
        cut = DashedLine(ax3.c2p(3.5, 0), ax3.c2p(3.5, 0.33), color=GOLD, stroke_width=3, dash_length=0.08)
        cut_t = M(r"X>3", 28, GOLD).next_to(cut, UP, buff=0.08)
        self.play(FadeIn(ghost), Create(cut), FadeIn(cut_t), *[st3[i].animate.set_color(GREY) for i in range(3)],
                  run_time=1.0)
        self.play(FadeOut(st3[:3], shift=DOWN * 0.3), run_time=0.7)
        moved = VGroup()
        for k, s in zip(kg[3:], st3[3:]):
            tgt = stems(ax3, [k - 3], [0.7 ** (k - 1) * 0.3 / 0.343], BRICK, dot_r=0.075)[0]
            moved.add(tgt)
        self.play(*[Transform(s, m) for s, m in zip(st3[3:], moved)], FadeOut(cut), FadeOut(cut_t),
                  run_time=2.2, rate_func=smooth)
        lg3 = legend([(TEAL, "原分布", "bar"), (BRICK, "条件分布", "dot")]).move_to(ax3.c2p(12.5, 0.27))
        mem = M(r"P(X>m+n\mid X>m)=P(X>n)", 30)
        mem_t = T("正整数值分布中唯一无记忆", 22, MUTED)
        memg = VGroup(mem, mem_t).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(col3, DOWN, buff=0.55)
        memg.align_to(col3, LEFT)
        self.play(FadeOut(pl3), FadeIn(lg3), Write(mem), run_time=1.4)
        self.play(FadeIn(mem_t), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(ax3, st3[3:], ghost, lg3, col3, memg)), run_time=0.6)

        # --- 负二项 ---
        self.seg(6)
        eh3 = entry_header("负二项分布", "Negative binomial / Pascal", r"X\sim \mathrm{NB}(r,p)", TEAL)
        self.play(FadeTransform(eh2, eh3), run_time=0.8)
        ax4 = axes([0, 41, 5], [0, 0.37, 0.1], 9.0, 4.0, xnums=[0, 5, 10, 15, 20, 25, 30, 35, 40],
                   ynums=[0.1, 0.2, 0.3], xlabel="k", ylabel="P(X=k)")
        ax4.move_to(LEFT * 1.8 + DOWN * 0.6)
        self.play(Create(ax4), run_time=0.8)
        series = VGroup()
        for r, c in ((1, INK), (3, TEAL), (6, BRICK)):
            ks4 = list(range(r, 41))
            pts = [ax4.c2p(k, nb_pmf(r, 0.35, k)) for k in ks4]
            ln = VMobject(stroke_color=c, stroke_width=3).set_points_as_corners(pts)
            ds = VGroup(*[Dot(q, radius=0.035, color=c) for q in pts])
            series.add(VGroup(ln, ds))
        lg4 = legend([(INK, "$r=1$"), (TEAL, "$r=3$"), (BRICK, "$r=6$")]).move_to(ax4.c2p(35, 0.17))
        self.play(FadeIn(lg4), run_time=0.4)
        for s in series:
            self.play(Create(s[0]), FadeIn(s[1], lag_ratio=0.05), run_time=1.3)
        f4 = M(r"P(X=k)=\binom{k-1}{r-1}p^r(1-p)^{k-r}", 32)
        b4a = bullet("$r$", " 个独立 ", "$\\mathrm{Geo}(p)$", " 之和", size=22)
        b4b = bullet("方差 > 均值的计数模型", size=22)
        col4 = VGroup(f4, b4a, b4b).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(RIGHT * 2.6 + UP * 1.35)
        self.play(FadeIn(f4), FadeIn(b4a, shift=RIGHT * 0.2), run_time=1.0)
        self.wait(max(0.2, self.durs[6] * 0.7 - 6.0))
        self.play(FadeIn(b4b, shift=RIGHT * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(ax4, series, lg4, col4)), run_time=0.6)

        # --- 超几何 ---
        self.seg(7)
        eh4 = entry_header("超几何分布", "Hypergeometric", r"X\sim H(N,K,n)", TEAL)
        self.play(FadeTransform(eh3, eh4), run_time=0.8)
        ax5 = axes([-0.7, 10.7, 1], [0, 0.36, 0.1], 7.4, 3.9, xnums=list(range(0, 11)), ynums=[0.1, 0.2, 0.3],
                   xlabel="k", ylabel="P(X=k)")
        ax5.move_to(LEFT * 2.75 + DOWN * 0.6)
        k5 = list(range(11))
        hb = bars(ax5, k5, [hyper_pmf(25, 10, 10, k) for k in k5], TEAL, w=0.36, opacity=0.5, offset=-0.19)
        bb = bars(ax5, k5, [binom_pmf(10, 0.4, k) for k in k5], GREY, w=0.36, opacity=0.35, offset=0.19)
        lg5 = legend([(TEAL, "$H(25,10,10)$", "bar"), (GREY, "$B(10,\\,0.4)$", "bar")]).move_to(ax5.c2p(8.6, 0.31))
        self.play(Create(ax5), FadeIn(lg5), run_time=0.8)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bb], lag_ratio=0.05), run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in hb], lag_ratio=0.05), run_time=1.0)
        var = MathTex(r"\operatorname{Var}X=n\frac{K}{N}\Big(1-\frac{K}{N}\Big)", r"\frac{N-n}{N-1}", font_size=34)
        var.move_to(RIGHT * 3.9 + UP * 1.1)
        hl = SurroundingRectangle(var[1], color=GOLD, buff=0.08, stroke_width=3, corner_radius=0.05)
        hl_t = T("有限总体修正 < 1", 22, GOLD).next_to(hl, DOWN, buff=0.15)
        self.play(Write(var), run_time=1.4)
        self.play(Create(hl), FadeIn(hl_t), run_time=0.8)
        lim5 = mixed("$N\\to\\infty,\\ K/N\\to p$", " 时 ", "$H\\to B(n,p)$", size=24)
        lim5b = note_box(lim5, TEAL, pad=0.22).next_to(hl_t, DOWN, buff=0.6)
        lim5b.set_x(3.9)
        self.wait(max(0.2, self.durs[7] * 0.62 - 5.8))
        self.play(FadeIn(lim5b, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(ax5, hb, bb, lg5, var, hl, hl_t, lim5b, eh4, hdr)), run_time=0.8)


class S03(VScene):
    SID = "S03"

    def construct(self):
        hdr = running_header("02")
        self.add(hdr)

        # --- 泊松分布条目 ---
        self.seg(0)
        eh = entry_header("泊松分布", "Poisson", r"X\sim P(\lambda)", TEAL)
        pl = param_line("$\\lambda>0$", "$\\{0,1,2,\\dots\\}$")
        pl.next_to(eh, DOWN, buff=0.3).align_to(eh, LEFT).shift(RIGHT * 0.2)
        formula = M(r"P(X=k)=e^{-\lambda}\frac{\lambda^k}{k!}", 54).move_to(UP * 0.8)
        cards = stat_cards([("期望", r"\lambda"), ("方差", r"\lambda"), ("矩母函数", r"\exp\big(\lambda(e^t-1)\big)")],
                           TEAL, y=-0.9)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.8)
        self.play(FadeIn(pl), Write(formula), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.25) for c in cards], lag_ratio=0.25), run_time=1.3)
        eq = M(r"=", 60, GOLD).move_to((cards[0].get_right() + cards[1].get_left()) / 2)
        hl = VGroup(*[SurroundingRectangle(c, color=GOLD, buff=0.06, corner_radius=0.1, stroke_width=3)
                      for c in cards[:2]])
        tip = T("检验计数数据：先看均值是否等于方差", 24, INK).move_to(DOWN * 2.3)
        self.wait(max(0.2, self.durs[0] * 0.35 - 3.6))
        self.play(Create(hl), FadeIn(eq, scale=1.5), run_time=1.0)
        self.play(FadeIn(tip, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(pl, formula, cards, hl, eq, tip)), run_time=0.6)

        # --- λ 变化 ---
        self.seg(1)
        ax = axes([0, 21, 1], [0, 0.4, 0.1], 9.6, 4.2, xnums=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                  ynums=[0.1, 0.2, 0.3], xlabel="k", ylabel="P(X=k)")
        ax.move_to(LEFT * 1.2 + DOWN * 0.55)
        lam = ValueTracker(1.0)
        ks = list(range(21))
        st = always_redraw(lambda: stems(ax, ks, [poisson_pmf(lam.get_value(), k) for k in ks], TEAL))
        sd_band = always_redraw(lambda: self._sd_band(ax, lam.get_value()))
        ll = VGroup(M(r"\lambda=", 36), DecimalNumber(1.0, num_decimal_places=1, font_size=36, color=INK))
        ll.arrange(RIGHT, buff=0.1).move_to(ax.c2p(16.5, 0.34))
        ll[1].add_updater(lambda m: m.set_value(lam.get_value()))
        self.play(Create(ax), run_time=0.8)
        self.play(FadeIn(st), FadeIn(ll), FadeIn(sd_band), run_time=0.8)
        self.play(lam.animate.set_value(4), run_time=2.4, rate_func=smooth)
        self.play(lam.animate.set_value(10), run_time=2.6, rate_func=smooth)
        note = mixed("标准差 ", "$\\sqrt{\\lambda}$", "；", "$\\lambda\\to\\infty$", " 时 ",
                     "$\\frac{X-\\lambda}{\\sqrt\\lambda}\\xrightarrow{d}N(0,1)$", size=22)
        note.move_to(ax.c2p(15.2, 0.255))
        self.play(FadeIn(note, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        ll[1].clear_updaters()
        self.play(FadeOut(VGroup(ax, st, sd_band, ll, note)), run_time=0.6)

        # --- 稀有事件极限 ---
        self.seg(2)
        ax2 = axes([-0.7, 10.7, 1], [0, 0.34, 0.1], 8.4, 4.0, xnums=list(range(11)), ynums=[0.1, 0.2, 0.3],
                   xlabel="k", ylabel="P(X=k)")
        ax2.move_to(LEFT * 2.2 + DOWN * 0.6)
        k2 = list(range(11))
        target = bars(ax2, k2, [poisson_pmf(3, k) for k in k2], TEAL, w=0.36, opacity=0.55, offset=0.19)
        specs = [(6, 0.5, r"B(6,\tfrac12)"), (15, 0.2, r"B(15,\,0.2)"), (100, 0.03, r"B(100,\,0.03)")]
        bb = bars(ax2, k2, [binom_pmf(6, 0.5, k) for k in k2], GREY, w=0.36, opacity=0.4, offset=-0.19)
        lab = M(specs[0][2], 36, MUTED)
        vs = VGroup(lab, M(r"\longrightarrow", 36, INK), M(r"P(3)", 36, TEAL)).arrange(RIGHT, buff=0.25)
        vs.move_to(RIGHT * 4.3 + UP * 1.3)
        self.play(Create(ax2), FadeIn(target), run_time=0.9)
        self.play(FadeIn(bb), FadeIn(vs), run_time=0.8)
        for n_, p_, s_ in specs[1:]:
            nb = bars(ax2, k2, [binom_pmf(n_, p_, k) for k in k2], GREY, w=0.36, opacity=0.4, offset=-0.19)
            nl = M(s_, 36, MUTED).move_to(lab, aligned_edge=RIGHT)
            self.play(Transform(bb, nb), Transform(lab, nl), run_time=1.5)
            self.wait(0.4)
        rule = mixed("$n\\to\\infty,\\ np_n\\to\\lambda$", "：", "$B(n,p_n)\\to P(\\lambda)$", size=24)
        rb = note_box(rule, TEAL, pad=0.22).next_to(vs, DOWN, buff=0.6)
        rb.set_x(4.3)
        lc = M(r"\textstyle\sum_k\big|B(n,p)\{k\}-P(np)\{k\}\big|\le 2np^2", 26, MUTED).next_to(rb, DOWN, buff=0.35)
        self.play(FadeIn(rb, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(lc), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, target, bb, vs, rb, lc, eh)), run_time=0.6)

        # --- 泊松过程 ---
        self.seg(3)
        ev = [0.35, 1.45, 1.85, 3.15, 3.65, 5.4, 5.95, 7.55]
        cax = axes([0, 10.3, 1], [0, 8.6, 2], 12.0, 3.5, xnums=(), ynums=[2, 4, 6, 8], xlabel=None,
                   ylabel="N(t)")
        cax.move_to(UP * 0.85)
        tl_y = -1.7
        x0 = cax.c2p(0, 0)[0]
        xu = cax.c2p(1, 0)[0] - x0
        tline = Arrow([x0 - 0.1, tl_y, 0], [x0 + 10.4 * xu, tl_y, 0], buff=0, color=AXIS, stroke_width=2,
                      max_tip_length_to_length_ratio=0.015)
        tl_lab = M("t", 28).next_to(tline, RIGHT, buff=0.1)
        zero = M("0", 22, MUTED).next_to([x0, tl_y, 0], DOWN, buff=0.12)
        t = ValueTracker(0)

        def path():
            g = VGroup()
            pts = [0] + [e for e in ev if e <= t.get_value()]
            for i, a in enumerate(pts):
                b = ev[i] if i < len(ev) and ev[i] <= t.get_value() else t.get_value()
                if i < len(pts) - 1:
                    b = pts[i + 1]
                else:
                    b = t.get_value()
                if b > a:
                    g.add(Line(cax.c2p(a, i), cax.c2p(b, i), color=BRICK, stroke_width=4))
                if i > 0:
                    g.add(Dot(cax.c2p(a, i), radius=0.07, color=BRICK))
                    g.add(Circle(radius=0.06, color=BRICK, stroke_width=2.5, fill_color=BG, fill_opacity=1)
                          .move_to(cax.c2p(a, i - 1)))
            return g

        def dots():
            g = VGroup()
            for e in ev:
                if e <= t.get_value():
                    g.add(Dot([x0 + e * xu, tl_y, 0], radius=0.09, color=TEAL))
                    g.add(DashedLine([x0 + e * xu, tl_y, 0], cax.c2p(e, 0), color=GREY, stroke_width=1.2,
                                     dash_length=0.05))
            return g

        P = always_redraw(path)
        D = always_redraw(dots)
        cursor = always_redraw(lambda: Line([x0 + t.get_value() * xu, tl_y - 0.2, 0],
                                            cax.c2p(t.get_value(), 8.4), color=GOLD, stroke_width=1.5,
                                            stroke_opacity=0.6))
        self.play(Create(cax), GrowArrow(tline), FadeIn(tl_lab), FadeIn(zero), run_time=1.0)
        self.add(P, D, cursor)
        self.play(t.animate.set_value(9.6), run_time=6.0, rate_func=linear)
        self.remove(cursor)
        braces = VGroup()
        for a, b, s in ((0, ev[0], "T_1"), (ev[0], ev[1], "T_2"), (ev[1], ev[2], "T_3")):
            br = BraceBetweenPoints([x0 + a * xu, tl_y - 0.15, 0], [x0 + b * xu, tl_y - 0.15, 0], DOWN,
                                    color=GOLD, buff=0.02)
            br.stretch_to_fit_height(0.15)
            braces.add(VGroup(br, M(s, 24, GOLD).next_to(br, DOWN, buff=0.06)))
        iid = M(r"T_i\overset{\text{iid}}{\sim}\mathrm{Exp}(\lambda)", 32, INK).move_to([x0 + 8.4 * xu, tl_y - 0.75, 0])
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in braces], lag_ratio=0.3), FadeIn(iid), run_time=1.4)
        self.catch_up()

        # --- 区间计数 ---
        self.seg(4)
        a_, b_ = 3.0, 6.6
        win = Rectangle(width=(b_ - a_) * xu, height=cax.c2p(0, 8.6)[1] - tl_y + 0.3, fill_color=TEAL,
                        fill_opacity=0.12, stroke_width=0)
        win.move_to([x0 + (a_ + b_) / 2 * xu, (cax.c2p(0, 8.6)[1] + tl_y - 0.3) / 2, 0])
        wl = mixed("区间 ", "$(3,\\,6.6]$", " 中 4 个事件，计数 ", "$\\sim P(3.6\\lambda)$", size=22, color=TEAL)
        wl.next_to(win, UP, buff=0.08)
        self.play(FadeIn(win), FadeIn(wl, shift=DOWN * 0.1), run_time=1.0)
        inside = [e for e in ev if a_ < e <= b_]
        self.play(LaggedStart(*[Flash([x0 + e * xu, tl_y, 0], color=TEAL, line_length=0.15, flash_radius=0.18)
                                for e in inside], lag_ratio=0.3), run_time=1.6)
        ind = T("不相交区间的计数相互独立", 22, MUTED).move_to(cax.c2p(8.6, 3.2))
        self.play(FadeIn(ind), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(cax, tline, tl_lab, zero, P, D, braces, iid, win, wl, ind)), run_time=0.7)

        # --- 可加性与稀疏化 ---
        self.seg(5)
        L, R = -4.2, 4.4

        def tline_at(y, c=AXIS):
            return Line([L, y, 0], [R, y, 0], color=c, stroke_width=2)

        rng = np.random.default_rng(3)
        e1 = np.sort(rng.uniform(0, 1, 9))
        e2 = np.sort(rng.uniform(0, 1, 7))
        y1, y2, y3 = 2.05, 1.05, -0.35
        l1, l2, l3 = tline_at(y1), tline_at(y2), tline_at(y3)
        lab1 = M(r"P(\lambda_1)", 28, TEAL).next_to(l1, LEFT, buff=0.2)
        lab2 = M(r"P(\lambda_2)", 28, BRICK).next_to(l2, LEFT, buff=0.2)
        d1 = VGroup(*[Dot([L + e * (R - L), y1, 0], radius=0.09, color=TEAL) for e in e1])
        d2 = VGroup(*[Dot([L + e * (R - L), y2, 0], radius=0.09, color=BRICK) for e in e2])
        self.play(Create(l1), Create(l2), FadeIn(lab1), FadeIn(lab2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(d, scale=1.6) for d in [*d1, *d2]], lag_ratio=0.06), run_time=1.2)
        lab3 = M(r"P(\lambda_1+\lambda_2)", 28, INK).next_to(l3, LEFT, buff=0.2)
        self.play(Create(l3), FadeIn(lab3), *[d.animate.set_y(y3) for d in [*d1, *d2]], run_time=1.4)
        sup = M(r"P(\lambda_1)+P(\lambda_2)=P(\lambda_1+\lambda_2)", 32).move_to(UP * 1.55 + RIGHT * 0.3)
        self.play(FadeOut(VGroup(l1, l2, lab1, lab2)), FadeIn(sup), run_time=0.9)
        allp = sorted([*d1, *d2], key=lambda d: d.get_x())
        keep = [i % 3 != 1 for i in range(len(allp))]
        y4 = -1.75
        l4 = tline_at(y4, GREY)
        drops = [d for d, k in zip(allp, keep) if not k]
        coin = T("每个点以概率 p 保留", 22, MUTED).next_to(l3, UP, buff=0.25).set_x(0)
        self.play(FadeIn(coin), run_time=0.6)
        self.play(Create(l4), *[d.animate.set_color(GREY).set_y(y4) for d in drops],
                  *[d.animate.set_color(GOLD) for d, k in zip(allp, keep) if k], run_time=1.3)
        k_lab = mixed("保留 ", "$\\sim P(\\lambda p)$", size=22, color=GOLD)
        d_lab = mixed("丢弃 ", "$\\sim P(\\lambda(1-p))$", size=22, color=MUTED)
        k_lab.next_to(l3, RIGHT, buff=0.15)
        d_lab.next_to(l4, RIGHT, buff=0.15)
        k_lab.set_x(R - k_lab.width / 2).shift(UP * 0.4)
        d_lab.set_x(R - d_lab.width / 2).shift(UP * 0.4)
        indep = T("两者相互独立", 24, INK, bold=True).move_to(DOWN * 2.55)
        self.play(FadeIn(k_lab), FadeIn(d_lab), run_time=0.7)
        self.play(FadeIn(indep, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(l3, l4, lab3, *allp, sup, coin, k_lab, d_lab, indep, hdr)), run_time=0.8)

    @staticmethod
    def _sd_band(ax, lam):
        s = math.sqrt(lam)
        y = 0.385 if lam < 2 else min(0.385, poisson_pmf(lam, int(lam)) + 0.05)
        a, b = ax.c2p(max(lam - s, 0), y), ax.c2p(lam + s, y)
        g = VGroup(DoubleArrow(a, b, buff=0, color=GOLD, stroke_width=2.5, tip_length=0.12,
                               max_tip_length_to_length_ratio=0.3))
        g.add(DashedLine(ax.c2p(lam, 0), ax.c2p(lam, y), color=GOLD, stroke_width=1.5, dash_length=0.05))
        return g
