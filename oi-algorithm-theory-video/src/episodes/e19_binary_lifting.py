"""第 19 集 倍增与 LCA 的应用：按二进制跳"""

from episodes.common import *

EDGES = [(1, 2), (1, 3), (2, 4), (4, 7), (7, 10), (3, 5), (3, 6), (5, 8), (8, 11), (6, 9), (9, 12)]
WEIGHT = {(1, 2): 4, (1, 3): 2, (2, 4): 7, (4, 7): 1, (7, 10): 3, (3, 5): 5, (3, 6): 6, (5, 8): 2, (8, 11): 8,
          (6, 9): 3, (9, 12): 1}
K = 3


def tables():
    par = {1: 1}
    dep = {1: 0}
    for p, c in EDGES:
        par[c] = p
        dep[c] = dep[p] + 1
    up = [dict(par)]
    for k in range(1, K):
        up.append({v: up[k - 1][up[k - 1][v]] for v in par})
    return par, dep, up


def lca_steps(u, v, dep, up):
    steps = []
    if dep[u] < dep[v]:
        u, v = v, u
    d = dep[u] - dep[v]
    for k in range(K - 1, -1, -1):
        if d >> k & 1:
            steps.append(("lift", k, u, up[k][u]))
            u = up[k][u]
    if u == v:
        return steps, u
    for k in range(K - 1, -1, -1):
        if up[k][u] != up[k][v]:
            steps.append(("both", k, (u, v), (up[k][u], up[k][v])))
            u, v = up[k][u], up[k][v]
        else:
            steps.append(("skip", k, (u, v), up[k][u]))
    return steps, up[0][u]


def build(S):
    S.cover("一棵很深的树上有大量询问：两点的最近公共祖先（LCA）、距离、第 k 个祖先、路径上的最大边。怎样每次 O(log n) 回答？",
            ["树的深度与父亲", "二进制表示"])

    par, dep, up = tables()

    # ------------------------------------------------------------ 一步一步太慢
    S.section("一步一步往上爬太慢")
    tree = Tree(EDGES, 1, x=500, y=460, w=720, h=520, r=28, size=24)
    S.show(tree)
    S.say("想找点 11 和点 12 的最近公共祖先：最直接的办法是先把深的那个点往上爬到同一深度，再两个一起一步一步往上爬，直到相遇。")
    S.note("朴素：一步一步往上爬，O(深度)")
    for a, b in [(11, 8), (12, 9)]:
        S.play(tree.edge(a, b).to(color=O, w=5), dur=0.3)
    for a, b in [(8, 5), (9, 6)]:
        S.play(tree.edge(a, b).to(color=O, w=5), dur=0.3)
    for a, b in [(5, 3), (6, 3)]:
        S.play(tree.edge(a, b).to(color=O, w=5), dur=0.3)
    S.play(tree[3].flash(Y), dur=0.6)
    S.say("树退化成一条链时深度是 n，每次询问 O(n)。我们需要“一次跳很多步”。")
    S.play(*[tree.edge(a, b).to(color=LINE2, w=3) for a, b in EDGES], dur=0.3)

    # ------------------------------------------------------------ 倍增表
    S.section("倍增表：跳 2^k 步", keep=[tree])
    S.say("对每个点 v 预先存好：往上跳 1 步、2 步、4 步、……、2^k 步分别到哪里，记作 up[k][v]。")
    S.note("{y|up[k][v]}：v 往上跳 2^k 步到达的祖先", color=Y)
    S.say("这张表怎么算？跳 2^k 步 = 先跳 2^(k−1) 步，再从那里跳 2^(k−1) 步：up[k][v] = up[k−1][ up[k−1][v] ]。")
    S.note("up[k][v] = up[k−1][ up[k−1][v] ]（两次 2^(k−1)）", color=G)
    a1 = Line(color=CY, w=4, head=12, bend=0.35).attach(tree[11], tree[5])
    a2 = Line(color=CY, w=4, head=12, bend=0.35).attach(tree[5], tree[1])
    a3 = Line(color=Y, w=5, head=14, bend=-0.3).attach(tree[11], tree[1])
    for a in (a1, a2, a3):
        a.tr["op"].base = 0
        tree.add(a)
    S.play(FadeIn(a1), dur=0.4)
    S.play(FadeIn(a2), dur=0.4)
    S.play(FadeIn(a3), dur=0.5)
    S.say("例：up[2][11]（跳 4 步）= 先跳 2 步到 5，再从 5 跳 2 步到 1。只要按 k 从小到大算，用到的都已经算好。")
    S.say("每个点存 log n 个值，预处理 O(n log n)。跳出根的统一记成根。")
    S.play(FadeOut(a1, a2, a3), dur=0.3)
    S.wide()
    nodes = sorted(par)
    g = Grid(K, len(nodes), x=960, y=600, cw=88, ch=54, gap=4, size=24, rlab=[f"up[{k}]" for k in range(K)],
             clab=[str(v) for v in nodes], vals=[[str(up[k][v]) for v in nodes] for k in range(K)])
    S.play(tree.to(x=960, y=300, sc=0.62), dur=0.6)
    S.show(g)
    S.say("整张表：第 k 行是每个点跳 2^k 步的结果。（根的祖先记为根自己。）")

    # ------------------------------------------------------------ 第 k 个祖先
    S.section("第 k 个祖先与 LCA")
    S.narrow()
    tree2 = Tree(EDGES, 1, x=500, y=460, w=720, h=520, r=28, size=24)
    S.show(tree2)
    S.say("跳任意 k 步：把 k 写成二进制，比如 3 = 2 + 1，就先跳 2 步再跳 1 步。每一位 1 跳一次，最多 log n 次。")
    S.note("第 k 个祖先：k 的每个二进制 1 跳一次", color=Y)
    tk = tree2.token(10, Y, 11)
    S.play(FadeIn(tk), dur=0.3)
    S.play(tk.to(x=tree2[4].g("x", 0), y=tree2[4].g("y", 0)), dur=0.6)
    S.play(tk.to(x=tree2[2].g("x", 0), y=tree2[2].g("y", 0)), dur=0.5)
    S.play(FadeOut(tk), dur=0.3)
    S.say("求 LCA 分两步。第一步：把较深的点跳到和另一个点同样深（跳的步数就是深度差，按二进制跳）。")
    S.note("LCA 第一步：深的点跳到同一深度")
    S.say("第二步：两个点一起往上跳，k 从大到小试：如果 up[k][u] ≠ up[k][v]，两个都跳；相等就不跳。")
    S.note("第二步：k 从大到小，祖先不同才一起跳", color=Y)
    S.say("最后 u、v 停在 LCA 的两个儿子上，LCA = u 的父亲。")
    S.note("最后：LCA = up[0][u]")

    steps, l = lca_steps(11, 12, dep, up)
    tu = tree2.token(11, CY, 12)
    tv = tree2.token(12, O, 12)
    S.play(FadeIn(tu), FadeIn(tv), dur=0.3)
    S.say("例：LCA(11, 12)，两点同深度，直接第二步。")
    for st in steps:
        kind, k = st[0], st[1]
        if kind == "skip":
            (u, v), a = st[2], st[3]
            S.say(f"k = {k}（跳 {2 ** k} 步）：两点都会跳到 {a}——祖先相同，可能已经跳过头了，不跳。")
            S.play(tree2[a].flash(R), dur=0.7)
        elif kind == "both":
            (u, v), (nu, nv) = st[2], st[3]
            S.say(f"k = {k}（跳 {2 ** k} 步）：分别到 {nu} 和 {nv}，不同，说明还没到公共祖先，放心跳。")
            S.play(tu.to(x=tree2[nu].g("x", 0), y=tree2[nu].g("y", 0)), tv.to(x=tree2[nv].g("x", 0), y=tree2[nv].g("y", 0)),
                   dur=0.6)
    S.say(f"停在 5 和 6，它们的父亲 {l} 就是 LCA。")
    S.play(tree2[l].to(fill=tint(Y, 0.5), stroke=Y), dur=0.5)

    # ------------------------------------------------------------ 为什么从大到小
    S.section("为什么从大到小试是对的")
    S.say("设 u、v 已在同一深度，它们的 LCA 在上方 d 步。把“跳 t 步后祖先不同”看成 t 的一个性质：")
    S.note("同深度时：跳 t 步后祖先不同 ⇔ t < d（d = 到 LCA 的步数）", color=Y)
    nl = Axes(x=640, y=440, w=900, h=60, xr=(0, 8), yr=(0, 1), ticks=False)
    S.show(nl)
    seg1 = Rect(nl.p(0, 0)[0] + 640 + (nl.p(3, 0)[0] - nl.p(0, 0)[0]) / 2, 440, nl.p(3, 0)[0] - nl.p(0, 0)[0], 40,
                fill=tint(G, 0.5), stroke=G, r=6)
    seg2 = Rect(nl.p(3, 0)[0] + 640 + (nl.p(8, 0)[0] - nl.p(3, 0)[0]) / 2, 440, nl.p(8, 0)[0] - nl.p(3, 0)[0], 40,
                fill=tint(R, 0.4), stroke=R, r=6)
    S.show(seg1, seg2, label(nl.p(1.5, 0)[0] + 640, 380, "t < d：祖先不同", 26, G), label(nl.p(5.5, 0)[0] + 640, 380, "t ≥ d：祖先相同", 26, R))
    S.say("这个性质是单调的：t 小于 d 时一直“不同”，从 d 开始一直“相同”（相遇之后就一起往上走）。")
    S.say("我们要找的是“不同”的最大 t，也就是 d − 1。从高位到低位试每个二进制位，能跳就跳，正是在逐位确定 d − 1 的二进制表示。")
    S.note("从高位到低位贪心 = 逐位确定 d − 1 的二进制", color=G)
    S.say("如果从小到大试，跳了小的以后，大的那一步可能就跳过头了，又没法退回来。所以必须从大到小。", extra=0.5)

    # ------------------------------------------------------------ 应用
    S.section("顺便维护路径上的信息")
    S.say("跳的时候还能顺便带上信息。距离：dist(u, v) = dep[u] + dep[v] − 2·dep[lca]。")
    S.note("dist(u, v) = dep[u] + dep[v] − 2·dep[LCA]")
    S.say("路径最大边权：再存一张表 mx[k][v] = 从 v 往上跳 2^k 步经过的边里最大的边权，同样由两半合并：")
    S.note("mx[k][v] = max( mx[k−1][v], mx[k−1][ up[k−1][v] ] )", color=Y)
    S.say("求 LCA 的过程中，每跳一步，就把对应的 mx 取进答案。凡是能“两半合并”的信息（和、最小值、gcd……）都可以这样带着走。")
    S.note("能两半合并的路径信息，都能跟着倍增一起算", color=G)
    S.say("一个常见用途：次小生成树——对每条非树边，要知道它两端在最小生成树上的路径最大边。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    S.quiz("用本集的树和倍增表，手推 LCA(10, 6)：\n"
           "(1) 第一步，10 要往上跳几步？按二进制怎样跳？\n"
           "(2) 第二步，k = 1 和 k = 0 时分别跳不跳？LCA 是谁？", think=20)
    steps2, l2 = lca_steps(10, 6, dep, up)
    tree3 = Tree(EDGES, 1, x=500, y=560, w=640, h=380, r=24, size=22)
    S.show(tree3)
    t1 = tree3.token(10, CY, 10)
    t2 = tree3.token(6, O, 10)
    S.play(FadeIn(t1), FadeIn(t2), dur=0.3)
    S.say(f"(1) dep[10] = 4，dep[6] = 2，差 2 = 二进制 10，只跳一次 2^1：10 → {up[1][10]}。")
    S.play(t1.to(x=tree3[4].g("x", 0), y=tree3[4].g("y", 0)), dur=0.6)
    S.note("(1) 深度差 2 = 10₂：跳 2^1，10 → 4", color=Y)
    S.say(f"(2) 现在是 4 和 6。k = 1：up[1][4] = {up[1][4]}，up[1][6] = {up[1][6]}，相同，不跳。k = 0：up[0][4] = 2，up[0][6] = 3，不同，跳到 2 和 3。")
    S.play(t1.to(x=tree3[2].g("x", 0), y=tree3[2].g("y", 0)), t2.to(x=tree3[3].g("x", 0), y=tree3[3].g("y", 0)), dur=0.6)
    S.note(f"(2) k=1 不跳，k=0 跳到 2、3；LCA = {l2}", color=Y)
    S.say(f"LCA = 2 的父亲 = {l2}。距离 = 4 + 2 − 0 = 6。")
    S.play(tree3[l2].to(fill=tint(Y, 0.5), stroke=Y), dur=0.5)

    S.recap([
        "倍增表 up[k][v]：跳 2^k 步的祖先，up[k][v] = up[k−1][up[k−1][v]]，O(n log n) 预处理。",
        "跳 k 步：按 k 的二进制一位一位跳。",
        "LCA：先跳到同深度，再从大到小试，祖先不同才一起跳，最后取父亲。",
        "从大到小的正确性：“祖先不同”关于步数单调，贪心就是逐位确定答案的二进制。",
        "路径上可两半合并的信息（最大边、和……）可以跟着倍增一起维护。",
    ], next_title="树上差分：路径修改，子树求和")
