# -*- coding: utf-8 -*-
from common import *


def closed_path(pts, n=300):
    """Resample a polyline (closed) to n points (z=0)."""
    P = np.array(pts, float)
    if P.shape[1] == 2:
        P = np.column_stack([P, np.zeros(len(P))])
    sc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))])
    s = np.linspace(0, sc[-1], n, endpoint=False)
    out = np.zeros((n, 3))
    for k in range(3):
        out[:, k] = np.interp(s, sc, np.concatenate([P[:, k], P[:1, k]]))
    return out


def slide_curves(ca, ra, cb, rb, n=320, gap=0.3):
    """Component A (circle) before/after sliding over a parallel copy of B."""
    t = np.linspace(0, TAU_, n, endpoint=False)
    A0 = np.stack([ca[0] + ra * np.cos(t), ca[1] + ra * np.sin(t), np.zeros(n)], 1)
    # after: left half of A, band to B, go once around a push-off of B, band back
    R = rb + gap
    left = [(ca[0] + ra * np.cos(a), ca[1] + ra * np.sin(a)) for a in np.linspace(PI / 2 - 0.25, 3 * PI / 2 + 0.25, 60)]
    b0 = PI + 0.22
    around = [(cb[0] + R * np.cos(a), cb[1] + R * np.sin(a)) for a in np.linspace(b0, b0 - TAU_ + 0.44, 120)]
    pts = left + around
    A1 = smooth_closed(closed_path(pts, n), 6)
    # align starting points for a pleasant morph
    j = np.argmin(np.linalg.norm(A1[:, :2] - A0[0, :2], axis=1))
    A1 = np.roll(A1, -j, axis=0)
    return A0, A1


# =====================================================================  10
class Ch10(Chapter):
    CH = 10

    def construct(self):
        self.intro_level()
        # s1: quadratic form on the Seifert surface
        self.at(1)
        S = seifert_schematic(0.85).move_to(LEFT * 3.4 + UP * 0.1)
        self.play(FadeIn(S, shift=UP * 0.3), run_time=1.0)
        push = DashedVMobject(S.curves[0][0].copy().set_stroke(RED_N, 3).shift(UP * 0.18 + RIGHT * 0.12), num_dashes=40)
        xl = tex("x", 44, RED_N).move_to(S.bands[0].point_from_proportion(0.3) + LEFT * 0.7)
        xp = tex("x^{+}", 40, RED_N).next_to(xl, UP, buff=0.3)
        self.play(Create(push), FadeIn(xl), FadeIn(xp), run_time=1.2)
        q = tex(r"q(x) = \operatorname{lk}(x,\ x^{+}) \bmod 2", 50, GOLD).move_to(RIGHT * 3.0 + UP * 1.0)
        dom = tex(r"x \in H_1(F;\ \mathbb{Z}/2)", 42, DIM).next_to(q, DOWN, buff=0.4)
        self.play(Write(q), run_time=1.4)
        self.play(FadeIn(dom), run_time=0.6)
        # s2: majority vote
        self.at(2)
        self.play(FadeOut(VGroup(S, push, xl, xp, dom)), q.animate.scale(0.8).to_edge(UP, buff=1.0), run_time=0.6)
        elems = ["0", "a", "b", "a+b"]
        vals = [0, 1, 1, 1]
        cols = VGroup()
        for e, v in zip(elems, vals):
            ee = tex(e, 46)
            box = RoundedRectangle(width=1.6, height=1.0, corner_radius=0.12).set_stroke(DIM, 2)
            vv = tex(f"q = {v}", 40, LIME if v == 0 else MAGENTA)
            col = VGroup(ee, box.copy().add(vv.move_to(box))).arrange(DOWN, buff=0.25)
            cols.add(col)
        cols.arrange(RIGHT, buff=0.6).move_to(LEFT * 2.0 + UP * 0.1)
        self.play(LaggedStart(*[FadeIn(c[0]) for c in cols], lag_ratio=0.2), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(c[1], scale=0.7) for c in cols], lag_ratio=0.3), run_time=1.6)
        bars = VGroup(
            Rectangle(width=0.7, height=0.6).set_fill(LIME, 0.7).set_stroke(width=0),
            Rectangle(width=0.7, height=1.8).set_fill(MAGENTA, 0.7).set_stroke(width=0))
        bars.arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to(RIGHT * 4.4 + DOWN * 0.1)
        bl = VGroup(tex("0", 36, LIME).next_to(bars[0], DOWN, buff=0.15), tex("1", 36, MAGENTA).next_to(bars[1], DOWN, buff=0.15))
        self.wait_to(self.S(2) + self.D(2) * 0.5)
        self.play(GrowFromEdge(bars[0], DOWN), GrowFromEdge(bars[1], DOWN), FadeIn(bl), run_time=1.0)
        arf = tex(r"\operatorname{Arf}(q) = 1", 52, MAGENTA).next_to(bars, UP, buff=0.4)
        self.play(Write(arf), run_time=0.8)
        # s3: Arf via the Conway polynomial
        self.at(3)
        self.play(FadeOut(VGroup(cols, bars, bl, arf, q)), run_time=0.5)
        c1 = tex(r"\nabla_K(z) = 1 + a_2 z^2 + a_4 z^4 + \cdots", 50).move_to(UP * 1.2)
        c2 = tex(r"\operatorname{Arf}(K) \equiv a_2 \pmod 2", 54, GOLD).next_to(c1, DOWN, buff=0.5)
        c3 = tex(r"\nabla_{3_1} = 1 + 1\cdot z^2 \ \Rightarrow\ \operatorname{Arf}(3_1) = 1", 46, CYAN).next_to(c2, DOWN, buff=0.5)
        self.play(Write(c1), run_time=1.2)
        self.play(Write(c2), run_time=1.2)
        self.wait_to(self.S(3) + self.D(3) * 0.6)
        self.play(Write(c3), run_time=1.4)
        # s4: Levine
        self.at(4)
        self.play(FadeOut(VGroup(c1, c2, c3)), run_time=0.4)
        lv = tex(r"\operatorname{Arf}(K) = 0 \iff \Delta_K(-1) \equiv \pm 1 \pmod 8", 52, GOLD).move_to(UP * 1.0)
        nm = zh("莱文", 30, DIM).next_to(lv, UP, buff=0.3)
        ex = tex(r"\Delta_{3_1}(-1) = 3 \not\equiv \pm 1 \ \Rightarrow\ \operatorname{Arf} = 1", 44, CYAN).next_to(lv, DOWN, buff=0.6)
        self.play(FadeIn(nm), Write(lv), run_time=1.6)
        self.play(Write(ex), run_time=1.4)
        # s5: Jones at t = i
        self.at(5)
        self.play(FadeOut(VGroup(lv, nm, ex)), run_time=0.4)
        circ = Circle(radius=1.5).set_stroke(DIM, 2).move_to(LEFT * 4.0 + UP * 0.2)
        ax = VGroup(Line(circ.get_left() + LEFT * 0.3, circ.get_right() + RIGHT * 0.3),
                    Line(circ.get_bottom() + DOWN * 0.3, circ.get_top() + UP * 0.3)).set_stroke(DIM, 1.5, 0.6)
        ip = glow(Dot(circ.get_top(), 0.11, color=WHITE), GOLD)
        il = tex(r"t = i", 40, GOLD).next_to(ip, RIGHT, buff=0.2)
        self.play(Create(circ), FadeIn(ax), run_time=0.8)
        self.play(FadeIn(ip, scale=2), FadeIn(il), run_time=0.6)
        big = tex(r"V_K(i) = (-1)^{\operatorname{Arf}(K)}", 66, GOLD).move_to(RIGHT * 2.0 + UP * 0.2)
        bx = SurroundingRectangle(big, buff=0.3, corner_radius=0.12).set_stroke(GOLD, 3)
        self.play(Write(big), run_time=1.6)
        self.play(Create(bx), run_time=0.6)
        self.play(Flash(bx.get_corner(UR), color=GOLD, flash_radius=0.5), run_time=0.6)
        # s6: check on the trefoil
        self.at(6)
        self.play(FadeOut(VGroup(circ, ax, ip, il, bx)), big.animate.scale(0.7).to_edge(UP, buff=1.0), run_time=0.6)
        st1 = texs(r"V(i) = ", r"i", r"+", r"i^{3}", r"-", r"i^{4}", size=60).move_to(UP * 0.4)
        st2 = texs(r"V(i) = ", r"i", r"-", r"i", r"-", r"1", size=60).move_to(UP * 0.4)
        st3 = tex(r"V(i) = -1", 66, MAGENTA).move_to(UP * 0.4)
        self.play(Write(st1), run_time=1.0)
        self.play(TransformMatchingTex(st1, st2), run_time=1.0)
        cancel = VGroup(Line(st2[1].get_corner(DL), st2[1].get_corner(UR)), Line(st2[3].get_corner(DL), st2[3].get_corner(UR)))
        cancel.set_stroke(RED_N, 5)
        self.play(Create(cancel), run_time=0.6)
        self.play(FadeOut(cancel), ReplacementTransform(st2, st3), run_time=0.8)
        ok = VGroup(tex(r"\operatorname{Arf}(3_1) = 1", 46, CYAN), check_mark(size=0.5)).arrange(RIGHT, buff=0.4).next_to(st3, DOWN, buff=0.6)
        self.play(FadeIn(ok, shift=UP * 0.2), run_time=0.6)
        # s7: bridge between eras
        self.at(7)
        self.play(FadeOut(VGroup(big, st3, ok)), run_time=0.4)
        a = VGroup(mono("1941", 40, CYAN), zh("阿尔夫 · 二次型", 30)).arrange(DOWN, buff=0.2).move_to(LEFT * 4 + DOWN * 0.3)
        b = VGroup(mono("1984", 40, MAGENTA), zh("琼斯多项式", 30)).arrange(DOWN, buff=0.2).move_to(RIGHT * 4 + DOWN * 0.3)
        arc = ArcBetweenPoints(a.get_top() + UP * 0.2, b.get_top() + UP * 0.2, angle=-1.6).set_stroke(GOLD, 5)
        arc_g = glow(arc, GOLD)
        mid = tex(r"t = i", 44, GOLD).move_to(arc.point_from_proportion(0.5) + UP * 0.4)
        self.play(FadeIn(a, shift=RIGHT * 0.3), FadeIn(b, shift=LEFT * 0.3), run_time=0.8)
        self.play(Create(arc_g), FadeIn(mid), run_time=1.4)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  11
class Ch11(Chapter):
    CH = 11

    def construct(self):
        self.intro_level()
        tp = trefoil_pts(400)
        sh = LEFT * 3.0 + DOWN * 0.2
        scl = 0.62
        # s1: knot group = loops in the complement
        self.at(1)
        kd = KnotDiagram(comps_of(tp), scale=scl, shift=sh, colors=[CYAN])
        self.play(Create(kd), run_time=1.0)
        base = sh + UP * 2.6 + RIGHT * 0.2
        bp = VGroup(glow(Dot(base, 0.09, color=WHITE), GOLD), tex("*", 40, GOLD).next_to(base, RIGHT, buff=0.1))
        self.play(FadeIn(bp, scale=2), run_time=0.5)
        P = to_scene(tp, scl, sh)
        piece_mid = [kd.pieces[k]["pts"][len(kd.pieces[k]["pts"]) // 2] for k in range(3)]
        mids = [np.array([*(m[:2] * scl), 0]) + sh for m in piece_mid]

        def lasso(target, wob=0.0):
            d = normalize(target - base)
            nrm = np.array([-d[1], d[0], 0])
            pts = [base, base + (target - base) * 0.5 + nrm * (0.25 + wob), target + nrm * 0.28 + d * 0.05,
                   target + d * 0.32, target - nrm * 0.28 + d * 0.05, base + (target - base) * 0.5 - nrm * (0.25 - wob), base]
            m = VMobject().set_points_smoothly(pts)
            return m.set_stroke(GOLD, 4)

        l1 = lasso(mids[0])
        l2 = lasso(mids[1])
        self.play(Create(l1), run_time=0.9)
        self.play(Transform(l1, lasso(mids[0], 0.5)), run_time=0.8)
        self.play(Transform(l1, lasso(mids[0], -0.1)), Create(l2), run_time=0.9)
        pi1 = tex(r"\pi_1\big(S^3 - K,\ *\big)", 56, GOLD).move_to(RIGHT * 3.2 + UP * 0.6)
        nm = zh("扭结群", 36, INK).next_to(pi1, DOWN, buff=0.35)
        self.play(Write(pi1), FadeIn(nm), run_time=1.2)
        # s2: Wirtinger generators
        self.at(2)
        self.play(FadeOut(VGroup(l1, l2, bp, pi1, nm)), run_time=0.4)
        gens = VGroup()
        for k, m in enumerate(mids):
            out = normalize(m - kd.get_center())
            lab = tex(f"x_{k + 1}", 44, [RED_N, LIME, SKY][k]).move_to(m + out * 0.6)
            ring = Ellipse(width=0.55, height=0.25).set_stroke([RED_N, LIME, SKY][k], 3).move_to(m)
            seg = kd.pieces[k]["pts"]
            j = len(seg) // 2
            tang = seg[j + 1] - seg[j - 1]
            ring.rotate(np.arctan2(tang[1], tang[0]) + PI / 2)
            tip = arrow_tip(ring.point_from_proportion(0.25), ring.point_from_proportion(0.27) - ring.point_from_proportion(0.23),
                            [RED_N, LIME, SKY][k], 0.14)
            gens.add(VGroup(ring, tip, lab))
        colored = KnotDiagram(comps_of(tp), scale=scl, shift=sh, color_fn=lambda k, p: [RED_N, LIME, SKY][k % 3])
        self.play(Transform(kd, colored), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(g, scale=1.3) for g in gens], lag_ratio=0.3), run_time=1.4)
        rule = VGroup(zh("每段弧 → 生成元", 32, INK), zh("每个交叉点 → 一条关系", 32, INK)).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        rule.move_to(RIGHT * 3.4 + UP * 0.4)
        self.wait_to(self.S(2) + self.D(2) * 0.5)
        self.play(FadeIn(rule[0], shift=LEFT * 0.2), run_time=0.6)
        self.wait_to(self.S(2) + self.D(2) * 0.78)
        self.play(FadeIn(rule[1], shift=LEFT * 0.2), run_time=0.6)
        # s3: the Wirtinger relation at one crossing
        self.at(3)
        self.play(FadeOut(rule), run_time=0.3)
        cx = colored_cross(GOLD, CYAN, MAGENTA, 2.2, width=8).move_to(RIGHT * 3.3 + UP * 0.7)
        li = tex("x_i", 44, GOLD).move_to(cx.get_corner(UR) + RIGHT * 0.15)
        lj = tex("x_j", 44, CYAN).move_to(cx.get_corner(DR) + RIGHT * 0.15)
        lk = tex("x_k", 44, MAGENTA).move_to(cx.get_corner(UL) + LEFT * 0.15)
        self.play(FadeIn(cx, scale=0.8), FadeIn(VGroup(li, lj, lk)), run_time=1.0)
        rel = tex(r"x_k = x_i\, x_j\, x_i^{-1}", 54, INK).move_to(RIGHT * 3.3 + DOWN * 1.4)
        self.play(Write(rel), run_time=1.4)
        # s4: trefoil group
        self.at(4)
        self.play(FadeOut(VGroup(cx, li, lj, lk, rel)), run_time=0.4)
        g1 = tex(r"\langle x_1, x_2, x_3 \mid x_3 = x_1x_2x_1^{-1},\ x_1 = x_2x_3x_2^{-1},\ x_2 = x_3x_1x_3^{-1} \rangle", 32)
        g1.move_to(RIGHT * 2.2 + UP * 1.4)
        if g1.width > 8.2:
            g1.scale_to_fit_width(8.2)
        arr = tex(r"\Downarrow", 50, DIM).next_to(g1, DOWN, buff=0.3)
        g2 = tex(r"\langle x, y \mid xyx = yxy \rangle", 64, GOLD).next_to(arr, DOWN, buff=0.3)
        self.play(Write(g1), run_time=1.6)
        self.play(FadeIn(arr), run_time=0.3)
        self.play(Write(g2), run_time=1.2)
        bx = SurroundingRectangle(g2, buff=0.2, corner_radius=0.1).set_stroke(GOLD, 3)
        self.play(Create(bx), run_time=0.5)
        # s5: unknot vs trefoil; map onto S3
        self.at(5)
        self.play(FadeOut(VGroup(kd, gens, g1, arr)), VGroup(g2, bx).animate.scale(0.75).move_to(RIGHT * 3.2 + UP * 2.0), run_time=0.6)
        unk = KnotDiagram(comps_of(circle_pts(120, 1.2)), scale=0.7, shift=LEFT * 4.6 + UP * 0.4, colors=[INK])
        ug = tex(r"\pi_1 = \mathbb{Z}", 46).next_to(unk, DOWN, buff=0.3)
        self.play(Create(unk), FadeIn(ug), run_time=0.9)
        tri = Triangle().scale(1.25).move_to(RIGHT * 0.4 + DOWN * 0.1).set_stroke(INK, 3)
        vs = tri.get_vertices()
        vd = VGroup(*[Dot(v, 0.13, color=c) for v, c in zip(vs, TRI)])
        m1 = DashedLine(vs[0], (vs[1] + vs[2]) / 2, dash_length=0.1).set_stroke(GOLD, 3)
        m2 = DashedLine(vs[1], (vs[0] + vs[2]) / 2, dash_length=0.1).set_stroke(GOLD, 3)
        self.play(Create(tri), FadeIn(vd), run_time=0.8)
        mp = VGroup(tex(r"x \mapsto (1\,2)", 42, GOLD), tex(r"y \mapsto (2\,3)", 42, GOLD)).arrange(DOWN, buff=0.3)
        mp.move_to(RIGHT * 4.2 + DOWN * 0.2)
        s3 = tex(r"\twoheadrightarrow S_3", 50, GOLD).next_to(mp, DOWN, buff=0.4)
        self.play(Create(m1), Create(m2), FadeIn(mp), run_time=1.0)
        self.play(Write(s3), run_time=0.7)
        self.play(Rotate(VGroup(tri, vd), PI, axis=(vs[0] - (vs[1] + vs[2]) / 2), about_point=tri.get_center()), run_time=1.0)
        eq = zh("= 三染色", 32, LIME).next_to(s3, DOWN, buff=0.3)
        self.play(FadeIn(eq), run_time=0.5)
        # s6: Fox calculus; Gordon-Luecke
        self.at(6)
        self.clear_stage(0.4)
        fx = tex(r"\frac{\partial (xyx\,y^{-1}x^{-1}y^{-1})}{\partial x}\Big|_{x,y \mapsto t} = 1 - t + t^{2} = \Delta_{3_1}(t)", 46)
        fx.move_to(UP * 1.1)
        fl = zh("福克斯自由微分", 30, CYAN).next_to(fx, UP, buff=0.35)
        self.play(FadeIn(fl), Write(fx), run_time=2.0)
        gl = VGroup(mono("1989", 36, MAGENTA), zh("戈登 – 吕克：扭结由补空间完全决定", 34, INK)).arrange(RIGHT, buff=0.4)
        gl.move_to(DOWN * 1.2)
        self.wait_to(self.S(6) + self.D(6) * 0.55)
        self.play(FadeIn(gl, shift=UP * 0.2), run_time=0.9)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  12
def surgery_label(diag, txt, color=GOLD, size=40):
    return tex(txt, size, color).next_to(diag, UR, buff=-0.05)


class Ch12(Chapter):
    CH = 12

    def construct(self):
        self.intro_level()
        # s1: Dehn surgery on a torus
        self.at(1)
        sh = LEFT * 2.6 + UP * 0.1
        t0 = self.time

        def scene_torus():
            ang = (self.time - t0) * 0.25
            rot = rot_matrix(-1.05 + 0.12 * np.sin(ang), 0, 0) @ rot_matrix(0, 0, ang * 0.6)
            g = torus_wire(rot, 1.0, sh, R=2.0, r=0.75, nu=28, nv=12, color=SKY, width=1.4)
            if show.get_value() > 0.5:
                v = np.linspace(0, TAU_, 80)
                g.add(depth_curve(torus_point(np.full_like(v, 0.6), v, 2.0, 0.75), rot, 1.0, sh, RED_N, 5, 1.0, 16))
                u = np.linspace(0, TAU_, 160)
                g.add(depth_curve(torus_point(u, np.full_like(u, PI / 2), 2.0, 0.75), rot, 1.0, sh, LIME, 5, 1.0, 30))
            if pq.get_value() > 0.5:
                s_ = np.linspace(0, TAU_, 400)
                g.add(depth_curve(torus_point(2 * s_, 3 * s_, 2.0, 0.75), rot, 1.0, sh, GOLD, 6, 1.0, 70))
            return g

        show = ValueTracker(0)
        pq = ValueTracker(0)
        tor = always_redraw(scene_torus)
        self.play(FadeIn(tor), run_time=1.0)
        lab = VGroup(zh("挖掉扭结的实心环面邻域", 30), zh("边界是一个环面", 30, DIM)).arrange(DOWN, buff=0.2)
        lab.move_to(RIGHT * 3.6 + UP * 1.8)
        self.play(FadeIn(lab), run_time=0.6)
        show.set_value(1)
        ml = VGroup(tex(r"\mu", 46, RED_N), zh("经线", 28, RED_N)).arrange(RIGHT, buff=0.15)
        ll = VGroup(tex(r"\lambda", 46, LIME), zh("纬线", 28, LIME)).arrange(RIGHT, buff=0.15)
        VGroup(ml, ll).arrange(RIGHT, buff=0.6).move_to(RIGHT * 3.6 + UP * 0.4)
        self.play(FadeIn(ml), FadeIn(ll), run_time=0.6)
        self.wait_to(self.S(1) + self.D(1) * 0.5)
        pq.set_value(1)
        glue = tex(r"\mu' \ \longmapsto\ p\,\mu + q\,\lambda", 52, GOLD).move_to(RIGHT * 3.6 + DOWN * 0.8)
        self.play(Write(glue), run_time=1.2)
        dn = zh("德恩手术", 36, GOLD, weight=BOLD).next_to(glue, DOWN, buff=0.35)
        self.wait_to(self.S(1) + self.D(1) * 0.85)
        self.play(FadeIn(dn, scale=1.2), run_time=0.6)
        # s2: examples
        self.at(2)
        self.play(FadeOut(frozen(tor)), FadeOut(VGroup(lab, ml, ll, glue, dn)), run_time=0.5)
        exs = VGroup()
        data = [(comps_of(circle_pts(120, 1.0)), 0.75, "0", r"S^2 \times S^1"),
                (comps_of(circle_pts(120, 1.0)), 0.75, "p", r"L(p,1)"),
                (comps_of(trefoil_pts()), 0.33, r"\pm 1", r"\text{Poincar\'e }\Sigma(2,3,5)")]
        for comps, scl, fr, res in data:
            d = KnotDiagram(comps, scale=scl, colors=[CYAN])
            fl = surgery_label(d, fr)
            arrow = tex(r"\Downarrow", 44, DIM).next_to(d, DOWN, buff=0.3)
            r = tex(res, 40, MAGENTA).next_to(arrow, DOWN, buff=0.25)
            exs.add(VGroup(d, fl, arrow, r))
        exs.arrange(RIGHT, buff=1.2).move_to(UP * 0.2)
        for e in exs:
            e[2].align_to(exs[0][2], UP)
            e[3].next_to(e[2], DOWN, buff=0.25)
        pcl = zh("庞加莱同调球面", 26, DIM).next_to(exs[2][3], DOWN, buff=0.2)
        sd = self.D(2)
        for i, e in enumerate(exs):
            self.wait_to(self.S(2) + sd * [0.0, 0.3, 0.55][i])
            self.play(FadeIn(e, shift=UP * 0.3), run_time=0.8)
        self.play(FadeIn(pcl), run_time=0.4)
        # s3: Lickorish-Wallace
        self.at(3)
        self.play(FadeOut(VGroup(exs, pcl)), run_time=0.4)
        card = panel(11.6, 2.0, GOLD, 0.07, 0.9).move_to(UP * 1.4)
        c1 = zh("任何闭的、连通的、可定向三维流形", 36, INK).move_to(card.get_center() + UP * 0.4)
        c2 = zh("= 三维球面中某个链环上的整数手术", 36, GOLD).move_to(card.get_center() + DOWN * 0.4)
        who = mono("LICKORISH · WALLACE  1960–62", 26, MAGENTA).next_to(card, UP, buff=0.2)
        self.play(FadeIn(card), FadeIn(who), run_time=0.6)
        self.play(Write(c1), run_time=1.4)
        self.play(Write(c2), run_time=1.4)
        bor = KnotDiagram(comps_of(*borromean_pts()), scale=0.55, shift=LEFT * 1.4 + DOWN * 1.5, colors=[RED_N, LIME, SKY])
        zs = VGroup(*[tex("0", 34, c) for c in (RED_N, LIME, SKY)])
        for z_, k in zip(zs, range(3)):
            a = PI / 2 + k * TAU_ / 3
            z_.move_to(bor.get_center() + 1.15 * np.array([np.cos(a), np.sin(a), 0]))
        t3 = VGroup(tex(r"\Longrightarrow", 46, DIM), tex(r"T^3 = S^1\times S^1\times S^1", 44, MAGENTA)).arrange(RIGHT, buff=0.3)
        t3.next_to(bor, RIGHT, buff=0.6)
        self.wait_to(self.S(3) + self.D(3) * 0.62)
        self.play(Create(bor), FadeIn(zs), run_time=1.2)
        self.play(FadeIn(t3, shift=LEFT * 0.2), run_time=0.7)
        # s4: the author
        self.at(4)
        self.play(FadeOut(VGroup(card, c1, c2, who, bor, zs, t3)), run_time=0.4)
        book = RoundedRectangle(width=3.0, height=4.0, corner_radius=0.08).set_fill("#13213a", 1).set_stroke(GOLD, 3)
        spine = Rectangle(width=0.25, height=4.0).set_fill(GOLD, 0.8).set_stroke(width=0).align_to(book, LEFT)
        bt = VGroup(mono("An Introduction", 20, INK), mono("to Knot Theory", 20, INK)).arrange(DOWN, buff=0.08)
        bk = KnotDiagram(comps_of(trefoil_pts()), scale=0.26, colors=[CYAN], width=4)
        ba = mono("W. B. R. Lickorish", 18, GOLD)
        bg = VGroup(bt, bk, ba).arrange(DOWN, buff=0.35).move_to(book).shift(RIGHT * 0.1)
        B = VGroup(book, spine, bg).move_to(LEFT * 2.6 + DOWN * 0.1)
        gtm = mono("GTM 175", 22, DIM).next_to(B, DOWN, buff=0.2)
        self.play(FadeIn(B, shift=UP * 0.3), FadeIn(gtm), run_time=0.8)
        au = zh("作者 = 利科里什本人", 38, GOLD, weight=BOLD).move_to(RIGHT * 2.8 + UP * 0.2)
        self.play(Write(au), run_time=1.0)
        # s5: many diagrams, one manifold
        self.at(5)
        self.play(FadeOut(VGroup(B, gtm, au)), run_time=0.4)
        d1 = KnotDiagram(comps_of(circle_pts(120, 1.0)), scale=0.8, shift=LEFT * 4.2 + UP * 0.3, colors=[CYAN])
        d2 = KnotDiagram(comps_of(circle_pts(120, 1.0)), scale=0.8, shift=LEFT * 0.0 + UP * 0.3, colors=[MAGENTA])
        l1 = surgery_label(d1, "+1")
        l2 = surgery_label(d2, "-1", MAGENTA)
        empty = DashedVMobject(Square(1.6), num_dashes=24).set_stroke(DIM, 2).move_to(RIGHT * 4.2 + UP * 0.3)
        el = zh("空图", 28, DIM).move_to(empty)
        eqs = VGroup(tex("=", 60).move_to(LEFT * 2.1 + UP * 0.3), tex("=", 60).move_to(RIGHT * 2.1 + UP * 0.3))
        s3l = VGroup(zh("全都是", 36, GOLD), tex(r"S^3", 54, GOLD)).arrange(RIGHT, buff=0.2).move_to(DOWN * 1.6)
        self.play(Create(d1), FadeIn(l1), run_time=0.8)
        self.play(FadeIn(eqs[0]), Create(d2), FadeIn(l2), run_time=0.8)
        self.play(FadeIn(eqs[1]), Create(empty), FadeIn(el), run_time=0.8)
        self.play(FadeIn(s3l), run_time=0.5)
        # s6: Kirby moves
        self.at(6)
        self.play(FadeOut(VGroup(d1, d2, l1, l2, empty, el, eqs, s3l)), run_time=0.4)
        p1 = labeled_panel("K1", 5.6, 4.2, CYAN).move_to(LEFT * 3.2 + DOWN * 0.1)
        p2 = labeled_panel("K2", 5.6, 4.2, MAGENTA).move_to(RIGHT * 3.2 + DOWN * 0.1)
        self.play(FadeIn(p1), FadeIn(p2), run_time=0.5)
        base = KnotDiagram(comps_of(trefoil_pts()), scale=0.3, shift=p1[0].get_center() + LEFT * 1.0, colors=[CYAN], width=5)
        bl = surgery_label(base, "n", CYAN, 32)
        u1 = KnotDiagram(comps_of(circle_pts(100, 0.5)), scale=1.0, shift=p1[0].get_center() + RIGHT * 1.4, colors=[GOLD], width=5)
        ul = tex(r"\pm 1", 32, GOLD).next_to(u1, UP, buff=0.1)
        cap1 = zh("添加 / 删除 ±1 孤立圆圈", 24, CYAN).next_to(p1[0], DOWN, buff=-0.55)
        self.play(Create(base), FadeIn(bl), FadeIn(cap1), run_time=0.8)
        self.play(FadeIn(u1, scale=0.3), FadeIn(ul), run_time=0.7)
        self.play(FadeOut(u1, scale=0.3), FadeOut(ul), run_time=0.6)
        self.play(FadeIn(u1, scale=0.3), FadeIn(ul), run_time=0.6)
        c2c = p2[0].get_center()
        A0, A1 = slide_curves(np.array([-1.3, 0.0]), 0.6, np.array([0.7, 0.0]), 0.75)
        B = circle_pts(200, 0.75, c=(0.7, 0.0, 0))
        tr = ValueTracker(0)
        Bd = KnotDiagram([Comp(B)], scale=1.0, shift=c2c, colors=[MAGENTA], width=5)
        Ad = knot_morph(self, [Comp(A0)], [Comp(A1)], tr, 1.0, c2c, width=5, colors=[LIME])
        cap2 = zh("柄滑动：一个分支滑过另一个", 24, MAGENTA).next_to(p2[0], DOWN, buff=-0.55)
        self.wait_to(self.S(6) + self.D(6) * 0.55)
        self.play(FadeIn(Bd), FadeIn(Ad), FadeIn(cap2), run_time=0.6)
        self.play(tr.animate.set_value(1), run_time=2.2)
        # s7: analogy
        self.at(7)
        self.clear_stage(0.4)
        tbl = VGroup(
            VGroup(zh("扭结", 40, CYAN), tex(r"\longleftrightarrow", 50, DIM), zh("赖德迈斯特变换", 40, CYAN)),
            VGroup(zh("三维流形", 40, MAGENTA), tex(r"\longleftrightarrow", 50, DIM), zh("柯比变换", 40, MAGENTA)))
        for r in tbl:
            r.arrange(RIGHT, buff=0.5)
        tbl.arrange(DOWN, buff=0.6).move_to(UP * 0.8)
        concl = zh("柯比变换下不变的链环不变量 ⇒ 三维流形不变量", 32, GOLD).next_to(tbl, DOWN, buff=0.7)
        self.play(FadeIn(tbl[0], shift=RIGHT * 0.3), run_time=0.7)
        self.play(FadeIn(tbl[1], shift=RIGHT * 0.3), run_time=0.7)
        self.wait_to(self.S(7) + self.D(7) * 0.45)
        self.play(Write(concl), run_time=1.4)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  13
class Ch13(Chapter):
    CH = 13

    def construct(self):
        self.intro_level()
        # s1: Witten; Reshetikhin-Turaev
        self.at(1)
        c1 = panel(5.6, 3.4, MAGENTA, 0.06, 0.8).move_to(LEFT * 3.1 + DOWN * 0.1)
        c2 = panel(5.6, 3.4, CYAN, 0.06, 0.8).move_to(RIGHT * 3.1 + DOWN * 0.1)
        w1 = VGroup(mono("WITTEN 1989", 30, MAGENTA), zh("陈–西蒙斯量子场论", 30),
                    tex(r"Z(M) = \int e^{\,2\pi i k\, CS(A)}\, \mathcal{D}A", 38, MAGENTA)).arrange(DOWN, buff=0.35).move_to(c1)
        w2 = VGroup(mono("RESHETIKHIN–TURAEV 1991", 24, CYAN), zh("量子群严格构造", 30),
                    tex(r"U_q(\mathfrak{sl}_2)", 48, CYAN)).arrange(DOWN, buff=0.35).move_to(c2)
        self.play(FadeIn(c1), FadeIn(w1, shift=UP * 0.2), run_time=1.2)
        self.wait_to(self.S(1) + self.D(1) * 0.5)
        self.play(FadeIn(c2), FadeIn(w2, shift=UP * 0.2), run_time=1.2)
        # s2: A a root of unity
        self.at(2)
        self.play(FadeOut(VGroup(c1, c2, w1, w2)), run_time=0.4)
        r = 5
        circ = Circle(radius=1.9).set_stroke(DIM, 2).move_to(LEFT * 3.0 + DOWN * 0.1)
        pts = VGroup(*[Dot(circ.get_center() + 1.9 * np.array([np.cos(TAU_ * k / (4 * r)), np.sin(TAU_ * k / (4 * r)), 0]),
                           0.07, color=SKY) for k in range(4 * r)])
        self.play(Create(circ), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, scale=2) for p in pts], lag_ratio=0.05), run_time=1.2)
        A = glow(Dot(pts[1].get_center(), 0.12, color=WHITE), GOLD)
        al = tex(r"A = e^{2\pi i/4r}", 42, GOLD).next_to(pts[1], RIGHT, buff=0.25)
        self.play(FadeIn(A, scale=2), FadeIn(al), run_time=0.6)
        txt = VGroup(zh("只用考夫曼括号", 34, INK), VGroup(zh("A 取", 34), tex(r"4r", 44, GOLD), zh("次本原单位根", 34))
                     .arrange(RIGHT, buff=0.15)).arrange(DOWN, buff=0.35).move_to(RIGHT * 3.2 + UP * 0.3)
        self.play(FadeIn(txt, shift=LEFT * 0.2), run_time=0.8)
        # s3: the element Omega
        self.at(3)
        self.play(FadeOut(VGroup(circ, pts, A, al, txt)), run_time=0.4)

        def colored_circle(label, color, rad=0.7):
            c = Circle(radius=rad).set_stroke(color, 6)
            box = Rectangle(width=0.62, height=0.38).set_fill("#0b1224", 1).set_stroke(color, 2.5).move_to(c.point_at_angle(0))
            t = tex(label, 26, color).move_to(box)
            return VGroup(glow(c, color), box, t)

        om = tex(r"\Omega \;=\; \sum_{n=0}^{r-2} \Delta_n \,\cdot", 60, GOLD)
        cc = colored_circle("f_n", GOLD)
        row1 = VGroup(om, cc).arrange(RIGHT, buff=0.3).move_to(UP * 0.8)
        self.play(Write(om), run_time=1.4)
        self.play(FadeIn(cc, scale=0.6), run_time=0.8)
        jw = zh("fₙ：琼斯–文茨尔幂等元（n 根平行线上的“过滤器”）", 28, DIM).next_to(row1, DOWN, buff=0.6)
        self.wait_to(self.S(3) + self.D(3) * 0.55)
        self.play(FadeIn(jw), run_time=0.8)
        # s4: decorate surgery link with Omega; sliding is free
        self.at(4)
        self.play(FadeOut(VGroup(row1, jw)), run_time=0.4)
        bor = KnotDiagram(comps_of(*borromean_pts()), scale=0.62, shift=LEFT * 3.6 + UP * 0.2, colors=[GOLD, GOLD, GOLD])
        oms = VGroup()
        for k in range(3):
            a = PI / 2 + k * TAU_ / 3
            oms.add(tex(r"\Omega", 38, GOLD).move_to(bor.get_center() + 1.35 * np.array([np.cos(a), np.sin(a), 0])))
        self.play(Create(bor), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(o, scale=1.6) for o in oms], lag_ratio=0.25), run_time=0.9)
        ctr = RIGHT * 2.8 + UP * 0.2
        A0, A1 = slide_curves(np.array([-1.4, 0.0]), 0.6, np.array([0.6, 0.0]), 0.75)
        Bc = circle_pts(200, 0.75, c=(0.6, 0.0, 0))
        tr = ValueTracker(0)
        Bd = KnotDiagram([Comp(Bc)], scale=1.0, shift=ctr, colors=[GOLD], width=6)
        bo = tex(r"\Omega", 40, GOLD).move_to(ctr + RIGHT * 0.6 + UP * 1.1)
        Ad = knot_morph(self, [Comp(A0)], [Comp(A1)], tr, 1.0, ctr, width=6, colors=[CYAN])
        self.wait_to(self.S(4) + self.D(4) * 0.4)
        self.play(FadeIn(Bd), FadeIn(bo), FadeIn(Ad), run_time=0.6)
        self.play(tr.animate.set_value(1), run_time=2.0)
        free = zh("滑过 Ω：括号值不变", 32, LIME).move_to(ctr + DOWN * 1.9)
        self.play(FadeIn(free, scale=1.2), run_time=0.6)
        self.play(tr.animate.set_value(0), run_time=1.6)
        # s5: normalisation -> WRT invariant
        self.at(5)
        self.clear_stage(0.4)
        f = tex(r"\tau(M) = \big\langle \Omega, \ldots, \Omega \big\rangle_{L}\;"
                r"\langle\Omega\rangle_{U_+}^{-b_+}\,\langle\Omega\rangle_{U_-}^{-b_-}", 52, INK).move_to(UP * 1.0)
        bpm = VGroup(tex(r"b_\pm", 40, CYAN), zh("：链环矩阵正 / 负特征值的个数", 30, CYAN)).arrange(RIGHT, buff=0.1)
        bpm.next_to(f, DOWN, buff=0.45)
        self.play(Write(f), run_time=2.0)
        self.play(FadeIn(bpm), run_time=0.7)
        wrt = mono("WITTEN–RESHETIKHIN–TURAEV", 34, GOLD).next_to(bpm, DOWN, buff=0.6)
        wz = zh("WRT 不变量", 36, GOLD, weight=BOLD).next_to(wrt, DOWN, buff=0.2)
        self.wait_to(self.S(5) + self.D(5) * 0.6)
        self.play(FadeIn(wrt, shift=UP * 0.2), FadeIn(wz), run_time=0.9)
        # s6: quantum topology
        self.at(6)
        self.clear_stage(0.4)
        kn = rotating_knot(self, comps_of(torus_pts(2, 5, 500)), 0.45, LEFT * 4.0 + UP * 0.3, speed=0.6, tilt=0.5,
                           width=6, grad=[CYAN, MAGENTA, GOLD])
        t0 = self.time
        tor = always_redraw(lambda: torus_wire(rot_matrix(-1.0, 0, 0) @ rot_matrix(0, 0, (self.time - t0) * 0.4), 0.75, RIGHT * 4.0 + UP * 0.3,
                                               2.0, 0.75, 22, 10, VIOLET, 1.4))
        arr = Arrow(LEFT * 2.0 + UP * 0.3, RIGHT * 1.6 + UP * 0.3, color=GOLD, stroke_width=6)
        self.add(kn)
        self.play(FadeIn(tor), GrowArrow(arr), run_time=1.0)
        qt = zh("量子拓扑", 64, INK, weight=HEAVY).move_to(DOWN * 1.9)
        qe = mono("QUANTUM TOPOLOGY", 28, CYAN).next_to(qt, UP, buff=0.2)
        self.wait_to(self.S(6) + self.D(6) * 0.5)
        self.play(FadeIn(qt, scale=1.3), FadeIn(qe), run_time=0.8)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()
