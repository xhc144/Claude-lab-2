"""第 35 集 可撤销并查集与线段树分治：加边容易删边难"""

from episodes.common import *

T = 8
EDGES = [(1, 2, 1, 6), (2, 3, 3, 8), (3, 4, 1, 4), (1, 4, 5, 8)]     # (u, v, 出现, 消失前最后一刻)
ECOL = [CY, O, G, K]
QUERIES = {2: (1, 3), 4: (1, 4), 7: (2, 4)}


def brute(t, a, b):
    adj = {v: [] for v in range(1, 5)}
    for u, v, l, r in EDGES:
        if l <= t <= r:
            adj[u].append(v)
            adj[v].append(u)
    seen, st = {a}, [a]
    while st:
        x = st.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                st.append(y)
    return b in seen


def decompose(l, r, lo=1, hi=T):
    if r < lo or hi < l:
        return []
    if l <= lo and hi <= r:
        return [(lo, hi)]
    m = (lo + hi) // 2
    return decompose(l, r, lo, m) + decompose(l, r, m + 1, hi)


class DSU:
    """按大小合并、不压缩路径；每次合并把 (被挂上去的根, 新父亲) 记进栈。"""

    def __init__(self, n):
        self.p = {v: v for v in range(1, n + 1)}
        self.sz = {v: 1 for v in range(1, n + 1)}
        self.stack = []

    def find(self, x):
        path = [x]
        while self.p[x] != x:
            x = self.p[x]
            path.append(x)
        return x, path

    def union(self, a, b):
        a, _ = self.find(a)
        b, _ = self.find(b)
        if a == b:
            return None
        if self.sz[a] < self.sz[b]:
            a, b = b, a
        self.p[b] = a
        self.sz[a] += self.sz[b]
        self.stack.append((b, a))
        return (b, a)

    def undo(self):
        b, a = self.stack.pop()
        self.p[b] = b
        self.sz[a] -= self.sz[b]
        return (b, a)


def plan():
    """线段树分治的全过程：[(事件, 结点, 数据)]。"""
    hang = {}
    for i, (u, v, l, r) in enumerate(EDGES):
        for nd in decompose(l, r):
            hang.setdefault(nd, []).append(i)
    d = DSU(4)
    ev = []
    ans = {}

    def go(lo, hi):
        mark = len(d.stack)
        added = []
        for i in hang.get((lo, hi), []):
            u, v = EDGES[i][:2]
            added.append((i, d.union(u, v)))
        ev.append(("enter", (lo, hi), added))
        if lo == hi:
            if lo in QUERIES:
                a, b = QUERIES[lo]
                ra, pa = d.find(a)
                rb, pb = d.find(b)
                ans[lo] = ra == rb
                ev.append(("query", (lo, hi), (a, b, pa, pb, ra == rb)))
        else:
            m = (lo + hi) // 2
            go(lo, m)
            go(m + 1, hi)
        undone = []
        while len(d.stack) > mark:
            undone.append(d.undo())
        ev.append(("leave", (lo, hi), undone))

    go(1, T)
    return hang, ev, ans


def build(S):
    S.cover("一张图随时间加边、删边，每个时刻问两个点是否连通。并查集加边很方便，可它不会删边——怎么办？",
            ["并查集", "线段树（第 14 集）"])

    hang, ev, ans = plan()
    for t, (a, b) in QUERIES.items():
        assert ans[t] == brute(t, a, b)

    # ------------------------------------------------------------ 问题
    S.section("离线的动态连通性")
    head = Array(list(range(1, T + 1)), x=700, y=190, cw=96, ch=44, gap=8, size=22, index=False,
                 fill=tint(B, 0.12))
    S.show(head, label(130, 190, "时刻", 24, DIM, anchor="lm"))
    rows = []
    for i, (u, v, l, r) in enumerate(EDGES):
        y = 290 + 78 * i
        lab = label(130, y, f"e{i + 1}：{u} — {v}", 26, ECOL[i], anchor="lm")
        x1, x2 = head.X(l) - 44, head.X(r) + 44
        bar = Rect((x1 + x2) / 2, y, x2 - x1, 34, fill=tint(ECOL[i], 0.45), stroke=ECOL[i], sw=1.5, r=17)
        bar.tr["op"].base = 0
        rows.append((lab, bar))
        S.add(lab)
        S.play(FadeIn(lab), FadeIn(bar, dx=-12), dur=0.4)
    S.say("4 个点，时刻 1～8。每条边只在一段时间里存在：e1 在时刻 1～6 存在，e2 在 3～8……条形就是每条边的存在时间。")
    S.note("每条边在一段时间 [l, r] 里存在")
    qls = []
    for k, (t, (a, b)) in enumerate(sorted(QUERIES.items())):
        q = label(head.X(t), 626, f"{a}~{b}?", 26, Y)
        mk = Rect(head.X(t), 408, 104, 356, fill=alpha(Y, 0.06), stroke=alpha(Y, 0.5), sw=1.5, r=12, dash=(6, 6))
        mk.tr["op"].base = 0
        S.objs.insert(0, mk)
        qls += [q, mk]
        S.play(FadeIn(q), FadeIn(mk), dur=0.4)
    S.say("询问：时刻 2 问 1、3 是否连通，时刻 4 问 1、4，时刻 7 问 2、4。所有询问事先都知道（离线）。")
    S.note("询问：时刻 t，u 和 v 连通吗？（离线）")
    S.play(*[rows[i][1].to(stroke=Y, sw=3) for i in range(4) if EDGES[i][2] <= 4 <= EDGES[i][3]], dur=0.5)
    S.say("时刻 4 存在的边是 e1、e2、e3（黄框）：1—2—3—4 连成一片，所以 1 和 4 连通。")
    S.play(*[rows[i][1].to(stroke=ECOL[i], sw=1.5) for i in range(4)], dur=0.3)
    S.say("如果时间只往前走、边只加不删，并查集一路合并就行。麻烦在删边：并查集合并之后拆不开。")
    S.note("只加边：并查集；删边：并查集做不到", color=R)

    # ------------------------------------------------------------ 可撤销并查集
    S.section("能撤销的并查集")
    S.wide()
    pos = {1: (-150, -90), 2: (150, -90), 3: (-150, 110), 4: (150, 110)}
    demo = DSU(4)
    ops = [demo.union(1, 2), demo.union(3, 4), demo.union(2, 4)]
    g = Graph(pos, [o for o in ops], x=520, y=420, directed=True, r=34, size=28, hidden_edges=True,
              ecolor=Y, ew=3.5)
    S.show(g, label(520, 200, "并查集：箭头指向父亲", 26, DIM))
    stk = Array([""] * 3, x=1260, y=420, cw=150, ch=56, gap=10, size=26, index=False)
    S.show(stk, label(1260, 340, "撤销栈（记下每次改了谁）", 26, DIM))
    S.say("不能删“任意一条边”，但可以只撤销“最近一次合并”——像栈一样后进先出。下面看看要记下什么。")
    for k, (b, a) in enumerate(ops):
        S.play(FadeIn(g.edge(b, a)), g[b].to(stroke=Y), stk.cells[k].to(text=f"{b} → {a}", fill=tint(Y, 0.3)),
               dur=0.6)
        S.play(g[b].to(stroke=LINE2), dur=0.2)
    S.say("按大小合并：小的那棵挂到大的根下面（一样大就随便）。每次合并只改了一个指针 p[根] 和一个大小，把它记进栈。")
    S.say("撤销最近一次合并：弹栈，把那个根的父亲改回自己、大小减回去，O(1)。")
    b, a = ops[-1]
    S.play(FadeOut(g.edge(b, a)), stk.cells[2].to(text="", fill=BG3), g[b].to(stroke=Y), dur=0.6)
    S.play(g[b].to(stroke=LINE2), dur=0.2)
    S.say("那路径压缩呢？它会顺手改一长串结点的父亲，撤销时要全部改回来；更糟的是它的均摊分析依赖“压过就不再变长”，撤销后这个前提不成立。")
    S.say("所以只用按大小合并、不压缩：每当一个点所在的树变高一层，这棵树的大小至少翻倍，树高不超过 log n，find 最坏 O(log n)。", extra=0.3)
    S.play(FadeIn(g.edge(b, a)), stk.cells[2].to(text=f"{b} → {a}", fill=tint(Y, 0.3)), dur=0.5)
    path = [4, 3, 1]
    S.play(*[g[v].to(fill=tint(G, 0.5)) for v in path], dur=0.6, lag=0.25)
    S.say("例如 find(4)：4 → 3 → 1，走了两步，什么也不改。只要不改，撤销就永远只需要弹栈。")
    S.play(*[g[v].to(fill=BG3) for v in path], dur=0.3)

    # ------------------------------------------------------------ 线段树分治
    S.section("把边挂到时间线段树上")
    S.narrow()
    st = SegTree(T, x=430, y=190, w=740, level_h=118, node_h=50, info_size=20)
    S.show(st, label(430, 128, "时间轴上的线段树", 22, DIM))
    S.say("撤销只能“后进先出”，那就让加边、删边的顺序正好嵌套。办法：对时间轴建一棵线段树。")
    S.note("对时间 [1, T] 建线段树")
    for i, (u, v, l, r) in enumerate(EDGES):
        nds = decompose(l, r)
        S.say(f"e{i + 1} 存在于 [{l}, {r}]，像线段树的区间修改一样，拆成 {len(nds)} 个结点：" + "、".join(f"[{a}, {b}]" for a, b in nds)
              + "，挂在这些结点上。")
        S.play(*[st[nd].to(stroke=ECOL[i], sw=3.5) for nd in nds], dur=0.5)
        S.play(*[st.info[nd].to(text=" ".join(f"e{j + 1}" for j in hang[nd] if j <= i)) for nd in nds],
               *[st[nd].to(stroke=LINE2, sw=2) for nd in nds], dur=0.5)
    S.note("每条边的时间段拆成 O(log T) 个结点挂上去", color=Y)
    S.say("挂在结点 [a, b] 上的边，在整个 [a, b] 时段都存在。所以时刻 t 存在的边，正好是根到叶子 t 这条路径上挂着的所有边。")
    S.note("时刻 t 的边 = 根到叶子 t 路径上挂的边", color=G)

    # ------------------------------------------------------------ DFS
    S.section("在时间轴上 DFS", keep=[st])
    pos2 = {1: (-80, -70), 2: (80, -70), 3: (-80, 70), 4: (80, 70)}
    pairs = []
    for kind, nd, data in ev:
        if kind in ("enter", "leave"):
            for item in data:
                pr = item[1] if kind == "enter" else item
                if pr and pr not in pairs:
                    pairs.append(pr)
    g2 = Graph(pos2, pairs, x=1050, y=300, directed=True, r=28, size=24, hidden_edges=True, ecolor=Y, ew=3)
    stk2 = Array([""] * 3, x=1050, y=520, cw=104, ch=48, gap=8, size=22, index=False)
    S.show(g2, label(1050, 180, "并查集", 22, DIM), stk2, label(1050, 466, "撤销栈", 22, DIM))
    res_t = {}
    for k, (t, (a, b)) in enumerate(sorted(QUERIES.items())):
        res_t[t] = label(90, 680 + 52 * k, f"时刻 {t}：{a} 和 {b} 连通吗？", 26, FG, anchor="lm")
    S.show(*res_t.values())
    S.say("从根开始 DFS：进入一个结点，就把它挂着的边用并查集合并；到叶子 t，回答时刻 t 的询问；离开结点时，把进入时做的合并全部撤销。")
    S.note("进入结点：合并挂着的边；离开：撤销到进入前", color=Y)
    S.note("叶子 t：回答时刻 t 的询问")
    depth = 0
    narrated = set()
    for kind, nd, data in ev:
        if kind == "enter":
            anims = [st[nd].to(stroke=Y, sw=3.5)]
            for i, pr in data:
                if pr:
                    b_, a_ = pr
                    anims.append(FadeIn(g2.edge(b_, a_)))
                    anims.append(stk2.cells[depth].to(text=f"{b_} → {a_}", fill=tint(ECOL[i], 0.4)))
                    depth += 1
            S.play(*anims, dur=0.45)
            if data and nd not in narrated and len(narrated) < 2:
                narrated.add(nd)
                S.say(f"进入 [{nd[0]}, {nd[1]}]：合并 " + "、".join(f"e{i + 1}" for i, _ in data) + "，每次合并压一条记录进栈。")
        elif kind == "query":
            a, b, pa, pb, ok = data
            S.play(*[g2[v].to(fill=tint(CY, 0.5)) for v in pa], *[g2[v].to(fill=tint(O, 0.5)) for v in pb], dur=0.5)
            S.say(f"叶子 {nd[0]}：find({a}) 走到 {pa[-1]}，find({b}) 走到 {pb[-1]}。"
                  + ("根相同，连通。" if ok else "根不同，不连通。"))
            S.play(res_t[nd[0]].to(text=f"时刻 {nd[0]}：{a} 和 {b} 连通吗？" + ("{g|连通}" if ok else "{r|不连通}")),
                   *[g2[v].to(fill=BG3) for v in set(pa + pb)], dur=0.5)
        else:
            anims = [st[nd].to(stroke=LINE2, sw=2)]
            for b_, a_ in data:
                depth -= 1
                anims.append(FadeOut(g2.edge(b_, a_)))
                anims.append(stk2.cells[depth].to(text="", fill=BG3))
            S.play(*anims, dur=0.4 if data else 0.25)
            if data and nd == (1, 4):
                S.say("离开 [1, 4]：e1、e3 的合并按相反顺序弹栈撤销，并查集回到进入之前——右半边 [5, 8] 看到的是干净的状态。")
                S.flush()
    S.say("三个询问的答案都和直接按时刻建图的结果一致。整个过程中，撤销的永远是最近的合并，栈正好够用。", extra=0.3)

    # ------------------------------------------------------------ 复杂度
    S.section("复杂度与适用条件")
    S.say("每条边挂在 O(log T) 个结点上，每次挂上都要合并一次（find 是 O(log n)），撤销 O(1)。")
    S.note("m 条边 × O(log T) 个结点 × O(log n) 的 find", color=Y)
    S.say("总复杂度 O(m log T log n + q log n)。注意它要求离线：必须事先知道每条边什么时候出现、什么时候消失。")
    S.note("总 O(m log T log n)；必须离线", color=G)
    S.say("这个套路叫“线段树分治”：任何“只支持加入和撤销、不支持删除”的结构都能这样用，比如维护二分图判定的带权并查集、线性基。", extra=0.5)
    S.note("线段树分治：把“删除”变成按时间嵌套的“撤销”")

    # ------------------------------------------------------------ 手推题
    S.quiz("时刻 1～8 的线段树。\n\n"
           "(1) 一条边在时刻 [3, 7] 存在，它会被挂到哪几个结点上？\n"
           "(2) 另一条边在时刻 2 加入，时刻 5 被删掉，时刻 7 又加回来，一直留到最后。怎么挂？\n"
           "(3) 为了更快，能不能在 DFS 里给并查集加上路径压缩？", think=20)
    S.say(f"(1) 像区间修改一样拆：[3, 7] = " + " + ".join(f"[{a}, {b}]" for a, b in decompose(3, 7))
          + "，挂 3 个结点。")
    S.note("(1) [3, 7] → " + "、".join(f"[{a}, {b}]" for a, b in decompose(3, 7)), color=Y)
    S.say("(2) 它的存在时间是两段：[2, 4] 和 [7, 8]。当成两条独立的“边”，分别拆开挂上去即可。")
    S.note("(2) 拆成 [2, 4]、[7, 8] 两段：" + "、".join(f"[{a}, {b}]" for a, b in decompose(2, 4) + decompose(7, 8)),
           color=G)
    S.say("(3) 不能。路径压缩会修改很多父指针，撤销时不能只弹一条记录；均摊的复杂度也会被反复撤销打破。只用按大小（或按秩）合并。")
    S.note("(3) 不能压缩路径：只按大小合并，保证可撤销", color=R)

    S.recap([
        "并查集不会删边，但可以撤销最近一次合并：按大小合并、不压缩路径，每次只改一个指针，记进栈，弹栈即撤销。",
        "线段树分治：对时间建线段树，每条边的存在时段拆成 O(log T) 个结点挂上去。",
        "DFS：进入结点合并它的边，到叶子回答询问，离开时撤销——加入与撤销正好嵌套。",
        "O(m log T log n)，要求离线；适用于任何“能加入、能撤销、不能删除”的结构。",
    ], next_title="KMP 中的 border")
