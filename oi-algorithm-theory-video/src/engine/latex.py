"""用真正的 LaTeX 排公式和西文。

画面上所有非中文的片段（字母、数字、符号、公式）都交给 LaTeX（Latin Modern 字体）排版：
latex → dvi → dvipng 输出白色透明底的 PNG，记下宽度、基线位置，绘制时再按需要的颜色和字号缩放。

- 富文本里写 $…$ 的部分原样当作数学公式；
- 其他西文片段自动转换：单个字母是变量（斜体），多字母单词用正体（\\text），
  max/min/log/gcd 等变成算子，Unicode 的 ≤ ≥ → × · ∞ 上下标等换成对应命令，x1 这样的写法变成 x₁。
- 一集里用到的所有片段先收集起来，一次编译（几百个片段不到一秒），结果按内容缓存在 build/tex/。
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import skia

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "tex"
DPI = 1200
PT = 8                            # 用 8pt 的字形（小字号设计的笔画更粗、字距更宽，屏幕上更清楚）
EM_PX = DPI * PT / 72.27          # 1em 对应的像素

PREAMBLE = r"""\documentclass[12pt]{article}
\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb}
\usepackage[active,tightpage]{preview}
\DeclareMathOperator{\lcm}{lcm}
\PreviewBorder=0pt
\begin{document}
"""

# ------------------------------------------------------------------ Unicode → LaTeX
SYM = {
    "−": "-", "–": "\\text{--}", "—": "\\text{---}", "×": "\\times ", "·": "\\cdot ", "÷": "\\div ",
    "≤": "\\le ", "≥": "\\ge ", "≠": "\\ne ", "≈": "\\approx ", "≡": "\\equiv ", "∝": "\\propto ",
    "→": "\\to ", "←": "\\leftarrow ", "↔": "\\leftrightarrow ", "⇒": "\\Rightarrow ", "⇔": "\\Leftrightarrow ",
    "⇐": "\\Leftarrow ", "⇝": "\\rightsquigarrow ", "↦": "\\mapsto ", "↑": "\\uparrow ", "↓": "\\downarrow ",
    "∞": "\\infty ", "∑": "\\sum ", "Σ": "\\sum ", "∏": "\\prod ", "∈": "\\in ", "∉": "\\notin ",
    "∪": "\\cup ", "∩": "\\cap ", "⊆": "\\subseteq ", "⊂": "\\subset ", "∅": "\\varnothing ", "⊕": "\\oplus ",
    "∀": "\\forall ", "∃": "\\exists ", "¬": "\\neg ", "∧": "\\wedge ", "∨": "\\vee ", "±": "\\pm ",
    "⌊": "\\lfloor ", "⌋": "\\rfloor ", "⌈": "\\lceil ", "⌉": "\\rceil ", "′": "'", "″": "''",
    "…": "\\ldots ", "⋯": "\\cdots ", "∣": "\\mid ", "∤": "\\nmid ", "∘": "\\circ ", "⊥": "\\perp ", "∠": "\\angle ",
    "α": "\\alpha ", "β": "\\beta ", "γ": "\\gamma ", "δ": "\\delta ", "ε": "\\varepsilon ", "θ": "\\theta ",
    "λ": "\\lambda ", "μ": "\\mu ", "π": "\\pi ", "σ": "\\sigma ", "φ": "\\varphi ", "ω": "\\omega ",
    "Δ": "\\Delta ", "Ω": "\\Omega ", "Γ": "\\Gamma ", "Λ": "\\Lambda ", "Φ": "\\Phi ",
    "✓": "\\checkmark ", "✗": "\\times ", "★": "\\star ", "•": "\\bullet ", "°": "^{\\circ}",
    "#": "\\#", "%": "\\%", "&": "\\&", "~": "\\sim ", "$": "\\$", "<": "<", ">": ">",
    "{": "\\{", "}": "\\}", "\\": "\\backslash ", "\"": "''", "`": "`",
}
SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
       "ᵢ": "i", "ⱼ": "j", "ₖ": "k", "ₙ": "n", "ₘ": "m", "ₓ": "x", "₊": "+", "₋": "-", "ᵤ": "u", "ᵥ": "v",
       "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₗ": "l", "ₛ": "s", "ₜ": "t", "ₚ": "p", "ₕ": "h"}
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
       "ⁿ": "n", "⁺": "+", "⁻": "-", "ᵏ": "k", "ⁱ": "i", "ᵐ": "m", "ᵖ": "p", "ᵃ": "a", "ᵇ": "b", "ᶜ": "c",
       "ᵈ": "d", "ᵉ": "e", "ᶠ": "f", "ᵍ": "g", "ʰ": "h", "ʲ": "j", "ˡ": "l", "ᵒ": "o", "ʳ": "r", "ˢ": "s",
       "ᵗ": "t", "ᵘ": "u", "ᵛ": "v", "ʷ": "w", "ˣ": "x", "ʸ": "y", "ᶻ": "z", "⁽": "(", "⁾": ")"}
OPS = {"max", "min", "log", "gcd", "lcm", "lg", "ln", "exp", "sin", "cos", "tan", "det", "deg", "lim", "sup",
       "inf", "arg"}
RELS = set("=<>≤≥≠≈≡→←↔⇒⇔⇐⇝↦∈∉⊆⊂∝")
WORDS2 = {"mx", "mn", "ok", "an", "am"}     # 看起来像两个变量相乘、其实是标识符或单词的两字母词
BINS = set("+−-×·÷∪∩⊕±∘")


DIGITS = set("0123456789")


def is_word_char(c):
    """西文字母（含 König 里的 ö 这类带变音符号的拉丁字母）。"""
    return c.isalpha() and ord(c) < 0x250


def convert(run):
    """把一段西文/符号转成数学模式里的 LaTeX。"""
    if "(mod " in run:                               # 同余式里的 (mod m)
        run = re.sub(r"\(mod ((?:[^()]|\([^()]*\))+)\)", lambda m: "$(\\operatorname{mod} " + convert(m.group(1)) + ")$", run)
    out = []
    i, n = 0, len(run)
    op_tail = False         # 刚输出过 \log、\sum 这类算子（后面可能还跟着上下标）：后面的空格不要
    while i < n:
        c = run[i]
        tail, op_tail = op_tail, False
        if c == "$":                                 # 显式公式
            j = run.find("$", i + 1)
            if j < 0:
                j = n
            out.append(run[i + 1:j])
            i = j + 1
            continue
        if is_word_char(c):
            j = i
            while j < n and (is_word_char(run[j]) or (run[j] in "-–" and j + 1 < n and is_word_char(run[j + 1])
                                                       and j > i and is_word_char(run[j - 1]))):
                j += 1
            word = run[i:j]
            if word in OPS or word == "mod":
                if out and out[-1] == "\\ ":
                    out.pop()
                out.append("\\bmod " if word == "mod" else "\\" + word + " ")
                op_tail = True
                i = j
                continue
            elif len(word) == 2 and word not in WORDS2 and word[0] in "abcmnkpqx" and word[1] in "xyzbnmkpqBVWLK":
                out.append(word)               # ax、by、O(nm)、O(qB) 这类是两个变量相乘，不是单词
            elif len(word) == 1:
                out.append(word)
                # x1 → x_1（单个字母后面紧跟数字）
                k = j
                while k < n and run[k] in DIGITS:
                    k += 1
                if k > j and (k >= n or not is_word_char(run[k])):
                    out.append("_{" + run[j:k] + "}")
                    j = k
            else:
                out.append("\\text{" + word.replace("–", "--") + "}")
            i = j
            continue
        if c in DIGITS:
            j = i
            while j < n and (run[j] in DIGITS or (run[j] == "." and j + 1 < n and run[j + 1] in DIGITS)):
                j += 1
            out.append(run[i:j])
            i = j
            continue
        if c in SUB:
            j = i
            while j < n and run[j] in SUB:
                j += 1
            out.append("_{" + "".join(SUB[x] for x in run[i:j]) + "}")
            i = j
            op_tail = tail     # 上下标不改变 op_tail
            continue
        if c in SUP:
            j = i
            while j < n and run[j] in SUP:
                j += 1
            out.append("^{" + "".join(SUP[x] for x in run[i:j]) + "}")
            i = j
            op_tail = tail     # 上下标不改变 op_tail
            continue
        if c == "√":
            # √n、√(n+1)、√q
            j = i + 1
            if j < n and run[j] == "(":
                depth, k = 0, j
                while k < n:
                    depth += run[k] == "("
                    depth -= run[k] == ")"
                    k += 1
                    if depth == 0:
                        break
                out.append("\\sqrt{" + convert(run[j + 1:k - 1]) + "}")
                i = k
            else:
                k = j
                while k < n and (run[k] in DIGITS or is_word_char(run[k])):
                    k += 1
                out.append("\\sqrt{" + convert(run[j:k]) + "}")
                i = k
            continue
        if c in ("_", "^") and i + 1 < n and run[i + 1] == "{":
            depth, k = 0, i + 1
            while k < n:
                depth += run[k] == "{"
                depth -= run[k] == "}"
                k += 1
                if depth == 0:
                    break
            out.append(c + "{" + convert(run[i + 2:k - 1]) + "}")
            i = k
            op_tail = tail     # 上下标不改变 op_tail
            continue
        if c in ("_", "^"):
            out.append(c)
            i += 1
            continue
        if c == " ":
            # 空格：挨着运算符、括号、逗号的丢掉（数学排版自带间距），否则留一个中等空白
            prev = run[i - 1] if i > 0 else ""
            j = i
            while j < n and run[j] == " ":
                j += 1
            nxt = run[j] if j < n else ""
            nxt_word = re.match(r"[A-Za-z]+", run[j:])
            if (prev and nxt and prev not in RELS | BINS | set("([{,;:/|") and nxt not in RELS | BINS | set(")]},;:/|")
                    and not tail and not (nxt_word and nxt_word.group(0) in OPS | {"mod"})):
                out.append("\\ ")
            i = j
            continue
        if c == "-" and i > 0 and (run[i - 1] in DIGITS or is_word_char(run[i - 1])) \
                and re.match(r"[A-Za-z]{2,}", run[i + 1:]):
            out.append("\\text{-}")          # 2-SAT、k-th 这样的连字符
            i += 1
            continue
        if c in SYM:
            out.append(SYM[c])
            op_tail = c in "Σ∑∏"
            i += 1
            continue
        if c == "'":
            out.append("'")
            i += 1
            continue
        if ord(c) < 128:
            out.append(c)
            i += 1
            continue
        # 其他字符：当作文本
        out.append("\\text{" + c + "}")
        i += 1
    return "".join(out).strip()


_TT_ESC = {"#": "\\#", "$": "\\$", "%": "\\%", "&": "\\&", "_": "\\_", "{": "\\{", "}": "\\}",
           "~": "\\textasciitilde{}", "^": "\\textasciicircum{}", "\\": "\\textbackslash{}", " ": "\\ "}


def texttt(s):
    """字符串原样用打字机字体排（字符串题里的字符、模式串）。"""
    return "\\texttt{" + "".join(_TT_ESC.get(c, c) for c in s) + "}"


# ------------------------------------------------------------------ 编译与缓存
_index = None
_pending = {}
FAILED = []
_bad = set()
_images = {}


def _key(tex, bold):
    return hashlib.sha1(((("B" if bold else "N") + tex)).encode()).hexdigest()[:16]


def _load_index():
    global _index
    if _index is None:
        CACHE.mkdir(parents=True, exist_ok=True)
        f = CACHE / "index.json"
        _index = json.loads(f.read_text()) if f.exists() else {}
    return _index


def _save_index():
    """并行渲染时几个进程会同时写：先合并磁盘上已有的，再原子地替换。"""
    f = CACHE / "index.json"
    try:
        disk = json.loads(f.read_text()) if f.exists() else {}
    except ValueError:
        disk = {}
    disk.update({k: v for k, v in _index.items() if k not in _bad})
    _index.update(disk)
    tmp = CACHE / f"index.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(disk))
    tmp.replace(f)


def metrics(tex, bold=False):
    """(宽, 基线以上高度, 基线以下深度)，单位是 1200dpi 下的像素；还没编译时返回估计值并登记待编译。"""
    idx = _load_index()
    k = _key(tex, bold)
    if k in idx:
        return tuple(idx[k][:3])
    _pending[k] = (tex, bold)
    est = 0.55 * EM_PX * max(1, len(re.sub(r"\\[a-zA-Z]+|[{}_^ ]", "x", tex)) * 0.8)
    return (est, 0.75 * EM_PX, 0.25 * EM_PX)


def has_pending():
    return bool(_pending)


def compile_pending():
    """把登记的片段一次编译完。编译出错时逐个重试，实在不行就当作纯文本。"""
    if not _pending:
        return 0
    items = list(_pending.items())
    _pending.clear()
    _compile_split(items)
    _save_index()
    return len(items)


def _compile_split(items):
    """整批编译；失败就对半分开再试，最后剩下的单个坏片段改成纯文本。"""
    if _compile(items):
        return
    if len(items) > 1:
        h = len(items) // 2
        _compile_split(items[:h])
        _compile_split(items[h:])
        return
    k, (tex, bold) = items[0]
    print(f"  [LaTeX] 无法编译，改为纯文本：{tex}")
    FAILED.append(tex)
    _bad.add(k)                     # 退回纯文本的结果不写进磁盘缓存，下次还会重试
    safe = "\\text{" + re.sub(r"[^A-Za-z0-9 ()\[\],.:;=+*/<>!?'-]", "", tex.replace("\\", " ")) + "}"
    if not _compile([(k, (safe, bold))]):
        _index[k] = [0, 0, 0]


def _compile(items):
    with tempfile.TemporaryDirectory(dir=str(CACHE)) as d:
        d = Path(d)
        body = []
        for k, (tex, bold) in items:
            body.append("\\begin{preview}{\\fontsize{%d}{%d}\\selectfont " % (PT, PT + 2) + ("\\bfseries\\boldmath" if bold else "") + "$" + tex
                        + "$}\\end{preview}\n")
        (d / "t.tex").write_text(PREAMBLE + "".join(body) + "\\end{document}\n")
        r = subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"], cwd=d,
                           capture_output=True, text=True)
        if r.returncode != 0 or not (d / "t.dvi").exists():
            return False
        r = subprocess.run(["dvipng", "-D", str(DPI), "-bg", "Transparent", "-fg", "rgb 1 1 1", "--depth",
                            "--height", "-q", "-o", "p%d.png", "t.dvi"], cwd=d, capture_output=True, text=True)
        dims = re.findall(r"depth=(-?\d+) height=(-?\d+)", r.stdout)
        if len(dims) != len(items):
            return False
        from PIL import Image
        for (k, _), (dep, hei), pg in zip(items, dims, range(1, len(items) + 1)):
            src = d / f"p{pg}.png"
            dst = CACHE / f"{k}.png"
            src.replace(dst)
            w = Image.open(dst).size[0]
            _index[k] = [w, int(hei), int(dep)]
    return True


def image(tex, bold=False):
    k = _key(tex, bold)
    if k not in _images:
        idx = _load_index()
        if k not in idx:
            _pending[k] = (tex, bold)
            compile_pending()
        if idx[k][0] == 0:
            _images[k] = None
            return None
        data = skia.Data.MakeFromFileName(str(CACHE / f"{k}.png"))
        img = skia.Image.MakeFromEncoded(data)
        _images[k] = img.withDefaultMipmaps() if img is not None else None
    return _images[k]


_SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def draw(canvas, tex, bold, x, baseline, scale, color, alpha):
    img = image(tex, bold)
    if img is None:
        return
    w, h, dpt = metrics(tex, bold)
    p = skia.Paint(AntiAlias=True)
    p.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(color[0], color[1], color[2], 1.0).toColor(),
                                             skia.BlendMode.kSrcIn))
    p.setAlphaf(max(0.0, min(1.0, color[3] * alpha)))
    dst = skia.Rect.MakeXYWH(x, baseline - h * scale, img.width() * scale, img.height() * scale)
    canvas.drawImageRect(img, dst, _SAMPLING, p)
