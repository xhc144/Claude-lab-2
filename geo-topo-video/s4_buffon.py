# -*- coding: utf-8 -*-
from common import *

D = 1.3          # 平行线间距
L = 1.0          # 针长
YS = [k * D for k in range(-2, 3)]
NEEDLE_C = "#9EEBFF"


def floor_lines(x0=-7.3, x1=7.3, ys=YS, col=BLUE):
    g = VGroup()
    planks = VGroup()
    for i in range(len(ys) - 1):
        planks.add(Rectangle(width=x1 - x0, height=ys[i + 1] - ys[i]).move_to([(x0 + x1) / 2, (ys[i] + ys[i + 1]) / 2, 0])
                   .set_stroke(width=0).set_fill("#0B1132" if i % 2 else "#080C26", 1))
    for y in ys:
        ln = Line([x0, y, 0], [x1, y, 0], stroke_width=3, color=col)
        g.add(VGroup(glow_layers(ln, layers=2, spread=4, strength=0.6), ln))
    return planks, g


def needle(center, theta, length=L, col=NEEDLE_C, width=5):
    d = np.array([np.cos(theta), np.sin(theta), 0]) * length / 2
    ln = Line(center - d, center + d, stroke_width=width, color=col)
    eye = Circle(0.04, color=col, stroke_width=2).move_to(center + d * 0.86)
    return VGroup(glow_layers(ln, layers=2, spread=4, strength=0.7), ln, eye)


def crossings_segment(p, q, ys=YS):
    out = []
    for y in ys:
        if (p[1] - y) * (q[1] - y) < 0:
            t = (y - p[1]) / (q[1] - p[1])
            out.append(p + t * (q - p))
    return out


def crossings_curve(m, ys=YS, n=400):
    pts = [m.point_from_proportion(a) for a in np.linspace(0, 1, n)]
    out = []
    for i in range(len(pts) - 1):
        out += crossings_segment(pts[i], pts[i + 1], ys)
    return out


def hit_dots(points, col=GREEN):
    return VGroup(*[glow_dot(p, col, 0.07, 3) for p in points])


def reuleaux(width=D, center=ORIGIN, angle=0.0):
    r = width / np.sqrt(3)
    vs = [center + r * np.array([np.cos(angle + PI / 2 + k * TAU / 3), np.sin(angle + PI / 2 + k * TAU / 3), 0])
          for k in range(3)]
    m = VMobject()
    for k in range(3):
        a, b = vs[k], vs[(k + 1) % 3]
        c = vs[(k + 2) % 3]
        arc = ArcBetweenPoints(a, b, angle=PI / 3)
        # ArcBetweenPoints 的弧心应在 c 一侧：通过方向检查
        if np.linalg.norm(arc.point_from_proportion(0.5) - c) < width * 0.99:
            arc = ArcBetweenPoints(a, b, angle=-PI / 3)
        if k == 0:
            m.set_points(arc.get_points())
        else:
            m.append_points(arc.get_points())
    return m


class Buffon(NScene):
    script_scene = "Buffon"

    def body(self):
        self.chapter(4, "布丰投针", "Buffon's Needle")
        self.show_corner()

        # ---------------- setup
        self.seg("setup")
        who = VGroup(zh("布丰", 52, WHITE_, weight=BOLD), en("Georges-Louis Leclerc, Comte de Buffon", 26),
                     en("1707 – 1788", 26, CYAN)).arrange(DOWN, buff=0.2)
        self.play(FadeIn(who, shift=UP * 0.3), run_time=1.0)
        self.wait_until(self.sent_at(1))
        planks, lines = floor_lines()
        self.play(FadeOut(who), FadeIn(planks), LaggedStart(*[Create(l) for l in lines], lag_ratio=0.12),
                  run_time=1.4)
        br = BraceBetweenPoints([5.6, YS[3], 0], [5.6, YS[2], 0], direction=RIGHT, color=YELLOW)
        dl = MathTex("d", font_size=48, color=YELLOW).next_to(br, RIGHT, buff=0.12)
        self.wait_until(self.phrase_at(1, "间距是"))
        self.play(GrowFromCenter(br), FadeIn(dl), run_time=0.7)
        self.wait_until(self.phrase_at(1, "随手往地上"))
        n1 = needle(np.array([-1.8, 0.75, 0]), 0.6)
        n1_start = n1.copy().scale(2.4).rotate(3.2).shift(UP * 2.5 + LEFT * 1.5).set_opacity(0)
        self.play(Transform(n1_start, n1), run_time=0.9, rate_func=rush_into)
        self.remove(n1_start)
        self.add(n1)
        bl = BraceBetweenPoints(n1[1].get_start(), n1[1].get_end(), direction=rotate_vector(UP, 0.6), color=CYAN)
        ll = MathTex("l", font_size=44, color=CYAN).next_to(bl.get_center(), rotate_vector(UP, 0.6), buff=0.35)
        self.play(GrowFromCenter(bl), FadeIn(ll), run_time=0.7)
        cond = MathTex(r"l \le d", font_size=44, color=WHITE_).move_to([4.6, 2.3, 0])
        self.wait_until(self.phrase_at(1, "不超过"))
        self.play(Write(cond), run_time=0.7)
        self.wait_until(self.sent_at(2))
        self.play(FadeOut(bl), FadeOut(ll), run_time=0.3)
        thrown = VGroup()
        specs = [((-1.8, 0.75), 0.6), ((1.2, -0.6), 2.1), ((-4.5, -1.6), 1.2), ((3.4, 0.2), 0.15)]
        anims = []
        hits = VGroup()
        for (x, y), th in specs[1:]:
            nd = needle(np.array([x, y, 0]), th)
            thrown.add(nd)
            anims.append(FadeIn(nd, scale=1.8, rate_func=rush_into))
        self.play(LaggedStart(*anims, lag_ratio=0.25), run_time=1.2)
        for nd in [n1, *thrown]:
            hits.add(hit_dots(crossings_segment(nd[1].get_start(), nd[1].get_end())))
        qbox = panel(4.2, 1.1, color=MAGENTA).move_to([-4.6, 2.85, 0])
        qtxt = VGroup(MathTex("P(", font_size=46), zh("相交", 32), MathTex(") = ?", font_size=46)).arrange(RIGHT, buff=0.08).move_to(qbox)
        self.play(LaggedStart(*[FadeIn(h, scale=2) for h in hits], lag_ratio=0.2), FadeIn(qbox), FadeIn(qtxt), run_time=1.2)
        self.sync(0.2)

        # ---------------- answer
        self.seg("answer")
        ans = MathTex("P", "=", r"\frac{2l}{", r"\pi", r"d}", font_size=96)
        ans[3].set_color(YELLOW)
        ans_bg = panel(4.4, 2.4, color=YELLOW).move_to([0, 0.2, 0])
        ans.move_to(ans_bg)
        dim = Rectangle(width=14.2, height=8).set_fill(BLACK, 0.6).set_stroke(width=0)
        self.play(FadeIn(dim), FadeIn(ans_bg), Write(ans), run_time=1.4)
        self.wait_until(self.phrase_at(0, "竟然算出了"))
        self.play(burst(ans[3].get_center(), YELLOW, r1=1.1), Indicate(ans[3], color=YELLOW, scale_factor=1.6),
                  run_time=1.0)
        self.sync(0.1)

        # ---------------- standard：积分解法
        self.seg("standard")
        integ = MathTex(r"P=\frac{1}{\pi}\int_0^{\pi}\frac{l\sin\theta}{d}\,d\theta=\frac{2l}{\pi d}", font_size=60)
        integ.move_to([0, 0.2, 0])
        tag = zh("标准解法：对角度和位置积分", 28, GREY_).next_to(integ, UP, buff=0.5)
        self.play(FadeOut(VGroup(ans_bg, ans)), FadeIn(integ, shift=UP * 0.2), FadeIn(tag), run_time=1.0)
        self.wait_until(self.phrase_at(0, "但这里"))
        better = zh("更漂亮的证明 →", 40, CYAN, weight=BOLD).next_to(integ, DOWN, buff=0.6)
        self.play(integ.animate.set_opacity(0.25), tag.animate.set_opacity(0.25), FadeIn(better, shift=RIGHT * 0.4),
                  run_time=1.0)
        self.sync(0.1)

        # ---------------- expect：平均交点数
        self.seg("expect")
        self.play(FadeOut(VGroup(integ, tag, better, dim, qbox, qtxt, cond)), run_time=0.6)
        Edef = VGroup(MathTex("E", "=", font_size=56).set_color_by_tex("E", YELLOW), zh("平均交点数", 36, YELLOW))
        Edef.arrange(RIGHT, buff=0.15)
        Ebox = panel(Edef.width + 0.7, 1.1, color=YELLOW).move_to([-4.3, 2.85, 0])
        Edef.move_to(Ebox)
        self.play(FadeIn(Ebox), Write(Edef), run_time=1.0)
        cnt_labs = VGroup()
        for nd in [n1, *thrown]:
            k = len(crossings_segment(nd[1].get_start(), nd[1].get_end()))
            cnt_labs.add(MathTex(str(k), font_size=36, color=GREEN if k else GREY_).next_to(nd, UP, buff=0.05))
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cnt_labs], lag_ratio=0.15), run_time=1.0)
        self.sync(0.1)

        # ---------------- additive：期望可加
        self.seg("additive")
        self.play(FadeOut(VGroup(n1, thrown, hits, cnt_labs)), run_time=0.6)
        c0 = np.array([0.3, 0.55, 0])
        th = 0.95
        dvec = np.array([np.cos(th), np.sin(th), 0])
        a_len = 1.3
        pA, pM, pB = c0 - dvec * a_len, c0, c0 + dvec * a_len
        segA = Line(pA, pM, stroke_width=7, color=CYAN)
        segB = Line(pM, pB, stroke_width=7, color=MAGENTA)
        long_n = VGroup(neon(segA), neon(segB))
        self.play(FadeIn(long_n, scale=1.5, rate_func=rush_into), run_time=0.8)
        hA = hit_dots(crossings_segment(pA, pM), CYAN)
        hB = hit_dots(crossings_segment(pM, pB), MAGENTA)
        self.play(FadeIn(hA, scale=2), FadeIn(hB, scale=2), run_time=0.6)
        eq_add = MathTex("E(", "a", "+", "b", ")", "=", "E(", "a", ")", "+", "E(", "b", ")", font_size=54)
        for i in (1, 7):
            eq_add[i].set_color(CYAN)
        for i in (3, 11):
            eq_add[i].set_color(MAGENTA)
        eq_box = panel(eq_add.width + 0.7, 1.1, color=PURPLE).move_to([3.6, 2.85, 0])
        eq_add.move_to(eq_box)
        self.wait_until(self.phrase_at(0, "期望总是可以相加"))
        self.play(FadeIn(eq_box), Write(eq_add), run_time=1.4)
        # 随机再扔两次，演示总是"两段之和"
        for k, (cc, tt) in enumerate([((-3.0, -0.9), 2.3), ((3.8, -1.0), 0.3)]):
            cc = np.array([cc[0], cc[1], 0])
            dv = np.array([np.cos(tt), np.sin(tt), 0])
            a1, m1, b1 = cc - dv * a_len, cc, cc + dv * a_len
            g = VGroup(neon(Line(a1, m1, stroke_width=7, color=CYAN)), neon(Line(m1, b1, stroke_width=7, color=MAGENTA)))
            h = VGroup(hit_dots(crossings_segment(a1, m1), CYAN), hit_dots(crossings_segment(m1, b1), MAGENTA))
            self.play(FadeIn(g, scale=1.5, rate_func=rush_into), run_time=0.6)
            self.play(FadeIn(h, scale=2), run_time=0.4)
            long_n.add(g)
            hA.add(h)
        self.wait_until(self.sent_at(1))
        lin = MathTex("E(l)", "=", "c", r"\cdot", "l", font_size=72)
        lin[2].set_color(YELLOW)
        lin_box = panel(lin.width + 1.0, 1.5, color=YELLOW).move_to([0, 0.3, 0])
        lin.move_to(lin_box)
        dim2 = Rectangle(width=14.2, height=8).set_fill(BLACK, 0.6).set_stroke(width=0)
        self.play(FadeIn(dim2), FadeIn(lin_box), Write(lin), run_time=1.2)
        cnote = zh("c 是某个常数", 28, GREY_).next_to(lin_box, DOWN, buff=0.3)
        self.play(FadeIn(cnote), Indicate(lin[2], color=YELLOW, scale_factor=1.5), run_time=1.0)
        self.sync(0.1)

        # ---------------- bend：把针掰弯
        self.seg("bend")
        self.play(FadeOut(VGroup(long_n, hA, hB, dim2, cnote, eq_box, eq_add, Ebox, Edef)),
                  VGroup(lin_box, lin).animate.scale(0.7).move_to([4.6, 2.85, 0]), run_time=0.8)
        straight = Line([-2.2, 0.3, 0], [2.2, 0.3, 0], stroke_width=7, color=NEEDLE_C)
        st_g = neon(straight)
        self.play(FadeIn(st_g, scale=1.2), run_time=0.6)
        noodle_pts = [(-2.0, 0.9), (-1.3, -0.2), (-0.3, 0.6), (0.2, 1.5), (1.0, 0.4), (1.6, -0.6), (2.3, 0.5)]
        noodle = smooth_path(noodle_pts).set_stroke(ORANGE, 7)
        nd_g = neon(noodle)
        self.play(Transform(st_g, nd_g), run_time=1.6)
        self.wait_until(self.sent_at(1))
        pieces = VGroup()
        N_P = 14
        props = np.linspace(0, 1, N_P + 1)
        for i in range(N_P):
            pieces.add(Line(noodle.point_from_proportion(props[i]), noodle.point_from_proportion(props[i + 1]),
                            stroke_width=7, color=[CYAN, MAGENTA][i % 2]))
        ticks = VGroup(*[Dot(noodle.point_from_proportion(p), radius=0.05, color=WHITE_) for p in props])
        self.play(FadeOut(st_g), LaggedStart(*[Create(p) for p in pieces], lag_ratio=0.08), FadeIn(ticks), run_time=1.8)
        contrib = MathTex(r"c\cdot\Delta l", font_size=36, color=YELLOW)
        contribs = VGroup(*[contrib.copy().next_to(pieces[i], UP, buff=0.08) for i in [2, 6, 10]])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in contribs], lag_ratio=0.3), run_time=1.2)
        self.wait_until(self.sent_at(2))
        EL = MathTex("E", "=", "c", r"\cdot", "L", font_size=72)
        EL[2].set_color(YELLOW)
        EL[4].set_color(ORANGE)
        EL_box = panel(EL.width + 1.0, 1.5, color=ORANGE).move_to([-4.3, 2.55, 0])
        EL.move_to(EL_box)
        self.play(FadeOut(contribs), FadeIn(EL_box), Write(EL), run_time=1.0)
        # 扔几根不同形状的面条
        shapes = [
            [(-5.8, -0.4), (-5.0, 0.9), (-4.2, -0.1), (-3.6, 1.1)],
            [(3.2, -1.9), (4.0, -0.9), (5.4, -1.6), (5.9, -0.3), (4.8, 0.4)],
            [(-2.6, -2.2), (-1.4, -1.4), (-0.4, -2.4), (0.8, -1.7)],
        ]
        nds, hts = VGroup(), VGroup()
        for i, sp in enumerate(shapes):
            m = smooth_path(sp).set_stroke([ORANGE, PINK, GREEN][i], 6)
            nds.add(neon(m, strength=0.7))
            hts.add(hit_dots(crossings_curve(m), YELLOW))
        self.play(FadeOut(pieces), FadeOut(ticks),
                  LaggedStart(*[FadeIn(n, scale=1.4, rate_func=rush_into) for n in nds], lag_ratio=0.3),
                  run_time=1.6)
        self.play(LaggedStart(*[FadeIn(h, scale=2) for h in hts], lag_ratio=0.2), run_time=1.0)
        self.sync(0.1)

        # ---------------- circle：直径为 d 的圆
        self.seg("circle")
        self.play(FadeOut(nds), FadeOut(hts), FadeOut(VGroup(lin_box, lin)), run_time=0.6)
        cpos = ValueTracker(0.0)
        path_pts = [np.array([0.0, YS[2] + D / 2, 0]), np.array([-3.5, 0.9, 0]), np.array([2.8, -1.1, 0]),
                    np.array([-1.0, -0.15, 0]), np.array([4.5, 1.6, 0]), np.array([0.6, 0.35, 0])]

        def cpos_at(t):
            k = min(int(t), len(path_pts) - 2)
            a = smooth(t - k)
            return path_pts[k] * (1 - a) + path_pts[k + 1] * a

        circ = always_redraw(lambda: neon(Circle(D / 2, color=GREEN, stroke_width=6).move_to(cpos_at(cpos.get_value()))))

        def circ_hits():
            c = cpos_at(cpos.get_value())
            pts = []
            for y in YS:
                dy = y - c[1]
                if abs(dy) < D / 2:
                    w = np.sqrt((D / 2) ** 2 - dy ** 2)
                    pts += [c + np.array([-w, dy, 0]), c + np.array([w, dy, 0])]
            return hit_dots(pts, YELLOW)

        chits = always_redraw(circ_hits)
        diam = DoubleArrow(path_pts[0] + DOWN * D / 2, path_pts[0] + UP * D / 2, buff=0, color=WHITE_,
                           stroke_width=3, tip_length=0.15)
        dlab = MathTex("d", font_size=40).next_to(diam, RIGHT, buff=0.1)
        self.play(Create(circ), run_time=1.0)
        self.play(GrowFromCenter(diam), FadeIn(dlab), run_time=0.6)
        self.wait_until(self.sent_at(1))
        cnt = VGroup(zh("交点数", 30, GREY_), Integer(2, font_size=48, color=YELLOW)).arrange(RIGHT, buff=0.2)
        cbox = panel(cnt.width + 0.6, 1.0, color=YELLOW).move_to([4.8, 2.75, 0])
        cnt.move_to(cbox)
        self.play(FadeOut(diam), FadeOut(dlab), FadeIn(chits), FadeIn(cbox), FadeIn(cnt), run_time=0.6)
        self.play(cpos.animate.set_value(len(path_pts) - 1), run_time=self.remaining(-0.4), rate_func=linear)
        self.sync(0.1)

        # ---------------- solve
        self.seg("solve")
        circ.clear_updaters()
        chits.clear_updaters()
        self.play(FadeOut(chits), FadeOut(cbox), FadeOut(cnt), FadeOut(EL_box), FadeOut(EL), run_time=0.5)
        c_now = cpos_at(len(path_pts) - 1)
        unroll = Line(c_now + LEFT * PI * D / 2 + DOWN * 0, c_now + RIGHT * PI * D / 2, color=GREEN, stroke_width=6)
        pid = MathTex(r"\pi d", font_size=44, color=GREEN).next_to(unroll, UP, buff=0.15)
        circ_core = circ[1].copy()
        self.remove(circ)
        self.add(circ_core)
        self.play(Transform(circ_core, unroll), run_time=1.4)
        self.play(FadeIn(pid), run_time=0.4)
        dim3 = Rectangle(width=14.2, height=8).set_fill(BLACK, 0.7).set_stroke(width=0)
        s1 = MathTex("c", r"\cdot", r"\pi d", "=", "2", font_size=64)
        s1[0].set_color(YELLOW)
        s1[2].set_color(GREEN)
        s2 = MathTex(r"\Rightarrow\ c", "=", r"\frac{2}{\pi d}", font_size=64)
        s2[0].set_color(YELLOW)
        col1 = VGroup(s1, s2).arrange(RIGHT, buff=0.6).move_to([0, 1.3, 0])
        self.wait_until(self.phrase_at(0, "所以"))
        self.play(FadeIn(dim3), Write(s1), run_time=1.0)
        self.wait_until(self.phrase_at(0, "也就是"))
        self.play(Write(s2), run_time=1.0)
        self.wait_until(self.sent_at(1))
        at_most = VGroup(zh("针长", 30), MathTex(r"l\le d", font_size=44), zh("⇒ 最多交 1 次 ⇒", 30),
                         MathTex("E", "=", "P", font_size=48)).arrange(RIGHT, buff=0.2).move_to([0, -0.1, 0])
        self.play(FadeIn(at_most, shift=UP * 0.2), run_time=1.0)
        self.wait_until(self.phrase_at(1, "相交的概率"))
        final = MathTex("P", "=", "c", r"\cdot", "l", "=", r"\frac{2l}{\pi d}", font_size=80)
        final[6].set_color(YELLOW)
        fbox = panel(final.width + 1.0, final.height + 0.6, color=YELLOW).move_to([0, -1.75, 0])
        final.move_to(fbox)
        self.play(FadeIn(fbox), Write(final), run_time=1.2)
        self.play(Circumscribe(final, color=YELLOW), run_time=1.0)
        self.sync(0.2)

        # ---------------- sim：蒙特卡洛
        self.seg("sim")
        self.play(FadeOut(VGroup(dim3, s1, s2, at_most, fbox, final, circ_core, pid)), run_time=0.6)
        rng = np.random.default_rng(SIM_SEED)
        NT = 1600
        cx = rng.uniform(-7.0, 7.0, NT)
        cy = rng.uniform(YS[0], YS[-1], NT)
        th = rng.uniform(0, PI, NT)
        hit = np.floor((cy - L / 2 * np.sin(th)) / D) != np.floor((cy + L / 2 * np.sin(th)) / D)
        needles = []
        for i in range(NT):
            d = np.array([np.cos(th[i]), np.sin(th[i]), 0]) * L / 2
            c = np.array([cx[i], cy[i], 0])
            needles.append(Line(c - d, c + d, stroke_width=2.2,
                                color=GREEN if hit[i] else "#5A6AA8", stroke_opacity=1 if hit[i] else 0.5))
        shown = VGroup()
        ntr = ValueTracker(0)

        def add_needles(g):
            n = int(ntr.get_value())
            if n > len(g):
                g.add(*needles[len(g):n])

        shown.add_updater(add_needles)
        box = panel(3.6, 2.5, color=CYAN).move_to([5.05, 2.15, 0]).set_z_index(10)
        box[1].set_fill("#070B22", 0.97)
        nN = Integer(0, font_size=40, color=WHITE_, group_with_commas=False)
        nH = Integer(0, font_size=40, color=GREEN, group_with_commas=False)
        est = DecimalNumber(0, num_decimal_places=4, font_size=48, color=YELLOW)
        lab1, lab2 = zh("投针", 28, GREY_), zh("相交", 28, GREY_)
        labp = MathTex(r"\pi\approx", font_size=48, color=YELLOW)
        labs = VGroup(lab1, lab2, labp).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        labs.move_to(box).shift(LEFT * 0.85)
        stats = VGroup(labs, nN, nH, est).set_z_index(11)

        def place():
            nN.next_to(lab1, RIGHT, buff=0.3)
            nH.next_to(lab2, RIGHT, buff=0.3)
            est.next_to(labp, RIGHT, buff=0.2)

        place()

        def upd_stats(m):
            n = int(ntr.get_value())
            h = int(hit[:n].sum())
            nN.set_value(n)
            nH.set_value(h)
            if h > 0:
                est.set_value(2 * L * n / (D * h))
            place()
            for mob in (nN, nH, est):
                mob.set_z_index(11)

        stats.add_updater(upd_stats)
        r3 = VGroup(labp, est)
        self.play(FadeOut(br), FadeOut(dl), run_time=0.3)
        self.add(shown)
        self.play(FadeIn(box), FadeIn(stats), run_time=0.5)
        T_sim = self.remaining(2.5)
        self.play(ntr.animate.set_value(NT), run_time=T_sim, rate_func=lambda t: t ** 2.2)
        stats.clear_updaters()
        shown.clear_updaters()
        true_pi = MathTex(r"\pi = 3.14159\ldots", font_size=40, color=GREY_).next_to(box, DOWN, buff=0.2).set_z_index(11)
        true_bg = BackgroundRectangle(true_pi, color=BLACK, fill_opacity=0.85, buff=0.12).set_z_index(10)
        self.play(FadeIn(true_bg), FadeIn(true_pi), Circumscribe(r3, color=YELLOW), run_time=1.2)
        self.sync(0.3)

        # ---------------- reuleaux：等宽曲线
        self.seg("reuleaux")
        self.play(FadeOut(VGroup(shown, box, stats, true_pi, true_bg, planks, lines)), run_time=0.8)
        W = 2.4
        yb, yt = -1.2, 1.2
        rails = VGroup(*[neon(Line([-7.2, y, 0], [7.2, y, 0], color=BLUE, stroke_width=4)) for y in (yb, yt)])
        self.play(Create(rails), run_time=0.8)
        rot = ValueTracker(0.0)

        def rolling_shape():
            a = rot.get_value()
            m = reuleaux(W, ORIGIN, a)
            pts = m.get_points()
            m.shift(UP * (yb - pts[:, 1].min()))
            m.shift(RIGHT * (-4.5 + 1.5 * a))
            m.set_stroke(MAGENTA, 6).set_fill(MAGENTA, 0.12)
            return neon(m)

        rshape = always_redraw(rolling_shape)
        wlab = always_redraw(lambda: VGroup(
            DoubleArrow([rshape[1].get_center()[0] + 1.6, yb, 0], [rshape[1].get_center()[0] + 1.6, yt, 0],
                        buff=0, color=YELLOW, stroke_width=3, tip_length=0.18),
            MathTex("d", font_size=40, color=YELLOW).move_to([rshape[1].get_center()[0] + 1.9, 0, 0])))
        self.play(FadeIn(rshape), FadeIn(wlab), run_time=0.8)
        name = VGroup(zh("勒洛三角形", 36, MAGENTA, weight=BOLD), en("Reuleaux triangle", 24)).arrange(RIGHT, buff=0.25)
        name.move_to([0, 2.4, 0])
        self.play(FadeIn(name, shift=DOWN * 0.2), run_time=0.6)
        self.play(rot.animate.set_value(6.0), run_time=self.remaining(-0.3), rate_func=linear)
        self.sync(0.1)

        # ---------------- barbier
        self.seg("barbier")
        rshape.clear_updaters()
        wlab.clear_updaters()
        self.play(FadeOut(rails), FadeOut(rshape), FadeOut(wlab), FadeOut(name), run_time=0.6)
        planks, lines = floor_lines()
        self.play(FadeIn(planks), FadeIn(lines), run_time=0.6)
        rs, rh = VGroup(), VGroup()
        for (x, y), a in [((-4.6, 0.35), 0.3), ((-1.4, -1.25), 1.2), ((1.9, 0.8), 2.0), ((5.0, -0.6), 0.7)]:
            m = reuleaux(D, np.array([x, y, 0]), a).set_stroke(MAGENTA, 5).set_fill(MAGENTA, 0.1)
            rs.add(neon(m))
            rh.add(hit_dots(crossings_curve(m), YELLOW))
        self.play(LaggedStart(*[FadeIn(r, scale=1.6, rate_func=rush_into) for r in rs], lag_ratio=0.25), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(h, scale=2) for h in rh], lag_ratio=0.2), run_time=1.0)
        two = VGroup(zh("每次都恰好交", 30), MathTex("2", font_size=52, color=YELLOW), zh("次", 30)).arrange(RIGHT, buff=0.12)
        tbox = panel(two.width + 0.6, 1.0, color=YELLOW).move_to([4.6, 2.75, 0])
        two.move_to(tbox)
        self.play(FadeIn(tbox), FadeIn(two), run_time=0.6)
        self.wait_until(self.sent_at(1))
        dim4 = Rectangle(width=14.2, height=8).set_fill(BLACK, 0.75).set_stroke(width=0)
        r_big = reuleaux(1.9, np.array([-2.6, 1.0, 0]), 0).set_stroke(MAGENTA, 6)
        c_big = Circle(0.95, color=GREEN, stroke_width=6).move_to([2.6, 1.0, 0]).rotate(-PI / 2)
        self.play(FadeIn(dim4), FadeOut(tbox), FadeOut(two), Create(r_big), Create(c_big), run_time=1.2)
        lr = Line([-PI * 1.9 / 2, -0.9, 0], [PI * 1.9 / 2, -0.9, 0], color=MAGENTA, stroke_width=7)
        lc = Line([-PI * 1.9 / 2, -1.5, 0], [PI * 1.9 / 2, -1.5, 0], color=GREEN, stroke_width=7)
        self.play(Transform(r_big.copy(), lr), Transform(c_big.copy(), lc), run_time=1.8)
        eqL = MathTex(r"=\ \pi d", font_size=56, color=YELLOW).next_to(VGroup(lr, lc), RIGHT, buff=0.4)
        self.play(Write(eqL), run_time=0.8)
        thm = VGroup(zh("巴比耶定理", 40, YELLOW, weight=BOLD), en("Barbier, 1860", 26)).arrange(RIGHT, buff=0.3)
        thm.move_to([0, 2.75, 0])
        self.wait_until(self.phrase_at(1, "这就是"))
        self.play(FadeIn(thm, shift=DOWN * 0.2), run_time=0.8)
        self.sync(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)


SIM_SEED = 274
