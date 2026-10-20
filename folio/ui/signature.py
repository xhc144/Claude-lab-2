"""手写签名：签名板、保存复用、盖到页面上（图片印章批注，可撤销）。"""
from __future__ import annotations

import glob
import os
import time

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..config import cache_dir
from ..theme import theme
from .page_view import smooth_path
from .tools import Tool
from .widgets import ColorRow

MAX_SIGNATURES = 6
INK_COLORS = ["#1F2329", "#1D3FBF", "#C92A2A"]


def signature_paths() -> list[str]:
    files = glob.glob(os.path.join(cache_dir("signatures"), "*.png"))
    return sorted(files, key=os.path.getmtime, reverse=True)


def save_signature(png: bytes) -> str:
    path = os.path.join(cache_dir("signatures"), f"sig-{int(time.time() * 1000)}.png")
    with open(path, "wb") as f:
        f.write(png)
    for old in signature_paths()[MAX_SIGNATURES:]:
        os.remove(old)
    return path


class SignaturePad(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 200)
        self.setCursor(Qt.CrossCursor)
        self.strokes: list[list[QPointF]] = []
        self.color = INK_COLORS[0]
        self.pen_width = 3.2

    def clear(self):
        self.strokes = []
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.strokes.append([e.position()])
            self.update()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self.strokes:
            self.strokes[-1].append(e.position())
            self.update()

    def _draw(self, p: QPainter, scale: float = 1.0, offset: QPointF = QPointF()):
        pen = QPen(QColor(self.color), self.pen_width * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for st in self.strokes:
            pts = [(q - offset) * scale for q in st]
            if len(pts) == 1:
                p.drawPoint(pts[0])
            else:
                p.drawPath(smooth_path(pts))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("white"))
        p.setPen(QPen(QColor(0, 0, 0, 40), 1, Qt.DashLine))
        y = self.height() * 0.72
        p.drawLine(QPointF(24, y), QPointF(self.width() - 24, y))
        if not self.strokes:
            p.setPen(QColor(0, 0, 0, 90))
            p.drawText(self.rect(), Qt.AlignCenter, "在这里用鼠标或手写笔签名")
        self._draw(p)

    def to_png(self) -> bytes | None:
        pts = [q for st in self.strokes for q in st]
        if not pts:
            return None
        pad = self.pen_width * 2
        x0, y0 = min(q.x() for q in pts) - pad, min(q.y() for q in pts) - pad
        x1, y1 = max(q.x() for q in pts) + pad, max(q.y() for q in pts) + pad
        scale = 3.0
        img = QImage(int((x1 - x0) * scale) + 1, int((y1 - y0) * scale) + 1, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        self._draw(p, scale, QPointF(x0, y0))
        p.end()
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        return bytes(ba)


class SignatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建签名")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(12)
        t = QLabel("新建签名")
        t.setObjectName("H2")
        lay.addWidget(t)
        self.pad = SignaturePad()
        self.pad.setStyleSheet(f"border: 1px solid {theme.c('border')};")
        lay.addWidget(self.pad, 1)
        row = QHBoxLayout()
        row.addWidget(QLabel("颜色"))
        colors = ColorRow(INK_COLORS, INK_COLORS[0])
        colors.changed.connect(self._set_color)
        row.addWidget(colors)
        row.addStretch(1)
        clear = QPushButton("清除")
        clear.clicked.connect(self.pad.clear)
        row.addWidget(clear)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("保存签名")
        ok.setProperty("primary", True)
        ok.clicked.connect(self._save)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)
        self.path: str | None = None

    def _set_color(self, c):
        self.pad.color = c
        self.pad.update()

    def _save(self):
        png = self.pad.to_png()
        if png:
            self.path = save_signature(png)
            self.accept()

    @classmethod
    def create(cls, parent) -> str | None:
        d = cls(parent)
        return d.path if d.exec() == QDialog.Accepted else None


class SignTool(Tool):
    name = "sign"

    def __init__(self, view, opts=None):
        super().__init__(view, opts)
        self._pos: QPointF | None = None
        self._img: QImage | None = None
        self._img_path = ""

    def cursor(self):
        return Qt.CrossCursor

    def current_path(self) -> str | None:
        want = self.opts.get("sign/path") or ""
        paths = signature_paths()
        if want in paths:
            return want
        return paths[0] if paths else None

    def _image(self) -> QImage | None:
        path = self.current_path()
        if not path:
            return None
        if path != self._img_path:
            self._img = QImage(path)
            self._img_path = path
        return self._img

    def _size_pt(self, img: QImage) -> tuple[float, float]:
        w = float(self.opts.get("sign/width", 140) or 140)
        return w, w * img.height() / max(1, img.width())

    def move(self, e, hit):
        self._pos = e.position() if hit else None
        self.view.viewport().update()

    def leave(self):
        self._pos = None
        self.view.viewport().update()

    def release(self, e, hit):
        if e.button() != Qt.LeftButton or not hit or not self.editable():
            return
        img = self._image()
        if img is None:
            return
        i, x, y = hit
        w, h = self._size_pt(img)
        a = self.view.unrot(i, x - w / 2, y - h / 2)
        b = self.view.unrot(i, x + w / 2, y + h / 2)
        rect = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        with open(self.current_path(), "rb") as f:
            self.doc.add_image_stamp(i, rect, f.read(), "签名")

    def paint(self, p: QPainter):
        img = self._image()
        if self._pos is None or img is None:
            return
        w, h = self._size_pt(img)
        s = self.view.scale
        r = QRectF(self._pos.x() - w * s / 2, self._pos.y() - h * s / 2, w * s, h * s)
        p.setOpacity(0.6)
        p.drawImage(r, img)
        p.setOpacity(1.0)
        p.setPen(QPen(theme.qc("accent"), 1, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRect(r)
