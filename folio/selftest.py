"""打包后的自检：Folio --selftest 结果.json

CI 在打包完成后运行，确认打包出的程序能启动、能渲染 PDF、系统文字识别等依赖都被打包进去了。
"""
from __future__ import annotations

import json
import os
import sys
import traceback


def run(out_path: str) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["FOLIO_NO_UPDATE"] = "1"
    from . import __version__

    result: dict = {"version": __version__, "platform": sys.platform, "checks": {}}
    checks = result["checks"]

    def step(name, fn, critical=True):
        try:
            checks[name] = {"ok": True, "detail": fn()}
        except Exception as ex:  # noqa: BLE001
            checks[name] = {"ok": False, "critical": critical, "detail": f"{ex.__class__.__name__}: {ex}",
                            "trace": traceback.format_exc()[-1500:]}

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([sys.argv[0]])

    def gui():
        from .config import Settings
        from .theme import theme
        from .ui.main_window import MainWindow

        theme.apply(app, "light")
        w = MainWindow(Settings())
        w.close()
        return "ok"

    def pdf():
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Folio selftest 你好", fontname="china-s", fontsize=14)
        pix = page.get_pixmap(dpi=72)
        return f"pymupdf {pymupdf.VersionBind}, {pix.width}x{pix.height}"

    def ocr():
        import pymupdf

        from .ocr.layer import render_for_ocr
        from .ocr.system import OcrImage, system_engine

        eng = system_engine()
        if eng is None:
            return "no system OCR engine"
        doc = pymupdf.open()
        page = doc.new_page(width=420, height=160)
        page.insert_text((30, 90), "Hello Folio 2026", fontname="helv", fontsize=30)
        pix = render_for_ocr(page)
        img = OcrImage(pix.width, pix.height, pix.samples, pix.tobytes("png"))
        lines = eng.recognize(img, "")
        text = " ".join(ln.text for ln in lines)
        if "Folio" not in text and "Hello" not in text:
            raise RuntimeError(f"{eng.name} 识别结果不对：{text!r}")
        return f"{eng.name}: {text}"

    def tts():
        from .tts.engines import SystemEngine

        return f"{len(SystemEngine.voices())} system voices"

    def assets():
        from .icons import asset_path

        names = ("folio.svg", "icons/scan-text.svg", "icons/audio-lines.svg")
        missing = [n for n in names if not os.path.exists(asset_path(n))]
        if missing:
            raise RuntimeError(f"缺少资源文件：{missing}")
        return "ok"

    step("gui", gui)
    step("pdf", pdf)
    step("assets", assets)
    step("ocr", ocr)
    step("tts", tts, critical=False)
    result["ok"] = all(c["ok"] or not c.get("critical", True) for c in checks.values())
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return 0 if result["ok"] else 1
