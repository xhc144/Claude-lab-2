# 扭结理论速通（视频）

把 Lickorish《An Introduction to Knot Theory》的 16 章做成的一支科普视频：1080p，约 21 分半，千问 AI 语音（qwen3-tts-flash，音色 Ethan）配音，带中文字幕。

- 视频：[`knot-theory-speedrun-1080p.mp4`](knot-theory-speedrun-1080p.mp4)
- 源码：[`src/`](src/)

## 内容

开场 → 16 关 → 通关，每一关对应书里的一章：

| 关 | 内容 |
|---|---|
| 01 | 扭结理论的开端：扭结图、赖德迈斯特变换、三染色 |
| 02 | 塞弗特曲面与扭结的分解：塞弗特算法、亏格、连通和、素分解 |
| 03 | 琼斯多项式：考夫曼括号、状态求和、扭数、拆接关系、三叶结的手性 |
| 04 | 交错链环的几何：棋盘染色、泰特图、泰特猜想 |
| 05 | 交错链环的琼斯多项式：跨度 = 交叉数 |
| 06 | 亚历山大多项式：塞弗特矩阵、det(V − tVᵀ)、亏格下界 |
| 07 | 覆盖空间：螺旋线覆盖圆周、无穷循环覆盖、亚历山大模 |
| 08 | 康威多项式、符号差与切片扭结 |
| 09 | 循环分支覆盖与戈里茨矩阵：行列式、透镜空间、三染色 |
| 10 | 阿尔夫不变量与琼斯多项式：V(i) = (−1)^Arf |
| 11 | 基本群：维廷格表示、三叶结群、福克斯自由微分 |
| 12 | 对 S³ 作手术：德恩手术、利科里什–华莱士定理、柯比变换 |
| 13 | 由琼斯多项式构造三维流形不变量：Ω、WRT 不变量 |
| 14 | 量子不变量的计算：坦珀利–利布代数、琼斯–文茨尔幂等元 |
| 15 | 琼斯多项式的推广：HOMFLY、考夫曼多项式 |
| 16 | HOMFLY 与考夫曼多项式的探索：辫指数、突变、未解问题 |

## 怎么重新生成

用 [manim](https://www.manim.community/)（Community 版，做的时候是 0.22.0）画动画，ffmpeg 合成。需要 LaTeX（`texlive-latex-extra`、`dvisvgm`）和思源黑体（`fonts-noto-cjk`）。

> manim 0.22 配新版 Pillow（13.x）时，画位图（棋盘染色、色轮）会报 `Invalid mode for data type`：把 `manim/camera/camera.py` 里 `Image.fromarray(np.zeros((self.pixel_height, self.pixel_width)), mode="RGBA")` 改成 `Image.new("RGBA", (self.pixel_width, self.pixel_height))` 即可。

```bash
cd src
pip install manim numpy scipy requests

# 1. 合成配音（需要千问的 DashScope API Key），生成 audio/ 和 timing.json
export DASHSCOPE_API_KEY=...        # 换音色：export QWEN_VOICE=Cherry
python tts.py

# 2. 渲染 18 段动画（1080p30，4 段并行）
./render_all.sh

# 3. 配音、背景音乐、字幕合成成片
python build.py 1080p30 扭结理论速通.mp4
```

- 解说词在 `narration.py`，改完重跑上面三步；画面按 `timing.json` 里每句话的时长对齐。
- `common.py`：配色、HUD（计时器、进度条）和扭结图引擎——由三维曲线投影、自动找交叉点、在下穿处断开，还能按 A/B 拆分交叉点（塞弗特圆、考夫曼括号状态求和、拆接树都用它算）。
- `scenes_a.py` ~ `scenes_d.py`：每章一个 Scene（`Ch00` 开场 … `Ch17` 通关）。
- 低清预览：`manim -ql scenes_a.py Ch01`，再 `python build.py 480p15 预览.mp4 1`。
