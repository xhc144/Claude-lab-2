"""第 47 集 矩阵递推：把转移写成矩阵"""

from episodes.common import *


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def mpow(M, e):
    R = [[int(i == j) for j in range(len(M))] for i in range(len(M))]
    while e:
        if e & 1:
            R = mul(R, M)
        M = mul(M, M)
        e >>= 1
    return R


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def build(S):
    S.cover("斐波那契数列的第 10¹⁸ 项（模某个数）怎么求？一项一项推要 10¹⁸ 步。把“推一步”写成乘一个矩阵，就能用快速幂在 O(log n) 次乘法内完成。",
            ["线性递推", "快速幂", "矩阵乘法"])

    # ------------------------------------------------------------ 写成矩阵
    S.section("把递推写成矩阵乘法")
    S.say("斐波那契：F(n + 1) = F(n) + F(n − 1)。推下一项要用到最近的两项，所以把这两项打包成一个“状态向量”。")
    S.note("状态向量：(F(n), F(n − 1))", color=Y)
    M = [[1, 1], [1, 0]]
    left = Matrix([["F(n+1)"], ["F(n)"]], x=330, y=400, cw=150, ch=64, size=30, color=CY)
    eq = label(460, 400, "=", 40, FG)
    mm = Matrix(M, x=590, y=400, cw=70, ch=64, size=32, color=Y)
    right = Matrix([["F(n)"], ["F(n−1)"]], x=800, y=400, cw=150, ch=64, size=30, color=CY)
    S.show(left, eq, mm, right, dur=0.6, lag=0.1)
    S.say("新状态的每个分量都是旧状态分量的线性组合：F(n + 1) = 1·F(n) + 1·F(n − 1)，F(n) = 1·F(n) + 0·F(n − 1)。把系数排成矩阵：")
    S.play(*[mm[0, j].to(color=O) for j in range(2)], left[0, 0].to(color=O), dur=0.5)
    S.play(*[mm[0, j].to(color=Y) for j in range(2)], left[0, 0].to(color=CY),
           *[mm[1, j].to(color=O) for j in range(2)], left[1, 0].to(color=O), dur=0.5)
    S.play(*[mm[1, j].to(color=Y) for j in range(2)], left[1, 0].to(color=CY), dur=0.3)
    S.note("vₙ₊₁ = M vₙ ⇒ vₙ = Mⁿ v₀", color=G)
    S.say("于是推 n 步就是乘 n 次 M：vₙ = Mⁿ v₀。一般的 k 阶线性递推，状态是最近 k 项，矩阵是 k × k。")
    S.note("k 阶线性递推：k × k 矩阵（第一行是系数，下面是“平移”）")

    # ------------------------------------------------------------ 快速幂
    S.section("结合律让快速幂成立")
    n = 13
    S.say(f"Mⁿ 怎么快速算？和整数快速幂一样：{n} 的二进制是 {bin(n)[2:]}，所以 M¹³ = M⁸ · M⁴ · M¹。M、M²、M⁴、M⁸ 依次平方得到。")
    pw = []
    for t, e in enumerate([1, 2, 4, 8]):
        P_ = mpow(M, e)
        box = Matrix(P_, x=200 + 270 * t, y=330, cw=64, ch=56, size=26, color=Y if n >> t & 1 else DIM)
        cap = label(200 + 270 * t, 240, f"M^{e}" if e > 1 else "M", 28, Y if n >> t & 1 else DIM)
        pw.append((box, cap))
        S.show(box, cap, dur=0.4)
    res = mpow(M, n)
    S.show(label(640, 480, f"M¹³ = M⁸ · M⁴ · M¹ = ", 30, FG, anchor="rm"),
           Matrix(res, x=760, y=480, cw=90, ch=56, size=28, color=G))
    S.say(f"结果左下角就是 F({n}) = {res[1][0]}。只做了 3 次平方和 3 次乘法，而不是 12 次乘法。")
    assert res[1][0] == fib(n)
    S.say("为什么能这样拆？因为矩阵乘法满足结合律：$(AB)C = A(BC)$。快速幂只是重新安排乘法的顺序，不需要交换律。", extra=0.3)
    S.note("结合律 ⇒ 快速幂：O(k³ log n)", color=Y)
    S.note("不需要交换律（矩阵乘法一般不可交换）")

    # ------------------------------------------------------------ 增广
    S.section("常数项：给状态加一个 1")
    S.say("f(n) = 2f(n − 1) + 3 不是“纯”线性的，多了常数 3。办法：在状态里加一个恒为 1 的分量，常数就成了这个分量的系数。")
    S.note("常数项：状态里加一个恒为 1 的分量", color=Y)
    A2 = Matrix([["f(n)"], ["1"]], x=330, y=380, cw=130, ch=64, size=30, color=CY)
    M2 = Matrix([[2, 3], [0, 1]], x=560, y=380, cw=70, ch=64, size=32, color=Y)
    B2 = Matrix([["f(n−1)"], ["1"]], x=770, y=380, cw=130, ch=64, size=30, color=CY)
    S.show(A2, label(450, 380, "=", 40), M2, B2, dur=0.6)
    S.say("第一行：f(n) = 2·f(n − 1) + 3·1；第二行：1 = 0·f(n − 1) + 1·1，让 1 一直保持为 1。")
    S.say("同样的技巧可以维护前缀和：S(n) = S(n − 1) + F(n)，把 S 也放进状态，矩阵多一行一列。", extra=0.3)
    S.note("前缀和、多个数列一起推：都可以放进状态向量", color=G)

    # ------------------------------------------------------------ 路径计数
    S.section("长度为 k 的路径数")
    pos = {1: (-170, -100), 2: (170, -100), 3: (0, 150)}
    E = [(1, 2), (2, 1), (2, 3), (3, 1), (1, 3)]
    g = Graph(pos, E, x=330, y=460, directed=True, r=34, size=28, ecolor=LINE2)
    S.show(g)
    Adj = [[0] * 3 for _ in range(3)]
    for u, v in E:
        Adj[u - 1][v - 1] += 1
    S.say("有向图的邻接矩阵 A：A[i][j] 是从 i 到 j 的边数。")
    am = Matrix(Adj, x=820, y=330, cw=66, ch=56, size=28, color=FG)
    S.show(label(700, 330, "A =", 30, FG, anchor="rm"), am)
    A2m = mpow(Adj, 2)
    S.say("A² 的 (i, j) 元 = Σₖ A[i][k]·A[k][j]：先走一步到 k，再走一步到 j，对所有中转点 k 求和——正好是长度为 2 的路径数。")
    a2 = Matrix(A2m, x=820, y=560, cw=66, ch=56, size=28, color=G)
    S.show(label(700, 560, "A² =", 30, FG, anchor="rm"), a2)
    S.play(a2[0, 0].to(color=Y), dur=0.3)
    S.play(g.edge(1, 2).to(color=Y, w=4), g.edge(2, 1).to(color=Y, w=4), dur=0.5)
    S.play(g.edge(1, 3).to(color=O, w=4), g.edge(3, 1).to(color=O, w=4), dur=0.5)
    S.say(f"例：从 1 出发走两步回到 1 有 {A2m[0][0]} 条：1 → 2 → 1 和 1 → 3 → 1。")
    S.play(*[g.edge(u, v).to(color=LINE2, w=3) for u, v in [(1, 2), (2, 1), (1, 3), (3, 1)]], dur=0.3)
    S.note("(Aᵏ)[i][j] = 从 i 到 j、恰好走 k 步的路径数", color=Y)
    S.say("归纳下去，Aᵏ 的 (i, j) 元就是恰好走 k 步的路径数。k 很大时用快速幂：O(n³ log k)。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    f = {1: 1, 2: 1}
    for i in range(3, 8):
        f[i] = f[i - 1] + 2 * f[i - 2] + 1
    Mq = [[1, 2, 1], [1, 0, 0], [0, 0, 1]]
    v = mul(mpow(Mq, 3), [[f[2]], [f[1]], [1]])
    assert v[0][0] == f[5]
    S.quiz("f(1) = f(2) = 1，f(n) = f(n − 1) + 2f(n − 2) + 1。\n\n"
           "(1) 选一个状态向量，写出转移矩阵。\n"
           "(2) 求 f(5)，并说明用矩阵怎样算 f(10¹⁸)。", think=20)
    S.say("(1) 状态 (f(n), f(n − 1), 1)，三行分别是：f(n + 1) = 1·f(n) + 2·f(n − 1) + 1·1；f(n) = 1·f(n)；1 = 1·1。")
    S.show(Matrix(Mq, x=640, y=560, cw=70, ch=56, size=30, color=Y))
    S.note("(1) 矩阵 [[1, 2, 1], [1, 0, 0], [0, 0, 1]]", color=Y)
    S.say(f"(2) 逐项推：f(3) = {f[3]}，f(4) = {f[4]}，f(5) = {f[5]}。用矩阵：(f(5), f(4), 1) = M³ · (f(2), f(1), 1)。")
    S.say("f(10¹⁸) 就是 M 的 (10¹⁸ − 2) 次方乘初始向量：快速幂约 60 次平方，每次 3 × 3 矩阵乘法 27 次乘法。", extra=0.5)
    S.note(f"(2) f(5) = {f[5]}；f(n) = (Mⁿ⁻² v₂) 的第一项", color=G)

    S.recap([
        "线性递推：把最近 k 项打包成状态向量，推一步就是乘一个 k × k 矩阵。",
        "矩阵乘法满足结合律，所以 Mⁿ 可以用快速幂在 O(k³ log n) 内算出。",
        "常数项、前缀和等都可以通过扩充状态（加一个恒为 1 的分量）放进矩阵。",
        "邻接矩阵的 k 次幂给出恰好走 k 步的路径数。",
    ], next_title="概率与期望 DP（上）")
