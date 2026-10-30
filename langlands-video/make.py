"""一键生成《朗兰兹纲领》介绍视频。

    python make.py                 # 合成语音 → 排时间线 → 配乐混音 → 并行渲染画面 → 合成 mp4
    python make.py --stills 5,40   # 只渲染这几个时刻的静帧（PNG），检查画面用
    python make.py --audio         # 只重新生成音轨

成品在 build/langlands.mp4。
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
import timeline  # noqa: E402
import tts  # noqa: E402


def make_timeline():
    lines = tts.load_lines()
    durations = [[len(x) / sr for x, sr in scene] for scene in lines]
    tl = timeline.build(durations)
    timeline.save(tl, BUILD / "timeline.json")
    return tl, lines


def _render_part(args):
    import render
    tl, f0, f1, out = args
    render.encode_range(tl, f0, f1, Path(out))
    return out


def render_video(tl, jobs):
    total = int(round(tl["duration"] * tl["fps"]))
    parts_dir = BUILD / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    n = jobs * 3  # 切得比进程数多一些，快的进程能多干点
    bounds = [round(total * k / n) for k in range(n + 1)]
    tasks = [(tl, bounds[k], bounds[k + 1], str(parts_dir / f"part{k:02d}.mp4")) for k in range(n)]
    print(f"渲染 {total} 帧（{tl['duration']:.1f} 秒），{jobs} 个进程")
    with ProcessPoolExecutor(jobs) as ex:
        outs = list(ex.map(_render_part, tasks))
    lst = parts_dir / "list.txt"
    lst.write_text("".join(f"file '{Path(o).name}'\n" for o in outs))
    video = BUILD / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(video)], check=True)
    return video


def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-shortest", str(out)], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="逗号分隔的时刻（秒），只渲染静帧")
    ap.add_argument("--audio", action="store_true", help="只生成音轨")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    fonts.ensure()
    BUILD.mkdir(exist_ok=True)
    tl, lines = make_timeline()
    print(f"时间线：{tl['duration']:.1f} 秒")

    if args.stills:
        import render
        out = BUILD / "stills"
        out.mkdir(exist_ok=True)
        for s in args.stills.split(","):
            t = float(s)
            p = out / f"t{t:07.2f}.png"
            render.still(tl, t, p)
            print(p)
        return

    import audio
    wav = audio.build(tl, lines, BUILD / "audio.wav")
    if args.audio:
        print(wav)
        return
    video = render_video(tl, args.jobs)
    out = mux(video, wav, BUILD / "langlands.mp4")
    print(f"完成：{out}")


if __name__ == "__main__":
    main()
