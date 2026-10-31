"""把各章的场景按顺序排起来，算出每个场景的起止时刻。"""

import s0_open
import s1_charfun
import s2_convolution
import s3_clt
import s4_series
import s5_heat
import s6_viete
import s7_uncertainty
import s8_finale

FPS = 30

ORDER = [s0_open, s1_charfun, s2_convolution, s3_clt, s4_series, s5_heat, s6_viete, s7_uncertainty, s8_finale]


class Timeline:
    def __init__(self, scenes):
        self.scenes = scenes
        t = 0.0
        for s in scenes:
            s.start = t
            t += s.dur
        self.duration = t

    def at(self, t):
        for s in self.scenes:
            if t < s.start + s.dur:
                return s, t - s.start
        s = self.scenes[-1]
        return s, s.dur - 1e-6

    def glitch_times(self):
        out = []
        for s in self.scenes:
            for tt, kind, *rest in s.sfx:
                if kind in ("impact", "glitch"):
                    out.append((s.start + tt, 1.0 if kind == "impact" else 0.7))
        return out

    def all_sfx(self):
        """全片的音效提示：[(绝对时刻, 种类, 参数)]。每条说明文字出现时自动加一声轻响。"""
        out = []
        for s in self.scenes:
            for tt, kind, *rest in s.sfx:
                out.append((s.start + tt, kind, rest[0] if rest else {}))
            for t0, t1, _ in s.caps:
                out.append((s.start + t0, "cap", {}))
        return sorted(out, key=lambda e: e[0])


def _scenes():
    out = []
    for m in ORDER:
        out.extend(m.SCENES)
    return out


TIMELINE = Timeline(_scenes())
