# 概率分布图鉴（系列讲解视频）

根据讲义《概率分布图鉴》（[`概率分布图鉴.pdf`](概率分布图鉴.pdf)）做的 8 集系列讲解视频，共约 __TOTAL__ 分钟。
讲义只是大纲，视频把它补成一条完整的线：**从一枚硬币出发**，每个分布都讲清楚它是从什么问题里来的、为什么长这样、公式怎么推出来，前后连成一个流程，而不是逐页念讲义。

- 1080p30，Manim 动画，配色沿用讲义（青绿 = 离散、赭红 = 连续、靛蓝 = 抽样分布与多元正态）。
- 讲解文字是人工撰写的（就写在 [`src/outline.py`](src/outline.py) 里），**没有用文本模型生成**；配音用千问语音合成（`qwen3-tts-flash`，音色 Maia）。
- λ、μ、σ、ρ 等希腊字母原样交给语音合成，它能直接读出来，不做任何替换。
- 字幕已烧录进画面，另附同名 `.srt`。

## 分集

| 集 | 视频 | 时长 | 讲什么 |
|---|---|---|---|
__TABLE__

## 怎么重新生成

用 [Manim Community](https://www.manim.community/)（0.22.1）画动画，ffmpeg 合成。需要 LaTeX（`texlive-latex-extra`、`texlive-fonts-recommended`、`dvisvgm`，公式用 Palatino 字体 `mathpazo`，和讲义一致）、思源黑体（`fonts-noto-cjk`），以及 `libcairo2-dev`、`libpango1.0-dev`。

```bash
cd src
pip install manim requests "pillow<13"
export DASHSCOPE_API_KEY=...          # 千问（阿里云百炼）的 API Key，只用于语音合成

# 1. 口播稿：把 outline.py 里每段“要讲的内容”整理成 narration.json（字幕也用它）
python make_narration.py

# 2. 配音：qwen3-tts-flash 逐段合成，写 audio/ 和 timing.json（换音色：export QWEN_VOICE=Ethan）
python tts.py

# 3. 渲染全部场景（4 个并行；低清预览用 ./render_all.sh -ql E3B）
./render_all.sh "-qh --frame_rate 30"

# 4. 每集合成一个视频：配音、背景音乐、字幕
QUALITY=1080p30 python build.py       # 只合成某几集：QUALITY=1080p30 python build.py 3 5
```

- `outline.py`：8 集的分镜大纲。每个场景分成若干段，每段写明画面和要讲的内容；“要讲的内容”就是口播稿原文，改讲解就改这里。
- `ep1.py` ~ `ep8.py`：每集的场景（`E1A`、`E1B`……），一个场景一个 `Scene`；`props.py` 是硬币、骰子、转盘、路线图等道具。
- `common.py`：配色、字体、版式组件（集标题卡、页眉、数字卡）、坐标轴和常用分布的密度函数；`VScene` 按配音时长推进画面，并把每段配音的实际起点写到 `marks/`，`build.py` 按它放置配音，画面和声音不会错位。
- 背景音乐是 `build.py` 里用正弦波合成的慢速和弦铺底，说话时自动压低。
- `audio/`、`media/`、`marks/`、`build/`、`timing.json` 都是中间产物，不提交。
