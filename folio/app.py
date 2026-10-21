"""程序入口：单实例（再次打开文件时交给已运行的窗口）、主题、命令行参数。

    Folio [文件 ...]                     打开文件
    Folio --tool compress 文件 ...       直接打开某个工具（资源管理器右键菜单用），工具名见 TOOL_KEYS
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

from PySide6.QtCore import QByteArray, QLockFile, Qt, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .config import Settings
from .icons import app_icon
from .theme import theme

SERVER_NAME = f"{APP_NAME}-single-instance-{os.environ.get('USERNAME') or os.environ.get('USER') or 'user'}"
TOOL_KEYS = ("compress", "images", "merge", "split")
# 资源管理器里多选文件再点右键菜单时，会同时启动好几个 Folio：先抢到锁的当主程序，其余的等它准备好后把文件交给它
CONNECT_WAIT_MS = 15000
ACK_WAIT_MS = 30000  # 主程序冷启动（杀毒软件扫描等）可能要好几秒，这期间连得上但还不能回复


def parse_args(argv: list[str]) -> tuple[str | None, list[str]]:
    """返回 (工具名或 None, 存在的文件列表)。"""
    tool = None
    files: list[str] = []
    args = argv[1:]
    k = 0
    while k < len(args):
        a = args[k]
        if a == "--tool" and k + 1 < len(args):
            tool = args[k + 1] if args[k + 1] in TOOL_KEYS else None
            k += 2
            continue
        if not a.startswith("-") and os.path.exists(a):
            files.append(os.path.abspath(a))
        k += 1
    return tool, files


def encode_request(tool: str | None, files: list[str]) -> bytes:
    return json.dumps({"tool": tool, "files": files}, ensure_ascii=False).encode("utf-8")


def decode_request(data: bytes) -> tuple[str | None, list[str]]:
    text = data.decode("utf-8", "ignore").strip()
    try:
        req = json.loads(text)
        tool = req.get("tool")
        return (tool if tool in TOOL_KEYS else None), [str(p) for p in req.get("files") or []]
    except (ValueError, AttributeError):
        # 旧版本的格式：每行一个路径，没有文件时是 __activate__
        return None, [p for p in text.splitlines() if p and p != "__activate__"]


def _lock_path() -> str:
    return os.path.join(tempfile.gettempdir(), f"{SERVER_NAME}.lock")


def _send_to_running(payload: bytes, primary_pid: int = 0, wait_ms: int = 300, ack_ms: int = ACK_WAIT_MS) -> bool:
    """把请求交给已经在运行的主程序，等它回复「收到」才算成功。

    主程序可能还在启动（窗口没建好，暂时读不了数据）；Windows 的命名管道不缓存数据，
    这时提前断开请求就丢了，所以要等到回复，最多等 ack_ms。
    """
    sock = QLocalSocket()
    deadline = time.monotonic() + wait_ms / 1000
    while True:
        sock.connectToServer(SERVER_NAME)
        if sock.waitForConnected(300):
            break
        sock.abort()
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)
    if primary_pid and sys.platform == "win32":
        # 用户刚刚双击文件，这个进程有把窗口切到前台的权利；把它让给主程序，主程序的窗口才能弹到最前面
        from .platform_win import allow_foreground

        allow_foreground(primary_pid)
    sock.write(QByteArray(payload.rstrip(b"\n") + b"\n"))
    reply = b""
    deadline = time.monotonic() + ack_ms / 1000
    while True:
        if sock.bytesToWrite():
            sock.waitForBytesWritten(100)
        if sock.bytesAvailable() or sock.waitForReadyRead(100):
            reply += bytes(sock.readAll())
        if reply.endswith(b"\n"):
            break
        if time.monotonic() >= deadline or sock.state() == QLocalSocket.UnconnectedState:
            sock.abort()
            return False
    sock.disconnectFromServer()
    return reply.strip() == b"ok"


def _primary_pid(lock: QLockFile) -> int:
    try:
        info = lock.getLockInfo()
        return int(info[0]) if info else 0
    except Exception:  # noqa: BLE001
        return 0


class InstanceServer:
    """主程序这一端：收到的请求先排队，窗口建好后再处理。"""

    def __init__(self):
        self.handler = None
        self._queue: list[tuple[str | None, list[str]]] = []
        self.server = QLocalServer()
        QLocalServer.removeServer(SERVER_NAME)
        self.server.listen(SERVER_NAME)
        self.server.newConnection.connect(self._on_connection)

    def set_handler(self, handler):
        self.handler = handler
        queued, self._queue = self._queue, []
        for req in queued:
            handler(*req)

    def _on_connection(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            buf = bytearray()
            done = []

            def read(sock=sock, buf=buf, done=done):
                buf.extend(bytes(sock.readAll()))
                if not done and buf.endswith(b"\n"):  # 一个请求一行；收齐后回复，对方收到回复才断开
                    done.append(True)
                    self._dispatch(decode_request(bytes(buf)))
                    sock.write(b"ok\n")
                    sock.flush()

            sock.readyRead.connect(read)
            sock.disconnected.connect(sock.deleteLater)
            if sock.bytesAvailable():
                read()

    def _dispatch(self, req):
        if self.handler is None:
            self._queue.append(req)
        else:
            self.handler(*req)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--selftest" in argv:
        from .selftest import run

        k = argv.index("--selftest")
        return run(argv[k + 1] if k + 1 < len(argv) else "folio-selftest.json")
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Folio.PDF.Reader")
        except Exception:
            pass

    tool, files = parse_args(argv)
    server = None
    lock = None
    if "--new-instance" not in argv:
        lock = QLockFile(_lock_path())
        lock.setStaleLockTime(0)  # 只按进程是否还在判断锁是否失效，不按时间
        if not lock.tryLock(0):
            if _send_to_running(encode_request(tool, files), _primary_pid(lock), CONNECT_WAIT_MS):
                return 0
            lock = None  # 已经在运行的 Folio 没有响应：自己打开一个窗口，不抢它的位置
        else:
            server = InstanceServer()

    settings = Settings()
    theme.apply(app, settings.get("ui/theme"))
    try:
        app.styleHints().colorSchemeChanged.connect(lambda *_: settings.get("ui/theme") == "system" and theme.apply(app))
    except Exception:
        pass

    from .ui.main_window import MainWindow

    win = MainWindow(settings)
    app.aboutToQuit.connect(settings.sync)
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        from .platform_win import sync_context_menu

        QTimer.singleShot(1500, lambda: sync_context_menu(bool(settings.get("shell/context_menu"))))

    if tool:
        # 从右键菜单打开工具：只显示工具窗口，需要时再显示主窗口
        win.handle_request(tool, files)
    else:
        win.show()
        for p in files:
            QTimer.singleShot(0, lambda p=p: win.open_path(p))
    if server is not None:
        QTimer.singleShot(0, lambda: server.set_handler(win.handle_request))
    code = app.exec()
    if lock is not None:
        lock.unlock()
    return code


if __name__ == "__main__":
    sys.exit(main())
