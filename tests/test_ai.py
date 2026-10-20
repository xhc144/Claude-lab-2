"""AI 中台：连接预设与迁移、OpenAI 兼容客户端、AI 识别结果解析、AI 校对。"""
import json

import numpy as np
import pytest

from folio.ai import client
from folio.ai.client import AIError
from folio.ai.hub import PRESETS, Connection, Hub, dashscope_host, is_local_url
from folio.ocr import ai as ocr_ai
from folio.ocr.system import OcrImage

from .fakeserver import FakeServer


class MemSettings:
    def __init__(self, **kw):
        self.d = dict(kw)

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


@pytest.fixture
def server():
    s = FakeServer()
    yield s
    s.close()


def local_conn(server, key="") -> Connection:
    return Connection("t", "测试服务", "custom", server.url + "/v1", key)


def blank_image(w=1000, h=1400) -> OcrImage:
    g = np.full((h, w), 255, dtype=np.uint8)
    for y in (100, 200, 300):          # 三行"文字"
        g[y:y + 20, 80:700] = 0
    return OcrImage(w, h, g.tobytes(), b"png", b"jpeg")


# ---------------------------------------------------------------- 连接
def test_default_connections_and_migration():
    st = MemSettings(**{"tts/api_key": "sk-old", "tts/region": "singapore"})
    conns = Hub(st).connections()
    ids = [c.id for c in conns]
    assert ids[:2] == ["qwen", "deepseek"] and "ollama" in ids and "lmstudio" in ids
    qwen = conns[0]
    assert qwen.api_key == "sk-old" and qwen.preset == "qwen_intl" and "intl" in qwen.base_url
    assert st.get("ai/connections")  # 已保存
    assert Hub(st).get("ollama").local and Hub(st).get("ollama").ready


def test_env_key_fallback(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env")
    c = Connection.from_preset("deepseek", "d")
    assert c.key() == "sk-env" and c.key_from_env() and c.ready
    c.api_key = "sk-own"
    assert c.key() == "sk-own" and not c.key_from_env()


def test_helpers():
    assert dashscope_host("https://dashscope.aliyuncs.com/compatible-mode/v1") == "https://dashscope.aliyuncs.com"
    assert dashscope_host("https://dashscope-intl.aliyuncs.com/compatible-mode/v1/") == "https://dashscope-intl.aliyuncs.com"
    assert is_local_url("http://localhost:11434/v1") and is_local_url("http://192.168.1.5:1234/v1")
    assert not is_local_url("https://api.deepseek.com")
    assert all(p.base_url.startswith(("https://", "http://localhost")) for k, p in PRESETS.items() if k != "custom")


def test_parse_json_variants():
    assert client.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert client.parse_json('结果如下：[1, 2]。') == [1, 2]
    with pytest.raises(ValueError):
        client.parse_json("没有 json")


# ---------------------------------------------------------------- 客户端
def test_client_models_chat_speech(server):
    server.json("GET", "/v1/models", {"data": [{"id": "b-model"}, {"id": "a-model"}]})
    server.json("POST", "/v1/chat/completions",
                {"choices": [{"message": {"content": "<think>想一想</think>你好"}}]})
    server.routes[("POST", "/v1/audio/speech")] = lambda body: (200, b"RIFF....WAVE", "audio/wav")
    conn = local_conn(server)
    assert client.list_models(conn) == ["a-model", "b-model"]
    assert client.chat(conn, "a-model", [{"role": "user", "content": "hi"}]) == "你好"
    assert client.speech(conn, "tts-1", "alloy", "你好") == b"RIFF....WAVE"
    method, path, headers, body = server.requests[-1]
    assert body["response_format"] == "wav" and body["voice"] == "alloy"
    assert "Authorization" not in headers  # 本地服务没填 Key 时不发送


def test_client_errors(server):
    server.json("POST", "/v1/chat/completions", {"error": {"message": "Incorrect API key", "code": "invalid_api_key"}},
                status=401)
    conn = local_conn(server, key="sk-bad")
    with pytest.raises(AIError, match="API Key 无效"):
        client.chat(conn, "m", [{"role": "user", "content": "hi"}])
    server.json("POST", "/v1/chat/completions", {"error": {"message": "model 'x' not found"}}, status=404)
    with pytest.raises(AIError, match="没有模型「x」"):
        client.chat(conn, "x", [{"role": "user", "content": "hi"}])
    cloud = Connection.from_preset("deepseek", "d")
    cloud.api_key = ""
    with pytest.raises(AIError, match="还没有填写 API Key"):
        client.chat(cloud, "deepseek-flash", [])


def test_client_local_service_down():
    conn = Connection("o", "Ollama（本地）", "ollama", "http://127.0.0.1:9/v1")
    with pytest.raises(AIError, match="连不上|无法连接"):
        client.list_models(conn)


# ---------------------------------------------------------------- AI 识别结果解析
def test_parse_reply_relative_boxes():
    img = blank_image()
    reply = '```json\n{"lines":[{"text":"第一行","box":[80,70,700,85]},{"text":"Second","box":[80,140,600,155]}]}\n```'
    lines = ocr_ai.parse_reply(reply, img)
    assert [ln.text for ln in lines] == ["第一行", "Second"]
    assert lines[0].box == pytest.approx((0.08, 0.07, 0.7, 0.085))


def test_parse_reply_qwen_rotate_rect_and_pixels():
    img = blank_image()
    # 千问 OCR 的 rotate_rect：[中心x, 中心y, 宽, 高, 角度]，角度 90 时宽高互换
    reply = json.dumps([{"rotate_rect": [400, 100, 20, 600, 90], "text": "旋转框"}])
    (ln,) = ocr_ai.parse_reply(reply, img)
    assert ln.box == pytest.approx((0.1, 0.09, 0.7, 0.11))
    # 坐标超过 1000：按像素理解
    reply = json.dumps({"lines": [{"text": "像素", "bbox": [80, 1200, 700, 1220]}]})
    (ln,) = ocr_ai.parse_reply(reply, img)
    assert ln.box == pytest.approx((0.08, 1200 / 1400, 0.7, 1220 / 1400))


def test_parse_reply_plain_text_uses_detected_lines():
    img = blank_image()
    lines = ocr_ai.parse_reply("第一行\n第二行\n第三行", img)
    assert [ln.text for ln in lines] == ["第一行", "第二行", "第三行"]
    tops = [round(ln.box[1] * img.height) for ln in lines]
    assert tops == [100, 200, 300]


def test_ai_recognize_and_proofread(server):
    def chat(body):
        content = body["messages"][-1]["content"]
        if isinstance(content, list):  # 识别请求带图片
            assert content[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")
            reply = '{"lines":[{"text":"识別结果","box":[80,70,700,85]}]}'
        else:
            items = json.loads(content)
            reply = json.dumps([t.replace("別", "别") for t in items], ensure_ascii=False)
        return 200, {"choices": [{"message": {"content": reply}}]}, "application/json"
    server.routes[("POST", "/v1/chat/completions")] = chat
    conn = local_conn(server)
    lines = ocr_ai.recognize(conn, "vision-model", blank_image())
    assert [ln.text for ln in lines] == ["识別结果"]
    assert ocr_ai.proofread(conn, "text-model", ["识別结果"]) == ["识别结果"]


def test_proofread_rejects_bad_replies(server):
    replies = iter(['["只有一行"]', '["完全不同的另一段话，和原文没有关系", "第二行"]'])
    server.routes[("POST", "/v1/chat/completions")] = lambda body: (
        200, {"choices": [{"message": {"content": next(replies)}}]}, "application/json")
    conn = local_conn(server)
    orig = ["第一行文字", "第二行"]
    assert ocr_ai.proofread(conn, "m", orig) == orig            # 行数不对：整段保持原样
    assert ocr_ai.proofread(conn, "m", orig) == orig            # 改动太大的行保持原样


def test_dashscope_ocr_native_path(server, monkeypatch):
    """千问 OCR 模型走原生接口，用 words_info 里的像素坐标。"""
    payload = {"output": {"choices": [{"message": {"content": [{"ocr_result": {"words_info": [
        {"location": [80, 100, 700, 100, 700, 120, 80, 120], "text": "原生接口"}]}}]}}]}}
    server.json("POST", "/api/v1/services/aigc/multimodal-generation/generation", payload)
    conn = Connection("q", "千问", "qwen", server.url + "/compatible-mode/v1", "sk-test")
    (ln,) = ocr_ai.recognize(conn, "qwen3.5-ocr", blank_image())
    assert ln.text == "原生接口" and ln.box == pytest.approx((0.08, 100 / 1400, 0.7, 120 / 1400))
    body = server.requests[-1][3]
    assert body["parameters"]["ocr_options"]["task"] == "advanced_recognition"


# ---------------------------------------------------------------- 设置界面与功能选用
def test_settings_dialog_roundtrip(qapp):
    from folio.config import Settings
    from folio.ocr.runner import resolve_plan
    from folio.ui.dialogs.settings_dialog import SettingsDialog

    st = Settings()
    st.set("ai/connections", None)
    d = SettingsDialog(None, st, "ai")
    hub = d.hub_page
    hub._add("ollama")
    new = hub.conns[-1]
    assert new.name == "Ollama（本地） 2" and new.base_url.startswith("http://localhost:11434")
    # 文字识别页立刻能选到新连接，并带出推荐的视觉模型
    k = d.ocr_page.source.findData(new.id)
    assert k > 0
    d.ocr_page.source.setCurrentIndex(k)
    assert d.ocr_page.model.currentText() == "qwen3-vl"
    d.ocr_page.model.setCurrentText("glm-ocr")
    d.ocr_page.fix_on.setChecked(True)
    d.ocr_page.fix_conn.setCurrentIndex(d.ocr_page.fix_conn.findData("deepseek"))
    assert d.ocr_page.fix_model.currentText() == "deepseek-flash"
    # 朗读页只列出支持语音的连接
    sources = [d.tts_page.source.itemData(i) for i in range(d.tts_page.source.count())]
    assert sources == ["qwen", "system"]
    d._save()
    assert st.get("ocr/engine") == new.id and st.get("ocr/model") == "glm-ocr"
    assert st.get("ocr/fix") == "deepseek" and st.get("ocr/fix_model") == "deepseek-flash"
    plan = resolve_plan(st)
    assert plan.conn.id == new.id and plan.model == "glm-ocr" and plan.fix_conn.id == "deepseek"
    assert Hub(st).get(new.id) is not None


def test_tts_engine_from_hub(qapp, monkeypatch):
    from folio.config import Settings
    from folio.tts import engines, qwen

    st = Settings()
    st.set("ai/connections", [Connection("qwen", "千问", "qwen", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                                         "sk-intl").to_dict(),
                              Connection("kokoro", "本地语音", "custom", "http://localhost:8880/v1").to_dict()])
    st.set("tts/engine", "qwen")
    st.set("tts/voice", "Cherry")
    calls = []
    monkeypatch.setattr(qwen, "synthesize", lambda text, **kw: calls.append(kw) or b"RIFF")
    try:
        eng = engines.make_engine(st)
    except RuntimeError as ex:
        pytest.skip(str(ex))
    assert eng.name == "千问 AI 语音" and eng.voice_label == "芊悦"
    eng.synth("你好")
    assert calls[0]["host"] == "https://dashscope-intl.aliyuncs.com" and calls[0]["api_key"] == "sk-intl"
    eng.shutdown()
    st.set("tts/engine", "kokoro")
    st.set("tts/oa_voice", "zf_xiaobei")
    eng = engines.make_engine(st)
    assert eng.name == "本地语音" and eng.voice_label == "zf_xiaobei"
    assert engines.describe(st) == "本地语音 · zf_xiaobei"
    eng.shutdown()
    st.set("tts/engine", "deleted-connection")  # 选的连接被删了：退回第一个支持语音的连接
    assert engines.tts_connection(st).id == "qwen"
