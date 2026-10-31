"""一键生成《当概率开始旋转》。

    python make.py                    # 字体 → 音轨 → 并行渲染画面 → 合成 → 压缩
    python make.py --stills 40,95.5   # 只渲染这几个时刻的静帧（PNG），检查画面用
    python make.py --audio            # 只重新生成音轨
    python make.py --jobs 4           # 渲染进程数（默认等于 CPU 核数）

原画质成片在 build/full.mp4，压缩后放进仓库的是 当概率开始旋转.mp4。
"""

import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
sys.path.insert(0, str(ROOT))

import fonts  # noqa: E402

OUT = ROOT / "当概率开始旋转.mp4"


def _render_part(args):
    import render
    f0, f1, out = args
    render.encode_range(f0, f1, Path(out))
    return out


def render_video(jobs):
    import timeline
    tl = timeline.TIMELINE
    total = int(round(tl.duration * timeline.FPS))
    parts = BUILD / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    n = jobs * 4                       # 切得比进程数多一些，快的进程能多干点
    bounds = [round(total * k / n) for k in range(n + 1)]
    tasks = [(bounds[k], bounds[k + 1], str(parts / f"part{k:02d}.mp4")) for k in range(n)]
    print(f"渲染 {total} 帧（{tl.duration:.1f} 秒），{jobs} 个进程")
    with ProcessPoolExecutor(jobs) as ex:
        outs = list(ex.map(_render_part, tasks))
    lst = parts / "list.txt"
    lst.write_text("".join(f"file '{Path(o).name}'\n" for o in outs))
    video = BUILD / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(video)], check=True)
    return video


def mux(video, wav, out):
    """合成音视频；音轨顺便做响度标准化（−16 LUFS）。"""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", str(out)], check=True)
    return out


def compress(src, dst, crf=28):
    """仓库里放压缩版（目标 50 MB 以内）。粒子画面细节多，用 slow 预设换体积。"""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c:v", "libx264", "-preset", "slow",
                    "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(dst)], check=True)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="逗号分隔的时刻（秒），只渲染静帧")
    ap.add_argument("--audio", action="store_true", help="只生成音轨")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--crf", type=int, default=28, help="压缩版的 CRF")
    args = ap.parse_args()

    fonts.ensure()
    BUILD.mkdir(exist_ok=True)
    import timeline
    tl = timeline.TIMELINE
    print(f"时长 {tl.duration:.1f} 秒")

    if args.stills:
        import render
        out = BUILD / "stills"
        out.mkdir(exist_ok=True)
        for s in args.stills.split(","):
            t = float(s)
            p = out / f"t{t:07.2f}.png"
            render.still(t, p)
            print(p)
        return

    import audio
    wav = audio.build(tl, BUILD / "audio.wav")
    print(f"音轨：{wav}")
    if args.audio:
        return
    video = render_video(args.jobs)
    full = mux(video, wav, BUILD / "full.mp4")
    compress(full, OUT, args.crf)
    print(f"完成：{OUT}（{OUT.stat().st_size / 1e6:.1f} MB）")


if __name__ == "__main__":
    main()
