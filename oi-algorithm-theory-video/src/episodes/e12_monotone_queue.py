"""第 12 集 单调队列优化 DP：过时又更差的候选永远没用"""

from episodes.common import *

C_ = [3, 1, 5, 2, 4, 1, 6, 2]
M = 3


def run():
    """f[i]：点亮第 i 座（1 开始），且前 i 座都满足要求的最小代价。f[0] = 0 是虚拟起点。
    返回每一步的 (i, 弹出的过期, 用到的队首, f[i], 从队尾弹出的, 队列内容)。"""
    n = len(C_)
    f = [0] + [None] * n
    dq = [0]
    log = []
    for i in range(1, n + 1):
        expired = []
        while dq and dq[0] < i - M:
            expired.append(dq.pop(0))
        head = dq[0]
        f[i] = f[head] + C_[i - 1]
        popped = []
        while dq and f[dq[-1]] >= f[i]:
            popped.append(dq.pop())
        dq.append(i)
        log.append((i, expired, head, f[i], popped, list(dq)))
    # 暴力核对
    g = [0] + [None] * n
    for i in range(1, n + 1):
        g[i] = C_[i - 1] + min(g[j] for j in range(max(0, i - M), i))
    assert g == f
    ans = min(f[n - M + 1:])
    return f, log, ans


def build(S):
    S.cover("一排烽火台，任意连续 m 座里至少点亮一座，点亮第 i 座花 cᵢ。最小总花费是多少？转移能不能做到 O(1)？",
            ["DP 的状态与转移", "双端队列"])

    f, log, ans = run()
    n = len(C_)

    # ------------------------------------------------------------ 问题与朴素转移
    S.section("问题：烽火传递")
    arr = Array(C_, x=640, y=230, cw=96, ch=70, gap=10, size=32)
    lab = label(130, 230, "代价 c", 24, DIM, anchor="rm")
    S.show(arr, lab)
    S.say(f"一排 {n} 座烽火台，点亮第 i 座要花 cᵢ。要求任意连续 {M} 座里至少有一座被点亮。求最小总花费。")
    S.note(f"任意连续 m 座（m = {M}）中至少点亮一座；求最小花费")
    S.say("状态：f[i] = 第 i 座被点亮、并且前 i 座都满足要求时的最小花费。上一座被点亮的 j 必须离 i 不超过 m。")
    S.note("{y|f[i] = cᵢ + min( f[j] )，i − m ≤ j ≤ i − 1}", color=Y)
    S.note("f[0] = 0（虚拟起点）；答案 = min f[n−m+1 .. n]")
    fa = Array([0] + [""] * n, x=640 - 53, y=470, cw=96, ch=70, gap=10, size=32, base=0)
    flab = label(80, 470, "f", 28, Y, anchor="rm")
    S.show(fa, flab)
    S.say("直接算：每个 i 都要在长度为 m 的窗口里找最小值，O(nm)。n、m 都是 10⁵ 时就慢了。")
    S.note("朴素：每次扫窗口，O(nm)", color=R)
    S.say("观察窗口：算 f[i] 时看 [i−m, i−1]，算 f[i+1] 时看 [i−m+1, i]。窗口的左右端点都只往右走。")
    win = fa.frame(0, 2, CY)
    S.play(FadeIn(win), dur=0.4)
    for i in (4, 5):
        S.play(fa.reframe(win, i - M, i - 1), dur=0.6)
        S.wait(0.3)
    S.note("窗口 [i−m, i−1] 的两端都单调右移", color=G)

    # ------------------------------------------------------------ 谁没用
    S.section("哪些候选永远没用")
    S.say("设两个候选 j < j′ 都在窗口里，并且 f[j] ≥ f[j′]。")
    S.say("j 比 j′ 早离开窗口（更“老”），值又不比 j′ 小（不更好）。只要 j 还在窗口里，j′ 也一定在，而且至少一样好。")
    S.note("j < j′ 且 f[j] ≥ f[j′] → j 永远不会再是最优", color=Y)
    S.say("所以 j 可以直接扔掉，再也不会用到。这就是“过时又更差的候选永远没用”。")
    S.say("扔掉所有这样的候选后，剩下的候选按下标从小到大排，f 值也严格从小到大。这个序列叫单调队列。")
    S.note("剩下的候选：下标递增，f 递增 → 单调队列")
    S.note("队首 = 窗口内最小值")
    S.say("每来一个新的 i，做三件事：")
    S.note("① 队首过期（< i − m）就弹出", color=CY)
    S.note("② 用队首算 f[i]", color=CY)
    S.note("③ 从队尾弹出所有 f ≥ f[i] 的，再把 i 放进队尾", color=CY)

    # ------------------------------------------------------------ 推一遍
    S.section("推一遍")
    arr2 = Array(C_, x=640, y=180, cw=96, ch=64, gap=10, size=30)
    lab2 = label(130, 180, "代价 c", 24, DIM, anchor="rm")
    fa2 = Array([0] + [""] * n, x=640 - 53, y=360, cw=96, ch=64, gap=10, size=30, base=0)
    flab2 = label(80, 360, "f", 28, Y, anchor="rm")
    S.show(arr2, lab2, fa2, flab2)
    S.note("队列里画的是下标（上）和 f 值（下）", color=DIM)
    S.note("① 队首过期（< i − m）就弹出", color=CY)
    S.note("② 用队首算 f[i]", color=CY)
    S.note("③ 队尾所有 f ≥ f[i] 的弹出，i 进队尾", color=CY)
    qlab = label(100, 620, "队列", 28, P, anchor="lm")
    qbox = Rect(700, 620, 1060, 110, fill=alpha(P, 0.06), stroke=alpha(P, 0.5), sw=2, r=14)
    front = label(200, 700, "队首", 22, DIM)
    back = label(1200, 700, "队尾", 22, DIM)
    S.show(qbox, qlab, front, back)
    win2 = fa2.frame(0, 0, CY)
    S.play(FadeIn(win2), dur=0.3)
    qcells = {}

    def qpos(k):
        return 270 + k * 130

    def enqueue(j, k):
        c = Cell(qpos(k), 620, 110, 80, "", 26, fill=tint(P, 0.3), stroke=P)
        c.label.tr["text"].base = f"{j}"
        sub = Text(0, 22, f"f={f[j]}", size=20, color=DIM)
        c.label.tr["y"].base = -12
        c.add(sub)
        qcells[j] = c
        return c

    c0 = enqueue(0, 0)
    S.show(c0, dur=0.4)
    detail = {4, 6}
    for (i, expired, head, fi, popped, dq) in log:
        anims = [fa2.reframe(win2, max(0, i - M), i - 1), arr2[i].to(fill=tint(Y, 0.3))]
        if i in detail:
            S.say(f"i = {i}：窗口是 [{max(0, i - M)}, {i - 1}]。" + (f"队首 {expired[0]} 已过期，弹出。" if expired else "队首没有过期。")
                  + f"用队首 {head}：f[{i}] = f[{head}] + c{i} = {f[head]} + {C_[i - 1]} = {fi}。")
        S.play(*anims, dur=0.4)
        if expired:
            S.play(*[qcells[j].to(fill=tint(R, 0.4), stroke=R) for j in expired], dur=0.3)
            S.play(FadeOut(*[qcells[j] for j in expired]), dur=0.3)
        S.play(qcells[head].to(stroke=Y, sw=4), dur=0.25)
        S.play(fa2[i].to(text=str(fi), fill=tint(Y, 0.3)), dur=0.4)
        S.play(qcells[head].to(stroke=P, sw=2), dur=0.2)
        if popped:
            if i in detail:
                S.say(f"再看队尾：" + "、".join(f"f[{j}] = {f[j]}" for j in popped) + f" 都 ≥ f[{i}] = {fi}，它们比 {i} 老又不比它好，弹出。")
            S.play(*[qcells[j].to(fill=tint(R, 0.4), stroke=R) for j in popped], dur=0.3)
            S.play(FadeOut(*[qcells[j] for j in popped]), dur=0.3)
        c = enqueue(i, len(dq) - 1)
        rest = [j for j in dq if j != i]
        S.play(*[qcells[j].to(x=qpos(k)) for k, j in enumerate(rest)], dur=0.3)
        S.show(c, dur=0.3)
        S.play(arr2[i].to(fill=BG3), fa2[i].to(fill=tint(G, 0.22)), dur=0.2)
        S.wait(0.35)
    S.say(f"最后几座里至少有一座要亮：答案 = min(f[{n - M + 1}..{n}]) = {ans}。")
    S.play(*[fa2[j].to(stroke=G, sw=4) for j in range(n - M + 1, n + 1)], dur=0.5)
    S.say("每个下标恰好进队一次，至多出队一次，所以总共 O(n)。单次可能弹出很多个，但平摊下来每次 O(1)。")

    # ------------------------------------------------------------ 条件
    S.section("什么时候能用")
    S.say("单调队列成立依赖两个条件。第一：窗口的左右端点都单调不减。被扔掉的候选永远不会再回到窗口里。")
    S.note("条件一：窗口两端单调移动（扔掉的不会再需要）", color=Y)
    S.say("如果某一步窗口的左端点往回缩了，一个早就被扔掉的老候选可能重新变成最优——但它已经不在队列里了。")
    S.say("第二：要比较的量只和 j 有关。f[i] = (只和 i 有关的部分) + min (只和 j 有关的部分 h(j))，队列按 h(j) 维护。")
    S.note("条件二：f[i] = g(i) + min h(j)，h 只依赖 j", color=Y)
    S.say("例如 f[i] = min(f[j] + (i − j)·w)，展开是 i·w + min(f[j] − j·w)，h(j) = f[j] − j·w，可以用。")
    S.note("f[j] + (i − j)·w → i·w + (f[j] − j·w) ✓", color=G)
    S.say("但 f[i] = min(f[j] + (sᵢ − sⱼ)²) 展开后有 −2sᵢsⱼ 这一项，同时依赖 i 和 j：对不同的 i，候选的优劣顺序会变，单调队列不再成立。")
    S.note("(sᵢ − sⱼ)² 含 sᵢsⱼ 交叉项 ✗ → 斜率优化（第 54 集）", color=R)
    S.say("另外，多重背包按“体积除以 w 的余数”分组后，每组里的转移恰好是滑动窗口最值，也能用单调队列做到 O(nV)。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("判断下面的转移能否用单调队列优化（窗口都是 [i−k, i−1]），能的话队列按什么值维护？\n"
           "(a) f[i] = max f[j] + aᵢ\n"
           "(b) f[i] = max ( f[j] − 2j ) 中再加上 3i\n"
           "(c) f[i] = min ( f[j] + j × i )\n"
           "(d) f[i] = min ( f[j] + |aᵢ − aⱼ| )", think=20)
    S.say("(a) 能：h(j) = f[j]，求最大值，队列里 f 值单调递减。")
    S.note("(a) ✓ h(j) = f[j]（单调递减队列）", color=G)
    S.say("(b) 能：3i 只和 i 有关，h(j) = f[j] − 2j。")
    S.note("(b) ✓ h(j) = f[j] − 2j", color=G)
    S.say("(c) 不能：j × i 是交叉项。i 变大时，j 大的候选“涨得更快”，优劣顺序会随 i 改变。这是斜率优化的形式。")
    S.note("(c) ✗ 交叉项 j·i → 斜率优化", color=R)
    S.say("(d) 不能直接用：绝对值按 aⱼ ≤ aᵢ 和 aⱼ > aᵢ 分成两种情况，候选要按 aⱼ 的大小分开处理（要用数据结构），不再是单纯按下标的窗口最值。")
    S.note("(d) ✗ 不能直接用：要按 aⱼ 分类，需要数据结构", color=R)

    S.recap([
        "滑动窗口最值：j < j′ 且 f[j] 不比 f[j′] 好，j 就永远没用，直接扔掉。",
        "剩下的候选下标递增、值单调，构成单调队列；队首就是窗口最优值。",
        "每个下标进出队列各一次，均摊 O(1)，总 O(n)。",
        "条件：窗口两端单调移动；转移能拆成 g(i) + 最值 h(j)。有交叉项时改用斜率优化。",
    ], next_title="树状数组的区间变换：差分把区间变成单点")
