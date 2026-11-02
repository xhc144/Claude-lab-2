"""第 50 集 可持久化线段树：只复制改动的那条路径"""

from episodes.common import *

A0 = [5, 2, 7, 1]
UPD = (3, 4)                      # 把第 3 个数改成 4
ARR = [2, 4, 1, 3, 2]             # 第二部分：值域 [1, 4]
Q = (2, 4, 2)                     # [2, 4] 里第 2 小


def kth(l, r, k):
    return sorted(ARR[l - 1:r])[k - 1]


def build(S):
    S.cover("对数组做很多次单点修改，还要能随时查询“第 t 次修改之后”的版本。每个版本都复制一棵线段树太浪费——修改到底改了哪些结点？",
            ["线段树（第 14 集）", "动态开点与线段树合并（第 17 集）", "整体二分（第 34 集，同一问题的另一种解法）"])

    # ------------------------------------------------------------ 只复制一条路径
    S.section("一次修改只动一条路径")
    n = len(A0)
    lv = {(1, 4): 0, (1, 2): 1, (3, 4): 1, (1, 1): 2, (2, 2): 2, (3, 3): 2, (4, 4): 2}
    ys = [230, 400, 570]
    W = 560

    def xpos(l, r, ox):
        return ox - W / 2 + ((l + r) / 2 - 0.5) * W / n

    def sums(arr):
        return {(l, r): sum(arr[l - 1:r]) for (l, r) in lv}

    s0 = sums(A0)
    A1 = A0[:]
    A1[UPD[0] - 1] = UPD[1]
    s1 = sums(A1)
    ox0, ox1 = 330, 930
    boxes0 = {}
    edges0 = []
    for (l, r), d in lv.items():
        g = Group(xpos(l, r, ox0), ys[d])
        g.add(Rect(0, 0, 112, 56, fill=BG3, stroke=LINE2, sw=2, r=10))
        g.add(Text(0, -44, f"[{l},{r}]", size=19, color=DIM))
        g.add(Text(0, 0, str(s0[(l, r)]), size=26))
        boxes0[(l, r)] = g
    for (l, r) in lv:
        if l < r:
            m = (l + r) // 2
            for c in ((l, m), (m + 1, r)):
                edges0.append(Line(xpos(l, r, ox0), ys[lv[(l, r)]] + 28, xpos(*c, ox0), ys[lv[c]] - 28, color=LINE2, w=2.5))
    S.show(*edges0, *boxes0.values(), label(ox0, 140, "版本 0（区间和）", 24, DIM), dur=0.6)
    S.say(f"版本 0：数组 {', '.join(map(str, A0))} 的区间和线段树。现在把第 {UPD[0]} 个数改成 {UPD[1]}，得到版本 1。")
    path = [(1, 4), (3, 4), (3, 3)]
    for p in path:
        S.play(boxes0[p].children[0].to(stroke=O, sw=3.5), dur=0.25)
    S.say("单点修改只会改到“根到这个叶子”的路径上的结点：这里是 3 个（橙色）。其他结点的值一点都没变。")
    S.note("单点修改只影响根到叶子的 O(log n) 个结点", color=Y)
    S.say("那就只给这条路径上的结点新建副本，其余的直接指向旧版本的结点——新旧版本共享没变的部分。")
    new = {}
    new_edges = []
    for p in path:
        g = Group(xpos(*p, ox1), ys[lv[p]])
        g.add(Rect(0, 0, 112, 56, fill=tint(O, 0.3), stroke=O, sw=3, r=10))
        g.add(Text(0, -44, f"[{p[0]},{p[1]}]", size=19, color=DIM))
        g.add(Text(0, 0, str(s1[p]), size=26))
        g.tr["op"].base = 0
        new[p] = g
    links = [((1, 4), (1, 2), False), ((1, 4), (3, 4), True), ((3, 4), (3, 3), True), ((3, 4), (4, 4), False)]
    for a, b, is_new in links:
        x1, y1 = xpos(*a, ox1), ys[lv[a]] + 28
        if is_new:
            x2, y2 = xpos(*b, ox1), ys[lv[b]] - 28
            ln = Line(x1, y1, x2, y2, color=O, w=3)
        else:
            x2, y2 = xpos(*b, ox0), ys[lv[b]] - 28
            ln = Line(x1, y1, x2, y2, color=CY, w=3, dash=(9, 6), head=12)
        ln.tr["op"].base = 0
        new_edges.append(ln)
    S.add(*new_edges, *new.values())
    S.play(*[FadeIn(new[p], dx=-20) for p in path], FadeIn(label(ox1, 140, "版本 1 新建的结点", 24, O)), dur=0.7, lag=0.15)
    S.play(*[FadeIn(e) for e in new_edges], dur=0.6)
    S.say(f"新根 [1,4] 的左儿子还是旧的 [1,2]（青色虚线指回去），右儿子是新的 [3,4]；新 [3,4] 的右儿子还是旧的 [4,4]。版本 1 的总和是 {s1[(1, 4)]}。")
    S.note("每次修改新建 O(log n) 个结点，其余指向旧结点", color=G)
    S.say("从版本 1 的根往下走，看到的就是完整的新数组；从版本 0 的根走，看到的还是旧数组——两个版本同时存在，互不干扰。")
    S.note("roots[t] = 第 t 个版本的根；查询某版本就从它的根出发", color=Y)
    S.say("m 次修改总共 O(n + m log n) 个结点。代价是不能再用“2i、2i + 1”编号孩子，要像动态开点那样给每个结点存左右儿子指针。", extra=0.3)
    S.note("空间 O(n + m log n)；孩子用指针（动态开点）")

    # ------------------------------------------------------------ 第 k 小
    S.section("前缀版本相减：区间第 k 小")
    S.say(f"经典应用：静态数组的区间第 k 小。数组 {', '.join(map(str, ARR))}，值域 1～4。对值域建线段树，结点存“落在这段值域里的数有几个”。")
    S.note("值域线段树：结点存“值在 [L, R] 里的数的个数”", color=Y)
    S.say("把数组从左到右依次插入，每插一个就得到一个新版本：版本 i 记录前 i 个数的分布。")
    S.note("版本 i = 插入 a₁…aᵢ 后的值域线段树（前缀）", color=Y)
    l, r, k = Q
    cnt = lambda upto, L, R: sum(1 for x in ARR[:upto] if L <= x <= R)       # noqa: E731
    st = SegTree(4, x=520, y=270, w=760, level_h=150, node_h=62, info_size=22)
    S.show(st, label(520, 170, "值域 [1, 4] 的线段树", 24, DIM))
    arr = Array(ARR, x=1100, y=230, cw=60, ch=54, gap=6, size=26)
    S.show(arr)
    fr = arr.frame(l, r, CY)
    S.play(FadeIn(fr), dur=0.4)
    nodes = list(st.nodes.keys())
    S.play(*[st.info[nd].to(text=f"{cnt(r, *nd)} − {cnt(l - 1, *nd)}") for nd in nodes], dur=0.6)
    S.say(f"询问 [{l}, {r}] 的第 {k} 小。关键：版本 {r} 减去版本 {l - 1}，每个结点的计数之差就是“[{l}, {r}] 里值在这段的数有几个”。结点里写的就是这两个数。")
    S.note(f"结点计数：cnt_{{r}} − cnt_{{l−1}} = 区间 [l, r] 里落在这段值域的个数", color=G)
    S.play(*[st.info[nd].to(text=str(cnt(r, *nd) - cnt(l - 1, *nd))) for nd in nodes], dur=0.6)
    cur = (1, 4)
    kk = k
    while cur[0] < cur[1]:
        L_, R_ = cur
        m = (L_ + R_) // 2
        left = cnt(r, L_, m) - cnt(l - 1, L_, m)
        S.play(st[cur].to(stroke=Y, sw=4), dur=0.3)
        if left >= kk:
            S.say(f"在 [{L_},{R_}]：左半值域 [{L_},{m}] 有 {left} 个 ≥ k = {kk}，第 {kk} 小在左边。")
            cur = (L_, m)
        else:
            S.say(f"在 [{L_},{R_}]：左半只有 {left} 个 < k = {kk}，去右半找第 {kk} − {left} = {kk - left} 小。")
            kk -= left
            cur = (m + 1, R_)
    S.play(st[cur].to(stroke=G, sw=4, fill=tint(G, 0.35)), dur=0.4)
    ans = cur[0]
    assert ans == kth(l, r, k)
    S.say(f"走到叶子 {ans}：[{l}, {r}] 里是 {', '.join(map(str, ARR[l - 1:r]))}，排序后第 {k} 个确实是 {ans}。每次询问 O(log V)。", extra=0.3)
    S.note("从根往下走，左边够 k 个就往左，否则 k 减去左边去右；O(log V)", color=G)

    # ------------------------------------------------------------ 手推题
    S.quiz("(1) n = 8 的线段树，单点修改一次要新建几个结点？做 10 次修改后总共有几个结点？\n"
           f"(2) 数组 {', '.join(map(str, ARR))}，用前缀版本相减求区间 [1, 5] 的第 4 小：从根往下每一步的判断是什么？", think=20)
    S.say("(1) 根到叶子的路径有 log₂8 + 1 = 4 个结点，每次新建 4 个。初始树 2·8 − 1 = 15 个，10 次修改后 15 + 40 = 55 个。")
    S.note("(1) 每次 4 个；共 15 + 40 = 55 个", color=Y)
    l2, r2, k2 = 1, 5, 4
    cur, kk = (1, 4), k2
    steps = []
    while cur[0] < cur[1]:
        L_, R_ = cur
        m = (L_ + R_) // 2
        left = cnt(r2, L_, m) - cnt(l2 - 1, L_, m)
        if left >= kk:
            steps.append(f"[{L_},{R_}]：左边 {left} 个 ≥ {kk}，往左")
            cur = (L_, m)
        else:
            steps.append(f"[{L_},{R_}]：左边 {left} 个 < {kk}，k 变成 {kk - left}，往右")
            kk -= left
            cur = (m + 1, R_)
    assert cur[0] == kth(l2, r2, k2)
    S.say("(2) " + "；".join(steps) + f"；到达叶子 {cur[0]}。")
    S.say(f"验算：全部 5 个数排序是 {', '.join(map(str, sorted(ARR)))}，第 4 个是 {cur[0]}。", extra=0.5)
    S.note(f"(2) 第 4 小 = {cur[0]}", color=G)

    S.recap([
        "单点修改只改根到叶子的 O(log n) 个结点：只复制这条路径，其余共享旧版本。",
        "每个版本记一个根；任何历史版本都能从它的根出发查询。",
        "区间第 k 小：按前缀依次插入得到版本，版本 r 减版本 l − 1 就是区间里的值分布。",
        "在差值树上二分下降：左边够 k 个就向左，否则减去左边向右，O(log V)。",
    ], next_title="点分治")
