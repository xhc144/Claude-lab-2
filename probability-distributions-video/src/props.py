# -*- coding: utf-8 -*-
"""各集共用的道具：硬币、骰子、转盘、篮球、路线图。"""
from common import *  # noqa: F401,F403


def coin(face="正", r=0.42, color=GOLD):
    """一枚硬币：金色圆片 + 内圈 + 字。"""
    disk = Circle(radius=r, fill_color=tint(color, 0.85), fill_opacity=1, stroke_color=color, stroke_width=3)
    ring = Circle(radius=r * 0.78, stroke_color=interpolate_color(ManimColor(color), ManimColor(WHITE), 0.35),
                  stroke_width=2)
    t = T(face, int(r * 60), INK, bold=True)
    g = VGroup(disk, ring, t)
    g.face, g.r = face, r
    return g


def flip(c, new_face, times=3, run_time=1.2, shift=ORIGIN, height=1.2):
    """把硬币抛起来翻几圈（横向压扁再展开），落下时换成 new_face。"""
    start = c.get_center()
    old, r = c.face, c.r

    def upd(m, a):
        sx = abs(math.cos(a * times * PI)) + 0.03
        face = new_face if a > 1 - 0.5 / times else old
        m.become(coin(face, r=r).stretch(sx, 0))
        m.move_to(start + shift * a + UP * height * math.sin(PI * a))
        m.face, m.r = face, r
    return UpdateFromAlphaFunc(c, upd, run_time=run_time, rate_func=linear)


def die(n, s=0.5, color=INK):
    """骰子的一面，n 个点。"""
    sq = RoundedRectangle(corner_radius=s * 0.18, width=s, height=s, fill_color=WHITE, fill_opacity=1,
                          stroke_color=color, stroke_width=2)
    pos = {1: [(0, 0)], 2: [(-1, 1), (1, -1)], 3: [(-1, 1), (0, 0), (1, -1)], 4: [(-1, 1), (1, 1), (-1, -1), (1, -1)],
           5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)], 6: [(-1, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)]}[n]
    dots = VGroup(*[Dot([x * s * 0.27, y * s * 0.27, 0], radius=s * 0.075, color=color) for x, y in pos])
    return VGroup(sq, dots)


def spinner(r=1.6, color=INDIGO):
    """0 到 1 的转盘：圆盘、刻度、数字和指针（指针是最后一个子对象）。"""
    disk = Circle(radius=r, fill_color=tint(color, 0.08), fill_opacity=1, stroke_color=color, stroke_width=3)
    ticks = VGroup()
    for i in range(20):
        ang = PI / 2 - TAU * i / 20
        d = np.array([math.cos(ang), math.sin(ang), 0])
        ln = 0.16 if i % 5 == 0 else 0.08
        ticks.add(Line(d * r, d * (r - ln), color=color, stroke_width=2))
    labels = VGroup()
    for v in (0, 0.25, 0.5, 0.75):
        ang = PI / 2 - TAU * v
        d = np.array([math.cos(ang), math.sin(ang), 0])
        labels.add(M(f"{v:g}", 22, MUTED).move_to(d * (r + 0.3)))
    hub = Dot(radius=0.07, color=INK)
    needle = Line(ORIGIN, UP * (r - 0.25), color=BRICK, stroke_width=5)
    needle.add_tip(tip_length=0.18, tip_width=0.14)
    g = VGroup(disk, ticks, labels, needle, hub)
    return g


def spin_to(sp, value, turns=3, run_time=2.4):
    """转盘指针转 turns 圈后停在 value（0~1，顺时针从 12 点钟方向量起）。"""
    needle = sp[3]
    center = sp[0].get_center()
    total = -(turns + value) * TAU
    state = {"prev": 0.0}

    def upd(m, a):
        ang = total * a
        m.rotate(ang - state["prev"], about_point=center)
        state["prev"] = ang
    return UpdateFromAlphaFunc(needle, upd, run_time=run_time, rate_func=rate_functions.ease_out_cubic)


def station(name, color, r=0.17):
    dot = Circle(radius=r, fill_color=BG, fill_opacity=1, stroke_color=color, stroke_width=4)
    lab = T(name, 20, INK, bold=True)
    return VGroup(dot, lab)


ROUTE = [("伯努利", TEAL), ("二项", TEAL), ("几何", TEAL), ("泊松", TEAL), ("指数", BRICK), ("伽马", BRICK),
         ("正态", BRICK), ("卡方", INDIGO), ("t", INDIGO), ("F", INDIGO), ("多元正态", INDIGO)]


def route_map():
    """系列路线图：像地铁线一样的两行折线，返回 (线, 站点列表)。"""
    top = [np.array([-5.6 + i * 2.24, 0.9, 0]) for i in range(6)]
    bot = [np.array([5.6 - 0.6 - i * 2.4, -1.5, 0]) for i in range(5)]
    pts = top + bot
    path = VMobject(stroke_color=GREY, stroke_width=7)
    path.set_points_as_corners([top[0]] + top[1:] + [np.array([5.6, -1.5, 0])] + bot)
    stations = []
    for (name, color), p in zip(ROUTE, pts):
        s = station(name, color).move_to(p)
        s[1].next_to(s[0], UP if p[1] > 0 else DOWN, buff=0.18)
        stations.append(s)
    return path, stations
