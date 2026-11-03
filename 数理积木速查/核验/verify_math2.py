"""续写部分（01b--01d、02b、03b--03c）的符号/数值核验。数值核验只覆盖所测参数。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, stats, optimize

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(2)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))
x, y, t, s = sp.symbols('x y t s', real=True)

# ---------- 01b 实分析 ----------
n = 2000; a = lambda m: math.exp(math.lgamma(2*m + 1) - 2*math.lgamma(m + 1) - 2*m*math.log(2))
check('1b', "Gauss 判别: n(a_n/a_{n+1}-1)→1/2", abs(n*(a(n)/a(n + 1) - 1) - 0.5) < 1e-3)
m = 100; H = sum(1/k for k in range(1, m + 1))
check('1b', "H_n 渐近展开", abs(H - (math.log(m) + 0.5772156649015329 + 1/(2*m) - 1/(12*m*m))) < 1e-9)
m = 10; st = m*math.log(m) - m + 0.5*math.log(2*math.pi*m) + 1/(12*m) - 1/(360*m**3)
check('1b', "ln n! Stirling 级数 (n=10)", abs(st - math.lgamma(11)) < 1e-8)
check('1b', "C(2n,n) ~ 4^n/sqrt(pi n)", abs(math.exp(math.lgamma(20001) - 2*math.lgamma(10001) - 10000*math.log(4))*math.sqrt(math.pi*10000) - 1) < 2e-5)
nn, ss = 5, 1.5
I = integrate.quad(lambda u: (1 - u/nn)**nn*u**(ss - 1), 0, nn)[0]
check('1b', "Gauss 乘积公式的有限 n 恒等式", close(I, math.factorial(nn)*nn**ss/np.prod([ss + j for j in range(nn + 1)]), 1e-8))
f = x*(1 - x)
check('1b', "Wirtinger: x(1-x) 满足 ∫f'^2 ≥ π²∫f²", float(sp.integrate(sp.diff(f, x)**2, (x, 0, 1))) >= float(sp.pi**2*sp.integrate(f**2, (x, 0, 1))))
xs = np.linspace(-20, 20, 400001); fv = np.sin(xs) + 0.3*np.sin(3*xs) + 0.2*np.cos(1.7*xs)
M0, M1, M2 = (np.max(np.abs(v)) for v in (fv, np.cos(xs) + 0.9*np.cos(3*xs) - 0.34*np.sin(1.7*xs), -np.sin(xs) - 2.7*np.sin(3*xs) - 0.578*np.cos(1.7*xs)))
check('1b', "Landau 不等式 M1² ≤ 2 M0 M2", M1**2 <= 2*M0*M2)
q = math.sin(1.0); xk = [0.0]
for _ in range(30): xk.append(math.cos(xk[-1]))
xstar = optimize.brentq(lambda u: math.cos(u) - u, 0, 1)
ok = all(abs(xk[j] - xstar) <= q**(j - 1)/(1 - q)*abs(xk[2] - xk[1]) + 1e-15 for j in range(2, 30))
check('1b', "压缩映射先验误差界 (cos, 自 x1 起)", ok)
F = x**2 + y**2 - 1
yp = -sp.diff(F, x)/sp.diff(F, y)
ypp = -(sp.diff(F, x, 2)*sp.diff(F, y)**2 - 2*sp.diff(F, x, y)*sp.diff(F, x)*sp.diff(F, y) + sp.diff(F, y, 2)*sp.diff(F, x)**2)/sp.diff(F, y)**3
yex = sp.sqrt(1 - x**2)
check('1b', "隐函数二阶导公式 (单位圆)", sp.simplify((ypp - sp.diff(yex, x, 2)).subs(y, yex)) == 0)
area = integrate.dblquad(lambda yy, xx: 1.0, 1/math.sqrt(2), math.sqrt(2), lambda xx: max(xx, 1/xx), lambda xx: min(2*xx, 2/xx))[0]
check('1b', "换元面积 ln2/2", close(area, math.log(2)/2, 1e-7))
check('1b', "余元公式、∫x^{s-1}/(1+x)、倍元公式", close(math.gamma(0.3)*math.gamma(0.7), math.pi/math.sin(0.3*math.pi))
      and close(integrate.quad(lambda u: u**(-0.7)/(1 + u), 0, np.inf)[0], math.pi/math.sin(0.3*math.pi), 1e-7)
      and close(math.gamma(1.3)*math.gamma(1.8), 2**(1 - 2.6)*math.sqrt(math.pi)*math.gamma(2.6)))
check('1b', "∫ln x/(1-x) = -ζ(2); Bose/Fermi 积分 s=3", close(integrate.quad(lambda u: math.log(u)/(1 - u), 0, 1)[0], -math.pi**2/6, 1e-8)
      and close(integrate.quad(lambda u: u**2/math.expm1(u), 0, 200)[0], 2*float(mp.zeta(3)), 1e-9)
      and close(integrate.quad(lambda u: u**2/(math.exp(u) + 1), 0, 200)[0], 0.75*2*float(mp.zeta(3)), 1e-9))
check('1b', "Gibbs 常数 Si(π)/π - 1/2 ≈ 0.0895", abs(special.sici(math.pi)[0]/math.pi - 0.5 - 0.0895) < 1e-4)

# ---------- 01c 复分析 ----------
z = sp.symbols('z')
check('1c', "Milne-Thomson 例: Re(z^3+z)=u", sp.simplify(sp.re(sp.expand((x + sp.I*y)**3 + x + sp.I*y)) - (x**3 - 3*x*y**2 + x)) == 0)
rts = np.roots([1, 0, 0, 0, 3, 1])
check('1c', "Rouché: z^5+3z+1 单位圆内 1 个, |z|<2 内 5 个", sum(abs(r) < 1 for r in rts) == 1 and sum(abs(r) < 2 for r in rts) == 5)
th = np.linspace(0, 2*np.pi, 200001); zz = 2*np.exp(1j*th)
val = np.trapezoid(zz**9/(zz**10 - 1)*1j*zz, th)
check('1c', "无穷远留数: ∮ z^9/(z^10-1) = 2πi", abs(val - 2j*np.pi) < 1e-8)
check('1c', "扇形: ∫dx/(1+x^5) = (π/5)/sin(π/5); Fresnel", close(integrate.quad(lambda u: 1/(1 + u**5), 0, np.inf)[0], (math.pi/5)/math.sin(math.pi/5), 1e-8)
      and abs(special.fresnel(50)[1]*math.sqrt(math.pi/2) - 0.5*math.sqrt(math.pi/2)) < 0.02)
ok = True
for _ in range(200):
    aa = (rng.random()*0.9)*np.exp(2j*np.pi*rng.random()); zz = (rng.random()*0.95)*np.exp(2j*np.pi*rng.random())
    fz = (zz - aa)/(1 - np.conj(aa)*zz)*zz; h = 1e-6
    fp = ((zz + h - aa)/(1 - np.conj(aa)*(zz + h))*(zz + h) - fz)/h
    ok &= abs(fp)/(1 - abs(fz)**2) <= 1/(1 - abs(zz)**2) + 1e-4
check('1c', "Schwarz-Pick (Blaschke 积, 200 例)", ok)
zz = np.exp(1j*th); w = zz + 1/zz
check('1c', "Joukowski 把单位圆映为 [-2,2]", np.max(np.abs(w.imag)) < 1e-12 and abs(np.max(w.real) - 2) < 1e-9)
ok = all(close(integrate.quad(lambda u: math.cos(k*u - 2.3*math.sin(u)), 0, 2*math.pi)[0]/(2*math.pi), special.jv(k, 2.3), 1e-10) for k in range(5))
check('1c', "Bessel 积分表示", ok)
zv = 0.37; prod = math.pi*zv*np.prod(1 - zv**2/np.arange(1, 200001)**2)
cot = 1/zv + sum(1/(zv - k) + 1/k + 1/(zv + k) - 1/k for k in range(1, 200001))
check('1c', "sin 乘积与 cot 部分分式", abs(prod - math.sin(math.pi*zv)) < 1e-5 and abs(cot - math.pi/math.tan(math.pi*zv)) < 1e-5)
check('1c', "Γ 在 -2 的留数 1/2; ζ(0)=-1/2, ζ(-1)=-1/12", abs(float(mp.limit(lambda u: (u + 2)*mp.gamma(u), -2)) - 0.5) < 1e-10
      and abs(float(mp.zeta(0)) + 0.5) < 1e-15 and abs(float(mp.zeta(-1)) + 1/12) < 1e-15)
sv, tt, aL, wL = sp.symbols('s t a omega', positive=True)
check('1c', "Bromwich: 1/(s+a)^2 → t e^{-at}; ω/(s²+ω²) → sin ωt", sp.simplify(sp.inverse_laplace_transform(1/(sv + aL)**2, sv, tt) - tt*sp.exp(-aL*tt)) == 0
      and sp.simplify(sp.inverse_laplace_transform(wL/(sv**2 + wL**2), sv, tt) - sp.sin(wL*tt)) == 0)
tv = 0.3; lhs = sum(math.exp(-math.pi*k*k*tv) for k in range(-50, 51)); rhs = sum(math.exp(-math.pi*k*k/tv) for k in range(-50, 51))/math.sqrt(tv)
check('1c', "theta 变换 (Poisson 求和)", abs(lhs - rhs) < 1e-12)

# ---------- 01d 代数 ----------
A2 = sp.Matrix(2, 2, sp.symbols('a b c d'))
check('1d', "Cayley-Hamilton 2×2", sp.simplify(A2**2 - A2.trace()*A2 + A2.det()*sp.eye(2)) == sp.zeros(2))
S3 = rng.normal(size=(3, 3)); S3 = S3 + S3.T; lam, V = np.linalg.eigh(S3)
P = [np.prod([(S3 - lam[j]*np.eye(3))/(lam[i] - lam[j]) for j in range(3) if j != i], axis=0) for i in range(3)]
P = [np.linalg.multi_dot([(S3 - lam[j]*np.eye(3))/(lam[i] - lam[j]) for j in range(3) if j != i]) for i in range(3)]
check('1d', "Sylvester 公式 e^A", np.allclose(sum(math.exp(lam[i])*P[i] for i in range(3)), linalg.expm(S3)))
Am = rng.normal(size=(8, 6)); U, sg, Vt = np.linalg.svd(Am); k = 2
Ak = U[:, :k]@np.diag(sg[:k])@Vt[:k]
check('1d', "Eckart-Young: 2-范数/F-范数误差", close(np.linalg.norm(Am - Ak, 2), sg[k]) and close(np.linalg.norm(Am - Ak, 'fro')**2, np.sum(sg[k:]**2)))
ok = True
for _ in range(100):
    G = rng.normal(size=(6, 6)) + np.diag(rng.normal(0, 4, 6)); radii = np.sum(np.abs(G), 1) - np.abs(np.diag(G))
    ok &= all(np.any(np.abs(ev - np.diag(G)) <= radii + 1e-9) for ev in np.linalg.eigvals(G))
check('1d', "Gershgorin (100 例)", ok)
cfirst = rng.normal(size=7); Cm = linalg.circulant(cfirst).T
om = np.exp(2j*np.pi/7); lam_c = [sum(cfirst[j]*om**(j*kk) for j in range(7)) for kk in range(7)]
check('1d', "循环矩阵特征值", all(np.min(np.abs(np.linalg.eigvals(Cm) - l)) < 1e-9 for l in lam_c))
nc = 9; Lc = linalg.circulant([2, -1] + [0]*(nc - 3) + [-1]); trees = round(np.linalg.det(Lc[1:, 1:]))
check('1d', "n 圈图生成树数 = n", trees == nc)
nT, aT, bT, cT = 7, 1.3, 0.8, 0.45
TT = np.diag([aT]*nT) + np.diag([bT]*(nT - 1), 1) + np.diag([cT]*(nT - 1), -1)
check('1d', "三对角 Toeplitz 谱", np.allclose(np.sort(np.linalg.eigvals(TT).real), np.sort([aT + 2*math.sqrt(bT*cT)*math.cos(kk*math.pi/(nT + 1)) for kk in range(1, nT + 1)])))
Ak_, Bk_, Xk_ = rng.normal(size=(3, 3)), rng.normal(size=(4, 4)), rng.normal(size=(3, 4))
check('1d', "vec(AXB) = (B^T⊗A)vec X; Sylvester 方程", np.allclose((Ak_@Xk_@Bk_).flatten('F'), np.kron(Bk_.T, Ak_)@Xk_.flatten('F'))
      and np.allclose(Ak_@linalg.solve_sylvester(Ak_, -Bk_, Xk_) - linalg.solve_sylvester(Ak_, -Bk_, Xk_)@Bk_, Xk_))
Pm = rng.random((5, 5)); rho = max(abs(np.linalg.eigvals(Pm)))
check('1d', "Perron 行和界", Pm.sum(1).min() - 1e-12 <= rho <= Pm.sum(1).max() + 1e-12)
At = lambda tt: np.array([[1 + tt, tt**2], [math.sin(tt), 2 - tt]]); dA = np.array([[1, 2*0.3], [math.cos(0.3), -1]]); hh = 1e-6
check('1d', "Jacobi 行列式导数公式", abs((np.linalg.det(At(0.3 + hh)) - np.linalg.det(At(0.3 - hh)))/(2*hh) - np.linalg.det(At(0.3))*np.trace(np.linalg.solve(At(0.3), dA))) < 1e-7)
faces = range(6)  # 0:+x 1:-x 2:+y 3:-y 4:+z 5:-z
rz = (0, 1, 2, 3, 4, 5); gz = {0: 2, 2: 1, 1: 3, 3: 0, 4: 4, 5: 5}; gx = {0: 0, 1: 1, 2: 4, 4: 3, 3: 5, 5: 2}
grp = {tuple(range(6))}; frontier = [tuple(range(6))]
while frontier:
    g = frontier.pop();
    for h_ in (gz, gx):
        new = tuple(h_[g[i]] for i in range(6))
        if new not in grp: grp.add(new); frontier.append(new)
cnt = {}
for kc in (2, 3):
    seen = set(); orb = 0
    for col in itertools.product(range(kc), repeat=6):
        if col in seen: continue
        orb += 1; seen.update(tuple(col[g[i]] for i in range(6)) for g in grp)
    cnt[kc] = orb
check('1d', "立方体旋转群 24 阶与面着色公式", len(grp) == 24 and all(cnt[kc] == (kc**6 + 3*kc**4 + 12*kc**3 + 8*kc**2)//24 for kc in (2, 3)), f"{cnt}")
check('1d', "3^100 mod 7 = 4", pow(3, 100, 7) == 4)
def nirr(p, nd):
    return sum(sp.mobius(d)*p**(nd//d) for d in sp.divisors(nd))//nd
brute = sum(1 for cs in itertools.product([0, 1], repeat=4) if sp.Poly([1] + list(cs), sp.Symbol('X'), modulus=2).is_irreducible)
check('1d', "F_2 上不可约多项式计数 n=3,4", nirr(2, 3) == 2 and nirr(2, 4) == 3 == brute)
from sympy.matrices.normalforms import smith_normal_form
snf = smith_normal_form(sp.Matrix([[2, 4], [6, 8]]), domain=sp.ZZ)
check('1d', "Smith 标准形 diag(2,4)", sorted(abs(int(v)) for v in [snf[0, 0], snf[1, 1]]) == [2, 4])

# ---------- 02b 微分几何 ----------
u, v, Rt, rt = sp.symbols('u v R r', positive=True)
Pt = sp.Matrix([(Rt + rt*sp.cos(u))*sp.cos(v), (Rt + rt*sp.cos(u))*sp.sin(v), rt*sp.sin(u)])
Pu, Pv = Pt.diff(u), Pt.diff(v); N = Pu.cross(Pv); N = N/sp.sqrt(sp.simplify(N.dot(N)))
E, F_, G = [sp.simplify(e) for e in (Pu.dot(Pu), Pu.dot(Pv), Pv.dot(Pv))]
L_, M_, N_ = [sp.simplify(e) for e in (Pt.diff(u, 2).dot(N), Pt.diff(u, v).dot(N), Pt.diff(v, 2).dot(N))]
Kt = sp.simplify((L_*N_ - M_**2)/(E*G - F_**2))
check('2b', "环面 K = cos u/(r(R+r cos u))", abs(float((Kt - sp.cos(u)/(rt*(Rt + rt*sp.cos(u)))).subs({u: 0.7, Rt: 3, rt: 1}))) < 1e-12)
check('2b', "旋转面 K=-f''/f (球面)", sp.simplify(-sp.diff(sp.sin(u), u, 2)/sp.sin(u) - 1) == 0)
xr = optimize.brentq(lambda q: q*math.tanh(q) - 1, 0.5, 2)
check('2b', "悬链面临界 d/R = 1.3255", abs(2*xr/math.cosh(xr) - 1.3255) < 1e-4)
nh = np.array([1, 2, 2])/3; K = np.array([[0, -nh[2], nh[1]], [nh[2], 0, -nh[0]], [-nh[1], nh[0], 0]]); thr = 0.9
check('2b', "Rodrigues 公式", np.allclose(np.eye(3) + math.sin(thr)*K + (1 - math.cos(thr))*K@K, linalg.expm(thr*K)))
r_, th_, ph_ = sp.symbols('r theta phi', positive=True); fS = sp.Function('f')(r_, th_, ph_)
g = sp.diag(1, r_**2, r_**2*sp.sin(th_)**2); sq = r_**2*sp.sin(th_); X = [r_, th_, ph_]
LB = sum(sp.diff(sq*g.inv()[i, i]*sp.diff(fS, X[i]), X[i]) for i in range(3))/sq
std = sp.diff(r_**2*sp.diff(fS, r_), r_)/r_**2 + sp.diff(sp.sin(th_)*sp.diff(fS, th_), th_)/(r_**2*sp.sin(th_)) + sp.diff(fS, ph_, 2)/(r_**2*sp.sin(th_)**2)
check('2b', "Laplace-Beltrami 球坐标", sp.simplify(LB - std) == 0)
X1 = sp.Matrix([1, 0, 0]); Y1 = sp.Matrix([0, 1, x]); xyz = [x, y, sp.Symbol('zz')]
br = sp.Matrix([sum(X1[j]*sp.diff(Y1[i], xyz[j]) - Y1[j]*sp.diff(X1[i], xyz[j]) for j in range(3)) for i in range(3)])
check('2b', "Lie 括号 [∂x, ∂y + x∂z] = ∂z", br == sp.Matrix([0, 0, 1]))

# ---------- 03b 极限定理与随机过程 ----------
pB, aB = 0.3, 0.5
Ileg = -optimize.minimize_scalar(lambda tt: -(tt*aB - math.log(1 - pB + pB*math.exp(tt))), bounds=(-20, 20), method='bounded').fun
check('3b', "Cramér 速率 = KL (Bernoulli)", close(Ileg, aB*math.log(aB/pB) + (1 - aB)*math.log((1 - aB)/(1 - pB)), 1e-6))
pex = np.prod([(365 - j)/365 for j in range(23)])
check('3b', "生日问题 n=23: 精确 0.493, 近似 0.500", abs(pex - 0.4927) < 1e-3 and abs(math.exp(-23*22/730) - 0.5) < 0.01)
aH, tH = 1.3, 2.0
dens = integrate.quad(lambda tt: aH/math.sqrt(2*math.pi*tt**3)*math.exp(-aH**2/(2*tt)), 0, tH)[0]
check('3b', "首中时密度 ↔ 2P(B_t ≥ a)", close(dens, 2*(1 - stats.norm.cdf(aH/math.sqrt(tH))), 1e-8))
muS, sgS, T_ = 0.1, 0.4, 2.0; ST = np.exp((muS - sgS**2/2)*T_ + sgS*math.sqrt(T_)*rng.normal(size=2_000_000))
check('3b', "GBM: E S_t = S0 e^{μt}", abs(ST.mean()/math.exp(muS*T_) - 1) < 3e-3)
xx, aa_, bb_, mu_, sg_ = sp.symbols('x a b mu sigma', positive=True)
Pd = (1 - sp.exp(-2*mu_*(xx - aa_)/sg_**2))/(1 - sp.exp(-2*mu_*(bb_ - aa_)/sg_**2))
check('3b', "带漂移离开概率满足 Lu=0 及边值", sp.simplify(mu_*sp.diff(Pd, xx) + sg_**2/2*sp.diff(Pd, xx, 2)) == 0 and sp.simplify(Pd.subs(xx, aa_)) == 0 and sp.simplify(Pd.subs(xx, bb_) - 1) == 0)
Et = (xx - aa_)*(bb_ - xx)/sg_**2
check('3b', "μ=0 期望离开时间满足 σ²/2 u''=-1", sp.simplify(sg_**2/2*sp.diff(Et, xx, 2) + 1) == 0)
rh = sp.symbols('rho', positive=True); kq = sp.symbols('k', integer=True, nonnegative=True)
check('3b', "M/M/1: L = ρ/(1-ρ)", sp.simplify(sp.summation(kq*(1 - rh)*rh**kq, (kq, 0, sp.oo)).subs(rh, sp.Rational(1, 3)) - sp.Rational(1, 2)) == 0)
def wait(pattern):
    m = len(pattern); Q = np.zeros((m, m));
    for st_ in range(m):
        for c in 'HT':
            s2 = pattern[:st_] + c; k2 = max(k for k in range(m + 1) if s2.endswith(pattern[:k]) or k == 0)
            if k2 < m: Q[st_, k2] += 0.5
    return np.linalg.solve(np.eye(m) - Q, np.ones(m))[0]
check('3b', "等待图案 HH=6, HT=4, HTH=10", all(abs(wait(p) - e) < 1e-9 for p, e in [('HH', 6), ('HT', 4), ('HTH', 10)]))
check('3b', "巨分支 c=2: ζ ≈ 0.797", abs(optimize.brentq(lambda zz: 1 - zz - math.exp(-2*zz), 0.1, 1) - 0.7968) < 1e-3)

# ---------- 03c 分布技巧 ----------
Xg, Yg = rng.gamma(2.5, size=400000), rng.gamma(1.5, size=400000); Bt = Xg/(Xg + Yg)
check('3c', "Gamma 比值为 Beta 且与和独立", abs(Bt.mean() - 2.5/4) < 2e-3 and abs(np.corrcoef(Bt, Xg + Yg)[0, 1]) < 5e-3)
U1, U2 = rng.random(400000), rng.random(400000); Z1 = np.sqrt(-2*np.log(U1))*np.cos(2*np.pi*U2); Z2 = np.sqrt(-2*np.log(U1))*np.sin(2*np.pi*U2)
check('3c', "Box-Muller 产生独立标准正态", abs(Z1.std() - 1) < 5e-3 and abs(np.corrcoef(Z1, Z2)[0, 1]) < 5e-3 and abs(stats.kurtosis(Z1)) < 0.03)
fr = []
for _ in range(4000):
    r_, b_ = 2, 3
    for _ in range(300):
        if rng.random() < r_/(r_ + b_): r_ += 1
        else: b_ += 1
    fr.append(r_/(r_ + b_))
check('3c', "Pólya 罐子 → Beta(2,3)", abs(np.mean(fr) - 0.4) < 0.01 and abs(np.var(fr) - 0.04) < 0.005)
tq, lq = sp.symbols('t lambda', positive=True)
Kp = lq*(sp.exp(tq) - 1)
check('3c', "Poisson 全部累积量为 λ", all(sp.simplify(sp.diff(Kp, tq, j).subs(tq, 0) - lq) == 0 for j in range(1, 6)))
th_, dd = rng.random(2_000_000)*np.pi/2, rng.random(2_000_000)*0.5
check('3c', "Buffon (ℓ=d=1): 2/π", abs(np.mean(dd <= 0.5*np.sin(th_)) - 2/np.pi) < 2e-3)
c1, c2 = np.sort(rng.random((1_000_000, 2)), 1).T; pieces = np.stack([c1, c2 - c1, 1 - c2])
check('3c', "折棒成三角形 1/4", abs(np.mean(pieces.max(0) < 0.5) - 0.25) < 2e-3)
check('3c', "100 囚犯 ≈ 0.3118", abs(1 - (sum(1/k for k in range(1, 101)) - sum(1/k for k in range(1, 51))) - 0.3118) < 1e-4)
nsec = 100; Ps = [r/nsec*sum(1/(k - 1) for k in range(r + 1, nsec + 1)) for r in range(1, nsec)]
check('3c', "秘书问题 n=100: r*=37, P≈0.371", int(np.argmax(Ps)) + 1 == 37 and abs(max(Ps) - 0.3710) < 1e-3)
nE = 50; mx = rng.exponential(size=(200000, nE)).max(1)
check('3c', "E max Exp = H_n; E max N ≤ √(2 ln n)", abs(mx.mean() - sum(1/k for k in range(1, nE + 1))) < 0.01 and rng.normal(size=(20000, nE)).max(1).mean() <= math.sqrt(2*math.log(nE)))
m1, s1, m2, s2 = 0.3, 1.2, -0.5, 0.8
kl = integrate.quad(lambda u: stats.norm.pdf(u, m1, s1)*math.log(stats.norm.pdf(u, m1, s1)/stats.norm.pdf(u, m2, s2)), -15, 15)[0]
check('3c', "两正态 KL 公式; 正态熵", close(kl, math.log(s2/s1) + (s1**2 + (m1 - m2)**2)/(2*s2**2) - 0.5, 1e-8) and close(stats.norm(0, 1.7).entropy(), 0.5*math.log(2*math.pi*math.e*1.7**2)))
tC = 1.5   # Exp(1): μ=1, σ=1
check('3c', "Cantelli 界成立 (指数分布)", math.exp(-(1 + tC)) <= 1/(1 + tC**2))
check('3c', "Bayes 例: 阳性真患病 ≈ 16.7%", abs(0.99*0.01/(0.99*0.01 + 0.05*0.99) - 1/6) < 1e-12)

npass = sum(r[2] for r in R); print(f"\n续写数学(一): {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
