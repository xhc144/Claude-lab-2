"""第 37 集 border 与周期：最小周期与循环节"""

from episodes.common import *
from episodes.e36_kmp_border import prefix_function, borders, st

S1 = "abcabcab"
REP = "aabaabaab"
QZ = "aabaabaa"


def periods(s):
    n = len(s)
    return [p for p in range(1, n + 1) if all(s[i] == s[i + p] for i in range(n - p))]


def build(S):
    S.cover("abcabcab 看起来像 abc 不断重复。一个字符串最短的“重复单元”有多长？它和上一集的 border 是什么关系？",
            ["KMP 与 border（第 36 集）"])

    n = len(S1)
    ps = periods(S1)
    pi, _ = prefix_function(S1)
    assert ps[0] == n - pi[n]

    # ------------------------------------------------------------ 周期
    S.section("周期：错开 p 位还能对上")
    top = Array(list(S1), x=560, y=260, cw=80, ch=70, gap=8, size=34, chain="tt")
    S.show(top, label(110, 260, "s", 30, DIM, anchor="lm"))
    step = top.cw + top.gap
    bot = Array(list(S1), x=560, y=420, cw=80, ch=70, gap=8, size=34, chain="tt", index=False, fill=tint(CY, 0.18))
    S.show(bot, label(110, 420, "s 右移 p", 26, DIM, anchor="lm"))
    S.say("如果对所有能比较的位置都有 s[i] = s[i + p]，就说 p 是 s 的一个周期。直观地说：把 s 复制一份右移 p 位，重叠部分完全一样。")
    S.note("周期 p：s[i] = s[i + p] 对所有 1 ≤ i ≤ n − p 成立", color=Y)
    for p in (1, 2, 3):
        S.play(bot.to(x=560 + p * step), dur=0.6)
        ok = all(S1[i] == S1[i + p] for i in range(n - p))
        cols = []
        for i in range(n - p):
            good = S1[i] == S1[i + p]
            cols.append(top[i + p + 1].to(fill=tint(G if good else R, 0.45)))
            cols.append(bot[i + 1].to(fill=tint(G if good else R, 0.45)))
        S.play(*cols, dur=0.5)
        if p == 1:
            S.say(f"p = 1：第 1 位 {st(S1[0])} 对着第 2 位 {st(S1[1])}，不一样（红色），1 不是周期。")
        elif p == 2:
            S.say("p = 2：也有对不上的位置，2 不是周期。")
        else:
            S.say(f"p = 3：重叠的 {n - 3} 个位置全部相同，3 是周期。s 就是 {st(S1[:3])} 一直重复，最后一段没写完。")
        S.play(*[top[i].to(fill=BG3) for i in range(1, n + 1)], *[bot[i].to(fill=tint(CY, 0.18)) for i in range(1, n + 1)],
               dur=0.3)
    S.note(f"{st(S1)} 的周期：" + "、".join(str(p) for p in ps) + f"（n = {n} 总是周期）")

    # ------------------------------------------------------------ 周期与 border
    S.section("周期 ⇔ border", keep=[top, bot])
    p = ps[0]
    S.play(bot.to(x=560 + p * step), dur=0.5)
    S.say(f"再看 p = {p} 时的重叠部分：上面一行是 s 的后 {n - p} 个字符，下面一行是 s 的前 {n - p} 个字符。")
    b1 = top.span(p + 1, n, f"后缀 {st(S1[p:])}", O, side="above")
    S.play(FadeIn(b1), *[top[i].to(fill=tint(O, 0.35)) for i in range(p + 1, n + 1)],
           *[bot[i].to(fill=tint(O, 0.35)) for i in range(1, n - p + 1)], dur=0.6)
    bl = label(560 + p * step + (bot.lx(1) + bot.lx(n - p)) / 2, 480, f"前缀 {st(S1[:n - p])}", 24, O)
    S.show(bl)
    S.say(f"“错开 {p} 位重叠部分相同”就是“长度 {n - p} 的前缀等于长度 {n - p} 的后缀”，即 s 有一个长度为 {n - p} 的 border。")
    S.note("p 是周期 ⇔ s 有长度为 n − p 的 border", color=Y)
    S.say(f"所以周期和 border 一一对应：p ↔ n − p。最长的 border 对应最短的周期：最小周期 = n − π[n] = {n} − {pi[n]} = {p}。")
    S.note("最小周期 = n − π[n]；全部周期 = n − (失配链上的每个 border)", color=G)
    bs = borders(S1)
    S.say("沿失配链列出全部 border：" + "、".join(f"{k}" for k in bs) + "，对应的周期就是 "
          + "、".join(str(n - k) for k in bs) + f"，再加上 n = {n} 本身。")
    S.play(FadeOut(b1), FadeOut(bl), *[top[i].to(fill=BG3) for i in range(1, n + 1)],
           *[bot[i].to(fill=tint(CY, 0.18)) for i in range(1, n + 1)], dur=0.4)

    # ------------------------------------------------------------ 周期引理
    S.section("两个周期的差还是周期")
    S.say("什么时候 s 能写成某个串的整数次重复（循环节）？先证明一个工具：如果 p < q 都是周期，并且 p + q ≤ n，那么 q − p 也是周期。")
    S.note("引理：p < q 是周期，p + q ≤ n ⇒ q − p 是周期", color=Y)
    pa = Array([""] * 10, x=600, y=330, cw=72, ch=60, gap=8, size=26)
    S.show(pa, label(600, 180, "要证：s[i] = s[i + (q − p)]，i 从 1 到 n − (q − p)", 26, FG))
    p_, q_ = 3, 5
    S.say(f"情形一：i + q ≤ n。先往右跳 q：s[i] = s[i + q]；再往左跳 p：s[i + q] = s[i + q − p]。合起来就是 s[i] = s[i + q − p]。")
    i0 = 2
    a1 = Line(pa.X(i0), 292, pa.X(i0 + q_), 292, color=CY, w=3, head=12, bend=-0.25)
    a2 = Line(pa.X(i0 + q_), 292, pa.X(i0 + q_ - p_), 292, color=O, w=3, head=12, bend=0.25)
    for a in (a1, a2):
        a.tr["op"].base = 0
    S.add(a1, a2)
    S.play(pa[i0].to(fill=tint(Y, 0.5)), FadeIn(a1), dur=0.5)
    S.play(FadeIn(a2), pa[i0 + q_ - p_].to(fill=tint(Y, 0.5)), dur=0.5)
    S.wait(0.8)
    S.say("情形二：i + q > n，往右跳不了 q。但这时 i > n − q ≥ p，可以先往左跳 p：s[i] = s[i − p]；再往右跳 q：s[i − p] = s[i − p + q]。")
    i1 = 8
    b1_ = Line(pa.X(i1), 400, pa.X(i1 - p_), 400, color=O, w=3, head=12, bend=-0.25)
    b2_ = Line(pa.X(i1 - p_), 400, pa.X(i1 - p_ + q_), 400, color=CY, w=3, head=12, bend=0.25)
    for a in (b1_, b2_):
        a.tr["op"].base = 0
    S.add(b1_, b2_)
    S.play(pa[i1].to(fill=tint(G, 0.5)), FadeIn(b1_), dur=0.5)
    S.play(FadeIn(b2_), pa[i1 - p_ + q_].to(fill=tint(G, 0.5)), dur=0.5)
    S.say("两种情形都得到 s[i] = s[i + (q − p)]。条件 p + q ≤ n 保证了两种情形总有一种能跳。")
    S.say("像辗转相减一样反复用这个引理，就得到：gcd(p, q) 也是周期（弱周期引理）。", extra=0.3)
    S.note("反复相减 ⇒ gcd(p, q) 也是周期", color=G)

    # ------------------------------------------------------------ 循环节
    S.section("什么时候是整数次重复")
    S.say("设 s = t 重复 k 次（k ≥ 2），|t| = q。那么 q 是周期且 q 整除 n。最小周期 p ≤ q，而 q ≤ n/2，所以 p + q ≤ n。")
    S.say("由引理，gcd(p, q) 也是周期；p 是最小的，只能 gcd(p, q) = p，即 p 整除 q，从而 p 整除 n。")
    S.note("s 是某个串的 k 次重复（k ≥ 2）⇔ p = n − π[n] < n 且 p | n", color=Y)
    S.say("所以判断只看最小周期：p 整除 n（且 p < n）就是整数次重复，循环节是前 p 个字符；否则不是。")
    pr, _ = prefix_function(REP)
    rows = []
    for i in range(1, len(REP) + 1):
        p_i = i - pr[i]
        good = pr[i] > 0 and i % p_i == 0
        rows.append([i, st(REP[:i]), pr[i], p_i, f"{{g|{i // p_i} 次}}" if good else "{f|否}"])
    tb = Grid(len(rows), 5, x=600, y=480, cw=150, ch=40, gap=3, size=22,
              vals=rows, clab=["i", "前缀", "π[i]", "i − π[i]", "整数次重复？"])
    S.show(tb, dur=0.8)
    S.say(f"对 {st(REP)} 的每个前缀判断：i = 2、6、9 时 i − π[i] 整除 i，分别是 {st('a')} 重复 2 次、{st('aab')} 重复 2 次、{st('aab')} 重复 3 次。")
    hl = [tb.frame(i - 1, 0, i - 1, 4, G) for i in (2, 6, 9)]
    S.play(*[FadeIn(h) for h in hl], dur=0.5)
    S.note("每个前缀 i：i − π[i] 整除 i 且 π[i] > 0 ⇒ 重复 i/(i − π[i]) 次", color=G)

    # ------------------------------------------------------------ 手推题
    pq, _ = prefix_function(QZ)
    m = len(QZ)
    pm = m - pq[m]
    add = 0 if (m % pm == 0 and pm < m) else pm - m % pm
    S.quiz(f"s = {{t|{QZ}}}（长度 {m}）。\n\n"
           "(1) 写出 s 的全部周期。\n"
           "(2) s 是不是某个串重复至少两次？\n"
           "(3) 至少在末尾补几个字符，才能变成某个串重复至少两次？补成什么？", think=20)
    bq = borders(QZ)
    S.say(f"(1) π[{m}] = {pq[m]}，失配链给出全部 border：" + "、".join(str(k) for k in bq)
          + "。周期是 " + "、".join(str(m - k) for k in bq) + f" 和 {m}。")
    S.note("(1) 周期：" + "、".join(str(m - k) for k in bq) + f"、{m}", color=Y)
    S.say(f"(2) 最小周期 p = {pm}，{m} 不是 {pm} 的倍数，所以不是整数次重复。")
    S.note(f"(2) p = {pm} 不整除 {m}：不是", color=R)
    full = (QZ[:pm] * ((m + add) // pm))
    S.say(f"(3) 补到 p 的倍数最省：补 {add} 个字符，变成 {st(full)} = {st(QZ[:pm])} 重复 {(m + add) // pm} 次。")
    pq_all = periods(QZ)
    S.say(f"为什么不会更少？补完后的串以 s 开头，它的最小周期 p′ 也必须是 s 的周期（{'、'.join(map(str, pq_all))}，或者比 {m} 大），"
          f"长度又至少是 2p′。逐个比较，p′ = {pm} 时补到 {m + add} 最短。", extra=0.5)
    S.note(f"(3) 补 {add} 个 → {st(full)}", color=G)

    S.recap([
        "p 是周期 ⇔ 错开 p 位重叠部分相同 ⇔ s 有长度 n − p 的 border。",
        "最小周期 = n − π[n]；全部周期由失配链上的全部 border 给出。",
        "两个周期 p + q ≤ n 时，q − p 和 gcd(p, q) 也是周期（弱周期引理）。",
        "s 是整数次重复 ⇔ 最小周期 p < n 且 p 整除 n；前缀同理，用 i − π[i] 判断。",
    ], next_title="Manacher")
