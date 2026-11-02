"""第 4 集 背包变式（下）：依赖关系——分组与树形背包"""

from episodes.common import *

GROUPS = {"甲": [(2, 3), (3, 4)], "乙": [(2, 2), (4, 5)]}
CAP = 5

EDGES = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (4, 6)]
CREDIT = {0: 0, 1: 2, 2: 3, 3: 1, 4: 1, 5: 2, 6: 5}
M = 4


def group_dp(correct=True):
    f = [0] * (CAP + 1)
    for items in GROUPS.values():
        if correct:
            for j in range(CAP, -1, -1):
                for w, v in items:
                    if j >= w:
                        f[j] = max(f[j], f[j - w] + v)
        else:
            for w, v in items:
                for j in range(CAP, w - 1, -1):
                    f[j] = max(f[j], f[j - w] + v)
    return f


def tree_dp(edges, credit, root=0):
    ch = {}
    for p, c in edges:
        ch.setdefault(p, []).append(c)
    steps = []   # (u, v, 合并前的 f[u], f[v], 合并后的 f[u])
    f = {}

    def dfs(u):
        cur = [0, credit[u]]          # f[u][j]：子树里选 j 个（含 u）
        for v in ch.get(u, []):
            dfs(v)
            fv = f[v]
            new = [None] * (len(cur) + len(fv) - 1)
            for a, x in enumerate(cur):
                if x is None:
                    continue
                for b, y in enumerate(fv):
                    if y is None or (a == 0 and b > 0):
                        continue      # 没选 u 就不能选 u 子树里的点
                    if new[a + b] is None or x + y > new[a + b]:
                        new[a + b] = x + y
            steps.append((u, v, cur, fv, new))
            cur = new
        f[u] = cur

    dfs(root)
    return f, steps


def fmt(arr):
    return "[" + ", ".join("−" if x is None else str(x) for x in arr) + "]"


def build(S):
    S.cover("物品之间有依赖：同一组只能选一个；买附件必须先买主件；选课必须先选先修课。背包该怎么改？",
            ["0/1 背包与一维写法（第 3 集）", "树的 DFS"])

    # ------------------------------------------------------------ 分组背包
    S.section("分组背包：组内互斥")
    S.say("先看最简单的依赖：物品分成若干组，{y|每组最多选一个}。容量 5，两组物品如下。")
    S.note("分组背包：每组最多选一件")
    boxes = []
    x = 330
    for name, items in GROUPS.items():
        b = Rect(x, 330, 360, 190, fill=BG3, stroke=LINE, sw=2, r=14)
        t = label(x, 255, f"{name}组", 28, DIM)
        cs = [Cell(x - 85 + 170 * k, 350, 150, 80, f"体积{w} 价值{v}", 24, fill=tint(CY if name == "甲" else O, 0.3),
                   stroke=CY if name == "甲" else O) for k, (w, v) in enumerate(items)]
        boxes.append((b, t, cs))
        x += 470
    for b, t, cs in boxes:
        S.show(b, t, *cs, lag=0.05)
    S.say("把“一组”看成一个物品，它有好几种“形态”（不选、选第一件、选第二件……）。对每个容量，在这些形态里挑最好的。")
    S.note("一组 = 一个有多种形态的物品")
    S.note("顺序：组 → 容量（倒序）→ 组内物品", color=Y)
    fc = group_dp(True)
    fw = group_dp(False)
    ac = Array(fc, x=420, y=620, cw=92, ch=66, gap=6, size=30, base=0)
    aw = Array([0] * (CAP + 1), x=420, y=620, cw=92, ch=66, gap=6, size=30, base=0)
    lc = label(420, 545, "正确顺序：容量在外、组内物品在内", 26, G)
    S.say("容量在外、物品在内：算 f[j] 时，组内所有物品都从同一个旧的 f 转移过来，所以只会选其中一件。")
    S.show(ac, lc)
    S.play(ac[CAP].flash(G), dur=0.7)
    S.say(f"结果 f[5] = {fc[CAP]}：甲组选体积 3 价值 4，乙组选体积 2 价值 2。")
    S.say("如果把两层循环写反（物品在外、容量在内），每件物品就各自成了一个 0/1 物品，同一组的两件可能都被选上。")
    lw = label(1010, 545, "写反：物品在外、容量在内", 26, R)
    aw.tr["x"].base = 1010
    S.show(aw, lw)
    S.play(*[aw.cells[j].to(text=str(fw[j])) for j in range(CAP + 1)], dur=0.6)
    S.play(aw[CAP].to(fill=tint(R, 0.35)), dur=0.3)
    S.play(aw[CAP].flash(R), dur=0.7)
    S.say(f"写反后 f[5] = {fw[CAP]}：甲组的体积 2 和体积 3 被同时选中，违反了“组内最多一件”。")
    S.note(f"写反：f[5] = {fw[CAP]}（甲组选了两件）✗", color=R)
    S.say("和上一集一样：循环顺序决定了“读到的是不是旧值”。这里要保证同一组的所有选择都读旧值。", extra=0.5)

    # ------------------------------------------------------------ 主件附件
    S.section("主件与附件")
    S.say("第二种依赖：买附件必须先买它的主件，每个主件最多两个附件（“金明的预算方案”）。")
    S.note("附件依赖主件；一个主件 ≤ 2 个附件")
    main = Cell(380, 300, 150, 76, "主件", 28, fill=tint(Y, 0.3), stroke=Y)
    a1 = Cell(250, 470, 150, 76, "附件 1", 26, fill=tint(CY, 0.25), stroke=CY)
    a2 = Cell(510, 470, 150, 76, "附件 2", 26, fill=tint(CY, 0.25), stroke=CY)
    e1 = Line(380, 338, 250, 432, color=LINE, w=3)
    e2 = Line(380, 338, 510, 432, color=LINE, w=3)
    S.show(e1, e2, main, a1, a2, lag=0.08)
    S.say("一个主件和它的附件组成一个“家族”。家族内部能选的方案只有这几种，而且互相排斥：")
    opts = ["不买", "只买主件", "主件 + 附件 1", "主件 + 附件 2", "主件 + 两个附件"]
    ot = [Cell(980, 210 + 92 * k, 380, 72, s, 26, fill=BG3, stroke=LINE) for k, s in enumerate(opts)]
    S.show(*ot, lag=0.1)
    S.say("“不买”之外的 4 种方案各算一个物品，正好构成一组——问题变成了分组背包。不同家族之间互不影响。")
    S.play(*[c.to(stroke=Y, fill=tint(Y, 0.18)) for c in ot[1:]], dur=0.6)
    S.note("一个家族 → 一组：{主}、{主+附1}、{主+附2}、{主+附1+附2}", color=Y)
    S.say("这种做法的前提是：一个家族里的方案数很少。附件越多，方案是 2^k 级别；附件还有自己的附件时更不行。")
    S.note("前提：家族内方案少（2^k）", color=DIM)

    # ------------------------------------------------------------ 树形依赖
    S.section("树形依赖：选课")
    S.say("一般的依赖形成一棵树：要选一门课，必须先选它的先修课。从 6 门课里选 4 门，学分最多是多少？")
    S.note("选课：选 u 必须先选父亲；选 m 门，学分最大")
    tree = Tree(EDGES, 0, x=300, y=480, w=400, h=440, r=30, size=26, labels={0: "根"})
    S.show(tree)
    tags = {}
    for v in range(1, 7):
        tags[v] = tree.tag(v, f"{CREDIT[v]}分", "l", DIM, 22)
    S.play(*[FadeIn(t) for t in tags.values()], dur=0.5)
    S.say("加一个虚拟的根（0 学分）把森林连成一棵树。贪心先选学分高的可选课程，只能得到 8 分。")
    S.note("虚拟根 0：把森林连成树")
    S.say("因为 5 分的第 6 门课藏在只有 1 分的第 4 门课后面。要把整棵子树一起考虑。")
    S.play(tree[6].flash(Y), tree[4].flash(DIM), dur=0.8)
    S.say("状态：f[u][j] = 在 u 的子树里选 j 门课（u 自己必须选，除非 j = 0）时的最大学分。")
    S.note("{y|f[u][j]}：u 的子树里选 j 个（含 u），最大学分", color=Y)
    S.say("怎么算 f[u]？先只有 u 自己：f[u] = [0, 学分(u)]。然后把儿子一个一个“并”进来。")
    S.say("并儿子 v 时，v 的子树就是一个分组：可以从中选 0 个、1 个……size(v) 个，价值是 f[v][k]，这些选择互斥。")
    S.note("并儿子 v：v 的子树 = 一组，选 k 个的价值 f[v][k]")
    S.note("f[u][j] ← max over k：f[u][j−k] + f[v][k]", color=Y)

    f, steps = tree_dp(EDGES, CREDIT)
    rows = {}
    nrow = [0]

    def frow(v, arr):
        if v not in rows:
            t = label(640, 190 + 52 * nrow[0], "", 26, CY, anchor="lm", chain="mono")
            nrow[0] += 1
            rows[v] = t
            S.add(t)
        return rows[v].to(text=f"f[{v}] = {fmt(arr)}")

    done = set()
    detailed = {(1, 4), (0, 2)}
    for (u, v, before, fv, after) in steps:
        if v not in done and not [s_ for s_ in steps if s_[0] == v]:
            S.play(frow(v, f[v]), tree[v].to(stroke=CY), dur=0.4)
            done.add(v)
        if (u, v) in detailed:
            if (u, v) == (1, 4):
                S.say(f"例：结点 1 已经并了儿子 3，f[1] = {fmt(before)}；现在并入儿子 4，f[4] = {fmt(fv)}。")
            else:
                S.say(f"最后在根上：已并入儿子 1，f[0] = {fmt(before)}；再并入儿子 2，f[2] = {fmt(fv)}。")
            S.play(frow(u, before), tree[u].to(stroke=Y, sw=4), tree.edge(u, v).to(color=Y, w=5), dur=0.5)
            box_ = Rect(950, 700, 620, 250, fill=C.BG2, stroke=alpha(Y, 0.8), sw=2.5, r=14)
            S.show(box_, dur=0.3)
            target = 3 if (u, v) == (1, 4) else 5
            cand = []
            for k, y in enumerate(fv):
                a_ = target - k
                if 0 <= a_ < len(before) and before[a_] is not None and not (a_ == 0 and k > 0):
                    cand.append((k, before[a_], y))
            lines = [f"算 f[{u}][{target}]："] + [f"k={k}：f[{u}][{target - k}] + f[{v}][{k}] = {x} + {y} = {x + y}"
                                                for k, x, y in cand]
            rows_ = []
            for i, s_ in enumerate(lines):
                t = label(670, 610 + 46 * i, s_, 25, FG if i else Y, anchor="lm")
                rows_.append(t)
            S.play(*[FadeIn(t, dx=-10) for t in rows_], dur=0.5, lag=0.25)
            best = max(c[1] + c[2] for c in cand)
            S.say(f"枚举从儿子子树里拿几个（k），其余从已并入的部分拿。最大是 {best}。")
            S.play(frow(u, after), dur=0.5)
            S.wait(1.0)
            S.play(FadeOut(box_, *rows_), tree[u].to(stroke=CY, sw=2.5), tree.edge(u, v).to(color=C.LINE2, w=3), dur=0.4)
        else:
            S.play(frow(u, after), tree[u].to(stroke=CY), tree.edge(u, v).to(color=CY), dur=0.5)
            S.play(tree.edge(u, v).to(color=C.LINE2), dur=0.2)
    ans = f[0][M + 1]
    S.say(f"根要算上自己，所以答案是 f[0][{M + 1}] = {ans}：选 1、4、6 和 2。")
    S.note(f"答案 f[0][m+1] = {ans}", color=G)
    S.play(*[tree[v].to(fill=tint(G, 0.35)) for v in (1, 4, 6, 2)], dur=0.6)

    # ------------------------------------------------------------ 复杂度
    S.section("合并的总代价为什么是 O(n²)")
    S.wide()
    S.say("每次合并要枚举 j 和 k，看上去像 O(n²)，n 个结点合起来岂不是 O(n³)？")
    S.say("关键：枚举时 j 不超过“已并入部分的大小” s1，k 不超过“儿子子树的大小” s2。一次合并的代价是 s1 × s2。")
    left = Group(620, 460)
    right = Group(1300, 460)
    lp = [(-120, -80), (-40, -120), (40, -70), (-90, 20), (10, 30), (90, 10), (-30, 110)]
    rp = [(-60, -60), (40, -90), (-20, 30), (70, 40), (0, 120)]
    ld = [left.add(Circle(x, y, 16, fill=tint(CY, 0.6), stroke=CY)) for x, y in lp]
    rd = [right.add(Circle(x, y, 16, fill=tint(O, 0.6), stroke=O)) for x, y in rp]
    lt = label(620, 290, f"已并入的部分：s1 = {len(lp)} 个点", 28, CY)
    rt = label(1300, 290, f"儿子子树：s2 = {len(rp)} 个点", 28, O)
    S.show(left, right, lt, rt, lag=0.1)
    pairs = []
    for i, (x1, y1) in enumerate(lp):
        for j, (x2, y2) in enumerate(rp):
            ln = Line(620 + x1, 460 + y1, 1300 + x2, 460 + y2, color=alpha(Y, 0.35), w=1.5)
            ln.tr["op"].base = 0
            pairs.append(ln)
    S.say(f"s1 × s2 恰好等于“左边一个点、右边一个点”的点对个数：{len(lp)} × {len(rp)} = {len(lp) * len(rp)} 对。")
    S.play(*[FadeIn(p) for p in pairs], dur=1.2, lag=0.01)
    S.say("把每次合并的代价都换成“点对”：这一次合并，数的是一端在左、一端在右的点对，它们的 LCA 正是当前结点 u。")
    S.say("每一对点 (x, y) 只会在它们的 LCA 处、x 和 y 第一次被并到一起时被数一次。之后它们已在同一边，不会再被数。")
    S.note_space()
    S.say("所以所有合并的代价之和 ≤ 点对总数 = n(n−1)/2，整个树形背包是 O(n²)。")
    tot = label(960, 760, "Σ s1 × s2 ≤ 点对总数 = n(n−1)/2 = O(n²)", 34, Y)
    S.show(tot)
    S.say("如果还限制最多选 m 个（j、k 都不超过 m），同样的论证可以证明总代价是 O(nm)。前提是循环上界写成 min(大小, m)。", extra=0.5)
    S.say("反过来，如果每次都把 j、k 枚举到 m 而不看子树大小，代价就退化成 O(n × m²)。上界写法直接决定复杂度。")
    S.play(FadeOut(*pairs), dur=0.4)

    # ------------------------------------------------------------ 手推题
    S.narrow()
    S.quiz("一棵树：根 r（学分 0，必须选）有两个儿子 a（3 分）、b（1 分）；b 有两个儿子 c（4 分）、d（2 分）。\n"
           "选课必须先选先修课。除根以外选 2 门，最多多少分？\n\n"
           "请写出 f[b]，再在根上合并 f[a] 与 f[b]。", think=20)
    q_edges = [("r", "a"), ("r", "b"), ("b", "c"), ("b", "d")]
    q_credit = {"r": 0, "a": 3, "b": 1, "c": 4, "d": 2}
    qf, qsteps = tree_dp(q_edges, q_credit, "r")
    qt = Tree(q_edges, "r", x=330, y=600, w=360, h=220, r=26, size=24)
    S.show(qt)
    for v in "abcd":
        t = qt.tag(v, f"{q_credit[v]}分", "l", DIM, 20)
        S.play(FadeIn(t), dur=0.2)
    S.say(f"f[c] = {fmt(qf['c'])}，f[d] = {fmt(qf['d'])}。b 先只有自己 [0, 1]，并入 c 得 [0, 1, 5]，再并入 d 得 {fmt(qf['b'])}。")
    S.note(f"f[b] = {fmt(qf['b'])}")
    S.say(f"根：先是 [0, 0]；并入 a（{fmt(qf['a'])}）得 [0, 0, 3]；再并入 b 得 {fmt(qf['r'])}。")
    S.note(f"f[r] = {fmt(qf['r'])}")
    S.say(f"选 2 门（加上根是 3 个点）：f[r][3] = {qf['r'][3]}。方案是 b 和 c：4 分的 c 必须先选 1 分的 b，仍然比 a + b 的 4 分好。")
    S.note(f"答案 {qf['r'][3]}（选 b、c）", color=Y)
    S.play(qt["b"].to(fill=tint(G, 0.4)), qt["c"].to(fill=tint(G, 0.4)), dur=0.6)

    S.recap([
        "分组背包：容量在外、组内物品在内，保证同一组的选择都从旧值转移，最多选一件。",
        "主件附件：一个家族的几种方案互斥 → 一组；前提是家族内方案数很少。",
        "树形依赖：f[u][j] 是 u 子树里选 j 个；把儿子子树当成一组，逐个合并：f[u][j] ← f[u][j−k] + f[v][k]。",
        "循环上界取已并入大小和儿子子树大小时，合并代价 s1 × s2 = 新产生的点对数，总共 O(n²)（限 m 个时 O(nm)）。",
    ], next_title="区间 DP 建模（上）：枚举最后一步——石子合并")
