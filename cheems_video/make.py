"""一键出片：配音 → 时间轴和混音 → 分段并行渲染 → 拼接 → 合成音轨。

  DASHSCOPE_API_KEY=sk-... python make.py --work /tmp/cheems --out 成片.mp4 [--jobs 4]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--chunks", type=int, default=12)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--skip-tts", action="store_true")
    args = ap.parse_args()
    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)
    env = dict(os.environ, CHEEMS_WORK=work)
    if not args.skip_tts:
        subprocess.run([sys.executable, os.path.join(HERE, "tts.py")], env=env, check=True)
    sys.path.insert(0, HERE)
    os.environ["CHEEMS_WORK"] = work
    import engine
    from gfx import FPS
    tl = engine.build(work, mix=True)
    total = int(round(tl.dur * FPS))
    seg_dir = os.path.join(work, "seg")
    os.makedirs(seg_dir, exist_ok=True)
    bounds = [round(total * i / args.chunks) for i in range(args.chunks + 1)]
    jobs = []
    for i in range(args.chunks):
        out = os.path.join(seg_dir, f"part{i:02d}.mp4")
        jobs.append((bounds[i] / FPS, bounds[i + 1] / FPS, out))
    t0 = time.time()

    def run(job):
        a, b, out = job
        if os.path.exists(out + ".done"):
            return out
        subprocess.run([sys.executable, os.path.join(HERE, "render.py"), "--work", work, "--seg", f"{a:.6f}",
                        f"{b:.6f}", out, "--crf", str(args.crf)], check=True)
        open(out + ".done", "w").close()
        print(f"完成 {os.path.basename(out)}  {time.time() - t0:.0f}s", flush=True)
        return out

    with ThreadPoolExecutor(args.jobs) as ex:
        outs = list(ex.map(run, jobs))
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    video = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", os.path.join(work, "mix.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000", "-movflags", "+faststart", "-shortest",
                    args.out], check=True)
    print("成片：", args.out, f"用时 {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
