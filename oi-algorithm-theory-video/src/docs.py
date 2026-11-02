"""根据 catalog.py 和 videos/ 里实际存在的成片，重写 README.md 的课程导航和 PROGRESS.md 的进度表。

python docs.py
README.md / PROGRESS.md 里 <!-- 导航开始 --> … <!-- 导航结束 -->、<!-- 进度开始 --> … <!-- 进度结束 --> 之间的内容会被替换，
其余部分是手写的，不会动。
"""

import json
import subprocess
import urllib.parse
from pathlib import Path

import catalog

ROOT = Path(__file__).resolve().parent
TOP = ROOT.parent


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def fmt(t):
    t = int(round(t))
    return f"{t // 60}:{t % 60:02d}"


def link(path, text):
    rel = path.relative_to(TOP).as_posix()
    return f"[{text}]({urllib.parse.quote(rel)})"


def video_of(ep):
    from build import video_path
    return video_path(ep)


def transcript_of(ep):
    return TOP / "transcripts" / (video_of(ep).stem + ".md")


def status():
    rows = []
    for ep in catalog.EPISODES:
        v = video_of(ep)
        done = v.exists()
        rows.append((ep, v, done, duration(v) if done else None))
    return rows


def nav(rows):
    out = []
    unit = None
    for ep, v, done, d in rows:
        if ep["unit"] != unit:
            unit = ep["unit"]
            out += ["", f"### {catalog.UNITS[unit]}", "",
                    "| 集 | 标题 | 先修 | 讲什么 | 成片 | 文字稿 |", "|---|---|---|---|---|---|"]
        pre = "、".join(str(p) for p in ep["pre"]) or "—"
        title = f"**{ep['title']}**<br>{ep['subtitle']}"
        if done:
            vid = link(v, f"▶ {fmt(d)}")
            tr = link(transcript_of(ep), "文字稿") if transcript_of(ep).exists() else "—"
        else:
            vid, tr = "未制作", "—"
        out.append(f"| {ep['num']} | {title} | {pre} | {ep['about']} | {vid} | {tr} |")
    return "\n".join(out).strip()


def progress(rows):
    done = [r for r in rows if r[2]]
    total = sum(r[3] for r in done)
    lines = [f"已完成 **{len(done)} / {len(rows)}** 集，成片合计 {fmt(total)}（约 {total / 60:.0f} 分钟）。", "",
             "| 集 | 单元 | 标题 | 状态 | 时长 | 大小 |", "|---|---|---|---|---|---|"]
    for ep, v, ok, d in rows:
        u = catalog.UNITS[ep["unit"]].split(" ")[0]
        if ok:
            lines.append(f"| {ep['num']} | {u} | {ep['title']} | ✅ 已完成 | {fmt(d)} | {v.stat().st_size / 1e6:.1f} MB |")
        elif ep.get("module") and (ROOT / "episodes" / f"{ep['module']}.py").exists():
            lines.append(f"| {ep['num']} | {u} | {ep['title']} | 🟡 脚本已写，未渲染 | — | — |")
        else:
            lines.append(f"| {ep['num']} | {u} | {ep['title']} | ⬜ 未制作 | — | — |")
    return "\n".join(lines)


def replace(path, start, end, body):
    s = path.read_text(encoding="utf-8")
    a = s.index(start) + len(start)
    b = s.index(end)
    path.write_text(s[:a] + "\n\n" + body + "\n\n" + s[b:], encoding="utf-8")


def main():
    rows = status()
    replace(TOP / "README.md", "<!-- 导航开始 -->", "<!-- 导航结束 -->", nav(rows))
    replace(TOP / "PROGRESS.md", "<!-- 进度开始 -->", "<!-- 进度结束 -->", progress(rows))
    print("已更新 README.md 和 PROGRESS.md")


if __name__ == "__main__":
    main()
