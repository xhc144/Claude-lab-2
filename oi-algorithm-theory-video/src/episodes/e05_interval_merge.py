"""第 5 集 区间 DP 建模（上）：枚举最后一步——石子合并"""

from episodes.common import *

A = [2, 3, 1, 3]


def prefix(a):
    s = [0]
    for x in a:
        s.append(s[-1] + x)
    return s


def interval_dp(a):
    n = len(a)
    s = prefix(a)
    f, best = {}, {}
    for i in range(1, n + 1):
        f[(i, i)] = 0
    for L in range(2, n + 1):
        for l in range(1, n - L + 2):
            r = l + L - 1
            cands = [(f[(l, k)] + f[(k + 1, r)], k) for k in range(l, r)]
            v, k = min(cands)
            f[(l, r)] = v + s[r] - s[l - 1]
            best[(l, r)] = k
    return f, best


def greedy_steps(a):
    a = list(a)
    steps, cost = [], 0
    while len(a) > 1:
        i = min(range(len(a) - 1), key=lambda i: (a[i] + a[i + 1], i))
        v = a[i] + a[i + 1]
        cost += v
        steps.append((i, v))
        a[i:i + 2] = [v]
    return steps, cost


class Piles:
    """一排石子堆：可以合并相邻两堆，剩下的堆重新居中排好。"""

    def __init__(self, S, vals, x, y, w=120, h=84, gap=28, color=None):
        self.S, self.x, self.y, self.w, self.h, self.gap = S, x, y, w, h, gap
        self.vals = list(vals)
        self.color = color or G
        self.cells = [Cell(0, y, w, h, str(v), 34, fill=tint(self.color, 0.28), stroke=self.color) for v in vals]
        for c, px in zip(self.cells, self.xs(len(vals))):
            c.tr["x"].base = px

    def xs(self, n):
        tot = n * self.w + (n - 1) * self.gap
        return [self.x - tot / 2 + self.w / 2 + i * (self.w + self.gap) for i in range(n)]

    def merge(self, i):
        a, b = self.cells[i], self.cells[i + 1]
        v = self.vals[i] + self.vals[i + 1]
        mid = (a.g("x", self.S.t) + b.g("x", self.S.t)) / 2
        new = Cell(mid, self.y, self.w, self.h, str(v), 34, fill=tint(Y, 0.35), stroke=Y)
        self.S.play(a.to(x=mid), b.to(x=mid), dur=0.5)
        self.S.play(FadeOut(a, b), FadeIn(new, scale=0.7), dur=0.4)
        self.cells[i:i + 2] = [new]
        self.vals[i:i + 2] = [v]
        xs = self.xs(len(self.cells))
        self.S.play(*[c.to(x=px) for c, px in zip(self.cells, xs)], new.to(fill=tint(self.color, 0.28), stroke=self.color),
                    dur=0.4)
        return v


def build(S):
    S.cover("一排石子堆，每次合并相邻两堆，代价是新堆的石子数。全部合成一堆的最小总代价是多少？",
            ["区间上的前缀和", "DP 的状态与转移"])

    # ------------------------------------------------------------ 问题
    S.section("问题：石子合并")
    P = Piles(S, A, 640, 300)
    S.show(*P.cells, lag=0.08)
    S.say("一排 4 堆石子：2、3、1、3。每次只能合并{y|相邻}的两堆，代价是合并后这一堆的石子数。")
    S.note("每次合并相邻两堆，代价 = 新堆大小")
    S.note("求：合成一堆的最小总代价", color=Y)
    S.say("最自然的贪心：每次挑合并代价最小的相邻两堆。")
    S.note("贪心：每次合并和最小的相邻两堆？")
    steps, gcost = greedy_steps(A)
    cost_t = label(640, 470, "总代价 0", 32, Y)
    S.show(cost_t)
    acc = 0
    for i, v in steps:
        acc += P.merge(i)
        S.play(cost_t.to(text=f"总代价 {acc}"), dur=0.3)
        S.wait(0.4)
    f, best = interval_dp(A)
    n = len(A)
    S.say(f"贪心总代价 {gcost}。但先合并 2、3，再合并 1、3，最后合并 5 和 4，总代价是 5 + 4 + 9 = {f[(1, n)]}。")
    P2 = Piles(S, A, 640, 640, color=CY)
    S.show(*P2.cells, lag=0.05)
    acc = 0
    cost2 = label(640, 790, "总代价 0", 32, CY)
    S.show(cost2)
    for i in (0, 1, 0):
        acc += P2.merge(i)
        S.play(cost2.to(text=f"总代价 {acc}"), dur=0.3)
    S.note(f"贪心 {gcost} > 最优 {f[(1, n)]}", color=R)
    S.say("贪心第一步把 3 和 1 合成 4，看着便宜，却让中间出现了一个大堆，后面每次合并都要再付一遍它。")
    S.say("补充：如果任意两堆都能合并（不要求相邻），“每次合并最小的两堆”就是最优的哈夫曼编码。正是“相邻”这个限制让贪心失效。",
          extra=0.5)
    S.note("不要求相邻 → 哈夫曼贪心正确；相邻限制使贪心失效", color=DIM)

    # ------------------------------------------------------------ 最后一步
    S.section("枚举最后一步")
    S.say("合并的顺序有很多种。怎样把它们分类，变成子问题？")
    arr = Array(A, x=640, y=330, cw=110, ch=84, gap=10, size=34)
    S.show(arr)
    S.say("看{y|最后一次合并}：它把两堆合成一堆。这两堆各自是什么？")
    S.say("因为每次只合并相邻的，任何时刻每一堆都是原来连续的一段。所以最后一次合并的，一定是 [1, k] 和 [k+1, 4] 这样的两段。")
    S.note("任何时刻，每一堆都是原序列的连续一段")
    sp1 = arr.span(1, 2, "[1, k]", CY, "above")
    sp2 = arr.span(3, 4, "[k+1, n]", O, "above")
    S.play(FadeIn(sp1), FadeIn(sp2), dur=0.5)
    S.say("在最后一次合并之前，左段和右段完全独立：左边怎么合并不影响右边。所以两边各自取最优就行。")
    for k in (1, 3, 2):
        S.play(arr.respan(sp1, 1, k), arr.respan(sp2, k + 1, 4), dur=0.6)
        S.wait(0.4)
    S.note("{y|f[l][r]}：把 [l, r] 合成一堆的最小代价", color=Y)
    S.note("f[l][r] = min_k ( f[l][k] + f[k+1][r] ) + sum(l..r)", color=Y)
    S.say("最后一次合并的代价是 [l, r] 全部石子数 sum(l..r)，和 k 无关，所以可以提到 min 外面。")
    S.say("为什么不漏不重？每一种合并方案都有唯一的“最后一次合并”，也就有唯一的分界点 k。按 k 分类，每个方案恰好落在一类里。")
    S.note("按最后一次合并的分界点 k 分类：不重不漏", color=G)
    S.say("如果换成枚举“第一次合并”呢？合并了第 i、i+1 堆之后，剩下的东西不再是“一段原始石子”，子问题的形状变了，状态描述不了。")
    S.note("枚举第一步：剩下的不是同类子问题 ✗", color=R)
    S.say("这就是区间 DP 的基本思路：选一个“最后一步”，让它把区间切成几个{y|同类型的更小区间}。", extra=0.5)

    # ------------------------------------------------------------ 推表
    S.section("按长度填表")
    s = prefix(A)
    g = Grid(n, n, x=420, y=500, cw=104, ch=84, gap=6, size=30, rbase=1, cbase=1,
             rlab=[f"l={i}" for i in range(1, n + 1)], clab=[f"r={j}" for j in range(1, n + 1)])
    for i in range(1, n + 1):
        for j in range(1, i):
            g[i, j].tr["op"].base = 0.0
    arr2 = Array(A, x=420, y=190, cw=80, ch=60, gap=8, size=28)
    S.show(arr2, g)
    S.say("f[l][r] 依赖更短的区间，所以按长度从小到大填：先长度 1（都是 0），再长度 2、3、4。")
    S.note("顺序：区间长度从小到大")
    S.play(*[g[i, i].to(text="0", tc=DIM) for i in range(1, n + 1)], dur=0.5, lag=0.1)
    for L in range(2, n + 1):
        for l in range(1, n - L + 2):
            r = l + L - 1
            if (l, r) == (1, 4):
                continue
            S.play(g[l, r].to(text=str(f[(l, r)])), arr2.fill(range(l, r + 1), tint(Y, 0.3)), dur=0.45)
            S.play(arr2.fill(range(l, r + 1), BG3), dur=0.2)
    S.say("最后算 f[1][4]。三个分界点：")
    cand_t = []
    for k in range(1, n):
        v = f[(1, k)] + f[(k + 1, n)]
        cand_t.append(label(780, 330 + 64 * (k - 1), f"k={k}：f[1][{k}] + f[{k + 1}][4] = {f[(1, k)]} + {f[(k + 1, n)]} = {v}",
                            28, FG, anchor="lm"))
    for k in range(1, n):
        S.play(g[1, k].to(stroke=CY, sw=4), g[k + 1, n].to(stroke=O, sw=4), FadeIn(cand_t[k - 1], dx=-10), dur=0.5)
        S.wait(0.8)
        S.play(g[1, k].to(stroke=LINE, sw=2), g[k + 1, n].to(stroke=LINE, sw=2), dur=0.3)
    kb = best[(1, n)]
    S.play(cand_t[kb - 1].to(color=Y), dur=0.4)
    tot = label(780, 330 + 64 * 3 + 20, f"f[1][4] = {f[(1, kb)] + f[(kb + 1, n)]} + sum = {f[(1, kb)] + f[(kb + 1, n)]} + {s[n]} = {f[(1, n)]}",
                30, Y, anchor="lm")
    S.say(f"最小的是 k = {kb}，再加上全部石子数 {s[n]}，得到 f[1][4] = {f[(1, n)]}。")
    S.show(tot)
    S.play(g[1, n].to(text=str(f[(1, n)]), fill=tint(Y, 0.35), stroke=Y, sw=4), dur=0.5)
    S.say("状态 O(n²) 个，每个枚举 O(n) 个分界点，总共 O(n³)。n 到几百没有问题。")
    S.note("O(n²) 个状态 × O(n) 分界点 = O(n³)")
    S.say("（满足四边形不等式时最优分界点有单调性，可以优化到 O(n²)，这里不展开。）")

    # ------------------------------------------------------------ 环
    S.section("环形：倍长成链")
    S.say("如果石子围成一圈，第一堆和最后一堆也算相邻，怎么办？")
    ring = Group(380, 480)
    R_ = 170
    import math
    pts = []
    vals = [3, 1, 2, 4]
    for i, v in enumerate(vals):
        ang = -math.pi / 2 + i * 2 * math.pi / 4
        pts.append((R_ * math.cos(ang), R_ * math.sin(ang)))
    gaps = []
    for i in range(4):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 4]
        gl = ring.add(Line(x1, y1, x2, y2, color=LINE2, w=3))
        gaps.append(gl)
    for (x, y), v in zip(pts, vals):
        ring.add(Cell(x, y, 90, 70, str(v), 32, fill=tint(G, 0.28), stroke=G))
    S.show(ring)
    S.say("观察：n 堆合成一堆要合并 n − 1 次，而环上有 n 处“相邻缝隙”。每次合并跨过一处缝隙，所以总有一处缝隙从来没被跨过。")
    S.note("n−1 次合并、n 处缝隙 → 至少一处缝隙从没被跨过", color=Y)
    S.play(gaps[3].to(color=R, w=5), dur=0.4)
    S.play(gaps[3].bump(dur=0.8, glow=1.0), dur=0.8)
    S.say("在那处缝隙把环剪开，就得到一条链，问题变回了直线版。只是我们不知道该在哪里剪，所以枚举剪开的位置。")
    S.note("在没被跨过的缝隙剪开 → 一条链；枚举剪开位置")
    dbl = vals + vals[:-1]
    arr3 = Array(dbl, x=930, y=330, cw=66, ch=60, gap=6, size=28)
    S.show(arr3)
    S.say("把数组复制一遍接在后面（长度 2n−1），从第 i 堆开始、长度为 n 的每一段，正好对应一种剪法。")
    fr = arr3.frame(1, 4, Y)
    S.play(FadeIn(fr), dur=0.4)
    for st in (2, 3, 4):
        S.play(arr3.reframe(fr, st, st + 3), dur=0.6)
        S.wait(0.3)
    S.note("倍长：a[1..2n−1]，答案 = min f[i][i+n−1]", color=G)
    S.say("在倍长的数组上只做一次区间 DP（长度不超过 n），答案取 min f[i][i+n−1]。复杂度仍是 O(n³)，而不是剪 n 次各做一遍。")

    # ------------------------------------------------------------ 手推题
    S.quiz("把合并的代价改成“两堆石子数的乘积”（合并 a 和 b 的代价是 a × b），仍然求最小总代价。\n\n"
           "(1) 区间 DP 的转移要怎么改？最后一次合并的代价还和 k 无关吗？\n"
           "(2) 再想一想：这个问题真的需要 DP 吗？", think=20)
    S.say("(1) 最后一次合并 [l, k] 与 [k+1, r]，代价是 sum(l..k) × sum(k+1..r)，现在和 k 有关了，要放进 min 里面。")
    S.note("f[l][r] = min_k ( f[l][k] + f[k+1][r] + S(l,k) × S(k+1,r) )")
    S.say("(2) 换个角度数代价：把每堆石子拆成一颗颗石子。合并 a 和 b 的代价 a × b，恰好是“一颗来自左堆、一颗来自右堆”的石子对数。")
    # 把每堆画成一列小石子，合并时连出跨两堆的石子对
    stones = []
    sx = [230, 470, 710, 950]
    for i, a in enumerate(A):
        col = []
        for k in range(a):
            d = Circle(sx[i], 470 + 70 * k, 14, fill=tint(G, 0.7), stroke=G, sw=2)
            col.append(d)
        stones.append(col)
    plab = [label(sx[i], 420, f"{A[i]} 颗", 24, DIM) for i in range(n)]
    S.show(*[d for col in stones for d in col], *plab, lag=0.02)
    cnt = label(1080, 380, "", 30, Y, anchor="rm")
    S.add(cnt)
    total = 0
    groups = [[i] for i in range(n)]

    def merge_groups(a, b, color):
        nonlocal total
        ga, gb = groups[a], groups[b]
        lines = []
        for i in ga:
            for j in gb:
                for d1 in stones[i]:
                    for d2 in stones[j]:
                        ln = Line(d1.g("x", 0), d1.g("y", 0), d2.g("x", 0), d2.g("y", 0), color=alpha(color, 0.55), w=2,
                                  bend=0.12)
                        ln.tr["op"].base = 0.0
                        lines.append(ln)
        sa = sum(A[i] for i in ga)
        sb = sum(A[j] for j in gb)
        total += sa * sb
        S.play(*[FadeIn(l_) for l_ in lines], cnt.to(text=f"本次 {sa}×{sb} = {sa * sb}，累计 {total}"), dur=0.9, lag=0.01)
        groups[a] = ga + gb
        del groups[b]
        return lines

    S.play(*[Appear(l_) for l_ in []], dur=0.01)
    merge_groups(0, 1, CY)
    S.wait(0.6)
    merge_groups(1, 2, O)
    S.wait(0.6)
    merge_groups(0, 1, Y)
    S.say("任意两颗石子，恰好在它们第一次进入同一堆时被数一次。所以无论怎样合并，总代价都等于所有 aᵢ × aⱼ（i < j）之和。")
    S.note("总代价 = Σ aᵢaⱼ（i < j），与合并顺序无关！", color=Y)
    tot_pair = sum(A[i] * A[j] for i in range(n) for j in range(i + 1, n))
    S.say(f"例如 2、3、1、3：任何顺序的总代价都是 {tot_pair}。这和上一集“点对只在 LCA 处被数一次”是同一个想法。")
    S.say("教训：写 DP 之前，先看看代价有没有更简单的结构。", extra=0.5)

    S.recap([
        "区间 DP 的核心是选一个“最后一步”，让它把区间切成几个同类型的更小区间。",
        "石子合并：最后一次合并把 [l, r] 分成 [l, k] 和 [k+1, r]，两边独立；按 k 分类不重不漏。",
        "f[l][r] 依赖更短的区间，按长度从小到大填，O(n³)。",
        "环形问题：n−1 次合并总有一处缝隙没被跨过，倍长数组后取长度为 n 的区间。",
        "相邻限制让贪心失效；而有些代价（如乘积）的总和与顺序无关，根本不用 DP。",
    ], next_title="区间 DP 建模（下）：端点里的信息——涂色与关路灯")
