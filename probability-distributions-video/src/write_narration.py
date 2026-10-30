# -*- coding: utf-8 -*-
"""用千问（DashScope 兼容 OpenAI 的接口）把 outline.py 的分镜要点写成口播稿，存到 narration.draft.json。

草稿要人工审校（数学是否准确、读起来是否顺），改好后另存为 narration.json，tts.py 只读 narration.json。

    export DASHSCOPE_API_KEY=...
    python write_narration.py            # 全部场景
    python write_narration.py S03 S05    # 只重写这几个场景
"""
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from outline import EP_OF, EPISODES, SCENES

URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = os.environ.get("QWEN_TEXT_MODEL", "qwen3.8-max")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "narration.draft.json")

SYSTEM = """你是数学科普视频的解说词作者，正在为动画系列《概率分布图鉴》（共 8 集，从一枚硬币出发把常用分布串成一条线）写口播稿。
听众是学过微积分、刚接触概率论的大学生。目标是讲明白每个分布从哪来、公式怎么推出来，而不是罗列结论。
语气清楚、平实、有节奏，像一位讲得很好的老师在黑板前一步步推导，不卖弄、不煽情。

规则：
1. 每段对应一个动画画面。按给出的段数逐段输出，不合并、不拆分、不增删。
2. 每段字数尽量接近“目标字数”（上下浮动不超过两成）。
3. 数学内容必须与“要点”完全一致：不添加要点里没有的新结论、新数字，也不要省略要点里的推导步骤和关键条件。
   可以为了衔接自然、便于理解稍微调整语序或加一个过渡短语，但推导的每一步都要保留。
4. 只写要念出来的话。不要“大家好”“接下来让我们”“如图所示”之类套话（片头可以有一句简短的欢迎）。
5. 会被语音合成朗读，也会作为字幕显示，所以：
   - 希腊字母 λ μ σ α β ν ρ θ π 直接写（语音合成能正确读出），也可以用单个英文字母 n p k r s t x X Y U V；
   - 不写公式，不写 B(n,p) 这类括号记号，不用分数线、上下标、根号、≤ 等符号；
   - 用文字表达运算：“p 分之一”“根号 n”“σ 平方”“一减 p”“n 减一”；
   - 小数和百分比可以用阿拉伯数字，例如 0.5、68%。
6. 用中文全角标点，每段一到四句话。

只输出 JSON：{"segs": ["第一段", "第二段", ...]}"""


def ask(scene):
    ep = EPISODES[EP_OF[scene["id"]] - 1]
    lines = [f"第 {ep['ep']} 集《{ep['title']}——{ep['sub']}》，场景：{scene['title']}（共 {len(scene['segs'])} 段）"]
    for i, (pic, point, n) in enumerate(scene["segs"], 1):
        lines.append(f"\n第 {i} 段\n画面：{pic}\n要点：{point}\n目标字数：{n}")
    body = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n".join(lines)}],
        "temperature": 0.5,
        "stream": True,  # 推理模型要想一阵子，用流式接收，免得长时间没有响应被断开
    }
    hdr = {"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"}
    for attempt in range(5):
        try:
            text = ""
            with requests.post(URL, json=body, headers=hdr, timeout=120, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    line = line.decode("utf-8")
                    if not line.startswith("data: {"):
                        continue
                    choices = json.loads(line[6:]).get("choices") or []
                    if choices:
                        text += choices[0].get("delta", {}).get("content") or ""
            segs = json.loads(re.search(r"\{.*\}", text, re.S).group(0))["segs"]
            if len(segs) != len(scene["segs"]):
                raise ValueError(f"段数不对：{len(segs)} != {len(scene['segs'])}")
            return [s.strip() for s in segs]
        except Exception as e:  # noqa: BLE001
            print("重试", scene["id"], attempt, e, file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError("千问没有返回可用的口播稿：" + scene["id"])


def main():
    only = set(sys.argv[1:])
    draft = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            draft = json.load(f)
    # 默认只写还没有草稿的场景；每写完一个就存盘，中途断了下次接着写
    todo = [sc for sc in SCENES if (sc["id"] in only) if only] or \
        [sc for sc in SCENES if not only and sc["id"] not in draft]
    lock = threading.Lock()

    def work(sc):
        segs = ask(sc)
        with lock:
            draft[sc["id"]] = segs
            ordered = {s["id"]: draft[s["id"]] for s in SCENES if s["id"] in draft}
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(ordered, f, ensure_ascii=False, indent=1)
            print(sc["id"], sc["title"], flush=True)
            for s in segs:
                print("   ", len(s), s, flush=True)

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(work, todo))


if __name__ == "__main__":
    main()
