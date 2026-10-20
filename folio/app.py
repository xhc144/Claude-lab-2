"""程序入口：单实例（再次打开文件时交给已运行的窗口）、主题、命令行参数。"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .config import Settings
from .icons import app_icon
from .theme import theme

SERVER_NAME = f"{APP_NAME}-single-instance-{os.environ.get('USERNAME') or os.environ.get('USER') or 'user'}"


def _send_to_running(paths: list[str]) -> bool:
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if not sock.waitForConnected(300):
        return False
    payload = "\n".join(os.path.abspath(p) for p in paths) or "__activate__"
    sock.write(QByteArray(payload.encode("utf-8")))
    sock.flush()
    sock.waitForBytesWritten(1000)
    sock.disconnectFromServer()
    return True


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
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

    files = [a for a in argv[1:] if not a.startswith("-") and os.path.exists(a)]
    if "--new-instance" not in argv and _send_to_running(files):
        return 0

    settings = Settings()
    theme.apply(app, settings.get("ui/theme"))
    try:
        app.styleHints().colorSchemeChanged.connect(lambda *_: settings.get("ui/theme") == "system" and theme.apply(app))
    except Exception:
        pass

    from .ui.main_window import MainWindow

    win = MainWindow(settings)

    server = QLocalServer()
    QLocalServer.removeServer(SERVER_NAME)
    server.listen(SERVER_NAME)

    def on_connection():
        sock = server.nextPendingConnection()

        def read():
            data = bytes(sock.readAll()).decode("utf-8", "ignore")
            for p in data.splitlines():
                if p and p != "__activate__":
                    win.open_path(p)
            win.showNormal() if win.isMinimized() else None
            win.raise_()
            win.activateWindow()
        sock.readyRead.connect(read)
    server.newConnection.connect(on_connection)

    win.show()
    for p in files:
        QTimer.singleShot(0, lambda p=p: win.open_path(p))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
