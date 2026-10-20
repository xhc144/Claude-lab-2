from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout


class NoteDialog(QDialog):
    def __init__(self, parent, title: str, text: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(380, 240)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("H3")
        lay.addWidget(t)
        self.edit = QPlainTextEdit(text)
        self.edit.setPlaceholderText("写点什么…")
        lay.addWidget(self.edit, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("确定")
        ok.setProperty("primary", True)
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)
        self.edit.setFocus()

    @classmethod
    def ask(cls, parent, title: str, text: str = "") -> str | None:
        d = cls(parent, title, text)
        if d.exec() == QDialog.Accepted:
            return d.edit.toPlainText().strip()
        return None
