"""自动更新：版本比较、清单、下载校验、解压、替换脚本。"""
import hashlib
import io
import json
import os
import subprocess
import sys
import threading
import time
import zipfile

import pytest

from folio import update

from .fakeserver import FakeServer


@pytest.fixture
def server():
    s = FakeServer()
    yield s
    s.close()


def test_version_order():
    order = ["0.1.0", "0.2.0.dev3", "0.2.0.dev15", "v0.2.0-beta.1", "0.2.0", "0.2.1", "0.10.0", "1.0"]
    keys = [update.parse_version(v) for v in order]
    assert keys == sorted(keys)
    assert update.is_newer("0.2.0", "0.2.0.dev15")
    assert not update.is_newer("0.2.0", "0.2.0")
    assert update.parse_version("v1.2.3+abc") == update.parse_version("1.2.3")


def test_parse_manifest():
    data = {"version": "0.3.0", "notes": "说明", "assets": {
        "windows-x64": {"url": "https://x/Folio-windows.zip", "sha256": "AB", "size": 10}}}
    info = update.parse_manifest(data, "windows-x64")
    assert (info.version, info.url, info.sha256, info.size) == ("0.3.0", "https://x/Folio-windows.zip", "ab", 10)
    assert update.parse_manifest(data, "macos-arm64").url == ""
    with pytest.raises(update.UpdateError):
        update.parse_manifest({}, "windows-x64")


def test_check(server, monkeypatch):
    monkeypatch.setattr(update, "platform_key", lambda: "windows-x64")
    server.json("GET", "/latest.json", {"version": "99.0.0", "assets": {"windows-x64": {"url": "u", "sha256": "s"}}})
    info = update.check(server.url + "/latest.json")
    assert info is not None and info.version == "99.0.0"
    server.json("GET", "/latest.json", {"version": "0.0.1", "assets": {}})
    assert update.check(server.url + "/latest.json") is None
    assert update.check(server.url + "/missing.json") is None  # 还没发布过
    with pytest.raises(update.UpdateError):
        update.check("http://example.com/latest.json")  # 不是 https


def make_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_download_verifies_hash(server, tmp_path):
    data = make_zip({"Folio/Folio.exe": b"new"})
    server.routes[("GET", "/pkg.zip")] = lambda body: (200, data, "application/zip")
    good = update.UpdateInfo("9.9.9", "", server.url + "/pkg.zip", hashlib.sha256(data).hexdigest(), len(data))
    progress = []
    path = update.download(good, str(tmp_path / "dl"), lambda f, m: progress.append(f))
    assert open(path, "rb").read() == data and progress[-1] == 1.0
    bad = update.UpdateInfo("9.9.9", "", server.url + "/pkg.zip", "0" * 64, len(data))
    with pytest.raises(update.UpdateError, match="校验失败"):
        update.download(bad, str(tmp_path / "dl2"))
    no_hash = update.UpdateInfo("9.9.9", "", server.url + "/pkg.zip", "", len(data))
    with pytest.raises(update.UpdateError, match="缺少校验值"):
        update.download(no_hash, str(tmp_path / "dl3"))


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS 用 ditto 解压 .app，单独测试")
def test_extract(tmp_path):
    exe = "Folio.exe" if sys.platform == "win32" else "Folio"
    z = tmp_path / "pkg.zip"
    z.write_bytes(make_zip({f"Folio/{exe}": b"new", "Folio/_internal/lib.dll": b"x"}))
    root = update.extract(str(z), str(tmp_path / "stage"))
    assert os.path.isfile(os.path.join(root, exe))
    evil = tmp_path / "evil.zip"
    evil.write_bytes(make_zip({"../outside.txt": b"x"}))
    with pytest.raises(update.UpdateError, match="不安全"):
        update.extract(str(evil), str(tmp_path / "stage2"))


def test_not_frozen_cannot_self_update():
    ok, why = update.can_self_update()
    assert not ok and why
    assert update.install_root() is None


def _sleeper() -> subprocess.Popen:
    """模拟正在运行的旧版程序：1.5 秒后退出（后台线程回收进程，避免变成僵尸进程让脚本一直等）。"""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1.5)"])
    threading.Thread(target=proc.wait, daemon=True).start()
    return proc


def _wait_for(cond, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.2)
    return False


def _make_dirs(tmp_path, name):
    dst = tmp_path / name
    dst.mkdir()
    (dst / "version.txt").write_text("old")
    src = tmp_path / ".folio-update" / "Folio"
    src.mkdir(parents=True)
    (src / "version.txt").write_text("new")
    return src, dst


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 替换脚本")
def test_windows_swap_script(tmp_path):
    src, dst = _make_dirs(tmp_path, "Folio App")
    script = tmp_path / "update.ps1"
    script.write_text(update.WIN_SCRIPT, encoding="utf-8-sig")
    marker = tmp_path / "launched.txt"
    launcher = tmp_path / "launch.cmd"
    launcher.write_text(f'@echo started> "{marker}"\r\n')
    proc = _sleeper()
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                        "-ProcId", str(proc.pid), "-Src", str(src), "-Dst", str(dst), "-Exe", str(launcher)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert (dst / "version.txt").read_text() == "new"
    assert _wait_for(marker.exists)
    assert not [p for p in tmp_path.iterdir() if p.name.startswith("Folio App.old-")]
    assert not (tmp_path / ".folio-update").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="macOS 替换脚本（Linux 上用假的 open/xattr 测试）")
def test_posix_swap_script(tmp_path):
    src, dst = _make_dirs(tmp_path, "Folio.app")
    marker = tmp_path / "opened.txt"
    env = dict(os.environ)
    if sys.platform != "darwin":
        fake = tmp_path / "bin"
        fake.mkdir()
        (fake / "open").write_text(f'#!/bin/sh\necho "$1" > "{marker}"\n')
        (fake / "xattr").write_text("#!/bin/sh\nexit 0\n")
        for f in fake.iterdir():
            f.chmod(0o755)
        env["PATH"] = f"{fake}:{env['PATH']}"
    script = tmp_path / "update.sh"
    script.write_text(update.MAC_SCRIPT)
    proc = _sleeper()
    r = subprocess.run(["/bin/sh", str(script), str(proc.pid), str(src), str(dst)], env=env, capture_output=True,
                       text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert (dst / "version.txt").read_text() == "new"
    assert proc.poll() is not None  # 等到原进程退出后才替换
    if sys.platform != "darwin":
        assert marker.read_text().strip() == str(dst)
    assert not [p for p in tmp_path.iterdir() if p.name.startswith("Folio.app.old-")]
    assert not (tmp_path / ".folio-update").exists()


def test_manifest_script(tmp_path):
    zw = tmp_path / "Folio-windows.zip"
    zw.write_bytes(b"windows-build")
    notes = tmp_path / "CHANGELOG.md"
    notes.write_text("# 更新记录\n\n## 0.3.0\n\n- 新功能\n\n## 0.2.0\n\n- 旧功能\n", encoding="utf-8")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = tmp_path / "latest.json"
    subprocess.run([sys.executable, os.path.join(root, "packaging", "make_manifest.py"), "--version", "v0.3.0",
                    "--base-url", "https://example.com/dl/v0.3.0", "--asset", f"windows-x64={zw}",
                    "--asset", f"macos-arm64={tmp_path / 'missing.zip'}", "--notes", str(notes), "--out", str(out)],
                   check=True)
    m = json.loads(out.read_text(encoding="utf-8"))
    assert m["version"] == "0.3.0" and m["notes"] == "- 新功能"
    assert m["assets"]["windows-x64"] == {"url": "https://example.com/dl/v0.3.0/Folio-windows.zip",
                                          "sha256": hashlib.sha256(b"windows-build").hexdigest(), "size": 13}
    assert "macos-arm64" not in m["assets"]
    info = update.parse_manifest(m, "windows-x64")
    assert info.sha256 == m["assets"]["windows-x64"]["sha256"]


def test_update_dialog_installs_on_close(qapp, monkeypatch):
    from folio.config import Settings
    from folio.ui.dialogs.update_dialog import UpdateDialog
    from folio.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog

    win = MainWindow(Settings())
    win.show()
    info = update.UpdateInfo("9.9.9", "- 新功能", "https://example.com/Folio.zip", "ab" * 32, 1)
    d = UpdateDialog(win, info)
    assert d.ok_btn.text() == "打开下载页面"  # 从源码运行时不能自动安装
    d.reject()

    monkeypatch.setattr(update, "can_self_update", lambda: (True, ""))
    monkeypatch.setattr(update, "prepare", lambda info, progress=None, cancelled=None: "/new/Folio")
    launched = []
    monkeypatch.setattr(update, "launch_installer", launched.append)
    other = QDialog(win)  # 例如从「设置」里检查更新时，设置窗口还开着
    other.show()
    d = UpdateDialog(win, info)
    assert d.ok_btn.text() == "立即更新"
    d.show()
    d._install()
    end = time.time() + 10
    while time.time() < end and not launched:
        qapp.processEvents()
        time.sleep(0.01)
    assert launched == ["/new/Folio"]
    assert not win.isVisible() and not other.isVisible()
