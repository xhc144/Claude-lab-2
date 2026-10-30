# -*- coding: utf-8 -*-
"""用千问语音合成（qwen3-tts-flash）把 narration.json 的每段解说念出来，写 audio/ 和 timing.json。

    export DASHSCOPE_API_KEY=...
    python tts.py                 # 换音色：export QWEN_VOICE=Ethan

字幕和送去合成的文字基本一样，希腊字母原样保留；spoken() 只去掉破折号。
合成结果按文字内容缓存在 audio/cache/，改了哪段只重新合成哪段。
"""
import hashlib
import json
import os
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")
CACHE = os.path.join(AUDIO, "cache")

MODEL = "qwen3-tts-flash"
VOICE = os.environ.get("QWEN_VOICE", "Maia")
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
SR = 24000

# 希腊字母原样送去合成：qwen3-tts-flash 能直接读出 λ、μ、σ 等（试过把 λ 换成“兰姆达”，反而念得别扭）。
# 只处理两种破折号，免得被读成奇怪的停顿。
READ = [("–", ""), ("—", "，")]


def spoken(text):
    for a, b in READ:
        text = text.replace(a, b)
    return text


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
        except Exception as e:  # noqa: BLE001
            print("重试", attempt, text[:20], e, file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("合成失败：" + text)


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1, path
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def trim(x, thr=0.01, pad=0.04):
    """去掉首尾的静音，留一点余量。"""
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def main():
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(HERE, "narration.json"), encoding="utf-8") as f:
        nar = json.load(f)
    jobs = [(sid, i, spoken(t)) for sid, segs in nar.items() for i, t in enumerate(segs)]
    with ThreadPoolExecutor(4) as ex:
        paths = list(ex.map(lambda j: synth(j[2]), jobs))
    durations, total = {}, 0.0
    for (sid, i, _), p in zip(jobs, paths):
        x = trim(read_wav(p))
        write_wav(os.path.join(AUDIO, f"{sid}_{i:02d}.wav"), x)
        durations.setdefault(sid, []).append(round(len(x) / SR, 3))
        total += len(x) / SR
    with open(os.path.join(HERE, "timing.json"), "w", encoding="utf-8") as f:
        json.dump({"model": MODEL, "voice": VOICE, "sr": SR, "durations": durations}, f, indent=1)
    print(f"{len(jobs)} 段，配音共 {total / 60:.1f} 分钟")


if __name__ == "__main__":
    main()
