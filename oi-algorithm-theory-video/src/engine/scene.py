"""一集视频的搭建器：页眉、板书、讲解文字、章节卡、片头、手推题、小结。

阅读时间的规则：S.say() 出现一句讲解后，紧接着的 S.play() 动画和阅读同时进行；
下一次 S.say() 之前，保证这句话至少显示了“按字数估算的阅读时间”，动画结束后也至少再停留一小会儿。
"""

import math

from . import text as T
from . import theme as C
from .core import Anim, FadeIn, FadeOut, Appear, flatten, Node, INF
from .widgets import Text, Rect, Line, Circle, Arc, Group, Card

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
        hdr = Group(0, 0)
        hdr.add(Rect(C.W / 2, C.HEADER_H / 2, C.W, C.HEADER_H, fill=C.BG2, stroke=None, sw=0, r=0))
        hdr.add(Line(0, C.HEADER_H, C.W, C.HEADER_H, color=C.LINE, w=2))
        chip_t = m.get("unit_name", "")
        chip = Text(56, C.HEADER_H / 2, chip_t, size=24, color=C.BG, anchor="lm", chain="bold")
        cw = T.layout(chip_t, 24, None).w + 30
        hdr.add(Rect(41 + cw / 2, C.HEADER_H / 2, cw, 40, fill=uc, stroke=None, sw=0, r=20))
        hdr.add(chip)
        hdr.add(Text(41 + cw + 22, C.HEADER_H / 2,
                     f"{{d|第 {m['num']} 集}}  {m['title']}", size=28, anchor="lm", chain="bold"))
        self.sec_text = Text(C.W - 48, C.HEADER_H / 2, "", size=26, color=C.DIM, anchor="rm")
        hdr.add(self.sec_text)
        hdr.tr["op"].base = 0.0
        self.header = hdr
        self.over.append(hdr)

        px0, py0, px1, py1 = C.PANEL
        pan = Group(0, 0)
        pan.add(Rect((px0 + px1) / 2, (py0 + py1) / 2, px1 - px0, py1 - py0, fill=C.BG2,
                     stroke=C.alpha(C.LINE, 0.7), sw=2, r=14))
        pan.add(Text(px0 + 24, py0 + 26, "板书", size=22, color=C.FAINT, anchor="lm"))
        pan.tr["op"].base = 0.0
        self.panel = pan
        self.under.append(pan)

        cx0, cy0, cx1, cy1 = C.CAPTION
        cap = Group(0, 0)
        cap.add(Line(cx0, cy0 - 6, cx1, cy0 - 6, color=C.alpha(C.LINE, 0.8), w=2))
        cap.tr["op"].base = 0.0
        self.capbar = cap
        self.under.append(cap)

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
        cap = Text(cx0 + 10, (cy0 + cy1) / 2, text, size=C.CAPTION_SIZE, anchor="lm",
                   maxw=cx1 - cx0 - 20, lh=1.5)
        cap.tr["op"].base = 0.0
        self.over.append(cap)
        cap.born = t0 + 0.15
        self._registered.add(cap)
        cap.tr["op"].add(t0 + 0.15, 0.35, 1.0, "out")
        L = T.layout(text, C.CAPTION_SIZE, None, cx1 - cx0 - 20, "sans", 1.5)
        if len(L.lines) > 2:
            self.warn(f"讲解超过两行：{text}")
        self.caption = cap
        n = T.plain_len(text)
        need = hold if hold is not None else READ_BASE + n / READ_RATE + extra
        self.read_until = t0 + 0.3 + max(2.4, need)
        self.captions.append([t0, None, text, self.section_name])
        self.t = t0 + 0.45
        return cap

    def note(self, text, color=None, size=C.NOTE_SIZE, gap=16, indent=0, bullet=True, read=True):
        """板书追加一条。返回这条的 Text，之后可以改颜色或闪烁。"""
        px0, py0, px1, py1 = C.PANEL
        y = py0 + 58
        for n in self.notes:
            if n.tr["op"].last() > 0.01:
                y = max(y, n._bottom + gap)
        maxw = px1 - px0 - 48 - indent
        tx = Text(px0 + 24 + indent, y, text, size=size, color=color or C.FG, anchor="lt", maxw=maxw, lh=1.4)
        L = T.layout(text, size, None, maxw, "sans", 1.4)
        tx._bottom = y + L.h
        if tx._bottom > py1 - 14:
            self.warn(f"板书超出：{text}")
        tx.tr["op"].base = 0.0
        tx.born = self.t
        self.under.append(tx)
        self._registered.add(tx)
        tx.tr["op"].add(self.t, 0.45, 1.0, "out")
        tx.tr["x"].add(self.t, 0, px0 + 24 + indent + 14)
        tx.tr["x"].add(self.t, 0.45, px0 + 24 + indent, "out")
        self.notes.append(tx)
        self.note_log.append((self.t, text, self.section_name))
        if read:
            self.read_until = max(self.read_until, self.t + 0.5 + T.plain_len(text) / NOTE_RATE)
        return tx

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
        print(f"  [警告] {self.meta.get('code', '')} t={self.t:.1f}s：{msg}")

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
        self.play(self.sec_text.to(text=title), dur=0.5, wait=False)
        if card:
            k = len(self.sections)
            num = Text(self.cx, self.cy - 70, f"{k:02d}", size=40, color=self.ucolor, chain="mono")
            tt = Text(self.cx, self.cy, title, size=56, chain="bold")
            ln = Line(self.cx - 160, self.cy + 56, self.cx + 160, self.cy + 56, color=self.ucolor, w=3, prog=0.0)
            self.play(FadeIn(num, dy=10), FadeIn(tt, dy=16), FadeIn(ln), ln.to(prog=1.0), dur=0.6)
            self.wait(1.0 + T.plain_len(title) / 8)
            self.play(FadeOut(num, tt, ln), dur=0.45)
        self.read_until = self.t
        self.anim_end = self.t

    # ------------------------------------------------------------ 片头
    def cover(self, goal, prereq=(), series="信息竞赛算法理论进阶"):
        m = self.meta
        uc = self.ucolor
        objs = []
        objs.append(Text(C.W / 2, 210, series, size=30, color=C.DIM))
        objs.append(Text(C.W / 2, 268, f"{m.get('unit_name', '')} · 第 {m['num']} 集", size=30, color=uc))
        objs.append(Text(C.W / 2, 370, m["title"], size=72, chain="bold"))
        if m.get("subtitle"):
            objs.append(Text(C.W / 2, 462, m["subtitle"], size=36, color=C.FG))
        ln = Line(C.W / 2 - 260, 520, C.W / 2 + 260, 520, color=uc, w=3, prog=0.0)
        self.play(*[FadeIn(o, dy=14) for o in objs], FadeIn(ln), ln.to(prog=1.0), dur=0.8, lag=0.12)
        y = 600
        g = Text(C.W / 2, y, f"{{d|本集问题}}  {goal}", size=32, maxw=1500)
        self.play(FadeIn(g, dy=10), dur=0.6)
        rest = [g]
        need = 2.5 + T.plain_len(goal) / READ_RATE
        if prereq:
            y += 30 + T.layout(f"本集问题  {goal}", 32, None, 1500).h
            p = Text(C.W / 2, y + 20, "{d|用到的旧知识}  " + "　·　".join(prereq), size=28, color=C.FG, maxw=1500)
            self.play(FadeIn(p, dy=10), dur=0.6)
            rest.append(p)
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
        ring_bg = Circle(x, y, 46, fill=(0, 0, 0, 0), stroke=C.LINE, sw=6)
        ring = Arc(x, y, 46, -90, 360, color=self.ucolor, w=6)
        num = Text(x, y, str(secs), size=34, chain="mono", color=self.ucolor)
        lab = Text(x, y + 82, "暂停思考", size=26, color=C.DIM)
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
        x0 = self.stage[0] + 80
        y = self.stage[1] + 40
        items = []
        for i, p in enumerate(points):
            dot = Text(x0, y, f"{i + 1}", size=30, color=self.ucolor, chain="mono", anchor="lt")
            tx = Text(x0 + 46, y, p, size=32, anchor="lt", maxw=C.W - x0 - 46 - 120)
            L = T.layout(p, 32, None, tx.maxw)
            self.play(FadeIn(dot, dx=-10), FadeIn(tx, dx=-10), dur=0.5)
            self.wait(1.0 + T.plain_len(p) / READ_RATE)
            items += [dot, tx]
            y += L.h + 26
        if next_title:
            nt = Text(C.W / 2, min(y + 50, 820), f"{{d|下一集}}  {next_title}", size=30, color=C.FG)
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
