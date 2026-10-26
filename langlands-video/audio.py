"""音轨：千问 TTS 的旁白 + 程序合成的配乐和音效，混音后输出 48kHz 立体声 wav。

配乐在 D 小调上：开场是钟表滴答和低沉的管风琴，标题处是电影预告片式的「Braam」冲击，
例子部分是 120 BPM 的脉冲贝斯，纲领部分是宏大的和弦铺底，片尾落在 D 大调上。
旁白出现时音乐自动压低（侧链闪避）。
"""

import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

import cues
from cues import Timeline

SR = 48000
RNG = np.random.default_rng(2026)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def n_of(t):
    return int(round(t * SR))


# ---------------------------------------------------------------- 基本音源
def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + phase) % 1.0) - 1


def lowpass(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR / 2 * 0.95), "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def highpass(x, fc, order=2):
    sos = signal.butter(order, fc, "high", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def bandpass(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "band", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def adsr(n, a, r, sustain=1.0):
    e = np.full(n, sustain)
    na, nr = min(n, n_of(a)), min(n, n_of(r))
    if na:
        e[:na] = np.linspace(0, sustain, na) ** 1.5
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def add(buf, x, t, gain=1.0, pan=0.0):
    """把单声道/立体声片段 x 叠加到 buf 的 t 秒处。pan：-1 左，1 右。"""
    i = n_of(t)
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]
        i = 0
    x = x[: len(buf) - i]
    if x.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        buf[i:i + len(x), 0] += x * gain * l * 1.414
        buf[i:i + len(x), 1] += x * gain * r * 1.414
    else:
        buf[i:i + len(x)] += x * gain


def reverb_ir(seconds, decay, seed):
    rng = np.random.default_rng(seed)
    n = n_of(seconds)
    t = np.arange(n) / SR
    env = np.exp(-t * 6.9 / decay)
    ir = rng.normal(0, 1, (n, 2)) * env[:, None]
    ir = lowpass(ir, 6000)
    ir[: n_of(0.012)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(x, seconds=3.0, decay=2.6, wet=0.35, seed=1):
    ir = reverb_ir(seconds, decay, seed)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([signal.oaconvolve(x[:, k], ir[:, k])[: len(x)] for k in range(2)], 1)
    return x * (1 - wet) + y * wet


# ---------------------------------------------------------------- 乐器
def pad(notes, dur, bright=1200, detune=0.12, organ=0.5):
    """和弦铺底：失谐锯齿波 + 管风琴式正弦叠加，左右声道各自失谐，声场宽。"""
    n = n_of(dur)
    out = np.zeros((n, 2))
    for m in notes:
        f = hz(m)
        for ch, d in enumerate((-detune, detune)):
            s = sum(saw(f * 2 ** (dd / 12), n, RNG.random()) for dd in (d, -d * 0.6, d * 0.3)) / 3
            t = np.arange(n) / SR
            org = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.25 * np.sin(6 * np.pi * f * t)
                   + 0.18 * np.sin(8 * np.pi * f * t))
            out[:, ch] += (1 - organ) * s + organ * org * 0.6
    out = lowpass(out, bright, 2)
    out *= adsr(n, min(2.5, dur * 0.3), min(2.5, dur * 0.35))[:, None]
    return out / max(1, len(notes))


def sub_drone(f, dur, lfo=0.08):
    n = n_of(dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * (0.8 + 0.2 * np.sin(2 * np.pi * lfo * t))
    return x * adsr(n, 2.0, 2.0)


def braam(strength=1.0, root=38):
    """电影预告片的「Braam」：低音铜管式的锯齿堆叠 + 下滑的次低音 + 噪声冲击。"""
    dur = 5.5
    n = n_of(dur)
    t = np.arange(n) / SR
    env = np.exp(-t / 1.6) * (1 - np.exp(-t / 0.012))
    out = np.zeros((n, 2))
    for m, g in ((root - 12, 1.0), (root, 0.8), (root + 7, 0.5), (root + 12, 0.35)):
        for ch, d in enumerate((-0.08, 0.09)):
            out[:, ch] += g * saw(hz(m) * 2 ** (d / 12), n, RNG.random())
    # 滤波器从亮到暗：亮、暗两版按包络交叉混合
    bright = lowpass(out, 2400, 2)
    dark = lowpass(out, 300, 2)
    k = np.exp(-t / 0.35)[:, None]
    out = (bright * k + dark * (1 - k)) * env[:, None]
    f = 70 * np.exp(-t / 0.9) + 32
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.8) * (1 - np.exp(-t / 0.005))
    noise = lowpass(RNG.normal(0, 1, (n, 2)), 900) * np.exp(-t / 0.18)[:, None]
    hit = out * 0.5 + sub[:, None] * 0.9 + noise * 0.35
    hit = np.tanh(hit * 1.6) / 1.2
    return reverb(hit, 4.0, 3.4, 0.35, seed=3) * strength


def riser(dur):
    n = n_of(dur)
    t = np.arange(n) / SR
    u = t / dur
    noise = RNG.normal(0, 1, (n, 2))
    noise = bandpass(noise, 400, 9000) * (u ** 2.4)[:, None]
    f = 110 * 2 ** (u * 3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 2
    tone2 = np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * u ** 3
    x = noise * 0.35 + (tone + 0.5 * tone2)[:, None] * 0.25
    fade = np.ones(n)
    fade[-n_of(0.03):] = np.linspace(1, 0, n_of(0.03))
    return x * fade[:, None]


def whoosh(dur=1.2):
    n = n_of(dur)
    t = np.arange(n) / SR
    u = t / dur
    noise = RNG.normal(0, 1, n)
    bands = [bandpass(noise, lo, lo * 2.2) for lo in (250, 600, 1400, 3200)]
    w = [np.exp(-((u - c) / 0.18) ** 2) for c in (0.2, 0.38, 0.55, 0.7)]
    x = sum(b * ww for b, ww in zip(bands, w))
    env = np.sin(np.pi * u) ** 1.5
    pan = np.linspace(-0.8, 0.8, n)
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * env * l, x * env * r], 1) * 1.4


def tick(f=2800, dur=0.03):
    n = n_of(dur)
    t = np.arange(n) / SR
    click = bandpass(RNG.normal(0, 1, n), f * 0.7, min(f * 1.6, 20000)) * np.exp(-t / 0.004)
    return click + 0.4 * np.sin(2 * np.pi * f * 0.5 * t) * np.exp(-t / 0.006)


def blip(f, dur=0.12):
    n = n_of(dur)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.035) * (1 - np.exp(-t / 0.002))


def bell(f, dur=2.5):
    n = n_of(dur)
    t = np.arange(n) / SR
    parts = [(1, 1, 1.4), (2.0, 0.5, 0.9), (2.76, 0.35, 0.6), (5.4, 0.2, 0.3), (8.9, 0.1, 0.15)]
    x = sum(g * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, g, d in parts)
    return x * (1 - np.exp(-t / 0.002))


def kick(dur=0.6, f0=110, f1=42):
    n = n_of(dur)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.05)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * (1 - np.exp(-t / 0.002))


def taiko(dur=1.4):
    n = n_of(dur)
    t = np.arange(n) / SR
    f = 55 + 40 * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    skin = lowpass(RNG.normal(0, 1, n), 1200) * np.exp(-t / 0.04)
    return np.tanh((body + 0.4 * skin) * 1.5)


def hat(dur=0.08):
    n = n_of(dur)
    t = np.arange(n) / SR
    return highpass(RNG.normal(0, 1, n), 7000) * np.exp(-t / 0.018)


def pluck_bass(f, dur=0.24):
    n = n_of(dur)
    t = np.arange(n) / SR
    x = saw(f, n) + 0.5 * saw(f * 1.004, n, 0.3)
    bright = lowpass(x, 1600)
    dark = lowpass(x, 220)
    k = np.exp(-t / 0.05)
    return (bright * k + dark * (1 - k)) * np.exp(-t / 0.18) * (1 - np.exp(-t / 0.003))


def glitch_sfx(dur=0.3):
    n = n_of(dur)
    x = RNG.normal(0, 1, n)
    # 采样保持 + 量化：数码故障的「滋啦」声
    hold = 18
    x = np.repeat(x[::hold], hold)[:n]
    x = np.round(x * 3) / 3
    gate = (RNG.random(n // 600 + 1) > 0.35).repeat(600)[:n]
    t = np.arange(n) / SR
    return bandpass(x * gate, 300, 6000) * np.exp(-t / 0.12) * 0.8


# ---------------------------------------------------------------- 配乐编排
D2, F2, A2, Bb1, C2, G1, A1 = 38, 41, 45, 34, 36, 31, 33

CHORDS = {
    "Dm": [38, 45, 50, 53, 57], "Bb": [34, 46, 50, 53, 58], "F": [41, 48, 53, 57, 60],
    "C": [36, 48, 52, 55, 60], "Gm": [31, 43, 50, 55, 58], "A": [33, 45, 49, 52, 57],
    "D": [38, 45, 50, 54, 57],
}


def chord_seq(buf, t0, t1, names, gain, bright=1100, organ=0.5):
    seg = (t1 - t0) / len(names)
    for k, nm in enumerate(names):
        x = pad(CHORDS[nm], seg + 1.6, bright, organ=organ)
        add(buf, x, t0 + k * seg - 0.3, gain)


def score(tl, n):
    m = np.zeros((n, 2))
    sc = tl.scene
    tr = cues.title_reveal(tl)
    er = cues.end_reveal(tl)

    # 开场：低沉的 D 持续音 + 钟表滴答 + 稀疏的钢琴式音符
    le = sc("letter")
    add(m, sub_drone(hz(26), tr - 0.3), 0.0, 0.35)
    add(m, pad(CHORDS["Dm"], tr + 0.2, 500, organ=0.8), 0.0, 0.32)
    t = 0.5
    k = 0
    while t < tr - 0.2:
        add(m, tick(3200 if k % 2 == 0 else 2400, 0.04), t, 0.16, pan=-0.3 if k % 2 == 0 else 0.3)
        t += 1.0
        k += 1
    for i, (dt, note) in enumerate([(3, 74), (7, 69), (11, 77), (15, 76), (19, 74), (23, 72), (26, 69)]):
        if le["start"] + dt < tr - 3:
            add(m, bell(hz(note), 3.0), le["start"] + dt, 0.07, pan=(-0.4, 0.4)[i % 2])

    # 标题：Braam + 明亮的 D 小调和弦长音
    add(m, pad(CHORDS["Dm"] + [62, 65], sc("title")["end"] - tr + 3, 2600, organ=0.4), tr, 0.38)
    add(m, sub_drone(hz(26), sc("title")["end"] - tr + 2), tr, 0.4)

    # 两片大陆：Bb – F – C – Dm，铃声琶音，两秒一次的轻底鼓
    w = sc("worlds")
    chord_seq(m, w["start"], w["end"], ["Bb", "F", "C", "Dm"], 0.3, 1300)
    arp = [62, 65, 69, 72, 74, 72, 69, 65]
    t = w["start"] + 1.0
    i = 0
    while t < w["end"] - 0.5:
        add(m, bell(hz(arp[i % len(arp)]), 1.6), t, 0.035, pan=0.5 * np.sin(i * 0.9))
        t += 0.375
        i += 1
    t = w["start"] + 0.5
    while t < w["end"] - 1:
        add(m, kick(0.6, 90, 40), t, 0.22)
        t += 2.0

    # 例子：120 BPM 的脉冲贝斯 + 踩镲，和弦 Dm – Bb – C – A
    ex = sc("example")
    roots = [38, 34, 36, 33]
    seq_chords = ["Dm", "Bb", "C", "A"]
    bar = 2.0
    t = ex["start"] + 0.3
    k = 0
    while t < ex["end"] - 0.2:
        root = roots[(k // 2) % 4]
        for s in range(8):
            ts = t + s * bar / 8
            if ts >= ex["end"]:
                break
            add(m, pluck_bass(hz(root + (12 if s in (3, 7) else 0))), ts, 0.16)
            add(m, hat(), ts + bar / 16, 0.05, pan=0.4)
        add(m, kick(0.5, 100, 42), t, 0.26)
        add(m, kick(0.5, 100, 42), t + bar / 2, 0.2)
        t += bar
        k += 1
    nb = int((ex["end"] - ex["start"]) / (2 * bar)) + 1
    for k in range(nb):
        t0 = ex["start"] + 0.3 + k * 2 * bar
        add(m, pad(CHORDS[seq_chords[k % 4]], 2 * bar + 1.2, 900, organ=0.6), t0 - 0.2, 0.18)

    # 费马：先收紧，冲击之后只剩低音——冰山之下
    fe = sc("fermat")
    fs = cues.fermat_schedule(tl)
    add(m, pad(CHORDS["Dm"], fs["qed"] - fe["start"] + 0.5, 900, organ=0.6), fe["start"], 0.25)
    t = fe["start"] + 0.2
    while t < fs["qed"] - 0.1:
        add(m, pluck_bass(hz(38)), t, 0.14)
        t += 0.25 if t < fs["qed"] - 2.0 else 0.125
    add(m, riser(2.0), fs["qed"] - 2.0, 0.35)
    add(m, sub_drone(hz(26), fe["end"] - fs["iceberg"] + 1.0, 0.05), fs["iceberg"] - 0.2, 0.35)
    add(m, pad([26, 38, 45], fe["end"] - fs["iceberg"] + 1.5, 400, organ=0.9), fs["iceberg"] - 0.2, 0.28)

    # 纲领：宏大，Dm – Bb – F – C – Gm – A，半分音符的太鼓
    pr = sc("program")
    chord_seq(m, pr["start"], pr["end"], ["Dm", "Bb", "F", "C", "Gm", "A"], 0.36, 1800, organ=0.45)
    add(m, sub_drone(hz(26), pr["end"] - pr["start"] + 1), pr["start"], 0.3)
    t = pr["start"] + 0.6
    k = 0
    while t < pr["end"] - 0.5:
        add(m, taiko(), t, 0.22 if k % 2 == 0 else 0.14, pan=(-0.2, 0.2)[k % 2])
        t += 1.5
        k += 1

    # 远征：120 BPM 的推进，Dm – Bb – F – C
    hi = sc("history")
    chord_seq(m, hi["start"], hi["end"], ["Dm", "Bb", "F", "C"] * 2, 0.3, 1600)
    t = hi["start"] + 0.2
    k = 0
    while t < hi["end"] - 0.4:
        add(m, kick(0.5, 100, 42), t, 0.24)
        add(m, hat(), t + 0.25, 0.05, pan=0.3)
        if k % 2:
            add(m, highpass(RNG.normal(0, 1, n_of(0.15)), 1500) * np.exp(-np.arange(n_of(0.15)) / SR / 0.05), t, 0.08)
        add(m, pluck_bass(hz(38 if (k // 8) % 4 == 0 else (34, 41, 36)[(k // 8) % 4 - 1])), t, 0.1)
        add(m, pluck_bass(hz(50 if (k // 8) % 4 == 0 else (46, 53, 48)[(k // 8) % 4 - 1])), t + 0.25, 0.06)
        t += 0.5
        k += 1

    # 尾声：退回管风琴和铃声，最后一句前几乎静下来
    fi = sc("finale")
    fsch = cues.finale_schedule(tl)
    chord_seq(m, fi["start"], fsch["decode"], ["Bb", "F", "C", "Dm"], 0.3, 1400, organ=0.7)
    t = fi["start"] + 0.5
    i = 0
    arp2 = [69, 74, 77, 81, 77, 74]
    while t < fsch["decode"] - 0.3:
        add(m, bell(hz(arp2[i % len(arp2)]), 2.0), t, 0.03, pan=0.5 * np.sin(i))
        t += 0.5
        i += 1
    add(m, pad([62, 69, 74], er - fsch["decode"] + 0.5, 3000, organ=0.9), fsch["decode"], 0.12)

    # 片尾：D 大调收束
    end = sc("end")
    add(m, pad(CHORDS["D"] + [62, 66, 69], end["end"] - er + 1, 2200, organ=0.5), er, 0.42)
    add(m, sub_drone(hz(26), end["end"] - er + 1), er, 0.4)
    for i, note in enumerate([74, 78, 81, 86]):
        add(m, bell(hz(note), 4.0), er + 1.0 + i * 0.6, 0.05, pan=(-0.4, 0.4)[i % 2])
    return m


def sfx(tl, n):
    s = np.zeros((n, 2))
    ev = cues.sound_events(tl)
    for t in ev["type"]:
        add(s, tick(4200, 0.025), t, 0.22, pan=0.1)
    for t in ev["glitch"]:
        add(s, glitch_sfx(), t, 0.3)
    for t in ev["glitch_soft"]:
        add(s, glitch_sfx(0.12), t, 0.1)
    for t_end, dur in ev["riser"]:
        add(s, riser(dur), t_end - dur, 0.32)
    for t, k in ev["impact"]:
        add(s, braam(k), t, 0.62)
    for t in ev["whoosh"]:
        add(s, whoosh(), t - 0.45, 0.2)
    for t, f in ev["blip"]:
        add(s, blip(f), t, 0.12, pan=0.2)
    for t in ev["ding"]:
        add(s, bell(hz(86), 1.4), t, 0.07, pan=-0.2)
    for i, t in enumerate(ev["tick"]):
        add(s, tick(5200, 0.015), t, 0.06, pan=((i * 37) % 11 - 5) / 6)
    for t, k in ev["hit"]:
        add(s, taiko(), t, 0.3 * k)
        add(s, kick(0.7, 120, 40), t, 0.35 * k)
    for t in ev["sub_drop"]:
        nn = n_of(3.0)
        tt = np.arange(nn) / SR
        f = 50 * np.exp(-tt / 1.2) + 25
        add(s, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 1.4), t, 0.42)
    return s


# ---------------------------------------------------------------- 旁白
def peaking(x, f0, gain_db, q=1.0):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x)


def compress(x, thresh_db=-20, ratio=3.0):
    env = np.sqrt(signal.lfilter([0.002], [1, -0.998], x * x) + 1e-12)
    level = 20 * np.log10(env + 1e-9)
    over = np.maximum(level - thresh_db, 0)
    gain = 10 ** (-(over - over / ratio) / 20)
    return x * gain


def process_voice(x, sr, quote=False):
    x = signal.resample_poly(x, SR, sr).astype(np.float64)
    x = highpass(x, 75)
    if quote:
        # 念信的声音：带通 + 轻微失真 + 底噪，像一段老录音
        x = bandpass(x, 220, 4200)
        x = np.tanh(x * 2.2) / 2.2 * 1.6
        hiss = highpass(RNG.normal(0, 0.004, len(x)), 3000)
        crackle = (RNG.random(len(x)) > 0.9994) * RNG.normal(0, 0.15, len(x))
        x = x + hiss + lowpass(crackle, 4000)
    else:
        x = peaking(x, 140, 3.5, 0.8)    # 胸腔共鸣
        x = peaking(x, 3500, 2.0, 1.0)   # 清晰度
        x = peaking(x, 7500, -1.5, 1.2)  # 收一点齿音
    x = compress(x, -22, 3.0)
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.1


def voice_track(tl, lines, n):
    v = np.zeros((n, 2))
    for S, sc_lines in zip(tl.scenes, lines):
        for ln, (x, sr) in zip(S["lines"], sc_lines):
            y = process_voice(x, sr, ln["quote"])
            add(v, y, ln["start"], 1.0)
    # 轻微的空间感：短混响
    return reverb(v, 1.6, 1.1, 0.10, seed=9)


def duck_envelope(voice, depth=0.6):
    """旁白在说话时把音乐压低 depth（侧链闪避），起音快、释放慢。"""
    mono = np.abs(voice).mean(1)
    win = n_of(0.05)
    env = np.convolve(mono, np.ones(win) / win, "same")
    env = env / (np.percentile(env[env > 1e-4], 95) + 1e-9)
    env = np.clip(env, 0, 1)
    # 释放：用一阶低通让包络慢慢回落
    rel = np.exp(-1 / (0.45 * SR))
    out = signal.lfilter([1 - rel], [1, -rel], env)
    out = np.maximum(out, env)
    return 1 - depth * np.clip(out * 1.5, 0, 1)


# ---------------------------------------------------------------- 总装
def write_wav(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build(tl_data, lines, out):
    tl = Timeline(tl_data)
    n = n_of(tl.duration + 0.5)
    print("合成配乐与音效 …")
    voice = voice_track(tl, lines, n)
    music = score(tl, n)
    music = reverb(music, 3.5, 3.0, 0.25, seed=5)
    effects = sfx(tl, n)
    duck = duck_envelope(voice, 0.55)[:, None]
    mix = voice * 1.0 + music * 0.75 * duck + effects * (0.6 + 0.4 * duck)
    # 母带：软限幅，再交给 ffmpeg 做响度标准化（-14 LUFS，流媒体常用）
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    fade = np.ones(n)
    fade[-n_of(1.5):] = np.linspace(1, 0, n_of(1.5))
    mix *= fade[:, None]
    raw = Path(out).with_name("audio_raw.wav")
    write_wav(raw, mix * 0.9)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", "loudnorm=I=-14:TP=-1.2:LRA=11", "-ar", str(SR), str(out)], check=True)
    # 同时导出分轨，方便单独检查
    write_wav(Path(out).with_name("stem_voice.wav"), voice / (np.abs(voice).max() + 1e-9) * 0.9)
    write_wav(Path(out).with_name("stem_music.wav"), (music * 0.75 + effects * 0.6) /
              (np.abs(music * 0.75 + effects * 0.6).max() + 1e-9) * 0.9)
    return out
