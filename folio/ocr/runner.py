"""识别任务调度：主线程逐页渲染图片 → 后台线程识别（和校对）→ 回到主线程写入文字层。

PyMuPDF 不支持多线程，所以渲染和写入都在主线程；识别（系统 OCR 或网络请求）在线程池里并行。
整次识别算一步撤销。
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from . import OcrError, OcrLine


@dataclass
class OcrPlan:
    label: str                  # 给用户看的识别方式
    engine: object = None       # SystemOcr（系统识别时）
    conn: object = None         # Connection（AI 识别时）
    model: str = ""
    lang: str = ""
    fix_conn: object = None     # AI 校对
    fix_model: str = ""

    @property
    def parallel(self) -> int:
        return 1 if self.engine is not None else 2

    def recognize(self, img) -> list[OcrLine]:
        if self.engine is not None:
            lines = self.engine.recognize(img, self.lang)
        else:
            from .ai import recognize

            lines = recognize(self.conn, self.model, img)
        if self.fix_conn is not None and lines:
            from .ai import proofread

            texts = proofread(self.fix_conn, self.fix_model, [ln.text for ln in lines])
            lines = [OcrLine(t, ln.box) for t, ln in zip(texts, lines)]
        return lines


def resolve_plan(settings) -> OcrPlan:
    """按设置决定用哪种方式识别；不可用时抛出 OcrError（消息直接给用户看）。"""
    from ..ai.hub import Hub
    from .system import system_engine, system_engine_hint

    hub = Hub(settings)
    fix_conn = hub.get(settings.get("ocr/fix"))
    fix_model = settings.get("ocr/fix_model") or (fix_conn.p.chat[0] if fix_conn and fix_conn.p.chat else "")
    fix_label = f"，{fix_conn.name} 校对" if fix_conn else ""
    eng = settings.get("ocr/engine") or "system"
    if eng == "system":
        engine = system_engine()
        if engine is None:
            raise OcrError("这台电脑上没有可用的系统文字识别。" + system_engine_hint() +
                           "\n也可以在「设置 → 文字识别」里改用 AI 识别。")
        return OcrPlan(engine.name + fix_label, engine=engine, lang=settings.get("ocr/language") or "",
                       fix_conn=fix_conn, fix_model=fix_model)
    conn = hub.get(eng)
    if conn is None:
        raise OcrError("文字识别选用的 AI 连接已被删除，请到「设置 → 文字识别」重新选择。")
    if not conn.ready:
        raise OcrError(f"「{conn.name}」还没有填写 API Key，请到「设置 → AI 中台」填写。")
    model = settings.get("ocr/model") or (conn.p.vision[0] if conn.p.vision else "")
    if not model:
        raise OcrError(f"还没有为「{conn.name}」选择视觉模型，请到「设置 → 文字识别」选择。")
    return OcrPlan(f"{conn.name} · {model}{fix_label}", conn=conn, model=model, fix_conn=fix_conn, fix_model=fix_model)


def describe_plan(settings) -> str:
    try:
        return resolve_plan(settings).label
    except OcrError as ex:
        return "⚠ " + str(ex).split("\n")[0]


class _Bridge(QObject):
    done = Signal(int, object, str)  # 页码, 识别结果, 错误


class _Task(QRunnable):
    def __init__(self, page: int, img, plan: OcrPlan, bridge: _Bridge):
        super().__init__()
        self.page, self.img, self.plan, self.bridge = page, img, plan, bridge

    def run(self):
        lines, err = None, ""
        for attempt in range(2):
            try:
                lines, err = self.plan.recognize(self.img), ""
                break
            except Exception as ex:  # noqa: BLE001
                err = str(ex) or ex.__class__.__name__
                if not any(k in err for k in ("超时", "无法连接", "太频繁")):
                    break
        try:
            self.bridge.done.emit(self.page, lines, err)
        except RuntimeError:
            pass


class OcrRunner(QObject):
    progress = Signal(int, int, str)     # 已完成页数, 总页数, 说明
    finished = Signal(int, int, str)     # 识别的页数, 文字行数, 错误（空表示成功）

    def __init__(self, doc, pages: list[int], plan: OcrPlan, parent=None):
        super().__init__(parent)
        self.doc, self.pages, self.plan = doc, list(pages), plan
        self.queue = list(pages)
        self.inflight: set[int] = set()
        self.done_pages = 0
        self.lines = 0
        self.error = ""
        self.cancelled = False
        self._before = None
        self._committed = False
        self._finished = False
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(plan.parallel)
        self._bridge = _Bridge()
        self._bridge.done.connect(self._on_done)

    def start(self):
        self._before = self.doc.snapshot()
        self.progress.emit(0, len(self.pages), f"正在识别第 {self.pages[0] + 1} 页…" if self.pages else "")
        self._schedule()

    def _schedule(self):
        while not self.cancelled and self.queue and len(self.inflight) < self.plan.parallel:
            i = self.queue.pop(0)
            try:
                img = self.doc.ocr_image(i)
            except Exception as ex:  # noqa: BLE001
                self.error = f"第 {i + 1} 页无法渲染：{ex}"
                self.cancelled = True
                break
            self.inflight.add(i)
            self._pool.start(_Task(i, img, self.plan, self._bridge))
        if not self.inflight:
            self._finish()

    def _on_done(self, page: int, lines, err: str):
        self.inflight.discard(page)
        if self.cancelled or self.doc.closed:
            if not self.inflight:
                self._finish()
            return
        if err:
            self.error = f"第 {page + 1} 页识别失败：{err}"
            self.cancelled = True
        else:
            self.lines += self.doc.apply_ocr(page, lines or [])
            self.done_pages += 1
            nxt = self.queue[0] + 1 if self.queue else None
            msg = f"已识别 {self.done_pages}/{len(self.pages)} 页" + (f"，正在识别第 {nxt} 页…" if nxt else "")
            self.progress.emit(self.done_pages, len(self.pages), msg)
        QTimer.singleShot(0, self._schedule)  # 让界面先刷新，再渲染下一页

    def cancel(self):
        self.cancelled = True
        if not self.inflight:
            self._finish()

    def wait(self, ms: int = 3000) -> bool:
        """关闭窗口时调用：等后台线程结束，把已写入的页面记为一次撤销。"""
        self.cancelled = True
        ok = self._pool.waitForDone(ms)
        self._commit()
        return ok

    def _commit(self):
        if self._committed or self.done_pages == 0 or self.doc.closed:
            return
        self._committed = True
        self.doc.commit_snapshot("文字识别", self._before)
        self._before = None

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        self._commit()
        err = self.error or ("已取消" if self.cancelled else "")
        self.finished.emit(self.done_pages, self.lines, err)
