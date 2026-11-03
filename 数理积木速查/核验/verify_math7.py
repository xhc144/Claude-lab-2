"""第三轮续写 04d--04i（数值方法与统计补充）的核验。数值核验只覆盖所测参数。"""
import math, itertools, json
import numpy as np, sympy as sp, mpmath as mp
from scipy import integrate, linalg, special, stats, optimize, fft, sparse
from scipy.sparse.linalg import spsolve

R = []
def check(ch, name, ok, note=""):
    R.append((ch, name, bool(ok), note)); print(f"[{'PASS' if ok else 'FAIL'}] {ch} {name} {note}")
rng = np.random.default_rng(7)
close = lambda a, b, tol=1e-9: abs(a - b) <= tol*max(1, abs(b))

# ---------- 04d 数值线代 ----------
A = np.vander(np.linspace(0, 1, 12), 8, increasing=True)
def cgs(A):
    Q = np.zeros_like(A)
    for j in range(A.shape[1]):
        v = A[:, j] - Q[:, :j] @ (Q[:, :j].T @ A[:, j]); Q[:, j] = v/np.linalg.norm(v)
    return Q
def mgs(A):
    Q = A.copy()
    for j in range(A.shape[1]):
        Q[:, j] /= np.linalg.norm(Q[:, j])
        for k in range(j + 1, A.shape[1]): Q[:, k] -= (Q[:, j] @ Q[:, k])*Q[:, j]
    return Q
lo = lambda Q: np.linalg.norm(np.eye(Q.shape[1]) - Q.T @ Q)
check('4d', "正交性损失: CGS ≫ MGS ≫ Householder", lo(cgs(A)) > 10*lo(mgs(A)) and lo(mgs(A)) > 10*lo(np.linalg.qr(A)[0]), f"{lo(cgs(A)):.1e},{lo(mgs(A)):.1e},{lo(np.linalg.qr(A)[0]):.1e}")
S = rng.normal(size=(8, 8)); S = S + S.T; x = rng.normal(size=8); errs = []
w, V = np.linalg.eigh(S)
for _ in range(4):
    mu = x @ S @ x/(x @ x); x = np.linalg.solve(S - mu*np.eye(8), x); x /= np.linalg.norm(x)
    errs.append(min(np.min(np.linalg.norm(V - x[:, None], axis=0)), np.min(np.linalg.norm(V + x[:, None], axis=0))))
check('4d', "Rayleigh 商迭代三次收敛", errs[2] < 1e-6 and (errs[1] < 1e-2 and errs[2] < 10*errs[1]**3 + 1e-14), str([f"{e:.1e}" for e in errs]))
n = 50; h = 1/(n + 1); T = np.diag(2*np.ones(n)) - np.diag(np.ones(n - 1), 1) - np.diag(np.ones(n - 1), -1)
D = np.diag(np.diag(T)); L = np.tril(T, -1); U = np.triu(T, 1)
rhoJ = max(abs(np.linalg.eigvals(np.linalg.solve(D, -(L + U))))); rhoGS = max(abs(np.linalg.eigvals(np.linalg.solve(D + L, -U))))
om = 2/(1 + math.sin(math.pi*h)); MSOR = np.linalg.solve(D + om*L, (1 - om)*D - om*U)
check('4d', "ρ_J=cos πh, ρ_GS=ρ_J², ρ_SOR=ω*-1", close(rhoJ, math.cos(math.pi*h), 1e-10) and close(rhoGS, rhoJ**2, 1e-8) and abs(max(abs(np.linalg.eigvals(MSOR))) - (om - 1)) < 1e-3)
check('4d', "κ(Laplacian) ≈ 4/(π²h²)", abs(np.linalg.cond(T)/(4/(math.pi**2*h**2)) - 1) < 0.02)
Wk = np.eye(30) - np.tril(np.ones((30, 30)), -1); Wk[:, -1] = 1
P_, L_, U_ = linalg.lu(Wk)
check('4d', "Wilkinson 矩阵增长因子 2^{n-1}", close(np.abs(U_).max(), 2.0**29))
J = np.diag(np.ones(9), 1); Jp = J.copy(); Jp[-1, 0] = 1e-10
check('4d', "Jordan 块扰动 ε^{1/n}", abs(max(abs(np.linalg.eigvals(Jp))) - 1e-1) < 1e-3)
Asym = rng.normal(size=(6, 6)); Asym = Asym + Asym.T; E = rng.normal(size=(6, 6))*1e-3; E = E + E.T
w0, V0 = np.linalg.eigh(Asym); w1, V1 = np.linalg.eigh(Asym + E)
gap = min(abs(w0[2] - w0[1]), abs(w0[2] - w0[3]))
check('4d', "Davis–Kahan sinθ ≤ ||E||/gap", math.sqrt(max(0, 1 - (V0[:, 2] @ V1[:, 2])**2)) <= np.linalg.norm(E, 2)/(gap - np.linalg.norm(E, 2)))
Al = np.vander(np.linspace(0, 1, 40), 10, increasing=True); xt = rng.normal(size=10); b = Al @ xt
xq = np.linalg.lstsq(Al, b, rcond=None)[0]; xn = np.linalg.solve(Al.T @ Al, Al.T @ b)
check('4d', "最小二乘：正规方程损失 κ²", np.linalg.norm(xn - xt) > 100*np.linalg.norm(xq - xt), f"κ={np.linalg.cond(Al):.1e}")
lam = 0.3; Ar = rng.normal(size=(20, 8)); br = rng.normal(size=20); Uu, s, Vt = np.linalg.svd(Ar, full_matrices=False)
check('4d', "Tikhonov 滤波因子形式", np.allclose(np.linalg.solve(Ar.T @ Ar + lam*np.eye(8), Ar.T @ br), Vt.T @ (s**2/(s**2 + lam)*(Uu.T @ br)/s)))
Ae = rng.normal(size=(6, 6))*3
check('4d', "缩放平方法 = expm", np.allclose((lambda s_: np.linalg.matrix_power(linalg.expm(Ae/2**s_), 2**s_))(6), linalg.expm(Ae), rtol=1e-8))
m_, n_, k_, p_ = 300, 200, 10, 8
Ar2 = rng.normal(size=(m_, 40)) @ np.diag(0.7**np.arange(40)) @ rng.normal(size=(40, n_))
sv = np.linalg.svd(Ar2, compute_uv=False); bnd = math.sqrt(1 + k_/(p_ - 1))*math.sqrt(np.sum(sv[k_:]**2))
errs = [np.linalg.norm(Ar2 - (lambda Q: Q @ (Q.T @ Ar2))(np.linalg.qr(Ar2 @ rng.normal(size=(n_, k_ + p_)))[0])) for _ in range(50)]
check('4d', "随机化 SVD 误差界（期望）", np.mean(errs) <= bnd)
c = rng.normal(size=64); bc = rng.normal(size=64); Cm = linalg.circulant(c)
check('4d', "循环系统 FFT 求解", np.allclose(np.real(fft.ifft(fft.fft(bc)/fft.fft(c))), np.linalg.solve(Cm, bc)))
N = 31; hh = 1/(N + 1); f2 = rng.normal(size=(N, N))
j = np.arange(1, N + 1); lamd = 4*np.sin(j*np.pi*hh/2)**2
uh = fft.idstn(fft.dstn(hh**2*f2, type=1)/(lamd[:, None] + lamd[None, :]), type=1)
Tn = sparse.diags([-1, 2, -1], [-1, 0, 1], shape=(N, N)); A2 = sparse.kron(Tn, sparse.eye(N)) + sparse.kron(sparse.eye(N), Tn)
check('4d', "DST 快速 Poisson 求解", np.allclose(uh.ravel(), spsolve(A2.tocsc(), hh**2*f2.ravel())))
Am = rng.normal(size=(50, 50)) + 50*np.eye(50); bm = rng.normal(size=50)
lu32 = linalg.lu_factor(Am.astype(np.float32)); xm = linalg.lu_solve(lu32, bm.astype(np.float32)).astype(np.float64)
for _ in range(5): xm += linalg.lu_solve(lu32, (bm - Am @ xm).astype(np.float32)).astype(np.float64)
check('4d', "混合精度迭代精化达双精度", np.linalg.norm(xm - np.linalg.solve(Am, bm))/np.linalg.norm(xm) < 1e-13)
As, Bs, Cs = rng.normal(size=(5, 5)), rng.normal(size=(4, 4)), rng.normal(size=(5, 4))
check('4d', "Sylvester（Bartels–Stewart）", np.allclose((lambda X: As @ X + X @ Bs)(linalg.solve_sylvester(As, Bs, Cs)), Cs))
ev = np.linalg.eigvalsh(Asym); sig = ev[2] + 0.05
it = [rng.normal(size=6)]
for _ in range(5): v = np.linalg.solve(Asym - sig*np.eye(6), it[-1]); it.append(v/np.linalg.norm(v))
check('4d', "位移逆迭代收敛到最近特征值", abs(it[-1] @ Asym @ it[-1] - ev[2]) < 1e-8)

# ---------- 04e 非线性与优化 ----------
mp.mp.dps = 600; f = lambda x: x**3 - 2*x - 5; root = mp.findroot(f, 2.1); xs = [mp.mpf(2), mp.mpf(3)]
for _ in range(11): xs.append(xs[-1] - f(xs[-1])*(xs[-1] - xs[-2])/(f(xs[-1]) - f(xs[-2])))
e = [abs(v - root) for v in xs]; ords = [float(mp.log(e[k + 1]/e[k])/mp.log(e[k]/e[k - 1])) for k in range(8, 11)]; mp.mp.dps = 15
check('4e', "割线法阶 ≈ 1.618", abs(ords[-1] - 1.618) < 0.15, str([f"{o:.2f}" for o in ords]))
g = lambda x: math.exp(-x)*3.0; x0 = 0.3; st = [x0]
for _ in range(5):
    x1 = g(x0); x2 = g(x1); x0 = x0 - (x1 - x0)**2/(x2 - 2*x1 + x0); st.append(x0)
fp = optimize.brentq(lambda x: g(x) - x, 0, 3)
check('4e', "Steffensen 二次收敛（原迭代 |g'|>1 也行）", abs(st[-1] - fp) < 1e-14 and abs(-g(fp)) > 1)
Hs = np.eye(3); sv_ = rng.normal(size=3); yv = rng.normal(size=3); yv = yv if yv @ sv_ > 0 else -yv; rho = 1/(yv @ sv_)
Hn = (np.eye(3) - rho*np.outer(sv_, yv)) @ Hs @ (np.eye(3) - rho*np.outer(yv, sv_)) + rho*np.outer(sv_, sv_)
check('4e', "BFGS 更新满足割线条件且正定", np.allclose(Hn @ yv, sv_) and np.linalg.eigvalsh(Hn).min() > 0)
Q = np.diag([1.0, 10.0, 100.0]); xg = np.ones(3); L_, mu_ = 100.0, 1.0; gd = []
for k in range(200): xg = xg - Q @ xg/L_; gd.append(np.linalg.norm(xg)**2)
check('4e', "强凸 GD 速率 (1-μ/L)^k", all(gd[k] <= (1 - mu_/L_)**(k + 1)*3 + 1e-15 for k in range(200)))
xa = np.ones(3); ya = xa.copy(); xprev = xa.copy(); acc = []
for k in range(200):
    xn_ = ya - Q @ ya/L_; ya = xn_ + (math.sqrt(L_) - 1)/(math.sqrt(L_) + 1)*(xn_ - xprev); xprev = xn_; acc.append(0.5*xn_ @ Q @ xn_)
check('4e', "Nesterov 加速 ≪ 普通 GD", acc[150] < 1e-6*0.5*np.ones(3) @ Q @ np.ones(3) and gd[150] > 1e-2)
gr = (math.sqrt(5) - 1)/2; a_, b_ = 0.0, 3.0; ff = lambda x: (x - 1.234)**2
c1, d1 = b_ - gr*(b_ - a_), a_ + gr*(b_ - a_)
for _ in range(60):
    if ff(c1) < ff(d1): b_, d1 = d1, c1; c1 = b_ - gr*(b_ - a_)
    else: a_, c1 = c1, d1; d1 = a_ + gr*(b_ - a_)
check('4e', "黄金分割每步缩 0.618", abs((a_ + b_)/2 - 1.234) < 1e-8)
check('4e', "软阈值 = prox_{λ|·|}", all(abs(optimize.minimize_scalar(lambda x: 0.7*abs(x) + 0.5*(x - v)**2).x - np.sign(v)*max(abs(v) - 0.7, 0)) < 1e-6 for v in (-2.0, -0.3, 0.5, 1.9)))
def proj_simplex(v):
    u = np.sort(v)[::-1]; cs = np.cumsum(u); rho_ = max(j for j in range(1, len(v) + 1) if u[j - 1] - (cs[j - 1] - 1)/j > 0)
    th = (cs[rho_ - 1] - 1)/rho_; return np.maximum(v - th, 0)
vv = rng.normal(size=6)
res = optimize.minimize(lambda x: np.sum((x - vv)**2), np.ones(6)/6, constraints={'type': 'eq', 'fun': lambda x: x.sum() - 1}, bounds=[(0, None)]*6, tol=1e-14)
check('4e', "投影到单纯形公式", np.allclose(proj_simplex(vv), res.x, atol=1e-6))
pw = np.poly(np.arange(1, 21)); pw2 = pw.copy(); pw2[1] -= 2**-23
check('4e', "Wilkinson 多项式：x^19 系数扰动 2^-23 产生复根", np.max(np.abs(np.roots(pw2).imag)) > 1)
check('4e', "伴随矩阵特征值 = 根", np.allclose(np.sort_complex(np.linalg.eigvals(np.polynomial.polynomial.polycompanion([2, -3, 0, 1]))), np.sort_complex(np.roots([1, 0, -3, 2]))))
fc = lambda z: np.exp(z)*np.sin(z)/(1 + z*z); xc = 0.7
check('4e', "复步长导数达机器精度", abs(np.imag(fc(xc + 1e-20j))/1e-20 - float(mp.diff(lambda t: mp.exp(t)*mp.sin(t)/(1 + t*t), xc))) < 1e-15)
Xl = rng.normal(size=(100, 5)); yl = Xl @ np.array([2, 0, -1, 0, 0.5]) + rng.normal(size=100)*0.5; lam_ = 0.1; beta = np.zeros(5)
for _ in range(200):
    for j in range(5):
        r = yl - Xl @ beta + Xl[:, j]*beta[j]; z = Xl[:, j] @ r/100
        beta[j] = np.sign(z)*max(abs(z) - lam_, 0)/(Xl[:, j] @ Xl[:, j]/100)
obj = lambda b: np.sum((yl - Xl @ b)**2)/200 + lam_*np.abs(b).sum()
check('4e', "坐标下降解 Lasso（与通用优化比较）", obj(beta) <= optimize.minimize(obj, np.zeros(5), method='Powell', options={'xtol': 1e-10, 'ftol': 1e-12}).fun + 1e-8)
p1 = [1, -6, 11, -6]; zs = np.array([0.4 + 0.9j, 0.4 + 0.9j*1j, (0.4 + 0.9j)**2])
for _ in range(100): zs = zs - np.polyval(p1, zs)/np.array([np.prod([zs[i] - zs[j] for j in range(3) if j != i]) for i in range(3)])
check('4e', "Durand–Kerner", np.allclose(np.sort(zs.real), [1, 2, 3]))

# ---------- 04f 插值与求积 ----------
xn = np.cos(np.pi*np.arange(11)/10); wts = (-1.0)**np.arange(11); wts[[0, -1]] *= 0.5
fr = lambda x: 1/(1 + 25*x**2); xe = 0.3217
bary = np.sum(wts*fr(xn)/(xe - xn))/np.sum(wts/(xe - xn))
check('4f', "重心公式（第二类 Chebyshev 点简化权）", close(bary, np.polyval(np.polyfit(xn, fr(xn), 10), xe), 1e-10))
def leb(nodes):
    xx = np.linspace(-1, 1, 20001); Lk = np.ones((len(nodes), xx.size))
    for i, xi in enumerate(nodes):
        for j, xj in enumerate(nodes):
            if i != j: Lk[i] *= (xx - xj)/(xi - xj)
    return np.abs(Lk).sum(0).max()
nn = 16
check('4f', "Lebesgue 常数：Chebyshev ≤ (2/π)ln(n+1)+1；等距 ~ 2^{n+1}/(e n ln n)", leb(np.cos(np.pi*np.arange(nn + 1)/nn)) <= 2/math.pi*math.log(nn + 1) + 1
      and 0.3 < leb(np.linspace(-1, 1, nn + 1))/(2**(nn + 1)/(math.e*nn*math.log(nn))) < 3)
cheb = np.polynomial.chebyshev.chebinterpolate(fr, 120); rho_ = 0.2 + math.sqrt(1.04)
check('4f', "Runge 函数 Chebyshev 系数 ~ ρ^{-k}, ρ≈1.22", abs(math.log(abs(cheb[100])/abs(cheb[60]))/40 + math.log(rho_)) < 0.01)
check('4f', "Padé [2/2] e^x 误差 O(x^5)", abs(np.exp(0.1) - (1 + 0.05 + 0.01/12)/(1 - 0.05 + 0.01/12)) < 2e-8)
a, b = 0.3, 1.7; F_ = np.sin; Fp = np.cos
xs_ = sp.symbols('x'); cs_ = sp.symbols('c0:4'); Hp = sum(cs_[i]*xs_**i for i in range(4))
sol = sp.solve([Hp.subs(xs_, a) - F_(a), Hp.subs(xs_, b) - F_(b), sp.diff(Hp, xs_).subs(xs_, a) - Fp(a), sp.diff(Hp, xs_).subs(xs_, b) - Fp(b)], cs_)
check('4f', "三次 Hermite 中点公式", close(float(Hp.subs(sol).subs(xs_, (a + b)/2)), (F_(a) + F_(b))/2 + (b - a)/8*(Fp(a) - Fp(b)), 1e-12))
Ntr = 20; Ttr = 2*math.pi/Ntr*sum(math.exp(math.cos(2*math.pi*k/Ntr)) for k in range(Ntr))
check('4f', "周期梯形公式 N=20 达机器精度", abs(Ttr - 2*math.pi*special.i0(1)) < 1e-13)
Qh = lambda hh: sum(hh*(math.exp(-(k*hh)**2) + math.exp(-((k + 1)*hh)**2))/2 for k in range(int(round(1/hh))))
check('4f', "Richardson 外推消去 h² 项", abs((4*Qh(0.05) - Qh(0.1))/3 - math.sqrt(math.pi)/2*special.erf(1)) < 1e-6 and abs(Qh(0.05) - math.sqrt(math.pi)/2*special.erf(1)) > 1e-5)
ng = 4; xgq, wgq = np.polynomial.legendre.leggauss(ng); f8 = lambda x: x**8
errG = 2/9 - np.sum(wgq*f8(xgq))
check('4f', "Gauss 误差常数 (n=4, f=x^8)", close(errG, 2**9*math.factorial(4)**4/(9*math.factorial(8)**3)*math.factorial(8), 1e-10))
J = np.diag(np.arange(1, ng)/np.sqrt(4*np.arange(1, ng)**2 - 1), 1); J = J + J.T; wj, vj = np.linalg.eigh(J)
check('4f', "Golub–Welsch", np.allclose(np.sort(wj), np.sort(xgq)) and np.allclose(2*vj[0, :]**2, wgq[np.argsort(xgq)]))
tt = np.linspace(-4, 4, 161); hs = tt[1] - tt[0]; uu = np.pi/2*np.sinh(tt); ww = np.pi/2*np.cosh(tt)/np.cosh(uu)**2
one_minus_x = 2/(1 + np.exp(2*uu))   # 1-tanh(u)，直接计算避免相消
check('4f', "tanh-sinh 处理端点奇异 ∫_{-1}^1 (1-x)^{-1/2}", abs(hs*np.sum(ww/np.sqrt(one_minus_x)) - 2*math.sqrt(2)) < 1e-6)
from scipy.stats import qmc
fq = lambda X: np.prod(1 + 0.5*(X - 0.5), axis=1)
eq = abs(fq(qmc.Sobol(4, scramble=True, seed=1).random(2**14)).mean() - 1); em = abs(fq(rng.random((2**14, 4))).mean() - 1)
check('4f', "QMC 误差 ≪ MC 误差", eq < em/5 or eq < 1e-5, f"{eq:.1e} vs {em:.1e}")
xs_n = np.linspace(-1, 1, 4001)
def remez_poly_err(n):
    p = np.polynomial.chebyshev.Chebyshev.fit(xs_n, np.abs(xs_n), n); return np.max(np.abs(p(xs_n) - np.abs(xs_n)))
check('4f', "|x| 多项式逼近 ~ 0.28/n 量级", 0.1 < remez_poly_err(40)*40 < 1.0)
tk = np.array([0, 0, 0, 0, 1, 2, 3, 4, 4, 4, 4], float)
from scipy.interpolate import BSpline
basis = [BSpline.basis_element(tk[i:i + 5], extrapolate=False) for i in range(len(tk) - 4)]
xb = np.linspace(0.01, 3.99, 200)
check('4f', "B 样条单位分解", np.allclose(np.nansum([bs(xb) for bs in basis], axis=0), 1))
def chebD(N):
    x = np.cos(np.pi*np.arange(N + 1)/N); c = np.r_[2, np.ones(N - 1), 2]*(-1)**np.arange(N + 1)
    X = np.tile(x, (N + 1, 1)).T; dX = X - X.T; Dm = np.outer(c, 1/c)/(dX + np.eye(N + 1)); return Dm - np.diag(Dm.sum(1)), x
D16, x16 = chebD(16); D32, _ = chebD(32)
check('4f', "Chebyshev 谱微分：指数精度、||D||~N²", np.max(np.abs(D16 @ np.exp(x16) - np.exp(x16))) < 1e-10 and 3 < np.linalg.norm(D32, 2)/np.linalg.norm(D16, 2) < 5)
check('4f', "Peano 核：Simpson 误差 -(b-a)^5/2880 f⁽⁴⁾", close((1/5) - (0 + 4*(0.5)**4 + 1)/6, -24/2880, 1e-12))

# ---------- 04g 微分方程数值 ----------
def rk4(f, y, t, h, n):
    for _ in range(n):
        k1 = f(t, y); k2 = f(t + h/2, y + h/2*k1); k3 = f(t + h/2, y + h/2*k2); k4 = f(t + h, y + h*k3)
        y = y + h/6*(k1 + 2*k2 + 2*k3 + k4); t += h
    return y
fo = lambda t, y: y*np.cos(t); ex = lambda t: np.exp(np.sin(t))
e1, e2 = abs(rk4(fo, 1.0, 0, 0.02, 100) - ex(2.0)), abs(rk4(fo, 1.0, 0, 0.01, 200) - ex(2.0))
check('4g', "RK4 观测阶 ≈ 4", abs(math.log2(e1/e2) - 4) < 0.2)
z = -1e6
check('4g', "L 稳定：BE R(-∞)=0，梯形 R→-1", abs(1/(1 - z)) < 1e-5 and abs((1 + z/2)/(1 - z/2) + 1) < 1e-5)
def bdf_roots(k):
    th = sp.symbols('z')   # BDFk 第一特征多项式 ρ(ζ)=Σ_{j=1}^k (1/j) ζ^{k-j}(ζ-1)^j
    return [complex(r) for r in sp.Poly(sp.expand(sum(sp.Rational(1, j)*th**(k - j)*(th - 1)**j for j in range(1, k + 1))), th).nroots()]
check('4g', "BDF 零稳定 k≤6，k=7 不稳定", all(max(abs(r) for r in bdf_roots(k)) <= 1 + 1e-9 for k in range(1, 7)) and max(abs(r) for r in bdf_roots(7)) > 1)
Tn_, dtn = 1.0, [2**-k for k in range(4, 9)]; muE, sE = 1.0, 0.5; strong = []
for dt in dtn:
    nstp = int(Tn_/dt); dW = rng.normal(scale=math.sqrt(dt), size=(4000, nstp)); X = np.ones(4000)
    for k in range(nstp): X = X + muE*X*dt + sE*X*dW[:, k]
    strong.append(np.mean(np.abs(X - np.exp((muE - sE**2/2)*Tn_ + sE*dW.sum(1)))))
slope = np.polyfit(np.log(dtn), np.log(strong), 1)[0]
check('4g', "Euler–Maruyama 强阶 ≈ 1/2", abs(slope - 0.5) < 0.12, f"{slope:.2f}")
nb = 200; hb = 1/(nb + 1); xb_ = np.linspace(hb, 1 - hb, nb)
ub = np.linalg.solve((np.diag(2*np.ones(nb)) - np.diag(np.ones(nb - 1), 1) - np.diag(np.ones(nb - 1), -1))/hb**2 + np.eye(nb), (math.pi**2 + 1)*np.sin(math.pi*xb_))
check('4g', "有限差分 BVP 二阶精度", np.max(np.abs(ub - np.sin(math.pi*xb_))) < 2e-4)
nu = 0.6; kh = np.linspace(0.01, math.pi, 50)
Gup = 1 - nu + nu*np.exp(-1j*kh); Glw = 1 - 1j*nu*np.sin(kh) - nu**2*(1 - np.cos(kh))
check('4g', "迎风修正方程耗散系数 (ah/2)(1-ν)", abs((1 - np.abs(Gup[0]))/(0.01**2) - nu*(1 - nu)/2) < 1e-3 and np.all(np.abs(Glw) <= 1 + 1e-12))
ww = 2*np.arcsin(0.8*np.sin(kh/2))/0.8
check('4g', "leapfrog 数值色散：相速度 < c", np.all(ww[1:]/kh[1:] < 1) and abs(ww[0]/kh[0] - 1) < 1e-4)
A_ = np.array([[0, 1], [-1, 0]]); B_ = np.array([[-0.3, 0], [0.2, -0.1]]); dt = 0.05
exact = linalg.expm((A_ + B_)*1.0)
lie = np.linalg.matrix_power(linalg.expm(dt*B_) @ linalg.expm(dt*A_), 20); strang = np.linalg.matrix_power(linalg.expm(dt/2*A_) @ linalg.expm(dt*B_) @ linalg.expm(dt/2*A_), 20)
lie2 = np.linalg.matrix_power(linalg.expm(dt/2*B_) @ linalg.expm(dt/2*A_), 40); strang2 = np.linalg.matrix_power(linalg.expm(dt/4*A_) @ linalg.expm(dt/2*B_) @ linalg.expm(dt/4*A_), 40)
check('4g', "Lie 一阶、Strang 二阶", abs(math.log2(np.linalg.norm(lie - exact)/np.linalg.norm(lie2 - exact)) - 1) < 0.1 and abs(math.log2(np.linalg.norm(strang - exact)/np.linalg.norm(strang2 - exact)) - 2) < 0.1)
def neumann_err(nn, ghost=True):
    hN = 1/nn; x = np.linspace(0, 1, nn + 1); A = np.zeros((nn + 1, nn + 1)); rhs = np.cos(x)*1.0 + np.cos(x)  # -u''+u = 2cos x, u=cos x? -(-cos)+cos=2cos
    for i in range(1, nn): A[i, i - 1:i + 2] = [-1/hN**2, 2/hN**2 + 1, -1/hN**2]
    A[nn, nn] = 1; rhs[nn] = math.cos(1)
    if ghost: A[0, 0] = 2/hN**2 + 1; A[0, 1] = -2/hN**2; rhs[0] = 2 + 2*0/hN   # u'(0)=0
    else: A[0, 0] = -1/hN; A[0, 1] = 1/hN; rhs[0] = 0
    return np.max(np.abs(np.linalg.solve(A, rhs) - np.cos(x)))
check('4g', "Neumann 虚点二阶、单侧一阶", abs(math.log2(neumann_err(40)/neumann_err(80)) - 2) < 0.2 and abs(math.log2(neumann_err(40, False)/neumann_err(80, False)) - 1) < 0.2)
def ctrl(err, tol=1e-6, p=4, h=0.1): return h*min(5, max(0.2, 0.9*(tol/err)**(1/(p + 1))))
check('4g', "步长控制公式数值例", close(ctrl(1e-4), 0.1*0.9*(1e-2)**0.2))

# ---------- 04h 统计推断 ----------
Xs = rng.exponential(2.0, size=(100000, 5)); ratio = Xs[:, 0]/Xs.sum(1)
check('4h', "Basu：Σ 与 X1/Σ 独立，E[X1/Σ]=1/n", abs(np.corrcoef(ratio, Xs.sum(1))[0, 1]) < 0.01 and abs(ratio.mean() - 0.2) < 2e-3)
n_ = 12; sd = 1.7; ok = 0; tr = 20000
for _ in range(tr):
    s2 = rng.normal(0, sd, n_).var(ddof=1)
    ok += (n_ - 1)*s2/stats.chi2.ppf(0.975, n_ - 1) <= sd**2 <= (n_ - 1)*s2/stats.chi2.ppf(0.025, n_ - 1)
check('4h', "方差 χ² 区间覆盖率 95%", abs(ok/tr - 0.95) < 0.006)
k_ = 7; lo_, hi_ = stats.chi2.ppf(0.025, 2*k_)/2, stats.chi2.ppf(0.975, 2*k_ + 2)/2
check('4h', "Garwood 区间端点满足尾概率", close(stats.poisson.sf(k_ - 1, lo_), 0.025, 1e-8) and close(stats.poisson.cdf(k_, hi_), 0.025, 1e-8))
xx_, nn_ = 3, 40; p0 = 0.2; z = (xx_/nn_ - p0)/math.sqrt(p0*(1 - p0)/nn_)
zw = 1.96; ph = xx_/nn_; cen = (ph + zw**2/(2*nn_))/(1 + zw**2/nn_); hw = zw/(1 + zw**2/nn_)*math.sqrt(ph*(1 - ph)/nn_ + zw**2/(4*nn_**2))
check('4h', "Score 区间 = Wilson 区间", all(abs(abs((ph - pp)/math.sqrt(pp*(1 - pp)/nn_)) - zw) < 1e-9 for pp in (cen - hw, cen + hw)))
tab = np.array([[8, 2], [1, 5]])
check('4h', "Fisher 精确检验（超几何）", close(stats.fisher_exact(tab, alternative='greater')[1], stats.hypergeom.sf(7, 16, 9, 10), 1e-12))
nW = 15; Wp = []
for _ in range(100000): Wp.append(np.sum(np.arange(1, nW + 1)[rng.random(nW) < 0.5]))
check('4h', "符号秩 E=n(n+1)/4, Var=n(n+1)(2n+1)/24", abs(np.mean(Wp) - nW*(nW + 1)/4) < 0.1 and abs(np.var(Wp)/(nW*(nW + 1)*(2*nW + 1)/24) - 1) < 0.02)
check('4h', "ARE：Wilcoxon 3/π，符号 2/π（正态）", close(12*(1/(2*math.sqrt(math.pi)))**2, 3/math.pi) and close(4*(1/math.sqrt(2*math.pi))**2, 2/math.pi))
g1, g2, g3 = rng.normal(0, 1, 8), rng.normal(0.5, 1, 10), rng.normal(1, 1, 7)
allv = np.r_[g1, g2, g3]; rk = stats.rankdata(allv); Nk = len(allv)
Rs = [rk[:8].sum(), rk[8:18].sum(), rk[18:].sum()]
check('4h', "Kruskal–Wallis 公式", close(12/(Nk*(Nk + 1))*sum(r**2/m for r, m in zip(Rs, (8, 10, 7))) - 3*(Nk + 1), stats.kruskal(g1, g2, g3).statistic))
al, be = 0.05, 0.1; A_, B_ = (1 - be)/al, be/(1 - al); m0, m1 = 0, 0.5
dec = []; Ns = []
for _ in range(20000):
    s = 0; k = 0
    while math.log(B_) < s < math.log(A_):
        x = rng.normal(m0); s += (m1 - m0)*x - (m1**2 - m0**2)/2; k += 1
    dec.append(s >= math.log(A_)); Ns.append(k)
check('4h', "SPRT：一类错误 ≤ α、E₀N 近似公式", np.mean(dec) <= al + 0.005 and abs(np.mean(Ns) - (al*math.log(A_) + (1 - al)*math.log(B_))/(-(m1 - m0)**2/2))/np.mean(Ns) < 0.2)
p = 10; th_ = rng.normal(size=p)*0.5; Xjs = th_ + rng.normal(size=(200000, p))
js = (1 - (p - 2)/np.sum(Xjs**2, 1))[:, None]*Xjs
check('4h', "James–Stein 风险 < p", np.mean(np.sum((js - th_)**2, 1)) < p - 1)
check('4h', "中位数区间 n=20 [X(6),X(15)] 覆盖率 95.9%", abs(1 - 2*stats.binom.cdf(5, 20, 0.5) - 0.9586) < 1e-4)
ns = 20000; Xp = rng.normal(rng.normal(size=ns)[:, None], 1.3, size=(ns, 2))
check('4h', "Neyman–Scott：MLE σ² → σ²/2", abs(np.sum((Xp[:, 0] - Xp[:, 1])**2)/(4*ns) - 1.69/2) < 0.02)
pp_ = 0.05
check('4h', "Sellke 界：p=0.05 时 BF ≤ 2.46", abs(1/(-math.e*pp_*math.log(pp_)) - 2.456) < 0.01)
check('4h', "bootstrap 在 max 处的原子 → 1-1/e", abs(1 - (1 - 1/1000)**1000 - (1 - 1/math.e)) < 2e-4)

# ---------- 04i 回归与多元 ----------
n, p = 60, 4; X = np.c_[np.ones(n), rng.normal(size=(n, p - 1))]; Hm = X @ np.linalg.solve(X.T @ X, X.T)
y = X @ np.array([1, 2, -1, 0.5]) + rng.normal(size=n); e = y - Hm @ y
loo = [y[i] - X[i] @ np.linalg.lstsq(np.delete(X, i, 0), np.delete(y, i), rcond=None)[0] for i in range(n)]
check('4i', "帽子矩阵 tr=p、h_ii≥1/n、留一残差 e/(1-h)", close(np.trace(Hm), p) and np.diag(Hm).min() >= 1/n - 1e-12 and np.allclose(loo, e/(1 - np.diag(Hm))))
x1 = rng.normal(size=n); x2 = 0.9*x1 + 0.3*rng.normal(size=n); Xv = np.c_[np.ones(n), x1, x2]
R2j = 1 - np.sum((x1 - np.c_[np.ones(n), x2] @ np.linalg.lstsq(np.c_[np.ones(n), x2], x1, rcond=None)[0])**2)/np.sum((x1 - x1.mean())**2)
check('4i', "VIF 公式", close(np.linalg.inv(Xv.T @ Xv)[1, 1], 1/((n - 1)*x1.var(ddof=1))/(1 - R2j), 1e-9))
Z = rng.normal(size=(100000, 2)); xa = Z[:, 0]; xb = 0.6*xa + 0.8*Z[:, 1]; yv = 2*xa + 3*xb + rng.normal(size=100000)
check('4i', "遗漏变量偏差 β1+β2δ", abs(np.polyfit(xa, yv, 1)[0] - (2 + 3*0.6)) < 0.02)
X1 = np.c_[np.ones(n), rng.normal(size=n)]; X2 = rng.normal(size=(n, 2)); yy = rng.normal(size=n)
M1 = np.eye(n) - X1 @ np.linalg.pinv(X1); full = np.linalg.lstsq(np.c_[X1, X2], yy, rcond=None)[0][2:]
check('4i', "Frisch–Waugh–Lovell", np.allclose(full, np.linalg.lstsq(M1 @ X2, M1 @ yy, rcond=None)[0]))
Xl = np.c_[np.ones(500), rng.normal(size=(500, 2))]; pl = 1/(1 + np.exp(-(Xl @ np.array([-0.5, 1.2, -0.7])))); yl = (rng.random(500) < pl).astype(float)
bb = np.zeros(3)
for _ in range(25):
    pr = 1/(1 + np.exp(-Xl @ bb)); W = pr*(1 - pr); zz = Xl @ bb + (yl - pr)/W; bb = np.linalg.solve(Xl.T @ (W[:, None]*Xl), Xl.T @ (W*zz))
nll = lambda b: -np.sum(yl*(Xl @ b) - np.log1p(np.exp(Xl @ b)))
check('4i', "Logistic IRLS = MLE", np.allclose(bb, optimize.minimize(nll, np.zeros(3), method='BFGS', options={'gtol': 1e-10}).x, atol=1e-5))
mu0, mu1 = np.zeros(2), np.array([1.0, 0.5]); Sg = np.array([[1, 0.3], [0.3, 0.8]]); Dm = math.sqrt((mu1 - mu0) @ np.linalg.solve(Sg, mu1 - mu0))
w_ = np.linalg.solve(Sg, mu1 - mu0); X0 = rng.multivariate_normal(mu0, Sg, 200000); X1_ = rng.multivariate_normal(mu1, Sg, 200000)
err = 0.5*np.mean(X0 @ w_ > w_ @ (mu0 + mu1)/2) + 0.5*np.mean(X1_ @ w_ < w_ @ (mu0 + mu1)/2)
check('4i', "LDA Bayes 错误率 Φ(-Δ/2)", abs(err - stats.norm.cdf(-Dm/2)) < 3e-3)
pH, nH = 3, 15; T2 = []
for _ in range(40000):
    Xh = rng.normal(size=(nH, pH)); xm = Xh.mean(0); Sh = np.cov(Xh.T); T2.append(nH*xm @ np.linalg.solve(Sh, xm))
check('4i', "Hotelling T² 的 F 分布", stats.kstest(np.array(T2)*(nH - pH)/(pH*(nH - 1)), stats.f(pH, nH - pH).cdf).statistic < 0.01)
xt_ = rng.normal(size=200000); w__ = xt_ + rng.normal(scale=0.7, size=200000); yt = 2*xt_ + rng.normal(size=200000)
check('4i', "衰减偏差 β·σx²/(σx²+σu²)", abs(np.polyfit(w__, yt, 1)[0] - 2/(1 + 0.49)) < 0.01)
u_ = rng.normal(size=200000); zI = rng.normal(size=200000); xI = 0.8*zI + u_ + 0.3*rng.normal(size=200000); yI = 1.5*xI - 2*u_ + rng.normal(size=200000)
check('4i', "工具变量 Cov(z,y)/Cov(z,x)", abs(np.cov(zI, yI)[0, 1]/np.cov(zI, xI)[0, 1] - 1.5) < 0.02 and abs(np.polyfit(xI, yI, 1)[0] - 1.5) > 0.3)
phi = 0.6; sar = np.zeros(400000); ee = rng.normal(size=400000)
for i in range(1, 400000): sar[i] = phi*sar[i - 1] + ee[i]
fw, Pw = __import__('scipy.signal', fromlist=['welch']).welch(sar, fs=2*math.pi, nperseg=4096)
check('4i', "AR(1) 谱密度 σ²/(2π(1-2φcos ω+φ²))（Welch 单边谱 = 2f）", np.median(np.abs(Pw[5:500]/(2/(2*math.pi*(1 - 2*phi*np.cos(fw[5:500]) + phi**2))) - 1)) < 0.1)
yw = np.array([1, phi, phi**2])
check('4i', "Yule–Walker（AR(1)）ρ_k=φ^k", np.allclose([np.corrcoef(sar[:-k], sar[k:])[0, 1] for k in (1, 2)], [phi, phi**2], atol=0.01))
G_, sg2, nj = 0.5, 1.0, 4
check('4i', "随机截距 BLUP 收缩 nτ²/(nτ²+σ²)", close(G_*nj/(nj*G_ + sg2), (lambda V: (G_*np.ones(nj) @ np.linalg.solve(V, np.ones(nj))))(G_*np.ones((nj, nj)) + sg2*np.eye(nj))))
Xk = rng.normal(size=(30, 2)); yk = np.sin(Xk[:, 0]) + 0.1*rng.normal(size=30); Kk = np.exp(-0.5*np.sum((Xk[:, None] - Xk[None])**2, -1))
alpha = np.linalg.solve(Kk + 0.1*np.eye(30), yk)
check('4i', "核岭回归解满足一阶条件", np.allclose(Kk @ (Kk @ alpha - yk) + 0.1*Kk @ alpha, 0, atol=1e-8))

npass = sum(r[2] for r in R); print(f"\n第三轮续写数学(四) 04d–04i: {npass}/{len(R)} PASS")
json.dump(R, open(__file__.replace('.py', '.json'), 'w'), ensure_ascii=False)
