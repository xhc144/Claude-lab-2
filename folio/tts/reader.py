"""朗读控制：从点击处所在句子开始，逐句朗读、高亮、自动翻页，并提前合成后面的句子。"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from ..config import Settings
from .engines import TtsEngine, make_engine

PREFETCH = 2
EMPTY_PAGE_LIMIT = 6   # 连续这么多页没有文字就停止


@dataclass
class Item:
    page: int
    start: int
    end: int
    text: str


class ReadAloud(QObject):
    stateChanged = Signal(str)        # idle / loading / playing / paused
    highlight = Signal(object, int, list)  # (doc, 页码, 未旋转矩形列表)；页码 -1 表示清除
    message = Signal(str)
    needsOcr = Signal(object, int)    # (doc, 页码)：扫描页没有文字，需要先识别

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.engine: TtsEngine | None = None
        self.doc = None
        self.items: list[Item] = []
        self.pos = 0
        self.state = "idle"
        self._gen = 0
        self._next_page = 0
        self._free_text = False

    # ---------- 引擎 ----------
    def _ensure_engine(self) -> bool:
        if self.engine is not None:
            return True
        try:
            self.engine = make_engine(self.settings)
        except Exception as ex:  # noqa: BLE001
            self.message.emit(str(ex))
            return False
        self.engine.started.connect(self._on_started)
        self.engine.finished.connect(self._on_finished)
        self.engine.failed.connect(self._on_failed)
        self.engine.waiting.connect(lambda w: w and self._set_state("loading"))
        return True

    def reload_engine(self):
        """设置改变后重建引擎。"""
        was = self.state
        self.stop()
        if self.engine:
            self.engine.shutdown()
            self.engine.deleteLater()
            self.engine = None
        return was

    def engine_label(self) -> str:
        if self.engine is not None:
            return f"{self.engine.name} · {getattr(self.engine, 'voice_label', '')}"
        from .engines import describe

        return describe(self.settings)

    def set_rate(self, rate: float):
        self.settings.set("tts/rate", rate)
        if self.engine:
            self.engine.set_rate(rate)

    # ---------- 队列 ----------
    def _token(self, idx: int) -> int:
        return self._gen * 1_000_000 + idx

    def _idx(self, token: int) -> int | None:
        if token // 1_000_000 != self._gen:
            return None
        return token % 1_000_000

    def _extend(self):
        """队列快读完时，把后面页面的句子加进来。"""
        if self._free_text or self.doc is None:
            return
        skip = bool(self.settings.get("tts/skip_margins"))
        empty = 0
        while len(self.items) - self.pos < PREFETCH + 2 and self._next_page < self.doc.page_count:
            p = self._next_page
            self._next_page += 1
            sents = self.doc.text(p).sentences(skip)
            if not sents:
                empty += 1
                if empty >= EMPTY_PAGE_LIMIT:
                    break
                continue
            empty = 0
            self.items += [Item(p, s.start, s.end, s.text) for s in sents]

    def start(self, doc, page: int, char_index: int):
        self.stop()
        if doc.text(page).empty and doc.pages_needing_ocr([page]):
            self.needsOcr.emit(doc, page)  # 扫描页：先识别文字
            return
        if not self._ensure_engine():
            return
        self.doc = doc
        self._free_text = False
        skip = bool(self.settings.get("tts/skip_margins"))
        pt = doc.text(page)
        sents = pt.sentences(skip)
        k = pt.sentence_index_at(char_index, skip) if sents else 0
        self.items = [Item(page, s.start, s.end, s.text) for s in sents[k:]]
        self._next_page = page + 1
        self.pos = 0
        self._extend()
        if not self.items:
            self.message.emit("这里没有可朗读的文字。")
            return
        self._play_current()

    def read_text(self, text: str):
        """朗读任意文字（例如选中的内容），不做页面高亮。"""
        from ..core.textmap import split_sentences

        self.stop()
        if not self._ensure_engine():
            return
        self._free_text = True
        self.doc = None
        self.items = [Item(-1, 0, 0, s.text) for s in split_sentences(text)]
        self.pos = 0
        if self.items:
            self._play_current()

    def _play_current(self):
        if self.pos >= len(self.items):
            self._extend()
        if self.pos >= len(self.items):
            self.stop()
            self.message.emit("朗读完毕")
            return
        it = self.items[self.pos]
        self._set_state("loading")
        self.engine.speak(self._token(self.pos), it.text)
        self._extend()
        for k in range(1, PREFETCH + 1):
            if self.pos + k < len(self.items):
                self.engine.prefetch(self._token(self.pos + k), self.items[self.pos + k].text)

    def _on_started(self, token: int):
        idx = self._idx(token)
        if idx is None or idx != self.pos:
            return
        self._set_state("playing")
        it = self.items[idx]
        if it.page >= 0 and self.doc is not None:
            rects = self.doc.text(it.page).rects_for_range(it.start, it.end)
            self.highlight.emit(self.doc, it.page, rects)

    def _on_finished(self, token: int):
        idx = self._idx(token)
        if idx is None or idx != self.pos or self.state == "idle":
            return
        self.pos += 1
        self._play_current()

    def _on_failed(self, msg: str):
        self.message.emit(msg)
        self.stop()

    # ---------- 控制 ----------
    def toggle_pause(self):
        if self.state in ("playing", "loading"):
            self.engine.pause()
            self._set_state("paused")
        elif self.state == "paused":
            self.engine.resume()
            self._set_state("playing")

    def next(self):
        if self.state == "idle" or not self.items:
            return
        self.pos = min(self.pos + 1, len(self.items))
        self._restart()

    def prev(self):
        if self.state == "idle" or not self.items:
            return
        self.pos = max(0, self.pos - 1)
        self._restart()

    def _restart(self):
        self.engine.stop()
        self._play_current()

    def stop(self):
        if self.engine:
            self.engine.stop()
        was_doc = self.doc
        self._gen += 1
        self.items = []
        self.pos = 0
        self._set_state("idle")
        self.highlight.emit(was_doc, -1, [])

    def _set_state(self, st: str):
        if st != self.state:
            self.state = st
            self.stateChanged.emit(st)
