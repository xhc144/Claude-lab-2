"""第 53 集 2-SAT：蕴含图与强连通分量"""

from itertools import product

from episodes.common import *

NV = 3
# 文字：(变量, 是否取反)；子句 (a ∨ b)
CLAUSES = [((1, False), (2, False)), ((1, True), (3, False)), ((2, True), (3, True)), ((3, True), (2, False))]
QCLAUSES = [((1, False), (2, True)), ((1, True), (2, True)), ((2, False), (3, False)), ((1, False), (3, True))]


def lit_name(l):
    v, neg = l
    return ("¬" if neg else "") + f"x{v}"


def node(l):
    v, neg = l
    return 2 * (v - 1) + (1 if neg else 0)


def neg(l):
    return (l[0], not l[1])


def implication_edges(clauses):
    E = []
    for a, b in clauses:
        E.append((neg(a), b))
        E.append((neg(b), a))
    return E


def tarjan(nv, E):
    n = 2 * nv
    adj = {i: [] for i in range(n)}
    for a, b in E:
        adj[node(a)].append(node(b))
    idx, low, on, st = {}, {}, set(), []
    comp = {}
    cnt = [0, 0]

    def dfs(v):
        idx[v] = low[v] = cnt[0]
        cnt[0] += 1
        st.append(v)
        on.add(v)
        for w in adj[v]:
            if w not in idx:
                dfs(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            while True:
                w = st.pop()
                on.discard(w)
                comp[w] = cnt[1]
                if w == v:
                    break
            cnt[1] += 1

    for v in range(n):
        if v not in idx:
            dfs(v)
    return comp


def solve(nv, clauses):
    comp = tarjan(nv, implication_edges(clauses))
    if any(comp[node((v, False))] == comp[node((v, True))] for v in range(1, nv + 1)):
        return None, comp
    # Tarjan 先完成的分量在拓扑序靠后：x 的分量编号更小（更靠后）就取 x 为真
    return {v: comp[node((v, False))] < comp[node((v, True))] for v in range(1, nv + 1)}, comp


def check(nv, clauses, asg):
    val = lambda l: asg[l[0]] != l[1]       # noqa: E731
    return all(val(a) or val(b) for a, b in clauses)


def brute(nv, clauses):
    return [dict(zip(range(1, nv + 1), bits)) for bits in product((False, True), repeat=nv)
            if check(nv, clauses, dict(zip(range(1, nv + 1), bits)))]


def build(S):
    S.cover("有 n 个布尔变量和很多条“两个里至少满足一个”的限制，能不能同时满足？一般的可满足性问题很难，可每条限制只涉及两个变量时，它能变成一张图上的强连通分量问题。",
            ["强连通分量（第 25 集）", "缩点之后（第 26 集）"])

    asg, comp = solve(NV, CLAUSES)
    assert asg is not None and check(NV, CLAUSES, asg)
    assert asg in brute(NV, CLAUSES)

    # ------------------------------------------------------------ 子句
    S.section("子句变成蕴含")
    cl_t = [label(160, 230 + 62 * k, f"({lit_name(a)} ∨ {lit_name(b)})", 32, FG, anchor="lm") for k, (a, b) in enumerate(CLAUSES)]
    S.show(*cl_t, dur=0.6, lag=0.12)
    S.say(f"{NV} 个变量 x₁、x₂、x₃，{len(CLAUSES)} 条子句，每条形如 (a ∨ b)：a、b 是某个变量或它的否定，至少有一个为真。")
    S.note("2-SAT：每条子句 (a ∨ b)，两个文字至少一个为真", color=Y)
    S.say("关键转化：(a ∨ b) 等价于两句“如果……就……”：如果 a 为假，b 必须为真；如果 b 为假，a 必须为真。")
    S.note("(a ∨ b) ⇔ (¬a → b) 且 (¬b → a)", color=G)
    imp = implication_edges(CLAUSES)
    imp_t = [label(620, 230 + 62 * k, f"{lit_name(neg(a))} → {lit_name(b)}，{lit_name(neg(b))} → {lit_name(a)}", 30, CY, anchor="lm")
             for k, (a, b) in enumerate(CLAUSES)]
    S.show(*imp_t, dur=0.6, lag=0.12)
    S.say("每个变量的“真”和“假”各建一个点，共 2n 个点；每条子句连两条有向边。这张图叫蕴含图：沿着边走，就是“一旦选了它，后面这些都被迫成立”。")

    # ------------------------------------------------------------ 图
    S.section("蕴含图与强连通分量")
    pos = {}
    for v in range(1, NV + 1):
        pos[node((v, False))] = (-330 + 330 * (v - 1), -150)
        pos[node((v, True))] = (-330 + 330 * (v - 1), 150)
    labels = {node((v, n_)): lit_name((v, n_)) for v in range(1, NV + 1) for n_ in (False, True)}
    E = [(node(a), node(b)) for a, b in imp]
    # 跨过中间结点的横边弯一下，免得穿过别的点
    bends = {(a, b): -0.3 for a, b in E if pos[a][1] == pos[b][1] and abs(pos[a][0] - pos[b][0]) > 400}
    g = Graph(pos, E, x=560, y=470, directed=True, r=38, size=26, labels=labels, ecolor=LINE2, bends=bends)
    S.show(g)
    S.say("上面一排是 xᵢ 为真，下面一排是 xᵢ 为假（¬xᵢ 为真）。")
    S.say("如果从 x 能走到 ¬x，同时从 ¬x 也能走到 x，那么 x 取真取假都会推出矛盾——无解。也就是 x 和 ¬x 在同一个强连通分量里。")
    S.note("无解 ⇔ 某个 x 与 ¬x 在同一个强连通分量", color=R)
    ncomp = max(comp.values()) + 1
    cols = [CY, O, G, K, P, B]
    S.play(*[g[v].to(fill=tint(cols[comp[v] % len(cols)], 0.45)) for v in range(2 * NV)], dur=0.6)
    S.say(f"用 Tarjan 求强连通分量（同色为同一分量），共 {ncomp} 个。每对 xᵢ、¬xᵢ 都不在同一个分量里，所以有解。反过来，“不在同一分量”也足以保证有解——下面直接构造。")
    S.note("反之若都不在同一分量，就一定有解（构造如下）", color=G)

    # ------------------------------------------------------------ 构造
    S.section("按拓扑序给出一组解", keep=[g])
    S.say("缩点后得到一个 DAG。对每个变量，比较 xᵢ 和 ¬xᵢ 所在分量的拓扑序：选拓扑序靠后的那个为真。")
    S.note("x 的分量在拓扑序里比 ¬x 靠后 ⇒ x 取真", color=Y)
    S.say("为什么？选一个文字为真，会迫使它能走到的所有文字为真。选靠后的那个，它不可能走到靠前的“自己的否定”，就不会自相矛盾。")
    S.say("Tarjan 有个方便的性质：先找到（编号小）的分量在拓扑序里靠后。所以只要比较编号：分量编号小的那个取真。")
    S.note("Tarjan 的分量编号 = 逆拓扑序：编号小的取真", color=G)
    tags = {}
    for v in range(1, NV + 1):
        pv, nv_ = node((v, False)), node((v, True))
        win = pv if asg[v] else nv_
        lose = nv_ if asg[v] else pv
        tags[pv] = g.tag(pv, f"#{comp[pv]}", "u", DIM, 22)
        tags[nv_] = g.tag(nv_, f"#{comp[nv_]}", "d", DIM, 22)
        S.play(FadeIn(tags[pv]), FadeIn(tags[nv_]), dur=0.3)
        S.play(g[win].to(stroke=G, sw=5), g[lose].to(stroke=R, sw=2, fill=tint(R, 0.15)), dur=0.4)
    S.say("结果：" + "，".join(f"x{v} = {'真' if asg[v] else '假'}" for v in range(1, NV + 1)) + "。代回四条子句检验，全部满足。")
    S.note("解：" + "，".join(f"x{v} = {'真' if asg[v] else '假'}" for v in range(1, NV + 1)), color=G)
    S.say("整体复杂度 O(n + m)：建图、一次 Tarjan、一次比较。“至多选一个”“必须选”这类限制也都能写成子句：x 必选就是 (x ∨ x)，也就是边 ¬x → x。", extra=0.3)
    S.note("必选 x：(x ∨ x)，即 ¬x → x；总 O(n + m)")

    # ------------------------------------------------------------ 手推题
    qa, qc = solve(3, QCLAUSES)
    sols = brute(3, QCLAUSES)
    S.quiz("子句：" + "、".join(f"({lit_name(a)} ∨ {lit_name(b)})" for a, b in QCLAUSES) + "。\n\n"
           "(1) 写出全部蕴含边。\n"
           "(2) 有解吗？如果有，用“拓扑序靠后取真”的方法给出一组解。", think=20)
    qe = implication_edges(QCLAUSES)
    S.say("(1) " + "；".join(f"{lit_name(a)} → {lit_name(b)}" for a, b in qe) + "。")
    S.note("(1) 每条子句两条边，共 8 条", color=Y)
    if qa is None:
        S.say("(2) 无解。", extra=0.5)
    else:
        assert check(3, QCLAUSES, qa)
        S.say("(2) 沿边推：x₁ → ¬x₂（第二条），¬x₂ → x₃（第三条），x₃ → x₁（第四条）——x₁、¬x₂、x₃ 互相可达，在同一个分量里；它们的否定也在另一个分量。")
        S.say("没有 x 和 ¬x 在同一分量，有解。按拓扑序取真：" + "，".join(f"x{v} = {'真' if qa[v] else '假'}" for v in range(1, 4))
              + f"。（这个例子一共有 {len(sols)} 组解。）", extra=0.5)
        S.note("(2) " + "，".join(f"x{v} = {'真' if qa[v] else '假'}" for v in range(1, 4)), color=G)

    S.recap([
        "(a ∨ b) ⇔ (¬a → b) 且 (¬b → a)：2n 个点的蕴含图。",
        "x 与 ¬x 在同一个强连通分量 ⇔ 无解。",
        "有解时，取 x 和 ¬x 中拓扑序靠后的为真（Tarjan 编号小的为真）。",
        "建图 + Tarjan，O(n + m)。",
    ], next_title="斜率优化 DP")
