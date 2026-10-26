"""根据每句旁白的实际时长排出整条时间线：场景起止、每句话的起止。画面和配乐都按它对齐。"""

import json

from narration import SCENES

FPS = 30


def build(durations):
    """durations[i][j]：第 i 个场景第 j 句话的秒数。"""
    t = 0.0
    scenes = []
    for scene, durs in zip(SCENES, durations):
        start = t
        t += scene["lead"]
        lines = []
        for line, d in zip(scene["lines"], durs):
            lines.append({"start": round(t, 3), "end": round(t + d, 3), "sub": line["sub"],
                          "quote": bool(line.get("quote"))})
            t += d + line["gap"]
        t += scene["tail"]
        scenes.append({"id": scene["id"], "start": round(start, 3), "end": round(t, 3), "lines": lines})
    return {"fps": FPS, "duration": round(t, 3), "scenes": scenes}


def save(tl, path):
    path.write_text(json.dumps(tl, ensure_ascii=False, indent=1))


def load(path):
    return json.loads(path.read_text())
