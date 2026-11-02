"""第 57 集 FFT（下）与 NTT：逆变换与模意义下的单位根"""

import math

from episodes.common import *
from episodes.e56_fft import cfmt


def dft(a, w):
    n = len(a)
    return [sum(a[k] * w ** (j * k) for k in range(n)) for j in range(n)]


def ntt(a, w, p):
    n = len(a)
    return [sum(a[k] * pow(w, j * k, p) for k in range(n)) % p for j in range(n)]


def build(S):
    S.cover("上一集把系数变成了点值。乘完以后还要变回系数——逆变换难道要另写一个算法？另外，浮点数的 FFT 会有精度误差，题目要求取模时，能不能在整数里做？",
            ["FFT（上）（第 56 集）", "扩展欧几里得与逆元（第 43 集）"])

    # ------------------------------------------------------------ 矩阵
    S.section("求值就是乘一个矩阵")
    S.say("在 n 个单位根上求值：yⱼ = Σₖ aₖ ωʲᵏ。写成矩阵就是 y = V a，V 的第 j 行第 k 列是 ωʲᵏ。")
    S.note("DFT：y = V a，V[j][k] = ω^{jk}", color=Y)
    pw = {0: "1", 1: "i", 2: "−1", 3: "−i"}
    V = [[pw[(j * k) % 4] for k in range(4)] for j in range(4)]
    mv = Matrix(V, x=520, y=450, cw=90, ch=64, size=30, color=CY)
    S.show(label(300, 450, "V =", 34, FG, anchor="rm"), mv, label(520, 280, "n = 4，ω = i", 28, DIM))
    S.say("n = 4 时 ω = i，矩阵里都是 i 的幂。逆变换就是求 V 的逆矩阵。")
    S.say("神奇之处：V 的逆几乎就是它自己——把 ω 换成 ω⁻¹，再整体除以 n。")
    S.note("V⁻¹ = (1/n) · V(ω⁻¹)", color=G)

    # ------------------------------------------------------------ 为什么
    S.section("为什么逆变换只是换成 ω⁻¹")
    S.say("看 V(ω) 和 V(ω⁻¹) 相乘的第 (j, l) 个元素：Σₖ ωʲᵏ · ω⁻ᵏˡ = Σₖ (ω^{j−l})ᵏ。")
    S.note("Σₖ (ω^{j−l})ᵏ：j = l 时为 n，否则为 0", color=Y)
    cx, cy, Rr = 420, 500, 200
    S.show(Circle(cx, cy, Rr, fill=(0, 0, 0, 0), stroke=LINE2, sw=2))
    n = 8
    arrows = []
    for k in range(n):
        a = 2 * math.pi * k / n
        ar = Line(cx, cy, cx + Rr * math.cos(a), cy - Rr * math.sin(a), color=O, w=3, head=12)
        ar.tr["op"].base = 0
        arrows.append(ar)
        S.add(ar)
    S.play(*[FadeIn(a) for a in arrows], dur=0.8, lag=0.05)
    S.say("j = l 时每一项都是 1，和为 n。j ≠ l 时，这是 n 个均匀分布在单位圆上的向量（图里 n = 8），首尾相接回到原点，和为 0。")
    S.say("严格地：这是公比 q = ω^{j−l} ≠ 1 的等比数列，和 = (qⁿ − 1)/(q − 1)，而 qⁿ = 1，所以为 0。")
    S.note("等比求和：(qⁿ − 1)/(q − 1) = 0（因为 qⁿ = 1）", color=G)
    S.say("所以 V(ω) · V(ω⁻¹) = n · I。逆变换和正变换是同一个 FFT 程序，只是单位根换成 ω⁻¹，最后每个数除以 n。", extra=0.3)

    # ------------------------------------------------------------ 完整例子
    S.section("完整的乘法：(1 + 2x)(3 + x)")
    A, Bc = [1, 2, 0, 0], [3, 1, 0, 0]
    ya, yb = dft(A, 1j), dft(Bc, 1j)
    yc = [x * y for x, y in zip(ya, yb)]
    c = [round((v / 4).real) for v in dft(yc, -1j)]
    assert c == [3, 7, 2, 0]
    rows = [["a（补到 4 项）"] + [str(v) for v in A],
            ["FFT(a)"] + [cfmt(v) for v in ya],
            ["b"] + [str(v) for v in Bc],
            ["FFT(b)"] + [cfmt(v) for v in yb],
            ["逐点相乘"] + [cfmt(v) for v in yc],
            ["逆 FFT ÷ 4"] + [str(v) for v in c]]
    tb = Grid(6, 5, x=640, y=470, cw=175, ch=54, gap=4, size=24, vals=rows,
              clab=["", "第 0 项 / ω⁰", "第 1 项 / ω¹", "第 2 项 / ω²", "第 3 项 / ω³"])
    for r in range(6):
        tb[r, 0].label.tr["color"].base = DIM
    S.show(tb)
    S.say("乘积是 2 次多项式，要 3 个点，补到 2 的幂 n = 4。两个多项式各做一次 FFT，逐点相乘，再做一次逆 FFT。")
    S.play(*[tb[5, k].to(fill=tint(G, 0.4)) for k in range(1, 5)], dur=0.5)
    S.say(f"结果 3 + 7x + 2x²，正是 (1 + 2x)(3 + x)。三次 FFT 加一次逐点乘：O(n log n)。")
    S.note("乘法：两次 FFT + 逐点乘 + 一次逆 FFT，O(n log n)", color=G)
    S.say("实际计算用浮点数，cos、sin 有舍入误差。系数很大或项数很多时，误差可能让四舍五入出错。题目要取模时，能不能直接在模 p 的整数里做？", extra=0.3)
    S.note("浮点 FFT：有精度误差", color=R)

    # ------------------------------------------------------------ 模意义下的单位根
    S.section("在模 p 下找“单位根”")
    S.say("FFT 用到单位根的三条性质：ωⁿ = 1；ω⁰…ωⁿ⁻¹ 互不相同；ω^{n/2} = −1（平方后减半）。模素数 p 时，能找到满足这些性质的整数吗？")
    S.note("需要：ωⁿ ≡ 1，前 n 个幂互不相同，ω^{n/2} ≡ −1", color=Y)
    p, g, nn = 17, 3, 8
    w = pow(g, (p - 1) // nn, p)
    S.say(f"例：p = {p}，3 是它的原根（3 的幂能取遍 1～16）。取 ω = 3^{{(p−1)/n}}。n = {nn} 时 ω = 3² = {w}。")
    powers = [pow(w, k, p) for k in range(1, nn + 1)]
    arr = Array(powers, x=640, y=420, cw=96, ch=62, gap=10, size=30, idx_labels=[f"ω^{k}" for k in range(1, nn + 1)],
                fill=tint(P, 0.25))
    S.show(arr, label(640, 330, f"ω = {w} 的各次幂（模 {p}）", 26, P))
    S.play(arr.cells[nn // 2 - 1].to(fill=tint(Y, 0.45), stroke=Y, sw=3), arr.cells[nn - 1].to(fill=tint(G, 0.45), stroke=G, sw=3),
           dur=0.5)
    assert powers[nn // 2 - 1] == p - 1 and powers[-1] == 1 and len(set(powers)) == nn
    S.say(f"{nn} 个幂互不相同，ω⁸ = 1，ω⁴ = {p - 1} ≡ −1。三条性质都满足，FFT 的推导一字不改就能在模 {p} 下进行。这就是 NTT（数论变换）。")
    S.note(f"p = c·2ᵏ + 1，原根 g：ωₙ = g^{{(p−1)/n}}（例：p = {p}，ω₈ = {w}）", color=G)
    S.say("为什么 ω^{n/2} ≡ −1？它的平方是 ωⁿ ≡ 1，又不等于 1（原根的性质），模素数时平方为 1 的只有 ±1。")
    S.say("条件是 n 整除 p − 1。竞赛里最常用 p = 998244353 = 119 × 2²³ + 1，原根是 3：长度 2 的幂、不超过 2²³ 都可以。", extra=0.3)
    S.note("998244353 = 119 · 2²³ + 1，原根 3", color=Y)

    # ------------------------------------------------------------ 适用条件
    S.section("NTT 的适用条件")
    S.say("NTT 全程整数运算、没有精度问题，但答案是模 p 的：题目本来就要求模 998244353 时最合适。")
    S.note("① 答案要求模 p（或真实系数小于 p）")
    S.say("逆变换照样成立：用 ω⁻¹（模 p 的逆元），最后乘以 n 在模 p 下的逆元。")
    S.note("② 逆变换：ω⁻¹ 与 n⁻¹ 都用模 p 的逆元")
    S.say("如果模数是任意的（比如 10⁹ + 7，它减 1 不含足够大的 2 的幂），可以用三个 NTT 模数分别算，再用中国剩余定理合并；或者把系数拆开用浮点 FFT。", extra=0.5)
    S.note("③ 任意模数：三模数 NTT + CRT，或拆系数的 FFT", color=DIM)

    # ------------------------------------------------------------ 手推题
    p2, n2 = 17, 4
    w2 = pow(3, (p2 - 1) // n2, p2)
    vals = ntt([1, 2, 0, 0], w2, p2)
    ninv = pow(n2, -1, p2)
    winv = pow(w2, -1, p2)
    back = [v * ninv % p2 for v in ntt(vals, winv, p2)]
    assert back == [1, 2, 0, 0]
    S.quiz("在模 17 下做长度 4 的 NTT（原根 3）。\n\n"
           "(1) ω₄ 是多少？验证 ω₄² ≡ −1。\n"
           "(2) 求 1 + 2x 的 NTT：在 ω₄⁰、ω₄¹、ω₄²、ω₄³ 处的值（模 17）。\n"
           "(3) 逆变换要乘的 4⁻¹ (mod 17) 是多少？", think=20)
    S.say(f"(1) ω₄ = 3^{{16/4}} = 3⁴ = 81 ≡ {w2}。{w2}² = {w2 * w2} ≡ {w2 * w2 % p2} ≡ −1 ✓。")
    S.note(f"(1) ω₄ = {w2}", color=Y)
    pts = [pow(w2, k, p2) for k in range(4)]
    S.say("(2) 四个点依次是 " + "、".join(map(str, pts)) + "，代入 1 + 2x 取模："
          + "、".join(f"1 + 2·{x} ≡ {v}" for x, v in zip(pts, vals)) + "。")
    S.note("(2) NTT = " + "、".join(map(str, vals)), color=G)
    S.say(f"(3) 4 × {ninv} = {4 * ninv} = 3 × 17 + 1，所以 4⁻¹ ≡ {ninv}。用 ω⁻¹ = {winv} 再做一次变换、每项乘 {ninv}，就回到 1, 2, 0, 0。", extra=0.5)
    S.note(f"(3) 4⁻¹ ≡ {ninv}；逆变换得回 1, 2, 0, 0", color=G)

    S.recap([
        "DFT 是矩阵乘法 y = Va；V(ω)·V(ω⁻¹) = nI，所以逆变换就是用 ω⁻¹ 做 FFT 再除以 n。",
        "关键等式：ω^{j−l} ≠ 1 时 Σₖ(ω^{j−l})ᵏ = 0（单位根之和为零）。",
        "模 p = c·2ᵏ + 1 下取 ω = g^{(p−1)/n}，满足单位根的全部性质：这就是 NTT，998244353 与原根 3 最常用。",
        "NTT 无精度误差但结果模 p；任意模数要三模数 NTT + CRT 或拆系数 FFT。",
    ], next_title=None)
