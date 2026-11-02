"""动画内核：属性轨道、场景树、时间线，以及逐帧渲染到 ffmpeg。

写一集的方式是“按时间顺序搭积木”：
    S.say("讲解文字")              # 下方出现一句讲解，并按字数留出阅读时间
    S.play(cell.to(fill=Y), ...)    # 在读这句话的同时播放动画
    S.note("板书")                  # 右侧板书追加一条
所有属性都记成“从某时刻开始、多长时间、变到什么值”的轨道段，渲染时按时间求值，
所以任何一帧都可以单独渲染；没有任何动画的帧直接复用上一帧，静止的阅读时间几乎不花渲染时间。
"""

import math
import subprocess
import sys
from bisect import bisect_right

import skia

from . import theme
from .theme import W, H, FPS

INF = float("inf")


# ------------------------------------------------------------------ 缓动
def _io(u):
    return 4 * u * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def _back(u):
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


EASES = {
    "lin": lambda u: u,
    "io": _io,
    "out": lambda u: 1 - (1 - u) ** 3,
    "in": lambda u: u ** 3,
    "back": _back,
    "bump": lambda u: math.sin(math.pi * u),
    "step": lambda u: 0.0 if u < 1 else 1.0,
}


def lerp(a, b, u):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return b if u >= 0.5 else a


# ------------------------------------------------------------------ 轨道
class Track:
    """分段的属性值。后开始的段覆盖先开始的段，所以 t 时刻的值只由“最后一个 t0 ≤ t 的段”决定。"""
    __slots__ = ("base", "t0s", "segs")

    def __init__(self, v):
        self.base = v
        self.t0s = []
        self.segs = []

    def at(self, t):
        i = bisect_right(self.t0s, t) - 1
        if i < 0:
            return self.base
        t0, t1, a, b, e, end = self.segs[i]
        if t >= t1:
            return end
        return lerp(a, b, EASES[e]((t - t0) / (t1 - t0)))

    def state(self, t):
        """给文字渐变用：返回 (旧值, 新值, 进度)。"""
        i = bisect_right(self.t0s, t) - 1
        if i < 0:
            return self.base, self.base, 1.0
        t0, t1, a, b, e, end = self.segs[i]
        if t >= t1:
            return end, end, 1.0
        return a, b, EASES[e]((t - t0) / (t1 - t0))

    def add(self, t0, dur, target, ease="io", bump=False):
        a = self.at(t0)
        dur = max(dur, 1e-4)
        end = a if bump else target
        i = bisect_right(self.t0s, t0)
        self.t0s.insert(i, t0)
        self.segs.insert(i, (t0, t0 + dur, a, target, "bump" if bump else ease, end))

    def last(self):
        return self.segs[-1][5] if self.segs else self.base


# ------------------------------------------------------------------ 动画
class Anim:
    """一个延迟执行的动画：apply(scene, t0, dur) 时才真正写入轨道。"""
    __slots__ = ("fn", "dur", "delay")

    def __init__(self, fn, dur=None, delay=0.0):
        self.fn = fn
        self.dur = dur
        self.delay = delay

    def apply(self, S, t0, dur):
        d = self.dur if self.dur is not None else dur
        self.fn(S, t0 + self.delay, d)
        return t0 + self.delay + d


def flatten(items):
    out = []
    for a in items:
        if a is None:
            continue
        if isinstance(a, (list, tuple)):
            out.extend(flatten(a))
        else:
            out.append(a)
    return out


# ------------------------------------------------------------------ 场景树
class Node:
    """所有画面元素的基类。(x, y) 是相对父节点的位置，op 是不透明度，sc 是缩放。"""

    def __init__(self, x=0.0, y=0.0, op=1.0, sc=1.0, **attrs):
        self.tr = {"x": Track(float(x)), "y": Track(float(y)), "op": Track(float(op)), "sc": Track(float(sc))}
        for k, v in attrs.items():
            self.tr[k] = Track(v)
        self.children = []
        self.parent = None
        self.born = -INF
        self.dead = INF
        self.z = 0

    # 属性
    def g(self, k, t):
        return self.tr[k].at(t)

    def setnow(self, **kw):
        """在搭建阶段直接改初始值（还没有任何动画时用）。"""
        for k, v in kw.items():
            if k in self.tr and not self.tr[k].segs:
                self.tr[k].base = v
            else:
                self.tr[k] = Track(v)
        return self

    def add(self, *kids):
        for k in kids:
            k.parent = self
            self.children.append(k)
        return kids[0] if len(kids) == 1 else kids

    def _check_alive(self, S, t0):
        r = self
        while r.parent is not None:
            r = r.parent
        if r in S._registered and r.dead < t0 - 0.05 and not getattr(r, "_warned_dead", False):
            r._warned_dead = True
            S.warn(f"动画作用在已经消失的对象上（{type(r).__name__}，消失于 {r.dead:.1f}s）——换小节时忘了 keep？")

    def to(self, dur=None, ease="io", delay=0.0, **kw):
        """把若干属性动画到目标值。"""
        def fn(S, t0, d):
            self._check_alive(S, t0)
            for k, v in kw.items():
                if k not in self.tr:
                    self.tr[k] = Track(v)
                self.tr[k].add(t0, d, v, ease)
        return Anim(fn, dur, delay)

    def bump(self, dur=None, delay=0.0, **kw):
        """属性先变到目标值再回到原值（闪烁、脉冲）。"""
        def fn(S, t0, d):
            for k, v in kw.items():
                if k not in self.tr:
                    self.tr[k] = Track(v)
                self.tr[k].add(t0, d, v, bump=True)
        return Anim(fn, dur, delay)

    def pulse(self, k=1.18, dur=0.5):
        return self.bump(dur=dur, sc=k)

    def alive(self, t):
        return self.born <= t < self.dead

    def draw(self, cv, t, op=1.0):
        if not (self.born <= t < self.dead):
            return
        o = op * self.tr["op"].at(t)
        if o <= 0.002:
            return
        x, y = self.local_xy(t)
        sc = self.tr["sc"].at(t)
        cv.save()
        cv.translate(x, y)
        if sc != 1.0:
            cv.scale(sc, sc)
        self.paint(cv, t, o)
        for c in self.children:
            c.draw(cv, t, o)
        cv.restore()

    def paint(self, cv, t, o):
        pass

    def local_xy(self, t):
        return self.tr["x"].at(t), self.tr["y"].at(t)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def abs_xy(self, t):
        """节点原点在画面上的绝对坐标。"""
        x, y = self.local_xy(t)
        p = self.parent
        while p is not None:
            s = p.tr["sc"].at(t)
            px, py = p.local_xy(t)
            x = px + s * x
            y = py + s * y
            p = p.parent
        return x, y

    def abs_scale(self, t):
        s, n = 1.0, self
        while n is not None:
            s *= n.tr["sc"].at(t)
            n = n.parent
        return s

    def visible(self, t):
        n = self
        while n is not None:
            if not (n.born <= t < n.dead) or n.tr["op"].at(t) <= 0.01:
                return False
            n = n.parent
        return True

    def bbox(self, t):
        """局部坐标下的包围盒 (x0, y0, x1, y1)，没有则返回 None。"""
        return None


class Group(Node):
    pass


# ------------------------------------------------------------------ 显示 / 隐藏
def FadeIn(*objs, dy=0.0, dx=0.0, scale=None, op=1.0):
    objs = flatten(objs)

    def fn(S, t0, d):
        for o in objs:
            if o.parent is None and o not in S._registered:
                S._register(o, t0)
            o.dead = INF
            o.tr["op"].add(t0, 0, 0.0)
            o.tr["op"].add(t0, d, op, "out")
            if dy or dx:
                x, y = o.tr["x"].at(t0), o.tr["y"].at(t0)
                o.tr["y"].add(t0, 0, y + dy)
                o.tr["x"].add(t0, 0, x + dx)
                o.tr["y"].add(t0, d, y, "out")
                o.tr["x"].add(t0, d, x, "out")
            if scale is not None:
                s = o.tr["sc"].at(t0)
                o.tr["sc"].add(t0, 0, s * scale)
                o.tr["sc"].add(t0, d, s, "back")
    return Anim(fn)


def FadeOut(*objs, kill=True):
    objs = flatten(objs)

    def fn(S, t0, d):
        for o in objs:
            o.tr["op"].add(t0, d, 0.0, "io")
            if kill and o.parent is None:
                o.dead = min(o.dead, t0 + d + 1e-3)
    return Anim(fn)


def Appear(*objs):
    """瞬间出现（不渐变）。"""
    objs = flatten(objs)

    def fn(S, t0, d):
        for o in objs:
            if o.parent is None and o not in S._registered:
                S._register(o, t0)
            o.dead = INF
            o.tr["op"].add(t0, 0, 1.0)
    return Anim(fn, dur=0.0)


def Call(f):
    """在某个时刻执行任意搭建代码 f(S, t0, dur)。"""
    return Anim(f)


# ------------------------------------------------------------------ 渲染
class Renderer:
    def __init__(self, scene):
        self.S = scene
        self.surface = skia.Surface(W, H)

    def frame(self, t):
        cv = self.surface.getCanvas()
        theme.background(cv)
        for layer in (self.S.under, self.S.objs, self.S.over):
            for o in sorted(layer, key=lambda n: n.z) if any(n.z for n in layer) else layer:
                o.draw(cv, t)
        return self.surface.makeImageSnapshot()

    def need_mask(self, nframes, fps):
        need = bytearray(nframes)
        if nframes:
            need[0] = 1

        def mark(t0, t1):
            f0 = max(0, int(math.floor(t0 * fps)))
            f1 = min(nframes - 1, int(math.ceil(t1 * fps)) + 1)
            for f in range(f0, f1 + 1):
                need[f] = 1

        for layer in (self.S.under, self.S.objs, self.S.over):
            for top in layer:
                for n in top.walk():
                    for tr in n.tr.values():
                        for seg in tr.segs:
                            mark(seg[0], seg[1])
                    if n.born != -INF:
                        mark(n.born, n.born)
                    if n.dead != INF:
                        mark(n.dead, n.dead)
        for t0, t1 in self.S.active:
            mark(t0, t1)
        return need

    def encode(self, out, fps=FPS, crf=27, t0=0.0, t1=None, audio=None, preset="medium", log=None):
        total = self.S.t if t1 is None else t1
        n = int(math.ceil((total - t0) * fps))
        need = self.need_mask(int(math.ceil(total * fps)) + 2, fps)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
               "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
        if audio:
            cmd += ["-i", str(audio)]
        cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-tune", "animation",
                "-pix_fmt", "yuv420p", "-x264-params", "keyint=300:min-keyint=30",
                "-movflags", "+faststart"]
        if audio:
            cmd += ["-c:a", "aac", "-b:a", "64k", "-ac", "2", "-shortest"]
        cmd += [str(out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        last = None
        rendered = 0
        f_start = int(round(t0 * fps))
        for k in range(n):
            f = f_start + k
            if last is None or (f < len(need) and need[f]):
                last = self.frame(f / fps).tobytes()
                rendered += 1
            proc.stdin.write(last)
            if log and k % 900 == 0:
                print(f"  {log}: {k}/{n} 帧（实际绘制 {rendered}）", file=sys.stderr, flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg 编码失败")
        return rendered, n

    def still(self, t, path):
        img = self.frame(t)
        img.save(str(path), skia.kPNG)
