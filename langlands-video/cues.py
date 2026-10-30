"""画面事件和音效共用的时间表：同一个时刻，画面上发生什么、音轨里就响什么。

所有时间都从时间线（每句旁白的起止）推出来，改了旁白、重新合成语音后自动对齐。
"""

from collections import defaultdict

DATE_TEXT = "JANUARY 1967"
EX_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
GRID_PRIMES = [2, 3, 5, 7, 11, 13]

MILESTONES = [
    # 年份, 标题, 说明, 徽章
    ("1967", "朗兰兹致信韦伊", "纲领诞生", ""),
    ("1990", "德林费尔德", "函数域上 GL(2) 的朗兰兹对应", "FIELDS MEDAL"),
    ("1994", "怀尔斯", "半稳定椭圆曲线的模性 · 费马大定理", ""),
    ("2002", "洛朗·拉福格", "函数域上 GL(n) 的朗兰兹对应", "FIELDS MEDAL"),
    ("2010", "吴宝珠", "证明基本引理", "FIELDS MEDAL"),
    ("2018", "罗伯特·朗兰兹", "阿贝尔奖", "ABEL PRIZE"),
    ("2024", "盖茨戈里、拉斯金等九位数学家", "证明几何朗兰兹猜想 · 近千页", ""),
]


class Timeline:
    def __init__(self, data):
        self.data = data
        self.duration = data["duration"]
        self.fps = data["fps"]
        self.scenes = data["scenes"]
        self.by_id = {s["id"]: s for s in self.scenes}

    def scene(self, sid):
        return self.by_id[sid]

    def line(self, sid, i):
        return self.by_id[sid]["lines"][i]

    def scene_at(self, t):
        for s in self.scenes:
            if t < s["end"]:
                return s
        return self.scenes[-1]


def title_reveal(tl):
    return tl.scene("title")["start"] + 1.0


def end_reveal(tl):
    s = tl.scene("end")
    return s["start"] + 0.8


def example_schedule(tl):
    L = tl.scene("example")["lines"]
    g0 = L[2]["start"] + 0.2
    g1 = L[3]["start"] - 0.5
    dt = (g1 - g0) / len(GRID_PRIMES)
    grids = [(p, g0 + k * dt, g0 + (k + 1) * dt) for k, p in enumerate(GRID_PRIMES)]
    n_reveal = [g0 + (k + 0.85) * dt for k in range(len(GRID_PRIMES))]
    n_reveal += [g1 + 0.05 + k * 0.14 for k in range(len(EX_PRIMES) - len(GRID_PRIMES))]
    a_reveal = [L[4]["start"] + 0.35 + k * 0.24 for k in range(len(EX_PRIMES))]
    match = [L[6]["start"] + 0.12 + k * 0.42 for k in range(6)]
    match += [L[6]["start"] + 2.85 + k * 0.16 for k in range(len(EX_PRIMES) - 6)]
    return {
        "curve": (L[1]["start"], L[1]["start"] + 3.2),
        "grids": grids,
        "n_reveal": n_reveal,
        "product": L[3]["start"] + 1.5,
        "series": (L[4]["start"], L[4]["end"] + 0.4),
        "a_reveal": a_reveal,
        "diff_row": L[5]["start"] + 0.3,
        "match": match,
        "scan": (L[7]["start"], L[7]["end"] + 0.4),
        "split": L[8]["start"],
    }


def fermat_schedule(tl):
    L = tl.scene("fermat")["lines"]
    return {
        "wiles": L[1]["start"],
        "fermat": L[2]["start"] - 0.1,
        "qed": L[2]["start"] + 0.72 * (L[2]["end"] - L[2]["start"]),
        "iceberg": L[3]["start"],
    }


def program_schedule(tl):
    L = tl.scene("program")["lines"]
    return {
        "columns": L[1]["start"],
        "dictionary": L[2]["start"],
        "lfunc": L[3]["start"] + 0.25,
        "functor": L[4]["start"],
        "bridges": [L[4]["start"] + 2.6 + k * 0.75 for k in range(7)],
    }


def history_schedule(tl):
    L = tl.scene("history")["lines"]
    s = tl.scene("history")
    focus = [s["start"] + 0.2,
             L[1]["start"] + 0.2, L[1]["start"] + 1.5, L[1]["start"] + 2.8,
             L[1]["start"] + 4.1, L[1]["start"] + 5.6,
             L[2]["start"] + 0.2]
    return {"focus": focus, "physics": L[3]["start"] - 0.2}


def finale_schedule(tl):
    L = tl.scene("finale")["lines"]
    d0 = L[0]["end"] - L[0]["start"]
    return {
        "words": [L[0]["start"] + k * d0 * 0.24 for k in range(4)],
        "converge": (L[1]["start"], L[1]["start"] + 2.2),
        "letter": L[2]["start"] - 0.2,
        "rise": L[3]["start"],
        "decode": L[4]["start"],
    }


def sound_events(tl):
    ev = defaultdict(list)
    le = tl.scene("letter")
    for i, ch in enumerate(DATE_TEXT):
        if ch != " ":
            ev["type"].append(le["start"] + 0.3 + i / 12)
    ev["glitch"].append(tl.line("letter", 3)["start"])
    r = title_reveal(tl)
    ev["riser"].append((r, 5.0))
    ev["impact"].append((r, 1.0))
    for sid in ["worlds", "example", "fermat", "program", "history", "finale"]:
        ev["whoosh"].append(tl.scene(sid)["start"] + 0.05)

    ex = example_schedule(tl)
    for t in ex["n_reveal"]:
        ev["blip"].append((t, 1320))
    for t in ex["a_reveal"]:
        ev["blip"].append((t, 1760))
    for t in ex["match"]:
        ev["ding"].append(t)
    t0, t1 = ex["scan"]
    k = 0
    while t0 + k * 0.045 < t1:
        ev["tick"].append(t0 + k * 0.045)
        k += 1
    ev["ding"].append(t1 - 0.1)
    for p, g0, g1 in ex["grids"]:
        ev["glitch_soft"].append(g0)

    fe = fermat_schedule(tl)
    ev["hit"].append((fe["wiles"], 0.6))
    ev["impact"].append((fe["qed"], 0.9))
    ev["sub_drop"].append(fe["iceberg"])

    pr = program_schedule(tl)
    ev["hit"].append((pr["columns"], 0.5))
    ev["impact"].append((pr["lfunc"], 0.7))
    for t in pr["bridges"]:
        ev["ding"].append(t)

    hi = history_schedule(tl)
    for t in hi["focus"]:
        ev["hit"].append((t, 0.55))
    ev["whoosh"].append(hi["physics"])

    fi = finale_schedule(tl)
    for t in fi["words"]:
        ev["hit"].append((t, 0.35))
    ev["impact"].append((fi["converge"][1], 0.6))
    ev["glitch"].append(fi["decode"])
    ev["riser"].append((end_reveal(tl), 3.0))
    ev["impact"].append((end_reveal(tl), 1.0))
    return ev


def glitch_times(tl):
    """画面上做色差、错位故障效果的时刻（和音效里的 glitch 对齐）。"""
    ev = sound_events(tl)
    return sorted(ev["glitch"] + [t for t, _ in ev["impact"]] + ev["whoosh"])
