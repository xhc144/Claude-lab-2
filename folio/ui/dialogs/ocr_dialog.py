"""文字识别对话框：选择页面范围，显示识别方式，逐页识别并写入隐藏文字层。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ...core.util import parse_page_ranges
from ...ocr import OcrError
from ...ocr.runner import OcrRunner, describe_plan, resolve_plan
from ..widgets import Segmented, label
from .base import ToolDialog, section


class OcrDialog(ToolDialog):
    recognized = Signal(int)   # 识别完成的页数

    def __init__(self, main, tab, pages: list[int] | None = None, autostart: bool = False):
        super().__init__(main, "文字识别（OCR）",
                         "识别扫描件和图片里的文字。识别结果作为隐藏文字写进 PDF，页面外观不变，之后就能搜索、选择、复制和朗读。",
                         "scan-text", 620, 470)
        self.main, self.tab, self.doc = main, tab, tab.doc
        self.settings = main.settings
        self.autostart = autostart
        self.fixed_pages = pages
        b = self.body_layout

        b.addWidget(section("识别哪些页"))
        cur = tab.view.current_page
        self._todo = self.doc.pages_needing_ocr()
        if pages is not None:
            opts = [("given", f"第 {', '.join(str(p + 1) for p in pages[:6])}{' 等' if len(pages) > 6 else ''} 页")]
        else:
            opts = [("todo", f"所有未识别的页（{len(self._todo)} 页）"), ("current", f"当前页（第 {cur + 1} 页）"),
                    ("range", "指定页码")]
        self.scope = Segmented(opts, opts[0][0])
        self.scope.changed.connect(lambda k: self.range_edit.setVisible(k == "range"))
        b.addWidget(self.scope)
        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText(f"例如 1-5, 8（共 {self.doc.page_count} 页）")
        self.range_edit.hide()
        b.addWidget(self.range_edit)
        b.addWidget(label("已经有文字的页面会自动跳过，不会重复识别。", "Faint"))

        b.addSpacing(4)
        b.addWidget(section("识别方式"))
        card = QFrame()
        card.setObjectName("Card")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(14, 10, 10, 10)
        tl = QVBoxLayout()
        tl.setSpacing(2)
        self.plan_label = QLabel()
        self.plan_label.setWordWrap(True)
        tl.addWidget(self.plan_label)
        self.plan_hint = label("", "Faint", wrap=True)
        tl.addWidget(self.plan_hint)
        cl.addLayout(tl, 1)
        change = QPushButton("更改…")
        change.clicked.connect(self._change_settings)
        cl.addWidget(change, 0, Qt.AlignVCenter)
        b.addWidget(card)
        b.addStretch(1)
        self._refresh_plan()
        self.run_btn.setText("开始识别")
        self.runner: OcrRunner | None = None
        if autostart:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(0, self.start)

    def _refresh_plan(self):
        text = describe_plan(self.settings)
        self.plan_label.setText(text)
        if self.settings.get("ocr/engine") in (None, "", "system"):
            self.plan_hint.setText("离线识别，速度快、不花钱。识别效果不理想时，可以改用 AI 识别（千问、本地模型等）。")
        else:
            self.plan_hint.setText("AI 识别准确度更高，每页大约需要几秒钟；云端服务会按用量计费。")

    def _change_settings(self):
        self.main.open_settings("ocr")
        self._refresh_plan()

    def _pages(self) -> list[int] | None:
        k = self.scope.value()
        if k == "given":
            wanted = self.fixed_pages or []
        elif k == "todo":
            wanted = self._todo
        elif k == "current":
            wanted = [self.tab.view.current_page]
        else:
            try:
                wanted = parse_page_ranges(self.range_edit.text(), self.doc.page_count)
            except ValueError as ex:
                self.set_status(str(ex), error=True)
                return None
        pages = self.doc.pages_needing_ocr(wanted)
        if not pages:
            self.set_status("这些页面已经有文字，不需要识别。" if wanted else "没有需要识别的页面。", ok=bool(wanted))
            return None
        return pages

    # ToolDialog 默认用 Worker 线程跑一个函数；这里改用 OcrRunner（渲染和写入必须在主线程）
    def start(self):
        if not self.doc.editable:
            self.set_status("只有 PDF 文件可以写入识别结果，请先「另存为」PDF。", error=True)
            return
        pages = self._pages()
        if not pages:
            return
        try:
            plan = resolve_plan(self.settings)
        except OcrError as ex:
            self.set_status(str(ex), error=True)
            return
        self.run_btn.setEnabled(False)
        self.body.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_btn.setText("取消")
        self.set_status(f"正在识别第 {pages[0] + 1} 页…")
        self.runner = OcrRunner(self.doc, pages, plan, self)
        self.worker = self.runner  # 让基类的「取消」和关闭窗口逻辑生效
        self.runner.progress.connect(self._on_progress)
        self.runner.finished.connect(self._on_finished)
        self.runner.start()

    def _on_progress(self, done: int, total: int, msg: str):
        self.progress.setValue(int(done / max(total, 1) * 1000))
        self.set_status(msg)

    def _on_finished(self, pages: int, lines: int, err: str):
        self._reset()
        self.runner = None
        if pages:
            self._todo = self.doc.pages_needing_ocr()
            self.recognized.emit(pages)
        if err and err != "已取消":
            done = f"已识别 {pages} 页。" if pages else ""
            self.set_status(f"{done}{err}", error=True)
            return
        if err == "已取消":
            self.set_status(f"已取消，识别了 {pages} 页。" if pages else "已取消")
            return
        self.set_status(f"✓ 识别完成：{pages} 页，{lines} 行文字。现在可以搜索和朗读了，保存后写入文件。", ok=True)
        self.cancel_btn.setText("完成")
        self.run_btn.hide()
        if self.autostart:
            self.accept()
