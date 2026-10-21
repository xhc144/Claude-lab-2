"""拆分 PDF：每 N 页 / 按页码范围 / 每页一个 / 按大小上限；以及提取指定页。"""
from __future__ import annotations

import os
from typing import Callable

import pymupdf

from .util import check_cancel, format_page_ranges, parse_range_groups, unique_path

SAVE_OPTS = dict(garbage=4, deflate=True, use_objstms=1)


def subset(src: pymupdf.Document, pages: list[int]) -> pymupdf.Document:
    out = pymupdf.open()
    # 连续页一次插入，速度快很多
    run_start = prev = None
    for p in pages + [None]:
        if p is not None and prev is not None and p == prev + 1:
            prev = p
            continue
        if run_start is not None:
            out.insert_pdf(src, from_page=run_start, to_page=prev)
        run_start = prev = p
    return out


def subset_size(src: pymupdf.Document, pages: list[int]) -> int:
    d = subset(src, pages)
    try:
        return len(d.tobytes(**SAVE_OPTS))
    finally:
        d.close()


def plan_split(src: pymupdf.Document, mode: str, value, cancel=None,
               progress: Callable[[float, str], None] | None = None) -> list[list[int]]:
    n = src.page_count
    if mode == "every":
        k = max(1, int(value))
        return [list(range(i, min(i + k, n))) for i in range(0, n, k)]
    if mode == "single":
        return [[i] for i in range(n)]
    if mode == "ranges":
        return parse_range_groups(str(value), n)
    if mode == "size":
        limit = int(value)
        groups: list[list[int]] = []
        start = 0
        while start < n:
            check_cancel(cancel)
            if progress:
                progress(start / n * 0.8, f"计算分组（第 {start + 1} 页）…")
            # 指数扩张 + 二分，找到不超过上限的最大页数
            good, step = 1, 1
            while start + good < n:
                trial = min(n - start, good + step)
                if subset_size(src, list(range(start, start + trial))) <= limit:
                    good, step = trial, step * 2
                else:
                    lo, hi = good, trial - 1
                    while lo < hi:
                        mid = (lo + hi + 1) // 2
                        if subset_size(src, list(range(start, start + mid))) <= limit:
                            lo = mid
                        else:
                            hi = mid - 1
                    good = lo
                    break
            groups.append(list(range(start, start + good)))
            start += good
        return groups
    raise ValueError(f"未知拆分方式：{mode}")


def split_pdf(path: str, out_dir: str, mode: str, value, *, password: str = "",
              progress: Callable[[float, str], None] | None = None, cancel=None) -> list[str]:
    src = pymupdf.open(path)
    if src.needs_pass and not src.authenticate(password):
        raise ValueError("文件已加密，需要密码")
    try:
        groups = plan_split(src, mode, value, cancel, progress)
        stem = os.path.splitext(os.path.basename(path))[0]
        os.makedirs(out_dir, exist_ok=True)
        outputs = []
        for i, pages in enumerate(groups):
            check_cancel(cancel)
            if progress:
                progress(0.8 * (mode == "size") + (i / len(groups)) * (0.2 if mode == "size" else 1.0),
                         f"写出第 {i + 1}/{len(groups)} 个文件…")
            label = format_page_ranges(pages) if len(pages) < src.page_count else "all"
            name = f"{stem}_{i + 1:02d}_p{label}.pdf" if len(label) <= 40 else f"{stem}_{i + 1:02d}.pdf"
            out_path = unique_path(os.path.join(out_dir, name))
            d = subset(src, pages)
            d.save(out_path, **SAVE_OPTS)
            d.close()
            outputs.append(out_path)
        if progress:
            progress(1.0, "完成")
        return outputs
    finally:
        src.close()
