"""设置里与 AI 有关的三页：AI 中台（连接管理）、朗读、文字识别。

AI 中台页保存一份正在编辑的连接列表，朗读和文字识别页从中选择连接，
所以新加的连接不用先保存就能在另外两页里选到。
"""
from __future__ import annotations

import os
import tempfile

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMenu, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ...ai import client
from ...ai.hub import PRESETS, Connection, Hub, dashscope_host, new_id
from ...config import Settings
from ...tts import qwen
from ...tts.engines import OPENAI_VOICES, SystemEngine
from ..widgets import Card, IconButton, StatusLabel, Switch, label
from .base import Worker, section

TEST_TEXT = "你好，这是 Folio 的朗读测试。Hello, this is a voice test."


def page(title: str, subtitle: str = "") -> tuple[QWidget, QVBoxLayout]:
    """设置里的一页：标题、说明，下面是一组组卡片；内容多时可以滚动。返回 (整页部件, 放内容的布局)。"""
    inner = QWidget()
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(28, 24, 28, 24)
    lay.setSpacing(8)
    lay.addWidget(label(title, "PageTitle"))
    if subtitle:
        lay.addWidget(label(subtitle, "Muted", wrap=True))
    lay.addSpacing(8)
    scroll = QScrollArea()
    scroll.setObjectName("PageScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(inner)
    return scroll, lay


def group(lay: QVBoxLayout, title: str) -> Card:
    """在页面里加一组：小标题 + 卡片。"""
    if lay.count() > 2:
        lay.addSpacing(10)
    lay.addWidget(section(title))
    card = Card()
    lay.addWidget(card)
    return card


def row(label_text: str, widget, hint: str = "", width: int = 96) -> QHBoxLayout:
    r = QHBoxLayout()
    r.setSpacing(12)
    lb = QLabel(label_text)
    lb.setFixedWidth(width)
    r.addWidget(lb)
    if isinstance(widget, QWidget):
        r.addWidget(widget, 1)
    else:
        r.addLayout(widget, 1)
    if hint:
        r.addWidget(label(hint, "Faint"))
    return r


def model_combo(current: str, suggestions, extra=()) -> QComboBox:
    cb = QComboBox()
    cb.setEditable(True)
    cb.setInsertPolicy(QComboBox.NoInsert)
    fill_models(cb, suggestions, extra)
    cb.setCurrentText(current or (list(suggestions)[0] if suggestions else ""))
    return cb


def fill_models(cb: QComboBox, suggestions, extra=()):
    cur = cb.currentText()
    cb.blockSignals(True)
    cb.clear()
    seen = set()
    for m in list(suggestions) + list(extra):
        if m and m not in seen:
            seen.add(m)
            cb.addItem(m)
    cb.setCurrentText(cur)
    cb.blockSignals(False)


# ================================================================= AI 中台
class HubPage(QWidget):
    connectionsChanged = Signal()

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.hub = Hub(settings)
        self.conns: list[Connection] = self.hub.connections()
        self.models: dict[str, list[str]] = {}
        self._worker = None
        self._loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)
        root.addWidget(label("AI 中台", "PageTitle"))
        root.addWidget(label("在这里统一填写各家 AI 服务的地址和 Key，朗读、文字识别、AI 校对都从这里选用，不用重复填写。"
                             "云端服务和本机运行的模型（Ollama、LM Studio）都可以。", "Muted", wrap=True))
        root.addSpacing(8)

        body = QHBoxLayout()
        body.setSpacing(12)
        list_card = Card()
        list_card.setFixedWidth(240)
        left = list_card.add_block(8)
        left.setContentsMargins(8, 8, 8, 10)
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._select)
        left.addWidget(self.list, 1)
        btns = QHBoxLayout()
        btns.setContentsMargins(4, 0, 4, 0)
        add = QPushButton("添加")
        menu = QMenu(add)
        for key, p in PRESETS.items():
            menu.addAction(p.name, lambda k=key: self._add(k))
        add.setMenu(menu)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._delete)
        btns.addWidget(add)
        btns.addWidget(self.del_btn)
        btns.addStretch(1)
        left.addLayout(btns)
        body.addWidget(list_card)

        self.editor = Card()
        el = self.editor.add_block(10)
        el.setContentsMargins(18, 16, 18, 16)
        self.kind = label("", "Muted")
        el.addLayout(row("类型", self.kind, width=72))
        self.name = QLineEdit()
        self.name.textEdited.connect(lambda t: self._edit("name", t))
        el.addLayout(row("名称", self.name, width=72))
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://…/v1")
        self.url.textEdited.connect(lambda t: self._edit("base_url", t.strip()))
        el.addLayout(row("服务地址", self.url, width=72))
        key_row = QHBoxLayout()
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.Password)
        self.key.textEdited.connect(lambda t: self._edit("api_key", t.strip()))
        eye = IconButton("eye", "显示 / 隐藏", size=16, checkable=True)
        eye.toggled.connect(lambda on: self.key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        self.get_key = QPushButton("获取 Key")
        self.get_key.setProperty("flat", True)
        self.get_key.clicked.connect(self._open_key_page)
        key_row.addWidget(self.key, 1)
        key_row.addWidget(eye)
        key_row.addWidget(self.get_key)
        el.addLayout(row("API Key", key_row, width=72))
        self.note = label("", "Faint", wrap=True)
        el.addWidget(self.note)
        trow = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test)
        self.test_status = label("", "Muted", wrap=True)
        trow.addWidget(self.test_btn, 0, Qt.AlignTop)
        trow.addWidget(self.test_status, 1)
        el.addLayout(trow)
        el.addStretch(1)
        el.addWidget(label("API Key 只保存在本机的设置文件里。没有填写时会读取对应的环境变量"
                           "（例如 DASHSCOPE_API_KEY、DEEPSEEK_API_KEY）。", "Faint", wrap=True))
        body.addWidget(self.editor, 1)
        root.addLayout(body, 1)

        self._fill_list()
        self.list.setCurrentRow(0)

    # ---------- 列表 ----------
    def _item_text(self, c: Connection) -> str:
        return f"{c.name or '未命名'}\n{c.status()}"

    def _fill_list(self):
        self.list.blockSignals(True)
        self.list.clear()
        for c in self.conns:
            it = QListWidgetItem(self._item_text(c))
            it.setData(Qt.UserRole, c.id)
            self.list.addItem(it)
        self.list.blockSignals(False)

    def current(self) -> Connection | None:
        r = self.list.currentRow()
        return self.conns[r] if 0 <= r < len(self.conns) else None

    def get(self, cid: str | None) -> Connection | None:
        return next((c for c in self.conns if c.id == cid), None)

    def _select(self, r: int):
        c = self.current()
        self.editor.setEnabled(c is not None)
        self.del_btn.setEnabled(c is not None)
        if c is None:
            return
        self._loading = True
        p = c.p
        self.kind.setText(p.name + ("（本机）" if c.local else ""))
        self.name.setText(c.name)
        self.url.setText(c.base_url)
        self.url.setCursorPosition(0)
        self.key.setText(c.api_key)
        if c.local:
            self.key.setPlaceholderText("本机服务一般不需要 Key")
        elif p.env and os.environ.get(p.env):
            self.key.setPlaceholderText("已读取环境变量里的 Key")
            self.key.setToolTip(f"没有填写时使用环境变量 {p.env}")
        else:
            self.key.setPlaceholderText("sk-…")
        self.get_key.setVisible(bool(p.key_url))
        self.get_key.setText("下载" if c.local else "获取 Key")
        self.note.setText(p.note)
        self.note.setVisible(bool(p.note))
        models = self.models.get(c.id)
        self.test_status.setText(f"✓ 可用模型 {len(models)} 个" if models else "")
        self._loading = False

    def _edit(self, attr: str, value: str):
        c = self.current()
        if c is None or self._loading:
            return
        setattr(c, attr, value)
        self.models.pop(c.id, None)
        self.list.currentItem().setText(self._item_text(c))
        if attr == "name":
            self.connectionsChanged.emit()

    def _add(self, key: str):
        c = Connection.from_preset(key, new_id())
        names = {x.name for x in self.conns}
        base, n = c.name, 2
        while c.name in names:
            c.name = f"{base} {n}"
            n += 1
        self.conns.append(c)
        self._fill_list()
        self.list.setCurrentRow(len(self.conns) - 1)
        self.connectionsChanged.emit()
        (self.url if key == "custom" else self.key).setFocus()

    def _delete(self):
        c = self.current()
        if c is None:
            return
        if QMessageBox.question(self, "删除连接", f"删除「{c.name}」？用到它的功能会改回默认设置。") != QMessageBox.Yes:
            return
        r = self.list.currentRow()
        self.conns.pop(r)
        self._fill_list()
        self.list.setCurrentRow(min(r, len(self.conns) - 1))
        self.connectionsChanged.emit()

    def _open_key_page(self):
        c = self.current()
        if c and c.p.key_url:
            QDesktopServices.openUrl(QUrl(c.p.key_url))

    # ---------- 测试 ----------
    def _test(self):
        c = self.current()
        if c is None:
            return
        conn = Connection.from_dict(c.to_dict())
        self.test_btn.setEnabled(False)
        self.test_status.setText("正在连接…")
        self._worker = Worker(lambda progress, cancel: client.list_models(conn), self)
        self._worker.done.connect(lambda models, cid=c.id: self._test_done(cid, models, ""))
        self._worker.failed.connect(lambda err, cid=c.id: self._test_done(cid, None, err))
        self._worker.start()

    def _test_done(self, cid: str, models, err: str):
        self.test_btn.setEnabled(True)
        c = self.current()
        if err:
            if "（404）" in err:
                err = "服务可以访问，但没有提供模型列表，请在用到它的地方手动填写模型名。"
            msg = f"⚠ {err}"
        else:
            self.models[cid] = list(models)
            preview = "、".join(models[:6]) + (" 等" if len(models) > 6 else "")
            msg = f"✓ 连接成功，可用模型 {len(models)} 个：{preview}" if models else "✓ 连接成功"
            self.connectionsChanged.emit()
        if c is not None and c.id == cid:
            self.test_status.setText(msg)

    def save(self):
        for c in self.conns:
            c.name = c.name.strip() or c.p.name
        self.hub.save(self.conns)


# ================================================================= 朗读
class TtsPage(QWidget):
    openHub = Signal()

    def __init__(self, settings: Settings, hub: HubPage):
        super().__init__()
        self.settings = settings
        self.hub = hub
        st = settings
        w, lay = page("朗读")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(w)

        src = group(lay, "语音来源").add_block()
        self.source = QComboBox()
        src.addLayout(row("使用", self.source))
        self.source.currentIndexChanged.connect(self._source_changed)
        self.key_hint = QHBoxLayout()
        self.key_label = label("", "Faint", wrap=True)
        self.key_hint.addWidget(self.key_label, 1)
        go = QPushButton("打开 AI 中台")
        go.setProperty("flat", True)
        go.clicked.connect(self.openHub.emit)
        self.key_hint.addWidget(go)
        src.addLayout(self.key_hint)

        # 千问
        self.qwen_box = QWidget()
        ql = QVBoxLayout(self.qwen_box)
        ql.setContentsMargins(0, 4, 0, 0)
        ql.setSpacing(10)
        self.q_model = model_combo(st.get("tts/model"), qwen.MODELS)
        ql.addLayout(row("模型", self.q_model))
        self.q_voice = QComboBox()
        for v, name, desc in qwen.VOICES:
            self.q_voice.addItem(f"{name}（{v}）· {desc}", v)
        self.q_voice.setCurrentIndex(next((k for k, (v, _, _) in enumerate(qwen.VOICES) if v == st.get("tts/voice")), 0))
        ql.addLayout(row("音色", self.q_voice))
        self.q_lang = QComboBox()
        for k, text in qwen.LANGUAGES:
            self.q_lang.addItem(text, k)
        self.q_lang.setCurrentIndex(next((k for k, (v, _) in enumerate(qwen.LANGUAGES) if v == st.get("tts/language")), 0))
        ql.addLayout(row("语言", self.q_lang, "单一语言的文档指定语言效果更好"))
        src.addWidget(self.qwen_box)

        # OpenAI 兼容
        self.oa_box = QWidget()
        ol = QVBoxLayout(self.oa_box)
        ol.setContentsMargins(0, 4, 0, 0)
        ol.setSpacing(10)
        self.oa_model = model_combo(st.get("tts/oa_model"), ())
        ol.addLayout(row("模型", self.oa_model))
        self.oa_voice = model_combo(st.get("tts/oa_voice") or "alloy", OPENAI_VOICES)
        ol.addLayout(row("音色", self.oa_voice, "本地语音服务请填它支持的音色名"))
        src.addWidget(self.oa_box)

        # 系统
        self.sys_box = QWidget()
        sl = QVBoxLayout(self.sys_box)
        sl.setContentsMargins(0, 4, 0, 0)
        self.sys_voice = QComboBox()
        self.sys_voice.addItem("自动（优先中文）", "")
        for v in SystemEngine.voices():
            self.sys_voice.addItem(v, v)
        cur = st.get("tts/system_voice") or ""
        for k in range(self.sys_voice.count()):
            if self.sys_voice.itemData(k) == cur:
                self.sys_voice.setCurrentIndex(k)
        sl.addLayout(row("系统音色", self.sys_voice))
        src.addWidget(self.sys_box)

        card = group(lay, "通用")
        self.skip = Switch(bool(st.get("tts/skip_margins")))
        card.add_row("跳过页眉、页脚和页码", "朗读时不读每页顶部和底部重复出现的文字。", self.skip)
        self.test_btn = QPushButton("试听")
        self.test_btn.clicked.connect(self._test)
        test_row = card.add_row("试听", "用上面选的语音读一句测试文字。合成的语音会缓存在本地，同一段重复朗读不会再次收费。",
                                self.test_btn)
        self.test_status = StatusLabel()
        test_row.text_layout.addWidget(self.test_status)
        lay.addStretch(1)
        self.reload(st.get("tts/engine"))
        hub.connectionsChanged.connect(lambda: self.reload(self.source.currentData()))
        self._player = None

    def reload(self, want: str | None):
        self.source.blockSignals(True)
        self.source.clear()
        for c in self.hub.conns:
            if c.tts:
                self.source.addItem(f"{c.name}（AI 语音）", c.id)
        self.source.addItem("系统语音（离线，不需要联网）", "system")
        idx = self.source.findData(want)
        self.source.setCurrentIndex(idx if idx >= 0 else 0)
        self.source.blockSignals(False)
        self._source_changed()

    def conn(self) -> Connection | None:
        return self.hub.get(self.source.currentData())

    def _source_changed(self, *_):
        c = self.conn()
        kind = c.tts if c else "system"
        self.qwen_box.setVisible(kind == "qwen")
        self.oa_box.setVisible(kind == "openai")
        self.sys_box.setVisible(kind == "system")
        if c is None:
            self.key_label.setText("使用操作系统自带的语音，离线可用。Windows 自带中文语音；Linux 需要安装 speech-dispatcher。")
        elif c.ready:
            self.key_label.setText(f"使用「{c.name}」连接（地址和 Key 在 AI 中台里设置）。")
        else:
            self.key_label.setText(f"⚠ 「{c.name}」还没有填写 API Key，请先到 AI 中台填写。")
        if kind == "openai":
            fill_models(self.oa_model, c.p.tts_models, [m for m in self.hub.models.get(c.id, []) if "tts" in m.lower()])
            if not self.oa_model.currentText() and c.p.tts_models:
                self.oa_model.setCurrentText(c.p.tts_models[0])

    def _test(self):
        c = self.conn()
        if c is None:
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
        conn = Connection.from_dict(c.to_dict())
        if c.tts == "qwen":
            params = dict(api_key=conn.key(), model=self.q_model.currentText().strip(), voice=self.q_voice.currentData(),
                          language=self.q_lang.currentData(), host=dashscope_host(conn.base_url))
            fn = lambda p, cancel: qwen.synthesize(TEST_TEXT, **params)  # noqa: E731
        else:
            model, voice = self.oa_model.currentText().strip(), self.oa_voice.currentText().strip()
            fn = lambda p, cancel: client.speech(conn, model, voice, TEST_TEXT)  # noqa: E731
        self.test_btn.setEnabled(False)
        self.test_status.setText(f"正在请求 {conn.name}…")
        self._worker = Worker(fn, self)
        self._worker.done.connect(lambda data: self._test_done(data, ""))
        self._worker.failed.connect(lambda err: self._test_done(b"", err))
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

    def save(self):
        st = self.settings
        st.set("tts/engine", self.source.currentData() or "system")
        st.set("tts/model", self.q_model.currentText().strip() or "qwen3-tts-flash")
        st.set("tts/voice", self.q_voice.currentData())
        st.set("tts/language", self.q_lang.currentData())
        st.set("tts/oa_model", self.oa_model.currentText().strip())
        st.set("tts/oa_voice", self.oa_voice.currentText().strip() or "alloy")
        st.set("tts/system_voice", self.sys_voice.currentData())
        st.set("tts/skip_margins", self.skip.isChecked())


# ================================================================= 文字识别
class OcrPage(QWidget):
    openHub = Signal()

    def __init__(self, settings: Settings, hub: HubPage):
        super().__init__()
        from ...ocr.system import system_engine, system_engine_hint

        self.settings = settings
        self.hub = hub
        st = settings
        w, lay = page("文字识别", "扫描件、拍照的文档识别出文字后，才能搜索、选择和朗读。")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(w)

        self.engine = system_engine()
        self._models = dict(st.get("ocr/models") or {})       # 每个连接各自记住选过的模型
        self._fix_models = dict(st.get("ocr/fix_models") or {})
        self._cur = self._cur_fix = None
        src = group(lay, "识别方式").add_block()
        self.source = QComboBox()
        src.addLayout(row("使用", self.source))
        self.source.currentIndexChanged.connect(self._source_changed)

        self.sys_box = QWidget()
        sl = QVBoxLayout(self.sys_box)
        sl.setContentsMargins(0, 4, 0, 0)
        sl.setSpacing(8)
        self.lang = QComboBox()
        self.lang.addItem("自动", "")
        if self.engine is not None:
            try:
                for code, name in self.engine.languages():
                    self.lang.addItem(f"{name}（{code}）" if name != code else code, code)
            except Exception:
                pass
        k = self.lang.findData(st.get("ocr/language") or "")
        self.lang.setCurrentIndex(max(k, 0))
        sl.addLayout(row("语言", self.lang))
        hint = system_engine_hint()
        if self.engine is None:
            hint = "⚠ 这台电脑上暂时没有可用的系统识别。" + hint
        sl.addWidget(label(hint, "Faint", wrap=True))
        src.addWidget(self.sys_box)

        self.ai_box = QWidget()
        al = QVBoxLayout(self.ai_box)
        al.setContentsMargins(0, 4, 0, 0)
        al.setSpacing(8)
        self.model = model_combo("", ())
        al.addLayout(row("视觉模型", self.model))
        self.ai_hint = label("", "Faint", wrap=True)
        al.addWidget(self.ai_hint)
        src.addWidget(self.ai_box)

        card = group(lay, "AI 校对（可选）")
        self.fix_on = Switch()
        card.add_row("识别后用 AI 改正错别字和标点", "只改错字和标点，不会改写内容。", self.fix_on)
        self.fix_box = QWidget()
        fl = QVBoxLayout(self.fix_box)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(8)
        self.fix_conn = QComboBox()
        fl.addLayout(row("使用", self.fix_conn))
        self.fix_model = model_combo("", ())
        fl.addLayout(row("文字模型", self.fix_model, "例如 deepseek-flash、qwen-flash"))
        fix_lay = card.add_block()
        fix_lay.addWidget(self.fix_box)
        self.fix_on.toggled.connect(self.fix_box.setEnabled)
        self.fix_conn.currentIndexChanged.connect(self._fix_changed)

        go = QPushButton("在 AI 中台里管理连接和 Key")
        go.setProperty("flat", True)
        go.clicked.connect(self.openHub.emit)
        h = QHBoxLayout()
        h.setContentsMargins(0, 6, 0, 0)
        h.addWidget(go)
        h.addStretch(1)
        lay.addLayout(h)
        lay.addStretch(1)

        self.reload(st.get("ocr/engine") or "system", st.get("ocr/fix") or "")
        hub.connectionsChanged.connect(lambda: self.reload(self.source.currentData(), self.fix_conn.currentData()))

    def reload(self, want: str, want_fix: str):
        name = self.engine.name if self.engine else "不可用"
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem(f"系统自带：{name}（离线、免费）", "system")
        for c in self.hub.conns:
            self.source.addItem(f"AI 识别：{c.name}", c.id)
        idx = self.source.findData(want)
        self.source.setCurrentIndex(idx if idx >= 0 else 0)
        self.source.blockSignals(False)
        self.fix_conn.blockSignals(True)
        self.fix_conn.clear()
        for c in self.hub.conns:
            self.fix_conn.addItem(c.name, c.id)
        idx = self.fix_conn.findData(want_fix)
        if idx < 0:
            idx = self.fix_conn.findData("deepseek")
        self.fix_conn.setCurrentIndex(max(idx, 0))
        self.fix_conn.blockSignals(False)
        self.fix_on.setChecked(bool(want_fix) and self.hub.get(want_fix) is not None)
        self.fix_box.setEnabled(self.fix_on.isChecked())
        self._source_changed()
        self._fix_changed()

    def _source_changed(self, *_):
        c = self.hub.get(self.source.currentData())
        self.sys_box.setVisible(c is None)
        self.ai_box.setVisible(c is not None)
        if self._cur:
            self._models[self._cur] = self.model.currentText().strip()
        self._cur = c.id if c else None
        if c is None:
            return
        fill_models(self.model, c.p.vision, self.hub.models.get(c.id, []))
        self.model.setCurrentText(self._models.get(c.id) or (c.p.vision[0] if c.p.vision else ""))
        tips = "需要能看图的模型。"
        if c.p.vision:
            tips += "推荐：" + "、".join(c.p.vision) + "。"
        if c.preset == "deepseek":
            tips = "DeepSeek 目前主要是文字模型，更适合放在下面的「AI 校对」里。"
        if c.local:
            tips += "本机模型需要先下载，例如 ollama pull qwen3-vl。"
        if not c.ready:
            tips = f"⚠ 「{c.name}」还没有填写 API Key，请先到 AI 中台填写。 " + tips
        self.ai_hint.setText(tips)

    def _fix_changed(self, *_):
        c = self.hub.get(self.fix_conn.currentData())
        if self._cur_fix:
            self._fix_models[self._cur_fix] = self.fix_model.currentText().strip()
        self._cur_fix = c.id if c else None
        if c is None:
            return
        fill_models(self.fix_model, c.p.chat, self.hub.models.get(c.id, []))
        self.fix_model.setCurrentText(self._fix_models.get(c.id) or (c.p.chat[0] if c.p.chat else ""))

    def save(self):
        st = self.settings
        self._source_changed()
        self._fix_changed()
        engine = self.source.currentData() or "system"
        fix = self.fix_conn.currentData() if self.fix_on.isChecked() else ""
        st.set("ocr/engine", engine)
        st.set("ocr/model", self._models.get(engine, "") if engine != "system" else "")
        st.set("ocr/models", self._models)
        st.set("ocr/language", self.lang.currentData() or "")
        st.set("ocr/fix", fix or "")
        st.set("ocr/fix_model", self._fix_models.get(fix, "") if fix else "")
        st.set("ocr/fix_models", self._fix_models)
