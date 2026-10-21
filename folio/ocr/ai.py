"""用 AI 视觉模型识别文字，以及用文字模型校对识别结果。

视觉模型按 OpenAI 兼容接口调用，要求按行输出文字和位置（千分比坐标）。
千问的 OCR 专用模型改走 DashScope 原生接口的 advanced_recognition 任务，能拿到精确的像素坐标。
模型没给出位置时，按图片里检测到的文字行依次摆放。
"""
from __future__ import annotations

import base64
import difflib
import json
from dataclasses import replace

import numpy as np

from ..ai import client
from ..ai.client import AIError
from ..ai.hub import Connection, dashscope_host
from . import OcrError, OcrLine, clamp_box
from .system import OcrImage

OCR_PROMPT = (
    "识别图片中的全部文字，按阅读顺序逐行输出。只输出 JSON，不要任何解释：\n"
    '{"lines":[{"text":"这一行的文字","box":[x0,y0,x1,y1]}]}\n'
    "box 是这一行文字的外接矩形，坐标用相对图片宽、高的千分比表示（0~1000 的整数，左上角为原点）。"
    "多栏排版时先读完左栏再读右栏；不要输出图片里没有的文字；图片里没有文字时输出 {\"lines\":[]}。"
)

FIX_PROMPT = (
    "下面是从扫描件中识别出的文字，JSON 数组里每个元素是一行。请只改正明显的识别错误（错别字、形近字、"
    "多余或缺少的空格、错误的标点），不要改写、润色、翻译或补充内容，不要合并或拆分行。"
    "输出 JSON 数组，元素个数和顺序与输入完全相同，只输出 JSON。"
)

FIX_CHUNK = 120


def is_dashscope_ocr(conn: Connection, model: str) -> bool:
    return conn.preset in ("qwen", "qwen_intl") and "ocr" in model.lower() and bool(dashscope_host(conn.base_url))


def recognize(conn: Connection, model: str, img: OcrImage) -> list[OcrLine]:
    if not model:
        raise OcrError(f"还没有为「{conn.name}」选择识别用的视觉模型，请到「设置 → 文字识别」选择。")
    if is_dashscope_ocr(conn, model):
        try:
            return _dashscope_ocr(conn, model, img)
        except AIError as ex:
            if "Key" in str(ex) or "余额" in str(ex):
                raise
            # 原生接口不可用时退回兼容接口
    reply = client.chat(conn, model, [client.image_message(OCR_PROMPT, img.jpeg or img.png,
                                                           "image/jpeg" if img.jpeg else "image/png")], timeout=180)
    return parse_reply(reply, img)


def _dashscope_ocr(conn: Connection, model: str, img: OcrImage) -> list[OcrLine]:
    data = img.jpeg or img.png
    mime = "image/jpeg" if img.jpeg else "image/png"
    native = replace(conn, base_url=dashscope_host(conn.base_url) + "/api/v1")
    body = {"model": model,
            "input": {"messages": [{"role": "user", "content": [
                {"image": f"data:{mime};base64," + base64.b64encode(data).decode("ascii")}]}]},
            "parameters": {"ocr_options": {"task": "advanced_recognition"}}}
    r = client.request(native, "POST", "/services/aigc/multimodal-generation/generation", body, timeout=180, model=model)
    if isinstance(r, dict) and r.get("code"):
        raise AIError(f"{conn.name} 返回错误：{r.get('message') or r.get('code')}")
    try:
        content = r["output"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AIError(f"{conn.name} 没有返回识别结果。") from None
    words = None
    text_reply = ""
    for part in content if isinstance(content, list) else []:
        if isinstance(part, dict):
            ocr = part.get("ocr_result") or {}
            if ocr.get("words_info") is not None:
                words = ocr["words_info"]
            text_reply = text_reply or part.get("text", "")
    if words is None:
        return parse_reply(text_reply, img)
    return _lines_from_items(words, img, pixel_hint=True)


def _coords(item: dict) -> tuple[float, float, float, float] | None:
    for k in ("box", "bbox", "bbox_2d", "rect", "box_2d"):
        v = item.get(k)
        if isinstance(v, (list, tuple)) and len(v) == 4:
            try:
                x0, y0, x1, y1 = (float(t) for t in v)
            except (TypeError, ValueError):
                return None
            return x0, y0, x1, y1
    loc = item.get("location")
    if isinstance(loc, (list, tuple)) and len(loc) >= 8:
        xs, ys = [float(t) for t in loc[0::2]], [float(t) for t in loc[1::2]]
        return min(xs), min(ys), max(xs), max(ys)
    rr = item.get("rotate_rect")
    if isinstance(rr, (list, tuple)) and len(rr) >= 4:
        cx, cy, w, h = (float(t) for t in rr[:4])
        ang = float(rr[4]) if len(rr) > 4 else 0.0
        if 45 <= abs(ang) <= 135:  # 千问的约定：角度 ±90 时宽高互换
            w, h = h, w
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    return None


def _lines_from_items(items: list, img: OcrImage, pixel_hint: bool = False) -> list[OcrLine]:
    raw: list[tuple[str, tuple | None]] = []
    for it in items:
        if isinstance(it, str):
            raw.append((it, None))
        elif isinstance(it, dict):
            text = str(it.get("text") or it.get("content") or it.get("words") or "").strip()
            if text:
                raw.append((text, _coords(it)))
    if not raw:
        return []
    with_box = [c for _, c in raw if c]
    if len(with_box) < max(1, len(raw) * 0.6):
        return fallback_layout([t for t, _ in raw], img)
    biggest = max(max(c) for c in with_box)
    pixels = pixel_hint or biggest > 1005  # 模型没按千分比给坐标，而是给了像素
    sx = 1 / img.width if pixels else 1 / 1000
    sy = 1 / img.height if pixels else 1 / 1000
    out = []
    for text, c in raw:
        box = clamp_box(c[0] * sx, c[1] * sy, c[2] * sx, c[3] * sy) if c else None
        if box:
            out.append(OcrLine(text, box))
    return out


def parse_reply(reply: str, img: OcrImage) -> list[OcrLine]:
    reply = (reply or "").strip()
    if not reply:
        return []
    try:
        data = client.parse_json(reply)
    except (ValueError, json.JSONDecodeError):
        data = None
    if isinstance(data, dict):
        data = data.get("lines") or data.get("words_info") or next((v for v in data.values() if isinstance(v, list)), [])
    if isinstance(data, list):
        return _lines_from_items(data, img)
    # 模型只回了纯文字
    texts = [ln.strip() for ln in reply.replace("```", "").splitlines() if ln.strip()]
    return fallback_layout(texts, img)


def text_bands(img: OcrImage) -> list[tuple[int, int, int, int]]:
    """在灰度图里找出一行行文字所在的横条（像素坐标 x0, y0, x1, y1）。"""
    g = np.frombuffer(img.gray, dtype=np.uint8).reshape(img.height, img.width)
    ink = g < 128
    rows = ink.mean(axis=1) > 0.002
    bands = []
    y = 0
    h = img.height
    while y < h:
        if not rows[y]:
            y += 1
            continue
        y0 = y
        while y < h and rows[y]:
            y += 1
        if y - y0 >= 4:
            cols = np.where(ink[y0:y].any(axis=0))[0]
            if len(cols):
                bands.append((int(cols[0]), y0, int(cols[-1]) + 1, y))
    return bands


def fallback_layout(texts: list[str], img: OcrImage) -> list[OcrLine]:
    texts = [t for t in texts if t.strip()]
    if not texts:
        return []
    bands = text_bands(img)
    out = []
    if bands:
        for k, t in enumerate(texts):
            b = bands[min(len(bands) - 1, int(k * len(bands) / len(texts)))]
            box = clamp_box(b[0] / img.width, b[1] / img.height, b[2] / img.width, b[3] / img.height)
            if box:
                out.append(OcrLine(t, box))
        return out
    step = 0.9 / len(texts)
    for k, t in enumerate(texts):
        y0 = 0.05 + k * step
        out.append(OcrLine(t, (0.08, y0, 0.92, y0 + step * 0.8)))
    return out


def proofread(conn: Connection, model: str, texts: list[str]) -> list[str]:
    """让文字模型改正识别错误；返回的行数对不上、或改动太大的行保持原样。"""
    if not texts:
        return texts
    if not model:
        raise OcrError(f"还没有为「{conn.name}」选择校对用的模型。")
    out: list[str] = []
    for i in range(0, len(texts), FIX_CHUNK):
        chunk = texts[i:i + FIX_CHUNK]
        reply = client.chat(conn, model, [{"role": "system", "content": FIX_PROMPT},
                                          {"role": "user", "content": json.dumps(chunk, ensure_ascii=False)}],
                            timeout=180)
        try:
            data = client.parse_json(reply)
        except (ValueError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), None)
        if not isinstance(data, list) or len(data) != len(chunk):
            out += chunk
            continue
        for old, new in zip(chunk, data):
            new = str(new).strip() if new is not None else ""
            ok = new and difflib.SequenceMatcher(None, old, new).ratio() >= 0.6
            out.append(new if ok else old)
    return out
