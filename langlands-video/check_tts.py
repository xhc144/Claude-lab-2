"""用千问语音识别（qwen3-asr-flash）把合成好的每句旁白转写回文字，核对内容和语气。

我们没法逐句去听，这一步能发现读错字、漏读、语气跑偏（ASR 会顺带给出情绪标签）。
"""

import base64
import difflib
import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from narration import SCENES
from tts import API, line_path, voice_for


def transcribe(path):
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = {"model": "qwen3-asr-flash",
            "input": {"messages": [{"role": "user", "content": [{"audio": "data:audio/wav;base64," + b64}]}]},
            "parameters": {"asr_options": {"language": "zh"}}}
    r = requests.post(API, json=body, timeout=120,
                      headers={"Authorization": "Bearer " + os.environ["DASHSCOPE_API_KEY"]})
    msg = r.json()["output"]["choices"][0]["message"]
    emotion = next((a.get("emotion") for a in msg.get("annotations", []) if a.get("type") == "audio_info"), "?")
    return msg["content"][0]["text"], emotion


def norm(s):
    return re.sub(r"[\s，。、；：！？…—“”「」·,.;:!?\-]", "", s)


def main():
    lines = [line for sc in SCENES for line in sc["lines"]]
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda l: transcribe(line_path(l["say"], voice_for(l), l.get("take", 0))), lines))
    bad = 0
    for line, (text, emotion) in zip(lines, results):
        ratio = difflib.SequenceMatcher(None, norm(line["say"]), norm(text)).ratio()
        flag = "  " if ratio > 0.9 else "!!"
        bad += ratio <= 0.9
        print(f"{flag} {ratio:.2f} [{emotion}] {text}")
    print(f"共 {len(lines)} 句，可疑 {bad} 句")


if __name__ == "__main__":
    main()
