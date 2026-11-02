"""第 10 集 状态压缩 DP（下）：一行一行地放"""

from episodes.common import *

N = 3
K = 2


def valid_masks(n):
    return [m for m in range(1 << n) if not (m & (m << 1))]


def ok(a, b):
    return not (a & b) and not (a & (b << 1)) and not (a & (b >> 1))


def pc(m):
    return bin(m).count("1")


def kings():
    ms = valid_masks(N)
    f = [{(m, pc(m)): 1 for m in ms if pc(m) <= K}]
    for i in range(1, N):
        g = {}
        for (a, k), v in f[-1].items():
            for b in ms:
                if ok(a, b) and k + pc(b) <= K:
                    g[(b, k + pc(b))] = g.get((b, k + pc(b)), 0) + v
        f.append(g)
    return ms, f


def mstr(m, n=N):
    return "".join("1" if (m >> (n - 1 - j)) & 1 else "0" for j in range(n))


def build(S):
    S.cover("N×N 的棋盘上放 K 个国王，使它们互不攻击（国王攻击周围 8 格），有多少种放法？",
            ["集合用二进制表示（第 9 集）", "接口思维（第 7 集）"])

    # ------------------------------------------------------------ 问题
    S.section("问题：互不侵犯")
    board = Grid(4, 4, x=360, y=470, cw=96, ch=96, gap=4, size=40)
    S.show(board)
    S.say("国王能攻击周围 8 个格子。在 N×N 的棋盘上放 K 个国王，要求任意两个都不互相攻击，问有多少种放法。")
    S.note("国王攻击周围 8 格；放 K 个，两两不攻击，求方案数")
    king = (1, 1)
    S.play(board[king].to(text="K", tc=Y, fill=tint(Y, 0.35)), dur=0.4)
    S.play(*[board[(king[0] + di, king[1] + dj)].to(fill=tint(R, 0.3)) for di in (-1, 0, 1) for dj in (-1, 0, 1)
             if (di, dj) != (0, 0)], dur=0.5)
    S.say("红色是它攻击的范围。棋盘有 N² 个格子，逐格枚举放不放是 2^(N²)，N = 9 时是 2⁸¹，不可能。")
    S.note("逐格枚举 2^(N²)：太多", color=R)
    S.play(*[board[(i, j)].to(fill=BG3, text="", tc=FG) for i in range(4) for j in range(4)], dur=0.4)
    S.say("换一种方式：一行一行地放。处理完前 i 行，接下来还需要知道什么？")

    # ------------------------------------------------------------ 接口
    S.section("一行一行：接口只有最后一行")
    S.say("第 i+1 行的国王只会和第 i 行的国王冲突，和更上面的行碰不到。所以前 i 行对未来的影响，只通过第 i 行这一排。")
    S.note("第 i+1 行只和第 i 行冲突 → 接口 = 最后一行的放法", color=Y)
    hl = board.frame(1, 0, 1, 3, Y)
    S.play(FadeIn(hl), *[board[(0, j)].to(fill=alpha(BG3, 0.4)) for j in range(4)], dur=0.5)
    S.say("另外还要知道已经放了几个国王（总数必须正好是 K）。至于上面几行具体怎么放，未来不关心。")
    S.note("{y|f[i][S][k]}：前 i 行，第 i 行的放法是 S，共放了 k 个", color=Y)
    S.play(FadeOut(hl), *[board[(0, j)].to(fill=BG3) for j in range(4)], dur=0.4)
    S.say("一行的放法 S 用二进制表示：第 j 位是 1 表示第 j 列有国王。")
    row = Array(["0", "1", "0", "1"], x=360, y=760, cw=70, ch=56, gap=6, size=28, index=False)
    S.show(row)
    S.play(board[(2, 1)].to(text="K", tc=Y, fill=tint(Y, 0.3)), board[(2, 3)].to(text="K", tc=Y, fill=tint(Y, 0.3)),
           row.cells[1].to(fill=tint(Y, 0.35)), row.cells[3].to(fill=tint(Y, 0.35)), dur=0.5)

    # ------------------------------------------------------------ 合法行
    S.section("一行之内与两行之间")
    S.say("条件一：同一行里不能有两个相邻的国王。也就是 S 的二进制里没有两个相邻的 1：S & (S << 1) = 0。")
    S.note("行内：S & (S << 1) = 0")
    ms4 = valid_masks(4)
    cells = []
    for i, m in enumerate(range(16)):
        good = m in ms4
        c = Cell(150 + (i % 8) * 128, 280 + (i // 8) * 90, 112, 64, mstr(m, 4), 28, fill=tint(G, 0.3) if good else alpha(BG3, 0.4),
                 tc=FG if good else FAINT, stroke=G if good else LINE, chain="mono")
        cells.append(c)
    S.show(*cells, lag=0.02)
    S.say(f"宽度为 4 时，16 种放法里只有 {len(ms4)} 种合法（绿色）。一般地，宽度 n 的合法行数是斐波那契数：n = 9 时只有 89 种，远小于 512。")
    S.note(f"合法行数 = 斐波那契数：n = 4 → {len(ms4)}，n = 9 → 89", color=G)
    S.say("条件二：上下相邻两行 A、B 不能冲突：同一列不能都有（A & B = 0），斜对角也不能（A & (B << 1) = 0，A & (B >> 1) = 0）。")
    S.note("两行相容：A & B = 0，A & (B<<1) = 0，A & (B>>1) = 0", color=Y)
    S.play(FadeOut(*cells), dur=0.4)
    A_ = Array(list("0100"), x=420, y=360, cw=80, ch=64, gap=6, size=30, index=False, chain="mono", base=0)
    B_ = Array(list("0010"), x=420, y=440, cw=80, ch=64, gap=6, size=30, index=False, chain="mono", base=0)
    la = label(200, 360, "A", 30, CY)
    lb = label(200, 440, "B", 30, O)
    S.show(A_, B_, la, lb)
    S.play(A_.cells[1].to(fill=tint(CY, 0.45)), B_.cells[2].to(fill=tint(O, 0.45)), dur=0.4)
    arrow = Line(420 + A_.lx(1), 392, 420 + B_.lx(2), 408, color=R, w=4)
    S.play(FadeIn(arrow), dur=0.3)
    S.say("例如 A = 0100、B = 0010：两个国王在斜对角，冲突。把 B 左移一位得到 0100，和 A 有公共的 1——A & (B << 1) ≠ 0，检查出来了。")
    C_ = Array(list("0100"), x=420, y=560, cw=80, ch=64, gap=6, size=30, index=False, chain="mono", base=0)
    lc = label(200, 560, "B << 1", 28, O)
    S.show(C_, lc)
    S.play(C_.cells[1].to(fill=tint(R, 0.45)), A_.cells[1].to(fill=tint(R, 0.45)), dur=0.5)
    S.play(A_.cells[1].flash(R), C_.cells[1].flash(R), dur=0.7)
    S.say("转移：f[i][B][k] = Σ f[i−1][A][k − |B|]，对所有与 B 相容的合法行 A 求和，|B| 是 B 里 1 的个数。")
    S.note("f[i][B][k] = Σ_A f[i−1][A][k − |B|]（A、B 相容）")

    # ------------------------------------------------------------ 推一遍
    S.section("推一遍：3×3 放 2 个")
    S.wide()
    ms, f = kings()
    S.say(f"3×3 的棋盘放 2 个国王。宽度 3 的合法行有 {len(ms)} 种：" + "、".join(mstr(m) for m in ms) + "。")
    tables = []
    for i in range(N):
        t = Grid(len(ms), K + 1, x=480 + i * 470, y=520, cw=92, ch=60, gap=4, size=28,
                 rlab=[mstr(m) for m in ms], clab=[f"k={k}" for k in range(K + 1)], lab_color=FG)
        tables.append(t)
        S.add(t)
        t.tr["op"].base = 0
    heads = [label(480 + i * 470, 270, f"第 {i + 1} 行", 28, Y) for i in range(N)]
    S.show(tables[0], heads[0])
    S.show(label(960, 190, "每张表：行 = 本行放法 B，列 = 累计个数 k", 24, DIM))
    S.say("第 1 行：每种合法行各一种放法，k 等于这一行的国王数。")
    S.play(*[tables[0][(r, pc(m))].to(text="1", fill=tint(G, 0.3)) for r, m in enumerate(ms)], dur=0.6)
    for i in range(1, N):
        S.show(tables[i], heads[i])
        if i == 1:
            S.say("第 2 行：对每个 B 和 k，把上一行所有相容的 A 在 k − |B| 那一列的值加起来。")
            b = 0b010
            r = ms.index(b)
            comp = [ms.index(a) for a in ms if ok(a, b)]
            S.play(*[tables[0][(rr, 0)].to(stroke=CY, sw=4) for rr in comp], tables[1][(r, 1)].to(stroke=Y, sw=4), dur=0.5)
            S.say(f"例：B = 010、k = 1。与 010 相容的只有 000（其余都会碰到中间的国王），f[1][000][0] = 1，所以这一格是 1。")
            S.play(tables[1][(r, 1)].to(text=str(f[1].get((b, 1), 0))), dur=0.4)
            S.play(*[tables[0][(rr, 0)].to(stroke=LINE, sw=2) for rr in comp], tables[1][(r, 1)].to(stroke=LINE, sw=2), dur=0.3)
        S.play(*[tables[i][(rr, k)].to(text=str(f[i][(m, k)]), fill=tint(G, 0.3))
                 for rr, m in enumerate(ms) for k in range(K + 1) if (m, k) in f[i]], dur=0.8, lag=0.04)
        S.wait(0.6)
    ans = sum(v for (m, k), v in f[-1].items() if k == K)
    S.say(f"答案是最后一行所有 k = 2 的格子之和：{ans}。可以核对：从 9 个格子里选 2 个有 36 种，减去 20 对相邻（含斜）的，正好 16。")
    S.play(*[tables[-1][(rr, K)].to(stroke=Y, sw=4) for rr, m in enumerate(ms) if (m, K) in f[-1]], dur=0.5)
    S.say("复杂度：N 行 × (合法行数)² × K。N = 9、K 最大 81 时，约 9 × 89² × 81 ≈ 580 万，很轻松。")

    # ------------------------------------------------------------ 变式
    S.section("变式：攻击范围变大，接口变宽")
    S.narrow()
    S.say("炮兵阵地：每个炮兵能打到上下左右各两格。那么第 i+1 行会和第 i 行、第 i−1 行都冲突。")
    S.note("攻击两行远 → 接口要包含最后两行", color=Y)
    S.note("f[i][A][B]：第 i−1 行放法 A，第 i 行放法 B")
    bd = Grid(5, 5, x=380, y=480, cw=80, ch=80, gap=4, size=34)
    S.show(bd)
    S.play(bd[(2, 2)].to(text="炮", tc=Y, fill=tint(Y, 0.35)), dur=0.4)
    S.play(*[bd[(2 + d, 2)].to(fill=tint(R, 0.3)) for d in (-2, -1, 1, 2)], *[bd[(2, 2 + d)].to(fill=tint(R, 0.3)) for d in (-2, -1, 1, 2)],
           dur=0.5)
    S.say("所以状态要同时记最后两行的放法 f[i][A][B]。接口有多宽，取决于“相互作用能跨多远”。")
    S.say("一行之内的合法放法也更少了（任意两个炮兵至少隔两格），所以 f[i][A][B] 的状态数依然可控。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("玉米田：2 行 3 列的田，第 1 行中间那格是贫瘠的，不能种。种玉米的格子不能上下左右相邻（斜对角可以）。"
           "可以种任意多格（包括一格都不种）。\n\n"
           "有多少种种法？请列出每行的合法放法，再按“两行相容”计数。", think=20)
    ms3 = valid_masks(3)
    row1 = [m for m in ms3 if not (m & 0b010)]
    S.say("每行的合法放法（左右不相邻）有 000、001、010、100、101 五种。第 1 行中间不能种，去掉 010，剩下四种。")
    S.note("第 1 行：000、001、100、101；第 2 行：五种都可以")
    S.say("这次只禁止上下相邻（没有斜对角），所以两行相容的条件只有 A & B = 0。")
    S.note("相容：A & B = 0（只看上下）", color=Y)
    rows_t = []
    tot = 0
    for i, a in enumerate(row1):
        bs = [b for b in ms3 if not (a & b)]
        tot += len(bs)
        t = label(140, 420 + 62 * i, f"第 1 行 {mstr(a)}：第 2 行可以是 " + "、".join(mstr(b) for b in bs) + f"，共 {len(bs)} 种",
                  28, FG, anchor="lm")
        rows_t.append(t)
    S.play(*[FadeIn(t, dx=-10) for t in rows_t], dur=0.6, lag=0.4)
    S.say(f"加起来是 5 + 3 + 3 + 2 = {tot} 种。")
    S.note(f"答案：{tot}", color=G)
    S.say("和互不侵犯相比：多了“哪些格子能用”的限制（每行先和地形求交），相容条件少了斜对角，状态的形式完全一样。", extra=0.5)

    S.recap([
        "逐行处理时，前 i 行对未来的影响只通过最后一行（接口），状态是“最后一行的放法 + 累计个数”。",
        "一行内的合法放法 S & (S<<1) = 0，数量是斐波那契数，远小于 2ⁿ；先把它们预处理出来。",
        "两行相容用位运算判断：A & B、A & (B<<1)、A & (B>>1) 都为 0。",
        "相互作用跨两行时，接口就要包含最后两行：f[i][A][B]。",
    ], next_title="数位 DP：贴着上界走")
