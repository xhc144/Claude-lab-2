"""第 55 集 线性基：异或空间的一组基"""

from itertools import combinations

from episodes.common import *

NUMS = [12, 9, 5, 3]
QNUMS = [6, 5, 3]
NB = 4


def bits(x, w=NB):
    return [(x >> k) & 1 for k in range(w - 1, -1, -1)]


def insert_log(nums, w=NB):
    base = [0] * w
    log = []
    for x in nums:
        steps = []
        cur = x
        placed = None
        for k in range(w - 1, -1, -1):
            if not (cur >> k) & 1:
                continue
            if base[k]:
                steps.append((k, base[k], cur ^ base[k]))
                cur ^= base[k]
            else:
                base[k] = cur
                placed = k
                break
        log.append((x, steps, placed, cur, base[:]))
    return base, log


def span(nums):
    out = {0}
    for r in range(1, len(nums) + 1):
        for c in combinations(nums, r):
            v = 0
            for t in c:
                v ^= t
            out.add(v)
    return out


def build(S):
    S.cover("从一堆数里选若干个异或起来，最大能得到多少？一共能得到多少种不同的结果？把每个数看成一个 0/1 向量，异或就是向量加法——这就是线性代数里的“基”。",
            ["二进制与异或", "（可选）线性代数里“基”的概念"])

    base, log = insert_log(NUMS)
    sp = span(NUMS)
    basis = [b for b in base if b]
    assert span(basis) == sp

    # ------------------------------------------------------------ 异或是向量加法
    S.section("异或就是二进制向量的加法")
    rows = [[str(x)] + [str(b) for b in bits(x)] for x in NUMS]
    tb = Grid(len(NUMS), NB + 1, x=420, y=380, cw=78, ch=58, gap=4, size=28, vals=rows,
              clab=["数"] + [f"2^{k}" for k in range(NB - 1, -1, -1)])
    S.show(tb)
    S.say(f"四个数 {', '.join(map(str, NUMS))} 写成二进制。异或是逐位相加再模 2：每个数就是一个长度为 {NB} 的 0/1 向量，异或就是向量相加。")
    S.note("x ⊕ y = 逐位相加模 2：数 = GF(2) 上的向量", color=Y)
    S.say(f"选一些数异或起来，就是这些向量的“线性组合”。所有能得到的结果构成一个集合（张成的空间），这里一共 {len(sp)} 种。")
    S.note("所有子集的异或结果 = 这些向量张成的空间")
    S.say("找一组“基”：个数尽量少，张成的空间不变，而且每个基向量的最高位互不相同——后面的问题就都好回答了。", extra=0.3)

    # ------------------------------------------------------------ 插入
    S.section("按最高位插入", keep=[tb])
    bt = Grid(NB, NB + 2, x=980, y=420, cw=62, ch=56, gap=4, size=26,
              vals=[[f"b[{k}]", ""] + [""] * NB for k in range(NB - 1, -1, -1)],
              clab=["", "值"] + [f"2^{k}" for k in range(NB - 1, -1, -1)])
    S.show(bt, label(980, 230, "线性基：b[k] 的最高位是第 k 位", 24, DIM))
    S.say("维护 b[3..0]：b[k] 要么为空，要么是一个最高位恰好是 k 的数。插入 x：从高位往低位看，遇到 x 的某一位 k 是 1——")
    S.note("插入 x：从高到低，第 k 位为 1 时：b[k] 空 → 放进去；否则 x ← x ⊕ b[k]", color=Y)
    S.say("如果 b[k] 是空的，就把 x 放进去，结束；否则 x ← x ⊕ b[k]，把第 k 位消掉，继续往低位看。")
    cur_t = label(420, 640, "", 30, FG)
    S.add(cur_t)
    for t, (x, steps, placed, cur, snap) in enumerate(log):
        S.play(tb[t, 0].to(fill=tint(O, 0.4)), cur_t.to(text=f"插入 {x} = {''.join(map(str, bits(x)))}₂"), dur=0.4)
        for (k, bk, nx) in steps:
            S.play(bt[NB - 1 - k, 1].to(stroke=O, sw=3), cur_t.to(text=f"第 {k} 位是 1：⊕ b[{k}] = {bk}，得到 {nx} = {''.join(map(str, bits(nx)))}₂"), dur=0.5)
            S.play(bt[NB - 1 - k, 1].to(stroke=LINE, sw=2), dur=0.2)
        if placed is not None:
            r_ = NB - 1 - placed
            S.play(bt[r_, 1].to(text=str(snap[placed]), fill=tint(G, 0.4)),
                   *[bt[r_, 2 + c].to(text=str(b_)) for c, b_ in enumerate(bits(snap[placed]))], dur=0.5)
        else:
            S.play(cur_t.to(text=f"{x} 被消成 0：它能由前面的数异或出来，不加入"), tb[t, 0].to(fill=tint(R, 0.3)), dur=0.5)
        if t == 1:
            S.say(f"插入 {x}：第 3 位是 1，b[3] = {snap[3]} 已存在，异或后变成 {steps[0][2]}；第 2 位是 1、b[2] 空，放进 b[2]。")
        if placed is None:
            S.say(f"插入 {x}：被消成 0。说明 {x} 已经能用基里的数异或出来，它不带来新东西，不用存。")
        S.play(tb[t, 0].to(fill=BG3), dur=0.2)
    S.note("x 被消成 0 ⇔ x 能由已有的数异或得到", color=R)
    S.say("为什么张成的空间不变？x 换成 x ⊕ b[k]，只是加上一个空间里已有的向量，能异或出的集合一点没变。", extra=0.3)
    S.note("x → x ⊕ b[k] 不改变张成的空间", color=G)

    # ------------------------------------------------------------ 最大异或
    S.section("最大异或和：从高位贪心", keep=[bt])
    S.say("选一些基向量异或，让结果最大。从高位往低位：ans ⊕ b[k] 比 ans 大就异或上。")
    S.note("ans = 0；k 从高到低：若 ans ⊕ b[k] > ans 则 ans ← ans ⊕ b[k]", color=Y)
    ans = 0
    ans_t = label(980, 690, "ans = 0", 32, Y)
    S.show(ans_t)
    for k in range(NB - 1, -1, -1):
        if not base[k]:
            continue
        r_ = NB - 1 - k
        take = (ans ^ base[k]) > ans
        S.play(bt[r_, 1].to(stroke=G if take else R, sw=3.5), dur=0.3)
        if take:
            ans ^= base[k]
        S.play(ans_t.to(text=f"ans = {ans} = {''.join(map(str, bits(ans)))}₂"), dur=0.4)
        S.say(f"b[{k}] = {base[k]}：ans ⊕ b[{k}] = {ans if take else ans ^ base[k]}，" + ("更大，取。" if take else f"不比 {ans} 大，不取。"))
    assert ans == max(sp)
    S.say(f"答案 {ans}。为什么贪心对？第 k 位只有 b[k] 能改变（更低的基向量最高位都低于 k），高位的 1 比所有低位加起来都重要，所以从高到低逐位决定。", extra=0.3)
    S.note(f"高位优先：第 k 位只能由 b[k] 决定；答案 {ans}", color=G)

    # ------------------------------------------------------------ 计数
    S.section("能表示多少个不同的数")
    r = len(basis)
    S.say(f"基里有 r = {r} 个数。它们的每个子集异或出来都不同（最高位互不相同，所以不会抵消成同一个数），而且恰好覆盖整个空间。")
    S.note("r 个基向量 ⇒ 恰好 2ʳ 个不同的异或值（含 0）", color=Y)
    vals = sorted(sp)
    arr = Array(vals, x=640, y=420, cw=84, ch=60, gap=10, size=28, index=False, fill=tint(P, 0.25))
    S.show(arr, label(640, 340, f"所有能得到的值：2^{r} = {len(vals)} 个", 26, P))
    S.say(f"所以一共 2^{r} = {2 ** r} 种结果（包括什么都不选的 0）。原来的 {len(NUMS)} 个数里有 {len(NUMS) - r} 个是多余的。", extra=0.5)
    assert len(vals) == 2 ** r

    # ------------------------------------------------------------ 手推题
    qbase, qlog = insert_log(QNUMS, 3)
    qb = [b for b in qbase if b]
    qmax = 0
    for k in range(2, -1, -1):
        if qbase[k] and (qmax ^ qbase[k]) > qmax:
            qmax ^= qbase[k]
    qs = span(QNUMS)
    assert qmax == max(qs) and len(qs) == 2 ** len(qb)
    S.quiz(f"数：{', '.join(map(str, QNUMS))}。\n\n"
           "(1) 依次插入线性基，写出每一步。哪个数被消成了 0？\n"
           "(2) 最大异或和是多少？一共能异或出多少种不同的值？", think=20)
    S.say(f"(1) 6 = 110₂ 放进 b[2]；5 = 101₂：第 2 位 ⊕ 6 得 011₂ = 3，放进 b[1]；3 = 011₂：第 1 位 ⊕ 3 得 0，被消掉——因为 3 = 6 ⊕ 5。")
    S.note("(1) 基 {6, 3}；3 被消成 0（3 = 6 ⊕ 5）", color=Y)
    S.say(f"(2) 贪心：ans = 6，6 ⊕ 3 = 5 更小，不取，最大是 {qmax}。基有 2 个数，共 2² = {len(qs)} 种：{', '.join(map(str, sorted(qs)))}。", extra=0.5)
    S.note(f"(2) 最大 {qmax}；{len(qs)} 种", color=G)

    S.recap([
        "数看成 GF(2) 上的向量，异或就是加法；所有子集异或值构成张成的空间。",
        "插入：从高位到低位，第 k 位为 1 时，b[k] 空就放入，否则异或 b[k]；变成 0 说明可以被表示。",
        "最大异或和：从高位到低位，能变大就异或上 b[k]。",
        "基里有 r 个数，就恰好能表示 2ʳ 个不同的值。",
    ], next_title="FFT（上）")
