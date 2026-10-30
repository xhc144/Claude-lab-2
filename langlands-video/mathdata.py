"""视频里「一个具体的例子」用到的真实数据。

椭圆曲线 E: y² + y = x³ − x²（Cremona 11a3，导子 11），模形式 q∏(1−qⁿ)²(1−q¹¹ⁿ)²（权 2、级 11）。
对每个质数 p，Nₚ 是方程在 𝔽ₚ 上的解数（不含无穷远点），aₚ 是模形式展开里 qᵖ 的系数。
模性定理说 p − Nₚ = aₚ。这里对 10000 以内的所有质数都真的算一遍，画面上的数字都来自这里。
"""

import json
from pathlib import Path

import numpy as np

LIMIT = 10000
CACHE = Path(__file__).resolve().parent / "build" / "mathdata.json"


def primes_below(n):
    sieve = np.ones(n, bool)
    sieve[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    return [int(p) for p in np.nonzero(sieve)[0]]


def count_points(p):
    """y² + y = x³ − x² 在 𝔽ₚ 上的解数。"""
    x = np.arange(p, dtype=np.int64)
    rhs = (x * x % p * x - x * x) % p
    y = np.arange(p, dtype=np.int64)
    lhs = (y * y + y) % p
    counts = np.bincount(lhs, minlength=p)
    return int(counts[rhs].sum())


def solutions(p):
    """解的坐标列表，画「模 p 网格」用。"""
    return [(x, y) for x in range(p) for y in range(p) if (y * y + y - x ** 3 + x * x) % p == 0]


def q_expansion(n):
    """q∏(1−qᵏ)²(1−q¹¹ᵏ)² 的前 n 项系数，返回 a，a[i] 是 qⁱ 的系数。"""
    c = np.zeros(n, np.int64)
    c[0] = 1  # 先算 ∏ 部分，最后整体乘 q（下标平移一位）

    def times(k):
        if k < n:
            c[k:] -= c[:-k].copy()

    for k in range(1, n):
        times(k)
        times(k)
        if 11 * k < n:
            times(11 * k)
            times(11 * k)
    a = np.zeros(n + 1, np.int64)
    a[1:] = c
    return a


def compute():
    ps = primes_below(LIMIT)
    a = q_expansion(LIMIT + 1)
    rows = []
    for p in ps:
        n = count_points(p)
        rows.append({"p": p, "N": n, "a": int(a[p])})
    data = {
        "rows": rows,
        "series": [int(v) for v in a[1:21]],  # q¹ … q²⁰ 的系数
        "all_match": all(r["p"] - r["N"] == r["a"] for r in rows),
    }
    return data


def load():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    data = compute()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data))
    return data


if __name__ == "__main__":
    d = compute()
    print(len(d["rows"]), "个质数，全部吻合：", d["all_match"])
    print(d["rows"][:12])
    print("q 展开：", d["series"])
