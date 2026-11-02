"""第 44 集 中国剩余定理：把同余方程一个个合并"""

from math import gcd

from episodes.common import *

SYS = [(2, 3), (3, 5), (2, 7)]          # x ≡ a (mod m)


def inv(a, m):
    return pow(a, -1, m)


def merge(a1, m1, a2, m2):
    """x ≡ a1 (mod m1) 与 x ≡ a2 (mod m2) 合并，返回 (a, m, g, k) 或 None。"""
    g = gcd(m1, m2)
    if (a2 - a1) % g:
        return None
    k = (a2 - a1) // g * inv(m1 // g, m2 // g) % (m2 // g) if m2 // g > 1 else 0
    m = m1 // g * m2
    return (a1 + m1 * k) % m, m, g, k


def build(S):
    S.cover("“三三数之剩二，五五数之剩三，七七数之剩二，问物几何？”——同时满足几个同余方程的数怎么找？模数不互素时又怎么办？",
            ["扩展欧几里得与逆元（第 43 集）"])

    M = 1
    for a, m in SYS:
        M *= m
    x = sum(a * (M // m) * inv(M // m, m) for a, m in SYS) % M
    assert all(x % m == a for a, m in SYS)

    # ------------------------------------------------------------ 构造
    S.section("模数两两互素：拼出来")
    eqs = [label(220, 220 + 60 * k, f"x ≡ {a} (mod {m})", 32, FG, anchor="lm") for k, (a, m) in enumerate(SYS)]
    S.show(*eqs, dur=0.5, lag=0.1)
    S.say("三个方程：x ≡ 2 (mod 3)，x ≡ 3 (mod 5)，x ≡ 2 (mod 7)。3、5、7 两两互素。")
    S.say("思路：分别造三个数，第 i 个数“只管”第 i 个方程——模 mᵢ 余 1，模其他模数余 0。然后按 aᵢ 加权求和。")
    S.note("造 eᵢ：eᵢ ≡ 1 (mod mᵢ)，且被其他所有 mⱼ 整除", color=Y)
    rows = []
    for a, m in SYS:
        Mi = M // m
        ti = inv(Mi, m)
        rows.append([str(m), str(a), str(Mi), str(ti), str(Mi * ti)] + [str(Mi * ti % mm) for _, mm in SYS])
    tb = Grid(len(SYS), 8, x=640, y=520, cw=118, ch=56, gap=4, size=24, vals=rows,
              clab=["mᵢ", "aᵢ", "Mᵢ = M/mᵢ", "tᵢ = Mᵢ⁻¹", "eᵢ = Mᵢtᵢ"] + [f"eᵢ mod {m}" for _, m in SYS])
    S.show(tb)
    S.say(f"M = 3 × 5 × 7 = {M}。Mᵢ = M/mᵢ 被其他模数整除；再乘上 Mᵢ 模 mᵢ 的逆元 tᵢ（互素所以存在），就让它模 mᵢ 余 1。")
    S.note(f"M = ∏mᵢ = {M}；eᵢ = Mᵢ · (Mᵢ⁻¹ mod mᵢ)")
    S.play(*[tb[k, 5 + k].to(fill=tint(G, 0.45)) for k in range(3)],
           *[tb[k, 5 + j].to(fill=tint(B, 0.15)) for k in range(3) for j in range(3) if j != k], dur=0.6)
    S.say("右边三列验证：e₁、e₂、e₃ 模 3、5、7 的余数排成单位矩阵——每个 eᵢ 只在自己的方程里是 1。")
    S.say(f"于是 x = 2e₁ + 3e₂ + 2e₃ = {sum(a * (M // m) * inv(M // m, m) for a, m in SYS)}，模 {M} 后得 x = {x}。")
    S.note(f"x = Σ aᵢeᵢ mod M = {x}", color=G)
    res = label(900, 280, f"x = {x}：{x} = {x // 3}×3 + {x % 3}，{x // 5}×5 + {x % 5}，{x // 7}×7 + {x % 7}", 28, Y)
    S.show(res)

    # ------------------------------------------------------------ 唯一性
    S.section("解在模 M 下唯一")
    S.say("如果 x 和 x′ 都是解，那么每个 mᵢ 都整除 x − x′。mᵢ 两两互素，所以它们的乘积 M 也整除 x − x′。")
    S.note("两两互素：解在模 M = ∏mᵢ 下唯一", color=Y)
    nl = Array([str(x + k * M) for k in range(-1, 4)], x=640, y=400, cw=130, ch=60, gap=12, size=28, index=False,
               fill=tint(G, 0.2))
    S.show(nl, label(640, 320, f"所有解：{x} + {M}k", 26, G))
    S.say(f"所有解就是 {x} + {M}k。反过来，模 M 的每个余数都恰好对应一组 (x mod 3, x mod 5, x mod 7)——{M} 个余数和 3 × 5 × 7 种余数组合一一对应。", extra=0.3)

    # ------------------------------------------------------------ 一般情形
    S.section("模数不互素：两个两个合并")
    S.say("模数不互素时，逆元可能不存在，上面的构造失效。换个思路：先把前两个方程合并成一个，再和第三个合并……")
    S.note("一般情形：两个方程合并成一个，依次合并", color=Y)
    a1, m1, a2, m2 = 2, 6, 8, 10
    seq = [a1 + m1 * k for k in range(6)]
    arr = Array(seq, x=640, y=330, cw=96, ch=58, gap=10, size=28, idx_labels=[f"k={k}" for k in range(6)])
    S.show(arr, label(640, 240, f"x ≡ {a1} (mod {m1})：x = {a1} + {m1}k", 26, CY))
    S.say(f"例：x ≡ {a1} (mod {m1})，x ≡ {a2} (mod {m2})。满足第一个的数是 {a1} + {m1}k，代入第二个：{m1}k ≡ {a2 - a1} (mod {m2})。")
    r = merge(a1, m1, a2, m2)
    g = gcd(m1, m2)
    S.play(*[arr.cells[k].to(fill=tint(G, 0.45) if seq[k] % m2 == a2 else BG3) for k in range(6)], dur=0.6)
    S.say(f"这是关于 k 的同余方程：有解 ⇔ g = gcd({m1}, {m2}) = {g} 整除 {a2 - a1}。约去 g 后用逆元解出 k ≡ {r[3]} (mod {m2 // g})。")
    S.note("m₁k ≡ a₂ − a₁ (mod m₂)：有解 ⇔ gcd(m₁, m₂) | a₂ − a₁", color=G)
    S.say(f"代回 x = {a1} + {m1}·{r[3]} = {r[0]}。合并后的方程是 x ≡ {r[0]} (mod {r[1]})，新模数是 lcm({m1}, {m2}) = {r[1]}。")
    S.note("合并结果：x ≡ a₁ + m₁k (mod lcm(m₁, m₂))", color=G)
    r2 = merge(r[0], r[1], 3, 7)
    S.say(f"再和 x ≡ 3 (mod 7) 合并：{r[0]} + {r[1]}k ≡ 3 (mod 7)，解得 k ≡ {r2[3]}，x ≡ {r2[0]} (mod {r2[1]})。依次合并就能处理任意多个方程。")
    assert r2[0] % 6 == 2 and r2[0] % 10 == 8 and r2[0] % 7 == 3
    bad = merge(1, 4, 2, 6)
    assert bad is None
    S.say("什么时候无解？例如 x ≡ 1 (mod 4) 和 x ≡ 2 (mod 6)：前者说 x 是奇数，后者说 x 是偶数。gcd(4, 6) = 2 不整除 2 − 1，正是这个矛盾。", extra=0.3)
    S.note("例：x ≡ 1 (mod 4)、x ≡ 2 (mod 6) 无解（奇偶矛盾）", color=R)
    S.say("实现时要小心溢出：k 先对 m₂/g 取模，模数一路乘到 lcm，中间乘法可能超过 64 位，需要用龟速乘或 128 位整数。", extra=0.3)
    S.note("注意溢出：中间乘积可能超过 64 位")

    # ------------------------------------------------------------ 手推题
    q = [(3, 4), (5, 6), (2, 5)]
    q1 = merge(q[0][0], q[0][1], q[1][0], q[1][1])
    q2 = merge(q1[0], q1[1], q[2][0], q[2][1])
    S.quiz("(1) 解方程组：x ≡ 3 (mod 4)，x ≡ 5 (mod 6)，x ≡ 2 (mod 5)。写出合并的每一步。\n"
           "(2) 如果把第二个方程改成 x ≡ 4 (mod 6)，还有解吗？为什么？", think=20)
    S.say(f"(1) 先合并前两个：3 + 4k ≡ 5 (mod 6)，即 4k ≡ 2 (mod 6)。gcd(4, 6) = 2 整除 2，约成 2k ≡ 1 (mod 3)，k ≡ {q1[3]}，x ≡ {q1[0]} (mod {q1[1]})。")
    S.say(f"再和 x ≡ 2 (mod 5) 合并：{q1[0]} + {q1[1]}k ≡ 2 (mod 5)，解得 k ≡ {q2[3]}，x ≡ {q2[0]} (mod {q2[1]})。验算：{q2[0]} 除以 4、6、5 分别余 {q2[0] % 4}、{q2[0] % 6}、{q2[0] % 5}。")
    S.note(f"(1) x ≡ {q1[0]} (mod {q1[1]}) → x ≡ {q2[0]} (mod {q2[1]})", color=Y)
    assert merge(3, 4, 4, 6) is None
    S.say("(2) 无解：x ≡ 3 (mod 4) 说明 x 是奇数，x ≡ 4 (mod 6) 说明 x 是偶数。用条件判断：gcd(4, 6) = 2 不整除 4 − 3 = 1。", extra=0.5)
    S.note("(2) 无解：gcd(4, 6) ∤ 1", color=R)

    S.recap([
        "两两互素：eᵢ = Mᵢ · (Mᵢ⁻¹ mod mᵢ) 只在第 i 个方程里余 1，x = Σaᵢeᵢ mod M。",
        "解在模 M = ∏mᵢ 下唯一；余数组合和模 M 的余数一一对应。",
        "一般情形两两合并：m₁k ≡ a₂ − a₁ (mod m₂)，有解 ⇔ gcd(m₁, m₂) | a₂ − a₁，新模数是 lcm。",
        "实现要注意中间结果溢出。",
    ], next_title="组合计数建模")
