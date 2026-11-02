"""第 8 集 换根 DP：让每个点都当一次根"""

from collections import deque

from episodes.common import *

EDGES = [(1, 2), (1, 3), (1, 4), (2, 5), (2, 6), (4, 7), (7, 8)]
N = 8


def rooted(edges, root):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    par, order = {root: None}, [root]
    for u in order:
        for v in adj[u]:
            if v not in par:
                par[v] = u
                order.append(v)
    ch = {u: [v for v in adj[u] if par.get(v) == u] for u in adj}
    return par, order, ch, adj


def dist_sum_dp():
    par, order, ch, adj = rooted(EDGES, 1)
    size, down = {}, {}
    for u in reversed(order):
        size[u] = 1 + sum(size[c] for c in ch[u])
        down[u] = sum(down[c] + size[c] for c in ch[u])
    ans = {1: down[1]}
    for u in order:
        for c in ch[u]:
            ans[c] = ans[u] - size[c] + (N - size[c])
    # 用 BFS 验证
    for s in adj:
        d = {s: 0}
        q = deque([s])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in d:
                    d[y] = d[x] + 1
                    q.append(y)
        assert sum(d.values()) == ans[s]
    return par, order, ch, size, down, ans


def ecc_dp():
    par, order, ch, adj = rooted(EDGES, 1)
    d1, d2, via = {}, {}, {}
    for u in reversed(order):
        best = [(0, None), (0, None)]
        for c in ch[u]:
            v = d1[c] + 1
            if v > best[0][0]:
                best = [(v, c), best[0]]
            elif v > best[1][0]:
                best[1] = (v, c)
        d1[u], via[u], d2[u] = best[0][0], best[0][1], best[1][0]
    up = {1: 0}
    for u in order:
        for c in ch[u]:
            other = d2[u] if via[u] == c else d1[u]
            up[c] = 1 + max(up[u], other)
    ecc = {u: max(d1[u], up[u]) for u in order}
    return d1, d2, via, up, ecc


def build(S):
    S.cover("树上每个点到其他所有点的距离之和是多少？要对所有点都求，能不能比做 n 次 DFS 更快？",
            ["树形 DP（第 7 集）", "子树大小 size"])

    par, order, ch, size, down, ans = dist_sum_dp()

    # ------------------------------------------------------------ 问题
    S.section("问题：每个点的距离和")
    tree = Tree(EDGES, 1, x=420, y=470, w=560, h=440, r=30, size=26)
    S.show(tree)
    S.say("一棵 8 个点的树，边长都是 1。对每个点 v，求 S(v) = v 到所有点的距离之和。")
    S.note("S(v) = Σ dist(v, u)，对每个 v 都要求")
    S.say("一个点的 S 很好算：从它出发做一次 DFS。但对每个点都做一次是 O(n²)，n = 10⁶ 时不行。")
    S.note("朴素：n 次 DFS，O(n²)", color=R)
    S.say("思路：先以 1 为根算出 S(1)，再想办法从 S(父亲) 一步推出 S(儿子)。")

    # ------------------------------------------------------------ 向下
    S.section("第一遍：向下汇总", keep=[tree])
    S.say("第一遍 DFS 算两样东西：子树大小 size[u]，以及 down[u] = u 到它子树里所有点的距离和。")
    S.note("size[u]：u 子树的点数")
    S.note("down[u] = Σ dist(u, x)，x 取遍 u 的子树")
    S.say("down 怎么合并？儿子 c 子树里的每个点，到 u 都比到 c 多走一步，一共多出 size[c]。")
    S.note("down[u] = Σ_c ( down[c] + size[c] )", color=Y)
    tgs = {v: tree.tag(v, "", "r" if ch[v] else "d", CY, 22) for v in order}
    for u in reversed(order):
        S.play(FadeIn(tgs[u]), tgs[u].to(text=f"size={size[u]} down={down[u]}"), tree[u].to(stroke=CY), dur=0.35)
    S.say(f"根 1 的 down 就是 S(1) = {down[1]}。")
    S.play(tree[1].to(fill=tint(Y, 0.45), stroke=Y), dur=0.4)

    # ------------------------------------------------------------ 换根
    S.section("第二遍：把根挪到儿子", keep=[tree])
    S.play(*[FadeOut(t) for t in tgs.values()], dur=0.3)
    S.say("现在把根从 u = 1 挪到儿子 c = 4。到每个点的距离怎么变？")
    sub = tree.subtree(4)
    S.play(*[tree[v].to(fill=tint(CY, 0.5), stroke=CY) for v in sub], tree[1].to(fill=BG3, stroke=LINE2), dur=0.5)
    S.play(*[tree[v].to(fill=tint(O, 0.45), stroke=O) for v in order if v not in sub], dur=0.5)
    S.play(tree.edge(1, 4).to(color=Y, w=6), dur=0.4)
    S.say(f"4 的子树里的 {size[4]} 个点（青色）：从 4 出发比从 1 出发{{c|近 1 步}}。其余 {N - size[4]} 个点（橙色）：要多走边 (1, 4)，{{o|远 1 步}}。")
    S.note("根 u → 儿子 c：c 子树里 size[c] 个点近 1，其余 n − size[c] 个点远 1")
    S.note("S(c) = S(u) − size[c] + (n − size[c])", color=Y)
    S.say(f"所以 S(4) = S(1) − {size[4]} + {N - size[4]} = {down[1]} − {size[4]} + {N - size[4]} = {ans[4]}。一步就算完。")
    S.say("第二遍 DFS 从根往下，用这个式子把每个点的答案依次推出来。两遍都是 O(n)。")
    S.play(*[tree[v].to(fill=BG3, stroke=LINE2) for v in order], tree.edge(1, 4).to(color=LINE2, w=3), dur=0.4)
    at = {v: tree.tag(v, "", "r" if ch[v] else "d", Y, 24) for v in order}
    S.play(FadeIn(at[1]), at[1].to(text=f"S={ans[1]}"), dur=0.4)
    for u in order:
        for c in ch[u]:
            S.play(tree.edge(u, c).to(color=Y, w=5), dur=0.25)
            S.play(FadeIn(at[c]), at[c].to(text=f"S={ans[c]}"), tree.edge(u, c).to(color=LINE2, w=3), dur=0.4)
    best = min(ans, key=lambda v: ans[v])
    S.say(f"S 最小的是点 {best}（{ans[best]}）。每个值都可以用 BFS 核对。")
    S.play(tree[best].flash(Y), dur=0.8)
    S.say("这个公式还说明：当 size[c] > n/2 时，把根移到 c 会让 S 变小。所以 S 最小的点就是树的重心。")
    S.note("size[c] > n/2 ⇒ 往 c 走更好 → 最优点是重心", color=G)

    # ------------------------------------------------------------ 一般化
    S.section("换根的一般形式")
    S.say("一般地，以 c 为根的答案由两部分拼成：c 自己子树里的信息 down[c]，和“c 子树以外”的信息 up[c]。")
    S.note("ans[c] = 合并( down[c], up[c] )")
    S.note("up[c]：从 c 往上看，树的其余部分的信息")
    S.say("up[c] 来自父亲 u：u 往上的部分 up[u]，加上 u 的{y|其他}儿子的子树。关键操作是“从 u 的总信息里去掉儿子 c 的贡献”。")
    S.note("关键：从 u 的信息里去掉儿子 c 的贡献", color=Y)
    S.say("距离和是加法，去掉一个儿子的贡献就是减法，所以很容易。但如果信息是最大值呢？最大值不能“减”。")
    S.note("加法：可减 ✓　最大值：不可减 ✗", color=R)

    d1, d2, via, up, ecc = ecc_dp()
    S.say("例：求每个点到最远点的距离（离心率）。down 部分是“向下最长的路” d1[u]。")
    tree2 = Tree(EDGES, 1, x=420, y=470, w=560, h=440, r=30, size=26)
    S.clear(dur=0.4)
    S.show(tree2)
    S.say("算 up[4]：要知道 1 的其他儿子方向最远能走多远。1 向下最长的路恰好经过 4（长度 3），去掉 4 之后要用{y|次长}的那条（经过 2，长度 2）。")
    S.play(tree2.edge(1, 4).to(color=R, w=5), tree2.edge(4, 7).to(color=R, w=5), tree2.edge(7, 8).to(color=R, w=5), dur=0.6)
    S.play(tree2.edge(1, 2).to(color=G, w=5), tree2.edge(2, 5).to(color=G, w=5), dur=0.6)
    S.note("最大值：同时记最长 d1[u] 和次长 d2[u]（以及最长来自哪个儿子）", color=G)
    S.note("up[c] = 1 + max( up[u], (c 是最长的来源 ? d2[u] : d1[u]) )")
    S.say(f"所以 up[4] = 1 + max(up[1], d2[1]) = 1 + max(0, {d2[1]}) = {up[4]}，离心率 = max(d1[4], up[4]) = max({d1[4]}, {up[4]}) = {ecc[4]}。")
    S.play(*[tree2.edge(a, b).to(color=LINE2, w=3) for a, b in EDGES], dur=0.3)
    et = {v: tree2.tag(v, "", "r" if ch[v] else "d", Y, 24) for v in order}
    S.play(*[FadeIn(et[v]) for v in order], *[et[v].to(text=f"{ecc[v]}") for v in order], dur=0.8, lag=0.05)
    S.say("如果信息更复杂，可以对每个点的儿子做前缀合并和后缀合并：去掉第 i 个儿子 = 前 i−1 个的前缀 ⊕ 后面的后缀。只要求合并满足结合律。")
    S.note("一般方法：儿子的前缀合并 + 后缀合并，“挖掉”任意一个儿子", color=CY)

    # ------------------------------------------------------------ 手推题
    S.quiz("每个点 x 上住着 a_x 个人，边长都是 1。要选一个点 v 开会，使所有人走的总路程\n"
           "T(v) = Σ a_x × dist(v, x) 最小。\n\n"
           "(1) 把根从 u 挪到儿子 c，T 怎么变？（记 A = 总人数，A[c] = c 子树里的人数）\n"
           "(2) 由此说明：最优的点满足什么条件？", think=20)
    S.say("(1) c 子树里的 A[c] 个人各少走 1 步，其余 A − A[c] 个人各多走 1 步。")
    S.note("T(c) = T(u) − A[c] + (A − A[c]) = T(u) + A − 2A[c]", color=Y)
    S.say("(2) 当 A[c] > A/2 时，挪到 c 会让 T 变小。所以最优点 v 满足：以 v 为根时，每个儿子子树里的人数都不超过 A/2。")
    S.note("最优点：每棵子树的人数 ≤ A/2（带权重心）", color=G)
    S.say("这就是“带权重心”。换根公式不只是算答案的工具，它的形式本身就揭示了最优解的结构。", extra=0.5)

    S.recap([
        "换根 DP：第一遍向下求 down（子树内的信息），第二遍向下用父亲的答案推出儿子的答案。",
        "距离和：S(c) = S(u) − size[c] + (n − size[c])，两遍 DFS，O(n)。",
        "一般形式：ans[c] = 合并(down[c], up[c])；关键是从父亲的信息里去掉儿子 c 的贡献。",
        "可减的信息直接减；最大值记最长和次长；更一般地用儿子的前缀、后缀合并。",
    ], next_title="状态压缩 DP（上）：把集合放进状态")
