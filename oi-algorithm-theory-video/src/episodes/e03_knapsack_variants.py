"""第 3 集 背包变式（上）：循环顺序、初值与拆分"""

from episodes.common import *

NEG = None   # 表示 −∞
ITEMS = [(2, 3), (3, 4)]      # (体积, 价值)
V = 7


def table01(items, cap, exact=False):
    rows = [[0 if (j == 0 or not exact) else NEG for j in range(cap + 1)]]
    for w, v in items:
        prev = rows[-1]
        cur = []
        for j in range(cap + 1):
            best = prev[j]
            if j >= w and prev[j - w] is not None:
                cand = prev[j - w] + v
                best = cand if best is None else max(best, cand)
            cur.append(best)
        rows.append(cur)
    return rows


def show(x):
    return "−∞" if x is None else str(x)


def build(S):
    S.cover("多重背包怎样不拆成一个一个也能做？一维数组的循环方向、初值、计数时的循环顺序，各自意味着什么？",
            ["0/1 背包与完全背包的基本写法"])

    # ------------------------------------------------------------ 新与旧
    S.section("一维数组里的“新”与“旧”")
    S.say("先回到二维的写法。f[i][j]：只考虑前 i 个物品、容量为 j 时的最大价值。下面两个物品：体积 2 价值 3，体积 3 价值 4。")
    S.note("f[i][j]：前 i 个物品，容量 j，最大价值")
    rows = table01(ITEMS, V)
    g = Grid(3, V + 1, x=660, y=330, cw=104, ch=70, gap=6, size=30, rlab=["i=0", "i=1", "i=2"],
             clab=[f"j={j}" for j in range(V + 1)], vals=[[show(x) for x in r] for r in rows])
    S.show(g)
    S.say("0/1 背包：f[i][j] = max(f[i−1][j], f[i−1][j−w] + v)。两个来源都在{c|上一行}——第 i 个物品最多用一次。")
    S.note("0/1：f[i][j] ← f[i−1][j]，f[i−1][j−w] + v（都在上一行）")
    a1 = g.arrow((1, 3), (2, 6), color=CY, w=4)
    a2 = g.arrow((1, 6), (2, 6), color=CY, w=4)
    S.play(FadeIn(a1), FadeIn(a2), g[2, 6].to(stroke=Y, sw=4), dur=0.6)
    S.say("完全背包只改一处：f[i][j] = max(f[i−1][j], f[i][j−w] + v)。第二个来源在{o|同一行}，意思是“已经可能用过第 i 个，还可以再用一个”。")
    S.note("完全：f[i][j−w] + v（在同一行）→ 第 i 个可以再用", color=O)
    a3 = g.arrow((2, 3), (2, 6), color=O, w=4, bend=-0.35)
    S.play(FadeOut(a1), FadeIn(a3), dur=0.6)
    S.say("压成一维数组时，f[j] 里同时住着两行：已经更新过的位置是这一行（新），还没更新的位置是上一行（旧）。")
    S.play(FadeOut(a2, a3), g[2, 6].to(stroke=LINE, sw=2), dur=0.4)

    arr = Array([show(x) for x in rows[1]], x=660, y=640, cw=104, ch=70, gap=6, size=30, base=0)
    S.show(arr)
    lab = label(660, 545, "一维数组 f[0..7]：正在用物品 2（w = 3, v = 4）更新", 26, DIM)
    S.show(lab)
    S.note("一维：已更新的位置 = 新行，未更新的 = 旧行", color=Y)
    S.say("倒序循环（j 从大到小）：算 f[j] 时，f[j−w] 在左边，{c|还没更新}，仍是上一行的值——这就是 0/1 背包。")
    ptr = arr.ptr(V, "j", Y)
    S.play(FadeIn(ptr), dur=0.3)
    w, v = ITEMS[1]
    cur = list(rows[1])
    for j in range(V, w - 1, -1):
        new = max(cur[j], cur[j - w] + v)
        arc = Line(arr.lx(j - w), -arr.ch / 2 - 6, arr.lx(j), -arr.ch / 2 - 6, color=CY, w=4, head=12,
                   bend=-0.4, prog=0.0)
        arc.tr["op"].base = 0.0
        arr.add(arc)
        S.play(arr.move(ptr, j), FadeIn(arc), arc.to(prog=1.0), dur=0.45)
        cur[j] = new
        S.play(arr[j].to(text=show(new), fill=tint(Y, 0.3)), dur=0.35)
        S.play(FadeOut(arc), dur=0.2)
    S.say("每次读到的 f[j−3] 都是灰色的旧值：物品 2 只被用了一次。结果和二维表的第 2 行完全一样。")
    S.play(*[g[2, j].flash(G) for j in range(V + 1)], dur=0.7)
    S.say("如果改成正序循环，算 f[j] 时 f[j−w] 已经是新值——它可能已经含有物品 2，再加一次就是“用两次”。这正是完全背包要的效果。")
    S.note("倒序 → f[j−w] 是旧的 → 0/1；正序 → 新的 → 完全", color=G)
    S.say("所以循环方向不是需要背的规则，而是在选择：f[j−w] 读的是上一行，还是这一行。", extra=0.5)

    # ------------------------------------------------------------ 初值
    S.section("初值决定含义")
    S.say("同样的转移，问“容量不超过 j”和“恰好装满 j”，答案不同。区别只在初值。")
    ex = table01(ITEMS, V, exact=True)
    am = table01(ITEMS, V, exact=False)
    t1 = Array([show(x) for x in ex[0]], x=660, y=300, cw=104, ch=70, gap=6, size=30, base=0)
    t2 = Array([show(x) for x in am[0]], x=660, y=560, cw=104, ch=70, gap=6, size=30, base=0)
    l1 = label(660, 215, "恰好装满：f[0] = 0，其余 −∞", 28, CY)
    l2 = label(660, 475, "不超过：全部为 0", 28, O)
    S.show(t1, t2, l1, l2, lag=0.1)
    S.say("初值就是“一个物品都不选”时的答案。什么都不选，体积恰好是 j 只在 j = 0 时可能，其他容量“做不到”，记为 −∞。")
    S.note("初值 = 一个物品都不选时的答案")
    S.note("恰好：f[0] = 0，f[j>0] = −∞（做不到）", color=CY)
    S.say("而“不超过 j”时，什么都不选对任何容量都合法，价值 0。")
    S.note("不超过：f[j] = 0", color=O)
    S.say("把两个物品依次加进去：")
    S.play(*[t1.cells[j].to(text=show(ex[2][j])) for j in range(V + 1)], *[t2.cells[j].to(text=show(am[2][j])) for j in range(V + 1)],
           dur=0.8, lag=0.03)
    S.say("“恰好”只在能凑出的体积 0、2、3、5 上有值；“不超过”的 f[j] 正好是“恰好”表里 f[0..j] 的最大值。")
    S.play(*[t1.cells[j].to(fill=tint(CY, 0.3)) for j in (0, 2, 3, 5)], dur=0.6)
    S.note("不超过的 f[j] = max(恰好的 f[0..j])")
    S.say("一句话：状态的定义写清楚，初值就是这个定义在“零个物品”时的取值，不需要记。", extra=0.5)

    # ------------------------------------------------------------ 二进制拆分
    S.section("多重背包：二进制拆分")
    S.say("多重背包：第 i 种物品有 c 个。最直接的做法是把它拆成 c 个一模一样的 0/1 物品，复杂度 O(V · Σc)。")
    S.note("朴素：拆成 c 个 0/1 物品，O(V·Σc)")
    S.say("其实我们只关心“这种物品最终用了几个”，用 0 个到 c 个都要能表示，而且不能超过 c 个。")
    S.note("要求：能凑出 0..c 中的每个数量，且不能超过 c", color=Y)
    c = 13
    parts = []
    p = 1
    while sum(parts) + p <= c:
        parts.append(p)
        p *= 2
    if c - sum(parts):
        parts.append(c - sum(parts))
    S.say(f"以 c = {c} 为例：拆成 1、2、4，再加上剩下的 {parts[-1]}。四个“包”各当成一个 0/1 物品，体积和价值都乘上份数。")
    S.note(f"c = {c} → " + "、".join(map(str, parts)) + "（四个 0/1 物品）", color=G)
    bars = []
    x0 = 200
    unit = 58
    cols = [CY, G, O, P]
    for k, q in enumerate(parts):
        b = Rect(x0 + q * unit / 2, 0, q * unit - 6, 50, fill=tint(cols[k], 0.4), stroke=cols[k], sw=2, r=8)
        bars.append(b)
    grp = Group(0, 0)
    yy = 260
    labs = []
    for k, (b, q) in enumerate(zip(bars, parts)):
        b.tr["y"].base = yy + k * 70
        grp.add(b)
        labs.append(grp.add(Text(x0 - 20, yy + k * 70, f"{q} 个", size=26, color=cols[k], anchor="rm")))
    S.show(grp)
    target = label(860, 600, "", 34, Y, anchor="lm")
    S.add(target)

    def combo(m):
        rest = m
        use = []
        if m > sum(parts[:-1]):
            use.append(len(parts) - 1)
            rest -= parts[-1]
        for k in range(len(parts) - 2, -1, -1):
            if rest >= parts[k]:
                use.append(k)
                rest -= parts[k]
        return sorted(use)

    S.say("为什么每个数量都能凑出来？前三个包 1、2、4 用二进制可以凑出 0 到 7 的任何数。")
    for m in (5, 7):
        use = combo(m)
        S.play(*[bars[k].to(fill=tint(cols[k], 0.9) if k in use else tint(cols[k], 0.15)) for k in range(4)],
               target.to(text=f"{m} = " + " + ".join(str(parts[k]) for k in use)), dur=0.6)
        S.wait(0.8)
    S.say(f"大于 7 的数量 m（8 到 13），先拿走最后的 {parts[-1]}，剩下 m − {parts[-1]} 在 2 到 7 之间，又能用 1、2、4 凑出来。")
    for m in (9, 13):
        use = combo(m)
        S.play(*[bars[k].to(fill=tint(cols[k], 0.9) if k in use else tint(cols[k], 0.15)) for k in range(4)],
               target.to(text=f"{m} = " + " + ".join(str(parts[k]) for k in use)), dur=0.6)
        S.wait(0.8)
    S.say("而所有包加起来正好是 13，选得再多也不会超过 c。“不少”和“不多”都成立，所以拆分前后可选的数量集合完全相同。")
    S.note("不少：0..c 都能凑出；不多：总和恰为 c", color=G)
    S.say("为什么最后一份不能也是 8？1+2+4+8 = 15，会凑出 14、15 个，比实际拥有的多——这就是“不多”被破坏了。")
    S.play(target.to(text="1 + 2 + 4 + 8 = 15 > 13 ✗", color=R), dur=0.5)
    S.say("一般地：取 1, 2, 4, …, 2^(k−1)，只要总和不超过 c；最后一份是剩下的 r，r 比 2^k 小。每种物品只拆成 O(log c) 份。")
    S.note("复杂度 O(V · Σ log c)（单调队列还能做到 O(nV)，见第 12 集）")

    # ------------------------------------------------------------ 计数
    S.section("计数：组合还是排列")
    S.say("背包也常用来计数。面值 1 和 2 的硬币各有无限个，凑出 4 有几种方法？")
    S.note("硬币 {1, 2}，凑出 4")
    S.say("如果不计顺序（1+1+2 和 2+1+1 算一种），答案是 3：{1,1,1,1}、{1,1,2}、{2,2}。如果计顺序，答案是 5。")
    S.note("不计顺序：3 种；计顺序：5 种")
    comb = [1, 0, 0, 0, 0]
    perm = [1, 0, 0, 0, 0]
    A1 = Array(comb, x=420, y=360, cw=86, ch=66, gap=6, size=30, base=0)
    A2 = Array(perm, x=420, y=640, cw=86, ch=66, gap=6, size=30, base=0)
    L1 = label(420, 270, "外层物品、内层容量", 28, CY)
    L2 = label(420, 550, "外层容量、内层物品", 28, O)
    S.show(A1, A2, L1, L2, lag=0.1)
    S.say("写法一：外层枚举硬币，内层枚举容量。先把面值 1 全部处理完，再处理面值 2。")
    for coin in (1, 2):
        for j in range(coin, 5):
            comb[j] += comb[j - coin]
            S.play(A1[j].to(text=str(comb[j]), fill=tint(CY, 0.3)), dur=0.3)
        lc = label(820, 300 + coin * 40, f"处理完面值 {coin}：{comb}", 24, DIM, anchor="lm")
        S.show(lc, dur=0.3)
    S.say("这样每种组合只会以“先放所有 1、再放所有 2”这一种顺序被数到，所以数的是组合：3。")
    S.note("外层物品：硬币按固定顺序加入 → 数组合", color=CY)
    S.say("写法二：外层枚举容量 j，内层枚举“最后一枚是哪种硬币”：g[j] = g[j−1] + g[j−2]。")
    for j in range(1, 5):
        perm[j] = perm[j - 1] + (perm[j - 2] if j >= 2 else 0)
        S.play(A2[j].to(text=str(perm[j]), fill=tint(O, 0.3)), dur=0.4)
    S.say("按“最后一枚”分类，1+1+2 和 1+2+1 最后一枚不同，会分别被数到，所以数的是排列：5。")
    S.note("外层容量、按最后一枚分类 → 数排列", color=O)
    S.say("两种写法都对，只是数的东西不同。读题时先想清楚：顺序不同算不算不同的方案。", extra=0.5)

    # ------------------------------------------------------------ 反例
    S.section("反例：方向写反")
    S.say("反过来，如果 0/1 背包用了正序循环，会发生什么？一个物品：体积 2、价值 3，容量 4。")
    arr2 = Array(["0"] * 5, x=660, y=420, cw=110, ch=74, gap=6, size=32, base=0)
    S.show(arr2)
    vals = [0] * 5
    ptr2 = arr2.ptr(2, "j", Y)
    S.play(FadeIn(ptr2), dur=0.3)
    for j in range(2, 5):
        vals[j] = max(vals[j], vals[j - 2] + 3)
        S.play(arr2.move(ptr2, j), arr2[j].to(text=str(vals[j]), fill=tint(R, 0.3) if j == 4 else tint(Y, 0.3)), dur=0.5)
    S.say("f[4] = f[2] + 3 = 6：f[2] 已经是“用过这个物品”的新值，于是这个物品被用了两次。只有一个物品，正确答案是 3。")
    S.play(arr2[4].flash(R), dur=0.8)
    S.note("0/1 背包正序：f[4] = 6（物品用了两次）✗", color=R)

    # ------------------------------------------------------------ 手推题
    S.quiz("面值 1、2、5 的硬币各有无限个，凑出 10。\n\n"
           "(1) 不计顺序有多少种方案？应该用哪种循环顺序？请手推一维数组。\n"
           "(2) 如果计顺序呢？写出递推式。", think=20)
    coins = [1, 2, 5]
    f = [1] + [0] * 10
    arr3 = Array(f, x=640, y=520, cw=92, ch=62, gap=5, size=26, base=0)
    S.say("(1) 不计顺序：外层枚举硬币，内层容量正序（硬币无限个）。")
    S.show(arr3)
    tag = label(640, 430, "初值：f[0] = 1", 26, DIM)
    S.show(tag)
    for c in coins:
        for j in range(c, 11):
            f[j] += f[j - c]
        S.play(*[arr3.cells[j].to(text=str(f[j])) for j in range(11)], tag.to(text=f"加入面值 {c} 后"), dur=0.6)
        S.wait(1.2)
    S.say(f"答案 f[10] = {f[10]}。可以核对：不用 5 有 6 种（2 的个数 0~5），用一个 5 有 3 种，用两个 5 有 1 种。")
    S.note(f"不计顺序：{f[10]}", color=Y)
    g2 = [1] + [0] * 10
    for j in range(1, 11):
        g2[j] = sum(g2[j - c] for c in coins if j >= c)
    S.say(f"(2) 计顺序：外层容量，按最后一枚分类，g[j] = g[j−1] + g[j−2] + g[j−5]，g[0] = 1，得到 g[10] = {g2[10]}。")
    S.note(f"计顺序：g[j] = g[j−1] + g[j−2] + g[j−5]，g[10] = {g2[10]}", color=Y)
    S.play(*[arr3.cells[j].to(text=str(g2[j]), fill=tint(O, 0.25)) for j in range(11)], tag.to(text="计顺序的 g[0..10]"),
           dur=0.6)

    S.recap([
        "一维背包的循环方向，决定 f[j−w] 读到的是上一行（旧，0/1）还是这一行（新，完全）。",
        "初值就是“一个物品都不选”时状态定义的取值：恰好装满用 −∞ 表示做不到，不超过则全为 0。",
        "多重背包二进制拆分成 1, 2, 4, …, 余数：能凑出 0..c 的每个数量，又不会超过 c，O(V Σ log c)。",
        "计数时外层物品数组合，外层容量（按最后一个分类）数排列。",
    ], next_title="背包变式（下）：依赖关系——分组与树形背包")
