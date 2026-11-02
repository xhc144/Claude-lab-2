"""第 11 集 数位 DP：贴着上界走"""

from episodes.common import *

NUM = 352


def windy(x):
    s = str(x)
    return all(abs(int(a) - int(b)) >= 2 for a, b in zip(s, s[1:]))


def gtable(maxrem):
    g = [[1] * 10]
    for rem in range(1, maxrem + 1):
        g.append([sum(g[rem - 1][e] for e in range(10) if abs(e - d) >= 2) for d in range(10)])
    return g


def blocks(n):
    """把 [1, n] 中位数等于 n 的数分成“前缀固定 + 后面自由”的块。返回 (前缀, 自由位数, 个数)。"""
    s = list(map(int, str(n)))
    L = len(s)
    g = gtable(L)
    out = []
    for pos in range(L):
        prefix = s[:pos]
        if pos >= 2 and abs(prefix[-1] - prefix[-2]) < 2:
            break
        lo = 1 if pos == 0 else 0
        for d in range(lo, s[pos]):
            if pos > 0 and abs(d - prefix[-1]) < 2:
                out.append((prefix + [d], L - pos - 1, 0))
                continue
            out.append((prefix + [d], L - pos - 1, g[L - pos - 1][d]))
    else:
        pass
    if windy(n):
        out.append((s, 0, 1))
    return out, g


def shorter(n):
    """位数比 n 少的 windy 数个数。"""
    L = len(str(n))
    g = gtable(L)
    return sum(g[k - 1][d] for k in range(1, L) for d in range(1, 10))


def build(S):
    S.cover("相邻两位数字之差至少为 2 的正整数叫 windy 数。[L, R] 里有多少个？R 可以到 2×10⁹。",
            ["记忆化搜索", "前缀和思想：区间 = 两个前缀相减"])

    # ------------------------------------------------------------ 问题
    S.section("问题：windy 数")
    S.say("windy 数：没有前导零，并且相邻两位数字之差的绝对值至少是 2。比如 135、352 是，121、88 不是。")
    S.note("windy 数：相邻两位之差 ≥ 2（无前导零）")
    exs = [("135", True), ("352", True), ("121", False), ("88", False)]
    cards = []
    for i, (t, okk) in enumerate(exs):
        c = Cell(280 + i * 230, 360, 180, 90, t, 40, fill=tint(G if okk else R, 0.3), stroke=G if okk else R, chain="mono")
        cards.append(c)
    S.show(*cards, lag=0.1)
    S.say("询问 [L, R] 里有多少个，R 可以到 2×10⁹，逐个检查太慢。")
    S.note("先转化：答案 = count(R) − count(L − 1)", color=Y)
    S.say("第一步转化：只要会算 count(N) = [1, N] 里的个数，区间答案就是 count(R) − count(L−1)。下面以 N = 352 为例。")
    S.play(FadeOut(*cards), dur=0.3)

    # ------------------------------------------------------------ 分块
    S.section("把 ≤ N 的数分成几大块")
    bl, g = blocks(NUM)
    digits = Array(list(str(NUM)), x=640, y=200, cw=90, ch=80, gap=10, size=40, index=False, chain="mono")
    lab = label(640, 130, "上界 N", 24, DIM)
    S.show(digits, lab)
    S.say("从最高位开始，一位一位地决定。三位数里：第一位如果小于 3（取 1 或 2），后面两位就{y|随便取}，不可能超过 352。")
    S.note("某一位比 N 小了 → 后面所有位都自由")
    S.say("第一位如果等于 3，就还“贴着上界”：第二位只能取 0~5。第二位小于 5 时，最后一位随便；等于 5 时，最后一位只能取 0~2。")
    S.note("一直和 N 相等 → “贴着上界”，下一位受限", color=Y)
    rows = []
    y0 = 330
    for k, (pre, rem, cnt) in enumerate(bl):
        txt = "".join(map(str, pre)) + "x" * rem
        col = CY if rem == 2 else (O if rem == 1 else G)
        rows.append((txt, cnt, col))
    # 用三列显示：自由位数 2 / 1 / 0
    groups = {2: [], 1: [], 0: []}
    for (pre, rem, cnt) in bl:
        groups[rem].append(("".join(map(str, pre)) + "x" * rem, cnt))
    titles = {2: "第 1 位就小于 3", 1: "第 1 位 = 3，第 2 位小于 5", 0: "前两位 = 35，第 3 位 ≤ 2"}
    colx = {2: 260, 1: 640, 0: 1040}
    allc = []
    for rem in (2, 1, 0):
        t = label(colx[rem], 300, titles[rem], 24, CY if rem == 2 else O if rem == 1 else G)
        cs = []
        for i, (txt, cnt) in enumerate(groups[rem]):
            c = Cell(colx[rem], 360 + i * 66, 230, 56, f"{txt}：{cnt} 个", 26, fill=BG3,
                     stroke=CY if rem == 2 else O if rem == 1 else G, chain="sans")
            cs.append(c)
        S.show(t, *cs, lag=0.05)
        allc += [t] + cs
    S.say("每一块都是“固定的前缀 + 自由的后缀”。前缀本身要满足 windy 条件（比如 32x、33x、34x 的前缀已经不合法，整块是 0）。")
    S.note("≤ N 的三位数 = 若干个“固定前缀 + 自由后缀”的块")
    S.say("块的个数很少：每一位最多 10 块，所以一共 O(位数 × 10) 块。问题变成：每一块里有多少个 windy 数？")
    S.play(FadeOut(digits, lab), dur=0.3)

    # ------------------------------------------------------------ 记忆化
    S.section("自由的后缀：可以记忆化")
    S.play(FadeOut(*allc), dur=0.3)
    S.say("一个自由块里的个数，只取决于两件事：后面还有几位自由（rem），以及前缀的最后一位 d（下一位要和它差 ≥ 2）。")
    S.note("{y|g[rem][d]}：前一位是 d，后面 rem 位随便填，有多少种填法", color=Y)
    S.note("g[0][d] = 1；g[rem][d] = Σ_{|e−d|≥2} g[rem−1][e]")
    gt = Grid(3, 10, x=640, y=470, cw=96, ch=64, gap=4, size=26, rlab=["rem=0", "rem=1", "rem=2"],
              clab=[f"d={d}" for d in range(10)])
    S.show(gt)
    for rem in range(3):
        S.play(*[gt[(rem, d)].to(text=str(g[rem][d])) for d in range(10)], dur=0.6, lag=0.04)
        if rem == 1:
            S.say("例：g[1][5]：前一位是 5，后一位只能取 0、1、2、3、7、8、9，共 7 种。")
            S.play(gt[(1, 5)].to(stroke=Y, sw=4), *[gt[(0, e)].to(stroke=CY, sw=3) for e in range(10) if abs(e - 5) >= 2],
                   dur=0.5)
            S.wait(0.6)
            S.play(gt[(1, 5)].to(stroke=LINE, sw=2), *[gt[(0, e)].to(stroke=LINE, sw=2) for e in range(10)], dur=0.3)
    S.say("块 1xx 的个数是 g[2][1]，2xx 是 g[2][2]，30x 是 g[1][0]……不同的块只要 (rem, d) 相同，就共用同一个值。")
    S.play(gt[(2, 1)].to(fill=tint(CY, 0.4)), gt[(2, 2)].to(fill=tint(CY, 0.4)), gt[(1, 0)].to(fill=tint(O, 0.4)), dur=0.6)
    S.say("而“贴着上界”的状态每一位只有一个（前缀和 N 完全相同），它不需要记忆化，也不能和自由的状态混在一起——它的下一位是受限的。")
    S.note("贴着上界的状态每位只有一个，单独处理；自由状态记忆化", color=G)
    S.say("这就是数位 DP 的状态：(位置, 前一位, 是否贴着上界)。“是否贴着上界”决定下一位能取到几。")
    S.note("状态：(pos, 前一位, 是否贴上界)", color=Y)

    # ------------------------------------------------------------ 前导零
    S.section("前导零")
    S.say("位数比 N 少的数怎么办？常见做法是补前导零：把 52 看成 052，统一成三位。")
    ex = Array(list("013"), x=480, y=360, cw=90, ch=80, gap=10, size=40, index=False, chain="mono")
    S.show(ex)
    S.say("但对 windy 数这样做会出错：13 是 windy 数，写成 013 后，0 和 1 只差 1，会被错误地排除。")
    S.play(ex.cells[0].to(fill=tint(R, 0.4)), ex.cells[1].to(fill=tint(R, 0.4)), dur=0.5)
    S.note("补前导零后，0 不能参与“相邻差 ≥ 2”的判断", color=R)
    S.say("所以要再加一个标记：数字是否已经“开始”。没开始时填 0 表示继续不开始，不受任何限制；第一个非零数字才算开始。")
    S.note("加标记 started：前导零不受限制", color=G)
    sh = shorter(NUM)
    tot3 = sum(c for _, _, c in bl)
    S.say(f"对 N = 352：一位和两位的 windy 数一共 {sh} 个，三位的各块加起来 {tot3} 个，count(352) = {sh + tot3}。暴力枚举验证也是 {sum(windy(i) for i in range(1, NUM + 1))}。")
    S.note(f"count(352) = {sh} + {tot3} = {sh + tot3}", color=Y)
    S.say("复杂度：位数 × 10 种前一位 × 2 × 2 个标记 × 10 种下一位，R = 2×10⁹ 时只有几千次运算。")

    # ------------------------------------------------------------ 手推题
    S.quiz("统计 [1, N] 中“不含数字 4，也不含连续的 62”的数的个数。\n\n"
           "(1) 状态里要记住前缀的什么信息？\n"
           "(2) 这道题需要“是否开始”的标记吗？\n"
           "(3) 手算 N = 100 的答案。", think=20)
    S.say("(1) 下一位能不能填 2，取决于前一位是不是 6；4 是否出现，在填的时候直接禁止。所以只需记“前一位是不是 6”，再加上“是否贴上界”。")
    S.note("(1) 状态：(pos, 前一位是否为 6, 是否贴上界)", color=Y)
    S.say("(2) 不需要。前导零 0 既不是 4，也不是 6，不会误伤任何数：62 写成 062 仍然含 62，该排除的照样排除。")
    S.note("(2) 前导零不影响判断 → 不需要", color=G)
    S.say("(3) 把 0~99 看成两位数 ab：a 有 9 种（除了 4），b 有 9 种，再去掉 62 这一个，共 80 个；去掉 00，再加上 100，答案 80。")
    S.note("(3) 9 × 9 − 1 − 1 + 1 = 80", color=Y)
    S.say("是否需要前导零标记，看的是“补上的 0 会不会改变判断”——这又是在问状态是否充分。", extra=0.5)

    S.recap([
        "区间计数先转化为前缀：count(R) − count(L−1)。",
        "≤ N 的数可以分成 O(位数 × 10) 块：固定前缀（某一位开始比 N 小）+ 自由后缀。",
        "自由后缀的方案数只和（剩余位数, 前一位）有关，可以记忆化；贴着上界的状态每位只有一个，单独处理。",
        "补前导零时要检查：补上的 0 会不会参与判断，会的话加一个“是否开始”的标记。",
    ], next_title="单调队列优化 DP：过时又更差的候选永远没用")
