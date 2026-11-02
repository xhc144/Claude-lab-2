"""第 6 集 区间 DP 建模（下）：端点里的信息——涂色与关路灯"""

from episodes.common import *

S_T = "RGRBGB"
COL = {"R": R, "G": G, "B": B}
X = [1, 3, 4, 7, 9]
PW = [2, 6, 7, 9, 4]
C0 = 2   # 起点（下标从 0 开始）


def paint_dp(s):
    n = len(s)
    f, how = {}, {}
    for i in range(n):
        f[(i, i)] = 1
    for L in range(2, n + 1):
        for l in range(n - L + 1):
            r = l + L - 1
            if s[l] == s[r]:
                f[(l, r)] = f[(l, r - 1)]
                how[(l, r)] = "eq"
            else:
                v, k = min((f[(l, k)] + f[(k + 1, r)], k) for k in range(l, r))
                f[(l, r)] = v
                how[(l, r)] = k
    return f, how


def strokes(s, f, how, l, r):
    """按 DP 构造一种最优涂法（按涂的先后顺序）。第一笔总是整段涂成 s[l]。"""
    if l == r:
        return [(l, r, s[l])]
    h = how[(l, r)]
    if h == "eq":
        st = strokes(s, f, how, l, r - 1)
        return [(l, r, s[l])] + st[1:]
    left = strokes(s, f, how, l, h)
    right = strokes(s, f, how, h + 1, r)
    return [(l, r, s[l])] + left[1:] + right


def lights_dp():
    n = len(X)
    P = sum(PW)
    pre = [0]
    for v in PW:
        pre.append(pre[-1] + v)

    def on(l, r):
        return P - (pre[r + 1] - pre[l])

    INF = float("inf")
    f, par = {(C0, C0, 0): 0, (C0, C0, 1): 0}, {}
    for L in range(2, n + 1):
        for l in range(n - L + 1):
            r = l + L - 1
            if not (l <= C0 <= r):
                continue
            a = [(f.get((l + 1, r, 0), INF) + (X[l + 1] - X[l]) * on(l + 1, r), (l + 1, r, 0)),
                 (f.get((l + 1, r, 1), INF) + (X[r] - X[l]) * on(l + 1, r), (l + 1, r, 1))]
            b = [(f.get((l, r - 1, 1), INF) + (X[r] - X[r - 1]) * on(l, r - 1), (l, r - 1, 1)),
                 (f.get((l, r - 1, 0), INF) + (X[r] - X[l]) * on(l, r - 1), (l, r - 1, 0))]
            f[(l, r, 0)], par[(l, r, 0)] = min(a)
            f[(l, r, 1)], par[(l, r, 1)] = min(b)
    end = min(((f[(0, n - 1, s)], (0, n - 1, s)) for s in (0, 1)))
    path = [end[1]]
    while path[-1] in par:
        path.append(par[path[-1]])
    return f, end[0], path[::-1]


def build(S):
    S.cover("区间 DP 的状态有时要带上端点的信息：涂色时首尾同色能省一笔；关路灯时还要记住人站在哪一端。",
            ["区间 DP：枚举最后一步、按长度递推（第 5 集）"])

    # ------------------------------------------------------------ 涂色
    S.section("涂色：问题")
    n = len(S_T)
    tgt = Array([""] * n, x=640, y=240, cw=100, ch=70, gap=8)
    for i, ch in enumerate(S_T):
        tgt.cells[i].setnow()
        tgt.cells[i].box.tr["fill"].base = tint(COL[ch], 0.75)
        tgt.cells[i].label.tr["text"].base = ch
    tl = label(640, 170, "目标颜色", 24, DIM)
    S.show(tgt, tl)
    S.say("一条木板分成 6 格，要涂成上面的颜色。每一笔把{y|连续的一段}涂成同一种颜色，后涂的会盖住先涂的。最少几笔？")
    S.note("一笔 = 把连续一段涂成同一种颜色；后涂盖住先涂")
    S.note("求：涂成目标的最少笔数", color=Y)
    f, how = paint_dp(S_T)
    st = strokes(S_T, f, how, 0, n - 1)
    canvas = Array([""] * n, x=640, y=560, cw=100, ch=70, gap=8)
    cl = label(640, 490, "木板", 24, DIM)
    S.show(canvas, cl)
    S.say(f"一种涂法：先把整段涂红，再涂一小段绿，然后右半段涂蓝，最后补一格绿，一共 {len(st)} 笔。")
    for k, (l, r, c) in enumerate(st):
        bar = Rect((canvas.lx(l + 1) + canvas.lx(r + 1)) / 2 + 640, 400 - 26 * k, (r - l + 1) * 108 - 8, 18,
                   fill=COL[c], stroke=None, sw=0, r=9)
        S.play(FadeIn(bar, dx=-20), *[canvas.cells[i].to(fill=tint(COL[c], 0.75), text=c) for i in range(l, r + 1)],
               dur=0.7)
        S.wait(0.3)
    S.say("状态还是 f[l][r]：把第 l 到 r 格涂好的最少笔数。关键是：最后一步、或第一步，该怎么拆？")
    S.note("{y|f[l][r]}：把 [l, r] 涂成目标的最少笔数", color=Y)

    # ------------------------------------------------------------ 两种情况
    S.section("首尾同色 / 首尾不同色")
    S.say("先做一个整理：可以假设任意两笔要么一笔套住另一笔，要么互不相交。")
    demo = Array([""] * 6, x=640, y=520, cw=100, ch=60, gap=8, index=False)
    S.show(demo)
    b1 = Rect(640 - 108, 420, 4 * 108 - 8, 18, fill=O, stroke=None, sw=0, r=9)
    b2 = Rect(640 + 108, 392, 4 * 108 - 8, 18, fill=CY, stroke=None, sw=0, r=9)
    S.play(FadeIn(b1), FadeIn(b2), dur=0.5)
    S.say("如果两笔部分重叠（先涂橙、后涂青），把先涂的那笔重叠的部分去掉，结果不变，笔数也不变。")
    S.play(b1.to(w=2 * 108 - 8, x=640 - 216), dur=0.8)
    S.note("整理：任意两笔要么嵌套、要么不相交")
    S.play(FadeOut(demo, b1, b2), dur=0.4)

    S.say("情况一：首尾同色，s[l] = s[r]。结论：f[l][r] = f[l][r−1]，最后一格不用多花一笔。")
    S.note("① s[l] = s[r]：f[l][r] = f[l][r−1]", color=G)
    ex = Array(list("RGBGR"), x=640, y=400, cw=100, ch=70, gap=8)
    for i, ch in enumerate("RGBGR"):
        ex.cells[i].box.tr["fill"].base = tint(COL[ch], 0.75)
    S.show(ex)
    S.say("“不会更少”：把 [l, r] 的任意涂法里每一笔都截掉第 r 格，就得到 [l, r−1] 的涂法，笔数不变。")
    S.play(ex.cells[4].to(op=0.3), dur=0.5)
    S.say("“不会更多”：DP 构造出的涂法，第一笔总是把整段涂成 s[l]（可以归纳验证）。把这第一笔延长一格到 r，颜色正好是 s[r]。")
    bar = Rect(640 - 54, 320, 4 * 108 - 8, 18, fill=R, stroke=None, sw=0, r=9)
    S.play(ex.cells[4].to(op=1.0), FadeIn(bar), dur=0.5)
    S.play(bar.to(w=5 * 108 - 8, x=640), dur=0.8)
    S.say("因为第一笔在最底层，延长出来的部分只要后面没有别的笔盖住，就露出 s[l] = s[r]。所以首尾同色时，最后一格是“免费”的。")
    S.play(FadeOut(ex, bar), dur=0.4)

    S.say("情况二：首尾不同色。结论：一定能在某处切开，f[l][r] = min_k f[l][k] + f[k+1][r]。")
    S.note("② s[l] ≠ s[r]：f[l][r] = min_k f[l][k] + f[k+1][r]", color=CY)
    ex2 = Array(list(S_T), x=640, y=560, cw=100, ch=70, gap=8)
    for i, ch in enumerate(S_T):
        ex2.cells[i].box.tr["fill"].base = tint(COL[ch], 0.75)
    S.show(ex2)
    S.say("看覆盖第 l 格的最外层那一笔 Z。如果 Z 没有伸到 r，那么没有任何一笔跨过 Z 的右端（嵌套或不相交），就在那里切开。")
    z = Rect(640 - 216 + 0, 470, 3 * 108 - 8, 18, fill=R, stroke=None, sw=0, r=9)
    z.tr["x"].base = (ex2.lx(1) + ex2.lx(3)) / 2 + 640
    cut = Line(640 + (ex2.right(3) + ex2.left(4)) / 2, 440, 640 + (ex2.right(3) + ex2.left(4)) / 2, 620,
               color=Y, w=4, dash=(10, 8))
    S.play(FadeIn(z), dur=0.4)
    S.play(FadeIn(cut), dur=0.4)
    S.say("如果 Z 盖住了整个 [l, r]：它的颜色至少和一端不同，比如和 s[l] 不同，那第 l 格一定被 Z 里面的某一笔盖住。")
    S.say("在那一笔的右端切开：左边是那一笔和它里面的笔，右边是 Z 截下的一段加上其余的笔，总笔数没有增加。")
    S.say("两种情况都说明：任何涂法都能拆成左右两段独立涂，而且不多花笔。所以枚举切点 k 不会漏掉最优解。")
    S.play(FadeOut(z, cut), dur=0.3)
    S.say("这里“端点颜色”这条信息决定了用哪个转移——区间 DP 的拆法要看端点的具体情况。", extra=0.5)

    # 填表
    S.section("推一遍")
    S.wide()
    tgt2 = Array(list(S_T), x=960, y=180, cw=90, ch=62, gap=8, size=28)
    for i, ch in enumerate(S_T):
        tgt2.cells[i].box.tr["fill"].base = tint(COL[ch], 0.75)
    g = Grid(n, n, x=760, y=560, cw=96, ch=64, gap=5, size=28, rbase=1, cbase=1,
             rlab=[f"l={i}" for i in range(1, n + 1)], clab=[f"r={j}" for j in range(1, n + 1)])
    for i in range(1, n + 1):
        for j in range(1, i):
            g[i, j].tr["op"].base = 0.0
    S.show(tgt2, g)
    S.say("按长度填表。黄色边框表示首尾同色，直接抄左边的格子；青色表示首尾不同色，要枚举切点。")
    for L in range(1, n + 1):
        anims = []
        for l in range(0, n - L + 1):
            r = l + L - 1
            c = g[l + 1, r + 1]
            if L == 1:
                anims.append(c.to(text="1", tc=DIM))
            elif how[(l, r)] == "eq":
                anims.append(c.to(text=str(f[(l, r)]), stroke=Y, sw=3))
            else:
                anims.append(c.to(text=str(f[(l, r)]), stroke=CY, sw=3))
        S.play(*anims, dur=0.6, lag=0.08)
        S.wait(0.5)
    S.say(f"答案 f[1][6] = {f[(0, n - 1)]}。复杂度和石子合并一样是 O(n³)。")
    S.play(g[1, n].to(fill=tint(Y, 0.35)), dur=0.4)
    S.play(g[1, n].flash(Y), dur=0.7)

    # ------------------------------------------------------------ 关路灯
    S.section("关路灯：状态要带上“站在哪一端”")
    S.narrow()
    xs = {i: 140 + (X[i] - 1) * 130 for i in range(len(X))}
    axis = Line(100, 470, 1240, 470, color=LINE2, w=3)
    lamps = [Circle(xs[i], 470, 26, fill=tint(Y, 0.6), stroke=Y, sw=3, glow=0.8) for i in range(len(X))]
    plab = [label(xs[i], 525, f"功率 {PW[i]}", 22, DIM) for i in range(len(X))]
    xlab = [label(xs[i], 410, f"x={X[i]}", 22, FAINT) for i in range(len(X))]
    S.show(axis, *lamps, *plab, *xlab, lag=0.04)
    S.say("一条路上有 5 盏灯，位置和功率如图。老人站在 x = 4 的灯下，每秒走 1 米，经过一盏灯就顺手关掉。")
    S.note("灯在 x 轴上；老人 1 米/秒，路过即关灯")
    S.say("每盏灯在关掉之前，每秒消耗等于功率的电。怎样走，让总耗电最少？")
    S.note("耗电 = Σ 功率 × 亮着的时间；求最小", color=Y)
    man = Circle(xs[C0], 440, 13, fill=CY, stroke=C.BG, sw=3)
    man.tr["op"].base = 0
    S.play(FadeIn(man), lamps[C0].to(fill=BG3, glow=0.0, stroke=LINE2), dur=0.5)
    S.say("先观察：关掉的灯一定是包含起点的一段连续区间 [l, r]——走到更远的灯必须先经过更近的灯。")
    S.note("已关的灯总是连续一段 [l, r]")
    band = Rect(xs[C0], 470, 60, 90, fill=alpha(CY, 0.12), stroke=alpha(CY, 0.6), sw=2, r=12)
    band.tr["op"].base = 0
    S.play(FadeIn(band), dur=0.4)
    S.say("而且老人一定站在区间的某一端：刚关掉的那盏灯不是 l 就是 r。只记区间不够，还要记站在左端还是右端。")
    S.note("{y|f[l][r][0/1]}：关完 [l, r]，站在左端(0) / 右端(1) 的最小耗电", color=Y)
    S.say("还缺什么？耗电和“已经过了多少时间”有关，难道要把时间也放进状态？")
    S.say("不用。换个记账方式：每走一段路，就把这段时间里{y|所有还亮着的灯}的耗电立刻记上。这叫费用提前计算。")
    S.note("费用提前：走 d 米，加上 d × (还亮着的灯的总功率)", color=G)
    S.say("这样，状态之后还要付多少钱，只取决于哪些灯还亮着（区间外的灯）和人在哪里，与过去花了多少时间无关。")
    S.note("f[l][r][0] ← f[l+1][r][0/1] + 距离 × 区间 [l+1, r] 之外的总功率")

    f2, best, path = lights_dp()
    cost = label(1100, 330, "耗电 0", 30, Y, anchor="rm")
    S.show(cost, dur=0.3)
    S.say(f"按最优方案走一遍：先关左边紧挨着的灯（功率 6），然后折回向右关掉功率 9、4 的两盏，最后才去最左边功率只有 2 的灯。总耗电 {best}。")
    acc = 0
    P = sum(PW)
    off = {C0}
    for (l0, r0, s0), (l1, r1, s1) in zip(path, path[1:]):
        p0 = l0 if s0 == 0 else r0
        p1 = l1 if s1 == 0 else r1
        d = abs(X[p1] - X[p0])
        acc += d * (P - sum(PW[i] for i in off))
        off.add(p1)
        S.play(man.to(x=xs[p1]), band.to(x=(xs[l1] + xs[r1]) / 2, w=xs[r1] - xs[l1] + 60),
               lamps[p1].to(fill=BG3, glow=0.0, stroke=LINE2), cost.to(text=f"耗电 {acc}"), dur=0.4 + 0.12 * d)
        S.wait(0.4)
    S.say("如果每次都走向最近的灯，会先把左边两盏都关掉，这段时间里右边功率 9 的灯一直亮着，耗电是 137。功率大的灯应该早点关。")
    S.note(f"最近优先：137　最优：{best}", color=DIM)
    S.say("状态 O(n²) × 2，每个 O(1) 转移，总共 O(n²)。")

    # ------------------------------------------------------------ 手推题
    S.quiz("关路灯的两个变式：\n"
           "(1) 每关一盏灯，老人要停下来花 1 秒。状态和转移要怎么改？\n"
           "(2) 如果老人可以乘车瞬间到达任意一盏灯（不经过中间的灯），f[l][r][0/1] 还对吗？为什么？", think=20)
    S.say("(1) 状态不用改。停下来的 1 秒里，亮着的灯照样耗电：每次关灯时，再加上 1 × (关这盏灯之前还亮着的灯的总功率)。")
    S.note("(1) 只改代价：关灯时加 1 × 当时亮着的总功率", color=G)
    S.say("这正是费用提前计算的好处：任何“花时间”的动作，都当场把所有亮着的灯的耗电记上，状态里永远不需要时间。")
    S.say("(2) 不对了。“已关的灯是一段连续区间”依赖于“走过去必然经过中间的灯”。能瞬移以后，已关的灯可以是任意集合。")
    S.note("(2) 已关的灯不再连续 → 区间状态失效（要用集合，指数级）", color=R)
    S.say("所以区间 DP 能用，靠的是问题本身保证“处理过的部分是连续一段”。设计状态前先找这种结构。", extra=0.5)

    S.recap([
        "涂色：首尾同色时 f[l][r] = f[l][r−1]（第一笔延长一格），不同色时一定能切开，枚举切点。",
        "证明的关键整理：任意两笔要么嵌套、要么不相交。",
        "关路灯：已关的灯是包含起点的连续区间，人一定在区间一端，状态 f[l][r][0/1]。",
        "费用提前计算：每走一段，就把所有还亮着的灯的耗电记上，状态里就不需要时间。",
        "区间状态成立的前提：处理过的部分总是连续的一段。",
    ], next_title="树形 DP：子树要向上交代多少信息")
