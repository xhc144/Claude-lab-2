"""单实例、右键菜单打开工具、工具窗口、标签栏和更新提示。"""
import os
import sys
import time

import pytest
from PySide6.QtCore import QLockFile

from .test_core import make_text_pdf
from .test_gui import open_doc, pump, win  # noqa: F401  （win 是 fixture）


# ---------------------------------------------------------------- 命令行和请求格式
def test_parse_args(tmp_path):
    from folio.app import parse_args

    a = make_text_pdf(str(tmp_path / "a.pdf"), 1)
    b = make_text_pdf(str(tmp_path / "b.pdf"), 1)
    assert parse_args(["Folio", a]) == (None, [a])
    assert parse_args(["Folio", "--tool", "compress", a, b]) == ("compress", [a, b])
    assert parse_args(["Folio", a, "--tool", "merge", str(tmp_path / "missing.pdf")]) == ("merge", [a])
    assert parse_args(["Folio", "--tool", "format-disk", a]) == (None, [a])  # 不认识的工具名忽略
    assert parse_args(["Folio", "--new-instance"]) == (None, [])


def test_request_roundtrip():
    from folio.app import decode_request, encode_request

    files = ["C:\\文件\\一.pdf", "/tmp/二 三.pdf"]
    assert decode_request(encode_request("compress", files)) == ("compress", files)
    assert decode_request(encode_request(None, [])) == (None, [])
    assert decode_request(b'{"tool": "rm", "files": []}') == (None, [])
    # 旧版本的格式
    assert decode_request("/a.pdf\n/b.pdf".encode()) == (None, ["/a.pdf", "/b.pdf"])
    assert decode_request(b"__activate__") == (None, [])


def test_instance_server_forwards(qapp, monkeypatch):
    from folio import app as appmod

    monkeypatch.setattr(appmod, "SERVER_NAME", f"folio-test-{os.getpid()}-{time.time_ns()}")
    server = appmod.InstanceServer()
    got = []
    # 窗口还没建好时收到的请求先排队
    assert appmod._send_to_running(appmod.encode_request("compress", ["/x/1.pdf"]), wait_ms=2000)
    for _ in range(100):
        pump(qapp, 10)
        if server._queue:
            break
    assert server._queue == [("compress", ["/x/1.pdf"])]
    server.set_handler(lambda tool, files: got.append((tool, files)))
    assert got == [("compress", ["/x/1.pdf"])]
    # 之后的请求直接交给窗口
    for k in range(3):
        assert appmod._send_to_running(appmod.encode_request("merge", [f"/x/{k}.pdf"]), wait_ms=2000)
    for _ in range(200):
        pump(qapp, 10)
        if len(got) == 4:
            break
    assert sorted(got[1:]) == [("merge", ["/x/0.pdf"]), ("merge", ["/x/1.pdf"]), ("merge", ["/x/2.pdf"])]
    server.server.close()


def test_send_without_server_gives_up(qapp, monkeypatch):
    from folio import app as appmod

    monkeypatch.setattr(appmod, "SERVER_NAME", f"folio-none-{os.getpid()}-{time.time_ns()}")
    t = time.time()
    assert not appmod._send_to_running(b"{}", wait_ms=600)
    assert time.time() - t < 5


def test_lock_elects_one_primary(qapp, tmp_path):
    from folio.app import _primary_pid

    path = str(tmp_path / "folio.lock")
    first = QLockFile(path)
    first.setStaleLockTime(0)
    assert first.tryLock(0)
    second = QLockFile(path)
    second.setStaleLockTime(0)
    assert not second.tryLock(0)  # 同时启动的其它进程拿不到锁，改为把文件交给主程序
    assert _primary_pid(second) == os.getpid()
    first.unlock()
    assert second.tryLock(0)
    second.unlock()


# ---------------------------------------------------------------- 工具窗口
def test_tool_windows_are_independent_and_merge_requests(win, qapp, tmp_path):  # noqa: F811
    a = make_text_pdf(str(tmp_path / "a.pdf"), 1)
    b = make_text_pdf(str(tmp_path / "b.pdf"), 1)
    win.handle_request("compress", [a])
    pump(qapp, win.TOOL_REQUEST_DELAY_MS + 100)
    assert len(win.tool_windows) == 1
    dlg = win.tool_windows[0]
    # 独立窗口：不是主窗口的子窗口，也不是模态，主窗口照常可以操作
    assert dlg.parent() is None and not dlg.isModal() and dlg.isVisible()
    assert win.isEnabled() and QApplicationModal() is None
    # 资源管理器里多选：第二个文件加进同一个窗口
    win.handle_request("compress", [b])
    pump(qapp, win.TOOL_REQUEST_DELAY_MS + 100)
    assert win.tool_windows == [dlg]
    assert dlg.files.paths() == [a, b]
    # 从主页再点「压缩」也回到这个窗口
    assert win.open_tool("compress") is dlg
    # 正在处理时，新的请求开新窗口
    dlg.worker = object()
    other = win.open_tool("compress", [a])
    assert other is not dlg and len(win.tool_windows) == 2
    dlg.worker = None
    # 文件拖到窗口任何地方都能加进去，不支持的类型忽略
    txt = tmp_path / "note.txt"
    txt.write_text("x")
    other.add_paths([str(txt), b])
    assert other.files.paths() == [a, b]
    other.close()
    pump(qapp, 30)
    assert win.tool_windows == [dlg]


def test_batched_requests_sorted_by_name(win, qapp, tmp_path):  # noqa: F811
    from folio.ui.main_window import natural_key

    names = ["第10页.pdf", "第2页.pdf", "第1页.pdf", "b.pdf", "A.pdf"]
    paths = [make_text_pdf(str(tmp_path / n), 1) for n in names]
    for p in paths + [paths[0]]:  # 同一个文件送来两次只算一次
        win.handle_request("merge", [p])
    pump(qapp, win.TOOL_REQUEST_DELAY_MS + 150)
    assert len(win.tool_windows) == 1
    got = [os.path.basename(p) for p in win.tool_windows[0].files.paths()]
    assert got == ["A.pdf", "b.pdf", "第1页.pdf", "第2页.pdf", "第10页.pdf"]
    assert sorted(["x10.pdf", "x9.pdf", "x.pdf"], key=natural_key) == ["x.pdf", "x9.pdf", "x10.pdf"]


def QApplicationModal():
    from PySide6.QtWidgets import QApplication

    return QApplication.activeModalWidget()


def test_closing_main_closes_tool_windows(win, qapp, tmp_path):  # noqa: F811
    a = make_text_pdf(str(tmp_path / "a.pdf"), 1)
    dlg = win.open_tool("merge", [a])
    pump(qapp, 20)
    assert dlg.isVisible()
    win.close()
    pump(qapp, 30)
    assert win.tool_windows == []


def test_tool_only_start_shows_main_when_needed(qapp, tmp_path):
    """从右键菜单启动时只显示工具窗口；之后要打开文档时主窗口才出现。"""
    from folio.config import Settings
    from folio.ui.main_window import MainWindow

    s = Settings()
    s.set("view/restore_position", False)
    w = MainWindow(s)
    a = make_text_pdf(str(tmp_path / "a.pdf"), 2)
    w.handle_request("split", [a])
    pump(qapp, w.TOOL_REQUEST_DELAY_MS + 100)
    dlg = w.tool_windows[0]
    assert dlg.isVisible() and not w.isVisible()
    assert dlg.src.text() == a
    dlg._last_output = a
    dlg._open_doc()  # 「在 Folio 中打开」
    pump(qapp, 50)
    assert w.isVisible() and len(w.tabs_widgets) == 1
    w.close()


def test_request_opens_documents_and_activates(win, qapp, tmp_path):  # noqa: F811
    a = make_text_pdf(str(tmp_path / "a.pdf"), 2)
    win.showMinimized()
    pump(qapp, 30)
    win.handle_request(None, [a])
    pump(qapp, 50)
    assert not win.isMinimized()
    assert len(win.tabs_widgets) == 1 and win.cur.doc.path == a


# ---------------------------------------------------------------- 界面
def test_tab_strip_layout(win, qapp, tmp_path):  # noqa: F811
    # 没有标签时加号紧挨着主页按钮
    assert not win.tabbar.isVisible()
    open_doc(win, qapp, tmp_path, 1)
    assert win.tabbar.isVisible()
    assert not win.tabbar.property("home")
    win.show_home()
    pump(qapp, 20)
    assert win.tabbar.property("home")  # 在主页时标签不显示为选中
    # 主菜单在标签栏上，主页也看得到
    assert win.btn_more.isVisible()


def test_toolbar_collapses_when_narrow(win, qapp, tmp_path):  # noqa: F811
    open_doc(win, qapp, tmp_path, 1)
    win.resize(1600, 800)
    pump(qapp, 30)
    assert win.btn_print.isVisible() and win.btn_zoom_in.isVisible()
    win.resize(900, 700)
    pump(qapp, 30)
    lay = win.topbar.layout()
    assert lay.sizeHint().width() <= win.topbar.width() + 4  # 按钮不会挤在一起
    assert not win.btn_print.isVisible()
    win.resize(1600, 800)
    pump(qapp, 30)
    assert win.btn_print.isVisible()


def test_update_badge_and_home_footer(win, qapp):  # noqa: F811
    from folio import __version__
    from folio.update import UpdateInfo

    assert __version__ in win.home.version_label.text()
    assert not win.update_btn.isVisible()
    win._set_update_info(UpdateInfo("99.0.0", "", "", "", 0))
    pump(qapp, 20)
    assert win.update_btn.isVisible() and "99.0.0" in win.update_btn.text()
    assert "99.0.0" in win.home.update_link.text()
    win._set_update_info(None)
    assert not win.update_btn.isVisible()
    assert win.home.update_link.text() == "检查更新"


@pytest.mark.skipif(sys.platform != "win32" or not os.environ.get("CI"), reason="只在 Windows CI 上改注册表")
def test_context_menu_registry():
    from folio.platform_win import CONTEXT_MENU, _read_value, context_menu_installed, sync_context_menu

    try:
        assert sync_context_menu(True)
        assert context_menu_installed()
        sub, text, tool = CONTEXT_MENU[0]
        cmd = _read_value(rf"Software\Classes\{sub}\command")
        assert f"--tool {tool}" in cmd and '"%1"' in cmd
        assert not sync_context_menu(True)  # 已经一致时不再改动
        assert sync_context_menu(False)
        assert not context_menu_installed()
    finally:
        sync_context_menu(False)
