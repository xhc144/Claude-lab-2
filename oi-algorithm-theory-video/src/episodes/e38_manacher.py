"""第 38 集 Manacher：回文半径的复用"""

from episodes.common import *
from episodes.e36_kmp_border import st

S0 = "abacabacx"
QZ = "abbabbaa"


def manacher(s):
    t = "#" + "#".join(s) + "#"
    n = len(t)
    p = [0] * n
    C = R = 0                  # 当前右端点最远的回文：中心 C，右端点 R = C + p[C]
    log = []
    for i in range(n):
        init, case, j = 0, "out", None
        if i < R:
            j = 2 * C - i
            if p[j] < R - i:
                init, case = p[j], "in"
            elif p[j] > R - i:
                init, case = R - i, "over"
            else:
                init, case = p[j], "edge"
        k = init
        while i - k - 1 >= 0 and i + k + 1 < n and t[i - k - 1] == t[i + k + 1]:
            k += 1
        p[i] = k
        log.append((i, C, R, j, case, init, k))
        if i + k > R:
            C, R = i, i + k
    return t, p, log


def longest(s):
    best = ""
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            if s[i:j] == s[i:j][::-1] and j - i > len(best):
                best = s[i:j]
    return best


def build(S):
    S.cover("求字符串里最长的回文子串。以每个位置为中心向两边扩展，最坏要 O(n²)。Manacher 把已经算过的回文“照镜子”复用，做到 O(n)。",
            ["回文串", "中心扩展法"])

    t, p, log = manacher(S0)
    assert max(p) == len(longest(S0))
    n = len(t)

    # ------------------------------------------------------------ 统一奇偶
    S.section("插入分隔符，统一奇偶")
    sa = Array(list(S0), x=640, y=230, cw=64, ch=58, gap=8, size=30, chain="tt")
    S.show(sa, label(640, 160, "原串 s", 24, DIM))
    S.say("回文有奇数长（中心是一个字符）和偶数长（中心在两个字符之间）两种。在每两个字符之间、以及两端插入一个分隔符 #，两种就统一了。")
    ta = Array(list(t), x=640, y=420, cw=52, ch=56, gap=6, size=26, chain="tt", base=0, idx_size=17)
    for i in range(n):
        if t[i] == "#":
            ta.cells[i].label.tr["color"].base = FAINT
    S.show(ta, label(640, 350, "插入分隔符后的 T（下标从 0 开始）", 24, DIM))
    S.note("T = # s₁ # s₂ # … # sₙ #：奇偶回文都以某个位置为中心")
    S.say("T 里每个回文都以某个位置为中心、两边对称；中心在字母上对应 s 的奇回文，中心在 # 上对应偶回文。")
    S.say("记 p[i] 为 T 中以 i 为中心的回文半径（不含中心，向一边延伸的格数）。它恰好等于 s 中对应回文的长度。")
    S.note("p[i] = 以 i 为中心的回文半径 = 对应 s 中回文的长度", color=Y)

    # ------------------------------------------------------------ 朴素扩展
    S.section("朴素：每个中心向外扩", keep=[ta])
    pv = Array([""] * n, x=640, y=560, cw=52, ch=48, gap=6, size=24, index=False, fill=tint(B, 0.12))
    S.show(pv, label(70, 560, "p", 30, B, anchor="lm"))
    c = 7
    S.say(f"以位置 {c}（字母 {st(t[c])}）为中心，两边一格一格比较，相同就扩大半径。")
    br = ta.span(c, c, "", Y, side="above")
    S.play(FadeIn(br), ta[c].to(fill=tint(Y, 0.4)), dur=0.4)
    for k in range(1, p[c] + 1):
        S.play(ta.respan(br, c - k, c + k), ta[c - k].to(fill=tint(Y, 0.25)), ta[c + k].to(fill=tint(Y, 0.25)), dur=0.3)
    if c + p[c] + 1 < n:
        S.play(ta[c - p[c] - 1].to(stroke=R, sw=3), ta[c + p[c] + 1].to(stroke=R, sw=3), dur=0.4)
    S.play(pv[c].to(text=str(p[c]), fill=tint(B, 0.35)), dur=0.4)
    S.say(f"扩到半径 {p[c]} 后两端不同（红框），p[{c}] = {p[c]}：s 中有长度 {p[c]} 的回文 {st(S0[(c - p[c]) // 2:(c + p[c]) // 2])}。")
    S.say("每个中心都这样扩，全是同一个字母的串（aaaa…）要 O(n²)。浪费在哪？大回文里面的小回文，左右两边是镜像的，算了两遍。")
    S.note("朴素：O(n²)；大回文内部左右对称，信息被重复计算", color=R)
    S.play(FadeOut(br), *[ta[k].to(fill=BG3, stroke=LINE, sw=2) for k in range(n)], pv[c].to(text="", fill=tint(B, 0.12)),
           dur=0.4)

    # ------------------------------------------------------------ 镜像
    S.section("镜像：对称位置的答案可以复用", keep=[ta, pv])
    S.say("从左到右算 p，同时记住“右端点最远”的那个回文：中心 C，右端 R = C + p[C]，左端 L = 2C − R。")
    S.note("维护右端点最远的回文 [L, R]，中心 C", color=Y)
    big = ta.span(0, 0, "", CY, side="above")
    S.add(big)
    big.tr["op"].base = 0
    ip = ta.ptr(0, "i", O)
    jp = ta.ptr(0, "j", CY)
    cur_C = None
    shown = False
    for (i, Cc, Rr, j, case, init, k) in log:
        if i < 4:
            S.play(pv[i].to(text=str(p[i]), fill=tint(B, 0.3)), dur=0.15)
            continue
        if Cc != cur_C and Rr > 0:
            S.play(*([FadeIn(big)] if not shown else []), ta.respan(big, 2 * Cc - Rr, Rr), dur=0.4)
            shown = True
            cur_C = Cc
        anims = [ta.move(ip, i)] + ([FadeIn(ip)] if i == 4 else [])
        if j is not None:
            anims += [ta.move(jp, j)] + ([FadeIn(jp)] if i == 4 else [])
        S.play(*anims, dur=0.3)
        if i == 9:
            S.say(f"i = 9 在大回文 [{2 * Cc - Rr}, {Rr}]（中心 {Cc}）里面。它的镜像位置 j = 2C − i = {j}，p[{j}] = {p[j]}。")
            S.say("大回文内部左右对称：j 周围长什么样，i 周围就长什么样。j 的回文完全落在大回文里（p[j] < R − i），所以 p[i] 一定恰好等于 p[j]。")
            S.note("i < R 时，镜像 j = 2C − i；p[j] < R − i ⇒ p[i] = p[j]", color=G)
        if i == 11:
            S.say(f"i = 11：镜像 j = {j}，p[{j}] = {p[j]}，恰好碰到大回文的边界（R − i = {Rr - i}）。边界以外的字符大回文管不着，只知道 p[i] ≥ {init}。")
            S.note("p[j] = R − i：只知道 p[i] ≥ R − i，要继续向外扩", color=Y)
        if i == 15:
            S.say(f"i = 15：镜像 j = {j}，p[{j}] = {p[j]}，比 R − i = {Rr - i} 大。这时 p[i] 恰好就是 R − i = {Rr - i}，不用扩。为什么？")
            Lb = 2 * Cc - Rr
            a_, b_, c_ = Lb - 1, Rr + 1, 2 * i - Rr - 1
            S.play(ta[a_].to(stroke=R, sw=3.5), ta[b_].to(stroke=R, sw=3.5), ta[c_].to(stroke=Y, sw=3.5), dur=0.5)
            S.say(f"再扩一格要比较 T[{b_}] 和 T[{c_}]。T[{c_}] 关于 C 镜像、再关于 j 镜像，等于 T[{a_}]；而大回文停在 [{Lb}, {Rr}]，正是因为 T[{a_}] ≠ T[{b_}]。")
            S.note("p[j] > R − i ⇒ p[i] = R − i（两次镜像得到矛盾）", color=G)
            S.play(ta[a_].to(stroke=LINE, sw=2), ta[b_].to(stroke=LINE, sw=2), ta[c_].to(stroke=LINE, sw=2), dur=0.3)
        if k > init:
            for kk in range(init + 1, k + 1):
                S.play(ta[i - kk].to(fill=tint(O, 0.35)), ta[i + kk].to(fill=tint(O, 0.35)), dur=0.3)
            if i + k + 1 < n:
                S.play(ta[i - k - 1].to(stroke=R, sw=3), ta[i + k + 1].to(stroke=R, sw=3), dur=0.3)
            if i == 11:
                S.say(f"从半径 {init} 接着往外比：又扩了 {k - init} 格，p[11] = {k}。右端点推进到 {i + k}，它成为新的“最右回文”。")
            S.play(*[ta[x].to(fill=BG3, stroke=LINE, sw=2) for x in range(max(0, i - k - 1), min(n, i + k + 2))], dur=0.3)
        S.play(pv[i].to(text=str(k), fill=tint(B, 0.3) if case in ("out", "edge") else tint(G, 0.3)), dur=0.3)
    S.play(FadeOut(ip), FadeOut(jp), FadeOut(big), dur=0.3)
    best = max(range(n), key=lambda x: p[x])
    S.say(f"最大的 p 是 p[{best}] = {p[best]}，对应最长回文子串 {st(S0[(best - p[best]) // 2:(best + p[best]) // 2])}。绿色的格子都是直接从镜像抄来的，没有做任何比较。")
    S.note("p[i] 的初值 = min(p[j], R − i)；只有等于 R − i 或 i ≥ R 时才扩", color=Y)

    # ------------------------------------------------------------ 复杂度
    S.section("为什么是线性的")
    S.say("复用镜像是 O(1)。真正花时间的是向外扩的比较。注意：只有初值碰到了 R（或者 i 在 R 之外）时才需要扩。")
    S.say("这时每扩成功一格，i 的回文右端就超出原来的 R 一格，R 随之更新为更右的位置。R 只增不减，最多到 |T| = 2n + 1。")
    S.note("每次成功扩展都让 R 右移一格；R ≤ 2n + 1 ⇒ 扩展总次数 O(n)", color=G)
    S.say("每个 i 最多再有一次失败的比较。所以总共 O(n)——和 KMP 的“j 只增不减”是同一种势能论证。", extra=0.5)
    S.note("每个 i 至多一次失败比较；总 O(n)")

    # ------------------------------------------------------------ 手推题
    tq, pq, lq = manacher(QZ)
    S.quiz(f"s = {{t|{QZ}}}。\n\n"
           f"(1) 写出插入分隔符后的 T（长度 {len(tq)}）和 p 数组。\n"
           "(2) 哪些位置的 p 是从镜像直接抄来的（不需要任何比较就确定）？\n"
           "(3) 最长回文子串是什么？", think=20)
    S.say("(1) p = " + " ".join(str(v) for v in pq) + "。")
    S.note("(1) p = " + " ".join(str(v) for v in pq), color=Y)
    copied = [i for (i, Cc, Rr, j, case, init, k) in lq if case in ("in", "over")]
    S.say("(2) 初值严格小于 R − i、或者镜像比 R − i 长的位置，直接确定：i = " + "、".join(map(str, copied)) + "。其余位置要往外扩（至少比一次）。")
    S.note("(2) 直接确定：" + "、".join(map(str, copied)), color=G)
    bq = max(range(len(tq)), key=lambda x: pq[x])
    S.say(f"(3) 最大 p 在位置 {bq}，p = {pq[bq]}，最长回文子串是 {st(QZ[(bq - pq[bq]) // 2:(bq + pq[bq]) // 2])}。", extra=0.5)
    S.note(f"(3) {st(QZ[(bq - pq[bq]) // 2:(bq + pq[bq]) // 2])}（长度 {pq[bq]}）")

    S.recap([
        "插入分隔符让奇偶回文统一；p[i] 是 T 中的回文半径，恰好等于 s 中对应回文的长度。",
        "维护右端点最远的回文 [L, R]：i < R 时镜像 j = 2C − i，p[i] 至少是 min(p[j], R − i)。",
        "p[j] < R − i 或 p[j] > R − i 时直接确定；只有等于 R − i（或 i ≥ R）才向外扩。",
        "每次成功扩展都让 R 右移，R 只增不减，总复杂度 O(n)。",
    ], next_title="AC 自动机")
