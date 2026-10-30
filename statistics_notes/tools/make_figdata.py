"""生成讲义插图所用的数据文件（figdata/*.dat）。

精确计算优先；需要模拟的图都固定了随机种子，可重复。
运行：python tools/make_figdata.py（需要 numpy、scipy）
"""
import itertools
import math
import os

import numpy as np
from scipy import stats

OUT = os.path.join(os.path.dirname(__file__), "..", "figdata")
os.makedirs(OUT, exist_ok=True)


def save(name, header, rows):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(" ".join(header) + "\n")
        for r in rows:
            f.write(" ".join(f"{v:.6g}" if isinstance(v, float) else str(v) for v in r) + "\n")


# ---------- 第0章：中心极限定理（二项分布标准化后的“密度”） ----------
p = 0.2
for n in (5, 20, 100):
    sd = math.sqrt(n * p * (1 - p))
    rows = []
    for k in range(n + 1):
        z = (k - n * p) / sd
        if -4 <= z <= 4.5:
            rows.append((z, stats.binom.pmf(k, n, p) * sd, 1.0 / sd))
    save(f"clt_n{n}.dat", ["z", "h", "w"], rows)

# ---------- 第1章：样本均值的抽样分布 ----------
p = 0.3
for n in (5, 20, 80):
    rows = [(k / n, stats.binom.pmf(k, n, p)) for k in range(n + 1)]
    save(f"xbar_n{n}.dat", ["x", "prob"], rows)

# ---------- 第2章：偏差与方差的靶图 ----------
rng = np.random.default_rng(7)
base = rng.standard_normal((12, 2))
for name, (cx, cy, s) in {
    "tgt_lb_lv": (0, 0, 0.16), "tgt_hb_lv": (0.55, 0.35, 0.16),
    "tgt_lb_hv": (0, 0, 0.42), "tgt_hb_hv": (0.55, 0.35, 0.42)}.items():
    save(f"{name}.dat", ["x", "y"], [(cx + s * a, cy + s * b) for a, b in base])

# ---------- 第2章：U(0,θ) 两个估计量的抽样密度（θ=1, n=10） ----------
n = 10
def irwin_hall_pdf(x, n):
    # n 个 U(0,1) 之和的密度
    s = 0.0
    for k in range(int(math.floor(x)) + 1):
        s += (-1) ** k * math.comb(n, k) * (x - k) ** (n - 1)
    return s / math.factorial(n - 1)
rows = []
for t in np.linspace(0.4, 1.6, 241):
    # T1 = 2*Xbar = (2/n) * sum  => density f(t) = (n/2) * IH(n t / 2)
    f1 = (n / 2) * irwin_hall_pdf(n * t / 2, n) if 0 < n * t / 2 < n else 0.0
    # T3 = (n+1)/n * M, M 密度 n m^(n-1)
    m = t * n / (n + 1)
    f3 = n * m ** (n - 1) * n / (n + 1) if 0 < m <= 1 else 0.0
    rows.append((float(t), f1, f3))
save("unif_est_density.dat", ["t", "f2xbar", "fmax"], rows)

# ---------- 第4章：置信区间的覆盖（40 个 95% t 区间，N(50,10^2)，n=10） ----------
rng = np.random.default_rng(2026)
mu, sigma, n = 50, 10, 10
tq = stats.t.ppf(0.975, n - 1)
rows = []
for i in range(1, 41):
    x = rng.normal(mu, sigma, n)
    m, s = x.mean(), x.std(ddof=1)
    lo, hi = m - tq * s / math.sqrt(n), m + tq * s / math.sqrt(n)
    rows.append((i, float(m), float(lo), float(hi), int(lo <= mu <= hi)))
save("ci_cover.dat", ["i", "m", "lo", "hi", "cover"], rows)
print("CI covered:", sum(r[4] for r in rows), "of 40")

# ---------- 第4章：t 分布与正态 ----------
rows = []
for x in np.linspace(-4.5, 4.5, 181):
    rows.append((float(x), stats.norm.pdf(x), stats.t.pdf(x, 1), stats.t.pdf(x, 3), stats.t.pdf(x, 10)))
save("tdens.dat", ["x", "norm", "t1", "t3", "t10"], rows)

# ---------- 第4章：比例区间的真实覆盖率（n=30） ----------
n, z = 30, stats.norm.ppf(0.975)
rows = []
for p in np.linspace(0.005, 0.995, 397):
    k = np.arange(n + 1)
    ph = k / n
    w_lo, w_hi = ph - z * np.sqrt(ph * (1 - ph) / n), ph + z * np.sqrt(ph * (1 - ph) / n)
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    pmf = stats.binom.pmf(k, n, p)
    wald = pmf[(w_lo <= p) & (p <= w_hi)].sum()
    wil = pmf[(c - h <= p) & (p <= c + h)].sum()
    rows.append((float(p), float(wald), float(wil)))
save("prop_cover.dat", ["p", "wald", "wilson"], rows)

# ---------- 第4章：功效函数（单侧 z 检验，σ=1，α=0.05） ----------
za = stats.norm.ppf(0.95)
rows = []
for mu in np.linspace(-0.5, 1.5, 201):
    rows.append((float(mu),) + tuple(float(1 - stats.norm.cdf(za - mu * math.sqrt(n))) for n in (10, 40)))
save("power.dat", ["mu", "n10", "n40"], rows)

# ---------- 第5章：睡眠数据 ----------
g1 = np.array([0.7, -1.6, -0.2, -1.2, -0.1, 3.4, 3.7, 0.8, 0.0, 2.0])
g2 = np.array([1.9, 0.8, 1.1, 0.1, -0.1, 4.4, 5.5, 1.6, 4.6, 3.4])
d = g2 - g1
save("sleep.dat", ["id", "a", "b", "d"], [(i + 1, float(g1[i]), float(g2[i]), float(round(d[i], 1))) for i in range(10)])
ds = np.sort(d)
q = stats.norm.ppf((np.arange(1, 11) - 0.5) / 10)
save("sleep_qq.dat", ["q", "d"], [(float(a), float(round(b, 1))) for a, b in zip(q, ds)])
# 符号翻转的精确分布：2^10 种符号
sums = {}
for signs in itertools.product((1, -1), repeat=10):
    s = round(float(np.dot(signs, d)), 1)
    sums[s] = sums.get(s, 0) + 1
save("sleep_flip.dat", ["s", "count"], sorted(sums.items()))
print("flip p one-sided:", sum(c for s, c in sums.items() if s >= round(d.sum(), 1)) / 1024)

# ---------- 第5章：方差不等时合并 t 检验的真实第一类错误（模拟） ----------
rng = np.random.default_rng(11)
REPS = 200_000
res = []
for (m, n_) in ((10, 10), (10, 40), (40, 10)):
    for ratio in (1, 2, 4):
        x = rng.standard_normal((REPS, m)) * ratio  # 第一组标准差 = ratio
        y = rng.standard_normal((REPS, n_))
        mx, my = x.mean(1), y.mean(1)
        vx, vy = x.var(1, ddof=1), y.var(1, ddof=1)
        sp2 = ((m - 1) * vx + (n_ - 1) * vy) / (m + n_ - 2)
        tp = (mx - my) / np.sqrt(sp2 * (1 / m + 1 / n_))
        rp = np.mean(np.abs(tp) > stats.t.ppf(0.975, m + n_ - 2))
        se2 = vx / m + vy / n_
        tw = (mx - my) / np.sqrt(se2)
        df = se2 ** 2 / ((vx / m) ** 2 / (m - 1) + (vy / n_) ** 2 / (n_ - 1))
        rw = np.mean(np.abs(tw) > stats.t.ppf(0.975, df))
        res.append((m, n_, ratio, float(rp), float(rw)))
save("welch_sim.dat", ["m", "n", "ratio", "pooled", "welch"], res)
for r in res:
    print("sim", r)

# ---------- 第6章：Forbes 数据 ----------
bp = np.array([194.5, 194.3, 197.9, 198.4, 199.4, 199.9, 200.9, 201.1, 201.4, 201.3,
               203.6, 204.6, 209.5, 208.6, 210.7, 211.9, 212.2])
pr = np.array([20.79, 20.79, 22.40, 22.67, 23.15, 23.35, 23.89, 23.99, 24.02, 24.01,
               25.14, 26.57, 28.49, 27.76, 29.04, 29.88, 30.06])
y = 100 * np.log10(pr)
n = len(bp)
X = np.c_[np.ones(n), bp]
beta = np.linalg.lstsq(X, y, rcond=None)[0]
fit = X @ beta
res_ = y - fit
s = math.sqrt((res_ ** 2).sum() / (n - 2))
h = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)
save("forbes.dat", ["id", "bp", "pres", "lp", "fit", "res", "h", "stdres"],
     [(i + 1, float(bp[i]), float(pr[i]), float(y[i]), float(fit[i]), float(res_[i]), float(h[i]),
       float(res_[i] / (s * math.sqrt(1 - h[i])))) for i in range(n)])
# 原始气压对沸点直线拟合的残差（显示弯曲）
b1 = np.polyfit(bp, pr, 1)
save("forbes_raw_res.dat", ["bp", "res"], [(float(a), float(b - np.polyval(b1, a))) for a, b in zip(bp, pr)])
# 置信带与预测带
xbar, Sxx = bp.mean(), ((bp - bp.mean()) ** 2).sum()
tq = stats.t.ppf(0.975, n - 2)
rows = []
for x0 in np.linspace(193, 213.5, 83):
    m0 = beta[0] + beta[1] * x0
    c = 1 / n + (x0 - xbar) ** 2 / Sxx
    rows.append((float(x0), float(m0), float(m0 - tq * s * math.sqrt(c)), float(m0 + tq * s * math.sqrt(c)),
                 float(m0 - tq * s * math.sqrt(1 + c)), float(m0 + tq * s * math.sqrt(1 + c))))
save("forbes_band.dat", ["x", "m", "clo", "chi", "plo", "phi"], rows)
# 删去第12个点后重新拟合
keep = np.arange(n) != 11
b2 = np.polyfit(bp[keep], y[keep], 1)
s2 = math.sqrt(((y[keep] - np.polyval(b2, bp[keep])) ** 2).sum() / (n - 3))
print("forbes full", beta, s, "R2", 1 - (res_ ** 2).sum() / ((y - y.mean()) ** 2).sum())
print("forbes drop12", b2[::-1], s2)
print("forbes Sxx", Sxx, "xbar", xbar, "ybar", y.mean(), "se slope", s / math.sqrt(Sxx), "tq", tq)

# ---------- 第6章：杠杆点的影响（示意数据） ----------
xs = np.array([1, 2, 3, 4, 5, 6, 7, 8.0])
ys = np.array([2.1, 2.9, 3.2, 4.4, 4.6, 5.3, 6.1, 6.4])
xa, ya = np.append(xs, 16.0), np.append(ys, 4.0)
c0 = np.polyfit(xs, ys, 1)
c1 = np.polyfit(xa, ya, 1)
save("lev_pts.dat", ["x", "y"], [(float(a), float(b)) for a, b in zip(xs, ys)])
Xa = np.c_[np.ones(9), xa]
ha = np.diag(Xa @ np.linalg.inv(Xa.T @ Xa) @ Xa.T)
print("lev lines: without", c0[::-1], "with", c1[::-1], "h_new", ha[-1])

# ---------- 第6章：辛普森悖论（两组示意数据） ----------
rng = np.random.default_rng(5)
rows = []
for g, (x0, y0) in enumerate(((2.0, 3.0), (6.0, 7.5)), start=1):
    xx = x0 + rng.uniform(-1.6, 1.6, 12)
    yy = y0 - 0.6 * (xx - x0) + rng.normal(0, 0.35, 12)
    for a, b in zip(xx, yy):
        rows.append((g, float(a), float(b)))
save("simpson.dat", ["g", "x", "y"], rows)
arr = np.array(rows)
for g in (1, 2):
    sel = arr[:, 0] == g
    print("simpson group", g, np.polyfit(arr[sel, 1], arr[sel, 2], 1))
print("simpson pooled", np.polyfit(arr[:, 1], arr[:, 2], 1))

# ---------- 第6章：残差图示意：真实关系弯曲 ----------
rng = np.random.default_rng(3)
xx = np.linspace(0, 10, 25)
yy = 1 + 0.12 * (xx - 2) ** 2 + rng.normal(0, 0.45, 25)
cc = np.polyfit(xx, yy, 1)
save("curve_res.dat", ["x", "y", "fit", "res"], [(float(a), float(b), float(np.polyval(cc, a)), float(b - np.polyval(cc, a))) for a, b in zip(xx, yy)])
print("curve fit", cc)

# ---------- 第0章：大数定律——三条抛币序列的累计正面比例（模拟） ----------
rng = np.random.default_rng(20261021)
ns = np.unique(np.round(np.logspace(0, 3, 160)).astype(int))
rows = []
paths = [np.cumsum(rng.random(1000) < 0.5) / np.arange(1, 1001) for _ in range(3)]
for k in ns:
    rows.append((int(k),) + tuple(float(pth[k - 1]) for pth in paths) +
                (0.5 - 2 * math.sqrt(0.25 / k), 0.5 + 2 * math.sqrt(0.25 / k)))
save("lln.dat", ["n", "p1", "p2", "p3", "lo", "hi"], rows)
