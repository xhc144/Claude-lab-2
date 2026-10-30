# -*- coding: utf-8 -*-
"""第六章极限定理与关系总图（S08）和第七章速查表、结尾（S09）。"""
from common import *  # noqa: F401,F403
from scenes_a import cover_art


def irwin_hall_std(z, n):
    """n 个独立 U(0,1) 之和标准化后的精确密度。"""
    sd = math.sqrt(n / 12)
    s = n / 2 + z * sd
    if s <= 0 or s >= n:
        return 0.0
    tot = sum((-1) ** k * math.comb(n, k) * (s - k) ** (n - 1) for k in range(int(math.floor(s)) + 1))
    return tot / math.factorial(n - 1) * sd


# 关系总图：节点 (名字, 记号, 列, 行, 颜色)
COLS = [-5.6, -2.8, 0.0, 2.8, 5.6]
ROWS = [2.7, 1.35, 0.0, -1.3, -2.5]
NODES = {
    "超几何": (r"H(N,K,n)", 0, 0, TEAL), "韦布尔": (r"\mathrm{Weibull}(k,\lambda)", 2, 0, BRICK),
    "均匀": (r"U(0,1)", 3, 0, BRICK), "贝塔": (r"\mathrm{Beta}(\alpha,\beta)", 4, 0, BRICK),
    "伯努利": (r"B(1,p)", 0, 1, TEAL), "二项": (r"B(n,p)", 1, 1, TEAL), "泊松": (r"P(\lambda)", 2, 1, TEAL),
    "指数": (r"\mathrm{Exp}(\lambda)", 3, 1, BRICK),
    "几何": (r"\mathrm{Geo}(p)", 0, 2, TEAL), "负二项": (r"\mathrm{NB}(r,p)", 1, 2, TEAL),
    "正态": (r"N(\mu,\sigma^2)", 2, 2, BRICK), "伽马": (r"\Gamma(\alpha,\lambda)", 3, 2, BRICK),
    "对数正态": (r"\mathrm{LN}(\mu,\sigma^2)", 1, 3, BRICK), "卡方": (r"\chi^2_k", 3, 3, INDIGO),
    "柯西": (r"\mathrm{Cauchy}", 1, 4, BRICK), "t 分布": (r"t_\nu", 2, 4, INDIGO), "F 分布": (r"F(d_1,d_2)", 3, 4, INDIGO),
}
NW, NH = 1.62, 0.8


def node(name):
    tex, c, r, color = NODES[name]
    box = RoundedRectangle(corner_radius=0.1, width=NW, height=NH, fill_color=tint(color, 0.10), fill_opacity=1,
                           stroke_color=color, stroke_width=2.2)
    t = T(name, 20, INK, bold=True)
    m = M(tex, 22, INK)
    g = VGroup(t, m).arrange(DOWN, buff=0.06)
    if g.width > NW - 0.15:
        g.scale_to_fit_width(NW - 0.15)
    g.move_to(box)
    out = VGroup(box, g).move_to([COLS[c], ROWS[r], 0])
    return out


def _offset(side, lab, shift):
    """标签相对箭头中点的偏移：左右放时按宽度让开，上下放时按高度让开。"""
    side = np.array(side, dtype=float)
    if abs(side[1]) < 1e-6:
        return side * (lab.width / 2 + 0.08 + shift)
    return side * (lab.height / 2 + 0.06 + shift)


def edge_label(s, size=15, color=INK):
    lab = M(s.strip("$"), size * 1.25, color) if s.startswith("$") else T(s, size, color)
    bg = BackgroundRectangle(lab, color=BG, fill_opacity=0.92, buff=0.04)
    return VGroup(bg, lab)


def P(nodes, name, d):
    """节点边框上的点：d 是方向（如 LEFT、UR）。"""
    b = nodes[name][0]
    return b.get_critical_point(d) if not isinstance(d, tuple) else b.get_critical_point(d[0]) + d[1]

def solid(a, b, label=None, side=UP, shift=0.0, both=False, lab_at=0.5):
    ar = (DoubleArrow if both else Arrow)(a, b, buff=0.04, color=AXIS, stroke_width=2.6, tip_length=0.14,
                                          max_tip_length_to_length_ratio=0.25)
    g = VGroup(ar)
    if label:
        lab = edge_label(label)
        lab.move_to(a + (b - a) * lab_at).shift(_offset(side, lab, shift))
        g.add(lab)
    return g

def dashed(a, b, label=None, side=UP, shift=0.0, arc=0.0, color=AXIS):
    if arc:
        path = ArcBetweenPoints(a, b, angle=arc)
    else:
        path = Line(a, b)
    dl = DashedVMobject(path.set_stroke(color, 2.4), num_dashes=max(6, int(path.get_arc_length() / 0.12)))
    tip = ArrowTriangleFilledTip(color=color, length=0.14, width=0.14)
    end_dir = path.point_from_proportion(1) - path.point_from_proportion(0.97)
    tip.rotate(angle_of_vector(end_dir)).move_to(b - normalize(end_dir) * 0.07)
    g = VGroup(dl, tip)
    if label:
        lab = edge_label(label)
        lab.move_to(path.point_from_proportion(0.5)).shift(_offset(side, lab, shift))
        g.add(lab)
    return g


def solid_edges(nodes):
    first = [
        solid(P(nodes, "伯努利", RIGHT), P(nodes, "二项", LEFT), "n 个独立和"),
        solid(P(nodes, "伯努利", DOWN), P(nodes, "几何", UP), "首次成功", side=RIGHT, shift=0.0),
        solid(P(nodes, "几何", RIGHT), P(nodes, "负二项", LEFT), "r 个独立和"),
        solid(P(nodes, "均匀", DOWN), P(nodes, "指数", UP), r"$-\ln U/\lambda$", side=RIGHT),
        solid(P(nodes, "指数", DOWN), P(nodes, "伽马", UP), "n 个独立和", side=LEFT),
        solid(P(nodes, "伽马", DOWN), P(nodes, "卡方", UP), r"$\alpha=k/2,\ \lambda=1/2$", side=RIGHT),
        solid(P(nodes, "卡方", (LEFT, DOWN * 0.25)), P(nodes, "t 分布", (UP, RIGHT * 0.45)), "作分母", side=DOWN + RIGHT * 0.3, shift=0.05),
        solid(P(nodes, "卡方", DOWN), P(nodes, "F 分布", UP), r"$(U/d_1)/(V/d_2)$", side=RIGHT),
    ]
    rest = [
        solid(P(nodes, "正态", (DOWN, RIGHT * 0.5)), P(nodes, "卡方", (LEFT, UP * 0.2)), r"$\sum Z_i^2$", side=UP + RIGHT * 0.5),
        solid(P(nodes, "正态", DOWN), P(nodes, "t 分布", UP), r"$Z/\sqrt{V/\nu}$", side=LEFT, lab_at=0.35),
        solid(P(nodes, "正态", (LEFT, DOWN * 0.2)), P(nodes, "对数正态", (UP, RIGHT * 0.4)), r"$e^{X}$", side=UP + LEFT * 0.3),
        solid(P(nodes, "正态", (DOWN, LEFT * 0.45)), P(nodes, "柯西", (UP, RIGHT * 0.6)), r"$Z_1/Z_2$", side=LEFT),
        solid(P(nodes, "t 分布", LEFT), P(nodes, "柯西", RIGHT), r"$\nu=1$"),
        solid(P(nodes, "t 分布", RIGHT), P(nodes, "F 分布", LEFT), r"$T^2\sim F(1,\nu)$", side=DOWN),
        solid(P(nodes, "指数", (LEFT, UP * 0.25)), P(nodes, "韦布尔", (DOWN, RIGHT * 0.45)), r"$\lambda E^{1/k}$",
              side=UP + LEFT * 0.3),
        solid(P(nodes, "均匀", RIGHT), P(nodes, "贝塔", LEFT), "次序统计量"),
        solid(P(nodes, "伽马", RIGHT), P(nodes, "贝塔", DOWN), r"$\frac{X}{X+Y}$", side=RIGHT),
        solid(P(nodes, "泊松", RIGHT), P(nodes, "指数", LEFT), "泊松过程", both=True),
    ]
    return first, rest


def limit_edges(nodes):
    lims = [
        dashed(P(nodes, "超几何", (DOWN, RIGHT * 0.5)), P(nodes, "二项", (UP, LEFT * 0.3)), r"$N\to\infty$", side=UP + RIGHT * 0.6),
        dashed(P(nodes, "二项", RIGHT), P(nodes, "泊松", LEFT), r"$np\to\lambda$", side=DOWN),
        dashed(P(nodes, "二项", (DOWN, RIGHT * 0.55)), P(nodes, "正态", (UP, LEFT * 0.5)), r"$n\to\infty$", side=LEFT,
               color=GOLD),
        dashed(P(nodes, "泊松", DOWN), P(nodes, "正态", UP), r"$\lambda\to\infty$", side=RIGHT, color=GOLD),
        dashed(P(nodes, "伽马", LEFT), P(nodes, "正态", RIGHT), r"$\alpha\to\infty$", side=DOWN, color=GOLD),
        dashed(P(nodes, "t 分布", (UP, RIGHT * 0.55)), P(nodes, "正态", (DOWN, RIGHT * 0.55)), r"$\nu\to\infty$", side=RIGHT,
               arc=0.5, color=GOLD),
    ]
    return lims


class MapStill(Scene):
    """检查用：一次画出完整的关系总图。"""

    def construct(self):
        nodes = {k: node(k) for k in NODES}
        first, rest = solid_edges(nodes)
        self.add(running_header("06"), *nodes.values(), *first, *rest, *limit_edges(nodes))


class S08(VScene):
    SID = "S08"

    def construct(self):
        self.seg(0)
        hdr = play_chapter(self, "06")

        # --- 中心极限定理 ---
        self.seg(1)
        eh = entry_header("中心极限定理", "Central limit theorem", r"\frac{S_n-n\mu}{\sigma\sqrt n}\xrightarrow{\ d\ }N(0,1)",
                          GOLD, y=2.85)
        eh[0].stretch_to_fit_height(0.9)
        eh[1].stretch_to_fit_height(0.9)
        self.play(FadeIn(eh, shift=DOWN * 0.2), run_time=0.8)
        cond = mixed("林德伯格–莱维：", "$X_i$", " 独立同分布，", "$\\operatorname{Var}X_i=\\sigma^2<\\infty$", size=24)
        cond.next_to(eh, DOWN, buff=0.3).align_to(eh, LEFT).shift(RIGHT * 0.25)
        self.play(FadeIn(cond, shift=RIGHT * 0.2), run_time=0.8)
        ax = axes([-3.5, 3.7, 1], [0, 0.6, 0.2], 9.2, 3.6, xnums=[-3, -2, -1, 0, 1, 2, 3], ynums=[0.2, 0.4],
                  ydec=1, xlabel="z", ylabel=T("密度", 20, INK))
        ax.move_to(LEFT * 1.3 + DOWN * 1.05)
        nc = DashedVMobject(curve(ax, norm_pdf, -3.5, 3.5, INK, width=3), num_dashes=70)
        lg = legend([(INK, "$N(0,1)$", "dash")], size=20).move_to(ax.c2p(2.85, 0.52))
        self.play(Create(ax), Create(nc), FadeIn(lg), run_time=1.2)
        specs = [(1, PLUM), (2, TEAL), (3, BRICK), (6, GOLD)]
        cur, lab, traces = None, None, VGroup()
        for n, c in specs:
            cv = curve(ax, lambda z, n=n: irwin_hall_std(z, n), -3.45, 3.45, c, width=4.5, n=700)
            nl = M(rf"n={n}", 40, c).move_to(RIGHT * 4.9 + DOWN * 0.3)
            if cur is None:
                self.play(Create(cv), FadeIn(nl), run_time=1.4)
            else:
                traces.add(cur.copy().set_stroke(opacity=0.22, width=2.5))
                self.add(traces[-1])
                self.play(Transform(cur, cv), Transform(lab, nl), run_time=1.6, rate_func=smooth)
            if cur is None:
                cur, lab = cv, nl
            self.wait(1.6)
        stages = T("矩形 → 三角 → 分段二次 → 几乎重合", 22, MUTED).next_to(lab, DOWN, buff=0.35)
        stages.set_x(4.6)
        if stages.get_right()[0] > 6.95:
            stages.shift(LEFT * (stages.get_right()[0] - 6.95))
        self.play(FadeIn(stages), run_time=0.7)
        self.catch_up()

        # --- 收敛速度与条件 ---
        self.seg(2)
        self.play(FadeOut(VGroup(ax, nc, lg, cur, lab, traces, stages, cond)), run_time=0.6)
        be_t = T("收敛速度（贝里–埃森）", 26, INK, bold=True)
        be = M(r"\sup_x\Big|P\Big(\frac{S_n-n\mu}{\sigma\sqrt n}\le x\Big)-\Phi(x)\Big|\ \le\ "
               r"\frac{C\,\mathbb{E}|X_1-\mu|^3}{\sigma^3\sqrt n},\qquad C<0.48", 40)
        be_n = T("偏度越大，收敛越慢", 22, MUTED)
        g1 = VGroup(be_t, be, be_n).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        warn = VGroup(T("条件不可少", 26, BRICK, bold=True),
                      T("方差无穷时，可能收敛到别的稳定分布（柯西的样本均值根本不收敛）", 22, INK)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.2)
        stack = VGroup(note_box(g1, GOLD, pad=0.3), note_box(warn, BRICK, pad=0.3)).arrange(DOWN, aligned_edge=LEFT,
                                                                                         buff=0.45)
        stack.move_to(DOWN * 0.45)
        self.play(FadeIn(stack[0][:2]), FadeIn(be_t), Write(be), run_time=2.0)
        self.play(FadeIn(be_n), run_time=0.6)
        self.wait(max(0.2, self.durs[2] * 0.45 - 3.2))
        self.play(FadeIn(stack[1], shift=UP * 0.2), run_time=0.8)
        self.catch_up()
        self.play(FadeOut(stack), FadeOut(eh), run_time=0.6)

        # --- 关系总图：节点 ---
        self.seg(3)
        nodes = {k: node(k) for k in NODES}
        order = ["伯努利", "二项", "几何", "负二项", "超几何", "泊松",
                 "均匀", "指数", "伽马", "正态", "对数正态", "贝塔", "韦布尔", "柯西",
                 "卡方", "t 分布", "F 分布"]
        lgd = VGroup(
            VGroup(RoundedRectangle(corner_radius=0.05, width=0.32, height=0.22, fill_color=tint(TEAL, 0.1),
                                    fill_opacity=1, stroke_color=TEAL, stroke_width=2), T("离散分布", 17)),
            VGroup(RoundedRectangle(corner_radius=0.05, width=0.32, height=0.22, fill_color=tint(BRICK, 0.1),
                                    fill_opacity=1, stroke_color=BRICK, stroke_width=2), T("连续分布", 17)),
            VGroup(RoundedRectangle(corner_radius=0.05, width=0.32, height=0.22, fill_color=tint(INDIGO, 0.1),
                                    fill_opacity=1, stroke_color=INDIGO, stroke_width=2), T("抽样分布", 17)),
            VGroup(Arrow(LEFT * 0.3, RIGHT * 0.3, buff=0, color=AXIS, stroke_width=2.5, tip_length=0.12),
                   T("精确关系", 17)),
            VGroup(DashedLine(LEFT * 0.3, RIGHT * 0.3, color=AXIS, stroke_width=2.5, dash_length=0.06),
                   T("极限关系", 17)),
        )
        for row in lgd:
            row.arrange(RIGHT, buff=0.15)
        lgd.arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([COLS[4], -1.85, 0])
        lgbox = soft_box(lgd, tint(INK, 0.04), pad=0.18)
        self.play(LaggedStart(*[FadeIn(nodes[k], scale=0.85) for k in order], lag_ratio=0.12),
                  FadeIn(VGroup(lgbox, lgd)), run_time=min(2.8, self.left(1.5)))
        self.catch_up()

        # --- 实线：精确关系 ---
        self.seg(4)
        first, rest = solid_edges(nodes)
        each = max(0.9, min(1.6, (self.durs[4] * 0.78) / len(first) - 0.15))
        for e in first:
            self.play(GrowArrow(e[0]) if not isinstance(e[0], DoubleArrow) else Create(e[0]),
                      *[FadeIn(x) for x in e[1:]], run_time=each)
            self.wait(0.12)
        self.play(LaggedStart(*[AnimationGroup(Create(e[0]), *[FadeIn(x) for x in e[1:]]) for e in rest],
                              lag_ratio=0.35), run_time=max(2.5, self.left(2.5)))
        self.catch_up()

        # --- 虚线：极限关系，几乎都通向正态 ---
        self.seg(5)
        lims = limit_edges(nodes)
        self.play(LaggedStart(*[AnimationGroup(Create(e[0]), FadeIn(e[1]), *[FadeIn(x) for x in e[2:]])
                                for e in lims], lag_ratio=0.3), run_time=3.2)
        nb = nodes["正态"][0]
        halo = VGroup(*[nb.copy().set_fill(opacity=0).set_stroke(GOLD, width=w, opacity=o)
                        for w, o in ((14, 0.12), (8, 0.25), (4, 0.9))])
        self.play(FadeIn(halo), nodes["正态"][0].animate.set_fill(tint(GOLD, 0.25)), run_time=0.8)
        self.play(*[ApplyMethod(h.scale, 1.12, rate_func=there_and_back) for h in halo], run_time=1.2)
        self.catch_up()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)


class S09(VScene):
    SID = "S09"

    def construct(self):
        hdr = running_header("07")

        # --- 速查表 ---
        self.seg(0)
        groups = [
            ("离散", TEAL, [("伯努利", "p", "p(1-p)"), ("二项", "np", "np(1-p)"), ("几何", r"1/p", r"(1-p)/p^2"),
                           ("负二项", r"r/p", r"r(1-p)/p^2"), ("超几何", r"nK/N",
                                                               r"n\frac KN\big(1-\frac KN\big)\frac{N-n}{N-1}"),
                           ("泊松", r"\lambda", r"\lambda")]),
            ("连续", BRICK, [("均匀", r"\frac{a+b}2", r"\frac{(b-a)^2}{12}"), ("指数", r"1/\lambda", r"1/\lambda^2"),
                           ("伽马", r"\alpha/\lambda", r"\alpha/\lambda^2"), ("正态", r"\mu", r"\sigma^2"),
                           ("对数正态", r"e^{\mu+\sigma^2/2}", r"(e^{\sigma^2}-1)e^{2\mu+\sigma^2}"),
                           ("贝塔", r"\frac{\alpha}{\alpha+\beta}", r"\frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}"),
                           ("韦布尔", r"\lambda\Gamma(1+\frac1k)",
                            r"\lambda^2\big[\Gamma(1+\frac2k)-\Gamma^2(1+\frac1k)\big]"),
                           ("柯西", None, None)]),
            ("抽样分布与多元", INDIGO, [("卡方", "k", "2k"), ("t", r"0\ (\nu>1)", r"\frac{\nu}{\nu-2}\ (\nu>2)"),
                                  ("F", r"\frac{d_2}{d_2-2}", r"\frac{2d_2^2(d_1+d_2-2)}{d_1(d_2-2)^2(d_2-4)}"),
                                  ("多元正态", r"\boldsymbol\mu", r"\Sigma")]),
        ]
        panels = VGroup()
        PW = 4.45
        for title, color, rows in groups:
            head = VGroup(T(title, 26, color, bold=True), T("期望", 20, MUTED), T("方差", 20, MUTED))
            head[0].move_to(LEFT * (PW / 2 - 0.1), aligned_edge=LEFT)
            head[1].move_to(LEFT * 0.15)
            head[2].move_to(RIGHT * 1.35)
            lines = VGroup(head)
            for name, e, v in rows:
                nm = T(name, 22, INK).move_to(LEFT * (PW / 2 - 0.1), aligned_edge=LEFT)
                if e is None:
                    ev = VGroup(T("不存在", 20, MUTED).move_to(LEFT * 0.15), T("不存在", 20, MUTED).move_to(RIGHT * 1.35))
                else:
                    em, vm = M(e, 27), M(v, 27)
                    if em.width > 1.25:
                        em.scale_to_fit_width(1.25)
                    if vm.width > 2.0:
                        vm.scale_to_fit_width(2.0)
                    if em.height > 0.48:
                        em.scale_to_fit_height(0.48)
                    if vm.height > 0.48:
                        vm.scale_to_fit_height(0.48)
                    ev = VGroup(em.move_to(LEFT * 0.15), vm.move_to(RIGHT * 1.35))
                lines.add(VGroup(nm, ev))
            for i, ln in enumerate(lines):
                ln.set_y(-i * 0.6)
            rule = Line(LEFT * PW / 2, RIGHT * PW / 2, stroke_width=1.2, color=FAINT).set_y(-0.3)
            top = Line(LEFT * PW / 2, RIGHT * PW / 2, stroke_width=3, color=color).set_y(0.35)
            panels.add(VGroup(top, rule, lines))
        panels.arrange(RIGHT, buff=0.22, aligned_edge=UP).move_to(UP * 0.35)
        panels.align_to(UP * 3.05, UP)
        self.play(FadeIn(hdr), run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(Create(p[0]), FadeIn(p[1]), LaggedStart(
            *[FadeIn(r, shift=UP * 0.12) for r in p[2]], lag_ratio=0.12)) for p in panels], lag_ratio=0.25),
            run_time=2.6)
        self.catch_up(2.6)  # 让表多停一会儿

        # --- 四条唯一性刻画 ---
        self.seg(1)
        cards_spec = [
            ("1", "无记忆性", [mixed("正整数值：唯一无记忆的是", " 几何分布", size=23),
                            mixed("非负连续：唯一无记忆的是", " 指数分布", size=23)], TEAL),
            ("2", "样本均值与样本方差", [mixed("独立同分布样本中 ", "$\\bar X$", " 与 ", "$S^2$", " 独立", size=23),
                                  mixed("$\\Longleftrightarrow$", " 总体是正态分布", size=23)], BRICK),
            ("3", "卢卡奇定理", [mixed("独立正变量 ", "$X,Y$", "：", "$X+Y$", " 与 ", "$\\frac{X}{X+Y}$", " 独立", size=23),
                            mixed("$\\Longleftrightarrow$", " 二者是同率参数的伽马分布", size=23)], INDIGO),
            ("4", "最大熵", [mixed("固定均值与方差 → ", "正态", size=23),
                          mixed("固定均值、支撑 ", "$[0,\\infty)$", " → ", "指数", size=23),
                          mixed("固定有界支撑 → ", "均匀", size=23)], GOLD),
        ]
        cards = VGroup()
        for num, title, body, color in cards_spec:
            badge = VGroup(Circle(radius=0.24, fill_color=color, fill_opacity=1, stroke_width=0),
                           T(num, 22, WHITE, bold=True))
            tt = T(title, 28, INK, bold=True)
            head = VGroup(badge, tt).arrange(RIGHT, buff=0.2)
            bd = VGroup(*body).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            inner = VGroup(head, bd).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
            box = RoundedRectangle(corner_radius=0.14, width=6.6, height=2.55, fill_color=tint(color, 0.08),
                                   fill_opacity=1, stroke_color=color, stroke_width=2)
            inner.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.3)
            cards.add(VGroup(box, inner))
        cards.arrange_in_grid(rows=2, cols=2, buff=(0.3, 0.3)).move_to(DOWN * 0.2)
        cap = T("四条“唯一性”刻画", 30, INK, bold=True)
        self.play(FadeOut(panels, shift=UP * 0.3), run_time=0.7)
        cap.next_to(cards, UP, buff=0.3)
        if cap.get_top()[1] > 3.35:
            VGroup(cap, cards).shift(DOWN * (cap.get_top()[1] - 3.35))
        self.play(FadeIn(cap, shift=DOWN * 0.1), run_time=0.5)
        self.play(FadeIn(cards[0], shift=UP * 0.3, scale=0.96), run_time=0.9)
        self.wait(max(0.2, self.durs[1] * 0.5 - 2.1))
        self.play(FadeIn(cards[1], shift=UP * 0.3, scale=0.96), run_time=0.9)
        self.catch_up()

        self.seg(2)
        self.play(FadeIn(cards[2], shift=UP * 0.3, scale=0.96), run_time=0.9)
        self.wait(max(0.2, self.durs[2] * 0.42 - 0.9))
        self.play(FadeIn(cards[3], shift=UP * 0.3, scale=0.96), run_time=0.9)
        self.catch_up()

        # --- 结尾 ---
        self.seg(3)
        self.play(FadeOut(VGroup(cards, cap, hdr)), run_time=0.8)
        ax, base, st, curves, fills = cover_art()
        title = T("概率分布图鉴", 100, INK, bold=True).move_to(UP * 1.2)
        thanks = T("谢谢观看", 34, MUTED).next_to(title, DOWN, buff=0.45)
        self.play(FadeIn(title, shift=UP * 0.3), Create(base), run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(s, DOWN) for s in st], lag_ratio=0.1),
                  LaggedStart(*[Create(c) for c in curves], lag_ratio=0.25), FadeIn(fills), run_time=2.0)
        self.play(FadeIn(thanks), run_time=0.8)
        self.catch_up(2.5)
        self.play(FadeOut(VGroup(title, thanks, base, st, curves, fills)), run_time=1.2)
