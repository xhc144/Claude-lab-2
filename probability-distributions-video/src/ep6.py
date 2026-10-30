# -*- coding: utf-8 -*-
"""第 6 集：钟形曲线从哪来——正态、对数正态与柯西。"""
from common import *  # noqa: F401,F403
from props import die

EP = 6


def dice_sum_dist(n):
    p = np.ones(6) / 6
    d = np.array([1.0])
    for _ in range(n):
        d = np.convolve(d, p)
    return {n + i: v for i, v in enumerate(d)}  # 点数和从 n 到 6n


def std_bars(ax, dist, mu, sd, color, unit=1.0):
    """把离散分布按 (x-μ)/σ 标准化后画成密度条（高度 × σ / 单位宽）。"""
    g = VGroup()
    for x, p in dist.items():
        z = (x - mu) / sd
        if -3.9 < z < 3.9:
            w = unit / sd
            lo, hi = ax.c2p(z - w / 2, 0), ax.c2p(z + w / 2, p * sd / unit)
            g.add(Rectangle(width=max(hi[0] - lo[0], 1e-3), height=max(hi[1] - lo[1], 1e-3), fill_color=tint(color, 0.5),
                            fill_opacity=1, stroke_color=color, stroke_width=0.8).move_to((lo + hi) / 2))
    return g


class E6A(VScene):
    SID = "E6A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP, hold=1.0)
        st = scene_title("加着加着就成了钟")
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        dl = VGroup(*[die(i, 0.55) for i in range(1, 7)]).arrange(RIGHT, buff=0.2).move_to(UP * 1.7)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dl], lag_ratio=0.1), run_time=1.0)
        self.catch_up()

        self.seg(1)
        ax = axes([-4, 4.2, 1], [0, 0.5, 0.1], 10.0, 3.8, xnums=(), ynums=(), tips=False)
        ax.move_to(DOWN * 0.8)
        self.play(FadeIn(ax), run_time=0.4)
        cur, lab, dice_row = None, None, None
        for n in (1, 2, 3, 5, 10):
            dist = dice_sum_dist(n)
            mu, sd = 3.5 * n, math.sqrt(35 / 12 * n)
            g = std_bars(ax, dist, mu, sd, INDIGO)
            nl = mixed("$n=" + str(n) + "$", " 个骰子", size=32, color=INDIGO).move_to(ax.c2p(-2.8, 0.45))
            row = VGroup(*[die((i * 3) % 6 + 1, 0.42) for i in range(min(n, 10))]).arrange(RIGHT, buff=0.1).move_to(
                UP * 1.7)
            if cur is None:
                cur, lab = g, nl
                self.play(FadeIn(g, lag_ratio=0.1), FadeIn(nl), ReplacementTransform(dl, row), run_time=1.2)
                dice_row = row
            else:
                self.play(Transform(cur, g), Transform(lab, nl), Transform(dice_row, row), run_time=1.5)
            self.wait(0.6)
        bell = curve(ax, norm_pdf, -3.9, 3.9, BRICK, width=4)
        self.play(Create(bell), run_time=1.0)
        self.catch_up()

        self.seg(2)
        self.play(FadeOut(VGroup(cur, lab, dice_row)), run_time=0.4)
        for name, maker, c in (("指数分布之和", lambda n: ("exp", n), BRICK), ("伯努利之和", lambda n: ("ber", n), TEAL)):
            title = T(name, 30, c, bold=True).move_to(UP * 1.8)
            self.play(FadeIn(title), run_time=0.4)
            g0 = None
            for n in (1, 3, 10, 40):
                if name.startswith("指数"):
                    sd = math.sqrt(n)
                    g = VGroup(curve(ax, lambda z, n=n: gamma_pdf(n + z * math.sqrt(n), n) * math.sqrt(n), -3.9, 3.9,
                                     c, width=4, ymax=0.5))
                else:
                    sd = math.sqrt(n * 0.3 * 0.7)
                    g = std_bars(ax, {k: binom_pmf(n, 0.3, k) for k in range(n + 1)}, n * 0.3, sd, c)
                g.add(M(f"n={n}", 30, c).move_to(ax.c2p(2.9, 0.45)))
                if g0 is None:
                    g0 = g
                    self.play(FadeIn(g), run_time=0.7)
                else:
                    self.play(Transform(g0, g), run_time=1.0)
                self.wait(0.25)
            self.play(FadeOut(g0), FadeOut(title), run_time=0.4)
        clt = T("中心极限定理", 40, GOLD, bold=True).move_to(UP * 1.8)
        self.play(FadeIn(clt, scale=1.2), bell.animate.set_stroke(width=7), run_time=0.8)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E6B(VScene):
    SID = "E6B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("中心极限定理")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        f = M(r"\frac{S_n-n\mu}{\sigma\sqrt n}\xrightarrow{\ d\ }N(0,1)", 58, GOLD).move_to(UP * 1.9)
        cond = T("独立同分布 · 方差有限", 24, MUTED).next_to(f, DOWN, buff=0.2)
        self.play(Write(f), FadeIn(cond), run_time=1.6)
        ax = axes([-4, 4.2, 1], [0, 0.48, 0.1], 9.6, 3.4, xnums=[-3, -2, -1, 0, 1, 2, 3], ynums=(), tips=False)
        ax.move_to(DOWN * 1.3)
        n = 12
        g1 = std_bars(ax, dice_sum_dist(n), 3.5 * n, math.sqrt(35 / 12 * n), INDIGO)
        g2 = curve(ax, lambda z: gamma_pdf(30 + z * math.sqrt(30), 30) * math.sqrt(30), -3.9, 3.9, BRICK, width=4)
        g3 = std_bars(ax, {k: binom_pmf(60, 0.3, k) for k in range(61)}, 18, math.sqrt(12.6), TEAL)
        self.play(Create(ax), FadeIn(g1), run_time=0.9)
        self.play(FadeIn(g3), Create(g2), run_time=1.2)
        bell = curve(ax, norm_pdf, -3.9, 3.9, INK, width=5)
        self.play(Create(bell), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(g1, g2, g3, bell, ax, cond)), f.animate.scale(0.6).to_corner(UR, buff=0.3).shift(DOWN * 0.5),
                  run_time=0.6)

        self.seg(1)
        ax2 = axes([-12, 12.5, 4], [0, 0.42, 0.1], 11.0, 3.5, xnums=[-12, -8, -4, 0, 4, 8, 12], ynums=(), tips=False)
        ax2.move_to(DOWN * 0.9)
        v = M(r"\operatorname{Var}S_n=n\sigma^2,\qquad \mathrm{sd}=\sigma\sqrt n", 42).move_to(UP * 1.75)
        self.play(Write(v), Create(ax2), run_time=1.2)
        cur = None
        for n in (1, 4, 16):
            g = curve(ax2, lambda x, n=n: norm_pdf(x, 0, math.sqrt(n)), -12, 12, TEAL, width=4)
            g = VGroup(g, M(f"n={n}", 30, TEAL).move_to(ax2.c2p(8, 0.35)))
            if cur is None:
                cur = g
                self.play(Create(g), run_time=0.8)
            else:
                self.play(Transform(cur, g), run_time=1.0)
        spread = T("不除：越摊越开", 26, BRICK, bold=True).move_to(ax2.c2p(-7.5, 0.33))
        self.play(FadeIn(spread), run_time=0.5)
        fixed = VGroup(curve(ax2, lambda x: norm_pdf(x, 0, 1), -12, 12, GOLD, width=5),
                       T("除以 √n：形状稳定", 26, GOLD, bold=True).move_to(ax2.c2p(-7.5, 0.25)))
        self.play(TransformFromCopy(cur, fixed), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, v, cur, spread, fixed)), run_time=0.5)

        self.seg(2)
        rows = VGroup(
            MathTex(r"M_{Z_n}(t)", r"=\Big[M\Big(\frac{t}{\sqrt n}\Big)\Big]^n", font_size=48),
            MathTex(r"=\Big[1+\frac{t^2}{2n}+o\Big(\frac1n\Big)\Big]^n", font_size=48),
            MathTex(r"\longrightarrow e^{t^2/2}", font_size=54),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to(LEFT * 1.4 + DOWN * 0.1)
        rows[1:].shift(RIGHT * 1.9)
        note0 = T("（不妨设 μ=0, σ=1）", 22, MUTED).next_to(rows[0], RIGHT, buff=0.4)
        self.play(Write(rows[0]), FadeIn(note0), run_time=1.4)
        self.wait(1.0)
        self.play(Write(rows[1]), run_time=1.4)
        br = Brace(rows[1], DOWN, color=MUTED)
        bl = T("一阶项是均值 0，二阶项是方差 1", 22, MUTED).next_to(br, DOWN, buff=0.1)
        self.play(GrowFromCenter(br), FadeIn(bl), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(br), FadeOut(bl), Write(rows[2]), rows[2].animate.set_color(GOLD), run_time=1.0)
        tag = T("= 标准正态的矩母函数", 26, GOLD, bold=True).next_to(rows[2], RIGHT, buff=0.4)
        self.play(FadeIn(tag), run_time=0.5)
        wash = T("高阶细节被抹平，只剩均值和方差", 28, INK, bold=True).move_to(DOWN * 2.6)
        self.play(FadeIn(wash, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E6C(V3Scene):
    SID = "E6C"

    def fixed(self, *mobs):
        self.add_fixed_in_frame_mobjects(*mobs)
        self.remove(*mobs)

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("正态密度里的 π")
        self.add_fixed_in_frame_mobjects(hdr)
        self.fixed(st)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        f = MathTex(r"\varphi(x)=", r"\frac{1}{\sqrt{2\pi}}", r"\,e^{-x^2/2}", font_size=72).move_to(UP * 0.4)
        self.fixed(f)
        self.play(Write(f), run_time=1.4)
        b1 = Brace(f[2], UP, color=BRICK)
        l1 = T("钟形：对称、快速衰减", 24, BRICK).next_to(b1, UP, buff=0.1)
        b2 = Brace(f[1], DOWN, color=INDIGO)
        l2 = T("让总面积等于 1", 24, INDIGO).next_to(b2, DOWN, buff=0.1)
        self.fixed(b1, l1, b2, l2)
        self.play(GrowFromCenter(b1), FadeIn(l1), run_time=0.8)
        self.wait(0.6)
        self.play(GrowFromCenter(b2), FadeIn(l2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(f, b1, l1, b2, l2)), run_time=0.5)

        self.seg(1)
        ax = ThreeDAxes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[0, 1.2, 0.5], x_length=6, y_length=6,
                        z_length=3.2, axis_config={"color": AXIS, "stroke_width": 2})
        surf = Surface(lambda u, v: ax.c2p(u, v, 2 * math.pi * norm_pdf(u) * norm_pdf(v)), u_range=[-3, 3],
                       v_range=[-3, 3], resolution=(36, 36), fill_opacity=0.85, stroke_width=0.4,
                       stroke_color=WHITE)
        surf.set_fill_by_checkerboard(tint(BRICK, 0.75), tint(BRICK, 0.55), opacity=0.9)
        g3 = VGroup(ax, surf).shift(DOWN * 0.6)
        self.move_camera(phi=62 * DEGREES, theta=-50 * DEGREES, run_time=1.2, added_anims=[FadeIn(ax)])
        self.play(Create(surf), run_time=2.0)
        eq = M(r"f(x,y)=\frac{1}{2\pi}e^{-(x^2+y^2)/2}", 40).to_corner(UR, buff=0.4).shift(DOWN * 0.6)
        lab = T("只依赖到原点的距离：旋转对称", 24, BRICK, bold=True).next_to(eq, DOWN, buff=0.2)
        self.fixed(eq, lab)
        self.play(FadeIn(eq), FadeIn(lab), run_time=0.8)
        self.begin_ambient_camera_rotation(rate=0.25)
        self.catch_up()

        self.seg(2)
        ring = Surface(lambda u, v: ax.c2p(u * math.cos(v), u * math.sin(v),
                                           2 * math.pi * norm_pdf(u) * norm_pdf(0)), u_range=[1.0, 1.25],
                       v_range=[0, TAU], resolution=(2, 48), fill_opacity=1)
        ring.set_fill(GOLD, opacity=1).set_stroke(GOLD, width=1)
        ring.shift(DOWN * 0.6)
        self.play(FadeIn(ring), surf.animate.set_fill(opacity=0.35), run_time=1.0)
        pol = M(r"\iint e^{-(x^2+y^2)/2}\,dx\,dy=\int_0^\infty e^{-r^2/2}\,2\pi r\,dr=2\pi", 40)
        pol2 = M(r"\Big(\int e^{-x^2/2}dx\Big)^2=2\pi\ \Rightarrow\ \int e^{-x^2/2}dx=\sqrt{2\pi}", 40, GOLD)
        VGroup(pol, pol2).arrange(DOWN, buff=0.3).to_edge(DOWN, buff=0.9)
        self.fixed(pol, pol2)
        bg = BackgroundRectangle(VGroup(pol, pol2), color=BG, fill_opacity=0.85, buff=0.15)
        self.fixed(bg)
        self.play(FadeIn(bg), Write(pol), run_time=1.6)
        self.wait(max(0.2, self.durs[2] * 0.45 - 2.6))
        self.play(Write(pol2), run_time=1.4)
        self.catch_up()
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(VGroup(ring, surf, ax, pol, pol2, bg, eq, lab)), run_time=0.7)
        self.move_camera(phi=0, theta=-90 * DEGREES, run_time=0.6)

        self.seg(3)
        h1 = M(r"f(x)\,f(y)=g(x^2+y^2)", 56).move_to(UP * 0.7)
        h2 = M(r"\Longrightarrow\ f(x)\propto e^{-c\,x^2}", 56, GOLD).move_to(DOWN * 0.6)
        who = VGroup(T("赫歇尔的问题", 28, INK, bold=True),
                     T("两个方向独立 + 只与距离有关", 24, MUTED)).arrange(DOWN, buff=0.15).move_to(UP * 2.0)
        self.fixed(who, h1, h2)
        self.play(FadeIn(who), run_time=0.7)
        self.play(Write(h1), run_time=1.3)
        self.wait(max(0.2, self.durs[3] * 0.5 - 2.0))
        self.play(Write(h2), run_time=1.2)
        only = T("满足这个函数方程的只有指数函数 → 只能是正态", 26, INK).move_to(DOWN * 1.6)
        self.fixed(only)
        self.play(FadeIn(only), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(who, h1, h2, only)), run_time=0.5)

        self.seg(4)
        ax2 = axes([-4, 4.2, 1], [0, 0.6, 0.1], 11.0, 3.6, xnums=(), ynums=(), xlabel="x")
        ax2.move_to(DOWN * 1.0)
        bell = curve(ax2, norm_pdf, -4, 4, BRICK, width=5)
        self.fixed(ax2, bell)
        self.play(Create(ax2), Create(bell), run_time=1.0)
        gen = M(r"X=\mu+\sigma Z\sim N(\mu,\sigma^2)", 40).move_to(UP * 2.0 + RIGHT * 2.5)
        self.fixed(gen)
        self.play(Write(gen), run_time=1.0)
        names = {-3: r"\mu-3\sigma", -2: r"\mu-2\sigma", -1: r"\mu-\sigma", 0: r"\mu", 1: r"\mu+\sigma",
                 2: r"\mu+2\sigma", 3: r"\mu+3\sigma"}
        ticks = VGroup(*[M(s_, 22, MUTED).next_to(ax2.c2p(k, 0), DOWN, buff=0.12) for k, s_ in names.items()])
        self.fixed(ticks)
        self.play(FadeIn(ticks), run_time=0.5)
        bands = []
        for k, op in ((1, 0.55), (2, 0.32), (3, 0.16)):
            bands.append(VGroup(area(ax2, norm_pdf, -k, -(k - 1), BRICK, opacity=op),
                                area(ax2, norm_pdf, k - 1, k, BRICK, opacity=op)) if k > 1 else
                         VGroup(area(ax2, norm_pdf, -1, 1, BRICK, opacity=op)))
        pcts = [T("68%", 30, WHITE, bold=True).move_to(ax2.c2p(0, 0.17)),
                T("95%", 26, BRICK, bold=True).move_to(ax2.c2p(-1.5, 0.48)),
                T("99.7%", 26, BRICK, bold=True).move_to(ax2.c2p(-2.6, 0.48))]
        for b_, p_ in zip(bands, pcts):
            self.fixed(b_, p_)
            self.play(FadeIn(b_), FadeIn(p_, scale=0.6), run_time=0.9)
            self.wait(0.4)
        q = mixed("95% 精确分位点：", "$\\pm1.96\\sigma$", size=26, color=GOLD).move_to(UP * 1.1 + RIGHT * 2.5)
        self.fixed(q)
        self.play(FadeIn(q), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, bell, gen, ticks, *bands, *pcts, q)), run_time=0.5)

        self.seg(5)
        lc = M(r"aX+bY\sim N\big(a\mu_1+b\mu_2,\ a^2\sigma_1^2+b^2\sigma_2^2\big)", 44).move_to(UP * 0.3)
        pre = mixed("$X,Y$", " 独立正态", size=30).next_to(lc, UP, buff=0.4)
        cen = T("误差 · 测量 · 统计推断的中心", 28, GOLD, bold=True).next_to(lc, DOWN, buff=0.6)
        self.fixed(lc, pre, cen)
        self.play(FadeIn(pre), Write(lc), run_time=1.5)
        self.play(FadeIn(cen), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(lc, pre, cen, st)), run_time=0.6)


class E6D(VScene):
    SID = "E6D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("乘法版本：对数正态")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        ax = axes([0, 10.4, 1], [0, 6.2, 1], 7.0, 4.4, xnums=[0, 5, 10], ynums=[1, 2, 4, 6], xlabel=T("年", 22, INK),
                  ylabel=T("财富（倍）", 20, INK))
        ax.move_to(LEFT * 2.8 + DOWN * 0.4)
        self.play(Create(ax), run_time=0.7)
        rng = np.random.default_rng(8)
        paths = VGroup()
        finals = []
        for _ in range(40):
            w, pts = 1.0, [ax.c2p(0, 1)]
            for yr in range(1, 11):
                w *= math.exp(rng.normal(0.03, 0.18))
                pts.append(ax.c2p(yr, min(w, 6.1)))
            finals.append(w)
            paths.add(VMobject(stroke_color=TEAL, stroke_width=1.8, stroke_opacity=0.6).set_points_as_corners(pts))
        self.play(LaggedStart(*[Create(p) for p in paths], lag_ratio=0.05), run_time=2.8)
        prod = M(r"W_{10}=R_1R_2\cdots R_{10}", 40).move_to(RIGHT * 3.6 + UP * 1.6)
        self.play(Write(prod), run_time=1.0)
        self.catch_up()

        self.seg(1)
        lg = M(r"\ln W_{10}=\ln R_1+\cdots+\ln R_{10}", 36).next_to(prod, DOWN, buff=0.45)
        arr = T("→ 和 → 近似正态", 26, GOLD, bold=True).next_to(lg, DOWN, buff=0.2)
        res = mixed("$W$", " 服从", "对数正态", size=30, color=BRICK).next_to(arr, DOWN, buff=0.35)
        self.play(Write(lg), run_time=1.2)
        self.play(FadeIn(arr), run_time=0.5)
        self.play(FadeIn(res), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, paths, prod, lg, arr, res)), run_time=0.5)

        self.seg(2)
        ax2 = axes([0, 4.15, 0.5], [0, 0.75, 0.25], 10.0, 3.8, xnums=[0, 1, 2, 3, 4], ynums=[0.25, 0.5], xlabel="x",
                   ylabel="f(x)")
        ax2.move_to(DOWN * 0.6)
        lp = lambda x: 0 if x <= 0 else math.exp(-(math.log(x)) ** 2 / 2) / (x * math.sqrt(2 * math.pi))  # noqa: E731
        cv = curve(ax2, lp, 0.01, 4.1, BRICK, width=5)
        self.play(Create(ax2), Create(cv), FadeIn(area(ax2, lp, 0.01, 4.1, BRICK, opacity=0.15)), run_time=1.2)
        marks = VGroup()
        for xv, name, tex in ((math.exp(-1), "众数", r"e^{\mu-\sigma^2}"), (1.0, "中位数", r"e^{\mu}"),
                              (math.exp(0.5), "均值", r"e^{\mu+\sigma^2/2}")):
            ln = DashedLine(ax2.c2p(xv, 0), ax2.c2p(xv, 0.72), color=INK, stroke_width=2)
            lab = VGroup(T(name, 22, INK, bold=True), M(tex, 26)).arrange(DOWN, buff=0.08).next_to(ax2.c2p(xv, 0.72), UP,
                                                                                                buff=0.05)
            marks.add(VGroup(ln, lab))
        self.play(LaggedStart(*[AnimationGroup(Create(m[0]), FadeIn(m[1])) for m in marks], lag_ratio=0.4),
                  run_time=2.0)
        inc = T("收入：平均数被少数高收入拉高，多数人在平均线以下", 24, BRICK, bold=True).move_to(DOWN * 2.85)
        self.play(FadeIn(inc), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E6E(VScene):
    SID = "E6E"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("反面典型：柯西分布")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        U = 1.5
        L = np.array([0, 1.4, 0])  # 灯塔
        shore_y = L[1] - U

        self.seg(0)
        sea = Rectangle(width=14.4, height=2.0, fill_color=tint(INDIGO, 0.12), fill_opacity=1, stroke_width=0).move_to(
            [0, shore_y + 1.0, 0])
        shore = Line([-7.2, shore_y, 0], [7.2, shore_y, 0], color=INK, stroke_width=4)
        sand = Rectangle(width=14.4, height=0.3, fill_color=tint(GOLD, 0.35), fill_opacity=1, stroke_width=0).next_to(
            shore, DOWN, buff=0)
        tower = VGroup(Polygon([-0.2, -0.35, 0], [0.2, -0.35, 0], [0.12, 0.35, 0], [-0.12, 0.35, 0],
                               fill_color=WHITE, fill_opacity=1, stroke_color=INK, stroke_width=2),
                       Rectangle(width=0.28, height=0.1, fill_color=BRICK, fill_opacity=1, stroke_width=0).move_to(UP * 0.05),
                       Circle(radius=0.1, fill_color=GOLD, fill_opacity=1, stroke_width=0).move_to(UP * 0.45)).move_to(L)
        dist = DoubleArrow(L + DOWN * 0.15, [0, shore_y, 0], buff=0, color=MUTED, stroke_width=2, tip_length=0.12)
        dl = T("1 公里", 20, MUTED).next_to(dist, RIGHT, buff=0.1)
        self.play(FadeIn(sea), Create(shore), FadeIn(sand), FadeIn(tower, shift=UP * 0.2), run_time=1.0)
        self.play(GrowFromCenter(dist), FadeIn(dl), run_time=0.6)
        rng = np.random.default_rng(4)
        thetas = rng.uniform(-math.pi / 2 * 0.97, math.pi / 2 * 0.97, 26)
        hits = VGroup()
        for i, th in enumerate(thetas):
            x = math.tan(th) * U
            end = np.array([max(-7.1, min(7.1, x)), shore_y, 0])
            if abs(x) > 7.1:
                end = L + (np.array([x, shore_y, 0]) - L) * (7.1 / abs(x))
            beam = Line(L + UP * 0.45, end, color=GOLD, stroke_width=3)
            self.play(ShowPassingFlash(beam.copy().set_stroke(GOLD, 6), time_width=0.8), run_time=0.25 if i > 3 else 0.6)
            if abs(x) <= 7.1:
                d = Dot([x, shore_y, 0], radius=0.07, color=BRICK)
                hits.add(d)
                self.add(d)
            else:
                ar = Arrow([math.copysign(6.4, x), shore_y - 0.45, 0], [math.copysign(7.1, x), shore_y - 0.45, 0],
                           buff=0, color=BRICK, stroke_width=3, max_tip_length_to_length_ratio=0.4)
                hits.add(ar)
                self.add(ar)
        self.catch_up()

        self.seg(1)
        th = 0.7
        x = math.tan(th) * U
        beam = Line(L + UP * 0.45, [x, shore_y, 0], color=GOLD, stroke_width=4)
        vert = DashedLine(L, [0, shore_y, 0], color=MUTED, stroke_width=2)
        ang = Arc(radius=0.8, start_angle=-PI / 2, angle=th, arc_center=L, color=INDIGO, stroke_width=3)
        thl = M(r"\theta", 32, INDIGO).move_to(L + 1.05 * np.array([math.sin(th / 2), -math.cos(th / 2), 0]))
        xl = M("X=\\tan\\theta", 32, BRICK).next_to([x, shore_y, 0], DOWN, buff=0.35)
        self.play(FadeOut(hits), FadeOut(dist), FadeOut(dl), Create(beam), Create(vert), Create(ang), FadeIn(thl),
                  run_time=1.0)
        self.play(FadeIn(xl), run_time=0.5)
        der = VGroup(M(r"\theta\sim U\big(-\tfrac{\pi}{2},\tfrac{\pi}{2}\big)", 34),
                     M(r"F(x)=P(\theta\le\arctan x)=\frac12+\frac{\arctan x}{\pi}", 34),
                     M(r"f(x)=\frac{1}{\pi(1+x^2)}", 40, BRICK)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        der.move_to(DOWN * 2.35)
        bg = BackgroundRectangle(der, color=BG, fill_opacity=0.9, buff=0.12)
        self.add(bg)
        for d_ in der:
            self.play(Write(d_), run_time=1.0)
            self.wait(0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(2)
        ax = axes([-8, 8.3, 2], [0, 0.42, 0.1], 11.0, 3.6, xnums=[-8, -4, 0, 4, 8], ynums=[0.1, 0.2, 0.3, 0.4], ydec=1,
                  xlabel="x")
        ax.move_to(DOWN * 0.5)
        nc = DashedVMobject(curve(ax, norm_pdf, -8, 8.2, INK, width=3), num_dashes=80)
        cc = curve(ax, lambda x: 1 / (math.pi * (1 + x * x)), -8, 8.2, BRICK, width=5)
        tails = VGroup(area(ax, lambda x: 1 / (math.pi * (1 + x * x)), -8, -3, BRICK, opacity=0.35),
                       area(ax, lambda x: 1 / (math.pi * (1 + x * x)), 3, 8.2, BRICK, opacity=0.35))
        self.play(Create(ax), Create(nc), Create(cc), run_time=1.3)
        lg = legend([(BRICK, "柯西"), (INK, "$N(0,1)$", "dash")]).move_to(ax.c2p(6, 0.33))
        self.play(FadeIn(tails), FadeIn(lg), run_time=0.8)
        div = M(r"\int_{-\infty}^{\infty}\frac{|x|}{\pi(1+x^2)}\,dx=\infty", 40).move_to(UP * 2.1)
        nm = T("均值不存在", 28, BRICK, bold=True).next_to(div, RIGHT, buff=0.4)
        self.wait(max(0.2, self.durs[2] * 0.5 - 2.1))
        self.play(Write(div), FadeIn(nm), run_time=1.2)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(3)
        axm = axes([0, 3.08, 1], [-4, 4.3, 2], 10.0, 4.2,
                   xnums=[(0, r"10^0"), (1, r"10^1"), (2, r"10^2"), (3, r"10^3")], ynums=[-4, -2, 0, 2, 4],
                   ylabel=r"\bar X_n", tips=False, xnums_at=-4)
        axm.move_to(LEFT * 0.6 + DOWN * 0.5)
        zero = DashedLine(axm.c2p(0, 0), axm.c2p(3.05, 0), color=GREY, stroke_width=1.5)
        rng = np.random.default_rng(245)
        c_, z_ = rng.standard_cauchy(1000), rng.standard_normal(1000)
        n_ = np.arange(1, 1001)
        mc, mz = np.cumsum(c_) / n_, np.cumsum(z_) / n_
        pc = VMobject(stroke_color=BRICK, stroke_width=3).set_points_as_corners(
            [axm.c2p(math.log10(n), float(np.clip(v, -4, 4))) for n, v in zip(n_, mc)])
        pz = VMobject(stroke_color=INK, stroke_width=3.5).set_points_as_corners(
            [axm.c2p(math.log10(n), float(np.clip(v, -4, 4))) for n, v in zip(n_, mz)])
        lgm = legend([(BRICK, "柯西的样本均值"), (INK, "正态的样本均值")]).move_to(axm.c2p(0.6, -3.0))
        self.play(Create(axm), Create(zero), FadeIn(lgm), run_time=0.8)
        self.play(Create(pz), Create(pc), run_time=5.5, rate_func=linear)
        res = VGroup(M(r"\bar X_n\sim\mathrm{Cauchy}", 34),
                     T("大数定律、中心极限定理都失效", 24, BRICK, bold=True),
                     T("“方差有限”一个字都不能少", 24, GOLD, bold=True)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        res.to_edge(RIGHT, buff=0.3).set_y(1.6)
        self.play(FadeIn(res, lag_ratio=0.3), run_time=1.2)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.6)

        self.seg(4)
        chips = VGroup()
        for name, tex in (("卡方", r"\chi^2_k"), ("t", r"t_\nu"), ("F", r"F(d_1,d_2)"), ("贝塔", r"\mathrm{Beta}")):
            box = RoundedRectangle(corner_radius=0.12, width=2.5, height=1.4, fill_color=tint(INDIGO, 0.12),
                                   fill_opacity=1, stroke_color=INDIGO, stroke_width=2)
            chips.add(VGroup(box, VGroup(T(name, 26, INK, bold=True), M(tex, 30, INDIGO)).arrange(DOWN, buff=0.12)
                             .move_to(box)))
        chips.arrange(RIGHT, buff=0.4).move_to(UP * 0.3)
        nt = T("下一集：从样本到推断", 30, INDIGO, bold=True).next_to(chips, DOWN, buff=0.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in chips], lag_ratio=0.25), run_time=1.4)
        self.play(FadeIn(nt), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
