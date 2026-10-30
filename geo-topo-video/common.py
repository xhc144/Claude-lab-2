# -*- coding: utf-8 -*-
"""公共样式与工具：配色、霓虹发光、中文文字、章节卡片、语音同步。"""
import json
import os

import numpy as np
from manim import *

ROOT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT, "audio", "timing.json")) as _f:
    TIMING = json.load(_f)

FONT = "Noto Sans CJK SC"
LATIN = "Inter"

CYAN = "#22E4FF"
BLUE = "#4D7CFF"
PURPLE = "#A78BFA"
MAGENTA = "#FF4FD8"
PINK = "#FF5C8A"
RED = "#FF4D5E"
ORANGE = "#FF9F43"
YELLOW = "#FFD84D"
GREEN = "#4DFFA6"
WHITE_ = "#F2F5FF"
GREY_ = "#8A93B2"
DIM = "#3A4266"

# 字幕区留白：主体内容保持在 y > SAFE_BOTTOM
SAFE_BOTTOM = -3.0

# ---------------------------------------------------------------- 3D 绘制顺序
# 让带 depth_sort 标记的曲线小段也参与深度排序（但不被 3D 光照染暗）。
def _get_mobjects_to_display(self, *args, **kwargs):
    mobs = Camera.get_mobjects_to_display(self, *args, **kwargs)
    rot = self.get_rotation_matrix()

    def key(m):
        if getattr(m, "always_back", False):
            return -np.inf
        if getattr(m, "shade_in_3d", False) or getattr(m, "depth_sort", False):
            return float(np.dot(m.get_z_index_reference_point(), rot.T)[2])
        return np.inf

    return sorted(mobs, key=key)


ThreeDCamera.get_mobjects_to_display = _get_mobjects_to_display


# ---------------------------------------------------------------- 文本
def zh(text, size=36, color=WHITE_, weight=NORMAL, **kw):
    return Text(text, font=FONT, font_size=size, color=color, weight=weight, **kw)


def en(text, size=28, color=GREY_, weight=NORMAL, **kw):
    return Text(text, font=LATIN, font_size=size, color=color, weight=weight, **kw)


def tex(s, size=48, color=WHITE_, **kw):
    return MathTex(s, font_size=size, color=color, **kw)


# ---------------------------------------------------------------- 霓虹发光
def glow_layers(mob, color=None, layers=4, spread=5.0, strength=1.0):
    """返回若干层逐渐变宽、变淡的描边副本，叠在原物体下方形成光晕。"""
    c = color or mob.get_stroke_color()
    w = max(mob.get_stroke_width(), 1.5)
    out = VGroup()
    for i in range(layers, 0, -1):
        g = mob.copy()
        g.set_fill(opacity=0)
        g.set_stroke(color=c, width=w + spread * i, opacity=strength * 0.42 / (i + 0.6) ** 1.5)
        out.add(g)
    return out


def neon(mob, color=None, width=None, layers=4, spread=5.0, strength=1.0):
    if color is not None:
        mob.set_stroke(color=color)
    if width is not None:
        mob.set_stroke(width=width)
    return VGroup(glow_layers(mob, layers=layers, spread=spread, strength=strength), mob)


def glow_text(t, color=None, layers=3, spread=4.0, strength=0.6):
    c = color or t.get_color()
    g = t.copy().set_fill(opacity=0).set_stroke(c, width=1)
    gl = VGroup()
    for i in range(layers, 0, -1):
        gl.add(g.copy().set_stroke(c, width=spread * i, opacity=strength * 0.35 / (i + 0.5) ** 1.4))
    return VGroup(gl, t)


def glow_dot(point=ORIGIN, color=YELLOW, radius=0.07, halo=4):
    d = Dot(point, radius=radius, color=color)
    halos = VGroup(*[
        Dot(point, radius=radius * (1 + 0.9 * i), color=color).set_opacity(0.32 / (i + 0.4) ** 1.6)
        for i in range(halo, 0, -1)
    ])
    return VGroup(halos, d)


def panel(width, height, color=CYAN, fill=0.10, corner=0.18):
    r = RoundedRectangle(width=width, height=height, corner_radius=corner)
    r.set_fill("#0B1030", opacity=0.82).set_stroke(color, width=2)
    return VGroup(glow_layers(r, layers=3, spread=4, strength=0.7), r)


def burst(point, color=YELLOW, n=18, r0=0.1, r1=1.0):
    """从一点向外迸发的光线段 + 光环。用 self.play(burst(...)) 播放。"""
    rays = VGroup()
    for k in range(n):
        a = TAU * k / n + 0.15 * np.sin(5 * k)
        d = np.array([np.cos(a), np.sin(a), 0])
        rays.add(Line(point + d * r0, point + d * r1 * (0.7 + 0.3 * ((k * 7) % 5) / 4),
                      stroke_width=3, color=color))
    ring = Circle(radius=r1 * 0.9, color=color, stroke_width=4).move_to(point)
    return AnimationGroup(
        LaggedStart(*[ShowPassingFlash(r.copy(), time_width=0.6) for r in rays], lag_ratio=0.02),
        ShowPassingFlash(ring, time_width=0.5),
        run_time=0.9,
    )


def ring_pulse(point, color=YELLOW, r=0.6):
    c = Circle(radius=0.05, color=color, stroke_width=6).move_to(point)
    return c.animate(rate_func=rush_from, run_time=0.8).scale(r / 0.05).set_stroke(opacity=0)


# ---------------------------------------------------------------- 语音同步
class Narrated:
    script_scene = None

    def init_narration(self):
        self.timing = TIMING[self.script_scene]
        self.seglog = []
        self._seg_end = 0.0
        self._seg_start = 0.0

    @property
    def now(self):
        return self.renderer.time

    def dur(self, key):
        return self.timing[key]["dur"]

    def seg(self, key, at=None):
        """开始一段旁白（可预约在未来某一时刻 at 开始）。返回该段时长。"""
        t0 = self.now if at is None else at
        if self.seglog and t0 < self._seg_end - 1e-3:
            print(f"!! overlap {self.script_scene}/{key}: {t0:.2f} < {self._seg_end:.2f}")
        self.seglog.append({"key": key, "start": round(t0, 4)})
        self._seg_start = t0
        self._seg_end = t0 + self.dur(key)
        self._sents = self.timing[key]["sents"]
        return self.dur(key)

    def sent_at(self, i, frac=0.0):
        """当前段第 i 句（可加句内比例 frac）的绝对时间。"""
        s = self._sents[i]
        return self._seg_start + s["start"] + frac * (s["end"] - s["start"])

    def phrase_at(self, i, phrase, after=False):
        """估计第 i 句中某个词出现的时刻（按字数比例）。"""
        txt = self._sents[i]["sub"]
        k = txt.find(phrase)
        if k < 0:
            raise ValueError(phrase)
        if after:
            k += len(phrase)
        return self.sent_at(i, k / max(1, len(txt)))

    def wait_until(self, t):
        if t - self.now > 1 / 60:
            self.wait(t - self.now)

    def until(self, t):
        """距离时刻 t 还有多久（至少一帧），用作 run_time。"""
        return max(1 / 30, t - self.now)

    def remaining(self, pad=0.0):
        return max(1 / 30, self._seg_end + pad - self.now)

    def sync(self, pad=0.35):
        self.wait_until(self._seg_end + max(pad, 0.08))

    def save_log(self):
        os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
        with open(os.path.join(ROOT, "logs", f"{type(self).__name__}.json"), "w") as f:
            json.dump({"script_scene": self.script_scene, "segs": self.seglog,
                       "length": self.now}, f, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------- 章节卡
    def chapter(self, num, title, english):
        d = self.seg("title")
        big = Text(f"{num:02d}", font=LATIN, font_size=200, weight=BOLD)
        big.set_fill(opacity=0).set_stroke(CYAN, width=3)
        big_g = VGroup(glow_layers(big, layers=4, spread=5, strength=0.9), big)
        bar = Line(UP * 1.3, DOWN * 1.3, stroke_width=4, color=MAGENTA)
        bar_g = neon(bar)
        tag = Text(f"P R O B L E M   {num:02d}", font=LATIN, font_size=24, color=CYAN, weight=BOLD)
        ttl = zh(title, size=84, weight=BOLD)
        ttl.set_color_by_gradient(CYAN, PURPLE, MAGENTA)
        sub = en(english, size=28, color=GREY_)
        right = VGroup(tag, ttl, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        group = VGroup(big_g, bar_g, right).arrange(RIGHT, buff=0.6).move_to(UP * 0.2)
        if group.width > 12.4:
            group.scale(12.4 / group.width)

        rng = np.random.default_rng(num)
        sparks = VGroup()
        for _ in range(46):
            p = bar.get_center() + np.array([0, rng.uniform(-1.3, 1.3), 0])
            sp = Dot(p, radius=rng.uniform(0.015, 0.04),
                     color=rng.choice([CYAN, MAGENTA, YELLOW, PURPLE]))
            sp.target_pt = p + np.array([rng.uniform(-5, 5), rng.uniform(-2.2, 2.2), 0])
            sparks.add(sp)

        self.play(GrowFromCenter(bar_g), run_time=0.5)
        self.play(
            LaggedStart(*[sp.animate(rate_func=rush_from).move_to(sp.target_pt).set_opacity(0)
                          for sp in sparks], lag_ratio=0.01, run_time=1.6),
            DrawBorderThenFill(big_g, run_time=1.2),
            FadeIn(right, shift=RIGHT * 0.6, run_time=0.9),
        )
        self.remove(sparks)
        self.wait_until(max(self._seg_end, self.now + 0.6) + 0.4)
        self.play(
            group.animate.scale(1.15).set_opacity(0),
            run_time=0.6, rate_func=rush_into,
        )
        self.remove(group)
        # 左上角常驻标签
        lab_num = Text(f"{num:02d}", font=LATIN, font_size=26, color=CYAN, weight=BOLD)
        lab_bar = Line(UP * 0.17, DOWN * 0.17, color=MAGENTA, stroke_width=3)
        lab_ttl = zh(title, size=24, color=GREY_)
        self.corner = VGroup(lab_num, lab_bar, lab_ttl).arrange(RIGHT, buff=0.18)
        self.corner.to_corner(UL, buff=0.35)
        return self.corner

    def show_corner(self, three_d=False):
        if three_d:
            self.add_fixed_in_frame_mobjects(self.corner)
        self.play(FadeIn(self.corner, shift=RIGHT * 0.3), run_time=0.5)


class NScene(Narrated, Scene):
    def construct(self):
        self.init_narration()
        self.body()
        self.save_log()


class NThreeDScene(Narrated, ThreeDScene):
    def construct(self):
        self.init_narration()
        self.body()
        self.save_log()

    def fix(self, *mobs):
        self.add_fixed_in_frame_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs


def make_corner(num, title):
    lab_num = Text(f"{num:02d}", font=LATIN, font_size=26, color=CYAN, weight=BOLD)
    lab_bar = Line(UP * 0.17, DOWN * 0.17, color=MAGENTA, stroke_width=3)
    lab_ttl = zh(title, size=24, color=GREY_)
    return VGroup(lab_num, lab_bar, lab_ttl).arrange(RIGHT, buff=0.18).to_corner(UL, buff=0.35)


def smooth_path(points, closed=False):
    m = VMobject()
    pts = [np.array(p, dtype=float) if len(p) == 3 else np.array([p[0], p[1], 0.0]) for p in points]
    if closed:
        pts = pts + [pts[0]]
    m.set_points_smoothly(pts)
    return m


# ---------------------------------------------------------------- 3D 曲面：预烘焙光照
LIGHT = np.array([-0.45, -0.55, 1.0]) / np.linalg.norm([-0.45, -0.55, 1.0])


def face_normal(f):
    a = f.get_anchors()
    if len(a) < 3:
        return OUT
    p0 = a[0]
    best = None
    for i in range(1, len(a) - 1):
        n = np.cross(a[i] - p0, a[i + 1] - p0)
        if best is None or np.linalg.norm(n) > np.linalg.norm(best):
            best = n
    ln = np.linalg.norm(best)
    return best / ln if ln > 1e-9 else OUT


def bake(surface, color=BLUE, color_fn=None, opacity=0.85, amb=0.35, stroke=0.6, light=LIGHT):
    """用固定光照给每个面片上色，关闭 Cairo 的逐帧 3D 着色（快约 3 倍），保留深度排序。"""
    for f in surface:
        n = face_normal(f)
        c = ManimColor(color_fn(f.get_center()) if color_fn else color)
        k = amb + (1 - amb) * abs(float(np.dot(n, light)))
        col = interpolate_color(ManimColor("#000000"), c, min(1.0, k * 1.08))
        f.set_fill(col, opacity=opacity)
        f.set_stroke(col, width=stroke, opacity=opacity * 0.9)
        f.shade_in_3d = False
        f.depth_sort = True
    return surface


def curve3d(points, color, width=4, closed=False, opacity=1.0):
    """把 3D 折线拆成小段，每段参与深度排序（曲线贴在曲面上时能正确遮挡）。"""
    P = np.array(points, dtype=float)
    if closed:
        P = np.vstack([P, P[:1]])
    g = VGroup()
    for i in range(len(P) - 1):
        s = Line(P[i], P[i + 1], stroke_width=width, color=color, stroke_opacity=opacity)
        s.depth_sort = True
        g.add(s)
    return g


class FastSurface(VGroup):
    """参数曲面：面片只建一次，每帧用向量化函数更新顶点与烘焙光照（替代 always_redraw(Surface)）。

    func(U, V) 接受同形状数组，返回形状 (*U.shape, 3) 的坐标。
    """

    def __init__(self, func, u_range, v_range, resolution=(32, 16), color=BLUE, color_fn=None,
                 opacity=0.85, amb=0.35, stroke=0.6, light=LIGHT, uv_color=None, **kw):
        super().__init__(**kw)
        nu, nv = resolution
        self.uv_rgb = None
        if uv_color is not None:  # uv_color(Uc, Vc) -> (nu, nv, 3) 的 rgb，按参数着色（静态）
            us, vs = np.linspace(*u_range, nu + 1), np.linspace(*v_range, nv + 1)
            Uc, Vc = np.meshgrid((us[:-1] + us[1:]) / 2, (vs[:-1] + vs[1:]) / 2, indexing="ij")
            self.uv_rgb = np.asarray(uv_color(Uc, Vc))
        self.U, self.V = np.meshgrid(np.linspace(*u_range, nu + 1), np.linspace(*v_range, nv + 1), indexing="ij")
        self.func = func
        self.base = np.array(ManimColor(color).to_rgb())
        self.color_fn = color_fn
        self.opacity, self.amb, self.stroke_w, self.light = opacity, amb, stroke, light
        self.nu, self.nv = nu, nv
        for _ in range(nu * nv):
            f = VMobject()
            f.depth_sort = True
            self.add(f)
        self.update_mesh()

    def update_mesh(self, func=None, opacity=None):
        if func is not None:
            self.func = func
        if opacity is not None:
            self.opacity = opacity
        P = np.asarray(self.func(self.U, self.V), dtype=float)
        c00, c10, c11, c01 = P[:-1, :-1], P[1:, :-1], P[1:, 1:], P[:-1, 1:]
        n = np.cross(c11 - c00, c01 - c10)
        ln = np.linalg.norm(n, axis=-1, keepdims=True)
        n = np.where(ln > 1e-12, n / np.maximum(ln, 1e-12), 0)
        k = self.amb + (1 - self.amb) * np.abs(n @ self.light)
        k = np.clip(k * 1.08, 0, 1)
        if self.uv_rgb is not None:
            base = self.uv_rgb
        elif self.color_fn is not None:
            base = self.color_fn((c00 + c10 + c11 + c01) / 4)  # (nu, nv, 3) rgb
        else:
            base = np.broadcast_to(self.base, c00.shape)
        rgb = base * k[..., None]
        a = self.opacity
        idx = 0
        for i in range(self.nu):
            for j in range(self.nv):
                f = self.submobjects[idx]
                f.set_points_as_corners([c00[i, j], c10[i, j], c11[i, j], c01[i, j], c00[i, j]])
                f.fill_rgbas = np.array([[*rgb[i, j], a]])
                f.stroke_rgbas = np.array([[*rgb[i, j], a * 0.9]])
                f.stroke_width = self.stroke_w
                idx += 1
        return self


def lerp_rgb(cols, t):
    """多段颜色渐变：cols 为颜色列表，t∈[0,1] 数组 → rgb 数组。"""
    C = np.array([ManimColor(c).to_rgb() for c in cols])
    t = np.clip(np.asarray(t, float), 0, 1) * (len(C) - 1)
    i = np.minimum(t.astype(int), len(C) - 2)
    f = (t - i)[..., None]
    return C[i] * (1 - f) + C[i + 1] * f


class FastPolyline(VGroup):
    """3D 折线：小段只建一次，每帧更新端点；每段参与深度排序。"""

    def __init__(self, points, color=WHITE, width=4, opacity=1.0, **kw):
        super().__init__(**kw)
        P = np.asarray(points, float)
        for i in range(len(P) - 1):
            s = Line(P[i], P[i + 1], stroke_width=width, color=color, stroke_opacity=opacity)
            s.depth_sort = True
            self.add(s)

    def update_points(self, points):
        P = np.asarray(points, float)
        for i, s in enumerate(self.submobjects):
            s.set_points_as_corners([P[i], P[i + 1]])
        return self
