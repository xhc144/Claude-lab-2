"""逐字提取页面文字及其位置，用于点读、划词选择、高亮和句子切分。

坐标都是 PyMuPDF 的"未旋转页面坐标"，与批注接口一致。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pymupdf

LINE_BREAK = "\x1f"   # 同一段落内的换行
BLOCK_BREAK = "\n"    # 段落（文本块）之间

_CJK = r"⺀-鿿豈-﫿＀-￯　-〿"
_CJK_RE = re.compile(f"[{_CJK}]")
_SPEAKABLE_RE = re.compile(rf"[0-9A-Za-zÀ-ɏЀ-ӿ{_CJK}぀-ヿ가-힯]")

TERMINATORS = set("。！？!?；;…")
CLOSERS = set("”’\"'）)】」』》〕]")
SOFT_BREAKS = set("，,、：:")
MAX_SENTENCE = 180

# 页眉页脚判断：位于页面上下 7% 区域且文字较短的文本块
MARGIN_FRACTION = 0.07
MARGIN_MAX_CHARS = 120


def is_cjk(ch: str) -> bool:
    return bool(ch) and _CJK_RE.match(ch) is not None


@dataclass
class Sentence:
    start: int
    end: int          # 不含
    text: str         # 规范化后用于朗读的文字


@dataclass
class PageText:
    text: str = ""
    rects: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))  # N×4，分隔符为 NaN
    line_ids: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int32))
    margin: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=bool))  # 是否属于页眉页脚
    _sentences: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.text)

    @property
    def empty(self) -> bool:
        return not _SPEAKABLE_RE.search(self.text)

    # ---------- 命中测试 ----------
    def hit(self, x: float, y: float, max_dist: float | None = None) -> int | None:
        """返回离 (x, y) 最近的字符下标；max_dist 为 None 时总是返回最近的。"""
        if not len(self.text):
            return None
        r = self.rects
        dx = np.maximum(np.maximum(r[:, 0] - x, x - r[:, 2]), 0)
        dy = np.maximum(np.maximum(r[:, 1] - y, y - r[:, 3]), 0)
        dist = dx + dy * 3.0  # 垂直方向更敏感，优先同一行
        dist = np.where(np.isnan(dist), np.inf, dist)
        i = int(np.argmin(dist))
        if not np.isfinite(dist[i]):
            return None
        if max_dist is not None and dist[i] > max_dist:
            return None
        return i

    def hit_caret(self, x: float, y: float) -> int | None:
        """划词时用：落在字符右半边就算到下一个位置。"""
        i = self.hit(x, y)
        if i is None:
            return None
        x0, _, x1, _ = self.rects[i]
        return i + 1 if x > (x0 + x1) / 2 else i

    # ---------- 区间 → 矩形 ----------
    def rects_for_range(self, start: int, end: int) -> list[tuple[float, float, float, float]]:
        """把 [start, end) 的字符按行合并成矩形，用于高亮/选择显示和高亮批注。"""
        start, end = max(0, start), min(len(self.text), end)
        out: list[list[float]] = []
        cur_line = None
        for i in range(start, end):
            lid = self.line_ids[i]
            if lid < 0:
                continue
            x0, y0, x1, y1 = self.rects[i]
            if self.text[i].isspace() and (cur_line != lid):
                continue
            if lid == cur_line and out:
                o = out[-1]
                o[0], o[1], o[2], o[3] = min(o[0], x0), min(o[1], y0), max(o[2], x1), max(o[3], y1)
            else:
                out.append([x0, y0, x1, y1])
                cur_line = lid
        return [tuple(o) for o in out if o[2] > o[0] and o[3] > o[1]]

    def range_text(self, start: int, end: int) -> str:
        """复制用：保留换行。"""
        s = self.text[max(0, start):end]
        return s.replace(LINE_BREAK, "\n").strip("\n")

    def word_at(self, i: int) -> tuple[int, int]:
        """双击选词：英文按单词，中文按标点之间的短语。"""
        t = self.text
        if not t or i is None:
            return (0, 0)
        i = min(max(i, 0), len(t) - 1)
        if is_cjk(t[i]):
            ok = lambda c: is_cjk(c) and c not in TERMINATORS and c not in SOFT_BREAKS and c not in "，。、"
        else:
            ok = lambda c: c.isalnum() or c in "_'-"
        if not ok(t[i]):
            return (i, i + 1)
        a = i
        while a > 0 and ok(t[a - 1]):
            a -= 1
        b = i + 1
        while b < len(t) and ok(t[b]):
            b += 1
        return (a, b)

    # ---------- 句子 ----------
    def sentences(self, skip_margins: bool = True) -> list[Sentence]:
        if skip_margins not in self._sentences:
            self._sentences[skip_margins] = split_sentences(self.text, self.margin if skip_margins else None)
        return self._sentences[skip_margins]

    def sentence_index_at(self, char_index: int, skip_margins: bool = True) -> int:
        sents = self.sentences(skip_margins)
        for k, s in enumerate(sents):
            if char_index < s.end:
                return k
        return max(0, len(sents) - 1)


def extract_page_text(page: pymupdf.Page) -> PageText:
    flags = pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP
    data = page.get_text("rawdict", flags=flags)
    chars: list[str] = []
    rects: list[tuple] = []
    lines: list[int] = []
    margin: list[bool] = []
    nan = (np.nan, np.nan, np.nan, np.nan)

    unrot = page.rect * page.derotation_matrix
    page_h = abs(unrot.y1 - unrot.y0) or 1
    top_limit = unrot.y0 + page_h * MARGIN_FRACTION
    bottom_limit = unrot.y1 - page_h * MARGIN_FRACTION

    line_id = 0
    prev_line = None  # 上一个文本块最后一行的 (x0, y0, y1, 字号)
    prev_margin = False
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        block_chars = sum(len(sp["chars"]) for ln in block["lines"] for sp in ln["spans"])
        if block_chars == 0:
            continue
        bx0, by0, bx1, by1 = block["bbox"]
        in_margin = block_chars <= MARGIN_MAX_CHARS and (by1 <= top_limit or by0 >= bottom_limit)
        first = _line_info(block["lines"][0])
        if chars and chars[-1] != BLOCK_BREAK:
            if prev_line and not in_margin and not prev_margin and _continues(prev_line, first):
                # 很多 PDF 每行都是一个独立文本块：行距正常、字号相同就当作同一段的换行
                chars.append(LINE_BREAK); rects.append(nan); lines.append(-1); margin.append(False)
            else:
                # 段落分隔符归属上一段（它是上一句的结尾）
                chars.append(BLOCK_BREAK); rects.append(nan); lines.append(-1); margin.append(margin[-1])
        prev_line = _line_info(block["lines"][-1])
        prev_margin = in_margin
        first_line = True
        for ln in block["lines"]:
            line_chars = [ch for sp in ln["spans"] for ch in sp["chars"]]
            if not line_chars:
                continue
            if not first_line:
                chars.append(LINE_BREAK); rects.append(nan); lines.append(-1); margin.append(in_margin)
            first_line = False
            for ch in line_chars:
                c = ch["c"]
                if c in ("\n", "\r"):
                    continue
                chars.append(c)
                rects.append(tuple(ch["bbox"]))
                lines.append(line_id)
                margin.append(in_margin)
            line_id += 1
    return PageText(
        text="".join(chars),
        rects=np.array(rects, dtype=float).reshape(-1, 4),
        line_ids=np.array(lines, dtype=np.int32),
        margin=np.array(margin, dtype=bool),
    )


def _line_info(line: dict) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = line["bbox"]
    sizes = [sp.get("size", 0) for sp in line.get("spans", []) if sp.get("chars")]
    return x0, y0, y1, max(sizes) if sizes else (y1 - y0)


def _continues(prev: tuple, cur: tuple) -> bool:
    """cur 这一行是否紧接着 prev 那一行（同一段落）。"""
    px0, py0, py1, psize = prev
    cx0, cy0, cy1, csize = cur
    h = max(py1 - py0, 1.0)
    if psize and abs(csize - psize) > psize * 0.15:
        return False
    gap = cy0 - py1
    return -h * 0.2 <= gap <= h * 0.9 and abs(cx0 - px0) <= h * 4


def speech_text(raw: str) -> str:
    """把页面原文整理成适合朗读的句子：去断行连字符、中文断行不加空格等。"""
    s = re.sub(rf"(?<=[A-Za-z])-{LINE_BREAK}(?=[a-z])", "", raw)
    s = re.sub(rf"(?<=[{_CJK}]){LINE_BREAK}|{LINE_BREAK}(?=[{_CJK}])", "", s)
    s = s.replace(LINE_BREAK, " ").replace(BLOCK_BREAK, " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_period_end(text: str, i: int) -> bool:
    """英文句点是否为句末：后面是空白/换行/结尾，且前面不是单个大写字母缩写（如 "U.S."）。"""
    nxt = text[i + 1] if i + 1 < len(text) else ""
    if nxt and not (nxt.isspace() or nxt in (LINE_BREAK, BLOCK_BREAK) or nxt in CLOSERS):
        return False
    j = i - 1
    while j >= 0 and text[j].isalpha():
        j -= 1
    word = text[j + 1:i]
    if len(word) == 1 and word.isupper():
        return False
    if word.lower() in {"mr", "mrs", "ms", "dr", "prof", "vs", "etc", "fig", "eq", "no", "e.g", "i.e", "al"}:
        return False
    return True


def split_sentences(text: str, margin: np.ndarray | None = None) -> list[Sentence]:
    bounds: list[tuple[int, int]] = []
    start = 0
    n = len(text)
    i = 0
    while i < n:
        c = text[i]
        end = None
        if c == BLOCK_BREAK:
            end = i + 1
        elif c in TERMINATORS or (c == "." and _is_period_end(text, i)):
            j = i + 1
            while j < n and (text[j] in TERMINATORS or text[j] in CLOSERS or text[j] == "."):
                j += 1
            end = j
        if end is not None:
            bounds.append((start, end))
            start = end
            i = end
            continue
        i += 1
    if start < n:
        bounds.append((start, n))

    out: list[Sentence] = []
    for a, b in bounds:
        for a2, b2 in _split_long(text, a, b):
            if margin is not None and len(margin) == n and margin[a2:b2].all():
                continue
            spoken = speech_text(text[a2:b2])
            if spoken and _SPEAKABLE_RE.search(spoken):
                out.append(Sentence(a2, b2, spoken))
    return out


def _split_long(text: str, a: int, b: int) -> list[tuple[int, int]]:
    """过长的句子在逗号或空格处再切开，降低合成延迟。"""
    parts = []
    while b - a > MAX_SENTENCE:
        cut = None
        for k in range(a + MAX_SENTENCE, a + MAX_SENTENCE // 3, -1):
            if text[k - 1] in SOFT_BREAKS:
                cut = k
                break
        if cut is None:
            for k in range(a + MAX_SENTENCE, a + MAX_SENTENCE // 3, -1):
                if text[k - 1].isspace() or text[k - 1] == LINE_BREAK:
                    cut = k
                    break
        cut = cut or a + MAX_SENTENCE
        parts.append((a, cut))
        a = cut
    parts.append((a, b))
    return parts
