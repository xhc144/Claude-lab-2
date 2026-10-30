# -*- coding: utf-8 -*-
"""第二章 行列式从哪里来：体积倍数 → 莱布尼茨公式 → 性质 → 克莱默法则 → 拉普拉斯展开。"""
from common import *


class Card2(ChapterCard):
    N = 2


def det2(m):
    return m[0][0] * m[1][1] - m[0][1] * m[1][0]


class VolumeFactor(BScene):
    CHAPTER = 2
    TITLE = "行列式 = 体积的伸缩倍数"

    def construct(self):
        self.header()
        plane = NumberPlane(x_range=[-12, 12, 1], y_range=[-8, 8, 1], background_line_style={
            "stroke_color": CYAN, "stroke_width": 1.2, "stroke_opacity": 0.35},
            axis_config={"stroke_color": SKY, "stroke_width": 2, "stroke_opacity": 0.6})
        sq = Polygon(ORIGIN, RIGHT, RIGHT + UP, UP, stroke_color=GOLD, stroke_width=3, fill_color=GOLD,
                     fill_opacity=0.35)
        grp = VGroup(plane, sq)
        grp.scale(1.5, about_point=ORIGIN)
        saved = grp.copy()
        e1 = always_redraw(lambda: vec(ORIGIN, sq.get_vertices()[1], CYAN, width=6))
        e2 = always_redraw(lambda: vec(ORIGIN, sq.get_vertices()[3], MAGENTA, width=6))

        def sdet():
            p = sq.get_vertices()
            a, b = p[1] - p[0], p[3] - p[0]
            return (a[0] * b[1] - a[1] * b[0]) / 2.25

        def arc():
            d = sdet()
            if abs(d) < 0.15:
                return VGroup()
            p = sq.get_vertices()
            c = (p[0] + p[2]) / 2
            return orient_arc(c, 0.3, d > 0, GOLD if d > 0 else RED, width=3)

        oa = always_redraw(arc)
        self.play(Create(plane, lag_ratio=0.02), run_time=1.2)
        self.play(FadeIn(sq), run_time=0.4)
        self.add(e1, e2, oa)
        self.cap("把平面上的线性变换作用在单位正方形 e₁∧e₂ 上，看面积变成多少倍", wait=None)

        # 读数
        lab = T("面积倍数", 24, MUTED)
        num = DecimalNumber(1.0, num_decimal_places=2, include_sign=True, font_size=50, color=GOLD)
        num.add_updater(lambda m: m.set_value(sdet()).set_color(GOLD if sdet() > 0.01 else (RED if sdet() < -0.01 else INK)))
        ro = VGroup(lab, num).arrange(RIGHT, buff=0.3).to_corner(UL, buff=0.5).shift(DOWN * 0.95)
        num.add_updater(lambda m: m.next_to(lab, RIGHT, buff=0.3))
        ro_bg = panel(VGroup(lab, num.copy()), pad=0.25, color=GOLD)
        self.play(FadeIn(ro_bg), FadeIn(ro), run_time=0.5)

        cases = [
            ([[2, 1], [0, 1.5]], "拉伸加剪切：面积变成 3 倍", None),
            ([[1, 1.2], [0, 1]], "纯剪切：面积不变，det = 1", None),
            ([[0.6, 1.4], [1.4, 0.3]], "镜像翻转：绕行方向反了，det < 0", RED),
            ([[1, 2], [0.5, 1]], "把平面压成一条直线：面积为 0，det = 0", ORANGE),
        ]
        mt_prev = None
        for m, text, col in cases:
            self.beat(4)
            mt = VGroup(M("T=", 40), matrix_tex([[f"{x:g}" for x in r] for r in m], 40),
                        M(rf"\det T = {det2(m):+.2f}".replace("+", r"+"), 36, col or GOLD)).arrange(RIGHT, buff=0.2)
            mt.to_corner(UR, buff=0.5).shift(DOWN * 0.95)
            mtb = panel(mt, pad=0.22, color=col or CYAN)
            anims = [FadeIn(VGroup(mtb, mt), shift=LEFT * 0.2)]
            if mt_prev is not None:
                anims.append(FadeOut(mt_prev))
            self.play(*anims, run_time=0.5)
            mt_prev = VGroup(mtb, mt)
            self.cap(text, wait=0)
            self.hit()
            self.play(ApplyMatrix(np.array(m), grp), run_time=2.0)
            self.wait(2.4)
            self.play(Transform(grp, saved.copy()), run_time=1.2)
        self.play(FadeOut(mt_prev), run_time=0.4)
        self.beat(4)
        e1.clear_updaters()
        e2.clear_updaters()
        oa.clear_updaters()
        self.clear_all(keep=[self._hdr])

        # 定义
        r1 = VGroup(T("线性映射 T 自动作用在 k-向量上：", 30, INK),
                    M(r"\Lambda^k T\,(v_1\wedge\cdots\wedge v_k) = Tv_1\wedge\cdots\wedge Tv_k", 42, CYAN)).arrange(
            DOWN, buff=0.25)
        r2 = VGroup(T("最高次只有一维：", 30, INK), M(r"\dim\Lambda^n(V) = \binom{n}{n} = 1", 42, MAGENTA)).arrange(
            RIGHT, buff=0.3)
        r3 = T("一维空间上的线性映射，只能是“乘以一个数”", 30, INK)
        rows = VGroup(r1, r2, r3).arrange(DOWN, buff=0.55).move_to(UP * 0.9)
        self.beat(2)
        self.play(FadeIn(r1[0], shift=DOWN * 0.2), run_time=0.5)
        self.play(Write(r1[1]), run_time=1.4)
        self.cap("每个向量先被 T 映过去，再楔起来", wait=None)
        self.beat(2)
        self.hit()
        self.play(FadeIn(r2, shift=DOWN * 0.2), run_time=0.8)
        self.wait(2.0)
        self.play(FadeIn(r3, shift=DOWN * 0.2), run_time=0.8)
        self.wait(2.2)
        d = M([r"Te_1\wedge Te_2\wedge\cdots\wedge Te_n", "=", r"(\det T)", r"\; e_1\wedge e_2\wedge\cdots\wedge e_n"], 54)
        d[2].set_color(GOLD)
        db = result_box(d, GOLD, pad=0.35)
        tagd = pill("定义", GOLD, 24).next_to(db, UP, buff=0.2).align_to(db, LEFT)
        VGroup(db, d).move_to(DOWN * 2.0)
        tagd.next_to(db, UP, buff=0.15).align_to(db, LEFT)
        self.beat(4)
        self.hit("impact")
        self.play(FadeIn(db), Write(d), FadeIn(tagd), run_time=1.2)
        self.play(ring_pulse(d[2].get_center(), GOLD, 3.0), light_sweep(d), run_time=0.9)
        self.cap("这个数就是行列式：Λⁿ T 在一维空间上的伸缩倍数", wait=None, t2c={"行列式": GOLD})
        self.cap("这个定义不用选坐标，也不用任何公式——它只用到 “Λⁿ 是一维的”", wait=None)
        self.clear_all()
        self.finish()


class Leibniz(BScene):
    CHAPTER = 2
    TITLE = "推导莱布尼茨公式"

    def construct(self):
        self.header()
        A = M(r"A=\begin{pmatrix} a_{11}&a_{12}&a_{13}\\ a_{21}&a_{22}&a_{23}\\ a_{31}&a_{32}&a_{33}\end{pmatrix}", 38)
        col = M(r"Ae_j=\sum_i a_{ij}\,e_i", 40, CYAN)
        top = VGroup(A, col).arrange(RIGHT, buff=0.8).move_to(UP * 1.9)
        self.play(FadeIn(A), run_time=0.6)
        self.play(Write(col), run_time=1.0)
        self.cap("第 j 列就是 Aeⱼ 的坐标。以 3 阶为例，按定义计算 Ae₁∧Ae₂∧Ae₃", wait=None)
        self.beat(4)
        ex = M([r"Ae_1\wedge Ae_2\wedge Ae_3", "=", r"\sum_{i,j,k}", r"a_{i1}a_{j2}a_{k3}", r"\;e_i\wedge e_j\wedge e_k"], 44)
        ex.move_to(UP * 1.9)
        self.play(FadeOut(top, shift=UP * 0.3), run_time=0.5)
        self.play(Write(ex), run_time=1.6)
        self.cap("三个括号各自展开：i、j、k 各取 1, 2, 3，一共 3 × 3 × 3 = 27 项", wait=None)

        # 27 块砖
        tiles = {}
        grid = VGroup()
        for i in (1, 2, 3):
            block = VGroup()
            for j in (1, 2, 3):
                for k in (1, 2, 3):
                    t = EN(f"{i}{j}{k}", 20, INK)
                    rep = len({i, j, k}) < 3
                    b = RoundedRectangle(corner_radius=0.06, width=0.82, height=0.48, stroke_color=SKY, stroke_width=1.5,
                                         fill_color=PANEL, fill_opacity=0.9)
                    tile = VGroup(b, t.move_to(b))
                    tile.rep = rep
                    tiles[(i, j, k)] = tile
                    block.add(tile)
            block.arrange_in_grid(3, 3, buff=0.1)
            grid.add(block)
        grid.arrange(RIGHT, buff=0.45).move_to(DOWN * 0.55)
        cnt = VGroup(EN("27", 40, GOLD, black=True), T("项", 26, MUTED)).arrange(RIGHT, buff=0.15).next_to(grid, DOWN,
                                                                                                         buff=0.4)
        self.beat(2)
        self.play(LaggedStart(*[FadeIn(tiles[key], scale=0.6) for key in sorted(tiles)], lag_ratio=0.03), run_time=1.6)
        self.play(FadeIn(cnt), run_time=0.4)
        self.wait(1.0)
        self.beat(4)
        self.cap("凡是下标有重复的，比如 e₁∧e₁∧e₂，都等于 0", wait=0, t2c={"0": RED})
        reps = [tiles[k] for k in sorted(tiles) if tiles[k].rep]
        self.play(*[t[0].animate.set_stroke(RED, 2.5) for t in reps], *[t[1].animate.set_color(RED) for t in reps],
                  run_time=0.6)
        self.wait(1.4)
        self.hit("impact")
        self.play(*[burst(t.get_center(), RED, n=8, radius=0.5, run_time=0.8) for t in reps],
                  *[FadeOut(t, scale=0.3) for t in reps],
                  Transform(cnt[0], EN("6", 40, GOLD, black=True).move_to(cnt[0])), run_time=0.8)
        self.cap("27 项里只剩 6 项活了下来——恰好是 1, 2, 3 的 3! = 6 个排列", wait=None, t2c={"6 个排列": GOLD})

        # 6 个排列：排成一列，配符号
        perms = [((1, 2, 3), "+", r"a_{11}a_{22}a_{33}"), ((2, 3, 1), "+", r"a_{21}a_{32}a_{13}"),
                 ((3, 1, 2), "+", r"a_{31}a_{12}a_{23}"), ((1, 3, 2), "-", r"a_{11}a_{32}a_{23}"),
                 ((2, 1, 3), "-", r"a_{21}a_{12}a_{33}"), ((3, 2, 1), "-", r"a_{31}a_{22}a_{13}")]
        rows = VGroup()
        for p, sg, tex in perms:
            c = GOLD if sg == "+" else RED
            perm = EN("".join(map(str, p)), 22, c)
            arrow = M(r"\to", 32, MUTED)
            wed = M(rf"e_{p[0]}\wedge e_{p[1]}\wedge e_{p[2]} = {sg}\,e_1\wedge e_2\wedge e_3", 32)
            term = M(sg + tex, 34, c)
            rows.add(VGroup(perm, arrow, wed, term).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to(DOWN * 0.5)
        for r in rows:
            r[3].align_to(rows[0][3], LEFT)
        keep_tiles = [tiles[p] for p, _, _ in perms]
        self.beat(4)
        self.play(FadeOut(cnt), *[ReplacementTransform(t, r[0]) for t, r in zip(keep_tiles, rows)], run_time=1.0)
        for r in rows:
            self.play(FadeIn(r[1]), FadeIn(r[2], shift=RIGHT * 0.2), run_time=0.45)
        self.cap("每一项按交换次数排好顺序：偶数次取 +，奇数次取 −", wait=None)
        self.play(LaggedStart(*[FadeIn(r[3], shift=LEFT * 0.2) for r in rows], lag_ratio=0.15), run_time=1.2)
        self.wait(1.5)

        # 合并成公式
        self.beat(4)
        res = M(r"\det A = a_{11}a_{22}a_{33}+a_{21}a_{32}a_{13}+a_{31}a_{12}a_{23}"
                r"-a_{11}a_{32}a_{23}-a_{21}a_{12}a_{33}-a_{31}a_{22}a_{13}", 38)
        res.move_to(DOWN * 0.3)
        self.play(FadeOut(VGroup(*[r[:3] for r in rows])), ReplacementTransform(VGroup(*[r[3] for r in rows]), res),
                  run_time=1.2)
        self.cap("这就是三阶行列式的展开式——不是背下来的，是算出来的", wait=None)
        self.beat(4)
        gen = M(r"\det A=\sum_{\sigma\in S_n}\operatorname{sgn}(\sigma)\,a_{\sigma(1)1}\,a_{\sigma(2)2}\cdots a_{\sigma(n)n}", 54,
                GOLD)
        gb = result_box(gen, GOLD, pad=0.35)
        VGroup(gb, gen).move_to(DOWN * 0.4)
        self.hit("impact")
        self.play(FadeOut(res, shift=DOWN * 0.3), FadeOut(ex, shift=UP * 0.3), FadeIn(gb), Write(gen), run_time=1.4)
        self.play(ring_pulse(gen.get_center(), GOLD, 4.0), light_sweep(gen), run_time=1.0)
        note = mixed("$n^n$", "项", r"$\;\longrightarrow\;$", "$n!$", "项", size=28, color=MUTED).next_to(gb, DOWN, buff=0.45)
        note[3].set_color(GOLD)
        self.play(FadeIn(note), run_time=0.6)
        self.cap("一般的 n 阶同样如此：nⁿ 项里只剩 n! 项，符号就是排列的奇偶性", wait=None)
        self.cap("课本把它当作定义；在外代数里，它只是一个推论", wait=None, t2c={"推论": GOLD})
        self.clear_all()
        self.finish()


class Properties(BScene):
    CHAPTER = 2
    TITLE = "行列式的性质，一口气全出来"

    def construct(self):
        self.header()
        cards = [
            ("交换两列，变号", r"\cdots\wedge v\wedge w\wedge\cdots=-\cdots\wedge w\wedge v\wedge\cdots", RED),
            ("两列相同，为 0", r"\cdots\wedge v\wedge\cdots\wedge v\wedge\cdots = 0", ORANGE),
            ("一列加上另一列的倍数，不变", r"v\wedge(w+c\,v)=v\wedge w+c\,v\wedge v=v\wedge w", LIME),
            ("三角矩阵 = 对角线之积",
             r"a_{11}e_1\wedge(a_{12}e_1+a_{22}e_2)\wedge\cdots=a_{11}a_{22}\cdots a_{nn}\,e_1\wedge\cdots\wedge e_n", SKY),
            ("det ≠ 0 ⟺ 列线性无关 ⟺ 可逆", r"Ae_1\wedge\cdots\wedge Ae_n\neq 0", VIOLET),
            ("乘法公式", r"\det(ST)=\det S\,\det T", GOLD),
        ]
        notes = [
            "楔积的反交换性",
            "规则 ③：同一个向量楔两次是 0",
            "多出来的一项含 v∧v，消失",
            "后面的每一列里，前面已有的 eᵢ 都被楔掉",
            "第一章的推论：楔积 ≠ 0 ⟺ 线性无关",
            "下面单独证明",
        ]
        slots = VGroup()
        small = []
        for i, (title, tex, c) in enumerate(cards):
            t = T(title, 24, c, bold=True)
            f = M(tex, 30)
            if f.width > 5.6:
                f.scale_to_fit_width(5.6)
            g = VGroup(t, f).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            box = RoundedRectangle(corner_radius=0.1, width=6.4, height=1.35, fill_color=PANEL, fill_opacity=0.88,
                                   stroke_color=c, stroke_width=2)
            g.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.3)
            small.append(VGroup(box, g))
        grid = VGroup(*small).arrange_in_grid(3, 2, buff=(0.35, 0.28)).move_to(DOWN * 0.35)
        self.cap("有了“行列式 = Λⁿ 的伸缩倍数”，课本里的性质都只剩一行", wait=None)
        for i, (title, tex, c) in enumerate(cards):
            # 先放大在中央展示，再缩回格子
            big_t = T(title, 40, c, bold=True)
            big_f = M(tex, 50)
            if big_f.width > 12:
                big_f.scale_to_fit_width(12)
            big_n = T(notes[i], 26, MUTED)
            big = VGroup(big_t, big_f, big_n).arrange(DOWN, buff=0.4).move_to(UP * 0.2)
            br = brackets(big_f, color=c, pad=0.35)
            modal = RoundedRectangle(corner_radius=0.15, width=13.2, height=big.height + 1.2, fill_color=PANEL,
                                     fill_opacity=0.97, stroke_color=c, stroke_width=2).move_to(big)
            self.beat(4)
            self.hit()
            self.play(FadeIn(modal, scale=0.95), FadeIn(big_t, shift=DOWN * 0.2), Write(big_f), Create(br), run_time=1.0)
            self.play(FadeIn(big_n), run_time=0.4)
            self.wait(max(2.2, read_time(notes[i]) + 0.6))
            self.play(ReplacementTransform(VGroup(big_t, big_f), small[i][1]), ReplacementTransform(modal, small[i][0]),
                      FadeOut(big_n), FadeOut(br), run_time=0.8)
        self.wait(1.0)
        self.beat(4)
        self.play(*[m.animate.set_opacity(0.25) for m in small[:5]], small[5].animate.scale(1.08), run_time=0.6)
        self.wait(0.6)
        self.play(FadeOut(VGroup(*small[:5])), small[5].animate.scale(1 / 1.08).to_edge(UP, buff=1.25), run_time=0.8)

        # 乘法公式的证明
        lines = [
            [r"(ST)e_1\wedge\cdots\wedge(ST)e_n", "=", r"S(Te_1)\wedge\cdots\wedge S(Te_n)"],
            ["=", r"\Lambda^n S\,(Te_1\wedge\cdots\wedge Te_n)"],
            ["=", r"\Lambda^n S\,\big(\det T\; e_1\wedge\cdots\wedge e_n\big)"],
            ["=", r"\det T\,\det S\; e_1\wedge\cdots\wedge e_n"],
        ]
        L = VGroup(*[M(l, 44) for l in lines]).arrange(DOWN, buff=0.32)
        for l in L[1:]:
            l.shift(RIGHT * (L[0][1].get_x() - l[0].get_x()))
        L.move_to(DOWN * 0.75)
        L[3][1].set_color(GOLD)
        why = ["先做 T，再做 S", "Λⁿ S 的定义", "Λⁿ T 就是乘 det T", "Λⁿ S 就是乘 det S"]
        for i, l in enumerate(L):
            self.beat(2)
            self.play(Write(l), run_time=1.1)
            self.cap(why[i], wait=1.6)
        self.hit("impact")
        bx = SurroundingRectangle(L[3][1], color=GOLD, buff=0.12, corner_radius=0.08)
        self.play(Create(bx), ring_pulse(L[3][1].get_center(), GOLD, 3), run_time=0.8)
        self.cap("如果从莱布尼茨公式硬证，要把 (n!)² 项重新配对；在这里它只是“先做 T 再做 S”", wait=None)
        self.clear_all()
        self.finish()


class Cramer(BScene):
    CHAPTER = 2
    TITLE = "克莱默法则：一行证明"

    def construct(self):
        self.header()
        K = 1.3  # 画面放大倍数（面积读数按原尺寸算）
        O = np.array([-6.4, -2.6, 0])
        a1 = np.array([2.0, 0.5, 0]) * K
        a2 = np.array([0.6, 1.6, 0]) * K
        x1, x2 = 1.4, 0.8
        b0 = x1 * a1 + x2 * a2
        s = ValueTracker(0)

        def B():
            return b0 - s.get_value() * x2 * a2

        P0 = para(O, a1, a2, CYAN, opacity=0.18)
        Pb = always_redraw(lambda: para(O, B(), a2, GOLD, opacity=0.3))
        A1 = vec(O, O + a1, CYAN, width=5)
        A2 = vec(O, O + a2, MAGENTA, width=5)
        Bv = always_redraw(lambda: vec(O, O + B(), GOLD, width=5))
        la1 = M("a_1", 36, CYAN).next_to(O + a1, DOWN, buff=0.12)
        la2 = M("a_2", 36, MAGENTA).next_to(O + a2, LEFT, buff=0.12)
        lb = always_redraw(lambda: M("b", 36, GOLD).next_to(O + B(), UR, buff=0.08))

        # 代数
        alg = [
            M([r"Ax=b", r"\iff", r"x_1a_1+x_2a_2+\cdots+x_na_n=b"], 38),
            M([r"a_1\wedge\cdots\wedge", r"\underset{i}{b}", r"\wedge\cdots\wedge a_n", "=", r"\sum_j x_j\;",
               r"a_1\wedge\cdots\wedge", r"\underset{i}{a_j}", r"\wedge\cdots\wedge a_n"], 38),
            M(["=", r"x_i", r"\;a_1\wedge\cdots\wedge a_n"], 38),
        ]
        AL = VGroup(*alg).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        alg[2].shift(RIGHT * (alg[1][3].get_x() - alg[2][0].get_x()))
        if AL.width > 12.6:
            AL.scale_to_fit_width(12.6)
        AL.move_to([0, 1.2, 0])
        alg[1][1].set_color(GOLD)
        alg[2][1].set_color(GOLD)
        self.play(Write(alg[0]), run_time=1.4)
        self.cap("解方程组 Ax = b，就是把 b 写成各列 a₁, …, aₙ 的组合", wait=None)
        self.beat(2)
        self.play(Write(alg[1]), run_time=1.8)
        self.cap("把第 i 列换成 b，再整体楔起来", wait=None)
        self.beat(2)
        self.cap("j ≠ i 的项里，aⱼ 出现了两次，全部是 0——只剩 j = i 这一项", wait=0)
        self.play(Indicate(alg[1][6], color=RED), run_time=1.0)
        self.play(Write(alg[2]), run_time=1.2)
        self.wait(2.0)
        res = M(r"x_i=\frac{\det A_i}{\det A}", 60, GOLD)
        rb = result_box(res, GOLD, pad=0.3)
        lab = T("（Aᵢ：A 的第 i 列换成 b）", 22, MUTED)
        VGroup(rb, res).move_to([0, -1.5, 0])
        lab.next_to(rb, DOWN, buff=0.2)
        self.beat(4)
        self.hit("impact")
        self.play(FadeIn(rb), Write(res), FadeIn(lab), run_time=1.0)
        self.play(ring_pulse(res.get_center(), GOLD, 2.5), run_time=0.6)
        self.cap("克莱默法则。课本上要用代数余子式绕一大圈，这里一行就完了", wait=None)

        # 几何
        self.beat(4)
        self.play(FadeOut(AL), VGroup(rb, res).animate.move_to([3.6, -1.4, 0]), lab.animate.move_to([3.6, -2.45, 0]),
                  run_time=0.6)
        self.add(P0, A1, A2, la1, la2)
        self.play(FadeIn(P0), FadeIn(A1), FadeIn(A2), FadeIn(la1), FadeIn(la2), run_time=0.6)
        self.add(Pb, Bv, lb)
        self.play(FadeIn(Pb), run_time=0.5)

        def area(p, q):
            return (p[0] * q[1] - p[1] * q[0]) / K ** 2

        ar = VGroup(T("b∧a₂ 的面积", 22, GOLD), DecimalNumber(area(b0, a2), num_decimal_places=2, font_size=40, color=GOLD))
        ar.arrange(RIGHT, buff=0.25)
        ar0 = VGroup(T("a₁∧a₂ 的面积", 22, CYAN), DecimalNumber(area(a1, a2), num_decimal_places=2, font_size=40,
                                                            color=CYAN)).arrange(RIGHT, buff=0.25)
        ar[1].add_updater(lambda m: m.set_value(area(B(), a2)))
        AR = VGroup(ar, ar0).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.6, 1.9, 0])
        self.play(FadeIn(AR), run_time=0.5)
        self.cap("几何上看（n = 2）：b∧a₂ 是金色的平行四边形", wait=None)
        self.beat(2)
        self.cap("让 b 沿着 a₂ 的方向滑动——就是减去 x₂a₂——面积不变", wait=0)
        guide = DashedLine(O + b0 + a2 * 1.0, O + x1 * a1 - a2 * 0.6, color=GOLD, stroke_width=2, dash_length=0.08)
        self.play(Create(guide), run_time=0.5)
        self.play(s.animate.set_value(1), run_time=2.6)
        self.wait(1.0)
        ratio = M(r"b\wedge a_2 = x_1\,(a_1\wedge a_2)", 44, GOLD).next_to(AR, DOWN, buff=0.45)
        self.hit()
        self.play(Write(ratio), run_time=1.0)
        self.cap("滑到底，b 变成了 x₁a₁：面积正好是 a₁∧a₂ 的 x₁ 倍（4.06 = 1.4 × 2.90）", wait=None)
        self.clear_all()
        self.finish()


class Laplace(BScene):
    CHAPTER = 2
    TITLE = "拉普拉斯展开（以及它的推广）"

    def construct(self):
        self.header()
        L = [
            M([r"\det A\; e_1\wedge\cdots\wedge e_n", "=", r"a_1", r"\wedge", r"(a_2\wedge\cdots\wedge a_n)"], 40),
            M([r"a_1", "=", r"\sum_i a_{i1}\,e_i"], 40),
            M([r"a_2\wedge\cdots\wedge a_n", "=", r"\sum_i M_{i1}\; e_1\wedge\cdots\wedge\widehat{e_i}\wedge\cdots\wedge e_n"], 40),
            M([r"e_i\wedge\big(e_1\wedge\cdots\wedge\widehat{e_i}\wedge\cdots\wedge e_n\big)", "=",
               r"(-1)^{i-1}\; e_1\wedge\cdots\wedge e_n"], 40),
        ]
        G = VGroup(*L).arrange(DOWN, buff=0.34).move_to(UP * 0.95)
        for l in L[1:]:
            l.shift(RIGHT * (L[0][1].get_x() - l[1].get_x()))
        notes = ["把第一列单独拿出来，后面 n − 1 列先楔在一起",
                 "第一列按基展开",
                 "后面 n − 1 列的楔积落在 Λⁿ⁻¹ 里，坐标是去掉第 i 行、第 1 列的子式 Mᵢ₁",
                 "把 eᵢ 往右移到第 i 个位置，要交换 i − 1 次"]
        L[0][2].set_color(CYAN)
        L[1][0].set_color(CYAN)
        for l, n in zip(L, notes):
            self.beat(2)
            self.play(Write(l), run_time=1.3)
            self.cap(n, wait=None)
        self.beat(4)
        res = M(r"\det A=\sum_{i=1}^n(-1)^{i+1}\,a_{i1}\,M_{i1}", 54, GOLD)
        rb = result_box(res, GOLD, pad=0.3)
        VGroup(rb, res).move_to(DOWN * 2.45)
        self.hit("impact")
        self.play(FadeIn(rb), Write(res), run_time=1.0)
        self.cap("按第一列展开的拉普拉斯公式，正负号交替的来历一目了然", wait=None)
        self.beat(4)
        self.play(FadeOut(G), VGroup(rb, res).animate.scale(0.75).to_edge(UP, buff=1.2), run_time=0.7)

        # 3 阶的例子：高亮行列
        ent = [[r"a_{11}", r"a_{12}", r"a_{13}"], [r"a_{21}", r"a_{22}", r"a_{23}"], [r"a_{31}", r"a_{32}", r"a_{33}"]]
        cells = VGroup(*[VGroup(*[M(e, 40) for e in row]).arrange(RIGHT, buff=0.55) for row in ent]).arrange(DOWN, buff=0.4)
        lpar = M(r"(", 40).stretch_to_fit_height(cells.height + 0.3).next_to(cells, LEFT, buff=0.15)
        rpar = M(r")", 40).stretch_to_fit_height(cells.height + 0.3).next_to(cells, RIGHT, buff=0.15)
        mat = VGroup(lpar, cells, rpar).move_to([-3.6, -0.6, 0])
        self.play(FadeIn(mat), run_time=0.6)
        terms = VGroup()
        signs = ["+", "-", "+"]
        for i in range(3):
            minor_rows = [r for r in range(3) if r != i]
            mtex = r"\begin{vmatrix}" + r"\\".join(" & ".join(ent[r][1:]) for r in minor_rows) + r"\end{vmatrix}"
            t = M(signs[i] + ent[i][0] + mtex, 38, INK)
            terms.add(t)
        terms.arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([2.8, -0.6, 0])
        for i in range(3):
            self.beat(2)
            row = cells[i]
            colm = VGroup(*[cells[r][0] for r in range(3)])
            hl = VGroup(*[SurroundingRectangle(cells[r][c], color=GOLD, buff=0.08)
                          for r in range(3) for c in range(1, 3) if r != i])
            self.play(cells[i][0].animate.set_color(GOLD), *[m.animate.set_opacity(0.25) for m in row[1:]],
                      *[cells[r][0].animate.set_opacity(0.25) for r in range(3) if r != i], Create(hl), run_time=0.6)
            self.play(Write(terms[i]), run_time=0.9)
            self.wait(1.0)
            self.play(FadeOut(hl), *[m.animate.set_opacity(1).set_color(INK) for r in cells for m in r], run_time=0.4)
        self.cap("三阶的情形：+、−、+ 交替，余子式就是挡住一行一列剩下的部分", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(mat, terms)), run_time=0.5)

        # 推广
        g1 = M([r"\underbrace{(a_1\wedge\cdots\wedge a_k)}_{\sum_I \det A_{I,[k]}\,e_I}", r"\wedge",
                r"\underbrace{(a_{k+1}\wedge\cdots\wedge a_n)}_{\sum_J \det A_{J,[k+1,n]}\,e_J}"], 42)
        g2 = M(r"\det A=\sum_{|I|=k}\pm\,\det A_{I,[1,k]}\;\det A_{I^c,[k+1,n]}", 48, MAGENTA)
        G2 = VGroup(g1, g2).arrange(DOWN, buff=0.6).move_to(DOWN * 0.6)
        self.play(Write(g1), run_time=1.6)
        self.cap("更一般地，把楔积从第 k 列处切成两段：前 k 列、后 n − k 列各自展开", wait=None)
        self.beat(2)
        self.hit()
        self.play(Write(g2), run_time=1.2)
        self.cap("e_I ∧ e_J 只在 J 恰好是 I 的补集时不为 0——这就是广义拉普拉斯展开", wait=None)
        self.cap("直接证明要小心翼翼地追踪每个符号；在外代数里，只是把楔积拆成两段", wait=None,
                 t2c={"拆成两段": MAGENTA})
        self.clear_all()
        self.finish()
