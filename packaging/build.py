"""用 PyInstaller 打包成可直接运行的程序。

    pip install -r requirements.txt pyinstaller
    python packaging/build.py

Windows 生成 dist/Folio/Folio.exe，macOS 生成 dist/Folio.app。

环境变量：
    FOLIO_VERSION          写入程序的版本号（CI 发布时取自标签，例如 0.2.0）
    MACOS_SIGN_IDENTITY    macOS 代码签名身份（Developer ID Application: …），由 CI 导入证书后设置
"""
from __future__ import annotations

import os
import re
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


def write_version() -> str | None:
    """写入 folio/_version.py：版本号，以及更新清单签名公钥（可以公开）。"""
    version = os.environ.get("FOLIO_VERSION", "").strip().lstrip("v")
    pubkey = os.environ.get("FOLIO_UPDATE_PUBKEY", "").strip()
    if not version and not pubkey:
        return None
    if not version:
        with open(os.path.join(ROOT, "folio", "__init__.py"), encoding="utf-8") as f:
            version = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)
    with open(os.path.join(ROOT, "folio", "_version.py"), "w", encoding="utf-8") as f:
        f.write(f'VERSION = "{version}"\nUPDATE_PUBKEY = "{pubkey}"\n')
    print("version:", version, "| update pubkey:", pubkey or "(none)")
    return version


def main():
    write_version()
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
    if sys.platform == "win32":  # Windows 自带文字识别（WinRT）
        args += ["--collect-submodules", "winrt"]
        for m in ("winrt.windows.media.ocr", "winrt.windows.graphics.imaging", "winrt.windows.storage.streams",
                  "winrt.windows.globalization", "winrt.windows.foundation", "winrt.windows.foundation.collections"):
            args += ["--hidden-import", m]
    if sys.platform == "darwin":  # macOS 自带文字识别（Vision）
        for m in ("objc", "Foundation", "Quartz", "Vision"):
            args += ["--hidden-import", m]
        identity = os.environ.get("MACOS_SIGN_IDENTITY", "").strip()
        if identity:
            args += ["--codesign-identity", identity,
                     "--osx-entitlements-file", os.path.join(ROOT, "packaging", "entitlements.plist")]
    if icon:
        args += ["--icon", icon]
    if sys.platform == "darwin":
        args += ["--osx-bundle-identifier", "app.folio.pdf"]
    args.append(os.path.join(ROOT, "run.py"))
    print(" ".join(args))
    subprocess.check_call(args, cwd=ROOT)


if __name__ == "__main__":
    main()
