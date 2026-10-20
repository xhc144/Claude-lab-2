"""生成自动更新用的 latest.json（发布 v* 标签时由 CI 调用）。

    python packaging/make_manifest.py --version 0.2.0 --base-url https://github.com/<repo>/releases/download/v0.2.0 \
        --asset windows-x64=Folio-windows.zip --asset macos-arm64=Folio-macos.zip --notes docs/CHANGELOG.md > latest.json
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re


def section_for(changelog: str, version: str) -> str:
    """从 CHANGELOG.md 取出「## 0.2.0」那一节。"""
    if not os.path.exists(changelog):
        return ""
    text = open(changelog, encoding="utf-8").read()
    m = re.search(rf"^##\s*v?{re.escape(version)}\b.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--asset", action="append", default=[], help="平台=文件路径")
    ap.add_argument("--notes", default="")
    ap.add_argument("--page", default="")
    a = ap.parse_args()
    version = a.version.lstrip("v")
    assets = {}
    for spec in a.asset:
        key, path = spec.split("=", 1)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        assets[key] = {"url": f"{a.base_url.rstrip('/')}/{os.path.basename(path)}",
                       "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    out = {"version": version, "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "notes": section_for(a.notes, version) if a.notes else "", "page": a.page, "assets": assets}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
