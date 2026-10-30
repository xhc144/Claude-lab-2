# -*- coding: utf-8 -*-
"""一键生成：并行渲染全部场景 → 配乐 → 拼接、背景辉光、章节标记 → 成片。

用法：
  python build.py render [-ql|-qh] [场景名 ...]   # 渲染（默认 1080p60，-ql 为 480p15 预览）
  python build.py music  [-ql]                     # 只重新合成配乐
  python build.py final  [-ql]                     # 拼接、混音、编码，输出成片
  python build.py all    [-ql]                     # 以上全部
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
MANIM = os.path.join(os.path.dirname(sys.executable), "manim")

ORDER = [
    ("intro.py", "Intro"),
    ("ch1.py", "Card1"), ("ch1.py", "AreaAlgebra"), ("ch1.py", "Rules"), ("ch1.py", "KVectors"),
    ("ch1.py", "Basis"), ("ch1.py", "FirstCompute"),
    ("ch2.py", "Card2"), ("ch2.py", "VolumeFactor"), ("ch2.py", "Leibniz"), ("ch2.py", "Properties"),
    ("ch2.py", "Cramer"), ("ch2.py", "Laplace"),
    ("ch3.py", "Card3"), ("ch3.py", "Compound"), ("ch3.py", "CauchyBinet"), ("ch3.py", "Pythagoras"),
    ("ch3.py", "CharPoly"), ("ch3.py", "Sylvester"), ("ch3.py", "PluckerAlg"), ("ch3.py", "PluckerLines"),
    ("ch3.py", "Forms"),
    ("outro.py", "Outro"),
]
# 视频里的章节标记（播放器里可以按章节跳转）
MARKS = {
    "Intro": "开场", "Card1": "第一章 什么是外代数", "AreaAlgebra": "1.1 面积的代数", "Rules": "1.2 三条规则",
    "KVectors": "1.3 k-向量", "Basis": "1.4 基底、维数与符号", "FirstCompute": "1.5 行列式自己跳出来",
    "Card2": "第二章 行列式从哪里来", "VolumeFactor": "2.1 体积的伸缩倍数", "Leibniz": "2.2 莱布尼茨公式",
    "Properties": "2.3 行列式的性质", "Cramer": "2.4 克莱默法则", "Laplace": "2.5 拉普拉斯展开",
    "Card3": "第三章 一行证明的定理们", "Compound": "3.1 子式矩阵", "CauchyBinet": "3.2 柯西–比内公式",
    "Pythagoras": "3.3 面积的勾股定理", "CharPoly": "3.4 特征多项式", "Sylvester": "3.5 西尔维斯特恒等式",
    "PluckerAlg": "3.6 普吕克关系", "PluckerLines": "3.7 空间直线", "Forms": "3.8 微分形式与斯托克斯",
    "Outro": "尾声",
}
# 成片按章分成三集（每集一个文件，都在 50 MB 以内）
PARTS = [
    ("外代数（上）什么是外代数", "Intro", "FirstCompute"),
    ("外代数（中）行列式从哪里来", "Card2", "Laplace"),
    ("外代数（下）一行证明的定理们", "Card3", "Outro"),
]
OUT = ROOT
HEAVY = {"KVectors", "Pythagoras", "PluckerLines", "Leibniz", "Outro", "Intro"}

QUALITY = {"-qh": ("1920,1080", 60, "1080p60"), "-ql": ("854,480", 15, "480p15")}


def video_path(f, cls, q):
    return os.path.join(BUILD, "media", "videos", os.path.splitext(f)[0], QUALITY[q][2], f"{cls}.mp4")


def render_one(job, q):
    f, cls = job
    res, fps, _ = QUALITY[q]
    args = [MANIM, "-r", res, "--fps", str(fps), "--disable_caching", "--progress_bar", "none",
            "--media_dir", os.path.join(BUILD, "media"), f, cls]
    os.makedirs(os.path.join(BUILD, "logs"), exist_ok=True)
    env = dict(os.environ, EA_JOB=cls)
    for attempt in range(3):
        with open(os.path.join(BUILD, "logs", f"{cls}.log"), "w") as lg:
            r = subprocess.run(args, cwd=HERE, stdout=lg, stderr=subprocess.STDOUT, env=env)
        if r.returncode == 0:
            print(f"  ✓ {cls}", flush=True)
            return True
        print(f"  ✗ {cls}（第 {attempt + 1} 次）", flush=True)
    return False


def render(q, only=None, workers=4):
    jobs = [j for j in ORDER if not only or j[1] in only]
    jobs.sort(key=lambda j: j[1] not in HEAVY)
    with ThreadPoolExecutor(workers) as ex:
        ok = list(ex.map(lambda j: render_one(j, q), jobs))
    if not all(ok):
        sys.exit("有场景渲染失败，见 build/logs/")


def timeline(q):
    """每个场景在成片里的起点、时长和重音（全部按整小节排好）。"""
    out, t = [], 0.0
    for f, cls in ORDER:
        info = json.load(open(os.path.join(BUILD, "cues", f"{cls}.json")))
        d = info["duration"]
        out.append({"scene": cls, "start": t, "duration": d, "cues": [dict(c, t=c["t"] + t) for c in info["cues"]]})
        t += d
    return out, t


def music():
    from music import build_music
    tl, total = timeline(None)
    path = os.path.join(BUILD, "music.wav")
    print(f"配乐：{total:.0f} 秒 …", flush=True)
    build_music(tl, total, path)
    return path


def probe(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]))


def normalized_music():
    """把整条配乐的响度统一到 −16 LUFS（两遍 loudnorm），之后再按集截取。"""
    src = os.path.join(BUILD, "music.wav")
    dst = os.path.join(BUILD, "music_norm.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "48000", dst], check=True)
    return dst


# 辉光：把画面模糊一份，用“滤色”叠回去，亮的线条和文字周围就有一圈光
BLOOM = ("format=gbrp,split[a][b];[b]gblur=sigma=11[g];[a][g]blend=all_mode=screen:all_opacity=0.42,"
         "format=yuv420p")


def final(q, crf=24, parts=None, full=False):
    tl, total = timeline(q)
    start = {s["scene"]: s["start"] for s in tl}
    dur = {s["scene"]: s["duration"] for s in tl}
    names = [c for _, c in ORDER]
    music_path = normalized_music()
    jobs = []
    if full:
        jobs.append(("外代数与线性代数（完整版）", names[0], names[-1]))
    for i, p in enumerate(PARTS):
        if parts is None or i + 1 in parts:
            jobs.append(p)
    outs = []
    for title, first, last in jobs:
        a, b = names.index(first), names.index(last)
        scenes = names[a:b + 1]
        t0 = start[first]
        T = sum(dur[s] for s in scenes)
        lst = os.path.join(BUILD, f"concat_{first}.txt")
        with open(lst, "w") as f:
            for (fn, cls) in ORDER[a:b + 1]:
                f.write(f"file '{video_path(fn, cls, q)}'\n")
        meta = os.path.join(BUILD, f"meta_{first}.txt")
        with open(meta, "w", encoding="utf-8") as f:
            f.write(f";FFMETADATA1\ntitle={title}\n")
            acc = 0.0
            for s in scenes:
                if s in MARKS:
                    f.write(f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(acc * 1000)}\nEND={int((acc + dur[s]) * 1000)}\n"
                            f"title={MARKS[s]}\n")
                acc += dur[s]
        out = os.path.join(OUT, f"{title}.mp4" if q == "-qh" else f"预览-{title}.mp4")
        fade = 1.5
        af = f"atrim=start={t0}:duration={T},asetpts=PTS-STARTPTS,afade=t=out:st={T - fade}:d={fade}"
        if a > 0:
            af += ",afade=t=in:st=0:d=0.05"
        cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", music_path,
               "-i", meta, "-map", "0:v", "-map", "1:a", "-map_metadata", "2", "-map_chapters", "2",
               "-vf", BLOOM, "-af", af, "-c:v", "libx264", "-preset", "slow" if q == "-qh" else "veryfast",
               "-tune", "animation", "-crf", str(crf), "-g", "600", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{T:.3f}", out]
        print("编码", title, f"{T:.0f} 秒", flush=True)
        subprocess.run(cmd, check=True)
        print(f"  → {out}  {os.path.getsize(out) / 1e6:.1f} MB", flush=True)
        outs.append(out)
    return outs


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    q = "-ql" if "-ql" in sys.argv else "-qh"
    names = [a for a in sys.argv[2:] if not a.startswith("-")]
    if cmd in ("render", "all"):
        render(q, names or None)
    if cmd in ("music", "all"):
        music()
    if cmd in ("final", "all"):
        crf = next((int(a[6:]) for a in sys.argv if a.startswith("--crf=")), 24)
        final(q, crf=crf, parts=[int(x) for x in names if x.isdigit()] or None, full="--full" in sys.argv)
