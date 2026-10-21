"""文字识别：文字层写入（含旋转页面）、行整理、各系统识别引擎、识别流程与撤销、点读扫描页。"""
import sys
import time

import pymupdf
import pytest

from folio.ocr import OcrLine, order_lines
from folio.ocr.layer import add_text_layer, needs_ocr, render_for_ocr
from folio.ocr.system import (MacVisionOcr, OcrImage, TesseractOcr, WindowsOcr, join_words, parse_tesseract_tsv,
                              words_to_lines)

LINES = [OcrLine("第一章 扫描文档测试", (0.098, 0.073, 0.382, 0.099)),
         OcrLine("这是一段用于测试文字识别的中文内容。", (0.097, 0.128, 0.592, 0.145)),
         OcrLine("Folio PDF reader supports OCR.", (0.097, 0.176, 0.555, 0.194))]


def scanned_pdf(path, rotation=0, text=("第一章 扫描文档测试", "Hello Folio 2026")) -> str:
    """生成一份"扫描件"：先把文字渲染成图片，再放进只有图片的 PDF，并设置页面旋转。"""
    src = pymupdf.open()
    p = src.new_page(width=595, height=842)
    y = 80
    for t in text:
        p.insert_text((60, y), t, fontname="china-s" if any(ord(c) > 255 for c in t) else "helv", fontsize=22)
        y += 50
    png = p.get_pixmap(dpi=150).tobytes("png")
    doc = pymupdf.open()
    w, h = (595, 842) if rotation in (0, 180) else (842, 595)
    page = doc.new_page(width=w, height=h)
    page.insert_image(page.rect, stream=png, rotate=rotation)
    page.set_rotation(rotation)
    doc.save(path)
    return path


def image_of(page) -> OcrImage:
    pix = render_for_ocr(page)
    return OcrImage(pix.width, pix.height, pix.samples, pix.tobytes("png"), pix.tobytes("jpeg"))


# ---------------------------------------------------------------- 文字层
@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_text_layer_on_rotated_pages(tmp_path, rotation):
    from folio.core.textmap import extract_page_text

    doc = pymupdf.open(scanned_pdf(str(tmp_path / "s.pdf"), rotation))
    page = doc[0]
    assert needs_ocr(page)
    assert add_text_layer(page, LINES) == 3
    assert not needs_ocr(page)
    pt = extract_page_text(page)
    assert pt.text.startswith("第一章 扫描文档测试")
    assert "Folio PDF reader" in pt.text
    # 显示方向上，"文字识别"应该落在识别框的位置
    k = pt.text.find("文字识别")
    r = pymupdf.Rect(*pt.rects[k]) * page.rotation_matrix
    box = LINES[1].box
    assert box[0] * page.rect.width < r.x0 < box[2] * page.rect.width
    assert box[1] * page.rect.height - 3 < r.y0 < r.y1 < box[3] * page.rect.height + 3
    assert r.width < r.height * 1.6  # 字是横着排的，不是竖条
    assert page.search_for("文字识别")
    # 文字不可见：渲染结果与写入前一致
    doc2 = pymupdf.open(scanned_pdf(str(tmp_path / "s2.pdf"), rotation))
    assert page.get_pixmap(dpi=40).samples == doc2[0].get_pixmap(dpi=40).samples


def test_needs_ocr_for_text_pdf():
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 72), "real text")
    assert not needs_ocr(p)
    assert not needs_ocr(doc.new_page())  # 空白页不需要识别


# ---------------------------------------------------------------- 行整理
def test_join_words_and_columns():
    assert join_words(["这", "是", "中文", "OCR", "text", "，", "结束"]) == "这是中文OCR text，结束"
    words = [("左栏", 100, 10, 160, 30), ("文字", 160, 10, 220, 30), ("右栏", 600, 10, 660, 30)]
    lines = words_to_lines(words, 1000, 1000)
    assert [ln.text for ln in lines] == ["左栏文字", "右栏"]


def test_order_lines_reads_column_by_column():
    L = lambda t, x0, y0: OcrLine(t, (x0, y0, x0 + 0.35, y0 + 0.02))  # noqa: E731
    lines = [OcrLine("标题", (0.1, 0.05, 0.9, 0.08)), L("左1", 0.1, 0.1), L("右1", 0.55, 0.1),
             L("左2", 0.1, 0.13), L("右2", 0.55, 0.13)]
    assert [ln.text for ln in order_lines(lines)] == ["标题", "左1", "左2", "右1", "右2"]


def test_parse_tesseract_tsv():
    head = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    rows = [head,
            "5\t1\t1\t1\t1\t1\t100\t50\t40\t20\t95\t你好",
            "5\t1\t1\t1\t1\t2\t140\t50\t40\t20\t95\t世界",
            "5\t1\t1\t1\t2\t1\t100\t90\t80\t20\t91\tHello",
            "5\t1\t1\t1\t2\t2\t190\t90\t80\t20\t-1\t",
            "5\t1\t1\t1\t2\t3\t190\t90\t80\t20\t90\tWorld"]
    lines = parse_tesseract_tsv("\n".join(rows), 1000, 1000)
    assert [ln.text for ln in lines] == ["你好世界", "Hello World"]
    assert lines[0].box == pytest.approx((0.1, 0.05, 0.18, 0.07))


# ---------------------------------------------------------------- 真实识别引擎（本机有才测）
ENGINES = [WindowsOcr, MacVisionOcr, TesseractOcr]


@pytest.mark.parametrize("cls", ENGINES, ids=lambda c: c.__name__)
def test_system_engine_recognizes(tmp_path, cls):
    if not cls.available():
        pytest.skip(f"{cls.__name__} 不可用")
    eng = cls()
    doc = pymupdf.open(scanned_pdf(str(tmp_path / "s.pdf"), 0, ("Hello Folio 2026", "Second line here")))
    lines = eng.recognize(image_of(doc[0]), "")
    text = " ".join(ln.text for ln in lines)
    assert "Folio" in text and "Second" in text, text
    assert lines[0].box[1] < lines[-1].box[1]
    print(cls.__name__, eng.languages()[:5], text)


@pytest.mark.skipif(sys.platform != "win32", reason="只在 Windows 上测")
def test_windows_ocr_is_available_on_windows():
    assert WindowsOcr.available(), "Windows 上应该能用系统 OCR（winrt 依赖没装好？）"


@pytest.mark.skipif(sys.platform != "darwin", reason="只在 macOS 上测")
def test_mac_vision_is_available_on_mac():
    assert MacVisionOcr.available(), "macOS 上应该能用 Vision 文字识别（pyobjc 依赖没装好？）"


# ---------------------------------------------------------------- 识别流程（界面）
class FakeEngine:
    name = "测试引擎"

    def __init__(self, delay=0.05):
        self.delay = delay
        self.calls = 0

    def recognize(self, img, lang=""):
        self.calls += 1
        time.sleep(self.delay)
        return [OcrLine(f"识别出的文字 第{self.calls}次。", (0.1, 0.1, 0.8, 0.13))]


def pump(app, until, timeout=10):
    end = time.time() + timeout
    while time.time() < end and not until():
        app.processEvents()
        time.sleep(0.01)


def test_runner_applies_and_undoes(qapp, tmp_path):
    from folio.model.document import PdfDocument
    from folio.ocr.runner import OcrPlan, OcrRunner

    path = scanned_pdf(str(tmp_path / "s.pdf"))
    src = pymupdf.open(path)
    src.insert_pdf(pymupdf.open(path))
    src.insert_pdf(pymupdf.open(path))
    src.save(str(tmp_path / "three.pdf"))
    doc = PdfDocument(str(tmp_path / "three.pdf"))
    assert doc.looks_scanned() and doc.pages_needing_ocr() == [0, 1, 2]
    plan = OcrPlan("测试", engine=FakeEngine())
    runner = OcrRunner(doc, [0, 1, 2], plan)
    result = []
    runner.finished.connect(lambda *a: result.append(a))
    runner.start()
    pump(qapp, lambda: result)
    assert result == [(3, 3, "")]
    assert doc.pages_needing_ocr() == [] and doc.modified
    assert doc.undo_label().endswith("文字识别")
    assert "识别出的文字" in doc.text(1).text
    doc.undo()
    assert doc.pages_needing_ocr() == [0, 1, 2] and not doc.modified
    doc.redo()
    assert doc.pages_needing_ocr() == []


def test_runner_error_keeps_finished_pages(qapp, tmp_path):
    from folio.model.document import PdfDocument
    from folio.ocr.runner import OcrPlan, OcrRunner

    class Failing(FakeEngine):
        def recognize(self, img, lang=""):
            if self.calls >= 1:
                raise RuntimeError("API Key 无效")
            return super().recognize(img, lang)

    path = scanned_pdf(str(tmp_path / "s.pdf"))
    src = pymupdf.open(path)
    src.insert_pdf(pymupdf.open(path))
    src.save(str(tmp_path / "two.pdf"))
    doc = PdfDocument(str(tmp_path / "two.pdf"))
    runner = OcrRunner(doc, [0, 1], OcrPlan("测试", engine=Failing()))
    result = []
    runner.finished.connect(lambda *a: result.append(a))
    runner.start()
    pump(qapp, lambda: result)
    pages, lines, err = result[0]
    assert pages == 1 and "第 2 页识别失败" in err and "API Key 无效" in err
    assert doc.pages_needing_ocr() == [1] and doc.can_undo


def test_click_to_read_scanned_page_offers_ocr(qapp, tmp_path, monkeypatch):
    from folio.config import Settings
    from folio.ocr import runner as runner_mod
    from folio.ui.main_window import MainWindow
    from PySide6.QtWidgets import QMessageBox

    st = Settings()
    st.set("view/restore_position", False)
    st.set("tts/engine", "system")
    win = MainWindow(st)
    win.show()
    tab = win.open_path(scanned_pdf(str(tmp_path / "s.pdf")))
    pump(qapp, lambda: tab.scan_bar.isVisible(), 3)
    assert tab.scan_bar.isVisible()

    monkeypatch.setattr(runner_mod, "resolve_plan", lambda settings: runner_mod.OcrPlan("测试", engine=FakeEngine(0)))
    import folio.ui.dialogs.ocr_dialog as od
    monkeypatch.setattr(od, "resolve_plan", runner_mod.resolve_plan)
    # 自动点"识别这一页并朗读"
    monkeypatch.setattr(QMessageBox, "exec", lambda self: self.buttons()[0].click() or 0)
    started = []
    monkeypatch.setattr(win.reader, "start", lambda doc, page, k: started.append((page, k)))
    win._offer_ocr(tab.doc, 0)
    assert tab.doc.pages_needing_ocr() == []
    assert started == [(0, 0)]
    assert not tab.scan_bar.isVisible()
    tab.doc._undo.mark_clean()
    win.close()


def test_reader_emits_needs_ocr(qapp, tmp_path):
    from folio.config import Settings
    from folio.model.document import PdfDocument
    from folio.tts.reader import ReadAloud

    st = Settings()
    st.set("tts/engine", "system")
    reader = ReadAloud(st)
    got = []
    reader.needsOcr.connect(lambda d, p: got.append(p))
    doc = PdfDocument(scanned_pdf(str(tmp_path / "s.pdf")))
    reader.start(doc, 0, 0)
    assert got == [0] and reader.engine is None  # 没有文字时不会去创建语音引擎
