"""PDF 压缩：先做无损优化，不够再逐级降低图片分辨率/质量，用二分法找到刚好不超过目标大小的档位。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pymupdf

from .util import check_cancel, human_size

# 从高画质到低画质：(目标 DPI, JPEG 质量)
LADDER: list[tuple[int, int]] = [
    (300, 85), (220, 80), (180, 75), (150, 72), (130, 66), (110, 60),
    (96, 55), (84, 50), (72, 45), (60, 40), (50, 35), (40, 30),
]

PRESETS = {
    "light": (220, 80),     # 轻度：基本看不出差别
    "medium": (150, 70),    # 推荐
    "strong": (96, 55),     # 强力：屏幕阅读够用
    "extreme": (60, 40),    # 极限
}


@dataclass
class CompressResult:
    data: bytes
    original_size: int
    size: int
    reached: bool = True
    level: str = ""
    note: str = ""

    @property
    def ratio(self) -> float:
        return self.size / self.original_size if self.original_size else 1.0


Progress = Callable[[float, str], None] | None


def _save(doc: pymupdf.Document) -> bytes:
    return doc.tobytes(garbage=4, clean=True, deflate=True, deflate_images=True,
                       deflate_fonts=True, use_objstms=1)


def lossless(src: bytes) -> bytes:
    doc = pymupdf.open("pdf", src)
    try:
        return _save(doc)
    finally:
        doc.close()


def with_images(base: bytes, dpi: int, quality: int, gray: bool = False) -> bytes:
    doc = pymupdf.open("pdf", base)
    try:
        doc.rewrite_images(dpi_threshold=int(dpi * 1.1) + 1, dpi_target=dpi, quality=quality,
                           lossy=True, lossless=True, bitonal=True, color=True, gray=True,
                           set_to_gray=gray)
        return _save(doc)
    finally:
        doc.close()


def rasterize(base: bytes, dpi: int, quality: int, gray: bool = False, cancel=None) -> bytes:
    """最后手段：把每页渲染成 JPEG 图片。文字将不能再选中和搜索。"""
    src = pymupdf.open("pdf", base)
    out = pymupdf.open()
    try:
        for page in src:
            check_cancel(cancel)
            pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY if gray else pymupdf.csRGB, annots=True)
            img = pix.tobytes("jpeg", jpg_quality=quality)
            np_ = out.new_page(width=page.rect.width, height=page.rect.height)
            np_.insert_image(np_.rect, stream=img)
        return _save(out)
    finally:
        src.close()
        out.close()


def compress_pdf(src: bytes, *, target_bytes: int | None = None, preset: str = "medium",
                 gray: bool = False, allow_rasterize: bool = False,
                 progress: Progress = None, cancel=None) -> CompressResult:
    original = len(src)

    def report(frac: float, msg: str):
        if progress:
            progress(frac, msg)

    report(0.02, "无损优化…")
    base = lossless(src)
    if len(base) > original:  # 极少数文件已高度优化，保留原文件
        base = src
    check_cancel(cancel)

    if target_bytes is None:
        dpi, q = PRESETS.get(preset, PRESETS["medium"])
        report(0.3, f"压缩图片（{dpi} DPI，质量 {q}）…")
        data = with_images(base, dpi, q, gray)
        if len(data) > len(base):
            data = base
        report(1.0, "完成")
        return CompressResult(data, original, len(data), True, f"{dpi} DPI / 质量 {q}")

    if len(base) <= target_bytes and not gray:
        report(1.0, "完成")
        return CompressResult(base, original, len(base), True, "无损优化",
                              "只做了无损优化就已达到目标，画质完全不变。")

    cache: dict[int, bytes] = {}
    steps = [0]

    def attempt(i: int) -> bytes:
        if i not in cache:
            check_cancel(cancel)
            dpi, q = LADDER[i]
            steps[0] += 1
            report(min(0.1 + steps[0] * 0.12, 0.9), f"尝试 {dpi} DPI / 质量 {q}…")
            cache[i] = with_images(base, dpi, q, gray)
        return cache[i]

    last = len(LADDER) - 1
    smallest = attempt(last)
    if len(smallest) > target_bytes:
        best = min([base, smallest], key=len)
        level = "无损优化" if best is base else "{} DPI / 质量 {}".format(*LADDER[last])
        if allow_rasterize:
            for dpi, q in ((110, 55), (90, 45), (72, 40), (60, 32), (48, 28)):
                check_cancel(cancel)
                report(0.92, f"转为图片页面（{dpi} DPI）…")
                data = rasterize(base, dpi, q, gray, cancel)
                if len(data) < len(best):
                    best, level = data, f"整页图片 {dpi} DPI"
                if len(data) <= target_bytes:
                    report(1.0, "完成")
                    return CompressResult(data, original, len(data), True, level,
                                          "已把页面转为图片，文字将不能再选中、搜索或朗读。")
        report(1.0, "完成")
        hint = "可以勾选「转为黑白」，或允许「转为图片页面」再试。" if not (gray and allow_rasterize) else ""
        return CompressResult(best, original, len(best), False, level,
                              f"文件里文字、字体等非图片内容较多，最小只能压到 {human_size(len(best))}。{hint}")

    # 二分：找画质最高（下标最小）且满足目标的档位
    lo, hi = 0, last
    while lo < hi:
        mid = (lo + hi) // 2
        if len(attempt(mid)) <= target_bytes:
            hi = mid
        else:
            lo = mid + 1
    data = attempt(lo)
    report(1.0, "完成")
    return CompressResult(data, original, len(data), True, "{} DPI / 质量 {}".format(*LADDER[lo]))
