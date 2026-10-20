import pymupdf
import pytest

from folio.model.document import NeedsPassword, PdfDocument

from .test_core import make_text_pdf


def annot_types(doc, i=0):
    return sorted(a.type[1] for a in doc.page(i).annots() if a.type[1] != "Popup")


@pytest.fixture
def doc(tmp_path):
    return PdfDocument(make_text_pdf(str(tmp_path / "d.pdf"), 3))


def test_add_undo_redo_annots(doc):
    doc.add_ink(0, [[(100, 200), (150, 250), (200, 220)]], (1, 0, 0), 2)
    doc.add_markup(0, "highlight", [(72, 85, 200, 104)], (1, 1, 0))
    doc.add_note(0, (300, 300), "便签内容", (1, 0.8, 0))
    doc.add_freetext(0, (50, 400, 250, 440), "文本框", 14, (0, 0, 1))
    doc.add_shape(0, "arrow", (100, 500), (200, 600), (0, 0, 0), 2)
    assert annot_types(doc) == ["FreeText", "Highlight", "Ink", "Line", "Text"]
    assert doc.modified
    for _ in range(5):
        doc.undo()
    assert annot_types(doc) == []
    assert not doc.modified
    for _ in range(5):
        doc.redo()
    assert annot_types(doc) == ["FreeText", "Highlight", "Ink", "Line", "Text"]


def test_erase_and_undo(doc):
    doc.add_ink(0, [[(100, 200), (200, 200)]], (1, 0, 0), 2)
    hits = doc.annots_at(0, 150, 201, 3)
    assert len(hits) == 1
    assert doc.annots_at(0, 150, 260, 3) == []
    doc.delete_annots(0, hits)
    assert annot_types(doc) == []
    doc.undo()
    assert annot_types(doc) == ["Ink"]


def test_modify_color_undo(doc):
    x = doc.add_shape(0, "rect", (100, 100), (200, 200), (1, 0, 0), 2)
    doc.set_annot_color(0, x, (0, 0, 1))
    assert doc.annot_info(0, x)["colors"]["stroke"] == pytest.approx((0, 0, 1))
    doc.undo()
    assert doc.annot_info(0, x)["colors"]["stroke"] == pytest.approx((1, 0, 0))
    doc.redo()
    assert doc.annot_info(0, x)["colors"]["stroke"] == pytest.approx((0, 0, 1))


def test_page_ops_undo(doc):
    first_text = lambda: doc.page(0).get_text().split("\n")[0]
    doc.add_ink(1, [[(100, 200), (200, 200)]], (1, 0, 0), 2)
    doc.move_pages([2], 0)
    assert first_text().startswith("Page 3")
    doc.delete_pages([0])
    assert doc.page_count == 2
    doc.insert_blank(0)
    assert doc.page_count == 3
    doc.rotate_pages([0], 90)
    assert doc.page(0).rotation == 90
    assert doc.page_size(0)[0] > doc.page_size(0)[1]
    for _ in range(4):
        doc.undo()
    assert doc.page_count == 3 and first_text().startswith("Page 1")
    assert annot_types(doc, 1) == ["Ink"]
    for _ in range(4):
        doc.redo()
    assert doc.page_count == 3 and doc.page(0).rotation == 90


def test_save_keeps_undo(doc, tmp_path):
    doc.add_ink(0, [[(100, 200), (200, 200)]], (1, 0, 0), 2)
    out = str(tmp_path / "saved.pdf")
    doc.save(out)
    assert not doc.modified
    assert [a.type[1] for a in pymupdf.open(out)[0].annots()] == ["Ink"]
    doc.undo()
    assert doc.modified and annot_types(doc) == []
    doc.save()
    assert list(pymupdf.open(out)[0].annots()) == []


def test_rotated_page_coordinates(doc):
    doc.rotate_pages([0], 90)
    # 显示坐标 (100, 50) 换算到未旋转坐标后画墨迹，渲染出来应在显示位置附近出现红色
    ux, uy = doc.to_unrot(0, 100, 50)
    doc.add_ink(0, [[(ux - 5, uy), (ux + 5, uy)]], (1, 0, 0), 6)
    pix = doc.render(0, 1.0)
    r, g, b = pix.pixel(100, 50)
    assert r > 200 and g < 80 and b < 80


def test_password(tmp_path):
    p = str(tmp_path / "enc.pdf")
    d = pymupdf.open()
    d.new_page()
    d.save(p, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="123", owner_pw="456")
    with pytest.raises(NeedsPassword):
        PdfDocument(p)
    doc = PdfDocument(p, password="123")
    doc.add_ink(0, [[(10, 10), (50, 50)]], (1, 0, 0), 2)
    doc.save()
    re = PdfDocument(p, password="123")
    assert len(list(re.page(0).annots())) == 1
