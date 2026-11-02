"""第 42 集 后缀数组（下）：height 与最长公共前缀"""

from engine import text as T
from episodes.common import *
from episodes.e36_kmp_border import st
from episodes.e41_suffix_array import suffix_array

S0 = "banana"
QZ = "abaab"


def lcp(a, b):
    k = 0
    while k < len(a) and k < len(b) and a[k] == b[k]:
        k += 1
    return k


def heights(s, sa):
    n = len(s)
    return [0] + [lcp(s[sa[r - 1] - 1:], s[sa[r] - 1:]) for r in range(1, n)]


def kasai(s, sa, rk):
    """按起点顺序求 h[i] = height[rk[i]]，记下每一步的起点值和扩展次数。"""
    n = len(s)
    h = [0] * (n + 1)
    k = 0
    log = []
    for i in range(1, n + 1):
        if k:
            k -= 1
        start = k
        if rk[i - 1] == 1:
            k = 0
            log.append((i, None, 0, 0))
            continue
        j = sa[rk[i - 1] - 2]
        while i + k <= n and j + k <= n and s[i + k - 1] == s[j + k - 1]:
            k += 1
        h[i] = k
        log.append((i, j, start, k))
    return h[1:], log


def distinct(s):
    return len({s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)})


def build(S):
    S.cover("后缀排好序以后，相邻两个后缀的最长公共前缀（LCP）藏着很多信息：重复子串、本质不同子串的个数……怎样在 O(n) 时间里求出它们？",
            ["后缀数组（第 41 集）", "ST 表（区间最小值）"])

    n = len(S0)
    sa, rk, _ = suffix_array(S0)
    ht = heights(S0, sa)

    # ------------------------------------------------------------ height
    S.section("相邻后缀的 LCP：height")
    def make_rows():
        out = []
        for r, i in enumerate(sa):
            y = 220 + 66 * r
            g = Group(0, 0)
            g.add(label(300, y, f"{r + 1}", 26, DIM))
            g.add(label(360, y, f"sa = {i}", 24, O, anchor="lm"))
            g.add(Text(500, y, st(S0[i - 1:]), size=32, anchor="lm"))
            out.append(g)
        return out

    rows = make_rows()
    S.show(*rows, dur=0.6, lag=0.06)
    S.show(label(300, 160, "名次", 22, DIM), label(500, 160, "后缀（已排序）", 22, DIM, anchor="lm"))
    S.say(f"{st(S0)} 的后缀已经排好序。height[r] = 第 r 名和第 r − 1 名两个后缀的最长公共前缀长度（第 1 名记 0）。")
    S.note("height[r] = LCP(第 r − 1 名, 第 r 名)", color=Y)
    hl = []
    for r in range(1, n):
        a, b = sa[r - 1], sa[r]
        k = ht[r]
        y0 = 220 + 66 * (r - 1)
        if k:
            kw = T.layout(st(S0[b - 1:b - 1 + k]), 32, None).w
            bx = Rect(500 + kw / 2, y0 + 33, kw + 12, 102, fill=alpha(Y, 0.10), stroke=alpha(Y, 0.6), sw=1.5, r=8)
            bx.tr["op"].base = 0
            S.objs.insert(0, bx)
            hl.append(bx)
        t = label(780, 220 + 66 * r, f"height = {k}", 26, Y if k else DIM, anchor="lm")
        t.tr["op"].base = 0
        S.add(t)
        S.play(*([FadeIn(bx)] if k else []), FadeIn(t), dur=0.4)
        if r == 2:
            S.say(f"{st(S0[a - 1:])} 和 {st(S0[b - 1:])} 开头有 {k} 个字符相同（黄框），height = {k}。")
    S.say("height 里最大的值，就是最长的、出现至少两次的子串长度：这里是 3，对应 " + st("ana") + "。")
    S.note("max height = 最长重复子串的长度", color=G)

    # ------------------------------------------------------------ 区间最小值
    S.section("任意两个后缀的 LCP = height 的区间最小值", keep=rows)
    S.say("任意两个后缀（名次 l < r）的 LCP 是多少？结论：等于 height[l + 1], …, height[r] 里的最小值。")
    S.note("LCP(第 l 名, 第 r 名) = min(height[l + 1..r])", color=Y)
    hv = Array(ht, x=1060, y=440, cw=56, ch=52, gap=6, size=24, idx_labels=[str(r + 1) for r in range(n)],
               fill=tint(Y, 0.15))
    S.show(hv, label(1060, 370, "height", 24, Y))
    l_, r_ = 1, 3
    fr = hv.frame(l_ + 1, r_, CY)
    S.play(FadeIn(fr), *[rows[x].to(op=1.0) for x in range(n)], dur=0.4)
    S.say(f"例：第 {l_} 名 {st(S0[sa[l_ - 1] - 1:])} 和第 {r_} 名 {st(S0[sa[r_ - 1] - 1:])}，"
          f"min(height[{l_ + 1}..{r_}]) = min({', '.join(str(ht[x]) for x in range(l_, r_))}) = {min(ht[l_:r_])}，确实只有开头 1 个字符相同。")
    assert lcp(S0[sa[l_ - 1] - 1:], S0[sa[r_ - 1] - 1:]) == min(ht[l_:r_])
    S.say("为什么？相邻的都共有前 m 个字符（m 是区间最小值），那么从第 l 名到第 r 名一路传过去，首尾也共有前 m 个字符：LCP ≥ m。")
    S.say("反过来，如果首尾共有前 m + 1 个字符，按字典序夹在它们中间的后缀也都以这 m + 1 个字符开头，每个相邻的 height 都 ≥ m + 1，和最小值是 m 矛盾。")
    S.note("相邻共享 ⇒ 首尾共享；首尾共享 ⇒ 中间都共享（字典序夹逼）", color=G)
    S.say("所以用 ST 表预处理 height 的区间最小值，任意两个后缀的 LCP 都能 O(1) 回答。", extra=0.3)
    S.note("ST 表：O(n log n) 预处理，O(1) 查询任意两个后缀的 LCP")

    # ------------------------------------------------------------ 线性求 height
    S.section("线性求 height：h[i] ≥ h[i − 1] − 1")
    S.say("直接按定义求 height，每个最坏比 O(n) 个字符，共 O(n²)。改成按起点顺序算：记 h[i] = height[rk[i]]，即后缀 i 和它前一名的 LCP。")
    S.note("h[i] = height[rk[i]]：后缀 i 和它在排序中的前一名的 LCP", color=Y)
    h, klog = kasai(S0, sa, rk)
    sarr = Array(list(S0), x=640, y=220, cw=72, ch=62, gap=8, size=30, chain="tt")
    harr = Array([""] * n, x=640, y=340, cw=72, ch=52, gap=8, size=26, index=False, fill=tint(B, 0.15))
    S.show(sarr, harr, label(150, 340, "h", 30, B, anchor="lm"))
    S.say("关键引理：h[i] ≥ h[i − 1] − 1。设后缀 i − 1 的前一名是后缀 k − 1，它们开头有 h[i − 1] 个字符相同。")
    S.say("两个后缀同时去掉第一个字符：后缀 k 仍然排在后缀 i 前面，而且开头还有 h[i − 1] − 1 个字符相同。")
    S.say("后缀 i 的前一名，在字典序上夹在后缀 k 和后缀 i 之间（或者就是 k），由上一节的结论，它和后缀 i 的 LCP 至少是 h[i − 1] − 1。")
    S.note("h[i] ≥ h[i − 1] − 1：从上一个 h 减一开始接着比", color=G)
    ex = 0
    for i, j, start, k in klog:
        S.play(sarr[i].to(fill=tint(O, 0.4)), dur=0.3)
        if j is not None:
            S.play(sarr[j].to(fill=tint(CY, 0.4)), dur=0.3)
        S.play(harr[i].to(text=str(k), fill=tint(B, 0.35)), dur=0.35)
        if j is not None and start > 0 and ex < 1:
            S.say(f"i = {i}：上一个 h = {h[i - 2]}，直接从 {start} 开始比，只多比了 {k - start} 次就得到 h[{i}] = {k}。")
            ex += 1
        S.play(sarr[i].to(fill=BG3), *([sarr[j].to(fill=BG3)] if j is not None else []), dur=0.2)
    assert all(h[i - 1] == ht[rk[i - 1] - 1] for i in range(1, n + 1))
    S.say("k 每轮最多减 1，而 k ≤ n，所以“往后比”的总次数不超过 2n：整个过程 O(n)。和 KMP、Manacher 是同一种势能论证。", extra=0.3)
    S.note("k 每轮至多减一、总增量 ≤ 2n ⇒ O(n)", color=Y)

    # ------------------------------------------------------------ 本质不同子串
    S.section("应用：本质不同的子串个数")
    rows = make_rows()
    S.show(*rows, label(300, 160, "名次", 22, DIM), label(500, 160, "后缀（已排序）", 22, DIM, anchor="lm"), dur=0.5)
    S.say("每个子串都是某个后缀的前缀。按排序顺序看：第 r 名后缀贡献它的全部前缀，但和前一名重合的 height[r] 个前缀已经数过了。")
    S.note("本质不同子串 = Σ (后缀长度 − height[r])", color=Y)
    contrib = [n - sa[r] + 1 - ht[r] for r in range(n)]
    tags = [label(780, 220 + 66 * r, f"{n - sa[r] + 1} − {ht[r]} = {contrib[r]}", 26, G, anchor="lm") for r in range(n)]
    S.show(*tags, dur=0.5, lag=0.08)
    S.say("为什么只减 height[r]？和更早的后缀的公共前缀，按区间最小值的结论，不会超过和前一名的公共前缀，所以不会漏减。")
    tot = sum(contrib)
    assert tot == distinct(S0)
    S.say(f"合计 {' + '.join(map(str, contrib))} = {tot}：{st(S0)} 有 {tot} 个本质不同的子串。", extra=0.3)
    S.note(f"{st(S0)}：{tot} 个本质不同子串", color=G)

    # ------------------------------------------------------------ 手推题
    qsa, qrk, _ = suffix_array(QZ)
    qh = heights(QZ, qsa)
    m = len(QZ)
    S.quiz(f"s = {{t|{QZ}}}，sa = " + " ".join(map(str, qsa)) + "。\n\n"
           "(1) 求 height 数组。\n"
           "(2) 后缀 1 和后缀 4 的 LCP 是多少？用区间最小值说明。\n"
           "(3) s 有多少个本质不同的子串？最长的重复子串是什么？", think=20)
    S.say("(1) 排好序依次是 " + "、".join(st(QZ[i - 1:]) for i in qsa) + "，height = " + " ".join(map(str, qh)) + "。")
    S.note("(1) height = " + " ".join(map(str, qh)), color=Y)
    a, b = sorted((qrk[0], qrk[3]))
    S.say(f"(2) 后缀 1 排第 {qrk[0]}，后缀 4 排第 {qrk[3]}，LCP = min(height[{a + 1}..{b}]) = {min(qh[a:b])}。")
    assert min(qh[a:b]) == lcp(QZ, QZ[3:])
    qc = [m - qsa[r] + 1 - qh[r] for r in range(m)]
    best = max(range(m), key=lambda r: qh[r])
    S.say(f"(3) Σ(长度 − height) = {' + '.join(map(str, qc))} = {sum(qc)}；最大 height = {qh[best]}，最长重复子串是 {st(QZ[qsa[best] - 1:qsa[best] - 1 + qh[best]])}。", extra=0.5)
    assert sum(qc) == distinct(QZ)
    S.note(f"(2) {min(qh[a:b])}；(3) {sum(qc)} 个，最长重复 {st(QZ[qsa[best] - 1:qsa[best] - 1 + qh[best]])}", color=G)

    S.recap([
        "height[r] 是排序后相邻两个后缀的 LCP；最大的 height 就是最长重复子串。",
        "任意两个后缀的 LCP = 它们名次之间 height 的区间最小值（字典序夹逼），配 ST 表 O(1) 查询。",
        "h[i] = height[rk[i]] 满足 h[i] ≥ h[i − 1] − 1，按起点顺序接着比，O(n) 求出全部 height。",
        "本质不同子串个数 = Σ(后缀长度 − height)。",
    ], next_title="扩展欧几里得与同余方程")
