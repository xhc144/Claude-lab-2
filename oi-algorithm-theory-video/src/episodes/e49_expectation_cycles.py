"""第 49 集 概率与期望 DP（下）：带环的期望"""

from fractions import Fraction as Fr
import random

from episodes.common import *
from episodes.e48_expectation_dp import fr


def walk_line(n):
    """0..n 上的随机游走（0 处只能向右），从 0 走到 n 的期望步数；d[i] = 从 i 第一次走到 i+1 的期望步数。"""
    d = [Fr(1)]
    for i in range(1, n):
        d.append(2 + d[-1])
    return d


def build(S):
    S.cover("掷骰子直到掷出 6、来回游走直到走到终点……状态会回到自己或者回到之前，倒推的顺序不存在了。带环的期望怎么求？",
            ["概率与期望 DP（上）（第 48 集）"])

    # ------------------------------------------------------------ 自环
    S.section("原地不动：解一个方程")
    S.say("掷一个骰子，直到掷出 6 为止，期望掷几次？设答案为 E。")
    a = Group(420, 400)
    a.add(Circle(0, 0, 66, fill=tint(CY, 0.3), stroke=CY, sw=3), Text(0, 0, "还没掷出 6", size=22))
    b = Group(860, 400)
    b.add(Circle(0, 0, 66, fill=tint(G, 0.3), stroke=G, sw=3), Text(0, 0, "结束", size=26))
    loop = Arc(420, 300, 46, 110, 320, color=O, w=3)
    l1 = Line(490, 400, 790, 400, color=G, w=3, head=14)
    S.show(a, b, l1, loop, label(640, 370, "1/6", 28, G), label(420, 220, "5/6", 28, O), dur=0.6)
    S.say("掷一次后：1/6 的概率结束；5/6 的概率回到原来的状态——而且“从这里出发还要多少次”和刚才一模一样，还是 E。")
    S.note("E = 1 + (5/6)·E + (1/6)·0", color=Y)
    S.say("于是 E = 1 + (5/6)E。状态指向自己，不能“先算后面再算前面”，但可以把 E 当未知数解方程：E/6 = 1，E = 6。")
    S.note("E = 6；一般地，成功概率 p 的几何分布期望 1/p", color=G)
    S.say("一般地，每次成功概率为 p，期望 1/p 次。带环的期望 DP，本质上就是解一个线性方程组。", extra=0.3)
    S.note("带环：状态的期望满足线性方程组")

    # ------------------------------------------------------------ 链上游走
    S.section("链上的随机游走：递推消元")
    n = 4
    d = walk_line(n)
    xs = [260 + 190 * i for i in range(n + 1)]
    nodes = []
    for i in range(n + 1):
        c = Group(xs[i], 420)
        c.add(Circle(0, 0, 36, fill=tint(G, 0.3) if i == n else BG3, stroke=G if i == n else LINE2, sw=2.5),
              Text(0, 0, str(i), size=28))
        nodes.append(c)
    edges = [Line(xs[i] + 40, 420, xs[i + 1] - 40, 420, color=LINE2, w=3) for i in range(n)]
    S.show(*edges, *nodes, dur=0.6)
    S.say(f"点 0～{n} 排成一条链。在 0 只能往右；在中间的点，各以 1/2 的概率往左或往右。从 0 出发走到 {n}，期望几步？")
    S.say("E[i] = 1 + ½E[i − 1] + ½E[i + 1]：每个方程同时用到左右两边，没有可以“先算”的方向。直接高斯消元是 O(n³)，可链的结构更简单。")
    S.note("E[i] = 1 + ½E[i − 1] + ½E[i + 1]：左右互相依赖", color=Y)
    S.say("换个状态：设 dᵢ = 从 i 出发、第一次到达 i + 1 的期望步数。走到 n 必须依次跨过每一条边，所以答案 = d₀ + d₁ + … + dₙ₋₁。")
    S.note("dᵢ = 从 i 第一次走到 i + 1 的期望步数；答案 = Σdᵢ", color=G)
    tags = [label((xs[i] + xs[i + 1]) / 2, 360, "", 28, Y) for i in range(n)]
    S.add(*tags)
    S.play(tags[0].to(text=f"d₀ = {fr(d[0])}"), dur=0.5)
    S.say("d₀ = 1：在 0 只能往右。")
    S.say("在 i（i ≥ 1）：走一步，1/2 直接到 i + 1；1/2 退到 i − 1，要先花 dᵢ₋₁ 回到 i，再花 dᵢ 到 i + 1。所以 dᵢ = 1 + ½(dᵢ₋₁ + dᵢ)，即 dᵢ = dᵢ₋₁ + 2。")
    S.note("dᵢ = 1 + ½(dᵢ₋₁ + dᵢ) ⇒ dᵢ = dᵢ₋₁ + 2", color=Y)
    for i in range(1, n):
        S.play(tags[i].to(text=f"d{''.join('₀₁₂₃₄₅₆₇₈₉'[int(c)] for c in str(i))} = {fr(d[i])}"),
               edges[i].to(color=Y, w=4), dur=0.5)
    tot = sum(d)
    S.say(f"dᵢ = 2i + 1，答案 = 1 + 3 + 5 + 7 = {fr(tot)} = {n}²。一般地从 0 走到 n 期望 n² 步。")
    rng = random.Random(1)
    sims = []
    for _ in range(20000):
        p, c = 0, 0
        while p < n:
            p = p + 1 if p == 0 or rng.random() < 0.5 else p - 1
            c += 1
        sims.append(c)
    S.note(f"答案 Σ(2i + 1) = n²（这里 {fr(tot)}；随机模拟 2 万次平均 {sum(sims) / len(sims):.2f}）", color=G)
    S.say("技巧在于：每个未知数只和相邻的有关时，可以把 E[i] 表示成“下一个未知数的一次函数”，一路代下去，O(n) 消元。树上也可以这样做。", extra=0.3)
    S.note("链、树上：用相邻未知数表示，逐个代入，O(n) 消元")

    # ------------------------------------------------------------ 优惠券
    S.section("收集优惠券")
    m = 4
    S.say(f"每次随机得到 {m} 种卡片中的一种（等概率），集齐所有种类期望要抽几次？")
    S.say("按“已经集到几种”分段。已有 k 种时，抽到新卡的概率是 (n − k)/n——这一段就是“直到成功”的几何分布，期望 n/(n − k) 次。")
    S.note("已有 k 种：下一种新卡期望 n/(n − k) 次", color=Y)
    stages = [Fr(m, m - k) for k in range(m)]
    bars = []
    for k, e in enumerate(stages):
        h = float(e) * 70
        x = 330 + 170 * k
        r = Rect(x, 640 - h / 2, 110, h, fill=tint(P, 0.5), stroke=P, sw=2, r=10)
        r.tr["op"].base = 0
        t = label(x, 640 - h - 26, fr(e), 28, Y)
        cap = label(x, 680, f"已有 {k} 种", 24, DIM)
        bars.append((r, t, cap))
        S.add(r)
        S.play(FadeIn(r, dy=10), FadeIn(t), FadeIn(cap), dur=0.45)
    tot2 = sum(stages)
    S.say(f"由线性性，总期望 = 各段之和 = {' + '.join(fr(e) for e in stages)} = {fr(tot2)} ≈ {float(tot2):.2f} 次。")
    S.note(f"总期望 n·(1 + 1/2 + … + 1/n) = n·Hₙ；n = {m} 时 {fr(tot2)}", color=G)
    S.say("越到后面越难：最后一种平均要 n 次。总体约 n ln n。注意这里没解方程——把过程切成几段几何分布，用线性性加起来就行。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    E0 = Fr(42)
    E1 = 1 + Fr(5, 6) * E0
    assert E0 == 1 + Fr(5, 6) * E0 + Fr(1, 6) * E1
    S.quiz("(1) 掷一个骰子，直到连续两次掷出 6 为止，期望一共掷几次？（提示：状态是“末尾连着几个 6”。）\n"
           "(2) 集齐 3 种卡片，期望要抽几次？", think=20)
    S.say("(1) E₀：末尾没有 6；E₁：末尾是一个 6。E₁ = 1 + (5/6)E₀ + (1/6)·0；E₀ = 1 + (5/6)E₀ + (1/6)E₁。")
    S.note("(1) E₁ = 1 + (5/6)E₀；E₀ = 1 + (5/6)E₀ + (1/6)E₁", color=Y)
    S.say(f"把 E₁ 代入：E₀ = 1 + (5/6)E₀ + 1/6 + (5/36)E₀，即 (1/36)E₀ = 7/6，E₀ = {fr(E0)}。")
    S.note(f"(1) E₀ = {fr(E0)}", color=G)
    q2 = sum(Fr(3, 3 - k) for k in range(3))
    S.say(f"(2) 3/3 + 3/2 + 3/1 = {fr(q2)}，即 {float(q2)} 次。", extra=0.5)
    S.note(f"(2) 3·(1 + 1/2 + 1/3) = {fr(q2)}", color=G)

    S.recap([
        "状态会回到自己时，期望满足方程：E = 1 + (1 − p)E ⇒ E = 1/p。",
        "一般带环的期望是线性方程组；链、树结构可以逐个代入消元，O(n)。",
        "换状态常能化简：“第一次从 i 到 i + 1 的期望”让链上游走变成简单递推，答案 n²。",
        "收集优惠券：切成几段几何分布，用线性性相加，n·Hₙ。",
    ], next_title="可持久化线段树")
