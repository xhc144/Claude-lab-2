from __future__ import annotations

import os
import re


class Cancelled(Exception):
    """用户在后台任务中途点了取消。"""


def check_cancel(cancel) -> None:
    if cancel is not None and cancel():
        raise Cancelled()


def parse_page_ranges(spec: str, page_count: int) -> list[int]:
    """把 "1-3,5,8-" 这样的页码表达式解析成从 0 开始的页码列表（保持书写顺序）。

    空字符串表示全部页。支持中文逗号、"~" 和 "—" 作为分隔符。
    """
    spec = (spec or "").strip()
    if not spec:
        return list(range(page_count))
    spec = spec.replace("，", ",").replace("、", ",").replace("~", "-").replace("—", "-").replace("–", "-")
    result: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d*)\s*-\s*(\d*)", part)
        if m:
            a = int(m.group(1)) if m.group(1) else 1
            b = int(m.group(2)) if m.group(2) else page_count
        elif part.isdigit():
            a = b = int(part)
        else:
            raise ValueError(f"无法识别的页码：{part}")
        if a < 1 or b < 1 or a > page_count or b > page_count:
            raise ValueError(f"页码超出范围（共 {page_count} 页）：{part}")
        step = 1 if b >= a else -1
        result.extend(range(a - 1, b - 1 + step, step))
    if not result:
        raise ValueError("没有选中任何页")
    return result


def parse_range_groups(spec: str, page_count: int) -> list[list[int]]:
    """按逗号/分号拆成多组，每组一个页码区间，用于"按范围拆分"。"""
    spec = (spec or "").replace("；", ";").replace("，", ",").replace("、", ",")
    groups = [g for g in re.split(r"[;,\n]", spec) if g.strip()]
    if not groups:
        raise ValueError("请填写页码范围，例如 1-3, 4-10")
    return [parse_page_ranges(g, page_count) for g in groups]


def format_page_ranges(pages: list[int]) -> str:
    """[0,1,2,4] -> "1-3,5"。"""
    if not pages:
        return ""
    pages = sorted(set(pages))
    out = []
    start = prev = pages[0]
    for p in pages[1:] + [None]:
        if p is not None and p == prev + 1:
            prev = p
            continue
        out.append(f"{start + 1}" if start == prev else f"{start + 1}-{prev + 1}")
        if p is not None:
            start = prev = p
    return ",".join(out)


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(n)} B"
            return f"{n:.1f} {unit}" if n < 100 else f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def unique_path(path: str) -> str:
    """文件已存在时追加 (1)、(2)……，避免覆盖。"""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{stem} ({i}){ext}"):
        i += 1
    return f"{stem} ({i}){ext}"


def write_atomic(path: str, data: bytes) -> None:
    """先写临时文件再替换，避免写到一半崩溃把原文件弄坏。"""
    tmp = f"{path}.folio-tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
