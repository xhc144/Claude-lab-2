# -*- coding: utf-8 -*-
"""Synthesize every narration segment with Qwen TTS (DashScope) and write timing.json."""
import hashlib, json, os, sys, time, wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests

from narration import CHAPTERS, seg_texts

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(ROOT, "audio")
CACHE = os.path.join(AUDIO, "cache")
os.makedirs(CACHE, exist_ok=True)

MODEL = "qwen3-tts-flash"
VOICE = os.environ.get("QWEN_VOICE", "Ethan")
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
SR = 24000

# Timeline layout (seconds)
LEAD = 0.6      # silence before first segment of a chapter
GAP = 0.42      # silence between segments
TAIL = 1.0      # silence after last segment


def synth(text):
    key = hashlib.sha1(f"{MODEL}|{VOICE}|{text}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".wav")
    if os.path.exists(path):
        return path
    body = {"model": MODEL, "input": {"text": text, "voice": VOICE, "language_type": "Chinese"}}
    hdr = {"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}", "Content-Type": "application/json"}
    for attempt in range(6):
        try:
            r = requests.post(URL, json=body, headers=hdr, timeout=120)
            r.raise_for_status()
            url = r.json()["output"]["audio"]["url"]
            a = requests.get(url, timeout=120)
            a.raise_for_status()
            with open(path + ".tmp", "wb") as f:
                f.write(a.content)
            os.replace(path + ".tmp", path)
            return path
        except Exception as e:  # retry with backoff
            print("retry", attempt, text[:20], e, file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("TTS failed: " + text)


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


def trim(x, thr=0.01, pad=0.04):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def main():
    jobs = []
    for ch in CHAPTERS:
        for k, seg in enumerate(ch["segs"]):
            jobs.append((ch["id"], k, seg_texts(seg)[0]))
    with ThreadPoolExecutor(4) as ex:
        paths = list(ex.map(lambda j: synth(j[2]), jobs))
    pmap = {(c, k): p for (c, k, _), p in zip(jobs, paths)}

    timing = {"lead": LEAD, "gap": GAP, "tail": TAIL, "sr": SR, "voice": VOICE, "chapters": []}
    gstart = 0.0
    for ch in CHAPTERS:
        segs, t = [], LEAD
        for k, seg in enumerate(ch["segs"]):
            x = trim(read_wav(pmap[(ch["id"], k)]))
            out = os.path.join(AUDIO, f"ch{ch['id']:02d}_{k:02d}.npy")
            np.save(out, x)
            d = len(x) / SR
            say, sub = seg_texts(seg)
            segs.append({"start": round(t, 3), "dur": round(d, 3), "sub": sub})
            t += d + GAP
        total = t - GAP + TAIL
        timing["chapters"].append({"id": ch["id"], "title": ch["title"], "gstart": round(gstart, 3),
                                   "total": round(total, 3), "segs": segs})
        gstart += total
    timing["grand_total"] = round(gstart, 3)
    with open(os.path.join(ROOT, "timing.json"), "w") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)
    for c in timing["chapters"]:
        print(f"ch{c['id']:02d} {c['total']:6.1f}s  {c['title']}")
    print(f"TOTAL {gstart/60:.2f} min")


if __name__ == "__main__":
    main()
