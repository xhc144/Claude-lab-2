"""第 18 集 DFS 序：把子树变成区间"""

from episodes.common import *

EDGES = [(1, 4), (1, 2), (1, 7), (4, 8), (4, 3), (2, 6), (7, 5)]
VAL = {1: 3, 2: 1, 3: 4, 4: 2, 5: 5, 6: 2, 7: 1, 8: 3}


def dfs_times():
    ch = {}
    for p, c in EDGES:
        ch.setdefault(p, []).append(c)
    tin, tout, order = {}, {}, []
    euler = []        # (结点, +1 进 / -1 出)
    t = [0]

    def go(u):
        t[0] += 1
        tin[u] = t[0]
        order.append(u)
        euler.append((u, +1))
        for c in ch.get(u, []):
            go(c)
        tout[u] = t[0]
        euler.append((u, -1))

    go(1)
    return tin, tout, order, euler, ch


def build(S):
    S.cover("树上的操作“把 u 的子树全部加 x”“求 u 的子树和”“求 v 到根的路径和”，怎样变成数组上的区间问题？",
            ["树的 DFS", "树状数组的区间变换（第 13 集）"])

    tin, tout, order, euler, ch = dfs_times()

    # ------------------------------------------------------------ DFS 序
    S.section("DFS 序：进入的时间")
    tree = Tree(EDGES, 1, x=420, y=400, w=560, h=420, r=30, size=26)
    S.show(tree)
    S.say("一棵树，要支持“子树加”“子树求和”。子树在树上是一团，没法直接用数组上的数据结构。")
    S.note("目标：子树操作 → 数组上的区间操作")
    S.say("做一次 DFS，记下每个点{y|第一次被访问的时间} in[u]。把点按 in 排成一排，就是 DFS 序。")
    S.note("in[u]：DFS 第一次到达 u 的时间")
    seq = Array([""] * 8, x=640, y=780, cw=86, ch=60, gap=8, size=28)
    S.show(seq, label(150, 780, "DFS 序", 24, DIM, anchor="rm"))
    tags = {v: tree.tag(v, "", "r", Y, 22) for v in tin}
    for u in order:
        S.play(tree[u].to(fill=tint(Y, 0.4), stroke=Y), FadeIn(tags[u]), tags[u].to(text=f"in={tin[u]}"),
               seq.cells[tin[u] - 1].to(text=str(u), fill=tint(Y, 0.25)), dur=0.45)
        S.play(tree[u].to(fill=tint(CY, 0.25), stroke=CY), dur=0.15)
    S.say("关键事实：DFS 进入 u 之后，会把 u 的整棵子树走完才离开 u，期间不会去访问子树外的点。")
    S.say("所以 u 的子树在 DFS 序里是{y|连续的一段}：从 in[u] 开始，到子树里最后被访问的点为止，记作 out[u]。")
    S.note("u 的子树 = DFS 序上的区间 [in[u], out[u]]", color=Y)
    for u, col in ((4, O), (2, G), (7, P)):
        sp = seq.span(tin[u], tout[u], f"子树 {u}", col, "above")
        S.play(FadeIn(sp), *[tree[v].to(stroke=col, sw=4) for v in tree.subtree(u)], dur=0.5)
        S.wait(0.4)
    S.play(*[tree[v].to(stroke=CY, sw=2.5) for v in tin], dur=0.3)

    # ------------------------------------------------------------ 括号结构
    S.section("括号结构")
    S.say("把每个点的区间 [in, out] 看成一对括号：任意两个点的区间，要么一个套住另一个，要么完全不相交，不会交叉。")
    S.note("任意两点的 [in, out]：嵌套 或 不相交，不会交叉", color=Y)
    br = Group(0, 0)
    xs = {i: 240 + (i - 1) * 110 for i in range(1, 9)}
    for i, u in enumerate(order, start=1):
        br.add(Text(xs[i], 420, str(u), size=28, color=FG))
    lvl = {}
    for u in order:
        d = 0
        p = u
        while p != 1:
            p = next(a for a, b in EDGES if b == p)
            d += 1
        lvl[u] = d
    bars = []
    for u in order:
        x1, x2 = xs[tin[u]] - 40, xs[tout[u]] + 40
        y = 470 + lvl[u] * 34
        b = Line(x1, y, x2, y, color=[Y, CY, G, O][lvl[u] % 4], w=5)
        b.tr["op"].base = 0
        br.add(b)
        bars.append(b)
    S.show(br)
    S.play(*[FadeIn(b) for b in bars], dur=1.0, lag=0.1)
    S.say("嵌套恰好对应祖先关系：u 是 v 的祖先 ⇔ v 的区间套在 u 的区间里 ⇔ in[u] ≤ in[v] ≤ out[u]。O(1) 判断祖先。")
    S.note("u 是 v 的祖先 ⇔ in[u] ≤ in[v] ≤ out[u]", color=G)
    S.say("于是“子树加 x”就是 DFS 序上的区间加，“子树求和”就是区间求和——交给树状数组或线段树，各 O(log n)。")
    S.note("子树加 / 子树和 → 区间加 / 区间和")

    # ------------------------------------------------------------ 到根路径
    S.section("到根路径：进加出减")
    S.say("另一类询问：点 v 到根的路径上所有点的权值和（支持单点修改）。路径不是 DFS 序上的一段，怎么办？")
    S.note("询问：v 到根的路径和；修改：单点改权值")
    S.say("把离开 u 的时刻也记下来，得到长度 2n 的“欧拉序”：进入 u 时写 +val[u]，离开 u 时写 −val[u]。")
    S.note("欧拉序：进入写 +val，离开写 −val（长 2n）", color=Y)
    eu = Array(["" for _ in euler], x=640, y=300, cw=66, ch=58, gap=4, size=22, index=False)
    for i, (u, s) in enumerate(euler):
        eu.cells[i].label.tr["text"].base = f"{'+' if s > 0 else '−'}{VAL[u]}"
        eu.cells[i].box.tr["fill"].base = tint(G if s > 0 else R, 0.25)
    nm = Array([str(u) for u, s in euler], x=640, y=240, cw=66, ch=40, gap=4, size=20, index=False, fill=(0, 0, 0, 0),
               stroke=(0, 0, 0, 0))
    S.show(nm, eu)
    S.show(label(640, 190, "（上：结点编号　下：写入的值）", 22, DIM))
    tree2 = Tree(EDGES, 1, x=640, y=600, w=560, h=300, r=26, size=24)
    vt = {u: tree2.tag(u, f"{VAL[u]}", "r", DIM, 20, hidden=False) for u in VAL}
    S.show(tree2)
    v = 3
    pos_in = next(i for i, (u, s) in enumerate(euler) if u == v and s > 0)
    S.say(f"求点 {v} 到根的和：取欧拉序上从开头到“进入 {v}”为止的前缀和。")
    fr = eu.frame(1, pos_in + 1, Y)
    S.play(FadeIn(fr), dur=0.4)
    S.say(f"这一段里，已经完整走完的点（比如 8：进入和离开都在里面）+ 和 − 正好抵消；还没离开的点，恰好就是 {v} 的祖先和 {v} 自己。")
    for i in range(pos_in + 1):
        u, s = euler[i]
        closed = any(j <= pos_in and euler[j] == (u, -1) for j in range(len(euler)))
        if closed:
            S.play(eu.cells[i].to(fill=alpha(BG3, 0.4), tc=FAINT), dur=0.15)
    anc = [u for u in tin if tin[u] <= tin[v] <= tout[u]]
    S.say(f"剩下的是 " + "、".join(f"+{VAL[u]}（点 {u}）" for u in sorted(anc, key=lambda x: tin[x])) +
          f"，和 = {sum(VAL[u] for u in anc)}，正是路径 {v}→{'→'.join(str(u) for u in sorted(anc, key=lambda x: -tin[x])[1:])} 的权值和。")
    S.play(*[tree2[u].to(fill=tint(Y, 0.45), stroke=Y) for u in anc], dur=0.5)
    S.play(*[tree2[u].to(fill=alpha(BG3, 0.5), stroke=LINE) for u in (8,)], dur=0.3)
    S.note("前缀和到 in[v]：走完的点 ± 抵消，剩下的正是 v 的祖先", color=G)
    S.say("修改点 u 的权值：改它的“进入”和“离开”两个位置。询问：一次前缀和。还是树状数组，各 O(log n)。")
    S.note("单点改 = 改两个位置；询问 = 一次前缀和")
    S.say("有了到根路径和，任意两点 u、v 之间的路径和 = S(u) + S(v) − S(lca) − S(lca 的父亲)。LCA 下一集讲。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("操作改成：把 u 的子树里每个点的权值都加 x；询问：v 到根的路径和。\n\n"
           "(1) 一次“子树加 x”，对 v 到根的路径和贡献多少？（v 在 u 的子树里时，用深度表示）\n"
           "(2) 怎样用两个树状数组维护？", think=20)
    S.say("(1) v 在 u 的子树里时，路径 v→根上属于 u 子树的点是 u 到 v 这一段，共 dep[v] − dep[u] + 1 个，贡献 x × (dep[v] − dep[u] + 1)。不在子树里则贡献 0。")
    S.note("(1) 贡献 = x × (dep[v] − dep[u] + 1)，v 在 u 子树内", color=Y)
    S.say("(2) 拆开：x × (dep[v] + 1) − x × dep[u]。第一项里 x 和 v 分开了，第二项只和修改有关——和第 13 集的拆法一模一样。")
    S.note("= (dep[v] + 1) × x − x·dep[u]")
    S.say("树状数组 A：在 [in[u], out[u]] 上区间加 x；树状数组 B：同一区间加 x·dep[u]。询问 v：(dep[v]+1) × A 在 in[v] 的值 − B 在 in[v] 的值。")
    S.note("BIT A 区间加 x，BIT B 区间加 x·dep[u]；答 (dep[v]+1)·A − B（单点查）", color=G)
    S.say("DFS 序负责把“子树”变成“区间”，后面的事情又回到了熟悉的区间问题。", extra=0.5)

    S.recap([
        "DFS 进入 u 后会走完整棵子树才离开，所以子树在 DFS 序上是连续区间 [in[u], out[u]]。",
        "任意两点的区间要么嵌套、要么不相交；嵌套 ⇔ 祖先关系，in[u] ≤ in[v] ≤ out[u]。",
        "子树加 / 子树和 = DFS 序上的区间加 / 区间和。",
        "到根路径和：欧拉序上进入写 +val、离开写 −val，前缀和里走完的点相互抵消，只剩祖先。",
    ], next_title="倍增与 LCA 的应用：按二进制跳")
