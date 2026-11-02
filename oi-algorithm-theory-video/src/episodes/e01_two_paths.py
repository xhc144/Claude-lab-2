"""第 1 集 多维状态设计（上）：两条路线为什么要一起走"""

from episodes.common import *

A = [[2, 2, 0, 0], [0, 9, 0, 9], [9, 3, 6, 0], [1, 0, 9, 2]]
N = 4


def a(r, c):
    return A[r - 1][c - 1]


def best_single(grid):
    """单条路线的最大和以及路线（1 开始编号）。"""
    f = [[0] * (N + 1) for _ in range(N + 1)]
    fr = {}
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            cand = []
            if r > 1:
                cand.append((f[r - 1][c], (r - 1, c)))
            if c > 1:
                cand.append((f[r][c - 1], (r, c - 1)))
            if cand:
                v, p = max(cand)
                f[r][c] = v + grid[r - 1][c - 1]
                fr[(r, c)] = p
            else:
                f[r][c] = grid[r - 1][c - 1]
    path = [(N, N)]
    while path[-1] in fr:
        path.append(fr[path[-1]])
    return f[N][N], path[::-1]


def valid(k):
    return range(max(1, k - N), min(N, k - 1) + 1)


def two_walk():
    """f[k][(x1, x2)]，k = x + y 从 2 到 2N。"""
    f = {2: {(1, 1): a(1, 1)}}
    par = {2: {}}
    for k in range(3, 2 * N + 1):
        f[k], par[k] = {}, {}
        for x1 in valid(k):
            for x2 in valid(k):
                best, bp = None, None
                for p in ((x1 - 1, x2 - 1), (x1 - 1, x2), (x1, x2 - 1), (x1, x2)):
                    if p in f[k - 1] and (best is None or f[k - 1][p] > best):
                        best, bp = f[k - 1][p], p
                add = a(x1, k - x1) + (a(x2, k - x2) if x1 != x2 else 0)
                f[k][(x1, x2)] = best + add
                par[k][(x1, x2)] = bp
    st = (N, N)
    pa, pb = [], []
    for k in range(2 * N, 1, -1):
        pa.append((st[0], k - st[0]))
        pb.append((st[1], k - st[1]))
        st = par[k].get(st)
    return f, pa[::-1], pb[::-1]


def build(S):
    S.cover("方格里从左上角走到右下角走两趟（只能向右或向下），每格的数只能取一次，两趟最多能取多少？",
            ["单条路线的网格 DP：f[i][j] = max(f[i−1][j], f[i][j−1]) + a[i][j]"])

    # ------------------------------------------------------------ 问题
    S.section("问题：走两趟")
    g = Grid(N, N, x=420, y=490, cw=100, ch=100, gap=6, vals=A, size=36, rbase=1, cbase=1,
             rlab=[str(i) for i in range(1, N + 1)], clab=[str(i) for i in range(1, N + 1)], lab_size=24)
    st = label(g.X(1) - 62, g.Y(1) - 70, "起点", 24, DIM)
    en = label(g.X(N) + 62, g.Y(N) + 70, "终点", 24, DIM)
    S.show(g, st, en)
    S.say("一个 4×4 的方格，每格有一个非负整数。从左上角走到右下角，每一步只能向右或向下。")
    S.note("每趟：(1,1) → (4,4)，只能向右、向下")
    S.say("一共走两趟。格子里的数被第一趟取走后就变成 0，第二趟再经过也拿不到。")
    S.note("走两趟；每格的数只能被取一次")
    S.note("求：两趟取数之和的最大值", color=Y)
    S.say("先看一个最自然的想法：第一趟取得尽量多，第二趟再在剩下的数里取得尽量多。", extra=0.5)

    # ------------------------------------------------------------ 贪心
    S.section("先走一趟最好的？")
    S.show(g, st, en, dur=0.01)
    s1, p1 = best_single(A)
    rest = [row[:] for row in A]
    for r, c in p1:
        rest[r - 1][c - 1] = 0
    s2, p2 = best_single(rest)
    pts1 = [(g.lx(c), g.ly(r)) for r, c in p1]
    pts2 = [(g.lx(c), g.ly(r)) for r, c in p2]
    r1 = route(g, pts1, CY, 6, (-28, -28))
    r2 = route(g, pts2, O, 6, (28, 28))
    t1 = token(g, pts1[0][0] - 28, pts1[0][1] - 28, CY)
    sum1 = label(800, 330, "", 34, CY, anchor="lm")
    sum2 = label(800, 410, "", 34, O, anchor="lm")
    tot = label(800, 500, "", 38, FG, anchor="lm", chain="bold")
    S.add(sum1, sum2, tot)
    S.note("想法：第一趟取最多，第二趟在剩下的里再取最多")
    S.say("第一趟就是单条路线的 DP：沿着最优路线走，能取到 {c|33}。")
    S.play(FadeIn(t1), dur=0.3)
    acc = 0
    for i, (r, c) in enumerate(p1):
        acc += a(r, c)
        anims = [t1.to(x=pts1[i][0] - 28, y=pts1[i][1] - 28), g[r, c].to(fill=tint(CY, 0.35)),
                 sum1.to(text=f"第一趟：{acc}")]
        if i:
            anims += grow(r1, i - 1)
        S.play(*anims, dur=0.42)
    S.say("这一趟经过的格子都被取空了。")
    S.play(*[g[r, c].to(text="0", tc=FAINT) for r, c in p1], dur=0.6, lag=0.05)
    S.say("第二趟在剩下的数里再求一次最优，只能取到 {o|10}。两趟合计 43。")
    t2 = token(g, pts2[0][0] + 28, pts2[0][1] + 28, O)
    S.play(FadeIn(t2), dur=0.3)
    acc = 0
    for i, (r, c) in enumerate(p2):
        acc += rest[r - 1][c - 1]
        anims = [t2.to(x=pts2[i][0] + 28, y=pts2[i][1] + 28), sum2.to(text=f"第二趟：{acc}")]
        if rest[r - 1][c - 1]:
            anims.append(g[r, c].to(fill=tint(O, 0.35)))
        if i:
            anims += grow(r2, i - 1)
        S.play(*anims, dur=0.42)
    S.play(tot.to(text=f"合计 {s1 + s2}"), dur=0.4)
    S.note(f"贪心：{s1} + {s2} = {s1 + s2}", color=DIM)
    f, pa, pb = two_walk()
    best = f[2 * N][(N, N)]
    S.say(f"可是这个方格的最优答案是 {{y|{best}}}。差在哪里？")
    S.play(FadeOut(t1, t2), *[s.to(op=0.0) for s in r1 + r2], dur=0.5)
    S.play(*[g[r, c].to(text=str(a(r, c)), tc=FG, fill=BG3) for r in range(1, N + 1) for c in range(1, N + 1)],
           dur=0.5)
    S.play(*[g[r, c].to(stroke=Y, sw=4) for r, c in [(2, 2), (3, 1), (2, 4)]], dur=0.5)
    S.say("方格里有三个 9。第一趟为了拿中间的 9，从中间穿过，把剩下的格子分成了左下和右上两块。")
    S.play(*[g[r, c].to(fill=tint(CY, 0.35)) for r, c in p1], dur=0.6)
    S.say("剩下的两个 9 一个在左下、一个在右上，第二趟只能走一边，只能拿到其中一个。")
    S.play(g[3, 1].bump(dur=0.8, glow=1.0), g[2, 4].bump(dur=0.8, glow=1.0), dur=0.8)
    S.play(*[g[r, c].to(fill=BG3) for r, c in p1], dur=0.4)
    qa = [(g.lx(c), g.ly(r)) for r, c in pa]
    qb = [(g.lx(c), g.ly(r)) for r, c in pb]
    ra = route(g, qa, CY, 6, (-28, -28))
    rb = route(g, qb, O, 6, (28, 28))
    sa = sum(a(r, c) for r, c in pa)
    sb = sum(a(r, c) for r, c in pb if (r, c) not in pa)
    S.say(f"最优解里两趟有分工：一趟走右上、拿中间和右边的 9，另一趟走左下、拿左边和下面的 9。")
    S.play(*grow(ra), *[g[r, c].to(fill=tint(CY, 0.35)) for r, c in pa], dur=1.0)
    S.play(*grow(rb), *[g[r, c].to(fill=tint(O, 0.35)) for r, c in pb if (r, c) not in pa], dur=1.0)
    S.play(sum1.to(text=f"右上一趟：{sa}"), sum2.to(text=f"左下一趟：{sb}"), tot.to(text=f"合计 {sa + sb}"),
           dur=0.5)
    S.say("第一趟单独最优，并不是“两趟合起来最优”的一部分。两趟通过共同经过的格子互相影响，必须一起决策。",
          extra=1.0)
    S.note("两趟互相影响：影响只发生在共同经过的格子上")
    S.note("→ 不能分开求最优，要放进同一个状态", color=Y)

    # ------------------------------------------------------------ 同步
    S.section("两个人同时出发")
    g2 = Grid(N, N, x=420, y=490, cw=100, ch=100, gap=6, vals=A, size=36, rbase=1, cbase=1,
              rlab=[str(i) for i in range(1, N + 1)], clab=[str(i) for i in range(1, N + 1)], lab_size=24)
    S.show(g2)
    S.say("先试试“先完整走完第一趟，再走第二趟”。第二趟每走一步，都要知道第一趟拿走了哪些格子。")
    ex = [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (4, 3), (4, 4)]
    S.play(*[g2[r, c].to(text="0", tc=FAINT, fill=tint(CY, 0.25)) for r, c in ex], dur=0.6, lag=0.06)
    S.note("先走完 A 再走 B：B 要知道 A 取走了哪些格子")
    S.say("“取走了哪些格子”就是第一趟的整条路线。路线有 C(2n−2, n−1) 种，n = 50 时大约 2.5×10²⁸ 种，没法放进状态。")
    S.note("这是一整条路线：C(2n−2, n−1) 种，太多", color=R)
    S.play(*[g2[r, c].to(text=str(a(r, c)), tc=FG, fill=BG3) for r, c in ex], dur=0.5)
    S.say("换一种走法：两个人 A、B 同时从起点出发，每一步两人各走一格。")
    ta = token(g2, g2.lx(1) - 28, g2.ly(1) - 28, CY, 15, "A")
    tb = token(g2, g2.lx(1) + 28, g2.ly(1) + 28, O, 15, "B")
    S.play(FadeIn(ta, scale=0.5), FadeIn(tb, scale=0.5), dur=0.5)
    S.note("A、B 同时出发，每步各走一格")
    diag_lab = label(800, 330, "", 32, Y, anchor="lm")
    S.add(diag_lab)

    def diag_cells(k):
        return [(x, k - x) for x in valid(k)]

    S.say("把满足 x + y = k 的格子叫作第 k 条斜线。起点在第 2 条斜线上，每走一步，所在斜线的编号加 1。")
    S.play(*[g2[r, c].to(stroke=Y, sw=4) for r, c in diag_cells(2)], diag_lab.to(text="第 2 条斜线"), dur=0.5)
    for k in range(3, 6):
        S.play(*[g2[r, c].to(stroke=LINE, sw=2, fill=alpha(BG3, 0.55), tc=FAINT) for r, c in diag_cells(k - 1)],
               *[g2[r, c].to(stroke=Y, sw=4) for r, c in diag_cells(k)],
               ta.to(x=g2.lx(pa[k - 2][1]) - 28, y=g2.ly(pa[k - 2][0]) - 28),
               tb.to(x=g2.lx(pb[k - 2][1]) + 28, y=g2.ly(pb[k - 2][0]) + 28),
               diag_lab.to(text=f"第 {k} 条斜线"), dur=0.7)
        S.wait(0.5)
    S.say("所以第 k 步结束时，A 和 B 都恰好在第 k 条斜线上。")
    S.note("第 k 步时，两人都在斜线 x + y = k 上", color=Y)
    S.say("关键在这里：已经走过的格子全在前面的斜线上（灰色），以后只会走到后面的斜线。")
    S.play(*[g2[r, c].bump(dur=0.8, glow=0.8, stroke=C.LINE2) for k in range(2, 5) for r, c in diag_cells(k)],
           dur=0.8)
    S.say("也就是说，“哪些格子被取过”对未来没有任何影响——未来根本碰不到它们。状态只需要记住两人现在的位置。",
          extra=1.0)
    S.note("过去在前面的斜线，未来在后面的斜线 → 不用记“取过哪些格”", color=G)
    S.say("再看重复计数。格子 (x, y) 只可能在第 x + y 步被经过，所以两人只可能在同一步、同一格重合。")
    S.play(*[g2[r, c].to(stroke=LINE, sw=2, fill=BG3, tc=FG) for r in range(1, N + 1) for c in range(1, N + 1)],
           diag_lab.to(text=""), dur=0.5)
    S.play(ta.to(x=g2.lx(2) - 28, y=g2.ly(2) - 28), tb.to(x=g2.lx(2) + 28, y=g2.ly(2) + 28),
           g2[2, 2].to(stroke=Y, sw=4), dur=0.8)
    S.say("比如两人第 4 步都走到 (2, 2)：这时 9 只加一次。判断“是否重合”只要比较两人的位置。")
    S.play(g2[2, 2].flash(Y), dur=0.8)
    S.note("重合只发生在同一步、同一格：位置相同就只加一次", color=G)

    # ------------------------------------------------------------ 状态与转移
    S.section("状态与转移")
    S.note("四维：f[x1][y1][x2][y2]")
    S.say("于是状态可以是 f[x1][y1][x2][y2]：A 在 (x1, y1)、B 在 (x2, y2) 时，已经取到的最大和。")
    S.say("但同步走时 x1 + y1 = x2 + y2 = k，知道 k 和行号，列号就确定了。四维里有一维是多余的。")
    S.note("同步：y = k − x，可以去掉两个 y", color=Y)
    S.note("{y|f[k][x1][x2]}：两人走到第 k 条斜线，A 在第 x1 行、B 在第 x2 行时的最大和")
    S.say("每一步两人各自选择向下或向右，所以一个状态有 2 × 2 = 4 个来源。")
    S.note("来源：x1′ ∈ {x1−1, x1}，x2′ ∈ {x2−1, x2}，共 4 个")
    S.note("加上 a[x1][y1] + a[x2][y2]；x1 = x2 时只加一次")

    g3 = Grid(N, N, x=230, y=470, cw=76, ch=76, gap=5, vals=A, size=28, rbase=1, cbase=1,
              rlab=[str(i) for i in range(1, N + 1)], clab=[str(i) for i in range(1, N + 1)], lab_size=20)
    hdr = [str(i) for i in range(1, N + 1)]
    prev = Grid(N, N, x=640, y=490, cw=62, ch=54, gap=4, size=24, rbase=1, cbase=1, rlab=hdr, clab=hdr)
    cur = Grid(N, N, x=1030, y=490, cw=62, ch=54, gap=4, size=24, rbase=1, cbase=1, rlab=hdr, clab=hdr)
    lp = label(640, 300, "第 k−1 层", 26, DIM)
    lc = label(1030, 300, "第 k 层", 26, Y)
    ax1 = label(640, 655, "列：x2　行：x1", 20, FAINT)
    ax2 = label(1030, 655, "列：x2　行：x1", 20, FAINT)
    S.say("把每一层 k 画成一张表：行是 A 的行号 x1，列是 B 的行号 x2。第 k 层只从第 k−1 层转移过来。")
    S.show(g3, prev, cur, lp, lc, ax1, ax2, lag=0.1)

    def show_layer(grid, k, anim=True):
        out = []
        for x1 in range(1, N + 1):
            for x2 in range(1, N + 1):
                if (x1, x2) in f[k]:
                    out.append(grid[x1, x2].to(text=str(f[k][(x1, x2)]), tc=FG, fill=BG3))
                else:
                    out.append(grid[x1, x2].to(text="·", tc=FAINT, fill=alpha(BG3, 0.4)))
        return out

    def mark_diag(k, on=True):
        return [g3[r, c].to(stroke=Y if on else LINE, sw=4 if on else 2) for r, c in diag_cells(k)]

    S.play(*show_layer(prev, 3), *show_layer(cur, 4), lp.to(text="第 3 层"), lc.to(text="第 4 层"),
           *mark_diag(4), dur=0.6)
    S.say("第 4 层：两人都在第 4 条斜线上，行号只能是 1、2、3，所以表里只有 3×3 个有效格。")
    S.say("看重合的格子 f[4][2][2]：两人都在 (2, 2)。来源是第 3 层的四个格子，最大是 4，再加一次 9，得到 13。")
    srcs = [(1, 1), (1, 2), (2, 1), (2, 2)]
    S.play(*[prev[p].to(stroke=CY, sw=4) for p in srcs], cur[2, 2].to(stroke=Y, sw=4),
           g3[2, 2].to(fill=tint(Y, 0.4)), dur=0.6)
    S.play(cur[2, 2].flash(Y), dur=0.7)
    S.play(*[prev[p].to(stroke=LINE, sw=2) for p in srcs], cur[2, 2].to(stroke=LINE, sw=2),
           g3[2, 2].to(fill=BG3), dur=0.4)
    S.play(*show_layer(prev, 4), *show_layer(cur, 5), lp.to(text="第 4 层"), lc.to(text="第 5 层"),
           *mark_diag(4, False), *mark_diag(5), dur=0.6)
    v = f[5][(2, 3)]
    S.say(f"再看 f[5][2][3]：A 在 (2, 3)，B 在 (3, 2)。四个来源里最大的是 f[4][2][3] = 22，"
          f"加上 a[2][3] = 0 和 a[3][2] = 3，得到 {v}。")
    srcs = [(1, 2), (1, 3), (2, 2), (2, 3)]
    S.play(*[prev[p].to(stroke=CY, sw=4) for p in srcs], cur[2, 3].to(stroke=Y, sw=4),
           g3[2, 3].to(fill=tint(CY, 0.4)), g3[3, 2].to(fill=tint(O, 0.4)), dur=0.6)
    S.play(prev[2, 3].flash(CY), dur=0.6)
    S.play(cur[2, 3].flash(Y), dur=0.6)
    S.play(*[prev[p].to(stroke=LINE, sw=2) for p in srcs], cur[2, 3].to(stroke=LINE, sw=2),
           g3[2, 3].to(fill=BG3), g3[3, 2].to(fill=BG3), dur=0.4)
    S.say("表是对称的：交换 A 和 B 的身份，答案不变。所以只算 x1 ≤ x2 的一半也可以。")
    S.play(*[cur[x1, x2].bump(dur=0.8, glow=0.9, stroke=C.LINE2) for x1, x2 in f[5] if x1 > x2], dur=0.8)
    S.say("一层一层推下去，直到第 8 层，两人都到了终点 (4, 4)。")
    for k in range(6, 2 * N + 1):
        S.play(*show_layer(prev, k - 1), *show_layer(cur, k), lp.to(text=f"第 {k - 1} 层"),
               lc.to(text=f"第 {k} 层"), *mark_diag(k - 1, False), *mark_diag(k), dur=0.6)
        S.wait(0.6)
    S.play(cur[N, N].to(stroke=Y, sw=4), dur=0.3)
    S.play(cur[N, N].flash(Y), dur=0.8)
    S.say(f"f[8][4][4] = {best}，和前面找到的最优方案一致，比“两次分别最优”的 43 多出 8。")
    S.note(f"本例：f[8][4][4] = {best}", color=Y)

    # ------------------------------------------------------------ 正确性与复杂度
    S.section("为什么对，要算多久")
    S.wide()
    c1 = Card(470, 330, 820, 300, "不漏", "任意两条路线，按步数对齐后就是一串状态 (k, x1, x2)，"
              "相邻两个状态之间正好是一种转移。所以每一对路线都被某条转移链表示了。", color=G, size=29)
    c2 = Card(1400, 330, 820, 300, "不重", "每个格子只在“它所在的那一步”被计入。两人在同一步走到同一格时，"
              "状态里 x1 = x2，只加一次。不同步的重合不可能发生。", color=CY, size=29)
    c3 = Card(470, 680, 820, 300, "无后效性", "到达 (k, x1, x2) 之后还能取到什么，只取决于两人现在的位置：未来只会走"
              "第 k 条以后的斜线，和过去走过的格子没有交集。", color=Y, size=29)
    c4 = Card(1400, 680, 820, 300, "复杂度", "k 有 2n−1 种，x1、x2 各 n 种，状态 O(n³)，每个状态 4 个来源，"
              "总共 O(n³)。四维写法是 O(n⁴)。", color=P, size=29)
    S.say("把正确性分成三件事来看：不漏、不重、无后效性。")
    S.show(c1, dy=12)
    S.say("不漏：任何一对路线都能写成一串状态转移，所以 DP 的最大值不会比真正的最优解小。")
    S.show(c2, dy=12)
    S.say("不重：同一个格子不会被加两次。这一点完全依赖“同步”——它把重合限制在了同一个状态里。")
    S.show(c3, dy=12)
    S.say("无后效性：这是能把“取过哪些格子”从状态里删掉的原因，也是整个设计的核心。", extra=0.5)
    S.show(c4, dy=12)
    S.say("时间是 O(n³)。n = 50 时状态大约 25 万个，很轻松。")
    S.say("一句话：同步不是为了省一维，而是为了让“过去”和“未来”在斜线两侧完全分开。", extra=1.0)

    # ------------------------------------------------------------ 变式与反例
    S.section("变式与反例")
    S.narrow()
    g4 = Grid(N, N, x=420, y=480, cw=96, ch=96, gap=6, vals=A, size=34, rbase=1, cbase=1,
              rlab=[str(i) for i in range(1, N + 1)], clab=[str(i) for i in range(1, N + 1)], lab_size=22)
    S.show(g4)
    S.say("变式：走三趟呢？同样让三个人同步走，状态 f[k][x1][x2][x3]，每个状态 8 个来源，O(n⁴)。")
    S.note("三趟：f[k][x1][x2][x3]，8 个来源，O(n⁴)")
    S.say("重合时，三个位置里相同的只算一次。趟数再多，维数跟着涨，那时要换成网络流（第 29、30 集）。")
    S.note("趟数多了维数爆炸 → 费用流", color=DIM)
    S.say("反例：如果允许向上或向左走，这套方法就失效了。")
    bad = [(1, 1), (1, 2), (1, 3), (2, 3), (2, 2), (3, 2), (3, 3), (4, 3), (4, 4)]
    pts = [(g4.lx(c), g4.ly(r)) for r, c in bad]
    rbad = route(g4, pts, R, 6, (-26, -26))
    S.play(*grow(rbad), dur=1.4)
    S.say("这条路线从 (2, 3) 向左回到 (2, 2)：第 5 步之后又回到了第 4 条斜线。"
          "“过去在前、未来在后”不再成立，B 可能走到 A 早就取空的格子。")
    S.play(g4[2, 2].to(stroke=R, sw=5), dur=0.4)
    S.play(g4[2, 2].flash(R), dur=0.8)
    S.note("能向上 / 向左走：过去和未来不再被斜线分开 → 只记位置不够", color=R)
    S.say("判断能不能用这一招，就看一件事：是否存在一个随步数单调前进的量，把已经用掉的资源和将来要用的资源分开。",
          extra=1.0)
    S.note("判断标准：有没有一个单调前进的量，把过去与未来隔开", color=Y)

    # ------------------------------------------------------------ 手推题
    S.quiz("传纸条：m×n 的方格，从左上角向右下角传两次纸条（只能向右、向下）。两条路线除了起点和终点，"
           "不能经过同一个格子。求两条路线上的数之和的最大值。\n\n"
           "和本集的做法相比，状态和转移要改什么？为什么这样改就够了？", think=18)
    S.say("状态和转移都不用改，只改一件事：除了起点和终点所在的那两步，不允许出现 x1 = x2 的状态。")
    S.note("中间步：f[k][x][x] = −∞（不合法）", color=Y)
    S.say("为什么够了？两条路线要共用一个格子，只能在同一步到达它，也就是某一步出现了 x1 = x2。")
    S.note("共用格子 ⇔ 某一步 x1 = x2")
    S.say("禁止这些状态，就恰好排除了所有相交的方案；而不相交的方案一个也没有被删掉。")
    S.say("实际写的时候，也可以只计算 x1 < x2 的状态，天然避开重合，顺便把对称的一半省掉。")
    S.note("等价写法：只算 x1 < x2", color=G)

    # ------------------------------------------------------------ 小结
    S.recap([
        "两趟路线通过共同经过的格子互相影响，分开各求最优会出错，必须放进同一个状态一起决策。",
        "让两条路线按步数同步：已经走过的格子都在前面的斜线上，未来碰不到它们，所以状态不必记“取过哪些格子”。",
        "同步之后，重合只可能发生在同一步、同一格；x1 = x2 时只加一次，做到不重不漏。",
        "k 确定后列号由行号决定，四维降到三维 f[k][x1][x2]，O(n³)。",
        "能这样做的前提：有一个单调前进的量（这里是 x + y）把过去和未来隔开。",
    ], next_title="多维状态设计（下）：状态里到底该装什么")
