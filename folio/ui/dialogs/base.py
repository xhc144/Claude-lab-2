"""对话框基类和后台任务线程。"""
from __future__ import annotations

import os
import traceback

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from ...core.util import Cancelled
from ..widgets import IconButton


class Worker(QThread):
    progress = Signal(float, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            result = self._fn(lambda f, m: self.progress.emit(float(f), m), lambda: self._cancel)
            self.done.emit(result)
        except Cancelled:
            self.failed.emit("已取消")
        except Exception as ex:  # noqa: BLE001
            traceback.print_exc()
            self.failed.emit(str(ex) or ex.__class__.__name__)


class ToolDialog(QDialog):
    """统一风格的工具对话框：顶部标题、中间内容、底部进度条与按钮。

    independent=True 时是独立窗口（压缩、合并等）：有自己的任务栏按钮，可以最小化，不会挡住主窗口，
    主窗口照样可以移动、最小化、继续阅读；关闭时自动释放。文件可以拖到窗口的任何地方。
    """

    def __init__(self, parent, title: str, subtitle: str = "", icon: str = "file", width: int = 640, height: int = 560,
                 independent: bool = False):
        super().__init__(None if independent else parent)
        self.main = parent
        if independent:
            self.setWindowFlags(Qt.Window)
            self.setAttribute(Qt.WA_DeleteOnClose)
        self.setProperty("titleColor", "surface")
        self.setAcceptDrops(True)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(520, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("DialogHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(22, 16, 22, 16)
        hl.setSpacing(12)
        badge = IconButton(icon, size=22, color_key="accent")
        badge.setEnabled(True)
        badge.setFixedSize(40, 40)
        badge.setStyleSheet("QToolButton { background: rgba(61,109,242,0.12); border-radius: 10px; }")
        hl.addWidget(badge)
        tl = QVBoxLayout()
        tl.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("H2")
        tl.addWidget(t)
        if subtitle:
            st = QLabel(subtitle)
            st.setObjectName("Muted")
            st.setWordWrap(True)
            tl.addWidget(st)
        hl.addLayout(tl, 1)
        root.addWidget(header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(22, 18, 22, 18)
        self.body_layout.setSpacing(14)
        root.addWidget(self.body, 1)

        footer = QFrame()
        footer.setObjectName("DialogFooter")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(22, 12, 22, 12)
        fl.setSpacing(10)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setFixedWidth(160)
        self.progress.hide()
        fl.addWidget(self.status, 1)
        fl.addWidget(self.progress)
        self.open_folder_btn = QPushButton("打开所在文件夹")
        self.open_folder_btn.hide()
        self.open_folder_btn.clicked.connect(self._open_folder)
        fl.addWidget(self.open_folder_btn)
        self.open_doc_btn = QPushButton("在 Folio 中打开")
        self.open_doc_btn.hide()
        self.open_doc_btn.clicked.connect(self._open_doc)
        fl.addWidget(self.open_doc_btn)
        self.cancel_btn = QPushButton("关闭")
        self.cancel_btn.clicked.connect(self._on_cancel)
        fl.addWidget(self.cancel_btn)
        self.run_btn = QPushButton("开始")
        self.run_btn.setProperty("primary", True)
        self.run_btn.setDefault(True)
        self.run_btn.clicked.connect(self.start)
        fl.addWidget(self.run_btn)
        root.addWidget(footer)

        self.worker: Worker | None = None
        self._last_output: str | None = None

    # 子类实现：返回 fn(progress, cancel) -> result；校验失败时返回 None
    def make_job(self):
        raise NotImplementedError

    def on_done(self, result):
        pass

    def start(self):
        job = self.make_job()
        if job is None:
            return
        self.run_btn.setEnabled(False)
        self.body.setEnabled(False)
        self.open_folder_btn.hide()
        self.open_doc_btn.hide()
        self.progress.setValue(0)
        self.progress.show()
        self.cancel_btn.setText("取消")
        self.set_status("正在处理…")
        self.worker = Worker(job, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._finished)
        self.worker.failed.connect(self._failed)
        self.worker.start()

    @property
    def busy(self) -> bool:
        return self.worker is not None

    def _on_progress(self, f: float, msg: str):
        self.progress.setValue(int(f * 1000))
        self.set_status(msg)

    def _reset(self):
        self.run_btn.setEnabled(True)
        self.body.setEnabled(True)
        self.progress.hide()
        self.cancel_btn.setText("关闭")
        self.worker = None

    def _finished(self, result):
        self._reset()
        self.on_done(result)

    def _failed(self, msg):
        self._reset()
        self.set_status(f"⚠ {msg}", error=True)

    def set_status(self, text: str, error: bool = False, ok: bool = False):
        self.status.setText(text)
        from ...theme import theme

        color = theme.c("danger") if error else theme.c("success") if ok else theme.c("text2")
        self.status.setStyleSheet(f"color: {color};")

    def show_output(self, path: str, openable: bool = False):
        self._last_output = path
        self.open_folder_btn.show()
        self.open_doc_btn.setVisible(openable and hasattr(self.main, "open_path"))

    def _open_doc(self):
        if self._last_output and os.path.isfile(self._last_output):
            self.main.open_path(self._last_output)
            if hasattr(self.main, "reveal"):
                self.main.reveal()
            self.accept()

    def _open_folder(self):
        if self._last_output:
            folder = self._last_output if os.path.isdir(self._last_output) else os.path.dirname(self._last_output)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _on_cancel(self):
        if self.worker is not None:
            self.worker.cancel()
            self.set_status("正在取消…")
        else:
            self.reject()

    def reject(self):
        if self.worker is not None:  # 按 Esc 时先停止任务，不直接关掉
            self._on_cancel()
            return
        super().reject()

    def _stop_worker(self) -> bool:
        """取消并等待后台任务结束；返回是否已经停下。"""
        if self.worker is None:
            return True
        self.worker.cancel()
        if not self.worker.wait(5000):
            return False
        self.worker = None  # 结束信号可能还在排队，窗口马上要关，不再处理
        return True

    def closeEvent(self, e):
        if not self._stop_worker():
            self.set_status("正在取消…")
            e.ignore()
            return
        super().closeEvent(e)

    # 文件拖到窗口任何地方都可以（不只是文件列表）
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and hasattr(self, "add_paths") and not self.busy:
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        paths = [p for p in paths if os.path.isfile(p)]
        if paths and hasattr(self, "add_paths") and not self.busy:
            self.add_paths(paths)
            e.acceptProposedAction()


def choose_save_path(parent, title: str, default_path: str, filt: str = "PDF 文件 (*.pdf)") -> str | None:
    path, _ = QFileDialog.getSaveFileName(parent, title, default_path, filt)
    if not path:
        return None
    if not os.path.splitext(path)[1]:
        path += ".pdf"
    return path


def section(title: str) -> QLabel:
    lb = QLabel(title)
    lb.setObjectName("SectionTitle")
    return lb


def form_row(label_text: str, widget, hint: str = "", expand: bool = False) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)
    lb = QLabel(label_text)
    lb.setMinimumWidth(84)
    lb.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    row.addWidget(lb)
    stretch = 1 if expand else 0
    if isinstance(widget, QWidget):
        row.addWidget(widget, stretch)
    else:
        row.addLayout(widget, stretch)
    if hint:
        h = QLabel(hint)
        h.setObjectName("Faint")
        row.addWidget(h)
    if not expand:
        row.addStretch(1)
    return row
