"""合成一帧：背景 → 场景 → 辉光 → 暗角 → 故障效果 → 说明文字，原始像素通过管道交给 ffmpeg。

每一帧只由时间 t 决定（随机数都在启动时用固定种子生成），所以整段视频可以切成几块并行渲染。
"""

import subprocess
import sys

import numpy as np
import skia

from gfx import (BG, CYAN, GOLD, H, MAGENTA, W, WHITE, background, clamp, col, draw_tokens, eout, env, font,
                 paint, radial, rich_lines, ring_flare, smooth, text, text_width)
from gfx import FPS


# ---------------------------------------------------------------- 章节卡与页眉
def chapter_card(c, u, ch):
    """章节开头约 4 秒的大标题：编号 + 中文标题 + 英文副标题。"""
    num, zh, en = ch
    if u > 4.4:
        return
    a = env(u, 0.05, 4.2, 0.35, 0.7)
    cx, cy = W / 2, H / 2 - 20
    # 横向闪过的一道光
    if u < 0.9:
        k = eout(u / 0.9)
        x = -200 + (W + 400) * k
        c.drawRect(skia.Rect(0, cy - 1.5, x, cy + 1.5), paint(CYAN, 0.6 * (1 - k)))
        c.drawCircle(x, cy, 160, paint(CYAN, 1, shader=radial(x, cy, 160, CYAN, 0.5 * (1 - k))))
    s = 1.12 - 0.12 * eout(u / 1.0)
    out = smooth((u - 3.5) / 0.7)
    s *= 1 + 0.06 * out
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    nw = text_width(num, 230, "orb", track=6)
    tw = max(text_width(zh, 84, "serif"), text_width(en, 22, "orbm", track=7))
    nx = -(nw + 70 + tw) / 2
    # 编号：描边发光 + 半透明填充
    text(c, num, nx, 80, 230, "orb", MAGENTA, 0.20 * a, align="l", track=6)
    text(c, num, nx, 80, 230, "orb", MAGENTA, a, align="l", track=6, p=paint(MAGENTA, 0.85 * a, stroke=2.5))
    # 中文标题逐字出现
    zx = nx + nw + 70
    f = font("serif", 84)
    x = zx
    for i, ch_ in enumerate(zh):
        k = clamp((u - 0.35 - i * 0.06) / 0.45)
        if k > 0:
            c.drawString(ch_, x, 22 + 18 * (1 - eout(k)), f, paint(WHITE, a * smooth(k)))
        x += f.measureText(ch_)
    k = clamp((u - 0.9) / 0.8)
    c.drawRect(skia.Rect(zx, 52, zx + (x - zx) * eout(k), 54.5), paint(GOLD, 0.8 * a))
    text(c, en, zx, 96, 22, "orbm", CYAN, 0.75 * a * smooth(k), align="l", track=7)
    c.restore()
    ring_flare(c, cx + (nx + nw / 2) * s, cy - 2, 200, (u - 0.2) / 1.6, MAGENTA, a)


def header(c, u, ch, dur):
    num, zh, en = ch
    a = env(u, 3.9, dur, 0.8, 0.5)
    if a <= 0.003:
        return
    text(c, num, 64, 82, 30, "orb", MAGENTA, a, align="l", track=2)
    w = text_width(num, 30, "orb", track=2)
    c.drawRect(skia.Rect(64 + w + 16, 60, 64 + w + 18, 88), paint(WHITE, 0.35 * a))
    text(c, zh, 64 + w + 34, 83, 28, "sans", WHITE, 0.85 * a, align="l")


def hud(c, t, a):
    if a <= 0.003:
        return
    m, L = 30, 30
    p = paint(CYAN, 0.32 * a, stroke=1.5, cap=False)
    for sx, sy in ((m, m), (W - m, m), (m, H - m), (W - m, H - m)):
        dx = L if sx < W / 2 else -L
        dy = L if sy < H / 2 else -L
        c.drawLine(sx, sy, sx + dx, sy, p)
        c.drawLine(sx, sy, sx, sy + dy, p)
    text(c, "WHEN PROBABILITY SPINS", W - 64, 74, 14, "orbm", CYAN, 0.42 * a, align="r", track=5)
    mm, ss = divmod(t, 60)
    text(c, f"T+{int(mm):02d}:{ss:05.2f}", W - 64, 100, 17, "mono", WHITE, 0.38 * a, align="r")


# ---------------------------------------------------------------- 说明文字
CAP_SIZE = 40
CAP_Y = 1004


def captions(c, scene, u):
    for t0, t1, s in scene.caps:
        if not (t0 - 0.1 <= u <= t1 + 0.1):
            continue
        a = env(u, t0, t1, 0.35, 0.35)
        if a <= 0.003:
            continue
        lines = rich_lines(s, CAP_SIZE, "sans", 1580)
        n = len(lines)
        lh = CAP_SIZE * 1.42
        y0 = CAP_Y - (n - 1) * lh
        rise = 10 * (1 - eout((u - t0) / 0.5))
        # 打字机：按 token 数推进，速度约每秒 45 个
        shown = int((u - t0) * 45) + 1
        for k, toks in enumerate(lines):
            upto = max(0, min(len(toks), shown - sum(len(l) for l in lines[:k])))
            if upto <= 0:
                continue
            y = y0 + k * lh + rise
            draw_tokens(c, toks, W / 2, y, CAP_SIZE, WHITE, a, upto=upto)


def caption_shadow(c, scene, u):
    """说明文字下面的深色渐变带，只在有字的时候出现。"""
    a = 0.0
    for t0, t1, s in scene.caps:
        a = max(a, env(u, t0 - 0.2, t1 + 0.2, 0.4, 0.4))
    if a <= 0.003:
        return
    top = H - 210
    c.drawRect(skia.Rect(0, top, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, top), skia.Point(0, H)], [col((0, 0, 0), 0), col((0, 0, 0), 0.62 * a)])))


# ---------------------------------------------------------------- 合成一帧
class Renderer:
    def __init__(self, tl=None):
        if tl is None:
            import timeline
            tl = timeline.TIMELINE
        self.tl = tl
        self.main = skia.Surface(W, H)
        self.fg = skia.Surface(W, H)
        self.half = skia.Surface(W // 2, H // 2)
        self.small0 = skia.Surface(W // 4, H // 4)
        self.glow = skia.Surface(W // 4, H // 4)
        self.glitches = self.tl.glitch_times()
        vs = skia.Surface(W, H)
        vc = vs.getCanvas()
        vc.clear(0)
        vc.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            skia.Point(W / 2, H / 2), W * 0.72, [col(BG, 0), col(BG, 0), col((0, 0, 0), 0.72)], [0, 0.55, 1])))
        self.vignette = vs.makeImageSnapshot()

    def bloom(self, img, canvas, a):
        """辉光：缩到 1/4（分两次对半缩，细线不闪），两种半径模糊后叠加，再放大垫在前景下面。

        CPU 上的 skia 做全分辨率的加法混合很慢，所以加法只在小图上做。
        """
        lin = skia.SamplingOptions(skia.FilterMode.kLinear)
        hc = self.half.getCanvas()
        hc.clear(0)
        hc.drawImageRect(img, skia.Rect(0, 0, W // 2, H // 2), lin)
        c0 = self.small0.getCanvas()
        c0.clear(0)
        c0.drawImageRect(self.half.makeImageSnapshot(), skia.Rect(0, 0, W // 4, H // 4), lin)
        small = self.small0.makeImageSnapshot()
        gc = self.glow.getCanvas()
        gc.clear(0)
        for sigma, strength in ((2.2, 0.95), (8.0, 0.85)):
            sp = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma), BlendMode=skia.BlendMode.kPlus)
            sp.setAlphaf(clamp(strength * a))
            gc.drawImage(small, 0, 0, skia.SamplingOptions(), sp)
        canvas.drawImageRect(self.glow.makeImageSnapshot(), skia.Rect(0, 0, W, H), lin)

    def frame(self, t):
        sc, u = self.tl.at(t)
        mc = self.main.getCanvas()
        background(mc, t, sc.theme, sc.spin)

        fc = self.fg.getCanvas()
        fc.clear(0)
        sc.draw(fc, u)
        if sc.chapter:
            chapter_card(fc, u, sc.chapter)
            header(fc, u, sc.chapter, sc.dur)
        hud(fc, t, sc.hud * env(u, 0.3, sc.dur, 0.6, 0.4))
        fg = self.fg.makeImageSnapshot()

        # 场景首尾淡入淡出；章节开头轻微放大回落
        fade = env(u, 0.0, sc.dur, sc.fade_in, sc.fade_out)
        z = 1 + 0.03 * (1 - eout(u / 0.7)) if sc.chapter else 1.0
        mc.save()
        if z != 1.0:
            mc.translate(W / 2, H / 2)
            mc.scale(z, z)
            mc.translate(-W / 2, -H / 2)
        self.bloom(fg, mc, fade * sc.bloom)
        fp = skia.Paint()
        fp.setAlphaf(fade)
        mc.drawImage(fg, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), fp)
        mc.restore()

        mc.drawImage(self.vignette, 0, 0)
        self.glitch(mc, t)
        caption_shadow(mc, sc, u)
        captions(mc, sc, u)
        # 片头片尾黑场
        if t < 0.8:
            mc.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), 1 - smooth(t / 0.8)))
        end = self.tl.duration
        if t > end - 1.5:
            mc.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), smooth((t - end + 1.5) / 1.4)))
        return self.main.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)

    CHANNELS = [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    ]

    def glitch(self, mc, t):
        """故障效果：RGB 三个通道错开，再随机横向错位几条。"""
        g = 0.0
        for tg, strength in self.glitches:
            if 0 <= t - tg < 0.3:
                g = max(g, strength * (1 - (t - tg) / 0.3) ** 2)
        if g < 0.02:
            return
        img = self.main.makeImageSnapshot()
        dx = 3 + 16 * g
        mc.clear(skia.ColorBLACK)
        for k, off in enumerate((dx, 0, -dx)):
            p = skia.Paint(BlendMode=skia.BlendMode.kPlus)
            p.setColorFilter(skia.ColorFilters.Matrix(self.CHANNELS[k]))
            mc.drawImage(img, off, 0, skia.SamplingOptions(), p)
        rng = np.random.default_rng(int(t * 1000))
        snap = self.main.makeImageSnapshot()
        for _ in range(int(2 + 5 * g)):
            y = float(rng.integers(0, H - 40))
            h = float(rng.integers(6, 36))
            sh = float(rng.integers(-50, 50) * g)
            mc.save()
            mc.clipRect(skia.Rect(0, y, W, y + h))
            mc.drawImage(snap, sh, 0)
            mc.restore()


def encode_range(f0, f1, out, crf=18):
    r = Renderer()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-x264-params", "keyint=60", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        proc.stdin.write(r.frame(f / FPS).tobytes())
        if (f - f0) % 300 == 0:
            print(f"  [{out.name}] {f - f0}/{f1 - f0}", file=sys.stderr, flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg 编码失败")
    return out


def still(t, out, tl=None):
    from PIL import Image
    arr = Renderer(tl).frame(t)
    Image.fromarray(arr[..., :3]).save(out)
