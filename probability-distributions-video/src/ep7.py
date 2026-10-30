# -*- coding: utf-8 -*-
"""第 7 集：从样本到推断——卡方、t、F 与贝塔。"""
from common import *  # noqa: F401,F403
from props import coin

EP = 7


def dashed(ax, f, a, b, color, width=3, ymax=None):
    return DashedVMobject(curve(ax, f, a, b, color, width=width, ymax=ymax), num_dashes=60, dashed_ratio=0.55)


def hist(ax, data, lo, hi, nb, color, opacity=0.4):
    """样本直方图，按密度归一化。"""
    cnt, edges = np.histogram(data, bins=nb, range=(lo, hi))
    w = edges[1] - edges[0]
    dens = cnt / (len(data) * w)
    g = VGroup()
    for c, x0 in zip(dens, edges[:-1]):
        if c <= 0:
            continue
        a, b = ax.c2p(x0, 0), ax.c2p(x0 + w, c)
        g.add(Rectangle(width=b[0] - a[0], height=b[1] - a[1], fill_color=tint(color, opacity), fill_opacity=1,
                        stroke_color=color, stroke_width=1).move_to((a + b) / 2))
    return g


class E7A(VScene):
    SID = "E7A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP, hold=1.2)
        st = scene_title("小样本的难题", INDIGO)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        place = T("1908 · 都柏林 · 吉尼斯酒厂", 34, INK, bold=True).move_to(UP * 1.9)
        self.play(FadeIn(place, shift=DOWN * 0.2), run_time=0.7)
        # 四支试管，每支一个化验读数
        tubes = VGroup()
        for i, v in enumerate(["3.1", "2.6", "3.4", "2.9"]):
            body = RoundedRectangle(corner_radius=0.18, width=0.42, height=1.6, stroke_color=INK, stroke_width=2.5)
            liquid = RoundedRectangle(corner_radius=0.16, width=0.36, height=0.6 + 0.15 * i, fill_color=GOLD,
                                      fill_opacity=0.75, stroke_width=0).align_to(body, DOWN).shift(UP * 0.03)
            lab = M(v, 30, INK).next_to(body, DOWN, buff=0.2)
            tubes.add(VGroup(body, liquid, lab))
        tubes.arrange(RIGHT, buff=0.7).move_to(DOWN * 0.1 + LEFT * 2.2)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.3) for t in tubes], lag_ratio=0.25), run_time=1.4)
        n4 = T("每批只能化验几次", 28, MUTED).next_to(tubes, DOWN, buff=0.4)
        self.play(FadeIn(n4), run_time=0.5)
        ax = axes([-4, 4.2, 1], [0, 0.45, 0.1], 5.2, 2.6, tips=False).move_to(RIGHT * 3.2 + DOWN * 0.2)
        nc = curve(ax, norm_pdf, -4, 4, GREY, width=3)
        tc = curve(ax, lambda x: t_pdf(x, 3), -4, 4, INDIGO, width=4)
        self.play(Create(ax), Create(nc), run_time=0.9)
        q = T("正态：过于自信", 24, GREY).next_to(ax, UP, buff=0.1)
        self.play(FadeIn(q), run_time=0.4)
        self.wait(max(0.3, self.left() - 2.6))
        q2 = T("戈塞特的答案：t 分布", 26, INDIGO, bold=True).move_to(q)
        self.play(Create(tc), ReplacementTransform(q, q2), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(place, tubes, n4, ax, nc, tc, q2)), run_time=0.5)

        self.seg(1)
        st2 = scene_title("卡方：距离的平方", INDIGO)
        self.play(ReplacementTransform(st, st2), run_time=0.4)
        plane = NumberPlane(x_range=[-3.2, 3.2, 1], y_range=[-3.2, 3.2, 1], x_length=5.4, y_length=5.4,
                            background_line_style={"stroke_color": FAINT, "stroke_width": 1},
                            axis_config={"stroke_color": AXIS, "stroke_width": 2}).move_to(LEFT * 3.2 + DOWN * 0.4)
        self.play(Create(plane), run_time=0.8)
        rng = np.random.default_rng(7)
        pts = rng.standard_normal((160, 2))
        dots = VGroup(*[Dot(plane.c2p(*p), radius=0.035, color=INDIGO, fill_opacity=0.55) for p in pts])
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.01), run_time=1.4)
        z = np.array([1.3, 0.9])
        P = Dot(plane.c2p(*z), radius=0.09, color=GOLD)
        seg_ = Line(plane.c2p(0, 0), plane.c2p(*z), color=GOLD, stroke_width=5)
        hx = DashedLine(plane.c2p(0, 0), plane.c2p(z[0], 0), color=BRICK, stroke_width=3)
        vy = DashedLine(plane.c2p(z[0], 0), plane.c2p(*z), color=TEAL, stroke_width=3)
        lz1 = M("Z_1", 30, BRICK).next_to(hx, DOWN, buff=0.1)
        lz2 = M("Z_2", 30, TEAL).next_to(vy, RIGHT, buff=0.1)
        self.play(FadeIn(P, scale=2), Create(seg_), run_time=0.7)
        self.play(Create(hx), Create(vy), FadeIn(lz1), FadeIn(lz2), run_time=0.8)
        f1 = MathTex(r"R^2=", r"Z_1^2", "+", r"Z_2^2", font_size=52).move_to(RIGHT * 3.4 + UP * 1.5)
        f1[1].set_color(BRICK)
        f1[3].set_color(TEAL)
        self.play(Write(f1), run_time=1.0)
        f2 = M(r"Z_1^2+Z_2^2+\cdots+Z_k^2\ \sim\ \chi^2_k", 44, INDIGO).move_to(RIGHT * 3.4 + UP * 0.2)
        self.play(TransformFromCopy(f1, f2), run_time=1.1)
        cap = T("k 个独立标准正态的平方和", 24, MUTED).next_to(f2, DOWN, buff=0.25)
        self.play(FadeIn(cap), run_time=0.5)
        # 圆周随半径呼吸：随机点到原点的距离
        ring = Circle(radius=0.01, color=GOLD, stroke_width=2).move_to(plane.c2p(0, 0))
        self.add(ring)
        r0 = np.linalg.norm(z)
        self.play(ring.animate.set(width=2 * r0 * plane.x_length / 6.4), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(plane, dots, P, seg_, hx, vy, lz1, lz2, ring, f1, cap)),
                  f2.animate.scale(0.75).to_corner(UR, buff=0.35).shift(DOWN * 0.55), run_time=0.6)

        self.seg(2)
        ax = axes([-3.2, 3.3, 1], [0, 0.45, 0.1], 6.0, 2.6, xnums=(), ynums=(), tips=False).move_to(
            LEFT * 3.3 + DOWN * 0.3)
        nz = curve(ax, norm_pdf, -3.2, 3.2, INK, width=3.5)
        self.play(Create(ax), Create(nz), run_time=0.8)
        sx = ValueTracker(0.4)
        shade = always_redraw(lambda: area(ax, norm_pdf, -sx.get_value(), sx.get_value(), INDIGO, 0.35))
        lo = always_redraw(lambda: M(r"-\sqrt x", 24, INDIGO).next_to(ax.c2p(-sx.get_value(), 0), DOWN, buff=0.12))
        hi = always_redraw(lambda: M(r"\sqrt x", 24, INDIGO).next_to(ax.c2p(sx.get_value(), 0), DOWN, buff=0.12))
        self.play(FadeIn(shade), FadeIn(lo), FadeIn(hi), run_time=0.5)
        self.play(sx.animate.set_value(1.5), run_time=1.5)
        self.play(sx.animate.set_value(0.9), run_time=0.8)
        rows = VGroup(
            M(r"P(Z^2\le x)=P(-\sqrt x\le Z\le\sqrt x)", 34),
            M(r"=2\Phi(\sqrt x)-1", 34),
            M(r"f(x)=2\varphi(\sqrt x)\cdot\frac{1}{2\sqrt x}", 34),
            M(r"=\frac{1}{\sqrt{2\pi}}\,x^{-1/2}e^{-x/2}", 38, INDIGO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to(RIGHT * 3.1 + UP * 0.6)
        for r in rows:
            self.play(Write(r), run_time=1.1)
            self.wait(0.4)
        gam = mixed("$=\\Gamma(\\tfrac12,\\tfrac12)$", " 的密度", size=28, color=GOLD).next_to(rows, DOWN, buff=0.35)
        self.play(FadeIn(gam, shift=UP * 0.2), Circumscribe(rows[3], color=GOLD), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, nz, shade, lo, hi, rows[:3])), VGroup(rows[3], gam).animate.move_to(UP * 1.7),
                  run_time=0.7)

        self.seg(3)
        terms = VGroup(*[M(r"\Gamma(\tfrac12,\tfrac12)", 32, INDIGO) for _ in range(4)])
        plus = VGroup(*[M("+", 32) for _ in range(3)])
        row = VGroup(terms[0], plus[0], terms[1], plus[1], terms[2], plus[2], M(r"\cdots", 32), M("=", 32),
                     M(r"\Gamma(\tfrac k2,\tfrac12)", 40, GOLD)).arrange(RIGHT, buff=0.2).move_to(UP * 0.4)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in row[:7]], lag_ratio=0.15), run_time=1.6)
        br = Brace(row[:7], DOWN, color=MUTED)
        bl = T("k 个独立同速率伽马相加", 22, MUTED).next_to(br, DOWN, buff=0.1)
        self.play(GrowFromCenter(br), FadeIn(bl), run_time=0.7)
        self.play(FadeIn(row[7:], shift=LEFT * 0.3), run_time=0.8)
        eq = M(r"=\chi^2_k", 44, INDIGO).next_to(row, RIGHT, buff=0.2)
        self.play(Write(eq), run_time=0.6)
        self.wait(max(0.3, self.left() - 2.0))
        cards = stat_cards([("期望", r"E\chi^2_k=k"), ("方差", r"\operatorname{Var}\chi^2_k=2k"),
                            ("来源", r"EZ^2=1,\ \operatorname{Var}Z^2=2")], INDIGO, width=11.6, y=-2.3)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.2), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(row, br, bl, eq, rows[3], gam, cards)), run_time=0.5)

        self.seg(4)
        ax = axes([0, 20.5, 2], [0, 0.55, 0.1], 10.5, 4.0, xnums=[0, 4, 8, 12, 16, 20], ynums=[0.2, 0.4],
                  xlabel="x").move_to(DOWN * 0.6)
        self.play(Create(ax), run_time=0.6)
        k = ValueTracker(1)
        cv = always_redraw(lambda: curve(ax, lambda x: chi2_pdf(x, k.get_value()), 0.02, 20.4, INDIGO, width=5,
                                         ymax=0.55))
        ar = always_redraw(lambda: area(ax, lambda x: chi2_pdf(x, k.get_value()), 0.02, 20.4, INDIGO, 0.15,
                                        ymax=0.55))
        kl = always_redraw(lambda: M(f"k={k.get_value():.1f}", 40, INDIGO).move_to(ax.c2p(15, 0.45)))
        self.play(FadeIn(cv), FadeIn(ar), FadeIn(kl), run_time=0.5)
        self.play(k.animate.set_value(2), run_time=1.2)
        ex = curve(ax, lambda x: 0.5 * math.exp(-x / 2), 0, 20.4, GOLD, width=3)
        exl = mixed("$k=2$", "：均值为 2 的指数", size=24, color=GOLD).move_to(ax.c2p(9.5, 0.33))
        self.play(Create(ex), FadeIn(exl), run_time=0.9)
        self.wait(0.6)
        self.play(FadeOut(ex), FadeOut(exl), run_time=0.4)
        self.play(k.animate.set_value(10), run_time=self.left(2.5) * 0.85, rate_func=smooth)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E7B(VScene):
    SID = "E7B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("样本方差与自由度", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        xs = [1.2, 2.6, 3.1, 4.4, 5.0, 6.7]
        mean = sum(xs) / len(xs)
        nl = NumberLine(x_range=[0, 8, 1], length=11, color=AXIS, include_numbers=False).move_to(UP * 0.6)
        self.play(Create(nl), run_time=0.6)
        dots = VGroup(*[Dot(nl.n2p(x), radius=0.12, color=INDIGO) for x in xs])
        for d in dots:
            d.shift(UP * 2.5)
        self.play(LaggedStart(*[d.animate.shift(DOWN * 2.5) for d in dots], lag_ratio=0.15), run_time=1.4,
                  rate_func=rate_functions.ease_out_bounce)
        labels = VGroup(*[M(f"X_{i + 1}", 26, INDIGO).next_to(d, UP, buff=0.15) for i, d in enumerate(dots)])
        self.play(FadeIn(labels), run_time=0.4)
        ml = DashedLine(nl.n2p(mean) + UP * 1.1, nl.n2p(mean) + DOWN * 2.8, color=GOLD, stroke_width=3)
        mlab = M(r"\bar X", 34, GOLD).next_to(ml, UP, buff=0.1)
        self.play(Create(ml), FadeIn(mlab), run_time=0.7)
        arrows = VGroup()
        for i, x in enumerate(xs):
            y = -0.35 - 0.38 * i
            arrows.add(Arrow(nl.n2p(mean) + UP * y, nl.n2p(x) + UP * y, buff=0, stroke_width=4,
                             max_tip_length_to_length_ratio=0.25, color=BRICK if x > mean else TEAL))
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.15), run_time=1.6)
        ss = M(r"\sum_{i=1}^n (X_i-\bar X)^2", 40).to_edge(DOWN, buff=0.35).shift(RIGHT * 3.6)
        self.play(Write(ss), run_time=0.9)
        self.catch_up()

        self.seg(1)
        # 偏差首尾相接：正负抵消回到原点
        base = nl.n2p(mean) + DOWN * 2.85
        chain = VGroup()
        cur = base.copy()
        unit = nl.n2p(1)[0] - nl.n2p(0)[0]
        for x, a in zip(xs, arrows):
            d = (x - mean) * unit
            chain.add(Arrow(cur, cur + RIGHT * d, buff=0, stroke_width=4, max_tip_length_to_length_ratio=0.25,
                            color=a.get_color()))
            cur = cur + RIGHT * d
        for i, c in enumerate(chain):
            c.shift(UP * (0.16 * (i % 2)))
        self.play(FadeOut(ss), run_time=0.3)
        self.play(LaggedStart(*[ReplacementTransform(a.copy(), c) for a, c in zip(arrows, chain)], lag_ratio=0.3),
                  run_time=2.4)
        zero = M(r"\sum (X_i-\bar X)=0", 38, GOLD).next_to(base, DOWN, buff=0.25).shift(RIGHT * 3.4)
        self.play(Write(zero), Flash(base, color=GOLD), run_time=1.0)
        self.wait(0.6)
        self.play(arrows[-1].animate.set_color(GREY).set_opacity(0.45), chain[-1].animate.set_color(GREY),
                  dots[-1].animate.set_color(GREY), run_time=0.8)
        q = T("最后一个由前面的决定", 24, GREY).next_to(arrows[-1].get_end(), UP, buff=0.1).shift(LEFT * 0.6)
        self.play(FadeIn(q), run_time=0.4)
        dof = mixed("自由度 ", "$=n-1$", size=36, color=INDIGO).to_edge(DOWN, buff=0.3).shift(LEFT * 3.5)
        self.play(FadeIn(dof, scale=1.2), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(nl, dots, labels, ml, mlab, arrows, chain, zero, q)),
                  dof.animate.scale(0.75).to_corner(UR, buff=0.35).shift(DOWN * 0.55), run_time=0.6)

        self.seg(2)
        r1 = M(r"\frac{(n-1)S^2}{\sigma^2}=\frac{\sum (X_i-\bar X)^2}{\sigma^2}\ \sim\ \chi^2_{n-1}", 48,
               INDIGO).move_to(UP * 1.4)
        self.play(Write(r1), run_time=1.6)
        r2 = mixed("$\\bar X$", " 与 ", "$S^2$", " 相互独立", size=32).move_to(UP * 0.0)
        r2n = T("（只有正态总体才成立）", 24, MUTED).next_to(r2, DOWN, buff=0.15)
        self.play(FadeIn(r2, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(r2n), run_time=0.5)
        self.wait(max(0.3, self.left() - 4.5))
        r3 = M(r"E S^2=\frac{\sigma^2}{n-1}\cdot E\chi^2_{n-1}=\frac{\sigma^2}{n-1}\cdot(n-1)=\sigma^2", 40).move_to(
            DOWN * 1.6)
        self.play(Write(r3), run_time=1.6)
        why = T("所以除以 n−1，而不是 n", 28, GOLD, bold=True).next_to(r3, DOWN, buff=0.3)
        self.play(FadeIn(why, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E7C(VScene):
    SID = "E7C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("t 分布", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        z = MathTex(r"\frac{\bar X-\mu}{\sigma/\sqrt n}", r"\ \sim\ N(0,1)", font_size=60).move_to(UP * 1.2)
        self.play(Write(z), run_time=1.4)
        self.wait(max(0.3, self.left() * 0.3))
        sig = z[0][5]  # 分母里的 σ
        cross = Cross(sig, stroke_color=BRICK, stroke_width=6)
        unk = T("σ 不知道", 28, BRICK, bold=True).next_to(z, LEFT, buff=0.4)
        self.play(Create(cross), FadeIn(unk), run_time=0.8)
        z2 = MathTex(r"\frac{\bar X-\mu}{S/\sqrt n}", r"\ \sim\ ?", font_size=60).move_to(DOWN * 1.0)
        self.play(TransformFromCopy(z, z2), run_time=1.2)
        s_note = T("S 本身也是随机的，小样本时常常偏小", 26, MUTED).next_to(z2, DOWN, buff=0.35)
        self.play(FadeIn(s_note), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(z, cross, unk, s_note)), z2.animate.move_to(UP * 1.8), run_time=0.6)

        self.seg(1)
        tt = MathTex(r"T=", r"\frac{Z}{\sqrt{V/\nu}}", font_size=64).move_to(DOWN * 0.1)
        tt[1].set_color(INDIGO)
        self.play(Write(tt), run_time=1.2)
        lab = VGroup(mixed("$Z\\sim N(0,1)$", size=26), mixed("$V\\sim\\chi^2_\\nu$", size=26),
                     T("两者独立", 24, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(tt, RIGHT, buff=0.7)
        self.play(FadeIn(lab, shift=LEFT * 0.2), run_time=0.8)
        nu = mixed("这里 ", "$\\nu=n-1$", size=30, color=INDIGO).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(nu), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(z2, tt, lab, nu)), run_time=0.5)

        self.seg(2)
        ax = axes([-6, 6.2, 1], [0, 0.45, 0.1], 11.0, 3.9, xnums=[-6, -4, -2, 0, 2, 4, 6], ynums=(),
                  tips=False).move_to(DOWN * 0.7)
        self.play(Create(ax), run_time=0.6)
        rng = np.random.default_rng(11)
        X = rng.standard_normal((4000, 4))
        ts = X.mean(1) / (X.std(1, ddof=1) / 2)
        nc = dashed(ax, norm_pdf, -6, 6, INK, width=3)
        cap = mixed("$n=4$", " 的 t 统计量（模拟 4000 次）", size=26, color=INDIGO).move_to(UP * 1.95)
        self.play(FadeIn(cap), run_time=0.4)
        hs = None
        for m in (200, 800, 4000):
            h = hist(ax, np.clip(ts[:m], -6, 6), -6, 6, 48, INDIGO)
            if hs is None:
                hs = h
                self.play(FadeIn(h, lag_ratio=0.05), run_time=0.9)
            else:
                self.play(Transform(hs, h), run_time=0.7)
        self.play(Create(nc), run_time=0.9)
        nlab = T("虚线：标准正态", 22, INK).move_to(ax.c2p(3.6, 0.36))
        self.play(FadeIn(nlab), run_time=0.4)
        tail_r = SurroundingRectangle(VGroup(*[r for r in hs if r.get_center()[0] > ax.c2p(2.3, 0)[0]]),
                                      color=BRICK, buff=0.08)
        tail_l = SurroundingRectangle(VGroup(*[r for r in hs if r.get_center()[0] < ax.c2p(-2.3, 0)[0]]),
                                      color=BRICK, buff=0.08)
        self.play(Create(tail_l), Create(tail_r), run_time=0.8)
        heavy = T("尾巴更厚", 28, BRICK, bold=True).next_to(tail_r, UP, buff=0.1)
        self.play(FadeIn(heavy), run_time=0.4)
        q = ax.c2p(1.96, 0)
        qline = DashedLine(q, q + UP * 2.2, color=GOLD, stroke_width=3)
        qlab = M("1.96", 26, GOLD).next_to(qline, UP, buff=0.08)
        self.play(Create(qline), FadeIn(qlab), run_time=0.6)
        frac = (np.abs(ts) > 1.96).mean()
        bad = mixed("超出 ±1.96 的比例：", f"${frac * 100:.0f}\\%$", "，而不是 5%", size=24, color=BRICK).move_to(
            ax.c2p(-3.4, 0.38))
        self.play(FadeIn(bad), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(hs, tail_l, tail_r, heavy, qline, qlab, bad, cap, nlab)), run_time=0.5)

        self.seg(3)
        nu_ = ValueTracker(1)
        cv = always_redraw(lambda: curve(ax, lambda x: t_pdf(x, nu_.get_value()), -6, 6, INDIGO, width=5))
        nl = always_redraw(lambda: M(r"\nu=" + f"{nu_.get_value():.0f}", 40, INDIGO).move_to(ax.c2p(-4.2, 0.36)))
        self.play(Create(cv), FadeIn(nl), run_time=0.8)
        cau = T("ν = 1：柯西分布", 26, BRICK, bold=True).move_to(ax.c2p(3.7, 0.25))
        self.play(FadeIn(cau, shift=LEFT * 0.2), run_time=0.5)
        self.wait(0.8)
        self.play(FadeOut(cau), run_time=0.3)
        ghosts = VGroup()
        for v in (2, 5, 30):
            ghosts.add(curve(ax, lambda x, v=v: t_pdf(x, v), -6, 6, tint(INDIGO, 0.35), width=2))
            self.play(nu_.animate.set_value(v), run_time=1.3)
            self.add(ghosts[-1])
            self.wait(0.3)
        close = T("ν ≥ 30：几乎就是正态", 26, INK).move_to(ax.c2p(3.7, 0.3))
        self.play(FadeIn(close), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, nc, cv, nl, ghosts, close)), run_time=0.5)

        self.seg(4)
        ci = M(r"\bar X\pm t_{n-1,\,0.975}\cdot\frac{S}{\sqrt n}", 54, INDIGO).move_to(UP * 1.6)
        self.play(Write(ci), run_time=1.3)
        nl2 = NumberLine(x_range=[-4, 4, 1], length=10, color=AXIS, include_numbers=False).move_to(DOWN * 1.2)
        c0 = nl2.n2p(0)
        unit = nl2.n2p(1)[0] - c0[0]
        self.play(Create(nl2), FadeIn(Dot(c0, color=INK)), run_time=0.6)

        def band(h, color, y, lab):
            r = Rectangle(width=2 * h * unit, height=0.32, fill_color=tint(color, 0.5), fill_opacity=1,
                          stroke_color=color, stroke_width=2).move_to(c0 + UP * y)
            t = VGroup(T(lab, 22, color, bold=True), M(f"\\pm{h:.2f}", 26, color)).arrange(RIGHT, buff=0.12)
            t.next_to(r, RIGHT, buff=0.3)
            return VGroup(r, t)
        bn = band(1.96, GREY, 0.75, "正态")
        bt = band(3.18, INDIGO, 0.0, "t, n=4")
        self.play(GrowFromCenter(bn[0]), FadeIn(bn[1]), run_time=0.8)
        self.play(GrowFromCenter(bt[0]), FadeIn(bt[1]), run_time=1.0)
        honest = T("小样本：区间更宽，也更诚实", 30, INDIGO, bold=True).to_edge(DOWN, buff=0.45)
        self.play(FadeIn(honest, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E7D(VScene):
    SID = "E7D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("F 分布：比较两组波动", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        rng = np.random.default_rng(3)
        g1 = rng.normal(0, 0.5, 10)
        g2 = rng.normal(0, 1.3, 10)
        rows = VGroup()
        for gname, data, c, y in (("甲组", g1, TEAL, 1.5), ("乙组", g2, BRICK, 0.4)):
            nl = NumberLine(x_range=[-3.5, 3.5, 1], length=7, color=AXIS, include_numbers=False).move_to(
                LEFT * 2.2 + UP * y)
            lab = T(gname, 24, c, bold=True).next_to(nl, LEFT, buff=0.3)
            ds = VGroup(*[Dot(nl.n2p(float(np.clip(v, -3.4, 3.4))), radius=0.09, color=c) for v in data])
            rows.add(VGroup(nl, lab, ds))
        for r in rows:
            self.play(Create(r[0]), FadeIn(r[1]), LaggedStart(*[FadeIn(d, shift=DOWN * 0.4) for d in r[2]],
                                                              lag_ratio=0.08), run_time=1.0)
        s1 = M(r"S_1^2", 40, TEAL).move_to(RIGHT * 3.6 + UP * 1.5)
        s2 = M(r"S_2^2", 40, BRICK).move_to(RIGHT * 3.6 + UP * 0.4)
        self.play(FadeIn(s1), FadeIn(s2), run_time=0.6)
        ratio = M(r"\frac{S_1^2}{S_2^2}", 48).move_to(RIGHT * 5.3 + UP * 0.95)
        self.play(TransformFromCopy(VGroup(s1, s2), ratio), run_time=0.9)
        f = M(r"F=\frac{U/d_1}{V/d_2}", 60, INDIGO).move_to(DOWN * 1.7 + LEFT * 2.0)
        uv = VGroup(mixed("$U\\sim\\chi^2_{d_1}$", ",  ", "$V\\sim\\chi^2_{d_2}$", size=26),
                    T("相互独立", 24, MUTED)).arrange(DOWN, buff=0.15).next_to(f, RIGHT, buff=0.6)
        self.play(Write(f), run_time=1.2)
        self.play(FadeIn(uv), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(rows, s1, s2, ratio, uv)), f.animate.scale(0.7).to_corner(UR, buff=0.35).shift(
            DOWN * 0.55), run_time=0.6)

        self.seg(1)
        ax = axes([0, 4.2, 1], [0, 1.6, 0.5], 7.0, 3.6, xnums=[0, 1, 2, 3, 4], ynums=[0.5, 1, 1.5],
                  xlabel="x").move_to(LEFT * 2.6 + DOWN * 0.5)
        self.play(Create(ax), run_time=0.6)
        cols = [TEAL, BRICK, INDIGO, GOLD]
        prs = [(1, 10), (3, 10), (10, 10), (20, 40)]
        cs = VGroup(*[curve(ax, lambda x, a=a, b=b: f_pdf(x, a, b), 0.02, 4.1, c, width=4, ymax=1.6)
                      for (a, b), c in zip(prs, cols)])
        lg = legend([(c, f"$F({a},{b})$") for (a, b), c in zip(prs, cols)], size=20).next_to(ax, UP, buff=0.0).align_to(
            ax, RIGHT).shift(DOWN * 0.9)
        self.play(LaggedStart(*[Create(c) for c in cs], lag_ratio=0.3), FadeIn(lg), run_time=2.0)
        rel = M(r"T_\nu^2\ \sim\ F(1,\nu)", 46, INDIGO).move_to(RIGHT * 3.9 + UP * 1.4)
        why = M(r"\Big(\frac{Z}{\sqrt{V/\nu}}\Big)^2=\frac{Z^2/1}{V/\nu}", 34).next_to(rel, DOWN, buff=0.3)
        self.play(Write(rel), run_time=1.0)
        self.play(FadeIn(why, shift=UP * 0.2), run_time=0.8)
        # 方差分析表示意
        tab = VGroup()
        heads = ["来源", "平方和", "自由度", "F"]
        body = [["组间", "SSB", "k−1", ""], ["组内", "SSW", "N−k", ""]]
        for j, h in enumerate(heads):
            tab.add(T(h, 20, INDIGO, bold=True).move_to(RIGHT * (2.4 + 1.2 * j) + DOWN * 0.9))
        for i, r in enumerate(body):
            for j, c in enumerate(r):
                if c:
                    tab.add(T(c, 20).move_to(RIGHT * (2.4 + 1.2 * j) + DOWN * (1.45 + 0.5 * i)))
        fv = M(r"\frac{SSB/(k-1)}{SSW/(N-k)}", 24, INDIGO).move_to(RIGHT * 6.0 + DOWN * 1.7)
        line = Line(RIGHT * 1.8 + DOWN * 1.17, RIGHT * 6.7 + DOWN * 1.17, color=FAINT)
        cap = T("方差分析表", 22, MUTED).next_to(tab, UP, buff=0.18)
        self.play(FadeIn(tab, lag_ratio=0.05), Create(line), FadeIn(fv), FadeIn(cap), run_time=1.2)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E7E(VScene):
    SID = "E7E"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("贝塔分布：排好队的均匀点", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        nl = NumberLine(x_range=[0, 1, 0.1], length=11, color=AXIS, include_numbers=False).move_to(UP * 0.9)
        ends = VGroup(M("0", 28, MUTED).next_to(nl.n2p(0), DOWN), M("1", 28, MUTED).next_to(nl.n2p(1), DOWN))
        self.play(Create(nl), FadeIn(ends), run_time=0.6)
        rng = np.random.default_rng(21)
        us = rng.uniform(0.04, 0.96, 7)
        drops = VGroup(*[Dot(nl.n2p(u) + UP * 2.2, radius=0.11, color=GREY) for u in us])
        self.play(LaggedStart(*[d.animate.move_to(nl.n2p(u)) for d, u in zip(drops, us)], lag_ratio=0.12),
                  run_time=1.4, rate_func=rate_functions.ease_out_bounce)
        order = np.argsort(us)
        tags = VGroup()
        for rank, idx in enumerate(order):
            tags.add(M(f"U_{{({rank + 1})}}", 24, MUTED).next_to(drops[idx], UP if rank % 2 == 0 else DOWN, buff=0.15))
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in tags], lag_ratio=0.1), run_time=1.2)
        third = drops[order[2]]
        self.play(third.animate.set_color(INDIGO).scale(1.5), tags[2].animate.set_color(INDIGO), run_time=0.6)
        q = mixed("第 3 小的点在哪里？", size=30, color=INDIGO).move_to(DOWN * 0.6)
        self.play(FadeIn(q, shift=UP * 0.2), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(q), run_time=0.3)

        self.seg(1)
        x0 = float(us[order[2]])
        bl = BraceBetweenPoints(nl.n2p(0), nl.n2p(x0), UP, color=TEAL).shift(UP * 0.55)
        br = BraceBetweenPoints(nl.n2p(x0), nl.n2p(1), UP, color=BRICK).shift(UP * 0.55)
        self.play(FadeOut(tags), run_time=0.3)
        tl = mixed("$k-1$", " 个点", size=24, color=TEAL).next_to(bl, UP, buff=0.1)
        tr = mixed("$n-k$", " 个点", size=24, color=BRICK).next_to(br, UP, buff=0.1)
        self.play(GrowFromCenter(bl), FadeIn(tl), run_time=0.7)
        self.play(GrowFromCenter(br), FadeIn(tr), run_time=0.7)
        dens = MathTex(r"f(x)\ \propto\ ", r"x^{k-1}", r"(1-x)^{n-k}", font_size=44).move_to(DOWN * 0.5 + LEFT * 2.8)
        dens[1].set_color(TEAL)
        dens[2].set_color(BRICK)
        self.play(Write(dens), run_time=1.3)
        be = M(r"\Rightarrow\ \mathrm{Beta}(k,\ n-k+1)", 40, INDIGO).next_to(dens, RIGHT, buff=0.3)
        self.play(FadeIn(be, shift=LEFT * 0.2), run_time=0.7)
        ax = axes([0, 1.02, 0.2], [0, 2.8, 1], 6.2, 2.3, xnums=[0, 0.5, 1], ynums=(), tips=False).move_to(
            DOWN * 2.35 + RIGHT * 2.6)
        U = np.sort(rng.uniform(0, 1, (3000, 7)), axis=1)[:, 2]
        self.play(Create(ax), run_time=0.5)
        hs = None
        for m in (150, 600, 3000):
            h = hist(ax, U[:m], 0, 1, 30, INDIGO)
            if hs is None:
                hs = h
                self.play(FadeIn(h, lag_ratio=0.05), run_time=0.8)
            else:
                self.play(Transform(hs, h), run_time=0.7)
        bc = curve(ax, lambda x: beta_pdf(x, 3, 5), 0, 1, GOLD, width=5)
        lab = mixed("$n=7,\\ k=3$", "：", "$\\mathrm{Beta}(3,5)$", size=22, color=GOLD).next_to(ax, LEFT, buff=0.3)
        self.play(Create(bc), FadeIn(lab), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(nl, ends, drops, bl, br, tl, tr, dens, be, ax, hs, bc, lab)), run_time=0.6)

        self.seg(2)
        ax = axes([0, 1.02, 0.25], [0, 3.2, 1], 7.0, 4.0, xnums=[0, 0.25, 0.5, 0.75, 1], ynums=[1, 2, 3],
                  xlabel="x").move_to(DOWN * 0.5 + LEFT * 2.0)
        a = ValueTracker(0.5)
        b = ValueTracker(0.5)
        cv = always_redraw(lambda: curve(ax, lambda x: beta_pdf(x, a.get_value(), b.get_value()), 0.004, 0.996,
                                         INDIGO, width=5, ymax=3.2))
        ar = always_redraw(lambda: area(ax, lambda x: beta_pdf(x, a.get_value(), b.get_value()), 0.004, 0.996,
                                        INDIGO, 0.15, ymax=3.2))
        lab = always_redraw(lambda: M(r"\alpha=" + f"{a.get_value():.1f}" + r",\ \beta=" + f"{b.get_value():.1f}",
                                      36, INDIGO).move_to(RIGHT * 4.4 + UP * 1.2))
        name = T("U 形", 30, INK, bold=True).move_to(RIGHT * 4.4 + UP * 0.3)
        self.play(Create(ax), FadeIn(cv), FadeIn(ar), FadeIn(lab), FadeIn(name), run_time=0.9)
        for (av, bv), nm in (((1, 1), "均匀"), ((4, 4), "单峰对称"), ((2, 6), "向左偏"), ((6, 1.6), "向右偏")):
            self.play(a.animate.set_value(av), b.animate.set_value(bv),
                      Transform(name, T(nm, 30, INK, bold=True).move_to(name)), run_time=1.4)
            self.wait(0.4)
        use = VGroup(T("住在 [0,1] 上", 26, MUTED), T("描述比例、概率本身", 26, MUTED)).arrange(DOWN, buff=0.12).move_to(
            RIGHT * 4.6 + DOWN * 0.9)
        self.play(FadeIn(use), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, cv, ar, lab, name, use)), run_time=0.5)

        self.seg(3)
        ax = axes([0, 1.02, 0.25], [0, 3.6, 1], 7.6, 3.6, xnums=[0, 0.25, 0.5, 0.75, 1], ynums=[1, 2, 3],
                  xlabel="p").move_to(DOWN * 0.9 + LEFT * 1.6)
        rule = mixed("$\\mathrm{Beta}(\\alpha,\\beta)$", "  看到 k 次成功、n−k 次失败  ",
                     "$\\Rightarrow\\ \\mathrm{Beta}(\\alpha+k,\\ \\beta+n-k)$", size=28, color=INDIGO).move_to(UP * 2.05)
        self.play(Write(rule), Create(ax), run_time=1.3)
        a = ValueTracker(2)
        b = ValueTracker(2)
        cv = always_redraw(lambda: curve(ax, lambda x: beta_pdf(x, a.get_value(), b.get_value()), 0.004, 0.996,
                                         INDIGO, width=5, ymax=3.6))
        ar = always_redraw(lambda: area(ax, lambda x: beta_pdf(x, a.get_value(), b.get_value()), 0.004, 0.996,
                                        INDIGO, 0.15, ymax=3.6))
        lab = always_redraw(lambda: M(r"\mathrm{Beta}(" + f"{a.get_value():.0f},{b.get_value():.0f}" + ")", 34,
                                      INDIGO).move_to(RIGHT * 4.6 + UP * 0.9))
        prior = curve(ax, lambda x: beta_pdf(x, 2, 2), 0.004, 0.996, GREY, width=2.5)
        self.play(FadeIn(cv), FadeIn(ar), FadeIn(lab), run_time=0.6)
        self.add(prior)
        seq = "成成败成成败成成败成"
        coins = VGroup(*[coin(c, r=0.22) for c in seq]).arrange_in_grid(2, 5, buff=0.12).move_to(RIGHT * 4.6 + DOWN * 0.8)
        step = max(0.55, (self.left() - 1.5) / len(seq))
        for i, c in enumerate(seq):
            cn = coins[i]
            if c == "败":
                cn[0].set_fill(tint(GREY, 0.6))
                cn[0].set_stroke(GREY)
            self.play(FadeIn(cn, scale=1.6), a.animate.increment_value(1 if c == "成" else 0),
                      b.animate.increment_value(0 if c == "成" else 1), run_time=step * 0.8)
        post = T("先验（灰）→ 后验：7 成 3 败", 24, MUTED).next_to(ax, UP, buff=0.05).align_to(ax, LEFT).shift(
            RIGHT * 0.6 + DOWN * 0.4)
        self.play(FadeIn(post), run_time=0.4)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, rule, cv, ar, lab, prior, coins, post)), run_time=0.5)

        self.seg(4)
        f = M(r"X\sim\Gamma(\alpha,\lambda),\quad Y\sim\Gamma(\beta,\lambda)", 40).move_to(UP * 1.5)
        self.play(Write(f), run_time=1.0)
        g = M(r"\frac{X}{X+Y}\ \sim\ \mathrm{Beta}(\alpha,\beta)", 54, INDIGO).move_to(UP * 0.0)
        self.play(TransformFromCopy(f, g), run_time=1.1)
        ind = mixed("且与 ", "$X+Y\\sim\\Gamma(\\alpha+\\beta,\\lambda)$", " 相互独立", size=30).move_to(DOWN * 1.3)
        self.play(FadeIn(ind, shift=UP * 0.2), run_time=0.7)
        # 两段等待拼成一根杆，分割点的位置就是比例
        bar_ = VGroup(Rectangle(width=4.2, height=0.3, fill_color=tint(BRICK, 0.6), fill_opacity=1, stroke_width=0),
                      Rectangle(width=2.6, height=0.3, fill_color=tint(TEAL, 0.6), fill_opacity=1, stroke_width=0)
                      ).arrange(RIGHT, buff=0).move_to(DOWN * 2.4)
        xl = M("X", 26, BRICK).next_to(bar_[0], DOWN, buff=0.1)
        yl = M("Y", 26, TEAL).next_to(bar_[1], DOWN, buff=0.1)
        self.play(GrowFromEdge(bar_[0], LEFT), FadeIn(xl), run_time=0.6)
        self.play(GrowFromEdge(bar_[1], LEFT), FadeIn(yl), run_time=0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)

        self.seg(5)
        pts = VGroup(*[Dot(radius=0.06, color=INDIGO) for _ in range(3)]).arrange(RIGHT, buff=1.4).move_to(UP * 0.3)
        lines = VGroup(*[Line(pts[i].get_center(), pts[j].get_center(), color=tint(INDIGO, 0.5), stroke_width=2)
                         for i, j in ((0, 1), (1, 2))])
        bells = VGroup()
        for p in pts:
            ax_ = Axes(x_range=[-3, 3], y_range=[0, 0.45], x_length=1.5, y_length=0.9, tips=False,
                       axis_config={"stroke_opacity": 0})
            c = ax_.plot(norm_pdf, color=INDIGO, stroke_width=3)
            bells.add(VGroup(ax_, c).next_to(p, UP, buff=0.1))
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in bells], lag_ratio=0.3), run_time=1.2)
        self.play(FadeIn(pts), Create(lines), run_time=0.8)
        nxt = T("下一集：多元正态与关系总图", 34, INDIGO, bold=True).move_to(DOWN * 1.4)
        self.play(FadeIn(nxt, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)
