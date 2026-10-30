# -*- coding: utf-8 -*-
"""第 5 集：连续的等待——指数、伽马与韦布尔。"""
from common import *  # noqa: F401,F403
from ep4 import phone

EP = 5


def weibull_pdf(x, k, lam=1.0):
    return 0.0 if x <= 0 else k / lam * (x / lam) ** (k - 1) * math.exp(-(x / lam) ** k)


def weibull_h(x, k, lam=1.0):
    return 0.0 if x <= 0 else k / lam * (x / lam) ** (k - 1)


def bulb(color=GOLD, on=True, r=0.35):
    glass = Circle(radius=r, fill_color=color if on else BG, fill_opacity=0.9 if on else 1, stroke_color=AXIS,
                   stroke_width=2)
    base = Rectangle(width=r * 0.9, height=r * 0.5, fill_color=GREY, fill_opacity=1, stroke_width=0)
    base.next_to(glass, DOWN, buff=-0.05)
    return VGroup(glass, base)


class E5A(VScene):
    SID = "E5A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP, hold=1.0)
        st = scene_title("指数分布从哪来")
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        L, R, Y = -5.5, 5.5, 0.6
        tl = Arrow([L, Y, 0], [R, Y, 0], buff=0, color=AXIS, stroke_width=3, max_tip_length_to_length_ratio=0.02)
        now = VGroup(Line([L, Y - 0.2, 0], [L, Y + 0.2, 0], color=INK, stroke_width=4),
                     T("现在", 22, INK, bold=True).next_to([L, Y, 0], DOWN, buff=0.3))
        nxt = phone().move_to([L + 4.3, Y + 0.55, 0])
        br = BraceBetweenPoints([L, Y - 0.15, 0], [L + 4.3, Y - 0.15, 0], DOWN, color=GOLD)
        tt = M("T", 40, GOLD).next_to(br, DOWN, buff=0.1)
        self.play(GrowArrow(tl), FadeIn(now), run_time=0.7)
        self.play(FadeIn(nxt, shift=DOWN * 0.3, scale=1.5), GrowFromCenter(br), FadeIn(tt), run_time=0.9)
        self.catch_up()

        self.seg(1)
        t_ = 3.0
        win = Rectangle(width=t_, height=1.2, fill_color=TEAL, fill_opacity=0.12, stroke_color=TEAL, stroke_width=2)
        win.move_to([L + t_ / 2, Y + 0.2, 0])
        wl = T("这段时间一个电话都没来", 22, TEAL, bold=True).next_to(win, UP, buff=0.1)
        tm = M("t", 32, TEAL).next_to([L + t_, Y, 0], DOWN, buff=0.3)
        self.play(FadeIn(win), FadeIn(wl), FadeIn(tm), run_time=0.8)
        d = MathTex(r"T>t", r"\iff", r"N(t)=0", font_size=50)
        d2 = MathTex(r"P(T>t)", r"=P(N(t)=0)", r"=e^{-\lambda t}\frac{(\lambda t)^0}{0!}", r"=e^{-\lambda t}", font_size=50)
        VGroup(d, d2).arrange(DOWN, buff=0.45).move_to(DOWN * 1.7)
        self.play(Write(d), run_time=1.2)
        self.wait(max(0.2, self.durs[1] * 0.35 - 2.0))
        for part in d2:
            self.play(Write(part), run_time=0.9)
        d2[3].set_color(GOLD)
        self.catch_up()
        self.play(FadeOut(VGroup(tl, now, nxt, br, tt, win, wl, tm, d)), d2.animate.scale(0.7).to_edge(UP, buff=1.2),
                  run_time=0.7)

        self.seg(2)
        F = M(r"F(t)=1-e^{-\lambda t}", 40).move_to(LEFT * 3.6 + UP * 1.0)
        f = M(r"f(t)=F'(t)=\lambda e^{-\lambda t}", 40, BRICK).next_to(F, DOWN, buff=0.4).align_to(F, LEFT)
        self.play(Write(F), run_time=0.8)
        self.play(Write(f), run_time=0.9)
        mv = M(r"\mathbb{E}T=\frac1\lambda,\quad \operatorname{Var}T=\frac1{\lambda^2}", 36).next_to(f, DOWN, buff=0.5)
        mv.align_to(F, LEFT)
        ax = axes([0, 5.3, 1], [0, 2.1, 0.5], 6.0, 3.6, xnums=[0, 1, 2, 3, 4, 5], ynums=[0.5, 1, 1.5, 2], xlabel="t",
                  ylabel="f(t)")
        ax.move_to(RIGHT * 3.3 + DOWN * 0.7)
        self.play(Create(ax), run_time=0.6)
        for l_, c in ((0.5, INK), (1, TEAL), (2, BRICK)):
            cv = curve(ax, lambda x, l_=l_: l_ * math.exp(-l_ * x), 0, 5.2, c, width=4)
            lab = M(rf"\lambda={l_:g}", 26, c).next_to(ax.c2p(0.25, l_), RIGHT, buff=0.2)
            self.play(Create(cv), FadeIn(lab), run_time=0.8)
        self.play(FadeIn(mv), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(3)
        ax2 = axes([0, 4.2, 1], [0, 1.1, 0.5], 10.0, 3.8, xnums=[0, 1, 2, 3, 4], ynums=[0.5, 1], xlabel="t")
        ax2.move_to(DOWN * 0.7)
        self.play(Create(ax2), run_time=0.6)
        lam = 1.0
        cur = None
        for n in (4, 10, 30):
            ks = np.arange(1, int(4.1 * n) + 1)
            p = lam / n
            g = VGroup(*[Line(ax2.c2p(k / n, 0), ax2.c2p(k / n, (1 - p) ** (k - 1) * p * n), color=TEAL,
                              stroke_width=3 if n < 20 else 1.6) for k in ks])
            g.add(M(f"n={n}", 36, TEAL).move_to(ax2.c2p(3.3, 0.85)))
            if cur is None:
                cur = g
                self.play(FadeIn(g, lag_ratio=0.03), run_time=1.0)
            else:
                self.play(Transform(cur, g), run_time=1.3)
            self.wait(0.4)
        ex = curve(ax2, lambda x: math.exp(-x), 0, 4.1, BRICK, width=5)
        self.play(Create(ex), run_time=1.0)
        lim = M(r"\Big(1-\frac{\lambda}{n}\Big)^{nt}\longrightarrow e^{-\lambda t}", 42).move_to(UP * 2.1)
        lbl = T("几何分布的连续版本", 26, BRICK, bold=True).next_to(lim, DOWN, buff=0.2)
        self.play(Write(lim), FadeIn(lbl), run_time=1.0)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)


class E5B(VScene):
    SID = "E5B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("无记忆与风险率")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        d = M(r"P(T>s+t\mid T>s)=\frac{e^{-\lambda(s+t)}}{e^{-\lambda s}}=e^{-\lambda t}", 42).move_to(UP * 2.2)
        self.play(Write(d), run_time=1.5)
        ax = axes([0, 5.3, 1], [0, 1.15, 0.5], 9.0, 3.6, xnums=[0, 1, 2, 3, 4, 5], ynums=[0.5, 1], xlabel="t",
                  ylabel="f(t)")
        ax.move_to(DOWN * 0.8)
        f1 = lambda x: math.exp(-x)  # noqa: E731
        s = 1.0
        base = curve(ax, f1, 0, 5.2, BRICK, width=4)
        self.play(Create(ax), Create(base), run_time=1.0)
        head = area(ax, f1, 0, s, GREY, opacity=0.3)
        tail = area(ax, f1, s, 5.2, BRICK, opacity=0.25)
        sl = DashedLine(ax.c2p(s, 0), ax.c2p(s, 1.1), color=GOLD, stroke_width=3)
        self.play(FadeIn(head), FadeIn(tail), Create(sl), run_time=0.8)
        self.play(FadeOut(head), run_time=0.5)
        tc = curve(ax, f1, s, 5.2, BRICK, width=4)
        self.add(tc)
        self.play(Transform(tc, curve(ax, lambda x: math.exp(-(x - s)), s, 5.2, BRICK, width=4)),
                  Transform(tail, area(ax, lambda x: math.exp(-(x - s)), s, 5.2, BRICK, opacity=0.25)), run_time=1.6)
        ghost = DashedVMobject(curve(ax, f1, 0, 4.2, INK, width=3), num_dashes=40)
        self.play(FadeIn(ghost), run_time=0.3)
        self.play(ghost.animate.shift(ax.c2p(s, 0) - ax.c2p(0, 0)), run_time=1.4)
        un = T("连续分布中唯一无记忆的分布", 26, GOLD, bold=True).move_to(ax.c2p(3.6, 0.85))
        self.play(FadeIn(un), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(1)
        h = M(r"h(t)=\lim_{\Delta\to0}\frac{P(t<T\le t+\Delta\mid T>t)}{\Delta}=\frac{f(t)}{S(t)}=\lambda", 40)
        h.move_to(UP * 2.0)
        self.play(Write(h), run_time=1.8)
        ax = axes([0, 5.3, 1], [0, 2, 1], 6.4, 2.6, xnums=[0, 1, 2, 3, 4, 5], ynums=[1], xlabel="t", ylabel="h(t)")
        ax.move_to(LEFT * 2.4 + DOWN * 1.0)
        hl = Line(ax.c2p(0, 1), ax.c2p(5.1, 1), color=BRICK, stroke_width=5)
        self.play(Create(ax), Create(hl), run_time=1.0)
        old = VGroup(bulb(GOLD, True), T("旧灯泡", 22)).arrange(DOWN, buff=0.2)
        new = VGroup(bulb(GOLD, True), T("新灯泡", 22)).arrange(DOWN, buff=0.2)
        pair = VGroup(old, new).arrange(RIGHT, buff=0.9).move_to(RIGHT * 4.2 + DOWN * 0.8)
        eq = M("=", 50).move_to(pair)
        self.play(FadeIn(pair, scale=0.8), FadeIn(eq), run_time=0.8)
        nt = T("不老化：一样容易坏", 26, GOLD, bold=True).next_to(pair, DOWN, buff=0.4)
        self.play(FadeIn(nt), run_time=0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(2)
        rates = [(0.5, TEAL), (1.0, INDIGO), (1.5, BRICK)]
        life = [2.6, 1.3, 2.1]
        rows = VGroup()
        for i, ((l_, c), lf) in enumerate(zip(rates, life)):
            b = bulb(GOLD).scale(0.8).move_to([-5.6, 1.4 - i * 1.0, 0])
            lab = M(rf"\mathrm{{Exp}}(\lambda_{i + 1})", 28, c).next_to(b, RIGHT, buff=0.3)
            rows.add(VGroup(b, lab))
        self.play(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.2), run_time=0.9)
        x0 = -3.0
        sc = 2.4
        bars_ = VGroup(*[Rectangle(width=0.01, height=0.35, fill_color=c, fill_opacity=0.6, stroke_width=0)
                         .move_to([x0, 1.4 - i * 1.0, 0], aligned_edge=LEFT) for i, (_, c) in enumerate(rates)])
        self.add(bars_)
        t = ValueTracker(0)
        for i, b in enumerate(bars_):
            b.add_updater(lambda m, i=i: m.stretch_to_fit_width(max(0.01, min(t.get_value(), life[i]) * sc))
                          .move_to([x0, 1.4 - i * 1.0, 0], aligned_edge=LEFT))
        self.play(t.animate.set_value(life[1]), run_time=2.0, rate_func=linear)
        rows[1][0][0].set_fill(BG, 1)
        out = VGroup(Line([x0 + life[1] * sc, 2.0, 0], [x0 + life[1] * sc, -0.9, 0], color=GOLD, stroke_width=3),
                     T("第一盏熄灭", 22, GOLD, bold=True).move_to([x0 + life[1] * sc, 2.25, 0]))
        self.play(Create(out[0]), FadeIn(out[1]), Flash(rows[1][0], color=GREY), run_time=0.8)
        for b in bars_:
            b.clear_updaters()
        mn = M(r"P(\min T_i>t)=\prod_i e^{-\lambda_i t}=e^{-(\lambda_1+\lambda_2+\lambda_3)t}", 38).move_to(DOWN * 1.8)
        pj = mixed("第 ", "$j$", " 个最先响的概率 ", "$=\\dfrac{\\lambda_j}{\\lambda_1+\\lambda_2+\\lambda_3}$", size=26)
        pj.next_to(mn, DOWN, buff=0.35)
        self.play(Write(mn), run_time=1.5)
        self.wait(max(0.2, self.durs[2] * 0.68 - 6.2))
        self.play(FadeIn(pj), run_time=0.8)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(3)
        ax = axes([0, 1.05, 0.5], [0, 4.2, 1], 4.4, 3.4, xnums=[0, 0.5, 1], ynums=[1, 2, 3, 4], xlabel="u",
                  ylabel=r"-\ln u/\lambda")
        ax.move_to(LEFT * 2.5 + DOWN * 0.4)
        cv = curve(ax, lambda u: -math.log(u), 0.015, 1, BRICK, width=4, ymax=4.15)
        self.play(Create(ax), Create(cv), run_time=1.0)
        f = M(r"U\sim U(0,1)\ \Rightarrow\ -\frac{\ln U}{\lambda}\sim\mathrm{Exp}(\lambda)", 40).move_to(RIGHT * 3.3 +
                                                                                                   UP * 0.8)
        back = T("← 第 1 集：逆变换", 24, MUTED).next_to(f, DOWN, buff=0.3)
        self.play(Write(f), run_time=1.2)
        self.play(FadeIn(back), run_time=0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)


class E5C(VScene):
    SID = "E5C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("伽马分布：等第 n 个事件")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        L, Y = -5.5, 1.2
        ev = [1.3, 2.5, 4.6]

        self.seg(0)
        tl = Arrow([L, Y, 0], [5.5, Y, 0], buff=0, color=AXIS, stroke_width=3, max_tip_length_to_length_ratio=0.02)
        self.play(GrowArrow(tl), run_time=0.6)
        rings = VGroup(*[phone().move_to([L + e * 1.6, Y + 0.5, 0]) for e in ev])
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.3) for r in rings], lag_ratio=0.3), run_time=1.0)
        cols = [TEAL, INDIGO, BRICK]
        pts = [0] + ev
        segs = VGroup()
        for i in range(3):
            br = BraceBetweenPoints([L + pts[i] * 1.6, Y - 0.15, 0], [L + pts[i + 1] * 1.6, Y - 0.15, 0], DOWN,
                                    color=cols[i])
            segs.add(VGroup(br, M(f"T_{i + 1}", 30, cols[i]).next_to(br, DOWN, buff=0.08)))
        self.play(LaggedStart(*[FadeIn(s_) for s_ in segs], lag_ratio=0.3), run_time=1.0)
        s3 = M(r"S_3=T_1+T_2+T_3", 42).move_to(DOWN * 0.9)
        self.play(Write(s3), run_time=0.9)
        self.catch_up()

        self.seg(1)
        self.play(FadeOut(VGroup(segs, s3)), run_time=0.4)
        a = MathTex(r"S_n>t", r"\iff", r"N(t)<n", font_size=50).move_to(DOWN * 0.3)
        b = MathTex(r"P(S_n>t)=\sum_{k=0}^{n-1}e^{-\lambda t}\frac{(\lambda t)^k}{k!}", font_size=50).move_to(DOWN * 1.8)
        win = Rectangle(width=3.0 * 1.6, height=1.4, fill_color=TEAL, fill_opacity=0.1, stroke_color=TEAL)
        win.move_to([L + 1.5 * 1.6, Y + 0.25, 0])
        wl = mixed("到 ", "$t$", " 为止来电少于 ", "$n$", " 个", size=22, color=TEAL).next_to(win, UP, buff=0.05)
        self.play(FadeIn(win), FadeIn(wl), Write(a), run_time=1.2)
        self.wait(0.6)
        self.play(Write(b), run_time=1.4)
        self.catch_up()
        self.play(FadeOut(VGroup(tl, rings, win, wl, a)), b.animate.scale(0.75).move_to(UP * 2.2), run_time=0.7)

        self.seg(2)
        rows = MathTex(r"-\frac{d}{dt}P(S_n>t)", r"=\lambda e^{-\lambda t}\Big[", r"\Big(1", r"-\lambda t\Big)",
                       r"+\Big(\lambda t", r"-\frac{(\lambda t)^2}{2!}\Big)", r"+\cdots+\Big(\frac{(\lambda t)^{n-2}}{(n-2)!}",
                       r"-\frac{(\lambda t)^{n-1}}{(n-1)!}\Big)\Big]", font_size=34).move_to(UP * 0.7)
        self.play(Write(rows), run_time=2.2)
        pairs = [(3, 4), (5, 6)]
        strikes = VGroup()
        for i, j in pairs:
            for k in (i, j):
                strikes.add(Line(rows[k].get_corner(DL), rows[k].get_corner(UR), color=BRICK, stroke_width=3))
        self.play(LaggedStart(*[Create(s_) for s_ in strikes], lag_ratio=0.3), run_time=1.6)
        lab = T("相邻两项两两抵消", 24, BRICK, bold=True).next_to(rows, DOWN, buff=0.3)
        self.play(FadeIn(lab), run_time=0.5)
        res = M(r"f_{S_n}(t)=\frac{\lambda^n t^{n-1}e^{-\lambda t}}{(n-1)!}", 54, GOLD).move_to(DOWN * 1.8)
        self.play(Write(res), run_time=1.3)
        er = T("爱尔朗分布", 26, GOLD, bold=True).next_to(res, RIGHT, buff=0.4)
        self.play(FadeIn(er), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(rows, strikes, lab, b, er, res)), run_time=0.7)

        self.seg(3)
        g = M(r"\Gamma(\alpha)=\int_0^\infty x^{\alpha-1}e^{-x}\,dx,\qquad \Gamma(n)=(n-1)!", 40).move_to(UP * 2.3 +
                                                                                                        RIGHT * 2.6)
        self.play(Write(g), run_time=1.4)
        ax = axes([0, 5.4, 1], [0, 25, 5], 8.4, 3.8, xnums=[1, 2, 3, 4, 5], ynums=[6, 24], xlabel=r"\alpha",
                  ylabel=r"\Gamma(\alpha)")
        ax.move_to(DOWN * 0.8)
        cv = curve(ax, lambda x: math.gamma(x), 0.35, 5.25, INDIGO, width=4, ymax=25)
        self.play(Create(ax), Create(cv), run_time=1.4)
        dots = VGroup(*[Dot(ax.c2p(n, math.factorial(n - 1)), radius=0.09, color=GOLD) for n in range(1, 6)])
        labs = VGroup(*[M(f"{math.factorial(n - 1)}", 24, GOLD).next_to(dots[n - 1], UL, buff=0.05) for n in range(1, 6)])
        self.play(LaggedStart(*[FadeIn(d, scale=2) for d in dots], lag_ratio=0.2), FadeIn(labs), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(g, ax, cv, dots, labs)), run_time=0.5)

        self.seg(4)
        f = M(r"f(x)=\frac{\lambda^\alpha}{\Gamma(\alpha)}x^{\alpha-1}e^{-\lambda x}", 40).move_to(UP * 2.2 + RIGHT * 3.0)
        ax = axes([0, 8.3, 1], [0, 1.1, 0.5], 8.6, 4.0, xnums=list(range(9)), ynums=[0.5, 1], xlabel="x",
                  ylabel="f(x)")
        ax.move_to(LEFT * 1.6 + DOWN * 0.6)
        al = ValueTracker(0.5)
        G = always_redraw(lambda: curve(ax, lambda x: gamma_pdf(x, al.get_value()), 0.004, 8.2, BRICK, width=4.5,
                                        ymax=1.08))
        alab = VGroup(M(r"\alpha=", 38), DecimalNumber(0.5, num_decimal_places=1, font_size=38, color=INK)).arrange(
            RIGHT, buff=0.1).move_to(ax.c2p(6.3, 0.9))
        alab[1].add_updater(lambda m: m.set_value(al.get_value()))
        self.play(Create(ax), Write(f), FadeIn(alab), Create(G), run_time=1.4)
        notes = {1: mixed("$\\alpha=1$", "：指数分布", size=24), 2: mixed("$\\alpha<1$", "：零附近冲高", size=24),
                 5: mixed("$\\alpha$", " 大：越来越对称 → 正态", size=24)}
        col = VGroup()
        traces = VGroup()
        for v in (1, 2, 3, 5):
            traces.add(curve(ax, lambda x, a=al.get_value(): gamma_pdf(x, a), 0.004, 8.2, BRICK, width=2,
                             ymax=1.08).set_stroke(opacity=0.25))
            self.add(traces[-1])
            anims = [al.animate.set_value(v)]
            if v in notes:
                col.add(notes[v])
            self.play(*anims, run_time=1.8, rate_func=smooth)
            self.wait(0.5)
        col.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(RIGHT * 4.6 + UP * 0.3)
        mv = M(r"\mathbb{E}X=\frac{\alpha}{\lambda},\ \operatorname{Var}X=\frac{\alpha}{\lambda^2}", 32).next_to(
            col, DOWN, buff=0.35)
        self.play(FadeIn(col), FadeIn(mv), run_time=0.8)
        self.catch_up()
        alab[1].clear_updaters()
        self.play(FadeOut(VGroup(f, ax, G, alab, col, mv, traces)), run_time=0.5)

        self.seg(5)
        add = M(r"\Gamma(2,\lambda)+\Gamma(3,\lambda)=\Gamma(5,\lambda)", 50).move_to(DOWN * 1.2)
        L2, Y2 = -5.0, 1.0
        evs = [1.0, 2.2, 3.1, 4.4, 6.0]
        tl = Arrow([L2, Y2, 0], [5.6, Y2, 0], buff=0, color=AXIS, stroke_width=3, max_tip_length_to_length_ratio=0.02)
        rings = VGroup(*[phone(0.2).move_to([L2 + e * 1.5, Y2 + 0.45, 0]) for e in evs])
        b1 = BraceBetweenPoints([L2, Y2 - 0.15, 0], [L2 + evs[1] * 1.5, Y2 - 0.15, 0], DOWN, color=TEAL)
        b2 = BraceBetweenPoints([L2 + evs[1] * 1.5, Y2 - 0.15, 0], [L2 + evs[4] * 1.5, Y2 - 0.15, 0], DOWN, color=INDIGO)
        self.play(GrowArrow(tl), LaggedStart(*[FadeIn(r) for r in rings], lag_ratio=0.15), run_time=1.2)
        self.play(GrowFromCenter(b1), GrowFromCenter(b2), run_time=0.8)
        self.play(Write(add), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(add, tl, rings, b1, b2)), run_time=0.5)

        self.seg(6)
        card = VGroup(M(r"\Gamma\big(\tfrac k2,\tfrac12\big)=\chi^2_k", 60, INDIGO),
                      T("第 7 集：正态变量的平方和", 26, MUTED)).arrange(DOWN, buff=0.4)
        cb = note_box(card, INDIGO, pad=0.4)
        self.play(FadeIn(cb, scale=0.9), run_time=1.0)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)


class E5D(VScene):
    SID = "E5D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("韦布尔：会老化的寿命")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        links = VGroup()
        for i in range(9):
            e = Ellipse(width=1.2, height=0.6 if i % 2 == 0 else 0.25, stroke_color=AXIS, stroke_width=6)
            links.add(e)
        links.arrange(RIGHT, buff=-0.25).move_to(UP * 0.8)
        self.play(LaggedStart(*[Create(l_) for l_ in links], lag_ratio=0.1), run_time=1.4)
        weak = links[5]
        self.play(weak.animate.set_color(BRICK), Flash(weak, color=BRICK, flash_radius=0.6), run_time=0.8)
        left, right = VGroup(*links[:5]), VGroup(*links[6:])
        self.play(FadeOut(weak, scale=1.4), left.animate.shift(DOWN * 0.5 + LEFT * 0.2).rotate(-0.15),
                  right.animate.shift(DOWN * 0.8 + RIGHT * 0.2).rotate(0.2), run_time=0.9)
        mn = M(r"T=\min(T_1,\dots,T_m)", 46).move_to(DOWN * 1.6)
        self.play(Write(mn), run_time=1.0)
        lab = T("最弱的一环决定整条链子", 26, BRICK, bold=True).next_to(mn, DOWN, buff=0.3)
        self.play(FadeIn(lab), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(left, right, mn, lab)), run_time=0.5)

        self.seg(1)
        f1 = M(r"E\sim\mathrm{Exp}(1),\qquad X=\lambda E^{1/k}", 48).move_to(UP * 1.0)
        f2 = M(r"F(x)=P(E\le (x/\lambda)^k)=1-e^{-(x/\lambda)^k}", 46).move_to(DOWN * 0.4)
        self.play(Write(f1), run_time=1.2)
        self.play(Write(f2), run_time=1.4)
        self.catch_up()
        self.play(FadeOut(f1), f2.animate.scale(0.7).move_to(UP * 2.3), run_time=0.6)

        self.seg(2)
        hf = M(r"h(x)=\frac{k}{\lambda}\Big(\frac{x}{\lambda}\Big)^{k-1}", 40).next_to(f2, DOWN, buff=0.25)
        axh = axes([0, 2.65, 0.5], [0, 4.2, 1], 7.0, 3.3, xnums=[0, 1, 2], ynums=[1, 2, 3, 4], xlabel="x",
                   ylabel="h(x)")
        axh.move_to(LEFT * 1.8 + DOWN * 1.3)
        self.play(Write(hf), Create(axh), run_time=1.1)
        specs = [(0.5, PLUM, "k<1：递减，早期故障"), (1.0, INK, "k=1：恒定，随机失效"), (3.0, BRICK, "k>1：递增，老化磨损")]
        rows = VGroup()
        for k, c, name in specs:
            cv = curve(axh, lambda x, k=k: weibull_h(x, k), 0.004, 2.6, c, width=4, ymax=4.15)
            row = VGroup(Line(ORIGIN, RIGHT * 0.4, color=c, stroke_width=4), T(name, 22, c, bold=True)).arrange(
                RIGHT, buff=0.15)
            rows.add(row)
            rows.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(RIGHT * 4.3 + DOWN * 1.0)
            self.play(Create(cv), FadeIn(row), run_time=1.3)
            self.wait(0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(3)
        ax = axes([0, 10.3, 1], [0, 2.2, 0.5], 10.4, 3.8, xnums=(), ynums=(), xlabel=T("使用时间", 22, INK),
                  ylabel=T("故障率", 22, INK))
        ax.move_to(DOWN * 0.5)
        tub = lambda x: 1.3 * math.exp(-1.2 * x) + 0.3 + 0.0012 * x ** 3  # noqa: E731
        cv = curve(ax, tub, 0.02, 10, GOLD, width=5)
        self.play(Create(ax), run_time=0.6)
        self.play(Create(cv), run_time=2.0)
        zones = VGroup()
        for (a, b), c, txt in (((0, 2.2), PLUM, "早期失效"), ((2.2, 7.0), INK, "偶然失效"), ((7.0, 10), BRICK, "耗损失效")):
            r = Rectangle(width=(ax.c2p(b, 0) - ax.c2p(a, 0))[0], height=3.6, fill_color=c, fill_opacity=0.07,
                          stroke_width=0).move_to(ax.c2p((a + b) / 2, 1.0))
            zones.add(VGroup(r, T(txt, 24, c, bold=True).move_to(ax.c2p((a + b) / 2, 1.95))))
        self.play(LaggedStart(*[FadeIn(z) for z in zones], lag_ratio=0.4), run_time=1.5)
        tt = T("浴盆曲线", 30, INK, bold=True).move_to(UP * 2.3)
        self.play(FadeIn(tt), run_time=0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(4)
        ax = axes([-4, 4.2, 1], [0, 0.45, 0.1], 9.0, 3.4, xnums=(), ynums=(), tips=False)
        ax.move_to(DOWN * 0.6)
        bell = curve(ax, norm_pdf, -4, 4, BRICK, width=5)
        pieces = VGroup(*[Rectangle(width=0.3, height=0.3, fill_color=tint(TEAL, 0.5), fill_opacity=1,
                                    stroke_color=TEAL).move_to([x, 2.4, 0]) for x in np.linspace(-5, 5, 14)])
        self.play(LaggedStart(*[FadeIn(p_, shift=DOWN * 0.3) for p_ in pieces], lag_ratio=0.05), run_time=1.0)
        self.play(*[p_.animate.move_to(bell.point_from_proportion(i / 13)) for i, p_ in enumerate(pieces)], run_time=1.4)
        self.play(Create(bell), FadeOut(pieces), run_time=1.0)
        nt = T("下一集：钟形曲线从哪来", 30, BRICK, bold=True).move_to(DOWN * 2.6)
        self.play(FadeIn(nt), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
