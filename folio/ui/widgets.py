"""通用小部件：图标按钮、分段选择、颜色选择、提示气泡、文件列表等。"""
from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QColorDialog, QFrame, QGraphicsOpacityEffect,
                               QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSizePolicy, QToolButton,
                               QVBoxLayout, QWidget)

from ..icons import themed
from ..theme import theme


class IconButton(QToolButton):
    """跟随主题自动换色的图标按钮。"""

    def __init__(self, icon: str, tip: str = "", parent=None, checkable: bool = False, size: int = 18,
                 text: str = "", color_key: str = "text2"):
        super().__init__(parent)
        self._icon_name = icon
        self._size = size
        self._color_key = color_key
        self.setCheckable(checkable)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        if tip:
            self.setToolTip(tip)
        if text:
            self.setText(text)
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.setProperty("textButton", True)
        self.setIconSize(QSize(size, size))
        self.retheme()
        theme.changed.connect(self.retheme)

    def set_icon_name(self, name: str):
        self._icon_name = name
        self.retheme()

    def retheme(self):
        self.setIcon(themed(self._icon_name, self._size, self._color_key))


def hline() -> QFrame:
    f = QFrame()
    f.setObjectName("Hairline")
    return f


def vline(height: int = 20) -> QFrame:
    f = QFrame()
    f.setObjectName("VHairline")
    f.setFixedHeight(height)
    return f


def label(text: str, kind: str = "", wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    if kind:
        lb.setObjectName(kind)
    lb.setWordWrap(wrap)
    return lb


class Segmented(QFrame):
    """分段选择器（类似 iOS 的 segmented control）。"""
    changed = Signal(str)

    def __init__(self, options: list[tuple[str, str]], current: str | None = None, parent=None,
                 icons: dict | None = None):
        super().__init__(parent)
        self.setObjectName("Segmented")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QToolButton] = {}
        for key, text in options:
            if icons and key in icons:
                b = IconButton(icons[key], text, checkable=True, size=16)
            else:
                b = QToolButton()
                b.setText(text)
                b.setCheckable(True)
                b.setCursor(Qt.PointingHandCursor)
                b.setFocusPolicy(Qt.NoFocus)
            self._group.addButton(b)
            self._buttons[key] = b
            lay.addWidget(b)
            b.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
        self.set_value(current or options[0][0])

    def value(self) -> str:
        for k, b in self._buttons.items():
            if b.isChecked():
                return k
        return ""

    def set_value(self, key: str):
        if key in self._buttons:
            self._buttons[key].setChecked(True)


class Swatch(QToolButton):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setCheckable(True)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolTip(color)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(4, 4, -4, -4)
        if self.isChecked():
            p.setPen(QPen(theme.qc("accent"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(self.rect().adjusted(1, 1, -1, -1))
        elif self.underMouse():
            p.setPen(QPen(theme.qc("border_strong"), 1.5))
            p.drawEllipse(self.rect().adjusted(1, 1, -1, -1))
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.setBrush(QColor(self.color))
        p.drawEllipse(r)


class ColorRow(QWidget):
    """一排预设颜色 + 自定义颜色。"""
    changed = Signal(str)

    def __init__(self, colors: list[str], current: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        self._group = QButtonGroup(self)
        self._swatches: list[Swatch] = []
        for c in colors:
            s = Swatch(c)
            self._group.addButton(s)
            self._swatches.append(s)
            lay.addWidget(s)
            s.clicked.connect(lambda _=False, sw=s: self._pick(sw.color))
        self._custom = Swatch(current if current not in colors else "#888888")
        self._custom.setToolTip("自定义颜色")
        self._group.addButton(self._custom)
        self._custom.clicked.connect(self._choose_custom)
        lay.addSpacing(2)
        lay.addWidget(self._custom)
        self._custom.setVisible(current not in colors)
        self._more = IconButton("palette", "自定义颜色…", size=16)
        self._more.clicked.connect(self._choose_custom)
        lay.addWidget(self._more)
        self.set_value(current)

    def set_value(self, color: str):
        for s in self._swatches:
            if s.color.lower() == color.lower():
                s.setChecked(True)
                self._custom.setVisible(False)
                return
        self._custom.color = color
        self._custom.setVisible(True)
        self._custom.setChecked(True)
        self._custom.update()

    def _pick(self, color: str):
        self.changed.emit(color)

    def _choose_custom(self):
        c = QColorDialog.getColor(QColor(self._custom.color), self.window(), "选择颜色")
        if c.isValid():
            self.set_value(c.name())
            self.changed.emit(c.name())


class Toast(QFrame):
    """页面底部的短暂提示。"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 9, 14, 9)
        self._label = QLabel()
        lay.addWidget(self._label)
        self._fx = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self.hide()

    def show_message(self, text: str, ms: int = 2600):
        self._label.setText(text)
        self.adjustSize()
        par = self.parentWidget()
        self.move((par.width() - self.width()) // 2, par.height() - self.height() - 72)
        self.raise_()
        self.show()
        self._anim.stop()
        self._anim.setStartValue(self._fx.opacity() if self.isVisible() else 0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(ms)

    def _fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._hide_once)
        self._anim.start()

    def _hide_once(self):
        try:
            self._anim.finished.disconnect(self._hide_once)
        except Exception:
            pass
        if self._fx.opacity() < 0.05:
            self.hide()


class ElidedLabel(QLabel):
    def __init__(self, text: str = "", parent=None, mode=Qt.ElideMiddle):
        super().__init__(parent)
        self._full = text
        self._mode = mode
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setText(text)

    def setText(self, text: str):
        self._full = text
        self.setToolTip(text)
        self._update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update()

    def _update(self):
        fm = QFontMetrics(self.font())
        super().setText(fm.elidedText(self._full, self._mode, max(10, self.width())))


class FileList(QListWidget):
    """可拖入文件、拖动排序的文件列表。"""
    filesDropped = Signal(list)
    changed = Signal()

    def __init__(self, exts: set[str] | None = None, parent=None):
        super().__init__(parent)
        self.exts = exts
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setSpacing(2)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.model().rowsMoved.connect(lambda *a: self.changed.emit())

    def accepts(self, path: str) -> bool:
        return self.exts is None or os.path.splitext(path)[1].lower() in self.exts

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            paths = [p for p in paths if os.path.isfile(p) and self.accepts(p)]
            if paths:
                self.filesDropped.emit(paths)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)
            self.changed.emit()

    def paths(self) -> list[str]:
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.count() == 0:
            p = QPainter(self.viewport())
            p.setPen(theme.qc("text3"))
            p.drawText(self.viewport().rect(), Qt.AlignCenter, "把文件拖到这里，或点击上方「添加文件」")


def file_item(path: str, subtitle: str = "") -> QListWidgetItem:
    it = QListWidgetItem()
    it.setData(Qt.UserRole, path)
    name = os.path.basename(path)
    it.setText(f"{name}\n{subtitle}" if subtitle else name)
    it.setToolTip(path)
    it.setSizeHint(QSize(0, 46 if subtitle else 32))
    return it


class Spinner(QWidget):
    """简单的加载转圈。"""

    def __init__(self, parent=None, size: int = 16):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._timer.start(40)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(theme.qc("accent"), 2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        r = self.rect().adjusted(2, 2, -2, -2)
        p.drawArc(r, -self._angle * 16, 270 * 16)


def vbox(*widgets, margins=(0, 0, 0, 0), spacing=8) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        elif isinstance(w, int):
            lay.addSpacing(w)
        elif isinstance(w, QWidget):
            lay.addWidget(w)
        else:
            lay.addLayout(w)
    return lay


def hbox(*widgets, margins=(0, 0, 0, 0), spacing=8) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        elif isinstance(w, int):
            lay.addSpacing(w)
        elif isinstance(w, QWidget):
            lay.addWidget(w)
        else:
            lay.addLayout(w)
    return lay
