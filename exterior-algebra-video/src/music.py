# -*- coding: utf-8 -*-
"""配乐：纯 numpy 合成的合成器浪潮（synthwave）风格，没有任何采样素材。

- 120 BPM，一小节 2 秒；每个场景都从小节线开始（common.py 保证），和弦进行在每个场景开头重新起句。
- 声部：超级锯齿波和弦铺底、八分音符脉冲贝斯、十六分音符琶音（乒乓延迟）、旋律、鼓组（底鼓、拍手、踩镲、吊镲）。
- 强度分 0–4 档：讲推导的段落用低档（铺底 + 琶音 + 轻鼓），开场的公式快闪和尾声用满档。
- 场景里记下的重音（cues）：hit = 一声短促的“闪光”，impact = 低频冲击 + 噪声爆发；章节卡前一小节加上升音。
"""
import numpy as np
from scipy.signal import butter, sosfilt, oaconvolve

from common import BAR, BEAT

SR = 44100


def midi(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


CH = {  # 和弦：(根音, 铺底音)
    "Am": (45, [57, 60, 64, 69]), "F": (41, [53, 57, 60, 65]), "C": (48, [55, 60, 64, 67]),
    "G": (43, [55, 59, 62, 67]), "Dm": (50, [57, 62, 65, 69]), "Em": (40, [55, 59, 64, 67]),
    "E": (40, [56, 59, 64, 68]), "Bb": (46, [53, 58, 62, 65]),
}
PROG = {
    0: ["Am", "F", "C", "G"],
    1: ["Am", "F", "C", "G"],
    2: ["F", "G", "Em", "Am"],
    3: ["Am", "Dm", "F", "E"],
    9: ["F", "G", "Am", "Am"],
}

# 每个场景：(和弦进行, [(场景内起始秒, 强度), ...])
SECTIONS = {
    "Intro": (0, [(0, 0), (4, 1), (12, 0), (14, 2), (22, 4), (38, 0), (42, 2), (50, 1)]),
    "Card1": (0, [(0, 0)]), "Card2": (0, [(0, 0)]), "Card3": (0, [(0, 0)]),
    "Forms": (9, [(0, 2), (40, 3)]),
    "Outro": (9, [(0, 4), (20, 1), (28, 3), (36, 0)]),
}
CHAPTER_OF = {}
for s in ["AreaAlgebra", "Rules", "KVectors", "Basis", "FirstCompute"]:
    CHAPTER_OF[s] = 1
for s in ["VolumeFactor", "Leibniz", "Properties", "Cramer", "Laplace"]:
    CHAPTER_OF[s] = 2
for s in ["Compound", "CauchyBinet", "Pythagoras", "CharPoly", "Sylvester", "PluckerAlg", "PluckerLines"]:
    CHAPTER_OF[s] = 3
LEVEL_OF_CHAPTER = {1: 1, 2: 2, 3: 2}


def section(scene):
    if scene in SECTIONS:
        return SECTIONS[scene]
    ch = CHAPTER_OF.get(scene, 1)
    return ch, [(0, LEVEL_OF_CHAPTER[ch])]


def level_at(levels, t):
    lv = levels[0][1]
    for a, l in levels:
        if t >= a - 1e-6:
            lv = l
    return lv


# ------------------------------------------------------------------ 振荡器
def polyblep(t, dt):
    out = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt
    out[m] = x + x - x * x - 1
    m = t > 1 - dt
    x = (t[m] - 1) / dt
    out[m] = x * x + x + x + 1
    return out


def saw(freq, n, phase0=0.0):
    dt = freq / SR
    ph = (phase0 + dt * np.arange(n)) % 1.0
    return (2 * ph - 1 - polyblep(ph, dt)).astype(np.float32)


def square(freq, n, width=0.5):
    dt = freq / SR
    ph = (dt * np.arange(n)) % 1.0
    s = np.where(ph < width, 1.0, -1.0) + polyblep(ph, dt) - polyblep((ph + 1 - width) % 1.0, dt)
    return s.astype(np.float32)


def lp(x, fc, order=2):
    sos = butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0).astype(np.float32)


def hp(x, fc, order=2):
    sos = butter(order, fc, "high", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0).astype(np.float32)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0).astype(np.float32)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    t = np.arange(n) / SR
    L = n / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((L - t) / max(r, 1e-4), 0, 1)
    return (e * rel).astype(np.float32)


class Mix:
    def __init__(self, total):
        self.n = int((total + 6) * SR)
        self.dry = np.zeros((self.n, 2), np.float32)
        self.verb = np.zeros((self.n, 2), np.float32)
        self.delay = np.zeros((self.n, 2), np.float32)
        self.duck = np.ones(self.n, np.float32)   # 底鼓带来的侧链压缩
        self.rng = np.random.default_rng(42)

    def put(self, t, x, gain=1.0, pan=0.0, verb=0.0, delay=0.0):
        a = int(round(t * SR))
        if a >= self.n or len(x) == 0:
            return
        x = x[: self.n - a]
        if x.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            x = np.stack([x * l, x * r], 1)
        x = x * gain
        self.dry[a:a + len(x)] += x
        if verb:
            self.verb[a:a + len(x)] += x * verb
        if delay:
            self.delay[a:a + len(x)] += x * delay


# ------------------------------------------------------------------ 乐器
def pad_block(notes, dur, bright, rng):
    n = int(dur * SR)
    out = np.zeros((n, 2), np.float32)
    for m in notes:
        f = float(midi(m))
        for k, det in enumerate((-0.12, -0.05, 0.0, 0.05, 0.12)):
            pan = (k - 2) / 2.5
            w = saw(f * 2 ** (det / 12), n, rng.uniform())
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            out[:, 0] += w * l
            out[:, 1] += w * r
    out /= 5 * len(notes)
    out = lp(out, 700 + 3500 * bright)
    e = env_adsr(n, a=0.6, d=1.0, s=0.85, r=0.9)
    return out * e[:, None]


def bass_note(m, dur, bright=0.5):
    n = int(dur * SR)
    f = float(midi(m))
    x = 0.7 * saw(f, n) + 0.3 * square(f / 2, n)
    x = lp(x, 250 + 700 * bright)
    e = env_adsr(n, a=0.004, d=0.12, s=0.6, r=0.05)
    return x * e


def pluck(m, dur=0.28, bright=0.6, width=0.3):
    n = int(dur * SR)
    f = float(midi(m))
    x = 0.6 * square(f, n, width) + 0.4 * saw(f * 1.003, n)
    x = lp(x, 1200 + 5000 * bright)
    t = np.arange(n) / SR
    e = np.minimum(1, t / 0.003) * np.exp(-t / 0.09)
    return (x * e).astype(np.float32)


def lead_note(m, dur, rng):
    n = int(dur * SR)
    f = float(midi(m))
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.3)
    ph = np.cumsum(f * vib) / SR
    x = (2 * (ph % 1.0) - 1) * 0.5 + 0.5 * (2 * ((ph * 1.005) % 1.0) - 1)
    x = lp(x.astype(np.float32), 3200)
    return x * env_adsr(n, a=0.02, d=0.3, s=0.7, r=0.15)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    click = np.exp(-t / 0.003) * 0.4
    return np.tanh(1.6 * (x + click)).astype(np.float32)


def clap(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    x = bp(noise, 900, 4500)
    e = np.exp(-t / 0.07) * (1 + 0.6 * (np.sin(2 * np.pi * 90 * t) > 0) * (t < 0.03))
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.4
    return (x * e + tone).astype(np.float32)


def hat(rng, open_=False):
    n = int((0.35 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n).astype(np.float32), 7000)
    return (x * np.exp(-t / (0.12 if open_ else 0.018))).astype(np.float32)


def crash(rng, dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal((n, 2)).astype(np.float32), 4000)
    return x * np.exp(-t / 0.7)[:, None].astype(np.float32)


def impact(rng):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 32 + 70 * np.exp(-t / 0.25)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    noise = lp(rng.standard_normal(n).astype(np.float32), 2500) * np.exp(-t / 0.25)
    x = np.tanh(1.4 * sub) + 0.5 * noise
    return np.stack([x, x], 1).astype(np.float32)


def sparkle(rng, m):
    """hit：一声短促的“闪光”（上行的铃音 + 一丝噪声）。"""
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    f = float(midi(m))
    bell = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) +
            0.2 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t / 0.35)
    sw = hp(rng.standard_normal(n).astype(np.float32), 6000) * np.exp(-t / 0.05) * 0.3
    thump = np.sin(2 * np.pi * (60 + 80 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.12) * 0.6
    return (bell * 0.5 + sw + thump).astype(np.float32)


def riser(rng, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    blocks = 32
    out = np.zeros(n, np.float32)
    for i in range(blocks):
        a, b = i * n // blocks, (i + 1) * n // blocks
        fc = 400 * (20 ** (i / blocks))
        out[a:b] = bp(noise[a:b], fc * 0.7, fc * 1.5)
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (2 * t / dur)) / SR) * 0.3
    e = (t / dur) ** 2
    return ((out + tone) * e).astype(np.float32)


# ------------------------------------------------------------------ 编曲
ARP = {
    0: [0, 2, 1, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 4, 3, 1],
    1: [0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 5, 6, 7],
    2: [0, 4, 2, 5, 1, 6, 3, 7, 0, 4, 2, 5, 3, 6, 4, 7],
    3: [7, 5, 6, 4, 5, 3, 4, 2, 3, 1, 2, 0, 1, 3, 5, 7],
    9: [0, 2, 4, 6, 7, 6, 4, 2, 1, 3, 5, 7, 6, 5, 3, 1],
}


def build_music(timeline, total, path=None):
    mix = Mix(total)
    rng = mix.rng
    K = kick()
    kicks = []
    order = [s["scene"] for s in timeline]
    for si, sc in enumerate(timeline):
        prog_id, levels = section(sc["scene"])
        prog = PROG[prog_id]
        arp_pat = ARP.get(prog_id, ARP[0])
        nbars = int(round(sc["duration"] / BAR))
        nxt = order[si + 1] if si + 1 < len(order) else None
        for b in range(nbars):
            t0 = sc["start"] + b * BAR
            lt = b * BAR
            lv = level_at(levels, lt)
            # 讲解段落每 16 小节留 4 小节“喘口气”：鼓和贝斯退一档
            if sc["scene"] in CHAPTER_OF and lv >= 2 and b % 16 >= 12 and b < nbars - 1:
                lv -= 1
            chord = CH[prog[(b // 2) % len(prog)]]
            root, notes = chord
            last = b == nbars - 1
            # 铺底：两小节一个和弦
            if b % 2 == 0:
                dur = min(2, nbars - b) * BAR + 0.9
                bright = [0.15, 0.3, 0.45, 0.6, 0.75][lv]
                mix.put(t0, pad_block(notes, dur, bright, rng), gain=[0.26, 0.27, 0.26, 0.24, 0.24][lv], verb=0.5)
            # 低音长音（0 档）
            if lv == 0 and b % 2 == 0:
                n = int(min(2, nbars - b) * BAR * SR)
                x = lp(saw(float(midi(root)), n), 180) * env_adsr(n, 0.5, 1, 0.8, 0.8)
                mix.put(t0, x, gain=0.07)
            # 琶音
            if lv >= 1:
                tones = notes + [m + 12 for m in notes]
                step = BEAT / 4
                br = [0, 0.25, 0.45, 0.65, 0.8][lv]
                g = [0, 0.08, 0.09, 0.1, 0.1][lv]
                for k in range(16):
                    if lv == 1 and k % 2 == 1:
                        continue
                    m = tones[arp_pat[k] % len(tones)] + 12
                    mix.put(t0 + k * step, pluck(m, bright=br), gain=g, pan=0.35 * np.sin(k * 0.8), verb=0.25,
                            delay=0.4)
            # 鼓
            if lv >= 1:
                beats = [0, 2] if lv == 1 else [0, 1, 2, 3]
                kg = [0, 0.2, 0.28, 0.34, 0.38][lv]
                for q in beats:
                    if last and lv >= 2 and q == 3:
                        continue
                    mix.put(t0 + q * BEAT, K, gain=kg)
                    kicks.append(t0 + q * BEAT)
                # 踩镲
                hg = [0, 0.018, 0.03, 0.04, 0.045][lv]
                sub = 2 if lv <= 2 else 4
                for k in range(4 * sub):
                    if lv >= 2 and sub == 2 and k % 2 == 0:
                        hgk = hg * 0.6
                    else:
                        hgk = hg
                    mix.put(t0 + k * BEAT / sub, hat(rng), gain=hgk, pan=0.3)
                if lv >= 3:
                    for q in (0.5, 1.5, 2.5, 3.5):
                        mix.put(t0 + q * BEAT, hat(rng, True), gain=0.025, pan=-0.3)
            if lv >= 2:
                cg = [0, 0, 0.12, 0.16, 0.18][lv]
                for q in (1, 3):
                    mix.put(t0 + q * BEAT, clap(rng), gain=cg, verb=0.3)
                if last:   # 小节末的军鼓滚奏
                    for k in range(4):
                        mix.put(t0 + 3 * BEAT + k * BEAT / 4, clap(rng), gain=cg * (0.4 + 0.15 * k), verb=0.2)
            # 贝斯
            if lv >= 2:
                bg = [0, 0, 0.12, 0.14, 0.15][lv]
                for k in range(8):
                    m = root + (12 if (lv >= 3 and k % 4 == 3) else 0)
                    mix.put(t0 + k * BEAT / 2, bass_note(m, BEAT / 2 * 0.9, 0.3 + 0.15 * lv), gain=bg)
            # 旋律（3 档以上）
            if lv >= 3:
                top = sorted(notes)[-1] + 12
                motif = [(0, 1.5, top), (1.5, 1.5, top - (3 if b % 2 else 5)), (3, 1, notes[1] + 12)]
                for (a, d, m) in motif:
                    mix.put(t0 + a * BEAT, lead_note(m, d * BEAT * 0.95, rng), gain=0.1, pan=-0.1, verb=0.35, delay=0.25)
            if lv >= 4 and b % 4 == 0:
                mix.put(t0, crash(rng), gain=0.09, verb=0.3)
            # 场景结尾：通向章节卡的上升音
            if last and nxt in ("Card1", "Card2", "Card3", "Outro"):
                r = riser(rng, BAR * 2)
                mix.put(t0 + BAR - BAR * 2, r, gain=0.12, verb=0.3)
        # 重音
        for c in sc["cues"]:
            chord = CH[prog[0]]
            if c["kind"] == "impact":
                mix.put(c["t"], impact(rng), gain=0.42, verb=0.4)
                mix.put(c["t"], crash(rng, 3.0), gain=0.1, verb=0.4)
                kicks.append(c["t"])
            else:
                m = chord[1][rng.integers(0, 4)] + 24
                mix.put(c["t"], sparkle(rng, m), gain=0.13, pan=rng.uniform(-0.4, 0.4), verb=0.4)
    # 开场前 4 秒：粒子汇聚时的上升音
    mix.put(0.0, riser(rng, 4.0), gain=0.16, verb=0.3)

    # 侧链：底鼓之后把铺底、贝斯压下去一点
    duck = np.ones(mix.n, np.float32)
    L = int(0.25 * SR)
    shape = (1 - 0.45 * np.exp(-np.arange(L) / SR / 0.08)).astype(np.float32)
    for tk in kicks:
        a = int(tk * SR)
        if a < mix.n:
            seg = duck[a:a + L]
            np.minimum(seg, shape[:len(seg)], out=seg)
    # 乒乓延迟（附点八分）
    d = int(BEAT * 0.75 * SR)
    delayed = np.zeros_like(mix.delay)
    src = mix.delay.copy()
    for k in range(1, 6):
        g = 0.45 ** k
        ch = k % 2
        sh = d * k
        if sh < mix.n:
            mono = src[:-sh, 0] + src[:-sh, 1]
            delayed[sh:, ch] += mono * g * 0.5
    delayed = lp(delayed, 3500)
    # 混响
    ir_n = int(2.8 * SR)
    ti = np.arange(ir_n) / SR
    out = mix.dry + delayed
    wet = np.zeros_like(out)
    vin = mix.verb + delayed * 0.4
    for ch in range(2):
        ir = (rng.standard_normal(ir_n) * np.exp(-ti / 0.75)).astype(np.float32)
        ir = lp(ir, 6000)
        ir /= np.sqrt((ir ** 2).sum())
        wet[:, ch] = oaconvolve(vin[:, ch], ir)[: mix.n]
    out = out * duck[:, None] ** 0.6 + wet * 0.55
    out = hp(out, 30)
    # 收尾淡出
    end = int(total * SR)
    fade = int(3.0 * SR)
    out[end - fade:end] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None] ** 2
    out[end:] = 0
    out = out[:end]
    out = np.tanh(out * 1.2) / np.tanh(1.2)
    out *= 0.9 / (np.max(np.abs(out)) + 1e-9)
    if path:
        import wave
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return out
