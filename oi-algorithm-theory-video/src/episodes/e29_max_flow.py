"""第 29 集 最大流：残量网络与反向边"""

from collections import deque

from episodes.common import *

DIAMOND = {"pos": {"s": (-360, 0), "a": (0, -170), "b": (0, 170), "t": (360, 0)},
           "cap": [("s", "a", 1), ("s", "b", 1), ("a", "b", 1), ("a", "t", 1), ("b", "t", 1)]}
NET = {"pos": {"s": (-450, 0), "a": (-150, -190), "c": (-150, 190), "b": (150, -190), "d": (150, 190), "t": (450, 0)},
       "cap": [("s", "a", 10), ("s", "c", 10), ("a", "b", 4), ("a", "c", 2), ("a", "d", 8), ("c", "d", 9),
               ("d", "b", 6), ("b", "t", 10), ("d", "t", 10)]}


def edmonds_karp(cap_list, s="s", t="t"):
    cap = {}
    for u, v, c in cap_list:
        cap[(u, v)] = cap.get((u, v), 0) + c
        cap.setdefault((v, u), 0)
    nodes = {u for u, v in cap} | {v for u, v in cap}
    flow = {k: 0 for k in cap}
    aug = []
    while True:
        prev = {s: None}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in nodes:
                if (u, v) in cap and v not in prev and cap[(u, v)] - flow[(u, v)] > 0:
                    prev[v] = u
                    q.append(v)
        if t not in prev:
            break
        path = [t]
        while prev[path[-1]] is not None:
            path.append(prev[path[-1]])
        path = path[::-1]
        b = min(cap[(u, v)] - flow[(u, v)] for u, v in zip(path, path[1:]))
        for u, v in zip(path, path[1:]):
            flow[(u, v)] += b
            flow[(v, u)] -= b
        aug.append((path, b, dict(flow)))
    reach = set(prev)
    total = sum(flow[(s, v)] for v in nodes if (s, v) in flow)
    return total, aug, reach, flow


def build(S):
    S.cover("网络里每条管道有容量上限，从源点 s 往汇点 t 最多能送多少流量？为什么需要“反向边”？最大流为什么等于最小割？",
            ["图与路径", "增广的思想（第 28 集）"])

    # ------------------------------------------------------------ 问题
    S.section("流网络")
    dg = Graph(DIAMOND["pos"], [(u, v, f"0/{c}") for u, v, c in DIAMOND["cap"]], x=600, y=470, directed=True, r=34,
               size=26, wsize=26, wcolor=FG)
    S.show(dg)
    S.say("每条有向边有一个容量。从 s 送流量到 t：每条边上的流量不超过容量；除了 s 和 t，每个点流进多少就流出多少。")
    S.note("容量限制：0 ≤ 流量 ≤ 容量")
    S.note("流量守恒：中间点 流入 = 流出")
    S.say("边上写的是“流量/容量”。这张图所有容量都是 1。最大流显然是 2：s→a→t 和 s→b→t 各 1。")
    S.say("最直接的算法：反复找一条每条边都还有剩余容量的 s→t 路径，把能推的流量推过去。")
    S.note("贪心：反复找还有剩余容量的路径，推流")

    # ------------------------------------------------------------ 卡住
    S.section("贪心找路会卡住", keep=[dg])
    S.say("如果第一次运气不好，找到的是 s→a→b→t：")
    p = [("s", "a"), ("a", "b"), ("b", "t")]
    S.play(*[dg.edge(u, v).to(color=Y, w=7) for u, v in p], *[dg.etags[(u, v)].to(text="1/1", color=Y) for u, v in p], dur=0.7)
    S.say("推了 1 之后，s→a、b→t 都满了。剩下还有空的边是 s→b、a→t，可它们连不成一条 s 到 t 的路。贪心停在 1，比最优的 2 少。")
    S.play(dg.edge("s", "b").to(color=CY, w=5), dg.edge("a", "t").to(color=CY, w=5), dur=0.5)
    S.note("走了 s→a→b→t 后卡在 1（最优是 2）", color=R)
    S.say("问题在于 a→b 这一步是“走错了”，但贪心不会撤销已经推出去的流量。需要一种“反悔”的机制。")

    # ------------------------------------------------------------ 反向边
    S.section("残量网络与反向边", keep=[dg])
    S.say("在边 u→v 上推了 f 的流量，就在“残量网络”里加一条反向边 v→u，容量是 f。走这条反向边，意思是把原来那 f 的流量“退回去”一部分。")
    S.note("推 f 后：u→v 剩余容量 −f；反向边 v→u 剩余容量 +f（可以退回）", color=Y)
    rev = Line(color=G, w=5, head=14, bend=0.25, dash=(10, 7)).attach(dg["b"], dg["a"])
    rev.tr["op"].base = 0
    dg.add(rev)
    rlab = label(600 + 110, 470, "反向 1", 24, G, anchor="lm")
    S.play(FadeIn(rev), FadeIn(rlab), dur=0.5)
    S.say("现在残量网络里有路 s→b→a→t：s→b 剩 1，b→a 是反向边（剩 1），a→t 剩 1。沿它再推 1。")
    S.play(dg.edge("s", "b").to(color=G, w=7), rev.to(color=G, w=7), dg.edge("a", "t").to(color=G, w=7), dur=0.6)
    S.say("走反向边 b→a，就是把 a→b 上的那 1 退掉。结果：a→b 的流量变回 0，s→a→t、s→b→t 各 1，总流量 2。")
    S.play(dg.edge("a", "b").to(color=LINE2, w=3), dg.etags[("a", "b")].to(text="0/1", color=FG), FadeOut(rev, rlab),
           dg.etags[("s", "b")].to(text="1/1", color=Y), dg.etags[("a", "t")].to(text="1/1", color=Y),
           dg.edge("s", "b").to(color=Y), dg.edge("a", "t").to(color=Y), dur=0.7)
    S.note("增广路可以走反向边 = 撤销之前的流量 → 不会卡住", color=G)
    S.say("这就是 Ford–Fulkerson 方法：在残量网络里反复找增广路并推流，直到 s 到不了 t。和二分图匹配里的“反悔”是同一个想法。")

    # ------------------------------------------------------------ 完整例子
    S.section("完整推一遍")
    S.wide()
    total, aug, reach, flow = edmonds_karp(NET["cap"])
    ng = Graph(NET["pos"], [(u, v, f"0/{c}") for u, v, c in NET["cap"]], x=700, y=480, directed=True, r=34, size=26,
               wsize=24, wcolor=FG)
    S.show(ng)
    capd = {(u, v): c for u, v, c in NET["cap"]}
    tot = label(1500, 300, "总流量 0", 34, Y)
    S.show(tot)
    S.say("每次用 BFS 找一条边数最少的增广路（Edmonds–Karp），推上路径上最小的剩余容量。")
    acc = 0
    for i, (path, b, fl) in enumerate(aug):
        es = list(zip(path, path[1:]))
        S.play(*[ng.edge(u, v).to(color=O, w=7) if (u, v) in ng.edges else ng.edge(u, v).to(color=G, w=7) for u, v in es],
               dur=0.5)
        acc += b
        S.play(*[ng.etags[k].to(text=f"{max(0, fl[k])}/{capd[k]}") for k in capd], tot.to(text=f"总流量 {acc}"), dur=0.5)
        if i < 2:
            S.say(f"第 {i + 1} 条增广路：{' → '.join(path)}，瓶颈 {b}。")
        S.play(*[ng.edge(u, v).to(color=Y if fl.get((u, v), 0) > 0 else LINE2, w=5 if fl.get((u, v), 0) > 0 else 3)
                 for u, v in capd], dur=0.3)
        S.wait(0.3)
    S.say(f"再也找不到增广路了，最大流 = {total}。")

    # ------------------------------------------------------------ 最小割
    S.section("最大流 = 最小割", keep=[ng])
    S.narrow()
    S.play(ng.to(x=640), dur=0.5)
    S.say("割：把点分成两部分 S（含 s）和 T（含 t）。割的容量 = 所有从 S 指向 T 的边的容量之和。")
    S.note("割 (S, T)：容量 = Σ 从 S 到 T 的边的容量")
    S.say("任何一个流都要从 S 走到 T，所以 流量 ≤ 任何一个割的容量。")
    S.note("任何流 ≤ 任何割", color=Y)
    S.say("算法结束时，令 S = 残量网络里从 s 还能到达的点。S 到 T 的边一定都满了（否则还能多到一个点），T 到 S 的边流量一定是 0（否则反向边能走）。")
    S.play(*[ng[v].to(fill=tint(CY, 0.45), stroke=CY) for v in reach], *[ng[v].to(fill=tint(O, 0.45), stroke=O) for v in NET["pos"] if v not in reach],
           dur=0.6)
    cut_edges = [(u, v) for u, v in capd if u in reach and v not in reach]
    S.play(*[ng.edge(u, v).to(color=R, w=8) for u, v in cut_edges], dur=0.5)
    cutcap = sum(capd[e] for e in cut_edges)
    S.say(f"于是流量恰好等于这个割的容量：S = {{{', '.join(sorted(reach))}}}，割边 " + "、".join(f"{u}→{v}" for u, v in cut_edges) +
          f"，容量 {cutcap} = 最大流 {total}。流量不能再大，割不能再小——两个都最优。")
    S.note("结束时：S = 残量网络中 s 可达的点 → 流量 = 割容量 → 最大流 = 最小割", color=G)
    S.say("Dinic 算法是更快的实现：先 BFS 给点分层，只沿“下一层”的边找路，一次把一层图推到阻塞。一般图 O(V²E)，实际上非常快。", extra=0.3)
    S.note("Dinic：BFS 分层 + 阻塞流，实践中很快", color=CY)

    # ------------------------------------------------------------ 手推题
    S.quiz("网络：s→a 容量 3，s→b 容量 2，a→b 容量 1，a→t 容量 2，b→t 容量 3。\n\n"
           "(1) 最大流是多少？给出每条边的流量。\n"
           "(2) 给出一个最小割，说明为什么不可能更大。", think=20)
    qcap = [("s", "a", 3), ("s", "b", 2), ("a", "b", 1), ("a", "t", 2), ("b", "t", 3)]
    qt, qaug, qreach, qflow = edmonds_karp(qcap)
    qg = Graph(DIAMOND["pos"], [(u, v, f"{qflow[(u, v)]}/{c}") for u, v, c in qcap], x=560, y=560, directed=True, r=32,
               size=24, wsize=24, wcolor=Y)
    S.show(qg)
    S.say(f"(1) s→a 送 3：其中 2 走 a→t，1 走 a→b；s→b 送 2，加上从 a 来的 1，b→t 送 3。总流量 {qt}。")
    S.note(f"(1) 最大流 {qt}", color=Y)
    S.say("(2) 割 S = {s}：割边 s→a、s→b，容量 3 + 2 = 5。任何流都要从 s 出来，最多 5，所以 5 就是最大。")
    S.play(qg["s"].to(fill=tint(CY, 0.5), stroke=CY), qg.edge("s", "a").to(color=R, w=7), qg.edge("s", "b").to(color=R, w=7), dur=0.5)
    S.note("(2) 割 {s} | {a, b, t}，容量 5（{s,a,b} | {t} 也是最小割）", color=G)

    S.recap([
        "流网络：容量限制 + 流量守恒；贪心找路推流可能卡在非最优。",
        "残量网络：推 f 就加一条容量 f 的反向边，走它等于撤销，保证不会卡住。",
        "Ford–Fulkerson：反复找增广路；Edmonds–Karp 用 BFS，Dinic 分层后推阻塞流。",
        "任何流 ≤ 任何割；算法结束时 s 在残量网络里可达的点给出一个容量等于流量的割：最大流 = 最小割。",
    ], next_title="最小割建模：割就是一种选择")
