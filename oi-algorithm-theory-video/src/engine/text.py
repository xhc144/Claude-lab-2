"""字体、富文本解析和排版。

富文本标记：{y|文字} 把“文字”染成黄色；颜色字母见 theme.TAG_COLORS。
在颜色字母后面加 m 表示等宽字体（公式、状态），加 ! 表示粗体，例如 {ym|f[i][j]}、{r!|错}、{m|dp[S][v]}。
标记可以嵌套：{y|状态 {m|f[i]} 表示……}。
"""

import functools
import re
from pathlib import Path

import skia

from . import theme

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "build" / "fonts"

FILES = {
    "sans": "NotoSansSC-Regular.ttf",
    "bold": "NotoSansSC-Bold.ttf",
    "mono": "JetBrainsMono-Medium.ttf",
    "math": "NotoSansMath-Regular.ttf",
    "latin": "NotoSans-Regular.ttf",
    "sym": "NotoSansSymbols2-Regular.ttf",
}

CHAINS = {
    "sans": ["sans", "math", "latin", "sym"],
    "bold": ["bold", "math", "latin", "sym"],
    "mono": ["mono", "sans", "math", "latin", "sym"],
    "monob": ["mono", "bold", "math", "latin", "sym"],
}


@functools.lru_cache(None)
def typeface(name):
    path = FONT_DIR / FILES[name]
    if not path.exists():
        import fonts  # noqa: 运行时下载
        fonts.ensure()
    tf = skia.Typeface.MakeFromFile(str(path))
    if tf is None:
        raise RuntimeError(f"无法加载字体 {path}")
    return tf


@functools.lru_cache(None)
def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    return f


@functools.lru_cache(200000)
def _has(name, ch):
    return font(name, 20).unicharToGlyph(ord(ch)) != 0


# 这些符号用西文字体更好看（中文字体里的引号带全角空白，≤ 是斜体样式）
PREFER_LATIN = set("“”‘’≤≥")


def pick(chain, ch):
    if ch in PREFER_LATIN and chain in ("sans", "bold") and _has("latin", ch):
        return "latin"
    for name in CHAINS[chain]:
        if _has(name, ch):
            return name
    return CHAINS[chain][0]


@functools.lru_cache(100000)
def measure(name, size, s):
    return font(name, size).measureText(s)


@functools.lru_cache(100000)
def blob(name, size, s):
    return skia.TextBlob.MakeFromString(s, font(name, size))


@functools.lru_cache(None)
def metrics(size):
    m = font("sans", size).getMetrics()
    return m.fAscent, m.fDescent


# ------------------------------------------------------------------ 解析
_TAG = re.compile(r"\{([ycgrpobkdwf]?)(m?)(!?)\|")


def parse(markup, color, chain="sans"):
    """返回 [(文字, 颜色, 字体链)]。"""
    out = []

    def rec(s, col, ch):
        i = 0
        buf = []
        while i < len(s):
            m = _TAG.match(s, i) if s[i] == "{" else None
            if m and (m.group(1) or m.group(2) or m.group(3)):
                # 找配对的右括号
                depth, j = 1, m.end()
                while j < len(s) and depth:
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                    j += 1
                if depth == 0:
                    if buf:
                        out.append(("".join(buf), col, ch))
                        buf = []
                    c2 = theme.TAG_COLORS.get(m.group(1), col) if m.group(1) else col
                    if m.group(2):
                        ch2 = "monob" if (m.group(3) or ch in ("bold", "monob")) else "mono"
                    elif m.group(3):
                        ch2 = "monob" if ch in ("mono", "monob") else "bold"
                    else:
                        ch2 = ch
                    rec(s[m.end():j - 1], c2, ch2)
                    i = j
                    continue
            buf.append(s[i])
            i += 1
        if buf:
            out.append(("".join(buf), col, ch))

    rec(markup, color, chain)
    return out


# ------------------------------------------------------------------ 分词与排版
_CLOSE = set("，。、；：！？）】》」』’”…")
_OPEN = set("（【《「『‘“")


def _is_cjk(c):
    o = ord(c)
    return (0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF
            or 0x3000 <= o <= 0x303F or 0x2460 <= o <= 0x24FF)


def _tokens(runs):
    """把 runs 切成不可再分的词：每个汉字一个词，连续的西文字符一个词，空格单独一个词。
    每个词是 [(文字, 颜色, 字体链)] 的列表（一个词可以跨颜色）。"""
    toks = []
    cur = []        # 当前西文词
    pending_open = []

    def flush():
        nonlocal cur
        if cur:
            toks.append(cur)
            cur = []

    for text, col, ch in runs:
        for c in text:
            if c == "\n":
                flush()
                toks.append("\n")
                continue
            if c == " ":
                flush()
                toks.append([(" ", col, ch)])
                continue
            piece = (c, col, ch)
            if _is_cjk(c) or c in _CLOSE or c in _OPEN:
                if c in _CLOSE and (cur or toks):
                    # 不能出现在行首：粘到前一个词上
                    if cur:
                        cur.append(piece)
                    elif toks and toks[-1] != "\n" and toks[-1][0][0] != " ":
                        toks[-1].append(piece)
                    else:
                        toks.append([piece])
                    continue
                flush()
                if c in _OPEN:
                    cur = [piece]          # 和下一个字粘在一起
                    continue
                toks.append([piece])
            else:
                cur.append(piece)
    flush()
    # 把以开括号结尾的孤立词与后一个词合并
    merged = []
    for t in toks:
        if merged and merged[-1] != "\n" and t != "\n" and len(merged[-1]) >= 1 \
                and merged[-1][-1][0] in _OPEN and t[0][0] != " ":
            merged[-1] = merged[-1] + t
        else:
            merged.append(t)
    return merged


def _shape(tok, size):
    """把一个词按后备字体切成小段：[(字体名, 文字, 颜色, 宽度)]"""
    segs = []
    for c, col, ch in tok:
        name = pick(ch, c)
        if segs and segs[-1][0] == name and segs[-1][2] == col:
            segs[-1][1] += c
        else:
            segs.append([name, c, col])
    return [(n, s, col, measure(n, size, s)) for n, s, col in segs]


class Layout:
    """排好的一段文字。lines: [(行宽, [(x, 字体名, 文字, 颜色)])]"""

    def __init__(self, lines, size, lh):
        self.lines = lines
        self.size = size
        self.lh = lh
        self.w = max((l[0] for l in lines), default=0)
        self.h = len(lines) * size * lh

    def draw(self, canvas, x, y, align="l", alpha=1.0, default=None):
        """(x, y) 是文字块左上角；align 是行内对齐；没有颜色标记的文字用 default 颜色。"""
        asc, desc = metrics(self.size)
        line_h = self.size * self.lh
        base0 = (line_h - (desc - asc)) / 2 - asc
        paint = skia.Paint(AntiAlias=True)
        for k, (lw, pieces) in enumerate(self.lines):
            dx = 0 if align == "l" else (self.w - lw) / 2 if align == "c" else self.w - lw
            by = y + k * line_h + base0
            for px, name, s, col in pieces:
                c = col if col is not None else (default or theme.FG)
                a = c[3] * alpha
                if a <= 0.003:
                    continue
                paint.setColor4f(skia.Color4f(c[0], c[1], c[2], min(1.0, a)))
                canvas.drawTextBlob(blob(name, self.size, s), x + dx + px, by, paint)


@functools.lru_cache(20000)
def layout(markup, size, color=None, maxw=None, chain="sans", lh=1.45):
    runs = parse(markup, color, chain)
    toks = _tokens(runs)
    lines = []
    cur, cw = [], 0.0

    def push():
        nonlocal cur, cw
        # 去掉行尾空格
        while cur and cur[-1][2] == " ":
            cw -= measure(cur[-1][1], size, " ")
            cur.pop()
        lines.append((cw, cur))
        cur, cw = [], 0.0

    for tok in toks:
        if tok == "\n":
            push()
            continue
        segs = _shape(tok, size)
        tw = sum(s[3] for s in segs)
        is_space = len(tok) == 1 and tok[0][0] == " "
        if is_space and not cur:
            continue
        if maxw is not None and cur and cw + tw > maxw and not is_space:
            push()
        for name, s, col, w in segs:
            cur.append((cw, name, s, col))
            cw += w
    if cur or not lines:
        push()
    return Layout(lines, size, lh)


@functools.lru_cache(20000)
def balanced(markup, size, maxw, chain="sans", lh=1.45):
    """居中的多行文字：在行数不变的前提下把宽度收窄，避免最后一行只剩一两个字。"""
    L = layout(markup, size, None, maxw, chain, lh)
    n = len(L.lines)
    if n <= 1 or maxw is None:
        return L
    lo, hi = maxw * 0.4, maxw
    for _ in range(14):
        mid = (lo + hi) / 2
        if len(layout(markup, size, None, mid, chain, lh).lines) <= n:
            hi = mid
        else:
            lo = mid
    return layout(markup, size, None, hi, chain, lh)


def plain_len(markup):
    """阅读量：一个汉字算 1，其他可见字符算 0.55。"""
    n = 0.0
    for text, _, _ in parse(markup, theme.FG):
        for c in text:
            if c.isspace():
                continue
            n += 1.0 if _is_cjk(c) else 0.55
    return n
