# 概率分布图鉴（讲解视频）

根据讲义《概率分布图鉴》（[`概率分布图鉴.pdf`](概率分布图鉴.pdf)）做的讲解视频：1080p60，约 12 分半钟，Manim 动画，配色沿用讲义（青绿 = 离散、赭红 = 连续、靛蓝 = 抽样分布与多元正态）。
口播稿由千问（`qwen3.8-max`）按分镜要点撰写、人工审校，配音用千问语音合成（`qwen3-tts-flash`，音色 Maia），带中文字幕。

- 视频：[`probability-distributions-1080p.mp4`](probability-distributions-1080p.mp4)（字幕已烧录；另附 [`probability-distributions-1080p.srt`](probability-distributions-1080p.srt)）
- 源码：[`src/`](src/)

## 内容

| 段落 | 讲义章节 | 画面 |
|---|---|---|
| 片头 | 封面、目录 | 仿讲义封面：竖线和三条密度曲线依次长出，三类颜色标签，七章目录 |
| 01 | 分布函数、质量函数与密度 | 混合型分布函数的跳点与点概率；逆变换抽样——均匀随机数沿曲线落下，堆成直方图；矩母函数与特征函数 |
| 02 | 离散分布 | 二项分布随 p 变化、方差上界、正态近似；几何分布的无记忆性（截掉前三根再放大，与原图重合）；负二项；超几何与有限总体修正 |
| 02 | 泊松分布 | λ 变化；二项逼近泊松；泊松过程的计数路径与指数间隔；区间计数；可加性与稀疏化 |
| 03 | 连续分布 | 均匀；指数分布及无记忆性的几何含义；伽马随 α 变形；正态的 68–95–99.7 和平移伸缩 |
| 03 | 连续分布（续） | 对数正态的众数、中位数、均值；贝塔的形状变化与共轭更新（逐次观测）；韦布尔的风险率；柯西的厚尾与不收敛的样本均值 |
| 04 | 抽样分布 | 卡方随自由度变化；样本方差；t 分布逼近正态；F 分布与 t² = F(1,ν) |
| 05 | 多元正态分布 | 点云与等高椭圆、特征向量；ρ 变化；回归线、条件分布与“向均值回归”；等价定义 |
| 06 | 极限定理与关系总图 | 均匀和的标准化密度逼近正态；贝里–埃森；17 个分布的关系总图（实线精确关系、虚线极限关系） |
| 07 | 速查表 | 期望与方差速查；四条唯一性刻画；结尾 |

## 怎么重新生成

用 [Manim Community](https://www.manim.community/)（0.22.1）画动画，ffmpeg 合成。需要 LaTeX（`texlive-latex-extra`、`texlive-fonts-recommended`、`dvisvgm`，公式用 Palatino 字体 `mathpazo`，和讲义一致）、思源黑体（`fonts-noto-cjk`），以及 `libcairo2-dev`、`libpango1.0-dev`。

```bash
cd src
pip install manim scipy requests "pillow<13"
export DASHSCOPE_API_KEY=...          # 千问（阿里云百炼）的 API Key

# 1. 口播稿：千问按 outline.py 的分镜要点写草稿 → narration.draft.json，人工审校后存为 narration.json
python write_narration.py

# 2. 配音：qwen3-tts-flash 逐段合成，写 audio/ 和 timing.json（换音色：export QWEN_VOICE=Ethan）
python tts.py

# 3. 渲染 10 个场景（1080p60，4 个并行；低清预览用 ./render_all.sh -ql）
./render_all.sh

# 4. 配音、背景音乐、字幕合成成片
python build.py
```

- `outline.py`：分镜大纲，每段写明画面和要讲的要点；`narration.json` 是审校后的口播稿（`narration.draft.json` 是千问的原始草稿，对照可以看出改了哪里）。
- `common.py`：配色、字体、版式组件（章节卡、条目抬头、数字卡）、坐标轴和常用分布的密度函数；`VScene` 按配音时长推进画面，并把每段配音的实际起点写到 `marks/`，`build.py` 按它放置配音，画面和声音不会错位。
- `scenes_a.py` ~ `scenes_e.py`：每个场景一个 `Scene`（`S00` 片头 … `S09` 速查与结尾）。`scenes_e.py` 里的 `MapStill` 可以单独渲染关系总图检查排版：`manim -qh -s scenes_e.py MapStill`。
- 字幕显示原文（λ、σ 等符号照写），送去合成的文字由 `tts.py` 的 `spoken()` 换成读音。
- 背景音乐是 `build.py` 里用正弦波合成的慢速和弦铺底，说话时自动压低。
