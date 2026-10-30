# -*- coding: utf-8 -*-
from common import *


def bullet_list(items, size=32, color=INK, buff=0.35, mark_color=CYAN):
    rows = VGroup()
    for it in items:
        m = mono("▸", size * 0.8, mark_color)
        t = it if isinstance(it, Mobject) else zh(it, size, color)
        rows.add(VGroup(m, t).arrange(RIGHT, buff=0.2))
    return rows.arrange(DOWN, buff=buff, aligned_edge=LEFT)


# =====================================================================  05
class Ch05(Chapter):
    CH = 5

    def construct(self):
        self.intro_level()
        # s1: span
        self.at(1)
        V = texs(r"V(t) = ", r"t", r"+ t^{3}", r"- t^{4}", size=64)
        V.move_to(UP * 0.8)
        self.play(Write(V), run_time=1.0)
        lo = SurroundingRectangle(V[1], buff=0.1, color=SKY)
        hi = SurroundingRectangle(V[3], buff=0.1, color=MAGENTA)
        ll = tex(r"\min = 1", 36, SKY).next_to(lo, DOWN, buff=0.2)
        hl = tex(r"\max = 4", 36, MAGENTA).next_to(hi, DOWN, buff=0.2)
        self.play(Create(lo), FadeIn(ll), Create(hi), FadeIn(hl), run_time=0.9)
        sp = tex(r"\operatorname{span} V = \max - \min = 4 - 1 = 3", 48, GOLD).move_to(DOWN * 1.4)
        self.play(Write(sp), run_time=1.0)
        # s2: theorem
        self.at(2)
        self.play(FadeOut(VGroup(V, lo, hi, ll, hl, sp)), run_time=0.4)
        who = zh("考夫曼 · 村杉邦男 · 西斯尔斯韦特（1987）", 32, CYAN).move_to(UP * 1.9)
        card = panel(11.0, 2.6, GOLD, 0.07, 0.9).move_to(DOWN * 0.1)
        t1 = zh("D 连通、约化、交错，有 n 个交叉点", 36, INK).move_to(card.get_center() + UP * 0.55)
        t2 = tex(r"\Longrightarrow\quad \operatorname{span} V_L(t) = n", 60, GOLD).move_to(card.get_center() + DOWN * 0.55)
        self.play(FadeIn(who, shift=DOWN * 0.2), run_time=0.8)
        self.play(FadeIn(card), Write(t1), run_time=1.4)
        self.wait_to(self.S(2) + self.D(2) * 0.6)
        self.play(Write(t2), run_time=1.2)
        self.play(Indicate(t2, color=WHITE, scale_factor=1.08), run_time=0.8)
        # s3: extreme states
        self.at(3)
        self.play(FadeOut(VGroup(who, card, t1, t2)), run_time=0.4)
        tre = comps_of(trefoil_pts(300))
        xs = find_crossings(tre)
        sA, _ = resolve(tre, {k: "A" for k in range(3)})
        sB, _ = resolve(tre, {k: "B" for k in range(3)})
        f = tex(r"\langle D\rangle = \sum_{s} A^{\,a(s)-b(s)}\,\delta^{\,|s|-1}", 50).move_to(UP * 2.0)
        self.play(Write(f), run_time=1.4)
        dA = KnotDiagram(sA, scale=0.5, shift=LEFT * 4.3 + DOWN * 0.3, colors=[LIME, SKY, GOLD])
        dB = KnotDiagram(sB, scale=0.5, shift=RIGHT * 4.3 + DOWN * 0.3, colors=[MAGENTA, ORANGE, VIOLET])
        lA = VGroup(zh("全 A 状态", 30, LIME), tex(r"|s_A| = 2", 36)).arrange(DOWN, buff=0.15).next_to(dA, DOWN, buff=0.3)
        lB = VGroup(zh("全 B 状态", 30, MAGENTA), tex(r"|s_B| = 3", 36)).arrange(DOWN, buff=0.15).next_to(dB, DOWN, buff=0.3)
        self.play(Create(dA), FadeIn(lA), run_time=1.2)
        self.play(Create(dB), FadeIn(lB), run_time=1.2)
        mx = zh("最高次项", 28, LIME).next_to(dA, UP, buff=0.2)
        mn = zh("最低次项", 28, MAGENTA).next_to(dB, UP, buff=0.2)
        self.play(FadeIn(mx), FadeIn(mn), run_time=0.6)
        no = zh("约化交错 ⇒\n极端项不会抵消", 34, GOLD, line_spacing=1.0).move_to(DOWN * 0.3)
        self.wait_to(self.S(3) + self.D(3) * 0.7)
        self.play(FadeIn(no, scale=1.1), run_time=0.8)
        # s4: inequality chain
        self.at(4)
        self.play(FadeOut(VGroup(dA, dB, lA, lB, mx, mn, no)), run_time=0.4)
        e1 = tex(r"|s_A| + |s_B| \le n + 2", 48).move_to(UP * 0.7)
        e2 = tex(r"\operatorname{span}\langle D\rangle \le 2n + 2(|s_A|+|s_B|) - 4 \le 4n", 46).next_to(e1, DOWN, buff=0.35)
        e3 = tex(r"\Rightarrow\ \operatorname{span} V \le n", 50, CYAN).next_to(e2, DOWN, buff=0.35)
        self.play(Write(e1), run_time=1.0)
        self.play(Write(e2), run_time=1.4)
        self.play(Write(e3), run_time=0.8)
        res = zh("约化交错图：等号成立 ⇒ 交叉数 c(K) = n", 34, GOLD).next_to(e3, DOWN, buff=0.45)
        self.wait_to(self.S(4) + self.D(4) * 0.62)
        self.play(FadeIn(res, shift=UP * 0.2), run_time=0.8)
        st = stamp("TAIT ① ✓", LIME, 44).move_to(RIGHT * 4.6 + DOWN * 2.0)
        self.wait_to(self.E(4) - 1.0)
        self.play(FadeIn(st, scale=2), run_time=0.35, rate_func=rush_from)
        # s5: verify
        self.at(5)
        self.play(FadeOut(VGroup(f, e1, e2, e3, res, st)), run_time=0.4)
        k1 = KnotDiagram(comps_of(trefoil_pts()), scale=0.5, shift=LEFT * 3.3 + UP * 0.9, colors=[CYAN])
        k2 = KnotDiagram(comps_of(figure8_pts2()), scale=0.5, shift=RIGHT * 3.3 + UP * 0.9, colors=[MAGENTA])
        v1 = tex(r"t + t^{3} - t^{4}", 46, CYAN).next_to(k1, DOWN, buff=0.35)
        v2 = tex(r"t^{-2} - t^{-1} + 1 - t + t^{2}", 46, MAGENTA).next_to(k2, DOWN, buff=0.35)
        s1 = tex(r"\operatorname{span} = 4-1 = 3 = n", 40).next_to(v1, DOWN, buff=0.3)
        s2 = tex(r"\operatorname{span} = 2-(-2) = 4 = n", 40).next_to(v2, DOWN, buff=0.3)
        self.play(Create(k1), Write(v1), run_time=1.2)
        self.play(FadeIn(s1, shift=UP * 0.2), run_time=0.7)
        self.wait_to(self.S(5) + self.D(5) * 0.5)
        self.play(Create(k2), Write(v2), run_time=1.2)
        self.play(FadeIn(s2, shift=UP * 0.2), run_time=0.7)
        # s6: all three conjectures solved
        self.at(6)
        self.play(FadeOut(VGroup(k1, k2, v1, v2, s1, s2)), run_time=0.4)
        rows = VGroup()
        data = [("①", "交叉数最少", "1987", "KMT"), ("②", "扭数不变", "1987", "KMT"),
                ("③", "翻转猜想", "1993", "梅纳斯科–西斯尔斯韦特")]
        for n, name, yr, who_ in data:
            r = VGroup(mono(n, 36, GOLD), zh(name, 34, INK, weight=BOLD), mono(yr, 30, CYAN), zh(who_, 26, DIM))
            r[1].set(width=r[1].width)
            rows.add(r)
        for r in rows:
            r.arrange(RIGHT, buff=0.5)
        rows.arrange(DOWN, buff=0.55, aligned_edge=LEFT).move_to(LEFT * 0.8 + UP * 0.2)
        marks = VGroup(*[check_mark(size=0.5).next_to(r, RIGHT, buff=0.5) for r in rows])
        for i, (r, m) in enumerate(zip(rows, marks)):
            self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.6)
            if i < 2:
                self.play(FadeIn(m, scale=1.6), run_time=0.3)
        self.wait_to(self.S(6) + self.D(6) * 0.55)
        self.play(FadeIn(marks[2], scale=1.6), run_time=0.3)
        st = stamp("SOLVED", GOLD, 60).move_to(RIGHT * 4.2 + DOWN * 2.0)
        self.wait_to(self.E(6) - 1.2)
        self.play(FadeIn(st, scale=2.2), run_time=0.35, rate_func=rush_from)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  06
class Ch06(Chapter):
    CH = 6

    def construct(self):
        self.intro_level()
        # s1: genus-g surface with 2g curves
        self.at(1)
        S = seifert_schematic(0.85).move_to(LEFT * 3.3 + UP * 0.1)
        self.play(FadeIn(S, shift=UP * 0.3), run_time=1.2)
        a1 = tex("a_1", 40, RED_N).move_to(S.bands[0].point_from_proportion(0.3) + LEFT * 0.75)
        a2 = tex("a_2", 40, GOLD).move_to(S.bands[1].point_from_proportion(0.7) + RIGHT * 0.75)
        lab = VGroup(zh("亏格 g = 1", 32, INK), VGroup(tex(r"2g = 2", 40, INK), zh("条曲线", 32)).arrange(RIGHT, buff=0.15)).arrange(DOWN, buff=0.25)
        lab.move_to(RIGHT * 3.2 + UP * 0.8)
        self.play(FadeIn(a1), FadeIn(a2), FadeIn(lab), run_time=1.0)
        # s2: push-off and Seifert matrix
        self.at(2)
        push = S.curves[0][0].copy().set_stroke(RED_N, 3, 0.9)
        push = DashedVMobject(push.shift(UP * 0.18 + RIGHT * 0.12), num_dashes=40)
        pl = tex("a_1^{+}", 40, RED_N).next_to(a1, UP, buff=0.3)
        self.play(FadeOut(lab), Create(push), FadeIn(pl), run_time=1.4)
        Vij = tex(r"V_{ij} = \operatorname{lk}(a_i,\ a_j^{+})", 50).move_to(RIGHT * 3.2 + UP * 1.4)
        self.play(Write(Vij), run_time=1.2)
        M = tex(r"V = \begin{pmatrix} -1 & 1 \\ 0 & -1 \end{pmatrix}", 54, CYAN).move_to(RIGHT * 3.2 + DOWN * 0.6)
        self.wait_to(self.S(2) + self.D(2) * 0.6)
        self.play(Write(M), run_time=1.4)
        # s3: definition
        self.at(3)
        self.play(FadeOut(VGroup(S, a1, a2, push, pl)), Vij.animate.move_to(LEFT * 3.4 + UP * 1.8).scale(0.8),
                  M.animate.move_to(LEFT * 3.4 + UP * 0.2), run_time=0.8)
        D = tex(r"\Delta_K(t) = \det\!\left(V - tV^{\mathsf T}\right)", 60, GOLD).move_to(RIGHT * 2.4 + UP * 0.8)
        self.play(Write(D), run_time=1.5)
        eqv = VGroup(zh("换一个曲面，结果只差", 30, DIM), tex(r"\pm t^{n}", 40, DIM)).arrange(RIGHT, buff=0.2).next_to(D, DOWN, buff=0.5)
        self.wait_to(self.S(3) + self.D(3) * 0.5)
        self.play(FadeIn(eqv, shift=UP * 0.2), run_time=1.0)
        # s4: compute trefoil, figure eight
        self.at(4)
        self.play(FadeOut(VGroup(Vij, M, eqv)), D.animate.scale(0.75).to_edge(UP, buff=1.0), run_time=0.6)
        c1 = tex(r"\det\begin{pmatrix} t-1 & 1 \\ -t & t-1 \end{pmatrix} = t^{2} - t + 1", 46, CYAN)
        c2 = tex(r"\det\begin{pmatrix} t-1 & 1 \\ -t & 1-t \end{pmatrix} = -t^{2} + 3t - 1", 46, MAGENTA)
        k1 = KnotDiagram(comps_of(trefoil_pts()), scale=0.3, colors=[CYAN])
        k2 = KnotDiagram(comps_of(figure8_pts2()), scale=0.3, colors=[MAGENTA])
        r1 = VGroup(k1, c1).arrange(RIGHT, buff=0.6)
        r2 = VGroup(k2, c2).arrange(RIGHT, buff=0.6)
        VGroup(r1, r2).arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to(DOWN * 0.4)
        self.play(FadeIn(k1), Write(c1), run_time=1.6)
        self.wait_to(self.S(4) + self.D(4) * 0.55)
        self.play(FadeIn(k2), Write(c2), run_time=1.6)
        # s5: properties
        self.at(5)
        self.play(FadeOut(VGroup(r1, r2)), run_time=0.4)
        props = VGroup(tex(r"\Delta(t) \doteq \Delta(t^{-1})", 48), tex(r"\Delta(1) = \pm 1", 48),
                       tex(r"\operatorname{span}\Delta \le 2g(K)", 48, GOLD))
        props.arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(DOWN * 0.3)
        nums = VGroup(*[mono(f"{i}", 28, CYAN).next_to(p, LEFT, buff=0.5) for i, p in zip((1, 2, 3), props)])
        sd = self.D(5)
        for i, (p, n) in enumerate(zip(props, nums)):
            self.wait_to(self.S(5) + sd * [0.15, 0.45, 0.68][i])
            self.play(FadeIn(n), Write(p), run_time=0.9)
        # s6: genus bound for the trefoil
        self.at(6)
        self.play(FadeOut(VGroup(props[:2], nums)), props[2].animate.move_to(UP * 0.6), run_time=0.6)
        ch = tex(r"\operatorname{span}(t^2 - t + 1) = 2 \le 2g \ \Rightarrow\ g \ge 1", 46).next_to(props[2], DOWN, buff=0.5)
        fin = tex(r"g(3_1) = 1", 64, LIME).next_to(ch, DOWN, buff=0.5)
        self.play(Write(ch), run_time=1.4)
        self.wait_to(self.S(6) + self.D(6) * 0.6)
        self.play(FadeIn(fin, scale=1.4), run_time=0.7)
        self.play(Circumscribe(fin, color=LIME), run_time=1.0)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  07
class Ch07(Chapter):
    CH = 7

    def construct(self):
        self.intro_level()
        # s1: helix covering the circle
        self.at(1)
        R = rot_matrix(-1.15, 0, 0)
        sh = ValueTracker(0.0)
        th = np.linspace(-2 * PI, 2 * PI, 480)
        pitch = 0.25

        def helix():
            P = np.stack([1.6 * np.cos(th), 1.6 * np.sin(th), pitch * th + sh.get_value()], 1)
            Q = P @ R.T
            g = VGroup()
            for i in range(0, len(Q) - 1, 6):
                seg = Q[i:i + 7]
                col = grad_color([CYAN, MAGENTA, GOLD], (th[i] / TAU_) % 1)
                op = 0.35 + 0.65 * (np.clip(seg[:, 2].mean(), -2, 2) + 2) / 4
                m = VMobject().set_points_as_corners(np.column_stack([seg[:, :2], np.zeros(len(seg))]) * 1.0 + UP * 0.5)
                g.add(m.set_stroke(col, 5, op))
            return g

        hel = always_redraw(helix)
        circ_pts = np.stack([1.6 * np.cos(np.linspace(0, TAU_, 200)), 1.6 * np.sin(np.linspace(0, TAU_, 200)),
                             np.full(200, -3.0)], 1) @ R.T
        circle = VMobject().set_points_smoothly(np.column_stack([circ_pts[:, :2], np.zeros(200)]) + UP * 0.5)
        circle.set_stroke(SKY, 5)
        self.play(FadeIn(hel), Create(circle), run_time=1.4)
        lr = tex(r"\mathbb{R}", 50, CYAN).move_to(RIGHT * 3.0 + UP * 1.9)
        ls = tex(r"S^1", 50, SKY).move_to(RIGHT * 3.0 + DOWN * 1.9)
        arr = Arrow(lr.get_bottom(), ls.get_top(), color=DIM, buff=0.3)
        pl = tex(r"p", 40, DIM).next_to(arr, RIGHT, buff=0.15)
        self.play(FadeIn(lr), FadeIn(ls), GrowArrow(arr), FadeIn(pl), run_time=1.0)
        vt = ValueTracker(-2 * PI)

        def tracer():
            a = vt.get_value()
            P = np.array([1.6 * np.cos(a), 1.6 * np.sin(a), pitch * a + sh.get_value()]) @ R.T
            Q = np.array([1.6 * np.cos(a), 1.6 * np.sin(a), -3.0]) @ R.T
            p1 = np.array([P[0], P[1], 0]) + UP * 0.5
            p2 = np.array([Q[0], Q[1], 0]) + UP * 0.5
            return VGroup(DashedLine(p1, p2, dash_length=0.08).set_stroke(WHITE, 2, 0.6),
                          glow(Dot(p1, 0.09, color=WHITE), GOLD), glow(Dot(p2, 0.09, color=WHITE), SKY))

        tr = always_redraw(tracer)
        self.add(tr)
        self.play(vt.animate.set_value(2 * PI), run_time=max(2.0, self.E(1) - self.time - 0.3), rate_func=linear)
        # s2: deck transformation
        self.at(2)
        tl = tex(r"t:\ x \mapsto x + 1", 46, GOLD).move_to(LEFT * 4.2 + UP * 1.6)
        self.play(FadeIn(tl), run_time=0.6)
        for _ in range(2):
            self.play(sh.animate.increment_value(-pitch * TAU_), run_time=1.3)
        cov = zh("直线 = 圆周的无穷循环覆盖", 32, INK).move_to(LEFT * 3.8 + DOWN * 2.2)
        self.play(FadeIn(cov), run_time=0.6)
        # s3: knot complement cut along the Seifert surface
        self.at(3)
        self.play(FadeOut(frozen(hel, tr)), FadeOut(VGroup(circle, lr, ls, arr, pl, tl, cov)), run_time=0.5)
        kd = KnotDiagram(comps_of(trefoil_pts()), scale=0.45, shift=LEFT * 4.2 + UP * 0.6, colors=[MAGENTA])
        kt = tex(r"X = S^3 - N(K)", 40).next_to(kd, DOWN, buff=0.3)
        self.play(Create(kd), FadeIn(kt), run_time=1.2)
        arr2 = Arrow(LEFT * 2.2 + UP * 0.6, LEFT * 0.6 + UP * 0.6, color=GOLD)
        cut = zh("沿 F 剪开", 28, GOLD).next_to(arr2, UP, buff=0.1)
        self.play(GrowArrow(arr2), FadeIn(cut), run_time=0.6)

        def block(label, w=3.4, h=1.0):
            body = RoundedRectangle(width=w, height=h, corner_radius=0.18).set_fill("#10233d", 1).set_stroke(SKY, 2)
            top = Line(body.get_corner(UL) + RIGHT * 0.18, body.get_corner(UR) + LEFT * 0.18).set_stroke(CYAN, 6)
            bot = Line(body.get_corner(DL) + RIGHT * 0.18, body.get_corner(DR) + LEFT * 0.18).set_stroke(MAGENTA, 6)
            t = tex(label, 38).move_to(body)
            return VGroup(body, top, bot, t)

        b0 = block("X_0").move_to(RIGHT * 1.6 + UP * 0.6)
        fp = tex("F_+", 34, CYAN).next_to(b0, RIGHT, buff=0.2).align_to(b0, UP)
        fm = tex("F_-", 34, MAGENTA).next_to(b0, RIGHT, buff=0.2).align_to(b0, DOWN)
        self.play(FadeIn(b0, scale=0.8), FadeIn(fp), FadeIn(fm), run_time=1.0)
        # s4: stack infinitely many copies
        self.at(4)
        self.play(FadeOut(VGroup(kd, kt, arr2, cut, fp, fm)), b0.animate.move_to(ORIGIN + UP * 0.2), run_time=0.6)
        blocks = {0: b0}
        for i in (1, -1, 2, -2):
            b = block(f"X_{{{i}}}").move_to(UP * (0.2 + i * 1.05))
            blocks[i] = b
        self.play(LaggedStart(*[FadeIn(blocks[i], shift=UP * 0.3 * np.sign(i)) for i in (1, -1, 2, -2)], lag_ratio=0.3),
                  run_time=1.6)
        dots = VGroup(tex(r"\vdots", 50).next_to(blocks[2], UP, buff=0.05), tex(r"\vdots", 50).next_to(blocks[-2], DOWN, buff=0.05))
        glue = VGroup(*[Line(blocks[i].get_top() + LEFT * 1.5, blocks[i].get_top() + RIGHT * 1.5).set_stroke(WHITE, 4, 0.8)
                        for i in (-2, -1, 0, 1)])
        self.play(FadeIn(dots), Create(glue), run_time=0.8)
        tilde = tex(r"\widetilde{X}_\infty", 56, GOLD).move_to(RIGHT * 4.0 + UP * 0.2)
        self.play(Write(tilde), run_time=0.8)
        # s5: deck transformation t, Alexander module
        self.at(5)
        tarrs = VGroup(*[CurvedArrow(blocks[i].get_left() + LEFT * 0.1, blocks[i + 1].get_left() + LEFT * 0.1, angle=-1.6,
                                     color=GOLD) for i in (-2, -1, 0, 1)])
        tlab = tex("t", 44, GOLD).next_to(tarrs, LEFT, buff=0.2)
        self.play(Create(tarrs), FadeIn(tlab), run_time=1.0)
        all_b = VGroup(*blocks.values())
        self.play(all_b.animate.shift(UP * 1.05), run_time=0.8, rate_func=there_and_back)
        mod = tex(r"H_1(\widetilde{X}_\infty)", 46).move_to(RIGHT * 4.0 + DOWN * 0.8)
        lam = VGroup(tex(r"\mathbb{Z}[t, t^{-1}]", 40, CYAN), zh("上的模", 30, CYAN)).arrange(RIGHT, buff=0.1).next_to(mod, DOWN, buff=0.3)
        self.wait_to(self.S(5) + self.D(5) * 0.45)
        self.play(Write(mod), run_time=0.9)
        self.play(FadeIn(lam, shift=UP * 0.2), run_time=0.7)
        am = zh("亚历山大模", 32, GOLD).next_to(lam, DOWN, buff=0.3)
        self.play(FadeIn(am), run_time=0.5)
        # s6: order = Alexander polynomial
        self.at(6)
        self.play(FadeOut(VGroup(all_b, dots, glue, tarrs, tlab, tilde, mod, lam, am)), run_time=0.5)
        e1 = tex(r"\operatorname{ord} H_1(\widetilde{X}_\infty) = \Delta_K(t)", 56, GOLD).move_to(UP * 0.9)
        e2 = VGroup(zh("展示矩阵：", 36, CYAN), tex(r"V - tV^{\mathsf T}", 52, CYAN)).arrange(RIGHT, buff=0.2).next_to(e1, DOWN, buff=0.6)
        self.play(Write(e1), run_time=1.4)
        self.wait_to(self.S(6) + self.D(6) * 0.4)
        self.play(Write(e2), run_time=1.4)
        geo = VGroup(zh("几何", 34, MAGENTA), tex(r"\Longleftrightarrow", 50), zh("代数", 34, CYAN)).arrange(RIGHT, buff=0.4)
        geo.next_to(e2, DOWN, buff=0.6)
        self.wait_to(self.S(6) + self.D(6) * 0.75)
        self.play(FadeIn(geo, scale=1.2), run_time=0.7)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  08
class Ch08(Chapter):
    CH = 8

    def construct(self):
        self.intro_level()
        g = lambda k: glyph(k, 0.75, CYAN)
        # s1: Conway skein relation
        self.at(1)
        sk = row(r"\nabla\Big(", g("pos"), r"\Big) - \nabla\Big(", g("neg"), r"\Big) = z\,\nabla\Big(", g("zero"),
                 r"\Big)", size=46).move_to(UP * 0.6)
        lbls = VGroup(tex("L_+", 32, GOLD).next_to(sk[1], DOWN, buff=0.1), tex("L_-", 32, GOLD).next_to(sk[3], DOWN, buff=0.1),
                      tex("L_0", 32, GOLD).next_to(sk[5], DOWN, buff=0.1))
        un = tex(r"\nabla(\bigcirc) = 1", 46).next_to(sk, DOWN, buff=1.0)
        yr = mono("CONWAY 1969", 28, MAGENTA).next_to(sk, UP, buff=0.6)
        self.play(FadeIn(yr), run_time=0.5)
        self.play(FadeIn(sk, shift=UP * 0.2), FadeIn(lbls), run_time=1.6)
        self.wait_to(self.S(1) + self.D(1) * 0.8)
        self.play(Write(un), run_time=0.8)
        # s2: skein tree for the trefoil
        self.at(2)
        self.play(FadeOut(VGroup(sk, lbls, un, yr)), run_time=0.4)
        tre = comps_of(trefoil_pts(320))
        Lm = flip_crossings(tre, [0])
        L0, _ = resolve(tre, {0: "O"})
        H = L0
        Hx = find_crossings(H)
        Hm = flip_crossings(H, [0])
        H0, _ = resolve(H, {0: "O"})
        sc = 0.28
        top = KnotDiagram(tre, scale=sc, shift=UP * 1.8, colors=[CYAN], width=5)
        n1 = KnotDiagram(Lm, scale=sc, shift=LEFT * 3.0 + DOWN * 0.2, colors=[CYAN], width=5)
        n2 = KnotDiagram(H, scale=sc, shift=RIGHT * 2.2 + DOWN * 0.2, colors=[GOLD, LIME], width=5)
        n3 = KnotDiagram(Hm, scale=sc, shift=RIGHT * 0.4 + DOWN * 2.2, colors=[GOLD, LIME], width=5)
        n4 = KnotDiagram(H0, scale=sc, shift=RIGHT * 4.0 + DOWN * 2.2, colors=[GOLD], width=5)
        e = lambda a, b, txt: VGroup(Line(a.get_bottom(), b.get_top(), buff=0.12).set_stroke(DIM, 2),
                                     tex(txt, 30, GOLD).move_to((a.get_bottom() + b.get_top()) / 2 + RIGHT * 0.35))
        e1, e2 = e(top, n1, "L_-"), e(top, n2, "L_0")
        e3, e4 = e(n2, n3, "L_-"), e(n2, n4, "L_0")
        v1 = tex("=1", 36, CYAN).next_to(n1, RIGHT, buff=0.15)
        v3 = tex("=0", 36, GOLD).next_to(n3, RIGHT, buff=0.15)
        v4 = tex("=1", 36, GOLD).next_to(n4, RIGHT, buff=0.15)
        hl = zh("霍普夫链环", 24, GOLD).next_to(n2, RIGHT, buff=0.15)
        sd = self.D(2)
        self.play(Create(top), run_time=0.8)
        self.play(Create(e1), Create(n1), Create(e2), Create(n2), run_time=1.2)
        self.play(FadeIn(v1), FadeIn(hl), run_time=0.5)
        self.wait_to(self.S(2) + sd * 0.45)
        self.play(Create(e3), Create(n3), Create(e4), Create(n4), run_time=1.2)
        self.play(FadeIn(v3), FadeIn(v4), run_time=0.5)
        vh = tex(r"\nabla(\text{Hopf}) = 0 + z\cdot 1 = z", 34, GOLD).move_to(LEFT * 3.6 + DOWN * 2.2)
        self.play(Write(vh), run_time=0.9)
        res = tex(r"\nabla(3_1) = 1 + z\cdot z = 1 + z^{2}", 40, CYAN).move_to(LEFT * 3.8 + UP * 1.8)
        self.wait_to(self.S(2) + sd * 0.82)
        self.play(Write(res), run_time=1.0)
        # s3: back to Alexander
        self.at(3)
        self.play(FadeOut(VGroup(top, n1, n2, n3, n4, e1, e2, e3, e4, v1, v3, v4, hl, vh)),
                  res.animate.move_to(UP * 1.6).scale(1.2), run_time=0.6)
        sub = tex(r"z = t^{1/2} - t^{-1/2}", 50, GOLD).move_to(UP * 0.2)
        fin = tex(r"1 + z^2 = 1 + (t - 2 + t^{-1}) = t - 1 + t^{-1} = \Delta(t)", 46).move_to(DOWN * 1.1)
        self.play(Write(sub), run_time=1.0)
        self.play(Write(fin), run_time=1.8)
        # s4: signature
        self.at(4)
        self.play(FadeOut(VGroup(res, sub, fin)), run_time=0.4)
        m = tex(r"V + V^{\mathsf T} = \begin{pmatrix} -2 & 1 \\ 1 & -2 \end{pmatrix}", 52).move_to(UP * 1.2)
        ev = VGroup(zh("特征值：", 30, DIM), tex(r"-1,\ -3", 42, DIM)).arrange(RIGHT, buff=0.15).next_to(m, DOWN, buff=0.4)
        sg = tex(r"\sigma(3_1) = 0 - 2 = -2", 52, CYAN).next_to(ev, DOWN, buff=0.45)
        mir = tex(r"\sigma(\overline{3_1}) = +2", 52, MAGENTA).next_to(sg, DOWN, buff=0.35)
        self.play(Write(m), run_time=1.4)
        self.wait_to(self.S(4) + self.D(4) * 0.45)
        self.play(FadeIn(ev), run_time=0.6)
        self.play(Write(sg), run_time=1.0)
        self.wait_to(self.S(4) + self.D(4) * 0.82)
        self.play(Write(mir), run_time=0.8)
        # s5: slice knots in the 4-ball
        self.at(5)
        self.play(FadeOut(VGroup(m, ev, sg, mir)), run_time=0.4)
        ball = Circle(radius=2.2).set_fill("#0e1f3a", 0.9).set_stroke(SKY, 3).move_to(LEFT * 2.6 + DOWN * 0.1)
        halo = glow(Circle(radius=2.2).set_stroke(SKY, 3).move_to(ball), SKY)
        lb = tex(r"B^4", 50, SKY).move_to(ball.get_center() + DOWN * 1.2)
        ls3 = tex(r"S^3 = \partial B^4", 40, SKY).next_to(ball, UP, buff=0.2)
        self.play(FadeIn(ball), FadeIn(halo), FadeIn(lb), FadeIn(ls3), run_time=1.0)
        # a disc dipping into the ball, bounded by a knot on the boundary
        top_c = ball.get_center() + UP * 1.75
        kn = KnotDiagram(comps_of(trefoil_pts()), scale=0.17, shift=top_c, colors=[GOLD], width=4)
        cap = VMobject().set_points_smoothly([top_c + LEFT * 0.5, ball.get_center() + LEFT * 0.4 + UP * 0.2,
                                              ball.get_center() + DOWN * 0.1, ball.get_center() + RIGHT * 0.4 + UP * 0.2,
                                              top_c + RIGHT * 0.5])
        cap.set_fill(GOLD, 0.25).set_stroke(GOLD, 3)
        self.play(Create(kn), run_time=0.8)
        self.play(DrawBorderThenFill(cap), run_time=1.4)
        t1 = VGroup(VGroup(zh("光滑圆盘", 32), tex(r"D^2 \subset B^4", 42)).arrange(RIGHT, buff=0.2),
                    tex(r"\partial D^2 = K", 42, GOLD)).arrange(DOWN, buff=0.3)
        t1.move_to(RIGHT * 3.3 + UP * 0.4)
        sl = zh("切片扭结", 40, GOLD, weight=BOLD).next_to(t1, DOWN, buff=0.5)
        self.play(Write(t1), run_time=1.2)
        self.play(FadeIn(sl, scale=1.2), run_time=0.6)
        # s6: signature obstruction; square knot
        self.at(6)
        self.play(FadeOut(VGroup(ball, halo, lb, ls3, kn, cap, t1, sl)), run_time=0.4)
        ob = VGroup(zh("K 切片", 38), tex(r"\Rightarrow\ \sigma(K) = 0", 52)).arrange(RIGHT, buff=0.25).move_to(UP * 2.0)
        self.play(Write(ob), run_time=1.2)
        tk = KnotDiagram(comps_of(trefoil_pts()), scale=0.42, shift=LEFT * 4.0 + DOWN * 0.3, colors=[CYAN])
        tl = tex(r"\sigma = -2 \ne 0", 40, CYAN).next_to(tk, DOWN, buff=0.25)
        self.play(Create(tk), FadeIn(tl), run_time=1.0)
        xm = cross_mark(size=0.8).move_to(tk)
        self.play(FadeIn(xm, scale=1.6), run_time=0.4)
        sq = smooth_closed(connect_sum(trefoil_pts(400), trefoil_pts(400) * [-1, 1, 1], gapx=1.6, cut=0.9), 8)
        sqd = KnotDiagram(comps_of(sq), scale=0.36, shift=RIGHT * 2.4 + DOWN * 0.3,
                          color_fn=lambda k, p: CYAN if p["pts"][:, 0].mean() < 0 else MAGENTA)
        sql = VGroup(zh("方结", 30, INK), tex(r"3_1 \# \overline{3_1}", 38)).arrange(RIGHT, buff=0.3).next_to(sqd, DOWN, buff=0.25)
        self.wait_to(self.S(6) + self.D(6) * 0.55)
        self.play(Create(sqd), FadeIn(sql), run_time=1.2)
        ck = check_mark(size=0.7).next_to(sqd, RIGHT, buff=0.3)
        sl2 = zh("切片 ✓", 30, LIME).next_to(ck, DOWN, buff=0.2)
        self.play(FadeIn(ck, scale=1.5), FadeIn(sl2), run_time=0.5)
        # s7: Fox-Milnor
        self.at(7)
        self.play(FadeOut(VGroup(ob, tk, tl, xm, sql, ck, sl2)), sqd.animate.scale(0.8).move_to(LEFT * 4.2 + DOWN * 0.6), run_time=0.6)
        fm = VGroup(zh("K 切片", 40, GOLD), tex(r"\Rightarrow\ \Delta_K(t) = f(t)\, f(t^{-1})", 54, GOLD)).arrange(RIGHT, buff=0.25).move_to(UP * 1.7)
        nm = zh("福克斯 – 米尔诺", 30, DIM).next_to(fm, UP, buff=0.25)
        self.play(FadeIn(nm), Write(fm), run_time=1.6)
        ex = tex(r"\Delta_{3_1\#\overline{3_1}} = (t - 1 + t^{-1})^2", 46, MAGENTA).move_to(RIGHT * 1.6 + DOWN * 0.4)
        self.play(Write(ex), run_time=1.2)
        shadow = zh("四维拓扑的影子，投射在三维扭结上", 30, INK).move_to(RIGHT * 1.6 + DOWN * 1.8)
        self.wait_to(self.S(7) + self.D(7) * 0.6)
        self.play(FadeIn(shadow, shift=UP * 0.2), run_time=0.8)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  09
def wheel_image(size=2.0, power=1, res=360):
    yy, xx = np.mgrid[-1:1:res * 1j, -1:1:res * 1j]
    z = xx - 1j * yy
    w = z ** power
    hue = (np.angle(w) / TAU_) % 1.0
    r = np.abs(z)
    import colorsys
    h6 = hue * 6
    i = np.floor(h6).astype(int) % 6
    f = h6 - np.floor(h6)
    v = np.clip(0.35 + 0.65 * np.minimum(r * 1.2, 1), 0, 1)
    s = 0.85
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    rgb = np.zeros(z.shape + (3,))
    for k, (a, b, c) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        rgb[m, 0], rgb[m, 1], rgb[m, 2] = a[m], b[m], c[m]
    # concentric rings
    ring = (np.abs(np.sin(np.abs(w) * 9)) < 0.08) & (r <= 1)
    rgb[ring] = rgb[ring] * 0.4
    alpha = np.clip((1 - r) * res / 3, 0, 1)
    img = np.dstack([rgb * 255, alpha * 230]).astype(np.uint8)
    im = ImageMobject(img)
    im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["linear"])
    im.set(height=size)
    return im


class Ch09(Chapter):
    CH = 9

    def construct(self):
        self.intro_level()
        # s1: z -> z^2
        self.at(1)
        L = wheel_image(3.6, 1).move_to(LEFT * 3.4 + UP * 0.3)
        Rw = wheel_image(3.6, 2).move_to(RIGHT * 3.4 + UP * 0.3)
        arr = Arrow(LEFT * 1.2 + UP * 0.3, RIGHT * 1.2 + UP * 0.3, color=GOLD)
        ml = tex(r"z \mapsto z^2", 46, GOLD).next_to(arr, UP, buff=0.15)
        self.play(FadeIn(L, scale=0.8), run_time=0.8)
        self.play(GrowArrow(arr), Write(ml), FadeIn(Rw, scale=0.8), run_time=1.2)
        a = ValueTracker(0)
        cL, cR = L.get_center(), Rw.get_center()
        dl = always_redraw(lambda: glow(Dot(cL + 1.3 * np.array([np.cos(a.get_value()), np.sin(a.get_value()), 0]),
                                            0.1, color=WHITE), WHITE))
        dr = always_redraw(lambda: glow(Dot(cR + 1.8 * (1.3 / 1.8) ** 2 * np.array([np.cos(2 * a.get_value()), np.sin(2 * a.get_value()), 0]),
                                            0.1, color=WHITE), WHITE))
        trailL = TracedPath(lambda: dl[-1].get_center(), stroke_color=WHITE, stroke_width=3)
        trailR = TracedPath(lambda: dr[-1].get_center(), stroke_color=GOLD, stroke_width=3)
        self.add(trailL, trailR, dl, dr)
        self.play(a.animate.set_value(TAU_), run_time=3.2, rate_func=linear)
        bp = glow(Dot(cR, 0.1, color=RED_N), RED_N)
        bl = zh("分支点", 28, RED_N).next_to(Rw, DOWN, buff=0.25)
        once = zh("转一圈", 26).next_to(L, DOWN, buff=0.25)
        twice = zh("转两圈", 26, GOLD).next_to(bl, DOWN, buff=0.1)
        self.play(FadeIn(bp, scale=2), FadeIn(bl), FadeIn(once), FadeIn(twice), run_time=0.8)
        # s2: n-fold cyclic branched cover
        self.at(2)
        self.play(FadeOut(frozen(dl, dr, trailL, trailR)), FadeOut(Group(L, Rw, arr, ml, bp, bl, once, twice)), run_time=0.5)
        n = 3
        ctr = UP * 0.3
        blocks = VGroup()
        for i in range(n):
            ang = PI / 2 + i * TAU_ / n
            b = RoundedRectangle(width=1.9, height=0.9, corner_radius=0.15).set_fill("#10233d", 1).set_stroke(SKY, 2)
            b.add(tex(f"X_{i}", 36).move_to(b))
            b.move_to(ctr + 2.1 * np.array([np.cos(ang), np.sin(ang), 0]))
            blocks.add(b)
        arrows = VGroup(*[CurvedArrow(blocks[i].get_center() + 0.0, blocks[(i + 1) % n].get_center(), angle=0.9,
                                      color=GOLD).scale(0.6) for i in range(n)])
        kc = KnotDiagram(comps_of(trefoil_pts()), scale=0.22, shift=ctr, colors=[MAGENTA], width=4)
        self.play(LaggedStart(*[FadeIn(b, scale=0.8) for b in blocks], lag_ratio=0.25), run_time=1.2)
        self.play(Create(arrows), run_time=1.0)
        tt = tex(r"t^{n} = 1", 40, GOLD).move_to(RIGHT * 4.3 + UP * 1.6)
        self.play(FadeIn(tt), run_time=0.5)
        self.wait_to(self.S(2) + self.D(2) * 0.55)
        self.play(Create(kc), Flash(ctr, color=MAGENTA, flash_radius=0.8), run_time=1.0)
        br = zh("分支轨迹 = K", 28, MAGENTA).move_to(RIGHT * 4.3 + DOWN * 0.2)
        sn = tex(r"\Sigma_n(K)", 56, CYAN).move_to(RIGHT * 4.3 + DOWN * 1.3)
        self.play(FadeIn(br), Write(sn), run_time=1.0)
        # s3: double branched cover, determinant
        self.at(3)
        self.play(FadeOut(VGroup(blocks, arrows, kc, tt, br, sn)), run_time=0.4)
        e1 = tex(r"\big|H_1(\Sigma_2(K))\big| = \big|\Delta_K(-1)\big| = \det(K)", 54, GOLD).move_to(UP * 0.9)
        self.play(Write(e1), run_time=1.8)
        e2 = tex(r"\det(3_1) = |1 + 1 + 1| = 3", 46, CYAN).next_to(e1, DOWN, buff=0.6)
        self.wait_to(self.S(3) + self.D(3) * 0.6)
        self.play(Write(e2), run_time=1.2)
        # s4: Goeritz matrix from the checkerboard colouring
        self.at(4)
        self.play(FadeOut(VGroup(e1, e2)), run_time=0.4)
        tp = trefoil_pts(400)
        sh = LEFT * 3.4 + UP * 0.2
        kd = KnotDiagram(comps_of(tp), scale=0.62, shift=sh, colors=[CYAN])
        im = evenodd_image([to_scene(tp, 0.62, sh)], CYAN, 0.30)
        self.play(FadeIn(im), Create(kd), run_time=1.2)
        r0 = tex("R_0", 40, GOLD).move_to(sh + UP * 0.15)
        r1 = tex("R_1", 40, GOLD).move_to(sh + RIGHT * 1.95 + DOWN * 1.35)
        self.play(FadeIn(r0, scale=1.4), FadeIn(r1, scale=1.4), run_time=0.6)
        rings = VGroup(*[Circle(radius=0.3).move_to(kd.cpoint(x)).set_stroke(LIME, 3) for x in kd.crossings])
        self.play(LaggedStart(*[Create(r) for r in rings], lag_ratio=0.3), run_time=1.0)
        G = tex(r"G = \begin{pmatrix} 3 & -3 \\ -3 & 3 \end{pmatrix}", 54).move_to(RIGHT * 3.0 + UP * 0.8)
        gl = zh("白色区域 × 白色区域", 26, DIM).next_to(G, UP, buff=0.3)
        self.wait_to(self.S(4) + self.D(4) * 0.55)
        self.play(FadeIn(gl), Write(G), run_time=1.4)
        # s5: delete a row and column
        self.at(5)
        Gp = tex(r"G' = (\,3\,),\quad |\det G'| = 3", 48, GOLD).next_to(G, DOWN, buff=0.5)
        self.play(Write(Gp), run_time=1.2)
        f8 = tex(r"\det(4_1) = 5", 44, MAGENTA).next_to(Gp, DOWN, buff=0.35)
        self.play(FadeIn(f8, shift=UP * 0.2), run_time=0.7)
        lens = VGroup(ArcBetweenPoints(LEFT * 0.9, RIGHT * 0.9, angle=-1.6), ArcBetweenPoints(RIGHT * 0.9, LEFT * 0.9, angle=-1.6))
        lens.set_stroke(VIOLET, 4).set_fill(VIOLET, 0.2)
        lt = tex(r"\Sigma_2(3_1) = L(3,1)", 42, VIOLET)
        lg = VGroup(lens, lt).arrange(RIGHT, buff=0.4).move_to(RIGHT * 3.0 + DOWN * 2.2)
        self.wait_to(self.S(5) + self.D(5) * 0.65)
        self.play(FadeIn(lg, shift=UP * 0.2), run_time=0.9)
        # s6: back to 3-colourings
        self.at(6)
        self.clear_stage(0.4)
        hdr = VGroup(zh("可三染色", 42, GOLD), tex(r"\iff 3 \mid \det(K)", 54, GOLD)).arrange(RIGHT, buff=0.3).move_to(UP * 1.9)
        self.play(Write(hdr), run_time=1.4)
        cols = VGroup()
        data = [(comps_of(circle_pts(120, 1.4)), 0.42, "1", False),
                (comps_of(trefoil_pts()), 0.3, "3", True),
                (comps_of(figure8_pts2()), 0.3, "5", False)]
        for comps, scl, d, ok in data:
            kd2 = KnotDiagram(comps, scale=scl, color_fn=(lambda k, p: TRI[k % 3]) if ok else None, colors=[INK])
            dt = tex(r"\det = " + d, 40).next_to(kd2, DOWN, buff=0.3)
            mk = (check_mark if ok else cross_mark)(size=0.5).next_to(dt, DOWN, buff=0.3)
            cols.add(VGroup(kd2, dt, mk))
        cols.arrange(RIGHT, buff=1.6).move_to(DOWN * 0.6)
        for c in cols:
            c[1].align_to(cols[0][1], UP)
            c[2].align_to(cols[0][2], UP)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cols], lag_ratio=0.35), run_time=2.0)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()
