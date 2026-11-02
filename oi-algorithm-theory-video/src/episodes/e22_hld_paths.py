"""第 22 集 树链剖分（下）：路径变成几段区间"""

from episodes.common import *
from episodes.e21_hld_structure import hld, EDGES, CHAIN_COLORS


def decompose(u, v, H):
    segs = []
    steps = []
    while H["top"][u] != H["top"][v]:
        tu, tv = H["top"][u], H["top"][v]
        if H["dep"][tu] < H["dep"][tv]:
            u, v = v, u
            tu, tv = tv, tu
        segs.append((H["dfn"][tu], H["dfn"][u]))
        steps.append(("jump", u, tu, H["par"][tu]))
        u = H["par"][tu]
    a, b = (u, v) if H["dep"][u] <= H["dep"][v] else (v, u)
    segs.append((H["dfn"][a], H["dfn"][b]))
    steps.append(("same", a, b))
    return segs, steps, a


def build(S):
    S.cover("有了重链剖分，路径 u–v 怎样拆成 O(log n) 段 dfn 区间？每次该跳哪一边，为什么不会跳过 LCA？",
            ["树链剖分的结构（第 21 集）", "线段树区间修改与查询（第 15 集）"])

    H = hld(EDGES)
    chains = {}
    for v, t in H["top"].items():
        chains.setdefault(t, []).append(v)
    cid = {t: i for i, t in enumerate(sorted(chains, key=lambda t: H["dfn"][t]))}

    def ccol(v):
        return CHAIN_COLORS[cid[H["top"][v]] % len(CHAIN_COLORS)]

    def setup(y_tree=330, sc=0.78, y_seq=760):
        tree = Tree(EDGES, 1, x=560, y=y_tree, w=760, h=500, r=26, size=22)
        tree.tr["sc"].base = sc
        for v in H["top"]:
            tree[v].c.tr["fill"].base = tint(ccol(v), 0.4)
            tree[v].c.tr["stroke"].base = ccol(v)
        for u, hv in H["heavy"].items():
            if hv:
                tree.edge(u, hv).tr["color"].base = alpha(Y, 0.8)
                tree.edge(u, hv).tr["w"].base = 6
        seq = Array([str(v) for v in H["seq"]], x=640, y=y_seq, cw=76, ch=58, gap=6, size=24)
        for v in H["seq"]:
            seq[H["dfn"][v]].box.tr["fill"].base = tint(ccol(v), 0.35)
        return tree, seq

    # ------------------------------------------------------------ 跳链
    S.section("沿重链往上跳")
    tree, seq = setup()
    S.show(tree, seq, label(640, 690, "按 dfn 排列（同色 = 同一条重链）", 22, DIM))
    S.say("回顾：每个点记录了 top（所在重链的链顶）和 dfn。同一条重链在 dfn 序里是连续的一段，链顶在最前面。")
    S.note("top[v]：v 所在重链的链顶；dfn[v]：重儿子优先的 DFS 序")
    S.say("处理路径 u–v：如果 u、v 不在同一条重链上，就把其中一个点“跳”到它的链顶的父亲，同时把跳过的这一段交给线段树。")
    S.note("不在同一条链：选一个点 x，处理 [dfn[top[x]], dfn[x]]，x ← fa[top[x]]", color=Y)
    S.say("选哪一个点跳？选{y|链顶更深}的那个。等两个点到了同一条链上，最后处理它们之间的一段，较浅的那个就是 LCA。")
    S.note("规则：跳链顶更深的那一个", color=Y)
    S.note("同一条链：处理 [dfn[浅], dfn[深]]，浅的那个 = LCA", color=G)

    u0, v0 = 12, 13
    segs, steps, l = decompose(u0, v0, H)
    tu = tree.token(u0, CY, 11)
    tv = tree.token(v0, O, 11)
    S.play(FadeIn(tu), FadeIn(tv), dur=0.3)
    S.say(f"例：路径 {u0}–{v0}。top[{u0}] = {H['top'][u0]}（深度 {H['dep'][H['top'][u0]]}），top[{v0}] = {H['top'][v0]}（深度 {H['dep'][H['top'][v0]]}）。")
    pos = {u0: tu, v0: tv}
    cur = {u0: u0, v0: v0}
    brs = []
    for i, st in enumerate(steps):
        if st[0] == "jump":
            _, x, tx, fx = st
            tok = tu if (cur[u0] == x) else tv
            key = u0 if cur[u0] == x else v0
            seg = (H["dfn"][tx], H["dfn"][x])
            S.say(f"{x} 的链顶 {tx} 更深：处理 dfn 区间 [{seg[0]}, {seg[1]}]（{tx} 到 {x} 这一段链），然后跳到 fa[{tx}] = {fx}。")
            br = seq.frame(seg[0], seg[1], Y if i == 0 else G)
            brs.append(br)
            S.play(FadeIn(br), *[tree[w].to(sw=5, stroke=Y) for w in chains[tx] if H["dfn"][tx] <= H["dfn"][w] <= H["dfn"][x]],
                   dur=0.5)
            S.play(tok.to(x=tree[fx].g("x", 0), y=tree[fx].g("y", 0)), dur=0.6)
            cur[key] = fx
        else:
            _, a, b = st
            seg = (H["dfn"][a], H["dfn"][b])
            S.say(f"现在两点都在同一条重链上（{a} 和 {b}），处理 [{seg[0]}, {seg[1]}]。较浅的 {a} 就是 LCA。")
            br = seq.frame(seg[0], seg[1], P)
            brs.append(br)
            S.play(FadeIn(br), tree[a].to(fill=tint(Y, 0.6)), dur=0.5)
    S.say(f"整条路径被拆成 {len(segs)} 段 dfn 区间：" + "、".join(f"[{a}, {b}]" for a, b in segs) + "。每段在线段树上做一次区间修改或查询。")
    S.note(f"路径 {u0}–{v0} = " + " ∪ ".join(f"[{a},{b}]" for a, b in segs))

    # ------------------------------------------------------------ 为什么跳深的
    S.section("为什么跳链顶深的不会出错")
    tree2, seq2 = setup(y_tree=350, sc=0.85, y_seq=-200)
    S.show(tree2)
    S.say("担心的是：跳过了 LCA。跳到 fa[top[x]] 是安全的，当且仅当 top[x] 在 LCA 的{y|下方}（严格更深）。")
    S.note("要证：链顶更深的那个点 x，top[x] 严格在 LCA 下方", color=Y)
    S.say("反证：假设 top[u] 更深（或一样深），却在 LCA 或 LCA 上方。那么 u 所在的链从 top[u] 往下一直到 u，经过了 LCA。")
    S.say("v 在 LCA 的子树里，v 的链和 u 的链不同，所以 v 的链不可能穿过 LCA，只能整条在 LCA 下方：top[v] 比 LCA 深，也就比 top[u] 深——矛盾。")
    S.note("反证：否则 top[v] 在 LCA 下方，比 top[u] 更深，矛盾", color=G)
    S.say("所以每次跳的那段链完全在路径上，不会越过 LCA；最后在同一条链上时，较浅的点一定是 LCA。")

    # ------------------------------------------------------------ 复杂度
    S.section("复杂度与子树操作")
    S.say("每跳一次，就从 top[x] 经过一条轻边到它的父亲。上一集证明了到根的路径上只有 O(log n) 条轻边，所以跳 O(log n) 次。")
    S.note("跳链次数 O(log n)；每次线段树 O(log n) → 路径操作 O(log² n)", color=Y)
    S.say("每段区间在线段树上 O(log n)，一次路径操作 O(log² n)。实际上大部分段都很短，常数很小，跑得很快。")
    S.say("子树操作更简单：重儿子优先的 DFS 序仍然是 DFS 序，子树 u 就是 [dfn[u], dfn[u] + size(u) − 1]，一段区间。")
    S.note("子树 u：[dfn[u], dfn[u] + size(u) − 1]，一次线段树操作", color=G)
    tree3, seq3 = setup(y_tree=330, sc=0.78, y_seq=760)
    S.show(tree3, seq3)
    sub = tree3.subtree(4)
    br3 = seq3.frame(H["dfn"][4], H["dfn"][4] + H["size"][4] - 1, CY)
    S.play(FadeIn(br3), *[tree3[w].to(sw=5, stroke=CY) for w in sub], dur=0.6)
    S.say(f"例：子树 4 有 {H['size'][4]} 个点，就是 dfn 区间 [{H['dfn'][4]}, {H['dfn'][4] + H['size'][4] - 1}]。路径操作和子树操作可以共用同一棵线段树。")
    S.say("顺带一提：同样的跳法不需要线段树也能求 LCA，O(log n)，常数比倍增小。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    S.quiz("用本集的树（dfn 序见画面），手推路径 10–13：\n"
           "(1) 依次跳哪个点？处理了哪些 dfn 区间？\n"
           "(2) LCA 是谁？", think=20)
    tree4, seq4 = setup(y_tree=480, sc=0.6, y_seq=760)
    S.show(tree4, seq4)
    segs2, steps2, l2 = decompose(10, 13, H)
    S.say(f"(1) top[10] = 10、top[13] = 9，深度都是 2，跳哪个都行，这里先跳 10：处理 [{H['dfn'][10]}, {H['dfn'][10]}]，到 4。")
    S.say(f"现在 top[4] = 1（深度 0），top[13] = 9（深度 2），跳 13：处理 [{H['dfn'][9]}, {H['dfn'][13]}]，到 4。")
    S.say(f"两点都在 4，同一条链，处理 [{H['dfn'][4]}, {H['dfn'][4]}]。")
    for a, b in segs2:
        S.play(FadeIn(seq4.frame(a, b, Y)), dur=0.4)
    S.note("(1) 区间：" + "、".join(f"[{a},{b}]" for a, b in segs2), color=Y)
    S.say(f"(2) LCA = {l2}。")
    S.play(tree4[l2].to(fill=tint(Y, 0.6)), dur=0.4)
    S.note(f"(2) LCA = {l2}", color=Y)

    S.recap([
        "路径 u–v：不在同一条重链时，跳链顶更深的点，处理 [dfn[top], dfn[x]]，再跳到链顶的父亲。",
        "跳链顶更深的点不会越过 LCA：否则另一点的链顶会更深，矛盾。",
        "同一条链时处理最后一段，较浅的点就是 LCA。",
        "跳链 O(log n) 次（每次过一条轻边），路径操作 O(log² n)；子树仍是一段区间，O(log n)。",
    ], next_title="分层图最短路：把额外信息放进结点")
