"""第 16 集 扫描线：矩形面积并"""

from episodes.common import *

RECTS = [(1, 1, 4, 3), (2, 2, 6, 5), (5, 0, 7, 2)]   # (x1, y1, x2, y2)
COLS = [CY, O, P]


def brute_area(rects):
    cells = set()
    for x1, y1, x2, y2 in rects:
        for x in range(x1, x2):
            for y in range(y1, y2):
                cells.add((x, y))
    return len(cells)


def sweep():
    ys = sorted({y for r in RECTS for y in (r[1], r[3])})
    events = []
    for k, (x1, y1, x2, y2) in enumerate(RECTS):
        events.append((x1, +1, y1, y2, k))
        events.append((x2, -1, y1, y2, k))
    events.sort(key=lambda e: (e[0], -e[1]))
    m = len(ys) - 1          # 叶子 i 管 [ys[i-1], ys[i])
    cnt = {}
    ln = {}
    kids = {}

    def build(l, r):
        cnt[(l, r)] = 0
        ln[(l, r)] = 0
        if l < r:
            mid = (l + r) // 2
            kids[(l, r)] = [(l, mid), (mid + 1, r)]
            build(l, mid)
            build(mid + 1, r)

    build(1, m)

    def pull(l, r):
        if cnt[(l, r)] > 0:
            ln[(l, r)] = ys[r] - ys[l - 1]
        elif l == r:
            ln[(l, r)] = 0
        else:
            ln[(l, r)] = sum(ln[k] for k in kids[(l, r)])

    def update(l, r, ql, qr, v, touched):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            cnt[(l, r)] += v
            touched.append((l, r))
            pull(l, r)
            return
        for k in kids[(l, r)]:
            update(*k, ql, qr, v, touched)
        pull(l, r)

    steps = []
    area = 0
    prev_x = None
    for (x, v, y1, y2, k) in events:
        if prev_x is not None:
            area += ln[(1, m)] * (x - prev_x)
        ql = ys.index(y1) + 1
        qr = ys.index(y2)
        touched = []
        update(1, m, ql, qr, v, touched)
        steps.append(dict(x=x, v=v, k=k, ql=ql, qr=qr, touched=touched, cnt=dict(cnt), ln=dict(ln),
                          area=area, L=ln[(1, m)]))
        prev_x = x
    assert area == brute_area(RECTS)
    return ys, m, steps, area


def rng_label(c, l, r, ys):
    if l != r:
        return Text(c.g("x", 0) - c.box.g("w", 0) / 2 - 8, c.g("y", 0), f"[{ys[l - 1]},{ys[r]})", size=20, color=DIM,
                    anchor="rm")
    return Text(c.g("x", 0), c.g("y", 0) + 46, f"[{ys[l - 1]},{ys[r]})", size=20, color=DIM)


def build(S):
    S.cover("平面上有若干个边平行于坐标轴的矩形，它们并起来的总面积是多少？",
            ["线段树的结点信息（第 14 集）", "坐标离散化"])

    ys, m, steps, area = sweep()

    # ------------------------------------------------------------ 问题与扫描
    S.section("问题与扫描的想法")
    ax = Axes(x=380, y=470, w=560, h=440, xr=(0, 8), yr=(0, 6), xstep=1, ystep=1, grid=True)
    S.show(ax)
    rects = []
    for (x1, y1, x2, y2), c in zip(RECTS, COLS):
        rr = ax.rect((x1, y1), (x2, y2), color=c, fill_a=0.22)
        rects.append(rr)
    S.play(*[FadeIn(r) for r in rects], dur=0.6, lag=0.2)
    S.say("三个矩形互相重叠。求它们的并的面积（重叠的部分只算一次）。")
    S.note("求矩形并的面积（重叠只算一次）")
    S.say("想象一条竖直的线从左往右扫过去。在两个相邻的“事件横坐标”之间，竖线被矩形盖住的总长度 L 不变。")
    sl = ax.seg((0, 0), (0, 6), color=Y, w=3, hidden=False)
    S.play(ax.moveseg(sl, (3, 0), (3, 6)), dur=1.0)
    S.note("相邻事件之间，竖线上被覆盖的长度 L 不变", color=Y)
    S.say("所以面积 = Σ L × Δx：把图形切成一条条竖着的长条，每条是一个矩形。")
    S.note("面积 = Σ L × Δx")
    S.say("事件：矩形的左边界让区间 [y1, y2) 覆盖次数 +1，右边界让它 −1。要维护的是：一堆可增可删的 y 区间，它们的并有多长。")
    S.note("左边界：[y1, y2) 覆盖 +1；右边界：−1", color=CY)
    S.note("需要：动态维护区间并的长度 → 线段树")

    # ------------------------------------------------------------ 线段树设计
    S.section("线段树里存什么")
    S.say(f"先离散化 y 坐标：{', '.join(map(str, ys))}。相邻两个 y 之间是一个“基本段”，线段树的叶子对应基本段。")
    S.note("叶子 = 相邻两个 y 之间的基本段")
    st = SegTree(m, x=640, y=230, w=980, level_h=160, node_h=60, info_size=22, show_range=False)
    for (l, r), c in st.nodes.items():
        c.label.tr["text"].base = "c=0 L=0"
        st.add(rng_label(c, l, r, ys))
    S.show(st)
    S.say("每个结点存两个量：cnt = 有几个矩形“恰好在这个结点上”整段覆盖了它；L = 这个结点的范围里被覆盖的总长度。")
    S.note("{y|cnt}：整段覆盖本结点（在本结点打上）的矩形数", color=Y)
    S.note("{y|L}：本结点范围内被覆盖的长度", color=Y)
    S.say("L 怎么算？如果 cnt > 0，整段都被盖住，L = 区间长度；否则 L = 两个儿子的 L 之和（叶子则为 0）。")
    S.note("cnt > 0：L = 区间长；否则 L = 左.L + 右.L", color=G)
    S.say("这里有个特别之处：cnt 从来不下传。一个矩形加入时把 [y1, y2) 拆成若干结点、在这些结点上 +1；删除时拆出的是完全相同的结点，−1 正好抵消。")
    S.note("cnt 不下传：加和删拆出同一组结点，正好抵消", color=CY)
    S.say("所以 cnt 不会变成负数，也不会被“错误地遗留”。而询问只看根的 L，从来不需要往下走。这叫“标记永久化”。")

    # ------------------------------------------------------------ 扫一遍
    S.section("扫一遍")
    S.wide()
    ax2 = Axes(x=420, y=480, w=600, h=480, xr=(0, 8), yr=(0, 6), xstep=1, ystep=1, grid=True)
    S.show(ax2)
    r2 = [ax2.rect((x1, y1), (x2, y2), color=c, fill_a=0.04, sw=3) for (x1, y1, x2, y2), c in zip(RECTS, COLS)]
    S.play(*[FadeIn(r) for r in r2], dur=0.4)
    st2 = SegTree(m, x=1340, y=230, w=860, level_h=160, node_h=60, info_size=22, show_range=False)
    for (l, r), c in st2.nodes.items():
        c.label.tr["text"].base = "c=0 L=0"
        st2.add(rng_label(c, l, r, ys))
    S.show(st2)
    sl2 = ax2.seg((0, 0), (0, 6), color=Y, w=3, hidden=False)
    areat = label(1340, 760, "面积 0", 32, Y)
    S.show(areat)
    strips = []
    prev = None
    active = set()

    def covered():
        segs = sorted((RECTS[k][1], RECTS[k][3]) for k in active)
        out = []
        for a, b in segs:
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out

    for idx, stp in enumerate(steps):
        x = stp["x"]
        if prev is not None and x > prev["x"]:
            new_strips = [ax2.rect((prev["x"], a), (x, b), color=Y, fill_a=0.45, sw=0) for a, b in covered()]
            strips += new_strips
            S.play(*[FadeIn(r) for r in new_strips], ax2.moveseg(sl2, (x, 0), (x, 6)), dur=0.6)
        else:
            S.play(ax2.moveseg(sl2, (x, 0), (x, 6)), dur=0.5)
        if stp["v"] > 0:
            active.add(stp["k"])
        else:
            active.discard(stp["k"])
        k = stp["k"]
        sign = "+1" if stp["v"] > 0 else "−1"
        if idx in (0, 1, 2):
            S.say(f"x = {x}：矩形 {k + 1} 的{'左' if stp['v'] > 0 else '右'}边界，区间 [{ys[stp['ql'] - 1]}, {ys[stp['qr']]}) 覆盖 {sign}。"
                  + f"拆成结点 " + "、".join(f"[{ys[a - 1]},{ys[b]})" for a, b in stp["touched"]) + f"。根的 L 变成 {stp['L']}。")
        S.play(*[st2[t].to(stroke=COLS[k], sw=4) for t in stp["touched"]], dur=0.3)
        S.play(*[st2[key].to(text=f"c={stp['cnt'][key]} L={stp['ln'][key]}") for key in st2.nodes], dur=0.4)
        S.play(*[st2[t].to(stroke=LINE2, sw=2) for t in stp["touched"]], areat.to(text=f"面积 {stp['area']}"), dur=0.3)
        if idx > 0:
            S.wait(0.3)
        prev = stp
    S.say(f"扫完：面积 = {area}。每一段长条的面积是“上一事件后根的 L”乘以两个事件的横坐标差，逐段累加。直接数格子也是 {area}。")
    S.note_space()
    S.say("每个事件在线段树上 O(log n)，事件 2n 个，加上排序，总共 O(n log n)。")

    # ------------------------------------------------------------ 手推题
    S.narrow()
    S.quiz("改成求“至少被两个矩形覆盖”的面积。\n\n"
           "线段树结点除了 cnt，还要存什么？写出它的计算式（仍然不下传 cnt）。", think=20)
    S.say("要求覆盖 ≥ 2 次的长度，记作 L2；同时还需要覆盖 ≥ 1 次的长度 L1（就是原来的 L）。")
    S.note("存 cnt、L1（≥1 次）、L2（≥2 次）", color=Y)
    S.say("cnt ≥ 2：本结点整段已被盖了两次，L2 = 区间长。")
    S.note("cnt ≥ 2：L2 = 区间长")
    S.say("cnt = 1：本结点已经盖了一次，儿子里只要再被盖过一次就够两次，所以 L2 = 左.L1 + 右.L1（叶子为 0）。")
    S.note("cnt = 1：L2 = 左.L1 + 右.L1", color=G)
    S.say("cnt = 0：两次都得来自下面，L2 = 左.L2 + 右.L2。")
    S.note("cnt = 0：L2 = 左.L2 + 右.L2")
    S.say("关键：本结点的 cnt 会“抬高”儿子信息的含义。这个设计又是“缺什么补什么”——为了算 L2，需要儿子的 L1。", extra=0.5)

    S.recap([
        "扫描线把二维面积变成一维问题：相邻事件之间覆盖长度不变，面积 = Σ L × Δx。",
        "左边界区间覆盖 +1，右边界 −1；离散化后用线段树维护“区间并的长度”。",
        "结点存 cnt 和 L：cnt > 0 时 L = 区间长，否则 L = 儿子 L 之和。",
        "cnt 不下传：加删拆出同一组结点、成对抵消，询问只看根。这叫标记永久化。",
    ], next_title="动态开点与线段树合并：只建用得到的结点")
