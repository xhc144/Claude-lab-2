"""借助 LibreOffice 把 Word / Excel / PPT 转成 PDF（未安装时给出提示）。"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import tempfile

OFFICE_EXTS = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".wps", ".et", ".dps"}


class OfficeNotFound(RuntimeError):
    pass


def find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    candidates = []
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            candidates += glob.glob(os.path.join(base, "LibreOffice*", "program", "soffice.exe"))
    elif sys.platform == "darwin":
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def office_to_pdf(path: str, out_dir: str | None = None, timeout: int = 240) -> str:
    soffice = find_soffice()
    if not soffice:
        raise OfficeNotFound("转换 Word/Excel/PPT 需要先安装免费的 LibreOffice（libreoffice.org）。")
    out_dir = out_dir or tempfile.mkdtemp(prefix="folio-office-")
    # 独立的用户配置目录，避免与正在运行的 LibreOffice 冲突
    profile = tempfile.mkdtemp(prefix="folio-lo-profile-")
    profile_url = "file:///" + profile.replace("\\", "/").lstrip("/")
    cmd = [soffice, f"-env:UserInstallation={profile_url}", "--headless", "--norestore",
           "--convert-to", "pdf", "--outdir", out_dir, path]
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False, **kwargs)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError(f"转换失败：{os.path.basename(path)}")
    return pdf
