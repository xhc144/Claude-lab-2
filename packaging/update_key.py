"""自动更新清单的签名密钥（Ed25519）。

发布时 CI 用仓库密钥 UPDATE_SIGNING_KEY 给 latest.json 签名，打包时把对应的公钥写进程序；
程序只接受用这把密钥签过名的更新清单，即使发布页或下载链接被人篡改也装不上假的更新。

    python packaging/update_key.py gen               生成新密钥：私钥存进仓库密钥 UPDATE_SIGNING_KEY
    python packaging/update_key.py check             检查环境变量 UPDATE_SIGNING_KEY 的格式（不显示内容）
    python packaging/update_key.py pubkey            输出公钥（可以公开）
    python packaging/update_key.py sign latest.json  给清单签名（直接改写文件）

UPDATE_SIGNING_KEY 支持：PEM 格式的 Ed25519 私钥（也可以整段再 base64 一次），
或者 32 字节私钥种子 / 64 字节 NaCl 格式私钥的 base64 或十六进制。
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ENV = "UPDATE_SIGNING_KEY"


class KeyFormatError(ValueError):
    pass


def _raw_bytes(text: str) -> bytes | None:
    t = "".join(text.split())
    if len(t) in (64, 128):
        try:
            return bytes.fromhex(t)
        except ValueError:
            pass
    try:
        return base64.b64decode(t + "=" * (-len(t) % 4), validate=True)
    except (binascii.Error, ValueError):
        try:
            return base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))
        except (binascii.Error, ValueError):
            return None


def _from_pem(data: bytes) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except TypeError:
        raise KeyFormatError("PEM 私钥带有密码，请导出不带密码的私钥") from None
    except ValueError as ex:
        raise KeyFormatError(f"PEM 私钥无法读取：{ex}") from None
    if not isinstance(key, Ed25519PrivateKey):
        raise KeyFormatError(f"PEM 私钥类型是 {type(key).__name__.replace('_', '')}，需要 Ed25519")
    return key


def load_private(text: str) -> Ed25519PrivateKey:
    """按上面列出的几种格式读取私钥；格式不对时抛出 KeyFormatError（说明里不含密钥内容）。"""
    text = (text or "").strip()
    if not text:
        raise KeyFormatError("没有设置")
    if "untrusted comment:" in text:
        raise KeyFormatError("这是 minisign / Tauri 格式的密钥，请用 `python packaging/update_key.py gen` 生成新的")
    if "-----BEGIN" in text:
        return _from_pem(text.encode())
    raw = _raw_bytes(text)
    if raw is None:
        raise KeyFormatError(f"既不是 PEM，也不是 base64 或十六进制（长度 {len(text)}）")
    if raw.startswith(b"-----BEGIN"):
        return _from_pem(raw)
    if b"untrusted comment:" in raw:
        raise KeyFormatError("这是 minisign / Tauri 格式的密钥，请用 `python packaging/update_key.py gen` 生成新的")
    if len(raw) in (32, 64):  # 64 字节：NaCl / libsodium 格式（种子 + 公钥）
        return Ed25519PrivateKey.from_private_bytes(raw[:32])
    if raw[:1] == b"\x30":  # DER
        try:
            key = serialization.load_der_private_key(raw, password=None)
        except (TypeError, ValueError):
            key = None
        if isinstance(key, Ed25519PrivateKey):
            return key
    raise KeyFormatError(f"解码后是 {len(raw)} 字节，不是 Ed25519 私钥（应为 32 或 64 字节）")


def public_b64(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def canonical(manifest: dict) -> bytes:
    """签名覆盖的内容：去掉 signature 字段后按固定格式序列化（程序里 folio/update.py 用同样的方法验证）。"""
    body = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest(manifest: dict, key: Ed25519PrivateKey) -> dict:
    out = dict(manifest)
    out["signature"] = {"alg": "ed25519", "key": public_b64(key),
                        "sig": base64.b64encode(key.sign(canonical(manifest))).decode()}
    return out


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cmd = argv[0] if argv else ""
    if cmd == "gen":
        key = Ed25519PrivateKey.generate()
        seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                 serialization.NoEncryption())
        print("私钥（存进仓库 Settings → Secrets → Actions，名字 UPDATE_SIGNING_KEY；不要发给别人）：")
        print(base64.b64encode(seed).decode())
        print("公钥（可以公开）：")
        print(public_b64(key))
        return 0
    try:
        key = load_private(os.environ.get(ENV, ""))
    except KeyFormatError as ex:
        print(f"{ENV}：{ex}", file=sys.stderr)
        return 2
    if cmd == "check":
        print(f"{ENV}：格式正确（Ed25519），公钥 {public_b64(key)}")
    elif cmd == "pubkey":
        print(public_b64(key))
    elif cmd == "sign" and len(argv) == 2:
        with open(argv[1], encoding="utf-8") as f:
            manifest = json.load(f)
        with open(argv[1], "w", encoding="utf-8") as f:
            json.dump(sign_manifest(manifest, key), f, ensure_ascii=False, indent=2)
        print(f"{argv[1]}：已签名")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
