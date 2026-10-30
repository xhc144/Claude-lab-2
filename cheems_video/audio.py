"""声音：配音特效、程序合成的原创配乐和音效、混音。全部现算，不用任何外部音频素材。"""
from __future__ import annotations

import math
import wave

import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(1234)


# ================================================================ 基础
def load_wav(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(1)
    if sr != SR:
        g = math.gcd(sr, SR)
        data = signal.resample_poly(data, SR // g, sr // g).astype(np.float32)
    return data


def save_wav(path, stereo):
    x = np.clip(stereo, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim_silence(x, thr=0.012, pad=0.04):
    a = np.abs(x)
    idx = np.where(a > thr)[0]
    if len(idx) == 0:
        return x
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(x), idx[-1] + int(pad * SR * 2))
    return x[s:e]


def sos(kind, f, order=4):
    if kind == "bp":
        return signal.butter(order, [f[0] / (SR / 2), f[1] / (SR / 2)], btype="band", output="sos")
    return signal.butter(order, f / (SR / 2), btype=kind, output="sos")


def filt(x, kind, f, order=4):
    return signal.sosfilt(sos(kind, f, order), x).astype(np.float32)


def t_arr(dur):
    return np.arange(int(dur * SR), dtype=np.float32) / SR


def env_ad(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    return e.astype(np.float32)


def adsr(n, a=0.02, d=0.1, s=0.8, r=0.2):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((dur - t) / r, 0, 1)
    return (e * rel).astype(np.float32)


_IR = {}


def reverb(x, size=1.6, wet=0.3, bright=6000, seed=0):
    key = (size, bright, seed)
    if key not in _IR:
        n = int(size * SR)
        rng = np.random.default_rng(seed + 99)
        ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / (SR * size / 6.0)).astype(np.float32)
        ir = filt(ir, "low", bright, 2)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        _IR[key] = ir
    y = signal.fftconvolve(x, _IR[key])[: len(x) + len(_IR[key])].astype(np.float32)
    out = np.zeros(len(y), np.float32)
    out[: len(x)] += x * (1 - wet)
    out += y * wet * 1.2
    return out


def echo(x, delay=0.25, fb=0.4, n=4):
    d = int(delay * SR)
    out = np.zeros(len(x) + d * n, np.float32)
    out[: len(x)] += x
    g = 1.0
    for k in range(1, n + 1):
        g *= fb
        out[k * d: k * d + len(x)] += x * g
    return out


def pitch(x, ratio):
    """变调（同时变速）：ratio>1 升调。"""
    n = int(len(x) / ratio)
    return signal.resample(x, n).astype(np.float32)


def tempo(x, r):
    """不变调变速（ffmpeg atempo）。"""
    if abs(r - 1.0) < 1e-3:
        return x
    import subprocess
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-filter:a", f"atempo={r}", "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def norm_rms(x, target=0.1):
    r = np.sqrt(np.mean(x ** 2) + 1e-12)
    return x * (target / r)


# ================================================================ 配音特效
def voice_fx(x, fx):
    x = trim_silence(x)
    x = norm_rms(x, 0.11)
    if not fx:
        return x
    if fx == "mimic":
        t = np.arange(len(x)) / SR
        rm = 1.0 - 0.32 + 0.32 * np.sin(2 * np.pi * 47 * t)
        y = filt(x * rm.astype(np.float32), "bp", (260, 4800), 2)
        y = echo(y, 0.07, 0.25, 2)
        y = reverb(y, 1.2, 0.22, 5000, 1)
        return norm_rms(y, 0.10)
    if fx == "vent":
        y = filt(x, "bp", (380, 3200), 2)
        out = np.copy(y)
        for d, g in ((0.011, 0.45), (0.017, 0.35), (0.029, 0.25)):
            k = int(d * SR)
            out[k:] += y[:-k] * g
        out = reverb(out, 0.6, 0.25, 4000, 2)
        return norm_rms(out, 0.075)
    if fx == "wall":
        y = filt(x, "low", 900, 4)
        y = reverb(y, 0.5, 0.2, 2000, 3)
        return norm_rms(y, 0.07)
    if fx == "whisper":
        y = filt(x, "bp", (300, 4200), 2)
        n = RNG.standard_normal(len(y)).astype(np.float32)
        envl = np.abs(signal.hilbert(y)).astype(np.float32)
        envl = filt(envl, "low", 40, 2)
        n = filt(n, "bp", (1500, 7000), 2) * envl * 0.6
        y = y * 0.75 + n
        y = reverb(y, 1.4, 0.32, 5000, 4)
        return norm_rms(y, 0.085)
    if fx == "flashback":
        y = filt(x, "bp", (300, 3000), 2)
        y = echo(y, 0.22, 0.42, 4)
        y = reverb(y, 1.5, 0.3, 3000, 5)
        return norm_rms(y, 0.08)
    if fx == "devil":
        y = pitch(x, 0.80)
        y = np.tanh(y * 3.0) * 0.4
        y = reverb(y, 0.6, 0.15, 4000, 6)
        return norm_rms(y, 0.1)
    if fx == "angel":
        y = pitch(x, 1.22)
        y = reverb(y, 1.8, 0.3, 9000, 7)
        return norm_rms(y, 0.1)
    if fx == "ethereal":
        y = x + 0.5 * np.concatenate([np.zeros(int(0.018 * SR), np.float32), x])[: len(x)]
        y = reverb(y, 2.8, 0.42, 7000, 8)
        return norm_rms(y, 0.09)
    if fx == "howl":
        y = echo(x, 0.28, 0.45, 4)
        y = reverb(y, 2.5, 0.35, 6000, 10)
        return norm_rms(y, 0.13)
    if fx == "far":
        y = filt(x, "low", 1600, 2)
        y = reverb(y, 1.2, 0.35, 3000, 9)
        return norm_rms(y, 0.06)
    return x


def mouth_env(x, fps=30):
    """嘴型：每帧的音量包络（0~1）。"""
    hop = SR // fps
    n = len(x) // hop + 1
    pad = np.zeros(n * hop, np.float32)
    pad[: len(x)] = x
    r = np.sqrt((pad.reshape(n, hop) ** 2).mean(1))
    if r.max() > 0:
        r = r / (np.percentile(r, 95) + 1e-6)
    r = np.clip((r - 0.12) / 0.75, 0, 1)
    out = np.copy(r)
    for i in range(1, len(r)):
        out[i] = max(r[i], out[i - 1] * 0.55)
    return out.astype(np.float32)


# ================================================================ 乐器
def note_hz(n):
    """'A4' / 'C#5' → Hz；也接受 MIDI 数字。"""
    if isinstance(n, (int, float)):
        return 440.0 * 2 ** ((n - 69) / 12)
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    k = names[n[0]]
    i = 1
    if n[i] == "#":
        k += 1
        i += 1
    elif n[i] == "b":
        k -= 1
        i += 1
    octv = int(n[i:])
    return 440.0 * 2 ** ((k + 12 * (octv + 1) - 69) / 12)


def musicbox(f, dur=1.6, amp=0.3):
    t = t_arr(dur)
    y = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 3)
         + 0.12 * np.sin(2 * np.pi * f * 4.17 * t) * np.exp(-t * 8))
    return (y * env_ad(len(t), 0.002, 0.55) * amp).astype(np.float32)


def piano(f, dur=2.5, amp=0.3):
    t = t_arr(dur)
    y = np.zeros_like(t)
    for k, a in enumerate((1.0, 0.5, 0.28, 0.16, 0.08, 0.05), start=1):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 12000:
            break
        y += a * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.2 + k * 0.7))
    return (y * env_ad(len(t), 0.004, 3.0) * amp).astype(np.float32)


def pluck(f, dur=1.2, amp=0.3, damp=0.996):
    n = int(dur * SR)
    p = max(2, int(SR / f))
    buf = RNG.uniform(-1, 1, p).astype(np.float32)
    out = np.zeros(n, np.float32)
    # Karplus-Strong（向量化：每次处理一个周期）
    cur = buf
    i = 0
    while i < n:
        m = min(p, n - i)
        out[i:i + m] = cur[:m]
        nxt = damp * 0.5 * (cur + np.roll(cur, -1))
        cur = nxt
        i += p
    out = filt(out, "low", 5000, 2)
    return (out * amp).astype(np.float32)


def pad(freqs, dur, amp=0.12, bright=1800, detune=0.004, attack=1.5, release=1.5):
    t = t_arr(dur)
    y = np.zeros_like(t)
    for f in freqs:
        for dt in (-detune, 0, detune):
            ff = f * (1 + dt)
            ph = RNG.uniform(0, 2 * np.pi)
            for k in range(1, 7):
                if ff * k > bright * 2.5:
                    break
                y += (1.0 / k) * np.sin(2 * np.pi * ff * k * t + ph * k)
    y = filt(y, "low", bright, 2)
    y *= adsr(len(t), attack, 0.1, 1.0, release)
    return (y / max(len(freqs) * 3, 1) * amp * 3).astype(np.float32)


def bass(f, dur, amp=0.3):
    t = t_arr(dur)
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)
    return (y * adsr(len(t), 0.005, 0.1, 0.7, 0.08) * amp).astype(np.float32)


def kick(amp=0.8):
    t = t_arr(0.4)
    f = 45 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 9) * amp).astype(np.float32)


def snare(amp=0.5):
    t = t_arr(0.25)
    n = filt(RNG.standard_normal(len(t)).astype(np.float32), "bp", (1200, 7000), 2)
    y = n * np.exp(-t * 18) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return (y * amp).astype(np.float32)


def hat(amp=0.15, dur=0.06):
    t = t_arr(dur)
    n = filt(RNG.standard_normal(len(t)).astype(np.float32), "high", 7000, 2)
    return (n * np.exp(-t * 60) * amp).astype(np.float32)


def place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m] * gain


# ================================================================ 配乐（原创，按需要的时长生成）
MOTIF_MINOR = ["A5", "E6", "D6", "C6", "B5", "C6", "A5", None, "G#5", "B5", "E5", None]
MOTIF_MAJOR = ["C5", "G5", "F5", "E5", "D5", "E5", "C5", None, "B4", "D5", "G4", None]


def cue(name, dur):
    n = int(dur * SR) + SR
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)

    def both(x, at, g=1.0, pan=0.0):
        place(L, x, at, g * (1 - max(pan, 0)))
        place(R, x, at, g * (1 + min(pan, 0)))

    if name in ("night", "night2", "cold"):
        root = 38 if name != "night2" else 37  # D2 / C#2
        # 低音铺底：根音 + 五度，缓慢起伏
        t = t_arr(dur + 1)
        dr = (np.sin(2 * np.pi * note_hz(root) * t) * 0.5 + np.sin(2 * np.pi * note_hz(root + 7) * 1.003 * t) * 0.3
              + np.sin(2 * np.pi * note_hz(root - 12) * t) * 0.4)
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / 11.0)
        dr = (dr * lfo * 0.10).astype(np.float32)
        both(dr, 0, 1.0)
        wind = filt(RNG.standard_normal(len(t)).astype(np.float32), "bp", (200, 900), 2)
        wl = (0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3 + 1)) ** 2
        both(wind * wl.astype(np.float32) * 0.05, 0, 1.0, 0.3)
        # 音乐盒旋律，稀疏，大混响
        mb = np.zeros(n, np.float32)
        step = 0.62 if name != "cold" else 0.8
        start = 3.0
        k = 0
        while start + k * step < dur - 2:
            nt = MOTIF_MINOR[k % len(MOTIF_MINOR)]
            phrase = (k // len(MOTIF_MINOR))
            if nt and phrase % 2 == 0:
                f = note_hz(nt) * (0.5 if name == "night2" else 1.0)
                place(mb, musicbox(f, 1.6, 0.16), start + k * step)
            k += 1
            if k % len(MOTIF_MINOR) == 0:
                start += 6.0
        mb = reverb(mb, 3.0, 0.55, 6000, 11)[:n]
        both(mb, 0, 0.9, -0.2)
        if name == "night2":
            # 心跳般的低频脉冲 + 不和谐的高音
            for k2 in range(int(dur / 1.1)):
                both(kick(0.35), k2 * 1.1, 0.8)
                both(kick(0.25), k2 * 1.1 + 0.28, 0.8)
            hi = pad([note_hz(80), note_hz(81)], dur, 0.05, 5000, 0.006, 6, 4)
            both(hi, 0, 1.0)
    elif name == "day":
        bpm = 104
        beat = 60 / bpm
        chords = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
        roots = ["C3", "G2", "A2", "F2"]
        mel = ["E5", "G5", "A5", "G5", "E5", "D5", "C5", "D5", "E5", None, "C5", "D5", "E5", "G5", "E5", None]
        bars = int(dur / (beat * 4)) + 1
        for b in range(bars):
            ch = chords[b % 4]
            t0 = b * beat * 4
            for s in range(8):
                f = note_hz(ch[(s * 2 + (s // 4)) % 3]) * (2 if s % 2 else 1)
                both(pluck(f, 1.0, 0.16), t0 + s * beat / 2, 1.0, 0.25 if s % 2 else -0.25)
            both(bass(note_hz(roots[b % 4]), beat * 1.8, 0.22), t0)
            both(bass(note_hz(roots[b % 4]), beat * 1.8, 0.18), t0 + beat * 2)
            for s in range(4):
                both(hat(0.05), t0 + s * beat + beat / 2, 1.0, 0.4)
            if b >= 2:
                for s in range(4):
                    nt = mel[(b * 4 + s) % len(mel)]
                    if nt:
                        both(musicbox(note_hz(nt), 1.0, 0.09), t0 + s * beat, 1.0, 0.1)
    elif name == "lobby":
        bpm = 84
        beat = 60 / bpm
        seq = ["D3", None, "A2", None, "F3", None, "A2", "C#3"]
        arp = ["D5", "F5", "A5", "F5", "C#5", "E5", "A5", "E5", "D5", "F5", "Bb5", "F5", "C#5", "E5", "G5", "E5"]
        steps = int(dur / (beat / 2)) + 1
        for s in range(steps):
            t0 = s * beat / 2
            nt = seq[s % len(seq)]
            if nt:
                both(pluck(note_hz(nt), 0.6, 0.22, 0.99), t0, 1.0)
            if s % 2 == 0:
                both(musicbox(note_hz(arp[(s // 2) % len(arp)]), 1.2, 0.06), t0, 1.0, 0.3 * math.sin(s))
        both(pad([note_hz("D3"), note_hz("A3"), note_hz("F4")], dur, 0.05, 1200), 0)
    elif name in ("tension", "tension2"):
        bpm = 112 if name == "tension" else 122
        beat = 60 / bpm
        root = 38 if name == "tension" else 40
        pat = [0, 0, 12, 0, 1, 0, 12, 1]
        steps = int(dur / (beat / 2)) + 1
        for s in range(steps):
            f = note_hz(root + pat[s % 8])
            x = bass(f, beat / 2 * 0.9, 0.16)
            x = np.tanh(x * 3) * 0.12
            both(x, s * beat / 2, 1.0)
            if s % 4 == 2:
                both(hat(0.06, 0.03), s * beat / 2, 1.0, 0.3)
        t = t_arr(dur + 1)
        rise = pad([note_hz(root + 24), note_hz(root + 25), note_hz(root + 31)], dur, 0.06, 3000, 0.005, 4, 2)
        both(rise * np.linspace(0.3, 1.0, len(rise)).astype(np.float32), 0)
        for k in range(int(dur / (beat * 8))):
            both(reverb(musicbox(note_hz(root + 36 + [0, 3, 7, 6][k % 4]), 1.4, 0.06), 2.0, 0.5, 6000, 12),
                 k * beat * 8 + beat * 4, 1.0, 0.3)
        if name == "tension2":
            for k in range(int(dur / (beat * 4))):
                both(kick(0.4), k * beat * 4, 1.0)
    elif name == "reveal":
        chords = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["D3", "F3", "A3"], ["E3", "G#3", "B3"]]
        cd = 4.0
        for k in range(int(dur / cd) + 1):
            ch = chords[k % 4]
            both(pad([note_hz(x) for x in ch], cd + 1.5, 0.07, 1600, 0.004, 1.2, 1.5), k * cd)
            for j, x in enumerate(ch * 2):
                both(musicbox(note_hz(x) * 2 * (2 if j >= 3 else 1), 1.4, 0.05), k * cd + j * cd / 6, 1.0,
                     0.3 * math.sin(j))
        both(np.zeros(1, np.float32), 0)
    elif name == "action":
        bpm = 150
        beat = 60 / bpm
        roots = [38, 38, 41, 43]
        bars = int(dur / (beat * 4)) + 1
        for b in range(bars):
            t0 = b * beat * 4
            r = roots[b % 4]
            for s in range(4):
                both(kick(0.55), t0 + s * beat, 1.0)
                if s % 2 == 1:
                    both(snare(0.32), t0 + s * beat, 1.0)
                both(hat(0.07), t0 + s * beat + beat / 2, 1.0, 0.3)
            for s in range(8):
                f = note_hz(r - 12 + (12 if s in (3, 6) else 0))
                x = np.tanh(bass(f, beat / 2 * 0.85, 0.3) * 2.5) * 0.15
                both(x, t0 + s * beat / 2, 1.0)
            if b % 2 == 0:
                st = pad([note_hz(r + 12), note_hz(r + 16), note_hz(r + 19)], beat * 1.2, 0.18, 3500, 0.006, 0.01, 0.3)
                both(st, t0, 1.0)
                both(st, t0 + beat * 1.5, 0.8)
    elif name in ("warm", "ending"):
        bpm = 72 if name == "warm" else 66
        beat = 60 / bpm
        prog = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
        roots = ["C3", "G2", "A2", "F2"]
        bars = int(dur / (beat * 4)) + 1
        for b in range(bars):
            t0 = b * beat * 4
            ch = prog[b % 4]
            for j, x in enumerate(ch):
                both(piano(note_hz(x), 3.0, 0.10), t0 + j * 0.03, 1.0, -0.2 + 0.2 * j)
            both(piano(note_hz(roots[b % 4]), 3.0, 0.12), t0)
            for s in (1, 2, 3):
                both(piano(note_hz(ch[s % 3]) * 2, 1.5, 0.05), t0 + s * beat, 1.0, 0.2)
            both(pad([note_hz(x) for x in ch], beat * 4 + 1, 0.035, 1400, 0.004, 1.0, 1.0), t0)
            if b >= 1:
                for s in range(4):
                    nt = MOTIF_MAJOR[((b - 1) * 4 + s) % len(MOTIF_MAJOR)]
                    if nt:
                        both(musicbox(note_hz(nt) * 2, 1.5, 0.07), t0 + s * beat, 1.0, 0.15)
        L[:] = reverb(L, 2.0, 0.25, 6000, 13)[:n]
        R[:] = reverb(R, 2.0, 0.25, 6000, 14)[:n]
    st = np.stack([L, R], 1)[: int(dur * SR)]
    # 首尾淡入淡出
    f = min(int(1.0 * SR), len(st) // 4)
    if f > 0:
        st[:f] *= np.linspace(0, 1, f)[:, None]
        st[-f:] *= np.linspace(1, 0, f)[:, None]
    return st


# ================================================================ 音效
def sfx(name):
    r = RNG

    def noise(d):
        return r.standard_normal(int(d * SR)).astype(np.float32)

    if name == "drone_hit" or name == "title_hit":
        t = t_arr(4.0)
        y = np.sin(2 * np.pi * 41 * t) * np.exp(-t * 0.9) * 0.8
        y += filt(noise(4.0), "low", 300, 2) * np.exp(-t * 1.5) * 0.5
        if name == "title_hit":
            y += sum(musicbox(note_hz(x), 4.0, 0.12) for x in ("A4", "E5", "Bb5"))
        return reverb(y.astype(np.float32), 3.0, 0.4, 3000, 20)
    if name in ("sting", "sting_soft"):
        t = t_arr(2.5)
        fs = [note_hz(x) for x in ("A5", "Bb5", "E6", "D#6")]
        y = sum(np.sin(2 * np.pi * f * t + r.uniform(0, 6)) for f in fs) / 4
        e = np.minimum(t / 0.03, 1) * np.exp(-t * 1.6)
        y = y * e
        y += np.sin(2 * np.pi * 55 * t) * np.exp(-t * 3) * 0.7
        y += filt(noise(2.5), "high", 3000, 2) * np.exp(-t * 6) * 0.2
        g = 0.9 if name == "sting" else 0.45
        return reverb((y * g).astype(np.float32), 2.0, 0.4, 7000, 21)
    if name == "glitch":
        y = np.concatenate([noise(0.05) * 0.4 * (k % 2) + np.sin(2 * np.pi * (300 + 200 * k) * t_arr(0.05)) * 0.3
                            for k in range(8)]).astype(np.float32)
        return filt(y, "bp", (200, 6000), 2)
    if name == "paper":
        d = 0.7
        y = filt(noise(d), "bp", (1500, 8000), 2)
        am = np.abs(filt(noise(d), "low", 25, 2)) * 6
        return (y * am * env_ad(len(y), 0.05, 0.4) * 0.6).astype(np.float32)
    if name == "sparkle":
        out = np.zeros(int(1.5 * SR), np.float32)
        for k, x in enumerate(("C6", "E6", "G6", "C7", "E7")):
            place(out, musicbox(note_hz(x), 1.0, 0.12), k * 0.06)
        return reverb(out, 1.5, 0.35, 9000, 22)
    if name in ("steps_soft", "steps_heavy", "patter", "run"):
        cnt, gap, f, g = {"steps_soft": (6, 0.42, 600, 0.25), "steps_heavy": (8, 0.5, 250, 0.6),
                          "patter": (10, 0.12, 1200, 0.18), "run": (10, 0.22, 500, 0.4)}[name]
        out = np.zeros(int((cnt * gap + 0.5) * SR), np.float32)
        for k in range(cnt):
            x = filt(noise(0.09), "low", f, 2) * env_ad(int(0.09 * SR), 0.002, 0.03)
            if name == "steps_heavy":
                x += np.sin(2 * np.pi * 70 * t_arr(0.09)) * env_ad(int(0.09 * SR), 0.002, 0.04) * 0.6
            place(out, x * g * r.uniform(0.7, 1.0), k * gap + r.uniform(0, 0.03))
        return reverb(out, 0.8, 0.2, 3000, 23)
    if name == "door_bell" or name == "bell_jingle":
        out = np.zeros(int(2.0 * SR), np.float32)
        notes = ("E6", "C6") if name == "door_bell" else ("A6", "C#7", "A6", "E7")
        for k, x in enumerate(notes):
            place(out, musicbox(note_hz(x), 1.5, 0.25), k * (0.35 if name == "door_bell" else 0.08))
        return reverb(out, 1.2, 0.3, 8000, 24)
    if name == "clock_chime":
        out = np.zeros(int(3.5 * SR), np.float32)
        place(out, piano(note_hz("A3"), 3.0, 0.3) + musicbox(note_hz("A4"), 3.0, 0.15), 0)
        return reverb(out, 2.5, 0.4, 4000, 25)
    if name == "wings":
        d = 1.0
        y = filt(noise(d), "bp", (300, 3000), 2)
        am = (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t_arr(d))) ** 3
        return (y * am * env_ad(len(y), 0.05, 0.4) * 0.35).astype(np.float32)
    if name == "gulp":
        t = t_arr(0.35)
        f = 300 - 200 * t / 0.35
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.01, 0.1)
        return (y * 0.5).astype(np.float32)
    if name in ("door_bang", "thump", "thud", "crash", "boom"):
        d = {"door_bang": 0.6, "thump": 0.5, "thud": 0.7, "crash": 1.6, "boom": 1.5}[name]
        t = t_arr(d)
        y = np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 10)
        y += filt(noise(d), "low", 900, 2) * np.exp(-t * 14) * 0.6
        if name == "crash":
            y += filt(noise(d), "high", 2500, 2) * np.exp(-t * 3.0) * 0.45
            for k in range(6):
                place(y, filt(noise(0.08), "high", 4000, 2) * env_ad(int(0.08 * SR), 0.001, 0.03) * 0.4,
                      0.1 + k * r.uniform(0.05, 0.15))
        g = {"door_bang": 0.6, "thump": 0.5, "thud": 0.8, "crash": 0.9, "boom": 0.9}[name]
        return reverb((y * g).astype(np.float32), 1.0, 0.25, 3000, 26)
    if name == "lights_off":
        y = np.zeros(int(1.0 * SR), np.float32)
        place(y, filt(noise(0.03), "high", 2000, 2) * 0.5, 0)
        t = t_arr(0.8)
        hum = np.sin(2 * np.pi * 100 * t) * np.exp(-t * 4) * 0.15
        place(y, hum.astype(np.float32), 0.0)
        return y
    if name == "blanket":
        d = 1.0
        y = filt(noise(d), "bp", (200, 2500), 2)
        return (y * env_ad(len(y), 0.15, 0.4) * 0.3).astype(np.float32)
    if name == "teeth":
        out = np.zeros(int(1.2 * SR), np.float32)
        for k in range(14):
            place(out, filt(noise(0.015), "high", 3000, 2) * 0.35, k * 0.075)
        return out
    if name == "flashlight" or name == "click":
        out = np.zeros(int(0.3 * SR), np.float32)
        place(out, filt(noise(0.012), "high", 2500, 2) * 0.6, 0)
        place(out, filt(noise(0.01), "high", 3500, 2) * 0.4, 0.06)
        return out
    if name == "whir":
        t = t_arr(1.6)
        f = 180 + 30 * np.sin(2 * np.pi * 3 * t)
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        y = filt(y, "bp", (300, 3000), 2) * adsr(len(t), 0.2, 0.1, 1, 0.4) * 0.15
        return y
    if name == "heartbeat":
        out = np.zeros(int(4.5 * SR), np.float32)
        for k in range(5):
            place(out, kick(0.5), k * 0.85)
            place(out, kick(0.35), k * 0.85 + 0.24)
        return filt(out, "low", 200, 2)
    if name in ("hiss", "scratch_fast"):
        d = 0.9 if name == "hiss" else 0.7
        y = filt(noise(d), "high", 3000 if name == "hiss" else 1500, 2)
        if name == "scratch_fast":
            y *= (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t_arr(d)))).astype(np.float32)
        return (y * env_ad(len(y), 0.05, 0.35) * 0.35).astype(np.float32)
    if name == "cart":
        d = 2.4
        t = t_arr(d)
        y = filt(noise(d), "low", 400, 2) * 0.15
        sq = np.sin(2 * np.pi * (1800 + 200 * np.sin(2 * np.pi * 1.5 * t)) * t) * \
            (np.sin(2 * np.pi * 1.5 * t) > 0.85) * 0.05
        return ((y + sq) * adsr(len(t), 0.3, 0.1, 1, 0.5)).astype(np.float32)
    if name == "bowl_slide":
        d = 0.7
        y = filt(noise(d), "bp", (500, 3000), 2) * env_ad(int(d * SR), 0.05, 0.3) * 0.25
        y[int(0.55 * SR):int(0.6 * SR)] += np.sin(2 * np.pi * 1800 * t_arr(0.05)) * 0.2
        return y.astype(np.float32)
    if name in ("crunch_small", "crunch"):
        cnt = 6 if name == "crunch_small" else 12
        out = np.zeros(int(2.0 * SR), np.float32)
        for k in range(cnt):
            x = filt(noise(0.05), "bp", (800, 5000), 2) * env_ad(int(0.05 * SR), 0.001, 0.02)
            place(out, x * (0.3 if name == "crunch_small" else 0.5), k * 0.13 + r.uniform(0, 0.05))
        return filt(out, "low", 2500, 2) if name == "crunch" else out
    if name == "sniff":
        out = np.zeros(int(1.2 * SR), np.float32)
        for k in range(3):
            x = filt(noise(0.14), "bp", (1500, 6000), 2) * env_ad(int(0.14 * SR), 0.04, 0.05) * 0.4
            place(out, x, k * 0.22)
        return out
    if name == "poof":
        d = 0.5
        y = filt(noise(d), "low", 1500, 2) * env_ad(int(d * SR), 0.01, 0.15) * 0.5
        return reverb(y.astype(np.float32), 0.8, 0.3, 4000, 27)
    if name == "stomach":
        t = t_arr(1.6)
        f = 70 + 25 * np.sin(2 * np.pi * 2.3 * t) + 15 * np.sin(2 * np.pi * 7 * t)
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        y = filt(y, "low", 400, 2) * adsr(len(t), 0.1, 0.1, 1, 0.5)
        y *= (0.6 + 0.4 * np.sin(2 * np.pi * 5 * t)).astype(np.float32)
        return (y * 0.5).astype(np.float32)
    if name == "drag":
        d = 2.2
        y = filt(noise(d), "bp", (150, 900), 2)
        am = 0.5 + 0.5 * np.sin(2 * np.pi * 1.2 * t_arr(d))
        return (y * am * adsr(int(d * SR), 0.4, 0.1, 1, 0.6) * 0.3).astype(np.float32)
    if name == "flap":
        out = np.zeros(int(0.8 * SR), np.float32)
        for k in range(3):
            x = filt(noise(0.04), "low", 1200, 2) * env_ad(int(0.04 * SR), 0.001, 0.02) * (0.5 - k * 0.12)
            place(out, x, k * 0.16)
        return out
    if name == "scratch":
        d = 2.5
        y = filt(noise(d), "bp", (1500, 6000), 2)
        am = (np.sin(2 * np.pi * 5 * t_arr(d)) > 0.2).astype(np.float32)
        return (y * am * adsr(int(d * SR), 0.1, 0.1, 1, 0.3) * 0.22).astype(np.float32)
    if name == "snore":
        d = 4.0
        t = t_arr(d)
        y = filt(noise(d), "low", 350, 2) * (np.sin(2 * np.pi * 0.45 * t) > 0.2) * 0.4
        return filt(y.astype(np.float32), "low", 600, 2) * 0.6
    if name == "pop":
        t = t_arr(0.2)
        f = 300 + 900 * t / 0.2
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.06)
        return (y * 0.5).astype(np.float32)
    if name in ("door_creak", "creak"):
        d = 1.4
        t = t_arr(d)
        f = 140 + 60 * np.sin(2 * np.pi * 0.7 * t)
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        y = filt(y, "bp", (400, 2500), 2) * adsr(len(t), 0.1, 0.1, 1, 0.3)
        y *= (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t)).astype(np.float32)
        return (y * 0.18).astype(np.float32)
    if name == "whoosh":
        d = 0.6
        y = filt(noise(d), "bp", (400, 3000), 2) * adsr(int(d * SR), 0.25, 0.05, 1, 0.3) * 0.35
        return y.astype(np.float32)
    if name == "card":
        out = sfx("whoosh") * 0.6
        return out
    if name == "glass":
        d = 2.2
        t = t_arr(d)
        y = filt(noise(d), "high", 3000, 2) * np.exp(-t * 2.5) * 0.5
        for k in range(18):
            place(y, (np.sin(2 * np.pi * r.uniform(3000, 8000) * t_arr(0.12)) * env_ad(int(0.12 * SR), 0.001, 0.04)
                      * 0.12).astype(np.float32), r.uniform(0.05, 1.4))
        y += np.sin(2 * np.pi * 60 * t) * np.exp(-t * 8) * 0.6
        return reverb(y.astype(np.float32), 1.2, 0.3, 8000, 28)
    if name == "howl_boom":
        t = t_arr(3.0)
        y = np.sin(2 * np.pi * 38 * t) * np.exp(-t * 1.2) * 0.8
        return reverb(y.astype(np.float32), 2.5, 0.35, 2000, 29)
    if name == "bark_chorus":
        out = np.zeros(int(3.0 * SR), np.float32)
        for k in range(26):
            f0 = r.uniform(280, 700)
            dd = r.uniform(0.09, 0.16)
            tt = t_arr(dd)
            f = f0 * (1.25 - 0.45 * tt / dd)
            b = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
            b = filt(b, "bp", (f0, f0 * 6), 2) * env_ad(len(tt), 0.006, dd * 0.4)
            b = np.tanh(b * 3) * 0.25
            place(out, b * r.uniform(0.3, 1.0), r.uniform(0, 2.7))
        out = reverb(out, 1.6, 0.45, 4000, 30)
        return out
    if name == "tear":
        d = 0.5
        y = filt(noise(d), "bp", (800, 5000), 2) * adsr(int(d * SR), 0.02, 0.1, 0.8, 0.1) * 0.4
        return y.astype(np.float32)
    if name == "squeak":
        t = t_arr(0.35)
        f = 900 + 600 * np.sin(np.pi * t / 0.35)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.01, 0.2) * 0.35
        return y.astype(np.float32)
    if name == "slip":
        t = t_arr(0.6)
        f = 1200 - 900 * t / 0.6
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.01, 0.3) * 0.25
        return y.astype(np.float32)
    if name == "metal_bend":
        d = 1.4
        t = t_arr(d)
        f = 300 - 120 * t / d
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        y += signal.sawtooth(2 * np.pi * np.cumsum(f * 1.41) / SR).astype(np.float32)
        y = filt(y, "bp", (300, 3000), 2) * adsr(len(t), 0.05, 0.1, 0.8, 0.5) * 0.15
        return reverb(y, 1.2, 0.3, 4000, 31)
    if name == "siren":
        d = 6.0
        t = t_arr(d)
        f = 750 + 250 * np.sign(np.sin(2 * np.pi * 0.9 * t))
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR)
        y = y * adsr(len(t), 1.5, 0.1, 1, 1.5) * 0.12
        return reverb(filt(y.astype(np.float32), "low", 3000, 2), 1.5, 0.4, 3000, 32)
    if name == "shimmer":
        out = np.zeros(int(4.0 * SR), np.float32)
        for k, x in enumerate(("C6", "G6", "E6", "C7", "G6", "E7", "C7")):
            place(out, musicbox(note_hz(x), 1.6, 0.08), k * 0.18)
        return reverb(out, 3.0, 0.5, 9000, 33)
    if name == "crayon":
        d = 1.8
        y = filt(noise(d), "bp", (1500, 6000), 2)
        am = (np.sin(2 * np.pi * 6 * t_arr(d)) > -0.2).astype(np.float32)
        return (y * am * 0.12).astype(np.float32)
    return np.zeros(int(0.1 * SR), np.float32)


def ambience(name, dur):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    if name == "room_tone":
        y = filt(RNG.standard_normal(n).astype(np.float32), "low", 300, 2) * 0.012
    elif name == "night_room":
        y = filt(RNG.standard_normal(n).astype(np.float32), "low", 250, 2) * 0.012
        # 钟表滴答
        for k in range(int(dur)):
            place(y, filt(RNG.standard_normal(int(0.01 * SR)).astype(np.float32), "high", 3000, 2) * 0.05, k + 0.0)
    elif name in ("birds", "morning", "dawn"):
        y = filt(RNG.standard_normal(n).astype(np.float32), "low", 500, 2) * 0.01
        cnt = int(dur * (0.6 if name == "birds" else 0.35 if name == "morning" else 0.15))
        for k in range(cnt):
            f0 = RNG.uniform(2500, 4500)
            d = RNG.uniform(0.08, 0.2)
            tt = t_arr(d)
            ch = np.sin(2 * np.pi * np.cumsum(f0 + 900 * np.sin(2 * np.pi * 25 * tt)) / SR) * env_ad(len(tt), 0.01, d / 2)
            place(y, ch.astype(np.float32) * 0.03, RNG.uniform(0, dur))
    else:
        y = np.zeros(n, np.float32)
    return np.stack([y, y], 1)
