"""第 2 集 多维状态设计（下）：状态里到底该装什么"""

import itertools

from episodes.common import *

A = [7, 1, 6, 8, 6, 7, 7, 8, 1, 4]          # 第 1..10 格的分数
CARDS = [1, 1, 2, 2, 3]
CNT = {1: 2, 2: 2, 3: 1}
GRID = [[0, 3, 2], [6, 9, 9], [1, 0, 2]]     # 反例：不能连续两次向右


def pos(i, j, k):
    return 1 + i + 2 * j + 3 * k


def turtle_dp():
    f = {}
    src = {}
    for k in range(CNT[3] + 1):
        for i in range(CNT[1] + 1):
            for j in range(CNT[2] + 1):
                cand = []
                if i:
                    cand.append((f[(i - 1, j, k)], (i - 1, j, k)))
                if j:
                    cand.append((f[(i, j - 1, k)], (i, j - 1, k)))
                if k:
                    cand.append((f[(i, j, k - 1)], (i, j, k - 1)))
                base = max(cand)[0] if cand else 0
                f[(i, j, k)] = base + A[pos(i, j, k) - 1]
                src[(i, j, k)] = [c[1] for c in cand]
    return f, src


def greedy():
    rem = list(CARDS)
    p, s, path = 1, A[0], [1]
    while rem:
        c = max(sorted(set(rem)), key=lambda c: (A[p + c - 1], -c))
        rem.remove(c)
        p += c
        s += A[p - 1]
        path.append(p)
    return s, path


def best_order():
    best = None
    for perm in sorted(set(itertools.permutations(CARDS))):
        p, s, path = 1, A[0], [1]
        for c in perm:
            p += c
            s += A[p - 1]
            path.append(p)
        if best is None or s > best[0]:
            best = (s, perm, path)
    return best


def grid_dp():
    """f[(r, c, 最后一步)]，1 开始编号。"""
    R, C_ = 3, 3
    f = {(1, 1, "S"): GRID[0][0]}
    for r in range(1, R + 1):
        for c in range(1, C_ + 1):
            for d in "RD":
                pr, pc = (r, c - 1) if d == "R" else (r - 1, c)
                if pr < 1 or pc < 1:
                    continue
                best = None
                for pd in "SRD":
                    if (pr, pc, pd) in f and not (d == "R" and pd == "R"):
                        v = f[(pr, pc, pd)]
                        best = v if best is None else max(best, v)
                if best is not None:
                    f[(r, c, d)] = best + GRID[r - 1][c - 1]
    return f


def grid_naive():
    """只记 f[i][j]（以及它的最优来源方向）的错误做法。"""
    f = {(1, 1): (GRID[0][0], "S")}
    for r in range(1, 4):
        for c in range(1, 4):
            if (r, c) == (1, 1):
                continue
            cand = []
            if c > 1 and (r, c - 1) in f and f[(r, c - 1)][1] != "R":
                cand.append((f[(r, c - 1)][0] + GRID[r - 1][c - 1], "R"))
            if r > 1 and (r - 1, c) in f:
                cand.append((f[(r - 1, c)][0] + GRID[r - 1][c - 1], "D"))
            if cand:
                f[(r, c)] = max(cand)
    return f[(3, 3)][0]


def build(S):
    S.cover("乌龟棋：用完手里的卡片从起点走到终点，怎样安排卡片的顺序让得分最高？状态里该放哪些量？",
            ["多维状态（第 1 集）", "无后效性：未来只和当前状态有关"])

    # ------------------------------------------------------------ 问题
    S.section("问题：乌龟棋")
    arr = Array(A, x=660, y=300, cw=88, ch=78, gap=8, size=32)
    S.show(arr)
    S.say("一排 10 个格子，每格有一个分数。乌龟从第 1 格出发，终点是第 10 格。")
    S.note("格子 1..N，每格有分数；从 1 走到 N")
    cards = []
    for t, c in enumerate(CARDS):
        cd = Cell(420 + t * 110, 560, 70, 96, str(c), 38, fill=tint(G, 0.3), stroke=G, chain="bold")
        cards.append(cd)
    clab = label(420 + 2 * 110, 650, "手里的卡片", 24, DIM)
    S.say("手里有 5 张卡片：两张 1、两张 2、一张 3。每用一张，乌龟就向前走卡片上的格数。")
    S.show(*cards, clab, lag=0.08, dy=20)
    S.note("卡片上写着前进格数（原题是 1~4 四种）")
    S.say("卡片恰好用完时正好走到终点。得分是经过的所有格子（含起点和终点）的分数之和。")
    S.note("卡片恰好用完；得分 = 经过格子的分数和")
    S.note("问：卡片按什么顺序用，得分最高？", color=Y)
    S.say("同一个数字的卡片可以以任意顺序使用。5 张卡片一共有 5!/(2!·2!·1!) = 30 种不同的顺序。")

    tur = token(arr, arr.lx(1), 0, Y, 16)
    tur.tr["y"].base = -arr.ch / 2 - 22

    def hop(p, q, color, above=True):
        y = -arr.ch / 2 - 8 if above else arr.ch / 2 + 40
        ln = Line(arr.lx(p), y, arr.lx(q), y, color=color, w=4, head=12, prog=0.0,
                  bend=-0.42 if above else 0.42)
        ln.tr["op"].base = 0.0
        arr.add(ln)
        return ln

    gs, gpath = greedy()
    S.say("贪心试试：每一步都选能落到最高分格子的那张卡。")
    S.play(FadeIn(tur), arr[1].to(fill=tint(Y, 0.35)), dur=0.4)
    used = [False] * 5
    acc = A[0]
    score = label(1060, 560, f"得分 {acc}", 32, Y, anchor="lm")
    S.show(score, dur=0.3)
    hops = []
    for p, q in zip(gpath, gpath[1:]):
        c = q - p
        ci = next(i for i in range(5) if CARDS[i] == c and not used[i])
        used[ci] = True
        acc += A[q - 1]
        h = hop(p, q, Y)
        hops.append(h)
        S.play(FadeIn(h), h.to(prog=1.0), tur.to(x=arr.lx(q)), cards[ci].to(op=0.25),
               arr[q].to(fill=tint(Y, 0.35)), score.to(text=f"得分 {acc}"), dur=0.7)
        S.wait(0.3)
    bs, border, bpath = best_order()
    S.say(f"贪心得到 {gs}。但最优顺序是 3, 2, 1, 1, 2，得分 {{y|{bs}}}。")
    S.note(f"贪心 {gs} < 最优 {bs}：只看下一步不行", color=DIM)
    S.play(*[FadeOut(h) for h in hops], *[arr[q].to(fill=BG3) for q in gpath[1:]],
           *[c.to(op=1.0) for c in cards], tur.to(x=arr.lx(1)), score.to(text=f"得分 {A[0]}"), dur=0.6)
    acc = A[0]
    hops = []
    used = [False] * 5
    for p, q in zip(bpath, bpath[1:]):
        c = q - p
        ci = next(i for i in range(5) if CARDS[i] == c and not used[i])
        used[ci] = True
        acc += A[q - 1]
        h = hop(p, q, G)
        hops.append(h)
        S.play(FadeIn(h), h.to(prog=1.0), tur.to(x=arr.lx(q)), cards[ci].to(op=0.25),
               arr[q].to(fill=tint(G, 0.35)), score.to(text=f"得分 {acc}"), dur=0.6)
    S.say("第一步不拿最近的高分，而是用 3 跳到 8 分，后面才能连着踩到两个 7 和第 8 格的 8。要做 DP。", extra=0.5)

    # ------------------------------------------------------------ 状态
    S.section("状态里放什么")
    arr2 = Array(A, x=660, y=250, cw=88, ch=78, gap=8, size=32)
    S.show(arr2)
    S.say("先问自己：站在某一步，要决定“接下来怎么走才最好”，需要知道过去的哪些事？")
    S.note("设计状态的问题：为了决定未来，需要知道过去的什么？", color=Y)
    S.say("需要知道两件事：现在在哪一格，以及手里还剩哪些卡片。其余的（比如之前按什么顺序用卡）都不影响未来。")
    S.note("未来只取决于：当前位置 + 剩下的卡片")
    S.say("“剩下哪些卡片”如果把每张卡都看成不同的，会有 2^M 种。但同样数字的卡没有区别，只需要知道每种还剩几张。")
    S.note("同种卡片没有区别 → 只记每种用了几张 i, j, k")
    S.say("再看位置：已经用了 i 张 1、j 张 2、k 张 3，位置一定是 1 + i + 2j + 3k。位置是这三个数的函数，不用单独记。")
    S.note("位置 = 1 + i + 2j + 3k，可以算出来 → 不进状态", color=G)
    S.note("{y|f[i][j][k]}：三种卡各用了 i, j, k 张时的最高得分")

    S.say("用一个例子看清楚：先 1 后 2，和先 2 后 1，都走到第 4 格，手里剩下的卡片也一样。")
    t1 = token(arr2, arr2.lx(1), 0, CY, 13)
    t1.tr["y"].base = -arr2.ch / 2 - 22
    t2 = token(arr2, arr2.lx(1), 0, O, 13)
    t2.tr["y"].base = arr2.ch / 2 + 52

    def hop2(p, q, color, above):
        y = -arr2.ch / 2 - 8 if above else arr2.ch / 2 + 44
        ln = Line(arr2.lx(p), y, arr2.lx(q), y, color=color, w=4, head=12, prog=0.0, bend=-0.45 if above else 0.45)
        ln.tr["op"].base = 0.0
        arr2.add(ln)
        return ln

    ha = [hop2(1, 2, CY, True), hop2(2, 4, CY, True)]
    hb = [hop2(1, 3, O, False), hop2(3, 4, O, False)]
    la = label(660, 450, "", 28, CY)
    lb = label(660, 500, "", 28, O)
    S.add(la, lb)
    S.play(FadeIn(t1), FadeIn(t2), dur=0.3)
    S.play(FadeIn(ha[0]), ha[0].to(prog=1.0), t1.to(x=arr2.lx(2)), dur=0.6)
    S.play(FadeIn(ha[1]), ha[1].to(prog=1.0), t1.to(x=arr2.lx(4)), la.to(text=f"1,2：{A[0]}+{A[1]}+{A[3]} = {A[0] + A[1] + A[3]}"),
           dur=0.6)
    S.play(FadeIn(hb[0]), hb[0].to(prog=1.0), t2.to(x=arr2.lx(3)), dur=0.6)
    S.play(FadeIn(hb[1]), hb[1].to(prog=1.0), t2.to(x=arr2.lx(4)), lb.to(text=f"2,1：{A[0]}+{A[2]}+{A[3]} = {A[0] + A[2] + A[3]}"),
           dur=0.6)
    S.say("这两段历史的未来完全一样：同一个位置、同样的剩余卡片，以后能做的选择和能拿的分数都相同。")
    S.play(arr2[4].flash(Y), dur=0.8)
    S.say(f"既然未来一样，就只需要保留过去得分更高的那一个（{A[0] + A[2] + A[3]}）。这就是 DP 合并状态的本质。")
    S.play(la.to(color=FAINT), dur=0.5)
    S.note("未来相同的历史可以合并，只留最优的", color=G)
    S.say("所以“状态”其实是对历史的分类：未来相同的历史放进同一类。分类分得越粗，状态越少；但不能把未来不同的历史分到一类。",
          extra=1.0)

    # ------------------------------------------------------------ 推一遍
    S.section("推一遍")
    f, src = turtle_dp()
    S.wide()
    arr3 = Array(A, x=960, y=200, cw=80, ch=70, gap=8, size=30)
    S.show(arr3)
    hdr = ["0", "1", "2"]
    L0 = Grid(3, 3, x=650, y=560, cw=110, ch=80, gap=6, size=30, rlab=["i=0", "i=1", "i=2"], clab=["j=0", "j=1", "j=2"])
    L1 = Grid(3, 3, x=1290, y=560, cw=110, ch=80, gap=6, size=30, rlab=["i=0", "i=1", "i=2"], clab=["j=0", "j=1", "j=2"])
    t0 = label(650, 362, "k = 0（3 还没用）", 28, DIM)
    tk1 = label(1290, 362, "k = 1（3 已用）", 28, DIM)
    S.say("把 f[i][j][k] 画成两张表：左边是还没用 3 的（k = 0），右边是已经用了 3 的（k = 1）。")
    S.show(L0, L1, t0, tk1, lag=0.1)
    S.say("转移：最后一张用的是哪种卡？三种可能，分别从 f[i−1][j][k]、f[i][j−1][k]、f[i][j][k−1] 来，再加上当前位置的分数。",
          extra=0.5)
    eq = label(960, 760, "f[i][j][k] = max(f[i−1][j][k], f[i][j−1][k], f[i][j][k−1]) + a[1+i+2j+3k]", 30, Y,
               chain="mono")
    S.show(eq)
    tok = token(arr3, arr3.lx(1), 0, Y, 13)
    tok.tr["y"].base = -arr3.ch / 2 - 20
    S.play(FadeIn(tok), dur=0.3)

    def cell_of(s):
        i, j, k = s
        return (L0 if k == 0 else L1)[i, j]

    order = [(i, j, k) for k in range(2) for i in range(3) for j in range(3)]
    detail = {(0, 0, 0), (1, 1, 0), (0, 1, 1), (2, 2, 1)}
    first_detail = True
    for s in order:
        i, j, k = s
        c = cell_of(s)
        p = pos(*s)
        if s in detail:
            if s == (0, 0, 0):
                S.say("f[0][0][0] 是起点：一张卡都没用，在第 1 格，得分 7。")
            elif s == (1, 1, 0):
                S.say(f"f[1][1][0]：用了一张 1、一张 2，位置是 1+1+2 = 4。来源是 f[0][1][0] 和 f[1][0][0]，取大的再加 a[4] = 8。")
            elif s == (0, 1, 1):
                S.say(f"f[0][1][1]：用了一张 2、一张 3，位置 1+2+3 = 6。来源 f[0][0][1]（最后用 2）和 f[0][1][0]（最后用 3）。")
            elif s == (2, 2, 1):
                S.say(f"最后 f[2][2][1]：全部卡片用完，位置 1+2+4+3 = 10，就是终点。")
            anims = [c.to(stroke=Y, sw=4), tok.to(x=arr3.lx(p)), arr3[p].to(fill=tint(Y, 0.35))]
            anims += [cell_of(q).to(stroke=CY, sw=4) for q in src[s]]
            S.play(*anims, dur=0.5)
            S.play(c.to(text=str(f[s])), dur=0.5)
            S.play(c.flash(Y), dur=0.6)
            S.play(c.to(stroke=LINE, sw=2), arr3[p].to(fill=BG3), *[cell_of(q).to(stroke=LINE, sw=2) for q in src[s]],
                   dur=0.3)
        else:
            S.play(tok.to(x=arr3.lx(p)), arr3[p].to(fill=tint(Y, 0.25)), dur=0.25)
            S.play(c.to(text=str(f[s])), arr3[p].to(fill=BG3), dur=0.3)
    S.say(f"终点的值 f[2][2][1] = {f[(2, 2, 1)]}，就是最优答案。全部状态只有 3×3×2 = 18 个，而顺序有 30 种。")
    S.play(L1[2, 2].to(fill=tint(G, 0.4), stroke=G, sw=4), dur=0.5)
    S.say("原题有四种卡、每种最多 40 张：状态最多 41⁴ ≈ 280 万个，每个 4 个来源，完全可以接受；直接枚举顺序则是天文数字。")

    # ------------------------------------------------------------ 两把尺子
    S.section("检验状态的两把尺子")
    S.narrow()
    S.note("尺子一 · 充分：状态相同 ⇒ 未来完全相同", color=G)
    S.note("尺子二 · 精简：能由其他分量算出的分量，删掉", color=CY)
    S.say("设计状态时用两把尺子量一量。第一把是“充分”：任意两段历史，只要状态相同，它们的未来（可选的决策和得到的收益）就必须相同。")
    S.say("这正是“无后效性”的精确说法。如果不满足，合并时就可能把一个“过去差一点、未来好得多”的历史丢掉。")
    S.say("第二把是“精简”：如果某个分量能由其他分量算出来（比如乌龟棋的位置），它就不必进状态，否则只是白白多一维。")
    S.say("第一把尺子量的是对不对，第二把量的是快不快。先保证充分，再追求精简。", extra=0.5)
    S.note("先保证充分，再追求精简", color=Y)

    # ------------------------------------------------------------ 反例
    S.section("反例：少记了一样东西")
    g = Grid(3, 3, x=420, y=480, cw=110, ch=110, gap=6, vals=GRID, size=38, rbase=1, cbase=1,
             rlab=["1", "2", "3"], clab=["1", "2", "3"])
    S.show(g)
    S.say("方格取数加一条限制：{r|不能连续两次向右走}。如果还用 f[i][j] 表示走到 (i, j) 的最大和，会怎样？")
    S.note("限制：不能连续两次向右")
    S.note("试试 f[i][j] = 到 (i, j) 的最大和？")
    fd = grid_dp()
    pts_a = [(g.lx(1), g.ly(1)), (g.lx(1), g.ly(2)), (g.lx(2), g.ly(2))]
    pts_b = [(g.lx(1), g.ly(1)), (g.lx(2), g.ly(1)), (g.lx(2), g.ly(2))]
    ra = route(g, pts_a, CY, 6, (-30, -30))
    rb = route(g, pts_b, O, 6, (30, 30))
    va, vb = fd[(2, 2, "R")], fd[(2, 2, "D")]
    S.say(f"走到中间 (2, 2) 有两段历史：先下后右，得 {va}；先右后下，得 {vb}。f[2][2] 只会留下 {va}。")
    S.play(*grow(ra), dur=0.8)
    S.play(*grow(rb), dur=0.8)
    ta = label(720, 380, f"先下后右：{va}（最后一步向右）", 28, CY, anchor="lm")
    tb = label(720, 440, f"先右后下：{vb}（最后一步向下）", 28, O, anchor="lm")
    S.show(ta, tb)
    S.say(f"但最好的未来是继续向右踩 (2, 3) 的 9。留下的 {va} 最后一步正是向右，{{r|不能再向右}}；被丢掉的 {vb} 反而可以。")
    S.play(g[2, 3].to(stroke=Y, sw=5), dur=0.4)
    S.play(g[2, 3].flash(Y), dur=0.8)
    best_c = max(v for (r, c, d), v in fd.items() if (r, c) == (3, 3))
    nv = grid_naive()
    S.say(f"结果：只记 f[i][j] 算出的最大值是 {nv}，而真正的最优是 {best_c}（右、下、右、下）。")
    S.note(f"只记 f[i][j]：{nv}　正确答案：{best_c}", color=R)
    S.say("用第一把尺子量：两段历史都在 (2, 2)，但未来不同——一个还能向右，一个不能。状态少记了“最后一步的方向”。")
    S.note("修正：f[i][j][d]，d = 最后一步的方向", color=G)
    S.play(FadeOut(ta, tb), dur=0.3)
    tr = g.add(Text(g.lx(2) + 40, g.ly(2) - 38, f"→{va}", size=20, color=CY))
    td = g.add(Text(g.lx(2) + 40, g.ly(2) + 38, f"↓{vb}", size=20, color=O))
    hidden(tr)
    hidden(td)
    S.say(f"加上一维 d 之后，(2, 2) 同时保存“最后向右：{va}”和“最后向下：{vb}”两个值，谁也不会被错误地丢掉。")
    S.play(FadeIn(tr), FadeIn(td), dur=0.5)
    S.say("检查一个状态是否充分，最有效的办法就是找两段到达同一状态的历史，问：它们的未来真的一样吗？", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("一排 n 个正整数 a1..an，选出若干个，要求{y|不能有连续 3 个都被选}，使选中的数之和最大。\n\n"
           "(1) 设计一个状态，并用“充分”这把尺子说明它够用。\n"
           "(2) 能不能不加额外的维度，只用 f[i]？转移要怎么写？", think=20)
    S.say("(1) 只记 f[i]（前 i 个数的最优值）不够：第 i 个数选没选、末尾已经连着选了几个，都会影响下一个数能不能选。")
    S.note("f[i][t]：前 i 个，末尾连续选了 t 个（t = 0, 1, 2）", color=Y)
    S.say("所以状态是 f[i][t]：考虑前 i 个数，末尾恰好连续选了 t 个。下一步能否选只取决于 t，满足“充分”。")
    S.note("不选：f[i][0] = max(f[i−1][0], f[i−1][1], f[i−1][2])")
    S.note("选：f[i][1] = f[i−1][0] + aᵢ，f[i][2] = f[i−1][1] + aᵢ")
    S.say("(2) 也可以只用 f[i]，把信息挪到转移里：枚举最后一个“没被选的数”的位置。")
    S.note("f[i] = max(f[i−1], f[i−2] + aᵢ, f[i−3] + aᵢ₋₁ + aᵢ)", color=G)
    S.say("f[i−1]：第 i 个不选；f[i−2] + aᵢ：第 i−1 个不选、只选第 i 个；f[i−3] + aᵢ₋₁ + aᵢ：第 i−2 个不选、选末尾两个。")
    S.say("两种写法都对：一种把“末尾连续几个”放进状态，另一种在转移里枚举它。信息总得放在某个地方。", extra=0.5)

    S.recap([
        "状态是对历史的分类：未来完全相同的历史可以合并，只保留最优的那个。",
        "设计状态先问：要决定未来，需要知道过去的什么？乌龟棋需要“位置 + 剩下的卡”。",
        "尺子一 · 充分：状态相同 ⇒ 未来相同（无后效性）。少记信息会把“过去差、未来好”的历史错误地丢掉。",
        "尺子二 · 精简：能由其他分量算出的分量（乌龟棋的位置）不进状态。",
        "检查的办法：找两段到达同一状态的历史，问它们的未来是否真的一样。",
    ], next_title="背包变式（上）：循环顺序、初值与拆分")
