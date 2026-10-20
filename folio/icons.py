"""Lucide 线性图标：按主题颜色着色并缓存。"""
from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def asset_dir() -> str:
    base = getattr(sys, "_MEIPASS", None)  # PyInstaller 打包后
    if base:
        return os.path.join(base, "folio", "assets")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def asset_path(*parts: str) -> str:
    return os.path.join(asset_dir(), *parts)


_svg_cache: dict[str, str] = {}
_pix_cache: dict[tuple, QPixmap] = {}
_tmp_dir = None


def svg_source(name: str) -> str:
    if name not in _svg_cache:
        with open(asset_path("icons", f"{name}.svg"), encoding="utf-8") as f:
            _svg_cache[name] = f.read()
    return _svg_cache[name]


def pixmap(name: str, color: str, size: int = 18, dpr: float = 2.0, stroke: float | None = None) -> QPixmap:
    key = (name, color, size, dpr, stroke)
    if key in _pix_cache:
        return _pix_cache[key]
    src = svg_source(name).replace("currentColor", color)
    if stroke is not None:
        src = src.replace('stroke-width="2"', f'stroke-width="{stroke}"')
    renderer = QSvgRenderer(QByteArray(src.encode("utf-8")))
    px = int(size * dpr)
    img = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p, QRectF(0, 0, px, px))
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(dpr)
    _pix_cache[key] = pm
    return pm


def make_icon(name: str, normal: str, active: str | None = None, disabled: str | None = None,
              size: int = 18, stroke: float | None = None) -> QIcon:
    icon = QIcon()
    icon.addPixmap(pixmap(name, normal, size, stroke=stroke), QIcon.Normal, QIcon.Off)
    icon.addPixmap(pixmap(name, active or normal, size, stroke=stroke), QIcon.Normal, QIcon.On)
    icon.addPixmap(pixmap(name, active or normal, size, stroke=stroke), QIcon.Active, QIcon.On)
    if disabled:
        icon.addPixmap(pixmap(name, disabled, size, stroke=stroke), QIcon.Disabled, QIcon.Off)
        icon.addPixmap(pixmap(name, disabled, size, stroke=stroke), QIcon.Disabled, QIcon.On)
    return icon


def themed(name: str, size: int = 18, color_key: str = "text2", stroke: float | None = None) -> QIcon:
    from .theme import theme

    return make_icon(name, theme.c(color_key), theme.c("accent"), theme.c("text3"), size, stroke)


def themed_file(name: str, color: str) -> str:
    """把着色后的 SVG 写到临时目录，供样式表 url() 使用。"""
    global _tmp_dir
    if _tmp_dir is None:
        _tmp_dir = tempfile.mkdtemp(prefix="folio-icons-")
    safe = color.replace("#", "").replace("(", "").replace(")", "").replace(",", "_").replace(" ", "")
    path = os.path.join(_tmp_dir, f"{name}-{safe}.svg")
    if not os.path.exists(path):
        src = svg_source(name).replace("currentColor", color)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return path.replace("\\", "/")


def app_icon() -> QIcon:
    icon = QIcon()
    renderer = QSvgRenderer(asset_path("folio.svg"))
    for s in (16, 24, 32, 48, 64, 128, 256):
        img = QImage(s, s, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        renderer.render(p, QRectF(0, 0, s, s))
        p.end()
        icon.addPixmap(QPixmap.fromImage(img))
    return icon


def logo_pixmap(size: int, dpr: float = 2.0) -> QPixmap:
    renderer = QSvgRenderer(asset_path("folio.svg"))
    px = int(size * dpr)
    img = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p, QRectF(0, 0, px, px))
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(dpr)
    return pm


ICON_SIZE = QSize(18, 18)
