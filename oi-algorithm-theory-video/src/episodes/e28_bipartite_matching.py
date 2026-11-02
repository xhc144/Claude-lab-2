"""第 28 集 二分图匹配：增广路与反悔"""

from episodes.common import *

ADJ = {1: [1, 2], 2: [1], 3: [2, 3], 4: [3, 4]}
N = 4


def bip_layout(n, gap=120, dx=300):
    pos = {}
    for i in range(1, n + 1):
        pos[("L", i)] = (-dx, (i - (n + 1) / 2) * gap)
        pos[("R", i)] = (dx, (i - (n + 1) / 2) * gap)
    return pos


def greedy():
    match_r = {}
    pairs = []
    for u in sorted(ADJ):
        for v in ADJ[u]:
            if v not in match_r:
                match_r[v] = u
                pairs.append((u, v))
                break
    return pairs


def kuhn_trace():
    match_r, match_l = {}, {}
    log = []

    def dfs(u, seen, path):
        for v in ADJ[u]:
            if v in seen:
                continue
            seen.add(v)
            if v not in match_r or dfs(match_r[v], seen, path + [(u, v), (match_r[v], v)] if v in match_r else path):
                match_r[v] = u
                match_l[u] = v
                return True
        return False

    for u in sorted(ADJ):
        before = dict(match_l)
        dfs(u, set(), [])
        log.append((u, before, dict(match_l)))
    return log, match_l


def build(S):
    S.cover("左边是人、右边是工作，连线表示能胜任。最多能让多少人各得一份不同的工作？贪心为什么不行，“反悔”又该怎么做？",
            ["图的基本概念", "DFS"])

    pos = bip_layout(N)
    edges = [(("L", u), ("R", v)) for u in ADJ for v in ADJ[u]]
    labels = {k: (f"人{k[1]}" if k[0] == "L" else f"工{k[1]}") for k in pos}

    # ------------------------------------------------------------ 问题与贪心
    S.section("问题：二分图最大匹配")
    g = Graph(pos, edges, x=600, y=470, r=34, size=22, labels=labels)
    S.show(g)
    S.say("二分图：点分成左右两边，边只连接左边和右边。匹配：选一些边，任意两条没有公共端点。最大匹配就是选得最多的那一种。")
    S.note("匹配：一组没有公共端点的边；求最多能选几条")
    gp = greedy()
    S.say("贪心：人 1 到人 4 依次挑第一个还空着的工作。")
    for u, v in gp:
        S.play(g.edge(("L", u), ("R", v)).to(color=Y, w=7), dur=0.4)
    S.play(g[("L", 2)].to(fill=tint(R, 0.5), stroke=R), dur=0.4)
    S.say(f"结果只匹配了 {len(gp)} 对：人 2 只会工作 1，可工作 1 已经被人 1 占了。其实人 1 换成工作 2、人 3 换成工作 3、人 4 换成工作 4，就能 4 个人全部安排。")
    S.note(f"贪心：{len(gp)} 对；最优：4 对。需要“反悔”", color=R)
    S.say("先到的人占了别人唯一能做的工作，要让它“让一让”。问题是：让的方式要系统，不能乱试。")

    # ------------------------------------------------------------ 增广路
    S.section("交错路与增广路", keep=[g])
    S.say("在当前匹配下，从一个{y|没匹配的左点}出发，交替走“非匹配边、匹配边、非匹配边……”，最后到达一个{y|没匹配的右点}，这样的路叫增广路。")
    S.note("增广路：未匹配左点 →(非匹配)→(匹配)→ … →(非匹配)→ 未匹配右点", color=Y)
    path = [("L", 2), ("R", 1), ("L", 1), ("R", 2), ("L", 3), ("R", 3), ("L", 4), ("R", 4)]
    S.play(g[("L", 2)].to(fill=BG3, stroke=Y, sw=4), dur=0.3)
    for a, b in zip(path, path[1:]):
        e = g.edge(a, b)
        matched = (a[0] == "R")
        S.play(e.to(color=O if matched else CY, w=7), dur=0.35)
    S.play(g[("R", 4)].to(stroke=Y, sw=4), dur=0.3)
    S.say("这里：人2 —工1— 人1 —工2— 人3 —工3— 人4 —工4。青色是非匹配边（4 条），橙色是匹配边（3 条）。")
    S.say("把路上所有边的状态{y|翻转}：青色变成匹配、橙色变成非匹配。匹配边从 3 条变成 4 条，而且仍然是合法的匹配（每个点最多一条）。")
    S.note("沿增广路翻转：匹配数 +1（非匹配边比匹配边多一条）", color=G)
    S.play(*[g.edge(a, b).to(color=(Y if a[0] == "L" else LINE2), w=(7 if a[0] == "L" else 3)) for a, b in zip(path, path[1:])],
           dur=0.8)
    S.play(g[("L", 2)].to(fill=tint(G, 0.4), stroke=G, sw=2.5), g[("R", 4)].to(fill=tint(G, 0.4), stroke=G, sw=2.5), dur=0.4)
    S.say("翻转就是“反悔”：人 1 让出工作 1、改做工作 2，人 3 让出工作 2、改做工作 3……一路让下去，直到有人拿到一份空着的工作。")

    # ------------------------------------------------------------ Berge
    S.section("没有增广路，就是最大")
    S.say("定理（Berge）：当前匹配是最大匹配 ⇔ 不存在增广路。“⇒”显然；关键是“⇐”：为什么找不到增广路就一定最大？")
    S.note("Berge：最大匹配 ⇔ 没有增广路", color=Y)
    S.say("设当前匹配 M，另有一个更大的匹配 M′。把两者“异或”：只属于其中一个的边留下。每个点最多连 M 一条、M′ 一条，所以留下的边组成若干条路径和环，并且 M、M′ 的边交替出现。")
    demo = Group(600, 470)
    pts = [(-400 + 160 * i, 0) for i in range(6)]
    for i, (x, y) in enumerate(pts):
        demo.add(Circle(x, y, 16, fill=BG3, stroke=LINE2))
    for i in range(5):
        col = CY if i % 2 == 0 else O
        demo.add(Line(pts[i][0], 0, pts[i + 1][0], 0, color=col, w=6))
    demo.add(Text(-80, -60, "青 = 只在 M′ 里　橙 = 只在 M 里", size=24, color=DIM))
    S.show(demo)
    S.say("环和偶数长的路里，两种边一样多。M′ 比 M 多，就一定有一条路 M′ 的边比 M 多一条——它的两端都没被 M 匹配，正是 M 的增广路。")
    S.note("M′ 更大 ⇒ M ⊕ M′ 里有一条 M′ 边多的路 ⇒ M 有增广路", color=G)
    S.say("所以算法就是：反复找增广路、翻转，直到找不到为止。")

    # ------------------------------------------------------------ 匈牙利算法
    S.section("匈牙利算法")
    S.play(FadeOut(demo), dur=0.2)
    g2 = Graph(pos, edges, x=600, y=470, r=34, size=22, labels=labels)
    S.show(g2)
    S.say("匈牙利算法：依次给每个左点 u 找增广路。用 DFS：枚举 u 的邻居 v（本次没试过的），如果 v 空着，直接配；否则让 v 现在的伙伴去找别的工作（递归），成功就把 v 给 u。")
    S.note("给 u 找：v 空着 → 配；v 被 w 占 → 递归让 w 另找，成功则 v 归 u", color=Y)
    S.note("每次 DFS 用 visited 标记右点，避免重复")
    log, ml = kuhn_trace()
    cur = {}
    for u, before, after in log:
        changed = [(x, after[x]) for x in after if before.get(x) != after[x]]
        S.play(g2[("L", u)].to(stroke=Y, sw=4), dur=0.3)
        old = [(x, before[x]) for x in before if after.get(x) != before[x]]
        S.play(*[g2.edge(("L", x), ("R", y)).to(color=LINE2, w=3) for x, y in old],
               *[g2.edge(("L", x), ("R", y)).to(color=Y, w=7) for x, y in changed], dur=0.6)
        S.play(g2[("L", u)].to(stroke=LINE2, sw=2.5), dur=0.2)
        if u == 2:
            S.say("轮到人 2：他只会工作 1，被人 1 占着。于是递归让人 1 另找——人 1 还会工作 2，空着，成功。人 1 改做工作 2，人 2 拿到工作 1。")
        if u == 4:
            S.say("轮到人 4：工作 3 被人 3 占着，让人 3 另找，人 3 想要的工作 2 又被人 1 占着……都让不开；人 4 改试工作 4，空着，直接配上。")
        S.wait(0.3)
    S.say(f"最终匹配 {len(ml)} 对。每个左点做一次 DFS，每次 O(m)，总共 O(n·m)。")
    S.note("复杂度 O(n·m)", color=G)

    # ------------------------------------------------------------ König
    S.section("König 定理与建模")
    S.say("一个常用的结论（König 定理）：二分图里，最大匹配数 = 最小点覆盖数（选最少的点，使每条边至少有一个端点被选）。")
    S.note("König：二分图中 最大匹配 = 最小点覆盖", color=Y)
    S.say("“≥”的方向很直观：匹配的每条边都至少要选一个端点，而且匹配边没有公共端点，所以点覆盖至少要匹配数那么多个点。另一半（能取到等号）需要构造，这里不展开。")
    S.say("建模时经常这样用：一个“对象”有两个属性（比如格子的行和列），每个对象要被“某一行”或“某一列”处理掉——把行、列当两边的点，对象当边，就是最小点覆盖。")
    S.note("建模：对象 = 边，两种“处理方式” = 两边的点", color=G)

    # ------------------------------------------------------------ 手推题
    S.quiz("3×3 的网格上有 4 个障碍：(1,1)、(1,3)、(2,2)、(3,2)。每次可以清除一整行或一整列的所有障碍。\n\n"
           "(1) 最少清除几次？怎样建二分图？\n"
           "(2) 给出一种最优方案。", think=20)
    obs = [(1, 1), (1, 3), (2, 2), (3, 2)]
    grid = Grid(3, 3, x=330, y=560, cw=90, ch=90, gap=4, rbase=1, cbase=1, rlab=["行1", "行2", "行3"], clab=["列1", "列2", "列3"])
    S.show(grid)
    S.play(*[grid[o].to(fill=tint(R, 0.5), text="×") for o in obs], dur=0.5)
    bpos = {("r", i): (-160, (i - 2) * 110) for i in range(1, 4)}
    bpos.update({("c", j): (160, (j - 2) * 110) for j in range(1, 4)})
    bg = Graph(bpos, [(("r", r), ("c", c)) for r, c in obs], x=880, y=560, r=30, size=20,
               labels={k: ("行" if k[0] == "r" else "列") + str(k[1]) for k in bpos})
    S.show(bg)
    S.say("(1) 左边是 3 行、右边是 3 列，每个障碍 (r, c) 连一条边“行 r — 列 c”。清除一行或一列 = 选一个点；清掉所有障碍 = 覆盖所有边。")
    S.say("最大匹配：行1—列1、行2—列2，行3 只连着列2，已被占，再增广也不行，所以最大匹配是 2，最少清除 2 次。")
    S.play(bg.edge(("r", 1), ("c", 1)).to(color=Y, w=6), bg.edge(("r", 2), ("c", 2)).to(color=Y, w=6), dur=0.5)
    S.note("(1) 行、列为两边点，障碍为边；最大匹配 2 → 最少 2 次", color=Y)
    S.say("(2) 一种方案：清除第 1 行（去掉 (1,1)、(1,3)）和第 2 列（去掉 (2,2)、(3,2)）。")
    S.play(bg[("r", 1)].to(fill=tint(G, 0.5), stroke=G), bg[("c", 2)].to(fill=tint(G, 0.5), stroke=G),
           *[grid[o].to(fill=tint(G, 0.4)) for o in obs], dur=0.6)
    S.note("(2) 清除第 1 行 + 第 2 列", color=G)

    S.recap([
        "贪心会被“先到先占”卡住，需要能反悔：沿增广路翻转，匹配数 +1。",
        "Berge：没有增广路 ⇔ 最大匹配（两个匹配的异或由交错路和环组成）。",
        "匈牙利算法：逐个左点 DFS 找增广路，被占就递归让对方另找，O(n·m)。",
        "König：二分图最大匹配 = 最小点覆盖；行列建图是常见的建模方式。",
    ], next_title="最大流：残量网络与反向边")
