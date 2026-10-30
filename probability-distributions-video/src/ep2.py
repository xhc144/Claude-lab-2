# -*- coding: utf-8 -*-
"""第 2 集：数成功的次数——二项、超几何与多项分布。"""
import random

from common import *  # noqa: F401,F403
from props import die

EP = 2


def hyper_pmf(N, K, n, k):
    if k < max(0, n - N + K) or k > min(n, K):
        return 0.0
    return math.comb(K, k) * math.comb(N - K, n - k) / math.comb(N, n)


def cell(txt, color, s=0.62):
    sq = RoundedRectangle(corner_radius=0.08, width=s, height=s, fill_color=tint(color, 0.5), fill_opacity=1,
                          stroke_color=color, stroke_width=2)
    return VGroup(sq, T(txt, int(s * 40), INK, bold=True).move_to(sq))


class Galton:
    """高尔顿板：rows 排钉子，球每层左右各一半。"""

    def __init__(self, rows=10, dx=0.48, dy=0.36, top=2.35, cx=-2.6):
        self.rows, self.dx, self.dy, self.top, self.cx = rows, dx, dy, top, cx
        self.bottom = top - (rows + 0.6) * dy

    def peg(self, r, i):
        return np.array([self.cx + (i - r / 2) * self.dx, self.top - r * self.dy, 0])

    def pegs(self):
        return VGroup(*[Dot(self.peg(r, i), radius=0.045, color=AXIS) for r in range(self.rows) for i in range(r + 1)])

    def slot_x(self, k):
        return self.cx + (k - self.rows / 2) * self.dx

    def walls(self, height):
        g = VGroup()
        for k in range(self.rows + 2):
            x = self.cx + (k - 0.5 - self.rows / 2) * self.dx
            g.add(Line([x, self.bottom, 0], [x, self.bottom - height, 0], color=FAINT, stroke_width=2))
        g.add(Line([self.slot_x(0) - self.dx / 2, self.bottom - height, 0],
                   [self.slot_x(self.rows) + self.dx / 2, self.bottom - height, 0], color=AXIS, stroke_width=2))
        return g

    def path(self, choices):
        pts = [self.peg(0, 0) + UP * 0.35]
        i = 0
        for r, c in enumerate(choices):
            p = self.peg(r, i) + UP * 0.09
            pts.append(p)
            i += c
            nxt = self.peg(r + 1, i) if r + 1 < self.rows else np.array([self.slot_x(i), self.bottom, 0])
            pts.append((p + nxt) / 2 + UP * 0.12)
        path = VMobject().set_points_smoothly(pts)
        return path, i


class E2A(VScene):
    SID = "E2A"

    def construct(self):
        self.seg(0)
        hdr = play_episode_card(self, EP)
        st = scene_title("高尔顿板")
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(1)
        g = Galton()
        pegs = g.pegs()
        H = 2.2
        walls = g.walls(H)
        self.play(LaggedStart(*[FadeIn(p, scale=0.3) for p in pegs], lag_ratio=0.01), Create(walls), run_time=1.4)
        rng = random.Random(4)
        ch = [rng.randint(0, 1) for _ in range(g.rows)]
        path, k = g.path(ch)
        ball = Dot(path.get_start(), radius=0.09, color=BRICK)
        self.play(FadeIn(ball, scale=2), run_time=0.3)
        self.play(MoveAlongPath(ball, path), run_time=4.0, rate_func=linear)
        bh = 0.13
        self.play(ball.animate.move_to([g.slot_x(k), g.bottom - H + bh / 2 + 0.02, 0]), run_time=0.4)
        lr = VGroup(*[T("右" if c else "左", 20, BRICK if c else INDIGO, bold=True) for c in ch]).arrange(RIGHT,
                                                                                                         buff=0.12)
        lr.move_to(RIGHT * 3.9 + UP * 1.8)
        cnt = mixed("往右 ", f"${sum(ch)}$", " 次 → 第 ", f"${k}$", " 格", size=28).next_to(lr, DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(x, shift=DOWN * 0.1) for x in lr], lag_ratio=0.1), run_time=1.2)
        self.play(FadeIn(cnt), run_time=0.6)
        self.catch_up()

        self.seg(2)
        self.play(FadeOut(lr), FadeOut(cnt), run_time=0.4)
        counts = [0] * (g.rows + 1)
        counts[k] += 1
        balls, anims = [], []
        rng = random.Random(11)
        for _ in range(170):
            ch = [rng.randint(0, 1) for _ in range(g.rows)]
            p, kk = g.path(ch)
            land = np.array([g.slot_x(kk), g.bottom - H + bh * (counts[kk] + 0.5) + 0.02, 0])
            counts[kk] += 1
            p.add_points_as_corners([land])
            b = Dot(p.get_start(), radius=0.06, color=BRICK).set_opacity(0)

            def mk(b=b, p=p):
                def upd(m, a):
                    m.move_to(p.point_from_proportion(a))
                    m.set_opacity(1 if a > 0 else 0)
                return UpdateFromAlphaFunc(b, upd, run_time=1.6, rate_func=rate_functions.ease_in_sine)
            balls.append(b)
            anims.append(mk())
        self.add(*balls)
        self.play(LaggedStart(*anims, lag_ratio=0.045), run_time=min(10.0, self.durs[2] * 0.75))
        ax = axes([-0.5, 10.5, 1], [0, 0.3, 0.1], 4.6, 3.0, xnums=[0, 5, 10], ynums=(), xlabel="k", tips=False)
        ax.move_to(RIGHT * 4.4 + DOWN * 0.6)
        bn = stems(ax, list(range(11)), [binom_pmf(10, 0.5, kk) for kk in range(11)], BRICK, dot_r=0.06)
        lab = M(r"X\sim B(10,\tfrac12)", 34, BRICK).next_to(ax, UP, buff=0.3)
        self.play(Create(ax), FadeIn(bn, lag_ratio=0.1), Write(lab), run_time=1.4)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m is not hdr], run_time=0.8)


class E2B(VScene):
    SID = "E2B"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("二项分布的推导")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        # --- 一条序列 ---
        self.seg(0)
        seq = ["成", "败", "成", "成"]
        cells = VGroup(*[cell(s, TEAL if s == "成" else BRICK, 0.9) for s in seq]).arrange(RIGHT, buff=0.25)
        cells.move_to(UP * 1.2)
        probs = VGroup(*[M("p" if s == "成" else "q", 44, TEAL if s == "成" else BRICK).next_to(c, DOWN, buff=0.3)
                         for s, c in zip(seq, cells)])
        qdef = M(r"q=1-p", 34, MUTED).to_edge(RIGHT, buff=0.8).set_y(2.2)
        self.play(FadeIn(qdef), run_time=0.5)
        for c, pr in zip(cells, probs):
            self.play(FadeIn(c, shift=DOWN * 0.3, scale=0.7), FadeIn(pr), run_time=0.5)
        dots = VGroup(*[M(r"\times", 36).move_to((probs[i].get_center() + probs[i + 1].get_center()) / 2)
                        for i in range(3)])
        res = M(r"=p^3q", 48).next_to(probs, RIGHT, buff=0.4)
        self.play(FadeIn(dots), run_time=0.4)
        self.play(Write(res), run_time=0.8)
        ind = T("各次独立 ⇒ 概率相乘", 24, GOLD).next_to(probs, DOWN, buff=0.5)
        self.play(FadeIn(ind), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(cells, probs, dots, res, ind)), run_time=0.5)

        # --- 所有 3 成 1 败 ---
        self.seg(1)
        rows = VGroup()
        for fail in range(4):
            s = ["成"] * 4
            s[fail] = "败"
            r = VGroup(*[cell(x, TEAL if x == "成" else BRICK, 0.62) for x in s]).arrange(RIGHT, buff=0.15)
            r.add(M(r"p^3q", 36).next_to(r, RIGHT, buff=0.5))
            rows.add(r)
        rows.arrange(DOWN, buff=0.25).move_to(LEFT * 1.0 + DOWN * 0.2)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in rows], lag_ratio=0.35), run_time=2.2)
        br = Brace(rows, RIGHT, color=GOLD)
        bl = mixed("$\\binom{4}{3}=4$", " 条", size=34, color=GOLD).next_to(br, RIGHT)
        self.wait(max(0.2, self.durs[1] * 0.5 - 2.2))
        self.play(GrowFromCenter(br), FadeIn(bl), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(rows, br, bl, qdef)), run_time=0.5)

        # --- 网格路径与帕斯卡三角（把网格转 45°，节点上的路径数正好排成帕斯卡三角） ---
        self.seg(2)
        n = 4
        dx, dy = 1.05, 0.95
        top = np.array([-2.2, 2.0, 0])
        pt = lambda i, j: top + RIGHT * (i - j) * dx + DOWN * (i + j) * dy  # noqa: E731  i 成功、j 失败
        grid = VGroup()
        for i in range(n + 1):
            for j in range(n + 1 - i):
                if i + j < n:
                    grid.add(Line(pt(i, j), pt(i + 1, j), color=tint(TEAL, 0.45), stroke_width=3))
                    grid.add(Line(pt(i, j), pt(i, j + 1), color=tint(BRICK, 0.45), stroke_width=3))
        nodes = VGroup(*[Dot(pt(i, j), radius=0.06, color=AXIS) for i in range(n + 1) for j in range(n + 1 - i)])
        lr = T("成功 ↘", 24, TEAL, bold=True).next_to(pt(1, 0), RIGHT, buff=0.3)
        lu = T("↙ 失败", 24, BRICK, bold=True).next_to(pt(0, 1), LEFT, buff=0.3)
        self.play(Create(grid), FadeIn(nodes), FadeIn(lr), FadeIn(lu), run_time=1.2)
        target = (3, 1)
        cols = [TEAL, BRICK, INDIGO, GOLD]
        paths = VGroup()
        for c, fail in zip(cols, range(4)):
            seq = [1] * 4
            seq[fail] = 0
            pts, i, j = [pt(0, 0)], 0, 0
            for s_ in seq:
                i, j = (i + 1, j) if s_ else (i, j + 1)
                pts.append(pt(i, j))
            paths.add(VMobject(stroke_color=c, stroke_width=7).set_points_as_corners(pts).shift(
                RIGHT * 0.06 * (fail - 1.5)))
        end = Dot(pt(*target), radius=0.14, color=GOLD)
        self.play(FadeIn(end, scale=2), run_time=0.4)
        for pth in paths:
            self.play(Create(pth), run_time=0.7)
        cnt4 = mixed("4 条路径 ", "$=\\binom{4}{3}$", size=28, color=GOLD).next_to(end, RIGHT, buff=0.35)
        self.play(FadeIn(cnt4), run_time=0.5)
        nums = VGroup()
        for i in range(n + 1):
            for j in range(n + 1 - i):
                lab = M(str(math.comb(i + j, i)), 34, GOLD if (i, j) == target else INK)
                circ = Circle(radius=0.26, fill_color=BG, fill_opacity=1, stroke_color=GOLD if (i, j) == target
                              else FAINT, stroke_width=2).move_to(pt(i, j))
                nums.add(VGroup(circ, lab.move_to(pt(i, j))))
        self.play(paths.animate.set_opacity(0.3), FadeOut(cnt4), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(x, scale=0.5) for x in sorted(nums, key=lambda m: -m.get_y())],
                              lag_ratio=0.08), run_time=2.0)
        tl = VGroup(T("每个节点上的数 = 走到它的路径条数", 24, INK, bold=True),
                    T("一行一行读下来，就是帕斯卡三角", 22, MUTED),
                    M(r"\binom{n}{k}=\binom{n-1}{k-1}+\binom{n-1}{k}", 32)).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        tl.move_to(RIGHT * 3.9 + DOWN * 0.2)
        self.play(FadeIn(tl, shift=LEFT * 0.2), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(grid, nodes, lr, lu, paths, end, nums, tl)), run_time=0.6)

        # --- 公式拼装 ---
        self.seg(3)
        f = MathTex(r"P(X=k)", r"=", r"\binom{n}{k}", r"p^{k}", r"(1-p)^{n-k}", font_size=64).move_to(UP * 0.6)
        tags = [("序列条数", GOLD, 2), ("k 次成功", TEAL, 3), ("n−k 次失败", BRICK, 4)]
        self.play(Write(f[0:2]), run_time=0.8)
        for txt, c, idx in tags:
            f[idx].set_color(c)
            self.play(FadeIn(f[idx], shift=UP * 0.5, scale=1.3), run_time=0.7)
            lab = T(txt, 22, c, bold=True).next_to(f[idx], DOWN, buff=0.55 if idx != 3 else 0.3)
            self.play(FadeIn(lab), run_time=0.3)
            self.wait(0.5)
        box = SurroundingRectangle(f, color=TEAL, buff=0.25, corner_radius=0.1)
        name = mixed("二项分布 ", "$X\\sim B(n,p)$", size=34, color=TEAL).next_to(box, UP, buff=0.3)
        self.play(Create(box), FadeIn(name), run_time=0.9)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (hdr, st)], run_time=0.5)

        # --- 二项式定理 ---
        self.seg(4)
        terms = MathTex(r"(p+q)^4", r"=", r"q^4", r"+4pq^3", r"+6p^2q^2", r"+4p^3q", r"+p^4", font_size=52)
        terms.move_to(UP * 2.0)
        self.play(Write(terms), run_time=1.6)
        ax = axes([-0.6, 4.6, 1], [0, 0.4, 0.1], 7.0, 2.6, xnums=[0, 1, 2, 3, 4], ynums=(), xlabel="k", tips=False)
        ax.move_to(DOWN * 0.8)
        ps = [binom_pmf(4, 0.6, k) for k in range(5)]
        sm = stems(ax, list(range(5)), ps, TEAL, dot_r=0.08, width=5)
        arrows = VGroup(*[Arrow(terms[2 + k].get_bottom(), sm[k][1].get_center() + UP * 0.12, buff=0.1, color=GREY,
                                stroke_width=2.5, max_tip_length_to_length_ratio=0.08) for k in range(5)])
        self.play(Create(ax), run_time=0.6)
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), GrowFromEdge(s, DOWN)) for a, s in zip(arrows, sm)],
                              lag_ratio=0.25), run_time=2.0)
        one = M(r"p+q=1\ \Rightarrow\ \sum_k P(X=k)=1", 40, GOLD).move_to(DOWN * 2.75)
        self.play(Write(one), run_time=1.2)
        self.catch_up()
        self.play(FadeOut(VGroup(terms, ax, sm, arrows, one, st)), run_time=0.6)


class E2C(VScene):
    SID = "E2C"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("期望和方差：拆成指示变量")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        n = 10
        res = [1, 0, 0, 1, 1, 0, 1, 0, 0, 1]
        lamps = VGroup()
        for i, r in enumerate(res):
            bulb = Circle(radius=0.3, stroke_color=AXIS, stroke_width=2, fill_color=BG, fill_opacity=1)
            lab = M(f"I_{{{i + 1}}}", 26).next_to(bulb, DOWN, buff=0.15)
            lamps.add(VGroup(bulb, lab))
        lamps.arrange(RIGHT, buff=0.32).move_to(UP * 0.9)
        self.play(LaggedStart(*[FadeIn(l_, shift=UP * 0.2) for l_ in lamps], lag_ratio=0.06), run_time=1.0)
        for l_, r in zip(lamps, res):
            if r:
                l_[0].generate_target()
                l_[0].target.set_fill(GOLD, opacity=1).set_stroke(GOLD)
        self.play(LaggedStart(*[MoveToTarget(l_[0]) for l_, r in zip(lamps, res) if r], lag_ratio=0.2),
                  *[Flash(l_[0], color=GOLD, flash_radius=0.4) for l_, r in zip(lamps, res) if r], run_time=1.2)
        xs = M(r"X=I_1+I_2+\cdots+I_{10}=5", 44).move_to(DOWN * 0.9)
        ei = M(r"I_i\sim B(1,p),\qquad \mathbb{E}I_i=p", 38, TEAL).move_to(DOWN * 2.1)
        self.play(Write(xs), run_time=1.2)
        self.play(FadeIn(ei), run_time=0.7)
        self.catch_up()

        self.seg(1)
        self.play(FadeOut(xs), FadeOut(ei), run_time=0.4)
        ex = MathTex(r"\mathbb{E}X", r"=\mathbb{E}I_1+\cdots+\mathbb{E}I_n", r"=np", font_size=54).move_to(DOWN * 0.8)
        self.play(Write(ex[0:2]), run_time=1.2)
        self.play(Write(ex[2]), ex[2].animate.set_color(GOLD), run_time=0.7)
        note = T("线性，不需要独立", 24, MUTED).next_to(ex, UP, buff=0.3)
        eg = mixed("例：", "$n=100,\\ p=0.3\\ \\Rightarrow\\ \\mathbb{E}X=30$", size=30).move_to(DOWN * 2.3)
        self.play(FadeIn(note), run_time=0.5)
        self.play(FadeIn(eg, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(ex, note, eg, lamps)), run_time=0.5)

        self.seg(2)
        vr = MathTex(r"\operatorname{Var}X", r"=\sum\operatorname{Var}I_i", r"=np(1-p)", font_size=50).move_to(UP * 2.0)
        self.play(Write(vr), run_time=1.4)
        tag = T("需要独立", 22, BRICK, bold=True).next_to(vr[1], DOWN, buff=0.15)
        self.play(FadeIn(tag), run_time=0.4)
        ax = axes([0, 1.04, 0.25], [0, 0.32, 0.1], 9.0, 3.2, xnums=[0, 0.25, 0.5, 0.75, 1], ynums=(),
                  xlabel="X/n", tips=False)
        ax.move_to(DOWN * 1.2)
        pline = DashedLine(ax.c2p(0.3, 0), ax.c2p(0.3, 0.31), color=GOLD, stroke_width=2)
        pl = M("p", 30, GOLD).next_to(pline, UP, buff=0.05)
        self.play(Create(ax), Create(pline), FadeIn(pl), run_time=0.8)
        cur = None
        for n_, c in ((10, TEAL), (40, INDIGO), (160, BRICK)):
            ks = list(range(n_ + 1))
            pts = [ax.c2p(k / n_, binom_pmf(n_, 0.3, k) * n_ / 10 * 0.3) for k in ks]
            g = VGroup(*[Line(ax.c2p(k / n_, 0), p_, color=c, stroke_width=2.5 if n_ < 100 else 1.5) for k, p_ in
                         zip(ks, pts)])
            lab = M(f"n={n_}", 32, c).move_to(ax.c2p(0.8, 0.26))
            g.add(lab)
            if cur is None:
                self.play(FadeIn(g, lag_ratio=0.03), run_time=1.0)
            else:
                self.play(Transform(cur, g), run_time=1.3)
            cur = cur or g
            self.wait(0.6)
        lln = T("比例 X/n 越来越集中在 p：大数定律", 26, GOLD, bold=True).move_to(UP * 0.9)
        self.play(FadeIn(lln, shift=UP * 0.2), run_time=0.7)
        self.catch_up()
        self.play(FadeOut(VGroup(vr, tag, ax, pline, pl, cur, lln)), run_time=0.5)

        self.seg(3)
        m1 = MathTex(r"M_{I}(t)", r"=q+pe^t", font_size=50).move_to(UP * 1.8)
        m2 = MathTex(r"M_X(t)", r"=(q+pe^t)^n", font_size=50).move_to(UP * 0.6)
        self.play(Write(m1), run_time=1.0)
        self.play(TransformFromCopy(m1, m2), run_time=1.2)
        add = M(r"B(m,p)+B(n,p)=B(m+n,p)", 46, TEAL).move_to(DOWN * 1.0)
        prf = M(r"(q+pe^t)^m(q+pe^t)^n=(q+pe^t)^{m+n}", 36, MUTED).next_to(add, DOWN, buff=0.4)
        self.wait(max(0.2, self.durs[3] * 0.45 - 2.2))
        self.play(Write(add), run_time=1.2)
        self.play(FadeIn(prf), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(m1, m2, add, prf, st)), run_time=0.6)


class E2D(VScene):
    SID = "E2D"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("二项分布的形状")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        ax = axes([0, 20.6, 1], [0, 0.3, 0.1], 10.4, 4.4, xnums=[0, 5, 10, 15, 20], ynums=[0.1, 0.2],
                  xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.45)
        p = ValueTracker(0.15)
        ks = list(range(21))
        S = always_redraw(lambda: stems(ax, ks, [binom_pmf(20, p.get_value(), k) for k in ks], TEAL, dot_r=0.07,
                                        width=4))
        lab = VGroup(M(r"n=20,\ p=", 36), DecimalNumber(0.15, num_decimal_places=2, font_size=36, color=INK)).arrange(
            RIGHT, buff=0.1).move_to(ax.c2p(16, 0.27))
        lab[1].add_updater(lambda m: m.set_value(p.get_value()))
        self.play(Create(ax), FadeIn(S), FadeIn(lab), run_time=1.0)
        self.play(p.animate.set_value(0.5), run_time=2.6, rate_func=smooth)
        self.wait(0.4)
        self.play(p.animate.set_value(0.85), run_time=2.6, rate_func=smooth)
        self.play(p.animate.set_value(0.3), run_time=1.6, rate_func=smooth)
        self.catch_up()
        lab[1].clear_updaters()

        self.seg(1)
        n_, pp = 20, 0.3
        ps = [binom_pmf(n_, pp, k) for k in ks]
        arrs = VGroup()
        for k in range(0, 14):
            r = ps[k + 1] / ps[k]
            a, b = ax.c2p(k + 0.15, ps[k] + 0.012), ax.c2p(k + 0.85, ps[k + 1] + 0.012)
            arrs.add(Arrow(a, b, buff=0, color=TEAL if r > 1 else BRICK, stroke_width=3, tip_length=0.12,
                           max_tip_length_to_length_ratio=0.4))
        ratio = MathTex(r"\frac{P(k+1)}{P(k)}", r"=\frac{(n-k)\,p}{(k+1)\,q}", font_size=46).move_to(UP * 2.15 +
                                                                                                    RIGHT * 2.4)
        self.play(FadeOut(lab), Write(ratio), run_time=1.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.12), run_time=2.4)
        up = T("> 1：上升", 24, TEAL, bold=True)
        dn = T("< 1：下降", 24, BRICK, bold=True)
        ud = VGroup(up, dn).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(ax.c2p(15.5, 0.17))
        self.play(FadeIn(ud), run_time=0.6)
        mode = math.floor((n_ + 1) * pp)
        mk = SurroundingRectangle(S[mode], color=GOLD, buff=0.08)
        ml = mixed("众数 ", "$\\lfloor (n+1)p\\rfloor=6$", size=28, color=GOLD).next_to(mk, UP, buff=0.5)
        self.wait(max(0.2, self.durs[1] * 0.62 - 4.4))
        self.play(Create(mk), FadeIn(ml), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(arrs, ratio, ud, mk, ml, S, ax)), run_time=0.6)

        self.seg(2)
        ax2 = axes([-4, 4.3, 1], [0, 0.48, 0.1], 10.0, 4.2, xnums=[-3, -2, -1, 0, 1, 2, 3], ynums=(),
                   xlabel=r"\frac{X-np}{\sqrt{np(1-p)}}")
        ax2.move_to(DOWN * 0.5)
        nc = DashedVMobject(curve(ax2, norm_pdf, -4, 4.2, INK, width=3), num_dashes=70)
        self.play(Create(ax2), run_time=0.7)
        cur = None
        for n2, c in ((10, PLUM), (30, TEAL), (100, BRICK)):
            mu, sd = n2 * pp, math.sqrt(n2 * pp * (1 - pp))
            g = VGroup()
            for k in range(n2 + 1):
                z = (k - mu) / sd
                if -4 < z < 4.2:
                    h = binom_pmf(n2, pp, k) * sd
                    lo, hi = ax2.c2p(z - 0.5 / sd, 0), ax2.c2p(z + 0.5 / sd, h)
                    g.add(Rectangle(width=hi[0] - lo[0], height=max(hi[1] - lo[1], 1e-3), fill_color=tint(c, 0.45),
                                    fill_opacity=1, stroke_color=c, stroke_width=1).move_to((lo + hi) / 2))
            g.add(M(f"n={n2}", 36, c).move_to(ax2.c2p(-2.8, 0.38)))
            if cur is None:
                cur = g
                self.play(FadeIn(g, lag_ratio=0.05), run_time=1.0)
            else:
                self.play(Transform(cur, g), run_time=1.4)
            self.wait(0.7)
        self.play(Create(nc), run_time=1.2)
        appr = mixed("近似：", "$B(n,p)\\approx N\\big(np,\\ np(1-p)\\big)$", size=30).move_to(UP * 2.1 + RIGHT * 2.0)
        nxt = T("→ 第 6 集：中心极限定理", 22, GOLD).next_to(appr, DOWN, buff=0.2)
        self.play(FadeIn(appr), FadeIn(nxt), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(VGroup(ax2, cur, nc, appr, nxt, st)), run_time=0.6)


class E2E(VScene):
    SID = "E2E"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("不放回：超几何分布")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        jar = VMobject(stroke_color=AXIS, stroke_width=4).set_points_as_corners(
            [[-1.5, 1.4, 0], [-1.5, -1.6, 0], [1.5, -1.6, 0], [1.5, 1.4, 0]]).move_to(LEFT * 3.6 + DOWN * 0.3)
        rng = random.Random(2)
        colors = [BRICK] * 8 + [GREY] * 12
        rng.shuffle(colors)
        balls = VGroup()
        for i, c in enumerate(colors):
            r_, col = divmod(i, 5)
            b = Circle(radius=0.22, fill_color=c, fill_opacity=1, stroke_color=WHITE, stroke_width=2)
            b.move_to(jar.get_corner(DL) + RIGHT * (0.32 + col * 0.57) + UP * (0.3 + r_ * 0.5))
            balls.add(b)
        self.play(Create(jar), LaggedStart(*[FadeIn(b, scale=0.4) for b in balls], lag_ratio=0.03), run_time=1.4)
        info = mixed("$N=20$", " 个球，", "$K=8$", " 个红球", size=28).next_to(jar, UP, buff=0.3)
        self.play(FadeIn(info), run_time=0.5)
        ratio = VGroup(T("罐中红球比例", 22, MUTED), M(r"8/20", 40, BRICK)).arrange(DOWN, buff=0.15)
        ratio.move_to(RIGHT * 4.6 + UP * 1.5)
        self.play(FadeIn(ratio), run_time=0.5)
        picks = [3, 7, 12, 15, 18]
        tray = [RIGHT * (0.2 + i * 0.6) + DOWN * 1.6 for i in range(5)]
        red, tot = 8, 20
        for i, idx in enumerate(picks):
            b = balls[idx]
            is_red = colors[idx] == BRICK
            red -= is_red
            tot -= 1
            nr = M(f"{red}/{tot}", 40, BRICK).move_to(ratio[1])
            self.play(b.animate.move_to(tray[i] + RIGHT * 0.4).set_stroke(GOLD, 3),
                      Transform(ratio[1], nr), run_time=0.75, path_arc=-0.6)
        dep = T("每摸走一个，比例就变：各次不独立", 24, BRICK, bold=True).move_to(DOWN * 2.6 + RIGHT * 2.2)
        self.play(FadeIn(dep, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(jar, balls, info, ratio, dep)), run_time=0.6)

        self.seg(1)
        f = MathTex(r"P(X=k)=", r"\frac{\binom{K}{k}\binom{N-K}{n-k}}{\binom{N}{n}}", font_size=64).move_to(UP * 0.5)
        self.play(Write(f), run_time=1.5)
        num = f[1][0:12]
        den = f[1][13:]
        b1 = Brace(den, DOWN, color=INK)
        l1 = T("所有选法", 24).next_to(b1, DOWN, buff=0.1)
        self.play(GrowFromCenter(b1), FadeIn(l1), run_time=0.8)
        b2 = Brace(num, UP, color=BRICK)
        l2 = T("红球里选 k 个 × 其余里选 n−k 个", 24, BRICK).next_to(b2, UP, buff=0.1)
        self.wait(max(0.2, self.durs[1] * 0.4 - 2.3))
        self.play(GrowFromCenter(b2), FadeIn(l2), run_time=0.8)
        name = mixed("超几何分布 ", "$X\\sim H(N,K,n)$", size=32, color=TEAL).move_to(DOWN * 2.4)
        self.play(FadeIn(name), run_time=0.6)
        self.catch_up()
        self.play(FadeOut(VGroup(f, b1, l1, b2, l2, name)), run_time=0.5)

        self.seg(2)
        ex = M(r"\mathbb{E}X=n\frac{K}{N}", 48).move_to(UP * 1.6)
        self.play(Write(ex), run_time=1.0)
        var = MathTex(r"\operatorname{Var}X=n\frac{K}{N}\Big(1-\frac{K}{N}\Big)", r"\frac{N-n}{N-1}", font_size=50)
        var.move_to(DOWN * 0.1)
        self.wait(max(0.2, self.durs[2] * 0.35 - 1.0))
        self.play(Write(var), run_time=1.4)
        hl = SurroundingRectangle(var[1], color=GOLD, buff=0.08, corner_radius=0.06)
        hlt = T("有限总体修正 < 1：负相关让波动变小", 24, GOLD, bold=True).next_to(var, DOWN, buff=0.5)
        self.play(Create(hl), FadeIn(hlt), run_time=0.9)
        self.catch_up()
        self.play(FadeOut(VGroup(ex, var, hl, hlt)), run_time=0.5)

        self.seg(3)
        ax = axes([-0.7, 10.7, 1], [0, 0.36, 0.1], 9.6, 4.0, xnums=list(range(11)), ynums=[0.1, 0.2, 0.3],
                  xlabel="k", ylabel="P(X=k)")
        ax.move_to(DOWN * 0.55)
        k5 = list(range(11))
        bb = bars(ax, k5, [binom_pmf(10, 0.4, k) for k in k5], GREY, w=0.36, opacity=0.35, offset=0.19)
        cur = bars(ax, k5, [hyper_pmf(20, 8, 10, k) for k in k5], TEAL, w=0.36, opacity=0.5, offset=-0.19)
        nl = M("N=20", 36, TEAL).move_to(ax.c2p(8.5, 0.32))
        lg = legend([(TEAL, "超几何（不放回）", "bar"), (GREY, "二项（放回）", "bar")]).move_to(ax.c2p(8.6, 0.24))
        self.play(Create(ax), FadeIn(bb), FadeIn(cur), FadeIn(nl), FadeIn(lg), run_time=1.0)
        for N in (50, 500):
            nb = bars(ax, k5, [hyper_pmf(N, int(0.4 * N), 10, k) for k in k5], TEAL, w=0.36, opacity=0.5,
                      offset=-0.19)
            self.play(Transform(cur, nb), Transform(nl, M(f"N={N}", 36, TEAL).move_to(nl)), run_time=1.4)
            self.wait(0.4)
        use = T("质量抽检 · 费舍尔精确检验", 24, MUTED).move_to(UP * 2.3)
        self.play(FadeIn(use), run_time=0.5)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, bb, cur, nl, lg, use, st)), run_time=0.6)


class E2F(VScene):
    SID = "E2F"

    def construct(self):
        hdr = running_header(EP)
        st = scene_title("多项分布")
        self.add(hdr)
        self.play(FadeIn(st, shift=RIGHT * 0.3), run_time=0.4)

        self.seg(0)
        rolls = [3, 6, 1, 3, 5, 2, 3, 6, 4, 1, 3, 5]
        ax = axes([0.4, 6.6, 1], [0, 4.6, 1], 6.0, 3.2, xnums=[1, 2, 3, 4, 5, 6], ynums=[1, 2, 3, 4], tips=False)
        ax.move_to(RIGHT * 2.8 + DOWN * 0.5)
        self.play(Create(ax), run_time=0.6)
        cnt = [0] * 7
        blocks = VGroup()
        unit = ax.c2p(0, 1)[1] - ax.c2p(0, 0)[1]
        dpos = LEFT * 4.2 + UP * 0.3
        for r in rolls:
            d = die(r, 0.9).move_to(dpos)
            self.add(d)
            blk = Rectangle(width=0.7, height=unit * 0.9, fill_color=tint(INDIGO, 0.5), fill_opacity=1,
                            stroke_color=INDIGO, stroke_width=1.5).move_to(ax.c2p(r, cnt[r] + 0.5))
            cnt[r] += 1
            self.play(FadeIn(d, scale=1.4), run_time=0.15)
            self.play(ReplacementTransform(d, blk), run_time=0.35)
            blocks.add(blk)
        lab = M(r"(N_1,\dots,N_6)\sim\mathrm{Mult}(12;\ \tfrac16,\dots,\tfrac16)", 32).next_to(ax, UP, buff=0.4)
        self.play(Write(lab), run_time=1.0)
        self.catch_up()
        self.play(FadeOut(VGroup(ax, blocks, lab)), run_time=0.5)

        self.seg(1)
        f = MathTex(r"P(N_1=k_1,\dots,N_m=k_m)=", r"\frac{n!}{k_1!\cdots k_m!}", r"\,p_1^{k_1}\cdots p_m^{k_m}",
                    font_size=54).move_to(UP * 0.8)
        self.play(Write(f), run_time=1.6)
        b1 = Brace(f[1], DOWN, color=GOLD)
        l1 = T("排列方式数", 24, GOLD).next_to(b1, DOWN, buff=0.1)
        b2 = Brace(f[2], DOWN, color=TEAL)
        l2 = T("一条序列的概率", 24, TEAL).next_to(b2, DOWN, buff=0.1)
        self.play(GrowFromCenter(b1), FadeIn(l1), run_time=0.7)
        self.play(GrowFromCenter(b2), FadeIn(l2), run_time=0.7)
        notes = VGroup(mixed("每一类：", "$N_i\\sim B(n,p_i)$", size=28),
                       mixed("类与类负相关：", "$\\operatorname{Cov}(N_i,N_j)=-np_ip_j$", size=28)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.25).move_to(DOWN * 2.0)
        self.wait(max(0.2, self.durs[1] * 0.55 - 3.0))
        self.play(LaggedStart(*[FadeIn(n_, shift=UP * 0.2) for n_ in notes], lag_ratio=0.5), run_time=1.4)
        self.catch_up()
        self.play(FadeOut(VGroup(f, b1, l1, b2, l2, notes, st)), run_time=0.6)

        self.seg(2)
        shots = VGroup()
        for i, hit in enumerate([0, 0, 0, 0, 1]):
            c = Circle(radius=0.35, fill_color=tint(GOLD, 0.7), fill_opacity=1, stroke_color=GOLD, stroke_width=3)
            mark = (Text("✓", font_size=36, color=TEAL) if hit else Text("✗", font_size=36, color=BRICK)).move_to(c)
            shots.add(VGroup(c, mark))
        shots.arrange(RIGHT, buff=0.4).move_to(UP * 0.5)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.4) for s in shots], lag_ratio=0.3), run_time=2.0)
        q = mixed("要试多少次才第一次成功？", size=34).next_to(shots, DOWN, buff=0.6)
        nxt = T("下一集：几何分布与负二项分布", 28, TEAL, bold=True).next_to(q, DOWN, buff=0.4)
        self.play(FadeIn(q), run_time=0.6)
        self.play(FadeIn(nxt, shift=UP * 0.2), run_time=0.6)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
