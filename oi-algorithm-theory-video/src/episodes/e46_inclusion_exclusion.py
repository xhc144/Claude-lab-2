"""第 46 集 容斥原理：多减了就加回来"""

from itertools import permutations, product
from math import comb, factorial

from episodes.common import *

N = 30
DIV = [2, 3, 5]


def derange(n):
    return sum(1 for p in permutations(range(n)) if all(p[i] != i for i in range(n)))


def bounded(n, k, ub):
    return sum(1 for xs in product(range(ub + 1), repeat=k) if sum(xs) == n)


def build(S):
    S.cover("1～30 里，能被 2、3、5 中至少一个整除的数有几个？直接相加会重复，减掉重复又可能减多……怎样保证每个数恰好算一次？",
            ["组合数", "插板法（第 45 集）"])

    sets = [{x for x in range(1, N + 1) if x % d == 0} for d in DIV]
    union = set().union(*sets)

    # ------------------------------------------------------------ 韦恩图
    S.section("三个集合：加、减、再加")
    cx, cy, rr = 470, 470, 175
    cents = [(cx - 95, cy - 70), (cx + 95, cy - 70), (cx, cy + 95)]
    cols = [CY, O, G]
    circ = []
    for (x, y), c in zip(cents, cols):
        ci = Circle(x, y, rr, fill=alpha(c, 0.10), stroke=c, sw=2.5)
        circ.append(ci)
    names = [label(cents[0][0] - 150, cents[0][1] - 150, "A：2 的倍数", 26, CY),
             label(cents[1][0] + 150, cents[1][1] - 150, "B：3 的倍数", 26, O),
             label(cents[2][0], cents[2][1] + 215, "C：5 的倍数", 26, G)]
    S.show(*circ, *names, dur=0.8, lag=0.1)
    # 七个区域的代表点和元素个数
    regions = {}
    for mask in range(1, 8):
        ins = [bool(mask >> i & 1) for i in range(3)]
        cnt = sum(1 for x in union if all((x in sets[i]) == ins[i] for i in range(3)))
        regions[mask] = cnt
    rpos = {1: (cx - 175, cy - 110), 2: (cx + 175, cy - 110), 4: (cx, cy + 190), 3: (cx, cy - 135),
            5: (cx - 90, cy + 65), 6: (cx + 90, cy + 65), 7: (cx, cy)}
    rl = {m: label(*rpos[m], "", 28, FG) for m in rpos}
    S.add(*rl.values())
    S.say(f"A、B、C 分别是 1～{N} 里 2、3、5 的倍数。图里分成 7 块，每块写的是“这块里的数被算了几次”。")
    S.note("|A ∪ B ∪ C| = Σ|A| − Σ|A ∩ B| + |A ∩ B ∩ C|", color=Y)
    counted = {m: 0 for m in rpos}
    steps = [
        ([1, 2, 4], +1, f"先加上 |A| + |B| + |C| = {len(sets[0])} + {len(sets[1])} + {len(sets[2])} = {sum(map(len, sets))}。"
                         "两块重叠的地方被算了 2 次，中间算了 3 次。"),
        ([3, 5, 6], -1, f"减去两两的交：|A∩B| + |A∩C| + |B∩C| = {len(sets[0] & sets[1])} + {len(sets[0] & sets[2])} + {len(sets[1] & sets[2])}。"
                         "重叠处变回 1 次，可中间被减了 3 次，变成 0 次。"),
        ([7], +1, f"再加回三者的交 |A∩B∩C| = {len(sets[0] & sets[1] & sets[2])}：每一块都恰好是 1 次。"),
    ]
    for masks, sgn, text in steps:
        for m in rpos:
            if any((m & mm) == mm for mm in masks):
                counted[m] += sgn * sum(1 for mm in masks if (m & mm) == mm)
        S.play(*[rl[m].to(text=f"{counted[m]} 次", color=Y if counted[m] == 1 else (R if counted[m] != 1 else FG)) for m in rpos],
               dur=0.6)
        S.say(text)
        S.flush()
    total = sum(map(len, sets)) - len(sets[0] & sets[1]) - len(sets[0] & sets[2]) - len(sets[1] & sets[2]) + len(sets[0] & sets[1] & sets[2])
    assert total == len(union)
    S.say(f"所以 |A ∪ B ∪ C| = {sum(map(len, sets))} − {len(sets[0] & sets[1]) + len(sets[0] & sets[2]) + len(sets[1] & sets[2])} + {len(sets[0] & sets[1] & sets[2])} = {total}。")
    S.note(f"1～{N} 中被 2、3、5 之一整除的数：{total} 个", color=G)

    # ------------------------------------------------------------ 一般情形
    S.section("为什么每个元素恰好算一次")
    S.say("一般形式：对所有非空的条件子集 T 求交集的大小，按 |T| 的奇偶加或减。")
    S.note("|A₁ ∪ … ∪ Aₙ| = Σ (−1)^{|T|+1} |∩ T|（T 取遍非空子集）", color=Y)
    S.say("看一个恰好属于 t 个集合的元素（t ≥ 1）。它出现在“从这 t 个里选出 j 个”的交集里，被计了 C(t, 1) − C(t, 2) + C(t, 3) − … 次。")
    rows = []
    for t in range(1, 5):
        terms = " − ".join(f"C({t},{j})" if j % 2 == 0 else f"C({t},{j})" for j in range(1, t + 1))
        vals = [comb(t, j) * (1 if j % 2 else -1) for j in range(1, t + 1)]
        expr = " ".join(("+ " if v > 0 and k else ("− " if v < 0 else "")) + str(abs(v)) for k, v in enumerate(vals))
        rows.append([str(t), expr, str(sum(vals))])
    tb = Grid(4, 3, x=640, y=460, cw=230, ch=56, gap=4, size=26, vals=rows, clab=["t", "被计的次数", "合计"])
    S.show(tb)
    S.say("由二项式定理，1 − C(t,1) + C(t,2) − … = (1 − 1)ᵗ = 0，所以 C(t,1) − C(t,2) + … = 1。每个元素恰好算一次，不属于任何集合的元素算 0 次。", extra=0.3)
    S.note("恰属于 t 个集合的元素被计 1 − (1 − 1)ᵗ = 1 次", color=G)

    # ------------------------------------------------------------ 错排
    S.section("错排：没有人拿到自己的帽子")
    n = 4
    D = derange(n)
    S.say(f"{n} 个人各有一顶帽子，打乱后重新分，没有人拿到自己的帽子，有几种分法？")
    S.say(f"设 Aᵢ 为“第 i 个人拿到自己的帽子”的排列。至少固定某 k 个人：剩下的随便排，(n − k)! 种；选哪 k 个人：C(n, k) 种。")
    S.note("|Aᵢ₁ ∩ … ∩ Aᵢₖ| = (n − k)!", color=Y)
    terms = [(k, comb(n, k) * factorial(n - k)) for k in range(n + 1)]
    expr = " ".join((("+ " if k % 2 == 0 else "− ") if k else "") + f"C({n},{k})·{n - k}!" for k, _ in terms)
    vals = " ".join((("+ " if k % 2 == 0 else "− ") if k else "") + str(v) for k, v in terms)
    S.show(label(640, 330, f"D{n} = " + expr, 30, FG), label(640, 410, f"= {vals} = {D}", 32, Y))
    assert D == sum((-1) ** k * v for k, v in terms)
    S.say(f"一个都不固定 = 全部 − 至少一个被固定：D{n} = Σ (−1)ᵏ C(n, k)(n − k)! = {D}。")
    S.note("Dₙ = Σ (−1)ᵏ C(n, k)(n − k)! = n! Σ (−1)ᵏ/k!", color=G)
    S.say("n 很大时 Dₙ/n! → 1/e ≈ 0.368：随便打乱，大约三分之一的概率谁都没拿到自己的帽子。", extra=0.3)

    # ------------------------------------------------------------ 上界
    S.section("有上界的不定方程")
    tot, ub, k = 10, 4, 3
    ans = bounded(tot, k, ub)
    S.say(f"x₁ + x₂ + x₃ = {tot}，0 ≤ xᵢ ≤ {ub}。插板法只能处理下界；上界用容斥：Aᵢ = “xᵢ ≥ {ub + 1}”（违反上界）。")
    S.note("上界：Aᵢ = “xᵢ 超过上界”，容斥后每个都用插板", color=Y)
    parts = []
    for j in range(k + 1):
        rest = tot - j * (ub + 1)
        c = comb(rest + k - 1, k - 1) if rest >= 0 else 0
        parts.append((j, comb(k, j), rest, c))
    lines = []
    for j, ck, rest, c in parts:
        if rest < 0:
            lines.append(f"违反 {j} 个：剩下的和是负数，0 种")
        else:
            lines.append(f"违反 {j} 个：C({k},{j}) 种选法 × 剩 {rest} 插板 C({rest + k - 1},{k - 1}) = {ck} × {c}")
    labs = [label(200, 260 + 64 * t, s_, 28, FG, anchor="lm") for t, s_ in enumerate(lines)]
    S.show(*labs, dur=0.6, lag=0.2)
    S.say(f"选定 j 个变量先各发 {ub + 1}，剩下的和插板。注意符号交替。")
    calc = sum((-1) ** j * ck * c for j, ck, rest, c in parts)
    assert calc == ans
    expr2 = " ".join((("+ " if j % 2 == 0 else "− ") if j else "") + f"{ck * c}" for j, ck, rest, c in parts if rest >= 0)
    S.show(label(640, 560, f"答案 = {expr2} = {ans}", 32, Y))
    S.say(f"答案 {ans}：(2, 4, 4)、(3, 3, 4) 各有 3 种排列，正好 6 组。")
    S.note(f"例：x₁ + x₂ + x₃ = {tot}，xᵢ ≤ {ub}：{ans} 组", color=G)

    # ------------------------------------------------------------ 至少与恰好
    S.section("“至少”与“恰好”")
    S.say("容斥里算的 |∩T| 是“至少满足 T 里这些条件”。设 f(k) = 所有大小为 k 的 T 的 |∩T| 之和，g(k) = 恰好满足 k 个条件的元素个数。")
    S.note("f(k) = Σ_{|T| = k} |∩ T|（至少）；g(k) = 恰好 k 个", color=Y)
    S.say("恰好满足 j 个条件的元素，在 f(k) 里被数了 C(j, k) 次（从它满足的 j 个里选 k 个）。所以 f(k) = Σⱼ C(j, k) g(j)。")
    S.note("f(k) = Σ_{j ≥ k} C(j, k) g(j)  ⇔  g(k) = Σ_{j ≥ k} (−1)^{j−k} C(j, k) f(j)", color=G)
    fk = [comb(n, k) * factorial(n - k) for k in range(n + 1)]
    gk = [sum(1 for p in permutations(range(n)) if sum(p[i] == i for i in range(n)) == k) for k in range(n + 1)]
    tb2 = Grid(2, n + 2, x=640, y=520, cw=110, ch=56, gap=4, size=26,
               vals=[["f(k)"] + [str(v) for v in fk], ["g(k)"] + [str(v) for v in gk]],
               clab=["", *[f"k = {k}" for k in range(n + 1)]])
    S.show(tb2)
    S.say(f"以 {n} 个人的帽子为例：f(k) = C({n}, k)(n − k)!，g(k) 是恰好 k 人拿到自己帽子的排列数。反过来用二项式反演，就能从 f 求出 g；g(0) 就是错排数 {gk[0]}。", extra=0.5)
    for kk in range(n + 1):
        assert gk[kk] == sum((-1) ** (j - kk) * comb(j, kk) * fk[j] for j in range(kk, n + 1))

    # ------------------------------------------------------------ 手推题
    q1 = sum(1 for x in range(1, 101) if all(x % d for d in DIV))
    q2 = bounded(12, 4, 5)
    S.quiz("(1) 1～100 中，不能被 2、3、5 中任何一个整除的数有几个？\n"
           "(2) x₁ + x₂ + x₃ + x₄ = 12，0 ≤ xᵢ ≤ 5，有几组整数解？", think=20)
    S.say(f"(1) 能被至少一个整除的：(50 + 33 + 20) − (16 + 10 + 6) + 3 = {103 - 32 + 3}，所以不能被整除的有 100 − {103 - 32 + 3} = {q1} 个。")
    assert q1 == 100 - (103 - 32 + 3)
    S.note(f"(1) {q1} 个", color=Y)
    a0, a1, a2 = comb(15, 3), 4 * comb(9, 3), comb(4, 2) * comb(3, 3)
    S.say(f"(2) 不管上界：C(15, 3) = {a0}；某个 ≥ 6：4 × C(9, 3) = {a1}；某两个 ≥ 6：C(4, 2) × C(3, 3) = {a2}；三个 ≥ 6 不可能。")
    assert a0 - a1 + a2 == q2
    S.say(f"答案 {a0} − {a1} + {a2} = {q2}。", extra=0.5)
    S.note(f"(2) {a0} − {a1} + {a2} = {q2}", color=G)

    S.recap([
        "容斥：Σ (−1)^{|T|+1}|∩T|；恰属于 t 个集合的元素被计 1 − (1 − 1)ᵗ = 1 次。",
        "错排 Dₙ = Σ(−1)ᵏ C(n, k)(n − k)!：“一个都不满足” = 全部 − 至少一个。",
        "有上界的方程：把“超过上界”当作坏条件，每一项先发掉再插板。",
        "“至少” f 与“恰好” g 满足 f(k) = ΣC(j, k)g(j)，用二项式反演互相转换。",
    ], next_title="矩阵递推")
