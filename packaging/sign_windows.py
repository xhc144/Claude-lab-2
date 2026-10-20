"""用 .pfx 证书给 Windows 程序签名（Authenticode + RFC 3161 时间戳）。

    python packaging/sign_windows.py dist/Folio/Folio.exe [更多文件…]

证书来自环境变量（在 GitHub 仓库 Settings → Secrets and variables → Actions 里添加）：
    WINDOWS_CERT_PFX        .pfx 文件的 Base64 内容
    WINDOWS_CERT_PASSWORD   .pfx 的密码
"""
from __future__ import annotations

import base64
import glob
import os
import subprocess
import sys
import tempfile

TIMESTAMP_SERVERS = ["http://timestamp.digicert.com", "http://timestamp.sectigo.com", "http://timestamp.globalsign.com/tsa/r6advanced1"]


def find_signtool() -> str:
    base = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    found = sorted(glob.glob(os.path.join(base, "Windows Kits", "10", "bin", "10.*", "x64", "signtool.exe")))
    if not found:
        sys.exit("找不到 signtool.exe（需要 Windows SDK）")
    return found[-1]


def main(files: list[str]) -> int:
    data = os.environ.get("WINDOWS_CERT_PFX", "").strip()
    if not data:
        print("没有设置 WINDOWS_CERT_PFX，跳过签名")
        return 0
    password = os.environ.get("WINDOWS_CERT_PASSWORD", "")
    signtool = find_signtool()
    fd, pfx = tempfile.mkstemp(suffix=".pfx")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64decode(data))
        for ts in TIMESTAMP_SERVERS:
            cmd = [signtool, "sign", "/fd", "sha256", "/f", pfx, "/p", password, "/tr", ts, "/td", "sha256",
                   "/d", "Folio PDF", *files]
            r = subprocess.run(cmd, capture_output=True, text=True)
            # 输出里不会包含密码；只打印 signtool 自己的结果
            print(r.stdout.strip())
            if r.returncode == 0:
                print("签名完成，时间戳服务器：", ts)
                return 0
            print(r.stderr.strip())
            print("签名失败，换一个时间戳服务器重试…")
        return 1
    finally:
        os.remove(pfx)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
