# -*- coding: utf-8 -*-
from common import *


# ------------------------------------------------------------------ Temperley-Lieb pictures
def tl_box(n, cups=(), w=None, h=1.5, color=CYAN, label=None):
    """Planar diagram in a box: n points top & bottom. cups: list of i (1-based) for e_i style
    cap/cup pairs; other strands go straight up."""
    w = w or 0.5 * n + 0.3
    box = Rectangle(width=w, height=h).set_stroke(DIM, 2).set_fill("#0b1224", 0.85)
    xs = [box.get_left()[0] + 0.15 + (k + 0.5) * (w - 0.3) / n for k in range(n)]
    yb, yt = box.get_bottom()[1], box.get_top()[1]
    g = VGroup(box)
    used = set()
    for i in cups:
        used |= {i - 1, i}
        a, b = xs[i - 1], xs[i]
        r = (b - a) / 2
        g.add(Arc(radius=r, start_angle=0, angle=PI, arc_center=[(a + b) / 2, yb, 0]).set_stroke(color, 5))
        g.add(Arc(radius=r, start_angle=PI, angle=PI, arc_center=[(a + b) / 2, yt, 0]).set_stroke(color, 5))
    for k in range(n):
        if k not in used:
            g.add(Line([xs[k], yb, 0], [xs[k], yt, 0]).set_stroke(color, 5))
    dots = VGroup(*[Dot([x, y, 0], 0.05, color=INK) for x in xs for y in (yb, yt)])
    g.add(dots)
    if label:
        g.add(tex(label, 36, INK).next_to(box, DOWN, buff=0.15))
    g.xs = xs
    return g


def jw_box(n=3, label="f_n", color=GOLD, h=1.6, w=1.6):
    xs = np.linspace(-w / 2 + 0.3, w / 2 - 0.3, n)
    g = VGroup()
    for x in xs:
        g.add(Line([x, -h / 2, 0], [x, h / 2, 0]).set_stroke(CYAN, 5))
    b = Rectangle(width=w, height=0.55).set_fill("#2a2108", 1).set_stroke(color, 3)
    g.add(b, tex(label, 34, color).move_to(b))
    return g


# =====================================================================  14
class Ch14(Chapter):
    CH = 14

    def construct(self):
        self.intro_level()
        # s1: Temperley-Lieb diagrams
        self.at(1)
        boxes = VGroup(tl_box(4, (), label="1"), tl_box(4, (1,), label="e_1"), tl_box(4, (2,), label="e_2"),
                       tl_box(4, (3,), label="e_3")).arrange(RIGHT, buff=0.6).move_to(UP * 0.4)
        hd = VGroup(zh("坦珀利–利布代数", 36, GOLD, weight=BOLD), tex(r"TL_n", 44, GOLD)).arrange(RIGHT, buff=0.3).to_edge(UP, buff=1.0)
        self.play(FadeIn(hd), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.3) for b in boxes], lag_ratio=0.25), run_time=2.0)
        note = zh("上下各 n 个点，曲线互不相交", 30, DIM).next_to(boxes, DOWN, buff=0.5)
        self.play(FadeIn(note), run_time=0.6)
        # s2: multiplication by stacking; loops -> delta
        self.at(2)
        self.play(FadeOut(VGroup(boxes, note)), run_time=0.4)
        lo = tl_box(4, (1,), color=CYAN)
        hi = tl_box(4, (1,), color=MAGENTA)
        st = VGroup(hi, lo).arrange(DOWN, buff=0).move_to(LEFT * 3.2 + DOWN * 0.1)
        self.play(FadeIn(lo, shift=UP * 0.3), run_time=0.6)
        self.play(FadeIn(hi, shift=DOWN * 0.3), run_time=0.6)
        xs = lo.xs
        y = lo[0].get_top()[1]
        loop = Circle(radius=(xs[1] - xs[0]) / 2).move_to([(xs[0] + xs[1]) / 2, y, 0]).set_stroke(GOLD, 7)
        self.wait_to(self.S(2) + self.D(2) * 0.5)
        self.play(Create(loop), Flash(loop.get_center(), color=GOLD, flash_radius=0.5), run_time=0.8)
        eq = tex(r"e_1 \cdot e_1 = \delta\, e_1", 56).move_to(RIGHT * 2.6 + UP * 0.6)
        dl = tex(r"\delta = -A^{2} - A^{-2}", 46, GOLD).next_to(eq, DOWN, buff=0.45)
        self.play(Write(eq), run_time=1.0)
        self.play(TransformFromCopy(loop, dl), run_time=0.9)
        # s3: relations, Kauffman bracket of a braid
        self.at(3)
        self.play(FadeOut(VGroup(st, loop, eq, dl)), run_time=0.5)
        rels = VGroup(tex(r"e_i^{2} = \delta\, e_i", 50), tex(r"e_i\, e_{i\pm1}\, e_i = e_i", 50)).arrange(RIGHT, buff=1.2)
        rels.move_to(UP * 1.2)
        self.play(Write(rels[0]), run_time=0.9)
        self.play(Write(rels[1]), run_time=0.9)
        g = lambda k: glyph(k, 0.9, CYAN, arrows=False)
        br = row(r"\sigma_i \;=\;", g("A"), r"\;\longmapsto\; A\cdot", g("Asm"), r"+\;A^{-1}\cdot", g("Bsm"), size=48)
        br.move_to(DOWN * 0.8)
        lb = VGroup(tex("1", 34, GOLD).next_to(br[3], DOWN, buff=0.1), tex("e_i", 34, GOLD).next_to(br[5], DOWN, buff=0.1))
        self.wait_to(self.S(3) + self.D(3) * 0.55)
        self.play(FadeIn(br, shift=UP * 0.2), FadeIn(lb), run_time=1.2)
        # s4: Jones-Wenzl idempotents
        self.at(4)
        self.play(FadeOut(VGroup(rels, br, lb)), run_time=0.4)
        f = jw_box(3).move_to(LEFT * 4.6 + UP * 1.0)
        fl = zh("琼斯–文茨尔幂等元", 30, GOLD).next_to(f, DOWN, buff=0.3)
        self.play(FadeIn(f, scale=0.8), FadeIn(fl), run_time=0.8)
        p1 = tex(r"f_n^{2} = f_n", 50).move_to(LEFT * 0.6 + UP * 1.4)
        capped = jw_box(3)
        xs_ = [m.get_center()[0] for m in capped[:3]]
        cap = Arc(radius=(xs_[1] - xs_[0]) / 2, start_angle=0, angle=PI,
                  arc_center=[(xs_[0] + xs_[1]) / 2, capped[0].get_top()[1], 0]).set_stroke(MAGENTA, 5)
        capped.add(cap)
        p2 = VGroup(capped.scale(0.7), tex("= 0", 50)).arrange(RIGHT, buff=0.3).move_to(RIGHT * 3.6 + UP * 1.3)
        self.play(Write(p1), run_time=0.8)
        self.play(FadeIn(p2), run_time=0.8)
        rec = tex(r"f_{n+1} = f_n\otimes 1 - \frac{\Delta_{n-1}}{\Delta_n}\,(f_n\otimes 1)\,e_n\,(f_n\otimes 1)", 44, CYAN)
        rec.move_to(DOWN * 1.15)
        dd = tex(r"\Delta_{n+1} = -(A^{2}+A^{-2})\,\Delta_n - \Delta_{n-1}", 40, DIM).next_to(rec, DOWN, buff=0.35)
        self.wait_to(self.S(4) + self.D(4) * 0.55)
        self.play(Write(rec), run_time=1.6)
        self.play(FadeIn(dd), run_time=0.6)
        # s5: coloured Jones, trivalent graphs, 6j
        self.at(5)
        self.clear_stage(0.4)
        tk = KnotDiagram(comps_of(trefoil_pts()), scale=0.42, shift=LEFT * 4.6 + UP * 0.4, colors=[CYAN])
        bx = Rectangle(width=0.5, height=0.32).set_fill("#2a2108", 1).set_stroke(GOLD, 2.5)
        bx.move_to(tk.get_center() + DOWN * 1.24)
        bt = tex("f_n", 26, GOLD).move_to(bx)
        cj = zh("彩色琼斯多项式", 28, CYAN).next_to(tk, DOWN, buff=0.45)
        self.play(Create(tk), run_time=0.8)
        self.play(FadeIn(bx), FadeIn(bt), FadeIn(cj), run_time=0.6)
        # trivalent vertex
        c = ORIGIN + UP * 0.3
        legs = VGroup(*[Line(c, c + 1.0 * np.array([np.cos(a), np.sin(a), 0])).set_stroke(MAGENTA, 6)
                        for a in (PI / 2, PI / 2 + TAU_ / 3, PI / 2 + 2 * TAU_ / 3)])
        labs = VGroup(*[tex(t, 36, MAGENTA).move_to(c + 1.3 * np.array([np.cos(a), np.sin(a), 0]))
                        for t, a in zip("abc", (PI / 2, PI / 2 + TAU_ / 3, PI / 2 + 2 * TAU_ / 3))])
        tv = zh("三价顶点", 28, MAGENTA).move_to(c + DOWN * 1.6)
        self.play(Create(legs), FadeIn(labs), FadeIn(tv), run_time=0.9)
        # tetrahedron (6j symbol)
        cc = RIGHT * 4.3 + UP * 0.3
        P = [cc + 1.2 * np.array([np.cos(a), np.sin(a), 0]) for a in (PI / 2, PI / 2 + TAU_ / 3, PI / 2 + 2 * TAU_ / 3)] + [cc]
        edges = VGroup(*[Line(P[i], P[j]).set_stroke(GOLD, 4) for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))])
        vd = VGroup(*[Dot(p, 0.08, color=WHITE) for p in P])
        sj = tex(r"\begin{Bmatrix} a & b & c \\ d & e & f \end{Bmatrix}", 40, GOLD).next_to(edges, DOWN, buff=0.3)
        self.wait_to(self.S(5) + self.D(5) * 0.5)
        self.play(Create(edges), FadeIn(vd), run_time=1.0)
        self.play(Write(sj), run_time=0.9)
        # s6: Delta_n vanishes at a root of unity
        self.at(6)
        self.clear_stage(0.4)
        r = 5
        vals = [(-1) ** n * np.sin((n + 1) * PI / r) / np.sin(PI / r) for n in range(r)]
        ax = Line(LEFT * 3.5 + UP * 0.3, RIGHT * 3.5 + UP * 0.3).set_stroke(DIM, 2)
        bars = VGroup()
        for n, v in enumerate(vals):
            x = -2.8 + n * 1.4
            hgt = max(abs(v) * 1.1, 0.02)
            b = Rectangle(width=0.8, height=hgt).set_fill(RED_N if abs(v) < 1e-9 else CYAN, 0.75).set_stroke(width=0)
            b.move_to([x, 0.3 + (hgt / 2 if v >= 0 else -hgt / 2), 0])
            lab = tex(fr"\Delta_{n}", 32).move_to([x, -1.65, 0])
            bars.add(VGroup(b, lab))
        hdr = VGroup(tex(r"A = e^{2\pi i/4r},\ r = 5:", 40), tex(r"\Delta_{r-1} = 0", 44, RED_N)).arrange(RIGHT, buff=0.5)
        hdr.to_edge(UP, buff=1.0)
        self.play(Create(ax), FadeIn(hdr[0]), run_time=0.6)
        self.play(LaggedStart(*[GrowFromEdge(b[0], DOWN if vals[i] >= 0 else UP) for i, b in enumerate(bars)], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(b[1]) for b in bars], lag_ratio=0.2), run_time=1.6)
        z = bars[4]
        dz = tex(r"\div 0", 50, RED_N).next_to(z, UP, buff=0.5)
        self.play(FadeIn(hdr[1]), FadeIn(dz, scale=1.5), Flash(z[0].get_center(), color=RED_N), run_time=0.8)
        brace = Brace(VGroup(*[b[1] for b in bars[:4]]), DOWN, color=GOLD)
        bl = tex(r"\Omega = \sum_{n=0}^{r-2}", 36, GOLD).next_to(brace, RIGHT, buff=0.3).shift(DOWN * 0.1)
        self.play(GrowFromCenter(brace), FadeIn(bl), run_time=0.8)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  15
class Ch15(Chapter):
    CH = 15

    def construct(self):
        self.intro_level()
        # s1: the acronym
        self.at(1)
        letters = "HOMFLYPT"
        names = ["Hoste", "Ocneanu", "Millett", "Freyd", "Lickorish", "Yetter", "Przytycki", "Traczyk"]
        cols = VGroup()
        for i, (L, nme) in enumerate(zip(letters, names)):
            c = NEON[i % 6]
            l = mono(L, 84, c, weight=HEAVY)
            n_ = mono(nme, 18, DIM, weight=NORMAL).next_to(l, DOWN, buff=0.15)
            cols.add(VGroup(l, n_))
        cols.arrange(RIGHT, buff=0.32).move_to(UP * 0.4)
        yr = mono("1985", 36, GOLD).next_to(cols, UP, buff=0.5)
        self.play(FadeIn(yr), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.4) for c in cols[:6]], lag_ratio=0.2), run_time=2.2)
        pl = zh("+ 两位波兰数学家", 30, INK).next_to(cols, DOWN, buff=0.6)
        self.wait_to(self.S(1) + self.D(1) * 0.7)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.4) for c in cols[6:]], lag_ratio=0.3), FadeIn(pl), run_time=1.0)
        # s2: skein relation
        self.at(2)
        self.play(FadeOut(VGroup(cols, yr, pl)), run_time=0.4)
        g = lambda k: glyph(k, 0.75, CYAN)
        sk = row(r"l\,P\Big(", g("pos"), r"\Big) + l^{-1}P\Big(", g("neg"), r"\Big) + m\,P\Big(", g("zero"), r"\Big) = 0", size=44)
        sk.move_to(UP * 0.6)
        lbls = VGroup(tex("L_+", 32, GOLD).next_to(sk[1], DOWN, buff=0.1), tex("L_-", 32, GOLD).next_to(sk[3], DOWN, buff=0.1),
                      tex("L_0", 32, GOLD).next_to(sk[5], DOWN, buff=0.1))
        un = tex(r"P(\bigcirc) = 1", 46).next_to(sk, DOWN, buff=1.0)
        self.play(FadeIn(sk, shift=UP * 0.2), FadeIn(lbls), run_time=1.6)
        self.wait_to(self.S(2) + self.D(2) * 0.75)
        self.play(Write(un), run_time=0.8)
        # s3: specialisations
        self.at(3)
        self.play(FadeOut(VGroup(sk, lbls, un)), run_time=0.4)
        P = panel(3.0, 1.2, GOLD, 0.1, 0.9).move_to(UP * 1.5)
        Pt = tex(r"P_L(l, m)", 50, GOLD).move_to(P)
        V = panel(3.0, 1.1, CYAN, 0.1, 0.9).move_to(LEFT * 3.6 + DOWN * 1.5)
        Vt = tex(r"V_L(t)", 48, CYAN).move_to(V)
        D = panel(3.0, 1.1, MAGENTA, 0.1, 0.9).move_to(RIGHT * 3.6 + DOWN * 1.5)
        Dt = tex(r"\Delta_L(t)", 48, MAGENTA).move_to(D)
        a1 = Arrow(P.get_bottom(), V.get_top(), color=CYAN, buff=0.1)
        a2 = Arrow(P.get_bottom(), D.get_top(), color=MAGENTA, buff=0.1)
        s1 = tex(r"l = i t^{-1},\ m = i(t^{-1/2} - t^{1/2})", 30, CYAN).next_to(a1.get_center(), LEFT, buff=0.2)
        s2 = tex(r"l = i,\ m = i(t^{-1/2} - t^{1/2})", 30, MAGENTA).next_to(a2.get_center(), RIGHT, buff=0.2)
        self.play(FadeIn(P), Write(Pt), run_time=0.8)
        self.play(GrowArrow(a1), FadeIn(V), FadeIn(Vt), FadeIn(s1), run_time=1.2)
        self.play(GrowArrow(a2), FadeIn(D), FadeIn(Dt), FadeIn(s2), run_time=1.2)
        # s4: Kauffman polynomial
        self.at(4)
        self.play(FadeOut(VGroup(P, Pt, V, Vt, D, Dt, a1, a2, s1, s2)), run_time=0.4)
        u = lambda k: glyph(k, 0.75, MAGENTA, arrows=False)
        kf = row(r"\Lambda\Big(", u("A"), r"\Big) + \Lambda\Big(", u("neg"), r"\Big) = z\Big[\Lambda\Big(", u("Asm"),
                 r"\Big) + \Lambda\Big(", u("Bsm"), r"\Big)\Big]", size=42)
        if kf.width > 12.6:
            kf.scale_to_fit_width(12.6)
        kf.move_to(UP * 1.0)
        kl = VGroup(tex("L_+", 30, GOLD).next_to(kf[1], DOWN, buff=0.1), tex("L_-", 30, GOLD).next_to(kf[3], DOWN, buff=0.1),
                    tex("L_0", 30, GOLD).next_to(kf[5], DOWN, buff=0.1), tex(r"L_\infty", 30, GOLD).next_to(kf[7], DOWN, buff=0.1))
        nori = zh("无需定向", 30, MAGENTA).next_to(kf, UP, buff=0.4)
        self.play(FadeIn(kf, shift=UP * 0.2), FadeIn(kl), run_time=1.6)
        self.play(FadeIn(nori), run_time=0.5)
        kk = row(r"\Lambda\Big(", u("kink"), r"\Big) = a\,\Lambda\Big(", u("line"), r"\Big),\qquad F(L) = a^{-w(D)}\Lambda(D)", size=40)
        kk.next_to(kf, DOWN, buff=0.9)
        self.wait_to(self.S(4) + self.D(4) * 0.6)
        self.play(FadeIn(kk, shift=UP * 0.2), run_time=1.2)
        # s5: algebra & physics
        self.at(5)
        self.clear_stage(0.4)
        colA = VGroup(mono("HOMFLY", 40, CYAN), tex(r"\Uparrow", 40, DIM), zh("赫克代数的迹", 32), tex(r"\Uparrow", 40, DIM),
                      tex(r"U_q(\mathfrak{sl}_N)", 46, CYAN)).arrange(DOWN, buff=0.25)
        colB = VGroup(mono("KAUFFMAN", 40, MAGENTA), tex(r"\Uparrow", 40, DIM), zh("BMW 代数", 32), tex(r"\Uparrow", 40, DIM),
                      tex(r"U_q(\mathfrak{so}_N),\ U_q(\mathfrak{sp}_{2n})", 42, MAGENTA)).arrange(DOWN, buff=0.25)
        VGroup(colA, colB).arrange(RIGHT, buff=2.4).move_to(DOWN * 0.1)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in colA], lag_ratio=0.15), run_time=1.6)
        self.wait_to(self.S(5) + self.D(5) * 0.35)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in colB], lag_ratio=0.15), run_time=1.6)
        # s6: the forest
        self.at(6)
        self.clear_stage(0.4)
        root = DOWN * 2.2
        nodes = {"Jones": (root + UP * 1.0, GOLD), "HOMFLY": (LEFT * 3.6 + UP * 0.6, CYAN),
                 "Kauffman": (RIGHT * 3.6 + UP * 0.6, MAGENTA), "colored Jones": (LEFT * 1.3 + UP * 1.4, LIME),
                 "WRT": (RIGHT * 1.3 + UP * 1.4, VIOLET)}
        trunk = Line(root, nodes["Jones"][0]).set_stroke(GOLD, 6)
        self.play(Create(trunk), run_time=0.5)
        objs = VGroup()
        for name, (pos, col) in nodes.items():
            lab = mono(name, 28, col)
            bgp = SurroundingRectangle(lab, buff=0.15, corner_radius=0.1).set_stroke(col, 2).set_fill("#0b1224", 0.9)
            objs.add(VGroup(bgp, lab).move_to(pos))
        branches = VGroup(*[CubicBezier(nodes["Jones"][0], nodes["Jones"][0] + UP * 0.8, nodes[k][0] + DOWN * 0.8, nodes[k][0])
                            .set_stroke(nodes[k][1], 4) for k in ("HOMFLY", "Kauffman", "colored Jones", "WRT")])
        self.play(FadeIn(objs[0], scale=0.6), run_time=0.4)
        self.play(Create(branches), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(o, scale=0.6) for o in objs[1:]], lag_ratio=0.2), run_time=1.0)
        leaves = VGroup(*[tex(t, 34, c).move_to(p) for t, c, p in
                          ((r"\mathfrak{sl}_N", CYAN, LEFT * 5.2 + UP * 2.2), (r"\mathfrak{so}_N", MAGENTA, RIGHT * 5.2 + UP * 2.2),
                           (r"\mathfrak{sp}_{2n}", MAGENTA, RIGHT * 3.0 + UP * 2.4), (r"G_2", ORANGE, LEFT * 0.0 + UP * 2.6),
                           (r"E_8", ORANGE, LEFT * 3.0 + UP * 2.4))])
        self.play(LaggedStart(*[FadeIn(l_, scale=1.5) for l_ in leaves], lag_ratio=0.15), run_time=1.0)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  16
TANGLE_ENDS = [(-1.0, 0.5), (-1.0, -0.5), (1.0, -0.5), (1.0, 0.5)]


def mutant_parts(angle=0.0):
    """A 3-crossing twist tangle with a bulge on its left half, rotated by `angle` in the plane."""
    x = np.linspace(-1, 1, 200)
    amp = 0.5 + 0.28 * np.exp(-((x + 0.45) / 0.3) ** 2)
    ph = 1.5 * PI * (x + 1)
    a = np.stack([x, amp * np.cos(ph) / 1.0, 0.6 * np.sin(ph)], 1)
    a[:, 1] *= 0.5 / amp[0] if False else 1.0
    b = a.copy()
    b[:, 1] *= -1
    b[:, 2] *= -1
    R = rot_matrix(0, 0, angle)
    return [Comp(a @ R.T, False), Comp(b @ R.T, False)]


class Ch16(Chapter):
    CH = 16

    def construct(self):
        self.intro_level()
        # s1: HOMFLY detects chirality
        self.at(1)
        R = KnotDiagram(comps_of(trefoil_pts()), scale=0.5, shift=LEFT * 3.4 + UP * 0.7, colors=[CYAN])
        L = KnotDiagram(comps_of(trefoil_pts() * [-1, 1, 1]), scale=0.5, shift=RIGHT * 3.4 + UP * 0.7, colors=[MAGENTA])
        pr = tex(r"P = -2l^{-2} - l^{-4} + l^{-2}m^{2}", 40, CYAN).next_to(R, DOWN, buff=0.35)
        pl = tex(r"P = -2l^{2} - l^{4} + l^{2}m^{2}", 40, MAGENTA).next_to(L, DOWN, buff=0.35)
        ne = tex(r"\neq", 80, RED_N).move_to(UP * 0.7)
        self.play(Create(R), Create(L), run_time=1.0)
        self.play(Write(pr), Write(pl), run_time=1.4)
        self.play(FadeIn(ne, scale=2), run_time=0.4)
        # s2: Morton-Franks-Williams
        self.at(2)
        self.play(FadeOut(VGroup(L, pl, ne)), R.animate.move_to(LEFT * 4.4 + DOWN * 0.2), pr.animate.scale(0.8).move_to(LEFT * 4.4 + DOWN * 1.9),
                  run_time=0.6)
        mfw = tex(r"b(L) \;\ge\; \tfrac12\,\operatorname{span}_l P_L + 1", 56, GOLD).move_to(RIGHT * 1.6 + UP * 1.7)
        who = zh("莫顿 · 弗兰克斯 · 威廉斯", 28, DIM).next_to(mfw, UP, buff=0.25)
        self.play(FadeIn(who), Write(mfw), run_time=1.6)
        ex = tex(r"3_1:\ \operatorname{span}_l P = 4 - 2 = 2 \ \Rightarrow\ b \ge 2", 42).next_to(mfw, DOWN, buff=0.5)
        self.play(Write(ex), run_time=1.4)
        br = rotating_knot(self, comps_of(torus_pts(2, 3, 400)), 0.42, RIGHT * 1.6 + DOWN * 1.3, speed=0.0, tilt=0.0, width=6,
                           colors=[LIME])
        axis = VGroup(Dot(RIGHT * 1.6 + DOWN * 1.3, 0.08, color=WHITE), Circle(radius=0.16).move_to(RIGHT * 1.6 + DOWN * 1.3).set_stroke(WHITE, 2))
        cl = VGroup(tex(r"\widehat{\sigma_1^{3}}", 44, LIME), tex(r"\Rightarrow b = 2", 44, LIME)).arrange(RIGHT, buff=0.3)
        cl.next_to(axis, RIGHT, buff=1.5)
        self.wait_to(self.S(2) + self.D(2) * 0.62)
        self.add(br)
        self.play(FadeIn(axis), FadeIn(cl), run_time=0.8)
        # s3: Kauffman polynomial and crossing number
        self.at(3)
        self.clear_stage(0.4)
        nk = KnotDiagram(comps_of(torus_pts(3, 4, 700)), scale=0.5, shift=LEFT * 3.2 + UP * 0.1, color_fn=lambda k, p: NEON[k % 6])
        nl = VGroup(tex(r"8_{19} = T(3,4)", 40), zh("非交错", 30, ORANGE)).arrange(DOWN, buff=0.2).next_to(nk, DOWN, buff=0.3)
        self.play(Create(nk), FadeIn(nl), run_time=1.4)
        tx = VGroup(tex(r"F_L(a, z)", 54, MAGENTA), tex(r"\Downarrow", 44, DIM), zh("交叉数的下界", 38, INK)).arrange(DOWN, buff=0.3)
        tx.move_to(RIGHT * 2.8 + UP * 0.3)
        self.play(FadeIn(tx, shift=UP * 0.2), run_time=1.0)
        # s4: mutation
        self.at(4)
        self.clear_stage(0.4)
        ctr = LEFT * 2.6 + UP * 0.2
        rad = 1.25
        ang = ValueTracker(0)
        corners = [rad * np.array([np.cos(a), np.sin(a)]) for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)]

        def outer():
            sc = rad * 0.9
            t = np.linspace(0, 1, 80)[:, None]
            L1, L2 = np.array([-1.0, 0.5, 0]) * sc, np.array([-1.0, -0.5, 0]) * sc
            R1, R2 = np.array([1.0, 0.5, 0]) * sc, np.array([1.0, -0.5, 0]) * sc
            CL, CR = np.array([-2.9, 0, 0]), np.array([2.9, 0, 0])
            arcs = [(1 - t) ** 2 * L1 + 2 * (1 - t) * t * (L1 * 0.4 + CL + UP * 1.6) + t ** 2 * L2,
                    (1 - t) ** 2 * R1 + 2 * (1 - t) * t * (R1 * 0.4 + CR + UP * 1.6) + t ** 2 * R2]
            arcs = [(1 - t) ** 3 * P + 3 * (1 - t) ** 2 * t * (P + D * 1.6) + 3 * (1 - t) * t ** 2 * (Q + D * 1.6) + t ** 3 * Q
                    for P, Q, D in ((L1, L2, LEFT), (R1, R2, RIGHT))]
            return VGroup(*[neon_strand(a_ + ctr, GOLD, 7) for a_ in arcs])

        def inner():
            comps = mutant_parts(ang.get_value())
            return KnotDiagram(comps, scale=rad * 0.9, shift=ctr, colors=[GOLD, GOLD], width=7)

        circ = DashedVMobject(Circle(radius=rad * 1.08).move_to(ctr), num_dashes=36).set_stroke(WHITE, 2, 0.7)
        out_ = outer()
        inn = always_redraw(inner)
        self.play(Create(out_), FadeIn(inn), run_time=1.0)
        cs = zh("康威球", 26, DIM).next_to(circ, DOWN, buff=0.15)
        self.play(Create(circ), FadeIn(cs), run_time=0.7)
        lab = VGroup(zh("剪下", 32), tex(r"\to", 40), zh("旋转 180°", 32, GOLD), tex(r"\to", 40), zh("粘回", 32))
        lab.arrange(RIGHT, buff=0.2).move_to(RIGHT * 3.4 + UP * 0.6)
        mu = zh("突变", 44, GOLD, weight=BOLD).next_to(lab, DOWN, buff=0.4)
        self.play(FadeIn(lab), run_time=0.6)
        self.play(ang.animate.set_value(PI), run_time=2.0)
        self.play(FadeIn(mu, scale=1.3), run_time=0.5)
        # s5: Conway knot vs Kinoshita-Terasaka
        self.at(5)
        self.clear_stage(0.4)
        cards = VGroup()
        for nm, gen, col in (("康威结", "3", CYAN), ("木下–寺坂结", "2", MAGENTA)):
            p = panel(4.8, 3.2, col, 0.06, 0.8)
            t = zh(nm, 38, col, weight=BOLD).next_to(p.get_top(), DOWN, buff=0.3)
            n11 = zh("11 个交叉点", 26, DIM).next_to(t, DOWN, buff=0.2)
            gg = VGroup(zh("亏格", 30), tex("= " + gen, 40)).arrange(RIGHT, buff=0.15).next_to(n11, DOWN, buff=0.45)
            cards.add(VGroup(p, t, n11, gg))
        cards.arrange(RIGHT, buff=1.2).move_to(UP * 0.5)
        mutl = VGroup(zh("突变", 30, GOLD), tex(r"\longleftrightarrow", 50, GOLD)).arrange(DOWN, buff=0.1).move_to(cards.get_center())
        self.play(FadeIn(cards[0], shift=RIGHT * 0.3), FadeIn(cards[1], shift=LEFT * 0.3), run_time=1.0)
        self.play(FadeIn(mutl), run_time=0.4)
        same = tex(r"P_{K} = P_{K'},\qquad F_{K} = F_{K'}", 50, GOLD).next_to(cards, DOWN, buff=0.4)
        self.wait_to(self.S(5) + self.D(5) * 0.55)
        self.play(Write(same), run_time=1.2)
        # s6: open problem
        self.at(6)
        self.clear_stage(0.4)
        q = tex(r"V_K(t) = 1 \ \overset{?}{\Longrightarrow}\ K = \bigcirc", 70, INK).move_to(UP * 0.6)
        op = mono("OPEN PROBLEM", 40, RED_N).next_to(q, DOWN, buff=0.6)
        self.play(Write(q), run_time=1.6)
        qm = tex("?", 200, GOLD).set_opacity(0.15).move_to(q)
        self.play(FadeIn(qm, scale=2), FadeIn(op, scale=1.3), run_time=0.8)
        # s7: the web of connections
        self.at(7)
        self.clear_stage(0.4)
        spin = rotating_knot(self, comps_of(trefoil_pts(420)), 0.42, UP * 0.2, speed=0.6, tilt=0.4, width=7,
                             grad=[CYAN, MAGENTA, GOLD])
        self.add(spin)
        pos = {"拓扑": UP * 2.2 + LEFT * 4.0, "代数": UP * 2.2 + RIGHT * 4.0, "物理": DOWN * 1.8 + LEFT * 4.0,
               "计算": DOWN * 1.8 + RIGHT * 4.0}
        cols = [CYAN, MAGENTA, GOLD, LIME]
        nodes = VGroup()
        lines = VGroup()
        for (k, p), c in zip(pos.items(), cols):
            t = zh(k, 40, c, weight=BOLD).move_to(p)
            ring = Circle(radius=0.75).move_to(p).set_stroke(c, 3)
            nodes.add(VGroup(glow(ring, c), t))
            lines.add(DashedLine(p * 0.78 + UP * 0.04, UP * 0.2, dash_length=0.12).set_stroke(c, 2, 0.7))
        self.play(LaggedStart(*[FadeIn(n_, scale=0.6) for n_ in nodes], lag_ratio=0.2), Create(lines), run_time=1.6)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  17 OUTRO
class Ch17(Chapter):
    CH = 17

    def construct(self):
        final_t = self.gstart - T0
        # s0: ALL CLEAR + final time
        self.at(0)
        bar = self.progress_bar()
        self.add(bar)
        clear = mono("ALL  CLEAR", 120, GOLD, weight=HEAVY)
        cg = glow(clear.copy().set_fill(opacity=0).set_stroke(GOLD, 3), GOLD)
        VGroup(clear, cg).move_to(UP * 0.9)
        mm, ss = int(final_t // 60), final_t % 60
        tt = VGroup(zh("通关时间", 34, INK), mono(f"{mm:02d}:{ss:04.1f}", 64, CYAN)).arrange(RIGHT, buff=0.5).next_to(clear, DOWN, buff=0.6)
        self.play(FadeIn(clear, scale=2.5), FadeIn(cg, scale=2.5), run_time=0.45, rate_func=rush_from)
        self.play(Flash(clear.get_center(), color=GOLD, flash_radius=3.5, num_lines=24, line_length=0.8), FadeIn(tt, shift=UP * 0.3),
                  run_time=0.9)
        # s1-s2: the route
        self.at(1)
        self.play(FadeOut(VGroup(clear, cg, tt)), run_time=0.4)
        pts = []
        for i in range(16):
            r_, c_ = divmod(i, 4)
            x = -4.8 + (c_ if r_ % 2 == 0 else 3 - c_) * 3.2
            y = 1.9 - r_ * 1.3
            pts.append(np.array([x, y, 0]))
        path = VMobject().set_points_as_corners(pts).set_stroke(DIM, 3, 0.6)
        nodes = VGroup()
        for i, p in enumerate(pts):
            c = NEON[i % 6]
            d = Circle(radius=0.26).move_to(p).set_stroke(c, 3).set_fill("#0b1224", 1)
            n_ = mono(f"{i + 1:02d}", 20, c).move_to(p)
            nm = LEVEL_NAMES[i + 1]
            if len(nm) > 9:
                nm = nm[:9] + "…"
            lab = zh(nm, 18, INK).next_to(d, DOWN, buff=0.08)
            nodes.add(VGroup(d, n_, lab))
        self.play(Create(path), LaggedStart(*[FadeIn(n_, scale=0.6) for n_ in nodes], lag_ratio=0.04), run_time=1.6)
        lit = VMobject().set_points_as_corners(pts).set_stroke(GOLD, 6)
        lit_g = glow(lit, GOLD)
        span1 = self.E(1) - self.time - 0.2
        # light the first ten stages during s1, the rest during s2
        part1 = VMobject().set_points_as_corners(pts[:10]).set_stroke(GOLD, 6)
        self.play(Create(glow(part1, GOLD)), LaggedStart(*[Indicate(n_[0], color=GOLD) for n_ in nodes[:10]], lag_ratio=0.1),
                  run_time=max(1.0, span1))
        self.at(2)
        part2 = VMobject().set_points_as_corners(pts[9:]).set_stroke(GOLD, 6)
        self.play(Create(glow(part2, GOLD)), LaggedStart(*[Indicate(n_[0], color=GOLD) for n_ in nodes[10:]], lag_ratio=0.15),
                  run_time=max(1.0, self.D(2) * 0.8))
        # s3: thanks
        self.at(3)
        keep = bar
        ms = [m for m in self.mobjects if m is not keep]
        self.play(FadeOut(Group(*ms)), run_time=0.5)
        self.remove(*ms)
        spin = rotating_knot(self, comps_of(trefoil_pts(500)), 0.55, UP * 1.1, speed=0.45, tilt=0.45, width=7,
                             grad=[CYAN, MAGENTA, GOLD])
        self.add(spin)
        th = zh("感谢观看", 64, INK, weight=HEAVY).move_to(DOWN * 1.35)
        ref = zh("参考：W. B. R. Lickorish《An Introduction to Knot Theory》", 24, DIM).next_to(th, DOWN, buff=0.3)
        vo = zh("配音：千问 Qwen TTS", 24, DIM).next_to(ref, DOWN, buff=0.12)
        self.play(FadeIn(th, shift=UP * 0.3), run_time=0.8)
        self.play(FadeIn(ref), FadeIn(vo), run_time=0.8)
        self.wait_to(self.total - 0.8)
        self.clear_stage(0.7)
        self.finish()
