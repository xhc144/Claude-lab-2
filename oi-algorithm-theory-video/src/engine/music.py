"""背景音乐：用 numpy 合成的轻柔钢琴 + 铺底和弦，不用任何外部素材。

每集按“单元 + 集号”选调性、速度、和弦进行和随机种子，所以各集的音乐不一样，但风格一致：
慢速（60~72 BPM）分解和弦钢琴、偶尔一两个高音旋律音、很轻的长音铺底和低音，整体加一层混响。
结构是 A A B A（每段 8 小节）循环，音量偏低，适合边看边想。
"""

import math
import wave

import numpy as np

SR = 44100

# 大调音阶的半音位置
MAJOR = [0, 2, 4, 5, 7, 9, 11]

# 和弦进行：（级数，和弦类型）；类型 M7 / m7 / 7sus / add9 / m9 / 6
PROGS = [
    [(1, "M7"), (6, "m7"), (4, "M7"), (5, "add9"), (3, "m7"), (6, "m7"), (2, "m9"), (5, "7sus")],
    [(4, "M7"), (5, "add9"), (3, "m7"), (6, "m7"), (2, "m9"), (5, "7sus"), (1, "M7"), (1, "add9")],
    [(1, "add9"), (3, "m7"), (4, "M7"), (1, "M7"), (6, "m9"), (4, "M7"), (2, "m7"), (5, "7sus")],
    [(6, "m9"), (4, "M7"), (1, "add9"), (5, "add9"), (6, "m7"), (3, "m7"), (4, "M7"), (5, "7sus")],
]

QUAL = {
    "M7": [0, 4, 7, 11, 14],
    "m7": [0, 3, 7, 10, 14],
    "m9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14, 16],
    "7sus": [0, 5, 7, 10, 14],
    "6": [0, 4, 7, 9, 14],
}

# 各单元的调（相对 C 的半音）和速度
STYLE = {
    1: (2, 68), 2: (5, 66), 3: (7, 70), 4: (3, 64), 5: (9, 68), 6: (4, 66), 7: (10, 64), 8: (0, 70),
}


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def piano(freq, dur, vel, rng):
    """柔和的钢琴音：几条带非谐性的泛音，高泛音衰减更快；松键后快速收尾。"""
    rel = 0.6
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    base = 0.55 + freq / 900.0
    out = np.zeros(n)
    B = 0.00035
    for k, amp in enumerate((1.0, 0.42, 0.2, 0.09, 0.045, 0.02), start=1):
        f = freq * k * math.sqrt(1 + B * k * k)
        if f > 9000:
            break
        a = amp * (0.6 + 0.4 * vel) ** (k - 1)
        out += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t * base * (0.8 + 0.55 * k))
    att = 1 - np.exp(-t / 0.006)
    env = att
    off = t > dur
    env = env * np.where(off, np.exp(-(t - dur) / 0.18), 1.0)
    return out * env * vel


def pad(freqs, dur, rng):
    """长音铺底：每个音两条略微失谐的正弦，慢起慢收。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.12):
            ph = rng.uniform(0, 2 * np.pi)
            out += np.sin(2 * np.pi * (f * (1 + det / 100)) * t + ph)
            out += 0.18 * np.sin(2 * np.pi * 2 * f * t + ph)
    a = min(1.6, dur / 3)
    env = np.clip(t / a, 0, 1) * np.clip((dur - t) / a, 0, 1)
    env = env * env * (3 - 2 * env)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
    return out * env * trem / (2 * len(freqs))


def bass(freq, dur):
    n = int((dur + 0.4) * SR)
    t = np.arange(n) / SR
    env = (1 - np.exp(-t / 0.02)) * np.exp(-t / (dur * 0.7))
    return (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)) * env


def onepole(x, a):
    """一阶低通（a 越接近 1 越闷）。"""
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def reverb_ir(seconds, rng, tau=0.85):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        noise = rng.standard_normal(n)
        noise = onepole(noise, 0.55)
        ir = noise * np.exp(-t / tau)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


def compose(duration, unit=1, num=1):
    from scipy.signal import oaconvolve
    rng = np.random.default_rng(1000 * unit + num)
    key, bpm = STYLE.get(unit, (0, 68))
    bpm += int(rng.integers(-3, 4))
    beat = 60.0 / bpm
    bar = 4 * beat
    total = duration + 6
    n = int(total * SR) + SR * 4
    L = np.zeros(n)
    R = np.zeros(n)

    def put(sig, t0, gain, panv):
        i = int(t0 * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        L[i:i + len(sig)] += sig * gain * math.cos((panv + 1) * math.pi / 4)
        R[i:i + len(sig)] += sig * gain * math.sin((panv + 1) * math.pi / 4)

    progA = PROGS[(unit + num) % len(PROGS)]
    progB = PROGS[(unit + num + 1) % len(PROGS)]
    form = [progA, progA, progB, progA]
    root_c = 48 + key            # 低音区的 C（+调）
    nbars = int(math.ceil(total / bar)) + 1
    patterns = [
        [0, None, 2, 1, 3, None, 2, 1],
        [0, 2, None, 3, 1, None, 4, 2],
        [0, None, 1, 2, None, 3, 2, None],
        [0, 3, 2, None, 1, 4, None, 2],
    ]
    pat_i = int(rng.integers(0, len(patterns)))
    for b in range(nbars):
        prog = form[(b // 8) % 4]
        deg, q = prog[b % 8]
        root = root_c + MAJOR[deg - 1]
        tones = QUAL[q]
        t0 = b * bar
        # 密度慢慢起伏
        dens = 0.62 + 0.3 * math.sin(2 * math.pi * b / 23 + unit)
        if b % 8 == 0 and b:
            pat_i = (pat_i + int(rng.integers(1, 3))) % len(patterns)
        pat = patterns[pat_i]
        # 右手分解和弦：在中音区排一个开放的和弦
        voicing = []
        for x in tones:
            v = root + 12 + x
            while v > 81:
                v -= 12
            while v < 52:
                v += 12
            if v not in voicing:
                voicing.append(v)
        voicing.sort()
        for k, idx in enumerate(pat):
            if idx is None:
                continue
            if k > 0 and rng.random() > dens:
                continue
            m = voicing[idx % len(voicing)]
            vel = 0.45 + 0.25 * rng.random() - (0.08 if k % 2 else 0)
            st = t0 + k * beat / 2 + rng.normal(0, 0.008)
            put(piano(midi_hz(m), beat * 1.6, vel, rng), max(0, st), 0.30, -0.25 + 0.5 * rng.random())
        # 低音
        put(bass(midi_hz(root - 12), bar * 0.9), t0, 0.22, 0.0)
        if rng.random() < 0.35:
            put(bass(midi_hz(root - 12 + 7), beat * 1.5), t0 + 2.5 * beat, 0.12, 0.0)
        # 铺底
        put(pad([midi_hz(root + tones[0]), midi_hz(root + 12 + tones[1]), midi_hz(root + 12 + tones[3])],
                bar * 1.15, rng), t0, 0.16, 0.0)
        # 偶尔的高音旋律
        if rng.random() < 0.55:
            cand = [root + 24 + x for x in tones[:4]] + [root + 36 + tones[0]]
            cand = [c for c in cand if 72 <= c <= 88] or [root + 24 + tones[0]]
            m = int(rng.choice(cand))
            st = t0 + beat * float(rng.choice([0, 1, 1.5, 2, 3]))
            put(piano(midi_hz(m), beat * 2.5, 0.42 + 0.2 * rng.random(), rng), st, 0.24, 0.3 * rng.normal())
    dry = np.stack([L, R])
    irs = reverb_ir(3.0, rng)
    wet = np.stack([oaconvolve(L, irs[0])[:n], oaconvolve(R, irs[1])[:n]])
    mix = dry * 0.78 + wet * 0.55
    # 柔和一点：轻微低通
    mix = np.stack([onepole(mix[0], 0.18), onepole(mix[1], 0.18)])
    m = int(duration * SR)
    mix = mix[:, :m]
    # 响度：RMS 约 -22.5 dBFS（约 -21 LUFS，偏轻），再软限幅
    rms = np.sqrt(np.mean(mix ** 2)) + 1e-9
    mix *= (10 ** (-22.5 / 20)) / rms
    mix = np.tanh(mix * 1.6) / 1.6
    fi, fo = int(2.5 * SR), int(5.0 * SR)
    mix[:, :fi] *= np.linspace(0, 1, fi) ** 2
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
    return mix


def write_wav(path, mix):
    data = np.clip(mix.T, -1, 1)
    pcm = (data * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    import sys
    d = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    write_wav("build/music_test.wav", compose(d, 1, 1))
