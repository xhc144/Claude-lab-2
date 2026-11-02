"""第 54 集 斜率优化 DP：把转移看成直线与点"""

from episodes.common import *

A = [1, 1, 1, 1, 3, 4]
M = 10


def prefix():
    s = [0]
    for x in A:
        s.append(s[-1] + x)
    return s


def solve():
    s = prefix()
    n = len(A)
    f = [0] * (n + 1)
    X = lambda j: s[j]                    # noqa: E731
    Y = lambda j: f[j] + s[j] ** 2        # noqa: E731
    q = [0]
    log = []
    for i in range(1, n + 1):
        k = 2 * s[i]
        popped_front = []
        while len(q) >= 2 and Y(q[1]) - Y(q[0]) <= k * (X(q[1]) - X(q[0])):
            popped_front.append(q.pop(0))
        j = q[0]
        f[i] = f[j] + (s[i] - s[j]) ** 2 + M
        assert f[i] == min(f[t] + (s[i] - s[t]) ** 2 + M for t in range(i))
        popped_back = []
        while len(q) >= 2 and (Y(q[-1]) - Y(q[-2])) * (X(i) - X(q[-1])) >= (Y(i) - Y(q[-1])) * (X(q[-1]) - X(q[-2])):
            popped_back.append(q.pop())
        q.append(i)
        log.append((i, k, j, popped_front, popped_back, q[:]))
    return s, f, log


def build(S):
    S.cover("一类 DP 的转移形如 f[i] = min f[j] + (sᵢ − sⱼ)² + M，直接枚举 j 是 O(n²)。把每个 j 看成平面上的一个点，最优的 j 就是“一条直线最先碰到的点”。",
            ["单调队列优化 DP（第 12 集）", "前缀和", "凸包的直观认识"])

    s, f, log = solve()
    n = len(A)

    # ------------------------------------------------------------ 问题
    S.section("问题与朴素 DP")
    arr = Array(A, x=520, y=240, cw=80, ch=60, gap=8, size=28)
    sa = Array(s, x=520 - 44, y=400, cw=80, ch=56, gap=8, size=26, base=0, fill=tint(B, 0.15))
    S.show(arr, label(130, 240, "a", 30, DIM, anchor="lm"), sa, label(130, 400, "s", 30, B, anchor="lm"))
    S.say(f"把序列 {', '.join(map(str, A))} 切成若干段，每段的代价是（段内和）² + {M}，求最小总代价。s 是前缀和。")
    S.note(f"f[i] = min_j f[j] + (sᵢ − sⱼ)² + M（M = {M}）", color=Y)
    S.say("f[i] = 前 i 个数的最小代价，枚举最后一段从 j + 1 到 i。每个 i 都要枚举所有 j：O(n²)。")
    S.say("平方项把 i 和 j 搅在一起，没法直接用单调队列。先把它展开看看。", extra=0.3)

    # ------------------------------------------------------------ 点与直线
    S.section("把 j 看成点，把 i 看成斜率")
    S.say("展开：f[j] + sᵢ² − 2sᵢsⱼ + sⱼ² + M。和 j 无关的 sᵢ² + M 提出去，要最小化的是 (f[j] + sⱼ²) − 2sᵢ · sⱼ。")
    S.note("令 xⱼ = sⱼ，yⱼ = f[j] + sⱼ²，k = 2sᵢ", color=Y)
    S.note("f[i] = min (yⱼ − k·xⱼ) + sᵢ² + M", color=Y)
    i0 = n
    k0 = 2 * s[i0]
    pts = [(s[j], f[j] + s[j] ** 2) for j in range(i0)]
    ax = Axes(x=560, y=500, w=900, h=560, xr=(0, 8), yr=(-60, 110), xstep=1, ystep=20, xlabel="x = sⱼ",
              ylabel="y = f[j] + sⱼ²", grid=True)
    S.show(ax)
    dots = [ax.dot(x, y, CY, 9, label=f"j={j}", side="ul", size=20) for j, (x, y) in enumerate(pts)]
    S.play(*[FadeIn(d) for d in dots], dur=0.6, lag=0.08)
    S.say(f"算 f[{i0}] 时，每个 j 是平面上一个点 (xⱼ, yⱼ)，sᵢ = {s[i0]}，斜率 k = 2sᵢ = {k0}。")
    S.say(f"yⱼ − k·xⱼ 就是“过点 j、斜率为 k 的直线”的纵截距。要它最小：拿一条斜率 {k0} 的直线从下往上平移，最先碰到的点就是最优的 j。")
    S.note("最优 j = 斜率 k 的直线从下往上平移时最先碰到的点", color=G)
    inter = [y - k0 * x for x, y in pts]
    best = min(range(i0), key=lambda j: (inter[j], -j))
    def clip(b):
        """斜率 k0、截距 b 的直线在绘图区里的那一段。"""
        xa = max(0.0, (-60 - b) / k0)
        xb = min(8.0, (110 - b) / k0)
        return (xa, b + k0 * xa), (xb, b + k0 * xb)

    b0 = min(inter) - 40
    ln = ax.seg(*clip(b0), color=O, w=3)
    S.play(FadeIn(ln), dur=0.4)
    S.play(ax.moveseg(ln, *clip(inter[best])), dur=1.2)
    S.play(dots[best].to(fill=Y, r=13), dur=0.4)
    S.say(f"最先碰到的是 j = {best}，截距 {inter[best]}，所以 f[{i0}] = {inter[best]} + {s[i0]}² + {M} = {f[i0]}。")
    assert inter[best] + s[i0] ** 2 + M == f[i0]

    # ------------------------------------------------------------ 下凸壳
    S.section("只有下凸壳上的点可能最优", keep=[ax, ln] + dots)
    hull = []                      # 点 0～i0−1 的下凸壳（x 已经递增）
    for j in range(i0):
        while len(hull) >= 2:
            (x1, y1), (x2, y2), (x3, y3) = pts[hull[-2]], pts[hull[-1]], pts[j]
            if (y2 - y1) * (x3 - x2) >= (y3 - y2) * (x2 - x1):
                hull.pop()
            else:
                break
        hull.append(j)
    hp = [ax.p(*pts[j]) for j in hull]
    poly = Poly([(x + ax.g("x", 0), y + ax.g("y", 0)) for x, y in hp], stroke=G, sw=3, closed=False)
    poly.tr["op"].base = 0
    S.add(poly)
    S.play(FadeIn(poly), dur=0.6)
    gone = [j for j in range(i0) if j not in hull]
    S.say("不管斜率是多少，从下往上平移的直线最先碰到的，一定是这些点的“下凸壳”（绿色折线）上的点。凸壳上方的点永远不会被先碰到。")
    S.play(*[dots[j].to(fill=FAINT) for j in gone], dur=0.4)
    S.say(f"比如点 j = {gone[0]} 在 j = {gone[0] - 1} 和 j = {gone[0] + 1} 连线的上方：任何斜率下，两边至少有一个点比它先被碰到。可以直接删掉。")
    S.note("只保留下凸壳：相邻点连线的斜率递增", color=Y)
    S.say("下凸壳上相邻两点连线的斜率递增。斜率为 k 的直线最先碰到的点 j，满足：左边那段的斜率 ≤ k ≤ 右边那段的斜率。", extra=0.3)
    S.note("最优点：左边线段斜率 ≤ k ≤ 右边线段斜率", color=G)

    # ------------------------------------------------------------ 单调队列
    S.section("斜率单调：单调队列维护凸壳")
    S.say("这里 a 都是正数，所以新加入的点 x 坐标递增；查询的斜率 k = 2sᵢ 也递增。两个单调性让我们可以用一个双端队列。")
    S.note("x 递增：新点从队尾加入；k 递增：最优点只会往右移", color=Y)
    S.say("队首：若队首两点连线的斜率 ≤ k，队首以后都不会再是最优（k 只会更大），弹掉。队尾：加入新点前，若队尾那个点在“倒数第二个点与新点”连线的上方，弹掉。")
    S.note("队首：斜率(q₁, q₂) ≤ k 则弹出；队尾：不凸则弹出", color=G)
    qa = Array([""] * (n + 1), x=640, y=330, cw=74, ch=56, gap=8, size=26, index=False, fill=tint(B, 0.12))
    st_t = label(640, 430, "", 26, FG)
    S.show(qa, label(640, 260, "队列（存的是 j）", 24, DIM), st_t)
    S.play(qa.cells[0].to(text="0", fill=tint(B, 0.35)), dur=0.3)
    for (i, k, j, pf, pb, q) in log:
        parts = [f"i = {i}，k = {k}"]
        if pf:
            parts.append("队首弹出 " + "、".join(map(str, pf)))
        parts.append(f"最优 j = {j}，f[{i}] = {f[i]}")
        if pb:
            parts.append("队尾弹出 " + "、".join(map(str, pb)))
        S.play(st_t.to(text="；".join(parts)),
               *[qa.cells[t].to(text=str(q[t]) if t < len(q) else "", fill=tint(B, 0.35) if t < len(q) else tint(B, 0.12))
                 for t in range(n + 1)], dur=0.6)
        S.wait(0.8)
        if i == 2:
            S.say(f"i = 2：新点 2 加入时，点 1 在点 0 和点 2 连线的上方（不凸），从队尾弹掉。")
    S.say(f"每个点进队一次、出队至多一次，均摊 O(n)。最终答案 f[{n}] = {f[n]}。", extra=0.3)
    S.note(f"总 O(n)；答案 f[{n}] = {f[n]}", color=G)

    # ------------------------------------------------------------ 手推题
    S.quiz("f[i] = min_j f[j] + (sᵢ − sⱼ)² + M。\n\n"
           "(1) 写出点的坐标 (xⱼ, yⱼ) 和直线的斜率 k。为什么要求的是下凸壳，而不是上凸壳？\n"
           "(2) 如果 a 里有负数，前缀和 s 不再单调，单调队列的哪一步会出问题？该怎么办？", think=20)
    S.say("(1) xⱼ = sⱼ，yⱼ = f[j] + sⱼ²，k = 2sᵢ。求的是截距的最小值，直线从下往上碰，所以是下凸壳；求最大值时就换成上凸壳。")
    S.note("(1) x = sⱼ，y = f[j] + sⱼ²，k = 2sᵢ；求最小 → 下凸壳", color=Y)
    S.say("(2) k 不再递增：最优点不一定往右走，不能弹队首，改成在凸壳上二分斜率。x 不再递增：新点可能插在中间，单调队列维护不了，要用平衡树、CDQ 分治或李超线段树。", extra=0.5)
    S.note("(2) k 无序：凸壳上二分；x 无序：平衡树 / CDQ / 李超树", color=G)

    S.recap([
        "展开平方：yⱼ − k·xⱼ 是过点 j、斜率 k 的直线的截距，最优 j 是直线从下往上最先碰到的点。",
        "只有下凸壳上的点可能最优；凸壳相邻斜率递增。",
        "x 递增、k 递增时用单调队列：队首斜率 ≤ k 就弹，队尾不凸就弹，均摊 O(n)。",
        "k 不单调就在凸壳上二分；x 不单调需要更强的数据结构。",
    ], next_title="线性基")
