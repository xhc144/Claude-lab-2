"""第 7 集 树形 DP：子树要向上交代多少信息"""

from episodes.common import *

EDGES = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (6, 7), (6, 8)]
COST = {1: 4, 2: 3, 3: 6, 4: 2, 5: 5, 6: 2, 7: 3, 8: 4}
INF = float("inf")


def dom_dp(edges, cost, root):
    ch = {}
    for p, c in edges:
        ch.setdefault(p, []).append(c)
    f, order, forced = {}, [], {}

    def dfs(u):
        f0, f1, f2, diff, any0, best_v = cost[u], 0, 0, INF, False, None
        for v in ch.get(u, []):
            dfs(v)
            a, b, c = f[v]
            f0 += min(a, b, c)
            f2 += b
            f1 += min(a, b)
            if a <= b:
                any0 = True
            if a - b < diff:
                diff, best_v = a - b, v
        if not ch.get(u):
            f1 = INF
        elif not any0:
            f1 += diff
            forced[u] = best_v
        f[u] = (f0, f1, f2)
        order.append(u)

    dfs(root)
    return f, order, ch, forced


def fmt(v):
    return "∞" if v == INF else str(v)


def trip(t):
    return "(" + ", ".join(fmt(x) for x in t) + ")"


def reconstruct(f, ch, cost, root):
    chosen = set()

    def go(u, st):
        if st == 0:
            chosen.add(u)
            for v in ch.get(u, []):
                a, b, c = f[v]
                m = min(a, b, c)
                go(v, 0 if a == m else 1 if b == m else 2)
        elif st == 2:
            for v in ch.get(u, []):
                go(v, 1)
        else:
            kids = ch.get(u, [])
            pick = [0 if f[v][0] <= f[v][1] else 1 for v in kids]
            if 0 not in pick:
                j = min(range(len(kids)), key=lambda j: f[kids[j]][0] - f[kids[j]][1])
                pick[j] = 0
            for v, s in zip(kids, pick):
                go(v, s)

    a, b, _ = f[root]
    go(root, 0 if a <= b else 1)
    return chosen


def build(S):
    S.cover("在树上选一些点放保安，每个点要么自己有保安，要么和有保安的点相邻。总费用最少是多少？状态要设计几个？",
            ["树形 DP 的基本写法（如最大独立集 f[u][0/1]）"])

    # ------------------------------------------------------------ 问题
    S.section("问题：最小支配集")
    tree = Tree(EDGES, 1, x=420, y=480, w=560, h=480, r=30, size=26)
    S.show(tree)
    ct = {v: tree.tag(v, f"{COST[v]}元", "l", DIM, 22) for v in COST}
    S.play(*[FadeIn(t) for t in ct.values()], dur=0.5)
    S.say("一棵树，每个点有一个费用。选一些点放保安，要求每个点{y|要么被选，要么至少有一个邻居被选}。总费用最少是多少？")
    S.note("每个点：自己被选，或有邻居被选（被“支配”）")
    S.note("求：被选点的总费用最小", color=Y)
    S.say("这叫最小支配集。在一般图上很难，在树上可以用树形 DP 在线性时间内解决。")
    S.say("按习惯，先试试两个状态：u 选或不选。")

    # ------------------------------------------------------------ 两个状态不够
    S.section("两个状态为什么不够")
    S.say("看最简单的例子：一条三个点的链，中间的点费用 1，两端各 5。显然只选中间的点，费用 1。")
    t3 = Tree([("b", "a"), ("b", "c")], "b", x=420, y=440, w=360, h=200, r=32, size=26)
    S.show(t3)
    tg = {v: t3.tag(v, s, "d", DIM, 22) for v, s in (("a", "5元"), ("b", "1元"), ("c", "5元"))}
    S.play(*[FadeIn(t) for t in tg.values()], dur=0.4)
    S.say("如果规定“u 不选时，u 必须被它子树里的点支配”：叶子 a 不选的话，它的子树里没有别人，这个状态不合法，只好选 a。")
    S.note("尝试：g[u][1] 选 u；g[u][0] 不选 u 且被子树支配")
    S.play(t3["a"].to(fill=tint(R, 0.4), stroke=R), t3["c"].to(fill=tint(R, 0.4), stroke=R), dur=0.6)
    S.say("于是 a、c 都被迫选上，算出来至少 10，而正确答案是 1。漏掉的方案是：a 由它的{y|父亲} b 来支配。")
    S.note("问题：叶子可以被父亲支配，子树内部不知道", color=R)
    S.play(t3["a"].to(fill=BG3, stroke=LINE2), t3["c"].to(fill=BG3, stroke=LINE2), t3["b"].to(fill=tint(Y, 0.5), stroke=Y),
           dur=0.6)
    S.say("如果反过来允许“u 不选、也还没被支配”，那就必须告诉父亲：你一定要被选。这是另一种情况，需要单独的状态。")
    S.say("所以“u 不选”要拆成两种：已经被某个儿子支配了，或者还在等父亲来支配。")
    S.note("“不选”拆成两种：被儿子支配 / 等父亲支配", color=Y)

    # ------------------------------------------------------------ 三个状态
    S.section("三个状态")
    S.say("站在父亲的角度问：关于子树 u，我需要知道什么？")
    S.note("{y|f[u][0]}：u 被选", color=Y)
    S.note("{g|f[u][1]}：u 不选，已被某个儿子支配", color=G)
    S.note("{r|f[u][2]}：u 不选，还没被支配（父亲必须选）", color=R)
    S.note("三种情况下，子树里除 u 以外的点都必须已经被支配")
    S.say("子树和外界唯一的联系是 u 和父亲之间的那条边。子树里除 u 以外的点都碰不到外面，所以它们必须在子树内部被支配。")
    S.say("能影响外界、或被外界影响的只有 u 自己：u 选没选（影响父亲是否被支配），u 不选时是否已被支配（决定父亲是否必须选）。三个状态正好覆盖这些情况。")
    S.say("转移。f[u][0]：u 被选，每个儿子三种状态都可以——儿子即使在“等父亲”，也被 u 支配了。")
    S.note("f[u][0] = 费用(u) + Σ min(f[v][0], f[v][1], f[v][2])")
    S.say("f[u][2]：u 不选、也没被支配，所以没有儿子被选；每个儿子也不能“等父亲”（父亲 u 没被选），只能是状态 1。")
    S.note("f[u][2] = Σ f[v][1]")
    S.say("f[u][1]：每个儿子取 min(f[v][0], f[v][1])，但{y|至少要有一个儿子被选}。")
    S.note("f[u][1] = Σ min(f[v][0], f[v][1])，至少一个儿子取 0")
    S.say("技巧：先让每个儿子各取各的最小值。如果碰巧没有一个儿子选了状态 0，就挑 f[v][0] − f[v][1] 最小的那个儿子改成状态 0，补上这个差。")
    S.note("若都没取 0：加上 min(f[v][0] − f[v][1])", color=G)

    # ------------------------------------------------------------ 推一遍
    S.section("自底向上推一遍")
    f, order, ch, forced = dom_dp(EDGES, COST, 1)
    tree2 = Tree(EDGES, 1, x=420, y=480, w=560, h=480, r=30, size=26)
    S.show(tree2)
    ct2 = {v: tree2.tag(v, f"{COST[v]}元", "l", DIM, 22) for v in COST}
    tr = {v: tree2.tag(v, "", "r" if ch.get(v) else "d", CY, 22) for v in COST}
    S.play(*[FadeIn(t) for t in ct2.values()], dur=0.4)
    S.say("每个点旁边写上三元组 (f0, f1, f2)。叶子：选它花自己的费用；不选时没有儿子能支配它，f1 = ∞；f2 = 0（等父亲）。")
    leaves = [v for v in order if not ch.get(v)]
    S.play(*[FadeIn(tr[v]) for v in leaves], *[tr[v].to(text=trip(f[v])) for v in leaves],
           *[tree2[v].to(stroke=CY) for v in leaves], dur=0.6)
    S.note("(f0, f1, f2) = (选 u, 被儿子支配, 等父亲)", color=DIM)
    S.note("叶子：(费用, ∞, 0)")
    for u in [v for v in order if ch.get(v)]:
        a, b, c = f[u]
        kids = ch[u]
        if u == 3:
            S.say(f"点 3 只有一个儿子 6，f[6] = {trip(f[6])}。f0 = 6 + min(2, 7, ∞) = 8；f1 = min(2, 7) = 2，而且取的正是“6 被选”；f2 = f[6][1] = 7。")
        elif u == 2:
            S.say(f"点 2 的两个儿子都是叶子：f0 = 3 + 0 + 0 = 3；f1 要求至少选一个儿子，选费用 2 的点 4，得到 7；f2 = ∞ + ∞（叶子不能被儿子支配）。")
        elif u == 1:
            S.say(f"根 1：f0 = 4 + min{trip(f[2])} + min{trip(f[3])} = 4 + 3 + 2 = 9；f1 = min(3, 7) + min(8, 2) = 5，儿子 2 已取状态 0，满足要求；f2 = 7 + 2 = 9。")
        S.play(*[tree2.edge(u, v).to(color=Y, w=5) for v in kids], tree2[u].to(stroke=Y, sw=4), dur=0.4)
        S.play(FadeIn(tr[u]), tr[u].to(text=trip(f[u])), dur=0.5)
        if u in (2, 3, 1):
            S.wait(0.8)
        S.play(*[tree2.edge(u, v).to(color=LINE2, w=3) for v in kids], tree2[u].to(stroke=CY, sw=2.5), dur=0.3)
    ans = min(f[1][0], f[1][1])
    S.say(f"根没有父亲，不能“等父亲”，所以答案是 min(f[1][0], f[1][1]) = {ans}。")
    S.note(f"答案 = min(f[根][0], f[根][1]) = {ans}（根不能取状态 2）", color=Y)
    chosen = reconstruct(f, ch, COST, 1)
    S.say(f"顺着取到最小值的选择往回找，就是选点 {'、'.join(map(str, sorted(chosen)))}：每个点都被支配，总费用 {ans}。")
    S.play(*[tree2[v].to(fill=tint(Y, 0.55), stroke=Y) for v in chosen], dur=0.6)
    others = [v for v in COST if v not in chosen]
    S.play(*[tree2[v].to(fill=tint(G, 0.3)) for v in others], dur=0.6)
    S.say("每个点只算一次三元组，每条边只在父亲处用一次，总共 O(n)。", extra=0.3)

    # ------------------------------------------------------------ 变式
    S.section("接口思维与变式")
    S.say("这一集的方法可以概括为“接口思维”：子树和外界只通过 u 相连，状态就是 u 这个接口上所有可能的情况。")
    S.note("接口思维：状态 = 子树对外接口（u）上所有可能的情况", color=Y)
    S.say("拿它去看最大独立集：父亲只关心 u 选没选（选了的话父亲不能选），所以两个状态。")
    S.note("最大独立集：u 选 / 不选 → 两个状态")
    S.say("如果改成“每个点要被距离 2 以内的被选点覆盖”，接口上就要说清楚：离 u 最近的被选点有多远，或者 u 还需要外面在多远之内提供覆盖——状态会更多。")
    S.note("距离 2 覆盖：要记“最近的被选点距离 / 还欠外面多远” → 更多状态", color=DIM)
    S.say("状态多少不是记出来的，而是问出来的：父亲到底需要知道什么？", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("(1) 最小点覆盖（每条边至少有一个端点被选）为什么只要两个状态 f[u][选/不选] 就够？用“接口”的角度解释。\n"
           "(2) 把支配集的要求改成：每个点要么被选，要么{y|至少有两个}邻居被选。状态该怎么设计？", think=20)
    S.say("(1) 点覆盖里，u 和父亲之间那条边被覆盖，当且仅当 u 或父亲被选。所以 u 不选，就一定要求父亲被选——没有“已被儿子解决”这种可能。")
    S.note("(1) u 不选 ⇒ 父亲必选；不存在“被儿子解决”，两种情况足够", color=G)
    S.say("支配集里，u 不选时，u 有可能已经被儿子支配，也可能还没有，所以要多一个状态。差别就在这里。")
    S.say("(2) u 不选时，要数它已经有几个被选的儿子：0 个、1 个、至少 2 个。父亲最多再补 1 个。")
    S.say("“0 个”的情况就算父亲被选也只有 1 个，不合法，直接丢掉。所以状态是：u 被选；u 不选且已有 ≥2 个儿子被选；u 不选且恰有 1 个儿子被选（父亲必须选）。")
    S.note("(2) 选 u / 不选且 ≥2 个儿子被选 / 不选且恰 1 个（等父亲）", color=Y)
    S.say("合并儿子时要记“已经有几个儿子被选（0、1、≥2）”，像一个很小的背包。", extra=0.5)

    S.recap([
        "两个状态的支配集会漏解：叶子可以由父亲支配，而子树内部不知道父亲会不会被选。",
        "三个状态：u 被选 / u 不选但已被儿子支配 / u 不选还在等父亲（父亲必须选）。",
        "“至少一个儿子被选”：先各取最小，没有人取到“被选”时补上最小的差值。",
        "接口思维：子树只通过 u 和外界相连，状态就是 u 这个接口上所有可能的情况。",
    ], next_title="换根 DP：让每个点都当一次根")
