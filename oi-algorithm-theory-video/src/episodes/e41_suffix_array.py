"""第 41 集 后缀数组（上）：倍增排序"""

from episodes.common import *
from episodes.e36_kmp_border import st

S0 = "banana"
QZ = "abaab"


def suffix_array(s):
    """倍增：返回 sa（1 起）、rk，以及每一轮 (长度, 排名, 二元组)。"""
    n = len(s)
    chars = sorted(set(s))
    rk = [0] + [chars.index(c) + 1 for c in s] + [0] * (n + 1)      # rk[n+1..] = 0 表示空
    rounds = [(1, rk[1:n + 1], None)]
    k = 1
    while True:
        pairs = [(rk[i], rk[i + k] if i + k <= n else 0) for i in range(1, n + 1)]
        uniq = sorted(set(pairs))
        new = [uniq.index(p) + 1 for p in pairs]
        rounds.append((2 * k, new, pairs))
        rk = [0] + new + [0] * (n + 1)
        k *= 2
        if len(uniq) == n:
            break
    sa = sorted(range(1, n + 1), key=lambda i: rk[i])
    return sa, rk[1:n + 1], rounds


def build(S):
    S.cover("把字符串的所有后缀按字典序排好，很多字符串问题就变成了“排序后相邻”的问题。直接比较两个后缀要 O(n)，有没有更快的排法？",
            ["基数排序 / 计数排序", "倍增思想"])

    n = len(S0)
    sa, rk, rounds = suffix_array(S0)
    assert sa == sorted(range(1, n + 1), key=lambda i: S0[i - 1:])

    # ------------------------------------------------------------ 后缀数组
    S.section("后缀数组与排名")
    sarr = Array(list(S0), x=640, y=190, cw=70, ch=60, gap=8, size=30, chain="tt")
    S.show(sarr, label(330, 190, "s", 30, DIM, anchor="lm"))
    rows = []
    for i in range(1, n + 1):
        y = 300 + 62 * (i - 1)
        idx = label(540, y, f"{i}", 26, DIM)
        tx = label(585, y, st(S0[i - 1:]), 30, FG, anchor="lm")
        rows.append(Group(0, 0))
        rows[-1].add(idx, tx)
    S.show(*rows, dur=0.6, lag=0.08)
    S.say(f"{st(S0)} 的 {n} 个后缀，按起点编号 1～{n}。后缀 i 就是从第 i 个字符开始到结尾的那一段。")
    S.say("把它们按字典序排好：排第 1 的是 " + st(S0[sa[0] - 1:]) + "，最后一个是 " + st(S0[sa[-1] - 1:]) + "。")
    order = {i: r for r, i in enumerate(sa)}
    S.play(*[rows[i - 1].to(y=62 * (order[i] - (i - 1))) for i in range(1, n + 1)], dur=1.2)
    rk_lab = [label(850, 300 + 62 * r, f"rk = {rk[i - 1]}", 26, CY, anchor="lm") for r, i in enumerate(sa)]
    sa_lab = [label(480, 300 + 62 * r, f"sa[{r + 1}] = {i}", 26, O, anchor="rm") for r, i in enumerate(sa)]
    S.show(*sa_lab, dur=0.5, lag=0.05)
    S.say("sa[r] = 排第 r 名的后缀的起点；rk[i] = 后缀 i 的名次。两个数组互为反函数：sa[rk[i]] = i。")
    S.note("sa[r]：第 r 小的后缀从哪开始；rk[i]：后缀 i 排第几", color=Y)
    S.show(*rk_lab, dur=0.5, lag=0.05)
    S.note("sa = " + " ".join(map(str, sa)) + "；rk = " + " ".join(map(str, rk)))
    S.say("直接用比较排序：O(n log n) 次比较，每次比较两个后缀最坏 O(n)，总共 O(n² log n)。慢在每次比较都从头比字符。")
    S.note("直接排序：O(n² log n)", color=R)

    # ------------------------------------------------------------ 倍增
    S.section("倍增：先按前 1、2、4… 个字符排")
    S.say("想法：先只按每个后缀的前 1 个字符排名，再按前 2 个、前 4 个……长度翻倍。长度超过 n 时，排名就是最终结果。")
    S.note("rkₖ(i)：后缀 i 的前 2ᵏ 个字符的排名（不够长就到结尾为止）", color=Y)
    cols = ["i", "后缀"]
    vals = [[str(i), st(S0[i - 1:])] for i in range(1, n + 1)]
    for L, r_, pairs in rounds:
        if pairs is not None:
            cols.append("二元组")
        cols.append(f"前 {L} 个")
    cw = 118
    ncol = len(cols)
    tb = Grid(n, ncol, x=640, y=480, cw=cw, ch=52, gap=4, size=22, clab=cols,
              vals=[vals[i] + [""] * (ncol - 2) for i in range(n)])
    for i in range(n):
        tb[i, 1].label.tr["size"].base = 20
    S.show(tb)
    col = 2
    L, r0, _ = rounds[0]
    S.play(*[tb[i, col].to(text=str(r0[i]), fill=tint(B, 0.25)) for i in range(n)], dur=0.6)
    S.say("第一轮：只看首字母。" + "、".join(f"{st(c)} 排 {k + 1}" for k, c in enumerate(sorted(set(S0)))) + "，相同字母排名相同。")
    col += 1
    for t_, (L, r_, pairs) in enumerate(rounds[1:]):
        half = L // 2
        S.play(*[tb[i, col].to(text=f"({p[0]}, {p[1]})", fill=tint(O, 0.18)) for i, p in enumerate(pairs)], dur=0.6)
        if t_ == 0:
            S.say(f"关键一步：前 {L} 个字符 = 前 {half} 个 + 从 i + {half} 开始的前 {half} 个。两段的排名上一轮都已经知道了！")
            S.note("前 2ᵏ⁺¹ 个字符的排名 = 二元组 (rkₖ(i), rkₖ(i + 2ᵏ)) 的排名", color=G)
            S.say(f"所以给每个后缀配一个二元组 (rk(i), rk(i + {half}))，按二元组排序，就得到前 {L} 个字符的排名。超出结尾的部分记作 0（空串最小）。")
        S.play(*[tb[i, col + 1].to(text=str(r_[i]), fill=tint(B, 0.25)) for i in range(n)], dur=0.6)
        if t_ == 0:
            S.say(f"例如后缀 2 和 4 的二元组都是 {pairs[1]}：前 {L} 个字符都是 {st(S0[1:1 + L])}，排名相同；它们要等下一轮才分得开。")
        else:
            S.say(f"前 {L} 个字符：二元组各不相同，排名 1～{n} 全部分开。排名不再有并列，就可以停了——这就是最终的 rk。")
        col += 2
    S.note("排名各不相同就提前结束；最多 ⌈log₂ n⌉ 轮", color=Y)

    # ------------------------------------------------------------ 基数排序
    S.section("每一轮为什么只要 O(n)")
    S.say("每轮按二元组排序。二元组的两个分量都是 0～n 的整数，用基数排序：先按第二关键字排，再按第一关键字做稳定的计数排序。")
    S.note("二元组分量都在 [0, n]：基数排序，每轮 O(n)", color=Y)
    demo = [(rounds[1][1][i], rounds[1][1][i + 2] if i + 2 < n else 0) for i in range(n)]
    pa = Array([f"({a},{b})" for a, b in demo], x=640, y=300, cw=120, ch=56, gap=8, size=24, idx_labels=[str(i + 1) for i in range(n)])
    S.show(pa, label(640, 220, "第三轮的二元组（下面是起点 i）", 24, DIM))
    by2 = sorted(range(n), key=lambda i: demo[i][1])
    pb = Array([f"({demo[i][0]},{demo[i][1]})" for i in by2], x=640, y=470, cw=120, ch=56, gap=8, size=24,
               idx_labels=[str(i + 1) for i in by2], fill=tint(O, 0.18))
    S.show(pb, label(640, 395, "① 按第二关键字排（稳定）", 24, O))
    by1 = sorted(by2, key=lambda i: demo[i][0])
    pc = Array([f"({demo[i][0]},{demo[i][1]})" for i in by1], x=640, y=640, cw=120, ch=56, gap=8, size=24,
               idx_labels=[str(i + 1) for i in by1], fill=tint(G, 0.2))
    S.show(pc, label(640, 565, "② 再按第一关键字稳定排序 → 完全排好", 24, G))
    S.say("第二步是稳定的：第一关键字相同的，保持第一步排出的第二关键字顺序。于是两步之后按 (第一, 第二) 字典序排好。")
    S.say("第一步其实不用排：第二关键字的顺序可以直接从上一轮的 sa 读出来——先放 i + 2ᵏ 超出结尾的那些 i，再按上一轮 sa 的顺序放其余的。")
    S.note("第二关键字的顺序可由上一轮 sa 直接得到", color=G)
    S.say("每轮 O(n)，最多 log n 轮：总 O(n log n)。还有 O(n) 的 SA-IS、DC3，但倍增在竞赛里最常用。", extra=0.5)
    S.note("总 O(n log n)")

    # ------------------------------------------------------------ 手推题
    qsa, qrk, qr = suffix_array(QZ)
    assert qsa == sorted(range(1, len(QZ) + 1), key=lambda i: QZ[i - 1:])
    S.quiz(f"s = {{t|{QZ}}}。\n\n"
           "(1) 写出每一轮（前 1、2、4 个字符）的排名。\n"
           "(2) 写出 sa 和 rk。", think=20)
    for L, r_, pairs in qr:
        if pairs is None:
            S.say(f"(1) 前 1 个：按字母，排名 " + " ".join(map(str, r_)) + "。")
        else:
            S.say(f"前 {L} 个：二元组 " + " ".join(f"({a},{b})" for a, b in pairs) + "，排名 " + " ".join(map(str, r_)) + "。")
        S.note(f"前 {L} 个：" + " ".join(map(str, r_)), color=Y)
    S.say("(2) sa = " + " ".join(map(str, qsa)) + "，rk = " + " ".join(map(str, qrk)) + "。按字典序："
          + " < ".join(st(QZ[i - 1:]) for i in qsa) + "。", extra=0.5)
    S.note("(2) sa = " + " ".join(map(str, qsa)) + "；rk = " + " ".join(map(str, qrk)), color=G)

    S.recap([
        "后缀数组 sa 按字典序列出所有后缀的起点；rk 是它的反函数。",
        "倍增：前 2ᵏ⁺¹ 个字符的排名 = 二元组 (rkₖ(i), rkₖ(i + 2ᵏ)) 的排名，长度翻倍、轮数 O(log n)。",
        "二元组分量是 0～n 的整数，用两遍稳定的计数排序（基数排序），每轮 O(n)，总 O(n log n)。",
        "排名全部不同就可以提前结束。",
    ], next_title="后缀数组（下）：height 与最长公共前缀")
