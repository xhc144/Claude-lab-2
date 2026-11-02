"""下载视频用到的字体到 build/fonts/（字体文件太大，不放进仓库）。

- 思源黑体（Noto Sans SC）Regular / Bold：全部中文文字
- JetBrains Mono：状态、下标、公式里的等宽部分
- Noto Sans Math、Noto Sans、Noto Sans Symbols 2：⌊⌋、上下标、✓✗ 等符号的后备字体
"""

import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "build" / "fonts"

GOOGLE = {
    "NotoSansSC-Regular.ttf": "Noto+Sans+SC:wght@400",
    "NotoSansSC-Bold.ttf": "Noto+Sans+SC:wght@700",
    "JetBrainsMono-Medium.ttf": "JetBrains+Mono:wght@500",
    "NotoSansMath-Regular.ttf": "Noto+Sans+Math",
    "NotoSans-Regular.ttf": "Noto+Sans:wght@400",
    "NotoSansSymbols2-Regular.ttf": "Noto+Sans+Symbols+2",
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
