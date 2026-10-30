# -*- coding: utf-8 -*-
"""用通义千问 TTS (DashScope, qwen3-tts-flash) 为旁白逐句合成语音。

输出:
  audio/sent/<hash>.wav          每句原始音频（缓存）
  audio/seg/<Scene>_<key>.wav    每段拼接后的音频（去掉首尾静音、句间留白）
  audio/timing.json              每段时长与段内每句的起止时间（用于动画同步与字幕）
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

from script import SCRIPT, SCENE_ORDER, iter_sentences

API = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = os.environ.get("TTS_MODEL", "qwen3-tts-flash")
VOICE = os.environ.get("TTS_VOICE", "Elias")
SR = 24000
GAP = 0.32          # 段内句与句之间的停顿（秒）
EDGE = 0.04         # 去静音后首尾保留的余量（秒）

ROOT = os.path.dirname(os.path.abspath(__file__))
SENT_DIR = os.path.join(ROOT, "audio", "sent")
SEG_DIR = os.path.join(ROOT, "audio", "seg")


def sent_path(tts_text):
    h = hashlib.sha1(f"{MODEL}|{VOICE}|{tts_text}".encode()).hexdigest()[:16]
    return os.path.join(SENT_DIR, f"{h}.wav")


def synth(tts_text):
    out = sent_path(tts_text)
    if os.path.exists(out):
        return out
    key = os.environ["DASHSCOPE_API_KEY"]
    body = {"model": MODEL, "input": {"text": tts_text, "voice": VOICE, "language_type": "Chinese"}}
    for attempt in range(6):
        try:
            r = requests.post(API, json=body, timeout=120,
                              headers={"Authorization": f"Bearer {key}"})
            d = r.json()
            url = d["output"]["audio"]["url"].replace("http://", "https://", 1)
            a = requests.get(url, timeout=120)
            a.raise_for_status()
            tmp = out + ".part"
            with open(tmp, "wb") as f:
                f.write(a.content)
            os.replace(tmp, out)
            return out
        except Exception as e:  # 限流或网络抖动时退避重试
            print(f"  retry {attempt + 1}: {tts_text[:16]}… {e} {str(locals().get('d', ''))[:200]}",
                  file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"TTS failed: {tts_text}")


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


def trim(x, thresh=0.012):
    env = np.convolve(np.abs(x), np.ones(240) / 240, mode="same")
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(EDGE * SR))
    b = min(len(x), idx[-1] + int(EDGE * SR))
    return x[a:b]


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    os.makedirs(SENT_DIR, exist_ok=True)
    os.makedirs(SEG_DIR, exist_ok=True)
    jobs = [tts for sc in SCENE_ORDER for _, _, tts in iter_sentences(sc)]
    print(f"{len(jobs)} sentences, {sum(len(j) for j in jobs)} chars, voice={VOICE}")
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(synth, jobs))

    timing = {}
    for sc in SCENE_ORDER:
        timing[sc] = {}
        for key, sents in SCRIPT[sc]:
            parts, sent_info, t = [], [], 0.0
            for s in sents:
                sub, tts = (s if isinstance(s, tuple) else (s, s))
                x = trim(read_wav(sent_path(tts)))
                if parts:
                    parts.append(np.zeros(int(GAP * SR), np.float32))
                    t += GAP
                parts.append(x)
                d = len(x) / SR
                sent_info.append({"sub": sub, "start": round(t, 3), "end": round(t + d, 3)})
                t += d
            seg = np.concatenate(parts)
            write_wav(os.path.join(SEG_DIR, f"{sc}_{key}.wav"), seg)
            timing[sc][key] = {"dur": round(len(seg) / SR, 3), "sents": sent_info}
        tot = sum(v["dur"] for v in timing[sc].values())
        print(f"{sc:10s} {tot:7.1f}s")
    with open(os.path.join(ROOT, "audio", "timing.json"), "w") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)
    print("total speech", sum(v["dur"] for s in timing.values() for v in s.values()))


if __name__ == "__main__":
    main()
