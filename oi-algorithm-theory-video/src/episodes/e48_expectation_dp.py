"""第 48 集 概率与期望 DP（上）：期望的线性性与倒推"""

from fractions import Fraction as Fr
from itertools import permutations, product

from episodes.common import *


def fr(x):
    x = Fr(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def walk_expect(n, steps):
    """从格子 i 出发，每次等概率前进 steps 里的一个步数，到达或越过 n 停止：期望步数 E[i]。"""
    E = {}
    for i in range(n + max(steps), -1, -1):
        if i >= n:
            E[i] = Fr(0)
        else:
            E[i] = 1 + sum(E[i + s] for s in steps) / len(steps)
    return E


def build(S):
    S.cover("随机过程问“平均要多少步”“平均有多少个”。概率分布往往很复杂，可期望有两件利器：线性性，和从终点倒着推。",
            ["概率的基本概念", "DAG 上的 DP"])

    # ------------------------------------------------------------ 线性性
    S.section("期望的线性性：不需要独立")
    S.say("随机变量 X 的期望 E[X] = Σ 取值 × 概率。最重要的性质：E[X + Y] = E[X] + E[Y]，对任何 X、Y 都成立，不要求独立。")
    S.note("E[X + Y] = E[X] + E[Y]（任何时候都成立）", color=Y)
    rows = []
    for t, (a, b) in enumerate([("X = 第一个骰子", "E = 7/2"), ("Y = 7 − X（完全由 X 决定）", "E = 7/2"),
                                ("X + Y = 7（恒等于 7）", "E = 7")]):
        y = 260 + 80 * t
        rows += [label(200, y, a, 30, FG, anchor="lm"), label(900, y, b, 30, Y if t == 2 else CY, anchor="lm")]
    S.show(*rows, dur=0.6, lag=0.1)
    S.say("例：X 是骰子点数，Y = 7 − X 和 X 完全相关，可 E[X + Y] = 7/2 + 7/2 = 7 照样成立。证明只用到求和可以拆开：Σ(x + y)p = Σxp + Σyp。")
    S.say("这让我们可以把一个复杂的量拆成很多简单的量分别求期望，完全不用管它们之间的关系。", extra=0.3)

    # ------------------------------------------------------------ 指示变量
    S.section("指示变量：把“个数”拆成很多个 0/1")
    n = 4
    perms = list(permutations(range(n)))
    fixed = sum(sum(p[i] == i for i in range(n)) for p in perms)
    S.say(f"随机打乱 1～{n}，期望有多少个位置上的数没动（不动点）？直接算分布：0 个、1 个……每种有几个排列？很麻烦。")
    S.say("拆开：令 Iᵢ = 1 表示“位置 i 没动”，否则为 0。不动点个数 X = I₁ + I₂ + … + Iₙ。")
    S.note("指示变量：E[Iᵢ] = P(事件 i 发生)", color=Y)
    cells = Array([f"I{i + 1}" for i in range(n)], x=640, y=330, cw=120, ch=64, gap=16, size=30, index=False,
                  fill=tint(CY, 0.2))
    S.show(cells)
    probs = Array(["1/4"] * n, x=640, y=480, cw=120, ch=56, gap=16, size=28, index=False, fill=tint(G, 0.2))
    S.show(probs, label(640, 400, "每个 E[Iᵢ] = P(位置 i 没动) = 1/n", 26, G))
    S.say(f"E[Iᵢ] = P(位置 i 没动) = 1/{n}。由线性性，E[X] = {n} × 1/{n} = 1。不管 n 是多少，期望都是 1 个不动点。")
    assert Fr(fixed, len(perms)) == 1
    S.note("随机排列的不动点个数：期望 = n · (1/n) = 1", color=G)
    S.say(f"验算：{n}! = {len(perms)} 个排列一共有 {fixed} 个不动点，平均恰好 1 个。注意各个 Iᵢ 之间并不独立，但线性性不在乎。", extra=0.3)

    # ------------------------------------------------------------ 倒推
    S.section("倒着推：从终点定义状态")
    L = 6
    steps = (1, 2)
    E = walk_expect(L, steps)
    S.say(f"格子 0～{L}，从 0 出发，每次掷硬币：正面前进 1 格，反面前进 2 格，到达或越过 {L} 就停。期望掷几次？")
    board = Array([str(i) for i in range(L + 2)], x=640, y=260, cw=100, ch=64, gap=10, size=28, index=False)
    for i in range(L, L + 2):
        board.cells[i].box.tr["fill"].base = tint(G, 0.3)
    S.show(board, label(640, 180, "格子", 24, DIM))
    S.say("正着想：从 0 出发，第 k 步走到每个格子的概率……要追踪整个分布，而且“停下”的时刻各不相同，很难写。")
    S.say("倒着想：设 E[i] = 从格子 i 出发、还要掷的期望次数。终点 E[i] = 0（i ≥ 6）；其他格子掷一次，再分两种情况各占一半。")
    S.note("E[i] = 1 + ½E[i + 1] + ½E[i + 2]；E[≥ n] = 0", color=Y)
    ev = Array([""] * (L + 2), x=640, y=380, cw=100, ch=56, gap=10, size=24, index=False, fill=tint(B, 0.15))
    S.show(ev, label(130, 380, "E", 30, B, anchor="lm"))
    for i in range(L + 1, -1, -1):
        anims = [ev.cells[i].to(text=fr(E[i]), fill=tint(B, 0.35))]
        if i < L:
            anims += [ev.cells[i + 1].to(stroke=O, sw=3), ev.cells[i + 2].to(stroke=O, sw=3)]
        S.play(*anims, dur=0.4)
        if i == L - 2:
            S.say(f"E[{i}] = 1 + ½·E[{i + 1}] + ½·E[{i + 2}] = 1 + ½·{fr(E[i + 1])} + ½·{fr(E[i + 2])} = {fr(E[i])}。从右往左，每一格只依赖右边已经算好的。")
        if i < L:
            S.play(ev.cells[i + 1].to(stroke=LINE, sw=2), ev.cells[i + 2].to(stroke=LINE, sw=2), dur=0.15)
    S.say(f"答案 E[0] = {fr(E[0])} ≈ {float(E[0]):.2f} 次。")
    S.note(f"答案 E[0] = {fr(E[0])}", color=G)
    S.say("为什么倒推方便？“从 i 出发还要多少步”只和 i 有关，与怎么走到 i 无关；而起点只有一个，答案就是 E[起点]。正推则要先知道到达每个状态的概率。", extra=0.3)
    S.note("倒推：状态 = “从这里出发的未来”，与来路无关", color=Y)

    # ------------------------------------------------------------ DAG
    S.section("一般形式：DAG 上按逆拓扑序")
    pos = {"s": (-330, 0), "a": (-60, -150), "b": (-60, 150), "c": (220, 0), "t": (480, 0)}
    E2 = [("s", "a", 2), ("s", "b", 1), ("a", "c", 2), ("a", "t", 6), ("b", "c", 3), ("c", "t", 1)]
    g = Graph(pos, E2, x=600, y=430, directed=True, r=34, size=26, wcolor=FG)
    S.show(g)
    S.say("一般地：DAG 上从 s 出发，每到一个点就等概率选一条出边走，边上数字是长度。到达 t 的期望总长度是多少？")
    out = {}
    for u, v, w in E2:
        out.setdefault(u, []).append((v, w))
    order = ["t", "c", "b", "a", "s"]
    EV = {}
    tags = {}
    for u in order:
        if u == "t":
            EV[u] = Fr(0)
        else:
            EV[u] = sum(w + EV[v] for v, w in out[u]) / len(out[u])
        tags[u] = g.tag(u, f"E = {fr(EV[u])}", "d" if u in ("b", "c") else "u", Y, 24, gap=10)
        S.play(FadeIn(tags[u]), g[u].to(fill=tint(Y, 0.3)), dur=0.5)
        if u == "a":
            S.say(f"E[a] = ½(2 + E[c]) + ½(6 + E[t]) = ½·{2 + EV['c']} + ½·6 = {fr(EV['a'])}。每个点等于“走一步的长度 + 下一个点的期望”的平均。")
    S.say(f"按逆拓扑序（t, c, b, a, s）算下来，E[s] = {fr(EV['s'])}。")
    S.note("E[u] = Σ p(u → v) · (w + E[v])，按逆拓扑序计算", color=G)

    # ------------------------------------------------------------ 手推题
    q = walk_expect(4, (1, 2, 3))
    nb, m = 3, 3
    empty = Fr(nb) * Fr(nb - 1, nb) ** m
    brute = Fr(sum(sum(1 for b in range(nb) if b not in xs) for xs in product(range(nb), repeat=m)), nb ** m)
    assert empty == brute
    S.quiz("(1) 把 3 个球独立、均匀地放进 3 个盒子，期望有几个空盒子？\n"
           "(2) 从格子 0 出发，每次等概率前进 1、2 或 3 格，到达或越过格子 4 就停。期望走几步？", think=20)
    S.say(f"(1) 指示变量：盒子 j 为空的概率是 (2/3)³ = 8/27，3 个盒子：期望 3 × 8/27 = {fr(empty)} 个。")
    S.note(f"(1) 3 · (2/3)³ = {fr(empty)}", color=Y)
    S.say(f"(2) 倒推：E[4] = E[5] = E[6] = 0，E[3] = {fr(q[3])}，E[2] = 1 + (E[3] + E[4] + E[5])/3 = {fr(q[2])}，"
          f"E[1] = {fr(q[1])}，E[0] = {fr(q[0])}。")
    S.say(f"所以期望走 {fr(q[0])} ≈ {float(q[0]):.2f} 步。", extra=0.5)
    S.note(f"(2) E[0] = {fr(q[0])}", color=G)

    S.recap([
        "期望的线性性 E[X + Y] = E[X] + E[Y] 不要求独立。",
        "指示变量：把“个数”拆成 0/1 变量之和，期望 = 各事件概率之和。",
        "期望 DP 常倒着推：状态定义为“从这里出发的未来”，终点为 0，答案是起点的值。",
        "DAG 上：E[u] = Σ p(u → v)(w + E[v])，按逆拓扑序计算。",
    ], next_title="概率与期望 DP（下）：带环的期望")
