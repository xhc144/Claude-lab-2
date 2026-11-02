"""第 34 集 整体二分：所有询问一起二分"""

from episodes.common import *

A = [5, 1, 4, 2, 7, 3, 6, 8]                       # 下标 1~8
QS = [(2, 6, 3), (1, 8, 6), (4, 8, 2), (1, 3, 3)]  # (l, r, k)：[l, r] 里第 k 小
QC = [CY, O, G, K]
V = 8


def kth(l, r, k):
    return sorted(A[l - 1:r])[k - 1]


def single(l, r, k):
    """单个询问的二分过程：[(L, R, mid, cnt)]。"""
    L, R = 1, V
    steps = []
    while L < R:
        mid = (L + R) // 2
        cnt = sum(1 for x in A[l - 1:r] if x <= mid)
        steps.append((L, R, mid, cnt))
        if cnt >= k:
            R = mid
        else:
            L = mid + 1
    return steps, L


def whole():
    """整体二分，按层记录每个分组：(L, R, mid, 元素下标, [(询问, 计数, 去左?, 新 k)])。"""
    levels = []
    ans = {}

    def solve(L, R, elems, qs, d):
        if not qs:
            return
        if L == R:
            for q, k in qs:
                ans[q] = L
            return
        mid = (L + R) // 2
        ins = [p for p in elems if A[p - 1] <= mid]
        res, lq, rq = [], [], []
        for q, k in qs:
            l, r, _ = QS[q]
            c = sum(1 for p in ins if l <= p <= r)
            if c >= k:
                res.append((q, c, True, k, k))
                lq.append((q, k))
            else:
                res.append((q, c, False, k, k - c))
                rq.append((q, k - c))
        while len(levels) <= d:
            levels.append([])
        levels[d].append((L, R, mid, ins, res))
        solve(L, mid, ins, lq, d + 1)
        solve(mid + 1, R, [p for p in elems if A[p - 1] > mid], rq, d + 1)

    solve(1, V, list(range(1, len(A) + 1)), [(i, q[2]) for i, q in enumerate(QS)], 0)
    return levels, ans


def build(S):
    S.cover("很多个询问“区间 [l, r] 里第 k 小的数”。一个询问可以二分答案，可每次检查都要扫一遍区间——能不能让所有询问共用同一次检查？",
            ["二分答案", "树状数组（第 13 集）", "CDQ 分治（第 33 集）"])

    levels, ans = whole()
    for i, (l, r, k) in enumerate(QS):
        assert ans[i] == kth(l, r, k)

    # ------------------------------------------------------------ 单个询问
    S.section("一个询问：二分答案")
    arr = Array(A, x=560, y=290, cw=84, ch=70, gap=10, size=32)
    S.show(arr, label(560, 190, "序列 A", 26, DIM))
    l, r, k = QS[0]
    fr = arr.frame(l, r, CY)
    S.play(FadeIn(fr), dur=0.4)
    S.say(f"询问：[{l}, {r}] 里第 {k} 小的数是多少？区间里是 {', '.join(map(str, A[l - 1:r]))}，排好序第 {k} 个是 {kth(l, r, k)}。")
    S.note(f"询问 [l, r] 第 k 小（例：[{l}, {r}] 第 {k} 小）")
    S.say("不排序也能求：猜一个答案 mid，数一数区间里 ≤ mid 的有几个，记作 cnt。cnt ≥ k 说明答案 ≤ mid，否则答案 > mid。")
    S.note("猜 mid，数 cnt = #{ x ≤ mid }：cnt ≥ k ⇔ 答案 ≤ mid", color=Y)
    vl = Array(list(range(1, V + 1)), x=560, y=600, cw=64, ch=54, gap=8, size=26, index=False,
               fill=tint(Y, 0.12))
    S.show(vl, label(560, 530, "答案可能的取值", 24, DIM))
    vf = vl.frame(1, V, Y)
    S.play(FadeIn(vf), dur=0.4)
    cnt_t = label(560, 410, "", 28, Y)
    S.add(cnt_t)
    steps, res = single(l, r, k)
    mp = vl.ptr(1, "mid", Y)
    first = True
    for (lo, hi, mid, cnt) in steps:
        cells = [arr[i].to(fill=tint(G, 0.45) if A[i - 1] <= mid else BG3) for i in range(l, r + 1)]
        S.play(*([FadeIn(mp)] if first else []), vl.move(mp, mid),
               *cells, cnt_t.to(text=f"mid = {mid}：区间里 ≤ {mid} 的有 {cnt} 个"), dur=0.6)
        first = False
        if cnt >= k:
            S.say(f"mid = {mid}：cnt = {cnt} ≥ {k}，第 {k} 小不会超过 {mid}，范围缩到 [{lo}, {mid}]。")
            S.play(vl.reframe(vf, lo, mid), *[vl[v].to(fill=BG3, tc=FAINT) for v in range(mid + 1, hi + 1)], dur=0.6)
        else:
            S.say(f"mid = {mid}：cnt = {cnt} < {k}，≤ {mid} 的数不够 {k} 个，答案 > {mid}，范围缩到 [{mid + 1}, {hi}]。")
            S.play(vl.reframe(vf, mid + 1, hi), *[vl[v].to(fill=BG3, tc=FAINT) for v in range(lo, mid + 1)], dur=0.6)
    S.play(vl[res].to(fill=tint(G, 0.55), stroke=G, sw=3), cnt_t.to(text=f"答案 = {res}"), dur=0.6)
    S.say(f"范围只剩 {res}，答案就是 {res}。值域大小为 V，要检查 log V 次，每次扫一遍区间。")
    S.say("q 个询问各二分一遍：O(q · n log V)。慢在每个询问都要单独检查，而不同询问的检查其实在做同一件事。")
    S.note("单独二分：每个询问 O(n log V)，共 O(q · n log V)", color=R)

    # ------------------------------------------------------------ 一起二分
    S.section("所有询问一起二分")
    S.say("把所有询问放在一起：开始时它们的答案范围都是 [1, 8]，猜的 mid 也都是 4。“哪些数 ≤ 4”对每个询问都一样，只需要准备一次。")
    arr2 = Array(A, x=420, y=262, cw=70, ch=60, gap=8, size=28)
    S.show(arr2, label(420, 172, "序列 A（格子下面是下标）", 22, DIM))
    names = [f"Q{i + 1}" for i in range(len(QS))]
    tab = Grid(len(QS), 4, x=420, y=640, cw=140, ch=50, gap=4, size=24,
               vals=[[f"{{{'cogk'[i]}|{names[i]}}}", f"[{q[0]}, {q[1]}]", q[2], "[1, 8]"] for i, q in enumerate(QS)],
               clab=["询问", "区间", "k", "答案范围"])
    S.show(tab)
    # 右侧：值域的递归树，询问用小圆点表示
    xv = {v: 818 + (v - 1) * 62 for v in range(1, V + 1)}
    ylv = [170, 268, 366, 464]
    rng_box = {}
    tree = Group(0, 0)
    spans = [[(1, 8)], [(1, 4), (5, 8)], [(1, 2), (3, 4), (5, 6), (7, 8)], [(v, v) for v in range(1, 9)]]
    for d, row in enumerate(spans):
        for a, b in row:
            w = xv[b] - xv[a] + 56
            bx = Rect((xv[a] + xv[b]) / 2, ylv[d], w, 50, fill=BG3, stroke=LINE, sw=1.5, r=10)
            bx.add(Text(0, 0, f"[{a}, {b}]" if a != b else str(a), size=22, color=FG))
            tree.add(bx)
            rng_box[(a, b)] = bx
    S.show(tree, label(1035, 120, "答案范围（值域）的二分", 22, DIM))
    tokens = []
    tg = Group(0, 0)
    for i in range(len(QS)):
        t = token(tg, 1035 + (i - 1.5) * 34, ylv[0] + 46, QC[i], r=15, label=str(i + 1))
        tokens.append(t)
    S.add(tg)
    S.play(*[FadeIn(t) for t in tokens], rng_box[(1, 8)].to(stroke=Y, sw=2.5), dur=0.5)
    S.note("所有询问共用 mid：把 ≤ mid 的数按下标放进树状数组")

    # 第一层，逐个询问细讲
    lo, hi, mid, ins, res0 = levels[0][0]
    S.say(f"mid = {mid}：把值 ≤ {mid} 的数（绿色）按下标加进树状数组。之后每个询问只要查一次区间和，就知道 [l, r] 里有几个 ≤ {mid}。")
    S.play(*[arr2[p].to(fill=tint(G, 0.45)) for p in ins], dur=0.6)
    qfr = arr2.frame(1, 1, CY)
    info = label(420, 400, "", 26, FG)
    S.add(info)
    for j, (q, c, left, k, nk) in enumerate(res0):
        l, r, _ = QS[q]
        S.play(*([FadeIn(qfr)] if j == 0 else []), qfr.to(stroke=QC[q]), arr2.reframe(qfr, l, r),
               tab[q, 0].to(stroke=QC[q], sw=3), dur=0.5)
        if left:
            S.play(info.to(text=f"{names[q]}：[{l}, {r}] 里 ≤ {mid} 的有 {c} 个 ≥ k = {k} → 答案在 [{lo}, {mid}]"),
                   tab[q, 3].to(text=f"[{lo}, {mid}]"), dur=0.5)
        else:
            S.play(info.to(text=f"{names[q]}：只有 {c} 个 < k = {k} → 答案在 [{mid + 1}, {hi}]，k 变成 {nk}"),
                   tab[q, 3].to(text=f"[{mid + 1}, {hi}]"), tab[q, 2].to(text=str(nk), fill=tint(O, 0.4)), dur=0.5)
        if q == 1:
            S.say(f"注意 Q2：[1, 8] 里 ≤ {mid} 的已经有 {c} 个，答案是剩下的数里第 {k} − {c} = {nk} 小。往右走时，k 要减去左边已经数过的个数。")
            S.note("去右边：k ← k − cnt（≤ mid 的那些数以后不再出现）", color=O)
        else:
            S.wait(1.4)
        S.play(tab[q, 0].to(stroke=LINE, sw=2), dur=0.2)
    S.play(FadeOut(qfr), info.to(text=""), dur=0.4)

    # 分组：元素和询问一起分到两边
    S.say("然后把元素和询问一起分成两组：值 ≤ 4 的数和答案在 [1, 4] 的询问去左边，其余去右边。两组互不相干，各自递归。")
    S.note("元素按值分、询问按答案范围分，两组分别递归", color=Y)
    lefts = [q for q, c, lf, k0, nk in res0 if lf]
    rights = [q for q, c, lf, k0, nk in res0 if not lf]

    def place(groups, d):
        out = []
        for rng, qs in groups:
            cx = (xv[rng[0]] + xv[rng[1]]) / 2
            for j, q in enumerate(qs):
                out.append(tokens[q].to(x=cx + (j - (len(qs) - 1) / 2) * 34, y=ylv[d] + 46))
        return out

    S.play(*place([((1, 4), lefts), ((5, 8), rights)], 1),
           *[arr2[p].to(fill=tint(CY, 0.3)) for p in ins],
           *[arr2[p].to(fill=tint(O, 0.3)) for p in range(1, 9) if p not in ins],
           rng_box[(1, 8)].to(stroke=LINE, sw=1.5), rng_box[(1, 4)].to(stroke=CY, sw=2.5),
           rng_box[(5, 8)].to(stroke=O, sw=2.5), dur=0.9)
    S.say("左组只剩值在 [1, 4] 的数，右组只剩 [5, 8] 的数。下一层两组各自取自己的 mid，再做一遍同样的事。")

    # 后面几层：每组一次插入、每个询问一次查询
    for d in range(1, len(levels)):
        groups = []
        for (lo, hi, mid, ins, res) in levels[d]:
            gcol = CY if lo <= 4 else O
            S.play(rng_box[(lo, hi)].to(stroke=Y, sw=3), *[arr2[p].to(stroke=Y, sw=3) for p in ins], dur=0.5)
            parts = []
            for (q, c, left, k, nk) in res:
                if left:
                    parts.append(f"{names[q]} 数到 {c} ≥ {k}，去 [{lo}, {mid}]")
                else:
                    parts.append(f"{names[q]} 数到 {c} < {k}，去 [{mid + 1}, {hi}]，k = {nk}")
            S.say(f"范围 [{lo}, {hi}]，mid = {mid}，加入值 ≤ {mid} 的 {len(ins)} 个数。" + "；".join(parts) + "。")
            upd = []
            for (q, c, left, k, nk) in res:
                rng = (lo, mid) if left else (mid + 1, hi)
                upd.append(tab[q, 3].to(text=f"[{rng[0]}, {rng[1]}]" if rng[0] != rng[1] else f"{{y|{rng[0]}}}"))
                if not left:
                    upd.append(tab[q, 2].to(text=str(nk)))
            S.play(*upd, dur=0.5)
            S.play(rng_box[(lo, hi)].to(stroke=gcol, sw=2), *[arr2[p].to(stroke=LINE, sw=2) for p in ins], dur=0.3)
            lq = [q for q, c, lf, k, nk in res if lf]
            rq = [q for q, c, lf, k, nk in res if not lf]
            groups += [((lo, mid), lq), ((mid + 1, hi), rq)]
        S.play(*place([g for g in groups if g[1]], d + 1),
               *[rng_box[g[0]].to(stroke=Y, sw=2) for g in groups if g[1] and g[0][0] == g[0][1]], dur=0.8)
    S.play(*[tab[q, 3].to(fill=tint(G, 0.35)) for q in range(len(QS))], dur=0.5)
    S.say("所有范围都缩成一个数：" + "，".join(f"{names[q]} = {ans[q]}" for q in range(len(QS)))
          + "。和直接排序求出的结果一致。")
    S.note("答案：" + "，".join(f"{names[q]} = {ans[q]}" for q in range(len(QS))), color=G)

    # ------------------------------------------------------------ 复杂度
    S.section("为什么快：每一层只看一遍", keep=[tree, tg])
    S.say("看值域那棵树：同一层的各组，值域互不重叠。每个数只落在一组里，每个询问也只落在一组里。")
    for d in range(3):
        S.play(*[rng_box[s].to(fill=tint(Y, 0.25)) for s in spans[d]], dur=0.4)
        S.wait(0.3)
        S.play(*[rng_box[s].to(fill=BG3) for s in spans[d]], dur=0.3)
    S.note("同一层：每个数、每个询问只在一组里", color=Y)
    S.say("一组的花费是 O((组里的数 + 组里的询问) · log n)：插入树状数组、查询区间和。所以一层合计 O((n + q) log n)。")
    S.say("值域每层减半，一共 log V 层。总复杂度 O((n + q) log n log V)，和询问个数基本无关地“摊”掉了检查。")
    S.note("每层 O((n + q) log n)，共 log V 层 → O((n + q) log n log V)", color=G)
    S.say("细节：一组做完要把树状数组还原。不能整个清空（那是 O(n)，组数一多就超时），只撤销自己加进去的那些位置。", extra=0.3)
    S.note("还原树状数组：只撤销本组加过的位置", color=R)

    # ------------------------------------------------------------ 适用条件
    S.section("什么时候能整体二分")
    S.say("条件一：每个询问的答案单独可以二分——“答案 ≤ mid”这件事关于 mid 单调。")
    S.note("① 每个询问单独可二分（判定单调）")
    S.say("条件二：同一个 mid 的判定可以批量做——先把“贡献”一次性加进数据结构，再让每个询问各查一次。")
    S.note("② 判定可以批量：先加贡献，询问各查一次")
    S.say("条件三：贡献可以拆开、可以累加。去右边时 k 减去左边的计数，靠的就是“≤ mid 的贡献”可以单独算出来再减掉。")
    S.note("③ 贡献可累加：去右边时减掉左半的贡献")
    S.say("带修改的第 k 小也能做：把“改一个数”拆成“删掉旧值、加入新值”两个事件，和询问一起按时间排好，按值分组时事件也分到两边。", extra=0.3)
    S.note("带修改：修改拆成删旧值 + 加新值，按时间顺序一起分组", color=DIM)
    S.say("和 CDQ 分治对照：CDQ 对“时间”分治、算左半对右半的贡献；整体二分对“答案”分治、把询问和贡献按答案分到两边。", extra=0.5)

    # ------------------------------------------------------------ 手推题
    S.quiz("n 个人，第 i 个人的目标是 pᵢ。一共 m 天，第 t 天给编号在 [lₜ, rₜ] 里的每个人加 aₜ（aₜ > 0）。\n"
           "求每个人最早在第几天，累计值达到自己的目标（到最后都达不到就输出 −1）。\n\n"
           "(1) 只问一个人，怎么二分？\n"
           "(2) 整体二分时，mid 表示什么？一组里做什么？人怎样分到两边？", think=20)
    S.say("(1) 答案是天数，可以二分：做完前 mid 天的操作后，第 i 个人的累计值 ≥ pᵢ，答案就 ≤ mid。累计值随天数只增不减，判定单调。")
    S.note("(1) 二分天数 mid：前 mid 天做完后累计 ≥ pᵢ？（单调）", color=Y)
    S.say("(2) mid 是天数。一组的答案范围是 [L, R]：把第 L～mid 天的区间加做进树状数组（区间加、单点查），每个人查自己的累计 s。")
    S.say("s ≥ p 的人去左边 [L, mid]；其余的人把目标减成 p − s，去右边 [mid + 1, R]——和第 k 小里的 k − cnt 是一回事。")
    S.note("(2) 组 [L, R]：做第 L～mid 天；s ≥ p 去左，否则 p ← p − s 去右", color=G)
    S.say("答案范围设成 [1, m + 1]，落在 m + 1 的就是达不到。复杂度 O((n + m) log n log m)。", extra=0.5)
    S.note("答案范围 [1, m + 1]：m + 1 表示 −1；O((n + m) log n log m)")

    S.recap([
        "单个询问可以二分答案；很多询问一起二分时，同一个 mid 的贡献只准备一次，每个询问各查一次。",
        "元素按值、询问按答案范围分到左右两组；去右边的询问要减掉左半的贡献（k ← k − cnt）。",
        "同一层里每个元素、每个询问只在一组中，共 log V 层：O((n + q) log n log V)；数据结构要撤销而不是清空。",
        "条件：判定单调、可以批量判定、贡献可累加。带修改时把修改拆成删除和插入事件一起分组。",
    ], next_title="可撤销并查集与线段树分治")
