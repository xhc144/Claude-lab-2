"""配色与版式常量。

整套课程共用一种深色版式：上面是细细的页眉，左边是图解区，右边是板书卡片，下面是讲解文字。
配色是低饱和的“夜色”底（靛蓝偏紫，带一点径向渐变和暗角）配柔和的粉彩强调色，长时间看不刺眼。
"""

W, H = 1920, 1080
FPS = 30


def hexc(s, a=1.0):
    s = s.lstrip("#")
    return (int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a)


def alpha(c, a):
    return (c[0], c[1], c[2], c[3] * a)


def mixc(c1, c2, u):
    return tuple(x + (y - x) * u for x, y in zip(c1, c2))


# 底色（由深到浅）
BG0 = hexc("#10111b")       # 画面四角
BG = hexc("#171927")        # 画面主体
BG_HI = hexc("#20233a")     # 渐变的亮处
BG2 = hexc("#1e2134")       # 板书、卡片
BG3 = hexc("#272b42")       # 单元格、结点默认底色
LINE = hexc("#383d5a")      # 网格线、边框
LINE2 = hexc("#525a7e")     # 树和图的边
FG = hexc("#e8eaf6")        # 正文
DIM = hexc("#a0a6c4")       # 次要文字
FAINT = hexc("#6b7192")

# 强调色：柔和的粉彩
YELLOW = hexc("#f6cb72")
CYAN = hexc("#76d3e4")
GREEN = hexc("#93d8a2")
RED = hexc("#f3808e")
PURPLE = hexc("#bba1f6")
ORANGE = hexc("#f6a974")
BLUE = hexc("#86aaf6")
PINK = hexc("#f29fca")
WHITE = hexc("#ffffff")

# 富文本里 {y|…} 这样的颜色标记
TAG_COLORS = {
    "y": YELLOW, "c": CYAN, "g": GREEN, "r": RED, "p": PURPLE,
    "o": ORANGE, "b": BLUE, "k": PINK, "d": DIM, "w": WHITE, "f": FAINT,
}


def tint(c, k=0.32):
    """单元格的强调底色：在默认底色里掺一点强调色，文字仍然是亮色。"""
    return mixc(BG3, c, k)


# 每个单元的主题色
UNIT_COLORS = {
    1: YELLOW, 2: CYAN, 3: GREEN, 4: BLUE, 5: ORANGE, 6: PINK, 7: PURPLE, 8: RED,
}

# 版式
HEADER_H = 84
STAGE = (40, 104, 1296, 862)        # 图解区 x0, y0, x1, y1
STAGE_WIDE = (40, 104, 1880, 862)
PANEL = (1324, 112, 1880, 860)      # 板书卡片
CAPTION = (96, 892, 1840, 1056)     # 讲解文字

CAPTION_SIZE = 38
NOTE_SIZE = 29

# ------------------------------------------------------------------ 背景
_bg_image = None


def background(cv):
    """画面背景：左上偏亮的径向渐变 + 暗角。只生成一次，以后每帧直接贴图。"""
    global _bg_image
    import skia
    if _bg_image is None:
        surf = skia.Surface(W, H)
        c = surf.getCanvas()
        c.clear(skia.Color4f(*BG))
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(
            (W * 0.30, H * 0.22), W * 0.85,
            [skia.Color4f(*BG_HI).toColor(), skia.Color4f(*BG).toColor(), skia.Color4f(*BG0).toColor()],
            [0.0, 0.55, 1.0]))
        c.drawRect(skia.Rect.MakeWH(W, H), p)
        # 右下角一点冷色的辉光，让画面不那么平
        q = skia.Paint(AntiAlias=True)
        q.setShader(skia.GradientShader.MakeRadial(
            (W * 0.92, H * 0.95), W * 0.45,
            [skia.Color4f(0.35, 0.30, 0.65, 0.10).toColor(), skia.Color4f(0.35, 0.30, 0.65, 0.0).toColor()],
            [0.0, 1.0]))
        c.drawRect(skia.Rect.MakeWH(W, H), q)
        _bg_image = surf.makeImageSnapshot()
    cv.drawImage(_bg_image, 0, 0)
