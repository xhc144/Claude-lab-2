"""字体、富文本解析和排版。

- 中文用思源宋体（Noto Serif SC），正文 Medium、强调 Bold、大标题 Black；
- 所有西文、数字、符号和公式都交给 LaTeX（见 latex.py），和中文按同一条基线排在一起，中西文之间自动留空。

富文本标记：{y|文字} 把“文字”染成黄色；颜色字母见 theme.TAG_COLORS。
在颜色字母后面加 t 表示字符串（打字机字体，如 {t|abab}），加 ! 表示粗体，例如 {y!|重点}。
标记可以嵌套：{y|状态 f[i] 表示……}。显式公式写在 $…$ 里，例如 $\\sum_{i<j} a_i a_j$。
"""

import functools
import re
from pathlib import Path

import skia

from . import theme
from . import latex as TX

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "build" / "fonts"

FILES = {
    "serif": "NotoSerifSC-Medium.ttf",
    "serifb": "NotoSerifSC-Bold.ttf",
    "serifk": "NotoSerifSC-Black.ttf",
    "sans": "NotoSansSC-Regular.ttf",
    "sym": "NotoSansSymbols2-Regular.ttf",
    "math": "NotoSansMath-Regular.ttf",
}

# 富文本里的“字体链”名字 → 中文字体
CJK_FONT = {"sans": "serif", "mono": "serif", "bold": "serifb", "monob": "serifb", "black": "serifk",
            "tt": "serif", "ttb": "serifb"}
BOLD = {"bold", "monob", "black", "ttb"}
TT = {"tt", "ttb"}          # 字符串里的字符：用 LaTeX 的打字机字体（\texttt），不当作数学变量

LATEX_SCALE = 1.0       # LaTeX 8pt 字形的 1em 和中文字号相当
AUTOSPACE = 0.22        # 中西文之间自动留的空（em）
WORDSPACE = 0.30        # 公式片段之间的空格（em）


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


def pick(primary, ch):
    for name in (primary, "sans", "sym", "math"):
        if _has(name, ch):
            return name
    return primary


@functools.lru_cache(100000)
def measure(name, size, s):
    return font(name, size).measureText(s)


@functools.lru_cache(100000)
def blob(name, size, s):
    return skia.TextBlob.MakeFromString(s, font(name, size))


@functools.lru_cache(None)
def metrics(size):
    m = font("serif", size).getMetrics()
    return m.fAscent, m.fDescent


# ------------------------------------------------------------------ 解析
_TAG = re.compile(r"\{([ycgrpobkdwf]?)(m?)(t?)(!?)\|")


def parse(markup, color, chain="sans"):
    """返回 [(文字, 颜色, 字体链)]。"""
    out = []

    def rec(s, col, ch):
        i = 0
        buf = []
        while i < len(s):
            if s[i] == "$":                       # 公式里的花括号不当作标记
                j = s.find("$", i + 1)
                j = len(s) - 1 if j < 0 else j
                buf.append(s[i:j + 1])
                i = j + 1
                continue
            m = _TAG.match(s, i) if s[i] == "{" else None
            if m and (m.group(1) or m.group(2) or m.group(3) or m.group(4)):
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
                    ch2 = ch
                    if m.group(3):                      # t：字符串（打字机字体）
                        ch2 = "ttb" if ch in BOLD else "tt"
                    if m.group(4):                      # !：粗体
                        ch2 = {"tt": "ttb", "ttb": "ttb", "black": "black"}.get(ch2, "bold")
                    rec(s[m.end():j - 1], c2, ch2)
                    i = j
                    continue
            buf.append(s[i])
            i += 1
        if buf:
            out.append(("".join(buf), col, ch))

    rec(markup, color, chain)
    return out


# ------------------------------------------------------------------ 中西文切分
_CLOSE = set("，。、；：！？）】》」』’”…")
_OPEN = set("（【《「『‘“")
_NOSPACE_BEFORE = set(")]},.;:!?")      # 西文的右括号、标点前面不加中西文间距


def _is_cjk(c):
    o = ord(c)
    return (0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF
            or 0x3000 <= o <= 0x303F or 0x2460 <= o <= 0x24FF or c in "“”‘’")


def _split_latin(run, fine=False):
    """把一段西文切成可以换行的小块：只在“顶层”、紧挨关系符/运算符或逗号的空格处断开。返回 [(块, 前面是否有空格)]。
    fine=True 时（整块太长、一行放不下）圆括号、方括号里面的空格也可以断，只有花括号里的不断。"""
    chunks, cur, depth = [], [], 0
    space_before = False
    i = 0
    rel = TX.RELS | TX.BINS
    while i < len(run):
        c = run[i]
        if c == "$":
            j = run.find("$", i + 1)
            j = len(run) - 1 if j < 0 else j
            cur.append(run[i:j + 1])
            i = j + 1
            continue
        if c in ("{" if fine else "([{"):
            depth += 1
        elif c in ("}" if fine else ")]}"):
            depth = max(0, depth - 1)
        if c == " " and depth == 0:
            j = i
            while j < len(run) and run[j] == " ":
                j += 1
            prev = run[i - 1] if i > 0 else ""
            nxt = run[j] if j < len(run) else ""
            if cur and (prev in rel or prev in ",;" or nxt in rel):
                chunks.append(("".join(cur), space_before))
                cur = []
                space_before = True
                i = j
                continue
        cur.append(c)
        i += 1
    if cur:
        chunks.append(("".join(cur), space_before))
    return chunks


class Piece:
    __slots__ = ("kind", "x", "w", "font", "text", "color", "tex", "bold", "scale")

    def __init__(self):
        self.kind, self.x, self.w, self.font, self.text = "font", 0.0, 0.0, None, ""
        self.color, self.tex, self.bold, self.scale = None, "", False, 1.0


def _tokens(runs, size, maxw=None):
    """切成不可再分的“词”：每个汉字一个词（处理避头尾），每个西文小块一个词。
    词 = (宽度, [Piece], 左边是否要求和前一个词之间留空, 类型)"""
    toks = []
    trailing = False            # 上一段（不同颜色 / 字体的富文本片段）是否以空格结尾
    for text, col, ch in runs:
        cjk_font = CJK_FONT.get(ch, "serif")
        bold = ch in BOLD
        i = 0
        while i < len(text):
            c = text[i]
            if c == "\n":
                toks.append("\n")
                i += 1
                continue
            if _is_cjk(c):
                p = Piece()
                p.kind, p.font, p.text, p.color = "font", pick(cjk_font, c), c, col
                p.w = measure(p.font, size, c)
                toks.append([p.w, [p], 0.0, "cjk", c])
                i += 1
                continue
            # 一段西文：到下一个汉字或换行为止
            j = i
            while j < len(text) and not _is_cjk(text[j]) and text[j] != "\n":
                if text[j] == "$":
                    k = text.find("$", j + 1)
                    j = len(text) if k < 0 else k + 1
                    continue
                j += 1
            run = text[i:j]
            lead = len(run) - len(run.lstrip(" "))
            sc = size * LATEX_SCALE / TX.EM_PX
            chunks = []
            for chunk, sp in _split_latin(run.strip(" ")):
                tex = TX.convert(chunk) if chunk.strip() else ""
                if tex and maxw and TX.metrics(tex, bold)[0] * sc > maxw * 0.92 and " " in chunk:
                    sub = _split_latin(chunk, fine=True)
                    chunks += [(c2, sp if k == 0 else s2) for k, (c2, s2) in enumerate(sub)]
                else:
                    chunks.append((chunk, sp))
            if ch in TT:                         # 字符串：整段原样用打字机字体，不拆
                chunks = [(run.strip(" "), False)]
            # 片段之间的空格（如 “border {t|aba}”）要保留成词间距
            if chunks and (lead or (i == 0 and trailing)):
                chunks[0] = (chunks[0][0], True)
            for chunk, sp in chunks:
                if ch in TT:
                    tex = TX.texttt(chunk) if chunk else ""
                else:
                    tex = TX.convert(chunk) if chunk.strip() else ""
                if not tex:
                    continue
                w, h, d = TX.metrics(tex, bold)
                p = Piece()
                p.kind, p.tex, p.bold, p.scale, p.color = "tex", tex, bold, sc, col
                p.w = w * sc
                toks.append([p.w, [p], WORDSPACE * size if sp else 0.0, "lat", chunk])
            i = j
        trailing = text.endswith(" ")
    # 标点挤压：两个全角标点相邻（如“），”），前一个只占半个字宽
    for a, b in zip(toks, toks[1:]):
        if a != "\n" and b != "\n" and a[3] == "cjk" and b[3] == "cjk" and a[4] in _CLOSE \
                and b[4] in _CLOSE | _OPEN and a[4] not in "…":
            a[1][0].w = a[0] = a[0] * 0.5
    # 避头尾：标点粘到前一个词；开括号粘到后一个词
    merged = []
    for t in toks:
        if t == "\n":
            merged.append(t)
            continue
        if t[3] == "cjk" and t[4] in _CLOSE and merged and merged[-1] != "\n":
            prev = merged[-1]
            off = prev[0]
            for p in t[1]:
                p.x = off
            prev[1].extend(t[1])
            prev[0] += t[0]
            prev[3] = prev[3] + "+"
            continue
        # 西文的点号、逗号、右括号（如“左.L”的“.L”）也不能放在行首：粘到前面的汉字上
        if t[3] == "lat" and t[4][:1] in _NOSPACE_BEFORE and not t[2] and merged \
                and merged[-1] != "\n" and merged[-1][3].startswith("cjk"):
            prev = merged[-1]
            kern = 0.08 * size
            prev[1][-1].w -= kern
            prev[1].extend(t[1])
            prev[0] += t[0] - kern
            del prev[5:]
            prev.append(("lat", t[4]))       # 结尾按西文算，决定和下一个词的间距
            continue
        merged.append(t)
    out = []
    for t in merged:
        if out and out[-1] != "\n" and t != "\n" and out[-1][3] == "cjk" and out[-1][4] in _OPEN:
            prev = out[-1]
            prev[1].extend(t[1])
            prev[0] += t[0]
            prev[3] = t[3]
            prev[4] = t[4] if len(t) > 4 else ""
            del prev[5:]
            prev.extend(t[5:])
            continue
        out.append(t)
    return out


class Layout:
    """排好的一段文字。lines: [(行宽, [Piece])]，Piece.x 是行内横坐标。"""

    def __init__(self, lines, size, lh):
        self.lines = lines
        self.size = size
        self.lh = lh
        self.w = max((l[0] for l in lines), default=0)
        self.h = len(lines) * size * lh

    def draw(self, canvas, x, y, align="l", alpha=1.0, default=None):
        asc, desc = metrics(self.size)
        line_h = self.size * self.lh
        base0 = (line_h - (desc - asc)) / 2 - asc
        paint = skia.Paint(AntiAlias=True)
        for k, (lw, pieces) in enumerate(self.lines):
            dx = 0 if align == "l" else (self.w - lw) / 2 if align == "c" else self.w - lw
            by = y + k * line_h + base0
            for p in pieces:
                c = p.color if p.color is not None else (default or theme.FG)
                a = c[3] * alpha
                if a <= 0.003:
                    continue
                if p.kind == "font":
                    paint.setColor4f(skia.Color4f(c[0], c[1], c[2], min(1.0, a)))
                    canvas.drawTextBlob(blob(p.font, self.size, p.text), x + dx + p.x, by, paint)
                else:
                    TX.draw(canvas, p.tex, p.bold, x + dx + p.x, by, p.scale, c, alpha)


def _place(tok_pieces, start):
    """把一个词里的 Piece 依次排开，返回词宽。"""
    x = start
    for p in tok_pieces:
        p.x = x
        x += p.w
    return x - start


@functools.lru_cache(20000)
def layout(markup, size, color=None, maxw=None, chain="sans", lh=1.5):
    """排版。多行时避免最后一行只剩一两个字：在行数不变的前提下把行宽收窄一点重排。"""
    L = _layout(markup, size, color, maxw, chain, lh)
    if maxw is None or len(L.lines) < 2 or L.lines[-1][0] >= 3.2 * size:
        return L
    n = len(L.lines)
    w = maxw
    for _ in range(12):
        w -= size
        if w < maxw * 0.7:
            break
        L2 = _layout(markup, size, color, w, chain, lh)
        if len(L2.lines) > n:
            break
        if L2.lines[-1][0] >= 3.2 * size:
            return L2
    return L


def _layout(markup, size, color=None, maxw=None, chain="sans", lh=1.5):
    runs = parse(markup, color, chain)
    toks = _tokens(runs, size, maxw)
    lines = []
    cur, cw, last_kind = [], 0.0, None
    last_punct = False
    last_src = ""

    def push():
        nonlocal cur, cw, last_kind
        lines.append((cw, cur))
        cur, cw, last_kind = [], 0.0, None

    for tok in toks:
        if tok == "\n":
            push()
            continue
        tw, pieces, gap, kind = tok[0], tok[1], tok[2], tok[3]
        # 间距：西文块之间按原文空格；中西文相邻时自动留空（全角标点自带空白，旁边不再留）
        if cur:
            k0 = kind[:3]
            src = tok[4] if len(tok) > 4 else ""
            if last_kind is not None and k0 != last_kind and not last_punct \
                    and not (pieces[0].kind == "font" and pieces[0].text in _OPEN) \
                    and not (k0 == "lat" and src[:1] in _NOSPACE_BEFORE) \
                    and not (last_kind == "lat" and (last_src[-1:] in "([{" or last_src == ".")):
                gap = max(gap, AUTOSPACE * size)
            elif last_kind is not None and k0 != last_kind and (
                    (k0 == "lat" and src[:1] in _NOSPACE_BEFORE)
                    or (last_kind == "lat" and (last_src[-1:] in "([{" or last_src == "."))):
                gap = -0.08 * size          # 西文括号、逗号贴着汉字时收紧一点（汉字字面本身带空白）
        else:
            gap = 0.0
        if maxw is not None and cur and cw + gap + tw > maxw:
            push()
            gap = 0.0
        # 重新计算词内各 piece 的位置
        x0 = cw + gap
        pieces_copy = []
        x = x0
        for p in pieces:
            q = Piece()
            q.kind, q.w, q.font, q.text, q.color = p.kind, p.w, p.font, p.text, p.color
            q.tex, q.bold, q.scale = p.tex, p.bold, p.scale
            q.x = x
            x += p.w
            pieces_copy.append(q)
        cur.extend(pieces_copy)
        cw = x
        last_kind = kind.rstrip("+")[:3]
        if kind.endswith("+"):
            last_kind = "cjk"
        last_punct = kind.endswith("+") or (kind == "cjk" and tok[4] in _CLOSE)
        last_src = tok[4] if len(tok) > 4 else ""
        if len(tok) > 5:
            last_kind, last_src = tok[5]
            last_punct = False
    if cur or not lines:
        push()
    return Layout(lines, size, lh)


@functools.lru_cache(20000)
def balanced(markup, size, maxw, chain="sans", lh=1.5):
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


def refresh():
    """LaTeX 片段编译完以后，清掉用估计宽度排过的版。"""
    layout.cache_clear()
    balanced.cache_clear()


def plain_len(markup):
    """阅读量：一个汉字算 1，其他可见字符算 0.55。"""
    n = 0.0
    for text, _, _ in parse(markup, theme.FG):
        for c in text:
            if c.isspace() or c == "$" or c == "\\":
                continue
            n += 1.0 if _is_cjk(c) else 0.55
    return n
