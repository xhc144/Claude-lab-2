# -*- coding: utf-8 -*-
"""第 8 集：多元正态与关系总图——把所有分布连成一张网。"""
from common import *  # noqa: F401,F403

EP = 8
RNG = np.random.default_rng(8)
Z = RNG.standard_normal((260, 2))


def bvn_pdf(x, y, r):
    q = (x * x - 2 * r * x * y + y * y) / (1 - r * r)
    return math.exp(-q / 2) / (2 * math.pi * math.sqrt(1 - r * r))


def make_plane(center, size=5.4, rng=3.2):
    return NumberPlane(x_range=[-rng, rng, 1], y_range=[-rng, rng, 1], x_length=size, y_length=size,
                       background_line_style={"stroke_color": FAINT, "stroke_width": 1},
                       axis_config={"stroke_color": AXIS, "stroke_width": 2}).move_to(center)


def cloud(plane, r, color=INDIGO, opacity=0.6, radius=0.035):
    """按 X1 = Z1, X2 = ρZ1 + √(1−ρ²)Z2 由同一批标准正态点造出相关系数为 ρ 的点云。"""
    s = math.sqrt(1 - r * r)
    return VGroup(*[Dot(plane.c2p(z1, r * z1 + s * z2), radius=radius, color=color, fill_opacity=opacity)
                    for z1, z2 in Z])


def ellipse(plane, r, k, color=GOLD, width=3):
    """等高线：单位圆按同一个线性变换拉伸，半径 k。"""
    s = math.sqrt(1 - r * r)
    pts = [plane.c2p(k * math.cos(t), r * k * math.cos(t) + s * k * math.sin(t)) for t in np.linspace(0, TAU, 120)]
    m = VMobject(stroke_color=color, stroke_width=width)
    m.set_points_as_corners(pts)
    return m


def hist(ax, data, lo, hi, nb, color, opacity=0.45):
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


class E8A(V3Scene):
    SID = "E8A"

    def fixed(self, *mobs):
        self.add_fixed_in_frame_mobjects(*mobs)
        self.remove(*mobs)

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP, hold=1.2)
        self.remove(hdr)
        self.add_fixed_in_frame_mobjects(hdr)
        st = scene_title("高尔顿的身高数据", INDIGO)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        ax = axes([158, 184, 4], [158, 184, 4], 5.6, 4.6, xnums=[162, 170, 178], ynums=[162, 170, 178],
                  xlabel=T("父母平均身高", 20, INK), ylabel=T("子女身高", 20, INK), xnums_at=158).move_to(
            LEFT * 2.0 + DOWN * 0.5)
        self.play(Create(ax), run_time=0.8)
        par = 170 + 4 * Z[:, 0]
        kid = 170 + 4 * (0.5 * Z[:, 0] + math.sqrt(0.75) * Z[:, 1])
        dots = VGroup(*[Dot(ax.c2p(p, k), radius=0.04, color=INDIGO, fill_opacity=0.6)
                        for p, k in zip(par, kid) if 158 < p < 184 and 158 < k < 184])
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.008), run_time=2.0)
        el = VMobject(stroke_color=GOLD, stroke_width=4)
        el.set_points_as_corners([ax.c2p(170 + 8 * math.cos(t), 170 + 8 * (0.5 * math.cos(t) + math.sqrt(0.75) *
                                                                           math.sin(t))) for t in
                                  np.linspace(0, TAU, 120)])
        self.play(Create(el), run_time=1.2)
        name = T("二元正态分布", 36, INDIGO, bold=True).move_to(RIGHT * 4.0 + UP * 0.6)
        sub = T("倾斜的椭圆形点云", 24, MUTED).next_to(name, DOWN, buff=0.2)
        self.play(FadeIn(name, shift=LEFT * 0.3), FadeIn(sub), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, dots, el, name, sub)), run_time=0.6)
        self.remove(st)
        self.fixed(st)

        self.seg(1)
        r = 0.5
        ax3 = ThreeDAxes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[0, 1.3, 0.5], x_length=6, y_length=6,
                         z_length=3.0, axis_config={"color": AXIS, "stroke_width": 2})
        sc = 2 * math.pi * math.sqrt(1 - r * r)
        surf = Surface(lambda u, v: ax3.c2p(u, v, sc * bvn_pdf(u, v, r)), u_range=[-3, 3], v_range=[-3, 3],
                       resolution=(36, 36), fill_opacity=0.85, stroke_width=0.4, stroke_color=WHITE)
        surf.set_fill_by_checkerboard(tint(INDIGO, 0.75), tint(INDIGO, 0.55), opacity=0.9)
        s = math.sqrt(1 - r * r)
        rings = VGroup()
        for k in (0.8, 1.6, 2.4):
            m = VMobject(stroke_color=GOLD, stroke_width=3)
            m.set_points_as_corners([ax3.c2p(k * math.cos(t), r * k * math.cos(t) + s * k * math.sin(t), 0)
                                     for t in np.linspace(0, TAU, 100)])
            rings.add(m)
        VGroup(ax3, surf, rings).shift(DOWN * 0.5)
        self.move_camera(phi=62 * DEGREES, theta=-50 * DEGREES, run_time=1.2, added_anims=[FadeIn(ax3)])
        self.play(Create(surf), run_time=2.0)
        self.play(Create(rings), run_time=1.0)
        lab1 = T("俯视：等高线是椭圆", 24, GOLD, bold=True)
        lab2 = T("竖切：截面是钟形", 24, INDIGO, bold=True)
        labs = VGroup(lab1, lab2).arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(UR, buff=0.4).shift(DOWN * 0.6)
        self.fixed(labs)
        self.play(FadeIn(lab1), run_time=0.5)
        self.begin_ambient_camera_rotation(rate=0.22)
        self.wait(max(0.3, self.left() * 0.4))
        cut = Surface(lambda u, v: ax3.c2p(0.8, u, v * sc * bvn_pdf(0.8, u, r)), u_range=[-3, 3], v_range=[0, 1],
                      resolution=(40, 2), fill_opacity=0.9).shift(DOWN * 0.5)
        cut.set_fill(GOLD, opacity=0.85).set_stroke(GOLD, width=0.5)
        self.play(FadeIn(cut), surf.animate.set_fill(opacity=0.45), FadeIn(lab2), run_time=1.0)
        self.catch_up()
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(VGroup(ax3, surf, rings, cut, labs)), run_time=0.6)
        self.move_camera(phi=0, theta=-90 * DEGREES, run_time=0.6)

        self.seg(2)
        plane = make_plane(LEFT * 3.0 + DOWN * 0.4)
        rho = ValueTracker(0.0)
        dots = always_redraw(lambda: cloud(plane, rho.get_value()))
        els = always_redraw(lambda: VGroup(*[ellipse(plane, rho.get_value(), k) for k in (1, 2)]))
        rl = always_redraw(lambda: M(r"\rho=" + f"{rho.get_value():+.2f}", 52, INDIGO).move_to(RIGHT * 3.6 + UP * 1.2))
        self.play(FadeIn(plane), run_time=0.5)
        self.add(dots, els, rl)
        note = T("ρ = 0：等高线是圆", 26, INK).move_to(RIGHT * 3.6 + DOWN * 0.1)
        self.fixed(note)
        self.play(FadeIn(note), run_time=0.5)
        self.wait(0.8)
        n2 = T("ρ → 1：沿对角线拉长", 26, INK).move_to(note)
        self.play(rho.animate.set_value(0.8), FadeOut(note), run_time=2.0)
        self.fixed(n2)
        self.play(FadeIn(n2), run_time=0.4)
        self.wait(0.8)
        n3 = T("ρ < 0：朝另一边倾斜", 26, INK).move_to(note)
        self.play(rho.animate.set_value(-0.6), FadeOut(n2), run_time=2.4)
        self.fixed(n3)
        self.play(FadeIn(n3), run_time=0.4)
        self.catch_up()
        self.play(FadeOut(n3), rho.animate.set_value(0.0), run_time=1.0)

        self.seg(3)
        c1 = M(r"X_1=Z_1", 44).move_to(RIGHT * 3.6 + UP * 1.2)
        c2 = M(r"X_2=\rho Z_1+\sqrt{1-\rho^2}\,Z_2", 44).next_to(c1, DOWN, buff=0.3)
        c0 = mixed("$Z_1,Z_2$", " 独立标准正态", size=26, color=MUTED).next_to(c1, UP, buff=0.4)
        for m in (c0, c1, c2):
            self.fixed(m)
        self.play(FadeOut(rl), FadeIn(c0), run_time=0.5)
        self.play(Write(c1), run_time=0.8)
        self.play(Write(c2), run_time=1.2)
        self.play(rho.animate.set_value(0.7), run_time=2.4)
        chk = VGroup(M(r"\operatorname{Var}X_2=\rho^2+(1-\rho^2)=1", 32),
                     M(r"\operatorname{Cov}(X_1,X_2)=\rho", 32, GOLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        chk.next_to(c2, DOWN, buff=0.5)
        self.fixed(chk)
        self.play(FadeIn(chk[0], shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(chk[1], shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(c0, c1, c2, chk)), run_time=0.5)

        self.seg(4)
        g1 = M(r"\mathbf X=\boldsymbol\mu+L\mathbf Z,\qquad \Sigma=LL^{\mathsf T}", 40).move_to(RIGHT * 3.4 + UP * 1.7)
        g2 = M(r"f(\mathbf x)=\frac{1}{(2\pi)^{d/2}|\Sigma|^{1/2}}"
               r"e^{-\frac12(\mathbf x-\boldsymbol\mu)^{\mathsf T}\Sigma^{-1}(\mathbf x-\boldsymbol\mu)}", 32).next_to(
            g1, DOWN, buff=0.45)
        self.fixed(g1, g2)
        self.play(Write(g1), run_time=1.2)
        self.play(Write(g2), run_time=1.6)
        quad = SurroundingRectangle(g2[0][-18:], color=GOLD, buff=0.06)
        ql = T("只依赖这个二次型 → 等高面是椭球", 22, GOLD).next_to(g2, DOWN, buff=0.3)
        self.fixed(quad, ql)
        self.play(Create(quad), FadeIn(ql), run_time=0.8)
        # 主轴沿 Σ 的特征向量 (1,1) 和 (1,−1)
        r = 0.7
        a1 = math.sqrt(1 + r) * 2
        a2 = math.sqrt(1 - r) * 2
        ax_major = DoubleArrow(plane.c2p(-a1 / math.sqrt(2), -a1 / math.sqrt(2)),
                               plane.c2p(a1 / math.sqrt(2), a1 / math.sqrt(2)), buff=0, color=BRICK, stroke_width=4,
                               tip_length=0.18)
        ax_minor = DoubleArrow(plane.c2p(-a2 / math.sqrt(2), a2 / math.sqrt(2)),
                               plane.c2p(a2 / math.sqrt(2), -a2 / math.sqrt(2)), buff=0, color=TEAL, stroke_width=4,
                               tip_length=0.18)
        el2 = ellipse(plane, r, 2, GOLD, 5)
        ev = T("主轴 = Σ 的特征向量", 22, BRICK, bold=True).next_to(ql, DOWN, buff=0.25)
        self.fixed(ax_major, ax_minor, el2, ev)
        self.play(GrowFromCenter(ax_major), GrowFromCenter(ax_minor), Create(el2), FadeIn(ev), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(g1, g2, quad, ql, ax_major, ax_minor, el2, ev, plane, dots, els, st)), run_time=0.6)


class E8B(VScene):
    SID = "E8B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("等价定义与一个陷阱", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        r = 0.6
        plane = make_plane(LEFT * 3.2 + DOWN * 0.45, size=5.2)
        pts = np.column_stack([Z[:, 0], r * Z[:, 0] + math.sqrt(1 - r * r) * Z[:, 1]])
        dots = VGroup(*[Dot(plane.c2p(*p), radius=0.035, color=INDIGO, fill_opacity=0.45) for p in pts])
        self.play(FadeIn(plane), FadeIn(dots, lag_ratio=0.005), run_time=1.0)
        th = ValueTracker(0.0)

        def direction():
            return np.array([math.cos(th.get_value()), math.sin(th.get_value())])
        line = always_redraw(lambda: Line(plane.c2p(*(-3.1 * direction())), plane.c2p(*(3.1 * direction())),
                                          color=GOLD, stroke_width=4))
        proj = always_redraw(lambda: VGroup(*[Dot(plane.c2p(*((p @ direction()) * direction())), radius=0.03,
                                                  color=BRICK, fill_opacity=0.5) for p in pts[::2]]))
        hax = axes([-3.6, 3.7, 1], [0, 0.55, 0.1], 5.2, 2.6, xnums=(), ynums=(), tips=False).move_to(
            RIGHT * 3.6 + DOWN * 0.9)

        def hpanel():
            u = direction()
            v = pts @ u
            sd = math.sqrt(1 + 2 * r * u[0] * u[1])
            return VGroup(hist(hax, v, -3.6, 3.6, 24, BRICK),
                          curve(hax, lambda x: norm_pdf(x, 0, sd), -3.6, 3.6, INK, width=3))
        hp = always_redraw(hpanel)
        cap = mixed("投影 ", "$\\mathbf a^{\\mathsf T}\\mathbf X$", " 的分布", size=26).next_to(hax, UP, buff=0.3)
        self.play(Create(line), FadeIn(proj), Create(hax), FadeIn(hp), FadeIn(cap), run_time=1.0)
        self.play(th.animate.set_value(PI), run_time=max(4.0, self.left() * 0.55), rate_func=linear)
        defn = mixed("任何线性组合都是一元正态", size=26, color=INDIGO).move_to(RIGHT * 3.6 + UP * 1.75)
        self.play(FadeIn(defn, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(dots, line, proj, hax, hp, cap, defn)), run_time=0.5)

        self.seg(1)
        z = Z[:, 0]
        sgn = np.where(RNG.random(len(z)) < 0.5, -1.0, 1.0)
        y = sgn * z
        f = mixed("$Y=S\\cdot Z$", "，", "$S=\\pm1$", " 各一半，与 ", "$Z$", " 独立", size=24).move_to(
            RIGHT * 3.5 + UP * 1.75)
        self.play(FadeIn(f), run_time=0.6)
        dz = VGroup(*[Dot(plane.c2p(a, 0), radius=0.04, color=TEAL, fill_opacity=0.6) for a in z])
        self.play(FadeIn(dz, lag_ratio=0.003), run_time=0.8)
        dxy = VGroup(*[Dot(plane.c2p(a, b), radius=0.04, color=BRICK, fill_opacity=0.6) for a, b in zip(z, y)])
        self.play(Transform(dz, dxy), run_time=1.6)
        a1 = axes([-3.4, 3.5, 1], [0, 0.5, 0.1], 2.5, 1.5, tips=False).move_to(RIGHT * 2.2 + DOWN * 0.3)
        a2 = axes([-3.4, 3.5, 1], [0, 0.5, 0.1], 2.5, 1.5, tips=False).move_to(RIGHT * 5.1 + DOWN * 0.3)
        h1 = VGroup(hist(a1, z, -3.4, 3.4, 16, TEAL), curve(a1, norm_pdf, -3.4, 3.4, INK, width=2.5))
        h2 = VGroup(hist(a2, y, -3.4, 3.4, 16, BRICK), curve(a2, norm_pdf, -3.4, 3.4, INK, width=2.5))
        l1 = M("Z", 30, TEAL).next_to(a1, UP, buff=0.1)
        l2 = M("Y", 30, BRICK).next_to(a2, UP, buff=0.1)
        self.play(Create(a1), Create(a2), FadeIn(h1), FadeIn(h2), FadeIn(l1), FadeIn(l2), run_time=1.0)
        ok = T("各自都是标准正态", 24, INK).next_to(VGroup(a1, a2), DOWN, buff=0.3)
        self.play(FadeIn(ok), run_time=0.5)
        bad = T("但散点只在两条对角线上：不是椭圆", 24, BRICK, bold=True).next_to(ok, DOWN, buff=0.25)
        self.play(FadeIn(bad), Indicate(dz, color=BRICK, scale_factor=1.05), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(a1, a2, h1, h2, l1, l2, ok, bad, f)), run_time=0.5)

        self.seg(2)
        card1 = VGroup(T("联合正态", 26, INDIGO, bold=True),
                       mixed("不相关 ", "$\\Longleftrightarrow$", " 独立", size=28)).arrange(DOWN, buff=0.25)
        card2 = VGroup(T("上面的反例", 26, BRICK, bold=True),
                       mixed("$\\operatorname{Cov}(Z,Y)=E[S]\\,E[Z^2]=0$", size=22),
                       T("不相关，却不独立：|Y| = |Z|", 22, INK)).arrange(DOWN, buff=0.2)
        b1 = note_box(card1, INDIGO).move_to(RIGHT * 3.6 + UP * 1.0)
        b2 = note_box(card2, BRICK).move_to(RIGHT * 3.6 + DOWN * 1.3)
        self.play(FadeIn(b1, shift=LEFT * 0.3), run_time=0.7)
        self.wait(0.5)
        self.play(FadeIn(b2, shift=LEFT * 0.3), run_time=0.7)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


class E8C(VScene):
    SID = "E8C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("条件分布与回归", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        r = 0.6
        s = math.sqrt(1 - r * r)
        plane = make_plane(LEFT * 3.0 + DOWN * 0.45, size=5.6)
        els = VGroup(*[ellipse(plane, r, k, tint(INDIGO, 0.6), 2.5) for k in (1, 2, 2.8)])
        dots = cloud(plane, r, GREY, 0.35, 0.03)
        xl = M("x_1", 28).next_to(plane.c2p(3.2, 0), DOWN, buff=0.1)
        yl = M("x_2", 28).next_to(plane.c2p(0, 3.2), RIGHT, buff=0.1)
        self.play(FadeIn(plane), FadeIn(dots), Create(els), FadeIn(xl), FadeIn(yl), run_time=1.0)
        unit = plane.c2p(1, 0)[0] - plane.c2p(0, 0)[0]

        def side_bell(x1, color=GOLD, k=1.6, width=4):
            pts = [plane.c2p(x1, y) + RIGHT * unit * k * norm_pdf(y, r * x1, s) for y in np.linspace(-3.1, 3.1, 120)]
            m = VMobject(stroke_color=color, stroke_width=width)
            m.set_points_as_corners(pts)
            return m

        self.seg(0)
        x1 = 1.5
        cut = DashedLine(plane.c2p(x1, -3.2), plane.c2p(x1, 3.2), color=GOLD, stroke_width=3)
        self.play(Create(cut), run_time=0.7)
        bell = side_bell(x1)
        self.play(Create(bell), run_time=1.2)
        ctr = Dot(plane.c2p(x1, r * x1), radius=0.08, color=BRICK)
        self.play(FadeIn(ctr, scale=2), run_time=0.4)
        f = VGroup(M(r"X_2\mid X_1=x_1\ \sim\ N(\rho x_1,\ 1-\rho^2)", 38, INDIGO),
                   T("条件分布还是正态", 24, MUTED)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.6 + UP * 1.6)
        self.play(Write(f[0]), FadeIn(f[1]), run_time=1.4)
        self.catch_up()

        self.seg(1)
        xs = [-2.2, -1.1, 0.0, 1.1, 2.2]
        bells = VGroup(*[side_bell(x, tint(GOLD, 0.6), width=2.5) for x in xs])
        ctrs = VGroup(*[Dot(plane.c2p(x, r * x), radius=0.07, color=BRICK) for x in xs])
        self.play(FadeOut(cut), Transform(bell, side_bell(x1, tint(GOLD, 0.6), width=2.5)), run_time=0.4)
        self.play(LaggedStart(*[Create(b) for b in bells], lag_ratio=0.15), LaggedStart(*[FadeIn(c) for c in ctrs],
                                                                                       lag_ratio=0.15), run_time=1.6)
        reg = Line(plane.c2p(-3.2, -3.2 * r), plane.c2p(3.2, 3.2 * r), color=BRICK, stroke_width=5)
        self.play(Create(reg), run_time=1.0)
        rl = M(r"x_2=\rho x_1", 32, BRICK).next_to(plane.c2p(3.2, 3.2 * r), RIGHT, buff=0.12)
        self.play(FadeIn(rl), run_time=0.4)
        major = DashedLine(plane.c2p(-3.1, -3.1), plane.c2p(3.1, 3.1), color=INDIGO, stroke_width=3)
        ml = M(r"x_2=x_1", 28, INDIGO).next_to(plane.c2p(-2.9, -3.0), RIGHT, buff=0.15)
        self.play(Create(major), FadeIn(ml), run_time=0.9)
        txt = VGroup(T("回归线比主轴更平", 26, BRICK, bold=True),
                     T("父母特别高 → 子女平均也偏高，", 22, INK),
                     T("但没有那么高", 22, INK),
                     T("“向均值回归”", 26, GOLD, bold=True)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        txt.move_to(RIGHT * 3.6 + DOWN * 0.6)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in txt], lag_ratio=0.4), run_time=2.0)
        self.catch_up()
        self.play(FadeOut(txt), run_time=0.4)

        self.seg(2)
        braces = VGroup()
        for x in xs:
            lo = plane.c2p(x, r * x - s) + LEFT * 0.08
            hi = plane.c2p(x, r * x + s) + LEFT * 0.08
            braces.add(Line(lo, hi, color=TEAL, stroke_width=6))
        self.play(LaggedStart(*[Create(b) for b in braces], lag_ratio=0.15), run_time=1.2)
        var = VGroup(M(r"\operatorname{Var}(X_2\mid X_1)=1-\rho^2", 36, TEAL),
                     T("宽度处处一样，与 x₁ 无关", 24, INK)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.6 + DOWN * 0.6)
        self.play(FadeIn(var, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.6)


NODES = {
    "伯努利": (-5.9, 2.3, TEAL), "二项": (-3.5, 2.3, TEAL), "泊松": (-1.1, 2.3, TEAL), "指数": (1.3, 2.3, BRICK),
    "伽马": (3.6, 2.3, BRICK), "卡方": (5.8, 2.3, INDIGO),
    "几何": (-5.9, 0.7, TEAL), "负二项": (-5.9, -0.9, TEAL), "超几何": (-3.5, 0.7, TEAL),
    "韦布尔": (1.3, 0.9, BRICK), "正态": (0.0, -0.6, BRICK), "对数正态": (-2.6, -1.8, BRICK),
    "柯西": (-0.8, -2.6, BRICK), "t": (3.0, -1.0, INDIGO), "F": (5.8, -1.0, INDIGO),
    "均匀": (-5.9, -2.5, INK), "贝塔": (-3.6, -2.6, INDIGO),
}


def node(name):
    x, y, c = NODES[name]
    lab = T(name, 26 if name != "正态" else 34, INK, bold=True)
    box = RoundedRectangle(corner_radius=0.14, width=lab.width + 0.42, height=lab.height + 0.3, fill_color=tint(c, 0.16),
                           fill_opacity=1, stroke_color=c, stroke_width=2.5)
    return VGroup(box, lab.move_to(box)).move_to([x, y, 0])


class E8D(VScene):
    SID = "E8D"

    def edge(self, a, b, label="", color=None, dashed=False, side=UP):
        na, nb = self.nodes[a], self.nodes[b]
        c = color or NODES[b][2]
        if dashed:
            ar = DashedLine(na.get_center(), nb.get_center(), color=c, stroke_width=3, dash_length=0.1)
            ar.put_start_and_end_on(na.get_boundary_point(nb.get_center() - na.get_center()),
                                    nb.get_boundary_point(na.get_center() - nb.get_center()))
            ar.add_tip(tip_length=0.16)
        else:
            ar = Arrow(na.get_center(), nb.get_center(), buff=0, color=c, stroke_width=3.5, tip_length=0.18)
            ar.put_start_and_end_on(na.get_boundary_point(nb.get_center() - na.get_center()),
                                    nb.get_boundary_point(na.get_center() - nb.get_center()))
        g = VGroup(ar)
        if label:
            t = T(label, 16, MUTED)
            d = ar.get_end() - ar.get_start()
            ang = math.atan2(d[1], d[0])
            if abs(ang) > PI / 2:
                ang += PI
            t.rotate(ang).move_to(ar.get_center())
            normal = np.array([-math.sin(ang), math.cos(ang), 0])
            t.shift(normal * 0.2 * (1 if np.dot(normal, side) >= 0 else -1))
            g.add(t)
        return g

    def show(self, names, edges, run_time=None):
        anims = [FadeIn(self.nodes[n], scale=0.7) for n in names]
        gs = [self.edge(*e) for e in edges]
        self.edges.add(*gs)
        self.play(LaggedStart(*anims, *[Create(g[0]) for g in gs], *[FadeIn(g[1]) for g in gs if len(g) > 1],
                              lag_ratio=0.12), run_time=run_time or 2.2)

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("关系总图", INDIGO)
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        self.nodes = {n: node(n) for n in NODES}
        self.edges = VGroup()

        self.seg(0)
        self.play(FadeIn(self.nodes["伯努利"], scale=0.7), Flash(self.nodes["伯努利"], color=TEAL), run_time=0.8)
        self.show(["二项"], [("伯努利", "二项", "重复 n 次")], 1.0)
        self.show(["几何"], [("伯努利", "几何", "等第一次", None, False, LEFT)], 1.0)
        self.show(["负二项"], [("几何", "负二项", "r 个相加", None, False, LEFT)], 1.0)
        self.show(["超几何"], [("二项", "超几何", "不放回", None, False, RIGHT)], 1.0)
        self.catch_up()

        self.seg(1)
        self.show(["泊松"], [("二项", "泊松", "n→∞, np=λ")], 0.9)
        self.show(["指数"], [("泊松", "指数", "间隔")], 0.9)
        self.show(["伽马"], [("指数", "伽马", "相加")], 0.9)
        self.show(["卡方"], [("伽马", "卡方", "特例")], 0.9)
        self.catch_up()

        self.seg(2)
        nn = self.nodes["正态"]
        halo = glow(SurroundingRectangle(nn, buff=0.05, corner_radius=0.16, color=GOLD), GOLD, layers=5, width=26,
                    opacity=0.12)
        self.play(FadeIn(nn, scale=0.6), FadeIn(halo), run_time=0.9)
        self.show([], [("二项", "正态", "", GOLD, True), ("泊松", "正态", "", GOLD, True),
                       ("伽马", "正态", "", GOLD, True)], 1.4)
        clt = T("中心极限定理", 22, GOLD, bold=True).next_to(nn, UP, buff=0.35).shift(RIGHT * 1.1)
        self.play(FadeIn(clt), run_time=0.4)
        self.show(["t"], [("t", "正态", "ν→∞", GOLD, True)], 0.9)
        self.show([], [("正态", "卡方", "平方和", INDIGO)], 0.9)
        self.show(["F"], [("卡方", "t", "", INDIGO), ("卡方", "F", "比值")], 1.2)
        self.show(["对数正态", "柯西"], [("正态", "对数正态", "取指数", None, False, LEFT),
                                         ("正态", "柯西", "相除", None, False, RIGHT)], 1.4)
        self.catch_up()

        self.seg(3)
        self.show(["均匀", "贝塔"], [("均匀", "贝塔", "次序统计量", None, False, DOWN)], 1.2)
        self.show(["韦布尔"], [("指数", "韦布尔", "幂变换", None, False, LEFT)], 1.0)
        self.catch_up()

        self.seg(4)
        net = VGroup(*self.nodes.values(), self.edges, halo, clt)
        self.play(net.animate.scale(0.42).to_corner(DL, buff=0.35).set_opacity(0.35), run_time=1.0)
        items = [("无记忆", "离散只有几何\n连续只有指数", TEAL),
                 ("均值与方差独立", "只有正态总体", BRICK),
                 ("最大熵", "定均值和方差：\n正态的熵最大", GOLD),
                 ("可加性", "同率伽马、泊松、\n正态、卡方", INDIGO)]
        cards = VGroup()
        for head, body, c in items:
            h = T(head, 26, c, bold=True)
            b = Paragraph(*body.split("\n"), font=FONT, font_size=21, color=INK, line_spacing=0.8, alignment="center")
            inner = VGroup(h, b).arrange(DOWN, buff=0.22)
            box = RoundedRectangle(corner_radius=0.12, width=3.5, height=2.0, fill_color=tint(c, 0.12),
                                   fill_opacity=1, stroke_color=c, stroke_width=2)
            cards.add(VGroup(box, inner.move_to(box)))
        cards.arrange_in_grid(2, 2, buff=0.3).move_to(RIGHT * 2.2 + DOWN * 0.2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.35), run_time=2.4)
        self.catch_up()
        self.play(FadeOut(cards), FadeOut(net), FadeOut(st), run_time=0.7)

        self.seg(5)
        ax = axes([-4, 4.2, 1], [0, 0.45, 0.1], 11.0, 3.0, tips=False).move_to(DOWN * 1.3)
        ax.set_opacity(0)
        fs = [(lambda x: norm_pdf(x), BRICK), (lambda x: t_pdf(x, 2), INDIGO),
              (lambda x: chi2_pdf(x + 3.5, 4) * 1.6, INDIGO), (lambda x: gamma_pdf(x + 4, 2, 1.2) * 1.1, BRICK),
              (lambda x: beta_pdf((x + 4) / 8, 2, 5) / 8 * 1.6, PLUM), (lambda x: 0.4 * math.exp(-(x + 4)), BRICK)]
        cs = VGroup(*[curve(ax, f, -4, 4, c, width=3, ymax=0.45) for f, c in fs])
        self.play(LaggedStart(*[Create(c) for c in cs], lag_ratio=0.15), run_time=2.0)
        title = T("概率分布图鉴", 64, INK, bold=True).move_to(UP * 1.2)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=1.0)
        target = curve(ax, norm_pdf, -4, 4, GOLD, width=5)
        self.wait(max(0.3, self.left() - 3.5))
        self.play(*[Transform(c, target.copy()) for c in cs], run_time=1.6)
        thanks = T("谢谢观看", 36, MUTED).next_to(title, DOWN, buff=0.4)
        self.play(FadeIn(thanks, shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
