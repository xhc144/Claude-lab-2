"""AI 连接的预设与存储。

每个连接 = 服务地址 + API Key，只填一次；各功能（朗读、文字识别、AI 校对）在设置里选用哪个连接、哪个模型。
除千问语音外，都按 OpenAI 兼容接口（/chat/completions、/models、/audio/speech）调用。
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True)
class Preset:
    key: str
    name: str
    base_url: str
    key_url: str = ""          # 申请 Key 的网页
    env: str = ""              # 没填 Key 时读取的环境变量
    local: bool = False        # 本机运行的服务，不需要 Key
    tts: str = ""              # 支持的语音接口：qwen / openai / 空
    chat: tuple = ()           # 推荐的文字模型（AI 校对用）
    vision: tuple = ()         # 推荐的视觉模型（文字识别用）
    tts_models: tuple = ()
    note: str = ""


PRESETS: dict[str, Preset] = {p.key: p for p in [
    Preset("qwen", "通义千问（阿里云百炼）", "https://dashscope.aliyuncs.com/compatible-mode/v1",
           "https://bailian.console.aliyun.com/", "DASHSCOPE_API_KEY", tts="qwen",
           chat=("qwen-flash", "qwen-plus", "deepseek-v4.1-flash"),
           vision=("qwen3.5-ocr", "qwen-vl-ocr", "qwen3-vl-plus"),
           tts_models=("qwen3-tts-flash",),
           note="一个 Key 同时支持 AI 朗读、文字识别和校对。"),
    Preset("qwen_intl", "通义千问（国际版·新加坡）", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
           "https://modelstudio.console.alibabacloud.com/", "DASHSCOPE_API_KEY", tts="qwen",
           chat=("qwen-flash", "qwen-plus"), vision=("qwen-vl-ocr", "qwen3-vl-plus"),
           tts_models=("qwen3-tts-flash",), note="国际版和国内版的 Key 不通用。"),
    Preset("deepseek", "DeepSeek", "https://api.deepseek.com", "https://platform.deepseek.com/api_keys",
           "DEEPSEEK_API_KEY", chat=("deepseek-flash", "deepseek-v4-pro"),
           note="适合做文字识别结果的 AI 校对。"),
    Preset("kimi", "Kimi（月之暗面）", "https://api.moonshot.cn/v1", "https://platform.moonshot.cn/console/api-keys",
           "MOONSHOT_API_KEY"),
    Preset("zhipu", "智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", "https://open.bigmodel.cn/usercenter/apikeys",
           "ZHIPUAI_API_KEY"),
    Preset("siliconflow", "硅基流动", "https://api.siliconflow.cn/v1", "https://cloud.siliconflow.cn/account/ak",
           "SILICONFLOW_API_KEY", vision=("deepseek-ai/DeepSeek-OCR",)),
    Preset("openai", "OpenAI", "https://api.openai.com/v1", "https://platform.openai.com/api-keys",
           "OPENAI_API_KEY", tts="openai", tts_models=("gpt-4o-mini-tts", "tts-1")),
    Preset("ollama", "Ollama（本地）", "http://localhost:11434/v1", "https://ollama.com/download", local=True,
           chat=("qwen3",), vision=("qwen3-vl", "glm-ocr"),
           note="先安装 Ollama，再下载模型，例如：ollama pull qwen3-vl"),
    Preset("lmstudio", "LM Studio（本地）", "http://localhost:1234/v1", "https://lmstudio.ai/", local=True,
           note="在 LM Studio 里加载模型并启动本地服务（Developer → Start Server）。"),
    Preset("custom", "其他（OpenAI 兼容）", "", tts="openai",
           note="vLLM、llama.cpp、LocalAI、各类中转服务等，只要兼容 OpenAI 接口都可以。"),
]}

# 首次使用时预先建好的连接（id 与预设同名）
DEFAULT_CONNECTIONS = ["qwen", "deepseek", "ollama", "lmstudio"]


def is_local_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".local"):
        return True
    return host.startswith(("192.168.", "10.")) or any(host.startswith(f"172.{n}.") for n in range(16, 32))


@dataclass
class Connection:
    id: str
    name: str
    preset: str
    base_url: str
    api_key: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def p(self) -> Preset:
        return PRESETS.get(self.preset, PRESETS["custom"])

    @property
    def local(self) -> bool:
        return self.p.local or is_local_url(self.base_url)

    @property
    def tts(self) -> str:
        return self.p.tts

    def key(self) -> str:
        k = (self.api_key or "").strip()
        if not k and self.p.env:
            k = os.environ.get(self.p.env, "").strip()
        return k

    def key_from_env(self) -> bool:
        return not (self.api_key or "").strip() and bool(self.key())

    @property
    def ready(self) -> bool:
        return bool(self.base_url.strip()) and (self.local or bool(self.key()))

    def status(self) -> str:
        if not self.base_url.strip():
            return "未填写地址"
        if self.local:
            return "本地服务"
        if not self.key():
            return "未填写 Key"
        return "已配置"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "preset": self.preset, "base_url": self.base_url,
                "api_key": self.api_key, "extra": self.extra}

    @classmethod
    def from_dict(cls, d: dict) -> "Connection":
        return cls(id=str(d.get("id") or new_id()), name=str(d.get("name") or ""), preset=str(d.get("preset") or "custom"),
                   base_url=str(d.get("base_url") or ""), api_key=str(d.get("api_key") or ""),
                   extra=dict(d.get("extra") or {}))

    @classmethod
    def from_preset(cls, key: str, cid: str | None = None) -> "Connection":
        p = PRESETS[key]
        return cls(id=cid or new_id(), name=p.name, preset=key, base_url=p.base_url)


def new_id() -> str:
    return "c" + uuid.uuid4().hex[:8]


def dashscope_host(base_url: str) -> str:
    """千问的 OpenAI 兼容地址 → DashScope 原生接口的域名部分。"""
    u = urlparse(base_url.strip())
    if not u.scheme:
        return ""
    path = u.path.rstrip("/")
    for suffix in ("/compatible-mode/v1", "/compatible-mode"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    else:
        path = ""
    return f"{u.scheme}://{u.netloc}{path}"


class Hub:
    """连接列表的读写。设置键 ai/connections 保存为字典列表。"""

    def __init__(self, settings):
        self.settings = settings

    def connections(self) -> list[Connection]:
        raw = self.settings.get("ai/connections")
        if raw is None:
            conns = self._defaults()
            self.save(conns)
            return conns
        return [Connection.from_dict(d) for d in raw if isinstance(d, dict)]

    def get(self, cid: str | None) -> Connection | None:
        if not cid:
            return None
        return next((c for c in self.connections() if c.id == cid), None)

    def save(self, conns: list[Connection]):
        self.settings.set("ai/connections", [c.to_dict() for c in conns])

    def tts_connections(self) -> list[Connection]:
        return [c for c in self.connections() if c.tts]

    def _defaults(self) -> list[Connection]:
        """第一次使用：建好常用连接；旧版本「朗读」里填过的千问 Key 搬过来。"""
        st = self.settings
        out = [Connection.from_preset(k, k) for k in DEFAULT_CONNECTIONS]
        qwen = out[0]
        qwen.api_key = st.get("tts/api_key") or ""
        region = st.get("tts/region") or "beijing"
        if region == "singapore":
            qwen.base_url = PRESETS["qwen_intl"].base_url
            qwen.name = PRESETS["qwen_intl"].name
            qwen.preset = "qwen_intl"
        elif region == "custom" and (st.get("tts/base_url") or "").strip():
            qwen.base_url = st.get("tts/base_url").strip().rstrip("/") + "/compatible-mode/v1"
        return out
