"""界面冒烟测试：在无界面（offscreen）模式下模拟鼠标操作。"""
import time

import pymupdf
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt, QTimer
from PySide6.QtTest import QTest

from .test_core import make_text_pdf


def pump(app, ms=50):
    end = time.time() + ms / 1000
    while time.time() < end:
        app.processEvents()
        time.sleep(0.005)


@pytest.fixture
def win(qapp, tmp_path):
    from folio.config import Settings
    from folio.ui.main_window import MainWindow

    s = Settings()
    s.set("view/restore_position", False)
    s.set("tts/engine", "system")
    w = MainWindow(s)
    w.resize(1280, 860)
    w.show()
    pump(qapp, 50)
    yield w
    for t in list(w.tabs_widgets):
        t.doc._undo.mark_clean()
    w.close()


def open_doc(win, qapp, tmp_path, pages=3):
    path = make_text_pdf(str(tmp_path / "doc.pdf"), pages)
    tab = win.open_path(path)
    pump(qapp, 100)
    return tab


def vp_point(tab, page, x_pt, y_pt) -> QPoint:
    """页面显示坐标(pt) → 视口像素坐标。"""
    r = tab.view.page_rect(page)
    return QPoint(int(r.x() + x_pt * tab.view.scale), int(r.y() + y_pt * tab.view.scale))


def drag(qapp, widget, pts):
    QTest.mousePress(widget, Qt.LeftButton, Qt.NoModifier, pts[0])
    for p in pts[1:]:
        QTest.mouseMove(widget, p)
        pump(qapp, 5)
    QTest.mouseRelease(widget, Qt.LeftButton, Qt.NoModifier, pts[-1])
    pump(qapp, 30)


def types(tab, page=0):
    return sorted(a.type[1] for a in tab.doc.page(page).annots() if a.type[1] != "Popup")


def test_open_and_navigate(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path, 5)
    assert win.page_total.text() == "/ 5"
    tab.view.go_to(3)
    pump(qapp, 50)
    assert tab.view.current_page == 3
    assert win.page_edit.text() == "4"
    tab.view.set_zoom(2.0)
    assert abs(tab.view.zoom - 2.0) < 1e-6
    tab.view.set_fit("page")
    assert tab.view.fit_mode == "page"
    win._toggle_layout()
    assert tab.view.layout_mode == "double"


def test_pen_and_undo(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    win.select_tool("pen")
    vp = tab.view.viewport()
    drag(qapp, vp, [vp_point(tab, 0, 100 + k * 10, 300 + (k % 3) * 8) for k in range(12)])
    assert types(tab) == ["Ink"]
    assert win.btn_undo.isEnabled()
    tab.doc.undo()
    assert types(tab) == []


def test_highlight_text_drag(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    win.select_tool("highlight")
    vp = tab.view.viewport()
    drag(qapp, vp, [vp_point(tab, 0, 74, 95), vp_point(tab, 0, 150, 95), vp_point(tab, 0, 250, 95)])
    assert types(tab) == ["Highlight"]


def test_select_and_copy(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    vp = tab.view.viewport()
    drag(qapp, vp, [vp_point(tab, 0, 72, 95), vp_point(tab, 0, 140, 95), vp_point(tab, 0, 200, 95)])
    text = tab.view.selected_text()
    assert text.startswith("Page 1")
    assert tab.view.copy_selection()
    from PySide6.QtWidgets import QApplication

    assert QApplication.clipboard().text() == text


def test_shape_eraser(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    win.select_tool("shape")
    vp = tab.view.viewport()
    drag(qapp, vp, [vp_point(tab, 0, 100, 400), vp_point(tab, 0, 160, 450), vp_point(tab, 0, 200, 500)])
    assert types(tab) == ["Square"]
    win.select_tool("eraser")
    drag(qapp, vp, [vp_point(tab, 0, 100, 450), vp_point(tab, 0, 101, 451)])
    assert types(tab) == []
    tab.doc.undo()
    assert types(tab) == ["Square"]


def test_text_box(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    win.select_tool("text")
    vp = tab.view.viewport()
    QTest.mouseClick(vp, Qt.LeftButton, Qt.NoModifier, vp_point(tab, 0, 100, 500))
    pump(qapp, 30)
    ed = tab.tools["text"]._editor
    assert ed is not None
    ed.insertPlainText("批注 note")
    QTest.keyClick(ed, Qt.Key_Return, Qt.ControlModifier)
    pump(qapp, 30)
    assert types(tab) == ["FreeText"]
    pg = tab.doc.page(0)
    assert [a.info["content"] for a in pg.annots()] == ["批注 note"]


def test_laser_does_not_modify(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path)
    win.select_tool("laser")
    vp = tab.view.viewport()
    drag(qapp, vp, [vp_point(tab, 0, 100 + k * 5, 200) for k in range(10)])
    assert types(tab) == []
    assert not tab.doc.modified
    assert tab.tools["laser"]._strokes


class FakeEngine:
    """立即"读完"每句话的假引擎。"""

    def __init__(self):
        from PySide6.QtCore import QObject, Signal

        class E(QObject):
            started = Signal(int)
            finished = Signal(int)
            failed = Signal(str)
            waiting = Signal(bool)
        self.q = E()
        self.started, self.finished, self.failed, self.waiting = self.q.started, self.q.finished, self.q.failed, self.q.waiting
        self.spoken = []
        self.name = "fake"

    def speak(self, token, text):
        self.spoken.append(text)
        QTimer.singleShot(0, lambda: self.started.emit(token))
        QTimer.singleShot(5, lambda: self.finished.emit(token))

    def prefetch(self, token, text):
        pass

    def stop(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def set_rate(self, r):
        pass

    def shutdown(self):
        pass


def test_read_aloud_from_click(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path, 2)
    eng = FakeEngine()
    win.reader.engine = eng
    eng.started.connect(win.reader._on_started)
    eng.finished.connect(win.reader._on_finished)
    win.select_tool("read")
    vp = tab.view.viewport()
    QTest.mouseClick(vp, Qt.LeftButton, Qt.NoModifier, vp_point(tab, 0, 130, 95))
    pump(qapp, 400)
    assert eng.spoken[0] == "Hello world."
    assert "第三句！" in eng.spoken
    assert "Page 2." in eng.spoken  # 自动读到下一页
    assert tab.read_bar.isVisible()


def test_presentation(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path, 3)
    win.present()
    pres = win._presenter
    pump(qapp, 50)
    assert pres.view.layout_mode == "present"
    QTest.keyClick(pres.view, Qt.Key_Right)
    assert pres.view.current_page == 1
    pres.close()
    pump(qapp, 30)
    assert tab.view.current_page == 1


def test_print_to_pdf_nup(win, qapp, tmp_path):
    from PySide6.QtPrintSupport import QPrinter

    from folio.ui.dialogs.print_dialog import PrintOptions, print_to

    tab = open_doc(win, qapp, tmp_path, 5)
    pr = QPrinter(QPrinter.ScreenResolution)
    pr.setOutputFormat(QPrinter.PdfFormat)
    out = str(tmp_path / "printed.pdf")
    pr.setOutputFileName(out)
    assert print_to(pr, tab.doc, PrintOptions(pages=list(range(5)), nup=2), None)
    assert pymupdf.open(out).page_count == 3


def test_dialogs_construct(win, qapp, tmp_path):
    from folio.ui.dialogs.print_dialog import PrintDialog
    from folio.ui.dialogs.settings_dialog import SettingsDialog
    from folio.ui.dialogs.tool_dialogs import DIALOGS

    tab = open_doc(win, qapp, tmp_path, 2)
    for key, cls in DIALOGS.items():
        d = cls(win, [tab.doc.path] if key != "images" else None)
        d.show()
        pump(qapp, 20)
        d.close()
    d = PrintDialog(win, tab.doc, 0, win.settings)
    d.show()
    pump(qapp, 20)
    assert d.preview.image is not None
    d.close()
    d = SettingsDialog(win, win.settings, "tts")
    d.show()
    pump(qapp, 20)
    d.close()


def test_thumbnail_reorder(win, qapp, tmp_path):
    tab = open_doc(win, qapp, tmp_path, 3)
    tab.doc.reorder([2, 0, 1])
    pump(qapp, 30)
    assert tab.doc.page(0).get_text().startswith("Page 3")
    assert tab.sidebar.thumbs.count() == 3
    tab.doc.undo()
    assert tab.doc.page(0).get_text().startswith("Page 1")


def test_signature_stamp(win, qapp, tmp_path):
    from PySide6.QtGui import QColor, QImage

    from folio.ui.signature import SignaturePad, save_signature

    pad = SignaturePad()
    pad.strokes = [[QPointF(10, 50), QPointF(60, 20), QPointF(120, 60)]]
    png = pad.to_png()
    assert png and QImage.fromData(png).pixelColor(0, 0) == QColor(0, 0, 0, 0)  # 背景透明
    path = save_signature(png)
    tab = open_doc(win, qapp, tmp_path)
    win.settings.set("sign/path", path)
    win.select_tool("sign")
    assert tab.tool_name == "sign"
    QTest.mouseClick(tab.view.viewport(), Qt.LeftButton, Qt.NoModifier, vp_point(tab, 0, 300, 600))
    pump(qapp, 30)
    assert types(tab) == ["Stamp"]
    tab.doc.undo()
    assert types(tab) == []
