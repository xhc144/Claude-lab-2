"""千问语音合成（阿里云百炼 DashScope，qwen3-tts-flash 等模型）的 HTTP 客户端。

接口：POST {base}/api/v1/services/aigc/multimodal-generation/generation
返回 output.audio.url（24 小时有效的 wav 文件地址）。单次文本最多 600 字。
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_HOST = "https://dashscope.aliyuncs.com"

MODELS = ["qwen3-tts-flash", "qwen-tts", "qwen-tts-latest"]

LANGUAGES = [("Auto", "自动识别"), ("Chinese", "中文"), ("English", "英文"), ("Japanese", "日语"),
             ("Korean", "韩语"), ("French", "法语"), ("German", "德语"), ("Spanish", "西班牙语"),
             ("Italian", "意大利语"), ("Portuguese", "葡萄牙语"), ("Russian", "俄语")]

# qwen3-tts-flash 系统音色（参数值, 中文名, 描述）
VOICES = [
    ("Cherry", "芊悦", "女 · 阳光亲切"),
    ("Serena", "苏瑶", "女 · 温柔"),
    ("Ethan", "晨煦", "男 · 活力温暖"),
    ("Maia", "四月", "女 · 知性温柔"),
    ("Neil", "阿闻", "男 · 新闻播报"),
    ("Elias", "墨讲师", "女 · 知识讲解"),
    ("Andre", "安德雷", "男 · 磁性沉稳"),
    ("Seren", "小婉", "女 · 舒缓助眠"),
    ("Moon", "月白", "男 · 率性帅气"),
    ("Kai", "凯", "男 · 舒缓 ASMR"),
    ("Chelsie", "千雪", "女 · 二次元"),
    ("Momo", "茉兔", "女 · 俏皮"),
    ("Vivian", "十三", "女 · 酷飒"),
    ("Mia", "乖小妹", "女 · 温顺乖巧"),
    ("Nofish", "不吃鱼", "男 · 不卷舌"),
    ("Jennifer", "詹妮弗", "女 · 美式英语"),
    ("Aiden", "艾登", "男 · 美式英语"),
    ("Ryan", "甜茶", "男 · 戏剧张力"),
    ("Katerina", "卡捷琳娜", "女 · 御姐"),
    ("Eldric Sage", "沧明子", "男 · 沉稳长者"),
    ("Arthur", "徐大爷", "男 · 讲故事"),
    ("Vincent", "田叔", "男 · 烟嗓豪迈"),
    ("Bella", "萌宝", "女 · 童声"),
    ("Dylan", "北京-晓东", "男 · 北京话"),
    ("Jada", "上海-阿珍", "女 · 上海话"),
    ("Sunny", "四川-晴儿", "女 · 四川话"),
    ("Eric", "四川-程川", "男 · 四川话"),
    ("Rocky", "粤语-阿强", "男 · 粤语"),
    ("Kiki", "粤语-阿清", "女 · 粤语"),
    ("Li", "南京-老李", "男 · 南京话"),
    ("Marcus", "陕西-秦川", "男 · 陕西话"),
    ("Roy", "闽南-阿杰", "男 · 闽南语"),
    ("Peter", "天津-李彼得", "男 · 天津话"),
]

MAX_CHARS = 600


class QwenError(RuntimeError):
    pass


def _friendly(code: str, message: str, status: int) -> str:
    code_l = (code or "").lower()
    if status == 401 or "invalidapikey" in code_l or "apikey" in code_l:
        return "千问 API Key 无效，请在「设置 → AI 中台」中检查（注意国内版和国际版的 Key 不通用）。"
    if status == 429 or "throttl" in code_l or "ratelimit" in code_l:
        return "千问语音请求太频繁或额度不足，请稍后再试。"
    if "arrearage" in code_l or "quota" in code_l:
        return "千问账户余额或免费额度不足。"
    if "model" in code_l and "notfound" in code_l.replace("_", ""):
        return f"找不到模型：{message}"
    return f"千问语音合成失败：{message or code or status}"


def pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    """给 16 位单声道 PCM 加上 WAV 头（千问流式输出是 24kHz PCM）。"""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def normalize_wav(data: bytes) -> bytes:
    """千问返回的 WAV 头里长度是占位值（流式写法），按实际长度改正，避免播放器算错时长。"""
    import struct

    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return data
    buf = bytearray(data)
    i = 12
    while i + 8 <= len(buf):
        cid = bytes(buf[i:i + 4])
        size = struct.unpack("<I", buf[i + 4:i + 8])[0]
        if cid == b"data":
            real = len(buf) - (i + 8)
            if size != real:
                buf[i + 4:i + 8] = struct.pack("<I", real)
            break
        i += 8 + size + (size & 1)
    buf[4:8] = struct.pack("<I", len(buf) - 8)
    return bytes(buf)


def synthesize(text: str, *, api_key: str, model: str = "qwen3-tts-flash", voice: str = "Cherry",
               language: str = "Auto", host: str = DEFAULT_HOST, timeout: float = 60, retries: int = 1) -> bytes:
    """合成一段文字，返回 wav 音频字节。host 是 DashScope 域名（国内版 / 国际版）。"""
    if not api_key:
        raise QwenError("还没有设置千问 API Key。请到「设置 → AI 中台」填写，或改用系统语音。")
    text = text[:MAX_CHARS]
    url = (host or DEFAULT_HOST).rstrip("/") + "/api/v1/services/aigc/multimodal-generation/generation"
    payload = {"model": model, "input": {"text": text, "voice": voice}}
    if language and language != "Auto":
        payload["input"]["language_type"] = language
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        try:
            err = json.loads(ex.read().decode("utf-8"))
        except Exception:
            err = {}
        raise QwenError(_friendly(err.get("code", ""), err.get("message", ""), ex.code)) from None
    except (urllib.error.URLError, OSError) as ex:  # 网络错误或超时：重试一次
        if retries > 0:
            return synthesize(text, api_key=api_key, model=model, voice=voice, language=language, host=host,
                              timeout=timeout, retries=retries - 1)
        reason = getattr(ex, "reason", ex)
        if isinstance(ex, TimeoutError) or "timed out" in str(reason):
            raise QwenError("连接千问服务超时，请检查网络") from None
        raise QwenError(f"无法连接千问服务：{reason}") from None

    if body.get("code"):
        raise QwenError(_friendly(body.get("code", ""), body.get("message", ""), 200))
    audio = (body.get("output") or {}).get("audio") or {}
    if audio.get("data"):
        import base64

        raw = base64.b64decode(audio["data"])
        return normalize_wav(raw) if raw[:4] == b"RIFF" else pcm_to_wav(raw)
    audio_url = audio.get("url")
    if not audio_url:
        raise QwenError("千问没有返回音频")
    try:
        with urllib.request.urlopen(audio_url, timeout=timeout) as resp:
            return normalize_wav(resp.read())
    except Exception as ex:  # noqa: BLE001
        raise QwenError(f"下载合成音频失败：{ex}") from None
