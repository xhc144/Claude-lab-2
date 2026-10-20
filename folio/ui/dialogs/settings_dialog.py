"""设置：常规、阅读、朗读（千问 / 系统语音）。"""
from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from ...config import Settings
from ...tts import qwen
from ...tts.engines import SystemEngine
from ..widgets import IconButton, Segmented
from .base import section

TEST_TEXT = "你好，这是 Folio 的朗读测试。Hello, this is a voice test."
KEY_URL = "https://bailian.console.aliyun.com/"


class _TestWorker(QThread):
    done = Signal(bytes, str)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params

    def run(self):
        try:
            self.done.emit(qwen.synthesize(TEST_TEXT, **self.params), "")
        except Exception as ex:  # noqa: BLE001
            self.done.emit(b"", str(ex))


def _row(label_text: str, widget, hint: str = "") -> QHBoxLayout:
    r = QHBoxLayout()
    r.setSpacing(12)
    lb = QLabel(label_text)
    lb.setFixedWidth(96)
    r.addWidget(lb)
    if isinstance(widget, QWidget):
        r.addWidget(widget, 1)
    else:
        r.addLayout(widget, 1)
    if hint:
        h = QLabel(hint)
        h.setObjectName("Faint")
        r.addWidget(h)
    return r


class SettingsDialog(QDialog):
    PAGES = [("general", "常规", "settings"), ("reading", "阅读", "book-open"), ("tts", "朗读", "audio-lines")]

    def __init__(self, parent, settings: Settings, page: str = ""):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.resize(760, 560)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("Surface")
        nav.setFixedWidth(180)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 18, 12, 12)
        t = QLabel("设置")
        t.setObjectName("H2")
        t.setContentsMargins(8, 0, 0, 8)
        nl.addWidget(t)
        self.nav = QListWidget()
        for key, text, _ in self.PAGES:
            it = QListWidgetItem(text)
            it.setData(Qt.UserRole, key)
            self.nav.addItem(it)
        nl.addWidget(self.nav, 1)
        root.addWidget(nav)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._general())
        self.stack.addWidget(self._reading())
        self.stack.addWidget(self._tts())
        right.addWidget(self.stack, 1)
        foot = QFrame()
        foot.setObjectName("DialogFooter")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(22, 12, 22, 12)
        fl.addStretch(1)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("保存")
        ok.setProperty("primary", True)
        ok.clicked.connect(self._save)
        fl.addWidget(cancel)
        fl.addWidget(ok)
        right.addWidget(foot)
        rw = QWidget()
        rw.setLayout(right)
        root.addWidget(rw, 1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        keys = [k for k, _, _ in self.PAGES]
        self.nav.setCurrentRow(keys.index(page) if page in keys else 0)
        self._player = None

    def _page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("H2")
        lay.addWidget(t)
        return w, lay

    # ---------------------------------------------------------------- 常规
    def _general(self) -> QWidget:
        w, lay = self._page("常规")
        lay.addWidget(section("界面主题"))
        self.theme = Segmented([("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")], self.settings.get("ui/theme"))
        lay.addWidget(self.theme)
        lay.addSpacing(6)
        lay.addWidget(section("打开文件"))
        self.restore = QCheckBox("打开文件时回到上次阅读的位置")
        self.restore.setChecked(bool(self.settings.get("view/restore_position")))
        lay.addWidget(self.restore)
        if sys.platform == "win32":
            lay.addSpacing(6)
            lay.addWidget(section("默认程序"))
            b = QPushButton("设为默认 PDF 阅读器…")
            b.clicked.connect(self._set_default_app)
            row = QHBoxLayout()
            row.addWidget(b)
            row.addStretch(1)
            lay.addLayout(row)
            hint = QLabel("会把 Folio 注册为 PDF 的打开方式，然后打开 Windows「默认应用」设置，在那里选择 Folio。")
            hint.setObjectName("Faint")
            hint.setWordWrap(True)
            lay.addWidget(hint)
        lay.addStretch(1)
        return w

    def _set_default_app(self):
        from ...platform_win import register_file_association

        ok, msg = register_file_association()
        if ok:
            QDesktopServices.openUrl(QUrl("ms-settings:defaultapps"))
        QMessageBox.information(self, "设为默认", msg)

    # ---------------------------------------------------------------- 阅读
    def _reading(self) -> QWidget:
        w, lay = self._page("阅读")
        lay.addWidget(section("页面颜色"))
        self.tone = Segmented([("normal", "默认"), ("sepia", "护眼（米黄）"), ("night", "夜间（反色）")],
                              self.settings.get("view/tone"))
        lay.addWidget(self.tone)
        lay.addSpacing(6)
        lay.addWidget(section("页面布局"))
        self.double = QCheckBox("默认双页显示")
        self.double.setChecked(self.settings.get("view/layout") == "double")
        lay.addWidget(self.double)
        lay.addStretch(1)
        return w

    # ---------------------------------------------------------------- 朗读
    def _tts(self) -> QWidget:
        w, lay = self._page("朗读")
        st = self.settings
        lay.addWidget(section("语音引擎"))
        self.engine = Segmented([("qwen", "千问 AI 语音（更自然，需联网）"), ("system", "系统语音（离线）")], st.get("tts/engine"))
        self.engine.changed.connect(self._engine_changed)
        lay.addWidget(self.engine)

        self.qwen_box = QWidget()
        ql = QVBoxLayout(self.qwen_box)
        ql.setContentsMargins(0, 6, 0, 0)
        ql.setSpacing(10)
        key_row = QHBoxLayout()
        self.key = QLineEdit(st.get("tts/api_key") or "")
        self.key.setEchoMode(QLineEdit.Password)
        env = os.environ.get("DASHSCOPE_API_KEY", "")
        self.key.setPlaceholderText("sk-…" + ("（已从环境变量 DASHSCOPE_API_KEY 读取）" if env else ""))
        eye = IconButton("eye", "显示 / 隐藏", size=16, checkable=True)
        eye.toggled.connect(lambda on: self.key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        key_row.addWidget(self.key, 1)
        key_row.addWidget(eye)
        get_key = QPushButton("获取 Key")
        get_key.setProperty("flat", True)
        get_key.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(KEY_URL)))
        key_row.addWidget(get_key)
        ql.addLayout(_row("API Key", key_row))
        self.region = QComboBox()
        for k, (text, _) in qwen.REGIONS.items():
            self.region.addItem(text, k)
        self.region.setCurrentIndex(max(0, list(qwen.REGIONS).index(st.get("tts/region")) if st.get("tts/region") in qwen.REGIONS else 0))
        ql.addLayout(_row("服务地域", self.region))
        self.custom_url = QLineEdit(st.get("tts/base_url") or "")
        self.custom_url.setPlaceholderText("https://…（只填到域名，例如 https://dashscope.aliyuncs.com）")
        self.custom_row = QWidget()
        self.custom_row.setLayout(_row("自定义地址", self.custom_url))
        self.custom_row.layout().setContentsMargins(0, 0, 0, 0)
        self.custom_row.setVisible(self.region.currentData() == "custom")
        self.region.currentIndexChanged.connect(lambda _: self.custom_row.setVisible(self.region.currentData() == "custom"))
        ql.addWidget(self.custom_row)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems(qwen.MODELS)
        self.model.setCurrentText(st.get("tts/model"))
        ql.addLayout(_row("模型", self.model))
        self.voice = QComboBox()
        for v, name, desc in qwen.VOICES:
            self.voice.addItem(f"{name}（{v}）· {desc}", v)
        idx = next((k for k, (v, _, _) in enumerate(qwen.VOICES) if v == st.get("tts/voice")), 0)
        self.voice.setCurrentIndex(idx)
        ql.addLayout(_row("音色", self.voice))
        self.lang = QComboBox()
        for k, text in qwen.LANGUAGES:
            self.lang.addItem(text, k)
        self.lang.setCurrentIndex(next((k for k, (v, _) in enumerate(qwen.LANGUAGES) if v == st.get("tts/language")), 0))
        ql.addLayout(_row("语言", self.lang, "单一语言的文档指定语言效果更好"))
        note = QLabel("API Key 只保存在本机。合成的语音会缓存在本地，重复朗读不会再次收费。")
        note.setObjectName("Faint")
        note.setWordWrap(True)
        ql.addWidget(note)
        lay.addWidget(self.qwen_box)

        self.sys_box = QWidget()
        sl = QVBoxLayout(self.sys_box)
        sl.setContentsMargins(0, 6, 0, 0)
        self.sys_voice = QComboBox()
        self.sys_voice.addItem("自动（优先中文）", "")
        for v in SystemEngine.voices():
            self.sys_voice.addItem(v, v)
        cur = st.get("tts/system_voice") or ""
        for k in range(self.sys_voice.count()):
            if self.sys_voice.itemData(k) == cur:
                self.sys_voice.setCurrentIndex(k)
        sl.addLayout(_row("系统音色", self.sys_voice))
        lay.addWidget(self.sys_box)

        lay.addSpacing(4)
        lay.addWidget(section("通用"))
        self.skip = QCheckBox("跳过页眉、页脚和页码")
        self.skip.setChecked(bool(st.get("tts/skip_margins")))
        lay.addWidget(self.skip)
        trow = QHBoxLayout()
        self.test_btn = QPushButton("试听")
        self.test_btn.clicked.connect(self._test)
        self.test_status = QLabel("")
        self.test_status.setObjectName("Muted")
        self.test_status.setWordWrap(True)
        trow.addWidget(self.test_btn)
        trow.addWidget(self.test_status, 1)
        lay.addLayout(trow)
        lay.addStretch(1)
        self._engine_changed(self.engine.value())
        return w

    def _engine_changed(self, k):
        self.qwen_box.setVisible(k == "qwen")
        self.sys_box.setVisible(k == "system")

    def _qwen_params(self) -> dict:
        return dict(api_key=self.key.text().strip() or os.environ.get("DASHSCOPE_API_KEY", ""),
                    model=self.model.currentText().strip(), voice=self.voice.currentData(),
                    language=self.lang.currentData(), region=self.region.currentData(),
                    custom_url=self.custom_url.text().strip())

    def _test(self):
        if self.engine.value() == "system":
            try:
                from PySide6.QtTextToSpeech import QTextToSpeech

                self._sys_tts = QTextToSpeech(self)
                name = self.sys_voice.currentData()
                for v in self._sys_tts.availableVoices():
                    if v.name() == name:
                        self._sys_tts.setVoice(v)
                self._sys_tts.say(TEST_TEXT)
                self.test_status.setText("正在用系统语音播放…")
            except Exception as ex:  # noqa: BLE001
                self.test_status.setText(f"系统语音不可用：{ex}")
            return
        self.test_btn.setEnabled(False)
        self.test_status.setText("正在请求千问语音…")
        self._worker = _TestWorker(self._qwen_params())
        self._worker.done.connect(self._test_done)
        self._worker.start()

    def _test_done(self, data: bytes, err: str):
        self.test_btn.setEnabled(True)
        if err:
            self.test_status.setText(f"⚠ {err}")
            return
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            path = os.path.join(tempfile.gettempdir(), "folio-tts-test.wav")
            with open(path, "wb") as f:
                f.write(data)
            self._out = QAudioOutput(self)
            self._player = QMediaPlayer(self)
            self._player.setAudioOutput(self._out)
            self._player.setSource(QUrl.fromLocalFile(path))
            self._player.play()
            self.test_status.setText("✓ 连接成功，正在播放")
        except Exception as ex:  # noqa: BLE001
            self.test_status.setText(f"合成成功，但播放失败：{ex}")

    # ---------------------------------------------------------------- 保存
    def _save(self):
        st = self.settings
        st.set("ui/theme", self.theme.value())
        st.set("view/restore_position", self.restore.isChecked())
        st.set("view/tone", self.tone.value())
        st.set("view/layout", "double" if self.double.isChecked() else "single")
        st.set("tts/engine", self.engine.value())
        st.set("tts/api_key", self.key.text().strip())
        st.set("tts/region", self.region.currentData())
        st.set("tts/base_url", self.custom_url.text().strip())
        st.set("tts/model", self.model.currentText().strip() or "qwen3-tts-flash")
        st.set("tts/voice", self.voice.currentData())
        st.set("tts/language", self.lang.currentData())
        st.set("tts/system_voice", self.sys_voice.currentData())
        st.set("tts/skip_margins", self.skip.isChecked())
        st.sync()
        parent = self.parent()
        if parent is not None and hasattr(parent, "set_tone"):
            parent.set_tone(self.tone.value())
        self.accept()
