# -*- coding: utf-8 -*-
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from common import *

# 僧人在山路上的位置（0 = 山脚，1 = 山顶），τ ∈ [0,1] 对应 6:00 → 18:00
P_UP = PchipInterpolator([0, .12, .22, .30, .42, .50, .60, .70, .80, .90, 1],
                         [0, .16, .16, .30, .40, .34, .50, .62, .62, .86, 1])
P_DOWN = PchipInterpolator([0, .10, .25, .35, .48, .60, .68, .80, .92, 1],
                           [1, .95, .78, .78, .60, .52, .40, .22, .08, 0])
TAU_MEET = brentq(lambda t: P_UP(t) - P_DOWN(t), 0, 1)


class DigitalClock(VGroup):
    """HH:MM 数字时钟，数字字形预先缓存，逐帧只切换可见性。"""

    def __init__(self, size=48, color=WHITE_):
        super().__init__()
        self.cells = []
        for k in range(4):
            cell = VGroup(*[Text(str(d), font="JetBrains Mono", font_size=size, color=color,
                                 weight=BOLD) for d in range(10)])
            self.cells.append(cell)
        colon = Text(":", font="JetBrains Mono", font_size=size, color=color, weight=BOLD)
        row = VGroup(self.cells[0][0], self.cells[1][0], colon, self.cells[2][0], self.cells[3][0])
        row.arrange(RIGHT, buff=0.04)
        for k, idx in zip(range(4), [0, 1, 3, 4]):
            for g in self.cells[k]:
                g.move_to(row[idx])
        self.add(*self.cells, colon)
        self.set_hours(6.0)

    def set_hours(self, h):
        m = int(round(h * 60)) % (24 * 60)
        digits = [m // 600, (m // 60) % 10, (m % 60) // 10, m % 10]
        for cell, dg in zip(self.cells, digits):
            for i, g in enumerate(cell):
                g.set_opacity(1 if i == dg else 0)
        return self


def make_mountain():
    sil = [(-7.6, -2.9), (-6.4, -2.3), (-5.2, -1.6), (-4.3, -0.7), (-3.4, 0.4), (-2.7, 1.3),
           (-2.0, 2.2), (-1.3, 1.6), (-0.4, 0.7), (0.6, -0.3), (1.7, -1.3), (2.9, -2.2), (4.2, -2.9)]
    outline = smooth_path(sil)
    body = outline.copy()
    body.add_line_to(np.array([4.2, -3.4, 0]))
    body.add_line_to(np.array([-7.6, -3.4, 0]))
    body.add_line_to(np.array([-7.6, -2.9, 0]))
    body.set_stroke(width=0).set_fill(color=["#1A1240", "#2B2470", "#3C3A9A"], opacity=1)
    body.set_sheen_direction(UP)
    outline.set_stroke(PURPLE, width=3)
    back = smooth_path([(-1.5, -3.0), (0.8, -0.6), (2.6, 0.9), (3.7, 1.5), (4.9, 0.6),
                        (6.2, -0.8), (7.6, -2.0)])
    back.add_line_to(np.array([7.6, -3.4, 0]))
    back.add_line_to(np.array([-1.5, -3.4, 0]))
    back.set_stroke(BLUE, width=1.5, opacity=0.5).set_fill(color=["#0B0F2A", "#151C4A"], opacity=1)
    back.set_sheen_direction(UP)
    return back, body, neon(outline, strength=0.8)


def make_path():
    wp = [(-5.0, -2.45), (-3.7, -2.05), (-4.2, -1.55), (-2.9, -1.15), (-3.5, -0.6), (-2.3, -0.25),
          (-2.9, 0.3), (-1.8, 0.55), (-2.3, 1.05), (-1.6, 1.3), (-2.0, 1.95)]
    return smooth_path(wp)


def make_temple(base):
    roof1 = Polygon([-0.42, 0.28, 0], [0.42, 0.28, 0], [0, 0.55, 0])
    body = Rectangle(width=0.5, height=0.28).move_to([0, 0.14, 0])
    roof2 = Polygon([-0.3, 0.6, 0], [0.3, 0.6, 0], [0, 0.82, 0]).shift(DOWN * 0.05)
    t = VGroup(body, roof1, roof2).set_stroke(YELLOW, 2.5).set_fill(YELLOW, 0.15)
    t.move_to(base, aligned_edge=DOWN)
    return VGroup(glow_layers(t, layers=3, spread=4, strength=0.8), t)


def make_sun():
    core = Circle(0.32).set_fill(YELLOW, 1).set_stroke(width=0)
    halo = VGroup(*[Circle(0.32 + 0.12 * i).set_fill(ORANGE, 0.16 / i).set_stroke(width=0)
                    for i in range(1, 6)])
    rays = VGroup(*[Line(0.45 * np.array([np.cos(a), np.sin(a), 0]),
                         0.65 * np.array([np.cos(a), np.sin(a), 0]),
                         color=YELLOW, stroke_width=3) for a in np.linspace(0, TAU, 12, endpoint=False)])
    return VGroup(halo, rays, core)


def sun_pos(tau):
    a = np.deg2rad(165 - 150 * tau)
    return np.array([1.2 + 6.0 * np.cos(a), -1.6 + 4.6 * np.sin(a), 0])


class Monk(NScene):
    script_scene = "Monk"

    def body(self):
        self.chapter(1, "僧人登山", "The Monk on the Mountain")
        self.show_corner()

        back, mountain, ridge = make_mountain()
        path = make_path()
        path_dash = DashedVMobject(path.copy().set_stroke(GREY_, 2.5, opacity=0.8), num_dashes=70)
        temple = make_temple(path.get_end() + UP * 0.05)
        foot = glow_dot(path.get_start(), GREEN, radius=0.06, halo=3)
        foot_lab = zh("山脚", 22, GREY_).next_to(path.get_start(), DOWN, buff=0.15)
        top_lab = zh("山顶寺庙", 22, YELLOW).next_to(temple, RIGHT, buff=0.2)

        tau = ValueTracker(0)
        sun = make_sun().move_to(sun_pos(0))
        sun.add_updater(lambda m: m.move_to(sun_pos(tau.get_value())))

        clock = DigitalClock(54)
        day_lab = zh("第一天", 30, ORANGE, weight=BOLD)
        clock_box = VGroup(day_lab, clock).arrange(DOWN, buff=0.15)
        clock_panel = panel(2.6, 1.7, color=ORANGE).move_to(clock_box)
        clock_grp = VGroup(clock_panel, clock_box).to_corner(UR, buff=0.4)
        clock.add_updater(lambda m: m.set_hours(6 + 12 * tau.get_value()))

        monk_up = glow_dot(path.get_start(), ORANGE, radius=0.11, halo=5)
        monk_up.add_updater(lambda m: m.move_to(path.point_from_proportion(
            float(np.clip(P_UP(tau.get_value()), 0, 1)))))

        # 状态小标签：上行 / 停 / 后退
        st_tags = VGroup(zh("前进", 20, ORANGE), zh("停下", 20, GREY_), zh("后退", 20, RED))

        def tag_update(g, fn=P_UP, dot=monk_up, sign=1):
            t = tau.get_value()
            v = sign * float(fn(min(t + 0.004, 1)) - fn(max(t - 0.004, 0)))
            k = 0 if v > 0.0006 else (1 if v > -0.0006 else 2)
            for i, s in enumerate(g):
                s.set_opacity(1 if i == k else 0)
            g.next_to(dot, LEFT, buff=0.15)

        # ---------------- setup1 + setup2：第一天上山
        self.seg("setup1")
        self.add(back, mountain)
        self.play(FadeIn(back, shift=UP * 0.3), FadeIn(mountain, shift=UP * 0.3),
                  Create(ridge), FadeIn(sun), run_time=1.6)
        self.play(Create(path_dash), FadeIn(foot), FadeIn(foot_lab), run_time=1.2)
        self.play(FadeIn(temple, shift=DOWN * 0.2), FadeIn(top_lab), FadeIn(clock_grp), run_time=0.9)
        self.play(FadeIn(monk_up, scale=2), run_time=0.5)
        st_tags.add_updater(tag_update)
        self.add(st_tags)
        # 第二段旁白在爬山动画进行中开始
        self.seg("setup2", at=self._seg_end + 0.3)
        self.play(tau.animate.set_value(1), run_time=self.until(self._seg_end), rate_func=linear)
        st_tags.clear_updaters()
        self.play(FadeOut(st_tags), Flash(temple[1].get_top(), color=YELLOW, line_length=0.3),
                  run_time=0.6)

        # ---------------- setup3：第二天下山
        self.seg("setup3")
        day2 = zh("第二天", 30, CYAN, weight=BOLD).move_to(day_lab)
        monk_dn = glow_dot(path.get_end(), CYAN, radius=0.11, halo=5)
        tau2 = ValueTracker(0)
        monk_dn.add_updater(lambda m: m.move_to(path.point_from_proportion(
            float(np.clip(P_DOWN(tau2.get_value()), 0, 1)))))
        clock.clear_updaters()
        clock.add_updater(lambda m: m.set_hours(6 + 12 * tau2.get_value()))
        sun.clear_updaters()
        sun.add_updater(lambda m: m.move_to(sun_pos(tau2.get_value())))
        monk_up.clear_updaters()
        self.play(FadeOut(monk_up), FadeIn(monk_dn, scale=2),
                  Transform(day_lab, day2), clock_panel.animate.set_stroke(CYAN),
                  run_time=0.8)
        self.play(tau2.animate.set_value(1), run_time=self.remaining(-0.2), rate_func=linear)
        self.sync(0.2)

        # ---------------- question
        self.seg("question")
        q_panel = panel(6.2, 2.6, color=MAGENTA).move_to([3.6, 0.35, 0])
        q1 = zh("是否一定存在某个时刻，", 32)
        q2 = zh("僧人在两天的这一时刻，", 32)
        q3 = zh("恰好位于山路上同一位置？", 32, YELLOW, weight=BOLD)
        qt = VGroup(q1, q2, q3).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(q_panel)
        qmark = Text("?", font=LATIN, font_size=200, weight=BOLD, color=MAGENTA).set_opacity(0.18)
        qmark.move_to(q_panel.get_right() + LEFT * 0.9)
        # 两个“幽灵”僧人：同一时刻两天的位置
        ghost_t = ValueTracker(0)
        g_up = glow_dot(ORIGIN, ORANGE, radius=0.09, halo=3)
        g_dn = glow_dot(ORIGIN, CYAN, radius=0.09, halo=3)
        g_up.add_updater(lambda m: m.move_to(path.point_from_proportion(float(np.clip(P_UP(ghost_t.get_value()), 0, 1)))))
        g_dn.add_updater(lambda m: m.move_to(path.point_from_proportion(float(np.clip(P_DOWN(ghost_t.get_value()), 0, 1)))))
        monk_dn.clear_updaters()
        self.play(FadeOut(monk_dn), FadeIn(q_panel), FadeIn(qmark, scale=0.5),
                  LaggedStart(*[FadeIn(q, shift=UP * 0.2) for q in qt], lag_ratio=0.25), run_time=1.6)
        self.sync(0.2)

        # ---------------- trap：速度是任意的
        self.seg("trap")
        v_eq = MathTex(r"v(t)", "=", r"\,?\,", font_size=72)
        v_eq[0].set_color(ORANGE)
        v_eq[2].set_color(RED)
        v_eq.move_to([3.6, 0.35, 0])
        cross = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(RED, 10).scale(0.9).move_to(v_eq)
        wiggle = FunctionGraph(lambda x: 0.35 * np.sin(3 * x) * np.cos(1.3 * x) + 0.15 * np.sin(7 * x),
                               x_range=[-2.4, 2.4], color=ORANGE).move_to([3.6, -1.4, 0])
        self.play(FadeOut(VGroup(q_panel, qt, qmark)), Write(v_eq), run_time=1.0)
        wig = neon(wiggle, strength=0.7)
        self.play(Create(wig), run_time=1.6)
        self.wait_until(self.phrase_at(0, "陷阱"))
        self.play(Create(cross), run_time=0.5)
        self.play(Wiggle(VGroup(v_eq, cross)), run_time=0.9)
        self.sync(0.1)

        # ---------------- key：把两天叠成一天
        self.seg("key")
        k1 = zh("把两天", 64, weight=BOLD)
        k2 = zh("叠成一天", 64, YELLOW, weight=BOLD)
        key_txt = VGroup(k1, k2).arrange(RIGHT, buff=0.25).move_to([3.4, 0.4, 0]).scale(0.8)
        key_g = glow_text(key_txt, color=YELLOW, strength=0.8)
        self.play(FadeOut(VGroup(v_eq, cross, wig)), run_time=0.4)
        self.play(FadeIn(key_g, scale=1.3), run_time=0.8)
        self.play(Indicate(k2, color=YELLOW, scale_factor=1.12), run_time=0.9)
        self.sync(0.1)

        # ---------------- twomonks：同一天两位僧人
        self.seg("twomonks")
        self.play(FadeOut(key_g, shift=UP * 0.4), run_time=0.6)
        both = zh("同一天", 30, YELLOW, weight=BOLD).move_to(day_lab)
        clock.clear_updaters()
        sun.clear_updaters()
        ghost_t.set_value(0)
        clock.add_updater(lambda m: m.set_hours(6 + 12 * ghost_t.get_value()))
        sun.add_updater(lambda m: m.move_to(sun_pos(ghost_t.get_value())))
        legend = VGroup(
            VGroup(glow_dot(ORIGIN, ORANGE, 0.08, 2), zh("上山的僧人", 26, ORANGE)).arrange(RIGHT, buff=0.2),
            VGroup(glow_dot(ORIGIN, CYAN, 0.08, 2), zh("下山的僧人", 26, CYAN)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([4.6, 0.6, 0])
        self.play(Transform(day_lab, both), clock_panel.animate.set_stroke(YELLOW),
                  FadeIn(g_up, scale=2), FadeIn(g_dn, scale=2), FadeIn(legend, shift=LEFT * 0.3),
                  run_time=1.0)
        self.wait_until(self.sent_at(1))
        self.play(ghost_t.animate.set_value(TAU_MEET), run_time=self.until(self.sent_at(2) - 0.3),
                  rate_func=linear)
        meet = path.point_from_proportion(float(P_UP(TAU_MEET)))
        meet_lab = zh("相遇！", 34, YELLOW, weight=BOLD).next_to(meet, RIGHT, buff=0.35)
        self.play(burst(meet, YELLOW, r1=1.0), ring_pulse(meet, YELLOW, 0.9),
                  FadeIn(meet_lab, scale=1.5), run_time=0.9)
        self.sync(0.3)

        # ---------------- graph1：坐标图
        self.seg("graph1")
        g_up.clear_updaters()
        g_dn.clear_updaters()
        clock.clear_updaters()
        sun.clear_updaters()
        scene_old = VGroup(back, mountain, ridge, path_dash, temple, foot, foot_lab, top_lab, sun,
                           g_up, g_dn, meet_lab, legend, clock_grp, day_lab)
        self.play(FadeOut(scene_old, shift=DOWN * 0.3), run_time=1.0)
        ax = Axes(x_range=[6, 18, 2], y_range=[0, 1, 0.5], x_length=9.5, y_length=4.8,
                  axis_config={"color": GREY_, "stroke_width": 2.5, "include_tip": True,
                               "tip_length": 0.2},
                  ).move_to([0, 0.15, 0])
        xl = VGroup(*[Text(f"{h}:00", font="JetBrains Mono", font_size=20, color=GREY_)
                      .next_to(ax.c2p(h, 0), DOWN, buff=0.18) for h in [6, 10, 14, 18]])
        yl = VGroup(zh("山脚", 22, GREY_).next_to(ax.c2p(6, 0), LEFT, buff=0.2),
                    zh("山顶", 22, YELLOW).next_to(ax.c2p(6, 1), LEFT, buff=0.2))
        top_line = DashedLine(ax.c2p(6, 1), ax.c2p(18, 1), color=DIM, stroke_width=2)
        x_title = zh("时间", 24, WHITE_).next_to(ax.x_axis.get_end(), RIGHT, buff=0.2)
        y_title = zh("位置", 24, WHITE_).next_to(ax.y_axis.get_end(), LEFT, buff=0.2)
        self.play(Create(ax), run_time=1.4)
        self.wait_until(self.phrase_at(0, "横轴"))
        self.play(FadeIn(xl, lag_ratio=0.2), FadeIn(x_title), run_time=1.0)
        self.wait_until(self.phrase_at(0, "纵轴"))
        self.play(FadeIn(yl, lag_ratio=0.3), FadeIn(y_title), Create(top_line), run_time=1.0)
        self.sync(0.1)

        # ---------------- graph2：两条曲线
        self.seg("graph2")
        c_up = ax.plot(lambda h: float(P_UP((h - 6) / 12)), x_range=[6, 18, 0.05], color=ORANGE,
                       stroke_width=5)
        c_dn = ax.plot(lambda h: float(P_DOWN((h - 6) / 12)), x_range=[6, 18, 0.05], color=CYAN,
                       stroke_width=5)
        cu, cd = neon(c_up, strength=0.9), neon(c_dn, strength=0.9)
        lab_up = zh("上山", 26, ORANGE, weight=BOLD).next_to(ax.c2p(18, 1), RIGHT, buff=0.2)
        lab_dn = zh("下山", 26, CYAN, weight=BOLD).next_to(ax.c2p(18, 0), RIGHT, buff=0.2).shift(UP * 0.3)
        d_up = glow_dot(ax.c2p(6, 0), ORANGE, 0.08, 3)
        d_dn = glow_dot(ax.c2p(6, 1), CYAN, 0.08, 3)
        self.play(FadeIn(d_up, scale=2), run_time=0.4)
        t_mid = self.phrase_at(0, "下山的轨迹")
        self.play(Create(cu), MoveAlongPath(d_up, c_up), run_time=self.until(t_mid - 0.2),
                  rate_func=linear)
        self.play(FadeIn(lab_up), FadeIn(d_dn, scale=2), run_time=0.4)
        self.play(Create(cd), MoveAlongPath(d_dn, c_dn), run_time=self.until(self.sent_at(1)),
                  rate_func=linear)
        self.play(FadeIn(lab_dn), run_time=0.4)
        h_star = 6 + 12 * TAU_MEET
        X = ax.c2p(h_star, float(P_UP(TAU_MEET)))
        self.wait_until(self.phrase_at(1, "必然相交"))
        vline = DashedLine(X, ax.c2p(h_star, 0), color=YELLOW, stroke_width=3)
        t_lab = MathTex("t^*", font_size=40, color=YELLOW).next_to(ax.c2p(h_star, 0), DOWN, buff=0.55)
        star = glow_dot(X, YELLOW, 0.1, 5)
        self.play(burst(X, YELLOW, r1=0.9), FadeIn(star, scale=3), run_time=0.9)
        self.play(Create(vline), FadeIn(t_lab, shift=UP * 0.2), run_time=0.8)
        self.sync(0.2)

        # ---------------- ivt：介值定理
        self.seg("ivt")
        graph_all = VGroup(ax, xl, yl, top_line, x_title, y_title, cu, cd, lab_up, lab_dn, d_up, d_dn,
                           vline, t_lab, star)
        self.play(graph_all.animate.scale(0.56).to_edge(LEFT, buff=0.4).shift(UP * 0.2), run_time=1.2)
        f_def = VGroup(MathTex("f(t)", "=", font_size=46),
                       zh("上山位置", 30, ORANGE), MathTex("-", font_size=46), zh("下山位置", 30, CYAN)
                       ).arrange(RIGHT, buff=0.18)
        f_def.move_to([3.55, 2.45, 0])
        ax2 = Axes(x_range=[6, 18, 2], y_range=[-1, 1, 1], x_length=5.6, y_length=2.8,
                   axis_config={"color": GREY_, "stroke_width": 2, "include_tip": False}).move_to([3.7, 0.15, 0])
        f_curve = ax2.plot(lambda h: float(P_UP((h - 6) / 12) - P_DOWN((h - 6) / 12)),
                           x_range=[6, 18, 0.05], color=MAGENTA, stroke_width=5)
        fc = neon(f_curve, strength=0.9)
        zero_lab = MathTex("0", font_size=30, color=GREY_).next_to(ax2.c2p(6, 0), LEFT, buff=0.15)
        f_lab = MathTex("f(t)", font_size=34, color=MAGENTA).next_to(ax2.c2p(18, 1), RIGHT, buff=0.1)
        self.play(Write(f_def), run_time=1.4)
        self.play(Create(ax2), FadeIn(zero_lab), run_time=0.8)
        self.play(Create(fc), FadeIn(f_lab), run_time=1.6)
        self.wait_until(self.sent_at(1))
        p0 = glow_dot(ax2.c2p(6, -1), RED, 0.09, 3)
        neg = MathTex("f(6{:}00) < 0", font_size=34, color=RED).next_to(ax2.c2p(6, -1), DOWN, buff=0.2).shift(RIGHT * 0.7)
        self.play(FadeIn(p0, scale=2), FadeIn(neg), run_time=0.7)
        self.wait_until(self.phrase_at(1, "傍晚六点"))
        p1 = glow_dot(ax2.c2p(18, 1), GREEN, 0.09, 3)
        pos = MathTex("f(18{:}00) > 0", font_size=34, color=GREEN).next_to(ax2.c2p(18, 1), UP, buff=0.2).shift(LEFT * 0.9)
        self.play(FadeIn(p1, scale=2), FadeIn(pos), run_time=0.7)
        self.wait_until(self.phrase_at(1, "介值定理"))
        Z = ax2.c2p(h_star, 0)
        zstar = glow_dot(Z, YELLOW, 0.1, 5)
        ivt = MathTex(r"\Rightarrow\ \exists\, t^*,\ f(t^*) = 0", font_size=44, color=YELLOW)
        ivt.move_to([3.7, -2.55, 0])
        self.play(burst(Z, YELLOW, r1=0.7), FadeIn(zstar, scale=3), run_time=0.8)
        self.play(Write(ivt), run_time=1.2)
        self.sync(0.3)

        # ---------------- moral
        self.seg("moral")
        self.play(FadeOut(VGroup(graph_all, f_def, ax2, fc, zero_lab, f_lab, p0, neg, p1, pos, zstar, ivt)),
                  run_time=0.8)
        E = MathTex(r"\exists", font_size=260, color=CYAN)
        Eg = glow_text(E, color=CYAN, strength=1.0)
        m1 = zh("知道它一定存在", 54, weight=BOLD)
        m2 = zh("却不必把它找出来", 54, weight=BOLD)
        m2.set_color_by_gradient(CYAN, MAGENTA)
        right = VGroup(m1, m2).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        VGroup(Eg, right).arrange(RIGHT, buff=0.9).move_to(UP * 0.3)
        self.play(FadeIn(Eg, scale=0.6), run_time=1.0)
        self.play(FadeIn(m1, shift=RIGHT * 0.4), run_time=0.8)
        self.wait_until(self.sent_at(1))
        self.play(FadeIn(m2, shift=RIGHT * 0.4), run_time=0.8)
        tag = zh("—— 拓扑学的典型思维", 30, GREY_).next_to(right, DOWN, buff=0.5, aligned_edge=RIGHT)
        self.wait_until(self.phrase_at(1, "拓扑学"))
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.8)
        self.sync(0.6)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
