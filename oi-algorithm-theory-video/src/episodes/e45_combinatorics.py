"""第 45 集 组合计数建模：把问题变成标准模型"""

from itertools import product
from math import comb

from episodes.common import *


def count_solutions(n, k, low=1):
    return sum(1 for xs in product(range(low, n + 1), repeat=k) if sum(xs) == n)


def catalan_paths(n):
    """从 (0,0) 到 (n,n)、始终 y ≤ x 的路径数（暴力）。"""
    cnt = 0
    for bits in product((0, 1), repeat=2 * n):
        if sum(bits) != n:
            continue
        x = y = 0
        ok = True
        for b in bits:
            if b:
                y += 1
            else:
                x += 1
            if y > x:
                ok = False
                break
        cnt += ok
    return cnt


def build(S):
    S.cover("很多计数题换一个角度看，就变成了几个标准模型：插板、网格路径、卡特兰数。关键是找到一一对应——怎么找？",
            ["排列组合数 C(n, k)", "加法原理、乘法原理"])

    # ------------------------------------------------------------ 插板
    S.section("插板法：把“拆分”变成“选空隙”")
    n, k = 7, 3
    assert count_solutions(n, k) == comb(n - 1, k - 1)
    S.say(f"问题：x₁ + x₂ + x₃ = {n}，每个 xᵢ 都是正整数，有几组解？等价于：{n} 个相同的球分给 3 个人，每人至少一个。")
    S.note("x₁ + … + xₖ = n，xᵢ ≥ 1 的解数", color=Y)
    gap = 110
    x0 = 640 - (n - 1) * gap / 2
    balls = [Circle(x0 + i * gap, 330, 26, fill=tint(CY, 0.55), stroke=CY, sw=2) for i in range(n)]
    S.show(*balls, dur=0.6, lag=0.05)
    gaps = [Line(x0 + (i + 0.5) * gap, 300, x0 + (i + 0.5) * gap, 360, color=alpha(DIM, 0.6), w=2, dash=(5, 5))
            for i in range(n - 1)]
    S.show(*gaps, dur=0.4)
    S.say(f"{n} 个球排成一排，中间有 {n - 1} 个空隙（虚线）。插 2 块板把球分成 3 段，每段至少一个球——每种插法恰好对应一组解。")
    choices = [(1, 4), (0, 5), (2, 3)]
    bars = [Rect(0, 330, 8, 110, fill=Y, stroke=None, sw=0, r=4) for _ in range(2)]
    for b in bars:
        b.tr["op"].base = 0
        S.add(b)
    res = label(640, 470, "", 32, Y)
    S.add(res)
    for t, (i, j) in enumerate(choices):
        xs = (i + 1, j - i, n - 1 - j)
        S.play(*([FadeIn(bars[0]), FadeIn(bars[1])] if t == 0 else []),
               bars[0].to(x=x0 + (i + 0.5) * gap), bars[1].to(x=x0 + (j + 0.5) * gap),
               res.to(text=f"x = ({xs[0]}, {xs[1]}, {xs[2]})"), dur=0.6)
        S.wait(0.6)
    S.say(f"所以答案是从 {n - 1} 个空隙里选 2 个：C({n - 1}, 2) = {comb(n - 1, 2)}。一般地是 C(n − 1, k − 1)。")
    S.note("插板：C(n − 1, k − 1)", color=G)
    S.say("如果允许 xᵢ = 0？令 yᵢ = xᵢ + 1 ≥ 1，方程变成 y₁ + … + yₖ = n + k，答案 C(n + k − 1, k − 1)。")
    S.say("一般的下界 xᵢ ≥ lᵢ 也一样：先把下界“预先发掉”，剩下的部分再插板。上界不好处理，要用下一集的容斥。", extra=0.3)
    S.note("xᵢ ≥ 0：C(n + k − 1, k − 1)；下界先减掉；上界用容斥", color=Y)

    # ------------------------------------------------------------ 网格路径
    S.section("网格路径：选哪几步向上")
    N = 4
    cell = 90
    ox, oy = 250, 760

    def pt(i, j):
        return ox + i * cell, oy - j * cell

    lattice = Group(0, 0)
    for i in range(N + 1):
        lattice.add(Line(*pt(i, 0), *pt(i, N + 1), color=alpha(LINE2, 0.6), w=1.5))
    for j in range(N + 2):
        lattice.add(Line(*pt(0, j), *pt(N, j), color=alpha(LINE2, 0.6), w=1.5))
    S.show(lattice, label(pt(0, 0)[0] - 30, pt(0, 0)[1] + 30, "(0, 0)", 22, DIM),
           label(pt(N, N)[0] + 40, pt(N, N)[1] - 30, f"({N}, {N})", 22, DIM))
    S.say(f"从 (0, 0) 走到 ({N}, {N})，每步向右或向上一格，有几条路？")
    path = "RURRUURU"

    def poly_of(steps, color, w=5):
        pts = [pt(0, 0)]
        i = j = 0
        for c in steps:
            if c == "R":
                i += 1
            else:
                j += 1
            pts.append(pt(i, j))
        pl = Poly(pts, stroke=color, sw=w, closed=False)
        pl.tr["op"].base = 0
        return pl

    p1 = poly_of(path, CY)
    S.add(p1)
    S.play(FadeIn(p1), dur=0.6)
    seq = label(860, 300, "步骤：" + "、".join("右" if c == "R" else "上" for c in path), 28, CY, anchor="lm")
    S.show(seq)
    S.say(f"一条路径就是 {2 * N} 步的序列，其中恰好 {N} 步向上。选出哪 {N} 步向上，路径就确定了：C({2 * N}, {N}) = {comb(2 * N, N)} 条。")
    S.note("(0,0) → (m, n) 的单调路径数 = C(m + n, n)", color=G)
    S.say("这就是“建模”：路径 ↔ 0/1 序列 ↔ 选子集。只要能建立一一对应，就能借用已知的计数结果。")

    # ------------------------------------------------------------ 卡特兰
    S.section("加一条限制：不越过对角线", keep=[lattice])
    diag = Line(*pt(0, 0), *pt(N, N), color=alpha(G, 0.7), w=2.5, dash=(8, 6))
    bad_line = Line(*pt(0, 1), *pt(N - 1, N), color=alpha(R, 0.8), w=2.5, dash=(8, 6))
    S.show(diag)
    S.say("现在要求路径始终不走到对角线上方（任何时刻向上的步数 ≤ 向右的步数）。好的路径有几条？")
    S.note("限制：任何前缀里 上 ≤ 右（不越过对角线）", color=Y)
    S.say("正难则反：数“坏”路径。坏路径一定会碰到直线 y = x + 1（红色虚线）。")
    S.show(bad_line)
    badp = "RUURRUUR"
    pb = poly_of(badp, R)
    S.add(pb)
    S.play(FadeIn(pb), dur=0.6)
    # 第一次碰到红线的位置
    i = j = 0
    first = None
    for t, c in enumerate(badp):
        if c == "R":
            i += 1
        else:
            j += 1
        if j == i + 1 and first is None:
            first = t + 1
    refl = badp[:first] + "".join("U" if c == "R" else "R" for c in badp[first:])
    pr = poly_of(refl, O)
    S.add(pr)
    i = j = 0
    for c in badp[:first]:
        i, j = (i + 1, j) if c == "R" else (i, j + 1)
    touch = Circle(*pt(i, j), 10, fill=Y, stroke=None, sw=0)
    touch.tr["op"].base = 0
    S.add(touch)
    S.play(FadeIn(touch, scale=0.3), dur=0.4)
    S.say("把坏路径在第一次碰到红线之后的部分，关于红线翻折（右变上、上变右），终点就从 (4, 4) 变成了 (3, 5)。")
    S.play(FadeIn(pr), dur=0.8)
    S.show(label(pt(N - 1, N + 1)[0] - 50, pt(N - 1, N + 1)[1] - 24, f"({N - 1}, {N + 1})", 22, O))
    S.say("反过来，每条到 (3, 5) 的路径都必然穿过红线，把第一次碰线后的部分翻回来，就得到一条坏路径。这是一一对应。")
    S.note("反射：坏路径 ↔ 到 (n − 1, n + 1) 的路径", color=O)
    good = comb(2 * N, N) - comb(2 * N, N + 1)
    assert good == catalan_paths(N)
    S.say(f"所以好路径 = C({2 * N}, {N}) − C({2 * N}, {N + 1}) = {comb(2 * N, N)} − {comb(2 * N, N + 1)} = {good}。这就是卡特兰数 Cₙ = C(2n, n)/(n + 1)。")
    S.note(f"卡特兰数 Cₙ = C(2n, n) − C(2n, n + 1) = C(2n, n)/(n + 1)；C₄ = {good}", color=G)

    # ------------------------------------------------------------ 双射
    S.section("双射：同一个数出现在很多地方")
    S.say("卡特兰数为什么常见？因为很多结构都能和“不越过对角线的路径”一一对应。")
    items = [
        ("括号序列", "右 → (，上 → )：任何前缀左括号不少于右括号"),
        ("出栈序列", "右 → 入栈，上 → 出栈：栈里元素不能是负数"),
        ("二叉树", "n 个结点的二叉树个数满足同样的递推 C(n+1) = Σ CᵢCₙ₋ᵢ"),
        ("凸多边形三角剖分", "n + 2 边形的三角剖分数"),
    ]
    rows = []
    for t, (a, b) in enumerate(items):
        y = 240 + 110 * t
        g = Group(0, 0)
        g.add(Rect(330, y, 300, 70, fill=tint(P, 0.25), stroke=P, sw=1.5, r=14))
        g.add(label(330, y, a, 28, FG, chain="bold"))
        g.add(para(510, y - 20, b, size=26, maxw=720))
        rows.append(g)
    S.show(*rows, dur=0.6, lag=0.25)
    S.say("建模的关键是验证“一一对应”：每个对象对应唯一一条路径，每条路径也能还原出唯一一个对象。做到这一点，计数结果就可以直接搬过来。", extra=0.3)
    S.note("双射：每个对象 ↔ 唯一一条路径；两个方向都要验证", color=Y)

    # ------------------------------------------------------------ 手推题
    q1 = count_solutions(10, 4, low=2)
    S.quiz("(1) 10 个相同的球放进 4 个不同的盒子，每个盒子至少 2 个，有几种放法？\n"
           "(2) 4 个人排队买票，每张票 5 元，其中 2 人拿 5 元、2 人拿 10 元，售票员一开始没有零钱。有几种排队顺序能让所有人都顺利买到票（同类人不区分）？", think=20)
    S.say(f"(1) 每个盒子先放 2 个，还剩 2 个，分给 4 个盒子（可以为 0）：C(2 + 3, 3) = {comb(5, 3)}。")
    assert q1 == comb(5, 3)
    S.note(f"(1) 先发下界，再插板：C(5, 3) = {comb(5, 3)}", color=Y)
    S.say("(2) 拿 5 元的看成“右”，拿 10 元的看成“上”：任何时刻找零需要的 5 元不能多于收到的，正是“上 ≤ 右”。")
    S.say(f"所以是 n = 2 的卡特兰数：C(4, 2) − C(4, 3) = {comb(4, 2) - comb(4, 3)}，即 (5,5,10,10) 和 (5,10,5,10) 两种。", extra=0.5)
    S.note(f"(2) 建模成路径：卡特兰数 C₂ = {comb(4, 2) - comb(4, 3)}", color=G)

    S.recap([
        "插板：x₁ + … + xₖ = n（xᵢ ≥ 1）有 C(n − 1, k − 1) 组解；下界先发掉，xᵢ ≥ 0 时是 C(n + k − 1, k − 1)。",
        "单调网格路径 = 选哪几步向上：C(m + n, n)。",
        "反射法：越过对角线的路径 ↔ 到 (n − 1, n + 1) 的路径，得到卡特兰数 C(2n, n) − C(2n, n + 1)。",
        "建模的核心是双射：两个方向都能唯一还原，计数结果才能搬过来。",
    ], next_title="容斥原理")
