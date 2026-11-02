"""第 24 集 差分约束：不等式就是最短路的三角形"""

from episodes.common import *

# 约束 x_v − x_u ≤ w，写成 (u, v, w)
CONS = [(1, 2, 3), (2, 3, -1), (1, 3, 1), (3, 4, 2), (4, 1, -2)]
POS = {0: (-430, 0), 1: (-170, -190), 2: (170, -190), 3: (170, 190), 4: (-170, 190)}


def bellman_ford(cons, n):
    edges = list(cons) + [(0, i, 0) for i in range(1, n + 1)]
    d = {0: 0}
    for i in range(1, n + 1):
        d[i] = float("inf")
    rounds = []
    for r in range(n + 1):
        changed = []
        for u, v, w in edges:
            if d[u] + w < d[v]:
                d[v] = d[u] + w
                changed.append((u, v))
        rounds.append((dict(d), changed))
        if not changed:
            break
    neg = bool(rounds[-1][1]) and len(rounds) == n + 1
    return d, rounds, neg


def build(S):
    S.cover("给出一组形如 xᵥ − xᵤ ≤ w 的不等式，求一组满足所有不等式的解，或者判断无解。这和最短路有什么关系？",
            ["最短路与 Bellman-Ford", "负环"])

    # ------------------------------------------------------------ 问题
    S.section("问题：一组差分不等式")
    S.say("有 4 个未知数 x₁…x₄，以及下面 5 条约束，每条都是“两个未知数之差不超过某个数”。")
    lines = [f"x{v} − x{u} ≤ {w}" for u, v, w in CONS]
    ts = [label(320, 230 + i * 70, s, 32, FG, chain="mono") for i, s in enumerate(lines)]
    S.show(*ts, lag=0.15)
    S.note("约束：xᵥ − xᵤ ≤ w；求一组解或判定无解")
    S.say("比如“x₃ − x₂ ≤ −1”就是“x₃ 至少比 x₂ 小 1”。排日程、安排时刻表时经常遇到这种约束。")
    S.say("看一眼最短路：算完最短路后，对每条边 u → v（边权 w）一定有 d[v] ≤ d[u] + w，否则还能再松弛。")
    S.note("最短路的三角形不等式：d[v] ≤ d[u] + w(u, v)", color=Y)
    S.say("把它移项：d[v] − d[u] ≤ w。和约束 xᵥ − xᵤ ≤ w 一模一样！")
    S.note("xᵥ − xᵤ ≤ w ⇔ 建边 u → v，边权 w", color=Y)

    # ------------------------------------------------------------ 建图
    S.section("建图：每条约束一条边")
    g = Graph(POS, [(u, v, w) for u, v, w in CONS], x=560, y=470, directed=True, r=32, size=26, wsize=26, wcolor=FG,
              labels={0: "0", 1: "x₁", 2: "x₂", 3: "x₃", 4: "x₄"})
    g[0].tr["op"].base = 0
    S.show(g)
    S.say("每条约束 xᵥ − xᵤ ≤ w 建一条边 u → v，权值 w。注意方向：被减的 xᵤ 是起点。")
    S.say("再加一个超级源点 0，向每个变量连一条权值 0 的边。这相当于多加约束 xᵢ − x₀ ≤ 0，保证从 0 出发能到达每个点。")
    src = []
    for i in range(1, 5):
        ln = Line(color=alpha(CY, 0.6), w=2.5, head=12, dash=(8, 6)).attach(g[0], g[i])
        ln.tr["op"].base = 0
        g.add(ln)
        src.append(ln)
    S.play(FadeIn(g[0]), *[FadeIn(l_) for l_ in src], dur=0.6)
    S.note("超级源点 0 → 每个变量，权 0（相当于 xᵢ ≤ x₀）")
    S.say("从 0 跑最短路（有负权，用 Bellman-Ford），令 xᵢ = d[i]。由三角形不等式，所有约束自动满足。")
    S.note("令 xᵢ = d[i] → 所有约束成立", color=G)

    # ------------------------------------------------------------ Bellman-Ford
    S.section("跑一遍 Bellman-Ford")
    S.wide()
    g2 = Graph(POS, [(u, v, w) for u, v, w in CONS], x=520, y=470, directed=True, r=32, size=26, wsize=26, wcolor=FG,
               labels={0: "0", 1: "x₁", 2: "x₂", 3: "x₃", 4: "x₄"})
    for i in range(1, 5):
        ln = Line(color=alpha(CY, 0.6), w=2.5, head=12, dash=(8, 6)).attach(g2[0], g2[i])
        g2.add(ln)
    S.show(g2)
    d, rounds, neg = bellman_ford(CONS, 4)
    tags = {i: g2.tag(i, "∞" if i else "0", "u" if POS[i][1] < 0 else "d", Y, 26, gap=8) for i in POS}
    S.play(*[FadeIn(t) for t in tags.values()], dur=0.4)
    tbl = Grid(len(rounds), 4, x=1420, y=500, cw=100, ch=58, gap=4, size=26, rlab=[f"第{r + 1}轮" for r in range(len(rounds))],
               clab=["x₁", "x₂", "x₃", "x₄"])
    S.show(tbl)
    S.say("Bellman-Ford：每一轮把所有边都松弛一遍。右边表格记录每轮结束时的 d。")
    for r, (dd, changed) in enumerate(rounds):
        S.play(*[g2.edge(u, v).to(color=Y, w=5) for u, v in changed if u != 0], dur=0.4)
        S.play(*[tags[i].to(text=str(dd[i])) for i in range(1, 5)],
               *[tbl[(r, i - 1)].to(text=str(dd[i])) for i in range(1, 5)], dur=0.5)
        S.play(*[g2.edge(u, v).to(color=C.LINE2, w=3) for u, v in changed if u != 0], dur=0.2)
        if r == 0:
            S.say("第一轮：变量都是 ∞，约束边松弛不动，只有源点的边把它们都设成 0。")
        elif r == 1:
            S.say("第二轮：负权的约束边开始起作用，x₃ 被压到 −1，x₁ 被压到 −2。再来一轮，什么都没变，结束。")
        S.wait(0.4)
    sol = [d[i] for i in range(1, 5)]
    S.say(f"稳定后得到 x = ({', '.join(map(str, sol))})。逐条代入检查：" +
          "；".join(f"x{v} − x{u} = {d[v] - d[u]} ≤ {w}" for u, v, w in CONS[:3]) + "……全部成立。")
    for u, v, w in CONS:
        assert d[v] - d[u] <= w
    S.say("这组解还有个性质：在“xᵢ ≤ 0”的前提下，每个 xᵢ 都取到了能取的最大值（最短路给出的是“最紧的上界”）。整体加同一个常数仍然是解。")

    # ------------------------------------------------------------ 负环
    S.section("负环 ⇔ 无解")
    S.narrow()
    S.say("如果约束互相矛盾呢？例如 x₂ − x₁ ≤ 1，x₃ − x₂ ≤ −2，x₁ − x₃ ≤ 0。")
    cpos = {1: (-200, 120), 2: (0, -160), 3: (200, 120)}
    cg = Graph(cpos, [(1, 2, 1), (2, 3, -2), (3, 1, 0)], x=560, y=470, directed=True, r=34, size=26, wsize=28, wcolor=FG,
               labels={1: "x₁", 2: "x₂", 3: "x₃"})
    S.show(cg)
    S.say("建出图来是一个环，边权之和 1 + (−2) + 0 = −1 < 0，是负环。")
    S.play(*[cg.edge(a, b).to(color=R, w=6) for a, b in [(1, 2), (2, 3), (3, 1)]], dur=0.6)
    S.say("把环上三条约束加起来：左边 (x₂ − x₁) + (x₃ − x₂) + (x₁ − x₃) = 0，右边是 −1，得到 0 ≤ −1，矛盾。所以有负环一定无解。")
    S.note("负环：把环上的约束相加得 0 ≤ 负数 → 无解", color=R)
    S.say("反过来，没有负环时最短路存在，按上面的方法就能构造出解。所以：有解 ⇔ 图中没有负环。")
    S.note("有解 ⇔ 没有负环（Bellman-Ford 第 n 轮还能松弛就是负环）", color=Y)

    # ------------------------------------------------------------ 转化
    S.section("各种不等式的转化")
    S.say("实际题目里的约束不一定是“≤”的标准形式，要先转化：")
    S.note("xᵥ − xᵤ ≥ w ⇔ xᵤ − xᵥ ≤ −w（边 v → u，权 −w）")
    S.note("xᵥ = xᵤ ⇔ xᵥ − xᵤ ≤ 0 且 xᵤ − xᵥ ≤ 0")
    S.note("整数且 xᵥ − xᵤ < w ⇔ xᵥ − xᵤ ≤ w − 1")
    S.note("xᵢ ≤ c ⇔ xᵢ − x₀ ≤ c（借助源点 x₀ = 0）")
    S.say("“≥” 就把两边同乘 −1；等式拆成两个不等式；整数的严格不等式减 1；单个变量的上下界借助一个固定为 0 的源点。")
    S.say("如果要求某个量的最小值，常把所有约束改写成“≥”的形式求{y|最长路}，原理完全对称。", extra=0.5)
    S.note("求最小值：写成 ≥，跑最长路", color=CY)

    # ------------------------------------------------------------ 手推题
    S.quiz("区间选点：在整数 0~10 中选一些数，要求满足若干条“区间 [a, b] 里至少选 c 个”的约束，问最少选几个。\n\n"
           "提示：设 Sᵢ = 0~i 中选了几个（S₋₁ = 0）。\n"
           "(1) 约束“[a, b] 至少选 c 个”怎样写成差分约束？\n"
           "(2) 还有哪些“隐含”的约束？答案是什么？", think=20)
    S.say("(1) [a, b] 里选的个数是 S_b − S_{a−1}，所以约束是 S_b − S_{a−1} ≥ c。")
    S.note("(1) S_b − S_{a−1} ≥ c", color=Y)
    S.say("(2) 每个数要么选要么不选：0 ≤ Sᵢ − Sᵢ₋₁ ≤ 1。这两条很容易漏掉，没有它们，解可能出现“选了负数个”。")
    S.note("(2) 隐含：0 ≤ Sᵢ − Sᵢ₋₁ ≤ 1", color=Y)
    S.say("所有约束都是差分约束。要 S₁₀ 最小，就把它们写成“≥”的形式，从 S₋₁ 出发求到 S₁₀ 的最长路。")
    S.note("求 S₁₀ 的最小值 = 最长路", color=G)

    S.recap([
        "最短路满足三角形不等式 d[v] ≤ d[u] + w，正好是差分约束 xᵥ − xᵤ ≤ w 的形式。",
        "每条约束建边 u → v（权 w），加超级源点，跑 Bellman-Ford，xᵢ = d[i] 就是一组解。",
        "有解 ⇔ 没有负环：环上的约束相加会得到 0 ≤ 负数。",
        "≥、=、严格不等号、单变量界都能转成标准形式；求最小值用最长路。",
    ], next_title="强连通分量：Tarjan 的 low 在找什么")
