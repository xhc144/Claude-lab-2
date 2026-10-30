# -*- coding: utf-8 -*-
from common import *
from rect_math import gamma

CARD_TITLES = ["僧人登山", "对跖点温度", "三座房子", "布丰投针", "内接矩形"]
CARD_COLORS = [ORANGE, YELLOW, CYAN, GREEN, MAGENTA]
CARD_X = [-5.3, -2.65, 0, 2.65, 5.3]


def icon(i):
    c = CARD_COLORS[i]
    if i == 0:
        m = Polygon([-0.9, -0.55, 0], [-0.2, 0.6, 0], [0.15, 0.2, 0], [0.4, 0.45, 0], [0.9, -0.55, 0])
        m.set_stroke(PURPLE, 3).set_fill(PURPLE, 0.25)
        path = DashedVMobject(smooth_path([(-0.6, -0.5), (-0.3, -0.25), (-0.45, 0.0), (-0.25, 0.25), (-0.2, 0.55)]).set_stroke(GREY_, 2), num_dashes=12)
        return VGroup(m, path, Dot([-0.42, -0.05, 0], radius=0.06, color=c), Dot([-0.4, -0.35, 0], radius=0.06, color=CYAN))
    if i == 1:
        g = Circle(0.62).set_stroke(BLUE, 3).set_fill("#0E2A6A", 0.8)
        eq = Ellipse(width=1.24, height=0.36).set_stroke(c, 3)
        d = DashedLine([-0.55, -0.08, 0], [0.55, 0.08, 0], color=WHITE_, stroke_width=2)
        return VGroup(g, eq, d, Dot([-0.55, -0.08, 0], radius=0.06, color=ORANGE), Dot([0.55, 0.08, 0], radius=0.06, color=CYAN))
    if i == 2:
        hs = [np.array([x, 0.45, 0]) for x in (-0.6, 0, 0.6)]
        us = [np.array([x, -0.45, 0]) for x in (-0.6, 0, 0.6)]
        cols = [CYAN, YELLOW, ORANGE]
        lines = VGroup(*[Line(h, u, stroke_width=2, color=cols[k]) for h in hs for k, u in enumerate(us)])
        H = VGroup(*[Square(0.2).move_to(h).set_stroke(HOUSE_LIGHT, 2).set_fill(BLACK, 1) for h in hs])
        U = VGroup(*[Circle(0.11).move_to(u).set_stroke(cols[k], 2).set_fill(BLACK, 1) for k, u in enumerate(us)])
        return VGroup(lines, H, U)
    if i == 3:
        ls = VGroup(*[Line([-0.85, y, 0], [0.85, y, 0], stroke_width=2, color=BLUE) for y in (-0.45, 0, 0.45)])
        ns = VGroup(*[Line(np.array([x, y, 0]) - 0.22 * np.array([np.cos(a), np.sin(a), 0]),
                           np.array([x, y, 0]) + 0.22 * np.array([np.cos(a), np.sin(a), 0]), stroke_width=3, color=c)
                      for x, y, a in [(-0.5, 0.2, 0.8), (0.1, -0.15, 2.2), (0.55, 0.3, 0.2), (-0.2, -0.5, 1.4)]])
        return VGroup(ls, ns)
    s = np.linspace(0, 1, 120, endpoint=False)
    P = gamma(s) * 0.25
    cv = VMobject().set_points_smoothly([np.array([p[0], p[1], 0]) for p in P] + [np.array([P[0][0], P[0][1], 0])])
    cv.set_stroke(CYAN, 3)
    from s5_rectangle import X_REP
    from rect_math import rect_from
    R = [np.array([p[0], p[1], 0]) * 0.25 for p in rect_from(X_REP)]
    return VGroup(cv, Polygon(*R).set_stroke(c, 3))


HOUSE_LIGHT = "#C9B6FF"


def card(i, w=2.4, h=2.9):
    c = CARD_COLORS[i]
    box = RoundedRectangle(width=w, height=h, corner_radius=0.18).set_stroke(c, 2.5).set_fill("#0B1030", 0.85)
    num = Text(f"{i + 1:02d}", font=LATIN, font_size=26, color=c, weight=BOLD)
    ic = icon(i)
    ic.scale(min(1.0, 1.7 / max(ic.width, 0.01)))
    ttl = zh(CARD_TITLES[i], 28, WHITE_, weight=BOLD)
    num.move_to(box.get_top() + DOWN * 0.35)
    ic.move_to(box.get_center() + UP * 0.05)
    ttl.move_to(box.get_bottom() + UP * 0.45)
    return VGroup(glow_layers(box, layers=3, spread=4, strength=0.6), box, num, ic, ttl)


def dimmers(cards):
    return VGroup(*[RoundedRectangle(width=c[1].width + 0.1, height=c[1].height + 0.1, corner_radius=0.18)
                    .move_to(c[1]).set_stroke(width=0).set_fill(BLACK, 0.68) for c in cards])


class Intro(NScene):
    script_scene = "Intro"

    def body(self):
        # ---------------- hook：粒子汇聚成曲线
        self.seg("hook")
        rng = np.random.default_rng(3)
        s = np.linspace(0, 1, 160, endpoint=False)
        P = gamma(s) * 0.9
        targets = [np.array([p[0], p[1] + 0.2, 0]) for p in P]
        dots = VGroup(*[Dot(np.array([rng.uniform(-7, 7), rng.uniform(-4, 4), 0]), radius=rng.uniform(0.02, 0.05),
                            color=rng.choice([CYAN, MAGENTA, PURPLE, YELLOW, BLUE])) for _ in targets])
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.004), run_time=1.0)
        self.play(LaggedStart(*[d.animate.move_to(t) for d, t in zip(dots, targets)], lag_ratio=0.004),
                  run_time=2.2, rate_func=smooth)
        curve = VMobject().set_points_smoothly(targets + [targets[0]]).set_stroke(CYAN, 5)
        cg = neon(curve)
        self.play(Create(cg), dots.animate.set_opacity(0), run_time=1.2)
        self.remove(dots)
        circ = Circle(2.3).shift(UP * 0.2).set_stroke(CYAN, 5)
        self.play(Transform(cg, neon(circ)), run_time=1.2)
        q = Text("?", font=LATIN, font_size=220, weight=BOLD, color=MAGENTA).move_to(UP * 0.2)
        qg = glow_text(q, MAGENTA, strength=0.9)
        self.play(FadeIn(qg, scale=0.4), run_time=0.8)
        self.wait_until(self.phrase_at(0, "几乎所有人"))
        self.play(Wiggle(qg, scale_value=1.15), run_time=1.0)
        self.wait_until(self.sent_at(1))
        # 点云：换个角度才看得清
        word = zh("换个角度", 120, WHITE_, weight=BOLD)
        pts = []
        for sub in word.family_members_with_points():
            n = max(8, int(sub.get_arc_length() * 14)) if hasattr(sub, "get_arc_length") else 20
            for a in np.linspace(0, 1, n, endpoint=False):
                pts.append(sub.point_from_proportion(a))
        pts = np.array(pts)
        depth = rng.uniform(-3.5, 3.5, len(pts))
        cloud3 = np.column_stack([pts[:, 0], pts[:, 1], depth])
        cols = [interpolate_color(ManimColor(CYAN), ManimColor(MAGENTA), (p[0] + 3.5) / 7) for p in cloud3]
        ang = ValueTracker(1.25)

        axis = np.array([0.55, 1.0, 0.2])

        def cloud():
            Rm = rotation_matrix(ang.get_value(), axis)
            Q = cloud3 @ Rm.T
            g = VGroup()
            for q, c in zip(Q, cols):
                g.add(Dot([q[0], q[1], 0], radius=0.028, color=c))
            return g

        cl = always_redraw(cloud)
        self.play(FadeOut(qg), FadeOut(cg), FadeIn(cl), run_time=1.0)
        self.play(ang.animate.set_value(0.0), run_time=self.until(self.phrase_at(1, "你想不到", after=True) + 0.4),
                  rate_func=smooth)
        cl.clear_updaters()
        self.play(FadeIn(glow_text(word.copy(), CYAN, strength=0.7)), cl.animate.set_opacity(0.0), run_time=0.8)
        self.remove(cl)
        self.sync(0.2)

        # ---------------- list：标题 + 五张卡片
        self.seg("list")
        for m in list(self.mobjects):
            self.remove(m)
        t1 = zh("第一次做，多半做不出来", 64, weight=BOLD)
        t1.set_color_by_gradient(CYAN, PURPLE, MAGENTA)
        t2 = zh("几何与拓扑中的五道经典难题", 32, GREY_)
        title = VGroup(t1, t2).arrange(DOWN, buff=0.3).move_to(UP * 2.55)
        bar = Line(LEFT * 4, RIGHT * 4, color=CYAN, stroke_width=2).next_to(title, DOWN, buff=0.25)
        self.play(Write(t1), run_time=1.6)
        self.play(FadeIn(t2, shift=UP * 0.2), GrowFromCenter(bar), run_time=0.8)
        cards = VGroup(*[card(i).move_to([CARD_X[i], -0.75, 0]) for i in range(5)])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.5) for c in cards], lag_ratio=0.15), run_time=1.6)
        dims = dimmers(cards)
        self.play(FadeIn(dims), run_time=0.6)
        keys = ["登山的僧人", "地球上的温度", "三座房子的管线", "扔在地上的针", "一条曲线"]
        self.wait_until(self.sent_at(1))
        for i, k in enumerate(keys):
            self.wait_until(self.phrase_at(1, k))
            self.play(FadeOut(dims[i]), cards[i].animate.scale(1.08), run_time=0.45)
            self.play(cards[i].animate.scale(1 / 1.08), run_time=0.3)
        self.sync(0.2)

        # ---------------- pause：先想一想
        self.seg("pause")
        self.play(FadeOut(cards), FadeOut(bar), FadeOut(title), run_time=0.8)
        ring_bg = Circle(0.9).set_stroke(DIM, 8).move_to(UP * 0.0)
        bars = VGroup(Rectangle(width=0.22, height=0.8), Rectangle(width=0.22, height=0.8)).arrange(RIGHT, buff=0.25)
        bars.set_stroke(width=0).set_fill(WHITE_, 1).move_to(ring_bg)
        prog = ValueTracker(0.001)
        ring = always_redraw(lambda: Arc(radius=0.9, start_angle=PI / 2, angle=-TAU * prog.get_value(),
                                         arc_center=ring_bg.get_center(), stroke_width=8, color=YELLOW))
        think = zh("暂停 · 先自己想一想", 34, YELLOW).next_to(ring_bg, RIGHT, buff=0.5)
        grp = VGroup(ring_bg, bars, think)
        VGroup(ring_bg, bars, think).move_to(ORIGIN)
        self.play(FadeIn(ring_bg), FadeIn(bars, scale=0.5), FadeIn(think, shift=LEFT * 0.3), run_time=0.8)
        self.add(ring)
        self.play(prog.animate.set_value(1.0), run_time=self.until(self.sent_at(1)), rate_func=linear)
        ring.clear_updaters()
        self.play(FadeOut(VGroup(grp, ring)), run_time=0.5)
        change = zh("换一个角度", 90, weight=BOLD)
        change.set_color_by_gradient(CYAN, MAGENTA)
        cgl = glow_text(change, PURPLE, strength=0.9)
        self.wait_until(self.phrase_at(1, "换一个角度"))
        self.play(FadeIn(cgl, scale=1.4), run_time=0.8)
        self.wait_until(self.phrase_at(1, "一目了然"))
        self.play(cgl.animate.scale(1.6).set_opacity(0), run_time=1.0, rate_func=rush_into)
        self.sync(0.3)


class Outro(NScene):
    script_scene = "Outro"

    def body(self):
        self.seg("recap")
        head = zh("回顾", 48, weight=BOLD).move_to(UP * 2.8)
        head.set_color_by_gradient(CYAN, MAGENTA)
        cards = VGroup(*[card(i).move_to([CARD_X[i], 0.35, 0]) for i in range(5)])
        self.play(FadeIn(head, shift=DOWN * 0.2), LaggedStart(*[FadeIn(c, shift=UP * 0.4) for c in cards], lag_ratio=0.12),
                  run_time=1.6)
        dims = dimmers(cards)
        self.play(FadeIn(dims), run_time=0.5)
        keys = ["把两天叠成一天", "让直径转过半圈", "用欧拉公式数一数", "把针掰成一个圆", "把一对点变成空间中的一个点"]
        short = ["两天 → 一天", "转过半圈", "欧拉公式", "针 → 圆", "点对 → 空间"]
        tags = VGroup()
        self.wait_until(self.sent_at(1))
        for i, k in enumerate(keys):
            self.wait_until(self.phrase_at(1, k))
            tg = zh(short[i], 28, CARD_COLORS[i], weight=BOLD).next_to(cards[i], DOWN, buff=0.35)
            tags.add(tg)
            self.play(FadeOut(dims[i]), FadeIn(tg, shift=UP * 0.2), run_time=0.6)
        self.sync(0.2)

        self.seg("common")
        self.play(VGroup(cards, tags).animate.scale(0.6).shift(DOWN * 1.75), FadeOut(head), run_time=0.9)
        m1 = zh("答案，不在题目原来的地方", 44, WHITE_)
        m1.move_to(UP * 2.0)
        self.play(FadeIn(m1, shift=UP * 0.2), run_time=0.8)
        self.wait_until(self.sent_at(1))
        m2 = zh("换一个空间看问题", 76, weight=BOLD)
        m2.set_color_by_gradient(CYAN, PURPLE, MAGENTA)
        m2g = glow_text(m2, PURPLE, strength=0.9).move_to(UP * 0.6)
        self.play(FadeIn(m2g, scale=1.3), run_time=1.0)
        self.sync(0.2)

        self.seg("end")
        self.play(FadeOut(VGroup(cards, tags, m1)), m2g.animate.shift(UP * 0.6), run_time=0.8)
        e1 = zh("几何与拓扑的魅力", 40, YELLOW).next_to(m2g, DOWN, buff=0.5)
        self.play(FadeIn(e1, shift=UP * 0.2), run_time=0.8)
        self.wait_until(self.phrase_at(0, "感谢观看"))
        thanks = zh("感谢观看", 34, GREY_).next_to(e1, DOWN, buff=0.6)
        self.play(FadeIn(thanks), run_time=0.8)
        self.sync(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)
