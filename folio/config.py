"""用户设置：基于 QSettings，统一以 JSON 存储，避免不同平台的类型差异。"""
from __future__ import annotations

import hashlib
import json
import os
import time

from PySide6.QtCore import QSettings, QStandardPaths

from . import APP_NAME

DEFAULTS: dict = {
    "ui/theme": "system",          # system / light / dark
    "ui/sidebar": True,
    "ui/sidebar_width": 230,
    "view/tone": "normal",         # normal / sepia / night
    "view/layout": "single",       # single / double
    "view/restore_position": True,
    "pen/color": "#E5484D",
    "pen/width": 2.0,
    "highlight/color": "#FFD43B",
    "highlight/kind": "highlight",  # highlight / underline / strikeout / squiggly
    "shape/kind": "rect",           # rect / ellipse / line / arrow
    "shape/color": "#E5484D",
    "shape/width": 2.0,
    "text/color": "#E5484D",
    "text/size": 14,
    "note/color": "#F5A524",
    "eraser/size": 12,
    "sign/path": "",
    "sign/width": 140,
    "laser/color": "#FF3B30",
    "tts/engine": "qwen",           # qwen / system
    "tts/api_key": "",
    "tts/region": "beijing",        # beijing / singapore / custom
    "tts/base_url": "",
    "tts/model": "qwen3-tts-flash",
    "tts/voice": "Cherry",
    "tts/language": "Auto",
    "tts/rate": 1.0,
    "tts/skip_margins": True,
    "tts/system_voice": "",
    "print/annots": True,
    "print/gray": False,
    "print/nup": 1,
    "print/scale": "fit",
    "recent": [],
}

MAX_RECENT = 20


class Settings:
    def __init__(self):
        self._qs = QSettings(QSettings.IniFormat, QSettings.UserScope, APP_NAME, APP_NAME)

    def get(self, key: str, default=None):
        fallback = DEFAULTS.get(key) if default is None else default
        raw = self._qs.value(key)
        if raw is None:
            return fallback
        try:
            return json.loads(raw)
        except Exception:
            return fallback

    def set(self, key: str, value) -> None:
        self._qs.setValue(key, json.dumps(value, ensure_ascii=False))

    def sync(self):
        self._qs.sync()

    # ---------- 千问 Key ----------
    def api_key(self) -> str:
        return (self.get("tts/api_key") or os.environ.get("DASHSCOPE_API_KEY", "")).strip()

    # ---------- 最近文件 ----------
    def recent(self) -> list[dict]:
        items = self.get("recent") or []
        return [r for r in items if isinstance(r, dict) and r.get("path")]

    def add_recent(self, path: str, title: str = "", pages: int = 0):
        path = os.path.abspath(path)
        items = [r for r in self.recent() if os.path.normcase(r["path"]) != os.path.normcase(path)]
        items.insert(0, {"path": path, "title": title, "pages": pages, "time": time.time()})
        self.set("recent", items[:MAX_RECENT])

    def remove_recent(self, path: str):
        self.set("recent", [r for r in self.recent() if r["path"] != path])

    def clear_recent(self):
        self.set("recent", [])

    # ---------- 阅读位置 ----------
    @staticmethod
    def _key(path: str) -> str:
        return "positions/" + hashlib.sha1(os.path.normcase(os.path.abspath(path)).encode()).hexdigest()[:16]

    def position(self, path: str) -> dict | None:
        return self.get(self._key(path), {}) or None

    def set_position(self, path: str, pos: dict):
        self.set(self._key(path), pos)


def data_dir() -> str:
    d = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) or os.path.expanduser(f"~/.{APP_NAME.lower()}")
    os.makedirs(d, exist_ok=True)
    return d


def cache_dir(sub: str) -> str:
    d = os.path.join(data_dir(), sub)
    os.makedirs(d, exist_ok=True)
    return d
