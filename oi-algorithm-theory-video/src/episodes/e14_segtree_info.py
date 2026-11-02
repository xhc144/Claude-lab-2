"""第 14 集 线段树的信息设计：结点里存什么才够合并"""

from episodes.common import *

A = [2, -3, 4, -1, 2, -5, 3, -2]
N = len(A)


def leaf(v):
    return (v, v, v, v)


def merge(L, R):
    s = L[0] + R[0]
    pre = max(L[1], L[0] + R[1])
    suf = max(R[2], R[0] + L[2])
    best = max(L[3], R[3], L[2] + R[1])
    return (s, pre, suf, best)


def brute_best(a):
    return max(sum(a[i:j + 1]) for i in range(len(a)) for j in range(i, len(a)))


def tup(t):
    return f"和{t[0]} 前{t[1]} 后{t[2]} 最{t[3]}"


def build(S):
    S.cover("单点修改、询问区间最大子段和。线段树的每个结点该存哪些量，才能由两个儿子算出父亲？",
            ["线段树的结构：结点管一段区间，查询拆成 O(log n) 个结点"])

    info = {}

    def calc(l, r):
        if l == r:
            info[(l, r)] = leaf(A[l - 1])
        else:
            m = (l + r) // 2
            calc(l, m)
            calc(m + 1, r)
            info[(l, r)] = merge(info[(l, m)], info[(m + 1, r)])
        return info[(l, r)]

    calc(1, N)
    assert info[(1, N)][3] == brute_best(A)

    # ------------------------------------------------------------ 问题
    S.section("问题：区间最大子段和")
    arr = Array(A, x=640, y=330, cw=110, ch=74, gap=10, size=32)
    S.show(arr)
    S.say("一个数组，支持两种操作：修改一个数；询问区间 [l, r] 里和最大的连续子段（最大子段和）。")
    S.note("操作：单点修改；询问 [l, r] 的最大子段和")
    S.say(f"例如整个数组的最大子段是 4、−1、2，和为 {info[(1, N)][3]}。每次询问都扫一遍是 O(n)，询问多了就慢。")
    S.play(*[arr[i].to(fill=tint(Y, 0.35)) for i in (3, 4, 5)], dur=0.6)
    S.say("线段树：每个结点管一段区间，存这段区间的“信息”。询问时把 [l, r] 拆成 O(log n) 个结点，把它们的信息依次合并。")
    S.note("线段树：询问 = 合并 O(log n) 个结点的信息")
    S.say("所以关键问题只有一个：结点里存什么，才能{y|只用两个儿子的信息}算出父亲的信息？")
    S.note("关键：信息必须“可合并”——父亲 = 合并(左儿子, 右儿子)", color=Y)

    # ------------------------------------------------------------ 只存最大值不够
    S.section("只存最大子段和，够吗")
    arr2 = Array(A, x=640, y=300, cw=110, ch=74, gap=10, size=32)
    S.show(arr2)
    left = arr2.frame(1, 4, CY)
    right = arr2.frame(5, 8, O)
    S.play(FadeIn(left), FadeIn(right), dur=0.5)
    L, R_ = info[(1, 4)], info[(5, 8)]
    S.say(f"假设每个结点只存“最大子段和”。左半 [1, 4] 的最大子段和是 {L[3]}，右半 [5, 8] 是 {R_[3]}。")
    lt = label(arr2.X(1) + 165, 430, f"左半最大：{L[3]}", 28, CY)
    rt = label(arr2.X(5) + 165, 430, f"右半最大：{R_[3]}", 28, O)
    S.show(lt, rt)
    S.say(f"可整体的答案是 {info[(1, N)][3]}：子段 4、−1、2 跨过了中点。只知道两边各自的最大值，算不出跨过中点的子段。")
    S.play(*[arr2[i].to(fill=tint(Y, 0.35)) for i in (3, 4, 5)], dur=0.5)
    S.note("只存“最大子段和”：跨中点的子段算不出 ✗", color=R)
    S.say(f"跨过中点的子段 = 左半的一个后缀 + 右半的一个前缀。要它最大，就取左半的最大后缀（{L[2]}）加右半的最大前缀（{R_[1]}）。")
    S.play(*[arr2[i].to(fill=tint(CY, 0.45)) for i in (3, 4)], arr2[5].to(fill=tint(O, 0.45)), dur=0.5)
    S.note("跨中点的最大值 = 左.最大后缀 + 右.最大前缀", color=Y)
    S.say("于是结点还要存“最大前缀和”和“最大后缀和”。那么父亲的最大前缀怎么算？")
    S.say("父亲的前缀要么完全在左半（左.前缀），要么吃掉整个左半再延伸到右半（左.总和 + 右.前缀）。又需要“总和”。")
    S.note("父.前缀 = max(左.前缀, 左.和 + 右.前缀) → 还需要“和”")
    S.say("“和”自己合并很简单：两边相加。到这里，四个量互相够用了：算父亲的任何一个量，只用到儿子的这四个量。")
    S.note("{y|(和, 前缀, 后缀, 最大)}：合并只用到这四个量 → 封闭", color=Y)

    # ------------------------------------------------------------ 公式与正确性
    S.section("合并公式与为什么够")
    S.note("和 = 左.和 + 右.和")
    S.note("前 = max(左.前, 左.和 + 右.前)")
    S.note("后 = max(右.后, 右.和 + 左.后)")
    S.note("最 = max(左.最, 右.最, 左.后 + 右.前)", color=Y)
    S.say("为什么“最”的公式不会漏？父亲区间里的任意一个子段，只有三种可能：完全在左半、完全在右半、跨过中点。")
    arr3 = Array(A, x=640, y=330, cw=110, ch=74, gap=10, size=32)
    S.show(arr3)
    f1 = arr3.frame(2, 3, CY)
    f2 = arr3.frame(6, 7, O)
    f3 = arr3.frame(3, 6, Y)
    S.play(FadeIn(f1), dur=0.4)
    S.play(FadeIn(f2), dur=0.4)
    S.play(FadeIn(f3), dur=0.4)
    S.say("前两种的最大值是左.最、右.最；第三种拆成“左边的某个后缀 + 右边的某个前缀”，两部分可以分别取最大，所以是左.后 + 右.前。")
    S.say("三种情况覆盖了全部子段、互不遗漏，取最大就对了。前缀、后缀的公式也是同样的分类。")
    S.say("这就是设计结点信息的方法：先写出想要的量，看合并时缺什么，就补什么，直到这组量对合并封闭。", extra=0.5)
    S.note_space()

    # ------------------------------------------------------------ 建树与查询
    S.section("建树与查询")
    S.wide()
    st = SegTree(N, x=960, y=200, w=1500, level_h=150, node_h=58, vals=A, info_size=21)
    S.show(st)
    S.say("叶子的四个量都是它本身的值。从下往上，每个结点用公式合并两个儿子：")
    for lr in st.postorder():
        if lr[0] == lr[1]:
            continue
        kids = st.kids[lr]
        S.play(*[st[k].to(stroke=CY, sw=3) for k in kids], dur=0.25)
        S.play(st[lr].to(text=tup(info[lr]), stroke=Y, sw=3), dur=0.4)
        S.play(*[st[k].to(stroke=LINE2, sw=2) for k in kids], st[lr].to(stroke=LINE2, sw=2), dur=0.2)
    S.say(f"根上的“最”是 {info[(1, N)][3]}，就是整个数组的答案。")
    ql, qr = 2, 7
    parts = st.decompose(ql, qr)
    S.say(f"询问 [{ql}, {qr}]：拆成 " + "、".join(f"[{a},{b}]" if a != b else f"[{a}]" for a, b in parts) + f" 这 {len(parts)} 个结点，从左到右依次合并。")
    S.play(*[st[p].to(fill=tint(Y, 0.3), stroke=Y, sw=3) for p in parts], dur=0.6)
    acc = None
    accs = []
    run = label(960, 800, "", 30, Y)
    S.add(run)
    for p in parts:
        acc = info[p] if acc is None else merge(acc, info[p])
        accs.append(acc)
        S.play(st[p].flash(Y), run.to(text=f"合并到 [{ql},{p[1]}]：" + tup(acc)), dur=0.6)
        S.wait(0.5)
    sub = A[ql - 1:qr]
    assert acc[3] == brute_best(sub)
    S.say(f"结果的“最”是 {acc[3]}，和直接枚举 [{ql}, {qr}] 的所有子段得到的一样。注意合并要{{y|按从左到右的顺序}}：这个合并不满足交换律。")
    S.say("修改一个数时，只要重新计算它到根路径上的 log n 个结点。询问、修改都是 O(log n)。")

    # ------------------------------------------------------------ 不能合并的信息
    S.section("反例：区间众数")
    S.narrow()
    S.say("不是所有信息都能这样设计。比如“区间众数”（出现次数最多的数）。")
    la_ = Array([1, 1, 1, 2, 2], x=330, y=360, cw=86, ch=70, gap=8, size=32)
    ra_ = Array([3, 3, 3, 2, 2], x=860, y=360, cw=86, ch=70, gap=8, size=32)
    S.show(la_, ra_)
    S.show(label(330, 470, "左半众数：1（3 次）", 28, CY), label(860, 470, "右半众数：3（3 次）", 28, O))
    S.say("左半的众数是 1，右半的众数是 3。可合在一起，2 出现了 4 次，众数是 2——它在哪一半都不是众数。")
    S.play(*[la_[i].to(fill=tint(Y, 0.4)) for i in (4, 5)], *[ra_[i].to(fill=tint(Y, 0.4)) for i in (4, 5)], dur=0.6)
    S.note("众数：合并后的众数可能在两半都不是众数 ✗", color=R)
    S.say("想要能合并，就得存下每个数的出现次数，信息量和区间长度一样大，失去了线段树的意义。众数要用别的方法（如第 31 集的分块）。")
    S.note("可合并的前提：用固定几个量就能封闭", color=Y)

    # ------------------------------------------------------------ 手推题
    S.quiz("区间询问“最长的连续严格上升段”的长度（例如 1 3 5 2 4 中是 1 3 5，长度 3）。支持单点修改。\n\n"
           "线段树结点需要存哪些量？写出“最长上升段”的合并式。", think=20)
    S.say("仿照最大子段和：跨过中点的上升段 = 左半的“最长上升后缀” + 右半的“最长上升前缀”。")
    S.say("但能不能接上，要看左半最后一个数是否小于右半第一个数。所以还要存区间的{y|首元素和尾元素}。")
    S.note("存：长度 len、首元素 first、尾元素 last、上升前缀 pre、上升后缀 suf、最长 best", color=Y)
    S.note("best = max(左.best, 右.best, 左.last < 右.first ? 左.suf + 右.pre : 0)")
    S.say("前缀也要分情况：如果左半整体就是上升的（左.pre = 左.len）并且能接上，父.pre = 左.len + 右.pre，否则就是左.pre。")
    S.note("pre = (左.pre = 左.len 且 左.last < 右.first) ? 左.len + 右.pre : 左.pre")
    S.say("又是同样的步骤：写出想要的量 → 看合并缺什么（边界元素、整体是否上升）→ 补上，直到封闭。", extra=0.5)

    S.recap([
        "线段树的核心是结点信息的设计：父亲的信息必须能只由两个儿子的信息算出。",
        "最大子段和：只存最大值不够（跨中点）→ 补最大前缀、后缀 → 再补总和，四个量封闭。",
        "正确性靠分类：子段要么在左、要么在右、要么跨中点（= 左后缀 + 右前缀）。",
        "合并要按左右顺序；众数这类信息无法用固定几个量封闭，不适合线段树。",
    ], next_title="懒标记及其复合：把标记看成函数")
