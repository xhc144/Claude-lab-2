"""下载视频用到的字体到 build/fonts/（字体文件太大，不放进仓库）。

- 思源宋体（Noto Serif SC）Medium / Bold / Black：全部中文文字（正文 / 强调 / 大标题）
- 思源黑体（Noto Sans SC）、Noto Sans Math、Noto Sans Symbols 2：个别字形的后备字体
西文、数字和公式不用这里的字体，而是交给 LaTeX（Latin Modern），见 engine/latex.py。
"""

import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "build" / "fonts"

GOOGLE = {
    "NotoSerifSC-Medium.ttf": "Noto+Serif+SC:wght@500",
    "NotoSerifSC-Bold.ttf": "Noto+Serif+SC:wght@700",
    "NotoSerifSC-Black.ttf": "Noto+Serif+SC:wght@900",
    "NotoSansSC-Regular.ttf": "Noto+Sans+SC:wght@400",
    "NotoSansMath-Regular.ttf": "Noto+Sans+Math",
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
