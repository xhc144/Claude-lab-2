# 第一次做，多半做不出来：几何与拓扑中的五道经典难题

一支约 18 分钟的数学讲解视频。动画用 Manim 制作，旁白由通义千问 TTS（`qwen3-tts-flash`，音色 Elias）合成，字幕根据每句语音的实际时长自动对齐。

## 内容

| 章节 | 题目 | 关键思路 |
|---|---|---|
| 01 | 僧人登山 | 把两天叠成一天 → 介值定理 |
| 02 | 对跖点的温度 | 直径转半圈，差值变号 → Borsuk–Ulam 定理 |
| 03 | 三座房子与三种管线 | 欧拉公式 V−E+F=2 推出矛盾；在环面上却能连通（3D 卷纸成甜甜圈） |
| 04 | 布丰投针 | 针 → 面条 → 圆，得到 2l/πd；蒙特卡洛估算 π；勒洛三角形与巴比耶定理 |
| 05 | 内接矩形 | 点对升到三维形成"帐篷"曲面；点对空间是莫比乌斯带；射影平面放不进三维 ⇒ 曲面必自相交 |

## 文件

- `output/几何与拓扑五道经典难题.mp4`：成片（1080p30，H.264 + AAC，内嵌章节标记）。为了不超过 GitHub 单文件 100 MB 的限制，仓库里这份是两遍编码压缩过的版本（约 90 MB）
- `output/字幕.srt`：独立字幕文件（成片已烧录字幕）
- `script.py`：全部旁白文本（字幕文本与朗读文本可分别指定）
- `tts.py`：调用 DashScope 逐句合成语音，生成 `audio/timing.json`（每段时长与每句起止时间）。语音文件本身（`audio/seg/`、`audio/sent/`）没有放进仓库，用 `tts.py` 重新生成
- `common.py`：配色、霓虹发光、章节卡、语音同步、快速 3D 曲面等公共组件
- `s0_intro_outro.py` … `s5_rectangle.py`：各章节动画
- `rect_math.py`：第五题曲线及内接矩形族的数值求解
- `build.py`：并行渲染、拼接、混音（人声 + 合成配乐 + 转场音效）、星空背景合成、烧录字幕

## 重新生成

```bash
python3 -m venv .venv && .venv/bin/pip install manim scipy requests
export DASHSCOPE_API_KEY=sk-...          # 千问 API Key（北京地域）
.venv/bin/python tts.py                  # 合成旁白（可用 TTS_VOICE=Ethan 等切换音色）
.venv/bin/python build.py render         # 1080p30 渲染全部镜头（4 进程并行）
.venv/bin/python build.py assemble       # 混音、字幕、背景，输出成片
```

依赖：ffmpeg（含 libass）、LaTeX（texlive + dvisvgm）、Noto Sans CJK 字体。
修改旁白后需重新运行 `tts.py` 和 `render`：动画会按新的语音时长自动重新对齐。
重新合成的语音时长可能和仓库里的 `audio/timing.json` 略有出入，`render` 会按新的时长重新排布动画，不需要手动调整。
渲染缓存（`media/`）、中间文件（`build/`、`logs/`）都在 `.gitignore` 里，不进仓库。
