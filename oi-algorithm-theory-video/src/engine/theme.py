"""配色与版式常量。整套课程共用一种深色版式：上面是页眉，左边是图解区，右边是板书，下面是讲解文字。"""

W, H = 1920, 1080
FPS = 30


def hexc(s, a=1.0):
    s = s.lstrip("#")
    return (int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a)


def alpha(c, a):
    return (c[0], c[1], c[2], c[3] * a)


def mixc(c1, c2, u):
    return tuple(x + (y - x) * u for x, y in zip(c1, c2))


BG = hexc("#11151e")
BG2 = hexc("#171c28")       # 板书、卡片底色
BG3 = hexc("#1e2534")       # 单元格默认底色
LINE = hexc("#323c52")      # 网格线、边框
LINE2 = hexc("#4a5672")
FG = hexc("#e9edf4")        # 正文
DIM = hexc("#8a94a8")       # 次要文字
FAINT = hexc("#5b6478")

YELLOW = hexc("#f5c451")
CYAN = hexc("#5ccfe6")
GREEN = hexc("#7bd88f")
RED = hexc("#ff7b7b")
PURPLE = hexc("#b794ff")
ORANGE = hexc("#ffa45c")
BLUE = hexc("#6aa7ff")
PINK = hexc("#ff8fc7")
WHITE = hexc("#ffffff")

# 富文本里 {y|…} 这样的颜色标记
TAG_COLORS = {
    "y": YELLOW, "c": CYAN, "g": GREEN, "r": RED, "p": PURPLE,
    "o": ORANGE, "b": BLUE, "k": PINK, "d": DIM, "w": WHITE, "f": FAINT,
}

# 单元格的几种常用底色（深一些，文字仍然是亮色）
def tint(c, k=0.32):
    return mixc(BG3, c, k)


# 每个单元的主题色
UNIT_COLORS = {
    1: YELLOW, 2: CYAN, 3: GREEN, 4: BLUE, 5: ORANGE, 6: PINK, 7: PURPLE, 8: RED,
}

# 版式
HEADER_H = 78
STAGE = (40, 100, 1290, 860)        # 图解区 x0, y0, x1, y1
STAGE_WIDE = (40, 100, 1880, 860)
PANEL = (1316, 100, 1880, 860)      # 板书
CAPTION = (70, 880, 1850, 1060)     # 讲解文字

CAPTION_SIZE = 38
NOTE_SIZE = 30
