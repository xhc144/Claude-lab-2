"""朗读引擎：千问 AI 语音（联网）和系统语音（离线）。

两者对外接口一致：speak(token, text) 播放一句，prefetch 预先合成后面几句；
开始播放时发 started(token)，播完发 finished(token)。
"""
from __future__ import annotations

import hashlib
import os
import time

from PySide6.QtCore import QLocale, QObject, QRunnable, QThreadPool, QUrl, Signal

from ..config import Settings, cache_dir
from . import qwen

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
except Exception:  # pragma: no cover
    QMediaPlayer = None  # type: ignore

try:
    from PySide6.QtTextToSpeech import QTextToSpeech
except Exception:  # pragma: no cover
    QTextToSpeech = None  # type: ignore

AUDIO_CACHE_LIMIT = 200 * 1024 * 1024


class TtsEngine(QObject):
    started = Signal(int)
    finished = Signal(int)
    failed = Signal(str)
    waiting = Signal(bool)   # 正在等待合成

    name = ""

    def speak(self, token: int, text: str): ...
    def prefetch(self, token: int, text: str): ...
    def stop(self): ...
    def pause(self): ...
    def resume(self): ...
    def set_rate(self, rate: float): ...

    def shutdown(self):
        self.stop()


# ============================================================ 千问
class _Bridge(QObject):
    ready = Signal(int, str, str)  # token, 音频文件路径, 错误信息


class _SynthTask(QRunnable):
    def __init__(self, token: int, text: str, path: str, params: dict, bridge: _Bridge):
        super().__init__()
        self.token, self.text, self.path, self.params, self.bridge = token, text, path, params, bridge

    def run(self):
        try:
            if not os.path.exists(self.path):
                data = qwen.synthesize(self.text, **self.params)
                tmp = self.path + f".{self.token}.part"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, self.path)
            self._emit(self.path, "")
        except Exception as ex:  # noqa: BLE001
            self._emit("", str(ex))

    def _emit(self, path: str, err: str):
        try:
            self.bridge.ready.emit(self.token, path, err)
        except RuntimeError:
            pass  # 引擎已关闭（例如切换了音色或退出程序）


class QwenEngine(TtsEngine):
    name = "千问 AI 语音"

    def __init__(self, settings: Settings):
        super().__init__()
        self.params = dict(api_key=settings.api_key(), model=settings.get("tts/model"),
                           voice=settings.get("tts/voice"), language=settings.get("tts/language"),
                           region=settings.get("tts/region"), custom_url=settings.get("tts/base_url") or "")
        self.rate = float(settings.get("tts/rate") or 1.0)
        self.voice_label = next((f"{n}" for v, n, _ in qwen.VOICES if v == self.params["voice"]), self.params["voice"])
        self._dir = cache_dir("tts")
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(2)
        self._bridge = _Bridge()
        self._bridge.ready.connect(self._on_ready)
        self._files: dict[int, str] = {}
        self._errors: dict[int, str] = {}
        self._requested: set[int] = set()
        self._want: int | None = None
        self._playing: int | None = None
        self._paused = False
        if QMediaPlayer is None:
            raise RuntimeError("当前系统缺少音频播放组件")
        self._out = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._out)
        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.errorOccurred.connect(self._on_error)
        _trim_cache(self._dir)

    def _path_for(self, text: str) -> str:
        p = self.params
        key = hashlib.sha1(f"{p['model']}|{p['voice']}|{p['language']}|{text}".encode("utf-8")).hexdigest()
        return os.path.join(self._dir, key + ".wav")

    def _request(self, token: int, text: str):
        if token in self._requested:
            return
        self._requested.add(token)
        self._pool.start(_SynthTask(token, text, self._path_for(text), self.params, self._bridge))

    def prefetch(self, token: int, text: str):
        self._request(token, text)

    def speak(self, token: int, text: str):
        self._want = token
        self._paused = False
        if token in self._files:
            self._play(token)
        elif token in self._errors:
            self.failed.emit(self._errors[token])
        else:
            self.waiting.emit(True)
            self._request(token, text)

    def _on_ready(self, token: int, path: str, err: str):
        if err:
            self._errors[token] = err
            if token == self._want:
                self.waiting.emit(False)
                self.failed.emit(err)
            return
        self._files[token] = path
        if token == self._want and self._playing != token and not self._paused:
            self._play(token)

    def _play(self, token: int):
        self.waiting.emit(False)
        self._playing = token
        self._player.setSource(QUrl.fromLocalFile(self._files[token]))
        self._player.setPlaybackRate(self.rate)
        self._player.play()
        self.started.emit(token)

    def _on_status(self, status):
        if status == QMediaPlayer.EndOfMedia and self._playing is not None:
            tok = self._playing
            self._playing = None
            self.finished.emit(tok)

    def _on_error(self, *args):
        if self._playing is not None:
            self.failed.emit(f"音频播放失败：{self._player.errorString()}")

    def stop(self):
        self._want = None
        self._playing = None
        self._paused = False
        self._player.stop()
        self.waiting.emit(False)

    def pause(self):
        self._paused = True
        self._player.pause()

    def resume(self):
        self._paused = False
        if self._playing is not None:
            self._player.play()
        elif self._want is not None and self._want in self._files:
            self._play(self._want)

    def set_rate(self, rate: float):
        self.rate = rate
        self._player.setPlaybackRate(rate)

    def shutdown(self):
        self.stop()
        self._pool.clear()


def _trim_cache(folder: str):
    try:
        files = [os.path.join(folder, f) for f in os.listdir(folder)]
        files = [(os.path.getmtime(f), os.path.getsize(f), f) for f in files if os.path.isfile(f)]
        total = sum(s for _, s, _ in files)
        for _, size, f in sorted(files):
            if total <= AUDIO_CACHE_LIMIT:
                break
            os.remove(f)
            total -= size
        # 清理半途中断的临时文件
        for _, _, f in files:
            if f.endswith(".part") and time.time() - os.path.getmtime(f) > 600:
                os.remove(f)
    except Exception:
        pass


# ============================================================ 系统语音
class SystemEngine(TtsEngine):
    name = "系统语音"

    def __init__(self, settings: Settings):
        super().__init__()
        if QTextToSpeech is None:
            raise RuntimeError("当前系统不支持语音合成")
        self._tts = QTextToSpeech(self)
        if self._tts.state() == QTextToSpeech.Error:
            raise RuntimeError(f"系统语音不可用：{self._tts.errorString()}")
        want = settings.get("tts/system_voice") or ""
        voices = self._tts.availableVoices()
        chosen = None
        for v in voices:
            if want and v.name() == want:
                chosen = v
                break
        if chosen is None and not want:
            for loc in [QLocale(QLocale.Chinese, QLocale.China)] + list(self._tts.availableLocales()):
                if loc.language() == QLocale.Chinese:
                    self._tts.setLocale(loc)
                    break
        elif chosen is not None:
            self._tts.setVoice(chosen)
        self.voice_label = self._tts.voice().name() if self._tts.voice() else "默认"
        self.set_rate(float(settings.get("tts/rate") or 1.0))
        self._token: int | None = None
        self._speaking = False
        self._tts.stateChanged.connect(self._on_state)

    @staticmethod
    def voices() -> list[str]:
        if QTextToSpeech is None:
            return []
        try:
            t = QTextToSpeech()
            return [v.name() for v in t.availableVoices()]
        except Exception:
            return []

    def speak(self, token: int, text: str):
        self._token = token
        self._speaking = True
        self._tts.say(text)
        self.started.emit(token)

    def _on_state(self, state):
        if state == QTextToSpeech.Ready and self._speaking and self._token is not None:
            self._speaking = False
            self.finished.emit(self._token)
        elif state == QTextToSpeech.Error:
            self.failed.emit(f"系统语音出错：{self._tts.errorString()}")

    def stop(self):
        self._speaking = False
        self._token = None
        self._tts.stop()

    def pause(self):
        self._tts.pause()

    def resume(self):
        self._tts.resume()

    def set_rate(self, rate: float):
        # QTextToSpeech 的语速范围是 -1..1，0 为正常
        self._tts.setRate(max(-1.0, min(1.0, (rate - 1.0) if rate >= 1 else (rate - 1.0) * 2)))


def make_engine(settings: Settings) -> TtsEngine:
    if settings.get("tts/engine") == "system":
        return SystemEngine(settings)
    return QwenEngine(settings)

