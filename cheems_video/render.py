"""逐帧渲染：画场景 → 时间卡 → 字幕 → 颗粒 → 黑场过渡，然后把原始像素喂给 ffmpeg。

用法：
  python render.py --work DIR --seg 0 12.5 out.mp4   # 渲染一段（秒）
  python render.py --work DIR --still 123.4 a.png      # 单帧
"""
from __future__ import annotations

import argparse
import subprocess
import sys

import numpy as np
import skia

import engine
import overlays as ov
from gfx import FPS, H, W, clamp, fill
from scenes import SCENE_FUNCS

NO_SUB = {"rules", "hidden"}


def render_frame(surface, tl, T):
    c = surface.getCanvas()
    c.save()
    c.clear(skia.ColorBLACK)
    sc, t = tl.find(T)
    SCENE_FUNCS[sc.name](c, t, sc)
    c.restore()
    c.save()
    card = sc.card_at(t)
    if card is not None:
        ov.time_card(c, card.text, card.sub, (t - card.start) / card.dur, t)
    ln = sc.line_at(t)
    if ln is not None and ln.who not in NO_SUB and sc.name != "cold_open":
        a = clamp((t - ln.start) / 0.12) * clamp((ln.start + ln.pre + ln.audio_len + 0.6 - t) / 0.2)
        ov.subtitle(c, ln.name, ln.sub, a)
    ov.grain(c, T, 0.05)
    fade = 0.0
    if t < engine.FADE and T > 0.01:
        fade = 1 - t / engine.FADE
    if t > sc.dur - engine.FADE:
        fade = max(fade, (t - (sc.dur - engine.FADE)) / engine.FADE)
    if T < 0.6:
        fade = max(fade, 1 - T / 0.6)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", clamp(fade)))
    c.restore()


def frames_range(tl, a, b):
    i0 = int(round(a * FPS))
    i1 = int(round(min(b, tl.dur) * FPS))
    return range(i0, i1)


def render_segment(work, a, b, out, crf=18, preset="medium"):
    tl = engine.load(work)
    surface = skia.Surface(W, H)
    buf = np.empty((H, W, 4), np.uint8)
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-threads", "2", "-tune", "animation", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rng = frames_range(tl, a, b)
    for n, i in enumerate(rng):
        render_frame(surface, tl, i / FPS)
        surface.getCanvas().readPixels(info, buf, 0, 0)
        proc.stdin.write(buf.tobytes())
        if n % 300 == 0:
            print(f"[{out}] {n}/{len(rng)}", flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        sys.exit(f"ffmpeg 失败：{out}")


def still(work, T, out):
    tl = engine.load(work)
    surface = skia.Surface(W, H)
    render_frame(surface, tl, T)
    surface.makeImageSnapshot().save(out, skia.kPNG)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--seg", nargs=3)
    ap.add_argument("--still", nargs=2)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()
    if args.seg:
        render_segment(args.work, float(args.seg[0]), float(args.seg[1]), args.seg[2], args.crf, args.preset)
    elif args.still:
        still(args.work, float(args.still[0]), args.still[1])
