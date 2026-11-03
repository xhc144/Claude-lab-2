"""第三轮续写 03d--03i（概率论补充）的核验：精确计算、数值积分与 Monte Carlo。数值核验只覆盖所测参数。"""
import math, itertools, json, fractions
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, special, stats, optimize, linalg

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(6)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
F = fractions.Fraction

# ---------- 03d 离散 ----------
pmf = {k: F(5, 6)**(k - 1)*F(1, 6) for k in range(1, 400)}
check('3d', "尾和公式 E X² = Σ(2k-1)P(X≥k)（几何分布）", abs(float(sum(k*k*p for k, p in pmf.items())) - float(sum((2*k - 1)*F(5, 6)**(k - 1) for k in range(1, 400)))) < 1e-9)
N_, K_, n_ = 20, 7, 6
hv = sum((k - n_*K_/N_)**2*math.comb(K_, k)*math.comb(N_ - K_, n_ - k)/math.comb(N_, n_) for k in range(n_ + 1))
check('3d', "超几何方差含 (N-n)/(N-1)", close(hv, n_*K_/N_*(N_ - K_)/N_*(N_ - n_)/(N_ - 1)))
check('3d', "阶乘矩 E[X^(k)] = n^(k) p^k", close(sum(math.perm(k, 3)*math.comb(10, k)*0.3**k*0.7**(10 - k) for k in range(11)), math.perm(10, 3)*0.3**3))
fp = [sum(1 for p in itertools.permutations(range(7)) if sum(p[i] == i for i in range(7)) == k) for k in range(8)]
check('3d', "配对问题 P(F=k) 公式与前 n 阶矩 = Bell 数", all(F(fp[k], math.factorial(7)) == F(1, math.factorial(k))*sum(F((-1)**j, math.factorial(j)) for j in range(8 - k)) for k in range(8))
      and [sum(k**m*fp[k] for k in range(8))//math.factorial(7) for m in range(1, 8)] == [1, 2, 5, 15, 52, 203, 877])
m_, nb = 6, 9
E_emp = sum(sum(1 for b in range(m_) if b not in c) for c in itertools.product(range(m_), repeat=nb))/m_**nb
V_emp = sum(sum(1 for b in range(m_) if b not in c)**2 for c in itertools.product(range(m_), repeat=nb))/m_**nb - E_emp**2
check('3d', "空盒数均值与方差（穷举 6 盒 9 球）", close(E_emp, m_*(1 - 1/m_)**nb) and close(V_emp, m_*(m_ - 1)*(1 - 2/m_)**nb + m_*(1 - 1/m_)**nb - m_**2*(1 - 1/m_)**(2*nb)))
ET = sum(math.prod(1 - j/365 for j in range(k)) for k in range(0, 366))
check('3d', "首次重复 E T ≈ √(πm/2)+2/3 (m=365)", abs(ET - (math.sqrt(math.pi*365/2) + 2/3)) < 0.02, f"{ET:.4f}")
def conway(A, B): return sum(2**(k - 1) for k in range(1, len(A) + 1) if A[-k:] == B[:k])
def sim_penney(A, B, trials=200000):
    w = 0; r = rng.integers(0, 2, size=(trials, 60))
    s = np.array(['HT'[x] for x in r.ravel()]).reshape(trials, 60)
    for row in s:
        st = ''.join(row); ia, ib = st.find(A), st.find(B)
        w += (ib != -1 and (ia == -1 or ib < ia))
    return w/trials
pb = sim_penney('HHT', 'THH', 40000)
check('3d', "Penney: THH 胜 HHT 赔率 3:1；E T_HH=6", conway('HHT', 'HHT') == 4 and conway('HHT', 'THH') == 1 and conway('THH', 'THH') == 4 and conway('THH', 'HHT') == 3 and abs(pb - 0.75) < 0.01 and 2*conway('HH', 'HH') == 6)
u = lambda n: math.comb(2*n, n)/4**n
fret = {}
for n in range(1, 9):
    fret[n] = u(n) - sum(fret[k]*u(n - k) for k in range(1, n))
check('3d', "首次返回 f_2n = u_2n/(2n-1)", all(close(fret[n], u(n)/(2*n - 1)) for n in range(1, 9)))
nn = 10; walks = np.array(list(itertools.product([-1, 1], repeat=nn))); S = np.cumsum(walks, 1); M = S.max(1)
check('3d', "反射: P(M_n≥k)=P(S_n≥k)+P(S_n>k)", all(close(np.mean(M >= k), np.mean(S[:, -1] >= k) + np.mean(S[:, -1] > k)) for k in range(1, 8)))
Wm = np.array(list(itertools.product([-1, 1], repeat=12))); Sm = np.cumsum(Wm, 1)
last0 = np.array([max([0] + [i + 1 for i in range(12) if s[i] == 0]) for s in Sm])
check('3d', "离散反正弦律 P(L=2k)=u_2k u_{2n-2k}", all(close(np.mean(last0 == 2*k), u(k)*u(6 - k)) for k in range(7)))
perms = list(itertools.permutations(range(7))); inv = [sum(p[i] > p[j] for i in range(7) for j in range(i + 1, 7)) for p in perms]
rec = [sum(1 for i in range(7) if p[i] == max(p[:i + 1])) for p in perms]
check('3d', "逆序方差 n(n-1)(2n+5)/72；记录数方差 H_n-ΣH^(2)", close(np.var(inv), 7*6*19/72) and close(np.var(rec), sum(1/k for k in range(1, 8)) - sum(1/k**2 for k in range(1, 8))))
Nt, kt = 30, 4
check('3d', "无放回抽样 E min=(N+1)/(k+1)", close(np.mean([min(c) for c in itertools.combinations(range(1, Nt + 1), kt)]), (Nt + 1)/(kt + 1)))
check('3d', "PGF 奇偶概率", close(sum(math.comb(9, k)*0.3**k*0.7**(9 - k) for k in range(0, 10, 2)), (1 + 0.4**9)/2))
q_ = 0.8; nmax = 10
Emax = sum(1 - (1 - q_**(k - 1))**nmax for k in range(1, 2000))
check('3d', "几何最大值 ≈ H_n/(-ln q)+1/2", abs(Emax - (sum(1/k for k in range(1, 11))/(-math.log(q_)) + 0.5)) < 0.05, f"{Emax:.3f}")
def monty(n, k, trials=200000):
    prize = rng.integers(0, n, trials); pick = rng.integers(0, n, trials); win = 0
    for pz, pk in zip(prize[:40000], pick[:40000]):
        others = [d for d in range(n) if d != pk and d != pz]; opened = set(rng.choice(others, k, replace=False))
        rem = [d for d in range(n) if d != pk and d not in opened]; win += rng.choice(rem) == pz
    return win/40000
check('3d', "Monty Hall 推广 (n=5,k=2): (n-1)/(n(n-k-1))", abs(monty(5, 2) - 4/(5*2)) < 0.01)
Nm = 50; uk = [math.comb(2*Nm - k, Nm)*2.0**(-(2*Nm - k)) for k in range(Nm + 1)]
check('3d', "Banach 火柴盒分布归一与 E k=(2N+1)C(2N,N)/4^N-1", close(sum(uk), 1, 1e-9) and close(sum(k*p for k, p in enumerate(uk)), (2*Nm + 1)*math.comb(2*Nm, Nm)/4**Nm - 1, 1e-10))
check('3d', "首张 A 前的牌数期望 48/5", close(np.mean([next(i for i, c in enumerate(rng.permutation(52)) if c < 4) for _ in range(100000)]), 9.6, 0.01))
fam = [(a, b, da, db) for a in 'BG' for b in 'BG' for da in range(7) for db in range(7)]
cond = [f for f in fam if (f[0] == 'B' and f[2] == 1) or (f[1] == 'B' and f[3] == 1)]
check('3d', "“周二出生的男孩” 13/27", F(sum(1 for f in cond if f[0] == f[1] == 'B'), len(cond)) == F(13, 27))
rolls = rng.integers(1, 7, size=(400000, 120)); first6 = np.argmax(rolls == 6, 1)
alleven = np.array([np.all(r[:i] % 2 == 0) for r, i in zip(rolls, first6)])
ET_tot = F(0); ET_cond_num = F(0); ET_cond_den = F(0)
for k in range(1, 200):
    ET_tot += F(5, 6)**(k - 1)*F(1, 6)*(F(3)*(k - 1) + 6)        # 前 k-1 次非 6 均值 3，最后一次 6
    ET_cond_num += k*F(1, 3)**(k - 1)*F(1, 6); ET_cond_den += F(1, 3)**(k - 1)*F(1, 6)
check('3d', "Wald：出 6 前总分期望 21；条件“之前全偶”时 E T=3/2（级数精确求和）", abs(float(ET_tot) - 21) < 1e-12 and abs(float(ET_cond_num/ET_cond_den) - 1.5) < 1e-12 and abs(np.mean(first6[alleven] + 1) - 1.5) < 0.01)

# ---------- 03e 连续 ----------
Z = rng.normal(size=(1_000_000, 3))
check('3e', "t² = F(1,k) 分位数；Beta 与 F 关系", close(stats.t.ppf(0.975, 7)**2, stats.f.ppf(0.95, 1, 7)) and close(stats.beta.cdf(3*1.7/(3*1.7 + 8), 1.5, 4), stats.f.cdf(1.7, 3, 8), 1e-10))
check('3e', "对数正态均值方差众数", close(stats.lognorm(0.6, scale=math.exp(0.3)).mean(), math.exp(0.3 + 0.18)) and close(stats.lognorm(0.6, scale=math.exp(0.3)).var(), (math.exp(0.36) - 1)*math.exp(0.6 + 0.36)))
U = np.sort(rng.random((200000, 6)), 1)
check('3e', "均匀极差 E R=(n-1)/(n+1)", abs((U[:, -1] - U[:, 0]).mean() - 5/7) < 2e-3)
Ex = np.sort(rng.exponential(1/2.0, size=(200000, 5)), 1)
check('3e', "Rényi：指数次序统计量均值 (H_n-H_{n-k})/λ、间隔独立", abs(Ex[:, 2].mean() - (sum(1/j for j in range(1, 6)) - sum(1/j for j in range(1, 3)))/2) < 3e-3 and abs(np.corrcoef(Ex[:, 1] - Ex[:, 0], Ex[:, 3] - Ex[:, 2])[0, 1]) < 0.01)
S = np.cumsum(rng.random((300000, 20)), 1); Nn = np.argmax(S > 1, 1) + 1
check('3e', "超过 1 所需均匀数 E N = e；P(S_n≤1)=1/n!", abs(Nn.mean() - math.e) < 0.01 and abs(np.mean(S[:, 3] <= 1) - 1/24) < 2e-3)
check('3e', "E χ_k 公式；E|Z|^p", close(np.mean(np.linalg.norm(Z, axis=1)), math.sqrt(2)*math.gamma(2)/math.gamma(1.5), 2e-3) and close(np.mean(np.abs(Z[:, 0])**1.5), 2**0.75*math.gamma(1.25)/math.sqrt(math.pi), 3e-3))
Sig = np.array([[2, 0.5, 0], [0.5, 1, 0.3], [0, 0.3, 1.5]]); X = rng.multivariate_normal(np.zeros(3), Sig, 400000)
md = np.einsum('ij,jk,ik->i', X, np.linalg.inv(Sig), X)
check('3e', "Mahalanobis ~ χ²_3", abs(md.mean() - 3) < 0.01 and abs(md.var() - 6) < 0.05)
check('3e', "Stein 引理 E[Z g(Z)] = E g'(Z) (g=sin)", close(math.exp(-0.5), float(mp.quad(lambda z: z*mp.sin(z)*mp.npdf(z), [-mp.inf, mp.inf]))))
xs = np.linspace(0.1, 8, 200); tail = stats.norm.sf(xs); phi = stats.norm.pdf(xs)
check('3e', "Mills 比上下界", np.all(xs/(1 + xs**2)*phi <= tail) and np.all(tail <= phi/xs))
check('3e', "截断正态均值 = 逆 Mills 比", close(integrate.quad(lambda z: z*stats.norm.pdf(z), 1.3, np.inf)[0]/stats.norm.sf(1.3), stats.norm.pdf(1.3)/stats.norm.sf(1.3)))
sg = 1.5; zz = rng.normal(size=2_000_000)
check('3e', "对数正态最大相关公式", abs(np.corrcoef(np.exp(zz), np.exp(sg*zz))[0, 1] - (math.exp(sg) - 1)/math.sqrt((math.e - 1)*(math.exp(sg**2) - 1))) < 0.02)
lam_ = rng.gamma(3.0, 1/1.5, 1_000_000); Nnb = rng.poisson(lam_)
check('3e', "Gamma–Poisson：Var = μ + μ²/r", abs(Nnb.var() - (2 + 4/3)) < 0.02)
check('3e', "正态尺度混合 → t_ν, Laplace", abs(stats.kstest(rng.normal(size=200000)*np.sqrt(1/rng.gamma(2.5, 1/2.5, 200000)), stats.t(5).cdf).statistic) < 0.005
      and abs(stats.kstest(rng.normal(size=200000)*np.sqrt(rng.exponential(2*0.7**2, 200000)), stats.laplace(scale=0.7).cdf).statistic) < 0.005)
al = np.array([1.5, 2.0, 0.5]); D = rng.dirichlet(al, 1_000_000); a0 = al.sum()
check('3e', "Dirichlet 协方差公式", abs(np.cov(D[:, 0], D[:, 1])[0, 1] - (-al[0]*al[1]/(a0**2*(a0 + 1)))) < 5e-4 and abs(D[:, 2].var() - al[2]*(a0 - al[2])/(a0**2*(a0 + 1))) < 5e-4)
check('3e', "Lévy 分布 = BM 首达时（与 1/Z² 比较）", abs(stats.kstest(1.3**2/rng.normal(size=200000)**2, stats.levy(scale=1.3**2).cdf).statistic) < 0.005)
l1, l2, l3 = 1.0, 2.5, 4.0
hyp = lambda x: sum(np.prod([lj/(lj - li) for lj in (l1, l2, l3) if lj != li])*li*np.exp(-li*x) for li in (l1, l2, l3))
check('3e', "亚指数密度（三项）", close(integrate.quad(hyp, 0, np.inf)[0], 1) and close(integrate.quad(lambda x: x*hyp(x), 0, np.inf)[0], 1/l1 + 1/l2 + 1/l3))
n_ = 400; W = rng.normal(size=(n_, n_)); W = (W + W.T)/math.sqrt(2); ev = np.linalg.eigvalsh(W/math.sqrt(n_))
check('3e', "Wigner 半圆律：二阶矩 1、谱在 [-2,2]", abs(np.mean(ev**2) - 1) < 0.02 and ev.min() > -2.15 and ev.max() < 2.15)
Xd = rng.normal(size=(200, 800)); evc = np.linalg.eigvalsh(Xd @ Xd.T/800); g_ = 200/800
check('3e', "Marchenko–Pastur 边缘 (1±√γ)²", abs(evc.max() - (1 + math.sqrt(g_))**2) < 0.08 and abs(evc.min() - (1 - math.sqrt(g_))**2) < 0.08)
mu1, mu2, s1, s2, rho = 0.3, -0.2, 1.2, 0.8, 0.4
Xc = rng.multivariate_normal([mu1, mu2], [[s1**2, rho*s1*s2], [rho*s1*s2, s2**2]], 2_000_000)
th_ = math.sqrt(s1**2 + s2**2 - 2*rho*s1*s2); a_ = (mu1 - mu2)/th_
check('3e', "Clark 公式 E max", abs(Xc.max(1).mean() - (mu1*stats.norm.cdf(a_) + mu2*stats.norm.cdf(-a_) + th_*stats.norm.pdf(a_))) < 3e-3)
check('3e', "二项尾 = Beta 分布函数", close(stats.binom.sf(6, 15, 0.37), stats.beta.cdf(0.37, 7, 9), 1e-12))
V = rng.normal(size=(200000, 50)); V /= np.linalg.norm(V, axis=1)[:, None]
check('3e', "球面坐标方差 1/n；两随机单位向量内积方差 1/n", abs(V[:, 0].var() - 1/50) < 3e-4 and abs(np.mean(np.sum(V[:100000]*V[100000:], 1)**2) - 1/50) < 5e-4)

# ---------- 03f 极限定理 ----------
p_ = 0.001
check('3f', "Bern(p) 与 Poi(p) 的 TV 距离 = p(1-e^{-p})", close(0.5*(abs((1 - p_) - math.exp(-p_)) + abs(p_ - p_*math.exp(-p_)) + (1 - math.exp(-p_) - p_*math.exp(-p_))), p_*(1 - math.exp(-p_)), 1e-12))
k_ = np.arange(0, 60); nB = 400
loc = stats.binom.pmf(k_ + 100, nB, 0.3) - np.exp(-((k_ + 100 - 120)/math.sqrt(84))**2/2)/math.sqrt(2*math.pi*84)
check('3f', "局部极限定理误差 O(n^{-1/2})·密度", np.max(np.abs(loc)) < 0.01/math.sqrt(84))
cc = stats.binom.cdf(55, 100, 0.5); check('3f', "连续性修正把误差从 1e-2 降到 1e-4", abs(stats.norm.cdf((55.5 - 50)/5) - cc) < 2e-3 and abs(stats.norm.cdf((55 - 50)/5) - cc) > 1e-2)
sims = []
for _ in range(2000):
    xx = np.sort(rng.random(300)); sims.append(np.max(np.maximum(np.arange(1, 301)/300 - xx, xx - np.arange(0, 300)/300)))
check('3f', "DKW 不等式在模拟中成立", np.mean(np.array(sims) > 0.06) <= 2*math.exp(-2*300*0.06**2))
pz = rng.exponential(size=1_000_000)
check('3f', "Paley–Zygmund（指数分布 θ=1/2）", np.mean(pz > 0.5) >= 0.25*1/2)
Gm = rng.pareto(2.5, size=(20000, 200)) + 1; Mx = Gm.max(1)/200**(1/2.5)
check('3f', "Pareto 最大值 / n^{1/α} → Fréchet", stats.kstest(Mx, lambda x: np.exp(-x**-2.5)).statistic < 0.02)
gaps = rng.gamma(2.0, 1.5, size=(20000, 400)); T_ = np.cumsum(gaps, 1); Nt_ = (T_ <= 300).sum(1)
check('3f', "更新 CLT：Var N(t) ≈ σ²t/μ³", abs(Nt_.var()/(4.5*300/27) - 1) < 0.05 and abs(Nt_.mean() - 300/3) < 1)
phi_ = 0.7; xar = np.zeros(400000)
e_ = rng.normal(size=400000)
for i in range(1, 400000): xar[i] = phi_*xar[i - 1] + e_[i]
bm = xar.reshape(400, 1000).mean(1)
check('3f', "AR(1) 渐近方差 τ_int=(1+φ)/(1-φ)", abs(bm.var()*1000/(xar.var()*(1 + phi_)/(1 - phi_)) - 1) < 0.15)
Tn = rng.normal(size=(200000, 100)).mean(1)
check('3f', "二阶 Delta：n·X̄² → χ²_1", abs(np.mean(100*Tn**2) - 1) < 0.01 and abs(np.var(100*Tn**2) - 2) < 0.03)

# ---------- 03g 随机过程 ----------
lam = 2.0; tt = 5.0
Np = rng.poisson(lam*tt, 200000); waits = np.array([np.sum(tt - rng.random(k)*tt) for k in Np[:50000]])
check('3g', "Poisson 条件均匀：E Σ(t-T_i) = λt²/2", abs(waits.mean() - lam*tt**2/2) < 0.1)
Yc = [rng.exponential(2.0, k).sum() for k in Np[:100000]]
check('3g', "复合 Poisson Var = λt E Y²", abs(np.var(Yc) - lam*tt*8) < 1.0)
Ad = np.array([[0, 1, 1, 0, 0], [1, 0, 1, 1, 0], [1, 1, 0, 1, 1], [0, 1, 1, 0, 1], [0, 0, 1, 1, 0]], float)
Lg = np.diag(Ad.sum(1)) - Ad; Lp = np.linalg.pinv(Lg); Reff = Lp[0, 0] + Lp[4, 4] - 2*Lp[0, 4]
P_ = Ad/Ad.sum(1)[:, None]
def hit(P, target):
    idx = [i for i in range(5) if i != target]; Q_ = P[np.ix_(idx, idx)]
    h = np.linalg.solve(np.eye(4) - Q_, np.ones(4)); out = np.zeros(5); out[idx] = h; return out
check('3g', "往返时间 = 2m R_eff", close(hit(P_, 4)[0] + hit(P_, 0)[4], 2*Ad.sum()/2*Reff, 1e-9))
c_, a_ = 8, 6.0
B = 1.0
for k in range(1, c_ + 1): B = a_*B/(k + a_*B)
check('3g', "Erlang B 递推 = 闭式", close(B, (a_**c_/math.factorial(c_))/sum(a_**k/math.factorial(k) for k in range(c_ + 1))))
Ccalc = c_*B/(c_ - a_*(1 - B))
rho_ = a_/c_; p0 = 1/(sum(a_**k/math.factorial(k) for k in range(c_)) + a_**c_/(math.factorial(c_)*(1 - rho_)))
check('3g', "Erlang C 由 B 得到", close(Ccalc, a_**c_/(math.factorial(c_)*(1 - rho_))*p0))
lam_q, ES, ES2 = 0.7, 1.0, 1.0 + 0.5
arr = np.cumsum(rng.exponential(1/lam_q, 400000)); serv = rng.gamma(2.0, 0.5, 400000)  # 均值 1, E S²=1.5
start = np.empty_like(arr); done = 0.0
for i in range(len(arr)): start[i] = max(arr[i], done); done = start[i] + serv[i]
check('3g', "Pollaczek–Khinchine W_q", abs((start - arr)[50000:].mean() - lam_q*ES2/(2*(1 - lam_q*ES))) < 0.05, f"{(start-arr)[50000:].mean():.3f}")
dt = 1e-3; nst = 1000; Bm = np.cumsum(rng.normal(scale=math.sqrt(dt), size=(20000, nst)), 1)
check('3g', "BM 反射原理 P(M_1≥a)=2P(B_1≥a)", abs(np.mean(Bm.max(1) >= 0.8) - 2*stats.norm.sf(0.8)) < 0.015)
check('3g', "首达时 Laplace 变换 e^{-a√(2λ)}", close(integrate.quad(lambda s: math.exp(-1.7*s)*1.2/math.sqrt(2*math.pi*s**3)*math.exp(-1.44/(2*s)), 0, np.inf)[0], math.exp(-1.2*math.sqrt(3.4)), 1e-7))
Bb = Bm - np.linspace(dt, 1, nst)[None, :]*Bm[:, -1:]
check('3g', "Brown 桥 P(max ≥ a)=e^{-2a²}", abs(np.mean(Bb.max(1) >= 0.7) - math.exp(-2*0.49)) < 0.02)
check('3g', "Kolmogorov 分布与 scipy.kstwobign 一致", close(2*sum((-1)**(k - 1)*math.exp(-2*k*k*1.1**2) for k in range(1, 50)), stats.kstwobign.sf(1.1), 1e-10))
pos = (Bm > 0).mean(1)
check('3g', "反正弦律：正侧时间分布", stats.kstest(pos, lambda x: 2/math.pi*np.arcsin(np.sqrt(np.clip(x, 0, 1)))).statistic < 0.03)
thO, sO, h = 1.3, 0.8, 0.1; xo = np.zeros(300000); nz = rng.normal(size=300000)
for i in range(1, 300000): xo[i] = math.exp(-thO*h)*xo[i - 1] + math.sqrt(sO**2/(2*thO)*(1 - math.exp(-2*thO*h)))*nz[i]
check('3g', "OU 精确离散化：平稳方差与自相关", abs(xo.var() - sO**2/(2*thO)) < 0.01 and abs(np.corrcoef(xo[:-5], xo[5:])[0, 1] - math.exp(-thO*0.5)) < 0.01)
dB = rng.normal(scale=math.sqrt(1e-4), size=(2000, 10000)); Bp = np.cumsum(dB, 1)
check('3g', "∫B dB = (B²-t)/2", np.max(np.abs(np.sum((Bp - dB)*dB, 1) - (Bp[:, -1]**2 - 1)/2)) < 0.05)
S0, K, r, sig, T = 100, 105, 0.03, 0.25, 0.75
d1 = (math.log(S0/K) + (r + sig**2/2)*T)/(sig*math.sqrt(T)); d2 = d1 - sig*math.sqrt(T)
ST = S0*np.exp((r - sig**2/2)*T + sig*math.sqrt(T)*rng.normal(size=2_000_000))
check('3g', "Black–Scholes 与 Monte Carlo", abs(math.exp(-r*T)*np.maximum(ST - K, 0).mean() - (S0*stats.norm.cdf(d1) - K*math.exp(-r*T)*stats.norm.cdf(d2))) < 0.05)
mu_, s2_ = 1.4, 0.9
Zs = np.ones(200000)
for g in range(4): Zs = rng.poisson(mu_*Zs)   # Poisson 后代：z 个个体的后代总数 ~ Poi(μz)
check('3g', "分支过程 Var Z_n = σ²μ^{n-1}(μ^n-1)/(μ-1)（Poisson 后代）", abs(Zs.var() - mu_*mu_**3*(mu_**4 - 1)/(mu_ - 1)) < 0.05*mu_*mu_**3*(mu_**4 - 1)/(mu_ - 1))
check('3g', "Borel 分布归一、均值 1/(1-μ)", close(float(mp.nsum(lambda n: mp.mpf(n)**(n - 1)*mp.e**(-0.6*n)*0.6**(n - 1)/mp.factorial(n), [1, mp.inf])), 1, 1e-8)
      and close(float(mp.nsum(lambda n: n*mp.mpf(n)**(n - 1)*mp.e**(-0.6*n)*0.6**(n - 1)/mp.factorial(n), [1, mp.inf])), 1/0.4, 1e-6))
Nn_ = 10
check('3g', "Ehrenfest 从全左回访 2^N；从平衡态 ≈ √(πN/2)", close(1/(math.comb(Nn_, 0)/2**Nn_), 2**Nn_) and abs(1/(math.comb(1000, 500)/2**1000) - math.sqrt(math.pi*1000/2)) < 0.1)
check('3g', "两指数最大值期望", close(np.maximum(rng.exponential(1/1.5, 1_000_000), rng.exponential(1/0.5, 1_000_000)).mean(), 1/1.5 + 1/0.5 - 1/2.0, 3e-3))

# ---------- 03h 信息论 ----------
h2 = lambda p: -p*math.log2(p) - (1 - p)*math.log2(1 - p)
check('3h', "BSC 容量 0.5 时 p≈0.11", abs(1 - h2(0.11) - 0.5) < 1e-3)
pz_ = 0.3
Iz = lambda q: h2(q*(1 - pz_)) - q*h2(pz_)   # 输入 1 的概率 q
check('3h', "Z 信道容量公式", close(-optimize.minimize_scalar(lambda q: -Iz(q), bounds=(0.01, 0.99), method='bounded').fun, math.log2(1 + (1 - pz_)*pz_**(pz_/(1 - pz_))), 1e-6))
a2, b2 = 0.2, 0.35
check('3h', "两状态链熵率 (b h(a)+a h(b))/(a+b)", close(-(b2/(a2 + b2))*((1 - a2)*math.log2(1 - a2) + a2*math.log2(a2)) - (a2/(a2 + b2))*((1 - b2)*math.log2(1 - b2) + b2*math.log2(b2)), (b2*h2(a2) + a2*h2(b2))/(a2 + b2)))
P = np.array([0.5, 0.3, 0.2]); Qd = np.array([0.2, 0.3, 0.5])
kl = np.sum(P*np.log(P/Qd)); tv = 0.5*np.abs(P - Qd).sum(); H2 = 0.5*np.sum((np.sqrt(P) - np.sqrt(Qd))**2); chi2 = np.sum((P - Qd)**2/Qd)
check('3h', "Pinsker、Hellinger、χ²、Bretagnolle–Huber", tv <= math.sqrt(kl/2) and H2 <= tv <= math.sqrt(2*H2) and kl <= math.log(1 + chi2) and tv <= math.sqrt(1 - math.exp(-kl)))
r_ = 0.6
check('3h', "二元正态互信息 -½ln(1-ρ²)", close(integrate.dblquad(lambda y, x: stats.multivariate_normal([0, 0], [[1, r_], [r_, 1]]).pdf([x, y])*math.log(stats.multivariate_normal([0, 0], [[1, r_], [r_, 1]]).pdf([x, y])/(stats.norm.pdf(x)*stats.norm.pdf(y))), -7, 7, -7, 7)[0], -0.5*math.log(1 - r_**2), 1e-6))
S1 = np.array([[1, 0.3], [0.3, 2]]); S2 = np.array([[1.5, 0], [0, 1]]); m1 = np.array([0.2, -0.1]); m2 = np.array([0, 0.5])
klmc = np.mean(stats.multivariate_normal(m1, S1).logpdf(xx := rng.multivariate_normal(m1, S1, 1_000_000)) - stats.multivariate_normal(m2, S2).logpdf(xx))
check('3h', "多元正态 KL 公式", abs(klmc - 0.5*(np.trace(np.linalg.solve(S2, S1)) + (m2 - m1) @ np.linalg.solve(S2, m2 - m1) - 2 + math.log(np.linalg.det(S2)/np.linalg.det(S1)))) < 3e-3)
check('3h', "正态 Chernoff 信息 δ²/(8σ²)", close(-optimize.minimize_scalar(lambda l: math.log(integrate.quad(lambda x: stats.norm.pdf(x, 0, 1.3)**l*stats.norm.pdf(x, 1.0, 1.3)**(1 - l), -15, 15)[0]), bounds=(0, 1), method='bounded').fun, 1.0/(8*1.69), 1e-6))
loads = [np.bincount(rng.integers(0, 10000, 10000), minlength=10000).max() for _ in range(30)]
two = []
for _ in range(10):
    b = np.zeros(10000, int)
    for i, j in rng.integers(0, 10000, (10000, 2)): b[i if b[i] <= b[j] else j] += 1
    two.append(b.max())
check('3h', "球入盒：单选最大负载 ~6–8，两选 ~3", 5 <= np.mean(loads) <= 9 and np.mean(two) <= 4)
nJ, DJ, eJ = 50, 2000, 0.5; kJ = math.ceil(4*math.log(nJ)/(eJ**2/2 - eJ**3/3))
Xp = rng.normal(size=(nJ, DJ)); Pm = rng.normal(scale=1/math.sqrt(kJ), size=(DJ, kJ)); Yp = Xp @ Pm
from scipy.spatial.distance import pdist
ratio = pdist(Yp)**2/pdist(Xp)**2
check('3h', "JL：Dasgupta–Gupta 维数下距离保持", ratio.min() > 1 - eJ and ratio.max() < 1 + eJ, f"k={kJ}")

# ---------- 03i 测度论 ----------
check('3i', "两两独立而不相互独立（硬币例）", (lambda om: all(abs(sum(1 for w in om if A(w) and B(w))/4 - 1/4) < 1e-12 for A, B in [(lambda w: w[0], lambda w: w[1]), (lambda w: w[0], lambda w: w[0] == w[1]), (lambda w: w[1], lambda w: w[0] == w[1])]) and sum(1 for w in om if w[0] and w[1] and w[0] == w[1]) == 1)(list(itertools.product([0, 1], repeat=2))))
cant = (2*rng.integers(0, 2, size=(1_000_000, 30))/3.0**np.arange(1, 31)).sum(1)
check('3i', "Cantor 分布均值 1/2、方差 1/8", abs(cant.mean() - 0.5) < 1e-3 and abs(cant.var() - 0.125) < 1e-3)
tt_ = 2*math.pi*3**4
check('3i', "Cantor 特征函数在 2π3^m 不衰减", abs(np.prod([math.cos(tt_/3**k) for k in range(1, 60)])) > 0.1)
lat = np.arcsin(2*rng.random(2_000_000) - 1); lon = rng.random(2_000_000)*2*math.pi
sel = np.abs(np.sin(lon)) < 0.01   # 大圆（经线）附近
check('3i', "Borel 悖论：沿经线纬度密度 ∝ cos φ", stats.kstest(lat[sel], lambda x: (np.sin(x) + 1)/2).statistic < 0.02)
xi = rng.normal(size=1000000)
check('3i', "X 与 X² 不相关而相依", abs(np.corrcoef(xi, xi**2)[0, 1]) < 5e-3 and abs(np.corrcoef(np.abs(xi), xi**2)[0, 1]) > 0.5)

npass = sum(r[2] for r in R); print(f"\n第三轮续写数学(三) 03d–03i: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
