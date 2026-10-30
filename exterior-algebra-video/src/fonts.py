"""下载英文标题用的 Orbitron 字体到 build/fonts/（字体文件不放进仓库）。

中文用系统里的思源黑体（Noto Sans CJK SC，Debian/Ubuntu 的 fonts-noto-cjk），公式用 LaTeX。
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = ROOT.parent / "build" / "fonts"

GOOGLE = {
    "Orbitron-Bold.ttf": "Orbitron:wght@700",
    "Orbitron-Black.ttf": "Orbitron:wght@900",
}


def _get(url):
    # 用老浏览器的 User-Agent，Google Fonts 会返回完整的 .ttf，而不是按字符分片的 woff2
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/4.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def ensure():
    DIR.mkdir(parents=True, exist_ok=True)
    for name, family in GOOGLE.items():
        path = DIR / name
        if path.exists():
            continue
        css = _get(f"https://fonts.googleapis.com/css2?family={family}").decode()
        url = re.search(r"https://[^)]+\.ttf", css).group(0)
        print(f"下载字体 {name}")
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(_get(url))
        tmp.rename(path)
    return DIR


if __name__ == "__main__":
    print(ensure())
