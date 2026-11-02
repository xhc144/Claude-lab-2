"""第 25 集 强连通分量：Tarjan 的 low 在找什么"""

from episodes.common import *

ADJ = {1: [2, 9], 2: [3], 3: [1, 4], 4: [5], 5: [6, 7], 6: [4], 7: [8], 8: [7], 9: [7]}
POS = {1: (-430, -200), 2: (-230, -60), 3: (-470, 60), 4: (-80, 160), 5: (120, 20), 6: (140, 230),
       7: (360, -120), 8: (450, 100), 9: (-160, -240)}
SCC_COL = [CY, O, G, P, K]


def tarjan(adj):
    dfn, low, onst, stack, sccs, events = {}, {}, set(), [], [], []
    t = [0]

    def go(u):
        t[0] += 1
        dfn[u] = low[u] = t[0]
        stack.append(u)
        onst.add(u)
        events.append(("visit", u, dfn[u]))
        for v in adj.get(u, []):
            if v not in dfn:
                events.append(("tree", u, v))
                go(v)
                old = low[u]
                low[u] = min(low[u], low[v])
                events.append(("back_up", u, v, old, low[u]))
            elif v in onst:
                old = low[u]
                low[u] = min(low[u], dfn[v])
                events.append(("onstack", u, v, old, low[u]))
            else:
                events.append(("popped", u, v))
        if low[u] == dfn[u]:
            comp = []
            while True:
                w = stack.pop()
                onst.discard(w)
                comp.append(w)
                if w == u:
                    break
            sccs.append(comp)
            events.append(("scc", u, list(comp)))

    for s in adj:
        if s not in dfn:
            go(s)
    return dfn, low, sccs, events


def build(S):
    S.cover("有向图里，互相可达的点组成强连通分量。Tarjan 算法一次 DFS 就能找出全部分量——它的 low 值到底在找什么？",
            ["有向图的 DFS", "栈"])

    # ------------------------------------------------------------ 问题
    S.section("强连通分量")
    edges = [(u, v) for u in ADJ for v in ADJ[u]]
    g = Graph(POS, edges, x=560, y=470, directed=True, r=28, size=24)
    S.show(g)
    S.say("有向图里，如果 u 能到 v、v 也能到 u，就说它们“强连通”。这是一种等价关系，把点分成若干个强连通分量（SCC）。")
    S.note("强连通：u ⇝ v 且 v ⇝ u；把点分成若干 SCC")
    S.say("这张图有 4 个分量：{1, 2, 3}、{4, 5, 6}、{7, 8}、{9}。对每对点都判断一次可达要 O(n·m)，太慢。")
    dfn, low, sccs, events = tarjan(ADJ)
    for i, comp in enumerate(reversed(sccs)):
        S.play(*[g[v].to(fill=tint(SCC_COL[i], 0.45), stroke=SCC_COL[i]) for v in comp], dur=0.4)
    S.say("Tarjan 算法只做一次 DFS，O(n + m)。关键是理解 DFS 时记录的两个数：dfn 和 low。")
    S.play(*[g[v].to(fill=BG3, stroke=LINE2) for v in POS], dur=0.4)

    # ------------------------------------------------------------ 关键观察
    S.section("每个分量有一个“根”")
    S.say("观察一：一个分量里，DFS 最先访问到的那个点叫这个分量的“根”。分量里的其他点都会出现在根的 DFS 子树里。")
    S.note("分量的根 = 分量中第一个被访问的点；整个分量在根的子树里", color=Y)
    S.say("（因为访问根时，分量里的其他点都还没访问过，而且都能从根沿着分量内部的路走到，DFS 一定会在离开根之前访问它们。）")
    S.say("所以只要能在 DFS 回溯时认出“这个点是某个分量的根”，就能把分量切下来：把它和它子树里还没归属的点打包。")
    S.note("任务：回溯到 u 时，判断 u 是不是某个分量的根")
    S.say("用一个栈记录“已经访问、但还没被分进任何分量”的点。认出根 u 时，栈里 u 及其上面的点，正好就是 u 的分量。")
    S.note("栈：已访问、未归属的点；认出根 u 时弹到 u 为止", color=G)

    # ------------------------------------------------------------ low
    S.section("low 的含义")
    S.say("dfn[u] 是 u 被访问的次序。low[u] 是：从 u 的子树出发，走若干条树边、再走一条非树边，能到达的{y|还在栈里}的点的最小 dfn。")
    S.note("{y|low[u]}：u 的子树经一条非树边能回到的、仍在栈中的点的最小 dfn", color=Y)
    S.say("如果 low[u] < dfn[u]：u 的子树能回到一个更早访问、还在栈里的点 w。w 还在栈里，说明 w 所在分量的根 r 还在当前 DFS 路径上，是 u 的祖先。")
    S.say("于是 r 沿树边能到 u，u 能到 w，w 又能回到 r——u 和 r 在同一个分量。r 比 u 先访问，所以 u 不是根。")
    S.note("low[u] < dfn[u]：能回到更早的未归属点 → 和它同一分量，u 不是根")
    S.say("如果 low[u] = dfn[u]：u 的子树没法回到任何更早的未归属点，再往上走不出去了——u 就是分量的根。")
    S.note("low[u] = dfn[u]：u 是根，弹栈得到一个分量", color=G)
    S.say("为什么非树边必须指向“还在栈里”的点？指向已经弹出的点，说明那个点所在的分量已经封闭，它回不到 u，这条边对 u 所在的分量毫无帮助。")
    S.note("指向已弹出的点：那个分量已封闭，不能用来更新 low", color=R)

    # ------------------------------------------------------------ 推一遍
    S.section("完整推一遍")
    S.wide()
    g2 = Graph(POS, edges, x=600, y=470, directed=True, r=28, size=24)
    S.show(g2)
    side = {3: "l", 6: "r", 8: "r", 4: "d", 2: "r"}
    tg = {v: g2.tag(v, "", side.get(v, "u"), Y, 21, gap=6) for v in POS}
    stk_lab = label(1500, 150, "栈（底 → 顶）", 26, DIM)
    S.show(stk_lab)
    stack_cells = []
    comp_i = 0
    explained = {"onstack": 0, "popped": 0, "scc": 0}
    for ev in events:
        kind = ev[0]
        if kind == "visit":
            _, u, d = ev
            c = Cell(1500, 220 + 64 * len(stack_cells), 160, 54, f"{u}", 26, fill=tint(Y, 0.25), stroke=Y)
            stack_cells.append((u, c))
            S.play(g2[u].to(stroke=Y, sw=4), FadeIn(tg[u]), tg[u].to(text=f"{d}/{d}"), FadeIn(c, dx=20), dur=0.4)
            if u == 1:
                S.say("每个点旁边写 dfn/low。访问一个点：dfn = low = 访问次序，压入栈。")
        elif kind == "tree":
            _, u, v = ev
            S.play(g2.edge(u, v).to(color=Y, w=5), dur=0.25)
        elif kind == "back_up":
            _, u, v, old, new = ev
            if new != old:
                S.play(tg[u].to(text=f"{dfn[u]}/{new}"), dur=0.3)
        elif kind == "onstack":
            _, u, v, old, new = ev
            S.play(g2.edge(u, v).to(color=CY, w=5), dur=0.3)
            if explained["onstack"] < 2:
                S.say(f"边 {u}→{v} 指向还在栈里的 {v}（dfn = {dfn[v]}），low[{u}] = min({old}, {dfn[v]}) = {new}。")
                explained["onstack"] += 1
            S.play(tg[u].to(text=f"{dfn[u]}/{new}"), dur=0.3)
        elif kind == "popped":
            _, u, v = ev
            S.play(g2.edge(u, v).to(color=R, w=5, dash=None), dur=0.3)
            S.say(f"边 {u}→{v}：{v} 已经被弹出、属于一个封闭的分量。不能用 dfn[{v}] = {dfn[v]} 更新——否则 low[{u}] 会变成 {dfn[v]} < {dfn[u]}，{u} 就不会被认作根，错误地和别的分量混在一起。")
            S.play(g2[u].flash(R), dur=0.6)
        elif kind == "scc":
            _, u, comp = ev
            col = SCC_COL[comp_i % len(SCC_COL)]
            comp_i += 1
            if explained["scc"] < 2:
                S.say(f"回溯到 {u}：low[{u}] = dfn[{u}] = {dfn[u]}，{u} 是根。弹栈直到 {u}：分量 {{{', '.join(map(str, sorted(comp)))}}}。")
                explained["scc"] += 1
            popped_cells = []
            for _ in comp:
                w, c = stack_cells.pop()
                popped_cells.append(c)
            S.play(*[g2[w].to(fill=tint(col, 0.5), stroke=col, sw=3) for w in comp], *[c.to(fill=tint(col, 0.5), stroke=col) for c in popped_cells],
                   dur=0.5)
            S.play(FadeOut(*popped_cells), dur=0.4)
    S.say("四个分量全部找出，弹出的顺序是 {7,8}、{4,5,6}、{9}、{1,2,3}。每个点进栈出栈各一次，每条边看一次，O(n + m)。")
    S.say("弹出顺序还有个用处：先弹出的分量在缩点后的图里更靠“下游”。这是下一集的内容。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    S.narrow()
    S.quiz("对下面的有向图从 1 开始做 Tarjan（邻接点按编号从小到大访问）：\n"
           "1→2，1→5，2→3，3→2，3→4，4→5，5→4。\n\n"
           "写出每个点最终的 dfn/low，以及分量被弹出的顺序。", think=22)
    qadj = {1: [2, 5], 2: [3], 3: [2, 4], 4: [5], 5: [4]}
    qpos = {1: (-360, 0), 2: (-120, -150), 3: (-120, 150), 4: (180, 150), 5: (180, -150)}
    qd, ql, qs, qe = tarjan(qadj)
    qg = Graph(qpos, [(u, v) for u in qadj for v in qadj[u]], x=560, y=560, directed=True, r=28, size=24)
    S.show(qg)
    qt = {v: qg.tag(v, f"{qd[v]}/{ql[v]}", "u" if qpos[v][1] < 0 else "d", Y, 22, gap=6, hidden=False) for v in qpos}
    S.say("DFS：1(1) → 2(2) → 3(3)，3→2 指向栈中的 2，low[3] = 2；再 3 → 4(4) → 5(5)，5→4 指向栈中的 4，low[5] = 4。")
    S.say("回到 4：low = dfn = 4，弹出 {4, 5}。回到 3、2：low[2] = 2 = dfn[2]，弹出 {2, 3}。")
    S.say("回到 1：还有边 1→5，但 5 已经弹出，不更新。low[1] = 1，弹出 {1}。")
    for i, comp in enumerate(qs):
        S.play(*[qg[w].to(fill=tint(SCC_COL[i], 0.5), stroke=SCC_COL[i]) for w in comp], dur=0.4)
    S.note("dfn/low：" + "，".join(f"{v}: {qd[v]}/{ql[v]}" for v in sorted(qd)), color=Y)
    S.note("弹出顺序：" + "、".join("{" + ",".join(map(str, sorted(c))) + "}" for c in qs), color=G)

    S.recap([
        "每个强连通分量有一个“根”（最先访问的点），整个分量都在根的 DFS 子树里。",
        "栈里放已访问、未归属的点；回溯时认出根，就把栈弹到根为止，得到一个分量。",
        "low[u]：子树经一条非树边能回到的、仍在栈中的最小 dfn；low[u] = dfn[u] ⇔ u 是根。",
        "指向已弹出点的边不能更新 low：那个分量已经封闭。",
    ], next_title="缩点之后：在 DAG 上做 DP")
