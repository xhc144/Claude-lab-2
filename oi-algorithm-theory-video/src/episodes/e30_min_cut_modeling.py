"""第 30 集 最小割建模：割就是一种选择"""

import itertools

from episodes.common import *
from episodes.e29_max_flow import edmonds_karp

A_COST = {1: 1, 2: 7, 3: 3}
B_COST = {1: 2, 2: 3, 3: 5}
PAIR = {(1, 2): 4, (2, 3): 1}
INF = 10 ** 6

PROFIT = {"P1": 10, "P2": 6}
NEED = {"P1": ["T1", "T2"], "P2": ["T2", "T3"]}
TOOL = {"T1": 4, "T2": 3, "T3": 8}


def two_choice():
    caps = []
    for i in A_COST:
        caps.append(("s", str(i), B_COST[i]))
        caps.append((str(i), "t", A_COST[i]))
    for (i, j), c in PAIR.items():
        caps.append((str(i), str(j), c))
        caps.append((str(j), str(i), c))
    flow, aug, reach, fl = edmonds_karp(caps)
    best = None
    for sides in itertools.product("AB", repeat=3):
        asg = dict(zip(A_COST, sides))
        cost = sum(A_COST[i] if asg[i] == "A" else B_COST[i] for i in A_COST)
        cost += sum(c for (i, j), c in PAIR.items() if asg[i] != asg[j])
        if best is None or cost < best[0]:
            best = (cost, asg)
    assert best[0] == flow
    return flow, reach, best


def closure():
    caps = [("s", p, w) for p, w in PROFIT.items()] + [(t, "t", c) for t, c in TOOL.items()]
    for p, ts in NEED.items():
        for t in ts:
            caps.append((p, t, INF))
    flow, aug, reach, fl = edmonds_karp(caps)
    best = None
    for k in range(len(PROFIT) + 1):
        for ps in itertools.combinations(PROFIT, k):
            tools = set(t for p in ps for t in NEED[p])
            val = sum(PROFIT[p] for p in ps) - sum(TOOL[t] for t in tools)
            if best is None or val > best[0]:
                best = (val, ps)
    assert sum(PROFIT.values()) - flow == best[0]
    return flow, reach, best


def build(S):
    S.cover("一堆东西各自要在两种选择里挑一个，选择之间还有代价和约束。怎样把“怎么选”变成“怎么割”，用最大流求出来？",
            ["最大流 = 最小割（第 29 集）"])

    # ------------------------------------------------------------ 割 = 选择
    S.section("割就是一种分组")
    S.say("一个割把所有点分成两组：和 s 在一起的（S 侧）、和 t 在一起的（T 侧）。每个点必须二选一。")
    S.note("割 = 把每个点分到 S 侧或 T 侧（二选一）", color=Y)
    S.say("如果每个“东西”都要在两种选择 A、B 中选一个，就让它对应一个点：分到 S 侧表示选 A，T 侧表示选 B。")
    S.note("点 i 在 S 侧 ⇔ 选 A；在 T 侧 ⇔ 选 B")
    S.say("然后设计边的容量，让“割的容量”恰好等于“这种选法的总代价”。最小割就是最优选法。")
    S.note("设计边：割的容量 = 选法的代价 → 最小割 = 最优解", color=G)

    # ------------------------------------------------------------ 二选一
    S.section("二选一：两台机器")
    S.say("例：3 个任务，每个放在机器 A 或机器 B 上运行，代价如下。另外，任务 1、2 如果不在同一台机器，要额外通信代价 4；任务 2、3 不在同一台要 1。")
    tb = Grid(3, 2, x=330, y=330, cw=150, ch=58, gap=6, size=26, rlab=["任务1", "任务2", "任务3"], clab=["放 A", "放 B"],
              vals=[[A_COST[i], B_COST[i]] for i in (1, 2, 3)], lab_color=FG)
    S.show(tb)
    S.show(label(330, 500, "1、2 分开 +4；2、3 分开 +1", 26, O))
    S.note("i 放 A 代价 aᵢ，放 B 代价 bᵢ；i、j 分开额外 cᵢⱼ")
    pos = {"s": (-330, 0), "1": (-60, -180), "2": (-60, 0), "3": (-60, 180), "t": (230, 0)}
    caps = [("s", str(i), f"b={B_COST[i]}") for i in A_COST] + [(str(i), "t", f"a={A_COST[i]}") for i in A_COST]
    gg = Graph(pos, caps + [("1", "2", None), ("2", "3", None)], x=900, y=520, directed=True, r=30, size=24, wsize=22,
               wcolor=FG)
    for e in [("1", "2"), ("2", "3")]:
        gg.edge(*e).tr["head"].base = 0
        gg.edge(*e).tr["color"].base = O
    gg.etag("1", "2", "4", color=O, size=22, hidden=False)
    gg.etag("2", "3", "1", color=O, size=22, hidden=False)
    S.show(gg)
    S.say("各自挑便宜的：1 放 A、2 放 B、3 放 A，代价 1 + 3 + 3，再加上两对都分开的 4 + 1，一共 12。可见不能各管各的。")
    S.say("建图：s → i 容量 bᵢ，i → t 容量 aᵢ。如果 i 在 S 侧（选 A），被割断的是 i → t，付 aᵢ；在 T 侧（选 B），被割断的是 s → i，付 bᵢ。")
    S.note("s → i 容量 bᵢ（i 选 B 时被割）；i → t 容量 aᵢ（i 选 A 时被割）", color=Y)
    S.say("任务之间连双向边，容量 cᵢⱼ。两个任务在同一侧，这条边不被割；在不同侧，恰好有一个方向从 S 指向 T，被割，付 cᵢⱼ。")
    S.note("i ↔ j 双向边容量 cᵢⱼ：分在两侧时恰好割一次", color=O)
    flow, reach, best = two_choice()
    S.say(f"跑最大流：最小割 = {flow}。对应的分组：" + "、".join(f"任务{i}放{best[1][i]}" for i in (1, 2, 3)) + "。枚举全部 8 种放法，最优代价也是这个数。")
    S.play(*[gg[v].to(fill=tint(CY, 0.45), stroke=CY) for v in reach], *[gg[v].to(fill=tint(O, 0.45), stroke=O) for v in pos if v not in reach],
           dur=0.6)
    S.say("为什么对？每一种放法对应一个割，割的容量恰好等于放法的代价；反过来每个割也对应一种放法。所以最小割 = 最小代价。")
    S.note("放法 ↔ 割（一一对应，代价 = 容量）", color=G)

    # ------------------------------------------------------------ 无穷边
    S.section("无穷边：表示“不允许”")
    S.say("约束“如果 i 选 A，那么 j 也必须选 A”怎么表达？连一条 i → j，容量 ∞。")
    S.note("“i 在 S 侧 ⇒ j 也在 S 侧”：边 i → j 容量 ∞", color=Y)
    S.say("如果违反约束（i 在 S 侧、j 在 T 侧），这条 ∞ 边就从 S 指向 T，会被割，割的容量变成 ∞——最小割绝不会选它。")
    S.say("注意方向：i 在 T 侧、j 在 S 侧时，边 j ← i 从 T 指向 S，不计入割的容量，不受影响。所以一条 ∞ 边正好表达一个“蕴含”。")
    S.note("∞ 边只禁止 “i 在 S、j 在 T” 这一种情况", color=G)

    # ------------------------------------------------------------ 最大权闭合子图
    S.section("最大权闭合子图")
    S.say("经典模型：有一些项目和一些工具。做项目 i 能赚 pᵢ，但需要它要求的所有工具；买工具 j 花 cⱼ。选哪些项目，净收益最大？")
    S.note("做项目赚 pᵢ，需要的工具都要买（花 cⱼ），求最大净收益")
    cpos = {"s": (-420, 0), "P1": (-160, -130), "P2": (-160, 130), "T1": (140, -200), "T2": (140, 0), "T3": (140, 200), "t": (420, 0)}
    ce = [("s", p, f"{w}") for p, w in PROFIT.items()] + [(t, "t", f"{c}") for t, c in TOOL.items()]
    ce += [(p, t, "∞") for p in NEED for t in NEED[p]]
    cg = Graph(cpos, ce, x=600, y=500, directed=True, r=30, size=22, wsize=22, wcolor=FG)
    S.show(cg)
    S.say("建图：s → 项目，容量是利润；工具 → t，容量是成本；项目 → 它需要的工具，容量 ∞。S 侧 = “选了”的项目和工具。")
    S.note("s → 项目 pᵢ；工具 → t cⱼ；项目 → 所需工具 ∞", color=Y)
    S.say("割的含义：s → 项目被割 = 放弃这个项目，损失利润；工具 → t 被割 = 买了这个工具，付出成本；∞ 边保证选了项目就一定选了它的工具。")
    S.note("答案 = 所有利润之和 − 最小割", color=G)
    flow2, reach2, best2 = closure()
    S.say(f"所有利润 {sum(PROFIT.values())}，最小割 {flow2}，答案 {sum(PROFIT.values())} − {flow2} = {best2[0]}：只做 P1，买 T1、T2。")
    S.play(*[cg[v].to(fill=tint(CY, 0.45), stroke=CY) for v in reach2], *[cg[v].to(fill=tint(O, 0.45), stroke=O) for v in cpos if v not in reach2],
           dur=0.6)
    S.say("“利润之和 − 最小割”的意思是：先假设所有项目都做，最小割算出“为了满足依赖而必须付出的最小代价”（放弃的利润或买工具的钱）。")

    # ------------------------------------------------------------ 手推题
    S.quiz("选课：4 门课，选课 i 得分 wᵢ = 5, −2, 3, −4（可以是负的，比如太难的课）。\n"
           "约束：选 1 必须选 2；选 3 必须选 4。\n\n"
           "(1) 用最小割建模：正分、负分、约束分别怎样连边？\n"
           "(2) 最大得分是多少？", think=20)
    S.say("(1) 这就是最大权闭合子图：正分的课 s → i 容量 wᵢ；负分的课 i → t 容量 −wᵢ；“选 i 必须选 j”连 i → j 容量 ∞。")
    S.note("(1) 正分：s → i 容 wᵢ；负分：i → t 容 −wᵢ；依赖 i → j 容 ∞", color=Y)
    qpos = {"s": (-380, 0), "1": (-120, -120), "3": (-120, 120), "2": (140, -120), "4": (140, 120), "t": (400, 0)}
    qcaps = [("s", "1", 5), ("s", "3", 3), ("2", "t", 2), ("4", "t", 4), ("1", "2", INF), ("3", "4", INF)]
    qf, qa, qr, qfl = edmonds_karp(qcaps)
    qg = Graph(qpos, [(u, v, "∞" if c == INF else str(c)) for u, v, c in qcaps], x=560, y=560, directed=True, r=30, size=24,
               wsize=22, wcolor=FG)
    S.show(qg)
    S.say(f"(2) 正分之和 5 + 3 = 8。最小割 = {qf}：选 1、2 净赚 3（割 2→t 付 2），3、4 不划算（割 s→3 放弃 3）。答案 8 − {qf} = {8 - qf}。")
    S.play(*[qg[v].to(fill=tint(CY, 0.45), stroke=CY) for v in qr], *[qg[v].to(fill=tint(O, 0.45), stroke=O) for v in qpos if v not in qr],
           dur=0.6)
    S.note(f"(2) 8 − {qf} = {8 - qf}（选 1、2）", color=G)

    S.recap([
        "割把每个点分到 S 侧或 T 侧，天然表示“二选一”。",
        "设计容量，让割的容量等于选法的代价：s → i 和 i → t 表示单点代价，i ↔ j 表示“分开”的代价。",
        "∞ 边 i → j 表示蕴含：i 在 S 侧则 j 必须在 S 侧。",
        "最大权闭合子图：s → 正权点，负权点 → t，依赖连 ∞；答案 = 正权和 − 最小割。",
    ], next_title="分块：整块打标记，零散暴力")
