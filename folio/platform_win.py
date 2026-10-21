"""Windows 专用：PDF 打开方式、资源管理器右键菜单、窗口置前、标题栏颜色（都只写当前用户，无需管理员权限）。"""
from __future__ import annotations

import sys

PROG_ID = "Folio.PDF"

# 资源管理器右键菜单（HKCU\Software\Classes 下）：(注册表位置, 菜单文字, 工具名)。
# packaging/installer.iss 里写的是同样的内容，改这里时两边一起改。
CONTEXT_MENU = [
    (r"SystemFileAssociations\.pdf\shell\Folio.Compress", "用 Folio 压缩", "compress"),
    (r"SystemFileAssociations\.pdf\shell\Folio.Merge", "用 Folio 合并", "merge"),
    (r"SystemFileAssociations\image\shell\Folio.ImagesToPdf", "用 Folio 转为 PDF", "images"),
]


def _launcher() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    # 源码运行：用 pythonw 启动 run.py
    import os

    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py")
    return f'"{pyw}" "{script}"'


def _exe_command() -> str:
    return f'{_launcher()} "%1"'


def _notify_shell():
    try:
        import ctypes

        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)  # SHCNE_ASSOCCHANGED
    except Exception:
        pass


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
        _notify_shell()
        return True, "已注册。接下来在打开的「默认应用」设置中，把 .pdf 的默认程序选为 Folio 即可。"
    except Exception as ex:  # noqa: BLE001
        return False, f"注册失败：{ex}"


# ---------------------------------------------------------------- 右键菜单
def _read_value(key: str, name: str = "") -> str | None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def context_menu_installed() -> bool:
    if sys.platform != "win32":
        return False
    return all(_read_value(rf"Software\Classes\{sub}\command") for sub, _, _ in CONTEXT_MENU)


def sync_context_menu(enabled: bool) -> bool:
    """让右键菜单和设置一致（程序位置变了也会更新命令）；返回是否改动了注册表。"""
    if sys.platform != "win32":
        return False
    import winreg

    changed = False
    launcher = _launcher()
    icon = f"{sys.executable},0" if getattr(sys, "frozen", False) else ""
    for sub, text, tool in CONTEXT_MENU:
        key = rf"Software\Classes\{sub}"
        try:
            if enabled:
                cmd = f'{launcher} --tool {tool} "%1"'
                if _read_value(key + r"\command") == cmd and _read_value(key, "MUIVerb") == text:
                    continue
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
                    winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, text)
                    if icon:
                        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon)
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key + r"\command") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)
                changed = True
            elif _read_value(key, "MUIVerb") is not None or _read_value(key + r"\command") is not None:
                for k in (key + r"\command", key):
                    try:
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, k)
                    except OSError:
                        pass
                changed = True
        except OSError:
            pass
    if changed:
        _notify_shell()
    return changed


# ---------------------------------------------------------------- 窗口
def allow_foreground(pid: int):
    """把当前进程切换前台窗口的权利让给 pid（由刚被用户启动的那个进程调用）。"""
    try:
        import ctypes

        ctypes.windll.user32.AllowSetForegroundWindow(int(pid))
    except Exception:
        pass


def bring_to_front(hwnd: int):
    try:
        import ctypes

        user32 = ctypes.windll.user32
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _colorref(color) -> int:
    return color.red() | (color.green() << 8) | (color.blue() << 16)


def style_title_bar(hwnd: int, caption, text, dark: bool):
    """标题栏跟随界面主题：深色模式（Windows 10 2004 起），标题栏底色和文字颜色（Windows 11 起，旧系统会忽略）。"""
    try:
        import ctypes
        from ctypes import byref, c_int, sizeof

        dwm = ctypes.windll.dwmapi
        flag = c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE（19 是 2004 之前的编号）
            if dwm.DwmSetWindowAttribute(hwnd, attr, byref(flag), sizeof(flag)) == 0:
                break
        for attr, color in ((35, caption), (36, text)):  # DWMWA_CAPTION_COLOR, DWMWA_TEXT_COLOR
            if color is not None:
                v = c_int(_colorref(color))
                dwm.DwmSetWindowAttribute(hwnd, attr, byref(v), sizeof(v))
    except Exception:
        pass
