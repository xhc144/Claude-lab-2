"""通用小部件：图标按钮、分段选择、开关、设置卡片、颜色选择、提示气泡、文件列表等。"""
from __future__ import annotations

import os

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QColorDialog, QFrame,
                               QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLayout, QListWidget, QListWidgetItem,
                               QSizePolicy, QToolButton, QVBoxLayout, QWidget)

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


class TabCloseButton(QWidget):
    """文档标签上的关闭按钮。

    不用 QSS 的 ::close-button：Qt 会把它贴着标签右边缘摆放，悬停底色顶到标签圆角上，叉号看起来不在中间。
    这里是一个正方形按钮（图标正好在中间），右边留出和左边文字差不多的空白。
    """
    clicked = Signal()

    def __init__(self, parent=None, tip: str = "关闭标签 (Ctrl+W)"):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(0)
        self.button = IconButton("x", tip, size=14)
        self.button.setObjectName("TabClose")
        self.button.setFixedSize(20, 20)
        self.button.clicked.connect(self.clicked)
        lay.addWidget(self.button)
        self.setFixedSize(28, 20)


class Switch(QCheckBox):
    """开关（Windows 11 风格），用法和 QCheckBox 一样：isChecked()、setChecked()、toggled。"""

    W, H = 40, 22

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._knob = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._slide)
        self.setChecked(checked)
        self._knob = 1.0 if checked else 0.0
        theme.changed.connect(self.update)

    def _get_knob(self) -> float:
        return self._knob

    def _set_knob(self, v: float):
        self._knob = v
        self.update()

    knob = Property(float, _get_knob, _set_knob)

    def _slide(self, on: bool):
        self._anim.stop()
        if not self.isVisible():
            self._set_knob(1.0 if on else 0.0)
            return
        self._anim.setStartValue(self._knob)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def sizeHint(self) -> QSize:
        return QSize(self.W, self.H)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.45)
        track = QRectF(0.5, (self.height() - self.H) / 2 + 0.5, self.W - 1, self.H - 1)
        r = track.height() / 2
        on = self.isChecked()
        if on:
            p.setPen(Qt.NoPen)
            p.setBrush(theme.qc("accent_hover" if self.underMouse() else "accent"))
        else:
            p.setPen(QPen(theme.qc("text3"), 1))
            p.setBrush(theme.qc("hover") if self.underMouse() else Qt.NoBrush)
        p.drawRoundedRect(track, r, r)
        # 关着时圆点小一点、颜色深，打开时是白色的大圆点（和 Windows 11 一样）
        knob_r = 7.0 if on else 5.5
        left, right = track.left() + r, track.right() - r
        cx = left + (right - left) * self._knob
        p.setPen(Qt.NoPen)
        p.setBrush(theme.qc("accent_text") if on else theme.qc("text2"))
        p.drawEllipse(QRectF(cx - knob_r, track.center().y() - knob_r, knob_r * 2, knob_r * 2))


class Card(QFrame):
    """设置页里的一组选项：圆角卡片，每一项之间有一条分隔线。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsCard")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)

    def add(self, item) -> QWidget:
        """加一项（部件或布局，布局会包上统一的内边距）。"""
        if isinstance(item, QLayout):
            w = QWidget()
            item.setContentsMargins(16, 12, 16, 12)
            w.setLayout(item)
            item = w
        if self._lay.count():
            self._lay.addWidget(hline())
        self._lay.addWidget(item)
        return item

    def add_block(self, spacing: int = 10) -> QVBoxLayout:
        """加一块可以自由排版的区域，返回它的布局。"""
        lay = QVBoxLayout()
        lay.setSpacing(spacing)
        self.add(lay)
        return lay

    def add_row(self, title: str, desc: str = "", control=None) -> QWidget:
        """左边标题和说明，右边开关、按钮等控件。"""
        row = QHBoxLayout()
        row.setSpacing(16)
        text = QVBoxLayout()
        text.setSpacing(3)
        text.addWidget(label(title, "RowTitle", wrap=True))
        if desc:
            text.addWidget(label(desc, "Faint", wrap=True))
        row.addLayout(text, 1)
        if isinstance(control, QWidget):
            row.addWidget(control, 0, Qt.AlignVCenter)
        elif control is not None:
            row.addLayout(control)
        w = self.add(row)
        w.text_layout = text  # 以后可以在说明下面再加状态文字
        if isinstance(control, QCheckBox):  # 点整行的文字也能切换开关
            w.mouseReleaseEvent = lambda e, c=control: c.isEnabled() and e.button() == Qt.LeftButton and c.toggle()
            w.setCursor(Qt.PointingHandCursor)
        return w


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


class StatusLabel(QLabel):
    """状态文字：没有内容时不占位置。"""

    def __init__(self, text: str = "", kind: str = "Muted", parent=None):
        super().__init__(parent)
        self.setObjectName(kind)
        self.setWordWrap(True)
        self.setText(text)

    def setText(self, text: str):
        super().setText(text)
        self.setVisible(bool(text))


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
