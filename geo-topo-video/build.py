# -*- coding: utf-8 -*-
"""合成流水线：渲染 → 拼接 → 配音/配乐 → 背景与字幕 → 成片。

用法:
  python build.py render [--preview]     # 并行渲染全部镜头（1080p30；--preview 为 480p15）
  python build.py assemble [--preview]   # 拼接 + 音频 + 字幕 + 背景，输出 output/
"""
import json
import os
import re
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import uniform_filter1d
from scipy.signal import oaconvolve, resample_poly, butter, sosfilt

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
BUILD = os.path.join(ROOT, "build")
MANIM = os.path.join(os.path.dirname(sys.executable), "manim")
SR = 48000

ORDER = [
    ("s0_intro_outro.py", "Intro"),
    ("s1_monk.py", "Monk"),
    ("s2_antipodal.py", "Antipodal"),
    ("s2_antipodal.py", "AntipodalBU"),
    ("s3_utilities.py", "Utilities"),
    ("s3_utilities.py", "UtilitiesTorus"),
    ("s4_buffon.py", "Buffon"),
    ("s5_rectangle.py", "Rectangle2D"),
    ("s5_rectangle.py", "RectangleLift"),
    ("s5_rectangle.py", "RectanglePairs"),
    ("s5_rectangle.py", "RectangleMobius"),
    ("s5_rectangle.py", "RectangleEnd"),
    ("s0_intro_outro.py", "Outro"),
]
CHAPTER_NAMES = {"Monk": "第一题 · 僧人登山", "Antipodal": "第二题 · 对跖点的温度",
                 "Utilities": "第三题 · 三座房子与三种管线", "Buffon": "第四题 · 布丰投针",
                 "Rectangle2D": "第五题 · 内接矩形", "Outro": "回顾与总结"}


def video_path(f, cls, preview):
    q = "480p15" if preview else "1080p30"
    return os.path.join(ROOT, "media", "videos", os.path.splitext(f)[0], q, f"{cls}.mp4")


def probe_dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", path])
    return float(out)


# ------------------------------------------------------------------ 渲染
def render_one(job, preview):
    f, cls = job
    args = [MANIM, "-ql", f, cls] if preview else [MANIM, "-r", "1920,1080", "--fps", "30", f, cls]
    os.makedirs(os.path.join(BUILD, "logs"), exist_ok=True)
    for attempt in range(3):
        with open(os.path.join(BUILD, "logs", f"render_{cls}.log"), "w") as lg:
            r = subprocess.run(args, cwd=ROOT, stdout=lg, stderr=subprocess.STDOUT)
        if r.returncode == 0:
            print(f"  ✓ {cls}", flush=True)
            return True
        print(f"  ✗ {cls} (attempt {attempt + 1})", flush=True)
    return False


def render(preview, only=None, workers=4):
    jobs = [j for j in ORDER if not only or j[1] in only]
    # 3D 镜头最慢，先开始
    heavy = {"RectangleMobius", "RectangleLift", "UtilitiesTorus", "AntipodalBU"}
    jobs.sort(key=lambda j: j[1] not in heavy)
    with ThreadPoolExecutor(workers) as ex:
        ok = list(ex.map(lambda j: render_one(j, preview), jobs))
    if not all(ok):
        sys.exit("render failed")


# ------------------------------------------------------------------ 背景
def make_background(path, w=1920, h=1080):
    rng = np.random.default_rng(11)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    r = np.sqrt(((x - cx) / w) ** 2 + ((y - cy) / h) ** 2)
    base = np.clip(1 - r * 1.35, 0, 1) ** 1.6
    img = np.zeros((h, w, 3), np.float32)
    center = np.array([16, 20, 48], np.float32)
    edge = np.array([2, 3, 8], np.float32)
    img += edge + (center - edge) * base[..., None]

    def blob(px, py, rad, col, k):
        d = ((x - px) ** 2 + (y - py) ** 2) / rad ** 2
        return np.exp(-d)[..., None] * np.array(col, np.float32) * k

    img += blob(w * 0.18, h * 0.2, 520, [60, 20, 90], 0.22)
    img += blob(w * 0.85, h * 0.82, 560, [10, 60, 80], 0.2)
    img += blob(w * 0.75, h * 0.15, 380, [20, 30, 90], 0.14)
    # 细网格
    grid = ((x % 96) < 1) | ((y % 96) < 1)
    img += grid[..., None] * np.array([5, 7, 14], np.float32) * base[..., None]
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # 星点
    stars = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(stars)
    for _ in range(420):
        sx, sy = rng.uniform(0, w), rng.uniform(0, h)
        rr = rng.choice([0.6, 0.9, 1.3], p=[0.6, 0.3, 0.1])
        dr.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=int(rng.uniform(40, 120)))
    stars = stars.filter(ImageFilter.GaussianBlur(0.6))
    arr = np.asarray(pil).astype(np.float32) + np.asarray(stars, np.float32)[..., None] * np.array([0.8, 0.85, 1.0])
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ 音频
def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def write_wav(path, x, sr=SR):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = x[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def synth_music(total, rng):
    """氛围铺底：Dm–B♭–F–C 循环的柔和和弦垫 + 低音 + 稀疏的铃音琶音，带混响。"""
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    chords = [[50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67]]
    bar = 8.0
    k = 0
    start = 0.0
    while start < total:
        ch = chords[k % 4]
        a = int(max(0, start - 1.5) * SR)
        b = min(n, int((start + bar + 2.0) * SR))
        tt = np.arange(b - a) / SR
        L = (b - a) / SR
        env = np.minimum(1, tt / 2.2) * np.minimum(1, (L - tt) / 2.2)
        env = np.clip(env, 0, 1) ** 1.5
        for j, m in enumerate(ch):
            f = midi_hz(m)
            for det, pan in [(-0.08, 0.3), (0.08, 0.7)]:
                ph = rng.uniform(0, 2 * np.pi)
                w = (np.sin(2 * np.pi * f * (1 + det / 100) * tt + ph)
                     + 0.25 * np.sin(4 * np.pi * f * tt + ph * 1.3)
                     + 0.08 * np.sin(6 * np.pi * f * tt + ph * 0.7))
                amp = 0.05 if j else 0.06
                out[a:b, 0] += (amp * (1 - pan) * env * w).astype(np.float32)
                out[a:b, 1] += (amp * pan * env * w).astype(np.float32)
        sub = 0.07 * np.sin(2 * np.pi * midi_hz(ch[0] - 12) * tt) * env
        out[a:b] += sub[:, None].astype(np.float32)
        # 铃音
        for q in range(4):
            if rng.random() < 0.7:
                ts = start + q * 2.0 + rng.uniform(0, 0.4)
                s0 = int(ts * SR)
                ln = int(2.5 * SR)
                if s0 + ln >= n:
                    continue
                tb = np.arange(ln) / SR
                note = rng.choice(ch[2:]) + 12
                bell = (np.sin(2 * np.pi * midi_hz(note) * tb) + 0.3 * np.sin(2 * np.pi * midi_hz(note) * 2.76 * tb))
                bell *= np.exp(-tb * 2.2) * np.minimum(1, tb / 0.01) * 0.018
                pan = rng.uniform(0.2, 0.8)
                out[s0:s0 + ln, 0] += (bell * (1 - pan)).astype(np.float32)
                out[s0:s0 + ln, 1] += (bell * pan).astype(np.float32)
        start += bar
        k += 1
    # 低通 + 混响
    sos = butter(2, 3200, "low", fs=SR, output="sos")
    out = sosfilt(sos, out, axis=0).astype(np.float32)
    ir_len = int(2.4 * SR)
    ti = np.arange(ir_len) / SR
    irL = (rng.standard_normal(ir_len) * np.exp(-ti * 2.6)).astype(np.float32)
    irR = (rng.standard_normal(ir_len) * np.exp(-ti * 2.6)).astype(np.float32)
    irL /= np.sqrt((irL ** 2).sum())
    irR /= np.sqrt((irR ** 2).sum())
    wetL = oaconvolve(out[:, 0], irL)[:n]
    wetR = oaconvolve(out[:, 1], irR)[:n]
    out = 0.65 * out + 0.35 * np.stack([wetL, wetR], 1).astype(np.float32) * 3
    return out


def whoosh(rng, dur=1.1):
    n = int(dur * SR)
    tb = np.arange(n) / SR
    noise = rng.standard_normal((n, 2)).astype(np.float32)
    out = np.zeros_like(noise)
    # 扫频带通：分块滤波
    blocks = 24
    for i in range(blocks):
        a, b = i * n // blocks, (i + 1) * n // blocks
        fc = 300 * (12 ** (i / blocks))
        sos = butter(2, [fc * 0.7, min(fc * 1.4, 20000)], "band", fs=SR, output="sos")
        out[a:b] = sosfilt(sos, noise[a:b], axis=0)
    env = np.sin(np.pi * np.clip(tb / dur, 0, 1)) ** 2
    out *= env[:, None] * 0.22
    boom_t = np.arange(int(1.2 * SR)) / SR
    f = 70 * np.exp(-boom_t * 1.5) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-boom_t * 3.2) * 0.32
    res = np.zeros((n + len(boom), 2), np.float32)
    res[:n] += out
    off = int(dur * 0.75 * SR)
    res[off:off + len(boom)] += boom[:, None]
    return res


def build_audio(segs_abs, chapter_times, total, path):
    rng = np.random.default_rng(5)
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for t0, wav in segs_abs:
        x, sr = read_wav(wav)
        x = resample_poly(x, SR // sr, 1).astype(np.float32) if sr != SR else x
        a = int(round(t0 * SR))
        voice[a:a + len(x)] += x[: max(0, n - a)]
    # 轻微压缩：抑制峰值
    pk = np.max(np.abs(voice)) + 1e-9
    voice = voice / pk * 0.89
    music = synth_music(total + 1, rng)[:n]
    # 闪避：有人声时压低音乐
    env = uniform_filter1d(np.abs(voice), int(0.25 * SR))
    env = np.clip(env / (env.max() * 0.35 + 1e-9), 0, 1)
    env = uniform_filter1d(env, int(0.6 * SR))
    gain = 0.42 * (1 - 0.5 * env)
    fade = np.minimum(1, np.arange(n) / (3 * SR)) * np.minimum(1, (n - np.arange(n)) / (4 * SR))
    mix = np.zeros((n, 2), np.float32)
    mix += voice[:, None]
    mix += music * (gain * fade)[:, None]
    for tc in chapter_times:
        w = whoosh(rng)
        a = int(max(0, tc - 0.55) * SR)
        b = min(n, a + len(w))
        mix[a:b] += w[: b - a]
    mix *= 0.95 / (np.max(np.abs(mix)) + 1e-9)
    write_wav(path, mix)


# ------------------------------------------------------------------ 字幕
def split_sub(text, maxlen=22):
    """先按句号/分号等强停顿分句，再在逗号处把短从句合并成不超过 maxlen 字的字幕行。"""
    out = []
    for sent in re.findall(r"[^。；！？：]+[。；！？：]?", text):
        parts = re.findall(r"[^，、]+[，、]?", sent)
        cur = ""
        for p in parts:
            if cur and len(cur) + len(p) > maxlen:
                out.append(cur)
                cur = p
            else:
                cur += p
        if cur:
            out.append(cur)
    res = []
    for c in out:
        while len(c) > maxlen + 6:   # 极长的从句再硬切
            res.append(c[:maxlen])
            c = c[maxlen:]
        res.append(c)
    # 过短的尾巴并回上一行
    merged = []
    for c in res:
        if merged and len(clean_sub(c)) <= 3 and len(merged[-1]) + len(c) <= maxlen + 6:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


def clean_sub(c):
    return re.sub(r"[，。；：、]+$", "", c).strip()


def ass_time(t):
    t = max(0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build_subs(events, ass_path, srt_path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK SC,46,&H00F5F2F2,&H000000FF,&H00200A05,&H8C000000,0,0,0,0,100,100,1,0,1,3,1.2,2,80,80,34,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, srt = [], []
    for i, (a, b, txt) in enumerate(events):
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,{txt}")
        srt.append(f"{i + 1}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt))


# ------------------------------------------------------------------ 汇总
def assemble(preview):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    timing = json.load(open(os.path.join(ROOT, "audio", "timing.json")))
    offset = 0.0
    segs_abs, events, chapters, concat_lines, chapter_marks = [], [], [], [], []
    for f, cls in ORDER:
        vp = video_path(f, cls, preview)
        d = probe_dur(vp)
        log = json.load(open(os.path.join(ROOT, "logs", f"{cls}.json")))
        sc = log["script_scene"]
        if cls in CHAPTER_NAMES:
            chapter_marks.append((offset, CHAPTER_NAMES[cls]))
        for sg in log["segs"]:
            t0 = offset + sg["start"]
            segs_abs.append((t0, os.path.join(ROOT, "audio", "seg", f"{sc}_{sg['key']}.wav")))
            if sg["key"] == "title":
                chapters.append(t0)
            for snt in timing[sc][sg["key"]]["sents"]:
                a, b = t0 + snt["start"], t0 + snt["end"]
                chunks = split_sub(snt["sub"])
                tot = sum(len(c) for c in chunks)
                acc = a
                for c in chunks:
                    dd = (b - a) * len(c) / tot
                    events.append((acc, acc + dd + (0.15 if c is chunks[-1] else 0.0), clean_sub(c)))
                    acc += dd
        concat_lines.append(f"file '{vp}'")
        print(f"{cls:16s} offset {offset:7.2f}  dur {d:6.2f}  log {log['length']:6.2f}")
        offset += d
    total = offset
    print(f"TOTAL {total:.1f}s = {total / 60:.1f} min")
    tag = "preview" if preview else "final"
    concat_txt = os.path.join(BUILD, f"concat_{tag}.txt")
    with open(concat_txt, "w") as fh:
        fh.write("\n".join(concat_lines) + "\n")
    raw = os.path.join(BUILD, f"raw_{tag}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", raw],
                   check=True)
    audio = os.path.join(BUILD, f"mix_{tag}.wav")
    build_audio(segs_abs, chapters, total, audio)
    ass = os.path.join(BUILD, f"subs_{tag}.ass")
    srt = os.path.join(OUT, "字幕.srt")
    build_subs(events, ass, srt)
    bg = os.path.join(BUILD, "bg.png")
    w, h = (854, 480) if preview else (1920, 1080)
    make_background(bg, 1920, 1080)
    final = os.path.join(OUT, "preview.mp4" if preview else "几何与拓扑五道经典难题.mp4")
    meta = os.path.join(BUILD, f"chapters_{tag}.txt")
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\ntitle=第一次做多半做不出来：几何与拓扑中的五道经典难题\n")
        marks = chapter_marks + [(total, None)]
        first = [(0.0, "开场")] if chapter_marks[0][0] > 0 else []
        marks = first + marks
        for (a, name), (b, _) in zip(marks[:-1], marks[1:]):
            fh.write(f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(a * 1000)}\nEND={int(b * 1000)}\ntitle={name}\n")
    vf = (f"[1:v]scale={w}:{h},format=gbrp[bg];[0:v]scale={w}:{h},format=gbrp[fg];"
          f"[bg][fg]blend=all_mode=screen,format=yuv420p,subtitles={ass}:original_size=1920x1080[v]")
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", raw, "-loop", "1", "-framerate", "30" if not preview else "15",
           "-i", bg, "-i", audio, "-i", meta, "-filter_complex", vf, "-map", "[v]", "-map", "2:a",
           "-map_metadata", "3", "-map_chapters", "3",
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000",
           "-c:v", "libx264", "-preset", "medium" if not preview else "veryfast", "-crf", "18" if not preview else "26",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final]
    subprocess.run(cmd, check=True)
    print("wrote", final)


if __name__ == "__main__":
    preview = "--preview" in sys.argv
    only = [a for a in sys.argv[2:] if not a.startswith("--")]
    if sys.argv[1] == "render":
        render(preview, only)
    elif sys.argv[1] == "assemble":
        assemble(preview)
