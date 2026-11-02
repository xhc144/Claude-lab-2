"""一集视频的搭建器：页眉、板书、讲解文字、章节卡、片头、手推题、小结。

阅读时间的规则：S.say() 出现一句讲解后，紧接着的 S.play() 动画和阅读同时进行；
下一次 S.say() 之前，保证这句话至少显示了“按字数估算的阅读时间”，动画结束后也至少再停留一小会儿。
"""

import math

from . import text as T
from . import theme as C
from .core import Anim, FadeIn, FadeOut, Appear, flatten, Node, INF
from .widgets import Text, Rect, Line, Circle, Arc, Group, Card, GradLine, Band

READ_RATE = 4.6        # 每秒读几个汉字（技术内容，边读边看图）
READ_BASE = 1.3        # 每句话的基础停留
NOTE_RATE = 7.0
TAIL = 0.7             # 动画结束后至少再停留


class Scene:
    def __init__(self, meta):
        self.meta = meta
        self.t = 0.0
        self.objs = []
        self.under = []
        self.over = []
        self._registered = set()
        self.active = []
        self.read_until = 0.0
        self.anim_end = 0.0
        self.caption = None
        self.captions = []      # (t0, t1, 文字, 章节) —— 文字稿和检查用
        self.notes = []         # 当前板书条目
        self.note_log = []
        self.section_name = ""
        self.sections = []      # (t, 名称)
        self.layout = "panel"
        self.checks = []        # 检查画面重叠的时刻
        self.warnings = []
        self._build_chrome()

    # ------------------------------------------------------------ 基础
    def _register(self, o, t0):
        o.born = t0
        self._registered.add(o)
        if o not in self.objs:
            self.objs.append(o)

    def add(self, *objs):
        """注册到图解区，立刻可见（不渐变）。"""
        for o in objs:
            self._register(o, self.t)
        return objs[0] if len(objs) == 1 else objs

    def play(self, *anims, dur=0.7, lag=0.0, wait=True):
        anims = flatten(anims)
        end = self.t
        for i, a in enumerate(anims):
            end = max(end, a.apply(self, self.t + i * lag, dur))
        if anims:
            self.anim_end = max(self.anim_end, end)
        if wait:
            self.t = end
        return end

    def do(self, *anims):
        """瞬间生效。"""
        anims = flatten(anims)
        for a in anims:
            a.dur = 0.0
            a.apply(self, self.t, 0.0)

    def show(self, *objs, dur=0.6, lag=0.0, dy=0.0, scale=None):
        objs = flatten(objs)
        return self.play(*[FadeIn(o, dy=dy, scale=scale) for o in objs], dur=dur, lag=lag)

    def hide(self, *objs, dur=0.5):
        objs = flatten(objs)
        if objs:
            self.play(FadeOut(*objs), dur=dur)

    def wait(self, s=1.0):
        self.t += s

    def flush(self):
        """等当前这句讲解读完。"""
        need = self.read_until
        if self.anim_end > self.t - 1e-6 and self.caption is not None:
            need = max(need, self.anim_end + TAIL)
        self.t = max(self.t, need)

    def stage_objs(self):
        return [o for o in self.objs if o.alive(self.t) and o.tr["op"].last() > 0.01]

    def clear(self, keep=(), dur=0.5):
        keep = set(flatten(list(keep)))
        objs = [o for o in self.stage_objs() if o not in keep]
        if objs:
            self.play(FadeOut(*objs), dur=dur)

    # ------------------------------------------------------------ 版式元素
    def _build_chrome(self):
        m = self.meta
        uc = C.UNIT_COLORS.get(m.get("unit", 1), C.YELLOW)
        self.ucolor = uc
        hy = C.HEADER_H / 2 + 4
        hdr = Group(0, 0)
        # 单元标签（描边小胶囊）
        parts = m.get("unit_name", "").split(" ")
        chip_t = " · ".join(parts)
        cw = T.layout(chip_t, 21, None, None, "bold").w + 34
        hdr.add(Rect(48 + cw / 2, hy, cw, 36, fill=C.alpha(uc, 0.13), stroke=C.alpha(uc, 0.55), sw=1.5, r=18))
        hdr.add(Text(48 + cw / 2, hy, chip_t, size=21, color=uc, chain="bold"))
        x = 48 + cw + 26
        ep = f"第 {m['num']} 集"
        hdr.add(Text(x, hy, ep, size=24, color=C.DIM, anchor="lm"))
        x += T.layout(ep, 24, None).w + 20
        hdr.add(Rect(x, hy, 2, 26, fill=C.alpha(C.LINE2, 0.9), stroke=None, sw=0, r=1))
        hdr.add(Text(x + 20, hy, m["title"], size=30, anchor="lm", chain="bold"))
        self.sec_text = Text(C.W - 52, hy, "", size=24, color=C.DIM, anchor="rm")
        hdr.add(self.sec_text)
        hdr.add(GradLine(48, C.HEADER_H, C.W - 48, [(0.0, C.alpha(uc, 0.85)), (0.18, C.alpha(C.LINE2, 0.7)),
                                                    (1.0, C.alpha(C.LINE2, 0.0))], w=1.5))
        hdr.tr["op"].base = 0.0
        self.header = hdr
        self.over.append(hdr)

        px0, py0, px1, py1 = C.PANEL
        pan = Group(0, 0)
        pan.add(Rect((px0 + px1) / 2, (py0 + py1) / 2, px1 - px0, py1 - py0, fill=C.alpha(C.BG2, 0.92),
                     stroke=C.alpha(C.LINE, 0.9), sw=1.5, r=22, shadow=1.0))
        pan.add(Circle(px0 + 32, py0 + 34, 5, fill=uc, stroke=None, sw=0))
        pan.add(Text(px0 + 48, py0 + 34, "板书", size=22, color=C.DIM, anchor="lm", chain="bold"))
        pan.add(GradLine(px0 + 24, py0 + 62, px1 - 24, [(0.0, C.alpha(C.LINE2, 0.8)), (1.0, C.alpha(C.LINE2, 0.0))],
                         w=1.2))
        pan.tr["op"].base = 0.0
        self.panel = pan
        self.under.append(pan)

        cx0, cy0, cx1, cy1 = C.CAPTION
        cap = Group(0, 0)
        cap.add(Band(0, cy0 - 30, C.W, C.H - cy0 + 30, C.alpha(C.BG0, 0.0), C.alpha(C.BG0, 0.55)))
        cap.add(GradLine(48, cy0 - 14, C.W - 48, [(0.0, C.alpha(C.LINE2, 0.0)), (0.5, C.alpha(C.LINE2, 0.55)),
                                                  (1.0, C.alpha(C.LINE2, 0.0))], w=1.2))
        cap.tr["op"].base = 0.0
        self.capbar = cap
        self.under.insert(0, cap)

    def chrome(self, on=True, dur=0.6):
        objs = [self.header, self.capbar] + ([self.panel] if self.layout == "panel" else [])
        if on:
            self.play(*[o.to(op=1.0) for o in objs], dur=dur, wait=False)
        else:
            self.play(*[o.to(op=0.0) for o in objs], dur=dur, wait=False)

    def wide(self, dur=0.5):
        """收起板书，图解区占满宽度。"""
        if self.layout != "wide":
            self.flush()
            self.layout = "wide"
            self.clear_notes(dur=dur, wait=False)
            self.play(self.panel.to(op=0.0), dur=dur, wait=False)

    def narrow(self, dur=0.5):
        if self.layout != "panel":
            self.flush()
            self.layout = "panel"
            self.play(self.panel.to(op=1.0), dur=dur, wait=False)

    @property
    def stage(self):
        return C.STAGE if self.layout == "panel" else C.STAGE_WIDE

    @property
    def cx(self):
        s = self.stage
        return (s[0] + s[2]) / 2

    @property
    def cy(self):
        s = self.stage
        return (s[1] + s[3]) / 2

    # ------------------------------------------------------------ 讲解与板书
    def say(self, text, extra=0.0, hold=None):
        """下方出现一句讲解。之后的动画与阅读同时进行。"""
        self.flush()
        t0 = self.t
        if self.caption is not None:
            old = self.caption
            old.tr["op"].add(t0, 0.25, 0.0)
            old.dead = t0 + 0.3
            self.captions[-1][1] = t0
            self.checks.append(t0 - 0.05)
        cx0, cy0, cx1, cy1 = C.CAPTION
        maxw = cx1 - cx0
        L = T.layout(text, C.CAPTION_SIZE, None, maxw, "sans", 1.5)
        if len(L.lines) > 2:
            self.warn(f"讲解超过两行：{text}")
        cy = (cy0 + cy1) / 2
        cap = Group(0, 0)
        bar_h = max(1, len(L.lines)) * C.CAPTION_SIZE * 1.5 - C.CAPTION_SIZE * 0.55
        cap.add(Rect(cx0 - 26, cy, 4, bar_h, fill=C.alpha(self.ucolor, 0.9), stroke=None, sw=0, r=2))
        cap.add(Text(cx0, cy, text, size=C.CAPTION_SIZE, anchor="lm", maxw=maxw, lh=1.5))
        cap.tr["op"].base = 0.0
        self.over.append(cap)
        cap.born = t0 + 0.15
        self._registered.add(cap)
        cap.tr["op"].add(t0 + 0.15, 0.35, 1.0, "out")
        cap.tr["y"].add(t0 + 0.15, 0, 8)
        cap.tr["y"].add(t0 + 0.15, 0.35, 0, "out")
        self.caption = cap
        n = T.plain_len(text)
        need = hold if hold is not None else READ_BASE + n / READ_RATE + extra
        self.read_until = t0 + 0.3 + max(2.4, need)
        self.captions.append([t0, None, text, self.section_name])
        self.t = t0 + 0.45
        return cap

    def note(self, text, color=None, size=C.NOTE_SIZE, gap=18, indent=0, bullet=True, read=True):
        """板书追加一条：左边一道小色条，右边是文字。返回这一条（Group）。"""
        if self.layout == "wide":
            self.warn(f"板书收起时写了板书：{text}")
        px0, py0, px1, py1 = C.PANEL
        y = py0 + 80
        for n in self.notes:
            if n.tr["op"].last() > 0.01:
                y = max(y, n._bottom + gap)
        x0 = px0 + 30 + indent
        tx0 = x0 + (18 if bullet else 0)
        maxw = px1 - 26 - tx0
        L = T.layout(text, size, None, maxw, "sans", 1.4)
        item = Group(0, 0)
        if bullet:
            mk = color if color is not None else C.alpha(self.ucolor, 0.55)
            item.add(Rect(x0 + 2, y + size * 0.7, 4, size * 0.78, fill=mk, stroke=None, sw=0, r=2))
        item.add(Text(tx0, y, text, size=size, color=color or C.FG, anchor="lt", maxw=maxw, lh=1.4))
        item._bottom = y + L.h
        if item._bottom > py1 - 14:
            self.warn(f"板书超出：{text}")
        item.tr["op"].base = 0.0
        item.born = self.t
        self.under.append(item)
        self._registered.add(item)
        item.tr["op"].add(self.t, 0.45, 1.0, "out")
        item.tr["x"].add(self.t, 0, 14)
        item.tr["x"].add(self.t, 0.45, 0, "out")
        self.notes.append(item)
        self.note_log.append((self.t, text, self.section_name))
        if read:
            self.read_until = max(self.read_until, self.t + 0.5 + T.plain_len(text) / NOTE_RATE)
        return item

    def note_space(self, h=10):
        if self.notes:
            self.notes[-1]._bottom += h

    def clear_notes(self, dur=0.4, wait=False):
        live = [n for n in self.notes if n.tr["op"].last() > 0.01]
        for n in live:
            n.tr["op"].add(self.t, dur, 0.0)
            n.dead = self.t + dur + 0.01
        self.notes = []
        if wait:
            self.t += dur

    def warn(self, msg):
        self.warnings.append(f"t={self.t:.1f}s：{msg}")

    # ------------------------------------------------------------ 章节
    def section(self, title, keep=(), card=True):
        self.flush()
        if self.caption is not None:
            self.caption.tr["op"].add(self.t, 0.3, 0.0)
            self.caption.dead = self.t + 0.35
            self.captions[-1][1] = self.t
            self.checks.append(self.t - 0.05)
            self.caption = None
        self.clear(keep=keep, dur=0.5)
        self.clear_notes(dur=0.4)
        self.section_name = title
        self.sections.append((self.t, title))
        self.play(self.sec_text.to(text=f"{{f|{len(self.sections):02d}}}　{title}"), dur=0.5, wait=False)
        kept = [o for o in flatten(list(keep)) if o.alive(self.t)]
        if card and kept:
            self.play(*[o.to(op=0.08) for o in kept], dur=0.4, wait=False)
        if card:
            k = len(self.sections)
            num = Text(self.cx, self.cy - 92, f"{k:02d}", size=46, color=self.ucolor, chain="bold")
            tt = Text(self.cx, self.cy, title, size=60, chain="black", maxw=self.stage[2] - self.stage[0] - 120)
            ln = Line(self.cx - 70, self.cy + 64, self.cx + 70, self.cy + 64, color=self.ucolor, w=3, prog=0.0)
            self.play(FadeIn(num, dy=10), FadeIn(tt, dy=16), FadeIn(ln), ln.to(prog=1.0), dur=0.6)
            self.wait(1.0 + T.plain_len(title) / 8)
            self.play(FadeOut(num, tt, ln), dur=0.45)
            if kept:
                self.play(*[o.to(op=1.0) for o in kept], dur=0.5)
        self.read_until = self.t
        self.anim_end = self.t

    # ------------------------------------------------------------ 片头
    def cover(self, goal, prereq=(), series="信息竞赛算法理论进阶"):
        m = self.meta
        uc = self.ucolor
        cx = C.W / 2
        objs = []
        objs.append(Text(cx, 176, series, size=26, color=C.DIM))
        parts = m.get("unit_name", "").split(" ")
        chip_t = " · ".join(parts + [f"第 {m['num']} 集"])
        cw = T.layout(chip_t, 24, None, None, "bold").w + 44
        chip = Group(cx, 236)
        chip.add(Rect(0, 0, cw, 44, fill=C.alpha(uc, 0.13), stroke=C.alpha(uc, 0.6), sw=1.5, r=22))
        chip.add(Text(0, 0, chip_t, size=24, color=uc, chain="bold"))
        objs.append(chip)
        objs.append(Text(cx, 352, m["title"], size=92, chain="black"))
        if m.get("subtitle"):
            objs.append(Text(cx, 452, m["subtitle"], size=38, color=C.DIM))
        ln = Line(cx - 60, 510, cx + 60, 510, color=uc, w=3, prog=0.0)
        self.play(*[FadeIn(o, dy=14) for o in objs], FadeIn(ln), ln.to(prog=1.0), dur=0.8, lag=0.12)
        # 本集问题：一张卡片
        gw = 1360
        GL = T.layout(goal, 32, None, gw - 96)
        gh = GL.h + 96
        gy = 560 + gh / 2
        g = Group(cx, gy)
        g.add(Rect(0, 0, gw, gh, fill=C.alpha(C.BG2, 0.9), stroke=C.alpha(C.LINE, 0.9), sw=1.5, r=22, shadow=1.0))
        g.add(Text(-gw / 2 + 48, -gh / 2 + 30, "本集问题", size=22, color=uc, anchor="lt", chain="bold"))
        g.add(Text(-gw / 2 + 48, -gh / 2 + 70, goal, size=32, anchor="lt", maxw=gw - 96))
        self.play(FadeIn(g, dy=12), dur=0.6)
        rest = [g]
        need = 2.5 + T.plain_len(goal) / READ_RATE
        if prereq:
            py = gy + gh / 2 + 66
            lab = "用到的旧知识"
            chips = Group(0, py)
            widths = [T.layout(p, 24, None).w + 40 for p in prereq]
            lw = T.layout(lab, 24, None).w
            total = lw + 24 + sum(widths) + 16 * (len(widths) - 1)
            x = cx - total / 2
            chips.add(Text(x, 0, lab, size=24, color=C.DIM, anchor="lm"))
            x += lw + 24
            for p, w in zip(prereq, widths):
                chips.add(Rect(x + w / 2, 0, w, 44, fill=C.alpha(C.BG3, 0.9), stroke=C.alpha(C.LINE2, 0.8), sw=1.5,
                               r=22))
                chips.add(Text(x + w / 2, 0, p, size=24, color=C.FG))
                x += w + 16
            self.play(FadeIn(chips, dy=10), dur=0.6)
            rest.append(chips)
            need += T.plain_len("".join(prereq)) / 6
        self.wait(need)
        self.play(FadeOut(*objs, ln, *rest), dur=0.6)
        self.chrome(True)
        self.wait(0.3)
        self.read_until = self.t
        self.anim_end = self.t

    # ------------------------------------------------------------ 手推题
    def quiz(self, problem, think=15, w=None, h=None, title="手推题", x=None, y=None):
        """出一道手推题：题面卡片 + “暂停思考”倒计时。返回卡片（解答时可以留着或收起）。"""
        self.section("手推 / 建模题")
        w = w or (self.stage[2] - self.stage[0] - 40)
        L = T.layout(problem, 32, None, w - 68)
        h = h or (L.h + 120)
        x = x if x is not None else self.cx
        y = y if y is not None else self.stage[1] + 30 + h / 2
        card = Card(x, y, w, h, title, problem, color=self.ucolor, size=32, title_size=30)
        self.show(card, dy=20)
        self.say("先别急着看答案：按暂停，在纸上推一推。", hold=3.0)
        self.think(think, y=y + h / 2 + 110 if y + h / 2 + 110 < 800 else None)
        # 解答时把题目缩小放到左上角，腾出地方
        k = 0.6
        self.play(card.to(sc=k, x=self.stage[0] + 10 + w * k / 2, y=self.stage[1] + 4 + h * k / 2), dur=0.7)
        self.quiz_bottom = self.stage[1] + 4 + h * k
        return card

    def think(self, secs=15, x=None, y=None):
        """倒计时环。"""
        self.flush()
        x = x if x is not None else self.cx
        y = y if y is not None else self.stage[3] - 110
        ring_bg = Circle(x, y, 46, fill=C.alpha(C.BG2, 0.9), stroke=C.alpha(C.LINE, 0.9), sw=6)
        ring = Arc(x, y, 46, -90, 360, color=self.ucolor, w=6)
        num = Text(x, y, str(secs), size=34, chain="bold", color=self.ucolor)
        lab = Text(x, y + 82, "暂停思考", size=26, color=C.DIM, chain="bold")
        self.show(ring_bg, ring, num, lab, dur=0.4)
        t0 = self.t
        ring.tr["sweep"].add(t0, secs, 0.0, "lin")
        for k in range(1, secs + 1):
            num.tr["text"].add(t0 + k - 0.15, 0.15, str(secs - k) if secs - k > 0 else "✓", "lin")
        self.active.append((t0, t0 + secs))
        self.t = t0 + secs
        self.play(FadeOut(ring_bg, ring, num, lab), dur=0.4)
        self.read_until = self.t
        self.anim_end = self.t

    # ------------------------------------------------------------ 小结
    def recap(self, points, next_title=None):
        self.section("本集小结")
        self.wide()
        x0 = self.stage[0] + 90
        y = self.stage[1] + 46
        items = []
        for i, p in enumerate(points):
            dot = Group(x0 + 20, y + 24)
            dot.add(Circle(0, 0, 21, fill=C.alpha(self.ucolor, 0.14), stroke=C.alpha(self.ucolor, 0.7), sw=1.8))
            dot.add(Text(0, 0, f"{i + 1}", size=24, color=self.ucolor, chain="bold"))
            tx = Text(x0 + 66, y, p, size=32, anchor="lt", maxw=C.W - x0 - 66 - 120)
            L = T.layout(p, 32, None, tx.maxw)
            self.play(FadeIn(dot, dx=-10), FadeIn(tx, dx=-10), dur=0.5)
            self.wait(1.0 + T.plain_len(p) / READ_RATE)
            items += [dot, tx]
            y += L.h + 30
        if next_title:
            lab = "下一集"
            lw = T.layout(lab, 24, None, None, "bold").w + 36
            tw = T.layout(next_title, 32, None, None, "bold").w
            total = lw + 20 + tw
            ny = min(y + 60, 810)
            nt = Group(C.W / 2 - total / 2, ny)
            nt.add(Rect(lw / 2, 0, lw, 42, fill=C.alpha(self.ucolor, 0.13), stroke=C.alpha(self.ucolor, 0.6),
                        sw=1.5, r=21))
            nt.add(Text(lw / 2, 0, lab, size=24, color=self.ucolor, chain="bold"))
            nt.add(Text(lw + 20, 0, next_title, size=32, anchor="lm", chain="bold"))
            self.play(FadeIn(nt, dy=10), dur=0.5)
            self.wait(2.5 + T.plain_len(next_title) / READ_RATE)
            items.append(nt)
        self.wait(1.0)
        self.play(FadeOut(*items), dur=0.6)
        self.chrome(False, dur=0.8)
        self.wait(1.2)
        self.read_until = self.t
        self.anim_end = self.t

    def finish(self):
        self.flush()
        if self.caption is not None:
            self.caption.tr["op"].add(self.t, 0.3, 0.0)
            self.captions[-1][1] = self.t
            self.caption = None
            self.t += 0.4
        return self.t
