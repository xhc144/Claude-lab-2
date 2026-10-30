# -*- coding: utf-8 -*-
"""尾声：全部结论连回中心的 ∧，回顾三条规则，片尾。"""
from common import *

NODES = [
    ("有向面积", 1), ("k-向量", 1), ("叉积 · 混合积", 1), ("行列式", 2), ("莱布尼茨公式", 2), ("乘法公式", 2),
    ("克莱默法则", 2), ("拉普拉斯展开", 2), ("子式矩阵 Λᵏ A", 3), ("柯西–比内", 3), ("柯西–施瓦茨", 3),
    ("面积的勾股定理", 3), ("特征多项式", 3), ("西尔维斯特", 3), ("普吕克关系", 3), ("斯托克斯定理", 3),
]


class Outro(BScene):
    def construct(self):
        core = glow(M(r"\wedge", 150, GOLD), GOLD, 5, layers=3, opacity=0.3)
        ring = Circle(radius=0.95, color=GOLD, stroke_width=3)
        center = VGroup(ring, core)
        self.hit("impact")
        self.play(FadeIn(core, scale=0.5), Create(ring), ring_pulse(ORIGIN, GOLD, 3), run_time=1.0)
        n = len(NODES)
        nodes, links = VGroup(), VGroup()
        for k, (name, ch) in enumerate(NODES):
            a = PI / 2 - TAU * k / n
            p = np.array([4.5 * math.cos(a), 2.9 * math.sin(a), 0])
            c = CH_COLORS[ch]
            t = T(name, 22, INK, bold=True)
            dot = Dot(p, radius=0.07, color=c)
            t.next_to(dot, normalize(p) * np.array([1, 1, 0]), buff=0.12)
            if abs(p[0]) < 0.5:
                t.next_to(dot, UP if p[1] > 0 else DOWN, buff=0.12)
            nodes.add(VGroup(dot, t))
            links.add(Line(normalize(p) * 0.98, p, color=c, stroke_width=2, stroke_opacity=0.7))
        self.beat(4)
        for k in range(n):
            if k % 2 == 0:
                self.hit()
            self.play(Create(links[k]), FadeIn(nodes[k], scale=0.6), run_time=BEAT * 0.98)
        self.beat(4)
        flows = VGroup(*[l.copy().set_stroke(GOLD, 6, opacity=1) for l in links])
        self.hit("impact")
        self.play(*[ShowPassingFlash(f.reverse_direction(), time_width=0.5) for f in flows],
                  ring_pulse(ORIGIN, GOLD, 2.5), run_time=1.2)
        self.play(*[ShowPassingFlash(f.copy(), time_width=0.5) for f in flows], run_time=1.2)
        self.wait(1.5)
        self.beat(4)

        # 三条规则
        self.play(FadeOut(VGroup(nodes, links)), center.animate.scale(0.6).move_to(UP * 2.3), run_time=0.8)
        rules = VGroup(
            VGroup(EN("01", 30, CYAN), T("双线性", 34, CYAN, bold=True)).arrange(RIGHT, buff=0.3),
            VGroup(EN("02", 30, MAGENTA), T("结合律", 34, MAGENTA, bold=True)).arrange(RIGHT, buff=0.3),
            VGroup(EN("03", 30, GOLD), M(r"v\wedge v=0", 48, GOLD)).arrange(RIGHT, buff=0.3),
        ).arrange(RIGHT, buff=1.2).move_to(UP * 0.4)
        for r in rules:
            self.hit()
            self.play(FadeIn(r, shift=UP * 0.3), run_time=0.6)
            self.beat(2)
        line = T("三条规则。剩下的一切——行列式、它的所有性质、", 34, INK)
        line2 = T("还有那些直接证明很费劲的恒等式——都是推论。", 34, INK)
        lines = VGroup(line, line2).arrange(DOWN, buff=0.25).move_to(DOWN * 1.4)
        self.play(Write(line), run_time=1.4)
        self.play(Write(line2), run_time=1.4)
        self.wait(3.0)
        self.beat(4)
        self.play(FadeOut(VGroup(rules, lines)), FadeOut(center), run_time=0.8)

        # 片尾
        self.beat(4)
        floor = RetroGrid()
        title = T("外代数", 110, INK, bold=True)
        en = EN("EXTERIOR  ALGEBRA", 32, CYAN)
        sub = T("与它在线性代数中的应用", 34, MUTED)
        g = VGroup(title, en, sub).arrange(DOWN, buff=0.3).shift(UP * 0.9)
        w = glow(M(r"\wedge", 120, GOLD), GOLD, 5, layers=2, opacity=0.3).next_to(g, UP, buff=0.3)
        self.hit("impact")
        a, gl = glitch(title, run_time=0.7)
        self.play(a, FadeIn(floor), FadeIn(w, scale=0.6), run_time=0.7)
        self.remove(gl[0], gl[1])
        self.add(title)
        self.play(FadeIn(en, shift=UP * 0.2), light_sweep(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.8)
        end = EN("THE  END", 26, MAGENTA).to_edge(DOWN, buff=0.6)
        self.wait(2.0)
        self.play(FadeIn(end), run_time=0.8)
        self.wait(3.5)
        self.beat(4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=2.0)
        self.wait(1.0)
        self.finish()
