"""用 PyInstaller 打包成可直接运行的程序。

    pip install -r requirements.txt pyinstaller
    python packaging/build.py

Windows 生成 dist/Folio/Folio.exe，macOS 生成 dist/Folio.app。
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, "packaging", "icons")


def make_icons() -> str | None:
    """从 folio.svg 生成 .ico / .icns。"""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PIL import Image
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    if QGuiApplication.instance() is None:  # SVG 渲染需要 Qt 应用实例
        make_icons.app = QGuiApplication([])
    os.makedirs(ICON_DIR, exist_ok=True)
    renderer = QSvgRenderer(os.path.join(ROOT, "folio", "assets", "folio.svg"))
    png = os.path.join(ICON_DIR, "folio-1024.png")
    img = QImage(1024, 1024, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p, QRectF(0, 0, 1024, 1024))
    p.end()
    img.save(png)
    pil = Image.open(png)
    if sys.platform == "win32":
        out = os.path.join(ICON_DIR, "folio.ico")
        pil.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return out
    if sys.platform == "darwin":
        out = os.path.join(ICON_DIR, "folio.icns")
        pil.save(out)
        return out
    return None


def main():
    icon = make_icons()
    sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", "Folio",
        "--add-data", f"{os.path.join(ROOT, 'folio', 'assets')}{sep}folio/assets",
        # 用不到的大模块，排除掉减小体积
        "--exclude-module", "PySide6.QtWebEngineCore", "--exclude-module", "PySide6.QtWebEngineWidgets",
        "--exclude-module", "PySide6.QtQml", "--exclude-module", "PySide6.QtQuick", "--exclude-module", "PySide6.Qt3DCore",
        "--exclude-module", "PySide6.QtCharts", "--exclude-module", "PySide6.QtDataVisualization",
        "--exclude-module", "PySide6.QtPdf", "--exclude-module", "tkinter",
        # PyMuPDF 2.x 自带的版面分析（ONNX 模型），本程序用不到
        "--exclude-module", "pymupdf.layout", "--exclude-module", "pymupdf_layout", "--exclude-module", "pymupdf4llm",
        "--exclude-module", "onnxruntime", "--exclude-module", "networkx",
        "--hidden-import", "PySide6.QtTextToSpeech", "--hidden-import", "PySide6.QtMultimedia",
    ]
    if icon:
        args += ["--icon", icon]
    if sys.platform == "darwin":
        args += ["--osx-bundle-identifier", "app.folio.pdf"]
    args.append(os.path.join(ROOT, "run.py"))
    print(" ".join(args))
    subprocess.check_call(args, cwd=ROOT)


if __name__ == "__main__":
    main()
