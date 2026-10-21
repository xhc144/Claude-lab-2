"""图片 / 长图转 PDF。长图按页面比例切分，并尽量在空白行处下刀，避免把一行字切成两半。"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pymupdf
from PIL import Image, ImageOps

from .util import check_cancel

try:  # 可选：支持 iPhone 的 HEIC 照片
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}

PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "A3": (841.89, 1190.55),
    "A5": (419.53, 595.28),
    "Letter": (612.0, 792.0),
    "fit": None,  # 与图片同尺寸
}

# 画质档位：(JPEG 质量, 最大宽度像素)；None 表示保留原图
QUALITY = {
    "original": None,
    "high": (90, 2480),
    "medium": (78, 1754),
    "small": (62, 1240),
}


@dataclass
class ImageOptions:
    page_size: str = "A4"
    orientation: str = "auto"      # auto / portrait / landscape
    margin: float = 0.0            # 页边距（pt）
    split_long: bool = True
    smart_split: bool = True
    overlap: int = 0               # 切分时上下页重叠的像素
    quality: str = "high"


def load_image(path: str) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def row_busyness(img: Image.Image) -> np.ndarray:
    """每一行像素的"忙碌度"（灰度标准差）。纯色/空白行接近 0。"""
    w, h = img.size
    small = img.convert("L")
    if w > 400:
        small = small.resize((400, h), Image.BILINEAR)
    arr = np.asarray(small, dtype=np.float32)
    return arr.std(axis=1)


def find_cuts(busy: np.ndarray, slice_h: int, smart: bool = True) -> list[int]:
    """返回切分位置（像素行号），不含 0 和总高度。"""
    total = len(busy)
    cuts: list[int] = []
    prev = 0
    window = max(8, int(slice_h * 0.22))
    while total - prev > slice_h:
        target = prev + slice_h
        cut = target
        if smart:
            lo = max(prev + slice_h // 2, target - window)
            seg = busy[lo:target]
            if len(seg):
                blank = seg < 2.5
                if blank.any():
                    # 找最靠近 target 的一段空白，在它中间切
                    idx = np.nonzero(blank)[0]
                    end = idx[-1]
                    start = end
                    while start - 1 >= 0 and blank[start - 1]:
                        start -= 1
                    cut = lo + (start + end) // 2 + 1
                else:
                    m = seg.min()
                    cand = np.nonzero(seg <= m * 1.05 + 0.5)[0]
                    cut = lo + int(cand[-1]) + 1
        cuts.append(int(cut))
        prev = int(cut)
    return cuts


def _encode(img: Image.Image, quality: str, src_path: str | None, whole: bool) -> bytes:
    q = QUALITY.get(quality)
    if q is None:
        if whole and src_path and src_path.lower().endswith((".jpg", ".jpeg")):
            with open(src_path, "rb") as f:
                return f.read()  # 原样嵌入 JPEG，不再二次压缩
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        return buf.getvalue()
    jpeg_q, max_w = q
    if img.width > max_w:
        img = img.resize((max_w, max(1, round(img.height * max_w / img.width))), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=jpeg_q, optimize=True, progressive=True)
    return buf.getvalue()


def _page_dims(opts: ImageOptions, img_w: int, img_h: int, dpi: float) -> tuple[float, float]:
    size = PAGE_SIZES.get(opts.page_size)
    if size is None:
        w = img_w * 72.0 / dpi + 2 * opts.margin
        h = img_h * 72.0 / dpi + 2 * opts.margin
        return w, h
    w, h = size
    landscape = opts.orientation == "landscape" or (opts.orientation == "auto" and img_w > img_h)
    return (h, w) if landscape else (w, h)


def _long_layout(opts: ImageOptions, img_w: int, dpi: float) -> tuple[float, float, int]:
    """长图模式下的内容区宽高（pt）以及每页对应的原图像素高度。长图默认用纵向页面。"""
    if opts.page_size == "fit":
        cw = img_w * 72.0 / dpi
        ref_w, ref_h = PAGE_SIZES["A4"]
        ch = cw * (ref_h - 2 * opts.margin) / (ref_w - 2 * opts.margin)
    else:
        pw, ph = PAGE_SIZES[opts.page_size]
        if opts.orientation == "landscape":
            pw, ph = ph, pw
        cw, ch = pw - 2 * opts.margin, ph - 2 * opts.margin
    return cw, ch, max(1, int(img_w * ch / cw))


def plan_slices(img_w: int, img_h: int, opts: ImageOptions) -> int:
    """预估一张图会被切成几页（用于界面预览）。"""
    _, _, slice_h = _long_layout(opts, img_w, 96)
    if not opts.split_long or img_h <= slice_h * 1.15:
        return 1
    return max(1, int(np.ceil(img_h / slice_h)))


def add_image_pages(doc: pymupdf.Document, path: str, opts: ImageOptions, cancel=None) -> int:
    img = load_image(path)
    w, h = img.size
    dpi = float((img.info.get("dpi") or (96, 96))[0] or 96)
    dpi = dpi if 50 <= dpi <= 1200 else 96

    cw, ch, slice_h = _long_layout(opts, w, dpi)
    is_long = opts.split_long and h > slice_h * 1.15

    if not is_long:
        pw, ph = _page_dims(opts, w, h, dpi)
        page = doc.new_page(width=pw, height=ph)
        box = pymupdf.Rect(opts.margin, opts.margin, pw - opts.margin, ph - opts.margin)
        page.insert_image(box, stream=_encode(img, opts.quality, path, True), keep_proportion=True)
        return 1

    cuts = find_cuts(row_busyness(img), slice_h, opts.smart_split)
    edges = [0] + cuts + [h]
    if opts.page_size == "fit":
        pw = cw + 2 * opts.margin
        ph = ch + 2 * opts.margin
    else:
        pw, ph = PAGE_SIZES[opts.page_size]
        if opts.orientation == "landscape":
            pw, ph = ph, pw
    count = 0
    for k in range(len(edges) - 1):
        check_cancel(cancel)
        top = max(0, edges[k] - (opts.overlap if k else 0))
        bottom = edges[k + 1]
        piece = img.crop((0, top, w, bottom))
        page = doc.new_page(width=pw, height=ph)
        draw_h = (bottom - top) * cw / w
        box = pymupdf.Rect(opts.margin, opts.margin, opts.margin + cw, opts.margin + min(draw_h, ch))
        page.insert_image(box, stream=_encode(piece, opts.quality, None, False), keep_proportion=True)
        count += 1
    return count


def images_to_pdf(paths: list[str], opts: ImageOptions,
                  progress: Callable[[float, str], None] | None = None, cancel=None) -> pymupdf.Document:
    doc = pymupdf.open()
    for i, p in enumerate(paths):
        check_cancel(cancel)
        if progress:
            progress(i / max(1, len(paths)), f"处理第 {i + 1}/{len(paths)} 张图片…")
        add_image_pages(doc, p, opts, cancel)
    if progress:
        progress(1.0, "完成")
    return doc
