"""原创卡通角色：Cheems（柴犬）、大壮（健身柴）、二哈（哈士奇）、小柯（柯基）、老金（金毛）、
大橘（橘猫管理员）、玩具猫（偷狗贼的遥控猫）、阿福（鹦鹉）。

所有角色都是用矢量路径现画的，坐标以「单位 u」表示：脚底中心是原点，向上为负。
"""
from __future__ import annotations

import math

import skia

from gfx import (C, clamp, poly, draw_shape, draw_text, fill, lerp, mirror_pts, mix, oval, rad, shade, spline,
                 stroke, wave)

OW = 0.05  # 描边宽度（单位 u）


class Pose:
    FIELDS = dict(
        eye="open", blink=0.0, look=(0.0, 0.0), brow=0.0, brow_y=0.0, mouth="smile", talk=0.0,
        ear=0.0, tilt=0.0, turn=0.0, bob=0.0, squash=0.0, tail=0.0, tremble=0.0, blush=0.0, tears=0.0,
        sweat=0.0, arm_l=0.0, arm_r=0.0, tongue=False, flip=False, alpha=1.0, drool=0.0, glow=0.0,
        pupil=1.0, walk=None, lean=0.0, sleep=False, mark=None, flex=0.0, wing=0.0, t=0.0,
    )

    def __init__(self, **kw):
        for k, v in self.FIELDS.items():
            setattr(self, k, v)
        for k, v in kw.items():
            if k not in self.FIELDS:
                raise KeyError(k)
            setattr(self, k, v)

    def copy(self, **kw):
        p = Pose(**{k: getattr(self, k) for k in self.FIELDS})
        for k, v in kw.items():
            setattr(p, k, v)
        return p


# 表情预设：只写和默认值不同的字段
EMOTIONS = {
    "normal": {},
    "happy": dict(eye="happy", mouth="grin", blush=0.35, ear=-0.05),
    "joy": dict(eye="happy", mouth="grin", blush=0.5, ear=-0.1, brow_y=0.5),
    "sad": dict(eye="sad", brow=1.0, mouth="frown", ear=0.75),
    "scared": dict(eye="wide", brow=1.0, mouth="wavy", ear=0.85, tremble=1.0, sweat=1.0, pupil=0.7),
    "terror": dict(eye="wide", brow=1.0, brow_y=0.6, mouth="o", ear=0.9, tremble=1.6, sweat=1.0, pupil=0.45),
    "shock": dict(eye="wide", brow_y=1.0, mouth="o", ear=-0.2, pupil=0.6),
    "cry": dict(eye="tight", brow=1.0, mouth="wavy", ear=0.9, tears=1.0),
    "weep": dict(eye="sad", brow=1.0, mouth="frown", ear=0.8, tears=0.6),
    "angry": dict(eye="angry", brow=-1.0, mouth="frown", ear=0.15),
    "determined": dict(eye="angry", brow=-0.7, mouth="flat", ear=-0.15),
    "smug": dict(eye="squint", brow=-0.3, mouth="smile"),
    "sleepy": dict(eye="closed", mouth="flat", ear=0.3),
    "sleep": dict(eye="closed", mouth="flat", ear=0.35, sleep=True),
    "confused": dict(eye="open", brow=0.5, mouth="flat", tilt=12, look=(0.3, -0.6)),
    "hungry": dict(eye="sparkle", mouth="open", tongue=True, drool=1.0, blush=0.3),
    "think": dict(eye="open", look=(0.6, -0.7), mouth="flat", brow=0.3),
    "lazy": dict(eye="squint", mouth="smile"),
    "cool": dict(eye="squint", brow=-0.5, mouth="smile"),
    "worried": dict(eye="open", brow=1.0, mouth="wavy", ear=0.5, sweat=0.6),
    "nervous": dict(eye="open", brow=1.0, mouth="wavy", ear=0.6, sweat=1.0, tremble=0.5),
    "sparkle": dict(eye="sparkle", mouth="grin", blush=0.4),
    "creepy": dict(eye="squint", mouth="smile", brow=-0.6),
    "guilty": dict(eye="sad", brow=1.0, mouth="flat", ear=0.9, look=(-0.4, 0.6)),
    "proud": dict(eye="happy", mouth="smile", brow=-0.2, blush=0.2),
    "derp": dict(eye="open", mouth="grin", tongue=True, look=(0.0, 0.0)),
}


def emo_pose(name, **kw):
    d = dict(EMOTIONS.get(name, {}))
    d.update(kw)
    return Pose(**d)


# ---------------------------------------------------------------- 物种配置
SPECIES = {
    "cheems": dict(fur="#E8A04F", fur_d="#C97A33", cream="#FFF2DC", cream_d="#E9CFA8", line="#4A2C17",
                   inner="#F7CBA6", nose="#2B1D16", ears="pointy", mask="shiba", eyes="dot", brows="dots",
                   body="sit", tail="curl", head_y=-2.35, head_s=1.0),
    "dazhuang": dict(fur="#DD8C3C", fur_d="#B96A26", cream="#FFEFD6", cream_d="#E8C99D", line="#4A2A12",
                     inner="#F5C29A", nose="#2B1D16", ears="pointy", mask="shiba", eyes="dot", brows="dots",
                     body="swole", tail="curl", head_y=-3.55, head_s=0.86, headband=True),
    "husky": dict(fur="#5B6573", fur_d="#444C58", cream="#F7F8F8", cream_d="#D5DAE0", line="#252A31",
                  inner="#F2D6D6", nose="#22252A", ears="pointy", mask="husky", eyes="husky", brows="dots_w",
                  body="sit", tail="bushy", head_y=-2.4, head_s=1.0),
    "corgi": dict(fur="#E8853A", fur_d="#C76822", cream="#FFF7EC", cream_d="#EBD6BC", line="#4D2A12",
                  inner="#F9C7A8", nose="#2A1B14", ears="big", mask="corgi", eyes="sparkle", brows=None,
                  body="short", tail="fluff", head_y=-2.0, head_s=1.0),
    "golden": dict(fur="#E3AE58", fur_d="#C18B37", cream="#F5DDAE", cream_d="#DCBE88", line="#4E3315",
                   inner="#E2A85A", nose="#2E2018", ears="floppy", mask="golden", eyes="gentle", brows="tufts",
                   body="fluffy", tail="feather", head_y=-2.5, head_s=1.05),
    "cat": dict(fur="#F0A048", fur_d="#D07C2C", cream="#FFF1DE", cream_d="#ECD1AE", line="#4A2A14",
                inner="#F6B8B0", nose="#E58A8A", ears="cat", mask="cat", eyes="cat", brows=None,
                body="cat", tail="cat", head_y=-2.25, head_s=0.92, stripes="#C9682A"),
    "robocat": dict(fur="#F2A24A", fur_d="#D47F2E", cream="#FFF3E2", cream_d="#EED4B2", line="#3B2416",
                    inner="#F6B8B0", nose="#E58A8A", ears="cat", mask="cat", eyes="robot", brows=None,
                    body="cat", tail="cat", head_y=-2.25, head_s=0.92, stripes="#C9682A", robot=True),
}

# 头部轮廓（右半边，从头顶到下巴）
HEAD_SHAPES = {
    "shiba": [(0, -0.86), (0.45, -0.81), (0.79, -0.58), (0.96, -0.22), (1.07, 0.13), (1.0, 0.43), (0.78, 0.67),
              (0.42, 0.84), (0, 0.89)],
    "husky": [(0, -0.88), (0.45, -0.83), (0.80, -0.60), (0.97, -0.22), (1.05, 0.12), (0.98, 0.42), (0.76, 0.67),
              (0.42, 0.86), (0, 0.92)],
    "corgi": [(0, -0.84), (0.46, -0.80), (0.80, -0.56), (0.98, -0.18), (1.04, 0.16), (0.96, 0.45), (0.74, 0.68),
              (0.40, 0.84), (0, 0.88)],
    "golden": [(0, -0.86), (0.44, -0.82), (0.76, -0.58), (0.90, -0.18), (0.89, 0.27), (0.70, 0.63),
               (0.38, 0.86), (0, 0.93)],
    "cat": [(0, -0.80), (0.50, -0.75), (0.84, -0.46), (1.0, -0.06), (1.10, 0.24), (0.94, 0.42), (0.92, 0.50),
            (0.62, 0.70), (0, 0.78)],
}


def _head_path(sp):
    key = {"shiba": "shiba", "husky": "husky", "corgi": "corgi", "golden": "golden", "cat": "cat"}[sp["mask"]]
    return spline(mirror_pts(HEAD_SHAPES[key]))


def sym(c, fn):
    """左右对称地画：fn(side) 里按右边（side=+1）的坐标画，左边自动镜像。"""
    fn(1)
    c.save()
    c.scale(-1, 1)
    fn(-1)
    c.restore()


# ---------------------------------------------------------------- 耳朵
def _ears(c, sp, pose, front=False):
    kind = sp["ears"]
    if (kind == "floppy") != front:
        return
    droop = pose.ear
    line = sp["line"]

    def one(side):
        c.save()
        if kind == "floppy":
            c.translate(0.62, -0.62)
            c.rotate(-droop * 8 + wave(pose.t, 2.3) * 2)
            c.translate(-0.62, 0.62)
            pts = [(0.52, -0.72), (0.86, -0.66), (1.08, -0.28), (1.13, 0.22), (1.04, 0.52), (0.86, 0.50),
                   (0.74, 0.12), (0.60, -0.36)]
            path = spline(pts)
            draw_shape(c, path, sp["fur"], line, OW, sp["fur_d"], (-0.05, -0.08))
            c.drawPath(spline([(0.66, -0.50), (0.84, -0.35), (0.96, 0.05), (0.98, 0.32)], closed=False),
                       stroke(sp["fur_d"], 0.035, 0.7))
        else:
            base = (0.62, -0.55)
            c.translate(*base)
            c.rotate(droop * 58 + wave(pose.t, 3.1, 0.2 * side) * 1.5)
            c.translate(-base[0], -base[1])
            if kind == "pointy":
                pts = [(0.18, -0.70), (0.38, -1.06), (0.64, -1.38), (0.80, -1.16), (0.96, -0.66), (0.88, -0.34)]
                inner = [(0.36, -0.78), (0.52, -1.04), (0.65, -1.20), (0.75, -1.00), (0.82, -0.66), (0.66, -0.55)]
            elif kind == "big":
                pts = [(0.14, -0.66), (0.40, -1.14), (0.76, -1.66), (1.00, -1.22), (1.05, -0.60), (0.92, -0.30)]
                inner = [(0.34, -0.76), (0.55, -1.12), (0.77, -1.46), (0.90, -1.12), (0.92, -0.66), (0.70, -0.52)]
            else:  # cat
                pts = [(0.22, -0.68), (0.46, -1.06), (0.66, -1.34), (0.80, -1.08), (0.94, -0.58), (0.84, -0.36)]
                inner = [(0.40, -0.74), (0.56, -1.02), (0.67, -1.16), (0.76, -0.96), (0.83, -0.62), (0.66, -0.56)]
            path = spline(pts)
            draw_shape(c, path, sp["fur"], line, OW, sp["fur_d"], (-0.04, -0.05))
            ic = sp["inner"] if sp["mask"] not in ("husky",) else sp["cream"]
            c.drawPath(spline(inner), fill(ic))
            c.drawPath(spline(inner), fill(shade(ic, -0.12), 0.6, blur=0.03))
            if sp["mask"] == "husky":
                c.drawPath(spline(inner), fill(sp["inner"], 0.5))
        c.restore()

    sym(c, one)


# ---------------------------------------------------------------- 面部花纹
def _mask(c, sp, pose, head):
    tx = pose.turn * 0.2
    c.save()
    c.clipPath(head, skia.ClipOp.kIntersect, True)
    m = sp["mask"]
    cream, cream_d = sp["cream"], sp["cream_d"]
    if m == "shiba":
        pts = [(0.0, 0.0), (0.22, -0.02), (0.48, 0.07), (0.76, 0.05), (1.12, 0.06), (1.15, 1.0), (0, 1.0)]
        path = spline([(x + tx, y) for x, y in mirror_pts(pts)])
        draw_shape(c, path, cream, None, 0, cream_d, (-0.03, -0.07))
    elif m == "husky":
        # 头顶深色「帽子」，中间一道深色延伸到鼻梁
        pts = [(0, -1.0), (0.7, -1.0), (1.2, -0.6), (1.18, 0.06), (0.96, 0.10), (0.72, -0.20), (0.48, -0.36),
               (0.24, -0.30), (0.10, -0.08), (0.06, 0.06), (0, 0.08)]
        path = spline([(x + tx, y) for x, y in mirror_pts(pts)])
        draw_shape(c, path, sp["fur"], None, 0, sp["fur_d"], (-0.03, -0.07))
    elif m == "corgi":
        pts = [(0, -0.9), (0.07, -0.9), (0.10, -0.32), (0.24, -0.04), (0.55, 0.10), (1.15, 0.20), (1.15, 1.0),
               (0, 1.0)]
        path = spline([(x + tx * 0.8, y) for x, y in mirror_pts(pts)])
        draw_shape(c, path, cream, None, 0, cream_d, (-0.03, -0.07))
    elif m == "golden":
        pass
    elif m == "cat":
        pts = [(0.0, 0.02), (0.24, 0.0), (0.50, 0.12), (0.80, 0.22), (1.15, 0.30), (1.15, 1.0), (0, 1.0)]
        path = spline([(x + tx, y) for x, y in mirror_pts(pts)])
        draw_shape(c, path, cream, None, 0, cream_d, (-0.03, -0.06))
        st = sp["stripes"]
        for dx, l in ((0.0, 0.30), (-0.18, 0.22), (0.18, 0.22)):
            c.drawPath(spline([(dx + tx, -0.80), (dx * 1.1 + tx, -0.80 + l)], closed=False),
                       stroke(st, 0.075, 0.9))

        def cheek(side):
            for i, yy in enumerate((0.02, 0.16)):
                c.drawPath(spline([(1.08, yy), (0.86, yy + 0.03), (0.72, yy + 0.08)], closed=False),
                           stroke(st, 0.06, 0.85))
        sym(c, cheek)
    # 头顶高光
    c.drawPath(oval(-0.38, -0.52, 0.42, 0.26), fill("#ffffff", 0.16, blur=0.12))
    c.restore()


# ---------------------------------------------------------------- 眼睛
def _eye(c, sp, pose, side):
    """画右眼（side=+1）或左眼（镜像后同样按右眼画，所以 look 的 x 要反过来）。"""
    style = sp["eyes"]
    turn = pose.turn * side
    ex = 0.38 + pose.turn * 0.2 * side
    ey = -0.12
    if style == "cat":
        ex, ey = 0.40 + pose.turn * 0.2 * side, -0.10
    sx = 1.0 - max(0.0, -turn) * 0.25  # 远处那只眼睛窄一点
    lx = pose.look[0] * side * 0.05
    ly = pose.look[1] * 0.05
    line = sp["line"]
    dark = "#21140D" if style != "husky" else "#15181C"
    e = pose.eye
    blink = clamp(pose.blink)
    c.save()
    c.translate(ex, ey)
    c.scale(sx, 1)
    if style == "gentle" and e == "open":
        e = "gentle"
    if e in ("open", "sad", "angry", "squint", "gentle") and blink > 0.85:
        e = "closed"
    if e == "happy":
        c.drawPath(spline([(-0.12, 0.04), (0.0, -0.08), (0.12, 0.04)], closed=False), stroke(dark, 0.06))
    elif e == "closed":
        c.drawPath(spline([(-0.12, -0.01), (0.0, 0.06), (0.12, -0.01)], closed=False), stroke(dark, 0.055))
    elif e == "tight":
        c.drawPath(spline([(-0.12, -0.07), (0.08, 0.0), (-0.12, 0.07)], closed=False), stroke(dark, 0.055))
    elif e == "x":
        c.drawLine(-0.08, -0.08, 0.08, 0.08, stroke(dark, 0.05))
        c.drawLine(-0.08, 0.08, 0.08, -0.08, stroke(dark, 0.05))
    elif e == "wide" or style in ("husky", "robot") or (style == "cat" and e not in ("squint",)):
        _eye_full(c, sp, pose, e, lx, ly, blink, side)
    else:
        # 小黑豆眼（Cheems 系）
        rx, ry = (0.088, 0.112) if style == "dot" else (0.12, 0.145) if style == "sparkle" else (0.09, 0.105)
        if e == "sparkle":
            rx, ry = 0.125, 0.15
        h = ry * (1 - blink)
        c.drawPath(oval(lx, ly, rx, max(h, 0.012)), fill(dark))
        if h > 0.04:
            c.drawPath(oval(lx - rx * 0.32, ly - h * 0.38, rx * 0.36, rx * 0.36), fill("#ffffff", 0.95))
            if style == "sparkle" or e == "sparkle":
                c.drawPath(oval(lx + rx * 0.35, ly + h * 0.35, rx * 0.18, rx * 0.18), fill("#ffffff", 0.85))
        # 眼皮
        if e == "sad":
            c.drawPath(spline([(-0.15, -0.06), (0.0, -0.09), (0.15, -0.03)], closed=False), stroke(line, 0.04))
            c.drawPath(poly([(-0.2, -0.2), (0.2, -0.2), (0.2, -0.02), (-0.2, -0.10)]),
                       fill(sp["fur"] if sp["mask"] != "corgi" else sp["fur"]))
        elif e == "angry":
            c.drawPath(poly([(-0.2, -0.22), (0.2, -0.22), (0.2, -0.10), (-0.2, -0.0)]),
                       fill(sp["fur"]))
            c.drawLine(-0.16, 0.0, 0.16, -0.10, stroke(line, 0.045))
        elif e in ("squint", "gentle"):
            k = 0.0 if e == "squint" else -0.02
            c.drawPath(poly([(-0.2, -0.22), (0.2, -0.22), (0.2, -0.02 + k), (-0.2, -0.02 + k)]),
                       fill(sp["fur"] if sp["mask"] != "golden" else sp["fur"]))
            c.drawPath(spline([(-0.14, -0.01 + k), (0.0, -0.035 + k), (0.14, -0.01 + k)], closed=False),
                       stroke(line, 0.045))
    c.restore()


def _eye_full(c, sp, pose, e, lx, ly, blink, side):
    """有眼白的眼睛：惊恐、哈士奇、猫、机器猫。"""
    style = sp["eyes"]
    dark = "#15181C"
    line = sp["line"]
    if style == "robot":
        r = 0.13
        c.drawPath(oval(0, 0, r + 0.03, r + 0.03), fill("#2A2A2E"))
        c.drawPath(oval(0, 0, r + 0.03, r + 0.03), stroke(line, 0.035))
        g = 0.6 + 0.4 * pose.glow
        c.drawPath(oval(lx * 0.5, ly * 0.5, r * 0.62, r * 0.62), fill("#FF2A2A", 0.9 * g))
        c.drawPath(oval(lx * 0.5, ly * 0.5, r * 1.6, r * 1.6), fill("#FF2020", 0.35 * g, blur=0.08))
        c.drawPath(oval(lx * 0.5, ly * 0.5, r * 0.25, r * 0.25), fill("#FFE0E0", 0.95))
        c.drawPath(oval(-0.05, -0.06, 0.035, 0.035), fill("#ffffff", 0.8))
        return
    if style == "cat" and e != "wide":
        # 杏仁形猫眼 + 竖瞳
        w, h = 0.19, 0.15 * (1 - blink)
        if e == "squint" or e == "lazy":
            h *= 0.55
        if e == "angry":
            h *= 0.7
        if h < 0.02:
            c.drawPath(spline([(-0.17, 0.0), (0.0, 0.05), (0.17, 0.0)], closed=False), stroke(line, 0.05))
            return
        almond = spline([(-w, 0.01), (-w * 0.5, -h), (w * 0.4, -h * 1.05), (w, -0.02), (w * 0.4, h * 0.9),
                         (-w * 0.5, h * 0.85)])
        c.drawPath(almond, fill("#C9DB5E"))
        c.save()
        c.clipPath(almond, skia.ClipOp.kIntersect, True)
        c.drawPath(oval(lx, ly + 0.03, 0.22, 0.2), fill("#8FB33A", 0.5, blur=0.03))
        pw = 0.028 + 0.06 * clamp(pose.pupil - 1.0, 0, 1)
        c.drawPath(oval(lx, ly, pw, 0.13), fill(dark))
        c.drawPath(oval(lx - 0.05, ly - 0.05, 0.035, 0.035), fill("#ffffff", 0.9))
        c.restore()
        c.drawPath(almond, stroke(line, 0.04))
        c.drawPath(spline([(-w - 0.01, 0.02), (-w * 0.5, -h - 0.01), (w * 0.4, -h * 1.05 - 0.01), (w + 0.03, -0.04)],
                          closed=False), stroke(line, 0.06))
        return
    # 圆形眼白
    r = 0.14 if e == "wide" else 0.125
    h = r * (1 - blink)
    if h < 0.02:
        c.drawPath(spline([(-0.12, -0.01), (0.0, 0.06), (0.12, -0.01)], closed=False), stroke(dark, 0.055))
        return
    eyeball = oval(0, 0, r, h)
    c.drawPath(eyeball, fill("#ffffff"))
    c.save()
    c.clipPath(eyeball, skia.ClipOp.kIntersect, True)
    pr = 0.075 * (pose.pupil if e == "wide" else 1.0)
    if style == "husky" and e != "wide":
        iris = "#57B7EC" if side > 0 else "#9A6531"
        c.drawPath(oval(lx * 1.2, ly * 1.2, 0.085, 0.085), fill(iris))
        c.drawPath(oval(lx * 1.2, ly * 1.2, 0.04, 0.04), fill(dark))
    else:
        c.drawPath(oval(lx * 1.3, ly * 1.3, pr, pr), fill(dark))
    c.drawPath(oval(lx * 1.3 - 0.03, ly * 1.3 - 0.035, 0.025, 0.025), fill("#ffffff"))
    c.drawPath(oval(0, -h, r * 1.2, h * 0.35), fill("#B8C4D0", 0.25, blur=0.02))
    c.restore()
    c.drawPath(eyeball, stroke(line, 0.035))


def _brows(c, sp, pose):
    style = sp.get("brows")
    if not style:
        return

    def one(side):
        bx = 0.33 + pose.turn * 0.2 * side
        by = -0.42 - pose.brow_y * 0.08
        ang = pose.brow * 18
        c.save()
        c.translate(bx, by)
        c.rotate(ang)
        if style == "dots":
            col = sp["cream"]
            c.drawPath(oval(0, 0, 0.115, 0.068), fill(col))
            c.drawPath(oval(0.01, 0.012, 0.115, 0.068), fill(sp["cream_d"], 0.5, blur=0.01))
            c.drawPath(oval(-0.01, -0.006, 0.105, 0.06), fill(col))
        elif style == "dots_w":
            c.drawPath(oval(0, 0, 0.11, 0.07), fill(sp["cream"]))
        elif style == "tufts":
            c.drawPath(spline([(-0.14, 0.03), (0.0, -0.05), (0.15, 0.0)], closed=False), stroke("#EFE6D6", 0.07))
        c.restore()

    sym(c, one)


def _nose_mouth(c, sp, pose):
    tx = pose.turn * 0.22
    line = sp["line"]
    cat = sp["mask"] == "cat"
    golden = sp["mask"] == "golden"
    # 口鼻部
    if not cat:
        mz = sp["cream"] if not golden else "#EFE4CF"
        my = 0.40 if not golden else 0.44
        rx, ry = (0.40, 0.29) if not golden else (0.44, 0.36)
        c.drawPath(oval(tx, my, rx, ry), fill(shade(mz, 0.35), 0.55, blur=0.05))
        if golden:
            c.drawPath(oval(tx, my, rx, ry), fill(mz, 0.9))
            c.drawPath(oval(tx, my + 0.1, rx * 0.9, ry * 0.6), fill("#D9CDB6", 0.4, blur=0.06))
    ny = 0.20 if not cat else 0.20
    if cat:
        nose = spline([(-0.07, 0.15), (0.07, 0.15), (0.0, 0.24)], tension=0.6)
        nose.offset(tx, 0)
        c.drawPath(nose, fill(sp["nose"]))
        c.drawPath(nose, stroke(line, 0.03))
    else:
        nose = spline([(-0.15, 0.13), (0.0, 0.11), (0.15, 0.13), (0.10, 0.25), (0.0, 0.30), (-0.10, 0.25)])
        nose.offset(tx, ny - 0.2)
        c.drawPath(nose, fill(sp["nose"]))
        c.drawPath(oval(tx - 0.05, ny - 0.04, 0.05, 0.028), fill("#ffffff", 0.55))
    # 嘴
    top = 0.30 if not cat else 0.25
    mo = pose.mouth
    talk = clamp(pose.talk)
    if pose.sleep:
        mo = "flat"
    if cat and mo in ("smile", "flat", "lazy") and talk < 0.06:
        mo = "cat"
    if robot_grin(sp, pose):
        _grin(c, tx, top, line)
        return
    open_amt = talk
    if mo == "open":
        open_amt = max(open_amt, 0.55)
    if mo == "o":
        open_amt = max(open_amt, 0.35)
    if mo == "grin":
        open_amt = max(open_amt, 0.35)
    c.drawLine(tx, top, tx, top + 0.07, stroke(line, 0.04))
    if open_amt > 0.06:
        h = 0.06 + 0.36 * open_amt
        wdt = 0.20 if mo != "o" else 0.11 + 0.05 * open_amt
        corner = {"smile": -0.04, "grin": -0.06, "frown": 0.05, "wavy": 0.02}.get(mo, 0.0)
        y0 = top + 0.07
        path = skia.Path()
        path.moveTo(tx - wdt, y0 + corner)
        path.cubicTo(tx - wdt * 0.6, y0 - 0.02, tx + wdt * 0.6, y0 - 0.02, tx + wdt, y0 + corner)
        path.cubicTo(tx + wdt * 0.9, y0 + h * 0.8, tx + wdt * 0.4, y0 + h, tx, y0 + h)
        path.cubicTo(tx - wdt * 0.4, y0 + h, tx - wdt * 0.9, y0 + h * 0.8, tx - wdt, y0 + corner)
        path.close()
        c.drawPath(path, fill("#5B1E22"))
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        c.drawPath(oval(tx, y0 + h * 1.02, wdt * 0.8, h * 0.45), fill("#F07D8C"))
        c.restore()
        c.drawPath(path, stroke(line, 0.04))
        if pose.tongue and mo != "o":
            tp = spline([(tx - 0.09, y0 + h * 0.7), (tx + 0.09, y0 + h * 0.7), (tx + 0.10, y0 + h + 0.18),
                         (tx, y0 + h + 0.24), (tx - 0.10, y0 + h + 0.18)])
            draw_shape(c, tp, "#F57F8F", line, 0.035, "#D9607A", (-0.02, -0.03))
            c.drawLine(tx, y0 + h * 0.8, tx, y0 + h + 0.12, stroke("#D9607A", 0.025))
    else:
        y = top + 0.07
        if mo in ("smile", "cat", "grin"):
            k = 0.06 if mo != "cat" else 0.04
            w2 = 0.17 if mo != "cat" else 0.12
            p = skia.Path()
            p.moveTo(tx - w2, y - k * 0.6)
            p.cubicTo(tx - w2 * 0.8, y + k * 1.2, tx - 0.03, y + k, tx, y)
            p.cubicTo(tx + 0.03, y + k, tx + w2 * 0.8, y + k * 1.2, tx + w2, y - k * 0.6)
            c.drawPath(p, stroke(line, 0.042))
        elif mo == "frown":
            p = skia.Path()
            p.moveTo(tx - 0.16, y + 0.07)
            p.cubicTo(tx - 0.12, y - 0.02, tx - 0.03, y - 0.0, tx, y)
            p.cubicTo(tx + 0.03, y, tx + 0.12, y - 0.02, tx + 0.16, y + 0.07)
            c.drawPath(p, stroke(line, 0.042))
        elif mo == "wavy":
            pts = [(tx - 0.18 + i * 0.06, y + 0.03 + (0.025 if i % 2 else -0.02)) for i in range(7)]
            c.drawPath(spline(pts, closed=False), stroke(line, 0.04))
        else:
            c.drawLine(tx - 0.12, y + 0.02, tx + 0.12, y + 0.02, stroke(line, 0.042))
        if pose.tongue:
            tp = spline([(tx - 0.07, y + 0.02), (tx + 0.07, y + 0.02), (tx + 0.08, y + 0.17), (tx, y + 0.22),
                         (tx - 0.08, y + 0.17)])
            draw_shape(c, tp, "#F57F8F", line, 0.03, "#D9607A", (-0.02, -0.03))
    if pose.drool > 0:
        d = pose.drool * (0.12 + 0.05 * wave(pose.t, 1.3))
        c.drawPath(spline([(tx + 0.13, top + 0.12), (tx + 0.16, top + 0.12 + d), (tx + 0.10, top + 0.12 + d)]),
                   fill("#BFE7FF", 0.85))


def robot_grin(sp, pose):
    return sp.get("robot") and True


def _grin(c, tx, top, line):
    """玩具猫：咧到耳根的固定笑容。"""
    y = top + 0.05
    p = skia.Path()
    p.moveTo(tx - 0.42, y - 0.08)
    p.cubicTo(tx - 0.30, y + 0.24, tx + 0.30, y + 0.24, tx + 0.42, y - 0.08)
    p.cubicTo(tx + 0.25, y + 0.05, tx - 0.25, y + 0.05, tx - 0.42, y - 0.08)
    p.close()
    c.drawPath(p, fill("#3A1518"))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    for i in range(-5, 6):
        c.drawRect(skia.Rect.MakeXYWH(tx + i * 0.07 - 0.025, y - 0.1, 0.05, 0.13), fill("#F5F2E8"))
    c.restore()
    c.drawPath(p, stroke(line, 0.035))


def _whiskers(c, sp, pose):
    if sp["mask"] != "cat":
        return
    tx = pose.turn * 0.2

    def one(side):
        for i, (dy, ang) in enumerate(((0.26, -8), (0.33, 2), (0.40, 12))):
            x0 = 0.28 + tx * side
            c.drawPath(spline([(x0, dy), (x0 + 0.35, dy + ang * 0.004 - 0.02), (x0 + 0.68, dy + ang * 0.012)],
                              closed=False), stroke("#5A3A22", 0.018, 0.7))
    sym(c, one)


def _extras_face(c, sp, pose):
    if pose.blush > 0:
        def b(side):
            c.drawPath(oval(0.66 + pose.turn * 0.15 * side, 0.24, 0.17, 0.09), fill("#FF8A9A", 0.4 * pose.blush,
                                                                                    blur=0.04))
        sym(c, b)
    if pose.tears > 0:
        def tr(side):
            x = 0.38 + pose.turn * 0.2 * side
            k = pose.tears
            c.drawPath(spline([(x - 0.07, 0.0), (x + 0.07, 0.0), (x + 0.10, 0.25 + 0.5 * k), (x - 0.10, 0.25 + 0.5 * k)],
                              tension=0.6), fill("#9FD8FF", 0.75))
            ph = (pose.t * 1.7 + side * 0.3) % 1.0
            c.drawPath(oval(x + 0.05, 0.1 + ph * 0.9, 0.05, 0.07), fill("#BFE6FF", 0.9 * (1 - ph)))
        sym(c, tr)
    if pose.sweat > 0:
        k = pose.sweat
        p = spline([(0.88, -0.62), (0.97, -0.40), (0.92, -0.32), (0.84, -0.32), (0.80, -0.40)], tension=0.8)
        c.drawPath(p, fill("#A9DDFF", 0.9 * k))
        c.drawPath(p, stroke("#4C8CC2", 0.03, k))
        c.drawPath(oval(0.86, -0.40, 0.02, 0.03), fill("#ffffff", 0.9 * k))


def _headband(c, sp, pose):
    if not sp.get("headband"):
        return
    head = _head_path(sp)
    band = skia.Path()
    band.moveTo(-1.2, -0.70)
    band.cubicTo(-0.5, -0.80, 0.5, -0.80, 1.2, -0.70)
    band.lineTo(1.2, -0.50)
    band.cubicTo(0.5, -0.60, -0.5, -0.60, -1.2, -0.50)
    band.close()
    band = skia.Op(band, head, skia.PathOp.kIntersect_PathOp)
    draw_shape(c, band, "#E23B3B", sp["line"], 0.035, "#B02424", (0.0, -0.05))
    # 飘带
    sw = wave(pose.t, 0.9) * 0.08
    for k, dy in ((0, 0.0), (1, 0.12)):
        p = spline([(0.95, -0.62 + dy), (1.25, -0.6 + dy + sw), (1.55, -0.50 + dy - sw), (1.50, -0.40 + dy - sw),
                    (1.22, -0.48 + dy + sw), (0.95, -0.52 + dy)], tension=0.8)
        draw_shape(c, p, "#E23B3B", sp["line"], 0.03, "#B02424", (0, -0.04))


def draw_head(c, sp, pose):
    head = _head_path(sp)
    _ears(c, sp, pose, front=False)
    base = sp["fur"] if sp["mask"] != "husky" else sp["cream"]
    base_d = sp["fur_d"] if sp["mask"] != "husky" else sp["cream_d"]
    draw_shape(c, head, base, None, 0, base_d, (-0.06, -0.09))
    _mask(c, sp, pose, head)
    c.drawPath(head, stroke(sp["line"], OW))
    _headband(c, sp, pose)
    _brows(c, sp, pose)
    sym(c, lambda side: _eye(c, sp, pose, side))
    _nose_mouth(c, sp, pose)
    _whiskers(c, sp, pose)
    _extras_face(c, sp, pose)
    _ears(c, sp, pose, front=True)
    if sp.get("robot"):
        # 接缝和指示灯
        c.drawPath(spline([(-0.9, 0.42), (-0.4, 0.62), (0.4, 0.62), (0.9, 0.42)], closed=False),
                   stroke("#8A5A30", 0.02, 0.6))
        on = 1.0 if (pose.t * 2) % 1.0 < 0.5 else 0.25
        c.drawPath(oval(0, -0.62, 0.05, 0.05), fill("#FF2B2B", on))
        c.drawPath(oval(0, -0.62, 0.14, 0.14), fill("#FF2B2B", 0.4 * on, blur=0.06))
        c.drawPath(oval(-0.45, -0.45, 0.12, 0.05), fill("#ffffff", 0.45))
    if pose.sleep:
        k = (pose.t * 0.5) % 1.0
        for i in range(3):
            kk = (k + i / 3) % 1.0
            draw_text(c, "Z", 0.9 + kk * 0.6, -0.9 - kk * 0.9, size=0.25 + kk * 0.2, name="kuaile",
                      color="#DDE6FF", a=(1 - kk) * 0.9, outline="#2A3050", ow=0.03)


# ---------------------------------------------------------------- 身体
def _leg(c, sp, x, top, bottom, w, color, color_d, angle=0.0, paw=True):
    c.save()
    c.translate(x, top)
    c.rotate(angle)
    length = bottom - top
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -w * 0.3, w / 2, length), w / 2, w / 2))
    draw_shape(c, p, color, sp["line"], OW, color_d, (-0.04, -0.03))
    if paw:
        pp = oval(0, length - 0.02, w * 0.62, w * 0.36)
        draw_shape(c, pp, sp["cream"], sp["line"], OW * 0.9, sp["cream_d"], (-0.02, -0.03))
        for dx in (-0.06, 0.06):
            c.drawLine(dx * w / 0.3, length - 0.06, dx * w / 0.3, length + 0.03, stroke(sp["line"], 0.025, 0.7))
    c.restore()


def _tail(c, sp, pose):
    t = sp["tail"]
    wag = pose.tail
    line = sp["line"]
    c.save()
    if t == "curl":
        c.translate(0.72, -0.55)
        c.rotate(wag * 14)
        c.translate(-0.72, 0.55)
        ring = skia.Path()
        ring.addCircle(0.95, -1.0, 0.36)
        c.drawPath(ring, stroke(line, 0.34))
        c.drawPath(ring, stroke(sp["fur"], 0.25))
        inner = skia.Path()
        inner.addArc(skia.Rect.MakeLTRB(0.66, -1.29, 1.24, -0.71), 200, 220)
        c.drawPath(inner, stroke(sp["cream"], 0.11))
    elif t == "bushy":
        c.translate(0.70, -0.5)
        c.rotate(wag * 18)
        c.translate(-0.70, 0.5)
        p = spline([(0.62, -0.42), (1.05, -0.65), (1.28, -1.10), (1.12, -1.55), (0.85, -1.62), (0.92, -1.25),
                    (0.95, -0.92), (0.66, -0.72)])
        draw_shape(c, p, sp["fur"], line, OW, sp["fur_d"], (-0.05, -0.05))
        c.drawPath(spline([(0.90, -1.45), (1.06, -1.52), (1.10, -1.30)], closed=False), stroke(sp["cream"], 0.12))
    elif t == "fluff":
        c.translate(0.6, -0.4)
        c.rotate(wag * 25)
        p = spline([(0.0, 0.0), (0.30, -0.25), (0.42, -0.10), (0.25, 0.10)])
        draw_shape(c, p, sp["fur"], line, OW, sp["fur_d"], (-0.03, -0.03))
    elif t == "feather":
        c.translate(0.70, -0.30)
        c.rotate(wag * 16)
        p = spline([(0.0, 0.0), (0.45, -0.20), (0.85, -0.55), (1.05, -0.95), (0.95, -1.0), (0.70, -0.62),
                    (0.38, -0.40), (0.05, -0.20)])
        draw_shape(c, p, sp["fur"], line, OW, sp["fur_d"], (-0.03, -0.04))
        c.drawPath(spline([(0.25, -0.22), (0.60, -0.45), (0.88, -0.80)], closed=False), stroke(sp["cream"], 0.07, 0.7))
    elif t == "cat":
        sw = wag * 0.25
        pts = [(0.45, -0.12), (0.95, -0.15), (1.25, -0.55 + sw * 0.3), (1.15 + sw, -1.05), (1.30 + sw * 1.5, -1.45)]
        p = spline(pts, closed=False)
        c.drawPath(p, stroke(line, 0.26))
        c.drawPath(p, stroke(sp["fur"], 0.17))
        meas = skia.PathMeasure(p, False)
        L = meas.getLength()
        for i in range(1, 6):
            pos, tan = meas.getPosTan(L * i / 6.2)
            nx, ny = -tan.y(), tan.x()
            c.drawLine(pos.x() - nx * 0.085, pos.y() - ny * 0.085, pos.x() + nx * 0.085, pos.y() + ny * 0.085,
                       stroke(sp["stripes"], 0.06, 0.9, cap="butt"))
        end, _ = meas.getPosTan(L)
        c.drawCircle(end.x(), end.y(), 0.085, fill(sp["stripes"]))
    c.restore()


def draw_body_sit(c, sp, pose, kind="sit"):
    line = sp["line"]
    fur, fur_d, cream, cream_d = sp["fur"], sp["fur_d"], sp["cream"], sp["cream_d"]
    if kind == "short":
        body_pts = [(0, -1.45), (0.46, -1.40), (0.78, -1.12), (0.94, -0.55), (0.90, -0.12), (0.62, 0.0), (0, 0.0)]
        bib = [(0, -1.46), (0.40, -1.36), (0.50, -0.95), (0.40, -0.55), (0.18, -0.35), (0, -0.30)]
        sh, leg_w, haunch = -0.62, 0.30, (0.66, -0.26, 0.34, 0.27)
    elif kind == "cat":
        body_pts = [(0, -1.62), (0.32, -1.58), (0.54, -1.28), (0.68, -0.72), (0.76, -0.22), (0.62, 0.0), (0, 0.0)]
        bib = [(0, -1.62), (0.28, -1.55), (0.33, -1.15), (0.26, -0.70), (0.12, -0.5), (0, -0.46)]
        sh, leg_w, haunch = -1.05, 0.21, (0.56, -0.28, 0.27, 0.30)
    else:
        body_pts = [(0, -1.70), (0.42, -1.66), (0.70, -1.40), (0.86, -0.95), (0.98, -0.45), (0.95, -0.12),
                    (0.70, 0.0), (0, 0.0)]
        bib = [(0, -1.68), (0.34, -1.60), (0.43, -1.20), (0.36, -0.75), (0.18, -0.45), (0, -0.40)]
        sh, leg_w, haunch = -0.95, 0.30, (0.70, -0.30, 0.35, 0.32)
    tx = pose.turn * 0.15
    # 后腿
    hx, hy, hrx, hry = haunch

    def hl(side):
        p = oval(hx, hy, hrx, hry)
        draw_shape(c, p, fur, line, OW, fur_d, (-0.05, -0.06))
        pp = oval(hx + 0.08, -0.05, hrx * 0.62, 0.09)
        draw_shape(c, pp, cream, line, OW * 0.9, cream_d, (-0.02, -0.03))
    sym(c, hl)
    body = spline(mirror_pts(body_pts))
    draw_shape(c, body, fur, None, 0, fur_d, (-0.07, -0.08))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    bibp = spline([(x + tx, y) for x, y in mirror_pts(bib)])
    if kind == "fluffy":
        pts = mirror_pts(bib)
        wavy = []
        for i, (x, y) in enumerate(pts):
            wavy.append((x * (1.08 if i % 2 else 0.95) + tx, y))
        bibp = spline(wavy, tension=1.3)
    draw_shape(c, bibp, cream, None, 0, cream_d, (-0.03, -0.06))
    c.restore()
    c.drawPath(body, stroke(line, OW))
    if sp.get("robot") is None and kind == "cat":
        # 项圈 + 管理员牌
        c.drawPath(spline([(-0.40, -1.56), (0.0, -1.46), (0.40, -1.56)], closed=False), stroke("#2C5AA0", 0.09))
    # 前腿
    for side, ang in ((1, pose.arm_r), (-1, pose.arm_l)):
        if ang > 60:
            continue
        legc = cream if sp["mask"] in ("shiba", "corgi", "cat") else fur
        legd = cream_d if sp["mask"] in ("shiba", "corgi", "cat") else fur_d
        _leg(c, sp, side * 0.30 * (0.75 if kind == "cat" else 1.0) + tx * 0.5, sh, -0.06, leg_w, legc, legd,
             angle=-side * ang)
    if kind == "cat" and not sp.get("robot"):
        c.drawPath(oval(0.05, -1.43, 0.11, 0.13), fill("#F2C14E"))
        c.drawPath(oval(0.05, -1.43, 0.11, 0.13), stroke("#8A6A20", 0.025))
        c.drawPath(oval(0.02, -1.47, 0.04, 0.03), fill("#ffffff", 0.7))
    return sh


def draw_raised_arms(c, sp, pose, sh, head_y):
    """抬起的前爪（挥手、捂嘴、捂眼）画在头的前面。"""
    for side, ang in ((1, pose.arm_r), (-1, pose.arm_l)):
        if ang <= 60:
            continue
        legc = sp["cream"] if sp["mask"] in ("shiba", "corgi", "cat") else sp["fur"]
        legd = sp["cream_d"] if sp["mask"] in ("shiba", "corgi", "cat") else sp["fur_d"]
        _leg(c, sp, side * 0.30, sh, sh + 0.9, 0.30, legc, legd, angle=-side * ang)


def draw_body_swole(c, sp, pose):
    """大壮：直立的肌肉柴。flex=1 时双臂弯举秀肌肉。"""
    line = sp["line"]
    fur, fur_d, cream, cream_d = sp["fur"], sp["fur_d"], sp["cream"], sp["cream_d"]
    walk = pose.walk

    # 腿
    def leg(side):
        sw = 0 if walk is None else math.sin(walk * 2 * math.pi + (0 if side > 0 else math.pi)) * 12
        c.save()
        c.translate(0.42, -1.25)
        c.rotate(sw * side)
        p = spline([(-0.28, 0.0), (0.30, 0.0), (0.32, 0.65), (0.26, 1.18), (-0.24, 1.18), (-0.30, 0.65)], tension=0.7)
        draw_shape(c, p, fur, line, OW, fur_d, (-0.05, -0.05))
        foot = oval(0.05, 1.20, 0.34, 0.12)
        draw_shape(c, foot, cream, line, OW, cream_d, (-0.02, -0.03))
        c.restore()
    sym(c, leg)
    # 躯干
    torso_pts = [(0, -2.78), (0.55, -2.76), (1.08, -2.52), (1.12, -2.10), (0.86, -1.72), (0.58, -1.32),
                 (0.50, -1.10), (0, -1.06)]
    torso = spline(mirror_pts(torso_pts))
    draw_shape(c, torso, fur, None, 0, fur_d, (-0.08, -0.08))
    c.save()
    c.clipPath(torso, skia.ClipOp.kIntersect, True)
    chest = spline(mirror_pts([(0, -2.74), (0.42, -2.70), (0.62, -2.30), (0.48, -1.70), (0.30, -1.20), (0, -1.10)]))
    draw_shape(c, chest, cream, None, 0, cream_d, (-0.04, -0.07))

    def pec(side):
        c.drawPath(spline([(0.04, -2.05), (0.30, -1.94), (0.56, -2.06), (0.62, -2.30)], closed=False),
                   stroke(cream_d, 0.05))
        for i in range(3):
            y = -1.80 + i * 0.20
            c.drawPath(oval(0.13, y, 0.10, 0.075), stroke(cream_d, 0.035))
    sym(c, pec)
    c.restore()
    c.drawPath(torso, stroke(line, OW))

    # 胳膊
    def arm(side):
        flex = pose.flex
        a_up = lerp(18, 95, flex)
        a_lo = lerp(8, -100, flex)
        if side < 0:
            a_up = lerp(18, 95, flex) if pose.arm_l == 0 else pose.arm_l
        c.save()
        c.translate(1.00, -2.42)
        c.rotate(-a_up)
        up = spline([(-0.26, -0.10), (0.20, -0.18), (0.36, 0.20), (0.30, 0.78), (-0.16, 0.85), (-0.30, 0.40)])
        draw_shape(c, up, fur, line, OW, fur_d, (-0.05, -0.05))
        c.translate(0.06, 0.78)
        c.rotate(a_lo)
        lo = spline([(-0.20, 0.0), (0.22, 0.0), (0.20, 0.62), (-0.16, 0.62)], tension=0.8)
        draw_shape(c, lo, fur, line, OW, fur_d, (-0.04, -0.04))
        fist = oval(0.02, 0.70, 0.22, 0.20)
        draw_shape(c, fist, cream, line, OW, cream_d, (-0.03, -0.03))
        c.restore()
    sym(c, arm)


def draw_critter(c, kind, x, y, u, pose: Pose):
    sp = SPECIES[kind]
    c.save()
    jx = jy = 0.0
    if pose.tremble:
        jx = math.sin(pose.t * 71.0) * 0.025 * pose.tremble
        jy = math.cos(pose.t * 53.0) * 0.012 * pose.tremble
    c.translate(x, y)
    c.scale(u, u)
    if pose.alpha < 1.0:
        c.saveLayerAlpha(None, int(clamp(pose.alpha) * 255))
    # 地面阴影
    c.drawPath(oval(0, 0.0, 1.05 if kind != "dazhuang" else 1.2, 0.16), fill("#000000", 0.28, blur=0.07))
    walk = pose.walk
    hop = 0.0
    if walk is not None:
        hop = -abs(math.sin(walk * math.pi)) * 0.18
    c.translate(jx, jy + hop + pose.bob)
    if pose.flip:
        c.scale(-1, 1)
    c.skew(pose.lean * 0.15, 0)
    sq = pose.squash
    c.scale(1 + sq * 0.12, 1 - sq * 0.12)
    look = pose.look
    if pose.flip:
        pose = pose.copy(look=(-look[0], look[1]), turn=pose.turn)
    if sp["body"] == "swole":
        draw_body_swole(c, sp, pose)
        sh = -2.42
    else:
        _tail(c, sp, pose)
        sh = draw_body_sit(c, sp, pose, sp["body"])
    hy = sp["head_y"]
    c.save()
    c.translate(pose.turn * 0.08, hy + math.sin(pose.t * 2.2) * 0.012)
    c.rotate(pose.tilt)
    s = sp["head_s"]
    c.scale(s, s)
    draw_head(c, sp, pose)
    c.restore()
    if sp["body"] != "swole":
        draw_raised_arms(c, sp, pose, sh, hy)
    if pose.mark:
        _mark(c, pose.mark, hy, pose.t)
    if pose.alpha < 1.0:
        c.restore()
    c.restore()


def _mark(c, mark, hy, t):
    """头顶的漫画符号：! ? 💧 ♪ 等。"""
    y = hy - 1.55
    if mark == "!":
        draw_text(c, "!", 0.95, y + 0.3, size=0.9, name="kuaile", color="#FF4D4D", outline="#5A1010", ow=0.06)
    elif mark == "?":
        draw_text(c, "?", 0.95, y + 0.3, size=0.8, name="kuaile", color="#FFD24D", outline="#5A4010", ow=0.06)
    elif mark == "!?":
        draw_text(c, "!?", 0.95, y + 0.3, size=0.8, name="kuaile", color="#FF7A4D", outline="#5A1010", ow=0.06)
    elif mark == "heart":
        k = (t * 0.8) % 1.0
        draw_text(c, "♥", 0.9, y + 0.3 - k * 0.3, size=0.6, name="sans", color="#FF6B8A", a=1 - k * 0.5)
    elif mark == "anger":
        p = skia.Path()
        for a in range(4):
            ang = a * math.pi / 2 + 0.6
            p.moveTo(0.9 + math.cos(ang) * 0.08, y + 0.2 + math.sin(ang) * 0.08)
            p.lineTo(0.9 + math.cos(ang) * 0.22, y + 0.2 + math.sin(ang) * 0.22)
        c.drawPath(p, stroke("#E33", 0.07))


# ---------------------------------------------------------------- 鹦鹉阿福
def draw_parrot(c, x, y, u, pose: Pose):
    c.save()
    c.translate(x, y)
    c.scale(u, u)
    if pose.flip:
        c.scale(-1, 1)
    if pose.alpha < 1:
        c.saveLayerAlpha(None, int(pose.alpha * 255))
    line = "#1F3A1F"
    bob = pose.bob + math.sin(pose.t * 3.0) * 0.02
    c.translate(0, bob)
    # 尾巴
    tail = spline([(-0.05, -0.30), (0.10, -0.30), (0.10, 0.12), (0.0, 0.22), (-0.08, 0.12)], tension=0.8)
    draw_shape(c, tail, "#2F8FD8", line, 0.04, "#2069A8", (-0.02, -0.03))
    # 身体
    body = spline([(0.0, -1.05), (0.32, -0.95), (0.42, -0.55), (0.34, -0.18), (0.08, -0.05), (-0.20, -0.12),
                   (-0.32, -0.50), (-0.28, -0.90)])
    draw_shape(c, body, "#4CBF55", line, 0.045, "#2F9A3A", (-0.04, -0.05))
    belly = spline([(0.05, -0.70), (0.26, -0.55), (0.24, -0.25), (0.05, -0.12), (-0.12, -0.28), (-0.10, -0.55)])
    c.drawPath(belly, fill("#C9E86A"))
    # 翅膀
    wing_a = pose.wing
    c.save()
    c.translate(-0.12, -0.70)
    c.rotate(-wing_a * 70)
    wing = spline([(0.0, 0.0), (0.18, 0.05), (0.15, 0.50), (-0.02, 0.72), (-0.14, 0.40)])
    draw_shape(c, wing, "#3AA845", line, 0.04, "#2A8A35", (-0.02, -0.03))
    c.drawPath(spline([(-0.08, 0.45), (0.02, 0.70), (0.10, 0.45)], closed=False), stroke("#2F8FD8", 0.07))
    c.restore()
    # 头
    head = oval(0.08, -1.10, 0.30, 0.28)
    draw_shape(c, head, "#4CBF55", line, 0.045, "#2F9A3A", (-0.03, -0.04))
    c.drawPath(oval(0.05, -1.30, 0.16, 0.08), fill("#E8473B"))
    c.drawPath(oval(0.18, -1.12, 0.10, 0.10), fill("#ffffff"))
    c.drawPath(oval(0.20 + pose.look[0] * 0.02, -1.12, 0.05, 0.055), fill("#111"))
    c.drawPath(oval(0.18, -1.15, 0.018, 0.018), fill("#fff"))
    # 嘴
    op = clamp(pose.talk) * 0.12
    up = spline([(0.28, -1.15), (0.48, -1.12), (0.52, -0.98), (0.44, -0.96 - op * 0.2), (0.32, -1.02)], tension=0.8)
    lo = spline([(0.30, -1.0 + op), (0.42, -0.97 + op), (0.38, -0.88 + op), (0.30, -0.92 + op)], tension=0.8)
    c.drawPath(lo, fill("#3B3B3B"))
    draw_shape(c, up, "#F2D9A0", line, 0.03, "#CDB070", (-0.01, -0.02))
    # 爪
    for dx in (-0.06, 0.12):
        c.drawLine(dx, -0.08, dx, 0.02, stroke("#9A8A7A", 0.05))
    if pose.alpha < 1:
        c.restore()
    c.restore()


# ---------------------------------------------------------------- 小天使 / 小恶魔 Cheems
def draw_tiny(c, x, y, u, pose: Pose, devil=False):
    c.save()
    draw_critter(c, "cheems", x, y, u, pose)
    c.translate(x, y)
    c.scale(u, u)
    hy = SPECIES["cheems"]["head_y"]
    if devil:
        for side in (1, -1):
            p = spline([(side * 0.45, hy - 0.75), (side * 0.75, hy - 1.35), (side * 0.72, hy - 0.70)], tension=0.5)
            draw_shape(c, p, "#C9302C", "#4A0E0E", 0.05)
        p = spline([(0.8, -0.6), (1.4, -0.4), (1.5, -0.9)], closed=False)
        c.drawPath(p, stroke("#4A0E0E", 0.09))
        c.drawPath(p, stroke("#C9302C", 0.05))
        c.drawPath(spline([(1.42, -1.05), (1.62, -0.82), (1.36, -0.82)], tension=0.4), fill("#C9302C"))
    else:
        c.drawPath(oval(0, hy - 1.15, 0.55, 0.13), stroke("#FFE36B", 0.09))
        c.drawPath(oval(0, hy - 1.15, 0.55, 0.13), stroke("#FFF5B0", 0.2, 0.35, blur=0.06))
        for side in (1, -1):
            p = spline([(side * 0.75, -1.5), (side * 1.45, -2.1), (side * 1.6, -1.6), (side * 1.25, -1.1)])
            draw_shape(c, p, "#FFFFFF", "#9AB0C8", 0.04, "#DDE7F3", (-0.03, -0.03))
    c.restore()


def blink_value(t, seed=0.0, period=3.7):
    """自然眨眼：每隔几秒眨一次，持续约 0.15 秒。"""
    ph = (t + seed * 1.37) % (period + seed % 1.3)
    if ph < 0.15:
        return math.sin(ph / 0.15 * math.pi)
    return 0.0
