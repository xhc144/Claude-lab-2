"""第 31 集 分块：整块打标记，零散暴力"""

import bisect

from episodes.common import *

A0 = [5, 1, 8, 3, 7, 2, 6, 4, 9, 2, 5, 7]
B = 4


def build(S):
    S.cover("区间加一个数、询问区间里有多少个数 ≥ c。线段树的结点信息合并不起来，怎么办？",
            ["线段树的信息设计与懒标记（第 14、15 集）", "二分查找"])

    n = len(A0)
    nb = n // B
    a = list(A0)
    tag = [0] * nb

    # ------------------------------------------------------------ 问题
    S.section("问题：区间加，数 ≥ c 的个数")
    arr = Array(a, x=640, y=300, cw=84, ch=66, gap=8, size=30)
    S.show(arr)
    S.say("两种操作：给 [l, r] 每个数加 x；询问 [l, r] 里有多少个数 ≥ c。")
    S.note("操作：区间加 x；询问区间内 ≥ c 的个数")
    S.say("用线段树的话，结点要能回答“我这段里有几个数 ≥ c”，c 每次都不同，只能存整段排好序的数组——再加上区间加的标记，合并和下传都很难。")
    S.note("线段树：信息（有序数组）太大，带标记合并困难", color=R)
    S.say("换一种思路：不切成 log n 层，只切一层。把数组分成若干块，每块长度 B。")

    # ------------------------------------------------------------ 分块
    S.section("分成 √n 块", keep=[arr])
    frames = [arr.frame(i * B + 1, i * B + B, [CY, O, G][i], pad=4) for i in range(nb)]
    S.play(*[FadeIn(f) for f in frames], dur=0.6)
    S.say(f"这里 n = {n}，每块 {B} 个，共 {nb} 块。每块额外维护两样东西：一个整块的加法标记 tag，以及块内元素排好序的副本。")
    S.note("每块：加法标记 tag + 块内元素的有序副本", color=Y)
    tags, sorts = [], []
    for i in range(nb):
        cx = arr.X(i * B + 1) + (B - 1) * (84 + 8) / 2
        t = label(cx, 410, "tag = 0", 24, [CY, O, G][i])
        srt = Array(sorted(a[i * B:(i + 1) * B]), x=cx, y=490, cw=56, ch=46, gap=4, size=22, index=False)
        tags.append(t)
        sorts.append(srt)
    S.show(*tags, *sorts, lag=0.1)
    slab = label(140, 490, "有序副本", 22, DIM, anchor="rm")
    S.show(slab)
    keep = [arr, slab] + tags + sorts
    S.say("核心原则：{y|整块的部分打标记，零散的部分暴力}。一个区间最多覆盖两个零散的半块，中间都是整块。")
    S.note("整块：只动标记；零散：直接改元素", color=G)

    # ------------------------------------------------------------ 区间加
    S.section("区间加", keep=keep)
    l, r, x = 3, 10, 2
    S.say(f"例：给 [{l}, {r}] 加 {x}。第 1 块只覆盖了 3、4 两个位置（零散），第 2 块整块被覆盖，第 3 块只覆盖 9、10（零散）。")
    span = arr.span(l, r, f"+{x}", Y, "above")
    S.play(FadeIn(span), dur=0.4)
    S.say("整块（第 2 块）：只把 tag 加 2。有序副本完全不用动——整块里每个数都加同样的数，相对大小顺序不变。")
    tag[1] += x
    S.play(tags[1].to(text=f"tag = {tag[1]}"), frames[1].bump(dur=0.8, glow=1.0), dur=0.8)
    S.note("整块加：tag += x，有序副本不变（同加一个数，顺序不变）", color=Y)
    S.say("零散部分：直接改那几个元素，然后把这一块的有序副本重新排序，代价 O(B log B)。")
    for i in (3, 4, 9, 10):
        a[i - 1] += x
    S.play(*[arr[i].to(text=str(a[i - 1]), fill=tint(Y, 0.35)) for i in (3, 4, 9, 10)], dur=0.5)
    S.play(*[sorts[0].cells[k].to(text=str(v)) for k, v in enumerate(sorted(a[0:4]))],
           *[sorts[2].cells[k].to(text=str(v)) for k, v in enumerate(sorted(a[8:12]))], dur=0.6)
    S.play(*[arr[i].to(fill=BG3) for i in (3, 4, 9, 10)], FadeOut(span), dur=0.3)
    S.say("注意第 2 块的元素本身还是原值，真实值 = 元素 + tag。")

    # ------------------------------------------------------------ 询问
    S.section("询问 ≥ c 的个数", keep=keep)
    ql, qr, c = 2, 11, 7
    real = [a[i] + tag[i // B] for i in range(n)]
    S.say(f"询问 [{ql}, {qr}] 中 ≥ {c} 的个数。")
    span2 = arr.span(ql, qr, f"≥ {c}?", CY, "above")
    S.play(FadeIn(span2), dur=0.4)
    S.say(f"整块（第 2 块）：真实值 ≥ {c} ⇔ 存的值 ≥ {c} − tag = {c - tag[1]}。在有序副本里二分，找到第一个 ≥ {c - tag[1]} 的位置，后面的都满足。")
    blk = sorted(a[4:8])
    pos = bisect.bisect_left(blk, c - tag[1])
    S.play(*[sorts[1].cells[k].to(fill=tint(G, 0.45) if k >= pos else BG3) for k in range(B)], dur=0.6)
    cnt_whole = B - pos
    S.note(f"整块：在有序副本里二分 ≥ c − tag，O(log B)", color=Y)
    S.say(f"第 2 块里有 {cnt_whole} 个。零散部分（位置 2、3、4 和 9、10、11）逐个看真实值是否 ≥ {c}。")
    cnt_part = 0
    for i in list(range(ql, 5)) + list(range(9, qr + 1)):
        ok = real[i - 1] >= c
        cnt_part += ok
        S.play(arr[i].to(fill=tint(G, 0.45) if ok else tint(R, 0.25)), dur=0.2)
    total = cnt_whole + cnt_part
    assert total == sum(1 for i in range(ql - 1, qr) if real[i] >= c)
    S.say(f"零散部分有 {cnt_part} 个，总共 {total} 个。")
    S.note(f"本例答案 {total}")

    # ------------------------------------------------------------ 复杂度
    S.section("块长取多少")
    S.say("设块长 B，块数 n/B。一次操作：整块最多 n/B 个，每个 O(1)（加）或 O(log B)（二分）；零散最多 2B 个元素，加上重排 O(B log B)。")
    S.note("单次：整块 O((n/B)·log B) + 零散 O(B log B)")
    ax = Axes(x=600, y=500, w=720, h=380, xr=(0, 100), yr=(0, 160), xstep=20, ystep=40, xlabel="B", ylabel="代价")
    S.show(ax)
    bs = list(range(10, 101, 3))
    d1 = [ax.dot(b_, 1200 / b_, CY, 4) for b_ in bs]
    d2 = [ax.dot(b_, b_, O, 4) for b_ in bs]
    d3 = [ax.dot(b_, 1200 / b_ + b_, Y, 5) for b_ in bs]
    S.play(*[FadeIn(p_) for p_ in d1], dur=0.5, lag=0.01)
    S.play(*[FadeIn(p_) for p_ in d2], dur=0.5, lag=0.01)
    S.play(*[FadeIn(p_) for p_ in d3], dur=0.5, lag=0.01)

    def at(xv, yv):
        px, py = ax.p(xv, yv)
        return 600 + px, 500 + py

    S.show(label(*at(80, 32), "整块部分 ∝ n/B", 24, CY), label(*at(99, 62), "零散部分 ∝ B", 24, O, anchor="rm"),
           label(*at(35, 88), "总和", 24, Y))
    S.say("一个随 B 增大而减小，一个随 B 增大而增大。两者相等时总和最小：B 取 √n 左右（考虑 log 因子可以略作调整）。")
    S.note("两部分平衡：B ≈ √n → 单次 O(√n · log n)", color=G)
    S.say("分块的思想是“只分一层”：牺牲一点复杂度（√n 而不是 log n），换来信息不必能合并、标记不必能复合的自由。")
    S.note("分块：用 √n 换取“不需要可合并”的自由", color=Y)

    # ------------------------------------------------------------ 手推题
    S.quiz("第 15 集说过：“区间开平方（向下取整）+ 区间求和”不能用懒标记。用分块怎么做？\n\n"
           "提示：一个不超过 10¹⁸ 的数，反复开平方，最多几次就变成 1？", think=20)
    S.say("10¹⁸ → 10⁹ → 31622 → 177 → 13 → 3 → 1，最多 6 次就变成 1（或 0），之后再开平方也不变。")
    S.note("每个数最多被开 6 次平方就不再变化", color=Y)
    S.say("所以每块维护：块内和，以及一个标记“这块已经全是 0 或 1”。开平方时，整块如果已经全是 0/1 就直接跳过；否则逐个元素暴力开平方。")
    S.note("每块：和 + “全是 0/1”标记；已全是 0/1 的块直接跳过", color=G)
    S.say("复杂度：每个元素一共最多被暴力处理 6 次，总共 O(6n)；每次操作还要扫过 O(n/B) 个块、处理 O(B) 个零散元素。分块不靠标记，靠的是“势能”。", extra=0.5)

    S.recap([
        "分块：分成长度 B 的块，整块打标记、零散暴力。",
        "区间加 + 计数 ≥ c：每块存 tag 和有序副本；整块加不改顺序，询问在有序副本里二分 c − tag。",
        "整块代价 ∝ n/B、零散代价 ∝ B，取 B ≈ √n 平衡。",
        "分块不要求信息可合并、标记可复合，适用面很广；也常和“势能”论证配合。",
    ], next_title="莫队：给询问排个序")
