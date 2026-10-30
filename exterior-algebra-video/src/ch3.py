# -*- coding: utf-8 -*-
"""第三章 一行证明的定理们：子式矩阵 → 柯西–比内 → 面积的勾股定理 → 特征多项式 → 西尔维斯特 → 普吕克 → 微分形式。"""
from common import *


class Card3(ChapterCard):
    N = 3


def vmat(rows, size=30, color=INK):
    body = r"\\".join(" & ".join(r) for r in rows)
    return M(r"\begin{vmatrix}" + body + r"\end{vmatrix}", size, color)


ENT = [[f"a_{{{i}{j}}}" for j in (1, 2, 3)] for i in (1, 2, 3)]


class Compound(BScene):
    CHAPTER = 3
    TITLE = "Λᵏ A：由子式组成的矩阵"

    def construct(self):
        self.header()
        f1 = M([r"(\Lambda^k A)\,e_J", "=", r"Ae_{j_1}\wedge\cdots\wedge Ae_{j_k}", "=",
                r"\sum_{|I|=k}\det A_{I,J}\;e_I"], 44)
        f1.move_to(UP * 2.2)
        f1[4].set_color(GOLD)
        self.play(Write(f1), run_time=1.6)
        self.cap("A 作用在 k-向量上得到 Λᵏ A。它在基 e_I 下的矩阵元，恰好是 A 的 k 阶子式", wait=None,
                 t2c={"k 阶子式": GOLD})
        self.beat(2)

        # 3 阶、k = 2 的例子
        cells = VGroup(*[VGroup(*[M(e, 36) for e in row]).arrange(RIGHT, buff=0.45) for row in ENT]).arrange(DOWN, buff=0.35)
        lp = M("(", 40).stretch_to_fit_height(cells.height + 0.3).next_to(cells, LEFT, buff=0.12)
        rp = M(")", 40).stretch_to_fit_height(cells.height + 0.3).next_to(cells, RIGHT, buff=0.12)
        A = VGroup(M("A=", 38), VGroup(lp, cells, rp)).arrange(RIGHT, buff=0.2).move_to([-4.9, -0.6, 0])
        idx = [(1, 2), (1, 3), (2, 3)]
        lab = {(1, 2): "12", (1, 3): "13", (2, 3): "23"}
        entries = {}
        for I in idx:
            for J in idx:
                rows = [[ENT[i - 1][j - 1] for j in J] for i in I]
                entries[(I, J)] = vmat(rows, 31)
        grid = VGroup(*[VGroup(*[entries[(I, J)] for J in idx]).arrange(RIGHT, buff=0.3) for I in idx]).arrange(DOWN, buff=0.25)
        glp = M("(", 40).stretch_to_fit_height(grid.height + 0.3).next_to(grid, LEFT, buff=0.12)
        grp_ = M(")", 40).stretch_to_fit_height(grid.height + 0.3).next_to(grid, RIGHT, buff=0.12)
        C = VGroup(M(r"\Lambda^2A=", 38), VGroup(glp, grid, grp_)).arrange(RIGHT, buff=0.2).move_to([2.2, -0.6, 0])
        rl = VGroup(*[EN(lab[I], 16, MUTED).next_to(grid[k], RIGHT, buff=0.45) for k, I in enumerate(idx)])
        cl = VGroup(*[EN(lab[J], 16, MUTED).next_to(grid[0][k], UP, buff=0.25) for k, J in enumerate(idx)])
        self.play(FadeIn(A), FadeIn(C[0]), FadeIn(glp), FadeIn(grp_), FadeIn(rl), FadeIn(cl), run_time=0.8)
        self.cap("以 3 阶矩阵、k = 2 为例：基是 e₁∧e₂、e₁∧e₃、e₂∧e₃，Λ²A 是 3×3 的", wait=None)
        demo = [((1, 2), (1, 3)), ((2, 3), (1, 2)), ((1, 3), (2, 3))]
        for I, J in demo:
            self.beat(2)
            hl = VGroup(*[SurroundingRectangle(cells[i - 1][j - 1], color=GOLD, buff=0.07) for i in I for j in J])
            self.play(Create(hl), *[cells[i - 1][j - 1].animate.set_color(GOLD) for i in I for j in J], run_time=0.6)
            src = VGroup(*[cells[i - 1][j - 1] for i in I for j in J]).copy()
            self.hit()
            self.play(ReplacementTransform(src, entries[(I, J)]), run_time=0.9)
            self.play(FadeOut(hl), *[cells[i - 1][j - 1].animate.set_color(INK) for i in I for j in J], run_time=0.4)
            self.wait(0.6)
        rest = [entries[(I, J)] for I in idx for J in idx if (I, J) not in demo]
        self.play(LaggedStart(*[FadeIn(e, scale=0.8) for e in rest], lag_ratio=0.1), run_time=1.2)
        self.cap("第 I 行、第 J 列的元素 = 取 A 的第 I 行、第 J 列交叉出的子式。它叫 A 的 k 阶复合矩阵", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(A, C, rl, cl, *entries.values())), run_time=0.6)

        # 函子性
        g1 = M([r"(AB)v_1\wedge\cdots\wedge(AB)v_k", "=", r"A(Bv_1)\wedge\cdots\wedge A(Bv_k)"], 42)
        g2 = M([r"\Lambda^k(AB)", "=", r"\Lambda^k A\;\Lambda^k B"], 58, GOLD)
        g3 = M(r"\det(AB)_{I,J}=\sum_{|K|=k}\det A_{I,K}\,\det B_{K,J}", 46, INK)
        G = VGroup(g1, g2, g3).arrange(DOWN, buff=0.5).move_to(DOWN * 0.5)
        self.play(Write(g1), run_time=1.4)
        self.cap("Λᵏ 和乘法相容：先做 B 再做 A，就是做 AB", wait=None)
        self.beat(2)
        self.hit("impact")
        gb = result_box(g2, GOLD)
        gb.move_to(g2)
        self.play(FadeIn(gb), Write(g2), run_time=1.0)
        self.wait(1.0)
        self.play(Write(g3), run_time=1.3)
        self.cap("翻译成子式：AB 的每个 k 阶子式，都是 A、B 的 k 阶子式的“乘积之和”", wait=None)
        self.cap("把 AB 的子式按定义硬展开去验证，几乎没法手算；这里只用了一行", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(g1, g3, f1)), VGroup(gb, g2).animate.scale(0.7).to_edge(UP, buff=1.2), run_time=0.7)

        # 特征值
        d1 = M([r"\Lambda^2\begin{pmatrix}\lambda_1&&\\&\lambda_2&\\&&\lambda_3\end{pmatrix}", "=",
                r"\begin{pmatrix}\lambda_1\lambda_2&&\\&\lambda_1\lambda_3&\\&&\lambda_2\lambda_3\end{pmatrix}"], 40)
        d2 = M(r"\operatorname{tr}\Lambda^k A=\sum_{i_1<\cdots<i_k}\lambda_{i_1}\cdots\lambda_{i_k}=e_k(\lambda_1,\dots,\lambda_n)",
               44, CYAN)
        D = VGroup(d1, d2).arrange(DOWN, buff=0.55).move_to(DOWN * 0.7)
        self.play(Write(d1), run_time=1.5)
        self.cap("特征值也一样：eᵢ∧eⱼ 被放大 λᵢλⱼ 倍。Λᵏ A 的特征值，是 A 的特征值任取 k 个相乘", wait=None)
        self.beat(2)
        self.play(Write(d2), run_time=1.3)
        self.cap("（一般矩阵先上三角化，结论相同）。这条迹的公式，马上会在特征多项式里出现", wait=None)
        self.clear_all()
        self.finish()


class CauchyBinet(BScene):
    CHAPTER = 3
    TITLE = "柯西–比内公式"

    def construct(self):
        self.header()
        st = M(r"\det(AB)=\sum_{\substack{S\subseteq\{1,\dots,n\}\\|S|=m}}\det A_{[m],S}\;\det B_{S,[m]}", 50)
        st_sub = T("A 是 m×n，B 是 n×m（m ≤ n）。AB 是方阵，但 A、B 都不是", 24, MUTED)
        top = VGroup(st, st_sub).arrange(DOWN, buff=0.25).move_to(UP * 1.9)
        self.play(Write(st), run_time=1.6)
        self.play(FadeIn(st_sub), run_time=0.5)
        self.cap("AB 的行列式，等于 A 的 m 阶子式和 B 的对应子式乘积之和", wait=None)

        # 通道图：1 维 → C(n,m) 维 → 1 维（m = 2, n = 3）
        self.beat(4)
        L = Circle(radius=0.42, color=CYAN, stroke_width=3).move_to([-4.6, -0.55, 0])
        R = Circle(radius=0.42, color=CYAN, stroke_width=3).move_to([4.6, -0.55, 0])
        Ls = M(r"e_1\wedge e_2", 26, CYAN).move_to(L)
        Rs = M(r"e_1\wedge e_2", 26, CYAN).move_to(R)
        mids = VGroup()
        names = [r"e_1\wedge e_2", r"e_1\wedge e_3", r"e_2\wedge e_3"]
        for k, nm in enumerate(names):
            c = Circle(radius=0.42, color=MAGENTA, stroke_width=3).move_to([0, 0.6 - 1.15 * k, 0])
            mids.add(VGroup(c, M(nm, 26, MAGENTA).move_to(c)))
        hL = VGroup(M(r"\Lambda^2\mathbb{R}^2", 32, CYAN), T("1 维", 20, MUTED)).arrange(DOWN, buff=0.1).next_to(L, DOWN, buff=0.3)
        hR = VGroup(M(r"\Lambda^2\mathbb{R}^2", 32, CYAN), T("1 维", 20, MUTED)).arrange(DOWN, buff=0.1).next_to(R, DOWN, buff=0.3)
        hM = VGroup(M(r"\Lambda^2\mathbb{R}^3", 32, MAGENTA), T("3 维", 20, MUTED)).arrange(RIGHT, buff=0.2).next_to(mids, DOWN, buff=0.25)
        e_in = [Line(L.get_right(), m[0].get_left(), color=DIM, stroke_width=3) for m in mids]
        e_out = [Line(m[0].get_right(), R.get_left(), color=DIM, stroke_width=3) for m in mids]
        wB = [M(rf"\det B_{{S_{k + 1}}}", 24, LIME).move_to(e_in[k].point_from_proportion(0.55) + UP * 0.22) for k in range(3)]
        wA = [M(rf"\det A_{{S_{k + 1}}}", 24, ORANGE).move_to(e_out[k].point_from_proportion(0.45) + UP * 0.22) for k in range(3)]
        tB = VGroup(M(r"\Lambda^2B", 34, LIME)).move_to([-2.3, 1.2, 0])
        tA = VGroup(M(r"\Lambda^2A", 34, ORANGE)).move_to([2.3, 1.2, 0])
        self.play(FadeOut(st_sub), st.animate.scale(0.75).to_edge(UP, buff=1.15), run_time=0.6)
        self.play(Create(L), Write(Ls), FadeIn(hL), run_time=0.6)
        self.play(*[Create(e) for e in e_in], LaggedStart(*[FadeIn(m, scale=0.7) for m in mids], lag_ratio=0.2),
                  FadeIn(hM), FadeIn(tB), run_time=1.0)
        self.play(*[Create(e) for e in e_out], Create(R), Write(Rs), FadeIn(hR), FadeIn(tA), run_time=1.0)
        self.play(*[FadeIn(w) for w in wB + wA], run_time=0.6)
        self.cap("以 m = 2, n = 3 为例：B 把一维的 Λ²ℝ² 送进三维的 Λ²ℝ³，A 再送回一维", wait=None)
        self.beat(2)
        for k in range(3):
            path = VMobject().set_points_as_corners([L.get_right(), mids[k][0].get_left(), mids[k][0].get_right(),
                                                     R.get_left()])
            path.set_stroke(GOLD, 7)
            self.hit()
            self.play(ShowPassingFlash(path, time_width=0.6), Indicate(mids[k], color=GOLD), run_time=1.0)
        self.cap("合起来乘的倍数 = 每条通道上“B 的子式 × A 的子式”之和——这就是柯西–比内", wait=None)
        pf = M(r"\det(AB)=\Lambda^m(AB)=\Lambda^mA\circ\Lambda^mB", 44, GOLD).move_to(st)
        pfb = panel(pf, pad=0.2, color=GOLD)
        self.play(FadeOut(st, shift=UP * 0.2), FadeIn(pfb), Write(pf), run_time=1.0)
        self.cap("证明只有一行：一维 → C(n,m) 维 → 一维，两个矩阵相乘时自然是求和", wait=None)
        self.beat(4)
        self.clear_all(keep=[self._hdr])

        # 推论：拉格朗日恒等式与柯西–施瓦茨
        tag = pill("推论", GOLD, 22).move_to([-5.7, 2.2, 0])
        c0 = M(r"A=\begin{pmatrix}a_1&a_2&\cdots&a_n\\ b_1&b_2&\cdots&b_n\end{pmatrix},\qquad B=A^{\mathsf T}", 40)
        c1 = M([r"\det(AA^{\mathsf T})", "=", r"\begin{vmatrix} a\cdot a & a\cdot b\\ a\cdot b & b\cdot b\end{vmatrix}", "=",
                r"|a|^2|b|^2-(a\cdot b)^2"], 42)
        c2 = M(["=", r"\sum_{i<j}(a_ib_j-a_jb_i)^2", r"\;\ge 0"], 46)
        C_ = VGroup(c0, c1, c2).arrange(DOWN, buff=0.45).move_to(UP * 0.4)
        c2.shift(RIGHT * (c1[3].get_x() - c2[0].get_x()))
        c2[2].set_color(GOLD)
        self.play(FadeIn(tag), Write(c0), run_time=1.2)
        self.cap("取 A 为两个向量 a、b 排成的 2×n 矩阵，B 取它的转置", wait=None)
        self.beat(2)
        self.play(Write(c1), run_time=1.6)
        self.wait(1.5)
        self.cap("左边按定义算；右边用柯西–比内：每个 2 阶子式平方后相加", wait=0)
        self.play(Write(c2), run_time=1.3)
        self.wait(2.0)
        res = M(r"(a\cdot b)^2\le |a|^2\,|b|^2", 60, GOLD)
        rb = result_box(res, GOLD, pad=0.3)
        name = T("柯西–施瓦茨不等式", 28, GOLD, bold=True)
        VGroup(rb, res).move_to(DOWN * 2.2)
        name.next_to(rb, RIGHT, buff=0.4)
        self.beat(4)
        self.hit("impact")
        self.play(FadeIn(rb), Write(res), FadeIn(name, shift=LEFT * 0.2), run_time=1.0)
        self.play(ring_pulse(res.get_center(), GOLD, 3), run_time=0.7)
        self.cap("柯西–施瓦茨不等式，变成了“平方和非负”；取等号当且仅当所有子式为 0，即 a、b 平行", wait=None)
        self.clear_all()
        self.finish()


class Pythagoras(B3D):
    CHAPTER = 3
    TITLE = "面积的勾股定理"

    def construct(self):
        self.set_camera_orientation(phi=62 * DEGREES, theta=38 * DEGREES)
        self.header()
        S = 1.05
        X0 = np.array([-1.3, -1.3, -1.2])   # 坐标原点在画面里的位置

        def P(x, y, z):
            return X0 + S * np.array([x, y, z], float)

        L = 3.4
        walls = VGroup(
            Polygon(P(0, 0, 0), P(L, 0, 0), P(L, L, 0), P(0, L, 0), stroke_color=DIM, stroke_width=1, fill_color=CYAN,
                    fill_opacity=0.05),
            Polygon(P(0, 0, 0), P(0, L, 0), P(0, L, L), P(0, 0, L), stroke_color=DIM, stroke_width=1, fill_color=MAGENTA,
                    fill_opacity=0.05),
            Polygon(P(0, 0, 0), P(L, 0, 0), P(L, 0, L), P(0, 0, L), stroke_color=DIM, stroke_width=1, fill_color=LIME,
                    fill_opacity=0.05),
        )
        axes = VGroup(Line(P(0, 0, 0), P(L, 0, 0), color=MUTED, stroke_width=2),
                      Line(P(0, 0, 0), P(0, L, 0), color=MUTED, stroke_width=2),
                      Line(P(0, 0, 0), P(0, 0, L), color=MUTED, stroke_width=2))
        self.play(Create(axes), FadeIn(walls), run_time=1.0)
        self.begin_ambient_camera_rotation(rate=0.02)
        q0 = np.array([0.8, 0.3, 2.6])
        v1 = np.array([2.0, 0.0, -1.333])
        v2 = np.array([0.37, 1.85, -1.17])
        quad = [q0, q0 + v1, q0 + v1 + v2, q0 + v2]
        par = Polygon(*[P(*q) for q in quad], stroke_color=GOLD, stroke_width=3, fill_color=GOLD, fill_opacity=0.45)
        A1 = vec3(P(*q0), P(*(q0 + v1)), CYAN)
        A2 = vec3(P(*q0), P(*(q0 + v2)), MAGENTA)
        self.play(Create(A1), Create(A2), run_time=0.8)
        self.play(FadeIn(par), run_time=0.6)
        self.cap("三维空间里两个向量张成的平行四边形，面积是多少？", wait=None)

        projs = [
            (lambda q: P(q[0], q[1], 0), CYAN, r"A_{xy}", 0),
            (lambda q: P(0, q[1], q[2]), MAGENTA, r"A_{yz}", 1),
            (lambda q: P(q[0], 0, q[2]), LIME, r"A_{zx}", 2),
        ]
        cross = np.cross(v1, v2)
        vals = [abs(cross[2]), abs(cross[0]), abs(cross[1])]
        shadows = VGroup()
        self.beat(2)
        for (f, c, nm, k) in projs:
            sh = Polygon(*[f(q) for q in quad], stroke_color=c, stroke_width=2.5, fill_color=c, fill_opacity=0.4)
            drops = VGroup(*[DashedLine(P(*q), f(q), color=c, stroke_width=1.5, dash_length=0.08) for q in quad])
            self.hit()
            self.play(Create(drops), run_time=0.6)
            self.play(TFC(par, sh), run_time=1.0)
            self.play(FadeOut(drops), run_time=0.3)
            shadows.add(sh)
        self.cap("把它投影到三个坐标平面上，得到三个影子", wait=None)

        # 数字面板
        rows = VGroup()
        for (f, c, nm, k), val in zip(projs, vals):
            rows.add(VGroup(M(nm, 34, c), M(rf"= {val:.2f}", 34, c)).arrange(RIGHT, buff=0.15))
        total = np.linalg.norm(cross)
        eq = M(rf"{vals[0]:.2f}^2+{vals[1]:.2f}^2+{vals[2]:.2f}^2={total:.2f}^2", 34, GOLD)
        info = VGroup(rows.arrange(DOWN, aligned_edge=LEFT, buff=0.15), eq).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        info.to_corner(UR, buff=0.5).shift(DOWN * 0.9)
        ipanel = panel(info, pad=0.25, color=GOLD, opacity=0.85)
        self.fix(ipanel, info)
        self.beat(4)
        self.play(FadeIn(ipanel), FadeIn(rows), run_time=0.6)
        self.hit("impact")
        self.play(Write(eq), run_time=1.2)
        self.cap("面积的平方 = 三个影子面积的平方和：这是“面积版”的勾股定理", wait=None, t2c={"勾股定理": GOLD})

        # 证明
        pf = M(r"|v_1\wedge v_2|^2=\det(V^{\mathsf T}V)=\sum_{|S|=2}(\det V_S)^2", 40, INK)
        pfb = panel(pf, pad=0.22, color=VIOLET)
        pg = VGroup(pfb, pf).to_corner(UL, buff=0.5).shift(DOWN * 0.9)
        self.fix(pg)
        self.beat(2)
        self.play(FadeIn(pfb), Write(pf), run_time=1.3)
        self.cap("证明：面积² 是格拉姆行列式 det(VᵀV)，对它用柯西–比内，每个 det V_S 正是一个影子的面积", wait=None)
        self.cap("同理：k 维平行体的体积² = 它在所有 k 维坐标平面上投影体积的平方和", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(par, A1, A2, shadows)), FadeOut(VGroup(ipanel, info, pg)), run_time=0.8)

        # 德古阿定理
        a, b, c = 2.6, 2.2, 1.9
        Pa, Pb, Pc, O = P(a, 0, 0), P(0, b, 0), P(0, 0, c), P(0, 0, 0)
        faces = VGroup(Polygon(O, Pa, Pb, stroke_color=CYAN, stroke_width=2, fill_color=CYAN, fill_opacity=0.35),
                       Polygon(O, Pb, Pc, stroke_color=MAGENTA, stroke_width=2, fill_color=MAGENTA, fill_opacity=0.35),
                       Polygon(O, Pa, Pc, stroke_color=LIME, stroke_width=2, fill_color=LIME, fill_opacity=0.35))
        slant = Polygon(Pa, Pb, Pc, stroke_color=GOLD, stroke_width=3, fill_color=GOLD, fill_opacity=0.4)
        self.play(LaggedStart(*[FadeIn(f) for f in faces], lag_ratio=0.3), run_time=1.0)
        self.hit()
        self.play(DrawBorderThenFill(slant), run_time=1.0)
        t1 = T("德古阿定理（三维勾股定理）", 28, GOLD, bold=True)
        t2 = M(r"S^2 = S_{xy}^2+S_{yz}^2+S_{zx}^2", 40, INK)
        Sx, Sy, Sz = a * b / 2, b * c / 2, a * c / 2
        t3 = M(rf"{Sx:.2f}^2+{Sy:.2f}^2+{Sz:.2f}^2 = {math.sqrt(Sx ** 2 + Sy ** 2 + Sz ** 2):.2f}^2", 32, MUTED)
        tg = VGroup(t1, t2, t3).arrange(DOWN, aligned_edge=LEFT, buff=0.22).to_corner(UR, buff=0.5).shift(DOWN * 0.9)
        tp = panel(tg, pad=0.25, color=GOLD)
        self.fix(tp, tg)
        self.play(FadeIn(tp), FadeIn(tg), run_time=0.8)
        self.cap("直角四面体：斜面的三个影子，恰好就是另外三个直角面", wait=None)
        self.cap("所以斜面面积² = 三个直角面面积的平方和", wait=None)
        self.stop_ambient_camera_rotation()
        self.clear_all()
        self.finish()


class CharPoly(BScene):
    CHAPTER = 3
    TITLE = "特征多项式的系数"

    def construct(self):
        self.header()
        top = M([r"\det(I+tA)\;e_1\wedge e_2\wedge e_3", "=", r"(e_1+tAe_1)\wedge(e_2+tAe_2)\wedge(e_3+tAe_3)"], 42)
        top.move_to(UP * 2.3)
        self.play(Write(top), run_time=1.6)
        self.cap("把 I + tA 代进定义：每个括号里选 eⱼ 或者 tAeⱼ，一共 2³ = 8 种选法", wait=None)

        def strip(choice):
            g = VGroup()
            for j, ch in enumerate(choice):
                if ch:
                    m = M(rf"tAe_{j + 1}", 28, GOLD)
                    c = GOLD
                else:
                    m = M(rf"e_{j + 1}", 28, MUTED)
                    c = DIM
                b = RoundedRectangle(corner_radius=0.06, width=0.95, height=0.5, stroke_color=c, stroke_width=1.5,
                                     fill_color=PANEL, fill_opacity=0.9)
                g.add(VGroup(b, m.move_to(b)))
            return g.arrange(RIGHT, buff=0.08)

        groups = {0: [(0, 0, 0)], 1: [(1, 0, 0), (0, 1, 0), (0, 0, 1)], 2: [(1, 1, 0), (1, 0, 1), (0, 1, 1)],
                  3: [(1, 1, 1)]}
        results = {
            0: r"1",
            1: r"t\,(a_{11}+a_{22}+a_{33})",
            2: r"t^2\left(\begin{vmatrix}a_{11}&a_{12}\\a_{21}&a_{22}\end{vmatrix}+\begin{vmatrix}a_{11}&a_{13}\\a_{31}&a_{33}\end{vmatrix}+\begin{vmatrix}a_{22}&a_{23}\\a_{32}&a_{33}\end{vmatrix}\right)",
            3: r"t^3\det A",
        }
        cols = VGroup()
        for k in range(4):
            ss = VGroup(*[strip(c) for c in groups[k]]).arrange(DOWN, buff=0.12)
            head = VGroup(M(f"k={k}", 28, CYAN), T("个 A", 20, MUTED)).arrange(RIGHT, buff=0.1)
            cols.add(VGroup(head, ss).arrange(DOWN, buff=0.2))
        cols.arrange(RIGHT, buff=0.45, aligned_edge=UP).move_to(UP * 0.35)
        self.beat(2)
        for k in range(4):
            self.hit()
            self.play(FadeIn(cols[k][0]), LaggedStart(*[FadeIn(s, shift=DOWN * 0.15) for s in cols[k][1]], lag_ratio=0.2),
                      run_time=0.7)
        self.wait(1.0)
        self.beat(4)
        ex = M([r"Ae_1\wedge e_2\wedge e_3", "=", r"(a_{11}e_1+a_{21}e_2+a_{31}e_3)\wedge e_2\wedge e_3", "=",
                r"a_{11}\;e_1\wedge e_2\wedge e_3"], 36)
        ex.move_to(DOWN * 1.75)
        ex[4].set_color(GOLD)
        self.play(Write(ex[:3]), run_time=1.2)
        self.cap("只有一个 A 时：Ae₁ 里的 e₂、e₃ 分量撞上后面的 e₂、e₃，都被楔成 0", wait=0)
        self.wait(1.2)
        self.play(Write(ex[3:]), run_time=0.8)
        self.wait(1.8)
        self.cap("所以一个 A 的三项合起来是对角元之和；两个 A 时剩下 2 阶主子式；三个 A 就是 det A", wait=0)
        rs = M([r"\det(I+tA)=", results[0], "+", results[1], "+", results[2], "+", results[3]], 34)
        rs[1].set_color(INK)
        for k in (3, 5, 7):
            rs[k].set_color(GOLD)
        if rs.width > 13.2:
            rs.scale_to_fit_width(13.2)
        rs.move_to(DOWN * 1.9)
        self.play(FadeOut(ex), run_time=0.4)
        self.play(FadeIn(rs[:2]), run_time=0.5)
        for k in (3, 5, 7):
            self.play(FadeIn(rs[k - 1]), FadeIn(rs[k], shift=UP * 0.15), Indicate(cols[(k - 1) // 2][1], color=GOLD,
                                                                                   scale_factor=1.03), run_time=0.8)
        self.wait(3.0)
        self.beat(4)
        self.play(FadeOut(VGroup(cols, rs)), run_time=0.6)

        r1 = M([r"\det(I+tA)", "=", r"\sum_{k=0}^{n}t^k\,\operatorname{tr}\Lambda^kA"], 52)
        r1[2].set_color(GOLD)
        r2 = M([r"\operatorname{tr}\Lambda^kA", "=", r"\sum_{|S|=k}\det A_{S,S}", "=", r"e_k(\lambda_1,\dots,\lambda_n)"], 44)
        r3 = M(r"\det(xI-A)=x^n-(\operatorname{tr}A)\,x^{n-1}+(\operatorname{tr}\Lambda^2A)\,x^{n-2}-\cdots+(-1)^n\det A", 38, CYAN)
        R = VGroup(r1, r2, r3).arrange(DOWN, buff=0.5).move_to(DOWN * 0.4)
        self.hit("impact")
        rb = result_box(r1, GOLD, pad=0.25)
        self.play(FadeIn(rb), Write(r1), run_time=1.2)
        self.cap("一般的 n 阶：tᵏ 的系数是 Λᵏ A 的迹，也就是所有 k 阶主子式之和", wait=None)
        self.beat(2)
        self.play(Write(r2), run_time=1.4)
        self.cap("又因为 det(I + tA) = ∏(1 + tλᵢ)：主子式之和 = 特征值的初等对称多项式", wait=None)
        self.beat(2)
        self.play(Write(r3), run_time=1.6)
        self.cap("于是特征多项式的每个系数都有了公式：tr A = Σλᵢ，det A = ∏λᵢ 只是两头的特例", wait=None)
        self.clear_all()
        self.finish()


class Sylvester(BScene):
    CHAPTER = 3
    TITLE = "西尔维斯特恒等式"

    def construct(self):
        self.header()
        # 形状示意
        def block(w, h, c, lab):
            r = Rectangle(width=w, height=h, stroke_color=c, stroke_width=3, fill_color=c, fill_opacity=0.2)
            return VGroup(r, M(lab, 34, c).move_to(r))

        Ab = block(2.4, 0.8, CYAN, "A")
        Bb = block(0.6, 2.4, MAGENTA, "B")
        AB = VGroup(Ab, Bb).arrange(RIGHT, buff=0.15, aligned_edge=UP)
        eqAB = VGroup(AB, M("=", 40), block(0.8, 0.8, GOLD, "AB")).arrange(RIGHT, buff=0.3)
        Bb2 = block(0.6, 2.4, MAGENTA, "B")
        Ab2 = block(2.4, 0.8, CYAN, "A")
        BA = VGroup(Bb2, Ab2).arrange(RIGHT, buff=0.15, aligned_edge=UP)
        eqBA = VGroup(BA, M("=", 40), block(2.4, 2.4, VIOLET, "BA")).arrange(RIGHT, buff=0.3)
        shapes = VGroup(eqAB, eqBA).arrange(RIGHT, buff=1.4).move_to(UP * 0.9)
        self.play(FadeIn(eqAB, shift=RIGHT * 0.3), run_time=0.8)
        self.play(FadeIn(eqBA, shift=LEFT * 0.3), run_time=0.8)
        self.cap("A 是 m×n、B 是 n×m：AB 是小方阵（m×m），BA 是大方阵（n×n）", wait=None)
        st = M(r"\det(I_m+AB)=\det(I_n+BA)", 60, GOLD)
        sb = result_box(st, GOLD, pad=0.3)
        VGroup(sb, st).move_to(DOWN * 1.9)
        self.beat(4)
        self.hit("impact")
        self.play(FadeIn(sb), Write(st), run_time=1.2)
        self.cap("大小不同的两个行列式，竟然总是相等", wait=None)
        ex = M(r"A=\begin{pmatrix}1&2&0&1\\0&1&3&1\end{pmatrix},\ B=\begin{pmatrix}1&0\\2&1\\0&1\\1&1\end{pmatrix}"
               r"\ \Rightarrow\ \det(I_2+AB)=33=\det(I_4+BA)", 34, INK)
        ex.move_to(DOWN * 1.9)
        self.beat(2)
        self.play(FadeOut(VGroup(sb, st)), FadeIn(ex), run_time=0.7)
        self.cap("随便取个例子验证：一个 2 阶、一个 4 阶，算出来都是 33", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(shapes, ex)), run_time=0.6)

        lines = [
            [r"\det(I_m+tAB)", "=", r"\sum_k t^k\operatorname{tr}\Lambda^k(AB)"],
            ["=", r"\sum_k t^k\operatorname{tr}\big(\Lambda^kA\;\Lambda^kB\big)"],
            ["=", r"\sum_k t^k\operatorname{tr}\big(\Lambda^kB\;\Lambda^kA\big)"],
            ["=", r"\sum_k t^k\operatorname{tr}\Lambda^k(BA)"],
            ["=", r"\det(I_n+tBA)"],
        ]
        why = ["上一节：系数是 Λᵏ 的迹", "Λᵏ 和乘法相容", "tr(XY) = tr(YX)（长方形也成立）",
               "再用一次相容性", "上一节的公式反过来用"]
        Ls = VGroup(*[M(l, 44) for l in lines]).arrange(DOWN, buff=0.28)
        for l in Ls[1:]:
            l.shift(RIGHT * (Ls[0][1].get_x() - l[0].get_x()))
        Ls.move_to(DOWN * 0.1).shift(LEFT * 2.3)
        tags = VGroup(*[T(w, 22, MUTED) for w in why])
        for t, l in zip(tags, Ls):
            t.next_to(Ls, RIGHT, buff=0.5).set_y(l.get_y())
        Ls[2][1].set_color(GOLD)
        for i, l in enumerate(Ls):
            self.beat(2)
            self.play(Write(l), FadeIn(tags[i], shift=LEFT * 0.2), run_time=1.0)
            self.wait(1.6)
        self.hit()
        self.play(Circumscribe(Ls[2], color=GOLD), run_time=1.0)
        self.cap("整个证明的关键只是 tr(XY) = tr(YX)；外代数把它从迹“抬”到了每一个系数", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(Ls, tags)), run_time=0.6)

        c1 = VGroup(pill("推论 1", CYAN, 22), M(r"\det(I_n+uv^{\mathsf T})=1+v^{\mathsf T}u", 48)).arrange(RIGHT, buff=0.4)
        c1n = T("秩一修正的行列式：n 阶变 1 阶", 24, MUTED)
        c2 = VGroup(pill("推论 2", MAGENTA, 22), M(r"x^n\det(xI_m-AB)=x^m\det(xI_n-BA)", 48)).arrange(RIGHT, buff=0.4)
        c2n = T("AB 和 BA 的非零特征值（连同重数）完全相同", 24, MUTED)
        CC = VGroup(c1, c1n, c2, c2n).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(DOWN * 0.2)
        c1n.shift(RIGHT * 1.5)
        c2n.shift(RIGHT * 1.5)
        self.beat(2)
        self.hit()
        self.play(FadeIn(c1, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(c1n), run_time=0.4)
        self.wait(2.0)
        self.beat(2)
        self.hit()
        self.play(FadeIn(c2, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(c2n), run_time=0.4)
        self.cap("两个推论都在机器学习、统计、矩阵分析里天天用到", wait=None)
        self.clear_all()
        self.finish()


class PluckerAlg(BScene):
    CHAPTER = 3
    TITLE = "普吕克关系：用一个 2-向量记住一张平面"

    def construct(self):
        self.header()
        a1 = M([r"W=\operatorname{span}(v,w)\subset\mathbb{R}^4", r"\quad\longmapsto\quad", r"v\wedge w\in\Lambda^2\mathbb{R}^4\cong\mathbb{R}^6"], 42)
        a2 = M(r"(v',w')=(v,w)\begin{pmatrix}\alpha&\beta\\\gamma&\delta\end{pmatrix}\ \Rightarrow\ v'\wedge w'=(\alpha\delta-\beta\gamma)\,v\wedge w", 38)
        a3 = M(r"v\wedge w=\sum_{i<j}p_{ij}\,e_i\wedge e_j,\qquad p_{ij}=v_iw_j-v_jw_i", 42, CYAN)
        A = VGroup(a1, a2, a3).arrange(DOWN, buff=0.5).move_to(UP * 0.7)
        self.play(Write(a1), run_time=1.5)
        self.cap("ℝ⁴ 里的一张二维平面，取一组基 v、w，记下 v∧w", wait=None)
        self.beat(2)
        self.play(Write(a2), run_time=1.6)
        self.cap("换一组基，v∧w 只差一个倍数（正是换基矩阵的行列式）——所以平面 ↔ v∧w 所在的直线", wait=None)
        self.beat(2)
        self.play(Write(a3), run_time=1.3)
        self.cap("它的 6 个坐标 pᵢⱼ 叫普吕克坐标：平面变成了 6 维空间里的一个点（差一个倍数）", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(a1, a2)), a3.animate.scale(0.8).to_edge(UP, buff=1.2), run_time=0.7)

        b1 = M([r"\omega\wedge\omega", "=", r"\sum_{i<j}\sum_{k<l}p_{ij}p_{kl}\;e_i\wedge e_j\wedge e_k\wedge e_l"], 42)
        b2 = M(["=", r"2\,\big(p_{12}p_{34}-p_{13}p_{24}+p_{14}p_{23}\big)", r"\;e_1\wedge e_2\wedge e_3\wedge e_4"], 42)
        b3 = M([r"(v\wedge w)\wedge(v\wedge w)", "=", "0"], 42)
        B = VGroup(b3, b1, b2).arrange(DOWN, buff=0.42).move_to(DOWN * 0.2)
        b2.shift(RIGHT * (b1[1].get_x() - b2[0].get_x()))
        self.cap("反过来：任给一个 2-向量 ω，它什么时候能写成 v∧w？", wait=None)
        self.beat(2)
        self.play(Write(b3), run_time=1.0)
        self.cap("如果 ω = v∧w，那 ω∧ω 里 v 出现两次，一定是 0", wait=None)
        self.beat(2)
        self.play(Write(b1), run_time=1.4)
        self.wait(1.2)
        self.play(Write(b2), run_time=1.4)
        self.cap("展开 ω∧ω：只有下标凑齐 1,2,3,4 的三对留下，符号由排列的奇偶决定", wait=None)
        res = M(r"p_{12}\,p_{34}-p_{13}\,p_{24}+p_{14}\,p_{23}=0", 58, GOLD)
        rb = result_box(res, GOLD, pad=0.3)
        VGroup(rb, res).move_to(DOWN * 2.45)
        self.beat(4)
        self.hit("impact")
        self.play(FadeIn(rb), Write(res), run_time=1.0)
        self.play(light_sweep(res), run_time=0.8)
        self.cap("普吕克关系：6 个坐标满足一个二次方程。反过来，满足它的 ω 一定可以写成 v∧w", wait=None)
        self.beat(2)
        cex = M(r"\omega=e_1\wedge e_2+e_3\wedge e_4:\quad \omega\wedge\omega=2\,e_1\wedge e_2\wedge e_3\wedge e_4\neq0", 38, RED)
        cex.next_to(rb, UP, buff=0.3)
        self.play(FadeOut(B), FadeIn(cex, shift=UP * 0.2), run_time=0.8)
        self.cap("反例：e₁∧e₂ + e₃∧e₄ 不是任何平面——它是两张平面“叠”在一起，拆不开", wait=None)
        self.clear_all()
        self.finish()


class PluckerLines(B3D):
    CHAPTER = 3
    TITLE = "空间直线的普吕克坐标"

    def construct(self):
        self.set_camera_orientation(phi=64 * DEGREES, theta=-48 * DEGREES)
        self.header()
        axes = ThreeDAxes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[-2.2, 2.2, 1], x_length=6, y_length=6,
                          z_length=4.4, axis_config={"stroke_color": DIM, "stroke_width": 2, "include_tip": False})
        self.play(Create(axes), run_time=0.8)
        self.begin_ambient_camera_rotation(rate=0.03)
        txt = VGroup(T("把射影空间里的点写成 (1, P)、方向写成 (0, d)，", 24, INK),
                     M(r"(1,P)\wedge(0,d)\ \longmapsto\ (d\,;\ m),\qquad m=P\times d", 36, CYAN),
                     M(r"p_{12}p_{34}-p_{13}p_{24}+p_{14}p_{23}=0\iff d\cdot m=0", 36, GOLD))
        txt.arrange(DOWN, buff=0.25, aligned_edge=LEFT).to_corner(UL, buff=0.5).shift(DOWN * 0.85)
        tp = panel(txt, pad=0.22, color=CYAN, opacity=0.85)
        self.fix(tp, txt)
        self.play(FadeIn(tp), FadeIn(txt[0]), run_time=0.6)
        self.play(Write(txt[1]), run_time=1.2)
        self.cap("ℝ⁴ 里的二维平面 = 三维空间里的一条直线（射影几何）。直线也有普吕克坐标", wait=None)

        Pt = ValueTracker(0)

        def params():
            a = Pt.get_value()
            P = np.array([1.2 * math.cos(a), 1.0 * math.sin(1.3 * a) - 0.3, 0.6 * math.cos(0.7 * a)])
            d = normalize(np.array([math.cos(0.8 * a + 1), math.sin(0.5 * a), 0.6 * math.sin(a + 0.5) + 0.2]))
            return P, d

        def line():
            P, d = params()
            return Line(P - 3.2 * d, P + 3.2 * d, color=MAGENTA, stroke_width=4)

        def pdot():
            P, d = params()
            return VGroup(Dot3D(P, radius=0.07, color=GOLD, resolution=(8, 8)), vec3(P, P + 1.2 * d, LIME))

        def mvec():
            P, d = params()
            m = np.cross(P, d)
            return vec3(ORIGIN, m * 1.3, ORANGE)

        def plane():
            P, d = params()
            return Polygon(ORIGIN, P - 3 * d, P + 3 * d, stroke_width=0, fill_color=MAGENTA, fill_opacity=0.12)

        Lm = always_redraw(line)
        Dm = always_redraw(pdot)
        Mm = always_redraw(mvec)
        Pl = always_redraw(plane)
        self.play(FadeIn(Pl), Create(Lm), FadeIn(Dm), run_time=1.0)
        self.bring_to_front(tp, txt, *self._hdr, self._cap or VGroup())
        self.cap("一条直线：过点 P（金），方向 d（绿）", wait=None)
        self.beat(2)
        self.play(FadeIn(Mm), run_time=0.6)
        self.cap("矩向量 m = P × d（橙）垂直于直线和原点所在的平面——无论 P 取直线上哪一点都一样", wait=None)

        cam = self.renderer.camera

        def live(fn, color, size=30):
            n = DecimalNumber(fn(), num_decimal_places=2, include_sign=True, font_size=size, color=color)

            def upd(m):
                c = m.get_center()
                m.set_value(fn() + 0.0)
                m.move_to(c)
                cam.add_fixed_in_frame_mobjects(m)

            n.add_updater(upd)
            return n

        def comps(vecfn, color):
            return VGroup(*[live(lambda i=i: round(float(vecfn()[i]), 2), color) for i in range(3)]).arrange(RIGHT, buff=0.25)

        dv = comps(lambda: params()[1], LIME)
        mv = comps(lambda: np.cross(*params()), ORANGE)
        num = live(lambda: round(float(np.dot(params()[1], np.cross(*params()))), 3), GOLD, 40)
        rd = VGroup(VGroup(M("d=", 34, LIME), dv).arrange(RIGHT, buff=0.15),
                    VGroup(M("m=", 34, ORANGE), mv).arrange(RIGHT, buff=0.15),
                    VGroup(M(r"d\cdot m=", 40, GOLD), num).arrange(RIGHT, buff=0.2))
        rd.arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UR, buff=0.6).shift(DOWN * 0.9)
        rdp = panel(rd, pad=0.22, color=GOLD)
        self.fix(rdp, rd)
        self.beat(2)
        self.play(FadeIn(rdp), FadeIn(rd), Write(txt[2]), run_time=1.0)
        self.bring_to_front(rdp, rd)
        self.hit()
        self.play(Pt.animate.set_value(5.0), run_time=7.0, rate_func=linear)
        self.cap("直线怎么动，d·m 永远是 0：这正是普吕克关系换了个写法", wait=None)
        self.play(Pt.animate.set_value(8.0), run_time=4.0, rate_func=linear)
        self.cap("所有空间直线组成五维射影空间里的一个二次曲面——克莱因二次曲面", wait=None,
                 t2c={"克莱因二次曲面": GOLD})
        self.stop_ambient_camera_rotation()
        self.clear_all()
        self.finish()


class Forms(BScene):
    CHAPTER = 3
    TITLE = "微分形式：换元公式里的雅可比"

    def construct(self):
        self.header()
        # 极坐标网格
        C = np.array([-4.3, -0.9, 0])
        rings = VGroup(*[Circle(radius=r, color=CYAN, stroke_width=1.5, stroke_opacity=0.5).move_to(C)
                         for r in np.arange(0.5, 2.76, 0.5)])
        rays = VGroup(*[Line(C, C + 2.75 * np.array([math.cos(a), math.sin(a), 0]), color=CYAN, stroke_width=1.5,
                             stroke_opacity=0.5) for a in np.arange(0, TAU, PI / 8)])
        self.play(Create(rings, lag_ratio=0.1), Create(rays, lag_ratio=0.05), run_time=1.4)
        r0, dr, t0, dt = 2.0, 0.5, PI / 8 * 2, PI / 8
        cell = AnnularSector(inner_radius=r0, outer_radius=r0 + dr, angle=dt, start_angle=t0, fill_color=GOLD,
                             fill_opacity=0.5, stroke_color=GOLD, stroke_width=2.5).move_arc_center_to(C)
        self.play(FadeIn(cell), run_time=0.6)
        bd = BraceBetweenPoints(C + r0 * np.array([math.cos(t0), math.sin(t0), 0]),
                                C + (r0 + dr) * np.array([math.cos(t0), math.sin(t0), 0]), direction=np.array([math.sin(t0), -math.cos(t0), 0]),
                                color=MAGENTA)
        lr = M("dr", 30, MAGENTA).next_to(bd, np.array([math.sin(t0), -math.cos(t0), 0]), buff=0.05)
        ar = Arc(radius=r0 + dr + 0.15, start_angle=t0, angle=dt, color=LIME, stroke_width=3).move_arc_center_to(C)
        la = M(r"r\,d\theta", 30, LIME).move_to(C + (r0 + dr + 0.55) * np.array([math.cos(t0 + dt / 2), math.sin(t0 + dt / 2), 0]))
        self.play(GrowFromCenter(bd), FadeIn(lr), Create(ar), FadeIn(la), run_time=0.8)
        self.cap("极坐标下的小面积元是 r dr dθ。这个 r 从哪来？让楔积自己算", wait=None)

        x0 = 0.6
        L = [
            M(r"x=r\cos\theta,\qquad y=r\sin\theta", 38),
            M(r"dx=\cos\theta\,dr-r\sin\theta\,d\theta", 38, CYAN),
            M(r"dy=\sin\theta\,dr+r\cos\theta\,d\theta", 38, MAGENTA),
        ]
        G = VGroup(*L).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([2.9, 1.7, 0])
        for l in L:
            self.play(Write(l), run_time=0.9)
        self.wait(1.2)
        e1 = M([r"dx\wedge dy", "=", r"\cos\theta\sin\theta\;dr\wedge dr", "+", r"r\cos^2\theta\;dr\wedge d\theta"], 36)
        e1b = M(["-", r"r\sin^2\theta\;d\theta\wedge dr", "-", r"r^2\sin\theta\cos\theta\;d\theta\wedge d\theta"], 36)
        e2 = M(["=", r"r\,(\cos^2\theta+\sin^2\theta)\;dr\wedge d\theta", "=", r"r\;dr\wedge d\theta"], 38)
        E = VGroup(e1, e1b, e2).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        e1b.shift(RIGHT * (e1[2].get_left()[0] - e1b[1].get_left()[0]))
        e2.shift(RIGHT * (e1[1].get_x() - e2[0].get_x()))
        if E.width > 8.2:
            E.scale_to_fit_width(8.2)
        E.next_to(G, DOWN, buff=0.45).to_edge(RIGHT, buff=0.35)
        e2[3].set_color(GOLD)
        self.beat(2)
        self.play(Write(e1), run_time=1.3)
        self.play(Write(e1b), run_time=1.2)
        self.cap("dr∧dr = dθ∧dθ = 0，dθ∧dr = −dr∧dθ", wait=0)
        self.hit()
        s1, s2 = strike(e1[2]), strike(e1b[3])
        self.play(Create(s1), Create(s2), burst(e1[2].get_center(), RED, n=16), burst(e1b[3].get_center(), RED, n=16),
                  run_time=0.8)
        self.play(Write(e2), run_time=1.4)
        self.hit("impact")
        self.play(Circumscribe(e2[3], color=GOLD), ring_pulse(cell.get_center(), GOLD, 1.5), run_time=1.0)
        self.cap("r 自己冒了出来——它就是雅可比行列式", wait=None, t2c={"雅可比行列式": GOLD})
        self.beat(4)
        self.clear_all(keep=[self._hdr])

        j = M(r"dy_1\wedge\cdots\wedge dy_n=\det\!\Big(\frac{\partial y_i}{\partial x_j}\Big)\;dx_1\wedge\cdots\wedge dx_n", 50)
        jb = result_box(j, GOLD, pad=0.3)
        VGroup(jb, j).move_to(UP * 1.4)
        jn = T("每个 dyᵢ = Σⱼ (∂yᵢ/∂xⱼ) dxⱼ，楔起来就是第二章的行列式定义", 26, MUTED).next_to(jb, DOWN, buff=0.3)
        self.hit()
        self.play(FadeIn(jb), Write(j), run_time=1.3)
        self.play(FadeIn(jn), run_time=0.5)
        self.cap("一般的换元公式里的雅可比行列式，就是楔积自动算出来的", wait=None)

        # 斯托克斯
        self.beat(4)
        cards = [
            ("牛顿–莱布尼茨", r"\int_a^b f'\,dx=f(b)-f(a)", CYAN),
            ("格林公式", r"\oint_{\partial D}P\,dx+Q\,dy=\iint_D(Q_x-P_y)\,dx\wedge dy", MAGENTA),
            ("高斯公式", r"\oint_{\partial V}\mathbf F\cdot d\mathbf S=\iiint_V\nabla\cdot\mathbf F\,dV", LIME),
            ("斯托克斯公式", r"\oint_{\partial S}\mathbf F\cdot d\mathbf r=\iint_S(\nabla\times\mathbf F)\cdot d\mathbf S", ORANGE),
        ]
        cg = VGroup()
        for name, tex, c in cards:
            f = M(tex, 30)
            if f.width > 5.6:
                f.scale_to_fit_width(5.6)
            g = VGroup(T(name, 22, c, bold=True), f).arrange(DOWN, buff=0.15)
            box = RoundedRectangle(corner_radius=0.1, width=6.2, height=1.4, fill_color=PANEL, fill_opacity=0.88,
                                   stroke_color=c, stroke_width=2)
            cg.add(VGroup(box, g.move_to(box)))
        cg.arrange_in_grid(2, 2, buff=(0.3, 0.3)).move_to(DOWN * 1.3)
        self.play(FadeOut(jn), VGroup(jb, j).animate.scale(0.6).to_edge(UP, buff=1.15), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cg], lag_ratio=0.25), run_time=1.6)
        self.cap("微积分里的四大公式，看起来各不相同……", wait=None)
        st = M(r"\int_M d\omega=\int_{\partial M}\omega", 84, GOLD)
        stg = glow(st.copy().set_fill(opacity=0).set_stroke(GOLD, 3), GOLD, 3, layers=2, opacity=0.3)
        stg.move_to(DOWN * 0.9)
        st.move_to(DOWN * 0.9)
        self.beat(4)
        self.hit("impact")
        self.play(*[c.animate.move_to(st.get_center()).scale(0.1).set_opacity(0) for c in cg], run_time=0.8)
        self.remove(*cg)
        self.play(Write(st), FadeIn(stg), burst(st.get_center(), GOLD, n=50, radius=4), run_time=1.2)
        self.cap("……在微分形式的语言里是同一个公式：广义斯托克斯定理", wait=None, t2c={"广义斯托克斯定理": GOLD})
        self.cap("而 d∘d = 0 一行就包含了“梯度无旋、旋度无源”——外代数从线性代数一路通到了微积分", wait=None)
        self.clear_all()
        self.finish()
