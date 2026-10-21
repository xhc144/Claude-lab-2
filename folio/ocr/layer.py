"""把识别结果写成页面上不可见的文字（渲染模式 3），这样就能搜索、选择、复制和朗读。"""
from __future__ import annotations

import math

import pymupdf

from . import OcrLine


def page_has_text(page: pymupdf.Page) -> bool:
    return any(ch.isalnum() for ch in page.get_text("text"))


def needs_ocr(page: pymupdf.Page) -> bool:
    """有图片、但没有文字的页面。

    先查图片（纯文字的 PDF 很快跳过），再看内容流里有没有文字指令（BT）：
    扫描页通常只有一条画图指令，这样不用真的提取文字（那会解码整张图片，慢很多）。
    """
    if not page.get_images(full=False):
        return False
    try:
        if b"BT" not in page.read_contents() and not page.get_xobjects():
            return True
    except Exception:
        pass
    return not page_has_text(page)


def _font_for(text: str) -> str:
    return "helv" if all(ord(c) < 256 for c in text) else "china-s"


def add_text_layer(page: pymupdf.Page, lines: list[OcrLine]) -> int:
    """lines 的坐标是页面显示方向（已旋转）上的比例坐标。返回写入的行数。"""
    rect = page.rect          # 显示方向的页面大小
    der = page.derotation_matrix
    rotation = page.rotation
    items = []
    for ln in lines:
        text = " ".join(ln.text.split())
        if not text:
            continue
        x0, y0, x1, y1 = ln.box
        x0, x1 = rect.x0 + x0 * rect.width, rect.x0 + x1 * rect.width
        y0, y1 = rect.y0 + y0 * rect.height, rect.y0 + y1 * rect.height
        h, w = y1 - y0, x1 - x0
        if h <= 0.5 or w <= 0.5:
            continue
        if h > w * 1.5 and len(text) > 1:
            continue  # 竖排文字暂不处理
        size = h * 0.9
        base = y1 - h * 0.2
        a = pymupdf.Point(x0, base) * der
        b = pymupdf.Point(x1, base) * der
        angle = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        items.append((a, angle, size, w, text))
    if not items:
        return 0
    # 在未旋转的坐标系里写入，再把文字转到与显示方向一致
    page.set_rotation(0)
    try:
        for a, angle, size, w, text in items:
            font = _font_for(text)
            length = pymupdf.get_text_length(text, fontname=font, fontsize=size)
            if length <= 0:
                continue
            m = pymupdf.Matrix(w / length, 1) * pymupdf.Matrix(-angle)
            page.insert_text(a, text, fontname=font, fontsize=size, render_mode=3, morph=(a, m))
    finally:
        page.set_rotation(rotation)
    return len(items)


def render_for_ocr(page: pymupdf.Page, dpi: int = 220, max_side: int = 3000, gray: bool = True) -> pymupdf.Pixmap:
    """按显示方向渲染（不含批注），长边不超过 max_side。"""
    zoom = dpi / 72
    longest = max(page.rect.width, page.rect.height) * zoom
    if longest > max_side:
        zoom *= max_side / longest
    cs = pymupdf.csGRAY if gray else pymupdf.csRGB
    return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=cs, alpha=False, annots=False)
