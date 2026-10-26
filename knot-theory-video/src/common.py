# -*- coding: utf-8 -*-
"""Shared look & feel, knot-diagram engine, HUD and timing-synced base scene."""
import json, os

import numpy as np
from PIL import Image, ImageFilter
from manim import *

ROOT = os.path.dirname(os.path.abspath(__file__))
TIMING = json.load(open(os.path.join(ROOT, "timing.json")))

# ---------------------------------------------------------------- palette
BG = "#05070f"
CYAN = "#22e4ff"
MAGENTA = "#ff3df2"
GOLD = "#ffd23f"
LIME = "#7dff6b"
ORANGE = "#ff8a3d"
VIOLET = "#9d7bff"
RED_N = "#ff4466"
SKY = "#6aa8ff"
DIM = "#5a6584"
INK = "#e8ecff"
TRI = [RED_N, LIME, SKY]          # three-colouring palette
NEON = [CYAN, MAGENTA, GOLD, LIME, VIOLET, ORANGE]

CJK = "Noto Sans CJK SC"
MONO = "JetBrains Mono"
TEX = TexTemplate(preamble=r"\usepackage{amsmath}\usepackage{amssymb}")

config.background_color = BG


def zh(s, size=36, color=INK, weight=NORMAL, **kw):
    return Text(s, font=CJK, font_size=size, color=color, weight=weight, **kw)


def mono(s, size=28, color=INK, weight=BOLD, **kw):
    return Text(s, font=MONO, font_size=size, color=color, weight=weight, **kw)


def tex(s, size=44, color=INK, **kw):
    return MathTex(s, tex_template=TEX, font_size=size, color=color, **kw)


def glow(mob, color=None, layers=((6.0, 0.05), (3.4, 0.10), (1.9, 0.22))):
    """Return VGroup(glow copies..., mob) giving a neon look to a stroked mobject."""
    out = VGroup()
    w = max(mob.get_stroke_width(), 1.5)
    for k, a in layers:
        g = mob.copy().set_fill(opacity=0)
        g.set_stroke(color=color or mob.get_stroke_color(), width=w * k, opacity=a)
        out.add(g)
    out.add(mob)
    return out


def panel(w, h, color=CYAN, opacity=0.06, stroke=0.6):
    r = RoundedRectangle(width=w, height=h, corner_radius=0.12)
    r.set_fill(color, opacity).set_stroke(color, width=1.6, opacity=stroke)
    return r


# ---------------------------------------------------------------- background
def make_background(path, w, h):
    if os.path.exists(path):
        return path
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.42
    r = np.sqrt(((xx - cx) / w) ** 2 + ((yy - cy) / h) ** 2)
    base = np.array([5, 7, 15], np.float32)
    glowc = np.array([18, 30, 62], np.float32)
    img = base + glowc * np.clip(1 - r * 1.6, 0, 1)[..., None] ** 1.6
    # faint magenta corner haze
    r2 = np.sqrt(((xx - w * 0.95) / w) ** 2 + ((yy - h * 0.05) / h) ** 2)
    img += np.array([30, 6, 34], np.float32) * np.clip(1 - r2 * 2.2, 0, 1)[..., None] ** 2
    r3 = np.sqrt(((xx - w * 0.03) / w) ** 2 + ((yy - h * 0.98) / h) ** 2)
    img += np.array([0, 22, 30], np.float32) * np.clip(1 - r3 * 2.4, 0, 1)[..., None] ** 2
    # dot grid
    step = int(round(w / 48))
    grid = ((xx % step) < 1.6 * w / 1920) & ((yy % step) < 1.6 * w / 1920)
    img[grid] += np.array([22, 30, 50], np.float32)
    # vignette + grain
    v = np.clip(1.15 - 0.9 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2) * 2.2, 0.55, 1)
    img *= v[..., None]
    rng = np.random.default_rng(1)
    img += rng.normal(0, 1.4, img.shape[:2])[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    im.save(path)
    return path


# ---------------------------------------------------------------- knot engine
TAU_ = 2 * np.pi


def curve(fn, n=360):
    t = np.linspace(0, TAU_, n, endpoint=False)
    return np.stack(fn(t), axis=1).astype(float)


def trefoil_pts(n=360):
    # right-handed trefoil
    return curve(lambda t: (np.sin(t) + 2 * np.sin(2 * t), np.cos(t) - 2 * np.cos(2 * t), np.sin(3 * t)), n)


def figure8_pts(n=420):
    return curve(lambda t: ((2 + np.cos(2 * t)) * np.cos(3 * t), (2 + np.cos(2 * t)) * np.sin(3 * t), np.sin(4 * t)), n)


def torus_pts(p, q, n=600, R=2.0, r=1.0):
    return curve(lambda t: ((R + r * np.cos(q * t)) * np.cos(p * t), (R + r * np.cos(q * t)) * np.sin(p * t),
                            -r * np.sin(q * t)), n)


def circle_pts(n=200, r=1.0, c=(0, 0, 0), tilt=0.0, phase=0.0):
    t = np.linspace(0, TAU_, n, endpoint=False) + phase
    return np.stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t), c[2] + tilt * np.sin(t)], 1)


def rot_matrix(ax=0.0, ay=0.0, az=0.0):
    cx, sx, cy, sy, cz, sz = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay), np.cos(az), np.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Comp:
    """One component of a link: 3D polyline, closed or open."""

    def __init__(self, pts, closed=True):
        self.p = np.asarray(pts, float)
        self.closed = closed

    @property
    def n(self):
        return len(self.p)

    def nseg(self):
        return self.n if self.closed else self.n - 1


def find_crossings(comps):
    """All transverse self/mutual crossings of the xy-projection.

    Returns list of dicts: comp/param (float index) for both strands, z values,
    point, over/under assignment and crossing sign (with param orientation).
    """
    P, Q, ZP, ZQ, CI, II = [], [], [], [], [], []
    for c, cp in enumerate(comps):
        m = cp.nseg()
        a = cp.p[:m]
        b = np.roll(cp.p, -1, axis=0)[:m] if cp.closed else cp.p[1:]
        P.append(a[:, :2]); Q.append(b[:, :2]); ZP.append(a[:, 2]); ZQ.append(b[:, 2])
        CI.append(np.full(m, c)); II.append(np.arange(m))
    P, Q, ZP, ZQ, CI, II = map(np.concatenate, (P, Q, ZP, ZQ, CI, II))
    D = Q - P
    M = len(P)
    # pairwise solve P_a + s D_a = P_b + u D_b
    dx = P[None, :, :] - P[:, None, :]           # P_b - P_a  (a rows, b cols)
    den = D[:, None, 0] * D[None, :, 1] - D[:, None, 1] * D[None, :, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (dx[..., 0] * D[None, :, 1] - dx[..., 1] * D[None, :, 0]) / den
        u = (dx[..., 0] * D[:, None, 1] - dx[..., 1] * D[:, None, 0]) / den
    ok = (np.abs(den) > 1e-12) & (s >= 0) & (s < 1) & (u >= 0) & (u < 1)
    ok &= np.triu(np.ones((M, M), bool), 1)
    # exclude adjacent segments of the same component
    same = CI[:, None] == CI[None, :]
    di = np.abs(II[:, None] - II[None, :])
    nsegs = np.array([comps[c].nseg() for c in CI])
    adj = same & ((di <= 1) | (di >= nsegs[:, None] - 1) & np.array([comps[c].closed for c in CI])[:, None])
    ok &= ~adj
    out = []
    for a, b in zip(*np.nonzero(ok)):
        sa, ub = s[a, b], u[a, b]
        za = ZP[a] + sa * (ZQ[a] - ZP[a])
        zb = ZP[b] + ub * (ZQ[b] - ZP[b])
        pt = P[a] + sa * D[a]
        ov, un = ((a, sa), (b, ub)) if za > zb else ((b, ub), (a, sa))
        do, du = D[ov[0]], D[un[0]]
        sign = 1 if (do[0] * du[1] - do[1] * du[0]) > 0 else -1
        out.append(dict(pt=pt, over=(int(CI[ov[0]]), II[ov[0]] + ov[1]), under=(int(CI[un[0]]), II[un[0]] + un[1]),
                        dover=do / np.linalg.norm(do), dunder=du / np.linalg.norm(du), sign=sign))
    return out


def _arclen(p, closed):
    seg = np.linalg.norm(np.diff(np.vstack([p, p[:1]]) if closed else p, axis=0)[:, :2], axis=1)
    return np.concatenate([[0], np.cumsum(seg)])


def _interp(p, s_cum, closed, s):
    """Point at arclength s along polyline (2D+z)."""
    pp = np.vstack([p, p[:1]]) if closed else p
    L = s_cum[-1]
    if closed:
        s = s % L
    s = np.clip(s, 0, L)
    i = np.searchsorted(s_cum, s, side="right") - 1
    i = np.clip(i, 0, len(pp) - 2)
    f = (s - s_cum[i]) / np.maximum(s_cum[i + 1] - s_cum[i], 1e-12)
    return pp[i] + np.asarray(f)[..., None] * (pp[i + 1] - pp[i])


def diagram_pieces(comps, gap=0.16, crossings=None):
    """Cut every under-strand around its crossings. Returns (pieces, crossings).

    pieces: list of dicts with 'pts' (k,3), 'comp', 's0','s1' (arclength range).
    """
    if crossings is None:
        crossings = find_crossings(comps)
    pieces = []
    for c, cp in enumerate(comps):
        sc = _arclen(cp.p, cp.closed)
        L = sc[-1]
        # param index -> arclength
        cuts = []
        for x in crossings:
            if x["under"][0] == c:
                idx = x["under"][1]
                i = int(np.floor(idx)) % cp.nseg()
                cuts.append(sc[i] + (idx - np.floor(idx)) * (sc[i + 1] - sc[i]))
        cuts = sorted(cuts)
        if not cuts:
            if cp.closed:
                pieces.append(dict(pts=np.vstack([cp.p, cp.p[:1]]), comp=c, s0=0, s1=L, closed=True))
            else:
                pieces.append(dict(pts=cp.p.copy(), comp=c, s0=0, s1=L, closed=False))
            continue
        intervals = []
        if cp.closed:
            for k in range(len(cuts)):
                a = cuts[k] + gap
                b = cuts[(k + 1) % len(cuts)] - gap + (L if k == len(cuts) - 1 else 0)
                if b > a:
                    intervals.append((a, b))
        else:
            edges = [-np.inf] + cuts + [np.inf]
            for k in range(len(edges) - 1):
                a = 0 if k == 0 else edges[k] + gap
                b = L if k == len(edges) - 2 else edges[k + 1] - gap
                if b > a:
                    intervals.append((a, b))
        for a, b in intervals:
            inner = sc[(sc > a) & (sc < b)] if b <= L else np.concatenate([sc[(sc > a)], sc[(sc > 0) & (sc < b - L)] + L])
            ss = np.concatenate([[a], inner, [b]])
            pts = _interp(cp.p, sc, cp.closed, ss)
            pieces.append(dict(pts=pts, comp=c, s0=a, s1=b, closed=False))
    return pieces, crossings


def to_scene(pts, scale=1.0, shift=ORIGIN):
    p = np.zeros((len(pts), 3))
    p[:, :2] = pts[:, :2] * scale
    return p + np.asarray(shift)


def neon_strand(pts, color, width=7, glow_on=True, core_white=0.55, opacity=1.0):
    core = VMobject().set_points_smoothly(pts) if len(pts) < 40 else VMobject().set_points_as_corners(pts)
    core.set_stroke(color=color, width=width, opacity=opacity)
    core.joint_type = LineJointType.ROUND
    hi = core.copy().set_stroke(color=interpolate_color(ManimColor(color), WHITE, core_white), width=width * 0.35,
                                opacity=0.9 * opacity)
    g = VGroup()
    if glow_on:
        for k, a in ((4.2, 0.05), (2.6, 0.10), (1.6, 0.22)):
            g.add(core.copy().set_stroke(color=color, width=width * k, opacity=a * opacity))
    g.add(core, hi)
    return g


def grad_color(palette, f):
    f = f % 1.0 * len(palette)
    i = int(f)
    return interpolate_color(ManimColor(palette[i % len(palette)]), ManimColor(palette[(i + 1) % len(palette)]), f - i)


def grad_strand(pts, pc, L, palette, width=7, chunk=10):
    """Strand coloured continuously along arclength (stable while the knot moves)."""
    g = VGroup()
    n = len(pts)
    smid = (pc["s0"] + pc["s1"]) / 2 / L
    base = VMobject().set_points_as_corners(pts)
    for k, a in ((4.2, 0.05), (2.6, 0.10), (1.6, 0.22)):
        g.add(base.copy().set_stroke(grad_color(palette, smid), width * k, a))
    seg = np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    tot = max(cum[-1], 1e-9)
    for i in range(0, n - 1, chunk):
        sub = pts[i:i + chunk + 1]
        f = (pc["s0"] + (pc["s1"] - pc["s0"]) * cum[min(i + chunk // 2, n - 1)] / tot) / L
        col = grad_color(palette, f)
        m = VMobject().set_points_as_corners(sub).set_stroke(col, width)
        hi = m.copy().set_stroke(interpolate_color(col, WHITE, 0.55), width * 0.35, 0.9)
        g.add(m, hi)
    return g


class KnotDiagram(VGroup):
    """A rendered knot/link diagram made from 3D components."""

    def __init__(self, comps, scale=1.0, shift=ORIGIN, colors=None, width=7, gap=None, color_fn=None,
                 glow_on=True, rot=None, grad=None, **kw):
        super().__init__(**kw)
        self.src = comps
        if rot is not None:
            comps = [Comp(c.p @ rot.T, c.closed) for c in comps]
        g = gap if gap is not None else 0.11 * width / 7 / max(scale, 1e-6) * 1.4
        self.pieces, self.crossings = diagram_pieces(comps, gap=g)
        self.scale_, self.shift_ = scale, np.asarray(shift, float)
        colors = colors or [CYAN, MAGENTA, GOLD, LIME]
        self.strands = VGroup()
        lens = [_arclen(c.p, c.closed)[-1] for c in comps]
        for k, pc in enumerate(self.pieces):
            if grad:
                self.strands.add(grad_strand(to_scene(pc["pts"], scale, shift), pc, lens[pc["comp"]], grad, width))
                continue
            col = color_fn(k, pc) if color_fn else colors[pc["comp"] % len(colors)]
            self.strands.add(neon_strand(to_scene(pc["pts"], scale, shift), col, width=width, glow_on=glow_on))
        self.add(self.strands)

    def cpoint(self, x):
        return np.array([*(x["pt"] * self.scale_), 0]) + self.shift_


def comps_of(*arrs, closed=True):
    return [Comp(a, closed) for a in arrs]


def ordered_arc_colors(diag, palette):
    return [palette[k % len(palette)] for k in range(len(diag.pieces))]


# ---------------------------------------------------------------- HUD
LEVEL_NAMES = {c["id"]: c["title"] for c in TIMING["chapters"]}
T0 = TIMING["chapters"][0]["segs"][3]["start"]       # speedrun timer starts at "计时开始"


class DigitClock(VGroup):
    """Speedrun clock MM:SS.d built from pre-rendered glyphs (fast per-frame)."""

    def __init__(self, size=30, color=INK):
        super().__init__()
        proto = [mono(str(d), size, color) for d in range(10)]
        w = max(p.width for p in proto) * 1.05
        self.slots = []
        x = 0
        layout = "dd:dd.d"
        for ch in layout:
            if ch == "d":
                grp = VGroup(*[p.copy().move_to([x, 0, 0], aligned_edge=DOWN) for p in proto])
                for m in grp:
                    m.align_to(proto[0], DOWN)
                    m.move_to([x, 0, 0])
                self.slots.append(grp)
                self.add(grp)
                x += w
            else:
                sep = mono(ch, size, color).move_to([x - w * 0.18, 0, 0])
                self.add(sep)
                x += w * 0.62
        self.set_value(0)

    def set_value(self, t):
        t = max(t, 0)
        mm, ss = int(t // 60), t % 60
        digits = [mm // 10 % 10, mm % 10, int(ss) // 10, int(ss) % 10, int((ss * 10) % 10)]
        for grp, d in zip(self.slots, digits):
            for k, m in enumerate(grp):
                m.set_opacity(1.0 if k == d else 0.0)
        return self


class Chapter(Scene):
    CH = 0

    def setup(self):
        config.text_dir = os.path.join(ROOT, "media", "texts", f"ch{self.CH:02d}")
        config.tex_dir = os.path.join(ROOT, "media", "Tex", f"ch{self.CH:02d}")
        os.makedirs(config.text_dir, exist_ok=True)
        os.makedirs(config.tex_dir, exist_ok=True)
        info = TIMING["chapters"][self.CH]
        self.info = info
        self.starts = [s["start"] for s in info["segs"]]
        self.durs = [s["dur"] for s in info["segs"]]
        self.total = info["total"]
        self.gstart = info["gstart"]
        bg = make_background(os.path.join(ROOT, f"bg_{config.pixel_width}x{config.pixel_height}.png"),
                             config.pixel_width, config.pixel_height)
        self.camera.background_image = bg
        self.camera.init_background()
        self.camera.reset()
        self.drift = 0.0

    # ---- timing helpers
    def D(self, k):
        return self.durs[k]

    def S(self, k):
        return self.starts[k]

    def E(self, k):
        return self.starts[k] + self.durs[k]

    def wait_to(self, t):
        dt = t - self.time
        if dt > 1e-3:
            self.wait(dt)
        elif dt < -0.08:
            print(f"[ch{self.CH}] DRIFT {dt:.2f}s at t={self.time:.2f}")

    def at(self, k, off=0.0):
        self.wait_to(self.S(k) + off)

    def finish(self):
        self.wait_to(self.total)

    def clear_stage(self, run_time=0.4):
        keep = getattr(self, "hud_group", None)
        ms = [m for m in self.mobjects if m is not keep]
        for m in ms:
            m.clear_updaters()
        if ms:
            self.play(FadeOut(Group(*ms)), run_time=run_time)
            self.remove(*ms)

    # ---- HUD
    def hud(self, show_level=True):
        clock = DigitClock(26, INK).to_corner(UR, buff=0.32)
        g0 = self.gstart - T0
        clock.add_updater(lambda m: m.set_value(g0 + self.time))
        dot = Dot(radius=0.06, color=RED_N).next_to(clock, LEFT, buff=0.16)
        rec = VGroup(dot, clock)
        bar = self.progress_bar()
        items = [rec, bar]
        if show_level and 1 <= self.CH <= 16:
            tag = VGroup(mono(f"LV.{self.CH:02d}", 22, CYAN), zh(LEVEL_NAMES[self.CH], 22, INK))
            tag.arrange(RIGHT, buff=0.2).to_corner(UL, buff=0.32)
            line = Line(tag.get_left(), tag.get_right(), stroke_width=1.4, color=CYAN, stroke_opacity=0.5)
            line.next_to(tag, DOWN, buff=0.08)
            items.append(VGroup(tag, line))
        self.hud_group = VGroup(*items)
        return self.hud_group

    def progress_bar(self):
        n = 16
        W = config.frame_width - 0.7
        y = -config.frame_height / 2 + 0.16
        x0 = -W / 2
        w = W / n
        grp = VGroup()
        cur = self.CH
        for i in range(1, n + 1):
            seg = Line([x0 + (i - 1) * w + 0.03, y, 0], [x0 + i * w - 0.03, y, 0], stroke_width=3.5)
            if i < cur or cur == 17:
                seg.set_stroke(CYAN, opacity=0.85)
            elif i == cur:
                seg.set_stroke(DIM, opacity=0.6)
            else:
                seg.set_stroke(DIM, opacity=0.35)
            grp.add(seg)
        if 1 <= cur <= 16:
            a = [x0 + (cur - 1) * w + 0.03, y, 0]
            b = [x0 + cur * w - 0.03, y, 0]
            fill = Line(a, a, stroke_width=3.5, color=GOLD)
            total = self.total
            fill.add_updater(lambda m: m.put_start_and_end_on(
                np.array(a), np.array(a) + (np.array(b) - np.array(a)) * max(min(self.time / total, 1), 0.002)))
            grp.add(fill)
        return grp

    # ---- title card for a level; runs during segment 0
    def title_card(self, knot_comps=None, knot_scale=0.55, rot_speed=0.5):
        k = self.CH
        d0 = self.D(0)
        big = mono(f"{k:02d}", 220, CYAN, weight=HEAVY).set_fill(opacity=0).set_stroke(CYAN, 2.5, 0.9)
        big_g = glow(big, CYAN, layers=((5, 0.05), (2.5, 0.12)))
        big_g.move_to(LEFT * 3.3 + UP * 0.35)
        lv = mono("LEVEL", 34, MAGENTA).next_to(big, UP, buff=0.12).align_to(big, LEFT)
        title = zh(LEVEL_NAMES[k], 58, INK, weight=BOLD)
        if title.width > 7.4:
            title.scale_to_fit_width(7.4)
        title.next_to(big, RIGHT, buff=0.7).align_to(big, DOWN).shift(UP * 0.3)
        sub = mono(f"STAGE {k:02d} / 16", 24, DIM, weight=NORMAL).next_to(title, UP, buff=0.3).align_to(title, LEFT)
        bar = Line(title.get_corner(DL) + DOWN * 0.25, title.get_corner(DR) + DOWN * 0.25 + RIGHT * 0.5,
                   stroke_width=4, color=GOLD)
        scan = Rectangle(width=config.frame_width, height=0.04).set_fill(CYAN, 0.6).set_stroke(width=0)
        scan.move_to(UP * 4.2)
        self.add(scan)
        self.play(scan.animate.move_to(DOWN * 4.2), FadeIn(big_g, scale=1.3), FadeIn(lv, shift=RIGHT * 0.3),
                  run_time=0.7, rate_func=rush_from)
        self.remove(scan)
        self.play(Write(title), FadeIn(sub, shift=UP * 0.2), Create(bar), run_time=min(1.0, d0 * 0.3))
        card = VGroup(big_g, lv, title, sub, bar)
        self.wait_to(self.E(0) + 0.05)
        self.play(FadeOut(card, shift=UP * 0.4, scale=0.9), run_time=0.35)
        return card

    def intro_level(self, **kw):
        """Standard level opening: HUD on, title card through segment 0."""
        self.at(0)
        self.title_card(**kw)
        self.add(self.hud())


def frozen(*ms):
    """Stop always_redraw/updaters so the mobjects can be animated (e.g. faded out)."""
    for m in ms:
        m.clear_updaters()
    return ms[0] if len(ms) == 1 else Group(*ms)


def rotating_knot(scene, comps, scale, shift=ORIGIN, speed=0.35, tilt=0.35, width=6, colors=None,
                  color_fn=None, t0=0.0, grad=None):
    """A knot diagram that re-projects itself every frame while spinning in 3D."""
    start = scene.time

    def build():
        t = scene.time - start + t0
        R = rot_matrix(tilt * np.sin(t * 0.4), t * speed, 0)
        return KnotDiagram(comps, scale=scale, shift=shift, width=width, colors=colors, color_fn=color_fn, rot=R,
                           grad=grad)

    return always_redraw(build)


def gradient_fn(palette, n_hint=None):
    def fn(k, pc):
        return palette[k % len(palette)]
    return fn


def alternating_from_2d(xy, h=0.6, w=None, start_over=True):
    """Lift a closed planar curve (n,2) to 3D so that its diagram is alternating."""
    xy = np.asarray(xy, float)
    flat = Comp(np.column_stack([xy, np.zeros(len(xy))]), True)
    xs = find_crossings([flat])
    sc = _arclen(flat.p, True)
    L = sc[-1]

    def s_of(idx):
        i = int(np.floor(idx)) % flat.n
        return sc[i] + (idx - np.floor(idx)) * (sc[i + 1] - sc[i])

    passes = []
    for x in xs:
        passes.append(s_of(x["over"][1]))
        passes.append(s_of(x["under"][1]))
    passes.sort()
    w = w or L / max(len(passes), 1) * 0.35
    s = sc[:-1]
    z = np.zeros(len(s))
    for k, sp in enumerate(passes):
        sgn = 1 if (k % 2 == 0) == start_over else -1
        d = (s - sp + L / 2) % L - L / 2
        z += sgn * h * np.exp(-(d / w) ** 2)
    return np.column_stack([xy, z])


def figure8_classic(n=480):
    t = np.linspace(0, TAU_, n, endpoint=False)
    x = 10 * (np.cos(t) + np.cos(3 * t)) + np.cos(2 * t) + np.cos(4 * t)
    y = 6 * np.sin(t) + 10 * np.sin(3 * t)
    return alternating_from_2d(np.column_stack([x, y]) / 7.0)


# ---------------------------------------------------------------- smoothing / resolving crossings
def resolve(comps, choice, r=0.22, crossings=None):
    """Smooth some crossings. choice: {crossing_idx: 'O'|'N'|'A'|'B'}.

    'O' = oriented (Seifert) smoothing, 'N' = the other one; 'A'/'B' follow the
    Kauffman convention (A == oriented smoothing at a positive crossing).
    Returns (new closed comps, crossings of the input).
    """
    xs = crossings if crossings is not None else find_crossings(comps)
    ch = {}
    for c, v in choice.items():
        if v in "AB":
            pos = xs[c]["sign"] > 0
            v = "O" if (v == "A") == pos else "N"
        ch[c] = v
    scs = [_arclen(cp.p, cp.closed) for cp in comps]

    def s_of(ci, idx):
        sc, cp = scs[ci], comps[ci]
        i = int(np.floor(idx)) % cp.nseg()
        return sc[i] + (idx - np.floor(idx)) * (sc[i + 1] - sc[i])

    passes = {ci: [] for ci in range(len(comps))}
    for k, x in enumerate(xs):
        for role in ("over", "under"):
            ci, idx = x[role]
            passes[ci].append((s_of(ci, idx), k, role[0]))
    edges = []          # dict(ci, s0, s1, start=(k,role), end=(k,role))
    in_edge, out_edge = {}, {}
    result = []
    for ci, ps in passes.items():
        L = scs[ci][-1]
        if not ps:
            result.append(comps[ci])
            continue
        ps.sort()
        m = len(ps)
        for j in range(m):
            s0, k0, r0 = ps[j]
            s1, k1, r1 = ps[(j + 1) % m]
            if j == m - 1 or m == 1:
                s1 += L
            e = len(edges)
            edges.append(dict(ci=ci, s0=s0, s1=s1, start=(k0, r0), end=(k1, r1)))
            out_edge[(k0, r0)] = e
            in_edge[(k1, r1)] = e

    def edge_pts(e, fwd):
        E = edges[e]
        a, b = E["s0"], E["s1"]
        if E["start"][0] in ch:
            a += r
        if E["end"][0] in ch:
            b -= r
        sc = scs[E["ci"]]
        L = sc[-1]
        inner = np.concatenate([sc[:-1] + L * k for k in range(3)])
        inner = inner[(inner > a) & (inner < b)]
        ss = np.concatenate([[a], inner, [b]])
        p = _interp(comps[E["ci"]].p, sc, True, ss)
        return p if fwd else p[::-1]

    other = {"o": "u", "u": "o"}
    used = set()
    for e0 in range(len(edges)):
        if (e0, True) in used or (e0, False) in used:
            continue
        pts = []
        e, fwd = e0, True
        while (e, fwd) not in used:
            used.add((e, fwd))
            seg = edge_pts(e, fwd)
            pts.append(seg)
            k, role = edges[e]["end"] if fwd else edges[e]["start"]
            port = "in" if fwd else "out"
            if k not in ch:
                e, fwd = (out_edge[(k, role)], True) if fwd else (in_edge[(k, role)], False)
                continue
            if ch[k] == "O":
                prole, pport = other[role], ("out" if port == "in" else "in")
            else:
                prole, pport = other[role], port
            ne, nf = (out_edge[(k, prole)], True) if pport == "out" else (in_edge[(k, prole)], False)
            nxt = edge_pts(ne, nf)
            P, Q, X = seg[-1], nxt[0], np.array([*xs[k]["pt"], 0.5 * (seg[-1][2] + nxt[0][2])])
            M = 0.5 * (P + Q)
            C = M + 0.12 * (X - M)
            tt = np.linspace(0, 1, 9)[1:-1, None]
            pts.append((1 - tt) ** 2 * P + 2 * (1 - tt) * tt * C + tt ** 2 * Q)
            e, fwd = ne, nf
        poly = np.vstack(pts)
        # drop near-duplicate consecutive points
        keep = np.concatenate([[True], np.linalg.norm(np.diff(poly[:, :2], axis=0), axis=1) > 1e-6])
        result.append(Comp(poly[keep], True))
    return result, xs


def flip_crossings(comps, which, h=1.2, w=None):
    """Switch over/under at the listed crossings by bumping z locally."""
    xs = find_crossings(comps)
    new = [Comp(c.p.copy(), c.closed) for c in comps]
    for k in which:
        x = xs[k]
        for role, sgn in (("over", -1), ("under", 1)):
            ci, idx = x[role]
            cp = new[ci]
            n = cp.n
            d = (np.arange(n) - idx + n / 2) % n - n / 2
            ww = w or n / 60
            cp.p[:, 2] += sgn * h * np.exp(-(d / ww) ** 2)
    return new


# ---------------------------------------------------------------- Laurent polynomials in A
def lp_mul(p, q):
    out = {}
    for a, x in p.items():
        for b, y in q.items():
            out[a + b] = out.get(a + b, 0) + x * y
    return {k: v for k, v in out.items() if v != 0}


def lp_add(p, q):
    out = dict(p)
    for k, v in q.items():
        out[k] = out.get(k, 0) + v
    return {k: v for k, v in out.items() if v != 0}


def lp_pow(p, n):
    out = {0: 1}
    for _ in range(n):
        out = lp_mul(out, p)
    return out


DELTA = {2: -1, -2: -1}


def bracket_states(comps):
    xs = find_crossings(comps)
    n = len(xs)
    states = []
    for mask in range(2 ** n):
        choice = {k: ("A" if not (mask >> k) & 1 else "B") for k in range(n)}
        loops, _ = resolve(comps, choice, crossings=xs)
        a = sum(1 for v in choice.values() if v == "A")
        states.append(dict(choice=choice, loops=loops, a=a, b=n - a))
    total = {}
    for s in states:
        term = lp_mul({s["a"] - s["b"]: 1}, lp_pow(DELTA, len(s["loops"]) - 1))
        total = lp_add(total, term)
    return states, total, xs


# ---------------------------------------------------------------- glyphs for skein relations
def arrow_tip(p, d, color, size=0.16):
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0], 0])
    tri = Polygon(p + d * size * 0.6, p - d * size * 0.6 + n * size * 0.55, p - d * size * 0.6 - n * size * 0.55)
    return tri.set_fill(color, 1).set_stroke(color, 1)


def glyph(kind, size=0.9, color=CYAN, frame=True, arrows=True, width=5):
    """Local skein pictures: 'pos','neg','zero','inf','A','B','cross','kink','line'."""
    s = size
    g = VGroup()
    k = 0.5 * s

    def bez(P, C, Q, n=30):
        t = np.linspace(0, 1, n)[:, None]
        return (1 - t) ** 2 * np.array(P) + 2 * (1 - t) * t * np.array(C) + t ** 2 * np.array(Q)

    if kind in ("pos", "neg", "cross", "A", "B"):
        t = np.linspace(-1, 1, 40)
        s1 = np.stack([t * k, t * k, np.ones_like(t)], 1)        # SW -> NE
        s2 = np.stack([-t * k, t * k, -np.ones_like(t)], 1)      # SE -> NW
        if kind == "neg":
            s1[:, 2], s2[:, 2] = -1, 1
        d = KnotDiagram([Comp(s1, False), Comp(s2, False)], colors=[color, color], width=width,
                        gap=0.14 * s / 0.9)
        g.add(d)
        if arrows and kind in ("pos", "neg"):
            g.add(arrow_tip(np.array([k, k, 0]), [1, 1, 0], color), arrow_tip(np.array([-k, k, 0]), [-1, 1, 0], color))
    elif kind in ("zero", "Asm"):          # ")(" : left & right arcs
        a1 = bez([-k, -k, 0], [-0.15 * s, 0, 0], [-k, k, 0])
        a2 = bez([k, -k, 0], [0.15 * s, 0, 0], [k, k, 0])
        g.add(neon_strand(a1, color, width), neon_strand(a2, color, width))
        if arrows and kind == "zero":
            g.add(arrow_tip(a1[-1], a1[-1] - a1[-3], color), arrow_tip(a2[-1], a2[-1] - a2[-3], color))
    elif kind in ("inf", "Bsm"):           # "≍" : top & bottom arcs
        a1 = bez([-k, k, 0], [0, 0.15 * s, 0], [k, k, 0])
        a2 = bez([-k, -k, 0], [0, -0.15 * s, 0], [k, -k, 0])
        g.add(neon_strand(a1, color, width), neon_strand(a2, color, width))
    elif kind == "kink":
        u = np.linspace(-np.pi, np.pi, 160)
        lam = 2.4
        y = (u - lam * np.sin(u)) / (2 * np.pi) * 1.0 * s
        x = (-lam * np.cos(u) + lam) / 5.5 * s - 0.18 * s
        z = u
        p = np.stack([x, y, z], 1)
        g.add(KnotDiagram([Comp(p, False)], colors=[color], width=width, gap=0.12 * s / 0.9))
    elif kind == "line":
        t = np.linspace(-k, k, 20)
        g.add(neon_strand(np.stack([np.zeros_like(t), t, np.zeros_like(t)], 1), color, width))
    elif kind == "circle":
        g.add(neon_strand(circle_pts(80, 0.32 * s)[:, :] * [1, 1, 0], color, width))
    if frame:
        c = Circle(radius=0.78 * s).set_stroke(DIM, 1.5, 0.6)
        g.add(DashedVMobject(c, num_dashes=28))
    return g


def row(*items, buff=0.12, size=44, color=INK):
    """Arrange TeX strings and mobjects in a row."""
    mobs = [tex(i, size, color) if isinstance(i, str) else i for i in items]
    return VGroup(*mobs).arrange(RIGHT, buff=buff)


# ---------------------------------------------------------------- checkerboard shading
def evenodd_image(polys, color, opacity=0.35, ppu=110, margin=0.1, ss=2):
    """Rasterise even-odd fill of closed scene-space polylines. Returns ImageMobject."""
    allp = np.vstack([p[:, :2] for p in polys])
    x0, y0 = allp.min(0) - margin
    x1, y1 = allp.max(0) + margin
    W = int((x1 - x0) * ppu) * ss
    H = int((y1 - y0) * ppu) * ss
    mask = np.zeros((H, W), bool)
    ys = y1 - (np.arange(H) + 0.5) / (ppu * ss)
    segs = []
    for p in polys:
        q = np.vstack([p[:, :2], p[:1, :2]])
        segs.append(np.stack([q[:-1], q[1:]], 1))
    S = np.concatenate(segs)
    A, B = S[:, 0], S[:, 1]
    for r, y in enumerate(ys):
        m = (A[:, 1] > y) != (B[:, 1] > y)
        if not m.any():
            continue
        a, b = A[m], B[m]
        xx = a[:, 0] + (y - a[:, 1]) * (b[:, 0] - a[:, 0]) / (b[:, 1] - a[:, 1])
        xx = np.sort((xx - x0) * ppu * ss)
        for k in range(0, len(xx) - 1, 2):
            mask[r, int(max(xx[k], 0)):int(min(xx[k + 1], W))] = True
    m = mask.reshape(H // ss, ss, W // ss, ss).mean((1, 3)) if ss > 1 else mask.astype(float)
    rgb = np.array(ManimColor(color).to_rgb()) * 255
    img = np.zeros((m.shape[0], m.shape[1], 4), np.uint8)
    img[..., :3] = rgb
    img[..., 3] = (m * opacity * 255).astype(np.uint8)
    im = ImageMobject(img)
    im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["linear"])
    im.stretch_to_fit_width(m.shape[1] / ppu).stretch_to_fit_height(m.shape[0] / ppu)
    im.move_to([(x0 + x1) / 2 - (x1 - x0 - m.shape[1] / ppu) / 2, (y0 + y1) / 2 + (y1 - y0 - m.shape[0] / ppu) / 2, 0])
    im.mask_ = m
    im.box_ = (x0, y1, ppu)
    return im


def region_centroids(im, min_px=30):
    from scipy import ndimage
    lab, n = ndimage.label(im.mask_ > 0.5)
    x0, y1, ppu = im.box_
    out = []
    for i in range(1, n + 1):
        ys, xs_ = np.nonzero(lab == i)
        if len(xs_) < min_px:
            continue
        out.append(np.array([x0 + (xs_.mean() + 0.5) / ppu, y1 - (ys.mean() + 0.5) / ppu, 0]))
    return out


# ---------------------------------------------------------------- torus wireframe
def torus_point(u, v, R=2.0, r=0.8):
    return np.stack([(R + r * np.cos(v)) * np.cos(u), (R + r * np.cos(v)) * np.sin(u), r * np.sin(v)], -1)


def depth_curve(P, rot, scale, shift, color, width=2.5, base_op=0.9, chunks=24, glow_on=False):
    """Polyline in 3D drawn with depth-dependent opacity (front brighter)."""
    Q = P @ rot.T
    zmin, zmax = -3, 3
    g = VGroup()
    n = len(Q)
    step = max(n // chunks, 2)
    for i in range(0, n - 1, step):
        seg = Q[i:i + step + 1]
        z = seg[:, 2].mean()
        op = base_op * (0.18 + 0.82 * np.clip((z - zmin) / (zmax - zmin), 0, 1))
        pts = np.zeros((len(seg), 3))
        pts[:, :2] = seg[:, :2] * scale
        pts += shift
        m = VMobject().set_points_as_corners(pts).set_stroke(color, width, op)
        g.add(m)
        if glow_on:
            g.add(m.copy().set_stroke(color, width * 3.5, op * 0.15))
    return g


def torus_wire(rot, scale=1.0, shift=ORIGIN, R=2.0, r=0.8, nu=24, nv=12, color=SKY, width=1.6):
    g = VGroup()
    shift = np.asarray(shift, float)
    for i in range(nu):
        u = TAU_ * i / nu
        v = np.linspace(0, TAU_, 60)
        g.add(depth_curve(torus_point(np.full_like(v, u), v, R, r), rot, scale, shift, color, width, 0.55, 6))
    for j in range(nv):
        v = TAU_ * j / nv
        u = np.linspace(0, TAU_, 140)
        g.add(depth_curve(torus_point(u, np.full_like(u, v), R, r), rot, scale, shift, color, width, 0.55, 14))
    return g


# ---------------------------------------------------------------- connected sum helper
def open_at(p, where="right", cut=0.5):
    """Open closed curve p near its extreme point. Returns open polyline (ends near the extreme)."""
    i = np.argmax(p[:, 0]) if where == "right" else np.argmin(p[:, 0])
    q = np.roll(p, -i, axis=0)
    sc = _arclen(q, True)
    L = sc[-1]
    keep = (sc[:-1] > cut / 2) & (sc[:-1] < L - cut / 2)
    return q[keep]


def connect_sum(pa, pb, gapx=1.2, cut=0.6):
    """Connected sum of two closed 3D curves placed side by side (pa left, pb right)."""
    A = open_at(pa, "right", cut)
    B = open_at(pb, "left", cut)
    A = A - [A[:, 0].max() + gapx / 2, 0, 0]
    B = B - [B[:, 0].min() - gapx / 2, 0, 0]
    # ensure A runs from its lower end to its upper end and B from upper to lower
    if A[0, 1] > A[-1, 1]:
        A = A[::-1]
    if B[0, 1] < B[-1, 1]:
        B = B[::-1]

    def bridge(P, Q, n=24):
        t = np.linspace(0, 1, n)[1:-1, None]
        mid = 0.5 * (P + Q)
        return (1 - t) ** 2 * P + 2 * (1 - t) * t * mid + t ** 2 * Q

    return np.vstack([A, bridge(A[-1], B[0]), B, bridge(B[-1], A[0])])


# ---------------------------------------------------------------- genus-one Seifert surface schematic
def seifert_schematic(scale=1.0, color=CYAN, fillc="#0f2a44", curves=True, bandw=30):
    s = scale
    disk = RoundedRectangle(width=4.2 * s, height=1.3 * s, corner_radius=0.35 * s).shift(DOWN * 0.9 * s)
    top = disk.get_top()[1] - 0.05 * s

    def band(x1, x2, h):
        P = np.array([x1 * s, top - 0.25 * s, 0])
        Q = np.array([x2 * s, top - 0.25 * s, 0])
        return CubicBezier(P, P + UP * h * s, Q + UP * h * s, Q)

    ba = band(-1.5, 0.5, 2.6)
    bb = band(-0.5, 1.5, 2.6)
    out = VGroup()
    out.add(disk.copy().set_fill(opacity=0).set_stroke(color, 4))
    up_parts, down_parts = VGroup(), VGroup()

    def core(b, colr):
        pts = np.array([b.point_from_proportion(t) for t in np.linspace(0, 1, 50)])
        P, Q = pts[0], pts[-1]
        back = np.array([Q + (P - Q) * t + DOWN * 0.35 * s * np.sin(np.pi * t) for t in np.linspace(0, 1, 30)])
        return (VMobject().set_points_smoothly(pts).set_stroke(colr, 4),
                VMobject().set_points_smoothly(back).set_stroke(colr, 4))

    ca_up, ca_dn = core(ba, RED_N)
    cb_up, cb_dn = core(bb, GOLD)
    fa, fb = ba.copy().set_stroke(fillc, bandw * s, 1), bb.copy().set_stroke(fillc, bandw * s, 1)
    out.add(ba.copy().set_stroke(color, bandw * 1.25 * s, 1), fa)
    if curves:
        out.add(ca_up)
    out.add(bb.copy().set_stroke(color, bandw * 1.25 * s, 1), fb)
    if curves:
        out.add(cb_up)
    out.add(disk.copy().scale(0.985).set_fill(fillc, 1).set_stroke(width=0))
    if curves:
        out.add(ca_dn, cb_dn)
    out.curves = VGroup(VGroup(ca_up, ca_dn), VGroup(cb_up, cb_dn))
    out.bands = (fa, fb)
    return out


def smooth_closed(p, iters=6, k=0.5, n_out=None):
    q = np.asarray(p, float).copy()
    for _ in range(iters):
        q = q + k * (0.5 * (np.roll(q, 1, 0) + np.roll(q, -1, 0)) - q)
    if n_out:
        sc = _arclen(q, True)
        q = _interp(q, sc, True, np.linspace(0, sc[-1], n_out, endpoint=False))
    return q


def alternating_link(xys, h=0.6, w=None):
    """Lift several closed planar curves to an alternating link (searches component parities)."""
    flats = [Comp(np.column_stack([xy, np.zeros(len(xy))]), True) for xy in xys]
    xs = find_crossings(flats)
    scs = [_arclen(c.p, True) for c in flats]

    def s_of(ci, idx):
        sc, cp = scs[ci], flats[ci]
        i = int(np.floor(idx)) % cp.n
        return sc[i] + (idx - np.floor(idx)) * (sc[i + 1] - sc[i])

    passes = {ci: [] for ci in range(len(flats))}
    for k, x in enumerate(xs):
        for role in ("over", "under"):
            ci, idx = x[role]
            passes[ci].append((s_of(ci, idx), k))
    for ci in passes:
        passes[ci].sort()
    nc = len(flats)
    for mask in range(2 ** nc):
        assign = {}
        for ci in range(nc):
            for j, (sv, k) in enumerate(passes[ci]):
                assign.setdefault(k, []).append((ci, sv, (j % 2 == 0) == bool((mask >> ci) & 1)))
        if all(len(v) == 2 and v[0][2] != v[1][2] for v in assign.values()):
            break
    out = []
    for ci, fl in enumerate(flats):
        sc = scs[ci]
        L = sc[-1]
        s = sc[:-1]
        z = np.zeros(len(s))
        ww = w or L / max(len(passes[ci]), 1) * 0.35
        for k, v in assign.items():
            for (cj, sv, over) in v:
                if cj != ci:
                    continue
                d = (s - sv + L / 2) % L - L / 2
                z += (1 if over else -1) * h * np.exp(-(d / ww) ** 2)
        out.append(np.column_stack([fl.p[:, :2], z]))
    return out


def borromean_pts(n=200, r=1.0, d=0.62):
    xys = []
    for k in range(3):
        a = PI / 2 + k * TAU_ / 3
        c = d * np.array([np.cos(a), np.sin(a)])
        t = np.linspace(0, TAU_, n, endpoint=False)
        xys.append(np.column_stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)]))
    return alternating_link(xys)


def hopf_pts(n=200, r=1.0, d=1.0):
    t = np.linspace(0, TAU_, n, endpoint=False)
    a = np.column_stack([-d / 2 + r * np.cos(t), r * np.sin(t)])
    b = np.column_stack([d / 2 + r * np.cos(t), r * np.sin(t)])
    return alternating_link([a, b])


def figure8_pts2(n=480):
    return figure8_classic(n) @ rot_matrix(0, 0, PI / 2).T


def check_mark(color=LIME, size=0.5):
    m = VMobject().set_points_as_corners([[-0.5, 0, 0], [-0.15, -0.38, 0], [0.55, 0.45, 0]]).scale(size)
    return glow(m.set_stroke(color, 7), color)


def cross_mark(color=RED_N, size=0.45):
    a = Line([-0.5, -0.5, 0], [0.5, 0.5, 0]).scale(size)
    b = Line([-0.5, 0.5, 0], [0.5, -0.5, 0]).scale(size)
    return glow(VGroup(a, b).set_stroke(color, 7), color)


def stamp(text="CLEAR!", color=GOLD, size=64):
    t = mono(text, size, color, weight=HEAVY)
    box = SurroundingRectangle(t, buff=0.18, corner_radius=0.08).set_stroke(color, 5)
    g = VGroup(glow(box, color), t).rotate(8 * DEGREES)
    return g


def labeled_panel(label, w=3.6, h=3.0, color=CYAN):
    p = panel(w, h, color, 0.04, 0.45)
    t = mono(label, 24, color).next_to(p.get_corner(UL), DR, buff=0.15)
    return VGroup(p, t)


def colored_cross(c_over, c_u1, c_u2, size=1.0, width=6):
    k = 0.5 * size
    t = np.linspace(-1, 1, 40)
    s1 = np.stack([t * k, t * k, np.ones_like(t)], 1)
    s2 = np.stack([-t * k, t * k, -np.ones_like(t)], 1)

    def cf(i, pc):
        if pc["comp"] == 0:
            return c_over
        return c_u1 if pc["s0"] < 0.1 else c_u2

    return KnotDiagram([Comp(s1, False), Comp(s2, False)], color_fn=cf, width=width, gap=0.15 * size)


def knot_morph(scene, A, B, tracker, scale, shift=ORIGIN, width=6, colors=None, color_fn=None, rot=None):
    """always_redraw diagram interpolating 3D curves A->B by tracker in [0,1]."""
    def build():
        a = tracker.get_value()
        a = smooth(np.clip(a, 0, 1))
        P = [Comp((1 - a) * x.p + a * y.p, x.closed) for x, y in zip(A, B)]
        return KnotDiagram(P, scale=scale, shift=shift, width=width, colors=colors, color_fn=color_fn, rot=rot)
    return always_redraw(build)


def texs(*parts, size=44, color=INK, **kw):
    return MathTex(*parts, tex_template=TEX, font_size=size, color=color, **kw)
