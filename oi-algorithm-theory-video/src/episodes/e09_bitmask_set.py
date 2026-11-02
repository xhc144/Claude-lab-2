"""第 9 集 状态压缩 DP（上）：把集合放进状态"""

import math

from episodes.common import *

D = [[0, 2, 9, 4],
     [2, 0, 3, 7],
     [9, 3, 0, 1],
     [4, 7, 1, 0]]
N = 4
POS = {0: (-170, -150), 1: (170, -150), 2: (170, 150), 3: (-170, 150)}
EDGES = [(0, 1, 2), (0, 2, 9), (0, 3, 4), (1, 2, 3), (1, 3, 7), (2, 3, 1)]
INF = float("inf")
WPOS = {(0, 2): 0.28, (1, 3): 0.28}


def tsp():
    f = {(1, 0): 0}
    src = {}
    for S_ in range(1, 1 << N):
        if not S_ & 1:
            continue
        for v in range(N):
            if not (S_ >> v) & 1 or (S_, v) not in f:
                continue
            for u in range(N):
                if (S_ >> u) & 1:
                    continue
                T_ = S_ | (1 << u)
                val = f[(S_, v)] + D[v][u]
                if val < f.get((T_, u), INF):
                    f[(T_, u)] = val
                    src[(T_, u)] = (S_, v)
    full = (1 << N) - 1
    end = min(range(1, N), key=lambda v: f[(full, v)])
    path = [(full, end)]
    while path[-1] in src:
        path.append(src[path[-1]])
    return f, src, end, [v for _, v in reversed(path)]


def bits(S_):
    return "".join("1" if (S_ >> b) & 1 else "0" for b in range(N - 1, -1, -1))


def pent(r=190):
    return {i: (r * math.cos(-math.pi / 2 + 2 * math.pi * i / 5), r * math.sin(-math.pi / 2 + 2 * math.pi * i / 5))
            for i in range(5)}


def build(S):
    S.cover("从城市 0 出发，经过全部 n 个城市各一次，最短要走多远？n ≤ 20 时，状态里该记什么？",
            ["DP 合并“未来相同的历史”（第 2 集）", "二进制与位运算"])

    # ------------------------------------------------------------ 问题
    S.section("问题：最短哈密顿路")
    g = Graph(POS, EDGES, x=380, y=480, r=34, size=28, wsize=24, wpos=WPOS)
    S.show(g)
    S.say("4 个城市，两两之间的距离标在边上。从城市 0 出发，每个城市恰好经过一次，路线最短是多少？（终点任意）")
    S.note("从 0 出发，经过每个城市恰好一次，求最短路线")
    S.say("枚举所有顺序要 (n−1)! 种。n = 20 时约 1.2×10¹⁷，不可能。要找能合并的东西。")
    S.note("枚举顺序：(n−1)!，n = 20 时 ≈ 1.2×10¹⁷", color=R)

    # ------------------------------------------------------------ 状态
    S.section("状态：走过的集合 + 现在的位置")
    pp = pent()
    g5 = Graph(pp, [(a, b) for a in range(5) for b in range(a + 1, 5)], x=380, y=490, r=32, size=26,
               ecolor=alpha(LINE2, 0.35), ew=2)
    S.show(g5)
    S.say("换成 5 个城市来看。走到一半时，要决定接下来怎么走，需要知道过去的什么？")
    S.say("两样东西：现在在哪个城市（下一步的距离从这里算），以及{y|哪些城市已经去过}（不能再去，剩下的必须去）。")
    S.note("未来只取决于：当前城市 v + 已访问集合 S", color=Y)
    S.say("先看可以合并的：0→1→2→3 和 0→2→1→3，都停在 3，都去过 {0, 1, 2, 3}。剩下的都只有城市 4，未来完全一样。")
    ra = label(840, 330, "0→1→2→3", 30, CY, anchor="lm")
    rb = label(840, 400, "0→2→1→3", 30, O, anchor="lm")
    S.play(*[g5.edge(a, b).to(color=CY, w=6) for a, b in [(0, 1), (1, 2), (2, 3)]], FadeIn(ra), dur=0.6)
    S.wait(1.0)
    S.play(*[g5.edge(a, b).to(color=alpha(LINE2, 0.35), w=2) for a, b in [(0, 1), (1, 2), (2, 3)]], dur=0.3)
    S.play(*[g5.edge(a, b).to(color=O, w=6) for a, b in [(0, 2), (2, 1), (1, 3)]], FadeIn(rb), dur=0.6)
    S.play(g5[3].flash(Y), g5[4].flash(G), dur=0.8)
    S.say("所以只要留下两条里较短的那条。经过的{y|顺序}不需要进状态。")
    S.note("顺序不进状态：同集合、同终点的路线只留最短的", color=G)
    S.play(FadeOut(ra, rb), dur=0.3)
    S.play(*[g5.edge(a, b).to(color=alpha(LINE2, 0.35), w=2) for a in range(5) for b in range(a + 1, 5)], dur=0.4)
    S.say("那能不能只记“去过几个城市”，不记是哪几个？看 0→1→2 和 0→3→2：都停在 2，都去过 3 个城市。")
    S.play(*[g5.edge(a, b).to(color=CY, w=6) for a, b in [(0, 1), (1, 2)]], dur=0.5)
    S.play(*[g5.edge(a, b).to(color=O, w=6) for a, b in [(0, 3), (3, 2)]], dur=0.5)
    la = label(840, 330, "0→1→2：还剩 {3, 4}", 30, CY, anchor="lm")
    lb = label(840, 400, "0→3→2：还剩 {1, 4}", 30, O, anchor="lm")
    S.show(la, lb)
    S.say("剩下要去的城市不同，未来不同，不能合并。所以只记个数不够，必须记住是{y|哪一个集合}。")
    S.note("只记个数 ✗：剩下的城市不同，未来不同", color=R)
    S.note("{y|f[S][v]}：从 0 出发，恰好走过集合 S，停在 v 的最短长度", color=Y)

    # ------------------------------------------------------------ 二进制
    S.section("用二进制表示集合")
    S.say("集合怎么当数组下标？n 个城市，每个城市在或不在，正好是 n 位二进制数。第 i 位是 1 就表示城市 i 在集合里。")
    S.note("集合 S ↔ n 位二进制数：第 i 位 = 城市 i 在不在")
    bit = Array(["0", "1", "1", "1"], x=520, y=380, cw=96, ch=80, gap=8, size=36, base=0,
                idx_labels=["城市 3", "城市 2", "城市 1", "城市 0"])
    S.show(bit)
    for i, c in enumerate(bit.cells):
        if c.label.g("text", 0) == "1":
            S.play(c.to(fill=tint(Y, 0.4)), dur=0.15)
    eq = label(520, 520, "0111₂ = 7 表示 {0, 1, 2}", 32, Y)
    S.show(eq)
    S.say("于是 f[S][v] 就是普通的二维数组 f[0..2ⁿ−1][0..n−1]。判断 u 在不在 S 里、把 u 加进 S，都是一次位运算。")
    S.note("u 在 S 中：S 的第 u 位为 1；加入 u：S | (1 << u)")
    S.say("转移：从 f[S][v] 出发，走到一个没去过的城市 u：f[S ∪ {u}][u] ← f[S][v] + d(v, u)。")
    S.note("f[S∪{u}][u] = min( f[S][v] + d(v, u) )，u ∉ S", color=Y)
    S.say("按什么顺序算？把 u 加进 S，二进制数一定变大。所以只要按 S 从小到大的顺序算，用到的状态都已经算好了。")
    S.note("顺序：S 从小到大（加一个元素，数值一定变大）", color=G)

    # ------------------------------------------------------------ 推表
    S.section("推一遍")
    f, src, end, path = tsp()
    S.wide()
    g4 = Graph(POS, EDGES, x=330, y=470, r=30, size=26, wsize=22, wpos=WPOS)
    g4.tr["sc"].base = 0.85
    masks = [m for m in range(1, 1 << N) if m & 1]
    tbl = Grid(len(masks), N, x=1180, y=500, cw=110, ch=58, gap=4, size=26,
               rlab=[f"{bits(m)}" for m in masks], clab=[f"v={v}" for v in range(N)], lab_size=24,
               lab_color=FG)
    for i, m in enumerate(masks):
        for v in range(N):
            if not (m >> v) & 1:
                tbl[i, v].box.tr["fill"].base = alpha(BG3, 0.35)
                tbl[i, v].label.tr["text"].base = ""
    S.show(g4, tbl)
    lab = label(1180, 140, "行：集合 S（二进制，最低位是城市 0）　列：停在 v", 24, DIM)
    S.show(lab)
    S.say("表的每一行是一个包含城市 0 的集合，按数值从小到大排；暗格表示 v 不在 S 里，没有意义。")
    S.play(tbl[0, 0].to(text="0", fill=tint(G, 0.35)), dur=0.5)
    S.say("起点：f[0001][0] = 0。然后一行一行往下算。")
    row_of = {m: i for i, m in enumerate(masks)}
    detail = (0b0111, 2)
    for m in masks[1:]:
        for v in range(N):
            if not (m >> v) & 1 or (m, v) not in f:
                continue
            c = tbl[row_of[m], v]
            if (m, v) == detail:
                prev = m & ~(1 << v)
                S.say(f"例：f[0111][2]，走过 {{0, 1, 2}}、停在 2。上一步的集合是 0011，只能停在 1（停在 0 就说明 1 没去过），"
                      f"所以 f[0111][2] = f[0011][1] + d(1, 2) = {f[(prev, 1)]} + 3 = {f[(prev, 1)] + 3}。")
                S.play(tbl[row_of[prev], 1].to(stroke=CY, sw=4), c.to(stroke=Y, sw=4),
                       g4.edge(1, 2).to(color=Y, w=6), dur=0.5)
                S.play(c.to(text=str(f[(m, v)])), dur=0.5)
                S.wait(0.8)
                S.play(tbl[row_of[prev], 1].to(stroke=LINE, sw=2), c.to(stroke=LINE, sw=2),
                       g4.edge(1, 2).to(color=LINE2, w=3), dur=0.3)
            else:
                S.play(c.to(text=str(f[(m, v)])), dur=0.3)
        S.wait(0.15)
    full = (1 << N) - 1
    S.say(f"最后一行 1111 是走遍所有城市的结果。取最小值：停在 {end}，长度 {f[(full, end)]}。")
    S.play(tbl[row_of[full], end].to(fill=tint(Y, 0.45), stroke=Y, sw=4), dur=0.5)
    S.say("沿着每一步的最优来源倒推回去，得到路线 " + " → ".join(map(str, path)) + "。")
    S.play(*[g4.edge(a, b).to(color=Y, w=7) for a, b in zip(path, path[1:])], dur=0.8, lag=0.2)

    # ------------------------------------------------------------ 复杂度
    S.section("复杂度与适用范围")
    S.narrow()
    S.say("状态有 2ⁿ × n 个，每个状态向外枚举 n 个城市，总共 O(2ⁿ · n²)。")
    S.note("O(2ⁿ × n²)　n = 20：约 4×10⁸ 次简单运算")
    bars = Axes(x=620, y=480, w=900, h=480, xr=(0, 21), yr=(0, 18), xstep=5, ystep=5, xlabel="n", ylabel="log₁₀(运算量)")
    S.show(bars)
    pts_fact = []
    pts_dp = []
    for n_ in range(2, 21):
        lf = math.log10(math.factorial(n_ - 1))
        ld = math.log10(2 ** n_ * n_ * n_)
        pts_fact.append(bars.dot(n_, lf, R, 6))
        pts_dp.append(bars.dot(n_, ld, CY, 6))
    S.play(*[FadeIn(p) for p in pts_dp], dur=0.8, lag=0.03)
    S.play(*[FadeIn(p) for p in pts_fact], dur=0.8, lag=0.03)
    S.show(label(890, 250, "(n−1)!", 28, R), label(1060, 440, "2ⁿ · n²", 28, CY, anchor="lm"), lag=0.1)
    S.say("红色是枚举顺序，青色是状压 DP（纵轴是 10 的几次方）。n = 20 时差了大约 8 个数量级。")
    S.say("但 2ⁿ 本身还是指数：n 到 30 左右就不行了。状压 DP 适用于“集合元素很少”的问题，题目里 n ≤ 20 往往就是提示。")
    S.note("适用：集合的元素个数很小（n ≤ 20 左右）", color=Y)

    # ------------------------------------------------------------ 手推题
    S.quiz("n 个人、n 项工作，第 i 个人做第 j 项工作的代价是 c[i][j]，每人恰好做一项、每项恰好一人做。求最小总代价。\n\n"
           "用状压 DP：状态是什么？为什么这次不需要再记“现在是谁”？复杂度是多少？", think=20)
    S.say("按人的编号依次分配：第 1 个人、第 2 个人……状态 f[S]：前 |S| 个人已经分配完，用掉的工作集合是 S。")
    S.note("f[S]：前 |S| 个人做了集合 S 里的工作，最小代价", color=Y)
    S.say("“现在轮到谁”就是 |S| + 1，由 S 中 1 的个数决定，不用单独记——这又是第 2 集里的“隐含维度”。")
    S.note("轮到第 |S|+1 个人：由 S 决定 → 隐含维度", color=G)
    S.say("转移：第 |S|+1 个人选一项没被选的工作 j：f[S ∪ {j}] ← f[S] + c[|S|+1][j]。状态 2ⁿ 个，每个 n 个转移，O(2ⁿ · n)。")
    S.note("f[S ∪ {j}] ← f[S] + c[|S|+1][j]　O(2ⁿ × n)")
    S.say("对比哈密顿路：那里“停在哪”影响下一步的代价，所以要记 v；这里下一步的代价只和“轮到谁”有关，而它已经藏在 S 里了。", extra=0.5)

    S.recap([
        "状态要能区分“未来不同”的历史：哈密顿路的未来取决于已访问集合和当前城市，与顺序无关。",
        "只记已访问的个数不够：剩下的城市不同，未来就不同。",
        "集合用 n 位二进制数表示；按数值从小到大递推，因为加入元素后数值一定变大。",
        "复杂度 O(2ⁿ n²)，适合 n ≤ 20 左右；能由集合推出的量（如“轮到第几个人”）不必再进状态。",
    ], next_title="状态压缩 DP（下）：一行一行地放")
