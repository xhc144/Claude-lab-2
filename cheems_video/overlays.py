"""画面上层：守则纸条、时间卡、字幕、片名、解说卡片、片尾字幕、暗角和胶片颗粒。"""
from __future__ import annotations

import math
import random

import skia

from gfx import (H, W, C, clamp, draw_shape, draw_text, ease_out, ease_out_back, fill, lerp, lin, make_noise_images,
                 oval, poly, rad, rrect, shade, spline, stroke, wave)
from sets import paw

NAME_COLORS = {
    "Cheems": "#FFB45C", "大橘": "#FF9A3C", "二哈": "#8EC9FF", "小柯": "#FF9D7A", "大壮": "#FF6B5C", "老金": "#F2CF6B",
    "主人": "#7FB6FF", "阿福": "#7DDB7D", "偷狗贼": "#C0C0C8", "王店长": "#FF9FB5", "？？？": "#C58BFF",
    "纸条": "#D8C8A8", "小恶魔Cheems": "#FF6060", "小天使Cheems": "#FFF0A0", "守则": "#E8E0C8",
}

OFFICIAL = ["一、晚上十点以后，请待在自己的房间里。走廊里，不会有任何住客。",
            "二、本旅馆只有一位夜班管理员，是一只橘猫。如果你同时看到两只橘猫，请立刻闭上眼睛，数到十。",
            "三、凌晨两点会送夜宵，夜宵只有狗粮。如果你闻到了肉骨头的香味，不要吃，那不是给你的。",
            "四、凌晨三点，隔壁的哈士奇可能会叫你的名字。不要回答。哈士奇不知道你的名字。",
            "五、天亮以后，如果主人来接你，请先看他手里有没有牵引绳。没有牵引绳的，不是你的主人。",
            "六、天亮之前，不要照镜子。",
            "七、本守则，全部为真。"]
HIDDEN = ["一、墙上的守则是管理员写的。管理员，不是猫。",
          "二、闻到肉骨头的香味，就说明又有一只狗，被它吃掉了。",
          "三、天亮以后，主人来接你，一定要跟他走。不管他有没有带牵引绳。",
          "四、想知道真相，就去走廊尽头的美容室，照一照镜子。"]

_NOISE = None


def wrap(text, f, width):
    lines, cur = [], ""
    for ch in text:
        if f.measureText(cur + ch) > width and cur:
            if ch in "，。！？、：；）》”":
                cur += ch
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


# ================================================================ 守则纸
def rules_paper(c, k, t, shown, hi=-1, hidden=False, cx=W / 2, cy=H / 2, scale=1.0, rot=-2.0):
    """k：出现进度（0~1）；shown：显示到第几条；hi：正在念的那条（-1 表示标题）。"""
    if k <= 0:
        return
    from gfx import font
    a = clamp(k)
    c.save()
    c.translate(cx, cy + (1 - ease_out(a)) * 120)
    c.rotate(rot + math.sin(t * 0.7) * 0.4)
    c.scale(scale * lerp(0.9, 1.0, ease_out(a)), scale * lerp(0.9, 1.0, ease_out(a)))
    pw, ph = (1240, 900) if not hidden else (1240, 660)
    c.saveLayerAlpha(None, int(a * 255))
    c.drawPath(rrect(-pw / 2 + 14, -ph / 2 + 22, pw, ph, 8), fill("#000000", 0.5, blur=18))
    if hidden:
        edge = []
        rnd = random.Random(8)
        for i in range(24):
            edge.append((-pw / 2 + i * pw / 23, -ph / 2 + rnd.uniform(-8, 8)))
        edge.append((pw / 2, ph / 2 - 60))
        for i in range(24):
            edge.append((pw / 2 - i * pw / 23, ph / 2 + rnd.uniform(-30, 10) - (40 if i < 8 else 0)))
        paper = poly(edge)
        c.drawPath(paper, fill(shader=lin((0, -ph / 2), (0, ph / 2), ["#D9C59A", "#C2A672"])))
        for (x, y, r) in ((-380, -250, 120), (420, 230, 160), (-100, 300, 90)):
            c.drawPath(oval(x, y, r, r * 0.7), fill("#8A6A3A", 0.18, blur=20))
        c.drawPath(paper, stroke("#6A5030", 3))
        title, lines, fn, col, fs = "真正的规则", HIDDEN, "hand", "#4A1E12", 50
    else:
        paper = rrect(-pw / 2, -ph / 2, pw, ph, 8)
        c.drawPath(paper, fill(shader=lin((0, -ph / 2), (0, ph / 2), ["#FBF4E2", "#EFE2C4"])))
        c.drawLine(-pw / 2, -ph / 6, pw / 2, -ph / 6 + 4, stroke("#D8C8A0", 3, 0.7))
        c.drawLine(-pw / 2 + 4, ph / 6, pw / 2, ph / 6 - 2, stroke("#D8C8A0", 3, 0.7))
        c.drawPath(paper, stroke("#B8A27A", 3))
        paw(c, pw / 2 - 90, ph / 2 - 80, 22, "#E39B4D", 0.85, ang=-12)
        title, lines, fn, col, fs = "月光宠物旅馆　夜间住客守则", OFFICIAL, "brush", "#2A2420", 40
    f = font(fn, fs)
    y = -ph / 2 + 100
    tc = "#7A1A10" if hidden else "#3A2010"
    draw_text(c, title, 0, y, size=fs + 14, name=fn, color=tc)
    if hi == -1 and shown >= 0:
        c.drawPath(rrect(-300, y - 60, 600, 80, 10), fill("#FFE08A", 0.0))
    y += 60
    for i, ln in enumerate(lines):
        rows = wrap(ln, f, pw - 160)
        vis = i < shown
        for r in rows:
            y += fs * 1.38
            if vis:
                if i == hi:
                    c.drawPath(rrect(-pw / 2 + 60, y - fs * 1.05, pw - 120, fs * 1.38, 8),
                               fill("#FFD36B" if not hidden else "#B0402A", 0.35 if not hidden else 0.22))
                draw_text(c, r, -pw / 2 + 80, y, size=fs, name=fn, color=col, align="left",
                          a=1.0 if i == hi or hi < -1 else 0.82)
        y += 10
    c.restore()
    c.restore()


# ================================================================ 时间卡
def time_card(c, text, sub, k, t):
    """k：卡片在本拍内的进度。"""
    a = clamp(min(k / 0.18, (1 - k) / 0.2))
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#05060C", a))
    if a <= 0:
        return
    jit = (random.Random(int(t * 30)).uniform(-4, 4) if (t * 7) % 1 < 0.12 else 0)
    draw_text(c, text, W / 2 + jit, H / 2 + 40, size=190, name="huangyou", color="#E8E2D2", a=a,
              glow=("#C8302A", 30, 0.55), spacing=6)
    if jit:
        draw_text(c, text, W / 2 + jit + 8, H / 2 + 40, size=190, name="huangyou", color="#FF3030", a=a * 0.35, spacing=6)
    if sub:
        draw_text(c, sub, W / 2, H / 2 + 130, size=48, name="kuaile", color="#B8B0A0", a=a)
    # 秒针
    r = 34
    cx, cy = W / 2, H / 2 - 170
    c.drawCircle(cx, cy, r, stroke("#E8E2D2", 4, a))
    ang = k * 6 * math.pi
    c.drawLine(cx, cy, cx + math.sin(ang) * r * 0.8, cy - math.cos(ang) * r * 0.8, stroke("#C8302A", 4, a))


# ================================================================ 字幕
def subtitle(c, name, text, a=1.0, y=H - 70):
    if not text or a <= 0:
        return
    from gfx import font
    f = font("sans", 50, 700)
    rows = wrap(text, f, W - 360)
    if len(rows) > 2:
        rows = wrap(text, font("sans", 44, 700), W - 300)
        size = 44
    else:
        size = 50
    total_h = len(rows) * size * 1.3
    y0 = y - total_h + size
    for i, r in enumerate(rows):
        draw_text(c, r, W / 2, y0 + i * size * 1.3, size=size, name="sans", weight=700, color="#FFFFFF", a=a,
                  outline="#101018", ow=9, oa=0.95)
    if name:
        col = NAME_COLORS.get(name, "#FFFFFF")
        f2 = font("kuaile", 40)
        wdt = f2.measureText(name) + 40
        bx, by = W / 2 - wdt / 2, y0 - size - 62
        c.drawPath(rrect(bx, by - 4, wdt, 52, 26), fill("#101018", 0.75 * a))
        c.drawPath(rrect(bx, by - 4, wdt, 52, 26), stroke(col, 3, a))
        draw_text(c, name, W / 2, by + 36, size=40, name="kuaile", color=col, a=a)


# ================================================================ 片名
def title_card(c, k, t):
    from chars import Pose, draw_critter
    a = clamp(min(k / 0.12, (1 - k) / 0.12))
    c.drawRect(skia.Rect.MakeWH(W, H), fill(shader=rad((W / 2, H / 2), 1100, ["#1A1F3A", "#05060C"])))
    rnd = random.Random(2)
    for i in range(90):
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1, 2.5),
                     fill("#FFFFFF", (0.3 + 0.4 * math.sin(t * 2 + i)) * a))
    c.drawCircle(W / 2 + 520, 230, 90, fill("#FFF1C2", a))
    c.drawCircle(W / 2 + 550, 205, 85, fill("#151A33", a))
    c.drawCircle(W / 2 + 520, 230, 220, fill("#FFF1C2", 0.12 * a, blur=40))
    s = ease_out_back(clamp(k / 0.25))
    c.save()
    c.translate(W / 2, H / 2 - 40)
    c.scale(s, s)
    draw_text(c, "Cheems", 0, -90, size=150, name="kuaile", color="#FFB45C", a=a, outline="#3A1A08", ow=12,
              glow=("#FF8A2A", 30, 0.5))
    draw_text(c, "规则怪谈", 0, 90, size=170, name="huangyou", color="#F2EBDC", a=a, outline="#2A0A0A", ow=10,
              glow=("#C8302A", 40, 0.7), spacing=10)
    c.restore()
    k2 = clamp((k - 0.25) / 0.2)
    draw_text(c, "—— 月光宠物旅馆 ——", W / 2, H / 2 + 200, size=64, name="brush", color="#E9C46A", a=a * k2)
    peek = clamp((k - 0.35) / 0.25)
    c.save()
    c.clipRect(skia.Rect.MakeWH(W, H))
    draw_critter(c, "cheems", 240, H + 230 - 300 * ease_out(peek), 110,
                 Pose(eye="wide", mouth="wavy", brow=1.0, ear=0.7, sweat=1.0, pupil=0.6, t=t, tremble=0.6,
                      look=(0.6, -0.3)))
    c.restore()
    for i in range(5):
        paw(c, 1500 + i * 70, H - 120 - i * 40, 18, "#E39B4D", 0.25 * a * k2, ang=-30)


# ================================================================ 解说卡片（真相）
def explain_card(c, kind, k, t, x=W * 0.70, y=H * 0.44):
    from chars import Pose, draw_critter, draw_parrot
    if k <= 0:
        return
    a = clamp(k)
    s = ease_out_back(a)
    c.save()
    c.translate(x + (1 - ease_out(a)) * 400, y)
    c.rotate(2.5 * math.sin(t * 0.8))
    c.scale(s, s)
    c.saveLayerAlpha(None, int(a * 255))
    cw, ch = 860, 620
    c.drawPath(rrect(-cw / 2 + 12, -ch / 2 + 18, cw, ch, 22), fill("#000", 0.45, blur=14))
    c.drawPath(rrect(-cw / 2, -ch / 2, cw, ch, 22), fill("#FBF4E2"))
    c.drawPath(rrect(-cw / 2, -ch / 2, cw, ch, 22), stroke("#B8A27A", 4))
    c.drawCircle(0, -ch / 2 + 6, 14, fill("#E2574C"))
    if kind == "map":
        draw_text(c, "他们进不来，只能骗你出去", 0, -ch / 2 + 70, size=46, name="kuaile", color="#3A2010")
        c.drawPath(rrect(-360, -150, 720, 300, 10), stroke("#3A2A20", 5))
        for i in range(5):
            dx = -300 + i * 120
            c.drawRect(skia.Rect.MakeXYWH(dx, -150, 90, 100), stroke("#3A2A20", 4))
            c.drawRect(skia.Rect.MakeXYWH(dx + 30, -66, 30, 16), fill("#8A5A33"))
            ar = (t * 0.8 + i * 0.2) % 1.0
            c.drawLine(dx + 45, -40, dx + 45, -40 + 70 * ar, stroke("#E2574C", 5))
            paw(c, dx + 45, -40 + 70 * ar, 7, "#E39B4D")
        c.drawRect(skia.Rect.MakeXYWH(-390, 0, 40, 110), fill("#7FB6FF"))
        draw_text(c, "警报", -370, 140, size=26, name="kuaile", color="#2C5AA0")
        c.drawLine(-430, 30, -320, 120, stroke("#E2574C", 9))
        c.drawLine(-430, 120, -320, 30, stroke("#E2574C", 9))
        c.drawRect(skia.Rect.MakeXYWH(360, -40, 20, 120), fill("#A7D3EE"))
        c.drawCircle(420, 20, 28, fill("#2C2F36"))
        c.drawPath(rrect(395, 45, 50, 70, 12), fill("#2C2F36"))
        draw_text(c, "窗外", 420, 150, size=26, name="kuaile", color="#3A2010")
        draw_text(c, "门下的狗洞：狗出得去，人进不来", 0, 245, size=34, name="kuaile", color="#6A4A2A")
    elif kind == "robot":
        draw_text(c, "第二只橘猫 = 遥控玩具猫", 0, -ch / 2 + 70, size=46, name="kuaile", color="#3A2010")
        draw_critter(c, "robocat", -210, 170, 70, Pose(t=t, glow=0.5 + 0.5 * math.sin(t * 6)))
        c.drawPath(rrect(10, -170, 330, 240, 14), fill("#0E2A14"))
        for i in range(3):
            ex = 70 + i * 100
            on = (i != 1)
            if on:
                c.drawCircle(ex - 16, -60, 10, fill("#B8FF9A"))
                c.drawCircle(ex + 16, -60, 10, fill("#B8FF9A"))
                c.drawCircle(ex, -60, 40, fill("#B8FF9A", 0.25, blur=12))
            else:
                c.drawLine(ex - 26, -60, ex - 6, -60, stroke("#3A6A3A", 4))
                c.drawLine(ex + 6, -60, ex + 26, -60, stroke("#3A6A3A", 4))
        draw_text(c, "夜视画面", 175, 40, size=26, name="sans", weight=700, color="#7AD87A")
        draw_text(c, "眼睛反光 = 被发现", 175, 140, size=34, name="kuaile", color="#C8302A")
        draw_text(c, "闭上眼睛 = 看不见你", 175, 200, size=34, name="kuaile", color="#2F7A3A")
    elif kind == "bone":
        draw_text(c, "肉骨头里下了药", 0, -ch / 2 + 70, size=46, name="kuaile", color="#3A2010")
        c.save()
        c.translate(-200, -20)
        c.rotate(-20)
        c.drawPath(rrect(-110, -22, 220, 44, 22), fill("#F2E6CC"))
        for sx in (-1, 1):
            for sy in (-1, 1):
                c.drawCircle(sx * 112, sy * 22, 30, fill("#F2E6CC"))
        c.drawPath(rrect(-110, -22, 220, 44, 22), stroke("#8A6A40", 4))
        c.restore()
        for i in range(3):
            px, py = -120 + i * 70, 110 + 15 * math.sin(t * 2 + i)
            c.save()
            c.translate(px, py)
            c.rotate(30)
            c.drawPath(rrect(-30, -13, 60, 26, 13), fill("#E2574C"))
            c.drawRect(skia.Rect.MakeXYWH(0, -13, 30, 26), fill("#FFFFFF"))
            c.drawPath(rrect(-30, -13, 60, 26, 13), stroke("#6A2A2A", 3))
            c.restore()
        draw_text(c, "→", 70, 30, size=80, name="sans", color="#3A2010")
        draw_critter(c, "dazhuang", 270, 200, 48, Pose(eye="closed", mouth="flat", sleep=True, t=t))
        draw_text(c, "睡得像块石头", 0, 255, size=36, name="kuaile", color="#6A4A2A")
    elif kind == "parrot":
        draw_text(c, "会学说话的阿福", 0, -ch / 2 + 70, size=46, name="kuaile", color="#3A2010")
        draw_parrot(c, -250, 190, 170, Pose(t=t, talk=0.5 + 0.5 * math.sin(t * 9)))
        for i, txt in enumerate(("“小柯~妈妈来了~”", "“Cheems~开门呀~”", "“我一定来接你”")):
            bx, by = 90, -130 + i * 95
            c.drawPath(rrect(bx - 190, by - 40, 380, 64, 30), fill("#E8F6E8"))
            c.drawPath(rrect(bx - 190, by - 40, 380, 64, 30), stroke("#4C9A4C", 3))
            draw_text(c, txt, bx, by + 6, size=30, name="kuaile", color="#2A5A2A")
        c.drawPath(rrect(-80, 175, 400, 70, 30), fill("#E3F1FF"))
        c.drawPath(rrect(-80, 175, 400, 70, 30), stroke("#4C82C6", 3))
        draw_text(c, "可二哈只会喊：芝士！", 120, 222, size=32, name="kuaile", color="#2C5AA0")
    c.restore()
    c.restore()


# ================================================================ 片尾
CREDITS = [
    ("big", "Cheems规则怪谈：月光宠物旅馆"),
    ("gap", ""),
    ("head", "原创动画短片"),
    ("line", "角色、剧情、分镜、画面、动画：全部原创，程序矢量绘制"),
    ("line", "配音：阿里云百炼 · 千问语音合成（qwen3-tts-flash）"),
    ("line", "配乐与音效：程序实时合成，原创"),
    ("line", "字体：站酷快乐体 · 站酷庆科黄油体 · 马善政 · 龙藏体 · 思源黑体（SIL OFL 开源授权）"),
    ("gap", ""),
    ("head", "出演"),
    ("line", "Cheems（柴犬）    大橘（橘猫管理员）    二哈（哈士奇）"),
    ("line", "小柯（柯基）    大壮（健身柴）    老金（金毛）"),
    ("line", "阿福（鹦鹉）    主人    王店长    偷狗贼"),
    ("gap", ""),
    ("small", "本片角色均为原创卡通形象，与任何真实动物、个人或作品无关。"),
    ("small", "养宠物请记得：外出寄养选正规机构，夜里关好门窗。"),
    ("gap", ""),
    ("quote", "如果你在夜里听见有人叫你的名字——"),
    ("quote", "先想一想：它，真的知道你的名字吗？"),
    ("gap", ""),
    ("big", "完"),
]


def credits(c, k, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#05060C"))
    total = 0
    for kind, _ in CREDITS:
        total += {"big": 130, "head": 90, "line": 66, "small": 56, "quote": 72, "gap": 60}[kind]
    y = H + 40 - k * (total + H * 0.55)
    for kind, txt in CREDITS:
        h = {"big": 130, "head": 90, "line": 66, "small": 56, "quote": 72, "gap": 60}[kind]
        y += h
        if -100 < y < H + 100 and txt:
            if kind == "big":
                draw_text(c, txt, W / 2, y, size=76, name="kuaile", color="#FFB45C", glow=("#FF8A2A", 20, 0.4))
            elif kind == "head":
                draw_text(c, txt, W / 2, y, size=50, name="kuaile", color="#E9C46A")
            elif kind == "line":
                draw_text(c, txt, W / 2, y, size=38, name="sans", weight=500, color="#E8E2D2")
            elif kind == "small":
                draw_text(c, txt, W / 2, y, size=32, name="sans", weight=400, color="#A8A090")
            elif kind == "quote":
                draw_text(c, txt, W / 2, y, size=48, name="brush", color="#D8C8A8")


# ================================================================ 后期
_VIG = None


def vignette(c, strength=0.55):
    """暗角：预先画好一张，按强度调透明度贴上去。"""
    global _VIG
    if _VIG is None:
        surf = skia.Surface(W, H)
        cc = surf.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        cc.drawRect(skia.Rect.MakeWH(W, H), fill(shader=rad((W / 2, H / 2), 1150, [("#000000", 0.0), ("#000000", 0.0),
                                                                                    ("#000000", 1.0)], [0, 0.55, 1.0])))
        _VIG = surf.makeImageSnapshot()
    p = skia.Paint()
    p.setAlphaf(clamp(strength))
    c.drawImage(_VIG, 0, 0, skia.SamplingOptions(), p)


def grain(c, t, amount=0.06):
    """胶片颗粒：几张预生成的半透明噪点图轮流贴。"""
    global _NOISE
    if _NOISE is None:
        import numpy as np
        rng = np.random.default_rng(7)
        _NOISE = []
        for _ in range(1):
            v = rng.integers(0, 2, (H, W), dtype=np.uint8) * 255
            a = (np.abs(rng.normal(0, 1, (H, W))) * 255 * 0.35).clip(0, 255).astype(np.uint8)
            rgb = (v.astype(np.uint16) * a // 255).astype(np.uint8)
            arr = np.stack([rgb, rgb, rgb, a], -1)
            _NOISE.append(skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType,
                                               alphaType=skia.kPremul_AlphaType))
    # 用同一张静态噪点（防渐变色带、带一点胶片质感），逐帧变化的噪点会让码率暴涨
    p = skia.Paint()
    p.setAlphaf(clamp(amount * 0.8))
    c.drawImage(_NOISE[0], 0, 0, skia.SamplingOptions(), p)


def onomatopoeia(c, text, x, y, size, color, k, t, rot=-8, outline="#2A1A10"):
    """漫画拟声字：弹出 + 抖动。"""
    if k <= 0 or k >= 1:
        return
    s = ease_out_back(clamp(k / 0.25))
    a = clamp((1 - k) / 0.25)
    c.save()
    c.translate(x + math.sin(t * 40) * 3, y + math.cos(t * 37) * 3)
    c.rotate(rot)
    c.scale(s, s)
    draw_text(c, text, 0, 0, size=size, name="kuaile", color=color, a=a, outline=outline, ow=size * 0.12)
    c.restore()


def thought_bubble(c, x, y, w, h, k, t, content=None):
    if k <= 0:
        return
    s = ease_out_back(clamp(k))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for i, (dx, dy, r) in enumerate(((-w * 0.42, h * 0.75, 14), (-w * 0.32, h * 0.58, 22))):
        c.drawCircle(dx, dy, r, fill("#FFFFFF"))
        c.drawCircle(dx, dy, r, stroke("#3A2A20", 4))
    pts = []
    n = 14
    for i in range(n):
        ang = i / n * 2 * math.pi
        pts.append((math.cos(ang) * w / 2 * (1 + 0.08 * math.sin(i * 2.7)), math.sin(ang) * h / 2 * (1 + 0.1 * math.cos(i * 1.9))))
    p = spline(pts, tension=1.4)
    c.drawPath(p, fill("#FFFFFF"))
    c.drawPath(p, stroke("#3A2A20", 5))
    if content:
        content(c, t)
    c.restore()


def drumstick(c, x, y, s, rot=0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawPath(rrect(30, -10, 70, 20, 10), fill("#F5EEDD"))
    c.drawPath(rrect(30, -10, 70, 20, 10), stroke("#8A6A40", 3))
    for dy in (-12, 12):
        c.drawCircle(104, dy, 13, fill("#F5EEDD"))
        c.drawCircle(104, dy, 13, stroke("#8A6A40", 3))
    meat = spline([(-95, 0), (-80, -50), (-30, -62), (20, -30), (40, -8), (40, 8), (20, 30), (-30, 62), (-80, 50)])
    draw_shape(c, meat, "#D9782E", "#5A2A10", 4, "#A84E18", (-8, -10))
    c.drawPath(oval(-50, -28, 26, 11), fill("#FFFFFF", 0.45))
    for i in range(3):
        c.drawLine(-70 + i * 30, 20, -55 + i * 30, 38, stroke("#A84E18", 4, 0.7))
    c.restore()


def bone_icon(c, x, y, s, rot=0, bitten=False):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    col = "#F2E6CC"
    c.drawPath(rrect(-60, -14, 120, 28, 14), fill(col))
    for sx in (-1, 1):
        for sy in (-1, 1):
            if bitten and sx > 0:
                continue
            c.drawCircle(sx * 62, sy * 14, 18, fill(col))
    if bitten:
        for i in range(4):
            c.drawCircle(60, -18 + i * 12, 9, fill("#000", 0.0))
        c.drawPath(spline([(55, -16), (66, -6), (58, 4), (66, 14)], closed=False), stroke("#C8A878", 5))
    c.drawPath(rrect(-60, -14, 120, 28, 14), stroke("#8A6A40", 4))
    c.restore()
