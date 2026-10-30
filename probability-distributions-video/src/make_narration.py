# -*- coding: utf-8 -*-
"""把 outline.py 里每段“要讲的内容”整理成口播稿 narration.json（字幕也用它）。

口播稿就是大纲里写好的讲解文字，不经过任何文本模型；这里只做几处让语音合成念顺的小改动。
改讲解内容请直接改 outline.py，然后重新运行本脚本和 tts.py。
"""
import json
import os
import re

from outline import SCENES

HERE = os.path.dirname(os.path.abspath(__file__))


def speakable(text):
    # 紧跟在字母后面的下标数字（Z1、x2、λ1）会被合成吞掉，中间加个空格就能念出来
    return re.sub(r"(?<=[A-Za-zλ])(\d)", r" \1", text)


def main():
    out = {s["id"]: [speakable(seg[1]) for seg in s["segs"]] for s in SCENES}
    with open(os.path.join(HERE, "narration.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(len(out), "个场景，", sum(len(t) for v in out.values() for t in v), "字")


if __name__ == "__main__":
    main()
