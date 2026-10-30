"""人类角色：主人、偷狗贼（夜里一身黑 / 天亮时伪装成蓝卫衣）、王店长。

简单的「两段式四肢」骨架，扁平风格。站立时身高 10 个单位（脚底为原点，向上为负）。
"""
from __future__ import annotations

import math

import skia

from gfx import clamp, draw_shape, fill, lerp, oval, shade, spline, stroke

LOOKS = {
    "owner": dict(top="#4C82C6", top_d="#3A68A3", legs="#34496B", skin="#F6CFAE", hair="#2A2220", shoes="#3B3B3B",
                  hood=True),
    "thief": dict(top="#2C2F36", top_d="#1E2026", legs="#23252B", skin="#E6BC9A", hair="#151515", shoes="#141414",
                  hood=True, cap=True, mask=True),
    "thief_blue": dict(top="#4A7DC0", top_d="#37639E", legs="#2B2F38", skin="#E6BC9A", hair="#151515",
                       shoes="#141414", hood=True, cap=True, mask=False, shadow_face=True),
    "staff": dict(top="#F0A3AE", top_d="#D58591", legs="#6B6F7A", skin="#F7D2B6", hair="#5A3A28", shoes="#4A3A30",
                  apron=True, bun=True),
    "police": dict(top="#2D3E66", top_d="#22304F", legs="#1E2740", skin="#F1C9A6", hair="#222", shoes="#111",
                   cap=True, police=True),
}

LINE = "#2A211C"


class HPose:
    FIELDS = dict(turn=0.0, pelvis=-4.7, l_th=0.0, l_sh=0.0, r_th=0.0, r_sh=0.0, l_up=8.0, l_lo=0.0, r_up=8.0,
                  r_lo=0.0, tilt=0.0, face="smile", talk=0.0, blink=0.0, look=(0.0, 0.0), hold=None,
                  kneel=False, bob=0.0, lean=0.0, alpha=1.0, t=0.0, silhouette=0.0, flip=False)

    def __init__(self, **kw):
        for k, v in self.FIELDS.items():
            setattr(self, k, v)
        for k, v in kw.items():
            if k not in self.FIELDS:
                raise KeyError(k)
            setattr(self, k, v)


def walk_pose(phase, **kw):
    s = math.sin(phase * 2 * math.pi)
    c = math.cos(phase * 2 * math.pi)
    d = dict(l_th=26 * s, r_th=-26 * s, l_sh=26 * s - max(0.0, -c) * 30, r_sh=-26 * s - max(0.0, c) * 30,
             l_up=10 - 22 * s, r_up=10 + 22 * s, l_lo=-15, r_lo=-15, bob=-abs(c) * 0.15)
    d.update(kw)
    return HPose(**d)


def _limb(c, x, y, a1, l1, a2, l2, w, color, outward=1):
    """两段式肢体，角度从「竖直向下」量起，outward=±1 决定正角度朝哪边。"""
    r1 = math.radians(a1)
    kx = x + outward * math.sin(r1) * l1
    ky = y + math.cos(r1) * l1
    r2 = math.radians(a1 + a2)
    ex = kx + outward * math.sin(r2) * l2
    ey = ky + math.cos(r2) * l2
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(kx, ky)
    p.lineTo(ex, ey)
    c.drawPath(p, stroke(LINE, w + 0.12))
    c.drawPath(p, stroke(color, w))
    return (kx, ky), (ex, ey)


def draw_human(c, kind, x, y, hs, pose: HPose):
    lk = LOOKS[kind]
    c.save()
    c.translate(x, y)
    c.scale(hs, hs)
    if pose.flip:
        c.scale(-1, 1)
    if pose.alpha < 1:
        c.saveLayerAlpha(None, int(clamp(pose.alpha) * 255))
    c.drawPath(oval(0, 0, 2.0, 0.28), fill("#000000", 0.25, blur=0.15))
    c.translate(0, pose.bob)
    c.skew(pose.lean * 0.12, 0)
    tx = pose.turn * 0.5
    py = pose.pelvis
    # 腿
    feet = []
    if pose.kneel:
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(side * 0.5, py)
            p.lineTo(side * 0.75, -0.35)
            c.drawPath(p, stroke(LINE, 1.07))
            c.drawPath(p, stroke(lk["legs"], 0.95))
            c.drawPath(oval(side * 0.8, -0.2, 0.62, 0.32), fill(lk["legs"]))
            c.drawPath(oval(side * 0.8, -0.2, 0.62, 0.32), stroke(LINE, 0.1))
    else:
        for side, th, sh in ((-1, pose.l_th, pose.l_sh), (1, pose.r_th, pose.r_sh)):
            _, foot = _limb(c, side * 0.48, py, th, 2.3, sh - th, 2.15, 0.95, lk["legs"], outward=1)
            feet.append(foot)
            fx, fy = foot
            shoe = spline([(fx - 0.45, fy + 0.05), (fx - 0.35, fy - 0.35), (fx + 0.45, fy - 0.30), (fx + 0.70, fy + 0.0),
                           (fx + 0.6, fy + 0.2), (fx - 0.4, fy + 0.2)], tension=0.8)
            draw_shape(c, shoe, lk["shoes"], LINE, 0.1)
            c.drawLine(fx - 0.4, fy + 0.14, fx + 0.6, fy + 0.14, stroke("#EEEEEE", 0.1))
    # 躯干
    top_y = py - 3.0
    torso = spline([(0, top_y - 0.05), (1.10, top_y + 0.05), (1.35, top_y + 0.6), (1.38, py - 1.1), (1.30, py + 0.25),
                    (0, py + 0.35), (-1.30, py + 0.25), (-1.38, py - 1.1), (-1.35, top_y + 0.6), (-1.10, top_y + 0.05)])
    if lk.get("hood"):
        c.drawPath(oval(tx * 0.3, top_y + 0.05, 1.05, 0.55), fill(lk["top_d"]))
        c.drawPath(oval(tx * 0.3, top_y + 0.05, 1.05, 0.55), stroke(LINE, 0.1))
    draw_shape(c, torso, lk["top"], LINE, 0.1, lk["top_d"], (-0.15, -0.2))
    if lk.get("hood"):
        pk = spline([(-0.85 + tx, py - 1.2), (0.85 + tx, py - 1.2), (1.0 + tx, py - 0.2), (-1.0 + tx, py - 0.2)],
                    tension=0.4)
        c.drawPath(pk, stroke(lk["top_d"], 0.09))
        for s in (-1, 1):
            c.drawLine(s * 0.28 + tx, top_y + 0.3, s * 0.32 + tx, top_y + 1.5, stroke("#EDEDED", 0.08))
    if lk.get("apron"):
        ap = spline([(-0.9 + tx, top_y + 0.9), (0.9 + tx, top_y + 0.9), (1.05 + tx, py + 0.6), (-1.05 + tx, py + 0.6)],
                    tension=0.3)
        draw_shape(c, ap, "#FFFFFF", LINE, 0.08, "#E6E6EA", (-0.1, -0.1))
        c.drawPath(oval(tx, py - 0.9, 0.35, 0.3), fill("#F0A3AE", 0.8))
    if lk.get("police"):
        c.drawPath(oval(0.7 + tx, top_y + 0.9, 0.22, 0.25), fill("#E8C34A"))
    # 手臂
    hands = {}
    for side, up, lo in ((-1, pose.l_up, pose.l_lo), (1, pose.r_up, pose.r_lo)):
        _, hand = _limb(c, side * 1.12 + tx * 0.2, top_y + 0.45, up, 1.7, lo, 1.55, 0.78, lk["top"], outward=side)
        hands[side] = hand
        c.drawCircle(hand[0], hand[1], 0.38, fill(lk["skin"]))
        c.drawCircle(hand[0], hand[1], 0.38, stroke(LINE, 0.09))
    _hold(c, pose, hands, lk)
    # 头
    hy = top_y - 1.15
    c.save()
    c.translate(tx * 0.4, hy)
    c.rotate(pose.tilt)
    c.drawRect(skia.Rect.MakeLTRB(-0.32, 0.6, 0.32, 1.25), fill(shade(lk["skin"], -0.1)))
    head = oval(0, 0, 1.18, 1.25)
    for s in (-1, 1):
        c.drawPath(oval(s * 1.12, 0.1, 0.25, 0.32), fill(lk["skin"]))
        c.drawPath(oval(s * 1.12, 0.1, 0.25, 0.32), stroke(LINE, 0.08))
    draw_shape(c, head, lk["skin"], LINE, 0.1, shade(lk["skin"], -0.08), (-0.12, -0.15))
    ftx = pose.turn * 0.45
    _face(c, pose, lk, ftx)
    _hair(c, pose, lk, ftx)
    c.restore()
    if pose.silhouette > 0:
        c.restore()
        c.save()
    if pose.alpha < 1:
        c.restore()
    c.restore()


def _face(c, pose, lk, ftx):
    if lk.get("mask"):
        m = spline([(-1.05, 0.15), (1.05, 0.15), (0.95, 0.75), (0.0, 1.22), (-0.95, 0.75)], tension=0.7)
        c.drawPath(m, fill("#1A1A1C"))
    shadow = lk.get("shadow_face")
    eye_y = -0.05
    for s in (-1, 1):
        ex = s * 0.42 + ftx
        if pose.blink > 0.8:
            c.drawLine(ex - 0.15, eye_y, ex + 0.15, eye_y, stroke(LINE, 0.09))
        elif lk.get("mask") or shadow:
            c.drawPath(oval(ex + pose.look[0] * 0.06, eye_y, 0.13, 0.06), fill("#F2F2F2", 0.9))
            c.drawPath(oval(ex + pose.look[0] * 0.06, eye_y, 0.05, 0.05), fill("#111"))
        else:
            c.drawPath(oval(ex + pose.look[0] * 0.06, eye_y + pose.look[1] * 0.05, 0.12, 0.15), fill("#2A1F1A"))
            c.drawPath(oval(ex - 0.04, eye_y - 0.06, 0.04, 0.04), fill("#fff"))
        # 眉毛
        by = -0.42
        if pose.face in ("worried", "sad", "cry"):
            c.drawLine(ex - 0.2, by + s * 0.0 - 0.0, ex + 0.2 * 1, by - 0.0, stroke(LINE, 0.0))
            c.drawLine(ex - 0.18 * s, by - 0.08, ex + 0.18 * s, by + 0.04, stroke(lk["hair"], 0.1))
        elif pose.face in ("angry", "evil"):
            c.drawLine(ex - 0.2 * s, by + 0.08, ex + 0.2 * s, by - 0.06, stroke(lk["hair"], 0.12))
        elif pose.face == "shock":
            c.drawLine(ex - 0.2, by - 0.12, ex + 0.2, by - 0.12, stroke(lk["hair"], 0.1))
        else:
            c.drawPath(spline([(ex - 0.2, by + 0.02), (ex, by - 0.06), (ex + 0.2, by + 0.02)], closed=False),
                       stroke(lk["hair"], 0.1))
    if lk.get("mask"):
        return
    if shadow:
        c.drawPath(oval(ftx, 0.3, 1.2, 0.9), fill("#1A2238", 0.55, blur=0.25))
    # 鼻子
    c.drawPath(spline([(ftx + 0.02, 0.15), (ftx + 0.1, 0.32), (ftx - 0.05, 0.35)], closed=False),
               stroke(shade(lk["skin"], -0.3), 0.07))
    # 嘴
    my = 0.62
    talk = clamp(pose.talk)
    if talk > 0.08 or pose.face in ("shock", "open"):
        h = 0.08 + 0.3 * max(talk, 0.5 if pose.face == "shock" else 0)
        p = spline([(ftx - 0.25, my), (ftx + 0.25, my), (ftx + 0.15, my + h), (ftx - 0.15, my + h)], tension=0.8)
        c.drawPath(p, fill("#6B2A2A"))
        c.drawPath(p, stroke(LINE, 0.07))
    elif pose.face in ("sad", "worried", "cry"):
        c.drawPath(spline([(ftx - 0.22, my + 0.08), (ftx, my - 0.02), (ftx + 0.22, my + 0.08)], closed=False),
                   stroke(LINE, 0.08))
    elif pose.face == "evil":
        c.drawPath(spline([(ftx - 0.3, my - 0.05), (ftx, my + 0.08), (ftx + 0.3, my - 0.1)], closed=False),
                   stroke(LINE, 0.08))
    else:
        c.drawPath(spline([(ftx - 0.25, my - 0.04), (ftx, my + 0.12), (ftx + 0.25, my - 0.04)], closed=False),
                   stroke(LINE, 0.08))
    if pose.face in ("smile", "happy"):
        for s in (-1, 1):
            c.drawPath(oval(s * 0.68 + ftx, 0.35, 0.2, 0.1), fill("#FF8F8F", 0.35, blur=0.05))


def _hair(c, pose, lk, ftx):
    if lk.get("cap"):
        cap = spline([(-1.22, -0.25), (-1.15, -0.85), (-0.5, -1.35), (0.5, -1.35), (1.15, -0.85), (1.22, -0.25)],
                     tension=0.9)
        cap.close()
        col = "#16171A" if not lk.get("police") else "#1E2A48"
        draw_shape(c, cap, col, LINE, 0.1)
        brim = spline([(-1.1 + ftx, -0.32), (1.4 + ftx, -0.32), (1.6 + ftx, -0.12), (-1.0 + ftx, -0.12)], tension=0.5)
        draw_shape(c, brim, col, LINE, 0.1)
        c.drawPath(oval(ftx, 0.05, 1.15, 0.35), fill("#000000", 0.35, blur=0.12))
        if lk.get("police"):
            c.drawPath(oval(ftx * 0.6, -0.85, 0.22, 0.22), fill("#E8C34A"))
        return
    hair = spline([(-1.25, 0.05), (-1.25, -0.6), (-0.8, -1.2), (0.0, -1.42), (0.85, -1.22), (1.28, -0.6), (1.25, 0.0),
                   (1.0, -0.45), (0.55 + ftx * 0.3, -0.62), (0.2 + ftx * 0.3, -0.45), (-0.2 + ftx * 0.3, -0.7),
                   (-0.8, -0.45), (-1.05, -0.1)], tension=0.9)
    draw_shape(c, hair, lk["hair"], LINE, 0.1, shade(lk["hair"], -0.2), (-0.05, -0.08))
    c.drawPath(oval(-0.4, -1.0, 0.35, 0.12), fill("#ffffff", 0.18, blur=0.05))
    if lk.get("bun"):
        b = oval(0.0, -1.55, 0.55, 0.45)
        draw_shape(c, b, lk["hair"], LINE, 0.1, shade(lk["hair"], -0.2), (-0.05, -0.08))


def _hold(c, pose, hands, lk):
    h = pose.hold
    if not h:
        return
    hx, hy = hands[1]
    if h == "leash":
        sway = math.sin(pose.t * 2.0) * 0.25
        p = spline([(hx, hy), (hx + 0.3 + sway * 0.5, hy + 1.2), (hx + sway, hy + 2.4)], closed=False)
        c.drawPath(p, stroke("#8E1B1B", 0.24))
        c.drawPath(p, stroke("#E23A3A", 0.16))
        c.drawPath(oval(hx + sway, hy + 2.55, 0.18, 0.22), stroke("#C9C9C9", 0.09))
        c.drawPath(oval(hx, hy, 0.42, 0.42), stroke("#E23A3A", 0.14))
    elif h == "sack":
        sx, sy = hands[-1]
        sack = spline([(sx - 0.3, sy - 0.1), (sx + 0.3, sy - 0.1), (sx + 0.9, sy + 1.4), (sx + 0.5, sy + 2.4),
                       (sx - 0.6, sy + 2.4), (sx - 0.9, sy + 1.3)], tension=0.9)
        draw_shape(c, sack, "#9B7A4E", LINE, 0.1, "#7D5F38", (-0.1, -0.1))
        c.drawLine(sx - 0.3, sy + 0.2, sx + 0.35, sy + 0.25, stroke("#5A4128", 0.1))
    elif h == "flashlight":
        c.save()
        c.translate(hx, hy)
        c.rotate(-80)
        c.drawRect(skia.Rect.MakeLTRB(-0.15, -0.2, 0.9, 0.2), fill("#3A3A3A"))
        c.drawRect(skia.Rect.MakeLTRB(0.8, -0.28, 1.05, 0.28), fill("#555"))
        c.restore()
