# -*- coding: utf-8 -*-
import json

from common import *
from rect_math import gamma, rect_from, aspect

with open(os.path.join(ROOT, "rect_family.json")) as _f:
    FAM = np.array(json.load(_f)["family"])
ASP = np.array([aspect(x) for x in FAM])
I_REP = int(np.argmin(np.abs(ASP - 0.62)))
I_SQ = int(np.argmax(ASP))
X_REP = FAM[I_REP]

CURVE_C = CYAN


def curve2d(scale=1.0, shift=ORIGIN, n=240):
    s = np.linspace(0, 1, n, endpoint=False)
    P = gamma(s) * scale
    pts = [np.array([p[0], p[1], 0]) + shift for p in P]
    m = VMobject()
    m.set_points_smoothly(pts + [pts[0]])
    return m


def g2(s, scale=1.0, shift=ORIGIN):
    p = gamma(s) * scale
    return np.array([p[0], p[1], 0]) + shift


def rect_pts(x, scale=1.0, shift=ORIGIN):
    return [np.array([p[0], p[1], 0]) * scale + shift for p in rect_from(x)]


def wild_radius_curve(scale, shift, amt):
    s = np.linspace(0, 1, 400, endpoint=False)
    th = TAU * s
    base = gamma(s)
    r = np.linalg.norm(base, axis=1)
    r2 = r * (1 + amt * (0.16 * np.sin(13 * th) + 0.1 * np.cos(21 * th + 0.7) + 0.08 * np.sin(8 * th + 2)))
    pts = [np.array([np.cos(t) * q, np.sin(t) * q, 0]) * scale + shift for t, q in zip(th, r2)]
    m = VMobject()
    m.set_points_smoothly(pts + [pts[0]])
    return m


class Rectangle2D(NScene):
    script_scene = "Rectangle"

    def body(self):
        self.chapter(5, "内接矩形", "The Inscribed Rectangle Problem")
        self.show_corner()
        SC, SH = 0.78, np.array([-2.9, 0.0, 0])

        # ---------------- setup
        self.seg("setup")
        stars = VGroup(*[Star(5, outer_radius=0.32, inner_radius=0.14).set_stroke(YELLOW, 2).set_fill(YELLOW, 0)
                         for _ in range(5)]).arrange(RIGHT, buff=0.25)
        diff = VGroup(zh("难度", 36, GREY_), stars).arrange(RIGHT, buff=0.4).move_to(UP * 0.3)
        self.play(FadeIn(diff, shift=UP * 0.2), run_time=0.6)
        self.play(LaggedStart(*[s.animate.set_fill(YELLOW, 1) for s in stars], lag_ratio=0.2), run_time=1.4)
        self.wait_until(self.sent_at(1))
        curve = curve2d(SC, SH).set_stroke(CURVE_C, 5)
        cg = neon(curve)
        self.play(FadeOut(diff), Create(cg), run_time=2.6)
        bad = smooth_path([(0, 0), (0.9, 0.7), (1.6, 0), (0.9, -0.7), (0, 0), (-0.9, 0.7), (-1.6, 0), (-0.9, -0.7)],
                          closed=True).set_stroke(GREY_, 4).scale(0.7).move_to([3.6, -1.6, 0])
        bad_x = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(RED, 6).scale(0.25).move_to(bad.get_center())
        bad_lab = zh("不能自交", 26, RED).next_to(bad, UP, buff=0.2)
        self.wait_until(self.phrase_at(1, "不能自己"))
        self.play(Create(bad), FadeIn(bad_lab), run_time=1.0)
        self.play(GrowFromCenter(bad_x), run_time=0.4)
        self.wait_until(self.sent_at(2))
        stmt_p = panel(5.8, 1.9, color=MAGENTA).move_to([3.6, 1.4, 0])
        st = VGroup(zh("证明：曲线上一定能找到", 32), zh("四个点，恰好构成矩形", 32, YELLOW, weight=BOLD)
                    ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(stmt_p)
        self.play(FadeOut(VGroup(bad, bad_x, bad_lab)), FadeIn(stmt_p), FadeIn(st, lag_ratio=0.2), run_time=1.2)
        R = rect_pts(X_REP, SC, SH)
        rdots = VGroup(*[glow_dot(p, YELLOW, 0.09, 4) for p in R])
        rpoly = DashedVMobject(Polygon(*R).set_stroke(YELLOW, 4), num_dashes=40)
        self.wait_until(self.phrase_at(2, "四个点"))
        self.play(LaggedStart(*[FadeIn(d, scale=3) for d in rdots], lag_ratio=0.2), run_time=1.0)
        self.play(Create(rpoly), run_time=1.0)
        self.sync(0.2)

        # ---------------- hard
        self.seg("hard")
        self.play(FadeOut(rdots), FadeOut(rpoly), run_time=0.5)
        wild = wild_radius_curve(SC, SH, 1.0).set_stroke(CURVE_C, 5)
        self.play(Transform(cg, neon(wild)), run_time=2.0)
        hardtxt = zh("无法直接构造", 40, RED, weight=BOLD).move_to([3.6, -1.0, 0])
        self.play(FadeIn(hardtxt, scale=1.2), run_time=0.6)
        self.wait_until(self._seg_end - 2.2)
        self.play(Transform(cg, neon(curve2d(SC, SH).set_stroke(CURVE_C, 5))), run_time=1.8)
        self.sync(0.1)

        # ---------------- criterion：矩形的判定
        self.seg("criterion")
        self.play(FadeOut(hardtxt), FadeOut(stmt_p), FadeOut(st), run_time=0.5)
        rc = np.array([3.6, 0.3, 0])
        A, B, C, D = [rc + np.array(v) for v in [(-1.6, -1.0, 0), (1.6, -1.0, 0), (1.6, 1.0, 0), (-1.6, 1.0, 0)]]
        rect = Polygon(A, B, C, D).set_stroke(WHITE_, 4)
        d1 = Line(A, C, color=CYAN, stroke_width=5)
        d2 = Line(B, D, color=MAGENTA, stroke_width=5)
        labs = VGroup(*[MathTex(t, font_size=36).next_to(p, dirn, buff=0.12) for t, p, dirn in
                        [("A", A, DL), ("B", B, DR), ("C", C, UR), ("D", D, UL)]])
        self.play(Create(rect), FadeIn(labs), run_time=1.0)
        d1g, d2g = neon(d1), neon(d2)
        self.play(Create(d1g), Create(d2g), run_time=1.0)
        self.wait_until(self.phrase_at(0, "中点相同"))
        O = glow_dot(rc, YELLOW, 0.1, 5)
        self.play(FadeIn(O, scale=3), burst(rc, YELLOW, r1=0.6), run_time=0.8)
        self.wait_until(self.phrase_at(0, "长度相等"))
        eqlen = MathTex("|AC|", "=", "|BD|", font_size=44).next_to(rect, DOWN, buff=0.4)
        eqlen[0].set_color(CYAN)
        eqlen[2].set_color(MAGENTA)
        self.play(Write(eqlen), ShowPassingFlash(d1.copy().set_stroke(WHITE, 9), time_width=0.6),
                  ShowPassingFlash(d2.copy().set_stroke(WHITE, 9), time_width=0.6), run_time=1.0)
        iff = VGroup(zh("中点相同", 28, YELLOW), zh("+", 28), zh("长度相等", 28, YELLOW),
                     MathTex(r"\Longleftrightarrow", font_size=40), zh("矩形", 28, WHITE_, weight=BOLD)).arrange(RIGHT, buff=0.15)
        iff.next_to(rect, UP, buff=0.45)
        self.play(FadeIn(iff, shift=DOWN * 0.2), run_time=0.8)
        self.sync(0.1)

        # ---------------- pairs：两对点
        self.seg("pairs")
        crit = VGroup(rect, labs, d1g, d2g, O, eqlen, iff)
        self.play(crit.animate.scale(0.6).move_to([4.6, 1.6, 0]), run_time=0.8)
        Rp = rect_pts(X_REP, SC, SH)
        c1 = Line(Rp[0], Rp[2], color=CYAN, stroke_width=5)
        c2 = Line(Rp[1], Rp[3], color=MAGENTA, stroke_width=5)
        pd = VGroup(*[glow_dot(p, col, 0.09, 3) for p, col in zip(Rp, [CYAN, MAGENTA, CYAN, MAGENTA])])
        self.play(Create(neon(c1)), FadeIn(pd[0]), FadeIn(pd[2]), run_time=0.9)
        self.play(Create(neon(c2)), FadeIn(pd[1]), FadeIn(pd[3]), run_time=0.9)
        mid = (Rp[0] + Rp[2]) / 2
        self.play(burst(mid, YELLOW, r1=0.6), FadeIn(glow_dot(mid, YELLOW, 0.1, 4), scale=3), run_time=0.8)
        txt = VGroup(zh("两对点", 32, WHITE_, weight=BOLD), zh("中点重合 · 距离相等", 32, YELLOW)).arrange(DOWN, buff=0.2)
        txt.move_to([3.8, -1.3, 0])
        self.play(FadeIn(txt, shift=UP * 0.2), run_time=0.7)
        self.play(Create(Polygon(*Rp).set_stroke(YELLOW, 4)), run_time=1.0)
        self.sync(0.6)
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not self.corner])), run_time=0.8)


# ------------------------------------------------------------------ 3D：点对 → 空间中的点
CS, HS = 0.8, 0.7


def tent(U, W):
    A = gamma(U) * CS
    B = gamma(U + W) * CS
    m = (A + B) / 2
    d = np.linalg.norm(A - B, axis=-1)
    return np.stack([m[..., 0], m[..., 1], HS * d], axis=-1)


def g3(s):
    p = gamma(s) * CS
    return np.array([p[0], p[1], 0.0])


def height_rgb(P):
    return lerp_rgb([PURPLE, BLUE, CYAN, GREEN], P[..., 2] / 2.8)


def curve3d_closed(color=CURVE_C, width=5, n=200):
    s = np.linspace(0, 1, n + 1)
    P = np.array([g3(x) for x in s])
    return FastPolyline(P, color, width)


class RectangleLift(NThreeDScene):
    script_scene = "Rectangle"

    def body(self):
        self.add_fixed_in_frame_mobjects(make_corner(5, "内接矩形"))
        self.set_camera_orientation(phi=62 * DEGREES, theta=-105 * DEGREES, zoom=0.95,
                                    frame_center=[0, 0, 1.0])
        floor = Rectangle(width=9, height=7).set_stroke(DIM, 1).set_fill("#0B1030", 0.6)
        floor.always_back = True
        base = curve3d_closed()
        base_g = VGroup(curve3d_closed(CURVE_C, 14, 120).set_stroke(opacity=0.18), base)

        # ---------------- lift
        self.seg("lift")
        self.play(FadeIn(floor), Create(base_g), run_time=1.8)
        title = VGroup(zh("一对点", 32), MathTex(r"\longrightarrow", font_size=40), zh("空间中的一个点", 32, YELLOW)).arrange(RIGHT, buff=0.2)
        title.to_edge(UP, buff=0.5).shift(RIGHT * 1.5)
        self.add_fixed_in_frame_mobjects(title)
        title.set_opacity(0)
        self.play(title.animate.set_opacity(1), run_time=0.8)
        self.begin_ambient_camera_rotation(rate=0.05)
        self.wait_until(self.sent_at(1))

        st = ValueTracker(0.08)
        tt = ValueTracker(0.47)

        def cur():
            s, t = st.get_value(), tt.get_value()
            Pp, Qp = g3(s), g3(t)
            M = (Pp + Qp) / 2
            X = M + np.array([0, 0, HS * np.linalg.norm(Pp - Qp)])
            return Pp, Qp, M, X

        chord = always_redraw(lambda: Line(cur()[0], cur()[1], color=ORANGE, stroke_width=5))
        dP = always_redraw(lambda: Dot3D(cur()[0], radius=0.09, color=ORANGE, resolution=(6, 6)))
        dQ = always_redraw(lambda: Dot3D(cur()[1], radius=0.09, color=ORANGE, resolution=(6, 6)))
        dM = always_redraw(lambda: Dot3D(cur()[2], radius=0.07, color=WHITE_, resolution=(6, 6)))
        vl = always_redraw(lambda: DashedLine(cur()[2], cur()[3], color=YELLOW, stroke_width=3))
        dX = always_redraw(lambda: Dot3D(cur()[3], radius=0.12, color=YELLOW, resolution=(8, 8)))
        self.play(FadeIn(dP), FadeIn(dQ), Create(chord), run_time=1.0)
        self.wait_until(self.phrase_at(1, "中点"))
        self.play(FadeIn(dM, scale=2), run_time=0.6)
        self.wait_until(self.phrase_at(1, "取高度"))
        self.play(Create(vl), run_time=1.0)
        self.play(FadeIn(dX, scale=3), run_time=0.6)
        rule = VGroup(zh("位置 = 中点", 28), zh("高度 = 两点距离", 28, YELLOW)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        rule.to_corner(UR, buff=0.5).shift(DOWN * 0.9)
        self.add_fixed_in_frame_mobjects(rule)
        rule.set_opacity(0)
        self.play(rule.animate.set_opacity(1), run_time=0.8)
        self.sync(0.1)

        # ---------------- surface
        self.seg("surface")
        trace = TracedPath(lambda: cur()[3], stroke_color=YELLOW, stroke_width=3, dissipating_time=None)
        self.add(trace)
        self.play(st.animate.set_value(0.38), tt.animate.set_value(0.92), run_time=3.0, rate_func=smooth)
        self.play(st.animate.set_value(0.6), tt.animate.set_value(0.75), run_time=2.0, rate_func=smooth)
        tent_s = FastSurface(tent, [0, 1], [0, 0.5], resolution=(72, 12), color_fn=height_rgb,
                             opacity=0.62, amb=0.45, stroke=0.4)
        self.play(FadeIn(tent_s), FadeOut(trace), run_time=2.0)
        self.wait_until(self.sent_at(1))
        self.play(tt.animate.set_value(0.6 + 0.004), run_time=self.until(self.phrase_at(1, "所以")), rate_func=smooth)
        self.play(ShowPassingFlash(curve3d_closed(WHITE, 10), time_width=0.4), run_time=2.0)
        edge_lab = zh("曲面的边缘 = 原曲线", 30, CYAN).to_corner(UR, buff=0.5).shift(DOWN * 2.2)
        self.add_fixed_in_frame_mobjects(edge_lab)
        edge_lab.set_opacity(0)
        self.play(edge_lab.animate.set_opacity(1), run_time=0.6)
        self.sync(0.1)

        # ---------------- goal
        self.seg("goal")
        for m in (chord, dP, dQ, dM, vl, dX):
            m.clear_updaters()
        self.play(FadeOut(VGroup(chord, dP, dQ, dM, vl, dX)), FadeOut(edge_lab), FadeOut(rule), run_time=0.6)
        s1, t1, s2, t2 = X_REP
        A, C, B, Dd = g3(s1), g3(t1), g3(s2), g3(t2)
        Mx = (A + C) / 2
        Xp = Mx + np.array([0, 0, HS * np.linalg.norm(A - C)])
        ch1 = Line(A, C, color=CYAN, stroke_width=6)
        ch2 = Line(B, Dd, color=MAGENTA, stroke_width=6)
        v1 = Line(Mx, Xp, color=YELLOW, stroke_width=4)
        bigX = Dot3D(Xp, radius=0.16, color=YELLOW, resolution=(8, 8))
        pts4 = VGroup(*[Dot3D(p, radius=0.09, color=c, resolution=(6, 6)) for p, c in
                        zip([A, B, C, Dd], [CYAN, MAGENTA, CYAN, MAGENTA])])
        self.play(Create(ch1), FadeIn(pts4[0]), FadeIn(pts4[2]), run_time=0.9)
        self.play(Create(ch2), FadeIn(pts4[1]), FadeIn(pts4[3]), run_time=0.9)
        self.play(Create(v1), FadeIn(bigX, scale=3), run_time=1.0)
        same = zh("两对点 → 同一个位置", 30, YELLOW).to_corner(UR, buff=0.5).shift(DOWN * 0.9)
        self.add_fixed_in_frame_mobjects(same)
        same.set_opacity(0)
        self.play(same.animate.set_opacity(1), run_time=0.6)
        rect = Polygon(A, B, C, Dd).set_stroke(YELLOW, 5)
        self.wait_until(self.phrase_at(0, "矩形就找到了"))
        self.play(Create(rect), run_time=1.0)
        self.wait_until(self.sent_at(1))
        goal = zh("只需证明：曲面一定自相交", 36, WHITE_, weight=BOLD)
        gbox = panel(goal.width + 0.8, 1.0, color=YELLOW)
        gg = VGroup(gbox, goal.move_to(gbox)).to_edge(DOWN, buff=0.8)
        self.add_fixed_in_frame_mobjects(gg)
        gg.set_opacity(0)
        self.play(gg.animate.set_opacity(1), run_time=0.8)
        self.sync(0.6)
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.9)


# ------------------------------------------------------------------ 2D：点对空间 = 莫比乌斯带
class RectanglePairs(NScene):
    script_scene = "Rectangle"

    def body(self):
        corner = make_corner(5, "内接矩形")
        self.add(corner)
        SC, SH = 0.42, np.array([-5.0, 1.2, 0])
        sq_c = np.array([1.6, -0.15, 0])
        S = 4.6

        def sq(s, t):  # 单位正方形坐标 → 屏幕
            return sq_c + np.array([(s - 0.5) * S, (t - 0.5) * S, 0])

        # ---------------- space1
        self.seg("space1")
        curve = curve2d(SC, SH).set_stroke(CURVE_C, 4)
        cg = neon(curve)
        st = ValueTracker(0.1)
        tt = ValueTracker(0.55)
        dP = always_redraw(lambda: glow_dot(g2(st.get_value() % 1, SC, SH), ORANGE, 0.08, 3))
        dQ = always_redraw(lambda: glow_dot(g2(tt.get_value() % 1, SC, SH), GREEN, 0.08, 3))
        lP = always_redraw(lambda: MathTex("P", font_size=30, color=ORANGE).next_to(dP, UP, buff=0.05))
        lQ = always_redraw(lambda: MathTex("Q", font_size=30, color=GREEN).next_to(dQ, UP, buff=0.05))
        self.play(Create(cg), run_time=1.2)
        self.play(FadeIn(dP), FadeIn(dQ), FadeIn(lP), FadeIn(lQ), run_time=0.6)
        q = zh("曲线上所有的点对 (P, Q)", 32, WHITE_).move_to([1.6, 2.9, 0])
        self.play(FadeIn(q, shift=DOWN * 0.2), st.animate.set_value(0.35), tt.animate.set_value(0.9), run_time=2.0)
        self.wait_until(self.sent_at(1))
        # 曲线 → 线段（横轴、纵轴）
        xaxis = Line(sq(0, 0), sq(1, 0), color=ORANGE, stroke_width=5)
        yaxis = Line(sq(0, 0), sq(0, 1), color=GREEN, stroke_width=5)
        c1 = curve.copy().set_stroke(ORANGE, 5)
        c2 = curve.copy().set_stroke(GREEN, 5)
        self.play(Transform(c1, xaxis), run_time=1.4)
        self.play(Transform(c2, yaxis), run_time=1.4)
        xl = zh("P 的位置", 26, ORANGE).next_to(xaxis, DOWN, buff=0.2)
        yl = zh("Q 的位置", 26, GREEN).rotate(PI / 2).next_to(yaxis, LEFT, buff=0.2)
        square = Square(S).move_to(sq_c).set_stroke(GREY_, 2).set_fill("#121A4A", 0.85)
        self.add(square)
        self.bring_to_back(square)
        self.play(FadeIn(square), FadeIn(xl), FadeIn(yl), run_time=0.8)
        pdot = always_redraw(lambda: glow_dot(sq(st.get_value() % 1, tt.get_value() % 1), YELLOW, 0.1, 4))
        self.play(FadeIn(pdot, scale=2), run_time=0.5)
        self.play(st.animate.set_value(0.8), tt.animate.set_value(0.3), run_time=2.2, rate_func=smooth)
        self.play(st.animate.set_value(0.2), tt.animate.set_value(0.7), run_time=2.0, rate_func=smooth)
        self.wait_until(self.phrase_at(1, "左右两边"))

        def arrows_on(a, b, col, n=1):
            mid = (a + b) / 2
            d = (b - a) / np.linalg.norm(b - a)
            return VGroup(*[Arrow(mid - d * 0.3 + d * 0.22 * k, mid + d * 0.2 + d * 0.22 * k, buff=0,
                                  stroke_width=6, color=col, max_tip_length_to_length_ratio=0.6)
                            for k in range(n)])

        lr = VGroup(arrows_on(sq(0, 0), sq(0, 1), CYAN), arrows_on(sq(1, 0), sq(1, 1), CYAN))
        tb = VGroup(arrows_on(sq(0, 0), sq(1, 0), MAGENTA, 2), arrows_on(sq(0, 1), sq(1, 1), MAGENTA, 2))
        self.play(FadeIn(lr), Indicate(VGroup(c2), color=CYAN), run_time=0.8)
        self.play(FadeIn(tb), run_time=0.8)
        self.wait_until(self.phrase_at(1, "环面"))
        tor = zh("= 环面", 32, WHITE_).next_to(square, RIGHT, buff=0.4)
        self.play(FadeIn(tor, shift=LEFT * 0.2), run_time=0.6)
        self.sync(0.1)

        # ---------------- space2：(P,Q) 与 (Q,P) 相同 → 对折
        self.seg("space2")
        self.play(FadeOut(tor), FadeOut(lr), FadeOut(tb), FadeOut(q), run_time=0.5)
        diag = DashedLine(sq(0, 0), sq(1, 1), color=WHITE_, stroke_width=3)
        p2 = always_redraw(lambda: glow_dot(sq(tt.get_value() % 1, st.get_value() % 1), YELLOW, 0.1, 4))
        link = always_redraw(lambda: DashedLine(sq(st.get_value() % 1, tt.get_value() % 1),
                                                sq(tt.get_value() % 1, st.get_value() % 1),
                                                color=YELLOW, stroke_width=2))
        self.play(Create(diag), FadeIn(p2, scale=2), Create(link), run_time=1.0)
        same = VGroup(MathTex("(P,Q)", font_size=40), zh("与", 28), MathTex("(Q,P)", font_size=40),
                      zh("是同一对点", 28, YELLOW)).arrange(RIGHT, buff=0.15).move_to([1.6, 2.9, 0])
        self.play(FadeIn(same, shift=DOWN * 0.2), st.animate.set_value(0.15), tt.animate.set_value(0.62), run_time=1.6)
        self.wait_until(self.phrase_at(0, "所以"))
        for m in (pdot, p2, link):
            m.clear_updaters()
        self.play(FadeOut(VGroup(pdot, p2, link)), run_time=0.4)
        upper = Polygon(sq(0, 0), sq(0, 1), sq(1, 1)).set_stroke(GREY_, 2).set_fill("#121A4A", 0.95)
        lower = Polygon(sq(0, 0), sq(1, 0), sq(1, 1)).set_stroke(GREY_, 2).set_fill("#1B2766", 0.95)
        self.remove(square)
        self.add(upper, lower)
        self.bring_to_back(upper, lower)
        self.remove(c1)
        self.play(Rotate(lower, PI, axis=np.array([1, 1, 0]), about_point=sq_c), FadeOut(xl), run_time=2.0)
        self.play(FadeOut(lower), upper.animate.set_fill("#18225C", 0.95), run_time=0.5)
        self.sync(0.1)

        # ---------------- space3：三角形的两条直角边按箭头相粘
        self.seg("space3")
        hyp = Line(sq(0, 0), sq(1, 1), color=GREEN, stroke_width=7)
        hyp_lab = zh("P = Q（两点重合）", 26, GREEN).next_to(hyp.get_center(), DR, buff=0.25)
        hyp_g = neon(hyp)
        self.play(FadeOut(diag), FadeOut(c2), FadeOut(yl), FadeOut(same), Create(hyp_g), FadeIn(hyp_lab), run_time=1.2)
        aL = arrows_on(sq(0, 0), sq(0, 1), YELLOW)
        aT = arrows_on(sq(0, 1), sq(1, 1), YELLOW)
        self.wait_until(self.phrase_at(0, "两条直角边"))
        self.play(ShowPassingFlash(Line(sq(0, 0), sq(0, 1)).set_stroke(YELLOW, 9), time_width=0.8),
                  ShowPassingFlash(Line(sq(0, 1), sq(1, 1)).set_stroke(YELLOW, 9), time_width=0.8), run_time=1.0)
        self.wait_until(self.phrase_at(0, "粘在了一起"))
        self.play(GrowArrow(aL[0]), GrowArrow(aT[0]), run_time=0.8)
        why = VGroup(MathTex(r"\{0,\,t\}", font_size=36, color=YELLOW), zh("与", 24),
                     MathTex(r"\{t,\,1\}", font_size=36, color=YELLOW), zh("是同一对点（曲线首尾相接）", 24, GREY_)
                     ).arrange(RIGHT, buff=0.12).next_to(upper, LEFT, buff=0.25).shift(DOWN * 1.6)
        why.scale(0.9).to_edge(LEFT, buff=0.4)
        self.play(FadeIn(why), run_time=0.8)
        self.sync(0.1)

        # ---------------- space4：剪开、翻转、粘回
        self.seg("space4")
        self.play(FadeOut(why), FadeOut(cg), FadeOut(dP), FadeOut(dQ), FadeOut(lP), FadeOut(lQ), run_time=0.4)
        Mm = sq(0.5, 0.5)
        Bv, Av, Cv = sq(0, 1), sq(0, 0), sq(1, 1)
        cut = DashedLine(Bv, Mm, color=RED, stroke_width=4)
        self.play(Create(cut), run_time=0.6)
        T1 = VGroup(Polygon(Av, Bv, Mm).set_stroke(GREY_, 2).set_fill("#18225C", 0.95),
                    Line(Av, Mm, color=GREEN, stroke_width=7), aL)
        cutA = arrows_on(Bv, Mm, RED, 2)
        T2 = VGroup(Polygon(Bv, Cv, Mm).set_stroke(GREY_, 2).set_fill("#22307A", 0.95),
                    Line(Cv, Mm, color=GREEN, stroke_width=7), aT)
        cutB = cutA.copy()
        self.remove(upper, hyp_g, hyp_lab)
        self.add(T1, T2, cutA)
        T2.add(cutB)
        self.play(FadeOut(cut), run_time=0.3)
        self.play(T2.animate.shift(RIGHT * 0.5 + UP * 0.3), run_time=0.6)
        self.play(Rotate(T2, PI, axis=np.array([1, 1, 0]), about_point=T2.get_center()), run_time=1.4)
        # 翻转后平移：原来的 B 点落到 A，于是 BC 边与 AB 边按箭头重合
        f_B = T2[0].get_vertices()[0]
        self.play(T2.animate.shift(Av - f_B), run_time=1.2)
        self.play(Flash(Av, color=YELLOW), Flash(Bv, color=YELLOW),
                  FadeOut(aL), FadeOut(aT), run_time=0.8)
        T1.remove(aL)
        T2.remove(aT)
        self.sync(0.0)

        # ---------------- space5：一条两端反向相粘的纸带
        self.seg("space5")
        shape = VGroup(T1, T2, cutA)
        # 旋转 -45°，并拉长成纸带
        self.play(Rotate(shape, -PI / 4, about_point=(Av + Bv) / 2), run_time=1.2)
        side = S * np.sqrt(2) / 2
        self.play(FadeOut(cutA), FadeOut(cutB), run_time=0.3)
        shape.remove(cutA)
        T2.remove(cutB)
        self.play(shape.animate.stretch(STRIP_L / side, 0).stretch(2 * MW / side, 1).move_to([0, 0, 0]), run_time=1.2)
        xl_, xr_ = -STRIP_L / 2, STRIP_L / 2
        endL = VGroup(Arrow([xl_ - 0.35, -0.55, 0], [xl_ - 0.35, 0.55, 0], buff=0, color=RED, stroke_width=7),
                      Arrow([xl_ - 0.6, -0.55, 0], [xl_ - 0.6, 0.55, 0], buff=0, color=RED, stroke_width=7))
        endR = VGroup(Arrow([xr_ + 0.35, 0.55, 0], [xr_ + 0.35, -0.55, 0], buff=0, color=RED, stroke_width=7),
                      Arrow([xr_ + 0.6, 0.55, 0], [xr_ + 0.6, -0.55, 0], buff=0, color=RED, stroke_width=7))
        cutA, cutB = endL, endR
        note = VGroup(zh("两端", 34), zh("反向", 34, RED, weight=BOLD), zh("相粘", 34)).arrange(RIGHT, buff=0.1)
        note.move_to([0, 2.5, 0])
        self.play(FadeIn(note, shift=DOWN * 0.2), GrowArrow(endL[0]), GrowArrow(endL[1]), GrowArrow(endR[0]),
                  GrowArrow(endR[1]), run_time=1.2)
        self.wait_until(self.phrase_at(0, "这正是"))
        mob = glow_text(zh("= 莫比乌斯带", 46, YELLOW, weight=BOLD).move_to([0, -2.3, 0]), YELLOW, strength=0.8)
        self.play(FadeIn(mob, scale=1.3), run_time=0.9)
        self.sync(0.6)
        self.play(FadeOut(note), FadeOut(mob), FadeOut(cutA), FadeOut(cutB), run_time=0.6)


# ------------------------------------------------------------------ 3D：莫比乌斯带 → 帐篷 → 射影平面
MR, MW = 1.8, 0.9   # 莫比乌斯带：中心圆半径、半宽
STRIP_L = TAU * MR


def mobius_morph(U, V, s):
    """纸带 (U∈[0,1] 沿长度, V∈[-1,1] 沿宽度) 在 s∈[0,1] 下逐渐弯成莫比乌斯带。"""
    U, V = np.asarray(U, float), np.asarray(V, float)
    if s < 1e-4:
        return np.stack([STRIP_L * (U - 0.5), MW * V, np.zeros_like(U)], axis=-1)
    a = TAU * s * (U - 0.5)
    rho = MR / s
    cx = rho * np.sin(a)
    cy = rho * np.cos(a) - rho + MR * s
    g = PI * s * (U - 0.5)
    Nx, Ny = np.sin(a), np.cos(a)
    off = MW * V
    return np.stack([cx + off * np.cos(g) * Nx, cy + off * np.cos(g) * Ny, off * np.sin(g)], axis=-1)


def mobius_std(alpha, v):
    """标准莫比乌斯带（与 mobius_morph(s=1) 一致），alpha 以 4π 为周期。"""
    r = MR + MW * v * np.cos(alpha / 2)
    return np.stack([r * np.sin(alpha), r * np.cos(alpha), MW * v * np.sin(alpha / 2)], axis=-1)


def mobius_uw(U, W, lift_z=1.4):
    P = mobius_std(4 * PI * np.asarray(U) - PI, 1 - 2 * np.asarray(W))
    return P + np.array([0, 0, lift_z])


def crosscap(U, V, k=2.3):
    x = np.sin(V) * np.cos(U)
    y = np.sin(V) * np.sin(U)
    z = np.cos(V)
    return np.stack([k * y * z, k * 2 * x * y * 0.8, k * (x * x - y * y) * 0.8 + 1.0], axis=-1)


def boy(R_, T_):
    """Bryant–Kusner 参数化的博伊曲面（射影平面在三维中的一种浸入）。"""
    w = np.asarray(R_) * np.exp(1j * np.asarray(T_))
    den = w ** 6 + np.sqrt(5) * w ** 3 - 1
    g1 = -1.5 * np.imag(w * (1 - w ** 4) / den)
    g2 = -1.5 * np.real(w * (1 + w ** 4) / den)
    g3 = np.imag((1 + w ** 6) / den) - 0.5
    g = g1 ** 2 + g2 ** 2 + g3 ** 2
    k = 1.9
    return np.stack([k * g1 / g, k * g2 / g, k * (g3 / g + 0.78) + 1.0], axis=-1)


def u_rgb(U, V):
    return lerp_rgb([MAGENTA, PURPLE, BLUE, CYAN, GREEN, YELLOW, ORANGE, MAGENTA], U)


class RectangleMobius(NThreeDScene):
    script_scene = "Rectangle"

    def body(self):
        self.add_fixed_in_frame_mobjects(make_corner(5, "内接矩形"))
        # 首帧与上一镜头末尾的纸带一致（俯视）
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=1.0)
        s = ValueTracker(0.0)
        strip = FastSurface(lambda U, V: mobius_morph(U, V, 0), [0, 1], [-1, 1], resolution=(64, 8),
                            uv_color=lambda U, V: lerp_rgb(["#1B2766", "#22307A"], U * 0 + 0.5),
                            opacity=0.88, amb=0.5, stroke=0.4)
        us = np.linspace(0, 1, 129)
        b_top = FastPolyline(mobius_morph(us, np.ones_like(us), 0), GREEN, 6)
        b_bot = FastPolyline(mobius_morph(us, -np.ones_like(us), 0), GREEN, 6)

        def refresh(_m=None):
            a = s.get_value()
            strip.update_mesh(lambda U, V: mobius_morph(U, V, a))
            b_top.update_points(mobius_morph(us, np.ones_like(us), a))
            b_bot.update_points(mobius_morph(us, -np.ones_like(us), a))

        driver = Mobject()
        driver.add_updater(refresh)
        self.add(strip, b_top, b_bot, driver)

        # ---------------- mobius
        self.seg("mobius")
        self.move_camera(phi=64 * DEGREES, theta=-70 * DEGREES, zoom=1.15,
                         added_anims=[s.animate.set_value(1.0)], run_time=6.0)
        driver.clear_updaters()
        self.begin_ambient_camera_rotation(rate=0.18)
        lab = VGroup(zh("所有无序点对", 30), MathTex("=", font_size=40), zh("莫比乌斯带", 30, YELLOW, weight=BOLD)).arrange(RIGHT, buff=0.15)
        lab.to_edge(UP, buff=0.5).shift(RIGHT * 1.5)
        self.add_fixed_in_frame_mobjects(lab)
        lab.set_opacity(0)
        self.play(lab.animate.set_opacity(1), run_time=0.8)
        self.wait_until(self.sent_at(1))
        bl = VGroup(zh("边界", 28, GREEN, weight=BOLD), zh("= 两点重合的情形", 28, GREEN)).arrange(RIGHT, buff=0.1)
        bl.to_corner(DL, buff=0.7).shift(UP * 0.4)
        self.add_fixed_in_frame_mobjects(bl)
        bl.set_opacity(0)
        self.play(bl.animate.set_opacity(1), b_top.animate.set_stroke(width=9), b_bot.animate.set_stroke(width=9),
                  run_time=1.0)
        self.play(b_top.animate.set_stroke(width=6), b_bot.animate.set_stroke(width=6), run_time=0.6)
        self.sync(0.1)

        # ---------------- mobius2：只有一条边界
        self.seg("mobius2")
        ph = ValueTracker(0.0)
        runner = always_redraw(lambda: Dot3D(mobius_std(ph.get_value() - PI, 1.0) * 1.0, radius=0.12,
                                             color=WHITE, resolution=(8, 8)))
        trail = TracedPath(lambda: mobius_std(ph.get_value() - PI, 1.0), stroke_color=WHITE, stroke_width=5,
                           dissipating_time=1.2)
        self.add(trail, runner)
        one = zh("只有一条边界", 30, WHITE_, weight=BOLD).next_to(bl, UP, buff=0.3).align_to(bl, LEFT)
        self.add_fixed_in_frame_mobjects(one)
        one.set_opacity(0)
        self.play(ph.animate.set_value(4 * PI), one.animate.set_opacity(1), run_time=self.remaining(-0.5),
                  rate_func=linear)
        runner.clear_updaters()
        self.play(FadeOut(runner), FadeOut(trail), run_time=0.4)
        self.sync(0.1)

        # ---------------- embed：莫比乌斯带 → 帐篷（边界落在平面曲线上）
        self.seg("embed")
        self.play(FadeOut(VGroup(bl, one, lab)), run_time=0.5)
        # 换成 (u,w) 参数的同一条莫比乌斯带（视觉无变化）
        mob = FastSurface(lambda U, W: mobius_uw(U, W, 0.0), [0, 1], [0, 0.5], resolution=(96, 8),
                          uv_color=lambda U, W: lerp_rgb(["#1B2766", "#22307A"], U * 0 + 0.5),
                          opacity=0.88, amb=0.5, stroke=0.4)
        ub = np.linspace(0, 1, 257)
        bnd = FastPolyline(mobius_uw(ub, np.zeros_like(ub), 0.0), GREEN, 6)
        self.remove(strip, b_top, b_bot)
        self.add(mob, bnd)
        floor = Rectangle(width=9, height=7).set_stroke(DIM, 1).set_fill("#0B1030", 0.55)
        floor.always_back = True
        base = curve3d_closed(CURVE_C, 5)
        q = zh("能否放到平面上方，边界落在曲线上，且不自交？", 30, WHITE_).to_edge(UP, buff=0.5).shift(RIGHT * 0.6)
        self.add_fixed_in_frame_mobjects(q)
        q.set_opacity(0)
        lift_t = ValueTracker(0.0)
        mt = ValueTracker(0.0)

        def morph_fn(U, W):
            a = smooth(mt.get_value())
            z = 1.4 * lift_t.get_value()
            return (1 - a) * mobius_uw(U, W, z) + a * tent(U, W)

        def refresh2(_m=None):
            mob.update_mesh(morph_fn)
            bnd.update_points(morph_fn(ub, np.zeros_like(ub)))

        d2 = Mobject()
        d2.add_updater(refresh2)
        self.add(d2)
        self.play(FadeIn(floor), Create(base), lift_t.animate.set_value(1.0), q.animate.set_opacity(1), run_time=2.0)
        self.move_camera(phi=62 * DEGREES, zoom=0.95, frame_center=[0, 0, 1.0], run_time=1.2)
        self.play(mt.animate.set_value(1.0), run_time=self.remaining(-1.2), rate_func=linear)
        d2.clear_updaters()
        mob.color_fn = height_rgb
        mob.uv_rgb = None
        mob.opacity = 0.62
        mob.update_mesh(tent)
        self.play(ShowPassingFlash(curve3d_closed(WHITE, 10), time_width=0.4), run_time=1.0)
        self.sync(0.1)

        # ---------------- rp2：封上圆盘 → 射影平面；射影平面放不进三维
        self.seg("rp2")
        self.play(FadeOut(q), run_time=0.4)
        no = zh("不能！", 48, RED, weight=BOLD).to_edge(UP, buff=0.5).shift(RIGHT * 1.0)
        self.add_fixed_in_frame_mobjects(no)
        no.set_opacity(0)
        self.play(no.animate.set_opacity(1), run_time=0.5)
        self.wait_until(self.phrase_at(0, "用一块圆盘"))
        disk = FastSurface(lambda R_, S_: np.concatenate([(gamma(S_) * CS) * R_[..., None],
                                                         np.zeros_like(R_)[..., None] + 0.005], axis=-1),
                           [0, 1], [0, 1], resolution=(6, 72), color=CYAN, opacity=0.45, amb=0.8, stroke=0.3)
        self.play(FadeIn(disk), FadeOut(no), run_time=1.5)
        eq = VGroup(zh("莫比乌斯带", 30, YELLOW), MathTex("+", font_size=40), zh("圆盘", 30, CYAN),
                    MathTex("=", font_size=40), zh("射影平面", 30, MAGENTA, weight=BOLD),
                    MathTex(r"\mathbb{R}P^2", font_size=40, color=MAGENTA)).arrange(RIGHT, buff=0.15)
        eq.to_edge(UP, buff=0.5).shift(RIGHT * 0.8)
        self.add_fixed_in_frame_mobjects(eq)
        eq.set_opacity(0)
        self.wait_until(self.phrase_at(0, "封闭曲面"))
        self.play(eq.animate.set_opacity(1), run_time=0.8)
        self.wait_until(self.sent_at(1))
        # 切换到交叉帽（射影平面在三维中的一种自相交模型）
        self.play(FadeOut(VGroup(mob, bnd, disk, base, floor)), run_time=1.0)
        cc = FastSurface(boy, [0, 0.999], [0, TAU], resolution=(24, 72),
                         uv_color=lambda U, V: lerp_rgb([YELLOW, ORANGE, MAGENTA, PURPLE, BLUE, CYAN], U),
                         opacity=0.82, amb=0.4, stroke=0.4)
        self.move_camera(phi=46 * DEGREES, added_anims=[FadeIn(cc)], run_time=1.5)
        cc_lab = VGroup(zh("博伊曲面：射影平面放进三维的样子", 26, GREY_),
                        zh("—— 必然自相交", 26, RED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        cc_lab.to_corner(DL, buff=0.7).shift(UP * 0.3)
        self.add_fixed_in_frame_mobjects(cc_lab)
        cc_lab.set_opacity(0)
        self.play(cc_lab.animate.set_opacity(1), run_time=0.8)
        self.wait_until(self.phrase_at(1, "三维空间中的封闭曲面"))
        r1 = VGroup(zh("三维中的封闭曲面", 28), MathTex(r"\Rightarrow", font_size=36), zh("分得出里外", 28, GREEN)).arrange(RIGHT, buff=0.15)
        r2 = VGroup(zh("射影平面含莫比乌斯带", 28), MathTex(r"\Rightarrow", font_size=36), zh("分不出正反", 28, RED)).arrange(RIGHT, buff=0.15)
        rr = VGroup(r1, r2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).to_corner(UR, buff=0.5).shift(DOWN * 1.0)
        self.add_fixed_in_frame_mobjects(rr)
        rr.set_opacity(0)
        self.play(r1.animate.set_opacity(1), run_time=0.8)
        self.wait_until(self.phrase_at(1, "但射影平面"))
        self.play(r2.animate.set_opacity(1), run_time=0.8)
        self.sync(0.2)

        # ---------------- conclude：回到帐篷，找到矩形
        self.seg("conclude")
        self.move_camera(phi=62 * DEGREES, added_anims=[FadeOut(cc), FadeOut(VGroup(eq, cc_lab, rr))], run_time=0.8)
        self.play(FadeIn(floor), FadeIn(base), FadeIn(mob), run_time=1.0)
        s1, t1, s2, t2 = X_REP
        A, C, B, Dd = g3(s1), g3(t1), g3(s2), g3(t2)
        Mx = (A + C) / 2
        Xp = Mx + np.array([0, 0, HS * np.linalg.norm(A - C)])
        ch1 = Line(A, C, color=CYAN, stroke_width=6)
        ch2 = Line(B, Dd, color=MAGENTA, stroke_width=6)
        l1 = Line(Mx, Xp, color=YELLOW, stroke_width=4)
        bigX = Dot3D(Xp, radius=0.17, color=YELLOW, resolution=(8, 8))
        self.wait_until(self.phrase_at(0, "交点处"))
        self.play(FadeIn(bigX, scale=3), run_time=0.7)
        self.play(Create(l1), Create(ch1), Create(ch2), run_time=1.2)
        rect = Polygon(A, B, C, Dd).set_stroke(YELLOW, 6)
        rect_f = Polygon(A, B, C, Dd).set_stroke(width=0).set_fill(YELLOW, 0.25)
        self.wait_until(self.phrase_at(0, "矩形的四个顶点"))
        self.play(Create(rect), FadeIn(rect_f), run_time=1.0)
        qed = VGroup(zh("证毕", 44, YELLOW, weight=BOLD), MathTex(r"\blacksquare", font_size=44, color=YELLOW)).arrange(RIGHT, buff=0.25)
        qed.to_edge(DOWN, buff=0.85)
        self.add_fixed_in_frame_mobjects(qed)
        qed.set_opacity(0)
        self.wait_until(self.phrase_at(0, "证毕"))
        self.play(qed.animate.set_opacity(1), run_time=0.6)
        self.sync(0.6)
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.0)


class RectangleEnd(NScene):
    script_scene = "Rectangle"

    def body(self):
        self.add(make_corner(5, "内接矩形"))
        SC, SH = 0.78, np.array([-2.9, 0.0, 0])
        curve = curve2d(SC, SH).set_stroke(CURVE_C, 5)
        cg = neon(curve)
        idx = ValueTracker(0.0)

        def x_at(t):
            t = float(np.clip(t, 0, len(FAM) - 1))
            i = min(int(t), len(FAM) - 2)
            a = t - i
            return FAM[i] * (1 - a) + FAM[i + 1] * a

        def rect_mob():
            R = rect_pts(x_at(idx.get_value()), SC, SH)
            poly = Polygon(*R).set_stroke(YELLOW, 5).set_fill(YELLOW, 0.12)
            dg = VGroup(Line(R[0], R[2], color=CYAN, stroke_width=2.5), Line(R[1], R[3], color=MAGENTA, stroke_width=2.5))
            dots = VGroup(*[Dot(p, radius=0.07, color=WHITE) for p in R])
            return VGroup(dg, poly, dots)

        # ---------------- family
        self.seg("family")
        idx.set_value(I_REP)
        rm = always_redraw(rect_mob)
        self.play(FadeIn(cg), FadeIn(rm), run_time=0.8)
        many = zh("内接矩形不止一个", 34, WHITE_, weight=BOLD).move_to([3.6, 1.8, 0])
        self.play(FadeIn(many, shift=DOWN * 0.2), run_time=0.6)
        self.play(idx.animate.set_value(0), run_time=2.4, rate_func=smooth)
        self.play(idx.animate.set_value(len(FAM) - 1), run_time=self.remaining(-0.3), rate_func=smooth)
        self.sync(0.1)

        # ---------------- square：内接正方形问题
        self.seg("square")
        self.play(idx.animate.set_value(I_SQ), run_time=2.2, rate_func=smooth)
        rm.clear_updaters()
        R = rect_pts(FAM[I_SQ], SC, SH)
        sqm = Polygon(*R).set_stroke(GREEN, 6).set_fill(GREEN, 0.15)
        self.play(FadeOut(rm), FadeIn(neon(sqm)), FadeOut(many), run_time=0.8)
        toep = VGroup(zh("内接正方形问题", 40, GREEN, weight=BOLD), en("Toeplitz, 1911", 26)).arrange(DOWN, buff=0.15)
        toep.move_to([3.6, 2.0, 0])
        self.play(FadeIn(toep, shift=DOWN * 0.2), run_time=0.8)
        self.wait_until(self.sent_at(1))
        ok = VGroup(zh("光滑曲线", 32), MathTex(r"\checkmark", font_size=48, color=GREEN), zh("已证明", 32, GREEN)).arrange(RIGHT, buff=0.2)
        unk = VGroup(zh("一般连续曲线", 32), MathTex("?", font_size=56, color=YELLOW), zh("至今未解决", 32, YELLOW)).arrange(RIGHT, buff=0.2)
        rows = VGroup(ok, unk).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([3.6, 0.1, 0])
        self.play(FadeIn(ok, shift=RIGHT * 0.3), run_time=0.8)
        self.wait_until(self.phrase_at(1, "但对于一般"))
        self.play(FadeIn(unk, shift=RIGHT * 0.3), run_time=0.8)
        self.play(Indicate(unk[1], color=YELLOW, scale_factor=1.6), run_time=1.0)
        self.sync(0.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.0)
