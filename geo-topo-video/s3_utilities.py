# -*- coding: utf-8 -*-
from common import *

HOUSE_C = "#C9B6FF"
UCOL = [CYAN, YELLOW, ORANGE]          # 自来水 / 电力 / 燃气
UNAME = ["自来水", "电力", "燃气"]


# ------------------------------------------------------------------ 图标
def house_icon(s=1.0):
    body = Polygon([-0.3, -0.25, 0], [0.3, -0.25, 0], [0.3, 0.1, 0], [0, 0.36, 0], [-0.3, 0.1, 0])
    door = Rectangle(width=0.12, height=0.18).move_to([0, -0.16, 0])
    g = VGroup(body, door).set_stroke(HOUSE_C, 3).set_fill(BLACK, 1)
    door.set_fill(HOUSE_C, 0.6)
    g.scale(1.25 * s)
    return VGroup(glow_layers(body, HOUSE_C, layers=3, spread=4, strength=0.8), g)


def drop_shape(r=0.22, wobble=0.0):
    t = np.linspace(0, TAU, 80)
    x = r * np.sin(t) * np.sin(t / 2) + wobble * np.sin(3 * t) * np.sin(t / 2) ** 2
    y = r * np.cos(t)
    m = VMobject()
    m.set_points_smoothly([np.array([a, b, 0]) for a, b in zip(x, y)])
    return m


def bolt_shape():
    pts = [(0.10, 0.26), (-0.14, -0.01), (0.0, -0.01), (-0.08, -0.27), (0.15, 0.05), (0.01, 0.05)]
    return Polygon(*[np.array([a, b, 0]) for a, b in pts])


def utility_icon(k, s=1.0):
    c = UCOL[k]
    ring = Circle(0.4).set_stroke(c, 3).set_fill(BLACK, 1)
    if k == 0:
        sym = drop_shape(0.2).set_fill(c, 0.9).set_stroke(c, 1)
    elif k == 1:
        sym = bolt_shape().set_fill(c, 0.95).set_stroke(c, 1)
    else:
        outer = drop_shape(0.21, 0.025).set_fill(c, 0.9).set_stroke(c, 1)
        inner = drop_shape(0.1).set_fill(YELLOW, 0.95).set_stroke(width=0).shift(DOWN * 0.07)
        sym = VGroup(outer, inner)
    g = VGroup(glow_layers(ring, c, layers=3, spread=4, strength=0.9), ring, sym)
    return g.scale(s)


# ------------------------------------------------------------------ 平面上的 K3,3
HP = [np.array([-3, 1.35, 0]), np.array([0, 1.35, 0]), np.array([3, 1.35, 0])]
UP_ = [np.array([-3, -1.55, 0]), np.array([0, -1.55, 0]), np.array([3, -1.55, 0])]


def P(*xy):
    return [np.array([a, b, 0.0]) for a, b in xy]


# (房子, 供应站, 路径)
PLANE_EDGES = [
    (0, 0, None),
    (1, 0, None),
    (1, 1, None),
    (2, 1, None),
    (2, 2, None),
    (0, 2, P((3, -1.55), (3.35, -2.3), (1.5, -2.7), (-1.5, -2.72), (-3.7, -2.45), (-4.35, -1.0),
             (-4.1, 0.75), (-3, 1.35))),
    (0, 1, P((-3, 1.35), (-3.55, 0.6), (-3.68, -1.0), (-3.3, -2.12), (-2.0, -2.25), (-0.65, -2.1),
             (0, -1.55))),
    (1, 2, P((0, 1.35), (0.55, 2.05), (2.2, 2.38), (3.85, 2.05), (4.35, 0.6), (4.05, -1.0),
             (3, -1.55))),
]
ATTEMPTS = [
    P((3, 1.35), (2.6, 2.0), (1.6, 2.6), (-0.5, 2.8), (-2.5, 2.4)),
    P((3, 1.35), (2.1, 0.1), (1.6, -1.5), (0.9, -2.35), (-1.0, -2.45), (-2.3, -2.3), (-2.85, -2.0),
      (-3, -1.55)),
]


def edge_core(h, u, pts):
    if pts is None:
        m = Line(HP[h], UP_[u])
    else:
        m = smooth_path(pts)
    return m.set_stroke(UCOL[u], 5)


def sample(m, n=300):
    return np.array([m.point_from_proportion(a) for a in np.linspace(0, 1, n)])


def seg_intersect(p, p2, q, q2):
    r, s = p2 - p, q2 - q
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    qp = q - p
    t = (qp[0] * s[1] - qp[1] * s[0]) / den
    u = (qp[0] * r[1] - qp[1] * r[0]) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return t
    return None


def first_hit(path, others, skip=0.6):
    A = sample(path, 400)
    Bs = [sample(o, 300) for o in others]
    start = A[0]
    for i in range(len(A) - 1):
        if np.linalg.norm(A[i] - start) < skip:
            continue
        for B in Bs:
            for j in range(len(B) - 1):
                t = seg_intersect(A[i], A[i + 1], B[j], B[j + 1])
                if t is not None:
                    return (i + t) / (len(A) - 1), A[i] + t * (A[i + 1] - A[i])
    return None


# ------------------------------------------------------------------ 环面上的 K3,3（平铺）
TW, TH = 6.4, 3.6           # 纸的宽、高
_hex = {k: 1.1 * np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a)), 0])
        for k, a in zip(["H1", "U1", "H2", "U2", "H3", "U3"], [90, 30, -30, -90, -150, 150])}
TORUS_V = {"H1": _hex["H1"], "H2": _hex["H2"], "H3": _hex["H3"],
           "U1": _hex["U1"], "U2": _hex["U2"], "U3": _hex["U3"]}
# 每条边：(房子, 供应站, [若干段折线点列])  —— 多段表示穿过纸边
TORUS_EDGES = [
    ("H1", "U1", [[_hex["H1"], _hex["U1"]]]),
    ("H2", "U1", [[_hex["U1"], _hex["H2"]]]),
    ("H2", "U2", [[_hex["H2"], _hex["U2"]]]),
    ("H3", "U2", [[_hex["U2"], _hex["H3"]]]),
    ("H3", "U3", [[_hex["H3"], _hex["U3"]]]),
    ("H1", "U3", [[_hex["U3"], _hex["H1"]]]),
    ("H1", "U2", [[_hex["H1"], _hex["U2"]]]),
    ("H2", "U3", [P((0.953, -0.55), (2.0, -0.5), (3.2, -0.35)),
                  P((-3.2, -0.35), (-2.0, 0.1), (-0.953, 0.55))]),
    ("H3", "U1", [P((0.953, 0.55), (1.35, 1.2), (1.7, 1.8)),
                  P((1.7, -1.8), (0.6, -1.63), (-0.3, -1.6), (-0.9, -1.32), (-0.953, -0.55))]),
]


def u_index(name):
    return int(name[1]) - 1


def torus_edge_paths(e):
    h, u, parts = e
    out = []
    for pts in parts:
        out.append(Line(pts[0], pts[1]) if len(pts) == 2 else smooth_path(pts))
    return out


class Utilities(NScene):
    script_scene = "Utilities"

    def body(self):
        self.chapter(3, "三座房子与三种管线", "The Three Utilities Problem")
        self.show_corner()

        # ---------------- setup
        self.seg("setup")
        houses = VGroup(*[house_icon().move_to(p) for p in HP])
        utils = VGroup(*[utility_icon(k).move_to(p) for k, p in enumerate(UP_)])
        ulabels = VGroup(zh(UNAME[0], 24, UCOL[0]).next_to(UP_[0], RIGHT, buff=0.55),
                         zh(UNAME[1], 24, UCOL[1]).next_to(UP_[1], RIGHT, buff=0.55),
                         zh(UNAME[2], 24, UCOL[2]).next_to(UP_[2], LEFT, buff=0.55))
        for m in [*houses, *utils]:
            m.set_z_index(5)
        self.play(LaggedStart(*[FadeIn(h, shift=DOWN * 0.3) for h in houses], lag_ratio=0.25), run_time=1.4)
        self.wait_until(self.sent_at(1, 0.35))
        self.play(LaggedStart(*[GrowFromCenter(u) for u in utils], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(l) for l in ulabels], lag_ratio=0.3), run_time=1.8)
        self.wait_until(self.sent_at(2))
        rule = VGroup(zh("规则：", 30, GREY_), zh("每座房子连通三个供应站", 30), zh("·", 30, GREY_),
                      zh("管线不能交叉", 30, RED, weight=BOLD)).arrange(RIGHT, buff=0.15).move_to([0, 3.0, 0])
        demo = VGroup(*[Line(HP[0], UP_[u], stroke_width=3, color=UCOL[u]).set_opacity(0.6) for u in range(3)])
        self.play(FadeIn(rule, shift=DOWN * 0.2), run_time=0.8)
        self.play(LaggedStart(*[Create(d) for d in demo], lag_ratio=0.3), run_time=1.5)
        demo2 = VGroup(*[Line(HP[h], UP_[u], stroke_width=3, color=UCOL[u]).set_opacity(0.6)
                         for h in [1, 2] for u in range(3)])
        self.play(LaggedStart(*[Create(d) for d in demo2], lag_ratio=0.15), run_time=1.6)
        cross_pts = []
        for a in [*demo, *demo2]:
            for b in [*demo, *demo2]:
                if a is b:
                    continue
                t = seg_intersect(a.get_start(), a.get_end(), b.get_start(), b.get_end())
                if t is not None and 0.02 < t < 0.98:
                    p = a.get_start() + t * (a.get_end() - a.get_start())
                    if all(np.linalg.norm(p - q) > 0.1 for q in cross_pts):
                        cross_pts.append(p)
        xs = VGroup(*[VGroup(Line(UL, DR), Line(UR, DL)).scale(0.11).set_stroke(RED, 5).move_to(p)
                      for p in cross_pts])
        self.wait_until(self.phrase_at(2, "但任意两条"))
        self.play(LaggedStart(*[GrowFromCenter(x) for x in xs], lag_ratio=0.1), run_time=1.0)
        self.sync(0.0)

        # ---------------- try：画出 8 条
        self.seg("try")
        self.play(FadeOut(demo), FadeOut(demo2), FadeOut(xs), FadeOut(rule), run_time=0.6)
        cores = [edge_core(h, u, pts) for h, u, pts in PLANE_EDGES]
        pipes = [neon(c, strength=0.7) for c in cores]
        cnt_lab = zh("已连接", 26, GREY_)
        cnt = Integer(0, font_size=40, color=WHITE_)
        cnt_tot = MathTex("/\\,9", font_size=40, color=GREY_)
        counter = VGroup(cnt_lab, cnt, cnt_tot).arrange(RIGHT, buff=0.15).to_corner(UR, buff=0.45)
        self.play(FadeIn(counter), run_time=0.4)
        avail = self.remaining(-0.2) - 0.4
        for i, p in enumerate(pipes):
            rt = avail * (0.08 if i < 5 else 0.19)
            new_cnt = Integer(i + 1, font_size=40, color=WHITE_).move_to(cnt)
            self.play(Create(p), Transform(cnt, new_cnt), run_time=rt)
        self.sync(0.0)

        # ---------------- fail：第 9 条
        self.seg("fail")
        dur_each = (self.remaining(0.6)) / 2
        for k, wp in enumerate(ATTEMPTS):
            full = smooth_path(wp).set_stroke(CYAN, 5)
            hit = first_hit(full, cores)
            a_hit, pt = hit
            part = full.copy().pointwise_become_partial(full, 0, a_hit)
            part_g = neon(part, strength=0.8)
            self.play(Create(part_g), run_time=dur_each * 0.55, rate_func=linear)
            xx = VGroup(Line(UL, DR), Line(UR, DL)).scale(0.2).set_stroke(RED, 8).move_to(pt)
            self.play(burst(pt, RED, r1=0.6), GrowFromCenter(xx), part_g.animate.set_color(RED),
                      run_time=dur_each * 0.25)
            self.play(FadeOut(part_g), FadeOut(xx), run_time=dur_each * 0.2)
        self.sync(0.1)

        # ---------------- invariant
        self.seg("invariant")
        k33 = VGroup(*pipes, houses, utils, ulabels)
        self.play(k33.animate.scale(0.5).to_edge(LEFT, buff=0.5).shift(UP * 0.2), FadeOut(counter), run_time=1.2)
        q = VGroup(zh("不够聪明？", 44, GREY_), zh("还是根本不可能？", 44, YELLOW, weight=BOLD)).arrange(DOWN, buff=0.3)
        q.move_to([3.0, 0.8, 0])
        self.play(FadeIn(q[0], shift=UP * 0.2), run_time=0.7)
        self.wait_until(self.phrase_at(0, "还是"))
        self.play(FadeIn(q[1], shift=UP * 0.2), run_time=0.7)
        self.wait_until(self.phrase_at(0, "不变量"))
        inv = zh("需要一个「不变量」", 40, CYAN, weight=BOLD).move_to([3.0, -1.0, 0])
        self.play(FadeIn(inv, scale=1.2), run_time=0.8)
        self.wait_until(self.sent_at(1))
        euler = MathTex("V", "-", "E", "+", "F", "=", "2", font_size=110)
        euler[0].set_color(CYAN)
        euler[2].set_color(YELLOW)
        euler[4].set_color(MAGENTA)
        eg = glow_text(euler, color=PURPLE, strength=0.9)
        e_title = zh("欧拉公式", 36, GREY_).next_to(euler, UP, buff=0.4)
        self.play(FadeOut(k33), FadeOut(q), FadeOut(inv), run_time=0.6)
        self.play(Write(euler), FadeIn(eg[0]), FadeIn(e_title, shift=DOWN * 0.2), run_time=1.6)
        self.sync(0.2)

        # ---------------- euler_def：举例
        self.seg("euler_def")
        self.play(VGroup(eg, e_title).animate.scale(0.5).to_corner(UR, buff=0.5), run_time=0.9)
        gx = np.array([-2.8, -0.2, 0])
        V_ = {k: gx + np.array(v) for k, v in
              dict(a=(-1.9, 0.6, 0), b=(0, 1.9, 0), c=(1.9, 0.6, 0), d=(1.25, -1.6, 0),
                   e=(-1.25, -1.6, 0), f=(0, 0.05, 0)).items()}
        E_ = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "a"), ("f", "a"), ("f", "c"), ("f", "d")]
        faces = [["a", "b", "c", "f"], ["c", "d", "f"], ["d", "e", "a", "f"]]
        fcols = [BLUE, PURPLE, GREEN]
        outer = Rectangle(width=14.2, height=8).set_stroke(width=0).set_fill(ORANGE, 0.06)
        faces_m = VGroup(*[Polygon(*[V_[k] for k in f]).set_stroke(width=0).set_fill(c, 0.32)
                           for f, c in zip(faces, fcols)])
        edges_m = VGroup(*[Line(V_[a], V_[b], stroke_width=4, color=YELLOW) for a, b in E_])
        verts_m = VGroup(*[glow_dot(V_[k], CYAN, 0.1, 3) for k in "abcdef"])
        self.play(LaggedStart(*[GrowFromCenter(v) for v in verts_m], lag_ratio=0.1),
                  LaggedStart(*[Create(e) for e in edges_m], lag_ratio=0.1), run_time=1.6)

        def count_row(sym, col, n):
            return VGroup(MathTex(sym, "=", font_size=56).set_color_by_tex(sym, col),
                          Integer(n, font_size=56, color=col)).arrange(RIGHT, buff=0.2)

        rows = VGroup(count_row("V", CYAN, 6), count_row("E", YELLOW, 8), count_row("F", MAGENTA, 4))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([3.4, 0.6, 0])
        self.wait_until(self.phrase_at(0, "顶点数"))
        self.play(LaggedStart(*[Indicate(v, scale_factor=1.6, color=WHITE) for v in verts_m], lag_ratio=0.08),
                  FadeIn(rows[0], shift=LEFT * 0.3), run_time=1.2)
        self.wait_until(self.phrase_at(0, "边数"))
        self.play(LaggedStart(*[ShowPassingFlash(e.copy().set_stroke(WHITE, 8), time_width=0.6)
                                for e in edges_m], lag_ratio=0.08),
                  FadeIn(rows[1], shift=LEFT * 0.3), run_time=1.2)
        self.wait_until(self.phrase_at(0, "区域数"))
        self.add(faces_m, edges_m, verts_m)
        self.bring_to_back(faces_m)
        self.play(LaggedStart(*[FadeIn(f) for f in faces_m], lag_ratio=0.3), run_time=1.2)
        self.wait_until(self.phrase_at(0, "包括外面"))
        self.add(outer)
        self.bring_to_back(outer)
        out_lab = zh("外部区域也算一个", 24, ORANGE).move_to(gx + np.array([0, -2.45, 0]))
        self.play(FadeIn(outer), FadeIn(out_lab), FadeIn(rows[2], shift=LEFT * 0.3), run_time=1.0)
        self.wait_until(self.sent_at(1))
        calc = MathTex("6", "-", "8", "+", "4", "=", "2", font_size=60).next_to(rows, DOWN, buff=0.6)
        calc[0].set_color(CYAN)
        calc[2].set_color(YELLOW)
        calc[4].set_color(MAGENTA)
        calc[6].set_color(GREEN)
        self.play(Write(calc), run_time=1.2)
        self.play(Indicate(calc[6], color=GREEN, scale_factor=1.5), run_time=0.8)
        self.sync(0.2)

        # ---------------- euler_start：从一个点开始
        self.seg("euler_start")
        self.play(FadeOut(VGroup(faces_m, edges_m, verts_m, outer, out_lab, calc)), run_time=0.7)
        gx = np.array([-3.0, 0.0, 0])
        pos = [gx + np.array(p) for p in [(0, 0, 0), (1.6, 1.4, 0), (1.7, -1.3, 0), (-1.7, 1.5, 0),
                                           (-1.6, -1.4, 0), (0.1, 2.6, 0), (0.0, -2.5, 0)]]
        Vn, En, Fn = [1], [0], [1]
        vals = [rows[0][1], rows[1][1], rows[2][1]]
        tally = MathTex("V", "-", "E", "+", "F", "=", "2", font_size=56)
        tally[0].set_color(CYAN)
        tally[2].set_color(YELLOW)
        tally[4].set_color(MAGENTA)
        tally[6].set_color(GREEN)
        tally.next_to(rows, DOWN, buff=0.6)
        tbox = SurroundingRectangle(tally, color=GREEN, buff=0.18, corner_radius=0.1)

        def set_counts(anims, dv=0, de=0, df=0):
            for i, d in enumerate([dv, de, df]):
                if d:
                    new = Integer([Vn, En, Fn][i][0] + d, font_size=56,
                                  color=[CYAN, YELLOW, MAGENTA][i]).move_to(vals[i], aligned_edge=LEFT)
                    [Vn, En, Fn][i][0] += d
                    plus = MathTex("+1", font_size=34, color=GREEN).next_to(vals[i], RIGHT, buff=0.35)
                    anims += [Transform(vals[i], new),
                              Succession(FadeIn(plus, shift=UP * 0.2, run_time=0.3),
                                         FadeOut(plus, shift=UP * 0.3, run_time=0.5))]
            return anims

        for i, n in enumerate([1, 0, 1]):
            vals[i].become(Integer(n, font_size=56, color=[CYAN, YELLOW, MAGENTA][i]).move_to(vals[i], aligned_edge=LEFT))
        plane = Rectangle(width=14.2, height=8).set_stroke(width=0).set_fill(ORANGE, 0.06)
        v0 = glow_dot(pos[0], CYAN, 0.11, 4)
        euler_stuff = [plane, v0]
        self.add(plane)
        self.bring_to_back(plane)
        self.play(FadeIn(plane), GrowFromCenter(v0), run_time=0.8)
        start_calc = MathTex("1", "-", "0", "+", "1", "=", "2", font_size=56).next_to(rows, DOWN, buff=0.6)
        start_calc[6].set_color(GREEN)
        self.wait_until(self.phrase_at(0, "1 − 0 + 1"))
        self.play(Write(start_calc), run_time=1.0)
        self.wait_until(self.sent_at(1))
        self.play(ReplacementTransform(start_calc, tally), Create(tbox), run_time=0.8)
        self.sync(0.0)

        built_edges = VGroup()
        vdots = [v0]

        def add_edge(i, j, new_vertex, face_pts=None, col=BLUE, rt=1.0):
            anims = []
            ln = Line(pos[i], pos[j], stroke_width=5, color=YELLOW)
            built_edges.add(ln)
            euler_stuff.append(ln)
            anims.append(Create(ln))
            if new_vertex:
                d = glow_dot(pos[j], CYAN, 0.11, 4)
                vdots.append(d)
                euler_stuff.append(d)
                anims.append(GrowFromCenter(d))
                set_counts(anims, dv=1, de=1)
            else:
                f = Polygon(*[pos[k] for k in face_pts]).set_stroke(width=0).set_fill(col, 0.35)
                euler_stuff.append(f)
                self.add(f)
                self.bring_to_back(f)
                self.bring_to_back(plane)
                anims.append(FadeIn(f))
                set_counts(anims, de=1, df=1)
            self.play(*anims, Indicate(tbox, color=GREEN, scale_factor=1.04), run_time=rt)

        # ---------------- case1：连向新顶点
        self.seg("euler_case1")
        lab1 = zh("连向新顶点：V +1，E +1", 28, CYAN).move_to([3.4, -2.6, 0])
        self.play(FadeIn(lab1, shift=UP * 0.2), run_time=0.4)
        add_edge(0, 1, True, rt=1.2)
        add_edge(1, 2, True, rt=1.2)
        self.sync(0.0)

        # ---------------- case2：连接已有顶点
        self.seg("euler_case2")
        lab2 = zh("连接已有顶点：E +1，F +1", 28, MAGENTA).move_to(lab1)
        self.play(FadeOut(lab1, shift=UP * 0.2), FadeIn(lab2, shift=UP * 0.2), run_time=0.5)
        self.wait_until(self.phrase_at(0, "把某个区域"))
        add_edge(2, 0, False, [0, 1, 2], BLUE, rt=1.6)
        self.sync(0.0)

        # ---------------- euler_inv：继续加边，不变
        self.seg("euler_inv")
        self.play(FadeOut(lab2), run_time=0.3)
        rt = (self.remaining(-0.3)) / 6
        add_edge(0, 3, True, rt=rt)
        add_edge(3, 1, False, [0, 3, 1], PURPLE, rt=rt)
        add_edge(0, 4, True, rt=rt)
        add_edge(4, 2, False, [0, 4, 2], GREEN, rt=rt)
        add_edge(3, 5, True, rt=rt)
        add_edge(5, 1, False, [3, 5, 1], PINK, rt=rt)
        self.play(Indicate(tally[6], color=GREEN, scale_factor=1.6), run_time=0.6)
        self.sync(0.1)

        # ---------------- apply1：V=6, E=9 ⇒ F=5
        self.seg("apply1")
        self.play(FadeOut(VGroup(*euler_stuff)), run_time=0.7)
        k33.scale(1 / 0.5).move_to(ORIGIN)
        k33.scale(0.62).move_to([-3.3, 0.05, 0])
        new_tally = tally.copy().scale(0.8).move_to([3.6, 0.4, 0])
        self.play(FadeIn(k33), rows.animate.scale(0.8).move_to([3.6, 1.75, 0]),
                  Transform(tally, new_tally), FadeOut(tbox), FadeOut(VGroup(eg, e_title)), run_time=0.9)
        for i, n in enumerate([6, 9]):
            new = Integer(n, font_size=45, color=[CYAN, YELLOW][i]).move_to(vals[i], aligned_edge=LEFT)
            self.play(Transform(vals[i], new), run_time=0.5)
        qF = MathTex("?", font_size=45, color=MAGENTA).move_to(vals[2], aligned_edge=LEFT)
        self.play(Transform(vals[2], qF), run_time=0.3)
        self.wait_until(self.phrase_at(0, "根据欧拉公式"))
        solve = MathTex("6", "-", "9", "+", "F", "=", "2", r"\ \Rightarrow\ ", "F", "=", "5", font_size=50)
        solve[0].set_color(CYAN)
        solve[2].set_color(YELLOW)
        solve[4].set_color(MAGENTA)
        solve[8].set_color(MAGENTA)
        solve[10].set_color(MAGENTA)
        solve.move_to(tally)
        solve.scale(0.8).move_to([3.6, 0.4, 0])
        self.play(ReplacementTransform(tally, solve), run_time=1.2)
        newF = Integer(5, font_size=45, color=MAGENTA).move_to(vals[2], aligned_edge=LEFT)
        self.play(Transform(vals[2], newF), Indicate(solve[8:], color=MAGENTA), run_time=0.9)
        self.sync(0.1)

        # ---------------- apply2：每个区域至少 4 条边
        self.seg("apply2")
        # 一个真实的区域：H1→U1→H2→U2→(e7)→H1
        c_e1, c_e2, c_e3, c_e7 = cores[0], cores[1], cores[2], cores[6]
        bpts = list(sample(c_e1, 30)) + list(sample(c_e2, 30)[::-1]) + list(sample(c_e3, 30)) + \
            list(sample(c_e7, 80)[::-1])
        face = VMobject().set_points_as_corners(bpts + [bpts[0]])
        face.set_stroke(width=0).set_fill(GREEN, 0.35)
        self.add(face)
        self.bring_to_back(face)
        self.play(FadeIn(face), run_time=0.8)
        loop = VMobject().set_points_as_corners(bpts + [bpts[0]]).set_stroke(WHITE, 6)
        self.wait_until(self.phrase_at(0, "所以沿着"))
        order = VGroup(house_icon(0.55), MathTex(r"\to", font_size=36), utility_icon(0, 0.55),
                       MathTex(r"\to", font_size=36), house_icon(0.55), MathTex(r"\to", font_size=36),
                       utility_icon(1, 0.55), MathTex(r"\to", font_size=36), house_icon(0.55),
                       MathTex(r"\cdots", font_size=36)).arrange(RIGHT, buff=0.12)
        order.move_to([3.6, -1.35, 0])
        self.play(ShowPassingFlash(loop, time_width=0.4), FadeIn(order, lag_ratio=0.1), run_time=2.4)
        self.wait_until(self.phrase_at(0, "一圈至少"))
        ge4 = VGroup(zh("每个区域", 30), MathTex(r"\ge 4", font_size=50, color=GREEN), zh("条边", 30)).arrange(RIGHT, buff=0.15)
        ge4.move_to([3.6, -0.55, 0])
        self.play(FadeIn(ge4, scale=1.2), run_time=0.8)
        self.sync(0.1)

        # ---------------- apply3：2E = 18 < 20
        self.seg("apply3")
        # 一条边两侧的两个区域
        mid = c_e3.point_from_proportion(0.5)
        sideL = Arrow(mid + LEFT * 0.75, mid + LEFT * 0.12, buff=0, color=GREEN, stroke_width=4)
        sideR = Arrow(mid + RIGHT * 0.75, mid + RIGHT * 0.12, buff=0, color=PINK, stroke_width=4)
        self.play(GrowArrow(sideL), GrowArrow(sideR),
                  ShowPassingFlash(c_e3.copy().set_stroke(WHITE, 10), time_width=1), run_time=1.0)
        self.play(FadeOut(order), FadeOut(ge4), run_time=0.5)
        l1 = VGroup(zh("所有区域的边数之和", 28), MathTex("=", "2E", "=", "18", font_size=46)).arrange(RIGHT, buff=0.2)
        l1[1][3].set_color(YELLOW)
        l2 = VGroup(zh("每个区域至少 4 条", 28), MathTex(r"\ge", "4F", "=", "20", font_size=46)).arrange(RIGHT, buff=0.2)
        l2[1][3].set_color(MAGENTA)
        lines = VGroup(l1, l2).arrange(DOWN, aligned_edge=RIGHT, buff=0.3).move_to([3.6, -0.85, 0])
        self.wait_until(self.phrase_at(0, "所以把所有"))
        self.play(FadeIn(l1, shift=UP * 0.2), run_time=0.8)
        self.wait_until(self.phrase_at(0, "总数是"))
        self.play(Indicate(l1[1][3], color=YELLOW, scale_factor=1.4), run_time=0.8)
        self.wait_until(self.sent_at(1))
        self.play(FadeIn(l2, shift=UP * 0.2), run_time=0.8)
        self.wait_until(self.phrase_at(1, "18 小于 20"))
        contra = MathTex("18", r"\ \ge\ ", "20", font_size=80)
        contra[0].set_color(YELLOW)
        contra[2].set_color(MAGENTA)
        contra.move_to([3.6, -2.3, 0])
        bad = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(RED, 10).scale(0.5).move_to(contra[1])
        self.play(FadeIn(contra, scale=1.3), run_time=0.7)
        self.play(GrowFromCenter(bad), contra.animate.set_color(RED), run_time=0.5)
        self.play(Wiggle(VGroup(contra, bad), scale_value=1.15), run_time=0.9)
        self.sync(0.1)

        # ---------------- conclude：不可能
        self.seg("conclude")
        stamp = zh("平面上：不可能", 80, RED, weight=BOLD)
        stamp_box = SurroundingRectangle(stamp, color=RED, buff=0.3, stroke_width=8)
        st = VGroup(stamp_box, stamp).rotate(-8 * DEGREES).move_to(ORIGIN)
        dim = Rectangle(width=14.2, height=8).set_fill(BLACK, 0.7).set_stroke(width=0)
        self.play(FadeIn(dim), FadeIn(st, scale=2.5, rate_func=rush_into), run_time=0.6)
        self.play(Wiggle(st, scale_value=1.05, rotation_angle=0.03 * TAU), run_time=0.7)
        self.sync(0.3)

        # ---------------- torus1：纸 → 环面（平铺）
        self.seg("torus1")
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not self.corner])), run_time=0.8)
        paper = Rectangle(width=TW, height=TH).set_stroke(GREY_, 2).set_fill("#151E58", 1)
        L_, R_ = paper.get_left(), paper.get_right()

        def edge_arrows(a, b, col, n=1):
            mid = (a + b) / 2
            d = (b - a) / np.linalg.norm(b - a)
            g = VGroup()
            for k in range(n):
                g.add(Arrow(mid - d * 0.35 + d * 0.22 * k, mid + d * 0.15 + d * 0.22 * k, buff=0,
                            stroke_width=6, color=col, max_tip_length_to_length_ratio=0.6))
            return g

        corners = [paper.get_corner(DL), paper.get_corner(DR), paper.get_corner(UR), paper.get_corner(UL)]
        left_e = Line(corners[0], corners[3], color=CYAN, stroke_width=6)
        right_e = Line(corners[1], corners[2], color=CYAN, stroke_width=6)
        bot_e = Line(corners[0], corners[1], color=MAGENTA, stroke_width=6)
        top_e = Line(corners[3], corners[2], color=MAGENTA, stroke_width=6)
        a_lr = VGroup(edge_arrows(corners[0], corners[3], CYAN), edge_arrows(corners[1], corners[2], CYAN))
        a_tb = VGroup(edge_arrows(corners[0], corners[1], MAGENTA, 2), edge_arrows(corners[3], corners[2], MAGENTA, 2))
        q2 = zh("如果建在甜甜圈上？", 40, YELLOW, weight=BOLD).move_to([0, 2.75, 0])
        self.play(FadeIn(q2, shift=DOWN * 0.2), run_time=0.8)
        self.wait_until(self.sent_at(1))
        self.play(FadeIn(paper), run_time=0.8)
        self.wait_until(self.phrase_at(1, "左右两边"))
        lr_neon = VGroup(neon(left_e.copy()), neon(right_e.copy()))
        tb_neon = VGroup(neon(top_e.copy()), neon(bot_e.copy()))
        self.play(Create(lr_neon), FadeIn(a_lr), run_time=1.0)
        self.play(Indicate(VGroup(left_e, right_e)), run_time=0.6)
        self.wait_until(self.phrase_at(1, "上下两边"))
        self.play(Create(tb_neon), FadeIn(a_tb), run_time=1.0)
        self.wait_until(self.phrase_at(1, "环面"))
        tlab = zh("= 环面", 34, WHITE_).next_to(paper, RIGHT, buff=0.35)
        self.play(FadeOut(q2), FadeIn(tlab, shift=LEFT * 0.2), run_time=0.7)
        self.sync(0.1)

        # ---------------- torus2：在环面上连线
        self.seg("torus2")
        self.play(FadeOut(tlab), run_time=0.4)
        tv = {}
        for k, p in TORUS_V.items():
            ic = house_icon(0.5) if k[0] == "H" else utility_icon(u_index(k), 0.5)
            tv[k] = ic.move_to(p).set_z_index(5)
        self.play(LaggedStart(*[FadeIn(tv[k], scale=0.5) for k in ["H1", "H2", "H3", "U1", "U2", "U3"]],
                              lag_ratio=0.1), run_time=1.0)
        normal = [e for e in TORUS_EDGES if len(e[2]) == 1]
        wraps = [e for e in TORUS_EDGES if len(e[2]) == 2]
        tpipes = VGroup()
        anims = []
        for e in normal:
            m = torus_edge_paths(e)[0].set_stroke(UCOL[u_index(e[1])], 4.5)
            g = neon(m, strength=0.7)
            tpipes.add(g)
            anims.append(Create(g))
        self.play(LaggedStart(*anims, lag_ratio=0.12), run_time=1.8)
        self.wait_until(self.phrase_at(0, "从右边穿出去"))
        for wi, e in enumerate(wraps):
            col = UCOL[u_index(e[1])]
            paths = [m.set_stroke(col, 4.5) for m in torus_edge_paths(e)]
            g1, g2 = neon(paths[0], strength=0.7), neon(paths[1], strength=0.7)
            ex, en_ = paths[0].get_end(), paths[1].get_start()
            self.play(Create(g1), run_time=1.0, rate_func=rush_into)
            self.play(Flash(ex, color=col, line_length=0.25), Flash(en_, color=col, line_length=0.25),
                      Indicate(a_lr if wi == 0 else a_tb, color=WHITE), run_time=0.6)
            self.play(Create(g2), run_time=1.0, rate_func=rush_from)
            tpipes.add(g1, g2)
            if wi == 0:
                self.wait_until(self.phrase_at(0, "从上边穿出去"))
        self.wait_until(self.sent_at(1))
        ok = VGroup(zh("9 / 9", 40, GREEN, weight=BOLD), zh("零交叉", 40, GREEN, weight=BOLD)).arrange(RIGHT, buff=0.4)
        ok.move_to([0, 2.65, 0])
        okg = glow_text(ok, GREEN, strength=0.8)
        self.play(FadeIn(okg, scale=1.3), run_time=0.7)
        self.play(LaggedStart(*[ShowPassingFlash(p[1].copy().set_stroke(WHITE, 8), time_width=0.5)
                                for p in tpipes], lag_ratio=0.05), run_time=1.6)
        self.sync(0.2)
        # 过渡到 3D：图标收成小圆点，与下一镜头首帧一致
        dots = VGroup(*[Dot(TORUS_V[k], radius=0.12, color=(HOUSE_C if k[0] == "H" else UCOL[u_index(k)]))
                        for k in TORUS_V])
        self.play(FadeOut(okg), FadeOut(a_lr), FadeOut(a_tb),
                  FadeOut(lr_neon), FadeOut(tb_neon),
                  *[ReplacementTransform(tv[k], d) for k, d in zip(TORUS_V, dots)],
                  paper.animate.set_stroke(width=0), run_time=0.8)
        self.wait(0.2)


# ------------------------------------------------------------------ 3D：卷成甜甜圈
def roll(X, Y, s1, s2):
    """纸面点 (X,Y)（纸宽 TW、高 TH，中心在原点）在卷曲参数 s1(上下相粘)、s2(左右相粘)下的位置。向量化。"""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    rho0 = TH / TAU
    if s1 < 1e-4:
        ys, zs = Y, np.zeros_like(Y)
    else:
        rho = TH / (TAU * s1)
        a = TAU * s1 * (Y / TH)
        ys, zs = rho * np.sin(a), -rho * (1 - np.cos(a))
    off_n, off_z = ys, zs + rho0 * s1
    if s2 < 1e-4:
        return np.stack([X, off_n, off_z], axis=-1)
    Rb = TW / (TAU * s2)
    b = TAU * s2 * (X / TW)
    px = (Rb + off_n) * np.sin(b)
    py = (Rb + off_n) * np.cos(b) - Rb + (TW / TAU) * s2
    return np.stack([px, py, off_z], axis=-1)


def lift(X, Y, s1, s2, eps=0.03):
    """映射到 3D 后沿纸的“正面”法向外移 eps，使曲线浮在曲面上方。"""
    h = 1e-3
    p = roll(X, Y, s1, s2)
    n = np.cross(roll(np.asarray(X) + h, Y, s1, s2) - p, roll(X, np.asarray(Y) + h, s1, s2) - p)
    ln = np.linalg.norm(n, axis=-1, keepdims=True)
    return p + eps * n / np.maximum(ln, 1e-12)


class UtilitiesTorus(NThreeDScene):
    script_scene = "Utilities"

    def body(self):
        corner = make_corner(3, "三座房子与三种管线")
        self.add_fixed_in_frame_mobjects(corner)
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)
        s1 = ValueTracker(0.0)
        s2 = ValueTracker(0.0)

        surf = FastSurface(lambda U, V: roll(U, V, 0, 0), [-TW / 2, TW / 2], [-TH / 2, TH / 2],
                           resolution=(48, 24), color="#1E2C80", opacity=0.72, amb=0.45, stroke=0.5)
        edge_samples = []
        for e in TORUS_EDGES:
            col = UCOL[u_index(e[1])]
            for m in torus_edge_paths(e):
                edge_samples.append(sample(m, 26))
        curves = VGroup()
        for e in TORUS_EDGES:
            col = UCOL[u_index(e[1])]
            for m in torus_edge_paths(e):
                pts = sample(m, 26)
                curves.add(FastPolyline(lift(pts[:, 0], pts[:, 1], 0, 0), col, 5))
        vkeys = list(TORUS_V)
        V2 = np.array([TORUS_V[k] for k in vkeys])
        dots = VGroup()
        for k in vkeys:
            d = Dot(ORIGIN, radius=0.12, color=(HOUSE_C if k[0] == "H" else UCOL[u_index(k)]))
            d.depth_sort = True
            dots.add(d)

        def refresh(_m=None):
            a, b = s1.get_value(), s2.get_value()
            surf.update_mesh(lambda U, V: roll(U, V, a, b))
            for c, pts in zip(curves, edge_samples):
                c.update_points(lift(pts[:, 0], pts[:, 1], a, b))
            Q = lift(V2[:, 0], V2[:, 1], a, b, 0.05)
            for d, q in zip(dots, Q):
                d.move_to(q)

        refresh()
        driver = Mobject()
        driver.add_updater(refresh)
        self.add(surf, curves, dots, driver)

        self.seg("torus3")
        self.play(s1.animate.set_value(1.0), run_time=4.5, rate_func=smooth)
        self.move_camera(phi=62 * DEGREES, theta=-80 * DEGREES, zoom=1.6,
                         added_anims=[s2.animate.set_value(1.0)], run_time=5.0)
        driver.clear_updaters()
        self.begin_ambient_camera_rotation(rate=0.16)
        self.wait(1.5)
        self.sync(0.2)

        self.seg("chi")
        eq = MathTex("V", "-", "E", "+", "F", "=", "0", font_size=64)
        eq[0].set_color(CYAN)
        eq[2].set_color(YELLOW)
        eq[4].set_color(MAGENTA)
        eq[6].set_color(GREEN)
        nums = MathTex("6", "-", "9", "+", "3", "=", "0", font_size=48, color=GREY_)
        lab = zh("环面上", 30, GREY_)
        blk = VGroup(lab, eq, nums).arrange(DOWN, buff=0.25).to_corner(UR, buff=0.6)
        self.add_fixed_in_frame_mobjects(blk)
        blk.set_opacity(0)
        self.play(blk.animate.set_opacity(1), run_time=1.0)
        self.wait_until(self.phrase_at(0, "欧拉示性数"))
        chi = VGroup(zh("欧拉示性数", 30, WHITE_), MathTex(r"\chi = 2 - 2g", font_size=48, color=YELLOW)).arrange(DOWN, buff=0.2)
        gnote = zh("g = 洞的个数", 24, GREY_).next_to(chi, DOWN, buff=0.15)
        table = VGroup(
            VGroup(zh("球面 / 平面", 26), MathTex(r"g=0,\ \chi=2", font_size=36, color=CYAN)).arrange(RIGHT, buff=0.3),
            VGroup(zh("环面", 26), MathTex(r"g=1,\ \chi=0", font_size=36, color=GREEN)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        chig = VGroup(chi, gnote, table).arrange(DOWN, buff=0.3).to_corner(DL, buff=0.6).shift(UP * 0.5)
        self.add_fixed_in_frame_mobjects(chig)
        chig.set_opacity(0)
        self.play(chig.animate.set_opacity(1), run_time=1.0)
        self.wait_until(self.sent_at(1))
        moral = zh("决定答案的，是空间的形状", 40, YELLOW, weight=BOLD).to_edge(DOWN, buff=0.85)
        self.add_fixed_in_frame_mobjects(moral)
        moral.set_opacity(0)
        self.wait_until(self.phrase_at(1, "决定答案的"))
        self.play(moral.animate.set_opacity(1), chig.animate.set_opacity(0.0), run_time=1.0)
        self.sync(0.8)
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.0)
