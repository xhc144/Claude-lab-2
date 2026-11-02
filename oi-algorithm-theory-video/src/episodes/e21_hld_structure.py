"""第 21 集 树链剖分（上）：重链为什么只有 log 条"""

from episodes.common import *

EDGES = [(1, 2), (1, 3), (1, 4), (2, 5), (2, 6), (3, 7), (4, 8), (4, 9), (4, 10), (8, 11), (8, 12), (9, 13), (11, 14)]
CHAIN_COLORS = [Y, CY, G, O, P, K, B, R]


def hld(edges, root=1):
    ch = {}
    par = {root: 0}
    for p, c in edges:
        ch.setdefault(p, []).append(c)
        par[c] = p
    size, heavy, dep = {}, {}, {root: 0}
    order = [root]
    for u in order:
        for c in ch.get(u, []):
            dep[c] = dep[u] + 1
            order.append(c)
    for u in reversed(order):
        size[u] = 1 + sum(size[c] for c in ch.get(u, []))
        heavy[u] = max(ch.get(u, []), key=lambda c: (size[c], -c)) if ch.get(u) else None
    top, dfn, seq = {}, {}, []

    def go(u, t):
        top[u] = t
        dfn[u] = len(seq) + 1
        seq.append(u)
        if heavy[u]:
            go(heavy[u], t)
        for c in ch.get(u, []):
            if c != heavy[u]:
                go(c, c)

    go(root, root)
    return dict(ch=ch, par=par, size=size, heavy=heavy, dep=dep, top=top, dfn=dfn, seq=seq)


def build(S):
    S.cover("路径修改、路径查询要在线完成。能不能把树拆成几条“链”，让任意一条路径只经过 O(log n) 条链？",
            ["DFS 序（第 18 集）", "线段树（第 14、15 集）", "子树大小 size"])

    H = hld(EDGES)

    # ------------------------------------------------------------ 动机
    S.section("把路径变成几段区间")
    tree = Tree(EDGES, 1, x=460, y=470, w=760, h=500, r=26, size=22)
    S.show(tree)
    S.say("上一集的树上差分只能离线。现在要求：路径加 x、路径求和，随时交替出现，每次都要快。")
    S.note("目标：在线的路径修改 / 路径查询")
    S.say("线段树擅长的是数组上的区间。如果能把树拆成若干条“链”，每条链在某个数组里连续，那么一条路径 = 几段区间。")
    S.note("想法：拆成链，每条链在数组里连续 → 路径 = 几段区间", color=Y)
    S.say("关键是路径经过的链要少。怎么拆，才能保证任意路径只经过 O(log n) 条链？")

    # ------------------------------------------------------------ 重儿子
    S.section("重儿子与轻边", keep=[tree])
    S.say("先算出每个点的子树大小 size。每个点选{y|子树最大}的那个儿子作为“重儿子”，连向它的边是重边，其余是轻边。")
    S.note("重儿子 = size 最大的儿子；连向它的是重边，其余轻边", color=Y)
    st = {v: tree.tag(v, f"{H['size'][v]}", "r", DIM, 20) for v in H["size"]}
    S.play(*[FadeIn(t) for t in st.values()], dur=0.6)
    heavy_edges = [(u, H["heavy"][u]) for u in H["heavy"] if H["heavy"][u]]
    S.play(*[tree.edge(a, b).to(color=Y, w=7) for a, b in heavy_edges], dur=0.8, lag=0.05)
    S.say("把重边连起来，树就被分成了若干条“重链”：每条重链从某个点（链顶）一直沿重儿子走到叶子。")
    S.note("重链：沿重边连成的链；每个点恰好属于一条重链")
    chains = {}
    for v, t in H["top"].items():
        chains.setdefault(t, []).append(v)
    cid = {t: i for i, t in enumerate(sorted(chains, key=lambda t: H["dfn"][t]))}
    S.play(*[tree[v].to(fill=tint(CHAIN_COLORS[cid[H['top'][v]] % len(CHAIN_COLORS)], 0.45),
                        stroke=CHAIN_COLORS[cid[H['top'][v]] % len(CHAIN_COLORS)]) for v in H["top"]], dur=0.8)
    S.say(f"这棵树被分成 {len(chains)} 条重链（同色的点在同一条链上，单独一个点也算一条链）。")

    # ------------------------------------------------------------ 关键引理
    S.section("走一条轻边，子树至少翻倍", keep=[tree])
    S.say("关键引理：如果 (u, v) 是轻边（v 是 u 的轻儿子），那么 size(v) ≤ size(u) / 2。")
    S.note("引理：轻边 (u, v)：size(v) ≤ size(u) / 2", color=Y)
    S.say("证明：u 的重儿子 h 的子树不比 v 小，size(h) ≥ size(v)。而 size(u) ≥ 1 + size(v) + size(h) > 2 × size(v)。")
    S.note("size(u) ≥ 1 + size(v) + size(h) ≥ 1 + 2·size(v)")
    S.say("所以从任意一个点往根走，每经过一条轻边，所在子树的大小至少翻一倍。子树大小不超过 n，最多翻倍 log₂ n 次。")
    S.note("到根的路径上轻边 ≤ log₂ n 条 → 经过的重链 ≤ log₂ n + 1 条", color=G)
    leaf = 6
    pth = tree.path_up(leaf, 1)
    S.play(*[tree.edge(pth[i + 1], pth[i]).to(color=R if H["heavy"][pth[i + 1]] != pth[i] else Y,
                                              w=9 if H["heavy"][pth[i + 1]] != pth[i] else 7) for i in range(len(pth) - 1)],
           dur=0.8)
    light = [(pth[i + 1], pth[i]) for i in range(len(pth) - 1) if H["heavy"][pth[i + 1]] != pth[i]]
    sizes = " → ".join(str(H["size"][v]) for v in pth)
    S.say(f"例：从 {leaf} 走到根，子树大小依次是 {sizes}。经过的轻边（红色）有 {len(light)} 条，每条都让大小至少翻倍。")
    S.say("任意两点之间的路径 = 两段“到 LCA 的向上路径”，所以也只经过 O(log n) 条重链。")

    # ------------------------------------------------------------ 链在数组里连续
    S.section("重儿子优先的 DFS 序", keep=[tree])
    S.say("还要让每条重链在数组里连续：做 DFS 时{y|先走重儿子}，再走轻儿子。")
    S.note("DFS 先走重儿子 → 每条重链在 DFS 序里连续", color=Y)
    S.play(tree.to(y=360, sc=0.8), dur=0.6)
    seq = Array([str(v) for v in H["seq"]], x=640, y=760, cw=76, ch=60, gap=6, size=26)
    S.show(seq, label(640, 690, "按 dfn 排成一排（同色 = 同一条重链）", 22, DIM))
    S.play(*[seq[H["dfn"][v]].to(fill=tint(CHAIN_COLORS[cid[H['top'][v]] % len(CHAIN_COLORS)], 0.45)) for v in H["seq"]],
           dur=0.8, lag=0.03)
    S.say("从链顶出发，DFS 会沿着重儿子一路走到底，中间不会岔出去，所以同一条链的点在数组里挨在一起，而且链顶在最前面。")
    S.say("同时它仍然是 DFS 序：每棵子树依旧是一段连续区间 [dfn[u], dfn[u] + size(u) − 1]。")
    S.note("子树仍是区间：[dfn[u], dfn[u] + size(u) − 1]")
    S.note("记录：fa、dep、size、重儿子、top（链顶）、dfn", color=CY)

    # ------------------------------------------------------------ 反例：随便选
    S.section("反例：不按大小选")
    S.say("如果重儿子不是按子树大小选，而是随便选一个（比如总选第一个儿子）呢？")
    spine = [(i, i + 1) for i in range(1, 6)]
    leaves = [(i, 10 + i) for i in range(1, 6)]
    edges2 = []
    for i in range(1, 6):
        edges2.append((i, 10 + i))
        edges2.append((i, i + 1))
    t2 = Tree(edges2, 1, x=560, y=470, w=700, h=520, r=24, size=20)
    S.show(t2)
    S.say("这棵“梳子”树：一条长长的主干，每个点还挂着一片叶子。如果每次都把叶子当成“重儿子”，主干上的边全是轻边。")
    S.play(*[t2.edge(i, 10 + i).to(color=Y, w=7) for i in range(1, 6)], dur=0.6)
    S.play(*[t2.edge(i, i + 1).to(color=R, w=7) for i in range(1, 6)], dur=0.6)
    S.say("从最深的点往上走，每一步都换一条链，经过 O(n) 条链，复杂度就退化了。按 size 选重儿子，主干就是一条链。")
    S.note("随便选重儿子：链的条数可能是 O(n) ✗", color=R)
    S.play(*[t2.edge(i, i + 1).to(color=Y, w=7) for i in range(1, 6)], *[t2.edge(i, 10 + i).to(color=LINE2, w=3) for i in range(1, 6)],
           dur=0.6)
    S.say("“选最大的儿子”保证了每条轻边都通向“不到一半”的子树，这是 log 的来源。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("一棵满二叉树，共 15 个点（4 层）。按本集的方法剖分（大小相同时选左儿子）。\n\n"
           "(1) 从某个叶子走到根，最多经过几条轻边？\n"
           "(2) 一共有多少条重链？一般地，重链的条数和什么有关？", think=20)
    fb = [(i, 2 * i) for i in range(1, 8)] + [(i, 2 * i + 1) for i in range(1, 8)]
    fb.sort(key=lambda e: (e[0], e[1]))
    H2 = hld(fb)
    t3 = Tree(fb, 1, x=640, y=560, w=900, h=330, r=22, size=18)
    S.show(t3)
    S.play(*[t3.edge(u, H2["heavy"][u]).to(color=Y, w=6) for u in H2["heavy"] if H2["heavy"][u]], dur=0.6)
    S.say("(1) 右儿子都是轻儿子。叶子 15 到根：15→7→3→1，三步全是轻边，最多 3 条（= log₂ 16 − 1）。")
    S.play(*[t3.edge(a, b).to(color=R, w=7) for a, b in [(7, 15), (3, 7), (1, 3)]], dur=0.6)
    S.note("(1) 最多 3 条轻边（叶子 15 → 根）", color=Y)
    nchains = len(set(H2["top"].values()))
    S.say(f"(2) 每条重链都在一个叶子处结束，每个叶子也恰好是一条链的末端，所以重链条数 = 叶子数 = {nchains}。")
    S.note(f"(2) 重链条数 = 叶子数 = {nchains}", color=Y)

    S.recap([
        "重儿子 = 子树最大的儿子；重边连成重链，每条链从链顶沿重儿子走到叶子。",
        "轻边 (u, v)：size(v) ≤ size(u)/2，所以任何点到根只经过 O(log n) 条轻边、O(log n) 条重链。",
        "DFS 先走重儿子：每条重链在 DFS 序里连续，子树也仍然连续。",
        "重儿子必须按大小选，否则链的条数可能退化成 O(n)。",
    ], next_title="树链剖分（下）：路径变成几段区间")
