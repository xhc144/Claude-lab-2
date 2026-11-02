"""第 51 集 点分治：经过重心的路径"""

from itertools import combinations

from episodes.common import *

EDGES = [(1, 2), (2, 3), (3, 4), (4, 5), (3, 6), (6, 7), (4, 8), (2, 9), (5, 10)]
N = 10
KD = 3


def adj_of():
    adj = {i: [] for i in range(1, N + 1)}
    for u, v in EDGES:
        adj[u].append(v)
        adj[v].append(u)
    return adj


ADJ = adj_of()


def bfs(s, allowed):
    d = {s: 0}
    q = [s]
    for x in q:
        for y in ADJ[x]:
            if y in allowed and y not in d:
                d[y] = d[x] + 1
                q.append(y)
    return d


def comps_without(c, comp):
    out = []
    for y in ADJ[c]:
        if y in comp:
            out.append(set(bfs(y, comp - {c})))
    return out


def centroid(comp):
    return min(comp, key=lambda c: (max([len(s) for s in comps_without(c, comp)] or [0]), c))


def count_through(c, comp, k):
    d = bfs(c, comp)
    A = sum(1 for u, v in combinations(comp, 2) if d[u] + d[v] <= k)
    B = sum(sum(1 for u, v in combinations(sub, 2) if d[u] + d[v] <= k) for sub in comps_without(c, comp))
    return d, A, B


def build(S):
    S.cover("树上有多少对点的距离不超过 K？枚举点对是 O(n²)。把“所有路径”按“经过哪个点”分类，再用重心保证分治的层数只有 log n。",
            ["树形 DP（第 7 集）", "双指针 / 排序"])

    allv = set(range(1, N + 1))
    D = {u: bfs(u, allv) for u in allv}
    total = sum(1 for u, v in combinations(allv, 2) if D[u][v] <= KD)
    tr = Tree(EDGES, 1, x=470, y=470, w=760, h=560, r=30, size=24)

    # ------------------------------------------------------------ 分类
    S.section("把路径按“经过哪个点”分类")
    S.show(tr)
    S.say(f"这棵树有 {N} 个点，边长都是 1。问：距离 ≤ {KD} 的点对有几对？（答案是 {total}。）")
    S.note(f"问题：距离 ≤ K 的点对数（K = {KD}）", color=Y)
    S.say("任选一个点 c。所有路径分成两类：经过 c 的；完全在删掉 c 之后的某一个连通块里的。")
    S.note("路径 = 经过 c 的 + 完全在某个子树里的（递归）", color=G)
    S.say("第二类正好是若干个规模更小的同类问题，递归去做。只要能高效地数出“经过 c 的”，就得到一个分治算法。")
    S.say("可是 c 选不好，比如一条链总选端点，每次只少一个点，要递归 n 层。怎么选 c 才能让每层都变小很多？", extra=0.3)

    # ------------------------------------------------------------ 重心
    S.section("选重心：每块不超过一半", keep=[tr])
    c = centroid(allv)
    parts = comps_without(c, allv)
    S.say("重心：删掉它之后，剩下的每个连通块都不超过 n/2 个点。")
    S.note("重心：删掉后每个连通块 ≤ n/2", color=Y)
    worst = {}
    for v in sorted(allv):
        worst[v] = max(len(s_) for s_ in comps_without(v, allv))
    tags = {v: tr.tag(v, str(worst[v]), "r", DIM, 20, gap=6) for v in allv}
    S.play(*[FadeIn(t) for t in tags.values()], dur=0.6)
    S.say("每个点旁边写的是“删掉它之后最大的连通块大小”。最小的那个点就是重心。")
    S.play(tr[c].to(fill=tint(Y, 0.5), stroke=Y), tags[c].to(color=Y), dur=0.5)
    cols = [CY, O, G, K]
    for s_, col in zip(parts, cols):
        S.play(*[tr[v].to(fill=tint(col, 0.35)) for v in s_], dur=0.4)
    S.say(f"点 {c}：删掉后剩下大小 {', '.join(str(len(s_)) for s_ in parts)} 的三块，都不超过 {N}/2 = {N // 2}。")
    S.say("重心一定存在：从任一点出发，只要有一块超过一半，就往那一块走一步；那一块越走越小，最后一定停下。用一次 DFS 算子树大小就能找到。")
    S.note("找重心：DFS 求子树大小，O(n)", color=G)
    S.say("每次都选重心，递归一层规模至少减半，所以递归深度不超过 log₂ n——每个点只会出现在 O(log n) 层里。", extra=0.3)
    S.note("递归深度 ≤ log₂ n", color=G)

    # ------------------------------------------------------------ 统计
    S.section("数经过重心的点对", keep=[tr])
    d, A, B = count_through(c, allv, KD)
    for v in allv:
        S.play(tags[v].to(text=f"d={d[v]}", color=Y), dur=0.05)
    S.say(f"以重心 {c} 为起点算出每个点的深度 d。经过 {c} 的路径 u—v 长度是 d(u) + d(v)，问题变成：有多少对 d(u) + d(v) ≤ {KD}？")
    S.note("经过 c：d(u) + d(v) ≤ K", color=Y)
    ds = sorted(d[v] for v in allv)
    arr = Array(ds, x=1060, y=260, cw=40, ch=48, gap=5, size=22, index=False, fill=tint(Y, 0.15))
    S.show(arr, label(1060, 200, "所有深度（排好序）", 22, DIM))
    S.say(f"把深度排序，用双指针数满足条件的对数，得 {A} 对。（重心自己 d = 0，也参与配对：它和深度 ≤ {KD} 的点都算。）")
    S.note(f"排序 + 双指针：O(m log m)，这里 {A} 对", color=Y)
    S.say(f"但这样会多算：同一块里的两个点（同色），d(u) + d(v) ≤ {KD}，它们的真实路径并不经过 {c}。")
    S.say(f"容斥：对每一块单独用同样的深度再数一遍（都是相对 {c} 的深度），共 {B} 对，减掉。")
    S.note("减去同一子树内的“假”点对（用同样的 d 再数一遍）", color=R)
    true_through = sum(1 for u, v in combinations(allv, 2) if D[u][v] <= KD and D[u][c] + D[c][v] == D[u][v])
    assert A - B == true_through
    S.say(f"经过 {c} 的点对 = {A} − {B} = {A - B}。剩下的在三块里各自递归，每块再找自己的重心。")
    S.note(f"经过重心：{A} − {B} = {A - B}", color=G)
    S.say("每一层所有块的大小加起来不超过 n，排序共 O(n log n)；一共 log n 层：总 O(n log² n)。", extra=0.3)
    S.note("总复杂度 O(n log² n)")

    # ------------------------------------------------------------ 手推题
    K2 = 2
    d2, A2, B2 = count_through(c, allv, K2)
    tot2 = sum(1 for u, v in combinations(allv, 2) if D[u][v] <= K2)
    S.quiz(f"还是这棵树，K 改成 {K2}。\n\n"
           f"(1) 以重心 {c} 为根，满足 d(u) + d(v) ≤ {K2} 的点对有几对？\n"
           "(2) 其中有几对在同一块里（要减掉）？经过重心的有几对？\n"
           "(3) 递归下去，三块里还要找哪些点作重心？", think=20)
    assert A2 == 11 and B2 == 0
    S.say(f"(1) 深度：0 一个（重心），1 三个，2 五个，3 一个。d(u) + d(v) ≤ {K2}：重心配深度 ≤ 2 的 8 个，深度 1 之间互配 C(3, 2) = 3 对，共 {A2} 对。")
    S.say(f"(2) 同一块里的：只有两个深度 1 的点在同一块时才会 ≤ 2，而三个深度 1 的点各在一块，所以 {B2} 对。经过重心的 {A2 - B2} 对。")
    S.note(f"(1) {A2} 对；(2) 减 {B2}，经过重心 {A2 - B2} 对", color=Y)
    subs = [centroid(s_) for s_ in parts]
    S.say("(3) 三块各自的重心：" + "、".join(f"{{{', '.join(map(str, sorted(s_)))}}} 里是 {cc}" for s_, cc in zip(parts, subs)) + "。")
    S.say(f"全部加起来：距离 ≤ {K2} 的点对共有 {tot2} 对。", extra=0.5)
    S.note("(3) 各块重心：" + "、".join(map(str, subs)), color=G)

    S.recap([
        "路径按“是否经过 c”分类：经过 c 的直接数，其余在删掉 c 后的各块里递归。",
        "c 取重心：删掉后每块 ≤ n/2，递归深度 O(log n)。",
        "经过重心：按深度数 d(u) + d(v) ≤ K 的对数，再减掉同一块里的“假”点对（容斥）。",
        "每层 O(n log n)，共 O(n log² n)。",
    ], next_title="虚树")
