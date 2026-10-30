# -*- coding: utf-8 -*-
from scipy.optimize import brentq

from common import *


def T_final(th):
    return 18 + 7 * np.cos(th - 0.6) + 4 * np.sin(2 * th + 1) + 3 * np.cos(3 * th - 0.3) \
        + 1.5 * np.sin(5 * th + 0.4)


def T_alt(th):
    return 17 + 9 * np.sin(th + 1.9) + 5 * np.cos(2 * th) - 3 * np.sin(4 * th + 0.5) \
        + 2 * np.cos(6 * th)


T_MIN, T_MAX = 2.0, 36.0
TH0 = 0.6


def g_final(th):
    return T_final(th) - T_final(th + PI)


def _first_zero():
    xs = np.linspace(TH0, TH0 + PI, 2000)
    ys = g_final(xs)
    i = np.where(np.sign(ys[:-1]) != np.sign(ys[1:]))[0][0]
    return brentq(g_final, xs[i], xs[i + 1])


TH_STAR = _first_zero()

COLD = ManimColor("#3B6CFF")
MID = ManimColor("#B66BFF")
HOT = ManimColor("#FF5A3C")


def temp_color(t):
    a = float(np.clip((t - T_MIN) / (T_MAX - T_MIN), 0, 1))
    if a < 0.5:
        return interpolate_color(COLD, MID, a * 2)
    return interpolate_color(MID, HOT, (a - 0.5) * 2)


class Antipodal(NScene):
    script_scene = "Antipodal"

    def body(self):
        self.chapter(2, "对跖点的温度", "Antipodal Points on the Earth")
        self.show_corner()

        # ---------------- setup：线框地球
        self.seg("setup")
        R = 2.3
        C = np.array([-3.3, 0.1, 0])
        tilt = 0.32  # 观察角：赤道呈椭圆
        phase = ValueTracker(0)

        def globe_lines():
            g = VGroup()
            for lat in np.linspace(-60, 60, 5):
                la = np.deg2rad(lat)
                e = Ellipse(width=2 * R * np.cos(la), height=2 * R * np.cos(la) * tilt)
                e.move_to(C + UP * R * np.sin(la) * np.sqrt(1 - tilt ** 2))
                g.add(e.set_stroke(BLUE, 1.5, opacity=0.45 if lat else 0))
            ph = phase.get_value()
            for k in range(8):
                lon = ph + k * PI / 8
                w = abs(np.cos(lon)) * R
                e = Ellipse(width=max(2 * w, 0.01), height=2 * R).move_to(C)
                g.add(e.set_stroke(BLUE, 1.5, opacity=0.45))
            return g

        disk = Circle(R).move_to(C).set_stroke(CYAN, 3)
        disk.set_fill(color=["#081A44", "#0E2A6A"], opacity=1).set_sheen_direction(UR)
        disk_g = VGroup(glow_layers(disk, layers=4, spread=6, strength=0.8), disk)
        lines = always_redraw(globe_lines)
        equator = Ellipse(width=2 * R, height=2 * R * tilt).move_to(C).set_stroke(YELLOW, 4)
        eq_g = neon(equator.copy())
        self.play(DrawBorderThenFill(disk_g), run_time=1.2)
        self.add(lines)
        self.play(phase.animate.set_value(PI / 8), run_time=self.until(self.sent_at(1)), rate_func=linear)

        stmt_panel = panel(6.2, 2.6, color=MAGENTA).move_to([3.4, 0.5, 0])
        s1 = zh("证明：任意时刻，", 32)
        s2 = zh("赤道上存在两个正好相对的点，", 32)
        s3 = zh("它们的温度完全相同。", 32, YELLOW, weight=BOLD)
        st = VGroup(s1, s2, s3).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(stmt_panel)
        self.play(Create(eq_g), FadeIn(stmt_panel), phase.animate.set_value(PI / 8 + 0.3),
                  LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in st], lag_ratio=0.3), run_time=2.0)
        self.play(phase.animate.set_value(PI / 8 + 1.2), run_time=self.until(self.sent_at(2)),
                  rate_func=linear)

        a0 = 2.4
        pP = C + np.array([R * np.cos(a0), R * tilt * np.sin(a0), 0])
        pQ = C - np.array([R * np.cos(a0), R * tilt * np.sin(a0), 0])
        dia = DashedLine(pP, pQ, color=WHITE_, stroke_width=3)
        dP, dQ = glow_dot(pP, ORANGE, 0.1, 4), glow_dot(pQ, CYAN, 0.1, 4)
        lP = MathTex("P", color=ORANGE, font_size=40).next_to(pP, DOWN + LEFT * 0.4, buff=0.15)
        lQ = MathTex("P'", color=CYAN, font_size=40).next_to(pQ, UP + RIGHT * 0.4, buff=0.15)
        term = zh("对跖点", 34, YELLOW, weight=BOLD).next_to(stmt_panel, DOWN, buff=0.4)
        term_en = en("antipodal points", 24, GREY_).next_to(term, RIGHT, buff=0.25)
        self.play(Create(dia), FadeIn(dP, scale=2), FadeIn(dQ, scale=2), FadeIn(lP), FadeIn(lQ),
                  phase.animate.set_value(PI / 8 + 1.6), run_time=1.2)
        self.play(FadeIn(term, shift=UP * 0.2), FadeIn(term_en), phase.animate.set_value(PI / 8 + 2.0),
                  run_time=1.0)
        self.play(phase.animate.set_value(PI / 8 + 2.6), run_time=self.remaining(0.2), rate_func=linear)

        # ---------------- unknown：俯视赤道，温度环
        self.seg("unknown")
        lines.clear_updaters()
        Rr = 1.8
        C2 = np.array([-4.2, 0.0, 0])
        ring_circle = Circle(Rr).move_to(C2).set_stroke(YELLOW, 4)
        ring_neon = neon(ring_circle)
        self.play(FadeOut(VGroup(lines, disk_g, dia, dP, dQ, lP, lQ, stmt_panel, st, term, term_en)),
                  ReplacementTransform(eq_g, ring_neon), run_time=1.4)
        mix = ValueTracker(0.0)
        N = 144
        ths = np.linspace(0, TAU, N, endpoint=False)

        def T_now(th):
            a = mix.get_value()
            return (1 - a) * T_alt(th) + a * T_final(th)

        def ring_mob():
            g = VGroup()
            for th in ths:
                t = T_now(th)
                col = temp_color(t)
                arc = Arc(radius=Rr, start_angle=th, angle=TAU / N * 1.02, arc_center=C2,
                          stroke_width=12, color=col)
                r1 = Rr + 0.18
                r2 = r1 + 0.03 + 0.024 * (t - T_MIN)
                bar = Line(C2 + r1 * np.array([np.cos(th), np.sin(th), 0]),
                           C2 + r2 * np.array([np.cos(th), np.sin(th), 0]),
                           stroke_width=3.2, color=col)
                g.add(arc, bar)
            return g

        ring = always_redraw(ring_mob)
        legend_bar = VGroup(*[Rectangle(width=0.06, height=0.28, stroke_width=0,
                                        fill_color=temp_color(T_MIN + (T_MAX - T_MIN) * k / 39),
                                        fill_opacity=1) for k in range(40)]).arrange(RIGHT, buff=0)
        legend = VGroup(zh("冷", 22, "#7FA0FF"), legend_bar, zh("热", 22, "#FF8A6A")).arrange(RIGHT, buff=0.15)
        legend.next_to(C2 + DOWN * (Rr + 0.85), DOWN, buff=0).shift(DOWN * 0.05)
        self.play(FadeIn(ring), FadeIn(legend), run_time=1.0)
        self.play(mix.animate.set_value(1.0), run_time=self.until(self.sent_at(1)), rate_func=there_and_back_with_pause)
        self.play(mix.animate.set_value(1.0), run_time=self.remaining(-0.3), rate_func=smooth)
        ring.clear_updaters()
        cont = zh("唯一的假设：温度连续变化", 30, GREY_).move_to([2.6, 2.6, 0])
        self.play(FadeIn(cont, shift=DOWN * 0.2), run_time=0.6)
        self.sync(0.2)

        # ---------------- diff：差值函数
        self.seg("diff")
        theta = ValueTracker(TH0)

        def on_ring(th, r=Rr):
            return C2 + r * np.array([np.cos(th), np.sin(th), 0])

        dia2 = always_redraw(lambda: Line(on_ring(theta.get_value()), on_ring(theta.get_value() + PI),
                                          color=WHITE_, stroke_width=3))
        dotP = always_redraw(lambda: glow_dot(on_ring(theta.get_value()), ORANGE, 0.1, 4))
        dotQ = always_redraw(lambda: glow_dot(on_ring(theta.get_value() + PI), CYAN, 0.1, 4))
        labP = always_redraw(lambda: MathTex("P", color=ORANGE, font_size=38).move_to(
            on_ring(theta.get_value(), Rr - 0.42)))
        labQ = always_redraw(lambda: MathTex("P'", color=CYAN, font_size=38).move_to(
            on_ring(theta.get_value() + PI, Rr - 0.42)))

        g_def = MathTex("g", "=", "T(P)", "-", "T(P')", font_size=50)
        g_def[0].set_color(MAGENTA)
        g_def[2].set_color(ORANGE)
        g_def[4].set_color(CYAN)
        g_def.move_to([2.6, 2.6, 0])

        # 温度柱
        base_y = -1.6
        bx1, bx2 = -0.95, -0.25
        hscale = 3.2 / (T_MAX - T_MIN)

        grow = ValueTracker(0.0)

        def bar(x, fn, col):
            def f():
                t = fn()
                h = max(0.02, (t - T_MIN) * hscale * grow.get_value())
                r = Rectangle(width=0.5, height=h).set_stroke(col, 2).set_fill(temp_color(t), 0.85)
                return r.move_to([x, base_y + h / 2, 0])
            return always_redraw(f)

        barP = bar(bx1, lambda: T_final(theta.get_value()), ORANGE)
        barQ = bar(bx2, lambda: T_final(theta.get_value() + PI), CYAN)
        bl = VGroup(MathTex("T(P)", font_size=28, color=ORANGE).move_to([bx1, base_y - 0.3, 0]),
                    MathTex("T(P')", font_size=28, color=CYAN).move_to([bx2, base_y - 0.3, 0]))

        # g 的图像
        gmax = 26
        ax = Axes(x_range=[0, PI, PI / 2], y_range=[-gmax, gmax, 10], x_length=5.2, y_length=3.8,
                  axis_config={"color": GREY_, "stroke_width": 2, "include_tip": False}).move_to([3.9, -0.15, 0])
        ax_lab = VGroup(zh("旋转角度", 22, GREY_).next_to(ax.x_axis.get_end(), DOWN, buff=0.2).shift(LEFT * 0.4),
                        MathTex("0", font_size=28, color=GREY_).next_to(ax.c2p(0, 0), LEFT, buff=0.12),
                        MathTex(r"\pi", font_size=30, color=GREY_).next_to(ax.c2p(PI, 0), DOWN, buff=0.15),
                        MathTex("g", font_size=34, color=MAGENTA).next_to(ax.y_axis.get_end(), LEFT, buff=0.15))
        g_val = DecimalNumber(g_final(TH0), num_decimal_places=1, include_sign=True, font_size=40,
                              color=GREEN)
        g_val.next_to(g_def, RIGHT, buff=0.3)

        def g_val_upd(m):
            v = g_final(theta.get_value())
            m.set_value(v).set_color(GREEN if v > 0 else RED)
            m.next_to(g_def, RIGHT, buff=0.3)

        self.play(FadeOut(cont), Write(g_def), run_time=1.2)
        self.wait_until(self.sent_at(1))
        self.play(Create(dia2), FadeIn(dotP), FadeIn(labP), run_time=0.8)
        self.wait_until(self.phrase_at(1, "对跖点为"))
        self.play(FadeIn(dotQ), FadeIn(labQ), run_time=0.6)
        self.wait_until(self.phrase_at(1, "定义"))
        self.add(barP, barQ)
        self.play(grow.animate.set_value(1), FadeIn(bl), run_time=0.8)
        self.play(Indicate(g_def, color=YELLOW), FadeIn(g_val), run_time=1.0)
        g_val.add_updater(g_val_upd)
        self.play(Create(ax), FadeIn(ax_lab), run_time=1.0)
        self.sync(0.1)

        # ---------------- rotate：旋转半圈
        self.seg("rotate")
        g_curve = always_redraw(lambda: ax.plot(lambda x: g_final(TH0 + x),
                                                x_range=[0, max(0.001, theta.get_value() - TH0), 0.01],
                                                color=MAGENTA, stroke_width=5))
        gdot = always_redraw(lambda: glow_dot(ax.c2p(theta.get_value() - TH0, g_final(theta.get_value())),
                                              MAGENTA, 0.08, 3))
        start_mark = glow_dot(ax.c2p(0, g_final(TH0)), GREEN, 0.09, 3)
        self.add(g_curve, gdot)
        self.play(FadeIn(start_mark), run_time=0.3)
        self.play(theta.animate.set_value(TH0 + PI), run_time=self.until(self.sent_at(1) + 0.6),
                  rate_func=linear)
        g_curve.clear_updaters()
        gdot.clear_updaters()
        end_mark = glow_dot(ax.c2p(PI, g_final(TH0 + PI)), RED, 0.09, 3)
        swap = zh("P 与 P′ 交换了位置", 28, YELLOW).move_to([-4.2, 2.75, 0])
        neg_eq = MathTex(r"g(\theta+\pi) = -\,g(\theta)", font_size=40, color=YELLOW).move_to([3.6, 2.0, 0])
        self.play(FadeIn(swap, shift=DOWN * 0.2), FadeIn(end_mark, scale=2), run_time=0.8)
        self.wait_until(self.phrase_at(1, "于是"))
        sym = DashedLine(ax.c2p(0, g_final(TH0)), ax.c2p(PI, g_final(TH0 + PI)), color=YELLOW,
                         stroke_width=2, dash_length=0.08)
        self.play(Write(neg_eq), Create(sym), run_time=1.2)
        self.sync(0.1)

        # ---------------- sign：从正到负，必过零
        self.seg("sign")
        plus = MathTex("+", font_size=54, color=GREEN).next_to(start_mark, LEFT, buff=0.15)
        minus = MathTex("-", font_size=54, color=RED).next_to(end_mark, RIGHT, buff=0.15)
        self.play(FadeIn(plus, scale=2), Flash(start_mark[1].get_center(), color=GREEN), run_time=0.8)
        self.wait_until(self.phrase_at(0, "转半圈后"))
        self.play(FadeIn(minus, scale=2), Flash(end_mark[1].get_center(), color=RED), run_time=0.8)
        self.wait_until(self.phrase_at(1, "中间一定会经过零"))
        Z = ax.c2p(TH_STAR - TH0, 0)
        zdot = glow_dot(Z, YELLOW, 0.1, 5)
        self.play(burst(Z, YELLOW, r1=0.8), FadeIn(zdot, scale=3), FadeOut(sym), run_time=0.9)
        self.play(theta.animate.set_value(TH_STAR), run_time=1.6)
        eqT = MathTex("T(P)", "=", "T(P')", font_size=50)
        eqT[0].set_color(ORANGE)
        eqT[2].set_color(CYAN)
        eqT.move_to([-4.2, 2.65, 0])
        eqg = glow_text(eqT, color=YELLOW, strength=0.8)
        self.wait_until(self.phrase_at(1, "在那里"))
        self.play(FadeIn(eqg, scale=1.3), FadeOut(swap),
                  Flash(on_ring(TH_STAR), color=ORANGE), Flash(on_ring(TH_STAR + PI), color=CYAN),
                  run_time=1.0)
        self.sync(0.6)
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not self.corner])), run_time=0.8)


# ------------------------------------------------------------------ 3D：Borsuk–Ulam
def T3(p):
    x, y, z = p
    return 0.9 * x + 0.5 * z + 0.6 * x * y * y + 0.4 * (x * x - y * y) + 0.3 * y * z


def P3(p):
    x, y, z = p
    return 0.8 * y - 0.45 * z + 0.5 * x * x * z + 0.35 * x * z + 0.2 * (z * z)


def odd(fn):
    return lambda p: fn(p) - fn(-p)


def zero_curve(fn, n_axis, samples=240):
    """在单位球面上追踪奇函数 fn 的零点集（接近以 n_axis 为法向的大圆）。"""
    n = np.array(n_axis, float)
    n /= np.linalg.norm(n)
    a = np.cross(n, [0.13, 0.31, 0.94])
    a /= np.linalg.norm(a)
    b = np.cross(n, a)
    pts = []
    for al in np.linspace(0, TAU, samples, endpoint=False):
        c = np.cos(al) * a + np.sin(al) * b

        def h(beta):
            return fn(np.cos(beta) * c + np.sin(beta) * n)
        betas = np.linspace(-1.2, 1.2, 97)
        vals = [h(bb) for bb in betas]
        best = None
        for i in range(len(betas) - 1):
            if np.sign(vals[i]) != np.sign(vals[i + 1]):
                r = brentq(h, betas[i], betas[i + 1])
                if best is None or abs(r) < abs(best):
                    best = r
        if best is not None:
            pts.append(np.cos(best) * c + np.sin(best) * n)
    return np.array(pts)


def solve_antipodal():
    from scipy.optimize import fsolve
    fT, fP = odd(T3), odd(P3)

    def F(v):
        th, ph = v
        p = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
        return [fT(p), fP(p)]
    best = None
    for th0 in np.linspace(0.2, 2.9, 7):
        for ph0 in np.linspace(0, TAU, 9):
            sol, info, ier, _ = fsolve(F, [th0, ph0], full_output=True)
            if ier == 1:
                th, ph = sol
                p = np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
                if p[2] < 0:
                    p = -p
                if best is None or p[0] + p[1] > best[0] + best[1]:
                    best = p
    return best


class AntipodalBU(NThreeDScene):
    script_scene = "Antipodal"

    def body(self):
        corner = make_corner(2, "对跖点的温度")
        self.add_fixed_in_frame_mobjects(corner)
        self.set_camera_orientation(phi=68 * DEGREES, theta=-50 * DEGREES, zoom=1.0,
                                    frame_center=[0, 0, -0.85])
        R = 2.15

        tv = []
        sph = Surface(lambda u, v: R * np.array([np.sin(v) * np.cos(u), np.sin(v) * np.sin(u), np.cos(v)]),
                      u_range=[0, TAU], v_range=[0, PI], resolution=(40, 20))
        tv = [T3(f.get_center() / R) for f in sph]
        lo, hi = min(tv), max(tv)
        bake(sph, color_fn=lambda c: temp_color(T_MIN + (T3(c / R) - lo) / (hi - lo) * (T_MAX - T_MIN)),
             opacity=0.82)

        cT = curve3d(zero_curve(odd(T3), [0.9, 0, 0.5], 160) * R * 1.012, YELLOW, 5, closed=True)
        cP = curve3d(zero_curve(odd(P3), [0, 0.8, -0.45], 160) * R * 1.012, CYAN, 5, closed=True)
        X = solve_antipodal()

        self.seg("bu1")
        self.begin_ambient_camera_rotation(rate=0.12)
        self.play(FadeIn(sph), run_time=1.5)
        lab = VGroup(
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=YELLOW, stroke_width=6), zh("温度相同的对跖点", 26, YELLOW)).arrange(RIGHT, buff=0.2),
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=CYAN, stroke_width=6), zh("气压相同的对跖点", 26, CYAN)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).to_corner(UR, buff=0.5)
        self.add_fixed_in_frame_mobjects(lab[0])
        self.play(Create(cT), FadeIn(lab[0]), run_time=2.0)
        self.add_fixed_in_frame_mobjects(lab[1])
        self.play(Create(cP), FadeIn(lab[1]), run_time=2.0)
        self.wait_until(self.phrase_at(0, "不仅温度相同"))
        A, B = X * R * 1.02, -X * R * 1.02
        axis_line = DashedLine(A * 1.25, B * 1.25, color=WHITE_, stroke_width=3)
        dA = Dot3D(A, radius=0.11, color=MAGENTA)
        dB = Dot3D(B, radius=0.11, color=MAGENTA)
        hA = Sphere(A, radius=0.22, resolution=(8, 8)).set_color(MAGENTA).set_opacity(0.25)
        hB = Sphere(B, radius=0.22, resolution=(8, 8)).set_color(MAGENTA).set_opacity(0.25)
        self.play(FadeIn(dA, scale=3), FadeIn(dB, scale=3), FadeIn(hA), FadeIn(hB), Create(axis_line),
                  run_time=1.2)
        self.sync(0.2)

        self.seg("bu2")
        t1 = VGroup(en("Borsuk–Ulam", 34, WHITE_, weight=BOLD), zh("定理", 34, WHITE_, weight=BOLD)).arrange(RIGHT, buff=0.15)
        t2 = VGroup(MathTex(r"f:\ S^2 \to \mathbb{R}^2", font_size=40), zh("连续", 28, GREY_),
                    MathTex(r"\Rightarrow\ \exists\, x,\ f(x)=f(-x)", font_size=40, color=YELLOW)).arrange(RIGHT, buff=0.2)
        thm = VGroup(t1, t2).arrange(DOWN, buff=0.3)
        box = panel(thm.width + 0.8, thm.height + 0.55, color=MAGENTA).move_to(thm)
        thm_g = VGroup(box, thm).scale(0.85).to_edge(DOWN, buff=0.75)
        self.add_fixed_in_frame_mobjects(thm_g)
        self.play(FadeIn(thm_g, shift=UP * 0.3), run_time=1.0)
        self.wait_until(self.sent_at(1))
        fx = VGroup(MathTex(r"f(x) = (", font_size=38), zh("温度", 30, YELLOW), MathTex(",", font_size=38),
                    zh("气压", 30, CYAN), MathTex(")", font_size=38)).arrange(RIGHT, buff=0.1)
        fx.next_to(lab, DOWN, buff=0.4).align_to(lab, LEFT)
        self.add_fixed_in_frame_mobjects(fx)
        self.play(FadeIn(fx, shift=LEFT * 0.3), run_time=0.8)
        self.play(Indicate(dA, color=YELLOW, scale_factor=1.6), Indicate(dB, color=YELLOW, scale_factor=1.6),
                  run_time=1.2)
        self.sync(0.6)
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.9)
