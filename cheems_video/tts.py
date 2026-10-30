"""用阿里云百炼（千问 TTS）给每句台词配音，结果按「音色 + 文本」缓存成 wav。

API Key 从环境变量 DASHSCOPE_API_KEY 读取，或者 CHEEMS_KEY_FILE 指向的文件。
用法：python tts.py            # 生成所有缺少的配音
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from script import VOICES, all_lines

HOST = "https://dashscope.aliyuncs.com"
MODEL = "qwen3-tts-flash"
CACHE = os.environ.get("CHEEMS_TTS_DIR", os.path.join(os.environ.get("CHEEMS_WORK", "."), "tts"))


def api_key():
    k = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not k and os.environ.get("CHEEMS_KEY_FILE"):
        k = open(os.environ["CHEEMS_KEY_FILE"]).read().strip()
    if not k:
        sys.exit("没有百炼 API Key：请设置 DASHSCOPE_API_KEY")
    return k


def cache_path(voice, text):
    h = hashlib.sha1(f"{MODEL}|{voice}|{text}".encode()).hexdigest()[:16]
    return os.path.join(CACHE, f"{h}.wav")


def synthesize(text, voice, key, tries=6):
    url = HOST + "/api/v1/services/aigc/multimodal-generation/generation"
    payload = {"model": MODEL, "input": {"text": text, "voice": voice, "language_type": "Chinese"}}
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = json.loads(r.read())
            audio = body["output"]["audio"]
            au = audio["url"]
            if au.startswith("http://"):
                au = "https://" + au[7:]
            with urllib.request.urlopen(au, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as ex:
            msg = ex.read().decode("utf-8", "replace")[:300]
            if ex.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise RuntimeError(f"HTTP {ex.code}: {msg}") from None
        except (urllib.error.URLError, OSError, KeyError) as ex:
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise RuntimeError(str(ex)) from None


def job(item):
    voice, text, key = item
    path = cache_path(voice, text)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path, False
    data = synthesize(text, voice, key)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return path, True


def main():
    os.makedirs(CACHE, exist_ok=True)
    key = api_key()
    items = []
    seen = set()
    for _, ln in all_lines():
        v = VOICES[ln.who]
        if (v, ln.text) not in seen:
            seen.add((v, ln.text))
            items.append((v, ln.text, key))
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        for path, new in ex.map(job, items):
            done += 1
            if new:
                print(f"[{done}/{len(items)}] {os.path.basename(path)}  {time.time() - t0:.0f}s", flush=True)
    print("全部配音完成", len(items))


if __name__ == "__main__":
    main()
