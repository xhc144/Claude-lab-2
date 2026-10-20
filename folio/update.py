"""自动更新：读取发布清单 latest.json → 下载对应平台的安装包 → 校验 → 退出后替换程序目录并重新启动。

清单由 GitHub Actions 在发布 v* 标签时生成，格式：
    {"version": "0.2.0", "date": "...", "notes": "...", "page": "https://…",
     "assets": {"windows-x64": {"url": "...", "sha256": "...", "size": 123}, "macos-arm64": {...}}}

安全措施：只从 HTTPS 下载；校验 SHA-256；当前程序带有代码签名时，新版本必须由同一签名者签名；
打包时写入了更新公钥（仓库密钥 UPDATE_SIGNING_KEY 对应的公钥）时，清单必须带有这把密钥的 Ed25519 签名。
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass

from . import APP_NAME, __version__

try:  # 打包时由 packaging/build.py 写入
    from ._version import UPDATE_PUBKEY
except ImportError:
    UPDATE_PUBKEY = ""

REPO = "xhc144/Claude-lab-2"
DEFAULT_FEED = f"https://github.com/{REPO}/releases/latest/download/latest.json"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
CHECK_INTERVAL = 20 * 3600


class UpdateError(RuntimeError):
    pass


@dataclass
class UpdateInfo:
    version: str
    notes: str
    url: str
    sha256: str
    size: int
    page: str = RELEASES_PAGE
    date: str = ""


# ---------------------------------------------------------------- 版本号
def parse_version(v: str) -> tuple:
    """'v1.2.3'、'1.2.3-beta.1'、'1.2.3.dev5+abc' → 可比较的元组；预发布版本小于正式版。"""
    v = v.strip().lstrip("vV").split("+")[0]
    m = re.match(r"(\d+(?:\.\d+)*)(.*)$", v)
    if not m:
        return (0,)
    nums = [int(x) for x in m.group(1).split(".")]
    while len(nums) < 3:
        nums.append(0)
    rest = m.group(2).lstrip(".-_").lower()
    if not rest:
        return (*nums, 9, 0)
    rank = 0  # dev < alpha < beta < rc < 正式版
    for word, r in (("rc", 3), ("c", 3), ("beta", 2), ("b", 2), ("alpha", 1), ("a", 1), ("dev", 0)):
        if rest.startswith(word):
            rank = r
            break
    n = re.search(r"(\d+)$", rest)
    return (*nums, rank, int(n.group(1)) if n else 0)


def is_newer(remote: str, local: str = __version__) -> bool:
    return parse_version(remote) > parse_version(local)


def platform_key() -> str | None:
    if sys.platform == "win32":
        return "windows-x64"
    if sys.platform == "darwin":
        return "macos-arm64" if platform.machine() == "arm64" else "macos-x64"
    return None


# ---------------------------------------------------------------- 检查
def _open(url: str, timeout: float):
    if not url.lower().startswith("https://") and not url.lower().startswith("http://127.0.0.1"):
        raise UpdateError("更新地址必须是 https 链接")
    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{__version__}", "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=timeout)


def parse_manifest(data: dict, key: str | None = None) -> UpdateInfo | None:
    key = key or platform_key()
    ver = str(data.get("version") or "")
    if not ver:
        raise UpdateError("更新清单格式不正确")
    asset = (data.get("assets") or {}).get(key or "")
    url = asset.get("url", "") if asset else ""
    return UpdateInfo(version=ver, notes=str(data.get("notes") or ""), url=url,
                      sha256=str(asset.get("sha256", "") if asset else "").lower(),
                      size=int(asset.get("size", 0) if asset else 0),
                      page=str(data.get("page") or RELEASES_PAGE), date=str(data.get("date") or ""))


def _canonical(data: dict) -> bytes:
    """与 packaging/update_key.py 的 canonical() 一致。"""
    body = {k: v for k, v in data.items() if k != "signature"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_manifest(data: dict, pubkey: str | None = None):
    """程序内置了更新公钥时，清单必须带有对应的有效签名。"""
    pubkey = UPDATE_PUBKEY if pubkey is None else pubkey
    if not pubkey:
        return
    sig = data.get("signature") or {}
    if not isinstance(sig, dict) or not sig.get("sig"):
        raise UpdateError("更新清单没有签名，已拒绝安装")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        raise UpdateError("缺少验证更新签名所需的组件") from None
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pubkey)).verify(
            base64.b64decode(sig["sig"]), _canonical(data))
    except (InvalidSignature, ValueError, TypeError):
        raise UpdateError("更新清单签名无效，可能被篡改，已拒绝安装") from None


def check(feed: str = "", timeout: float = 15) -> UpdateInfo | None:
    """有新版本时返回 UpdateInfo，否则 None。"""
    try:
        with _open(feed or DEFAULT_FEED, timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except UpdateError:
        raise
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return None  # 还没有发布过版本
        raise UpdateError(f"检查更新失败（{ex.code}）") from None
    except Exception as ex:  # noqa: BLE001
        raise UpdateError(f"检查更新失败：{getattr(ex, 'reason', ex)}") from None
    verify_manifest(data)
    info = parse_manifest(data)
    return info if info and is_newer(info.version) else None


# ---------------------------------------------------------------- 安装位置
def install_root() -> str | None:
    """打包后程序所在的目录（Windows）或 .app 包（macOS）；从源码运行时为 None。"""
    if not getattr(sys, "frozen", False):
        return None
    exe = os.path.abspath(sys.executable)
    if sys.platform == "darwin":
        app = os.path.dirname(os.path.dirname(os.path.dirname(exe)))
        return app if app.endswith(".app") else None
    if sys.platform == "win32":
        return os.path.dirname(exe)
    return None


def can_self_update() -> tuple[bool, str]:
    root = install_root()
    if root is None:
        return False, "当前是从源码运行，请用 git pull 更新。" if not getattr(sys, "frozen", False) else "当前系统不支持自动安装更新。"
    parent = os.path.dirname(root)
    if not (os.access(root, os.W_OK) and os.access(parent, os.W_OK)):
        return False, f"没有权限写入 {parent}，请手动下载新版本。"
    return True, ""


# ---------------------------------------------------------------- 下载与校验
def download(info: UpdateInfo, dest: str, progress=None, cancelled=None) -> str:
    if not info.url:
        raise UpdateError("这个版本没有适合当前系统的安装包，请到下载页面查看。")
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, os.path.basename(info.url.split("?")[0]) or "update.zip")
    h = hashlib.sha256()
    got = 0
    try:
        with _open(info.url, 60) as r, open(path, "wb") as f:
            total = int(r.headers.get("Content-Length") or info.size or 0)
            while True:
                if cancelled and cancelled():
                    raise UpdateError("已取消")
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                got += len(chunk)
                if progress and total:
                    progress(got / total, f"正在下载 {got / 1048576:.1f} / {total / 1048576:.1f} MB")
    except UpdateError:
        raise
    except Exception as ex:  # noqa: BLE001
        raise UpdateError(f"下载失败：{getattr(ex, 'reason', ex)}") from None
    if info.size and got != info.size:
        raise UpdateError("下载的文件不完整，请重试。")
    if not info.sha256:
        raise UpdateError("更新清单里缺少校验值，已停止更新。")
    if h.hexdigest() != info.sha256:
        raise UpdateError("下载的文件校验失败（SHA-256 不一致），已停止更新。")
    return path


def extract(zip_path: str, staging: str) -> str:
    """解压到 staging，返回新版本的程序目录 / .app 路径。"""
    if os.path.exists(staging):
        shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging)
    if sys.platform == "darwin":
        # ditto 能保留符号链接、权限和代码签名
        subprocess.run(["ditto", "-x", "-k", zip_path, staging], check=True, capture_output=True)
    else:
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():
                target = os.path.realpath(os.path.join(staging, name))
                if not target.startswith(os.path.realpath(staging) + os.sep):
                    raise UpdateError("安装包里有不安全的路径，已停止更新。")
            z.extractall(staging)
    for name in os.listdir(staging):
        cand = os.path.join(staging, name)
        if sys.platform == "darwin" and name.endswith(".app"):
            return cand
        if sys.platform != "darwin" and os.path.isfile(os.path.join(cand, f"{APP_NAME}.exe" if sys.platform == "win32" else APP_NAME)):
            return cand
    raise UpdateError("安装包内容不正确，找不到程序。")


# ---------------------------------------------------------------- 签名
def _no_window() -> dict:
    return {"creationflags": 0x08000000} if sys.platform == "win32" else {}


def signer(path: str) -> dict:
    """读取代码签名：{'signed': bool, 'valid': bool, 'id': 签名者标识}。"""
    try:
        if sys.platform == "win32":
            ps = ("$s = Get-AuthenticodeSignature -LiteralPath $env:FOLIO_SIG_PATH; "
                  "[pscustomobject]@{status=[string]$s.Status; thumb=$s.SignerCertificate.Thumbprint; "
                  "subject=$s.SignerCertificate.Subject} | ConvertTo-Json -Compress")
            r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True,
                               text=True, timeout=30, env={**os.environ, "FOLIO_SIG_PATH": path}, **_no_window())
            d = json.loads(r.stdout or "{}")
            status = d.get("status") or ""
            return {"signed": status not in ("", "NotSigned"), "valid": status == "Valid", "id": d.get("subject") or ""}
        if sys.platform == "darwin":
            ok = subprocess.run(["codesign", "--verify", "--deep", "--strict", path], capture_output=True).returncode == 0
            r = subprocess.run(["codesign", "-dv", "--verbose=2", path], capture_output=True, text=True)
            team = re.search(r"TeamIdentifier=(\S+)", r.stderr or "")
            team_id = team.group(1) if team and team.group(1) != "not" else ""
            return {"signed": bool(team_id), "valid": ok, "id": team_id}
    except Exception:
        pass
    return {"signed": False, "valid": False, "id": ""}


def _main_binary(root: str) -> str:
    if sys.platform == "win32":
        return os.path.join(root, f"{APP_NAME}.exe")
    return root


def verify_same_signer(current_root: str, new_root: str):
    cur = signer(_main_binary(current_root))
    if not cur["signed"]:
        return  # 当前版本没有签名，只能依赖 HTTPS 和 SHA-256
    new = signer(_main_binary(new_root))
    if not new["valid"] or new["id"] != cur["id"]:
        raise UpdateError("新版本的数字签名与当前版本不一致，已停止更新。")


# ---------------------------------------------------------------- 安装
WIN_SCRIPT = r"""
param([int]$ProcId, [string]$Src, [string]$Dst, [string]$Exe)
$ErrorActionPreference = 'Stop'
try { Wait-Process -Id $ProcId -Timeout 120 -ErrorAction SilentlyContinue } catch {}
Start-Sleep -Milliseconds 400
$bak = "$Dst.old-" + (Get-Date -Format 'yyyyMMddHHmmss')
$moved = $false
for ($i = 0; $i -lt 40; $i++) {
  try { Rename-Item -LiteralPath $Dst -NewName (Split-Path $bak -Leaf); $moved = $true; break } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $moved) { Start-Process -FilePath $Exe; exit 1 }
try {
  Move-Item -LiteralPath $Src -Destination $Dst
} catch {
  Rename-Item -LiteralPath $bak -NewName (Split-Path $Dst -Leaf)
  Start-Process -FilePath $Exe
  exit 1
}
Start-Process -FilePath $Exe
Start-Sleep -Seconds 2
Remove-Item -LiteralPath $bak -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Split-Path $Src -Parent) -Recurse -Force -ErrorAction SilentlyContinue
"""

MAC_SCRIPT = r"""#!/bin/sh
PID="$1"; SRC="$2"; DST="$3"
i=0
while kill -0 "$PID" 2>/dev/null && [ $i -lt 600 ]; do sleep 0.2; i=$((i+1)); done
BAK="$DST.old-$(date +%s)"
if mv "$DST" "$BAK"; then
  if mv "$SRC" "$DST"; then
    xattr -dr com.apple.quarantine "$DST" 2>/dev/null
    open "$DST"
    rm -rf "$BAK" "$(dirname "$SRC")"
  else
    mv "$BAK" "$DST"; open "$DST"
  fi
else
  open "$DST"
fi
"""


def staging_dir(root: str) -> str:
    """解压位置放在程序目录旁边（同一个磁盘），替换时只需重命名。"""
    return os.path.join(os.path.dirname(root), f".{APP_NAME.lower()}-update")


def prepare(info: UpdateInfo, progress=None, cancelled=None) -> str:
    """下载、校验、解压，返回准备好的新版本路径。"""
    ok, why = can_self_update()
    if not ok:
        raise UpdateError(why)
    root = install_root()
    tmp = tempfile.mkdtemp(prefix=f"{APP_NAME.lower()}-dl-")
    try:
        zip_path = download(info, tmp, progress, cancelled)
        if progress:
            progress(1.0, "正在解压…")
        new_root = extract(zip_path, staging_dir(root))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if progress:
        progress(1.0, "正在检查数字签名…")
    verify_same_signer(root, new_root)
    return new_root


def launch_installer(new_root: str):
    """启动替换脚本；调用方随后退出程序，脚本等程序退出后替换并重新启动。"""
    root = install_root()
    if root is None:
        raise UpdateError("当前不能自动安装更新")
    pid = os.getpid()
    if sys.platform == "win32":
        script = os.path.join(tempfile.gettempdir(), f"{APP_NAME.lower()}-update-{int(time.time())}.ps1")
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(WIN_SCRIPT)
        exe = os.path.join(root, f"{APP_NAME}.exe")
        flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File",
                          script, "-ProcId", str(pid), "-Src", new_root, "-Dst", root, "-Exe", exe],
                         creationflags=flags, close_fds=True)
    elif sys.platform == "darwin":
        script = os.path.join(tempfile.gettempdir(), f"{APP_NAME.lower()}-update-{int(time.time())}.sh")
        with open(script, "w") as f:
            f.write(MAC_SCRIPT)
        os.chmod(script, 0o755)
        subprocess.Popen(["/bin/sh", script, str(pid), new_root, root], start_new_session=True, close_fds=True)
    else:
        raise UpdateError("当前系统不支持自动安装更新")
