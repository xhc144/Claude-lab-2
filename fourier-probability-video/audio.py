"""音轨：没有配音，只有音效和铺底，全部用 numpy 合成。

- 铺底：每章一组和弦的慢速铺垫（几层略微失谐的泛音），章与章之间交叉淡化；最后落在 D 大调。
- 频率的声音：画面里频率 t 在变的时候，有一个音高跟着 t 走、音量跟着 |φ(t)| 走的持续音（scene.tone）。
- 音效：按各场景的 sfx 提示放置——呼啸、钟声、冲击、故障、硬币、雨滴、噼啪声……统一过一个合成的混响。
"""

import math
import wave

import numpy as np
from scipy.signal import istft, oaconvolve, stft

SR = 48000


def tl_samples(t):
    return int(round(t * SR))


# ---------------------------------------------------------------- 基本零件
def envelope(n, attack, release, curve=2.0):
    """attack / release 以秒计；中间保持 1。"""
    e = np.ones(n, np.float32)
    a = min(n, int(attack * SR))
    r = min(n - a, int(release * SR))
    if a > 0:
        e[:a] = np.linspace(0, 1, a) ** curve
    if r > 0:
        e[n - r:] = np.linspace(1, 0, r) ** curve
    return e


def decay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR)).astype(np.float32)


def shaped_noise(dur, center, width, rng):
    """噪声在频域里按随时间变化的“中心频率 / 宽度”塑形：center(t), width(t) 都是 Hz。"""
    n = int(dur * SR)
    x = rng.standard_normal(n + 2048).astype(np.float32)
    f, t, Z = stft(x, SR, nperseg=1024)
    tt = np.clip(t / dur, 0, 1)
    c = center(tt)[None, :]
    w = width(tt)[None, :]
    mask = np.exp(-0.5 * ((f[:, None] - c) / w) ** 2)
    _, y = istft(Z * mask, SR, nperseg=1024)
    y = y[:n].astype(np.float32)
    return y / (np.max(np.abs(y)) + 1e-9)


def osc(freq, n, phase=0.0, shape="sine"):
    """freq 可以是常数或逐样本数组。"""
    if np.isscalar(freq):
        ph = phase + 2 * np.pi * freq * np.arange(n) / SR
    else:
        ph = phase + 2 * np.pi * np.cumsum(freq) / SR
    if shape == "sine":
        return np.sin(ph).astype(np.float32)
    if shape == "soft":                                  # 带几个泛音的柔和音色
        return (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph) + 0.06 * np.sin(4 * ph)).astype(np.float32) / 1.5
    raise ValueError(shape)


def pan2(x, pan):
    a = (pan + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], 1)


# ---------------------------------------------------------------- 音效
def sfx_chime(p, rng):
    f = p.get("f", 880)
    n = int(3.2 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for ratio, amp, tau in ((1.0, 1.0, 1.4), (2.0, 0.5, 0.9), (3.01, 0.28, 0.6), (4.16, 0.18, 0.4), (5.43, 0.12, 0.25)):
        out += amp * np.sin(2 * np.pi * f * ratio * t + rng.random() * 6) * np.exp(-t / tau)
    out *= envelope(n, 0.003, 0.05)
    return pan2(out * 0.16 * p.get("amp", 1.0), rng.uniform(-0.35, 0.35))


def sfx_coin(p, rng):
    f = p.get("f", 1600)
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for ratio, amp, tau in ((1.0, 1.0, 0.35), (2.76, 0.6, 0.18), (5.40, 0.35, 0.09), (8.93, 0.2, 0.05)):
        out += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / tau)
    out *= envelope(n, 0.001, 0.02)
    return pan2(out * 0.10, rng.uniform(-0.5, 0.5))


def sfx_tick(p, rng):
    f = p.get("f", 1500)
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.004)
    out = 0.6 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018) + 0.25 * noise
    return pan2(out.astype(np.float32) * 0.12 * p.get("amp", 1.0), rng.uniform(-0.6, 0.6))


def sfx_cap(p, rng):
    """说明文字出现：很轻的一声“嘀”。"""
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 2200 + 900 * t / t[-1]
    out = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025) * envelope(n, 0.002, 0.01)
    return pan2(out.astype(np.float32) * 0.035, 0.0)


def sfx_drop(p, rng):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    f0 = rng.uniform(1400, 2600)
    f = f0 * np.exp(-t / 0.03) + 500
    out = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.02)
    return pan2(out.astype(np.float32) * 0.05, rng.uniform(-0.8, 0.8))


def sfx_whoosh(p, rng):
    dur = p.get("dur", 1.5)
    x = shaped_noise(dur, lambda u: 300 + 2600 * np.sin(np.pi * u) ** 2, lambda u: 300 + 900 * np.sin(np.pi * u), rng)
    n = len(x)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    # 左右扫过
    pan = np.linspace(-0.7, 0.7, n) * rng.choice([-1, 1])
    a = (pan + 1) * np.pi / 4
    y = x * e * 0.22
    return np.stack([y * np.cos(a), y * np.sin(a)], 1).astype(np.float32)


def sfx_riser(p, rng):
    dur = p.get("dur", 3.0)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    noise = shaped_noise(dur, lambda v: 400 + 5000 * v ** 2, lambda v: 200 + 1500 * v, rng)
    f = 160 * 2 ** (3 * u ** 1.5)
    tone = osc(f, n, shape="soft") + 0.5 * osc(f * 1.5, n, shape="sine")
    y = (0.6 * noise + 0.35 * tone) * u ** 2.2 * 0.22
    y *= envelope(n, 0.01, 0.03)
    return np.stack([y, np.roll(y, 240)], 1).astype(np.float32)


def sfx_impact(p, rng):
    n = int(4.5 * SR)
    t = np.arange(n) / SR
    # 低频下潜
    f = 30 + 40 * np.exp(-t / 0.25)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1)
    # 噪声冲击
    nb = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.08)
    nb = np.convolve(nb, np.ones(24) / 24, mode="same")
    # 铜管般的低音和弦（Braam）
    braam = np.zeros(n)
    for fr, amp in ((73.42, 1.0), (110.0, 0.7), (146.83, 0.5), (174.61, 0.35)):
        ph = 2 * np.pi * fr * t
        braam += amp * (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.33 * np.sin(3 * ph) + 0.2 * np.sin(4 * ph))
    braam *= np.exp(-t / 1.4) * (1 - np.exp(-t / 0.02))
    y = 0.55 * sub + 0.5 * nb + 0.11 * braam
    y = np.tanh(y * 1.4) * 0.5
    y *= envelope(n, 0.001, 0.3)
    return np.stack([y, y * 0.97], 1).astype(np.float32)


def sfx_boom(p, rng):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    f = 38 + 50 * np.exp(-t / 0.15)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    nb = rng.standard_normal(n) * np.exp(-t / 0.05)
    nb = np.convolve(nb, np.ones(40) / 40, mode="same")
    y = np.tanh((0.7 * sub + 0.6 * nb) * 1.3) * 0.38
    y *= envelope(n, 0.001, 0.2)
    return np.stack([y, y], 1).astype(np.float32)


def sfx_glitch(p, rng, amp=1.0):
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # 降采样 + 量化：数字感
    hold = int(rng.integers(6, 30))
    x = np.repeat(x[::hold], hold)[:n]
    x = np.round(x * 3) / 3
    gate = (rng.random(n // 600 + 1) > 0.35).repeat(600)[:n]
    beep = np.sin(2 * np.pi * rng.choice([880, 1320, 1760, 2640]) * t) * (rng.random(n // 900 + 1) > 0.6).repeat(900)[:n]
    y = (0.6 * x * gate + 0.4 * beep) * np.exp(-t / 0.15) * 0.16 * amp
    return np.stack([y * rng.uniform(0.6, 1), y * rng.uniform(0.6, 1)], 1).astype(np.float32)


def sfx_alarm(p, rng):
    n = int(0.9 * SR)
    y = np.zeros(n)
    for k, f in enumerate((740, 698.46, 740)):
        s0 = int(k * 0.22 * SR)
        m = int(0.16 * SR)
        tt = np.arange(m) / SR
        y[s0:s0 + m] += np.sin(2 * np.pi * f * tt) * envelope(m, 0.005, 0.06) + 0.3 * np.sin(4 * np.pi * f * tt) * envelope(m, 0.005, 0.06)
    return pan2((y * 0.07).astype(np.float32), 0.0)


def sfx_pitch(p, rng):
    dur = p.get("dur", 2.0)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    f0 = p.get("f0", 330)
    f = f0 * 2 ** (u if p.get("up", True) else -u)
    y = osc(f, n, shape="soft") * np.sin(np.pi * u) ** 1.2 * 0.07
    return np.stack([y, np.roll(y, 300)], 1).astype(np.float32)


def sfx_shimmer(p, rng):
    dur = p.get("dur", 3.0)
    n = int((dur + 1.0) * SR)
    out = np.zeros((n, 2), np.float32)
    k = int(30 * dur)
    for _ in range(k):
        t0 = rng.random() * dur
        f = rng.uniform(2500, 7000)
        m = int(0.35 * SR)
        tt = np.arange(m) / SR
        g = (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.08) * envelope(m, 0.003, 0.02)).astype(np.float32)
        s0 = int(t0 * SR)
        amp = 0.03 * math.sin(math.pi * t0 / dur) ** 0.5
        out[s0:s0 + m] += pan2(g * amp, rng.uniform(-0.9, 0.9))[: n - s0]
    return out


def sfx_swell(p, rng):
    dur = p.get("dur", 3.0)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    x = shaped_noise(dur, lambda v: 3000 + 4000 * v, lambda v: 1500 + 2000 * v, rng)
    y = x * u ** 3 * envelope(n, 0.0, 0.08) * 0.10
    return np.stack([y, np.roll(y, 500)], 1).astype(np.float32)


def sfx_rewind(p, rng):
    dur = p.get("dur", 1.6)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    f = 1800 * 2 ** (-4 * u) + 120
    y = osc(f, n, shape="soft") * 0.08
    noise = shaped_noise(dur, lambda v: 4000 - 3000 * v, lambda v: 800 + 0 * v, rng) * 0.06
    y = (y + noise) * envelope(n, 0.05, 0.3)
    return np.stack([y, np.roll(y, 200)], 1).astype(np.float32)


def sfx_rain(p, rng):
    dur = p.get("dur", 5.0)
    n = int((dur + 0.3) * SR)
    out = np.zeros((n, 2), np.float32)
    for _ in range(int(26 * dur)):
        t0 = rng.random() * dur
        d = sfx_drop({}, rng) * 0.8
        s0 = int(t0 * SR)
        out[s0:s0 + len(d)] += d[: n - s0]
    return out


def sfx_fire(p, rng):
    """噼啪声 + 低沉的呼呼声：铁环被烧热。"""
    dur = p.get("dur", 8.0)
    n = int(dur * SR)
    rumble = shaped_noise(dur, lambda v: 180 + 0 * v, lambda v: 120 + 0 * v, rng) * 0.06
    out = np.stack([rumble, np.roll(rumble, 400)], 1)
    for _ in range(int(9 * dur)):
        s0 = int(rng.random() * (n - 2000))
        m = int(rng.uniform(0.002, 0.012) * SR)
        click = rng.standard_normal(m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.02, 0.09)
        out[s0:s0 + m] += pan2(click.astype(np.float32), rng.uniform(-0.8, 0.8))
    out *= envelope(n, 1.0, 1.5)[:, None]
    return out.astype(np.float32)


def sfx_hiss(p, rng):
    dur = p.get("dur", 20.0)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    x = shaped_noise(dur, lambda v: 5000 - 3500 * v, lambda v: 2500 - 1500 * v, rng)
    y = x * 0.022 * (1 - u) ** 0.7 * envelope(n, 1.5, 2.0)
    return np.stack([y, np.roll(y, 700)], 1).astype(np.float32)


def sfx_drone_in(p, rng):
    n = int(8 * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 36.71 * t) + 0.5 * np.sin(2 * np.pi * 73.42 * t)) * (t / 8) ** 2 * np.exp(-np.maximum(t - 6, 0) / 0.8)
    return pan2((y * 0.12).astype(np.float32), 0.0)


def sfx_outro(p, rng):
    """片尾：一串上行的钟声分解和弦，落在 D 大调。"""
    dur = p.get("dur", 10.0)
    n = int((dur + 3) * SR)
    out = np.zeros((n, 2), np.float32)
    notes = [293.66, 369.99, 440.0, 587.33, 739.99, 880.0, 1174.66]
    for i, f in enumerate(notes):
        c = sfx_chime({"f": f, "amp": 0.6}, rng)
        s0 = int((0.5 + i * 0.32) * SR)
        out[s0:s0 + len(c)] += c[: n - s0]
    return out


SFX = {
    "chime": sfx_chime, "coin": sfx_coin, "tick": sfx_tick, "cap": sfx_cap, "drop": sfx_drop, "whoosh": sfx_whoosh,
    "riser": sfx_riser, "impact": sfx_impact, "boom": sfx_boom, "glitch": sfx_glitch, "alarm": sfx_alarm,
    "pitch": sfx_pitch, "shimmer": sfx_shimmer, "swell": sfx_swell, "rewind": sfx_rewind, "rain": sfx_rain,
    "fire": sfx_fire, "hiss": sfx_hiss, "drone_in": sfx_drone_in, "outro": sfx_outro,
    "glitch_sfx": lambda p, rng: sfx_glitch(p, rng, 0.6 * p.get("amp", 1.0)),
}


# ---------------------------------------------------------------- 铺底和弦
CHORDS = [
    [73.42, 110.0, 146.83, 174.61, 329.63],          # 0 片头    Dm(add9)
    [58.27, 87.31, 146.83, 220.0, 261.63],           # 1 第 1 章 B♭maj7(add9)
    [87.31, 130.81, 220.0, 261.63, 392.0],           # 2 第 2 章 F(add9)
    [65.41, 98.0, 164.81, 196.0, 293.66],            # 3 第 3 章 C(add9)
    [49.0, 73.42, 116.54, 174.61, 220.0],            # 4 第 4 章 Gm9
    [55.0, 82.41, 110.0, 146.83, 164.81],            # 5 第 5 章 Asus4
    [58.27, 87.31, 146.83, 174.61, 261.63],          # 6 第 6 章 B♭(add9)
    [73.42, 110.0, 174.61, 220.0, 261.63],           # 7 第 7 章 Dm7
    [73.42, 110.0, 185.0, 220.0, 329.63],            # 8 尾声    D(add9)
]


def pad(chord, n, rng):
    t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for j, f in enumerate(chord):
        lfo = 0.65 + 0.35 * np.sin(2 * np.pi * (0.03 + 0.02 * rng.random()) * t + rng.random() * 6)
        amp = 1.0 / (1 + 0.35 * j) * (1.3 if f < 80 else 1.0)
        for side, det in ((0, 0.9985), (1, 1.0015)):
            ph = 2 * np.pi * f * det * t + rng.random() * 6
            v = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
            out[:, side] += (v * lfo * amp).astype(np.float32)
    return out / len(chord)


def bed(tl, n_total, rng):
    out = np.zeros((n_total, 2), np.float32)
    xf = 2.5
    for s in tl.scenes:
        s0 = max(0, tl_samples(s.start - xf / 2))
        s1 = min(n_total, tl_samples(s.start + s.dur + xf / 2))
        n = s1 - s0
        p = pad(CHORDS[s.bed], n, rng)
        p *= envelope(n, xf, xf, 1.0)[:, None]
        out[s0:s1] += p
    # 空气声：很轻的高频噪声
    air = shaped_noise(n_total / SR, lambda v: 6000 + 0 * v, lambda v: 2500 + 0 * v, rng) * 0.012
    out[:, 0] += air
    out[:, 1] += np.roll(air, 900)
    return out * 0.17


# ---------------------------------------------------------------- 频率的声音
def tones(tl, n_total):
    out = np.zeros((n_total, 2), np.float32)
    for s in tl.scenes:
        if s.tone is None:
            continue
        s0 = tl_samples(s.start)
        n = min(n_total - s0, tl_samples(s.dur))
        u = np.arange(n) / SR
        f, a = s.tone(u)
        f = np.broadcast_to(np.asarray(f, float), (n,)).astype(np.float64)
        a = np.broadcast_to(np.asarray(a, float), (n,)).astype(np.float64)
        # 音量平滑，避免咔哒声
        k = int(0.03 * SR)
        a = np.convolve(a, np.ones(k) / k, mode="same")
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * u)
        y = osc(f * vib, n, shape="soft") * a
        y2 = osc(f * 1.003, n, shape="sine") * a * 0.4
        out[s0:s0 + n, 0] += (y + 0.6 * y2).astype(np.float32)
        out[s0:s0 + n, 1] += (0.85 * y + y2).astype(np.float32)
    return out


# ---------------------------------------------------------------- 混音
def reverb_ir(rng, dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-t / 0.55)[:, None].astype(np.float32)
    ir[: int(0.02 * SR)] = 0
    # 高频衰减得更快：简单地把尾巴做个滑动平均
    for c in range(2):
        ir[:, c] = np.convolve(ir[:, c], np.ones(6) / 6, mode="same")
    return ir / np.sqrt(np.sum(ir ** 2, 0))


def build(tl, out_path):
    rng = np.random.default_rng(1234)
    n_total = tl_samples(tl.duration) + SR
    fx = np.zeros((n_total, 2), np.float32)
    for i, (t, kind, p) in enumerate(tl.all_sfx()):
        fn = SFX.get(kind)
        if fn is None:
            raise KeyError(f"未知的音效种类：{kind}")
        sig = fn(p, np.random.default_rng(1000 + i))
        s0 = tl_samples(t)
        m = min(len(sig), n_total - s0)
        if m > 0:
            fx[s0:s0 + m] += sig[:m]
    ton = tones(tl, n_total)
    ir = reverb_ir(rng)
    send = fx + 0.6 * ton
    wet = np.stack([oaconvolve(send[:, c], ir[:, c], mode="full")[:n_total] for c in range(2)], 1).astype(np.float32)
    mix = bed(tl, n_total, rng) + fx + ton + 0.32 * wet
    # 首尾淡入淡出 + 柔和限幅
    mix *= envelope(n_total, 0.5, 2.5, 1.0)[:, None]
    peak = np.max(np.abs(mix)) + 1e-9
    mix = np.tanh(mix / peak * 1.6) / math.tanh(1.6) * 0.89
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path
