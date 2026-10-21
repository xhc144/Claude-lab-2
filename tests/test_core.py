import io
import os

import numpy as np
import pymupdf
import pytest
from PIL import Image, ImageDraw

from folio.core import compress, images, merge, split, textmap, util


# ---------- 工具函数 ----------

def make_text_pdf(path, pages=3):
    doc = pymupdf.open()
    for i in range(pages):
        p = doc.new_page()
        p.insert_text((72, 100), f"Page {i + 1}. Hello world. This is a test.", fontsize=14)
        p.insert_text((72, 130), "中文测试，第二句。第三句！", fontsize=14, fontname="china-s")
    doc.save(path)
    return path


def make_image_pdf(path, n=2, size=(1800, 2400)):
    doc = pymupdf.open()
    rng = np.random.default_rng(0)
    for _ in range(n):
        arr = (rng.random((size[1], size[0], 3)) * 60 + np.linspace(0, 190, size[0])[None, :, None]).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, "PNG")
        p = doc.new_page()
        p.insert_image(p.rect, stream=buf.getvalue())
        p.insert_text((50, 50), "image page", fontsize=20)
    doc.save(path)
    return path


def make_long_image(path, w=800, h=5000, line_every=120):
    """模拟长截图：每隔一段画一行"文字"（黑条），行之间留白。"""
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    y = 40
    while y < h - 40:
        d.rectangle([40, y, w - 40, y + 28], fill=(30, 30, 30))
        y += line_every
    img.save(path)
    return path


# ---------- util ----------

def test_parse_page_ranges():
    assert util.parse_page_ranges("", 5) == [0, 1, 2, 3, 4]
    assert util.parse_page_ranges("1-3,5", 5) == [0, 1, 2, 4]
    assert util.parse_page_ranges("4-", 5) == [3, 4]
    assert util.parse_page_ranges("3-1", 5) == [2, 1, 0]
    assert util.parse_page_ranges("1，2", 5) == [0, 1]
    with pytest.raises(ValueError):
        util.parse_page_ranges("9", 5)
    with pytest.raises(ValueError):
        util.parse_page_ranges("abc", 5)


def test_format_page_ranges():
    assert util.format_page_ranges([0, 1, 2, 4, 6, 7]) == "1-3,5,7-8"


# ---------- 文字定位与句子切分 ----------

def test_textmap_sentences(tmp_path):
    path = make_text_pdf(str(tmp_path / "t.pdf"), 1)
    doc = pymupdf.open(path)
    pt = textmap.extract_page_text(doc[0])
    texts = [s.text for s in pt.sentences()]
    assert texts[0] == "Page 1."
    assert "Hello world." in texts
    assert "中文测试，第二句。" in texts
    assert "第三句！" in texts
    # 点击 "world" 附近，应定位到含 Hello 的句子
    i = pt.hit(130, 95)
    assert i is not None
    k = pt.sentence_index_at(i)
    assert pt.sentences()[k].text == "Hello world."
    rects = pt.rects_for_range(pt.sentences()[k].start, pt.sentences()[k].end)
    assert len(rects) == 1


def test_speech_text_joins_lines():
    lt = textmap.LINE_BREAK
    assert textmap.speech_text(f"inter-{lt}national") == "international"
    assert textmap.speech_text(f"中文{lt}换行") == "中文换行"
    assert textmap.speech_text(f"hello{lt}world") == "hello world"


def test_split_long_sentence():
    text = "，".join(["这是一个很长的句子片段"] * 40) + "。"
    sents = textmap.split_sentences(text)
    assert len(sents) > 1
    assert all(len(s.text) <= textmap.MAX_SENTENCE for s in sents)


def test_abbreviations_not_split():
    sents = textmap.split_sentences("Dr. Smith went to the U.S. in 2020. He liked it.")
    assert [s.text for s in sents] == ["Dr. Smith went to the U.S. in 2020.", "He liked it."]


def test_margin_skip(tmp_path):
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 30), "Running header", fontsize=9)
    p.insert_text((72, 300), "Body text here.", fontsize=12)
    p.insert_text((290, 830), "12", fontsize=9)
    pt = textmap.extract_page_text(p)
    assert [s.text for s in pt.sentences()] == ["Body text here."]


# ---------- 压缩 ----------

def test_compress_target(tmp_path):
    path = make_image_pdf(str(tmp_path / "img.pdf"))
    src = open(path, "rb").read()
    target = len(src) // 8
    res = compress.compress_pdf(src, target_bytes=target)
    assert res.reached
    assert res.size <= target
    doc = pymupdf.open("pdf", res.data)
    assert doc.page_count == 2
    assert "image page" in doc[0].get_text()


def test_compress_unreachable_reports(tmp_path):
    path = make_text_pdf(str(tmp_path / "t.pdf"), 2)
    src = open(path, "rb").read()
    res = compress.compress_pdf(src, target_bytes=500)
    assert not res.reached
    assert res.note


def test_compress_preset(tmp_path):
    path = make_image_pdf(str(tmp_path / "img.pdf"), 1)
    src = open(path, "rb").read()
    res = compress.compress_pdf(src, preset="strong")
    assert res.size < len(src)


# ---------- 图片转 PDF ----------

def test_find_cuts_in_blank_rows():
    busy = np.zeros(1000)
    for y in range(0, 1000, 100):  # 每 100 行有 30 行"文字"
        busy[y + 40:y + 70] = 50
    cuts = images.find_cuts(busy, 300, smart=True)
    assert cuts
    for c in cuts:
        assert busy[c] < 2.5 and busy[c - 1] < 2.5  # 切口在空白处


def test_long_image_split(tmp_path):
    path = make_long_image(str(tmp_path / "long.png"))
    opts = images.ImageOptions()
    expected = images.plan_slices(800, 5000, opts)
    doc = images.images_to_pdf([path], opts)
    assert doc.page_count == expected > 3
    assert abs(doc[0].rect.width - 595.28) < 0.1


def test_normal_image_single_page(tmp_path):
    p = str(tmp_path / "photo.jpg")
    Image.new("RGB", (1600, 1200), (200, 100, 50)).save(p)
    doc = images.images_to_pdf([p], images.ImageOptions(quality="original"))
    assert doc.page_count == 1
    assert doc[0].rect.width > doc[0].rect.height  # 横图自动横向


# ---------- 合并与拆分 ----------

def test_merge_mixed(tmp_path):
    a = make_text_pdf(str(tmp_path / "a.pdf"), 3)
    b = make_text_pdf(str(tmp_path / "b.pdf"), 2)
    img = str(tmp_path / "c.png")
    Image.new("RGB", (600, 800), "white").save(img)
    out = merge.merge_files([merge.MergeItem(a, "1,3"), merge.MergeItem(b), merge.MergeItem(img)])
    assert out.page_count == 2 + 2 + 1
    toc = out.get_toc()
    assert [t[1] for t in toc if t[0] == 1] == ["a", "b", "c"]
    assert [t[2] for t in toc if t[0] == 1] == [1, 3, 5]


def test_split_modes(tmp_path):
    src = make_text_pdf(str(tmp_path / "s.pdf"), 7)
    outs = split.split_pdf(src, str(tmp_path / "every"), "every", 3)
    assert [pymupdf.open(p).page_count for p in outs] == [3, 3, 1]
    outs = split.split_pdf(src, str(tmp_path / "ranges"), "ranges", "1-2, 5-7")
    assert [pymupdf.open(p).page_count for p in outs] == [2, 3]
    outs = split.split_pdf(src, str(tmp_path / "single"), "single", None)
    assert len(outs) == 7


def test_split_by_size(tmp_path):
    src = make_image_pdf(str(tmp_path / "big.pdf"), 4, size=(600, 800))
    one_page = split.subset_size(pymupdf.open(src), [0])
    outs = split.split_pdf(src, str(tmp_path / "size"), "size", int(one_page * 2.5))
    sizes = [os.path.getsize(p) for p in outs]
    assert sum(pymupdf.open(p).page_count for p in outs) == 4
    assert len(outs) >= 2
    assert all(s <= one_page * 2.5 for s in sizes)


# ---------- 千问 WAV 修正 ----------

def test_normalize_wav():
    import struct
    import wave

    from folio.tts.qwen import normalize_wav, pcm_to_wav

    good = pcm_to_wav(b"\x00\x01" * 2400)
    bad = bytearray(good)
    bad[40:44] = struct.pack("<I", 2147483547)  # 流式占位长度
    fixed = normalize_wav(bytes(bad))
    w = wave.open(io.BytesIO(fixed))
    assert w.getnframes() == 2400


# ---------- Office 转换（需要 LibreOffice，没装就跳过） ----------

def test_merge_office_rtf(tmp_path):
    from folio.core.office import find_soffice

    if not find_soffice():
        pytest.skip("未安装 LibreOffice")
    rtf = tmp_path / "memo.rtf"
    rtf.write_text(r"{\rtf1\ansi Hello from RTF\par Second line\par}", encoding="ascii")
    a = make_text_pdf(str(tmp_path / "a.pdf"), 1)
    out = merge.merge_files([merge.MergeItem(a), merge.MergeItem(str(rtf))])
    assert out.page_count == 2
    assert "Hello from RTF" in out[1].get_text()
