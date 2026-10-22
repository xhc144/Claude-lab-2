"""分镜与表演：每一场一个函数 draw(c, t, S)，t 是场内时间，S 是这一场的时间轴（查拍的起止、嘴型、表情）。"""
from __future__ import annotations

import math
import random

import skia

import overlays as ov
import sets
from chars import Pose, blink_value, draw_critter, draw_parrot, draw_tiny, emo_pose
from gfx import (C, H, W, clamp, draw_shape, draw_text, ease_in, ease_in_out, ease_out, ease_out_back, fill, keyframes,
                 layer_paint, lerp, lin, noise1, oval, poly, rad, rrect, smooth, spline, stroke, wave)
from humans import HPose, draw_human, walk_pose
from sets import DOOR_X, FLOOR_Y, GROOM, ROOM

KIND = {"cheems": "cheems", "cat": "cat", "husky": "husky", "corgi": "corgi", "zhuang": "dazhuang",
        "golden": "golden", "robocat": "robocat"}
SEED = {"cheems": 0.3, "cat": 1.7, "husky": 2.9, "corgi": 4.1, "zhuang": 5.3, "golden": 6.7, "robocat": 8.0,
        "devil": 9.1, "angel": 9.9}
LINE = "#2A211C"
PLUS = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen


# ================================================================ 工具
def cam(c, x, y, z=1.0, rot=0.0):
    c.translate(W / 2, H / 2)
    if rot:
        c.rotate(rot)
    c.scale(z, z)
    c.translate(-x, -y)


def camf(x, y, z=1.0, rot=0.0):
    return lambda c: cam(c, x, y, z, rot)


def pz(S, ch, t, default="normal", **kw):
    """按时间轴取角色的表情、眨眼、嘴型、尾巴。"""
    e = S.emo(ch, t, default) if S is not None else default
    p = emo_pose(e)
    p.t = t + SEED[ch] * 3
    if p.eye not in ("closed", "happy", "tight"):
        p.blink = blink_value(t, SEED[ch])
    p.talk = S.talk(ch, t) if S is not None else 0.0
    happy = e in ("happy", "joy", "sparkle", "proud")
    p.tail = math.sin(t * (10 if happy else 2.2) + SEED[ch]) * (1.0 if happy else 0.35)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def dog(c, ch, x, y, u, p):
    draw_critter(c, KIND[ch], x, y, u, p)


def lightmap(c, cf, ambient, lights):
    """乘法光照：先铺环境色，再叠加各个光源，最后整体乘到画面上。"""
    p = skia.Paint()
    p.setBlendMode(skia.BlendMode.kMultiply)
    c.saveLayer(None, p)
    c.drawColor(C(ambient))
    c.save()
    cf(c)
    for L in lights:
        kind = L[0]
        if kind == "pt":
            _, x, y, r, col, a = L
            q = fill(shader=rad((x, y), r, [(col, a), (col, a * 0.45), (col, 0.0)], [0, 0.45, 1]), blend=PLUS)
            c.drawCircle(x, y, r, q)
        elif kind == "cone":
            _, x, y, ang, spread, length, col, a = L
            path = skia.Path()
            path.moveTo(x, y)
            for k in range(17):
                aa = math.radians(ang - spread + 2 * spread * k / 16)
                path.lineTo(x + math.cos(aa) * length, y + math.sin(aa) * length)
            path.close()
            q = fill(shader=rad((x, y), length, [(col, a), (col, a * 0.55), (col, 0.0)], [0, 0.55, 1]), blend=PLUS,
                     blur=length * 0.03)
            c.drawPath(path, q)
        elif kind == "rect":
            _, x, y, w, h, col, a, bl = L
            c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fill(col, a, blur=bl, blend=PLUS))
        elif kind == "beam":
            _, pts, col, a, bl = L
            c.drawPath(poly(pts), fill(col, a, blur=bl, blend=PLUS))
    c.restore()
    c.restore()


def glow(c, cf, items):
    c.save()
    cf(c)
    for x, y, r, col, a in items:
        c.drawCircle(x, y, r, fill(shader=rad((x, y), r, [(col, a), (col, 0.0)]), blend=SCREEN))
    c.restore()


def walkx(t, keys):
    """按关键帧插值 x，并返回 (x, 是否在走, 朝向)。"""
    x = keyframes(t, keys, ease=smooth)
    x2 = keyframes(t + 0.05, keys, ease=smooth)
    moving = abs(x2 - x) > 0.4
    return x, moving, (1 if x2 > x else -1) if moving else 0


def shake_xy(t, amp, seed=0):
    return noise1(t * 9, seed) * amp, noise1(t * 9, seed + 7) * amp


def dust(c, x, y, k, n=6, size=30, seed=0):
    if k <= 0 or k >= 1:
        return
    rnd = random.Random(seed)
    for i in range(n):
        ang = rnd.uniform(math.pi * 1.05, math.pi * 1.95)
        d = ease_out(k) * rnd.uniform(60, 140)
        r = size * (0.5 + k) * rnd.uniform(0.6, 1.2)
        c.drawCircle(x + math.cos(ang) * d, y + math.sin(ang) * d * 0.5, r, fill("#EDE3D2", 0.7 * (1 - k)))


def sparkles(c, x, y, k, t, n=6, r=80, col="#FFF2A8"):
    if k <= 0:
        return
    for i in range(n):
        ang = i / n * 2 * math.pi + t * 1.5
        d = r * (0.6 + 0.4 * math.sin(t * 3 + i))
        s = 10 + 6 * math.sin(t * 5 + i * 2)
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d
        p = skia.Path()
        p.moveTo(px, py - s)
        p.quadTo(px, py, px + s, py)
        p.quadTo(px, py, px, py + s)
        p.quadTo(px, py, px - s, py)
        p.quadTo(px, py, px, py - s)
        c.drawPath(p, fill(col, clamp(k)))


def hearts(c, x, y, k, t, n=4):
    for i in range(n):
        ph = (t * 0.6 + i / n) % 1.0
        draw_text(c, "♥", x + math.sin(ph * 6 + i) * 40 + (i - n / 2) * 30, y - ph * 160, size=40 + 10 * i % 20,
                  name="sans", color="#FF6B8A", a=clamp(k) * (1 - ph))


# ================================================================ 房间公共部分
def room_flap(c, swing):
    fx, fy, fw, fh = ROOM["flap"]
    sq = 1.0 - min(abs(swing), 1.0) * 0.85
    c.save()
    c.translate(0, fy)
    c.scale(1, max(sq, 0.12) * (1 if swing >= 0 else -1))
    c.drawPath(rrect(fx, 0, fw, fh, 12), fill("#3B2A22"))
    c.drawPath(rrect(fx + 10, 10, fw - 20, fh - 20, 8), stroke("#2A1E18", 3))
    c.drawPath(rrect(fx, 0, fw, fh, 12), stroke("#1E140E", 4))
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(fx, fy - 6, fw, 8), fill("#888"))


def window_view(c, inside=None, lamp=0.6):
    wx, wy, ww, wh = ROOM["win"]
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), fill(shader=lin((0, wy), (0, wy + wh), ["#3A3F5E", "#1A1E30"])))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy + wh * 0.55, ww, wh * 0.45), fill("#2A2026"))
    c.drawLine(wx, wy + wh * 0.55, wx + ww, wy + wh * 0.55, stroke("#151018", 4))
    c.drawCircle(wx + ww * 0.7, wy + 4, 60, fill("#FFE2A0", 0.25 * lamp, blur=16))
    if inside:
        inside(c)
    c.restore()
    c.drawPath(poly([(wx + 14, wy + 8), (wx + 50, wy + 8), (wx + 24, wy + wh - 8), (wx + 8, wy + wh - 8)]),
               fill("#FFFFFF", 0.07))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), stroke("#4A2E1A", 6))


def room_base(c, t, flap=0.0, inside=None, bowl_full=False, vent_open=0.0):
    sets.room(c, t, bowl_full=bowl_full, vent_open=vent_open)
    room_flap(c, flap)
    window_view(c, inside)


def night_room_light(c, cf, t, extra=(), lights_on=0.0, window=0.35):
    wx, wy, ww, wh = ROOM["win"]
    amb = tuple(int(lerp(a, b, lights_on)) for a, b in zip((64, 72, 124), (255, 250, 240)))
    L = [("pt", 595, 595, 330, "#FFD890", 0.55), ("rect", wx - 10, wy - 10, ww + 20, wh + 20, "#9AA8E0", window, 30),
         ("beam", [(wx, wy + wh), (wx + ww, wy + wh), (wx + ww + 220, 1080), (wx - 120, 1080)], "#8090C8",
          window * 0.35, 40)]
    lightmap(c, cf, amb, L + list(extra))
    glow(c, cf, [(595, 595, 90, "#FFE9A0", 0.5)])


def blanket(c, x, y, u, peek, t, col="#E9EEF8"):
    """盖在 Cheems 身上的毯子。peek=0 只露眼睛，1 时头完全露出来。"""
    c.save()
    c.translate(x, y)
    c.scale(u, u)
    top = lerp(-2.25, -1.55, clamp(peek))
    p = spline([(-1.45, 0.1), (-1.3, top + 0.5), (-0.6, top - 0.05), (0.6, top - 0.05), (1.3, top + 0.5), (1.45, 0.1)],
               tension=0.9)
    p.close()
    draw_shape(c, p, col, "#7A8AA8", 0.05, "#C9D3E6", (-0.05, -0.08))
    for i in range(4):
        yy = top + 0.4 + i * 0.35
        c.drawPath(spline([(-1.1, yy), (0.0, yy + 0.1), (1.1, yy)], closed=False), stroke("#B8C4DC", 0.04, 0.8))
    for k in range(5):
        c.drawCircle(-0.9 + k * 0.45, top + 0.9, 0.06, fill("#F5B8C4", 0.8))
    c.restore()


# ================================================================ 冷开场
def s_cold_open(c, t, S):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#05060C"))
    fl = 0.75 + 0.25 * math.sin(t * 13) * math.sin(t * 7.3)
    c.drawCircle(W / 2, H / 2, 900, fill(shader=rad((W / 2, H / 2), 900, [("#2A2238", 0.9 * fl), ("#05060C", 0.0)])))
    k = S.p("r0", t, 0, 1.2)
    if t < S.s("glitch"):
        hi = 6 if S.after("r7", t) else -2
        ov.rules_paper(c, k, t, 7, hi=hi, scale=0.95)
    elif S.within("glitch", t):
        rnd = random.Random(int(t * 30))
        ov.rules_paper(c, 1.0, t, 7, hi=6, scale=0.95, cx=W / 2 + rnd.uniform(-30, 30))
        for i in range(8):
            y = rnd.uniform(0, H)
            c.drawRect(skia.Rect.MakeXYWH(0, y, W, rnd.uniform(4, 40)), fill(rnd.choice(["#FF2A2A", "#2AFFFF", "#FFFFFF"]),
                                                                              0.35))
    else:
        ov.title_card(c, S.p("title", t), t)
    ov.vignette(c, 0.7)


# ================================================================ 旅馆门口
def s_drop_off(c, t, S):
    keys = [(0, (1050, 780, 2.1)), (S.s("n2") - 0.5, (1040, 740, 1.6)), (S.s("n2") + 1.5, (1180, 560, 0.85)),
            (S.e("n2") - 0.3, (1180, 560, 0.85)), (S.s("o1") + 0.6, (1000, 690, 1.45)), (S.s("c1"), (1010, 700, 1.5)),
            (S.e("c2"), (1000, 690, 1.45)), (S.s("leave") + 0.4, (900, 660, 1.15)), (S.s("c3"), (950, 650, 1.2)),
            (S.s("c3") + 0.8, (1050, 780, 1.9))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.exterior(c, "day", t)
    # 主人
    kneel = S.s("o1") - 0.3 <= t < S.s("leave") + 0.5
    ox = 880
    if t >= S.s("leave") + 0.5:
        k = S.p("leave", t, 0.5, None)
        ox = lerp(880, 200, ease_in_out(k))
        if t >= S.s("c3"):
            ox = -400
        hp = walk_pose(t * 1.3, turn=-0.7, l_up=150 + 25 * math.sin(t * 9), l_lo=-30, flip=False)
        hp.face = "smile"
        draw_human(c, "owner", ox, 905, 58, hp)
    elif kneel:
        lift = S.within("o2", t) or S.within("c2", t)
        hp = HPose(kneel=True, pelvis=-2.7, turn=0.4, face="smile", talk=S.talk("owner", t), t=t,
                   r_up=95 if lift and S.within("o2", t) else (60 if S.within("c2", t) else 20),
                   r_lo=-60 if S.within("o2", t) else (10 if S.within("c2", t) else -10),
                   hold="leash" if S.after("o2", t) else None, l_up=10, look=(0.6, 0.3))
        draw_human(c, "owner", ox, 905, 58, hp)
    else:
        draw_human(c, "owner", ox, 905, 58, HPose(face="smile", t=t, hold=None, turn=0.3, l_up=8, r_up=8,
                                                 look=(0.5, 0.4)))
    # Cheems
    p = pz(S, "cheems", t, "hungry")
    if S.within("c2", t):
        p.arm_l = 135
    if t >= S.s("leave"):
        p.look = (-0.8, -0.1)
        p.ear = max(p.ear, 0.6)
    elif t >= S.s("o1"):
        p.look = (-0.6, -0.5)
    dog(c, "cheems", 1050, 905, 62, p)
    if S.within("c2", t):
        sparkles(c, 990, 700, S.p("c2", t, 0.8, 1.6), t, 6, 50)
    c.restore()
    # 想吃的泡泡
    if t < S.e("n1"):
        k = S.p("n1", t, 0.8, 1.6)
        out = 1 - S.pe("n1", t, 0.6)
        sx = W / 2 + 330
        sy = H / 2 - 260

        def content(cc, tt):
            ov.drumstick(cc, -60, -10, 1.2, -20 + 8 * math.sin(tt * 3))
            ov.bone_icon(cc, 110, 30, 0.8, 25 + 6 * math.sin(tt * 2.5))
        ov.thought_bubble(c, sx, sy, 420, 260, k * out, t, content)
    # 飘落的花瓣
    rnd = random.Random(3)
    for i in range(14):
        ph = (t * rnd.uniform(0.05, 0.1) + rnd.random()) % 1.0
        x = (rnd.uniform(0, W) + ph * 300) % W
        y = ph * (H + 100) - 50
        c.save()
        c.translate(x, y)
        c.rotate(ph * 720 + i * 40)
        c.drawPath(oval(0, 0, 10, 6), fill("#FFC1CF", 0.85))
        c.restore()
    ov.vignette(c, 0.3)


# ================================================================ 大堂登记
def s_lobby(c, t, S):
    keys = [(0, (1050, 560, 0.92)), (S.e("n3") - 0.4, (1050, 560, 0.92)), (S.s("k1") + 0.4, (980, 640, 1.25)),
            (S.s("p1"), (980, 640, 1.25)), (S.s("p1") + 0.35, (720, 560, 1.55)), (S.e("p2"), (740, 580, 1.5)),
            (S.s("k2") + 0.5, (1050, 600, 1.3)), (S.e("c6"), (1050, 600, 1.3)), (S.s("k4") + 0.3, (1150, 560, 1.7)),
            (S.e("k5"), (1180, 540, 2.3)), (S.s("photo") + 1.0, (1220, 300, 2.5)), (S.e("photo"), (1220, 290, 2.7))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.lobby(c, "day", t)
    sets.draw_cage(c, 640, 520, front=False)
    pp = Pose(t=t, talk=S.talk("parrot", t), look=(0.5, 0))
    if S.within("p1", t):
        pp.wing = abs(math.sin(t * 14)) * 0.8
        pp.bob = -0.05 * abs(math.sin(t * 7))
    draw_parrot(c, 640, 456, 72, pp)
    sets.draw_cage(c, 640, 520, front=True)
    # 橘猫趴在前台上
    cp = pz(S, "cat", t, "lazy")
    if t >= S.s("k4"):
        cp.look = (-0.4, 0.2)
    dog(c, "cat", 1190, 646, 58, cp)
    # Cheems 走进来
    x, moving, d = walkx(t, [(0, 260), (0.4, 260), (3.4, 760)])
    p = pz(S, "cheems", t)
    if moving:
        p.walk = t * 3.0
        p.turn = 0.5 * d
    if S.within("p1", t) or S.within("c5", t) or S.within("p2", t):
        p.look = (-0.7, -0.6)
        if S.within("p1", t):
            p.mark = "!"
    elif t >= S.s("k1") and t < S.s("photo"):
        p.look = (0.7, -0.6)
    if S.within("c6", t):
        p.mark = "?"
    if t >= S.s("photo"):
        p.look = (0.5, -0.9)
    dog(c, "cheems", x, 905, 68, p)
    c.restore()
    dim = S.p("k4", t, 0, 1.5) * (1 - S.p("photo", t, 1.5, None))
    lightmap(c, cf, (int(255 - 80 * dim), int(250 - 85 * dim), int(240 - 60 * dim)),
             [("pt", 1190, 520, 420, "#FFE6B0", 0.4 * dim)])
    ov.vignette(c, 0.3 + 0.35 * dim)


# ================================================================ 走廊认识邻居
def s_corridor_day(c, t, S):
    xs = [(0, 120), (S.e("n4") - 0.5, 540), (S.s("z1") - 0.1, 540), (S.s("z1") + 2.2, 1290), (S.s("k6"), 1290),
          (S.s("k6") + 2.6, 2150), (S.s("j1"), 2150), (S.s("j1") + 3.0, 3560)]
    x, moving, d = walkx(t, xs)
    cxk = [(tt, v + 260) for tt, v in xs]
    cxk.append((S.s("h1"), 2420))
    cxk.sort()
    cx = keyframes(t, [(0, 450), (S.e("n4") - 0.5, 760), (S.s("z1"), 760), (S.s("z1") + 2.2, 1480),
                       (S.s("k6"), 1480), (S.s("k6") + 2.6, 2400), (S.s("h1") + 0.3, 2450), (S.s("j1"), 2450),
                       (S.s("j1") + 3.0, 3760)], ease=smooth)
    z = 1.38
    cy = 715
    if S.within("h1", t):
        dx, dy = shake_xy(t, 6 * (1 - S.p("h1", t, 0, 0.8)))
        cx += dx
        cy += dy
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.corridor(c, t, night=False)
    gy = 935
    # 小柯
    dog(c, "corgi", DOOR_X[1] + 60, gy, 52, pz(S, "corgi", t, "weep", look=(-0.6, -0.2)))
    # 大壮
    zp = pz(S, "zhuang", t, "cool")
    if t < S.e("z1"):
        zp.flex = 0.5 + 0.5 * math.sin(t * 6)
    elif S.within("z2", t):
        zp.flex = 1.0
    else:
        zp.flex = 0.6
    zp.look = (-0.5, 0.2)
    dog(c, "zhuang", DOOR_X[2] + 70, gy, 52, zp)
    # 二哈：从 4 号门冲出来
    if t >= S.s("h1"):
        k = S.p("h1", t, 0, 0.6)
        hx = lerp(DOOR_X[4], 2470, ease_out(k))
        hy = gy - math.sin(k * math.pi) * 180
        hp = pz(S, "husky", t, "derp", look=(-0.7, 0))
        hp.bob = -0.15 * abs(math.sin(t * 8)) if t > S.s("h2") and t < S.e("h3") else 0
        hp.tongue = True
        dog(c, "husky", hx, hy, 62, hp)
        dust(c, 2470, gy, S.p("h1", t, 0.55, 1.3), 7, 26, 4)
    # 老金
    gp = pz(S, "golden", t, "normal", look=(-0.6, 0.1))
    gp.tail = math.sin(t * 1.4) * 0.3
    dog(c, "golden", DOOR_X[5] + 30, gy, 64, gp)
    # 大橘跟在后面
    catx = keyframes(t, [(tt, v - 210) for tt, v in xs], ease=smooth)
    ctp = pz(S, "cat", t, "lazy")
    if moving:
        ctp.walk = t * 3.0 + 0.5
        ctp.turn = 0.6
    else:
        ctp.look = (0.5, 0)
    dog(c, "cat", catx, gy + 10, 56, ctp)
    p = pz(S, "cheems", t)
    if moving:
        p.walk = t * 3.0
        p.turn = 0.55 * d
    if t >= S.s("g1") and t < S.s("z1"):
        p.look = (0.8, 0.1)
    if t >= S.s("z1") and t < S.s("k6"):
        p.look = (0.8, -0.4)
    if t >= S.s("h1") and t < S.s("j1"):
        p.look = (0.8, -0.1)
        if S.within("h1", t):
            p.mark = "!"
    if S.within("c12", t):
        p.mark = "?"
    dog(c, "cheems", x, gy + 5, 62, p)
    c.restore()
    lightmap(c, cf, (238, 222, 200), [("pt", lx, 200, 520, "#FFE2B0", 0.18) for lx in range(500, 5600, 800)])
    ov.vignette(c, 0.3)


# ================================================================ 22:00 守则
def s_rules(c, t, S):
    n5 = S.s("n5")
    if t < n5:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000"))
        return
    lights_on = 1 - S.p("n5", t, 0.1, 0.6)
    hide_k = S.p("c14", t, 2.0, 3.0, ease_in_out)
    # 镜头
    reading = S.s("r_t") <= t < S.s("c13")
    keys = [(n5, (950, 640, 1.25)), (n5 + 4, (860, 700, 1.6)), (S.s("r_t"), (860, 700, 1.7)),
            (S.e("r7b"), (860, 690, 1.6)), (S.s("c13") + 0.3, (800, 680, 1.55)), (S.s("c14") + 1.5, (650, 690, 1.35)),
            (S.e("hide"), (520, 700, 1.6))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    found = S.p("n5", t, 5.2, 6.5)
    room_base(c, t, bowl_full=False)
    # Cheems：舔碗 → 发现纸 → 害怕 → 钻进毯子
    bx = lerp(800, 520, hide_k)
    p = pz(S, "cheems", t, "hungry")
    if t < S.s("r_t"):
        lick = S.p("n5", t, 2.0, 5.0)
        p.tilt = 14 * math.sin(lick * math.pi)
        p.look = (0.3, 0.9) if lick > 0 and lick < 1 else (0, 0)
        if found > 0:
            p.mark = "!"
    if reading:
        p.look = (0.0, 0.5)
    if hide_k > 0:
        p.walk = t * 3.5 if hide_k < 1 else None
        p.turn = -0.5 if hide_k < 1 else 0
    if hide_k < 1:
        dog(c, "cheems", bx, 960, 92, p)
    # 纸从碗底下滑出来
    if found > 0 and not reading and t < S.s("c13"):
        c.save()
        c.translate(lerp(900, 780, found), lerp(875, 820, found))
        c.rotate(-20 + 25 * found)
        c.drawPath(rrect(-50, -36, 100, 72, 4), fill("#F7EFDC"))
        c.drawPath(rrect(-50, -36, 100, 72, 4), stroke("#B8A27A", 3))
        c.restore()
    if hide_k >= 1:
        p2 = pz(S, "cheems", t, "scared")
        dog(c, "cheems", 470, 900, 80, p2)
        blanket(c, 470, 905, 80, 0.0, t)
    elif hide_k > 0.6:
        blanket(c, 470, 905, 80, 1 - (hide_k - 0.6) / 0.4, t)
    c.restore()
    night_room_light(c, cf, t, lights_on=lights_on)
    if reading or S.within("r_t", t):
        k = min(S.p("r_t", t, 0, 0.7), 1 - S.pe("r7b", t, 0.6))
        shown, hi = 0, -1
        for i, bid in enumerate(("r1", "r2", "r3", "r4", "r5", "r6", "r7b")):
            if t >= S.s(bid):
                shown = i + 1
                hi = i
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", 0.55 * k))
        ov.rules_paper(c, k, t, shown, hi=hi, scale=1.02)
    ov.vignette(c, 0.6)


def _peek_eyes(c, x, y, u, t):
    """毯子缝里露出的两只眼睛。"""
    b = blink_value(t, 0.3)
    for s in (-1, 1):
        ex = x + s * 0.32 * u + math.sin(t * 0.8) * 4
        ey = y - 1.85 * u
        c.drawPath(oval(ex, ey, 0.13 * u, 0.15 * u * (1 - b)), fill("#FFFFFF"))
        c.drawPath(oval(ex + 0.03 * u, ey, 0.06 * u, 0.07 * u * (1 - b)), fill("#1A120C"))
    c.drawPath(spline([(x - 0.6 * u, y - 1.65 * u), (x, y - 1.6 * u), (x + 0.6 * u, y - 1.65 * u)], closed=False),
               stroke("#7A8AA8", 4))


# ================================================================ 23:00 小柯
def s_corgi_cry(c, t, S):
    vent_shot = S.within("g2", t) or S.within("g3", t) or S.within("g4", t)
    keys = [(0, (560, 640, 1.5)), (S.s("g2"), (560, 640, 1.5)), (S.s("g2") + 1.2, (420, 420, 1.9)),
            (S.e("g2"), (420, 420, 1.9)), (S.s("c15") + 0.6, (520, 650, 1.6)), (S.e("c16"), (520, 650, 1.6)),
            (S.s("g3") + 0.5, (430, 520, 1.7)), (S.s("c17") + 0.3, (560, 700, 2.0)), (S.e("c17"), (600, 720, 2.1)),
            (S.s("g4") + 0.5, (480, 560, 1.6)), (S.e("c18"), (470, 640, 1.8))]
    cx, cy, z = keyframes(t, keys)
    if S.within("c18", t):
        dx, dy = shake_xy(t, 3)
        cx += dx
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    room_base(c, t)
    p = pz(S, "cheems", t, "worried", look=(-0.5, -0.8))
    if S.within("c16", t):
        p.look = (0.3, -0.5)
    if S.within("c18", t):
        p.tremble = 1.4
    peek = 1.0
    dog(c, "cheems", 470, 900, 80, p)
    blanket(c, 470, 905, 80, peek, t)
    if S.within("c17", t):
        # 尾巴变成甜甜圈的小玩笑
        k = S.p("c17", t, 0.2, 0.7)
        c.save()
        c.translate(560, 790)
        c.scale(ease_out_back(k), ease_out_back(k))
        c.drawCircle(0, 0, 46, stroke("#F2A0B8", 34))
        rnd = random.Random(5)
        for i in range(14):
            ang = rnd.uniform(0, 2 * math.pi)
            c.save()
            c.rotate(math.degrees(ang))
            c.drawRect(skia.Rect.MakeXYWH(40, -3, 12, 5), fill(rnd.choice(["#FFFFFF", "#7FD3F7", "#FFE07A"])))
            c.restore()
        c.restore()
        draw_text(c, "甜甜圈？", 650, 720, size=44, name="kuaile", color="#FFB45C", outline="#3A1A08", ow=6, a=k)
    c.restore()
    night_room_light(c, cf, t)
    if S.within("c16", t):
        k = S.p("c16", t, 0.5, 1.2) * (1 - S.pe("c16", t, 0.5))

        def content(cc, tt):
            ang = tt * 200
            cc.save()
            cc.rotate(ang)
            draw_critter(cc, "cheems", 85, 95, 42, Pose(eye="happy", mouth="grin", t=tt, walk=tt * 5, turn=-1))
            cc.restore()
            cc.drawCircle(0, 0, 34, stroke("#F2A0B8", 20))
        ov.thought_bubble(c, W / 2 + 380, H / 2 - 220, 380, 320, k, t, content)
    if vent_shot:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000", 0.0))
    ov.vignette(c, 0.6)


# ================================================================ 00:00 影子
def s_shadow(c, t, S):
    win_shot = S.within("pass", t) or S.within("z3", t) or S.within("z4", t) or S.within("jog", t)
    keys = [(0, (700, 640, 1.2)), (S.s("c19"), (560, 660, 1.7)), (S.e("c19"), (560, 660, 1.75)),
            (S.s("pass") + 0.3, (1330, 450, 3.0)), (S.e("z3"), (1330, 450, 3.1)), (S.s("c20") + 0.3, (520, 650, 1.8)),
            (S.e("c20"), (520, 650, 1.8)), (S.s("z4") + 0.3, (1330, 450, 3.0)), (S.e("jog"), (1330, 450, 3.0)),
            (S.s("n7") + 0.5, (900, 600, 1.15)), (S.e("n7"), (700, 650, 1.6))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    wx, wy, ww, wh = ROOM["win"]

    def inside(cc):
        if S.within("pass", t):
            k = S.p("pass", t, 0, 1.6)
            sx = lerp(wx - 160, wx + ww * 0.5, ease_out(k))
            cc.drawPath(oval(sx, wy + 75, 90, 120), fill("#06070C", 0.92))
            cc.drawPath(oval(sx, wy + 10, 50, 46), fill("#06070C", 0.95))
            if t > S.s("pass") + 1.6:
                cc.drawCircle(sx - 18, wy + 10, 5, fill("#FFF0B0"))
                cc.drawCircle(sx + 18, wy + 10, 5, fill("#FFF0B0"))
        elif S.within("z3", t) or S.within("z4", t):
            zp = pz(S, "zhuang", t, "happy")
            dog(cc, "zhuang", wx + ww / 2, wy + wh / 2 + 200, 56, zp)
        elif S.within("jog", t):
            k = S.p("jog", t)
            zp = pz(S, "zhuang", t, "happy", walk=t * 4, turn=0.8)
            dog(cc, "zhuang", lerp(wx + ww / 2, wx + ww + 120, k), wy + wh / 2 + 200, 56, zp)
    c.save()
    cf(c)
    room_base(c, t, inside=inside)
    p = pz(S, "cheems", t, "scared", look=(0.9, -0.4))
    dog(c, "cheems", 470, 900, 80, p)
    blanket(c, 470, 905, 80, 0.85, t)
    c.restore()
    win_light = 0.35 + (0.3 if S.within("z3", t) or S.within("z4", t) else 0)
    night_room_light(c, cf, t, window=win_light)
    if S.within("n7", t):
        k = S.p("n7", t, 5.5, 7.5)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#300000", 0.25 * k))
    ov.vignette(c, 0.65)


# ================================================================ 01:00 两只橘猫
def s_two_cats(c, t, S):
    wx, wy, ww, wh = ROOM["win"]
    keys = [(0, (900, 600, 1.2)), (S.s("k8") + 0.6, (1050, 520, 1.7)), (S.e("k9"), (1150, 500, 2.0)),
            (S.s("second") + 0.4, (1330, 450, 3.1)), (S.e("second"), (1330, 450, 3.3)),
            (S.s("c22") + 0.15, (560, 660, 2.2)), (S.e("c22"), (560, 660, 2.3)),
            (S.s("open"), (1330, 450, 3.4)), (S.e("k10"), (1330, 450, 3.6)), (S.e("leave"), (1000, 560, 1.4)),
            (S.e("c23"), (700, 640, 1.6))]
    cx, cy, z = keyframes(t, keys)
    if S.within("open", t):
        dx, dy = shake_xy(t, 10 * (1 - S.p("open", t)))
        cx, cy = cx + dx, cy + dy
    cf = camf(cx, cy, z)
    cat_here = S.s("k8") <= t < S.s("close")
    after_open = S.s("open") <= t < S.e("k10") + 0.6
    flash_on = cat_here or after_open

    def inside(cc):
        if cat_here:
            ctp = pz(S, "cat", t, "lazy", look=(-0.3, 0.3))
            if t >= S.s("second"):
                ctp.turn = 0.6
                ctp.look = (0.8, 0)
            dog(cc, "cat", wx + 72, wy + wh + 60, 52, ctp)
            if t >= S.s("second"):
                k = S.p("second", t, 0.6, 1.4)
                rp = Pose(t=t, glow=1.0, alpha=k)
                dog(cc, "robocat", wx + ww - 32, wy + wh - 18, 18, rp)
                cc.drawCircle(wx + ww - 38, wy + wh - 58, 26, fill("#FF2020", 0.35 * k, blur=8))
        elif after_open:
            ctp = pz(S, "cat", t, "creepy", pupil=2.0)
            ctp.mouth = "smile"
            dog(cc, "cat", wx + ww / 2, wy + wh / 2 + 190, 82, ctp)
    c.save()
    cf(c)
    room_base(c, t, inside=inside)
    p = pz(S, "cheems", t, "nervous", look=(0.9, -0.4))
    dog(c, "cheems", 470, 900, 80, p)
    blanket(c, 470, 905, 80, 0.85, t)
    c.restore()
    extra = []
    if flash_on:
        extra = [("cone", wx + ww / 2, wy + wh / 2, 140 + 10 * math.sin(t * 1.3), 22, 1100, "#FFF3D0", 0.75)]
    night_room_light(c, cf, t, extra=extra, window=0.6 if flash_on else 0.3)
    # 闭眼数数：全黑 + 心跳红光 + 数字
    if S.s("close") <= t < S.s("open"):
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000"))
        hb = (t % 0.85)
        pulse = math.exp(-hb * 8) + 0.6 * math.exp(-max(hb - 0.24, 0) * 8) * (hb > 0.24)
        c.drawRect(skia.Rect.MakeWH(W, H), fill(shader=rad((W / 2, H / 2), 1100, [("#000000", 0), ("#5A0000", 0.6 * pulse)])))
        n = 0
        for i, bid in enumerate(("count1", "count2", "count3")):
            if t >= S.s(bid):
                n = i
        if t >= S.s("count1"):
            # 按时间平均分配 1~10
            t0 = S.s("count1")
            t1 = S.ae("count3")
            idx = min(int((t - t0) / max(t1 - t0, 0.1) * 10) + 1, 10)
            k = ((t - t0) / max(t1 - t0, 0.1) * 10) % 1.0
            draw_text(c, f"{idx}", W / 2, H / 2 + 80, size=260 + 60 * ease_out(1 - k), name="huangyou",
                      color="#E8E2D2", a=0.85, glow=("#C8302A", 30, 0.5))
        draw_text(c, "（闭着眼睛）", W / 2, H / 2 - 220, size=40, name="kuaile", color="#8A8070", a=0.7)
    ov.vignette(c, 0.65)


# ================================================================ 02:00 肉骨头
def s_bone(c, t, S):
    keys = [(0, (900, 640, 1.2)), (S.s("k11") + 0.5, (1100, 720, 1.5)), (S.e("c24"), (980, 720, 1.6)),
            (S.s("aroma") + 0.5, (1050, 700, 1.4)), (S.s("c25"), (950, 700, 1.7)), (S.s("d1"), (950, 640, 1.6)),
            (S.e("a1"), (950, 640, 1.6)), (S.s("growl"), (950, 700, 1.8)), (S.e("c26"), (950, 700, 1.9)),
            (S.s("z5") + 0.3, (1250, 640, 1.3)), (S.e("silence"), (1250, 640, 1.35)), (S.s("c27"), (1000, 680, 1.7)),
            (S.e("drag"), (1250, 560, 1.6))]
    cx, cy, z = keyframes(t, keys)
    if S.within("z5", t):
        dx, dy = shake_xy(t, 4)
        cx += dx
    cf = camf(cx, cy, z)
    wx, wy, ww, wh = ROOM["win"]
    slide = S.p("k11", t, 1.0, 1.8, ease_out)
    flap = 0.0
    if S.within("k11", t):
        flap = math.sin(S.p("k11", t, 0.9, 2.2) * math.pi * 3) * (1 - S.p("k11", t, 0.9, 2.2))

    def inside(cc):
        if S.within("drag", t):
            k = S.p("drag", t, 0.3, 2.4)
            sx = lerp(wx - 120, wx + ww + 120, k)
            cc.drawPath(spline([(sx - 60, wy + wh - 10), (sx - 40, wy + wh - 70), (sx + 30, wy + wh - 80),
                                (sx + 60, wy + wh - 10)]), fill("#0A0A0E", 0.9))
    c.save()
    cf(c)
    room_base(c, t, flap=flap, inside=inside)
    # 夜宵碗
    if slide > 0:
        sets.bowl(c, lerp(1330, 1080, slide), 900, full=t < S.s("aroma"), s=0.8)
    # Cheems 走到碗边
    x = keyframes(t, [(S.s("k11") + 1.5, 600), (S.s("k11") + 2.6, 900)], ease=smooth)
    p = pz(S, "cheems", t, "normal")
    if S.s("k11") + 1.5 < t < S.s("k11") + 2.6:
        p.walk = t * 3.5
        p.turn = 0.5
    if S.within("c24", t):
        p.tilt = 10 * math.sin(t * 6)
        p.look = (0.4, 0.8)
    if S.within("aroma", t):
        p.look = (0.9, 0.3)
        p.mark = "!" if S.p("aroma", t) > 0.5 else None
    if S.within("growl", t) or S.within("c26", t) or S.within("pillow", t):
        p.tremble = 0.6
    if t >= S.s("z5"):
        p.look = (0.9, -0.2)
    dog(c, "cheems", x, 960, 88, p)
    # 香味
    if S.s("aroma") <= t < S.s("growl") + 1.0:
        k = S.p("aroma", t, 0, 1.5)
        fade = 1 - S.p("growl", t, 0, 1.0)
        nose = (x + 20, 960 - 2.15 * 88)
        for i in range(3):
            pts = []
            for j in range(13):
                f = j / 12 * k
                bx = lerp(1330, nose[0], f)
                by = lerp(840 - i * 30, nose[1], f) - math.sin(f * math.pi) * 90
                off = math.sin(t * 2.5 + j * 0.9 + i * 2) * 22 * (1 - f * 0.6)
                pts.append((bx, by + off))
            c.drawPath(spline(pts, closed=False), stroke("#FFC870", 16, 0.28 * fade * k, blur=5))
            c.drawPath(spline(pts, closed=False), stroke("#FFE3A0", 5, 0.75 * fade * k))
        sparkles(c, nose[0] + 40, nose[1] - 30, k * fade, t, 5, 60, "#FFE3A0")
    c.restore()
    night_room_light(c, cf, t)
    # 小恶魔 / 小天使
    if S.s("d1") <= t < S.e("a1") + 0.4:
        kd = S.p("d1", t, 0, 0.4, ease_out_back)
        ka = S.p("a1", t, 0, 0.4, ease_out_back)
        out = 1 - S.pe("a1", t, 0.2) if t < S.e("a1") else 0
        out = 1 if t < S.e("a1") - 0.2 else out
        dp = Pose(eye="squint", brow=-0.8, mouth="grin", t=t, talk=S.talk("devil", t), bob=0.05 * math.sin(t * 4))
        ap = Pose(eye="happy", mouth="smile", t=t, talk=S.talk("angel", t), bob=0.05 * math.sin(t * 4 + 1))
        if kd > 0:
            draw_tiny(c, 560, 640, 70 * kd * out, dp, devil=True)
        if ka > 0:
            draw_tiny(c, 1220, 640, 70 * ka * out, ap, devil=False)
    if S.within("growl", t):
        ov.onomatopoeia(c, "咕噜噜~", W / 2 + 140, H / 2 + 200, 110, "#FFB45C", S.p("growl", t), t)
    if S.within("z5", t):
        k = S.p("z5", t, 0.9, None)
        ov.onomatopoeia(c, "嘎嘣！", W - 360, H / 2 - 120, 120, "#FFFFFF", k, t, rot=10)
    if S.within("silence", t):
        ov.onomatopoeia(c, "嘎嘣…", W - 380, H / 2 - 60, 90, "#DDDDDD", S.p("silence", t, 0, 1.4), t, rot=6)
        ov.onomatopoeia(c, "咚。", W - 330, H / 2 + 80, 130, "#AAAAAA", S.p("silence", t, 1.6, None), t, rot=-4)
    ov.vignette(c, 0.6)


# ================================================================ 03:00 叫名字
def s_voices(c, t, S):
    wx, wy, ww, wh = ROOM["win"]
    sit_flap = t >= S.s("hm2")
    keys = [(0, (1100, 520, 1.6)), (S.e("wings"), (1250, 480, 2.2)), (S.s("m1") + 1, (900, 560, 1.3)),
            (S.s("g5"), (420, 420, 1.8)), (S.s("c28"), (520, 640, 1.8)), (S.e("gone"), (520, 640, 1.6)),
            (S.e("c29"), (700, 620, 1.3)), (S.s("hm1") + 1.0, (1330, 520, 2.4)), (S.s("c30"), (560, 680, 2.2)),
            (S.e("c31"), (560, 690, 2.4)), (S.s("c32"), (560, 680, 2.2)), (S.s("hm2"), (1100, 700, 1.4)),
            (S.s("hm2") + 1.5, (1330, 760, 1.9)), (S.e("hold"), (1330, 760, 1.9)), (S.s("h5"), (1400, 600, 1.4)),
            (S.e("quiet"), (1250, 650, 1.5))]
    cx, cy, z = keyframes(t, keys)
    if S.within("hm2", t):
        dx, dy = shake_xy(t, 3)
        cx += dx
    cf = camf(cx, cy, z)
    flap = 0.0
    if S.within("g5", t):
        flap = 0.0
    if S.within("hm2", t) or S.within("hold", t):
        flap = 0.25 * math.sin(t * 25) * (1 - S.p("hold", t))

    def inside(cc):
        if S.within("wings", t):
            k = S.p("wings", t)
            bx = lerp(wx - 60, wx + ww + 60, k)
            by = wy + 40 + math.sin(k * 8) * 10
            fl = math.sin(t * 30)
            cc.drawPath(oval(bx, by, 26, 14), fill("#05060A"))
            cc.drawPath(poly([(bx - 8, by), (bx - 40, by - 30 * fl), (bx + 10, by - 4)]), fill("#05060A"))
            cc.drawPath(poly([(bx + 8, by), (bx + 30, by + 26 * fl), (bx - 6, by + 4)]), fill("#05060A"))
    c.save()
    cf(c)
    room_base(c, t, flap=flap, inside=inside)
    p = pz(S, "cheems", t, "worried", look=(-0.5, -0.8))
    if t >= S.s("hm1"):
        p.look = (0.9, 0.0)
    if S.within("cover", t) or S.within("c31", t):
        p.arm_l = p.arm_r = 205
        p.eye = "wide"
    if S.within("c31", t):
        p.arm_l = p.arm_r = 0
        p.eye = "open"
    if sit_flap:
        p.look = (-0.3, -0.2)
        p.tremble = 1.2 if S.within("hm2", t) else 0.4
        dog(c, "cheems", 1330, 905, 78, p)
    else:
        dog(c, "cheems", 470, 900, 80, p)
        blanket(c, 470, 905, 80, 1.0, t)
    # 掉进来的一根绿羽毛（线索）
    if t >= S.s("quiet"):
        k = S.p("quiet", t, 0.2, None)
        fx = 1330 + math.sin(k * 8) * 60
        fy = lerp(760, 880, ease_out(k))
        c.save()
        c.translate(fx, fy)
        c.rotate(30 + math.sin(k * 8) * 25)
        c.drawPath(spline([(0, -26), (8, -6), (5, 20), (0, 26), (-5, 20), (-8, -6)]), fill("#4CBF55"))
        c.drawLine(0, -26, 0, 30, stroke("#2F7A35", 2))
        c.restore()
    c.restore()
    night_room_light(c, cf, t)
    # 回忆：二哈喊「芝士」
    if S.within("h4", t):
        k = min(S.p("h4", t, 0, 0.25), 1 - S.pe("h4", t, 0.25))
        fw, fh = 900, 520
        fx, fy = W / 2 - fw / 2, H / 2 - fh / 2 - 60
        sep = skia.ColorFilters.Matrix([0.393, 0.769, 0.189, 0, 0, 0.349, 0.686, 0.168, 0, 0,
                                        0.272, 0.534, 0.131, 0, 0, 0, 0, 0, 1, 0])
        lp = skia.Paint()
        lp.setColorFilter(sep)
        lp.setAlphaf(k)
        c.saveLayer(None, lp)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(fx, fy, fw, fh))
        c.translate(fx + fw / 2, fy + fh / 2)
        c.scale(0.9, 0.9)
        c.translate(-2310, -780)
        sets.corridor(c, t)
        hp = Pose(eye="open", mouth="grin", tongue=True, t=t, talk=S.talk("husky", t), look=(-0.6, 0),
                  bob=-0.1 * abs(math.sin(t * 8)))
        draw_critter(c, "husky", 2470, 935, 62, hp)
        draw_critter(c, "cheems", 2150, 940, 62, Pose(eye="sad", brow=1, mouth="frown", ear=0.7, t=t, look=(0.8, 0)))
        c.restore()
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(fx, fy, fw, fh), stroke("#E8D8B0", 10, k))
        draw_text(c, "白天", fx + 70, fy + 60, size=40, name="kuaile", color="#E8D8B0", a=k)
    if S.within("h5", t):
        for i in range(3):
            ph = (t * 0.5 + i / 3) % 1.0
            draw_text(c, "Z", W - 200 + ph * 80, H / 2 - ph * 200, size=60 + ph * 50, name="kuaile",
                      color="#DDE6FF", a=(1 - ph) * 0.9, outline="#2A3050", ow=5)
    ov.vignette(c, 0.65)


# ================================================================ 03:30 老金的纸条
def s_note(c, t, S):
    reading = S.s("x0") <= t < S.s("c34")
    keys = [(0, (700, 560, 1.2)), (S.s("j5"), (430, 380, 1.8)), (S.s("c33"), (480, 560, 1.6)),
            (S.s("j6"), (420, 420, 1.7)), (S.s("slide"), (380, 500, 1.6)), (S.e("j8"), (420, 560, 1.5)),
            (S.s("c34"), (480, 600, 1.7)), (S.s("j9"), (420, 440, 1.7)), (S.s("c35"), (480, 620, 1.8)),
            (S.s("j10"), (380, 380, 2.0)), (S.e("j10"), (360, 340, 2.4))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    vx, vy, vw, vh = ROOM["vent"]
    c.save()
    cf(c)
    room_base(c, t)
    # 老金的眼睛在通风口里
    if S.s("j5") <= t:
        b = blink_value(t, 6.7)
        for s in (-1, 1):
            ex = vx + vw / 2 + s * 32
            ey = vy + vh / 2
            c.drawPath(oval(ex, ey, 9, 11 * (1 - b)), fill("#FFE7B0", 0.9))
            c.drawPath(oval(ex, ey, 20, 20), fill("#FFE7B0", 0.15, blur=6))
    p = pz(S, "cheems", t, "worried", look=(-0.6, -0.9))
    dog(c, "cheems", 470, 900, 80, p)
    blanket(c, 470, 905, 80, 1.0, t)
    # 纸条飘下来
    if S.s("slide") <= t < S.s("x0") + 0.3:
        k = S.p("slide", t, 0.2, None)
        px = vx + vw / 2 + math.sin(k * 7) * 70
        py = lerp(vy + vh, 760, ease_out(k))
        c.save()
        c.translate(px, py)
        c.rotate(math.sin(k * 7) * 30)
        c.drawPath(rrect(-55, -40, 110, 80, 4), fill("#D2BC8E"))
        c.drawPath(rrect(-55, -40, 110, 80, 4), stroke("#6A5030", 3))
        c.restore()
    c.restore()
    night_room_light(c, cf, t)
    if reading:
        k = min(S.p("x0", t, 0, 0.7), 1 - S.pe("x4", t, 0.5))
        shown, hi = 0, -1
        for i, bid in enumerate(("x1", "x2", "x3", "x4")):
            if t >= S.s(bid):
                shown, hi = i + 1, i
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", 0.6 * k))
        ov.rules_paper(c, k, t, shown, hi=hi, hidden=True, scale=0.98, rot=3)
    ov.vignette(c, 0.65)


# ================================================================ 04:00 走廊夜行
def corridor_night_light(c, cf, t, extra=()):
    fl = 0.5 + 0.5 * (math.sin(t * 17) > -0.6) * (0.6 + 0.4 * math.sin(t * 5))
    L = [("pt", 405, 147, 300, "#40FF90", 0.35), ("pt", 3300, 140, 600, "#FFD890", 0.45 * fl),
         ("pt", 900, 140, 450, "#FFD890", 0.18), ("pt", 4700, 300, 400, "#9AC8FF", 0.25)]
    lightmap(c, cf, (58, 66, 114), L + list(extra))
    glow(c, cf, [(405, 147, 120, "#40FF90", 0.4), (3300, 135, 70, "#FFE9A0", 0.6 * fl)])


def s_mirror_walk(c, t, S):
    half = S.s("walk2") + 1.5
    second = t >= half
    if not second:
        xs = [(0, 2300), (S.s("squeeze") + 1.1, 2300), (S.s("c36"), 2240), (S.e("c36") + 1.8, 1600),
              (S.e("c38"), 1600), (half, 1950)]
        x, moving, d = walkx(t, xs)
        cx = keyframes(t, [(0, 2300), (S.s("c36"), 2250), (S.e("c36") + 1.8, 1650), (S.e("c38"), 1650),
                           (half, 1950)], ease=smooth)
        cy, z = 640, 1.35
        if S.within("c37", t) or S.within("c38", t):
            cy, z = keyframes(t, [(S.s("c37"), (640, 1.35)), (S.s("c37") + 1.0, (700, 1.7))])
    else:
        x, moving, d = walkx(t, [(half, 4250), (S.e("walk2"), 4560)])
        cx, cy, z = 4500, 620, 1.3
    cf = camf(cx, cy, z)
    flaps = {1: 0.15 * math.sin(t * 2.0), 2: 0.2 * math.sin(t * 1.6 + 1)}
    sq = 0.0
    if S.within("squeeze", t):
        k = S.p("squeeze", t)
        flaps[3] = math.sin(k * math.pi * 2) * (1 - k)
    c.save()
    cf(c)
    sets.corridor(c, t, night=True, flaps=flaps)
    # 半根骨头
    ov.bone_icon(c, 1690, 915, 0.9, 10, bitten=True)
    p = pz(S, "cheems", t, "nervous")
    if moving:
        p.walk = t * 3.0
        p.turn = 0.55 * d
    if S.within("squeeze", t):
        k = S.p("squeeze", t, 0.5, 1.2)
        p.squash = -0.8 * (1 - k)
        p.alpha = clamp(k * 3)
        dust(c, 2300, 920, S.p("squeeze", t, 1.0, 1.6), 6, 24, 2)
    if S.within("c37", t) or S.within("c38", t):
        p.look = (0.7, 0.8)
        p.tilt = 12
    if S.within("c38", t):
        k = (t * 2) % 1.0
        for i in range(3):
            c.drawPath(spline([(1650 + i * 20, 760 - k * 40), (1660 + i * 20, 740 - k * 40), (1650 + i * 20, 720 - k * 40)],
                              closed=False), stroke("#D8F0D8", 4, 0.8 * (1 - k)))
    y = 945
    if not (S.within("squeeze", t) and S.p("squeeze", t, 0.5, 1.2) <= 0):
        dog(c, "cheems", x, y, 66, p)
    if S.within("squeeze", t):
        ov.onomatopoeia(c, "啵！", 2420, 760, 70, "#FFF1C9", S.p("squeeze", t, 1.0, None), t)
    if second:
        k = S.p("walk2", t, 2.0, None)
        c.drawRect(skia.Rect.MakeXYWH(DOOR_X["groom"] - 135, FLOOR_Y - 440, 270 * k, 440), fill("#0A0E1A", 0.8))
    c.restore()
    corridor_night_light(c, cf, t, [("pt", x, 820, 200, "#B0C0FF", 0.15)])
    # 两段之间的快速黑场
    dk = 1 - min(abs(t - half) / 0.3, 1)
    if dk > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000", dk))
    ov.vignette(c, 0.7)


# ================================================================ 镜子
def s_mirror(c, t, S):
    mx, my, mw, mh = GROOM["mirror"]
    lamp_off = t >= S.s("k12") + 0.35
    fallen = S.p("k12", t, 0.25, 0.6)
    keys = [(0, (960, 560, 1.0)), (S.e("c39"), (900, 560, 1.15)), (S.s("peek") + 0.8, (900, 540, 1.3)),
            (S.e("peek"), (920, 520, 1.4)), (S.s("c40"), (720, 680, 1.6)), (S.s("turn") + 0.9, (720, 680, 1.5)),
            (S.s("turn") + 1.3, (900, 540, 1.35)), (S.s("k12"), (960, 560, 1.2)), (S.s("dark") + 0.5, (960, 560, 1.1)),
            (S.s("k13"), (900, 600, 1.1)), (S.e("retreat"), (940, 520, 1.3))]
    cx, cy, z = keyframes(t, keys)
    if S.within("k12", t) or S.within("dark", t):
        dx, dy = shake_xy(t, 12 * (1 - S.p("dark", t)))
        cx, cy = cx + dx, cy + dy
    cf = camf(cx, cy, z)
    spun = S.within("turn", t) and S.p("turn", t, 0.0, 0.9) > 0.2 and S.p("turn", t, 0.0, 0.9) < 1
    c.save()
    cf(c)
    sets.grooming(c, t, lamp_on=not lamp_off, lamp_fallen=fallen)
    # 镜子里
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(mx, my, mw, mh))
    if not lamp_off:
        c.drawRect(skia.Rect.MakeXYWH(mx, my, mw, mh), fill(shader=lin((0, my), (0, my + mh), ["#34405A", "#1E2638"])))
        for x in range(mx, mx + mw, 60):
            c.drawLine(x, my, x, my + mh, stroke("#3E4C68", 2))
        c.drawCircle(960, my + mh - 20, 160, fill("#FFD890", 0.25, blur=30))
        # 窗外的人慢慢出现在「倒影」后面
        man = S.p("peek", t, 1.2, 2.6)
        if t >= S.s("turn"):
            man = 1.0
        closer = S.p("turn", t, 1.1, 2.0, ease_out)
        if man > 0:
            hs = lerp(38, 62, closer)
            hp = HPose(face="evil", alpha=man * 0.85, r_up=lerp(10, 165, closer), r_lo=lerp(0, -20, closer),
                       hold="flashlight" if t >= S.s("turn") + 1.7 else None)
            draw_human(c, "thief", 1080, my + mh + 380 * lerp(1, 1.4, closer), hs, hp)
        rp = pz(S, "cheems", t, "nervous", look=(-0.6, 0.0), flip=True)
        rp.alpha = 0.75
        draw_critter(c, "cheems", 800, my + mh + 160, 70, rp)
        c.drawRect(skia.Rect.MakeXYWH(mx, my, mw, mh), fill("#8AA0C8", 0.12))
        if t >= S.s("turn") + 1.7:
            c.drawCircle(1180, my + 120, 70, fill("#FFFFFF", 0.9, blur=18))
    else:
        man = 1 - S.p("retreat", t)
        sets.alley_view(c, mx, my, mw, mh, t, man=man, flashlight=False)
    c.restore()
    c.drawPath(poly([(mx + 30, my + 20), (mx + 140, my + 20), (mx + 60, my + mh - 20), (mx + 10, my + mh - 20)]),
               fill("#FFFFFF", 0.06))
    # Cheems
    p = pz(S, "cheems", t, "nervous", look=(0.8, -0.5))
    if spun:
        p.flip = True
        p.look = (0.8, -0.3)
    if S.within("c39", t):
        p.eye = "closed" if (t - S.s("c39")) % 2.0 < 1.4 else "open"
        p.look = (-0.6, 0.2)
    if t >= S.s("k12"):
        p.look = (0.4, -0.5)
    cx_ch = 600
    if t >= S.s("k12") + 0.2:
        p.squash = 0.4 * (1 - S.p("dark", t))
    dog(c, "cheems", cx_ch, 975, 92, p)
    # 大橘扑进来
    if t >= S.s("k12"):
        k = S.p("k12", t, 0, 0.45)
        catx = lerp(2050, 1080, ease_out(k))
        caty = lerp(700, 975, k) - math.sin(k * math.pi) * 260
        cp = pz(S, "cat", t, "angry", look=(-0.6, -0.3))
        if t < S.s("k13"):
            cp.mouth = "open"
        dog(c, "cat", catx, caty, 82, cp)
    c.restore()
    # 灯光
    if not lamp_off:
        lights = [("pt", 960, 600, 620, "#FFD890", 0.85)]
        if t >= S.s("turn") + 1.7:
            lights.append(("cone", 1180, 290, 150, 26, 1300, "#FFFFFF", 0.9))
        lightmap(c, cf, (60, 66, 100), lights)
        glow(c, cf, [(960, 580, 110, "#FFE8A8", 0.6)])
        if t >= S.s("turn") + 1.7:
            glow(c, cf, [(1180, 290, 240, "#FFFFFF", 0.7)])
    else:
        lightmap(c, cf, (40, 48, 92), [("rect", mx, my, mw, mh, "#7080C0", 0.4, 30),
                                       ("beam", [(mx, my + mh), (mx + mw, my + mh), (mx + mw + 300, 1080), (mx - 200, 1080)],
                                        "#6070B0", 0.25, 40)])
    if S.within("k12", t):
        k = S.p("k12", t, 0.3, 0.8)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 0.3 * (1 - k) * (k > 0)))
    ov.vignette(c, 0.6)


# ================================================================ 真相
def s_truth(c, t, S):
    mx, my, mw, mh = GROOM["mirror"]
    card = None
    for bid, kind in (("k17", "map"), ("k18", "robot"), ("k19", "bone"), ("c42", "parrot")):
        if S.s(bid) <= t < (S.e(bid) if bid != "c42" else S.e("k21")):
            card = (bid, kind)
    keys = [(0, (700, 640, 1.5)), (S.s("k15"), (760, 660, 1.6)), (S.s("k16"), (720, 650, 1.75)),
            (S.s("k17") + 0.6, (980, 620, 1.35)), (S.e("k21"), (980, 620, 1.35)), (S.s("c43") + 0.5, (700, 660, 1.6)),
            (S.s("k22"), (760, 640, 1.7)), (S.s("silent"), (820, 640, 1.8)), (S.e("k23"), (840, 620, 2.0))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.grooming(c, t, lamp_on=False, lamp_fallen=1.0)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(mx, my, mw, mh))
    sets.alley_view(c, mx, my, mw, mh, t, man=0.0, van=True)
    c.restore()
    p = pz(S, "cheems", t, "scared", look=(0.8, -0.2))
    if S.within("k15", t):
        p.look = (0.2, 0.9)
        p.mark = "?"
    dog(c, "cheems", 560, 1000, 86, p)
    cp = pz(S, "cat", t, "normal", look=(-0.8, -0.1))
    if S.within("silent", t):
        cp.turn = 0.6
        cp.look = (0.9, 0.3)
    dog(c, "cat", 860, 1000, 80, cp)
    if S.within("k15", t):
        # 面包梗
        k = S.p("k15", t, 0.8, 1.4)
        c.save()
        c.translate(380, 760)
        c.scale(ease_out_back(k), ease_out_back(k))
        loaf = spline([(-80, 30), (-85, -20), (-50, -55), (0, -62), (50, -55), (85, -20), (80, 30)], tension=0.9)
        loaf.close()
        draw_shape(c, loaf, "#E8A04F", "#5A3015", 5, "#C97A33", (-6, -8))
        for i in range(3):
            c.drawLine(-40 + i * 40, -50, -30 + i * 40, -20, stroke("#FFF2DC", 6))
        c.restore()
        sparkles(c, 380, 740, k, t, 4, 90)
    c.restore()
    lightmap(c, cf, (88, 96, 150), [("rect", mx, my, mw, mh, "#7080C0", 0.45, 30),
                                    ("beam", [(mx, my + mh), (mx + mw, my + mh), (mx + mw + 300, 1080), (mx - 200, 1080)],
                                     "#6070B0", 0.3, 40)])
    if S.within("k16", t):
        k = S.p("k16", t, 0, 0.6)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#400000", 0.3 * (1 - k)))
    if card:
        bid, kind = card
        k = S.p(bid, t, 0, 0.5)
        end = S.e(bid) if bid != "c42" else S.e("k21")
        k_out = clamp((end - t) / 0.4)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000", 0.35 * min(k, k_out)))
        ov.explain_card(c, kind, min(k, k_out), t)
    ov.vignette(c, 0.55)


# ================================================================ 天亮
def s_dawn(c, t, S):
    broken = t >= S.s("t1")
    keys = [(0, (700, 540, 1.0)), (S.e("n9"), (500, 560, 1.15)), (S.s("om1") + 0.5, (420, 520, 1.6)),
            (S.s("c45"), (700, 600, 1.2)), (S.s("stop"), (560, 640, 1.5)), (S.s("c46"), (430, 640, 1.7)),
            (S.e("om2"), (420, 600, 1.7)), (S.s("c47"), (620, 660, 1.6)), (S.s("j11"), (900, 640, 1.2)),
            (S.s("j12") + 0.5, (1000, 650, 1.5)), (S.e("j13"), (1020, 650, 1.65)), (S.s("c49"), (850, 660, 1.4)),
            (S.e("realize"), (900, 650, 1.45)), (S.s("t1"), (560, 560, 1.05)), (S.e("t1"), (600, 560, 1.1))]
    cx, cy, z = keyframes(t, keys)
    if S.within("t1", t):
        dx, dy = shake_xy(t, 16 * (1 - S.p("t1", t, 0, 0.8)))
        cx, cy = cx + dx, cy + dy
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.lobby(c, "dawn", t, door_broken=1.0 if broken else 0.0)
    sets.draw_cage(c, 640, 520, front=False)
    sets.draw_cage(c, 640, 520, front=True)
    # 门外的人（伪装成主人的蓝卫衣）
    if not broken:
        hp = HPose(face="evil", talk=0, t=t, l_up=4, r_up=4, l_lo=-8, r_lo=-8)
        draw_human(c, "thief_blue", 290, 880, 54, hp)
        # 帽子里露出的一撮绿毛
        c.drawPath(oval(330, 880 - 54 * 7.95, 16, 12), fill("#4CBF55"))
        c.drawPath(oval(340, 880 - 54 * 8.05, 7, 7), fill("#E8473B"))
        c.drawRect(skia.Rect.MakeXYWH(120, 300, 340, 570), fill("#A8C0E8", 0.18))
    else:
        k = S.p("t1", t, 0, 0.8)
        hp = HPose(face="evil", talk=S.talk("thief", t), t=t, hold="sack", lean=0.3 * (1 - k))
        draw_human(c, "thief_blue", lerp(290, 560, ease_out(k)), 920, 56, hp)
        rnd = random.Random(9)
        for i in range(16):
            gx = 300 + rnd.uniform(-120, 300) * k
            gy = 860 + rnd.uniform(-40, 60)
            c.drawPath(poly([(gx, gy), (gx + 14, gy - 8), (gx + 6, gy + 10)]), fill("#DDEBFF", 0.8))
    # Cheems
    xs = [(0, 980), (S.s("c45") + 0.2, 980), (S.s("c45") + 1.2, 640), (S.e("c49"), 640), (S.s("t1") + 0.2, 640),
          (S.s("t1") + 0.8, 760)]
    x, moving, d = walkx(t, xs)
    p = pz(S, "cheems", t, "normal", look=(-0.8, -0.4))
    if moving:
        p.walk = t * 4
        p.turn = 0.6 * d
    if S.within("stop", t):
        p.look = (-0.8, 0.3)
        p.mark = "?"
    if S.s("j11") <= t < S.s("t1"):
        p.look = (0.8, -0.3)
    if broken:
        p.look = (-0.9, -0.5)
    dog(c, "cheems", x, 930, 70, p)
    # 老金
    if t >= S.s("j11"):
        k = S.p("j11", t, 0, 0.8)
        gp = pz(S, "golden", t, "sad", look=(-0.8, 0.2), alpha=k)
        dog(c, "golden", 1150, 930, 70, gp)
    c.restore()
    lightmap(c, cf, (128, 132, 182), [("beam", [(120, 300), (460, 300), (1000, 1080), (0, 1080)], "#FFC89A", 0.35, 30),
                                      ("pt", 300, 600, 500, "#FFB890", 0.3)])
    ov.vignette(c, 0.5)


# ================================================================ 反击
def s_fight(c, t, S):
    # 分三段：大堂 → 走廊叫醒二哈 → 邻居亮灯 → 大堂扭打
    in_corr = S.s("c50") + 1.0 <= t < S.e("h7")
    in_ext = S.within("chorus", t)
    if in_corr:
        _fight_corridor(c, t, S)
    elif in_ext:
        k = S.p("chorus", t)
        cf = camf(1200, 560, 0.85 + 0.05 * k)
        c.save()
        cf(c)
        sets.exterior(c, "dawn", t, neighbors=k * 1.6)
        c.restore()
        lightmap(c, cf, (150, 150, 190), [("pt", 1300, 500, 900, "#FFD0A0", 0.2)])
        rnd = random.Random(4)
        for i in range(10):
            kk = clamp((k - i * 0.07) / 0.3)
            if kk > 0 and kk < 1:
                ov.onomatopoeia(c, "汪！", rnd.uniform(150, W - 150), rnd.uniform(150, H - 300), rnd.uniform(60, 110),
                                "#FFF1C9", kk, t, rot=rnd.uniform(-15, 15))
        ov.vignette(c, 0.4)
    else:
        _fight_lobby(c, t, S)


def _fight_corridor(c, t, S):
    howl = S.within("h7", t)
    k = S.p("h7", t, 0, 1.5)
    cx, cy, z = 3000, 640, 1.5
    if howl:
        dx, dy = shake_xy(t, 18 * (1 - k * 0.5))
        cx, cy = cx + dx, cy + dy
        z = 1.5 - 0.2 * ease_out(k)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.corridor(c, t, night=True, flaps={4: 0.3 * math.sin(t * 9) if S.within("h6", t) else 0})
    p = pz(S, "cheems", t, "determined", look=(0.8, -0.3))
    dog(c, "cheems", 2850, 945, 66, p)
    if t >= S.s("h6"):
        kk = S.p("h6", t, 0, 0.5)
        hp = pz(S, "husky", t, "sleepy", look=(-0.7, 0))
        if howl:
            hp.tilt = -25
            hp.mouth = "o"
            hp.eye = "tight"
            hp.ear = -0.2
        dog(c, "husky", lerp(3100, 3170, kk), 945, 66, hp)
    c.restore()
    corridor_night_light(c, cf, t)
    if howl:
        for i in range(5):
            ph = (t * 1.2 + i / 5) % 1.0
            r = 100 + ph * 1200
            c.drawCircle(W / 2 + 150, H / 2 - 100, r, stroke("#FFFFFF", 14 * (1 - ph), 0.5 * (1 - ph)))
        ov.onomatopoeia(c, "嗷呜————！", W / 2 + 60, 200, 140, "#BFE4FF", min(S.p("h7", t), 0.9), t, rot=-4,
                        outline="#10284A")
    ov.vignette(c, 0.6)


def _fight_lobby(c, t, S):
    lunge = S.p("lunge", t)
    after_lunge = t >= S.s("lunge")
    slip_k = S.p("slip", t, 0.4, 1.2)
    keys = [(0, (800, 600, 1.25)), (S.s("c50"), (900, 620, 1.3)), (S.s("c50") + 1.0, (1500, 640, 1.2)),
            (S.s("t2"), (760, 560, 1.2)), (S.s("lunge"), (820, 600, 1.35)), (S.s("j14"), (840, 620, 1.4)),
            (S.s("k25"), (780, 470, 1.6)), (S.s("c52"), (860, 700, 1.5)), (S.s("slip"), (900, 620, 1.2)),
            (S.e("slip"), (1000, 600, 1.15))]
    cx, cy, z = keyframes(t, keys)
    if S.within("slip", t) and slip_k >= 1:
        dx, dy = shake_xy(t, 14 * (1 - S.p("slip", t, 1.1, None)))
        cx, cy = cx + dx, cy + dy
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.lobby(c, "dawn", t, door_broken=1.0)
    sets.draw_cage(c, 640, 520, front=False)
    sets.draw_cage(c, 640, 520, front=True)
    # 玩具猫倒在地上
    c.save()
    c.translate(700, 960)
    c.rotate(-80)
    draw_critter(c, "robocat", 0, 0, 34, Pose(t=t, glow=0.3))
    c.restore()
    # 大橘
    cat_on_face = S.s("k25") <= t < S.s("slip") + 0.6
    # 偷狗贼
    tx = 920 + lerp(0, 120, ease_out(lunge))
    ang = 0
    if t >= S.s("slip"):
        tx = lerp(1040, 840, ease_in_out(S.p("slip", t, 0.2, 1.1)))
        ang = -75 * ease_in(slip_k)
    face = "evil" if t < S.s("j14") else "shock"
    hp = HPose(face=face, talk=S.talk("thief", t), t=t, lean=0.4 * lunge if t < S.s("slip") else 0,
               r_up=60 + 40 * lunge, r_lo=-30, l_up=30 if t >= S.s("k25") else 10, l_lo=-120 if cat_on_face else 0)
    c.save()
    c.translate(tx, 930)
    c.rotate(ang)
    draw_human(c, "thief_blue", 0, 0, 56, hp)
    if cat_on_face:
        cp = pz(S, "cat", t, "angry")
        cp.mouth = "open"
        cp.tremble = 1.5
        draw_critter(c, "cat", 30, -56 * 7.6, 50, cp)
        for i in range(3):
            c.drawLine(-60 + i * 30, -56 * 9.5, -20 + i * 30, -56 * 8.3, stroke("#FF4040", 7, 0.8 * (math.sin(t * 20 + i) > 0)))
    c.restore()
    if not cat_on_face and t < S.s("k25"):
        cp = pz(S, "cat", t, "angry", look=(-0.6, -0.2))
        dog(c, "cat", 1190, 646, 58, cp)
    # 老金扑腿
    if t >= S.s("j14"):
        k = S.p("j14", t, 0, 0.6)
        gx = lerp(1350, tx + 60, ease_out(k)) if t < S.s("slip") else tx + 120
        gy = 935 - math.sin(k * math.pi) * 160
        gp = pz(S, "golden", t, "angry", look=(-0.8, -0.3))
        dog(c, "golden", gx, gy, 70, gp)
    # Cheems 咬裤脚
    p = pz(S, "cheems", t, "determined", look=(-0.6, -0.5))
    chx = 1180
    if S.s("c50") <= t < S.s("c50") + 1.0:
        k = S.p("c50", t, 0, 1.0)
        chx = lerp(1180, 1900, ease_in(k))
        p.walk = t * 5
        p.turn = 0.7
    if t >= S.s("c52"):
        chx = tx - 70 + 20 * math.sin(t * 12)
        p.lean = -0.6
        p.mouth = "grin"
        p.eye = "tight"
    dog(c, "cheems", chx, 955, 66, p)
    if S.within("c52", t):
        ov.onomatopoeia(c, "嗷呜！", chx - 40, 650, 60, "#FFB45C", S.p("c52", t, 0.6, None), t)
    if S.within("slip", t) and slip_k >= 1:
        k = S.p("slip", t, 1.1, None)
        dust(c, 840, 900, k, 10, 40, 6)
        for i in range(5):
            ang2 = t * 4 + i * 1.25
            draw_text(c, "★", 820 + math.cos(ang2) * 90, 560 + math.sin(ang2) * 30, size=46, name="sans",
                      color="#FFE36B", a=1 - k)
    c.restore()
    lightmap(c, cf, (150, 152, 196), [("beam", [(120, 300), (460, 300), (1000, 1080), (0, 1080)], "#FFC89A", 0.35, 30)])
    if S.within("slip", t):
        ov.onomatopoeia(c, "哐当！", W / 2 - 150, H / 2 - 160, 150, "#FFFFFF", S.p("slip", t, 1.1, None), t, rot=-10)
    ov.vignette(c, 0.45)


# ================================================================ 面包车
def s_van(c, t, S):
    in_van = t < S.s("p3")
    if in_van:
        bent = S.p("z8", t, 0.4, 1.2, ease_out)
        burst = S.p("burst", t, 0, 0.8)
        keys = [(0, (960, 600, 1.3)), (S.s("g6"), (900, 620, 1.4)), (S.s("z7"), (980, 580, 1.5)),
                (S.s("z8"), (960, 560, 1.6)), (S.e("burst"), (960, 560, 1.2))]
        cx, cy, z = keyframes(t, keys)
        if S.within("z8", t) or S.within("burst", t):
            dx, dy = shake_xy(t, 12)
            cx, cy = cx + dx, cy + dy
        cf = camf(cx, cy, z)
        c.save()
        cf(c)
        sets.van_inside(c, t)
        zx = 900 + 160 * ease_out(burst)
        zp = pz(S, "zhuang", t, "sleepy", look=(0.3, 0))
        if t >= S.s("z8"):
            zp.flex = clamp(S.p("z8", t, 0, 0.5) * 2)
        dog(c, "zhuang", zx, 830, 62, zp)
        kp = pz(S, "corgi", t, "cry", look=(0.6, -0.4))
        if t >= S.s("burst"):
            dog(c, "corgi", zx + 40, 830 - 62 * 4.4, 34, kp)
        else:
            dog(c, "corgi", 1110, 830, 46, kp)
        if burst < 0.5:
            sets.cage_front(c, 640, 420, 640, 420, bent=bent)
        else:
            for i in range(6):
                k = burst
                bx = 640 + i * 110 + (i - 2.5) * 200 * k
                by = 620 + 300 * k * k - 200 * k
                c.save()
                c.translate(bx, by)
                c.rotate((i - 2.5) * 50 * k)
                c.drawLine(0, -180, 0, 180, stroke("#B9C1CE", 10))
                c.restore()
        if t >= S.s("z8"):
            a = S.p("z8", t, 0, 0.6)
            for i in range(10):
                ang = i / 10 * 2 * math.pi + t
                c.drawLine(zx + math.cos(ang) * 120, 640 + math.sin(ang) * 140, zx + math.cos(ang) * 200,
                           640 + math.sin(ang) * 230, stroke("#FFE36B", 8, 0.7 * a))
        c.restore()
        lightmap(c, cf, (90, 96, 130), [("rect", 1600, 80, 400, 740, "#FFC89A", 0.7, 40),
                                        ("beam", [(1600, 820), (2000, 820), (1500, 1080), (1000, 1080)], "#FFC89A", 0.4, 40),
                                        ("pt", 960, 640, 500, "#FFE3A0", 0.4 * S.p("z8", t, 0, 0.5))])
        if S.within("z8", t):
            ov.onomatopoeia(c, "蛋白质之力！", W / 2, 200, 120, "#FF6B5C", S.p("z8", t), t, rot=-6)
        if S.within("burst", t):
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 0.5 * (1 - S.p("burst", t, 0, 0.4))))
    else:
        # 门口：警车、被带走的偷狗贼、慌张的阿福
        k = S.p("n10", t)
        cf = camf(1250, 600, 0.9 + 0.04 * k)
        c.save()
        cf(c)
        sets.exterior(c, "dawn", t, neighbors=1.6)
        # 警车（偷狗贼坐在后座）
        px = 1700
        draw_human(c, "thief_blue", px + 70, 905, 30, HPose(face="sad", t=t))
        c.drawPath(rrect(px - 260, 820, 520, 120, 36), fill("#F4F4F4"))
        c.drawPath(rrect(px - 160, 740, 320, 100, 30), fill("#F4F4F4"))
        c.drawPath(rrect(px - 260, 860, 520, 34, 10), fill("#2C5AA0"))
        draw_text(c, "警察", px, 890, size=34, name="sans", weight=700, color="#FFFFFF")
        c.drawPath(rrect(px - 130, 755, 110, 70, 10), fill("#3A4460"))
        c.drawPath(rrect(px + 20, 755, 110, 70, 10), fill("#3A4460"))
        red = (t * 3) % 1.0 < 0.5
        c.drawPath(rrect(px - 60, 718, 55, 24, 8), fill("#FF3030" if red else "#801818"))
        c.drawPath(rrect(px + 5, 718, 55, 24, 8), fill("#3060FF" if not red else "#182880"))
        for wx in (px - 160, px + 160):
            c.drawCircle(wx, 940, 46, fill("#15161C"))
            c.drawCircle(wx, 940, 18, fill("#8A8A8A"))
        draw_human(c, "police", 1250, 905, 52, HPose(face="smile", t=t, r_up=40, r_lo=-20))
        pp = Pose(t=t, talk=S.talk("parrot", t), wing=abs(math.sin(t * 16)), look=(0.5, 0))
        draw_parrot(c, 1450 + 40 * math.sin(t * 2), 520 + 30 * math.sin(t * 3.3), 70, pp)
        c.restore()
        red_a = 0.35 if red else 0.0
        lightmap(c, cf, (150, 150, 190), [("pt", px - 30, 730, 700, "#FF3030", red_a),
                                          ("pt", px + 30, 730, 700, "#3060FF", 0.35 - red_a)])
        ov.vignette(c, 0.4)


# ================================================================ 早晨
def _morning_cast(c, t, S, staff_x=640, staff_face="smile", turn_to_photo=0.0, cheems_look=None):
    hp = HPose(face=staff_face, talk=S.talk("staff", t), t=t, turn=-0.4 if turn_to_photo else 0.3,
               l_up=10, r_up=10 if not S.within("s1", t) else 60, r_lo=-40 if S.within("s1", t) else 0)
    draw_human(c, "staff", staff_x, 930, 54, hp)
    gp = pz(S, "golden", t, "normal", look=(0.3, -0.3))
    dog(c, "golden", 800, 920, 66, gp)
    p = pz(S, "cheems", t, "normal", look=cheems_look or (-0.7, -0.6))
    dog(c, "cheems", 1000, 940, 66, p)
    dog(c, "corgi", 1150, 950, 50, pz(S, "corgi", t, "happy", look=(-0.7, -0.2)))
    dog(c, "zhuang", 1330, 950, 50, pz(S, "zhuang", t, "happy", look=(-0.7, -0.1), flex=0.3))
    hp2 = pz(S, "husky", t, "derp", look=(-0.6, 0))
    dog(c, "husky", 1520, 950, 58, hp2)


def s_morning(c, t, S):
    keys = [(0, (1000, 600, 1.0)), (S.s("g7"), (1080, 660, 1.25)), (S.s("c53"), (900, 640, 1.3)),
            (S.s("s2"), (800, 600, 1.3)), (S.e("freeze"), (820, 590, 1.4)), (S.s("s3") + 0.5, (900, 520, 1.2)),
            (S.s("plaque") + 0.8, (1220, 300, 3.0)), (S.e("plaque"), (1220, 310, 3.1)), (S.s("s4") + 0.8, (900, 600, 1.4)),
            (S.e("s4"), (900, 600, 1.4)), (S.s("turn") + 1.8, (1900, 600, 1.4)), (S.e("fade"), (1930, 580, 1.55)),
            (S.s("c55") + 0.4, (1020, 680, 2.0)), (S.e("c55"), (1020, 690, 2.2))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.lobby(c, "morning", t, door_broken=1.0, photo_ribbon=False)
    sets.draw_cage(c, 640, 520, front=False)
    sets.draw_cage(c, 640, 520, front=True)
    sx = keyframes(t, [(0, 300), (2.0, 640)], ease=smooth)
    look = None
    if t >= S.s("turn"):
        look = (0.9, -0.3)
    _morning_cast(c, t, S, staff_x=sx, staff_face="shock" if S.after("freeze", t) else "smile",
                  turn_to_photo=S.after("s3", t), cheems_look=look)
    # 幽灵大橘
    if t >= S.s("turn"):
        k = S.p("turn", t, 1.2, 2.6)
        out = S.p("fade", t, 0.3, None)
        cp = pz(S, "cat", t, "happy", look=(-0.6, 0.1))
        cp.alpha = k * (1 - out) * 0.85
        dog(c, "cat", 1960, 860, 70, cp)
        if k > 0:
            c.drawCircle(1960, 720, 180, fill("#FFF4C8", 0.3 * k * (1 - out), blur=40))
        if out > 0:
            rnd = random.Random(1)
            for i in range(40):
                ph = clamp(out * 1.3 - rnd.random() * 0.3)
                px = 1960 + rnd.uniform(-90, 90) + math.sin(t * 2 + i) * 10
                py = 860 - rnd.uniform(0, 260) - ph * 300
                c.drawCircle(px, py, rnd.uniform(3, 7), fill("#FFF4C8", (1 - ph) * 0.9 * (ph > 0)))
    c.restore()
    lightmap(c, cf, (236, 228, 214), [("beam", [(120, 300), (460, 300), (1100, 1080), (0, 1080)], "#FFE8B0", 0.3, 30),
                                      ("beam", [(1820, 250), (2120, 250), (2200, 1080), (1700, 1080)], "#FFF0C0",
                                       0.35 * S.p("turn", t, 0.5, 2.0), 40)])
    if S.within("plaque", t) or (S.s("s3") + 1.0 < t < S.s("s4") + 1.0):
        k = min(S.p("plaque", t, 0.6, 1.4), 1 - clamp((t - S.s("s4") - 0.4) / 0.6))
        if k > 0:
            c.drawPath(rrect(W / 2 - 520, H - 330, 1040, 150, 14), fill("#D9B26A", 0.95 * k))
            c.drawPath(rrect(W / 2 - 520, H - 330, 1040, 150, 14), stroke("#6A4A1A", 5, k))
            draw_text(c, "本店店猫　大橘（2012—2019）", W / 2, H - 268, size=50, name="brush", color="#3A2410", a=k)
            draw_text(c, "她曾从偷狗贼手里，救下了七只狗狗。", W / 2, H - 210, size=40, name="brush", color="#3A2410", a=k)
    ov.vignette(c, 0.3)


# ================================================================ 主人来接
def s_reunion(c, t, S):
    keys = [(0, (900, 600, 1.05)), (S.s("c56"), (950, 620, 1.3)), (S.s("hug") + 0.5, (900, 560, 1.4)),
            (S.s("c57"), (1050, 620, 1.3)), (S.s("o4"), (1080, 620, 1.3)), (S.s("j16"), (1200, 660, 1.6)),
            (S.e("wag"), (1100, 620, 1.3))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    sets.lobby(c, "morning", t, door_broken=1.0)
    sets.draw_cage(c, 640, 520, front=False)
    sets.draw_cage(c, 640, 520, front=True)
    ox = keyframes(t, [(0, 150), (1.8, 820)], ease=smooth)
    running = t < 1.8
    hugging = S.s("c56") + 1.0 <= t < S.s("c57")
    if running:
        hp = walk_pose(t * 2.2, turn=0.7, hold="leash", face="worried", talk=S.talk("owner", t), t=t)
    else:
        hp = HPose(kneel=True, pelvis=-2.7, turn=0.3 if t < S.s("o4") else 0.6, face="smile" if hugging else "worried",
                   talk=S.talk("owner", t), t=t, hold="leash", r_up=40, r_lo=-40,
                   l_up=60 if hugging else 15, l_lo=-80 if hugging else 0, look=(0.7, 0.3))
        if t >= S.s("o4"):
            hp.face = "smile"
    draw_human(c, "owner", ox, 935, 58, hp)
    # Cheems
    p = pz(S, "cheems", t, "shock", look=(-0.8, -0.6))
    if hugging:
        k = S.p("c56", t, 1.0, 1.6)
        p2 = pz(S, "cheems", t, "happy")
        hx = lerp(1000, ox + 40, ease_out(k))
        hy = lerp(940, 935 - 58 * 3.0, ease_out(k)) - math.sin(k * math.pi) * 120
        dog(c, "cheems", hx, hy, 60, p2)
        hearts(c, hx, hy - 260, 1.0, t)
    else:
        if t >= S.s("c57"):
            p.look = (0.8, -0.2)
        dog(c, "cheems", 1000, 945, 64, p)
        if t >= S.s("c57"):
            # 系上红色牵引绳
            c.drawPath(spline([(ox + 58 * 1.6, 935 - 58 * 3.2), (ox + 120, 880), (980, 945 - 64 * 1.62)], closed=False),
                       stroke("#E23A3A", 6))
    # 老金
    gp = pz(S, "golden", t, "sad", look=(-0.8, -0.2))
    if t >= S.s("wag"):
        gp.tail = math.sin(t * 10) * 1.0
    dog(c, "golden", 1280, 935, 70, gp)
    if t >= S.s("wag"):
        hearts(c, 1280, 935 - 300, S.p("wag", t, 0.5, 1.5), t, 3)
    c.restore()
    lightmap(c, cf, (238, 230, 216), [("beam", [(120, 300), (460, 300), (1100, 1080), (0, 1080)], "#FFE8B0", 0.3, 30)])
    if S.within("c56", t):
        ov.onomatopoeia(c, "红色牵引绳！", W / 2, 230, 90, "#FF5A5A", S.p("c56", t, 0.2, None), t, rot=-4)
    ov.vignette(c, 0.3)


# ================================================================ 尾声
def s_epilogue(c, t, S):
    if t < S.s("n12"):
        # 大堂夜里：照片前的一小碗猫粮
        k = S.p("n11", t)
        cf = camf(1220, 460 - 20 * k, 1.6 + 0.1 * k)
        c.save()
        cf(c)
        sets.lobby(c, "night", t)
        sets.bowl(c, 1220, 628, full=True, s=0.45)
        c.restore()
        lightmap(c, cf, (70, 70, 110), [("pt", 1220, 420, 420, "#FFD890", 0.75)])
        ov.vignette(c, 0.6)
        return
    if t >= S.s("credits"):
        ov.credits(c, S.p("credits", t), t)
        return
    note_shot = S.s("o6") <= t < S.s("window")
    if note_shot:
        k = S.p("o6", t, 0, 0.8)
        c.drawRect(skia.Rect.MakeWH(W, H), fill(shader=lin((0, 0), (0, H), ["#E9EEF2", "#C8D2DA"])))
        sets.fridge_note(c, W / 2 - 120, H / 2 + 20, 1.9, t, line2=S.p("c59", t, 0.1, -0.3))
        if t >= S.s("c59"):
            p = pz(S, "cheems", t, "smug", look=(-0.8, -0.5))
            if S.within("o7", t):
                p.mark = "!"
            dog(c, "cheems", W - 330, H + 60, 120, p)
            if S.within("c59", t):
                c.save()
                c.translate(W - 520, H - 300)
                c.rotate(-40)
                c.drawPath(rrect(-12, -80, 24, 160, 8), fill("#E2574C"))
                c.drawPath(poly([(-12, -80), (12, -80), (0, -112)]), fill("#E2574C"))
                c.restore()
        ov.vignette(c, 0.3)
        return
    keys = [(S.s("n12"), (1000, 560, 1.0)), (S.e("n12"), (1080, 640, 1.25)), (S.s("window"), (1000, 600, 1.1)),
            (S.s("window") + 2.0, (520, 360, 1.9)), (S.e("r7c"), (520, 360, 2.1))]
    cx, cy, z = keyframes(t, keys)
    cf = camf(cx, cy, z)
    c.save()
    cf(c)
    cat_k = S.p("window", t, 1.0, 2.5) * (1 - S.p("r7c", t, 0.5, None))
    sets.home(c, t, cat_in_window=cat_k)
    dog(c, "golden", 1230, 860, 60, pz(None, "golden", t, "sleep"))
    dog(c, "cheems", 1080, 870, 58, pz(None, "cheems", t, "sleep"))
    c.restore()
    lightmap(c, cf, (90, 80, 100), [("pt", 900, 300, 700, "#FFD890", 0.75), ("rect", 260, 160, 520, 400, "#7080C0", 0.3, 30)])
    glow(c, cf, [(900, 300, 140, "#FFE8A8", 0.5)])
    if t >= S.s("r7c"):
        k = S.p("r7c", t, 0, 1.0)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000", 0.55 * k))
        draw_text(c, "第七条：本守则，全部为真。", W / 2, H / 2 + 30, size=84, name="brush", color="#E8E0C8", a=k,
                  glow=("#C8302A", 24, 0.5))
    ov.vignette(c, 0.55)


SCENE_FUNCS = {
    "cold_open": s_cold_open, "drop_off": s_drop_off, "lobby": s_lobby, "corridor_day": s_corridor_day,
    "rules": s_rules, "corgi_cry": s_corgi_cry, "shadow": s_shadow, "two_cats": s_two_cats, "bone": s_bone,
    "voices": s_voices, "note": s_note, "mirror_walk": s_mirror_walk, "mirror": s_mirror, "truth": s_truth,
    "dawn": s_dawn, "fight": s_fight, "van": s_van, "morning": s_morning, "reunion": s_reunion,
    "epilogue": s_epilogue,
}
