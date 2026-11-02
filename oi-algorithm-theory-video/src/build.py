"""渲染：python build.py 1 2 3（按集号）/ python build.py all / python build.py 1 --stills

每一集：搭时间线 → 合成背景音乐 → 逐帧绘制并交给 ffmpeg 编码 → 写文字稿。
成片放在 ../videos/，文字稿放在 ../transcripts/，中间文件（音频、静帧）在 build/ 下，不提交。
"""

import argparse
import importlib
import json
import multiprocessing as mp
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import catalog  # noqa: E402
from engine import theme  # noqa: E402
from engine.scene import Scene  # noqa: E402
from engine.core import Renderer  # noqa: E402

VIDEOS = ROOT.parent / "videos"
TRANSCRIPTS = ROOT.parent / "transcripts"
BUILD = ROOT / "build"


def make_scene(ep):
    meta = dict(ep)
    meta["unit_name"] = catalog.UNITS[ep["unit"]]
    S = Scene(meta)
    mod = importlib.import_module(f"episodes.{ep['module']}")
    mod.build(S)
    S.finish()
    return S


def video_path(ep):
    unit_dir = VIDEOS / f"{ep['unit']}-{catalog.UNITS[ep['unit']].split(' ')[-1]}"
    return unit_dir / catalog.filename(ep)


def transcript(S, ep, path):
    lines = [f"# 第 {ep['num']} 集　{ep['title']}", ""]
    if ep.get("subtitle"):
        lines += [f"**{ep['subtitle']}**", ""]
    lines += [f"> {catalog.UNITS[ep['unit']]}　·　时长 {fmt_time(S.t)}　·　视频：`{video_path(ep).relative_to(ROOT.parent)}`",
              "", "这是视频里全部讲解文字和板书的文字稿（按出现顺序），方便复习和检索。", ""]
    events = [(t, "cap", s, sec) for t, _, s, sec in S.captions] + [(t, "note", s, sec) for t, s, sec in S.note_log]
    events.sort(key=lambda e: (e[0], e[1] != "note"))
    cur = None
    for t, kind, s, sec in events:
        if sec != cur:
            lines += ["", f"## {sec}", ""]
            cur = sec
        s = strip_markup(s)
        if kind == "cap":
            lines.append(f"- `{fmt_time(t)}` {s}")
        else:
            lines.append(f"  - 板书：{s}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def strip_markup(s):
    from engine.text import parse
    return "".join(x[0] for x in parse(s, None)).replace("\n", " ")


def fmt_time(t):
    t = int(round(t))
    return f"{t // 60}:{t % 60:02d}"


def lint(S):
    """在每句讲解结束前检查：可见文字互相重叠、超出画面。"""
    from engine.widgets import Text
    issues = []
    nodes = []
    for layer in (S.objs, S.under):
        for top in layer:
            for n in top.walk():
                if isinstance(n, Text):
                    nodes.append(n)
    for t in S.checks:
        boxes = []
        for n in nodes:
            if not n.visible(t):
                continue
            bb = n.bbox(t)
            if bb is None:
                continue
            x, y = n.abs_xy(t)
            s = n.abs_scale(t)
            box = (x + bb[0] * s, y + bb[1] * s, x + bb[2] * s, y + bb[3] * s)
            boxes.append((box, n))
            if box[0] < 0 or box[2] > theme.W or box[1] < theme.HEADER_H or box[3] > theme.CAPTION[1] - 8:
                issues.append(f"t={t:.1f} 越界：{strip_markup(n.g('text', t))[:30]} {tuple(int(v) for v in box)}")
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, na = boxes[i]
                b, nb = boxes[j]
                ox = min(a[2], b[2]) - max(a[0], b[0])
                oy = min(a[3], b[3]) - max(a[1], b[1])
                if ox > 4 and oy > 4:
                    issues.append(f"t={t:.1f} 重叠：「{strip_markup(na.g('text', t))[:20]}」与「{strip_markup(nb.g('text', t))[:20]}」")
    seen = set()
    out = []
    for s in issues:
        k = s.split(" ", 1)[1]
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def build_one(num, stills=False, still_times=None, crf=30, preset="medium", only_lint=False):
    ep = catalog.get(num)
    t0 = time.time()
    S = make_scene(ep)
    print(f"[{ep['num']:02d}] {ep['title']}：时长 {fmt_time(S.t)}，{len(S.captions)} 句讲解")
    issues = lint(S)
    for s in issues[:40]:
        print(f"  [检查] {s}")
    if only_lint:
        if only_lint == "times":
            for t, name in S.sections:
                print(f"  {t:7.1f}s  == {name}")
            for c in S.captions:
                print(f"  {c[0]:7.1f}s  {strip_markup(c[2])[:40]}")
        return num, S.t, len(issues)
    if stills or still_times:
        d = BUILD / "stills" / f"{num:02d}"
        d.mkdir(parents=True, exist_ok=True)
        R = Renderer(S)
        times = still_times or [c[1] - 0.1 for c in S.captions if c[1]]
        for i, t in enumerate(times):
            R.still(t, d / f"{i:03d}_{t:07.1f}.png")
        print(f"  静帧写到 {d}")
        return num, S.t, len(issues)
    from engine import music
    adir = BUILD / "audio"
    adir.mkdir(parents=True, exist_ok=True)
    wav = adir / f"{num:02d}.wav"
    music.write_wav(wav, music.compose(S.t + 0.5, ep["unit"], ep["num"]))
    out = video_path(ep)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part.mp4")
    R = Renderer(S)
    drawn, total = R.encode(tmp, crf=crf, audio=wav, preset=preset, log=f"{num:02d}")
    tmp.rename(out)
    transcript(S, ep, TRANSCRIPTS / f"{out.stem}.md")
    info = {"num": num, "duration": round(S.t, 2), "captions": len(S.captions), "frames": total, "drawn": drawn,
            "sections": [s for _, s in S.sections], "size": out.stat().st_size}
    (BUILD / "info").mkdir(exist_ok=True)
    (BUILD / "info" / f"{num:02d}.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(f"[{num:02d}] 完成：{out.name}，{fmt_time(S.t)}，{out.stat().st_size / 1e6:.1f} MB，"
          f"绘制 {drawn}/{total} 帧，用时 {time.time() - t0:.0f}s")
    return num, S.t, len(issues)


def _job(args):
    return build_one(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eps", nargs="+")
    ap.add_argument("--stills", action="store_true", help="只渲染每句讲解结束时的静帧")
    ap.add_argument("--at", default=None, help="只渲染这些时刻的静帧，逗号分隔")
    ap.add_argument("--lint", action="store_true", help="只检查版面")
    ap.add_argument("--times", action="store_true", help="列出各小节和每句讲解的开始时刻")
    ap.add_argument("-j", type=int, default=1)
    ap.add_argument("--crf", type=int, default=30)
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args()
    if a.eps == ["all"]:
        nums = [e["num"] for e in catalog.EPISODES
                if e.get("module") and (ROOT / "episodes" / f"{e['module']}.py").exists()]
    else:
        nums = []
        for s in a.eps:
            if "-" in s:
                x, y = map(int, s.split("-"))
                nums += list(range(x, y + 1))
            else:
                nums.append(int(s))
    at = [float(x) for x in a.at.split(",")] if a.at else None
    jobs = [(n, a.stills, at, a.crf, a.preset, "times" if a.times else a.lint) for n in nums]
    if a.j > 1 and len(jobs) > 1:
        with mp.Pool(a.j) as pool:
            for r in pool.imap_unordered(_job, jobs):
                pass
    else:
        for j in jobs:
            _job(j)


if __name__ == "__main__":
    main()
