"""系统自带的文字识别：Windows OCR（Windows 10/11）、macOS Vision（实况文本同款），其它系统用 Tesseract。

识别在后台线程里运行，输入是已经渲染好的灰度图（OcrImage），不再调用 PyMuPDF。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from . import OcrError, OcrLine, clamp_box, order_lines


@dataclass
class OcrImage:
    width: int
    height: int
    gray: bytes      # 8 位灰度，逐行排列
    png: bytes
    jpeg: bytes = b""


def _is_cjk(ch: str) -> bool:
    from ..core.textmap import is_cjk

    return is_cjk(ch)


def join_words(words: list[str]) -> str:
    """把识别出的单词拼成一行：中日韩文字之间不加空格（Windows OCR 会把每个汉字当成一个词）。"""
    out = ""
    for w in words:
        w = w.strip()
        if not w:
            continue
        if out and not (_is_cjk(out[-1]) or _is_cjk(w[0])):
            out += " "
        out += w
    return out


def words_to_lines(words: list[tuple[str, float, float, float, float]], width: int, height: int) -> list[OcrLine]:
    """一行里的单词（文字, x0, y0, x1, y1 像素）→ OcrLine；中间有大段空白（分栏）时拆成几行。"""
    if not words:
        return []
    words = sorted(words, key=lambda w: w[1])
    hs = sorted(w[4] - w[2] for w in words)
    gap_limit = max(hs[len(hs) // 2], 1) * 2.5
    groups = [[words[0]]]
    for w in words[1:]:
        if w[1] - groups[-1][-1][3] > gap_limit:
            groups.append([w])
        else:
            groups[-1].append(w)
    out = []
    for g in groups:
        box = clamp_box(min(w[1] for w in g) / width, min(w[2] for w in g) / height,
                        max(w[3] for w in g) / width, max(w[4] for w in g) / height)
        text = join_words([w[0] for w in g])
        if box and text:
            out.append(OcrLine(text, box))
    return out


class SystemOcr:
    name = ""
    install_hint = ""

    @classmethod
    def available(cls) -> bool:
        return False

    def languages(self) -> list[tuple[str, str]]:
        return []

    def recognize(self, img: OcrImage, lang: str = "") -> list[OcrLine]:
        raise NotImplementedError


# ============================================================ Windows
class WindowsOcr(SystemOcr):
    name = "Windows 系统 OCR"
    install_hint = "在 Windows「设置 → 时间和语言 → 语言和区域」里给中文添加「光学字符识别」功能即可识别中文。"

    @classmethod
    def available(cls) -> bool:
        if sys.platform != "win32":
            return False
        try:
            from winrt.windows.media.ocr import OcrEngine  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def _init_thread():
        try:
            from winrt.runtime import ApartmentType, init_apartment

            init_apartment(ApartmentType.MULTI_THREADED)
        except Exception:
            pass  # 已经初始化过

    def languages(self) -> list[tuple[str, str]]:
        from winrt.windows.media.ocr import OcrEngine

        return [(lang.language_tag, lang.display_name) for lang in OcrEngine.available_recognizer_languages]

    def recognize(self, img: OcrImage, lang: str = "") -> list[OcrLine]:
        import numpy as np

        self._init_thread()
        from winrt.windows.globalization import Language
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.media.ocr import OcrEngine

        engine = None
        if lang:
            engine = OcrEngine.try_create_from_language(Language(lang))
        if engine is None:
            engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise OcrError("Windows 没有安装可用的文字识别语言。" + self.install_hint)
        g = np.frombuffer(img.gray, dtype=np.uint8).reshape(img.height, img.width)
        bgra = np.empty((img.height, img.width, 4), dtype=np.uint8)
        bgra[..., 0] = bgra[..., 1] = bgra[..., 2] = g
        bgra[..., 3] = 255
        data = bgra.tobytes()
        try:
            bmp = SoftwareBitmap.create_copy_from_buffer(data, BitmapPixelFormat.BGRA8, img.width, img.height)
        except TypeError:
            from winrt.windows.storage.streams import DataWriter

            w = DataWriter()
            w.write_bytes(data)
            bmp = SoftwareBitmap.create_copy_from_buffer(w.detach_buffer(), BitmapPixelFormat.BGRA8, img.width, img.height)
        result = engine.recognize_async(bmp).get()
        out: list[OcrLine] = []
        for line in result.lines:
            words = []
            for wd in line.words:
                r = wd.bounding_rect
                words.append((wd.text, r.x, r.y, r.x + r.width, r.y + r.height))
            out += words_to_lines(words, img.width, img.height)
        return order_lines(out)


# ============================================================ macOS
class MacVisionOcr(SystemOcr):
    name = "macOS 文字识别（Vision）"
    DEFAULT_LANGS = ["zh-Hans", "zh-Hant", "en-US"]

    @classmethod
    def available(cls) -> bool:
        if sys.platform != "darwin":
            return False
        try:
            import Vision  # noqa: F401
            return True
        except Exception:
            return False

    def languages(self) -> list[tuple[str, str]]:
        import Vision

        req = Vision.VNRecognizeTextRequest.alloc().init()
        try:
            langs, _ = req.supportedRecognitionLanguagesAndReturnError_(None)
        except Exception:
            langs = self.DEFAULT_LANGS
        names = {"zh-Hans": "简体中文", "zh-Hant": "繁體中文", "en-US": "English", "ja-JP": "日本語", "ko-KR": "한국어"}
        return [(str(x), names.get(str(x), str(x))) for x in (langs or [])]

    def recognize(self, img: OcrImage, lang: str = "") -> list[OcrLine]:
        import objc
        import Vision
        from Foundation import NSData

        with objc.autorelease_pool():
            data = NSData.dataWithBytes_length_(img.png, len(img.png))
            handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, {})
            req = Vision.VNRecognizeTextRequest.alloc().init()
            req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            req.setUsesLanguageCorrection_(True)
            req.setRecognitionLanguages_([lang] if lang else self.DEFAULT_LANGS)
            ok, err = handler.performRequests_error_([req], None)
            if not ok:
                raise OcrError(f"macOS 文字识别失败：{err}")
            out: list[OcrLine] = []
            for obs in req.results() or []:
                cands = obs.topCandidates_(1)
                if not cands:
                    continue
                text = str(cands[0].string()).strip()
                bb = obs.boundingBox()  # 归一化坐标，原点在左下角
                x, y, w, h = bb.origin.x, bb.origin.y, bb.size.width, bb.size.height
                box = clamp_box(x, 1 - (y + h), x + w, 1 - y)
                if box and text:
                    out.append(OcrLine(text, box))
            return out


# ============================================================ Tesseract
TESS_NAMES = {"chi_sim": "简体中文", "chi_tra": "繁體中文", "eng": "English", "jpn": "日本語", "kor": "한국어",
              "chi_sim_vert": "简体中文（竖排）", "osd": ""}


def tesseract_path() -> str | None:
    p = shutil.which("tesseract")
    if p:
        return p
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", ""),
                     os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
            cand = os.path.join(base, "Tesseract-OCR", "tesseract.exe")
            if base and os.path.isfile(cand):
                return cand
    for cand in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"):
        if os.path.isfile(cand):
            return cand
    return None


def _no_window() -> dict:
    if sys.platform == "win32":
        return {"creationflags": 0x08000000}  # CREATE_NO_WINDOW
    return {}


class TesseractOcr(SystemOcr):
    name = "Tesseract"
    install_hint = "安装 Tesseract（含 chi_sim 中文语言包）后即可离线识别。"

    @classmethod
    def available(cls) -> bool:
        return tesseract_path() is not None

    def languages(self) -> list[tuple[str, str]]:
        try:
            out = subprocess.run([tesseract_path(), "--list-langs"], capture_output=True, text=True, timeout=10,
                                 **_no_window()).stdout
        except Exception:
            return []
        codes = [ln.strip() for ln in out.splitlines()[1:] if ln.strip()]
        return [(c, TESS_NAMES.get(c, c)) for c in codes if TESS_NAMES.get(c, c)]

    def default_lang(self) -> str:
        have = {c for c, _ in self.languages()}
        want = [c for c in ("chi_sim", "eng") if c in have]
        return "+".join(want) or "eng"

    def recognize(self, img: OcrImage, lang: str = "") -> list[OcrLine]:
        exe = tesseract_path()
        if not exe:
            raise OcrError("没有找到 Tesseract。" + self.install_hint)
        lang = lang or self.default_lang()
        fd, path = tempfile.mkstemp(suffix=".png", prefix="folio-ocr-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(img.png)
            r = subprocess.run([exe, path, "stdout", "-l", lang, "--psm", "3", "tsv"], capture_output=True,
                               timeout=300, **_no_window())
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        if r.returncode != 0:
            raise OcrError("Tesseract 识别失败：" + r.stderr.decode("utf-8", "replace").strip()[-300:])
        return parse_tesseract_tsv(r.stdout.decode("utf-8", "replace"), img.width, img.height)


def parse_tesseract_tsv(tsv: str, width: int, height: int) -> list[OcrLine]:
    lines: dict[tuple, list] = {}
    order: list[tuple] = []
    for row in tsv.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or cols[0] != "5":
            continue
        text = cols[11].strip()
        if not text:
            continue
        try:
            conf = float(cols[10])
        except ValueError:
            conf = 0
        if conf < 0:
            continue
        key = (cols[1], cols[2], cols[3], cols[4])  # page, block, par, line
        left, top, w, h = (int(cols[k]) for k in (6, 7, 8, 9))
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append((text, left, top, left + w, top + h))
    out = []
    for key in order:
        out += words_to_lines(lines[key], width, height)
    return order_lines(out)


# ============================================================ 选择
def system_engine() -> SystemOcr | None:
    for cls in (WindowsOcr, MacVisionOcr, TesseractOcr):
        if cls.available():
            return cls()
    return None


def system_engine_hint() -> str:
    if sys.platform == "win32":
        return "Windows 10/11 自带文字识别。" + WindowsOcr.install_hint
    if sys.platform == "darwin":
        return "使用 macOS 自带的文字识别（与「实况文本」相同）。"
    return "Linux 需要安装 Tesseract，例如：sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
