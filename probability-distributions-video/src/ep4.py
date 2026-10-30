# -*- coding: utf-8 -*-
"""第 4 集：稀有事件——从二项到泊松。"""
import random

from common import *  # noqa: F401,F403

EP = 4
LAM = 4


def phone(r=0.22, color=TEAL):
    c = Circle(radius=r, fill_color=tint(color, 0.6), fill_opacity=1, stroke_color=color, stroke_width=2)
    return VGroup(c, Text("☎", font_size=int(r * 100), color=INK).move_to(c))


CALLS = [0.07, 0.21, 0.26, 0.48, 0.63, 0.88]  # 一小时里的来电时刻（占一小时的比例）


class E4A(VScene):
    SID = "E4A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP, hold=1.2)
        st = scene_title("把时间切细")
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        L, R, Y = -5.5, 5.5, 0.3
        tl = Line([L, Y, 0], [R, Y, 0], color=AXIS, stroke_width=4)
        t0 = T("0", 22, MUTED).next_to(tl.get_start(), DOWN, buff=0.15)
        t1 = T("1 小时", 22, MUTED).next_to(tl.get_end(), DOWN, buff=0.15)
        self.play(Create(tl), FadeIn(t0), FadeIn(t1), run_time=0.8)
        rings = VGroup(*[phone().move_to([L + c * (R - L), Y + 0.5, 0]) for c in CALLS])
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.3, scale=1.6) for r in rings], lag_ratio=0.3), run_time=2.0)
        q = mixed("平均每小时 ", "$\\lambda=4$", " 个电话；恰好 ", "$k$", " 个的概率？", size=30).move_to(DOWN * 1.6)
        self.play(FadeIn(q, shift=UP * 0.2), run_time=0.7)
        self.catch_up()

        self.seg(1)
        self.play(FadeOut(q), run_time=0.4)

        def cells(n, lit=True):
            g = VGroup()
            w = (R - L) / n
            for i in range(n):
                has = any(i * w <= (c * (R - L)) < (i + 1) * w for c in CALLS) and lit
                g.add(Rectangle(width=w, height=0.5, fill_color=GOLD if has else tint(TEAL, 0.12), fill_opacity=0.8 if has
                                else 1, stroke_color=TEAL, stroke_width=1.5 if n <= 60 else 0.4)
                      .move_to([L + (i + 0.5) * w, Y - 0.45, 0]))
            return g

        c10 = cells(10, lit=False)
        self.play(FadeIn(c10, lag_ratio=0.05), run_time=0.8)
        labs = VGroup(*[M(r"\tfrac{\lambda}{n}", 22, TEAL).move_to(c) for c in c10])
        self.play(FadeIn(labs), run_time=0.6)
        self.wait(0.6)
        self.play(Transform(c10, cells(10)), FadeOut(labs), run_time=0.8)
        rules = VGroup(T("每格最多一个电话，概率 λ/n", 24), T("各格相互独立", 24)).arrange(DOWN, aligned_edge=LEFT,
                                                                                              buff=0.15)
        rules.move_to(LEFT * 2.5 + DOWN * 1.9)
        appr = M(r"X\approx B\Big(n,\ \frac{\lambda}{n}\Big)", 46, TEAL).move_to(RIGHT * 3.2 + DOWN * 1.9)
        self.play(FadeIn(rules), run_time=0.7)
        self.play(Write(appr), run_time=1.0)
        self.catch_up()

        self.seg(2)
        self.play(FadeOut(rules), FadeOut(appr), rings.animate.shift(UP * 0.0), run_time=0.4)
        ax = axes([-0.6, 12.6, 1], [0, 0.3, 0.1], 7.2, 2.3, xnums=[0, 2, 4, 6, 8, 10, 12], ynums=(), xlabel="k",
                  tips=False, num_size=18)
        ax.move_to(DOWN * 2.0)
        ks = list(range(13))
        cur_b = bars(ax, ks, [binom_pmf(10, 0.4, k) for k in ks], TEAL, w=0.7, opacity=0.45)
        nl = M("n=10", 34, TEAL).move_to(ax.c2p(10.5, 0.24))
        self.play(FadeIn(ax), FadeIn(cur_b), FadeIn(nl), run_time=0.8)
        for n in (60, 600):
            self.play(Transform(c10, cells(n)), Transform(cur_b, bars(ax, ks, [binom_pmf(n, LAM / n, k) for k in ks],
                                                                      TEAL, w=0.7, opacity=0.45)),
                      Transform(nl, M(f"n={n}", 34, TEAL).move_to(nl)), run_time=1.3)
            self.wait(0.5)
        qq = M(r"n\to\infty\ ?", 40, GOLD).next_to(nl, UP, buff=0.3)
        self.play(FadeIn(qq), run_time=0.5)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.7)


class E4B(VScene):
    SID = "E4B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("取极限")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        f = MathTex(r"\binom{n}{k}\Big(\frac{\lambda}{n}\Big)^k", r"\Big(1-\frac{\lambda}{n}\Big)^{n}",
                    r"\Big(1-\frac{\lambda}{n}\Big)^{-k}", font_size=56).move_to(UP * 1.8)
        cols = [TEAL, BRICK, INDIGO]
        boxes = VGroup(*[SurroundingRectangle(f[i], color=c, buff=0.1, corner_radius=0.08) for i, c in enumerate(cols)])
        nums = VGroup(*[M(str(i + 1), 30, c).next_to(boxes[i], UP, buff=0.1)
                        for i, c in enumerate(cols)])
        self.play(Write(f), run_time=1.6)
        self.play(LaggedStart(*[AnimationGroup(Create(b), FadeIn(n_)) for b, n_ in zip(boxes, nums)],
                              lag_ratio=0.4), run_time=1.5)
        self.catch_up()

        self.seg(1)
        b1 = MathTex(r"=\frac{n(n-1)\cdots(n-k+1)}{n^k}", r"\cdot\frac{\lambda^k}{k!}", font_size=48)
        b1b = MathTex(r"=1\cdot\Big(1-\frac1n\Big)\cdots\Big(1-\frac{k-1}{n}\Big)", r"\cdot\frac{\lambda^k}{k!}",
                      r"\ \longrightarrow\ \frac{\lambda^k}{k!}", font_size=48)
        b1.move_to(DOWN * 0.1)
        b1b.move_to(DOWN * 1.5)
        self.play(Indicate(f[0], color=TEAL), run_time=0.6)
        self.play(TransformFromCopy(f[0], b1), run_time=1.5)
        self.wait(1.0)
        self.play(Write(b1b[0:2]), run_time=1.6)
        each = T("k 个因子，每个都 → 1", 24, TEAL, bold=True).next_to(b1b, DOWN, buff=0.3)
        self.play(FadeIn(each), run_time=0.6)
        self.play(Write(b1b[2]), b1b[2].animate.set_color(TEAL), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(b1, b1b, each)), run_time=0.5)

        self.seg(2)
        lim2 = MathTex(r"\Big(1-\frac{\lambda}{n}\Big)^{n}", r"\longrightarrow", r"e^{-\lambda}", font_size=52)
        lim2.move_to(LEFT * 3.2 + DOWN * 0.3)
        lim2[2].set_color(BRICK)
        ax = axes([0, 3.15, 1], [0, 0.06, 0.02], 5.4, 3.0, xnums=[(1, "10"), (2, "100"), (3, "1000")],
                  ynums=[(math.exp(-4), r"e^{-4}")], xlabel="n", tips=False, num_size=22)
        ax.move_to(RIGHT * 3.4 + DOWN * 0.6)
        ln = DashedLine(ax.c2p(0.5, math.exp(-4)), ax.c2p(3.1, math.exp(-4)), color=BRICK, stroke_width=2)
        dots = VGroup()
        for e in np.linspace(math.log10(5), 3.1, 30):
            n = 10 ** e
            dots.add(Dot(ax.c2p(e, (1 - 4 / n) ** n), radius=0.045, color=BRICK))
        self.play(TransformFromCopy(f[1], lim2[0]), run_time=1.0)
        self.play(Write(lim2[1:]), Create(ax), Create(ln), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(d, scale=2) for d in dots], lag_ratio=0.08), run_time=2.0)
        lab = mixed("λ = 4 时的数值", size=20, color=MUTED).move_to(ax.c2p(2.2, 0.012))
        edef = T("这正是 e 的定义", 24, BRICK, bold=True).next_to(lim2, DOWN, buff=0.35)
        self.play(FadeIn(lab), FadeIn(edef), run_time=0.6)
        lim3 = MathTex(r"\Big(1-\frac{\lambda}{n}\Big)^{-k}\longrightarrow 1", font_size=44, color=INDIGO)
        lim3.next_to(edef, DOWN, buff=0.45)
        self.wait(max(0.2, self.durs[2] * 0.7 - 6.4))
        self.play(TransformFromCopy(f[2], lim3), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(lim2, ax, ln, dots, lab, edef, lim3)), run_time=0.5)

        self.seg(3)
        res = MathTex(r"P(X=k)", r"=", r"e^{-\lambda}", r"\frac{\lambda^k}{k!}", font_size=72).move_to(DOWN * 0.3)
        res[2].set_color(BRICK)
        res[3].set_color(TEAL)
        self.play(Write(res[0:2]), run_time=0.7)
        self.play(TransformFromCopy(f[1], res[2]), TransformFromCopy(f[0], res[3]), run_time=1.4)
        gb = SurroundingRectangle(res, color=GOLD, buff=0.25, corner_radius=0.12, stroke_width=4)
        name = mixed("泊松分布 ", "$X\\sim P(\\lambda)$", "：λ = 单位时间内的平均次数", size=28).next_to(gb, DOWN, buff=0.4)
        self.play(Create(gb), run_time=0.8)
        self.play(FadeIn(name), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(f, boxes, nums, name)), VGroup(res, gb).animate.scale(0.6).move_to(UP * 2.2 + RIGHT * 3),
                  run_time=0.8)

        self.seg(4)
        s1 = MathTex(r"\sum_{k=0}^{\infty}e^{-\lambda}\frac{\lambda^k}{k!}", r"=e^{-\lambda}", r"\Big(1+\lambda+\frac{\lambda^2}{2!}+\cdots\Big)",
                     r"=e^{-\lambda}e^{\lambda}=1", font_size=48).move_to(DOWN * 0.2)
        self.play(Write(s1[0:2]), run_time=1.2)
        self.play(Write(s1[2]), run_time=1.2)
        br = Brace(s1[2], DOWN, color=TEAL)
        bl = M(r"e^{\lambda}", 36, TEAL).next_to(br, DOWN, buff=0.1)
        self.play(GrowFromCenter(br), FadeIn(bl), run_time=0.7)
        self.play(Write(s1[3]), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(s1, br, bl)), run_time=0.5)

        self.seg(5)
        cards = stat_cards([("期望", r"np=\lambda"), ("方差", r"np(1-p)\to\lambda")], TEAL, width=9.0, y=0.2,
                           value_size=40)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cards], lag_ratio=0.4), run_time=1.4)
        eq = T("均值 = 方差 = λ", 32, GOLD, bold=True).move_to(DOWN * 1.6)
        self.wait(max(0.2, self.durs[5] * 0.55 - 1.4))
        self.play(FadeIn(eq, scale=1.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(cards, eq, res, gb, st)), run_time=0.6)


class E4C(VScene):
    SID = "E4C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("泊松分布的样子和性质")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        ax = axes([0, 21, 1], [0, 0.4, 0.1], 10.4, 4.3, xnums=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                  ynums=[0.1, 0.2, 0.3], xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.45)
        lam = ValueTracker(1.0)
        ks = list(range(21))
        S = always_redraw(lambda: stems(ax, ks, [poisson_pmf(lam.get_value(), k) for k in ks], TEAL, dot_r=0.07,
                                        width=4))

        def band():
            l_ = lam.get_value()
            s = math.sqrt(l_)
            y = min(0.385, poisson_pmf(l_, int(l_)) + 0.05)
            return VGroup(DoubleArrow(ax.c2p(max(l_ - s, 0), y), ax.c2p(l_ + s, y), buff=0, color=GOLD,
                                      stroke_width=2.5, tip_length=0.12, max_tip_length_to_length_ratio=0.3),
                          M(r"\pm\sqrt{\lambda}", 26, GOLD).move_to(ax.c2p(l_, y + 0.03)))
        B = always_redraw(band)
        ll = VGroup(M(r"\lambda=", 40), DecimalNumber(1.0, num_decimal_places=1, font_size=40, color=INK)).arrange(
            RIGHT, buff=0.1).move_to(ax.c2p(17, 0.33))
        ll[1].add_updater(lambda m: m.set_value(lam.get_value()))
        self.play(Create(ax), FadeIn(S), FadeIn(ll), FadeIn(B), run_time=1.0)
        self.play(lam.animate.set_value(4), run_time=3.0, rate_func=smooth)
        self.play(lam.animate.set_value(10), run_time=3.0, rate_func=smooth)
        self.catch_up()
        ll[1].clear_updaters()
        self.play(FadeOut(VGroup(ax, S, B, ll)), run_time=0.5)

        self.seg(1)
        icons = VGroup()
        for sym, txt in (("✎", "一页书里的错别字"), ("☢", "一秒内衰变的原子"), ("◎", "一年里的大地震"),
                         ("♞", "骑兵被马踢死的人数")):
            box = RoundedRectangle(corner_radius=0.12, width=2.8, height=1.5, fill_color=tint(TEAL, 0.1), fill_opacity=1,
                                   stroke_color=TEAL, stroke_width=2)
            g = VGroup(Text(sym, font_size=44, color=TEAL), T(txt, 20, INK)).arrange(DOWN, buff=0.15).move_to(box)
            icons.add(VGroup(box, g))
        icons.arrange(RIGHT, buff=0.3).move_to(UP * 1.5)
        self.play(LaggedStart(*[FadeIn(i, shift=UP * 0.3) for i in icons], lag_ratio=0.3), run_time=2.0)
        # 博特基维茨（1898）：普鲁士 10 个骑兵军团 20 年，每军团每年被马踢死的人数
        obs = [109, 65, 22, 3, 1]
        ax2 = axes([-0.6, 4.6, 1], [0, 0.6, 0.2], 6.4, 2.5, xnums=[0, 1, 2, 3, 4], ynums=[0.2, 0.4], ydec=1,
                   xlabel=T("死亡人数", 18, INK), num_size=20)
        ax2.move_to(DOWN * 1.65 + LEFT * 1.4)
        ob = bars(ax2, list(range(5)), [o / 200 for o in obs], BRICK, w=0.5, opacity=0.5)
        fit = stems(ax2, list(range(5)), [poisson_pmf(0.61, k) for k in range(5)], INK, dot_r=0.07)
        self.wait(max(0.2, self.durs[1] * 0.45 - 2.0))
        self.play(Indicate(icons[3], color=BRICK), Create(ax2), FadeIn(ob, lag_ratio=0.2), run_time=1.2)
        self.play(FadeIn(fit), run_time=0.7)
        lg = legend([(BRICK, "实际：200 个军团·年", "bar"), (INK, "泊松 λ = 0.61", "dot")], size=18)
        lg.next_to(ax2, RIGHT, buff=0.4)
        self.play(FadeIn(lg), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(icons, ax2, ob, fit, lg)), run_time=0.5)

        self.seg(2)
        L, R = -4.2, 3.4

        def tline(y, c=AXIS):
            return Line([L, y, 0], [R, y, 0], color=c, stroke_width=2)
        rng = np.random.default_rng(3)
        e1, e2 = np.sort(rng.uniform(0, 1, 9)), np.sort(rng.uniform(0, 1, 7))
        y1, y2, y3 = 1.9, 0.9, -0.5
        l1, l2, l3 = tline(y1), tline(y2), tline(y3)
        lab1 = M(r"P(\lambda_1)", 28, TEAL).next_to(l1, LEFT, buff=0.2)
        lab2 = M(r"P(\lambda_2)", 28, BRICK).next_to(l2, LEFT, buff=0.2)
        d1 = VGroup(*[Dot([L + e * (R - L), y1, 0], radius=0.09, color=TEAL) for e in e1])
        d2 = VGroup(*[Dot([L + e * (R - L), y2, 0], radius=0.09, color=BRICK) for e in e2])
        self.play(Create(l1), Create(l2), FadeIn(lab1), FadeIn(lab2), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(d, scale=1.6) for d in [*d1, *d2]], lag_ratio=0.05), run_time=1.0)
        lab3 = M(r"P(\lambda_1+\lambda_2)", 28, INK).next_to(l3, LEFT, buff=0.2)
        self.play(Create(l3), FadeIn(lab3), *[d.animate.set_y(y3) for d in [*d1, *d2]], run_time=1.3)
        sup = M(r"P(\lambda_1)+P(\lambda_2)=P(\lambda_1+\lambda_2)", 34).move_to(DOWN * 1.6)
        self.play(FadeOut(VGroup(l1, l2, lab1, lab2)), Write(sup), run_time=1.0)
        self.catch_up()

        self.seg(3)
        self.play(FadeOut(sup), run_time=0.4)
        allp = sorted([*d1, *d2], key=lambda d: d.get_x())
        keep = [i % 3 == 1 for i in range(len(allp))]
        y4 = -1.7
        l4 = tline(y4, GREY)
        coin = T("每个电话以概率 p 是投诉", 24, MUTED).next_to(l3, UP, buff=0.3)
        self.play(FadeIn(coin), run_time=0.5)
        self.play(Create(l4), *[d.animate.set_color(GOLD).scale(1.2) for d, k in zip(allp, keep) if k],
                  *[d.animate.set_color(GREY).set_y(y4) for d, k in zip(allp, keep) if not k], run_time=1.3)
        kl = mixed("投诉 ", "$\\sim P(\\lambda p)$", size=24, color=GOLD).next_to(l3, RIGHT, buff=0.2)
        dl = mixed("其他 ", "$\\sim P(\\lambda(1-p))$", size=24, color=MUTED).next_to(l4, RIGHT, buff=0.2)
        self.play(FadeIn(kl), FadeIn(dl), run_time=0.6)
        ind = T("两者相互独立", 28, INK, bold=True).move_to(DOWN * 2.6)
        self.play(FadeIn(ind, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E4D(VScene):
    SID = "E4D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("泊松过程")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        ev = [0.35, 1.45, 1.85, 3.15, 3.65, 5.4, 5.95, 7.55, 8.9]

        self.seg(0)
        cax = axes([0, 10.3, 1], [0, 9.6, 2], 12.0, 3.4, xnums=(), ynums=[2, 4, 6, 8], ylabel="N(t)")
        cax.move_to(UP * 0.7)
        tl_y = -1.75
        x0 = cax.c2p(0, 0)[0]
        xu = cax.c2p(1, 0)[0] - x0
        tline = Arrow([x0 - 0.1, tl_y, 0], [x0 + 10.4 * xu, tl_y, 0], buff=0, color=AXIS, stroke_width=2,
                      max_tip_length_to_length_ratio=0.015)
        tl_lab = M("t", 28).next_to(tline, RIGHT, buff=0.1)
        t = ValueTracker(0)

        def path():
            g = VGroup()
            tv = t.get_value()
            pts = [0] + [e for e in ev if e <= tv]
            for i, a in enumerate(pts):
                b = pts[i + 1] if i < len(pts) - 1 else tv
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
                    g.add(phone(0.16).move_to([x0 + e * xu, tl_y, 0]))
                    g.add(DashedLine([x0 + e * xu, tl_y + 0.16, 0], cax.c2p(e, 0), color=GREY, stroke_width=1.2,
                                     dash_length=0.05))
            return g

        Pth, D = always_redraw(path), always_redraw(dots)
        cursor = always_redraw(lambda: Line([x0 + t.get_value() * xu, tl_y - 0.25, 0], cax.c2p(t.get_value(), 9.3),
                                            color=GOLD, stroke_width=1.5, stroke_opacity=0.7))
        self.play(Create(cax), GrowArrow(tline), FadeIn(tl_lab), run_time=1.0)
        self.add(Pth, D, cursor)
        self.play(t.animate.set_value(10), run_time=min(9.0, self.durs[0] * 0.55), rate_func=linear)
        self.remove(cursor)
        rules = VGroup(mixed("不重叠时间段的计数相互独立", size=22),
                       mixed("长度 ", "$t$", " 的时间段：计数 ", "$\\sim P(\\lambda t)$", size=22))
        rules.arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        rb = note_box(rules, TEAL, pad=0.2).move_to(cax.c2p(2.2, 7.3))
        self.play(FadeIn(rb), run_time=0.8)
        self.catch_up()

        self.seg(1)
        self.play(FadeOut(rb), run_time=0.4)
        wins = VGroup()
        for (a, b), c in (((1.0, 3.0), TEAL), ((5.2, 7.2), INDIGO)):
            r = Rectangle(width=(b - a) * xu, height=cax.c2p(0, 9.6)[1] - tl_y + 0.3, fill_color=c, fill_opacity=0.12,
                          stroke_width=0).move_to([x0 + (a + b) / 2 * xu, (cax.c2p(0, 9.6)[1] + tl_y - 0.3) / 2, 0])
            n = sum(1 for e in ev if a < e <= b)
            lab = mixed(f"{n} 个，", "$\\sim P(2\\lambda)$", size=20, color=c).next_to(r, UP, buff=0.05)
            wins.add(VGroup(r, lab))
        self.play(LaggedStart(*[FadeIn(w) for w in wins], lag_ratio=0.5), run_time=1.4)
        self.catch_up()

        self.seg(2)
        self.play(FadeOut(wins), run_time=0.4)
        braces = VGroup()
        for a, b, s in ((0, ev[0], "T_1"), (ev[0], ev[1], "T_2"), (ev[1], ev[2], "T_3"), (ev[2], ev[3], "T_4")):
            br = BraceBetweenPoints([x0 + a * xu, tl_y - 0.25, 0], [x0 + b * xu, tl_y - 0.25, 0], DOWN, color=GOLD,
                                    buff=0.02)
            br.stretch_to_fit_height(0.15)
            braces.add(VGroup(br, M(s, 26, GOLD).next_to(br, DOWN, buff=0.06)))
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in braces], lag_ratio=0.3), run_time=1.4)
        qq = mixed("间隔服从什么分布？", " ", "$\\to$", " 下一集：指数分布", size=28, color=GOLD).move_to(
            [x0 + 7.4 * xu, tl_y - 0.7, 0])
        self.play(FadeIn(qq, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
