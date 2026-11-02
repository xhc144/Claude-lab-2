"""第 13 集 树状数组的区间变换：差分把区间变成单点"""

from episodes.common import *

A0 = [3, 1, 4, 1, 5, 9, 2, 6]
N = len(A0)


def lowbit(i):
    return i & -i


def build(S):
    S.cover("树状数组只会“单点修改、前缀求和”。怎样让它支持区间加、区间求和？",
            ["树状数组：单点加、前缀和，各 O(log n)", "前缀和与差分"])

    # ------------------------------------------------------------ 回顾
    S.section("树状数组能做什么")
    arr = Array(A0, x=640, y=200, cw=96, ch=64, gap=8, size=30)
    S.show(arr)
    S.say("先回顾一下：树状数组的第 i 个格子 c[i] 管着一段 (i − lowbit(i), i]，lowbit(i) 是 i 的二进制里最低的那个 1。")
    S.note("c[i] 管 (i − lowbit(i), i]")
    bars = {}
    for i in range(1, N + 1):
        lb = lowbit(i)
        lv = {1: 0, 2: 1, 4: 2, 8: 3}[lb]
        x1, x2 = arr.left(i - lb + 1) + 640, arr.right(i) + 640
        b = Rect((x1 + x2) / 2, 330 + lv * 62, x2 - x1 - 6, 44, fill=tint(CY, 0.25), stroke=CY, sw=2, r=8)
        b.add(Text(0, 0, f"c[{i}]", size=22, color=FG))
        bars[i] = b
    S.show(*bars.values(), lag=0.05)
    S.say("求前缀和 a[1] + … + a[7]：c[7] 管第 7 个，c[6] 管 5~6，c[4] 管 1~4，三块拼起来。每次去掉最低位的 1，最多 log n 块。")
    S.note("前缀和：沿 i → i − lowbit(i) 拼起来，O(log n)")
    for i in (7, 6, 4):
        S.play(bars[i].to(fill=tint(Y, 0.5), stroke=Y), dur=0.4)
    S.say("单点加 a[3] += x：所有管着第 3 个的格子都要改，c[3]、c[4]、c[8]，沿 i → i + lowbit(i) 往上走，也是 log n 个。")
    S.play(*[bars[i].to(fill=tint(CY, 0.25), stroke=CY) for i in (7, 6, 4)], dur=0.3)
    for i in (3, 4, 8):
        S.play(bars[i].to(fill=tint(O, 0.5), stroke=O), dur=0.4)
    S.note("单点加：沿 i → i + lowbit(i) 修改，O(log n)")
    S.say("它天生只会这两件事：单点修改、前缀求和。本集要做的，是通过换一个“维护对象”，让它支持区间操作。")
    S.note("基本能力：单点改 + 前缀和", color=Y)

    # ------------------------------------------------------------ 区间加 单点查
    S.section("区间加、单点查：差分")
    a = list(A0)
    arr2 = Array(a, x=640, y=230, cw=96, ch=64, gap=8, size=30)
    la = label(130, 230, "a", 30, FG, anchor="rm")
    d = [a[0]] + [a[i] - a[i - 1] for i in range(1, N)]
    darr = Array(d, x=640, y=440, cw=96, ch=64, gap=8, size=30)
    ld = label(130, 440, "d", 30, Y, anchor="rm")
    S.show(arr2, la)
    S.say("操作变成：给 a[l..r] 每个数加 x，然后查询某个 a[p]。")
    S.note("问题一：区间加，单点查")
    S.say("维护差分数组 d[i] = a[i] − a[i−1]。那么 a[p] 就是 d 的前缀和：a[p] = d[1] + d[2] + … + d[p]。")
    S.show(darr, ld)
    S.note("d[i] = a[i] − a[i−1]，a[p] = Σ_{k≤p} d[k]", color=Y)
    l, r, x = 3, 6, 2
    S.say(f"给 a[{l}..{r}] 加 {x}：区间内部相邻两数的差不变，只有左端 d[{l}] 多了 {x}，右端外面 d[{r + 1}] 少了 {x}。")
    S.play(*[arr2[i].to(fill=tint(O, 0.35)) for i in range(l, r + 1)], dur=0.4)
    a2 = [a[i] + (x if l <= i + 1 <= r else 0) for i in range(N)]
    d2 = [a2[0]] + [a2[i] - a2[i - 1] for i in range(1, N)]
    S.play(*[arr2.cells[i].to(text=str(a2[i])) for i in range(N)], dur=0.5)
    S.play(darr[l].to(text=str(d2[l - 1]), fill=tint(G, 0.4)), darr[r + 1].to(text=str(d2[r]), fill=tint(R, 0.4)), dur=0.6)
    S.note("a[l..r] += x ⇔ d[l] += x，d[r+1] −= x", color=G)
    S.say("所以区间加变成了 d 上的两次单点加，单点查询变成了 d 的前缀和——正好是树状数组会做的事。对 d 建树状数组就行。")
    S.note("对 d 建树状数组：两次单点加 + 一次前缀和")
    a = a2
    d = d2

    # ------------------------------------------------------------ 区间加 区间和
    S.section("区间加、区间和：两个树状数组")
    S.say("再进一步：区间加，区间求和。区间和可以拆成两个前缀和相减，所以只要会求前缀和 a[1] + … + a[p]。")
    S.note("问题二：区间加，区间求和 → 只要会求 Σ_{i≤p} a[i]")
    S.say("把每个 a[i] 展开成 d 的前缀和，看看 d[k] 一共被加了几次：")
    p = 5
    tri = Grid(p, p, x=480, y=480, cw=74, ch=58, gap=4, size=24, rbase=1, cbase=1,
               rlab=[f"a[{i}]" for i in range(1, p + 1)], clab=[f"d[{k}]" for k in range(1, p + 1)], lab_color=FG)
    for i in range(1, p + 1):
        for k in range(1, p + 1):
            if k > i:
                tri[i, k].tr["op"].base = 0.0
    S.show(tri)
    S.play(*[tri[i, k].to(text="✓", fill=tint(Y, 0.3)) for i in range(1, p + 1) for k in range(1, i + 1)], dur=0.8, lag=0.03)
    S.say(f"以 p = {p} 为例：第 i 行是 a[i] 用到的 d[1..i]。d[k] 出现在第 k 行到第 p 行，一共 p − k + 1 次。")
    S.play(*[tri[i, 2].to(fill=tint(O, 0.5)) for i in range(2, p + 1)], dur=0.6)
    cnt = label(950, 330, f"d[2] 出现 {p} − 2 + 1 = {p - 1} 次", 28, O, anchor="lm")
    S.show(cnt)
    S.note("Σ_{i≤p} a[i] = Σ_{k≤p} d[k] × (p − k + 1)", color=Y)
    S.say("把 (p − k + 1) 拆开：= (p + 1) × Σ d[k]  −  Σ k × d[k]。前一项里 p 和 k 分开了，后一项只和 k 有关。")
    S.note("= (p + 1) × Σ d[k]  −  Σ k·d[k]", color=Y)
    eq = label(950, 430, "(p+1) × Σ d[k] − Σ k·d[k]", 30, Y, anchor="lm")
    S.show(eq)
    S.say("两项都是“前缀和”：一个树状数组维护 d[k]，另一个维护 k·d[k]。区间加时两个数组各改两个点，求和时各查一次前缀。")
    S.note("树状数组 1 存 d[k]，树状数组 2 存 k·d[k]", color=G)
    S.say("核心手法：前缀和里有一个随 p 变化的系数 (p − k + 1)，把它拆成“只和 p 有关”乘“只和 k 有关”的项之和，每一项就都能用树状数组维护。")

    # 演算
    S.play(FadeOut(tri, cnt, eq), dur=0.4)
    arr3 = Array(a, x=640, y=230, cw=96, ch=64, gap=8, size=30)
    darr3 = Array(d, x=640, y=400, cw=96, ch=64, gap=8, size=30)
    kd = [(k + 1) * d[k] for k in range(N)]
    karr3 = Array(kd, x=640, y=560, cw=96, ch=64, gap=8, size=30)
    S.show(arr3, darr3, karr3, label(130, 230, "a", 30, FG, anchor="rm"), label(130, 400, "d", 30, Y, anchor="rm"),
           label(130, 560, "k·d", 30, CY, anchor="rm"), lag=0.05)
    p = 7
    s1 = sum(d[:p])
    s2 = sum(kd[:p])
    S.say(f"核对 p = {p}：Σ d[1..7] = {s1}，Σ k·d[k] = {s2}，(7+1) × {s1} − {s2} = {(p + 1) * s1 - s2}；直接把 a[1..7] 加起来也是 {sum(a[:p])}。")
    S.play(*[darr3.cells[k].to(fill=tint(Y, 0.3)) for k in range(p)], *[karr3.cells[k].to(fill=tint(CY, 0.3)) for k in range(p)],
           *[arr3.cells[k].to(fill=tint(G, 0.3)) for k in range(p)], dur=0.8)

    # ------------------------------------------------------------ 变式与边界
    S.section("变式与边界")
    S.say("变式：给 [l, r] 加一个等差数列 x, x+t, x+2t, …。一阶差分 d 上变成“d[l] 加 x、d[l+1..r] 都加 t、d[r+1] 减掉末项”——仍然是区间加。")
    S.note("加等差数列：一阶差分上是区间加 → 再差分一次（二阶差分）", color=Y)
    S.say("于是再差分一次（二阶差分 e），等差数列加就变成 e 上的几个单点修改。查询时系数变成二次式，再按同样的方法拆开。")
    S.say("边界：树状数组靠“前缀和相减”得到区间信息，要求信息可以相减。区间最大值不能相减，区间赋值也不能写成差分上的少数几次单点修改。")
    S.note("局限：信息要可减（max 不行）；修改要能变成差分上的单点（赋值不行）", color=R)
    S.say("这些情况交给线段树——下一集讲线段树结点里该存什么。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    S.quiz("初始 a 全为 0（n = 8）。操作：在 [3, 6] 上依次加 1, 2, 3, 4（即 a[3] += 1，a[4] += 2，…）。\n\n"
           "(1) 一阶差分 d 变成了什么？二阶差分 e 呢？\n"
           "(2) 一般地，在 [l, r] 上加 1, 2, …, len，e 上要改哪几个点？", think=20)
    av = [0, 0, 1, 2, 3, 4, 0, 0]
    dv = [av[0]] + [av[i] - av[i - 1] for i in range(1, 8)]
    ev = [dv[0]] + [dv[i] - dv[i - 1] for i in range(1, 8)]
    ra = Array(av, x=640, y=440, cw=92, ch=60, gap=8, size=28)
    rd = Array(dv, x=640, y=580, cw=92, ch=60, gap=8, size=28)
    re = Array(ev, x=640, y=720, cw=92, ch=60, gap=8, size=28, index=False)
    S.show(ra, label(160, 440, "a", 28, FG, anchor="rm"))
    S.say("a 变成 0 0 1 2 3 4 0 0。差分 d：区间内部每两个相邻数差 1，左端多 1，右端外面掉回 0，差 −4。")
    S.show(rd, label(160, 580, "d", 28, Y, anchor="rm"))
    S.say("再差分一次得到 e：只有三个位置非零——e[3] = 1，e[7] = −5，e[8] = 4。")
    S.show(re, label(160, 720, "e", 28, CY, anchor="rm"))
    S.play(*[re.cells[i].to(fill=tint(CY, 0.4)) for i in range(8) if ev[i]], dur=0.5)
    S.note("e[l] += 1，e[r+1] −= len + 1，e[r+2] += len", color=Y)
    S.say("一般地：e[l] 加 1，e[r+1] 减 (len + 1)，e[r+2] 加 len。查询 a[p] 是 e 的“二重前缀和”，系数 (p − k + 1)，又回到了两个树状数组。")

    S.recap([
        "树状数组本身只会单点修改、前缀求和；区间操作靠“换一个维护对象”。",
        "区间加单点查：维护差分 d，区间加变成两次单点加，a[p] = d 的前缀和。",
        "区间加区间和：Σ a[i] = (p+1)Σd[k] − Σk·d[k]，用两个树状数组分别维护 d[k] 和 k·d[k]。",
        "等差数列加：再差分一次。局限：信息必须可减，修改必须能化成少数几个单点。",
    ], next_title="线段树的信息设计：结点里存什么才够合并")
