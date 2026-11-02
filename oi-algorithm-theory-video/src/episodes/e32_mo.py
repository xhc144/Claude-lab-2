"""第 32 集 莫队：给询问排个序"""

import math

from episodes.common import *

A = [1, 3, 2, 1, 4, 3, 3, 2, 5, 1, 4, 4, 2, 5, 3, 1]
QS = [(2, 14), (5, 7), (1, 9), (11, 16), (3, 5), (8, 15), (2, 3), (6, 12), (12, 13), (4, 10)]
N = len(A)
BLK = 4


def moves(order):
    l, r = 1, 0
    tot = 0
    path = [(l, r)]
    for (ql, qr) in order:
        tot += abs(ql - l) + abs(qr - r)
        l, r = ql, qr
        path.append((l, r))
    return tot, path


def mo_order(qs, oddeven=False):
    def key(q):
        b = (q[0] - 1) // BLK
        return (b, q[1] if not (oddeven and b % 2) else -q[1])
    return sorted(qs, key=key)


def distinct(l, r):
    return len(set(A[l - 1:r]))


def build(S):
    S.cover("很多个询问“区间 [l, r] 里有几种不同的数”，不需要在线回答。把询问换个顺序处理，能快多少？",
            ["分块（第 31 集）", "双指针"])

    # ------------------------------------------------------------ 双指针
    S.section("从一个区间挪到相邻区间")
    arr = Array(A, x=640, y=260, cw=66, ch=60, gap=6, size=26)
    S.show(arr)
    S.say("询问：[l, r] 里有多少种不同的数。不强制在线：可以先把所有询问读进来，按任意顺序回答。")
    S.note("询问 [l, r] 中不同数的个数；离线（可以重排询问）")
    S.say("关键观察：如果已经知道 [l, r] 的答案（并记着每个数出现了几次 cnt），那么扩展或收缩一格只要 O(1)。")
    S.note("[l, r] → [l, r±1] 或 [l±1, r]：O(1) 更新", color=Y)
    fr = arr.frame(3, 7, Y)
    S.play(FadeIn(fr), dur=0.4)
    ans = label(640, 400, f"[3, 7]：{distinct(3, 7)} 种", 30, Y)
    S.show(ans)
    S.say(f"加入一个数 x：cnt[x] 从 0 变成 1 时，种类数 +1。删掉一个数：cnt[x] 从 1 变成 0 时，种类数 −1。")
    S.play(arr.reframe(fr, 3, 8), ans.to(text=f"[3, 8]：{distinct(3, 8)} 种"), dur=0.5)
    S.play(arr.reframe(fr, 3, 9), ans.to(text=f"[3, 9]：{distinct(3, 9)} 种（新出现了 5）"), dur=0.5)
    S.play(arr.reframe(fr, 4, 9), ans.to(text=f"[4, 9]：{distinct(4, 9)} 种"), dur=0.5)
    S.say("于是回答一串询问，就是让两个指针 l、r 依次挪到每个询问的位置，代价 = 指针移动的总距离。")
    S.note("总代价 = 两个指针移动的总步数")
    S.say("按读入顺序处理，最坏每次都要从一头挪到另一头，O(n·q)。能不能排个序，让总移动量变小？")

    # ------------------------------------------------------------ 平面视角
    S.section("把询问画成平面上的点")
    ax = Axes(x=500, y=480, w=600, h=520, xr=(0, 17), yr=(0, 17), xstep=4, ystep=4, xlabel="l", ylabel="r", grid=False)
    S.show(ax)
    dots = {q: ax.dot(q[0], q[1], CY, 8) for q in QS}
    S.play(*[FadeIn(d) for d in dots.values()], dur=0.6, lag=0.05)
    S.say("把每个询问 (l, r) 看成平面上的一个点。从一个询问到下一个，指针移动的步数就是两点之间的“曼哈顿距离” |Δl| + |Δr|。")
    S.note_space()
    tot0, path0 = moves(QS)
    pts = [ax.p(max(l, 0.0), max(r, 0.0)) for l, r in path0]
    poly0 = Poly([(x + 500, y + 480) for x, y in pts], stroke=R, sw=3, closed=False)
    poly0.tr["op"].base = 0
    S.add(poly0)
    S.play(FadeIn(poly0), dur=0.8)
    t0 = label(870, 250, f"读入顺序：{tot0} 步", 30, R, anchor="lm")
    S.show(t0)
    S.say("问题变成：给这些点排一个访问顺序，让路径总长尽量短。最优顺序很难求，但莫队给了一个简单又够好的顺序。")

    # ------------------------------------------------------------ 莫队排序
    S.section("莫队的顺序：先按块，再按右端点", keep=[ax, poly0, t0] + list(dots.values()))
    S.say(f"把 l 按块分组（块长 B，这里 B = {BLK}）：先按 l 所在的块排序，同一块里按 r 从小到大排序。")
    S.note("排序：先按 l 所在的块，同块内按 r 递增", color=Y)
    bands = []
    for b in range(0, 4):
        x1, _ = ax.p(b * BLK + 0.5, 0)
        x2, _ = ax.p(b * BLK + BLK + 0.5, 0)
        _, y1 = ax.p(0, 0)
        _, y2 = ax.p(0, 17)
        rr = Rect(500 + (x1 + x2) / 2, 480 + (y1 + y2) / 2, x2 - x1, y1 - y2, fill=alpha([CY, O, G, P][b], 0.08),
                  stroke=alpha([CY, O, G, P][b], 0.4), sw=1.5, r=0)
        rr.tr["op"].base = 0
        bands.append(rr)
        S.objs.insert(0, rr)
    S.play(*[FadeIn(b) for b in bands], dur=0.5)
    mq = mo_order(QS)
    tot1, path1 = moves(mq)
    pts1 = [ax.p(max(l, 0.0), max(r, 0.0)) for l, r in path1]
    poly1 = Poly([(x + 500, y + 480) for x, y in pts1], stroke=G, sw=4, closed=False)
    poly1.tr["op"].base = 0
    S.add(poly1)
    S.play(poly0.to(op=0.25), FadeIn(poly1), dur=0.8)
    t1 = label(870, 310, f"莫队顺序：{tot1} 步", 30, G, anchor="lm")
    S.show(t1)
    S.say("在同一个竖条（同一块）里，r 只往上走；l 在块内来回晃，但每次最多晃 B 步。")
    S.say("为什么这样就快？分开数两个指针的移动：")
    S.note("r：每块内单调递增，每块 O(n)，共 n/B 块 → O(n²/B)", color=CY)
    S.note("l：每个询问在块内移动 ≤ B，跨块 O(n) 共 n/B 次 → O(qB + n)", color=O)
    S.say("r 在每一块里单调，最多走 n 步；一共 n/B 块，合计 O(n²/B)。l 每个询问最多在块内挪 B 步，合计 O(qB)。")
    S.say("取 B = n/√q（n、q 同阶时就是 √n），总移动量 O(n√q)。n = q = 10⁵ 时大约 3×10⁷ 次 O(1) 的更新。")
    S.note("B ≈ n/√q → 总 O(n√q)；n、q 同阶即 O(n√n)", color=G)
    S.say("小优化：奇数块里 r 从小到大，偶数块里从大到小（奇偶排序），r 不用每到新的一块都从头跑，常数能小不少。", extra=0.3)

    # ------------------------------------------------------------ 适用条件
    S.section("什么时候能用莫队")
    S.say("条件一：离线——必须能先读入所有询问再重排。题目强制在线（下一个询问依赖上一个答案）时不能用。")
    S.note("① 离线", color=Y)
    S.say("条件二：区间伸缩一格的更新要快。不同数的个数、出现次数的平方和（小 Z 的袜子）都是 O(1)。")
    S.note("② 伸缩一格的代价小（通常 O(1)）", color=Y)
    S.say("条件三：没有修改。带修改时可以给询问再加一维“时间”，变成三个指针（带修莫队），复杂度 O(n^(5/3))。")
    S.note("③ 无修改（有修改：带修莫队，加时间维）", color=DIM)
    S.say("莫队的本质：答案只依赖区间，而相邻区间转移便宜——于是把“很多次重新计算”变成“一条尽量短的路径”。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("(1) 为什么要按 l 所在的“块”排序，而不是直接按 l 排序（l 相同再按 r）？\n"
           "(2) 如果伸缩一格的代价是 O(log n)（比如要维护一棵平衡树），莫队的总复杂度是多少？块长要不要变？", think=20)
    S.say("(1) 直接按 l 排序：l 只往右走，但相邻两个询问的 r 可以忽大忽小，每次都可能跳 O(n)，总共 O(n·q)。")
    S.note("(1) 只按 l 排：r 来回跳，O(nq)", color=R)
    S.say("分块之后，同一块里的询问按 r 排好，r 在块内单调——用 l 的“粗略”顺序换来 r 的单调性。")
    S.note("分块：l 粗排、r 在块内单调 → 两个指针都受控", color=G)
    S.say("(2) 总移动量不变，仍是 O(n√q)，每步多一个 log：O(n√q · log n)。块长的平衡点不变，因为两边都乘上了同一个 log。")
    S.note("(2) O(n√q · log n)；块长不变（两边同乘 log）", color=Y)

    S.recap([
        "离线区间询问：已知 [l, r] 的答案，伸缩一格 O(1)，回答询问 = 移动两个指针。",
        "把询问看成平面上的点，总代价是访问路径的长度（曼哈顿距离）。",
        "莫队排序：先按 l 所在块，同块按 r；r 每块单调 O(n)，l 每次 ≤ B，总 O(n√q)。",
        "条件：离线、伸缩便宜、无修改（有修改加时间维）。",
    ], next_title="CDQ 分治：三维偏序")
