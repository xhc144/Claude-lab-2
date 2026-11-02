"""背景音乐：程序即兴编出一支轻快的 lo-fi / 爵士流行小乐队，用 FluidSynth 和 FluidR3_GM 音色库里的真实乐器采样演奏。

- 乐器：电钢琴（或钢琴）弹七和弦、九和弦，指弹贝斯，轻爵士鼓（带一点摇摆），颤音琴 / 钢片琴 / 马林巴 / 长笛之一吹旋律，
  很轻的暖色铺底；
- 速度 88～98 BPM，大调，进行用 IV–V–iii–vi、ii–V–I–vi 这类明亮的流行爵士进行，不拖沓、不催眠；
- 结构：前奏 4 小节 → A（律动）/ B（加旋律）/ 间奏（去掉鼓，只剩和弦和旋律）轮换，每段 8 小节，最后淡出；
- 每集按“单元 + 集号”选调、速度、和弦进行、乐器和随机种子，所以各集都不一样，但风格统一；
- 渲染成 WAV 后用 ffmpeg 统一响度（约 −19 LUFS），开头淡入、结尾淡出。
"""

import json
import random
import subprocess
import tempfile
from pathlib import Path

import mido

SF2_CANDIDATES = ["/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/soundfonts/FluidR3_GM.sf2",
                  "/usr/share/sounds/sf2/default-GM.sf2"]
TPB = 480
SR = 44100

MAJOR = [0, 2, 4, 5, 7, 9, 11]
PENTA = [0, 2, 4, 7, 9]             # 大调五声音阶（相对主音）

# 和弦类型：相对根音的半音
QUAL = {
    "M7": [0, 4, 7, 11], "M9": [0, 4, 7, 11, 14], "m7": [0, 3, 7, 10], "m9": [0, 3, 7, 10, 14],
    "7": [0, 4, 7, 10], "9": [0, 4, 7, 10, 14], "sus": [0, 5, 7, 10, 14], "add9": [0, 4, 7, 14],
    "69": [0, 4, 7, 9, 14],
}

# 和弦进行：每小节一个和弦（级数, 类型）
PROGS = [
    [(4, "M9"), (5, "9"), (3, "m7"), (6, "m9")],      # IV–V–iii–vi（流行的“王道进行”）
    [(2, "m9"), (5, "9"), (1, "M9"), (6, "m7")],      # ii–V–I–vi
    [(1, "M9"), (6, "m9"), (2, "m7"), (5, "sus")],    # I–vi–ii–V
    [(4, "M7"), (3, "m7"), (2, "m9"), (1, "69")],     # IV–iii–ii–I
    [(6, "m9"), (4, "M9"), (1, "add9"), (5, "sus")],  # vi–IV–I–V
    [(1, "M9"), (3, "m7"), (4, "M9"), (5, "9")],      # I–iii–IV–V
    [(4, "M9"), (3, "m7"), (6, "m9"), (5, "sus")],    # IV–iii–vi–V
]

# 各单元的调（相对 C 的半音）和基准速度
STYLE = {1: (5, 94), 2: (2, 92), 3: (7, 96), 4: (3, 90), 5: (9, 95), 6: (0, 93), 7: (10, 90), 8: (4, 96)}

# GM 音色号（从 0 开始）
KEYS = [4, 4, 5, 0]                 # 电钢琴 1 / 电钢琴 2 / 原声钢琴
LEADS = [11, 11, 8, 12, 73, 13]     # 颤音琴、钢片琴、马林巴、长笛、木琴
BASS = 33                           # 指弹电贝斯
PAD = 89                            # 暖色铺底
KITS = [0, 32, 8]                   # 标准 / 爵士 / 房间鼓组

CH_KEYS, CH_BASS, CH_LEAD, CH_PAD, CH_DRUM = 0, 1, 2, 3, 9

# 伴奏的节奏型：(起拍, 时值, 力度系数)
COMP = [
    [(0, 1.4, 1.0), (1.5, 0.9, 0.8), (3.0, 0.4, 0.7), (3.5, 0.45, 0.78)],
    [(0, 1.9, 1.0), (2.5, 1.3, 0.85)],
    [(0, 0.9, 1.0), (1.5, 0.45, 0.72), (2.0, 0.9, 0.86), (3.5, 0.45, 0.8)],
    [(0, 0.45, 0.95), (0.5, 1.3, 0.8), (2.5, 0.45, 0.75), (3.0, 0.9, 0.85)],
]
# 旋律两小节的节奏型：(起拍, 时值)，拍数从 0 到 8
RHYTHMS = [
    [(0, 0.5), (0.5, 0.5), (1.0, 1.0), (2.5, 0.5), (3.0, 1.0), (4.5, 0.5), (5.0, 0.5), (5.5, 1.5)],
    [(0.5, 0.5), (1.0, 0.5), (1.5, 1.0), (3.0, 0.5), (3.5, 1.5), (5.0, 1.0), (6.0, 1.5)],
    [(0, 1.0), (1.5, 0.5), (2.0, 0.5), (2.5, 1.0), (4.0, 0.5), (4.5, 0.5), (5.0, 2.0)],
    [(0.5, 0.5), (1.0, 1.0), (2.0, 0.5), (2.5, 0.5), (3.0, 1.5), (4.5, 1.0), (6.0, 0.5), (6.5, 1.0)],
]


def sf2():
    for p in SF2_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError("找不到 GM 音色库：sudo apt install fluid-soundfont-gm")


class Composer:
    def __init__(self, duration, unit, num):
        self.rng = random.Random(1000 * unit + num)
        key, bpm = STYLE.get(unit, (0, 92))
        r = self.rng
        self.key = key
        self.bpm = bpm + r.choice([-3, -2, 0, 0, 2, 3])
        self.beat = 60.0 / self.bpm
        self.bar = 4 * self.beat
        self.nbars = int((duration + 1.0) / self.bar) + 1
        self.events = {ch: [] for ch in (CH_KEYS, CH_BASS, CH_LEAD, CH_PAD, CH_DRUM)}
        progs = r.sample(range(len(PROGS)), 3)
        self.progA, self.progB, self.progK = (PROGS[i] for i in progs)
        self.keys_prog = r.choice(KEYS)
        self.lead_prog = r.choice(LEADS)
        self.kit = r.choice(KITS)
        self.prev_voicing = None
        self.prev_lead = 71

    # -------------------------------------------------------------- 工具
    def note(self, ch, beat, dur, pitch, vel, human=True):
        r = self.rng
        if human:
            beat += r.uniform(-0.018, 0.018)
            vel += r.randint(-6, 6)
        vel = max(1, min(127, int(vel)))
        t0 = max(0, int(round(beat * TPB)))
        t1 = max(t0 + 10, int(round((beat + dur) * TPB)))
        self.events[ch].append((t0, 1, pitch, vel))
        self.events[ch].append((t1, 0, pitch, 0))

    @staticmethod
    def swing(b):
        """八分音符的反拍往后推一点（轻摇摆）。"""
        frac = b - int(b)
        if abs(frac - 0.5) < 1e-6:
            return b + 0.07
        return b

    def chord_root(self, deg):
        return (self.key + MAJOR[deg - 1]) % 12

    def voicing(self, deg, qual):
        """和弦的排法：去掉根音（贝斯会弹），其余音放在中音区，并和上一个和弦尽量靠近。"""
        root = self.chord_root(deg)
        ivs = [i for i in QUAL[qual] if i % 12 != 0] or QUAL[qual]
        pcs = [(root + i) % 12 for i in ivs][:4]
        best, best_cost = None, None
        for rot in range(len(pcs)):
            order = pcs[rot:] + pcs[:rot]
            for base in range(50, 62):
                v, cur = [], base - 1
                for pc in order:
                    n = cur + 1
                    while n % 12 != pc:
                        n += 1
                    v.append(n)
                    cur = n
                if v[0] != base or v[-1] > 79:
                    continue
                center = sum(v) / len(v)
                cost = abs(center - 63)
                if self.prev_voicing:
                    cost = 0.4 * cost + sum(min(abs(a - b) for b in self.prev_voicing) for a in v) / len(v)
                if best_cost is None or cost < best_cost:
                    best, best_cost = v, cost
        self.prev_voicing = best
        return best

    def chord_pcs(self, deg, qual):
        root = self.chord_root(deg)
        return [(root + i) % 12 for i in QUAL[qual]]

    # -------------------------------------------------------------- 各声部
    def keys_bar(self, b0, deg, qual, style, vel=72):
        v = self.voicing(deg, qual)
        if style == "roll":                       # 分解的长和弦（前奏、间奏、尾声）
            for i, p in enumerate(v):
                self.note(CH_KEYS, b0 + 0.04 * i, 3.8 - 0.04 * i, p, vel * 0.85)
            return
        pat = COMP[style]
        for st, du, k in pat:
            for i, p in enumerate(v):
                self.note(CH_KEYS, self.swing(b0 + st) + 0.012 * i, du, p, vel * k)

    def bass_bar(self, b0, deg, qual, nxt_deg, busy=True, vel=88):
        r = self.rng
        root = 36 + (self.chord_root(deg) - 36) % 12
        if root > 45:
            root -= 12
        fifth = root + 7
        third = root + QUAL[qual][1]
        nroot = 36 + (self.chord_root(nxt_deg) - 36) % 12
        if nroot > 45:
            nroot -= 12
        if not busy:
            self.note(CH_BASS, b0, 1.8, root, vel * 0.9)
            self.note(CH_BASS, b0 + 2.5, 1.3, fifth if r.random() < 0.6 else root + 12, vel * 0.75)
            return
        pat = r.choice([
            [(0, 1.3, root, 1.0), (1.5, 0.4, root, 0.7), (2.0, 0.9, fifth, 0.85), (3.0, 0.45, third, 0.75),
             (3.5, 0.45, nroot + (1 if nroot < root else -1), 0.72)],
            [(0, 0.9, root, 1.0), (1.0, 0.45, root + 12, 0.7), (1.5, 0.9, fifth, 0.8), (2.5, 0.45, root, 0.75),
             (3.0, 0.9, fifth if r.random() < 0.5 else third, 0.8)],
            [(0, 1.9, root, 1.0), (2.5, 0.45, root, 0.7), (3.0, 0.45, fifth, 0.8), (3.5, 0.45, root + 12, 0.7)],
        ])
        for st, du, p, k in pat:
            self.note(CH_BASS, self.swing(b0 + st), du, p, vel * k)

    def pad_bar(self, b0, deg, qual, vel=46):
        root = self.chord_root(deg)
        ivs = QUAL[qual]
        for iv in (ivs[1], ivs[3] if len(ivs) > 3 else ivs[2]):
            p = 60 + (root + iv - 60) % 12
            self.note(CH_PAD, b0, 4.0, p, vel, human=False)

    def drums_bar(self, b0, kind, fill=False, crash=False, vel=1.0):
        r = self.rng
        n = lambda beat, p, v: self.note(CH_DRUM, beat, 0.25, p, v * vel)   # noqa: E731
        if kind == "none":
            return
        if kind == "shaker":
            for i in range(8):
                n(self.swing(b0 + i * 0.5), 70, 42 if i % 2 == 0 else 30)
            return
        light = kind == "light"
        # 底鼓
        n(b0, 36, 92)
        if r.random() < 0.6:
            n(b0 + 1.75, 36, 52)
        n(self.swing(b0 + 2.5), 36, 78)
        # 军鼓（轻的段落用边击）
        sn = 37 if light else 38
        n(b0 + 1, sn, 62 if light else 74)
        n(b0 + 3, sn, 64 if light else 78)
        if not light and r.random() < 0.5:
            n(b0 + 2.75, 38, 26)
        # 踩镲：八分音符，轻重交替
        for i in range(8):
            if fill and i >= 6:
                break
            v = 58 if i % 2 == 0 else 40
            n(self.swing(b0 + i * 0.5), 42, v * (0.8 if light else 1.0))
        if not light and r.random() < 0.4:
            n(self.swing(b0 + 3.5), 46, 46)
        if fill:
            for i, p in enumerate((38, 38, 47, 45)):
                n(b0 + 3 + 0.25 * i, p, 40 + 10 * i)
        if crash:
            n(b0, 49, 62)

    def lead_phrase(self, b0, prog, bars=8, vel=72):
        """8 小节的旋律：动机 → 变化 → 动机 → 收束。强拍落在和弦音上，其余在五声音阶上小步走。"""
        r = self.rng
        scale = sorted({(self.key + p) % 12 for p in PENTA})
        pool = [p for p in range(62, 86) if p % 12 in scale]
        motif = r.choice(RHYTHMS)
        motif2 = r.choice(RHYTHMS)
        plan = [motif, motif2, motif, None]
        for k, rh in enumerate(plan):
            base = b0 + k * 8
            if k * 2 >= bars:
                break
            if rh is None:                        # 收束：两三个音落到主和弦音上
                deg, qual = prog[(k * 2) % len(prog)]
                pcs = self.chord_pcs(deg, qual)
                tgt = min((p for p in pool if p % 12 in pcs), key=lambda p: abs(p - self.prev_lead))
                self.note(CH_LEAD, self.swing(base + 0.5), 0.5, self._step(pool, tgt, 1), vel * 0.85)
                self.note(CH_LEAD, base + 1.0, 2.6, tgt, vel)
                self.prev_lead = tgt
                continue
            cur = self.prev_lead
            for st, du in rh:
                bar_i = (k * 2 + int(st // 4)) % len(prog)
                deg, qual = prog[bar_i]
                pcs = self.chord_pcs(deg, qual)
                strong = (st % 2) == 0
                if strong:
                    cands = [p for p in pool if p % 12 in pcs and abs(p - cur) <= 5] or \
                            [min(pool, key=lambda p: abs(p - cur))]
                    nxt = r.choice(cands)
                else:
                    nxt = self._step(pool, cur, r.choice([-2, -1, -1, 1, 1, 2]))
                if nxt > 81:
                    nxt = self._step(pool, nxt, -3)
                if nxt < 65:
                    nxt = self._step(pool, nxt, 3)
                self.note(CH_LEAD, self.swing(base + st), du * 0.95, nxt, vel * (1.0 if strong else 0.86))
                cur = nxt
            self.prev_lead = cur

    @staticmethod
    def _step(pool, p, k):
        i = min(range(len(pool)), key=lambda j: abs(pool[j] - p))
        return pool[max(0, min(len(pool) - 1, i + k))]

    # -------------------------------------------------------------- 编排
    def arrange(self):
        r = self.rng
        bar = 0
        # 前奏 4 小节：分解和弦 + 铺底，后两小节进轻鼓
        prog = self.progA
        for i in range(4):
            deg, qual = prog[i % 4]
            self.keys_bar(bar * 4, deg, qual, "roll", 66)
            self.pad_bar(bar * 4, deg, qual)
            if i >= 2:
                self.drums_bar(bar * 4, "light", fill=(i == 3), vel=0.85)
                self.bass_bar(bar * 4, deg, qual, prog[(i + 1) % 4][0], busy=False)
            bar += 1
        cycle = ["A", "B", "A2", "B", "K", "A", "B2", "K"]
        ci = 0
        outro = 4
        while bar < self.nbars - outro:
            sec = cycle[ci % len(cycle)]
            ci += 1
            n = min(8, self.nbars - outro - bar)
            prog = self.progB if sec.startswith("B") else self.progK if sec == "K" else self.progA
            comp = r.randrange(len(COMP))
            for i in range(n):
                b0 = (bar + i) * 4
                deg, qual = prog[i % 4]
                nxt = prog[(i + 1) % 4][0]
                last = i == n - 1
                if sec == "K":                         # 间奏：没有鼓，分解和弦 + 铺底 + 旋律
                    self.keys_bar(b0, deg, qual, "roll" if i % 2 == 0 else comp, 64)
                    self.pad_bar(b0, deg, qual, 50)
                    self.bass_bar(b0, deg, qual, nxt, busy=False, vel=78)
                    self.drums_bar(b0, "shaker" if i >= 4 else "none")
                else:
                    self.keys_bar(b0, deg, qual, comp, 74 if sec != "A" else 70)
                    self.bass_bar(b0, deg, qual, nxt, busy=True)
                    self.drums_bar(b0, "light" if sec == "A" else "full", fill=last, crash=(i == 0 and sec != "A"))
                    if sec.startswith("B"):
                        self.pad_bar(b0, deg, qual, 40)
            if sec in ("B", "B2", "K") or (sec == "A2" and r.random() < 0.5):
                self.lead_phrase(bar * 4, prog, bars=n, vel=70 if sec != "K" else 62)
            bar += n
        # 尾声：主和弦长音
        for i in range(outro + 2):            # 尾声多留两小节，保证主和弦一直响到淡出结束
            b0 = bar * 4
            if i % 2 == 0:
                self.keys_bar(b0, 1, "M9", "roll", 64 - 6 * i)
                self.pad_bar(b0, 1, "M9", 44)
                self.pad_bar(b0 + 4, 1, "M9", 40)
                self.bass_bar(b0, 1, "M9", 1, busy=False, vel=70 - 5 * i)
            bar += 1

    # -------------------------------------------------------------- 输出
    def midi(self, path):
        mf = mido.MidiFile(type=1, ticks_per_beat=TPB)
        meta = mido.MidiTrack()
        meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm), time=0))
        mf.tracks.append(meta)
        setup = {
            CH_KEYS: (self.keys_prog, 92, 52, 58, 40),
            CH_BASS: (BASS, 100, 64, 8, 0),
            CH_LEAD: (self.lead_prog, 84, 76, 72, 20),
            CH_PAD: (PAD, 52, 64, 90, 30),
            CH_DRUM: (self.kit, 84, 64, 28, 0),
        }
        for ch, evs in self.events.items():
            tr = mido.MidiTrack()
            prog, vol, pan, rev, cho = setup[ch]
            tr.append(mido.Message("program_change", channel=ch, program=prog, time=0))
            for cc, v in ((7, vol), (10, pan), (91, rev), (93, cho)):
                tr.append(mido.Message("control_change", channel=ch, control=cc, value=v, time=0))
            last = 0
            for t, on, p, v in sorted(evs, key=lambda e: (e[0], e[1])):
                kind = "note_on" if on else "note_off"
                tr.append(mido.Message(kind, channel=ch, note=p, velocity=v, time=t - last))
                last = t
            mf.tracks.append(tr)
        mf.save(str(path))


def render(path, duration, unit, num):
    """生成并渲染一集的背景音乐，写成 44.1kHz 立体声 WAV。"""
    path = Path(path)
    c = Composer(duration, unit, num)
    c.arrange()
    with tempfile.TemporaryDirectory() as d:
        mid = Path(d) / "m.mid"
        raw = Path(d) / "raw.wav"
        c.midi(mid)
        subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.45", "-r", str(SR), "-F", str(raw),
                        "-o", "synth.reverb.room-size=0.62", "-o", "synth.reverb.damp=0.35",
                        "-o", "synth.reverb.width=0.9", "-o", "synth.reverb.level=0.55",
                        "-o", "synth.chorus.level=1.2", sf2(), str(mid)],
                       check=True, capture_output=True)
        fade = max(0.0, duration - 4.0)
        pre = f"apad=whole_dur={duration:.2f},highpass=f=35,lowpass=f=11500,atrim=0:{duration:.2f}"
        # 两遍 loudnorm：先测响度，再线性地调到 −19 LUFS（不会忽大忽小）
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af",
                            pre + ",loudnorm=I=-19:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True)
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        ln = (f"loudnorm=I=-19:TP=-2:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
              f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
        af = f"{pre},{ln},afade=t=in:d=1.5,afade=t=out:st={fade:.2f}:d=4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, "-ar", str(SR), "-ac", "2",
                        str(path)], check=True)
    return path
