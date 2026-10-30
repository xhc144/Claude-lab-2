# -*- coding: utf-8 -*-
"""公共部分：配色、字体、背景图、霓虹组件、字幕条、章节卡，以及按音乐小节对齐的场景基类。

没有配音，画面节奏由音乐决定：BPM 固定为 120（一拍 0.5 秒，一小节 2 秒）。
每个场景结束时补齐到整小节，所以每个场景都从小节线开始；场景里用 ``self.beat()``
把重要的出场卡在拍点上，再用 ``self.hit()`` 记下时间，配乐（music.py）在这些时刻加重音。
"""
import json
import math
import os
import random

import manimpango
import numpy as np
from manim import *  # noqa: F401,F403
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), "build")
CUES = os.path.join(BUILD, "cues")

# ---------- 节拍 ----------
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT

# ---------- 配色：深夜蓝底 + 霓虹 ----------
BG = "#04050C"
INK = "#E9F1FF"      # 正文
MUTED = "#8090B8"    # 辅助文字
DIM = "#3A4672"      # 暗线
PANEL = "#0A1024"    # 面板底色
CYAN = "#2BE8FF"     # 第一个向量 / 1-向量
MAGENTA = "#FF46D2"  # 第二个向量 / 2-向量
LIME = "#8DFF5C"     # 第三个向量 / 3-向量
GOLD = "#FFD447"     # 结果、强调
ORANGE = "#FF9442"
VIOLET = "#A780FF"
RED = "#FF4D6D"      # 负号、定向翻转
SKY = "#6FA8FF"

CH_COLORS = {1: CYAN, 2: MAGENTA, 3: GOLD}

FONT = "Noto Sans CJK SC"
FONT_EN = "Orbitron"

for _f in ("Orbitron-Bold.ttf", "Orbitron-Black.ttf"):
    _p = os.path.join(BUILD, "fonts", _f)
    if os.path.exists(_p):
        manimpango.register_font(_p)

config.background_color = BG
# 并行渲染时每个场景用自己的 LaTeX / 文字缓存目录，避免几个进程同时写同一个文件
_job = os.environ.get("EA_JOB")
if _job:
    config.tex_dir = os.path.join(BUILD, "cache", _job, "Tex")
    config.text_dir = os.path.join(BUILD, "cache", _job, "texts")

TEX = TexTemplate()
TEX.add_to_preamble(r"\usepackage{amsmath,amssymb,bm}")
config.tex_template = TEX
MathTex.set_default(color=INK)
Tex.set_default(color=INK)
Text.set_default(font=FONT, color=INK)


# ---------- 背景图：径向暗角 + 两团星云 + 极淡的网格 + 星点 ----------
def background_path():
    w, h = config.pixel_width, config.pixel_height
    os.makedirs(BUILD, exist_ok=True)
    path = os.path.join(BUILD, f"bg_{w}x{h}.png")
    if os.path.exists(path):
        return path
    rng = np.random.default_rng(7)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    s = w / 1920
    r = np.sqrt(((x - w / 2) / w) ** 2 + ((y - h / 2) / h) ** 2)
    base = np.clip(1 - r * 1.3, 0, 1) ** 1.7
    edge = np.array([2, 3, 8], np.float32)
    center = np.array([10, 14, 34], np.float32)
    img = edge + (center - edge) * base[..., None]

    def blob(px, py, rad, col, k):
        d = ((x - px) ** 2 + (y - py) ** 2) / (rad * s) ** 2
        return np.exp(-d)[..., None] * np.array(col, np.float32) * k

    img += blob(w * 0.12, h * 0.15, 560, [70, 20, 110], 0.20)
    img += blob(w * 0.90, h * 0.88, 600, [0, 70, 95], 0.20)
    img += blob(w * 0.80, h * 0.10, 380, [30, 25, 100], 0.12)
    step = int(round(w / 14.222 / 2))  # 半个 manim 单位一格
    grid = ((x.astype(int) % step) == 0) | ((y.astype(int) % step) == 0)
    img += grid[..., None] * np.array([4, 6, 13], np.float32) * (0.4 + base[..., None])
    stars = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(stars)
    for _ in range(int(380 * s * s) + 60):
        sx, sy = rng.uniform(0, w), rng.uniform(0, h)
        rr = rng.choice([0.6, 0.9, 1.4], p=[0.6, 0.3, 0.1]) * s
        dr.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=int(rng.uniform(30, 100)))
    stars = stars.filter(ImageFilter.GaussianBlur(0.6 * s))
    img = img + np.asarray(stars, np.float32)[..., None] * np.array([0.75, 0.82, 1.0])
    rgba = np.concatenate([np.clip(img, 0, 255), np.full((h, w, 1), 255, np.float32)], axis=2)
    Image.fromarray(rgba.astype(np.uint8), "RGBA").save(path)
    return path


# ---------- 文字 ----------
def T(s, size=30, color=INK, bold=False, **kw):
    """中文文字。"""
    return Text(s, font_size=size, color=color, weight=BOLD if bold else NORMAL, **kw)


def EN(s, size=30, color=INK, black=False, spacing=0, **kw):
    """英文标题字（Orbitron）。"""
    if spacing:
        s = (" " * spacing).join(s)
    return Text(s, font=FONT_EN, font_size=size, color=color, weight=HEAVY if black else BOLD, **kw)


def M(s, size=40, color=INK, **kw):
    if isinstance(s, (list, tuple)):
        return MathTex(*s, font_size=size, color=color, **kw)
    return MathTex(s, font_size=size, color=color, **kw)


def mixed(*parts, size=30, color=INK, buff=0.12):
    """中文和公式混排的一行：以 $ 开头的片段当公式，其余当文字。"""
    mobs = []
    for p in parts:
        if isinstance(p, Mobject):
            mobs.append(p)
        elif p.startswith("$"):
            mobs.append(M(p.strip("$"), size=size * 1.25, color=color))
        else:
            mobs.append(T(p, size=size, color=color))
    return VGroup(*mobs).arrange(RIGHT, buff=buff)


def read_time(s):
    """按字数估计读完一句的时间（秒）。"""
    n = len([c for c in s if not c.isspace()])
    return max(2.0, 0.21 * n + 0.8)


# ---------- 霓虹组件 ----------
def glow(mob, color=None, width=None, layers=3, opacity=0.22):
    """在 mob 背后叠几层更粗、更透明的描边，做出霓虹光晕。返回 VGroup(光晕…, mob)。"""
    g = VGroup()
    for k in range(layers, 0, -1):
        c = mob.copy()
        c.set_fill(opacity=0)
        sw = (width or max(mob.get_stroke_width(), 2)) * (1 + 1.8 * k)
        c.set_stroke(color or mob.get_color(), width=sw, opacity=opacity / k)
        g.add(c)
    g.add(mob)
    return g


def neon_line(a, b, color, width=4, layers=2):
    core = Line(a, b, color=color, stroke_width=width)
    return glow(core, color, width, layers=layers)


def vec(start, end, color, width=5, tip=0.24, glow_layers=3):
    """霓虹箭头。start、end 是三维点。"""
    start, end = np.array(start, float), np.array(end, float)
    d = end - start
    L = np.linalg.norm(d)
    g = VGroup()
    if L < 1e-6:
        return VGroup(Dot(start, radius=0.04, color=color))
    u = d / L
    tl = min(tip, L * 0.45)
    base = end - u * tl
    for k in range(glow_layers, 0, -1):
        gl = Line(start, base, stroke_width=width * (1 + 1.6 * k), color=color, stroke_opacity=0.2 / k)
        gl.cap_style = CapStyleType.ROUND
        g.add(gl)
    g.add(Line(start, base + u * 0.02, stroke_width=width, color=color))
    n = np.array([-u[1], u[0], 0.0])
    tipm = Polygon(end, base + n * tl * 0.45, base - n * tl * 0.45, stroke_width=0, fill_color=color, fill_opacity=1)
    g.add(tipm)
    return g


def vec3(start, end, color, width=5, tip=0.26):
    """三维场景用的轻量箭头：线段 + 两片互相垂直的三角形箭头（比 Arrow3D 的曲面快得多）。"""
    start, end = np.array(start, float), np.array(end, float)
    d = end - start
    L = np.linalg.norm(d)
    u = d / L
    tl = min(tip, L * 0.45)
    base = end - u * tl
    a = np.cross(u, OUT)
    if np.linalg.norm(a) < 1e-3:
        a = np.cross(u, RIGHT)
    a = a / np.linalg.norm(a)
    b = np.cross(u, a)
    g = VGroup()
    gl = Line(start, base, stroke_width=width * 3, color=color, stroke_opacity=0.18)
    g.add(gl, Line(start, base + u * 0.02, stroke_width=width, color=color))
    for n in (a, b):
        g.add(Polygon(end, base + n * tl * 0.42, base - n * tl * 0.42, stroke_width=0, fill_color=color,
                      fill_opacity=1))
    return g


def para(o, v, w, color=GOLD, opacity=0.32, stroke=2.5, fill=None):
    """以 o 为顶点、v、w 为两边的平行四边形。fill 给两种颜色时做渐变填充。"""
    o, v, w = (np.array(p, float) for p in (o, v, w))
    P = Polygon(o, o + v, o + v + w, o + w, stroke_color=color, stroke_width=stroke,
                fill_color=color, fill_opacity=opacity)
    if fill is not None:
        P.set_fill(fill, opacity=opacity)
        P.set_sheen_direction(v - w if np.linalg.norm(v - w) > 1e-6 else RIGHT)
    return P


def orient_arc(center, radius=0.35, positive=True, color=GOLD, width=3):
    """表示定向的小圆弧箭头：逆时针为正。"""
    if positive:
        arc = Arc(radius=radius, start_angle=-PI * 0.75, angle=PI * 1.5, color=color, stroke_width=width)
    else:
        arc = Arc(radius=radius, start_angle=PI * 0.75, angle=-PI * 1.5, color=color, stroke_width=width)
    arc.add_tip(tip_length=0.13, tip_width=0.13)
    arc.move_arc_center_to(center)
    return arc


def panel(mob, pad=0.3, color=CYAN, opacity=0.82, radius=0.12, stroke_opacity=0.45):
    """半透明玻璃面板，放在公式下面挡住背景。"""
    box = RoundedRectangle(corner_radius=radius, width=mob.width + 2 * pad, height=mob.height + 2 * pad,
                           fill_color=PANEL, fill_opacity=opacity, stroke_color=color, stroke_width=1.5,
                           stroke_opacity=stroke_opacity)
    box.move_to(mob)
    return box


def brackets(mob, pad=0.22, length=0.32, color=CYAN, width=3):
    """科幻 HUD 式的四角框。"""
    x0, x1 = mob.get_left()[0] - pad, mob.get_right()[0] + pad
    y0, y1 = mob.get_bottom()[1] - pad, mob.get_top()[1] + pad
    g = VGroup()
    for (x, y, sx, sy) in [(x0, y1, 1, -1), (x1, y1, -1, -1), (x0, y0, 1, 1), (x1, y0, -1, 1)]:
        p = np.array([x, y, 0])
        g.add(VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(
            [p + RIGHT * sx * length, p, p + UP * sy * length]))
    return g


def result_box(mob, color=GOLD, pad=0.25):
    """结论框：面板 + 发光描边。"""
    box = RoundedRectangle(corner_radius=0.1, width=mob.width + 2 * pad, height=mob.height + 2 * pad,
                           fill_color=PANEL, fill_opacity=0.85, stroke_color=color, stroke_width=3)
    box.move_to(mob)
    return VGroup(glow(box.copy().set_fill(opacity=0), color, 3, layers=2, opacity=0.3), box)


def burst(point, color=GOLD, n=26, radius=1.1, run_time=0.8, size=0.035, seed=None):
    """粒子爆散：n 个小点从 point 向四周飞出并熄灭。"""
    rng = random.Random(seed if seed is not None else int(abs(point[0] * 1000 + point[1] * 77)))
    point = np.array(point, float)
    dots = VGroup(*[Dot(point, radius=size * rng.uniform(0.6, 1.4), color=color) for _ in range(n)])
    dirs = []
    for _ in range(n):
        a = rng.uniform(0, TAU)
        dirs.append(np.array([math.cos(a), math.sin(a), 0]) * radius * rng.uniform(0.35, 1.0))

    def upd(m, a):
        e = 1 - (1 - a) ** 3
        for d, dv in zip(m, dirs):
            d.move_to(point + dv * e)
            d.set_opacity(max(0, 1 - a) ** 1.5)

    return UpdateFromAlphaFunc(dots, upd, run_time=run_time, remover=True)


def ring_pulse(point, color=GOLD, radius=1.2, run_time=0.7, width=6):
    """从一点扩散出去的光环。"""
    c = Circle(radius=0.05, color=color, stroke_width=width).move_to(point)

    def upd(m, a):
        m.become(Circle(radius=0.05 + radius * (1 - (1 - a) ** 2), color=color,
                        stroke_width=width * (1 - a) + 0.5).move_to(point))
        m.set_stroke(opacity=1 - a)

    return UpdateFromAlphaFunc(c, upd, run_time=run_time, remover=True)


def glitch(mob, run_time=0.5, amp=0.12, seed=3):
    """故障风出场：红、青两份错位的拷贝抖动几下后合上。"""
    rng = random.Random(seed)
    red = mob.copy().set_color(MAGENTA)
    cyn = mob.copy().set_color(CYAN)
    jit = [(rng.uniform(-1, 1), rng.uniform(-0.3, 0.3)) for _ in range(12)]
    home = mob.get_center()
    grp = VGroup(red, cyn, mob)

    def upd(g, a):
        r, c, m = g
        k = min(int(a * len(jit)), len(jit) - 1)
        dx, dy = jit[k]
        s = amp * (1 - a) ** 1.2
        m.move_to(home + np.array([dx * s * 0.4, dy * s, 0]))
        r.move_to(home + np.array([-s - dx * s * 0.5, dy * s, 0]))
        c.move_to(home + np.array([s + dx * s * 0.5, -dy * s, 0]))
        on = 0 if (k % 3 == 1 and a < 0.7) else 1
        m.set_opacity(on * min(1, a * 2.5))
        r.set_opacity(0.6 * (1 - a))
        c.set_opacity(0.6 * (1 - a))

    def done(g):
        g[0].set_opacity(0)
        g[1].set_opacity(0)

    anim = UpdateFromAlphaFunc(grp, upd, run_time=run_time)
    anim.finish = (lambda f=anim.finish: (f(), done(grp)))
    return anim, grp


def light_sweep(mob, color=WHITE, run_time=0.9, width=0.35):
    """一道竖直的光从左到右扫过 mob。"""
    h = mob.height + 0.6
    bar = Rectangle(width=width, height=h, stroke_width=0, fill_color=color, fill_opacity=0.0)
    x0, x1 = mob.get_left()[0] - 0.5, mob.get_right()[0] + 0.5
    y = mob.get_center()[1]

    def upd(m, a):
        m.move_to(np.array([x0 + (x1 - x0) * a, y, 0]))
        m.set_fill(opacity=0.35 * math.sin(PI * a))

    return UpdateFromAlphaFunc(bar, upd, run_time=run_time, remover=True)


def TFC(a, b, **kw):
    """从 a 的拷贝变成 b。不用 TransformFromCopy：它会把 b 本身的子对象结构改掉，之后再按下标取 b[i] 就错了。"""
    return ReplacementTransform(a.copy(), b, **kw)


def strike(mob, color=RED, width=5):
    """斜线划掉。"""
    return Line(mob.get_corner(DL) + LEFT * 0.05, mob.get_corner(UR) + RIGHT * 0.05, color=color, stroke_width=width)


def matrix_tex(rows, size=40, color=INK, **kw):
    body = r" \\ ".join(" & ".join(r) for r in rows)
    return M(r"\begin{pmatrix}" + body + r"\end{pmatrix}", size=size, color=color, **kw)


def pill(text, color, size=22):
    """圆角小标签。"""
    t = T(text, size, color, bold=True)
    box = RoundedRectangle(corner_radius=(t.height + 0.16) / 2, width=t.width + 0.4, height=t.height + 0.2,
                           stroke_color=color, stroke_width=2, fill_color=PANEL, fill_opacity=0.9)
    return VGroup(box, t.move_to(box))


class RetroGrid(VGroup):
    """合成器浪潮风格的透视网格地面，横线不断向观众涌来。"""

    def __init__(self, horizon=-2.35, bottom=-4.3, color=MAGENTA, speed=0.6, n_h=14, n_v=17, **kw):
        super().__init__(**kw)
        self.horizon, self.bottom, self.speed, self.n_h = horizon, bottom, speed, n_h
        self.color = color
        self.phase = 0.0
        vp = np.array([0, horizon, 0])
        for k in range(-n_v, n_v + 1):
            end = np.array([k * 1.1, bottom - 0.5, 0])
            ln = Line(vp + (end - vp) * 0.06, end, stroke_width=1.6)
            ln.set_stroke(color=[color, BG], width=1.6, opacity=0.55)
            ln.set_sheen_direction(DOWN)
            self.add(ln)
        self.hlines = VGroup(*[Line(LEFT * 8, RIGHT * 8, stroke_width=1.6) for _ in range(n_h)])
        self.add(self.hlines)
        self._place()
        self.add_updater(lambda m, dt: m._step(dt))

    def _place(self):
        H = self.horizon - self.bottom
        for i, ln in enumerate(self.hlines):
            z = 1 + ((i + self.phase) % self.n_h) * 0.55   # 深度
            y = self.horizon - H / z
            a = max(0.0, min(1.0, (2.6 - z * 0.5)))
            ln.put_start_and_end_on(np.array([-8, y, 0]), np.array([8, y, 0]))
            ln.set_stroke(self.color, width=1.0 + 1.4 / z, opacity=0.6 * a)

    def _step(self, dt):
        self.phase = (self.phase - dt * self.speed * 2) % self.n_h
        self._place()


# ---------- 场景基类 ----------
class Beat:
    """按 120 BPM 对齐的场景：卡拍、记重音、字幕条、页眉、补齐到整小节。"""
    CHAPTER = 0          # 0 = 开场/尾声
    TITLE = ""           # 页眉里的小标题
    threed = False

    def setup(self):
        self.camera.background_image = background_path()
        self.camera.init_background()
        self.camera.reset()
        self._cues = []
        self._cap = None
        # 让帧数严格等于 时长 × 帧率：静止的 wait 原本向下取整，会每次少一帧，拍点就对不齐了
        r = self.renderer

        def freeze(duration, r=r):
            dt = 1 / r.camera.frame_rate
            r.add_frame(r.get_frame(), num_frames=max(0, int(round(duration / dt))))

        r.freeze_current_frame = freeze

    def get_time_progression(self, run_time, description, n_iterations=None, override_skip_animations=False):
        # 浮点误差会让 np.arange 多出一帧（0.6 × 15 = 9.000000000000002）
        return super().get_time_progression(max(run_time - 1e-7, 1e-7), description, n_iterations,
                                            override_skip_animations)

    # 时间
    @property
    def now(self):
        return self.renderer.time

    def beat(self, n=1):
        """等到下一个 n 拍的整数倍（让下一个出场落在拍点上）。"""
        q = BEAT * n
        t = self.now
        target = math.ceil(t / q - 1e-6) * q
        k = round((target - t) * config.frame_rate)
        if k > 0:
            self.wait(k / config.frame_rate)

    def hit(self, kind="hit"):
        """记一个重音（配乐在这里加打击乐）。"""
        self._cues.append({"t": round(self.now, 3), "kind": kind})

    def bar(self):
        self.beat(4)

    # 固定在画面上的东西（3D 场景里要特别处理）
    def fix(self, *mobs):
        if self.threed:
            self.add_fixed_in_frame_mobjects(*mobs)
        return mobs

    # 页眉
    def header(self, title=None, animate=True):
        title = title or self.TITLE
        color = CH_COLORS.get(self.CHAPTER, INK)
        if self.CHAPTER:
            num = EN(f"{self.CHAPTER:02d}", 26, color, black=True)
        else:
            num = EN("∧", 26, color, black=True)
        bar = Rectangle(width=0.06, height=0.38, fill_color=color, fill_opacity=1, stroke_width=0)
        t = T(title, 26, INK, bold=True)
        left = VGroup(num, bar, t).arrange(RIGHT, buff=0.2).to_corner(UL, buff=0.36)
        right = EN("EXTERIOR ALGEBRA", 14, MUTED, spacing=0).to_corner(UR, buff=0.42)
        line = Line(LEFT * 7.1, RIGHT * 7.1, stroke_width=1, color=DIM).next_to(left, DOWN, buff=0.18)
        line.set_x(0)
        hdr = VGroup(left, right, line)
        self.fix(hdr)
        if animate:
            self.play(FadeIn(left, shift=RIGHT * 0.3), FadeIn(right), Create(line), run_time=0.8)
        else:
            self.add(hdr)
        self._hdr = hdr
        return hdr

    # 字幕条
    def caption_mob(self, text, color=INK, t2c=None, size=28):
        t = T(text, size, color, t2c=t2c or {})
        if t.width > 12.6:
            t.scale_to_fit_width(12.6)
        mark = Rectangle(width=0.07, height=t.height + 0.12, fill_color=CH_COLORS.get(self.CHAPTER, CYAN),
                         fill_opacity=1, stroke_width=0)
        row = VGroup(mark, t).arrange(RIGHT, buff=0.22)
        bgbox = RoundedRectangle(corner_radius=0.08, width=row.width + 0.5, height=row.height + 0.28,
                                 fill_color=PANEL, fill_opacity=0.72, stroke_width=0)
        g = VGroup(bgbox, row)
        bgbox.move_to(row)
        g.move_to(DOWN * 3.42)
        return g

    def cap(self, text, wait=0, color=INK, t2c=None, run_time=0.45):
        """换一条字幕。wait 为 None 时按字数停留。"""
        new = self.caption_mob(text, color, t2c)
        self.fix(new)
        anims = [FadeIn(new, shift=UP * 0.12)]
        if self._cap is not None:
            anims.append(FadeOut(self._cap, shift=UP * 0.12))
        self.play(*anims, run_time=run_time)
        self._cap = new
        if wait is None:
            wait = read_time(text)
        if wait:
            self.wait(wait)
        return new

    def uncap(self, run_time=0.4):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=run_time)
            self._cap = None

    def clear_all(self, run_time=0.7, keep=()):
        kept = {id(x) for k in keep for x in k.get_family()}
        mobs = [m for m in self.mobjects if id(m) not in kept]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
        self._cap = None

    def finish(self, tail=0.0):
        """结尾：停一会儿，补齐到整小节，写出时长和重音表。"""
        if tail:
            self.wait(tail)
        self.bar()
        if self.now < BAR:
            self.wait(BAR - self.now)
        os.makedirs(CUES, exist_ok=True)
        with open(os.path.join(CUES, f"{type(self).__name__}.json"), "w") as f:
            json.dump({"duration": round(self.now, 3), "cues": self._cues}, f)


class BScene(Beat, Scene):
    pass


class B3D(Beat, ThreeDScene):
    threed = True


# ---------- 章节卡 ----------
CHAPTERS = {
    1: ("什么是外代数", "THE WEDGE PRODUCT", "三条规则，造出“有向的面积与体积”"),
    2: ("行列式从哪里来", "WHERE DETERMINANTS COME FROM", "不用背公式：行列式是最高次楔积的伸缩倍数"),
    3: ("一行证明的定理们", "ONE-LINE PROOFS", "直接证明很费劲的恒等式，在外代数里只是一句话"),
}


class ChapterCard(BScene):
    N = 1

    def construct(self):
        title, en, sub = CHAPTERS[self.N]
        color = CH_COLORS[self.N]
        self.hit("impact")
        big = EN(f"{self.N:02d}", 200, color, black=True)
        big.set_fill(opacity=0).set_stroke(color, width=3)
        kicker = EN(f"CHAPTER  {self.N:02d}", 24, color)
        t = T(title, 76, INK, bold=True)
        e = EN(en, 22, MUTED, spacing=0)
        s = T(sub, 30, MUTED)
        words = VGroup(kicker, t, e, s).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        card = VGroup(big, words).arrange(RIGHT, buff=0.7).move_to(ORIGIN)
        rule = Line(LEFT * 7.2, RIGHT * 7.2, color=color, stroke_width=2).next_to(card, DOWN, buff=0.5)
        a, grp = glitch(t, run_time=0.6)
        self.play(DrawBorderThenFill(big, run_time=1.0), FadeIn(kicker, shift=RIGHT * 0.4), a, run_time=1.0)
        self.add(t)
        self.remove(grp[0], grp[1])
        self.play(FadeIn(e, shift=RIGHT * 0.3), Create(rule), light_sweep(t), run_time=1.0)
        self.play(Write(s), run_time=1.2)
        self.wait(2.2)
        self.play(FadeOut(VGroup(big, words), shift=LEFT * 0.6), FadeOut(rule), run_time=0.6)
        self.finish()
