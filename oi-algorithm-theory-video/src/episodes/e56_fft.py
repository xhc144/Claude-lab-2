"""第 56 集 FFT（上）：从系数到点值"""

import cmath
import math

from episodes.common import *

QA = [1, 2, 3, 4]


def cfmt(z):
    """把复数写成 a + bi 的样子（整数时省略小数）。"""
    a, b = round(z.real, 6), round(z.imag, 6)
    fa = (str(int(a)) if abs(a - round(a)) < 1e-6 else f"{a:.2f}")
    fb = (str(int(abs(b))) if abs(abs(b) - round(abs(b))) < 1e-6 else f"{abs(b):.2f}")
    if abs(b) < 1e-9:
        return fa
    if abs(a) < 1e-9:
        return ("−" if b < 0 else "") + ("" if fb == "1" else fb) + "i"
    return f"{fa} {'−' if b < 0 else '+'} {'' if fb == '1' else fb}i".replace("-", "−")


def evaluate(coef, x):
    return sum(c * x ** k for k, c in enumerate(coef))


def build(S):
    S.cover("两个 n 次多项式相乘，逐项相乘是 O(n²)。换一种表示——用若干个点上的取值来描述多项式——乘法就只要 O(n)。难点在于两种表示之间怎么快速转换。",
            ["多项式", "复数与单位圆（片中会补充）"])

    # ------------------------------------------------------------ 两种表示
    S.section("系数表示与点值表示")
    S.say("多项式 A(x) = a₀ + a₁x + … + aₙ₋₁xⁿ⁻¹ 可以用系数 (a₀, …, aₙ₋₁) 表示；也可以用它在 n 个不同点上的取值表示——n 个点唯一确定一个 n − 1 次多项式。")
    S.note("系数表示 (a₀, …, aₙ₋₁) ↔ 点值表示 (A(x₀), …, A(xₙ₋₁))", color=Y)
    A = [1, 2]
    Bc = [3, 1]
    C = [3, 7, 2]
    xs = [0, 1, 2]
    rows = [[f"x = {x}", str(evaluate(A, x)), str(evaluate(Bc, x)), str(evaluate(A, x) * evaluate(Bc, x))] for x in xs]
    tb = Grid(3, 4, x=560, y=430, cw=170, ch=58, gap=4, size=26, vals=rows,
              clab=["取值点", "A(x) = 1 + 2x", "B(x) = 3 + x", "C = A · B"])
    S.show(tb)
    S.say("乘积 C = A · B 在每个点的取值，就是 A、B 在这个点取值的乘积：点值表示下乘法只要逐点相乘，O(n)。")
    S.play(*[tb[r, 3].to(fill=tint(G, 0.35)) for r in range(3)], dur=0.5)
    S.say(f"C 是 2 次多项式，需要 3 个点才能确定。从这 3 个值反推系数，正好是 C(x) = 3 + 7x + 2x²。")
    assert all(evaluate(C, x) == evaluate(A, x) * evaluate(Bc, x) for x in xs)
    S.note("点值表示下乘法 O(n)；点数要 ≥ 乘积的次数 + 1", color=G)
    S.say("于是乘法可以这样做：系数 → 点值（求值）→ 逐点相乘 → 点值 → 系数（插值）。可是朴素求值每个点 O(n)，n 个点又是 O(n²)。关键在于挑一组特别的点。", extra=0.3)
    S.note("系数 → 点值 → 相乘 → 系数；瓶颈在两头的转换", color=R)

    # ------------------------------------------------------------ 单位根
    S.section("单位根：平方后个数减半")
    cx, cy, Rr = 420, 470, 250
    circ = Circle(cx, cy, Rr, fill=(0, 0, 0, 0), stroke=LINE2, sw=2)
    axx = Line(cx - Rr - 40, cy, cx + Rr + 40, cy, color=alpha(LINE2, 0.7), w=1.5)
    axy = Line(cx, cy + Rr + 40, cx, cy - Rr - 40, color=alpha(LINE2, 0.7), w=1.5)
    S.show(axx, axy, circ)
    n = 8
    S.say("复数 ω = cos(2π/n) + i·sin(2π/n) 叫 n 次单位根：在单位圆上，从 1 出发转 1/n 圈。它的各次幂 ω⁰, ω¹, …, ωⁿ⁻¹ 把圆周 n 等分。")
    S.note("ωₙ = e^{2πi/n}；ωₙᵏ（k = 0..n−1）把单位圆 n 等分", color=Y)
    dots, labs = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Circle(cx + Rr * math.cos(a), cy - Rr * math.sin(a), 11, fill=CY, stroke=None, sw=0)
        d.tr["op"].base = 0
        t = label(cx + (Rr + 46) * math.cos(a), cy - (Rr + 46) * math.sin(a), f"ω^{k}", 26, CY)
        t.tr["op"].base = 0
        dots.append(d)
        labs.append(t)
        S.add(d, t)
    S.play(*[FadeIn(d, scale=0.3) for d in dots], *[FadeIn(t) for t in labs], dur=0.8, lag=0.06)
    S.say("乘以一个单位圆上的复数，就是转一个角度。所以 ωᵏ 的平方，角度翻倍。")
    S.note("复数乘法：长度相乘、角度相加", color=G)
    S.play(*[d.to(x=cx + Rr * math.cos(4 * math.pi * k / n), y=cy - Rr * math.sin(4 * math.pi * k / n), fill=O)
             for k, d in enumerate(dots)], *[FadeOut(t) for t in labs], dur=1.4)
    S.say(f"把 {n} 个点全部平方：角度翻倍，ωᵏ 和 ω^{k+n/2} 落到同一个点上。{n} 个点只剩 {n // 2} 个，正好是 {n // 2} 次单位根。")
    S.note("(ωₙᵏ)² = ω_{n/2}ᵏ，且 ωₙ^{k+n/2} = −ωₙᵏ：平方后个数减半", color=Y)
    S.say("另一面：ω^{k+n/2} = −ωᵏ，正好在 ωᵏ 的对面。这两个性质就是 FFT 能分治的原因。", extra=0.3)

    # ------------------------------------------------------------ 奇偶拆分
    S.section("奇偶拆分：一次算两个点")
    S.say("把 A(x) 的系数按下标奇偶分开：A(x) = E(x²) + x · O(x²)，E 是偶数项系数组成的多项式，O 是奇数项。")
    S.show(label(640, 250, "A(x) = (a₀ + a₂x² + a₄x⁴ + …) + x · (a₁ + a₃x² + a₅x⁴ + …)", 32, FG),
           label(640, 320, "= E(x²) + x · O(x²)", 32, Y))
    S.note("A(x) = E(x²) + x · O(x²)", color=Y)
    S.say("代入 ωᵏ 和它对面的 −ωᵏ：两者平方都是 ω²ᵏ，所以只要知道 E、O 在 ω²ᵏ 处的值，就能同时得到两个点：")
    S.show(label(640, 430, "A(ωᵏ) = E(ω²ᵏ) + ωᵏ · O(ω²ᵏ)", 34, CY),
           label(640, 500, "A(−ωᵏ) = E(ω²ᵏ) − ωᵏ · O(ω²ᵏ)", 34, O))
    S.note("A(±ωᵏ) = E(ω²ᵏ) ± ωᵏ · O(ω²ᵏ)", color=G)
    S.say("而 E、O 要在 n/2 个点（n/2 次单位根）上求值——规模减半的同一个问题，递归下去。")
    S.say("T(n) = 2T(n/2) + O(n)，所以 T(n) = O(n log n)。这就是快速傅里叶变换（FFT）。n 要补成 2 的幂。", extra=0.3)
    S.note("T(n) = 2T(n/2) + O(n) = O(n log n)；n 补到 2 的幂", color=G)

    # ------------------------------------------------------------ 蝴蝶
    S.section("蝴蝶：把递归摊平")
    S.say("把递归展开：最底层是单个系数，往上每一层把两半合并。n = 4 时，叶子的顺序是 a₀、a₂、a₁、a₃——下标的二进制翻转后的顺序。")
    S.note("叶子顺序 = 下标二进制翻转（位逆序）", color=Y)
    xs4 = [140, 480, 820, 1160]
    ys4 = [250, 360, 470, 580]
    order = [0, 2, 1, 3]
    col0 = [label(xs4[0], ys4[r], f"a{order[r]}", 30, FG) for r in range(4)]
    col1_txt = ["E(1)", "E(−1)", "O(1)", "O(−1)"]
    col2_txt = ["A(1)", "A(i)", "A(−1)", "A(−i)"]
    col1 = [label(xs4[1] + 60, ys4[r], col1_txt[r], 28, CY) for r in range(4)]
    col2 = [label(xs4[2] + 120, ys4[r], col2_txt[r], 28, G) for r in range(4)]
    S.show(*col0, dur=0.4)
    lines1 = []
    for a, b in [(0, 1), (2, 3)]:
        for s_, t_ in [(a, a), (a, b), (b, a), (b, b)]:
            ln = Line(xs4[0] + 40, ys4[s_], xs4[1], ys4[t_], color=alpha(CY, 0.7), w=2.5)
            ln.tr["op"].base = 0
            lines1.append(ln)
    S.add(*lines1)
    S.play(*[FadeIn(l) for l in lines1], *[FadeIn(t) for t in col1], dur=0.7)
    S.say("第一层：每两个合并。E(y) = a₀ + a₂y 在 y = ±1 的值是 a₀ ± a₂；O 同理是 a₁ ± a₃。")
    lines2 = []
    for r in range(4):
        for t_ in ([r, r + 2] if r < 2 else [r - 2, r]):
            ln = Line(xs4[1] + 120, ys4[r], xs4[2] + 60, ys4[t_], color=alpha(G, 0.7), w=2.5)
            ln.tr["op"].base = 0
            lines2.append(ln)
    S.add(*lines2)
    S.play(*[FadeIn(l) for l in lines2], *[FadeIn(t) for t in col2], dur=0.7)
    S.say("第二层：A(ωᵏ) = E(ω²ᵏ) + ωᵏO(ω²ᵏ)，A(−ωᵏ) 换成减号。每一对交叉的线像一只蝴蝶——这就是“蝴蝶操作”。")
    S.note("每层 n/2 个蝴蝶，共 log n 层；可以原地、非递归实现", color=G)
    S.say("每层 n/2 个蝴蝶，log n 层。按位逆序排好系数后，从下往上原地合并，不需要递归。下一集讲怎样从点值变回系数。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    vals = {}
    w = 1j
    for k, x in enumerate([1, w, -1, -w]):
        vals[k] = evaluate(QA, x)
    S.quiz("A(x) = 1 + 2x + 3x² + 4x³。用奇偶拆分求它在 4 次单位根 1、i、−1、−i 处的值。\n\n"
           "(1) 写出 E(y)、O(y)。\n"
           "(2) 先求 E、O 在 y = 1 和 y = −1 处的值，再拼出四个 A 值。", think=20)
    S.say("(1) 偶数项：E(y) = 1 + 3y；奇数项：O(y) = 2 + 4y。")
    S.note("(1) E(y) = 1 + 3y，O(y) = 2 + 4y", color=Y)
    S.say("(2) E(1) = 4，E(−1) = −2；O(1) = 6，O(−1) = −2。"
          f"A(1) = 4 + 6 = {cfmt(vals[0])}，A(−1) = 4 − 6 = {cfmt(vals[2])}；"
          f"A(i) = E(−1) + i·O(−1) = {cfmt(vals[1])}，A(−i) = {cfmt(vals[3])}。")
    assert abs(vals[1] - (-2 - 2j)) < 1e-9
    S.say("验算 A(i) = 1 + 2i + 3i² + 4i³ = 1 + 2i − 3 − 4i = −2 − 2i。", extra=0.5)
    S.note(f"(2) A(1) = {cfmt(vals[0])}，A(i) = {cfmt(vals[1])}，A(−1) = {cfmt(vals[2])}，A(−i) = {cfmt(vals[3])}", color=G)

    S.recap([
        "点值表示下多项式乘法是逐点相乘 O(n)；难点是系数与点值之间的转换。",
        "取 n 次单位根作为求值点：平方后变成 n/2 次单位根，且 ω^{k+n/2} = −ωᵏ。",
        "A(x) = E(x²) + x·O(x²)，A(±ωᵏ) 共用 E、O 在 ω²ᵏ 的值：T(n) = 2T(n/2) + O(n) = O(n log n)。",
        "展开递归得到蝴蝶结构，按位逆序排列后可原地迭代实现。",
    ], next_title="FFT（下）与 NTT")
