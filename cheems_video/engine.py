"""时间轴：按配音实际长度排出每一拍的起止时间，提供嘴型、表情查询；并完成整片混音。"""
from __future__ import annotations

import os
import pickle

import numpy as np

import audio
from script import MOUTH_OF, NAMES, SCENES, TEMPO, VOICES
from tts import cache_path

FPS = 30
FADE = 0.35  # 场与场之间的黑场过渡（每边）

# 台词说话人 → 画面上动嘴的角色
WHO_CHAR = {"cheems": "cheems", "cat": "cat", "husky": "husky", "corgi": "corgi", "zhuang": "zhuang",
            "golden": "golden", "owner": "owner", "parrot": "parrot", "thief": "thief", "staff": "staff",
            "narr": None, "rules": None, "hidden": None}


class Beat:
    def __init__(self, b, start, dur, audio_len=0.0, env=None):
        self.kind = b.kind
        self.id = b.id
        self.start = start
        self.dur = dur
        self.end = start + dur
        self.audio_len = audio_len
        self.env = env
        self.emo = dict(b.emo)
        self.sfx = list(b.sfx)
        if b.kind == "line":
            self.who = b.who
            self.text = b.text
            self.sub = b.sub
            self.fx = b.fx
            self.pre = b.pre
            self.char = MOUTH_OF.get(b.who, WHO_CHAR.get(b.who))
            self.name = NAMES.get(b.who, "")
        elif b.kind == "card":
            self.text = b.text
            self.sub = b.sub


class SceneT:
    def __init__(self, sc, start):
        self.name = sc.name
        self.start = start
        self.beats = []
        self.music = sc.music
        self.amb = sc.amb
        self.ids = {}
        self.dur = 0.0

    def add(self, beat):
        self.beats.append(beat)
        if beat.id:
            self.ids[beat.id] = beat
        self.dur = beat.end

    # ---- 查询
    def s(self, bid):
        return self.ids[bid].start

    def e(self, bid):
        return self.ids[bid].end

    def ae(self, bid):
        """台词声音结束的时间。"""
        b = self.ids[bid]
        return b.start + b.pre + b.audio_len if b.kind == "line" else b.end

    def p(self, bid, t, a=0.0, b=None, ease=None):
        """在拍 bid 内的进度（0~1）。a、b 是相对拍起点的秒数，b 为 None 时到拍结束；b<0 表示从结束往前数。"""
        bt = self.ids[bid]
        t0 = bt.start + a
        if b is None:
            t1 = bt.end
        elif b < 0:
            t1 = bt.end + b
        else:
            t1 = bt.start + b
        if t1 <= t0:
            return 1.0 if t >= t0 else 0.0
        k = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
        return ease(k) if ease else k

    def pe(self, bid, t, d):
        """拍结束前 d 秒内的进度（0~1），用来做淡出。"""
        b = self.ids[bid]
        return min(max((t - (b.end - d)) / d, 0.0), 1.0)

    def after(self, bid, t, off=0.0):
        return t >= self.ids[bid].start + off

    def within(self, bid, t):
        b = self.ids[bid]
        return b.start <= t < b.end

    def talk(self, char, t):
        for b in self.beats:
            if b.kind == "line" and b.char == char:
                t0 = b.start + b.pre
                if t0 <= t < t0 + b.audio_len and b.env is not None:
                    i = int((t - t0) * FPS)
                    return float(b.env[min(i, len(b.env) - 1)])
        return 0.0

    def speaking(self, char, t):
        for b in self.beats:
            if b.kind == "line" and b.char == char and b.start <= t < b.start + b.pre + b.audio_len:
                return True
        return False

    def emo(self, char, t, default="normal"):
        cur = default
        for b in self.beats:
            if b.start > t:
                break
            if char in b.emo:
                cur = b.emo[char]
        return cur

    def line_at(self, t):
        for b in self.beats:
            if b.kind == "line" and b.start <= t < b.start + b.pre + b.audio_len + min(b.dur - b.audio_len - b.pre, 0.6):
                return b
        return None

    def card_at(self, t):
        for b in self.beats:
            if b.kind == "card" and b.start <= t < b.end:
                return b
        return None


class Timeline:
    def __init__(self):
        self.scenes = []
        self.dur = 0.0

    def find(self, T):
        for sc in self.scenes:
            if sc.start <= T < sc.start + sc.dur:
                return sc, T - sc.start
        sc = self.scenes[-1]
        return sc, sc.dur - 1e-3


def build(work, mix=True):
    """读配音、套特效、排时间轴；mix=True 时顺便混出整片音轨 work/mix.wav。"""
    tl = Timeline()
    voices = []  # (全局时间, 音频)
    T = 0.0
    for sc in SCENES:
        st = SceneT(sc, T)
        t = 0.0
        for b in sc.beats:
            if b.kind == "line":
                path = cache_path(VOICES[b.who], b.text)
                x = audio.load_wav(path)
                x = audio.tempo(audio.trim_silence(x), b.speed or TEMPO.get(b.who, 1.0))
                x = audio.voice_fx(x, b.fx) * b.vol
                alen = len(x) / audio.SR
                env = audio.mouth_env(x, FPS)
                dur = b.pre + alen + b.gap
                beat = Beat(b, t, dur, alen, env)
                voices.append((T + t + b.pre, x))
            else:
                beat = Beat(b, t, b.dur)
            st.add(beat)
            t += beat.dur
        # 每场前后留出过渡时间
        st.dur = t + FADE
        tl.scenes.append(st)
        T += st.dur
    tl.dur = T
    with open(os.path.join(work, "timeline.pkl"), "wb") as f:
        pickle.dump(tl, f)
    print(f"时间轴：{len(tl.scenes)} 场，总长 {T / 60:.1f} 分钟")
    if mix:
        mixdown(tl, voices, os.path.join(work, "mix.wav"))
    return tl


def mixdown(tl, voices, out):
    SR = audio.SR
    n = int((tl.dur + 2) * SR)
    vox = np.zeros(n, np.float32)
    for at, x in voices:
        audio.place(vox, x, at)
    fx = np.zeros((n, 2), np.float32)
    mus = np.zeros((n, 2), np.float32)
    amb = np.zeros((n, 2), np.float32)
    cache = {}
    for sc in tl.scenes:
        for b in sc.beats:
            for name, off, g in b.sfx:
                if name not in cache:
                    cache[name] = audio.sfx(name)
                x = cache[name]
                at = sc.start + b.start + off
                audio.place(fx[:, 0], x, at, g)
                audio.place(fx[:, 1], x, at, g)
    # 配乐：相邻同名的场连成一段，段与段之间交叉淡化
    runs = []
    for sc in tl.scenes:
        if runs and runs[-1][0] == sc.music:
            runs[-1][2] = sc.start + sc.dur
        else:
            runs.append([sc.music, sc.start, sc.start + sc.dur])
    xf = 1.2
    for name, a, b in runs:
        if not name:
            continue
        a2 = max(0.0, a - xf / 2)
        seg = audio.cue(name, b - a2 + xf)
        g = {"day": 0.85, "lobby": 0.8, "night": 1.0, "night2": 1.0, "cold": 1.0, "tension": 0.9,
             "tension2": 0.9, "reveal": 0.9, "action": 0.75, "warm": 0.8, "ending": 0.85}.get(name, 0.8)
        i = int(a2 * SR)
        m = min(len(seg), n - i)
        mus[i:i + m] += seg[:m] * g
    runs = []
    for sc in tl.scenes:
        if runs and runs[-1][0] == sc.amb:
            runs[-1][2] = sc.start + sc.dur
        else:
            runs.append([sc.amb, sc.start, sc.start + sc.dur])
    for name, a, b in runs:
        if not name:
            continue
        seg = audio.ambience(name, b - a)
        f = min(int(0.5 * SR), len(seg) // 3)
        seg[:f] *= np.linspace(0, 1, f)[:, None]
        seg[-f:] *= np.linspace(1, 0, f)[:, None]
        i = int(a * SR)
        m = min(len(seg), n - i)
        amb[i:i + m] += seg[:m]
    # 对白闪避：有人说话时配乐压低
    envl = audio.filt(np.abs(vox), "low", 3, 2)
    duck = 1.0 - 0.55 * np.clip(envl / 0.04, 0, 1)
    mus *= duck[:, None]
    master = mus * 0.55 + amb * 0.8 + fx * 0.75
    master[:, 0] += vox * 1.6
    master[:, 1] += vox * 1.6
    # 响度：整体 RMS 归一，再软限幅
    rms = np.sqrt(np.mean(master ** 2) + 1e-12)
    master *= 0.085 / rms
    master = np.tanh(master * 1.15) / 1.15
    pk = np.abs(master).max()
    if pk > 0.97:
        master *= 0.97 / pk
    audio.save_wav(out, master[: int(tl.dur * SR)])
    print("混音完成", out)


def load(work):
    with open(os.path.join(work, "timeline.pkl"), "rb") as f:
        return pickle.load(f)
