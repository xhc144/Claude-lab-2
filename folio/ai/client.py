"""OpenAI 兼容接口的最小客户端（只用标准库）：列模型、对话、语音合成。

错误统一转成 AIError，消息是给用户看的中文说明。
"""
from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request

from .. import __version__
from .hub import Connection


class AIError(RuntimeError):
    pass


def _opener(conn: Connection):
    if conn.local:  # 本机服务不走系统代理，否则 Windows 上开了代理软件时会连不上 localhost
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def _friendly(conn: Connection, status: int, code: str, message: str, model: str = "") -> str:
    low = f"{code} {message}".lower()
    name = conn.name
    if status in (401, 403) or "invalid_api_key" in low or "invalidapikey" in low or "unauthorized" in low:
        return f"{name} 的 API Key 无效或没有权限，请到「设置 → AI 中台」检查。"
    if status == 402 or "insufficient" in low or "arrearage" in low or "balance" in low:
        return f"{name} 账户余额或额度不足。"
    if status == 429 or "rate limit" in low or "ratelimit" in low or "throttl" in low:
        return f"{name} 请求太频繁或额度用完了，请稍后再试。"
    if model and (status == 404 or "model_not_found" in low or "model not" in low or "does not exist" in low
                  or "not found" in low and "model" in low):
        hint = "（本地服务需要先下载或加载这个模型）" if conn.local else ""
        return f"{name} 上没有模型「{model}」{hint}。"
    if "image" in low and ("support" in low or "invalid" in low or "vision" in low):
        return f"模型「{model}」不支持图片输入，文字识别需要选择视觉模型。"
    return f"{name} 返回错误（{status}）：{message or code or '未知错误'}"


def request(conn: Connection, method: str, path: str, payload: dict | None = None, *, timeout: float = 60,
            model: str = "", raw: bool = False):
    base = conn.base_url.strip().rstrip("/")
    if not base:
        raise AIError(f"「{conn.name}」还没有填写服务地址。")
    if not conn.local and not conn.key():
        raise AIError(f"「{conn.name}」还没有填写 API Key，请到「设置 → AI 中台」填写。")
    headers = {"User-Agent": f"Folio/{__version__}", "Accept": "application/json"}
    if conn.key():
        headers["Authorization"] = f"Bearer {conn.key()}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with _opener(conn).open(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as ex:
        text = ex.read().decode("utf-8", "replace")
        code, message = "", text[:300]
        try:
            err = json.loads(text)
            e = err.get("error", err) if isinstance(err, dict) else {}
            if isinstance(e, dict):
                code, message = str(e.get("code") or e.get("type") or ""), str(e.get("message") or message)
            elif isinstance(e, str):
                message = e
        except Exception:
            pass
        raise AIError(_friendly(conn, ex.code, code, message, model)) from None
    except (urllib.error.URLError, OSError) as ex:
        reason = getattr(ex, "reason", ex)
        if isinstance(ex, (TimeoutError, socket.timeout)) or "timed out" in str(reason):
            raise AIError(f"连接 {conn.name} 超时，请检查网络或稍后再试。") from None
        if conn.local and isinstance(reason, ConnectionRefusedError | ConnectionResetError):
            raise AIError(f"连不上 {conn.name}（{base}），请确认它已经启动。") from None
        raise AIError(f"无法连接 {conn.name}：{reason}") from None
    if raw:
        return body
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        raise AIError(f"{conn.name} 返回的内容无法解析。") from None


def list_models(conn: Connection, timeout: float = 20) -> list[str]:
    r = request(conn, "GET", "/models", timeout=timeout)
    items = r.get("data") if isinstance(r, dict) else r
    if not isinstance(items, list):
        items = r.get("models", []) if isinstance(r, dict) else []
    ids = [str(m.get("id") or m.get("name")) for m in items if isinstance(m, dict) and (m.get("id") or m.get("name"))]
    return sorted(set(ids), key=str.lower)


_THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def chat(conn: Connection, model: str, messages: list[dict], *, timeout: float = 120, temperature: float = 0.0,
         max_tokens: int | None = None) -> str:
    if not model:
        raise AIError("还没有选择模型。")
    body: dict = {"model": model, "messages": messages, "stream": False, "temperature": temperature}
    if max_tokens:
        body["max_tokens"] = max_tokens
    r = request(conn, "POST", "/chat/completions", body, timeout=timeout, model=model)
    try:
        content = r["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError):
        raise AIError(f"{conn.name} 没有返回结果。") from None
    if isinstance(content, list):
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return _THINK_RE.sub("", content or "").strip()


def image_message(prompt: str, image: bytes, mime: str = "image/jpeg") -> dict:
    import base64

    url = f"data:{mime};base64," + base64.b64encode(image).decode("ascii")
    return {"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}},
                                        {"type": "text", "text": prompt}]}


def speech(conn: Connection, model: str, voice: str, text: str, *, timeout: float = 60) -> bytes:
    """OpenAI 兼容的 /audio/speech（OpenAI、本地 Kokoro / LocalAI 等），返回 wav。"""
    body = {"model": model, "input": text, "voice": voice or "alloy", "response_format": "wav"}
    data = request(conn, "POST", "/audio/speech", body, timeout=timeout, model=model, raw=True)
    if not data:
        raise AIError(f"{conn.name} 没有返回音频。")
    return data


def parse_json(text: str):
    """从模型回复里取出 JSON（去掉 ```json 包裹、前后的说明文字）。"""
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    starts = [i for i in (s.find("["), s.find("{")) if i >= 0]
    if not starts:
        raise ValueError("回复中没有 JSON")
    start = min(starts)
    end = max(s.rfind("]"), s.rfind("}"))
    return json.loads(s[start:end + 1])
