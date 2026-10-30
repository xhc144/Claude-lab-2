# -*- coding: utf-8 -*-
"""第一章 什么是外代数：有向面积 → 三条规则 → k-向量 → 基底与符号 → 第一次计算。"""
from common import *


class Card1(ChapterCard):
    N = 1


def rot2(p, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([c * p[0] - s * p[1], s * p[0] + c * p[1], 0.0])


class AreaAlgebra(BScene):
    CHAPTER = 1
    TITLE = "面积的代数"

    def construct(self):
        self.header()
        O = np.array([-5.7, -2.5, 0])
        v0 = np.array([2.9, 0.6, 0])
        w0 = np.array([1.0, 2.5, 0])
        vs = ValueTracker(1.0)   # v 的伸缩
        sh = ValueTracker(0.0)   # w 沿 v 方向的剪切
        th = ValueTracker(0.0)   # w 的转角
        tw = ValueTracker(0.001)
        tv = ValueTracker(0.001)

        def V():
            return v0 * vs.get_value() * tv.get_value()

        def W():
            return (rot2(w0, th.get_value()) + sh.get_value() * v0) * tw.get_value()

        def det():
            a, b = V(), W()
            return a[0] * b[1] - a[1] * b[0]

        P = always_redraw(lambda: para(O, V(), W(), GOLD, opacity=0.4, fill=[CYAN, MAGENTA]))
        A = always_redraw(lambda: vec(O, O + V(), CYAN, width=6))
        B = always_redraw(lambda: vec(O, O + W(), MAGENTA, width=6))
        lv = always_redraw(lambda: M("v", 44, CYAN).move_to(O + V() + normalize(V() + 1e-9) * 0.35 + DOWN * 0.15))
        lw = always_redraw(lambda: M("w", 44, MAGENTA).move_to(O + W() + normalize(W() + 1e-9) * 0.35 + LEFT * 0.1))

        def arc():
            d = det()
            c = O + (V() + W()) / 2
            if abs(d) < 0.25:
                return VGroup()
            return orient_arc(c, 0.32, d > 0, GOLD if d > 0 else RED)

        OA = always_redraw(arc)
        self.add(P, A, B)
        self.play(tv.animate.set_value(1), run_time=0.8, rate_func=rush_from)
        self.add(lv)
        self.play(tw.animate.set_value(1), run_time=0.8, rate_func=rush_from)
        self.add(lw, OA)

        # 面积读数
        lab = T("有向面积", 26, MUTED)
        num = DecimalNumber(det(), num_decimal_places=2, include_sign=True, font_size=52, color=GOLD)
        num.add_updater(lambda m: m.set_value(det()).set_color(GOLD if det() > 0.005 else (RED if det() < -0.005 else INK)))
        readout = VGroup(lab, num).arrange(RIGHT, buff=0.3).move_to([-4.2, 2.35, 0])
        num.add_updater(lambda m: m.next_to(lab, RIGHT, buff=0.3))
        self.play(FadeIn(readout, shift=DOWN * 0.2), run_time=0.6)
        self.cap("两个向量张成一个平行四边形。它的面积，是这两个向量的函数", wait=None)

        # 规则板
        board_t = T("面积满足的规律", 28, INK, bold=True)
        rows = [
            ("伸缩", r"(2v)\wedge w = 2\,(v\wedge w)", CYAN),
            ("剪切", r"v\wedge (w+t\,v) = v\wedge w", LIME),
            ("退化", r"v\wedge v = 0", ORANGE),
            ("反号", r"w\wedge v = -\,v\wedge w", RED),
        ]
        items = VGroup()
        for name, tex, c in rows:
            items.add(VGroup(pill(name, c, 20), M(tex, 36)).arrange(RIGHT, buff=0.3))
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        board = VGroup(board_t, items).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        board.to_edge(RIGHT, buff=0.75).set_y(0.15)
        bpanel = panel(board, pad=0.4, color=VIOLET)
        self.play(FadeIn(bpanel), FadeIn(board_t), run_time=0.6)
        notation = VGroup(T("记作", 26, MUTED), M(r"v\wedge w", 46, GOLD)).arrange(RIGHT, buff=0.25)
        notation.next_to(readout, DOWN, buff=0.25, aligned_edge=LEFT)
        self.play(Write(notation), run_time=0.8)
        self.cap("它叫 v 楔 w：一块带方向的面积（逆时针为正）", wait=None, t2c={"v 楔 w": GOLD})

        # 1 伸缩
        self.beat(2)
        self.cap("把 v 拉长到 2 倍，面积也变成 2 倍", t2c={"2 倍": CYAN})
        self.play(vs.animate.set_value(2), run_time=1.6)
        self.hit()
        self.play(FadeIn(items[0], shift=LEFT * 0.3), run_time=0.6)
        self.wait(1.2)
        self.play(vs.animate.set_value(1), run_time=1.0)

        # 2 剪切
        self.beat(2)
        self.cap("让 w 沿着 v 的方向滑动：底不变、高不变，面积不变", t2c={"面积不变": LIME})
        base_line = always_redraw(lambda: DashedLine(O + W() - 3 * v0, O + W() + 3 * v0, color=LIME,
                                                     stroke_width=2, dash_length=0.1).set_opacity(0.6))
        self.play(FadeIn(base_line), run_time=0.4)
        self.play(sh.animate.set_value(1.1), run_time=1.6)
        self.play(sh.animate.set_value(-0.8), run_time=2.0)
        self.play(sh.animate.set_value(0), run_time=1.2)
        self.hit()
        self.play(FadeIn(items[1], shift=LEFT * 0.3), FadeOut(base_line), run_time=0.6)
        self.wait(1.0)

        # 3 退化
        self.beat(2)
        self.cap("把 w 转到和 v 同一条直线上：平行四边形被压扁，面积为 0", t2c={"面积为 0": ORANGE})
        ang_w = math.atan2(w0[1], w0[0])
        ang_v = math.atan2(v0[1], v0[0])
        self.play(th.animate.set_value(ang_v - ang_w), run_time=2.0)
        self.hit()
        self.play(burst(O + v0 * 0.9, ORANGE, n=30, radius=1.4), FadeIn(items[2], shift=LEFT * 0.3), run_time=0.8)
        self.wait(1.2)

        # 4 反号
        self.beat(2)
        self.cap("继续转过去，绕行方向变成顺时针——面积变成负数", t2c={"负数": RED})
        self.play(th.animate.set_value(ang_v - ang_w - 0.75), run_time=1.8)
        self.wait(1.2)
        self.play(th.animate.set_value(0), run_time=1.5)
        self.cap("交换先后顺序也一样：从 w 转向 v 是顺时针，所以 w∧v = −v∧w", wait=None,
                 t2c={"w∧v = −v∧w": RED})
        self.hit()
        self.play(FadeIn(items[3], shift=LEFT * 0.3), run_time=0.6)
        self.play(Indicate(items[3][1], color=RED), run_time=0.8)
        self.wait(1.0)

        # 收尾
        self.beat(4)
        self.play(*[Circumscribe(it, color=VIOLET, time_width=0.6) for it in items], run_time=1.2)
        self.cap("把这些规律抽出来，当作运算规则——这就是外代数", wait=None, t2c={"外代数": GOLD})
        self.clear_all()
        self.finish()


class Rules(BScene):
    CHAPTER = 1
    TITLE = "三条规则"

    def construct(self):
        self.header()
        head = VGroup(T("外代数", 34, GOLD, bold=True), M(r"\Lambda(V)", 44, GOLD),
                      T("：向量可以“楔”在一起，只要求", 30, INK)).arrange(RIGHT, buff=0.2)
        head.move_to(UP * 2.3)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.7)
        rules = [
            ("①", "双线性", r"(a u+b v)\wedge w = a\,u\wedge w+b\,v\wedge w", CYAN, "每个位置上都可以像乘法一样展开"),
            ("②", "结合律", r"(u\wedge v)\wedge w = u\wedge (v\wedge w)", MAGENTA, "括号可以去掉，写成 u∧v∧w"),
            ("③", "交错性", r"v\wedge v = 0", GOLD, "同一个向量楔两次，得 0"),
        ]
        cards = VGroup()
        for num, name, tex, c, note in rules:
            n = EN(num, 34, c)
            nm = T(name, 30, c, bold=True)
            f = M(tex, 42)
            nt = T(note, 22, MUTED)
            left = VGroup(n, nm).arrange(RIGHT, buff=0.2)
            right = VGroup(f, nt).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            row = VGroup(left, right).arrange(RIGHT, buff=0.6)
            cards.add(row)
        for r in cards:
            r[1].align_to(cards[0][1], LEFT)
        cards.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(DOWN * 0.35)
        for r in cards:
            r[1].set_x(cards[0][1].get_x()).align_to(cards[0][1], LEFT)
        pn = panel(cards, pad=0.4, color=VIOLET)
        self.play(FadeIn(pn), run_time=0.4)
        for i, r in enumerate(cards):
            self.beat(2)
            self.hit()
            self.play(FadeIn(r[0], shift=RIGHT * 0.3), Write(r[1][0]), run_time=0.9)
            self.play(FadeIn(r[1][1]), run_time=0.4)
            self.wait(2.0)
        self.cap("就这三条。没有别的公理，下面的一切都由它们推出来", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(pn, cards)), head.animate.scale(0.75).move_to(UP * 2.55), run_time=0.7)

        # 推论 1：反交换
        tag1 = pill("推论 1", CYAN, 22).move_to([-5.6, 1.7, 0])
        l0 = M([r"0", r"=", r"(v+w)\wedge(v+w)"], 46)
        l1 = M([r"=", r"v\wedge v", "+", r"v\wedge w", "+", r"w\wedge v", "+", r"w\wedge w"], 46)
        l2 = M([r"=", r"v\wedge w", "+", r"w\wedge v"], 46)
        lines = VGroup(l0, l1, l2).arrange(DOWN, buff=0.4)
        for l in (l1, l2):
            l.shift(RIGHT * (l0[1].get_x() - l[0].get_x()))
        l1.align_to(l0[1], LEFT)
        l2.align_to(l0[1], LEFT)
        lines.move_to([0.6, 0.2, 0])
        self.play(FadeIn(tag1), run_time=0.4)
        self.cap("先看看规则 ③ 能推出什么：把 v + w 和自己楔一下", wait=0)
        self.play(Write(l0), run_time=1.2)
        self.wait(1.5)
        self.play(TFC(l0[2], l1[1:]), FadeIn(l1[0]), run_time=1.2)
        self.cap("按双线性展开成四项", wait=1.6)
        self.beat(2)
        self.cap("v∧v 和 w∧w 按规则 ③ 都是 0", wait=0, t2c={"0": GOLD})
        self.hit()
        s1, s2 = strike(l1[1]), strike(l1[7])
        self.play(Create(s1), Create(s2), burst(l1[1].get_center(), RED, n=20, radius=0.8),
                  burst(l1[7].get_center(), RED, n=20, radius=0.8), run_time=0.8)
        self.play(TFC(VGroup(l1[0], l1[3], l1[4], l1[5]), l2), run_time=1.0)
        self.wait(1.5)
        res = M(r"w\wedge v = -\,v\wedge w", 56, GOLD)
        res_box = result_box(res, GOLD)
        VGroup(res_box, res).next_to(lines, DOWN, buff=0.55)
        self.beat(2)
        self.hit("impact")
        self.play(FadeIn(res_box), Write(res), run_time=0.9)
        self.play(ring_pulse(res.get_center(), GOLD, 2.5), run_time=0.7)
        self.cap("于是交换两个向量就变号——“反号”不需要单独假设", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(l0, l1, l2, s1, s2, tag1)), VGroup(res_box, res).animate.scale(0.6).to_corner(UR).shift(DOWN * 1.1),
                  run_time=0.7)

        # 推论 2：线性相关 ⇒ 0
        tag2 = pill("推论 2", MAGENTA, 22).move_to([-5.6, 1.7, 0])
        m0 = M([r"w", "=", r"a\,u+b\,v"], 46)
        m1 = M([r"u\wedge v\wedge w", "=", r"a\,u\wedge v\wedge u", "+", r"b\,u\wedge v\wedge v"], 46)
        m2 = M([r"=", r"-a\,u\wedge u\wedge v", "+", r"0", "=", "0"], 46)
        mm = VGroup(m0, m1, m2).arrange(DOWN, buff=0.4)
        m0.align_to(m1, LEFT)
        m2.shift(RIGHT * (m1[1].get_x() - m2[0].get_x()))
        mm.move_to([0.3, 0.3, 0])
        self.play(FadeIn(tag2), run_time=0.4)
        self.cap("如果 w 能用 u、v 线性表示（三个向量线性相关）……", wait=0)
        self.play(Write(m0), run_time=1.0)
        self.wait(1.5)
        self.play(Write(m1), run_time=1.5)
        self.cap("……每一项里都有一个向量出现了两次", wait=1.2)
        self.play(Indicate(m1[2], color=RED), Indicate(m1[4], color=RED), run_time=1.2)
        self.play(Write(m2), run_time=1.4)
        self.hit()
        self.play(burst(m2[5].get_center(), MAGENTA, n=24), run_time=0.7)
        res2 = mixed("线性相关", r"$\;\Longleftrightarrow\;$", r"$v_1\wedge\cdots\wedge v_k = 0$", size=34, color=INK)
        res2[0].set_color(MAGENTA)
        res2_box = result_box(res2, MAGENTA)
        VGroup(res2_box, res2).next_to(mm, DOWN, buff=0.55)
        self.play(FadeIn(res2_box), FadeIn(res2), run_time=0.8)
        self.cap("反过来也成立：线性无关的向量，楔积一定不是 0（下一节看基底就明白）", wait=None)
        self.cap("楔积 ≠ 0，正是“线性无关”的代数判据", wait=None, t2c={"线性无关": MAGENTA})
        self.clear_all()
        self.finish()


class KVectors(B3D):
    CHAPTER = 1
    TITLE = "从线段到体积：k-向量"

    def construct(self):
        self.set_camera_orientation(phi=66 * DEGREES, theta=-52 * DEGREES)
        self.header()
        u = np.array([2.3, -0.3, 0.0]) * 1.25
        v = np.array([0.5, 2.0, 0.15]) * 1.25
        w = np.array([0.3, 0.6, 1.8]) * 1.25
        O = -(u + v + w) / 2 + RIGHT * 0.6
        grid = NumberPlane(x_range=[-2, 3, 1], y_range=[-2, 3, 1], background_line_style={
            "stroke_color": DIM, "stroke_width": 1, "stroke_opacity": 0.6}, axis_config={"stroke_opacity": 0})
        grid.set_opacity(0.5).shift(OUT * O[2])
        self.play(Create(grid), run_time=1.0)
        self.begin_ambient_camera_rotation(rate=0.025)

        def arrow(a, b, c):
            return vec3(a, b, c)

        # 侧边栏
        lad = [
            (r"u", "1-向量", "有向线段", CYAN),
            (r"u\wedge v", "2-向量", "有向平面块", MAGENTA),
            (r"u\wedge v\wedge w", "3-向量", "有向体积", LIME),
        ]
        side = VGroup()
        for tex, g, d, c in lad:
            row = VGroup(M(tex, 40, c), VGroup(T(g, 26, c, bold=True), T(d, 22, MUTED)).arrange(DOWN, aligned_edge=LEFT,
                                                                                               buff=0.08))
            row.arrange(RIGHT, buff=0.35)
            side.add(row)
        side.arrange(DOWN, aligned_edge=LEFT, buff=0.5).to_edge(LEFT, buff=0.6).shift(DOWN * 0.3)
        for r in side:
            r[1].align_to(side[2][1], LEFT)
        spanel = panel(side, pad=0.3, color=VIOLET, opacity=0.75)
        self.fix(spanel)
        self.play(FadeIn(spanel), run_time=0.5)

        # 1-向量
        au = arrow(O, O + u, CYAN)
        self.beat(2)
        self.hit()
        self.play(Create(au), run_time=0.9)
        self.fix(side[0])
        self.play(FadeIn(side[0], shift=RIGHT * 0.2), run_time=0.5)
        self.cap("一个向量：一段有方向的线段", wait=None)

        # 2-向量：v 沿 u 扫出平行四边形
        av = arrow(O, O + v, MAGENTA)
        self.beat(2)
        self.play(Create(av), run_time=0.8)
        s2 = ValueTracker(0.001)
        face = always_redraw(lambda: Polygon(O, O + u * s2.get_value(), O + u * s2.get_value() + v, O + v, stroke_color=GOLD,
                                             stroke_width=2, fill_color=MAGENTA, fill_opacity=0.35))
        self.add(face)
        self.hit()
        self.play(s2.animate.set_value(1), run_time=1.6)
        face.clear_updaters()
        # 平面内的绕行箭头
        e1 = normalize(u)
        e2 = normalize(v - np.dot(v, e1) * e1)
        cen = O + (u + v) / 2

        def circ(r=0.45, a0=-0.4, a1=4.6):
            pts = [cen + r * (math.cos(t) * e1 + math.sin(t) * e2) for t in np.linspace(a0, a1, 40)]
            c = VMobject(stroke_color=GOLD, stroke_width=4).set_points_smoothly(pts)
            end = pts[-1]
            dirn = normalize(pts[-1] - pts[-2])
            side_ = np.cross(np.cross(e1, e2), dirn)
            tipm = Polygon(end + dirn * 0.16, end + side_ * 0.09, end - side_ * 0.09, stroke_width=0, fill_color=GOLD,
                           fill_opacity=1)
            return VGroup(c, tipm)

        cc = circ()
        self.play(Create(cc), run_time=0.8)
        self.fix(side[1])
        self.play(FadeIn(side[1], shift=RIGHT * 0.2), run_time=0.5)
        self.cap("两个向量：一块有方向的平面——u 先、v 后，决定了绕行方向", wait=None)

        # 形状不重要
        area = np.linalg.norm(np.cross(u, v))
        self.beat(4)
        self.cap("2-向量只记得三件事：所在的平面、面积、绕行方向。形状无关紧要", wait=0,
                 t2c={"平面": GOLD, "面积": GOLD, "绕行方向": GOLD})
        rr = math.sqrt(area / PI)
        disk = Polygon(*[cen + rr * (math.cos(t) * e1 + math.sin(t) * e2) for t in np.linspace(0, TAU, 4 * 24,
                                                                                               endpoint=False)],
                       stroke_color=GOLD, stroke_width=2, fill_color=MAGENTA, fill_opacity=0.35)
        sq = math.sqrt(area) / 2
        square = Polygon(*[cen + sq * (x * e1 + y * e2) for x, y in [(-1, -1), (1, -1), (1, 1), (-1, 1)]],
                         stroke_color=GOLD, stroke_width=2, fill_color=MAGENTA, fill_opacity=0.35)
        alab = VGroup(T("面积", 24, MUTED), DecimalNumber(area, num_decimal_places=2, font_size=40, color=GOLD)).arrange(
            RIGHT, buff=0.2).to_corner(UR, buff=0.6).shift(DOWN * 0.9)
        self.fix(alab)
        self.play(FadeIn(alab), run_time=0.4)
        face_copy = face.copy()
        self.play(Transform(face, disk), run_time=1.6)
        self.wait(0.8)
        self.play(Transform(face, square), run_time=1.4)
        self.wait(0.8)
        self.play(Transform(face, face_copy), run_time=1.4)
        self.wait(1.0)

        # 3-向量
        self.beat(4)
        aw = arrow(O, O + w, LIME)
        self.play(Create(aw), FadeOut(cc), FadeOut(alab), run_time=0.8)
        s3 = ValueTracker(0.001)

        def box():
            h = w * s3.get_value()
            pts = [O, O + u, O + u + v, O + v]
            top = [p + h for p in pts]
            fs = VGroup()
            fs.add(Polygon(*top, stroke_color=LIME, stroke_width=2, fill_color=LIME, fill_opacity=0.18))
            for i in range(4):
                a, b = pts[i], pts[(i + 1) % 4]
                fs.add(Polygon(a, b, b + h, a + h, stroke_color=LIME, stroke_width=1.5, fill_color=LIME,
                               fill_opacity=0.12))
            return fs

        bx = always_redraw(box)
        self.add(bx)
        self.hit()
        self.play(s3.animate.set_value(1), run_time=2.0)
        bx.clear_updaters()
        self.fix(side[2])
        self.play(FadeIn(side[2], shift=RIGHT * 0.2), run_time=0.5)
        self.cap("三个向量：一块有方向的体积（右手系为正）", wait=None)

        # 第四个向量
        self.beat(4)
        x4 = np.array([-1.2, 1.4, 1.2]) * 1.25
        ax = arrow(O, O + x4, ORANGE)
        self.play(Create(ax), run_time=0.8)
        z = M(r"u\wedge v\wedge w\wedge x = 0", 48, ORANGE)
        zb = panel(z, pad=0.25, color=ORANGE)
        zg = VGroup(zb, z).to_corner(UR, buff=0.5).shift(DOWN * 1.0)
        self.fix(zg)
        self.hit()
        self.play(FadeIn(zb), Write(z), run_time=0.9)
        self.cap("三维空间里的四个向量必然线性相关，所以再楔一个就只能得 0", wait=None)
        self.cap("于是在三维里：标量、向量、2-向量、3-向量——到 3 为止", wait=None)
        self.stop_ambient_camera_rotation()
        self.clear_all()
        self.finish()


class Basis(BScene):
    CHAPTER = 1
    TITLE = "基底、维数与符号"

    def construct(self):
        self.header()
        cols = [
            (r"\Lambda^0", [r"1"], INK),
            (r"\Lambda^1", [r"e_1", r"e_2", r"e_3"], CYAN),
            (r"\Lambda^2", [r"e_1\wedge e_2", r"e_1\wedge e_3", r"e_2\wedge e_3"], MAGENTA),
            (r"\Lambda^3", [r"e_1\wedge e_2\wedge e_3"], LIME),
        ]
        grp = VGroup()
        for head, items, c in cols:
            h = M(head + r"(\mathbb{R}^3)", 40, c)
            its = VGroup(*[M(t, 36) for t in items]).arrange(DOWN, buff=0.32)
            boxes = VGroup(*[RoundedRectangle(corner_radius=0.08, width=max(2.6, it.width + 0.4), height=0.62,
                                              stroke_color=c, stroke_width=1.5, fill_color=PANEL, fill_opacity=0.85)
                             .move_to(it) for it in its])
            col = VGroup(h, VGroup(boxes, its)).arrange(DOWN, buff=0.4)
            grp.add(col)
        grp.arrange(RIGHT, buff=0.45, aligned_edge=UP).move_to(UP * 0.55)
        dims = VGroup()
        for col, (_, items, c) in zip(grp, cols):
            d = EN(str(len(items)), 44, GOLD, black=True).move_to([col.get_x(), -2.0, 0])
            dims.add(d)
        self.cap("以 ℝ³ 的基 e₁, e₂, e₃ 为例：把基向量按下标从小到大楔起来，就得到各次的基", wait=0)
        for i, col in enumerate(grp):
            self.beat(2)
            self.hit()
            self.play(FadeIn(col[0], shift=DOWN * 0.2), LaggedStart(*[FadeIn(VGroup(b, t), shift=DOWN * 0.15)
                                                                     for b, t in zip(col[1][0], col[1][1])],
                                                                   lag_ratio=0.25), run_time=1.0)
        self.wait(1.0)
        dl = T("维数", 24, MUTED).next_to(dims, LEFT, buff=0.6)
        self.play(FadeIn(dl), LaggedStart(*[FadeIn(d, scale=1.5) for d in dims], lag_ratio=0.2), run_time=1.0)
        tot = M(r"1+3+3+1 = 8 = 2^3", 42, GOLD).move_to(DOWN * 2.75)
        self.play(Write(tot), run_time=1.0)
        self.cap("k 次的基 = 从 3 个基向量里选 k 个，所以维数是组合数", wait=None)
        self.beat(4)
        self.play(FadeOut(VGroup(grp, dims, dl, tot)), run_time=0.6)

        # 帕斯卡三角
        rows = VGroup()
        for n in range(7):
            r = VGroup(*[EN(str(math.comb(n, k)), 28, INK) for k in range(n + 1)]).arrange(RIGHT, buff=0.55)
            rows.add(r)
        rows.arrange(DOWN, buff=0.28).move_to([-2.4, 0.0, 0])
        for n, r in enumerate(rows):
            r.set_x(-2.4)
        lbl = VGroup(*[M(rf"n={n}", 26, MUTED).next_to(rows[n], LEFT, buff=0.0).set_x(-6.0) for n in range(7)])
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.1) for r in rows], lag_ratio=0.12), FadeIn(lbl), run_time=1.6)
        self.hit()
        self.play(rows[3].animate.set_color(GOLD), run_time=0.6)
        f = M(r"\dim \Lambda^k(\mathbb{R}^n) = \binom{n}{k}", 52, GOLD)
        f2 = M(r"\dim \Lambda(\mathbb{R}^n) = 2^n", 44, INK)
        rg = VGroup(f, f2).arrange(DOWN, buff=0.5).move_to([3.9, 0.2, 0])
        self.play(FadeIn(panel(rg, pad=0.4, color=GOLD)), Write(f), run_time=1.0)
        self.play(Write(f2), run_time=0.8)
        self.cap("ℝⁿ 上的外代数：第 k 层的维数是 C(n,k)，最高一层 Λⁿ 只有一维", wait=None,
                 t2c={"只有一维": GOLD})
        self.play(rows[6][-1].animate.set_color(GOLD).scale(1.4), run_time=0.6)
        self.cap("记住这一点：最高次只有一维——第二章的行列式全靠它", wait=None, t2c={"第二章": MAGENTA})
        self.beat(4)
        self.clear_all(keep=[self._hdr])

        # 排序与符号
        sign = ValueTracker(1)
        tiles_tex = [r"e_2", r"e_3", r"e_1"]
        colors = {r"e_1": CYAN, r"e_2": MAGENTA, r"e_3": LIME}

        def tile(t):
            m = M(t, 50, colors[t])
            b = RoundedRectangle(corner_radius=0.12, width=1.2, height=1.0, stroke_color=colors[t], stroke_width=2.5,
                                 fill_color=PANEL, fill_opacity=0.9)
            return VGroup(b, m.move_to(b))

        tiles = [tile(t) for t in tiles_tex]
        xs = [-1.2, 0.6, 2.4]
        for t, x in zip(tiles, xs):
            t.move_to([x, 0.6, 0])
        wedges = VGroup(*[M(r"\wedge", 46, MUTED).move_to([(xs[i] + xs[i + 1]) / 2, 0.6, 0]) for i in range(2)])
        sg = M("+", 80, GOLD).move_to([-2.9, 0.6, 0])
        self.cap("基向量的顺序乱了怎么办？相邻两个交换一次，就变一次号", wait=0)
        self.play(*[FadeIn(t, shift=UP * 0.3) for t in tiles], FadeIn(wedges), FadeIn(sg), run_time=0.8)
        self.wait(1.5)
        counter = VGroup(T("交换次数", 22, MUTED), EN("0", 30, GOLD)).arrange(RIGHT, buff=0.25).move_to([0.6, -1.0, 0])
        self.play(FadeIn(counter), run_time=0.4)

        def swap(i, j, k, newsign):
            a, b = tiles[i], tiles[j]
            pa, pb = a.get_center(), b.get_center()
            new_sg = M(newsign, 80, RED if newsign == "-" else GOLD).move_to(sg)
            newc = EN(str(k), 30, GOLD).move_to(counter[1])
            self.hit()
            self.play(Swap(a, b, path_arc=PI * 0.7), Transform(sg, new_sg), Transform(counter[1], newc), run_time=0.9)
            self.play(Flash(sg, color=RED if newsign == "-" else GOLD, flash_radius=0.6), run_time=0.5)
            tiles[i], tiles[j] = tiles[j], tiles[i]

        self.beat(2)
        swap(1, 2, 1, "-")
        self.wait(1.2)
        self.beat(2)
        swap(0, 1, 2, "+")
        self.wait(1.0)
        eq = M(r"e_2\wedge e_3\wedge e_1 = +\,e_1\wedge e_2\wedge e_3", 44).move_to(DOWN * 2.0)
        self.play(Write(eq), run_time=1.0)
        self.wait(1.5)
        self.beat(4)
        gen = M(r"e_{\sigma(1)}\wedge e_{\sigma(2)}\wedge\cdots\wedge e_{\sigma(n)} = \operatorname{sgn}(\sigma)\;"
                r"e_1\wedge e_2\wedge\cdots\wedge e_n", 46, GOLD)
        gb = result_box(gen, GOLD)
        VGroup(gb, gen).move_to(DOWN * 2.0)
        self.hit("impact")
        self.play(FadeOut(eq), FadeIn(gb), Write(gen), run_time=1.0)
        self.cap("排列的奇偶性 sgn(σ) 自己冒了出来：交换奇数次为 −1，偶数次为 +1", wait=None,
                 t2c={"sgn(σ)": GOLD})
        rep = M(r"e_1\wedge e_3\wedge e_1 = 0", 44, ORANGE).move_to(UP * 2.2 + RIGHT * 3.8)
        self.play(Write(rep), run_time=0.8)
        self.play(burst(rep.get_right() + LEFT * 0.2, ORANGE), run_time=0.6)
        self.cap("而有下标重复的，直接是 0。这两条马上就要派上大用场", wait=None)
        self.clear_all()
        self.finish()


class FirstCompute(BScene):
    CHAPTER = 1
    TITLE = "第一次计算：行列式自己跳出来"

    def construct(self):
        self.header()
        A = matrix_tex([["a", "b"], ["c", "d"]], 48)
        cols = VGroup(M(r"v = a\,e_1 + c\,e_2", 40, CYAN), M(r"w = b\,e_1 + d\,e_2", 40, MAGENTA)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.25)
        top = VGroup(A, cols).arrange(RIGHT, buff=0.6).move_to([-3.4, 1.85, 0])
        # 把矩阵的两列染色
        ents = A[0]
        # pmatrix 的子对象顺序：左括号, a, b, c, d, 右括号（按出现顺序）
        self.play(FadeIn(A), run_time=0.6)
        self.play(Write(cols), run_time=1.2)
        self.cap("在平面上：v、w 的坐标就是矩阵的两列", wait=None)

        l1 = M([r"v\wedge w", "=", r"(a\,e_1+c\,e_2)\wedge(b\,e_1+d\,e_2)"], 44)
        l2 = M(["=", r"ab\;e_1\wedge e_1", "+", r"ad\;e_1\wedge e_2", "+", r"cb\;e_2\wedge e_1", "+",
                r"cd\;e_2\wedge e_2"], 44)
        l3 = M(["=", r"ad\;e_1\wedge e_2", "-", r"bc\;e_1\wedge e_2"], 44)
        l4 = M(["=", r"(ad-bc)", r"\;e_1\wedge e_2"], 44)
        L = VGroup(l1, l2, l3, l4).arrange(DOWN, buff=0.38)
        for l in (l2, l3, l4):
            l.shift(RIGHT * (l1[1].get_x() - l[0].get_x()))
        L.move_to([0.4, -0.95, 0])
        L.shift(RIGHT * (0.4 - (L.get_left()[0] + L.get_right()[0]) / 2))
        self.beat(2)
        self.play(Write(l1), run_time=1.3)
        self.wait(1.0)
        self.play(TFC(l1[2], VGroup(*l2[1:])), FadeIn(l2[0]), run_time=1.3)
        self.cap("按双线性展开成四项", wait=1.6)
        self.beat(2)
        self.hit()
        s1, s2 = strike(l2[1]), strike(l2[7])
        self.play(Create(s1), Create(s2), burst(l2[1].get_center(), RED, n=20, radius=0.9),
                  burst(l2[7].get_center(), RED, n=20, radius=0.9), run_time=0.8)
        self.cap("e₁∧e₁ = e₂∧e₂ = 0；e₂∧e₁ 交换一次变成 −e₁∧e₂", wait=0)
        self.play(Indicate(l2[5], color=RED), run_time=0.9)
        self.play(FadeIn(l3[0]), TFC(l2[3], l3[1]), TFC(l2[4], l3[2]),
                  TFC(l2[5], l3[3]), run_time=1.2)
        self.wait(1.4)
        self.play(TFC(l3, l4), run_time=1.0)
        self.beat(2)
        self.hit("impact")
        det_lab = M(r"=\det\begin{pmatrix}a&b\\c&d\end{pmatrix}", 44, GOLD).next_to(l4, RIGHT, buff=0.3)
        bx = SurroundingRectangle(l4[1], color=GOLD, buff=0.1, corner_radius=0.08)
        self.play(Create(bx), l4[1].animate.set_color(GOLD), FadeIn(det_lab, shift=LEFT * 0.2), run_time=0.8)
        self.play(ring_pulse(l4[1].get_center(), GOLD, 2.0), run_time=0.6)
        self.cap("二阶行列式 ad − bc 不是规定出来的，是算出来的", wait=None, t2c={"算出来的": GOLD})
        self.beat(4)
        self.clear_all(keep=[self._hdr])

        # 三维：叉积是伪装的 2-向量
        r1 = M([r"u\wedge v", "=", r"(u_2v_3-u_3v_2)", r"\,e_2\wedge e_3", "+", r"(u_3v_1-u_1v_3)", r"\,e_3\wedge e_1",
                "+", r"(u_1v_2-u_2v_1)", r"\,e_1\wedge e_2"], 38)
        r2 = M([r"u\times v", "=", r"(u_2v_3-u_3v_2)", r"\,e_1", "+", r"(u_3v_1-u_1v_3)", r"\,e_2", "+",
                r"(u_1v_2-u_2v_1)", r"\,e_3"], 38)
        R = VGroup(r1, r2).arrange(DOWN, buff=1.3).move_to(UP * 0.6)
        for k in (2, 3, 5, 6, 8, 9):
            r2[k].set_x(r1[k].get_x())
        r2[0].align_to(r1[0], RIGHT)
        r2[1].set_x(r1[1].get_x())
        r2[4].set_x(r1[4].get_x())
        r2[7].set_x(r1[7].get_x())
        self.cap("在三维里，同样展开 u∧v，会得到三个坐标平面上的分量", wait=0)
        self.play(Write(r1), run_time=2.0)
        self.wait(2.0)
        self.beat(2)
        self.play(FadeIn(r2, shift=UP * 0.2), run_time=1.0)
        links = VGroup()
        for k in (3, 6, 9):
            a = r1[k].get_bottom() + DOWN * 0.08
            b = r2[k].get_top() + UP * 0.08
            links.add(DoubleArrow(a, b, buff=0, color=GOLD, stroke_width=3, tip_length=0.15))
        self.hit()
        self.play(LaggedStart(*[GrowFromCenter(l) for l in links], lag_ratio=0.3), run_time=1.0)
        for k in (2, 5, 8):
            self.play(Indicate(VGroup(r1[k], r2[k]), color=GOLD), run_time=0.5)
        self.cap("系数和叉积一模一样！叉积就是 2-向量换了个马甲：每个坐标平面换成它的法向量", wait=None,
                 t2c={"一模一样": GOLD})
        self.beat(4)
        trip = M(r"u\wedge v\wedge w = \big((u\times v)\cdot w\big)\; e_1\wedge e_2\wedge e_3"
                 r" = \det(u,v,w)\; e_1\wedge e_2\wedge e_3", 40, INK)
        tb = result_box(trip, LIME)
        VGroup(tb, trip).move_to(DOWN * 2.1)
        self.hit()
        self.play(FadeIn(tb), Write(trip), run_time=1.5)
        self.cap("再楔上 w：混合积，也就是三阶行列式。那么 n 阶呢？", wait=None)
        self.clear_all()
        self.finish()
