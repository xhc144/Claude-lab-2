# -*- coding: utf-8 -*-
"""开场：粒子汇聚 → 两个向量扫出平行四边形 → ∧ → 标题 → 公式快闪 → 三章路线图。"""
from common import *


MONTAGE = [
    ("莱布尼茨公式", r"\det A=\sum_{\sigma\in S_n}\operatorname{sgn}(\sigma)\,a_{\sigma(1)1}\cdots a_{\sigma(n)n}", CYAN),
    ("乘法公式", r"\det(AB)=\det A\,\det B", MAGENTA),
    ("克莱默法则", r"x_i=\frac{\det A_i}{\det A}", LIME),
    ("柯西–比内公式", r"\det(AB)=\sum_{|S|=m}\det A_{[m],S}\,\det B_{S,[m]}", GOLD),
    ("特征多项式", r"\det(I+tA)=\sum_{k}t^k\operatorname{tr}\Lambda^k\!A", ORANGE),
    ("西尔维斯特恒等式", r"\det(I_m+AB)=\det(I_n+BA)", VIOLET),
    ("普吕克关系", r"p_{12}p_{34}-p_{13}p_{24}+p_{14}p_{23}=0", SKY),
    ("换元公式", r"dx\wedge dy=r\,dr\wedge d\theta", RED),
]


ROAD = {1: "三条规则 · 有向的面积与体积", 2: "体积的伸缩倍数", 3: "直接证明很费劲的恒等式"}


class Intro(BScene):
    def construct(self):
        rng = np.random.default_rng(1)
        # ---- 粒子向中心汇聚 ----
        n = 160
        p0 = np.c_[rng.uniform(-7.5, 7.5, n), rng.uniform(-4.2, 4.2, n), np.zeros(n)]
        cols = [rng.choice([CYAN, MAGENTA, GOLD, VIOLET]) for _ in range(n)]
        sizes = rng.uniform(0.012, 0.04, n)
        s = ValueTracker(0)
        dots = VGroup(*[Dot(p0[i], radius=sizes[i], color=cols[i]) for i in range(n)])

        def upd(g):
            a = s.get_value()
            for i, d in enumerate(g):
                k = 1 - 0.93 * a ** 1.3
                ang = 1.4 * a * (1 + 0.3 * (i % 5))
                q = rotate_vector(p0[i], ang) * k
                d.move_to(q)
                d.set_opacity(min(1, 0.25 + 1.2 * a) * (1 - max(0, a - 0.9) * 10))

        dots.add_updater(upd)
        self.add(dots)
        core = Dot(ORIGIN, radius=0.06, color=WHITE)
        halo = Circle(radius=0.3, stroke_width=0, fill_color=GOLD, fill_opacity=0.25)
        self.play(s.animate.set_value(1), FadeIn(core, scale=0.2), FadeIn(halo), run_time=4, rate_func=smooth)
        dots.clear_updaters()
        self.remove(dots)
        self.hit("hit")
        self.play(ring_pulse(ORIGIN, GOLD, 3.5, run_time=0.9), FadeOut(halo), run_time=0.9)

        # ---- 两个向量扫出平行四边形 ----
        o = np.array([-2.2, -1.4, 0])
        v = np.array([3.8, 0.9, 0])
        w = np.array([1.1, 2.6, 0])
        tv = ValueTracker(0.001)
        tw = ValueTracker(0.001)
        sweep = ValueTracker(0.0)
        fillv = ValueTracker(0.0)
        A = always_redraw(lambda: vec(o, o + v * tv.get_value(), CYAN, width=6))
        B = always_redraw(lambda: vec(o + v * sweep.get_value(), o + v * sweep.get_value() + w * tw.get_value(),
                                      MAGENTA, width=6))
        P = always_redraw(lambda: para(o, v * max(fillv.get_value(), 1e-3), w * tw.get_value(), GOLD,
                                       opacity=0.35, fill=[CYAN, MAGENTA]))
        self.play(core.animate.move_to(o), run_time=0.6)
        self.add(P, A, B)
        self.beat()
        self.play(tv.animate.set_value(1), run_time=0.7, rate_func=rush_from)
        lv = M("v", 48, CYAN).next_to(o + v, DR, buff=0.1)
        self.play(FadeIn(lv), tw.animate.set_value(1), run_time=0.7, rate_func=rush_from)
        lw = M("w", 48, MAGENTA).next_to(o + w, UL, buff=0.1)
        self.play(FadeIn(lw), run_time=0.3)
        self.beat(2)
        self.play(sweep.animate.set_value(1), fillv.animate.set_value(1), run_time=1.5, rate_func=smooth)
        lab = M(r"v\wedge w", 64, GOLD).move_to(o + (v + w) / 2)
        self.play(Write(lab), sweep.animate.set_value(0), run_time=1.0)
        self.beat(4)
        # 平行四边形收缩成一个巨大的 ∧
        wedge = glow(M(r"\wedge", 360, GOLD), GOLD, 6, layers=3, opacity=0.3).move_to(ORIGIN)
        A.clear_updaters()
        B.clear_updaters()
        P.clear_updaters()
        self.hit("impact")
        self.play(ReplacementTransform(VGroup(P, A, B, lab, lv, lw, core), wedge), run_time=0.8, rate_func=rush_into)
        self.play(burst(ORIGIN, GOLD, n=60, radius=4.5, run_time=1.2), ring_pulse(ORIGIN, GOLD, 5, run_time=1.0),
                  wedge.animate.scale(0.92), run_time=1.2)

        # ---- 标题 ----
        self.beat(4)
        title = T("外代数", 130, INK, bold=True)
        en = EN("EXTERIOR  ALGEBRA", 34, CYAN)
        sub = T("一个符号 ∧，改写整本线性代数", 36, MUTED, t2c={"∧": GOLD})
        grp = VGroup(title, en, sub).arrange(DOWN, buff=0.35).shift(DOWN * 0.9)
        floor = RetroGrid()
        self.hit("impact")
        a, gl = glitch(title, run_time=0.7)
        self.play(wedge.animate.scale(0.38).move_to(UP * 2.6), a, run_time=0.7)
        self.remove(gl[0], gl[1])
        self.add(title)
        self.play(FadeIn(en, shift=UP * 0.2), light_sweep(title, run_time=1.0), run_time=1.0)
        self.play(Write(sub), FadeIn(floor), run_time=1.3)
        rule = Line(LEFT * 4, RIGHT * 4, color=CYAN, stroke_width=2).next_to(sub, DOWN, buff=0.35)
        self.play(GrowFromCenter(rule), run_time=0.6)
        self.wait(2.0)
        self.beat(4)
        self.play(FadeOut(VGroup(title, en, sub, rule), shift=DOWN * 0.3), FadeOut(floor), wedge.animate.scale(0.6).move_to(UP * 3.1),
                  run_time=0.7)

        # ---- 公式快闪：每小节一条 ----
        self.beat(4)
        prev = None
        cards = []
        for i, (name, tex, col) in enumerate(MONTAGE):
            f = M(tex, 64, INK)
            if f.width > 11.5:
                f.scale_to_fit_width(11.5)
            lab = T(name, 30, col, bold=True)
            idx = EN(f"{i + 1:02d}/08", 20, col)
            top = VGroup(idx, lab).arrange(RIGHT, buff=0.3)
            card = VGroup(top, f).arrange(DOWN, buff=0.5).move_to(DOWN * 0.1)
            br = brackets(f, color=col, pad=0.35)
            card.add(br)
            cards.append(card)
            self.hit("hit")
            anims = []
            if prev is not None:
                anims.append(FadeOut(prev, shift=LEFT * 0.8, run_time=0.25))
            ga, gg = glitch(f, run_time=0.45, seed=i)
            self.play(*anims, ga, FadeIn(top, shift=RIGHT * 0.3), Create(br), run_time=0.45)
            self.remove(gg[0], gg[1])
            self.add(f)
            self.play(light_sweep(f, color=col, run_time=0.7), run_time=0.7)
            self.beat(4)
            prev = card
        # 全部收进 ∧
        self.hit("impact")
        self.play(FadeOut(prev, scale=0.3, target_position=wedge.get_center()), wedge.animate.scale(1.6).move_to(UP * 0.6),
                  run_time=0.6)
        line = T("它们全部来自同一个运算", 40, INK, bold=True).next_to(wedge, DOWN, buff=0.6)
        self.play(FadeIn(line, shift=UP * 0.2), ring_pulse(wedge.get_center(), GOLD, 3), run_time=1.0)
        self.wait(1.8)
        self.beat(4)

        # ---- 路线图 ----
        self.play(FadeOut(line), wedge.animate.scale(0.5).move_to(UP * 2.4), run_time=0.6)
        nodes = VGroup()
        xs = [-4.6, 0, 4.6]
        for k, x in zip((1, 2, 3), xs):
            title_, en_, sub_ = CHAPTERS[k]
            c = CH_COLORS[k]
            ring = Circle(radius=0.55, color=c, stroke_width=4).move_to([x, 0.2, 0])
            num = EN(f"{k:02d}", 36, c, black=True).move_to(ring)
            t = T(title_, 32, INK, bold=True).next_to(ring, DOWN, buff=0.35)
            st = T(ROAD[k], 22, MUTED).next_to(t, DOWN, buff=0.2)
            nodes.add(VGroup(glow(ring, c, 4, layers=2), num, t, st))
        links = VGroup(*[Line(nodes[i][0].get_right() + RIGHT * 0.1, nodes[i + 1][0].get_left() + LEFT * 0.1,
                              color=DIM, stroke_width=3) for i in range(2)])
        stem = Line(wedge.get_bottom(), nodes[1][0].get_top(), color=DIM, stroke_width=2)
        self.play(Create(stem), run_time=0.4)
        self.beat(2)
        for i, nd in enumerate(nodes):
            self.hit("hit")
            self.play(FadeIn(nd, scale=0.7), *([Create(links[i - 1])] if i else []), run_time=0.6)
            self.beat(4)
        flow = VGroup(*[l.copy().set_stroke(GOLD, 5) for l in links])
        self.play(*[ShowPassingFlash(f, time_width=0.5) for f in flow], run_time=1.0)
        self.wait(1.5)
        self.beat(4)
        self.play(FadeOut(VGroup(nodes, links, stem, wedge)), run_time=0.8)
        self.finish()
