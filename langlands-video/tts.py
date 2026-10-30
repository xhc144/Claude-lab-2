"""用千问（通义千问 Qwen3-TTS，阿里云百炼 DashScope）把旁白逐句合成为语音。

需要环境变量 DASHSCOPE_API_KEY。结果按（模型、音色、文字）缓存在 build/tts/，改了哪句只重新合成哪句。
"""

import hashlib
import json
import os
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

from narration import SCENES

API = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = os.environ.get("QWEN_TTS_MODEL", "qwen3-tts-flash")
# 旁白用 Kai：低沉（基频一百赫兹出头）、有磁性、语气沉稳，像电影预告片的旁白。
# 试过 Ryan，戏剧张力很足，但 ASR 几乎每句都判成「愤怒」，听着像在吼。想换音色就设 QWEN_TTS_VOICE。
VOICE = os.environ.get("QWEN_TTS_VOICE", "Kai")
# 朗兰兹信里的原话换成温和、年轻一些的 Ethan 来「念信」，后期再加一层老录音的质感，和旁白区分开。
QUOTE_VOICE = os.environ.get("QWEN_TTS_QUOTE_VOICE", "Ethan")

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "build" / "tts"


def voice_for(line):
    return QUOTE_VOICE if line.get("quote") else VOICE


def _synthesize(text, voice):
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        sys.exit("没有设置 DASHSCOPE_API_KEY")
    body = {"model": MODEL, "input": {"text": text, "voice": voice, "language_type": "Chinese"}}
    for attempt in range(5):
        try:
            r = requests.post(API, json=body, timeout=120,
                              headers={"Authorization": f"Bearer {key}"})
            data = r.json()
            if "output" not in data:
                raise RuntimeError(f"TTS 失败：{data}")
            url = data["output"]["audio"]["url"].replace("http://", "https://", 1)
            audio = requests.get(url, timeout=120)
            audio.raise_for_status()
            return audio.content
        except Exception as e:  # 网络抖动、限流：退避重试
            if attempt == 4:
                raise
            print(f"  重试（{e}）", file=sys.stderr)
            time.sleep(2 ** (attempt + 1))


def _trim(path):
    """去掉首尾静音，返回 (采样, 采样率)。"""
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    env = np.convolve(np.abs(x), np.ones(240) / 240, "same")
    loud = np.nonzero(env > 0.01)[0]
    if len(loud) == 0:
        return x, sr
    a = max(0, loud[0] - int(0.03 * sr))
    b = min(len(x), loud[-1] + int(0.08 * sr))
    return x[a:b], sr


def line_path(text, voice, take=0):
    # TTS 每次结果不完全一样；某句读得不好时，给它设 take=1、2…… 换一版重新合成。
    tag = f"{MODEL}|{voice}|{text}" + (f"|{take}" if take else "")
    h = hashlib.sha1(tag.encode()).hexdigest()[:16]
    return CACHE / f"{h}.wav"


def ensure_all():
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = []
    for scene in SCENES:
        for line in scene["lines"]:
            p = line_path(line["say"], voice_for(line), line.get("take", 0))
            if not p.exists():
                todo.append((line["say"], voice_for(line), p))

    def job(item):
        text, voice, p = item
        p.with_suffix(".tmp").write_bytes(_synthesize(text, voice))
        p.with_suffix(".tmp").rename(p)
        print(f"  合成：{text[:24]}…")

    if todo:
        print(f"千问 TTS（{MODEL}，旁白 {VOICE}，信件 {QUOTE_VOICE}）：合成 {len(todo)} 句")
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(job, todo))


def load_lines():
    """返回每个场景每句话的 (采样, 采样率)。"""
    ensure_all()
    out = []
    for scene in SCENES:
        out.append([_trim(line_path(line["say"], voice_for(line), line.get("take", 0))) for line in scene["lines"]])
    return out


if __name__ == "__main__":
    lines = load_lines()
    total = sum(len(x) / sr for sc in lines for x, sr in sc)
    print(json.dumps({"voice": VOICE, "lines": sum(map(len, lines)), "speech_seconds": round(total, 1)}, ensure_ascii=False))
