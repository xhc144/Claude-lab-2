"""文字识别（OCR）：系统自带引擎或 AI 视觉模型识别扫描页，再写入不可见的文字层。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OcrLine:
    text: str
    box: tuple[float, float, float, float]  # 相对图片宽高的比例坐标 (x0, y0, x1, y1)，0~1，左上角为原点


class OcrError(RuntimeError):
    pass


def clamp_box(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float] | None:
    x0, x1 = sorted((max(0.0, min(1.0, x0)), max(0.0, min(1.0, x1))))
    y0, y1 = sorted((max(0.0, min(1.0, y0)), max(0.0, min(1.0, y1))))
    if x1 - x0 < 1e-4 or y1 - y0 < 1e-4:
        return None
    return x0, y0, x1, y1


def order_lines(lines: list[OcrLine]) -> list[OcrLine]:
    """按栏整理阅读顺序：与上一行横向重叠、纵向紧挨着的行归入同一栏，读完一栏再读下一栏。"""
    columns: list[list[OcrLine]] = []
    for ln in lines:
        x0, y0, x1, y1 = ln.box
        h = max(y1 - y0, 1e-3)
        target = None
        for col in columns:
            px0, py0, px1, py1 = col[-1].box
            overlap = min(x1, px1) - max(x0, px0)
            if overlap > 0.3 * min(x1 - x0, px1 - px0) and -h <= y0 - py1 <= 2.5 * h:
                target = col
                break
        if target is None:
            columns.append([ln])
        else:
            target.append(ln)
    return [ln for col in columns for ln in col]
