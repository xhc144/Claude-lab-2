"""场景背景：全部是矢量现画（每帧重画，镜头推近也保持清晰）。

世界坐标：地面（地板）y≈860~900，画面高 1080。
"""
from __future__ import annotations

import math
import random

import skia

from gfx import (clamp, draw_shape, draw_text, fill, lerp, lin, mix, oval, poly, rad, rrect, shade, spline,
                 stroke, wave)

LINE = "#3A2A20"


def paw(c, x, y, s, color, a=1.0, ang=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    p = fill(color, a)
    c.drawPath(oval(0, 0.25, 0.55, 0.45), p)
    for dx, dy in ((-0.55, -0.35), (-0.2, -0.7), (0.2, -0.7), (0.55, -0.35)):
        c.drawPath(oval(dx, dy, 0.2, 0.26), p)
    c.restore()


# ================================================================ 外景
def exterior(c, tod="day", t=0.0, neighbors=0.0):
    """旅馆外观。世界宽 2400。tod: day / dawn / night。"""
    sky = {"day": ("#7CC8F2", "#D8F0FF"), "dawn": ("#33416E", "#F3B08A"), "night": ("#0A1230", "#25325E")}[tod]
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2600, 900), fill(shader=lin((0, 0), (0, 900), list(sky))))
    rnd = random.Random(5)
    if tod == "day":
        c.drawCircle(1950, 170, 70, fill("#FFF6C8"))
        c.drawCircle(1950, 170, 140, fill("#FFF6C8", 0.35, blur=30))
        for cx, cy, s in ((300, 160, 1.0), (900, 110, 0.8), (1500, 200, 1.2), (2200, 120, 0.9)):
            cx += t * 6 * s
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                c.drawCircle(cx + dx * s, cy + dy * s, r * s, fill("#FFFFFF", 0.92))
    else:
        for i in range(140):
            x, y = rnd.uniform(-100, 2500), rnd.uniform(-50, 600)
            tw = 0.5 + 0.5 * math.sin(t * 2 + i)
            c.drawCircle(x, y, rnd.uniform(1, 2.6), fill("#FFFFFF", (0.3 + 0.5 * tw) * (1 if tod == "night" else 0.35)))
        if tod == "night":
            c.drawCircle(400, 160, 60, fill("#FFF4D2"))
            c.drawCircle(425, 145, 55, fill(sky[0]))
            c.drawCircle(400, 160, 150, fill("#FFF4D2", 0.15, blur=40))
    # 远山和树
    hill = {"day": "#9CCB9A", "dawn": "#4A4F78", "night": "#1A2446"}[tod]
    hill2 = {"day": "#7FB884", "dawn": "#3B4068", "night": "#141C3A"}[tod]
    c.drawPath(spline([(-200, 900), (-200, 640), (300, 560), (800, 620), (1300, 540), (1900, 600), (2600, 560),
                       (2600, 900)], tension=0.8), fill(hill))
    for i in range(18):
        x = -100 + i * 150 + rnd.uniform(-30, 30)
        h = rnd.uniform(120, 220)
        c.drawPath(spline([(x - 60, 760), (x - 50, 760 - h * 0.6), (x, 760 - h), (x + 50, 760 - h * 0.6),
                           (x + 60, 760)]), fill(hill2))
    # 邻居的房子（左右两边）
    for hx, hw, hh, roof in ((-150, 600, 360, "#8C5A4A"), (2050, 520, 330, "#5A6E8C")):
        wall = {"day": "#E8D7C0", "dawn": "#8A7F94", "night": "#3A3A55"}[tod]
        c.drawRect(skia.Rect.MakeXYWH(hx, 900 - hh, hw, hh), fill(wall))
        c.drawPath(poly([(hx - 30, 900 - hh), (hx + hw / 2, 900 - hh - 140), (hx + hw + 30, 900 - hh)]),
                   fill(shade(roof, -0.3 if tod != "day" else 0)))
        for k in range(2):
            wx = hx + 90 + k * (hw - 260)
            lit = neighbors > (0.3 + k * 0.3) if tod != "day" else False
            col = "#FFD98A" if lit else {"day": "#9CC6E0", "dawn": "#3B4766", "night": "#1E2540"}[tod]
            c.drawRect(skia.Rect.MakeXYWH(wx, 900 - hh + 90, 90, 110), fill(col))
            c.drawRect(skia.Rect.MakeXYWH(wx, 900 - hh + 90, 90, 110), stroke(LINE, 5))
            if lit:
                c.drawRect(skia.Rect.MakeXYWH(wx - 30, 900 - hh + 60, 150, 170), fill("#FFD98A", 0.35, blur=25))
    hotel(c, tod, t)
    # 人行道和马路
    c.drawRect(skia.Rect.MakeLTRB(-200, 900, 2600, 965), fill({"day": "#CFC8BE", "dawn": "#7D7A86", "night": "#3A3B4C"}[tod]))
    for x in range(-200, 2600, 120):
        c.drawLine(x, 900, x, 965, stroke("#000000", 2, 0.12))
    c.drawRect(skia.Rect.MakeLTRB(-200, 965, 2600, 1300), fill({"day": "#5E6470", "dawn": "#3A3D4E", "night": "#1C1E2A"}[tod]))
    for x in range(-200, 2600, 220):
        c.drawRect(skia.Rect.MakeXYWH(x, 1030, 110, 10), fill("#F2E6B8", 0.7))
    # 路灯
    c.drawRect(skia.Rect.MakeXYWH(292, 520, 16, 380), fill("#3C4150"))
    c.drawPath(spline([(300, 525), (330, 490), (380, 490)], closed=False), stroke("#3C4150", 12))
    c.drawPath(oval(385, 500, 34, 14), fill("#3C4150"))
    if tod != "day":
        c.drawPath(oval(385, 512, 22, 8), fill("#FFE7A8"))


def hotel(c, tod, t):
    x0, x1, top, ground = 700, 1900, 250, 900
    wall = {"day": "#F6E7CC", "dawn": "#9C8C9A", "night": "#4A4560"}[tod]
    wall_d = shade(wall, -0.15)
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, ground), fill(shader=lin((0, top), (0, ground), [wall, wall_d])))
    # 木质腰线
    c.drawRect(skia.Rect.MakeLTRB(x0, 720, x1, ground), fill(shade("#B98A5E", -0.0 if tod == "day" else -0.45)))
    c.drawLine(x0, 720, x1, 720, stroke(LINE, 6))
    # 屋顶
    roof = {"day": "#3E4A6B", "dawn": "#2C3350", "night": "#1E2238"}[tod]
    c.drawPath(poly([(x0 - 60, top + 10), (x0 + 60, top - 110), (x1 - 60, top - 110), (x1 + 60, top + 10)]),
               fill(roof))
    c.drawPath(poly([(x0 - 60, top + 10), (x0 + 60, top - 110), (x1 - 60, top - 110), (x1 + 60, top + 10)]),
               stroke(LINE, 6))
    c.drawRect(skia.Rect.MakeLTRB(x0 - 70, top + 5, x1 + 70, top + 30), fill(shade(roof, 0.15)))
    # 招牌
    sx, sy, sw, sh = 1050, 300, 500, 130
    c.drawPath(rrect(sx, sy, sw, sh, 24), fill("#22305A"))
    c.drawPath(rrect(sx, sy, sw, sh, 24), stroke("#E9C46A", 7))
    c.drawCircle(sx + 70, sy + 65, 42, fill("#FFE08A"))
    c.drawCircle(sx + 88, sy + 52, 38, fill("#22305A"))
    paw(c, sx + 440, sy + 70, 26, "#FFE08A")
    draw_text(c, "月光宠物旅馆", sx + 265, sy + 88, size=58, name="kuaile", color="#FFF1C9")
    if tod != "day":
        c.drawPath(rrect(sx - 20, sy - 20, sw + 40, sh + 40, 40), fill("#FFE08A", 0.12, blur=25))
    # 窗户（两层）
    lit = tod != "day"
    for wx in (760, 900, 1640, 1780):
        for wy in (330, 520):
            if 1000 < wx < 1600 and wy == 330:
                continue
            col = "#FFD98A" if lit else "#A7D3EE"
            c.drawPath(rrect(wx, wy, 100, 130, 10), fill(col))
            if not lit:
                c.drawPath(poly([(wx + 20, wy + 10), (wx + 50, wy + 10), (wx + 15, wy + 70), (wx + 5, wy + 70)]),
                           fill("#FFFFFF", 0.5))
            c.drawPath(rrect(wx, wy, 100, 130, 10), stroke(LINE, 6))
            c.drawLine(wx + 50, wy, wx + 50, wy + 130, stroke(LINE, 4))
            # 遮阳棚
            for k in range(5):
                col2 = "#3E7CC0" if k % 2 == 0 else "#F5F5F5"
                c.drawPath(poly([(wx - 10 + k * 24, wy - 10), (wx + 14 + k * 24, wy - 10), (wx + 14 + k * 24, wy + 15),
                                 (wx - 10 + k * 24, wy + 15)]), fill(shade(col2, 0 if tod == "day" else -0.5)))
            c.drawLine(wx - 10, wy + 15, wx + 110, wy + 15, stroke(LINE, 4))
    # 大门（玻璃）
    dx, dw, dh = 1170, 260, 330
    c.drawPath(rrect(dx - 20, ground - dh - 20, dw + 40, dh + 20, 14), fill("#7A5235"))
    inside = "#FFE3A8" if lit else "#BFE3F5"
    c.drawRect(skia.Rect.MakeXYWH(dx, ground - dh, dw, dh), fill(shader=lin((0, ground - dh), (0, ground),
                                                                          [inside, shade(inside, -0.2)])))
    c.drawLine(dx + dw / 2, ground - dh, dx + dw / 2, ground, stroke(LINE, 6))
    for k in (0, 1):
        c.drawPath(poly([(dx + 20 + k * 130, ground - dh + 20), (dx + 60 + k * 130, ground - dh + 20),
                         (dx + 25 + k * 130, ground - 120), (dx + 10 + k * 130, ground - 120)]), fill("#FFFFFF", 0.35))
    c.drawRect(skia.Rect.MakeXYWH(dx, ground - dh, dw, dh), stroke(LINE, 6))
    c.drawRect(skia.Rect.MakeXYWH(dx + dw / 2 - 30, ground - 190, 10, 60), fill("#D9B26A"))
    c.drawRect(skia.Rect.MakeXYWH(dx + dw / 2 + 20, ground - 190, 10, 60), fill("#D9B26A"))
    # 门口地垫和盆栽
    c.drawPath(rrect(dx + 20, ground - 6, dw - 40, 22, 8), fill("#A0523A"))
    paw(c, dx + dw / 2, ground + 4, 9, "#F2D7A0")
    for px in (dx - 90, dx + dw + 40):
        c.drawPath(poly([(px, ground - 90), (px + 60, ground - 90), (px + 50, ground), (px + 10, ground)]),
                   fill("#C8673E"))
        for k in range(6):
            ang = -150 + k * 25
            r = math.radians(ang)
            c.drawPath(oval(px + 30 + math.cos(r) * 45, ground - 120 + math.sin(r) * 40, 26, 40),
                       fill(shade("#5DAA5C", -0.0 if tod == "day" else -0.55)))
    c.drawRect(skia.Rect.MakeLTRB(x0, top, x1, ground), stroke(LINE, 6))


# ================================================================ 大堂
def lobby(c, tod="day", t=0.0, door_broken=0.0, photo_ribbon=False, bowl=False):
    """世界宽 2200。左边玻璃大门，中间前台，墙上有猫的照片，右边通往客房走廊。"""
    # 墙
    c.drawRect(skia.Rect.MakeLTRB(-500, -100, 2700, 640), fill(shader=lin((0, 0), (0, 640), ["#CFE6DD", "#B5D6CB"])))
    for i in range(-420, 2700, 140):
        for j in range(40, 640, 140):
            paw(c, i + (70 if (j // 140) % 2 else 0), j, 9, "#FFFFFF", 0.22, ang=15)
    # 护墙板
    c.drawRect(skia.Rect.MakeLTRB(-500, 640, 2700, 870), fill(shader=lin((0, 640), (0, 870), ["#B98A5E", "#9C6E47"])))
    for x in range(-500, 2700, 110):
        c.drawLine(x, 660, x, 860, stroke("#7E5534", 3, 0.6))
    c.drawRect(skia.Rect.MakeLTRB(-500, 628, 2700, 646), fill("#8A5C38"))
    # 地板
    c.drawRect(skia.Rect.MakeLTRB(-500, 870, 2700, 1300), fill(shader=lin((0, 870), (0, 1080), ["#C99B6B", "#A9784C"])))
    for k, y in enumerate(range(870, 1300, 52)):
        c.drawLine(-500, y, 2700, y, stroke("#8A5C38", 3, 0.55))
        off = (k % 2) * 160
        for x in range(-500 + off, 2700, 320):
            c.drawLine(x, y, x, y + 52, stroke("#8A5C38", 3, 0.45))
    c.drawRect(skia.Rect.MakeLTRB(-500, 862, 2700, 878), fill("#6E4528"))
    # 玻璃大门
    outside = {"day": ["#BFE6FA", "#E8F6FF"], "dawn": ["#425186", "#E9A985"], "night": ["#0F1734", "#24305A"],
               "morning": ["#FFE8B8", "#FFF7E2"]}[tod]
    gx, gy, gw, gh = 120, 300, 340, 570
    c.drawPath(rrect(gx - 26, gy - 26, gw + 52, gh + 26, 10), fill("#7A5235"))
    c.drawRect(skia.Rect.MakeXYWH(gx, gy, gw, gh), fill(shader=lin((0, gy), (0, gy + gh), outside)))
    # 门外的灌木
    bush = {"day": "#6DB46A", "dawn": "#2E3656", "night": "#121A30", "morning": "#7CBF6C"}[tod]
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(gx, gy, gw, gh))
    for k in range(6):
        c.drawCircle(gx + k * 70, gy + gh - 60, 70, fill(bush))
    c.restore()
    if door_broken < 0.5:
        c.drawLine(gx + gw / 2, gy, gx + gw / 2, gy + gh, stroke(LINE, 7))
        for k in (0, 1):
            c.drawPath(poly([(gx + 25 + k * 170, gy + 30), (gx + 70 + k * 170, gy + 30), (gx + 30 + k * 170, gy + 300),
                             (gx + 12 + k * 170, gy + 300)]), fill("#FFFFFF", 0.3))
        draw_text(c, "推", gx + gw / 2 - 45, gy + 290, size=36, name="kuaile", color="#FFFFFF", a=0.7)
        draw_text(c, "拉", gx + gw / 2 + 45, gy + 290, size=36, name="kuaile", color="#FFFFFF", a=0.7)
    else:
        # 碎玻璃
        rnd = random.Random(3)
        cx, cy = gx + gw / 2, gy + gh * 0.55
        for k in range(14):
            ang = k / 14 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
            r = rnd.uniform(140, 300)
            c.drawLine(cx, cy, cx + math.cos(ang) * r, cy + math.sin(ang) * r, stroke("#FFFFFF", 3, 0.7))
        for k in range(3):
            c.drawCircle(cx, cy, 50 + k * 60, stroke("#FFFFFF", 2, 0.5))
    c.drawRect(skia.Rect.MakeXYWH(gx, gy, gw, gh), stroke(LINE, 7))
    # 天花板吊灯
    for lx in (700, 1300, 1900):
        c.drawLine(lx, -100, lx, 120, stroke("#3A2A20", 4))
        c.drawPath(poly([(lx - 70, 175), (lx - 35, 115), (lx + 35, 115), (lx + 70, 175)]), fill("#E8B04A"))
        c.drawPath(oval(lx, 175, 70, 12), fill("#FFF3C4"))
    # 墙上的照片（大橘）
    photo(c, 1220, 260, 1.0, ribbon=photo_ribbon)
    # 钟
    clock(c, 1650, 270, 70, t)
    # 钥匙板
    c.drawPath(rrect(1450, 220, 140, 110, 10), fill("#8A5C38"))
    for k in range(5):
        kx = 1470 + k * 25
        c.drawCircle(kx, 245, 5, fill("#D9B26A"))
        c.drawLine(kx, 245, kx, 290, stroke("#D9B26A", 3))
        draw_text(c, str(k + 1), kx, 315, size=16, name="sans", color="#FFF1C9")
    # 前台
    dx0, dx1, dtop = 880, 1560, 640
    c.drawPath(rrect(dx0 - 20, dtop - 30, dx1 - dx0 + 40, 40, 10), fill("#7A4E2E"))
    c.drawRect(skia.Rect.MakeLTRB(dx0, dtop + 10, dx1, 880), fill(shader=lin((0, dtop), (0, 880), ["#C78B57", "#A26A3D"])))
    for x in range(dx0 + 40, dx1, 90):
        c.drawLine(x, dtop + 30, x, 870, stroke("#8A5A33", 3, 0.6))
    c.drawPath(rrect(dx0 + 230, dtop + 70, 220, 120, 14), fill("#22305A"))
    c.drawCircle(dx0 + 285, dtop + 130, 32, fill("#FFE08A"))
    c.drawCircle(dx0 + 300, dtop + 120, 29, fill("#22305A"))
    draw_text(c, "前台", dx0 + 375, dtop + 145, size=40, name="kuaile", color="#FFF1C9")
    c.drawRect(skia.Rect.MakeLTRB(dx0, dtop + 10, dx1, 880), stroke(LINE, 5))
    # 台面上的东西：铃、登记簿、笔筒
    c.drawPath(oval(dx0 + 90, dtop - 32, 40, 10), fill("#8A6A2A"))
    c.drawPath(spline([(dx0 + 55, dtop - 34), (dx0 + 90, dtop - 75), (dx0 + 125, dtop - 34)]), fill("#E9C46A"))
    c.drawCircle(dx0 + 90, dtop - 78, 6, fill("#E9C46A"))
    book = poly([(dx0 + 440, dtop - 34), (dx0 + 560, dtop - 50), (dx0 + 680, dtop - 34), (dx0 + 680, dtop - 28),
                 (dx0 + 440, dtop - 28)])
    c.drawPath(book, fill("#FFFBF0"))
    c.drawPath(book, stroke(LINE, 3))
    c.drawLine(dx0 + 560, dtop - 50, dx0 + 560, dtop - 30, stroke(LINE, 2))
    c.drawPath(rrect(dx0 + 610, dtop - 95, 40, 62, 8), fill("#5A8DB8"))
    for k in range(3):
        c.drawLine(dx0 + 620 + k * 10, dtop - 95, dx0 + 615 + k * 12, dtop - 130, stroke(["#E23A3A", "#2C5AA0", "#2F9A3A"][k], 5))
    # 鹦鹉架（笼子在 draw_cage 里单独画）
    c.drawRect(skia.Rect.MakeXYWH(632, 520, 16, 350), fill("#5A4030"))
    c.drawPath(oval(640, 868, 70, 14), fill("#5A4030"))
    # 通往走廊的拱门
    ax, aw = 1820, 300
    c.drawPath(spline([(ax, 870), (ax, 330), (ax + aw / 2, 230), (ax + aw, 330), (ax + aw, 870)], closed=False),
               fill("#2A2030"))
    c.drawPath(spline([(ax, 870), (ax, 330), (ax + aw / 2, 230), (ax + aw, 330), (ax + aw, 870)], closed=False),
               stroke("#7A5235", 22))
    c.drawPath(rrect(ax + 40, 170, 220, 56, 12), fill("#22305A"))
    draw_text(c, "客房", ax + 120, 210, size=34, name="kuaile", color="#FFF1C9")
    c.drawPath(poly([(ax + 178, 190), (ax + 210, 190), (ax + 210, 180), (ax + 232, 198), (ax + 210, 216),
                     (ax + 210, 206), (ax + 178, 206)]), fill("#FFF1C9"))
    # 盆栽
    px = 1680
    c.drawPath(poly([(px, 790), (px + 110, 790), (px + 95, 880), (px + 15, 880)]), fill("#C8673E"))
    for k in range(7):
        ang = math.radians(-160 + k * 23)
        c.drawPath(oval(px + 55 + math.cos(ang) * 70, 720 + math.sin(ang) * 80, 34, 60), fill("#4E9A55"))
    if bowl:
        c.drawPath(oval(1220, 440, 40, 10), fill("#E9C46A"))


def photo(c, x, y, s, ribbon=False, plaque_text=False):
    """大橘的照片：相框 + 猫 + 铭牌。"""
    from chars import Pose, draw_critter
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(rrect(-110, -130, 220, 260, 8), fill("#8A5C38"))
    c.drawPath(rrect(-95, -115, 190, 230, 4), fill(shader=lin((0, -115), (0, 115), ["#F7E3C3", "#E3C49A"])))
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(-95, -115, 190, 230))
    draw_critter(c, "cat", 0, 205, 70, Pose(eye="happy", mouth="cat", t=0.0, blush=0.3))
    c.restore()
    c.drawPath(rrect(-110, -130, 220, 260, 8), stroke(LINE, 5))
    c.drawPath(rrect(-60, 140, 120, 34, 5), fill("#D9B26A"))
    c.drawPath(rrect(-60, 140, 120, 34, 5), stroke("#8A6A2A", 3))
    draw_text(c, "大橘", 0, 166, size=22, name="kuaile", color="#4A3210")
    if ribbon:
        c.drawPath(poly([(-110, -60), (-40, -130), (-10, -130), (-110, -30)]), fill("#1A1A1A"))
        c.drawPath(poly([(110, -60), (40, -130), (10, -130), (110, -30)]), fill("#1A1A1A"))
    c.restore()


def clock(c, x, y, r, t, hour=None, minute=None):
    c.drawCircle(x, y, r + 10, fill("#8A5C38"))
    c.drawCircle(x, y, r, fill("#FFF8E8"))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        c.drawLine(x + math.sin(a) * r * 0.8, y - math.cos(a) * r * 0.8, x + math.sin(a) * r * 0.92,
                   y - math.cos(a) * r * 0.92, stroke(LINE, 4 if k % 3 == 0 else 2))
    if hour is None:
        hour, minute = 4.0, t * 2
    ma = (minute / 60) * 2 * math.pi
    ha = ((hour % 12) / 12 + minute / 720) * 2 * math.pi
    c.drawLine(x, y, x + math.sin(ha) * r * 0.5, y - math.cos(ha) * r * 0.5, stroke(LINE, 7))
    c.drawLine(x, y, x + math.sin(ma) * r * 0.75, y - math.cos(ma) * r * 0.75, stroke(LINE, 4))
    c.drawCircle(x, y, 6, fill(LINE))
    c.drawCircle(x, y, r + 10, stroke(LINE, 4))


def draw_cage(c, x, y, front=True, door_open=0.0):
    """鹦鹉笼。front=False 只画后面的栏杆（先画），front=True 画前面的栏杆和顶。"""
    w, h = 170, 230
    if not front:
        c.drawPath(oval(x, y, w / 2, 16), fill("#C9A35A"))
        return
    for k in range(9):
        bx = x - w / 2 + k * w / 8
        c.drawLine(bx, y, bx, y - h + 40 - 30 * math.sin(k / 8 * math.pi), stroke("#C9A35A", 4))
    c.drawPath(spline([(x - w / 2, y - h + 40), (x, y - h - 20), (x + w / 2, y - h + 40)], closed=False),
               stroke("#C9A35A", 6))
    c.drawCircle(x, y - h - 30, 12, stroke("#C9A35A", 5))
    c.drawLine(x - w / 2, y, x + w / 2, y, stroke("#A8823A", 8))
    c.drawLine(x - w / 2, y - h + 40, x + w / 2, y - h + 40, stroke("#C9A35A", 4))
    c.drawLine(x - 40, y - 60, x + 40, y - 60, stroke("#8A6A2A", 6))


# ================================================================ 走廊
DOOR_X = {1: 700, 2: 1500, 3: 2300, 4: 3100, 5: 3900, "groom": 4700}
FLOOR_Y = 860


def corridor(c, t=0.0, night=False, flaps=None):
    """世界宽 5600。左边接大堂，右边尽头是美容室。flaps: {房号: 摆动量}。"""
    flaps = flaps or {}
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 5800, 600), fill(shader=lin((0, 0), (0, 600), ["#F1E2C6", "#E6D1AF"])))
    for x in range(-200, 5800, 60):
        c.drawLine(x, 60, x, 600, stroke("#D8C09A", 6, 0.35))
    c.drawRect(skia.Rect.MakeLTRB(-200, 600, 5800, FLOOR_Y), fill(shader=lin((0, 600), (0, FLOOR_Y), ["#A87650", "#8E5F3D"])))
    for x in range(-200, 5800, 120):
        c.drawRect(skia.Rect.MakeXYWH(x + 14, 625, 92, 210), stroke("#7A4E30", 3, 0.6))
    c.drawRect(skia.Rect.MakeLTRB(-200, 590, 5800, 606), fill("#7A4E30"))
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 5800, 40), fill("#E0CBA8"))
    c.drawRect(skia.Rect.MakeLTRB(-200, 36, 5800, 48), fill("#B08A60"))
    # 地板
    c.drawRect(skia.Rect.MakeLTRB(-200, FLOOR_Y, 5800, 1300), fill(shader=lin((0, FLOOR_Y), (0, 1080), ["#C2915F", "#9E6E43"])))
    for k, y in enumerate(range(FLOOR_Y, 1300, 50)):
        c.drawLine(-200, y, 5800, y, stroke("#7E5230", 3, 0.5))
        off = (k % 2) * 170
        for x in range(-200 + off, 5800, 340):
            c.drawLine(x, y, x, y + 50, stroke("#7E5230", 3, 0.4))
    c.drawRect(skia.Rect.MakeLTRB(-200, FLOOR_Y - 10, 5800, FLOOR_Y + 6), fill("#5E3A20"))
    # 左端：通往大堂的拱门
    c.drawPath(spline([(-60, FLOOR_Y), (-60, 330), (90, 240), (240, 330), (240, FLOOR_Y)], closed=False),
               fill("#FFE3A8" if not night else "#3A3040"))
    c.drawPath(spline([(-60, FLOOR_Y), (-60, 330), (90, 240), (240, 330), (240, FLOOR_Y)], closed=False),
               stroke("#7A5235", 22))
    # 安全出口灯
    c.drawPath(rrect(330, 120, 150, 54, 6), fill("#1E9E55"))
    draw_text(c, "安全出口", 405, 158, size=28, name="sans", weight=700, color="#FFFFFF")
    # 吊灯
    for lx in range(500, 5600, 800):
        c.drawLine(lx, 40, lx, 90, stroke(LINE, 4))
        c.drawPath(poly([(lx - 55, 135), (lx - 28, 88), (lx + 28, 88), (lx + 55, 135)]), fill("#E8B04A"))
        c.drawPath(oval(lx, 135, 55, 10), fill("#FFF3C4" if not night else "#C9B07A"))
    # 门之间的装饰画
    deco = [(1100, "bone"), (1900, "paw"), (2700, "ball"), (3500, "bone"), (4300, "paw")]
    for dx, kind in deco:
        c.drawPath(rrect(dx - 80, 250, 160, 120, 6), fill("#8A5C38"))
        c.drawPath(rrect(dx - 68, 262, 136, 96, 3), fill("#F8EBD3"))
        if kind == "bone":
            c.drawPath(rrect(dx - 40, 302, 80, 18, 9), fill("#E8D3B0"))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    c.drawCircle(dx + sx * 42, 311 + sy * 9, 12, fill("#E8D3B0"))
        elif kind == "paw":
            paw(c, dx, 315, 22, "#E39B4D")
        else:
            c.drawCircle(dx, 310, 32, fill("#E2574C"))
            c.drawPath(spline([(dx - 30, 300), (dx, 312), (dx + 30, 300)], closed=False), stroke("#FFFFFF", 5))
    # 灭火器
    c.drawPath(rrect(4380, 700, 50, 130, 20), fill("#D8322B"))
    c.drawRect(skia.Rect.MakeXYWH(4392, 680, 26, 24), fill("#333"))
    for n in (1, 2, 3, 4, 5):
        door(c, DOOR_X[n], str(n), flap=flaps.get(n, 0.0), night=night)
    # 美容室的门
    gx = DOOR_X["groom"]
    door(c, gx, None, flap=None, night=night, glass=True)
    c.drawPath(rrect(gx - 110, 360, 220, 60, 10), fill("#2F7FA8"))
    draw_text(c, "美容室", gx, 402, size=36, name="kuaile", color="#FFFFFF")
    # 尽头的墙
    c.drawRect(skia.Rect.MakeLTRB(5300, -200, 5800, 1300), fill("#000000", 0.18))


def door(c, x, num, flap=0.0, night=False, glass=False, window_content=None):
    w, h = 270, 440
    top = FLOOR_Y - h
    c.drawPath(rrect(x - w / 2 - 18, top - 18, w + 36, h + 18, 8), fill("#6E4528"))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, top, w, h), fill(shader=lin((x - w / 2, 0), (x + w / 2, 0), ["#B57E50", "#A06B40"])))
    c.drawPath(rrect(x - w / 2 + 28, top + 170, w - 56, 140, 8), stroke("#8A5A33", 5))
    # 小窗
    wx, wy, ww, wh = x - 65, top + 40, 130, 100
    c.drawPath(rrect(wx - 8, wy - 8, ww + 16, wh + 16, 8), fill("#6E4528"))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), fill("#1B2238" if night else "#3B4A66"))
    c.drawPath(poly([(wx + 15, wy + 8), (wx + 45, wy + 8), (wx + 20, wy + wh - 8), (wx + 8, wy + wh - 8)]),
               fill("#FFFFFF", 0.18))
    # 门把手
    c.drawCircle(x + w / 2 - 40, top + 250, 14, fill("#D9B26A"))
    c.drawCircle(x + w / 2 - 40, top + 250, 14, stroke(LINE, 3))
    if num is not None:
        c.drawCircle(x, top - 52, 30, fill("#22305A"))
        c.drawCircle(x, top - 52, 30, stroke("#E9C46A", 4))
        draw_text(c, num, x, top - 39, size=36, name="kuaile", color="#FFF1C9")
    if flap is not None:
        fx, fw, fh = x - 60, 120, 110
        fy = FLOOR_Y - fh - 4
        c.drawPath(rrect(fx - 8, fy - 8, fw + 16, fh + 12, 14), fill("#5E3A20"))
        sq = 1.0 - min(abs(flap), 1.0) * 0.85
        c.save()
        c.translate(0, fy)
        c.scale(1, max(sq, 0.12) * (1 if flap >= 0 else -1))
        c.drawPath(rrect(fx, 0, fw, fh, 10), fill("#3B2A22" if flap == 0 else "#2A1E18"))
        c.drawPath(rrect(fx, 0, fw, fh, 10), stroke("#1E140E", 3))
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(fx, fy - 6, fw, 8), fill("#888"))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, top, w, h), stroke(LINE, 5))


# ================================================================ Cheems 的房间
ROOM = dict(door_x=1330, door_top=330, win=(1240, 380, 180, 120), flap=(1270, 752, 120, 106), vent=(230, 170, 220, 120),
            bed=(430, 850), bowl=(860, 868))


def room(c, t=0.0, flap=0.0, vent_open=0.0, bowl_full=False):
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 860), fill(shader=lin((0, 0), (0, 860), ["#C9D9EA", "#AFC3DA"])))
    rnd = random.Random(11)
    for i in range(70):
        x, y = rnd.uniform(-100, 2100), rnd.uniform(0, 640)
        s = rnd.uniform(5, 10)
        _star(c, x, y, s, "#FFFFFF", 0.35)
    c.drawRect(skia.Rect.MakeLTRB(-200, 640, 2200, 860), fill(shader=lin((0, 640), (0, 860), ["#8FA6C4", "#7A92B2"])))
    c.drawRect(skia.Rect.MakeLTRB(-200, 630, 2200, 646), fill("#5E7698"))
    # 地板
    c.drawRect(skia.Rect.MakeLTRB(-200, 860, 2200, 1300), fill(shader=lin((0, 860), (0, 1080), ["#C79A6A", "#A6774B"])))
    for k, y in enumerate(range(860, 1300, 48)):
        c.drawLine(-200, y, 2200, y, stroke("#86592F", 3, 0.5))
        off = (k % 2) * 150
        for x in range(-200 + off, 2200, 300):
            c.drawLine(x, y, x, y + 48, stroke("#86592F", 3, 0.4))
    c.drawRect(skia.Rect.MakeLTRB(-200, 852, 2200, 866), fill("#5E3A20"))
    # 地毯
    c.drawPath(oval(820, 960, 420, 80), fill("#D9837A"))
    c.drawPath(oval(820, 960, 380, 64), stroke("#F2C9A0", 6))
    # 门
    d = ROOM
    dx, top = d["door_x"], d["door_top"]
    w = 340
    c.drawPath(rrect(dx - w / 2 - 22, top - 22, w + 44, 860 - top + 22, 8), fill("#6E4528"))
    c.drawRect(skia.Rect.MakeLTRB(dx - w / 2, top, dx + w / 2, 860), fill(shader=lin((dx - w / 2, 0), (dx + w / 2, 0), ["#B57E50", "#A06B40"])))
    c.drawPath(rrect(dx - w / 2 + 34, top + 220, w - 68, 170, 8), stroke("#8A5A33", 5))
    c.drawCircle(dx - w / 2 + 40, top + 300, 16, fill("#D9B26A"))
    c.drawCircle(dx - w / 2 + 40, top + 300, 16, stroke(LINE, 3))
    wx, wy, ww, wh = d["win"]
    c.drawPath(rrect(wx - 10, wy - 10, ww + 20, wh + 20, 8), fill("#6E4528"))
    # 狗洞
    fx, fy, fw, fh = d["flap"]
    c.drawPath(rrect(fx - 10, fy - 10, fw + 20, fh + 14, 14), fill("#5E3A20"))
    c.drawRect(skia.Rect.MakeLTRB(dx - w / 2, top, dx + w / 2, 860), stroke(LINE, 5))
    # 通风口
    vx, vy, vw, vh = d["vent"]
    c.drawPath(rrect(vx - 12, vy - 12, vw + 24, vh + 24, 10), fill("#8E9BB0"))
    c.drawPath(rrect(vx, vy, vw, vh, 6), fill("#1A1F2C"))
    if vent_open < 0.5:
        for k in range(6):
            yy = vy + 12 + k * (vh - 20) / 5
            c.drawPath(rrect(vx + 8, yy - 6, vw - 16, 12, 6), fill("#B9C4D4"))
    for (sx, sy) in ((vx - 2, vy - 2), (vx + vw + 2, vy - 2), (vx - 2, vy + vh + 2), (vx + vw + 2, vy + vh + 2)):
        c.drawCircle(sx, sy, 5, fill("#5A6478"))
    # 钟
    clock(c, 820, 230, 64, t, hour=None)
    # 骨头画
    c.drawPath(rrect(1580, 220, 200, 150, 6), fill("#8A5C38"))
    c.drawPath(rrect(1594, 234, 172, 122, 3), fill("#F8EBD3"))
    paw(c, 1680, 300, 30, "#E39B4D")
    # 墙上的小夜灯（月亮）
    c.drawPath(rrect(560, 560, 70, 70, 14), fill("#E8E2D0"))
    c.drawCircle(595, 595, 22, fill("#FFE9A0"))
    c.drawCircle(605, 588, 20, fill("#E8E2D0"))
    # 窝和毯子
    bx, by = d["bed"]
    c.drawPath(oval(bx, by + 10, 260, 80), fill("#000", 0.25, blur=10))
    c.drawPath(oval(bx, by - 5, 250, 85), fill("#6A8FC9"))
    c.drawPath(oval(bx, by - 5, 250, 85), stroke(LINE, 5))
    c.drawPath(oval(bx, by - 20, 195, 52), fill("#E9EEF8"))
    c.drawPath(oval(bx, by - 20, 195, 52), stroke("#9DB0D0", 4))
    # 枕头
    c.drawPath(rrect(bx + 70, by - 70, 130, 60, 26), fill("#F7F1E6"))
    c.drawPath(rrect(bx + 70, by - 70, 130, 60, 26), stroke(LINE, 4))
    # 饭碗
    bwx, bwy = d["bowl"]
    bowl(c, bwx, bwy, full=bowl_full)


def bowl(c, x, y, full=False, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(oval(0, 8, 95, 16), fill("#000", 0.25, blur=6))
    p = spline([(-90, -40), (90, -40), (70, 6), (-70, 6)], tension=0.5)
    draw_shape(c, p, "#E2574C", LINE, 4, "#B8433A", (-6, -6))
    c.drawPath(oval(0, -40, 90, 16), fill("#8F2F28"))
    if full:
        rnd = random.Random(2)
        for k in range(26):
            c.drawCircle(rnd.uniform(-70, 70), -44 + rnd.uniform(-8, 6), rnd.uniform(7, 10), fill("#A0612E"))
            c.drawCircle(rnd.uniform(-70, 70), -44 + rnd.uniform(-8, 6), 4, fill("#C88A4A"))
    c.drawPath(oval(0, -40, 90, 16), stroke(LINE, 4))
    paw(c, 0, -14, 9, "#FFFFFF", 0.8)
    c.restore()


def _star(c, x, y, s, color, a):
    pts = []
    for k in range(10):
        ang = k / 10 * 2 * math.pi - math.pi / 2
        r = s if k % 2 == 0 else s * 0.45
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
    c.drawPath(poly(pts), fill(color, a))


# ================================================================ 美容室
GROOM = dict(mirror=(620, 170, 680, 470), lamp=(960, 660))


def grooming(c, t=0.0, lamp_on=True, lamp_fallen=0.0):
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 870), fill("#DDEAF0"))
    for x in range(-200, 2200, 80):
        c.drawLine(x, -200, x, 870, stroke("#BFD2DC", 3))
    for y in range(-200, 870, 80):
        c.drawLine(-200, y, 2200, y, stroke("#BFD2DC", 3))
    c.drawRect(skia.Rect.MakeLTRB(-200, 870, 2200, 1300), fill(shader=lin((0, 870), (0, 1080), ["#9FB3BF", "#7F95A3"])))
    for x in range(-200, 2200, 120):
        c.drawLine(x, 870, x - 60, 1300, stroke("#6E8291", 3, 0.6))
    c.drawRect(skia.Rect.MakeLTRB(-200, 862, 2200, 876), fill("#5E7180"))
    mx, my, mw, mh = GROOM["mirror"]
    c.drawPath(rrect(mx - 26, my - 26, mw + 52, mh + 52, 18), fill("#B9C4CE"))
    c.drawPath(rrect(mx - 26, my - 26, mw + 52, mh + 52, 18), stroke(LINE, 5))
    # 洗手台
    c.drawPath(rrect(mx - 60, 680, mw + 120, 36, 10), fill("#F4F7F9"))
    c.drawPath(rrect(mx - 60, 680, mw + 120, 36, 10), stroke(LINE, 4))
    c.drawRect(skia.Rect.MakeLTRB(mx - 40, 716, mx + mw + 40, 870), fill("#C8D3DB"))
    c.drawRect(skia.Rect.MakeLTRB(mx - 40, 716, mx + mw + 40, 870), stroke(LINE, 4))
    for k in range(3):
        c.drawLine(mx - 40 + (k + 1) * (mw + 80) / 4, 716, mx - 40 + (k + 1) * (mw + 80) / 4, 870, stroke(LINE, 3))
        c.drawCircle(mx - 40 + (k + 0.5) * (mw + 80) / 4 + 50, 790, 7, fill("#8A99A6"))
    # 浴缸
    c.drawPath(spline([(80, 660), (580, 660), (560, 820), (100, 820)], tension=0.4), fill("#FFFFFF"))
    c.drawPath(spline([(80, 660), (580, 660), (560, 820), (100, 820)], tension=0.4), stroke(LINE, 5))
    c.drawPath(rrect(60, 640, 540, 34, 16), fill("#F4F7F9"))
    c.drawPath(rrect(60, 640, 540, 34, 16), stroke(LINE, 5))
    for lx in (130, 520):
        c.drawPath(oval(lx, 845, 22, 30), fill("#D9B26A"))
    c.drawPath(spline([(520, 640), (520, 560), (470, 540), (450, 570)], closed=False), stroke("#9AA8B4", 10))
    # 美容台
    c.drawPath(rrect(1420, 600, 380, 34, 8), fill("#5A6E82"))
    c.drawRect(skia.Rect.MakeXYWH(1590, 634, 30, 230), fill("#7A8A98"))
    c.drawPath(oval(1605, 866, 110, 16), fill("#5A6E82"))
    c.drawLine(1760, 600, 1760, 380, stroke("#7A8A98", 10))
    c.drawPath(spline([(1760, 385), (1700, 400), (1660, 440)], closed=False), stroke("#7A8A98", 10))
    # 架子和瓶子
    c.drawRect(skia.Rect.MakeXYWH(1420, 260, 380, 18), fill("#B08A60"))
    for k, col in enumerate(("#F2A0A8", "#8FD3C9", "#F7D57A", "#A7B8F0", "#F2A0A8")):
        bx = 1450 + k * 70
        c.drawPath(rrect(bx, 180, 44, 80, 10), fill(col))
        c.drawPath(rrect(bx, 180, 44, 80, 10), stroke(LINE, 3))
        c.drawRect(skia.Rect.MakeXYWH(bx + 14, 160, 16, 22), fill("#FFFFFF"))
    # 毛巾
    c.drawLine(1850, 460, 2000, 460, stroke("#B08A60", 8))
    c.drawPath(rrect(1870, 460, 110, 170, 10), fill("#F7C6CF"))
    for k in range(3):
        c.drawLine(1870, 500 + k * 40, 1980, 500 + k * 40, stroke("#E6A9B5", 4))
    # 台灯
    lx, ly = GROOM["lamp"]
    c.save()
    if lamp_fallen > 0:
        c.translate(lx + lamp_fallen * 120, ly + lamp_fallen * 30)
        c.rotate(lamp_fallen * 95)
        c.translate(-lx, -ly)
    c.drawPath(oval(lx, ly + 18, 46, 10), fill("#5A5A64"))
    c.drawLine(lx, ly + 18, lx, ly - 50, stroke("#5A5A64", 8))
    shade_col = "#F5D58A" if lamp_on else "#9A8A6A"
    c.drawPath(poly([(lx - 50, ly - 40), (lx - 26, ly - 100), (lx + 26, ly - 100), (lx + 50, ly - 40)]), fill(shade_col))
    c.drawPath(poly([(lx - 50, ly - 40), (lx - 26, ly - 100), (lx + 26, ly - 100), (lx + 50, ly - 40)]), stroke(LINE, 4))
    c.restore()


def alley_view(c, x, y, w, h, t, man=1.0, flashlight=False, van=True):
    """镜子（其实是窗户）后面的后巷：路灯、面包车、站着的人。在窗框坐标里画。"""
    from humans import HPose, draw_human
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fill(shader=lin((0, y), (0, y + h), ["#0B1028", "#1C2340"])))
    # 砖墙
    for row in range(12):
        for col in range(10):
            bx = x + col * 90 + (45 if row % 2 else 0) - 40
            by = y + h - 120 - row * 40
            c.drawRect(skia.Rect.MakeXYWH(bx, by, 84, 34), fill("#2A2338", 0.6))
    c.drawRect(skia.Rect.MakeXYWH(x, y + h - 90, w, 90), fill("#141826"))
    # 路灯光
    c.drawPath(poly([(x + w * 0.82, y + 20), (x + w * 0.60, y + h), (x + w * 1.05, y + h)]),
               fill("#FFE2A0", 0.18, blur=12))
    c.drawCircle(x + w * 0.82, y + 24, 10, fill("#FFE7A8"))
    c.drawCircle(x + w * 0.82, y + 24, 40, fill("#FFE7A8", 0.3, blur=14))
    if van:
        vx, vy = x + w * 0.08, y + h - 250
        c.drawPath(rrect(vx, vy, 360, 190, 26), fill("#C9CED8"))
        c.drawPath(rrect(vx, vy, 360, 190, 26), stroke("#0A0C14", 4))
        c.drawPath(rrect(vx + 250, vy + 25, 90, 60, 8), fill("#3A4460"))
        c.drawCircle(vx + 80, vy + 192, 34, fill("#15161C"))
        c.drawCircle(vx + 280, vy + 192, 34, fill("#15161C"))
        c.drawRect(skia.Rect.MakeXYWH(vx, y, 360, h), fill("#0B1028", 0.35))
    if man > 0:
        draw_human(c, "thief", x + w * 0.5, y + h - 20, 36, HPose(face="evil", r_up=150 if flashlight else 20,
                                                                    r_lo=10 if flashlight else 0, alpha=man,
                                                                    hold="flashlight" if flashlight else None))
    c.restore()


# ================================================================ 面包车车厢
def van_inside(c, t=0.0, bars_bent=0.0, door_light=1.0):
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 1300), fill(shader=lin((0, 0), (0, 1080), ["#2A2F3C", "#1A1D26"])))
    for x in range(-200, 2200, 160):
        c.drawLine(x, -200, x, 820, stroke("#3A4050", 8))
    c.drawRect(skia.Rect.MakeLTRB(-200, 820, 2200, 1300), fill("#22252E"))
    for x in range(-200, 2200, 60):
        c.drawLine(x, 820, x - 100, 1300, stroke("#2E323C", 4))
    # 打开的后门（右边），透进晨光
    c.drawRect(skia.Rect.MakeLTRB(1600, 80, 2000, 820), fill(shader=lin((0, 80), (0, 820), ["#F7B58A", "#FFE1B8"]), a=door_light))
    c.drawRect(skia.Rect.MakeLTRB(1600, 80, 2000, 820), stroke("#0A0C12", 10))
    # 杂物：麻袋、箱子
    c.drawPath(spline([(160, 820), (180, 640), (300, 600), (380, 660), (360, 820)]), fill("#7A5E3A"))
    c.drawPath(rrect(1350, 650, 200, 170, 6), fill("#8A6A44"))
    c.drawLine(1350, 700, 1550, 700, stroke("#6A4E30", 6))


def cage_front(c, x, y, w, h, bent=0.0, t=0.0):
    """笼子正面的栏杆；bent>0 时中间的栏杆被掰弯。"""
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, 14), fill("#8E96A6"))
    c.drawRect(skia.Rect.MakeXYWH(x, y + h - 14, w, 14), fill("#8E96A6"))
    n = 9
    for k in range(n + 1):
        bx = x + k * w / n
        mid = (k - n / 2) / (n / 2)
        push = bent * (1 - abs(mid)) ** 1.5 * 140 * (1 if mid >= 0 else -1)
        if abs(mid) < 0.25:
            push = bent * 160 * (1 if mid >= 0 else -1)
        p = spline([(bx, y + 10), (bx + push * 0.6, y + h * 0.35), (bx + push, y + h * 0.55), (bx + push * 0.5, y + h * 0.8),
                    (bx, y + h - 10)], closed=False)
        c.drawPath(p, stroke("#3A3F4A", 14))
        c.drawPath(p, stroke("#B9C1CE", 8))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), stroke("#3A3F4A", 8))


# ================================================================ 新家
def home(c, t=0.0, cat_in_window=0.0):
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 860), fill(shader=lin((0, 0), (0, 860), ["#F2D9B8", "#E4C49A"])))
    for x in range(-200, 2200, 90):
        c.drawLine(x, -200, x, 860, stroke("#E8CDA6", 10, 0.6))
    c.drawRect(skia.Rect.MakeLTRB(-200, 860, 2200, 1300), fill(shader=lin((0, 860), (0, 1080), ["#B4855A", "#93673F"])))
    c.drawRect(skia.Rect.MakeLTRB(-200, 850, 2200, 866), fill("#6E4528"))
    # 窗户（夜空）
    wx, wy, ww, wh = 260, 160, 520, 400
    c.drawPath(rrect(wx - 24, wy - 24, ww + 48, wh + 48, 10), fill("#8A5C38"))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), fill(shader=lin((0, wy), (0, wy + wh), ["#0E1638", "#2A3768"])))
    rnd = random.Random(4)
    for i in range(30):
        c.drawCircle(wx + rnd.uniform(0, ww), wy + rnd.uniform(0, wh * 0.7), rnd.uniform(1, 2.5),
                     fill("#FFFFFF", 0.5 + 0.4 * math.sin(t * 2 + i)))
    c.drawCircle(wx + 400, wy + 100, 40, fill("#FFF4D2"))
    c.drawCircle(wx + 418, wy + 88, 37, fill("#16204A"))
    # 窗台外的猫的剪影
    if cat_in_window > 0:
        from chars import Pose, draw_critter
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
        c.saveLayerAlpha(None, int(clamp(cat_in_window) * 200))
        draw_critter(c, "cat", wx + 150, wy + wh - 10, 55, Pose(eye="happy" if (t % 3) > 2.6 else "lazy",
                                                                mouth="cat", t=t, tail=math.sin(t * 2)))
        c.restore()
        c.restore()
    c.drawLine(wx + ww / 2, wy, wx + ww / 2, wy + wh, stroke("#8A5C38", 12))
    c.drawLine(wx, wy + wh / 2, wx + ww, wy + wh / 2, stroke("#8A5C38", 12))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), stroke(LINE, 6))
    c.drawPath(rrect(wx - 50, wy + wh + 20, ww + 100, 30, 6), fill("#8A5C38"))
    # 窗帘
    for sx in (wx - 90, wx + ww + 30):
        c.drawPath(spline([(sx, wy - 50), (sx + 60, wy - 50), (sx + 70, wy + wh + 80), (sx - 10, wy + wh + 80)],
                          tension=0.3), fill("#C85C5C"))
    # 落地灯
    c.drawLine(900, 860, 900, 330, stroke("#4A3A30", 10))
    c.drawPath(poly([(830, 340), (860, 250), (940, 250), (970, 340)]), fill("#F5D58A"))
    # 冰箱
    fx = 1550
    c.drawPath(rrect(fx, 180, 300, 680, 26), fill("#E9EEF2"))
    c.drawPath(rrect(fx, 180, 300, 680, 26), stroke(LINE, 5))
    c.drawLine(fx, 430, fx + 300, 430, stroke(LINE, 4))
    c.drawRect(skia.Rect.MakeXYWH(fx + 250, 260, 14, 120), fill("#AAB4BE"))
    c.drawRect(skia.Rect.MakeXYWH(fx + 250, 480, 14, 160), fill("#AAB4BE"))
    # 狗窝
    c.drawPath(oval(1150, 880, 300, 70), fill("#000", 0.2, blur=10))
    c.drawPath(oval(1150, 860, 290, 80), fill("#7A9A6A"))
    c.drawPath(oval(1150, 860, 290, 80), stroke(LINE, 5))
    c.drawPath(oval(1150, 850, 230, 50), fill("#E8E2C8"))
    # 墙上的全家福
    c.drawPath(rrect(1060, 220, 240, 170, 6), fill("#8A5C38"))
    c.drawPath(rrect(1074, 234, 212, 142, 3), fill("#FDF2DC"))
    from chars import Pose, draw_critter
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(1074, 234, 212, 142))
    draw_critter(c, "cheems", 1140, 395, 38, Pose(eye="happy", mouth="grin", t=0))
    draw_critter(c, "golden", 1225, 395, 38, Pose(eye="happy", mouth="smile", t=0))
    c.restore()


def fridge_note(c, x, y, s, t, line2=0.0):
    """贴在冰箱上的家规。line2：Cheems 用蜡笔写第二条的进度。"""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(-3)
    c.drawPath(rrect(-200, -150, 400, 300, 6), fill("#FFFDF4"))
    for k in range(6):
        c.drawLine(-180, -60 + k * 40, 180, -60 + k * 40, stroke("#B8D4F0", 2))
    c.drawPath(rrect(-200, -150, 400, 300, 6), stroke("#C8B89A", 3))
    c.drawCircle(0, -150, 16, fill("#E2574C"))
    draw_text(c, "家　规", 0, -95, size=44, name="brush", color="#3A2A20")
    draw_text(c, "一、晚上十点以后，", -175, -30, size=30, name="brush", color="#2A3A6A", align="left")
    draw_text(c, "　　不准偷吃零食。", -175, 10, size=30, name="brush", color="#2A3A6A", align="left")
    if line2 > 0:
        txt = "二、家规里有一条是假的m"
        n = int(len(txt) * clamp(line2))
        draw_text(c, txt[:n], -175, 80, size=32, name="hand", color="#E2574C", align="left")
        if line2 >= 1:
            paw(c, 150, 115, 12, "#E39B4D")
    c.restore()
