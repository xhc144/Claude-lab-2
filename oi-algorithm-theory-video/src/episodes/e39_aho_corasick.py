"""第 39 集 AC 自动机：在 Trie 上建失配指针"""

from collections import deque

from episodes.common import *
from episodes.e36_kmp_border import st

PATS = ["he", "she", "his", "hers"]
TEXT = "ushers"
QPATS = ["ab", "bab", "bca", "caa"]
QTEXT = "bcaab"


class AC:
    def __init__(self, pats):
        self.ch = [{}]
        self.s = [""]
        self.end = [[]]
        for k, p in enumerate(pats):
            u = 0
            for c in p:
                if c not in self.ch[u]:
                    self.ch.append({})
                    self.s.append(self.s[u] + c)
                    self.end.append([])
                    self.ch[u][c] = len(self.ch) - 1
                u = self.ch[u][c]
            self.end[u].append(k)
        n = len(self.ch)
        self.fail = [0] * n
        self.order = []
        self.trace = {}          # 结点 → 构造 fail 时沿链尝试过的结点
        q = deque()
        for c, v in self.ch[0].items():
            q.append(v)
            self.trace[v] = (0, c, [0])
        while q:
            u = q.popleft()
            self.order.append(u)
            for c, v in self.ch[u].items():
                f = self.fail[u]
                tried = [f]
                while f and c not in self.ch[f]:
                    f = self.fail[f]
                    tried.append(f)
                self.fail[v] = self.ch[f][c] if c in self.ch[f] and self.ch[f][c] != v else 0
                self.trace[v] = (u, c, tried)
                q.append(v)

    def go(self, u, c):
        while u and c not in self.ch[u]:
            u = self.fail[u]
        return self.ch[u].get(c, 0)

    def outputs(self, u):
        out = []
        while u:
            out += self.end[u]
            u = self.fail[u]
        return out

    def node_of(self, s):
        u = 0
        for c in s:
            u = self.ch[u][c]
        return u


def brute_occ(pats, text):
    return sorted((i + len(p), k) for k, p in enumerate(pats) for i in range(len(text) - len(p) + 1)
                  if text[i:i + len(p)] == p)


def build(S):
    S.cover("给很多个模式串（比如一本敏感词词典）和一篇文本，找出每个模式串在文本里的所有出现。每个模式串跑一遍 KMP 太慢——能不能只扫一遍文本？",
            ["KMP 与 border（第 36 集）", "Trie（字典树）", "BFS"])

    ac = AC(PATS)
    n = len(ac.ch)
    edges = [(u, v) for u in range(n) for v in ac.ch[u].values()]
    labels = {u: (st(ac.s[u]) if u else "ε") for u in range(n)}

    # ------------------------------------------------------------ Trie
    S.section("把模式串放进一棵 Trie")
    tr = Tree(edges, 0, x=470, y=480, w=780, h=600, r=36, labels=labels, size=22)
    for u in range(n):
        for c, v in ac.ch[u].items():
            tr.etag(u, v, st(c), color=FG, size=22, hidden=False)
    S.show(tr, dur=0.8)
    S.say("模式串 " + "、".join(st(p) for p in PATS) + " 插入 Trie：每个结点代表一个前缀，结点里写的就是这个前缀。")
    S.note("Trie 的结点 = 所有模式串的所有前缀")
    for k, p in enumerate(PATS):
        S.play(tr[ac.node_of(p)].to(stroke=Y, sw=4), dur=0.25)
    S.say("黄框的结点是某个模式串的结尾。在 Trie 上沿着文本走，就能同时和所有模式串比较——问题还是失配：走不下去时该去哪？")
    S.note("单个模式串失配看 π；多个模式串失配看 fail", color=Y)

    # ------------------------------------------------------------ fail 的定义
    S.section("fail：最长的、在 Trie 里的真后缀", keep=[tr])
    u5 = ac.node_of("she")
    S.say(f"类比 KMP：对结点 u（代表串 str(u)），fail(u) 指向 str(u) 的最长真后缀里、在 Trie 中出现的那一个。")
    S.note("fail(u) = str(u) 的真后缀中，在 Trie 里最长的那个", color=Y)
    S.play(tr[u5].to(fill=tint(CY, 0.5)), dur=0.4)
    sufs = [ac.s[u5][k:] for k in range(1, len(ac.s[u5]) + 1)]
    S.say(f"例：{st('she')} 的真后缀有 {st('he')}、{st('e')} 和空串。{st('he')} 在 Trie 里，而且最长，所以 fail({st('she')}) = {st('he')}。")
    farrows = {}

    def fail_arrow(v):
        ln = Line(color=P, w=2.5, head=12, bend=0.28, dash=(8, 6)).attach(tr[v], tr[ac.fail[v]])
        ln.tr["op"].base = 0
        tr.add(ln)
        farrows[v] = ln
        return ln

    S.play(FadeIn(fail_arrow(u5)), tr[ac.fail[u5]].to(fill=tint(P, 0.4)), dur=0.6)
    S.say("这和 KMP 的 π 是同一个想法：已经匹配上的部分里，“最长的、还能继续往下匹配”的后缀。单个模式串时，Trie 是一条链，fail 就是 π。")
    S.note("单个模式串时 fail 就是 π", color=G)
    S.play(tr[u5].to(fill=BG3), tr[ac.fail[u5]].to(fill=BG3), dur=0.3)

    # ------------------------------------------------------------ BFS 构造
    S.section("按 BFS 顺序构造 fail", keep=[tr, farrows[u5]])
    S.say("深度为 1 的结点，fail 都指向根。其余结点 v（父亲 u，边上字符 c）：str(v) 的后缀去掉最后的 c，就是 str(u) 的后缀。")
    S.note("v = u 的 c 儿子：沿 fail(u) 的链找第一个有 c 儿子的结点 f，fail(v) = f 的 c 儿子", color=Y)
    S.say("所以从 fail(u) 出发沿 fail 链往上找，第一个有 c 儿子的结点 f，fail(v) 就是 f 的 c 儿子；找不到就指向根。")
    S.say("链上的结点都比 v 浅，按 BFS（一层一层）的顺序处理，用到的 fail 都已经算好了。")
    S.note("BFS 顺序：用到的 fail 都更浅，已算好")
    narrated = 0
    for v in ac.order:
        if v == u5:
            continue
        u, c, tried = ac.trace[v]
        anims = [tr[v].to(fill=tint(CY, 0.45))]
        if u:
            anims.append(tr[u].to(fill=tint(O, 0.35)))
        S.play(*anims, dur=0.3)
        if u and narrated < 3 and ac.fail[v]:
            path = " → ".join("ε" if f == 0 else st(ac.s[f]) for f in tried)
            S.say(f"{st(ac.s[v])}：父亲是 {st(ac.s[u])}，从 fail({st(ac.s[u])}) 出发找 {st(c)} 儿子，依次看 {path}，"
                  f"找到 {st(ac.s[ac.fail[v]])}，所以 fail = {st(ac.s[ac.fail[v]])}。")
            narrated += 1
        if ac.fail[v]:
            S.play(FadeIn(fail_arrow(v)), dur=0.4)
        S.play(tr[v].to(fill=BG3), *([tr[u].to(fill=BG3)] if u else []), dur=0.2)
    S.say("没画箭头的结点，fail 都指向根。每个结点沿链往上找的总步数，和 KMP 一样可以用深度做势能分析，整体是线性的（乘字符集大小）。")
    S.note("构造 O(Σ|Pᵢ| · |Σ|)，与 KMP 同样的势能论证")

    # ------------------------------------------------------------ 匹配
    S.section("扫描文本：每一步都只沿边走", keep=[tr] + list(farrows.values()))
    ta = Array(list(TEXT), x=1080, y=190, cw=56, ch=54, gap=6, size=28, chain="tt")
    S.show(ta, label(1080, 128, "文本", 22, DIM))
    S.say("再进一步：把“失配就沿 fail 跳”预先算进转移里。trans(u, c)：u 有 c 儿子就走过去，否则等于 trans(fail(u), c)。")
    S.note("trans(u, c) = u 的 c 儿子；没有则 = trans(fail(u), c)", color=Y)
    S.say("按 BFS 顺序补全每个结点、每个字符的转移（Trie 图），匹配时每读一个字符只走一步，不再有 while 循环。")
    tok = tr.token(0, color=Y)
    S.play(FadeIn(tok), dur=0.3)
    out_t = para(905, 290, "", size=24, maxw=380)
    S.add(out_t)
    u = 0
    found = []
    for i, c in enumerate(TEXT, start=1):
        v = ac.go(u, c)
        S.play(ta[i].to(fill=tint(Y, 0.4)), tr.move_token(tok, u, v) if (u, v) in tr.edges else tok.to(
            x=tr[v].g("x", 0), y=tr[v].g("y", 0)), dur=0.5)
        outs = ac.outputs(v)
        if c == "r":
            S.say(f"读到 {st('r')}：{st('she')} 没有 {st('r')} 儿子。补全的转移已经替我们沿 fail 跳到 {st('he')}，再走到 {st('her')}——一步到位。")
        if outs:
            found += [(i, k) for k in outs]
            S.play(out_t.to(text="找到：" + "、".join(f"{st(PATS[k])}（结尾 {i}）" for i, k in found)), dur=0.4)
            if v == u5:
                S.say(f"到达 {st('she')}：它是模式串，报告 {st('she')}。沿 fail 链往上，{st('he')} 也是模式串——{st('he')} 也在这里结尾！")
                S.note("到达 u 时，fail 链上所有的模式串结尾都在这里出现", color=G)
        S.play(ta[i].to(fill=BG3), dur=0.2)
        u = v
    assert sorted(found) == brute_occ(PATS, TEXT)
    S.say("一遍扫描，三个出现全部找到。注意报告时要沿 fail 链收集——下一集会看到，这条链可以变成一棵树来批量处理。", extra=0.3)

    # ------------------------------------------------------------ 手推题
    qa = AC(QPATS)
    S.quiz("模式串：" + "、".join(f"{{t|{p}}}" for p in QPATS) + f"；文本：{{t|{QTEXT}}}。\n\n"
           "(1) 画出 Trie，求 fail({t|bab})、fail({t|bca})、fail({t|caa})。\n"
           "(2) 用 AC 自动机扫描文本，依次经过哪些结点？找到了哪些出现？", think=20)
    fb = {s_: qa.s[qa.fail[qa.node_of(s_)]] or "ε" for s_ in ("bab", "bca", "caa")}
    S.say(f"(1) {st('bab')} 的真后缀 {st('ab')} 在 Trie 里，fail = {st(fb['bab'])}；{st('bca')} 的后缀 {st('ca')} 在，fail = {st(fb['bca'])}；"
          f"{st('caa')} 的后缀 {st('aa')} 不在、{st('a')} 在，fail = {st(fb['caa'])}。")
    S.note("(1) fail：" + "，".join(f"{st(k)} → {st(v) if v != 'ε' else 'ε'}" for k, v in fb.items()), color=Y)
    u = 0
    seq = []
    occ = []
    for i, c in enumerate(QTEXT, start=1):
        u = qa.go(u, c)
        seq.append(qa.s[u] or "ε")
        occ += [(i, k) for k in qa.outputs(u)]
    assert sorted(occ) == brute_occ(QPATS, QTEXT)
    S.say("(2) 依次到达 " + " → ".join(st(x) if x != "ε" else "ε" for x in seq) + "。")
    S.say("找到：" + "、".join(f"{st(QPATS[k])}（结尾在第 {i} 位）" for i, k in occ) + "。", extra=0.5)
    S.note("(2) " + "、".join(f"{st(QPATS[k])}@{i}" for i, k in occ), color=G)

    S.recap([
        "把所有模式串放进 Trie；fail(u) 指向 str(u) 在 Trie 里的最长真后缀——多串版的 π。",
        "按 BFS 构造：v 是 u 的 c 儿子，沿 fail(u) 的链找第一个有 c 儿子的结点。",
        "补全转移 trans(u, c) 后，扫描文本每个字符只走一步，O(|T|)。",
        "到达一个结点时，它 fail 链上的所有模式串都在当前位置结尾。",
    ], next_title="fail 树")
