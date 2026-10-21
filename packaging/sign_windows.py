"""用 .pfx 证书给 Windows 程序签名（Authenticode + RFC 3161 时间戳）。

    python packaging/sign_windows.py dist/Folio/Folio.exe [更多文件…]
    python packaging/sign_windows.py --subject      只输出证书的 Subject（Windows 的写法，例如 CN=xhc144），
                                                    右键菜单稀疏包清单里的 Publisher 必须和它完全一致

证书来自环境变量（在 GitHub 仓库 Settings → Secrets and variables → Actions 里添加）：
    WINDOWS_CERT_PFX        .pfx 文件的 Base64 内容（仓库密钥 WINDOWS_CERT_PFX_BASE64）
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


def decode_pfx(text: str) -> bytes:
    """Base64 → .pfx；兼容 certutil -encode 生成的带 -----BEGIN/END----- 行的格式。"""
    body = "".join(ln for ln in text.splitlines() if not ln.strip().startswith("-----"))
    return base64.b64decode("".join(body.split()))


def diagnose(pfx: bytes, passwords: list[str]) -> tuple[str | None, str]:
    """用 cryptography 打开 .pfx：返回能打开它的密码，以及说明（不含密码和证书内容）。"""
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
    except ImportError:
        return passwords[0], ""
    for pw in passwords:
        try:
            key, cert, _ = pkcs12.load_key_and_certificates(pfx, pw.encode() if pw else None)
        except ValueError:
            continue
        if cert is None or key is None:
            return None, ".pfx 里没有证书或私钥（导出时要勾选「导出私钥」）"
        info = f"证书：{cert.subject.rfc4514_string()}，有效期至 {cert.not_valid_after_utc:%Y-%m-%d}"
        return pw, info
    return None, (f".pfx 文件 {len(pfx)} 字节，用 WINDOWS_CERT_PASSWORD 打不开："
                  "密码不对，或者 WINDOWS_CERT_PFX_BASE64 不是这个 .pfx 文件的完整 Base64")


# Windows（X509Certificate2.Subject、MSIX 清单的 Publisher）用的属性名
_SUBJECT_NAMES = {"2.5.4.3": "CN", "2.5.4.10": "O", "2.5.4.11": "OU", "2.5.4.7": "L", "2.5.4.8": "S", "2.5.4.6": "C",
                  "2.5.4.9": "STREET", "2.5.4.5": "SERIALNUMBER", "1.2.840.113549.1.9.1": "E"}


def windows_subject(cert) -> str:
    """证书 Subject 的 Windows 写法：从最具体的一项开始，用「, 」分隔，含特殊字符的值加双引号。"""
    parts = []
    for rdn in reversed(cert.subject.rdns):
        for attr in rdn:
            value = str(attr.value)
            if any(ch in value for ch in ',+="\n<>#;') or value != value.strip():
                value = '"' + value.replace('"', '""') + '"'
            parts.append(f"{_SUBJECT_NAMES.get(attr.oid.dotted_string, 'OID.' + attr.oid.dotted_string)}={value}")
    return ", ".join(parts)


def print_subject(pfx_bytes: bytes, candidates: list[str]) -> int:
    from cryptography.hazmat.primitives.serialization import pkcs12

    for pw in candidates:
        try:
            _, cert, _ = pkcs12.load_key_and_certificates(pfx_bytes, pw.encode() if pw else None)
        except ValueError:
            continue
        if cert is not None:
            print(windows_subject(cert))
            return 0
    print("用 WINDOWS_CERT_PASSWORD 打不开 .pfx", file=sys.stderr)
    return 1


def main(files: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台默认编码无法输出中文
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    data = os.environ.get("WINDOWS_CERT_PFX", "").strip()
    if files == ["--subject"]:
        if not data:
            print("没有设置 WINDOWS_CERT_PFX", file=sys.stderr)
            return 1
        raw = os.environ.get("WINDOWS_CERT_PASSWORD", "")
        return print_subject(decode_pfx(data), list(dict.fromkeys([raw, raw.strip(), raw.strip("\r\n")])))
    if not data:
        print("没有设置 WINDOWS_CERT_PFX，跳过签名")
        return 0
    try:
        pfx_bytes = decode_pfx(data)
    except ValueError:
        print("WINDOWS_CERT_PFX_BASE64 不是有效的 Base64")
        return 1
    raw = os.environ.get("WINDOWS_CERT_PASSWORD", "")
    # 粘贴密码时容易多带空格或换行
    candidates = list(dict.fromkeys([raw, raw.strip(), raw.strip("\r\n")]))
    password, info = diagnose(pfx_bytes, candidates)
    print(info)
    if password is None:
        return 1
    if password != raw:
        print("注意：密码首尾有多余的空格或换行，已自动去掉")
    signtool = find_signtool()
    fd, pfx = tempfile.mkstemp(suffix=".pfx")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(pfx_bytes)
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
            if "password" in r.stderr.lower():
                return 1
            print("签名失败，换一个时间戳服务器重试…")
        return 1
    finally:
        os.remove(pfx)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
