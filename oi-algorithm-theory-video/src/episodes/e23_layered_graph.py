"""第 23 集 分层图最短路：把额外信息放进结点"""

import heapq

from episodes.common import *

POS = {1: (-420, 0), 2: (-170, -170), 3: (170, -170), 4: (0, 170), 5: (420, 0)}
EDGES = [(1, 2, 4), (2, 3, 4), (3, 5, 4), (1, 4, 10), (4, 5, 1)]
K = 1


def dijkstra_plain():
    adj = {v: [] for v in POS}
    for a, b, w in EDGES:
        adj[a].append((b, w))
        adj[b].append((a, w))
    dist = {1: 0}
    pq = [(0, 1)]
    prev = {}
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist.get(v, 1e9):
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(pq, (d + w, v))
    path = [5]
    while path[-1] != 1:
        path.append(prev[path[-1]])
    return dist, path[::-1]


def dijkstra_layered():
    adj = {}
    for a, b, w in EDGES:
        for u, v in ((a, b), (b, a)):
            for j in range(K + 1):
                adj.setdefault((u, j), []).append(((v, j), w))
                if j < K:
                    adj.setdefault((u, j), []).append(((v, j + 1), 0))
    dist = {(1, 0): 0}
    order = []
    prev = {}
    pq = [(0, (1, 0))]
    done = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        order.append((u, d))
        for v, w in adj.get(u, []):
            if d + w < dist.get(v, 1e9):
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(pq, (d + w, v))
    return dist, order, prev


def build(S):
    S.cover("走 s 到 t 的最短路，但最多可以让 k 条路免费。最短路算法不知道“还剩几次机会”，怎么办？",
            ["Dijkstra 最短路", "DP 的状态（第 2 集）"])

    # ------------------------------------------------------------ 问题
    S.section("问题：k 次免费")
    g = Graph(POS, EDGES, x=640, y=440, r=34, size=28, wsize=26, wcolor=FG)
    S.show(g)
    S.say("5 个城市，边上是过路费。从 1 到 5，最多可以选 k = 1 条路免费通过。最少花多少钱？")
    S.note("从 s 到 t，最多 k 条边免费，求最小花费")
    dist, path = dijkstra_plain()
    S.say(f"先求普通最短路：1→2→3→5，花 {dist[5]}。在它上面免掉一条最贵的边（4），花 8。")
    S.play(*[g.edge(a, b).to(color=CY, w=6) for a, b in zip(path, path[1:])], dur=0.6)
    S.note(f"先求最短路再免最贵的边：{dist[5]} − 4 = 8", color=DIM)
    S.say("但走 1→4→5，把 10 那条免掉，只花 1。有免费机会时，最优路线可能根本不是原来的最短路。")
    S.play(*[g.edge(a, b).to(color=LINE2, w=3) for a, b in zip(path, path[1:])], dur=0.3)
    S.play(g.edge(1, 4).to(color=G, w=6, dash=None), g.edge(4, 5).to(color=Y, w=6), dur=0.6)
    S.note("走 1→4→5，免掉 10：只花 1", color=G)
    S.say("问题出在：最短路算法的“状态”只有“在哪个城市”，不知道“已经用了几次免费”。这又是状态少记了信息。")
    S.note("状态少记了“已经用了几次免费”", color=R)

    # ------------------------------------------------------------ 分层图
    S.section("把次数放进结点：分层图")
    S.say("把状态改成二元组 (城市 v, 已用次数 j)。每个二元组当成新图上的一个点。")
    S.note("{y|新结点 = (v, j)}：在城市 v，已经用了 j 次免费", color=Y)
    S.say("新图有 k + 1 层：第 j 层是“已用 j 次”的所有城市。原来的一条边 (u, v, w) 变成两种边：")
    S.note("层内：(u, j) → (v, j)，花 w（照常付费）")
    S.note("层间：(u, j) → (v, j+1)，花 0（这条边免费）", color=G)
    lpos = {}
    for v, (x, y) in POS.items():
        lpos[(v, 0)] = (x * 0.85, y * 0.55 - 190)
        lpos[(v, 1)] = (x * 0.85 + 60, y * 0.55 + 190)
    ledges = []
    for a, b, w in EDGES:
        for j in range(K + 1):
            ledges.append(((a, j), (b, j), w))
    for a, b, w in EDGES:
        ledges.append(((a, 0), (b, 1), None))
        ledges.append(((b, 0), (a, 1), None))
    lab = {k: str(k[0]) for k in lpos}
    bends = {}
    for a, b, w in EDGES:
        bends[((a, 0), (b, 1))] = 0.18
        bends[((b, 0), (a, 1))] = -0.18
    lg = Graph(lpos, ledges, x=640, y=480, r=28, size=24, wsize=22, labels=lab, directed=True, wcolor=FG, hidden_edges=True,
               bends=bends)
    for a, b, w in EDGES:
        for j in range(K + 1):
            e = lg.edge((a, j), (b, j))
            e.tr["head"].base = 0
    cross = [lg.edge((a, 0), (b, 1)) for a, b, w in EDGES] + [lg.edge((b, 0), (a, 1)) for a, b, w in EDGES]
    for e in cross:
        e.dash = (8, 7)
        e.tr["color"].base = alpha(G, 0.55)
        e.tr["w"].base = 2.5
    S.show(lg)
    l0 = label(70, 190, "第 0 层：一次没用", 24, CY, anchor="lm")
    l1 = label(70, 590, "第 1 层：已用 1 次", 24, O, anchor="lm")
    S.show(l0, l1)
    same = [lg.edge((a, j), (b, j)) for a, b, w in EDGES for j in range(K + 1)]
    S.play(*[FadeIn(e) for e in same], *[FadeIn(lg.etags[((a, j), (b, j))]) for a, b, w in EDGES for j in range(K + 1)],
           dur=0.6)
    S.say("层内的边和原图一样；层间的边（绿色虚线）从上一层指向下一层，费用为 0，表示“用掉一次机会走这条路”。")
    S.play(*[FadeIn(e) for e in cross], dur=0.8, lag=0.03)
    S.say("层间边只往下指：免费次数只增不减，走过去就回不来。")

    # ------------------------------------------------------------ 跑 Dijkstra
    S.section("在分层图上跑 Dijkstra", keep=[lg, l0, l1])
    S.say("起点是 (1, 0)，终点是任意一层的 5：答案 = min_j dist(5, j)。新图的边权都非负，直接跑 Dijkstra。")
    S.note("起点 (s, 0)；答案 = min over j：dist(t, j)", color=Y)
    ld, order, prev = dijkstra_layered()
    dt = {v: lg.tag(v, "", "u", Y, 22, gap=6) for v in lpos}
    for (v, d) in order:
        S.play(lg[v].to(fill=tint(Y, 0.4), stroke=Y), FadeIn(dt[v]), dt[v].to(text=f"{d}"), dur=0.4)
        S.wait(0.15)
    best = min(ld.get((5, j), 1e9) for j in range(K + 1))
    S.say(f"dist(5, 0) = {ld[(5, 0)]}，dist(5, 1) = {ld[(5, 1)]}，答案是 {best}。")
    node = (5, 1) if ld[(5, 1)] <= ld[(5, 0)] else (5, 0)
    pth = [node]
    while pth[-1] in prev:
        pth.append(prev[pth[-1]])
    pth = pth[::-1]
    S.play(*[lg.edge(a, b).to(color=R, w=6) for a, b in zip(pth, pth[1:])], dur=0.6)
    S.say("最短路是 (1,0) → (4,1) → (5,1)：走 1→4 时下到第 1 层（这条免费），4→5 正常付 1。对应原图上“免掉 10”的方案。")
    S.say("为什么对？原图上的每一种“路线 + 选哪些边免费”，都恰好对应新图上的一条路径，花费相同；反过来也一样。所以两边的最小值相等。")
    S.note("一一对应：（路线，免费边集合）↔ 新图上的路径，花费相同", color=G)
    S.say(f"复杂度：点数 n(k+1)，边数 2m(k+1)，Dijkstra O(mk log(nk))。")

    # ------------------------------------------------------------ 一般原则
    S.section("一般原则：状态图")
    S.say("这其实就是 DP：(v, j) 是状态，边是转移。只不过状态之间有环，不能按固定顺序递推，于是用 Dijkstra 按距离从小到大的顺序“填表”。")
    S.note("分层图 = 状态有环的 DP；Dijkstra 提供计算顺序", color=Y)
    S.say("凡是“最短路，但还要记住某些额外信息”的问题——剩余的次数、手里的钥匙、上一步的方向、当前时刻模几……都可以把信息放进结点。")
    S.note("额外信息（次数、钥匙、方向、时间模 p……）→ 放进结点")
    S.say("一个小变式：如果所有边权只有 0 和 1，可以用双端队列：权 0 的边放队首，权 1 的边放队尾，O(n + m)。叫 0-1 BFS。", extra=0.5)
    S.note("边权只有 0/1：0-1 BFS（双端队列），O(n + m)", color=CY)

    # ------------------------------------------------------------ 手推题
    S.quiz("网格迷宫，每步走到相邻格子（上下左右）。迷宫里有 A、B、C 三种门，各有一把对应的钥匙放在某些格子里。"
           "拿到钥匙后才能通过对应的门。求从起点到终点的最少步数。\n\n"
           "(1) 图的结点是什么？一共有几层？\n"
           "(2) 有哪些边？用什么算法？", think=20)
    S.say("(1) 额外信息是“手里有哪些钥匙”，三种钥匙的子集有 2³ = 8 种。结点 = (格子, 钥匙集合)，一共 8 层。")
    S.note("(1) 结点 (格子, 钥匙集合 S)，8 层", color=Y)
    S.say("(2) 在第 S 层里，正常走到相邻格子，步数 +1；如果那格是门，要求 S 里有对应的钥匙。")
    S.note("层内：走到相邻格，+1；门要求对应钥匙在 S 中")
    S.say("走到放钥匙 x 的格子时，从第 S 层转到第 S ∪ {x} 层（不费步数）。所有边权是 0 或 1，用 0-1 BFS。")
    S.note("捡钥匙：(格子, S) → (格子, S ∪ {x})，0 步；0-1 BFS", color=G)
    S.say("这里的“层”不再排成一列，而是 8 个集合之间的转移——但想法一样：把影响未来的信息放进结点。", extra=0.5)

    S.recap([
        "带“额外条件”的最短路，普通算法会因为状态少记信息而出错。",
        "分层图：结点 = (原结点, 额外信息)，层内边照常、层间边表示用掉一次机会。",
        "原问题的方案与新图的路径一一对应、花费相同，所以新图的最短路就是答案。",
        "本质是状态有环的 DP，用 Dijkstra（或 0-1 BFS）确定计算顺序。",
    ], next_title="差分约束：不等式就是最短路的三角形")
