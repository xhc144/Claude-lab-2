"""工具选项栏（颜色/粗细等）和浮动朗读控制条。"""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
                               QToolButton, QWidget)

from ..config import Settings
from .signature import SignatureDialog, signature_paths
from .widgets import ColorRow, IconButton, Segmented, Spinner, vline

PEN_COLORS = ["#1F2329", "#E5484D", "#F5A524", "#2BA471", "#3D6DF2", "#8E4EC6"]
HL_COLORS = ["#FFD43B", "#7CE38B", "#74C0FC", "#FFA8D5", "#FFA94D"]
LASER_COLORS = ["#FF3B30", "#34C759", "#0A84FF", "#FFCC00"]

HINTS = {
    "select": "拖动选择文字，Ctrl+C 复制；双击选词；右键查看更多操作",
    "hand": "拖动页面浏览；任何工具下按住空格或鼠标中键也能拖动",
    "highlight": "在文字上拖动即可标注；空白处拖动则为荧光笔手绘",
    "pen": "按住拖动书写，Ctrl+Z 撤销",
    "shape": "拖动绘制，按住 Shift 画正方形 / 正圆 / 45° 线",
    "text": "点击页面放置文本框，Ctrl+Enter 或点空白处完成，Esc 取消",
    "note": "点击页面添加便签",
    "sign": "点击页面放置签名，Ctrl+Z 可撤销",
    "eraser": "在批注上点击或拖动擦除（整条擦除）",
    "laser": "移动鼠标显示激光点，按住拖动画出会自动消失的轨迹",
    "read": "点击任意文字，从那一句开始朗读",
}


class OptionsBar(QFrame):
    """根据当前工具显示的第二行选项。"""
    changed = Signal()

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setObjectName("OptionsBar")
        self.settings = settings
        self.setFixedHeight(44)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(14, 4, 14, 4)
        self._lay.setSpacing(10)
        self._content = QWidget()
        self._content_lay = QHBoxLayout(self._content)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        self._content_lay.setSpacing(10)
        self._lay.addWidget(self._content)
        self._lay.addStretch(1)
        self.hint = QLabel("")
        self.hint.setObjectName("Faint")
        self._lay.addWidget(self.hint)
        self.tool = ""

    def _set(self, key, value):
        self.settings.set(key, value)
        self.changed.emit()

    def _clear(self):
        while self._content_lay.count():
            it = self._content_lay.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.deleteLater()

    def _add(self, w):
        self._content_lay.addWidget(w)

    def _caption(self, text):
        lb = QLabel(text)
        lb.setObjectName("Muted")
        self._add(lb)

    def _width_slider(self, key, lo, hi, step=0.5, unit="pt"):
        s = QSlider(Qt.Horizontal)
        s.setFixedWidth(110)
        s.setRange(int(lo / step), int(hi / step))
        s.setValue(int(float(self.settings.get(key)) / step))
        val = QLabel(f"{float(self.settings.get(key)):g} {unit}")
        val.setObjectName("Muted")
        val.setFixedWidth(44)

        def on(v):
            val.setText(f"{v * step:g} {unit}")
            self._set(key, v * step)
        s.valueChanged.connect(on)
        self._add(s)
        self._add(val)

    def show_tool(self, tool: str):
        self.tool = tool
        self._clear()
        self.hint.setText(HINTS.get(tool, ""))
        st = self.settings
        if tool == "pen":
            self._caption("颜色")
            cr = ColorRow(PEN_COLORS, st.get("pen/color"))
            cr.changed.connect(lambda c: self._set("pen/color", c))
            self._add(cr)
            self._add(vline())
            self._caption("粗细")
            self._width_slider("pen/width", 0.5, 12)
        elif tool == "highlight":
            seg = Segmented([("highlight", "高亮"), ("underline", "下划线"), ("strikeout", "删除线"), ("squiggly", "波浪线")],
                            st.get("highlight/kind"))
            seg.changed.connect(lambda k: self._set("highlight/kind", k))
            self._add(seg)
            self._add(vline())
            cr = ColorRow(HL_COLORS + ["#E5484D", "#3D6DF2"], st.get("highlight/color"))
            cr.changed.connect(lambda c: self._set("highlight/color", c))
            self._add(cr)
        elif tool == "shape":
            seg = Segmented([("rect", "矩形"), ("ellipse", "椭圆"), ("line", "直线"), ("arrow", "箭头")],
                            st.get("shape/kind"),
                            icons={"rect": "square", "ellipse": "circle", "line": "line", "arrow": "arrow-line"})
            seg.changed.connect(lambda k: self._set("shape/kind", k))
            self._add(seg)
            self._add(vline())
            cr = ColorRow(PEN_COLORS, st.get("shape/color"))
            cr.changed.connect(lambda c: self._set("shape/color", c))
            self._add(cr)
            self._add(vline())
            self._caption("线宽")
            self._width_slider("shape/width", 0.5, 10)
        elif tool == "text":
            self._caption("字号")
            sp = QSpinBox()
            sp.setRange(6, 72)
            sp.setValue(int(st.get("text/size")))
            sp.setSuffix(" pt")
            sp.setFixedWidth(76)
            sp.valueChanged.connect(lambda v: self._set("text/size", v))
            self._add(sp)
            self._add(vline())
            cr = ColorRow(PEN_COLORS, st.get("text/color"))
            cr.changed.connect(lambda c: self._set("text/color", c))
            self._add(cr)
        elif tool == "note":
            self._caption("颜色")
            cr = ColorRow(["#F5A524", "#FFD43B", "#7CE38B", "#74C0FC", "#FFA8D5"], st.get("note/color"))
            cr.changed.connect(lambda c: self._set("note/color", c))
            self._add(cr)
        elif tool == "sign":
            self._sign_options()
        elif tool == "eraser":
            self._caption("橡皮大小")
            s = QSlider(Qt.Horizontal)
            s.setFixedWidth(110)
            s.setRange(4, 40)
            s.setValue(int(st.get("eraser/size")))
            s.valueChanged.connect(lambda v: self._set("eraser/size", v))
            self._add(s)
        elif tool == "laser":
            self._caption("颜色")
            cr = ColorRow(LASER_COLORS, st.get("laser/color"))
            cr.changed.connect(lambda c: self._set("laser/color", c))
            self._add(cr)
        self.setVisible(tool in ("pen", "highlight", "shape", "text", "note", "sign", "eraser", "laser", "read"))

    def _sign_options(self):
        paths = signature_paths()
        cur = self.settings.get("sign/path") or (paths[0] if paths else "")
        group = QButtonGroup(self._content)
        for path in paths:
            b = QToolButton()
            b.setCheckable(True)
            b.setIcon(QIcon(QPixmap(path)))
            b.setIconSize(QSize(72, 26))
            b.setToolTip("使用这个签名")
            b.setChecked(path == cur)
            b.clicked.connect(lambda _=False, p=path: self._set("sign/path", p))
            group.addButton(b)
            self._add(b)

        def new():
            p = SignatureDialog.create(self.window())
            if p:
                self._set("sign/path", p)
                self.show_tool("sign")

        def remove():
            p = self.settings.get("sign/path")
            if p and os.path.exists(p):
                os.remove(p)
                self._set("sign/path", "")
                self.show_tool("sign")
        nb = QPushButton("新建签名")
        nb.clicked.connect(new)
        self._add(nb)
        if paths:
            db = QPushButton("删除当前")
            db.clicked.connect(remove)
            self._add(db)
        self._add(vline())
        self._caption("宽度")
        self._width_slider("sign/width", 40, 300, step=5)


class ReadBar(QFrame):
    """悬浮在页面底部的朗读控制条。"""
    closeRequested = Signal()
    settingsRequested = Signal()

    RATES = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

    def __init__(self, reader, parent=None):
        super().__init__(parent)
        self.reader = reader
        self.setObjectName("FloatingBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 8, 6)
        lay.setSpacing(4)
        self.icon = IconButton("audio-lines", "朗读", size=18, color_key="accent")
        lay.addWidget(self.icon)
        self.prev_btn = IconButton("skip-back", "上一句")
        self.play_btn = IconButton("pause", "暂停 / 继续 (Ctrl+Shift+Space)")
        self.next_btn = IconButton("skip-forward", "下一句")
        self.stop_btn = IconButton("square", "停止")
        for b in (self.prev_btn, self.play_btn, self.next_btn, self.stop_btn):
            lay.addWidget(b)
        self.prev_btn.clicked.connect(reader.prev)
        self.next_btn.clicked.connect(reader.next)
        self.play_btn.clicked.connect(reader.toggle_pause)
        self.stop_btn.clicked.connect(reader.stop)
        lay.addWidget(vline(18))
        self.status = QLabel("点击页面上的文字开始朗读")
        self.status.setObjectName("Muted")
        self.spinner = Spinner(self, 14)
        self.spinner.hide()
        lay.addSpacing(4)
        lay.addWidget(self.spinner)
        lay.addWidget(self.status)
        lay.addSpacing(6)
        self.rate = QComboBox()
        for r in self.RATES:
            self.rate.addItem(f"{r:g}×", r)
        cur = float(reader.settings.get("tts/rate") or 1.0)
        self.rate.setCurrentIndex(min(range(len(self.RATES)), key=lambda k: abs(self.RATES[k] - cur)))
        self.rate.setToolTip("语速")
        self.rate.setFixedWidth(72)
        self.rate.currentIndexChanged.connect(lambda _: reader.set_rate(self.rate.currentData()))
        lay.addWidget(self.rate)
        self.voice_btn = IconButton("settings", "朗读设置（引擎、音色、千问 Key）", size=16)
        self.voice_btn.clicked.connect(self.settingsRequested.emit)
        lay.addWidget(self.voice_btn)
        self.close_btn = IconButton("x", "关闭朗读", size=16)
        self.close_btn.clicked.connect(self.closeRequested.emit)
        lay.addWidget(self.close_btn)
        reader.stateChanged.connect(self.update_state)
        self.update_state(reader.state)

    def update_state(self, st: str):
        playing = st in ("playing", "loading")
        self.play_btn.set_icon_name("pause" if playing else "play")
        for b in (self.prev_btn, self.next_btn, self.stop_btn, self.play_btn):
            b.setEnabled(st != "idle")
        if st == "loading":
            self.spinner.start()
            self.status.setText("正在合成语音…" if "千问" in self.reader.engine_label() else "准备中…")
        else:
            self.spinner.stop()
            self.status.setText({"idle": "点击页面上的文字开始朗读", "playing": self.reader.engine_label(),
                                 "paused": "已暂停"}.get(st, ""))
        self.adjustSize()
        self.reposition()

    def reposition(self):
        par = self.parentWidget()
        if par:
            self.adjustSize()
            self.move((par.width() - self.width()) // 2, par.height() - self.height() - 22)
