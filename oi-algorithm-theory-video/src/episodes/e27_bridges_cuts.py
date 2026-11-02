"""第 27 集 桥、割点与双连通分量：无向图里的 low"""

from episodes.common import *

EDGES = [(1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 6), (6, 4), (4, 7), (7, 8), (8, 4), (8, 9)]
POS = {1: (-480, -120), 2: (-480, 130), 3: (-260, 0), 4: (0, 0), 5: (120, -210), 6: (260, -60),
       7: (120, 210), 8: (300, 110), 9: (500, 200)}


def analyze(edges, root=1):
    adj = {}
    for i, (a, b) in enumerate(edges):
        adj.setdefault(a, []).append((b, i))
        adj.setdefault(b, []).append((a, i))
    for v in adj:
        adj[v].sort()
    dfn, low, par_edge, children = {}, {}, {}, {}
    tree_edges, back_edges = [], []
    order = []
    t = [0]

    def go(u, pe):
        t[0] += 1
        dfn[u] = low[u] = t[0]
        order.append(u)
        children[u] = []
        for v, i in adj[u]:
            if i == pe:
                continue
            if v not in dfn:
                tree_edges.append((u, v))
                children[u].append(v)
                go(v, i)
                low[u] = min(low[u], low[v])
            else:
                if dfn[v] < dfn[u]:
                    back_edges.append((u, v))
                low[u] = min(low[u], dfn[v])

    go(root, -1)
    par = {v: u for u, ch in children.items() for v in ch}
    bridges = [(u, v) for u, v in tree_edges if low[v] > dfn[u]]
    cuts = []
    for u in dfn:
        if u == root:
            if len(children[u]) >= 2:
                cuts.append(u)
        elif any(low[v] >= dfn[u] for v in children[u]):
            cuts.append(u)
    return dfn, low, tree_edges, back_edges, bridges, sorted(cuts), order, par


def build(S):
    S.cover("无向连通图里，删掉哪条边、哪个点会让图断开？一次 DFS 怎样把它们全找出来？",
            ["DFS 树", "Tarjan 的 dfn 与 low（第 25 集）"])

    dfn, low, tree_e, back_e, bridges, cuts, order, par = analyze(EDGES)

    # ------------------------------------------------------------ 定义
    S.section("桥与割点")
    g = Graph(POS, EDGES, x=600, y=470, r=28, size=24)
    S.show(g)
    S.say("无向连通图里：删掉后图会断开的边叫{y|桥}，删掉后图会断开的点叫{y|割点}。")
    S.note("桥：删掉这条边，图不连通")
    S.note("割点：删掉这个点（及其边），图不连通")
    S.play(*[g.edge(a, b).to(color=R, w=6) for a, b in [(3, 4), (8, 9)]], dur=0.5)
    S.play(*[g[v].to(fill=tint(O, 0.5), stroke=O) for v in (3, 4, 8)], dur=0.5)
    S.say("这张图里，红色的边 3–4、8–9 是桥；橙色的点 3、4、8 是割点。注意 4 是割点，但它连着的环没有桥——割点和桥不是一回事。")
    S.say("网络的“薄弱环节”就是这些东西。逐个删掉试是 O(n·m)，用一次 DFS 可以做到 O(n + m)。")
    S.play(*[g.edge(a, b).to(color=LINE2, w=3) for a, b in [(3, 4), (8, 9)]], *[g[v].to(fill=BG3, stroke=LINE2) for v in (3, 4, 8)],
           dur=0.4)

    # ------------------------------------------------------------ 无向 DFS
    S.section("无向图的 DFS：只有树边和返祖边")
    S.say("在无向图上做 DFS，每条非树边都连接一个点和它的祖先（返祖边）。不会出现有向图里那种连到别的分支的“横叉边”。")
    S.note("无向 DFS：非树边都是返祖边（没有横叉边）", color=Y)
    S.say("原因：如果 u 有一个已访问的邻居 v 在另一个分支里，那么当初访问 v 时，DFS 就会顺着这条边先访问 u，u 会成为 v 的后代。")
    g2 = Graph(POS, EDGES, x=600, y=470, r=28, size=24)
    S.clear(dur=0.3)
    S.show(g2)
    tg = {v: g2.tag(v, "", "u" if POS[v][1] <= 0 else "d", Y, 21, gap=6) for v in POS}
    S.say("从 1 开始 DFS（邻点按编号从小到大），树边加粗，返祖边画成虚线。每个点旁边写 dfn/low。")
    for v in order:
        pe = [(a, b) for a, b in tree_e if b == v]
        anims = [g2[v].to(stroke=Y, sw=4), FadeIn(tg[v]), tg[v].to(text=f"{dfn[v]}")]
        if pe:
            a, b = pe[0]
            anims.append(g2.edge(a, b).to(color=Y, w=6))
        S.play(*anims, dur=0.35)
    for a, b in back_e:
        e = g2.edge(a, b)
        e.dash = (9, 7)
        S.play(e.to(color=CY, w=4), dur=0.3)
    S.note("low[u]：u 的子树经一条返祖边能到的最小 dfn（不能走回父亲的那条树边）")
    S.say("low 的定义和有向图类似：u 的子树里的点，经过一条返祖边，能到达的最小 dfn。注意不能沿着来时的树边直接回到父亲。")
    S.play(*[tg[v].to(text=f"{dfn[v]}/{low[v]}") for v in order], dur=0.8, lag=0.05)

    # ------------------------------------------------------------ 判定
    S.section("判定：一个是 >，一个是 ≥", keep=[g2])
    S.say("看一条树边 u–v（v 是儿子）。如果 v 的子树能通过返祖边回到 u 或更高的地方，就有一个环经过这条边，它不是桥。")
    S.note("桥：树边 (u, v) 是桥 ⇔ low[v] > dfn[u]", color=Y)
    S.say("所以 (u, v) 是桥，当且仅当 low[v] > dfn[u]：v 的子树连 u 本身都回不到。")
    for a, b in bridges:
        S.play(g2.edge(a, b).to(color=R, w=7), dur=0.5)
        S.say(f"例：树边 {a}–{b}，low[{b}] = {low[b]} > dfn[{a}] = {dfn[a]}，是桥。")
    S.say("割点看的是点 u：删掉 u 后，某个儿子 v 的子树会不会和上面断开？只要 v 的子树最多只能回到 u 本身，删掉 u 它就断了。")
    S.note("割点（非根）：存在儿子 v，low[v] ≥ dfn[u]", color=Y)
    for u in cuts:
        if u == 1:
            continue
        v = next(v for v in par if par[v] == u and low[v] >= dfn[u])
        S.play(g2[u].to(fill=tint(O, 0.55), stroke=O), dur=0.4)
        S.say(f"例：点 {u} 的儿子 {v}：low[{v}] = {low[v]} ≥ dfn[{u}] = {dfn[u]}，删掉 {u} 后 {v} 的子树断开，{u} 是割点。")
    S.say("为什么一个是 >、一个是 ≥？回到 u 本身：对桥来说说明有环绕过这条边，边可以删；对割点来说 u 被删掉了，回到 u 没有用。")
    S.note("区别：能回到 u 本身 → 边不是桥；但点 u 删掉后回到它没用", color=G)

    # ------------------------------------------------------------ 根与重边
    S.section("两个细节：根和重边")
    S.say("根没有祖先，任何儿子都满足 low[v] ≥ dfn[根]，不能用上面的条件。根是割点 ⇔ 它在 DFS 树里有至少两个儿子。")
    S.note("根：DFS 树里至少两个儿子才是割点", color=Y)
    tpos = {"r": (0, -140), "a": (-180, 80), "b": (180, 80)}
    t1 = Graph(tpos, [("r", "a"), ("r", "b")], x=400, y=520, r=28, size=24)
    t2 = Graph(tpos, [("r", "a"), ("a", "b"), ("b", "r")], x=900, y=520, r=28, size=24)
    S.show(t1, t2, label(400, 330, "根有两个儿子：割点", 24, O), label(900, 330, "根只有一个儿子：不是", 24, G))
    S.play(t1["r"].to(fill=tint(O, 0.5), stroke=O), dur=0.4)
    S.say("另一个细节：两点之间可能有两条边（重边）。“不能走回父亲”要按{y|边的编号}判断，而不是按“邻居是不是父亲”判断——走另一条重边回到父亲是合法的，那时它们不是桥。")
    S.note("重边：按边编号排除来时那条边，不要按父结点排除", color=R)
    S.play(FadeOut(t1, t2), dur=0.3)

    # ------------------------------------------------------------ 双连通分量
    S.section("两种双连通分量")
    g3 = Graph(POS, EDGES, x=600, y=470, r=28, size=24)
    S.show(g3)
    S.say("把所有桥删掉，剩下的每个连通块叫“边双连通分量”：块内任意两点之间至少有两条不共享边的路径。")
    S.note("边双：删掉所有桥后的连通块")
    blocks_e = [[1, 2, 3], [4, 5, 6, 7, 8], [9]]
    for i, b in enumerate(blocks_e):
        S.play(*[g3[v].to(fill=tint([CY, G, P][i], 0.5), stroke=[CY, G, P][i]) for v in b], dur=0.3)
    S.play(*[g3.edge(a, b).to(op=0.15) for a, b in bridges], dur=0.4)
    S.say("点双连通分量（块）则以割点为界：{1,2,3}、{3,4}、{4,5,6}、{4,7,8}、{8,9}。割点（黄色）同时属于好几个块，比如 4 属于 {3,4}、{4,5,6}、{4,7,8}。")
    S.note("点双：以割点为界；一个割点可属于多个点双", color=Y)
    S.play(*[g3[v].to(fill=tint(G, 0.5), stroke=G) for v in (5, 6)], *[g3[v].to(fill=tint(O, 0.5), stroke=O) for v in (7, 8)],
           *[g3[v].to(fill=tint(Y, 0.6), stroke=Y) for v in (3, 4, 8)], g3.edge(3, 4).to(op=1.0), g3.edge(8, 9).to(op=1.0),
           dur=0.6)
    S.say("把每个点双缩成一个点，和割点交替连起来，会得到一棵树，叫“圆方树 / 块割树”，是把一般图问题转成树问题的常用工具。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    S.quiz("无向图：1–2，2–3，3–1，2–4，4–5，5–6，6–4。从 1 开始 DFS（邻点按编号从小到大）。\n\n"
           "(1) 写出每个点的 dfn/low。\n"
           "(2) 哪些边是桥？哪些点是割点？1 为什么不是割点？", think=20)
    qe = [(1, 2), (2, 3), (3, 1), (2, 4), (4, 5), (5, 6), (6, 4)]
    qd, ql, qt, qb, qbr, qc, qo, qp = analyze(qe)
    qpos = {1: (-380, -120), 2: (-200, 40), 3: (-420, 160), 4: (40, 40), 5: (240, -110), 6: (260, 170)}
    qg = Graph(qpos, qe, x=560, y=560, r=28, size=24)
    S.show(qg)
    qtg = {v: qg.tag(v, f"{qd[v]}/{ql[v]}", "u" if qpos[v][1] <= 40 else "d", Y, 21, gap=6, hidden=False) for v in qpos}
    S.say("(1) 1(1) → 2(2) → 3(3)，3–1 是返祖边，low[3] = 1；回到 2，low[2] = 1。2 → 4(4) → 5(5) → 6(6)，6–4 返祖边，low[6] = low[5] = low[4] = 4。")
    S.note("(1) dfn/low：" + "，".join(f"{v}: {qd[v]}/{ql[v]}" for v in sorted(qd)), color=Y)
    S.say(f"(2) 树边 2–4：low[4] = 4 > dfn[2] = 2，是桥。点 2：儿子 4 满足 low[4] = 4 ≥ dfn[2]，是割点；点 4：儿子 5 满足 low[5] = 4 ≥ dfn[4] = 4，是割点。")
    for a, b in qbr:
        S.play(qg.edge(a, b).to(color=R, w=7), dur=0.4)
    S.play(*[qg[v].to(fill=tint(O, 0.55), stroke=O) for v in qc], dur=0.4)
    S.note(f"(2) 桥：" + "、".join(f"{a}–{b}" for a, b in qbr) + "；割点：" + "、".join(map(str, qc)), color=G)
    S.say("1 是根，在 DFS 树里只有一个儿子 2（3 是经 2 访问到的），所以不是割点——删掉 1，2 和 3 仍然连着。")

    S.recap([
        "无向图的 DFS 只有树边和返祖边；low[u] 是子树经一条返祖边能回到的最小 dfn。",
        "树边 (u, v) 是桥 ⇔ low[v] > dfn[u]；非根点 u 是割点 ⇔ 有儿子 v 使 low[v] ≥ dfn[u]。",
        "> 与 ≥ 的区别：能回到 u 本身说明边在环上，但对删掉的点 u 没有帮助。",
        "根要单独判断（至少两个儿子）；重边按边编号排除父边。边双以桥为界，点双以割点为界。",
    ], next_title="二分图匹配：增广路与反悔")
