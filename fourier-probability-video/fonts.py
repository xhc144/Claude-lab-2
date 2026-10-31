"""下载视频用到的字体到 build/fonts/（字体文件太大，不放进仓库）。

- 思源宋体 Black（Noto Serif SC）：章节标题、片名
- 思源黑体 Medium / Bold（Noto Sans SC）：说明文字
- Orbitron：英文标题、章节编号
- JetBrains Mono：读数（t = 1.25 这类）
"""

import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "build" / "fonts"

GOOGLE = {
    "NotoSerifSC-Black.ttf": "Noto+Serif+SC:wght@900",
    "NotoSerifSC-Medium.ttf": "Noto+Serif+SC:wght@500",
    "NotoSansSC-Medium.ttf": "Noto+Sans+SC:wght@500",
    "NotoSansSC-Bold.ttf": "Noto+Sans+SC:wght@700",
    "Orbitron-Black.ttf": "Orbitron:wght@900",
    "Orbitron-Medium.ttf": "Orbitron:wght@500",
    "JetBrainsMono-Medium.ttf": "JetBrains+Mono:wght@500",
}


def ensure():
    DIR.mkdir(parents=True, exist_ok=True)
    for name, family in GOOGLE.items():
        path = DIR / name
        if path.exists():
            continue
        # 用老浏览器的 User-Agent，Google Fonts 会返回完整的 .ttf，而不是按字符分片的 woff2
        css = requests.get(f"https://fonts.googleapis.com/css2?family={family}",
                           headers={"User-Agent": "Mozilla/4.0"}, timeout=60).text
        url = re.search(r"https://[^)]+\.ttf", css).group(0)
        print(f"下载字体 {name}")
        data = requests.get(url, timeout=300).content
        path.with_suffix(".tmp").write_bytes(data)
        path.with_suffix(".tmp").rename(path)
    return DIR


if __name__ == "__main__":
    print(ensure())
