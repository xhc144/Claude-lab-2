"""Windows 专用：把 Folio 注册为 PDF 的打开方式（当前用户，无需管理员权限）。"""
from __future__ import annotations

import sys

PROG_ID = "Folio.PDF"


def _exe_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" "%1"'
    # 源码运行：用 pythonw 启动 run.py
    import os

    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py")
    return f'"{pyw}" "{script}" "%1"'


def register_file_association() -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "只在 Windows 上可用。"
    try:
        import winreg

        cmd = _exe_command()
        icon = sys.executable if getattr(sys, "frozen", False) else ""
        base = r"Software\Classes"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\{PROG_ID}") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "PDF 文档")
        if icon:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\{PROG_ID}\DefaultIcon") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f"{icon},0")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\{PROG_ID}\shell\open\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\.pdf\OpenWithProgids") as k:
            winreg.SetValueEx(k, PROG_ID, 0, winreg.REG_NONE, b"")
        try:
            import ctypes

            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)  # SHCNE_ASSOCCHANGED
        except Exception:
            pass
        return True, "已注册。接下来在打开的「默认应用」设置中，把 .pdf 的默认程序选为 Folio 即可。"
    except Exception as ex:  # noqa: BLE001
        return False, f"注册失败：{ex}"
