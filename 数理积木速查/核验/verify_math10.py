"""第四轮续写 03j--03l、04j--04l 的核验。Monte Carlo 只在给定样本量与容差下检验。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, stats, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(10)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))

# ---------- 03j 概率经典问题 ----------
M = 400000
def in_semicircle(n):
    th = np.sort(rng.uniform(0, 2*np.pi, size=(M, n)), axis=1)
    gaps = np.diff(np.concatenate([th, th[:, :1] + 2*np.pi], axis=1), axis=1)
    return np.mean(gaps.max(axis=1) >= np.pi)
check('3j', "半圆问题 n/2^{n-1}（n=3,4,5）", all(abs(in_semicircle(n) - n/2**(n - 1)) < 4e-3 for n in (3, 4, 5)))
check('3j', "锐角三角形概率 1/4", abs(1 - in_semicircle(3) - 0.25) < 4e-3)
def sphere_hemi(n, m=200000):
    v = rng.normal(size=(m, n, 3))
    cnt = 0
    # n=4：四面体含球心 ⇔ 0 在凸包内 ⇔ 存在正系数线性组合为 0
    for i in range(m):
        V = v[i].T
        lam = np.linalg.solve(V[:, :3], -V[:, 3])
        cnt += np.all(lam > 0)
    return 1 - cnt/m
check('3j', "球面 4 点在某半球内 (n²-n+2)/2^n = 7/8", abs(sphere_hemi(4, 60000) - 14/16) < 6e-3)
def stick(n):
    u = np.sort(rng.uniform(size=(M, n - 1)), axis=1)
    seg = np.diff(np.concatenate([np.zeros((M, 1)), u, np.ones((M, 1))], axis=1), axis=1)
    return np.mean(seg.max(axis=1) < 0.5)
check('3j', "折棒成多边形 1-n/2^{n-1}", all(abs(stick(n) - (1 - n/2**(n - 1))) < 4e-3 for n in (3, 4, 6)))
sq = (2 + math.sqrt(2) + 5*math.log(1 + math.sqrt(2)))/15
p1, p2 = rng.uniform(size=(M, 2)), rng.uniform(size=(M, 2))
check('3j', "单位正方形平均距离 ≈0.5214", abs(np.mean(np.linalg.norm(p1 - p2, axis=1)) - sq) < 2e-3 and abs(sq - 0.5214) < 1e-4)
def disk(m):
    r = np.sqrt(rng.uniform(size=m)); t = rng.uniform(0, 2*np.pi, m)
    return np.c_[r*np.cos(t), r*np.sin(t)]
check('3j', "单位圆盘平均距离 128/(45π)", abs(np.mean(np.linalg.norm(disk(M) - disk(M), axis=1)) - 128/(45*math.pi)) < 3e-3)
c1, c2 = rng.uniform(size=(M, 3)), rng.uniform(size=(M, 3))
check('3j', "单位立方体平均距离 ≈0.6617", abs(np.mean(np.linalg.norm(c1 - c2, axis=1)) - 0.6617) < 2e-3)
u1 = rng.normal(size=(M, 3)); u1 /= np.linalg.norm(u1, axis=1)[:, None]; u2 = rng.normal(size=(M, 3)); u2 /= np.linalg.norm(u2, axis=1)[:, None]
check('3j', "单位球面平均弦长 4/3", abs(np.mean(np.linalg.norm(u1 - u2, axis=1)) - 4/3) < 3e-3)
a3 = rng.uniform(size=(M, 3, 2))
area = 0.5*np.abs((a3[:, 1, 0] - a3[:, 0, 0])*(a3[:, 2, 1] - a3[:, 0, 1]) - (a3[:, 2, 0] - a3[:, 0, 0])*(a3[:, 1, 1] - a3[:, 0, 1]))
d1, d2, d3 = disk(M), disk(M), disk(M)
aread = 0.5*np.abs((d2[:, 0] - d1[:, 0])*(d3[:, 1] - d1[:, 1]) - (d3[:, 0] - d1[:, 0])*(d2[:, 1] - d1[:, 1]))
check('3j', "随机三角形平均面积：正方形 11/144，圆盘 35/(48π)", abs(area.mean() - 11/144) < 1e-3 and abs(aread.mean() - 35/(48*math.pi)) < 2e-3)
b_, c_ = sp.symbols('b c', positive=True)
check('3j', "x²+Bx+C 有实根：1/12，13/24", sp.integrate(b_**2/4, (b_, 0, 1)) == sp.Rational(1, 12) and
      sp.Rational(1, 2) + sp.integrate(b_**2/4, (b_, 0, 1))/2 == sp.Rational(13, 24))
A3 = rng.uniform(size=(2*M, 3))
check('3j', "ax²+bx+c（均匀[0,1]）有实根 (5+6ln2)/36", abs(np.mean(A3[:, 1]**2 >= 4*A3[:, 0]*A3[:, 2]) - (5 + 6*math.log(2))/36) < 2e-3)
a_, bb, l_ = 1.0, 1.5, 0.7
cx, cy, th = rng.uniform(0, a_, M), rng.uniform(0, bb, M), rng.uniform(0, np.pi, M)
dx, dy = l_/2*np.abs(np.cos(th)), l_/2*np.abs(np.sin(th))
hit = (cx - dx < 0) | (cx + dx > a_) | (cy - dy < 0) | (cy + dy > bb)
check('3j', "Buffon--Laplace 网格投针", abs(hit.mean() - (2*l_*(a_ + bb) - l_*l_)/(math.pi*a_*bb)) < 3e-3)
from fractions import Fraction as Fr
Vk = [Fr(7, 2)]
for _ in range(3):
    Vk.append(sum(max(Fr(f), Vk[-1]) for f in range(1, 7))/6)
check('3j', "掷骰最优停止 V2=4.25，V3=14/3，V4≈4.94", Vk[1] == Fr(17, 4) and Vk[2] == Fr(14, 3) and abs(float(Vk[3]) - 4.94) < 0.01)
B = 1e9; K = int(math.floor(math.log2(B)))
check('3j', "St. Petersburg：上限 10⁹ 时期望≈31，对数效用等价 4", abs(K + B/2**K - 31) < 0.5 and close(2**sum(k/2**k for k in range(1, 200)), 4.0))
n_ = 7
perms = list(itertools.permutations(range(n_)))
def cyc_of(p, e):
    c = [e]; x = p[e]
    while x != e: c.append(x); x = p[x]
    return c
lens = [len(cyc_of(p, 0)) for p in perms]
check('3j', "随机排列：元素 1 所在圈长均匀，1 与 2 同圈概率 1/2", all(lens.count(L) == math.factorial(n_ - 1) for L in range(1, n_ + 1)) and
      sum(1 in cyc_of(p, 0) for p in perms)*2 == len(perms))
check('3j', "P(最长圈 > n/2) → ln2，E L/n → 0.6243（Golomb--Dickman）", abs(sum(1/k for k in range(5001, 10001)) - math.log(2)) < 1e-4 and
      abs(float(mp.quad(lambda x_: mp.exp(-x_ - mp.e1(x_)), [0, mp.inf])) - 0.62433) < 1e-4)
n_ = 10**4
Ecyc = sum(math.exp(math.lgamma(n_ + 1) - math.lgamma(n_ - k + 1) - k*math.log(n_)) for k in range(1, n_ + 1))
check('3j', "随机映射循环点期望 ~ √(πn/2)", abs(Ecyc/math.sqrt(math.pi*n_/2) - 1) < 0.01)
n_ = 7
peaks = [sum(1 for i in range(1, n_ - 1) if p[i] > p[i - 1] and p[i] > p[i + 1]) for p in perms]
check('3j', "峰的期望数 (n-2)/3", close(np.mean(peaks), (n_ - 2)/3))
def alt(n):
    return sum(1 for p in itertools.permutations(range(n)) if all((p[i] < p[i + 1]) if i % 2 == 0 else (p[i] > p[i + 1]) for i in range(n - 1)))
xx = sp.symbols('x'); ser = sp.series(sp.sec(xx) + sp.tan(xx), xx, 0, 9).removeO()
check('3j', "交替排列数 = sec+tan 的系数（Euler zigzag）", all(alt(n) == ser.coeff(xx, n)*math.factorial(n) for n in range(1, 9)))
pT = [math.exp(math.lgamma(2*n + 1) - 2*math.lgamma(n + 1) - math.log(n + 1) - (2*n + 1)*math.log(2)) for n in range(2000)]
check('3j', "首次领先 P(T=2n+1)=C_n/2^{2n+1}，总和→1，均值发散", abs(sum(pT) - 1) < 0.02 and sum((2*n + 1)*q for n, q in enumerate(pT[:500])) > 20)
p_ = 0.6
walks = np.cumsum(np.where(rng.random((20000, 400)) < p_, 1, -1), axis=1)
first = np.argmax(walks > 0, axis=1) + 1
check('3j', "有偏硬币 E T = 1/(2p-1)", abs(first.mean() - 1/(2*p_ - 1)) < 0.15)
props = []
for seq in itertools.product([0, 1], repeat=4):
    after = [seq[i + 1] for i in range(3) if seq[i] == 1]
    if after: props.append(sum(after)/len(after))
check('3j', "热手偏差：n=4 时“中后命中率”期望 17/42 < 1/2", abs(np.mean(props) - 17/42) < 1e-12)

# ---------- 03k 金融数学 ----------
C, r, n = 100.0, 0.05, 30
check('3k', "年金现值公式", close(sum(C/(1 + r)**k for k in range(1, n + 1)), C*(1 - (1 + r)**-n)/r))
def bs(S, K, T, r, q, s, call=True):
    d1 = (math.log(S/K) + (r - q + s*s/2)*T)/(s*math.sqrt(T)); d2 = d1 - s*math.sqrt(T)
    if call: return S*math.exp(-q*T)*stats.norm.cdf(d1) - K*math.exp(-r*T)*stats.norm.cdf(d2)
    return K*math.exp(-r*T)*stats.norm.cdf(-d2) - S*math.exp(-q*T)*stats.norm.cdf(-d1)
S, K, T, rr, q, sg = 100, 95, 0.75, 0.03, 0.01, 0.25
check('3k', "买卖权平价 C-P=Se^{-qT}-Ke^{-rT}", close(bs(S, K, T, rr, q, sg) - bs(S, K, T, rr, q, sg, False), S*math.exp(-q*T) - K*math.exp(-rr*T)))
def crr(S, K, T, r, s, N):
    dt = T/N; u = math.exp(s*math.sqrt(dt)); d = 1/u; p = (math.exp(r*dt) - d)/(u - d)
    j = np.arange(N + 1); V = np.maximum(S*u**j*d**(N - j) - K, 0)
    for _ in range(N):
        V = math.exp(-r*dt)*(p*V[1:] + (1 - p)*V[:-1])
    return V[0]
check('3k', "CRR 二叉树收敛到 Black--Scholes", abs(crr(S, K, T, rr, sg, 4000) - bs(S, K, T, rr, 0, sg)) < 5e-3)
h = 1e-3
Vf = lambda s_, t_: bs(s_, K, T - t_, rr, 0, sg)
Th = -(Vf(S, h) - Vf(S, -h))/(2*h)*(-1); Th = (Vf(S, h) - Vf(S, -h))/(2*h)
De = (Vf(S + h, 0) - Vf(S - h, 0))/(2*h); Ga = (Vf(S + h, 0) - 2*Vf(S, 0) + Vf(S - h, 0))/h**2
check('3k', "Θ+½σ²S²Γ+rSΔ=rV", abs(Th + 0.5*sg*sg*S*S*Ga + rr*S*De - rr*Vf(S, 0)) < 1e-4)
d1 = (math.log(S/K) + (rr + sg*sg/2)*T)/(sg*math.sqrt(T))
check('3k', "Δ=Φ(d1)，Γ=φ(d1)/(Sσ√T)", abs(De - stats.norm.cdf(d1)) < 1e-6 and abs(Ga - stats.norm.pdf(d1)/(S*sg*math.sqrt(T))) < 1e-5)
pw, bw = 0.55, 1.5
fstar = pw - (1 - pw)/bw
opt = optimize.minimize_scalar(lambda f: -(pw*math.log(1 + bw*f) + (1 - pw)*math.log(1 - f)), bounds=(0, 0.99), method='bounded').x
mu_, r_, s_ = 0.08, 0.02, 0.2
g = lambda f: r_ + f*(mu_ - r_) - f*f*s_*s_/2
fc = (mu_ - r_)/s_**2
check('3k', "Kelly f*=p-(1-p)/b；连续版 2f* 增长归零、半 Kelly 得 75%", abs(opt - fstar) < 1e-5 and close(g(2*fc), r_) and close(g(fc/2) - r_, 0.75*(g(fc) - r_)) and close(g(fc), r_ + (mu_ - r_)**2/(2*s_*s_)))
Sig = np.cov(rng.normal(size=(5, 50))); Sig += 0.1*np.eye(5)
w = np.linalg.solve(Sig, np.ones(5)); w /= w.sum()
check('3k', "最小方差组合 Σ⁻¹1/(1ᵀΣ⁻¹1)", all(w@Sig@w <= v@Sig@v + 1e-12 for v in (lambda W: W/W.sum(1)[:, None])(rng.normal(size=(500, 5)) + 1)))
n_, rho, s2 = 10, 0.3, 2.0
Cm = s2*((1 - rho)*np.eye(n_) + rho*np.ones((n_, n_)))
check('3k', "等权组合方差 σ²/n+(1-1/n)ρσ²", close(np.ones(n_)@Cm@np.ones(n_)/n_**2, s2/n_ + (1 - 1/n_)*rho*s2))
z99 = stats.norm.ppf(0.99)
check('3k', "99% VaR=2.33σ，ES=2.67σ", abs(z99 - 2.33) < 0.005 and abs(stats.norm.pdf(z99)/0.01 - 2.67) < 0.005)
check('3k', "±50% 交替的几何收益 -13.4%", abs(math.sqrt(1.5*0.5) - 1 + 0.134) < 1e-3)
cf = [(t_, 5.0) for t_ in range(1, 10)] + [(10, 105.0)]
Pf = lambda y: sum(c*math.exp(-y*t_) for t_, c in cf)
y0 = 0.04; Dmac = sum(t_*c*math.exp(-y0*t_) for t_, c in cf)/Pf(y0)
check('3k', "连续复利下 Macaulay 久期 = -dlnP/dy", close(-(math.log(Pf(y0 + 1e-6)) - math.log(Pf(y0 - 1e-6)))/2e-6, Dmac, 1e-6))
Nn = 8
check('3k', "倍投策略期望为 0", close((1 - 2**-Nn)*1 - 2**-Nn*(2**Nn - 1), 0))
tau, a = sp.symbols('tau a', positive=True)
Bf = (1 - sp.exp(-a*tau))/a
check('3k', "Vasicek B(τ)=(1-e^{-aτ})/a 满足 B'=1-aB，B(0)=0", sp.simplify(sp.diff(Bf, tau) - (1 - a*Bf)) == 0 and Bf.subs(tau, 0) == 0)
om, al, be = 0.05, 0.08, 0.9
z = rng.normal(size=400000); s2t = om/(1 - al - be); rs = np.empty_like(z)
for i in range(len(z)):
    rs[i] = math.sqrt(s2t)*z[i]; s2t = om + al*rs[i]**2 + be*s2t
check('3k', "GARCH(1,1) 无条件方差 ω/(1-α-β)", abs(np.var(rs[1000:]) - om/(1 - al - be)) < 0.06*om/(1 - al - be))

# ---------- 03l 随机矩阵与高维概率 ----------
def goe(n):
    X = rng.normal(size=(n, n)); return (X + X.T)/math.sqrt(2*n)
mom = np.zeros(4)
for _ in range(10):
    ev = np.linalg.eigvalsh(goe(400)); mom += [np.mean(ev**(2*k)) for k in range(1, 5)]
mom /= 10
check('3l', "半圆律矩 → Catalan 1,2,5,14", np.allclose(mom, [1, 2, 5, 14], rtol=0.03), str(np.round(mom, 3)))
pg = lambda s: math.pi*s/2*math.exp(-math.pi*s*s/4); pu = lambda s: 32*s*s/math.pi**2*math.exp(-4*s*s/math.pi)
check('3l', "Wigner 猜测式归一且平均间距 1", all(close(integrate.quad(f, 0, np.inf)[0], 1, 1e-10) and close(integrate.quad(lambda s: s*f(s), 0, np.inf)[0], 1, 1e-10) for f in (pg, pu)))
X = rng.normal(size=(400000, 3)); sp2 = np.sqrt((X[:, 0] - X[:, 1])**2 + 2*X[:, 2]**2); sp2 /= sp2.mean()
check('3l', "2×2 GOE 间距 E s² = 4/π（与猜测式一致）", abs(np.mean(sp2**2) - 4/math.pi) < 5e-3)
def gue(n):
    X = rng.normal(size=(n, n)) + 1j*rng.normal(size=(n, n)); return (X + X.conj().T)/math.sqrt(4*n)
tw = [(np.linalg.eigvalsh(gue(200))[-1] - 2)*200**(2/3) for _ in range(300)]
check('3l', "GUE 最大特征值 2+n^{-2/3}TW₂，E TW₂≈-1.77", abs(np.mean(tw) + 1.77) < 0.2, f"{np.mean(tw):.3f}")
n = 1500; W = goe(n); v = rng.normal(size=n); v /= np.linalg.norm(v)
ev, U = np.linalg.eigh(W + 2.0*np.outer(v, v))
check('3l', "BBP（Wigner，θ=2）：λmax→2.5，重叠²→3/4", abs(ev[-1] - 2.5) < 0.05 and abs((U[:, -1]@v)**2 - 0.75) < 0.05)
ev2 = np.linalg.eigvalsh(W + 0.5*np.outer(v, v))
check('3l', "BBP 阈值以下（θ=0.5）λmax→2", abs(ev2[-1] - 2) < 0.08)
p_, n_, ell = 1000, 2000, 3.0
lams = []
for _ in range(4):
    Xs = rng.normal(size=(n_, p_)); Xs[:, 0] *= math.sqrt(ell)
    lams.append(np.linalg.eigvalsh(Xs.T@Xs/n_)[-1])
lam = np.mean(lams); gam = p_/n_
check('3l', "尖峰协方差 λmax→ℓ(1+γ/(ℓ-1))", abs(lam - ell*(1 + gam/(ell - 1))) < 0.08, f"{lam:.3f}")
G = rng.normal(size=(2000, 500)); sv = np.linalg.svd(G, compute_uv=False)
check('3l', "Gauss 矩阵奇异值 √n±√p", abs(sv[0] - (math.sqrt(2000) + math.sqrt(500))) < 1.0 and abs(sv[-1] - (math.sqrt(2000) - math.sqrt(500))) < 1.0)
n = 800; Gi = rng.normal(size=(n, n))/math.sqrt(n); ev = np.linalg.eigvals(Gi)
check('3l', "圆律：|z|<1/2 的比例≈1/4，实特征值≈√(2n/π)", abs(np.mean(np.abs(ev) < 0.5) - 0.25) < 0.02 and abs(np.sum(np.abs(ev.imag) < 1e-9) - math.sqrt(2*n/math.pi)) < 12)
zc = 0.5 + 0.3j
mnum = integrate.quad(lambda x_: (math.sqrt(4 - x_*x_)/(2*math.pi)/(x_ - zc)).real, -2, 2)[0] + 1j*integrate.quad(lambda x_: (math.sqrt(4 - x_*x_)/(2*math.pi)/(x_ - zc)).imag, -2, 2)[0]
mform = (-zc + np.sqrt(zc*zc - 4 + 0j))/2
if mform.imag < 0: mform = (-zc - np.sqrt(zc*zc - 4 + 0j))/2
check('3l', "半圆 Stieltjes 变换 m²+zm+1=0", abs(mnum - mform) < 1e-8 and abs(mnum**2 + zc*mnum + 1) < 1e-8)
aa = np.ones(20)
tail = lambda t: sum(math.comb(20, k) for k in range(21) if abs(2*k - 20) >= t)/2**20
check('3l', "Rademacher 和的 Hoeffding 界", all(tail(t) <= 2*math.exp(-t*t/(2*20)) for t in range(0, 21, 2)))
Emax = lambda n: integrate.quad(lambda x_: x_*n*stats.norm.pdf(x_)*stats.norm.cdf(x_)**(n - 1), -10, 10)[0]
check('3l', "E max g_i ≤ √(2 ln n)", all(Emax(n) <= math.sqrt(2*math.log(n)) for n in (2, 10, 100, 1000, 10**5)))
L = rng.normal(size=(4, 4)); Sg = L@L.T; Am = rng.normal(size=(4, 4)); Am = Am + Am.T
xs = rng.multivariate_normal(np.zeros(4), Sg, size=1000000)
qf = np.einsum('ij,jk,ik->i', xs, Am, xs)
check('3l', "Gauss 二次型：E=tr(AΣ)，Var=2tr(AΣAΣ)", abs(qf.mean() - np.trace(Am@Sg)) < 0.02*np.sqrt(qf.var()) + 0.01 and abs(qf.var()/(2*np.trace(Am@Sg@Am@Sg)) - 1) < 0.02)
nr = np.sum(xs**2, 1)
check('3l', "E‖x‖⁴=(trΣ)²+2trΣ²", abs(np.mean(nr**2)/((np.trace(Sg))**2 + 2*np.trace(Sg@Sg)) - 1) < 0.02)
vec = np.array([1.0, 0.0]); acc = 0.0; Nm = 400000
for M_ in rng.normal(size=(Nm, 2, 2)):
    vec = M_@vec; nv = np.linalg.norm(vec); acc += math.log(nv); vec /= nv
check('3l', "2×2 Gauss 矩阵乘积 Lyapunov 指数 ½(ln2-γ)≈0.058", abs(acc/Nm - 0.5*(math.log(2) - float(mp.euler))) < 0.004, f"{acc/Nm:.4f}")
check('3l', "Newman 公式 d=1 给 E ln|g|", close(0.5*(math.log(2) + float(mp.digamma(0.5))), -(float(mp.euler) + math.log(2))/2))
def kac(n):
    with mp.workdps(60):
        f = lambda t: mp.sqrt(max(mp.mpf(0), 1/(1 - t*t)**2 - (n + 1)**2*t**(2*n)/(1 - t**(2*n + 2))**2))
        return 4/mp.pi*mp.quad(f, [0, 0.5, 0.9, 0.99, 0.999, 1])
check('3l', "Kac：E N = (2/π)ln n + 0.6257 + o(1)", all(abs(float(kac(n)) - (2/math.pi*math.log(n) + 0.6257)) < 0.02 for n in (200, 1000)))
nk = 16
cnt = 0; T_ = 20000
for _ in range(T_):
    co = rng.normal(size=nk + 1)*np.sqrt([math.comb(nk, k) for k in range(nk + 1)])
    rt = np.roots(co[::-1]); cnt += np.sum(np.abs(rt.imag) < 1e-7)
check('3l', "Kostlan 系综 E N = √n", abs(cnt/T_ - 4) < 0.06)
check('3l', "Sauer--Shelah 对区间类取等：1+n+C(n,2)", all(len({tuple(range(i, j)) for i in range(n + 1) for j in range(i, n + 1)}) == 1 + n + math.comb(n, 2) for n in range(1, 12)))
g1, g2 = rng.normal(size=(2, 2000000))
fv = np.sin(g1) + g1*g2; grad2 = (np.cos(g1) + g2)**2 + g1**2
check('3l', "Gauss Poincaré：Var f ≤ E|∇f|²", fv.var() <= grad2.mean())
Xu = rng.uniform(size=(400000, 5)); Xu2 = rng.uniform(size=(400000, 5))
fm = Xu.max(1); es = 0
for i in range(5):
    Y = Xu.copy(); Y[:, i] = Xu2[:, i]; es += np.mean((fm - Y.max(1))**2)
check('3l', "Efron--Stein（max of 5 uniforms）", fm.var() <= 0.5*es and abs(fm.var() - 5/(36*7)) < 2e-3)

# ---------- 04j 机器学习数学 ----------
z = rng.normal(size=6); y = np.eye(6)[2]
sm = lambda z: np.exp(z - z.max())/np.exp(z - z.max()).sum()
Lf = lambda z: -np.sum(y*np.log(sm(z)))
gnum = np.array([(Lf(z + 1e-6*e) - Lf(z - 1e-6*e))/2e-6 for e in np.eye(6)])
check('4j', "softmax 交叉熵梯度 p-y", np.allclose(gnum, sm(z) - y, atol=1e-8))
Wm = rng.normal(size=(3, 4)); xv = rng.normal(size=4); bv = rng.normal(size=3); cv = rng.normal(size=3)
Lw = lambda W_, x_, b_: cv@np.tanh(W_@x_ + b_)
delta = cv*(1 - np.tanh(Wm@xv + bv)**2)
gW = np.array([[(Lw(Wm + 1e-6*np.outer(np.eye(3)[i], np.eye(4)[j]), xv, bv) - Lw(Wm - 1e-6*np.outer(np.eye(3)[i], np.eye(4)[j]), xv, bv))/2e-6 for j in range(4)] for i in range(3)])
gx = np.array([(Lw(Wm, xv + 1e-6*e, bv) - Lw(Wm, xv - 1e-6*e, bv))/2e-6 for e in np.eye(4)])
check('4j', "反向传播 ∂L/∂W=δxᵀ，∂L/∂x=Wᵀδ", np.allclose(gW, np.outer(delta, xv), atol=1e-7) and np.allclose(gx, Wm.T@delta, atol=1e-7))
H = np.diag([10.0, 1.0])
def gd(eta, n=2000):
    th = np.array([1.0, 1.0])
    for _ in range(n): th = th - eta*H@th
    return np.linalg.norm(th)
check('4j', "GD 收敛 ⇔ η<2/λmax", gd(0.199) < 1 and gd(0.201) > 1e3)
kap = 10.0
check('4j', "最优固定步长速率 (κ-1)/(κ+1)", close(max(abs(1 - 2/(10 + 1)*l) for l in (10, 1)), (kap - 1)/(kap + 1)))
sp_, sn_ = rng.normal(1, 1, 300), rng.normal(0, 1, 400)
auc = np.mean(sp_[:, None] > sn_[None, :])
check('4j', "AUC = Mann--Whitney U/(n₊n₋)", close(auc, stats.mannwhitneyu(sp_, sn_).statistic/(300*400)))
Bt, rh, s2 = 25, 0.3, 4.0
Cm = s2*((1 - rh)*np.eye(Bt) + rh*np.ones((Bt, Bt)))
check('4j', "B 棵相关树平均的方差 ρσ²+(1-ρ)σ²/B", close(np.ones(Bt)@Cm@np.ones(Bt)/Bt**2, rh*s2 + (1 - rh)*s2/Bt))
check('4j', "AdaBoost 2√(ε(1-ε)) ≤ exp(-2γ²)", all(2*math.sqrt(e*(1 - e)) <= math.exp(-2*(0.5 - e)**2) for e in np.linspace(0.01, 0.49, 49)))
Xd = rng.normal(size=(200, 6))@rng.normal(size=(6, 6)); Xd -= Xd.mean(0)
Ud, sd, Vd = np.linalg.svd(Xd, full_matrices=False)
W1 = rng.normal(size=(2, 6))*0.1; W2 = rng.normal(size=(6, 2))*0.1
for _ in range(20000):
    E_ = Xd.T - W2@W1@Xd.T
    W2 += 1e-4*E_@(W1@Xd.T).T; W1 += 1e-4*W2.T@E_@Xd
check('4j', "线性自编码器最优误差 = PCA 尾部奇异值平方和", abs(np.linalg.norm(Xd.T - W2@W1@Xd.T)**2/np.sum(sd[2:]**2) - 1) < 1e-3)
check('4j', "Xavier/He：Var(Σwx)=n Var w Var x", abs(np.var((rng.normal(0, math.sqrt(2/256), size=(20000, 256))*rng.normal(size=(20000, 256))).sum(1)) - 2) < 0.06)

# ---------- 04k 实验设计 ----------
check('4k', "16 法则：2(1.96+0.84)²≈16，5% 基线检测 0.5% 约 3 万", abs(2*(1.96 + 0.84)**2 - 15.68) < 1e-9 and abs(16*0.05*0.95/0.005**2 - 30400) < 1)
Np = 16
X = np.array(list(itertools.product([-1, 1], repeat=4)))
check('4k', "2^k 设计每个效应方差 4σ²/N", close(np.sum((X[:, 0]/(Np/2))**2), 4/Np))
wq = sp.symbols('w', positive=True)
pts = [(-1, wq), (0, 1 - 2*wq), (1, wq)]
Mq = sp.zeros(3, 3)
for xx_, ww in pts:
    f_ = sp.Matrix([1, xx_, xx_**2]); Mq += ww*f_*f_.T
check('4k', "二次模型 D 最优：{-1,0,1} 各 1/3", sp.solve(sp.diff(sp.log(Mq.det()), wq), wq) == [sp.Rational(1, 3)])
check('4k', "两点设计 Var b̂ = σ²/N", close(1/np.sum((np.r_[-np.ones(10), np.ones(10)])**2), 1/20))
check('4k', "中心复合设计可旋转 α=(2^k)^{1/4}", close((2**2)**0.25, math.sqrt(2)))
Z = np.cumsum(rng.normal(size=(200000, 5)), axis=1)/np.sqrt(np.arange(1, 6))
check('4k', "5 次中期偷看的一类错误≈14%", abs(np.mean(np.any(np.abs(Z) > 1.96, axis=1)) - 0.142) < 0.004)
check('4k', "Pocock 界 2.41、O'Brien--Fleming 首界 4.56", abs(np.mean(np.any(np.abs(Z) > 2.413, axis=1)) - 0.05) < 0.003 and
      abs(np.mean(np.any(np.abs(Z) > 2.04*np.sqrt(5/np.arange(1, 6)), axis=1)) - 0.05) < 0.003 and abs(2.04*math.sqrt(5) - 4.56) < 0.01)
d_ = 1.96 - stats.norm.ppf(0.8)
cond = d_ + stats.norm.pdf(1.96 - d_)/(1 - stats.norm.cdf(1.96 - d_))
check('4k', "检验力 20% 时显著结果的效应被夸大 >2 倍", cond/d_ > 2, f"{cond/d_:.2f}")
check('4k', "Cohen：d=0.5 每组≈64，d=0.2 每组≈400", round(16/0.25) == 64 and round(16/0.04) == 400)
nI = 400000; xc = rng.normal(size=nI); e = 1/(1 + np.exp(-xc)); Tt = rng.random(nI) < e
Y = 2.0*Tt + xc + rng.normal(size=nI)
ipw = np.mean(Tt*Y/e - (1 - Tt)*Y/(1 - e))
check('4k', "IPW 估计无偏（真效应 2）", abs(ipw - 2) < 0.03)
check('4k', "设计效应 1+(m-1)ρ：m=50,ρ=0.05 得 3.45", close(1 + 49*0.05, 3.45))
check('4k', "Spearman--Brown：ρ=0.5,k=4 → 0.8", close(4*0.5/(1 + 3*0.5), 0.8))
Nh = np.array([100, 300, 600]); sh = np.array([10, 4, 1]); nn = 60
var_ = lambda nh: np.sum(Nh**2*sh**2/nh)
ney = nn*Nh*sh/np.sum(Nh*sh)
check('4k', "Neyman 分配 n_h∝N_hσ_h 方差最小", all(var_(ney) <= var_(nn*w_/w_.sum()) + 1e-9 for w_ in rng.uniform(0.05, 1, size=(2000, 3))))
check('4k', "配对设计 Var= 2σ²(1-ρ)/n", close(np.var(rng.multivariate_normal([0, 0], [[1, 0.8], [0.8, 1]], 400000)@[1, -1]), 2*(1 - 0.8), 0.02))

# ---------- 04l 时间序列 ----------
def acf_ar(phi, K):
    # 由 Yule--Walker 解出 ρ
    p = len(phi); A = np.zeros((p, p)); b = np.zeros(p)
    for k in range(1, p + 1):
        for i in range(1, p + 1):
            j = abs(k - i)
            if j == 0: b[k - 1] -= phi[i - 1]
            else: A[k - 1, j - 1] += phi[i - 1]
        A[k - 1, k - 1] -= 1
    rho = list(np.linalg.solve(A, b))
    rho = [1.0] + rho
    for k in range(p + 1, K + 1): rho.append(sum(phi[i]*rho[k - 1 - i] for i in range(p)))
    return np.array(rho)
f1, f2 = 0.5, 0.3
rho = acf_ar([f1, f2], 5)
check('4l', "AR(2)：ρ1=φ1/(1-φ2)，ρ2=φ2+φ1²/(1-φ2)", close(rho[1], f1/(1 - f2)) and close(rho[2], f2 + f1*f1/(1 - f2)))
def sim_ar(phi, n, burn=500):
    p = len(phi); x = np.zeros(n + burn); e = rng.normal(size=n + burn)
    for t in range(p, n + burn): x[t] = sum(phi[i]*x[t - 1 - i] for i in range(p)) + e[t]
    return x[burn:]
xs = sim_ar([f1, f2], 200000)
sacf = lambda x, k: np.corrcoef(x[:-k], x[k:])[0, 1]
check('4l', "模拟 AR(2) 的样本 ACF 与 Yule--Walker 一致", abs(sacf(xs, 1) - rho[1]) < 0.01 and abs(sacf(xs, 3) - rho[3]) < 0.01)
def levinson(r, p):
    phi = np.zeros((p + 1, p + 1)); v = [1.0]
    for k in range(1, p + 1):
        num = r[k] - sum(phi[k - 1, j]*r[k - j] for j in range(1, k)); den = 1 - sum(phi[k - 1, j]*r[j] for j in range(1, k))
        phi[k, k] = num/den
        for j in range(1, k): phi[k, j] = phi[k - 1, j] - phi[k, k]*phi[k - 1, k - j]
        v.append(v[-1]*(1 - phi[k, k]**2))
    return phi, v
rr3 = acf_ar([0.4, -0.3, 0.2], 6)
phi_, v_ = levinson(rr3, 3)
Tm = linalg.toeplitz(rr3[:3])
check('4l', "Levinson--Durbin = 直接解 Toeplitz 方程；v_k 递减", np.allclose(phi_[3, 1:], np.linalg.solve(Tm, rr3[1:4])) and np.allclose(phi_[3, 1:], [0.4, -0.3, 0.2]) and all(np.diff(v_) <= 1e-15))
ok = True
for f1_ in np.linspace(-2.2, 2.2, 45):
    for f2_ in np.linspace(-1.2, 1.2, 25):
        roots = np.roots([-f2_, -f1_, 1]) if f2_ != 0 else np.roots([-f1_, 1])
        stat = np.all(np.abs(roots) > 1 + 1e-9)
        tri = (f1_ + f2_ < 1) and (f2_ - f1_ < 1) and (abs(f2_) < 1)
        if abs(f1_ + f2_ - 1) > 1e-6 and abs(f2_ - f1_ - 1) > 1e-6 and abs(abs(f2_) - 1) > 1e-6:
            ok &= stat == tri
check('4l', "AR(2) 平稳三角形 ⇔ 根在单位圆外", ok)
f1c, f2c = 1.0, -0.6
rc = acf_ar([f1c, f2c], 30); r_ = math.sqrt(-f2c); th_ = math.acos(f1c/(2*r_))
ratio = rc[1:]/(r_**np.arange(1, 31))
A_ = np.c_[np.cos(th_*np.arange(1, 31)), np.sin(th_*np.arange(1, 31))]
check('4l', "AR(2) 复根：ACF = r^k × 余弦（频率 θ）", np.allclose(A_@np.linalg.lstsq(A_, ratio, rcond=None)[0], ratio))
phi1 = 0.7; h = 5
xs1 = sim_ar([phi1], 400000)
err = xs1[h:] - phi1**h*xs1[:-h]
check('4l', "AR(1) h 步预测误差方差 σ²(1-φ^{2h})/(1-φ²)", abs(err.var() - (1 - phi1**(2*h))/(1 - phi1**2)) < 0.02)
for q_ in (0.1, 1.0, 4.0):
    P = (q_ + math.sqrt(q_*q_ + 4*q_))/2; Kg = P/(P + 1)
    ok = close(q_, Kg*Kg/(1 - Kg))
check('4l', "局部水平模型稳态增益 α：q=α²/(1-α)", ok)
def df_stats(n, reps, const):
    out = []
    for _ in range(reps):
        x = np.cumsum(rng.normal(size=n)); y = np.diff(x); xl = x[:-1]
        Xr = np.c_[xl, np.ones(n - 1)] if const else xl[:, None]
        b, res, *_ = np.linalg.lstsq(Xr, y, rcond=None)
        s2_ = np.sum((y - Xr@b)**2)/(n - 1 - Xr.shape[1]); cov = s2_*np.linalg.inv(Xr.T@Xr)
        out.append(b[0]/math.sqrt(cov[0, 0]))
    return np.quantile(out, 0.05)
check('4l', "Dickey--Fuller 5% 临界值 -1.95（无常数）、-2.86（有常数）", abs(df_stats(500, 6000, False) + 1.95) < 0.06 and abs(df_stats(500, 6000, True) + 2.86) < 0.06)
e = rng.normal(size=500000)
check('4l', "过度差分：白噪声差分后 ρ(1)=-1/2", abs(sacf(np.diff(e), 1) + 0.5) < 0.005)
th_ma = 0.6; nB = 400; reps = 3000; r2s = []
for _ in range(reps):
    ee = rng.normal(size=nB + 1); xm = ee[1:] + th_ma*ee[:-1]; xm -= xm.mean()
    r2s.append(np.sum(xm[:-2]*xm[2:])/np.sum(xm*xm))
rho1 = th_ma/(1 + th_ma**2)
check('4l', "Bartlett：MA(1) 的 Var(ρ̂₂)≈(1+2ρ₁²)/n", abs(np.var(r2s)*nB/(1 + 2*rho1**2) - 1) < 0.08)
phiL = 0.6; means = [sim_ar([phiL], 400, burn=200).mean() for _ in range(4000)]
check('4l', "长期方差 σ²/(1-φ)²", abs(400*np.var(means)/(1/(1 - phiL)**2) - 1) < 0.08)
nP = 1024; ratios = []
for _ in range(400):
    x = sim_ar([0.5], nP); I = np.abs(np.fft.fft(x))**2/(2*math.pi*nP)
    w_ = 2*np.pi*np.arange(1, nP//2)/nP; f_ = 1/(2*math.pi*np.abs(1 - 0.5*np.exp(-1j*w_))**2)
    ratios.append(I[1:nP//2]/f_)
ratios = np.concatenate(ratios)
check('4l', "周期图 I/f ≈ Exp(1)（均值 1，方差 1）", abs(ratios.mean() - 1) < 0.02 and abs(ratios.var() - 1) < 0.06)
phis = [0.5, -0.3]; sig2 = 1.0
fspec = lambda w: sig2/(2*math.pi*abs(1 - phis[0]*np.exp(-1j*w) - phis[1]*np.exp(-2j*w))**2)
check('4l', "Kolmogorov--Szegő 公式（AR(2)）", close(2*math.pi*math.exp(integrate.quad(lambda w: math.log(fspec(w)), -math.pi, math.pi)[0]/(2*math.pi)), sig2, 1e-9)
      and close(integrate.quad(fspec, -math.pi, math.pi)[0], 1/(1 - phis[0]*acf_ar(phis, 2)[1] - phis[1]*acf_ar(phis, 2)[2]), 1e-8))
Av = np.array([[0.5, 0.2], [-0.1, 0.4]]); Sv = np.array([[1.0, 0.3], [0.3, 0.5]])
G0 = linalg.solve_discrete_lyapunov(Av, Sv)
xv = np.zeros(2); acc = np.zeros((2, 2)); ch = np.linalg.cholesky(Sv); Nv = 300000
for t in range(Nv):
    xv = Av@xv + ch@rng.normal(size=2); acc += np.outer(xv, xv)
check('4l', "VAR(1) 平稳协方差 Γ₀=AΓ₀Aᵀ+Σ", np.allclose(acc/Nv, G0, atol=0.03))
d = 0.3
rk = lambda k: math.exp(math.lgamma(k + d) + math.lgamma(1 - d) - math.lgamma(k - d + 1) - math.lgamma(d))
check('4l', "分数差分 ρ(k)~(Γ(1-d)/Γ(d)) k^{2d-1}", abs(rk(10**6)/(math.gamma(1 - d)/math.gamma(d)*(10**6)**(2*d - 1)) - 1) < 1e-4)
def dfa(x, scales):
    y = np.cumsum(x - x.mean()); F = []
    for s in scales:
        m = len(y)//s; seg = y[:m*s].reshape(m, s); tt = np.arange(s)
        res = [np.mean((sg - np.polyval(np.polyfit(tt, sg, 1), tt))**2) for sg in seg]
        F.append(math.sqrt(np.mean(res)))
    return np.polyfit(np.log(scales), np.log(F), 1)[0]
check('4l', "DFA：白噪声 α≈0.5，随机游走 α≈1.5", abs(dfa(rng.normal(size=2**16), [16, 32, 64, 128, 256]) - 0.5) < 0.05 and abs(dfa(np.cumsum(rng.normal(size=2**16)), [16, 32, 64, 128, 256]) - 1.5) < 0.07)
nC = 200; ccs = []
for _ in range(3000):
    a1 = sim_ar([0.8], nC, 200); a2 = sim_ar([0.8], nC, 200)
    ccs.append(np.corrcoef(a1, a2)[0, 1])
check('4l', "独立 AR(1) 互相关方差 Σρxxρyy/n=(1+φ²)/(1-φ²)/n", abs(np.var(ccs)*nC/((1 + 0.64)/(1 - 0.64)) - 1) < 0.1)

npass = sum(r[2] for r in R); print(f"\n第四轮数学（二）: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
