"""各集共用的小工具。"""

from engine import theme as C
from engine.core import Anim, FadeIn, FadeOut, Appear, Call, flatten
from engine.widgets import (Text, Rect, Circle, Line, Poly, Arc, Group, Cell, Array, Grid, Tree, Graph,
                            Axes, Card, Matrix, Bracket, Pointer, SegTree, hidden)

Y, CY, G, R, P, O, B, K = C.YELLOW, C.CYAN, C.GREEN, C.RED, C.PURPLE, C.ORANGE, C.BLUE, C.PINK
FG, DIM, FAINT, BG3, LINE, LINE2 = C.FG, C.DIM, C.FAINT, C.BG3, C.LINE, C.LINE2
tint = C.tint
alpha = C.alpha


def route(parent, pts, color, w=5, off=(0, 0)):
    """在 parent 里画一条折线路线（每段一条 Line，初始隐藏、长度为 0）。pts 是局部坐标。"""
    segs = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        ln = Line(x1 + off[0], y1 + off[1], x2 + off[0], y2 + off[1], color=color, w=w, prog=0.0)
        ln.tr["op"].base = 0.0
        parent.add(ln)
        segs.append(ln)
    return segs


def grow(segs, i=None):
    """让路线的第 i 段（或全部）长出来。"""
    segs = segs if i is None else [segs[i]]
    return [FadeIn(s) for s in segs] + [s.to(prog=1.0) for s in segs]


def token(parent, x, y, color, r=13, label=None):
    d = Circle(x, y, r, fill=color, stroke=C.BG, sw=3)
    d.tr["op"].base = 0.0
    d.z = 3
    parent.add(d)
    if label:
        d.add(Text(0, 0, label, size=16, color=C.BG, chain="bold"))
    return d


def label(x, y, s, size=28, color=None, anchor="cm", **kw):
    t = Text(x, y, s, size=size, color=color or FG, anchor=anchor, **kw)
    return t


def para(x, y, s, size=30, maxw=600, color=None, anchor="lt", **kw):
    return Text(x, y, s, size=size, color=color or FG, anchor=anchor, maxw=maxw, **kw)


def box(x, y, w, h, color=Y, fill=None, sw=3, r=12, dash=None):
    return Rect(x, y, w, h, fill=fill or (0, 0, 0, 0), stroke=color, sw=sw, r=r, dash=dash)


def count_up(txt, values, fmt="{}"):
    """让一个 Text 依次显示 values（配合 S.play(..., lag=...) 使用）。"""
    return [txt.to(text=fmt.format(v)) for v in values]
