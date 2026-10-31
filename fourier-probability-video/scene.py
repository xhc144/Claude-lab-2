"""场景的描述：时长、画面函数、说明文字、音效提示。画面和音轨都从这里取时间，所以不会错位。"""


class Scene:
    def __init__(self, id, dur, draw, caps=(), sfx=(), tone=None, chapter=None, theme=0, hud=1.0,
                 spin=1.0, fade_in=0.4, fade_out=0.5, bloom=1.0, bed=0):
        self.id = id
        self.dur = dur
        self.draw = draw          # draw(canvas, u)，u 是场景内的时间（秒）
        self.caps = list(caps)    # [(开始, 结束, "文字，可以夹 $公式$"), ...]
        self.sfx = list(sfx)      # [(时刻, 种类, {参数}), ...]，见 audio.py
        self.tone = tone          # tone(u 数组) -> (频率, 音量)：把画面里的频率 t 变成听得见的音高
        self.chapter = chapter    # ("01", "中文标题", "ENGLISH TITLE")
        self.theme = theme        # 背景星云的配色
        self.hud = hud
        self.spin = spin
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.bloom = bloom
        self.bed = bed            # 背景铺底用哪一组和弦（audio.CHORDS 的下标）
        self.start = 0.0
