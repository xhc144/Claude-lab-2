# -*- coding: utf-8 -*-
"""把各场景的画面、配音、背景音乐和字幕合成成片。

    python build.py                      # 用 media/<场景>/videos/*/1080p60/ 下的场景，输出 ../probability-distributions-1080p.mp4
    python build.py 480p15 预览.mp4      # 用低清渲染做预览

配音按 marks/*.json 里记下的实际起点放置（场景渲染时写出），所以画面和声音不会错位。
"""
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = [("scenes_a", "S00"), ("scenes_a", "S01"), ("scenes_b", "S02"), ("scenes_b", "S03"), ("scenes_c", "S04"),
          ("scenes_c", "S05"), ("scenes_d", "S06"), ("scenes_d", "S07"), ("scenes_e", "S08"), ("scenes_e", "S09")]
SR = 48000
BUILD = os.path.join(HERE, "build")


def probe_duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                   path])
    return float(out)


def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:  # 24k → 48k 线性插值
        t_new = np.arange(int(len(x) * SR / sr)) / SR
        x = np.interp(t_new, np.arange(len(x)) / sr, x).astype(np.float32)
    return x


# ---------- 背景音乐：慢速的柔和和弦铺底 ----------
def note(name):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n, octv = name[:-1], int(name[-1])
    semis = names[n[0]] + (1 if "#" in n else 0) - (1 if "b" in n[1:] else 0)
    return 440.0 * 2 ** ((semis - 9) / 12 + (octv - 4))


CHORDS = [
    ["C3", "G3", "E4", "B4", "D5"],    # Cmaj9
    ["A2", "E3", "C4", "G4", "B4"],    # Am9
    ["F2", "C3", "A3", "E4", "G4"],    # Fmaj9
    ["G2", "D3", "B3", "E4", "A4"],    # G6/9
]


def pad_music(total, seconds_per_chord=8.0):
    n = int(total * SR)
    out = np.zeros(n, dtype=np.float32)
    t_chord = np.arange(int((seconds_per_chord + 4) * SR)) / SR
    env = np.minimum(1, t_chord / 2.5) * np.clip((seconds_per_chord + 4 - t_chord) / 3.5, 0, 1)
    env = env ** 1.5
    k = 0
    start = 0.0
    while start < total:
        chord = CHORDS[k % len(CHORDS)]
        tone = np.zeros_like(t_chord)
        for i, nm in enumerate(chord):
            f = note(nm)
            amp = 1.0 / (1 + 0.35 * i)
            for det in (-0.0015, 0.0015):
                ph = np.random.default_rng(k * 10 + i).uniform(0, 2 * np.pi)
                tone += amp * (np.sin(2 * np.pi * f * (1 + det) * t_chord + ph)
                               + 0.18 * np.sin(4 * np.pi * f * (1 + det) * t_chord + ph))
        tone *= env * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t_chord))
        a = int(start * SR)
        b = min(n, a + len(tone))
        out[a:b] += tone[:b - a]
        start += seconds_per_chord
        k += 1
    out /= np.max(np.abs(out)) + 1e-9
    fade = int(3 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-int(5 * SR):] *= np.linspace(1, 0, int(5 * SR))
    return out


def smooth_env(x, win):
    """滑动平均包络（用累加和算，长音频也快）。"""
    c = np.concatenate([[0.0], np.cumsum(np.abs(x), dtype=np.float64)])
    h = win // 2
    idx = np.arange(len(x))
    lo, hi = np.clip(idx - h, 0, len(x)), np.clip(idx + h + 1, 0, len(x))
    return ((c[hi] - c[lo]) / (hi - lo)).astype(np.float32)


# ---------- 字幕 ----------
def split_sub(text, limit=22):
    """按标点把一段解说切成不超过 limit 个字的几行。"""
    parts = re.split(r"(?<=[，。；：！？、])", text)
    out, cur = [], ""
    for p in parts:
        if not p:
            continue
        if cur and len(cur) + len(p) > limit:
            out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    res = []
    for s in out:  # 仍然太长的再硬切
        while len(s) > limit + 6:
            res.append(s[:limit])
            s = s[limit:]
        res.append(s)
    return [s.strip().rstrip("，。；：、") for s in res if s.strip()]


def fmt_srt(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def fmt_ass(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK SC,44,&H00442A1E,&H00442A1E,&H00E6F0F4,&H00000000,0,0,0,0,100,100,1,0,1,3.2,0,2,80,80,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    quality = sys.argv[1] if len(sys.argv) > 1 else "1080p60"
    out_name = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(HERE),
                                                                   "probability-distributions-1080p.mp4")
    root = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "media")
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(HERE, "narration.json"), encoding="utf-8") as f:
        nar = json.load(f)

    # 1. 拼接画面
    lst = os.path.join(BUILD, "concat.txt")
    offsets, t = {}, 0.0
    with open(lst, "w") as f:
        for mod, sid in SCENES:
            p = os.path.join(root, sid, "videos", mod, quality, sid + ".mp4")  # 每个场景单独的 --media_dir
            f.write(f"file '{p}'\n")
            offsets[sid] = t
            t += probe_duration(p)
    total = t
    video = os.path.join(BUILD, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video],
                   check=True)

    # 2. 配音轨 + 字幕
    voice = np.zeros(int((total + 1) * SR), dtype=np.float32)
    srt, ass, n = [], [ASS_HEAD], 1
    for _, sid in SCENES:
        with open(os.path.join(HERE, "marks", sid + ".json")) as f:
            marks = json.load(f)["marks"]
        for i, (m, text) in enumerate(zip(marks, nar[sid])):
            x = read_wav(os.path.join(HERE, "audio", f"{sid}_{i:02d}.wav"))
            a = int((offsets[sid] + m) * SR)
            voice[a:a + len(x)] += x
            start, dur = offsets[sid] + m, len(x) / SR
            lines = split_sub(text)
            weights = np.array([len(s) + 2 for s in lines], dtype=float)
            cuts = start + np.concatenate([[0], np.cumsum(weights) / weights.sum() * dur])
            for s, t0, t1 in zip(lines, cuts[:-1], cuts[1:]):
                srt.append(f"{n}\n{fmt_srt(t0)} --> {fmt_srt(t1 - 0.04)}\n{s}\n")
                ass.append(f"Dialogue: 0,{fmt_ass(t0)},{fmt_ass(t1 - 0.04)},Sub,,0,0,0,,{s}\n")
                n += 1
    voice = voice[:int(total * SR)]
    rms = np.sqrt(np.mean(voice[np.abs(voice) > 0.01] ** 2))
    voice *= 10 ** (-17 / 20) / rms  # 有声部分约 -17 dBFS
    music = pad_music(total)
    duck = 1 - 0.55 * np.clip(smooth_env(voice, int(0.35 * SR)) / 0.05, 0, 1)
    music_level = 10 ** (-33 / 20) / (np.sqrt(np.mean(music ** 2)) + 1e-9)
    mix = voice + music * music_level * duck
    peak = np.max(np.abs(mix))
    if peak > 0.97:
        mix *= 0.97 / peak
    audio = os.path.join(BUILD, "audio.wav")
    with wave.open(audio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    srt_path = os.path.splitext(out_name)[0] + ".srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    ass_path = os.path.join(BUILD, "subs.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("".join(ass))

    # 3. 烧字幕、编码
    crf = os.environ.get("CRF", "24")
    subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-i", video, "-i", audio,
                    "-vf", f"ass={ass_path}", "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-tune", "animation",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-movflags", "+faststart",
                    "-shortest", out_name], check=True)
    mb = os.path.getsize(out_name) / 1e6
    print(f"成片 {out_name}：{total / 60:.1f} 分钟，{mb:.1f} MB；字幕 {srt_path}")


if __name__ == "__main__":
    main()
