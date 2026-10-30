# -*- coding: utf-8 -*-
"""Assemble rendered chapter videos + Qwen voiceover + music bed + subtitles into the final mp4.

usage: python build.py <quality_dir e.g. 1080p30> <out.mp4> [chapter ids...]
"""
import json, os, re, subprocess, sys, wave

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(ROOT, "timing.json")))
SR = 48000
MODULE = {**{i: "scenes_a" for i in range(0, 5)}, **{i: "scenes_b" for i in range(5, 10)},
          **{i: "scenes_c" for i in range(10, 14)}, **{i: "scenes_d" for i in range(14, 18)}}


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                   "default=nw=1:nk=1", path])
    return float(out)


def resample(x, sr_in):
    n = int(len(x) * SR / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


# ------------------------------------------------------------------ music bed
def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # vectorised one-pole via lfilter-like loop in chunks (scipy-free)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x).astype(np.float32)


def music_bed(n):
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]  # Am F C G
    bar = 8.0
    rng = np.random.default_rng(0)
    nb = int(np.ceil(n / SR / bar)) + 1
    for b in range(nb):
        ch = chords[b % 4]
        s0 = int(b * bar * SR)
        L = int((bar + 2.0) * SR)
        if s0 >= n:
            break
        tt = np.arange(L) / SR
        env = np.minimum(1, tt / 2.5) * np.minimum(1, np.maximum(0, (bar + 2.0 - tt) / 2.5))
        sig = np.zeros(L, np.float32)
        for m in ch:
            for det in (-0.07, 0.07):
                f = note(m) * 2 ** (det / 12)
                ph = rng.uniform(0, 2 * np.pi)
                sig += (np.sin(2 * np.pi * f * tt + ph) + 0.3 * np.sin(4 * np.pi * f * tt + ph)) * 0.12
        sig += 0.35 * np.sin(2 * np.pi * note(ch[0] - 24) * tt)          # sub bass
        sig *= env
        e = min(n, s0 + L)
        out[s0:e] += sig[: e - s0]
    # soft arpeggio plucks with delay
    step = 60 / 76 / 2
    arp = np.zeros(n, np.float32)
    k = 0
    while k * step * SR < n:
        b = int(k * step / bar)
        ch = chords[b % 4]
        m = ch[[0, 2, 3, 1, 2, 3, 1, 2][k % 8]] + 12
        s0 = int(k * step * SR)
        L = int(1.2 * SR)
        tt = np.arange(L) / SR
        p = np.sin(2 * np.pi * note(m) * tt) * np.exp(-tt * 5.0) * 0.18
        e = min(n, s0 + L)
        arp[s0:e] += p[: e - s0]
        k += 1
    d = int(0.39 * SR)
    for g in (0.45, 0.2):
        arp[d:] += g * arp[:-d]
    out = lowpass(out, 1400) + lowpass(arp, 3000)
    out /= np.max(np.abs(out)) + 1e-9
    return out


def whoosh(L=1.0):
    n = int(L * SR)
    rng = np.random.default_rng(5)
    x = rng.normal(0, 1, n).astype(np.float32)
    from scipy.signal import lfilter
    tt = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(tt / L, 0, 1)) ** 2
    # sweep a band-ish filter by mixing two lowpasses
    lo = lfilter([0.05], [1, -0.95], x)
    hi = x - lfilter([0.3], [1, -0.7], x)
    mix = (1 - tt / L) * lo * 3 + (tt / L) * hi * 0.4
    return (mix * env * 0.25).astype(np.float32)


def blip(f=1320, L=0.25):
    tt = np.arange(int(L * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 18) * 0.25).astype(np.float32)


# ------------------------------------------------------------------ subtitles
def ass_time(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def chunks(text, maxlen=22):
    parts = [p for p in re.split(r"(?<=[，。；：！？、])", text) if p]
    lines, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > maxlen:
            lines.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        lines.append(cur)
    out = []
    for ln in lines:
        while len(ln) > maxlen + 6:          # very long clause: hard split
            out.append(ln[:maxlen])
            ln = ln[maxlen:]
        out.append(ln)
    return out


def clean(s):
    s = s.strip()
    s = re.sub(r"[，。；：、]+$", "", s)
    return s.replace("，", "  ").replace("。", "  ").replace("；", "  ")


def write_ass(path, events):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK SC,48,&H00FFFFFF,&H000000FF,&H00140A05,&H96000000,0,0,0,0,100,100,1,0,1,3.2,1.2,2,80,80,46,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for a, b, txt in events:
            f.write(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,{txt}\n")


# ------------------------------------------------------------------ main
def main():
    qdir = sys.argv[1]
    out = sys.argv[2]
    ids = [int(x) for x in sys.argv[3:]] or list(range(18))
    work = os.path.join(ROOT, "build_" + qdir)
    os.makedirs(work, exist_ok=True)
    vids, offs, durs = [], [], []
    off = 0.0
    for i in ids:
        v = os.path.join(ROOT, "media", "videos", MODULE[i], qdir, f"Ch{i:02d}.mp4")
        d = probe(v)
        vids.append(v)
        offs.append(off)
        durs.append(d)
        expect = T["chapters"][i]["total"]
        if abs(d - expect) > 0.1:
            print(f"warning ch{i}: video {d:.2f}s vs timeline {expect:.2f}s")
        off += d
    total = off
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)
    events = []
    for i, o in zip(ids, offs):
        ch = T["chapters"][i]
        for k, seg in enumerate(ch["segs"]):
            x = resample(np.load(os.path.join(ROOT, "audio", f"ch{i:02d}_{k:02d}.npy")), T["sr"])
            s = int((o + seg["start"]) * SR)
            voice[s:s + len(x)] += x[: max(0, n - s)]
            # subtitles
            parts = chunks(seg["sub"])
            L = sum(len(p) for p in parts)
            t = o + seg["start"]
            for p in parts:
                dt = seg["dur"] * len(p) / L
                events.append((t, t + dt - 0.02, clean(p)))
                t += dt
        if 1 <= i <= 16:
            w = whoosh(0.9)
            s = int((o + ch["segs"][0]["start"] - 0.35) * SR)
            s = max(s, 0)
            sfx[s:s + len(w)] += w[: n - s]
        if i == 0:
            b = blip(1760, 0.4)
            s = int((o + ch["segs"][3]["start"]) * SR)
            sfx[s:s + len(b)] += b
    # music with ducking under the voice
    bed = music_bed(n)
    from scipy.signal import lfilter
    env = lfilter([0.0008], [1, -0.9992], np.abs(voice))
    env = env / (env.max() + 1e-9)
    duck = 1 - 0.55 * np.clip(env * 6, 0, 1)
    fade = np.minimum(1, np.arange(n) / (3 * SR)) * np.minimum(1, (n - np.arange(n)) / (4 * SR))
    vpk = np.percentile(np.abs(voice[voice != 0]), 99.5)
    voice = voice / vpk * 0.72
    mix = voice + bed * 0.075 * duck * fade + sfx * 0.6
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    wav = os.path.join(work, "mix.wav")
    with wave.open(wav, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    ass = os.path.join(work, "subs.ass")
    write_ass(ass, events)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for v in vids:
            f.write(f"file '{v}'\n")
    cat = os.path.join(work, "concat.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cat])
    crf = "19" if "1080" in qdir else "26"
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", cat, "-i", wav,
                           "-vf", f"ass={ass}", "-c:v", "libx264", "-preset", "medium", "-crf", crf,
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-movflags", "+faststart", "-shortest", out])
    print("wrote", out, f"{total / 60:.2f} min")


if __name__ == "__main__":
    main()
