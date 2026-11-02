"""第 43 集 扩展欧几里得与同余方程：把 gcd 的过程倒着走"""

from math import gcd

from episodes.common import *

A, B = 99, 78


def exgcd_steps(a, b):
    """欧几里得的每一步 (a, b, q, r)，以及回代得到的 (x, y)（从下往上）。"""
    steps = []
    while b:
        steps.append((a, b, a // b, a % b))
        a, b = b, a % b
    steps.append((a, 0, None, None))
    xy = [None] * len(steps)
    xy[-1] = (1, 0)
    for k in range(len(steps) - 2, -1, -1):
        x1, y1 = xy[k + 1]
        q = steps[k][2]
        xy[k] = (y1, x1 - q * y1)
    return steps, xy


def build(S):
    S.cover("求方程 ax + by = c 的整数解，或者同余方程 ax ≡ c (mod m) 的解。辗转相除求 gcd 的过程，倒着走一遍就能把解构造出来。",
            ["辗转相除法（欧几里得算法）", "带余除法"])

    steps, xy = exgcd_steps(A, B)
    g = steps[-1][0]
    x0, y0 = xy[0]
    assert A * x0 + B * y0 == g == gcd(A, B)

    # ------------------------------------------------------------ 裴蜀定理
    S.section("ax + by 能凑出哪些数")
    a, b = 30, 12
    S.say(f"先看一个问题：用 {a} 和 {b}，允许乘任意整数（可以是负数）再相加，能凑出哪些数？")
    x_0, x_1 = 120, 1240
    lo, hi = 0, 60
    X = lambda v: x_0 + (v - lo) / (hi - lo) * (x_1 - x_0)       # noqa: E731
    axis = Line(x_0 - 20, 420, x_1 + 20, 420, color=LINE2, w=2.5, head=12)
    ticks = []
    for v in range(lo, hi + 1, 2):
        big = v % 6 == 0
        ticks.append(Line(X(v), 420 - (10 if big else 5), X(v), 420 + (10 if big else 5), color=LINE2, w=2 if big else 1.2))
        if big:
            ticks.append(label(X(v), 455, str(v), 22, DIM))
    S.show(axis, *ticks, dur=0.6)
    combos = {}
    for x in range(-4, 5):
        for y in range(-8, 9):
            v = a * x + b * y
            if lo <= v <= hi and (v not in combos or abs(x) + abs(y) < sum(map(abs, combos[v]))):
                combos[v] = (x, y)
    dots = []
    for v in sorted(combos):
        d = Circle(X(v), 420, 9, fill=Y, stroke=None, sw=0)
        d.tr["op"].base = 0
        dots.append(d)
        S.add(d)
    S.play(*[FadeIn(d, scale=0.3) for d in dots], dur=0.8, lag=0.06)
    ex = [label(X(v), 360 - 40 * (k % 2), f"{a}·({combos[v][0]}) + {b}·({combos[v][1]})", 20, Y)
          for k, v in enumerate([6, 18, 42])]
    S.show(*ex, dur=0.5)
    S.say(f"凑出来的恰好是 {gcd(a, b)} 的所有倍数，一个不多、一个不少。{gcd(a, b)} 正是 gcd({a}, {b})。")
    S.note("裴蜀定理：{ax + by} = gcd(a, b) 的所有倍数", color=Y)
    S.say("为什么？a、b 都是 g = gcd(a, b) 的倍数，所以 ax + by 一定是 g 的倍数。反过来要说明 g 本身能凑出来。")
    S.say("设 d 是能凑出的最小正数。a 除以 d 的余数 = a − ⌊a/d⌋·d 也能凑出，且比 d 小，只能是 0；所以 d 整除 a，同理整除 b。d 是公因数，又是 g 的倍数，只能 d = g。", extra=0.3)
    S.note("最小的正 ax + by 整除 a、b ⇒ 它就是 gcd", color=G)

    # ------------------------------------------------------------ 辗转相除
    S.section("辗转相除，再倒着回代")
    rows = len(steps)
    vals = [[str(s_[0]), str(s_[1]), "" if s_[2] is None else str(s_[2]), "", ""] for s_ in steps]
    tb = Grid(rows, 5, x=520, y=470, cw=130, ch=56, gap=4, size=26, vals=vals,
              clab=["a", "b", "⌊a/b⌋", "x", "y"])
    S.show(tb)
    S.say(f"求 gcd({A}, {B})：gcd(a, b) = gcd(b, a mod b)，一直除到 b = 0。表格每一行是一步。")
    S.note("gcd(a, b) = gcd(b, a mod b)；b = 0 时 gcd = a")
    for k in range(rows):
        S.play(tb[k, 0].to(fill=tint(CY, 0.25)), tb[k, 1].to(fill=tint(CY, 0.25)), dur=0.25)
    S.say(f"最后一行 b = 0，gcd = {g}。现在要找 x、y 使 {A}x + {B}y = {g}。从最后一行往上构造。")
    S.say(f"最后一行：{g}·1 + 0·0 = {g}，取 x = 1，y = 0。")
    S.play(tb[rows - 1, 3].to(text="1", fill=tint(G, 0.35)), tb[rows - 1, 4].to(text="0", fill=tint(G, 0.35)), dur=0.5)
    S.say("假设下一行已经有 b·x′ + (a mod b)·y′ = g。把 a mod b = a − ⌊a/b⌋·b 代进去整理：a·y′ + b·(x′ − ⌊a/b⌋·y′) = g。")
    S.note("x = y′，y = x′ − ⌊a/b⌋ · y′（x′, y′ 是下一行的解）", color=Y)
    for k in range(rows - 2, -1, -1):
        x, y = xy[k]
        S.play(tb[k + 1, 3].to(stroke=O, sw=3), tb[k + 1, 4].to(stroke=O, sw=3), tb[k, 2].to(stroke=O, sw=3), dur=0.3)
        S.play(tb[k, 3].to(text=str(x), fill=tint(G, 0.35)), tb[k, 4].to(text=str(y), fill=tint(G, 0.35)), dur=0.4)
        if k == rows - 3:
            x1, y1 = xy[k + 1]
            S.say(f"例：这一行 a = {steps[k][0]}，b = {steps[k][1]}，下一行解是 ({x1}, {y1})，于是 x = {y1}，y = {x1} − {steps[k][2]}·{y1} = {y}。")
        S.play(tb[k + 1, 3].to(stroke=LINE, sw=2), tb[k + 1, 4].to(stroke=LINE, sw=2), tb[k, 2].to(stroke=LINE, sw=2), dur=0.2)
    S.say(f"回到第一行：x = {x0}，y = {y0}。验算：{A}·({x0}) + {B}·{y0} = {A * x0} + {B * y0} = {g}。")
    S.note(f"{A}·({x0}) + {B}·{y0} = {g}", color=G)
    S.say("这就是扩展欧几里得：和辗转相除同样的 O(log min(a, b)) 步，顺便求出一组 x、y。", extra=0.3)

    # ------------------------------------------------------------ 全部解
    S.section("全部的解")
    S.say(f"一组解有了，其他解呢？两组解相减：a(x − x₀) = −b(y − y₀)。两边除以 g，a/g 与 b/g 互素，所以 b/g 整除 x − x₀。")
    S.note("通解：x = x₀ + k·b/g，y = y₀ − k·a/g（k 为任意整数）", color=Y)
    bg, ag = B // g, A // g
    sol = [(x0 + k * bg, y0 - k * ag) for k in range(-1, 3)]
    tbs = Grid(len(sol), 3, x=520, y=430, cw=170, ch=56, gap=4, size=26,
               vals=[[str(k), str(x), str(y)] for k, (x, y) in zip(range(-1, 3), sol)], clab=["k", "x", "y"])
    S.show(tbs)
    S.say(f"这里 b/g = {bg}，a/g = {ag}：x 每次加 {bg}，y 每次减 {ag}，都满足 {A}x + {B}y = {g}。")
    xm = x0 % bg
    S.say(f"常要的是最小正整数解：x = ((x₀ mod {bg}) + {bg}) mod {bg} = {xm}（结果是 0 时取 {bg}）。")
    S.note("最小非负 x：(x₀ mod (b/g) + b/g) mod (b/g)")
    S.say("一般的 ax + by = c：g 不整除 c 就无解；整除时，把上面的解乘以 c/g 即可。", extra=0.3)
    S.note("ax + by = c 有解 ⇔ g | c；解 = (c/g) × 上面的解", color=G)

    # ------------------------------------------------------------ 同余方程
    S.section("同余方程与逆元")
    a2, m2 = 7, 26
    st2, xy2 = exgcd_steps(a2, m2)
    inv = xy2[0][0] % m2
    assert a2 * inv % m2 == 1
    S.say("ax ≡ c (mod m) 的意思是 ax − c 是 m 的倍数，即存在整数 y 使 ax + my = c。它就是上面的方程。")
    S.note("ax ≡ c (mod m) ⇔ ax + my = c", color=Y)
    S.say("所以：有解 ⇔ gcd(a, m) 整除 c；解在模 m/gcd(a, m) 意义下唯一，模 m 意义下有 gcd(a, m) 个。")
    S.note("有解 ⇔ gcd(a, m) | c；模 m 下有 gcd(a, m) 个解")
    S.say(f"特别地，ax ≡ 1 (mod m) 的解叫 a 的逆元，有逆元 ⇔ gcd(a, m) = 1。例：{a2} 模 {m2} 的逆元，用扩展欧几里得解 {a2}x + {m2}y = 1。")
    big = label(640, 400, f"{a2} × {inv} = {a2 * inv} = {a2 * inv // m2} × {m2} + 1", 40, Y)
    S.show(big)
    S.say(f"得到 x = {xy2[0][0]}，调整到 0～{m2 - 1}：逆元是 {inv}。验算 {a2} × {inv} = {a2 * inv} ≡ 1 (mod {m2})。")
    S.note(f"逆元存在 ⇔ gcd(a, m) = 1；例：{a2}⁻¹ ≡ {inv} (mod {m2})", color=G)
    S.say("模数是素数 p 时，也可以用费马小定理：a⁻¹ ≡ aᵖ⁻² (mod p)。扩展欧几里得的好处是模数不必是素数。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    qa, qb, qc = 21, 15, 9
    qs, qxy = exgcd_steps(qa, qb)
    qg = qs[-1][0]
    qx0, qy0 = qxy[0][0] * (qc // qg), qxy[0][1] * (qc // qg)
    step = qb // qg
    qxm = qx0 % step if qx0 % step else step
    qym = (qc - qa * qxm) // qb
    S.quiz(f"(1) 求 {qa}x + {qb}y = {qc} 的一组整数解，以及 x 最小的正整数解。\n"
           "(2) 解同余方程 8x ≡ 6 (mod 14)，写出模 14 意义下的全部解。", think=20)
    S.say(f"(1) 辗转相除：gcd({qa}, {qb}) = {qg}，{qg} 整除 {qc}，有解。回代得 {qa}·({qxy[0][0]}) + {qb}·{qxy[0][1]} = {qg}，乘以 {qc // qg}：x₀ = {qx0}，y₀ = {qy0}。")
    S.say(f"通解 x = {qx0} + {step}k。最小正整数解 x = {qxm}，此时 y = {qym}：{qa}·{qxm} + {qb}·({qym}) = {qc}。")
    assert qa * qxm + qb * qym == qc
    S.note(f"(1) 一组解 ({qx0}, {qy0})；最小正 x = {qxm}，y = {qym}", color=Y)
    sols = [x for x in range(14) if 8 * x % 14 == 6]
    S.say(f"(2) gcd(8, 14) = 2 整除 6，有 2 个解。两边和模数同除以 2：4x ≡ 3 (mod 7)，4 的逆元是 2，x ≡ 6 (mod 7)。")
    S.say(f"回到模 14：x ≡ {sols[0]} 或 {sols[1]} (mod 14)。验算 8 × {sols[0]} = {8 * sols[0]}，8 × {sols[1]} = {8 * sols[1]}，除以 14 都余 6。", extra=0.5)
    S.note(f"(2) x ≡ {sols[0]}、{sols[1]} (mod 14)", color=G)

    S.recap([
        "裴蜀定理：ax + by 能取到的恰好是 gcd(a, b) 的所有倍数。",
        "扩展欧几里得：辗转相除到 b = 0，再倒着回代 x = y′，y = x′ − ⌊a/b⌋y′，O(log) 步。",
        "通解 x = x₀ + k·b/g、y = y₀ − k·a/g；ax + by = c 有解 ⇔ g | c。",
        "ax ≡ c (mod m) 就是 ax + my = c；逆元存在 ⇔ gcd(a, m) = 1。",
    ], next_title="中国剩余定理")
