"""构建 Windows 11 资源管理器右键菜单（第一层新菜单）：C++ 扩展 DLL 和稀疏包 Folio-Shell.msix。

    python packaging/build_shell.py --publisher "CN=xhc144" [--test]

先运行 packaging/build.py（--test 要用 dist/Folio/Folio.exe）。需要 Visual Studio（C++）、CMake 和 Windows SDK。
输出到 dist/Folio-shell，安装程序把它装到 %LOCALAPPDATA%\\Programs\\Folio-shell：
    FolioShell.exe             稀疏包清单要求有一个程序，实际不会用到
    <版本>/FolioShellExt.dll    右键菜单（IExplorerCommand）。放在带版本号的子目录里：升级时旧 DLL 可能还被
                               Explorer（dllhost）加载着，删不掉也覆盖不了
    Folio-Shell.msix           稀疏包（只有清单和图标），外部位置就是 Folio-shell 这个目录
    register.ps1               安装 / 卸载时注册、移除稀疏包，失败时保留旧的注册表菜单
之后用 sign_windows.py 给 exe、dll、msix 签名；msix 的 Publisher 必须和签名证书的 Subject 完全一致，
所以 --publisher 要填证书的 Subject（sign_windows.py --subject 可以读出来）。

环境变量 FOLIO_VERSION：版本号（CI 发布时取自标签），没有时用 folio/__init__.py 里的。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "shellext")
BUILD = os.path.join(SRC, "build")
OUT = os.path.join(ROOT, "dist", "Folio-shell")
SPARSE = os.path.join(ROOT, "packaging", "sparse")


def app_version() -> str:
    v = os.environ.get("FOLIO_VERSION", "").strip().lstrip("v")
    if v:
        return v
    with open(os.path.join(ROOT, "folio", "__init__.py"), encoding="utf-8") as f:
        return re.search(r'__version__ = "([^"]+)"', f.read()).group(1)


def package_version(v: str) -> str:
    """MSIX 的版本号必须是四段数字：0.2.3 → 0.2.3.0，0.2.3.dev15 → 0.2.3.15。

    开发版的第四段可能比正式版大，所以安装时总是先移除旧包再注册（register.ps1），不依赖版本比较。
    """
    m = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[.\-_]?(?:dev|alpha|beta|rc|a|b)\.?(\d+))?", v)
    if not m:
        sys.exit(f"版本号格式不对：{v}")
    parts = [int(x or 0) for x in m.groups()]
    if any(x > 65535 for x in parts):
        sys.exit(f"版本号的每一段不能超过 65535：{v}")
    return ".".join(str(x) for x in parts)


def sdk_tool(name: str) -> str:
    base = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    found = sorted(glob.glob(os.path.join(base, "Windows Kits", "10", "bin", "10.*", "x64", name)))
    if not found:
        sys.exit(f"找不到 {name}（需要 Windows SDK）")
    return found[-1]


def build_native():
    cmake = shutil.which("cmake") or sys.exit("找不到 cmake")
    subprocess.check_call([cmake, "-S", SRC, "-B", BUILD, "-A", "x64"])
    subprocess.check_call([cmake, "--build", BUILD, "--config", "Release"])


def built(name: str) -> str:
    for cand in (os.path.join(BUILD, "Release", name), os.path.join(BUILD, name)):
        if os.path.isfile(cand):
            return cand
    sys.exit(f"没有找到编译结果 {name}")


def make_manifest(stage: str, version: str, publisher: str):
    with open(os.path.join(SPARSE, "AppxManifest.xml"), encoding="utf-8") as f:
        text = f.read()
    text = (text.replace("@VERSION@", package_version(version)).replace("@DLLDIR@", version)
            .replace("@PUBLISHER@", publisher.replace("&", "&amp;").replace('"', "&quot;")))
    with open(os.path.join(stage, "AppxManifest.xml"), "w", encoding="utf-8") as f:
        f.write(text)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build import render_logo

    assets = os.path.join(stage, "Assets")
    os.makedirs(assets, exist_ok=True)
    for name, size in (("StoreLogo.png", 50), ("Square44x44Logo.png", 44), ("Square150x150Logo.png", 150)):
        render_logo(os.path.join(assets, name), size)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台默认编码无法输出中文
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--publisher", required=True, help="签名证书的 Subject，例如 CN=xhc144")
    ap.add_argument("--test", action="store_true", help="构建后直接加载 DLL 自检（需要 dist/Folio/Folio.exe）")
    args = ap.parse_args(argv)
    version = app_version()
    print("version:", version, "| msix version:", package_version(version), "| publisher:", args.publisher)

    build_native()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, version))
    shutil.copy2(built("FolioShell.exe"), OUT)
    shutil.copy2(built("FolioShellExt.dll"), os.path.join(OUT, version))
    shutil.copy2(os.path.join(SPARSE, "register.ps1"), OUT)

    stage = os.path.join(BUILD, "sparse")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    make_manifest(stage, version, args.publisher)
    # /nv：不做内容校验。稀疏包里没有清单引用的 exe 和 dll，它们在外部位置
    subprocess.check_call([sdk_tool("makeappx.exe"), "pack", "/o", "/nv", "/d", stage,
                           "/p", os.path.join(OUT, "Folio-Shell.msix")])

    if args.test:
        r = subprocess.run([built("FolioShellTest.exe"), os.path.join(OUT, version, "FolioShellExt.dll"),
                            os.path.join(BUILD, "selftest")])
        if r.returncode:
            return r.returncode
    print("done:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
