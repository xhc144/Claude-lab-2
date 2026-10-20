"""撤销/重做。

批注的增删通过把批注对象从页面 /Annots 数组里摘下或挂回来实现：对象本身一直保留在内存里，
所以撤销后还能完整恢复（包括其它软件画的批注）。保存时不做垃圾回收，保证保存后仍可撤销。
页面结构改动（删除、移动、插入页）则保存整份文档的快照。
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .document import PdfDocument

SNAPSHOT_BUDGET = 400 * 1024 * 1024  # 快照最多占用的内存
MAX_COMMANDS = 300


def annot_refs(fz, page_xref: int) -> list[int]:
    t, v = fz.xref_get_key(page_xref, "Annots")
    if t == "xref":
        v = fz.xref_object(int(v.split()[0]))
    elif t != "array":
        return []
    return [int(x) for x in re.findall(r"(\d+)\s+0\s+R", v)]


def set_annot_refs(fz, page_xref: int, refs: list[int]) -> None:
    if refs:
        fz.xref_set_key(page_xref, "Annots", "[" + " ".join(f"{r} 0 R" for r in refs) + "]")
    else:
        fz.xref_set_key(page_xref, "Annots", "null")


def with_popup(fz, xref: int) -> list[int]:
    t, v = fz.xref_get_key(xref, "Popup")
    if t == "xref":
        return [xref, int(v.split()[0])]
    return [xref]


class Command:
    label = ""
    snapshot_bytes = 0

    def undo(self, doc: "PdfDocument") -> None: ...
    def redo(self, doc: "PdfDocument") -> None: ...


class AnnotToggle(Command):
    """added=True 表示这条命令"添加了"批注；undo 时摘下，redo 时挂回。"""

    def __init__(self, label: str, page_xref: int, xrefs: list[int], added: bool):
        self.label = label
        self.page_xref = page_xref
        self.xrefs = xrefs
        self.added = added

    def _attach(self, doc: "PdfDocument", attach: bool):
        fz = doc.fz
        refs = annot_refs(fz, self.page_xref)
        if attach:
            refs += [x for x in self.xrefs if x not in refs]
        else:
            refs = [r for r in refs if r not in self.xrefs]
        set_annot_refs(fz, self.page_xref, refs)
        doc._page_touched(doc.page_index_of_xref(self.page_xref))

    def undo(self, doc):
        self._attach(doc, not self.added)

    def redo(self, doc):
        self._attach(doc, self.added)


class AnnotModify(Command):
    """记录批注对象及其外观流修改前后的完整内容。"""

    def __init__(self, label: str, page_xref: int, before: dict, after: dict):
        self.label = label
        self.page_xref = page_xref
        self.before = before
        self.after = after

    @staticmethod
    def capture(fz, xref: int) -> dict:
        state = {xref: (fz.xref_object(xref, compressed=False), None)}
        src = state[xref][0]
        for ap in re.findall(r"/(?:N|D|R)\s+(\d+)\s+0\s+R", src):
            ap = int(ap)
            if fz.xref_is_stream(ap):
                state[ap] = (fz.xref_object(ap, compressed=False), fz.xref_stream(ap))
        return state

    def _apply(self, doc, state: dict):
        fz = doc.fz
        for x, (src, stream) in state.items():
            fz.update_object(x, src)
            if stream is not None:
                fz.update_stream(x, stream, new=False, compress=True)
        doc._page_touched(doc.page_index_of_xref(self.page_xref))

    def undo(self, doc):
        self._apply(doc, self.before)

    def redo(self, doc):
        self._apply(doc, self.after)


class Rotate(Command):
    def __init__(self, page_xrefs: list[int], before: list[int], after: list[int]):
        self.label = "旋转页面"
        self.page_xrefs, self.before, self.after = page_xrefs, before, after

    def _apply(self, doc, rots):
        for px, r in zip(self.page_xrefs, rots):
            i = doc.page_index_of_xref(px)
            if i is not None:
                doc.fz[i].set_rotation(r)
        doc._structure_touched()

    def undo(self, doc):
        self._apply(doc, self.before)

    def redo(self, doc):
        self._apply(doc, self.after)


class Snapshot(Command):
    def __init__(self, label: str, before: bytes, after: bytes):
        self.label = label
        self.before, self.after = before, after
        self.snapshot_bytes = len(before) + len(after)

    def undo(self, doc):
        doc._restore(self.before)

    def redo(self, doc):
        doc._restore(self.after)


class Compound(Command):
    def __init__(self, label: str, commands: list[Command]):
        self.label = label
        self.commands = commands
        self.snapshot_bytes = sum(c.snapshot_bytes for c in commands)

    def undo(self, doc):
        for c in reversed(self.commands):
            c.undo(doc)

    def redo(self, doc):
        for c in self.commands:
            c.redo(doc)


class UndoStack:
    def __init__(self):
        self._done: list[Command] = []
        self._undone: list[Command] = []
        self.clean_index = 0  # 保存时 _done 的长度

    def push(self, cmd: Command):
        self._done.append(cmd)
        self._undone.clear()
        self._trim()

    def _trim(self):
        while len(self._done) > MAX_COMMANDS or (
                len(self._done) > 1 and sum(c.snapshot_bytes for c in self._done) > SNAPSHOT_BUDGET):
            self._done.pop(0)
            self.clean_index -= 1

    @property
    def can_undo(self) -> bool:
        return bool(self._done)

    @property
    def can_redo(self) -> bool:
        return bool(self._undone)

    def undo_label(self) -> str:
        return self._done[-1].label if self._done else ""

    def redo_label(self) -> str:
        return self._undone[-1].label if self._undone else ""

    def pop_undo(self) -> Command | None:
        if not self._done:
            return None
        c = self._done.pop()
        self._undone.append(c)
        return c

    def pop_redo(self) -> Command | None:
        if not self._undone:
            return None
        c = self._undone.pop()
        self._done.append(c)
        return c

    @property
    def is_clean(self) -> bool:
        return self.clean_index == len(self._done)

    def mark_clean(self):
        self.clean_index = len(self._done)
