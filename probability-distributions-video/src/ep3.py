# -*- coding: utf-8 -*-
"""第 3 集：等待第一次成功——几何分布与负二项分布。"""
from common import *  # noqa: F401,F403

EP = 3
P = 0.3


def shot(hit, r=0.32):
    c = Circle(radius=r, fill_color=tint(GOLD, 0.7), fill_opacity=1, stroke_color=GOLD, stroke_width=3)
    mark = (Text("✓", font_size=int(r * 100), color=TEAL) if hit else Text("✗", font_size=int(r * 100), color=BRICK))
    return VGroup(c, mark.move_to(c))


def strip_pieces(width=12.0, height=0.6, p=P, n=9, left=-6.0, y=0.0):
    """长度为 1 的纸条按几何级数切开：第 k 段长度 p(1-p)^{k-1}。返回 (各段, 剩余尾巴)。"""
    pieces = VGroup()
    x = left
    rem = 1.0
    for k in range(n):
        w = rem * p * width
        col = TEAL if k % 2 == 0 else interpolate_color(ManimColor(TEAL), ManimColor(INDIGO), 0.45)
        r = Rectangle(width=w, height=height, fill_color=tint(col, 0.65), fill_opacity=1, stroke_color=BG,
                      stroke_width=2)
        r.move_to([x + w / 2, y, 0])
        pieces.add(r)
        x += w
        rem *= 1 - p
    tail = Rectangle(width=rem * width, height=height, fill_color=tint(TEAL, 0.25), fill_opacity=1, stroke_color=BG,
                     stroke_width=2).move_to([x + rem * width / 2, y, 0])
    return pieces, tail


class E3A(VScene):
    SID = "E3A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP)
        st = scene_title("几何分布")
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(1)
        res = [0, 0, 0, 1]
        shots = VGroup(*[shot(h) for h in res]).arrange(RIGHT, buff=0.5).move_to(UP * 0.8)
        nums = VGroup(*[M(f"{i + 1}", 28, MUTED).next_to(s, DOWN, buff=0.2) for i, s in enumerate(shots)])
        for s_, n_ in zip(shots, nums):
            self.play(FadeIn(s_, shift=DOWN * 0.6, scale=0.6), FadeIn(n_), run_time=0.55)
        xl = M(r"X=4", 52, GOLD).next_to(shots, RIGHT, buff=0.8)
        self.play(Write(xl), Flash(shots[3], color=TEAL), run_time=0.8)
        pr = VGroup(*[M("1-p" if not h else "p", 32, BRICK if not h else TEAL).next_to(n_, DOWN, buff=0.25)
                      for h, n_ in zip(res, nums)])
        self.play(LaggedStart(*[FadeIn(x) for x in pr], lag_ratio=0.2), run_time=1.0)
        self.catch_up()

        self.seg(2)
        prod = M(r"P(X=4)=(1-p)^3\,p", 44).next_to(pr, DOWN, buff=0.45)
        self.play(Write(prod), run_time=1.0)
        self.wait(0.6)
        gen = M(r"P(X=k)=(1-p)^{k-1}p", 48, TEAL)
        self.play(FadeOut(VGroup(shots, nums, pr, xl)), ReplacementTransform(prod, gen.move_to(UP * 2.2 + RIGHT * 2.6)),
                  run_time=1.0)
        ax = axes([0, 12.8, 1], [0, 0.34, 0.1], 10.0, 3.6, xnums=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                  ynums=[0.1, 0.2, 0.3], xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.9)
        ks = list(range(1, 13))
        sm = stems(ax, ks, [(1 - P) ** (k - 1) * P for k in ks], TEAL, dot_r=0.07, width=4)
        self.play(Create(ax), run_time=0.7)
        self.play(LaggedStart(*[GrowFromEdge(s, DOWN) for s in sm], lag_ratio=0.12), run_time=1.8)
        ratio = VGroup(*[M(r"\times(1-p)", 22, BRICK).move_to(ax.c2p(k + 0.5, (1 - P) ** (k - 1) * P + 0.04))
                         for k in (1, 2, 3)])
        self.play(LaggedStart(*[FadeIn(r) for r in ratio], lag_ratio=0.3), run_time=1.0)
        name = T("公比 1−p 的几何级数 → “几何”分布", 24, GOLD, bold=True).move_to(ax.c2p(8.5, 0.25))
        self.play(FadeIn(name), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(gen, ratio, name)), run_time=0.5)

        self.seg(3)
        pieces, tail = strip_pieces(y=1.6)
        frame = Rectangle(width=12, height=0.6, stroke_color=INK, stroke_width=2).move_to([0, 1.6, 0])
        one = M("1", 32).next_to(frame, UP, buff=0.12)
        self.play(Create(frame), FadeIn(one), FadeIn(VGroup(*pieces, tail).copy().set_fill(tint(TEAL, 0.25))),
                  run_time=0.8)
        links = VGroup()
        for k, pc in enumerate(pieces):
            knife = Line(pc.get_corner(UR) + UP * 0.25, pc.get_corner(DR) + DOWN * 0.25, color=BRICK, stroke_width=3)
            self.play(Create(knife), FadeIn(pc), run_time=0.35 if k < 4 else 0.2)
            self.remove(knife)
            if k < 6:
                links.add(DashedLine(pc.get_bottom(), sm[k][1].get_center(), color=GREY, stroke_width=1.2,
                                     dash_length=0.05))
        self.play(Create(links), run_time=0.8)
        sumone = M(r"\sum_{k\ge1}(1-p)^{k-1}p=1", 36, GOLD).move_to(UP * 2.55 + RIGHT * 3.5)
        self.play(FadeIn(sumone), run_time=0.6)
        self.catch_up()

        self.seg(4)
        k0 = 3
        rest = VGroup(*pieces[k0:], tail)
        br = Brace(rest, UP, color=BRICK)
        bl = M(r"P(X>3)=(1-p)^3", 34, BRICK).next_to(br, UP, buff=0.1)
        self.play(FadeOut(sumone), GrowFromCenter(br), FadeIn(bl), *[pieces[i].animate.set_opacity(0.3) for i in range(k0)],
                  run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(pieces, tail, frame, one, links, br, bl, ax, sm, st)), run_time=0.7)
        self.remove(*[m for m in self.mobjects if m is not hdr])


class E3B(VScene):
    SID = "E3B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("无记忆性")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        d = MathTex(r"P(X>m+n\mid X>m)", r"=\frac{P(X>m+n)}{P(X>m)}", r"=\frac{(1-p)^{m+n}}{(1-p)^{m}}",
                    r"=(1-p)^n", font_size=50)
        d.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(LEFT * 0.5 + UP * 0.2)
        d[1:].shift(RIGHT * 2.6)
        for i, part in enumerate(d):
            self.play(Write(part), run_time=1.1)
            self.wait(0.4 if i < 3 else 0.2)
        same = M(r"=P(X>n)", 50, GOLD).next_to(d[3], RIGHT, buff=0.3)
        self.play(Write(same), run_time=0.7)
        box = SurroundingRectangle(VGroup(d[0], same), color=GOLD, buff=0.2, corner_radius=0.1)
        self.play(Create(box), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(d, same, box)), run_time=0.5)

        self.seg(1)
        pieces, tail = strip_pieces(y=1.7, n=12)
        frame = Rectangle(width=12, height=0.6, stroke_color=INK, stroke_width=2).move_to([0, 1.7, 0])
        self.play(Create(frame), FadeIn(pieces), FadeIn(tail), run_time=1.0)
        k0 = 3
        cut = DashedLine(pieces[k0].get_corner(UL) + UP * 0.35, pieces[k0].get_corner(DL) + DOWN * 0.35, color=BRICK,
                         stroke_width=3)
        lab = T("已经失败 3 次", 22, BRICK, bold=True).next_to(VGroup(*pieces[:k0]), UP, buff=0.2)
        self.play(Create(cut), *[pieces[i].animate.set_opacity(0.25) for i in range(k0)], FadeIn(lab), run_time=0.9)
        rest = VGroup(*pieces[k0:], tail).copy()
        self.play(rest.animate.shift(DOWN * 1.6), run_time=1.0)
        f = 1 / (1 - P) ** k0
        self.play(rest.animate.stretch(f, 0).move_to([0, 0.1, 0]), run_time=2.2, rate_func=smooth)
        orig = VGroup(pieces, tail).copy().set_opacity(1).move_to([0, -1.2, 0])
        self.play(TransformFromCopy(VGroup(pieces, tail), orig), run_time=1.2)
        for i in range(k0):
            orig[0][i].set_opacity(1)
        eqs = VGroup(T("剩下的部分放大到长度 1", 22, BRICK, bold=True).next_to(rest, UP, buff=0.12),
                     T("原来的整根纸条", 22, MUTED).next_to(orig, DOWN, buff=0.12))
        self.play(FadeIn(eqs), run_time=0.4)
        same = T("一模一样：硬币没有记忆", 30, GOLD, bold=True).move_to(DOWN * 2.35)
        self.play(FadeIn(same, shift=UP * 0.2), run_time=0.7)
        gamb = T("“输了这么多次，这次该赢了”——赌徒谬误", 24, BRICK).next_to(same, DOWN, buff=0.2)
        self.wait(max(0.2, self.durs[1] * 0.7 - 8.0))
        self.play(FadeIn(gamb), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(pieces, tail, frame, cut, lab, rest, orig, eqs, same, gamb)), run_time=0.6)

        self.seg(2)
        l1 = M(r"S(k)=P(X>k)", 44).move_to(UP * 1.4)
        l2 = M(r"S(m+n)=S(m)\,S(n)", 50, INDIGO).move_to(UP * 0.2)
        l3 = M(r"\Longrightarrow\ S(k)=S(1)^k=(1-p)^k", 50, GOLD).move_to(DOWN * 1.1)
        self.play(Write(l1), run_time=0.9)
        self.play(Write(l2), run_time=1.1)
        self.wait(0.5)
        self.play(Write(l3), run_time=1.2)
        uniq = T("取正整数值的分布中，几何分布是唯一无记忆的", 26, INK, bold=True).move_to(DOWN * 2.4)
        self.play(FadeIn(uniq, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(l1, l2, l3, uniq, st)), run_time=0.6)


class E3C(VScene):
    SID = "E3C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("期望：首步分析")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        root = VGroup(Circle(radius=0.45, fill_color=tint(INK, 0.1), fill_opacity=1, stroke_color=INK),
                      T("开始", 22, INK, bold=True)).move_to(LEFT * 4.6 + UP * 0.3)
        root[1].move_to(root[0])
        win = VGroup(shot(1, 0.38), T("成功：共用 1 次", 26, TEAL, bold=True)).arrange(RIGHT, buff=0.3)
        lose = VGroup(shot(0, 0.38), T("失败：用掉 1 次，然后从头再来", 26, BRICK, bold=True)).arrange(RIGHT, buff=0.3)
        win.move_to(RIGHT * 0.9 + UP * 1.7)
        lose.move_to(RIGHT * 1.9 + DOWN * 1.1)
        a1 = Arrow(root.get_right(), win.get_left(), buff=0.15, color=TEAL, stroke_width=4)
        a2 = Arrow(root.get_right(), lose.get_left(), buff=0.15, color=BRICK, stroke_width=4)
        p1 = M("p", 36, TEAL).next_to(a1.get_center(), UP + LEFT * 0.2, buff=0.12)
        p2 = M("1-p", 36, BRICK).next_to(a2.get_center(), DOWN + LEFT * 0.2, buff=0.12)
        self.play(FadeIn(root, scale=0.6), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(p1), FadeIn(win, shift=RIGHT * 0.3), run_time=1.0)
        self.wait(max(0.2, self.durs[0] * 0.3 - 1.5))
        self.play(GrowArrow(a2), FadeIn(p2), FadeIn(lose, shift=RIGHT * 0.3), run_time=1.0)
        loop = CurvedArrow(lose.get_bottom() + DOWN * 0.1, root.get_bottom() + DOWN * 0.1, angle=-1.2, color=GREY,
                           stroke_width=3)
        again = mixed("无记忆 ⇒ 平均还要 ", "$E$", " 次", size=24, color=MUTED).next_to(loop, DOWN, buff=0.05)
        self.play(Create(loop), FadeIn(again), run_time=1.2)
        self.catch_up()

        self.seg(1)
        tree = VGroup(root, win, lose, a1, a2, p1, p2, loop, again)
        self.play(tree.animate.scale(0.5).to_corner(DL, buff=0.5), run_time=0.8)
        eq = MathTex(r"E", r"=p\cdot 1+(1-p)(1+E)", font_size=52)
        e2 = MathTex(r"E", r"=1+(1-p)E", font_size=52)
        e3 = MathTex(r"pE", r"=1", font_size=52)
        e4 = MathTex(r"E", r"=\frac{1}{p}", font_size=60)
        col = VGroup(eq, e2, e3, e4).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(RIGHT * 2.0 + UP * 0.9)
        self.play(Write(eq), run_time=1.4)
        for e in (e2, e3):
            self.play(TransformFromCopy(col[col.submobjects.index(e) - 1], e), run_time=0.9)
        self.play(TransformFromCopy(e3, e4), e4.animate.set_color(GOLD), run_time=0.9)
        ex = mixed("命中率 0.2 ⇒ 平均投 ", "$5$", " 次", size=28).next_to(col, DOWN, buff=0.4)
        self.play(FadeIn(ex), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(tree, col, ex)), run_time=0.5)

        self.seg(2)
        var = M(r"\operatorname{Var}X=\frac{1-p}{p^2}", 50).move_to(UP * 2.1)
        self.play(Write(var), run_time=1.0)
        ax = axes([0, 25.5, 1], [0, 0.52, 0.1], 10.4, 3.6, xnums=[1, 5, 10, 15, 20, 25], ynums=[0.1, 0.3, 0.5],
                  xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.95)
        self.play(Create(ax), run_time=0.6)
        cur = None
        for pp, c in ((0.5, TEAL), (0.2, INDIGO), (0.1, BRICK)):
            ks = list(range(1, 26))
            g = stems(ax, ks, [(1 - pp) ** (k - 1) * pp for k in ks], c, dot_r=0.05)
            g.add(M(f"p={pp:g}", 34, c).move_to(ax.c2p(19, 0.42)))
            if cur is None:
                cur = g
                self.play(FadeIn(g, lag_ratio=0.03), run_time=0.8)
            else:
                self.play(Transform(cur, g), run_time=1.0)
            self.wait(0.4)
        self.catch_up()
        self.play(FadeOut(VGroup(var, ax, cur)), run_time=0.5)

        self.seg(3)
        nl1 = NumberLine(x_range=[0, 6, 1], length=8, color=AXIS, include_numbers=False).move_to(UP * 0.9 + RIGHT * 0.8)
        nl2 = NumberLine(x_range=[0, 6, 1], length=8, color=AXIS, include_numbers=False).move_to(DOWN * 1.2 + RIGHT * 0.8)
        for nl, start, c in ((nl1, 1, TEAL), (nl2, 0, BRICK)):
            for v in range(0, 6):
                nl.add(M(str(v), 26, c if v >= start else FAINT).next_to(nl.n2p(v), DOWN, buff=0.15))
        t1 = VGroup(T("数试验次数", 26, TEAL, bold=True), M(r"X\in\{1,2,\dots\},\ \ \mathbb{E}X=\tfrac1p", 30))
        t2 = VGroup(T("数失败次数", 26, BRICK, bold=True),
                    M(r"Y=X-1\in\{0,1,\dots\},\ \ \mathbb{E}Y=\tfrac{1-p}{p}", 30))
        for t, nl in ((t1, nl1), (t2, nl2)):
            t.arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(nl, UP, buff=0.3).align_to(nl, LEFT)
        self.play(Create(nl1), FadeIn(t1), run_time=1.0)
        self.play(Create(nl2), FadeIn(t2), run_time=1.0)
        warn = T("看书时先分清用的是哪一种约定", 24, GOLD, bold=True).move_to(DOWN * 2.6)
        self.play(FadeIn(warn), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(nl1, nl2, t1, t2, warn, st)), run_time=0.6)


class E3D(VScene):
    SID = "E3D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("负二项分布：等到第 r 次成功")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)
        res = [0, 1, 0, 0, 1, 0, 0, 0, 1]

        self.seg(0)
        cells = VGroup(*[shot(h, 0.3) for h in res]).arrange(RIGHT, buff=0.25).move_to(UP * 1.0)
        idx = VGroup(*[M(str(i + 1), 24, MUTED).next_to(c, DOWN, buff=0.15) for i, c in enumerate(cells)])
        for c_, i_ in zip(cells, idx):
            self.play(FadeIn(c_, shift=DOWN * 0.4, scale=0.6), FadeIn(i_), run_time=0.3)
        rlab = mixed("等到第 ", "$r=3$", " 次成功", size=28).next_to(cells, UP, buff=0.4)
        xlab = M(r"X=9", 44, GOLD).next_to(cells, RIGHT, buff=0.4)
        self.play(FadeIn(rlab), Write(xlab), run_time=0.8)
        self.catch_up()

        self.seg(1)
        b1 = Brace(VGroup(*cells[:-1]), DOWN, buff=0.55, color=INDIGO)
        t1 = MathTex(r"\binom{k-1}{r-1}p^{r-1}(1-p)^{k-r}", font_size=36, color=INDIGO).next_to(b1, DOWN, buff=0.1)
        l1 = T("前 k−1 次里恰好 r−1 次成功（二项概率）", 22, INDIGO).next_to(t1, DOWN, buff=0.12)
        b2 = Brace(cells[-1], DOWN, buff=0.55, color=TEAL)
        t2 = M(r"\times\,p", 40, TEAL).next_to(b2, DOWN, buff=0.1)
        self.play(GrowFromCenter(b1), Write(t1), FadeIn(l1), run_time=1.4)
        self.wait(max(0.2, self.durs[1] * 0.35 - 1.4))
        self.play(GrowFromCenter(b2), Write(t2), run_time=0.9)
        f = M(r"P(X=k)=\binom{k-1}{r-1}p^{r}(1-p)^{k-r}", 46, TEAL).move_to(DOWN * 2.65)
        fb = SurroundingRectangle(f, color=TEAL, buff=0.15, corner_radius=0.08)
        self.wait(max(0.2, self.durs[1] * 0.68 - self.durs[1] * 0.35 - 0.9))
        self.play(Write(f), Create(fb), run_time=1.3)
        self.catch_up()
        self.play(FadeOut(VGroup(b1, t1, l1, b2, t2, f, fb)), run_time=0.5)

        self.seg(2)
        segs = [(0, 1), (2, 4), (5, 8)]
        cols = [TEAL, INDIGO, BRICK]
        bands = VGroup()
        for (a, b), c in zip(segs, cols):
            r = SurroundingRectangle(VGroup(*cells[a:b + 1]), color=c, buff=0.08, corner_radius=0.1,
                                     fill_color=c, fill_opacity=0.12, stroke_width=3)
            lab = M(r"\mathrm{Geo}(p)", 28, c).next_to(r, DOWN, buff=0.55)
            bands.add(VGroup(r, lab))
        for b_ in bands:
            self.play(Create(b_[0]), FadeIn(b_[1]), run_time=0.8)
        sum_ = M(r"X=G_1+G_2+\cdots+G_r", 42).move_to(DOWN * 1.5)
        mv = M(r"\mathbb{E}X=\frac{r}{p},\qquad \operatorname{Var}X=\frac{r(1-p)}{p^2}", 40, GOLD).move_to(DOWN * 2.6)
        self.play(Write(sum_), run_time=1.0)
        self.wait(max(0.2, self.durs[2] * 0.6 - 3.4))
        self.play(Write(mv), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(cells, idx, rlab, xlab, bands, sum_, mv)), run_time=0.5)

        self.seg(3)
        ax = axes([0, 41, 5], [0, 0.37, 0.1], 10.6, 4.2, xnums=[0, 5, 10, 15, 20, 25, 30, 35, 40], ynums=[0.1, 0.2, 0.3],
                  xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.5)
        self.play(Create(ax), run_time=0.6)
        for r, c in ((1, INK), (3, TEAL), (6, BRICK)):
            ks = list(range(r, 41))
            pts = [ax.c2p(k, math.comb(k - 1, r - 1) * 0.35 ** r * 0.65 ** (k - r)) for k in ks]
            ln = VMobject(stroke_color=c, stroke_width=3.5).set_points_as_corners(pts)
            ds = VGroup(*[Dot(q, radius=0.04, color=c) for q in pts])
            lab = M(f"r={r}", 32, c).move_to(ax.c2p(*{1: (3.2, 0.34), 3: (9.5, 0.14), 6: (21, 0.1)}[r]))
            self.play(Create(ln), FadeIn(ds, lag_ratio=0.03), FadeIn(lab), run_time=1.1)
        clt = T("越多独立小段相加 → 越像钟形", 26, GOLD, bold=True).move_to(ax.c2p(28, 0.3))
        self.play(FadeIn(clt), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.5)

        self.seg(4)
        dual = MathTex(r"P(X\le n)", r"=", r"P\big(B(n,p)\ge r\big)", font_size=56).move_to(UP * 0.8)
        dual[0].set_color(TEAL)
        dual[2].set_color(INDIGO)
        self.play(Write(dual), run_time=1.4)
        l1 = T("前 n 次内等到第 r 次成功", 24, TEAL).next_to(dual[0], DOWN, buff=0.5)
        l2 = T("n 次里至少成功 r 次", 24, INDIGO).next_to(dual[2], DOWN, buff=0.5)
        self.play(FadeIn(l1), FadeIn(l2), run_time=0.8)
        pair = T("一个数等待，一个数次数", 28, GOLD, bold=True).move_to(DOWN * 1.8)
        self.play(FadeIn(pair, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(dual, l1, l2, pair)), run_time=0.5)

        self.seg(5)
        ax2 = axes([-0.6, 14.6, 1], [0, 0.25, 0.05], 10.0, 3.8, xnums=[0, 2, 4, 6, 8, 10, 12, 14], ynums=[0.1, 0.2],
                   xlabel=T("理赔次数", 20, INK))
        ax2.move_to(DOWN * 0.6)
        k2 = list(range(15))
        # 均值 3、方差 7.5 的负二项（失败次数形式 r=2, p=0.4）对比均值 3 的泊松
        nbp = [math.comb(k + 1, 1) * 0.4 ** 2 * 0.6 ** k for k in k2]
        bb = bars(ax2, k2, nbp, BRICK, w=0.7, opacity=0.45)
        po = stems(ax2, k2, [poisson_pmf(3, k) for k in k2], INK, dot_r=0.05, width=2.5)
        self.play(Create(ax2), FadeIn(bb, lag_ratio=0.05), run_time=1.0)
        self.play(FadeIn(po), run_time=0.7)
        lg = legend([(BRICK, "实际数据：均值 3，方差 7.5", "bar"), (INK, "泊松：方差 = 均值 = 3", "dot")])
        lg.move_to(ax2.c2p(9.8, 0.2))
        self.play(FadeIn(lg), run_time=0.6)
        od = T("方差 > 均值：过度离散 → 用负二项", 26, GOLD, bold=True).move_to(UP * 2.25)
        self.play(FadeIn(od), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, bb, po, lg, od, st)), run_time=0.5)

        self.seg(6)
        tl = Arrow(LEFT * 6, RIGHT * 6, buff=0, color=AXIS, stroke_width=3, max_tip_length_to_length_ratio=0.02)
        tl.shift(DOWN * 0.2)
        times = [-4.7, -3.1, -2.6, -0.4, 1.3, 2.0, 4.4]
        rings = VGroup()
        for t_ in times:
            ring = VGroup(Circle(radius=0.22, fill_color=tint(TEAL, 0.6), fill_opacity=1, stroke_color=TEAL),
                          Text("☎", font_size=22, color=INK)).move_to([t_, 0.35, 0])
            ring[1].move_to(ring[0])
            rings.add(ring)
        self.play(GrowArrow(tl), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.3, scale=1.5) for r in rings], lag_ratio=0.25), run_time=2.2)
        nxt = T("下一集：把时间切得无限细 → 泊松分布", 28, TEAL, bold=True).move_to(DOWN * 1.6)
        self.play(FadeIn(nxt, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
