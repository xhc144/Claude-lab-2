"""Folio —— PDF 阅读、批注、朗读与处理工具。"""
import sys

# PyMuPDF 2.x 导入时会自动加载 ONNX 版面分析模型（约 0.7 秒、上百 MB 内存），本程序用不到，直接屏蔽。
sys.modules.setdefault("pymupdf.layout", None)

APP_NAME = "Folio"
APP_DISPLAY_NAME = "Folio PDF"
__version__ = "0.2.3"
try:  # 打包时 packaging/build.py 会写入实际版本号（例如发布标签 v0.2.0，或开发版 0.2.0.dev15）
    from ._version import VERSION as __version__  # noqa: F401
except ImportError:
    pass
