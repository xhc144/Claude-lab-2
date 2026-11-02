"""第 36 集 KMP 中的 border：失配链枚举全部 border"""

from episodes.common import *

S0 = "abacaba"
P = "abacabab"
TXT = "abacabacabab"
QZ = "aabaaab"


def st(x):
    """字符串用打字机字体。"""
    return "{t|" + x + "}"


def borders(s):
    return [k for k in range(len(s) - 1, 0, -1) if s[:k] == s[-k:]]


def prefix_function(s):
    """π[i]（i 从 1 开始），并记下每一步 j 依次尝试的值。"""
    n = len(s)
    pi = [0] * (n + 1)
    trials = {}
    j = 0
    for i in range(2, n + 1):
        tried = [j]
        while j > 0 and s[j] != s[i - 1]:
            j = pi[j]
            tried.append(j)
        if s[j] == s[i - 1]:
            j += 1
        pi[i] = j
        trials[i] = tried
    return pi, trials


def kmp_match(t, p, pi):
    """匹配过程：[(i, j_before, [跳到的 j...], 匹配后 j)]，以及出现位置。"""
    j = 0
    log, occ = [], []
    for i in range(1, len(t) + 1):
        jumps = []
        while j > 0 and (j == len(p) or p[j] != t[i - 1]):
            j = pi[j]
            jumps.append(j)
        if p[j] == t[i - 1]:
            j += 1
        log.append((i, jumps, j))
        if j == len(p):
            occ.append(i - len(p) + 1)
    return log, occ


def build(S):
    S.cover("在文本里找模式串出现的所有位置。失配时，朴素做法把模式串右移一格从头比；KMP 直接跳到“下一个还可能成功”的位置——这个位置是怎么算出来的？",
            ["字符串的前缀、后缀"])

    pi, trials = prefix_function(P)
    assert pi[1:] == [max([0] + borders(P[:i])) for i in range(1, len(P) + 1)]

    # ------------------------------------------------------------ border
    S.section("border：既是前缀，又是后缀")
    s = Array(list(S0), x=640, y=330, cw=86, ch=76, gap=10, size=38, chain="tt")
    S.show(s, label(640, 220, "字符串 s", 26, DIM))
    S.say("先补一个概念：字符串 s 的 border，是 s 的一个真前缀（不等于 s 本身），同时也是 s 的后缀。")
    S.note("border：既是真前缀又是后缀的串")
    bs = borders(S0)
    bpre = s.span(1, bs[0], "", CY, side="above")
    bsuf = s.span(len(S0) - bs[0] + 1, len(S0), "", O, side="below")
    for k in bs:
        S.play(FadeIn(bpre), FadeIn(bsuf), s.respan(bpre, 1, k), s.respan(bsuf, len(S0) - k + 1, len(S0)),
               *[s[i].to(fill=tint(CY, 0.35)) for i in range(1, k + 1)],
               *[s[i].to(fill=tint(O, 0.35)) for i in range(len(S0) - k + 1, len(S0) + 1)],
               *[s[i].to(fill=BG3) for i in range(k + 1, len(S0) - k + 1)], dur=0.7)
        both = [i for i in range(1, k + 1) if i >= len(S0) - k + 1]
        if both:
            S.play(*[s[i].to(fill=tint(G, 0.45)) for i in both], dur=0.3)
        S.say(f"长度 {k}：前 {k} 个字符是 {st(S0[:k])}，后 {k} 个字符也是 {st(S0[-k:])}，所以 {st(S0[:k])} 是一个 border。"
              + ("前缀和后缀可以重叠（绿色）。" if both else ""))
    S.play(*[s[i].to(fill=BG3) for i in range(1, len(S0) + 1)], FadeOut(bpre), FadeOut(bsuf), dur=0.4)
    S.note(f"{st(S0)} 的 border：" + "、".join(st(S0[:k]) for k in bs) + "（还有空串）", color=Y)
    S.say("KMP 用到的是“最长 border”：把前 i 个字符的最长 border 长度记作 π[i]。π 就是 KMP 的失配数组（也叫 next）。")
    S.note("π[i] = s 的前 i 个字符的最长 border 长度", color=G)

    # ------------------------------------------------------------ border 的 border
    S.section("border 的 border 还是 border", keep=[s])
    S.say(f"一个关键事实：s 的全部 border，可以从最长的那个出发，一个套一个地全部找出来。")
    k1 = bs[0]
    t1 = s.span(1, k1, f"最长 border：{st(S0[:k1])}", CY, side="above")
    t2 = s.span(len(S0) - k1 + 1, len(S0), st(S0[-k1:]), CY, side="below")
    S.play(FadeIn(t1), FadeIn(t2), dur=0.5)
    S.say(f"设 t 是 s 的任意一个更短的 border。t 是 s 的前缀，也就是最长 border {st(S0[:k1])} 的前缀；t 是 s 的后缀，也就是 {st(S0[-k1:])} 的后缀。")
    k2 = bs[1]
    S.play(*[s[i].to(fill=tint(Y, 0.45)) for i in range(1, k2 + 1)],
           *[s[i].to(fill=tint(Y, 0.45)) for i in range(len(S0) - k2 + 1, len(S0) + 1)], dur=0.6)
    S.say(f"所以 t 既是 {st(S0[:k1])} 的前缀又是它的后缀——t 是“最长 border 的 border”。这里 t = {st(S0[:k2])}。")
    S.note("s 的 border = 最长 border b₁，以及 b₁ 的所有 border", color=Y)
    S.say("反过来，border 的 border 当然还是 s 的 border。于是：s 的全部 border 恰好是 π 沿着自己一路跳下去的那条链。")
    S.note("全部 border：π[n] → π[π[n]] → … → 0（失配链）", color=G)
    pi0, _ = prefix_function(S0)
    chain = [len(S0)]
    while chain[-1]:
        chain.append(pi0[chain[-1]])
    S.say(f"例如 {st(S0)}：π[7] = {pi0[7]}，π[3] = {pi0[3]}，π[1] = 0。链 7 → 3 → 1 → 0 正好给出全部 border：{st(S0[:3])}、{st(S0[:1])}。", extra=0.3)
    S.play(FadeOut(t1), FadeOut(t2), *[s[i].to(fill=BG3) for i in range(1, len(S0) + 1)], dur=0.4)

    # ------------------------------------------------------------ 计算 π
    S.section("沿失配链计算 π")
    pa = Array(list(P), x=600, y=260, cw=86, ch=72, gap=10, size=36, chain="tt")
    pv = Array([""] * len(P), x=600, y=420, cw=86, ch=60, gap=10, size=30, index=False, fill=tint(B, 0.12))
    S.show(pa, pv, label(120, 420, "π", 34, B))
    S.say(f"对模式串 {st(P)} 从左到右算 π。π[1] = 0（单个字符没有真前缀）。")
    S.play(pv[1].to(text="0"), dur=0.4)
    S.say("算 π[i] 时，前 i 个字符的 border 去掉最后一个字符，就是前 i − 1 个字符的 border。所以只要在“前 i − 1 个字符的全部 border”里找。")
    S.note("前 i 个的 border = 前 i − 1 个的某个 border + 第 i 个字符", color=Y)
    S.say("候选从长到短就是失配链 j = π[i − 1], π[j], …；第一个满足“s[j + 1] = s[i]”的 j，给出 π[i] = j + 1。")
    S.note("j 从 π[i − 1] 起沿链跳，直到 s[j + 1] = s[i]，则 π[i] = j + 1", color=G)
    ip = pa.ptr(2, "i", O)
    jp = pa.ptr(1, "j+1", CY, side="above")
    S.play(FadeIn(ip), dur=0.3)
    for i in range(2, len(P) + 1):
        tr = trials[i]
        S.play(pa.move(ip, i), dur=0.35)
        for k, j in enumerate(tr):
            ok = P[j] == P[i - 1]
            last = k == len(tr) - 1
            if j + 1 <= len(P):
                S.play(*([FadeIn(jp)] if (i == 2 and k == 0) else []), pa.move(jp, j + 1),
                       pa[j + 1].to(stroke=G if ok else R, sw=3.5), pa[i].to(stroke=G if ok else R, sw=3.5),
                       dur=0.35)
            if i == len(P):
                if not ok and not last:
                    S.say(f"i = {i}：j = {j}，比较 s[{j + 1}] = {st(P[j])} 和 s[{i}] = {st(P[i - 1])}，不相等，失配。j 跳到 π[{j}] = {tr[k + 1]}——前 {j} 个字符的最长 border。")
                elif ok:
                    S.say(f"j = {j}：s[{j + 1}] = {st(P[j])} 等于 s[{i}]，匹配成功，π[{i}] = {j + 1}。")
            S.play(pa[j + 1].to(stroke=LINE, sw=2), pa[i].to(stroke=LINE, sw=2), dur=0.2)
        S.play(pv[i].to(text=str(pi[i]), fill=tint(B, 0.3)), dur=0.35)
        if i == 4:
            S.say(f"i = 4：j = {tr[0]} 时 s[{tr[0] + 1}] = {st(P[tr[0]])} 不等于 s[4] = {{t|c}}，跳到 j = 0 也不等，π[4] = 0。")
        if i == 7:
            S.say("i = 5、6、7：每次 s[j + 1] 都和 s[i] 相等，j 一路加一，π = 1, 2, 3。")
    S.play(FadeOut(ip), FadeOut(jp), dur=0.3)
    S.note("π = " + " ".join(str(v) for v in pi[1:]), color=B)

    # ------------------------------------------------------------ 复杂度
    S.section("为什么是 O(n)：j 的涨落", keep=[pa, pv])
    S.play(pa.to(y=190), pv.to(y=330), dur=0.6)
    ax = Axes(x=620, y=620, w=760, h=300, xr=(0, len(P) + 1), yr=(0, 4), xstep=1, ystep=1, xlabel="i",
              ylabel="j", grid=True)
    S.show(ax)
    S.say("里面有个 while 循环，会不会很慢？看 j 的变化：每处理一个字符，j 最多 +1；每跳一次失配链，j 至少 −1。")
    path = [(1, 0)]
    for i in range(2, len(P) + 1):
        tr = trials[i]
        for j in tr[1:]:
            path.append((i - 0.35, j))
        path.append((i, pi[i]))
    for a, b in zip(path, path[1:]):
        col = G if b[1] > a[1] else R if b[1] < a[1] else DIM
        S.play(FadeIn(ax.seg(a, b, color=col, w=3.5)), dur=0.18)
    S.say("j 始终 ≥ 0，所有的“+1”合起来不超过 n，所以所有的“下跳”合起来也不超过 n。整个计算 O(n)。")
    S.note("j 每步最多 +1、每跳至少 −1、且 j ≥ 0 → 总跳数 ≤ n，O(n)", color=Y)

    # ------------------------------------------------------------ 匹配
    S.section("匹配：同一条失配链")
    log, occ = kmp_match(TXT, P, pi)
    ta = Array(list(TXT), x=620, y=230, cw=72, ch=64, gap=8, size=32, chain="tt")
    S.show(ta, label(70, 230, "文本", 26, DIM, anchor="lm"))
    step = ta.cw + ta.gap
    pb = Array(list(P), x=ta.X(1) + (len(P) - 1) * step / 2, y=360, cw=72, ch=64, gap=8, size=32, chain="tt",
               index=False, fill=tint(CY, 0.2))
    S.show(pb, label(70, 360, "模式", 26, DIM, anchor="lm"))
    S.say(f"用 π 在文本里找 {st(P)}。j 表示“模式串的前 j 个字符已经和文本对上”。前 7 个字符一路对上。")
    S.play(*[ta[i].to(fill=tint(G, 0.35)) for i in range(1, 8)], dur=0.6)
    fail = next(e for e in log if e[1])
    i, jumps, jn = fail
    S.play(ta[i].to(stroke=R, sw=3.5), pb[8].to(stroke=R, sw=3.5), dur=0.4)
    S.say(f"文本第 {i} 个字符 {{t|c}} 和模式第 8 个字符 {{t|b}} 失配。朴素做法右移一格从头比；KMP 让 j 跳到 π[7] = {jumps[0]}。")
    shift = 7 - jumps[0]
    S.play(pb.to(x=pb.g("x", 0) + shift * step), ta[i].to(stroke=LINE, sw=2), pb[8].to(stroke=LINE, sw=2),
           *[ta[k].to(fill=BG3) for k in range(1, shift + 1)], dur=0.8)
    S.say(f"相当于模式串右移 7 − {jumps[0]} = {shift} 格：已经对上的 {st(P[:7])} 里，最长 border {st(P[:jumps[0]])} 还对着文本，不用重比。")
    S.note("失配：j ← π[j]，相当于右移 j − π[j] 格", color=Y)
    S.say(f"会不会漏掉移动 1～{shift - 1} 格的位置？如果移 d 格能成功，{st(P[:7])} 就有一个长度为 7 − d 的 border，比 π[7] 还长——矛盾。")
    S.note("不会漏：移得更少就意味着更长的 border", color=G)
    S.play(*[ta[k].to(fill=tint(G, 0.35)) for k in range(shift + 1, len(TXT) + 1)], dur=0.8)
    S.say(f"继续比下去，文本第 {occ[0]}～{occ[0] + len(P) - 1} 位与模式串完全匹配。文本里每个字符只让 j 加一次，匹配同样是 O(n + m)。", extra=0.3)
    S.note(f"出现位置：{occ[0]}；匹配 O(n + m)")

    # ------------------------------------------------------------ 手推题
    pq, trq = prefix_function(QZ)
    S.quiz(f"s = {{t|{QZ}}}。\n\n"
           "(1) 求 π[1]～π[7]。\n"
           "(2) 计算 π[6] 时，j 依次取了哪些值？\n"
           "(3) 写出 s 的全部 border。", think=20)
    S.say("(1) 逐个推：π = " + ", ".join(str(v) for v in pq[1:]) + "。")
    S.note("(1) π = " + " ".join(str(v) for v in pq[1:]), color=Y)
    tr6 = trq[6]
    S.say(f"(2) 从 j = π[5] = {tr6[0]} 开始：s[{tr6[0] + 1}] = {st(QZ[tr6[0]])} ≠ s[6] = {st(QZ[5])}，跳到 j = π[{tr6[0]}] = {tr6[1]}；"
          f"s[{tr6[1] + 1}] = {st(QZ[tr6[1]])} = s[6]，所以 π[6] = {pq[6]}。")
    S.note("(2) j：" + " → ".join(str(j) for j in tr6) + f"，π[6] = {pq[6]}", color=G)
    ch = [len(QZ)]
    while ch[-1]:
        ch.append(pq[ch[-1]])
    bq = borders(QZ)
    S.say(f"(3) 沿失配链：{' → '.join(str(c) for c in ch)}。全部 border 只有 " + "、".join(st(QZ[:k]) for k in bq) + "（和空串）。",
          extra=0.5)
    S.note("(3) border：" + "、".join(st(QZ[:k]) for k in bq))

    S.recap([
        "border：既是真前缀又是后缀；π[i] 是前 i 个字符的最长 border 长度。",
        "border 的 border 还是 border；全部 border 就是 π 的失配链 π[n] → π[π[n]] → … → 0。",
        "算 π[i]：沿 π[i − 1] 的失配链找第一个能接上 s[i] 的 j；匹配文本用的是同一条链。",
        "j 每步最多加一、每跳至少减一，所以总共 O(n)；失配时右移 j − π[j] 格，不会漏掉任何出现。",
    ], next_title="border 与周期")
