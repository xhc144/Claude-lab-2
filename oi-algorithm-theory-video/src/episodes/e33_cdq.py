"""第 33 集 CDQ 分治：三维偏序"""

from episodes.common import *

PTS = [(1, 4, 2), (2, 2, 5), (3, 6, 3), (4, 1, 1), (5, 5, 4), (6, 3, 6), (7, 7, 2), (8, 2, 3)]   # (a, b, c)，a 已排好


def brute():
    return [sum(1 for j, q in enumerate(PTS) if j != i and q[0] <= p[0] and q[1] <= p[1] and q[2] <= p[2])
            for i, p in enumerate(PTS)]


def cdq():
    n = len(PTS)
    ans = [0] * n
    log = []

    def solve(lo, hi, depth):
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        solve(lo, mid, depth + 1)
        solve(mid, hi, depth + 1)
        left = sorted(range(lo, mid), key=lambda i: PTS[i][1])
        right = sorted(range(mid, hi), key=lambda i: PTS[i][1])
        bit = {}
        k = 0
        steps = []
        for i in right:
            added = []
            while k < len(left) and PTS[left[k]][1] <= PTS[i][1]:
                c = PTS[left[k]][2]
                bit[c] = bit.get(c, 0) + 1
                added.append(left[k])
                k += 1
            got = sum(v for cc, v in bit.items() if cc <= PTS[i][2])
            ans[i] += got
            steps.append((i, added, got))
        log.append((lo, mid, hi, depth, left, right, steps))

    solve(0, n, 0)
    return ans, log


def build(S):
    S.cover("每个元素有三个属性 (a, b, c)，对每个元素数一数：有多少个别的元素三个属性都不比它大？",
            ["树状数组（第 13 集）", "归并排序与分治"])

    ans, log = cdq()
    assert ans == brute()
    n = len(PTS)

    # ------------------------------------------------------------ 问题
    S.section("问题：三维偏序")
    tb = Grid(n, 4, x=420, y=480, cw=110, ch=56, gap=4, size=26, clab=["元素", "a", "b", "c"],
              vals=[[f"#{i + 1}", *p] for i, p in enumerate(PTS)], lab_color=FG)
    S.show(tb)
    S.say("8 个元素，每个有 (a, b, c)。对每个元素 i，求有多少个 j ≠ i 满足 aⱼ ≤ aᵢ、bⱼ ≤ bᵢ、cⱼ ≤ cᵢ。")
    S.note("求：aⱼ ≤ aᵢ, bⱼ ≤ bᵢ, cⱼ ≤ cᵢ 的 j 有几个")
    S.say("两两比较是 O(n²)。先回忆少一维的情形：只有 (a, b) 时，按 a 排序后从前往后扫，用树状数组维护已经扫过的 b，每个元素查一次前缀和。")
    S.note("二维：按 a 排序 + 树状数组维护 b → O(n log n)", color=Y)
    S.say("三维多了一个条件。排序能消掉一维，树状数组能处理一维，还差一维——这一维交给分治。")
    S.note("三维：排序消一维 + 分治消一维 + 树状数组处理一维", color=G)

    # ------------------------------------------------------------ 分治
    S.section("按 a 排好，再对下标分治")
    S.say("元素已经按 a 从小到大排好（这里 a 就是 1~8）。把序列从中间分成左右两半，分别递归处理，各自算好“半边内部”的贡献。")
    arr = Array([f"{p[1]},{p[2]}" for p in PTS], x=640, y=260, cw=118, ch=64, gap=8, size=24,
                idx_labels=[f"a={p[0]}" for p in PTS])
    S.show(arr, label(640, 180, "每格写的是 (b, c)，按 a 排序", 22, DIM))
    fl = arr.frame(1, 4, CY)
    fr = arr.frame(5, 8, O)
    S.play(FadeIn(fl), FadeIn(fr), dur=0.5)
    S.say("剩下的只有“左半的 j 对右半的 i”的贡献。左半的 a 都 ≤ 右半的 a，所以 a 的条件{y|自动满足}！只需要数 bⱼ ≤ bᵢ 且 cⱼ ≤ cᵢ 的对数。")
    S.note("左半 → 右半：a 自动满足，只剩 (b, c) 二维问题", color=Y)
    S.say("这又是一个二维问题：把左右两半各自按 b 排序，像二维的做法一样扫描 b，树状数组维护 c。")
    S.note("左右各按 b 排序，扫描 b，树状数组按 c 计数")

    # ------------------------------------------------------------ 合并一步
    S.section("最顶层的那一次合并")
    top = log[-1]
    lo, mid, hi, depth, left, right, steps = top
    lt = Array([f"{PTS[i][1]},{PTS[i][2]}" for i in left], x=360, y=330, cw=110, ch=60, gap=8, size=24,
               idx_labels=[f"#{i + 1}" for i in left], fill=tint(CY, 0.2))
    rt = Array([f"{PTS[i][1]},{PTS[i][2]}" for i in right], x=920, y=330, cw=110, ch=60, gap=8, size=24,
               idx_labels=[f"#{i + 1}" for i in right], fill=tint(O, 0.2))
    S.show(lt, rt, label(360, 250, "左半（按 b 排序）", 24, CY), label(920, 250, "右半（按 b 排序）", 24, O))
    bitv = [0] * 7
    bit = Array(bitv, x=640, y=560, cw=80, ch=56, gap=6, size=24, idx_labels=[f"c={c}" for c in range(1, 8)])
    S.show(bit, label(640, 490, "树状数组：已加入的左半元素，按 c 计数", 22, DIM))
    S.say("右半从 b 小到大依次处理。处理某个 i 之前，先把左半里所有 b ≤ bᵢ 的元素按 c 加进树状数组；然后查询 c ≤ cᵢ 的个数。")
    res = label(640, 700, "", 28, Y)
    S.add(res)
    lpos = {i: k for k, i in enumerate(left)}
    rpos = {i: k for k, i in enumerate(right)}
    for (i, added, got) in steps:
        for j in added:
            c = PTS[j][2]
            bitv[c - 1] += 1
            S.play(lt.cells[lpos[j]].to(fill=tint(G, 0.45)), bit[c].to(text=str(bitv[c - 1]), fill=tint(G, 0.3)), dur=0.35)
        S.play(rt.cells[rpos[i]].to(stroke=Y, sw=4), *[bit[c].to(stroke=Y, sw=3) for c in range(1, PTS[i][2] + 1)], dur=0.35)
        S.play(res.to(text=f"#{i + 1}（b={PTS[i][1]}, c={PTS[i][2]}）：左半贡献 {got}"), dur=0.4)
        S.wait(0.5)
        S.play(rt.cells[rpos[i]].to(stroke=LINE, sw=2), *[bit[c].to(stroke=LINE, sw=2) for c in range(1, 8)], dur=0.2)
    S.say("扫描时 b 的指针只往右走，每个左半元素只加入一次，这一层的合并是 O(len · log n)。最后别忘了清空树状数组（只撤销加过的位置）。")
    S.note("一次合并 O(len log n)；树状数组用完要撤销", color=Y)

    # ------------------------------------------------------------ 为什么对
    S.section("为什么每一对恰好算一次")
    S.say("任取一对 j、i（按 a 排序后 j 在 i 前面）。递归的每一层，它们要么在同一半，要么被分到左右两半。")
    rec = Group(640, 470)
    levels = [(0, 8), (0, 4), (4, 8), (0, 2), (2, 4), (4, 6), (6, 8)]
    ycoord = {0: -150, 1: -30, 2: 90}
    boxes = {}
    for lo_, hi_ in levels:
        d = {8: 0, 4: 1, 2: 2}[hi_ - lo_]
        x0 = -480 + lo_ * 120
        w = (hi_ - lo_) * 120 - 12
        bx = Rect(x0 + w / 2, ycoord[d], w, 70, fill=BG3, stroke=LINE2, r=10)
        bx.add(Text(0, 0, f"[{lo_ + 1}, {hi_}]", size=24, color=FG))
        rec.add(bx)
        boxes[(lo_, hi_)] = bx
    S.show(rec)
    S.say("例：#2 和 #3 在 [1,8]、[1,4] 里都在同一半，直到 [1,4] 分成 [1,2] 和 [3,4] 时才第一次分开——它们只在这一次合并中被统计。")
    S.play(boxes[(0, 4)].to(stroke=Y, sw=4, fill=tint(Y, 0.2)), dur=0.5)
    S.note("每一对 (j, i) 恰在“第一次被分开”的那层合并中被统计一次", color=G)
    S.say("一对元素第一次被分到两边，只发生在唯一的一层；之后它们在不同的子问题里，再也不会相遇。所以不重不漏。")
    S.say("复杂度：每层合并总共 O(n log n)，一共 log n 层，O(n log² n)。")
    S.note("T(n) = 2T(n/2) + O(n log n) = O(n log² n)")
    S.say("一个细节：完全相同的元素互相都要算上，但分治只算“左对右”。所以先把相同的三元组合并成一个，带上个数，再分别补上。", extra=0.3)
    S.note("相同元素：先去重并记个数，最后补上彼此的贡献", color=R)

    # ------------------------------------------------------------ 手推题
    S.quiz("平面上依次发生两种操作：在 (x, y) 加一个点；询问“目前已有的点中，有多少个满足 x ≤ X 且 y ≤ Y”。\n\n"
           "(1) 这是几维偏序？三个维度分别是什么？\n"
           "(2) 用 CDQ 分治时，哪一维已经排好？合并时谁对谁有贡献？", think=20)
    S.say("(1) 一个点 j 对询问 i 有贡献，需要三个条件：j 发生在 i 之前（时间），xⱼ ≤ X，yⱼ ≤ Y。三维偏序：时间、x、y。")
    S.note("(1) 三维：时间、x、y", color=Y)
    S.say("(2) 操作本来就按时间顺序给出，时间这一维已经排好，直接对操作序列分治。合并时只看“左半的加点操作”对“右半的询问操作”的贡献。")
    S.note("(2) 按时间分治；左半的加点 → 右半的询问；按 x 扫描、树状数组维护 y", color=G)
    S.say("这就是 CDQ 最常见的用法：把“修改对后面询问的影响”离线成偏序问题，时间那一维由分治吃掉。", extra=0.5)

    S.recap([
        "三维偏序：排序消掉 a，分治处理“左半对右半”，树状数组处理 c。",
        "左半的 a 都不超过右半，合并时 a 自动满足，只剩 (b, c) 的二维计数：按 b 扫描、树状数组按 c 计数。",
        "每一对元素恰好在第一次被分到两边的那一层被统计一次，不重不漏；O(n log² n)。",
        "常见用法：把时间当作一维，离线处理“修改对之后询问的贡献”。",
    ], next_title="整体二分：所有询问一起二分")
