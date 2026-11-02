"""第 52 集 虚树：只留下关键点和它们的 LCA"""

from itertools import combinations

from episodes.common import *

EDGES = [(1, 2), (1, 3), (2, 4), (2, 5), (4, 6), (4, 7), (5, 8), (3, 9), (3, 10), (9, 11), (9, 12), (10, 13)]
KEYS = [6, 8, 11, 13]
QKEYS = [7, 8, 12]


def prep():
    ch, par, dep = {}, {1: None}, {1: 0}
    for p, c in EDGES:
        ch.setdefault(p, []).append(c)
        par[c] = p
    dfn, order = {}, []

    def dfs(v):
        dfn[v] = len(order)
        order.append(v)
        for c in ch.get(v, []):
            dep[c] = dep[v] + 1
            dfs(c)

    dfs(1)
    return par, dep, dfn


PAR, DEP, DFN = prep()


def lca(a, b):
    while DEP[a] > DEP[b]:
        a = PAR[a]
    while DEP[b] > DEP[a]:
        b = PAR[b]
    while a != b:
        a, b = PAR[a], PAR[b]
    return a


def build_vt(keys):
    """栈建虚树，返回 (边列表, 每一步的日志)。"""
    keys = sorted(keys, key=lambda v: DFN[v])
    stk = [1]
    edges, log = [], []
    for x in keys:
        if x == 1:
            continue
        l = lca(x, stk[-1])
        ev = []
        if l != stk[-1]:
            while len(stk) >= 2 and DFN[stk[-2]] >= DFN[l]:
                edges.append((stk[-2], stk[-1]))
                ev.append(("edge", stk[-2], stk[-1]))
                stk.pop()
            if stk[-1] != l:
                edges.append((l, stk[-1]))
                ev.append(("edge", l, stk[-1]))
                stk[-1] = l
                ev.append(("replace", l))
        stk.append(x)
        log.append((x, l, ev, stk[:]))
    tail = []
    while len(stk) >= 2:
        edges.append((stk[-2], stk[-1]))
        tail.append((stk[-2], stk[-1]))
        stk.pop()
    return edges, log, tail


def build(S):
    S.cover("一棵很大的树，很多次询问，每次只关心其中 k 个“关键点”（所有询问的 k 加起来不大）。每次都在整棵树上 DP 太慢——能不能只留下和关键点有关的那一小部分？",
            ["倍增与 LCA（第 19 集）", "DFS 序（第 18 集）", "树形 DP（第 7 集）"])

    keys_sorted = sorted(KEYS, key=lambda v: DFN[v])
    pair_lcas = {lca(a, b) for a, b in combinations(KEYS, 2)}
    adj_lcas = {lca(a, b) for a, b in zip(keys_sorted, keys_sorted[1:])}
    assert pair_lcas == adj_lcas
    edges, log, tail = build_vt(KEYS)
    assert {x: l for x, l, _, _ in log} == {6: 1, 8: 2, 11: 1, 13: 3}     # 下面的讲解按这个过程写
    vnodes = set(KEYS) | adj_lcas | {1}

    tr = Tree(EDGES, 1, x=440, y=470, w=760, h=560, r=28, size=22)

    # ------------------------------------------------------------ 要留哪些点
    S.section("要留下哪些点")
    S.show(tr)
    S.play(*[tr[v].to(fill=tint(Y, 0.55), stroke=Y) for v in KEYS], dur=0.5)
    S.say(f"黄色是这次询问的关键点 {', '.join(map(str, KEYS))}。很多树形 DP 只关心关键点之间的“分叉”结构，中间一长串只有一个儿子的点可以缩掉。")
    S.note("虚树：只保留关键点和它们两两的 LCA，压缩其余的链", color=Y)
    S.say("需要保留的是关键点、它们两两的 LCA（分叉处），再加上根。可两两 LCA 有 O(k²) 对，要全部算吗？")
    S.say("不用。把关键点按 DFS 序排好，只算相邻两个的 LCA 就够了：" +
          "、".join(f"LCA({a}, {b}) = {lca(a, b)}" for a, b in zip(keys_sorted, keys_sorted[1:])) + "。")
    S.play(*[tr[v].to(fill=tint(O, 0.5), stroke=O) for v in adj_lcas if v not in KEYS], dur=0.5)
    S.note("按 DFS 序排序后，相邻关键点的 LCA 就包含了所有两两 LCA", color=G)
    S.say("为什么？任取 aᵢ、aⱼ（i < j，按 DFS 序）。它们的 LCA 是 aᵢ 到 aⱼ 之间相邻各对 LCA 里最浅的那个——因为 DFS 序在 aᵢ、aⱼ 之间的点都在 LCA(aᵢ, aⱼ) 的子树里。")
    S.say(f"所以虚树最多 k 个关键点 + (k − 1) 个 LCA = 2k − 1 个点（不算额外加的根）。这里正好 {len(vnodes)} 个。", extra=0.3)
    S.note("虚树至多 2k − 1 个点（+ 根）", color=Y)

    # ------------------------------------------------------------ 用栈建树
    S.section("用栈建树", keep=[tr])
    S.say("按 DFS 序依次加入关键点，用一个栈维护“虚树上从根到当前点的那条链”。栈底是根。")
    S.note("栈 = 虚树中从根到最近加入点的链", color=Y)
    stk = Array([""] * 5, x=1060, y=230, cw=70, ch=56, gap=6, size=26, index=False, fill=tint(B, 0.12))
    S.show(stk, label(1060, 170, "栈（左边是栈底）", 22, DIM))
    S.play(stk.cells[0].to(text="1", fill=tint(B, 0.35)), dur=0.4)
    vedges = {}

    def vedge(a, b):
        ln = Line(color=O, w=5, bend=0.18).attach(tr[a], tr[b])
        ln.tr["op"].base = 0
        tr.add(ln)
        vedges[(a, b)] = ln
        return FadeIn(ln)

    def show_stack(cur):
        return [stk.cells[i].to(text=str(cur[i]) if i < len(cur) else "", fill=tint(B, 0.35) if i < len(cur) else tint(B, 0.12))
                for i in range(5)]

    info = label(1060, 330, "", 26, FG)
    S.add(info)
    for x, l, ev, cur in log:
        S.play(tr[x].to(sw=5), info.to(text=f"加入 {x}：LCA({x}, 栈顶) = {l}"), dur=0.4)
        anims = []
        for e in ev:
            if e[0] == "edge":
                anims.append(vedge(e[1], e[2]))
        S.play(*anims, *show_stack(cur), dur=0.6)
        if x == 8:
            S.say("加入 8：它和栈顶 6 的 LCA 是 2，不在栈里。说明 6 那一支已经结束了：连上 2 → 6，再把栈顶换成 2，最后压入 8。")
        elif x == 11:
            S.say("加入 11：LCA(11, 8) = 1。比 1 深的栈元素都要出栈，出栈时把它和下面一个连边：2 → 8，1 → 2。然后压入 11。")
            S.note("弹栈直到栈顶的深度 ≤ LCA；弹出时与下面的元素连边；必要时把 LCA 压进去", color=G)
        elif x == 13:
            S.say("加入 13：LCA(13, 11) = 3 不在栈里：连 3 → 11，栈顶换成 3，压入 13。")
        S.play(tr[x].to(sw=2.5), dur=0.2)
    S.play(*[vedge(a, b) for a, b in tail], *show_stack([1]), info.to(text="最后把栈里剩下的链依次连起来"), dur=0.6)
    S.say("所有关键点加入后，栈里剩下的链依次连边。橙色的边就是虚树：" + "、".join(f"{a} → {b}" for a, b in sorted(edges)) + "。")
    assert {v for e in edges for v in e} == vnodes
    S.say("每个点进栈、出栈各一次，每次求一个 LCA：建树 O(k log n)。在虚树上做树形 DP，就只和 k 有关了。", extra=0.3)
    S.note("建虚树 O(k log n)；所有询问合计 O(Σk · log n)", color=G)

    # ------------------------------------------------------------ 应用
    S.section("虚树上的 DP 要注意什么")
    S.say("例：切断一些边让所有关键点和根不连通，最小代价是多少？在原树上是树形 DP，在虚树上同样做，只是虚树的一条边代表原树的一整条链。")
    S.note("虚树的一条边 = 原树的一条链：边上的信息要先汇总（如链上的最小边权）", color=Y)
    S.say("所以要预处理“链上的信息”：比如每个点到根路径上的最小边权，虚树边 u → v 的代价就是 v 到 u 那段链上的最小边权（用倍增求）。")
    S.say("另一个细节：每次询问用完要把虚树清空，只清自己用过的点，不能 O(n) 清整棵树。", extra=0.5)
    S.note("每次询问只清理用过的点")

    # ------------------------------------------------------------ 手推题
    q_sorted = sorted(QKEYS, key=lambda v: DFN[v])
    qe, _, _ = build_vt(QKEYS)
    qn = sorted({v for e in qe for v in e})
    S.quiz(f"还是这棵树，关键点改成 {', '.join(map(str, QKEYS))}。\n\n"
           "(1) 按 DFS 序排好关键点，求相邻两点的 LCA。\n"
           "(2) 虚树有哪些点、哪些边？", think=20)
    S.say(f"(1) DFS 序：{', '.join(map(str, q_sorted))}。" + "，".join(f"LCA({a}, {b}) = {lca(a, b)}" for a, b in zip(q_sorted, q_sorted[1:])) + "。")
    S.note("(1) " + "，".join(f"LCA({a},{b}) = {lca(a, b)}" for a, b in zip(q_sorted, q_sorted[1:])), color=Y)
    S.say(f"(2) 点：{', '.join(map(str, qn))}；边：" + "、".join(f"{a} → {b}" for a, b in sorted(qe)) + "。", extra=0.5)
    S.note("(2) 边：" + "、".join(f"{a}→{b}" for a, b in sorted(qe)), color=G)

    S.recap([
        "虚树只保留关键点和它们的 LCA（以及根），把中间的链压缩成一条边。",
        "按 DFS 序排序后，相邻关键点的 LCA 已包含所有两两 LCA，所以至多 2k − 1 个点。",
        "用栈维护根到当前点的链，按 DFS 序插入，弹栈时连边：O(k log n)。",
        "虚树的边代表原树的链，链上的信息要预处理；每次询问只清理用过的点。",
    ], next_title="2-SAT")
