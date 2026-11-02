"""第 17 集 动态开点与线段树合并：只建用得到的结点"""

from episodes.common import *

V = 8


def path(v, l=1, r=V):
    out = [(l, r)]
    while l < r:
        m = (l + r) // 2
        if v <= m:
            r = m
        else:
            l = m + 1
        out.append((l, r))
    return out


def counts(vals):
    c = {}
    for v in vals:
        for nd in path(v):
            c[nd] = c.get(nd, 0) + 1
    return c


TREE_EDGES = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6)]
COLOR = {1: 2, 2: 3, 3: 1, 4: 3, 5: 2, 6: 1}


def build(S):
    S.cover("值域到 10⁹ 的权值线段树怎么建？树上每个点都要统计子树里的颜色，怎样把儿子们的线段树合并起来？",
            ["线段树的结点信息（第 14 集）", "树的 DFS"])

    # ------------------------------------------------------------ 动态开点
    S.section("动态开点")
    S.say("权值线段树：下标是“值”，结点存这个值域里有几个数。它能回答“第 k 小”“某个值出现几次”等问题。")
    S.note("权值线段树：按值建树，结点存该值域内数的个数")
    S.say("可值域如果是 [1, 10⁹]，把整棵树建出来要几十亿个结点，不可能。")
    st = SegTree(V, x=640, y=200, w=1100, level_h=145, node_h=52, info_size=22)
    for k, c in st.nodes.items():
        c.tr["op"].base = 0.18
    S.show(st)
    S.say("但真正插入的数只有 m 个。插入一个数只会经过从根到叶子的一条路径，只要{y|用到哪个结点，才建哪个结点}。")
    S.note("动态开点：只建插入路径上的结点", color=Y)
    vals = [3, 6, 7]
    created = set()
    cnt = {}
    for v in vals:
        p = path(v)
        new = [nd for nd in p if nd not in created]
        for nd in p:
            cnt[nd] = cnt.get(nd, 0) + 1
        created |= set(p)
        S.play(*[st[nd].to(op=1.0, stroke=Y, sw=3) for nd in new], *[st[nd].to(text=str(cnt[nd])) for nd in p], dur=0.6)
        S.play(*[st[nd].to(stroke=LINE2, sw=2) for nd in new], dur=0.2)
        if v == 3:
            S.say(f"插入 3：建出根到叶子 3 的 4 个结点，每个结点计数 +1。没走到的儿子保持“空”（指针为空）。")
    S.say(f"再插入 6、7：新建的只有路径上原来不存在的结点。一共只建了 {len(created)} 个结点，而完整的树有 {2 * V - 1} 个。")
    S.note("每次插入最多新建 log V 个结点，总共 O(m log V)", color=G)
    S.say("访问一个空儿子时，按“计数为 0”处理即可。值域 10⁹、插入 10⁵ 次，结点数大约 30 × 10⁵ = 3×10⁶，可以接受。")

    # ------------------------------------------------------------ 合并
    S.section("线段树合并")
    S.say("现在有两棵动态开点的权值线段树 A、B（值域相同），想得到一棵表示“两个多重集合并起来”的树。")
    S.note("合并 A、B：得到两个多重集之并的权值线段树")
    A_vals, B_vals = [2, 5, 5], [5, 7]
    ca, cb = counts(A_vals), counts(B_vals)
    ta = SegTree(V, x=340, y=200, w=560, level_h=135, node_h=46, info_size=20, show_range=False)
    tb = SegTree(V, x=960, y=200, w=560, level_h=135, node_h=46, info_size=20, show_range=False)
    for t, c in ((ta, ca), (tb, cb)):
        for nd, node in t.nodes.items():
            if nd in c:
                node.label.tr["text"].base = str(c[nd])
            else:
                node.tr["op"].base = 0.0
        for (p, k), e in t.edges.items():
            if k not in c:
                e.tr["op"].base = 0.0
    la = label(340, 130, "A = {2, 5, 5}", 28, CY)
    lb = label(960, 130, "B = {5, 7}", 28, O)
    S.show(ta, tb, la, lb)
    S.say("合并从两棵树的根同时往下走，规则只有三条：")
    S.note("① 有一边是空：直接用另一边的子树（不再往下）", color=Y)
    S.note("② 都是叶子：计数相加", color=Y)
    S.note("③ 都不空：递归合并左右儿子，再更新计数", color=Y)
    both = [nd for nd in ca if nd in cb]
    only_a = [nd for nd in ca if nd not in cb]
    only_b = [nd for nd in cb if nd not in ca]
    S.say("两棵树都有的结点（黄色）需要递归处理；只有一边有的子树（比如 A 的 [1,4]、B 的 [7,8]），在第一次碰到时就整个“挂”过去，不用往下看。")
    S.play(*[ta[nd].to(stroke=Y, sw=4) for nd in both], *[tb[nd].to(stroke=Y, sw=4) for nd in both], dur=0.6)
    tops_b = [nd for nd in only_b if st.up(nd) in both or st.up(nd) is None]
    tops_a = [nd for nd in only_a if st.up(nd) in both or st.up(nd) is None]
    S.play(*[tb[nd].to(stroke=G, sw=4) for nd in tops_b], *[ta[nd].to(stroke=G, sw=4) for nd in tops_a], dur=0.6)
    S.say(f"结果直接改在 A 上：两边都有的 {len(both)} 个结点计数相加；B 独有的子树接到 A 上。A 变成 {{2, 5, 5, 5, 7}}。")
    cm = counts(A_vals + B_vals)
    for nd in only_b:
        ta[nd].label.tr["text"].base = str(cm[nd])
    S.play(*[FadeIn(ta[nd]) for nd in only_b],
           *[FadeIn(ta.edges[(ta.up(nd), nd)]) for nd in only_b],
           *[ta[nd].to(text=str(cm[nd])) for nd in both], FadeOut(tb, lb), la.to(text="A ∪ B = {2, 5, 5, 5, 7}"), dur=0.8)
    S.play(*[ta[nd].to(stroke=LINE2, sw=2) for nd in ta.nodes], dur=0.3)

    # ------------------------------------------------------------ 复杂度
    S.section("为什么合并很快")
    S.say("一次合并的代价是多少？递归只会深入“两棵树都有”的结点；碰到一边为空就立刻返回。")
    S.note("一次合并的代价 = 两棵树公共结点的个数（再乘常数）")
    S.say("而每个公共结点被处理完后，B 里对应的那个结点就“作废”了（它的信息已经并进 A）。")
    S.say("所以：每做一次 O(1) 的递归工作，就有一个结点永久消失。结点总数一开始是 O(m log V)，消失的次数不会超过这个数。")
    S.note("每处理一个公共结点 = 消灭一个结点 → 所有合并总代价 ≤ 结点总数", color=Y)
    S.note("总复杂度 O(m log V)", color=G)
    S.say("这是一个“势能”论证：单次合并可能很慢（两棵大树大量重合），但慢的代价都“花掉”了结点，总量有上限。")

    # ------------------------------------------------------------ 树上应用
    S.section("应用：子树里出现最多的颜色")
    tr = Tree(TREE_EDGES, 1, x=380, y=460, w=480, h=380, r=32, size=26)
    S.show(tr)
    cnames = {1: "红", 2: "蓝", 3: "绿"}
    ccols = {1: R, 2: B, 3: G}
    S.play(*[tr[v].to(fill=tint(ccols[COLOR[v]], 0.5), stroke=ccols[COLOR[v]]) for v in COLOR], dur=0.6)
    S.say("每个点有一种颜色。对每个点 u，问：u 的子树里出现次数最多的颜色是哪种？")
    S.note("对每个 u：子树里出现最多的颜色")
    S.say("做法：每个点先建一棵只含自己颜色的权值线段树（结点存“最大出现次数”和对应颜色）。DFS 回溯时，把每个儿子的树合并到自己的树上。")
    S.note("每点建一棵树 → 回溯时把儿子的树并进来 → 当场回答", color=Y)
    tags = {v: tr.tag(v, "", "r", Y, 22) for v in COLOR}
    ch = {}
    for p, c in TREE_EDGES:
        ch.setdefault(p, []).append(c)
    sub = {}

    def dfs(u):
        s = {COLOR[u]: 1}
        for c in ch.get(u, []):
            for k, v in dfs(c).items():
                s[k] = s.get(k, 0) + v
        sub[u] = s
        return s

    dfs(1)
    order = [4, 5, 2, 6, 3, 1]
    for u in order:
        s = sub[u]
        best = max(sorted(s), key=lambda k: s[k])
        S.play(*[tr.edge(u, c).to(color=Y, w=5) for c in ch.get(u, [])], dur=0.3)
        S.play(FadeIn(tags[u]), tags[u].to(text=f"{cnames[best]}×{s[best]}"), dur=0.4)
        S.play(*[tr.edge(u, c).to(color=LINE2, w=3) for c in ch.get(u, [])], dur=0.2)
    S.say("例如点 2 的子树里有两个绿、一个蓝，答案是绿；根的子树里红、蓝、绿各 2 个，取编号最小的红。")
    S.say("注意：合并是“破坏性”的——儿子的树被并进父亲后就不能再单独用了。所以要在合并完成的那一刻立即回答这个点的询问（离线回答）。")
    S.note("合并会破坏儿子的树 → 每个点合并完立即回答", color=R)
    S.say(f"总共 n 次插入，每次 O(log V) 个结点，所有合并的总代价也不超过这个数：O(n log V)。")

    # ------------------------------------------------------------ 手推题
    S.quiz("值域 [1, 8]。A 是插入了 {1, 2, 3, 4} 的权值线段树，B 是插入了 {5, 6, 7, 8} 的。\n"
           "C 是插入了 {1, 2, 3, 4} 的，D 也是插入了 {1, 2, 3, 4} 的。\n\n"
           "(1) 合并 A 和 B、合并 C 和 D，各要递归处理几个公共结点？\n"
           "(2) 合并 C 和 D 那么“贵”，为什么不会让总复杂度变差？", think=20)
    S.say("(1) A 的结点都在左半 [1,4] 里，B 的都在右半 [5,8] 里，公共结点只有根 [1,8]。合并只做 O(1) 的工作，两棵子树直接挂上去。")
    S.note("(1) A、B：公共结点只有根 → O(1)", color=G)
    S.say("C 和 D 一模一样，左半 7 个结点全部重合，再加上根，公共结点 8 个，每一个都要递归处理。")
    S.note("C、D：公共结点 8 个 → 8 次递归", color=O)
    S.say("(2) 处理这 8 个公共结点的同时，D 的 8 个结点被消灭了。要再出现这么贵的合并，就得先再插入数、新建结点“付费”。总代价仍然 ≤ 结点总数。")
    S.note("(2) 贵的合并消灭的结点也多：总代价 ≤ 建过的结点数", color=Y)

    S.recap([
        "动态开点：只建插入路径上的结点，m 次插入 O(m log V) 个结点，值域再大也不怕。",
        "线段树合并：一边为空直接接上另一边；都不空就递归合并左右儿子，叶子计数相加。",
        "每处理一个公共结点就消灭一个结点，所有合并的总代价不超过结点总数：O(m log V)。",
        "树上应用：回溯时把儿子的树并进来；合并是破坏性的，要当场回答询问。",
    ], next_title="DFS 序：把子树变成区间")
