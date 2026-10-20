"""把 PDF、图片、电子书、Office 文档合并成一个 PDF，可按文件生成书签。"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Callable

import pymupdf

from .images import IMAGE_EXTS, ImageOptions, add_image_pages
from .office import OFFICE_EXTS, office_to_pdf
from .util import check_cancel, parse_page_ranges

EBOOK_EXTS = {".epub", ".xps", ".oxps", ".cbz", ".fb2", ".mobi", ".svg", ".txt"}
PDF_EXTS = {".pdf"}
ALL_EXTS = PDF_EXTS | IMAGE_EXTS | OFFICE_EXTS | EBOOK_EXTS


@dataclass
class MergeItem:
    path: str
    pages: str = ""          # 页码范围，空表示全部
    password: str = ""


def kind_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in PDF_EXTS:
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in OFFICE_EXTS:
        return "office"
    if ext in EBOOK_EXTS:
        return "ebook"
    return "unknown"


def open_as_pdf(path: str, password: str = "", tmpdir: str | None = None,
                image_opts: ImageOptions | None = None) -> pymupdf.Document:
    k = kind_of(path)
    if k == "pdf":
        doc = pymupdf.open(path)
        if doc.needs_pass and not doc.authenticate(password):
            raise ValueError(f"{os.path.basename(path)} 已加密，需要密码")
        return doc
    if k == "image":
        doc = pymupdf.open()
        add_image_pages(doc, path, image_opts or ImageOptions())
        return doc
    if k == "office":
        return pymupdf.open(office_to_pdf(path, tmpdir))
    src = pymupdf.open(path)
    pdf_bytes = src.convert_to_pdf()
    src.close()
    return pymupdf.open("pdf", pdf_bytes)


def merge_files(items: list[MergeItem], *, bookmarks: bool = True,
                image_opts: ImageOptions | None = None,
                progress: Callable[[float, str], None] | None = None, cancel=None) -> pymupdf.Document:
    out = pymupdf.open()
    toc: list[list] = []
    tmpdir = tempfile.mkdtemp(prefix="folio-merge-")
    try:
        for i, item in enumerate(items):
            check_cancel(cancel)
            name = os.path.basename(item.path)
            if progress:
                progress(i / max(1, len(items)), f"合并 {name}（{i + 1}/{len(items)}）…")
            src = open_as_pdf(item.path, item.password, tmpdir, image_opts)
            try:
                pages = parse_page_ranges(item.pages, src.page_count)
                start = out.page_count
                if pages == list(range(src.page_count)):
                    out.insert_pdf(src)
                    mapping = {p: start + p for p in pages}
                else:
                    mapping = {}
                    for p in pages:
                        out.insert_pdf(src, from_page=p, to_page=p)
                        mapping.setdefault(p, out.page_count - 1)
                if bookmarks:
                    toc.append([1, os.path.splitext(name)[0], start + 1])
                    for lvl, title, pno, *_ in src.get_toc(simple=True):
                        if pno - 1 in mapping:
                            toc.append([lvl + 1, title, mapping[pno - 1] + 1])
            finally:
                src.close()
        if bookmarks and toc:
            # set_toc 要求层级连续，修正跳级
            fixed, prev = [], 0
            for lvl, title, pno in toc:
                lvl = min(lvl, prev + 1)
                fixed.append([lvl, title, pno])
                prev = lvl
            out.set_toc(fixed)
        if progress:
            progress(1.0, "完成")
        return out
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
