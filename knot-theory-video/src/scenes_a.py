# -*- coding: utf-8 -*-
from common import *


# =====================================================================  00 INTRO
def tangle_pts(n=700, seed=7):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, TAU_, n, endpoint=False)
    P = np.zeros((n, 3))
    for k in range(1, 7):
        a = rng.normal(0, 1.0 / k ** 0.9, (3, 2))
        P[:, 0] += a[0, 0] * np.cos(k * t) + a[0, 1] * np.sin(k * t)
        P[:, 1] += a[1, 0] * np.cos(k * t) + a[1, 1] * np.sin(k * t)
        P[:, 2] += a[2, 0] * np.cos(k * t) + a[2, 1] * np.sin(k * t)
    P[:, :2] /= np.abs(P[:, :2]).max(0)
    return P * [3.2, 2.2, 1.0]


class Ch00(Chapter):
    CH = 0

    def construct(self):
        # s0: tangled cord
        self.at(0)
        tang = tangle_pts()
        tr = trefoil_pts(700) * [0.77, 0.77, 1] + [0, 0.9 / 0.85, 0]
        tk = ValueTracker(0)
        cols = [INK]
        cord = knot_morph(self, [Comp(tang)], [Comp(tr)], tk, scale=0.85, shift=UP * 0.2, width=6,
                          colors=[INK])
        static = KnotDiagram([Comp(tang)], scale=0.85, shift=UP * 0.2, width=6, colors=[INK])
        self.play(Create(static, lag_ratio=0.02), run_time=2.6)
        self.remove(static)
        self.add(cord)
        q = zh("真的打结了吗？", 48, GOLD, weight=BOLD).to_edge(DOWN, buff=1.2)
        self.play(FadeIn(q, shift=UP * 0.3), run_time=0.6)
        for _ in range(2):
            self.play(q.animate.scale(1.08), run_time=0.35, rate_func=there_and_back)
        # s1: becomes a trefoil; title
        self.at(1)
        self.play(FadeOut(q), tk.animate.set_value(1), run_time=3.0)
        self.remove(cord)
        spin = rotating_knot(self, comps_of(trefoil_pts(420)), 0.62, UP * 0.95, speed=0.5, tilt=0.4, width=7,
                             grad=[CYAN, MAGENTA, GOLD])
        self.add(spin)
        title = zh("扭结理论", 96, INK, weight=HEAVY)
        en = mono("KNOT  THEORY", 34, CYAN)
        tt = VGroup(title, en).arrange(DOWN, buff=0.25).move_to(DOWN * 2.0)
        self.play(FadeIn(title, shift=UP * 0.4), FadeIn(en, shift=UP * 0.2), run_time=1.0)
        # s2: the 16-level route map
        self.at(2)
        self.play(FadeOut(frozen(spin)), FadeOut(tt), run_time=0.6)
        self.remove(spin)
        tiles = VGroup()
        for i in range(1, 17):
            box = RoundedRectangle(width=2.95, height=1.05, corner_radius=0.1)
            box.set_stroke(DIM, 1.5, 0.8).set_fill("#0b1224", 0.9)
            num = mono(f"{i:02d}", 26, DIM).move_to(box.get_left() + RIGHT * 0.38)
            nm = LEVEL_NAMES[i]
            if len(nm) > 8:
                cut = (len(nm) + 1) // 2
                nm = nm[:cut] + "\n" + nm[cut:]
            name = zh(nm, 20, INK, line_spacing=0.8)
            if name.width > 2.1:
                name.scale_to_fit_width(2.1)
            name.next_to(num, RIGHT, buff=0.18)
            tiles.add(VGroup(box, num, name))
        tiles.arrange_in_grid(4, 4, buff=(0.22, 0.25)).move_to(UP * 0.05)
        head = mono("SPEEDRUN ROUTE  ·  16 STAGES", 28, MAGENTA).next_to(tiles, UP, buff=0.35)
        self.play(FadeIn(head, shift=DOWN * 0.2), LaggedStart(*[FadeIn(t, scale=0.8) for t in tiles], lag_ratio=0.05),
                  run_time=1.8)
        light = []
        for i, t in enumerate(tiles):
            c = NEON[i % len(NEON)]
            light.append(AnimationGroup(t[0].animate.set_stroke(c, 2.5, 1), t[1].animate.set_color(c)))
        self.play(LaggedStart(*light, lag_ratio=0.25), run_time=max(1.0, self.D(2) - 2.6))
        # s3: start!
        self.at(3)
        self.play(FadeOut(VGroup(tiles, head), scale=1.1), run_time=0.4)
        go = mono("START", 150, LIME, weight=HEAVY)
        go_g = glow(go.copy().set_fill(opacity=0).set_stroke(LIME, 3), LIME)
        self.play(FadeIn(go, scale=2.5), FadeIn(go_g, scale=2.5), run_time=0.35, rate_func=rush_from)
        h = self.hud(show_level=False)
        self.add(h)
        self.play(Flash(go.get_center(), color=LIME, line_length=1.2, num_lines=16, flash_radius=2.6),
                  run_time=0.6)
        self.wait_to(self.total - 0.4)
        self.play(FadeOut(VGroup(go, go_g), scale=0.6), run_time=0.35)
        self.finish()


# =====================================================================  01
def rope_curve(lam, n=420):
    """Trefoil opened at a lobe tip, with hanging tails (lam=1 open, lam=0 closed)."""
    rot = rot_matrix(0, 0, -2 * PI / 3 + PI / 2 - PI / 3)
    d = 0.32 * lam + 1e-3
    t = np.linspace(PI / 3 + d, PI / 3 + TAU_ - d, n)
    P = np.stack([np.sin(t) + 2 * np.sin(2 * t), np.cos(t) - 2 * np.cos(2 * t), np.sin(3 * t)], 1) @ rot.T
    if lam < 0.02:
        return Comp(P[:-1], True)
    T0 = P[0] - P[1]
    T0 /= np.linalg.norm(T0)
    T1 = P[-1] - P[-2]
    T1 /= np.linalg.norm(T1)
    s = np.linspace(0, 2.2 * lam, 40)[1:, None]
    tail0 = P[0] + T0 * s + np.array([0, -1, 0]) * s ** 2 * 0.5
    tail1 = P[-1] + T1 * s + np.array([0, -1, 0]) * s ** 2 * 0.5
    return Comp(np.vstack([tail0[::-1], P, tail1]), False)


def r1_curve(lam):
    u = np.linspace(-PI, PI, 200)
    y = (u - lam * np.sin(u)) / TAU_ * 2.4
    x = (-lam * np.cos(u) + lam) * 0.28 - 0.3
    return [Comp(np.stack([x, y, u], 1), False)]


def r2_curves(s):
    x = np.linspace(-1.3, 1.3, 120)
    b = np.exp(-x ** 2 / 0.3)
    a = np.stack([x, 0.55 - s * 1.15 * b, np.ones_like(x)], 1)
    c = np.stack([x, -0.55 + s * 1.15 * b, -np.ones_like(x)], 1)
    return [Comp(a, False), Comp(c, False)]


def r3_curves(c):
    t = np.linspace(-1.2, 1.2, 80)
    A = np.stack([t, t, np.zeros_like(t)], 1)
    B = np.stack([t, -t, -np.ones_like(t)], 1)
    C = np.stack([t * 1.1, np.full_like(t, c), np.ones_like(t)], 1)
    return [Comp(A, False), Comp(B, False), Comp(C, False)]


class Ch01(Chapter):
    CH = 1

    def construct(self):
        self.intro_level()
        # s1: rope -> knot
        self.at(1)
        lam = ValueTracker(1.0)
        rope = always_redraw(lambda: KnotDiagram([rope_curve(lam.get_value())], scale=0.75, shift=LEFT * 2.6 + UP * 0.3,
                                                 colors=[GOLD], width=8))
        static = KnotDiagram([rope_curve(1.0)], scale=0.75, shift=LEFT * 2.6 + UP * 0.3, colors=[GOLD], width=8)
        self.play(Create(static), run_time=2.0)
        self.remove(static)
        self.add(rope)
        lbl = tex(r"K:\ S^1 \hookrightarrow \mathbb{R}^3", 60).move_to(RIGHT * 3.4 + UP * 0.8)
        sub = zh("不自交的闭曲线", 34, INK).next_to(lbl, DOWN, buff=0.35)
        self.play(Write(lbl), run_time=1.0)
        self.play(lam.animate.set_value(0.0), FadeIn(sub, shift=UP * 0.2), run_time=max(1.5, self.E(1) - self.time - 0.4))
        # s2: unknot, trefoil, Hopf, Borromean
        self.at(2)
        self.play(FadeOut(VGroup(lbl, sub)), FadeOut(frozen(rope)), run_time=0.5)
        self.remove(rope)
        items = [
            (KnotDiagram(comps_of(circle_pts(160, 1.3)), scale=0.95, colors=[CYAN]), "平凡结"),
            (KnotDiagram(comps_of(trefoil_pts()), scale=0.52, colors=[MAGENTA]), "三叶结"),
            (KnotDiagram(comps_of(*hopf_pts(r=1.0, d=1.1)), scale=0.68, colors=[GOLD, LIME]), "霍普夫链环"),
            (KnotDiagram(comps_of(*borromean_pts()), scale=0.78, colors=[RED_N, LIME, SKY]), "博罗梅安环"),
        ]
        grp = VGroup()
        for d, name in items:
            grp.add(VGroup(d, zh(name, 30, INK).next_to(d, DOWN, buff=0.3)))
        grp.arrange(RIGHT, buff=0.75).move_to(UP * 0.1)
        for g in grp:
            g[1].align_to(grp, DOWN)
        self.play(LaggedStart(*[AnimationGroup(Create(g[0]), FadeIn(g[1], shift=UP * 0.2)) for g in grp],
                              lag_ratio=0.35), run_time=min(4.0, self.D(2) - 0.8))
        # s3: isotopy via an ambient deformation of space
        self.at(3)
        self.play(FadeOut(grp), run_time=0.5)
        a = ValueTracker(1.0)

        def warp(P, k):
            x, y = P[..., 0], P[..., 1]
            return np.stack([x + k * 0.55 * np.sin(1.2 * y + 0.4), y + k * 0.45 * np.sin(1.1 * x - 0.3),
                             P[..., 2] + k * 0.5 * np.sin(0.9 * x + 0.8 * y)], -1)

        base = trefoil_pts(420)

        def grid_build():
            k = a.get_value()
            g = VGroup()
            for xv in np.linspace(-5, 5, 13):
                ys = np.linspace(-3.2, 3.2, 40)
                P = warp(np.stack([np.full_like(ys, xv), ys, np.zeros_like(ys)], 1) / 1.0, k)
                g.add(VMobject().set_points_smoothly(np.column_stack([P[:, :2] * 0.62, np.zeros(40)]) + UP * 0.1))
            for yv in np.linspace(-3.2, 3.2, 9):
                xs_ = np.linspace(-5, 5, 50)
                P = warp(np.stack([xs_, np.full_like(xs_, yv), np.zeros_like(xs_)], 1), k)
                g.add(VMobject().set_points_smoothly(np.column_stack([P[:, :2] * 0.62, np.zeros(50)]) + UP * 0.1))
            return g.set_stroke(SKY, 1.2, 0.25)

        grid = always_redraw(grid_build)
        kn = always_redraw(lambda: KnotDiagram([Comp(warp(base, a.get_value()))], scale=0.62, shift=UP * 0.1,
                                               colors=[MAGENTA], width=7))
        self.play(FadeIn(grid), FadeIn(kn), run_time=0.8)
        iso = zh("同痕：连续变形，不剪断、不穿过自己", 32, GOLD).to_edge(DOWN, buff=1.05)
        self.play(a.animate.set_value(-0.6), FadeIn(iso, shift=UP * 0.2), run_time=2.6)
        self.play(a.animate.set_value(0.0), run_time=max(1.5, self.E(3) - self.time - 0.3))
        # s4: projection
        self.at(4)
        self.play(FadeOut(frozen(grid, kn)), FadeOut(iso), run_time=0.4)
        self.remove(grid, kn)
        spin = rotating_knot(self, comps_of(trefoil_pts(380)), 0.55, LEFT * 3.6 + UP * 0.2, speed=0.8, tilt=0.6,
                             width=6, colors=[MAGENTA])
        lab3 = zh("三维中的扭结", 28, INK).move_to(LEFT * 3.6 + DOWN * 2.1)
        arrow = Arrow(LEFT * 1.0, RIGHT * 1.0, color=GOLD, stroke_width=6).shift(UP * 0.2)
        alab = zh("投影", 26, GOLD).next_to(arrow, UP, buff=0.1)
        diag = KnotDiagram(comps_of(trefoil_pts()), scale=0.55, shift=RIGHT * 3.6 + UP * 0.2, colors=[CYAN])
        lab2 = zh("扭结图 = 投影 + 上下信息", 28, INK).move_to(RIGHT * 3.6 + DOWN * 2.1)
        self.add(spin)
        self.play(FadeIn(lab3), run_time=0.6)
        self.play(GrowArrow(arrow), FadeIn(alab), run_time=0.6)
        self.play(Create(diag), FadeIn(lab2), run_time=1.6)
        x0 = diag.crossings[0]
        cp = diag.cpoint(x0)
        ring = Circle(radius=0.38, color=GOLD).move_to(cp).set_stroke(width=4)
        self.play(Create(ring), run_time=0.5)
        o_dir = np.array([*x0["dover"], 0])
        u_dir = np.array([*x0["dunder"], 0])
        up_l = zh("上", 26, LIME).move_to(cp + o_dir * 0.7 + np.array([-o_dir[1], o_dir[0], 0]) * 0.25)
        dn_l = zh("下", 26, RED_N).move_to(cp + u_dir * 0.7 + np.array([-u_dir[1], u_dir[0], 0]) * 0.25)
        self.play(FadeIn(up_l, scale=1.4), FadeIn(dn_l, scale=1.4), run_time=0.5)
        # s5: Reidemeister theorem
        self.at(5)
        self.play(FadeOut(VGroup(lab3, arrow, alab, diag, lab2, ring, up_l, dn_l)), FadeOut(frozen(spin)), run_time=0.5)
        self.remove(spin)
        th = zh("赖德迈斯特定理", 40, GOLD, weight=BOLD).to_edge(UP, buff=1.0)
        stmt = tex(r"K_1 \simeq K_2 \iff D_1 \xrightarrow{\ \text{R1, R2, R3}\ } D_2", 50).next_to(th, DOWN, buff=0.35)
        self.play(Write(th), run_time=0.8)
        self.play(Write(stmt), run_time=1.4)
        panels = VGroup(*[labeled_panel(f"R{i}", 3.7, 3.0, c) for i, c in zip((1, 2, 3), (CYAN, MAGENTA, GOLD))])
        panels.arrange(RIGHT, buff=0.35).shift(DOWN * 1.05)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.3) for p in panels], lag_ratio=0.2), run_time=1.0)
        ctr = [p[0].get_center() + DOWN * 0.1 for p in panels]
        # s6: R1
        self.at(6)
        lamv = ValueTracker(0.3)
        r1 = always_redraw(lambda: KnotDiagram(r1_curve(lamv.get_value()), scale=0.95, shift=ctr[0], colors=[CYAN], width=6))
        self.add(r1)
        self.play(lamv.animate.set_value(2.3), run_time=self.D(6) * 0.45)
        self.play(lamv.animate.set_value(0.3), run_time=self.D(6) * 0.4)
        # s7: R2
        self.at(7)
        sv = ValueTracker(0.0)
        r2 = always_redraw(lambda: KnotDiagram(r2_curves(sv.get_value()), scale=1.1, shift=ctr[1], colors=[MAGENTA, VIOLET], width=6))
        self.add(r2)
        self.play(sv.animate.set_value(1.0), run_time=self.D(7) * 0.45)
        self.play(sv.animate.set_value(0.0), run_time=self.D(7) * 0.4)
        # s8: R3
        self.at(8)
        cv = ValueTracker(-0.75)
        r3 = always_redraw(lambda: KnotDiagram(r3_curves(cv.get_value()), scale=1.0, shift=ctr[2], colors=[GOLD, ORANGE, LIME], width=6))
        self.add(r3)
        self.play(cv.animate.set_value(0.75), run_time=self.D(8) * 0.55)
        self.play(cv.animate.set_value(-0.75), run_time=self.D(8) * 0.35)
        # s9: invariants
        self.at(9)
        for m in (r1, r2, r3):
            m.clear_updaters()
        self.play(FadeOut(VGroup(th, stmt, panels, r1, r2, r3)), run_time=0.5)
        d1 = KnotDiagram(comps_of(trefoil_pts()), scale=0.38, shift=LEFT * 5 + UP * 0.9, colors=[MAGENTA])
        d2 = KnotDiagram(comps_of(circle_pts(120, 1.4)), scale=0.6, shift=LEFT * 5 + DOWN * 1.3, colors=[CYAN])
        box = panel(2.6, 1.6, GOLD, 0.08, 0.9).move_to(ORIGIN + DOWN * 0.2)
        ftxt = tex(r"f", 90, GOLD).move_to(box)
        mach = VGroup(box, ftxt)
        a1 = Arrow(d1.get_right(), box.get_left() + UP * 0.3, color=DIM, buff=0.15)
        a2 = Arrow(d2.get_right(), box.get_left() + DOWN * 0.3, color=DIM, buff=0.15)
        o1 = tex(r"f(D_1)", 46, MAGENTA).move_to(RIGHT * 3.2 + UP * 0.9)
        o2 = tex(r"f(D_2)", 46, CYAN).move_to(RIGHT * 3.2 + DOWN * 1.3)
        b1 = Arrow(box.get_right() + UP * 0.3, o1.get_left(), color=DIM, buff=0.15)
        b2 = Arrow(box.get_right() + DOWN * 0.3, o2.get_left(), color=DIM, buff=0.15)
        neq = tex(r"\neq", 60, RED_N).move_to(RIGHT * 3.2 + DOWN * 0.2).rotate(PI / 2)
        concl = tex(r"f(D_1)\neq f(D_2)\ \Rightarrow\ K_1 \neq K_2", 44, INK).to_edge(DOWN, buff=1.0)
        inv = zh("不变量：三种变换下都不变", 34, GOLD).to_edge(UP, buff=1.0)
        self.play(Create(d1), Create(d2), run_time=1.0)
        self.play(FadeIn(mach, scale=0.8), FadeIn(inv), GrowArrow(a1), GrowArrow(a2), run_time=1.0)
        self.play(GrowArrow(b1), GrowArrow(b2), FadeIn(o1), FadeIn(o2), run_time=1.0)
        self.play(FadeIn(neq, scale=1.5), Write(concl), run_time=1.2)
        # s10: tricolouring
        self.at(10)
        self.play(FadeOut(VGroup(d1, d2, mach, a1, a2, o1, o2, b1, b2, neq, concl, inv)), run_time=0.5)
        tre = KnotDiagram(comps_of(trefoil_pts()), scale=0.68, shift=LEFT * 3.4 + UP * 0.15, colors=[INK])
        self.play(Create(tre), run_time=1.0)
        colored = KnotDiagram(comps_of(trefoil_pts()), scale=0.68, shift=LEFT * 3.4 + UP * 0.15,
                              color_fn=lambda k, p: TRI[k % 3])
        rules = VGroup(
            VGroup(colored_cross(RED_N, RED_N, RED_N, 1.0), check_mark(size=0.45)),
            VGroup(colored_cross(RED_N, LIME, SKY, 1.0), check_mark(size=0.45)),
            VGroup(colored_cross(RED_N, LIME, LIME, 1.0), cross_mark(size=0.4)),
        )
        for r in rules:
            r.arrange(DOWN, buff=0.3)
        rules.arrange(RIGHT, buff=0.6).move_to(RIGHT * 3.2 + UP * 0.6)
        rl = VGroup(zh("同色", 26), zh("全不同", 26), zh("两同一异", 26))
        for t, r in zip(rl, rules):
            t.next_to(r, DOWN, buff=0.2)
        cond = zh("且至少用两种颜色", 28, GOLD).next_to(VGroup(rules, rl), DOWN, buff=0.35)
        for k in range(3):
            self.play(Transform(tre.strands[k], colored.strands[k]), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(VGroup(r, t), shift=UP * 0.2) for r, t in zip(rules, rl)], lag_ratio=0.4),
                  run_time=2.4)
        self.play(FadeIn(cond), run_time=0.6)
        # s11: unknot cannot; trefoil knotted
        self.at(11)
        self.play(FadeOut(VGroup(rules, rl, cond)), run_time=0.4)
        unk = KnotDiagram(comps_of(circle_pts(140, 1.35)), scale=0.85, shift=RIGHT * 3.2 + UP * 0.15, colors=[RED_N])
        ul = zh("只有一段弧 → 只能一种颜色", 26, INK).next_to(unk, DOWN, buff=0.3)
        self.play(Create(unk), FadeIn(ul), run_time=1.0)
        cm = cross_mark(size=0.7).move_to(unk.get_center())
        ck = check_mark(size=0.8).move_to(tre.get_center())
        self.play(FadeIn(cm, scale=1.5), FadeIn(ck, scale=1.5), run_time=0.6)
        st = stamp("CLEAR!").move_to(UP * 0.2)
        self.wait_to(self.E(11) - 1.6)
        self.play(FadeIn(st, scale=2.2), run_time=0.35, rate_func=rush_from)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()


# =====================================================================  02
class Ch02(Chapter):
    CH = 2

    def construct(self):
        self.intro_level()
        tre = comps_of(trefoil_pts())
        # s1: every knot bounds an orientable surface
        self.at(1)
        circ = KnotDiagram(comps_of(circle_pts(160, 1.2)), scale=1.0, shift=LEFT * 3.4 + UP * 0.2, colors=[CYAN])
        disk = Circle(radius=1.2).move_to(LEFT * 3.4 + UP * 0.2).set_fill(CYAN, 0.18).set_stroke(width=0)
        t1 = tex(r"\partial F = K", 56, INK).move_to(RIGHT * 2.6 + UP * 1.0)
        t2 = zh("F：可定向曲面（塞弗特曲面）", 32, GOLD).next_to(t1, DOWN, buff=0.4)
        self.play(Create(circ), run_time=1.0)
        self.play(FadeIn(disk), Write(t1), run_time=1.2)
        self.play(FadeIn(t2, shift=UP * 0.2), run_time=0.8)
        # s2: Seifert's algorithm
        self.at(2)
        self.play(FadeOut(VGroup(circ, disk, t1, t2)), run_time=0.5)
        sh = UP * 0.2
        d = KnotDiagram(tre, scale=0.7, shift=sh, colors=[CYAN])
        self.play(Create(d), run_time=1.2)
        # orientation arrows
        P = to_scene(tre[0].p, 0.7, sh)
        arrows = VGroup()
        for i in (30, 150, 270):
            arrows.add(arrow_tip(P[i], P[i + 2] - P[i], GOLD, 0.22))
        self.play(FadeIn(arrows, scale=1.5), run_time=0.6)
        loops, xs = resolve(tre, {0: "O", 1: "O", 2: "O"})
        sc = KnotDiagram(loops, scale=0.7, shift=sh, colors=[GOLD, MAGENTA])
        rings = VGroup(*[Circle(radius=0.35).move_to(d.cpoint(x)).set_stroke(LIME, 3) for x in xs])
        self.play(LaggedStart(*[Create(r) for r in rings], lag_ratio=0.3), run_time=1.0)
        self.play(FadeOut(arrows), ReplacementTransform(d, sc), run_time=1.8)
        self.play(FadeOut(rings), run_time=0.4)
        lab = zh("塞弗特圆 × 2", 30, GOLD).to_edge(DOWN, buff=1.05)
        self.play(FadeIn(lab), run_time=0.5)
        # s3: discs + twisted bands
        self.at(3)
        fills = VGroup()
        for c, col, op in zip(loops, [GOLD, MAGENTA], [0.16, 0.32]):
            pts = to_scene(c.p, 0.7, sh)
            fills.add(Polygon(*pts[::3]).set_fill(col, op).set_stroke(width=0))
        self.play(FadeIn(fills), run_time=1.0)
        bands = VGroup()
        for x in xs:
            cp = d.cpoint(x)
            do = np.array([*x["dover"], 0]) * 0.33
            du = np.array([*x["dunder"], 0]) * 0.33
            t1_ = Polygon(cp - do, cp - du, cp).set_fill(LIME, 0.75).set_stroke(LIME, 2)
            t2_ = Polygon(cp + do, cp + du, cp).set_fill(LIME, 0.75).set_stroke(LIME, 2)
            bands.add(VGroup(t1_, t2_))
        self.play(LaggedStart(*[GrowFromCenter(b) for b in bands], lag_ratio=0.3), run_time=1.4)
        btxt = zh("半扭转的带子", 28, LIME).next_to(sc, RIGHT, buff=0.6).shift(UP * 0.5)
        self.play(FadeIn(btxt), FadeOut(lab), run_time=0.6)
        euler = tex(r"\chi = s - c = 2 - 3 = -1", 42).next_to(sc, RIGHT, buff=0.6).shift(DOWN * 0.4)
        self.play(Write(euler), run_time=1.2)
        # s4: genus
        self.at(4)
        surf = VGroup(sc, fills, bands, btxt, euler)
        self.play(surf.animate.scale(0.62).to_edge(LEFT, buff=0.6), run_time=0.8)
        gf = tex(r"g(F) = \tfrac{1}{2}(1-\chi) = 1", 46, INK).move_to(RIGHT * 2.2 + UP * 1.7)
        # little genus pictures: disc, torus with hole
        d0 = Ellipse(width=1.6, height=1.0).set_fill(CYAN, 0.2).set_stroke(CYAN, 3)
        tor = VGroup(Ellipse(width=2.0, height=1.1).set_stroke(MAGENTA, 3).set_fill(MAGENTA, 0.15),
                     Arc(radius=0.45, start_angle=PI + 0.5, angle=PI - 1.0).set_stroke(MAGENTA, 3).shift(UP * 0.1),
                     Arc(radius=0.35, start_angle=0.6, angle=PI - 1.2).set_stroke(MAGENTA, 3).shift(DOWN * 0.18))
        pics = VGroup(VGroup(d0, tex("g=0", 36).next_to(d0, DOWN, buff=0.2)),
                      VGroup(tor, tex("g=1", 36).next_to(tor, DOWN, buff=0.2))).arrange(RIGHT, buff=1.0)
        pics.move_to(RIGHT * 2.2 + DOWN * 0.1)
        gk = tex(r"g(K) = \min_F\, g(F)", 46, GOLD).move_to(RIGHT * 2.2 + DOWN * 1.9)
        self.play(Write(gf), run_time=1.0)
        self.play(FadeIn(pics, shift=UP * 0.2), run_time=1.0)
        self.play(Write(gk), run_time=1.0)
        vals = VGroup(tex(r"g(\bigcirc)=0", 38, CYAN), tex(r"g(3_1)=1", 38, MAGENTA)).arrange(RIGHT, buff=0.8)
        vals.next_to(gk, DOWN, buff=0.3)
        self.wait_to(self.E(4) - 3.5)
        self.play(FadeIn(vals, shift=UP * 0.2), run_time=0.8)
        # s5: connected sum
        self.at(5)
        self.play(FadeOut(VGroup(surf, gf, pics, gk, vals)), run_time=0.5)
        A = trefoil_pts(400)
        B = figure8_pts2(480) * [1.0, 1.0, 1]
        dA = KnotDiagram(comps_of(A), scale=0.5, shift=LEFT * 3.0 + UP * 0.2, colors=[CYAN])
        dB = KnotDiagram(comps_of(B), scale=0.5, shift=RIGHT * 3.0 + UP * 0.2, colors=[MAGENTA])
        self.play(Create(dA), Create(dB), run_time=1.2)
        cs = smooth_closed(connect_sum(A, B, gapx=2.2, cut=1.0), iters=10)
        dS = KnotDiagram(comps_of(cs), scale=0.5, shift=UP * 0.2, color_fn=lambda k, p: CYAN if p["pts"][:, 0].mean() < 0 else MAGENTA)
        sc1 = Text("✂", font_size=60, color=GOLD).move_to(UP * 0.2)
        self.play(FadeIn(sc1, scale=1.5), run_time=0.4)
        self.play(FadeOut(sc1), ReplacementTransform(VGroup(dA, dB), dS), run_time=1.6)
        hs = tex(r"K_1 \,\#\, K_2", 54, GOLD).to_edge(DOWN, buff=1.0)
        self.play(Write(hs), run_time=0.8)
        # s6: additivity of genus
        self.at(6)
        self.play(dS.animate.scale(0.75).shift(UP * 0.9), hs.animate.shift(UP * 2.4).scale(0.8), run_time=0.7)
        add = tex(r"g(K_1 \# K_2) = g(K_1) + g(K_2)", 54, INK).shift(DOWN * 1.3)
        box = SurroundingRectangle(add, buff=0.2, corner_radius=0.1).set_stroke(GOLD, 3)
        self.play(Write(add), Create(box), run_time=1.4)
        cor = tex(r"\bigcirc = K_1 \# K_2 \;\Rightarrow\; 0 = g_1 + g_2 \;\Rightarrow\; g_1 = g_2 = 0", 40, CYAN)
        cor.next_to(box, DOWN, buff=0.35)
        self.wait_to(self.S(6) + self.D(6) * 0.45)
        self.play(Write(cor), run_time=1.6)
        # s7: unique prime factorisation
        self.at(7)
        self.play(FadeOut(VGroup(dS, hs, add, box, cor)), run_time=0.5)
        num = tex(r"360 = 2^3 \cdot 3^2 \cdot 5", 56, INK).move_to(UP * 1.9)
        self.play(Write(num), run_time=1.2)
        ks = [KnotDiagram(comps_of(trefoil_pts()), scale=0.3, colors=[CYAN]),
              KnotDiagram(comps_of(figure8_pts2()), scale=0.28, colors=[MAGENTA]),
              KnotDiagram(comps_of(torus_pts(2, 5)), scale=0.36, colors=[GOLD])]
        eq = VGroup(tex("K", 60), tex("=", 60), ks[0], tex(r"\#", 60), ks[1], tex(r"\#", 60), ks[2])
        eq.arrange(RIGHT, buff=0.35).move_to(DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(m, scale=0.7) for m in eq], lag_ratio=0.15), run_time=2.0)
        sch = zh("舒伯特 1949：素分解唯一", 34, GOLD).to_edge(DOWN, buff=1.05)
        self.play(FadeIn(sch, shift=UP * 0.2), run_time=0.8)
        self.wait_to(self.total - 0.45)
        self.play(FadeOut(VGroup(num, eq, sch)), run_time=0.4)
        self.finish()


# =====================================================================  03
class Ch03(Chapter):
    CH = 3

    def construct(self):
        self.intro_level()
        # s1: A and B smoothings
        self.at(1)
        X = glyph("A", 1.6, CYAN, arrows=False)
        As = glyph("Asm", 1.6, LIME)
        Bs = glyph("Bsm", 1.6, MAGENTA)
        X.move_to(LEFT * 3.8 + UP * 0.3)
        As.move_to(RIGHT * 1.2 + UP * 1.4)
        Bs.move_to(RIGHT * 1.2 + DOWN * 1.0)
        la = zh("A 拆分", 32, LIME).next_to(As, RIGHT, buff=0.4)
        lb = zh("B 拆分", 32, MAGENTA).next_to(Bs, RIGHT, buff=0.4)
        aa = Arrow(X.get_right(), As.get_left(), color=LIME, buff=0.1)
        ab = Arrow(X.get_right(), Bs.get_left(), color=MAGENTA, buff=0.1)
        self.play(FadeIn(X, scale=0.7), run_time=0.7)
        self.play(GrowArrow(aa), FadeIn(As), FadeIn(la), run_time=0.9)
        self.play(GrowArrow(ab), FadeIn(Bs), FadeIn(lb), run_time=0.9)
        # s2: the three bracket rules
        self.at(2)
        self.play(FadeOut(VGroup(X, As, Bs, la, lb, aa, ab)), run_time=0.4)
        g = lambda k: glyph(k, 0.75, CYAN, arrows=False)
        r1 = row(r"\big\langle", g("A"), r"\big\rangle = A\,\big\langle", g("Asm"), r"\big\rangle + A^{-1}\big\langle",
                 g("Bsm"), r"\big\rangle", size=46)
        r2 = row(r"\big\langle L \sqcup \bigcirc \big\rangle = (-A^{2}-A^{-2})\,\big\langle L \big\rangle", size=46)
        r3 = row(r"\big\langle \bigcirc \big\rangle = 1", size=46)
        rules = VGroup(r1, r2, r3).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(UP * 0.3)
        nums = VGroup(*[mono(f"{i}", 26, GOLD).next_to(r, LEFT, buff=0.4) for i, r in zip((1, 2, 3), rules)])
        dl = tex(r"\delta = -A^{2}-A^{-2}", 40, GOLD).to_edge(DOWN, buff=1.1)
        self.play(FadeIn(nums[0]), Write(r1), run_time=min(2.5, self.D(2) * 0.3))
        self.wait_to(self.S(2) + self.D(2) * 0.45)
        self.play(FadeIn(nums[1]), Write(r2), run_time=1.6)
        self.wait_to(self.S(2) + self.D(2) * 0.8)
        self.play(FadeIn(nums[2]), Write(r3), FadeIn(dl), run_time=1.2)
        # s3: state sum on the trefoil
        self.at(3)
        self.play(FadeOut(VGroup(rules, nums, dl)), run_time=0.4)
        tre = comps_of(trefoil_pts(300))
        states, total, xs = bracket_states(tre)
        cells = VGroup()
        for s in states:
            dd = KnotDiagram(s["loops"], scale=0.24, colors=NEON, width=4)
            lbl = tex(r"A^{%d}\delta^{%d}" % (s["a"] - s["b"], len(s["loops"]) - 1), 30, INK)
            ab_ = mono("".join(s["choice"][k] for k in range(3)), 18, DIM)
            cells.add(VGroup(dd, lbl.next_to(dd, DOWN, buff=0.12), ab_.next_to(dd, UP, buff=0.08)))
        cells.arrange_in_grid(2, 4, buff=(0.55, 0.3)).move_to(UP * 0.55)
        self.play(LaggedStart(*[FadeIn(c, scale=0.7) for c in cells], lag_ratio=0.12), run_time=2.6)
        res = tex(r"\langle 3_1 \rangle = A^{-7} - A^{-3} - A^{5}", 48, GOLD).to_edge(DOWN, buff=1.05)
        self.wait_to(self.S(3) + self.D(3) * 0.45)
        self.play(Write(res), run_time=1.4)
        kink = row(r"\big\langle", glyph("kink", 0.8, MAGENTA), r"\big\rangle = -A^{3}\,\big\langle",
                   glyph("line", 0.8, MAGENTA), r"\big\rangle", size=44)
        kink.move_to(res)
        self.wait_to(self.S(3) + self.D(3) * 0.72)
        self.play(FadeOut(res, shift=UP * 0.3), FadeIn(kink, shift=UP * 0.3), run_time=0.8)
        # s4: writhe
        self.at(4)
        self.play(FadeOut(VGroup(cells, kink)), run_time=0.4)
        d = KnotDiagram(comps_of(trefoil_pts()), scale=0.62, shift=LEFT * 3.2 + UP * 0.1, colors=[CYAN])
        self.play(Create(d), run_time=1.0)
        P = to_scene(trefoil_pts()[:, :], 0.62, LEFT * 3.2 + UP * 0.1)
        arr = VGroup(*[arrow_tip(P[i], P[i + 2] - P[i], GOLD, 0.2) for i in (30, 150, 270)])
        signs = VGroup(*[tex("+1", 34, LIME).move_to(d.cpoint(x) + 0.45 * normalize(d.cpoint(x) - d.get_center()))
                         for x in d.crossings])
        self.play(FadeIn(arr), LaggedStart(*[FadeIn(s, scale=1.4) for s in signs], lag_ratio=0.3), run_time=1.2)
        gp = VGroup(glyph("pos", 1.0, LIME), glyph("neg", 1.0, RED_N)).arrange(RIGHT, buff=0.8).move_to(RIGHT * 3 + UP * 1.0)
        gl = VGroup(tex("+1", 40, LIME).next_to(gp[0], DOWN, buff=0.2), tex("-1", 40, RED_N).next_to(gp[1], DOWN, buff=0.2))
        self.play(FadeIn(gp), FadeIn(gl), run_time=0.8)
        w = tex(r"w(D) = \sum \varepsilon(c) = 3", 46, INK).move_to(RIGHT * 3 + DOWN * 1.4)
        self.play(Write(w), run_time=1.0)
        # s5: Jones polynomial + skein
        self.at(5)
        self.play(FadeOut(VGroup(gp, gl, w, d, arr, signs)), run_time=0.6)
        V = tex(r"V(L) = \left(-A^{3}\right)^{-w(D)} \langle D \rangle \Big|_{A = t^{-1/4}}", 50, INK).move_to(UP * 1.4 + RIGHT * 1.0)
        self.play(Write(V), run_time=1.6)
        gg = lambda k: glyph(k, 0.75, CYAN)
        sk = row(r"t^{-1}V\Big(", gg("pos"), r"\Big) - t\,V\Big(", gg("neg"), r"\Big) + (t^{-1/2}-t^{1/2})V\Big(",
                 gg("zero"), r"\Big) = 0", size=40)
        sk.move_to(DOWN * 0.8)
        if sk.width > 12.5:
            sk.scale_to_fit_width(12.5)
        lbls = VGroup(tex("L_+", 32, GOLD).next_to(sk[1], DOWN, buff=0.1), tex("L_-", 32, GOLD).next_to(sk[3], DOWN, buff=0.1),
                      tex("L_0", 32, GOLD).next_to(sk[5], DOWN, buff=0.1))
        self.wait_to(self.S(5) + self.D(5) * 0.4)
        self.play(FadeIn(sk, shift=UP * 0.2), FadeIn(lbls), run_time=1.4)
        # s6: right trefoil vs left trefoil
        self.at(6)
        self.play(FadeOut(VGroup(V, sk, lbls, d)), run_time=0.4)
        R = KnotDiagram(comps_of(trefoil_pts()), scale=0.55, shift=LEFT * 3.4 + UP * 0.6, colors=[CYAN])
        L = KnotDiagram(comps_of(trefoil_pts() * [-1, 1, 1]), scale=0.55, shift=RIGHT * 3.4 + UP * 0.6, colors=[MAGENTA])
        vr = tex(r"V = t + t^{3} - t^{4}", 46, CYAN).next_to(R, DOWN, buff=0.4)
        vl = tex(r"V = t^{-1} + t^{-3} - t^{-4}", 46, MAGENTA).next_to(L, DOWN, buff=0.4)
        nr = zh("右手三叶结", 28).next_to(R, UP, buff=0.25)
        nl = zh("左手三叶结（镜像）", 28).next_to(L, UP, buff=0.25)
        mirror = DashedLine(UP * 2.6, DOWN * 2.4, color=DIM)
        self.play(Create(R), FadeIn(nr), run_time=1.0)
        self.play(Write(vr), run_time=1.2)
        self.play(Create(mirror), TransformFromCopy(R, L), FadeIn(nl), run_time=1.2)
        self.play(Write(vl), run_time=1.2)
        # s7: chirality detected
        self.at(7)
        ne = tex(r"\neq", 90, RED_N).move_to(UP * 0.6)
        self.play(FadeOut(mirror), FadeIn(ne, scale=2), run_time=0.5)
        al = tex(r"\Delta(t) = t - 1 + t^{-1}\ \ (\text{both})", 36, DIM).to_edge(DOWN, buff=1.05)
        self.play(FadeIn(al), run_time=0.8)
        self.play(Indicate(vr, color=GOLD), Indicate(vl, color=GOLD), run_time=1.2)
        self.wait_to(self.total - 0.45)
        self.play(FadeOut(VGroup(R, L, vr, vl, nr, nl, ne, al)), run_time=0.4)
        self.finish()


# =====================================================================  04
class Ch04(Chapter):
    CH = 4

    def construct(self):
        self.intro_level()
        # s1: walk along the knot: over/under alternate
        self.at(1)
        shA, shB = LEFT * 3.3 + UP * 0.2, RIGHT * 3.3 + UP * 0.2
        tp = trefoil_pts(400)
        fp = figure8_pts2(480)
        dA = KnotDiagram(comps_of(tp), scale=0.62, shift=shA, colors=[CYAN])
        dB = KnotDiagram(comps_of(fp), scale=0.6, shift=shB, colors=[MAGENTA])
        self.play(Create(dA), Create(dB), run_time=1.2)

        def walker(pts3, diag, scale, shift, color):
            P = to_scene(pts3, scale, shift)
            n = len(P)
            vt = ValueTracker(0)
            dot = always_redraw(lambda: glow(Dot(P[int(vt.get_value()) % n], radius=0.09, color=WHITE), color))
            labels = VGroup()
            events = []
            for x in diag.crossings:
                for role, txt, col in (("over", "上", LIME), ("under", "下", RED_N)):
                    idx = x["over"][1] if role == "over" else x["under"][1]
                    lab = zh(txt, 26, col, weight=BOLD)
                    pos = P[int(idx) % n]
                    tan = P[(int(idx) + 2) % n] - P[int(idx) % n]
                    nrm = normalize(np.array([-tan[1], tan[0], 0]))
                    lab.move_to(pos + nrm * 0.32)
                    events.append((idx, lab))
            for idx, lab in events:
                lab.add_updater(lambda m, i=idx: m.set_opacity(1.0 if vt.get_value() >= i else 0.0))
                labels.add(lab)
            return vt, dot, labels, n

        vA, dotA, labA, nA = walker(tp, dA, 0.62, shA, CYAN)
        vB, dotB, labB, nB = walker(fp, dB, 0.6, shB, MAGENTA)
        self.add(dotA, dotB, labA, labB)
        rt = max(3.0, self.E(1) - self.time - 0.6)
        self.play(vA.animate.set_value(nA - 1), vB.animate.set_value(nB - 1), run_time=rt, rate_func=linear)
        # s2: checkerboard
        self.at(2)
        for m in (*labA, *labB):
            m.clear_updaters()
        self.play(FadeOut(frozen(dotA, dotB)), FadeOut(VGroup(labA, labB)), run_time=0.4)
        imA = evenodd_image([to_scene(tp, 0.62, shA)], CYAN, 0.32)
        imB = evenodd_image([to_scene(fp, 0.6, shB)], MAGENTA, 0.32)
        self.play(FadeIn(imA), FadeIn(imB), run_time=1.5)
        self.bring_to_front(dA, dB)
        cb = zh("棋盘染色", 34, GOLD).to_edge(DOWN, buff=1.05)
        self.play(FadeIn(cb), run_time=0.5)
        # s3: Tait graphs of the trefoil
        self.at(3)
        self.play(FadeOut(VGroup(dB, cb)), FadeOut(imB), run_time=0.4)
        cents = region_centroids(imA)
        X = [dA.cpoint(x) for x in dA.crossings]
        vdots = VGroup(*[Dot(c, radius=0.11, color=GOLD) for c in cents])
        edges = VGroup()
        for x in X:
            near = sorted(cents, key=lambda c: np.linalg.norm(c - x))[:2]
            edges.add(VMobject().set_points_smoothly([near[0], x, near[1]]).set_stroke(GOLD, 5))
        self.play(FadeIn(vdots, scale=1.6), run_time=0.6)
        self.play(Create(edges), run_time=1.0)
        tri = VGroup(*[Dot(c, radius=0.11, color=GOLD) for c in cents])
        # dual graph: centre + outside
        ctr = shA + UP * 0.1
        tb_v = VGroup(Dot(RIGHT * 3.0 + UP * 1.2, radius=0.12, color=SKY), Dot(RIGHT * 3.0 + DOWN * 1.2, radius=0.12, color=SKY))
        tb_e = VGroup(*[ArcBetweenPoints(tb_v[0].get_center(), tb_v[1].get_center(), angle=a).set_stroke(SKY, 5)
                        for a in (-1.2, 0, 1.2)])
        tg1 = VGroup(*[Dot(RIGHT * 3.0 + 1.2 * np.array([np.cos(a), np.sin(a), 0]), radius=0.12, color=GOLD)
                       for a in (PI / 2, PI / 2 + TAU_ / 3, PI / 2 + 2 * TAU_ / 3)])
        tg1_e = VGroup(*[Line(tg1[i].get_center(), tg1[(i + 1) % 3].get_center()).set_stroke(GOLD, 5) for i in range(3)])
        grp1 = VGroup(tg1_e, tg1).move_to(RIGHT * 1.6 + UP * 0.2)
        grp2 = VGroup(tb_e, tb_v).move_to(RIGHT * 4.9 + UP * 0.2)
        l1 = zh("三角形", 28, GOLD).next_to(grp1, DOWN, buff=0.35)
        l2 = zh("三条平行边", 28, SKY).next_to(grp2, DOWN, buff=0.35)
        self.play(TransformFromCopy(VGroup(edges, vdots), grp1), FadeIn(l1), run_time=1.2)
        self.play(FadeIn(grp2, shift=LEFT * 0.3), FadeIn(l2), run_time=1.0)
        dual = zh("互为对偶", 30, INK).move_to(RIGHT * 3.25 + UP * 1.0)
        dd = DoubleArrow(grp1.get_right(), grp2.get_left(), color=INK, buff=0.2)
        self.play(GrowFromCenter(dd), FadeIn(dual), run_time=0.8)
        # s4: Tait's knot tables
        self.at(4)
        self.play(FadeOut(Group(dA, imA, vdots, edges, grp1, grp2, l1, l2, dual, dd)), run_time=0.5)
        rng = np.random.default_rng(3)
        knots = [trefoil_pts(300), figure8_pts2(360), torus_pts(2, 5, 400), torus_pts(2, 7, 500)]
        for sd in range(4):
            t = np.linspace(0, TAU_, 500, endpoint=False)
            r = 1 + 0.45 * np.sin(3 * t + sd) + 0.25 * np.cos((5 + sd % 2) * t)
            xy = np.column_stack([r * np.cos(2 * t + 0.3 * sd), r * np.sin(3 * t)])
            knots.append(alternating_from_2d(xy * 1.4))
        tab = VGroup()
        for i, k in enumerate(knots):
            dk = KnotDiagram(comps_of(k), scale=1.0, colors=[NEON[i % 6]], width=4)
            dk.scale_to_fit_height(1.4)
            tab.add(dk)
        tab.arrange_in_grid(2, 4, buff=(0.6, 0.4)).move_to(UP * 0.3)
        who = zh("泰特（P. G. Tait）· 十九世纪的扭结表", 30, GOLD).to_edge(DOWN, buff=1.05)
        self.play(LaggedStart(*[Create(k) for k in tab], lag_ratio=0.15), FadeIn(who), run_time=min(3.0, self.D(4)))
        # s5: the three conjectures
        self.at(5)
        self.play(FadeOut(VGroup(tab, who)), run_time=0.4)
        cards = VGroup()
        texts = [("①", "交叉数最少", "约化交错图的交叉数 = 最小交叉数"),
                 ("②", "扭数不变", "同一扭结的约化交错图，扭数相同"),
                 ("③", "翻转猜想", "约化交错图之间可用翻转互相转化")]
        for i, (n, h, b) in enumerate(texts):
            p = panel(3.9, 2.6, NEON[i], 0.06, 0.8)
            tn = mono(n, 40, NEON[i]).next_to(p.get_top(), DOWN, buff=0.25)
            th = zh(h, 34, INK, weight=BOLD).next_to(tn, DOWN, buff=0.15)
            tb = zh(b, 22, DIM)
            if tb.width > 3.5:
                tb.scale_to_fit_width(3.5)
            tb.next_to(th, DOWN, buff=0.3)
            cards.add(VGroup(p, tn, th, tb))
        cards.arrange(RIGHT, buff=0.3).move_to(UP * 0.2)
        seg = self.D(5)
        for i, c in enumerate(cards):
            self.wait_to(self.S(5) + seg * [0.0, 0.3, 0.62][i])
            self.play(FadeIn(c, shift=UP * 0.3), run_time=0.7)
        # flype schematic inside card 3
        self.wait_to(self.S(5) + seg * 0.75)
        box = Square(0.7).set_stroke(GOLD, 3).set_fill(GOLD, 0.1)
        F = Text("F", font=MONO, font_size=34, color=GOLD).move_to(box)
        cr = glyph("A", 0.55, CYAN, frame=False, arrows=False)
        fl = VGroup(cr, VGroup(box, F)).arrange(RIGHT, buff=0.1).move_to(cards[2][0].get_bottom() + UP * 0.55)
        self.play(FadeIn(fl), run_time=0.4)
        self.play(cr.animate.move_to(box.get_center() + RIGHT * 0.65), VGroup(box, F).animate.shift(LEFT * 0.62),
                  Rotate(F, PI, axis=RIGHT), run_time=1.2)
        # s6: reduced diagrams; ~100 years
        self.at(6)
        self.play(FadeOut(VGroup(cards, fl)), run_time=0.4)
        # a nugatory crossing: flip the right lobe over and the crossing disappears
        t = np.linspace(0, TAU_, 360, endpoint=False)
        lem = np.stack([1.6 * np.cos(t), 0.85 * np.sin(2 * t), 0.4 * np.sin(t)], 1)
        th = ValueTracker(0.0)

        def flipped():
            P = lem.copy()
            a_ = th.get_value()
            m = P[:, 0] > 0
            y, z = P[m, 1], P[m, 2]
            w = np.clip(P[m, 0] / 0.5, 0, 1)
            ang = a_ * w
            P[m, 1] = y * np.cos(ang) - z * np.sin(ang)
            P[m, 2] = y * np.sin(ang) + z * np.cos(ang)
            return KnotDiagram([Comp(P)], scale=0.95, shift=LEFT * 3.4 + UP * 0.5, colors=[MAGENTA])

        dn = always_redraw(flipped)
        cut = DashedLine(LEFT * 3.4 + UP * 1.8, LEFT * 3.4 + DOWN * 0.8, dash_length=0.12).set_stroke(GOLD, 3)
        nl = zh("多余的交叉点：一刀可剪开", 28, GOLD).move_to(LEFT * 3.4 + DOWN * 1.4)
        self.play(FadeIn(dn), run_time=0.6)
        self.play(Create(cut), FadeIn(nl), run_time=0.8)
        self.play(th.animate.set_value(PI), run_time=1.6)
        line = Arrow(RIGHT * 0.3 + DOWN * 0.2, RIGHT * 6.3 + DOWN * 0.2, color=DIM, stroke_width=4, buff=0)
        y1 = VGroup(mono("1880s", 30, GOLD), zh("泰特猜想", 26)).arrange(DOWN, buff=0.15).next_to(line.get_start(), UP, buff=0.2).shift(RIGHT * 0.6)
        y2 = VGroup(mono("1984", 30, CYAN), zh("琼斯多项式", 26)).arrange(DOWN, buff=0.15).next_to(line.get_end(), UP, buff=0.2).shift(LEFT * 0.9)
        self.wait_to(self.S(6) + self.D(6) * 0.45)
        self.play(GrowArrow(line), FadeIn(y1), run_time=1.0)
        self.play(FadeIn(y2, shift=LEFT * 0.3), run_time=0.8)
        zz = zh("≈ 100 年", 32, INK).next_to(line, DOWN, buff=0.25)
        self.play(FadeIn(zz), run_time=0.5)
        self.wait_to(self.total - 0.45)
        self.clear_stage(0.4)
        self.finish()
