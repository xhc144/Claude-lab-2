"""第 26 集 缩点之后：在 DAG 上做 DP"""

from episodes.common import *
from episodes.e25_scc_tarjan import tarjan, ADJ, POS, SCC_COL

WT = {1: 2, 2: 1, 3: 3, 4: 1, 5: 2, 6: 4, 7: 5, 8: 1, 9: 8}


def condense():
    dfn, low, sccs, _ = tarjan(ADJ)
    comp = {}
    for i, c in enumerate(sccs):
        for v in c:
            comp[v] = i
    cw = [sum(WT[v] for v in c) for c in sccs]
    cedges = set()
    for u in ADJ:
        for v in ADJ[u]:
            if comp[u] != comp[v]:
                cedges.add((comp[u], comp[v]))
    # 弹出顺序 i 越小越“下游”；f[c] = 从 c 出发的最大和，按弹出顺序算
    f = {}
    nxt = {}
    for i in range(len(sccs)):
        best, arg = 0, None
        for a, b in cedges:
            if a == i and f[b] > best:
                best, arg = f[b], b
        f[i] = cw[i] + best
        nxt[i] = arg
    return sccs, comp, cw, sorted(cedges), f, nxt


def build(S):
    S.cover("有向图上每个点有权值，可以重复走点和边，但每个点的权值只算一次。从任意点出发，最多能拿到多少？",
            ["强连通分量（第 25 集）", "DAG 上的 DP 与拓扑序"])

    sccs, comp, cw, cedges, f, nxt = condense()

    # ------------------------------------------------------------ 问题
    S.section("问题：有环的图上取点权")
    edges = [(u, v) for u in ADJ for v in ADJ[u]]
    g = Graph(POS, edges, x=560, y=470, directed=True, r=28, size=24)
    S.show(g)
    wt = {v: g.tag(v, f"{WT[v]}", "u", DIM, 22, gap=6) for v in POS}
    S.play(*[FadeIn(t) for t in wt.values()], dur=0.5)
    S.say("还是上一集的图，每个点有一个权值。可以从任意点出发，沿边随便走（点、边都能重复经过），每个点的权值只算一次。")
    S.note("点权只算一次；可重复走；求最大总和")
    S.say("如果图没有环，就是 DAG 上的最长路：按拓扑序 DP。可现在有环，DP 找不到计算顺序。")
    S.note("有环 → 没有拓扑序，DP 不能直接做", color=R)

    # ------------------------------------------------------------ 缩点
    S.section("缩点：分量里的点可以全拿", keep=[g])
    S.say("关键观察：一旦进入一个强连通分量，就能把分量里的点全部走一遍再出来——它们两两可达。")
    S.note("进入一个 SCC → 可以拿到其中所有点权", color=Y)
    for i, c in enumerate(sccs):
        S.play(*[g[v].to(fill=tint(SCC_COL[i], 0.45), stroke=SCC_COL[i]) for v in c], dur=0.3)
    S.say("所以把每个分量“缩”成一个点，权值是分量内点权之和。分量之间的边保留，分量内部的边去掉。")
    S.note("缩点：每个 SCC → 一个点，权值 = 分量内点权之和")
    cpos = {}
    for i, c in enumerate(sccs):
        xs = [POS[v][0] for v in c]
        ys = [POS[v][1] for v in c]
        cpos[i] = (sum(xs) / len(xs), sum(ys) / len(ys))
    S.play(*[FadeOut(t) for t in wt.values()], dur=0.3)
    S.play(*[g[v].to(x=cpos[comp[v]][0], y=cpos[comp[v]][1]) for v in POS], dur=1.0)
    names = {i: "{" + ",".join(map(str, sorted(c))) + "}" for i, c in enumerate(sccs)}
    cg = Graph(cpos, cedges, x=560, y=470, directed=True, r=48, size=22,
               labels={i: names[i] for i in cpos})
    for i in cpos:
        cg[i].c.tr["fill"].base = tint(SCC_COL[i], 0.45)
        cg[i].c.tr["stroke"].base = SCC_COL[i]
    S.play(FadeOut(g), FadeIn(cg), dur=0.6)
    ct = {i: cg.tag(i, f"权 {cw[i]}", "d", Y, 22, gap=8) for i in cpos}
    S.play(*[FadeIn(t) for t in ct.values()], dur=0.4)
    S.say("缩完以后的图一定没有环。如果分量 A、B 之间有环，A 能到 B、B 也能到 A，它们里的点就全都互相可达，本该是同一个分量。")
    S.note("缩点图是 DAG：分量间若有环，它们本应合并", color=G)

    # ------------------------------------------------------------ DAG DP
    S.section("在 DAG 上 DP", keep=[cg])
    S.say("在 DAG 上：f[c] = 从分量 c 出发能拿到的最大总和 = 权(c) + max(f[后继])。要先算后继，再算自己。")
    S.note("f[c] = 权(c) + max f[后继]（没有后继则为权(c)）", color=Y)
    S.say("顺序从哪来？Tarjan 弹出分量的顺序恰好是“逆拓扑序”：一个分量被弹出时，它能到达的分量都已经先被弹出了。")
    S.note("Tarjan 弹出顺序 = 逆拓扑序：按弹出顺序算 f 即可", color=G)
    ft = {i: cg.tag(i, "", "u", G, 24, gap=8) for i in cpos}
    for i in range(len(sccs)):
        succ = [b for a, b in cedges if a == i]
        S.play(*[cg.edge(i, b).to(color=Y, w=5) for b in succ], cg[i].to(stroke=Y, sw=4), dur=0.4)
        S.play(FadeIn(ft[i]), ft[i].to(text=f"f = {f[i]}"), dur=0.4)
        S.play(*[cg.edge(i, b).to(color=LINE2, w=3) for b in succ], cg[i].to(stroke=SCC_COL[i], sw=2.5), dur=0.2)
        S.wait(0.3)
    start = max(f, key=lambda i: f[i])
    S.say(f"最大值 f = {f[start]}：从 {names[start]} 出发，走到 {names[nxt[start]]}，再到 {names[nxt[nxt[start]]]}。"
          f"比走 {{4,5,6}} 那条路（{cw[start]} + 7 + 6 = 19）多 1。")
    path = [start]
    while nxt[path[-1]] is not None:
        path.append(nxt[path[-1]])
    S.play(*[cg.edge(a, b).to(color=R, w=6) for a, b in zip(path, path[1:])], dur=0.6)
    S.say("整个过程：Tarjan O(n + m)，建缩点图 O(n + m)，DAG 上 DP O(n + m)。")
    S.say("这个套路很通用：有环的图上做 DP，先缩点变成 DAG。只要“在一个分量里可以随便绕”这件事对问题成立。", extra=0.5)
    S.note("通用套路：有环 → 缩点成 DAG → 按拓扑序 DP", color=Y)

    # ------------------------------------------------------------ 应用二：出度为 0
    S.section("应用：被所有点到达的点")
    S.say("另一个经典问题：有多少个点，能被其他所有点到达？（“受欢迎的牛”）")
    S.note("问：多少个点能被所有其他点到达？")
    dpos = {"a": (-420, -120), "b": (-180, 60), "c": (60, -120), "d": (300, 60), "e": (-120, 230)}
    dg = Graph(dpos, [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("e", "b")], x=560, y=470, directed=True, r=32,
               size=24)
    S.show(dg)
    S.say("缩点后看出度为 0 的分量（“汇点”）。DAG 至少有一个汇点：从任意点一直往前走，因为没有环，最终一定停在汇点。")
    tk = dg.token("e", Y)
    S.play(FadeIn(tk), dur=0.3)
    for a, b in (("e", "b"), ("b", "d")):
        S.play(dg.edge(a, b).to(color=Y, w=5), tk.to(x=dg[b].g("x", 0), y=dg[b].g("y", 0)), dur=0.6)
    S.play(dg["d"].to(fill=tint(G, 0.5), stroke=G), dur=0.4)
    S.say("如果汇点只有一个，那么任何点往前走都会停在它那里——它里面的每个点都能被所有点到达，答案是它的大小。")
    S.note("只有一个汇点分量：答案 = 它的大小", color=G)
    S.play(FadeOut(tk), dg.edge("c", "d").to(op=0.0), dg["c"].to(fill=tint(R, 0.5), stroke=R), dur=0.6)
    S.say("如果有两个汇点（比如去掉 c→d，c 也成了汇点），它们互相到不了，任何点都不可能被所有点到达，答案是 0。")
    S.note("两个及以上汇点：答案 = 0", color=R)

    # ------------------------------------------------------------ 手推题
    S.quiz("有向图 6 个点：1→2，2→1，2→3，3→4，4→5，5→3，6→3。\n\n"
           "(1) 有哪几个强连通分量？缩点后的 DAG 长什么样？\n"
           "(2) 有多少个点能被其他所有点到达？", think=20)
    qadj = {1: [2], 2: [1, 3], 3: [4], 4: [5], 5: [3], 6: [3]}
    qd, ql, qs, _ = tarjan(qadj)
    qpos = {1: (-380, -100), 2: (-200, 40), 3: (40, 40), 4: (240, -100), 5: (300, 140), 6: (-120, 220)}
    qg = Graph(qpos, [(u, v) for u in qadj for v in qadj[u]], x=560, y=560, directed=True, r=28, size=24)
    S.show(qg)
    S.say("(1) 1、2 互相可达；3→4→5→3 是一个环；6 单独一个。分量：{1,2}、{3,4,5}、{6}。缩点后：{1,2} → {3,4,5} ← {6}。")
    for i, c in enumerate(qs):
        S.play(*[qg[v].to(fill=tint(SCC_COL[i], 0.5), stroke=SCC_COL[i]) for v in c], dur=0.3)
    S.note("(1) {1,2}、{3,4,5}、{6}；DAG：{1,2} → {3,4,5} ← {6}", color=Y)
    S.say("(2) 出度为 0 的分量只有 {3,4,5}，所以 3、4、5 都能被所有点到达，答案是 3。")
    S.note("(2) 唯一汇点 {3,4,5} → 答案 3", color=G)

    S.recap([
        "强连通分量里的点两两可达，进入就能全部拿到，于是把每个分量缩成一个点。",
        "缩点后的图一定是 DAG：分量之间若有环，它们本应是同一个分量。",
        "Tarjan 的弹出顺序是逆拓扑序，可以直接按它做 DAG 上的 DP。",
        "汇点分量唯一 ⇔ 其中的点能被所有点到达；有环图上的 DP 先缩点。",
    ], next_title="桥、割点与双连通分量：无向图里的 low")
