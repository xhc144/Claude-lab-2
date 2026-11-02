"""第 20 集 树上差分：路径修改，子树求和"""

from episodes.common import *

EDGES = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7), (5, 8), (5, 9)]
PATHS = [(8, 4), (9, 6)]


def tree_info():
    par = {1: 0}
    ch = {}
    dep = {1: 0}
    for p, c in EDGES:
        par[c] = p
        ch.setdefault(p, []).append(c)
        dep[c] = dep[p] + 1
    return par, ch, dep


def lca(u, v, par, dep):
    while dep[u] > dep[v]:
        u = par[u]
    while dep[v] > dep[u]:
        v = par[v]
    while u != v:
        u, v = par[u], par[v]
    return u


def path_nodes(u, v, par, dep):
    l = lca(u, v, par, dep)
    a, b = [], []
    while u != l:
        a.append(u)
        u = par[u]
    while v != l:
        b.append(v)
        v = par[v]
    return a + [l] + b[::-1]


def subtree_sums(c, ch, root=1):
    s = {}

    def go(u):
        s[u] = c.get(u, 0) + sum(go(w) for w in ch.get(u, []))
        return s[u]

    go(root)
    return s


def build(S):
    S.cover("对树上的很多条路径“每个点都加 x”，最后问每个点的值。能不能每条路径只改常数个点？",
            ["数组差分与前缀和", "LCA（第 19 集）", "DFS 序（第 18 集）"])

    par, ch, dep = tree_info()

    # ------------------------------------------------------------ 回顾数组差分
    S.section("先看数组：差分 + 前缀和")
    arr = Array([0] * 8, x=640, y=300, cw=96, ch=64, gap=8, size=30)
    dif = Array([0] * 8, x=640, y=480, cw=96, ch=64, gap=8, size=30)
    S.show(arr, dif, label(130, 300, "a", 28, FG, anchor="rm"), label(130, 480, "c", 28, Y, anchor="rm"))
    S.say("数组上，给 [3, 6] 都加 1：只在 c[3] 加 1、c[7] 减 1，最后求前缀和，就还原出每个位置的值。")
    S.play(dif[3].to(text="1", fill=tint(G, 0.4)), dif[7].to(text="−1", fill=tint(R, 0.4)), dur=0.5)
    S.play(*[arr[i].to(text="1" if 3 <= i <= 6 else "0", fill=tint(Y, 0.3) if 3 <= i <= 6 else BG3) for i in range(1, 9)],
           dur=0.6, lag=0.05)
    S.say("关键是：c[i] 的修改会影响“它右边的所有前缀和”。树上也需要一种“汇总”方式，让一个点的修改影响到一整条链。")
    S.note("数组：c 的一个修改 → 影响它之后的所有前缀和")

    # ------------------------------------------------------------ 树上的汇总：子树和
    S.section("树上的“前缀和”：子树和")
    tree = Tree(EDGES, 1, x=460, y=460, w=620, h=460, r=30, size=26)
    S.show(tree)
    S.say("树上对应的汇总方式是{y|子树和}：最终 val[v] = v 子树里所有 c 的和（从叶子往上累加一遍）。")
    S.note("树上：val[v] = Σ_{w 在 v 子树里} c[w]", color=Y)
    S.say("那么在点 w 上加 x，会影响哪些点的子树和？正好是 w 和它的所有祖先——一条从 w 到根的链。")
    S.play(tree[8].to(fill=tint(G, 0.5), stroke=G), dur=0.4)
    S.play(*[tree[v].to(stroke=Y, sw=4) for v in (8, 5, 2, 1)], dur=0.6)
    S.note("c[w] += x → w 到根的整条链都 +x")
    S.say("所以“到根的链”是基本单位，就像数组里的“后缀”。一条路径能不能写成几条到根的链的加加减减？")
    S.play(*[tree[v].to(stroke=LINE2, sw=2.5, fill=BG3) for v in (8, 5, 2, 1)], dur=0.3)

    # ------------------------------------------------------------ 点差分
    S.section("点差分：四个修改点", keep=[tree])
    u, v = PATHS[0]
    l = lca(u, v, par, dep)
    pn = path_nodes(u, v, par, dep)
    S.say(f"路径 {u}–{v}（LCA 是 {l}）上每个点加 1。试试：c[{u}] += 1，c[{v}] += 1。")
    S.play(*[tree[w].to(stroke=Y, sw=4) for w in pn], dur=0.5)
    tags = {w: tree.tag(w, "", "r", Y, 22) for w in par}
    c = {u: 1, v: 1}
    S.play(FadeIn(tags[u]), FadeIn(tags[v]), tags[u].to(text="c=+1"), tags[v].to(text="c=+1"), dur=0.4)
    s = subtree_sums(c, ch)
    vt = {w: tree.tag(w, "", "d", CY, 22) for w in par}
    S.play(*[FadeIn(vt[w]) for w in par], *[vt[w].to(text=f"{s[w]}") for w in par], dur=0.6)
    S.say(f"这时候 {u}、{v} 往上的链各被加了一次：路径上 LCA 以下的点值为 1，可 LCA {l} 被加了 2 次，LCA 以上的点也被加了 2 次。")
    S.play(tree[l].flash(R), tree[1].flash(R), dur=0.8)
    S.say(f"所以在 LCA 处减 1：c[{l}] −= 1。这样 LCA 变成 1，但 LCA 的父亲以上还剩 1，再在 LCA 的父亲处减 1：c[{par[l]}] −= 1。")
    c[l] = c.get(l, 0) - 1
    c[par[l]] = c.get(par[l], 0) - 1
    S.play(FadeIn(tags[l]), FadeIn(tags[par[l]]), tags[l].to(text="c=−1", color=R), tags[par[l]].to(text="c=−1", color=R),
           dur=0.5)
    s = subtree_sums(c, ch)
    S.play(*[vt[w].to(text=f"{s[w]}") for w in par], dur=0.6)
    S.note("点差分：c[u] += x，c[v] += x，c[lca] −= x，c[fa(lca)] −= x", color=Y)
    S.say("检查：路径上的点（包括 LCA）值都是 1；其余的点都是 0。四个修改点就表示了一整条路径。")
    S.play(*[tree[w].to(fill=tint(Y, 0.35)) for w in pn], dur=0.5)
    S.say("为什么对？路径上 u 一侧的点，子树里只含 u（+1）；LCA 的子树含 u、v、LCA（+1 +1 −1）；更上面的点四个都含（抵消为 0）；其他点一个都不含。")
    S.note("按“子树里包含哪几个修改点”分类验证", color=G)

    # 第二条路径
    u2, v2 = PATHS[1]
    l2 = lca(u2, v2, par, dep)
    S.say(f"再加一条路径 {u2}–{v2}（LCA 是根 {l2}，根没有父亲，第四个修改点省略）。多条路径的修改直接叠加，最后统一做一遍子树和。")
    for w, d in ((u2, 1), (v2, 1), (l2, -1)):
        c[w] = c.get(w, 0) + d
    s = subtree_sums(c, ch)
    S.play(*[FadeIn(tags[w]) for w in c], *[tags[w].to(text=f"c={'+' if c[w] > 0 else ''}{c[w]}" if c[w] else "c=0",
                                                         color=Y if c[w] >= 0 else R) for w in c], dur=0.5)
    S.play(*[vt[w].to(text=f"{s[w]}") for w in par], *[tree[w].to(fill=tint(Y, 0.15 + 0.2 * s[w])) for w in par], dur=0.6)
    S.say(f"结果：点 5、2 被两条路径经过，值为 2；其余在路径上的点为 1。每条路径 O(1) 次修改加一次 LCA，最后 O(n) 汇总。")
    S.note("m 条路径：O(m log n) 求 LCA + O(n) 求一次子树和")

    # ------------------------------------------------------------ 边差分
    S.section("边差分：三个修改点")
    tree2 = Tree(EDGES, 1, x=460, y=460, w=620, h=460, r=30, size=26)
    S.show(tree2)
    S.say("如果要统计的是{y|边}被经过的次数：把边 (w, 父亲) 的值存在下面的点 w 上，边的值 = w 的子树和。")
    S.note("边 (w, fa(w)) 的值存在 w 上")
    u, v = PATHS[0]
    l = lca(u, v, par, dep)
    pe = [(par[w], w) for w in path_nodes(u, v, par, dep) if w != l]
    S.play(*[tree2.edge(a, b).to(color=Y, w=6) for a, b in pe], dur=0.5)
    S.say(f"路径 {u}–{v} 的边都在 LCA 下方。c[{u}] += 1、c[{v}] += 1 之后，LCA 和它上面的点都被加了 2；LCA 自己代表的是它上方那条边，不在路径上。")
    S.say(f"所以只要 c[{l}] −= 2 就够了：三个修改点。")
    S.note("边差分：c[u] += x，c[v] += x，c[lca] −= 2x", color=Y)
    S.say("经典用法：运输计划——二分答案 T，所有长度超过 T 的路径都必须经过同一条被改造的边。用边差分数出每条边被多少条“超长路径”经过即可。")
    S.note("例：运输计划 = 二分 + 边差分统计", color=DIM)

    # ------------------------------------------------------------ 在线版本
    S.section("如果修改和询问交错")
    S.say("上面的做法要求先做完所有修改，最后一次性求子树和（离线）。如果修改和询问交错出现呢？")
    tin, tout, order = {}, {}, []

    def go(w):
        tin[w] = len(order) + 1
        order.append(w)
        for x in ch.get(w, []):
            go(x)
        tout[w] = len(order)

    go(1)
    tr4 = Tree(EDGES, 1, x=420, y=380, w=560, h=330, r=26, size=24)
    seq = Array([str(w) for w in order], x=640, y=720, cw=90, ch=58, gap=8, size=26)
    S.show(tr4, seq, label(130, 720, "DFS 序", 22, DIM, anchor="rm"))
    S.say("“c[w] 加 x”是单点修改，“val[v] = v 子树里 c 的和”是子树求和——用上一集的 DFS 序，正好是树状数组的单点加、区间和。")
    S.play(tr4[8].to(fill=tint(G, 0.5), stroke=G), seq[tin[8]].to(fill=tint(G, 0.5)), dur=0.5)
    sp = seq.span(tin[2], tout[2], "val[2] = 这一段的和", Y, "above")
    S.play(FadeIn(sp), *[tr4[w].to(stroke=Y, sw=4) for w in tr4.subtree(2)], dur=0.6)
    S.note("在线：c 的单点加 + 子树求和 → DFS 序上的树状数组", color=G)
    S.say("于是“路径加、单点查”可以做到每次 O(log n)。反过来，“单点加、路径查”就是上一集的“进加出减”。差分就是在这两种视角之间转换。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("本集的树上，有三条路径：4–9、7–8、6–7。用边差分统计每条边被经过的次数。\n\n"
           "(1) 写出每条路径在 c 上的三个修改。\n"
           "(2) 哪条边被经过的次数最多？", think=20)
    qp = [(4, 9), (7, 8), (6, 7)]
    cc = {}
    lines = []
    for a, b in qp:
        lab_ = lca(a, b, par, dep)
        cc[a] = cc.get(a, 0) + 1
        cc[b] = cc.get(b, 0) + 1
        cc[lab_] = cc.get(lab_, 0) - 2
        lines.append(f"{a}–{b}：LCA = {lab_}；c[{a}] +1，c[{b}] +1，c[{lab_}] −2")
    S.say("(1) 先求每条路径的 LCA，再各改三个点：")
    for t in lines:
        S.note(t)
    s = subtree_sums(cc, ch)
    tree3 = Tree(EDGES, 1, x=560, y=560, w=600, h=360, r=26, size=24)
    S.show(tree3)
    for w in par:
        if w != 1:
            tree3.etag(par[w], w, str(s[w]), color=Y, size=24, hidden=False)
    best = max((w for w in par if w != 1), key=lambda w: s[w])
    S.say(f"(2) 求子树和后，每条边的次数标在边上。最多的是边 ({par[best]}, {best})，被经过 {s[best]} 次。")
    S.play(tree3.edge(par[best], best).to(color=Y, w=7), dur=0.5)
    S.note(f"(2) 边 ({par[best]}, {best}) 最多：{s[best]} 次", color=Y)

    S.recap([
        "树上的“前缀和”是子树和：在 w 上加 x，影响 w 到根的整条链。",
        "点差分：c[u] += x，c[v] += x，c[lca] −= x，c[fa(lca)] −= x；按“子树里含哪些修改点”分类即可验证。",
        "边差分：边值存在下面的点上，c[u] += x，c[v] += x，c[lca] −= 2x。",
        "离线一次子树和 O(n)；在线时用 DFS 序 + 树状数组，单点加、子树和。",
    ], next_title="树链剖分（上）：重链为什么只有 log 条")
