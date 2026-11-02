"""第 40 集 fail 树：出现次数就是子树和"""

from collections import Counter

from episodes.common import *
from episodes.e36_kmp_border import st
from episodes.e39_aho_corasick import AC, brute_occ

PATS = ["he", "she", "his", "hers"]
TEXT = "hishershe"
QPATS = ["a", "ab", "b", "bab"]
QTEXT = "babab"


def scan(ac, text):
    u = 0
    states, cnt = [], [0] * len(ac.ch)
    for c in text:
        u = ac.go(u, c)
        states.append(u)
        cnt[u] += 1
    return states, cnt


def subtree_sums(ac, cnt):
    tot = cnt[:]
    for v in reversed(ac.order):
        tot[ac.fail[v]] += tot[v]
    return tot


def build(S):
    S.cover("还是多个模式串和一篇文本，这次要数出每个模式串出现了几次。到达一个状态就沿 fail 链逐个报告，最坏会很慢——把 fail 指针反过来看，事情就简单了。",
            ["AC 自动机（第 39 集）"])

    ac = AC(PATS)
    n = len(ac.ch)
    states, cnt = scan(ac, TEXT)
    tot = subtree_sums(ac, cnt)
    real = Counter(k for _, k in brute_occ(PATS, TEXT))
    for k, p in enumerate(PATS):
        assert tot[ac.node_of(p)] == real[k]
    labels = {u: (st(ac.s[u]) if u else "ε") for u in range(n)}

    # ------------------------------------------------------------ 沿链报告太慢
    S.section("沿 fail 链报告，可能很慢")
    demo = Array(list("aaaaaaaa"), x=640, y=230, cw=70, ch=62, gap=8, size=30, chain="tt")
    S.show(demo, label(640, 160, "模式串：a、aa、aaa、aaaa；文本：aaaaaaaa", 26, FG))
    S.say("上一集说：到达状态 u 时，u 的 fail 链上每个模式串都在这里结尾，要沿链逐个报告。")
    S.say("可是链可能很长：模式串 a、aa、aaa、aaaa，文本全是 a。从第 4 个字符起，每读一个字符都要沿链报告 4 次。")
    bars = []
    for i in range(1, 9):
        k = min(i, 4)
        b = Rect(demo.X(i), 340 + 18 * k, 50, 36 * k, fill=tint(R, 0.5), stroke=R, sw=1.5, r=8)
        b.tr["op"].base = 0
        bars.append(b)
        S.add(b)
    S.play(*[FadeIn(b, dy=10) for b in bars], dur=0.6, lag=0.08)
    S.say("一般地，报告的总次数可以达到 |T| × 模式串个数。如果只想知道每个模式串出现几次，就不该一个一个报告。")
    S.note("沿链逐个报告：最坏 O(|T| · k)", color=R)

    # ------------------------------------------------------------ fail 树
    S.section("fail 指针连成一棵树")
    tr = Tree([(u, v) for u in range(n) for v in ac.ch[u].values()], 0, x=280, y=500, w=440, h=560, r=32,
              labels=labels, size=20)
    S.show(tr, label(280, 170, "Trie", 24, DIM))
    S.say("还是 " + "、".join(st(p) for p in PATS) + " 这几个模式串。除了根，每个结点恰好有一个 fail，并且 fail 指向更短的串。")
    S.note("每个非根结点恰有一个 fail，且指向更短的串 ⇒ 构成一棵树", color=Y)
    fedges = sorted(((ac.fail[v], v) for v in range(1, n)), key=lambda e: (len(ac.s[e[0]]), ac.s[e[1]]))
    ft = Tree(fedges, 0, x=930, y=500, w=640, h=560, r=32, labels=labels, size=20, ecolor=P)
    S.show(ft, label(930, 170, "fail 树（父亲 = fail）", 24, P))
    S.say("把每个结点连向它的 fail，得到一棵以根为根的树：fail 树。fail 链就是 fail 树上从结点到根的路径。")
    S.note("fail 链 = fail 树上到根的路径")

    # ------------------------------------------------------------ 祖先
    S.section("出现 ⇔ 是祖先", keep=[tr, ft])
    u5 = ac.node_of("she")
    S.play(ft[u5].to(fill=tint(CY, 0.5)), tr[u5].to(fill=tint(CY, 0.5)), dur=0.4)
    path = []
    v = u5
    while v:
        path.append(v)
        v = ac.fail[v]
    S.play(*[ft[x].to(stroke=Y, sw=4) for x in path], dur=0.6)
    S.say(f"读完文本某个前缀后停在 {st('she')}。在 {st('she')} 这里结尾的模式串，就是 fail 树上 {st('she')} 的祖先（含自己）里的那些：{st('she')} 和 {st('he')}。")
    S.note("模式串 P 在位置 i 结尾 ⇔ node(P) 是第 i 步状态的祖先", color=Y)
    S.play(*[ft[x].to(stroke=LINE2, sw=2.5) for x in path], ft[u5].to(fill=BG3), tr[u5].to(fill=BG3), dur=0.3)
    S.say("换个角度：模式串 P 出现的次数 = 有多少个位置 i，第 i 步的状态落在 node(P) 的子树里。")
    S.note("P 的出现次数 = node(P) 子树里所有状态被经过的次数之和", color=G)

    # ------------------------------------------------------------ 计数
    S.section("扫一遍记次数，再求子树和", keep=[tr, ft])
    ta = Array(list(TEXT), x=640, y=160, cw=52, ch=48, gap=6, size=26, chain="tt")
    S.play(tr.to(y=505, sc=0.92), ft.to(y=505, sc=0.92), dur=0.5)
    S.show(ta)
    S.say(f"扫描文本 {st(TEXT)}，每到一个状态就在那里记一笔（cnt 加一），不沿链报告。")
    tags = {v: ft.tag(v, "", "d", Y, 24, gap=4) for v in range(1, n)}
    for v in tags:
        tags[v].tr["text"].base = ""
    tok = tr.token(0, color=Y)
    S.play(FadeIn(tok), dur=0.3)
    run = [0] * n
    prev = 0
    for i, v in enumerate(states, start=1):
        run[v] += 1
        anims = [ta[i].to(fill=tint(Y, 0.35)),
                 tok.to(x=tr[v].g("x", 0), y=tr[v].g("y", 0))]
        if v:
            anims += [FadeIn(tags[v]), tags[v].to(text=str(run[v])), ft[v].to(fill=tint(Y, 0.25))]
        S.play(*anims, dur=0.35)
        S.play(ta[i].to(fill=BG3), dur=0.15)
    S.play(FadeOut(tok), dur=0.3)
    S.say("现在每个结点上记着“停在这里几次”。按逆 BFS 序（从深到浅）把每个结点的数加到它的 fail 父亲上，就得到子树和。")
    S.note("每到一个状态给它的计数加一；再按逆 BFS 序把 tot[v] 加到 tot[fail(v)] 上", color=Y)
    acc = cnt[:]
    for v in reversed(ac.order):
        f = ac.fail[v]
        if acc[v] and f:
            acc[f] += acc[v]
            S.play(ft[v].to(stroke=O, sw=3.5), ft[f].to(stroke=O, sw=3.5),
                   FadeIn(tags[f]), tags[f].to(text=str(acc[f])), dur=0.4)
            S.play(ft[v].to(stroke=LINE2, sw=2.5), ft[f].to(stroke=LINE2, sw=2.5), dur=0.2)
    S.play(*[ft[ac.node_of(p)].to(stroke=G, sw=4) for p in PATS], dur=0.5)
    S.say("模式串结点上的子树和就是答案：" + "、".join(f"{st(p)} 出现 {tot[ac.node_of(p)]} 次" for p in PATS)
          + "。和逐个比对的结果一样。")
    S.say("BFS 序里 fail(v) 一定排在 v 前面（更浅），所以倒着加不会漏。总复杂度 O(|T| + Trie 大小)。", extra=0.3)
    S.note("总 O(|T| + 结点数)：与模式串个数、链长无关", color=G)

    # ------------------------------------------------------------ 变式
    S.section("变式：模式串在模式串里出现几次")
    S.say("常见变式：问“模式串 x 在模式串 y 里出现几次”。把 y 在 Trie 上的路径（y 的每个前缀结点）都记一笔，答案就是 node(x) 子树里被记的个数。")
    S.note("x 在 y 中出现次数 = node(x) 的 fail 子树里，y 的前缀结点个数", color=Y)
    S.say("多组询问时，用 fail 树的 DFS 序把子树变成区间（第 18 集），离线按 y 在 Trie 上 DFS，配合树状数组做单点加、区间查。", extra=0.5)
    S.note("多组询问：fail 树 DFS 序 + 树状数组，离线")

    # ------------------------------------------------------------ 手推题
    qa = AC(QPATS)
    qs, qc = scan(qa, QTEXT)
    qt = subtree_sums(qa, qc)
    qreal = Counter(k for _, k in brute_occ(QPATS, QTEXT))
    for k, p in enumerate(QPATS):
        assert qt[qa.node_of(p)] == qreal[k]
    S.quiz("模式串：" + "、".join(f"{{t|{p}}}" for p in QPATS) + f"；文本：{{t|{QTEXT}}}。\n\n"
           "(1) 画出 fail 树。\n"
           "(2) 扫描文本，每个状态被经过几次？\n"
           "(3) 用子树和求每个模式串的出现次数。", think=20)
    S.say("(1) fail：" + "，".join(f"{st(qa.s[v])} → {st(qa.s[qa.fail[v]]) if qa.fail[v] else 'ε'}" for v in range(1, len(qa.ch))) + "。")
    S.note("(1) " + "，".join(f"{st(qa.s[v])}→{st(qa.s[qa.fail[v]]) if qa.fail[v] else 'ε'}" for v in range(1, len(qa.ch))), color=Y)
    S.say("(2) 依次到达 " + " → ".join(st(qa.s[v]) for v in qs) + "，被经过的次数："
          + "，".join(f"{st(qa.s[v])} {qc[v]} 次" for v in range(1, len(qa.ch)) if qc[v]) + "。")
    S.say("(3) 子树和：" + "，".join(f"{st(p)} = {qt[qa.node_of(p)]}" for p in QPATS)
          + f"。例如 {st('b')} 的子树里有 {st('b')}、{st('ab')}、{st('bab')}，合计 {qt[qa.node_of('b')]} 次。", extra=0.5)
    S.note("(3) " + "，".join(f"{st(p)}: {qt[qa.node_of(p)]}" for p in QPATS), color=G)

    S.recap([
        "每个非根结点有唯一的 fail，且指向更短的串，所以 fail 指针构成一棵树。",
        "P 在当前位置结尾 ⇔ node(P) 是当前状态在 fail 树上的祖先。",
        "数出现次数：扫描时只给到达的状态计数，再按逆 BFS 序求子树和，O(|T| + 结点数)。",
        "子树问题可以借助 DFS 序变成区间问题，处理“x 在 y 中出现几次”这类多组询问。",
    ], next_title="后缀数组（上）")
